from collections import defaultdict
import datetime
from HTMLParser import HTMLParser
import logging
import math
import operator
from pysolr import SolrError
import urllib
from itertools import islice
from urlparse import urljoin, urlparse, parse_qs, parse_qsl

from django.conf import settings
from django.shortcuts import redirect
from django.template.defaultfilters import safe
from django.utils.html import strip_tags
from haystack.backends.solr_backend import SolrSearchQuery
from haystack.inputs import Raw
from haystack.query import SQ, EmptySearchQuerySet
from ordereddict import OrderedDict

from seo_pysolr import Solr
from seo.search_backend import DESearchQuerySet
from seo.models import BusinessUnit, Company
from seo.templatetags.seo_extras import facet_text, smart_truncate
from seo.filters import FacetListWidget, CustomFacetListWidget
from serializers import JSONExtraValuesSerializer
from moc_coding.models import Moc
from xmlparse import text_fields


# Because we don't want things like 'salted_date' in the url paramters,
# the terms we'll accept as a url parameter need to be mapped to the
# solr fields they're supposed to be sorting by.
sort_order_mapper = {
    'relevance': '-score',
    'date': '-salted_date',
    'new': '-date_new_exact',
    'updated': '-date_updated_exact'
}
sort_fields = ['relevance', 'date']


# Fields that populate the Solr "fl" parameter on searches that use
# get_jobs().
search_fields = ['apply_info', 'city', 'company', 'company_canonical_microsite',
                 'company_enhanced', 'company_exact', 'company_slab', 'country',
                 'country_short', 'date_new', 'date_updated',
                 'description', 'django_ct', 'django_id', 'guid', 'highlighted',
                 'id', 'is_posted', 'link', 'location',
                 'location_exact', 'reqid', 'score', 'state',
                 'state_short', 'text', 'title', 'title_exact', 'uid']


def standard_facets_by_name_slug(name_slugs):
    custom_facets = settings.STANDARD_FACET
    return [facet for facet in custom_facets
            if facet.name_slug in name_slugs]


def company_thumbnails(companies, use_canonical=True):
    """
    Generate company information used in the carousel, company modules,
    and company listing pages.

    Inputs:
    :companies: a list of Company objects
    :use_canonical: boolean indicating whether to use canonical url or
    /{{company}}/careers url

    Returns:
    A list of dictionaries including company name, canonical microsite,
    and logo data.

    """
    if companies:
        return [{'url': (co.canonical_microsite if
                         (co.canonical_microsite and use_canonical)
                         else "/" + co.company_slug + "/careers"),
                 'name': co.name,
                 'image': co.logo_url} for co in companies]
    else:
        return []


def build_filter_dict(slug_path):
    """
    Parses out the slug tags and associated values into key/value pairs.
    Slug tags are the keys, and values are values.

    Then, it maps values from the returned slug_dict to keys from
    settings.SLUG_TAGS

    General Format:
    {value_1}/{slug_tag_1}/{value_2}/{slug_tag_2}/.../{value_n}/{slug_tag_n}/

    Example:
        slug_path = "project-manager/jobs-in/usa/jobs/"

        The first list comprehension returns <dict>:
        {
            'jobs-in': 'project-manager',
            'jobs': 'usa'
        }

        Location values can span across multiple '/':
        i.e.- boston/ma/usa/jobs
                slug_tag = jobs
                value = boston/ma/usa

        So now we have:

        slugs_dict:
        {
            'jobs-in': 'project-manager',
            'jobs': 'usa'
        }

        And,

        settings.SLUG_TAGS:
        {
            'title_slug': '/jobs-in/',
            'location_slug': '/jobs/',
            'facet_slug': '/new-jobs/',
            'moc_slug': '/veteran-jobs/'
        }

        That get turned into this:

        Final Result:
        {
            'title_slug': 'project-manager',
            'location_slug': 'usa',
            'facet_slug': None,
            'moc_slug': None
        }

    """
    slug_value_list = settings.SLUG_TAG_PARSING_REGEX.findall(slug_path)
    slugs_dict = dict([(key, value.strip('/')) for (value, key) in
                       slug_value_list])
    #We use an ordered dict to ensure that the the string representation of
    #identicial filters are equal if they have the same filters
    return OrderedDict([(key, slugs_dict.get(value.strip('/')))
                        for key, value in sorted(settings.SLUG_TAGS.items())])


def canonical_path_from_filter_dict(filters):
    """Builds a canonical url path from a dictionary of filter terms"""
    term_paths = [''.join([filters[key], slug]) for key, slug in
                  settings.SLUG_TAGS.items() if slug is not None]
    return ''.join(term_paths)


def build_results_heading(breadbox):
    """
    Builds a sensible, human-readable heading for the results page in the
    format of COMPANY Careers<br>(CUSTOM_SEARCH | "TITLE Jobs")("in LOCATION")

    :param breadbox: A Breadbox instance with all the breadcrumbs that should
                     appear in the heading already built.

    :return: A string containing the heading.

    """
    heading = []

    has_facet = bool(breadbox.custom_facet_breadcrumbs)
    has_title = bool(breadbox.title_breadcrumb)
    has_moc = bool(breadbox.moc_breadcrumbs)
    # breadbox.location_breadcrumbs accounts for both
    # the location data from the path and from the query parameters.
    # The heading is only built from the path data, so we have to
    # ignore any data passed in for location from the query parameters here.
    has_location = bool(breadbox.filters['location_slug'])
    has_count = bool(breadbox.job_count)

    if has_facet and not (has_title or has_moc):
        heading.append(breadbox.custom_facet_display_heading())

    if has_title:
        heading.append(breadbox.title_display_heading())
    elif not heading:
        if has_count:
            heading.append(unicode(breadbox.job_count))
        heading.append("Jobs")

    if has_location:
        heading.append("in %s" % breadbox.location_display_heading())

    return " ".join(heading)


