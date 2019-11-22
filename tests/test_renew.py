from datetime import timedelta
from time import sleep

from django.utils import timezone

from tests.base import *


class TestLockRenew(LockMgrTestBase):
    
    def test_renew_existing_name(self):
        """Renew an existing lock by lock name and confirm locked_until was increased"""
        get_lock('test_renew', expires=20)
        renew_lock('test_renew', expires=60)
        l = Lock.objects.get(name='test_renew')
        self.assertGreaterEqual(l.locked_until - timezone.now(), timedelta(seconds=50))
    
    def test_renew_existing_name_add_time(self):
        """Renew an existing lock by lock name with add_time=True and confirm locked_until was increased"""
        get_lock('test_renew', expires=10)
        renew_lock('test_renew', expires=20, add_time=True)
        l = Lock.objects.get(name='test_renew')
        self.assertGreaterEqual(l.locked_until - timezone.now(), timedelta(seconds=25))
    
    def test_renew_non_existing_name(self):
        """Renew a non-existent lock by lock name and confirm LockNotFound is raised"""
        with self.assertRaises(LockNotFound):
            renew_lock('test_no_exist_lock_renew', expires=60)
    
    def test_renew_non_existing_name_create(self):
        """Renew a non-existent lock by lock name with create=True and confirm new lock is created"""
        renew_lock('test_renew_create', expires=60, create=True)
        l = Lock.objects.get(name='test_renew_create')
        self.assertGreaterEqual(l.locked_until - timezone.now(), timedelta(seconds=50))
    
    def test_renew_lock_object(self):
        """Renew an existing lock by Lock object and confirm locked_until was increased"""
        lck = get_lock('test_renew', expires=20)
        renew_lock(lck, expires=60)
        l = Lock.objects.get(name='test_renew')
        self.assertGreaterEqual(l.locked_until - timezone.now(), timedelta(seconds=50))
    
    def test_renew_existing_object_add_time(self):
        """Renew an existing lock by Lock object with add_time=True and confirm locked_until was increased"""
        lck = get_lock('test_renew', expires=10)
        renew_lock(lck, expires=20, add_time=True)
        l = Lock.objects.get(name='test_renew')
        self.assertGreaterEqual(l.locked_until - timezone.now(), timedelta(seconds=25))
    
    def test_renew_shorter_expiration(self):
        """Renew a lock with a shorter expiration time than it already has. Test the expiration time doesn't drop."""
        get_lock('test_renew_shorten', expires=120)
        renew_lock('test_renew_shorten', expires=30, add_time=False)
        lck = Lock.objects.get(name='test_renew_shorten')
        self.assertGreaterEqual(lck.locked_until - timezone.now(), timedelta(seconds=115))
        self.assertLessEqual(lck.locked_until - timezone.now(), timedelta(seconds=120))

    def test_renew_shorter_expiration_add_time(self):
        """Renew a lock with a shorter expiration seconds (but with add_time=True). Test expiration time increases."""
        get_lock('test_renew_shorten', expires=120)
        renew_lock('test_renew_shorten', expires=30, add_time=True)
        lck = Lock.objects.get(name='test_renew_shorten')
        self.assertGreaterEqual(lck.locked_until - timezone.now(), timedelta(seconds=140))
        self.assertLessEqual(lck.locked_until - timezone.now(), timedelta(seconds=150))

    def test_lockmgr_renew_main(self):
        """Renew the main lock within a LockMgr 'with' statement, confirm appropriate time was added to the lock"""
        
        with LockMgr('test_renew_lockmgr', expires=20) as lm:
            time_left = lm.main_lock.locked_until - timezone.now()
            self.assertGreaterEqual(time_left, timedelta(seconds=15))
            self.assertLessEqual(time_left, timedelta(seconds=20))
            lm.renew(expires=30)
            lck = Lock.objects.get(name='test_renew_lockmgr')
            time_left = lck.locked_until - timezone.now()
            self.assertGreaterEqual(time_left, timedelta(seconds=40))
            self.assertLessEqual(time_left, timedelta(seconds=50))

    def test_lockmgr_renew_expired(self):
        """Renew an expired main lock within a LockMgr 'with' statement, confirm time was added to the lock expiry"""
    
        with LockMgr('test_renew_lockmgr_ex', expires=3) as lm:
            time_left = lm.main_lock.locked_until - timezone.now()
            self.assertGreaterEqual(time_left, timedelta(seconds=0))
            self.assertLessEqual(time_left, timedelta(seconds=3))
            sleep(4)
            self.assertTrue(lm.main_lock.expired)
            # Unlike the normal renew_lock, LockMgr.renew should default to create=True, and re-create
            # the deleted/expired lock.
            lm.renew(expires=30)
            lck = Lock.objects.get(name='test_renew_lockmgr_ex')
            time_left = lck.locked_until - timezone.now()
            self.assertGreaterEqual(time_left, timedelta(seconds=25))
            self.assertLessEqual(time_left, timedelta(seconds=30))
