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
    vendedor = db.Column(db.UnicodeText(3))
    descuento = db.Column(db.Numeric(10, 2), default=Decimal(0))
    neto = db.Column(db.Numeric(10, 2), nullable=False)
    fiscal = db.Column(db.UnicodeText(10), default=None)
    periodo_iva = db.Column(db.Date, nullable=True, default=None)

    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    cliente = db.relationship('Cliente', backref="documentos")

    # Info extra documento
    cliente_nombre = db.Column(db.UnicodeText(35))
    cliente_direccion = db.Column(db.UnicodeText(60))
    cliente_cuit = db.Column(db.UnicodeText(13), nullable=True)

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
    codigo = db.Column(db.UnicodeText(14))
    descripcion = db.Column(db.UnicodeText(40), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    articulo_id = db.Column(db.Integer, db.ForeignKey('articulo.id'))
    articulo = db.relationship('Articulo', backref="doc_items")

    documento_id = db.Column(db.Integer, db.ForeignKey('documento.id'), nullable=False)
    documento = db.relationship(Documento, backref="items")


class Tasa(db.Model):
    __tablename__ = 'tasas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.UnicodeText(3), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)

    documento_id = db.Column(db.Integer, db.ForeignKey('documento.id'), nullable=False)
    documento = db.relationship(Documento, backref="tasas")


class Cliente(db.Model):
    __tablename__ = 'clientes'
    __table_args__ = (db.UniqueConstraint('codigo', 'relacion'),)

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Integer)
    nombre = db.Column(db.UnicodeText(35), nullable=False)
    domicilio = db.Column(db.UnicodeText(35))
    localidad = db.Column(db.UnicodeText(20))
    codigo_postal = db.Column(db.UnicodeText(8))
    responsabilidad_iva = db.Column(db.Enum(u'C', u'I', u'R', u'M', u'E', name='respiva_enum'),
                                    default=u'C')
    cuit = db.Column(db.UnicodeText(13))
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

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Unicode(14), nullable=False, unique=True)
    descripcion = db.Column(db.UnicodeText(40), nullable=False)
    proveedor = db.Column(db.UnicodeText(20))
    agrupacion = db.Column(db.UnicodeText(20))
    vigencia = db.Column(db.DateTime)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    existencia = db.Column(Numeric(10, 2), default=Decimal(0))
    es_activo = db.Column(db.Boolean, default=True)

    # doc_items field added by ItemDocumento model


class Cache(db.Model):
    __tablename__ = 'cache'
    __table_args__ = (UniqueConstraint('vendedor', 'username', 'hostname'),)

    id = db.Column(db.Integer, primary_key=True)
    vendedor = db.Column(db.Unicode(3), nullable=False)
    username = db.Column(db.Unicode(64), nullable=False)
    hostname = db.Column(db.Unicode(64), nullable=False)
    doctype = db.Column(db.UnicodeText(3))
    descuento = db.Column(db.Numeric(10, 2), default=Decimal(0))
    total = db.Column(db.Numeric(10, 2), default=Decimal(0))

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    cliente = db.relationship(Cliente)

    modified = db.Column(db.DateTime, nullable=False, default=datetime.now,
                         onupdate=datetime.now)
    items = db.Column(db.PickleType, default=None)
