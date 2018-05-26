# -*- coding: utf-8 -*-

from . import db


class ItemDocumento(db.Model):
    __tablename__ = 'items_documento'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.UnicodeText(14))
    descripcion = db.Column(db.UnicodeText(40), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    articulo_id = db.Column(db.Integer, db.ForeignKey('articulos.id'),
                            index=True)
    articulo = db.relationship('Articulo', backref='doc_items')

    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'),
                             index=True, nullable=False)
    documento = db.relationship('Documento', backref='items')