def parse_location_slug(location_slug):
    """
    Location slug can take the form of these examples:
        boston/massachusettes/usa
        boston/none/usa
        none/none/usa

        massachusetts/usa

        /usa

    So it will have 1, 2, or 3 pieces to it. We'll return
    a dictionary with this form:

    locations = {
        "country": {value|None},
        "state": {value|None},
        "city": {value|None}
    }

    """

    locations = {
        "country_short": '',
        "state": '',
        "city": ''
    }
    # we want to strip leading/trailing backslashes
    location_slug = location_slug.strip('/')
    location_pieces = location_slug.split('/')
    location_length = len(location_pieces)
    # we have 3 conditions to check for:
    #     1, 2 or 3 location pieces
    if location_length == 3:
        # we possibly have all 3 location pieces
        locations["country_short"] = location_pieces[2]
        locations["state"] = location_pieces[1]
        locations["city"] = location_pieces[0]
    elif location_length == 2:
        # we possibly have:
        #     state and country
        locations["country_short"] = location_pieces[1]
        locations["state"] = location_pieces[0]
    else:
        # we only have the country
        locations["country_short"] = location_pieces[0]

    return locations


def parse_moc_slug(moc_slug):
    """
    Return {'moc': <moc_code>} dictionary.

    """
    moc_slug = moc_slug.strip('/').split('/')
    return {'moc': moc_slug[1]}


def get_nav_type(filters):
    """
    This method determines which type of primary nav we should build.
    It's pretty heavy on business logic, so it makes sense to keep
    it self contained within here.

    Business Logic:
        # if we have a moc_slug, build that nav
        # if we have a facet_slug, build that nav
        # else if we have a title_slug, build that nav
        # else if we have a location_slug, build that nav
            # if we have 3 location pieces, build city
            # if we have 2 location pieces, build state
            # if we have 1 piece, build country

    """
    nav_type = ''
    moc_slug = filters["moc_slug"]
    facet_slug = filters["facet_slug"]
    title_slug = filters["title_slug"]
    location_slug = filters["location_slug"]

    if moc_slug:
        nav_type = 'moc'
    elif facet_slug:
        nav_type = 'facet'
    elif title_slug:
        nav_type = 'title'
    elif location_slug:
        location_slug = location_slug.strip('/')
        location_pieces = location_slug.split('/')
        location_length = len(location_pieces)
        if location_length == 3:
            nav_type = 'city'
        elif location_length == 2:
            nav_type = 'state'
        else:
            nav_type = 'country'

    return nav_type


def job_breadcrumbs(job, company=False):
    """
    Generate breadcrumbs for job detail pages.
    Inputs:
        :job: Job document from Haystack
        :company: Boolean, set to True to include comapny information in output

    Outputs:
        A list of dictionaries for each field in the breadbox

    """
    fields = ['title', 'city', 'state', 'country']
    breadcrumbs = {}
    # A map to define what URL elements will compose a new URL when a
    # breadcrumb is selected. For instance, when a user clicks the
    # "State" breadcrumb, only the title and country (and company if the
    # site is configured to show companies) will be represented in the
    # destination URL.
    #
    # So each key in `dropmap` represents that type of breadcrumb. The
    # value of the key is a list of the elements that will comprise the
    # URL the user will be taken to if they click on that breadcrumb. For
    # the location-type breadcrumbs, the name represents the maximum
    # depth. So the 'city' breadcrumb would be e.g.
    # "fort-worth/texas/usa/jobs", while 'state' would be "texas/usa/jobs"
    # and so forth.
    dropmap = {'country': ['title'],
               'state': ['title', 'country'],
               'city': ['title', 'state'],
               'title': ['city']}
    attrs = {}

    if company:
        fields.append('company')

        for k in dropmap:
            dropmap[k].append('company')

        dropmap['company'] = ['title', 'city']

    for i in fields:
        slab = getattr(job, "%s_slab" % i)
        if slab:
            slab = slab.split("::")
        else:
            continue

        if i == "city":
            slab[1] = job.city or job.location

            if not job.state:
                dropmap['city'][dropmap['city'].index('state')] = 'country'

        attrs['%s' % i] = {'path': slab[0], 'display': slab[1]}

    for f, value in attrs.items():
        display = value["display"]

        # One of two things will happen here: If the job has a value in the
        # city or state attribute, that value will be set to display in the
        # template; if not, the city value -- ordinarily JUST the cityname --
        # will be set to the "City, ST" location field on the job document.
        if display != "None":
            up_slug = "/".join([attrs[k]['path'] for k in dropmap[f]])
            breadcrumbs[f] = {'path': "/" + up_slug + "/",
                              'display': display or getattr(job, f)}
    return breadcrumbs


def _page_title(crumbs):
    """Generates title for job detail page."""
    locs = filter(lambda x: x, [crumbs.get(loc) for loc in
                                ['city', 'state', 'country']])
    displays = [loc['display'] for loc in locs]
    loc_part = ", ".join(filter(lambda x: x, displays))
    if crumbs.get("company"):
        info_part = " ".join([crumbs['company']['display'],
                              crumbs['title']['display']])
    else:
        info_part = crumbs['title']['display']

    return " in ".join([info_part, loc_part])


def bread_box_company_heading(company_slug_value):
    # TODO write test to hit this logic
    if not company_slug_value:
        return None

    kwargs = {'title_slug': company_slug_value}
    business_unit = BusinessUnit.objects.filter(**kwargs)

    try:
        return business_unit[0].title
    except Exception:
        return None


