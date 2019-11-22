"""
This file contains code shared between tests, such as :class:`.LockMgrTestBase` which is the base class shared
by all unit tests.

**Copyright**::

    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Django Database Lock Manager               |
    |        License: X11/MIT                           |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+

"""
import logging
import os
from django.test import TestCase

from privex.loghelper import LogHelper
from os import getenv as env

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lockmgr.settings")
from lockmgr.lockmgr import LockMgr, Locked, Lock, get_lock, unlock, is_locked, renew_lock, LockNotFound

LOG_LEVEL = env('LOG_LEVEL')
LOG_LEVEL = logging.getLevelName(str(LOG_LEVEL).upper()) if LOG_LEVEL is not None else logging.WARNING
LOG_FORMATTER = logging.Formatter('[%(asctime)s]: %(name)-55s -> %(funcName)-20s : %(levelname)-8s:: %(message)s')
_lh = LogHelper('lockmgr.tests', handler_level=LOG_LEVEL, formatter=LOG_FORMATTER)
_lh.add_console_handler()
log = _lh.get_logger()


class LockMgrTestBase(TestCase):
    """
    Base class for all django-lockmgr test classes. Includes :meth:`.tearDown` to delete all locks after each test.
    """
    def tearDown(self) -> None:
        """Ensure all locks are deleted after each test"""
        locks_removed = Lock.objects.all().delete()
        log.debug('tearDown -> Removed %d locks', locks_removed[0])


__all__ = [
    'LockMgrTestBase', 'get_lock', 'unlock', 'is_locked', 'renew_lock', 'Lock', 'LockMgr', 'Locked', 'LockNotFound',
    'LOG_LEVEL', 'LOG_FORMATTER'
]
"""
We manually specify __all__ so that we can safely use ``from tests.base import *`` within each test file.
"""

