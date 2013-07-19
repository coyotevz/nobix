#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import date
from decimal import Decimal

from nobix.db import setup_db, Session
from nobix.models import Documento, Tasa
from nobix.config import load_config
from nobix import widget

end_date = date(2010, 06, 01)
zero = Decimal(0)

def limpiar():
    config = load_config()
    setup_db(config.database_uri)
    session = Session()

    for doc in session.query(Documento).filter(Documento.fecha<end_date).all():
        # Limpiamos tasas
        for t in doc.tasas:
            session.delete(t)

        doc.periodo_iva = None
        doc.descuento = zero
        doc.neto = zero
        doc.fiscal = None
        doc.cliente_id = None

    session.commit()
    session.close()


if __name__ == '__main__':
    limpiar()
