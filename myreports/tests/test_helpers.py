"""Tests associated with myreports helpers."""

import csv
import json
from cStringIO import StringIO
from django.test.client import RequestFactory

from mypartners.tests.factories import ContactRecordFactory, TagFactory
from mypartners.models import ContactRecord
from myreports.tests.test_views import MyReportsTestCase
from myreports import helpers


class TestHelpers(MyReportsTestCase):
    def setUp(self):
        super(TestHelpers, self).setUp()

        tags = [TagFactory(name=name, company=self.company) for name in [
            'test', 'stuff', 'working']]

        # Returns a list rather than a QuerySet, which is what the helper
        # functions use, so saving this to a variable isn't really helpful
        ContactRecordFactory.create_batch(
            10, partner=self.partner, contact__name='Joe Shmoe', tags=tags)
        self.records = ContactRecord.objects.all()

    def test_serialize_python(self):
        """
        Test that serializing a `QuerySet` into a Python object creates the
        correct number of `dict`s.
        """

        data = helpers.serialize('python', self.records)

        self.assertEqual(len(data), self.records.count())

    def test_serialize_values(self):
        """
        Test that if the `values` parameter is specified, column
        inclusion/exclusion as well as column ordering is respected.
        """

        # by default, all fields except pk should be inclued, and columns
        # should be sorted alphabetically
        data = helpers.serialize('python', self.records)
        values = data[-1].keys()

        self.assertEqual(data[0].keys(), sorted(values))

        # when values are specified, output records should respec the nubmer
        # and order of fields specified
        values = ['contact', 'contact_email', 'tags']
        data = helpers.serialize('python', self.records, values=values)

        self.assertEqual(data[0].keys(), values)

    def test_serialize_order_by(self):
        """
        Test that if the `order_by` parameter is specified, records are ordered
        by that parameter's value.
        """

        data = helpers.serialize(
            'python', self.records, order_by='-date_time')

        datetimes = [record['date_time'] for record in data]
        # make sure the earliest time is first
        self.assertTrue(max(datetimes) == datetimes[0])
        # make sure that the latest time is last
        self.assertTrue(min(datetimes) == datetimes[-1])

    def test_serialize_strip_html(self):
        """
        Test that HTML is properly stripped from fields when being serialized.
        """

        # Only adding notes to one recod so that we can test that empty notes
        # are parsed correctly as well
        record = self.records[0]
        record.notes = """
        <div class="tip-content">
            Saved Search Notification<br />
            <a href="https://secure.my.jobs">My.jobs</a>
            <p>Saved search was created on your behalf</p>
        </div>
        """
        record.save()

        data = helpers.serialize('python', self.records)

        for record in data:
            text = ''.join(str(value) for value in record.values())
            self.assertTrue('<' not in text, text)
            self.assertTrue('>' not in text, text)

    def test_serialize_json(self):
        """
        Test that serializing to JSON creates the correct number of
        objects.
        """

        # JSON is returned as a string, but deserializing it after serializing
        # it should create a list of dicts comparable to the number of records
        # that actually exist.
        data = json.loads(helpers.serialize('json', self.records))

        self.assertEqual(len(data), self.records.count())

    def test_serialize_csv(self):
        """Test that serializing to CSV creates the correct number of rows."""

        data = StringIO(helpers.serialize('csv', self.records))
        reader = csv.reader(data, delimiter=',')

        self.assertEqual(len(list(reader)) - 1, self.records.count())

    def test_parse_params(self):
        """Test that params are properly parsed from a `QueryDict`."""

        factory = RequestFactory()
        request = factory.post(
            '/reports/view/mypartners/contact',
            data=dict(
                baz=u'',
                biz=[u'bez', u''],
                foo=['bar', 'baz'],
                buz=['biz'],
                quz='fizz',
                quox='false'
            ))

        params = helpers.parse_params(request.POST)

        # Singleton lists should be flattened into single elements, lists
        # should be converted to tuples, and already flat elements should
        # remain untouched.
        self.assertEqual(params, dict(
            biz=u'bez', foo=('bar', 'baz'), buz='biz', quz='fizz',
            quox=False))
