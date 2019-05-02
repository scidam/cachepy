import hashlib
import time
import unittest
import base64

from .utils import get_function_hash, PY3, can_encrypt

if can_encrypt:
    from .utils import AESCipher

from . import FileBackend, MemBackend, Cache
from .conf import settings

DEFAULT_ENCODING = settings.DEFAULT_ENCODING

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import numpy as np
except ImportError:
    np = None


# ------------------- Simple functions to be cached --------------

def function_to_cache():
    return [1, 2, 3, 4, 5]


def function_with_pars(x):
    return [x]*3


def function_with_kwargs(x, default='test'):
    return [x, default]


def function_returns_dict(x):
    return {'output': x}


def function_returns_random_numpy(size):
    return np.random.rand(size, size)


def function_returns_none(x):
    return None
# ----------------------------------------------------------------


class BaseCacheHasherTests(unittest.TestCase):

    def hasher(self, s):
        ss = hashlib.sha256()
        if PY3:
            ss.update(s.encode(DEFAULT_ENCODING))
        else:
            ss.update(s)
        ss = ss.hexdigest()
        return ss

    def setUp(self):
        self.mycache = Cache(None)
        self.mycache_ttl = Cache(None, ttl=5)
        self.mycache_key = Cache(None, key='nothing')
        self.mycache_key_ttl = Cache(None, ttl=5, key='nothing')

    def test_get_function_hash_simple(self):
        computed = get_function_hash(function_to_cache, args=([], 0, ''))
        self.assertEqual(self.hasher("function_to_cache[]0''"), computed)

    def test_get_function_hash_simple_pars(self):
        computed = get_function_hash(function_with_pars, args=([3], 0, ''))
        self.assertEqual(self.hasher("function_with_pars[3]0''"), computed)

    def test_get_function_hash_simple_pars_kwargs(self):
        computed = get_function_hash(function_with_kwargs, args=([3], 0, ''), kwargs={'default': 7})
        self.assertEqual(self.hasher("function_with_kwargs[3]0''default=7"),
                         computed)

    def test_get_function_hash_ttl(self):
        computed = get_function_hash(function_to_cache, args=([], 5, ''))
        self.assertEqual(self.hasher("function_to_cache[]5''"), computed)

    def test_get_function_hash_ttl_pars(self):
        computed = get_function_hash(function_with_pars, args=([3], 5, ''))
        self.assertEqual(self.hasher("function_with_pars[3]5''"), computed)

    def test_get_function_hash_ttl_pars_kwargs(self):
        computed = get_function_hash(function_with_kwargs, args=([3], ''), 
                                     ttl=5, kwargs={'default': 7})
        self.assertEqual(self.hasher("function_with_kwargs[3]''default=75"),
                         computed)

    def test_get_function_hash_with_key(self):
        computed = get_function_hash(function_to_cache, args=([], 0), key='nothing')
        if can_encrypt:
            res = self.hasher('function_to_cache[]0nothing')
        else:
            res = self.hasher('function_to_cache[]0')
        self.assertEqual(res, computed)

    def test_get_function_hash_with_key_pars(self):
        computed = get_function_hash(function_with_pars, args=([3], 0), key='nothing')
        if can_encrypt:
            res = self.hasher('function_with_pars[3]0nothing')
        else:
            res = self.hasher('function_with_pars[3]0')
        self.assertEqual(res, computed)

    def test_get_function_hash_with_key_pars_kwargs(self):
        computed = get_function_hash(function_with_kwargs, args=([3], 0),
                                     key='nothing', kwargs={'default': 7})
        if can_encrypt:
            res = self.hasher('function_with_kwargs[3]0default=7nothing')
        else:
            res = self.hasher('function_with_kwargs[3]0default=7')
        self.assertEqual(res, computed)

    def test_get_function_hash_with_ttl_key(self):
        computed = get_function_hash(function_to_cache, args=([],), ttl=5, key='nothing')
        if can_encrypt:
            res = self.hasher('function_to_cache[]5nothing')
        else:
            res = self.hasher('function_to_cache[]5')
        self.assertEqual(res, computed)

    def test_get_function_hash_with_ttl_key_pars(self):
        computed = get_function_hash(function_with_pars, args=(3,), ttl=5, key='nothing')
        if can_encrypt:
            res = self.hasher('function_with_pars35nothing')
        else:
            res = self.hasher('function_with_pars35')
        self.assertEqual(res, computed)

    def test_get_function_hash_with_ttl_key_pars_kwargs(self):
        computed = get_function_hash(function_with_kwargs, args=(3,), ttl=5, key='nothing', kwargs={'default':7})
        if can_encrypt:
            res = self.hasher('function_with_kwargs3default=75nothing')
        else:
            res = self.hasher('function_with_kwargs3default=75')
        self.assertEqual(res, computed)


