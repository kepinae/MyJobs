# -*- coding: utf-8 -*-
import datetime
import os.path
import shutil

from seo_pysolr import Solr
from xmlparse import DEv2JobFeed, guid_from_link
from import_jobs import DATA_DIR, download_feed_file, update_solr
from postajob.tests.factories import SitePackageFactory
from seo.tests.factories import BusinessUnitFactory, CompanyFactory
from setup import DirectSEOBase


class JobFeedHelpersTest(DirectSEOBase):
    def test_guid_from_link(self):
        links_to_guids = [
            ('http://my.jobs/0F21D879F4904BDB90EC27A3843A1B0910/',
             '0F21D879F4904BDB90EC27A3843A1B09'),
            ('http://jcnlx.org/8FA6F9676C914E0B96A5C5A3C19317B010/',
             '8FA6F9676C914E0B96A5C5A3C19317B0'),
            ('http://this.should.still.work.net/012345678901234567890123456789012346/',
             '01234567890123456789012345678901'),
            ('http://this.has.no.path/', ''),
            ('http://this.path.is.too.short/1', '1'),
            ('', ''),
        ]
        for url, expected_guid in links_to_guids:
            guid = guid_from_link(url)
            self.assertEqual(guid, expected_guid)

class JobFeedTestCase(DirectSEOBase):

    def setUp(self):
        super(JobFeedTestCase, self).setUp()
        self.businessunit = BusinessUnitFactory(id=0)
        self.buid_id = self.businessunit.id
        self.numjobs = 14
        self.testdir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                                    'data')
        self.company = CompanyFactory()
        self.company.job_source_ids.add(self.businessunit)
        self.company.save()
        self.conn = Solr("http://127.0.0.1:8983/solr/seo")
        self.emptyfeed = os.path.join(self.testdir, "dseo_feed_0.no_jobs.xml")
        self.malformed_feed = os.path.join(self.testdir, 'dseo_malformed_feed_0.xml')
        self.invalid_feed = os.path.join(self.testdir, 'dseo_invalid_feed_0.xml')
        self.unused_field_feed = os.path.join(self.testdir, 'dseo_feed_1.xml')
        self.no_onet_feed = os.path.join(self.testdir, 'dseo_feed_no_onets.xml')

        #Ensures DATA_DIR used by import_jobs.download_feed_file exists
        data_path = DATA_DIR
        if not os.path.exists(data_path):
            os.mkdir(data_path)

    def test_company_canonical_microsite(self):
        # Test that canonical microsites is correctly added to solr
        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])

        jobs = results.solr_jobs()
        self.assertEqual(jobs[0]['company_canonical_microsite_exact'], None)

        self.company.canonical_microsite = "http://test.jobs"
        self.company.save()

        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])

        jobs = results.solr_jobs()
        self.assertEqual(jobs[0]['company_canonical_microsite_exact'],
                         'http://test.jobs')

    def test_company_enhanced(self):
        # Test that company enhanced check is correctly added to solr
        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])

        jobs = results.solr_jobs()
        self.assertFalse(jobs[0]['company_enhanced'])

        self.company.enhanced = True
        self.company.save()

        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])

        jobs = results.solr_jobs()
        self.assertTrue(jobs[0]['company_enhanced'])

    def test_company_member(self):
        # Test that company member check is correctly added to solr
        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])
        jobs = results.solr_jobs()
        self.assertTrue(jobs[0]['company_member'])

        self.company.member = False
        self.company.save()

        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])

        jobs = results.solr_jobs()
        self.assertFalse(jobs[0]['company_member'])

    def test_company_digital_strategies_customer(self):
        # Test that digial strategies customer check is correctly added to solr
        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])

        jobs = results.solr_jobs()
        self.assertFalse(jobs[0]['company_digital_strategies_customer'])

        self.company.digital_strategies_customer = True
        self.company.save()

        results = DEv2JobFeed(
            'seo/tests/data/dseo_feed_0.xml',
            jsid=self.businessunit.id,
            company=self.businessunit.company_set.all()[0])

        jobs = results.solr_jobs()
        self.assertTrue(jobs[0]['company_digital_strategies_customer'])

    def test_no_markdown_newline_breaks(self):
        # Test that non-markdown businessunits have newlines converted to breaks
        no_markdown_bu = BusinessUnitFactory.build(id=5, enable_markdown=False)
        results = DEv2JobFeed(
                    'seo/tests/data/dseo_feed_0.xml', 
                    jsid=no_markdown_bu.id,
                    markdown=no_markdown_bu.enable_markdown) 
        jobs = results.solr_jobs()
        self.assertNotEqual(jobs[0]['html_description'].find('Operations<br />'), -1)
        
    def test_markdown_no_newline_breaks(self):
        # Test that markdown businessunits do not have newlines converted to breaks
        results = DEv2JobFeed(
                    'seo/tests/data/dseo_feed_0.xml', 
                    jsid=self.businessunit.id,
                    markdown = self.businessunit.enable_markdown) 
        jobs = results.solr_jobs()
        self.assertEqual(jobs[0]['html_description'].find('Operations<br />'), -1)

    def test_unused_fields(self):
        # Test that new fields don't break existing code
        results = DEv2JobFeed(self.unused_field_feed,
                              jsid=self.businessunit.id)
        jobs = results.solr_jobs()
        self.assertEqual(len(results.jobparse()), 1)

    def test_unescape(self):
        """Tests that escaped html characters are unescaped when imported"""
        results = DEv2JobFeed(
                    'seo/tests/data/dseo_feed_0.escaped_chars.xml', 
                    jsid=0) 
        jobs = results.solr_jobs()
        self.assertEqual(results.job_source_name.find('&#162;'), -1)
        self.assertEqual(jobs[0]['description'].find('&amp;'), -1)

    def test_markdown_code_blocks(self):
        #test that code blocks are not in html job descriptions
        results = DEv2JobFeed(
                    'seo/tests/data/dseo_feed_0.markdown.xml', 
                    jsid=0) 
        jobs = results.solr_jobs()
        for job in jobs:
            self.assertEqual(job['html_description'].find('<code>'), -1)
            self.assertEqual(job['html_description'].find('</code>'), -1)
            self.assertEqual(job['html_description'].find('<pre>'), -1)
            self.assertEqual(job['html_description'].find('<h1>'), -1)
            self.assertEqual(job['html_description'].find('##'), -1)
            self.assertNotEqual(job['html_description'].find('<h4>'), -1)
            self.assertNotEqual(job['html_description'].find('<h6>'), -1)
            self.assertNotEqual(job['html_description'].find('<li>'), -1)
            self.assertNotEqual(job['html_description'].find('</li>'), -1)

    def test_no_null_values(self):
        # test that there's no literal null in html 'city' entry
        results = DEv2JobFeed(
                    'seo/tests/data/dseo_feed_0.markdown.xml', 
                    jsid=0) 
        jobs = results.solr_jobs()
        for job in jobs:
            self.assertNotEqual(job['city'], 'null')
        
    def test_dev2_feed(self):
        filepath = download_feed_file(self.buid_id)
        results = DEv2JobFeed(filepath)
        jobs = results.jobparse()
        self.assertEqual(results.jsid, self.buid_id)
        self.assertEqual(results.job_source_name, self.businessunit.title)
        self.assertEqual(len(jobs), self.numjobs)

    def test_mocids(self):
        """
        Tests that mocid fields exist when jobs are imported from a feed and
        added to a solr connnection
        
        """
        filepath = download_feed_file(self.buid_id)
        results = DEv2JobFeed(filepath)
        jobs = results.solr_jobs()
        # Since we're going to be adding/updating data in the Solr index, we're
        # hardcoding in the local Solr instance so that we don't accidentally
        # alter production data.
        self.conn.add(jobs)
        num_hits = self.conn.search(q="*:*",
                                    fq="buid:%s -mocid:[* TO *]" % self.buid_id)
        self.assertEqual(num_hits.hits, self.numjobs)
        for job in jobs:
            self.assertTrue('mocid' in job)

    def test_empty_feed(self):
        """
        Test that the schema for the v2 DirectEmployers feed file schema
        allows for empty feed files.
        
        """
        results = DEv2JobFeed(self.emptyfeed)
        # If the schema is such that empty feed files are considered invalid,
        # trying to run jobparse() will throw an exception.
        self.assertEqual(len(results.jobparse()), 0)

    def test_empty_solr(self):
        """
        Tests for the proper behavior when encountering a job-less, but
        otherwise valid, feed file. The proper behavior is to delete any
        jobs associated with that BusinessUnit from the Solr index.

        """
        # Normal download-and-parse operation on a feed file with jobs.
        update_solr(self.buid_id)
        results = self.conn.search(q="*:*", fq="buid:%s" % self.buid_id)
        self.assertEqual(results.hits, self.numjobs)

        # Download-and-parse operation on a feed file with no jobs. Expected
        # behavior is to delete all jobs.
        self._get_feedfile()
        update_solr(self.buid_id, download=False)
        results = self.conn.search(q="*:*", fq="buid:%s" % self.buid_id)
        self.assertEqual(results.hits, 0)

    def test_zipcode(self):
        """
        Tests to ensure proper behavior of zipcode field in being entered in
        Solr.

        """
        filepath = download_feed_file(self.buid_id)
        dbresults = DEv2JobFeed(filepath)
        solrresults = dbresults.solr_jobs()

        zips_from_feedfile = ['30269', '30269', '48332', '30269', '30269',
                              '30269', '30269', '30269', '48332', '48332',
                              '30269', None, '30269', '30269']

        solrzips = [i['zipcode'] for i in solrresults]
        for coll in [solrzips]:
            self.assertItemsEqual(zips_from_feedfile, coll)

    def test_salt_date(self):
        """
        Test to ensure that job postings show up in a quasi-random
        fashion by sorting by the `salted_date` attribute in the index
        vice strictly by `date_new`.
        
        """
        filepath = download_feed_file(self.buid_id)
        jobs = DEv2JobFeed(filepath)
        solrjobs = jobs.solr_jobs()
        self.conn.add(solrjobs)
        results = self.conn.search(q="*:*", sort="salted_date asc")
        self.assertEqual(self.numjobs, results.hits)
        # We can't really test for inequality between the two result sets,
        # since sometimes results.docs will equal results2.docs.
        results2 = self.conn.search(q="*:*", sort="date_new asc")
        self.assertItemsEqual(results2.docs, results.docs)

    def test_date_updated(self):
        """
        Test to ensure proper behavior of date updated field when added to
        Solr.

        """
        filepath = download_feed_file(self.buid_id)
        jobs = DEv2JobFeed(filepath)
        solrjobs = jobs.solr_jobs()
        self.conn.add(solrjobs)
        dates_updated = [datetime.datetime.strptime("4/16/2015 11:35:13 PM",
                                                    "%m/%d/%Y %I:%M:%S %p"),
                         datetime.datetime.strptime("4/16/2015 11:35:14 PM",
                                                    "%m/%d/%Y %I:%M:%S %p"),
                         datetime.datetime.strptime("4/16/2015 11:35:15 PM",
                                                    "%m/%d/%Y %I:%M:%S %p")]
        solr_dates = [i['date_updated'] for i in solrjobs]
        for solr_date in solr_dates:
            self.assertIn(solr_date, dates_updated)
        
    def _get_feedfile(self):
        # Download the 'real' feed file then copy the empty feed file in its
        # place.
        realfeed = download_feed_file(self.buid_id)
        shutil.copyfile(realfeed, "%s.bak" % realfeed)
        shutil.copyfile(self.emptyfeed, realfeed)

    def test_parse_malformed_feed(self):
        """
        Test that a malformed feedfile does not cause an unhandled exception.

        """
        result = DEv2JobFeed(self.malformed_feed, jsid=0)

    def test_parse_invalid_feed(self):
        """
        Test that a feed file that fails validation does not cause an unhandled
        exception. 

        """
        result = DEv2JobFeed(self.invalid_feed, jsid=0)

    def test_no_onets(self):
        result = DEv2JobFeed(self.no_onet_feed, jsid=0)
        jobs = result.solr_jobs()
        self.assertEqual(jobs[0]['onet'], '')

    def test_on_sites_by_buid(self):
        business_unit = BusinessUnitFactory(pk=77)

        results = DEv2JobFeed('seo/tests/data/dseo_feed_0.xml',
                              jsid=business_unit.id,
                              markdown=business_unit.enable_markdown)
        jobs = results.solr_jobs()
        for job in jobs:
            self.assertItemsEqual(job['on_sites'], [0])

        site_package = SitePackageFactory(owner=self.company)
        business_unit.site_packages.add(site_package)

        results = DEv2JobFeed('seo/tests/data/dseo_feed_0.xml',
                              jsid=business_unit.id,
                              markdown=business_unit.enable_markdown)
        jobs = results.solr_jobs()
        for job in jobs:
            self.assertItemsEqual(job['on_sites'], [site_package.pk])

        site_package2 = SitePackageFactory(owner=self.company)
        business_unit.site_packages.add(site_package2)

        results = DEv2JobFeed('seo/tests/data/dseo_feed_0.xml',
                              jsid=business_unit.id,
                              markdown=business_unit.enable_markdown)
        jobs = results.solr_jobs()
        for job in jobs:
            self.assertItemsEqual(job['on_sites'], [site_package.pk,
                                                    site_package2.pk])

        site_package2.delete()
        site_package.delete()
        business_unit.delete()

