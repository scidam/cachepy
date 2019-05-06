'''
Caching results of functions in Python.

Features
--------

    * Storing cached data either on disk or in memory
    * Setting up time-to-live and the number of function calls for your cache
    * Encryption of cached data (symmetric encryption (RSA) algorithm is used)

Note
----

    - Encryption functionality requires `pycrypto` package to be installed
    - When using cache-to-file functionality you have to
      to clean up (if needed) created file(s) manually


Examples
--------

.. code-block:: python

    from cachepy import *

    mycache = Cache() # cache to memory without encryption

    @mycache
    def my_heavy_function(x):
        """Performs heavy computations"""
        print('Hi, I am called...')
        return x**2

    my_heavy_function(2)
    # "Hi, I am called..." will be printed to stdout only once
    my_heavy_function(2)


To store data to file, you need to create decorator as follows:

.. code-block:: python

    # create cache-to-file decorator
    filecache = Cache('mycache.dat')

Its behaviour is the same as a memory-based one.

One can set up time-to-live and/or maximum number of retrievals for cached data
when a decorator is created:

.. code-block:: python

    import time
    from cachepy import *
    # or from cachepy import Cache

    cache_with_ttl = Cache(ttl=2) # ttl given in seconds

    @cache_with_ttl
    def my_heavy_function(x):
        """Performs heavy computations"""
        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    my_heavy_function(3) # This will not print 'Hi, I am called ...'
    time.sleep(2)
    my_heavy_function(3) # 'Hi, I am called ...' will be printed again


.. code-block:: python

    cache_with_noc = Cache(noc=2) # Number-of-calls = 2

    @cache_with_noc
    def my_heavy_function(x):
        """Performs heavy computations"""
        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    my_heavy_function(3) # This will not print 'Hi, I am called ...'
    my_heavy_function(3) # 'Hi, I am called ...' will be printed again


It is easy to use both `noc` and `ttl` arguments on a cache decorator:

.. code-block:: python

    cache_with_noc_ttl = Cache(noc=2, ttl=1)

    @cache_with_noc_ttl
    def my_heavy_function(x):
        """Performs heavy computations"""
        print('Hi, I am called...')
        return x**2

    my_heavy_function(3)
    my_heavy_function(3) # This will not print 'Hi, I am called ...'
    my_heavy_function(3) # This will print 'Hi, I am called ...'
    time.sleep(2) # get ttl to be expired
    my_heavy_function(3) # This will print 'Hi, I am called ...'

One can encrypt cached data by providing non-empty `key` argument as
a password (RSA algo is used):

.. code-block:: python

    cache_to_file_ttl_noc = Cache('mycache.dat',
                                   noc=2, ttl = 2, key='mypassword')

    @cache_to_file_ttl_noc
    def my_heavy_function(x):
        """Performs heavy computations"""
        print('Hi, I am called...')
        return x**2

    my_heavy_function(2) # Will print 'Hi, I am called...'
    my_heavy_function(2) # Will not print 'Hi, I am called...'

Calling `my_heavy_function` function being decorated by `cache_to_file_ttl_noc`
will store `4` (result of computations)
in the file `mycache.dat`;
along with the result of computations,
additional info will be stored (these all will be encrypted by the RSA algo
with the password `mypassword`):
result expiration  time (computed from ttl), noc and the number
of performed calls of the decorated function (`my_heavy_function`).
Data will not be encrypted, if `pycrypto` package isn't installed.
If you pass non-empty `key` parameter to the  `Cache` constructor, the
warning will occurred ("Pycrypto not installed. Data isn't encrypted");
In this case, the cache will work without encryption functionality.


Testing
-------

The code tested (and works as expected) in **Python > 2.7.x** and **Python > 3.4.x**.

.. code-block:: bash

         python -m  cachepy.test


TODO
----

    * Writing backend for redis server
    * Testing in Python 3.x causes Error 11?!

Log list
--------

    * Version 0.1
        - initial release


.. codeauthor:: Dmitry Kislov <kislov@easydan.com>

'''

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
           'LimitedMemCache')

BASE_LOCK = threading.Lock()


class BaseCache(object):
    """Base class for cache decorator.
    """

    def __init__(self, backend=None, key='', ttl=0, noc=0, **kwargs):
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


_parameters_desription = """
    Parameters
    ==========

        {}
        :param ttl: cache time to live in seconds;
        :param key: encryption key; empty by default; if provided,
                    the cached data will be encrypted.
        :param noc: number of the function calls; 
                    if it is reached, the cache is cleared.
"""


class Cache(BaseCache):
    """Cache results of function execution in memory.

    """ + _parameters_desription.format('')

    def __init__(self, *args, **kwargs):
        super(Cache, self).__init__(*args, **kwargs)
        self.backend = MemBackend()


class FileCache(BaseCache):
    """Caches results of function execution in a file.
    """ + _parameters_desription.format("""
:param filename: name of a file, where the cached data will be stored;
""")

    def __init__(self, filename, *args,  **kwargs):
        super(FileCache, self).__init__(*args, **kwargs)
        self.backend = FileBackend(filename)


class LimitedMemCache(BaseCache):
    """Caches the result of a function execution in memory.
    Uses cache of limited capacity.

    """ + _parameters_desription.format("""
:param cache_size: cache capacity; an integer number; if it is exeeded,\
                   cached data is removed according to the algorithm\
                   (either 'lfu' or 'mfu');
:param algorithm: strategy of removing cached data; either `lfu`\
                  (least frequently used) or `mfu` (most frequently used)\
                  cached value is removed when cache is exhausted.
""")
    def __init__(self, *args, **kwargs):
        super(LimitedMemCache, self).__init__(*args, **kwargs)
        self.backend = LimitedMemBackend(**kwargs)


class LimitedFileCache(BaseCache):
    """Caches results of function execution in a file.
    """ + _parameters_desription.format("""
:param cache_size: cache capacity; an integer number; if it is exeeded,\
                   cached data is removed according to the algorithm\
                   (either 'lfu' or 'mfu');
:param algorithm: strategy of removing cached data; either `lfu`\
                  (least frequently used) or `mfu` (most frequently used)\
                  cached value is removed when cache is exhausted.
""")

    def __init__(self, filename, *args, **kwargs):
        super(LimitedFileCache, self).__init__(*args, **kwargs)
        self.backend = LimitedFileBackend(filename, **kwargs)


# ----------------- Shortcuts  --------------------------
memcache = Cache()
memcache.__doc__ = """
Shortcut for `memcache = Cache()`.

Simple cache decorator without encryption.
"""

# -------------------------------------------------------
