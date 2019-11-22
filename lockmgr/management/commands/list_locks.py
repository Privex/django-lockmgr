"""

The ``list_locks`` management command allows you to **view all current locks**, which may be useful for troubleshooting,
e.g. checking whether or not a lock name really is locked, and what locked it


Below is an excerpt from the manage.py help ``./manage.py list_locks --help``::
    
    List all locks that were set using Privex's django-lockmgr package


There are no arguments nor switches available for this command.


**Example usage**

.. code-block:: bash

    # Create the two locks 'hello' and 'world'
    ./manage.py set_lock hello world

        Finished creating / renewing 2 locks.
    
    
    ./manage.py list_locks

        There are currently 2 active locks using Privex Django-LockMgr
        
        =========================================================
        
        <Lock name='hello' locked_by='example.org' lock_process='None' locked_until='2019-11-22 00:49:02.264729+00:00'>
        <Lock name='world' locked_by='example.org' lock_process='None' locked_until='2019-11-22 00:49:02.267728+00:00'>
        
        =========================================================



"""
from django.core.management import BaseCommand, CommandParser
from lockmgr import lockmgr
from lockmgr.models import Lock


class Command(BaseCommand):
    help = "List all locks that were set using Privex's django-lockmgr package"
    
    def __init__(self):
        super(Command, self).__init__()
    
    def handle(self, *args, **options):
        lockmgr.clean_locks()   # Clean up any locks due for expiration.
        lock_count = Lock.objects.count()
        print()
        print(f"There are currently {lock_count} active locks using Privex Django-LockMgr")
        
        print("\n=========================================================\n")
        for l in Lock.objects.all():
            print(
                f"<Lock name='{l.name}' locked_by='{l.locked_by}' lock_process='{l.lock_process}' "
                f"locked_until='{l.locked_until}'>"
            )
        print("\n=========================================================\n")


