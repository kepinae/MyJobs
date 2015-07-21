import datetime
import hashlib
import string
import urllib
import uuid
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver

import pytz

from django.utils.safestring import mark_safe
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        Group, PermissionsMixin)
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.importlib import import_module
from django.utils.translation import ugettext_lazy as _

from default_settings import GRAVATAR_URL_PREFIX, GRAVATAR_URL_DEFAULT
from registration import signals as custom_signals
from mymessages.models import Message, MessageInfo
from universal.helpers import get_domain, send_email

BAD_EMAIL = ['dropped', 'bounce']
STOP_SENDING = ['unsubscribe', 'spamreport']
DEACTIVE_TYPES_AND_NONE = ['none'] + BAD_EMAIL + STOP_SENDING


class CustomUserManager(BaseUserManager):
    # Characters used for passwor generation with ambiguous ones ignored.
    # string.strip() doesn't play nicely with quote characters...
    ALLOWED_CHARS = string.printable.translate(
        None, """iloILO01!<>{}()[]|^"'`,.:;~-_/\\\t\n\r\x0b\x0c """)

    def get_email_owner(self, email):
        """
        Tests if the specified email is already in use.

        Inputs:
        :email: String representation of email to be checked

        Outputs:
        :user: User object if one exists; None otherwise
        """
        try:
            user = self.get(email__iexact=email)
        except User.DoesNotExist:
            try:
                user = self.get(
                    profileunits__secondaryemail__email__iexact=email)
            except User.DoesNotExist:
                user = None
        return user

    def make_random_password(self, length=8, allowed_chars=None):
        """
        Like django's built-in `make_random_password`, but with a default of
        8 characters, a larger character set, and validation.
        """
        password = ''
        allowed_chars = allowed_chars or self.ALLOWED_CHARS
        # continue to generate a new password until all constriants are met
        while not all(set(password).intersection(getattr(string, category))
                      for category in ['ascii_lowercase', 'ascii_uppercase',
                                       'digits', 'punctuation']):
            password = super(CustomUserManager, self).make_random_password(
                length=length, allowed_chars=allowed_chars)

        return password

    def create_user_by_type(self, **kwargs):
        """
        Creates users by user type (normal or superuser). If a user
        already exists

        Inputs (all kwargs):
        :email: Email for this account; required
        :send_email: Boolean defaulted to true to signal that an email needs to
            be sent
        :request: HttpRequest instance used to pull cookies related to creation
            source
        :user_type: String, must be either normal or superuser
        Additionally accepts values for all fields on the User model

        Outputs:
        :user: User object instance
        :created: Boolean indicating whether a new user was created
        """
        email = kwargs.get('email')
        if not email:
            raise ValueError('Email address required.')

        user_type = kwargs.get('user_type', 'normal')
        if user_type not in ['superuser', 'normal']:
            raise ValueError('Bad user_type: %s' % user_type)

        user = self.get_email_owner(email)
        created = False
        if user is None:
            email = self.normalize_email(email)
            user_args = {'email': email,
                         'gravatar': '',
                         'timezone': settings.TIME_ZONE,
                         'is_active': True,
                         'in_reserve': kwargs.get('in_reserve', False)
                         }

            if user_type == 'superuser':
                user_args.update({'is_staff': True, 'is_superuser': True})
            password_fields = ['password', 'password1']
            for password_field in password_fields:
                password = kwargs.get(password_field)
                if password:
                    break
            create_password = False
            if not password:
                create_password = True
                user_args['password_change'] = True
                password = self.make_random_password()

            kwarg_source = kwargs.get('source')
            request = kwargs.get('request')
            if request:
                last_microsite_source = request.COOKIES.get('lastmicrosite')
                request_source = request.GET.get('source')
            else:
                last_microsite_source = None
                request_source = None

            if kwarg_source:
                user_args['source'] = kwarg_source
            elif request_source:
                user_args['source'] = request_source
            elif last_microsite_source:
                user_args['source'] = last_microsite_source
            elif hasattr(settings, 'SITE') and settings.SITE:
                user_args['source'] = settings.SITE.domain

            user = self.model(**user_args)
            user.set_password(password)
            user.make_guid()
            user.full_clean()
            user.save()
            user.add_default_group()
            custom_signals.email_created.send(sender=self, user=user,
                                              email=email)
            send_email = kwargs.get('send_email', False)
            if send_email:
                custom_msg = kwargs.get("custom_msg", None)
                activation_args = {
                    'sender': self,
                    'user': user,
                    'email': email,
                    'custom_msg': custom_msg,
                }
                if create_password:
                    activation_args['password'] = password
                custom_signals.send_activation.send(**activation_args)

            created = True
        return user, created

    def create_user(self, **kwargs):
        """
        Creates an already activated user.

        """
        return self.create_user_by_type(user_type='normal', **kwargs)

    def create_superuser(self, **kwargs):
        user, _ = self.create_user_by_type(user_type='superuser', **kwargs)
        return user

    def not_disabled(self, user):
        """
        Used by the user_passes_test decorator to set view permissions.
        The user_passes_test method, passes in the user from the request,
        and gives permission to access the view if the value returned is true.
        This returns true as long as the user hasn't disabled their account.
        """

        if user.is_anonymous():
            return False
        else:
            return not user.is_disabled

    def is_verified(self, user):
        """
        Used by the user_passes_test decorator to set view permissions
        """

        if user.is_anonymous():
            return False
        else:
            return user.is_verified

    def is_group_member(self, user, group):
        """
        Used by the user_passes_test decorator to determine if the user's group
        membership is adequate for certain actions

        Example usage:
        Determine if user is in the 'Job Seeker' group:
        @user_passes_test(lambda u: User.objects.is_group_member(u, 'Job Seeker'))

        Inputs:
        :user: User instance, passed by the user_passes_test decorator
        :group: Name of the group that is being tested for

        Outputs:
        :is_member: Boolean representing the user's membership status
        """
        return user.groups.filter(name=group).count() >= 1


