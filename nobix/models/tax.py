# -*- coding: utf-8 -*-

from . import db


class Tasa(db.Model):
    __tablename__ = 'tax'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column('name', db.UnicodeText(3), nullable=False)
    monto = db.Column('amount', db.Numeric(10, 2), nullable=False)

    documento_id = db.Column('document_id', db.Integer,
                             db.ForeignKey('document.id'),
                             index=True, nullable=False)
    documento = db.relationship('Documento', backref=db.backref('tasas',
                                cascade="delete,delete-orphan"))
