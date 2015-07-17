from datetime import datetime, timedelta
from os import path
from re import sub
from urllib import urlencode
from uuid import uuid4

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from myjobs.models import User
from postajob.location_data import states
from states import synonyms


CONTACT_TYPE_CHOICES = (('email', 'Email'),
                        ('phone', 'Phone'),
                        ('meetingorevent', 'Meeting or Event'),
                        ('job', 'Job Followup'),
                        ('pssemail', "Partner Saved Search Email"))
CONTACT_TYPES = dict(CONTACT_TYPE_CHOICES)

# Flags for ContactLogEntry action_flag. Based on django.contrib.admin.models
# action flags.
ADDITION = 1
CHANGE = 2
DELETION = 3
EMAIL = 4

ACTIVITY_TYPES = {
    1: 'added',
    2: 'updated',
    3: 'deleted',
    4: 'sent',
}


class Status(models.Model):
    """
    Keeps track of a particular model's approval status.
    """
    UNPROCESSED, APPROVED, DENIED = range(3)
    CODES = {
        UNPROCESSED: 'Unprocessed',
        APPROVED: 'Approved',
        DENIED: 'Denied'
    }

    code = models.PositiveSmallIntegerField(
        default=APPROVED, choices=CODES.items(), verbose_name="Status Code")
    approved_by = models.ForeignKey(
        'myjobs.User', null=True, on_delete=models.SET_NULL)
    last_modified = models.DateTimeField(
        auto_now=True, verbose_name="Last Modified")

    def __unicode__(self):
        return dict(Status.CODES)[self.code]


class SearchParameterQuerySet(models.query.QuerySet):
    """
    Defines a query set with a `from_search` method for filtering by query
    paramenters.
    """

    # used ot map field types to a query
    QUERY_BY_TYPE = {
        'CharField': '__icontains',
        'TextField': '__icontains',
        'AutoField': '__exact',
        'ForeignKey': '',
        'ManyToManyField': ''}

    # TODO: Come up with a better name for this method
    def from_search(self, company=None, parameters=None):
        """
        Intelligently filter based on query parameters.

        Inputs:
            :company: The company to restrict results to
            :parameters: A dict of field: term pairs where field is a field of
                         the `ContactRecord` model and term is search term
                         you'd like to filter against.

                         For `datetime`, pass `start_date` and/or `end_date`
                         instead.
            If the model has a `_parse_parameters` method, that is called
            before parsing remaining parameters.
        """
        parameters = (parameters or {}).copy()
        # only return records the current user has access to
        if company:
            company_ref = getattr(self.model, 'company_ref', 'company')
            self = self.filter(**{company_ref: company})
        else:
            self = self.all()

        # fetch related models in one query
        self = self.select_related()

        # extract special fields so they aren't traversed later
        if parameters.get('start_date'):
            parameters['start_date'] = datetime.strptime(
                parameters['start_date'], '%m/%d/%Y').date()

        if parameters.get('end_date'):
            # handles off-by-one error; otherwise date provided is excluded
            parameters['end_date'] = datetime.strptime(
                parameters['end_date'], '%m/%d/%Y').date() + timedelta(1)

        # do special parsing
        if parameters and hasattr(self.model, '_parse_parameters'):
            self = self.model._parse_parameters(parameters, self)

        for key, value in parameters.items():
            if hasattr(value, '__iter__'):
                query = '%s%s' % (key, '__in')
            else:
                type_ = self.get_field_type(key)

                # construct query based on field type
                query = '%s%s' % (
                    key, SearchParameterQuerySet.QUERY_BY_TYPE[type_])

            self = self.filter(**{query: value})

        # remove duplicates
        self = self.distinct()

        return self

    def get_field_type(self, name):
        """
        Returns the type of the `model`'s `field` or None if it doesn't
        exist.
        """

        if '__' in name:
            return 'ForeignKey'

        # using get_fields isn't sufficient as it doesn't account
        field = self.model._meta.get_field_by_name(name)[0]

        try:
            field_type = field.get_internal_type()
        except AttributeError:
            # field apparently isn't a field
            field_type = field.field.get_internal_type()

        return field_type


class SearchParameterManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super(SearchParameterManager, self).__init__(*args, **kwargs)

    def get_query_set(self):
        return SearchParameterQuerySet(self.model, using=self._db)

    def from_search(self, company=None, parameters=None):
        return self.get_query_set().from_search(
            company, parameters)

    def sort_by(self, *fields):
        return self.get_query_set().sort_by(*fields)


class Location(models.Model):
    label = models.CharField(max_length=60, verbose_name='Address Label',
                             blank=True)
    address_line_one = models.CharField(max_length=255,
                                        verbose_name='Address Line One',
                                        blank=True)
    address_line_two = models.CharField(max_length=255,
                                        verbose_name='Address Line Two',
                                        blank=True)
    city = models.CharField(max_length=255, verbose_name='City')
    state = models.CharField(max_length=200, verbose_name='State/Region')
    country_code = models.CharField(max_length=3, verbose_name='Country',
                                    default='USA')
    postal_code = models.CharField(max_length=12, verbose_name='Postal Code',
                                   blank=True)

    def __unicode__(self):
        return ", ".join(filter(bool, [self.city, self.state]))

    natural_key = __unicode__

    def save(self, **kwargs):
        super(Location, self).save(**kwargs)


class Contact(models.Model):
    """
    Everything here is self explanatory except for one part. With the Contact
    object there is Contact.partner_set and .partners_set

    """
    user = models.ForeignKey(User, blank=True, null=True,
                             on_delete=models.SET_NULL)
    partner = models.ForeignKey('Partner', 
                                null=True, on_delete=models.SET_NULL)
    # used if this partner was created by using the partner library
    library = models.ForeignKey('PartnerLibrary', null=True,
                                on_delete=models.SET_NULL)
    name = models.CharField(max_length=255, verbose_name='Full Name')
    email = models.EmailField(max_length=255, verbose_name='Email', blank=True)
    phone = models.CharField(max_length=30, verbose_name='Phone', blank=True,
            default='')
    locations = models.ManyToManyField('Location', related_name='contacts')
    tags = models.ManyToManyField('Tag', null=True)
    notes = models.TextField(max_length=1000, verbose_name='Notes',
                             blank=True, default="")
    archived_on = models.DateTimeField(null=True)
    approval_status = models.OneToOneField(
        'mypartners.Status', null=True, verbose_name="Approval Status")

    company_ref = 'partner__owner'
    objects = SearchParameterManager()

    class Meta:
        verbose_name_plural = 'contacts'

    @classmethod
    def _parse_parameters(self, parameters, records):
        """Used to parse state during `from_search()`."""

        contact_type = parameters.pop('contact_type', None)
        start_date = parameters.pop('start_date', None)
        end_date = parameters.pop('end_date', None)
        state = parameters.pop('state', None)
        city = parameters.pop('city', None)
        tags = parameters.pop('tags__name', None)

        if tags:
            if not hasattr(tags, '__iter__'):
                tags = [tags]
            for tag in tags:
                records = records.filter(tags__name__icontains=tag)

        # using a foreign relationship, so can't just filter twice
        if start_date and end_date:
            records = records.filter(
                partner__contactrecord__date_time__range=[
                    start_date, end_date])
        elif start_date:
            records = records.filter(
                partner__contactrecord__date_time__gte=start_date)
        elif end_date:
            records = records.filter(
                partner__contactrecord__date_time__lte=end_date)

        if state:
            state_query = models.Q()
            # match state synonyms when querying
            for synonym in synonyms[state.strip().lower()]:
                state_query |= models.Q(
                    locations__state__iexact=synonym)

            records = records.filter(state_query)

        if city:
            records = records.filter(locations__city__icontains=city)

        if contact_type:
            if not hasattr(contact_type, '__iter__'):
                contact_type = [contact_type]

            records = records.filter(
                contactrecord__contact_type__in=contact_type)

        return records

    def __unicode__(self):
        if self.name:
            return self.name
        if self.email:
            return self.email
        return 'Contact object'

    natural_key = __unicode__

    def save(self, *args, **kwargs):
        """
        Checks to see if there is a User that is using self.email add said User
        to self.user

        """
        if not self.user:
            if self.email:
                try:
                    user = User.objects.get(email=self.email)
                except User.DoesNotExist:
                    pass
                else:
                    self.user = user

        return super(Contact, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pre_delete.send(sender=Contact, instance=self, using='default')
        self.archived_on = datetime.now()
        self.primary_contact.clear()
        self.save()

    def get_contact_url(self):
        base_urls = {
            'contact': reverse('edit_contact'),
        }
        params = {
            'partner': self.partner.pk,
            'company': self.partner.owner.pk,
            'id': self.pk,
            'ct': ContentType.objects.get_for_model(Contact).pk
        }
        query_string = urlencode(params)
        return "%s?%s" % (base_urls[self.content_type.name], query_string)


@receiver(pre_delete, sender=Contact, dispatch_uid='pre_delete_contact_signal')
def delete_contact(sender, instance, using, **kwargs):
    """
    Signalled when a Contact is deleted to deactivate associated partner saved
    searches, if any exist
    """

    if instance.user is not None:
        # user.partnersavedsearch_set filters on partnersavedsearch.owner, not
        # .user
        to_disable = instance.user.savedsearch_set.filter(
            partnersavedsearch__isnull=False)

        for pss in to_disable:
            pss.is_active = False
            note = ('\nThe contact for this partner saved search ({name}) '
                    'was deleted by the partner. As a result, this search '
                    'has been disabled.').format(name=instance.name)
            pss.notes += note
            pss.save()


@receiver(pre_delete, sender=Contact,
          dispatch_uid='post_delete_contact_signal')
def delete_contact_locations(sender, instance, **kwargs):
    """
    Since locations will more than likely be specific to a contact, we should
    be able to delete all of a contact's locations when that contact is
    deleted.
    """
    for location in instance.locations.all():
        if not location.contacts.all():
            location.delete()


@receiver(pre_save, sender=Contact, dispatch_uid='pre_save_contact_signal')
def save_contact(sender, instance, **kwargs):
    if not instance.approval_status:
        # if no relation exists, instance.user will raise an attribute error
        instance.approval_status = Status.objects.create(
            approved_by=instance.user)


class Partner(models.Model):
    """
    Object that this whole app is built around.

    """
    name = models.CharField(max_length=255,
                            verbose_name='Partner Organization')
    data_source = models.CharField(max_length=255,
                                   verbose_name='Source',
                                   blank=True)
    uri = models.URLField(verbose_name='URL', blank=True)
    primary_contact = models.ForeignKey('Contact', null=True,
                                        related_name='primary_contact',
                                        on_delete=models.SET_NULL)
    # used if this partner was created by using the partner library
    library = models.ForeignKey('PartnerLibrary', null=True,
                                on_delete=models.SET_NULL)
    tags = models.ManyToManyField('Tag', null=True)
    # owner is the Company that owns this partner.
    owner = models.ForeignKey('seo.Company', null=True,
                              on_delete=models.SET_NULL)
    approval_status = models.OneToOneField(
        'mypartners.Status', null=True, verbose_name="Approval Status")

    company_ref = 'owner'
    objects = SearchParameterManager()

    @classmethod
    def _parse_parameters(cls, parameters, records):
        """Used to parse state during `from_search()`."""

        start_date = parameters.pop('start_date', None)
        end_date = parameters.pop('end_date', None)
        state = parameters.pop('state', None)
        city = parameters.pop('city', None)
        contact_type = parameters.pop('contact_type', None)
        tags = parameters.pop('tags__name', None)
        contactrecord_tags = parameters.pop('contactrecord__tags__name', None)

        if tags:
            if not hasattr(tags, '__iter__'):
                tags = [tags]

            for tag in tags:
                records = records.filter(tags__name__icontains=tag)

        if contactrecord_tags:
            if not hasattr(contactrecord_tags, '__iter__'):
                contactrecord_tags = [contactrecord_tags]

            for tag in contactrecord_tags:
                records = records.filter(
                    contactrecord__tags__name__icontains=tag)

        # using a foreign relationship, so can't just filter twice
        if start_date and end_date:
            records = records.filter(contactrecord__date_time__range=[
                start_date, end_date])
        elif start_date:
            records = records.filter(contactrecord__date_time__gte=start_date)
        elif end_date:
            records = records.filter(contactrecord__date_time__lte=end_date)

        if state:
            state_query = models.Q()
            # match state synonyms when querying
            for synonym in synonyms[state.strip().lower()]:
                state_query |= models.Q(
                    contact__locations__state__iexact=synonym)

            records = records.filter(state_query)

        if city:
            records = records.filter(contact__locations__city__icontains=city)

        if contact_type:
            if not hasattr(contact_type, '__iter__'):
                contact_type = [contact_type]

            records = records.filter(
                contactrecord__contact_type__in=contact_type)

        return records

    def __unicode__(self):
        return self.name

    natural_key = __unicode__

    # get_searches_for_partner
    def get_searches(self):
        saved_searches = self.partnersavedsearch_set.all()
        saved_searches = saved_searches.order_by('-created_on')
        return saved_searches

    # get_logs_for_partner
    def get_logs(self, content_type_id=None, num_items=10):
        logs = ContactLogEntry.objects.filter(partner=self)
        if content_type_id:
            logs = logs.filter(content_type_id=content_type_id)
        return logs.order_by('-action_time')[:num_items]

    def get_contact_locations(self):
        """Return a list of unique contact locations as strings."""

        # Unique city and state pairs attached to contacts belonging to this
        # partner.
        locs = Location.objects.filter(
            contacts__in=self.contact_set.all()).exclude(
                contacts__archived_on__isnull=False).values(
                    'city', 'state').distinct().order_by('state', 'city')

        # Convert these city/state pairs into comma separated strings
        return [", ".join(filter(bool, [l['city'], l['state']])) for l in locs]

    # get_contact_records_for_partner
    def get_contact_records(self, contact_name=None, record_type=None,
                            created_by=None, date_start=None, date_end=None,
                            order_by=None, keywords=None, tags=None):

        records = self.contactrecord_set.prefetch_related('tags').all()
        if contact_name:
            records = records.filter(contact__name=contact_name)
        if date_start:
            records = records.filter(date_time__gte=date_start)
        if date_end:
            date_end = date_end + timedelta(1)
            records = records.filter(date_time__lte=date_end)
        if record_type:
            records = records.filter(contact_type=record_type)
        if created_by:
            records = records.filter(created_by=created_by)
        if tags:
            for tag in tags:
                records = records.filter(tags__name__icontains=tag)
        if keywords:
            query = models.Q()
            for keyword in keywords:
                query &= (models.Q(contact_email__icontains=keyword) |
                          models.Q(contact_phone__icontains=keyword) |
                          models.Q(subject__icontains=keyword) |
                          models.Q(notes__icontains=keyword) |
                          models.Q(job_id__icontains=keyword))

            records = records.filter(query)

        if order_by:
            records = records.order_by(order_by)
        else:
            records = records.order_by('-date_time')

        return records

    def get_all_tags(self):
        """Gets unique tags for partner and its contacts"""
        tags = set(self.tags.all())
        tags.update(
            Tag.objects.filter(contact__in=self.contact_set.all()))

        return tags


@receiver(pre_save, sender=Partner, dispatch_uid='pre_save_partner_signal')
def save_partner(sender, instance, **kwargs):
    if not instance.approval_status:
        # TODO: find out how to get a user for approved_by
        # if no relation exists, instance.user will raise an attribute error    
        instance.approval_status = Status.objects.create()


class PartnerLibrary(models.Model):
    """
    Partners curated from the Office of Federal Contract Compliance
    Programs (OFCCP).

    .. note:: For the differences between `state` and `st`, see the ofccp
    module.

    """

    def __init__(self, *args, **kwargs):
        """
        Regular initialization with a custom has_valid_location property.
        Rather than modify the data on import, we mark the location as invalid.
        """

        super(PartnerLibrary, self).__init__(*args, **kwargs)
        self.has_valid_location = self.st.upper() in states.keys()

    # Where the data was pulled from
    data_source = models.CharField(
        max_length=255,
        default='Employment Referral Resource Directory')

    # Organization Info
    name = models.CharField(max_length=255,
                            verbose_name='Partner Organization')
    uri = models.URLField(blank=True)
    region = models.CharField(max_length=30, blank=True)
    # long state name
    state = models.CharField(max_length=30, blank=True)
    area = models.CharField(max_length=255, blank=True)

    # Contact Info
    contact_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    phone_ext = models.CharField(max_length=10, blank=True)
    alt_phone = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=255, blank=True)

    # Location info
    street1 = models.CharField(max_length=255, blank=True)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    # short state name
    st = models.CharField(max_length=10, blank=True)
    zip_code = models.CharField(max_length=12, blank=True)

    # Demographic Info
    is_minority = models.BooleanField('minority', default=False)
    is_female = models.BooleanField('female', default=False)
    is_disabled = models.BooleanField('disabled', default=False)
    is_veteran = models.BooleanField('veteran', default=False)
    is_disabled_veteran = models.BooleanField('disabled_veteran',
                                              default=False)

    def __unicode__(self):
        return self.name

    natural_key = __unicode__

    def save(self, *args, **kwargs):
        self.has_valid_location = self.st.upper() in states.keys()

        super(PartnerLibrary, self).save(*args, **kwargs)


