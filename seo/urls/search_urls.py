from django.conf.urls import patterns, url
from django.conf import settings
from django.views.generic import TemplateView

from seo.views import search_views

#Lazily matches any repition of alphanumeric characters, /, or -
SLUG_RE = '[/\w-]+?'

urlpatterns = patterns('seo.views.search_views',
    # static files
    url(r'^style/style.css$',
        'stylesheet',
        {'css_file':'stylesheet.css'},
        name="stylesheet"),
    url(r'^style/posting-style.css$',
        'stylesheet',
        {'css_file': 'posting-stylesheet.css'},
        name="posting-stylesheet"),
    url(r'^style/def.ui.dotjobs.css$',
        'stylesheet',
        {'css_file':'def.ui.dotjobs.css'},
        name="dotjobs_stylesheet"),
    url(r'^style/def.ui.dotjobs.ie7.css$',
        'stylesheet',
        {'css_file':'def.ui.dotjobs.ie7.css'},
        name="dotjobs_ie7_stylesheet"),
    url(r'^style/def.ui.dotjobs.results.css$',
        'stylesheet',
        {'css_file':'def.ui.dotjobs.results.css'},
        name="dotjobs_results_stylesheet"),
    url(r'^style/def.ui.microsite.mobile.css$',
        'stylesheet',
        {'css_file':'def.ui.microsite.mobile.css'},
        name="mobile_stylesheet"),
    (r'^ajax/mac/$','moc_index'),
    url(r'^sitemap.xml$', 'new_sitemap_index', name='sitemap_xml'),
    url(r'^sitemap-(?P<jobdate>[\d-]+)\.xml$', 'new_sitemap',
        name='sitemap_date'),
    (r'^robots.txt$', 'robots_txt'),
)

urlpatterns += patterns('seo.views.search_views',
    ## V2 redirect for browse by occupation put here so it's not caught by nav_cc3_location_home
    url(r'(?P<onet>\d+)/jobs/$',
        'v2_redirect', {'v2_redirect': 'occupation'}, name="v2_occupation")
    )

stripped_slugs = []
for val in settings.SLUG_TAGS.values():
    stripped_slugs.append(val.strip('/'))


urlpatterns += patterns('seo.views.search_views',
    # rss feed
    url(r'^(?P<filter_path>[/\w-]*)feed/(?P<feed_type>json|rss|xml|atom|indeed|jsonp)$',
        'syndication_feed', name="feed"),
    # `jobs/` is the only allowable standalone slug tag
    url(r'^jobs/$', search_views.SearchResults.as_view(), name='all_jobs'),
    url(r'^[/\w-]+?/(%s)/$' % ('|'.join(stripped_slugs)),
        search_views.SearchResults.as_view(),
        name="search_by_results_and_slugs"),


    # home page
    url(r'^$', search_views.HomePage.as_view(), name="home"),
    url(r'^site-family$', 'site_family', name='site_family'),
    # all companies page
    url(r'^all-companies/$', 'company_listing', {'group': 'all'},
        name='all-companies_home'),
    url(r'^all-companies/0-9/$', 'company_listing', {'alpha': '0-9', 'group': 'all'},
        name='all-companies'),
    url(r'^all-companies/(?P<alpha>[a-z])/$', 'company_listing', {'group': 'all'},
        name='all-companies'),
    # featured companies page
    url(r'^featured-companies/$', 'company_listing', {'group': 'featured'},
        name='featured-companies_home'),
    url(r'^featured-companies/0-9/$', 'company_listing',
        {'alpha': '0-9', 'group': 'featured'},
        name='featured-companies_home'),
    url(r'^featured-companies/(?P<alpha>[a-z])/$', 'company_listing',
        {'group': 'featured'},
        name='featured-companies'),
    url(r'^ajax/member-companies/jsonp$', 'member_carousel_data'),
    url(r'^member-companies/$', 'company_listing',
        {'alpha': 'a', 'group': 'member'},
        name='member-companies_home'),
    url(r'^member-companies/0-9/$', 'company_listing',
        {'alpha': '0-9', 'group': 'member'},
        name='member-companies_home'),
    url(r'^member-companies/(?P<alpha>[a-z])/$', 'company_listing',
        {'group': 'member'},
        name='member-companies'),

    # job detail (aka job view)
    url(r'^(?P<location_slug>[\w-]+)/(?P<title_slug>[\w~-]+)/(?P<job_id>[0-9A-Fa-f]{1,32})/job/$',
        search_views.JobDetail.as_view(),
        name="job_detail_by_location_slug_title_slug_job_id"),
    url(r'(?P<feed>xml|rss|atom|json|indeed)?/?(?P<job_id>[0-9A-Fa-f]{1,32})/job/$',
        search_views.JobDetail.as_view(),
        name="job_detail_by_job_id"),


    # ajax urls
    url(r'^ajax/(?P<filter_path>[/\w-]*)(?P<facet_type>titles|cities|states|'
        'countries|facets|mapped|mocs|company-ajax)/$', 'ajax_get_facets'),
    url(r'^ajax/data/cities$', 'ajax_cities'),
    url(r'^ajax/data/sites$', 'ajax_sites'),
    url(r'^data/buids$', 'ajax_buids'),
    url(r'^ajax/ac/$', 'solr_ac'),
    url(r'^ajax/filtercarousel/$', 'ajax_filter_carousel'),
    url(r'^ajax/geolocation/$', 'ajax_geolocation_facet',
        name='ajax_geolocation_facet'),
    # These urls aren't ajax, they're just there to prevent bots
    url(r'^ajax/postajob/$', 'post_a_job'),
    url(r'^ajax/deleteajob/$', 'delete_a_job'),
    url(r'^ajax/markdown/$', 'test_markdown'),

    url(r'^search$', 'search_by_results_and_slugs'),

    # this url doesn't really follow the convention used in the others,
    # since it collides with our normal url structure where '/jobs/'
    # comes at the end of the url
    url(r'^(?P<filter_path>[/\w-]*)ajax/joblisting/$', 'ajax_get_jobs'),
)

