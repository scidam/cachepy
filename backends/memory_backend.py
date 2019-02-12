import datetime
from .base import BaseBackend, PY3

if PY3:
    from collections import UserDict
else:
    from UserDict import UserDict


class MemBackend(UserDict, BaseBackend):
    """Used to store the cached data in memory.
    """

    def store_data(self, data_key, data, key='', ttl=0, noc=0, ncalls=0):
        if ttl:
            expired = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else:
            expired = None
        super(MemBackend, self).store_data(data_key, data, key=key, expired=expired,
                                           noc=noc, ncalls=ncalls)
