"""Computes a derived symmetric key from a secret and a message
:param str secret: The secret to use for the key
:param str msg: The message to use for the key
:returns: The derived symmetric key
:rtype: bytes
"""

import circuitpython_base64 as base64
from .hmac import new_hmac

def compute_derived_symmetric_key(secret: str, msg: str) -> bytes:
    """Computes a derived symmetric key from a secret and a message
    :param str secret: The secret to use for the key
    :param str msg: The message to use for the key
    :returns: The derived symmetric key
    :rtype: bytes
    """
    secret = base64.b64decode(secret)
    return base64.b64encode(new_hmac(secret, msg=msg.encode("utf8")).digest())
