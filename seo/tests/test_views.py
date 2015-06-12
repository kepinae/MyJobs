# -*- coding: utf-8 -*-
from datetime import datetime
from copy import deepcopy
import default_settings
import itertools
import json
from StringIO import StringIO

from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.core.cache import cache
from django.contrib.flatpages.models import FlatPage
from django.contrib.redirects.models import Redirect
from django.template import Template, Context
from django.template import RequestContext as TemplateContext
from django.test.client import RequestFactory
from django.utils.http import urlquote
from django.core.urlresolvers import reverse

from BeautifulSoup import BeautifulSoup
from lxml import etree

from import_jobs import clear_solr, download_feed_file, update_solr
from xmlparse import DEv2JobFeed
from moc_coding import models as moc_models
from moc_coding.tests import factories as moc_factories
from myblocks.models import BlockOrder, Page, RowOrder
from myblocks.tests.factories import (ContentBlockFactory, PageFactory,
                                      RowFactory)
from myjobs.tests.factories import UserFactory
from postajob.models import SitePackage
from postajob.tests.factories import (JobFactory, JobLocationFactory,
                                      SitePackageFactory)
from seo import helpers
from seo.tests.setup import (connection, DirectSEOBase, DirectSEOTestCase,
                             patch_settings)
from seo.models import (BusinessUnit, Company, Configuration, CustomPage,
                        SeoSite, SeoSiteFacet, SiteTag, User, SeoSiteRedirect)
from seo.templatetags.seo_extras import url_for_sort_field
from seo.tests import factories
import solr_settings
from universal.helpers import build_url


class FallbackTestCase(DirectSEOTestCase):
    def setUp(self):
        super(FallbackTestCase, self).setUp()

        self.job = solr_settings.SOLR_FIXTURE[0]
        self.conn.add([self.job])

        self.site = SeoSite.objects.get()
        self.buid = BusinessUnit.objects.get_or_create(pk=self.job['buid'])
        self.site.business_units.add(self.job['buid'])
        self.site.save()

        self.content = 'This is a content block'

        self.config = Configuration.objects.get(status=2)
        self.config.home_page_template = 'home_page/home_page_listing.html'
        self.config.footer = ''
        self.config.save()

    def tearDown(self):
        self.conn.delete(q='*:*')

    def make_page(self, page_type):
        content = 'This is a content block'
        content_block = ContentBlockFactory(template=content)
        row = RowFactory()
        BlockOrder.objects.create(row=row, block=content_block, order=1)
        page = PageFactory(page_type=page_type, sites=(self.site, ))
        RowOrder.objects.create(page=page, row=row, order=1)

        return page

    def test_home_page_fallback(self):
        response = self.client.get(reverse('home'))
        # The default home_page_listing.html template should
        # result in a div with the class direct_joblisting.
        self.assertIn('"direct_joblisting"', response.content)

        self.make_page(Page.HOME_PAGE)

        response = self.client.get(reverse('home'))
        # The content block should be present, since there's
        # a Page.
        self.assertIn(self.content, response.content)
        self.assertNotIn('"direct_joblisting"', response.content)

    def test_job_detail_fallback(self):
        response = self.client.get(reverse('job_detail_by_job_id',
                                           kwargs={'job_id': self.job['guid']}),
                                   follow=True)
        # The job location be in the breadbox on the search results page.
        self.assertIn(self.job['location'], response.content)

        self.make_page(Page.JOB_DETAIL)

        response = self.client.get(reverse('job_detail_by_job_id',
                                           kwargs={'job_id': self.job['guid']}),
                                   follow=True)
        # The content block should be present, since there's
        # a Page.
        self.assertIn(self.content, response.content)
        self.assertNotIn(self.job['location'], self.content)

    def test_404_fallback(self):
        error_text = ('If you found this page from a job link, '
                      'then that job is expired.')

        response = self.client.get('/asldfjsadflasjfsdlafj/', follow=True)
        # The standard 404 error text should be on the 404 error page.
        self.assertIn(error_text, response.content)

        self.make_page(Page.ERROR_404)

        response = self.client.get('/asldfjsadflasjfsdlafj/', follow=True)
        # The content block should be present, since there's
        # a Page.
        self.assertIn(self.content, response.content)
        self.assertNotIn(error_text, self.content)

    def test_search_results_fallback(self):
        response = self.client.get(reverse('all_jobs'))
        self.assertIn('"direct_joblisting"', response.content)

        self.make_page(Page.SEARCH_RESULTS)

        response = self.client.get(reverse('all_jobs'))
        self.assertIn(self.content, response.content)
        self.assertNotIn('"direct_joblisting"', response.content)

    def test_search_results_no_results_fallback(self):
        self.conn.delete(q='*:*')
        error = 'There are no jobs that match:'

        url = build_url(reverse('all_jobs'), {'q': 'something'})
        response = self.client.get(url)
        self.assertIn(error, response.content)

        self.make_page(Page.NO_RESULTS)

        response = self.client.get(url)
        self.assertIn(self.content, response.content)
        self.assertNotIn(error, response.content)


class WidgetsTestCase(DirectSEOTestCase):
    """
    This test case makes sure that the facet builder does not display the
    more/less link unless there are enough *visible* items to warrent it.
    It runs through two sets of data, the first set has enough haystack
    slabs to require a more button. The second does not. This test will fail
    if the first data set does NOT have the more button html or if the second
    data set DOES contain the more button html.

    """
    fixtures = ['seo_views_testdata.json']
    
    def test_get_widget(self):        
        import widget_settings  # tuple of haystack slab sets
        resp = self.client.get("/")  # get the homepage
        site_config = resp.context['site_config'] # grab the current site config
        # for each dataset, instantiate and test a widget object.
        for facet_count in widget_settings.facet_counts:
            test_widget = helpers.get_widgets(resp.request, site_config,
                                              facet_count, [])
            for test in test_widget:
                widget_object = "%s" % test.render()
                # check the html result for more button class name
                more_string = 'class="more_less_links_container'
                # if there are hidden <li>, there must be more button
                if widget_object.find("direct_hiddenOption") == -1:
                    self.assertEqual(widget_object.find(more_string), -1)
                # if there are no hidden <li>, there are no more to show
                else:
                    self.assertNotEqual(widget_object.find(more_string), -1)


class SearchBoxTests(DirectSEOTestCase):
    fixtures = ['seo_views_testdata.json']

    def setUp(self):
        super(SearchBoxTests, self).setUp()
        # Add buid 0 to the site so we'll have jobs in the
        # "all_jobs" view.
        self.site = SeoSite.objects.get()
        bu = BusinessUnit.objects.get(id=0)
        self.site.business_units.add(bu)

        self.config = factories.ConfigurationFactory(status=2)
        self.site.configurations.add(self.config)

    def check_for_label_on_results_pages(self, label):
        # The label will be between two label tags.
        label = '>%s</label>' % label
        self.check_for_string_on_results_pages(label)

    def check_for_placeholder_on_results_pages(self, placeholder):
        # The placeholder will always show up inside a placeholder attribute.
        placeholder = 'placeholder="%s"' % placeholder
        self.check_for_string_on_results_pages(placeholder)

    def check_for_helptext_on_results_pages(self, helptext):
        # The helptext is always inside of a span.
        helptext = ">%s</span" % helptext
        self.check_for_string_on_results_pages(helptext)

    def check_for_string_on_results_pages(self, string):
        resp = self.client.get(reverse('home'))
        self.assertIn(string, resp.content)

        resp = self.client.get(reverse('all_jobs'))
        self.assertIn(string, resp.content)

    def test_custom_search_box_labels(self):
        # No custom where label added.
        # Regular search box.
        default_where_label = 'Where'
        default_what_label = 'What'
        default_moc_label = 'Military'

        self.check_for_label_on_results_pages(default_where_label)
        self.check_for_label_on_results_pages(default_what_label)

        # Search box vets.
        self.config.browse_moc_show = True
        self.config.save()
        self.check_for_label_on_results_pages(default_where_label)
        self.check_for_label_on_results_pages(default_what_label)
        self.check_for_label_on_results_pages(default_moc_label)

        # With custom label.
        custom_where_label = 'Custom Where'
        custom_what_label = 'Custom What'
        custom_moc_label = 'Custom Moc'

        # Regular search box.
        self.config.browse_moc_show = False
        self.config.where_label = custom_where_label
        self.config.save()
        self.check_for_label_on_results_pages(custom_where_label)
        self.config.what_label = custom_what_label
        self.config.save()
        self.check_for_label_on_results_pages(custom_what_label)

        # Search box vets.
        self.config.browse_moc_show = True
        self.config.save()
        self.check_for_label_on_results_pages(custom_where_label)
        self.check_for_label_on_results_pages(custom_what_label)
        self.config.moc_label = custom_moc_label
        self.config.save()
        self.check_for_label_on_results_pages(custom_moc_label)

    def test_custom_search_box_placeholders(self):
        # There are no default placeholders, so we can only check custom ones.
        custom_where_placeholder = 'Custom Where placeholder'
        custom_what_placeholder = 'Custom What placeholder'
        custom_moc_placeholder = 'Custom Moc placeholder'

        # Regular search box.
        self.config.where_placeholder = custom_where_placeholder
        self.config.save()
        self.check_for_placeholder_on_results_pages(custom_where_placeholder)
        self.config.what_placeholder = custom_what_placeholder
        self.config.save()
        self.check_for_placeholder_on_results_pages(custom_what_placeholder)

        # Search box vets.
        self.config.browse_moc_show = True
        self.config.save()
        self.check_for_placeholder_on_results_pages(custom_where_placeholder)
        self.check_for_placeholder_on_results_pages(custom_what_placeholder)
        self.config.moc_placeholder = custom_moc_placeholder
        self.config.save()
        self.check_for_placeholder_on_results_pages(custom_moc_placeholder)

    def test_custom_search_box_helptexts(self):
        # No custom where helptext added.
        # Regular search box.
        default_where_helptext = 'city, state, country'
        default_what_helptext = 'job title, keywords'
        default_moc_helptext = 'military job title or code'

        self.check_for_helptext_on_results_pages(default_where_helptext)
        self.check_for_helptext_on_results_pages(default_what_helptext)

        # Search box vets.
        self.config.browse_moc_show = True
        self.config.save()
        self.check_for_helptext_on_results_pages(default_where_helptext)
        self.check_for_helptext_on_results_pages(default_what_helptext)
        self.check_for_helptext_on_results_pages(default_moc_helptext)

        # With custom helptext.
        custom_where_helptext = 'Custom Where helptext'
        custom_what_helptext = 'Custom What helptext'
        custom_moc_helptext = 'Custom Moc helptext'

        # Regular search box.
        self.config.browse_moc_show = False
        self.config.where_helptext = custom_where_helptext
        self.config.save()
        self.check_for_helptext_on_results_pages(custom_where_helptext)
        self.config.what_helptext = custom_what_helptext
        self.config.save()
        self.check_for_helptext_on_results_pages(custom_what_helptext)

        # Search box vets.
        self.config.browse_moc_show = True
        self.config.save()
        self.check_for_helptext_on_results_pages(custom_where_helptext)
        self.check_for_helptext_on_results_pages(custom_what_helptext)
        self.config.moc_helptext = custom_moc_helptext
        self.config.save()
        self.check_for_helptext_on_results_pages(custom_moc_helptext)


