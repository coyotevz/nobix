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

punto_venta = u'1'

sucursales = {
    u'1': u"Ciudad",
    u'3': u"Godoy Cruz",
}

usar_nuevo_algoritmo = False
case_sensitive_search = True

manager_hostname = 'cocodrilo'
manager_port = 18280

documentos = {
    u'FAA': {
        'nombre': u"Factura A",
        'discrimina_iva': True,
        'needs_cuit': True,
        'has_body': True,
        'stock': u'salida',
        'max_amount': 25000,
        'allowed_custom_items': True,
        'docnumber_generation': u'<external>',
        'printer': u'Hasar615',
        'print_docletter': u'A',
        'libro_iva': u'+venta',
        'default_tax': u'V21',
        'allowed_taxes': (u'V21',),
        'print_max_rows': hasar_max_rows,
    },

    u'NFA': {
        'nombre': u"Nuestra Factura A",
        'needs_cuit': True,
        'has_body': False,
        'libro_iva': u'+venta',
        'default_tax': u'V21',
        'allowed_taxes': (u'V21',),
    },

    u'FAC': {
        'nombre': u"Factura B",
        'has_body': True,
        'stock': u'salida',
        'max_amount': 25000,
        'allowed_custom_items': True,
        'docnumber_generation': u'<external>',
        'printer': u'Hasar615',
        'print_docletter': u'B',
        'libro_iva': u'+venta',
        'default_tax': u'V21',
        'allowed_taxes': (u'V21',),
        'print_max_rows': hasar_max_rows,
    },

    u'NFB': {
        'nombre': u"Nuestra Factura B",
        'has_body': False,
        'libro_iva': u'+venta',
        'default_tax': u'V21',
        'allowed_taxes': (u'V21',),
    },

    u'PRE': {
        'nombre': u"Presupuesto",
        'allowed_custom_items': True,
        'printer': ('HP LaserJet 1020', 'PDF Printer'),
        'print_template': basic_template,
        'print_show_logo': True,
        'print_show_footer_legend': True,
        #'print_copies': 2, # Solo cuando se imprime
        'print_copies': 1,
        'print_docname': u"Presupuesto",
        'print_vendedor_fmt': u'%(codigo)s - %(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    u'PRF': {
        'nombre': u"Pre Firmado",
        'allowed_custom_items': True,
        'printer': 'HP LaserJet 1020',
        'print_template': basic_template,
        'print_show_logo': True,
        'print_show_footer_legend': True,
        'print_copies': 2, # Solo cuando se imprime
        'print_docname': u"Presupuesto FF",
        'print_vendedor_fmt': u'%(codigo)s - %(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    u'ENV': {
        'nombre': u"Envio a GC",
        'allowed_custom_items': True,
        'printer': 'HP LaserJet 1020',
        'print_template': basic_template,
        'print_show_logo': True,
        'print_show_footer_legend': True,
        'print_copies': 2, # Solo cuando se imprime
        'print_docname': u"Envio",
        'print_vendedor_fmt': u'%(codigo)s - %(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    u'REM': {
        'nombre': u"Presupuesto II",
        'printer': 'HP LaserJet 1020',
        'stock': 'salida',
        'min_amount': 333,
        'print_template': basic_template,
        'print_copies': 2,
        'print_docname': u"Presupuesto.",
        'print_max_rows': pdf_max_rows,
    },

    u'ENT': {
        'nombre': u"Entrada",
        'need_pass': True,
        'stock': u'entrada',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': u'%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    u'SAL': {
        'nombre': u"Salida",
        'need_pass': True,
        'stock': u'salida',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': u'%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    u'AJU': {
        'nombre': u"Ajuste",
        'need_pass': True,
        'stock': u'ajuste',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': u'%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    u'INV': {
        'nombre': u"Inventario",
        'need_pass': True,
        'stock': u'inventario',
        'printer': (None, 'HP LaserJet 1020'),
        'print_template': basic_template,
        'print_vendedor_fmt': u'%(nombre)s',
        'print_max_rows': pdf_max_rows,
    },

    u'NNC': {
        'nombre': u"Nuestra Nota de Crédito",
        'has_body': False,
        'need_pass': True,
        'libro_iva': u'-venta',
        'default_tax': u'V21',
        'allowed_taxes': ('V21',),
    },

    u'NCA': {
        'nombre': u"Nuestra Nota de Crédito A",
        'has_body': False,
        'need_pass': True,
        'needs_cuit': True,
        'libro_iva': u'-venta',
        'default_tax': u'V21',
        'allowed_taxes': ('V21',),
    },

    u'VFA': {
        'nombre': u"Vuestra Factura A",
        'has_body': False,
        'need_pass': True,
        'tercero': u'P',
        'libro_iva': u'+compra',
        'default_tax': u'C21',
        'allowed_taxes': (u'C21', u'C10', u'C27', u'C96', u'PIB', u'PI2', u'PI6'),
    },

    u'VNC': {
        'nombre': u"Vuestra Nota de Crédito",
        'has_body': False,
        'need_pass': True,
        'tercero': u'P',
        'libro_iva': u'-compra',
        'default_tax': u'C21',
        'allowed_taxes': (u'C21', u'C10', u'C27', u'C96', u'PIB', u'PI2', u'PI6'),
    },

    u'VND': {
        'nombre': u"Vuestra Nota de Débito",
        'has_body': False,
        'need_pass': True,
        'tercero': u'P',
        'libro_iva': u'+compra',
        'default_tax': u'C21',
        'allowed_taxes': (u'C21', u'C10', u'C27', u'C96', u'PIB', u'PI2', u'PI6'),
    },

    # Prueba de etiquetadora
    u'E1': {
        'nombre': u"Etiqueta 38x20x2",
        'allowed_custom_items': True,
        'printer': ('Tag Printer', 'Remote Tag Printer'),
        'print_size': {'width': 38, 'height': 20, 'gap': 2, 'paper': 'E1'},
        'allowed_users': [u'18', u'19'],
    },

    u'REP': {
        'nombre': u"Remito Preimpreso",
        'allowed_custom_items': True,
        'printer': ('HP LaserJet 1020', 'PDF Printer Remitos'),
        'print_template': remito_template,
        'print_max_rows': remito_max_rows,
        'print_copies': 2,
        'has_body': True,
        'need_pass': False,
    },

    # Documentos Especiales, no son editables solo se utilizan para configurar algunos parametros
    u'AGRUP_LISTPRINT': {
        'nombre': u"Lista de Artículos por Agrupación",
        'grouped': u"agrupacion",
        'columns': [
            (u"Código", "codigo", 14, "left", "unicode"),
            (u"Descripción", "descripcion", 40, "left", "unicode"),
            (u"Vigencia", "vigencia", 10, "center", "date"),
            (u"Precio", "precio", 10, "right", "decimal"),
            (None, None, 4, None, None),
            (u"Existencia", "existencia", 10, "right", "decimal"),
        ],
        'docnumber_generation': None,
        'printer': u'HP LaserJet 1020',
        'print_template': list_template,
        'print_docname': u"listado_por_agrupacion",
        'print_show_footer_legend': True,
        'print_vendedor_fmt': u'%(codigo)s - %(nombre)s',
        'print_max_rows': list_pdf_max_rows,
    },

    u'TEMP_LISTPRINT': {
        'nombre': u"Lista de Artículos",
        'grouped': None,
        'columns': [
            # Separador
            # (None, None, 4, None, None),
            (u"Código", "codigo", 14, "left", "unicode"),
            (u"Descripción", "descripcion", 40, "left", "unicode"),
            (u"Cantidad", "cantidad", 8, "right", "decimal"),
            (u"Precio", "precio", 8, "right", "decimal"),
            (u"Vigencia", "vigencia", 8, "center", "date,%d/%m/%y"),
            (u"Agrupación", "agrupacion", 20, "left", "unicode"),
        ],
        'docnumber_generation': None,
        'printer': u'HP LaserJet 1020',
        'print_template': list_template,
        'print_docname': u"listado_de_articulos",
        'print_show_footer_legend': True,
        'print_vendedor_fmt': u'%(codigo)s - %(nombre)s',
        'print_max_rows': list_pdf_max_rows,
    },

    u'REPORT_LISTPRINT': {
        'nombre': u"Informe Mensual",
        'grouped': None,
        'columns': [
            (u"Código", "codigo", 14, "left", "unicode"),
            (u"Descripción", "descripcion", 40, "left", "unicode"),
            (u"Vigencia", "vigencia", 10, "center", "date"),
            (u"Precio", "precio", 10, "right", "decimal"),
        ],
        'docnumber_generation': None,
        'printer': u'HP LaserJet 1020',
        'print_template': list_template,
        'print_docname': u"informe_mensual",
        'print_show_footer_legend': True,
        'print_vendedor_fmt': u'%(codigo)s - %(nombre)s',
        'print_max_rows': list_pdf_max_rows,
    },
}


vendedores = {
    u'001': {'nombre': u'Mostrador'},
}

impuestos = {

    u'V21': {
        'nombre': u'IVA Venta 21%',
        'alicuota': u'21.00',
        'operacion': u'venta',
    },

    u'C10': {
        'nombre': u'IVA Compra 10,5%',
        'alicuota': u'10.50',
        'operacion': u'compra',
    },

    u'C21': {
        'nombre': u'IVA Compra 21%',
        'alicuota': u'21.00',
        'operacion': u'compra',
    },

    u'C27': {
        'nombre': u'IVA Compra 27%',
        'alicuota': u'27.00',
        'operacion': u'compra',
    },

    u'C96': {
        'nombre': u'Percepción IVA 3%',
        'alicuota': u'3.00',
        'operacion': u'compra',
    },

    u'PIB': {
        'nombre': u'Percepción IB 2,5%',
        'alicuota': u'2.50',
        'operacion': u'compra',
    },

    u'PI2': {
        'nombre': u'Percepción IB 2%',
        'alicuota': u'2.00',
        'operacion': u'compra',
    },

    u'PI6': {
        'nombre': u'Percepción IB BA 6%',
        'alicuota': u'6.00',
        'operacion': u'compra',
    }
}

customer_doctype_map = {
    0: {
        'nombre': u'Libreta de Enrolamiento',
        'nombre_corto': u'L.Enrolamiento',
        'label': u'L.E.',
    },
    1: {
        'nombre': u'Libreta Cívica',
        'nombre_corto': u'L.Civica',
        'label': u'L.C.',
    },
    2: {
        'nombre': u'Documento Nacional de Identidad',
        'nombre_corto': u'D.N.I.',
        'label': u'D.N.I.',
    },
    3: {
        'nombre': u'Pasaporte',
        'nombre_corto': u'Pasaporte',
        'label': u'PAS.',
    },
    4: {
        'nombre': u'Cédula de Identidad',
        'nombre_corto': u'C.Identidad',
        'label': u'C.I.',
    }
}


iva_resp_map = {
    u'C': {
        'nombre': u'Consumidor Final',
        'nombre_corto': u'Cons. Final',
        'label': u'CONSUMIDOR FINAL',
        'needs_cuit': False,
        'doctypes': [u'FAC', u'NFB', u'PRE', u'PRF', u'ENV', u'REM', u'ENT', u'SAL', u'AJU', u'INV', u'NNC', u'REP', u'E1'],
    },

    u'I': {
        'nombre': u'Responsable Inscripto',
        'nombre_corto': u'Resp. Inscripto',
        'label': u'RESPONSABLE INSCRIPTO',
        'needs_cuit': True,
        'doctypes': [u'FAA', u'NFA', u'PRE', u'PRF', u'REM', u'VFA', u'VNC', u'NCA', u'REP'],
    },

#    u'R': {
#        'nombre': u'Responsable No Inscripto',
#        'label': u'RESPONSABLE NO INSCRIPTO',
#        'needs_cuit': True,
#        'doctypes': [u'FAA', u'NFA', u'PRE', u'REM'],
#    },

    u'E': {
        'nombre': u'Exento',
        'nombre_corto': u'Exento',
        'label': u'EXENTO',
        'needs_cuit': True,
        'doctypes': [u'FAC', u'NFB', u'NNC', u'PRE', u'REM', u'REP'],
    },

    u'M': {
        'nombre': u'Monotributo',
        'nombre_corto': u'Monotributo',
        'label': u'MONOTRIBUTO',
        'needs_cuit': True,
        'doctypes': [u'FAC', u'NFB', u'PRE', u'REM'],
    },
}


impresoras = {
    u'HP LaserJet 1020': {
        'type': u"cups",
        #'cups_server': 't00.godoycruz.rioplomo-net.com.ar', # Sample
        'cups_server': None,
        'cups_port': None,
        'cups_user': None,
        'cups_password': None, # Not Tested
        'cups_printer': u'HP_LaserJet_1020',
        'cups_store': u'/tmp/nobix/cups_files',
        'cups_docpv': punto_venta,
    },

    u'Hasar615': {
        'type': u"fiscal",
        'fiscal_mode': u"spooler", # "daemon", "direct"
        'fiscal_input': u"/tmp/hasard",
        'fiscal_output': u"/tmp/hasard",
        'fiscal_timeout': 15,
        'fiscal_template': fiscal_template,
        'fiscal_vendedor_fmt': u'%(nombre)s',
        'fiscal_docpv': punto_venta,
        'fiscal_logfile': u"/var/log/nobix/hasar_responses.log",
    },

    u'PDF Printer': {
        'type': u"file",
        'file_store': u"/var/nobix/pdfs/",
        'file_filename': u"%(docname)s-%(date)s-%(time)s_%(codigo)s_%(docnumber)s.pdf",
        'file_docpv': punto_venta,
    },

    u'PDF Printer Remitos': {
        'type': u"file",
        'file_store': u"/var/nobix/remitos/",
        'file_filename': u"%(docname)s-%(date)s-%(time)s_%(codigo)s_%(docnumber)s.pdf",
        'file_docpv': punto_venta,
    },

    u'Tag Printer': {
        'type': u"tag",
        'tag_idVendor': 0x1664,
        'tag_idProduct': 0x013b,
    },

    u'Remote Tag Printer': {
        'type': u"remote-tag",
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

database_uri = "sqlite:////var/nobix/data/nobix.db"
#database_uri = "postgresql://nobix:nobix@localhost/nobix"
#database_uri = "mysql://nobix:nobix@localhost/nobix"

default_doctype = u"FAC"
default_vendedor = u"001"
default_cliente = u"1"

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
    u'1': {'codigo': 1, 'nombre': u'VENTA IMPERSONAL', 'domicilio': u'', 'localidad': u'',
          'codigo_postal': u'', 'cuit': u''},
    u'2': {'codigo': 2, 'nombre': u'VENTA IMPERSONAL A', 'domicilio': u'', 'localidad': u'',
           'codigo_postal': u'', 'cuit': u'', 'responsabilidad_iva': u'I'},
    u'13': {'codigo': 13, 'nombre': u'PEDIDO A RIO PLOMO', 'domicilio': u'', 'localidad': u'',
          'codigo_postal': u'', 'cuit': u''},
    u'14': {'codigo': 14, 'nombre': u'ENVIO A RIO PLOMO', 'domicilio': u'', 'localidad': u'',
          'codigo_postal': u'', 'cuit': u''},
    u'18': {'codigo': 18, 'nombre': u'RECIBIDO DE RIO PLOMO', 'domicilio': u'', 'localidad': u'',
          'codigo_postal': u'', 'cuit': u''},
    u'30': {'codigo': 30, 'nombre': u'MERCADERIA FALLADA', 'domicilio': u'', 'localidad': u'',
          'codigo_postal': u'', 'cuit': u''},
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
