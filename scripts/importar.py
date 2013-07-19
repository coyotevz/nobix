#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import glob
import time
import string
import codecs
import itertools
from datetime import datetime
from decimal import Decimal, InvalidOperation
from optparse import OptionParser

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from nobix.db import setup_db, Session
from nobix.models import Articulo, Documento, ItemDocumento, Tasa, Cliente
from nobix.config import load_config
from nobix import widget
from nobix.utils import validar_cuit, convert2dp, smart_unicode

_numbers = tuple(string.digits)
stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout)

def su(t):
    return unicode(t).encode('utf-8')

def parse_cuit(cuit_str):
    if cuit_str == "Cons.Final":
        return None
    if "-" in cuit_str:
        return cuit_str
    if cuit_str.startswith("000"):
        # recreo digito verificador
        base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        cuit = cuit_str[3:]
        aux = 0
        for i in xrange(10):
            aux += int(cuit[i])*base[i]
        aux = 11 - (aux - (int(aux/11) * 11))
        if aux == 11:
            aux = 0
        if aux == 10:
            aux = 9
        return cuit[:2] + "-" + cuit[2:] + "-" + unicode(aux)

def report_time(func, *args):
    t0 = datetime.now()
    retval = func(*args)
    t1 = datetime.now()
    t = t1 - t0
    secs = t.days*24*60*60+t.seconds
    mins, sec = divmod(secs, 60)
    hrs, mins = divmod(mins, 60)
    ptime(u"%2dh%2dm%2d.%ss\n" % (hrs, mins, sec, str(t.microseconds)[:3]))
    return retval

def migrar_articulos(args):
    """
    Importa los artículos existentes en el sistema OPUS.
    
    Tiene como entrada tres archivos que son generados con el sistema OPUS, y
    luego retocados un poco a mano, como sacar las lineas que no tienen sentido.
    
    Se esperan archivos generados de la siguente manera (en este orden):
    
    STOCK.
    LISTE STARTICULO STNOMBRE STPRECIOVTA1.
    YA.
    
    STOCK.
    LISTE STARTICULO STAGRUPACION STTROQUEL.
    YA.
    
    STOCK.
    LISTE STARTICULO STFECHADIA STFECHAMES STFECHAANO.
    YA.
    
    Nota: OPUS tiene un bug que intercambia STFECHADIA con STFECHAANO, por lo que al parsear,
    tomamos el primer campo como año y el tercer campo como día.
    """
    try:
        session, outpath, artnombre_filename, artagrupacion_filename, artvigencia_filename = args
    except (ValueError, IndexError):
        error(u"migrar_articulos(): Argumentos Inválidos")

    artnombre = codecs.open(artnombre_filename, "r", encoding="cp850")
    artagrupacion = codecs.open(artagrupacion_filename, "r", encoding="cp850")
    artvigencia = codecs.open(artvigencia_filename, "r", encoding="cp850")

    _mezclados = {}
    _invalidos = {}
    _fecha_invalida = {}

    lineno = 0
    _readed = 0

    bar = ProgressBar(u"analizando artículos", sum(map(os.path.getsize, args[2:])))

    for lnombre, lagrupacion, lvigencia in itertools.izip(artnombre, artagrupacion, artvigencia):
        lineno += 1

        art = lnombre[:19].strip()
        art2 = lagrupacion[:19].strip()
        art3 = lvigencia[:19].strip()

        if art == art2 == art3:
            if art.startswith(_numbers):
                descripcion = lnombre[19:75].strip()
                precio = lnombre[75:].strip()
                agrupacion = lagrupacion[19:34].strip()
                proveedor = lagrupacion[34:].strip()
                v_anio = lvigencia[19:22].strip()
                v_mes = lvigencia[26:29].strip()
                v_dia = lvigencia[33:].strip()
                try:
                    vigencia = datetime(2000 + int(v_anio), int(v_mes), int(v_dia))
                except ValueError:
                    vigencia = datetime(2000, 1, 1)
                    _fecha_invalida[lineno] = {'art': art, 'descripcion': descripcion,
                            'precio': precio, 'agrupacion': agrupacion, 'proveedor': proveedor,
                            'bad_date': (v_dia, v_mes, v_anio)}
                a = Articulo()
                a.codigo = art
                a.descripcion = descripcion
                a.precio = Decimal(precio)
                a.agrupacion = agrupacion
                a.proveedor = proveedor
                a.vigencia = vigencia
                session.add(a)
            else:
                _invalidos[lineno] = (lnombre, lagrupacion, lvigencia)
        else:
            _mezclados[lineno] = (lnombre, lagrupacion, lvigencia)

        _readed += len(lnombre) + len(lagrupacion) + len(lvigencia)
        bar.update_state(_readed)
    bar.finish()

    valid_data_len = len(session.new)
    session.commit()
    artnombre.close()
    artagrupacion.close()
    artvigencia.close()

    info(u"Se agregaron %d artículos a la base de datos" % valid_data_len)

    if _mezclados:
        warn(u"Lineas mezcladas (%d)" % len(_mezclados))
        out = codecs.open(os.path.join(outpath, "imp_articulos_mezclados.txt"), "w", encoding="utf-8")
        for key, value in sorted(_mezclados.iteritems()):
            out.write(u"%d: %r\n" % (key, value[0]))
            out.write(u"%d: %r\n" % (key, value[1]))
            out.write(u"%d: %r\n\n" % (key, value[2]))
        out.close()

    if _invalidos:
        warn(u"Lineas inválidas (%s)" % len(_invalidos))
        out = codecs.open(os.path.join(outpath, "imp_articulos_linea_invalida.txt"), "w", encoding="utf-8")
        for key, value in sorted(_invalidos.iteritems()):
            out.write(u"%d: %r\n" % (key, value[0]))
            out.write(u"%d: %r\n" % (key, value[1]))
            out.write(u"%d: %r\n\n" % (key, value[2]))
        out.close()

    if _fecha_invalida:
        warn(u"Algunas Fechas inválidas (%s)" % len(_fecha_invalida))
        out = codecs.open(os.path.join(outpath, "imp_articulos_fecha_invalida.txt"), "w", encoding="utf-8")
        out.write(u"# Estos artículos existen en la base de datos pero con fecha 01/01/2000\n\n")
        for key, value in sorted(_fecha_invalida.iteritems()):
            out.write(u"%5d: " % key)
            out.write(u"%(art)-14s " % value)
            out.write(u" %10s " % ("(" + "/".join(value['bad_date']) + ")"))
            out.write(u"%(descripcion)-40s %(precio)8s %(agrupacion)-20s %(proveedor)-20s\n" % value)
        out.close()

