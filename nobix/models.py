#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import mapper, relation, synonym, object_mapper, backref, object_session
from sqlalchemy.sql import select, func
from sqlalchemy import UniqueConstraint, Table, Column

import elixir
elixir.options_defaults['mapper_options'] = {'save_on_init': False}

from elixir import EntityBase, EntityMeta, ColumnProperty
from elixir import Field, Integer, Unicode, UnicodeText, Date, Time, DateTime, Numeric,\
                   Enum, Boolean, String, Text, PickleType, ManyToOne, OneToMany
from elixir import using_options, using_table_options

#from nobix.schema import documentos, tasas, items_documento
#from nobix.schema import clientes, articulos, cache_table
from nobix.config import get_current_config
from nobix.exc import NobixModelError, NobixPrintError

from nobix.db import metadata, Numeric

__all__ = ('Documento', 'ItemDocumento', 'Cliente', 'Articulo', 'NobixModelError')

# Mantener sincronizada con la version del repositorio dbmigrate
SCHEMA_VERSION = '3'

def time_now():
    return datetime.now().time()

class Model(EntityBase):
    __metaclass__ = EntityMeta

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, ', '.join('%s=%s' %\
                (k.name, repr(getattr(self, k.name))) for k in self.table.columns))

class Documento(Model):
    using_options(tablename='documentos')

    id = Field(Integer, primary_key=True)
    _tipo = Field(Unicode(3), colname='tipo', synonym='tipo', required=True)
    fecha = Field(Date, required=True)
    hora = Field(Time, default=time_now)
    numero = Field(Integer)
    vendedor = Field(UnicodeText(3))
    # Descuento neto (sin impuestos)
    descuento = Field(Numeric(10, 2), default=Decimal)
    # Subtotal - Descuento = Neto
    # Neto + Impuestos = Total
    neto = Field(Numeric(10, 2), required=True)
    fiscal = Field(UnicodeText(10), default=None)
    periodo_iva = Field(Date, required=False, default=None)
    cliente = ManyToOne('Cliente', required=True)

    # Info extra documento
    cliente_nombre = Field(UnicodeText(35))
    cliente_direccion = Field(UnicodeText(60)) # domicilio + localidad + cp
    cliente_cuit = Field(UnicodeText(13), required=False) # cuit si corresponde

    tasas = OneToMany('Tasa', cascade="delete,delete-orphan")
    items = OneToMany('ItemDocumento')

    using_table_options(UniqueConstraint('tipo', 'fecha', 'numero'))

    def _get_tipo(self):
        return self._tipo
    def _set_tipo(self, val):
        if val not in get_current_config().documentos.keys():
            raise NobixModelError(u"'%s' no es un tipo de documento valido" % val)
        self._tipo = val
    tipo = property(_get_tipo, _set_tipo)

    @property
    def total(self):
        return Decimal(self.neto if self.neto is not None else 0) + Decimal(sum(t.monto for t in self.tasas))

class Tasa(Model):
    using_options(tablename='tasas')

    id = Field(Integer, primary_key=True)
    nombre = Field(UnicodeText(3), required=True)
    monto = Field(Numeric(10, 2), required=True)

    documento = ManyToOne('Documento', required=True)

class ItemDocumento(Model):
    using_options(tablename='items_documento')

    id = Field(Integer, primary_key=True)
    codigo = Field(UnicodeText(14))
    descripcion = Field(UnicodeText(40), required=True)
    cantidad = Field(Numeric(10, 2), required=True)
    precio = Field(Numeric(10, 2), required=True)

    articulo = ManyToOne('Articulo')
    documento = ManyToOne('Documento', required=True)

class Cliente(Model):
    using_options(tablename='clientes')

    id = Field(Integer, primary_key=True)
    codigo = Field(Integer)
    nombre = Field(UnicodeText(35), required=True)
    domicilio = Field(UnicodeText(35))
    localidad = Field(UnicodeText(20))
    codigo_postal = Field(UnicodeText(8))
    responsabilidad_iva = Field(Enum(u'C', u'I', u'R', u'M', u'E', name="respiva_enum"), default=u"C")
    cuit = Field(UnicodeText(13))
    relacion = Field(Enum(u'C', u'P', name="rel_enum"), default=u"C")

    documentos = OneToMany('Documento')

    using_table_options(UniqueConstraint('codigo', 'relacion'))

    @property
    def direccion(self):
        dir_data = self.domicilio, self.localidad
        if all(dir_data):
            d = " - ".join(dir_data)
        else:
            d = "".join(dir_data)
        if self.codigo_postal:
            d += " (%s)" % self.codigo_postal
        return d