class SeoSiteTestCase(DirectSEOTestCase):
    fixtures = ['seo_views_testdata.json']

    def test_ajax_geolocation(self):
        base_url = reverse('ajax_geolocation_facet')
        site = SeoSite.objects.get()
        bu = BusinessUnit.objects.get(id=0)
        site.business_units.add(bu)

        resp = self.client.get(base_url)
        result = json.loads(resp.content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['count'], 2)

        test_path = '/retail-associate-розничная-ассоциированных/jobs-in/'
        with_path = '%s?filter_path=%s'
        with_path = with_path % (base_url, test_path)
        resp = self.client.get(with_path)
        result = json.loads(resp.content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['count'], 1)

        with_query_string = '%s?q=guid:%s'
        with_query_string = with_query_string % (base_url, '2'*32)
        resp = self.client.get(with_query_string)
        result = json.loads(resp.content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['count'], 1)

    def test_update_email_domain_no_access(self):
        # Not logged in
        resp = self.client.get(reverse('seosites_settings_email_domain_edit'))
        self.assertEqual(resp.status_code, 404)

        password = 'abcdef123456!!!!!!'
        user = UserFactory(password=password)
        credentials = {
            'username': user.email,
            'password': password
        }
        self.assertTrue(self.client.login(**credentials))

        # No company
        resp = self.client.get(reverse('seosites_settings_email_domain_edit'))
        self.assertEqual(resp.status_code, 404)

    def test_update_email_domain(self):
        company = factories.CompanyFactory(product_access=True)
        site = factories.SeoSiteFactory(canonical_company=company)
        site2 = factories.SeoSiteFactory(canonical_company=company)

        data = {
            str(site.pk): site.domain,
            str(site2.pk): site2.domain,
        }
        self.assertNotEqual(data[str(site.pk)], site.email_domain)
        self.assertNotEqual(data[str(site2.pk)], site2.email_domain)

        password = 'abcdef123456!!!!!!'
        user = UserFactory(password=password)
        factories.CompanyUserFactory(user=user, company=company)
        credentials = {
            'username': user.email,
            'password': password
        }
        self.assertTrue(self.client.login(**credentials))

        resp = self.client.post(reverse('seosites_settings_email_domain_edit'),
                                data=data, follow=False)

        self.assertEqual(resp.status_code, 302)
        site = SeoSite.objects.get(pk=site.pk)
        site2 = SeoSite.objects.get(pk=site2.pk)
        self.assertEqual(data[str(site.pk)], site.email_domain)
        self.assertEqual(data[str(site2.pk)], site2.email_domain)

    def test_special_characters(self):
        self.conn.delete(q='*:*')
        special_jobs = [
            {
                'django_id': '8888',
                'guid': '8888',
                'django_ct': 'seo.joblisting',
                'id': 'seo.joblisting.8888',
                'title': 'C#',
                'title_ac': 'C#',
                'title_exact': 'C#',
                'title_slab': 'c/jobs-in::c',
                'title_slab_exact': 'c/jobs-in::c',
                'title_slug': 'c',
                'uid': '8888',
                'buid': self.buid_id,
                'text': 'C#',
            },
            {
                'django_id': '7777',
                'guid': '7777',
                'django_ct': 'seo.joblisting',
                'id': 'seo.joblisting.7777',
                'title': 'C$',
                'title_ac': 'C$',
                'title_exact': 'C$',
                'title_slab': 'c/jobs-in::c',
                'title_slab_exact': 'c/jobs-in::c',
                'title_slug': 'c',
                'uid': '7777',
                'buid': self.buid_id,
                'text': 'C$',
            },
            {
                'django_id': '9998',
                'id': 'seo.joblisting.9998',
                'guid': '9998',
                'django_ct': 'seo.joblisting',
                'title': 'Just C',
                'title_ac': 'Just C',
                'title_exact': 'Just C',
                'title_slab': 'just-c/jobs-in::just-c',
                'title_slab_exact': 'just-c/jobs-in::just-c',
                'title_slug': 'just-c',
                'uid': '9998',
                'buid': self.buid_id,
                'text': 'Just C',
            },
            {
                'django_id': '9997',
                'id': 'seo.joblisting.9997',
                'guid': '9997',
                'django_ct': 'seo.joblisting',
                'title': 'AT&T',
                'title_ac': 'AT&T',
                'title_exact': 'AT&T',
                'title_slab': 'att/jobs-in::att',
                'title_slab_exact': 'att/jobs-in::att',
                'title_slug': 'att',
                'uid': '9997',
                'buid': self.buid_id,
                'text': 'AT&T',
            },
            {
                'django_id': '9996',
                'id': 'seo.joblisting.9996',
                'guid': '9996',
                'django_ct': 'seo.joblisting',
                'title': 'AT Also Has A T',
                'title_ac': 'AT Also Has A T',
                'title_exact': 'AT Also Has A T',
                'title_slab': 'at-also-has-a-t/jobs-in::at-also-has-a-t',
                'title_slab_exact': 'att/jobs-in::at-also-has-a-t',
                'title_slug': 'at-also-has-a-t',
                'uid': '9996',
                'buid': self.buid_id,
                'text': 'AT Also Has A T',
            }
        ]
        self.conn.add(special_jobs)
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()

        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            resp = self.client.get('/jobs/?q=C#', follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.context['default_jobs']), 1)

            resp = self.client.get('/jobs/?q=C$', follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.context['default_jobs']), 1)

            resp = self.client.get('/jobs/?q=AT%5C%26T', follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.context['default_jobs']), 1)

    def test_postajob(self):
        company = factories.CompanyFactory()
        jobs = []
        for i in range(0, 10):
            jobs.append({
                'key': settings.POSTAJOB_API_KEY,
                'id': i,
                'buid': self.buid_id,
                'city': 'Indianapolis',
                'company': company.id,
                'country': 'United States',
                'country_short': 'USA',
                'date_new': str(datetime.now()),
                'date_updated': str(datetime.now()),
                'description': 'This is a description of a job. It might contain 特殊字符.',
                'guid': i,
                'link': 'http://my.jobs/%s' % i,
                'on_sites': '0',
                'state': 'Indiana',
                'state_short': 'IN',
                'reqid': 7,
                'title': 'Job Title',
                'uid': i,
                'zipcode': '46268'
            })
            data = {
                'jobs': json.dumps(jobs),
                'key': settings.POSTAJOB_API_KEY
            }
            resp = self.client.get('/ajax/postajob/',
                                   data)
            self.assertEqual('{"jobs_added": %s}' % str(i+1), resp.content)

        # Confirm that all of the jobs got added to solr only once.
        solr_res = self.conn.search('is_posted:true', fl='guid').docs
        guids = [int(x['guid']) for x in solr_res]
        self.assertEqual(guids, range(0, 10))

    def test_deleteajob(self):
        guids = []
        jobs = []
        for i in range(0, 10):
            jobs.append({
                'uid': i,
                'guid': i,
                'is_posted': True,
                'id': i
            })
        self.conn.add(jobs)
        for i in range(0, 10):
            guids.append(i)
            data = {
                'guids': ",".join([str(g) for g in guids]),
                'key': settings.POSTAJOB_API_KEY
            }
            resp = self.client.get('/ajax/deleteajob/',
                                   data)
            self.assertEqual('{"jobs_deleted": %s}' % str(i+1), resp.content)

        solr_res = self.conn.search('is_posted:True', fl='guid').docs
        self.assertEqual(solr_res, [])

    def test_limiting_jobs_by_package(self):
        site = factories.SeoSiteFactory()
        resp = self.client.get('/jobs/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        self.assertEqual(resp.status_code, 200)
        # Start with two default jobs, availble on [0] (all sites)
        self.assertEqual(len(resp.context['default_jobs']), 2)

        # Add a posted job available on all sites [0], and another posted job
        # limited to site packages [3, 4]
        self.conn.add(solr_settings.POSTED_JOB_FIXTURE)

        package = SitePackage.objects.create(pk=1)
        package.sites.add(site)
        package.save()
        resp = self.client.get('/jobs/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['default_jobs']), 3)

        package.delete()
        package = SitePackage.objects.create(pk=3)
        package.sites.add(site)
        package.save()
        resp = self.client.get('/jobs/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['default_jobs']), 4)

        package.delete()
        package = SitePackage.objects.create(pk=4)
        package.sites.add(site)
        package.save()
        resp = self.client.get('/jobs/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['default_jobs']), 4)

        package.delete()
        package = SitePackage.objects.create(pk=5)
        package.sites.add(site)
        package.save()
        resp = self.client.get('/jobs/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['default_jobs']), 3)

    def test_limiting_job_detail_by_package(self):
        site = factories.SeoSiteFactory()
        bu = factories.BusinessUnitFactory(id=1000)
        config = factories.ConfigurationFactory()
        site.business_units.add(bu)
        site.configurations.add(config)
        site.save()
        site2 = factories.SeoSiteFactory(domain='somewhere.jobs', id=102,
                                         site_ptr_id=102)
        site2.business_units.add(bu)
        site2.configurations.add(config)
        site2.save()
        site3 = factories.SeoSiteFactory(domain='anywhere.jobs', id=112,
                                         site_ptr_id=112)
        site3.configurations.add(config)
        site3.save()
        self.conn.add(solr_settings.POSTED_JOB_FIXTURE)
        package = SitePackage.objects.create(pk=3)
        package.sites.add(site)
        package.save()

        # The posted job with guid '88888888888888888888888888888888' is
        # only available on site packages [3, 4] and therefore should be
        # available on site but not site2.
        resp = self.client.get('/88888888888888888888888888888888/job/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        expected = 'http://buckconsultants.jobs/indianapolis-in/retail-associate/88888888888888888888888888888888/job/'
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain[-1][0], expected)

        resp = self.client.get('/88888888888888888888888888888888/job/',
                               HTTP_HOST='somewhere.jobs', follow=True)
        expected = 'http://somewhere.jobs/'
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain[-1][0], expected)

        # Sites with no business unit should be able to access the job
        # anyway.
        resp = self.client.get('/88888888888888888888888888888888/job/',
                               HTTP_HOST='anywhere.jobs', follow=True)
        expected = 'http://anywhere.jobs/indianapolis-in/retail-associate/88888888888888888888888888888888/job/'
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.redirect_chain[-1][0], expected)

    def test_facet_unicode_title(self):
        group = factories.GroupFactory()
        site = factories.SeoSiteFactory(group=group)

        default_cf = factories.CustomFacetFactory.build(
            #default facet will return both jobs
            name="Default Facet",
            title=u'Розничная ассоциированных',
            show_production=True,
            group=group)
        default_cf.save()

        default_site_facet = factories.SeoSiteFacetFactory(
            customfacet=default_cf,
            seosite=site,
            facet_type=SeoSiteFacet.DEFAULT)
        default_site_facet.save()

        standard_cf = factories.CustomFacetFactory.build(
            #default facet will return both jobs
            name="Standard Facet",
            querystring=u'text:特殊字符',
            show_production=True,
            group=group)
        standard_cf.save()

        standard_site_facet = factories.SeoSiteFacetFactory(
            seosite=site,
            customfacet=standard_cf,
            facet_type=SeoSiteFacet.STANDARD)
        standard_site_facet.save()

        resp = self.client.get('/standard-facet/new-jobs/',
                               HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)

        default_jobs = resp.context['default_jobs']
        self.assertEqual(len(default_jobs), 1)
        self.assertEqual(resp.context['total_jobs_count'], 1)

    def test_facet_non_ascii_description(self):
        group = factories.GroupFactory()
        site = factories.SeoSiteFactory(group=group)

        default_cf = factories.CustomFacetFactory.build(
            #default facet will return both jobs
            name="Default Facet",
            querystring=u'text:特殊字符',
            show_production=True,
            group=group)
        default_cf.save()

        default_site_facet = factories.SeoSiteFacetFactory(
            customfacet=default_cf,
            seosite=site,
            facet_type=SeoSiteFacet.DEFAULT)
        default_site_facet.save()

        standard_cf = factories.CustomFacetFactory(
            #default facet will return both jobs
            name="Standard Facet",
            querystring=u'text:特殊字符',
            show_production=True,
            group=group)
        standard_cf.save()

        standard_site_facet = factories.SeoSiteFacetFactory(
            seosite=site,
            customfacet=standard_cf,
            facet_type=SeoSiteFacet.STANDARD)
        standard_site_facet.save()

        resp = self.client.get('/standard-facet/new-jobs/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        self.assertEqual(resp.status_code, 200)

        default_jobs = resp.context['default_jobs']
        self.assertEqual(len(default_jobs), 1)
        self.assertEqual(resp.context['total_jobs_count'], 1)

    def test_bad_lookup_value(self):
        """ 
            Tests the use of else block in the solr_ac view when
            the lookup is neither title nor location
        """
        resp1 = self.client.get(u'/ajax/ac/?lookup=title&term=developer')
        resp2 = self.client.get(u'/ajax/ac/?lookup=location&term=california')
        resp3 = self.client.get(u'/ajax/ac/?lookup=bad_value&term=california')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        # when lookup was neither title nor location, request 
        #returns a page which has None([]) as content
        self.assertNotEqual(resp3.status_code, 500)

    def test_facet_reserved_word_search(self):
        site = factories.SeoSiteFactory.build()
        site.save()
        default_cf = factories.CustomFacetFactory.build(
                #default facet will return both jobs
                name="Default Facet",
                querystring=u'state_short_exact:IN')

        default_cf.save()
        default_site_facet = factories.SeoSiteFacetFactory(
            seosite=site, facet_type=SeoSiteFacet.DEFAULT)
        default_site_facet.save()

        resp = self.client.get('/jobs/',
                               HTTP_HOST='buckconsultants.jobs', follow=True)
        self.assertEqual(resp.status_code, 200)

        default_jobs = resp.context['default_jobs']
        self.assertEqual(len(default_jobs), 2)
        self.assertEqual(resp.context['total_jobs_count'], 2)

    def test_dup_featured_facets(self):
        """
        Regression test, using the same custom facet in a Site for both
        featured and default facets caused a 500 error
        
        """
        site = factories.SeoSiteFactory.build()
        site.save()

        default_cf = factories.CustomFacetFactory.build(
            # default facet will return both jobs
            name="Default Facet",
            querystring=
            u'id:({i1} OR {i2})'.format(
                i1=self.solr_docs[0]['id'],
                i2=self.solr_docs[1]['id']))
        default_cf.save()
        
        factories.SeoSiteFacetFactory(
            customfacet=default_cf,
            seosite=site,
            facet_type=SeoSiteFacet.DEFAULT)

        factories.SeoSiteFacetFactory(
            customfacet=default_cf,
            seosite=site,
            facet_type=SeoSiteFacet.FEATURED)

        resp = self.client.get('/', HTTP_HOST='buckconsultants.jobs',
                               follow=True)

        self.assertEqual(resp.status_code, 200)

    def test_featured_facets(self):
        """
        Tests that default and featured facets are applied correctly and don't
        return duplicate jobs.

        """
        group = factories.GroupFactory()
        site = factories.SeoSiteFactory(group=group)

        default_job = self.solr_docs[0]
        featured_job = self.solr_docs[1]

        default_cf = factories.CustomFacetFactory.build(
            #default facet will return both jobs
            name="Default Facet",
            querystring=u'id:({i1} OR {i2})'.format(
                i1=self.solr_docs[0]['id'],
                i2=self.solr_docs[1]['id']),
            group=group)
        default_cf.save()

        featured_cf = factories.CustomFacetFactory.build(
            #featured facet will return 1 job
            name="Featured Facet",
            querystring='id:({i1} OR {i2}) AND uid:{u}'.format(
                i1=self.solr_docs[0]['id'],
                i2=self.solr_docs[1]['id'],
                u=featured_job['uid']),
            group=group)
        featured_cf.save()
 
        factories.SeoSiteFacetFactory(customfacet=default_cf,
                                      seosite=site,
                                      facet_type=SeoSiteFacet.DEFAULT)

        factories.SeoSiteFacetFactory(
            customfacet=featured_cf,
            seosite=site,
            facet_type=SeoSiteFacet.FEATURED)

        resp = self.client.get('/jobs/', HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)

        default_jobs = resp.context['default_jobs']
        self.assertEqual(len(default_jobs), 1)
        self.assertEqual(resp.context['total_jobs_count'], 2)
        self.assertEqual(str(default_jobs[0].uid), default_job['uid'])

        featured_jobs = resp.context['featured_jobs']
        self.assertEqual(len(featured_jobs), 1)
        self.assertEqual(str(featured_jobs[0].uid), featured_job['uid'])

        resp = self.client.get('/', HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)

        default_jobs = resp.context['default_jobs']
        self.assertEqual(len(default_jobs), 1)
        self.assertEqual(resp.context['total_jobs_count'], 2)
        self.assertEqual(str(default_jobs[0].uid), default_job['uid'])

        featured_jobs = resp.context['featured_jobs']
        self.assertEqual(len(featured_jobs), 1)
        self.assertEqual(str(featured_jobs[0].uid), featured_job['uid'])

        resp = self.client.get('/ajax/joblisting/?offset=1&num_items=2',
                               HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)

        default_jobs = resp.context['default_jobs']
        self.assertEqual(len(default_jobs), 1)
        self.assertEqual(str(default_jobs[0].uid), default_job['uid'])

        featured_jobs = resp.context['featured_jobs']
        self.assertEqual(len(featured_jobs), 0)

        resp = self.client.get('/ajax/joblisting/?offset=0&num_items=1',
                               HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)

        default_jobs = resp.context['default_jobs']
        self.assertEqual(len(default_jobs), 0)

        featured_jobs = resp.context['featured_jobs']
        self.assertEqual(len(featured_jobs), 1)

    def test_default_custom_facets_homepage(self):
        """
        Tests that custom facets are applied to ajax_get_jobs when viewing all
        jobs. 
        
        """
        site = factories.SeoSiteFactory.build()
        site.save()
        site_job = self.solr_docs[1]

        default_cf = factories.CustomFacetFactory.build(
            # This querystring should return 1 result for the matching uid
            querystring='id:({i1} OR {i2}) AND uid:{u}'.format(
                i1=self.solr_docs[0]['id'],
                i2=self.solr_docs[1]['id'],
                u=site_job['uid']))

        default_cf.save()

        factories.SeoSiteFacetFactory(customfacet=default_cf,
                                      seosite=site,
                                      facet_type=SeoSiteFacet.DEFAULT)
        
        resp = self.client.get('/jobs/', follow=True,
                               HTTP_HOST='buckconsultants.jobs')

        self.assertEqual(resp.status_code, 200)
        all_jobs = resp.context['default_jobs']
        self.assertEqual(len(all_jobs), 1)
        self.assertEqual(resp.context['total_jobs_count'], 1)
        self.assertEqual(str(all_jobs[0].uid), site_job['uid'])

        #This querystring should return two jobs 
        default_cf.querystring = 'id:({i}) OR uid:{u}'.format(
            i=self.solr_docs[0]['id'],
            u=site_job['uid'])
        default_cf.save()
        resp = self.client.get('/jobs/', follow=True,
                               HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)
        all_jobs = resp.context['default_jobs']
        self.assertEqual(len(all_jobs), 2)

        #This querystring should return one job
        default_cf.querystring = '(id:{i} AND uid:{u}) OR uid:{u}'.format(
            i=self.solr_docs[0]['id'],
            u=site_job['uid'])
        default_cf.save()
        resp = self.client.get('/jobs/', follow=True,
                               HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)
        all_jobs = resp.context['default_jobs']
        self.assertEqual(len(all_jobs), 1)
        self.assertEqual(str(all_jobs[0].uid), site_job['uid'])

    def test_custom_ajax_get_facets(self):
        site = factories.SeoSiteFactory.build()
        site.save()
        site_job = self.solr_docs[1]

        query_strings = [
            #shoudln't match anything
            'lksjadfionv',
            #testing more complex queries
            'city:("Indianapolis" OR "Norfolk") AND state:Indiana'
        ]

        facet_fields = ['facets', 'titles', 'cities', 'states', 'mocs',
                        'countries', 'facets', 'company-facets']
 
        for query in query_strings:
            default_cf = factories.CustomFacetFactory.build(querystring=query)
            default_cf.save()

            factories.SeoSiteFacetFactory(customfacet=default_cf,
                                          seosite=site,
                                          facet_type=SeoSiteFacet.DEFAULT)

            site = SeoSite.objects.get(id=1)
            for field in facet_fields:
                resp = self.client.get("/ajax/{f}/".format(f=field))
                self.assertEqual(resp.status_code, 200)

    def test_unicode_job_detail_redirect(self):
        """
        Regression test - Urls with escaped utf-8 characters were causing
        database errors when the django_redirect table used a non utf8 character
        set.
        """
        resp = self.client.get('virtual-usa/asystentka-dzia%C5%82u/34215982/job/')
        # This can be a redirect or 404, so we just check against a 500 error
        self.assertNotEqual(resp.status_code, 500)

    def test_custom_moc(self):
        """
        Regression test on a series of default and custom moc mappings. Checks
        two-to-one and one-to-two moc-onet mappings, which were returning 
        null search results - Ticket MS-378

        """
        # MOC and Onet are not typically retrieved in the search results,
        # so we need to add them.
        base_search_fields = deepcopy(helpers.search_fields)
        helpers.search_fields += ['onet', 'moc']

        moc_id = "4105"
        moc_code = "1343"

        #Create two jobs and save them to Solr
        default_job = deepcopy(self.solr_docs[0])
        default_job.update({
            'buid': '1',
            'moc': moc_code,
            'mocid': moc_id,
            'mapped_moc': moc_code,
            'mapped_mocid': moc_id,
            'onet': '1234'
        })

        custom_job = deepcopy(self.solr_docs[1])
        custom_job.update({
            'buid': '1',
            'mocid': moc_id+"100",
            'onet': '2345'
        })

        self.conn.add([default_job, custom_job])
        
        #Perform a search by moc code, Solr should be queried by that moc code
        resp = self.client.get('/jobs/?location=&q=&moc=%s' % moc_code,
                               follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['default_jobs']) == 1)
        self.assertIn(default_job['onet'],
                      resp.context['default_jobs'][0].onet)

        moc = moc_factories.MocFactory.build(code=moc_code, branch="army",
                                             id=4105)
        moc.save()

        #Perform a search by moc with an moc_models.Moc object in ORM 
        #Solr should now be queried by mocid, but the result should still
        #be default_job
        resp = self.client.get('/jobs/?&moc=%s' % moc_code)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['default_jobs']) == 1)
        self.assertIn(default_job['onet'],
                      resp.context['default_jobs'][0].onet)

        default_onet = moc_factories.OnetFactory.build(code=default_job['onet'])
        default_onet.save()

        custom_onet = moc_factories.OnetFactory.build(code=custom_job['onet'])
        custom_onet.save()

        custom_career = moc_factories.CustomCareerFactory.build(
            moc=moc, object_id=self.buid_id, onet_id=custom_onet.code)
        custom_career.save()

        bu = BusinessUnit.objects.get(id=1)
        bu.customcareers = [custom_career]
        bu.save()

        default_job.update({
            'buid': '1',
            'mapped_moc': None,
            'mapped_mocid': None,
            'onet': '1234'
        })
        custom_job.update({
            'buid': '1',
            'mapped_moc': [moc],
            'mapped_mocid': [moc.id]
        })

        self.conn.delete(q='*:*')
        self.conn.add([default_job, custom_job])

        #Perform a search by moc with a custom_career mapping. Search result 
        #should be custom job
        resp = self.client.get('/jobs/?moc=%s' % moc_code)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['default_jobs']) == 1)
        self.assertIn(custom_onet.code,
                      resp.context['default_jobs'][0].onet)

        custom_career2 = moc_factories.CustomCareerFactory.build(moc=moc,
                                                                 object_id=self.buid_id,
                                                                 onet_id=default_onet.code)
        custom_career2.save()
        bu.customcareers = [custom_career, custom_career2]
        bu.save()

        default_job.update({
            'buid': '1',
            'mapped_moc': [moc],
            'mapped_mocid': [moc.id],
            'onet': '1234'
        })

        self.conn.add([default_job])

        #Now there is 1 moc mapped to two different onets. Both jobs should
        #match the query
        resp = self.client.get('/jobs/?moc=%s' % moc_code)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['default_jobs']) == 2)

        moc2 = moc_factories.MocFactory.build(code=moc_code, branch="navy",
                                              moc_detail=moc_factories.MocDetailFactory())
        moc2.save()
        custom_career2.moc_id=moc2.id
        custom_career2.onet_id = custom_onet.code
        custom_career2.save()
        bu.customcareers = [custom_career, custom_career2]
        bu.save()

        default_job.update({
                    'buid':'1',
                    'mapped_moc':None,
                    'mapped_mocid':None,
                    'onet':'1234'})
        self.conn.add([default_job])

        #Now there are 2 mocs mapped to custom_onet. Only custom_job should
        #match the query
        resp = self.client.get('/jobs/?moc=%s' % moc_code)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['default_jobs']) == 1)
        self.assertIn(custom_onet.code,
                      resp.context['default_jobs'][0].onet)

        # Reset the search_fields so onet and moc are no longer retrieved.
        helpers.search_fields = base_search_fields


