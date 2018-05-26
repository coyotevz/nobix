# -*- coding: utf-8 -*-

from . import db


class Tasa(db.Model):
    __tablename__ = 'tasas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.UnicodeText(3), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)

    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'),
                             index=True, nullable=False)
    documento = db.relationship('Documento', backref=db.backref('tasas',
                                cascade="delete,delete-orphan"))
