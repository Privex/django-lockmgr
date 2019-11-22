from privex.loghelper import LogHelper
import os
from os import getenv as env
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = False
SECRET_KEY = 'NotApplicable'

LOG_FORMATTER = logging.Formatter('[%(asctime)s]: %(name)-55s -> %(funcName)-20s : %(levelname)-8s:: %(message)s')

LOG_LEVEL = logging.WARNING

_lh = LogHelper('lockmgr', formatter=LOG_FORMATTER, handler_level=LOG_LEVEL)

_lh.add_console_handler()

INSTALLED_APPS = ['django_nose', 'lockmgr']

DATABASES = {}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True

if env('DB_BACKEND', 'sqlite') in ['sqlite', 'sqlite3']:
    DATABASES = dict(default=dict(
        ENGINE='django.db.backends.sqlite3',
        NAME=os.path.join(BASE_DIR, env('DB_PATH', 'db.sqlite3'))
    ))
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.' + env('DB_BACKEND'),
            'NAME': env('DB_NAME', 'lockmgr'),
            'USER': env('DB_USER', 'lockmgr'),
            'PASSWORD': env('DB_PASS', ''),
            'HOST': env('DB_HOST', 'localhost'),
            'PORT': env('DB_PORT', ''),
        }
    }
