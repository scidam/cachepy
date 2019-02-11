import base64
import random
import string
import binascii
import hashlib
import sys
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHAKE128
from .conf import DEFAULT_ENCODING

PY3 = sys.version_info.major == 3

def padding(s, bs=AES.block_size):
    """Fills a string with arbitrary symbols to make its length divisible by `bs`.
    """

    if PY3:
        s = s.decode(DEFAULT_ENCODING)

    if len(s) % bs == 0:
        res = s + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - 1)) + chr(96 - bs)
    elif len(s) % bs > 0 and len(s) > bs:
        res = s + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - len(s) % bs -1)) + chr(96 + len(s) % bs - bs)
    else:
        res = s + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - len(s) - 1)) + chr(96 + len(s) - bs)
    return res.encode(DEFAULT_ENCODING) if PY3 else res


def unpadding(s, bs=AES.block_size):
    """Reverse operation to padding (see above)
    """

    # if PY3:
    #     s = s.decode(DEFAULT_ENCODING)
    return s[:ord(s[-1])-96] if len(s) % bs == 0 else ''


class AESCipher:
    def __init__(self, key):
        self.key = hashlib.md5(key).hexdigest()
        if PY3:
            self.key = self.key.encode(DEFAULT_ENCODING)


    def encrypt(self, raw):
        raw = padding(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpadding(cipher.decrypt(enc[AES.block_size:]))
