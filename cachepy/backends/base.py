import warnings
import datetime
from ..utils import can_encrypt, PY3, decode_safely, encode_safely

from ..conf import settings


if can_encrypt:
    from ..crypter import AESCipher


class BaseBackend(object):
    """Base backend class.

    Backends are used for control processes of storing and retrieving cached data.

    TODO: Verify docstrings!!!!

    .. note::
            - Backend is a dict-like object, that performs storing and
              retrieving data by key, e.g. backend['hash'] (e.g. `__getitem__`, `__setitem__`)
            - It is assumed that AES enryption algorithm is used
            - `pycryptodome` is required to enable encryption functionality
    """

    def _to_bytes(self, data, key='', expired=None, noc=0, ncalls=0):
        """Serialize (and encrypt if `key` is provided) the data and represent
        it as string.

        **Parameters**

            :param data: any python serializable (pickable) object
            :param key: If the key is provided (is not empty) and `pycryptodome`
                        is installed, cached data will be encrypted.
                        It is empty by default.
            :param expired: exact date when the cache will be expired; `None` by default
            :param noc: the number of allowed calls;
            :param ncalls: internal counter of calls;
            :type key: str
            :type expired: `datetime` or `None`
            :type noc: int
            :type ncalls: int
            :returns: serialized data
            :rtype: str
        """

        data_tuple = (data, expired, noc, ncalls)

        if not can_encrypt and key:
            warnings.warn("Pycrypto not installed. The data will not be encrypted",
                          UserWarning)
            result = encode_safely(data_tuple)
        elif can_encrypt and key:
            if PY3:
                cipher = AESCipher(key.encode(settings.DEFAULT_ENCODING))
            else:
                cipher = AESCipher(key)
            result = cipher.encrypt(encode_safely(data_tuple))
        else:
            result = encode_safely(data_tuple)
        return result

    def _from_bytes(self, byte_data, key=''):
        """Deserialize (and decrypt, if the key is provided) cached
        data stored in the byte_data (bytes object) parameter.
        """

        if not can_encrypt and key:
            result = decode_safely(byte_data)
        elif can_encrypt and key:
            cipher = AESCipher(key)
            result = decode_safely(cipher.decrypt(byte_data))
        else:
            result = decode_safely(byte_data)
        return result

    def store_data(self, data_key, data, key='', ttl=0, noc=0, ncalls=0):
        if ttl:
            expired = datetime.datetime.now() + datetime.timedelta(seconds=ttl)
        else:
            expired = None
        self[data_key] = self._to_bytes(data, key=key, expired=expired,
                                        noc=noc, ncalls=ncalls)

    def get(self, key='', default=None):
        raise NotImplementedError

    def popitem(self, key=None):
        raise NotImplementedError

    def remove(self, key):
        if not hasattr(self, '__contains__'):
            raise NotImplementedError
        if key in self:
            del self[key]

    def get_data(self, data_key, key=''):
        """Get data from the cache.

        :param data_key: a key for accessing the data; 
        :param key: if provided (e.g. non-empty string), will be used to
                    decrypt the data as a password;
        :returns: the data extracted from the cache, a python object.
        """

        flag = False  # set to True, if data was successfully extracted.
        extracted = self.get(data_key, -1)

        if extracted != -1:
            try:
                data, expired, noc, ncalls = self._from_bytes(extracted, key=key)
                flag = True
            except ValueError:
                return None, flag

            if noc:
                ncalls += 1
                self[data_key] = self._to_bytes(data, expired=expired,
                                                key=key, noc=noc,
                                                ncalls=ncalls)
                if ncalls >= noc:
                    self.remove(data_key)
                    flag = False

            if expired and datetime.datetime.now() > expired:
                self.remove(data_key)
                flag = False

        return (data, flag) if flag else (None, flag)


class BaseLimitedBackend(BaseBackend):
    """Base class to control cache size.

    Parameters
    ==========

        :param cache_size: integer, cache capacity, default value is {}.
        :param algorithm : string, cache-clearing algorithm; the cache is clearing when
                           it is almost exhausted; available values are `lfu` and
                           `mfu`: stands for the least frequently used and most
                           frequently used caching algorithms respectively; 
                           default value is {}.
    """.format(settings.DEFAULT_CACHE_SIZE, settings.DEFAULT_CACHE_ALGO)

    def __init__(self, *args, **kwargs):
        self._counter = dict()
        self.algorithm = kwargs.pop('algorithm', settings.DEFAULT_CACHE_ALGO)
        self.cache_size = kwargs.pop('cache_size', settings.DEFAULT_CACHE_SIZE)
        super(BaseLimitedBackend, self).__init__(*args, **kwargs)

    def store_data(self, data_key, *args, **kwargs):
        self.control_cache_size()
        super(BaseLimitedBackend, self).store_data(data_key, *args, **kwargs)
        self._counter.setdefault(data_key, 0)

    def get_data(self, data_key, *args, **kwargs):
        result = super(BaseLimitedBackend, self).get_data(data_key, *args, **kwargs)
        if result[-1]:
            self._counter[data_key] += 1
        return result

    def control_cache_size(self):
        if len(self) >= self.cache_size:
            to_remove = None
            if self._counter:
                if self.algorithm == 'mfu':
                    to_remove = max(self._counter, key=self._counter.get)
                else:
                    to_remove = min(self._counter, key=self._counter.get)
            if to_remove is None:
                if hasattr(self, 'popitem'):
                    try:
                        self.popitem()
                    except KeyError:
                        pass
                else:
                    raise RuntimeError("Cache is exhausted. No methods "
                                       "were defined for removing cached data.")
            else:
                self.remove(to_remove)
                self._counter.pop(to_remove)
