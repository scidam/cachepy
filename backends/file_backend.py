import shelve
from .memory_backend import MemBackend, LimitedMemBackend, BaseLimitedBackend


class FileBackend(shelve.Shelf, MemBackend):
    """File-based cache backend.
    """

    def __init__(self, filename):
        self.filename = filename
        try:
            import anydbm
        except ImportError:
            import dbm as anydbm
        shelve.Shelf.__init__(self, anydbm.open(self.filename, flag='c'))

    def store_data(self, data_key, data, key='', ttl=0, noc=0, ncalls=0):
        super(FileBackend, self).store_data(data_key, data, key=key, ttl=ttl,
                                            noc=noc, ncalls=ncalls)
        self.sync()


class LimitedFileBackend(LimitedMemBackend, FileBackend):
    """File-based cache backend with limited capacity.
    """ + BaseLimitedBackend.__init__.__doc__
