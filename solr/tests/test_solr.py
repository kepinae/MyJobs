import datetime
import uuid

from mock import Mock
import pytz

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from myjobs.tests.setup import MyJobsBase
from mydashboard.tests.factories import CompanyFactory, BusinessUnitFactory
from myjobs.models import User
from myjobs.tests.factories import UserFactory
from myprofile.models import ProfileUnits
from myprofile.tests.factories import (PrimaryNameFactory, AddressFactory,
                                       SummaryFactory)
from mysearches.models import SavedSearch
from mysearches.tests.factories import SavedSearchFactory
from solr.models import Update
from solr.helpers import Solr
from solr.signals import profileunits_to_dict, object_to_dict
from solr.tests.helpers import MockLog
from tasks import update_solr_task, parse_log, delete_old_analytics_docs


class SolrTests(MyJobsBase):
    def setUp(self):
        super(SolrTests, self).setUp()
        self.test_solr = settings.TEST_SOLR_INSTANCE

    def tearDown(self):
        super(SolrTests, self).tearDown()
        Solr().delete()

    def test_adding_and_deleting_signals(self):
        """
        Adds and deletes ProfileUnits, Users, and SavedSearches to confirm that
        they are being correctly flagged for addition to and deletion from solr
        and runs add/deletion task to confirm that they are being properly
        added to and deleted from solr.

        """
        Solr().delete()
        user = UserFactory(email="example@example.com")
        PrimaryNameFactory(user=user)

        for i in range(5):
            # Create 5 new users
            user = UserFactory(email='example%s@example.com' % i)
            for search in ['django', 'python', 'programming']:
                # Create 15 new searches and assign three per user
                SavedSearchFactory(user=user,
                                   url='http://test.jobs/search?q=%s' % search,
                                   label='%s Jobs' % search)
        # 6 Users + 15 SavedSearches + 1 ProfileUnit = 22
        self.assertEqual(Update.objects.all().count(), 22)
        update_solr_task(self.test_solr)
        self.assertEqual(Solr().search().hits, 22)
        SavedSearch.objects.all().delete()
        update_solr_task(self.test_solr)
        self.assertEqual(Solr().search().hits, 7)
        User.objects.all().delete()
        update_solr_task(self.test_solr)
        self.assertEqual(Solr().search().hits, 0)

    def test_xml_chars(self):
        Solr().delete()

        user = UserFactory(email="example@example.com")
        SummaryFactory(user=user, the_summary='&&& \x01test\x02')

        update_solr_task(self.test_solr)
        self.assertEqual(Solr().search().hits, 2)

    def test_profileunit_to_dict(self):
        """
        Confirms that a solr dictionary is being generated as expected by
        the profileunits_to_dict function.

        """
        user = UserFactory(email="example@example.com")
        name = PrimaryNameFactory(user=user)
        content_type = ContentType.objects.get_for_model(ProfileUnits)

        expected = {
            "Name_content_type_id": [25],
            "Name_given_name": ["Alice"],
            "uid": "%s##%s" % (str(content_type.pk), str(user.pk)),
            "ProfileUnits_user_id": 1,
            "Name_user_id": [1],
            "Name_id": [name.pk],
            "Name_family_name": ["Smith"],
            "Name_primary": [True],
        }

        result = profileunits_to_dict(user.id)

        self.assertEqual(result['Name_id'], expected['Name_id'])
        self.assertEqual(result['uid'], expected['uid'])

    def test_user_to_dict(self):
        """
        Confirms that a solr dictionary is being generated as expected by
        the object_to_dict function for Users.

        """
        user = UserFactory(email="example@example.com")
        content_type = ContentType.objects.get_for_model(User)
        expected = {
            'User_is_superuser': False,
            u'User_id': 1,
            'uid': '%s##%s' % (str(content_type.pk), str(user.pk)),
            'User_is_active': True,
            'User_user_guid': 'c1cf679c-86f8-4bce-bf1a-ade8341cd3c1',
            'User_is_staff': False, 'User_first_name': u'',
            'User_gravatar': 'alice@example.com',
            'User_last_name': u'',
            'User_is_disabled': False,
            'User_opt_in_myjobs': True,
            'User_profile_completion': 0,
            'User_opt_in_employers': True,
            'User_email': 'example@example.com',
        }

        result = object_to_dict(User, user)

        # Exact dictionary comparisons can't be made because of the datetime
        # fields, so compare a few fields instead.
        self.assertEqual(expected['uid'], result['uid'])
        self.assertEqual(expected['User_email'], result['User_email'])

    def test_savedsearch_to_dict(self):
        """
        Confirms that a solr dictionary is being generated as expected by
        the object_to_dict function for SavedSearch.

        """
        user = UserFactory(email="example@example.com")
        search = SavedSearchFactory(user=user)
        content_type = ContentType.objects.get_for_model(SavedSearch)
        expected = {'User_is_superuser': False,
                    'uid': '%s##%s' % (str(content_type.pk), str(search.pk)),
                    'User_is_staff': False,
                    'SavedSearch_day_of_month': None,
                    'User_is_disabled': False,
                    'SavedSearch_last_sent': None,
                    'User_email': 'example@example.com',
                    'SavedSearch_feed': 'http://www.my.jobs/jobs/feed/rss?',
                    'SavedSearch_is_active': True,
                    'SavedSearch_label': 'All Jobs',
                    'User_user_guid': '9ba19d0d-6ee1-4032-a2b8-50a1fc4c1ab5',
                    u'SavedSearch_id': 1,
                    'SavedSearch_email': 'alice@example.com',
                    'SavedSearch_notes': 'All jobs from www.my.jobs',
                    'SavedSearch_frequency': 'W', u'User_id': 1,
                    'User_gravatar': 'alice@example.com',
                    'User_last_name': u'',
                    'SavedSearch_user_id': 1,
                    'User_opt_in_myjobs': True,
                    'User_profile_completion': 0,
                    'SavedSearch_day_of_week': '1',
                    'User_is_active': True,
                    'User_first_name': u'',
                    'SavedSearch_url': 'http://www.my.jobs/jobs',
                    'User_opt_in_employers': True,
                    'SavedSearch_sort_by': 'Relevance'
        }

        result = object_to_dict(SavedSearch, search)

        # Exact dictionary comparisons can't be made because of the datetime
        # fields, so compare a few fields instead.
        self.assertEqual(expected['uid'], result['uid'])
        self.assertEqual(expected['User_email'], result['User_email'])
        self.assertEqual(expected['SavedSearch_url'], result['SavedSearch_url'])

    def test_savedsearch_no_user(self):
        """
        A saved search with a null recipient should never be inserted in Solr
        """
        solr = Solr()
        SavedSearchFactory()
        update_solr_task(self.test_solr)
        results = solr.search(q='*:*')
        # One hit for the search, one for its recipient
        self.assertEqual(results.hits, 2)

        solr.delete()
        search = SavedSearchFactory(user=None)
        self.assertEqual(object_to_dict(SavedSearch, search), None)
        update_solr_task(self.test_solr)
        results = solr.search(q='*:*')
        self.assertEqual(results.hits, 0)

    def test_address_slabs(self):
        expected = {
            'Address_content_type_id': [26],
            'Address_address_line_two': [u'Apt. 8'],
            u'Address_id': [1],
            'uid': '23##1',
            'ProfileUnits_user_id': 1,
            'Address_country_code': [u'USA'],
            'Address_region': [u'USA##IN'],
            'Address_country_sub_division_code': [u'IN'],
            'Address_postal_code': [u'12345'],
            'Address_address_line_one': [u'1234 Thing Road'],
            'Address_user_id': [1],
            'Address_label': [u'Home'],
            'Address_full_location': [u'USA##IN##Indianapolis'],
            'Address_city_name': [u'Indianapolis']
        }

        user = UserFactory(email="example@example.com")
        AddressFactory(user=user)
        result = profileunits_to_dict(user.id)

        self.assertEqual(expected['Address_country_code'],
                         result['Address_country_code'])
        self.assertEqual(expected['Address_region'],
                         result['Address_region'])
        self.assertEqual(expected['Address_full_location'],
                         result['Address_full_location'])

    def test_presave_ignore(self):
        user = UserFactory(email="test@test.test")
        update_solr_task(self.test_solr)

        user.last_login = datetime.datetime(2011, 8, 15, 8, 15, 12, 0, pytz.UTC)
        user.save()

        self.assertEqual(Update.objects.all().count(), 0)

        user.last_login = datetime.datetime(2013, 8, 15, 8, 15, 12, 0, pytz.UTC)
        user.email = "test1@test1.test1"
        user.save()

        self.assertEqual(Update.objects.all().count(), 1)

    def test_analytics_log_parsing(self):
        """
        Ensure that analytics logs are parsed and stored in solr correctly
        """
        company = CompanyFactory(id=1)
        business_unit = BusinessUnitFactory(id=1000)
        company.job_source_ids.add(business_unit)

        # match and no_match will be used later to ensure that the correct
        # number of documents were associated with a company or associated
        # with the default company
        match = Mock(
            wraps=lambda: self.assertEqual(doc['company_id'], company.pk))
        no_match = Mock(
            wraps=lambda: self.assertEqual(doc['company_id'], 999999))

        for log_type in ['analytics', 'redirect']:
            log = MockLog(log_type=log_type)
            parse_log([log], self.test_solr)

            solr = Solr()
            results = solr.search(q='uid:analytics*')

            # fake logs contain two lines - one human and one bot hit
            # If it is getting processed correctly, there should be only one
            # hit recorded
            self.assertEqual(results.hits, 1)
            multi_field = 'facets'
            if log_type == 'redirect':
                with self.assertRaises(KeyError):
                    results.docs[0][multi_field]
            else:
                self.assertEqual(len(results.docs[0][multi_field]), 2)
            for field in results.docs[0].keys():
                if field != multi_field:
                    self.assertTrue(type(results.docs[0][field] != list))
            uuid.UUID(results.docs[0]['aguid'])
            with self.assertRaises(KeyError):
                results.docs[0]['User_user_guid']

            for doc in results.docs:
                if doc['job_view_buid'] == business_unit.pk:
                    # If business units match, company ids should match
                    match()
                else:
                    # Business units don't match; company id should be set to
                    # the default company
                    no_match()

            solr.delete()
            user = UserFactory()
            user.user_guid = '1e5f7e122156483f98727366afe06e0b'
            user.save()
            parse_log([log], self.test_solr)
            results = solr.search(q='uid:analytics*')
            for guid in ['aguid', 'User_user_guid']:
                uuid.UUID(results.docs[0][guid])

            solr.delete()
            user.delete()

        # We have already determined that there are only two documents.
        # Ensure that there is exactly one document that matches a specific
        # company and one document that was given the default company
        self.assertEqual(match.call_count, 1)
        self.assertEqual(no_match.call_count, 1)

    def test_analytics_delete_old_data(self):
        """
        When Solr is updated with analytics data, we should delete all docs
        from the "current" collection older than 30 days.
        """
        solr = Solr()

        # Create old logs that will be pruned when delete is run
        logs = [MockLog(log_type=type_, delta=datetime.timedelta(days=-31))
                for type_ in ['analytics', 'redirect']]
        parse_log(logs, self.test_solr)
        results = solr.search(q='doc_type:analytics')
        self.assertEqual(results.hits, 2, 'Old logs were not added')
        old_uids = {doc['uid'] for doc in results.docs}

        # Create logs timestamped for today
        logs = [MockLog(log_type=type_) for type_ in ['analytics', 'redirect']]
        parse_log(logs, self.test_solr)
        results = solr.search(q='doc_type:analytics')
        self.assertEqual(results.hits, 4, 'New logs were not added')
        all_uids = {doc['uid'] for doc in results.docs}

        # delete_old_analytics_docs is called after parse_logs in read_new_logs
        # and has not been called yet. Call it now
        delete_old_analytics_docs()
        results = solr.search(q='doc_type:analytics')
        self.assertEqual(results.hits, 2, 'Old logs were not deleted')
        new_uids = {doc['uid'] for doc in results.docs}

        # Ensure that the correct documents have been added/removed
        # The old and new uid sets should be disjoint (no elements in common)
        self.assertTrue(old_uids.isdisjoint(new_uids),
                        'Sets are not disjoint; Intersecting elements: %s' %
                        str(old_uids.intersection(new_uids)))
        # Since the old and new uid sets have nothing in common, their union
        # should equal the set of all uids
        self.assertEqual(old_uids.union(new_uids),
                         all_uids,
                         'Sets are not equal; difference: %s' %
                         str(old_uids.union(new_uids).symmetric_difference(
                             all_uids)))
