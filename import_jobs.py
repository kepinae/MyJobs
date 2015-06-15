import json
import os
import sys
import urllib
import datetime
import logging
from itertools import izip_longest
import urllib2
import base64
import zipfile
import shutil

from slugify import slugify
from lxml import etree
from django.conf import settings
from django.db import IntegrityError
from billiard import current_process

from seo_pysolr import Solr
from xmlparse import DEv2JobFeed
from seo.helpers import slices, create_businessunit
from seo.models import BusinessUnit, Company
import tasks
from transform import hr_xml_to_json, make_redirect


logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, '../../data/'))
sys.path.insert(0, os.path.join(BASE_DIR))
sys.path.insert(0, os.path.join(BASE_DIR, '../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'directseo.settings'
FEED_FILE_PREFIX = "dseo_feed_"


def update_job_source(guid, buid, name, fc, staffing_code, industries, clear_cache=False):
    """Composed method for resopnding to a guid update."""

    logger.info("Updating Job Source %s", guid)
    # Make the BusinessUnit and Company
    create_businessunit(buid)
    bu = BusinessUnit.objects.get(id=buid)
    bu.title = name
    bu.save()
    add_company(bu)

    # Lookup the jobs, filter then, transform them, and then load the jobs
    zf = get_jobsfs_zipfile(guid)
    jobs = get_jobs_from_zipfile(zf, guid)
    jobs = filter_current_jobs(jobs, bu)
    jobs = [hr_xml_to_json(job, bu) for job in jobs]
    for job in jobs:
        job['link'] = make_redirect(job, bu).make_link()
        job['ind'] = industries
        job['federal_contractor'] = "True" if fc == "1" else "False"
        job['staffing_code'] = "True" if staffing_code == "1" else "False"
        job['network'] = 'False' if 2649 < bu.id < 2704 else 'True'
    add_jobs(jobs)
    remove_expired_jobs(buid, jobs)

    # Update business information
    bu.associated_jobs = len(jobs)
    bu.date_updated = datetime.datetime.utcnow()
    bu.save()
    if clear_cache:
        # Clear cache in 25 minutes to allow for solr replication
        tasks.task_clear_bu_cache.delay(buid=bu.id, countdown=1500)


def filter_current_jobs(jobs, bu):
    """Given a iterator/generator of jobs, filter the list, removing jobs that should not be indexed for microsites.
    Inputs:
        :jobs: A iterable of etree objects.
        :bu: The BusinessUnit these jobs are associated with.

       Returns: a generator of jobs which pass validation for indexing."""

    hr_xml_include_in_index = ".//*[@schemeName='dbextras.tempjobwrappingjobs.includeinindex']"
    for job in jobs:
        # Written using continues to allow easily adding multiple conditions to
        # remove jobs.
        if bu.ignore_includeinindex is False and job.find(hr_xml_include_in_index).text == '0':
            logger.info("A job was filtered for %s" % bu)
            continue
        yield job


def get_jobsfs_zipfile(guid):
    """Get a fileobject for the zipfile from JobsFS.

    This has been separated to simplify uncouple parsing zipfiles from jobsFS, so we can more easily test the rest of
    this code.

    Inputs:
        :guid: The guid of which to download.
    :return: A urllib2 Response (A filelike object)
    """
    # Download the zipfile
    url = 'http://jobsfs.directemployers.org/%s/ActiveDirectory_%s.zip' % \
        (guid, guid)
    req = urllib2.Request(url)
    authheader = "Basic %s" % base64.encodestring('%s:%s' % ('microsites',
                                                             'di?dsDe4'))
    req.add_header("Authorization", authheader)
    resp = urllib2.urlopen(req)
    return resp


def get_jobs_from_zipfile(zipfileobject, guid):
    """Get a list of xml documents representing all the current jobs.

    Input:
        :guid: A guid used to access the jobsfs server.
    :return: [lxml.eTree, lxml.eTree,...]"""
    logger.debug("Getting current Jobs for guid: %s", guid)


    # Get current worker process id, to prevent race conditions.
    try:
        p = current_process()
        process_id =  p.index
    except AttributeError:
        process_id = 0


    # Delete any existing data and use the guid to create a unique folder.
    directory = "/tmp/%s/%s" % (process_id, guid)
    prefix =  os.path.commonprefix(['/tmp/%s' % process_id, os.path.abspath(directory)])
    assert prefix == '/tmp/%s' % process_id, "Directory should be located in /tmp/%s" % process_id

    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

    # Write zipfile to filesystem
    filename = os.path.join(directory, '%s.zip' % guid)
    with open(filename, 'wb') as f:
        for chunk in iter(lambda: zipfileobject.read(1024 * 16), ''):
            f.write(chunk)

    # Extact all files from zipfile.
    # Note: Using try/finally because zipfile doesn't support context managers
    #       until python 2.7.  Upon migration to python 2.7, can be replaced.
    zf = zipfile.ZipFile(filename)
    try:
        zf.extractall(directory)
    finally:
        zf.close()

    # Process the files.
    active_directory = os.path.join(directory, 'ActiveDirectory_%s' % guid)
    files = os.listdir(active_directory)
    logger.info("Found %s jobs for guid %s", len(files), guid)
    for f in files:
        path = os.path.join(active_directory, f)
        if os.path.isdir(path):
            logger.warn("Found folder '%s' inside active jobs for JSID: %s",
                        f, guid)
            continue
        with open(path) as _f:
            yield etree.fromstring(_f.read())

    # clean up after ourselves.
    shutil.rmtree(directory)

class FeedImportError(Exception):
    def __init__(self, msg):
        self.msg = msg


def add_company(bu):
    """
    Add the company to the Django database if it doesn't exist already.
    If the company does exist, but the business unit isn't related to it,
    add the relationship.

    Inputs
    :bu: An instance of BusinessUnit, passed in from update_solr().

    Returns
    None.

    Writes/Modifies
    The Django database is updated to reflect a new company or the
    name change of an existing company.

    """
    # See if there is an existing relationship. For now, we are assuming only
    # one or zero instances of a company exist in the database--this may change
    companies = bu.company_set.all()
    if companies:
        co = companies[0]
    else:
        co = False

    # Attempt to look up the company by the name of the BusinessUnit title
    try:
        existing_company = Company.objects.get(user_created=False,
                                               name=bu.title)
    except Company.DoesNotExist:
        existing_company = False

    # If a matching company exists, associate bu with it.
    # This removes any existing relationships.
    if existing_company:
        logger.debug("Associating Company '%s' with BusinessUnit '%s'", co,
                     existing_company)
        bu.company_set = [existing_company]
        co = existing_company
        return co

    # If a relationship exists but the name is different
    # and the company is not tied to another business unit
    if co and bu.title and co.name != bu.title:
        if co.job_source_ids.all().count() == 1:
            logger.warn("Changing name of Company '%s' to BusinessUnit title"
                        " '%s'", co, bu.title)
            # change the name of the company related to the BusinessUnit object
            co.name = bu.title
            co.save()
            return co
        else:
            co = False

    # If a there is NOT a relationship, or the company is associated with
    # more than one business unit
    if not co:
        logger.info("Creating a company for BusinessUnit %s", bu)
        # Remove existing relationships from business unit
        # Create the company
        slug = slugify(bu.title)
        logo_url = '//d2e48ltfsb5exy.cloudfront.net/100x50/seo/%s.gif'
        co = Company(name=bu.title, company_slug=slug, logo_url=logo_url % slug)
        try:
            co.save()
        except IntegrityError:
            logging.error("Failed to add BUID %s to Company object with title, "
                          "%s. Company already exists." % (bu.id, bu.title))
        else:
            bu.company_set = [co]
            return co


def update_solr(buid, download=True, force=True, set_title=False,
                delete_feed=True, data_dir=DATA_DIR, clear_cache=False):
    """
    Update the Solr master index with the data contained in a feed file
    for a given buid/jsid.

    This is meant to be a standalone function such that the state of the
    Solr index is not tied to the state of the database.

    Inputs:
    :buid: An integer; the ID for a particular business unit.
    :download: Boolean. If False, this process will not download a new
    feedfile, but instead use the one on disk. Should only be false for
    the purposes of our test suite.
    :force: Boolean. If True, every job seen in the feed file will be
    updated in the index. Otherwise, only the jobs seen in the feed file
    but not seen in the index will be updated. This latter option will
    soon be deprecated.

    Returns:
    A 2-tuple consisting of the number of jobs added and the number deleted.

    Writes/Modifies:
    Job data found in the feed file is used to modify the Solr index. This
    includes adds & deletes. (Solr does not have a discrete equivalent to
    SQL's UPDATE; by adding a document with the same UID as a document in
    the index, the equivalent of an update operation is performed.)

    """
    if download:
        filepath = download_feed_file(buid, data_dir=data_dir)
    else:
        # Get current worker process id, to prevent race conditions.
        try:
            p = current_process()
            process_id =  p.index
        except:
            process_id = 0
        filepath = os.path.join(data_dir, str(process_id), FEED_FILE_PREFIX + str(buid) +
                                '.xml')
    bu = BusinessUnit.objects.get(id=buid)
    try:
        co = bu.company_set.all()[0]
    except IndexError:
        co = None
    jobfeed = DEv2JobFeed(filepath, jsid=buid, markdown=bu.enable_markdown,
                          company=co)
    # If the feed file did not pass validation, return. The return value is
    # '(0, 0)' to match what's returned on a successful parse.
    if jobfeed.errors:
        error = jobfeed.error_messages
        logging.error("BUID:%s - Feed file has failed validation on line %s. "
                      "Exception: %s" % (buid, error['line'],
                                         error['exception']))
        raise FeedImportError(error)

    # A dictionary of uids
    jobs = jobfeed.jobparse()

    # Build a set of all the UIDs for all those instances.
    job_uids = set([long(i.get('uid')) for i in jobs if i.get('uid')])
    conn = Solr(settings.HAYSTACK_CONNECTIONS['default']['URL'])
    step1 = 1024

    # Get the count of all the results in the Solr index for this BUID.
    hits = conn.search("*:*", fq="buid:%s" % buid, facet="false",
                       mlt="false").hits
    # Create (start-index, stop-index) tuples to facilitate handling results
    # in ``step1``-sized chunks. So if ``hits`` returns 2048 results,
    # ``job_slices`` will look like ``[(0,1024), (1024, 2048)]``. Those
    # values are then used to slice up the total results.
    #
    # This was put in place because part of the logic to figuring out what
    # jobs to delete from and add jobs to the Solr index is using set
    # algebra. We convert the total list of UIDs in the index and the UIDs
    # in the XML feed to sets, then compare them via ``.difference()``
    # (seen below). However for very large feed files, say 10,000+ jobs,
    # this process was taking so long that the connection would time out. To
    # address this problem we break up the comparisons as described above.
    # This results in more requests but it alleviates the connection timeout
    # issue.
    job_slices = slices(range(hits), step=step1)
    results = [_solr_results_chunk(tup, buid, step1) for tup in job_slices]
    solr_uids = reduce(lambda x, y: x | y, results) if results else set()
    # Return the job UIDs that are in the Solr index but not in the feed
    # file.
    solr_del_uids = solr_uids.difference(job_uids)

    if not force:
        # Return the job UIDs that are in the feed file but not in the Solr
        # index.
        solr_add_uids = job_uids.difference(solr_uids)
        # ``jobfeed.solr_jobs()`` yields a list of dictionaries. We want to
        # filter out any dictionaries whose "uid" key is not in
        # ``solr_add_uids``. This is because by default we only want to add
        # new documents (which each ``solr_jobs()`` dictionary represents),
        # not update.
        add_docs = filter(lambda x: int(x.get("uid", 0)) in solr_add_uids,
                          jobfeed.solr_jobs())
    else:
        # This might seem redundant to refer to the same value
        # twice with two different variable names. However, this decision
        # was made during the implementation of the "force Solr update"
        # feature to this function.
        #
        # Instead of adding only the documents with UIDs that are in the feed
        # file but not in the Solr index, we're going to add ALL the documents
        # in the feed file. This will add the new documents of course, but it
        # will also update existing documents with any new data. Uniqueness of
        # the documents is ensured by the ``id`` field defined in the Solr
        # schema (the template for which can be seen in
        # templates/search_configuration/solr.xml). At the very bottom you'll
        # see <uniqueKey>id</uniqueKey>. This serves as the equivalent of the pk
        # (i.e. globally unique) in a database.
        solr_add_uids = job_uids
        add_docs = jobfeed.solr_jobs()

    # Slice up ``add_docs`` in chunks of 4096. This is because the
    # maxBooleanClauses setting in solrconfig.xml is set to 4096. This means
    # if we used any more than that Solr would throw an error and our
    # updates wouldn't get processed.
    add_steps = slices(range(len(solr_add_uids)), step=4096)
    # Same concept as ``add_docs``.
    del_steps = slices(range(len(solr_del_uids)), step=4096)
    # Create a generator that yields 2-tuples with each invocation. The
    # 2-tuples consist of one tuple each from del_steps & add_steps. Any
    # mismatched values (e.g. there are more del_steps than add_steps)
    # will be compensated for with the ``fillvalue``.
    zipped_steps = izip_longest(del_steps, add_steps, fillvalue=(0, 0))

    for tup in zipped_steps:
        update_chunk = add_docs[tup[1][0]:tup[1][1] + 1]

        if update_chunk:
            logging.debug("BUID:%s - SOLR - Update chunk: %s" %
                         (buid, [i['uid'] for i in update_chunk]))
            # Pass 'commitWithin' so that Solr doesn't try to commit the new
            # docs right away. This will help relieve some of the resource
            # stress during the daily update. The value is expressed in
            # milliseconds.
            conn.add(update_chunk, commitWithin="30000")

        delete_chunk = _build_solr_delete_query(
            list(solr_del_uids)[tup[0][0]:tup[0][1] + 1])

        if delete_chunk:
            # Post-a-job jobs should not be deleted during import
            delete_chunk = "(%s) AND -is_posted:true" % delete_chunk
            logging.debug("BUID:%s - SOLR - Delete chunk: %s" %
                         (buid, list(solr_del_uids)))
            conn.delete(q=delete_chunk)

    #Update business unit information: title, dates, and associated_jobs
    if set_title or not bu.title or (bu.title != jobfeed.job_source_name and
                                     jobfeed.job_source_name):
        bu.title = jobfeed.job_source_name
    updated = bool(solr_add_uids) or bool(solr_del_uids)
    _update_business_unit_modified_dates(bu, jobfeed.crawled_date,
                                         updated=updated)
    bu.associated_jobs = len(jobs)
    bu.save()
    if clear_cache:
        # Clear cache in 25 minutes to allow for solr replication
        tasks.task_clear_bu_cache.delay(buid=bu.id, countdown=1500)
    #Update the Django database to reflect company additions and name changes
    add_company(bu)
    if delete_feed:
        os.remove(filepath)
        logging.info("BUID:%s - Deleted feed file." % buid)
    return len(solr_add_uids), len(solr_del_uids)


def clear_solr(buid):
    """Delete all jobs for a given business unit/job source."""
    conn = Solr(settings.HAYSTACK_CONNECTIONS['default']['URL'])
    hits = conn.search(q="*:*", rows=1, mlt="false", facet="false").hits
    logging.info("BUID:%s - SOLR - Deleting all %s jobs" % (buid, hits))
    conn.delete(q="buid:%s" % buid)
    logging.info("BUID:%s - SOLR - All jobs deleted." % buid)


def _solr_results_chunk(tup, buid, step):
    """
    Takes a (start_index, stop_index) tuple and gets the results in that
    range from the Solr index.

    """
    conn = Solr(settings.HAYSTACK_CONNECTIONS['default']['URL'])
    results = conn.search("*:*", fq="buid:%s" % buid, fl="uid",
                          rows=step, start=tup[0], facet="false",
                          mlt="false").docs
    return set([i['uid'] for i in results if 'uid' in i])


def _job_filter(job):
    if job.uid:
        return long(job.uid)


def _xml_errors(jobfeed):
    """
    Checks XML input for errors, and logs any it finds.

    """
    if jobfeed.errors:
        logging.error("XML Job Feed Error",
                      extra={'data': jobfeed.error_messages})
    return jobfeed.error_messages


def download_feed_file(buid, data_dir=DATA_DIR):
    """
    Downloads the job feed data for a particular job source id.

    """

    # Get current worker process id, to prevent race conditions.
    try:
        p = current_process()
        process_id =  p.index
    except AttributeError:
        process_id = 0

    full_file_path = os.path.join(data_dir, str(process_id), FEED_FILE_PREFIX + str(buid) +
                                  '.xml')
    # Download new feed file for today
    logging.info("Downloading new file for BUID %s..." % buid)
    if not os.path.exists(os.path.dirname(full_file_path)):
        os.makedirs(os.path.dirname(full_file_path))
    urllib.urlretrieve(generate_feed_url(buid), full_file_path)
    logging.info("Download complete for BUID %s" % buid)
    return full_file_path


def _has_errors(doc):
    has_errors = False
    errors = etree.iterparse(doc, tag='error')
    # we have at least one error, lets deal with it
    for event, error in errors:
        has_errors = True
    return has_errors, errors


def _update_business_unit_modified_dates(business_unit, crawled_date,
                                         updated=True):
    """
    Updates crawled_date and date_updated for a businessunit
    :Inputs:
        business_unit: An instance of seo.models.BusinessUnit
        crawled_date: A datetime object
        updated: Boolean, True if date_updated should be set to now

    :Outputs:
        An updated BusinessUnit instance
    """
    if crawled_date:
        business_unit.date_crawled = crawled_date
    if updated:
        business_unit.date_updated = datetime.datetime.utcnow()
    return business_unit


def schedule_jobs(buid):
    parser = etree.XMLParser(no_network=False)
    result = etree.parse(generate_feed_url(buid, 'schedule'), parser)
    try:
        result.find('confirmation').text
        result = {'success': True}
        logging.info("XML Job Feed - Scheduled for Buid: %s" % buid)
    except AttributeError:
        result = {'success': False,
                  'error': 'Error: %s' % (result.find('/error/description')
                                                .text)}
        logging.error(
            "XML Job Feed - Schedule Error", exc_info=sys.exc_info(),
            extra={"data": {"buid": buid,
                            "error": result}})
    return result


def unschedule_jobs(buid):
    parser = etree.XMLParser(no_network=False)
    result = etree.parse(generate_feed_url(buid, 'unschedule'), parser)
    try:
        result.find('confirmation').text
        result = {'success': True}
        logging.info("XML Job Feed - Unscheduled for Buid: %s" % buid)
    except AttributeError:
        result = {'success': False,
                  'error': 'Error: %s' % (result.find('/error/description')
                                                .text)}
        logging.error(
            "XML Job Feed - Unschedule Error", exc_info=sys.exc_info(),
            extra={"data": {"buid": buid,
                            "error": result}})
    return result


def force_create_jobs(buid):
    parser = etree.XMLParser(no_network=False)
    result = etree.parse(generate_feed_url(buid, 'create'), parser)
    try:
        result.find('confirmation').text
        result = ("Business unit was created/recreated"
                  "and will automatically update shortly.")
        logging.info("XML Job Feed - Force create for Buid: %s" % buid)
    except AttributeError:
        result = "Error: %s" % result.find('/error/description').text
        logging.error(
            "XML Job Feed - Force Create Error",
            exc_info=sys.exc_info(),
            extra={"data": {"buid": buid,
                            "error": result}})
    return result


def generate_feed_url(buid, task=None):
    key = settings.SEO_XML_KEY
    the_url = ('http://seoxml.directemployers.com/v2/?key=%s&buid=%s' %
               (key, str(buid)))
    if task in ['create', 'schedule', 'unschedule']:
        the_url += '&task=%s' % task
    return the_url


def _build_solr_delete_query(old_jobs):
    if old_jobs:
        delete_query = ("uid:(%s)" % " OR ".join([str(x) for x in old_jobs]))
    else:
        delete_query = None

    return delete_query


def chunk(l, chunk_size=1024):
    """
    Create chunks from a list.

    """
    for i in xrange(0, len(l), chunk_size):
        yield l[i:i + chunk_size]


def remove_expired_jobs(buid, active_jobs, upload_chunk_size=1024):
    """
    Given a job source id and a list of active jobs for that job source,
    Remove the jobs on solr that are not among the active jobs.
    """
    conn = Solr(settings.HAYSTACK_CONNECTIONS['default']['URL'])
    count = conn.search("*:*", fq="buid:%s" % buid, facet="false",
                                      mlt="false").hits
    old_jobs = conn.search("*:*", fq="buid:%s" % buid, facet="false",
                           rows=count, mlt="false").docs
    active_ids = set(j['id'] for j in active_jobs)
    old_ids = set(j['id'] for j in old_jobs)
    expired = old_ids - active_ids
    chunks = chunk(list(expired), upload_chunk_size)
    for jobs in chunks:
        query = "id:(%s)" % " OR ".join([str(x) for x in jobs])
        conn.delete(q=query)
    return expired


def add_jobs(jobs, upload_chunk_size=1024):
    """
    Loads a solr-ready json list of jobs into solr.

    inputs:
        :jobs: A list of solr-ready, json-formatted jobs.

    outputs:
        The number of jobs loaded into solr.
    """
    conn = Solr(settings.HAYSTACK_CONNECTIONS['default']['URL'])
    num_jobs = len(jobs)
    # AT&T Showed that large numbers of MOCs can cause import issues due to the size of documents.
    # Therefore, when processing AT&T lower the document chunk size.
    for job in jobs:
        if int(job.get('buid', 0)) == 19389:
            logger.warn("AT&T has large amounts of mapped_mocs, that cause problems.  Reducing chunk size.")
            upload_chunk_size = 64
            break
            
    
    # Chunk them
    jobs = chunk(jobs, upload_chunk_size)
    for job_group in jobs:
        conn.add(list(job_group))
    return num_jobs


def delete_by_guid(guids):
    """
    Removes a jobs from solr by guid.

    inputs:
        :guids: A list of guids

    outputs:
        The number of jobs that were requested to be deleted. This may
        be higher than the number of actual jobs deleted if a guid
        passed in did not correspond to a job in solr.
    """
    conn = Solr(settings.HAYSTACK_CONNECTIONS['default']['URL'])
    if not guids:
        return 0
    num_guids = len(guids)
    guids = chunk(guids)
    for guid_group in guids:
        delete_str = " OR ".join(guid_group)
        conn.delete(q="guid: (%s)" % delete_str)
    return num_guids
