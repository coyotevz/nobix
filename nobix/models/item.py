# -*- coding: utf-8 -*-

from . import db


class ItemDocumento(db.Model):
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column('sku', db.UnicodeText(14))
    descripcion = db.Column('description', db.UnicodeText(40), nullable=False)
    cantidad = db.Column('quantity', db.Numeric(10, 2), nullable=False)
    precio = db.Column('price', db.Numeric(10, 2), nullable=False)

    articulo_id = db.Column('product_id', db.Integer, db.ForeignKey('product.id'),
                            index=True)
    articulo = db.relationship('Articulo', backref='doc_items')

    documento_id = db.Column('document_id', db.Integer, db.ForeignKey('document.id'),
                             index=True, nullable=False)
    documento = db.relationship('Documento', backref='items')
