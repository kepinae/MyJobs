import datetime
import itertools
import json
import logging
from lxml import etree
import operator
from fsm.views import FSMView
import urllib
import json as simplejson
from types import IntType
from urlparse import urlparse, urlunparse

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core import urlresolvers
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import (HttpResponse, Http404, HttpResponseNotFound,
                         HttpResponseRedirect, HttpResponseServerError,
                         QueryDict)
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext, loader
from django.template.defaultfilters import safe
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_str, iri_to_uri
from django.utils.feedgenerator import Atom1Feed
from django.views.decorators.csrf import csrf_exempt

from slugify import slugify

from moc_coding import models as moc_models
from serializers import ExtraValue, XMLExtraValuesSerializer
from settings import DEFAULT_PAGE_SIZE
from tasks import task_etl_to_solr, task_update_solr, task_priority_etl_to_solr
from xmlparse import text_fields
from import_jobs import add_jobs, delete_by_guid
from transform import transform_for_postajob

from myblocks.views import BlockView
from myblocks.models import SearchResultBlock, Page
from myblocks import context_tools
from seo.templatetags.seo_extras import facet_text, smart_truncate
from seo.breadbox import Breadbox
from seo.cache import get_custom_facets, get_site_config, get_total_jobs_count
from seo.search_backend import DESearchQuerySet
from seo import helpers
from seo.filters import FacetListWidget
from seo.forms.admin_forms import UploadJobFileForm
from seo.models import (BusinessUnit, Company, Configuration, Country,
                        GoogleAnalytics, JobFeed, SeoSite, SiteTag)
from seo.decorators import (sns_json_message, custom_cache_page, protected_site,
                            home_page_check)
from seo.sitemap import DateSitemap
from seo.templatetags.seo_extras import filter_carousel
from transform import hr_xml_to_json


"""
The 'filters' dictionary seen in some of these methods
has this basic structure:

filters = {'title_slug': {value}|None,
           'location_slug': {value}|None,
           'facet_slug': {value}|None,
           'moc_slug': {value}|None}

From this dictionary, we should be able to filter most
items down to what we actually need.
"""
LOG = logging.getLogger('views')


def site_family(request):
    callback = request.GET.get("callback")
    ctx = {'user': request.user}
    response = render_to_response(
        'seo/site_family.html', ctx, content_type='text/html')

    if callback:
        content = "%s(%s)" % (callback, json.dumps(response.content))
        response = HttpResponse(content_type='text/javascript')
        response.content = content
        return response
    else:
        return response


def find_page(request, page_type):
    page = None
    if request.user.is_authenticated() and request.user.is_staff:
        page = Page.objects.filter(sites=settings.SITE,
                                   status=Page.STAGING,
                                   page_type=page_type).first()

    if not page:
        page = Page.objects.filter(sites=settings.SITE,
                                   status=Page.PRODUCTION,
                                   page_type=page_type).first()

    if not page:
        page = Page.objects.filter(sites__pk=1,
                                   status=Page.PRODUCTION,
                                   page_type=page_type).first()
    return page


class FallbackBlockView(BlockView):
    page_type = Page.SEARCH_RESULTS
    fallback = None

    def handle_request(self, request, *args, **kwargs):
        if not self.page:
            self.set_page(request)
        if not self.page:
            return self.fallback(request, *args, **kwargs)
        required_redirect = self.page.handle_redirect(request, *args, **kwargs)
        if required_redirect:
            return required_redirect
        return HttpResponse(self.page.render(request, **kwargs))

    def post(self, request, *args, **kwargs):
        self.set_page(request)
        if not self.page:
            return self.fallback(request, *args, **kwargs)
        return super(FallbackBlockView, self).post(request, *args, **kwargs)

    def set_page(self, request):
        page = find_page(request, self.page_type)
        setattr(self, 'page', page)


def ajax_geolocation_facet(request):
    """
    Returns facets for the inputted facet_type
    Inputs:
        :filter_path: Filters arguments from url
        :facet_type: Field that is being faceted
        :sqs: starting Haystack Search Query Set
        :search_facets: Boolean, True when there is a query to apply
                before faceting
    Output:
        :HttpResponse: listing facets for the input facet_type

    """
    filter_path = request.GET.get('filter_path', '/jobs/')
    filters = helpers.build_filter_dict(filter_path)

    sort_order = request.REQUEST.get('sort', 'relevance')

    num_items = int(request.GET.get('num_items', DEFAULT_PAGE_SIZE))

    facet_field_type = request.GET.get('facet', 'buid')

    sqs = helpers.prepare_sqs_from_search_params(request.GET)
    sqs = sqs.facet("lat_long_%s_slab" % facet_field_type, limit=-1)
    default_jobs = helpers.get_jobs(default_sqs=sqs,
                                    custom_facets=settings.DEFAULT_FACET,
                                    exclude_facets=settings.FEATURED_FACET,
                                    jsids=settings.SITE_BUIDS,
                                    filters=filters,
                                    facet_limit=num_items,
                                    sort_order=sort_order)
    featured_jobs = helpers.get_featured_jobs(default_sqs=sqs,
                                              jsids=settings.SITE_BUIDS,
                                              filters=filters,
                                              facet_limit=num_items,
                                              sort_order=sort_order)

    facet_counts = default_jobs.add_facet_count(featured_jobs).get('fields')
    facet_counts = facet_counts['lat_long_%s_slab' % facet_field_type]

    data = []
    for facet_count in facet_counts:
        slab, count = facet_count
        try:
            latitude, longitude, buid = slab.split('::')
        except ValueError:
            continue

        data.append({
            'buid': buid,
            'count': count,
            'lat': latitude,
            'lng': longitude,
        })

    data = json.dumps(data, sort_keys=True)
    callback_name = request.GET.get('callback')
    if callback_name:
        data = callback_name + "(" + data + ")"

    return HttpResponse(data, content_type='application/javascript')


def ajax_get_facets(request, filter_path, facet_type):
    """
    Returns facets for the inputted facet_type
    Inputs:
        :filter_path: Filters arguments from url
        :facet_type: Field that is being faceted
        :sqs: starting Haystack Search Query Set
        :search_facets: Boolean, True when there is a query to apply
                before faceting
    Output:
        :HttpResponse: listing facets for the input facet_type

    """
    plurals = {'titles': 'title', 'cities': 'city', 'states': 'state',
               'mocs': 'moc', 'mapped': 'mapped_moc',
               'countries': 'country', 'facets': 'facet',
               'company-ajax': 'company'}
    _type = plurals[facet_type]
    GET = request.GET
    site_config = get_site_config(request)
    filter_path = GET.get('filter_path', filter_path)
    filters = helpers.build_filter_dict(filter_path)

    sqs = helpers.prepare_sqs_from_search_params(GET)
    sort_order = request.REQUEST.get('sort', 'relevance')
    offset = int(GET.get('offset', site_config.num_filter_items_to_show*2))
    num_items = int(GET.get('num_items', DEFAULT_PAGE_SIZE))
    if _type == 'facet':
        # Standard facets are all already loaded on page load,
        # so there will never be anything to return here.
        items = []
    else:
        default_jobs = helpers.get_jobs(default_sqs=sqs,
                                        custom_facets=settings.DEFAULT_FACET,
                                        exclude_facets=settings.FEATURED_FACET,
                                        jsids=settings.SITE_BUIDS,
                                        filters=filters,
                                        facet_limit=num_items,
                                        facet_offset=offset,
                                        sort_order=sort_order)

        featured_jobs = helpers.get_featured_jobs(default_sqs=sqs,
                                                  jsids=settings.SITE_BUIDS,
                                                  filters=filters,
                                                  facet_limit=num_items,
                                                  facet_offset=offset,
                                                  sort_order=sort_order)


        #TODO: This may throw off num_items and offset. Add slicing to each
        #field list to return the correct number of facet constraints/counts
        #Jason McLaughlin 09/10/2012
        facet_counts = default_jobs.add_facet_count(featured_jobs).get('fields')
        facet_results = facet_counts['%s_slab' % _type]

        qs = QueryDict(request.META.get('QUERY_STRING', None)).copy()
        for param in ['offset', 'filter_path', 'num_items']:
            if param in qs:
                del qs[param]
        query_string = qs.urlencode()

        widget = FacetListWidget(request, site_config, _type, facet_results,
                                 filters, query_string=query_string)

        items = []
        for facet in facet_results:
            facet_slab, facet_count = facet
            url = widget.get_abs_url(facet)
            name = safe(smart_truncate(facet_text(facet_slab)))
            if name == 'None' or name.startswith('Virtual'):
                continue
            items.append({'url': url, 'name': name, 'count': facet_count})

    data_dict = {'items': items, 'item_type': _type, 'num_items': 0}

    return render_to_response('ajax_filter_items.html',
                              data_dict,
                              context_instance=RequestContext(request),
                              content_type='text/html')


