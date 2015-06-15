import datetime
import logging

from dateutil.parser import parse as date_parse
from django.utils.encoding import force_text
from lxml import etree
from seo.models import Company, Country, Redirect
from slugify import slugify
from xmlparse import DEJobFeed, get_strptime, text_fields, get_mapped_mocs
import uuid

logger = logging.getLogger(__name__)

states = {
    "AB": "Alberta",
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AZ": "Arizona",
    "BC": "British Columbia",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DC": "District Of Columbia",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MB": "Manitoba",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MP": "Northern Mariana Islands",
    "MS": "Mississippi",
    "MT": "Montana",
    "NB": "New Brunswick",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NL": "Newfoundland",
    "NM": "New Mexico",
    "NS": "Nova Scotia",
    "NU": "Territory of Nunavut",
    "NV": "Nevada",
    "NW": "Northwest Territories",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "ON": "Ontario",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "PE": "Prince Edward Island",
    "PR": "Puerto Rico",
    "QC": "Quebec",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "SK": "Saskatchewan",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
    "YT": "Yukon Territory"
}


def transform_for_postajob(job):
    """
    Cleans a job coming from My.jobs post-a-job. This should add any
    required fields, and re-format any fields that are not coming in
    in the required format.

    inputs:
        :job: A dictionary with the following fields: postajob.job.id (id),
            city, company.id (company), country, country_short, date_new,
            date_updated, description, guid, link, on_sites, state,
            state_short, reqid, title, uid, and zipcode.

    outputs:
        A solr-ready job as a dictionary

    """
    try:
        company = Company.objects.get(id=job['company'])
    except Company.DoesNotExist:
        return None

    job['date_new'] = _clean_time(job['date_new'])
    job['date_updated'] = _clean_time(job['date_updated'])

    solr_job = {'is_posted': True}
    on_sites = job.get('on_sites', '0')

    if not on_sites:
        solr_job['on_sites'] = ''
    else:
        solr_job['on_sites'] = [str(x) for x in on_sites.split(',')]

    solr_job['id'] = 'postajob.job.%s' % job['guid']
    # This has to be seo.joblisting, otherwise the jobs won't be included
    # in the search results.
    solr_job['django_ct'] = 'seo.joblisting'
    solr_job['django_id'] = 0
    solr_job['city_slug'] = slugify(job['city'])
    solr_job['country_short'] = job['country_short']
    solr_job['date_updated_exact'] = job['date_updated']
    solr_job['job_source_name'] = 'Post-a-Job'
    solr_job['date_updated'] = job['date_updated']
    solr_job['salted_date'] = DEJobFeed.date_salt(job['date_updated'])
    solr_job['reqid'] = job['reqid']
    solr_job['company_digital_strategies_customer'] = company.digital_strategies_customer
    solr_job['guid'] = job['guid']
    solr_job['uid'] = job['id']
    solr_job['company_member'] = company.member
    solr_job['city'] = job['city']
    solr_job['date_new'] = job['date_new']
    solr_job['country_exact'] = job['country']
    solr_job['country_slug'] = slugify(job['country'])
    solr_job['company_ac'] = company.name
    solr_job['html_description'] = DEJobFeed.markdown_to_html(job['description'])
    solr_job['state'] = job['state']
    solr_job['country_ac'] = job['country']
    solr_job['city_ac'] = job['city']
    solr_job['state_short_exact'] = job['state_short']
    solr_job['title_ac'] = job['title']
    solr_job['company_canonical_microsite'] = company.canonical_microsite
    solr_job['description'] = job['description']
    solr_job['state_ac'] = job['state']
    solr_job['company'] = company.name
    solr_job['state_short'] = job['state_short']
    solr_job['title_exact'] = job['title']
    solr_job['link'] = job.get('link', '')
    solr_job['apply_info'] = job.get('apply_info', '')
    solr_job['company_enhanced'] = company.enhanced
    solr_job['state_slug'] = slugify(job['state'])
    solr_job['city_exact'] = job['city']
    solr_job['title_slug'] = slugify(job['title'])
    solr_job['state_exact'] = job['state']
    solr_job['zipcode'] = job['zipcode']
    solr_job['title'] = job['title']
    solr_job['date_new_exact'] = job['date_new']
    solr_job['country'] = job['country']
    solr_job['company_exact'] = company.name
    solr_job['company_canonical_microsite_exact'] = company.canonical_microsite

    # Requires city, state_short, state, and country_short to be filled
    # in on solr_job to work.
    solr_job['location'] = DEJobFeed.location(solr_job)
    # Requires city, state, location, and country to be filled in on
    # solr_jobs.
    solr_job['full_loc'] = DEJobFeed.full_loc(solr_job)
    solr_job['full_loc_exact'] = solr_job['full_loc']
    solr_job['company_slab'] = DEJobFeed.co_slab(company.name)
    # Requires solr_job['country_short'], solr_job['state'], and
    # solr_job['city'] to already be filled in.
    solr_job['city_slab'] = DEJobFeed.city_slab(solr_job)
    # Requires solr_job['country_short'] and solr_job['state'] to already be
    # filled in.
    solr_job['state_slab'] = DEJobFeed.state_slab(solr_job)
    # Requires solr_job['country_short'] to already be filled in.
    solr_job['country_slab'] = DEJobFeed.country_slab(solr_job)
    # Requires solr_job['title'] to already be filled in.
    solr_job['title_slab'] = DEJobFeed.title_slab(solr_job)

    solr_job['location_exact'] = solr_job['location']
    solr_job['state_slab_exact'] = solr_job['state_slab']
    solr_job['company_slab_exact'] = solr_job['company_slab']
    solr_job['country_slab_exact'] = solr_job['country_slab']
    solr_job['city_slab_exact'] = solr_job['city_slab']
    solr_job['title_slab_exact'] = solr_job['title_slab']

    solr_job['text'] = " ".join([force_text((job.get(k)) or "None") for k in
                                 text_fields])

    return solr_job


