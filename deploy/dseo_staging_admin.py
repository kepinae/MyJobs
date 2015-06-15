import datetime

from default_settings import *
from dseo_celery import *
from secrets import PROD_DB_PASSWD


ALLOWED_HOSTS = ['*', ]


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


SESSION_CACHE_ALIAS = 'sessions'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'VERSION': str(datetime.date.fromtimestamp(os.path.getmtime('.'))),
        'LOCATION': [
            'staging-mc-cluster.qksjst.0001.use1.cache.amazonaws.com:11211'
        ]
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            'staging-mc-cluster.qksjst.0001.use1.cache.amazonaws.com:11211'
        ]
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'seo.search_backend.DESolrEngine',
        'URL': 'http://ec2-54-242-14-151.compute-1.amazonaws.com:8983/solr',
        'TIMEOUT': 300,
        'HTTP_AUTH_USERNAME': SOLR_AUTH['username'],
        'HTTP_AUTH_PASSWORD': SOLR_AUTH['password']
    },
    'groups': {
        'ENGINE': 'saved_search.groupsearch.SolrGrpEngine',
        'URL': 'http://ec2-54-242-14-151.compute-1.amazonaws.com:8983/solr',
        'TIMEOUT': 300,
        'HTTP_AUTH_USERNAME': SOLR_AUTH['username'],
        'HTTP_AUTH_PASSWORD': SOLR_AUTH['password']
    }
}

ROOT_URLCONF = 'dseo_urls'
MIDDLEWARE_CLASSES += ('wildcard.middleware.WildcardMiddleware', )
WILDCARD_REDIRECT=False
TEMPLATE_CONTEXT_PROCESSORS += (
    "social_links.context_processors.social_links_context",
    "seo.context_processors.site_config_context",
)

SOLR = {
    'all': 'http://ec2-23-20-67-65.compute-1.amazonaws.com:8983/solr/myjobs_test/',
    'current': 'http://ec2-23-20-67-65.compute-1.amazonaws.com:8983/solr/myjobs_test_current/',
    }

ABSOLUTE_URL = 'http://staging.my.jobs/'

PROJECT = "dseo"

BROKER_HOST = '204.236.236.123'
BROKER_PORT = 5672
BROKER_USER = 'celery'
BROKER_VHOST = 'dseo-qc'

CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'dseo.default'
CELERY_QUEUES = {
    'dseo': {
        'binding_key': 'dseo.#'
    },
    'solr': {
        'binding_key': 'solr.#'
    }
}
CELERY_ROUTES = {
    'tasks.task_update_solr': {
        'queue': 'solr',
        'routing_key': 'solr.update_solr'
    },
    'tasks.task_clear_solr': {
        'queue': 'solr',
        'routing_key': 'solr.clear_solr'
    },
    'tasks.etl_to_solr': {
        'queue': 'solr',
        'routing_key': 'solr.update_solr'
    },
}
