"""Caching results of functions in Python.

Features
--------

    * Memory-based and file-based caches;
    * Assigning ttl (time-to-live) and noc (the number of calls) for the caches;
    * Encryption of cached data (symmetric encryption (RSA) algorithm is used);
    * lfu (least frequently used) and mfu (most frequently used) cache clearing strategies;
    * caches of limited size;

Note
----

    - Encryption functionality requires `PyCryptodome` package to be installed
    - File-based caches don't clear the data being stored on the program closing;
      Such data should be cleaned up manually, if needed.

Examples
--------

.. code-block:: python

    from cachepy import *

    mycache = Cache()  # cache to memory without encryption

    @mycache
    def my_heavy_function(x):
        '''Performs heavy computations'''

        print('Hi, I am called...')
        return x**2

    my_heavy_function(2)
    # "Hi, I am called..." will be printed to stdout only once
    # return 4
    
    my_heavy_function(2)
    # return 4


To store data to a file, you need to create a decorator as follows:

.. code-block:: python

    # create cache-to-file decorator
    filecache = Cache('mycache')  # mycache.dat will be created; 
    # `.dat` extension is appended automatically to the filename
    # (depends on shelve module implementation);

Its behaviour is the same as memory-based one.

One can set up time-to-live (ttl) and/or maximum number of retrievals (noc) 
for cached data when the decorator is created:

.. code-block:: python

    import time
    from cachepy import *

    cache_with_ttl = Cache(ttl=2)  # ttl given in seconds

    @cache_with_ttl
    def my_heavy_function(x):
        '''Performs heavy computations'''
        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    # return 9
    my_heavy_function(3) # 'Hi, I am called ...' will not be printed
    # return 9
    time.sleep(2)
    my_heavy_function(3) # 'Hi, I am called ...' will be printed again


.. code-block:: python

    cache_with_noc = Cache(noc=2)  # the number-of-calls: noc = 2

    @cache_with_noc
    def my_heavy_function(x):
        '''Performs heavy computations'''

        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    my_heavy_function(3) # 'Hi, I am called ...' will not be printed
    my_heavy_function(3) # 'Hi, I am called ...' will be printed again


It is easy to use both `noc` and `ttl` arguments on a cache decorator:

.. code-block:: python

    cache_with_noc_ttl = Cache(noc=2, ttl=1)

    @cache_with_noc_ttl
    def my_heavy_function(x):
        '''Performs heavy computations'''
        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    my_heavy_function(3)  # 'Hi, I am called ...' will not be printed
    my_heavy_function(3)  # 'Hi, I am called ...' will be printed (noc is
    # reached, recompute the func value)
    time.sleep(2)  # get ttl to be expired
    my_heavy_function(3) # 'Hi, I am called ...' will be printed again

One can encrypt cached data by providing non-empty `key` argument as
a password (RSA encryption algorithm is used):

.. code-block:: python

    cache_to_file_ttl_noc = FileCache('mycache',
                                      noc=2, ttl = 2, key='mypassword')

    @cache_to_file_ttl_noc
    def my_heavy_function(x):
        '''Performs heavy computations'''
        print('Hi, I am called...')
        return x**2

    my_heavy_function(2) # 'Hi, I am called...' will be printed
    my_heavy_function(2) # 'Hi, I am called...' will not be printed

When one calls `my_heavy_function` being decorated by  `cache_to_file_ttl_noc`,
the value `4` will be computed and the result of
computation will be stored in the file named `mycache.dat`. Along
with the result of computation,  additional information will be stored
in that file `mycache.dat` 
(all the data will be encrypted by the RSA encryption algorithm
using password `mypassword`): 1) result's expiration time
(computed from ttl), noc and the number
of already performed calls for the function being decorated (`my_heavy_function`).

Encryption is available only if `PyCryptodome` package is installed and
`key` parameter (non-empty string representing password) is passed to the
cache constructor.

If you passed non-empty `key` parameter to the cache constructor,
but `PyCryptodome` was not found, special warning would raised in this case
("PyCryptodome not installed. Data isn't encrypted") and
the cache would worked as usual, but without encryption functionality.


Testing
-------

.. code-block:: bash

         python -m  cachepy.test


TODO
----

    * Writing backend for redis server


Log list
--------

    * Version 1.0
    * Version 0.1
        - initial release


.. codeauthor:: Dmitry Kislov <kislov@easydan.com>

"""

import threading
from .backends import (FileBackend, MemBackend, LimitedFileBackend,
                       LimitedMemBackend)
from .utils import get_function_hash, PY3
from functools import wraps


# -------------------- Module meta info --------------------
__author__ = "Dmitry E. Kislov"
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Dmitry E. Kislov"
__email__ = "kislov@easydan.com"
# ----------------------------------------------------------

