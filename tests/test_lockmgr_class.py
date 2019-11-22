from datetime import timedelta
from django.utils import timezone
from tests.base import *


class TestLockMgrClass(LockMgrTestBase):
    """
    Tests which are related to the manager class :class:`lockmgr.lockmgr.LockMgr`

    Tests related to the module-level functions in :py:mod:`lockmgr.lockmgr` can be
    found in :py:mod:`tests.test_lockmgr`
    """
    def test_lockmgr(self):
        """Locking test_lockmgr and test_lockmgr2 using LockMgr, then verifying the lock was created"""
        with LockMgr('test_lockmgr') as lck:
            lck.lock('test_lockmgr2')
            # Attempt to lock test_lockmgr again, which should cause a Locked exception
            with self.assertRaises(Locked, msg="getting lock test_lockmgr should raise Locked"):
                lck.lock('test_lockmgr')
            self.assertTrue(is_locked('test_lockmgr2'), msg="is_locked('test_lockmgr2') == True")
        # Confirm that both test_lockmgr + test_lockmgr2 are unlocked after the with statement.
        self.assertFalse(is_locked('test_lockmgr'), msg="is_locked('test_lockmgr') == False")
        self.assertFalse(is_locked('test_lockmgr2'), msg="is_locked('test_lockmgr2') == False")
    
    def test_lockmgr_except(self):
        """Testing that LockMgr correctly removes Locks after an exception"""
        try:
            # Lock test_except, verify it's locked, then throw an AttributeError
            with LockMgr('test_except') as lck:
                self.assertTrue(is_locked('test_except'), msg="is_locked('test_except') == True")
                raise AttributeError('Fake AttributeError')
        except AttributeError:
            # Verify that test_except is now cleanly unlocked
            self.assertFalse(is_locked('test_except'), msg="is_locked('test_except') == False")
    
    def test_lock_wait(self):
        """Test that LockMgr runs code with 'wait for lock expiry' when lock expires within wait period"""
        get_lock('test_wait', expires=4)
        start_lock = timezone.now()
        with LockMgr('test_wait', wait=5):
            end_lock = timezone.now()
            self.assertGreaterEqual(end_lock, start_lock + timedelta(seconds=4),
                                    msg="Assert lock released after at least 4 seconds")
            self.assertLess(end_lock, start_lock + timedelta(seconds=15), msg="Assert lock released in <15 seconds")
    
    def test_lock_wait_timeout(self):
        """Test that LockMgr raises Locked with 'wait for lock expiry' when lock still locked after waiting period"""
        get_lock('test_wait', expires=15)
        start_lock = timezone.now()
        # LockMgr should raise `Locked` because `test_wait` should still be valid for another 10 seconds.
        with self.assertRaises(Locked):
            with LockMgr('test_wait', wait=5):
                pass
        end_lock = timezone.now()
        self.assertGreaterEqual(end_lock, start_lock + timedelta(seconds=5),
                                msg="Lock wait timed out after at least 5 secs")
        self.assertLess(end_lock, start_lock + timedelta(seconds=15), msg="Lock wait timed out in <15 seconds")

