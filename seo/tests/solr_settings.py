# -*- coding: utf-8 -*-
import datetime

from settings import *

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'seo.tests.setup.TestDESolrEngine',
        'URL': 'http://127.0.0.1:8983/solr/seo',
        'INCLUDE_SPELLING': True,
    },
}

SOLR_FIXTURE = [
    {
        'buid': 0,
        'city': 'Indianapolis',
        'city_ac': 'Indianapolis',
        'city_exact': 'Indianapolis',
        'city_slab': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',        
        'city_slab_exact': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',
        'city_slug': 'indianapolis',
        'company': 'Test Company',
        'company_ac': 'Test Company',
        'company_exact': 'Test Company',
        'company_slab': 'test-company/careers::Test Company',
        'company_slab_exact': 'test-company/careers::Test Company',
        'country': 'United States',
        'country_ac': 'United States',
        'country_exact': 'United States',
        'country_short': 'USA',
        'country_slab': 'usa/jobs::United States',
        'country_slab_exact': 'usa/jobs::United States',
        'country_slug': 'united-states',
        'date_new': datetime.datetime.now(),
        'date_new_exact': datetime.datetime.now(),
        'date_updated': datetime.datetime.now(),
        'date_updated_exact': datetime.datetime.now(),
        'description': u'# This is a **description** of a # 1 #job. It might contain 特殊字符.',
        'django_ct': 'seo.joblisting',
        'django_id': 1,
        'full_loc': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'full_loc_exact': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'guid': '1'*32,
        'id': 'seo.joblisting.1',
        'is_posted': False,
        'location': 'Indianapolis, IN',
        'location_exact': 'Indianapolis, IN',
        'onet': 100,
        'onet_exact': 100,
        'on_sites': [0],
        'reqid': 'AAA000001',
        'state': 'Indiana',
        'state_ac': 'Indiana',
        'state_exact': 'Indiana',
        'state_short': 'IN',
        'state_short_exact': 'IN',
        'state_slab': 'indiana/usa/jobs::Indiana',
        'state_slab_exact': 'indiana/usa/jobs::Indiana',
        'state_slug': 'indiana',
        'text': u'This is a description of a job. It might contain 特殊字符.',
        'title': u'Retail Associate Розничная ассоциированных',
        'title_ac': u'Retail Associate Розничная ассоциированных',
        'title_exact': u'Retail Associate Розничная ассоциированных',
        'title_slab': u'retail-associate-розничная-ассоциированных/jobs-in::Retail Associate Розничная ассоциированных',
        'title_slab_exact': u'retail-associate-розничная-ассоциированных/jobs-in::Retail Associate Розничная ассоциированных',
        'title_slug': u'retail-associate-розничная-ассоциированных',
        'uid': "1000",
        'link': 'mailto:apply@test.jobs',
        'lat_long_buid_slab_exact': '-32.202924::-64.404945::0'
    },
    {
        'buid': 0,
        'city': 'Indianapolis',
        'city_ac': 'Indianapolis',
        'city_exact': 'Indianapolis',
        'city_slab': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',
        'city_slab_exact': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',
        'city_slug': 'indianapolis',
        'company': 'Acme',
        'company_ac': 'Acme',
        'company_exact': 'Acme',
        'company_slab': 'acme/careers::Acme',
        'company_slab_exact': 'acme::Acme',
        'country': 'United States',
        'country_ac': 'United States',
        'country_exact': 'United States',
        'country_short': 'USA',
        'country_slab': 'usa/jobs::United States',
        'country_slab_exact': 'usa/jobs::United States',
        'country_slug': 'united-states',
        'date_new': datetime.datetime.now(),
        'date_new_exact': datetime.datetime.now(),
        'date_updated': datetime.datetime.now(),
        'date_updated_exact': datetime.datetime.now(),
        'description': u'This is a description of a job. It might contain 特殊字符.',
        'django_ct': 'seo.joblisting',
        'django_id': 2,
        'full_loc': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'full_loc_exact': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'guid': '2'*32,
        'id': 'seo.joblisting.2',
        'is_posted': False,
        'location': 'Indianapolis, IN',
        'location_exact': 'Indianapolis, IN',
        'onet': 100,
        'onet_exact': 100,
        'on_sites': [0],
        'reqid': 'AAA000002',
        'state': 'Indiana',
        'state_ac': 'Indiana',
        'state_exact': 'Indiana',
        'state_short': 'IN',
        'state_short_exact': 'IN',
        'state_slab': 'indiana/usa/jobs::Indiana',
        'state_slab_exact': 'indiana/usa/jobs::Indiana',
        'state_slug': 'indiana',
        'text': 'témp',
        'title': 'Retail Associate',
        'title_ac': 'Retail Associate',
        'title_exact': 'Retail Associate',
        'title_slab': 'retail-associate/jobs-in::Retail Associate',
        'title_slab_exact': 'retail-associate/jobs-in::Retail Associate',
        'title_slug': 'retail-associate',
        'uid': "1001",
        'link': 'http://my.jobs/EE45273E6D914AED8CB3C9C59D203F4410',
        'lat_long_buid_slab_exact': '-32.202924::-64.404945::0'
    },
]