class BaseCacheToMemTests(unittest.TestCase):

    def setUp(self):
        self.decorator = Cache()
        self.decorator_key = Cache(key='a')
        self.decorator_key_ttl_noc = Cache(key='a', ttl=1, noc=2)

    def test_cache_clearing(self):
        simple = self.decorator(function_to_cache)
        simple()
        self.assertEqual(self.decorator.backend.get_data(get_function_hash(function_to_cache, args=tuple()))[0], [1, 2, 3, 4, 5])
        simple.clear()
        _, flag = self.decorator.backend.get_data(get_function_hash(function_to_cache, args=tuple()))
        self.assertFalse(flag)

    def test_two_functions_same_decorator(self):
        simple = self.decorator(function_to_cache)
        with self.assertRaises(RuntimeError):
            # The `simple` decorator is already used, exception should be raised here.
            simple1 = self.decorator(function_returns_none)

    def test_function_returns_none(self):
        simple = self.decorator(function_returns_none)
        simple(3)
        data, flag = self.decorator.backend.get_data(get_function_hash(function_returns_none, args=(3,)))
        self.assertTrue(flag)
        self.assertIsNone(data)

    def test_simple_function(self):
        simple = self.decorator(function_to_cache)
        self.assertEqual(simple(), [1, 2, 3, 4, 5])

    def test_simple_function_key(self):
        simple = self.decorator_key(function_to_cache)
        self.assertEqual(simple(), [1, 2, 3, 4, 5])

    def test_simple_function_ttl_noc(self):
        simple = self.decorator_key_ttl_noc(function_to_cache)
        self.assertEqual(simple(), [1, 2, 3, 4, 5])

    def test_function_returns_dict(self):
        dictfun = self.decorator(function_returns_dict)
        self.assertEqual(dictfun(2), {'output': 2})

    @unittest.skipIf(not np, "Skipped: Numpy is not installed.")
    def test_function_returns_np(self):
        npfun = self.decorator(function_returns_random_numpy)
        self.assertEqual(np.shape(npfun(3)), (3, 3))
        np.testing.assert_array_equal(npfun(3), npfun(3))

    @unittest.skipIf(not np, "Skipped: Numpy is not installed.")
    def test_function_returns_np_noc(self):
        npfun = self.decorator_key_ttl_noc(function_returns_random_numpy)
        res = npfun(2) # compute the value
        res1 = npfun(2) # get the value from cache
        npfun(2) # get the value from cache
        res2 = npfun(2) # recompute the value
        np.testing.assert_array_equal(res, res1)
        self.assertFalse((res == res2).all())

    @unittest.skipIf(not np, "Skipped: Numpy is not installed.")
    def test_function_returns_np_ttl(self):
        npfun = self.decorator_key_ttl_noc(function_returns_random_numpy)
        res = npfun(2)
        res1 = npfun(2)
        time.sleep(2)
        res2 = npfun(2)
        np.testing.assert_array_equal(res, res1)
        self.assertFalse((res == res2).all())


class BaseCacheToFileTests(BaseCacheToMemTests):

    def clear_storage(self):
        import os
        try:
            os.remove('testfilecache.dat')
        except (IOError, OSError):
            pass

    def setUp(self):
        self.decorator = Cache('testfilecache.dat')
        self.decorator_key = Cache('testfilecache.dat', key='a')
        self.decorator_key_ttl_noc = Cache('testfilecache.dat', key='a',
                                           ttl=1, noc=2)

    def tearDown(self):
        self.clear_storage()


