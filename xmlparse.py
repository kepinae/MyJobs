"""
Converts XML feed file into a list of dictionaries for Solr

"""

import datetime
import markdown2
import random
import time
from collections import namedtuple
from HTMLParser import HTMLParser
from lxml import etree
from slugify import slugify
from urlparse import urlparse

from django.contrib.contenttypes.models import ContentType
from django.utils.html import linebreaks

from seo.models import BusinessUnit
from moc_coding.models import CustomCareer, Moc
from universal.helpers import get_object_or_none


text_fields = ['description', 'title', 'country', 'country_short', 'state',
               'state_short', 'city', 'company']


class JobFeed(object):
    """
    A skeleton for building new translators for job feeds. This class
    should not be invoked directly, only used as a subclass for other
    classes.

    args:
    business_unit -- Either an int/numeric string (e.g. "13"), or a
    BusinessUnit instance. In the first case, the arg willl be used to
    query the database for a BusinessUnit instance.
    filepath -- A string describing the path to the feedfile to be parsed.
    This must be the feed file for the Business Unit referred to by the
    `business_unit` arg.
    js_field -- String. The name of the XML tag containing the name of
    the job source the jobs belong to.
    crawl_field -- String. The name of the XML tag containing the datetime
    the feed was crawled.
    node_tag -- String. The name of the XML tag that marks the beginning
    of an XML node that contains all the data for an individual job.
    datetime_pattern -- A string specifying the format of the datetime
    data in the feed. Should conform to the specification outlined here:
    http://docs.python.org/library/time.html#time.strftime
    """
    def __init__(self, filepath, js_field=None, crawl_field=None, node_tag=None,
                 datetime_pattern=None, jsid=None, schema=None, markdown=True,
                 company=None):
        if None in (js_field, crawl_field, datetime_pattern):
            raise AttributeError("You must specify valid values for js_field, "
                                 "datetime_pattern and crawl_field.")
        self.filepath = filepath
        self.bu_mapped_mocs = None
        self.parser = etree.XMLParser(recover=False, schema=schema)
        self.doc = etree.parse(self.filepath, self.parser)
        self.datetime_pattern = datetime_pattern
        self.jsid = jsid
        self.node_tag = node_tag
        self.job_source_name = self.unescape(self.parse_doc(js_field))
        self.crawled_date = get_strptime(self.parse_doc(crawl_field),
                                         self.datetime_pattern)
        self.markdown = markdown
        self.company = company
        self.industries = self.get_industry()
        if jsid is None:
            jsid = self.parse_doc('job_source_id')
            if jsid:
                self.jsid = int(jsid)
        else:
            self.jsid = jsid

        self.bu = (get_object_or_none(BusinessUnit, pk=self.jsid)
                   if self.jsid is not None else None)


    def jobparse(self):
        raise NotImplementedError

    def solr_job_dict(self, job_node):
        """
        This method must return a dictionary consisting of a mapping
        between fields in the Solr schema (defined in seo.search_indexes)
        and a single job.

        """
        raise NotImplementedError

    def solr_jobs(self):
        """
        This method must return a list of dictionaries from solr_job_dict.

        """
        return [self.solr_job_dict(node) for node in
                self.doc.find(self.node_tag).iterchildren()]

    @staticmethod
    def moc_data(mocs):
        MocData = namedtuple("MocData", "codes slabs ids")
        if not mocs:
            return MocData(None, None, None)
        moc_set = [moc.code for moc in mocs]
        moc_slab = ["%s/%s/%s/vet-jobs::%s - %s" %
                    (slugify(moc.title), moc.code, moc.branch, moc.code,
                     moc.title)
                    for moc in mocs]
        moc_ids = [moc.id for moc in mocs]
        return MocData(moc_set, moc_slab, moc_ids)

    @staticmethod
    def job_mocs(job):
        """
        Return a list of MOCs and MOC slabs for a given job.
        
        """
        onets = job.get('onet_code', '')
        moc_list = []
        if onets:
            [moc_list.append(moc) for moc in
             Moc.objects.filter(onets__code__in=onets)]
        return moc_list

    def mapped_mocs(self, mocs, job):
        """
        Return a list of moc data that will match this job's CustomCareer
        mappings, as well as original moc-onet mappings that haven't been
        overridden.
        
        This is union of (CustomCareer mapped mocs) and (all mocs that would
        normally map, minus any mocs with custom mappings)

        If there are no CustomCareer mappings for a job, then mapped mocs will
        return data for the original input mocs

        This lets us use one field for searching and faceting on sites with
        CustomCareer mappings

        Input:
            :mocs: An iterable of moc instances
            :job: A job node from the xml feed

        """
        content_type = ContentType.objects.get_for_model(BusinessUnit)
        if self.bu_mapped_mocs is None:
            self.bu_mapped_mocs = CustomCareer.objects.filter(
                object_id=self.jsid,
                content_type=content_type).values_list('moc', flat=True)
        if not self.bu_mapped_mocs:
            return self.moc_data(mocs)

        # If an moc is normally mapped to a job, but has a custom mapping
        # for this business unit, we remove the original mapping
        unmapped_mocs = set(mocs) - set(self.bu_mapped_mocs)

        onet_list = []
        [onet_list.append(bu_onet) for bu_onet in
         self.bu_mapped_mocs.filter(onet__in=job['onet_code'])]
        mapped_job_mocs = Moc.objects.filter(id__in=list(onet_list))
        mapped_job_moc_set = set(mapped_job_mocs)
        job_mocs = unmapped_mocs | mapped_job_moc_set
        return self.moc_data(job_mocs) 

    @staticmethod
    def clean_onet(onet):
        if onet is None:
            return ""
        return onet.replace("-", "").replace(".", "")

    def parse_doc(self, field, wrapper=None):
        """Use for retrieving document-level (as opposed to job-level) tags."""
        result = self.doc.find('.//' + field)
        if result is not None:
            if wrapper:
                return wrapper(result.text)
            else:
                return result.text
            return result

    @staticmethod
    def unescape(val):
        h = HTMLParser()

        if val:
            return h.unescape(val.strip())

    def get_industry(self):
        results = self.doc.findall('.//industry')
        industries = []
        if results:
            industries = [result.text for result in results]
        return industries

    @staticmethod
    def full_loc(obj):
        fields = ['city', 'state', 'location', 'country']
        strings = ['%s::%s' % (f, obj[f]) for f in fields]
        
        return '@@'.join(strings)

    @staticmethod
    def country_slab(obj):
        return "%s/jobs::%s" % (obj['country_short'].lower(), obj['country'])

    @staticmethod
    def state_slab(obj):
        if slugify(obj['state']):
            url = "%s/%s/jobs" % (slugify(obj['state']),
                                  obj['country_short'].lower())
            
            return "%s::%s" % (url, obj['state'])

    @staticmethod
    def city_slab(obj):
        url = "%s/%s/%s/jobs" % (slugify(obj['city']), slugify(obj['state']), 
                                 obj['country_short'].lower())
        return "%s::%s" % (url, obj['location'])

    @staticmethod
    def title_slab(obj):
        if slugify(obj['title']) and slugify(obj['title']) != "none":
            return "%s/jobs-in::%s" % (slugify(obj['title']).strip('-'),
                                       obj['title'])

    @staticmethod
    def co_slab(co):
        return u"{cs}/careers::{cn}".format(cs=slugify(co),
                                            cn=co)


