import operator
import pytz

from django import http
from django.core.urlresolvers import reverse
from django.utils.timezone import activate
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.shortcuts import redirect

from postajob.models import SitePackage
from seo.models import SeoSite, SeoSiteRedirect, SeoSiteFacet
import version


if settings.NEW_RELIC_TRACKING:
    try:
        import newrelic.agent
    except ImportError:
        pass


class PasswordChangeRedirectMiddleware:
    """
    Redirects a user to the password change form if several conditions are met:
    - A user is logged in
    - That user's password_change flag is set to True
    - The user is not trying to log out,
        change passwords, or activate an account

    Returns a 403 status code if the request is ajax and the request dict
    contains the 'next' key (i.e. no user is logged in, a privileged
    page was left open, and an unauthorized user tries to access something
    that they shouldn't)
    """
    def process_request(self, request):
        if request.user.is_authenticated():
            urls = [reverse('read'),
                    reverse('edit_account'),
                    reverse('auth_logout'),
                    reverse('registration_activate', args=['a'])[0:-2]]
            url_matches = reduce(operator.or_,
                                 [request.path.startswith(url)
                                  for url in urls])

            if (not url_matches and request.user.password_change):
                return http.HttpResponseRedirect(reverse('edit_account')
                                                 + '#as-password')

        elif request.is_ajax() and bool(request.REQUEST.get('next')):
            return http.HttpResponse(status=403)


XS_SHARING_ALLOWED_ORIGINS = '*'
XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']
XS_SHARING_ALLOWED_HEADERS = 'Content-Type'


class XsSharing(object):
    """
        This middleware allows cross-domain XHR using the html5 postMessage API.

        Access-Control-Allow-Origin: http://foo.example
        Access-Control-Allow-Methods: POST, GET, OPTIONS, PUT, DELETE
    """
    def process_request(self, request):

        if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META:
            response = http.HttpResponse()
            response['Access-Control-Allow-Origin'] = XS_SHARING_ALLOWED_ORIGINS
            response['Access-Control-Allow-Headers'] = XS_SHARING_ALLOWED_HEADERS
            response['Access-Control-Allow-Methods'] = ",".join(
                XS_SHARING_ALLOWED_METHODS)

            return response

        return None

    def process_response(self, request, response):
        # Avoid unnecessary work
        if response.has_header('Access-Control-Allow-Origin'):
            return response

        response['Access-Control-Allow-Origin'] = XS_SHARING_ALLOWED_ORIGINS
        response['Access-Control-Allow-Headers'] = XS_SHARING_ALLOWED_HEADERS
        response['Access-Control-Allow-Methods'] = ",".join(
            XS_SHARING_ALLOWED_METHODS)

        return response


class NewRelic(object):
    """
    Manages New Relic tracking.

    """
    def process_response(self, request, response):
        newrelic.agent.add_custom_parameter('url', request.META['HTTP_HOST'])
        if hasattr(request, 'user'):
            newrelic.agent.add_custom_parameter('user_id', request.user.id)
        else:
            newrelic.agent.add_custom_parameter('user_id', 'anonymous')
        return response

    def process_request(self, request):
        newrelic.agent.add_custom_parameter('url', request.META['HTTP_HOST'])
        if hasattr(request, 'user'):
            newrelic.agent.add_custom_parameter('user_id', request.user.id)
        else:
            newrelic.agent.add_custom_parameter('user_id', 'anonymous')


class CompactP3PMiddleware(object):
    """
    Adds a compact privacy policy to site headers

    """
    def process_response(self, request, response):
        response['P3P'] = 'CP="ALL DSP COR CURa IND PHY UNR"'
        return response


class TimezoneMiddleware(object):
    """
    Activates the user-selected timezone.

    """
    def process_request(self, request):
        if hasattr(request, 'user') and not request.user.is_anonymous():
            try:
                activate(pytz.timezone(request.user.timezone))
            except Exception:
                activate(pytz.timezone('America/New_York'))


class SiteRedirectMiddleware:
    def process_request(self, request):
        """
        Find out if we need to redirect to a different url.

        There's 3 cases we need to handle:
        1. A site exists and has a redirect.
        2. A site exists but has no redirect.
        3. The site doesn't exist at all.

        NOTE: this middleware should probably come first, as if we're going
              to redirect, why go thru any other unneeded processing

        """
        host = request.get_host()
        try:
            ss = SeoSiteRedirect.objects. \
                select_related('seosite__domain').get(redirect_url=host)
            redirect_host = ss.seosite.domain
            uri = request.path
            redirect_url = 'http://%s%s' % (redirect_host, uri)
            return redirect(redirect_url, permanent=True)
        except SeoSiteRedirect.DoesNotExist:
            return