def migrar_existencias(args):
    """
    Importa la existencia de los artículos, este script debe ser ejecutado luego de importar
    los artículos a la base de datos.
    
    Tiene como entrada la salida de un archivo generado en el OPUS con los siguentes comandos.
    
    STOCK.
    LISTE MDARTICULO MDEXISTENCIAS MDEXISTINICIAL
    YA.
    """
    try:
        session, outpath, existencias_filename = args
    except (ValueError, IndexError):
        error(u"migrar_existencias(): Argumentos Inválidos")

    existencias = codecs.open(existencias_filename, "r", encoding="cp850")

    _no_encontrados = {}
    _multiple_found = {}

    lineno = 0
    _readed = 0
    modified = 0

    bar = ProgressBar(u"analizando existencias", os.path.getsize(existencias_filename))

    for line in existencias:
        lineno += 1
        _readed += len(line)

        if not line[0].isdigit():
            continue

        codigo = line[:13].strip()
        desc = line[13:48].strip()
        exis = line[71:81].strip()

        # 1. Nos fijamos si puede ser un codigo incompleto
        if len(codigo) == 13:
            try:
                # 2. Buscamos todos los que empiezan con este codigo
                art = session.query(Articulo).filter(Articulo.codigo.startswith(codigo)).one()
            except MultipleResultsFound:
                # 3. Buscamos todos los que empiezan con este codigo y esta descripcion
                try:
                    art = session.query(Articulo).filter(Articulo.codigo.startswith(codigo))\
                                                 .filter(Articulo.descripcion.startswith(desc)).one()
                except MultipleResultsFound:
                    # No podemos adivinar mas
                    _multiple_found[lineno] = line.strip()
                    continue
                except NoResultFound:
                    # No Exsiten con este comienzo de descripcion
                    _no_encontrados[lineno] = line.strip()
                    continue
            except NoResultFound:
                # No existe ningun articulo con este codigo
                _no_encontrados[lineno] = line.strip()
                continue
        else:
            try:
                art = session.query(Articulo).filter(Articulo.codigo==codigo).one()
            except NoResultFound:
                _no_encontrados[lineno] = line.strip()
                continue
        # Si raisea MultipleResultsFound en este nivel lo dejamos porque es un error de consistencia.

        if exis:
            e = Decimal(exis.replace(',', '.'))
            if e != 0:
                modified += 1
                art.existencia = Decimal(exis.replace(',', '.'))

        bar.update_state(_readed)

    bar.finish()
    session.commit()
    existencias.close()

    info(u"Se modificó la existencia de %d artículos" % modified)

    if _no_encontrados:
        warn(u"No se encotraron algunos artículos en la base de datos (%d)" % len(_no_encontrados))
        out = codecs.open(os.path.join(outpath, "imp_existencia_no_encontrados.txt"), "w", encoding="utf-8")
        for key, value in sorted(_no_encontrados.iteritems()):
            out.write(u"%d: %s\n" % (key, value))
        out.close()

    if _multiple_found:
        warn(u"No se pudieron adivinar algunos artículos (%d)" % len(_multiple_found))
        out = codecs.open(os.path.join(outpath, "imp_existencia_no_adivinados.txt"), "w", encoding="utf-8")
        for key, value in sorted(_multiple_found.iteritems()):
            out.write(u"%d: %s\n" % (key, value))
        out.close()

