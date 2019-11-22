"""
This module contains test cases for Privex's Django Lock Manager (django-lockmgr).


Testing pre-requisites
----------------------

    - Install all core and development requirements listed in requirements.txt
    - Either PostgreSQL or MySQL is recommended, however the default SQLite3 may or may not work.
    - Python 3.7 or 3.8 is recommended at the time of writing this. See README.md in-case this has changed.


.. code-block:: bash

    pip3 install -r requirements.txt

If you're using MySQL / Postgres, create a ``.env`` file in the root of the project, and enter the database
connection details::

    # If not specified, DB_USER and DB_NAME both default to 'lockmgr'
    DB_USER=root
    DB_NAME=lockmgr
    # If not specified, then the DB user password defaults to blank
    DB_PASS=
    # If not specified, the DB host defaults to localhost, and the port as blank (automatic depending on backend)
    DB_HOST=localhost
    DB_PORT=5432
    # If not specified, the DB backend defaults to SQLite3 (stored in db.sqlite3 in root of project)
    # If you're using PostgreSQL:
    DB_BACKEND=postgresql
    # If you're using MySQL / MariaDB:
    DB_BACKEND=mysql


Running the tests via Django Test Runner / Django-Nose
------------------------------------------------------

After installing the packages listed in ``requirements.txt``, you should now be able to run the tests using
Django's manage.py::


    # Ensure you have all development requirements installed
    user@host: ~/django-lockmgr $ pip3 install -r requirements.txt
    
    # Then run the tests using manage.py
    user@host: ~/django-lockmgr $ ./manage.py test
    
    nosetests --verbosity=1
    Creating test database for alias 'default'...
    ............................
    ----------------------------------------------------------------------
    Ran 28 tests in 20.291s
    
    OK
    Destroying test database for alias 'default'...


For more verbosity, simply add ``--verbose`` to the end of the command::

    $ ./manage.py test --verbose
    
        nosetests --verbose --verbosity=2
        
        Creating test database for alias 'default' ('test_lockmgr')...
        Operations to perform:
          Synchronize unmigrated apps: django_nose
          Apply all migrations: lockmgr
        Synchronizing apps without migrations:
          Creating tables...
            Running deferred SQL...
        Running migrations:
          Applying lockmgr.0001_initial... OK
          
        Locking test_getlock then checking if Lock is raised when calling it again. ... ok
        Locking test_unlock, unlocking it, then lock/unlock again to confirm it was freed. ... ok
        Test that expired locks are correctly removed ... ok
        Test that LockMgr runs code with 'wait for lock expiry' when lock expires within wait period ... ok
        Test that LockMgr raises Locked with 'wait for lock expiry' when lock still locked after waiting period ... ok
        Locking test_lockmgr and test_lockmgr2 using LockMgr, then verifying the lock was created ... ok
        Testing that LockMgr correctly removes Locks after an exception ... ok
        Renew an existing lock by lock name and confirm locked_until was increased ... ok
        Renew an existing lock by lock name with add_time=True and confirm locked_until was increased ... ok
        Renew an existing lock by Lock object with add_time=True and confirm locked_until was increased ... ok
        Renew an existing lock by Lock object and confirm locked_until was increased ... ok
        Renew a non-existent lock by lock name and confirm LockNotFound is raised ... ok
        Renew a non-existent lock by lock name with create=True and confirm new lock is created ... ok
        
        ----------------------------------------------------------------------
        Ran 13 tests in 10.106s
        
        OK
        Destroying test database for alias 'default' ('test_lockmgr')...





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
from tests.base import *
from tests.test_lockmgr import *
from tests.test_lockmgr_class import *
from tests.test_renew import *
