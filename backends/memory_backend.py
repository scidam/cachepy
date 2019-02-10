from .base import BaseBackend

class MemBackend(dict, BaseBackend):
    """Used to store cached data in memory.
    """

    def store_data(self, chash, data, key='', ttl=0, noc=0, ncalls=0):
        if ttl:
            _expired = datetime.datetime.now()\
                       + datetime.timedelta(seconds=ttl)
        else:
            _expired = datetime.datetime.now()
        super(MemBackend, self).store_data(chash, data, key=key,
                                           expired=_expired, noc=noc,
                                           ncalls=ncalls)

    def get_data(self, chash, key='', ttl=0, noc=0):
        return super(MemBackend, self).get_data(chash,
                                                key=key, ttl=ttl, noc=noc)
