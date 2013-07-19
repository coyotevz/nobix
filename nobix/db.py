#!/usr/bin/env python
# -*- coding: utf-8 -*-

import decimal

from sqlalchemy import MetaData, create_engine
from sqlalchemy import types
from sqlalchemy.orm import sessionmaker, scoped_session

import elixir
from elixir import metadata
from elixir import session as Session

#metadata = MetaData()
#Session = scoped_session(sessionmaker())

def setup_db(db_uri, echo=False):
    #from nobix.schema import check_migration_table
    from nobix.models import check_migration_table

    engine = create_engine(db_uri, echo=echo)
    if engine.name == "sqlite":
        conn = engine.raw_connection()
        conn.connection.create_function("regexp", 2, _sqlite_regexp)
#    Session.configure(bind=engine)
    metadata.bind = engine
    check_migration_table(bind=engine)
    elixir.setup_all()
    elixir.create_all()
#    metadata.create_all(bind=engine)

# From: http://www.sqlalchemy.org/trac/ticket/1759
class ShiftedDecimal(types.TypeDecorator):
    impl = types.Integer

    def __init__(self, scale):
        types.TypeDecorator.__init__(self)
        self.scale = scale

    def process_bind_param(self, value, dialect):
        if value is not None:
            # posible bug en el modulo decimal?? valor para el que falla total = 134.00
            #value = value.shift(decimal.Decimal(self.scale))
            #value = decimal.Decimal(value) * (10**self.scale)
            value = decimal.Decimal(value).scaleb(self.scale)
            value = int(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = decimal.Decimal(str(value))
            value = value * decimal.Decimal("1E-%d" % self.scale)
        return value

    def copy(self):
        return ShiftedDecimal(self.scale)

# Custom type that implements types.Numeric as ShiftedDecimal for sqlite backend
class Numeric(types.TypeDecorator):
    impl = types.Numeric

    def __init__(self, precision=None, scale=None, asdecimal=True):
        types.TypeDecorator.__init__(self, precision, scale, asdecimal)
        if scale is None:
            scale = 2
        self.scale = scale

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return ShiftedDecimal(self.scale)
        else:
            return super(Numeric, self).load_dialect_impl(dialect)


## Adding RegExp support to SQLite
def _sqlite_regexp(re_pattern, re_string):
    import re
    try:
        return bool(re.search(re_pattern, re_string))
    except:
        return False

def _sqlite_regexp2(re_pattern, re_string):
    import re
    r = re.compile(re_pattern)
    return r.match(item) is not None

def REGEXP(col, exp):
    return col.op('REGEXP')(exp)

def IREGEXP(col, exp):
    return REGEXP(col, '(?i)'+exp)
