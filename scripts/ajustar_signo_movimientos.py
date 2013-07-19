#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy.orm import contains_eager

from nobix.db import setup_db, Session
from nobix.models import ItemDocumento, Documento
from nobix.config import load_config

def ajustar():
    config = load_config()
    setup_db(config.database_uri)
    session = Session()

    salidas = [docname for docname, conf in config.documentos.iteritems() if conf['stock'] == u'salida']
    query = session.query(ItemDocumento).filter(ItemDocumento.documento.has(Documento.tipo.in_(salidas)))

    print "Se ajustaran %s items." % query.count()

    for item in query:
        item.cantidad = -item.cantidad
    session.commit()

if __name__ == '__main__':
    ajustar()