class ContactRecordQuerySet(SearchParameterQuerySet):
    @property
    def communication_activity(self):
        return self.exclude(contact_type='job')

    @property
    def referral_activity(self):
        activity = self.filter(contact_type='job').aggregate(
            applications=models.Sum('job_applications'),
            interviews=models.Sum('job_interviews'),
            hires=models.Sum('job_hires'))

        return {key: int(value or 0) for key, value in activity.items()}

    @property
    def emails(self):
        return self.communication_activity.filter(
            contact_type='email').count()

    @property
    def calls(self):
        return self.communication_activity.filter(
            contact_type='phone').count()

    @property
    def meetings(self):
        return self.communication_activity.filter(
            contact_type='meetingorevent').count()

    @property
    def searches(self):
        return self.communication_activity.filter(
            contact_type='pssemail').count()

    @property
    def applications(self):
        return self.referral_activity['applications']

    @property
    def interviews(self):
        return self.referral_activity['interviews']

    @property
    def hires(self):
        return self.referral_activity['hires']

    @property
    def referrals(self):
        return self.filter(contact_type='job').count()

    @property
    def contacts(self):
        contacts = self.exclude(
            contact_type='job').values(
                'partner__name', 'partner', 'contact__name',
                'contact_email').annotate(
                    records=models.Count('contact__name')).distinct().order_by(
                        '-records')

        referrals = dict(self.filter(contact_type='job').values_list(
            'contact__name').annotate(
                referrals=models.Count('contact__name')).distinct())

        for contact in contacts:
            contact['referrals'] = referrals.get(contact['contact__name'], 0)

        return contacts


