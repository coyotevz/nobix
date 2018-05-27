# -*- coding: utf-8 -*-

from decimal import Decimal
from nobix.config import get_current_config
from nobix.exc import NobixModelError
from . import db, time_now


class Documento(db.Model):
    __tablename__ = 'documentos'
    __table_args__ = (
        db.UniqueConstraint('doc_type', 'issue_date', 'number'),
    )

    id = db.Column(db.Integer, primary_key=True)
    _tipo = db.Column('doc_type', db.Unicode(3), nullable=False)
    fecha = db.Column('issue_date', db.Date, nullable=False)
    hora = db.Column('issue_time', db.Time, default=time_now)
    numero = db.Column('number', db.Integer)
    vendedor = db.Column('salesman', db.UnicodeText(3))
    # Descuento neto (sin impuestos)
    descuento = db.Column('discount', db.Numeric(10, 2), default=Decimal)
    # Subtotal - Descuento = Neto
    # Neto + Impuestos = Total
    neto = db.Column('net', db.Numeric(10, 2), nullable=False)
    fiscal = db.Column('fiscal', db.UnicodeText(10), default=None)
    periodo_iva = db.Column('fiscal_period', db.Date, nullable=True, default=None)

    cliente_id = db.Column('customer_id', db.Integer, db.ForeignKey('clientes.id'),
                           index=True, nullable=False)
    cliente = db.relationship('Cliente', backref='documentos')

    # Info extra documento
    cliente_nombre = db.Column('customer_name', db.UnicodeText(35))
    # domicilio + localidad + cp
    cliente_direccion = db.Column('customer_address', db.UnicodeText(60))
    # cuit si corresponde
    cliente_cuit = db.Column('customer_cuit', db.UnicodeText(13), nullable=True)

    #: 'tasas' field add by Tasa model
    #: 'items' field add by ItemDocumento model

    def _get_tipo(self):
        return self._tipo

    def _set_tipo(self, val):
        if val not in list(get_current_config().documentos.keys()):
            raise NobixModelError("'%s' no es un tipo de documento valido"
                                  % val)
        self._tipo = val

    tipo = property(_get_tipo, _set_tipo)

    @property
    def total(self):
        return Decimal(self.neto if self.neto is not None else 0) + \
                Decimal(sum(t.monto for t in self.tasas))