class MultiHostMiddleware:
    def process_request(self, request):
        """
        get the host name
        see if we have the settings for the site cached
            - if so, load those
            - if not, grab them from that database
                - store them in cache

        """
        host = None
        if request.user.is_authenticated() and request.user.is_staff:
            host = request.REQUEST.get('domain')

        if host is None:
            host = request.get_host()

        # get rid of any possible port number that comes thru on the host
        # examples:    localhost:80,
        #             127.0.0.1:8000,
        #             find.ibm.jobs:80
        host = host.split(":")[0]
        site_cache_key = '%s:SeoSite' % host
        MINUTES_TO_CACHE = getattr(settings, 'MINUTES_TO_CACHE', 120)
        ## REMINDER: make domain a unique field on site model
        # see if the cache has it
        my_site = cache.get(site_cache_key)
        if not my_site:
            #DO NOT add filters to prefetched objects. Use only with .all()
            sites = SeoSite.objects.select_related('group',
                                                   'microsite_carousel',
                                                   'view_sources',
                                                   ).prefetch_related('billboard_images',
                                                                      'business_units',
                                                                      'featured_companies',
                                                                      'site_tags',
                                                                      'google_analytics')
            # the cache didn't have it, so lets get it and set the cache
            try:
                my_site = sites.get(domain=host)
            except Site.MultipleObjectsReturned:
                my_site = sites.filter(domain=host)[:1][0]
            except Site.DoesNotExist:
                my_site = sites.get(id=1)
            cache.set(site_cache_key, my_site, MINUTES_TO_CACHE*60)
        settings.SITE = my_site
        my_buids = [bu.id for bu in my_site.business_units.all()]
        settings.SITE_ID = my_site.id
        settings.SITE_NAME = my_site.name
        settings.SITE_BUIDS = my_buids
        settings.SITE_TAGS = [tag.site_tag for tag in my_site.site_tags.all()]
        # version information
        settings.VERSION = version.marketing_version
        settings.BUILD = version.build_calculated
        settings.FULL_VERSION = version.release_number

        # Place variables that need a non blank default value here
        if my_site.site_title:  # title defaults to site name
            settings.SITE_TITLE = my_site.site_title
        else:
            settings.SITE_TITLE = my_site.name
        if my_site.site_heading:  # heading defaults to site name
            settings.SITE_HEADING = my_site.site_heading
        else:
            settings.SITE_HEADING = my_site.name
        if my_site.site_description:
            settings.SITE_DESCRIPTION = my_site.site_description
        else:
            settings.SITE_DESCRIPTION = None

        # Default variable loading. Assigns empty string as default
        site_flags = {
            'ats_source_codes': 'ATS_SOURCE_CODES',
            'google_analytics_campaigns': 'GA_CAMPAIGN',
            'special_commitments': 'COMMITMENTS',
            'view_sources': 'VIEW_SOURCE'
        }

        for k, v in site_flags.items():
            attr = getattr(my_site, k)
            if attr:
                setattr(settings, v, attr)
            else:
                setattr(settings, v, '')

        site_facets = SeoSiteFacet.objects.filter(seosite=my_site)
        site_facets = site_facets.select_related('customfacet')

        settings.CACHE_MIDDLEWARE_KEY_PREFIX = "%s" % my_site.domain

        default = SeoSiteFacet.DEFAULT
        default_site_facets = site_facets.filter(facet_type=default)
        settings.DEFAULT_FACET = custom_facets_ops_groups(default_site_facets)

        featured = SeoSiteFacet.FEATURED
        featured_site_facets = site_facets.filter(facet_type=featured)
        settings.FEATURED_FACET = custom_facets_ops_groups(featured_site_facets)

        standard = SeoSiteFacet.STANDARD
        standard_site_facets = site_facets.filter(facet_type=standard)
        settings.STANDARD_FACET = custom_facets_ops_groups(standard_site_facets)

        packages = SitePackage.objects.filter(sites=my_site)
        settings.SITE_PACKAGES = [int(site_package.pk)
                                  for site_package in packages]


def custom_facets_ops_groups(site_facets):
    """
    Returns a list of custom facets with boolean_operation attributes set
    from site facets

    """
    custom_facets = []
    for site_facet in site_facets:
        custom_facet = site_facet.customfacet
        setattr(custom_facet, 'boolean_operation', site_facet.boolean_operation)
        setattr(custom_facet, 'facet_group', site_facet.facet_group)
        custom_facets.append(custom_facet)
    return custom_facets


def filter_custom_facets_by_production_status(custom_facets):
    return [facet for facet in custom_facets if facet.show_production]