def location_from_job(job, num_locations):
    try:
        if num_locations == 3:
            return job.location
        elif num_locations == 2:
            return job.state
        elif num_locations == 1:
            return job.country
    except IndexError:
        return None


def bread_box_location_heading(location_slug_value, jobs=None):
    if not location_slug_value:
        return None

    location_slug_value = location_slug_value.strip('/')
    location = None
    locations = location_slug_value.split('/')
    loc_length = len(locations)

    try:
        location = location_from_job(jobs[0], loc_length)
    except IndexError:
        # We don't have a job
        pass

    if not location:
        # We didn't have a valid job to pull the location, state,
        # or country from.
        sqs = DESearchQuerySet()
        jobs = filter_sqs_by_location(sqs, location_slug_value)[:1]
        try:
            location = location_from_job(jobs[0], loc_length)
        except IndexError:
            pass

    if not location:
        # Solr has no results for it at all either. Resort to
        # title casing the location term.
        location = " ".join(locations)
        location = location.replace('-', ' ').title()

    return location


def bread_box_moc_heading(moc_slug_value):
    if not moc_slug_value:
        return None

    moc_slug_value = moc_slug_value.strip('/')
    moc_pieces = moc_slug_value.split('/')
    moc_code = moc_pieces[1]
    branch = moc_pieces[2]

    try:
        moc = Moc.objects.get(code=moc_code, branch=branch)
    except (Moc.DoesNotExist, Moc.MultipleObjectsReturned):
        return None

    return moc.code + ' - ' + moc.title


def bread_box_title_heading(title_slug_value, jobs=None):
    if (not title_slug_value and not jobs) or not title_slug_value:
        return None

    if jobs:
        job = jobs[0]
        if title_slug_value == job.title_slug:
            return job.title
        else:
            for job in jobs:
                if title_slug_value == job.title_slug:
                    return job.title

    # Try searching solr for a matching title.
    conn = Solr(settings.HAYSTACK_CONNECTIONS['default']['URL'])
    try:
        search_terms = {
            'q': u'title_slug:%s' % title_slug_value,
            'fl': 'title, title_slug',
            'rows': 1,
        }
        res = conn.search(**search_terms)
    except SolrError:
        # Poorly formated title_slug_values can sometimes cause Solr errors.
        res = None

    if res and res.docs[0].get('title_slug') == title_slug_value:
        return res.docs[0]['title']
    else:
        if title_slug_value:
            return title_slug_value.replace('-', ' ').title()
        else:
            return None


def get_bread_box_headings(filters=None, jobs=None):
    """
    This function builds the 'bread box' titles that area seen
    in the right hand column on any page with filter criteria
    applied to it.

    Inputs:
        filters -- filters in use on the current path
        jobs -- solr/haystack jobs query object

    Returns:
        bread_box_title -- formatted page title

    """
    filters = filters or {}
    bread_box_headings = {}

    if filters and jobs:
        location_slug_value = filters.get('location_slug')
        location = bread_box_location_heading(location_slug_value, jobs)
        if location:
            bread_box_headings['location_slug'] = location

        title_slug_value = filters.get('title_slug')
        title = bread_box_title_heading(title_slug_value, jobs)
        if title:
            bread_box_headings['title_slug'] = title

        moc_slug_value = filters.get('moc_slug')
        moc = bread_box_moc_heading(moc_slug_value)
        if moc:
            bread_box_headings['moc_slug'] = moc

        company_slug_value = filters.get("company_slug")
        company = bread_box_company_heading(company_slug_value)
        if company:
            bread_box_headings['company_slug'] = company

    return bread_box_headings


def get_jobs(custom_facets=None, exclude_facets=None, jsids=None,
             default_sqs=None, filters={},  fields=None, facet_limit=250,
             facet_sort="count", facet_offset=None, mc=1,
             sort_order='relevance', fl=search_fields):
    """
    Returns 3-tuple containing a DESearchQuerySet object, a set of facet
    counts that have been filtered, and a set of unfiltered facet counts.

    The unfiltered facet count object is used by the primary nav box to
    build items and options.
    Inputs:
        :custom_facets: A list of saved searches (Custom Facets) to apply to
                        sqs. Defaults to site's default custom facets set in
                        Middleware
        :default_sqs: Starting search query set
        :filters: Dictionary of filter terms in field_name:search_term format
        The following inputs are Solr parameters.
        :facet_limit: max number of facets to return per field. -1=unlimited
        :facet_sort: How to sort facets
        :facet_offset: offset into the facet list
        :mc: mincount - Smallest facet size to return

    """
    if default_sqs is not None:
        sqs = default_sqs
    else:
        sqs = DESearchQuerySet()
    sqs = sqs_apply_custom_facets(custom_facets, sqs, exclude_facets)
    sqs = _sqs_narrow_by_buid_and_site_package(sqs, buids=jsids)
    # Limit the retrieved results to only fields that are actually needed.
    sqs = sqs.fields(fl)

    sqs = sqs.order_by(sort_order_mapper.get(sort_order, '-score'))

    #The boost function added to this search query set scales relevancy scores
    #by a factor of 1/2 at ~6 months (1.8e-11 ms) in all future queries
    sqs = sqs.bf('recip(ms(NOW/HOUR,salted_date),1.8e-9,1,1)')

    if fields:
        sqs = sqs.fields(fields)

    if facet_offset:
        sqs = sqs.facet_offset(facet_offset)

    if facet_limit > 0:
        sqs = sqs.facet_limit(facet_limit)

    sqs = sqs.facet_sort(facet_sort).facet_mincount(mc)
    sqs = sqs.facet("city_slab").facet("state_slab").facet("country_slab")\
             .facet("moc_slab").facet("title_slab").facet("full_loc")\
             .facet("company_slab").facet("buid").facet("mapped_moc_slab")

    # When get_jobs is called from job_listing_by_slug_tag, sqs already has site
    # default facets and filters from URL applied. The call to filter_sqs
    # concatenates the querystring (q=querystring) with itself,
    # adding + operators and causing parsing errors for more complex custom
    # facets. Can't remove now until we verify other views don't rely on
    # this call to filter_sqs.
    # Jason McLaughlin 09-07-2012
    return filter_sqs(sqs, filters)


