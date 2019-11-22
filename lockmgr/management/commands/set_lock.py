"""
The ``set_lock`` management command allows you to **create / renew locks** using django-lockmgr from the command line.

If you don't specify any behaviour switches such as ``--no-renew`` or ``--fail``, then set_lock will create any
locks which aren't already locked, and renew any locks which are already locked.

Below is an excerpt from ``./manage.py set_lock --help`` (added at 21 Nov @ 9 PM UTC)::

  -h, --help            show this help message and exit
  -n, --no-renew        Do not renew any locks which already exist
  -r, --only-renew      Only renew existing locks, do not create new ones.
  -k, --no-timeout      Never expire these locks (--timeout will be ignored). They must be manually unlocked.
  -t TIMEOUT, --timeout TIMEOUT     Lock timeout in seconds (default 600)
  -e, --fail            Return an error (exit code 2) if one or more locks already exist. (will not create/renew ANY
  passed locks if one of the passed lock names exists)


The ``-e`` or ``--fail`` option can be a useful option when you're wanting to set multiple locks in unison, but
you need to be sure that all of the locks are set at the same time - and if any of the locks already exist, any
of the locks specified should not be created / be rolled back.

Below is an example of this special feature in use:

.. code-block:: bash
    
    user@host ~ $ ./manage.py set_lock example
     > Lock example did not yet exist. Successfully locked 'example' - expiry: 2019-11-21 15:30:03.857412


    user@host ~ $ ./manage.py set_lock -e hello world example

     > Lock hello did not yet exist. Successfully locked 'hello' - expiry: 2019-11-21 15:30:27.706378

     > Lock world did not yet exist. Successfully locked 'world' - expiry: 2019-11-21 15:30:27.709321
    
     !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
     !!! An existing lock was found:
     !!!     <Lock name='example' locked_by='Chriss-iMac-Pro.local' locked_until='2019-11-21 15:30:03.857412'>
     !!! As you have specified -e / --fail, any locks created during this session will now be
     !!! rolled back for your safety.
     !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
     !!! Any locks created during this session should now have been removed.
     !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    user@host ~ $ ./manage.py list_locks
    
    There are currently 1 active locks using Privex Django-LockMgr
    
    =========================================================
    
    <Lock name='example' locked_by='example.org' lock_process='None' locked_until='2019-11-21 15:30:03.857412'>
    
    =========================================================


"""
import sys

from django.core.management import BaseCommand, CommandParser
from privex.helpers import is_true
from privex.loghelper import LogHelper

from lockmgr import lockmgr
from lockmgr.lockmgr import LockFail, set_lock

import logging

log = logging.getLogger(__name__)

LOG_FORMATTER = logging.Formatter('[%(asctime)s]: %(name)-35s -> %(funcName)-10s : %(levelname)-8s:: %(message)s\n')


class Command(BaseCommand):
    help = "Add and/or renew locks using Privex's django-lockmgr package"
    
    def __init__(self):
        super(Command, self).__init__()
    
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            'locks', type=str, nargs='+',
            help='One or more lockmgr lock names (as positional args) to create/renew'
        )
        parser.add_argument('-n', '--no-renew', action='store_true', dest='no_renew', default=False,
                            help='Do not renew any locks which already exist')
        
        parser.add_argument('-r', '--only-renew', action='store_true', dest='only_renew', default=False,
                            help='Only renew existing locks, do not create new ones.')
        
        parser.add_argument(
            '-k', '--no-timeout', action='store_true', dest='no_timeout', default=False,
            help='Never expire these locks (--timeout will be ignored). They must be manually unlocked.'
        )
        parser.add_argument('-t', '--timeout', dest='timeout', default=600, type=int,
                            help='Lock timeout in seconds (default 600)')
        parser.add_argument('-e', '--fail', action='store_true', dest='fail', default=False,
                            help='Return an error (exit code 2) if one or more locks already exist. '
                                 '(will not create/renew ANY passed locks if one of the passed lock names exists)')
        
        parser.add_argument('--locked-by', dest='locked_by', default=None, type=str,
                            help='Set a custom "locked_by" string (defaults to system hostname)')
        parser.add_argument('--pid', '--process-id', dest='process_id', default=None, type=int,
                            help='Set a custom "lock_process" integer ID (defaults to None)')

    def handle(self, *args, **options):

        _lh = LogHelper(__name__, formatter=LOG_FORMATTER, handler_level=logging.INFO)
        _lh.add_console_handler()
        _lh.get_logger().propagate = False
        lockmgr.clean_locks()  # Clean up any locks due for expiration.
        
        fail = is_true(options['fail'])
        no_renew = is_true(options['no_renew'])
        only_renew = is_true(options['only_renew'])
        no_timeout = is_true(options['no_timeout'])
        
        locks: list = options['locks']
        process_id: int = int(options['process_id']) if options['process_id'] is not None else None
        locked_by: str = options['locked_by']
        timeout = None if no_timeout else int(options['timeout'])
        lock_args = dict(expires=timeout, locked_by=locked_by, lock_process=process_id)
        if len(locks) == 0:
            print('No lock names specified.')
            return
        
        _create = False if only_renew else True
        _renew = False if no_renew else True
        
        try:
            res = set_lock(
                *locks, timeout=timeout, locked_by=locked_by, process_id=process_id,
                fail=fail, create=_create, renew=_renew
            )
            print(f"Finished creating / renewing {len(locks)} locks.\n")

            print("\n====================Status Report=====================\n")
            print(f"  Per-lock:\n")
            print("\t\t{:<20}{:<20}{:<20}{:<20}\n".format("Name", "Was Locked?", "Now Locked?", "Status"))
            for lck_name, lres in res.statuses:
                print("\t\t{:<20}{:<20}{:<20}{:<20}".format(
                    lck_name,
                    'YES' if lres.was_locked else 'NO',
                    'YES' if lres.locked else 'NO',
                    lres.status
                ))
            print("\n========================================================\n")
            print("  Summary:\n")
            print(f"    Locks Created:      {res.counts['created']}")
            print(f"    Locks Renewed:      {res.counts['renewed']}")
            print(f"    Renewals Skipped:   {res.counts['skip_renew']}")
            print(f"    Creations Skipped:  {res.counts['skip_create']}")

        except LockFail as e:
            print("\n---------------------------------------------------------------------------\n")
            print(" [lockmgr.management.commands.set_lock] Caught exception LockFail while creating/setting locks...")
            print(" [lockmgr.management.commands.set_lock] The following existing lock was encountered:\n")
            print(f"\t{e.lock}\n")
            print(" >>> As you have set -e / --fail, this means that any lock creations or updates triggered during "
                  "this run of set_lock should have been rolled back.")
            print(" >>> If in doubt, run './manage.py list_locks' to view all current locks.\n")
            print(" !!! Now exiting with return code 2...\n")
            return sys.exit(2)
        
        print("")
        print("\n=========================================================\n")
        print("Finished creating / renewing locks.")
        print("\n=========================================================\n")