class ContactRecordManager(SearchParameterManager):
    def __init__(self, *args, **kwargs):
        super(ContactRecordManager, self).__init__(*args, **kwargs)

    def get_query_set(self):
        return ContactRecordQuerySet(self.model, using=self._db)

    def communication_activity(self):
        return self.get_query_set().communication_activity


class ContactRecord(models.Model):
    """
    Object for Communication Records
    """

    company_ref = 'partner__owner'
    objects = ContactRecordManager()

    created_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    partner = models.ForeignKey(Partner, null=True, on_delete=models.SET_NULL)
    contact = models.ForeignKey(Contact, null=True, on_delete=models.SET_NULL)
    contact_type = models.CharField(choices=CONTACT_TYPE_CHOICES,
                                    max_length=50,
                                    verbose_name="Contact Type")
    # contact type fields, fields required depending on contact_type. Enforced
    # on the form level.
    contact_email = models.CharField(max_length=255,
                                     verbose_name="Contact Email",
                                     blank=True)
    contact_phone = models.CharField(verbose_name="Contact Phone Number",
                                     max_length=30, blank=True, default="")
    location = models.CharField(verbose_name="Meeting Location",
                                max_length=255, blank=True, default="")
    length = models.TimeField(verbose_name="Meeting Length", blank=True,
                              null=True)
    subject = models.CharField(verbose_name="Subject or Topic", max_length=255,
                               blank=True, default="")
    date_time = models.DateTimeField(verbose_name="Date & Time", blank=True)
    notes = models.TextField(max_length=1000,
                             verbose_name='Details, Notes or Transcripts',
                             blank=True, default="")
    job_id = models.CharField(max_length=40, verbose_name='Job Number/ID',
                              blank=True, default="")
    job_applications = models.CharField(max_length=6,
                                        verbose_name="Number of Applications",
                                        blank=True, default="")
    job_interviews = models.CharField(max_length=6,
                                      verbose_name="Number of Interviews",
                                      blank=True, default="")
    job_hires = models.CharField(max_length=6, verbose_name="Number of Hires",
                                 blank=True, default="")
    tags = models.ManyToManyField('Tag', null=True)
    approval_status = models.OneToOneField(
        'mypartners.Status', null=True, verbose_name="Approval Status")

    @classmethod
    def _parse_parameters(cls, parameters, records):
        """Used to parse state during `from_search()`."""

        start_date = parameters.pop('start_date', None)
        end_date = parameters.pop('end_date', None)
        # popping city and state so it doesn't get parsed again
        state = parameters.pop('state', None)
        city = parameters.pop('city', None)
        tags = parameters.pop('tags__name', None)

        if tags:
            if not hasattr(tags, '__iter__'):
                tags = [tags]
            for tag in tags:
                records = records.filter(tags__name__icontains=tag)

        # using a foreign relationship, so can't just filter twice
        if start_date and end_date:
            records = records.filter(date_time__range=[start_date, end_date])
        elif start_date:
            records = records.filter(date_time__gte=start_date)
        elif end_date:
            records = records.filter(date_time__lte=end_date)

        if city or state:
            if state:
                records = records.filter(contact__locations__state=state)

            if city:
                records = records.filter(contact__locations__city=city)

        return records

    def __unicode__(self):
        return "%s Contact Record - %s" % (self.contact_type, self.subject)

    def save(self, *args, **kwargs):
        if not self.pk and self.contact:
            self.contact_email = self.contact_email or self.contact.email
            self.contact_phone = self.contact_phone or self.contact.phone

        super(ContactRecord, self).save(*args, **kwargs)

    def get_record_description(self):
        """
        Generates a human readable description of the contact
        record.

        """
        content_type = ContentType.objects.get_for_model(self.__class__)
        contact_type = dict(CONTACT_TYPE_CHOICES)[self.contact_type]
        if contact_type == 'Email':
            contact_type = 'n email'
        else:
            contact_type = ' %s' % contact_type

        try:
            logs = ContactLogEntry.objects.filter(object_id=self.pk,
                                                  content_type=content_type)
            log = logs.order_by('-action_time')[:1][0]
        except IndexError:
            return ""

        contact_str = "A%s record for %s was %s" % \
                      (contact_type.lower(),
                       self.contact.name, ACTIVITY_TYPES[log.action_flag])

        if log.user:
            user = log.user.email
            if log.user.get_fullname:
                user = log.user.get_full_name()
            contact_str = "%s by %s" % (contact_str, user)

        return contact_str

    def get_human_readable_contact_type(self):
        contact_types = dict(CONTACT_TYPE_CHOICES)
        return contact_types[self.contact_type]

    def get_record_url(self):
        params = {
            'partner': self.partner.pk,
            'id': self.pk,
        }
        query_string = urlencode(params)
        return "%s?%s" % (reverse('record_view'), query_string)

    def shorten_date_time(self):
        return self.date_time.strftime('%b %e, %Y')


