# -*- coding: utf-8 -*-

"""
    nobix.lib.sa_mutable
    ~~~~~~~~~~~~~~~~~~~~

    Implements some mutable-scalar types for SQLAlchemy+PostgreSQL(psycopg2)
"""

from sqlalchemy.ext.mutable import Mutable


class MutableList(Mutable, list):
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

    def __setitem__(self, idx, value):
        "Detect list set events and emit change events."
        list.__setitem__(self, idx, value)
        self.changed()

    def __delitem__(self, idx):
        "Detect list del events and emit change events."
        list.__delitem__(self, idx)
        self.changed()

    def append(self, value):
        "Detect list append event and emit change events."
        list.append(self, value)
        self.changed()
