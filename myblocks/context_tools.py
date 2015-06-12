import collections
import functools
from itertools import chain

from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.urlresolvers import reverse, resolve
from django.http import QueryDict

from seo import cache, helpers
from seo.breadbox import Breadbox
from seo.search_backend import DESearchQuerySet
from seo.templatetags.job_setup import create_arranged_jobs


class Memoized(object):
    """
    Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).

    """
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        if not settings.MEMOIZE:
            return self.func(*args, **kwargs)
        if not isinstance(args, collections.Hashable) or kwargs:
            return self.func(*args, **kwargs)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        return self.func.__doc__

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)


@Memoized
def get_arranged_jobs(request):
    featured_jobs = get_featured_jobs(request)
    default_jobs = get_default_jobs(request)
    site_config = get_site_config(request)
    return create_arranged_jobs(request, featured_jobs, default_jobs,
                                site_config)


@Memoized
def get_breadbox(request):
    filters = get_filters(request)

    jobs_and_counts = get_jobs_and_counts(request)
    default_jobs = jobs_and_counts[0]
    total_default_jobs = jobs_and_counts[1]
    featured_jobs = jobs_and_counts[2]
    total_featured_jobs = jobs_and_counts[3]

    jobs = list(chain(featured_jobs, default_jobs))

    breadbox = Breadbox(request.path, filters, jobs, request.GET)

    breadbox.job_count = intcomma(total_default_jobs + total_featured_jobs)

    return breadbox


@Memoized
def get_custom_facet_counts(request):
    custom_facet_counts = []
    filters = get_filters(request)
    querystring = get_query_string(request)
    site_config = get_site_config(request)

    if site_config.browse_facet_show:
        cached_custom_facets = cache.get_custom_facets(request, filters=filters,
                                                       query_string=querystring)

        if not filters['facet_slug']:
            custom_facet_counts = cached_custom_facets
        else:
            facet_slugs = filters['facet_slug'].split('/')
            active_facets = helpers.standard_facets_by_name_slug(facet_slugs)
            custom_facet_counts = [(facet, count) for facet, count
                                   in cached_custom_facets
                                   if facet not in active_facets]
    return custom_facet_counts


@Memoized
def get_default_jobs(request):
    default_jobs, _, _, _, _ = get_jobs_and_counts(request)
    return default_jobs


@Memoized
def get_facet_blurb_facet(request):
    filters = get_filters(request)
    facet_blurb_facet = None
    site_config = get_site_config(request)

    if site_config.browse_facet_show and filters['facet_slug']:
        facet_slugs = filters['facet_slug'].split('/')
        active_facets = helpers.standard_facets_by_name_slug(facet_slugs)
        active_facets = list(set(active_facets))

        # Set the facet blurb only if we have exactly one
        # CustomFacet applied.
        if len(active_facets) == 1 and active_facets[0].blurb:
            facet_blurb_facet = active_facets[0]

    return facet_blurb_facet


@Memoized
def get_featured_jobs(request):
    _, _, featured_jobs, _, _ = get_jobs_and_counts(request)
    return featured_jobs


@Memoized
def get_filters(request):
    return helpers.build_filter_dict(request.path)

@Memoized
def get_google_analytics(request):
    return settings.SITE.google_analytics.all()

@Memoized
def get_job(request, job_id):
    search_type = 'guid' if len(job_id) > 31 else 'uid'
    if not job_id:
        return None

    try:
        query = "%s:(%s)" % (search_type, job_id)
        return DESearchQuerySet().narrow(query)[0]
    except IndexError:
        return None


@Memoized
def get_jobs_and_counts(request):
    # Text uses html_description instead of just description.
    fl = list(helpers.search_fields)
    fl.remove('description')
    fl.append('html_description')

    filters = get_filters(request)
    site_config = get_site_config(request)
    num_jobs = int(site_config.num_job_items_to_show) * 2
    percent_featured = site_config.percent_featured

    args = (request, filters, num_jobs)
    kwargs = {'fl': fl}
    default_jobs, featured_jobs, facet_counts = helpers.jobs_and_counts(*args, **kwargs)

    total_default_jobs = default_jobs.count()
    total_featured_jobs = featured_jobs.count()

    args = (featured_jobs.count(), default_jobs.count(), num_jobs,
            percent_featured)
    featured_needed, default_needed, _, _ = helpers.featured_default_jobs(*args)

    default_jobs = default_jobs[:default_needed]
    featured_jobs = featured_jobs[:featured_needed]

    jobs = list(chain(featured_jobs, default_jobs))
    for job in jobs:
        helpers.add_text_to_job(job)

    return (default_jobs, total_default_jobs, featured_jobs,
            total_featured_jobs, facet_counts)

@Memoized
def get_job_detail_breadbox(request, job_id):
    job = get_job(request, job_id)
    if not job:
        return {}

    site_config = get_site_config(request)

    breadbox = helpers.job_breadcrumbs(job, site_config.browse_company_show)

    query_string = get_query_string(request)
    if query_string:
        # Append the query_path to all of the exising urls
        for field in breadbox:
            path = breadbox[field].get('path', '/jobs/')
            path_and_query_string = "%s?%s" % (path, query_string)
            new_url = (path_and_query_string if query_string
                       else breadbox[field]['path'])
            breadbox[field]['path'] = new_url

        # Create a new path for title and moc query string values
        # from the job information.
        fields = ['title', 'city']
        path = ''
        for field in fields:
            slab = getattr(job, '%s_slab' % field)
            path = "%s%s/" % (path, slab.split("::")[0])
        for field in ['q', 'moc']:
            if request.GET.get(field, None):
                breadbox[field] = {}
                qs = QueryDict(query_string).copy()
                del qs[field]
                breadbox[field]['path'] = "/%s?%s" % (path, qs.urlencode())
                breadbox[field]['display'] = request.GET.get(field)

    return breadbox


@Memoized
def get_location_term(request, **kwargs):
    function_name = resolve(request.path).func.func_name

    if function_name == 'JobDetail':
        job_id = kwargs.get('job_id', '')
        job = get_job(request, job_id)
        return getattr(job, 'location', '')

    breadbox = get_breadbox(request)
    return breadbox.location_display_heading()


@Memoized
def get_moc_term(request):
    breadbox = get_breadbox(request)
    return breadbox.moc_display_heading()


@Memoized
def get_moc_id_term(request):
    return request.GET.get('moc_id', '')


@Memoized
def get_query_string(request):
    return request.META.get('QUERY_STRING', None)


@Memoized
def get_results_heading(request):
    breadbox = get_breadbox(request)
    return helpers.build_results_heading(breadbox)


@Memoized
def get_search_url(request):
    return request.path if request.path != '/' else reverse('all_jobs')


@Memoized
def get_site_commitments_string(request):
    return helpers.make_specialcommit_string(settings.COMMITMENTS.all())


@Memoized
def get_site_config(request):
    return cache.get_site_config(request)


@Memoized
def get_title_term(request):
    return request.GET.get('q', '')


@Memoized
def get_total_jobs_count(request):
    return cache.get_total_jobs_count()


@Memoized
def get_widgets(request):
    filters = get_filters(request)
    _, _, _, _, facet_counts = get_jobs_and_counts(request)
    site_config = get_site_config(request)

    custom_facet_counts = get_custom_facet_counts(request)

    return helpers.get_widgets(request, site_config, facet_counts,
                               custom_facet_counts, filters=filters)
