import base64
import random
import string
import hashlib
import sys
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHAKE128
from .conf import DEFAULT_ENCODING

PY3 = sys.version_info.major == 3


def to_bytes(obj):
    """Ensures that the obj is of byte-type.
    """

    if PY3:
        if isinstance(obj, str):
            return obj.encode(DEFAULT_ENCODING)
        else:
            return obj if isinstance(obj, bytes) else b''
    else:
        if isinstance(obj, str):
            return obj
        else:
            return obj.encode(DEFAULT_ENCODING) if isinstance(obj, unicode) else ''


def padding(s, bs=AES.block_size):
    """Fills a bytes-like object with arbitrary symbols to make its length divisible by `bs`.
    """
    
    s = to_bytes(s)

    if len(s) % bs == 0:
        res = s + b''.join(map(to_bytes, [random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - 1)])) + to_bytes(chr(96 - bs))
    elif len(s) % bs > 0 and len(s) > bs:
        res = s + b''.join(map(to_bytes, [random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - len(s) % bs -1)])) + to_bytes(chr(96 + len(s) % bs - bs))
    else:
        res = s + b''.join(map(to_bytes, [random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - len(s) - 1)])) + to_bytes(chr(96 + len(s) - bs))
    return res


def unpadding(s, bs=AES.block_size):
    """Reverse operation to padding (see above).

    Parameters
    ==========

        :param s: bytes-like object;
        :param bs: encryption block size.
    """

    if PY3:
        return s[:s[-1]-96] if len(s) % bs == 0 else ''
    else:
        return s[:ord(s[-1])-96] if len(s) % bs == 0 else ''


class AESCipher:
    def __init__(self, key):
        """ 
        Parameters
        ==========

            :param key: a string

        Note
        ====

            The key is internally represented as a byte-object. 
        """

        self.key = to_bytes(hashlib.md5(to_bytes(key)).hexdigest())

    def encrypt(self, raw):
        """Encrypt a string (either a string of bytes or a regular string).

        Parameters
        ==========

            :param raw: a string of bytes to be encrypted.
        """

        raw = padding(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpadding(cipher.decrypt(enc[AES.block_size:]))
