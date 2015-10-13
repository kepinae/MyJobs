from myreports.tests.setup import MyReportsTestCase

from myreports.models import (
    UserType, ReportingType, ReportType, Configuration, DynamicReport)
from myjobs.tests.factories import UserFactory
from mypartners.tests.factories import ContactFactory, PartnerFactory
from seo.tests.factories import CompanyUserFactory


class TestModels(MyReportsTestCase):
    fixtures = ['class_and_pres.json']

    def test_jobseeker_user_type(self):
        user = UserFactory.create()
        self.assert_user_type(None, user)

    def test_employer_user_type(self):
        cuser = CompanyUserFactory.create()
        user = cuser.user
        self.assert_user_type('EMPLOYER', user)

    def test_staff_user_type(self):
        user = UserFactory.create()
        user.is_staff = True
        self.assert_user_type('STAFF', user)

    def assert_user_type(self, expected, user):
        self.client.login_user(self.user)
        user_type = UserType.objects.for_user(user)
        if expected is None:
            self.assertTrue(user_type is None)
        else:
            self.assertEqual(expected, user_type.user_type)

    def test_active_reporting_type(self):
        reporting_type = (ReportingType.objects
                          .active_for_user(self.user).first())
        self.assertEqual('PRM', reporting_type.reporting_type)

    def test_active_report_type_by_reporting_type(self):
        reporting_type = ReportingType.objects.get(id=1)
        report_types = (ReportType.objects
                        .active_for_reporting_type(reporting_type))
        names = set(t.report_type for t in report_types)
        self.assertEqual(set(['Partners', 'Communication Records']), names)


class TestDynamicReport(MyReportsTestCase):
    fixtures = ['class_and_pres.json']

    def test_report(self):
        """Run a dynamic report through it's paces."""

        partner = PartnerFactory(owner=self.company)
        for i in range(0, 10):
            ContactFactory.create(name="name-%s" % i, partner=partner)

        config = Configuration.objects.get(id=3)
        report = DynamicReport.objects.create(
            configuration=config,
            owner=self.company)
        report.regenerate()
        self.assertEqual(10, len(report.python))
