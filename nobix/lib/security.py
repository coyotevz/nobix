"""
    nobix.lib.security
    ~~~~~~~~~~~~~~~~~~
"""

import uuid
import hashlib
from hmac import compare_digest


def generate_password_hash(password, salt=None):
    if salt is None:
        salt = uuid.uuid4().hex
    return salt + '$' + hashlib.sha512(password + salt).hexdigest()

def check_password_hash(pwhash, password):
    if pwhash.count('$') < 1:
        return False
    s, _, h = pwhash.partition('$')
    return compare_digest(str(h), hashlib.sha512(password + s).hexdigest())
