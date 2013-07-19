#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rudimentario script útil para la sincronización de articulos entre sucursales.
Principalmente pensado para ser processado con 'diff' o algo parecido.
"""

import sys

from nobix.db import setup_db, Session
from nobix.models import Articulo
from nobix.config import load_config

session = Session()

def init_db():
    config = load_config()
    setup_db(config.database_uri)

def listar_articulos(agrupaciones=None):
    query = session.query(Articulo).filter(Articulo.es_activo==True)\
                   .order_by(Articulo.codigo.asc())

    if agrupaciones and isinstance(agrupaciones, list):
        query = query.filter(Articulo.agrupacion.in_(agrupaciones))

    for art in query:
        print ("%-14s %-40s %9s %9s %-20s" % (art.codigo, art.descripcion,
                                              art.precio, art.vigencia.strftime("%d/%m/%Y"),
                                              art.agrupacion)).strip().encode('utf-8')

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    init_db()
    listar_articulos([unicode(a) for a in args])

if __name__ == '__main__':
    main()
