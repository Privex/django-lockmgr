.. _Install:

Installing Django Lock Manager
==============================

Download and install from PyPi using pipenv / pip (recommended)
---------------------------------------------------------------


**Installing with** `Pipenv`_ **(recommended)**

.. code-block:: bash

    pipenv install django-lockmgr


**Installing with standard** ``pip3``

.. code-block:: bash

    pip3 install django-lockmgr


.. _Pipenv: https://pipenv.kennethreitz.org/en/latest/




(Alternative) Manual install from Git
--------------------------------------

You may wish to use the alternative installation methods if:

* You need a feature / fix from the Git repo which hasn't yet released as a versioned PyPi package
* You need to install django-lockmgr on a system which has no network connection
* You don't trust / can't access PyPi
* For some reason you can't use ``pip`` or ``pipenv``


**Option 1 - Use pip to install straight from Github**

.. code-block:: bash

    pip3 install git+https://github.com/Privex/django-lockmgr


**Option 2 - Clone and install manually**

.. code-block:: bash

    # Clone the repository from Github
    git clone https://github.com/Privex/django-lockmgr
    cd django-lockmgr

    # RECOMMENDED MANUAL INSTALL METHOD
    # Use pip to install the source code
    pip3 install .

    # ALTERNATIVE MANUAL INSTALL METHOD
    # If you don't have pip, or have issues with installing using it, then you can use setuptools instead.
    python3 setup.py install


Post-installation
-----------------

**Django Lock Manager** requires very little configuration after installation. Simply add it to your
``INSTALLED_APPS``, and run ``./manage.py migrate lockmgr`` to create the database tables.


Add ``lockmgr`` to your ``INSTALLED_APPS``

.. code-block:: python

    INSTALLED_APPS = [
        'django.contrib.admin.apps.SimpleAdminConfig',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        # ...
        'lockmgr'
    ]


Run the migrations

.. code-block:: bash

    ./manage.py migrate lockmgr

