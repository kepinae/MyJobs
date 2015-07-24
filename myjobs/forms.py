import pytz

from django.forms import *
from passwords.fields import PasswordField
from django.core.validators import ValidationError

from myjobs.models import User
from myprofile.models import SecondaryEmail


timezones = [('America/New_York', 'America/New_York'),
             ('America/Chicago', 'America/Chicago'),
             ('America/Phoenix', 'America/Phoenix'),
             ('America/Los_Angeles', 'America/Los_Angeles'),
             ('America/Anchorage', 'America/Anchorage'),
             ('US/Alaska', 'US/Alaska'),
             ('US/Aleutian', 'US/Aleutian'),
             ('US/Arizona', 'US/Arizona'),
             ('US/Central', 'US/Central'),
             ('US/East-Indiana', 'US/East-Indiana'),
             ('US/Eastern', 'US/Eastern'),
             ('US/Hawaii', 'US/Hawaii'),
             ('US/Indiana-Starke', 'US/Indiana-Starke'),
             ('US/Michigan', 'US/Michigan'),
             ('US/Mountain', 'US/Mountain'),
             ('US/Pacific', 'US/Pacific'),
             ('US/Pacific-New', 'US/Pacific-New'),
             ('US/Samoa', 'US/Samoa'),
             ('Etc/GMT0', 'GMT+0'),
             ('Etc/GMT+1', 'GMT+1'),
             ('Etc/GMT+2', 'GMT+2'),
             ('Etc/GMT+3', 'GMT+3'),
             ('Etc/GMT+4', 'GMT+4'),
             ('Etc/GMT+5', 'GMT+5'),
             ('Etc/GMT+6', 'GMT+6'),
             ('Etc/GMT+7', 'GMT+7'),
             ('Etc/GMT+8', 'GMT+8'),
             ('Etc/GMT+9', 'GMT+9'),
             ('Etc/GMT+10', 'GMT+10'),
             ('Etc/GMT+11', 'GMT+11'),
             ('Etc/GMT+12', 'GMT+12'),
             ('Etc/GMT-1', 'GMT-1'),
             ('Etc/GMT-2', 'GMT-2'),
             ('Etc/GMT-3', 'GMT-3'),
             ('Etc/GMT-4', 'GMT-4'),
             ('Etc/GMT-5', 'GMT-5'),
             ('Etc/GMT-6', 'GMT-6'),
             ('Etc/GMT-7', 'GMT-7'),
             ('Etc/GMT-8', 'GMT-8'),
             ('Etc/GMT-9', 'GMT-9'),
             ('Etc/GMT-10', 'GMT-10'),
             ('Etc/GMT-11', 'GMT-11'),
             ('Etc/GMT-12', 'GMT-12'),
             ('Etc/GMT-13', 'GMT-13'),
             ('Etc/GMT-14', 'GMT-14')]


def make_choices(user):
    """
    Turns the set of email addresses associated with a user into a list
    suitable for use in a ChoiceField

    Inputs:
    :user: User instance
    """
    choices = []
    if user.is_verified:
        choices.append((user.email, user.email))
        for email in SecondaryEmail.objects.filter(user=user, verified=True):
            choices.append((email.email, email.email))
    return choices


