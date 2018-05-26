# -*- coding: utf-8 -*-

from decimal import Decimal
from nobix.config import get_current_config

from . import db
from .document import Documento
from .item import ItemDocumento


class Articulo(db.Model):
    __tablename__ = 'articulos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Unicode(14), nullable=False, unique=True)
    descripcion = db.Column(db.UnicodeText(40), nullable=False)
    proveedor = db.Column(db.UnicodeText(20))
    agrupacion = db.Column(db.UnicodeText(20))
    vigencia = db.Column(db.DateTime)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    existencia = db.Column(db.Numeric(10, 2), default=Decimal)
    es_activo = db.Column(db.Boolean, default=True)

    #: 'doc_items' field added by ItemDocumento model

    @property
    def existencia_new(self):
        sal = [k for k, v in get_current_config().documentos.items()
               if v['stock'] == 'salida']
        ent = [k for k, v in get_current_config().documentos.items()
               if v['stock'] in ('entrada', 'ajuste')]
        sess = db.object_session(self)
        q = sess.query(db.func.sum(ItemDocumento.cantidad))\
                .filter(ItemDocumento.articulo == self)
        s = q.filter(ItemDocumento.documento.has(Documento.tipo.in_(sal)))\
            .scalar() or Decimal()
        e = q.filter(ItemDocumento.documento.has(Documento.tipo.in_(ent)))\
            .scalar() or Decimal()
        return e - s