urlpatterns += patterns('',
    # filter paths for url tag reversing only
    url(r'^(?P<facet_slug>[/\w-]+?)%s$' % (settings.SLUG_TAGS['facet_slug']),
        TemplateView.as_view(template_name='name_value.html'), name="nav_facet_slug"),
    url(r'^(?P<title_slug>[/\w-]+?)%s$' % (settings.SLUG_TAGS['title_slug']),
        TemplateView.as_view(template_name='name_value.html'), name="nav_title_slug"),
    url(r'^(?P<city_slug>[\w-]+)/(?P<state_slug>[\w-]+)/(?P<country_short>[a-z]{2,3})%s$' % (settings.SLUG_TAGS['location_slug']),
        TemplateView.as_view(template_name='name_value.html'), name="nav_city_slug"),
    url(r'^(?P<state_slug>[\w-]+)/(?P<country_short>[a-z]{2,3})%s$' % (settings.SLUG_TAGS['location_slug']),
        TemplateView.as_view(template_name='name_value.html'), name="nav_state_slug"),
    url(r'^(?P<country_short>[a-z]{2,3})%s$' % (settings.SLUG_TAGS['location_slug']),
        TemplateView.as_view(template_name='name_value.html'), name="nav_country_slug"),
    url(r'^(?P<full_slug_path>[/\w-]+?)/z$',
        TemplateView.as_view(template_name='name_value.html'), name="nav_full_slug_path"),
)

# version 2.0 redirects - at end of urls.py as final catch all
urlpatterns += patterns('seo.views.search_views',
    # locations
    url(r'(?P<country>[A-Z]{3})/\w+/jobs$',
        'v2_redirect', {'v2_redirect': 'country'}, name="v2_country"),
    url(r'(?P<state>\w+)/(?P<city>\w+)/[A-Z]{2}/jobs$',
        'v2_redirect', {'v2_redirect': 'city'}, name="v2_city"),
    url(r'(?P<state>\w+)/[A-Z]{2}/jobs$',
        'v2_redirect', {'v2_redirect': 'state'}, name="v2_state"),
    url(r'(?P<country>[A-Z]{3})/(?P<city>\w+)/\w+/jobs$',
        'v2_redirect', {'v2_redirect': 'city-country'}, name="v2_city_country"),
)

urlpatterns += patterns('seo.updates',
                        # Although this isn't ajax, it's put under ajax
                        # to prevent bots.
                        url(r'^ajax/update_buid/$', 'update_businessunit'))

urlpatterns += patterns('seo.views.search_views',
    url(r'sns_confirmation$', 'send_sns_confirm'),
    url(r'load_job_source', 'confirm_load_jobs_from_etl'),
    url(r'^(?P<guid>[0-9A-Fa-f]{32})(?P<vsid>\d+)?(?P<debug>\+)?$',
        'urls_redirect', name='urls_redirect'),
)
