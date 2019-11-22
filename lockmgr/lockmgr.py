"""
This is the main module file for `Django Lock Manager`_ (django-lockmgr) and contains lock management functions/classes.

.. _Django Lock Manager: https://github.com/Privex/django-lockmgr

There are **two ways** you can use Django Lock Manager:

 * The first (and recommended) way, is to use the context manager class :class:`.LockMgr`.
 * The second (lower level) way, is to use the lock functions directly, such as :func:`.get_lock`, :func:`.unlock`,
   and :func:`.set_lock`.

Using the context manager LockMgr (recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`.LockMgr` is a wrapper class for the various locking functions in this module, e.g. :py:func:`.get_lock`, and
is designed to be used as a **context manager**, i.e. using a ``with`` statement.

It's strongly recommended to use django-lockmgr via the :class:`.LockMgr` context manager unless you have a specific
need for manual lock management, as it greatly reduces the risk of "stuck locks" due to human error, or
incorrect exception handling.

By using django-lockmgr via this context manager, it ensures you don't forget to release any locks after
you've finished with the resources you were using.

Not only that, but it also ensures in the event of an exception, or an unexpected crash of your application,
that your locks will usually be safely released by :py:meth:`.LockMgr.__exit__`.

    >>> from lockmgr.lockmgr import LockMgr
    >>> try:
    ...     with LockMgr('mylock', 60) as l:
    ...         print('Doing stuff with mylock locked.')
    ...         # Obtain an additional lock for 'otherlock' - will use the same expiry as mylock
    ...         # Since ``ret`` is set to True, it will return a bool instead of raising Lock
    ...         if l.lock('otherlock', ret=True):
    ...             print('Now otherlock is locked...')
    ...             l.unlock('otherlock')
    ...         else:
    ...             print('Not doing stuff because otherlock is already locked...')
    ...         # If you're getting close to your lock's expiry (timeout), you can call '.renew()' to add an extra
    ...         # 2 minutes to your expiry time. Or manually specify the expiry with 'expires=120'
    ...         sleep(50)
    ...         l.renew(expires=30) # Add an extra 30 seconds to the expiration of 'mylock'
    ... except Locked as e:
    ...     print('Failed to lock. Reason: ', type(e), str(e))

Using the raw module lock management functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases, it might not be suitable to use context management due to a complex application flow, such as
the use of threading / multiprocessing, sharing the locks across other applications, etc.

If you need to, you can access the lower level lock management functions by importing this module, or the
individual functions.

Here's some examples:

First, let's get a lock using :func:`.get_lock` that expires in 10 seconds, and wait a few seconds.

    >>> from lockmgr import lockmgr
    >>> lk = lockmgr.get_lock('my_app:somelock', expires=10)
    >>> sleep(5)

Since our lock is going to expire soon, we'll use :func:`.renew_lock` to reset the expiration time to 20 seconds
from now.
 
    >>> lk = lockmgr.renew_lock(lk, 20)   # Change the expiry time to 20 seconds from now
    >>> sleep(15)

Using :func:`.is_locked`, we can confirm that the lock ``my_app:somelock` is still locked::

    >>> lockmgr.is_locked('my_app:somelock') # 15 seconds later, the lock is still locked
    True

Finally, we use :func:`.unlock` to release the lock. You can pass either a string lock name such as
``my_app:somelock``, or you can also pass a :class:`.Lock` database object i.e. the result from :func:`.get_lock`.
Use whichever parameter type you prefer, it doesn't make a difference.

    >>> lockmgr.unlock(lk)


Extra documentation
^^^^^^^^^^^^^^^^^^^

This is not the end of the documentation, this is only the beginning! :)

You'll find detailed documentation on the pages for each function / class / method. Most things are documented
using **PyDoc**, which means you can view usage information straight from most Python IDEs (e.g. PyCharm and VS Code),
as well as via the ``help()`` function inside of the Python REPL.

**Browsable HTML API docs**

We have `online documentation`_ for this module, which shows the usage information for each individual function and
class method in this module.

.. _online documentation: https://django-lockmgr.readthedocs.io/lockmgr/lockmgr.lockmgr.html#api-docs-lockmgr-lockmgr

**Python REPL help**

Using the ``help()`` function, you can view help on modules, classes, functions and more straight from the REPL::

    $ ./manage.py shell
    Python 3.8.0 (v3.8.0:fa919fdf25, Oct 14 2019, 10:23:27)
    [Clang 6.0 (clang-600.0.57)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> from lockmgr import lockmgr
    >>> help(lockmgr.get_lock)

Below is a screenshot showing the REPL help page for :func:`.get_lock`

.. image:: https://cdn.privex.io/github/django-lockmgr/repl_help.png
   :target: https://cdn.privex.io/github/django-lockmgr/repl_help.png
   :width: 800px
   :alt: Screenshot of REPL help
   :align: center


"""
import logging
import socket
from datetime import timedelta
from time import sleep
from typing import Union, List, Optional, Dict, Tuple

