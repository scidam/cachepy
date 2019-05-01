import hashlib
from base64 import b64decode, b64encode

__all__ = ('settings', )
 

class Settings:

    # Allowed key length
    MAX_KEY_LENGTH = 100
    MIN_KEY_LENGTH = 3

    # ENCODER & decoder
    BASE_ENCODER = b64encode
    BASE_DECODER = b64decode

    DEFAULT_ENCODING = 'utf-8'

    HASH_FUNCTION = hashlib.sha256

    # Null object; different from possible None returned by a function is being cached
    null = object()


settings = Settings()
