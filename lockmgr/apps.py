from django.apps import AppConfig
from lockmgr import VERSION

class LockMgrConfig(AppConfig):
    name = 'lockmgr'
    version = VERSION