def filter_sqs_by_location(sqs, location_slug):
    loc = parse_location_slug(location_slug)

    for k, v in loc.items():
        if v:
            if k == 'country_short':
                sqs = sqs.narrow('country_short:(%s)' % v.upper())
            elif k == 'state':
                if v != 'none':
                    sqs = sqs.narrow("state_slug:(%s)" % v)
            else:
                if v != 'none':
                    sqs = sqs.narrow("city_slug:(%s)" % v)
    return sqs


def filter_sqs(sqs, filters):
    """
    Filters a DESearchQuerySet based on the requested URL via
    build_filter_dict's URL-parsing algorithm. Returns a count of the
    results.

    This helper function enables accurate counts in the template when
    displaying number of results next to the Custom Facet(tm) name on the
    right-hand "Filter By x" column.

    """

    if filters.get('facet_slug'):
        facet_slugs = filters.get('facet_slug').split('/')
        custom_facets = standard_facets_by_name_slug(facet_slugs)
        # Apply each custom facet seperately so that we can guarantee the
        # search terms are ANDed together (via being their own seperate
        # fq parameters) rather than using the default operator for the
        # custom facet.
        for custom_facet in custom_facets:
            sqs = sqs_apply_custom_facets([custom_facet], sqs)

    _filters = filter(lambda x: filters.get(x) and x != 'facet_slug', filters)

    for f in _filters:
        if f == 'location_slug':
            sqs = filter_sqs_by_location(sqs, filters['location_slug'])

        elif f == 'moc_slug':
            t = filters[f]
            try:
                t = t.split('/')[1]
            except IndexError:
                pass
            if settings.SITE_BUIDS:
                sqs = sqs.narrow("mapped_moc_exact:(%s)" % _clean(t))
            else:
                sqs = sqs.narrow("moc_exact:(%s)" % _clean(t))
        elif f == 'company_slug':
            company = BusinessUnit.objects.filter(title_slug=filters[f])

            if not company:
                logging.error("No BusinessUnit found for title_slug %s" %
                              filters[f])
                sqs = sqs.narrow("company:(%s)" % filters[f])
            else:
                sqs = sqs.narrow('buid:(%s)' % ' OR '.join([str(c.id) for c
                                                            in company]))
        else:
            t = filters[f]
            sqs = sqs.narrow("title_slug:(%s)" % _clean(t))
    return sqs


def get_featured_jobs(*args, **kwargs):
    """
    Uses get_jobs to return a SearchQuerySet of featured jobs
    Passes arguments onto get_jobs, and overwrites custom_facets
    with site featured facets if they exist

    """
    if settings.FEATURED_FACET:
        kwargs.update(custom_facets=settings.FEATURED_FACET)
        featured_jobs = get_jobs(*args, **kwargs)
    else:
        featured_jobs = EmptySearchQuerySet()
    return featured_jobs


def featured_default_jobs(f, d, total, percent_f, offset=0):
    """
    Returns number of featured and default jobs to display based on their
    search query result counts, number of total jobs requested, and percent
    featured
    Inputs:
    :f: Integer number of jobs in featured search query set
    :d: Integer number of jobs in default search query set
    :total: Total number of jobs requested
    :percent_f: Percent of featured jobs to display

    Outputs:
    A tuple containing:
    :num_featured_jobs:
    :num_default_jobs:
    :f_offset:Start offset for featured query set, may be larger than f
    :d_offset:Start offset for default query set, may be larger than d

    If offsets aren't needed, Python convention is to use _ as
    an ignore placeholder in the packing tuple i.e.:
        (a,b,_,_) = featured_default_jobs()

    """
    if offset > 0:
        f_offset = int(math.ceil(offset*percent_f))
        f = f-f_offset

        #if f is negative, we add that many jobs to d_offset
        d_offset = offset - f_offset - min(0, f)
        d = d - d_offset
        f_offset = f_offset - min(0, d)
        f = f + min(0, d)
    else:
        f_offset = 0
        d_offset = 0
    f = max(0, f)
    d = max(0, d)

    #Fill percent_f of total from f
    num_featured_jobs = min(f, int(math.ceil(total * percent_f)))

    #Fill remaining total from d
    num_default_jobs = min(total - num_featured_jobs, d)
    num_default_jobs = max(0, num_default_jobs)

    #If total isn't filled, increase f
    num_featured_jobs = min(f, total-num_default_jobs)
    num_featured_jobs = max(0, num_featured_jobs)

    return (num_featured_jobs, num_default_jobs, f_offset, d_offset)


def _clean(term):
    return DESearchQuerySet().query.clean(term)


