from datetime import timedelta

from django.utils import timezone

from lockmgr.lockmgr import clean_locks
from tests.base import *


class TestLockMgrModule(LockMgrTestBase):
    """
    Tests which are related to the module-level functions in :py:mod:`lockmgr.lockmgr`
    
    Tests related to the manager class :class:`lockmgr.lockmgr.LockMgr` can be found
    in :py:mod:`tests.test_lockmgr_class`
    """
    
    def test_getlock_clean(self):
        """Locking test_getlock then checking if Locked is raised when calling it again."""
        get_lock('test_getlock')
        with self.assertRaises(Locked):
            get_lock('test_getlock')

    def test_is_locked(self):
        """Locking test_is_locked then testing is_locked returns True for existing locks and False for non-existent."""
        get_lock('test_is_locked')
        
        self.assertTrue(is_locked('test_is_locked'))
        self.assertFalse(is_locked('test_is_locked_nonexistent'))

    def test_getlock_unlock(self):
        """Locking test_unlock, unlocking it, then lock/unlock again to confirm it was freed."""
        get_lock('test_unlock')
        unlock('test_unlock')
        lck = get_lock('test_unlock')
        unlock(lck)

    def test_lock_expiry(self):
        """Test that expired locks are correctly removed"""
        lck = get_lock('test_expire', expires=600)
        self.assertTrue(is_locked('test_expire'), msg="is_locked('test_expire') == True")
        # Change the expiry time to 10 seconds before now, so the lock is expired
        lck.locked_until = timezone.now() - timedelta(seconds=10)
        lck.save()
        # Confirm the lock is no longer locked, as it has expired.
        self.assertFalse(is_locked('test_expire'), msg="is_locked('test_expire') == False")

    def test_lock_no_expiry(self):
        """Test that locks with ``None`` timeout aren't removed by clean_locks"""
        lck = get_lock('test_no_expire', expires=None)
        self.assertFalse(lck.expired)
        self.assertIsNone(lck.expires_seconds)
        self.assertIsNone(lck.expires_in)
        clean_locks()
        _lck = Lock.objects.get(name='test_no_expire')
        self.assertFalse(_lck.expired)

    def test_lock_zero_expiry(self):
        """Test that locks with ``0`` timeout aren't removed by clean_locks"""
        lck = get_lock('test_no_expire_zero', expires=0)
        self.assertFalse(lck.expired)
        self.assertIsNone(lck.expires_seconds)
        self.assertIsNone(lck.expires_in)
        clean_locks()
        _lck = Lock.objects.get(name='test_no_expire_zero')
        self.assertFalse(_lck.expired)
    