@receiver(pre_save, sender=ContactRecord, 
          dispatch_uid='pre_save_contactrecord_signal')
def save_contactrecord(sender, instance, **kwargs):
    if not instance.approval_status:
        # if no relation exists, instance.user will raise an attribute error
        instance.approval_status = Status.objects.create(
            approved_by=instance.created_by)


MAX_ATTACHMENT_MB = 4
S3_CONNECTION = 'S3Connection:s3.amazonaws.com'

def get_file_name(attachment, filename):
    """
    Ensures that a file name is unique before uploading.
    The PRMAttachment instance requires an extra attribute,
    partner (a Partner instance) to be set in order to create the
    file name.

    """
    filename, extension = path.splitext(filename)
    filename = '.'.join([sub(r'[\W]', '', filename),
                         sub(r'[\W]', '', extension)])

    # If the uploaded file only contains invalid characters the end
    # result will be a file named "."
    if not filename or filename == '.':
        filename = 'unnamed_file'

    uid = uuid4()
    path_addon = "mypartners/%s/%s/%s" % (attachment.partner.owner.pk,
                                          attachment.partner.pk, uid)
    name = "%s/%s" % (path_addon, filename)

    # Make sure that in the unlikely event that a filepath/uid/filename
    # combination isn't actually unique a new unique id
    # is generated.
    while default_storage.exists(name):
        uid = uuid4()
        path_addon = "mypartners/%s/%s/%s" % (attachment.partner.owner,
                                              attachment.partner.name, uid)
        name = "%s/%s" % (path_addon, filename)

    return name


