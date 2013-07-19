#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generar una copia en PDF de un presupuesto almacenado en la base de datos.
"""

import sys
import nobix.widget # Fix circular dependency import
from nobix.db import setup_db, Session
from nobix.models import Documento
from nobix.config import load_config, get_current_config
from nobix.printers import FilePrinter

session = Session()

def init_db():
    config = load_config()
    setup_db(config.database_uri)

def build_document(doc_number):
    # llamar al metodo print_doc() de la instancia impresora
    # el metodo print_doc recibe dos argumentos doc_data y opts
    options = {}

    # 1) Obtener el documento solicitado
    document = Documento.query.filter(Documento.tipo==u'PRE')\
                              .filter(Documento.numero==doc_number)\
                              .first()

    options['vendedor'] = '%(codigo)s - %(nombre)s' % {
        'codigo': document.vendedor,
        'nombre': get_current_config().vendedores.get(document.vendedor)['nombre'],
    }

    print options

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    init_db()
    build_document(int(args[0]))

if __name__ == '__main__':
    main()