# New in Django 1.5. This is now the default auth user table.
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name=_("email address"),
                              max_length=255, unique=True, db_index=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    gravatar = models.EmailField(verbose_name=_("gravatar email"),
                                 max_length=255, db_index=True, blank=True)

    profile_completion = models.IntegerField(validators=[MaxValueValidator(100),
                                                         MinValueValidator(0)],
                                             blank=False, default=0)

    # Permission Levels
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_("Designates whether the user "
                                               "can log into this admin site."))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_("Designates whether this "
                                                "corresponds to a valid"
                                                "email address. Deselect this"
                                                "instead of deleting "
                                                "accounts."))
    is_disabled = models.BooleanField(_('disabled'), default=False)
    is_verified = models.BooleanField(_('verified'),
                                      default=False,
                                      help_text=_("User has verified this "
                                                  "address and can access "
                                                  "most My.jobs features. "
                                                  "Deselect this instead of "
                                                  "deleting accounts."))
    in_reserve = models.BooleanField(_('reserved'), default=False,
                                     editable=False,
                                     help_text=_("This user will be held in "
                                                 "reserve until any "
                                                 "invitations associated "
                                                 "with it are processed."))

    # Communication Settings

    # opt_in_myjobs is current hidden on the top level, refer to forms.py
    opt_in_myjobs = models.BooleanField(_('Opt-in to non-account emails and '
                                          'Saved Search'),
                                        default=True,
                                        help_text=_('Checking this allows '
                                                    'My.jobs to send email '
                                                    'updates to you.'))

    opt_in_employers = models.BooleanField(_('Email is visible to Employers'),
                                           default=True,
                                           help_text=_('Checking this allows '
                                                       'employers to send '
                                                       'emails to you.'))

    last_response = models.DateField(default=datetime.datetime.now, blank=True)

    # Password Settings
    password_change = models.BooleanField(_('Password must be changed on next '
                                            'login'), default=False)

    user_guid = models.CharField(max_length=100, db_index=True, unique=True)

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=255, default=settings.TIME_ZONE)

    source = models.CharField(max_length=255,
                              default='https://secure.my.jobs',
                              help_text=_('Site that initiated account '
                                          'creation'))
    deactivate_type = models.CharField(max_length=11,
                                       choices=zip(DEACTIVE_TYPES_AND_NONE,
                                                   DEACTIVE_TYPES_AND_NONE),
                                       blank=False,
                                       default=DEACTIVE_TYPES_AND_NONE[0])

    USERNAME_FIELD = 'email'
    objects = CustomUserManager()

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        # Get a copy of the original password so we can determine if
        # it has changed in the save().
        self.__original_password = getattr(self, 'password', None)
        self.__original_opt_in_myjobs = self.opt_in_myjobs

    def __unicode__(self):
        return self.email

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # TODO: Fix PartnerSavedSearch-User relationship.
        # Then self.partnersavedsearch_set will work properly.
        # Importing locally otherwise circular imports.
        from mysearches.models import PartnerSavedSearch

        if (self.__original_opt_in_myjobs != self.opt_in_myjobs
                and not self.opt_in_myjobs):
            PartnerSavedSearch.objects.filter(user=self).update(
                unsubscribed=True)
            self.send_opt_out_notifications()
        elif (self.__original_opt_in_myjobs != self.opt_in_myjobs
                and self.opt_in_myjobs):
            PartnerSavedSearch.objects.filter(
                user=self, is_active=True).update(unsubscribed=False)

        # If the password has changed, it's not being set for the first time
        # and it wasn't change to a blank string, don't require them to change
        # their password again.
        if ((self.password != self.__original_password)
                and self.__original_password and (self.password != '')):
            self.password_change = False

        if update_fields is not None and 'is_active' in update_fields:
            if self.is_active:
                self.deactivate_type = DEACTIVE_TYPES_AND_NONE[0]
                if 'deactivate_type' not in update_fields:
                    update_fields.append('deactivate_type')
        super(User, self).save(force_insert, force_update, using,
                               update_fields)

    def email_user(self, message, email_type=settings.GENERIC, **kwargs):
        headers = kwargs.pop('headers', {})
        if 'X-SMTPAPI' not in headers:
            headers['X-SMTPAPI'] = '{"category": "Email to User (%s)"}' % self.pk
        send_email(message, email_type=email_type, recipients=[self.email],
                   headers=headers, **kwargs)

    def get_username(self):
        return self.email

    def get_short_name(self):
        return self.email

    def get_gravatar_url(self, size=20):
        """
        Gets the container for the gravatar/initials block.

        inputs:
        :self: A user.
        :size: The height and width the resulting block should be.

        outputs:
        :gravatar_url: Either an image tag with a src = to a valid gravatar, or
                       a div tag for the initials block.
        """

        gravatar_url = GRAVATAR_URL_PREFIX + \
            hashlib.md5(self.gravatar.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d': GRAVATAR_URL_DEFAULT,
                                          's': str(size)})

        if urllib.urlopen(gravatar_url).getcode() == 404:
            # Determine background color for initials block based on the
            # same formula used for profile completion bars.
            from helpers import get_completion

            color = get_completion(self.profile_completion)

            try:
                text = self.profileunits_set.get(content_type__name="name",
                                                 name__primary=True).name
                if not text.given_name and not text.family_name:
                    text = self.email[0]
                else:
                    text = "%s%s" % (text.given_name[0], text.family_name[0])
            except ObjectDoesNotExist:
                text = self.email[0]

            font_size = int(size)
            font_size *= .65
            gravatar_url = mark_safe(
                "<div class='gravatar-blank gravatar-%s' style='height: %spx; "
                "width: %spx'><span class='gravatar-text' style='font-size:"
                "%spx;'>%s</span></div>" % (color, size, size,
                                            font_size, text.upper()))
        else:
            gravatar_url = mark_safe("<img src='%s' id='id_gravatar'>"
                                     % gravatar_url)

        return gravatar_url

    def get_companies(self):
        """
        Returns a QuerySet of all the Companies a User has access to.

        """
        from seo.models import Company
        return Company.objects.filter(admins=self).distinct()

    def get_sites(self):
        """
        Returns a QuerySet of all the SeoSites a User has access to.

        """
        from seo.models import SeoSite
        kwargs = {'business_units__company__admins': self}
        return SeoSite.objects.filter(**kwargs).distinct()

    def disable(self):
        self.is_disabled = True
        self.save()

        custom_signals.user_disabled.send(sender=self, user=self,
                                          email=self.email)

    def update_profile_completion(self):
        """
        Updates the percent of modules in
        settings.PROFILE_COMPLETION_MODULES that a user has completed.
        """
        profile_dict = self.profileunits_set.all()
        num_complete = len(list(set([unit.get_model_name() for unit
                           in profile_dict if unit.get_model_name()
                           in settings.PROFILE_COMPLETION_MODULES])))
        self.profile_completion = int(float(
            1.0 * num_complete / len(settings.PROFILE_COMPLETION_MODULES))*100)
        self.save()

    def add_default_group(self):
        group, _ = Group.objects.get_or_create(name='Job Seeker')
        self.groups.add(group.pk)

    def make_guid(self):
        """
        Creates a uuid for the User only if the User does not currently has
        a user_guid.  After the uuid is made it is checked to make sure there
        are no duplicates. If no duplicates, save the GUID.
        """
        if not self.user_guid:
            guid = uuid.uuid4().hex
            if User.objects.filter(user_guid=guid):
                self.make_guid()
            else:
                self.user_guid = guid

    def get_messages(self):
        """
        Gathers Messages based on user, user's groups and if message has
        started and is not expired.

        Outputs:
        :active_messages:   A list of messages that starts before the current
                            time and expires after the current time. 'active'
                            messages.
        """
        now = timezone.now().date()
        messages = Message.objects.prefetch_related('messageinfo_set').filter(
            Q(group__in=self.groups.all()) | Q(users=self),
            Q(expire_at__isnull=True) | Q(expire_at__gte=now),
            Q(messageinfo__deleted_on__isnull=True)).distinct()

        return messages

    def claim_messages(self):
        """
        Create MessageInfos for group-based messages that this user hasn't
        seen yet.
        """
        if not self.pk:
            return
        messages = self.get_messages().exclude(users=self)

        with transaction.atomic():
            for message in messages:
                MessageInfo.objects.get_or_create(
                    user=self, message=message)

    def get_full_name(self, default=""):
        """
        Returns the user's full name based off of first_name and last_name
        from the user model.

        Inputs:
        :default:   Can add a default if the user doesn't have a first_name
                    or last_name.
        """
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        else:
            return default

    def add_primary_name(self, update=False, f_name="", l_name=""):
        """
        Primary function that adds the primary user's ProfileUnit.Name object
        first and last name to the user model, if Name object exists.

        Inputs:
        :update:    Update is a flag that should be used to determine if to use
                    this function as an update (must provide f_name and l_name
                    if that is the case) or if the function needs to be called
                    to set the user's first_name and last_name in the model.

        :f_name:    If the update flag is set to true this needs to have the
                    given_name value from the updating Name object.

        :l_name:    If the update flag is set to true this needs to have the
                    family_name value from the updating Name object.
        """
        if update and f_name != '' and l_name != '':
            self.first_name = f_name
            self.last_name = l_name
            self.save()
            return

        try:
            name_obj = self.profileunits_set.filter(
                content_type__name="name").get(name__primary=True)
        except ObjectDoesNotExist:
            name_obj = None

        if name_obj:
            self.first_name = name_obj.name.given_name
            self.last_name = name_obj.name.family_name
            self.save()
        else:
            self.first_name = ""
            self.last_name = ""
            self.save()

    def get_expiration(self):
        """
        Returns expiration date for this user's activation profile

        Outputs:
        :delta: Time delta between now and activation profile expiration;
            Negative delta is in the past, positive is in the future
        """
        if self.is_active:
            return None
        else:
            profile, _ = self.activationprofile_set.get_or_create(
                email=self.email)
            now = datetime.datetime.now(tz=pytz.UTC)
            return profile.expires() - now

    def can_receive_myjobs_email(self):
        """
        Determines if this user can receive My.jobs email
        """
        if self.opt_in_myjobs and not self.is_disabled:
            return True
        return False

    def send_opt_out_notifications(self, saved_searches=None):
        """
        Notify saved search creators that a user has opted out of their emails.
        """
        from mysearches.models import PartnerSavedSearch

        subject = "My.jobs Partner Saved Search Update"

        saved_searches = saved_searches or PartnerSavedSearch.objects.filter(
            user=self)

        # MySQL doesn't support passing a column to distinct, and I don't want
        # to deal with dictionaries returned by `values()`, so I just keep
        # track of unique contacts manually.
        contacts = []
        # need the partner name, so can't send a batch email or message
        for pss in saved_searches:
            if (pss.email, pss.partner) in contacts:
                continue

            contacts.append((pss.email, pss.partner))

            # send notification email
            message = render_to_string(
                "mysearches/email_opt_out.html",
                {'user': self,
                 'partner': pss.partner,
                 'company': pss.provider})

            headers = {
                'X-SMTPAPI': '{"category": "Partner Saved Search Opt Out '
                             '(%s:%s)"}' % (pss.pk, pss.created_by.pk)
            }

            email_type = settings.PARTNER_SAVED_SEARCH_RECIPIENT_OPTED_OUT
            send_email(message,  email_type=email_type,
                       recipients=[pss.created_by.email], headers=headers)

            # create PRM message
            body = render_to_string(
                "mysearches/email_opt_out_message.html",
                {'user': self,
                 'partner': pss.partner,
                 'company': pss.provider})
            Message.objects.create_message(
                subject, body, users=[pss.created_by])

    def registration_source(self):
        from seo.models import SeoSite

        domain = get_domain(self.source)
        # Use __iendswith because we strip subdomains in get_domain but
        # the subdomain will still be present in SeoSite.domain.
        try:
            return SeoSite.objects.filter(domain__iendswith=domain)[0]
        except (IndexError, ValueError):
            return None

    def can_access_site(self, site):
        """
        If a user belongs to a company who has at least one site package which
        includes `site`, this method will return `True`. This method will also
        return `True` if the site has no site packages.

        Inputs:
        :site: The site to look for
        """
        packages = site.sitepackage_set

        return not packages.exists() or packages.filter(
            owner__in=self.company_set.all()).exists()


