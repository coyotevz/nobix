"""
    nobix.lib.security
    ~~~~~~~~~~~~~~~~~~
"""

import crypt
from hmac import compare_digest


def generate_password_hash(password):
    return crypt.crypt(password)

def check_password_hash(pwhash, password):
    return compare_digest(pwhash, crypt.crypt(password, pwhash))
