from datetime import datetime, timedelta

from django.contrib.auth.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.core.mail import send_mail
from django.db import models, OperationalError, ProgrammingError
from django.db.models.signals import pre_save, post_save
from django.template import Template, Context
from django.utils.translation import ugettext_lazy as _

from myemails.signals import (
    cron_post_save, value_pre_save, value_post_save,  post_add_invoice,
    pre_add_invoice
)
from seo.models import CompanyUser
import tasks


class EmailSection(models.Model):
    SECTION_TYPES = (
        (1, 'Header'),
        (2, 'Body'),
        (3, 'Footer'),
    )

    name = models.CharField(max_length=255)
    owner = models.ForeignKey('seo.Company', blank=True, null=True)
    section_type = models.PositiveIntegerField(choices=SECTION_TYPES)
    content = models.TextField()

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.owner or "Global")


class EmailTemplate(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey('seo.Company', blank=True, null=True)
    header = models.ForeignKey('EmailSection', related_name='header_for')
    body = models.ForeignKey('EmailSection', related_name='body_for')
    footer = models.ForeignKey('EmailSection', related_name='footer_for')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.owner or "Global")

    @staticmethod
    def build_context(for_object):
        """
        Builds context based on a generic number of things that
        a user might want to include in an email.

        Inputs:
        :for_object: The object the context is being built for.
        :return: A dictionary of context for the templates to use.

        """
        context = for_object.context()
        return Context(context)

    def render(self, for_object):
        """
        Renders the EmailTemplate for a given object.

        Inputs:
        :for_object: The object the email is being rendered for.
        :return: The rendered email.
        """
        context = self.build_context(for_object)
        template = Template('\n'.join([self.header.content, self.body.content,
                                       self.footer.content]))
        return template.render(context)


class Event(models.Model):
    email_template = models.ForeignKey('EmailTemplate')
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey('seo.Company')
    sites = models.ManyToManyField('seo.SeoSite')
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.owner)

    class Meta:
        abstract = True

    def schedule_task(self, for_object):
        """
        Creates an EmailTask for the for_object.

        Inputs:
        :for_object: The object that will have an email sent for it
                     in the future.

        Returns:
        :return: The created EamilTask.
        """
        return EmailTask.objects.create(
            act_on=for_object,
            related_event=self,
            scheduled_for=self.schedule_for(for_object)
        )

    def schedule_for(self, for_object):
        """
        Determines what time an event should be scheduled for; Unless
        overridden in a subclass, this defaults to right now.

        Inputs:
        :for_object: Object being scheduled; not used in the default method.

        Returns:
        :return: Time to schedule an event.
        """
        return datetime.now()

    def send_email(self, for_object):
        """
        Sends an email for a for_object.

        Inputs:
        :for_object: The object an email is being sent for.
        """
        subject = ''
        if self.model.model == 'purchasedjob':
            # host company to purchaser
            recipient_company = for_object.owner
            sending_company = for_object.purchased_product.product.owner
        elif self.model.model == 'purchasedproduct':
            # host company to purchaser
            recipient_company = for_object.owner
            sending_company = for_object.product.owner
        elif self.model.model == 'request':
            # purchaser to host company
            recipient_company = for_object.owner
            sending_company = for_object.requesting_company()
            subject = '%s has submitted a new request' % sending_company.name
        elif self.model.model == 'invoice':
            # host company to purchaser
            recipient_company = for_object.purchasedproduct_set.first()\
                .product.owner
            sending_company = for_object.owner
            subject = 'Your invoice from %s' % sending_company.name
        else:
            raise NotImplementedError('Add %s here somewhere!' %
                                      self.model.model)

        if not subject:
            subject = 'An update on your %s' % self.model.name

        recipients = CompanyUser.objects.filter(
            company=recipient_company).values_list('user__email',
                                                   flat=True)
        if hasattr(sending_company, 'companyprofile'):
            email_domain = sending_company.companyprofile.outgoing_email_domain
        else:
            email_domain = 'my.jobs'

        body = self.email_template.render(for_object)
        send_mail(subject, body, '%s@%s' % (self.model.model, email_domain),
                  recipients)


CRON_EVENT_MODELS = ['purchasedjob', 'purchasedproduct']
VALUE_EVENT_MODELS = ['purchasedjob', 'purchasedproduct', 'request']
CREATED_EVENT_MODELS = ['invoice']
ALL_EVENT_MODELS = set().union(CRON_EVENT_MODELS, VALUE_EVENT_MODELS,
                               CREATED_EVENT_MODELS)


class CronEvent(Event):
    model = models.ForeignKey(ContentType,
                              limit_choices_to={'model__in': [
                                  'purchasedjob',
                                  'purchasedproduct']})
    field = models.CharField(max_length=255, blank=True)
    minutes = models.IntegerField()

    def schedule_for(self, for_object):
        """
        Determines what time for_object should be scheduled.

        Inputs:
        :for_object: Object being used to determine send time.

        Returns:
        :return: The next valid time this Event would be scheduled for.
        """
        base_time = getattr(for_object, self.field, datetime.now())
        if base_time is None or base_time == '':
            base_time = datetime.now()
        return base_time + timedelta(minutes=self.minutes)


class ValueEvent(Event):
    COMPARISON_CHOICES = (
        ('eq', 'is equal to'),
        ('ge', 'is greater than or equal to'),
        ('le', 'is less than or equal to'),
    )

    compare_using = models.CharField(_('Comparison Type'),
                                     max_length=255, choices=COMPARISON_CHOICES)
    model = models.ForeignKey(ContentType,
                              limit_choices_to={'model__in': [
                                  'purchasedjob',
                                  'purchasedproduct',
                                  'request']})
    field = models.CharField(max_length=255)
    value = models.PositiveIntegerField()


class CreatedEvent(Event):
    model = models.ForeignKey(ContentType,
                              limit_choices_to={'model__in': [
                                  'invoice'
                              ]})


class EmailTask(models.Model):
    # Object being used to generate this email
    object_id = models.PositiveIntegerField()
    object_model = models.ForeignKey(ContentType, related_name='email_model')
    act_on = GenericForeignKey('object_model', 'object_id')

    # Event type of this email
    event_id = models.PositiveIntegerField()
    event_model = models.ForeignKey(ContentType, related_name='email_type')
    related_event = GenericForeignKey('event_model', 'event_id')

    completed_on = models.DateTimeField(blank=True, null=True)

    scheduled_for = models.DateTimeField(default=datetime.now)
    scheduled_at = models.DateTimeField(auto_now_add=True)

    task_id = models.CharField(max_length=36, blank=True, default='',
                               help_text='guid with dashes')

    @property
    def completed(self):
        return bool(self.completed_on)

    def schedule(self):
        """
        Submits this task to Celery for processing.
        """
        tasks.send_event_email.apply_async(args=[self], eta=self.scheduled_for)

    def send_email(self):
        self.related_event.send_email(self.act_on)