def ajax_get_jobs(request, filter_path):
    # Allow for a SearchResult block to handle the requests if
    # there is a SearchResult block associated with a SEARCH_RESULTS
    # page for this site.
    page = find_page(request, Page.SEARCH_RESULTS)
    if page:
        search_result_block = None
        for block in page.all_blocks():
            if isinstance(block, SearchResultBlock):
                search_result_block = block
                break

        if search_result_block:
            return HttpResponse(search_result_block.render_for_ajax(request))


    GET = request.GET
    # TODO: let's put the site_config onto the request object
    site_config = get_site_config(request)
    site_config.num_job_items_to_show = 0
    filters = helpers.build_filter_dict(filter_path)
    try:
        offset = int(GET.get(u'offset', 0))
    except ValueError:
        offset = 0
    try:
        num_items = int(GET.get(u'num_items', DEFAULT_PAGE_SIZE))
    except ValueError:
        num_items = DEFAULT_PAGE_SIZE
    custom_facets = settings.DEFAULT_FACET
    sqs = helpers.prepare_sqs_from_search_params(GET)
    sort_order = request.REQUEST.get('sort', 'relevance')
    default_jobs = helpers.get_jobs(default_sqs=sqs,
                                    custom_facets=custom_facets,
                                    exclude_facets=settings.FEATURED_FACET,
                                    jsids=settings.SITE_BUIDS,
                                    filters=filters,
                                    sort_order=sort_order)
    featured_jobs = helpers.get_featured_jobs(default_sqs=sqs,
                                              jsids=settings.SITE_BUIDS,
                                              filters=filters,
                                              sort_order=sort_order)
    (num_featured_jobs, num_default_jobs, featured_offset, default_offset) = \
        helpers.featured_default_jobs(featured_jobs.count(),
                                      default_jobs.count(),
                                      num_items,
                                      site_config.percent_featured,
                                      offset)

    for job in default_jobs[default_offset:default_offset+num_default_jobs]:
        text = filter(None, [getattr(job, x, "None") for x in text_fields])
        setattr(job, 'text', " ".join(text))
    for job in featured_jobs[featured_offset:featured_offset+num_featured_jobs]:
        text = filter(None, [getattr(job, x, "None") for x in text_fields])
        setattr(job, 'text', " ".join(text))

    # Build the site commitment string
    sitecommit_str = helpers.\
        make_specialcommit_string(settings.COMMITMENTS.all())
    data_dict = {
        'default_jobs':
            default_jobs[default_offset:default_offset+num_default_jobs],
        'featured_jobs':
            featured_jobs[featured_offset:featured_offset+num_featured_jobs],
        'site_config': site_config,
        'filters': filters,
        'title_term': request.GET.get('q', '\*'),
        'site_commitments_string': sitecommit_str,
        'site_tags': settings.SITE_TAGS
    }

    return render_to_response('listing_items.html',
                              data_dict,
                              context_instance=RequestContext(request),
                              content_type='text/html')


def robots_txt(request):
    host = str(request.META["HTTP_HOST"])
    return render_to_response('robots.txt', {'host': host},
                              content_type="text/plain")


@protected_site
@custom_cache_page
@home_page_check
def job_detail_by_title_slug_job_id(request, job_id, title_slug=None,
                                    location_slug=None, feed=None):
    """
    Build the job detail page.

    Inputs:
    :request:       a django request object
    :job_id:        the uid of the selected job
    :title_slug:    the job title from the url (if provided)
    :location_slug: the job location from the url (if provided)
    :feed:          the feed source from the url (if provided)

    """
    # preserve any query strings passed in from the referer. J.Sole 11-9-12
    qry = ""
    for k, v in request.GET.items():
        qry = ("=".join([k, v]) if qry == "" else
               "&".join([qry, "=".join([k, v])]))

    site_config = get_site_config(request)
    filters = helpers.build_filter_dict(request.path)

    search_type = 'guid' if len(job_id) > 31 else 'uid'
    try:
        the_job = DESearchQuerySet().narrow("%s:(%s)" % (search_type,
                                                         job_id))[0]
    except IndexError:
        return dseo_404(request)
    else:
        if settings.SITE_BUIDS and the_job.buid not in settings.SITE_BUIDS:
            if the_job.on_sites and not (set(settings.SITE_PACKAGES) & set(the_job.on_sites)):
                return redirect('home')

    breadbox_path = helpers.job_breadcrumbs(the_job,
                                            site_config.browse_company_show)

    query_path = request.META.get('QUERY_STRING', None)
    if query_path:
        # Remove location from query path since it shouldn't be in the
        # final urls.
        qs = QueryDict(query_path).copy()
        try:
            del qs['location']
        except KeyError:
            pass

        query_path = "%s" % qs.urlencode() if qs.urlencode() else ''

        # Append the query_path to all of the exising urls
        for field in breadbox_path:
            breadbox_path[field]['path'] = (("%s?%s" %
                                             (breadbox_path[field].get(
                                                 'path', '/jobs/'), query_path))
                                            if query_path else
                                            breadbox_path[field]['path'])

        # Create a new path for title and moc query string values
        # from the job information.
        fields = ['title', 'city']
        path = ''
        for field in fields:
            slab = getattr(the_job, '%s_slab' % field)
            path = "%s%s/" % (path, slab.split("::")[0])
        for field in ['q', 'moc']:
            if request.GET.get(field, None):
                breadbox_path[field] = {}
                qs = QueryDict(query_path).copy()
                del qs[field]
                breadbox_path[field]['path'] = "/%s?%s" % (path, qs.urlencode())
                breadbox_path[field]['display'] = request.GET.get(field)

    # Get the job's Company object; it will be used for the canonical URL
    # and the Open Graph image tag later on
    try:
        co = Company.objects.get(name=the_job.company)
    except Company.DoesNotExist:
        co = None

    pg_title = helpers._page_title(breadbox_path)

    # Build the data for the company module, if it's displayed on this site
    if site_config.browse_company_show and co and co.member:
        company_data = helpers.company_thumbnails([co])[0]
    else:
        company_data = None

    # This check is to make sure we're at the canonical job detail url.

    # We only need the job id to be in the url, but we also put the title.
    # The offshoot of that is that if someone mistypes or mispells the title
    # in the url, then we want whoever clicks the link to be directed to the
    # canonical (and correctly spelled/no typo) version.
    if (title_slug == the_job.title_slug and
            location_slug == slugify(the_job.location)) \
            and not search_type == 'uid':
        ga = settings.SITE.google_analytics.all()
        host = 'foo'
        link_query = ""
        jobs_count = get_total_jobs_count()

        if the_job.link is None:
            LOG.error("No link for job %s", the_job.uid)
            url = ''
            path = ''
        else:
            url = urlparse(the_job.link)
            path = url.path.replace("/", "")
            # use the override view source
            if settings.VIEW_SOURCE:
                path = "%s%s" % (path[:32], settings.VIEW_SOURCE.view_source)

        # add any ats source code name value pairs
        ats = settings.ATS_SOURCE_CODES.all()
        if ats:
            link_query += "&".join(["%s" % code for code in ats])

        # build the google analytics query string
        gac = settings.GA_CAMPAIGN
        gac_data = {
            "campaign_source": "utm_source",
            "campaign_medium": "utm_medium",
            "campaign_term": "utm_term",
            "campaign_content": "utm_content",
            "campaign_name": "utm_campaign"
        }

        if gac:
            q_str = "&".join(["%s=%s" % (v, getattr(gac, k))
                              for k, v in gac_data.items()])
            link_query = "&".join([link_query, q_str])

        if link_query:
            urllib.quote_plus(link_query, "=&")

        if the_job.link:
            the_job.link = urlunparse((url.scheme, url.netloc, path,
                                       '', link_query, ''))

        # Build the site commitment string
        sitecommit_str = helpers.make_specialcommit_string(
            settings.COMMITMENTS.all())

        data_dict = {
            'the_job': the_job,
            'total_jobs_count': jobs_count,
            'company': company_data,
            'og_img': co.og_img if co else co,
            'google_analytics': ga,
            'site_name': settings.SITE_NAME,
            'site_title': settings.SITE_TITLE,
            'site_heading': settings.SITE_HEADING,
            'site_tags': settings.SITE_TAGS,
            'site_description': settings.SITE_DESCRIPTION,
            'site_commitments_string': sitecommit_str,
            'host': host,
            'site_config': site_config,
            'type': 'title',
            'filters': filters,
            'crumbs': breadbox_path,
            'pg_title': pg_title,
            'build_num': settings.BUILD,
            'view_source': settings.VIEW_SOURCE,
            'search_url': '/jobs/',
            'title_term': request.GET.get('q', '\*'),
            'moc_term': request.GET.get('moc', '\*'),
            'location_term': the_job.location
        }

        # Render the response, but don't return it yet--we need to add an
        # additional canonical url header to the response.
        the_response = render_to_response('job_detail.html', data_dict,
                                  context_instance=RequestContext(request))

        # The test described in MS-481 was considered a success and the code
        # is now in a more general form (MS-604). Companies with a microsite use
        # that, companies without use www.my.jobs as their canonical host. The
        # canonical link is attached to the response object as a header field.
        if co:
            can_ms = co.canonical_microsite if co.canonical_microsite else 'http://www.my.jobs'
            if can_ms[-1] == '/':
                can_ms = can_ms[:-1]
            # Text sent in headers can only be in the ASCII set; characters
            # outside this set won't work. We mitigate this by running each
            # chunk of the URL through slugify to convert accented characters,
            # etc. to their nearest ASCII equivalent, and rejoining the pieces.
            # The path is broken into pieces to preserve the slashes--slugify
            # strips those otherwise.
            path_uri = iri_to_uri(request.path)
            canonical_path = '<{0}{1}>; rel="canonical"'.format(
                can_ms, ("/".join([slugify(each) for each in
                                   path_uri.split('/')])))
            the_response['Link'] = canonical_path.encode('utf8')

        return the_response
    else:
        # The url wasn't quite the canonical form, so we redirect them
        # to the correct version based on the title and location of the
        # job with the passed in id.
        kwargs = {
            'location_slug': slugify(the_job.location),
            'title_slug': the_job.title_slug,
            'job_id': the_job.guid
        }
        redirect_url = reverse(
            'job_detail_by_location_slug_title_slug_job_id',
            kwargs=kwargs
        )

        # if the feed type is passed, add source params, otherwise only preserve
        # the initial query string.
        if feed:
            if qry != "":
                qry = "&%s" % qry
            redirect_url += "?utm_source=%s&utm_medium=feed%s" % (feed, qry)
        elif qry:
            redirect_url += "?%s" % qry
        return redirect(redirect_url, permanent=True)


