#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
El archivo generado se puede imprimir con cups:
    $ lp -o cpi=12 <archivo_generado>
"""

import sys
import os
import codecs
from itertools import count, izip_longest
from operator import itemgetter

from sqlalchemy import func

from nobix.db import setup_db, Session
from nobix.models import Articulo
from nobix.config import load_config

def listar_agrupaciones(out):

    config = load_config()
    setup_db(config.database_uri)
    session = Session()

    query = session.query(Articulo.agrupacion, func.count(Articulo.id)).filter(Articulo.es_activo==True)\
                   .group_by(Articulo.agrupacion)

    lista = sorted(query, key=itemgetter(0))
    p = count(1)
    title = (u"Índice de agrupaciones (tot %d)" % len(lista)).center(80)

    while len(lista) > 0:
        lpage, lista = lista[:132], lista[132:]
        out.write("".join([title, (u"Página #%d" % p.next()).rjust(12), '\n']))
        col1, col2 = lpage[:66], lpage[66:]
        for (a1, c1), (a2, c2) in izip_longest(col1, col2, fillvalue=("", "")):
            out.write("%-12s %3s%30s%-12s %3s\n" % (a1, c1, "", a2, c2))
    out.flush()

def listar(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) == 0:
        out = codecs.getwriter(sys.stdout.encoding)(sys.stdout)
    else:
        outfn = args[0]
        if os.path.exists(outfn):
            raise Exception("El archivo %s ya existe." % outfn)
        out = codecs.open(outfn, "w", encoding="utf-8")

    listar_agrupaciones(out)
    out.close()

if __name__ == '__main__':
    listar()
