"""
    nobix.lib.security
    ~~~~~~~~~~~~~~~~~~
"""

import string
import crypt
from hmac import compare_digest
from random import SystemRandom


SALT_CHARS = string.ascii_letters + string.digits + './'
_sr = SystemRandom()


def mksalt():
    return ''.join(_sr.choice(SALT_CHARS) for char in range(16))

def generate_password_hash(password, salt=None):
    if salt is None:
        salt = mksalt()
    return crypt.crypt(password, salt)

def check_password_hash(pwhash, password):
    return compare_digest(pwhash, crypt.crypt(password, pwhash))
