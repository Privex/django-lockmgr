Privex's Django Database Lock Manager
======================================

```
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

Django Database Lock Manager - Easy to use lock system using your Django app's database
Copyright (c) 2019    Privex Inc. ( https://www.privex.io )
```

# Install with pip

We recommend at least Python 3.6 - we cannot guarantee compatibility with older versions.

```
pip3 install django-lockmgr
```

Add `lockmgr` to your `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # ...
    'lockmgr'
]   
```

Run the migrations

```bash
./manage.py migrate lockmgr
```

# Usage

Use the `LockMgr` in your code like so:

```python
from lockmgr.lockmgr import LockMgr, Locked

try:
    with LockMgr('mylock') as lck:
        print('The lock "mylock" is now locked.')
        lck.lock('otherlock')
        print('The lock "otherlock" should also be locked.')
    print('The locks "mylock" and "otherlock" should now both be cleared.')
except Locked as e:
    print('Error! mylock is already locked: ', type(e), str(e))

```

If you want to wait for the lock to be released, rather than immediately excepting:

```python
from lockmgr.lockmgr import LockMgr, Locked

try:
    # expires=60 means the lock will expire after 60 seconds if you don't renew it.
    # wait=90 (must be in 5 second intervals) means: if the key is locked, retry every 5 seconds, if 90 seconds have 
    #         passed and it's still locked, then give up and raise Locked.
    with LockMgr('somelock', expires=60, wait=90) as lck:
        print('The lock "somelock" is now locked.')
    print('The lock "somelock" should now be cleared.')
except Locked as e:
    print('Error! After retrying for 90 seconds, "somelock" is still locked: ', type(e), str(e))

```

Unit Tests
===========

To run the unit tests, clone the project and make a `.env` file containing details for a database:

```
DB_BACKEND=mysql
DB_NAME=lockmgr
DB_USER=someuser
DB_PASS=mypassword
```

Install all required dependencies:

```
pip3 install -r requirements.txt -U
```

Now run the tests (-v2 for verbosity level 2):

```
./manage.py test -v2
```

