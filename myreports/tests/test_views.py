"""Tests associated with myreports views."""

import json
import os

from django.test import TestCase
from django.core.urlresolvers import reverse

from myjobs.tests.test_views import TestClient
from myjobs.tests.factories import UserFactory
from mypartners.tests.factories import (ContactFactory, ContactRecordFactory,
                                        LocationFactory, PartnerFactory)
from myreports.models import Report
from seo.tests.factories import CompanyFactory, CompanyUserFactory


class MyReportsTestCase(TestCase):
    """
    Base class for all MyReports Tests. Identical to `django.test.TestCase`
    except that it provides a MyJobs TestClient instance and a logged in user.
    """
    def setUp(self):
        self.client = TestClient()
        self.user = UserFactory(email='testuser@directemployers.org')
        self.company = CompanyFactory(name='Test Company')
        self.partner = PartnerFactory(name='Test Partner', owner=self.company)

        # associate company to user
        CompanyUserFactory(user=self.user, company=self.company)

        self.client.login_user(self.user)


class TestOverview(MyReportsTestCase):
    """Tests the reports view, which is the landing page for reports."""

    def test_available_to_staff(self):
        """Should be available to staff users."""

        response = self.client.get(reverse('overview'))

        self.assertEqual(response.status_code, 200)


class TestViewRecords(MyReportsTestCase):
    """
    Tests the `view_records` view which is used to query various models.
    """

    def setUp(self):
        super(TestViewRecords, self).setUp()
        self.client = TestClient(path='/reports/ajax/mypartners',
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.login_user(self.user)

        ContactRecordFactory.create_batch(
            10, partner=self.partner, contact__name='Joe Shmoe')

    def test_restricted_to_ajax(self):
        """View should only be reachable through AJAX."""

        self.client.path += '/partner'
        self.client.defaults.pop('HTTP_X_REQUESTED_WITH')
        response = self.client.post()

        self.assertEqual(response.status_code, 404)

    def test_restricted_to_get(self):
        """POST requests should raise a 404."""

        self.client.path += '/partner'
        response = self.client.post()

        self.assertEqual(response.status_code, 404)

    def test_json_output(self):
        """Test that filtering contact records through ajax works properly."""

        # records to be filtered out
        ContactRecordFactory.create_batch(10, contact__name='John Doe')

        self.client.path += '/contactrecord'
        response = self.client.get(data={'contact__name': 'Joe Shmoe'})
        output = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(output), 10)

    def test_only_user_results_returned(self):
        """Results should only contain records user has access to."""

        # records not owned by user
        partner = PartnerFactory(name="Wrong Partner")
        ContactRecordFactory.create_batch(10, partner=partner)

        self.client.path += '/contactrecord'
        response = self.client.get()
        output = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(output), 10)

    def test_filtering_on_partner(self):
        """Test the ability to filter by partner."""

        # we already have one because of self.partner
        PartnerFactory.create_batch(9, name="Test Partner", owner=self.company)

        self.client.path += '/partner'
        response = self.client.get(data={'name': 'Test Partner'})
        output = json.loads(response.content)

        # ContactRecordFactory creates 10 partners in setUp
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(output), 10)

    def test_list_query_params(self):
        """Test that query parameters that are lists are parsed correctly."""

        contacts = ContactFactory.create_batch(10, partner__owner=self.company)
        pks = [contact.pk for contact in contacts[:5]]

        self.client.path += '/partner'
        response = self.client.get(data={'contact': pks})
        output = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(output), 5)

    def test_filtering_on_contact(self):
        """Test the ability to filter by contact."""

        ContactFactory.create_batch(10, name="Jen Doe", partner=self.partner)

        # contacts with the wrong name
        ContactFactory.create_batch(10, name="Jen Smith", partner=self.partner)

        self.client.path += '/contact'
        response = self.client.get(data={'name': 'Jen Doe'})
        output = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(output), 10)

    def test_filter_by_state(self):
        """Tests that filtering by state works."""

        indiana = LocationFactory(state="IN")
        ContactFactory.create_batch(10, name="Jen Doe", partner=self.partner,
                                    locations=[indiana])

        self.client.path += '/contact'
        response = self.client.get(data={'state': 'IN'})
        output = json.loads(response.content)

        self.assertEqual(len(output), 10)

    def test_filter_by_city(self):
        """Tests that filtering by city works."""

        indianapolis = LocationFactory(city="Indianapolis")
        ContactFactory.create_batch(10, name="Jen Doe", partner=self.partner,
                                    locations=[indianapolis])

        self.client.path += '/contact'
        response = self.client.get(data={'city': 'indianapolis'})
        output = json.loads(response.content)

        self.assertEqual(len(output), 10)


class TestReportView(MyReportsTestCase):
    """
    Tests the ReportView class, which is used to create and retrieve
    reports.
    """
    def setUp(self):
        super(TestReportView, self).setUp()
        self.client = TestClient(path=reverse('reports', kwargs={
            'app': 'mypartners', 'model': 'contactrecord'}))
        self.client.login_user(self.user)

        ContactRecordFactory.create_batch(5, partner__owner=self.company)
        ContactRecordFactory.create_batch(
            5, contact_type='job', job_applications=1,
            partner__owner=self.company)
        ContactRecordFactory.create_batch(
            5, contact_type='job',
            job_hires=1, partner__owner=self.company)

    def test_create_report(self):
        """Test that a report model instance is properly created."""

        # create a report whose results is for all contact records in the
        # company
        response = self.client.post()
        report_name = response.content
        report = Report.objects.get(name=report_name)

        self.assertEqual(len(report.python), 15)

        # we use this in other tests

        return report_name

    def test_get_report(self):
        """Test that chart data is retreived from record results."""

        report_name = self.test_create_report()
        report = Report.objects.get(name=report_name)

        response = self.client.get(data={'id': report.pk})
        data = json.loads(response.content)

        # check contact record stats
        for key in ['applications', 'hires', 'communications', 'emails']:
            self.assertEqual(data[key], 5)

        # check contact stats
        self.assertEqual(data['contacts'][0]['records'], 1)
        self.assertEqual(data['contacts'][0]['referrals'], 10)


