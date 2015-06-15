import base64
from bs4 import BeautifulSoup
from datetime import timedelta, date
from importlib import import_module
import time
import uuid
from urllib import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.contrib.sessions.models import Session
from django.core import mail
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.test.client import Client, MULTIPART_CONTENT
from mymessages.models import Message
from mymessages.tests.factories import MessageInfoFactory

from setup import MyJobsBase
from myjobs.models import User, EmailLog, FAQ
from myjobs.tests.factories import UserFactory
from mypartners.tests.factories import PartnerFactory
from mysearches.models import PartnerSavedSearch
from seo.tests.factories import CompanyFactory
from myprofile.models import Name, Education
from mysearches.models import SavedSearch, SavedSearchLog
from registration.models import ActivationProfile
from registration import signals as custom_signals

from secrets import options, my_agent_auth
from jira.client import JIRA

from tasks import process_batch_events


class TestClient(Client):
    """
    Custom test client that decouples testing from the authentication bits, as
    well as reduces boilerplate when sending requests.
    """

    def __init__(self, enforce_csrf_checks=False, path=None,
                 data=None, **defaults):
        """
        In addition to Django's test client, this method also takes an optional
        path and data attribute to be used for get and post requests.
        """
        self.path = path
        self.data = data or {}
        super(TestClient, self).__init__(enforce_csrf_checks, **defaults)

    def get(self, path=None, data=None, follow=False, secure=False, **extra):
        """
        Like the builtin get method, but uses the instances path and data when
        available.
        """
        path = path or self.path
        data = data or self.data

        try:
            return super(TestClient, self).get(
                path, data=data, follow=follow, secure=secure, **extra)
        except TypeError:
            raise Exception("Calls to TestClient's methods require that "
                            "either path be passed explicit, or the "
                            "path be specified in the constructor")

    def post(self, path=None, data=None, content_type=MULTIPART_CONTENT,
             secure=False, **extra):
        path = path or self.path
        data = data or self.data

        try:
            return super(TestClient, self).post(
                path, data=data, content_type=content_type,
                secure=secure, **extra)
        except TypeError:
            raise Exception("Calls to TestClient's methods require that "
                            "either path be passed explicit, or the "
                            "path be specified in the constructor")

    def login_user(self, user):
        if 'django.contrib.sessions' not in settings.INSTALLED_APPS:
            raise AssertionError("Unable to login without "
                                 "django.contrib.sessions in INSTALLED_APPS")
        user.backend = "%s.%s" % ("django.contrib.auth.backends",
                                  "ModelBackend")
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()
        if self.session:
            request.session = self.session
        else:
            request.session = engine.SessionStore()
        login(request, user)

        # Set the cookie to represent the session.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE or None,
            'expires': None,
        }
        self.cookies[session_cookie].update(cookie_data)

        # Save the session values.
        request.session.save()


