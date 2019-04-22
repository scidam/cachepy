import hashlib

__all__ = ('settings', )
 

class Settings:

    # Allowed key length
    MAX_KEY_LENGTH = 100
    MIN_KEY_LENGTH = 3

    #ENCODER
    BASE_ENCODER = 'base64'
    BASE_DECODER = 'base64'

    DEFAULT_ENCODING = 'utf-8'

    HASH_FUNCTION = hashlib.sha256

    # Null object; different from possible None returned by a function is being cached
    null = object()


settings = Settings()