def combine_groups(custom_facet_counts, match_field='name'):
    """
    This function collapses/combines duplicate facets (based on
    CustomFacet.match_field) in custom_facet_counts into a single 2-tuple.

    Inputs:
    :custom_facet_counts: A list of 2-tuples, each consisting of a
                          seo.models.CustomFacet instance and a count
                          of the DESearchQuerySet results from that
                          instance, e.g.:
                          (<CustomFacet: Camber Instructors>, 25)
    :match_field: Items with equal values in match_field sum their counts in
                  a single returned tuple

    :returns: A list of (custom facet, count) tuples sorted by count.
    """

    # {<CustomFacet instance>: <count of items>}
    collapsed_custom_facet_counts = {}

    for facet, count in custom_facet_counts:
        field = getattr(facet, match_field)
        if facet not in collapsed_custom_facet_counts:
            collapsed_custom_facet_counts[field] = {
                'facet': facet,
                'count': count
            }
        else:
            collapsed_custom_facet_counts[field]['count'] += count

    custom_facet_counts = [(count_dict['facet'], count_dict['count'])
                           for count_dict in
                           collapsed_custom_facet_counts.values()]
    custom_facet_counts.sort(key=lambda x: -x[1])
    return custom_facet_counts or []


def sort_custom_facets_by_group(custom_facets):
    """
    Groups a list of custom facets based on the related SeoSiteFacet
    facet_group.

    :param custom_facets: A list of custom facets to be sorted.
    :return: A dictionary where the keys are the facet_groups and the
             values are a list of custom facets for that facet_group.

    """
    # Right now we know we only have these 3 facet_groups.
    grouped_facets = {1: [], 2: [], 3: []}

    for facet, count in custom_facets:
        cached_facets = getattr(settings, 'STANDARD_FACET', [])
        try:
            # Attempt to match the facet to a cached version, which
            # will have the facet_group already included.
            cached_facet = cached_facets[(cached_facets.index(facet))]
            facet_group = getattr(cached_facet, 'facet_group', 1)
        except (IndexError, ValueError):
            # If we can't match it to a cached version, do the lookup
            # manually.
            site_facet = facet.active_site_facet()
            if not site_facet:
                continue
            facet_group = site_facet.facet_group
        grouped_facets[facet_group].append((facet, count))
    return grouped_facets


def get_widgets(request, site_config, facet_counts, custom_facets,
                filters=None, featured=False):
    """
    Return a list of widget FacetListWidget objects to the home_page or
    job_list_by_slug_tag view, sorted by their browse order as set in the
    site config.

    """
    filters = filters or {}

    moc_field = 'mapped_moc' if settings.SITE_BUIDS else 'moc'
    if featured:
        types = [('featured', 1),
                 ('city', site_config.browse_city_order+1),
                 ('state', site_config.browse_state_order+1),
                 ('country', site_config.browse_country_order+1),
                 ('title', site_config.browse_title_order+1),
                 ('company', site_config.browse_company_order+1),
                 (moc_field, site_config.browse_moc_order+1)]
    else:
        types = [('city', site_config.browse_city_order),
                 ('state', site_config.browse_state_order),
                 ('country', site_config.browse_country_order),
                 ('title', site_config.browse_title_order),
                 ('company', site_config.browse_company_order),
                 (moc_field, site_config.browse_moc_order)]

    num_items = site_config.num_filter_items_to_show
    widgets = []
    for _type in types:
        w = FacetListWidget(request, site_config, _type[0],
                            facet_counts['%s_slab' % _type[0]][0:num_items*2],
                            filters)
        w.precedence = _type[1]
        widgets.append(w)
    if custom_facets:
        grouped_facets = sort_custom_facets_by_group(custom_facets)
        for facet_group, facets in grouped_facets.items():
            if facets:
                # Since all of the custom facets are already loaded on the
                # page (but hidden), pass in an arbitrarily large number
                # as the offset in order to avoid more requests for custom
                # facets to be made.
                offset = len(custom_facets)*10000

                # The facet widget must be generated "separately" from
                # location/title/moc widgets, since facet counts aren't
                # generated from the SearchIndex.
                search_widget = CustomFacetListWidget(request, site_config,
                                                      facets, filters,
                                                      facet_group,
                                                      offset=offset)
                search_widget.precedence = site_config.browse_facet_order
                widgets.append(search_widget)
    widgets.sort(key=lambda x: x.precedence)
    return widgets


def split_locs(facet):
    for f in facet:
        loc_tuples = f[0].split('@@')
        for atom in loc_tuples:
            loc_tuples[loc_tuples.index(atom)] = atom.split('::')
        facet[facet.index(f)] = dict(loc_tuples)

    return facet


def facet_data(jsids):
    sqs = DESearchQuerySet().facet_limit(-1).facet_sort("count").\
        facet_mincount(1)
    sqs = sqs.facet("full_loc").facet("title").facet("country").facet("state")
    sqs = _sqs_narrow_by_buid_and_site_package(sqs)
    return sqs.facet_counts()['fields']


def more_custom_facets(custom_facets, offset=0, num_items=0):
    """Generates AJAX response for more custom_facets."""
    custom_facets = combine_groups(custom_facets)[offset:offset+num_items]
    items = []
    for i in custom_facets:
        url = i[0].url_slab.split("::")[0]
        name = safe(smart_truncate(facet_text(i[0].url_slab)))
        items.append({'url': url, 'name': name, 'count': i[1]})

    return items


def sqs_apply_custom_facets(custom_facets, sqs=None, exclude_facets=None):
    """
    Return a DESearchQuerySet filtered by the input list of saved searches and
    exclude searches

    Inputs:
    :custom_facets: Queryset of CustomFacets to apply to sqs, required
    :sqs: Haystack SearchQuerySet, optional
    :exclude_facet: Queryset of ExcludeFacets to exclude from sqs, optional

    """

    if sqs is None:
        sqs = DESearchQuerySet()
    # Apply SearchQueries for exclude facets and custom facets to our
    # SearchQuerySet
    if exclude_facets:
        combined_exclude_sq = create_sq(exclude_facets)
        if combined_exclude_sq:
            sqs = sqs.narrow_exclude(combined_exclude_sq.build_query())
    if custom_facets:
        combined_sq = create_sq(custom_facets)
        if combined_sq:
            sqs = sqs.narrow(combined_sq.build_query())
    return sqs