class TemplateTestCase(DirectSEOTestCase):
    fixtures = ['seo_views_testdata.json']
    
    def setUp(self):
        super(TemplateTestCase, self).setUp()
        self.site = factories.SeoSiteFactory.build(id=1)
        self.site.save()
        settings.SITE=self.site

    def test_xss_job_list(self):
        template = Template(file("templates/includes/job_list.html", 'r').read())
        context = Context({'location_term': '%27%22%3E%3Cimg+src%3Dx+onerror%3Dalert%28document.cookie%29%3E'})
        resp = template.render(context)
        self.assertEqual(resp.find('"><img src=x onerror=alert(document.cookie)>'), -1)


    def test_xss_job_listing(self):
        settings.SITE_TITLE = "Acme"
        settings.SITE_DESCRIPTION = "test"
        settings.SITE_HEADING = "test"
        settings.SITE_TAGS = ["network"]

        config = factories.ConfigurationFactory.build()
        request =RequestFactory().get('/job/')
        request.user = AnonymousUser()
        template = Template(file("templates/job_listing.html", 'r').read())
        resp = template.render(TemplateContext(request,
            {'location_term':'%27%22%3E%3Cimg+src%3Dflerg+onerror%3Dalert%28document.cookie%29%3E',
                                                         'site_config':config}))
        #Check string from view_all_jobs_label
        self.assertEqual(resp.find('"><img src=x onerror=alert(document.cookie)>'), -1)

 
    def test_view_all_jobs_label(self):
        bu = BusinessUnit.objects.get(id=1)
        bu.title="Acme"
        bu.save()
        self.site.business_units.add(bu)        
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        settings.SITE_TITLE = "Acme Ohio Jobs"
        #test with view_all_jobs_detail = False (default)
        template = Template(
                "{% load seo_extras %}"
                "{% view_all_jobs_label site_config.view_all_jobs_detail%}")
        resp = template.render(TemplateContext(request))
        self.assertEqual(resp,"View All Jobs")
        #test with view_all_jobs_detail = True
        config = factories.ConfigurationFactory.build(id=2)
        config.view_all_jobs_detail = True
        config.save()
        self.site.configurations.clear()
        self.site.configurations.add(config)
        cache.clear()
        request.site_config = config
        template = Template(
                "{% load seo_extras %}"
                "{% view_all_jobs_label site_config.view_all_jobs_detail %}")
        resp = template.render(TemplateContext(request))
        #Check string from view_all_jobs_label
        self.assertEqual(resp, "View All Ohio Jobs")

    def test_view_all_jobs_label_bad_bu_title(self):
        """
        A regression test. We were getting 500 errors when business units
        with null titles were assigned to a site with a custom view all jobs
        label
        """
        bu = BusinessUnit.objects.get(id=1)
        bu.title=None
        bu.save()
        self.site.business_units.add(bu)        
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        settings.SITE_TITLE = "Acme Ohio Jobs"
        #test with view_all_jobs_detail = False (default)
        template = Template(
                "{% load seo_extras %}"
                "{% view_all_jobs_label site_config.view_all_jobs_detail%}")
        resp = template.render(TemplateContext(request))
        self.assertEqual(resp,"View All Jobs")
        config = factories.ConfigurationFactory.build(id=2)
        config.view_all_jobs_detail=True        
        config.save()        
        self.site.configurations.clear()
        self.site.configurations.add(config)
        cache.clear()
        request.site_config = config
        template = Template(
                "{% load seo_extras %}"
                "{% view_all_jobs_label site_config.view_all_jobs_detail %}")
        resp = template.render(TemplateContext(request))
        #Check string from view_all_jobs_label
        self.assertEqual(resp,"View All Acme Ohio Jobs")        

    def test_search_box_template(self):
        config = factories.ConfigurationFactory.build()
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        template = Template(file("templates/search_box.html", 'r').read())
        resp = template.render(TemplateContext(request, {'site_config':config}))
        #Check string from view_all_jobs_label
        self.assertIn("View All Jobs", resp)

    def test_search_box_vets_template(self):
        """Renders search_box_vets.html"""
        config = factories.ConfigurationFactory.build()
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        template = Template(file("templates/search_box_vets.html", 'r').read())
        resp = template.render(TemplateContext(request, {'site_config':config}))
        #Check string from view_all_jobs_label
        self.assertIn("View All Jobs", resp)

    def test_seo_base_template(self):
        """Renders seo_base.html"""
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        settings.SITE_TITLE = "Acme"        
        template = Template(file("templates/seo_base.html", 'r').read())
        resp = template.render(TemplateContext(request, {}))
        #Check string from view_all_jobs_label
        self.assertIn("View All Jobs", resp)
        
    def test_seo_no_sponsor_logo_network_site(self):
        """Check that the empty sponsor logo function is rendered on
        network sites with no sponsor set"""
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        settings.SITE_TITLE = "Acme"
        settings.SITE_DESCRIPTION = "test"
        settings.SITE_HEADING = "test"
        settings.SITE_TAGS = ["network"]
        template = Template(
            file("templates/seo_billboard_homepage_base.html", 'r').read())
        resp = template.render(TemplateContext(request, {'widgets':'',
                                                         'site_tags':'["network"]'}))
        self.assertIn('BuildSponsorLogo("",""));', resp)
    
    def test_seo_sponsor_logo_network_site(self):
        """Check that the sponsor logo function is rendered with data on
        network sites with a sponsor set"""
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        settings.SITE_TITLE = "Acme"
        bb = factories.BillboardImageFactory.build()
        bb.save()        
        settings.SITE.billboard_images.add(bb)        
        template = Template(
            file("templates/seo_billboard_homepage_base.html", 'r').read())
        resp = template.render(
            TemplateContext(
                request, {
                    'widgets':'',
                    'billboard_images':settings.SITE.billboard_images.all(),
                    'site_tags':['network'],                    
                    }
                )
            )
        self.assertIn('BuildSponsorLogo(billboard_list[0].logo_url,', resp)
        
    def test_seo_no_sponsor_logo_company_site(self):
        """Check that the empty sponsor logo function is not rendered on
        company sites with no sponsor set"""
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        config_obj = factories.ConfigurationFactory.build(id=1)
        config_obj.wide_header = "abcdefg"
        site = factories.SeoSiteFactory()
        site.configurations.add(config_obj)
        site.save()
        settings.SITE = site
        settings.SITE_TITLE = "Acme"
        settings.SITE_DESCRIPTION = "test"
        settings.SITE_HEADING = "test"
        settings.SITE_TAGS = ["network"]
        settings.VIEW_SOURCE = None
        bb = factories.BillboardImageFactory(logo_url="", sponsor_url="")
        site.billboard_images.add(bb)
        site.save()
        template = Template(
            file("templates/seo_billboard_homepage_base.html", 'r').read())
        resp = template.render(
            TemplateContext(
                request, {
                    'widgets': '',
                    'billboard_images': settings.SITE.billboard_images.all(),
                    'site_tags': ['company'],
                }
            )
        )
        self.assertNotIn('BuildSponsorLogo(billboard_list[0].logo_url,', resp)
        
    def test_seo_sponsor_logo_company_site(self):
        """Check that the sponsor logo function is rendered on
        company sites with a sponsor set"""
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        config_obj = factories.ConfigurationFactory.build(id=1)
        config_obj.wide_header = "abcdefg"
        site = factories.SeoSiteFactory()
        site.configurations.add(config_obj)
        site.save()
        settings.SITE = site
        settings.SITE_TITLE = "Acme"        
        bb = factories.BillboardImageFactory.build()
        bb.save()        
        settings.SITE.billboard_images.add(bb)        
        template = Template(
            file("templates/seo_billboard_homepage_base.html", 'r').read())
        resp = template.render(
            TemplateContext(
                request, {
                    'widgets': '',
                    'billboard_images': settings.SITE.billboard_images.all(),
                    'site_tags': ['company'],
                }
            )
        )
        self.assertIn('BuildSponsorLogo(billboard_list[0].logo_url,', resp)        

    def test_smart_truncate(self):
        """Test that the smart truncate template tag properly reduces the the
        allowable width for double wide unicode characters"""
        from seo.templatetags.seo_extras import smart_truncate
        std_string = "This is a 48 character string. It is non-unicode"
        uni_string =u"This is a 48 character string. It is unicode7890"
        eas_string =u"(特殊字符特殊字符) A 48 char string w wide E Asian glifs"
        self.assertEqual(smart_truncate(std_string),
                         "This is a 48 character string. I...")
        self.assertEqual(smart_truncate(uni_string),
                         u"This is a 48 character string. I...")
        self.assertEqual(smart_truncate(eas_string),
                         u"(特殊字符特殊字符) A 48 char str...")

    