class JobDetail(FallbackBlockView):
    page_type = Page.JOB_DETAIL

    def __init__(self, **kwargs):
        super(JobDetail, self).__init__(**kwargs)
        self.fallback = job_detail_by_title_slug_job_id


@custom_cache_page
def stylesheet(request, cid=None, css_file="stylesheet.css"):
    """
    This view allows for the templatizing of css stylesheets via the django
    templating system.

    Inputs:
    :request: The django request object
    :cid: the confirguration object id. None by default.
    "css_file: the stylesheet in the tempalte folder to render.

    Returns:
    render_to_response object as CSS file

    """
    if cid:
        selected_stylesheet = Configuration.objects.get(id=cid)
    else:
        selected_stylesheet = get_site_config(request)
    return render_to_response(css_file, {'css': selected_stylesheet},
                              context_instance=RequestContext(request),
                              content_type="text/css",)


@custom_cache_page
def posting_stylesheet(request, cid=None, css_file="posting-stylesheet.css"):
    """
    TODO: Make stylesheet dynamic and not hard code.
    Quick C&P due to due date.
    """
    if cid:
        selected_stylesheet = Configuration.objects.get(id=cid)
    else:
        selected_stylesheet = get_site_config(request)
    return render_to_response(css_file, {
                              'css': selected_stylesheet},
                              context_instance=RequestContext(request),
                              content_type="text/css",)


@custom_cache_page
def job_listing_nav_redirect(request, home=None, cc3=None):
    """
    An alternate url syntax to job_listing_by_slug_tag view for browsing
    jobs by fields and applying a 3 letter country code.

    Inputs:
    :home: slug filter type passed by url
    :cc3: 3 letter country code
    """
    path_part = request.path
    filters = helpers.build_filter_dict(path_part)
    url = 'location'
    sort_order = request.REQUEST.get('sort', 'relevance')
    jobs = helpers.get_jobs(custom_facets=settings.DEFAULT_FACET,
                            jsids=settings.SITE_BUIDS,
                            filters=filters, sort_order=sort_order)
    facet_counts = jobs.facet_counts()['fields']

    if not cc3:
        # facet_counts['country_slab'] might look like:
        #   [('usa/jobs::United States', 247)]
        cc3 = facet_counts['country_slab'][0][0].split('/')[0]
    redirect_kwargs = {'location_slug': cc3}
    if home == 'state':
        url = 'location'
        primary_nav = facet_counts['state_slab']
        slug = primary_nav[0][0].split('::')[0] if primary_nav else ''
        redirect_kwargs['location_slug'] = '/'.join(slug.split('/')[0:-1])
    elif home == 'city':
        url = 'location'
        primary_nav = facet_counts['city_slab']
        slug = primary_nav[0][0].split('::')[0] if primary_nav else ''
        redirect_kwargs['location_slug'] = '/'.join(slug.split('/')[0:-1])
    elif home == 'title':
        url = 'title_location'
        primary_nav = facet_counts['title_slab']
        slug = primary_nav[0][0].split('::')[0] if primary_nav else ''
        redirect_kwargs['title_slug'] = '/'.join(slug.split('/')[0:-1])
    elif home == 'facet':
        url = 'location_facet'
        custom_facets = helpers.get_solr_facet(settings.SITE_ID,
                                               settings.SITE_BUIDS,
                                               filters)
        # This needs to be changed to get_object_or_404
        country = Country.objects.get(abbrev=cc3)
        primary_nav = [x for x in custom_facets if x[0].country in
                       (country.name, '') and x[1]]
        redirect_kwargs['facet_slug'] = primary_nav[0][0].url_slab.split('::')[0] if primary_nav else ''
    elif home == 'moc':
        url = 'location_moc'
        redirect_kwargs['moc_slug'] = facet_counts['moc_slab'][0][0].split('::')[0]

    return redirect(url, permanent=True, **redirect_kwargs)