def migrar_movimientos(args):
    """
    Importa el movimiento de los artículos del sistema OPUS.
    
    Tiene como entrada la salida del comando en OPUS:
    
        S31 --> Criterio de Selección --> Fecha
            --> Orden de Acceso --> 2 (Por fecha y numero de comprobante)
            --> Ejecuta
    """

    try:
        session, outpath, config, movimientos_filename = args
    except (ValueError, IndexError):
        error(u"migrar_movimientos(): Argumentos Inválidos")

    movimientos = codecs.open(movimientos_filename, "r", encoding="cp850")

    _no_encontrados = {}
    _multiple_found = {}
    _articulos_bad_col = {}
    _articulos_bad_doc = {}
    _articulos_bad_qty = {}

    new_doc = True
    created_number = None
    lineno = 0
    movcount = 0
    _readed = 0

    bar = ProgressBar(u"analizando movimientos", os.path.getsize(movimientos_filename), interval=0.3)

    for line in movimientos:
        lineno += 1
        _readed += len(line)

        if line[0] == '.':
            new_doc = True
            created_number = None
            continue

        if not line[0].isdigit():
            continue

        codigo = line[:12].strip()
        desc = line[12:43].strip()
        suc = line[44:47].strip()
        fecha = line[48:56].strip()
        docnumber = line[57:63].strip()
        doc_tipo = line[64:67].strip()
        vend = line[68:71].strip()
        clinum = line[76:87].strip()
        ent = line[88:98].strip()
        sal = line[99:107].strip()
        exis = line[108:116].strip()

        # 1. Nos fijamos si puede ser un codigo incompleto
        if len(codigo) == 12:
            try:
                # 2. Buscamos todos los que empiezan con este codigo
                art = session.query(Articulo).filter(Articulo.codigo.startswith(codigo)).one()
            except MultipleResultsFound:
                # 3. Buscamos todos los que empiezan con este codigo y esta descripcion
                try:
                    art = session.query(Articulo).filter(Articulo.codigo.startswith(codigo))\
                                                 .filter(Articulo.descripcion.startswith(desc)).one()
                except MultipleResultsFound:
                    # No podemos adivinar mas
                    _multiple_found[lineno] = line.strip()
                    continue
                except NoResultFound:
                    # No Exsiten con este comienzo de descripcion
                    _no_encontrados[lineno] = line.strip()
                    continue
            except NoResultFound:
                # No existe ningun articulo con este codigo
                _no_encontrados[lineno] = line.strip()
                continue
        else:
            try:
                art = session.query(Articulo).filter(Articulo.codigo==codigo).one()
            except NoResultFound:
                _no_encontrados[lineno] = line.strip()
                continue
        # Si raisea MultipleResultsFound en este nivel lo dejamos porque es un error de consistencia.

        if doc_tipo == u"VEN":
            doc_tipo = u"INV"
            ent, sal = sal, ent

        doctype = config.documentos.get(doc_tipo)
        if ((doctype is None) or
            (doctype['stock'] == 'salida' and ent != '') or
            (doctype['stock'] in ('entrada', 'ajuste', 'inventario') and sal != '')):
            _articulos_bad_col[lineno] = line.strip()
            continue

        fecha = datetime.strptime(fecha, "%d%m%Y").date()

        docnumber = int(docnumber or 1)
        if created_number is not None:
            docnumber = created_number

        if new_doc:
            # Pueden haber dos documentos en el mismo día con el mismo numero
            while session.query(Documento).filter_by(tipo=doc_tipo, fecha=fecha, numero=docnumber).count():
                docnumber += 1
            created_number = docnumber
            documento = Documento(tipo=doc_tipo, fecha=fecha, numero=docnumber, vendedor=vend, neto=Decimal(0))
            session.add(documento)
            new_doc = False
        else:
            # Comprobar validez
            if documento.tipo != doc_tipo or\
               documento.fecha != fecha or\
               documento.numero != docnumber or\
               documento.vendedor != vend:
                _articulos_bad_doc[lineno] = line.strip()
                continue

        try:
            cantidad = Decimal( (sal if doctype['stock'] == 'salida' else ent).replace(',', '.') )
        except InvalidOperation:
            _articulos_bad_qty[lineno] = line.strip()
            cantidad = Decimal(0)
        item = ItemDocumento(codigo=art.codigo, descripcion=art.descripcion, cantidad=cantidad,
                             precio=art.precio, articulo=art, documento=documento)
        movcount += 1

        bar.update_state(_readed)

    bar.finish()
    session.commit()
    movimientos.close()

    info(u"Se agregaron %s movimientos de artículos" % movcount)

    if _no_encontrados:
        warn(u"No se encotraron algunos artículos en la base de datos (%d)" % len(_no_encontrados))
        out = codecs.open(os.path.join(outpath, "imp_movimiento_no_encontrados.txt"), "w", encoding="utf-8")
        for key, value in sorted(_no_encontrados.iteritems()):
            out.write(u"%6d: %s\n" % (key, value))
        out.close()

    if _multiple_found:
        warn(u"No se pudieron adivinar algunos artículos (%d)" % len(_multiple_found))
        out = codecs.open(os.path.join(outpath, "imp_movimiento_no_adivinados.txt"), "w", encoding="utf-8")
        for key, value in sorted(_multiple_found.iteritems()):
            out.write(u"%6d: %s\n" % (key, value))
        out.close()

    if _articulos_bad_doc:
        warn(u"Hay artículos que no pertenecen al mismo documento que sus compañeros (%s)" %\
                len(_articulos_bad_doc))
        out = codecs.open(os.path.join(outpath, "imp_movimiento_bad_doc.txt"), "w", encoding="utf-8")
        for key, value in sorted(_articulos_bad_doc.iteritems()):
            out.write(u"%6d: %s\n" % (key, value))
        out.close()

    if _articulos_bad_col:
        warn(u"Hay movimientos de artículos tiene su columna incopatible con el tipo de"
             u" documento al que pertenecen (%d)" % len(_articulos_bad_col))
        out = codecs.open(os.path.join(outpath, "imp_movimiento_bad_col.txt"), "w", encoding="utf-8")
        for key, value in sorted(_articulos_bad_col.iteritems()):
            out.write(u"%6d: %s\n" % (key, value))
        out.close()

    if _articulos_bad_qty:
        warn(u"Hay movimientos de artículos tiene sus columnas vacías (%d)" % len(_articulos_bad_qty))
        out = codecs.open(os.path.join(outpath, "imp_movimiento_bad_qty.txt"), "w", encoding="utf-8")
        for key, value in sorted(_articulos_bad_qty.iteritems()):
            out.write(u"%6d: %s\n" % (key, value))
        out.close()