@receiver(pre_delete, sender=User, dispatch_uid='pre_delete_user')
def delete_user(sender, instance, using, **kwargs):
    """
    Fakes a combination of SET_NULL and CASCADE on_delete handlers. The user's
    saved searches will be deleted and partner saved searches will have the
    user nullified.
    """
    from mysearches.models import PartnerSavedSearch
    instance.send_opt_out_notifications()
    PartnerSavedSearch.objects.filter(user=instance).update(
        user=None, is_active=False, unsubscribed=True,
        unsubscriber=instance.email)
    instance.savedsearch_set.filter(partnersavedsearch__isnull=True).delete()


class EmailLog(models.Model):
    email = models.EmailField(max_length=254)
    event = models.CharField(max_length=11)
    received = models.DateField()
    processed = models.BooleanField(default=False, blank=True)
    category = models.CharField(max_length=255, blank=True)
    send_log = models.ForeignKey('mysearches.SavedSearchLog', null=True,
                                 blank=True, on_delete=models.SET_NULL,
                                 help_text="""Entries prior to the
                                 release of saved search logging will
                                 have no categories, meaning we cannot
                                 match them with a SendGrid
                                 response.""",
                                 related_name='sendgrid_response')
    # The event api reference makes no mention about how long this can be.
    reason = models.TextField(blank=True)