@custom_cache_page
def syndication_feed(request, filter_path, feed_type):
    """
    Generates a specific feed type, based on the imput values.

    Inputs:
    :request: django request object
    :filter_path: the url path containing job filters, if any
    :feed_type: format of the feed. json|rss|xml|atom|indeed

    Returns:
    HttpResponse Object which is the feed.

    GET Parameters (all optional):
    :num_items: Number of job listings to return; Default: 500,
        Max: 1000
    :offset: Number of listings to skip when returning a feed;
        Default: 0
    :date_sort: Sort listings by date; Default: 'True'
    :days_ago: Only return listings that were created at most
        this many days ago; Default: 0 (any date)

    """
    filters = helpers.build_filter_dict(filter_path)
    date_sort = 'True'
    max_items, num_items, offset, days_ago = 1000, 500, 0, 0
    if request.GET:
        sqs = helpers.prepare_sqs_from_search_params(request.GET)
        #Leave num_items and offset at defaults if they're not in QueryDict
        date_sort = request.GET.get(u'date_sort', date_sort)
        try:
            new_num_items = request.GET.get(u'num_items')
            num_items = int(new_num_items)
        except (ValueError, TypeError, UnicodeEncodeError):
            pass
        try:
            new_offset = request.GET.get(u'offset', offset)
            offset = int(new_offset)
        except (ValueError, TypeError, UnicodeEncodeError):
            pass
        try:
            new_days_ago = request.GET.get(u'days_ago', days_ago)
            days_ago = int(new_days_ago)
        except (ValueError, TypeError, UnicodeEncodeError):
            pass

    else:
        sqs = helpers._sqs_narrow_by_buid_and_site_package(
            helpers.sqs_apply_custom_facets(settings.DEFAULT_FACET))
    sort_order = 'new' if date_sort == 'True' else 'relevance'
    jobs = helpers.get_jobs(default_sqs=sqs,
                            custom_facets=settings.DEFAULT_FACET,
                            jsids=settings.SITE_BUIDS,
                            filters=filters, sort_order=sort_order)

    job_count = jobs.count()
    num_items = min(num_items, max_items, job_count)
    jobs[:num_items]

    if days_ago:
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(days=days_ago)
        jobs = jobs.filter(date_new__gte=start_date)

    try:
        j = jobs[0]
    except IndexError:
        j = None

    if jobs and j.date_updated:
        buid_last_written = j.date_updated
    else:
        buid_last_written = datetime.datetime.now()

    qs = jobs.values('city', 'company', 'country', 'country_short',
                     'date_new', 'description', 'location', 'reqid', 'state',
                     'state_short', 'title', 'uid', 'guid',
                     'is_posted')[offset:offset+num_items]

    self_link = ExtraValue(name="link", content="",
                           attributes={'href': request.build_absolute_uri(),
                                       'rel': 'self'})
    links = [self_link]
    next_offset = num_items + offset
    if next_offset < job_count:
        next_num_items = min(num_items, job_count-next_offset)
        #build the link to the next page
        next_uri = "{h}?num_items={ni}&offset={no}".format(
            h=request.build_absolute_uri().split("?")[0],
            ni=next_num_items,
            no=next_offset)
        #Add other attributes back to next_uri
        request_attributes = [u'&%s=%s' % (key, value) for(key, value)
                              in request.GET.items() if
                              key not in ('num_items', 'offset', 'amp')]
        attributes_string = ''.join(request_attributes)
        next_uri += attributes_string

        next_link = ExtraValue(name="link", content="",
                               attributes={"href": next_uri, "rel": "next"})
        links.append(next_link)

    if feed_type == 'json':
        response = HttpResponse(helpers.make_json(qs, request.get_host()),
                                content_type='application/json')
    elif feed_type == 'jsonp':
        callback_name = request.GET.get('callback', 'direct_jsonp_callback')
        data = helpers.make_json(qs, request.get_host())
        output = callback_name + "(" + data + ")"
        response = HttpResponse(output, content_type='application/javascript')
    elif feed_type == 'xml':
        # return xml data for page's jobs
        # consider trimming non-essential feilds from job document
        s = XMLExtraValuesSerializer(
            publisher=settings.SITE_NAME,
            extra_values=links,
            publisher_url="http://%s" % request.get_host(),
            last_build_date=buid_last_written)
        data = s.serialize(qs)
        response = HttpResponse(data, content_type='application/xml')
    elif feed_type == 'indeed':
        # format xml feed per Indeed's xml feed specifications
        # here: http://www.indeed.com/intl/en/xmlinfo.html
        s = XMLExtraValuesSerializer(
            feed_type=feed_type,
            use_cdata=True,
            extra_values=links,
            publisher=settings.SITE_NAME,
            publisher_url="http://%s" % request.get_host(),
            last_build_date=buid_last_written,
            field_mapping={'date_new': 'date',
                           'uid': 'referencenumber'})
        data = s.serialize(qs)
        response = HttpResponse(data, content_type='application/xml')

    else:
        # return rss or atom for this page's jobs
        if feed_type != 'atom':
            feed_type = 'rss'
        rss = JobFeed(feed_type)
        rss.items = qs

        selected = helpers.get_bread_box_headings(filters, jobs)
        rss.description = ''

        if not any in selected.values():
            selected = {'title_slug': request.GET.get('q'),
                        'location_slug': request.GET.get('location')}

        breadbox = Breadbox(request.path, selected, jobs, request.GET)

        rss.description = helpers.build_results_heading(breadbox)
        rss.title = rss.description

        if feed_type == 'atom':
            rss.feed_type = Atom1Feed

        data = Feed.get_feed(rss, jobs, request)
        response = HttpResponse(content_type=data.mime_type)
        data.write(response, 'utf-8')

    return response


def member_carousel_data(request):
    """
    Returns the carousel data as JSONP for all member companies; this is called
    from outside the Django app by a JavaScript widget.

    Inputs
    :request: A Django request object

    Returns
    :jsonp: JSONP formatted bit of JavaScript with company url, name, and image

    """

    if request.GET.get('microsite_only') == 'true':
        members = helpers.company_thumbnails(Company.objects.filter(
            member=True).exclude(canonical_microsite__isnull=True).exclude(
            canonical_microsite=u""))
    else:
        members = Company.objects.filter(member=True)
        members = helpers.company_thumbnails(members)

    if request.GET.get('callback'):
        callback_name = request.GET['callback']
    else:
        callback_name = 'member_carousel_callback'
    data = json.dumps(members)
    output = callback_name + "(" + data + ")"
    return HttpResponse(output, content_type='application/javascript')


def ajax_filter_carousel(request):
    filters = helpers.build_filter_dict(request.path)
    query_path = request.META.get('QUERY_STRING', None)

    site_config = get_site_config(request)
    num_jobs = int(site_config.num_job_items_to_show) * 2
    sort_order = request.REQUEST.get('sort', 'relevance')
    # Apply any parameters in the querystring to the solr search.
    sqs = (helpers.prepare_sqs_from_search_params(request.GET) if query_path
           else None)

    custom_facet_counts = []
    if site_config.browse_facet_show:
        cf_count_tup = get_custom_facets(request, filters=filters,
                                         query_string=query_path)

        if not filters['facet_slug']:
            custom_facet_counts = cf_count_tup
        else:
            facet_slugs = filters['facet_slug'].split('/')
            active_facets = helpers.standard_facets_by_name_slug(facet_slugs)
            custom_facet_counts = [(facet, count) for facet, count
                                   in cf_count_tup
                                   if facet not in active_facets]

    default_jobs = helpers.get_jobs(default_sqs=sqs,
                                    custom_facets=settings.DEFAULT_FACET,
                                    exclude_facets=settings.FEATURED_FACET,
                                    jsids=settings.SITE_BUIDS, filters=filters,
                                    facet_limit=num_jobs, sort_order=sort_order)

    featured_jobs = helpers.get_featured_jobs(default_sqs=sqs,
                                              filters=filters,
                                              jsids=settings.SITE_BUIDS,
                                              facet_limit=num_jobs,
                                              sort_order=sort_order)
    facet_counts = default_jobs.add_facet_count(featured_jobs).get('fields')

    widgets = helpers.get_widgets(request, site_config, facet_counts,
                                  custom_facet_counts, filters=filters)

    html = loader.render_to_string('filter-carousel.html',
                                   filter_carousel({'widgets': widgets}))
    return HttpResponse(json.dumps(html),
                        content_type='text/javascript')


def ajax_cities(request):
    """
    Returns a list of cities and job counts for a given state.
    TODO: This is a good candidate for the API

    Inputs
    :request: A Django request object

    Returns
    render_to_response call (a list of cities in HTML format)

    """
    sqs = DESearchQuerySet()
    state = request.GET.get('state', "[* TO *]")
    slab_state = state.lower().replace(" ", "")
    results = sqs.narrow(u"state:({0})".format(state)
              ).facet('city_slab').facet_counts().get('fields').get('city_slab')

    output = []
    for result in results:
        city = {}
        city['count'] = result[1]
        url, location = result[0].split("::")
        city['url'] = url
        city['location'] = location[:-4]
        city['slab_state'] = slab_state

        output.append(city)

    data_dict = {
        'city_data': output
    }

    return render_to_response('ajax_cities.html', data_dict,
                              context_instance=RequestContext(request))

def ajax_sites(request):
    selected_tag = request.GET.get('tag', None)
    try:
        tag = SiteTag.objects.get(site_tag=selected_tag)
    except:
        tag = ""
    tag_sites = SeoSite.objects.filter(
                   site_tags__site_tag=tag)

    data_dict = {
        'sites': tag_sites
    }

    return render_to_response('ajax_sites.html', data_dict,
                              context_instance=RequestContext(request))


class BusinessUnitAdminFilter(FSMView):
    model = BusinessUnit
    fields = ('title__icontains', 'pk__icontains', )

    @method_decorator(login_required(login_url='/admin/'))
    def dispatch(self, *args, **kwargs):
        """
        Decorators on this function will be run on every request that
        goes through this class.

        """
        return super(BusinessUnitAdminFilter, self).dispatch(*args, **kwargs)


class SeoSiteAdminFilter(FSMView):
    model = SeoSite
    fields = ('domain__icontains',) 

    @method_decorator(login_required(login_url='/admin/'))
    def dispatch(self, *args, **kwargs):
        """
        Decorators on this function will be run on every request that
        goes through this class.

        """
        return super(SeoSiteAdminFilter, self).dispatch(*args, **kwargs)


