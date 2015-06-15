import urllib
from django.contrib.auth.models import Group
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.http import urlquote

from setup import MyJobsBase
from myjobs.models import User
from myjobs.tests.test_views import TestClient
from myjobs.tests.factories import UserFactory
from myprofile.models import SecondaryEmail, Name, Telephone
from mysearches.models import PartnerSavedSearch
from myreports.models import Report
from seo.tests.factories import CompanyFactory
from mysearches.tests.factories import PartnerSavedSearchFactory


class UserManagerTests(MyJobsBase):
    user_info = {'password1': 'complicated_password',
                 'email': 'alice@example.com',
                 'send_email': True}

    def test_user_validation(self):
        user_info = {'password1': 'complicated_password',
                     'email': 'Bad Email'}
        with self.assertRaises(ValidationError):
            User.objects.create_user(**user_info)
        self.assertEqual(User.objects.count(), 0)

    def test_user_creation(self):
        new_user, _ = User.objects.create_user(**self.user_info)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(new_user.is_active, True)
        self.assertEqual(new_user.is_verified, False)
        self.assertEqual(new_user.email, 'alice@example.com')
        self.failUnless(new_user.check_password('complicated_password'))
        self.failUnless(new_user.groups.filter(name='Job Seeker').count() == 1)
        self.assertIsNotNone(new_user.user_guid)

    def test_superuser_creation(self):
        new_user = User.objects.create_superuser(
            **{'password': 'complicated_password',
               'email': 'alice@example.com'})
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(new_user.is_superuser, True)
        self.assertEqual(new_user.is_staff, True)
        self.assertEqual(new_user.email, 'alice@example.com')
        self.failUnless(new_user.check_password('complicated_password'))
        self.failUnless(new_user.groups.filter(name='Job Seeker').count() == 1)
        self.assertIsNotNone(new_user.user_guid)

    def test_gravatar_url(self):
        """
        Test that email is hashed correctly and returns a 200 response
        """
        user = UserFactory()
        gravatar_url = "http://www.gravatar.com/avatar/c160f8cc69a4f0b" \
                              "f2b0362752353d060?s=20&d=mm"
        no_gravatar_url = ("<div class='gravatar-blank gravatar-danger' "
                               "style='height: 20px; width: 20px'>"
                               "<span class='gravatar-text' "
                               "style='font-size:13.0px;'>A</span></div>")
        generated_gravatar_url = user.get_gravatar_url()
        self.assertEqual(no_gravatar_url, generated_gravatar_url)
        status_code = urllib.urlopen(gravatar_url).getcode()
        self.assertEqual(status_code, 200)

    def test_not_disabled(self):
        """
        An anonymous user who provides the :verify: query string or
        user with is_disabled set to True should be redirected to the home
        page. An anonymous user who does not should see a 404. A user with
        is_active set to False should proceed to their destination.
        """
        client = TestClient()
        user = UserFactory()

        #Anonymous user
        resp = client.get(reverse('view_profile'))
        path = resp.request.get('PATH_INFO')
        self.assertRedirects(resp, reverse('home') + '?next=' + path)

        # This is ugly, but it is an artifact of the way Django redirects
        # users who fail the `user_passes_test` decorator.
        qs = '?verify=%s' % user.user_guid
        next_qs = '?next=' + urlquote('/profile/view/%s' % qs)

        # Anonymous user navigates to url with :verify: in query string
        resp = client.get(reverse('view_profile') + qs)
        # Old path + qs is urlquoted and added to the url as the :next: param
        self.assertRedirects(resp, "http://testserver/" + next_qs)

        # Active user
        client.login_user(user)
        resp = client.get(reverse('view_profile'))
        self.assertTrue(resp.status_code, 200)

        #Disabled user
        user.is_disabled = True
        user.save()
        resp = client.get(reverse('view_profile'))
        self.assertRedirects(resp, "http://testserver/?next=/profile/view/")

    def test_inactive_user_sees_message(self):
        """
        A user with is_verified or is_active set to False should see an
        activation message instead of the content they were originally meaning
        to see.
        """
        client = TestClient(path=reverse('saved_search_main'))
        user = UserFactory()

        # Active user
        client.login_user(user)
        resp = client.get()
        self.assertIn('Saved Search', resp.content)

        # Inactive user
        user.is_verified= False
        user.save()
        resp = client.get()
        self.assertIn('unavailable', resp.content)

    def test_group_status(self):
        """
        Should return True if user.groups contains the group specified and
        False if it does not.
        """
        user = UserFactory()

        user.groups.all().delete()

        for group in Group.objects.all():
            # Makes a list of all group names, excluding the one that the
            # user will be a member of
            names = map(lambda group: group.name,
                        Group.objects.filter(~Q(name=group.name)))

            user.groups.add(group.pk)
            user.save()

            for name in names:
                self.assertFalse(User.objects.is_group_member(user, name))
            self.assertTrue(User.objects.is_group_member(user, group.name))

            user.groups.all().delete()

    def test_user_with_multiple_profileunits(self):
        """
        Confirms that the owner of an email is correctly being found.

        """
        user, _ = User.objects.create_user(**self.user_info)
        SecondaryEmail.objects.create(user=user, email='secondary@email.test')
        Telephone.objects.create(user=user)
        Name.objects.create(user=user, given_name="Test", family_name="Name")
        owner_user = User.objects.get_email_owner(user.email)
        self.assertEqual(owner_user.pk, user.pk)
        owner_user = User.objects.get_email_owner('secondary@email.test')
        self.assertEqual(owner_user.pk, user.pk)

    def test_deleting_user_does_not_cascade(self):
        """
        Deleting a user shouldn't delete related objects such as partner saved
        searches and reports.
        """

        user = UserFactory(email="test@test.com")
        company = CompanyFactory()
        pss = PartnerSavedSearchFactory(created_by=user)
        report = Report.objects.create(created_by=user, owner=company)

        user.delete()
        self.assertIn(pss, PartnerSavedSearch.objects.all())
        self.assertIn(report, Report.objects.all())
