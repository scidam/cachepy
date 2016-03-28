import hashlib
import time
import unittest
import datetime

from __init__ import BaseCache, Backend, MemBackend
from crypter import AESCipher

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import Crypto
    crypto = True
except ImportError:
    crypto = False



# ------------------- Simple functions to be cached --------------
def function_to_cache():
    return [1, 2, 3, 4, 5]

def function_with_pars(x):
    return [x]*3

def function_with_kwargs(x, default='test'):
    return [x, default]

# ----------------------------------------------------------------


class BaseCacheHasherTests(unittest.TestCase):

    def setUp(self):
        self.mycache = BaseCache(None)
        self.mycache_ttl = BaseCache(None, ttl=5)
        self.mycache_key = BaseCache(None, key='nothing')
        self.mycache_key_ttl = BaseCache(None, ttl=5, key='nothing')
        self.hasher = hashlib.sha256()

    def test_func_hash_simple(self):
        computed = self.mycache._hash(function_to_cache)
        self.hasher.update('function_to_cache')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_simple_pars(self):
        computed = self.mycache._hash(function_with_pars, 3)
        self.hasher.update('function_with_pars3')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_simple_pars_kwargs(self):
        computed = self.mycache._hash(function_with_kwargs, 3, default=7)
        self.hasher.update('function_with_kwargs3default=7')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_ttl(self):
        computed = self.mycache_ttl._hash(function_to_cache)
        self.hasher.update('function_to_cache5')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_ttl_pars(self):
        computed = self.mycache_ttl._hash(function_with_pars, 3)
        self.hasher.update('function_with_pars35')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_ttl_pars_kwargs(self):
        computed = self.mycache_ttl._hash(function_with_kwargs, 3, default=7)
        self.hasher.update('function_with_kwargs3default=75')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_with_key(self):
        computed = self.mycache_key._hash(function_to_cache)
        if crypto:
            self.hasher.update('function_to_cachenothing')
        else:
            self.hasher.update('function_to_cache')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_with_key_pars(self):
        computed = self.mycache_key._hash(function_with_pars, 3)
        if crypto:
            self.hasher.update('function_with_pars3nothing')
        else:
            self.hasher.update('function_with_pars3')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_with_key_pars_kwargs(self):
        computed = self.mycache_key._hash(function_with_kwargs, 3, default=7)
        if crypto:
            self.hasher.update('function_with_kwargs3default=7nothing')
        else:
            self.hasher.update('function_with_kwargs3default=7')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_with_ttl_key(self):
        computed = self.mycache_key_ttl._hash(function_to_cache)
        if crypto:
            self.hasher.update('function_to_cache5nothing')
        else:
            self.hasher.update('function_to_cache5')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_with_ttl_key_pars(self):
        computed = self.mycache_key_ttl._hash(function_with_pars, 3)
        if crypto:
            self.hasher.update('function_with_pars35nothing')
        else:
            self.hasher.update('function_with_pars35')
        self.assertEqual(self.hasher.hexdigest(), computed)

    def test_func_hash_with_ttl_key_pars_kwargs(self):
        computed = self.mycache_key_ttl._hash(function_with_kwargs, 3, default=7)
        if crypto:
            self.hasher.update('function_with_kwargs3default=75nothing')
        else:
            self.hasher.update('function_with_kwargs3default=75')
        self.assertEqual(self.hasher.hexdigest(), computed)


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.curmembackend = MemBackend()
#         self.filebackend = Backend('filecache.dat')
        myhash = hashlib.md5('myhash').hexdigest()
        myhash += hashlib.md5(myhash).hexdigest()
        self.myhash = myhash

    def test_store_to_mem(self):
        self.curmembackend.store_data(self.myhash, 'sample text')
        self.assertEqual(self.curmembackend.get_data(self.myhash), 'sample text')

    def test_store_to_mem_with_ttl(self):
        self.curmembackend.store_data(self.myhash, 'sample text', ttl=1)
        self.assertEqual(self.curmembackend.get_data(self.myhash), 'sample text')
        time.sleep(2)
        self.assertIsNone(self.curmembackend.get_data(self.myhash, ttl=1))

    def test_store_to_mem_with_key(self):
        self.curmembackend.store_data(self.myhash, 'sample text', key='empty')
        self.assertEqual(self.curmembackend.get_data(self.myhash, key='empty'), 'sample text')

    def test_store_to_mem_with_key_noc(self):
        self.curmembackend.store_data(self.myhash, 'sample text', key='empty', noc=4)
        self.assertEqual(self.curmembackend.get_data(self.myhash, key='empty'), 'sample text')
        for x in range(7):
            self.curmembackend.get_data(self.myhash, key='empty', noc=4)
        self.assertIsNone(self.curmembackend.get_data(self.myhash, key='empty'))
    
    def test_store_to_mem_with_key_ttl(self):
        self.curmembackend.store_data(self.myhash, 'sample text', key='empty', noc=0, ttl=1)
        self.assertEqual(self.curmembackend.get_data(self.myhash, key='empty', ttl=1), 'sample text')
        time.sleep(2)
        self.assertIsNone(self.curmembackend.get_data(self.myhash, key='empty', ttl=1))


    def test_valid_keys_mem(self):
        self.curmembackend['wrong key'] = 'nothing'
        self.assertEqual(set(self.curmembackend.keys()), set(['wrong key']))
        self.curmembackend[self.myhash] = 'nothing'
        self.assertEqual(self.curmembackend.valid_keys, [self.myhash])


@unittest.skipIf(not crypto, "Skipped: Pycrypto not installed.")
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
