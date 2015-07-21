from collections import OrderedDict
import djcelery
import os
import re
import sys

from celery.schedules import crontab
from os.path import abspath, dirname, basename, join

from secrets import *

djcelery.setup_loader()

_PATH = PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

APP = abspath(dirname(__file__))
PROJ_ROOT = abspath(dirname(__file__))
sys.path.append(APP)


DEBUG = False
TEMPLATE_DEBUG = DEBUG

ENVIRONMENT = 'Local'

WILDCARD_REDIRECT = True
NEVER_REDIRECT = ['amazonaws', ]

# NOTE: ADMINS and MANAGERS in local_settings.py or deploy_settings.py
# NOTE: Databse in local_settings.py or deploy_settings.py

ROOT_PATH = abspath(dirname(__file__))
PROJECT_NAME = basename(ROOT_PATH)

TIME_ZONE = 'America/New_York'
LANGUAGE_CODE = 'en-us'

USE_TZ = True
DATE_FORMAT = 'd-M-Y'
# Not a default Django setting, but form formatting differs from model
# formatting. Both are included for potential future l10n changes
# d-M-Y (model) == %d-%b-%Y (form)
FORM_DATE_FORMAT = '%d-%b-%Y'

# Dates of the format "25-Jun-2013" are not in the default list of allowed
# formats.
DATE_INPUT_FORMATS = (
    '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%b %d %Y', '%b %d, %Y',
    '%d %b %Y', '%d %b, %Y', '%B %d %Y', '%B %d, %Y', '%d %B %Y',
    '%d %B, %Y',
)

DATE_INPUT_FORMATS += (FORM_DATE_FORMAT,)

USE_I18N = True
I18N_URLS = False
USE_L10N = True

MEDIA_ROOT = os.path.join(_PATH, 'files', 'media')
MEDIA_URL = '/files/media/'

STATIC_ROOT = os.path.join(_PATH, 'collected_static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(PROJ_ROOT, 'static'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

ADMIN_MEDIA_PREFIX = '//d2e48ltfsb5exy.cloudfront.net/myjobs/admin/'

TEMPLATE_DIRS = (
    join(ROOT_PATH, 'templates'),
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
        'django.template.loaders.eggs.Loader',
    )),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'middleware.SiteRedirectMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',  # http auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'middleware.MultiHostMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'middleware.PasswordChangeRedirectMiddleware',
    'middleware.XsSharing',
    'django.middleware.locale.LocaleMiddleware',
    'middleware.CompactP3PMiddleware',
    'middleware.TimezoneMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'backends.CaseInsensitiveAuthBackend',
    'django.contrib.auth.backends.ModelBackend',  # default
    'django.contrib.auth.backends.RemoteUserBackend',  # http
)