@login_required(login_url='/admin/')
def ajax_buids(request):
    """
    Creates a jsonp formatted list of business units.

    inputs:
    :filter: The business units or business unit names being searched for,
             seperated by commas.
    :callback: The javascript function that will be called on return.

    returns:
    :response: A jsonp formatted list of all of the business units matching the
               filter.`
    """
    buid_list = request.GET.get('filter', '')
    callback = request.GET.get('callback', '')

    buids = []
    if buid_list:
        buids = buid_list.split(",")

    for i in range(0, len(buids)):
        try:
            buids[i] = int(buids[i])
        except Exception:
            pass

    q = [Q(id=buid) if type(buid) is IntType else Q(title__icontains=buid)
         for buid in buids]

    if q:
        result = BusinessUnit.objects.filter(reduce(operator.or_, q))
    else:
        result = BusinessUnit.objects.all()

    data = {}
    for r in result:
        data[r.id] = r.title

    response = '%s(%s);' % (callback, json.dumps(data))
    return HttpResponse(response, content_type="text/javascript")


@custom_cache_page
def home_page(request):
    """
    The base view for the root URL of a site.

    inputs:
    :request: django request object

    returns:
    render_to_response call

    """

    site_config = get_site_config(request)
    num_facet_items = site_config.num_filter_items_to_show
    custom_facet_counts = []

    num_jobs = site_config.num_job_items_to_show * 2
    default_jobs = helpers.get_jobs(custom_facets=settings.DEFAULT_FACET,
                                    exclude_facets=settings.FEATURED_FACET,
                                    jsids=settings.SITE_BUIDS)
    jobs_count = get_total_jobs_count()

    featured_jobs = helpers.get_featured_jobs()

    (num_featured_jobs, num_default_jobs, _, _) = helpers.featured_default_jobs(
        featured_jobs.count(), default_jobs.count(),
        num_jobs, site_config.percent_featured)

    featured = settings.SITE.featured_companies.all()
    # Because we're getting the featured company information from the SQL
    # database instead of Solr, we need to append the generated feature
    # slabs to the rest of the counts.
    featured_counts = [(item.company_slug+'/careers::'+item.name,
                        item.associated_jobs()) for item in featured]

    all_counts = default_jobs.add_facet_count(featured_jobs).get('fields')
    all_counts['featured_slab'] = featured_counts

    # Build a list of Company objects of current members that's the intersection
    # of all member companies and the companies returned in the Solr query
    all_buids = [buid[0] for buid in all_counts['buid']]
    members = Company.objects.filter(member=True)
    members = members.filter(job_source_ids__in=all_buids)

    if site_config.browse_facet_show:
        cust_facets = get_custom_facets(request)
        custom_facet_counts = helpers.combine_groups(cust_facets)

    ga = settings.SITE.google_analytics.all()

    home_page_template = site_config.home_page_template

    # The carousel displays the featured companies if there are any, otherwise
    # it displays companies that were returned in the Solr query and are members
    billboard_templates = ['home_page/home_page_billboard.html',
                           'home_page/home_page_billboard_icons_top.html']
    if home_page_template in billboard_templates:
        billboard_images = (settings.SITE.billboard_images.all())
        company_images = helpers.company_thumbnails(featured) if featured else \
            helpers.company_thumbnails(members)
        company_images_json = json.dumps(company_images, ensure_ascii=False)
    else:
        billboard_images = []
        company_images = None
        company_images_json = None

    widgets = helpers.get_widgets(request, site_config, all_counts,
                                  custom_facet_counts, featured=bool(featured))

    data_dict = {
        'default_jobs': default_jobs[:num_default_jobs],
        'featured_jobs': featured_jobs[:num_featured_jobs],
        'total_jobs_count': jobs_count,
        'widgets': widgets,
        'item_type': 'home',
        'base_path': request.path,
        'facet_blurb': False,
        'google_analytics': ga,
        'site_name': settings.SITE_NAME,
        'site_title': settings.SITE_TITLE,
        'site_heading': settings.SITE_HEADING,
        'site_tags': settings.SITE_TAGS,
        'site_description': settings.SITE_DESCRIPTION,
        'host': str(request.META.get("HTTP_HOST", "localhost")),
        'site_config': site_config,
        'build_num': settings.BUILD,
        'company_images': company_images,
        'company_images_json': company_images_json,
        'billboard_images': billboard_images,
        'featured': str(bool(featured)).lower(),
        'filters': {},
        'view_source': settings.VIEW_SOURCE}

    return render_to_response(home_page_template, data_dict,
                              context_instance=RequestContext(request))


class HomePage(FallbackBlockView):
    page_type = Page.HOME_PAGE

    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)
        self.fallback = home_page



@custom_cache_page
@home_page_check
def company_listing(request, alpha=None, group=None):
    """
    Generates the company listings for all, featured, and member company pages.

    Inputs:
        :request:   django request object
        :alpha:     alpha numeric key character for sorting
        :group:     type of company list to return

    Returns:
        render_to_reponse object

    """
    site_config = get_site_config(request)
    jobs_count = get_total_jobs_count()
    custom_facets = settings.DEFAULT_FACET
    featured = SeoSite.objects.get(id=settings.SITE_ID).\
               featured_companies.all()

    if group == 'featured':
        companies = featured
    else:
        sqs = helpers.sqs_apply_custom_facets(custom_facets)
        sqs = helpers._sqs_narrow_by_buid_and_site_package(sqs)
        counts = sqs.facet("buid").facet_limit(-1).fields(['buid']).\
                 facet_mincount(1).facet_counts()
        buids = [item[0] for item in counts['fields']['buid']]

        # Some companies are associated with multiple BUIDs, so we use distinct()
        companies = Company.objects.filter(job_source_ids__in=buids).\
            exclude(company_slug='').distinct()

        if group == 'member':
            companies = companies.filter(member=True)

    # Get ordered list of first character of company names (used to determine
    # what buttons to display).
    alpha_filters = set()
    for co in companies:
        if len(alpha_filters) == 27:
            break
        alpha_filters.add(co.company_slug[0] if co.company_slug[0].isalpha()
                             else '0-9')

    # Move the '0-9' filter to the back of the list if it is present. This does
    # two things--a letter will always be selected on the root page, and the 0-9
    # button appears after the letters on the web page.
    alpha_filters = sorted(alpha_filters)
    if alpha_filters and alpha_filters[0] == '0-9':
        alpha_filters = alpha_filters[1:] + alpha_filters[:1]

    # handle "root" page
    if alpha is None and group != 'featured':
        try:
            alpha = alpha_filters[0]
        except IndexError:
            alpha = "a" # fail gracefully if the page has ZERO companies

    # filter by alpha, i.e. .../all|member|featured-companies/<<alpha>>/
    # unless it's featured companies, then display all of them
    if group == 'featured':
        filtered_companies = list(companies)
    elif alpha == "0-9":
        filtered_companies = [co for co in companies
                              if co.company_slug[0].isdigit()]
    else:
        filtered_companies = [co for co in companies
                              if co.company_slug.startswith(alpha)]

    filtered_companies.sort(key=lambda co: co.company_slug)

    company_data = helpers.company_thumbnails(filtered_companies,
                                              use_canonical=False)

    if company_data:
        co_count = len(company_data)
        column_count = co_count // 3 if co_count % 3 == 0 else co_count // 3 + 1
    else:
        column_count = None

    data_dict = {
        'site_config': site_config,
        'site_name': settings.SITE_NAME,
        'site_title': settings.SITE_TITLE,
        'site_heading': settings.SITE_HEADING,
        'site_tags': settings.SITE_TAGS,
        'site_description': settings.SITE_DESCRIPTION,
        'company_data': company_data,
        'column_count': column_count,
        'total_jobs_count': jobs_count,
        'alpha_filters': alpha_filters,
        'alpha': alpha,
        'featured': str(bool(featured)).lower(),
        'group': group,
        'build_num' : settings.BUILD,
        'view_source' : settings.VIEW_SOURCE
    }

    return render_to_response('all_companies_page.html', data_dict,
                              context_instance=RequestContext(request))


def solr_ac(request):
    """Populate the searchbox autocomplete."""

    lookup_type = request.GET.get('lookup')
    term = request.GET.get('term')
    sqs = DESearchQuerySet().facet_mincount(1).facet_sort("count").facet_limit(15)
    sqs = helpers._sqs_narrow_by_buid_and_site_package(sqs)
    # filter `sqs` by default facet, if one exists.
    sqs = helpers.sqs_apply_custom_facets(settings.DEFAULT_FACET, sqs=sqs)

    callback = request.GET.get('callback')
    if lookup_type == 'location':
        loc_fields = {'country': 'country',
                      'state': 'state',
                      'city': 'location'}

        for field in loc_fields:
            sqs = sqs.facet(loc_fields[field])
        # mfac = multi field auto complete
        sqs = sqs.mfac(fields=['%s_ac__contains' % f for f in loc_fields],
                       fragment=helpers._clean(term), lookup='__contains')

        if sqs.facet_counts():
            res = reduce(operator.add, [v for k,v in
                                        sqs.facet_counts()['fields'].items()])
        else:
            res = []
    elif lookup_type == 'title':
        sqs = sqs.facet('title').autocomplete(title_ac=helpers._clean(term))
        # title_ac__exact - from haystack API (autocomplete)
        if sqs.facet_counts():
            res = sqs.facet_counts()['fields']['title']
        else:
            res = []
    else:
        res = []

    res = json.dumps([{lookup_type: i[0], 'jobcount': str(i[1])} for i in res])
    jsonpres = "{jsonp}({res})".format(jsonp=callback, res=res)
    return HttpResponse(jsonpres, content_type="application/json")


