from itertools import product
from datetime import datetime, timedelta
import random

from mypartners import helpers
from mypartners.forms import ContactRecordForm
from mypartners.tests.test_views import (MyPartnersTestCase,
                                         PartnerLibraryTestCase)
from mypartners.tests.factories import (ContactRecordFactory, PartnerFactory,
                                        PRMAttachmentFactory)



class HelpersTests(MyPartnersTestCase):

    def test_find_partner_from_email(self):
        email_and_expected_partner = [
            ('someone@my.jobs', self.partner),
            ('someone@www.my.jobs', self.partner),
            ('someone@notmy.jobs', None),
            (None, None),
        ]
        for email, expected_partner in email_and_expected_partner:
            partner = helpers.find_partner_from_email([self.partner], email)
            self.assertEqual(partner, expected_partner)

    def test_find_partner_from_email_no_partners(self):
        partner = helpers.find_partner_from_email(None, 'someone@my.jobs')
        self.assertIsNone(partner)

    def test_get_records_from_request_with_date(self):
        """ Make sure that the number of days shown in the date drop dwon
            matches the what was selected by user"""

        record_types = ["email", "phone", "meetingorevent"]
        date = ["0", "1", "30", "90", ""]

        params = product(record_types, date)

        for record_type, date in params:
            request = self.request_factory.get(
                'prm/view/reports/details/records/', dict(
                    company=self.company.id,
                    partner=self.partner.id,
                    record_type=record_type,
                    date=date,
                )
            )
            request.user = self.staff_user

            response = helpers.get_records_from_request(request)
            (range_start, range_end), date_str, records = response

            expected = date_str.split()[0].lstrip("-")

            if expected.isdigit():
                days = int(expected)
                if days == 1:
                    self.assertEqual("1 Day", date_str)
                else:
                    self.assertEqual(
                        "%i Days" % (range_end - range_start).days, date_str)
            else:
                self.assertEqual("View All", date_str)

    def test_get_form_delta(self):
        """Test that all form changes are properly logged as a delta."""
        attachment = PRMAttachmentFactory()
        contact_record = attachment.contact_record
        form = ContactRecordForm(instance=contact_record, 
                                 partner=attachment.partner)

        # TODO:
        # - figure out the syntax for form save with deleted attachment
        # - assert no errors
        # - check the delta


    def test_start_date_before_end_date(self):
        request = self.request_factory.get(
            'prm/view/reports/details/records/', dict(
                company=self.company.id,
                partner=self.partner.id,
                range_start='02/15/14',
                range_end='04/15/12'))
        request.user = self.staff_user

        response = helpers.get_records_from_request(request)
        (start_date, end_date), _, _ = response
        self.assertGreaterEqual(end_date, start_date)


class PartnerLibraryFilterTests(PartnerLibraryTestCase):

    def test_all_ofccp_partners_available(self):
        """
        When a company doesn't have any OFCCP partners, they should all be
        available to choose from in the partner library search.
        """
        partner_count = self.partner_library.count()
        request = self.request_factory.get(
            'prm/view/partner-library/', dict(company=self.company.id))
        request.user = self.staff_user

        partners = helpers.filter_partners(request, partner_library=True)

        self.assertEqual(len(partners), partner_count)

    def test_ofccp_duplicates_ignored(self):
        """
        When a company has already added OFCCP partners, those partners should
        not be displayed in the filter search results.
        """

        # create a new partner
        library_id = random.randint(1, self.partner_library.count())
        request = self.request_factory.get(
            'prm/view/partner-library/add', dict(
                company=self.company.id, library_id=library_id))
        request.user = self.staff_user
        partner = helpers.new_partner_from_library(request)

        # get a list of OFCCP partners
        request = self.request_factory.get(
            'prm/view/partner-library', dict(company=self.company.id))
        request.user = self.staff_user
        library = helpers.filter_partners(request, partner_library=True)

        self.assertFalse(partner.library.id in [p.id for p in library])

    def test_keyword_filter(self):
        """
        When a user tries to filter using keywords, the partner name, partner
        URI, and contact name should be searched.
        """

        request = self.request_factory.get(
            'prm/view/partner-library/', dict(
                company=self.company.id,
                keywords='center, .org'))
        request.user = self.staff_user

        partners = helpers.filter_partners(request, partner_library=True)
        self.assertTrue(partners)

        for partner in partners:
            searchable_fields = " ".join(
                [partner.name, partner.uri, partner.contact_name,
                 partner.email]).lower()

            self.assertIn('center', searchable_fields)
            self.assertIn('.org', searchable_fields)

    def test_state_filter(self):
        """
        Filter by state.
        """

        request = self.request_factory.get(
            'prm/view/partner-library/', dict(
                company=self.company.id,
                state='PA'))
        request.user = self.staff_user

        partners = helpers.filter_partners(request, partner_library=True)
        self.assertTrue(partners)

        for partner in partners:
            self.assertEqual(partner.st, 'PA')

    def test_city_filter(self):
        """
        Filter by city.
        """

        request = self.request_factory.get(
            'prm/view/partner-library/', dict(
                company=self.company.id,
                city='Pittsburgh'))
        request.user = self.staff_user

        partners = helpers.filter_partners(request, partner_library=True)
        self.assertTrue(partners)

        for partner in partners:
            self.assertEqual(partner.city, 'Pittsburgh')

    def test_date_filters(self):
        """
        Filter by activity start and end date.

        """
        end_date = datetime.now().date()

        # randomly create partners and assign them contact records ranging from
        # 60 days ago to now.
        partners = [PartnerFactory(owner=self.company) for i in range(3)]
        partners.append(self.partner)

        # we want the contact records to exist before the tests, hence the
        # second for loop
        for days in [60, 30, 1, 0]:
            ContactRecordFactory(partner=random.choice(partners),
                                 date_time=end_date - timedelta(days))

        for days in [60, 30, 1, 0]:
            start_date = (datetime.now() - timedelta(days)).date()

            request = self.request_factory.get(
                'prm/view/partner-library', dict(
                    company=self.company.id,
                    start_date=start_date.strftime("%m/%d/%Y"),
                    end_date=end_date.strftime("%m/%d/%Y")))
            request.user = self.staff_user

            partners = helpers.filter_partners(request)

            for partner in partners:
                date_times = [c.date_time.date()
                              for c in partner.contactrecord_set.all()]

                # ensure that for each partner, at least one contact record is
                # within range
                if partner.contactrecord_set.all():
                    self.assertTrue(filter(
                        lambda x: start_date <= x <= end_date , date_times))
