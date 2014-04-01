from default_settings import *
import datetime
import os

DEBUG = True

DATABASES = {
    'default': {
        'NAME': 'dseo_mj',
        'ENGINE': 'django.db.backends.mysql',
        'USER': 'dseo_mj',
        'PASSWORD': PROD_DB_PASSWD,
        'HOST': 'db-dseomjstaging.c9shuxvtcmer.us-east-1.rds.amazonaws.com',
        'PORT': '3306',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

TEST_RUNNER = 'testrunner.SilentTestRunner'

SOLR = {
    'default': 'http://ec2-23-20-67-65.compute-1.amazonaws.com:8983/solr/myjobs_test/',
}

TEST_SOLR_INSTANCE = SOLR['default']

CELERY_ALWAYS_EAGER = True