__all__ = ('Cache', 'memcache', 'FileCache', 'LimitedFileCache',
           'LimitedCache')

BASE_LOCK = threading.Lock()


class BaseCache(object):
    """Base class for cache decorator.
    """

    def __init__(self, key='', ttl=0, noc=0, backend=None):
        self.backend = backend
        self.ttl = ttl
        self.key = key
        self.noc = noc
        self.is_used = False

    def __call__(self, func):
        if self.is_used:
            raise RuntimeError("This cache decorator is already used. "
                               "Create another one.")

        self.cached_keys = list()

        @wraps(func)
        def wrapper(*args, **kwargs):
            data_key = get_function_hash(func, args, kwargs,
                                         self.ttl, self.key, self.noc)

            if data_key not in self.cached_keys:
                self.cached_keys.append(data_key)

            with BASE_LOCK:
                result, flag = self.backend.get_data(data_key,
                                                     key=self.key)
            if not flag:
                result = func(*args, **kwargs)
                with BASE_LOCK:
                    self.backend.store_data(data_key, result,
                                            key=self.key, ttl=self.ttl,
                                            noc=self.noc, ncalls=0)
            return result

        def clear():
            """Clear cache for specified funcion"""
            with BASE_LOCK:
                for data_key in self.cached_keys:
                    self.backend.remove(data_key)

        wrapper.clear = clear
        self.is_used = True
        return wrapper

# -------------------------- Block of documentation ------------------

_class_description = """{}

    Parameters
    ==========

{}
        :param ttl: cache time to live in seconds;
        :param key: encryption key; empty by default; if provided,
                    the cached data will be encrypted.
        :param noc: number of the function calls;
                    if it is reached, the cache is cleared.
"""

_class_titles = {
    'Cache': 'Cache results of function execution in memory.', 
    'FileCache': 'Caches results of function execution in a file.',
    'LimitedCache': """Caches the result of a function execution in memory.
    Uses cache of limited capacity.""",
    'LimitedFileCache': """Caches the result of a function execution in a file.
    Uses cache of limited capacity."""}


_class_extra_parameters = {'Cache': '', 
'FileCache': """\
        :param filename: name of the file, where
                        the cached data will be stored;""",
'LimitedCache': """\
        :param cache_size: cache capacity; an integer number; if it is exeeded,
                        cached data is removed according to the algorithm
                        (either 'lfu' or 'mfu');
        :param algorithm: strategy of removing cached data; either `lfu`
                          (least frequently used) or `mfu` (most frequently used)
                          cached value is removed when cache is exhausted.
""",
'LimitedFileCache': """\
        :param filename: name of the file, where
                        the cached data will be stored;
        :param cache_size: cache capacity; an integer number; if it is exeeded,
                        cached data is removed according to the algorithm
                        (either 'lfu' or 'mfu');
        :param algorithm:  strategy of removing cached data; either `lfu`
                        (least frequently used) or `mfu` (most frequently used)
                        cached value is removed when cache is exhausted.
"""
}                                       
# --------------------------------------------------------------------

class Cache(BaseCache):
    __doc__ = _class_description.format(
        _class_titles['Cache'], 
        _class_extra_parameters['Cache'])

    def __init__(self, key='', ttl=0, noc=0):
        super(Cache, self).__init__(key=key, ttl=ttl, noc=noc,
                                    backend=MemBackend())


class FileCache(BaseCache):
    __doc__ = _class_description.format(
        _class_titles['FileCache'], 
        _class_extra_parameters['FileCache'])

    def __init__(self, filename, key='', ttl=0, noc=0):
        super(FileCache, self).__init__(key=key, ttl=ttl, noc=noc)
        self.backend = FileBackend(filename)


class LimitedCache(BaseCache):
    __doc__ = _class_description.format(
        _class_titles['LimitedCache'], 
        _class_extra_parameters['LimitedCache'])

    def __init__(self, key='', ttl=0, noc=0, **kwargs):
        super(LimitedCache, self).__init__(key=key, ttl=ttl, noc=noc)
        self.backend = LimitedMemBackend(**kwargs)


class LimitedFileCache(BaseCache):
    __doc__ = _class_description.format(
        _class_titles['LimitedFileCache'], 
        _class_extra_parameters['LimitedFileCache'])

    def __init__(self, filename, key='', ttl=0, noc=0, **kwargs):
        super(LimitedFileCache, self).__init__(key=key, ttl=ttl, noc=noc)
        self.backend = LimitedFileBackend(filename, **kwargs)

    


# ----------------- Shortcuts  --------------------------
memcache = Cache()
memcache.__doc__ = """
Shortcut for `memcache = Cache()`.

Simple cache decorator without encryption.
"""

# -------------------------------------------------------