class BaseUserForm(ModelForm):
    """
    Most models in the other apps are associated with a user. This base form
    will take a user object as a key word argument and saves the form instance
    to a that specified user. It also takes a few common inputs that can be
    used to customize form rendering.

    Inputs (these are the common inputs we will use for rendering forms):
    :user: a user object. We will always pass a user object in  because all
        ProfileUnits are linked to a user.
    :auto_id: this is a boolean that determines whether a label is displayed or
        not and is by default set to True. Setting this to false uses the
        placeholder text instead, except for boolean and select fields.
    :empty_permitted: allow form to be submitted as empty even if the fields
        are required. This is particularly useful when we combine multiple
        Django forms on the front end and submit it as one request instead of
        several separate requests.
    :only_show_required: Template uses this flag to determine if it should only
        render required forms. Default is False.
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.only_show_required = kwargs.pop('only_show_required', False)
        super(BaseUserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(BaseUserForm, self).save(commit=False)
        if self.user and not self.user.is_anonymous():
            instance.user = self.user
            instance.save()
        return instance


class EditCommunicationForm(BaseUserForm):
    def __init__(self, *args, **kwargs):
        super(EditCommunicationForm, self).__init__(*args, **kwargs)
        choices = make_choices(self.user)
        self.fields["email"] = ChoiceField(widget=Select(attrs={
                                           'id': 'id_digest_email'}),
                                           choices=choices,
                                           initial=choices[0][0])
        self.fields["email"].label = "Primary Email"
        self.fields['timezone'].widget = Select(choices=timezones)
        self.fields['timezone'].initial = self.user.timezone

    def clean_timezone(self):
        if self.cleaned_data['timezone'] not in pytz.all_timezones:
            raise ValidationError("You must select a valid timezone.")
        return self.cleaned_data['timezone']

    def save(self):
        if self.cleaned_data['email'] != self.user.email:
            new_email = SecondaryEmail.objects.get(
                email__iexact=self.cleaned_data['email'])
            if new_email.verified:
                new_email.set_as_primary()
            else:
                self.cleaned_data['email'] = self.user.email
        super(EditCommunicationForm, self).save(self)

    class Meta:
        model = User
        fields = ('email', 'timezone', 'opt_in_myjobs', 'opt_in_employers', )


class ChangePasswordForm(Form):
    password = CharField(label="Password",
                         widget=PasswordInput(
                             attrs={'placeholder': 'Password'}))
    new_password1 = PasswordField(label=('New Password'),
                              widget=PasswordInput(
                                  attrs={
                                      'placeholder': 'New Password',
                                      # so broken :-(
                                      'class': 'broken'
                                  }),
                              help_text="Must contain an uppercase "
                                        "letter, lowercase letter, number, "
                                        "and special character.")
    new_password2 = CharField(label="New Password (again)",
                              widget=PasswordInput(
                                  attrs={'placeholder':
                                         'New Password (again)'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.user.check_password(password):
            raise ValidationError(("Wrong password."))
        else:
            return self.cleaned_data['password']

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        if 'new_password1' in self.cleaned_data and 'new_password2' in self.cleaned_data:
            if self.cleaned_data['new_password1'] != self.cleaned_data['new_password2']:
                error_msg = u"The new password fields did not match."
                self._errors["new_password1"] = self.error_class([error_msg])
                self._errors["new_password2"] = self.error_class([error_msg])

                # These fields are no longer valid. Remove them from the
                # cleaned data.
                del cleaned_data["new_password1"]
                del cleaned_data["new_password2"]
            else:
                return self.cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save()


class UserAdminForm(ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    # Used to update/change a password.
    new_password = CharField(label='New password', required=False)

    def __init__(self, *args, **kwargs):
        super(UserAdminForm, self).__init__(*args, **kwargs)

    def full_clean(self):
        """
        Removes ValidationErrors from gravatars that are actually correct.

        """
        super(UserAdminForm, self).full_clean()
        if 'gravatar' in self._errors:
            # If the gravatar is none (the default value) or blank, force
            # the ValidationError to be ignored.
            gravatar_val = self.data['gravatar']
            if gravatar_val == '' or gravatar_val == 'none':
                del self._errors['gravatar']

    def save(self, commit=True):
        instance = super(UserAdminForm, self).save(commit)
        # A blank string and 'none' are both valid gravatar options that
        # don't pass form validation, so gravatar needs to be saved here
        # if the gravatar was set to either.
        if (self.data['gravatar'] != instance.gravatar) and \
           (self.data['gravatar'] == 'none' or self.data['gravatar'] == ''):
            instance.gravatar = self.data['gravatar']
        if not instance.user_guid:
            instance.make_guid()
        if 'new_password' in self.cleaned_data:
            if self.cleaned_data['new_password'] != '':
                instance.set_password(self.cleaned_data['new_password'])
        return instance
