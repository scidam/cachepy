
import hashlib



try:
    basestring = basestring
except NameError:
    basestring = str

try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None


try:
    import cPickle as pickle
except ImportError:
    import pickle


class Backend(object):
    def __init__(self, backend):
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
        if self.key and AES:
            chash.update(str(self.key))
        return chash.hexdigest()







