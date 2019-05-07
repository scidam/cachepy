import os
import shelve
from .base import BaseLimitedBackend, BaseBackend
import warnings
import datetime

try:
    basestring
except NameError:
    basestring = str


class FileBackend(BaseBackend):
    """File-based cache backend.
    """

    def __init__(self, filename, *args, **kwargs):
        _fn = kwargs.pop('filename', None)
        self.filename = filename or _fn
        if not isinstance(self.filename, basestring):
            raise TypeError("Filename should be a string. ")
        if os.path.exists(self.filename):
            warnings.warn("This file already exists. Its content will be overwritten.")
        self.db = shelve.open(self.filename, flag='c', writeback=True)
        super(FileBackend, self).__init__(*args, **kwargs)

    def keys(self):
        return tuple(self.db.keys())

    def remove(self, item):
        if item in self.db:
            del self.db[item]

    def get(self, key, default=None):
        return self.db.get(key, default)

    def __setitem__(self, key, value):
        self.db[key] = value

    def __getitem__(self, key):
        return self.get(key)

    def store_data(self, data_key, data, key='', ttl=0, noc=0, ncalls=0):
        if ttl:
            expired = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else:
            expired = None
        super(FileBackend, self).store_data(data_key, data, key=key,
                                            expired=expired, noc=noc,
                                            ncalls=ncalls)
        self.db.sync()

    def __len__(self):
        return len(self.keys())

    def close(self):
        self.db.close()

    def __del__(self):
        try:
            self.db.close()
        except ValueError:
            pass


class LimitedFileBackend(FileBackend, BaseLimitedBackend):
    """File-based cache backend with limited capacity.

    See details in `BaseLimitedBackend`.
    """