def create_sq(custom_facets):
    """
    Returns a single SQ object from an iterable of custom_facets
    Inputs:
        :custom_facets: An interable of CustomFacet objects
    Returns:
        A list of Haystack SearchQuery objects

    """
    #maps boolean_operation codes to their operator functions. Default is or_
    op_map = [("", operator.or_),
              ("or", operator.or_),
              ("and", operator.and_)]

    result_sq = SolrSearchQuery()
    facets_by_op = defaultdict(list)
    #map each facet to a it's boolean_operation in a dict
    map(lambda facet: facets_by_op[facet.get_op()].append(facet), custom_facets)
    for op, op_func in op_map:
        #Create an op_list for custom facets of current operation type
        op_facets = facets_by_op[op]
        #Create a Search Query for each customfacet in op_list
        if op_facets:
            op_query_list = [SQ(content=Raw(cf.saved_querystring)) for cf in
                             op_facets if cf.saved_querystring]
            if op_query_list:
                # Creates a single search query joined by op, for each
                # non-empty SQ
                op_sq = (reduce(op_func, filter(lambda x: x, op_query_list)))
            else:
                continue
            result_sq.add_filter(op_sq)
    return result_sq


def prepare_sqs_from_search_params(params, sqs=None):
    boost_value = 1.5
    title = params.get('q')
    location = params.get('location')
    moc = params.get('moc')
    moc_id = params.get('moc_id')
    company = params.get('company')
    exact_title = bool(params.get('exact_title'))
    if sqs is None:
        sqs = DESearchQuerySet()

    # The Haystack API does not allow for boosting terms in individual
    # fields. In this case we want to boost the term represented by
    # the variable 'title' ONLY when it appears in the `title` field in
    # the search index.
    #
    # To get around this I instead construct the string according to the
    # format specified for boosting a term in a specific field by the
    # Solr documentation:
    #   'q=title:(Accountant)^2'
    # By using parens instead of quotes, Solr can parse more complex title
    # searches.
    #
    # I then pass that string to an SQ object and proceed as normal.
    # This allows us to ensure that titles that match a query exactly
    # will appear higher in the results list than results that simply
    # have the query term in the text of the document.
    cleaned_params = dict([(val, _clean(val)) for val in
                           [title, location, moc, moc_id, company] if val])
    q_val = cleaned_params.get(title)
    moc_val = cleaned_params.get(moc)
    moc_id_val = cleaned_params.get(moc_id)
    loc_val = cleaned_params.get(location)

    # If 'q' has a value in the querystring, filter our results by it in
    # two places: 1. In the `text` field (full document) 2. In the `title`
    # field, after it has been boosted by a factor of 0.5. We want to make
    # sure that someone searching for a title like "engineer" sees jobs
    # that match on job title first, before results that "only" match on
    # random words in the full text of the document.
    if q_val:
        # Escape dashes surrounded by spaces, since they probably aren't
        # intended as negation.
        # Retail -Sales will search for Retail excluding Sales
        # Retail - Sales will search for 'Retail - Sales'
        title = "(%s)" % title.replace(' - ', ' \\- ')
        tb = u"({t})^{b}".format(t=title, b=boost_value)

        if exact_title:
            sqs = sqs.filter(title_exact__exact=title)
        else:
            sqs = sqs.filter(SQ(content=Raw(title)) | SQ(title=Raw(tb)))\
                     .highlight()

    # If there is a value in the `location` parameter, add filters for it
    # in each location-y field in the index. If the `exact` parameter is
    # `true` in the querystring, search locations for EXACT matches only;
    # the rationale being that if a user clicks on "San Diego" he probably
    # doesn't give a crap about "San Francisco" or "San Jose" results.
    if loc_val:
        sqs = sqs.filter(full_loc=loc_val)

    if company:
        sqs = sqs.filter(company_exact__exact=company)

    if moc_val:
        # Before we can search for MOC, we have to find out if the SeoSite
        # has specified any custom MOC-Onet mappings. If they do, we'll search
        # on the jobs mapped_moc* fields
        prefix = 'mapped_' if settings.SITE_BUIDS else ''

        if moc_id_val:
            moc_filt = SQ(**{'%smocid' % prefix: moc_id_val})
        else:
            moc_filt = SQ(SQ(**{'%smoc' % prefix: moc_val}) |
                          SQ(**{'%smoc_slab' % prefix: moc_val}))
        sqs = sqs.filter(moc_filt)

    return sqs.highlight()


def _sqs_narrow_by_buid_and_site_package(sqs, buids=None, site_packages=None):
    """Narrows Search Query Set to results with given buids and site ids.
    Inputs:
        :sqs: SearchQuerySet
        :buids: List of buids to narrow by.
        :site_ids: List of site ids to narrow by.

    Results:
        :sqs: SearchQuerySet narrowed to documents with buids in list 'buids'.
    """
    if site_packages is None:
        site_packages = settings.SITE_PACKAGES

    if buids is None:
        buids = settings.SITE_BUIDS
    if not buids:
        site_packages.append(0)

    if site_packages:
        site_packages = ' OR '.join([str(i) for i in site_packages])
    if buids:
        buids = ' OR '.join([str(i) for i in buids])

    if buids and site_packages:
        sqs = sqs.narrow("(on_sites:(%s) OR buid:(%s))" % (site_packages, buids))
    elif buids and not site_packages:
        sqs = sqs.narrow("(buid:(%s))" % buids)
    else:
        sqs = sqs.narrow("on_sites:(%s)" % site_packages)

    return sqs