class MyJobsViewsTests(MyJobsBase):
    def setUp(self):
        super(MyJobsViewsTests, self).setUp()
        self.user = UserFactory()
        self.client = TestClient()
        self.client.login_user(self.user)
        self.events = ['open', 'delivered', 'click']

        self.email_user = UserFactory(email='accounts@my.jobs')

        self.auth = '%s:%s' % (settings.SENDGRID_BATCH_POST_USER,
                               settings.SENDGRID_BATCH_POST_PASSWORD)
        self.auth = base64.b64encode(self.auth)

    def make_messages(self, when, apiversion=2, categories=None):
        """
        Creates test api messages for sendgrid tests.

        Inputs:
        :self:  the calling object
        :when:  timestamp
        :apiversion: the version of the API to mimic
        :category: list of categories that the originating email was sent with;
            Optional

        Returns:
        JSON-esque object if apiversion<3
        JSON object is apiversion >=3

        """
        message = '{{"email":"alice@example.com","timestamp":"{0}",' \
            '"event":"{1}"{2}}}'
        messages = []
        category = ''
        if categories:
            categories = ['"%s"' % cat for cat in categories]
            if len(categories) > 1:
                category = ',"category":[%s]' % ','.join(categories)
            else:
                category = ',"category":%s' % categories[0]
        for event in self.events:
            messages.append(message.format(time.mktime(when.timetuple()),
                                           event, category))
        if apiversion < 3:
            return '\r\n'.join(messages)
        else:
            return_json = ','.join(messages)
            return '['+return_json+']'

    def test_change_password_success(self):
        resp = self.client.post(reverse('edit_account')+'?password',
                                data={'password': '5UuYquA@',
                                      'new_password1': '7dY=Ybtk',
                                      'new_password2': '7dY=Ybtk'},
                                follow=True)
        user = User.objects.get(id=self.user.id)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(user.check_password('7dY=Ybtk'))

    def test_change_password_failure(self):
        resp = self.client.post(reverse('edit_account')+'?password',
                                data={'password': '5UuYquA@',
                                      'new_password1': '7dY=Ybtk',
                                      'new_password2': 'notNew'}, follow=True)

        errors = {'new_password2': [u'The new password fields did not match.'],
                  'new_password1': [u'The new password fields did not match.']}

        response_errors = resp.context['password_form'].errors
        self.assertItemsEqual(response_errors, errors)

    def test_password_without_lowercase_failure(self):
        resp = self.client.post(reverse('edit_account')+'?password',
                                data={'password': '5UuYquA@',
                                      'new_password1': 'SECRET',
                                      'new_password2': 'SECRET'}, follow=True)

        errors = {'new_password1': [
            u'Invalid Length (Must be 8 characters or more)',
            u'Based on a common sequence of characters',
            u'Must be more complex (Must contain 1 or more lowercase '
            u'characters)']}

        response_errors = resp.context['password_form'].errors
        self.assertItemsEqual(response_errors, errors)

    def test_password_without_uppercase_failure(self):
        resp = self.client.post(reverse('edit_account')+'?password',
                                data={'password': '5UuYquA@',
                                      'new_password1': 'secret',
                                      'new_password2': 'secret'}, follow=True)

        errors = {'new_password1': [
            u'Invalid Length (Must be 8 characters or more)',
            u'Based on a common sequence of characters',
            u'Must be more complex (Must contain 1 or more uppercase '
            u'characers)']}

        response_errors = resp.context['password_form'].errors
        self.assertItemsEqual(response_errors, errors)

    def test_password_without_digit_failure(self):
        resp = self.client.post(reverse('edit_account')+'?password',
                                data={'password': '5UuYquA@',
                                      'new_password1': 'Secret',
                                      'new_password2': 'Secret'}, follow=True)

        errors = {'new_password1': [
            u'Invalid Length (Must be 8 characters or more)',
            u'Based on a common sequence of characters',
            u'Must be more complex (Must contain 1 or more digits)']}

        response_errors = resp.context['password_form'].errors
        self.assertItemsEqual(response_errors, errors)

    def test_password_without_punctuation_failure(self):
        resp = self.client.post(reverse('edit_account')+'?password',
                                data={'password': '5UuYquA@',
                                      'new_password1': 'S3cr37',
                                      'new_password2': 'S3cr37'}, follow=True)

        errors = {'new_password1': [
            u'Invalid Length (Must be 8 characters or more)',
            u'Based on a common sequence of characters',
            u'Must be more complex (Must contain 1 or more punctuation '
            u'character)']}

        response_errors = resp.context['password_form'].errors
        self.assertItemsEqual(response_errors, errors)

    def test_partial_successful_profile_form(self):
        resp = self.client.post(reverse('home'),
                                data={'name-given_name': 'Alice',
                                      'name-family_name': 'Smith',
                                      'name-primary': False,
                                      'action': 'save_profile'}, follow=True)
        self.assertEquals(resp.content, 'valid')

    def test_complete_successful_profile_form(self):
        # Form with only some sections completely filled out should
        # save successfully

        resp = self.client.post(
            reverse('home'),
            data={'name-given_name': 'Alice',
                  'name-family_name': 'Smith',
                  'edu-organization_name': 'Stanford University',
                  'edu-degree_date': '2012-01-01',
                  'edu-education_level_code': '6',
                  'edu-degree_major': 'Basket Weaving',
                  'work-position_title': 'Rocket Scientist',
                  'work-organization_name': 'Blamco Inc.',
                  'work-start_date': '2013-01-01',
                  'ph-use_code': 'Home',
                  'ph-area_dialing': '999',
                  'ph-number': '1234567',
                  'addr-address_line_one': '123 Easy St.',
                  'addr-city_name': 'Pleasantville',
                  'addr-country_sub_division_code': 'IN',
                  'addr-country_code': 'USA',
                  'addr-postal_code': '99999',
                  'action': 'save_profile'},
            follow=True)

        self.assertEquals(resp.content, 'valid')

    def test_incomplete_profile_form(self):
        # Form with incomplete sections should return a page with "This field
        # "is required" errors
        resp = self.client.post(reverse('home'),
                                data={'name-given_name': 'Alice',
                                      'action': 'save_profile'}, follow=True)

        self.failIf(resp.context['name_form'].is_valid())
        self.assertContains(resp, 'This field is required.')

    def test_no_profile_duplicates(self):
        # An initial registration form with errors should save those parts
        # that are valid.
        self.client.post(reverse('home'),
                         data={'name-given_name': 'Alice',
                               'name-family_name': 'Smith',
                               'name-primary': False,
                               'education-organization_name': 'U',
                               'action': 'save_profile'}, follow=True)

        self.assertEqual(Name.objects.count(), 1)
        self.assertEqual(Education.objects.count(), 0)
        self.client.post(reverse('home'),
                         data={'name-given_name': 'Alice',
                               'name-family_name': 'Smith',
                               'name-primary': False,
                               'edu-organization_name': 'U',
                               'edu-degree_date': '2012-01-01',
                               'edu-education_level_code': 6,
                               'edu-degree_major': 'Basket Weaving',
                               'action': 'save_profile'}, follow=True)
        self.assertEqual(Name.objects.count(), 1)
        self.assertEqual(Education.objects.count(), 1)

    def test_delete_account(self):
        """
        Going to the delete_account view removes a user and their data
        completely
        """
        self.assertEqual(User.objects.count(), 2)
        self.client.get(reverse('delete_account'), follow=True)
        self.assertEqual(User.objects.count(), 1)

    def test_disable_account(self):
        """
        Going to the disabled account view disables the account, meaning that
        (1) a new activation key is created, (2) User is set to not active and
        (3) User is set to disabled.
        """

        custom_signals.create_activation_profile(sender=self, user=self.user,
                                                 email=self.user.email)
        profile = ActivationProfile.objects.get(user=self.user)
        ActivationProfile.objects.activate_user(profile.activation_key)
        profile = ActivationProfile.objects.get(user=self.user)
        self.assertEqual(profile.activation_key, 'ALREADY ACTIVATED')

        self.client.get(reverse('disable_account'), follow=True)
        user = User.objects.get(id=self.user.id)
        profile = ActivationProfile.objects.get(user=user)
        self.assertNotEqual(profile.activation_key, 'ALREADY ACTIVATED')
        self.assertTrue(user.is_disabled)

    def test_about_template(self):
        # About page should return a status code of 200
        response = self.client.get(reverse('about'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_batch_recent_message_digest(self):
        """
        Posting data created recently should result in one EmailLog instance
        being created per message and no emails being sent

        This test is for sendgrid APIs prior to version 3.

        """

        # Create activation profile for user; Used when disabling an account
        custom_signals.create_activation_profile(sender=self,
                                                 user=self.user,
                                                 email=self.user.email)

        now = date.today()

        # Submit a batch of three events created recently
        messages = self.make_messages(now, 2)
        response = self.client.post(reverse('batch_message_digest'),
                                    data=messages,
                                    content_type="text/json",
                                    HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EmailLog.objects.count(), 3)
        process_batch_events()
        self.assertEqual(len(mail.outbox), 0)

        for log in EmailLog.objects.all():
            self.assertTrue(log.event in self.events)

    def test_batch_recent_message_digest_api_version_3(self):
        """
        Posting data created recently should result in one EmailLog instance
        being created per message and no emails being sent

        This test is for version 3 of the sendgrid API.

        """

        # Create activation profile for user; Used when disabling an account
        custom_signals.create_activation_profile(sender=self,
                                                 user=self.user,
                                                 email=self.user.email)

        now = date.today()

        # Submit a batch of three events created recently
        messages = self.make_messages(now, 3)
        response = self.client.post(reverse('batch_message_digest'),
                                    data=messages,
                                    content_type="text/json",
                                    HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EmailLog.objects.count(), 3)
        process_batch_events()
        self.assertEqual(len(mail.outbox), 0)

        for log in EmailLog.objects.all():
            self.assertTrue(log.event in self.events)

    def test_batch_with_one_event(self):
        """
        Version 1 and Version 2 posts that contain a single event are valid
        JSON and do not play well with our batch digest method.

        This tests both forms of post to ensure they work.
        """
        now = date.today()

        # make_messages makes len(self.events) messages. We only want one
        self.events = ['open']
        for api_ver in [2, 3]:
            messages = self.make_messages(now, api_ver)
            response = self.client.post(reverse('batch_message_digest'),
                                        data=messages,
                                        content_type='text/json',
                                        HTTP_AUTHORIZATION='BASIC %s' %
                                                           self.auth)
            self.assertEqual(response.status_code, 200)
        process_batch_events()
        self.assertEqual(EmailLog.objects.count(), 2)

    def test_batch_with_category(self):
        """
        When a batch submission contains categories, we should try to link the
        relevant events with a saved search log.
        """
        now = date.today()
        log_uuid = uuid.uuid4().hex
        SavedSearchLog.objects.create(was_sent=True, recipient=self.user,
                                      recipient_email=self.user.email,
                                      uuid=log_uuid, new_jobs=0,
                                      backfill_jobs=0)
        self.events = ['open']
        category = '(stuff|%s)' % log_uuid
        message = self.make_messages(now, 3, [category])
        self.client.post(reverse('batch_message_digest'),
                         data=message,
                         content_type='text/json',
                         HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertEqual(EmailLog.objects.count(), 1)
        email_log = EmailLog.objects.get()
        self.assertIn(log_uuid, email_log.category)
        saved_search_log = SavedSearchLog.objects.get()
        self.assertEqual(saved_search_log.uuid, log_uuid)
        # One saved search log can handle multiple sendgrid responses
        # (multiple bounces, clicks, opens, etc per email).
        self.assertTrue(email_log in saved_search_log.sendgrid_response.all())
        self.assertTrue(saved_search_log.was_received)

    def test_batch_with_multiple_categories(self):
        """
        Manually-sent saved search emails will contain multiple categories.
        Ensure nothing breaks horribly when multiple categories are used.
        If one of the categories is Production, remove it and continue
        processing (creating EmailLogs, etc). If one of the categories is QC,
        Staging, Jenkins, or Local, stop processing the event.
        """
        self.assertEqual(EmailLog.objects.count(), 0)
        now = date.today()
        categories = ["My.jobs Email", "Production"]
        message = self.make_messages(now, categories=categories)
        self.client.post(reverse('batch_message_digest'),
                         data=message,
                         content_type='text/json',
                         HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertEqual(EmailLog.objects.count(), 3)

        for category in ['QC', 'Staging', 'Jenkins', 'Local']:
            categories[1] = category
            message = self.make_messages(now, categories=categories)
            self.client.post(reverse('batch_message_digest'),
                             data=message,
                             content_type='text/json',
                             HTTP_AUTHORIZATION='BASIC %s' % self.auth)
            self.assertEqual(EmailLog.objects.count(), 3)

    def test_batch_bounce_message_digest(self):
        now = date.today()
        message = '[{{"email":"alice@example.com","timestamp":"{0}",' \
                  '"event":"bounce","category":"My.jobs email redirect",' \
                  '"status":418,"reason":"I\'m a teapot!",' \
                  '"type":"bounced"}}]'.format(
                      time.mktime(now.timetuple()))
        response = self.client.post(reverse('batch_message_digest'),
                                    data=message,
                                    content_type='text/json',
                                    HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox.pop()
        self.assertEqual(email.subject,
                         'My.jobs email redirect failure')
        self.assertEqual(email.from_email, self.user.email)
        self.assertEqual(email.to, [settings.EMAIL_TO_ADMIN])
        for text in ["I'm a teapot!", '418']:
            self.assertTrue(text in email.body)

    def test_batch_month_old_message_digest_with_searches(self):
        """
        Posting data created a month ago should result in one EmailLog instance
        being created per message and one email being sent per user

        """

        # Create activation profile for user; Used when disabling an account
        custom_signals.create_activation_profile(sender=self,
                                                 user=self.user,
                                                 email=self.user.email)

        week_before_expiration = date.today() - timedelta(days=172)
        self.user.last_response = week_before_expiration - timedelta(days=1)
        self.user.save()
        SavedSearch(user=self.user).save()

        # Submit a batch of events created a month ago
        # The owners of these addresses should be sent an email
        messages = self.make_messages(week_before_expiration)
        response = self.client.post(reverse('batch_message_digest'),
                                    data=messages,
                                    content_type="text/json",
                                    HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertTrue(response.status_code, 200)
        self.assertEqual(EmailLog.objects.count(), 3)
        self.assertEqual(
            EmailLog.objects.filter(
                received=week_before_expiration
            ).count(), 3
        )
        process_batch_events()
        self.assertEqual(len(mail.outbox), 1)

        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.last_response, week_before_expiration)

    def test_batch_month_old_message_digest_no_searches(self):
        """
        Posting data created a month ago should result in no emails being sent
        if the user has no saved searches
        """

        # Create activation profile for user
        custom_signals.create_activation_profile(sender=self,
                                                 user=self.user,
                                                 email=self.user.email)

        month_ago = date.today() - timedelta(days=30)
        self.user.last_response = month_ago - timedelta(days=1)
        self.user.save()

        messages = self.make_messages(month_ago)
        response = self.client.post(reverse('batch_message_digest'),
                                    data=messages,
                                    content_type="text/json",
                                    HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertTrue(response.status_code, 200)
        self.assertEqual(EmailLog.objects.count(), 3)
        self.assertEqual(
            EmailLog.objects.filter(
                received=month_ago
            ).count(), 3
        )
        process_batch_events()
        self.assertEqual(len(mail.outbox), 0)

    def test_batch_month_and_week_old_message_digest(self):
        """
        Posting data created a month and a week ago should result in one
        EmailLog instance being created per message, no emails being sent,
        and the user's opt-in status being set to False
        """

        # Create activation profile for user; Used when disabling an account
        custom_signals.create_activation_profile(sender=self,
                                                 user=self.user,
                                                 email=self.user.email)

        six_months_ago = date.today() - timedelta(days=180)
        self.user.last_response = six_months_ago - timedelta(days=1)
        self.user.save()

        # Submit a batch of events created a month and a week ago
        # The owners of these addresses should no longer receive email
        messages = self.make_messages(six_months_ago)
        response = self.client.post(reverse('batch_message_digest'),
                                    data=messages,
                                    content_type="text/json",
                                    HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertTrue(response.status_code, 200)
        self.assertEqual(EmailLog.objects.count(), 3)
        self.assertEqual(
            EmailLog.objects.filter(
                received__lte=(date.today() - timedelta(days=180))
            ).count(), 3
        )
        process_batch_events()
        self.assertEqual(len(mail.outbox), 0)

        user = User.objects.get(pk=self.user.pk)
        self.assertFalse(user.opt_in_myjobs)
        self.assertTrue(user.last_response, six_months_ago)

    def test_invalid_batch_post(self):
        response = self.client.post(reverse('batch_message_digest'),
                                    data='this is invalid',
                                    content_type="text/json",
                                    HTTP_AUTHORIZATION='BASIC %s' % self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EmailLog.objects.count(), 0)

    def test_invalid_user(self):
        now = date.today()
        messages = self.make_messages(now)

        response = self.client.post(reverse('batch_message_digest'),
                                    data=messages,
                                    content_type="text/json")
        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse('batch_message_digest'),
                                    data=messages,
                                    content_type="text/json",
                                    HTTP_AUTHORIZATION='BASIC %s' %
                                    base64.b64encode(
                                        'does%40not.exist:wrong_pass'))
        self.assertEqual(response.status_code, 403)

    def test_redirect_query_params(self):
        """
        If a user is redirected, the next parameter should not be missing query
        parameters.
        """
        # log out to force redirects
        self.client.post(reverse('auth_logout'))

        response = self.client.get(reverse('prm') + '?company=1')
        self.assertIn(urlencode({'next': '/prm/view?company=1'}),
                      response.get('Location'))

    def test_anonymous_continue_sending_mail(self):
        Session.objects.all().delete()
        self.user.last_response = date.today() - timedelta(days=7)
        self.user.save()

        # Navigating to the 'continue sending email' page while logged out...
        response = self.client.get(reverse('continue_sending_mail'))
        path = response.request.get('PATH_INFO')
        self.assertRedirects(response, reverse('home')+'?next='+path)

        # or with the wrong email address...
        response = self.client.get(reverse('continue_sending_mail') +
                                   '?verify=wrong@example.com')
        self.assertRedirects(response, reverse('home'))
        # should result in redirecting to the login page

        response = self.client.get(reverse('continue_sending_mail') +
                                   '?verify=%s' % self.user.user_guid)
        self.assertRedirects(response, reverse('home'))
        self.user = User.objects.get(pk=self.user.pk)
        self.assertEqual(self.user.last_response, date.today())

    def test_continue_sending_mail(self):
        self.user.last_response = date.today() - timedelta(days=7)
        self.user.save()

        response = self.client.get(reverse('continue_sending_mail'),
                                   data={'user': self.user}, follow=True)

        self.assertEqual(self.user.last_response,
                         date.today() - timedelta(days=7))
        self.assertRedirects(response, '/')
        self.user = User.objects.get(pk=self.user.pk)
        self.assertEqual(self.user.last_response, date.today())

    def test_redirect_autocreated_user(self):
        """
        When users are created with no password, their password_change
        flag is set to true; If this is the case, all pages except for
        a select few should redirect to the password change form
        """
        self.user.password_change = True
        self.user.save()
        self.user = User.objects.get(email=self.user.email)

        response = self.client.get(reverse('saved_search_main'))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('edit_account')+"#as-password")

        profile = ActivationProfile.objects.get_or_create(
            user=self.user,
            email=self.user.email)[0]
        response = self.client.get(reverse('registration_activate',
                                           args=[profile.activation_key]))

        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('edit_account')+'?password',
                                    data={'password': '5UuYquA@',
                                          'new_password1': '7dY=Ybtk',
                                          'new_password2': '7dY=Ybtk'})

        # When models are updated, instances still reference old data
        self.user = User.objects.get(email=self.user.email)
        self.assertFalse(self.user.password_change)

        response = self.client.get(reverse('saved_search_main'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mysearches/saved_search_main.html')

    def test_inactive_user_nav(self):
        """ Test that inactive users can't access restricted apps"""
        inactive_user = UserFactory(email='inactive@my.jobs', is_active=False)
        self.client.login_user(inactive_user)
        response = self.client.get("/")
        soup = BeautifulSoup(response.content)
        self.assertFalse(soup.findAll('a', {'id': 'savedsearch-link'}))

    def test_user_account_settings(self):
        """
        Test that the communication portion of account settings is not
        present for inactive users
        """
        def assert_communication_settings_presence(is_verified, contents):
            """
            If is_active is True, assert that div#as-communication exists
            Else, assert that it does not exist
            """
            communication_div = contents.find('div',
                                              {'id': 'as-communication'})
            if is_verified is True:
                self.assertTrue(communication_div)
            else:
                self.assertFalse(communication_div)

        unverified_user = UserFactory(email='inactive@my.jobs',
                                      is_verified=False)

        for user in [self.user, unverified_user]:
            self.client.login_user(user)
            response = self.client.get(reverse('edit_account'))
            soup = BeautifulSoup(response.content)

            assert_communication_settings_presence(user.is_verified, soup)

    def test_case_insensitive_login(self):
        """
        Test that emails are case-insensitive when logging in
        """
        for email in [self.user.email, self.user.email.upper()]:
            response = self.client.post(reverse('home'),
                                        data={'username': email,
                                              'password': '5UuYquA@',
                                              'action': 'login'})

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, '{"url": null,' +
                                               ' "units": false,' +
                                               ' "gravatar_url": "' +
                                               self.user.get_gravatar_url(
                                                   size=100)+'",' +
                                               ' "validation": "valid"}')

            self.client.get(reverse('auth_logout'))

    def test_guid_cookies_login_and_off(self):
        """
        Tests logging in and recieving a guid cookie. Logging out deletes guid
        cookie.
        """
        response = self.client.post(reverse('home'),
                                    data={'username': self.user.email,
                                          'password': '5UuYquA@',
                                          'action': 'login'})

        self.assertTrue(response.cookies['myguid'])
        cookie_guid = response.cookies['myguid']
        guid = cookie_guid.value
        self.assertEqual(guid, self.user.user_guid)

        resp_logoff = self.client.post(reverse('auth_logout'))
        cookie_guid_off = resp_logoff.cookies['myguid']
        guid_off = cookie_guid_off.value
        self.assertEqual(guid_off, '')

    def test_jira_login(self):
        jira = JIRA(options=options, basic_auth=my_agent_auth)
        self.assertIsNotNone(jira)

    def test_anonymous_unsubscribe_all_myjobs_emails(self):
        Session.objects.all().delete()
        self.assertTrue(self.user.opt_in_myjobs)

        # Navigating to the unsubscribe page while logged out...
        response = self.client.get(reverse('unsubscribe_all'))
        path = response.request.get('PATH_INFO')
        self.assertRedirects(response, reverse('home')+'?next='+path)
        # or with the wrong email address...
        response = self.client.get(reverse('unsubscribe_all') +
                                   '?verify=wrong@example.com')
        # should result in the user's status remaining unchanged
        # and the user should be redirected to the login page
        self.assertRedirects(response, reverse('home'))
        self.user = User.objects.get(id=self.user.id)
        self.assertTrue(self.user.opt_in_myjobs)

        # Navigating to the unsubscribe page while logged out
        # and with the correct email address...
        self.client.get(reverse('unsubscribe_all') +
                        '?verify=%s' % self.user.user_guid)
        self.user = User.objects.get(id=self.user.id)
        # should result in the user's :opt_in_myjobs: attribute being
        # set to False
        self.assertFalse(self.user.opt_in_myjobs)

    def test_unsubscribe_all_myjobs_emails(self):
        self.assertTrue(self.user.opt_in_myjobs)

        self.client.get(reverse('unsubscribe_all'))
        self.user = User.objects.get(id=self.user.id)
        self.assertFalse(self.user.opt_in_myjobs)

    def test_opt_out_sends_notifications(self):
        """
        When a user creates a saved search for another user and that user opts
        out of My.jobs communications, the creator should get a My.jobs message
        and email notifying them of the opt-out.
        """

        # required fields for saved search
        company = CompanyFactory()
        partner = PartnerFactory(owner=company)

        creator = UserFactory(id=3, email='normal@user.com')

        # should not have any messages
        self.assertFalse(creator.message_set.all())

        PartnerSavedSearch.objects.create(user=self.user, provider=company,
                                          created_by=creator,
                                          partner=partner)

        # simulate a user opting out
        self.user.opt_in_myjobs = False
        self.user.save()

        self.client.get(reverse('unsubscribe_all'))

        # creator should have a My.jobs message and email
        for body in [creator.message_set.first().body,
                     mail.outbox[0].body]: 
            self.assertIn(self.user.email, body)
            self.assertIn('unsubscribed from one or more saved search emails',
                          body)

        # email should be sent to right person
        self.assertIn(creator.email, mail.outbox[0].to)

    def test_unsubscribe_sends_notifications(self):
        """
        When a user unsubscribes from one or more saved searches, the user who
        created the saved search should recieve an email and notification.
        """

        # required fields for saved search
        company = CompanyFactory()
        partner = PartnerFactory(owner=company)

        creator = UserFactory(id=3, email='normal@user.com')

        # should not have any messages
        self.assertFalse(creator.message_set.all())

        PartnerSavedSearch.objects.create(user=self.user, provider=company,
                                          created_by=creator,
                                          partner=partner)

        self.client.get(reverse('unsubscribe_all'))

        # creator should have a My.jobs message and email
        for body in [creator.message_set.first().body,
                     mail.outbox[0].body]: 
            self.assertIn(self.user.email, body)
            self.assertIn('unsubscribed from one or more saved search emails',
                          body)

        # email should be sent to right person
        self.assertIn(creator.email, mail.outbox[0].to)

    def test_toolbar_logged_in(self):
        self.client.login_user(self.user)
        response = self.client.get(reverse('toolbar'))
        expected_response = '"user_fullname": "alice@example.com"'
        self.assertIn(expected_response, response.content)

    def test_toolbar_not_logged_in(self):
        Session.objects.all().delete()
        response = self.client.get(reverse('toolbar'))
        expected_response = '({"user_fullname": "", "user_gravatar": '\
                            '"", "employer": ""});'
        self.assertEqual(response.content, expected_response)

    def test_p3p(self):
        """
        make sure the P3P headers are being set

        """
        self.client.login_user(self.user)
        response = self.client.get(reverse('toolbar'))
        p3p = str(response["P3P"])
        self.assertEqual('CP="ALL' in p3p, True)

    def test_topbar_with_invalid_session(self):
        response = self.client.get(
            reverse('topbar'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # ensure topbar shows logged in options
        self.assertIn(self.user.email, response.content)

        Session.objects.all().delete()
        response = self.client.get(
            reverse('topbar'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # ensure topbar shows logged out options
        self.assertIn("Login", response.content)

    def test_referring_site_in_topbar(self):
        self.client.get(
            reverse('toolbar') + '?site_name=Indianapolis%20Jobs&site=http%3A'
                                 '%2F%2Findianapolis.jobs&callback=foo',
            HTTP_REFERER='http://indianapolis.jobs')

        last_site = self.client.cookies.get('lastmicrosite').value
        last_name = self.client.cookies.get('lastmicrositename').value

        response = self.client.get(reverse('home'))
        self.assertIn(last_site, response.content)
        self.assertIn(last_name, response.content)

    def test_messages_in_topbar(self):
        self.client.login_user(self.user)
        for num_messages in range(1, 5):
            # The indicator in the topbar will display a max of three messages.
            # Test that the correct number of messages is displayed for all
            # possible counts.
            infos = MessageInfoFactory.create_batch(size=num_messages,
                                                    user=self.user)
            # Mark the first message as read to show that read messages are
            # not shown.
            infos[0].mark_read()

            response = self.client.get(reverse('home'))
            self.assertTrue('id="menu-inbox">%s<' % (num_messages-1, )
                            in response.content)
            if num_messages == 1:
                # The only message has been read in this instance; it should
                # not have been displayed.
                self.assertTrue('No new unread messages' in response.content,
                                'Iteration %s' % num_messages)
            for info in infos[1:4]:
                # Ensure that the 1-3 messages we expect are appearing on
                # the page.
                self.assertTrue('message=%s' % info.message.pk
                                in response.content,
                                'Iteration %s, %s not found' % (
                                    num_messages,
                                    'message=%s' % info.message.pk))
            for info in infos[4:]:
                # Ensure that any additional unread messages beyond 3 are not
                # displayed.
                self.assertFalse('message=%s' % info.message.pk
                                 in response.content,
                                 "Iteration %s, %s exists but shouldn't" % (
                                     num_messages,
                                     'message=%s' % info.message.pk))
            Message.objects.all().delete()

    def test_cas_logged_in(self):
        response = self.client.get(reverse('cas'), follow=True)
        self.assertEqual(response.redirect_chain[-1][0].split("?")[0],
                         'http://www.my.jobs/')

    def test_cas_not_logged_in(self):
        self.client.post(reverse('auth_logout'))
        response = self.client.get(reverse('cas'), follow=True)
        self.assertEqual(response.redirect_chain[-1][0],
                         'https://secure.my.jobs/?next=http://www.my.jobs/')

    def test_user_creation_source(self):
        """
        User.source should be set to the last microsite a new user visited,
        an explicity defined source, the current site, or
        https://secure.my.jobs.
        """
        self.client.post(reverse('home'),
                         {'action': 'register',
                          'email': 'default@example.com',
                          'password1': '5UuYquA@',
                          'password2': '5UuYquA@'})
        user = User.objects.get(email='default@example.com')
        # settings.SITE.domain == jobs.directemployers.org.
        self.assertEqual(user.source, 'jobs.directemployers.org')

        self.client.get(
            reverse('toolbar') + '?site_name=Indianapolis%20Jobs&site=http'
                                 '%3A%2F%2Findianapolis.jobs&callback=foo',
            HTTP_REFERER='http://indianapolis.jobs')

        last_site = self.client.cookies.get('lastmicrosite').value
        self.assertEqual(last_site, 'http://indianapolis.jobs')

        self.client.post(reverse('home'),
                         {'action': 'register',
                          'email': 'microsite@example.com',
                          'password1': '5UuYquA@',
                          'password2': '5UuYquA@'})

        user = User.objects.get(email='microsite@example.com')
        self.assertEqual(user.source, last_site)

    def test_contact_FAQ(self):
        """
        Tests the redirect feature when no FAQ is created or visible.
        Then creates FAQ and checks to make sure it does show.

        """
        response = self.client.post(reverse('contact_faq'))
        # checks redirect
        self.assertEqual(response.status_code, 302)

        faq = FAQ(question="1101", answer="13")
        faq.save()

        response = self.client.post(reverse('contact_faq'))
        self.assertEqual(response.status_code, 200)

        faq.is_visible = False
        faq.save()

        response = self.client.post(reverse('contact_faq'))
        # checks redirect
        self.assertEqual(response.status_code, 302)

    def test_changing_title_content(self):
        """
        Tests that the title logo on the login page changes based on url.

        """
        self.client.logout()
        response = self.client.get(reverse('home'))
        content = BeautifulSoup(response.content)
        title = content.select('div#title')[0]
        self.assertTrue('The Right Place for' in title.text)

        response = self.client.get(reverse('home') + '?next=/prm/view/')
        content = BeautifulSoup(response.content)
        title = content.select('div#title')[0]
        self.assertTrue('The new OFCCP regulations' in title.text)

    def test_manual_account_creation(self):
        self.client.logout()
        self.assertEqual(len(mail.outbox), 0)
        self.client.post(reverse('home'), data={'email': 'new@example.com',
                                                'password1': '5UuYquA@',
                                                'password2': '5UuYquA@',
                                                'action': 'register'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         'Account Activation for my.jobs')
