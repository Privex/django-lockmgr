"""
The ``reset_locks`` management command allows you to **delete ALL LOCKS** set by django-lockmgr in your
application's database, regardless of their expiration time, name, or who/what created them.

You may encounter stagnant locks if you're using locking functions such as :py:func:`.get_lock`, instead of using the
context manager :class:`.LockMgr` (or in rare events where your application exits unexpectedly, without time
to cleanup locks).


Below is an excerpt from the manage.py help ``./manage.py reset_locks --help``::

    Clears ALL locks that were set using Privex's django-lockmgr package
    
    optional arguments:
      -h, --help            show this help message and exit
      -f, --force           Do not show warning / ask if you are sure before deleting ALL locks


**Example usage**

First let's create two locks using :py:mod:`lockmgr.management.commands.set_lock`

.. code-block:: bash

    # Create the two locks 'hello' and 'world'
    ./manage.py set_lock hello world

        Finished creating / renewing 2 locks.


Now we'll run ``reset_locks`` without any arguments. You can see it requires confirmation, since it can be dangerous
to clear all locks if there are any applications running (or scheduled on a cron) that depend on the locks
to avoid conflicts.


.. code-block:: bash

    ./manage.py reset_locks
    
        WARNING: You are about to clear ALL locks set using Privex LockMgr.
        You should only do this if you know what you're doing, and have made sure to stop any running
        instances of your application, to ensure no conflicts are caused by removing ALL LOCKS.
        
        
        The following 2 locks would be removed:
        
        =========================================================
        
        <Lock name='hello' locked_by='example.org' locked_until='2019-11-22 00:49:02.264729+00:00'>
        <Lock name='world' locked_by='example.org' locked_until='2019-11-22 00:49:02.267728+00:00'>
        
        =========================================================
        
        Are you SURE you want to clear all locks?
        Type YES in all capitals if you are sure > YES
        
        =========================================================

        Please wait... Removing all locks regardless of their status or expiration.
        
        A total of 2 lock rows were deleted. All locks should now be removed.
        
        =========================================================
        
        Finished clearing locks.
        
        =========================================================

**Example 2 - Using the FORCE argument to skip the prompt**

Let's re-create those locks, and now run ``reset_locks`` with ``-f`` (force).


.. code-block:: bash

    # Create the two locks 'hello' and 'world'
    ./manage.py set_lock hello world

        Finished creating / renewing 2 locks.

    # Run 'reset_locks' with option '-f' (force / do not ask for confirmation)
    ./manage.py reset_locks -f
        
        The following 2 locks would be removed:
        
        =========================================================
        
        <Lock name='hello' locked_by='example.org' locked_until='2019-11-22 00:58:00.042322+00:00'>
        <Lock name='world' locked_by='example.org' locked_until='2019-11-22 00:58:00.045513+00:00'>
        
        =========================================================
        
        Option 'force' (-f / --force) was specified. Skipping confirmation prompt.
        Please wait... Removing all locks regardless of their status or expiration.
        
        A total of 2 lock rows were deleted. All locks should now be removed.
        
        =========================================================
        
        Finished clearing locks.
        
        =========================================================

"""

from django.core.management import BaseCommand, CommandParser
from lockmgr import lockmgr
from lockmgr.models import Lock


class Command(BaseCommand):
    help = "Clears ALL locks that were set using Privex's django-lockmgr package"
    
    def __init__(self):
        super(Command, self).__init__()
    
    def add_arguments(self, parser: CommandParser):
        parser.add_argument('-f', '--force', action='store_true', dest='force', default=False,
                            help='Do not show warning / ask if you are sure before deleting ALL locks')
    
    def handle(self, *args, **options):
        lockmgr.clean_locks()  # Clean up any locks due for expiration.
        lock_count = Lock.objects.count()
        if not options['force']:
            print("WARNING: You are about to clear ALL locks set using Privex LockMgr.\n"
                  "You should only do this if you know what you're doing, and have made sure to stop any running\n"
                  "instances of your application, to ensure no conflicts are caused by removing ALL LOCKS.\n\n")
        print(f"The following {lock_count} locks would be removed:")

        print("\n=========================================================\n")
        for l in Lock.objects.all():
            print(l)
        print("\n=========================================================\n")

        if options['force']:
            print("Option 'force' (-f / --force) was specified. Skipping confirmation prompt.")
        else:
            print('Are you SURE you want to clear all locks?')
            answer = input('Type YES in all capitals if you are sure > ').strip()
            print("\n\n=========================================================\n")
            if answer != 'YES':
                print("You didn't type YES so we're now returning you back to the terminal.")
                print("\n=========================================================\n")
                return
        print("Please wait... Removing all locks regardless of their status or expiration.\n")

        total_del, _ = Lock.objects.all().delete()

        print(f"A total of {total_del} lock rows were deleted. All locks should now be removed.\n")

        print("")
        print("\n=========================================================\n")
        print("Finished clearing locks.")
        print("\n=========================================================\n")


