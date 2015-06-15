from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType
from django.core import mail

from myemails.tests import factories
from myjobs.tests.setup import MyJobsBase
from mysearches.tests.factories import SavedSearchFactory
from postajob.models import PurchasedJob, Invoice
from postajob.tests import factories as posting_factories
from seo.tests.factories import CompanyUserFactory


class EmailTemplateTests(MyJobsBase):
    def test_email_template_render(self):
        product = posting_factories.ProductFactory()
        email_template = factories.EmailTemplateFactory(
            header__content="This is a header. {{product_name}}")
        rendered_email = email_template.render(product)

        # Default email content comes from the
        default_email = 'This is a header. %s\nThis is a body.\n' \
                        'This is a footer.' % product.name
        self.assertEqual(rendered_email, default_email)


class EventTests(MyJobsBase):
    def setUp(self):
        super(EventTests, self).setUp()
        self.product = posting_factories.ProductFactory()
        self.company_user = CompanyUserFactory(company=self.product.owner)

        ct = ContentType.objects.get_for_model(Invoice)
        self.created_event = factories.CreatedEventFactory(
            model=ct, owner=self.product.owner)

        self.purchased_product = posting_factories.PurchasedProductFactory(
            product=self.product, owner=self.product.owner)

    def test_generate_cron_email(self):
        mail.outbox = []
        ct = ContentType.objects.get_for_model(PurchasedJob)
        event = factories.CronEventFactory(
            model=ct, field='max_expired_date',
            owner=self.product.owner
        )
        posting_factories.PurchasedJobFactory(
            purchased_product=self.purchased_product,
            owner=self.product.owner, created_by=self.company_user.user)

        self.assertEqual(len(mail.outbox), 1)
        template = event.email_template
        for part in [template.header, template.body, template.footer]:
            self.assertTrue(part.content in mail.outbox[0].body)

    def test_generate_value_email(self):
        mail.outbox = []
        ct = ContentType.objects.get_for_model(PurchasedJob)
        event = factories.ValueEventFactory(model=ct, field='is_approved',
                                            compare_using='eq', value=1,
                                            owner=self.product.owner)
        job = posting_factories.PurchasedJobFactory(
            purchased_product=self.purchased_product,
            owner=self.product.owner, created_by=self.company_user.user)
        job.is_approved = True
        job.save()
        self.assertEqual(len(mail.outbox), 1)
        template = event.email_template
        for part in [template.header, template.body, template.footer]:
            self.assertTrue(part.content in mail.outbox[0].body)

    def test_generate_created_email(self):
        i = Invoice.objects.get()
        i.purchasedproduct_set.add(self.purchased_product)
        self.assertEqual(len(mail.outbox), 1)
        template = self.created_event.email_template
        for part in [template.header, template.body, template.footer]:
            self.assertTrue(part.content in mail.outbox[0].body)


class CronEventTests(MyJobsBase):
    def setUp(self):
        super(CronEventTests, self).setUp()
        # I'm using SavedSearch for these tests, but you can use any
        # model with a DateTimeField for the "*_with_field" option, and
        # any object for the "*_no_field" option.
        # It might actually be worth using additional object types
        # in future tests.
        yesterday = datetime.now() - timedelta(1)
        self.saved_search = SavedSearchFactory(last_sent=yesterday)

        model = self.saved_search._meta.model
        self.saved_search_contenttype = ContentType.objects.get_for_model(model)
        cron_kwargs = {'model': self.saved_search_contenttype}
        self.cron_event_no_field = factories.CronEventFactory(**cron_kwargs)
        cron_kwargs['field'] = 'last_sent'
        self.cron_event_with_field = factories.CronEventFactory(**cron_kwargs)

    def test_cron_event_schedule_task_no_field(self):
        today = datetime.now().date()
        task = self.cron_event_no_field.schedule_task(self.saved_search)

        self.assertEqual(task.object_id, self.saved_search.id)
        self.assertEqual(task.object_model, self.saved_search_contenttype)
        self.assertEqual(task.related_event, self.cron_event_no_field)
        self.assertEqual(task.scheduled_for.date(), today)
        self.assertEqual(task.scheduled_at.date(), today)
        self.assertIsNone(task.completed_on)

    def test_cron_event_schedule_task_with_field(self):
        yesterday = (datetime.now() - timedelta(1)).date()
        today = datetime.now().date()
        task = self.cron_event_with_field.schedule_task(self.saved_search)

        self.assertEqual(task.object_id, self.saved_search.id)
        self.assertEqual(task.object_model, self.saved_search_contenttype)
        self.assertEqual(task.related_event, self.cron_event_with_field)
        self.assertEqual(task.scheduled_for.date(), yesterday)
        self.assertEqual(task.scheduled_at.date(), today)
        self.assertIsNone(task.completed_on)

    def test_scheduled_for_with_field(self):
        """
        CronEvents that have an associated field should schedule from the
        time contained within the associated field.
        
        """
        tomorrow = datetime.now() + timedelta(1)
        self.saved_search.last_sent = tomorrow
        self.saved_search.save()

        self.cron_event_with_field.minutes = 60*25
        self.cron_event_with_field.save()
        should_be_scheduled_for = (tomorrow + timedelta(1)).date()

        task = self.cron_event_with_field.schedule_task(self.saved_search)
        self.assertEqual(task.scheduled_for.date(), should_be_scheduled_for)

    def test_scheduled_for_no_field(self):
        """
        CronEvents that don't have an associated field should instead be
        scheduled based on the current time.

        """
        self.cron_event_no_field.minutes = 60
        self.cron_event_no_field.save()
        should_be_scheduled_for = datetime.now() + timedelta(minutes=60)
        should_be_scheduled_for = should_be_scheduled_for.date()

        task = self.cron_event_no_field.schedule_task(self.saved_search)
        self.assertEqual(task.scheduled_for.date(), should_be_scheduled_for)