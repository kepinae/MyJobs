import datetime

from django.core.validators import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.utils.translation import ugettext_lazy as _
from collections import OrderedDict
from itertools import chain

from registration import signals as reg_signals
from registration.models import ActivationProfile
from myjobs.models import User


class ProfileUnits(models.Model):
    """
    This is the parent class for all user information. Creating any new
    profile unit instances (Education, Name, Email etc) end up in the
    ProfileUnits queryset as well.
    
    """
    date_created = models.DateTimeField(default=datetime.datetime.now,
                                        editable=False)
    date_updated = models.DateTimeField(default=datetime.datetime.now,
                                        editable=False)
    content_type = models.ForeignKey(ContentType, editable=False, null=True)
    user = models.ForeignKey(User, editable=False)

    def save(self, *args, **kwargs):
        """
        Custom save method to set the content type of the instance.
        
        """
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super(ProfileUnits, self).save(*args, **kwargs)

    def get_fields(self):
        """
        Returns the module type, value, and field type for all
        fields on a specific model
        """
        field_list = []
        for field in self._meta.local_fields:
            if not field.primary_key:
                field_list.append([field.verbose_name.title(),
                                   self.__getattribute__(field.name),
                                   field.get_internal_type()])
        return field_list

    def __unicode__(self):
        return self.content_type.name

    def get_model_name(self):
        return self.content_type.model

    @classmethod
    def get_verbose_class(object):
        return object.__name__

    def get_verbose(self):
        return self.content_type.name.title()

    @classmethod
    def suggestions(cls, user, by_priority=True):
        """Get a list of all suggestions for a user to improve their profile.

        :Inputs:
        user = User for which to get suggestions
        by_priority: Sort results by priority before returning, otherwise items
            will be in the order they appear in the `classes` list

        :Outputs:
        suggestions - A list of dictionary objects.  Each dictionary should
            conform to the following format.
            {
                'msg': '...',
                'priority': [0-9],
                'url': '...'
            }

        Note: this (and the similar method on the subclasses) are class methods
        because for any given class the user may not have an instance that can
        be used to access it.
        """
        classes = [Name, Summary, Address, Telephone, EmploymentHistory,
                   Education, License, MilitaryService, SecondaryEmail,
                   VolunteerHistory, Website]

        suggestions = chain(*[klass.get_suggestion(user) for klass in classes])
        if by_priority:
            suggestions = sorted(suggestions, reverse=True,
                                 key=lambda x: x['priority'])
        return suggestions


class Name(ProfileUnits):
    given_name = models.CharField(max_length=30,
                                  verbose_name=_("first name"))
    family_name = models.CharField(max_length=30,
                                   verbose_name=_("last name"))
    primary = models.BooleanField(default=False,
                                  verbose_name=_("Is primary name?"))

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """

        full_name = '%s %s' % (self.given_name, self.family_name)
        return full_name.strip()

    def save(self, *args, **kwargs):
        """
        Custom name save method to ensure only one name object per user
        has one primary=True. This function also updates the
        user's first_name and last_name.
        """
        duplicate_names = Name.objects.filter(user=self.user,
                                              given_name=self.given_name,
                                              family_name=self.family_name)
        if duplicate_names:
            if self.primary:
                if self.id in [name.id for name in duplicate_names]:
                    self.switch_primary_name()
                else:
                    duplicate = duplicate_names[0]
                    if duplicate.primary is False:
                        try:
                            current_primary = Name.objects.get(primary=True,
                                                               user=self.user)
                        except Name.DoesNotExist:
                            duplicate.primary = True
                            self.user.add_primary_name(
                                update=True, f_name=duplicate.given_name,
                                l_name=duplicate.family_name)
                            duplicate.save()
                        else:
                            current_primary.primary = False
                            current_primary.save()
                            duplicate.primary = True
                            self.user.add_primary_name(
                                update=True, f_name=duplicate.given_name,
                                l_name=duplicate.family_name)
                            duplicate.save()
            elif self.id in [name.id for name in duplicate_names]:
                self.user_full_name_check()
                super(Name, self).save(*args, **kwargs)
        else:
            if self.primary:
                self.switch_primary_name()
            else:
                try:
                    primary = Name.objects.get(primary=True, user=self.user)
                except Name.DoesNotExist:
                    primary = False
                if not primary:
                    self.user.add_primary_name(update=True, f_name="",
                                               l_name="")
                super(Name, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.get_full_name()

    def switch_primary_name(self, *args, **kwargs):
        try:
            temp = Name.objects.get(primary=True, user=self.user)
        except Name.DoesNotExist:
            self.user_full_name_check()
            super(Name, self).save(*args, **kwargs)
        else:
            temp.primary = False
            temp.save()
            self.user.add_primary_name(update=True, f_name=self.given_name,
                                       l_name=self.family_name)
            super(Name, self).save(*args, **kwargs)

    def user_full_name_check(self):
        if self.primary:
            self.user.add_primary_name(update=True, f_name=self.given_name,
                                       l_name=self.family_name)
        else:
            if self.user.get_full_name() == self.get_full_name():
                self.user.add_primary_name(update=True, f_name="", l_name="")
            else:
                self.user.add_primary_name()

    @classmethod
    def get_suggestion(cls, user):
        """Get a suggestion for a user to improve their education
        profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            return [{'msg': "Please add your name.",
                     'priority': 5,
                     'url': reverse('handle_form') + '?module=Name&id=new',
                     'module': 'Name'}]
        return []


