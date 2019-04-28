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
              retrieving data via backend['chash'] (e.g. `__getitem__`, `__setitem__`)
            - It is assumed that AES enryption algorithm is used #TODO: Update docstring!
              (`pycrypto` required to enable encryption functionality)
    """

    def _to_bytes(self, data, key='', expired=None, noc=0, ncalls=0):
        """Serialize (and encrypt if `key` is provided) the data and represent it as string.

        **Parameters**

            :param data: any python serializable (pickable) object
            :param key: If the key is provided and `pycrypto` is installed, cached
                        data will be encrypted (If `pycrypto` is not installed, this #TODO: pycrypto or something else?!
                        parameter will be ignored). Empty string by default.
            :param expired: exact date when the cache will be expired; It is `None` by default
            :param noc: the number of allowed calls; TODO: Clarify what does it mean, exactly?!!!!
            :param ncalls: What is it; I don't understand!!! TODO: clarify this!!!!
            :type key: str
            :type expired: `datetime` or `None`
            :type noc: int
            :type ncalls: int
            :returns: serialized data
            :rtype: str
        """

        data_tuple = (data, expired, noc, ncalls)

        if not can_encrypt and key:
            # TODO: Probably not only Pycrypto will be using for encryption!!!
            # Clarification needed
            warnings.warn("Pycrypto is not installed. The data will not be encrypted",
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
        """Deserialize (and decrypt if key is provided) cached
        data stored in the byte_data (bytes object).

        # TODO: Full description of the method needed

        :param sdata: a string
        :param key: if provided (e.g. non-empty string), it
                    will be used to decrypt `sdata` as a password
        :type key: str, default is empty string
        :returns: a python object
        """

        if not can_encrypt and key:
            result = decode_safely(byte_data)
        elif can_encrypt and key:
            cipher = AESCipher(key)
            result = decode_safely(cipher.decrypt(byte_data))
        else:
            result = decode_safely(byte_data)
        return result

    def store_data(self, data_key, data, key, expired, noc, ncalls):
        self[data_key] = self._to_bytes(data, key=key, expired=expired,
                                        noc=noc, ncalls=ncalls)

    def get(self, name='', default=None):
        raise NotImplementedError

    def remove(self, name):
        if not hasattr(self, '__contains__'):
            raise NotImplementedError
        if name in self:
            del self[name]

    def get_data(self, data_key, key=''):
        """Get the data from the cache.

        :param data_key: a key for accessing the data; 
        :param key: if provided (e.g. non-empty string), will be used to
                    decrypt the data as a password;
        :returns: the data extracted from the cache, a python object.
        """

        flag = False  # set to True if data was successfully extracted.
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