# Celery settings
CELERY_RESULT_BACKEND = 'amqp'
CELERY_IMPORTS = ('tasks',)
CELERY_PREFETCH_MULTIPLIER = 0
CELERY_IGNORE_RESULTS = True
CELERY_TIMEZONE = 'US/Eastern'
CELERYBEAT_PIDFILE = '/var/run/celerybeat.pid'
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_QUEUES = {
    'dseo': {
        'binding_key': 'dseo.#'
    },
    'solr': {
        'binding_key': 'solr.#'
    },
    'priority': {
        'binding_key': 'priority.#'
    },
    'myjobs': {
        'binding_key': 'myjobs.#'
    },
    'sendgrid': {
        'binding_key': 'sendgrid.#'
    },
    'myemails': {
        'binding_key': 'myemails.#'
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
    'tasks.priority_etl_to_solr': {
        'queue': 'priority',
        'routing_key': 'priority.update_solr'
    },
    'tasks.task_clear_bu_cache': {
        'queue': 'priority',
        'routing_key': 'priority.clear_cache'
    },
    'tasks.send_search_digest': {
        'queue': 'myjobs',
        'routing_key': 'myjobs.send_search_digest'
    },
    'tasks.send_search_digests': {
        'queue': 'myjobs',
        'routing_key': 'myjobs.send_search_digests'
    },
    'tasks.delete_inactive_activations': {
        'queue': 'myjobs',
        'routing_key': 'myjobs.delete_inactive_activations',
    },
    'tasks.process_batch_events': {
        'queue': 'myjobs',
        'routing_key': 'myjobs.process_batch_events'
    },
    'tasks.expire_jobs': {},
    'tasks.update_solr_from_model': {
        'queue': 'myjobs',
        'routing_key': 'myjobs.expire_jobs'
    },
    'tasks.update_solr_from_log': {
        'queue': 'myjobs',
        'routing_key': 'myjobs.update_solr_from_log'
    },
    'tasks.submit_all_sitemaps': {
        'queue': 'myjobs',
        'routing_key': 'dseo.submit_all_sitemaps'
    },
    'tasks.send_event_email': {
        'queue': 'myemails',
        'routing_key': 'myemails.send_event_emails'
    },
    'tasks.process_sendgrid_event': {
        'queue': 'sendgrid',
        'routing_key': 'sendgrid.process_sendgrid_event',
    },
}
CELERYBEAT_SCHEDULE = {
    'weekly-partner-library-update': {
        'task': 'tasks.update_partner_library',
        'schedule': crontab(day_of_week='sun', hour=0, minute=0),
    },
    'daily-search-digest': {
        'task': 'tasks.send_search_digests',
        'schedule': crontab(minute=0, hour=10),
    },
    'daily-delete-activation': {
        'task': 'tasks.delete_inactive_activations',
        'schedule': crontab(minute=0, hour=2)
    },
    'daily-batch-processing': {
        'task': 'tasks.process_batch_events',
        'schedule': crontab(minute=0, hour=0),
    },
    'daily-job-expire': {
        'task': 'tasks.expire_jobs',
        'schedule': crontab(minute=0, hour=0),
    },
    'regular-solr-update': {
        'task': 'tasks.update_solr_from_model',
        'schedule': crontab(minute='*/5'),
    },
    'analytics-solr-update': {
        'task': 'tasks.update_solr_from_log',
        'schedule': crontab(hour='*/1'),
    },
    'morning-sitemap-ping': {
        'task': 'tasks.submit_all_sitemaps',
        'schedule': crontab(hour=13, minute=0)
    },
}


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'myjobs.context_processors.current_site_info',
    'myjobs.context_processors.absolute_url',
)

INTERNAL_IPS = ('127.0.0.1', '216.136.63.6',)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.flatpages',
    'django.contrib.redirects',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'djcelery',
    'django_jenkins',
    'widget_tweaks',
    #'south',
    'django_nose',
    'tastypie',
    'captcha',
    'endless_pagination',
    'storages',
    'django_extensions',
    'haystack',
    'saved_search',
    'taggit',
    'fsm',
    'compressor',
)

# Captcha SSL
RECAPTCHA_USE_SSL = True
CAPTCHA_AJAX = True

# Add all MyJobs apps here. This separation ensures that automated Jenkins tests
# only run on these apps
PROJECT_APPS = ('myjobs', 'myprofile', 'mysearches', 'registration',
                'mydashboard', 'mysignon', 'mymessages', 'mypartners',
                'solr', 'postajob', 'moc_coding', 'seo', 'social_links',
                'wildcard', 'myblocks', 'myemails', 
                'myreports', 'redirect', 'automation')

INSTALLED_APPS += PROJECT_APPS

JENKINS_TASKS = (
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
)

# Registration
ACCOUNT_ACTIVATION_DAYS = 90

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/home'

AUTH_USER_MODEL = 'myjobs.User'

SESSION_SAVE_EVERY_REQUEST = True

MANAGERS = ADMINS

# Logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s "
                      "[%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'verbose': {
            'format': ('%(levelname)s %(asctime)s %(module)s %(process)d '
                       '%(thread)d %(message)s')
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'file': {
            'filename': '/var/log/directseo/dseo.log',
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'backupCount': 3,
            'formatter': 'verbose'
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "/home/web/myjobslogs/logfile",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'logfile'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'myjobs': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'formatter': 'standard',
        },
        'tasks': {
            'handlers': ['console', 'logfile'],
            'level': 'INFO',
            'formatter': 'standard',
        },
        'pysolr': {
            'level': 'ERROR'
        },
        'views': {
            'level': 'INFO',
            'handlers': ['file']
        },
        'requests.packages.urllib3.connectionpool': {
            'level': 'ERROR'
        },
        'amqplib': {
            'level': 'INFO'
        },
        'factory': {
            'level': 'INFO'
        },
    }
}

GRAVATAR_URL_PREFIX = "https://secure.gravatar.com/avatar/"
GRAVATAR_URL_DEFAULT = 404

NEW_RELIC_TRACKING = False

# Modules considered when calculating profile completion
PROFILE_COMPLETION_MODULES = (
    'name',
    'summary',
    'address',
    'telephone',
    'employmenthistory',
    'education',
)

BOTS = ['agent', 'archive', 'ask', 'auto', 'bot', 'check', 'crawl',
        'facebookexternalhit', 'flipdog', 'grub', 'harvest', 'heritrix',
        'index', 'indy+library', 'infoseek', 'jakarta', 'java', 'job',
        'keynote', 'larbin', 'libwww', 'mechani', 'nutch', 'panscient', 'perl',
        'proximic', 'python', 'scan', 'scooter', 'scoutjet', 'search', 'slurp',
        'spider', 'url+control', 'urllib', 'validator', 'watchfire',
        'whizbang', 'wget', 'xenu', 'yahoo-fetch', 'yahooseeker']

# A list of proected sites and the groups (by id) that are allowed
# to access them. Copied from directseo.
PROTECTED_SITES = {42751: [25803, ]}


# Default site settings
SITE_ID = 1
SITE_NAME = ""
SITE_BUIDS = []
SITE_PACKAGES =[]
DEFAULT_FACET = ""

DEFAULT_PAGE_SIZE = 40
DEFAULT_SORT_DIRECTION = '-num_jobs'
SLUG_TAG_PARSING_REGEX = re.compile('([/\w\(\)-]+?)/(jobs|jobs-in|new-jobs|'
                                    'vet-jobs|careers)/', re.U)
# Max number of filters bots can apply.
ROBOT_FILTER_LEVEL = 2

#This is the canonical order that filter paths will be redirected to
SLUG_TAGS = OrderedDict([
    ('title_slug', '/jobs-in/'),
    ('location_slug', '/jobs/'),
    ('moc_slug', '/vet-jobs/'),
    ('facet_slug', '/new-jobs/'),
    ('company_slug', '/careers/'),
])

ALLOW_MULTIPLE_SLUG_TAGS = {
    'title': False,
    'location': False,
    'moc': False,
    'facet': True,
    'company': False,
    'featured': False,
}

FEED_VIEW_SOURCES = {
    'xml': 23,
    'json': 24,
    'rss': 25,
    'atom': 26,
    'indeed': 27,
    'sitemap': 28,
}

# Solr/Haystack
HAYSTACK_LIMIT_TO_REGISTERED_MODELS = False
FACET_RULE_DELIMITER = '#@#'
TEST_SOLR_INSTANCE = {
    'all': 'http://127.0.0.1:8983/solr/myjobs_test/',
    'current': 'http://127.0.0.1:8983/solr/myjobs_test_current/'
}


# Caching
MINUTES_TO_CACHE = 120
CACHE_MIDDLEWARE_KEY_PREFIX = 'this'
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True


# South
#SOUTH_TESTS_MIGRATE = False
#SKIP_SOUTH_TESTS = True
#SOUTH_MIGRATION_MODULES = {
#    'taggit': 'taggit.south_migrations',
#}


