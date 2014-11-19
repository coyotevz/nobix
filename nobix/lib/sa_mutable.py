# -*- coding: utf-8 -*-

"""
    nobix.lib.sa_mutable
    ~~~~~~~~~~~~~~~~~~~~

    Implements some mutable-scalar types for SQLAlchemy+PostgreSQL(psycopg2)
"""

from collections import MutableSequence
from sqlalchemy.ext.mutable import Mutable


class MutableList(Mutable, MutableSequence):
    "Use as MutableList.as_mutable(ARRAY(<type>))"

    @classmethod
    def coerce(cls, key, value):
        "Convert plain list or tuple to MutableList."
        if not isinstance(value, MutableList):
            if isinstance(value, (list, tuple)):
                return MutableList(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __init__(self, initlist=None):
        self._data = []
        if initlist is not None:
            self._data = list(initlist)

    def __getitem__(self, index):
        return list.__getitem__(self._data, index)

    def __len__(self):
        return list.__len__(self._data)

    def __setitem__(self, index, value):
        "Detect list set events and emit change events."
        list.__setitem__(self._data, index, value)
        self.changed()

    def __delitem__(self, index):
        "Detect list del events and emit change events."
        list.__delitem__(self._data, index)
        self.changed()

    def insert(self, index, value):
        "Detect list insert events and emit change events."
        list.insert(self._data, index, value)
        self.changed()