def migrar_terceros(args):
    """
    Importa los datos de terceros existentes en el sistema OPUS.
    
    Tiene como entrada tres archivos que son generados desde el sistema OPUS.
    
    Se esperan archivos generados de la siguente manerea (en este orden):
    
    TERCEROS.
    LISTE CTCODTER CTNUMTER CTNOMBRE CTCODPOSTAL.
    YA.
    
    TERCEROS.
    LISTE CTCODTER CTNUMTER CTCUIT CTCODIVA.
    YA.
    
    TERCEROS.
    LISTE CTCODTER CTNUMTER CTDOMICILIO CTLOCALIDAD.
    YA.
    """
    try:
        session, outpath, config, ternombre_filename, tercodiva_filename, terdomicilio_filename = args
    except (ValueError, IndexError):
        error(u"migrar_terceros(): Argumentos Inválidos")

    clientes_especiales_extra = {
        '219': None,
    }

    ternombre = codecs.open(ternombre_filename, "r", encoding="cp850")
    tercodiva = codecs.open(tercodiva_filename, "r", encoding="cp850")
    terdomicilio = codecs.open(terdomicilio_filename, "r", encoding="cp850")

    _instaladores = {}
    _cuit_invalido = {}
    _omitidos = {}
    _incompletos = {}
    _invalidos = {}
    _mezclados = {}

    clientes_especiales = config.clientes_especiales.copy()
    clientes_especiales.update(clientes_especiales_extra)

    lineno = 0
    _readed = 0
    session.add_all([Cliente(**data) for data in filter(None, clientes_especiales.values())])

    current_codigo = { u'C': 50, u'P': 100 }

    bar = ProgressBar(u"analizando tercero", sum(map(os.path.getsize, args[3:])))

    for lnombre, lcodiva, ldomicilio in itertools.izip(ternombre, tercodiva, terdomicilio):
        lineno += 1
        _readed += len(lnombre) + len(lcodiva) + len(ldomicilio)

        codter = lnombre[:6].strip()
        numter = lnombre[6:23].strip()
        codter2 = lcodiva[:6].strip()
        numter2 = lcodiva[6:23].strip()
        codter3 = ldomicilio[:6].strip()
        numter3 = ldomicilio[6:23].strip()

        if codter == codter2 == codter3 and \
           numter == numter2 == numter3:

            nombre = lnombre[23:63].strip()
            codigo_postal = lnombre[63:].strip()
            cuit = lcodiva[23:42].strip()
            codiva = lcodiva[42:].strip()
            domicilio = ldomicilio[23:63].strip()
            localidad = ldomicilio[63:].strip()

            if codter in (u'C', u'P'):
                if numter and nombre and codiva:
                    if codiva in (u'I', u'E', u'M', u'R') and not validar_cuit(cuit):
                        _cuit_invalido[lineno] = {'codter': codter, 'numter': numter,
                                                  'nombre': nombre, 'cuit': cuit,
                                                  'codiva': codiva, 'domicilio': domicilio,
                                                  'localidad': localidad, 'cp': codigo_postal}
                    elif numter in clientes_especiales.keys():
                        _omitidos[lineno] = {'codter': codter, 'numter': numter, 'nombre': nombre,
                                'cuit': cuit, 'codiva': codiva, 'domicilio': domicilio,
                                'localidad': localidad, 'cp': codigo_postal}
                    else:
                        c = Cliente()
                        c.relacion = codter
                        c.codigo = current_codigo[codter]
                        c.nombre = nombre
                        c.domicilio = domicilio
                        c.localidad = localidad
                        c.codigo_postal = codigo_postal
                        c.responsabilidad_iva = codiva.replace(u'F', u'C')
                        if codiva != u'F':
                            c.cuit = cuit
                        session.add(c)
                        current_codigo[codter] += 1
                else:
                    _incompletos[lineno] = (lnombre, lcodiva, ldomicilio)
            elif codter == u'I':
                _instaladores[numter] = {'nombre': nombre,
                                         'domicilio': domicilio,
                                         'localidad': localidad,
                                         'cp': codigo_postal}
            else:
                _invalidos[lineno] = (lnombre, lcodiva, ldomicilio)
        else:
            _mezclados[lineno] = (lnombre, lcodiva, ldomicilio)

        bar.update_state(_readed)

    bar.finish()
    valid_data_len = len(session.new)
    session.commit()

    ternombre.close()
    tercodiva.close()
    terdomicilio.close()

    info(u"Se agregaron %d clientes a la base de datos." % valid_data_len)

    if _mezclados:
        warn(u"Lineas mezcladas (%d)" % len(_mezclados))
        out = codecs.open(os.path.join(outpath, "imp_terceros_mezclados.txt"), "w", encoding="utf-8")
        for key, value in sorted(_mezclados.iteritems()):
            out.write(u"%d: %r\n" % (key, value[0]))
            out.write(u"%d: %r\n" % (key, value[1]))
            out.write(u"%d: %r\n\n" % (key, value[2]))
        out.close()

    if _invalidos:
        warn(u"Lineas inválidas (%s)" % len(_invalidos))
        out = codecs.open(os.path.join(outpath, "imp_terceros_lineas_invalidas.txt"), "w", encoding="utf-8")
        for key, value in sorted(_invalidos.iteritems()):
            out.write(u"%d: %r\n" % (key, value[0]))
            out.write(u"%d: %r\n" % (key, value[1]))
            out.write(u"%d: %r\n\n" % (key, value[2]))
        out.close()

    if _cuit_invalido:
        warn(u"Algunos CUIT inválidos (%d)" % len(_cuit_invalido))
        out = codecs.open(os.path.join(outpath, "imp_terceros_cuit_invalido.txt"), "w", encoding="utf-8")
        for key, value in sorted(_cuit_invalido.iteritems()):
            out.write((u"%4d: " % key) +\
                      (u"%(codter)-2s %(numter)-12s %(nombre)-35s %(codiva)-2s %(cuit)14s" \
                       u"  %(domicilio)-35s %(localidad)-20s %(cp)-8s" % value).strip() + u"\n")
        out.close()

    if _omitidos:
        info(u"Algunos Clientes omitidos (%d)" % len(_omitidos))
        out = codecs.open(os.path.join(outpath, "imp_terceros_omitidos.txt"), "w", encoding="utf-8")
        out.write(u"# Esta es la lista de cliente omitidos porque han sido configurados\n")
        out.write(u"# como clientes especiales.\n\n")
        for key, value in sorted(_omitidos.iteritems()):
            out.write((u"%4d: " % key) +\
                      (u"%(codter)-2s %(numter)-12s %(nombre)-35s %(codiva)-2s %(cuit)14s" \
                       u"  %(domicilio)-35s %(localidad)-20s %(cp)-8s" % value).strip() + u"\n")
        out.close()

    if _instaladores:
        fname = os.path.join(outpath, 'instaladores.txt')
        info(u"Instaladores almacenados en '%s' (%d)" % (fname, len(_instaladores)))
        out = codecs.open(fname, "w", encoding="utf-8")
        for key, value in sorted(_instaladores.iteritems()):
            out.write((u"%-12s " % key).ljust(8) +\
                      (u"%(nombre)-35s %(domicilio)-35s %(localidad)-20s %(cp)-8s" % value).strip() + u"\n")
        out.close()