class DEJobFeed(JobFeed):
    def __init__(self, *args, **kwargs):
        kwargs.update({
            'crawl_field': 'date_modified',
            'node_tag': 'jobs',
            'datetime_pattern': '%m/%d/%Y %I:%M:%S %p'
        })
        super(DEJobFeed, self).__init__(*args, **kwargs)

    @staticmethod
    def date_salt(date):
        """
        Generate a new datetime value salted with a random value, so that
        jobs will not be clumped together by job_source_id on the job list
        pages. This time is constrained to between `date` and the
        previous midnight so that jobs that are new on a given day don't
        wind up showing up on the totally wrong day inadvertently.

        Input:
        :date: A `datetime.datetime` object. Represents the date a job
        was posted.

        Returns:
        A datetime object representing a random time between `date` and
        the previous midnight.
        
        """
        oneday = datetime.timedelta(hours=23, minutes=59, seconds=59)
        # midnight last night
        lastnight = datetime.datetime(date.year, date.month, date.day)
        # midnight tonight
        tonight = lastnight + oneday
        # seconds since midnight last night
        start = (date - lastnight).seconds
        # seconds until midnight tonight
        end = (tonight - date).seconds
        # Number of seconds between 'date' and the previous midnight.
        salt = random.randrange(-start, end)
        # seconds elapsed from epoch to 'date'
        seconds = time.mktime(date.timetuple())
        # Convert milliseconds -> time tuple
        salted_time = time.localtime(seconds + salt)
        # `salted_time` at this point is a time tuple, which has the same API
        # as a normal tuple. We destructure it and pass only the first six
        # elements (year,month,day,hour,min,sec).
        return datetime.datetime(*salted_time[0:6])

    def node_to_dict(self, job_node):
        job_dict = {}
        for element in job_node.iterchildren():
            # check and replace the literal null with blank string
            if element.text == 'null':
                job_dict[element.tag] = self.unescape('')
            else:
                job_dict[element.tag] = self.unescape(element.text)
        return job_dict
        
    @staticmethod
    def markdown_to_html(description):
        markdowner = markdown2.Markdown(extras={'demote-headers': 3})
        # convert markdown to html
        html_description = markdowner.convert(description)
        # Remove code blocks
        html_description = html_description.replace('<code>', '').replace(
            '</code>', '').replace('<pre>', '').replace('</pre>', '')
        return html_description

    @staticmethod
    def text_to_html(description):
        return linebreaks(description)

    @staticmethod
    def location(job_node):
        if job_node['city'] and job_node['state_short']:
            return job_node['city'].title() + ', ' + job_node['state_short'].upper()
        elif job_node['city'] and job_node['country_short']:
            return job_node['city'].title() + ', ' + job_node['country_short'].upper()
        elif job_node['state'] and job_node['country_short']:
            return job_node['state'] + ', ' + job_node['country_short'].upper()
        elif job_node['country']:
            return 'Virtual, ' + job_node['country_short']
        else:
            return 'Global'

    def solr_job_dict(self, job_node):
        """
        Creates a dictionary for a solr job from a job_node in the xml feed.
        Assumes that job_node is a bottom level node

        """
        job_dict = {}
        # Convert the xml element to a dictionary for easier handling
        job_node = self.node_to_dict(job_node)
    
        job_node['location'] = self.location(job_node)

        job_node['date_created'] = get_strptime(job_node['date_created'], 
                                                self.datetime_pattern)
        job_node['date_modified'] = get_strptime(job_node['date_modified'], 
                                                 self.datetime_pattern)
        job_node['date_added'] = datetime.datetime.now()

        onets = job_node.get('onet_code', '')
        if onets:
            onets = onets.split(',')
            onets = [self.clean_onet(onet).strip() for onet in onets]
        else:
            onets = ''
        job_node['onet_code'] = onets

        if self.markdown:
            html_description = DEJobFeed.markdown_to_html(job_node['description'])
        else:
            html_description = DEJobFeed.text_to_html(job_node['description'])

        country_slab = self.country_slab(job_node)
        city_slab = self.city_slab(job_node)
        state_slab = self.state_slab(job_node)
        title_slab = self.title_slab(job_node)
        mocs = self.job_mocs(job_node)
        moc_tups = self.moc_data(mocs)
        mapped_moc_tups = self.mapped_mocs(mocs, job_node)
        
        job_dict['job_source_name'] = self.job_source_name
        job_dict['all_locations'] = [job_node['zip'], job_node['city'], job_node['state'],
                                     job_node['state_short'], "%s, %s" % (job_node['city'], job_node['state']),
                                     job_node['country']]
        job_dict['buid'] = self.jsid 
        job_dict['city'] = job_node['city']
        job_dict['city_ac'] = job_node['city']
        job_dict['city_exact'] = job_node['city']
        job_dict['city_slab'] = city_slab
        job_dict['city_slab_exact'] = city_slab
        job_dict['city_slug'] = slugify(job_node['city'])
        job_dict['company'] = job_node['company']
        company_slab = self.co_slab(job_dict['company'])
        company_buid_slab = "%s::%s" % (job_node['company'], self.jsid)
        if self.company:
            job_dict['company_canonical_microsite'] = getattr(self.company, "canonical_microsite", "")
            job_dict['company_canonical_microsite_exact'] = getattr(self.company, "canonical_microsite", "")
            job_dict['company_enhanced'] = self.company.enhanced
            job_dict['company_member'] = self.company.member
            job_dict['company_digital_strategies_customer'] = self.company.digital_strategies_customer
        job_dict['company_ac'] = job_node['company']
        job_dict['company_exact'] = job_node['company']
        job_dict['company_slab'] = company_slab
        job_dict['company_slab_exact'] = company_slab
        job_dict['company_buid_slab'] = company_buid_slab
        job_dict['company_buid_slab_exact'] = company_buid_slab
        job_dict['country'] = job_node['country']
        job_dict['country_ac'] = job_node['country']
        job_dict['country_exact'] = job_node['country']
        job_dict['country_short'] = job_node['country_short']
        job_dict['country_slab'] = country_slab
        job_dict['country_slab_exact'] = country_slab
        job_dict['country_slug'] = slugify(job_node['country'])
        job_dict['date_new'] = job_node['date_created']
        job_dict['date_new_exact'] = job_node['date_created']
        job_dict['date_updated'] = job_node['date_modified']
        job_dict['date_updated_exact'] = job_node['date_modified']
        job_dict['description'] = job_node['description']
        job_dict['federal_contractor'] = job_node['fc']
        job_dict['full_loc'] = self.full_loc(job_node)
        job_dict['full_loc_exact'] = self.full_loc(job_node)
        job_dict['html_description'] = html_description
        job_dict['ind'] = self.industries
        job_dict['link'] = job_node['link']
        job_dict['guid'] = guid_from_link(job_node['link'])
        job_dict['location'] = job_node['location']
        job_dict['location_exact'] = job_node.get('location')
        job_dict['moc'], job_dict['moc_exact'] = moc_tups.codes, moc_tups.codes
        job_dict['moc_slab'], job_dict['moc_slab_exact'] = (moc_tups.slabs,
                                                            moc_tups.slabs)
        job_dict['mocid'] = moc_tups.ids
        job_dict['mapped_moc'] = mapped_moc_tups.codes
        job_dict['mapped_moc_exact'] = mapped_moc_tups.codes
        job_dict['mapped_moc_slab'] = mapped_moc_tups.slabs
        job_dict['mapped_moc_slab_exact'] = mapped_moc_tups.slabs
        job_dict['mapped_mocid'] = mapped_moc_tups.ids
        job_dict['network'] = 'False' if 2649 < self.jsid < 2704 else 'True'
        job_dict['onet'] = job_node['onet_code']
        job_dict['onet_exact'] = job_node['onet_code']
        job_dict['reqid'] = job_node['reqid']
        job_dict['salted_date'] = self.date_salt(job_node['date_created'])
        job_dict['staffing_code'] = job_node['staffing_code']
        job_dict['state'] = job_node['state']
        job_dict['state_ac'] = job_node['state']
        job_dict['state_exact'] = job_node['state']
        job_dict['state_short'] = job_node['state_short']
        job_dict['state_short_exact'] = job_node['state_short']
        job_dict['state_slab'] = state_slab
        job_dict['state_slab_exact'] = state_slab
        job_dict['state_slug'] = slugify(job_node['state'])
        job_dict['title'] = job_node['title']
        job_dict['title_ac'] = job_node['title']
        job_dict['title_exact'] = job_node['title']
        job_dict['title_slab'] = title_slab
        job_dict['title_slab_exact'] = title_slab
        job_dict['title_slug'] = slugify(job_node['title'])
        job_dict['uid'] = job_node['uid']
        job_dict['zipcode'] = job_node['zip']

        # Post-a-job specific fields
        job_dict['is_posted'] = False

        # Determine what sites these jobs should be on
        if self.bu:
            on_sites = set(self.bu.site_packages.values_list('pk', flat=True))
            on_sites = filter(None, on_sites)
            job_dict['on_sites'] = on_sites or [0]
        else:
            job_dict['on_sites'] = [0]

        # Custom fields defined originally as part of Haystack and incorporated
        # into our application. Except 'id', which is the uniqueKey for our
        # index (think primary key for a database).
        job_dict['id'] = 'seo.joblisting.' + job_dict['uid']
        job_dict['django_id'] = 0
        job_dict['django_ct'] = 'seo.joblisting'
        job_dict['text'] = " ".join([(job_dict.get(k) or "None") for k
                                     in text_fields])
        return job_dict


