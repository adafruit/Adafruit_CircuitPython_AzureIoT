# SPDX-FileCopyrightText: 2020 Jim Bennett for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`HMAC`
================================================================================

HMAC (Keyed-Hashing for Message Authentication) Python module.
Implements the HMAC algorithm as described by RFC 2104.

This is here as code instead of using https://github.com/jimbobbennett/CircuitPython_HMAC.git
as we only need sha256, so just having the code we need saves 19k of RAM

"""

try:
    from typing import Union
except ImportError:
    pass


def __translate(key: Union[bytes, bytearray], translation: bytes) -> bytes:
    return bytes(translation[x] for x in key)


TRANS_5C = bytes((x ^ 0x5C) for x in range(256))
TRANS_36 = bytes((x ^ 0x36) for x in range(256))

SHA_BLOCKSIZE = 64
SHA_DIGESTSIZE = 32


def new_shaobject() -> dict:
    """Struct. for storing SHA information."""
    return {
        "digest": [0] * 8,
        "count_lo": 0,
        "count_hi": 0,
        "data": [0] * SHA_BLOCKSIZE,
        "local": 0,
        "digestsize": 0,
    }


def sha_init() -> dict:
    """Initialize the SHA digest."""
    sha_info = new_shaobject()
    sha_info["digest"] = [
        0x6A09E667,
        0xBB67AE85,
        0x3C6EF372,
        0xA54FF53A,
        0x510E527F,
        0x9B05688C,
        0x1F83D9AB,
        0x5BE0CD19,
    ]
    sha_info["count_lo"] = 0
    sha_info["count_hi"] = 0
    sha_info["local"] = 0
    sha_info["digestsize"] = 32
    return sha_info


ROR = lambda x, y: (((x & 0xFFFFFFFF) >> (y & 31)) | (x << (32 - (y & 31)))) & 0xFFFFFFFF
Ch = lambda x, y, z: (z ^ (x & (y ^ z)))
Maj = lambda x, y, z: (((x | y) & z) | (x & y))
S = ROR
R = lambda x, n: (x & 0xFFFFFFFF) >> n
Sigma0 = lambda x: (S(x, 2) ^ S(x, 13) ^ S(x, 22))
Sigma1 = lambda x: (S(x, 6) ^ S(x, 11) ^ S(x, 25))
Gamma0 = lambda x: (S(x, 7) ^ S(x, 18) ^ R(x, 3))
Gamma1 = lambda x: (S(x, 17) ^ S(x, 19) ^ R(x, 10))


def sha_transform(sha_info: dict) -> None:
    W = []

    d = sha_info["data"]
    for i in range(0, 16):
        W.append((d[4 * i] << 24) + (d[4 * i + 1] << 16) + (d[4 * i + 2] << 8) + d[4 * i + 3])

    for i in range(16, 64):
        W.append((Gamma1(W[i - 2]) + W[i - 7] + Gamma0(W[i - 15]) + W[i - 16]) & 0xFFFFFFFF)

    ss = sha_info["digest"][:]

    def RND(a, b, c, d, e, f, g, h, i, ki):  # type: ignore[no-untyped-def]
        """Compress"""
        t0 = h + Sigma1(e) + Ch(e, f, g) + ki + W[i]
        t1 = Sigma0(a) + Maj(a, b, c)
        d += t0
        h = t0 + t1
        return d & 0xFFFFFFFF, h & 0xFFFFFFFF

    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 0, 0x428A2F98)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 1, 0x71374491)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 2, 0xB5C0FBCF)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 3, 0xE9B5DBA5)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 4, 0x3956C25B)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 5, 0x59F111F1)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 6, 0x923F82A4)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 7, 0xAB1C5ED5)
    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 8, 0xD807AA98)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 9, 0x12835B01)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 10, 0x243185BE)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 11, 0x550C7DC3)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 12, 0x72BE5D74)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 13, 0x80DEB1FE)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 14, 0x9BDC06A7)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 15, 0xC19BF174)
    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 16, 0xE49B69C1)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 17, 0xEFBE4786)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 18, 0x0FC19DC6)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 19, 0x240CA1CC)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 20, 0x2DE92C6F)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 21, 0x4A7484AA)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 22, 0x5CB0A9DC)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 23, 0x76F988DA)
    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 24, 0x983E5152)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 25, 0xA831C66D)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 26, 0xB00327C8)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 27, 0xBF597FC7)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 28, 0xC6E00BF3)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 29, 0xD5A79147)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 30, 0x06CA6351)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 31, 0x14292967)
    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 32, 0x27B70A85)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 33, 0x2E1B2138)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 34, 0x4D2C6DFC)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 35, 0x53380D13)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 36, 0x650A7354)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 37, 0x766A0ABB)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 38, 0x81C2C92E)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 39, 0x92722C85)
    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 40, 0xA2BFE8A1)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 41, 0xA81A664B)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 42, 0xC24B8B70)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 43, 0xC76C51A3)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 44, 0xD192E819)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 45, 0xD6990624)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 46, 0xF40E3585)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 47, 0x106AA070)
    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 48, 0x19A4C116)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 49, 0x1E376C08)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 50, 0x2748774C)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 51, 0x34B0BCB5)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 52, 0x391C0CB3)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 53, 0x4ED8AA4A)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 54, 0x5B9CCA4F)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 55, 0x682E6FF3)
    ss[3], ss[7] = RND(ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], 56, 0x748F82EE)
    ss[2], ss[6] = RND(ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], 57, 0x78A5636F)
    ss[1], ss[5] = RND(ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], ss[5], 58, 0x84C87814)
    ss[0], ss[4] = RND(ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], ss[4], 59, 0x8CC70208)
    ss[7], ss[3] = RND(ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], ss[3], 60, 0x90BEFFFA)
    ss[6], ss[2] = RND(ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], ss[2], 61, 0xA4506CEB)
    ss[5], ss[1] = RND(ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], ss[1], 62, 0xBEF9A3F7)
    ss[4], ss[0] = RND(ss[1], ss[2], ss[3], ss[4], ss[5], ss[6], ss[7], ss[0], 63, 0xC67178F2)

    # Feedback
    dig = []
    for i, x in enumerate(sha_info["digest"]):
        dig.append((x + ss[i]) & 0xFFFFFFFF)
    sha_info["digest"] = dig


def sha_update(sha_info: dict, buffer: Union[bytes, bytearray]) -> None:
    """Update the SHA digest.
    :param dict sha_info: SHA Digest.
    :param str buffer: SHA buffer size.
    """
    if isinstance(buffer, str):
        raise TypeError("Unicode strings must be encoded before hashing")
    count = len(buffer)
    buffer_idx = 0
    clo = (sha_info["count_lo"] + (count << 3)) & 0xFFFFFFFF
    if clo < sha_info["count_lo"]:
        sha_info["count_hi"] += 1
    sha_info["count_lo"] = clo

    sha_info["count_hi"] += count >> 29

    if sha_info["local"]:
        i = SHA_BLOCKSIZE - sha_info["local"]
        i = min(i, count)

        # copy buffer
        for x in enumerate(buffer[buffer_idx : buffer_idx + i]):
            sha_info["data"][sha_info["local"] + x[0]] = x[1]

        count -= i
        buffer_idx += i

        sha_info["local"] += i
        if sha_info["local"] != SHA_BLOCKSIZE:
            return

        sha_transform(sha_info)
        sha_info["local"] = 0
    while count >= SHA_BLOCKSIZE:
        # copy buffer
        sha_info["data"] = list(buffer[buffer_idx : buffer_idx + SHA_BLOCKSIZE])
        count -= SHA_BLOCKSIZE
        buffer_idx += SHA_BLOCKSIZE
        sha_transform(sha_info)

    # copy buffer
    pos = sha_info["local"]
    sha_info["data"][pos : pos + count] = list(buffer[buffer_idx : buffer_idx + count])
    sha_info["local"] = count


def getbuf(s: Union[str, bytes, bytearray]) -> Union[bytes, bytearray]:
    return s.encode("ascii") if isinstance(s, str) else bytes(s)


def sha_final(sha_info: dict) -> bytes:
    """Finish computing the SHA Digest."""
    lo_bit_count = sha_info["count_lo"]
    hi_bit_count = sha_info["count_hi"]
    count = (lo_bit_count >> 3) & 0x3F
    sha_info["data"][count] = 0x80
    count += 1
    if count > SHA_BLOCKSIZE - 8:
        # zero the bytes in data after the count
        sha_info["data"] = sha_info["data"][:count] + ([0] * (SHA_BLOCKSIZE - count))
        sha_transform(sha_info)
        # zero bytes in data
        sha_info["data"] = [0] * SHA_BLOCKSIZE
    else:
        sha_info["data"] = sha_info["data"][:count] + ([0] * (SHA_BLOCKSIZE - count))

    sha_info["data"][56] = (hi_bit_count >> 24) & 0xFF
    sha_info["data"][57] = (hi_bit_count >> 16) & 0xFF
    sha_info["data"][58] = (hi_bit_count >> 8) & 0xFF
    sha_info["data"][59] = (hi_bit_count >> 0) & 0xFF
    sha_info["data"][60] = (lo_bit_count >> 24) & 0xFF
    sha_info["data"][61] = (lo_bit_count >> 16) & 0xFF
    sha_info["data"][62] = (lo_bit_count >> 8) & 0xFF
    sha_info["data"][63] = (lo_bit_count >> 0) & 0xFF

    sha_transform(sha_info)

    dig = []
    for i in sha_info["digest"]:
        dig.extend([((i >> 24) & 0xFF), ((i >> 16) & 0xFF), ((i >> 8) & 0xFF), (i & 0xFF)])
    return bytes(dig)


class sha256:
    digest_size = digestsize = SHA_DIGESTSIZE
    block_size = SHA_BLOCKSIZE
    name = "sha256"

    def __init__(self, s: Union[str, bytes, bytearray] = None):
        """Constructs a SHA256 hash object."""
        self._sha = sha_init()
        if s:
            sha_update(self._sha, getbuf(s))

    def update(self, s: Union[str, bytes, bytearray]) -> None:
        """Updates the hash object with a bytes-like object, s."""
        sha_update(self._sha, getbuf(s))

    def digest(self) -> bytes:
        """Returns the digest of the data passed to the update()
        method so far."""
        return sha_final(self._sha.copy())[: self._sha["digestsize"]]

    def hexdigest(self) -> str:
        """Like digest() except the digest is returned as a string object of
        double length, containing only hexadecimal digits.
        """
        return "".join(["%.2x" % i for i in self.digest()])

    def copy(self) -> "sha256":
        """Return a copy (“clone”) of the hash object."""
        new = sha256()
        new._sha = self._sha.copy()
        return new


class HMAC:
    """RFC 2104 HMAC class.  Also complies with RFC 4231.

    This supports the API for Cryptographic Hash Functions (PEP 247).
    """

    blocksize = 64  # 512-bit HMAC; can be changed in subclasses.

    def __init__(self, key: Union[bytes, bytearray], msg: Union[bytes, bytearray] = None):
        """Create a new HMAC object.

        key:       key for the keyed hash object.
        msg:       Initial input for the hash, if provided.
        digestmod: A module supporting PEP 247.  *OR*
                   A hashlib constructor returning a new hash object. *OR*
                   A hash name suitable for hashlib.new().
                   Defaults to hashlib.md5.
                   Implicit default to hashlib.md5 is deprecated and will be
                   removed in Python 3.6.

        Note: key and msg must be a bytes or bytearray objects.
        """

        if not isinstance(key, (bytes, bytearray)):
            raise TypeError("key: expected bytes or bytearray, but got %r" % type(key).__name__)

        digestmod = sha256

        self.digest_cons = digestmod

        self.outer = self.digest_cons()
        self.inner = self.digest_cons()
        self.digest_size = self.inner.digest_size

        if hasattr(self.inner, "block_size"):
            blocksize = self.inner.block_size
            if blocksize < 16:
                blocksize = self.blocksize
        else:
            blocksize = self.blocksize

        # self.blocksize is the default blocksize. self.block_size is
        # effective block size as well as the public API attribute.
        self.block_size = blocksize

        if len(key) > blocksize:
            key = self.digest_cons(key).digest()

        key = key + bytes(blocksize - len(key))
        self.outer.update(__translate(key, TRANS_5C))
        self.inner.update(__translate(key, TRANS_36))
        if msg is not None:
            self.update(msg)

    @property
    def name(self) -> str:
        """Return the name of this object"""
        return "hmac-" + self.inner.name

    def update(self, msg: Union[bytes, bytearray]) -> None:
        """Update this hashing object with the string msg."""
        self.inner.update(msg)

    def copy(self) -> "HMAC":
        """Return a separate copy of this hashing object.

        An update to this copy won't affect the original object.
        """
        # Call __new__ directly to avoid the expensive __init__.
        other = self.__class__.__new__(self.__class__)
        other.digest_cons = self.digest_cons
        other.digest_size = self.digest_size
        other.inner = self.inner.copy()
        other.outer = self.outer.copy()
        return other

    def _current(self) -> "sha256":
        """Return a hash object for the current state.

        To be used only internally with digest() and hexdigest().
        """
        hmac = self.outer.copy()
        hmac.update(self.inner.digest())
        return hmac

    def digest(self) -> bytes:
        """Return the hash value of this hashing object.

        This returns a string containing 8-bit data.  The object is
        not altered in any way by this function; you can continue
        updating the object after calling this function.
        """
        hmac = self._current()
        return hmac.digest()

    def hexdigest(self) -> str:
        """Like digest(), but returns a string of hexadecimal digits instead."""
        hmac = self._current()
        return hmac.hexdigest()


def new_hmac(key: Union[bytes, bytearray], msg: Union[bytes, bytearray] = None) -> "HMAC":
    """Create a new hashing object and return it.

    key: The starting key for the hash.
    msg: if available, will immediately be hashed into the object's starting
    state.

    You can now feed arbitrary strings into the object using its update()
    method, and can ask for the hash value at any time by calling its digest()
    method.
    """
    return HMAC(key, msg)
