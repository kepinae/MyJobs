from collections import namedtuple

from django.conf import settings
from django.http import QueryDict

from moc_coding.tests.factories import MocFactory
from seo.breadbox import Breadbox
from seo.models import CustomFacet
from seo.tests.factories import (BusinessUnitFactory, CustomFacetFactory,
                                 SeoSiteFacetFactory, SeoSiteFactory)
from seo.tests.setup import DirectSEOBase


class BreadboxTests(DirectSEOBase):
    def setUp(self):
        super(BreadboxTests, self).setUp()

        self.site = SeoSiteFactory()
        settings.SITE = self.site
        settings.SITE_ID = self.site.pk
        settings.STANDARD_FACET = []
        for x in range(1, 4):
            facet = CustomFacetFactory(name_slug='custom-facet-%s' % x,
                                       name="Custom Facet %s" % x,
                                       always_show=True,
                                       show_production=1)
            SeoSiteFacetFactory(customfacet=facet, seosite=self.site)
            settings.STANDARD_FACET.append(facet)

        kwargs = {'seositefacet__seosite': self.site}
        self.custom_facets = CustomFacet.objects.filter(**kwargs)

        self.filters = {
            'title_slug': None,
            'location_slug': None,
            'moc_slug': None,
            'facet_slug': None,
            'company_slug': None,
        }

    def test_facet_breadcrumbs(self):
        name_slugs = self.custom_facets.values_list('name_slug', flat=True)
        name_slugs = '/'.join(name_slugs)
        path = "/%s/%s/" % (name_slugs, settings.SLUG_TAGS['facet_slug'])

        self.filters['facet_slug'] = name_slugs

        jobs = []

        query_dict = QueryDict('')

        breadbox = Breadbox(path, self.filters, jobs, query_dict)

        self.assertEqual(len(breadbox.custom_facet_breadcrumbs), 3)
        names = self.custom_facets.values_list('name', flat=True)
        for breadcrumb in breadbox.custom_facet_breadcrumbs:
            self.assertIn(breadcrumb.display_title, names)

    def test_title_breadcrumbs(self):
        path = '/test-title/%s/' % settings.SLUG_TAGS['title_slug']

        self.filters['title_slug'] = 'test-title'

        jobs = []

        query_dict = QueryDict('')

        breadbox = Breadbox(path, self.filters, jobs, query_dict)

        self.assertEqual(breadbox.title_breadcrumb.display_title, 'Test Title')

    def test_location_breadcrumbs(self):
        Job = namedtuple('Job', ['location', 'state', 'country', 'title_slug'])
        jobs = [Job(location='Indianapolis, IN', state='Indiana',
                    country='USA', title_slug='')]

        # Location from param
        path = '/jobs/'

        query_dict = QueryDict('location=Indianapolis, IN')

        breadbox = Breadbox(path, self.filters, jobs, query_dict)

        self.assertEqual(len(breadbox.location_breadcrumbs), 1)
        self.assertEqual(breadbox.location_breadcrumbs[0].display_title,
                         'Indianapolis, IN')

        # Location from path
        path = '/indianapolis/in/usa/%s/' % settings.SLUG_TAGS['location_slug']

        self.filters['location_slug'] = 'indianapolis/in/usa'

        query_dict = QueryDict('')

        breadbox = Breadbox(path, self.filters, jobs, query_dict)

        self.assertEqual(len(breadbox.location_breadcrumbs), 1)
        self.assertEqual(breadbox.location_breadcrumbs[0].display_title,
                         'Indianapolis, IN')

    def test_breadcrumbs_from_slugs(self):
        """Tests that breadcrumb URLs aren't mangled on creation from slugs."""
        path = u'deu/jobs/deutsche-bank/careers/'

        self.filters['company_slug'] = 'deutsche-bank'
        self.filters['location_slug'] = 'deu'
        query_dict = QueryDict('')

        breadbox = Breadbox(path, self.filters, [], query_dict)
        breadbox.build_location_breadcrumbs_from_slugs()

        # Before, the resulting URL would become '[tsche-bank/careers/', which
        # is incorrect, as deu as a slug should be removed, rather than the
        # company name being mangled
        self.assertEqual(breadbox.location_breadcrumbs[0].url,
                         'deutsche-bank/careers/')

        # location slug not being part of the path shouldn't raise an error
        path = '/jobs/deutsche-bank/careers/'
        breadbox = Breadbox(path, self.filters, [], query_dict)
        breadbox.build_location_breadcrumbs_from_slugs()

    def test_moc_slug(self):
        moc = MocFactory()

        self.filters['moc_slug'] = 'something/%s/%s' % (moc.code, moc.branch)

        path = '/%s/%s/' % (self.filters['moc_slug'],
                            settings.SLUG_TAGS['moc_slug'])

        jobs = []

        query_dict = QueryDict('')

        breadbox = Breadbox(path, self.filters, jobs, query_dict)
        self.assertEqual(len(breadbox.moc_breadcrumbs), 1)
        self.assertEqual(breadbox.moc_breadcrumbs[0].display_title,
                         "%s - %s" % (moc.code, moc.title))

    def test_company_slug(self):
        bu = BusinessUnitFactory(title_slug='test-bu', id=7,
                                 title='Test')
        path = '/%s/%s/' % (bu.title_slug, settings.SLUG_TAGS['company_slug'])

        self.filters['company_slug'] = bu.title_slug

        jobs = []

        query_dict = QueryDict('')

        breadbox = Breadbox(path, self.filters, jobs, query_dict)
        self.assertEqual(breadbox.company_breadcrumb.display_title, bu.title)
