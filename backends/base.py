from ..utils import is_key_valid


class BaseBackend(object):
    """Base backend class

    Backends are used for storing and retrieving the data being cached.

    TODO: Verify docstrings!!!!
    .. note::
            - Backend is a dict-like object, that performs storing and
              retrieving data via backend['chash'] (e.g. `__getitem__`, `__setitem__`)
            - It is assumed that AES enryption algorithm is used #TODO: Update docstring!
              (`pycrypto` required to enable encryption functionality)
    """

    def to_string(self, data, key='', expired=None, noc=0, ncalls=0):
        '''Serialize (and encrypt if `key` is provided) the data and represent it as a string

        **Parameters**

        :param data: any python serializable (by pickle) object
        :param key: If the key is provided and `pycrypto` is installed, cached
                    data will be encrypted (If `pycrypto` is not installed, this #TODO: pycrypto or something else?!
                    parameter will be ignored). Empty string by default.
        :param expired: exact date when the cache will be expired; It is `None` by default
        :param noc: the number of allowed calls; TODO: Clarify what does it mean, exactly?!!!!
        :type key: str
        :type expired: `datetime` or `None`
        :type noc: int
        :type ncalls: int
        :returns: serialized data
        :rtype: str
        '''
        _key = key if is_key_valid(key) else None

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