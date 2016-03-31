import hashlib
import time
import unittest

from . import _hash, FileBackend, MemBackend, Cache

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from crypter import AESCipher
    crypto = True
except ImportError:
    crypto = False

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
# ----------------------------------------------------------------


class BaseCacheHasherTests(unittest.TestCase):

    def hasher(self, s):
        ss = hashlib.sha256()
        ww = hashlib.md5()
        ss.update(s.encode('utf-8'))
        ss = ss.hexdigest()
        ww.update(ss.encode('utf-8'))
        return ss + ww.hexdigest()

    def setUp(self):
        self.mycache = Cache(None)
        self.mycache_ttl = Cache(None, ttl=5)
        self.mycache_key = Cache(None, key='nothing')
        self.mycache_key_ttl = Cache(None, ttl=5, key='nothing')

    def test_func_hash_simple(self):
        computed = _hash(function_to_cache, [], 0, '')
        self.assertEqual(self.hasher('function_to_cache'), computed)

    def test_func_hash_simple_pars(self):
        computed = _hash(function_with_pars, [3], 0, '')
        self.assertEqual(self.hasher('function_with_pars3'), computed)

    def test_func_hash_simple_pars_kwargs(self):
        computed = _hash(function_with_kwargs, [3], 0, '', default=7)
        self.assertEqual(self.hasher('function_with_kwargs3default=7'),
                         computed)

    def test_func_hash_ttl(self):
        computed = _hash(function_to_cache, [], 5, '')
        self.assertEqual(self.hasher('function_to_cache5'), computed)

    def test_func_hash_ttl_pars(self):
        computed = _hash(function_with_pars, [3], 5, '')
        self.assertEqual(self.hasher('function_with_pars35'), computed)

    def test_func_hash_ttl_pars_kwargs(self):
        computed = _hash(function_with_kwargs, [3], 5, '', default=7)
        self.assertEqual(self.hasher('function_with_kwargs3default=75'),
                         computed)

    def test_func_hash_with_key(self):
        computed = _hash(function_to_cache, [], 0, 'nothing')
        if crypto:
            res = self.hasher('function_to_cachenothing')
        else:
            res = self.hasher('function_to_cache')
        self.assertEqual(res, computed)

    def test_func_hash_with_key_pars(self):
        computed = _hash(function_with_pars, [3], 0, 'nothing')
        if crypto:
            res = self.hasher('function_with_pars3nothing')
        else:
            res = self.hasher('function_with_pars3')
        self.assertEqual(res, computed)

    def test_func_hash_with_key_pars_kwargs(self):
        computed = _hash(function_with_kwargs, [3], 0, 'nothing', default=7)
        if crypto:
            res = self.hasher('function_with_kwargs3default=7nothing')
        else:
            res = self.hasher('function_with_kwargs3default=7')
        self.assertEqual(res, computed)

    def test_func_hash_with_ttl_key(self):
        computed = _hash(function_to_cache, [], 5, 'nothing')
        if crypto:
            res = self.hasher('function_to_cache5nothing')
        else:
            res = self.hasher('function_to_cache5')
        self.assertEqual(res, computed)

    def test_func_hash_with_ttl_key_pars(self):
        computed = _hash(function_with_pars, [3], 5, 'nothing')
        if crypto:
            res = self.hasher('function_with_pars35nothing')
        else:
            res = self.hasher('function_with_pars35')
        self.assertEqual(res, computed)

    def test_func_hash_with_ttl_key_pars_kwargs(self):
        computed = _hash(function_with_kwargs, [3], 5, 'nothing', default=7)
        if crypto:
            res = self.hasher('function_with_kwargs3default=75nothing')
        else:
            res = self.hasher('function_with_kwargs3default=75')
        self.assertEqual(res, computed)


class BaseCacheToMemTests(unittest.TestCase):

    def setUp(self):
        self.decorator = Cache()
        self.decorator_key = Cache(key='a')
        self.decorator_key_ttl_noc = Cache(key='a', ttl=1, noc=2)

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
        res = npfun(2)
        res1 = npfun(2)
        res2 = npfun(2)
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
        myhash = hashlib.md5('myhash'.encode('utf-8')).hexdigest()
        myhash += hashlib.md5(myhash.encode('utf-8')).hexdigest()
        self.myhash = myhash

    def test_store_to_mem(self):
        self.backend.store_data(self.myhash, 'sample text')
        self.assertEqual(self.backend.get_data(self.myhash), 'sample text')

    def test_store_to_mem_with_ttl(self):
        self.backend.store_data(self.myhash, 'sample text', ttl=1)
        self.assertEqual(self.backend.get_data(self.myhash), 'sample text')
        time.sleep(2)
        self.assertIsNone(self.backend.get_data(self.myhash, ttl=1))

    def test_store_to_mem_with_key(self):
        self.backend.store_data(self.myhash, 'sample text', key='empty')
        self.assertEqual(self.backend.get_data(self.myhash, key='empty'),
                         'sample text')

    def test_store_to_mem_with_key_noc(self):
        self.backend.store_data(self.myhash, 'sample text', key='empty', noc=4)
        self.assertEqual(self.backend.get_data(self.myhash, key='empty'),
                         'sample text')
        for x in range(7):
            self.backend.get_data(self.myhash, key='empty', noc=4)
        self.assertIsNone(self.backend.get_data(self.myhash, key='empty'))

    def test_store_to_mem_with_key_ttl(self):
        self.backend.store_data(self.myhash, 'sample text', key='empty',
                                noc=0, ttl=1)
        self.assertEqual(self.backend.get_data(self.myhash,
                                               key='empty', ttl=1),
                         'sample text')
        time.sleep(2)
        self.assertIsNone(self.backend.get_data(self.myhash,
                                                key='empty', ttl=1))

    def test_valid_keys_mem(self):
        self.backend['wrong key'] = 'nothing'
        self.assertEqual(set(self.backend.keys()), set(['wrong key']))
        self.backend[self.myhash] = 'nothing'
        self.assertEqual(self.backend.valid_keys, [self.myhash])


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
        myhash = hashlib.md5('myhash'.encode('utf-8')).hexdigest()
        myhash += hashlib.md5(myhash.encode('utf-8')).hexdigest()
        self.myhash = myhash

    def tearDown(self):
        self.clear_storage()


@unittest.skipIf(not crypto, "Skipped: Pycrypto is not installed.")
class CrypterTests(unittest.TestCase):
    def setUp(self):
        self.cipher = AESCipher('scidam')

    def test_one_symbol_encrypt(self):
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt('a')), 'a')

    def test_16byte_encrypt(self):
        word = 'scidamanotherlog'
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(word)), word)

    def test_long_encrypt(self):
        word = 'scidams'*123
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(word)), word)

    def test_64byte_encrypt(self):
        word = 'scidamus'*8
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt(word)), word)

    def test_key_structure(self):
        self.assertEqual(self.cipher.key, hashlib.md5('scidam').hexdigest())

    def test_empty_encrypt(self):
        self.assertEqual(self.cipher.decrypt(self.cipher.encrypt('')), '')


if __name__ == '__main__':
    unittest.main()
