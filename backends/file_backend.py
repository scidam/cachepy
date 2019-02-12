import shelve
from .memory_backend import MemBackend


class FileBackend(shelve.Shelf, MemBackend):
    """Used to store the cached data in a file.
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
