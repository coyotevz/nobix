#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Table, Column, Integer, Date, Time, DateTime, MetaData,\
                       ForeignKey, Boolean, Enum, UniqueConstraint,\
                       PickleType, UnicodeText, Unicode, String, Text
from sqlalchemy import types
from nobix.db import metadata, Numeric

# Mantener sincronizada con la version del repositorio dbmigrate
SCHEMA_VERSION = '2'

def time_now():
    return datetime.now().time()

documentos = Table('documentos', metadata,
    Column('id', Integer, primary_key=True),
    Column('tipo', Unicode(3), nullable=False), # FAA, FAC, VFA, VNC, REM, PRE, ENT, SAL, AJU, INV
    Column('fecha', Date, nullable=False),
    Column('hora', Time, default=time_now),
    Column('numero', Integer),
    Column('vendedor', UnicodeText(3)),
    # Descuento neto (sin impuestos)
    Column('descuento', Numeric(10, 2), default=Decimal('0')),
    # Subtotal - Descuento = Neto
    # Neto + Impuestos = Total
    Column('neto', Numeric(10, 2), nullable=False),
    Column('fiscal', UnicodeText(10), default=None),
    # Algunos documentos que participan en el Libro IVA (documentos.fiscal!=None)
    # pertenecen a periodos distintos a los que podriamos inferir por su fecha,
    Column('periodo_iva', Date, nullable=True, default=None),
    Column('cliente_id', Integer, ForeignKey('clientes.id'), nullable=True, index=True),

    # Info extra por documento
    Column('cliente_nombre', UnicodeText(35)),
    Column('cliente_direccion', UnicodeText(60)), # domicilio + localidad + cp
    Column('cliente_cuit', UnicodeText(13), nullable=True), # cuit si corresponde

    UniqueConstraint('tipo', 'fecha', 'numero'),
)

# Tabla de impuestos asociados a documentos (documentos *<-->1 tasa)
# Se almacena el monto en pesos y el nombre del impuesto (C21)
tasas = Table('tasas', metadata,
    Column('id', Integer, primary_key=True),
    Column('nombre', UnicodeText(3), nullable=False),
    Column('monto', Numeric(10, 2), nullable=False),
    Column('documento_id', Integer, ForeignKey('documentos.id'), nullable=True, index=True),
)

items_documento = Table('items_documento', metadata,
    Column('id', Integer, primary_key=True),
    Column('codigo', UnicodeText(14)),
    Column('descripcion', UnicodeText(40), nullable=False),
    Column('cantidad', Numeric(10, 2), nullable=False),
    Column('precio', Numeric(10, 2), nullable=False),
    Column('articulo_id', Integer, ForeignKey('articulos.id'), index=True),
    Column('documento_id', Integer, ForeignKey('documentos.id'), nullable=False, index=True),
)

clientes = Table('clientes', metadata,
    Column('id', Integer, primary_key=True),
    Column('codigo', Integer),
    Column('nombre', UnicodeText(35), nullable=False),
    Column('domicilio', UnicodeText(35)),
    Column('localidad', UnicodeText(20)),
    Column('codigo_postal', UnicodeText(8)),
    Column('responsabilidad_iva', Enum(u'C', u'I', u'R', u'M', u'E', name="respiva_enum"), default=u"C"),
    Column('cuit', UnicodeText(13)),
    # Puede ser cliente o proveedor
    Column('relacion', Enum(u'C', u'P', name="rel_enum"), default=u"C"),

    UniqueConstraint('codigo', 'relacion'),
)

articulos = Table('articulos', metadata,
    Column('id', Integer, primary_key=True),
    Column('codigo', Unicode(14), nullable=False, unique=True),
    Column('descripcion', UnicodeText(40), nullable=False),
    Column('proveedor', UnicodeText(20)),
    Column('agrupacion', UnicodeText(20)),
    Column('vigencia', DateTime),
    Column('precio', Numeric(10, 2), nullable=False),
    Column('existencia', Numeric(10, 2), default=Decimal('0')),
    Column('es_activo', Boolean, default=True),
)

cache_table = Table('cache', metadata,
    Column('id', Integer, primary_key=True),
    Column('vendedor', Unicode(3), nullable=False),
    Column('username', Unicode(64), nullable=False),
    Column('hostname', Unicode(64), nullable=False),
    Column('doctype', UnicodeText(3)),
    Column('descuento', Numeric(10, 2)),
    Column('total', Numeric(10, 2)),
    Column('cliente_id', Integer, ForeignKey('clientes.id'), index=True),
    Column('modified', DateTime, nullable=False,
           default=datetime.now, onupdate=datetime.now),
    Column('items', PickleType, default=None),

    UniqueConstraint('vendedor', 'username', 'hostname'),
)

# sqlalchemy-migration tools
# Se define SCHEMA_VERSION al principio del archivo
REPO_PATH = "dbmigrate"
REPO_ID = "Nobix Data Evolution"

#migrate_version = Table('migrate_version', metadata,
#    Column('repository_id', String(250), primary_key=True),
#    Column('repository_path', Text),
#    Column('version', Integer),
#)

def check_migration_table(bind):

    if not migrate_version.exists(bind=bind):
        migrate_version.create(bind=bind)
        bind.execute(migrate_version.insert(),
                     repository_id=REPO_ID,
                     repository_path=REPO_PATH,
                     version=SCHEMA_VERSION)
