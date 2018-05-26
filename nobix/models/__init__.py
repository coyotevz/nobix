# -*- coding: utf-8 -*-

from datetime import datetime
from nobix.lib.saw import SQLAlchemy


db = SQLAlchemy()


def time_now():
    return datetime.now().time()
