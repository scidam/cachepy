import datetime
from .base import BaseBackend, BaseLimitedBackend, PY3
from ..conf import settings

if PY3:
    from collections import UserDict
else:
    from UserDict import UserDict


class MemBackend(UserDict, BaseBackend):
    """Store cached data in memory.
    """

    def store_data(self, data_key, data, key='', ttl=0, noc=0, ncalls=0):
        if ttl:
            expired = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else:
            expired = None
        super(MemBackend, self).store_data(data_key, data, key=key,
                                           expired=expired, noc=noc,
                                           ncalls=ncalls)


class LimitedMemBackend(BaseLimitedBackend, MemBackend):
    """Memory cache backend with limited capacity.

    See details in `BaseLimitedBackend`.
    """
