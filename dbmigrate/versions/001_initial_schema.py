from sqlalchemy import *
from migrate import *

from decimal import Decimal

meta = MetaData()

documentos = Table('documentos', meta,
    Column('id', Integer, primary_key=True),
    Column('tipo', Unicode(3), nullable=False),
    Column('fecha', Date, nullable=False),
    Column('hora', Time),
    Column('numero', Integer),
    Column('vendedor', UnicodeText(3)),
    Column('descuento', Numeric(10, 2), default=Decimal()),
    Column('neto', Numeric(10, 2), nullable=False),
    Column('fiscal', UnicodeText(10), default=False),
    Column('periodo_iva', Date, nullable=False, default=None),
    Column('cliente_id', Integer, ForeignKey('clientes.id'), nullable=True),
    Column('cliente_nombre', UnicodeText(35)),
    Column('cliente_direccion', UnicodeText(60)),
    Column('cliente_cuit', UnicodeText(13), nullable=True),
    UniqueConstraint('tipo', 'fecha', 'numero'),
)

tasas = Table('tasas', meta,
    Column('id', Integer, primary_key=True),
    Column('nombre', UnicodeText(3), nullable=False),
    Column('monto', Numeric(10, 2), nullable=False),
    Column('documento_id', Integer, ForeignKey('documentos.id'), nullable=True),
)

items_documento = Table('items_documento', meta,
    Column('id', Integer, primary_key=True),
    Column('codigo', UnicodeText(14)),
    Column('descripcion', UnicodeText(40), nullable=False),
    Column('cantidad', Numeric(10, 2), nullable=False),
    Column('precio', Numeric(10, 2), nullable=False),
    Column('articulo_id', Integer, ForeignKey('articulos.id')),
    Column('documento_id', Integer, ForeignKey('documentos.id'), nullable=False),
)

clientes = Table('clientes', meta,
    Column('id', Integer, primary_key=True),
    Column('codigo', Integer),
    Column('nombre', UnicodeText(35), nullable=False),
    Column('domicilio', UnicodeText(35)),
    Column('localidad', UnicodeText(20)),
    Column('codigo_postal', UnicodeText(8)),
    Column('responsabilidad_iva', Enum(u'C', u'I', u'R', u'M', u'E', name="respiva_enum"), default=u"C"),
    Column('cuit', UnicodeText(13)),
    Column('relacion', Enum(u'C', u'P', name="rel_enum"), default=u"C"),
    UniqueConstraint('codigo', 'relacion'),
)

articulos = Table('articulos', meta,
    Column('id', Integer, primary_key=True),
    Column('codigo', Unicode(14), nullable=False, unique=True),
    Column('descripcion', UnicodeText(40), nullable=False),
    Column('proveedor', UnicodeText(20)),
    Column('agrupacion', UnicodeText(20)),
    Column('vigencia', DateTime),
    Column('precio', Numeric(10, 2), nullable=False),
    Column('existencia', Numeric(10, 2), default=Decimal()),
    Column('es_activo', Boolean, default=True),
)

cache_table = Table('cache', meta,
    Column('id', Integer, primary_key=True),
    Column('vendedor', Unicode(3), nullable=False),
    Column('username', Unicode(64), nullable=False),
    Column('hostname', Unicode(64), nullable=False),
    Column('doctype', UnicodeText(3)),
    Column('descuento', Numeric(10, 2)),
    Column('total', Numeric(10, 2)),
    Column('cliente_id', Integer, ForeignKey('clientes.id')),
    Column('modified', DateTime, nullable=False),
    Column('items', PickleType, default=None),
    UniqueConstraint('vendedor', 'username', 'hostname'),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    meta.bind = migrate_engine

    for table in meta.sorted_tables:
        table.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine

    for table in reversed(meta.sorted_tables):
        table.drop()