def v2_redirect(request, v2_redirect=None, country=None, state=None, city=None,
                onet=None):
    v2_redirect_kwargs = {}
    try:
        jobs = DESearchQuerySet();
        if v2_redirect == 'country' and country:
            v2_redirect_kwargs['country_short'] = country.lower()
            url = 'nav_country_slug'
        elif v2_redirect == 'state' and state:
            slugs = jobs.filter(stateSlug=slugify(state.replace(
                                            '_','-')))\
                                        .values('stateSlug', 'country_short')[0]
            v2_redirect_kwargs = {'state_slug': slugs['stateSlug'],
                                  'country_short': slugs['country_short']\
                                                   .lower()}
            url = 'nav_state_slug'
        elif v2_redirect == 'city' and state and city:
            slugs = jobs.filter(stateSlug=slugify(state.replace(
                                            '_','-')))\
                                        .filter(citySlug=slugify(city.replace(
                                            '_','-')))\
                                        .values('citySlug', 'stateSlug',
                                                'country_short')[0]
            v2_redirect_kwargs = {'city_slug': slugs['citySlug'],
                                  'state_slug': slugs['stateSlug'],
                                  'country_short': slugs['country_short']\
                                                   .lower()}
            url = 'nav_city_slug'
        elif v2_redirect == 'city-country' and country and city:
            v2_redirect_kwargs = {'city_slug': slugify(city.replace('_','-')),
                                  'state_slug': 'none',
                                  'country_short': country.lower()}
            url = 'nav_city_slug'
        else:
            url = 'home'
            LOG.debug("V2 redirect to home page", extra={
                'view': 'v2_redirect',
                'data': {
                    'request': request
                }
            })
    except IndexError:
        url = 'home'
        LOG.debug("V2 redirect to home page from IndexError", extra={
            'view': 'v2_redirect',
            'data': {
                'request': request
            }
        })
    return redirect(url, permanent=True, **v2_redirect_kwargs)


@csrf_exempt
@sns_json_message
def send_sns_confirm(response):
    """
    Called when a job feed file is ready to be imported. Calls celery update
    tasks.

    """
    # Postajob buids and state job bank buids
    allowed_buids = [1228, 5480] + range(2650,2704)

    LOG.info("sns received for SEOXML")
    if response:
        if response['Subject'] != 'END':
            buid = response['Subject']
            if int(buid) in allowed_buids:
                LOG.info("Creating update_solr task for %s" % buid)
                set_title = helpers.create_businessunit(int(buid))
                task_update_solr.delay(buid, force=True, set_title=set_title)
            else:
                LOG.info("Skipping update_solr for %s because it is not in the allowed buids list." % buid)


def new_sitemap_index(request):
    """
    Generates the sitemap index page, which instructs the crawler how to
    get to every other page.

    """
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    midnight = datetime.time.max
    #The latest date/time in sitemaps is yesterday, midnight (time.max)
    latest_datetime = datetime.datetime.combine(yesterday, midnight)
    # Number of days to go back from today.
    history = 30
    # Populate a list of datetime.datetime objects representing today's date
    # as well as one for each day going back 'history' days.
    dates = [latest_datetime - datetime.timedelta(days=i) for i in xrange(history)]
    earliest_day = (latest_datetime - datetime.timedelta(days=history)).date()
    datecounts = DateSitemap().numpages(startdate=earliest_day,
                                        enddate=latest_datetime)
    sitemaps = {}

    for date in dates:
        dt = datetime.date(*date.timetuple()[0:3]).isoformat()
        sitemaps[dt] = {'sitemap': DateSitemap(), 'count': datecounts[dt]}
    current_site = Site.objects.get_current()
    protocol = request.is_secure() and 'https' or 'http'

    #List of tuples: (sitemap url, lastmod date)
    sites_dates = []
    for date in sorted(sitemaps.keys(), reverse=True):
        pages = sitemaps[date]['count']
        sitemap_url = urlresolvers.reverse('sitemap_date',
                                           kwargs={'jobdate': date})
        sites_dates.append(('%s://%s%s' % (protocol, current_site.domain,
                                           sitemap_url),
                            date))
        if pages > 1:
            for page in xrange(2, pages+1):
                sites_dates.append(('%s://%s%s?p=%s' % (protocol,
                                                        current_site.domain,
                                                        sitemap_url, page),
                                    date))

    xml = loader.render_to_string('sitemaps/sitemap_index_lastmod.xml',
                                  {'sitemaps': sites_dates})
    return HttpResponse(xml, content_type='application/xml')


def new_sitemap(request, jobdate=None):
    page = request.GET.get("p", 1)
    fields = ['title', 'location', 'uid', 'guid']
    sitemaps = {
        jobdate: DateSitemap(page=page, fields=fields, jobdate=jobdate)
    }
    maps, urls = [], []
    if jobdate:
        if jobdate not in sitemaps:
            raise Http404("No sitemap available for job date: %r" % jobdate)
        maps.append(sitemaps[jobdate])
    else:
        maps = sitemaps.values()

    for site in maps:
        try:
            urls.extend(site.get_urls())
        except EmptyPage:
            raise Http404("Page %s empty" % page)
        except PageNotAnInteger:
            raise Http404("No page '%s'" % page)
    xml = smart_str(loader.render_to_string('sitemap.xml', {'urlset': urls}))
    return HttpResponse(xml, content_type='application/xml')


def get_group_sites(request):
    if request.method == u'GET':
        GET = request.GET
        group_id = GET.__getitem__(u'groupId')
        sites = SeoSite.objects.filter(group__id__exact=group_id)\
                               .values('id', 'domain')
        json = simplejson.dumps(list(sites))
        return HttpResponse(json, content_type='application/json')


def get_group_relationships(request):
    """
    This view is called by seosite.js. The purpose is to filter items in
    the admin page for various inline model admins.

    Inputs:
    :request: Django request object

    Returns
    A Django-formed HTTP response of MIME type 'application/json'.
    :json: A JSON string containing querysets filtered by a particular group.

    """
    if request.method == u'GET':
        GET = request.GET
        group_id = GET.get(u'groupId')
        obj_id = GET.get(u'objId')
        if obj_id == "add":
            obj_id = None

        site = get_object_or_404(SeoSite, id=obj_id)
        # QuerySets can't be JSON serialized so we'll coerce this to a list
        configs = list(Configuration.objects.filter(group__id=group_id)\
                                            .values('id', 'title'))
        ga_qs = GoogleAnalytics.objects.filter(group__id=group_id)\
                                       .values('id', 'web_property_id')
        google_analytics = [{'id': g['id'], 'title': g['web_property_id']}
                            for g in ga_qs]

        try:
            site = SeoSite.objects.get(id=obj_id)
        except SeoSite.DoesNotExist:
            selected = {
                'configurations': [],
                'google_analytics': []
            }
        else:
            configurations = site.configurations.values_list('id', flat=True)
            ga = site.google_analytics.values_list('id', flat=True)
            selected = {
                'configurations': [c for c in configurations],
                'google_analytics': [g for g in ga]
            }

        view_data = {
            'configurations': configs,
            'google_analytics': google_analytics,
            'selected': selected
        }
        json = simplejson.dumps(view_data)
        return HttpResponse(json, content_type='application/json')


def moc_index(request):
    """
    Handles requests from the veteran search field.

    Inputs:
    :request: the request object. It contains a term that is either a list of
    keywords a single phrase, which is denoted by the use of quotes as wrappers.

    Returns:
    json httpResponse object

    """
    # Search records for matching values.
    # Matches on occupations code, military description, and civilian
    # description.

    t = request.REQUEST['term']

    # provide capability for searching exact multi-word searches encased
    # in quotes
    if t.startswith('"') and t.endswith('"'):
        t = t.split('"')[1]
        term_list = [t]
    else:
        term_list = t.split()

    callback = request.GET.get('callback')
    args = [_moc_q(term) for term in term_list]

    data_set = moc_models.MocDetail.objects.filter(
        moc__isnull=False, *args).distinct().order_by('primary_value')[:15]

    res = json.dumps([_moc_json(i) for i in data_set])
    jsonpres = "{jsonp}({res})".format(jsonp=callback, res=res)
    return HttpResponse(jsonpres, content_type="application/json")