def hr_xml_to_json(xml, business_unit):
    """
    Cleans a job coming from an HR-XML document. This should add any
    required fields, and re-format any fields that are not coming in
    in the required format.

    This function is also used for markdown testing, and should not make
    any changes to the database or solr.

    inputs:
        :xml: an HR-XML document
        :business unit: the business unit the job is coming from
        :create_redirect: flags whether or not a redirect for the job link
                          should be added to the redirect table

    outputs:
        A solr-ready job as a dictionary

    """
    # Clean up the xml document
    for elem in xml.getiterator():
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i + 1:]
    etree.cleanup_namespaces(xml)

    # Get some useful references
    app = xml.xpath('.//ApplicationArea')[0]
    data = xml.xpath('.//PositionOpening')[0]

    guid = data.find(".//*[@schemeName='juid']").text
    logger.debug("Parsing job %s", guid)

    reqid = data.find(".//*[@schemeName='reqid']").text
    city = data.find('.//CityName').text
    city = city if city not in ['', 'XX'] else None
    state_code = data.find('.//CountrySubDivisionCode').text
    state_short = state_code if state_code in states.keys() else None
    state = states.get(state_code, None)
    country_short = data.find('.//CountryCode').text
    if country_short in [None, '', 'XXX']:
        country = country_short = ""
    else:
        country = Country.objects.get(abbrev=country_short).name
    title = data.find('.//PositionTitle').text
    description = data.find('.//PositionFormattedDescription/Content').text
    link = data.find('.//Communication/URI').text
    zipcode = data.find('.//PostalCode')
    zipcode = zipcode.text if zipcode != None else ""

    latitude = data.find('.//SpatialLocation/Latitude').text
    longitude = data.find('.//SpatialLocation/Longitude').text

    # Lookup the company.  (Assumes that company is 1-to-1 on BusinessUnit)
    try:
        company = business_unit.company_set.all()[0]
    except Company.DoesNotExist, Company.MultipleObjectsReturned:
        logger.error("Unable to find Company for BusinessUnit %s",
                     business_unit)
        return None

    job = {'is_posted': False}
    # Use dateutil here because datetime.strptime does not support this format.
    try:
        date_new = data.get('validFrom')
        job['date_new'] = date_parse(date_new).replace(tzinfo=None)
        updated = date_parse(app.find('.//CreationDateTime').text)
        job['date_updated'] = updated.replace(tzinfo=None)
        job['date_added'] = datetime.datetime.now()
    except ValueError:
        logger.error("Unable to parse string %s as a date", date_new)
        raise

    # Determine what sites these jobs should be on
    on_sites = set(business_unit.site_packages.values_list('pk', flat=True))
    on_sites = filter(None, on_sites)
    job['on_sites'] = on_sites or [0]


    # This has to be seo.joblisting, otherwise the jobs won't be included
    # in the search results.
    job['id'] = 'seo.joblisting.%s' % guid.replace('-', '')
    job['all_locations'] = [zipcode, city, state, state_short,
                                "%s, %s" % (city, state), country]
    job['django_ct'] = 'seo.joblisting'
    job['django_id'] = 0
    job['city_slug'] = slugify(city)
    job['country_short'] = country_short
    job['date_updated_exact'] = job['date_updated']
    job['job_source_name'] = business_unit.title
    job['salted_date'] = DEJobFeed.date_salt(job['date_updated'])
    job['buid'] = business_unit.id
    job['reqid'] = reqid
    job['company_digital_strategies_customer'] = company.digital_strategies_customer
    job['guid'] = guid.replace('-', '')
    job['uid'] = ""
    job['company_member'] = company.member
    job['city'] = city
    job['country'] = country
    job['country_exact'] = country
    job['country_slug'] = slugify(country)
    job['company_ac'] = company.name
    job['html_description'] = DEJobFeed.markdown_to_html(description)
    job['state'] = state
    job['country_ac'] = country
    job['city_ac'] = city
    job['state_short_exact'] = state_short
    job['title_ac'] = title
    job['company_canonical_microsite'] = company.canonical_microsite
    job['description'] = description
    job['state_ac'] = state
    job['company'] = company.name
    job['company_buid_slab'] = "%s::%s" % (company.name, business_unit.id)
    job['state_short'] = state_short
    job['title_exact'] = title
    job['link'] = link
    job['company_enhanced'] = company.enhanced
    job['state_slug'] = slugify(state)
    job['city_exact'] = city
    job['title_slug'] = slugify(title)
    job['state_exact'] = state
    job['zipcode'] = zipcode
    job['title'] = title
    job['date_new_exact'] = job['date_new']
    job['country'] = country
    job['company_exact'] = company.name
    job['company_canonical_microsite_exact'] = company.canonical_microsite

    # Requires city, state_short, state, and country_short to be filled
    # in on job to work.
    job['location'] = DEJobFeed.location(job)
    # Requires city, state, location, and country to be filled in on
    # jobs.
    job['full_loc'] = DEJobFeed.full_loc(job)
    job['full_loc_exact'] = job['full_loc']
    job['company_slab'] = DEJobFeed.co_slab(company.name)
    # Requires job['country_short'], job['state'], and
    # job['city'] to already be filled in.
    job['city_slab'] = DEJobFeed.city_slab(job)
    # Requires job['country_short'] and job['state'] to already be
    # filled in.
    job['state_slab'] = DEJobFeed.state_slab(job)
    # Requires job['country_short'] to already be filled in.
    job['country_slab'] = DEJobFeed.country_slab(job)
    # Requires job['title'] to already be filled in.
    job['title_slab'] = DEJobFeed.title_slab(job)

    job['location_exact'] = job['location']
    job['state_slab_exact'] = job['state_slab']
    job['company_slab_exact'] = job['company_slab']
    job['company_buid_slab_exact'] = job['company_buid_slab']
    job['country_slab_exact'] = job['country_slab']
    job['city_slab_exact'] = job['city_slab']
    job['title_slab_exact'] = job['title_slab']

    onets = [node.text for node in data.findall('.//JobCategoryCode')]
    onets = set(DEJobFeed.clean_onet(onet) for onet in onets)
    job['onet'] = job['onet_exact'] = list(onets)

    # Standard Mocs
    mocs = DEJobFeed.job_mocs({'onet_code': job['onet']})
    moc_tups = DEJobFeed.moc_data(mocs)
    job['moc'] = job['moc_exact'] = moc_tups.codes
    job['moc_slab'] = job['moc_slab_exact'] = moc_tups.slabs
    job['mocid'] = moc_tups.ids

    # Mapped Mocs
    mapped_moc_tup = get_mapped_mocs(business_unit, onets)
    job['mapped_moc'] = job['mapped_moc_exact'] = mapped_moc_tup.codes
    job['mapped_moc_slab'] = job['mapped_moc_slab_exact'] = mapped_moc_tup.slabs
    job['mapped_mocid'] = mapped_moc_tup.ids

    job['text'] = " ".join([force_text((job.get(k)) or "None") for k in
                            text_fields])

    job['GeoLocation'] = ("%s, %s" % (latitude, longitude)
                          if latitude and longitude else None)
    job['lat_long_buid_slab'] = "%s::%s::%s" % (latitude, longitude,
                                                business_unit.id)
    job['lat_long_buid_slab_exact'] = job['lat_long_buid_slab']

    return job


def _clean_time(time):
    """
    Trys to turn a str(datetime) to datetime. Checks for formats with
    and without microsecond. Does not handle utc offsets.

    """
    try:
        return get_strptime(time, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        try:
            return get_strptime(time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.datetime.now()


def make_redirect(job, business_unit):
    """Given a job dictionary, make a redirect record

    Input:
        :job: A dictionary describing a job.
    :return: a redirect"""
    location = "%s-%s" % (job['state_short'], job['city_slab_exact'])

    # Get or create doesn't support not saving, and Redirects are not valid to
    # save until new_date is set.
    guid = '{%s}' % str(uuid.UUID(job['guid'])).upper()
    try:
        redirect = Redirect.objects.get(guid=guid)
        redirect.url = job['link']
        redirect.save()
        return redirect
    except Redirect.DoesNotExist:
        logger.debug("Creating new redirect for guid %s", guid)
        redirect = Redirect(guid=guid,
                            buid=business_unit.id,
                            uid=None,
                            url=job['link'],
                            new_date=job['date_new'],
                            expired_date=None,
                            job_location=location,
                            job_title=job['title_exact'],
                            company_name=job['company'])
        redirect.save()
        return redirect
