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

         python -m  cachepy.tests


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
import hashlib
import warnings
import datetime
import base64
import shelve
import sys

try:
    basestring = basestring
except NameError:
    basestring = str

try:
    from crypter import AESCipher
    crypto = True
except ImportError:
    crypto = False


try:
    import cPickle as pickle
except ImportError:
    import pickle

# -------------------- Module meta info --------------------
__author__ = "Dmitry E. Kislov"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Dmitry E. Kislov"
__email__ = "kislov@easydan.com"
# ----------------------------------------------------------

__all__ = ('Cache', 'memcache')


def _validate_key(key):
    '''Returns validated key or None'''

    if not isinstance(key, basestring):
        return None
    elif len(key) > 1000:
        return None
    else:
        return key


def _load_safely_or_none(sdata):
    result = None
    try:
        result = pickle.loads(base64.b64decode(sdata))
    except:
        warnings.warn("Could not load data.", RuntimeWarning)
    return result


def _dump_safely_or_none(data):
    result = ''
    try:
        result = base64.b64encode(pickle.dumps(data))
    except:
        warnings.warn("Data could be serialized.", RuntimeWarning)
    return result


def _hash(func, args, ttl, key, **kwargs):
    '''Compute hash of the function to be evaluated'''

    chash = hashlib.sha256()
    complhash = hashlib.md5()
    chash.update(func.__name__.encode('utf-8'))
    if args:
        for a in args:
            chash.update(repr(a).encode('utf-8'))
    for k in sorted(kwargs):
        chash.update(("%s=%s" % (k, repr(kwargs[k]))).encode('utf-8'))
    if ttl:
        chash.update(str(ttl).encode('utf-8'))
    if key and crypto:
        chash.update(str(key).encode('utf-8'))
    chash = chash.hexdigest()
    complhash.update(chash.encode('utf-8'))
    return chash + complhash.hexdigest()


class BaseBackend(object):
    '''
    Abstract backend class.

    Backends are used for storing cached data.

    .. note::
            - Backend is a dict-like object, that performs storing and
             retrieving data via backend['chash']
             (e.g. `__getitem__, __setitem__`)
            - It is assumed that AES enryption algorithm is used
              (`pycrypto` required to enable encryption functionality)
    '''

    def _tostring(self, data, key='', expired=None, noc=0, ncalls=0):
        '''
        Serialize (and encrypt if `key` is provided) data to string.

        Cache expiration date and the number of querying cache
        is stored in this string.

        **Parameters**

        :param data: any python serializable (by pickle) object
        :param key: If provided and `pycrypto` is installed cached
                    data will be encrypted
                    (If `pycrypto` not installed this
                    parameter will be ignored).
                    Default is empty string.
        :param expired: data of cache expiration or None (default)
        :param noc:  number of calls
        :type key: str
        :type expired: datetime,  None
        :type noc: int
        :type ncalls: int
        :returns: serialized data
        :rtype: str
        '''

        _key = _validate_key(key)
        _tuple = (data, expired, noc, ncalls)
        if not crypto and _key:
            warnings.warn("Pycrypto not installed. Data isn't encrypted",
                          RuntimeWarning)
            result = _dump_safely_or_none(_tuple)
        elif crypto and _key:
            cipher = AESCipher(_key)
            result = cipher.encrypt(_dump_safely_or_none(_tuple))
        else:
            result = _dump_safely_or_none(_tuple)
        return result

    def _fromstring(self, sdata, key=''):
        '''
        Deserialize (and decrypt if key is provided) cached
        data stored in the sdata (string).

        :param sdata: a string
        :param key: if provided (e.g. non-empty string), it
                    will be used to decrypt `sdata` as a password
        :type key: str, default is empty string
        :returns: a python object
        '''

        if sys.version_info >= (3, 0):
            sdata = sdata.decode('utf-8')
        _key = _validate_key(key)
        if not isinstance(sdata, basestring):
            warnings.warn("Input data must be a string", RuntimeWarning)
            return
        if not crypto and _key:
            result = _load_safely_or_none(sdata)
        elif crypto and _key:
            cipher = AESCipher(_key)
            result = _load_safely_or_none(cipher.decrypt(sdata))
        else:
            result = _load_safely_or_none(sdata)
        return result

    @property
    def valid_keys(self):
        '''Returns list of valid keys or empty list
        '''
        return [item for item in self.keys() if
                hashlib.md5(item[:-32].encode('utf-8')
                            ).hexdigest() == item[-32:]]

    def store_data(self, chash, data, key, expired, noc, ncalls):
        self[chash] = self._tostring(data, key=key, expired=expired,
                                     noc=noc, ncalls=ncalls)

    def get_data(self, chash, key='', ttl=0, noc=0):
        '''
        Get data from cache.

        :param chash: a string
        :param key: if provided (e.g. non-empty string),
                    will be used to decrypt sdata as a password
        :param ttl: time-to-live in seconds
        :param noc: maximum number of cached data retrieving
        :type ttl: int
        :type noc: int
        :returns: a python object (representing sotred data)
        '''
        res = None
        if chash in self:
            res = self._fromstring(self[chash], key=key)
        if isinstance(res, tuple):
            updated = (res[0], res[1], res[2], res[3]+1)
            self[chash] = self._tostring(updated[0], expired=updated[1],
                                         key=key, noc=updated[2],
                                         ncalls=updated[3])
            if noc and updated[3] >= noc:
                res = None
                del self[chash]
            if res is not None:
                if ttl and datetime.datetime.now() > res[1]:
                    res = None
                    del self[chash]
        return res[0] if res else None


class MemBackend(dict, BaseBackend):
    '''Used to store cached data in memory'''

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


class FileBackend(shelve.Shelf, MemBackend):
    '''Used to save cached data to file'''

    def __init__(self, filename):
        try:
            import anydbm
        except ImportError:
            import dbm as anydbm
        shelve.Shelf.__init__(self, anydbm.open(filename, flag='c'))

    def store_data(self, chash, data, key='', ttl=0, noc=0, ncalls=0):
        super(FileBackend, self).store_data(chash, data,
                                            key=key, ttl=ttl,
                                            noc=noc, ncalls=ncalls)

    def get_data(self, chash, key='', ttl=0, noc=0):
        result = super(FileBackend, self).get_data(chash, key=key,
                                                   ttl=ttl, noc=noc)
        return result if chash in self else None


class BaseCache(object):
    """Abstract class for cache decorators"""

    def __init__(self, backend=None, key='', ttl=0, noc=0):
        if isinstance(backend, basestring):
            self.backend = FileBackend(backend)
        else:
            self.backend = MemBackend()
        self.ttl = ttl
        self.key = key
        self.noc = noc

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            chash = _hash(func, list(args), self.ttl, self.key, **kwargs)
            result = self.backend.get_data(chash,
                                           key=self.key,
                                           ttl=self.ttl, noc=self.noc)

            if result is not None:
                return result
            else:
                result = func(*args, **kwargs)
                self.backend.store_data(chash, result, key=self.key,
                                        ttl=self.ttl, noc=self.noc, ncalls=0)
            if isinstance(self.backend, FileBackend):
                self.backend.sync()
            return result
        return wrapper


class Cache(BaseCache):
    ''' '''
    pass


# ----------------- Shortcuts  --------------------------
memcache = Cache()
memcache.__doc__ = '''
Shortcut for `memcache = Cache()`.

Simple cache decorator without encryption, ttl etc.
'''

# -------------------------------------------------------