class MemBackendTests(unittest.TestCase):

    def setUp(self):
        self.backend = MemBackend()
        myhash = hashlib.md5('myhash'.encode(DEFAULT_ENCODING)).hexdigest()
        self.myhash = myhash

    def test_store_to_mem(self):
        self.backend.store_data(self.myhash, 'sample text')
        self.assertEqual(self.backend.get_data(self.myhash)[0], 'sample text')

    def test_store_to_mem_with_ttl(self):
        self.backend.store_data(self.myhash, 'sample text', ttl=1)
        self.assertEqual(self.backend.get_data(self.myhash)[0], 'sample text')
        time.sleep(2)
        self.assertIsNone(self.backend.get_data(self.myhash)[0])

    def test_store_to_mem_with_key(self):
        self.backend.store_data(self.myhash, 'sample text', key='empty')
        self.assertEqual(self.backend.get_data(self.myhash, key='empty')[0],
                         'sample text')

    def test_store_to_mem_with_key_noc(self):
        self.backend.store_data(self.myhash, 'sample text', key='empty', noc=4)
        self.assertEqual(self.backend.get_data(self.myhash, key='empty')[0],
                         'sample text')
        for _ in range(7):
            self.backend.get_data(self.myhash, key='empty')
        self.assertIsNone(self.backend.get_data(self.myhash, key='empty')[0])

    def test_store_to_mem_with_key_ttl(self):
        self.backend.store_data(self.myhash, 'sample text', key='empty',
                                noc=0, ttl=1)
        self.assertEqual(self.backend.get_data(self.myhash, key='empty')[0],
                         'sample text')
        time.sleep(2)
        self.assertIsNone(self.backend.get_data(self.myhash, key='empty')[0])


class ChangingSettingsOnTheFly(unittest.TestCase):
    def setUp(self):
        from .conf import settings
        self.backend = MemBackend()
        self.settings = settings
        self.old_decoder = self.settings.BASE_DECODER

    def test_switching_settings(self):
        self.backend.store_data('hash_value', 'sample text')
        self.settings.BASE_DECODER = staticmethod(base64.b16decode)
        with self.assertRaises(BaseException):
            val, fl = self.backend.get_data('hash_value')
        self.settings.BASE_DECODER = self.old_decoder
        self.assertEqual(self.backend.get_data('hash_value')[0], 'sample text')

    def tearDown(self):
        self.settings.BASE_DECODER = self.old_decoder


class FileBackendTests(MemBackendTests):

    def clear_storage(self):
        import os
        try:
            os.remove('testfilecache.dat')
        except (OSError, IOError):
            pass

    def setUp(self):
        self.clear_storage()
        self.backend = FileBackend('testfilecache.dat')
        myhash = hashlib.md5('myhash'.encode(DEFAULT_ENCODING)).hexdigest()
        myhash += hashlib.md5(myhash.encode(DEFAULT_ENCODING)).hexdigest()
        self.myhash = myhash

    def tearDown(self):
        self.clear_storage()
    
    # TODO:  Some test should be written!!!


@unittest.skipIf(not can_encrypt, "Skipped: Pycan_encrypt is not installed.")
class CrypterTests(unittest.TestCase):
    def setUp(self):
        self.cipher = AESCipher('scidam'.encode(DEFAULT_ENCODING))

    def test_one_symbol_encrypt(self):
        word = 'a'.encode(DEFAULT_ENCODING)
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(word)), word)

    def test_16byte_encrypt(self):
        word = 'scidamanotherlog'.encode(DEFAULT_ENCODING)
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(word)), word)

    def test_long_encrypt(self):
        word = ('scidams' * 123).encode(DEFAULT_ENCODING)
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(word)), word)

    def test_64byte_encrypt(self):
        word = ('scidamus' * 8).encode(DEFAULT_ENCODING)
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(word)), word)

    def test_key_structure(self):
        expected = hashlib.md5('scidam'.encode(DEFAULT_ENCODING)).hexdigest().encode(DEFAULT_ENCODING)
        self.assertEqual(self.cipher.key, expected)

    def test_empty_encrypt(self):
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(b'')), b'')


if __name__ == '__main__':
    unittest.main()
