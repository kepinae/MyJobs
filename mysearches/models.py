from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from pynliner import Pynliner
from urlparse import urlparse

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
import uuid

from myjobs.models import User
from mypartners.models import Contact, ContactRecord, Partner, EMAIL
from mysearches.helpers import (parse_feed, update_url_if_protected,
                                url_sort_options, validate_dotjobs_url)
import mypartners.helpers
from universal.helpers import send_email


FREQUENCY_CHOICES = (
    ('D', _('Daily')),
    ('W', _('Weekly')),
    ('M', _('Monthly')))

DOM_CHOICES = [(i, i) for i in range(1, 31)]
DOW_CHOICES = (('1', _('Monday')),
               ('2', _('Tuesday')),
               ('3', _('Wednesday')),
               ('4', _('Thursday')),
               ('5', _('Friday')),
               ('6', _('Saturday')),
               ('7', _('Sunday')))

JOBS_PER_EMAIL_CHOICES = [(5, 5)] + [(i, i) for i in range(10, 101, 10)]

CONTENT_TYPES = {}


class SavedSearch(models.Model):

    SORT_CHOICES = (('Relevance', _('Relevance')),
                    ('Date', _('Date')))

    # User can be null on PartnerSavedSearch. As South doesn't like custom
    # on_delete handlers and I'm not sure when 1.7 is coming, the actual
    # decision on setting this to null or cascading the delete is done
    # in the delete_user pre_delete signal defined in myjobs/models.py.
    user = models.ForeignKey('myjobs.User', editable=False, null=True,
                             on_delete=models.DO_NOTHING)

    created_on = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=60, verbose_name=_("Search Name"))
    url = models.URLField(max_length=300,
                          verbose_name=_("URL of Search Results"))
    sort_by = models.CharField(max_length=9, choices=SORT_CHOICES,
                               default='Relevance', verbose_name=_("Sort by"))
    feed = models.URLField(max_length=300)
    is_active = models.BooleanField(default=True,
                                    verbose_name=_("Search is Active"))
    email = models.EmailField(max_length=255,
                              verbose_name=_("Which Email Address"))
    frequency = models.CharField(max_length=2, choices=FREQUENCY_CHOICES,
                                 default='W',
                                 verbose_name=_("Frequency"))
    day_of_month = models.IntegerField(choices=DOM_CHOICES,
                                       blank=True, null=True,
                                       verbose_name=_("on"))
    day_of_week = models.CharField(max_length=2, choices=DOW_CHOICES,
                                   blank=True, null=True,
                                   verbose_name=_("on"))
    jobs_per_email = models.PositiveSmallIntegerField(
        default=5, choices=JOBS_PER_EMAIL_CHOICES,
        verbose_name=_("Jobs per Email"))
    notes = models.TextField(blank=True, null=True,
                             verbose_name=_("Comments"))
    last_sent = models.DateTimeField(blank=True, null=True, editable=False)

    # Custom messages were created for PartnerSavedSearches
    custom_message = models.TextField(max_length=300, blank=True, null=True)

    @property
    def content_type(self):
        """
        Determines the content type for self and stores it. Handles both
        SavedSearch and PartnerSavedSearch.

        Outputs:
            Primary key of the calculated content type
        """
        if hasattr(self, 'partnersavedsearch'):
            if 'pss' not in CONTENT_TYPES:
                CONTENT_TYPES['pss'] = ContentType.objects.get_for_model(
                    PartnerSavedSearch).pk
            return CONTENT_TYPES['pss']
        else:
            if 'ss' not in CONTENT_TYPES:
                CONTENT_TYPES['ss'] = ContentType.objects.get_for_model(
                    SavedSearch).pk
            return CONTENT_TYPES['ss']

    def get_company(self):
        """
        Attempts to match the feed url to an SeoSite and then determine the
        owner of that SeoSite.

        """
        from seo.models import SeoSite
        netloc = urlparse(self.feed).netloc
        try:
            site = SeoSite.objects.get(domain__iexact=netloc)
            return site.get_companies()[0].pk
        except (SeoSite.DoesNotExist, SeoSite.MultipleObjectsReturned,
                IndexError):
            # No match was found, so make the company DirectEmployers.
            return 999999

    def get_verbose_frequency(self):
        for choice in FREQUENCY_CHOICES:
            if choice[0] == self.frequency:
                return choice[1]

    def get_verbose_dow(self):
        for choice in DOW_CHOICES:
            if choice[0] == self.day_of_week:
                return choice[1]

    def get_feed_items(self, num_items=None):
        num_items = num_items or self.jobs_per_email
        url_of_feed = url_sort_options(self.feed, self.sort_by, self.frequency,
                                       hasattr(self, 'partnersavedsearch'))
        url_of_feed = update_url_if_protected(url_of_feed, self.user)
        parse_feed_args = {
            'feed_url': url_of_feed,
            'frequency': self.frequency,
            'num_items': num_items,
            'return_items': num_items,
            'last_sent': self.last_sent
        }
        if hasattr(self, 'partnersavedsearch'):
            parse_feed_args['ignore_dates'] = True
        items = parse_feed(**parse_feed_args)
        return items

    def send_email(self, custom_msg=None, additional_categories=None,
                   additional_headers=None):
        log_kwargs = {
            'was_sent': False,
            'was_received': False,
            'recipient': self.user,
            'recipient_email': self.email,
            'new_jobs': 0,
            'backfill_jobs': 0,
            'uuid': uuid.uuid4().hex
        }
        if self.user.can_receive_myjobs_email():
            items, count = self.get_feed_items()
            is_pss = hasattr(self, 'partnersavedsearch')
            if items or is_pss:
                log_kwargs['was_sent'] = True
                if is_pss:
                    extras = self.partnersavedsearch.url_extras
                    if extras:
                        mypartners.helpers.add_extra_params_to_jobs(items,
                                                                    extras)
                        self.url = mypartners.helpers.add_extra_params(self.url,
                                                                       extras)
                if self.custom_message and not custom_msg:
                    custom_msg = self.custom_message

                context_dict = {'saved_searches': [(self, items, count)],
                                'custom_msg': custom_msg,
                                'contains_pss': is_pss}
                message = render_to_string('mysearches/email_single.html',
                                           context_dict)
                categories = [('My.jobs Saved Search Sent '
                               '({content_type}:{pk}|{uuid})').format(
                                   content_type=self.content_type,
                                   pk=self.pk, uuid=log_kwargs['uuid']),
                              settings.ENVIRONMENT]

                # additional_categories and additional_headers are used when
                # sending email from qc/staging to stop SendGrid's url
                # redirection and to enable us to drop events that we shouldn't
                # be processing (QC emails getting posted to Production)
                if additional_categories is not None:
                    categories.extend(
                        additional_categories if isinstance(
                            additional_categories, list)
                        else [additional_categories])
                categories = ['"%s"' % category for category in categories]
                category = '[%s]' % ','.join(categories)
                header = ['"category": ' + category]
                if additional_headers is not None:
                    header.extend(
                        additional_headers if isinstance(
                            additional_headers, list)
                        else [additional_headers])
                header = '{%s}' % (','.join(header), )
                headers = {'X-SMTPAPI': header}

                send_email(message, email_type=settings.SAVED_SEARCH,
                           recipients=[self.email], label=self.label.strip(),
                           headers=headers)

                self.last_sent = datetime.now()
                self.save()

                if is_pss:
                    record = self.partnersavedsearch.create_record(custom_msg)
                    log_kwargs['contact_record'] = record
                    log_kwargs['new_jobs'] = len([item for item in items
                                                 if item.get('new')])
                    log_kwargs['backfill_jobs'] = count - log_kwargs['new_jobs']

                else:
                    log_kwargs['new_jobs'] = count
                    log_kwargs['backfill_jobs'] = 0
            else:
                log_kwargs['reason'] = 'No jobs'
        else:
            log_kwargs['reason'] = "User can't receive MyJobs email"
        SavedSearchLog.objects.create(**log_kwargs)

    def initial_email(self, custom_msg=None, send=True):
        """
        Generates the body for an initial saved search notification and returns
        it or sends it in an email based on the opt in status of the user.

        Inputs:
        :custom_msg: Custom message to be added when manually resending an
            initial email
        :send: Denotes if we should send the generated email (True) or return
            the body (False). If False, the body will be used in an invitation.
            Default: True

        Outputs:
        :message: Generated email body (if :send: is False) or None
        """
        log_kwargs = {
            'reason': 'Jobs are not sent in initial saved search emails',
            'was_sent': False,
            'was_received': False,
            'recipient': self.user,
            'recipient_email': self.email,
            'new_jobs': 0,
            'backfill_jobs': 0,
            'uuid': uuid.uuid4().hex
        }
        message = None
        if self.user.opt_in_myjobs:
            # Even if send=False, this will still get sent; send=False currently
            # means the generated email body will be used in an invitation.
            log_kwargs['was_sent'] = True
            context_dict = {'saved_searches': [(self,)],
                            'custom_msg': custom_msg,
                            'contains_pss': hasattr(self, 'partnersavedsearch')}
            message = render_to_string("mysearches/email_initial.html",
                                       context_dict)
            message = Pynliner().from_string(message).run()

            if send:
                category = ('{"category": "My.jobs Saved Search Created '
                            '(%s:%s|%s)"}') % (
                                self.content_type,
                                self.pk,
                                log_kwargs['uuid'])
                headers = {'X-SMTPAPI': category}
                send_email(message, email_type=settings.SAVED_SEARCH_INITIAL,
                           recipients=[self.email], label=self.label.strip(),
                           headers=headers)
        else:
            log_kwargs['reason'] = "User can't receive MyJobs email"
        SavedSearchLog.objects.create(**log_kwargs)

        if not send:
            return message

    def send_update_email(self, msg, custom_msg=None):
        """
        This function is meant to be called from the shell. It sends a notice to
        the user that their saved search has been updated by the system or an
        admin.

        Inputs:
        :msg:   The description of the update. Passed through verbatim to the
                template.

        Returns:
        nothing

        """
        context_dict = {
            'saved_searches': [(self,)],
            'message': msg,
            'custom_msg': custom_msg,
            'contains_pss': hasattr(self, 'partnersavedsearch')
        }
        message = render_to_string("mysearches/email_update.html",
                                   context_dict)

        category = '{"category": "My.jobs Saved Search Updated (%s:%s)"}' % (
            self.content_type,
            self.pk)
        headers = {'X-SMTPAPI': category}
        send_email(message, email_type=settings.SAVED_SEARCH_UPDATED,
                   recipients=[self.email], label=self.label.strip(),
                   headers=headers)
        SavedSearchLog.objects.create(
            reason='Jobs are not sent in saved search update emails',
            was_sent=True, was_received=False, recipient=self.user,
            recipient_email=self.email, new_jobs=0, backfill_jobs=0)

    def create(self, *args, **kwargs):
        """
        On creation, check if that same URL exists for the user and raise
        validation if it's a duplicate.
        """

        duplicates = SavedSearch.objects.filter(user=self.user, url=self.url)

        if duplicates:
            raise ValidationError('Saved Search URLS must be unique.')
        super(SavedSearch, self).create(*args, **kwargs)

    def save(self, *args, **kwargs):
        """"
        Create a new saved search digest if one doesn't exist yet
        """

        if self.user and not SavedSearchDigest.objects.filter(user=self.user):
            # Since user can be null on SavedSearch but not SavedSearchDigest,
            # we need to ensure that a user exists before trying to use it.
            SavedSearchDigest.objects.create(user=self.user, email=self.email)

        super(SavedSearch, self).save(*args, **kwargs)

    def __unicode__(self):
        if hasattr(self, 'user') and self.user is not None:
            return "Saved Search %s for %s" % (self.url, self.user.email)
        else:
            return "Saved Search %s for %s" % (self.url, self.email)

    class Meta:
        verbose_name_plural = "saved searches"

    def disable_or_fix(self):
        """
        Disables or fixes this saved search based on the presence or lack of an
        rss feed on the search url. Sends a "search has been disabled" email
        if this is not fixable.
        """
        try:
            _, feed = validate_dotjobs_url(self.url, self.user)
        except ValueError:
            feed = None

        if feed is None:
            # search url did not contain an rss link and is not valid
            self.is_active = False
            self.save()
            self.send_disable_email()
        elif self.feed == '':
            # search url passed validation in the past even though there was
            # an issue retrieving the page; update the feed url
            self.feed = feed
            self.save()

    def send_disable_email(self):
        message = render_to_string('mysearches/email_disable.html',
                                   {'saved_search': self})

        category = '{"category": "My.jobs Saved Search Disabled (%s:%s)"}' % (
            self.content_type,
            self.pk)
        headers = {'X-SMTPAPI': category}
        send_email(message, email_type=settings.SAVED_SEARCH_DISABLED,
                   recipients=[self.email], headers=headers)