def migrar_libro_iva(args):
    """
    Importa los documentos que han particupado del libro IVA en el sistema OPUS.
    
    Lamentablemente no he encotrado la manera de extraer toda la información de una sola
    vez, asique hay que exportar mes x mes el libro IVA del sistema OPUS y colocarles el nombre
    IVA_mmaa.TXT donde mm corresponde al mes y aa corresponde al año del periodo fiscal al que
    pertenecen.
    
    Se espera el nombre de un directorio que contiene todos estos archivos esportados.
    """
    try:
        session, outpath, config, base_dir = args
    except (ValueError, IndexError):
        error(u"migrar_libro_iva(): Argumentos Inválidos")

    if not os.path.isdir(base_dir):
        error(u"migrar_libro_iva(): '%s' no es un directorio válido" % base_dir)

    livas = glob.glob(os.path.join(base_dir, "IVA_????.TXT"))
    livas.sort(cmp=lambda x, y: cmp(x[-6:-4]+x[-8:-6], y[-6:-4]+y[-8:-6]))

    complete_line_pat = re.compile(r'^(\s[1-9]|[12][0-9]|3[01])/(0[1-9]|1[012])/(19|20)\d\d\s(A|B)')
    only_tax_line_pat = re.compile(r'^\s{11}(A|B)')

    _no_related_doc = {}
    _bad_gravado_doc = {}
    _invalid_docnumber = {}

    fileno = 0
    docmod = 0
    docnew = 0

    _venta_impersonal = session.query(Cliente).filter(Cliente.codigo==1).one()

    for liva_filename in livas:
        fileno += 1
        liva = codecs.open(liva_filename, "r", encoding="cp850")
        lineno = 0
        _readed = 0
        tcount = 0

        periodo_iva = datetime.strptime(liva_filename, os.path.join(base_dir, "IVA_%m%y.TXT")).date()

        current_document = None

        bar = ProgressBar(u"cargando iva  %s" % periodo_iva.strftime("%m/%Y"), os.path.getsize(liva_filename))

        for line in liva:
            lineno += 1
            _readed += len(line)

            if not complete_line_pat.match(line) and not only_tax_line_pat.match(line):
                continue

            fecha = line[:10].strip()
            docletter = line[11:12].strip()
            docnumber = line[17:24].strip()
            doc_tipo = line[25:28].strip()
            cliname = line[29:51].strip()
            clicuit = line[52:65].strip()
            gravado = line[66:77].strip()
            tax_code = line[89:92].strip()
            impuesto = line[93:119].strip()
            total = line[121:133].strip()

            if complete_line_pat.match(line):
                fecha = datetime.strptime(fecha, "%d/%m/%Y").date()
                gravado = Decimal(convert2dp(gravado) if gravado else 0)
                doctype = config.documentos.get(doc_tipo)
                cuit = parse_cuit(clicuit)

                cliente = session.query(Cliente).filter(Cliente.nombre.startswith(cliname))\
                                                .filter(Cliente.cuit==cuit).first()
                if not cliente:
                    if docletter == u'B':
                        cliente = _venta_impersonal
                    cliente_direccion = None
                else:
                    cliname = cliente.nombre
                    cliente_direccion = cliente.direccion[:60]

                if current_document and current_document not in session:
                    session.add(current_document)

                try:
                    docnumber = int(docnumber)
                except ValueError:
                    _invalid_docnumber['%s:%s' % (liva_filename, lineno)] = line.strip()
                    continue

                try:
                    d = current_document = session.query(Documento).filter_by(tipo=doc_tipo,
                                                                              fecha=fecha,
                                                                              numero=int(docnumber)).one()
                    docmod += 1
                except NoResultFound:
                    d = current_document = Documento(tipo=doc_tipo, fecha=fecha, numero=int(docnumber))
                    docnew += 1

                d.neto = gravado
                d.fiscal = doctype['libro_iva']
                if periodo_iva.month == fecha.month and periodo_iva.year == fecha.year:
                    d.periodo_iva = None
                else:
                    d.periodo_iva = periodo_iva
                d.cliente = cliente
                d.cliente_nombre = cliname
                d.cliente_direccion = cliente_direccion
                d.cliente_cuit = cuit

                monto = Decimal(convert2dp(impuesto) if impuesto else 0)
                t = Tasa(nombre=tax_code, monto=monto, documento=current_document)
                session.add(t)
                tcount += 1
            else:
                if current_document is None:
                    _no_related_doc["%s:%s" % (liva_filename, lineno)] = line.strip()
                    continue
                elif current_document.neto != Decimal(convert2dp(gravado) if gravado else 0):
                    _bad_gravado_doc["%s:%s" % (liva_filename, lineno)] = line.strip()
                    continue
                monto = Decimal(convert2dp(impuesto) if impuesto else 0)
                t = Tasa(nombre=tax_code, monto=monto, documento=current_document)
                session.add(t)
                tcount += 1
            bar.update_state(_readed)
        bar.finish()

        if current_document and current_document not in session:
            session.add(current_document)
        liva.close()
        session.commit()
        #info(u"Se cargaron datos del periodo %s (%d)" % (periodo_iva.strftime("%m/%Y"), tcount))

    nl()
    info(u"Se crearon %d documentos nuevos y se completaron %s documentos en la base de\n"
         u"datos desde %d archivos de libro de IVA\n" % (docnew, docmod, fileno))

    if _no_related_doc:
        warn(u"Impuestos sin documento relacionado (%s)" % len(_no_related_docs))
        out = codecs.open(os.path.join(outpath, "imp_libro_iva_no_related_doc.txt"), "w", encoding="utf-8")
        for key, value in sorted(_no_related_doc.iteritems()):
            out.write(u"%s: %s\n" % (key, value))
        out.close()

    if _bad_gravado_doc:
        warn(u"Impuestos con valor gravado inválido (%s)" % len(_bad_gravado_doc))
        out = codecs.open(os.path.join(outpath, "imp_libro_iva_bad_gravado_doc.txt"), "w", encoding="utf-8")
        for key, value in sorted(_bad_gravado_doc.iteritems()):
            out.write(u"%s: %s\n" % (key, value))
        out.close()

    if _invalid_docnumber:
        warn(u"Documentos con número inválido (%s)" % len(_invalid_docnumber))
        out = codecs.open(os.path.join(outpath, "imp_libro_iva_invalid_docnumber.txt"), "w", encoding="utf-8")
        for key, value in sorted(_invalid_docnumber.iteritems()):
            out.write(u"%s: %s\n" % (key, value))
        out.close()

