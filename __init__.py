'''
Caching results of callables in Python.

Features
--------

    * Storing cached data either on disk or in memory
    * Setting up time-to-live and max number of querying for your cache
    * Encryption of cached data with symmetric encryption (RSA) algorithm

Note
----

    Encryption functionality requires `pycrypto` package.

Examples
--------

.. code-block:: python

    from cachepy import *

    mycache = Cache() # cache to memory without encryption

    @mycache
    my_heavy_function(x)
        """Performs heavy computations"""
        print('Hi, I am called...')
        return x**2

    my_heavy_function(x) 



Tests
-----
     

TODO
----

    * Writting redis backend




Author: Dmitry E. Kislov
Email: kislov@easydan.com
Date: 30 March 2016
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


__all__ = ('MemBackend', 'FileBackend', 'Cache', 'memcache')


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
    return  chash + complhash.hexdigest() 


class BaseBackend(object):
    '''
    Abstract backend class.

    Backends are used for storing cached data.

    .. note:: 
            - Backend is a dict-like object, that performs storing and 
             retrieving data via backend['chash'] (e.g. `__getitem__, __setitem__`)
            - It is assumed that AES enryption algorithm is used 
              (`pycrypto` required to enable encryption functionality) 
    '''

    def _tostring(self, data, key='', expired=None, noc=0, ncalls=0):
        '''
        Serialize (and encrypt if `key` is provided) data to string. 

        Cache expiration date and the number of querying cache is stored in this string.

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
            warnings.warn("Pycrypto not installed. Data isn't encrypted", RuntimeWarning)
            result = _dump_safely_or_none(_tuple)
        elif crypto and _key:
            cipher = AESCipher(_key)
            result = cipher.encrypt(_dump_safely_or_none(_tuple))
        else:
            result = _dump_safely_or_none(_tuple)
        return result

    def _fromstring(self, sdata, key=''):
        '''
        Deserialize (and decrypt if key is provided) cached data stored in the sdata (string).

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
        return [item for item in self.keys() if hashlib.md5(item[:-32].encode('utf-8')).hexdigest() == item[-32:]]

    def store_data(self, chash, data, key, expired, noc, ncalls):
        self[chash] = self._tostring(data, key=key, expired=expired, noc=noc, ncalls=ncalls)

    def get_data(self, chash, key='', ttl=0, noc=0):
        '''
        Get data from cache. 

        :param sdata: a string
        :param key: if provided (e.g. non-empty string),
                    will be used to decrypt sdata as a password 
        :type key: str, default is empty string
        :returns: a python object (representing sotred data)

        '''
        res = None
        if chash in self: 
            res = self._fromstring(self[chash], key=key)
        if isinstance(res, tuple):
            updated = (res[0], res[1], res[2], res[3]+1)
            self[chash] = self._tostring(updated[0], expired=updated[1], key=key, noc=updated[2], ncalls=updated[3])
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
            _expired = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else: 
            _expired = datetime.datetime.now()
        super(MemBackend, self).store_data(chash, data, key=key, expired=_expired, noc=noc, ncalls=ncalls)

    def get_data(self, chash, key='', ttl=0, noc=0):
        return super(MemBackend, self).get_data(chash, key=key, ttl=ttl, noc=noc)


class FileBackend(shelve.Shelf, MemBackend):
    '''Used to save cached data to file'''

    def __init__(self, filename, flag='c', protocol=None, writeback=False):
        try:
            import anydbm
        except ImportError:
            import dbm as anydbm
        shelve.Shelf.__init__(self, anydbm.open(filename, flag), protocol, writeback)

    def store_data(self, chash, data, key='', ttl=0, noc=0, ncalls=0):
        super(FileBackend, self).store_data(chash, data, key=key, ttl=ttl, noc=noc, ncalls=ncalls)
        self.sync()

    def get_data(self, chash, key='', ttl=0, noc=0):
        result =  super(FileBackend, self).get_data(chash, key=key, ttl=ttl, noc=noc)
        self.sync()
        return result if chash in self else None


class BaseCache(object):
    """Store and get function results to."""

    def __init__(self, backend=None, key='', ttl=0, noc=0):
        if isinstance(backend, basestring):
            self.backend = FileBackend(backend)
        else:
            self.backend = MemBackend()
        self.ttl = ttl
        self.key = key
        self.noc = noc

    def __call__(self, func):
        """Decorator function for caching results of a callable."""
        def wrapper(*args, **kwargs):
            """Function wrapping the decorated function."""
            chash = _hash(func, list(args), self.ttl, self.key, **kwargs)
            result = self.backend.get_data(chash, key=self.key, ttl=self.ttl, noc=self.noc)
            if result is not None:
                return result
            else:
                result = func(*args, **kwargs)
                self.backend.store_data(chash, result, key=self.key, ttl=self.ttl, noc=self.noc, ncalls=0)
            return result
        return wrapper


class Cache(BaseCache):
    pass


# ----------------- Shortcuts  --------------------------
memcache = Cache()
memcache.__doc__='''
Shortcut for `memcache = Cache()`. 

Simple cache decorator without encryption, ttl etc.
'''

# -------------------------------------------------------
# 
# if __name__ == "__main__":
#     import doctest
#     doctest.testmod()
