import sys
import warnings
import hashlib
from .conf import *

PY3 = sys.version_info.major == 3 

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    basestring = basestring
except NameError:
    basestring = str

try:
    from .crypter import AESCipher
    can_encrypt = True
except ImportError:
    can_encrypt = False

from base64 import b64encode, b64decode

if BASE_ENCODER == 'base64' and BASE_DECODER == 'base64':
    base_encoder = b64encode
    base_decoder = b64decode
elif 1:  # TODO: Check if encoder is a function, that has some desired futures. 
    pass
else:
    # TODO: SHOW WARNING HERE, SINCE THE ENCODER PROVIDED BY THE USER DOESN"T MEET REQUIREMENTS
    base_encoder = b64encode
    base_decoder = b64decode


def is_key_valid(key):
    """Check if the key is valid or not.
    """

    if isinstance(key, basestring):
        if MIN_KEY_LENGTH <= len(key) <= MAX_KEY_LENGTH:
            return True
    return False


def encode_safely(data, encoder=base_encoder):
    """Encode the data.

    Default encoder is base64.
    """

    result = ""
    try:
        result = encoder(pickle.dumps(data))
    except:
        # Raise an error HERE!!! TODO: 
        # The data could not be encoded, so it could not
        # be stored in our key-store!!!
        warnings.warn("Data could be serialized.", RuntimeWarning)
    return result


def decode_safely(encoded_data, decoder=base_decoder):
    """Inverse for the `encode_safely` function.
    """

    result = None
    try:
        result = pickle.loads(decoder(sdata))
    except:
        # TODO: COuld not decode the data, something was wrong with the data; anything can happen here!!!
        # So, we need to use wildcard exception here
        # This is an error exception, not warning.
        warnings.warn("Could not load the data.", RuntimeWarning)
    return result


def get_function_hash(func, args=None, kwargs=None, ttl=None, key=None):
    """Compute the hash of the function to be evaluated.

    # TODO: Full description of the algorithm needed!!!!

    """

    base_hash = hashlib.sha256()
    complementary_hash = hashlib.md5()

    if PY3:
        base_hash.update(func.__name__.encode(DEFAULT_ENCODING))
    else:
        base_hash.update(func.__name__)

    if args:
        for a in args:
            if PY3:
                base_hash.update(repr(a).encode(DEFAULT_ENCODING))
            else:
                base_hash.update(repr(a))

    if kwargs:
        for k in sorted(kwargs):
            if PY3:
                base_hash.update(("%s=%s" % (k, repr(kwargs[k]))).encode(DEFAULT_ENCODING))
            else:
                base_hash.update(("%s=%s" % (k, repr(kwargs[k]))))
        
    if ttl:
        base_hash.update(str(ttl).encode(DEFAULT_ENCODING)) # NOTE: ttl is int

    if key and can_encrypt:
        if PY3:
            base_hash.update(key.encode(DEFAULT_ENCODING))
        else:
            base_hash.update(key)
    
    base_hash_hex = base_hash.hexdigest()
    complementary_hash.update(base_hash_hex.encode(DEFAULT_ENCODING))

    return base_hash_hex + complementary_hash.hexdigest()