import boto
from datetime import date, timedelta, datetime
from itertools import chain, izip_longest
import json
import logging
import newrelic.agent
import os
import pysolr
import sys
import traceback
from urllib2 import HTTPError, URLError
import urlparse
import uuid

from celery import group
from celery.task import task

from django.conf import settings
from django.contrib.sitemaps import ping_google
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.urlresolvers import reverse_lazy
from django.template.loader import render_to_string
from django.db.models import Q

from seo.models import Company, SeoSite, BusinessUnit
from myjobs.models import EmailLog, User, STOP_SENDING, BAD_EMAIL
from myjobs.helpers import log_to_jira
from mymessages.models import Message
from mysearches.models import SavedSearch, SavedSearchDigest, SavedSearchLog
from mypartners.models import PartnerLibrary
from mypartners.helpers import get_library_partners
import import_jobs
from postajob.models import Job
from registration.models import ActivationProfile
from solr import helpers
from solr.models import Update
from solr.signals import object_to_dict, profileunits_to_dict


logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = "/de/data/"
sys.path.insert(0, os.path.join(BASE_DIR))
sys.path.insert(0, os.path.join(BASE_DIR, '../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
FEED_FILE_PREFIX = "dseo_feed_"
PARTNER_LIBRARY_SOURCES = {
    # http://www.dol-esa.gov/errd/index.html
    'Employment Referral Resource Directory': {
        'url': 'http://www.dol-esa.gov/errd/getexcel.jsp?op=1',
        'params': {
            'sel': 'ALL',
            'subreg': 'Download'
        }
    },
    #  http://www.dol-esa.gov/errd/Resources.503VEVRAA.html
    'Disability and Veterans Community Resources Directory': {
        'url': 'http://www.dol-esa.gov/errd/resourcequery.jsp',
        'params': {
            'returnformat': 'excel',
            'formname': 'downloadreg',
            'reg': 'ALL',
            'subreg': 'Download'
        }
    }
}


@task(name='tasks.send_search_digest', ignore_result=True,
      default_retry_delay=180, max_retries=2, bind=True)
def send_search_digest(self, search):
    """
    Task used by send_send_search_digests to send individual digest or search
    emails.

    Inputs:
    :search: SavedSearch or SavedSearchDigest instance to be mailed
    """
    try:
        search.send_email()
    except (ValueError, URLError, HTTPError) as e:
        if self.request.retries < 2:  # retry sending email twice
            raise send_search_digest.retry(arg=[search], exc=e)
        else:
            # After the initial try and two retries, disable the offending
            # saved search
            search.disable_or_fix()


@task(name='tasks.update_partner_library', ignore_result=True,
      default_retry_delay=180, max_retries=2)
def update_partner_library():

    for source, data in PARTNER_LIBRARY_SOURCES.items():
        print "Connecting to %s...." % source
        print "Parsing data for PartnerLibrary information..."

        added = skipped = 0
        for partner in get_library_partners(data['url'], data['params']):
            # the second join + split take care of extra internal whitespace
            fullname = " ".join(" ".join([partner.first_name,
                                          partner.middle_name,
                                          partner.last_name]).split())
            emails = [email.strip()
                      for email in partner.email_id.split(';', 1)]

            for email in emails:
                # disambiguate records by source, contact name, and address
                if not PartnerLibrary.objects.filter(data_source=source,
                                                     contact_name=fullname,
                                                     st=partner.st,
                                                     city=partner.city,
                                                     email=email).exists():
                    PartnerLibrary.objects.create(
                        data_source=source,
                        name=partner.organization_name,
                        uri=partner.website,
                        region=partner.region,
                        state=partner.state,
                        area=partner.area,
                        contact_name=fullname,
                        phone=partner.phone,
                        phone_ext=partner.phone_ext,
                        alt_phone=partner.alt_phone,
                        fax=partner.fax,
                        email=email,
                        street1=partner.street1,
                        street2=partner.street2,
                        city=partner.city,
                        st=partner.st,
                        zip_code=partner.zip_code,
                        is_minority=partner.minority,
                        is_female=partner.female,
                        is_disabled=partner.disabled,
                        is_disabled_veteran=partner.disabled_veteran,
                        is_veteran=partner.veteran)
                    added += 1
                else:
                    skipped += 1

        print "%d records added and %d records skipped from '%s.\n" % (
            added, skipped, source)


@task(name='tasks.send_search_digests', ignore_result=True)
def send_search_digests():
    """
    Daily task to send saved searches. If user opted in for a digest, they
    receive it daily and do not get individual saved search emails. Otherwise,
    each active saved search is sent individually.
    """

    def filter_by_time(qs):
        """
        Filters the provided query set for emails that should be sent today

        Inputs:
        :qs: query set to be filtered

        Outputs:
        :qs: filtered query set containing today's outgoing emails
        """
        today = datetime.today()
        day_of_week = today.isoweekday()

        daily = qs.filter(frequency='D')
        weekly = qs.filter(frequency='W', day_of_week=str(day_of_week))
        monthly = qs.filter(frequency='M', day_of_month=today.day)
        return chain(daily, weekly, monthly)

    digests = SavedSearchDigest.objects.filter(is_active=True,
                                               user__opt_in_myjobs=True,
                                               user__is_disabled=False)
    digests = filter_by_time(digests)
    for obj in digests:
        send_search_digest.s(obj).apply_async()

    not_digest = SavedSearchDigest.objects.filter(is_active=False,
                                                  user__opt_in_myjobs=True,
                                                  user__is_disabled=False)
    for item in not_digest:
        saved_searches = item.user.savedsearch_set.filter(is_active=True)
        saved_searches = filter_by_time(saved_searches)
        for search_obj in saved_searches:
            send_search_digest.s(search_obj).apply_async()


@task(name='task.delete_inactive_activations', ignore_result=True)
def delete_inactive_activations():
    """
    Daily task checks if activation keys are expired and deletes them.
    Disabled users are exempt from this check.
    """

    for profile in ActivationProfile.objects.all():
        try:
            if profile.activation_key_expired():
                user = profile.user
                if not user.is_disabled and not user.is_verified:
                    user.delete()
                    profile.delete()
        except User.DoesNotExist:
            profile.delete()


@task(name='tasks.process_user_events', ignore_result=True)
def process_user_events(email):
    """
    Processes all email events for a given user.
    """
    user = User.objects.get_email_owner(email=email)
    logs = EmailLog.objects.filter(email=email,
                                   processed=False).order_by('-received')
    newest_log = logs[0]

    filter_by_event = lambda x: [log for log in logs if log.event in x]

    # The presence of deactivate or stop_sending determines what kind (if any)
    # of My.jobs message the user will receive. deactivate takes precedence.
    # The logs query set has already been evaluated, so the only overhead
    # is the list comprehension
    deactivate = filter_by_event(BAD_EMAIL)
    stop_sending = filter_by_event(STOP_SENDING)
    update_fields = []
    if user:
        if (deactivate or stop_sending) and user.opt_in_myjobs:
            user.opt_in_myjobs = False
            if deactivate:
                user.is_verified = False
                user.deactivate_type = deactivate[0].event
                update_fields.append('is_verified')
                body = ('<b>Warning</b>: Attempts to send messages to {email} '
                        'have failed. Please check your email address in your '
                        '<a href="{{settings_url}}">'
                        'account settings</a>.').format(
                            email=deactivate[0].email)
            else:
                user.deactivate_type = stop_sending[0].event
                body = ('<b>Warning</b>: We have received a request to stop '
                        'communications with {email}. If this was in error, '
                        'please opt back into emails in your '
                        '<a href="{{settings_url}}">'
                        'account settings</a>.').format(
                            email=stop_sending[0].email)
            body = body.format(settings_url=reverse_lazy('edit_account'))
            Message.objects.create_message(users=user, subject='', body=body)
            update_fields.extend(['deactivate_type',
                                  'opt_in_myjobs'])

        if user.last_response < newest_log.received:
            user.last_response = newest_log.received
            update_fields.append('last_response')

        # If update_fields is an empty iterable, the save is aborted
        # This doesn't hit the DB unless a field has changed
        user.save(update_fields=update_fields)

    logs.update(processed=True)


@task(name='tasks.process_batch_events', ignore_result=True)
def process_batch_events():
    """
    Processes all events that have accumulated over the last day, sends emails
    to inactive users, and disables users who have been inactive for a long
    period of time.
    """
    now = date.today()
    EmailLog.objects.filter(received__lte=now-timedelta(days=60),
                            processed=True).delete()

    emails = set(EmailLog.objects.values_list('email', flat=True).filter(
        processed=False))

    result = group(process_user_events.subtask((email, ))
                   for email in emails).apply()
    result.join()

    # These users have not responded in a month. Send them an email if they
    # own any saved searches
    inactive = User.objects.select_related('savedsearch_set')
    inactive = inactive.filter(Q(last_response=now-timedelta(days=172)) |
                               Q(last_response=now-timedelta(days=179)))

    category = '{"category": "User Inactivity (%s)"}'
    for user in inactive:
        if user.savedsearch_set.exists():
            time = (now - user.last_response).days
            message = render_to_string('myjobs/email_inactive.html',
                                       {'user': user,
                                        'time': time})

            site = user.registration_source()
            headers = {'X-SMTPAPI': category}
            user.email_user(message, email_type=settings.INACTIVITY, site=site,
                            headers=headers)

    # These users have not responded in 90 days. Stop sending emails.
    users = User.objects.filter(last_response__lte=now-timedelta(days=180))
    users.update(opt_in_myjobs=False)


@task(name="tasks.update_solr_from_model", ignore_result=True)
def update_solr_task(solr_location=None):
    """
    Deletes all items scheduled for deletion, and then adds all items
    scheduled to be added to solr.

    Inputs:
    :solr_location: Dict of separate cores to be updated
    """
    if hasattr(mail, 'outbox'):
        solr_location = settings.TEST_SOLR_INSTANCE
    elif solr_location is None:
        solr_location = settings.SOLR
    objs = Update.objects.filter(delete=True).values_list('uid', flat=True)

    if objs:
        objs = split_list(objs, 1000)
        for obj_list in objs:
            obj_list = filter(None, list(obj_list))
            uid_list = " OR ".join(obj_list)
            for location in solr_location.values():
                solr = pysolr.Solr(location)
                solr.delete(q="uid:(%s)" % uid_list)
        Update.objects.filter(delete=True).delete()

    objs = Update.objects.filter(delete=False)
    updates = []

    for obj in objs:
        content_type, key = obj.uid.split("##")
        model = ContentType.objects.get_for_id(content_type).model_class()
        if model == SavedSearch:
            search = model.objects.get(pk=key)
            # Saved search recipients can currently be null; Displaying these
            # searches may be implemented in the future but will likely require
            # some template work.
            if search.user:
                updates.append(object_to_dict(model, search))
        # If the user is being updated, because the user is stored on the
        # SavedSearch document, every SavedSearch belonging to that user
        # also has to be updated.
        elif model == User:
            searches = SavedSearch.objects.filter(user_id=key)
            [updates.append(object_to_dict(SavedSearch, s)) for s in searches]
            updates.append(object_to_dict(model, model.objects.get(pk=key)))
        else:
            updates.append(profileunits_to_dict(key))

    updates = split_list(updates, 1000)
    for location in solr_location.values():
        solr = pysolr.Solr(location)
        for update_subset in updates:
            update_subset = filter(None, list(update_subset))
            solr.add(list(update_subset))
    objs.delete()


def split_list(l, list_len, fill_val=None):
    """
    Splits a list into sublists.

    inputs:
    :l: The list to be split.
    :list_len: The length of the resulting lists.
    :fill_val: The value that is inserted when there are less items in the
        final list than list_len.

    outputs:
    A generator of tuples size list_len.

    """
    args = [iter(l)] * list_len
    return izip_longest(fillvalue=fill_val, *args)


@task(name="tasks.reindex_solr", ignore_result=True)
def task_reindex_solr(solr_location=None):
    """
    Adds all ProfileUnits, Users, and SavedSearches to solr.

    Inputs:
    :solr_location: Dict of separate cores to be updated (Optional);
        defaults to the default instance from settings
    """
    if solr_location is None:
        solr_location = settings.SOLR
    l = []

    u = User.objects.all().values_list('id', flat=True)
    for x in u:
        l.append(profileunits_to_dict(x))

    s = SavedSearch.objects.filter(user__isnull=False)
    for x in s:
        saved_search_dict = object_to_dict(SavedSearch, x)
        saved_search_dict['doc_type'] = 'savedsearch'
        l.append(saved_search_dict)

    u = User.objects.all()
    for x in u:
        l.append(object_to_dict(User, x))

    l = split_list(l, 1000)

    for location in solr_location.values():
        solr = pysolr.Solr(location)
        for x in l:
            x = filter(None, list(x))
            solr.add(x)


def parse_log(logs, solr_location):
    """
    Turns a list of boto keys into a list of dicts, with each dict representing
    a line from the keys

    Inputs:
    :logs: List of logs generated by boto that reference files on s3
        Lines in analytics logs are formatted as follows:
            %{%Y-%m-%d %H:%M:%S}t %a %m %U %q %H %s %{Referer}i %{aguid}C
                %{myguid}C %{user-agent}i
        Lines in redirect logs are formatted slightly differently:
            %{%Y-%m-%d %H:%M:%S}t %a %m %U %{X-REDIRECT}o %p %u %{X-Real-IP}i
                %H "%{User-agent}i" %{r.my.jobs}C %{Referer}i %V %>s %O %I %D

    :solr_location: Dict of separate cores to be updated (Optional);
        defaults to the default instance from settings
    """
    # Logs are potentially very large. If we are going to look up the company
    # associated with each hit, we should memoize the ids.
    log_memo = {}

    for log in logs:
        to_solr = []
        path = '/tmp/parse_log'
        # Ensure local temp storage for log files exists
        try:
            os.mkdir(path)
        except OSError:
            if not os.path.isdir(path):
                raise
        f = open('%s/%s' % (path, uuid.uuid4().hex), 'w+')
        try:
            log.get_contents_to_file(f)
            f.seek(0)

            for line in f:
                if line[0] == '#':
                    # Logs contain a header that LogParser uses to determine
                    # the log format; if we see this, ignore it
                    continue

                # line in f does not strip newlines if they exist
                line = line.rstrip('\n')
                line = line.split(' ')

                # reconstruct date and time
                line[0] = '%s %s' % (line[0], line[1])
                # turn date and time into a datetime object
                line[0] = datetime.strptime(line[0], '%Y-%m-%d %H:%M:%S')
                # remove the time portion, which is now merged with the date
                del line[1]

                # reconstruct user agent
                # and remove it from the line
                if 'redirect' in log.key:
                    ua = ' '.join(line[9:-7])
                    del line[9:-7]
                else:
                    ua = line[8]
                    del line[8]

                if not helpers.is_bot(ua):
                    # Only track hits that come from actual users
                    update_dict = {
                        'view_date': line[0],
                        'doc_type': 'analytics',
                    }

                    # Make sure the value for a given key is only a list if
                    # there are multiple elements
                    qs = dict((k, v if len(v) > 1 else v[0])
                              for k, v in urlparse.parse_qs(
                                  line[4]).iteritems())

                    if 'redirect' in log.key:
                        aguid = qs.get('jcnlx.aguid', '')
                        myguid = qs.get('jcnlx.myguid', '')
                        update_dict['view_source'] = qs.get('jcnlx.vsid', 0)
                        update_dict['job_view_buid'] = qs.get('jcnlx.buid', '0')

                        # GUID is the path portion of this line, which starts
                        # with a '/'; Remove it
                        update_dict['job_view_guid'] = line[3][1:]
                        update_dict['page_category'] = 'redirect'
                        domain = qs.get('jcnlx.ref', '')
                        domain = urlparse.urlparse(domain).netloc
                        update_dict['domain'] = domain
                    else:
                        aguid = qs.get('aguid', '')
                        myguid = qs.get('myguid', '')
                        update_dict['view_source'] = qs.get('jvs', 0)
                        update_dict['job_view_buid'] = qs.get('jvb', '0')
                        update_dict['job_view_guid'] = qs.get('jvg', '')
                        update_dict['page_category'] = qs.get('pc', '')

                        # These fields are only set in analytics logs
                        update_dict['domain'] = qs.get('d', '')
                        update_dict['facets'] = qs.get('f', '')
                        update_dict['job_view_title_exact'] = qs.get('jvt', '')
                        update_dict['job_view_company_exact'] = qs.get('jvc', '')
                        update_dict['job_view_location_exact'] = qs.get('jvl', '')
                        update_dict['job_view_canonical_domain'] = qs.get('jvcd', '')
                        update_dict['search_location'] = qs.get('sl', '')
                        update_dict['search_query'] = qs.get('sq', '')
                        update_dict['site_tag'] = qs.get('st', '')
                        update_dict['special_commitment'] = qs.get('sc', '')

                    # Handle logs containing the old aguid/myguid formats
                    aguid = aguid.replace('{', '').replace('}', '').replace('-', '')
                    update_dict['aguid'] = aguid

                    myguid = myguid.replace('-', '')

                    if myguid:
                        try:
                            user = User.objects.get(user_guid=myguid)
                        except User.DoesNotExist:
                            update_dict['User_user_guid'] = ''
                        else:
                            update_dict.update(object_to_dict(User, user))

                    buid = update_dict['job_view_buid']
                    domain = update_dict.get('domain', None)
                    if not (buid in log_memo or domain in log_memo):
                        # We haven't seen this buid or domain before
                        if buid == '0' and domain is not None:
                            # Retrieve company id via domain
                            try:
                                site = SeoSite.objects.get(domain=domain)
                                company_id = site.business_units.values_list(
                                    'company__pk', flat=True)[0]
                            except (SeoSite.DoesNotExist,
                                    IndexError):
                                # SeoSite.DoesNotExist: Site does not exist
                                #   with the given domain
                                # IndexError: SeoSite exists, but is not
                                #   associated with business units or companies
                                company_id = 999999
                            key = domain
                        else:
                            # Retrieve company id via buid
                            try:
                                # See if there is a company associated with it
                                company_id = Company.objects.filter(
                                    job_source_ids=buid)[0].pk
                            except IndexError:
                                # There is not; default to DirectEmployers
                                # Association
                                company_id = 999999
                            key = buid

                        # The defining feature of a given document will either
                        # be the domain or the buid.
                        # Our memoization dict will have the following structure
                        # {str(buid): int(company_id),
                        #  str(domain): int(company_id)}
                        log_memo[key] = company_id

                    # By this point, we are guaranteed that the correct key is
                    # in log_memo; pull the company id from the memo dict.
                    if domain is not None and domain in log_memo:
                        update_dict['company_id'] = log_memo[domain]
                    else:
                        update_dict['company_id'] = log_memo[buid]

                    update_dict['uid'] = 'analytics##%s#%s' % \
                                         (update_dict['view_date'], aguid)
                    to_solr.append(update_dict)
        except Exception:
            # There may be more logs to process, don't propagate the exception
            pass
        finally:
            # remove the file from the filesystem to ensure we don't fill the
            # drive (again)
            f.close()
            os.remove(f.name)

        # Ensure all hits get recorded by breaking a potentially massive list
        # down into something that solr can manage
        subsets = split_list(to_solr, 500)
        for location in solr_location.values():
            solr = pysolr.Solr(location)
            for subset in subsets:
                try:
                    subset = filter(None, subset)
                    solr.add(subset)
                except pysolr.SolrError:
                    # There is something wrong with this chunk of data. It's
                    # better to lose 500 documents than the entire file
                    pass


@task(name="tasks.delete_old_analytics_docs", ignore_result=True)
def delete_old_analytics_docs():
    """
    Deletes all analytics docs from the "current" collection that are older
    than 30 days
    """
    if hasattr(mail, 'outbox'):
        solr_location = settings.TEST_SOLR_INSTANCE['current']
    else:
        solr_location = settings.SOLR['current']

    pysolr.Solr(solr_location).delete(
        q="doc_type:analytics AND view_date:[* TO NOW/DAY-30DAYS]")


@task(name="tasks.update_solr_from_log", ignore_result=True)
def read_new_logs(solr_location=None):
    """
    Reads new logs and stores their contents in solr

    Inputs:
    :solr_location: Dict of separate cores to be updated (Optional);
        defaults to the default instance from settings
    """
    # If running tests, use test instance of local solr
    if hasattr(mail, 'outbox'):
        solr_location = settings.TEST_SOLR_INSTANCE
    elif solr_location is None:
        solr_location = settings.SOLR

    conn = boto.connect_s3(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_KEY)
    # https://github.com/boto/boto/issues/2078
    # validate=True costs 13.5x validate=False; Skip validation if we are
    # reasonably certain that the bucket exists.
    log_bucket = conn.get_bucket('my-jobs-logs', validate=False)

    # Sort logs into groups based on server
    all_logs = log_bucket.list()
    logs_by_host = {}
    for log in all_logs:
        # Logs are being stored with a key of host/log_type/file.log
        key_parts = log.key.split('/')

        # Since we are also storing redirect error logs, we should ensure
        # we are only processing the logs we care about
        if key_parts[1] in ['analytics', 'redirect']:
            logs_by_host.setdefault(key_parts[0], []).append(log)

    logs_to_process = []
    for key in logs_by_host.keys():
        # Files are named by date and time; the last log for each host is the
        # last log uploaded by that host
        logs_to_process += logs_by_host[key][-1:]

    # Ensure we only process each['href'] file once
    processed = getattr(settings, 'PROCESSED_LOGS', set())
    unprocessed = [log for log in logs_to_process if log.key not in processed]

    parse_log(unprocessed, solr_location)

    settings.PROCESSED_LOGS = set([log.key for log in logs_to_process])

    delete_old_analytics_docs.delay()


@task(name='tasks.expire_jobs', ignore_result=True)
def expire_jobs():
    jobs = Job.objects.filter(date_expired__lt=date.today(),
                              is_expired=False, autorenew=False)
    for job in jobs:
        # Setting is_expired to True will trigger job.remove_from_solr()
        job.is_expired = True
        job.save()

    jobs = Job.objects.filter(date_expired__lt=date.today(),
                              is_expired=False, autorenew=True)
    for job in jobs:
        job.date_expired = date.today() + timedelta(days=30)
        # Saving will trigger job.add_to_solr().
        job.save()


@task(name="tasks.task_clear_bu_cache", acks_late=True, ignore_results=True)
def task_clear_bu_cache(buid, **kwargs):
    try:
        BusinessUnit.clear_cache(buid)
    except:
        logging.error(traceback.format_exc(sys.exc_info()))

@task(name="tasks.task_update_solr", acks_late=True, ignore_result=True)
def task_update_solr(jsid, **kwargs):
    try:
        import_jobs.update_solr(jsid, **kwargs)
    except:
        logging.error(traceback.format_exc(sys.exc_info()))
        raise task_update_solr.retry()


@task(name='tasks.etl_to_solr', ignore_result=True, send_error_emails=True)
def task_etl_to_solr(guid, buid, name):
    try:
        import_jobs.update_job_source(guid, buid, name)
    except Exception as e:
        logging.error("Error loading jobs for jobsource: %s", guid)
        logging.exception(e)
        raise task_etl_to_solr.retry()


@task(name='tasks.priority_etl_to_solr', ignore_result=True)
def task_priority_etl_to_solr(guid, buid, name):
    try:
        import_jobs.update_job_source(guid, buid, name, clear_cache=True)
    except Exception as e:
        logging.error("Error loading jobs for jobsource: %s", guid)
        logging.exception(e)
        raise task_priority_etl_to_solr.retry()


@task(name="tasks.task_clear_solr", ignore_result=True)
def task_clear_solr(jsid):
    """Delete all jobs for a given Business Unit/Job Source."""
    import_jobs.clear_solr(jsid)


@task(name="tasks.task_force_create", ignore_result=True)
def task_force_create(jsid):
    import_jobs.force_create_jobs(jsid.id)


@task(name="tasks.task_submit_sitemap", ignore_result=True)
def task_submit_sitemap(domain):
    """
    Submits yesterday's sitemap to google for the given domain
    Input:
        :domain: sitemap domain
    """
    ping_google('http://{d}/sitemap.xml'.format(d=domain))


@task(name="tasks.task_submit_all_sitemaps", ignore_result=True)
def task_submit_all_sitemaps():
    sites = SeoSite.objects.all()
    for site in sites:
        task_submit_sitemap.delay(site.domain)


def get_event_list(events):
    """
    Turns a block of json events into a list of events.

    :param events: A json encoded group of events.
    :return: A list of the events as dictionaries.
    """

    try:
        # try parsing post data as json
        event_list = json.loads(events)
    except ValueError:  # nope, it's V1 or V2
        event_list = []
        events = events.splitlines()
        for event_str in events:
            if event_str == '':
                continue
            # nested try :/ -need to catch json exceptions
            try:
                event_list.append(json.loads(event_str))
            except ValueError:  # Bad json
                newrelic.agent.record_exception(
                    *sys.exc_info())
                return []
    except Exception:
        newrelic.agent.record_exception(*sys.exc_info())
        return []
    else:
        # If only one event was posted, this could be any
        # version of the api; event_list will be a list of
        # dicts if using V3 but will be a dict for V1 and V2.
        if type(event_list) != list:
            event_list = [event_list]

    return event_list


def event_list_to_email_log(event_list):
    """
    :param event_list: A list of events, where each event is a dictionary.
    :return: A list of EmailLog objects.
    """
    events_to_create = []
    for event in event_list:
        category = event.get('category', '')
        email_log_args = {
            'email': event['email'], 'event': event['event'],
            'received': date.fromtimestamp(float(event['timestamp'])),
            'category': category,
            # Events can have a response (delivered, deferred),
            # a reason (bounce, block), or neither, but never
            # both.
            'reason': event.get('response',
                                event.get('reason', ''))
        }
        if event['event'] == 'bounce' and category == 'My.jobs email redirect':
            subject = 'My.jobs email redirect failure'
            body = """
                   Contact: %s
                   Type: %s
                   Reason: %s
                   Status: %s
                   """ % (event['email'], event['type'],
                          event['reason'], event['status'])
            issue_dict = {
                'summary': 'Redirect email failure',
                'description': body,
                'issuetype': {'name': 'Bug'}
            }
            log_to_jira(subject, body, issue_dict, event['email'])

        is_list = isinstance(category, list)
        for env in ['QC', 'Staging', 'Local', 'Jenkins']:
            # This event has multiple attached categories and env is one of them
            # or there is only one category, which is env.
            if (is_list and env in category) or \
                    (not is_list and category == env):
                break
        else:
            if is_list:
                try:
                    category.remove('Production')
                except ValueError:
                    pass
                else:
                    if len(category) == 1:
                        # This preserves our prior functionality - if there are
                        # legitimately multiple categories on this email,
                        # category will remain a list and this will get logged
                        # by NewRelic.
                        category = category[0]
            elif category == 'Production':
                category = ''

            # These categories resemble the following:
            # Saved Search Sent (<list of keys>|event_id)
            try:
                event_id = category.split('|')[-1][:-1]
            except AttributeError:
                newrelic.agent.record_exception(*sys.exc_info())
                return []
            if event_id:
                try:
                    log = SavedSearchLog.objects.get(uuid=event_id)
                    email_log_args['send_log'] = log
                    if event['event'] not in BAD_EMAIL:
                        log.was_received = True
                        log.save()
                except SavedSearchLog.DoesNotExist:
                    pass
            events_to_create.append(EmailLog(**email_log_args))

    return events_to_create


@task(name="tasks.process_sendgrid_event", ignore_result=True)
def process_sendgrid_event(events):
    """
    Processes events POSTed by SendGrid.

    :events: A request body containing a batch of events from SendGrid. A batch
             of events is a series of JSON strings separated by new lines
             (Version 1 and 2) or as well formed JSON (Version 3)

    """
    event_list = get_event_list(events)
    events_to_create = event_list_to_email_log(event_list)
    EmailLog.objects.bulk_create(events_to_create)


@task(name="tasks.send_event_email", ignore_result=True)
def send_event_email(email_task):
    """
    Send an appropriate email given an EmailTask instance.

    Inputs:
    :email_task: EmailTask we are using to generate this email
    """
    email_task.task_id = send_event_email.request.id
    email_task.save()

    email_task.send_email()

    email_task.completed_on = datetime.now()
    email_task.save()