class SeoViewsTestCase(DirectSEOTestCase):
    fixtures = ['seo_views_testdata.json']

    def test_sort(self):
        """
        Confirm that Sort by links are showing up on the search results
        pages.

        """
        site = factories.SeoSiteFactory()
        site.business_units.add(self.buid_id)
        site.save()

        response = self.client.get('/jobs/', HTTP_HOST=site.domain)
        self.assertIn('?sort=date', response.content)

        response = self.client.get('/jobs/?sort=date', HTTP_HOST=site.domain)
        self.assertIn('?sort=relevance', response.content)

    def test_sort_jobs(self):
        """
        Confirm that sorting is actually being applied and works as desired.

        """
        site = factories.SeoSiteFactory()
        site.business_units.add(self.buid_id)
        site.save()

        response = self.client.get('/jobs/?q=Retail Associate',
                                   HTTP_HOST=site.domain)
        jobs = response.context['default_jobs']
        self.assertEqual(jobs[0].pk, '2')

        response = self.client.get('/jobs/?q=Retail Associate&sort=date',
                                   HTTP_HOST=site.domain)
        jobs = response.context['default_jobs']
        self.assertEqual(jobs[0].pk, '1')

    def test_xss_job_listing(self):
        resp = self.client.get(
                '/jobs/?q=%27%22%3E%3Cimg+src%3Dx+onerror%3Dalert%28document.cookie%29%3E' +
                '&location=%27%22%3E%3Cimg+src%3Dy+onerror%3Dalert%28document.cookie%29%3E' +
                '&moc=%27%22%3E%3Cimg+src%3Dz+onerror%3Dalert%28document.cookie%29%3E',
                HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.content.find('"><img src=x onerror=alert(document.cookie)>'), -1)
        self.assertEqual(resp.content.find('"><img src=y onerror=alert(document.cookie)>'), -1)
        self.assertEqual(resp.content.find('"><img src=z onerror=alert(document.cookie)>'), -1)

    def test_no_markdown_highlight(self):
        site = factories.SeoSiteFactory.build()
        site.save()
        config = factories.ConfigurationFactory.build()
        config.status = 2
        config.save()
        site.configurations.add(config)
        removed_characters = ('**', '<br>', '##', '<testh1>',
                              '</testh1>', '<p>', )
        preserved_strings = ('#hashtag', '* asterisks', '= equals',
                             u'特殊字符', )
        # Test that markdown businessunits do not have newlines converted to
        # breaks
        results = DEv2JobFeed('seo/tests/data/dseo_feed_0.xml',
                              jsid=self.businessunit.id,
                              markdown=self.businessunit.enable_markdown)
        job = results.solr_jobs()[1]
        self.conn.add([job])
        resp = self.client.get('/jobs/?q=bold_markdown',
                               HTTP_HOST='buckconsultants.jobs')
        soup = BeautifulSoup(resp.content)
        resp.content = soup.find('div', {'class': 'directseo_jobsnippet'})
        for mark in removed_characters:
            self.assertNotContains(resp, mark)
        for preserved in preserved_strings:
            self.assertContains(resp, preserved)

    def test_xss_job_listing_bread_box(self):
        site = factories.SeoSiteFactory.build()
        site.save()
        config = factories.ConfigurationFactory.build()
        config.status = 2
        config.save()
        site.configurations.add(config)
        resp = self.client.get('/usa/jobs/?P=\"><script>524199182',
                               HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.content.find('<script>524199182'), -1)
        self.assertContains(resp, 'script%3E524199182')
        resp = self.client.get(
            '/indianapolis/indiana/usa/jobs/?P=\"><script>120341734',
            HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.content.find('<script>120341734'), -1)
        self.assertContains(resp,
                            '"loc_up_bread_box" href="/indiana/usa/jobs/?P=%22%3E%3Cscript%3E120341734"')

    def test_location_redirect(self):
        """
        Checks the url to make sure the most recently changed
        location selection method (slug or query) is being used.

        """
        queries = [
            {'referer': '/salt-lake-city/utah/usa/jobs/',
             'url': '/salt-lake-city/utah/usa/jobs/?location=Ogden, UT&q=',
             'result': '/jobs/?location=Ogden%2C+UT'},
            {'referer': '/jobs/?location=Ogden, UT&q=',
             'url': '/salt-lake-city/utah/usa/jobs/?q=cashier&location=Ogden, UT',
             'result': '/salt-lake-city/utah/usa/jobs/?q=cashier'},
            {'referer': '',
             'url': '/salt-lake-city/utah/usa/jobs/?q=&location=Ogden, UT',
             'result': '/jobs/?location=Ogden%2C+UT'},
            {'referer': '',
             'url': '/jobs/?q=&location=Ogden, UT',
             'result': '/jobs/?location=Ogden%2C+UT'},
            {'referer': '',
             'url': '/salt-lake-city/utah/usa/jobs/?q=cashier&location=',
             'result': '/salt-lake-city/utah/usa/jobs/?q=cashier'},
            {'referer': '',
             'url': '/jobs/?q=cashier&location=',
             'result': '/jobs/?q=cashier'},
            {'referer': '/jobs/?q=&location=Ogden, UT',
             'url': '/jobs/?q=cashier&location=Ogden, UT',
             'result': '/jobs/?q=cashier&location=Ogden, UT'},
            {'referer': '/salt-lake-city/utah/usa/jobs/',
             'url': '/salt-lake-city/utah/usa/jobs/?location=&q=cashier',
             'result': '/salt-lake-city/utah/usa/jobs/?q=cashier'},
            {'referer': '',
             'url': '/louisville/kentucky/usa/jobs/?q=Security+Officer+保安员&location=Louisville%2C+KY',
             'result': '/jobs/?q=Security+Officer+%E4%BF%9D%E5%AE%89%E5%91%98&location=Louisville%2C+KY'},
        ]

        for query in queries:
            response = self.client.get(query['url'], follow=True,
                                       HTTP_REFERER=query['referer'])
            qs = response.context['request'].META.get('QUERY_STRING', None)
            path = response.context['request'].path
            result_url = "%s?%s" % (path, qs) if qs else path
            self.assertEqual(result_url, query['result'])

    def test_moc_redirect(self):
        """
        Checks the url to make sure the most recently changed
        moc selection method (slug or query) is being used.

        """
        queries = [
            {'referer': '/material-management-officer/8862/marines/vet-jobs/',
             'url': '/material-management-officer/8862/marines/vet-jobs/?location=&q=&moc=9662&moc_id=',
             'result': '/jobs/?moc=9662'},
            {'referer': '/jobs/?q=&moc=9662&moc_id=&location=',
             'url': '/material-management-officer/8862/marines/vet-jobs/?location=&q=cashier&moc=9662&moc_id=',
             'result': '/material-management-officer/8862/marines/vet-jobs/?q=cashier'},
            {'referer': '',
             'url': '/material-management-officer/8862/marines/vet-jobs/?location=&q=&moc=9662&moc_id=',
             'result': '/jobs/?moc=9662'},
            {'referer': '',
             'url': '/jobs/?q=&moc=9662&moc_id=&location=',
             'result': '/jobs/?moc=9662'},
            {'referer': '',
             'url': '/material-management-officer/8862/marines/vet-jobs/?location=&q=cashier&moc=&moc_id=',
             'result': '/material-management-officer/8862/marines/vet-jobs/?q=cashier'},
            {'referer': '',
             'url': '/jobs/?location=&q=cashier&moc=&moc_id=',
             'result': '/jobs/?q=cashier'},
            {'referer': '/jobs/?q=&moc=9662&moc_id=&location=',
             'url': '/jobs/?q=cashier&moc=9662&moc_id=&location=',
             'result': '/jobs/?q=cashier&moc=9662'},
            {'referer': '/material-management-officer/8862/marines/vet-jobs/',
             'url': '/material-management-officer/8862/marines/vet-jobs/?q=cashier&moc=&moc_id=&location=',
             'result': '/material-management-officer/8862/marines/vet-jobs/?q=cashier'},
        ]

        for query in queries:
            response = self.client.get(query['url'], follow=True,
                                       HTTP_REFERER=query['referer'])
            qs = response.context['request'].META.get('QUERY_STRING', None)
            path = response.context['request'].path
            result_url = "%s?%s" % (path, qs) if qs else path
            self.assertEqual(result_url, query['result'])

    def test_search_redirect(self):
        """
        Confirms that /search? is redirecting to /jobs/? while preserving the
        query string.

        """
        response = self.client.get("/search?q=cashier&location=Utah",
                                   follow=True)
        response_qs = response.context['request'].META['QUERY_STRING']
        response_path = response.context['request'].path
        self.assertEqual("%s?%s" % (response_path, response_qs),
                         '/jobs/?q=cashier&location=Utah')

    def test_hashtag_search(self):
        results = self.conn.search("description:#job", fl="uid").docs
        self.assertEqual(results, [{u'uid': 1000}])
    
    def build_slug_tag_paths(self, SLUG_TAGS, reverse=False):
        """Builds a list of url filter paths from a slug tag dictionary"""
        paths = []
        rev_paths = []
        rev = reversed if reverse else lambda x:x
        for i in range(2, len(SLUG_TAGS)):
            #Merge key-value slug tag pairs into a single-tag filter path
            tag_paths = [''.join([key, value]) for key,value in SLUG_TAGS.items()]
            tag_combos = itertools.combinations(tag_paths, i)
            #Merge combinations of tag paths into single paths
            n_paths = ['/%s' % ''.join(rev(combo)) for combo in tag_combos]
            paths.extend(n_paths)
        return paths

    def test_view_all_jobs(self):
        site = factories.SeoSiteFactory.build()
        site.save()
        resp = self.client.get(
                '/jobs/',
                HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(resp.context['default_jobs'], 0)

    def test_slug_tag_permanent_redirect(self):
        """Filter paths not in canonical order result in a 301 to the canonical
        path"""
        paths = self.build_slug_tag_paths(
                default_settings.SLUG_TAGS, reverse=True)
        targets = self.build_slug_tag_paths(default_settings.SLUG_TAGS)
        for (path,target) in zip(paths, targets):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 301)
            domain = "http://testserver"
            domain_target = "{d}{t}".format(d=domain, t=target)
            self.assertEqual(resp.get('location'), domain_target)

    def test_slug_tag_redirect(self):
        """Filter paths in canonical order don't result in a redirect"""
        paths = self.build_slug_tag_paths(default_settings.SLUG_TAGS)
        for path in paths:
            resp = self.client.get(path)
            #job_listing_by_slug tag can return a 200, 302, or 404 depending
            #on the filters and job data available. For now we'll ensure
            #it's not getting caught by slug_tag_redirect and returing a 301
            self.assertNotEqual(resp.status_code, 301)

    def test_feed_link_querystring(self):
        # Make sure that links from feed that include a query string aren't
        # stripped of the query string by the redirect to the canonical URL
        site = factories.SeoSiteFactory.build()
        site.save()        
        resp = self.client.get('/indeed/1000/job?src=indeed_test', 
            follow=True, HTTP_HOST='buckconsultants.jobs')
        target_path = u'indianapolis-in/retail-associate-розничная-ассоциированных/11111111111111111111111111111111/job/?utm_source=indeed&utm_medium=feed&src=indeed_test'
        quoted_path = urlquote(target_path, safe='&:=?/')
        target = u'http://buckconsultants.jobs/{0}'.format(quoted_path)
        self.assertRedirects(resp,target,status_code=301)

    def test_site_map(self):
        resp = self.client.get('/sitemap.xml')
        self.assertEqual(resp.status_code, 200)

    def test_home_page(self):
        self.assertTrue(self.client.login(email='matt@directemployers.org',
                                          password='lingo23'))
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(resp.context['site_config'].id), 1)
        self.client.logout()
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(resp.context['site_config'].id), 2)

    def test_company_only_search(self):
        """Regression test - requests with only a company term were being
        redirected to /jobs/"""
        co = 'Acme'
        resp = self.client.get(
                u'/jobs/?q=&company=%s&exact_title=&location=&exact_loc=' % co,
                follow=True)
        jobs = resp.context['default_jobs']
        self.assertEqual(resp.status_code, 200)
        for job in jobs:
            self.assertEqual(job.company, co)

    def test_search_results(self):
        resp = self.client.get(
          u'/search?location=&q=Oil+%26+Gas+Upstream+Project+Manager+-+Houston%2C+TX',
          follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_ajax_get_jobs_bad_params(self):
        resp = self.client.get(
                u'/ajax/joblisting/?num_items=q&offset=')
        self.assertEqual(resp.status_code, 200)

    def test_ajax_get_jobs(self):
        resp = self.client.get(u'/ajax/joblisting/')
        self.assertEqual(resp.status_code, 200)

    def test_search(self):

        def test_search_not(self):
            """Tests the '-' search operator for a title query"""
            #This query should return results for Retail Associate, 
            #but not Retail Manager
            resp = self.client.get(
                u'/jobs/?q=Retail+-Manager'
            )
            jobs=resp.context['default_jobs']
            self.assertEqual(jobs[0].title, 'Master Retail Associate')

        def test_title_boost(self):
            """Tests that a match in title has higher relevance
            than a match in description"""
            resp = self.client.get(
                    u'/jobs/?q=Master+Retail+Manager'
            )
            jobs=resp.context['default_jobs']
            self.assertEqual(jobs[0].title, 'Master Retail Manager')

        self.conn.delete(q="*:*")

        solr_docs_copy = deepcopy(self.solr_docs)
        kwargs1 = {
            'buid': 1,
            'id': "seo.joblisting.1",
            'title': "Master Retail Associate",
            'description': 'Master Retail Manager'
        }
        solr_docs_copy[0].update(kwargs1)

        kwargs2 = {
            'buid': 1,
            'id': "seo.joblisting.2",
            'title': "Master Retail Manager",
        }
        solr_docs_copy[1].update(kwargs2)

        self.conn.add(solr_docs_copy)

        test_search_not(self)
        test_title_boost(self)

    def test_job_detail(self):
        """
        Test that job detail pages return no server errors and that objects
        all work.

        """
        SeoSite.objects.get(id=1).delete()
        ats = factories.ATSSourceCodeFactory.build()
        ats.save()
        gac = factories.GACampaignFactory.build()
        gac.save()
        site = factories.SeoSiteFactory.build(
            google_analytics_campaigns=gac,
            view_sources=factories.ViewSourceFactory(id=1),
            id=1)
        site.save()
        site.ats_source_codes.add(ats),
        site.special_commitments.add(factories.SpecialCommitmentFactory(id=1))
        site.save()
        view_source = factories.ViewSourceFactory.build()
        view_source.save()
        special_commitment = factories.SpecialCommitmentFactory.build()
        special_commitment.save()

        # Job lookup by guid, missing state slug.
        resp = self.client.get(
            u'/indianapolis/retail-associate-розничная-ассоциированных/11111111111111111111111111111111/job/',
            HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 301)
        # Job lookup by uid & missing state slug.
        resp = self.client.get(
            u'/indianapolis/retail-associate-розничная-ассоциированных/1000/job/',
            HTTP_HOST='buckconsultants.jobs')
        # Job lookup by uid.
        self.assertEqual(resp.status_code, 301)
        resp = self.client.get(
            u'/indianapolis-in/retail-associate-розничная-ассоциированных/1000/job/',
            HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 301)
        # Successful job lookup by guid.
        resp = self.client.get(
            u'/indianapolis-in/retail-associate-розничная-ассоциированных/11111111111111111111111111111111/job/',
            HTTP_HOST='buckconsultants.jobs')
        self.assertEqual(resp.status_code, 200)

        # etree.parse breaks here; BeautifulSoup does not
        soup = BeautifulSoup(resp.content)

        # Tracking pixel should be near the end of the page; reverse list of
        # img tags to find the one we want quicker.
        images = soup.findAll('img')[::-1]
        pixel_found = False
        for image in images:
            if 'my.jobs/pixel.gif' in image.get('src'):
                pixel_found = True
                break
        self.assertTrue(pixel_found, 'My.jobs tracking pixel not found')

    def test_job_listing_count(self):
        """
        Test that the job listing header contains the correct job count.

        """
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            job = solr_settings.SOLR_FIXTURE[0].copy()
            job.update({
                'city': 'Muncie',
                'city_ac': 'Muncie',
                'city_exact': 'Muncie',
                'city_slab': 'muncie/indiana/usa/jobs::muncie, IN',
                'city_slab_exact': 'muncie/indiana/usa/jobs::Muncie, IN',
                'city_slug': 'muncie',
                'full_loc': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
                'full_loc_exact': 'city::Muncie@@state::Indiana@@location::Muncie, IN@@country::United States',
                'guid': '3'*32,
                'id': 'seo.joblisting.3',
                'location': 'Muncie, IN',
                'location_exact': 'Muncie, IN',
                'reqid': 'AAA000002',
                'uid': "1002",
                'link': 'http://my.jobs/' + '3'*32
            })
            self.conn.add([job])
            site = factories.SeoSiteFactory.build()
            site.save()

            for url, num_jobs in [('/indiana/usa/jobs/', 3),
                                  ('/indianapolis/indiana/usa/jobs/', 2)]:
                resp = self.client.get(url,
                                       HTTP_HOST='buckconsultants.jobs',
                                       follow=True)
                self.assertEqual(len(resp.context['default_jobs']), num_jobs)
                content = BeautifulSoup(resp.content)
                count = content.find('h3',
                                     **{'class': 'direct_highlightedText'})

                count_text = '%d Jobs in Indiana' % num_jobs
                if 'indianapolis' in url:
                    count_text += 'polis, IN'
                self.assertEqual(count.text.strip(), count_text)

    def test_url_for_sort_field(self):
        """
        Test that queries with unicode in search terms don't cause an error.
        The templatetag is being used directly to bypass the possibility of 404
        errors, thus minimizing external factors related to this particular
        regression.
        """
        request = RequestFactory().get(
            '/jobs/?q=Truck+Driver+%E2%80%93+CDL+Class+A%2FTouch+Freight'
            '+%E2%80%93+Penske+Logistics')

        context = {'request': request}
        try:
            url_for_sort_field(context, 'relevance')
        except UnicodeEncodeError as e:
            self.fail(e)

    def test_job_listing_by_slug_tag(self):
        """
        Test that job listing pages return no server errors and that objects
        all work.
        
        """
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            site = factories.SeoSiteFactory.build()
            site.save()
            resp = self.client.get(
                '/indianapolis/indiana/usa/jobs/',
                HTTP_HOST='buckconsultants.jobs',
                follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.context['default_jobs']), 2)

    def test_customfacet_with_querystring(self):
        """
        Test to ensure that CustomFacets that have only the 'querystring'
        attribute set are processed by helpers.get_solr_jobs properly and
        return the results we expect them to.

        This is a regression test designed to hedge against a former bug
        in our CustomFacet system in which raw querystrings were not
        handled in the same way as field lookups. That is, if a
        CustomFacet instance had its 'querystring' attribute set, it was
        handled by passing it to Haystack's 'raw_search' method, while
        field lookups were handled by turning them into SQ objects.

        """
        site = factories.SeoSiteFactory()
        cf1 = factories.CustomFacetFactory.build(querystring="uid:[17000000 TO 17999999]",
                                                 name="Engineering Jobs",
                                                 show_production=True)
        cf1.save()

        factories.SeoSiteFacetFactory(customfacet=cf1, seosite=site)
                        
        cf2 = factories.CustomFacetFactory.build(city="Pasadena", state="Texas",
                                                 country="United States",
                                                 name="Pasadena Jobs",
                                                 show_production=True)
        cf2.save()

        factories.SeoSiteFacetFactory(customfacet=cf2, seosite=site)

        config = factories.ConfigurationFactory.build(id=2)
        config.save()
        resp = self.client.get(
            '/pasadena/texas/usa/jobs/engineering-jobs/new-jobs/',
            follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_feed_items(self):
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()
        expected_fields = ['country_short', 'city', 'description', 'date_new',
                           'url', 'country', 'company', 'title', 'reqid',
                           'state', 'state_short', 'location', 'guid', 'uid']

        response = self.client.get('/feed/json')
        jobs = json.loads(response.content)
        job = jobs[0]
        self.assertItemsEqual(expected_fields, job.keys())
        for field in expected_fields:
            self.assertIsNotNone(job[field])
            self.assertNotEqual(job[field], 'None')

    def test_syndicate_feed_paging(self):
        feed_types = {'xml': 'xml', 'indeed': 'xml'}
        # Since the BusinessUnit id for our test XML feed is set to 0 on the
        # crawler's side, we need to make sure that everything else in the
        # tests is updated to reflect that, including data in our test database
        # and Solr index.
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()
        
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            next_link = '/feed/xml?num_items=1'
            num_pages = 0
            while next_link:
                num_pages += 1
                resp = self.client.get(next_link)
                tree = etree.parse(StringIO(resp.content))
                self.assertEqual(resp.status_code, 200)
                next_link = tree.find("link[@rel='next']")
                if next_link is not None:
                    next_link = next_link.get('href')
            self.assertEqual(num_pages, 2)

    def test_syndicate_feed_offset_larger_than_num_records(self):
        """Validate that when the offset is greater than the number of records,
        we return an empty document.
        """
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()
        job = self.solr_docs[0]
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            resp = self.client.get(
                    '/feed/rss?q=uid:1000&offset=1'
                )
            tree = etree.parse(StringIO(resp.content))
            self.assertEqual(resp.status_code, 200)
            # Check that ther ren't any jobs.
            self.assertNotIn('<guid>', resp.content)

    def test_syndicate_feed_query_results(self):
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()
        job = self.solr_docs[0]
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            resp = self.client.get(
                    '/feed/rss?q=uid:1000' 
                )
            tree = etree.parse(StringIO(resp.content))
            self.assertEqual(resp.status_code, 200)
            #Check that there's only one job
            self.assertEqual(resp.content.find('<guid>'),
                             resp.content.rfind('<guid>'))

    def test_syndicate_feed_query(self):
        # Since the BusinessUnit id for our test XML feed is set to 0 on the
        # crawler's side, we need to make sure that everything else in the
        # tests is updated to reflect that, including data in our test database
        # and Solr index.
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()
        job = self.solr_docs[0]
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            resp = self.client.get(
                '/feed/xml?num_items=1&location=Indianapolis&q=Retail'
                )
            tree = etree.parse(StringIO(resp.content))
            self.assertEqual(resp.status_code, 200)
            self_link = tree.find("link[@rel='self']").get('href')
            self.assertTrue('location=' in self_link and 'q=' in self_link)
            next_link = tree.find("link[@rel='next']").get('href')
            # Get the child tags of the first <job> tag from the XML output
            self.assertTrue('location=' in next_link and 'q=' in next_link) 

    def test_feed_title(self):
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()
        feed_types = ['rss', 'atom'] 
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            for feed_type in feed_types:
                resp = self.client.get('/jobs/feed/%s?q=Retail&location=Indianapolis' % 
                                       feed_type, HTTP_HOST="buckconsultants.jobs")
                self.assertEqual(resp.status_code, 200)
                self.assertNotEqual(resp.content.find(
                                    'Retail Jobs in Indianapolis'), -1)

    def test_rss_link_title(self):
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            resp = self.client.get('/jobs/?q=Retail&location=Indianapolis',
                                   HTTP_HOST="buckconsultants.jobs")
            self.assertEqual(resp.status_code, 200)

            rss_link = '<link rel="alternate" type="application/rss+xml" ' \
                       'title="Test - Retail Jobs in Indianapolis" ' \
                       'href="http://buckconsultants.jobs/jobs/feed/' \
                       'rss?q=Retail&amp;amp;location=Indianapolis">'
            self.assertIn(rss_link, resp.content)

    def test_feed_urls(self):
        
        feed_types = {
            'xml': 'xml', 
            'json': 'json', 
            'indeed': 'xml',
            'atom': 'atom+xml; charset=utf-8', 
            'rss': 'rss+xml; charset=utf-8',
            'jsonp': 'javascript'
        }
        # Since the BusinessUnit id for our test XML feed is set to 0 on the
        # crawler's side, we need to make sure that everything else in the
        # tests is updated to reflect that, including data in our test database
        # and Solr index.
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()

        # Set up a site package for the site and add posted job for
        # that site package.
        package = SitePackageFactory()
        package.sites.add(site)
        package.save()
        job = JobFactory()
        job_location = JobLocationFactory()
        job.locations.add(job_location)
        job.site_packages.add(package)
        job.save()

        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            known_url = 'http://testserver/11111111111111111111111111111111'
            postajob_url = 'http://testserver/%s/job/' % job_location.guid
            for feed_type in feed_types:
                resp = self.client.get('/feed/%s' % feed_type)

                # Confirm that the url for a posted job is correct in the
                # feed.
                self.assertIn(postajob_url, resp.content)
                # Confirm that the url for a normal job is correct
                # in the feed.
                self.assertIn(known_url, resp.content)

                # Sanity check. Make sure the extra field we've added
                # to help generate the urls isn't making it to the
                # final feed.
                self.assertNotIn('is_posted', resp.content)

    def test_syndicate_feed(self):

        feed_types = {
            'xml': 'xml',
            'json': 'json',
            'indeed': 'xml',
            'atom': 'atom+xml; charset=utf-8',
            'rss': 'rss+xml; charset=utf-8',
            'jsonp': 'javascript'
        }
        # Since the BusinessUnit id for our test XML feed is set to 0 on the
        # crawler's side, we need to make sure that everything else in the
        # tests is updated to reflect that, including data in our test database
        # and Solr index.
        site = SeoSite.objects.get(id=1)
        site.business_units = [self.buid_id]
        site.save()

        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            resp = self.client.get('/feed/xml')
            tree = etree.parse(StringIO(resp.content))
            walker = etree.iterwalk(tree, events=("start",), tag="job")
            # Get the child tags of the first <job> tag from the XML output
            children = walker.next()[1].iterchildren()
            tags = [child.tag for child in children]
            self.assertIn('reqid', tags)
            site = factories.SeoSiteFactory.build()
            site.save()
            for feed_type, ctype in feed_types.items():
                resp = self.client.get('/jobs/feed/%s' % feed_type,
                                       HTTP_HOST="buckconsultants.jobs")
                self.assertEqual(resp.status_code, 200)

                job = self.conn.search(q='uid:1000')
                vs = feed_type
                if vs == 'jsonp':
                    vs = 'json'
                test_str = "http://buckconsultants.jobs/%s%d" % \
                           (job.docs[0]['guid'],
                            settings.FEED_VIEW_SOURCES[vs])
                self.assertNotEqual(resp.content.decode('utf-8').find(test_str),
                                    -1)

                self.assertEqual(resp['Content-Type'], 'application/%s' % ctype)

    def test_new_businessunit(self):
        """
        Test for the following business logic:
        1. An SNS message is sent notifying DirectSEO that a feed file
           for business unit 'k' is ready
        2. Check if the directseo database has business unit 'k'. If not,
           create this business unit.

        """
        buid = 0
        with patch_settings(WILDCARD_REDIRECT=False):
            resp = self.client.post("/sns_confirmation",
                                    data="{\"Subject\": \"%s\"}" % buid,
                                    content_type="application/json")
            self.assertEqual(resp.status_code, 200)
            businessunit = BusinessUnit.objects.filter(id=buid)
            self.assertEqual(businessunit.count(), 1)

    def test_xml_parse_moc(self):
        import os

        filepath = download_feed_file(self.buid_id)
        moc = moc_factories.MocFactory.build()
        moc.save()
        onet = moc_factories.OnetFactory.build(code="11303102")
        onet.save()
        # Accounts for Many to Many relation between moc and onet
        moc.onets = moc_models.Onet.objects.all()
        moc.save()
        results = DEv2JobFeed(filepath)
        self.assertTrue(results.solr_jobs()[0]['moc'] != [])

    def test_update_solr(self):
        factories.BusinessUnitFactory.build(id=self.buid_id,
                                            title="General Motors").save()
        results = [{'uid': 1000}, {'uid': 1001}]
        self.assertEqual(self.conn.search("*:*", fl="uid").docs, results)

        # update_solr returns a 2-tuple like
        # (<# items to add/update>, <# items to delete>). We expect it here to
        # add all the jobs in the test feed file and remove all the jobs that
        # are pre-populated in the setUp() method.
        resp = update_solr(self.buid_id)
        self.assertEqual(resp, (self.feed_numjobs, 2))
        self.assertEqual(self.conn.search("*:*").hits, self.feed_numjobs)
        buid_search = self.conn.search("*:*", fq="buid:%s" % self.buid_id)
        self.assertEqual(buid_search.hits, self.feed_numjobs)
        flsearch = self.conn.search("*:*", fl="uid")
        docs = [{'uid': i} for i in self.feed_uids]
        self.assertItemsEqual(flsearch.docs, docs)

    def test_update_solr_with_posted_jobs(self):
        search = {'q': "buid:%s" % self.buid_id, 'fl': 'uid'}

        self.conn.delete(q="*:*")
        bu = factories.BusinessUnitFactory.build(id=self.buid_id,
                                                 title="General Motors")
        bu.save()

        posted_job = {
            'django_id': '1002',
            'id': 'seo.joblisting.%s' % '1002',
            'title': 'Trombonist',
            'title_ac': 'Trombonist',
            'title_exact': 'Trombonist',
            'title_slab': 'trombonist/jobs-in::Trombonist',
            'title_slab_exact': 'trombonist/jobs-in::Trombonist',
            'title_slug': 'Trombonist',
            'uid': '1002',
            'buid': self.buid_id,
            'is_posted': True,
        }
        self.conn.add([posted_job])
        self.assertEqual(self.conn.search(**search).docs, [{'uid': 1002}])
        # Posted jobs should not be deleted during solr updates
        update_solr(self.buid_id)
        self.assertIn({'uid': 1002}, self.conn.search(**search).docs)

    def test_update_solr_forced(self):
        """
        Test the update_solr function with the flag to update ALL jobs
        regardless of whether they're in the index already or not.

        """
        self.conn.delete(q="*:*")
        kwargs = {
            'django_id': self.feed_uids[0],
            'id': 'seo.joblisting.%s' % self.feed_uids[0],
            'title': 'Trombonist',
            'title_ac': 'Trombonist',
            'title_exact': 'Trombonist',
            'title_slab': 'trombonist/jobs-in::Trombonist',
            'title_slab_exact': 'trombonist/jobs-in::Trombonist',
            'title_slug': 'Trombonist',
            'uid': self.feed_uids[0]
        }
        self.solr_docs[1].update(kwargs)
        self.conn.add(self.solr_docs)
        self.assertEqual(self.conn.search("title:Trombonist").hits, 1)
        resp = update_solr(self.buid_id, force=True, delete_feed=False)
        # We want to ensure that we're updating two jobs -- both of the jobs
        # in the feed file -- and only deleting one: self.solr_docs[0].
        self.assertEqual(resp, (self.feed_numjobs, 1))
        # We should now have no hits for Trombonist, since the job listing
        # was updated in the index from the data in the feed file. Additionally,
        # there should also now be as many jobs in the Solr index as there are
        # in the feed file (which is equal to `self.feed_numjobs`).
        self.assertEqual(self.conn.search("title:Trombonist").hits, 0)
        self.assertEqual(self.conn.search("*:*").hits, self.feed_numjobs)

    def test_clear_solr(self):
        self.assertEqual(self.conn.search("*:*").hits, 2)
        clear_solr(self.buid_id)
        self.assertEqual(self.conn.search("*:*").hits, 0)

    def test_404_error(self):
        r'(%s)+' % '|'.join(['(?P<{n}>[/\w-]+{s})'.format(n=name, s=slug)
                             for name, slug in
                             default_settings.SLUG_TAGS.items()])
        response = self.client.get('/test/test/test/')
        self.assertEqual(response.status_code, 404)
        
    def test_stylesheet(self):
        response = self.client.get('/style/style.css')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/style/def.ui.dotjobs.css')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/style/def.ui.dotjobs.ie7.css')
        self.assertEqual(response.status_code, 200)   
        response = self.client.get('/style/def.ui.dotjobs.results.css')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/style/def.ui.microsite.mobile.css')
        self.assertEqual(response.status_code, 200)

    def test_moc_search_results(self):
        # MOC and Onet are not typically retrieved in the search results,
        # so we need to add them.
        base_search_fields = deepcopy(helpers.search_fields)
        helpers.search_fields += ['onet', 'moc']

        onetcode = "11904100"
        onettitle = "Engineering Managers"
        onet2code = "13209901"
        onet2title = "Financial Quantitative Analysts"
        moccode = "1343"
        mocmil = ("""AEGIS Weapon System MK-7 Technician (TK-II)/AEGIS Computer\
                   System (TK-II) Supervisor""")
        mocciv = "Supervisor, Mechanics, Installers, or Repairers"
        # Grab a job that has an Onet code matching the one we'll be using to
        # create our mock MocMap instance to test out
        # seo.helpers.prepare_sqs_from_search_params.
        result = self.conn.search(q="*:*", rows="1").docs
        result[0]['buid'] = 1
        result[0]['onet'] = onet2code
        result[0]['mapped_moc'] = [moccode]
        result[0]['mapped_mocid'] = 4105
        self.conn.add(result)
        onet = moc_factories.OnetFactory.build(title=onettitle,
                                               code=onetcode)
        onet.save()
        mocdetail = moc_factories.MocDetailFactory(id=4105, service_branch="n",
                                                   primary_value=moccode,
                                                   military_description=mocmil,
                                                   civilian_description=mocciv)
        mocdetail.save()
        moc = moc_factories.MocFactory.build(code=moccode, branch="navy",
                                             title=mocmil,
                                             moc_detail=mocdetail)
        moc.save()
        onet2 = moc_factories.OnetFactory.build(title=onet2title,
                                                code=onet2code)
        onet2.save()
        customcareer = moc_factories.CustomCareerFactory.build(moc=moc,
                                                               object_id=self.buid_id,
                                                               onet_id=onet2.code)
        customcareer.save()
        bu = BusinessUnit.objects.get(id=1)
        bu.customcareers = [customcareer]
        bu.save()
        resp = self.client.get('/jobs/?moc=%s' % moccode)
        self.assertTrue(len(resp.context['default_jobs']) == 1)
        self.assertIn(onet2code, str(resp.context['default_jobs'][0].onet))
        self.assertEqual(resp.status_code, 200)

        # Reset the search_fields since Onet and MOC are no longer needed.
        helpers.search_fields = base_search_fields

    def test_moc_ac(self):
        """Test the autocomplete for the MOC search box."""
        branches = {
            "a": "army",
            "c": "coast-guard",
            "f": "air-force",
            "n": "navy",
            "m": "marines"
        }
        mocd = moc_factories.MocDetailFactory.build()
        mocd.save()
        moc = moc_factories.MocFactory.build(code='01', moc_detail=mocd)
        moc.save()
        onet = moc_factories.OnetFactory.build()
        onet.save()
        
        moc.onets = moc_models.Onet.objects.all()
        val = mocd.primary_value
        label = "%s - %s (%s - %s)" % (val, mocd.civilian_description,
                                      branches[mocd.service_branch].capitalize(),
                                      mocd.military_description)
        mocid = moc.id
        
        # test for code
        resp = self.client.get("/ajax/mac/?lookup=moc&term=01&callback=jq_code")
        self.assertEqual(resp.content, ('jq_code([{"moc_id": %s, "value": "%s",'
                                        ' "label": "%s"}])' % (mocid, val,
                                                              label)))
        # test for keyword        
        resp = self.client.get("/ajax/mac/?lookup=moc&term=busi&callback=jq_term")
        self.assertEqual(resp.content, ('jq_term([{"moc_id": %s, "value": "%s",'
                                        ' "label": "%s"}])' % (mocid, val,
                                                              label)))
        
        # remove buid associations and try again
        buids = BusinessUnit.objects.all()
        for buid in buids:
            buid.delete()
        # test for code
        resp = self.client.get("/ajax/mac/?lookup=moc&term=01&callback=jq_code")
        self.assertEqual(resp.content, ('jq_code([{"moc_id": %s, "value": "%s",'
                                        ' "label": "%s"}])' % (mocid, val,
                                                              label)))
        # test for keyword        
        resp = self.client.get("/ajax/mac/?lookup=moc&term=busi&callback=jq_term")
        self.assertEqual(resp.content, ('jq_term([{"moc_id": %s, "value": "%s",'
                                        ' "label": "%s"}])' % (mocid, val,
                                                              label)))
        
    def test_configuration_admin(self):
        """
        Test the custom configuration admin template to make sure there are no
        errors in the template tags or block translations.
        
        """        
        config = factories.ConfigurationFactory.build()
        config.save()
        self.assertTrue(self.client.login(email='matt@directemployers.org',
                                          password='lingo23'))
        resp = self.client.get('/admin/seo/configuration/1/')
        self.assertEqual(resp.status_code,200)

    def test_ajax_get_facets(self):
        """
        Test the default site.jobs/facet_field that makes a call to
        ajax_get_facets
        """
        facet_fields=['facets', 'titles', 'cities', 'states', 'mocs',
                      'countries', 'facets', 'company-facets']
        site = SeoSite.objects.get(id=1)
        for field in facet_fields:
            resp = self.client.get("/ajax/{f}/".format(f=field))
            self.assertEqual(resp.status_code, 200)

    def test_ajax_sites_manual_input(self):
        """
        Test manually inputing a fake tag directly into the URL for ajax_sites.html
        """
        resp = self.client.post("/ajax/data/sites?tag=Fake%20Tag")
        self.assertEqual(resp.status_code, 200)

    def test_company_302(self):
        """
        Regression test to ensure that a URL specifying a non-existent
        company name returns a 302 appropriately.

        The bug that spawned this test was one in which it was found that
        visiting a URL like `http://www.my.jobs/alksjdklajsd/careers/`
        returned all results for www.my.jobs. This would work on any site
        that has company facets enabled.

        """
        # In order to actually capture this bug properly, we must set our
        # SeoSite to not have any related BusinessUnit instances, so that in
        # the case there are no matches, it will still serve all the results
        # in the database.
        site = SeoSite.objects.get(id=1)
        site.business_units = []
        site.save()
        resp = self.client.get("/aslkdjas/careers/")
        self.assertEqual(resp.status_code, 302)
        
    def test_moc_duplicate_search(self):       
        """Search by non-unique moc should return all matching jobs."""
        self.conn.delete(q="*:*")
        solr_docs_copy=deepcopy(self.solr_docs)

        kwargs1 = {
            'buid': 1,
            'id': "seo.joblisting.1",
            'title': "First job with MOC 01",
            'moc': '01',
            'mapped_moc': '01'
        }
        solr_docs_copy[0].update(kwargs1)

        kwargs2 = {
            'buid': 1,
            'id': "seo.joblisting.2",
            'title': "Unrelated Job with MOC 01",
            'moc': '01',
            'mapped_moc': '01'
        }
        solr_docs_copy[1].update(kwargs2)
        self.conn.add(solr_docs_copy)

        resp = self.client.get("/jobs/?moc=01")
        jobs=resp.context['default_jobs']
        self.assertEqual(len(jobs), 2)
        self.assertNotEqual(jobs[0].id, jobs[1].id)

    def test_moc_id_search(self):       
        """Search by unique moc_id should return jobs unique to the moc record."""
        #create two job listings with the same moc
        self.conn.delete(q="*:*")
        solr_docs_copy = deepcopy(self.solr_docs)
        kwargs1 = {
            'buid': 1,
            'id': "seo.joblisting.1",
            'title': "First job with MOC 01",
            'mapped_moc': '01',
            'mapped_mocid': 3
        }
        solr_docs_copy[0].update(kwargs1)

        kwargs2 = {
            'buid': 1,
            'id': "seo.joblisting.2",
            'title': "Unrelated Job with MOC 01",
            'mapped_moc': '01',
            'mapped_mocid': 4
        }
        solr_docs_copy[1].update(kwargs2)
        self.conn.add(solr_docs_copy)
        #Check that a search by duplicated moc and unique moc_id 
        #returns 1 correct job listing only
        resp = self.client.get("/jobs/?moc=%s&moc_id=%s" % (kwargs1['mapped_moc'],
                                                            kwargs2['mapped_mocid']),
                               follow=True)
        self.assertEqual(resp.status_code, 200)
        jobs = resp.context['default_jobs']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, kwargs2['id'])
    
    def test_company_list(self):
        """
        Test the view all companies listing to make sure it returns results.
        
        """
        self.conn.delete(q="*:*")

        solr_docs_copy = deepcopy(self.solr_docs)
        kwargs1 = {
            'buid': 1,
            'id': "seo.joblisting.1",
            'title': "Master Retail Associate",
            'description': 'Master Retail Manager'
        }
        solr_docs_copy[0].update(kwargs1)

        self.conn.add(solr_docs_copy)
        
        alpha_buid = factories.BusinessUnitFactory.build(title="1A Company",id=1)
        alpha_buid.save()
        site = factories.SeoSiteFactory.build(id=1,
                                    domain=u'www.my.jobs',name='www.my.jobs')
        site.save()
        company = factories.CompanyFactory.build(name="1A Company")
        company.save()
        company.job_source_ids.add(alpha_buid.id)
        company.save()
        
        company = factories.CompanyFactory.build(name="A Company")
        company.save()
        company.job_source_ids.add(alpha_buid.id)
        company.save()
        
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):   
            #test for companies beginning with a number
            resp = self.client.get("/all-companies/0-9/")
            self.assertContains(resp,'<li class="company">',count=None, 
                                status_code=200, msg_prefix='')
            #test for companies beginning with a letter
            resp = self.client.get("/all-companies/a/")
            self.assertContains(resp,'<li class="company">',count=None, 
                                status_code=200, msg_prefix='')
            
    def test_empty_company_listing(self):
        company = Company.objects.none()
        response = self.client.get('/all-companies/')
        self.assertEqual(response.status_code, 200)
        
    def test_static_page_analytics(self):           
        site = factories.SeoSiteFactory.build(id=1, domain=u'www.my.jobs',
                                              name='www.my.jobs')
        site.save()
        site_tag = SiteTag(site_tag='network')
        site_tag.save()
        site.site_tags.add(site_tag)
        fp = FlatPage(url="/test-page/", content="About my company")
        fp.save()
        fp.sites.add(site)
        fp.save()
        
        ga = factories.GoogleAnalyticsFactory.build()
        ga.save()
        site.google_analytics.add(ga)
        
        resp = self.client.get('/test-page/')

        self.assertIn(ga.web_property_id, resp.content)      
        self.assertEqual(resp.content.count(ga.web_property_id), 1)      
        #GA pageview sent in footer
        self.assertContains(resp, "'g"+str(ga.id)+".send', 'pageview'")
        #Check that site is getting default header and footer
        self.assertContains(resp, "direct_dotjobsFooterContent")
        self.assertContains(resp, "direct_dotjobsWideHeader")
        #Check that CSS for network sites is loaded properly
        self.assertContains(resp, '/style/def.ui.dotjobs.css')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(settings.SITE_ID, 1)
        self.assertEqual(settings.SITE_TITLE, "Test Site")

    def footer_no_network_tag_test(self):
        """ 
        Sites that do not have the network tag should not get a header and footer
        """         
        site = factories.SeoSiteFactory.build(id=1,
                                    domain=u'www.my.jobs',name='www.my.jobs')
        site.save()
        fp = FlatPage(url="/test-page/", content="About my company")
        fp.save()
        fp.sites.add(site)
        fp.save()
        resp = self.client.get('/test-page/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(settings.SITE_ID, 1)
        #Header text
        self.assertNotIn("direct_dotjobsWideHeader", resp)
        #Footer text
        self.assertNotIn("direct_dotjobsFooterContent", resp)

    def test_google_universal_analytics(self):
        """Test that google universal analytics are loading"""
        site = factories.SeoSiteFactory.build()
        site.save()
        ga = factories.GoogleAnalyticsFactory.build()
        ga.save()
        site.google_analytics.add(ga)
 
        resp = self.client.get(
                '/',
                HTTP_HOST='buckconsultants.jobs',
                follow=True)
        self.assertIn(ga.web_property_id, resp.content)
        # Check that universal analytics script is present
        self.assertIn('function(i,s,o,g,r,a,m)', resp.content)
        # Check that classic analytics script isn't present
        self.assertNotIn('google-analytics.com/ga.js', resp.content)
        self.assertEqual(resp.content.count(ga.web_property_id), 1)      
        
    def test_saved_search_render(self):
        """Test that network sites get the saved search form on job listings."""
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            site = factories.SeoSiteFactory.build()
            site.save()
            site_tag = SiteTag(site_tag='network')
            site_tag.save()
            site.site_tags.add(site_tag)
            resp = self.client.get(
                    '/indianapolis/indiana/usa/jobs/',
                    HTTP_HOST='buckconsultants.jobs',
                    follow=True)
            self.assertContains(resp,'<div id="de-myjobs-widget"',count=None, 
                                    status_code=200, msg_prefix='')
            
    def test_saved_search_non_render(self):
        """Test company sites don't have a saved search form on job listings."""
        with connection(connections_info=solr_settings.HAYSTACK_CONNECTIONS):
            site = factories.SeoSiteFactory.build()
            site.save()
            site_tag = SiteTag(site_tag='company')
            site_tag.save()
            site.site_tags.add(site_tag) 
            resp = self.client.get(
                    '/indianapolis/indiana/usa/jobs/',
                    HTTP_HOST='buckconsultants.jobs',
                    follow=True)
            self.assertNotContains(resp,'<div id="direct_savedsearch"', 
                                   status_code=200, msg_prefix='')


class FlatpagesTestCase(DirectSEOBase):
    def setUp(self):
        super(FlatpagesTestCase, self).setUp()
        self.test_site = factories.SeoSiteFactory.build()
        self.test_site.save()
        self.fp = CustomPage()
        self.fp.url = '/careers/'
        self.fp.content = 'Hello fancy feasts.'
        self.fp.save()
        self.fp.sites.add(self.test_site)

    def test_flatpage(self):
        response = self.client.get('/careers/',
                                   HTTP_HOST=u'buckconsultants.jobs')
        secret_code = response.content.find('Hello fancy feasts.')
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(secret_code, -1)


class ProtectedSiteTestCase(DirectSEOBase):
    fixtures = ['seo_views_testdata.json']

    def setUp(self):
        super(ProtectedSiteTestCase, self).setUp()
        settings.PROTECTED_SITES = {1: [1, ]}
        self.user_email = 'test@test.com'
        self.user_password = 'password'
        self.user, created = User.objects.create_user(email=self.user_email,
                                                      password=self.user_password)
        self.user.save()

    def test_not_logged_in(self):
        """
        Checks for correct redirect for protected sites when users aren't
        logged in.

        """
        response = self.client.get('http://testserver.jobs/jobs/?q=none')
        # Due to some funky treatment of follow we can't
        # actually confirm that this ever reaches the myjobs login page.
        self.assertEqual(response['Location'],
                         'https://secure.my.jobs/cas/?redirect_url=http://testserver/jobs/?q=none')
        self.assertEqual(response.status_code, 302)

    def test_logged_in_in_group(self):
        """
        Confirm that logged in users that are in the appropriate group
        can reach protected pages.

        """
        self.user.groups.add(1)
        self.user.save()
        self.client.login(username=self.user, password=self.user_password)
        response = self.client.get('http://testserver.jobs/jobs/?q=none')
        self.assertEqual(response.status_code, 200)

    def test_logged_in_not_in_group(self):
        """
        Confirm that logged in users that are not in the appropriate group
        cannot reach protected pages.

        """
        self.user.groups.remove(1)
        self.user.save()
        self.client.login(username=self.user_email, password=self.user_password)
        response = self.client.get('http://testserver.jobs/jobs/?q=none')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://www.my.jobs/')

    def test_unprotected_site(self):
        """
        Test that unprotected sites are not being treated as protected.

        """
        settings.PROTECTED_SITES = {}
        response = self.client.get('http://testserver.jobs/jobs/?q=none')
        self.assertEqual(response.status_code, 200)

    def test_protected_site_bypass(self):
        url = ('http://testserver.jobs/jobs/?q=none&key=%s' %
               settings.SEARCH_API_KEY)
        response = self.client.get(url)

        # Confirm that the key does in fact bypass the protected site.
        self.assertFalse(hasattr(response, 'redirect_chain'))
        self.assertEqual(response.request['PATH_INFO'], '/jobs/')


class StaticPageOverrideTests(DirectSEOTestCase):
    def setUp(self):
        super(StaticPageOverrideTests, self).setUp()
        self.site = SeoSite.objects.get()

    def test_non_network_redirects(self):
        """
        Non-network sites either 404 on certain pages or redirect elsewhere
        if an entry exists in the Django redirects app for a given path/domain.
        """
        response = self.client.get('/about/', HTTP_HOST=self.site.domain)
        self.assertEqual(response.status_code, 404)

        redirect = Redirect.objects.create(site=self.site, old_path='/about/',
                                           new_path='http://example.com')

        response = self.client.get('/about/', HTTP_HOST=self.site.domain)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], redirect.new_path)

    def test_network_redirects(self):
        """
        Network sites redirect to secure.my.jobs for certain paths.
        """
        self.site.site_tags.add(SiteTag.objects.create(site_tag='network'))
        response = self.client.get('/about/', HTTP_HOST=self.site.domain)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://secure.my.jobs/about')
