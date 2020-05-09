# The MIT License (MIT)
#
# Copyright (c) 2020 Jim Bennett
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Computes a derived symmetric key from a secret and a message
:param str secret: The secret to use for the key
:param str msg: The message to use for the key
:returns: The derived symmetric key
:rtype: bytes
"""

from .base64 import b64decode, b64encode
from .hmac import new_hmac


def compute_derived_symmetric_key(secret: str, msg: str) -> bytes:
    """Computes a derived symmetric key from a secret and a message
    :param str secret: The secret to use for the key
    :param str msg: The message to use for the key
    :returns: The derived symmetric key
    :rtype: bytes
    """
    return b64encode(new_hmac(b64decode(secret), msg=msg.encode("utf8")).digest())