class SavedSearchDigest(models.Model):
    is_active = models.BooleanField(default=False)
    user = models.OneToOneField('myjobs.User', editable=False)
    email = models.EmailField(max_length=255)
    frequency = models.CharField(max_length=2, choices=FREQUENCY_CHOICES,
                                 default='D',
                                 verbose_name=_("How often:"))
    day_of_month = models.IntegerField(choices=DOM_CHOICES,
                                       blank=True, null=True,
                                       verbose_name=_("on"))
    day_of_week = models.CharField(max_length=2, choices=DOW_CHOICES,
                                   blank=True, null=True,
                                   verbose_name=_("on"))

    # For now, emails will only be sent if they have searches; When this
    # functionality is added, remove `editable=False` to show this option on
    # the form
    send_if_none = models.BooleanField(default=False,
                                       verbose_name=_("Send even if there are"
                                                      " no results"),
                                       editable=False)

    @property
    def content_type(self):
        """
        Determines and stores the content type for saved search digests.

        Outputs:
            Primary key for the saved search digest content type
        """
        if 'ssd' not in CONTENT_TYPES:
            CONTENT_TYPES['ssd'] = ContentType.objects.get_for_model(
                SavedSearchDigest).pk
        return CONTENT_TYPES['ssd']

    def send_email(self, custom_msg=None):
        log_kwargs = {
            'was_sent': False,
            'was_received': False,
            'recipient': self.user,
            'recipient_email': self.email,
            'new_jobs': 0,
            'backfill_jobs': 0,
            'uuid': uuid.uuid4().hex
        }
        total_jobs = 0
        saved_searches = self.user.savedsearch_set.filter(is_active=True)
        search_list = []
        contains_pss = False
        for search in saved_searches:
            items, count = search.get_feed_items()
            total_jobs += count
            pss = None
            if hasattr(search, 'partnersavedsearch'):
                pss = search.partnersavedsearch
            elif isinstance(search, PartnerSavedSearch):
                pss = search

            if pss is not None:
                # New jobs will have a "new" key in their job dictionaries.
                # We can count the number that do not
                log_kwargs['backfill_jobs'] += len([item for item in items
                                                    if not item.get('new')])
                log_kwargs['new_jobs'] += count - log_kwargs['backfill_jobs']
                contains_pss = True
                extras = pss.url_extras
                if extras:
                    mypartners.helpers.add_extra_params_to_jobs(items, extras)
                    search.url = mypartners.helpers.add_extra_params(search.url,
                                                                     extras)
                pss.create_record(custom_msg)
            search_list.append((search, items, count))

        saved_searches = [(search, items, count)
                          for search, items, count in search_list
                          if (items or hasattr(search, 'partnersavedsearch'))]

        if self.user.can_receive_myjobs_email() and saved_searches:
            log_kwargs['was_sent'] = True
            context_dict = {
                'saved_searches': saved_searches,
                'digest': self,
                'custom_msg': custom_msg,
                'contains_pss': contains_pss
            }
            message = render_to_string('mysearches/email_digest.html',
                                       context_dict)
            category = '{"category": "My.jobs Saved Search Digest Send (%s:%s:%s:%s)"}' % (
                self.content_type,
                self.pk,
                ','.join([str(search[0].pk) for search in saved_searches]),
                log_kwargs['uuid'])
            headers = {'X-SMTPAPI': category}
            send_email(message, email_type=settings.SAVED_SEARCH_DIGEST,
                       recipients=[self.email], headers=headers)

            sent_search_kwargs = {
                'pk__in': [search[0].pk for search in saved_searches]
            }
            searches_sent = SavedSearch.objects.filter(**sent_search_kwargs)
            searches_sent.update(last_sent=datetime.now())
        else:
            if not saved_searches:
                log_kwargs['reason'] = ("No saved searches or saved searches "
                                        "have no jobs")
            else:
                log_kwargs['reason'] = "User can't receive MyJobs email"
        SavedSearchLog.objects.create(**log_kwargs)

    def disable_or_fix(self):
        """
        Calls SavedSearch.disable_or_fix for each saved search associated
        with the owner of this digest.
        """
        for search in self.user.savedsearch_set.filter(is_active=True):
            search.disable_or_fix()


