
import hashlib
import warnings
import datetime
import base64

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

class BaseBackend(object):

    def _tostring(self, data, key='', expired=None, noc=0, ncalls=0):
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


class MemBackend(dict, BaseBackend):

    def store_data(self, hash, data, key='', ttl=0, noc=0, ncalls=0):
        if ttl:
            _expired = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else: 
            _expired = datetime.datetime.now()
        self[hash] = self._tostring(data, key=key, expired=_expired, noc=noc, ncalls=ncalls)

    @property
    def valid_keys(self):
        '''Get valid keys'''
        return [item for item in self.keys() if hashlib.md5(item[:-32]).hexdigest() == item[-32:]]

    def get_data(self, hash, key='', ttl=0, noc=0):
        res = None
        try: 
            res = self._fromstring(self[hash], key=key)
        except KeyError:
            warnings.warn("Key is absent...", RuntimeWarning)
        if isinstance(res, tuple):
            updated = (res[0], res[1], res[2], res[3]+1)
            self[hash] = self._tostring(updated[0], expired=updated[1], key=key, noc=updated[2], ncalls=updated[3])
            if noc and res[3] > noc:
                res = None
                del self[hash]
            if ttl and datetime.datetime.now() > res[1]:
                res = None
                del self[hash]
        return res[0] if res else None




class Backend(object):
    def __init__(self, backend=None):

        if backend is None:
            self.backend = MemBackend()

        if isinstance(backend, basestring):
            pass
        elif isinstance(backend, dict):
            pass
        else:
            pass


class BaseCache(object):
    """Store and get function results to."""

    def __init__(self, backend, key='', ttl=0):
        self.backend = backend
        self.ttl = ttl
        self.key = key

#     def __call__(self, func):
#         """Decorator function for caching results of a callable."""
# 
#         def wrapper(*args, **kwargs):
#             """Function wrapping the decorated function."""
# 
#             ckey = [func.__name__] # parameter hash
#             for a in args:
#                 ckey.append(self.__repr(a))
#             for k in sorted(kwargs):
#                 ckey.append("%s:%s" % (k, self.__repr(kwargs[k])))
#             ckey = hashlib.sha1(''.join(ckey).encode("UTF8")).hexdigest()
# 
#             if ckey in self.__cache:
#                 result = self.__cache[ckey]
#             else:
#                 result = func(*args, **kwargs)
#                 self.__cache[ckey] = result
#             self.__cache["%s:atime" % ckey] = time.time() # access time
#             if self.__livesync:
#                 self.__cache.sync()
#             return result
# 
#         return wrapper


    def _hash(self, func, *args, **kwargs):
        '''Compute hash of the function to be evaluated'''

        chash = hashlib.sha256()
        chash.update(func.__name__)
        for a in args:
            chash.update(repr(a))
        for k in sorted(kwargs):
            chash.update("%s=%s" % (k, repr(kwargs[k])))
        if self.ttl:
            chash.update(str(self.ttl))
        if self.key:
            chash.update(str(self.key))
        return chash.hexdigest()