class Articulo(Model):
    using_options(tablename='articulos')

    id = Field(Integer, primary_key=True)
    codigo = Field(Unicode(14), required=True, unique=True)
    descripcion = Field(UnicodeText(40), required=True)
    proveedor = Field(UnicodeText(20))
    agrupacion = Field(UnicodeText(20))
    vigencia = Field(DateTime)
    precio = Field(Numeric(10, 2), required=True)
    existencia = Field(Numeric(10, 2), default=Decimal)
    es_activo = Field(Boolean, default=True)

    doc_items = OneToMany('ItemDocumento')

    @property
    def existencia_new(self):
        sal = [k for k, v in get_current_config().documentos.iteritems() if v['stock'] == u'salida']
        ent = [k for k, v in get_current_config().documentos.iteritems() if v['stock'] in (u'entrada', u'ajuste')]
        sess = object_session(self)
        q = sess.query(func.sum(ItemDocumento.cantidad)).filter(ItemDocumento.articulo==self)
        s = q.filter(ItemDocumento.documento.has(Documento.tipo.in_(sal))).scalar() or Decimal()
        e = q.filter(ItemDocumento.documento.has(Documento.tipo.in_(ent))).scalar() or Decimal()
        return e - s

class Cache(Model):
    using_options(tablename='cache')

    id = Field(Integer, primary_key=True)
    vendedor = Field(Unicode(3), required=True)
    username = Field(Unicode(64), required=True)
    hostname = Field(Unicode(64), required=True)
    doctype = Field(UnicodeText(3))
    descuento = Field(Numeric(10, 2), default=0)
    total = Field(Numeric(10, 2), default=0)
    cliente = ManyToOne('Cliente')
    modified = Field(DateTime, required=True, default=datetime.now, onupdate=datetime.now)
    items = Field(PickleType, default=None)

    using_table_options(UniqueConstraint('vendedor', 'username', 'hostname'))


#
# Not Mapped as object
#

REPO_PATH = "dbmigrate"
REPO_ID = "Nobix Data Evolution"

migrate_version = Table('migrate_version', metadata,
    Column('repository_id', String(250), primary_key=True),
    Column('repository_path', Text),
    Column('version', Integer),
)

def check_migration_table(bind):

    if not migrate_version.exists(bind=bind):
        migrate_version.create(bind=bind)
        bind.execute(migrate_version.insert(),
                     repository_id=REPO_ID,
                     repository_path=REPO_PATH,
                     version=SCHEMA_VERSION)

## Original classes

#class Model(object):
#    # adapted form http://www.sqlalchemy.org/trac/wiki/UsageRecipes/GenericOrmBaseClass
#
#    def __init__(self, **kw):
#        _mapper = object_mapper(self)
#        for key in kw:
#            if _mapper.has_property(key): #key in _mapper.c:
#                setattr(self, key, kw[key])
#            else:
#                raise AttributeError("Cannot set attribute which is " +
#                                     "not column in mapped table: %s" % (key,))
#
#    def __repr__(self):
#        _mapper = object_mapper(self)
#        attrs = []
#        for key in _mapper.c.keys():
#            if key in self.__dict__:
#                if not (hasattr(_mapper.c.get(key).default, 'arg') and
#                        getattr(_mapper.c.get(key).default, 'arg') == getattr(self, key)):
#                    attrs.append((key, getattr(self, key)))
#        return "%s(%s)" % (type(self).__name__, ', '.join('%s=%s' % (x[0], repr(x[1])) for x in attrs))
#
#class Documento(Model):
#
#    def _get_tipo(self):
#        return self._tipo
#    def _set_tipo(self, val):
#        if val not in get_current_config().documentos.keys():
#            raise NobixModelError(u"'%s' no es un tipo de documento valido" % val)
#        self._tipo = val
#    tipo = property(_get_tipo, _set_tipo)
#
#    @property
#    def total(self):
#        return Decimal(self.neto if self.neto is not None else 0) + Decimal(sum(t.monto for t in self.tasas))
#
#class PeriodoIVA(Model):
#    pass
#
#class Tasa(Model):
#    pass
#
#class ItemDocumento(Model):
#    pass
#
#class Cliente(Model):
#
#    @property
#    def direccion(self):
#        dir_data = self.domicilio, self.localidad
#        if all(dir_data):
#            d = " - ".join(dir_data)
#        else:
#            d = "".join(dir_data)
#        if self.codigo_postal:
#            d += " (%s)" % self.codigo_postal
#        return d
#
#class Articulo(Model):
#    pass
#
#class Cache(Model):
#    pass
#
## Mapper configuration
#mapper(Documento, documentos, properties={
#    'cliente': relation(Cliente, backref="documentos"),
#    'tipo': synonym("_tipo", map_column=True),
#    'tasas': relation(Tasa, backref="documento", cascade="delete,delete-orphan"),
#})
#mapper(Tasa, tasas)
#mapper(ItemDocumento, items_documento, properties={
#    'documento': relation(Documento, backref="items"),
#    'articulo': relation(Articulo, backref="doc_items"),
#})
#mapper(Cliente, clientes)
#mapper(Articulo, articulos)
#mapper(Cache, cache_table, properties={
#    'cliente': relation(Cliente),
#})
