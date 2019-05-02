import datetime
from .base import BaseBackend, PY3
from .conf import settings

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


class LimitedMemBackend(MemBackend):
    """Cache backend with limited capacity.

    Parameters
    ==========

        :param cache_size: size of cache; allowed number of keys.

    """

    def __init__(self, *args, **kwargs):
        try:
            self.cache_size = int(kwargs.pop('cache_size'))
            if self.cache_size < settings.MIN_CACHE_CAPACITY or\
               self.cache_size > settings.MAX_CACHE_CAPACITY:
                self.cache_size = settings.DEFAULT_CACHE_CAPACITY
        except (KeyError, ValueError):
            self.cache_size = settings.DEFAULT_CACHE_CAPACITY

        if PY3:
            super().__init__(self, *args, **kwargs)
        else:
            super(LimitedMemBackend, self).__init__(*args, **kwargs)

    def store_data(*args, **kwargs):
        if PY3:
            super().store_data(*args, **kwargs)
        else:
            super(LimitedMemBackend).store_data(*args, **kwargs)
        if len(self.keys) == self.cache_size - 1
        
    