def related_jobs(job):
    return _sqs_narrow_by_buid_and_site_package(DESearchQuerySet()).more_like_this(job)[0:10]


def take(n, seq):
    "Return first n items of the seq as a list"
    return list(islice(seq, n))


def drop(n, seq):
    "Return seq with the first n items removed."
    return list(islice(seq, n, None, 1))


def split_by(n, seq):
    return [take(n, seq), drop(n, seq)]


def slices(seq, start=0, end=None, step=2):
    """
    Takes a sequence 'seq' and yields a 2-tuple that expresses a
    'step'-sized. Ex:

    >> x = slices(range(20), step=4)
    >> x.next()
    (0, 4)
    >> x.next()
    (4, 8)
    >> x.next()
    (8, 12)

    etc. Put another way:

    >> x = slices(range(20), step=4)
    >> [i for i in x]
    [(0, 4), (4, 8), (8, 12), (12, 16), (16, 20), (20, 21)]

    Note the calculation of the 'rng' variable. If 'len(seq)' is a
    multiple of 'step', we add an additional item onto the end so we make
    sure to get each item. (This is why in the example above the last
    tuple is '(20, 21)'.)

    """
    fun = split_by
    ls = len(seq)
    if ls < step and seq:
        yield (0, ls)
    else:
        if ls % step:
            rng = xrange(ls/step+1)
        else:
            rng = xrange(ls/step)

        for i in rng:
            segment = fun(step, seq[start:])
            start += step
            yield segment[0][0], segment[0][-1]


def create_businessunit(buid):
    """
    Create a BusinessUnit instance with the given business unit id
    ('buid') if one does not already exist.

    Input:
    :buid: Positive integer.

    Returns:
    A boolean. This value is used by `import_jobs.update_solr` to
    determine whether or not to set the company title on the BusinessUnit.
    This determination is made at that point because `xmlparse.JobFeed`
    and its subclasses have a `company` attribute which is the name of
    the company as parsed from the feed file.

    Writes/Modifies:
    `seo_businessunit` table in the database.

    """
    # We use BUID 0 for testing, but in all other cases the buid must be > 0.
    if buid < 0:
        raise AttributeError("'buid' must be a positive integer.")

    if not BusinessUnit.objects.filter(id=buid).exists():
        # Set the date_crawled & date_updated fields to Jan. 1, 1901 so that
        # import_jobs._buid_is_stale() will return True
        never = datetime.datetime(1971, 01, 01, 00, 00, 00)
        BusinessUnit.objects.create(id=buid, date_crawled=never,
                                    date_updated=never)
        return True
    else:
        return False


def make_json(data, host):
    s = JSONExtraValuesSerializer(publisher_url="http://%s" % host)
    output = s.serialize(data)
    return output


def make_specialcommit_string(special_commits):
    """
    Build the site commitment string here instead of multiple times in the
    template. Called from seo.views.search_views.job_listing_by_slug_tag and
    seo.views.search_views.
    [10-8-12 JPSOLE]

    Inputs:
    :special_commits:      settings.COMMITMENTS.all() object

    Returns:
    A space separated string of values in special_commits

    """
    return ' '.join(special_commits.values_list('commit', flat=True))


def make_sitetag_string(site_tags):
    return ' '.join(site_tags)


def determine_redirect(request, filters):
    """
    Determines whether or not a search url needs to be restructured. This
    happens for 5 mains reasons:
    1. The filter paths are out of order.
    2. The path uses /search/ instead of /jobs/.
    3. There is a location in both the path and the query string.
    4. There is an moc in both the path and the query string.
    5. There are extra (ticket, uid) or unused terms in the query string.

    Inputs:
    :request: The request object
    :filters: The search filters built from the request path.

    Outputs:
    None if no redirect is required
    A response object to the redirect url if a redirect is required.

    """
    needs_redirect = False
    referer = request.META.get('HTTP_REFERER', None)
    query_dict = (request.GET.dict() if request.META.get('QUERY_STRING', None)
                  else {})
    filter_loc = filters.get('location_slug', None)
    query_loc = request.GET.get('location', None)
    filter_moc = filters.get('moc_slug', None)
    query_moc = request.GET.get('moc', None)

    if request.path.startswith('/search'):
        needs_redirect = True
    elif '/jobs/' != request.path:
        slug_tag_paths = [''.join([filters[key], value]) for key, value
                          in settings.SLUG_TAGS.items() if filters[key]]
        canonical_url = '/%s' % ''.join(slug_tag_paths)
        if request.path != canonical_url:
            needs_redirect = True

    # Determines whether to pull the location/moc from the path or the query
    # by checking which has changed. If there is no referer but there is
    # a location/moc in both the query and the path, the query location/moc is
    # used.
    if ((filter_loc and query_loc) or (filter_moc and query_moc)) and referer:
        needs_redirect = True

        ref = urlparse(referer)

        ref_filter_loc = build_filter_dict(ref.path).get('location_slug')
        ref_query_loc = parse_qs(ref.query).get('location', None)

        referer_filter_moc = build_filter_dict(ref.path).get('moc_slug')
        referer_query_moc = parse_qs(ref.query).get('moc', None)

        if ref_filter_loc != filter_loc:
            del query_dict['location']

        elif ref_query_loc != query_loc:
            filters['location_slug'] = None

        if referer_filter_moc != filter_moc:
            del query_dict['moc']

        elif referer_query_moc != query_moc:
            filters['moc_slug'] = None

    if query_moc and filter_moc and not referer:
        filters['moc_slug'] = None
        needs_redirect = True

    if query_loc and filter_loc and not referer:
        filters['location_slug'] = None
        needs_redirect = True

    new_filters = [''.join([filters[key], value]) for key, value in
                   settings.SLUG_TAGS.items() if filters[key]]
    new_path = '/%s' % ''.join(new_filters)

    if not new_path or new_path == '/' or new_path.startswith('/search'):
        new_path = '/jobs/'

    new_query = clean_query_dict(query_dict)
    old_dict = request.GET.dict()
    for key, value in old_dict.items():
        old_dict[key] = unicode(value).encode('utf-8')

    if (new_path != request.path) or cmp(new_query, old_dict) != 0 \
            or needs_redirect:
        redirect_url = urljoin(new_path, "?%s" % urllib.urlencode(new_query)) \
            if new_query else new_path
        return redirect(redirect_url, permanent=True)
    else:
        return None


