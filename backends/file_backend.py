import os
import shelve
from .memory_backend import MemBackend, LimitedMemBackend, BaseLimitedBackend
import warnings


class FileBackend(shelve.Shelf, MemBackend):
    """File-based cache backend.
    """

    def __init__(self, filename, **kwargs):
        _fn = kwargs.pop('filename', None)
        self.filename = filename or _fn
        try:
            import anydbm
        except ImportError:
            import dbm as anydbm
        if os.path.exists(self.filename):
            warnings.warn()  # FIXME: Warning message should be added !!!  # file will be overwritten! message should be raised!
        # shelve.Shelf
        super(FileBackend, self).__init__(anydbm.open(self.filename, flag='c'))

    def store_data(self, data_key, data, key='', ttl=0, noc=0, ncalls=0):
        super(FileBackend, self).store_data(data_key, data, key=key, ttl=ttl,
                                            noc=noc, ncalls=ncalls)
        self.sync()

    def __del__(self):
        try:
            self.close()
        except ValueError:
            pass


class LimitedFileBackend(LimitedMemBackend, FileBackend):
    """File-based cache backend with limited capacity.

    See details in `BaseLimitedBackend`.
    """
