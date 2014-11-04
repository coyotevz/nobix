# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

from nobix.models.saw import SQLAlchemy

db = SQLAlchemy()


def time_now():
    return datetime.now().time()

class Documento(db.Model):
    __tablename__ = 'documentos'

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
    cliente = db.relationship('Cliente')

    # Info extra documento
    cliente_nombre = db.Column(db.UnicodeText(35))
    cliente_direccion = db.Column(db.UnicodeText(60))
    cliente_cuit = db.Column(db.UnicodeText(13), nullable=True)
