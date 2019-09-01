from datetime import timedelta

from django.test import TestCase
import os

from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lockmgr.settings")

from lockmgr.lockmgr import LockMgr, Locked, Lock, get_lock, unlock, is_locked


class TestLockMgr(TestCase):
    def test_getlock_clean(self):
        """Locking test_getlock then checking if Lock is raised when calling it again."""
        l = get_lock('test_getlock')
        with self.assertRaises(Locked):
            get_lock('test_getlock')

    def test_getlock_unlock(self):
        """Locking test_unlock, unlocking it, then lock/unlock again to confirm it was freed."""
        get_lock('test_unlock')
        unlock('test_unlock')
        l = get_lock('test_unlock')
        unlock(l)

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

    def test_lock_expiry(self):
        """Test that expired locks are correctly removed"""
        lck = get_lock('test_expire', expires=600)
        self.assertTrue(is_locked('test_expire'), msg="is_locked('test_expire') == True")
        # Change the expiry time to 10 seconds before now, so the lock is expired
        lck.locked_until = timezone.now() - timedelta(seconds=10)
        lck.save()
        # Confirm the lock is no longer locked, as it has expired.
        self.assertFalse(is_locked('test_expire'), msg="is_locked('test_expire') == False")


if __name__ == "__main__":
    import dotenv
    import unittest
    from django.conf import settings

    dotenv.read_dotenv()
    settings.configure()
    unittest.main()