class DEv2JobFeed(DEJobFeed):
    """
    Transform an XML feed file from DirectEmployers Foundation into database-
    and Solr-ready data structures.

    """
    def __init__(self, *args, **kwargs):
        self.schema = etree.XMLSchema(etree.parse("feed_schema.xsd"))
        kwargs.update({'js_field': 'job_source_name'})
        kwargs.update({'schema': self.schema})
        try:
            super(DEv2JobFeed, self).__init__(*args, **kwargs)
        except etree.XMLSyntaxError:
            pass
        else:
            self.errors = False
            self.error_messages = []
        finally:
            self.create_parse_error_message(self.parser.error_log)

    def create_parse_error_message(self, error_log):
        """Creates jobfeed error messages from schema validation fail"""
        # We're sending one email for every validation error. This is going to
        # cause an email explosion if for some reason there is a mass error in
        # the system that creates the feed files. Definitely, definitely want
        # to build this out so that it aggregates messages and, after either a
        # certain period of time or a certain number of errors, it sends a
        # single email.
        #
        # I would think the cache key would be a composite of the timestamp the
        # first error was cached and a list containing the data in
        # ``self.error_messages`` below. If a certain number of minutes have
        # passed since the timestamp, send the email. Alternatively, if the
        # size of the errors list grows beyond some limit, like 20, send the
        # email and clear that cache key.
        if len(error_log) > 0:
            self.errors = True
            exc = error_log.last_error
            self.error_messages = {'exception': exc.message, 'line': exc.line}
        else:
            self.errors = False
            self.error_messages = []

    def jobparse(self):
        joblist = []
        jobs = self.doc.find(self.node_tag).iterchildren()

        for job in jobs:
            attr = job.find('uid')
            jobdict = {'uid': self.unescape(attr.text)}
            joblist.append(jobdict)
        return joblist

    
def get_strptime(ts, pattern):
    """Convert a datetime string to a datetime object."""
    if not ts:
        return None
    else:
        return datetime.datetime.fromtimestamp(time.mktime(
            time.strptime(ts, pattern)))


def guid_from_link(link):
    """
    Returns the guid from a jcnlx link.

    >>> guid_from_link('http://jcnlx.com/8FA6F9676C914E0B96A5C5A3C19317B010')
    8FA6F9676C914E0B96A5C5A3C19317B0

    """
    url = urlparse(link)
    return url.path.replace("/", "")[:32] if url and url.path else ''


def get_mapped_mocs(bu, onets):
    """For a given job, determine any custom onet mappings that override the 
    defaults.
    Input:
        :bu: The businessUnit this job is associated with
        :onets: The onets associated with this job.
    """
    original = set(DEJobFeed.job_mocs({'onet_code': onets}))
    content_type = ContentType.objects.get_for_model(BusinessUnit)
    mappings = CustomCareer.objects.filter(object_id=bu.pk,
                                           content_type=content_type,
                                           onet__in=onets).select_related()
    mappings = set([map.moc for map in mappings])
    return DEJobFeed.moc_data(mappings | original)
