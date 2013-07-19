#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
from decimal import Decimal
from datetime import datetime
from sqlalchemy import func, or_

from nobix.db import setup_db, Session
from nobix.models import Articulo
from nobix.config import load_config

"""
Para imprimir archivo generado:
    $ cat <archivo_generado.txt> | lp -o cpi=16 -o lpi=8 -o media=a4
"""

q = Decimal('0.01')
now = datetime.now()

def aumentar_y_asentar(factor, outfile):

    config = load_config()
    setup_db(config.database_uri)
    session = Session()

    query = session.query(Articulo).filter(Articulo.es_activo==True)\
                   .filter(or_(Articulo.agrupacion.startswith(u"FV"),
                               Articulo.agrupacion.endswith(u"FV")))\
                   .order_by(Articulo.agrupacion, Articulo.codigo)

    last_group = None
    for articulo in query:
        if last_group != articulo.agrupacion:
            last_group = articulo.agrupacion
            outfile.write("\n%s\n%s\n" % (last_group, "-"*len(last_group)))
        precio_viejo = articulo.precio
        vigencia_vieja = articulo.vigencia
        articulo.precio = (articulo.precio * factor).quantize(q)
        articulo.vigencia = now
        outfile.write("%-14s %-40s / %9s (%s) --> %9s (%s) %7s\n" % (
            articulo.codigo, articulo.descripcion,
            precio_viejo, vigencia_vieja.strftime("%d/%m/%Y"),
            articulo.precio, articulo.vigencia.strftime("%d/%m/%Y"),
            "+%s" % (articulo.precio - precio_viejo)))
    session.commit()

if __name__ == '__main__':
    factor = Decimal('1.07')
    fn = "actualizacion_fv_%s.txt" % now.strftime("%Y-%m-%d-%H%M")
    with codecs.open(fn, "w", encoding="utf-8") as outfile:
        outfile.write(u"Aumento precios FV 7%% (%s)\n" % now.strftime("%d-%m-%Y %H:%M"))
        aumentar_y_asentar(factor, outfile)
    print "Se escribio %s" % fn
