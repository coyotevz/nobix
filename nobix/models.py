# !/usr/bin/env python
#  -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

# from sqlalchemy.orm import mapper, relation, synonym, object_mapper, backref, object_session
# from sqlalchemy.sql import select, func
# from sqlalchemy import UniqueConstraint, Table, Column
# 
# import elixir
# elixir.options_defaults['mapper_options'] = {'save_on_init': False}
# 
# from elixir import EntityBase, EntityMeta, ColumnProperty
# from elixir import db.Column, Integer, Unicode, UnicodeText, Date, Time, DateTime, Numeric,\
#                    Enum, Boolean, String, Text, PickleType, ManyToOne, OneToMany
# from elixir import using_options, using_table_options

# from nobix.schema import documentos, tasas, items_documento
# from nobix.schema import clientes, articulos, cache_table
from nobix.config import get_current_config
from nobix.exc import NobixModelError, NobixPrintError

# from nobix.db import metadata, Numeric

# __all__ = ('Documento', 'ItemDocumento', 'Cliente', 'Articulo', 'NobixModelError')

#  Mantener sincronizada con la version del repositorio dbmigrate
SCHEMA_VERSION = '3'

# class Model(EntityBase, metaclass=EntityMeta):
#     def __repr__(self):
#         return "<%s %s>" % (type(self).__name__, ', '.join('%s=%s' %\
#                 (k.name, repr(getattr(self, k.name))) for k in self.table.columns))




# 
#  Not Mapped as object
# 

REPO_PATH = "dbmigrate"
REPO_ID = "Nobix Data Evolution"

migrate_version = db.Table('migrate_version', db.metadata,
    db.Column('repository_id', db.String(250), primary_key=True),
    db.Column('repository_path', db.Text),
    db.Column('version', db.Integer),
)

def check_migration_table(bind):

    if not migrate_version.exists(bind=bind):
        migrate_version.create(bind=bind)
        bind.execute(migrate_version.insert(),
                     repository_id=REPO_ID,
                     repository_path=REPO_PATH,
                     version=SCHEMA_VERSION)

# # Original classes

# class Model(object):
#     # adapted form http://www.sqlalchemy.org/trac/wiki/UsageRecipes/GenericOrmBaseClass
# 
#     def __init__(self, **kw):
#         _mapper = object_mapper(self)
#         for key in kw:
#             if _mapper.has_property(key): #key in _mapper.c:
#                 setattr(self, key, kw[key])
#             else:
#                 raise AttributeError("Cannot set attribute which is " +
#                                      "not column in mapped table: %s" % (key,))
# 
#     def __repr__(self):
#         _mapper = object_mapper(self)
#         attrs = []
#         for key in _mapper.c.keys():
#             if key in self.__dict__:
#                 if not (hasattr(_mapper.c.get(key).default, 'arg') and
#                         getattr(_mapper.c.get(key).default, 'arg') == getattr(self, key)):
#                     attrs.append((key, getattr(self, key)))
#         return "%s(%s)" % (type(self).__name__, ', '.join('%s=%s' % (x[0], repr(x[1])) for x in attrs))
# 
# class Documento(db.Model):
# 
#     def _get_tipo(self):
#         return self._tipo
#     def _set_tipo(self, val):
#         if val not in get_current_config().documentos.keys():
#             raise NobixModelError(u"'%s' no es un tipo de documento valido" % val)
#         self._tipo = val
#     tipo = property(_get_tipo, _set_tipo)
# 
#     @property
#     def total(self):
#         return Decimal(self.neto if self.neto is not None else 0) + Decimal(sum(t.monto for t in self.tasas))
# 
# class PeriodoIVA(db.Model):
#     pass
# 
# class Tasa(db.Model):
#     pass
# 
# class ItemDocumento(db.Model):
#     pass
# 
# class Cliente(db.Model):
# 
#     @property
#     def direccion(self):
#         dir_data = self.domicilio, self.localidad
#         if all(dir_data):
#             d = " - ".join(dir_data)
#         else:
#             d = "".join(dir_data)
#         if self.codigo_postal:
#             d += " (%s)" % self.codigo_postal
#         return d
# 
# class Articulo(db.Model):
#     pass
# 
# class Cache(db.Model):
#     pass
# 
# # Mapper configuration
# mapper(Documento, documentos, properties={
#     'cliente': relation(Cliente, backref="documentos"),
#     'tipo': synonym("_tipo", map_column=True),
#     'tasas': relation(Tasa, backref="documento", cascade="delete,delete-orphan"),
# })
# mapper(Tasa, tasas)
# mapper(ItemDocumento, items_documento, properties={
#     'documento': relation(Documento, backref="items"),
#     'articulo': relation(Articulo, backref="doc_items"),
# })
# mapper(Cliente, clientes)
# mapper(Articulo, articulos)
# mapper(Cache, cache_table, properties={
#     'cliente': relation(Cliente),
# })
