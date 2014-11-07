# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

from nobix.exc import NobixModelError
from nobix.config import get_current_config
from nobix.saw import SQLAlchemy


db = SQLAlchemy()

def time_now():
    return datetime.now().time()


class Documento(db.Model):
    __tablename__ = 'documentos'
    __table_args__ = (db.UniqueConstraint('tipo', 'fecha', 'numero'),)

    id = db.Column(db.Integer, primary_key=True)
    _tipo = db.Column('tipo', db.Unicode(3), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, default=time_now)
    numero = db.Column(db.Integer)
    vendedor = db.Column(db.UnicodeText)
    descuento = db.Column(db.Numeric(10, 2), default=Decimal(0))
    neto = db.Column(db.Numeric(10, 2), nullable=False)
    fiscal = db.Column(db.UnicodeText, default=None)
    periodo_iva = db.Column(db.Date, nullable=True, default=None)

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'),
                           nullable=False, index=True)
    cliente = db.relationship('Cliente', backref="documentos")

    # Info extra documento
    cliente_nombre = db.Column(db.UnicodeText)
    cliente_direccion = db.Column(db.UnicodeText)
    cliente_cuit = db.Column(db.UnicodeText, nullable=True)

    # tasas field added by Tasa model
    # items field added by ItemDocumento model

    @property
    def tipo(self):
        return self._tipo

    @tipo.setter
    def tipo(self, value):
        if value not in get_current_config().documentos.keys():
            raise NobixModelError(u"'%s' no es un tipo de documento válido" % value)
        self._tipo = value

    @property
    def total(self):
        return Decimal(self.neto if self.neto is not None else 0) +\
               Decimal(sum(t.monto for t in self.tasas))


class ItemDocumento(db.Model):
    __tablename__ = 'items_documento'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.UnicodeText)
    descripcion = db.Column(db.UnicodeText, nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    articulo_id = db.Column(db.Integer, db.ForeignKey('articulos.id'),
                            index=True)
    articulo = db.relationship('Articulo', backref="doc_items")

    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'),
                             nullable=False, index=True)
    documento = db.relationship(Documento, backref="items")


class Tasa(db.Model):
    __tablename__ = 'tasas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.UnicodeText, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)

    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'),
                             nullable=False, index=True)
    documento = db.relationship(Documento, backref="tasas")


class Cliente(db.Model):
    __tablename__ = 'clientes'
    __table_args__ = (db.UniqueConstraint('codigo', 'relacion'),)

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Integer)
    nombre = db.Column(db.UnicodeText, nullable=False)
    domicilio = db.Column(db.UnicodeText)
    localidad = db.Column(db.UnicodeText)
    codigo_postal = db.Column(db.UnicodeText)
    responsabilidad_iva = db.Column(db.Enum(u'C', u'I', u'R', u'M', u'E', name='respiva_enum'),
                                    default=u'C')
    cuit = db.Column(db.UnicodeText)
    relacion = db.Column(db.Enum(u'C', u'P', name="rel_enum"), default=u'C')

    # documentos field added by Documento model

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

    #: the product is available and can be used on a |purchase|/|sale|
    STATUS_AVAILABLE = u'STATUS_AVAILABLE'

    #: the product is closed, that is, it sill eixsts for references, but it
    #: should not be possible to create |purchase|/|sale| with it
    STATUS_CLOSED = u'STATUS_CLOSED'

    #: the product is suspended, that is, it sill exists for future references
    #: but it should not be possible to create a |purchase|/|sale| with it
    #: until back to available status.
    STATUS_SUSPENDED = u'STATUS_SUSPENDED'

    _statuses = {
        STATUS_AVAILABLE: u'Disponible',
        STATUS_CLOSED: u'Cerrado',
        STATUS_SUSPENDED: u'Suspendido',
    }

    TYPE_PERMANENT = u'TYPE_PERMANENT'
    TYPE_ON_REQUEST = u'TYPE_ON_REQUEST'
    TYPE_CONSIGMENT = u'TYPE_CONSIGMENT'

    _product_types = {
        TYPE_PERMANENT: u'Permanente',
        TYPE_ON_REQUEST: u'Bajo Pedido',
        TYPE_CONSIGMENT: u'Consignación',
    }

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Unicode(14), nullable=False, unique=True)
    descripcion = db.Column(db.UnicodeText, nullable=False)
    proveedor = db.Column(db.UnicodeText)
    agrupacion = db.Column(db.UnicodeText)
    vigencia = db.Column(db.DateTime)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    tax_code = db.Column(db.Unicode(3), nullable=False)
    status = db.Column(db.UnicodeText, nullable=False)
    product_type = db.Column(db.UnicodeText, nullable=False)

    existencia = db.Column(db.Numeric(10, 2), default=Decimal(0))
    es_activo = db.Column(db.Boolean, default=True)

    # doc_items field added by ItemDocumento model

    @db.validates('status')
    def validate_status(self, key, status):
        assert status in self._statuses.keys()
        return status

    @db.validates('product_type')
    def validate_product_type(self, key, product_type):
        assert product_type in self._product_types.keys()
        return product_type

    @property
    def status_str(self):
        return self._statuses.get(self.status)

    @property
    def product_type_str(self):
        return self._product_types.get(self.product_type)


class Cache(db.Model):
    __tablename__ = 'cache'
    __table_args__ = (db.UniqueConstraint('vendedor', 'username', 'hostname'),)

    id = db.Column(db.Integer, primary_key=True)
    vendedor = db.Column(db.Unicode(3), nullable=False)
    username = db.Column(db.Unicode(64), nullable=False)
    hostname = db.Column(db.Unicode(64), nullable=False)
    doctype = db.Column(db.UnicodeText)
    descuento = db.Column(db.Numeric(10, 2), default=Decimal(0))
    total = db.Column(db.Numeric(10, 2), default=Decimal(0))

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'),
                           index=True)
    cliente = db.relationship(Cliente)

    modified = db.Column(db.DateTime, nullable=False, default=datetime.now,
                         onupdate=datetime.now)
    items = db.Column(db.PickleType, default=None)
