import base64
import hashlib
import random
import string

from Crypto import Random
from Crypto.Cipher import AES


def padding(s, bs=AES.block_size):
    if len(s) % bs == 0:
        return s + hashlib.md5(s).hexdigest()
    if len(s) % bs > 0 and len(s) > bs:
        res = s + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - len(s) % bs -1)) + chr(96 + len(s) % bs - bs)
    else:
        res = s + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(bs - len(s) - 1)) + chr(96 + len(s) - bs)
    return res


def unpadding(s, bs=AES.block_size):
    if len(s) % bs == 0 and hashlib.md5(s[:-32]).hexdigest() == s[-32:]:
        return s[:-32]
    elif len(s) % bs == 0:
        return s[:ord(s[-1])-96]
    else:
        return ''


class AESCipher:
    def __init__(self, key):
        self.key = hashlib.md5(key).hexdigest()

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
