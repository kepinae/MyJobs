from django.conf.urls import *
from django.contrib import admin
from django.db.models.loading import cache as model_cache
from django.views.generic import RedirectView

from seo.views.search_views import (BusinessUnitAdminFilter, SeoSiteAdminFilter,
                                    Dseo404)
from registration import views as registration_views

# This is a bit of code pulled from a Django TRAC ticket describing a problem
# I was seeing when working with the inline model forms:
# https://code.djangoproject.com/ticket/10405#comment:11

# Without this, on pages that aren't serving job-related content, e.g. sitemap,
# stylesheet, etc. pages, we'd see an error like:
# AttributeError: 'str' object has no attribute '_default_manager'

# The Trac ticket linked above recommended including this bit of code, and also
# included a comprehensive explanation. When/if this particular issue gets
# resolved we can safely remove this conditional.
if not model_cache.loaded:
    model_cache.get_models()

admin.autodiscover()
handler404 = Dseo404.as_view()
handler500 = 'seo.views.search_views.dseo_500'

# secure.my.jobs redirects
urlpatterns = patterns('',
    url(r'^about/$',
        RedirectView.as_view(url='https://secure.my.jobs/about')),
    url(r'^account/$',
        RedirectView.as_view(url='https://secure.my.jobs/account/edit')),
    url(r'^candidates/$',
        RedirectView.as_view(url='https://secure.my.jobs/candidates/view')),
    url(r'^contact/$',
        RedirectView.as_view(url='https://secure.my.jobs/contact/')),
    url(r'^privacy/$',
        RedirectView.as_view(url='https://secure.my.jobs/privacy/')),
    url(r'^profile/$',
        RedirectView.as_view(url='https://secure.my.jobs/profile/view')),
    url(r'^savedsearch/$',
        RedirectView.as_view(url='https://secure.my.jobs/saved-search/view')),
    url(r'^terms/$',
        RedirectView.as_view(url='https://secure.my.jobs/terms/')),
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


from myjobs.views import About, Testimonials, Privacy, Terms

urlpatterns += patterns(
    '',
    url(r'^accounts/', include('registration.urls')),
    url(r'^about/$', About.as_view(), name='about'),
    url(r'^about/testimonials/$', Testimonials.as_view(), name='testimonials'),
    url(r'^privacy/$', Privacy.as_view(), name='privacy'),
    url(r'^terms/$', Terms.as_view(), name='terms'),
    url(r'^contact/$', 'contact', name='contact'),
    url(r'^contact-faq', 'contact_faq', name='contact_faq'),
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

