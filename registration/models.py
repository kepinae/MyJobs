import datetime
import hashlib
import random
import re
from django.core.exceptions import ValidationError

from pynliner import Pynliner

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now as datetime_now
from django.utils.translation import ugettext_lazy as _

from universal.helpers import send_email


SHA1_RE = re.compile('^[a-f0-9]{40}$')


class RegistrationManager(models.Manager):
    def activate_user(self, activation_key):
        """
        Searches for activation key in the database. If the key is found and
        not expired,

        Outputs:
        A boolean True and sets the key to 'ALREADY ACTIVATED'.
        Otherwise, returns False to signify the activation failed.

        """
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False

            user = profile.user
            if not user.is_disabled and profile.activation_key_expired():
                return False
            else:
                from myprofile import signals
                signals.activated.send(sender=self, user=user,
                                       email=profile.email)
                profile.activation_key = self.model.ACTIVATED
                profile.save()
                Invitation.objects.filter(invitee=user,
                                          accepted=False).update(accepted=True)
                return user
        return False

    def delete_expired_users(self):
        for profile in self.all():
            try:
                if profile.activation_key_expired():
                    user = profile.user

                    if not user.is_disabled and not user.is_verified:
                        user.delete()
                        profile.delete()
            except DoesNotExist:
                profile.delete()


class ActivationProfile(models.Model):
    user = models.ForeignKey('myjobs.User', verbose_name="user")
    activation_key = models.CharField(_('activation_key'), max_length=40)
    email = models.EmailField(max_length=255)
    sent = models.DateTimeField(auto_now_add=True)

    ACTIVATED = "ALREADY ACTIVATED"
    objects = RegistrationManager()

    def __unicode__(self):
        return "Registration for %s" % self.user

    def activation_key_expired(self):
        expiration_date = datetime.timedelta(
            days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or \
            (self.sent + expiration_date <= datetime_now())

    def generate_key(self):
        """
        Generates a random string that will be used as the activation key for a
        registered user.
        """

        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        email = self.email
        if isinstance(email, unicode):
            email = email.encode('utf-8')
        activation_key = hashlib.sha1(salt + email).hexdigest()
        return activation_key

    def reset_activation(self):
        """
        Used to reset activation key when user is disabled.
        """
        self.activation_key = self.generate_key()
        self.sent = datetime_now()
        self.save()

    def send_activation_email(self, primary=True, password=None,
                              custom_msg=None):
        if self.activation_key_expired():
            self.reset_activation()
        if custom_msg:
            custom_msg = custom_msg.replace('\n', '<br>')
            custom_msg = mark_safe(custom_msg)

        ctx_dict = {'activation_key': self.activation_key,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'password': password,
                    'primary': primary,
                    'user': self.user,
                    'custom_msg': custom_msg}
        message = render_to_string('registration/activation_email.html',
                                   ctx_dict)
        message = Pynliner().from_string(message).run()

        site = getattr(settings, 'SITE', None)

        headers = {
            'X-SMTPAPI': '{"category": "Activation sent (%s)"}' % self.pk
        }

        send_email(message, email_type=settings.ACTIVATION,
                   recipients=[self.email], site=site, headers=headers)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.activation_key = self.generate_key()
        super(ActivationProfile, self).save(*args, **kwargs)

    def expires(self):
        delta = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.sent + delta


class Invitation(models.Model):
    """
    Represents a non-user being invited to create an account on secure.my.jobs.

    Staff can use the admin interface to send generic invitations or
    invitations that add permissions. Members can use PRM to send generic
    invitations, access to their company features, or saved searches.
    """
    inviting_user = models.ForeignKey('myjobs.User', editable=False,
                                      related_name='invites_sent',
                                      null=True)
    inviting_company = models.ForeignKey('seo.Company', blank=True, null=True,
                                         related_name='invites_sent')
    invitee = models.ForeignKey('myjobs.User', related_name='invites',
                                on_delete=models.SET_NULL, null=True,
                                editable=False)
    invitee_email = models.CharField(max_length=255, db_index=True)
    invited = models.DateTimeField(auto_now_add=True, editable=False)
    added_permission = models.ForeignKey('auth.Group', blank=True, null=True)
    added_saved_search = models.ForeignKey('mysearches.SavedSearch',
                                           blank=True, null=True,
                                           editable=False)
    accepted = models.BooleanField(default=False, editable=False,
                                   help_text='Has the invitee accepted '
                                             'this invitation')

    def save(self, *args, **kwargs):
        from myjobs.models import User
        invitee = [self.invitee_email, self.invitee]
        if all(invitee):
            if not User.objects.get_email_owner(
                    self.invitee_email) == self.invitee:
                # ValidationErrors aren't appropriate, but nothing else fits
                # either; these are unrecoverable
                raise ValidationError('Invitee information does not match')
        elif not any(invitee):
            raise ValidationError('Invitee not provided')
        elif self.invitee_email:
            # create_user first checks if an email is in use and creates an
            # account if it does not.
            self.invitee = User.objects.create_user(email=self.invitee_email,
                                                    in_reserve=True)[0]
        else:
            self.invitee_email = self.invitee.email

        if not self.pk:
            self.send()

        super(Invitation, self).save(*args, **kwargs)

    def send(self):
        ap = ActivationProfile.objects.get_or_create(user=self.invitee,
                                                     email=self.invitee_email)[0]
        if ap.activation_key_expired():
            ap.reset_activation()
            ap = ActivationProfile.objects.get(pk=ap.pk)

        context = {'invitation': self,
                   'activation_key': ap.activation_key}

        if self.added_saved_search:
            initial_email = self.added_saved_search.initial_email(send=False)
            context['initial_search_email'] = initial_email

        body = render_to_string('registration/invitation_email.html',
                                context)
        body = Pynliner().from_string(body).run()

        if self.inviting_user:
            from_ = self.inviting_user.email
        else:
            from_ = self.inviting_company.name

        headers = {
            'X-SMTPAPI': '{"category": "Invitation Sent (%s)"}' % self.pk
        }

        self.invitee.email_user(body, email_type=settings.INVITATION,
                                inviter=from_, headers=headers)

        ap.sent = datetime_now()
        ap.save()
