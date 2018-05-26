# !/usr/bin/env python
#  -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

from nobix.lib.saw import SQLAlchemy

db = SQLAlchemy()

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

def time_now():
    return datetime.now().time()

# class Model(EntityBase, metaclass=EntityMeta):
#     def __repr__(self):
#         return "<%s %s>" % (type(self).__name__, ', '.join('%s=%s' %\
#                 (k.name, repr(getattr(self, k.name))) for k in self.table.columns))

class Documento(db.Model):
    __tablename__ = 'documentos'
    __table_args__ = (db.UniqueConstraint('tipo', 'fecha', 'numero'),)

    id = db.Column(db.Integer, primary_key=True)
    _tipo = db.Column('tipo', db.Unicode(3), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, default=time_now)
    numero = db.Column(db.Integer)
    vendedor = db.Column(db.UnicodeText(3))
    # Descuento neto (sin impuestos)
    descuento = db.Column(db.Numeric(10, 2), default=Decimal)
    # Subtotal - Descuento = Neto
    # Neto + Impuestos = Total
    neto = db.Column(db.Numeric(10, 2), nullable=False)
    fiscal = db.Column(db.UnicodeText(10), default=None)
    periodo_iva = db.Column(db.Date, nullable=True, default=None)

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), index=True, nullable=False)
    cliente = db.relationship('Cliente', backref='documentos')

    # Info extra documento
    cliente_nombre = db.Column(db.UnicodeText(35))
    cliente_direccion = db.Column(db.UnicodeText(60)) # domicilio + localidad + cp
    cliente_cuit = db.Column(db.UnicodeText(13), nullable=True) # cuit si corresponde

    #: 'tasas' field add by Tasa model
    #: 'items' field add by ItemDocumento model

    def _get_tipo(self):
        return self._tipo

    def _set_tipo(self, val):
        if val not in list(get_current_config().documentos.keys()):
            raise NobixModelError("'%s' no es un tipo de documento valido" % val)
        self._tipo = val

    tipo = property(_get_tipo, _set_tipo)

    @property
    def total(self):
        return Decimal(self.neto if self.neto is not None else 0) + Decimal(sum(t.monto for t in self.tasas))

class Tasa(db.Model):
    __tablename__ = 'tasas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.UnicodeText(3), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)

    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'), index=True, nullable=False)
    documento = db.relationship('Documento', backref=db.backref('tasas', cascade="delete,delete-orphan"))

class ItemDocumento(db.Model):
    __tablename__ = 'items_documento'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.UnicodeText(14))
    descripcion = db.Column(db.UnicodeText(40), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    articulo_id = db.Column(db.Integer, db.ForeignKey('articulos.id'), index=True)
    articulo = db.relationship('Articulo', backref='doc_items')

    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'), index=True, nullable=False)
    documento = db.relationship('Documento', backref='items')

class Cliente(db.Model):
    __tablename__ = 'clientes'
    __table_args__ = (db.UniqueConstraint('codigo', 'relacion'),)

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Integer)
    nombre = db.Column(db.UnicodeText(35), nullable=False)
    domicilio = db.Column(db.UnicodeText(35))
    localidad = db.Column(db.UnicodeText(20))
    codigo_postal = db.Column(db.UnicodeText(8))
    responsabilidad_iva = db.Column(db.Enum('C', 'I', 'R', 'M', 'E', name="respiva_enum"), default="C")
    cuit = db.Column(db.UnicodeText(13))
    relacion = db.Column(db.Enum('C', 'P', name="rel_enum"), default="C")

    #: 'documentos' field added by Documento model

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

class Articulo(db.Model):
    __tablename__ = 'articulos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Unicode(14), nullable=False, unique=True)
    descripcion = db.Column(db.UnicodeText(40), nullable=False)
    proveedor = db.Column(db.UnicodeText(20))
    agrupacion = db.Column(db.UnicodeText(20))
    vigencia = db.Column(db.DateTime)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    existencia = db.Column(db.Numeric(10, 2), default=Decimal)
    es_activo = db.Column(db.Boolean, default=True)

    #: 'doc_items' field added by ItemDocumento model

    @property
    def existencia_new(self):
        sal = [k for k, v in get_current_config().documentos.items() if v['stock'] == 'salida']
        ent = [k for k, v in get_current_config().documentos.items() if v['stock'] in ('entrada', 'ajuste')]
        sess = object_session(self)
        q = sess.query(func.sum(ItemDocumento.cantidad)).filter(ItemDocumento.articulo==self)
        s = q.filter(ItemDocumento.documento.has(Documento.tipo.in_(sal))).scalar() or Decimal()
        e = q.filter(ItemDocumento.documento.has(Documento.tipo.in_(ent))).scalar() or Decimal()
        return e - s

class Cache(db.Model):
    __tablename__ = 'cache'
    __table_args__ = (db.UniqueConstraint('vendedor', 'username', 'hostname'),)

    id = db.Column(db.Integer, primary_key=True)
    vendedor = db.Column(db.Unicode(3), nullable=False)
    username = db.Column(db.Unicode(64), nullable=False)
    hostname = db.Column(db.Unicode(64), nullable=False)
    doctype = db.Column(db.UnicodeText(3))
    descuento = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), index=True)
    cliente = db.relationship('Cliente', lazy='joined')
    modified = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    items = db.Column(db.PickleType, default=None)


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