POSTED_JOB_FIXTURE = [
    {
        'buid': 0,
        'city': 'Indianapolis',
        'city_ac': 'Indianapolis',
        'city_exact': 'Indianapolis',
        'city_slab': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',
        'city_slab_exact': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',
        'city_slug': 'indianapolis',
        'company': 'Acme',
        'company_ac': 'Acme',
        'company_exact': 'Acme',
        'company_slab': 'acme/careers::Acme',
        'company_slab_exact': 'acme::Acme',
        'country': 'United States',
        'country_ac': 'United States',
        'country_exact': 'United States',
        'country_short': 'USA',
        'country_slab': 'usa/jobs::United States',
        'country_slab_exact': 'usa/jobs::United States',
        'country_slug': 'united-states',
        'date_new': datetime.datetime.now(),
        'date_new_exact': datetime.datetime.now(),
        'date_updated': datetime.datetime.now(),
        'date_updated_exact': datetime.datetime.now(),
        'description': u'This is a description of a job. It might contain 特殊字符.',
        'django_ct': 'seo.joblisting',
        'django_id': 'postajob.job.3',
        'full_loc': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'full_loc_exact': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'guid': '7'*32,
        'id': 'postajob.job.3',
        'is_posted': False,
        'location': 'Indianapolis, IN',
        'location_exact': 'Indianapolis, IN',
        'onet': 100,
        'onet_exact': 100,
        'on_sites': [0],
        'reqid': '1',
        'state': 'Indiana',
        'state_ac': 'Indiana',
        'state_exact': 'Indiana',
        'state_short': 'IN',
        'state_short_exact': 'IN',
        'state_slab': 'indiana/usa/jobs::Indiana',
        'state_slab_exact': 'indiana/usa/jobs::Indiana',
        'state_slug': 'indiana',
        'text': 'témp',
        'title': 'Retail Associate',
        'title_ac': 'Retail Associate',
        'title_exact': 'Retail Associate',
        'title_slab': 'retail-associate/jobs-in::Retail Associate',
        'title_slab_exact': 'retail-associate/jobs-in::Retail Associate',
        'title_slug': 'retail-associate',
        'uid': "9999",
        'link': 'http://my.jobs/1'
    },
    {
        'buid': 0,
        'city': 'Indianapolis',
        'city_ac': 'Indianapolis',
        'city_exact': 'Indianapolis',
        'city_slab': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',
        'city_slab_exact': 'indianapolis/indiana/usa/jobs::Indianapolis, IN',
        'city_slug': 'indianapolis',
        'company': 'Acme',
        'company_ac': 'Acme',
        'company_exact': 'Acme',
        'company_slab': 'acme/careers::Acme',
        'company_slab_exact': 'acme::Acme',
        'country': 'United States',
        'country_ac': 'United States',
        'country_exact': 'United States',
        'country_short': 'USA',
        'country_slab': 'usa/jobs::United States',
        'country_slab_exact': 'usa/jobs::United States',
        'country_slug': 'united-states',
        'date_new': datetime.datetime.now(),
        'date_new_exact': datetime.datetime.now(),
        'date_updated': datetime.datetime.now(),
        'date_updated_exact': datetime.datetime.now(),
        'description': u'This is a description of a job. It might contain 特殊字符.',
        'django_ct': 'seo.joblisting',
        'django_id': 'postajob.job.2',
        'full_loc': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'full_loc_exact': 'city::Indianapolis@@state::Indiana@@location::Indianapolis, IN@@country::United States',
        'guid': '8'*32,
        'id': 'postajob.job.2',
        'is_posted': True,
        'location': 'Indianapolis, IN',
        'location_exact': 'Indianapolis, IN',
        'onet': 100,
        'onet_exact': 100,
        'on_sites': [3, 4],
        'reqid': '2',
        'state': 'Indiana',
        'state_ac': 'Indiana',
        'state_exact': 'Indiana',
        'state_short': 'IN',
        'state_short_exact': 'IN',
        'state_slab': 'indiana/usa/jobs::Indiana',
        'state_slab_exact': 'indiana/usa/jobs::Indiana',
        'state_slug': 'indiana',
        'text': 'témp',
        'title': 'Retail Associate',
        'title_ac': 'Retail Associate',
        'title_exact': 'Retail Associate',
        'title_slab': 'retail-associate/jobs-in::Retail Associate',
        'title_slab_exact': 'retail-associate/jobs-in::Retail Associate',
        'title_slug': 'retail-associate',
        'uid': "9998",
        'link': 'http://my.jobs/2'
    },
]