# Default haystack settings. Should be overwritten by settings.py.
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'seo.search_backend.DESolrEngine',
        'URL': 'http://127.0.0.1:8983/solr/seo',
        'HTTP_AUTH_USERNAME': SOLR_AUTH['username'],
        'HTTP_AUTH_PASSWORD': SOLR_AUTH['password'],
    },
    'groups': {
        'ENGINE': 'saved_search.groupsearch.SolrGrpEngine',
        'URL': 'http://127.0.0.1:8983/solr/seo',
        'HTTP_AUTH_USERNAME': SOLR_AUTH['username'],
        'HTTP_AUTH_PASSWORD': SOLR_AUTH['password'],
    },
}

# Password settings
PASSWORD_MIN_LENGTH = 8
PASSWORD_COMPLEXITY = {
    'UPPER': 1,
    'LOWER': 1,
    'DIGITS': 1,
    'PUNCTUATION': 1
}

# email types
ACTIVATION = 1
CREATE_CONTACT_RECORD = 3
FORGOTTEN_PASSWORD = 4
GENERIC = 5
INACTIVITY = 6
INVITATION = 7
INVOICE = 8
PARTNER_SAVED_SEARCH_RECIPIENT_OPTED_OUT = 10
POSTING_REQUEST_CREATED = 11
SAVED_SEARCH = 12
SAVED_SEARCH_DIGEST = 13
SAVED_SEARCH_DISABLED = 14
SAVED_SEARCH_INITIAL = 15
SAVED_SEARCH_UPDATED = 16

EMAIL_FORMATS = {
    ACTIVATION: {
        'address': u'accounts@{domain}',
        'subject': u'Account Activation for {domain}'
    },
    CREATE_CONTACT_RECORD : {
        'address': PRM_EMAIL,
        'subject': u'Partner Relationship Manager Contact Records'
    },
    FORGOTTEN_PASSWORD: {
        'address': u'accounts@{domain}',
        # Subject is handled by the templates used in Django's default
        # password reset.
        'subject': u'Password Reset on {domain}',
    },
    GENERIC: {

    },
    INACTIVITY: {
        'address': u'accounts@{domain}',
        'subject': u'Account Inactive',
    },
    INVITATION: {
        'address': u'accounts@{domain}',
        'subject': u'{company_name} invitation from {inviter}',
    },
    INVOICE: {
        'address': u'invoice@{domain}',
        'subject': u'{company_name} Invoice',
    },
    PARTNER_SAVED_SEARCH_RECIPIENT_OPTED_OUT: {
        'address': u'{company_name} Saved Search <savedsearch@{domain}>',
        'subject': u'My.jobs Partner Saved Search Update',
    },
    POSTING_REQUEST_CREATED: {
        'address': u'request@{domain}',
        'subject': u'New request for {company_name}',
    },
    SAVED_SEARCH: {
        'address': u'{company_name} Saved Search <savedsearch@{domain}>',
        'subject': u'{label}',
    },
    SAVED_SEARCH_DIGEST: {
        'address': u'{company_name} Saved Search <savedsearch@{domain}>',
        'subject': u'Your Saved Search Digest',

    },
    SAVED_SEARCH_DISABLED: {
        'address': u'{company_name} Saved Search <savedsearch@{domain}',
        'subject': u'Invalid URL in Your {company_name} Saved Search',
    },
    SAVED_SEARCH_INITIAL: {
        'address': u'{company_name} Saved Search <savedsearch@{domain}>',
        'subject': u'{company_name} New Saved Search - {label}',
    },
    SAVED_SEARCH_UPDATED: {
        'address': u'{company_name} Saved Search <savedsearch@{domain}>',
        'subject': u'{company_name} Saved Search Updated - {label}',
    },
}

MEMOIZE = True

DATABASE_ROUTERS = ['redirect.routers.ArchiveRouter']

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

COMPRESS_ROOT = join(ROOT_PATH, 'static')

COMPRESS_OUTPUT_DIR = 'CACHE'

COMPRESS_CSS_HASHING_METHOD = 'hash'

COMPRESS_OFFLINE = True

COMPRESS_ENABLED = False