def _moc_q(term):
    """
    Return a single Q object that encapsulates a query for 'term' in
    'fields'.

    Input:
    :term: The auto-complete term passed in from the search box.

    Returns:
    Multiple Q objects combined into a single one using bitwise OR.

    """

    fields = ["primary_value", "military_description", "civilian_description"]
    q = [Q((field+"__icontains", term)) for field in fields]
    return reduce(operator.or_, q)


def _moc_json(detail):
    """
    Yields a dictionary suitable for serialization to JSON containing the
    data needed to render autocomplete results in the dropdown on the
    search boxes.

    Input:
    :detail: A single MocDetail object

    Returns:
    A dictionary like `{'label': <MOC info label>, 'value': <MOC code>}`

    """
    branches = {
        "a": "army",
        "c": "coast-guard",
        "f": "air-force",
        "n": "navy",
        "m": "marines"
    }
    value = detail.primary_value
    civ = detail.civilian_description
    branch = branches[detail.service_branch].capitalize()
    mil = detail.military_description
    moc_id = detail.moc.id
    label = "%s - %s (%s - %s)" % (value, civ, branch, mil)
    return {'label': label, 'value': value, 'moc_id': moc_id}


def dseo_404(request, the_job=None, job_detail=False):
    """
    Handles 404 page not found errors. the_job and job_detail are only passed
    if this is an expired job, which should almost never happen with the new
    import engine that is in place with 4.2

    Inputs:
    :request: Django request object
    :the_job: if there is a job associated with the path, get its info.
    :job_detail: detail info for the above job

    Returns:
    HttpResponseNotFound call

    """
    jobs_count = get_total_jobs_count()
    data_dict = {
        'total_jobs_count': jobs_count,
        'path': request.path,
        'domain': 'http://' + request.get_host(),
        'jobdata': {},
        'referer': request.META.get('HTTP_REFERER'),
        'site_name': settings.SITE_NAME,
        'site_title': settings.SITE_TITLE,
        'site_heading': settings.SITE_HEADING,
        'site_tags': settings.SITE_TAGS,
        'site_description': settings.SITE_DESCRIPTION,
        'build_num': settings.BUILD,
        'view_source': settings.VIEW_SOURCE
    }

    if job_detail and the_job:
        data_dict['jobdata'].update({'jobtitle': the_job.title,
                                     'joblocation': the_job.location})

    return HttpResponseNotFound(loader.render_to_string(
        'dseo_404.html', data_dict,
        context_instance=RequestContext(request)))


class Dseo404(FallbackBlockView):
    page_type = Page.ERROR_404

    def __init__(self, **kwargs):
        super(Dseo404, self).__init__(**kwargs)
        self.fallback = dseo_404


def dseo_500(request):
    """
    Handles server errors gracefully.

    Inputs:
    :request: the django request object.

    Returns:
    HttpResponseServerError call

    """

    jobs_count = get_total_jobs_count()
    data_dict = {
        'total_jobs_count': jobs_count,
        'path': request.path,
        'domain': 'http://%s' % request.get_host(),
        'referer': request.META.get('HTTP_REFERER'),
        'site_name': settings.SITE_NAME,
        'site_title': settings.SITE_TITLE,
        'site_heading': settings.SITE_HEADING,
        'site_tags': settings.SITE_TAGS,
        'site_description': settings.SITE_DESCRIPTION,
        'build_num': settings.BUILD,
        'view_source': settings.VIEW_SOURCE
    }
    return HttpResponseServerError(loader.render_to_string(
                                   'dseo_500.html', data_dict,
                                   context_instance=RequestContext(request)))


@home_page_check
@protected_site
def search_by_results_and_slugs(request, *args, **kwargs):
    filters = helpers.build_filter_dict(request.path)

    redirect_url = helpers.determine_redirect(request, filters)
    if redirect_url:
        return redirect_url

    query_path = request.META.get('QUERY_STRING', None)
    moc_id_term = request.GET.get('moc_id', None)
    q_term = request.GET.get('q', None)
    sort_order = request.GET.get('sort', 'relevance')
    if sort_order not in helpers.sort_order_mapper.keys():
        sort_order = 'relevance'

    facet_blurb_facet = None
    ga = settings.SITE.google_analytics.all()
    sitecommit_str = helpers.make_specialcommit_string(settings.COMMITMENTS.all())
    site_config = get_site_config(request)
    num_jobs = int(site_config.num_job_items_to_show) * 2

    custom_facet_counts = []
    if site_config.browse_facet_show:
        cf_count_tup = get_custom_facets(request, filters=filters,
                                         query_string=query_path)

        if not filters['facet_slug']:
            custom_facet_counts = cf_count_tup
        else:
            facet_slugs = filters['facet_slug'].split('/')
            active_facets = helpers.standard_facets_by_name_slug(facet_slugs)
            custom_facet_counts = [(facet, count) for facet, count
                                   in cf_count_tup
                                   if facet not in active_facets]

            # Set the facet blurb only if we have exactly one
            # CustomFacet applied.
            if len(active_facets) == 1 and active_facets[0].blurb:
                facet_blurb_facet = active_facets[0]

    # Text uses html_description instead of just description.
    fl = list(helpers.search_fields)
    index = fl.index('description')
    fl.pop(index)
    # We use the html_description to show highlighted snippets of the
    # description that match the search term. If there is no search
    # term there's no reason to even get the html_description.
    if q_term:
        fl.append('html_description')

    default_jobs, featured_jobs, facet_counts = helpers.jobs_and_counts(
        request, filters, num_jobs, fl=fl)

    total_featured_jobs = featured_jobs.count()
    total_default_jobs = default_jobs.count()

    (num_featured_jobs, num_default_jobs, _, _) = helpers.featured_default_jobs(
        total_featured_jobs, total_default_jobs,
        num_jobs, site_config.percent_featured)

    if not facet_counts:
        return redirect("/")

    if num_default_jobs == 0 and num_featured_jobs == 0 and not query_path:
        return redirect("/")

    default_jobs = default_jobs[:num_default_jobs]
    featured_jobs = featured_jobs[:num_featured_jobs]

    jobs = list(itertools.chain(featured_jobs, default_jobs))
    if query_path:
        for job in jobs:
            helpers.add_text_to_job(job)
    
    breadbox = Breadbox(request.path, filters, jobs, request.GET)

    company_data = helpers.get_company_data(filters)

    widgets = helpers.get_widgets(request, site_config, facet_counts,
                                  custom_facet_counts, filters=filters)

    location_term = breadbox.location_display_heading()
    moc_term = breadbox.moc_display_heading()
    if not location_term:
        location_term = '\*'
    if not moc_term:
        moc_term = '\*'

    results_heading = helpers.build_results_heading(breadbox)
    breadbox.job_count = intcomma(total_default_jobs + total_featured_jobs)
    count_heading = helpers.build_results_heading(breadbox)

    data_dict = {
        'breadbox': breadbox,
        'build_num': settings.BUILD,
        'company': company_data,
        'count_heading': count_heading,
        'default_jobs': default_jobs,
        'facet_blurb_facet': facet_blurb_facet,
        'featured_jobs': featured_jobs,
        'filters': filters,
        'google_analytics': ga,
        'host': str(request.META.get("HTTP_HOST", 'localhost')),
        'location_term': location_term,
        'max_filter_settings': settings.ROBOT_FILTER_LEVEL,
        'moc_id_term': moc_id_term if moc_id_term else '\*',
        'moc_term': moc_term,
        'num_filters': len([k for (k, v) in filters.iteritems() if v]),
        'total_jobs_count': get_total_jobs_count(),
        'results_heading': results_heading,
        'search_url': request.path,
        'site_commitments': settings.COMMITMENTS,
        'site_commitments_string': sitecommit_str,
        'site_config': site_config,
        'site_description': settings.SITE_DESCRIPTION,
        'site_heading': settings.SITE_HEADING,
        'site_name': settings.SITE_NAME,
        'site_tags': settings.SITE_TAGS,
        'site_title': settings.SITE_TITLE,
        'sort_fields': helpers.sort_fields,
        'sort_order': sort_order,
        'title_term': q_term if q_term else '\*',
        'view_source': settings.VIEW_SOURCE,
        'widgets': widgets,
    }

    return render_to_response('job_listing.html', data_dict,
                              context_instance=RequestContext(request))