def clean_query_dict(query_dict):
    """
    Removes unneeded (ticket, uid) or unused items from a query dict.

    Inputs:
    :query dict: A dictionary representing the query string.

    Outputs:
    A dictionary of only used keys with utf-8 encoded values.

    """
    for key, value in query_dict.items():
        if not value:
            del query_dict[key]
        elif key == 'ticket' or key == 'uid':
            del query_dict[key]
        else:
            query_dict[key] = unicode(value).encode('utf-8')

    return query_dict


def urlencode_path_and_query_string(url):
    try:
        path, query_string = url.split("?")
    except ValueError:
        path = url
        query_string = ''

    result = urllib.quote(path)

    if query_string:
        query_string = parse_qsl(query_string)
        query_string = urllib.urlencode(query_string)
        result = '{path}?{query_string}'.format(path=result,
                                                query_string=query_string)
    return result


def _build_facet_queries(custom_facets):
    tagged_facets = {}
    sqs = DESearchQuerySet()
    custom_facet_queries = [facet.saved_querystring for facet in custom_facets]
    for query, facet in zip(custom_facet_queries, custom_facets):
        tagged_facets[query] = {
            'custom_facet': facet,
        }
        sqs = sqs.query_facet(query)
    return tagged_facets, sqs


def _facet_query_result_counts(tagged_facets, sqs):
    """
    Map query results back to their originating CustomFacet instances.

    """
    fields = ['django_ct', 'django_id', 'score', 'id']
    sqs.query.fields = fields
    sqs.query.end_offset = 0
    facet_results = sqs.facet_counts()
    if not facet_results:
        return []

    counts = []
    for query, count in facet_results['queries'].iteritems():
        tagged_facet = tagged_facets[query]['custom_facet']
        if count > 0 or tagged_facet.always_show:
            counts.append((tagged_facet, count))
    return counts


def get_solr_facet(jsids, filters=None, params=None):
    custom_facets = settings.STANDARD_FACET

    # Short-circuit the function if a site has facets turned on, but either
    # does not have any facets with `show_production` == 1 or has not yet
    # created any facets.
    if not custom_facets:
        return []

    tagged_facets, sqs = _build_facet_queries(custom_facets)

    # If this function is called from
    # seo.views.search_views.job_listing_by_slug_tag, it is passed the
    #  additional "filters" parameter, which is the output
    # from helper.build_filter_dict(request.path).
    if filters:
        sqs = filter_sqs(sqs, filters)

    # Intersect the CustomFacet object's query parameters with those of
    # the site's default facet, if it has one.
    if settings.DEFAULT_FACET:
        sqs = sqs_apply_custom_facets(settings.DEFAULT_FACET, sqs)

    sqs = _sqs_narrow_by_buid_and_site_package(sqs, buids=jsids)

    if params:
        sqs = prepare_sqs_from_search_params(params, sqs=sqs)

    result_counts = _facet_query_result_counts(tagged_facets, sqs)
    result_counts.sort(key=lambda x: -x[1])
    return result_counts


def add_text_to_job(job):
    # Strip html and markdown formatting from description snippets
    try:
        i = text_fields.index('description')
        text_fields[i] = 'html_description'
    except ValueError:
        pass

    h = HTMLParser()
    text = filter(None, [getattr(job, x, "None") for x in text_fields])
    unformatted_text = h.unescape(strip_tags(" ".join(text)))
    setattr(job, 'text', unformatted_text)
    return job


def jobs_and_counts(request, filters, num_jobs, fl=search_fields):
    sort_order = request.GET.get('sort', 'relevance')

    sqs = prepare_sqs_from_search_params(request.GET)
    default_jobs = get_jobs(default_sqs=sqs,
                            custom_facets=settings.DEFAULT_FACET,
                            exclude_facets=settings.FEATURED_FACET,
                            jsids=settings.SITE_BUIDS, filters=filters,
                            facet_limit=num_jobs, sort_order=sort_order,
                            fl=fl)
    featured_jobs = get_featured_jobs(default_sqs=sqs, filters=filters,
                                      jsids=settings.SITE_BUIDS,
                                      facet_limit=num_jobs,
                                      sort_order=sort_order, fl=fl)

    # Force the query to evaluate and populate the result cache. After this
    # unless changes are made to the sqs objects
    # anything using query results will be working with the same
    # exact version of the query results (and more importantly,
    # the query won't be re-run).
    default_jobs[:num_jobs]
    featured_jobs[:num_jobs]

    facet_counts = default_jobs.add_facet_count(featured_jobs).get('fields')

    return default_jobs, featured_jobs, facet_counts


def get_company_data(filters):
    if filters['company_slug']:
        company_obj = Company.objects.filter(member=True)
        company_obj = company_obj.filter(company_slug=filters['company_slug'])
        if company_obj:
            return company_thumbnails(company_obj)[0]
        else:
            return None
    else:
        return None