class PRMAttachment(models.Model):


    attachment = models.FileField(upload_to=get_file_name, blank=True,
                                  null=True, max_length=767)
    contact_record = models.ForeignKey(ContactRecord, null=True,
                                       on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        instance = super(PRMAttachment, self).save(*args, **kwargs)

        # Confirm that we're not trying to change public/private status of
        # actual files during local testing.
        try:
            if repr(default_storage.connection) == S3_CONNECTION:
                from boto import connect_s3, s3
                conn = connect_s3(settings.AWS_ACCESS_KEY_ID,
                                  settings.AWS_SECRET_KEY)
                bucket = conn.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)
                key = s3.key.Key(bucket)
                key.key = self.attachment.name
                key.set_acl('private')
        except AttributeError:
            pass

        return instance

    def delete(self, *args, **kwargs):
        filename = self.attachment.name
        super(PRMAttachment, self).delete(*args, **kwargs)
        default_storage.delete(filename)


class ContactLogEntry(models.Model):
    action_flag = models.PositiveSmallIntegerField('action flag')
    action_time = models.DateTimeField('action time', auto_now=True)
    change_message = models.TextField('change message', blank=True)
    # A value that can meaningfully (email, name) identify the contact.
    contact_identifier = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    delta = models.TextField(blank=True)
    object_id = models.TextField('object id', blank=True, null=True)
    object_repr = models.CharField('object repr', max_length=200)
    partner = models.ForeignKey(Partner, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    def get_edited_object(self):
        """
        Returns the edited object represented by this log entry

        """
        try:
            return self.content_type.get_object_for_this_type(pk=self.object_id)
        except self.content_type.model_class().DoesNotExist:
            return None

    def get_object_url(self):
        """
        Creates the link that leads to the view/edit view for that object.

        """
        obj = self.get_edited_object()
        if not obj or not self.partner:
            return None
        base_urls = {
            'contact': reverse('edit_contact'),
            'contact record': reverse('record_view'),
            'partner saved search': reverse('partner_edit_search'),
            'partner': reverse('partner_details'),
        }
        params = {
            'partner': self.partner.pk,
            'id': obj.pk,
            'ct': self.content_type.pk,
        }
        query_string = urlencode(params)
        return "%s?%s" % (base_urls[self.content_type.name], query_string)


class Tag(models.Model):
    name = models.CharField(max_length=255)
    hex_color = models.CharField(max_length=6, default="d4d4d4", blank=True)
    company = models.ForeignKey('seo.Company')

    created_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    objects = SearchParameterManager()

    def __unicode__(self):
        return "%s for %s" % (self.name, self.company.name)

    def natural_key(self):
        return self.name

    class Meta:
        unique_together = ('name', 'company')
        verbose_name = "tag"
