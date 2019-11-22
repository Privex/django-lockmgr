"""
The ``clear_lock`` management command allows you to **delete one or more locks**, which may be useful for
troubleshooting if you have stagnant locks.

You may encounter stagnant locks if you're using locking functions such as :py:func:`.get_lock`, instead of using the
context manager :class:`.LockMgr` (or in rare events where your application exits unexpectedly, without time
to cleanup locks).


Below is an excerpt from the manage.py help ``./manage.py clear_lock --help``::
    
    Releases one or more specified locks set using Privex's django-lockmgr package
    
    positional arguments:
      locks                 One or more lockmgr lock names (as positional args) to release the locks for

**Example usage**

.. code-block:: bash
    
    # Create the two locks 'hello' and 'world'
    ./manage.py set_lock hello world

        Finished creating / renewing 2 locks.


    # Delete the locks 'hello', 'world' and 'test' (it doesn't matter if some of the passed locks don't exist)
    ./manage.py clear_lock hello world test
    
        Releasing lock hello from LockMgr...
        Lock hello has been removed (if it exists).
        
        Releasing lock world from LockMgr...
        Lock world has been removed (if it exists).
        
        Releasing lock test from LockMgr...
        Lock test has been removed (if it exists).


"""
from django.core.management import BaseCommand, CommandParser
from lockmgr import lockmgr


class Command(BaseCommand):
    help = "Releases one or more specified locks set using Privex's django-lockmgr package"
    
    def __init__(self):
        super(Command, self).__init__()
    
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            'locks', type=str, nargs='+',
            help='One or more lockmgr lock names (as positional args) to release the locks for'
        )
    
    def handle(self, *args, **options):
        lockmgr.clean_locks()  # Clean up any locks due for expiration.
        locks: list = options['locks']
        
        if len(locks) == 0:
            print('No lock names specified.')
            return
        
        for l in locks:
            print()
            print(f"Releasing lock {l} from LockMgr...")
            lockmgr.unlock(l)
            print(f"Lock {l} has been removed (if it exists).")
        print("\n=========================================================\n")
        print("Finished clearing locks.")
        print("\n=========================================================\n")


