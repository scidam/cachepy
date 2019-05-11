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

    def __init__(self, key='', ttl=0, noc=0):
        self.key = key
        self.ttl = ttl
        self.noc = noc
        super(MemBackend, self).__init__()


class LimitedMemBackend(BaseLimitedBackend, MemBackend):
    """Memory cache backend with limited capacity.

    See details in `BaseLimitedBackend`.
    """
