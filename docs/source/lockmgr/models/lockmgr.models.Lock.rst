Lock
====

.. currentmodule:: lockmgr.models

.. autoclass:: Lock


   .. automethod:: __init__
      :noindex:


Methods
^^^^^^^

.. rubric:: Methods

.. autosummary::
   :toctree: lock

    ~Lock.get_next_by_created_at
    ~Lock.get_next_by_updated_at
    ~Lock.get_previous_by_created_at
    ~Lock.get_previous_by_updated_at





Attributes
^^^^^^^^^^

.. rubric:: Attributes

.. autosummary::
   :toctree: lock

    ~Lock.created_at
    ~Lock.expired
    ~Lock.expires_in
    ~Lock.expires_seconds
    ~Lock.lock_process
    ~Lock.locked_by
    ~Lock.locked_until
    ~Lock.name
    ~Lock.objects
    ~Lock.updated_at