# Fancy progress ala (pacman) ArchLinux
_colors = {
    'BOLD':   u'\x1b[01;1m',
    'RED':    u'\x1b[01;31m',
    'GREEN':  u'\x1b[01;32m',
    'YELLOW': u'\x1b[01;33m',
    'BLUE':   u'\x1b[01;34m',
    'PINK':   u'\x1b[01;35m',
    'CYAN':   u'\x1b[01;36m',
    'NORMAL': u'\x1b[0m',
    'cursor_on':  u'\x1b[?25h',
    'cursor_off': u'\x1b[?25l',
}

class ProgressBar(object):
    indicator = '\x1b[K%s%s%s\r'
    end_color = _colors['NORMAL']

    def __init__(self, name, total, stream=stdout, suffix=True,
                 color='BOLD', sec_color='BLUE', interval=0.1):
        self.name = name
        self.total = total
        self.start_color = _colors.get(color, _colors['NORMAL'])
        self.sec_start_color = _colors.get(sec_color, _colors['NORMAL'])
        self._interval = interval
        self._last_update = 0
        self._stream = stream
        self._cast = float if suffix and (total > 2040) else type(total)
        self._total_n = self._calc_total_len(total, suffix)
        self._color_n = 2*len(self.start_color) + len(self.sec_start_color) + 3*len(self.end_color)
        if suffix:
            self._format_qty = self._suffix_format_qty
        else:
            self._format_qty = self._simple_format_qty

        self.start_timer()

    def update_state(self, current):
        if time.time() < (self._last_update + self._interval):
            return
        return self.force_update_state(current)

    def finish(self):
        self.force_update_state(self.total, eta=False)
        self._stream.write(u'\n')
        self._stream.flush()

    def force_update_state(self, current, eta=True):
        self._last_update = time.time()
        n = self._total_n
        q = self._format_qty
        sc, ssc, ec = self.start_color, self.sec_start_color, self.end_color
        total = self.total

        pc = (100.*current)/self.total
        eta = self.get_elapsed_time(current=(current if eta else None))
        left = u"%s*%s %s%-22s%s  %s %s  %s [" % (ssc, ec, sc, self.name[:22], ec, q(current), q(total), eta)
        right = u'] %s%3d%%%s' % (sc, pc, ec)

        cols = 22

        ratio = int((cols*current)/total)
        bar = (u'#'*ratio+'-'*cols)[:cols]
        self._stream.write(self.indicator % (left, bar, right))
        self._stream.flush()

    def get_elapsed_time(self, current=None, start=None):
        if start is None: start = self._start
        delta = datetime.now() - start
        if current:
            # estimated time averange
            delta = ((self.total*delta)/current) - delta
        return unicode(delta).split('.')[0]

    def _simple_format_qty(self, qty):
        return (u"%%%dd" % self._total_n) % qty

    def _suffix_format_qty(self, qty):
        sizes = ['K', 'M', 'G', 'T']
        idx = 0
        size = ' '
        while qty > 2048.0:
            qty /= 1024.0
            size = sizes[idx]
            idx += 1

        if self._cast is int: d = '%dd' % self._total_n
        elif self._cast is float: d = '%d.1f' % self._total_n
        else: d = 's'
        return ((u"%%%s%%s" % d) % (self._cast(qty), size)).replace(u".", u",")

    def _calc_total_len(self, total, suffix=False):
        if suffix:
            if self._cast is int:
                return 4
            elif self._cast is float:
                return 6
        return len(str(total))

    def start_timer(self):
        self._start = datetime.now()

