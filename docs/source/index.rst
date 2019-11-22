.. _Privex Django Lock Manager documentation:



Privex Django Lock Manager (django-lockmgr) documentation
=================================================

.. image:: https://www.privex.io/static/assets/svg/brand_text_nofont.svg
   :target: https://www.privex.io/
   :width: 400px
   :height: 400px
   :alt: Privex Logo
   :align: center

Welcome to the documentation for Privex's `Django Lock Manager`_ - a small, open source Python 3 package
for Django, designed to provide simple, frustration free locks in your Django application, without requiring
any additional services like Redis / Memcached.

This documentation is automatically kept up to date by ReadTheDocs, as it is automatically re-built each time
a new commit is pushed to the `Github Project`_ 

.. _Django Lock Manager: https://github.com/Privex/django-lockmgr
.. _Github Project: https://github.com/Privex/python-helpers

.. contents::


Quick install
-------------

**Installing with** `Pipenv`_ **(recommended)**

.. code-block:: bash

    pipenv install django-lockmgr


**Installing with standard** ``pip3``

.. code-block:: bash

    pip3 install django-lockmgr


Add `lockmgr` to your `INSTALLED_APPS`

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


.. _Pipenv: https://pipenv.kennethreitz.org/en/latest/





All Documentation
=================

.. toctree::
   :maxdepth: 8
   :caption: Main:

   self
   install


.. toctree::
   :maxdepth: 3
   :caption: Code Documentation:

   lockmgr/index


.. toctree::
   :caption: Unit Testing

   lockmgr/tests


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
