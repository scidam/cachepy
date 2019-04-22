import sys
import warnings
import hashlib
from base64 import b64encode, b64decode
from .conf import settings

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from .crypter import AESCipher
    can_encrypt = True
except ImportError:
    can_encrypt = False


PY3 = sys.version_info.major == 3 


class Helpers(object):
    """Helper class that implements prebound method pattern.
    """

    def _encoder_decoder(self):
        if settings.BASE_ENCODER == 'base64' and settings.BASE_DECODER == 'base64':
            base_encoder = b64encode
            base_decoder = b64decode
        elif callable(settings.BASE_ENCODER) and callable(settings.BASE_DECODER):
            base_encoder = settings.BASE_ENCODER
            base_decoder = settings.BASE_DECODER
        else:
            warnings.warn("Incorrect/Inconsistent encoder/decoder functions. Use defaults: base64.encoder, base64.decoder", UserWarning)
            base_encoder = b64encode
            base_decoder = b64decode
        return base_encoder, base_decoder

    @property
    def base_encoder(self):
        enc, _ = self._encoder_decoder()
        return enc
    
    @property
    def base_decoder(self):
        _, dec = self._encoder_decoder()
        return dec

    def encode_safely(self, data):
        """Encode the data.
        """
        
        encoder = self.base_encoder
        result = settings.null

        try:
            result = encoder(pickle.dumps(data))
        except:
            warnings.warn("Data could not be serialized.", RuntimeWarning)
        return result


    def decode_safely(self, encoded_data):
        """Inverse for the `encode_safely` function.
        """

        decoder = self.base_decoder
        result = settings.null

        try:
            result = pickle.loads(decoder(encoded_data))
        except:
            warnings.warn("Could not load and deserialize the data.", RuntimeWarning)
        return result

    def get_function_hash(self, func, args=None, kwargs=None, ttl=None, key=None, noc=None):
        """Compute the hash of the function to be evaluated.
        """

        base_hash = settings.HASH_FUNCTION()

        if PY3:
            base_hash.update(func.__name__.encode(settings.DEFAULT_ENCODING))
        else:
            base_hash.update(func.__name__)

        if args:
            for a in args:
                if PY3:
                    base_hash.update(repr(a).encode(settings.DEFAULT_ENCODING))
                else:
                    base_hash.update(repr(a))

        if kwargs:
            for k in sorted(kwargs):
                if PY3:
                    base_hash.update(("{}={}".format(k, repr(kwargs[k]))).encode(settings.DEFAULT_ENCODING))
                else:
                    base_hash.update(("{}={}".format(k, repr(kwargs[k]))))

        if ttl:
            base_hash.update(str(ttl).encode(settings.DEFAULT_ENCODING))

        if key and can_encrypt:
            if PY3:
                base_hash.update(key.encode(settings.DEFAULT_ENCODING))
            else:
                base_hash.update(key)

        if noc:
            base_hash.update(str(noc).encode(settings.DEFAULT_ENCODING))

        base_hash_hex = base_hash.hexdigest()

        return base_hash_hex



_helper = Helpers()

get_function_hash = _helper.get_function_hash
decode_safely = _helper.decode_safely
encode_safely = _helper.encode_safely
