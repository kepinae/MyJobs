from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from passwords.fields import PasswordField

from myjobs.models import User
from registration.models import Invitation
from registration.templatetags.password_reset_tags import get_current_seosite
from universal.helpers import send_email


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom password form based on Django's default set password form. This 
    allows us to enforce the new password rules.
    """
    new_password1 = PasswordField(error_messages={'required':
                                              'Password is required.'},
                                  label=('Password'), required=True,
                                  widget=forms.PasswordInput(attrs={
                                      'placeholder': _('Password'),
                                      'id': 'id_password1',
                                      'autocomplete': 'off'}),
                                  help_text="Must contain an uppercase "
                                            "letter, lowercase letter, "
                                            "number, and special character.")

    new_password2 = forms.CharField(error_messages={'required':
                                                'Password is required.'},
                                    label=_("Password (again)"), required=True,
                                    widget=forms.PasswordInput(
                                        attrs={'placeholder': _('Password (again)'),
                                               'id': 'id_password2',
                                               'autocomplete': 'off'},
                                        render_value=False))

    def clean(self):
        """
        Verify that the values entered into the two password fields
        match.
        
        """
        if 'password1' in self._errors:
            self._errors['password1'] = [
                error if error.endswith('.') else 'Password Error: ' + error
                for error in self._errors['password1'][:]]

        if 'password2' in self._errors:
            self._errors['password1'] = [
                error if error.endswith('.') else 'Password Error: ' + error
                for error in self._errors['password2'][:]]

        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                error_msg = u"The new password fields did not match."
                self._errors["password1"] = self.error_class([error_msg])
                # needed to ensure field is wrapped by error class
                self._errors["password2"] = self.error_class([""])

                # These fields are no longer valid. Remove them from the
                # cleaned data.
                del self.cleaned_data["password1"]
                del self.cleaned_data["password2"]

        return self.cleaned_data


class CustomAuthForm(AuthenticationForm):
    """
    Custom login form based on Django's default login form. This allows us to
    bypass the is_active check on the user in order to allow a limited profile
    view for users that haven't activated yet.
    
    """
    username = forms.CharField(error_messages={'required':'Email is required.'},
                               label=_("Email"), required=True,
                               widget=forms.TextInput(
                                   attrs={'placeholder': _('Email'),
                                          'id':'id_username'}))
    password = forms.CharField(error_messages={'required':'Password is required.'},
                               label=_("Password"), required=True,
                               widget=forms.PasswordInput(
                                   attrs={'placeholder':_('Password'),
                                          'id':'id_password'},
                                   render_value=False,))

    remember_me = forms.BooleanField(label=_('Keep me logged in for 2 weeks'),
                                     required=False,
                                     widget=forms.CheckboxInput(
                                         attrs={'id': 'id_remember_me'}))

    def __init__(self, request=None, *args, **kwargs):
        super(CustomAuthForm, self).__init__(request, *args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                error_msg = u"Invalid username or password. Please try again."

                self._errors['username'] = self.error_class([error_msg])
                # needed to ensure field is wrapped by error class
                self._errors['password'] = self.error_class([""])

                # These fields are no longer valid. Remove them from the
                # cleaned data
                del self.cleaned_data['username']
                del self.cleaned_data['password']  

        self.check_for_test_cookie()
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(self.error_messages['no_cookies'])

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form validates even when user is not active.
    """
    email = forms.CharField(error_messages={'required': 'Email is required.'},
                            label=_("Email"), required=True,
                            widget=forms.TextInput(
                                attrs={'placeholder': _('Email'),
                                       'id': 'id_email',
                                       'class': 'reset-pass-input'}))

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Cleaned save that doesn't do lots of stuff we don't need. Adds
        categories to emails and allows them to be html.
        """
        email = self.cleaned_data['email']
        user = User.objects.get_email_owner(email)
        if user is None:
            return
        c = {
            'user': user,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': token_generator.make_token(user)
        }
        headers = {
            'X-SMTPAPI': '{"category": "Forgotten Password for User %s"}' % (
                user.pk)
        }
        body = loader.render_to_string(email_template_name, c)
        send_email(body, email_type=settings.FORGOTTEN_PASSWORD,
                   recipients=[email], headers=headers,
                   domain=get_current_seosite('domain', 'lower'))


class RegistrationForm(forms.Form):
    email = forms.EmailField(error_messages={'required':'Email is required.'},
                             label=_("Email"), required=True,
                             widget=forms.TextInput(attrs={
                                 'placeholder': _('Email'),
                                 'id':'id_email',
                                 'autocomplete': 'off'}),
                             max_length=255)
    password1 = PasswordField(error_messages={'required':
                                              'Password is required.'},
                              label=('Password'), required=True,
                              widget=forms.PasswordInput(attrs={
                                  'placeholder': _('Password'),
                                  'id': 'id_password1',
                                  'autocomplete': 'off'}),
                              help_text="Must contain an uppercase "
                                        "letter, lowercase letter, digit, and "
                                        "special character.")
    password2 = forms.CharField(error_messages={'required':
                                                'Password is required.'},
                                label=_("Password (again)"), required=True,
                                widget=forms.PasswordInput(
                                    attrs={'placeholder': _('Password (again)'),
                                           'id': 'id_password2',
                                           'autocomplete': 'off'},
                                    render_value=False))

    def clean_email(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        if User.objects.get_email_owner(self.cleaned_data['email']):
            raise forms.ValidationError(_("A user with that email already exists."))
        else:
            return self.cleaned_data['email']

    def clean(self):
        """
        Verify that the values entered into the two password fields
        match.
        
        """
        if 'password1' in self._errors:
            self._errors['password1'] = [
                error if error.endswith('.') else 'Password Error: ' + error
                for error in self._errors['password1'][:]]

        if 'password2' in self._errors:
            self._errors['password1'] = [
                error if error.endswith('.') else 'Password Error: ' + error
                for error in self._errors['password2'][:]]

        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                error_msg = u"The new password fields did not match."
                self._errors["password1"] = self.error_class([error_msg])
                # needed to ensure field is wrapped by error class
                self._errors["password2"] = self.error_class([""])

                # These fields are no longer valid. Remove them from the
                # cleaned data.
                del self.cleaned_data["password1"]
                del self.cleaned_data["password2"]

        return self.cleaned_data


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = '__all__'

    def clean_invitee_email(self):
        invitee_email = self.cleaned_data['invitee_email']
        # validate_email raises a ValidationError if validation fails
        validate_email(invitee_email)
        invitee = User.objects.get_email_owner(invitee_email)
        if invitee is None:
            invitee = User.objects.create_user(email=invitee_email,
                                               send_email=False)[0]
        setattr(self, 'invitee', invitee)
        return invitee_email

    def clean_inviting_user(self):
        inviting_user = self.data.get('inviting_user')
        if inviting_user is None:
            inviting_user = getattr(self, 'admin_user', None)
        return inviting_user

    def clean(self):
        cleaned_data = super(InvitationForm, self).clean()
        inviting_user = self.clean_inviting_user()
        cleaned_data['inviting_user'] = inviting_user
        return cleaned_data

    def save(self, commit=True):
        instance = super(InvitationForm, self).save(commit=False)
        instance.invitee = getattr(self, 'invitee')
        for field, value in self.cleaned_data.items():
            if value is not None:
                setattr(instance, field, value)
        instance.save()
        return instance