class SearchResults(FallbackBlockView):
    page_type = Page.SEARCH_RESULTS

    def __init__(self, **kwargs):
        super(SearchResults, self).__init__(**kwargs)
        self.fallback = search_by_results_and_slugs

    def set_page(self, request):
        if request.user.is_authenticated() and request.user.is_staff:
            no_results_pages = Page.objects.filter(page_type=Page.NO_RESULTS,
                                                   sites=settings.SITE)
        else:
            no_results_pages = Page.objects.filter(page_type=Page.NO_RESULTS,
                                                   sites=settings.SITE,
                                                   status=Page.PRODUCTION)

        if no_results_pages.exists():
            jobs_and_counts = context_tools.get_jobs_and_counts(request)

            default_jobs = jobs_and_counts[0]
            featured_jobs = jobs_and_counts[2]

            if not default_jobs and not featured_jobs:
                self.page_type = Page.NO_RESULTS
        return super(SearchResults, self).set_page(request)


def urls_redirect(request, guid, vsid=None, debug=None):
    if vsid is None:
        vsid = '20'

    if debug is None:
        debug = ''

    site = getattr(settings, 'SITE', None)
    if site is None:
        site = Site.objects.get(domain='www.my.jobs')
    qs = QueryDict(request.META['QUERY_STRING'], mutable=True)
    qs['my.jobs.site.id'] = site.pk
    qs = qs.urlencode()
    return HttpResponseRedirect('http://my.jobs/%s%s%s?%s' %
                                (guid, vsid, debug, qs))


@csrf_exempt
def post_a_job(request):
    data = request.REQUEST
    key = data.get('key')

    if settings.POSTAJOB_API_KEY != key:
        resp = {
            'error': 'Unauthorized',
        }
        resp = json.dumps(resp)
        return HttpResponse(resp, content_type='application/json', status=401)

    jobs_to_add = data.get('jobs')
    if jobs_to_add:
        jobs_to_add = json.loads(jobs_to_add)
        jobs_to_add = [transform_for_postajob(job) for job in jobs_to_add]
        jobs_added = add_jobs(jobs_to_add)
    else:
        jobs_added = 0
    resp = {'jobs_added': jobs_added}
    return HttpResponse(json.dumps(resp), content_type='application/json')


@csrf_exempt
def delete_a_job(request):
    data = request.REQUEST
    key = data.get('key')
    if settings.POSTAJOB_API_KEY != key:
        resp = {
            'error': 'Unauthorized',
        }
        resp = json.dumps(resp)
        return HttpResponse(resp, content_type='application/json', status=401)

    guids_to_clear = data.get('guids')
    if guids_to_clear:
        guids_to_clear = guids_to_clear.split(',')
    jobs_deleted = delete_by_guid(guids_to_clear)

    resp = {'jobs_deleted': jobs_deleted}
    return HttpResponse(json.dumps(resp), content_type='application/json')


@csrf_exempt
@sns_json_message
def confirm_load_jobs_from_etl(response):
    """
    Called when a job source is ready to be imported. Calls celery update
    tasks.

    """

    blocked_jsids = ('4051c882-fa2c-4c93-9db5-91c9add39def',
                     '10f89212-654e-4ee5-8655-2bbb4770252f',
                     'e6fa8adb-07c9-4b15-87ad-5816c3968d43',
                     '8667bd35-c6d3-4008-8b62-36d6b6e3bb62',
                     'c94ddf73-23c8-4b6c-ad5a-a98b5f2a04b0',
                     '5de582a0-cab5-45f8-88a8-a31f7fe03025',
                     '72690d11-b3fc-403c-8726-c80883e27774',
                     'e0fe5671-c591-40d4-bba9-f0d8542882e2',
                     'dd5fd646-655b-4867-8784-700bb5c6315b',
                     'c4d56d17-7b35-436a-8871-80d8c2e37bf9',
                     'ff794484-8f24-4bdc-96e3-227c9dec2c26',
                     'cd7fc92a-9bff-4bbd-a10a-ffd6a57a93a1',
                     '3388e1e9-8292-4d6f-a5ee-c4ed2bae59a4',
                     '868672a0-c22b-4337-9dcc-2fa5b6671592',
                     '09ae740c-36d8-432d-bc84-de538dbac8fd',
                     '03516574-c452-45ab-b217-8ea0357be747',
                     '1b0e4f3b-a9e1-40b9-8c8b-85a65882c2a3',
                     'de0762b3-698b-4a3b-92d2-388144edb15a',
                     '77e1b0eb-4017-44b7-ab9d-898d35390b81',
                     '905ad700-0a73-4da1-8bf5-b12bf6ba89a7',
                     'f39aaaf4-e126-4d53-bdf3-98831f45d731',
                     '1f78a1c6-1ced-4d80-b338-1c3bd8ac57a7',
                     '4d9330b3-8ca8-41ef-8ca2-305da6ddc5f0',
                     'aeb6cdb4-1b02-4bab-b398-4d3980097659',
                     'c20f2c86-bd08-4cce-af94-b3339944676e',
                     '249308c5-623b-41b9-9364-2589e49b5e02',
                     '27f0d51d-2882-4168-bfca-cb415f666fb3',
                     '8d506b65-f911-449e-bad8-c308a196e1c0',
                     'c6203550-2435-4137-9c11-b0710f3ef4cf',
                     '682deefb-fde9-4de2-8985-13371d04a8ff',
                     'c8bfb1b1-398a-46a4-a1f4-fbdb5354ee78',
                     '769ca60a-f4e7-446d-b2ba-b66a5a3e9313',
                     '7ecfcde8-b7e1-4bb1-a671-b52d729903b5',
                     '817d2b90-9299-4ef6-b484-46208ce69e19',
                     '00152da3-1abe-458e-8895-121ca9008cf7',
                     '94d95b97-24e4-4d98-8ecf-1dce6202c523',
                     'ccc31e40-a65f-46b0-a194-b0517c33a7f6',
                     'be4dcd74-ff51-4f99-8057-55a876b3ce56',
                     '15079de2-7de2-4191-b8cf-7924036b4b97',
                     'c8d8da8c-542f-4620-b90b-4a37d55d659f',
                     '66cbd5e6-c86b-4659-b80c-11aa5a5fa6a7',
                     '265357bd-a619-40b7-b9bc-9674d6e96400',
                     '7d6ea31f-e36d-43e7-b68e-d9dbd45446f7',
                     'b3c58f53-144a-4de7-807b-8fe140259d7f',
                     '23322abe-6faf-4303-b08b-713e5127e019',
                     'bedee5c5-a9ca-459f-899b-29482712d7c9',
                     '69f485d0-40d5-430f-a5eb-6221ee14092d',
                     'b0c01590-0085-4ab5-b0b0-27149fa0fb4a',
                     '536dcdbb-2a88-40d8-bf68-8630306c2818',
                     'ad875783-c49e-49ff-b82a-b0538026e089',
                     '0ab41358-8323-4863-9f19-fdb344a75a35',)

    LOG.info("sns received for ETL")

    if response:
        if response.get('Subject', None) != 'END':
            msg = json.loads(response['Message'])
            jsid = msg['jsid']
            buid = msg['buid']
            name = msg['name']
            prio = msg["priority"]
            if jsid.lower() in blocked_jsids:
                LOG.info("Ignoring sns for %s", jsid)
                return None
            LOG.info("Creating ETL Task (%s, %s, %s" % (jsid, buid, name))
            if int(prio) == 1:
                task_priority_etl_to_solr.delay(jsid, buid, name)
            else:
                task_etl_to_solr.delay(jsid, buid, name)


@staff_member_required
def test_markdown(request):
    """
    Gets an hrxml formatted job file and displays the job
    detail page that it would generate.

    """
    class TempJob:
        """
        Creates a job object from a dictionary so the dict can be used
        in the job_detail template.

        """
        def __init__(self, **entries):
            self.__dict__.update(entries)

    if request.method == 'POST':
        form = UploadJobFileForm(request.POST, request.FILES)
        if form.is_valid():
            xml = etree.fromstring(request.FILES['job_file'].read())
            # Business Unit is usually specified by the sns message, but since
            # there's no sns message and it's pretty unecessary to force
            # the user to specify the business unit, use the DE one.
            bu = BusinessUnit.objects.get(id=999999)
            job_json = hr_xml_to_json(xml, bu)
            job_json['buid'] = bu
            data_dict = {
                'the_job': TempJob(**job_json)
            }
            return render_to_response('job_detail.html', data_dict,
                                      context_instance=RequestContext(request))
    else:
        form = UploadJobFileForm()
        data_dict = {
            'form': form,
        }
        return render_to_response('seo/basic_form.html', data_dict,
                                  context_instance=RequestContext(request))
