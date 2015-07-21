from django.conf.urls import *
from django.contrib import admin
from django.db.models.loading import cache as model_cache
from django.views.generic import RedirectView

from seo.views.search_views import (BusinessUnitAdminFilter, SeoSiteAdminFilter,
                                    Dseo404)
from seo.views.settings_views import secure_redirect
from registration import views as registration_views

from tastypie.api import Api
from seo.api.resources import *

v1_api = Api(api_name="v1")
v1_api.register(SeoSiteResource())
v1_api.register(ATSResource())
v1_api.register(GroupResource())
v1_api.register(ViewSourceResource())
v1_api.register(BusinessUnitResource())
v1_api.register(GoogleAnalyticsResource())
v1_api.register(GoogleAnalyticsCampaignResource())
v1_api.register(SpecialCommitmentResource())
v1_api.register(CustomFacetResource())
v1_api.register(ConfigurationResource())
v1_api.register(FeaturedCompanyResource())
v1_api.register(CompanyResource())
v1_api.register(BillboardImageResource())
v1_api.register(BillboardHotspotResource())
v1_api.register(MocResource())
v1_api.register(MocDetailResource())
v1_api.register(OnetResource())
v1_api.register(JobSearchResource())
v1_api.register(JobResource())

admin.autodiscover()
handler404 = Dseo404.as_view()
handler500 = 'seo.views.search_views.dseo_500'


# API endpoints
urlpatterns = patterns('',
    url('^api/', include(v1_api.urls))
)

# Custom Admin URLs
urlpatterns += patterns('seo.views.search_views',
    url(r'^admin/groupsites/$', 'get_group_sites'),
    url(r'^admin/grouprelationships/$', 'get_group_relationships'),
)

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url('', include('seo.urls.search_urls', app_name='seo')),
    url('settings/', include('seo.urls.settings_urls')),
    url('^mocmaps/', include('moc_coding.urls', app_name='moc_coding')),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'},
        name='auth_logout'),
    url(r'^posting/', include('postajob.urls', app_name='postajob')),
)


urlpatterns += patterns(
    '',
    # Filtering urls
    url(r'^ajax/data/filter/business_units/$',
        BusinessUnitAdminFilter.as_view(),
        name='buid_admin_fsm'),
    url(r'^ajax/data/filter/sites/$', SeoSiteAdminFilter.as_view(),
        name='site_admin_fsm')
)


urlpatterns += patterns(
    '',
    url(r'^account/$',
        RedirectView.as_view(url='https://secure.my.jobs/account/edit')),
    url(r'^candidates/$',
        RedirectView.as_view(url='https://secure.my.jobs/candidates/view')),
    url(r'^profile/$',
        RedirectView.as_view(url='https://secure.my.jobs/profile/view')),
    url(r'^savedsearch/$',
        RedirectView.as_view(url='https://secure.my.jobs/saved-search/view')),
    url(r'^accounts/', include('registration.urls')),
)

for page in ['about', 'privacy', 'contact', 'contact-faq', 'terms']:
    urlpatterns += patterns(
        '',
        url(r'^{page}/'.format(page=page), secure_redirect, {'page': page},
            name=page.replace('-', '_'))
    )

urlpatterns += patterns(
    'myjobs.views',
    url(r'^account/edit/$', 'edit_account', name='edit_account'),
    url(r'^account/delete$', 'delete_account', name='delete_account'),
    url(r'^account/disable$', 'disable_account', name='disable_account'),
)

urlpatterns += patterns(
    'registration.views',
    url(r'^login', registration_views.DseoLogin.as_view(), name='login'),
)

# This feature does not exist...
urlpatterns += patterns(
    '',
    url(r'^message/', include('mymessages.urls'))
)

