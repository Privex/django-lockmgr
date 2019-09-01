import logging
import socket
from datetime import timedelta
from time import sleep
from typing import Union, List

from django.db import transaction
from django.utils import timezone
from privex.helpers import empty, PrivexException
from lockmgr.models import Lock

log = logging.getLogger(__name__)


class Locked(PrivexException):
    """Raised when a lock already exists with the given name"""
    pass


class LockMgr:
    """

    Usage:

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

    """

    def __init__(self, name, expires: int = 600, locked_by=None, lock_process=None, wait: int = None):
        self.expires = int(expires)
        self.wait = None if empty(wait) else int(wait)
        self.locked_by = socket.gethostname() if empty(locked_by) else locked_by
        self.name, self.lock_process = name, lock_process
        self._locks = []  # type: List[Lock]

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
        log.debug('Attempting to get lock %s with expiry of %s', name, expires)
        try:
            lck = get_lock(name=name, locked_by=self.locked_by, lock_process=self.lock_process, expires=expires)
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

    @staticmethod
    def unlock(lock: Union[Lock, str]):
        """Alias for :py:func:`.unlock`"""
        return unlock(lock)

    def __enter__(self):
        self.lock(self.name, self.expires)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug('LockMgr exiting. Releasing all held locks')
        for lock in self._locks:
            self.unlock(lock)
        return True


def is_locked(name) -> bool:
    """Cleans expired locks, then returns ``True`` if the given lock key ``name`` exists, otherwise ``False``"""
    clean_locks()
    with transaction.atomic():
        lck = Lock.objects.select_for_update().filter(name=name)
    return lck.count() > 0


def clean_locks():
    """Deletes expired :class:`payments.models.Lock` objects."""
    with transaction.atomic():
        expired_locks = Lock.objects.select_for_update().filter(locked_until__lt=timezone.now())
        if expired_locks.count() > 0:
            log.info('Deleting expired locks: %s', expired_locks.values_list('name', flat=True))
            expired_locks.delete()


def get_lock(name, expires: int = 600, locked_by: str = None, lock_process: int = None) -> Lock:
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
    :param str locked_by: (Default: system hostname) What server/app is trying to obtain this lock?
    :param int lock_process: (Optional) The process ID requesting the lock

    :raises Locked: If the requested lock ``name`` is already locked elsewhere, :class:`.Locked` will be raised

    :return Lock lock: If successfully locked, will return the :class:`payments.models.Lock` of the requested lock.

    """
    # First let's remove any old expired locks
    clean_locks()
    locked_by = socket.gethostname() if empty(locked_by) else locked_by
    is_locked = Lock.objects.filter(name=name)
    if is_locked.count() > 0:
        raise Locked(f'Lock with name {name} already exists.')
    with transaction.atomic():
        is_locked = Lock.objects.select_for_update().filter(name=name)
        if is_locked.count() > 0:
            raise Locked(f'Lock with name {name} already exists.')
        lock = Lock.objects.create(
            name=name, locked_by=locked_by, lock_process=lock_process,
            locked_until=timezone.now() + timedelta(seconds=int(expires))
        )
        lock.save()
        return lock
    raise Locked(f'Unexpected transaction.atomic exit via get_lock()')


def unlock(lock: Union[Lock, str]):
    """
    Releases a given lock - either specified as a string name, or as a :class:`payments.models.Lock` object.

    Usage:

        >>> mylock = get_lock('mylock', expires=60)
        >>> unlock('mylock') # Delete the lock by name
        >>> unlock(mylock)   # Or by Lock object.

    :param lock:
    :return:
    """
    log.debug('Releasing lock for %s', lock)
    if type(lock) is str:
        Lock.objects.filter(name=lock).delete()
        return True
    lock.delete()
    return True
