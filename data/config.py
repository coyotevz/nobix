#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from os.path import join

hasar_max_rows = 30
pdf_max_rows = 36
remito_max_rows = 31
list_pdf_max_rows = 70

basic_template = join(sys.prefix, "share/nobix/templates/presupuesto.svg.mako")
list_template = join(sys.prefix, "share/nobix/templates/lista_agrupacion.svg.mako")
fiscal_template = join(sys.prefix, "share/nobix/templates/hasar615.dat.mako")
remito_template = join(sys.prefix, "share/nobix/templates/remito_preimpreso.svg.mako")

punto_venta = '1'

sucursales = {
    '1': "Ciudad",
    '3': "Godoy Cruz",
}

usar_nuevo_algoritmo = False
case_sensitive_search = True

manager_hostname = 'cocodrilo'
manager_port = 18280

documentos = {
    'FAA': {
        'nombre': "Factura A",
        'discrimina_iva': True,
        'needs_cuit': True,
        'has_body': True,
        'stock': 'salida',
        'max_amount': 25000,
        'allowed_custom_items': True,
        'docnumber_generation': '<external>',
        'printer': 'Hasar615',
        'print_docletter': 'A',
        'libro_iva': '+venta',
        'default_tax': 'V21',
        'allowed_taxes': ('V21','V10'),
        'print_max_rows': hasar_max_rows,
    },

    'NFA': {
        'nombre': "Nuestra Factura A",
        'needs_cuit': True,
        'has_body': False,
        'libro_iva': '+venta',
        'default_tax': 'V21',
        'allowed_taxes': ('V21','V10'),
    },

    'FAC': {
        'nombre': "Factura B",
        'has_body': True,
        'stock': 'salida',
        'max_amount': 25000,
        'allowed_custom_items': True,
        'docnumber_generation': '<external>',
        'printer': 'Hasar615',
        'print_docletter': 'B',
        'libro_iva': '+venta',
        'default_tax': 'V21',
        'allowed_taxes': ('V21',),
        'print_max_rows': hasar_max_rows,
    },

    'NFB': {
        'nombre': "Nuestra Factura B",
        'has_body': False,
        'libro_iva': '+venta',
        'default_tax': 'V21',
        'allowed_taxes': ('V21',),
    },

    'PRE': {
        'nombre': "Presupuesto",
        'allowed_custom_items': True,
        'printer': ('HP LaserJet 1020', 'PDF Printer'),
        'print_template': basic_template,
        'print_show_logo': True,
        'print_show_footer_legend': True,
        #'print_copies': 2, # Solo cuando se imprime
        'print_copies': 1,
        'print_docname': "Presupuesto",
        'print_vendedor_fmt': '%(codigo)s - %(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    'PRF': {
        'nombre': "Pre Firmado",
        'allowed_custom_items': True,
        'printer': 'HP LaserJet 1020',
        'print_template': basic_template,
        'print_show_logo': True,
        'print_show_footer_legend': True,
        'print_copies': 2, # Solo cuando se imprime
        'print_docname': "Presupuesto FF",
        'print_vendedor_fmt': '%(codigo)s - %(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    'ENV': {
        'nombre': "Envio a GC",
        'allowed_custom_items': True,
        'printer': 'HP LaserJet 1020',
        'print_template': basic_template,
        'print_show_logo': True,
        'print_show_footer_legend': True,
        'print_copies': 2, # Solo cuando se imprime
        'print_docname': "Envio",
        'print_vendedor_fmt': '%(codigo)s - %(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    'REM': {
        'nombre': "Presupuesto II",
        'printer': 'HP LaserJet 1020',
        'stock': 'salida',
        'min_amount': 333,
        'print_template': basic_template,
        'print_copies': 2,
        'print_docname': "Presupuesto.",
        'print_max_rows': pdf_max_rows,
    },

    'ENT': {
        'nombre': "Entrada",
        'need_pass': True,
        'stock': 'entrada',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': '%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    'SAL': {
        'nombre': "Salida",
        'need_pass': True,
        'stock': 'salida',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': '%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    'AJU': {
        'nombre': "Ajuste",
        'need_pass': True,
        'stock': 'ajuste',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': '%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    'INV': {
        'nombre': "Inventario",
        'need_pass': True,
        'stock': 'inventario',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': '%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    'NNC': {
        'nombre': "Nuestra Nota de Crédito",
        'has_body': False,
        'need_pass': True,
        'libro_iva': '-venta',
        'default_tax': 'V21',
        'allowed_taxes': ('V21','V10'),
    },

    'NCA': {
        'nombre': "Nuestra Nota de Crédito A",
        'has_body': False,
        'need_pass': True,
        'needs_cuit': True,
        'libro_iva': '-venta',
        'default_tax': 'V21',
        'allowed_taxes': ('V21','V10'),
    },

    'VFA': {
        'nombre': "Vuestra Factura A",
        'has_body': False,
        'need_pass': True,
        'tercero': 'P',
        'libro_iva': '+compra',
        'default_tax': 'C21',
        'allowed_taxes': ('C21', 'C10', 'C27', 'C96', 'PIB', 'PI2', 'PI6'),
    },

    'VNC': {
        'nombre': "Vuestra Nota de Crédito",
        'has_body': False,
        'need_pass': True,
        'tercero': 'P',
        'libro_iva': '-compra',
        'default_tax': 'C21',
        'allowed_taxes': ('C21', 'C10', 'C27', 'C96', 'PIB', 'PI2', 'PI6'),
    },

    'VND': {
        'nombre': "Vuestra Nota de Débito",
        'has_body': False,
        'need_pass': True,
        'tercero': 'P',
        'libro_iva': '+compra',
        'default_tax': 'C21',
        'allowed_taxes': ('C21', 'C10', 'C27', 'C96', 'PIB', 'PI2', 'PI6'),
    },

    # Prueba de etiquetadora
    'E1': {
        'nombre': "Etiqueta 38x20x2",
        'allowed_custom_items': True,
        'printer': ('Tag Printer', 'Remote Tag Printer'),
        'print_size': {'width': 38, 'height': 20, 'gap': 2, 'paper': 'E1'},
        'allowed_users': ['18', '19'],
    },

    'REP': {
        'nombre': "Remito Preimpreso",
        'allowed_custom_items': True,
        'printer': ('HP LaserJet 1020', 'PDF Printer Remitos'),
        'print_template': remito_template,
        'print_max_rows': remito_max_rows,
        'print_copies': 2,
        'has_body': True,
        'need_pass': False,
    },

    # Documentos Especiales, no son editables solo se utilizan para configurar algunos parametros
    'AGRUP_LISTPRINT': {
        'nombre': "Lista de Artículos por Agrupación",
        'grouped': "agrupacion",
        'columns': [
            ("Código", "codigo", 14, "left", "unicode"),
            ("Descripción", "descripcion", 40, "left", "unicode"),
            ("Vigencia", "vigencia", 10, "center", "date"),
            ("Precio", "precio", 10, "right", "decimal"),
            (None, None, 4, None, None),
            ("Existencia", "existencia", 10, "right", "decimal"),
        ],
        'docnumber_generation': None,
        'printer': 'HP LaserJet 1020',
        'print_template': list_template,
        'print_docname': "listado_por_agrupacion",
        'print_show_footer_legend': True,
        'print_vendedor_fmt': '%(codigo)s - %(nombre)s',
        'print_max_rows': list_pdf_max_rows,
    },

    'TEMP_LISTPRINT': {
        'nombre': "Lista de Artículos",
        'grouped': None,
        'columns': [
            # Separador
            # (None, None, 4, None, None),
            ("Código", "codigo", 14, "left", "unicode"),
            ("Descripción", "descripcion", 40, "left", "unicode"),
            ("Cantidad", "cantidad", 8, "right", "decimal"),
            ("Precio", "precio", 8, "right", "decimal"),
            ("Vigencia", "vigencia", 8, "center", "date,%d/%m/%y"),
            ("Agrupación", "agrupacion", 20, "left", "unicode"),
        ],
        'docnumber_generation': None,
        'printer': 'HP LaserJet 1020',
        'print_template': list_template,
        'print_docname': "listado_de_articulos",
        'print_show_footer_legend': True,
        'print_vendedor_fmt': '%(codigo)s - %(nombre)s',
        'print_max_rows': list_pdf_max_rows,
    },

    'REPORT_LISTPRINT': {
        'nombre': "Informe Mensual",
        'grouped': None,
        'columns': [
            ("Código", "codigo", 14, "left", "unicode"),
            ("Descripción", "descripcion", 40, "left", "unicode"),
            ("Vigencia", "vigencia", 10, "center", "date"),
            ("Precio", "precio", 10, "right", "decimal"),
        ],
        'docnumber_generation': None,
        'printer': 'HP LaserJet 1020',
        'print_template': list_template,
        'print_docname': "informe_mensual",
        'print_show_footer_legend': True,
        'print_vendedor_fmt': '%(codigo)s - %(nombre)s',
        'print_max_rows': list_pdf_max_rows,
    },
}


vendedores = {
    '001': {'nombre': 'Mostrador'},
    '18': {'nombre': 'Vendedor 18', 'pass': "a6a3956bdf73824f41d1d8e69cde4c2f"},
}

impuestos = {

    'V10': {
        'nombre': 'IVA Venta 10,5%',
        'alicuota': '10.50',
        'operacion': 'venta',
    },

    'V21': {
        'nombre': 'IVA Venta 21%',
        'alicuota': '21.00',
        'operacion': 'venta',
    },

    'C10': {
        'nombre': 'IVA Compra 10,5%',
        'alicuota': '10.50',
        'operacion': 'compra',
    },

    'C21': {
        'nombre': 'IVA Compra 21%',
        'alicuota': '21.00',
        'operacion': 'compra',
    },

    'C27': {
        'nombre': 'IVA Compra 27%',
        'alicuota': '27.00',
        'operacion': 'compra',
    },

    'C96': {
        'nombre': 'Percepción IVA 3%',
        'alicuota': '3.00',
        'operacion': 'compra',
    },

    'PIB': {
        'nombre': 'Percepción IB 2,5%',
        'alicuota': '2.50',
        'operacion': 'compra',
    },

    'PI2': {
        'nombre': 'Percepción IB 2%',
        'alicuota': '2.00',
        'operacion': 'compra',
    },

    'PI6': {
        'nombre': 'Percepción IB BA 6%',
        'alicuota': '6.00',
        'operacion': 'compra',
    }
}

customer_doctype_map = {
    0: {
        'nombre': 'Libreta de Enrolamiento',
        'nombre_corto': 'L.Enrolamiento',
        'label': 'L.E.',
    },
    1: {
        'nombre': 'Libreta Cívica',
        'nombre_corto': 'L.Civica',
        'label': 'L.C.',
    },
    2: {
        'nombre': 'Documento Nacional de Identidad',
        'nombre_corto': 'D.N.I.',
        'label': 'D.N.I.',
    },
    3: {
        'nombre': 'Pasaporte',
        'nombre_corto': 'Pasaporte',
        'label': 'PAS.',
    },
    4: {
        'nombre': 'Cédula de Identidad',
        'nombre_corto': 'C.Identidad',
        'label': 'C.I.',
    }
}


iva_resp_map = {
    'C': {
        'nombre': 'Consumidor Final',
        'nombre_corto': 'Cons. Final',
        'label': 'CONSUMIDOR FINAL',
        'needs_cuit': False,
        'doctypes': ['FAC', 'NFB', 'PRE', 'PRF', 'ENV', 'REM', 'ENT', 'SAL', 'AJU', 'INV', 'NNC', 'REP', 'E1'],
    },

    'I': {
        'nombre': 'Responsable Inscripto',
        'nombre_corto': 'Resp. Inscripto',
        'label': 'RESPONSABLE INSCRIPTO',
        'needs_cuit': True,
        'doctypes': ['FAA', 'NFA', 'PRE', 'PRF', 'REM', 'VFA', 'VNC', 'NCA', 'REP'],
    },

#    u'R': {
#        'nombre': u'Responsable No Inscripto',
#        'label': u'RESPONSABLE NO INSCRIPTO',
#        'needs_cuit': True,
#        'doctypes': [u'FAA', u'NFA', u'PRE', u'REM'],
#    },

    'E': {
        'nombre': 'Exento',
        'nombre_corto': 'Exento',
        'label': 'EXENTO',
        'needs_cuit': True,
        'doctypes': ['FAC', 'NFB', 'NNC', 'PRE', 'REM', 'REP'],
    },

    'M': {
        'nombre': 'Monotributo',
        'nombre_corto': 'Monotributo',
        'label': 'MONOTRIBUTO',
        'needs_cuit': True,
        'doctypes': ['FAC', 'NFB', 'PRE', 'REM'],
    },
}


impresoras = {
    'HP LaserJet 1020': {
        'type': "cups",
        #'cups_server': 't00.godoycruz.rioplomo-net.com.ar', # Sample
        'cups_server': None,
        'cups_port': None,
        'cups_user': None,
        'cups_password': None, # Not Tested
        'cups_printer': 'HP_LaserJet_1020',
        'cups_store': '/tmp/nobix/cups_files',
        'cups_docpv': punto_venta,
    },

    'Hasar615': {
        'type': "fiscal",
        'fiscal_mode': "spooler", # "daemon", "direct"
        'fiscal_input': "/tmp/hasard",
        'fiscal_output': "/tmp/hasard",
        'fiscal_timeout': 15,
        'fiscal_template': fiscal_template,
        'fiscal_vendedor_fmt': '%(nombre)s',
        'fiscal_docpv': punto_venta,
        'fiscal_logfile': "/var/log/nobix/hasar_responses.log",
    },

    'PDF Printer': {
        'type': "file",
        'file_store': "/var/nobix/pdfs/",
        'file_filename': "%(docname)s-%(date)s-%(time)s_%(codigo)s_%(docnumber)s.pdf",
        'file_docpv': punto_venta,
    },

    'PDF Printer Remitos': {
        'type': "file",
        'file_store': "/var/nobix/remitos/",
        'file_filename': "%(docname)s-%(date)s-%(time)s_%(codigo)s_%(docnumber)s.pdf",
        'file_docpv': punto_venta,
    },

    'Tag Printer': {
        'type': "tag",
        'tag_idVendor': 0x1664,
        'tag_idProduct': 0x013b,
    },

    'Remote Tag Printer': {
        'type': "remote-tag",
        'remote-tag_idVendor': 0x1664,
        'remote-tag_idProduct': 0x013b,
        'remote-tag_addr': 'd01',
        'remote-tag_port': 9999,

    }
}

# Valid SQLite URL forms are:
#  sqlite:///:memory: (or, sqlite://)
#  sqlite:///relative/path/to/file.db
#  sqlite:////absolute/path/to/file.db
#
# postgresql://scott:tiger@localhost/mydatabase
# mysql://scott:tiger@localhost/foo
#
# ver: http://www.sqlalchemy.org/docs/dbengine.html#create-engine-url-arguments

#database_uri = "sqlite:////var/nobix/data/nobix.db"
database_uri = "postgresql://nobix-app:nobix-app@perseo:5433/nobix-test"
#database_uri = "mysql://nobix:nobix@localhost/nobix"

default_doctype = "FAC"
default_vendedor = "001"
default_cliente = "1"

finish_key = "end"

#clock_fmt = "%d/%m/%y %H:%M:%S" # Por defecto '%d/%m/%y %H:%M'
#clock_update_interval = 1 # Por defecto 60
#clock_width = 17 # Se calcula internamente si no se especifica

menu_items = [
    'maestro_stock',
    'maestro_clientes',
    'maestro_proveedores',
    'modificar_precios',
    'documentos_especiales',
    'ver_listados',
    'cierre_fiscal',
]

listados = [
    #'libro_iva_fechas',
    'libro_iva_periodo',
    #'subdiario_periodo',
    'subdiario_periodo_tree',
    #'subdiario_fechas',
    #'subdiario_fechas_tree',
    #'movimientos_fecha',
    #'historial_clientes',
    'listado_por_agrupacion',
    'resumen_periodo',
    #'resumen_fecha',
]

clientes_especiales = {
    '1': {'codigo': 1, 'nombre': 'VENTA IMPERSONAL', 'domicilio': '', 'localidad': '',
          'codigo_postal': '', 'cuit': ''},
    '2': {'codigo': 2, 'nombre': 'VENTA IMPERSONAL A', 'domicilio': '', 'localidad': '',
           'codigo_postal': '', 'cuit': '', 'responsabilidad_iva': 'I'},
    '13': {'codigo': 13, 'nombre': 'PEDIDO A RIO PLOMO', 'domicilio': '', 'localidad': '',
          'codigo_postal': '', 'cuit': ''},
    '14': {'codigo': 14, 'nombre': 'ENVIO A RIO PLOMO', 'domicilio': '', 'localidad': '',
          'codigo_postal': '', 'cuit': ''},
    '18': {'codigo': 18, 'nombre': 'RECIBIDO DE RIO PLOMO', 'domicilio': '', 'localidad': '',
          'codigo_postal': '', 'cuit': ''},
    '30': {'codigo': 30, 'nombre': 'MERCADERIA FALLADA', 'domicilio': '', 'localidad': '',
          'codigo_postal': '', 'cuit': ''},
}


color_palette = [
    # ui style
    ('inputbox.highlight', 'white', 'dark green'),

    ('header', 'dark gray', 'dark cyan'),
    # header cliente
    ('header.cliente', 'light cyan', 'dark cyan'),
    ('header.cliente.label', 'light cyan', 'dark cyan'),
    ('header.cliente.input', 'white', 'dark cyan'),
    ('header.cliente.input.focus', 'white', 'dark red'),
    ('header.cliente.name', 'dark gray', 'dark cyan'),
    ('header.cliente.resp', 'dark gray', 'dark cyan'),
    ('header.cliente.cuit', 'white', 'dark cyan'),

    # header vendedor
    ('header.vendedor', 'light cyan', 'dark cyan'),
    ('header.vendedor.label', 'light cyan', 'dark cyan'),
    ('header.vendedor.input', 'white', 'dark cyan'),
    ('header.vendedor.input.focus', 'white', 'dark red'),
    ('header.vendedor.name', 'dark gray', 'dark cyan'),

    # header tipo_documento
    ('header.tipo_documento', 'light cyan', 'dark cyan'),
    ('header.tipo_documento.label', 'light cyan', 'dark cyan'),
    ('header.tipo_documento.input', 'white', 'dark cyan'),
    ('header.tipo_documento.input.focus', 'white', 'dark red'),
    ('header.tipo_documento.name', 'dark gray', 'dark cyan'),

    # document
    ('document', 'black', 'dark cyan'),

    # document header
    ('document.header', 'dark blue,bold', 'light gray'),

    # document items
    ('document.item_list', 'white', 'dark cyan'),

    # document cached
    ('document.cached', 'white', 'light gray'),
    ('document.cached.vendedor', 'yellow,bold', 'light gray'),
    ('document.cached.doctype', 'white', 'light gray'),
    ('document.cached.cliente', 'dark gray', 'light gray'),
    ('document.cached.total', 'white', 'light gray'),

    # document product info
    ('document.info', 'white', 'light gray'),
    ('document.info.codigo', 'white', 'light gray'),
    ('document.info.descripcion', 'white', 'light gray'),
    ('document.info.vigencia.label', 'dark gray', 'light gray'),
    ('document.info.vigencia.value', 'white', 'light gray'),
    ('document.info.precio.label', 'dark gray', 'light gray'),
    ('document.info.precio.value', 'white', 'light gray'),
    ('document.info.existencia.label', 'dark gray', 'light gray'),
    ('document.info.existencia.value', 'white', 'light gray'),
    ('document.info.agrupacion.label', 'dark gray', 'light gray'),
    ('document.info.agrupacion.value', 'white', 'light gray'),
    ('document.info.proveedor.label', 'dark gray', 'light gray'),
    ('document.info.proveedor.value', 'white', 'light gray'),

    # document subtotal
    ('document.subtotal.label', 'light gray', 'dark blue'),
    ('document.subtotal.value', 'white', 'dark cyan'),

    # document descuento
    ('document.descuento.label', 'light gray', 'dark blue'),
    ('document.descuento.value', 'white', 'dark cyan'),

    # document iva
    ('document.iva.label', 'light gray', 'dark blue'),
    ('document.iva.value', 'white', 'dark cyan'),

    # document total
    ('document.total.label', 'white', 'dark red'),
    ('document.total.value', 'white', 'dark red'),

    # footer
    ('footer', 'light gray', 'black'),
    ('footer.key', 'light cyan', 'black', 'underline'),
    ('footer.title', 'white', 'black'),

    # Listado
    ('listado.title', 'white', 'dark red'),
    ('listado.title.important', 'yellow,bold', 'dark red'),
    ('listado.list_header', 'dark gray,bold', 'light gray'),
    ('listado.body', 'white', 'dark cyan'),
    ('listado.body.key', 'white,bold', 'dark cyan'),
    ('listado.body.important', 'dark gray', 'dark cyan'),
    ('listado.body.important.bold', 'dark gray,bold', 'dark cyan'),
    ('listado.footer', 'light cyan', 'dark blue'),
    ('listado.footer.key', 'light cyan,bold', 'dark blue'),
    ('listado.footer.important', 'white,bold', 'dark blue'),

    ('listado.tree.docline', 'white', 'dark cyan'),
    ('listado.tree.docline.focus', 'dark red,bold', 'dark cyan'),
    ('listado.tree.itemheader', 'dark gray', 'light gray'),
    ('listado.tree.itemheader.key', 'dark gray,bold', 'light gray'),
    ('listado.tree.itemheader.important', 'light blue,bold', 'light gray'),
    ('listado.tree.itemline', 'white', 'default'),
    ('listado.tree.itemline.focus', 'white,bold', 'dark green'),


    # dialogs
    ('dialog', 'white', 'dark blue'),
    ('dialog.title', 'dark red,bold', 'dark blue'),
    ('dialog.subtitle', 'dark red', 'dark blue'),
    ('dialog.button', 'black', 'light gray'),
    ('dialog.button.focus', 'white,bold', 'dark red', 'bold'),
    ('dialog.radio', 'dark gray', 'light gray'),
    ('dialog.radio.focus', 'white,bold', 'dark red', 'bold'),

    ('dialog.error', 'white', 'dark red'),
    ('dialog.error.title', 'yellow,bold', 'dark red'),
    ('dialog.error.important', 'yellow,bold', 'dark red'),

    ('dialog.warning', 'white', 'dark red'),
    ('dialog.warning.title', 'yellow,bold', 'dark red'),
    ('dialog.warning.important', 'yellow,bold', 'dark red'),
    ('dialog.warning.button', 'black', 'light gray'),
    ('dialog.warning.button.focus', 'white,bold', 'dark blue'),

    ('dialog.search', 'white', 'light gray'),
    ('dialog.search.title', 'white,bold', 'light gray'),
    ('dialog.search.subtitle', 'white', 'light gray'),
    ('dialog.search.input', 'white', 'dark gray'),
    ('dialog.search.item', 'black', 'light gray'),
    ('dialog.search.item.focus', 'white,bold', 'black'),
    ('dialog.search.item.selected', 'dark blue,bold', 'light gray'),
    ('dialog.search.item.focus.selected', 'dark red,bold', 'black'),

    ('dialog.password', 'white', 'dark red'),
    ('dialog.password.title', 'white,bold', 'dark red'),
    ('dialog.password.action', 'light red', 'dark red'),
    ('dialog.password.label', 'yellow', 'dark red'),
    ('dialog.password.value', 'white', 'dark red'),
    ('dialog.password.value.focus', 'white', 'black'),

    ('dialog.descuento', 'white', 'dark red'),
    ('dialog.descuento.title', 'yellow', 'dark red'),
    ('dialog.descuento.input', 'white', 'black'),

    ('dialog.maestock', 'white', 'dark blue'),
    ('dialog.maestock.title', 'white,bold', 'dark blue'),
    ('dialog.maestock.label', 'light cyan', 'dark blue'),
    ('dialog.maestock.input', 'white,bold', 'dark blue'),
    ('dialog.maestock.input.focus', 'white,bold', 'dark red'),
    ('dialog.maestock.action', 'light cyan,bold', 'dark blue'),
    ('dialog.maestock.instrucciones', 'default', 'dark blue'),
    ('dialog.maestock.key', 'white', 'dark red'),
    ('dialog.maestock.error', 'dark red,bold', 'dark blue'),

    ('dialog.maeter', 'white', 'dark blue'),
    ('dialog.maeter.title', 'white,bold', 'dark blue'),
    ('dialog.maeter.label', 'light cyan', 'dark blue'),
    ('dialog.maeter.input', 'white,bold', 'dark blue'),
    ('dialog.maeter.input.focus', 'white,bold', 'dark red'),
    ('dialog.maeter.action', 'light cyan,bold', 'dark blue'),
    ('dialog.maeter.instrucciones', 'default', 'dark blue'),
    ('dialog.maeter.key', 'white', 'dark red'),
    ('dialog.maeter.error', 'dark red,bold', 'dark blue'),
    ('dialog.maeter.group', 'white', 'light gray'),

    ('dialog.documento', 'default', 'dark blue'),
    ('dialog.documento.title', 'white,bold', 'dark blue'),
    ('dialog.documento.label', 'light cyan', 'dark blue'),
    ('dialog.documento.input', 'white,bold', 'dark blue'),
    ('dialog.documento.input.focus', 'white,bold', 'dark red'),
    ('dialog.documento.action', 'light cyan,bold', 'dark blue'),
    ('dialog.documento.key', 'white', 'dark red'),
    ('dialog.documento.tercero', 'light cyan,bold', 'dark blue'),
    ('dialog.documento.error', 'dark red,bold', 'dark blue'),
    ('dialog.documento.tax', 'white', 'dark blue'),
    ('dialog.documento.tax.label', 'white', 'dark blue'),
    ('dialog.documento.tax.input', 'white,bold', 'dark blue'),
    ('dialog.documento.tax.input.focus', 'white,bold', 'dark red'),

    ('dialog.pricemodifier', 'white', 'dark blue'),
    ('dialog.pricemodifier.title', 'white,bold', 'dark blue'),
    ('dialog.pricemodifier.label', 'light cyan', 'dark blue'),
    ('dialog.pricemodifier.input', 'white,bold', 'dark blue'),
    ('dialog.pricemodifier.input.focus', 'white,bold', 'dark red'),
    ('dialog.pricemodifier.action', 'light cyan,bold', 'dark blue'),
    ('dialog.pricemodifier.error', 'dark red,bold', 'dark blue'),

    ('dialog.listprinter', 'white', 'dark blue'),
    ('dialog.listprinter.title', 'white,bold', 'dark blue'),
    ('dialog.listprinter.label', 'light cyan', 'dark blue'),
    ('dialog.listprinter.input', 'white,bold', 'dark blue'),
    ('dialog.listprinter.input.focus', 'white,bold', 'dark red'),
    ('dialog.listprinter.action', 'light cyan,bold', 'dark blue'),
    ('dialog.listprinter.error', 'dark red,bold', 'dark blue'),

    ('dialog.printwizard', 'white', 'dark blue'),
    ('dialog.printwizard.title', 'white,bold', 'dark magenta'),
    ('dialog.printwizard.error', 'dark red,bold', 'dark blue'),
    ('dialog.printwizard.cliente.label', 'light cyan', 'dark blue'),
    ('dialog.printwizard.cliente.input', 'white,bold', 'dark blue'),
    ('dialog.printwizard.cliente.input.focus', 'white,bold', 'dark red'),
    ('dialog.printwizard.total.label', 'white,bold', 'dark blue'),
    ('dialog.printwizard.total.input', 'white,bold', 'brown'),
    ('dialog.printwizard.articulos.label', 'light cyan', 'dark blue'),
    ('dialog.printwizard.articulos.input', 'white,bold', 'dark blue'),

    ('dialog.chooseprinter', 'white', 'dark blue'),
    ('dialog.chooseprinter.title', 'yellow,bold', 'dark blue'),
    ('dialog.chooseprinter.button', 'black', 'light gray'),
    ('dialog.chooseprinter.button.focus', 'white,bold', 'dark red'),

    ('dialog.waitfiscal', 'white', 'dark blue'),
    ('dialog.waitfiscal.title', 'dark red,bold', 'white'),

    ('dialog.singlemessage', 'white', 'dark green'),

    ('dialog.chooselist', 'white', 'dark blue'),
    ('dialog.chooselist.title', 'yellow,bold', 'dark blue'),
    ('dialog.chooselist.button', 'black', 'light gray'),
    ('dialog.chooselist.button.focus', 'white,bold', 'dark red'),

    ('dialog.selectdate', 'white', 'dark blue'),
    ('dialog.selectdate.title', 'white,bold', 'dark blue'),
    ('dialog.selectdate.label', 'light cyan', 'dark blue'),
    ('dialog.selectdate.input', 'white,bold', 'dark blue'),
    ('dialog.selectdate.input.focus', 'white,bold', 'dark red'),
    ('dialog.selectdate.action', 'light cyan,bold', 'dark blue'),
    ('dialog.selectdate.error', 'dark red,bold', 'dark blue'),

    ('dialog.menu', 'light cyan', 'dark blue'),
    ('dialog.menu.title', 'white', 'dark blue'),
    ('dialog.menu.item', 'light cyan', 'dark blue'),
    ('dialog.menu.item.focus', 'dark blue,bold', 'light cyan'),

    ('dialog.about', 'white', 'dark blue'),
    ('dialog.about.title', 'dark blue,bold', 'white'),
    ('dialog.about.key', 'white,bold', 'dark blue'),
    ('dialog.about.lema', 'light cyan,bold', 'dark blue'),
]

if os.environ.get('TERM', 'linux') == 'linux':
    color_palette.extend([
        ('dialog.search.input', 'white', 'dark green'),
        ('dialog.menu.item.focus', 'dark blue', 'dark cyan'),
        ('dialog.about.title', 'dark blue,bold', 'light gray'),
        ('dialog.waitfiscal.title', 'dark red,bold', 'light gray'),
        ('dialog.search.item.selected', 'dark blue,bold', 'light gray'),
        ('dialog.search.item.focus.selected', 'dark red,bold', 'black'),
    ])