def save_primary(sender, instance, created, **kwargs):
    user = instance.user
    if len(Name.objects.filter(user=user)) == 1 and created:
        try:
            user.profileunits_set.get(content_type__name="name",
                                      name__primary=True)
        except ProfileUnits.DoesNotExist:
            instance.primary = True
            instance.user.add_primary_name(update=True,
                                           f_name=instance.given_name,
                                           l_name=instance.family_name)
            instance.save()


def delete_primary(sender, instance, **kwargs):
    try:
        user = instance.user
        user.add_primary_name(update=True, f_name="", l_name="")
    except User.DoesNotExist:
        pass

post_save.connect(save_primary, sender=Name, dispatch_uid="save_primary")
post_delete.connect(delete_primary, sender=Name, dispatch_uid="delete_primary")


EDUCATION_LEVEL_CHOICES = (
    ('', _('Education Level')),
    (3, _('High School')),
    (4, _('Non-Degree Education')),
    (5, _('Associate')),
    (6, _('Bachelor')),
    (7, _('Master')),
    (8, _('Doctoral')),
)


class Education(ProfileUnits):
    organization_name = models.CharField(max_length=255,
                                         verbose_name=_('institution'),
                                         blank=True)
    degree_date = models.DateField(verbose_name=_('completion date'),
                                   blank=True, null=True)
    city_name = models.CharField(max_length=255, blank=True,
                                 verbose_name=_('city'))
    # ISO 3166-2:2007
    country_sub_division_code = models.CharField(max_length=5, blank=True,
                                                 verbose_name=_("State/Region"))
    country_code = models.CharField(max_length=3, blank=True,
                                    verbose_name=_("country"))  # ISO 3166-1
    # ISCED-2011 Can be [0-8]
    education_level_code = models.IntegerField(choices=EDUCATION_LEVEL_CHOICES,
                                               verbose_name=_("education level"),
                                               blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    education_score = models.CharField(max_length=255, blank=True,
                                       verbose_name=_("GPA"))
    degree_name = models.CharField(max_length=255, blank=True,
                                   verbose_name=_('degree type'))
    degree_major = models.CharField(max_length=255, verbose_name=_('major'),
                                    blank=True)
    degree_minor = models.CharField(max_length=255, blank=True,
                                    verbose_name=_('minor'))

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of all suggestions for a user to improve their education
        profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            return [{
                'msg': ("Would you like to provide information about "
                        "your education?"),
                'priority': 5,
                'module': 'Education',
                'url': reverse('handle_form') + '?module=Education&id=new'}]
        else:
            return []


class Address(ProfileUnits):
    label = models.CharField(max_length=60, blank=True,
                             verbose_name=_('Address Label'))
    address_line_one = models.CharField(max_length=255, blank=True,
                                        verbose_name=_('Address Line One'))
    address_line_two = models.CharField(max_length=255, blank=True,
                                        verbose_name=_('Address Line Two'))
    city_name = models.CharField(max_length=255, blank=True,
                                 verbose_name=_("City"))
    country_sub_division_code = models.CharField(max_length=5, blank=True,
                                                 verbose_name=_("State/Region"))
    country_code = models.CharField(max_length=3, blank=True,
                                    verbose_name=_("Country"))
    postal_code = models.CharField(max_length=12, blank=True,
                                   verbose_name=_("Postal Code"))

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of all suggestions for a user to improve their address
        profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        objects = cls.objects.filter(user=user).order_by('date_updated')
        if len(objects) == 0:
            return [{'msg': 'Would you like to provide your address?',
                     'url': reverse('handle_form') + '?module=Address&id=new',
                     'priority': 5,
                     'module': 'Address'}]
        else:
            return [{'msg': 'Do you need to update your address from %s?' %
                            objects[0].address_line_one,
                     'url': reverse('handle_form') + '?module=Address&id=%s' %
                            objects[0].pk,
                     'priority': 1,
                     'module': 'Address'}]


class Telephone(ProfileUnits):
    USE_CODE_CHOICES = (
        ('', 'Phone Type'),
        ('Home', 'Home'),
        ('Work', 'Work'),
        ('Mobile', 'Mobile'),
        ('Pager', 'Pager'),
        ('Fax', 'Fax'),
        ('Other', 'Other')
    )
    channel_code = models.CharField(max_length=30, editable=False, blank=True)
    country_dialing = models.CharField(max_length=3, blank=True,
                                       verbose_name=_("Country Code"))
    area_dialing = models.CharField(max_length=5, blank=True,
                                    verbose_name=_("Area Code"))
    number = models.CharField(max_length=10, blank=True,
                              verbose_name=_("Local Number"))
    extension = models.CharField(max_length=5, blank=True)
    use_code = models.CharField(max_length=30, choices=USE_CODE_CHOICES,
                                blank=True, verbose_name=_("Phone Type"))

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of all suggestions for a user to improve their telephone
        profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            return [{'msg': 'Would you like to add a telephone?',
                     'priority': 5,
                     'module': 'Telephone',
                     'url': reverse('handle_form') + '?module=Telephone&id=new'
                    }]
        else:
            return []

    def save(self, *args, **kwargs):
        if self.use_code == "Home" or self.use_code == "Work" or self.use_code == "Other":
            self.channel_code = "Telephone"
        if self.use_code == "Mobile":
            self.channel_code = "MobileTelephone"
        if self.use_code == "Pager":
            self.channel_code = "Pager"
        if self.use_code == "Fax":
            self.channel_code = "Fax"
        super(Telephone, self).save(*args, **kwargs)


class EmploymentHistory(ProfileUnits):
    position_title = models.CharField(max_length=255,
                                      verbose_name=_("Position Title"))
    organization_name = models.CharField(max_length=255, blank=True,
                                         verbose_name=_("Company"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    current_indicator = models.BooleanField(default=False,
                                            verbose_name=_("I still work here"))

    # Optional fields
    end_date = models.DateField(blank=True, null=True)
    city_name = models.CharField(max_length=255, blank=True, null=True)
    country_sub_division_code = models.CharField(max_length=5, blank=True,
                                                 verbose_name=_("State/Region"))
    country_code = models.CharField(max_length=3, blank=True, null=True,
                                    verbose_name=_("country"))
    description = models.TextField(blank=True, null=True)

    # Hidden fields
    industry_code = models.CharField(max_length=255, blank=True, null=True,
                                     verbose_name=_("industry"),
                                     editable=False)
    job_category_code = models.CharField(max_length=255, blank=True, null=True,
                                         verbose_name=_("job category"),
                                         editable=False)
    onet_code = models.CharField(max_length=255, blank=True, null=True,
                                 editable=False)

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of all suggestions for a user to improve their employment
        history on their profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        objects = cls.objects.filter(user=user).order_by('start_date')
        if len(objects) == 0:
            return [{'msg': "Would you like to add your employment history?",
                     'url': reverse('handle_form') + \
                            '?module=EmploymentHistory&id=new',
                     'priority': 5,
                     'module': 'Employment'}]
        elif objects[0].current_indicator:
            return [{'msg': "Are you still employed with %s?" %
                            objects[0].organization_name,
                     'url': reverse('handle_form') + \
                            '?module=EmploymentHistory&id=%s' % objects[0].pk,
                     'priority': 0,
                     'module': 'Employment'}]
        else:
            return [{'msg': "Have you worked anywhere since being employed" +
                            " with %s?" % objects[0].organization_name,
                     'url': reverse('handle_form') + \
                            '?module=EmploymentHistory&id=%s' % objects[0].pk,
                     'priority': 1,
                     'module': 'Employment'}]


class SecondaryEmail(ProfileUnits):
    email = models.EmailField(max_length=255, unique=True, error_messages={
        'unique': 'This email is already registered.'})
    label = models.CharField(max_length=30, blank=True, null=True)
    verified = models.BooleanField(default=False, editable=False)
    verified_date = models.DateTimeField(blank=True, null=True, editable=False)

    def __unicode__(self):
        return self.email

    def save(self, *args, **kwargs):
        """
        Custom save triggers the creation of an activation profile and the
        sending of an activation email if the email is new.
        """

        primary = kwargs.pop('old_primary', None)
        if not self.pk and not self.verified and primary is None:
            reg_signals.email_created.send(sender=type(self), user=self.user,
                                           email=self.email)
            reg_signals.send_activation.send(sender=type(self), user=self.user,
                                             email=self.email)
        super(SecondaryEmail, self).save(*args, **kwargs)

    def set_as_primary(self):
        """
        Replaces the User email with this email object, saves the old primary
        as a new address while maintaining the state of verification. The
        new primary address is then deleted from the SecondaryEmail table. This
        is only allowed if the email has been verified.
        Returns boolean if successful.
        """

        if self.verified:
            user = self.user
            user.is_active, self.verified = self.verified, user.is_active

            self.email, user.email = user.email, self.email

            user.save()
            self.user = user
            self.save(old_primary=True)

            return True
        else:
            return False

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of all suggestions for a user to add secondary emails to 
        their profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            return [{'msg': "Would you like to add an additional email?",
                     'url': reverse('handle_form') + \
                            '?module=SecondaryEmail&id=new',
                     'priority': 3,
                     'module': 'Secondary Email'}]
        return []


class MilitaryService(ProfileUnits):
    country_code = models.CharField(max_length=3, blank=True,
                                    verbose_name=_("Country"))  # ISO 3166-1
    branch = models.CharField(max_length=255, verbose_name="Branch")
    department = models.CharField(max_length=255, blank=True,
                                  verbose_name="Department")
    division = models.CharField(max_length=255, blank=True,
                                verbose_name="Division")
    expertise = models.CharField(max_length=255, blank=True,
                                 verbose_name="Expertise")
    service_start_date = models.DateField(verbose_name=_("Start Date"),
                                          null=True, blank=True)
    service_end_date = models.DateField(verbose_name=_("End Date"),
                                        null=True, blank=True)
    start_rank = models.CharField(max_length=50, blank=True,
                                  verbose_name=_("Start Rank"))
    end_rank = models.CharField(max_length=50, blank=True, 
                                verbose_name=_("End Rank"))
    campaign = models.CharField(max_length=255, blank=True,
                                verbose_name="Campaign")
    honor = models.CharField(max_length=255, blank=True,
                             verbose_name="Honors")

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of suggestions for a user to add military service to 
        their profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            return [{'msg': "Have you served in the armed forces?",
                     'url': reverse('handle_form') + \
                     '?module=MilitaryService&id=new',
                    'priority': 3,
                     'module': 'Military Service'}]
        return []


class Website(ProfileUnits):
    SITE_TYPE_CHOICES = (
        ('personal', 'Personal'),
        ('portfolio', 'Portfolio of my work'),
        ('created', 'Site I created or helped create'),
        ('association', 'Group or Association'),
        ('social', 'Social media'),
        ('other', 'Other'),
    )

    display_text = models.CharField(max_length=50, blank=True,
                                    verbose_name='Display Text')
    uri = models.URLField(verbose_name='Web Address')
    uri_active = models.BooleanField(default=False,
                                     verbose_name='Currently active?')
    description = models.TextField(max_length=500, blank=True,
                                   verbose_name='Site Description')
    site_type = models.CharField(max_length=50, choices=SITE_TYPE_CHOICES,
                                 blank=True, verbose_name='Type of Site')

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of suggestions for a user to add a website to their

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user):
            return [{
                'msg': "Do you have a personal website or online portfolio?",
                'url': reverse('handle_form') + '?module=Website&id=new',
                'priority': 3,
                'module': 'Website'}]
        return []


class License(ProfileUnits):
    license_name = models.CharField(max_length=255, verbose_name="License Name")
    license_type = models.CharField(max_length=255, verbose_name="License Type")
    description = models.CharField(max_length=255, verbose_name="Description",
                                   blank=True)

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of all suggestions for a user to add licenses or
        certifications to their profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            msg = ('Would you like to add and professional licenses or ' +
                  'certifications?')
            return [{'msg': msg,
                     'url': reverse('handle_form') + '?module=License&id=new',
                     'priority': 3,
                     'module': 'License'}]
        return []


class Summary(ProfileUnits):
    headline = models.CharField(max_length=100, verbose_name="Headline",
                                help_text='How you describe your profession.' +
                                          ' ie "Experienced accounting ' +
                                          'professional"')
    the_summary = models.TextField(max_length=2000, verbose_name="Summary",
                                   blank=True,
                                   help_text='A short summary of your ' +
                                             'strength and career to date.')

    def save(self, *args, **kwargs):
        try:
            summary_model = self.user.profileunits_set.get(
                content_type__name="summary")
        except ProfileUnits.DoesNotExist:
            summary_model = None

        if not summary_model:
            super(Summary, self).save(*args, **kwargs)
        else:
            if self.id == summary_model.id:
                super(Summary, self).save(*args, **kwargs)
            else:
                raise ValidationError("A summary already exists")

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of all suggestions for a user to add a summary to their
        profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            return [{'msg': "Would you like to add a summary of your career?",
                     'url': reverse('handle_form') + '?module=Summary&id=new',
                     'priority': 5,
                     'module': 'Resume Summary'}]
        return []


class VolunteerHistory(ProfileUnits):
    position_title = models.CharField(max_length=255,
                                      verbose_name=_("Position Title"))
    organization_name = models.CharField(max_length=255,
                                         verbose_name=_("Organization"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    current_indicator = models.BooleanField(default=False,
                                            verbose_name=_(
                                                "I still volunteer here"))

    # Optional fields
    end_date = models.DateField(blank=True, null=True)
    city_name = models.CharField(max_length=255, blank=True)
    country_sub_division_code = models.CharField(max_length=5, blank=True,
                                                 verbose_name=_("State/Region"))
    country_code = models.CharField(max_length=3, blank=True,
                                    verbose_name=_("country"))
    description = models.TextField(blank=True)

    @classmethod
    def get_suggestion(cls, user):
        """Get a list of suggestions for a user to improve their volunteer
        history profile.

        :Inputs:
        user = User for which to get suggestions

        :Outputs:
        suggestion - A dictionary object which should conform to the format
                     indicated in ProfileUnits.suggestions().
        """
        if not cls.objects.filter(user=user).exists():
            msg = ("Do you have any relevant volunteer experience you would " +
                    "like to include?")
            return [{'msg': msg,
                     'url': reverse('handle_form') + \
                            '?module=VolunteerHistory&id=new',
                     'priority':3,
                     'module': 'Volunteer History'}]
        return []


def delete_secondary_activation(sender, **kwargs):
    """
    When a secondary email is deleted, deletes that email's associated
    activation profile

    Inputs:
    :sender: Model that sent this signal
    :instance: instance of :sender:
    """

    instance = kwargs.get('instance')
    activation = ActivationProfile.objects.filter(user=instance.user,
                                                  email__iexact=instance.email)
    activation.delete()

# Calls `delete_secondary_activation` after a secondary email is deleted.
# dispatch_uid: arbitrary unique string that prevents this signal from
# being connected to multiple times
models.signals.pre_delete.connect(delete_secondary_activation,
                                  sender=SecondaryEmail,
                                  dispatch_uid='delete_secondary_activation')


class BaseProfileUnitManager(object):
    """
    Class for managing how profile units are displayed

    Visible units are returned by displayed_units

    Displayed and excluded models are defined as lists of model names

    Child classes can define custom display logic per model in
    <model_name>_is_displayed methods
        i.e.
            def name_is_displayed(self, unit):
                return unit.is_primary()

    Each input accepts a list of model names as strings i.e. ['name','address']
    Inputs:
    :displayed: List of units one wants to be displayed
    :excluded:  List of units one would want to exclude from being displayed
    :order:     List of units to order the output for displayed_units
    """
    def __init__(self, displayed=None, excluded=None, order=None):
        self.displayed = displayed or []
        self.excluded = excluded or []
        self.order = order or []

    def is_displayed(self, unit):
        """
        Returns True if a unit should be displayed
        Input:
        :unit: An instance of ProfileUnit
        """
        try:
            field_is_displayed = getattr(self,
                                         unit.get_model_name()+'_is_displayed')
            if field_is_displayed:
                return field_is_displayed(unit)
        except AttributeError:
            pass
        if not self.displayed and not self.excluded:
            return True
        elif self.displayed and self.excluded:
            return unit.get_model_name() in self.displayed \
                and unit.get_model_name() not in self.excluded
        elif self.excluded:
            return unit.get_model_name() not in self.excluded
        elif self.displayed:
            return unit.get_model_name() in self.displayed
        else:
            return True

    def order_units(self, profileunits, order):
        """
        Sorts the dictionary from displayed_units

        Inputs:
        :profileunits:  Dict of profileunits made in displayed_units
        :order:         List of model names (as strings)

        Outputs:
        Returns an OrderedDict of the sorted list
        """
        sorted_units = []
        units_map = {item[0]: item for item in profileunits.items()}
        for item in order:
            try:
                sorted_units.append(units_map[item])
                units_map.pop(item)
            except KeyError:
                pass
        sorted_units.extend(units_map.values())
        return OrderedDict(sorted_units)

    def displayed_units(self, profileunits):
        """
        Returns a dictionary of {model_names:[profile units]} to be displayed

         Inputs:
        :profileunits:  The default value is .all() profileunits, but you can
                        input your own QuerySet of profileunits if you are
                        using specific filters

        Outputs:
        :models:        Returns a dictionary of profileunits, an example:
                        {u'name': [<Name: Foo Bar>, <Name: Bar Foo>]}
        """
        models = {}

        for unit in profileunits:
            if self.is_displayed(unit):
                models.setdefault(unit.get_model_name(), []).append(
                    getattr(unit, unit.get_model_name()))

        if self.order:
            models = self.order_units(models, self.order)

        return models


class PrimaryNameProfileUnitManager(BaseProfileUnitManager):
    """
    Excludes primary name from displayed_units and sets self.primary_name
    """
    def __init__(self, displayed=None, excluded=None, order=None):
        super(PrimaryNameProfileUnitManager, self).__init__(displayed,
                                                            excluded, order)

    def name_is_displayed(self, profileunit):
        if profileunit.name.primary:
            self.primary_name = profileunit.name.get_full_name()
        return False