class PartnerSavedSearch(SavedSearch):
    """
    Partner Saved Search (PSS) is a subclass of SavedSearch. PSSs' emails are
    sent out as if it is a SavedSearch. When a PSS is created a SavedSearch
    is also created and is attached to the User. Then the PSS is connected via
    a OneToOne relationship to the SavedSearch. Only way to access a PSS from a
    User is SavedSearch.partnersavedsearch.

    """
    provider = models.ForeignKey('seo.Company')
    partner = models.ForeignKey(Partner)
    url_extras = models.CharField(max_length=255, blank=True,
                                  help_text="Anything you put here will be "
                                            "added as query string parameters "
                                            "to each of links in the saved "
                                            "search.")
    partner_message = models.TextField(
        blank=True, help_text="Use this field to provide a customized "
                              "greeting that will be sent with each copy "
                              "of this saved search.")
    unsubscribed = models.BooleanField(default=False)
    tags = models.ManyToManyField('mypartners.Tag', null=True)
    created_by = models.ForeignKey(User, editable=False,
                                   related_name='created_by',
                                   on_delete=models.SET_NULL,
                                   null=True)
    unsubscriber = models.EmailField(max_length=255, blank=True, editable=False,
                                     verbose_name='Unsubscriber')

    def save(self, *args, **kwargs):
        if hasattr(self, 'changed_data') and hasattr(self, 'request'):
            # This save was initiated by a form. Update unsubscriber and send
            # notifications as appropriate.
            if 'is_active' in self.changed_data and self.pk:
                if self.is_active:
                    self.unsubscriber = ''
                    self.unsubscribed = False
                else:
                    self.unsubscriber = self.request.user.email
                    self.unsubscribed = True
                    self.user.send_opt_out_notifications([self])
        super(PartnerSavedSearch, self).save(*args, **kwargs)

    def initial_email(self, custom_msg=None, send=True):
        """
        Calls the base initial_email function and then creates a record of it.
        """
        body = super(PartnerSavedSearch, self).initial_email(custom_msg,
                                                             send)
        change_msg = "Automatic sending of initial partner saved search."
        self.create_record(change_msg, body)
        return body

    def send_update_email(self, msg, custom_msg=None):
        super(PartnerSavedSearch, self).send_update_email(msg, custom_msg)
        change_msg = "Automatic sending of updated partner saved search."
        self.create_record(change_msg)

    def create_record(self, change_msg=None, body=None):
        """
        Creates a record of this saved search being sent. Records the contents
        of :body: if present, otherwise generates the body for a single saved
        search and records it.

        Inputs:
        :change_msg: Custom message to be added on manual send. Default: None
        :body: Text to be added to this record. Default: None
        """
        subject = self.label.strip()
        if change_msg is None:
            change_msg = "Automatic sending of partner saved search."

        if not body:
            items, count = self.get_feed_items()
            extras = self.partnersavedsearch.url_extras
            if extras:
                mypartners.helpers.add_extra_params_to_jobs(items, extras)
                self.url = mypartners.helpers.add_extra_params(self.url, extras)

            custom_msg = self.custom_message if self.custom_message else ''
            context_dict = {
                'saved_searches': [(self, items, count)],
                'custom_msg': custom_msg,
                'contains_pss': True
            }
            body = render_to_string('mysearches/email_single.html',
                                    context_dict)

        contact = Contact.objects.filter(partner=self.partner,
                                         user=self.user).first()
        record = ContactRecord.objects.create(
            partner=self.partner,
            contact_type='pssemail',
            contact=contact,
            contact_email=self.user.email,
            created_by=self.created_by,
            date_time=datetime.now(),
            subject=subject,
            notes=body,
        )
        record.tags.add(*self.tags.all())
        mypartners.helpers.log_change(record, None, None, self.partner,
                                      self.user.email, action_type=EMAIL,
                                      change_msg=change_msg)
        return record


class SavedSearchLog(models.Model):
    was_sent = models.BooleanField(default=False)
    was_received = models.BooleanField(default=False,
                                       help_text=("If date_sent is very "
                                       "recent and was_received is unchecked, "
                                       "SendGrid may not have responded yet - "
                                       "give it a few minutes."))
    reason = models.TextField()
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recipient_email = models.EmailField(max_length=255, blank=False)
    new_jobs = models.IntegerField()
    backfill_jobs = models.IntegerField()
    date_sent = models.DateTimeField(auto_now_add=True)
    contact_record = models.ForeignKey('mypartners.ContactRecord', null=True,
                                       blank=True, on_delete=models.SET_NULL)
    uuid = models.CharField(max_length=32, db_index=True)
