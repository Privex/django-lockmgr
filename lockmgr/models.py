from django.db import models
from django.utils import timezone
from datetime import timedelta


def default_lock_expiry():
    return timezone.now() + timedelta(minutes=60)


class Lock(models.Model):
    name = models.CharField('Unique Lock Name', max_length=100, primary_key=True)
    """Unique name of the lock, referring to what specific resource(s) is locked"""

    locked_by = models.CharField(max_length=100, blank=True, null=True)
    """Name of the node / app which created this lock"""

    lock_process = models.IntegerField('Process ID of lock requester', default=0, blank=True, null=True)

    locked_until = models.DateTimeField(default=default_lock_expiry)
    """
    Locks have an expiration time, to help avoid the issue of stuck locks, either due to forgetting to add cleanup code, 
    or simply due to the app/server crashing before it can release the lock.

    After a lock has expired, it's assumed that the lock is stale and needs to be removed, and the affected resources 
    are safe to use.
    """

    created_at = models.DateTimeField('Locked At', auto_now_add=True)
    updated_at = models.DateTimeField('Last Update', auto_now=True)

    def __str__(self):
        return f"<Lock name='{self.name}' locked_by='{self.locked_by}' locked_until='{self.locked_until}'>"
