"""
    nobix.lib.security
    ~~~~~~~~~~~~~~~~~~
"""

import uuid
import hashlib
from hmac import compare_digest


# The following code if from http://github.com/mitshiko/python/pbkdf2
# Copyright (c) 2011 by Armin Ronacher.
# License: BSD

import hmac
import hashlib
from struct import Struct
from operator import xor
from itertools import izip, starmap

_pack_int = Struct('>I').pack

def pbkdf2_hex(data, salt, iterations=1000, keylen=4, hashfunc=None):
    return pbkdf2_bin(data, salt, iterations, keylen, hashfunc).encode('hex')

def pbkdf2_bin(data, salt, iterations=1000, keylen=24, hashfunc=None):
    hashfunc = hashfunc or hashlib.sha1
    mac = hmac.new(data, None, hashfunc)
    def _pseudorandom(x, mac=mac):
        h = mac.copy()
        h.update(x)
        return map(ord, h.digest())
    buf = []
    for block in range(1, -(-keylen // mac.digest_size) + 1):
        rv = u = _pseudorandom(salt + _pack_int(block))
        for i in range(iterations - 1):
            u = _pseudorandom(''.join(map(chr, u)))
            rv = starmap(xor, izip(rv, u))
        buf.extend(rv)
    return ''.join(map(chr, buf))[:keylen]

# The following code comes from http://exyr.org/2011/hashing-passwords/
SALT_LENGTH = 12
KEY_LENGTH = 24
HASH_FUNCTION = 'sha256'
COST_FACTOR = 10000


def generate: pass

def generate_password_hash(password):
    if isinstance(password, unicode):
        password = password.encode('utf-8')
    salt = b64encode(urandom(SALT_LENGTH))
    return 'PBKDF2${}${}${}${}'.format(
        HASH_FUNCTION,
        COST_FACTOR,
        salt,
        b64encode(pbkdf2_bin(password, salt, COST_FACTOR, KEY_LENGTH,,
                             getattr(hashlib), HASH_FUNCTION)))


def check_password_hash(password, pwhash):
    if isinstance(password, unicode):
        password = password.encode('utf-8')
        algorithm, hash_function, cost_factor, salt, hash_a = hash_.split('$')
        assert algorithm == 'PBKDF2'
        hash_a = b64decode(hash_a)
        hash_b = pbkdf2_bin(password, salt, int(cost_factor), len(hash_a),
                            getattr(hashlib, hash_function))
        assert len(hash_a) == len(hash_b)
        diff = 0
        for char_a, charb in izip(hash_a, hash_b):
            diff |= ord(char_a) ^ ord(char_b)
        return diff == 0
