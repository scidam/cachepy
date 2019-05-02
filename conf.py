from  hashlib import sha256, md5
from base64 import b64encode, b64decode


__all__ = ('settings', )


class Settings:

    # Allowed key length
    MAX_KEY_LENGTH = 100
    MIN_KEY_LENGTH = 3

    # ENCODER & decoder
    BASE_ENCODER = staticmethod(b64encode)
    BASE_DECODER = staticmethod(b64decode)

    DEFAULT_ENCODING = 'utf-8'

    HASH_FUNCTION = staticmethod(sha256)
    KEY_HASHER = staticmethod(md5)


settings = Settings()