class TestDownloads(MyReportsTestCase):
    """Tests the reports view."""

    def setUp(self):
        super(TestDownloads, self).setUp()
        self.client = TestClient(path=reverse('downloads'),
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.login_user(self.user)

        ContactRecordFactory.create_batch(10, partner__owner=self.company)

    def test_column_order(self):
        """Tests that column order is preserved"""

        # create a report whose results is for all contact records in the
        # company
        response = self.client.post(
            path=reverse('reports', kwargs={
                'app': 'mypartners', 'model': 'contactrecord'}),
            data={'values': ['partner', 'contact__name', 'contact_type']})

        report_name = response.content
        report = Report.objects.get(name=report_name)

        response = self.client.get(data={'id': report.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['columns'], {
            'Partner': True, 'Contact Name': True, 'Contact Type': True})

    def test_blacklisted_columns(self):
        """Test that blacklisted columns aren't visible."""
        blacklist = ['pk', 'approval_status']
        response = self.client.post(
            path=reverse('reports', kwargs={
                'app': 'mypartners', 'model': 'contactrecord'}),
            data={'values': ['partner', 'contact__name', 'contact_type']})

        report_name = response.content
        report = Report.objects.get(name=report_name)

        response = self.client.get(data={'id': report.id})
        self.assertFalse(
            set(response.context['columns']).intersection(blacklist))


class TestDownloadReport(MyReportsTestCase):
    """Tests that reports can be downloaded."""

    def setUp(self):
        super(TestDownloadReport, self).setUp()
        self.client = TestClient(path=reverse('download_report'))
        self.client.login_user(self.user)

        ContactRecordFactory.create_batch(5, partner__owner=self.company)
        ContactRecordFactory.create_batch(
            5, contact_type='job', job_applications=1,
            partner__owner=self.company)
        ContactRecordFactory.create_batch(
            5, contact_type='job',
            job_hires=1, partner__owner=self.company)

    def test_download_csv(self):
        """Test that a report can be downloaded in CSV format."""

        # create a report whose results is for all contact records in the
        # company
        response = self.client.post(path=reverse('reports', kwargs={
            'app': 'mypartners', 'model': 'contactrecord'}))
        report_name = response.content
        report = Report.objects.get(name=report_name)
        python = report.python

        # download the report
        response = self.client.get(data={
            'id': report.pk,
            'values': ['contact', 'contact_email', 'contact_phone']})

        self.assertEqual(response['Content-Type'], 'text/csv')

        # specifying export values shouldn't modify the underlying report
        self.assertEqual(len(python[0].keys()), len(report.python[0].keys()))
        

class TestRegenerate(MyReportsTestCase):
    """Tests the reports can be regenerated."""

    def setUp(self):
        super(TestRegenerate, self).setUp()
        self.client = TestClient(path=reverse('reports', kwargs={
            'app': 'mypartners', 'model': 'contactrecord'}))
        self.client.login_user(self.user)

        ContactRecordFactory.create_batch(10, partner__owner=self.company)

    def test_regenerate(self):
        # create a new report
        response = self.client.post(
            path=reverse('reports', kwargs={
                'app': 'mypartners', 'model': 'contactrecord'}))

        report_name = response.content
        report = Report.objects.get(name=report_name)

        response = self.client.get(data={'id': report.id})
        self.assertEqual(response.status_code, 200)

        # remove report results and ensure we can still get a reasonable
        # response
        report.results.delete()
        report.save()
        self.assertFalse(report.results)

        response = self.client.get(data={'id': report.id})
        self.assertEqual(response.status_code, 200)

        # regenerate results and ensure they are the same as the original
        response = self.client.get(path=reverse('regenerate'), data={
            'id': report.pk})
        report = Report.objects.get(name=report_name)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(report.results)

        # regenerate report without deleting the report prior
        # see if it overwrites other report.
        results = report.results
        response = self.client.get(path=reverse('regenerate'), data={
            'id': report.pk})
        report = Report.objects.get(name=report_name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(results.name, report.results.name)

    def test_regenerating_missing_file(self):
        """Tests that a report can be regenerated when file is missing."""

        # create a new report
        response = self.client.post(
            path=reverse('reports', kwargs={
                'app': 'mypartners', 'model': 'contactrecord'}))

        report_name = response.content
        report = Report.objects.get(name=report_name)

        # report should have results
        self.assertTrue(report.results)

        # delete physical file and ensure that json reflects the missing link
        os.remove(report.results.file.name)
        report = Report.objects.get(pk=report.pk)
        self.assertFalse(report.results)
        self.assertEqual(report.json, u'{}')
        self.assertEqual(report.python, {})
    
        # regenerate the report even though the file is physically missing
        report.regenerate()
        self.assertTrue(report.results)
