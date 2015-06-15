from S3 import CallingFormat

from default_settings import *
from dseo_celery import *
from secrets import PROD_DB_PASSWD


DATABASES = {
    'default': {
        'NAME': 'redirect',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'de_dbuser',
        'PASSWORD': PROD_DB_PASSWD,
        'HOST': 'db-redirectstaging.c9shuxvtcmer.us-east-1.rds.amazonaws.com',
        'PORT': '3306',
    },
    'api': {
        'NAME': 'api',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'de_dbuser',
        'PASSWORD': PROD_DB_PASSWD,
        'HOST': 'db-redirectstaging.c9shuxvtcmer.us-east-1.rds.amazonaws.com',
        'PORT': '3306',
    },
    'qc-redirect': {
        'NAME': 'redirect',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'de_dbuser',
        'PASSWORD': PROD_DB_PASSWD,
        'HOST': 'db-redirectqc.c9shuxvtcmer.us-east-1.rds.amazonaws.com',
        'PORT': '3306',
    },
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://ec2-50-19-85-235.compute-1.amazonaws.com:8983/solr',
        'HTTP_AUTH_USERNAME': SOLR_AUTH['username'],
        'HTTP_AUTH_PASSWORD': SOLR_AUTH['password']
    },
    'groups': {
        'ENGINE': 'saved_search.groupsearch.SolrGrpEngine',
        'URL': 'http://ec2-50-19-85-235.compute-1.amazonaws.com:8983/solr',
        'HTTP_AUTH_USERNAME': SOLR_AUTH['username'],
        'HTTP_AUTH_PASSWORD': SOLR_AUTH['password']
    }
}

TEMPLATE_DIRS = (
    '/home/web/direct-seo/directseo/templates/',
)

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

ROOT_URLCONF = 'dseo_urls'
MIDDLEWARE_CLASSES += ('wildcard.middleware.WildcardMiddleware', )
TEMPLATE_CONTEXT_PROCESSORS += (
    "social_links.context_processors.social_links_context",
    "seo.context_processors.site_config_context",
)

SOLR = {
    'all': 'http://ec2-23-20-67-65.compute-1.amazonaws.com:8983/solr/myjobs_test/',
    'current': 'http://ec2-23-20-67-65.compute-1.amazonaws.com:8983/solr/myjobs_test_current/',
    }

ABSOLUTE_URL = 'http://qc.secure.my.jobs/'

PROJECT = "dseo"
