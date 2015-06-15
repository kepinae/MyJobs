#  -*- coding: utf-8 -*-
import os
import json

from django.conf import settings
from lxml import etree

from seo_pysolr import Solr
import import_jobs
from seo.tests import factories
from seo.models import SeoSite
from seo.search_backend import DESearchQuerySet
from setup import DirectSEOBase


class SiteTestCase(DirectSEOBase):
    """
    We're adding these tests to ensure unicode jobs descriptions and titles
    make it through the import process and work with high-level features.
    We should use http requests wherever possible since it's difficult to
    predict which modules will have issues with unicode.

    """

    def setUp(self):
        super(SiteTestCase, self).setUp()
        self.conn = Solr('http://127.0.0.1:8983/solr/seo')
        self.conn.delete(q="*:*")        
        self.businessunit = factories.BusinessUnitFactory(id=0)
        self.buid = self.businessunit.id
        self.filepath = os.path.join(import_jobs.DATA_DIR,
                                     'dseo_feed_%s.xml' % self.buid)
        SeoSite.objects.all().delete()
        self.site = factories.SeoSiteFactory(id=1)

        self.configuration = factories.ConfigurationFactory(status=2)
        self.configuration.save()
        self.site.configurations.clear()
        self.site.configurations.add(self.configuration)

    def tearDown(self):
        super(SiteTestCase, self).tearDown()
        self.conn.delete(q="*:*")
    
    def test_unicode_title(self):
        # Test imports
        group = factories.GroupFactory()
        self.site.group = group
        self.site.business_units.add(self.businessunit)
        self.site.save()
        import_jobs.update_solr(self.buid, download=False, delete_feed=False,
                                data_dir='seo/tests/data/')
        solr_jobs = self.conn.search("*:*")
        resp = self.client.get('/')
        self.assertEqual(resp.context['total_jobs_count'], solr_jobs.hits)

        # test standard facets against Haystack query
        standard_cf = factories.CustomFacetFactory.build(
            # default facet will return both jobs
            name="Keyword Facet",
            group=group,
            show_production=True)
        standard_cf.save()
        standard_cf.keyword.add(u'Ключевые')
        standard_cf.save()
        standard_site_facet = factories.SeoSiteFacetFactory(
            seosite=self.site,
            customfacet=standard_cf,
            facet_type=factories.SeoSiteFacet.STANDARD)
        standard_site_facet.save()

        # test standard facets against Haystack query
        standard_cf2 = factories.CustomFacetFactory.build(
            # default facet will return both jobs
            name='Country Facet',
            country='United States',
            group=group,
            show_production=True)
        standard_cf2.save()
        standard_site_facet2 = factories.SeoSiteFacetFactory(
            seosite=self.site,
            customfacet=standard_cf2,
            facet_type=factories.SeoSiteFacet.STANDARD)
        standard_site_facet2.save()

        resp = self.client.get('/keyword-facet/new-jobs/',
                               HTTP_HOST=self.site.domain, follow=True)
        sqs = DESearchQuerySet().filter(text=u'Ключевые')
        self.assertEqual(len(resp.context['default_jobs']), sqs.count())
        for facet_widget in resp.context['widgets']:
            # Ensure that no standard facet has more results than current
            # search results
            for count_tuple in facet_widget.items:
                self.assertTrue(sqs.count() >= count_tuple[1])
        
        # Test default site facets against PySolr query
        from django.core.cache import cache
        cache.clear()
        default_cf = factories.CustomFacetFactory.build(
            name="Default Facet",
            title=u"Специалист",
            group=group,
            show_production=True)
        default_cf.save()
        default_site_facet = factories.SeoSiteFacetFactory(
            seosite=self.site,
            facet_type=factories.SeoSiteFacet.DEFAULT,
            customfacet=default_cf)
        default_site_facet.save()
        resp = self.client.get('/jobs/', HTTP_HOST=self.site.domain,
                               follow=True)
        total_jobs = resp.context['total_jobs_count']
        solr_jobs = self.conn.search(q=u'title:"Специалист"')
        self.assertEqual(total_jobs, solr_jobs.hits)
        self.assertEqual(len(resp.context['default_jobs']), total_jobs)
        for facet_widget in resp.context['widgets']:
            for count_tuple in facet_widget.items:
                self.assertTrue(sqs.count() >= count_tuple[1])

        # Feed test
        resp = self.client.get('/feed/json', HTTP_HOST=self.site.domain)
        jobs = json.loads(resp.content)
        self.assertEqual(len(jobs), total_jobs)
        for job in jobs:
            resp = self.client.get(job['url'], HTTP_HOST=self.site.domain,
                                   follow=False)
            self.assertEqual(resp.status_code, 302)
            expected = 'http://my.jobs/%s%d?my.jobs.site.id=%s' %\
                       (job['guid'],
                        settings.FEED_VIEW_SOURCES['json'],
                        str(self.site.pk))
            self.assertEqual(resp['Location'], expected)

        # Sitemap index Test - Since sitemap only builds out updates from the
        # last 30 days, this test will eventually be checking 0 jobs in sitemap
        # TODO, find a way to keep feed dates current. We might be able to use
        # the mock library to override datetime functions
        resp = self.client.get('/sitemap.xml', HTTP_HOST=self.site.domain)  
        root = etree.fromstring(resp.content)
        self.assertGreater(len(root), 0)
        crawled_jobs = 0
        for loc, lastmod in root:
            self.assertTrue(loc.text)
            resp = self.client.get(loc.text, HTTP_HOST=self.site.domain)  
            self.assertEqual(resp.status_code, 200)
            # Get the first daily sitemap
            urlset = etree.fromstring(resp.content)
            # Check each job in daily sitemap - I'm a bot
            for loc, _, _, _ in urlset:
                resp = self.client.get(loc.text, HTTP_HOST=self.site.domain)
                self.assertEqual(resp.status_code, 200)
                self.assertIn(str(resp.context['the_job'].uid), loc.text)
                crawled_jobs += 1
        # This assertion worked when the test was made, but will change with
        # date
        # self.assertEqual(crawled_jobs, 2)
        # This assertion should work after date issues have been resolved
        # self.assertEqual(crawled_jobs, total_jobs)