from django.db import transaction
from django.utils import timezone
from privex.helpers import empty, PrivexException, is_true

from lockmgr.models import Lock

log = logging.getLogger(__name__)


class Locked(PrivexException):
    """Raised when a lock already exists with the given name"""
    pass


class LockNotFound(PrivexException):
    """Raised when a requested lock doesn't exist"""
    pass


class LockMgr:
    """
    LockMgr is a wrapper class for the various locking functions in this module, e.g. :py:func:`.get_lock`, and
    is designed to be used as a **context manager**, i.e. using a ``with`` statement.
    
    By using django-lockmgr via this context manager, it ensures you don't forget to release any locks after
    you've finished with the resources you were using.
    
    Not only that, but it also ensures in the event of an exception, or an unexpected crash of your application,
    that your locks will usually be safely released by :py:meth:`.__exit__`.
    
    **Usage:**

        Using a ``with`` statement, create a LockMgr for ``mylock`` with automatic expiration if held for more than
        60 seconds. After the ``with`` statement is completed, all locks created will be removed.

        >>> try:
        ...     with LockMgr('mylock', 60) as l:
        ...         print('Doing stuff with mylock locked.')
        ...         # Obtain an additional lock for 'otherlock' - will use the same expiry as mylock
        ...         # Since ``ret`` is set to True, it will return a bool instead of raising Lock
        ...         if l.lock('otherlock', ret=True):
        ...             print('Now otherlock is locked...')
        ...             l.unlock('otherlock')
        ...         else:
        ...             print('Not doing stuff because otherlock is already locked...')
        ... except Locked as e:
        ...     print('Failed to lock. Reason: ', type(e), str(e))
        
        You can also use :meth:`.renew` to request more time / re-create the lock if you're close to, or have already
        exceeded the lock expiration time (defaults to 10 mins).
        
        >>> try:
        ...     with LockMgr('mylock', 60) as l:
        ...         print('Doing stuff with mylock locked.')
        ...         sleep(50)
        ...         l.renew(expires=30)    # Add an additional 30 seconds of time to the lock expiration
        ...         sleep(50)              # It's now been 100 seconds. 'mylock' should be expired.
        ...         # We can still renew an expired lock when using LockMgr. It will simply re-create the lock.
        ...         l.renew()              # Add an additional 120 seconds (default) of time to the lock expiration
        ... except Locked as e:
        ...     print('Failed to lock. Reason: ', type(e), str(e))
    
    """

    name: str
    """The lock name (from the constructor)"""
    main_lock: Optional[Lock]
    """The :class:`.Lock` object created at the start of a ``with LockManager('xyz')`` statement"""
    _locks: List[Lock]
    """A list of locks created with this LockMgr instance, including the :py:attr:`.main_lock`"""
    locked_by: str
    """Who/what created this lock - usually the hostname unless manually specified"""
    lock_process: Optional[int]
    """Usually None, but sometimes may represent the process ID this lock belongs to"""
    wait: Optional[int]
    """How long to wait for a lock before giving up. If this is ``None`` then waiting will be disabled"""
    expires: int
    """The user supplied expiration time in seconds"""

    def __init__(self, name, expires: Optional[int] = 600, locked_by=None, lock_process=None, wait: int = None):
        """
        Create an instance of :class:`.LockMgr`. This class is primarily intended to be used as
        a context manager (i.e. ``with LockMgr('mylock') as l:``), see the main PyDoc block for :class:`.LockMgr`
        for more info.
        
        :param str name:            The lock name to create (when using as a context manager)
        :param int expires:         How many seconds before this lock is considered stale and forcefully released?
        :param str locked_by:       (Optional) Who/what is using this lock. Defaults to system hostname.
        :param int lock_process:    (Optional) The process ID of the app using this lock
        :param int wait:            (Optional) Wait this many seconds for a lock to be released before giving up. If
                                    this is ``None`` then waiting will be disabled
        
        """
        self.expires = int(expires) if expires not in [None, False] else 0
        self.wait = None if empty(wait) else int(wait)
        self.locked_by = socket.gethostname() if empty(locked_by) else locked_by
        self.name, self.lock_process = name, lock_process
        self._locks = []  # type: List[Lock]
        self.main_lock = None

    def lock(self, name, expires: int = None, ret: bool = False, wait: int = None):
        """
        Obtains a lock using :py:func:`.get_lock` and appends it to :py:attr:`._locks` if successful.

        If the argument ``ret`` is ``False`` (default), it will raise :class:`.Locked` if the lock couldn't be obtained.

        Otherwise, if ``ret`` is ``True``, it will simply return ``False`` if the requested lock name is already locked.

        :param str name: A unique name to identify your lock
        :param int expires: (Default: 600 sec) How long before this lock is considered stale and forcefully released?
        :param bool ret: (Default: False) Return ``False`` if locked, instead of raising ``Locked``.
        :param int wait: (Optional) Retry obtaining the lock for this many seconds. MUST be divisible by 5.
                         If not empty, will retry obtaining the lock every 5 seconds until ``wait`` seconds

        :raises Locked: If the requested lock ``name`` is already locked elsewhere, :class:`.Locked` will be raised

        :return bool success: ``True`` if successful. If ``ret`` is true then will also return False on failure.
        """
        expires = self.expires if empty(expires) else int(expires)
        wait = self.wait if empty(wait) else int(wait)
        log.debug('Attempting to get lock %s with expiry of %s', name, expires)
        try:
            lck = get_lock(name=name, locked_by=self.locked_by, lock_process=self.lock_process, expires=expires)
            if len(self._locks) == 0 or self.main_lock is None:
                self.main_lock = lck
            self._locks.append(lck)
            log.debug('Lock obtained for %s', name)
            return True
        except Locked as e:
            if empty(wait, zero=True):
                log.info('A lock already exists on %s...', name)
                if ret: return False
                raise e

            wait = int(wait)
            if wait % 5 != 0:
                raise ArithmeticError('The argument "wait" must be divisible by 5 seconds.')
            log.info('Lock "%s" was locked - waiting up to %s seconds for lock to be released.', name, wait)
            log.info('Retrying lock in 5 seconds...')
            sleep(5)
            return self.lock(name=name, expires=expires, ret=ret, wait=wait - 5)

    def unlock(self, lock: Union[Lock, str] = None):
        """Alias for :py:func:`.unlock`"""
        lock = self.main_lock if lock is None else lock
        return unlock(lock)

    def renew(self, lock: Union[str, Lock] = None, expires: int = 120, add_time: bool = True, **kwargs) -> Lock:
        """
        Add ``expires`` seconds to the lock expiry time of ``lock``. If ``lock`` isn't specified, will default to
        the class instance's original lock :py:attr:`.main_lock`
        
        Alias for :py:func:`.renew_lock` - but with ``add_time`` and ``create`` set to ``True`` by default,
        instead of ``False``.
        
        With no arguments specified, this method will renew the main lock of the class :py:attr:`.main_lock`
        for an additional 2 minutes (or if the lock is already expired, will re-create it with 2 min expiry).
        
        **Example usage**::
        
            >>> with LockMgr('mylock', expires=30) as l:
            ...     sleep(10)
            ...     l.renew(expires=60)                  # Add 60 seconds more time to 'mylock' expiration
            ...     l.main_lock.refresh_from_db()
            ...     print(l.main_lock.expires_seconds)   # Output: 79
            ...     l.renew('lockx', expires=60)         # Add 60 seconds more time to 'lockx' expiration
        
        :param str lock:       Name of the lock to renew
        :param Lock lock:      A :class:`.Lock` object to renew
        :param int expires:    (Default: 120) If not add_time, then this is the new expiration time in seconds from now.
                               If add_time, then this many seconds will be added to the expiration time of the lock.
        :param bool add_time:  (Default: ``True``) If True, then ``expires`` seconds will be added to the existing
                               lock expiration time, instead of setting the expiration time to ``now + expires``
        .. rubric:: Extra Keyword Arguments
        
        :key bool create:      (Default: ``True``) If True, then create a new lock if it doesn't exist / already expired
        :key str locked_by:    (Default: system hostname) What server/app is trying to obtain this lock?
        :key int lock_process: (Optional) The process ID requesting the lock
        
        .. rubric:: Exceptions

        :raises LockNotFound: Raised if the requested ``lock`` doesn't exist / is already expired and ``create`` is False.
        
        :return Lock lock: The :class:`.Lock` object which was renewed
        """
        create = is_true(kwargs.pop('create', True))
        lock = self.main_lock if lock is None else lock
        return renew_lock(lock=lock, expires=expires, add_time=add_time, create=create, **kwargs)

    def __enter__(self):
        """
        When :class:`.LockMgr` is used as a context manager, i.e. ``with LockManager('xyz') as l:`` - this method
        is called to setup the context manager and return the object used for the ``with`` statement.
        
        This function simply creates the lock specified by the user to :meth:`.__init__` - then when the context
        manager is finished, or an exception occurs, :meth:`.__exit__` is called.
        """
        self.lock(self.name, self.expires)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        When the context manager is finished or an exception occurs, we unlock all locks that were created
        during the context manager session.
        """
        log.debug('LockMgr exiting. Releasing all held locks')
        for lock in self._locks:
            self.unlock(lock)


def is_locked(name: Union[Lock, str]) -> bool:
    """Cleans expired locks, then returns ``True`` if the given lock key ``name`` exists, otherwise ``False``"""
    clean_locks()
    if type(name) is not str:
        name = name.name
    with transaction.atomic():
        lck = Lock.objects.select_for_update().filter(name=name)
    return lck.count() > 0


def clean_locks():
    """Deletes expired :class:`.Lock` objects."""
    with transaction.atomic():
        expired_locks = Lock.objects.select_for_update().filter(
            locked_until__lt=timezone.now(), locked_until__isnull=False
        )
        if expired_locks.count() > 0:
            log.info('Deleting expired locks: %s', expired_locks.values_list('name', flat=True))
            expired_locks.delete()


def get_lock(name, expires: Optional[int] = 600, locked_by: str = None, lock_process: int = None) -> Lock:
    """
    READ THIS: It's best to use :class:`.LockMgr` as it automatically handles locking and unlocking using ``with``.

    Calls :py:func:`.clean_locks` to remove any expired locks, checks for any existing locks using a FOR UPDATE
    transaction, then attempts to obtain a lock using the Lock model :class:`payments.models.Lock`

    If ``name`` is already locked, then :class:`.Locked` will be raised.

    Otherwise, if it was successfully locked, a :class:`payments.models.Lock` object for the requested lock name
    will be returned.

    Usage:

        >>> try:   # Obtain a lock on 'mylock', with an automatic expiry of 60 seconds.
        ...     mylock = get_lock('mylock', 60)
        ...     print('Successfully locked mylock')
        ... except Locked as e:
        ...     print('Failed to lock. Reason: ', type(e), str(e))
        ... finally:  # Regardless of whether there was an exception or not, remember to remove the lock!
        ...     print('Removing lock on "mylock"')
        ...     unlock(mylock)

    :param str name: A unique name to identify your lock
    :param int expires: (Default: 600 sec) How long before this lock is considered stale and forcefully released?
                        Set this to ``0`` for a lock which will never expire (must manually call :func:`.unlock`)
    :param str locked_by: (Default: system hostname) What server/app is trying to obtain this lock?
    :param int lock_process: (Optional) The process ID requesting the lock

    :raises Locked: If the requested lock ``name`` is already locked elsewhere, :class:`.Locked` will be raised

    :return Lock lock: If successfully locked, will return the :class:`payments.models.Lock` of the requested lock.

    """
    clean_locks()  # First let's remove any old expired locks
    locked_by = socket.gethostname() if empty(locked_by) else locked_by
    expires = 0 if expires in [None, False] else int(expires)
    locked = Lock.objects.filter(name=name)
    if locked.count() > 0:
        raise Locked(f'Lock with name {name} already exists.')
    
    with transaction.atomic():
        locked = Lock.objects.select_for_update().filter(name=name)
        if locked.count() > 0:
            raise Locked(f'Lock with name {name} already exists.')
        expires_at = timezone.now() + timedelta(seconds=expires) if expires > 0 else None
        lock = Lock.objects.create(name=name, locked_by=locked_by, lock_process=lock_process, locked_until=expires_at)
        lock.save()
        return lock
    raise Locked(f'Unexpected transaction.atomic exit via get_lock()')


def renew_lock(lock: Union[str, Lock], expires: int = 600, add_time: bool = False, **kwargs) -> Lock:
    """
    Renew an existing lock for more expiry time.
    
    **Note:** This function will NOT reduce a lock's expiry time, only lengthen. If ``add_time`` is ``False``,
    and the new expiration time ``expires`` is shorter than the lock's existing expiration time, then the lock's
    expiry time will be left untouched.
    
    **Example - Renew an existing lock**::
    
        >>> lk = get_lock('my_app:somelock', expires=10)
        >>> sleep(5)
        >>> lk = renew_lock(lk, 20)   # Change the expiry time to 20 seconds from now
        >>> sleep(15)
        >>> is_locked('my_app:somelock') # 15 seconds later, the lock is still locked
        True
    
    **Example - Try to renew, but get a new lock if it's already been released**::
    
        >>> lk = get_lock('my_app:somelock', expires=5)
        >>> sleep(10)
        >>> lk = renew_lock(lk, 20, create=True)   # If the lock is expired/non-existant, make a new lock
        >>> sleep(15)
        >>> is_locked('my_app:somelock') # 15 seconds later, the lock is still locked
        True

    :param str lock:       Name of the lock to renew
    :param Lock lock:      A :class:`.Lock` object to renew
    :param int expires:    (Default: 600) If not add_time, then this is the new expiration time in seconds from now.
                           If add_time, then this many seconds will be added to the expiration time of the lock.
    :param bool add_time:  (Default: ``False``) If True, then ``expires`` seconds will be added to the existing
                           lock expiration time, instead of setting the expiration time to ``now + expires``
    
    :key bool create:      (Default: ``False``) If True, then create a new lock if it doesn't exist / already expired.
    :key str locked_by:    (Default: system hostname) What server/app is trying to obtain this lock?
    :key int lock_process: (Optional) The process ID requesting the lock

    :raises LockNotFound: Raised if the requested ``lock`` doesn't exist / is already expired and ``create`` is False.
    
    :return Lock lock: The :class:`.Lock` object which was renewed
    """
    create, lk = is_true(kwargs.get('create', False)), lock
    expires = 0 if expires in [None, False] else int(expires)
    clean_locks()
    with transaction.atomic():
        if type(lock) is str:
            try:
                lk = Lock.objects.select_for_update().get(name=lock)
            except Lock.DoesNotExist:
                # If we can't find an existing lock under the given name, then depending on `create`, we
                # either raise a reception, or simply make a new lock.
                if not create:
                    raise LockNotFound(f'Lock with name {lock} does not exist, cannot renew (set create=True).')
                return get_lock(
                    lock, expires=expires, locked_by=kwargs.get('locked_by'), lock_process=kwargs.get('lock_process')
                )
        # Preserve the lock name in-case the lock is expired, so we don't lose it when we refresh from DB.
        lock_name = str(lk.name)
        try:
            lk.refresh_from_db()
        except Lock.DoesNotExist:
            if not create:
                raise LockNotFound(f'Lock with name {lock} does not exist, cannot renew (set create=True).')
            return get_lock(
                lock_name, expires=expires, locked_by=kwargs.get('locked_by'), lock_process=kwargs.get('lock_process')
            )
            
        if lk.expired:  # If the passed `Lock` object is already expired, update locked_until to now before extending.
            lk.locked_until = timezone.now()
        # If expires is 0 or lower, then we set locked_until to None (never expires)
        if expires <= 0:
            lk.locked_until = None
            lk.save()
            return lk
        # If add_time, add `expires` seconds to the existing expiry, otherwise replace it with `now + expires`
        ex = lk.locked_until + timedelta(seconds=expires) if add_time else timezone.now() + timedelta(seconds=expires)
        # We only want to update the lock expiry time if the new expiry time is actually longer than it's existing
        # expiration time. This ensures we don't have a renewal where it causes a 10 minute lock to be reduced to
        # 1 minute unknowingly.
        if ex > lk.locked_until:
            lk.locked_until = ex
        lk.save()
    return lk


def unlock(lock: Union[Lock, str]):
    """
    Releases a given lock - either specified as a string name, or as a :class:`payments.models.Lock` object.

    Usage:

        >>> mylock = get_lock('mylock', expires=60)
        >>> unlock('mylock') # Delete the lock by name
        >>> unlock(mylock)   # Or by Lock object.

    :param str lock: The name of the lock to release
    :param Lock lock: A :class:`.Lock` object to release
    """
    log.debug('Releasing lock for %s', lock)
    if type(lock) is str:
        Lock.objects.filter(name=lock).delete()
        return True
    lock.delete()
    return True


class LockFail(Locked):
    """Raised when locks were requested, with failure/rollback if any already existed."""
    
    def __init__(self, *args, lock: Lock = None):
        super().__init__(*args)
        self.lock = lock


class LockSetStatus(dict):
    was_locked: bool
    locked: bool
    status: str
    
    def __init__(self, **kwargs):
        """
        
        :key bool was_locked: Was this name key locked when first checked
        :key bool locked: Is this name now locked after checking it?
        :key str status: One of: ``skip``, ``create``, ``extend``
        """
        super().__init__(**kwargs)
        self.was_locked = kwargs.get('was_locked')
        self.locked = kwargs.get('locked')
        self.status = kwargs.get('status')

    def __getitem__(self, key):
        """When the instance is accessed like a dict, try returning the matching attribute."""
        if hasattr(self, key):
            return getattr(self, key)
        return super().__getitem__(key)
        # raise KeyError(key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
        super().__setitem__(key, value)


class LockSetResult(dict):
    locks: List[Lock]
    counts: Dict[str, int]
    statuses: List[Tuple[str, LockSetStatus]]
    
    def __init__(self, **kwargs):
        """

        :key list locks: List of :class:`.Lock` objects
        :key dict counts: Dict containing counts of created, renewed, skip_create, skip_renew
        :key list statuses: List of tuples containing lock name and :class:`.LockSetStatus`
        """
        super().__init__(**kwargs)
        self.locks = kwargs.get('locks', [])
        self.counts = kwargs.get('counts', {})
        self.statuses = kwargs.get('statuses', [])

    def __getitem__(self, key):
        """When the instance is accessed like a dict, try returning the matching attribute."""
        if hasattr(self, key):
            return getattr(self, key)
        return super().__getitem__(key)
        # raise KeyError(key)

    def __setitem__(self, key, value):
        setattr(self, key, value)
        super().__setitem__(key, value)


def set_lock(*locks, timeout=600, fail=False, renew=True, create=True, **options) -> LockSetResult:
    """
    This function is for advanced users, offering multiple lock creation, renewing, along with "all or nothing"
    locking with database rollback via the argument ``fail``.
    
    Unlike other lock management functions, set_lock returns a :class:`.LockSetResult` object, which is designed
    to allow you to see clearly as to what locks were created, renewed, or skipped.
    
    **Example Usage**
    
    Let's set two locks, ``hello`` and ``world``.
    
        >>> res = set_lock('hello', 'world')
        >>> res['locks']
        [<Lock name='hello' locked_by='example.org' locked_until='2019-11-22 02:01:55.439390+00:00'>,
         <Lock name='world' locked_by='example.org' locked_until='2019-11-22 02:01:55.442734+00:00'>]
        >>> res['counts']
        {'created': 2, 'renewed': 0, 'skip_create': 0, 'skip_renew': 0}
    
    If we run ``set_lock`` again with the same arguments, we'll still get the locks list, but we'll see the counts
    show that they were renewed instead of created.
    
        >>> x = set_lock('hello', 'world')
        >>> x['locks']
        [<Lock name='hello' locked_by='example.org' locked_until='2019-11-22 02:03:06.762620+00:00'>,
         <Lock name='world' locked_by='example.org' locked_until='2019-11-22 02:03:06.766804+00:00'>]
        >>> x['counts']
        {'created': 0, 'renewed': 2, 'skip_create': 0, 'skip_renew': 0}
    
    Since the result is an object, you can also access attributes via dot notation, as well as dict-like notation.
    
    We can see inside of the ``statuses`` list - the action that was taken on each lock we specified, so we can see
    what locks were created, renewed, or skipped etc.
    
        >>> x.statuses[0]
        ('hello', {'was_locked': True, 'status': 'extend', 'locked': True})
        >>> x.statuses[1]
        ('world', {'was_locked': True, 'status': 'extend', 'locked': True})
    
    
    :param str locks:    One or more lock names, as positional arguments, to create or renew.
    :param int timeout:  On existing locks, update locked_until to ``now + timeout`` (seconds)
    :param bool fail:    (Default: False) If ``True``, all lock creations will be rolled back if an existing lock
                         is encountered, and :class:`.LockFail` will be raised.
    :param bool renew:   (Default: True) If ``True``, any existing locks in ``locks`` will be renewed to
                         ``now + timeout`` (seconds). If False, existing locks will just be skipped.
    :param bool create:  (Default: True) If ``True``, any names in ``locks`` which aren't yet locked, will have a lock
                         created for them, with their expiry set to ``timeout`` seconds from now.
    :key str locked_by:    (Default: system hostname) What server/app is trying to obtain this lock?
    :key int process_id: (Optional) The process ID requesting the lock
    :return LockSetResult results: A :class:`.LockSetResult` object containing the results of the set_lock operation.
    """
    fail = is_true(fail)

    timeout = int(timeout)
    process_id = options.get('process_id')
    process_id: int = int(process_id) if process_id is not None else None
    locked_by: str = options.get('locked_by')
    lock_args = dict(expires=timeout, locked_by=locked_by, lock_process=process_id)

    result = LockSetResult(
        locks=[],
        counts=dict(created=0, renewed=0, skip_create=0, skip_renew=0),
        statuses=[]
    )

    
    try:
        with transaction.atomic():
            sid = transaction.savepoint()
            for l in locks:
                try:
                    if not create and not is_locked(l):
                        log.debug(f" > The lock '{l}' doesn't exist, but create=False was specified. Not locking.")
                        result['statuses'] += [(l, LockSetStatus(was_locked=False, status='skip', locked=False))]
                        # result['locks'] += [lck]
                        result.counts['skip_create'] += 1
                        continue
                    lck = get_lock(l, **lock_args)
                    log.info(
                        f" > Lock {l} did not yet exist. Successfully locked '{l}' - expiry: {lck.locked_until}")
                    result.statuses += [(l, LockSetStatus(was_locked=False, status='create', locked=True))]
                    result.locks += [lck]
                    result.counts['created'] += 1
                except Locked:
                    lck = Lock.objects.get(name=l)
                    if fail:
                        transaction.savepoint_rollback(sid)
                        raise LockFail(f"Lock '{l}' already existed. Aborting!", lock=lck)
                    if not renew:
                        result['statuses'] += [(l, LockSetStatus(was_locked=True, status='skip', locked=True))]
                        result['locks'] += [lck]
                        log.debug(f" > The lock '{l}' already exists, but renew=False - not renewing this lock.")
                        log.debug(f"\tLock: %s\t", lck)
                        log.debug(" > Skipping this lock...\n")
                        result.counts['skip_renew'] += 1
                        continue
                    lck = renew_lock(lck, **lock_args)
                    result['locks'] += [lck]
                    result['statuses'] += [(l, LockSetStatus(was_locked=True, status='extend', locked=True))]
                    result.counts['renewed'] += 1
                    log.info(f" > The lock '{l}' already exists. Renewed it's expiry to: {lck.locked_until}")
    except LockFail as e:
        log.error(
            "Error: An existing lock was found while fail=True"
            "\n !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            " !!! An existing lock was found:\n"
            f" !!! \t{e.lock}\n"
            " !!! As you have specified fail=True, any locks created during this session will now be\n"
            " !!! rolled back for your safety.\n"
            " !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        )
        transaction.rollback()
        log.error("Any locks created during this session should now have been removed...")
        raise e
    return result
