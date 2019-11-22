Django Management Commands
==========================

While Django Lock Manager is primarily designed to be used programmatically within your Django application
via the Python functions and methods - sometimes it can be useful to have administration commands to help
when troubleshooting or experimenting with the lock manager.

Once you've :ref:`installed django-lockmgr <Install>`, including adding the app to your ``INSTALLED_APPS`` and
ran the migrations, you'll be able to use the below commands via your Django application's ``./manage.py`` script.

See the below module links for documentation about each command.

.. automodule:: lockmgr.management.commands

.. autosummary::
    :toctree: commands

    lockmgr.management.commands.clear_lock
    lockmgr.management.commands.list_locks
    lockmgr.management.commands.reset_locks
    lockmgr.management.commands.set_lock

   
   
   
   
   

   
   
   

   
   