NORMAL = _colors['NORMAL']
BOLD = _colors['BOLD']
BLUE = _colors['BLUE']
PINK = _colors['PINK']

INFO = _colors['GREEN']
WARNING = _colors['YELLOW']
ERROR = _colors['RED']

def info(s):
    stdout.write(INFO + u'INFO:' + NORMAL + u" " + s + u"\n")
    stdout.flush()

def warn(s):
    stdout.write(WARNING + u'WARNING:' + NORMAL + u" " + s + u"\n")
    stdout.flush()

def error(s):
    stdout.write(ERROR + u'ERROR:' + NORMAL + u" " + s + u"\n")
    stdout.flush()
    sys.exit(1)

def msg(s):
    stdout.write(BLUE + u'::' + NORMAL + u' ' + BOLD + s + NORMAL + u'\n')
    stdout.flush()

def ptime(s, l=u'tiempo'):
    stdout.write(PINK + u'**' + NORMAL + u' ' + l + u': ' + s + u'\n')

def nl(c=1):
    while c > 0:
        stdout.write(u"\n")
        c -= 1
    stdout.flush()

def main():

    parser = OptionParser(u"uso: %prog [opciones]")
    parser.add_option("-b", "--base-path", dest="basepath", default="./",
                      help=u"directorio base [default: %default]")
    parser.add_option("-o", "--out-path", dest="outpath", default="./migration_results",
                      help=u"directorio donde dejar los archivos de resultados [default: %default]")

    (options, args) = parser.parse_args()
    if len(args) != 0:
        error(u"número incorrecto de argumentos")

    path = os.path.abspath(os.path.expanduser(options.basepath))
    outpath = os.path.abspath(os.path.expanduser(options.outpath))
    if not os.path.isdir(path):
        error(BOLD + u"%s"%path + NORMAL + u" no es un directorio")
    if not os.path.isdir(outpath):
        try:
            os.makedirs(outpath)
        except OSError as e:
            error(u"No se puede crear el directorio " + BOLD + u'%s'%outpath + NORMAL + u'\n' + unicode(e))

    d = dict([
        ('artnombre', 'articulo_nombre_precio.txt'),
        ('artagrupacion', 'articulo_agrupacion.txt'),
        ('artvigencia', 'articulo_vigencia.txt'),
        ('artexistencia', 'articulo_existencia.txt'),
        ('artmovimientos', 'articulo_movimientos.txt'),
        ('ternombre', 'terceros_nombre.txt'),
        ('tercodiva', 'terceros_codiva.txt'),
        ('terdomicilio', 'terceros_domicilio.txt')
    ])

    not_found = []
    for var, name in d.items():
        fname = os.path.join(path, name)
        if os.path.isfile(fname):
            d[var] = fname
        else:
            not_found.append(fname)

    if not_found:
        error(u"Faltan archivos de importación:\n\n" +
              u"\n".join([ERROR+u'* '+NORMAL+nf for nf in not_found]) + u'\n')

    config = load_config()
    setup_db(config.database_uri)
    session = Session()

    msg(u"importando archivos desde %s ..." % path)
    nl()

    report_time(migrar_articulos, (session, outpath, d['artnombre'], d['artagrupacion'], d['artvigencia']))
    report_time(migrar_existencias, (session, outpath, d['artexistencia']))
    report_time(migrar_movimientos, (session, outpath, config, d['artmovimientos']))
    report_time(migrar_terceros, (session, outpath, config, d['ternombre'], d['tercodiva'], d['terdomicilio']))
    report_time(migrar_libro_iva, (session, outpath, config, path))

    session.close()

    nl()
    msg(u"los archivos residuales se almacenaron en %s" % outpath)
    nl()


if __name__ == '__main__':
    main()