class CustomHomepage(Site):
    logo_url = models.URLField('Logo Image URL', max_length=200, null=True,
                               blank=True)
    show_signup_form = models.BooleanField(default=True)


class Ticket(models.Model):
    class Meta:
        unique_together = ['ticket', 'user']

    ticket = models.CharField(max_length=255)
    user = models.ForeignKey('User')


class Shared_Sessions(models.Model):
    # session is a comma separated list stored as a string of session keys
    session = models.TextField(blank=True)
    user = models.ForeignKey('User', unique=True)


def save_related_session(sender, user, request, **kwargs):
    if user and user.is_authenticated():
        session, _ = Shared_Sessions.objects.get_or_create(user=user)
        current = session.session.split(",") if session.session else []
        try:
            current.append(request.session.session_key)
            session.session = ",".join(current)
        except:
            pass
        session.save()


def delete_related_session(sender, user, request, **kwargs):
    """
    Deletes all microsites sessions for user on logout.

    """

    if user and user.is_authenticated():
        try:
            sessions = Shared_Sessions.objects.get(user=user)
        except Shared_Sessions.DoesNotExist:
            return

        session_keys = sessions.session.split(",") if \
            sessions.session else []
        engine = import_module(settings.SESSION_ENGINE)
        for key in session_keys:
            try:
                s = engine.SessionStore(key)
                s.delete()
            except:
                pass
        sessions.delete()

user_logged_in.connect(save_related_session)
user_logged_out.connect(delete_related_session)


class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name='Question')
    answer = models.TextField(verbose_name='Answer',
                              help_text='Answers allow use of HTML')
    is_visible = models.BooleanField(default=True, verbose_name='Is visible')
