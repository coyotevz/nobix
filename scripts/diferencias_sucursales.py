#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
from optparse import OptionParser
from sqlalchemy.orm import create_session
from sqlalchemy.orm.exc import NoResultFound

from nobix.db import metadata, create_engine
from nobix.models import Articulo, Documento, ItemDocumento, Cliente, Cache, Tasa

def diff_precios(e1, e2):
    sess1, sess2 = _create_sessions(e1, e2)

    precios = []

    for a1 in sess1.query(Articulo).filter(Articulo.es_activo==True):
        try:
            a2 = sess2.query(Articulo).filter_by(codigo=a1.codigo).one()
        except NoResultFound:
            continue
        if a1.precio != a2.precio:
            diff = a2.precio - a1.precio
            precios.append((diff, a1, a2))
    sess1.close()
    sess2.close()
    del sess1, sess2

    return sorted(precios, key=lambda e: abs(e[0]), reverse=True)

def diff_agrupacion(e1, e2):
    sess1, sess2 = _create_sessions(e1, e2)

    for a1 in sess1.query(Articulo).filter(Articulo.es_activo==True):
        try:
            a2 = sess2.query(Articulo).filter_by(codigo=a1.codigo).one()
        except NoResultFound:
            continue
        if a1.agrupacion != a2.agrupacion:
            yield (a1, a2)
    sess1.close()
    sess2.close()
    del sess1, sess2
    raise StopIteration

def diff_descripcion(e1, e2):
    sess1, sess2 = _create_sessions(e1, e2)

    for a1 in sess1.query(Articulo).filter(Articulo.es_activo==True):
        try:
            a2 = sess2.query(Articulo).filter_by(codigo=a1.codigo).one()
        except NoResultFound:
            continue
        if a1.descripcion.strip() != a2.descripcion.strip():
            yield (a1, a2)
    sess1.close()
    sess2.close()
    del sess1, sess2
    raise StopIteration

def diff_faltantes(e1, e2):
    sess1, sess2 = _create_sessions(e1, e2)

    for a1 in sess1.query(Articulo).filter(Articulo.es_activo==True):
        try:
            a2 = sess2.query(Articulo).filter_by(codigo=a1.codigo).one()
        except NoResultFound:
            yield a1
    sess1.close()
    sess2.close()
    del sess1, sess2
    raise StopIteration

def desc_vacias(engine):
    metadata.create_all(bind=engine)
    sess = create_session(bind=engine)

    for a in sess.query(Articulo).filter(Articulo.es_activo==True):
        if a.descripcion.strip() == u"":
            yield a

def _create_sessions(e1, e2):
    metadata.create_all(bind=e1)
    metadata.create_all(bind=e2)

    sess1 = create_session(bind=e1)
    sess2 = create_session(bind=e2)
    return sess1, sess2

def main():
    parser = OptionParser()
    parser.add_option('--url1', dest='url1')
    parser.add_option('--url2', dest='url2')

    (options, args) = parser.parse_args()

    if not options.url1 or not options.url2:
        parser.error("debe proveer ambos argumentos --url1 y --url2")

    engine1 = create_engine(options.url1)
    engine2 = create_engine(options.url2)

    with codecs.open("faltantes_en_godoycruz.txt", "w", encoding="utf-8") as out:
        for a in diff_faltantes(engine1, engine2):
            out.write(("%-14s %-40s %9s %9s %-20s" % (a.codigo, a.descripcion, a.precio,
                a.vigencia.strftime("%d/%m/%Y"), a.agrupacion)).strip()+'\n')
    print "Se escribio faltantes_en_godoycruz.txt"

    with codecs.open("faltantes_en_ciudad.txt", "w", encoding="utf-8") as out:
        for a in diff_faltantes(engine2, engine1):
            out.write(("%-14s %-40s %9s %9s %-20s" % (a.codigo, a.descripcion, a.precio,
                a.vigencia.strftime("%d/%m/%Y"), a.agrupacion)).strip()+'\n')
    print "Se escribio faltantes_en_ciudad.txt"

    with codecs.open("diferencias_de_precio.txt", "w", encoding="utf-8") as out:
        for diff, a1, a2 in diff_precios(engine1, engine2):
            out.write(("%-14s %-40s / %9s (%s) <--> %9s (%s) %7s" % (a1.codigo, a1.descripcion,
                a1.precio, a1.vigencia.strftime("%d/%m/%Y"),
                a2.precio, a2.vigencia.strftime("%d/%m/%Y"), diff)).strip()+'\n')
    print "Se escribio diferencias_de_precio.txt"

    with codecs.open("diferencias_de_agrupacion.txt", "w", encoding="utf-8") as out:
        for a1, a2 in diff_agrupacion(engine1, engine2):
            out.write(("%-14s %-40s / %-20s <--> %-20s" % (a1.codigo, a1.descripcion,
                a1.agrupacion, a2.agrupacion)).strip()+'\n')
    print "Se escribio diferencias_de_agrupacion.txt"

    with codecs.open("diferencias_de_descripcion.txt", "w", encoding="utf-8") as out:
        for a1, a2 in diff_descripcion(engine1, engine2):
            out.write(("%-14s %-40s %s\n%-14s %-40s %s" % (a1.codigo, a1.descripcion,
                a1.vigencia.strftime("%d/%m/%Y"), "", a2.descripcion,
                a2.vigencia.strftime("%d/%m/%Y"))).strip()+'\n')
    print "Se escribio diferencias_de_descripcion.txt"

    with codecs.open("descripciones_vacias.txt", "w", encoding="utf-8") as out:
        for engine in (engine1, engine2):
            url = str(engine.url)
            out.write("\n%s\n%s\n" % (url, "-"*len(url)))
            for a in desc_vacias(engine):
                out.write(("%-14s Descripcion Vacia / %-20s %9s %9s" % (a.codigo, a.agrupacion, a.precio,
                    a.vigencia.strftime("%d/%m/%Y"))).strip()+'\n')
    print "Se escribio descripciones_vacias.txt"

if __name__ == '__main__':
    main()
