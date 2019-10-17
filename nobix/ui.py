#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
from datetime import datetime, date, timedelta
from decimal import Decimal, getcontext, ROUND_HALF_UP
from collections import namedtuple, defaultdict
from dateutil.relativedelta import relativedelta
import operator
import itertools
import functools

from urwid import Text, Columns, Pile, Divider, SimpleListWalker, ListBox
from urwid import Padding, Filler, Frame, AttrMap, WidgetWrap, Button, CheckBox, RadioButton
from urwid import LineBox, GridFlow, command_map, connect_signal, emit_signal

from sqlalchemy import and_, or_
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

## Nobix imports #{{{
from nobix.widget import InputBox, IntegerInputBox, DateInputBox, DateSelectorBox
from nobix.widget import NumericInputBox as _NumericInputBox
from nobix.widget import NumericText as _NumericText
from nobix.widget import Dialog, Menu, SearchListItem, SearchDialog
from nobix.utils import show_error, show_warning, check_password, get_next_clinumber, get_next_docnumber
from nobix.utils import smart_unicode, validar_cuit, get_username, get_hostname, moneyfmt, message_waiter
from nobix.utils import CachedItem, DocumentData, ItemData
from nobix import printers, __version__ as VERSION
from nobix.db import Session
from nobix.models import Documento, Tasa, ItemDocumento, Cliente, Articulo, Cache
from nobix.config import get_current_config
#}}}

AGRUP_LIST_DOCTYPE = "AGRUP_LISTPRINT"

# Set context rounding
getcontext().rounding=ROUND_HALF_UP

q0 = Decimal('0')
q = Decimal('0.01')
q2 = Decimal('0.0001')

_numbers = list("0123456789")
_commands = ['right', 'left', 'end', 'home', 'up', 'down',
             'esc', 'enter', 'backspace', 'delete']
_finish_key = object()
_date_pattern = "%d/%m/%Y"

session = Session()

def highlight_focus_in(widget):
    widget.highlight = 0, len(widget._edit_text)

def restrict_horizontal(widget, key):#{{{
    p = widget.edit_pos
    if command_map[key] == 'cursor left':
        if p == 0: return None
    elif command_map[key] == 'cursor right':
        if p >= len(widget.edit_text): return None
    return key
#}}}
def restrict_moviment(widget, key):#{{{
    key = restrict_horizontal(widget, key)
    if key and command_map[key] in ('cursor up', 'cursor down'):
        return None
    return key
#}}}

def _create_cached_for_vendedor(vendedor_code):#{{{
    return Cache(vendedor=vendedor_code, username=get_username(), hostname=get_hostname())
#}}}
def _get_cached_for_vendedor_or_none(vendedor_code):#{{{

    try:
        return session.query(Cache).filter(and_(
            Cache.vendedor==unicode(vendedor_code),
            Cache.username==get_username(),
            Cache.hostname==get_hostname(),
        )).one()
    except NoResultFound:
        return None
#}}}
def _get_cached_for_vendedor(vendedor_code):#{{{
    cached = _get_cached_for_vendedor_or_none(vendedor_code)
    if cached is None:
        cached = _create_cached_for_vendedor(vendedor_code)
    else:
        session.delete(cached)
        session.commit()
    return cached
#}}}
def _remove_cached_for_vendedor(vendedor_code):#{{{
    cached = _get_cached_for_vendedor_or_none(vendedor_code)
    if cached is not None:
        session.delete(cached)
        session.commit()
#}}}

def choose_printer(printers):#{{{
    def _press(btn, user_data=None):
        d.dialog_result = user_data
        d.quit()
    buttons = [AttrMap(Button(p.name if hasattr(p, 'name') else p, on_press=_press, user_data=i),
                       'dialog.chooseprinter.button', 'dialog.chooseprinter.button.focus')
               for i, p in list(enumerate(printers)) + [(None, "Cancelar")]]
    pile = Padding(Pile(buttons), width=30, left=1, right=1)

    d = Dialog(pile, title="ELEGIR IMPRESORA", height=None, width=34,
            attr_style="dialog.chooseprinter",
            title_attr_style="dialog.chooseprinter.title",
        )

    return d.run()
#}}}
# Rewrite class constructor for default commons attributes
def NumericText(*args, **kwargs):#{{{
    opts = {
        'sep': kwargs.get('sep', ","),
    }
    kwargs.update(opts)
    return _NumericText(*args, **kwargs)
#}}}
def NumericInputBox(*args, **kwargs):#{{{
    opts = {
        'sep': kwargs.get('sep', ","),
        'align': kwargs.get('align', "right"),
        'max_digits': kwargs.get('max_digits', 2),
    }
    kwargs.update(opts)
    return _NumericInputBox(*args, **kwargs)
#}}}

class CodeBox(InputBox):#{{{

    signals = ['search-item', 'check-can-move', 'switch-to-line-item']

    def filter_input(self, text):
        return text.upper()

    def keypress(self, size, key):#{{{
        if emit_signal(self, 'check-can-move', self):
            key = restrict_horizontal(self, key)
            _can_finish = True
        else:
            key = restrict_moviment(self, key)
            _can_finish = False

        if key == _finish_key and _can_finish:
            return key

        if key and key not in (_numbers + _commands):
            if self.edit_pos == 0 or self.highlight is not None:
                if key == '-':
                    emit_signal(self, "switch-to-line-item")
                else:
                    self._emit("search-item", key)
                return key
        return self.__super.keypress(size, key)
    #}}}
#}}}
class TerceroBox(InputBox):#{{{

    signals = ['search-client', 'edit-cliente']

    def keypress(self, size, key):
        if key in string.letters:
            self._emit("search-client", "exact description", key)
            return key
        elif key == ".":
            self._emit("search-client", "word description")
            return key
        elif key == "*":
            self._emit("search-client", "cuit")
            return key
        elif key == 'f2':
            self._emit("edit-cliente", self.get_edit_text())
        if key:
            return self.__super.keypress(size, key)

    def filter_input(self, text):
        return text.upper()
#}}}
class ClienteBox(TerceroBox):#{{{

    def keypress(self, size, key):
        key = restrict_moviment(self, key)
        if key:
            return self.__super.keypress(size, key)
#}}}
class VendedorBox(InputBox):#{{{

    def valid_char(self, ch):
        return len(ch) == 1 and ch in "0123456789"

    def keypress(self, size, key):
        key = restrict_moviment(self, key)
        if key:
            return self.__super.keypress(size, key)
#}}}
class TipoDocumentoBox(InputBox):#{{{

    def filter_input(self, text):
        return text.upper()

    def keypress(self, size, key):
        key = restrict_moviment(self, key)
        if key:
            return self.__super.keypress(size, key)
#}}}
class InfoArticulo(WidgetWrap):#{{{

    def __init__(self):#{{{
        self.codigo = Text(u"", wrap='clip')
        self.descripcion = Text(u"", wrap='clip')
        self.precio = NumericText(align="left")
        self.existencia = NumericText()
        self.vigencia = Text(u"", wrap='clip')
        self.proveedor = Text(u"", wrap='clip')
        self.agrupacion = Text(u"", wrap='clip')

        row1 = Columns([
            ('fixed', 15, AttrMap(self.codigo, 'document.info.codigo')),
            #('fixed', 1, Divider()),
            ('fixed', 40, AttrMap(self.descripcion, 'document.info.descripcion')),
        ])

        row2 = Columns([
            ('fixed', 12, AttrMap(Text("Vigencia: ", align="right"), 'document.info.vigencia.label')),
            ('fixed', 10, AttrMap(self.vigencia, 'document.info.vigencia.value')),
            ('fixed', 3, Divider()),
            ('fixed', 12, AttrMap(Text("Precio: ", align="right"), 'document.info.precio.label')),
            ('fixed', 8, AttrMap(self.precio, 'document.info.precio.value')),
        ])

        row3 = Columns([
            ('fixed', 12, AttrMap(Text("Existencia: "), 'document.info.existencia.label')),
            ('fixed', 10, AttrMap(self.existencia, 'document.info.existencia.value')),
            ('fixed', 3, Divider()),
            ('fixed', 12, AttrMap(Text(u"Agrupación: "), 'document.info.agrupacion.label')),
            ('fixed', 20, AttrMap(self.agrupacion, 'document.info.agrupacion.value')),
        ])

        row4 = Columns([
            AttrMap(Text("Proveedor: "), 'document.info.proveedor.label'),
            AttrMap(self.proveedor, 'document.info.proveedor.value'),
            AttrMap(Text("Agrupación: "), 'document.info.agrupacion.label'),
            AttrMap(self.agrupacion, 'document.info.agrupacion.value'),
        ])

        pile = Pile([
            row1,
            row2,
            row3,
            #row4,
        ])

        self.__super.__init__(pile)
#}}}
    def update(self, obj):#{{{
        if isinstance(obj, Articulo):
            self.codigo.set_text(obj.codigo)
            self.descripcion.set_text(obj.descripcion)
            self.precio.set_value(obj.precio)
            self.existencia.set_value(obj.existencia)
            self.vigencia.set_text(obj.vigencia.strftime("%d/%m/%Y"))
            self.proveedor.set_text(obj.proveedor)
            self.agrupacion.set_text(obj.agrupacion)
        else:
            if isinstance(obj, basestring):
                self.codigo.set_text(obj[:15])
                self.descripcion.set_text(obj[15:])
            else:
                self.codigo.set_text(u"")
                self.descripcion.set_text(u"")
            self.precio.set_text(u"")
            self.existencia.set_text(u"")
            self.vigencia.set_text(u"")
            self.proveedor.set_text(u"")
            self.agrupacion.set_text(u"")
#}}}
    def reset(self):#{{{
        self.update(None)
#}}}
#}}}

class DocumentHeader(WidgetWrap):#{{{

    signals = ['cliente-set', 'tipo-documento-set']

    def __init__(self, doc_body):#{{{

        self._doc_body = doc_body
        connect_signal(doc_body, 'finish-document', self.finish_document)
        connect_signal(doc_body, 'print-temp-list', self.print_temp_list)

        self._cliente = None

        # left panel
        self.cliente_box = ClienteBox(max_length=5, align='right')
        connect_signal(self.cliente_box, 'focus-in', highlight_focus_in)
        connect_signal(self.cliente_box, 'edit-done', self.on_cliente_edit_done)
        connect_signal(self.cliente_box, 'search-client', self.on_cliente_search)
        connect_signal(self.cliente_box, 'edit-cliente', self.on_cliente_edit_record)
        connect_signal(self.cliente_box, 'edit-cancel', lambda *w: self._emit("cliente-set"))
        self.cliente_name = Text(u"", wrap='clip')
        self.cliente_cuit = Text(u"", wrap='clip')
        self.cliente_resp = Text(u"", wrap='clip')

        cliente_row_1 = Columns([
            ('fixed', 4, AttrMap(Text("Cl: "), 'header.cliente.label')),
            ('fixed', 6, AttrMap(self.cliente_box, 'header.cliente.input', 'header.cliente.input.focus')),
            ('fixed', 1, Divider()),
            AttrMap(self.cliente_name, 'header.cliente.name'),
        ])

        cliente_row_2 = Columns([
            ('fixed', 11, Text(u"")),
            AttrMap(self.cliente_resp, 'header.cliente.resp'),
            ('fixed', 13, AttrMap(self.cliente_cuit, 'header.cliente.cuit')),
        ])

        vbox1 = Pile([
            cliente_row_1,
            cliente_row_2,
        ])

        # right panel
        self.vendedor_box = VendedorBox(max_length=3, align='right')
        connect_signal(self.vendedor_box, 'focus-in', self.on_vendedor_focus_in)
        connect_signal(self.vendedor_box, 'edit-done', self.on_vendedor_edit_done)
        connect_signal(self.vendedor_box, 'edit-cancel', self.on_vendedor_edit_done)
        self.vendedor_name = Text(u"", wrap='clip')

        self.vendedor_row = Columns([
            ('fixed', 6, AttrMap(Text("Vend:"), 'header.vendedor.label')),
            ('fixed', 3, AttrMap(self.vendedor_box, 'header.vendedor.input', 'header.vendedor.input.focus')),
            ('fixed', 1, Divider()),
            AttrMap(self.vendedor_name, 'header.vendedor.name'),
        ])

        self.tipo_documento_box = TipoDocumentoBox(max_length=3)
        connect_signal(self.tipo_documento_box, 'focus-in', highlight_focus_in)
        connect_signal(self.tipo_documento_box, 'edit-done', self.on_tipo_documento_edit_done)
        connect_signal(self.tipo_documento_box, 'edit-cancel', self.on_tipo_documento_edit_done)
        self.tipo_documento_name = Text(u"", wrap='clip')

        self.tipo_documento_row = Columns([
            ('fixed', 6, AttrMap(Text("Docu:"), 'header.tipo_documento.label')),
            ('fixed', 4, AttrMap(self.tipo_documento_box, 'header.tipo_documento.input', 'header.tipo_documento.input.focus')),
            AttrMap(self.tipo_documento_name, 'header.tipo_documento.name'),
        ])

        vbox2 = Pile([
            AttrMap(self.vendedor_row, 'header.vendedor'),
            AttrMap(self.tipo_documento_row, 'header.tipo_documento'),
        ])

        self.hbox = Columns([
            AttrMap(vbox1, 'header.cliente'),
            ('fixed', 29, vbox2),
        ], dividechars=1)

        self.__super.__init__(self.hbox)
#}}}
    def _set_doctype_for_cliente(self):#{{{
        iva_resp_map = get_current_config().iva_resp_map
        resp = self._cliente.responsabilidad_iva if self._cliente is not None else None
        if resp in iva_resp_map:
            doctypes = iva_resp_map[resp]['doctypes']
            current_type = self.tipo_documento_box.get_edit_text()
            if (current_type == u"") or (current_type not in doctypes):
                self.rellenar_tipo_documento(doctypes[0])
#}}}
    def save_current_document(self):#{{{
        vendedor = self.vendedor_box.get_edit_text()
        if vendedor not in get_current_config().vendedores:
            return
        cached = _get_cached_for_vendedor_or_none(vendedor)

        if cached is None:
            cached = _create_cached_for_vendedor(vendedor)
            cached.doctype = self.tipo_documento_box.get_edit_text() or None
            cached.descuento = self._doc_body.get_descuento()
            cached.cliente_id = self._cliente.id if self._cliente is not None else None
            cached.total = self._doc_body.calcular_total()
            cached.items = self._doc_body.get_items_for_cache()

            session.add(cached)
            session.commit()
#}}}
    def load_stored_document_for_vendedor(self, vendedor):#{{{
        obj = _get_cached_for_vendedor(vendedor)

        self.rellenar_vendedor(vendedor)
        self.rellenar_tipo_documento(obj.doctype)
        self.rellenar_cliente(obj.cliente or 'default')

        # Check for valid documents found in config
        self._set_doctype_for_cliente()

        if obj.items:
            self._doc_body.set_items_from_cache(obj.items)
            self._doc_body.set_descuento(obj.descuento)

        return obj.doctype, obj.cliente
#}}}
    def rellenar_tipo_documento(self, doctype=None):#{{{
        if doctype is 'current':
            doctype = self.tipo_documento_box.get_edit_text() or None
        elif doctype is 'default':
            doctype = get_current_config().default_doctype

        if doctype is None:
            doctype = u""

        self.tipo_documento_box.set_edit_text(doctype)
        self._doc_body.set_tipo_documento(doctype)
        docname = get_current_config().documentos.get(doctype, {}).get('nombre', '')
        self.tipo_documento_name.set_text(docname)
#}}}
    def rellenar_vendedor(self, vendedor=None):#{{{
        if vendedor is 'current':
            vendedor = self.vendedor_box.get_edit_text() or None
        elif vendedor is 'default':
            vendedor = get_current_config().default_vendedor

        if vendedor is None:
            vendedor = u""

        self.vendedor_box.set_edit_text(vendedor)
        vnombre = get_current_config().vendedores.get(vendedor, {}).get('nombre', '')
        self.vendedor_name.set_text(vnombre)
#}}}
    def rellenar_cliente(self, cliente=None):#{{{
        if cliente is 'current':
            cliente = self.cliente_box.get_edit_text() or None
        elif cliente is 'default':
            cliente = get_current_config().default_cliente

        q = None
        if isinstance(cliente, basestring): # codigo cliente
            q = session.query(Cliente).filter(Cliente.codigo==int(cliente))
        elif isinstance(cliente, int): # cliente id
            q = session.query(Cliente).filter(Cliente.id==cliente)
        if q is not None:
            try:
                cliente = q.one()
            except NoResultFound:
                cliente = None

        codigo = u""
        nombre = u""
        resp_label = u""
        cuit = u""

        if isinstance(cliente, Cliente): # Cliente object
            cliente_id = cliente.id
            codigo = cliente.codigo
            nombre = cliente.nombre
            resp_label = get_current_config().iva_resp_map[cliente.responsabilidad_iva]['label']
            cuit = cliente.cuit or ''
        else:
            cliente = None

        self.cliente_box.set_edit_text(codigo)
        self.cliente_name.set_text(nombre)
        self.cliente_resp.set_text(resp_label)
        self.cliente_cuit.set_text(cuit)
        self._cliente = cliente
#}}}
    def reset_document(self):#{{{
        _remove_cached_for_vendedor(self.vendedor_box.edit_text)
        self.clear_document()
#}}}
    def clear_document(self):#{{{
        self.rellenar_vendedor(None)
        self.rellenar_tipo_documento(None)
        self.rellenar_cliente(None)

        self._doc_body.set_descuento(None)
        self._doc_body.clear_items()
        self._doc_body.add_item() # add empty item
        self._doc_body.reset_info()
#}}}
    def set_document_defaults(self):#{{{

        self.rellenar_vendedor('default')
        self.rellenar_tipo_documento('default')
        self.rellenar_cliente('default')
#}}}
    def renew_document(self):#{{{
        self.reset_document()
        self.set_document_defaults()
        self.vendedor_box._emit('edit-done', self.vendedor_box.get_edit_text())
#}}}
    def finish_document(self, body):#{{{
        doctype = self.tipo_documento_box.get_edit_text()
        doc_conf = get_current_config().documentos[doctype]
        resp_map = get_current_config().iva_resp_map

        raw_items = body.get_items()

        if len(raw_items) < 1:
            show_error("El documento no contiene items.")
            return

        cliente = self._cliente
        resp = cliente.responsabilidad_iva
        if doctype not in resp_map[resp]['doctypes']:
            show_error(["El tipo de cliente ", ('dialog.warning.important', resp_map[resp]['label']),
                " no es compatible con el tipo de documento ", ('dialog.warning.important', doctype),
                ".\n\nCambie el tipo de documento o el tipo de cliente."])
            return

        if doc_conf['need_pass']:
            permiso = check_password("Grabar %s" % doc_conf['nombre'])
            if not permiso:
                show_error("Ud. no tiene los permisos suficientes para emitir este documento.")
                return
            elif permiso == '<cancelled>':
                return

        def _valid_item(item):
            precio = item.precio if item.precio is not None else item.articulo.precio
            return (item.cantidad * precio) > Decimal(0)

        def _positive_valid_item(item):
            return item.cantidad >= Decimal(0)

        def _items_with_article(item):
            return isinstance(item.articulo, Articulo)

        if not doc_conf['allowed_custom_items']:
            allowed_items = filter(_items_with_article, raw_items)
            if len(raw_items) > len(allowed_items):
                show_error(u"En este tipo de documento no está permitida la venta de artículos"
                           u" sin código.\n\nElimine los artículos sin código.")
                return

        if doc_conf['stock'] not in ('ajuste', 'inventario'):
            positive_items = filter(_positive_valid_item, raw_items)
            if len(raw_items) > len(positive_items):
                show_error([u"Hay elementos inválidos: las ", ('dialog.warning.important', u"cantidades"),
                    u" no pueden ser ", ('dialog.warning.important', u"negativas"), u" por favor corrija ",
                    u"los items correspondientes."])
                return

        items_data = filter(_valid_item, raw_items)
        if len(raw_items) > len(items_data) and doc_conf['stock'] not in ('ajuste', 'inventario'):
            cont = show_warning([u"Hay elementos inválidos cuyo ", ('dialog.warning.important', u"precio"),
                u" y/o ", ('dialog.warning.important', u"cantidad"), u" son igual a cero.",
                u"\n\n", u"Estos elementos serán ", ('dialog.warning.important', u"eliminados"),
                u" automáticamente del documento.", u"\n"
                ], [(u"Continuar", True), (u"Volver", False)], focus_button=1)
            if cont is not True:
                return
            if len(items_data) < 1: # Recheck validity
                show_error(u"El documento no contiene items válidos.")
                return
        else:
            # Incluimos los items con cantidad 0 y precio 0
            items_data = raw_items

        if doc_conf['max_amount'] is not None and body.calcular_total() > Decimal(doc_conf['max_amount']):
            show_error(
                [u"El monto excede el máximo permitido (",
                 ('dialog.error.important', moneyfmt(Decimal(doc_conf['max_amount']), sep='.', dp=',')),
                 u")\n\n", ('dialog.error.important', u"Solución"),
                 u"\n* Reparta los items en distintos documentos manteniendose por debajo del máximo permitido.",
                 u"\n* Utilice fomularios manuales si lo anterior no es posible."])
            return

        if doc_conf['min_amount'] is not None and body.calcular_total() < Decimal(doc_conf['min_amount']):
            show_error(
                [u"El monto es inferior al permitido (",
                 ('dialog.error.important', moneyfmt(Decimal(doc_conf['min_amount']), sep='.', dp=',')),
                 u")\n\n", ('dialog.error.important', u"Solución"),
                 u"\n* Utilice otro tipo de documento para esta operación."])
            return

        if doc_conf['print_max_rows'] is not None and len(items_data) > doc_conf['print_max_rows']:
            citems, cmax = len(items_data), int(doc_conf['print_max_rows'])
            doc_qty = int(citems / cmax) + int(bool(citems % cmax))
            cont = show_warning([u"La cantidad de items excede la cantidad permitida para este documento.\n\n",
                u"El sistema repartirá automaticamente los items en la cantidad de documentos",
                u" que sean necesarios.\n\n", u"Total Documentos: ",
                ('dialog.warning.important', u"%d" % doc_qty), "\n"],
                [(u"Continuar", True), (u"Volver", False)], focus_button=0)
            if cont is not True:
                return

        # Collect data
        vendcode = self.vendedor_box.get_edit_text()
        vendedor = get_current_config().vendedores.get(vendcode)
        vendedor['codigo'] = vendcode
        descuento = body.get_descuento()
        total = body.calcular_total()
        doc_data = DocumentData(vendedor, doctype, cliente, descuento, total, items_data)

        if doctype == u'FAC' and cliente.responsabilidad_iva == u'C' and total > Decimal('9999.99'):
            pw = SpecialPrintWizard(doc_data, self)
        else:
            pw = PrintWizard(doc_data, self)
        pw.run()
#}}}
    def print_temp_list(self, body):#{{{
        items = body.get_items()
        if len(items) == 0:
            show_error(u"No puedo imprimir una lista vacía.")
            return None
        return temporary_list_printer(self.vendedor_name.get_text()[0], items)
#}}}
    def store_printed_document(self, printed_data, doc_data):#{{{
        # Aquí debemos Crear los items correspondientes en la base de datos y
        # relacionarlos con los artículos que correspondan, debemos tambien crear
        # un documento que se relacione con todos los items creados y tambien debemos
        # realizar el movimiento de stock si corresponde según el tipo de documento.
        doc_conf = get_current_config().documentos[doc_data.doctype]
        tax_name = doc_conf['default_tax']
        if tax_name:
            doc_tasa = get_current_config().impuestos[tax_name]
        else:
            doc_tasa = None

        doc_items = []
        for item in doc_data.items:
            if isinstance(item.articulo, Articulo):
                codigo = item.articulo.codigo
                descripcion = item.articulo.descripcion
                precio = item.precio if item.precio is not None else item.articulo.precio
                articulo = item.articulo
            elif isinstance(item.articulo, basestring):
                codigo = None
                descripcion = item.articulo
                precio = item.precio
                articulo = None
            else:
                raise RuntimeError("Unknown item type '%s'" % type(i.articulo).__name__)
            i = ItemDocumento(codigo=codigo, descripcion=descripcion, cantidad=item.cantidad,
                              precio=precio, articulo=articulo)

            doc_items.append(i)

        dir_data = map(printed_data.get, ['customer_domicilio', 'customer_localidad'])
        if all(dir_data):
            direccion = " - ".join(dir_data)
        else:
            direccion = u"".join(dir_data)
        if printed_data['customer_cp']:
            direccion += " (%s)" % printed_data['customer_cp']

        fiscal = doc_conf['libro_iva'] if bool(doc_conf['libro_iva']) else None

        if doc_tasa:
            alicuota = Decimal(doc_tasa['alicuota']) / 100
            neto = doc_data.total / (1+alicuota)
            tasas = [Tasa(nombre=doc_tasa['codigo'], monto=(doc_data.total - neto))]
            session.add_all(tasas)
            descuento = doc_data.descuento / (1+alicuota)
        else:
            tasas = []
            neto = doc_data.total
            descuento = doc_data.descuento

        if printed_data['customer_cuit'] != "00000000000":
            cliente_cuit = printed_data['customer_cuit']
        else:
            cliente_cuit = None
        document = Documento(tipo=doc_data.doctype, fecha=printed_data['docdate'],
                numero=int(printed_data['docnumber']), vendedor=doc_data.vendedor['codigo'],
                descuento=descuento, neto=neto, tasas=tasas, fiscal=fiscal,
                cliente=doc_data.cliente, items=doc_items,
                # Info extra cliente
                cliente_nombre=printed_data['customer_name'],
                cliente_direccion=direccion[:60],
                cliente_cuit=cliente_cuit)

        if doc_conf['stock'] == 'salida':
            for item in doc_items:
                if item.articulo is not None:
                    item.articulo.existencia -= item.cantidad
        elif doc_conf['stock'] in ('entrada', 'ajuste'):
            for item in doc_items:
                item.articulo.existencia += item.cantidad
        elif doc_conf['stock'] == 'inventario':
            for item in doc_items:
                item.articulo.existencia = item.cantidad

        session.add(document)
        session.commit()

        self.renew_document()
    #}}}
    def show_existing_cached(self):#{{{
        self._doc_body_frame = frame = self._doc_body._w
        self._temp_original_body = frame.body # AttrMap instance

        clist = session.query(Cache.vendedor,
                              Cache.doctype,
                              Cache.total,
                              Cache.cliente_id).filter(and_(
                                  Cache.username==get_username(),
                                  Cache.hostname==get_hostname(),
                              )).all()

        _cids = [l.cliente_id for l in clist]

        cli_dict = dict(session.query(Cliente.id, Cliente.nombre).filter(Cliente.id.in_(_cids)))

        cols = [Columns([
                    ('fixed', 3, AttrMap(Text(c.vendedor, align='right'), 'document.cached.vendedor')),
                    ('fixed', 3, AttrMap(Text(c.doctype), 'document.cached.doctype')),
                    AttrMap(Text(cli_dict[c.cliente_id], wrap='clip'), 'document.cached.cliente'),
                    ('fixed', 8, AttrMap(NumericText(c.total), 'document.cached.total')),
                ], dividechars=2) for c in clist]

        w = LineBox(ListBox(cols))
        w = Padding(AttrMap(w, 'document.cached'), align='center', width=('relative', 70))
        w = Filler(w, valign=('fixed top', 2), height=len(cols)+2)
        frame.body = w
#}}}
    def hide_existing_cached(self):#{{{
        # Restore original body
        if hasattr(self, '_doc_body_frame') and\
           hasattr(self, '_temp_original_body'):
            self._doc_body_frame.body = self._temp_original_body
#}}}

    ### Signals handlers ###

    def on_cliente_edit_done(self, widget, cod_cliente):#{{{
        try:
            c = session.query(Cliente).filter(Cliente.codigo==int(cod_cliente))\
                                      .filter(Cliente.relacion==u"C").one()
        except (NoResultFound, ValueError):
            return
        self.rellenar_cliente(c)

        # Check for valid documents found in config
        self._set_doctype_for_cliente()

        self._emit('cliente-set')
#}}}
    def on_cliente_search(self, widget, search_by=None, first_key=None):#{{{
        response = search_terceros(search_by=search_by, first_key=first_key)
        if response:
            self.rellenar_cliente(response[0])
            self._set_doctype_for_cliente()
            self._emit('cliente-set')
        return None
#}}}
    def on_cliente_edit_record(self, widget, cod_cliente):#{{{
        try:
            cod_cliente = unicode(int(cod_cliente))
        except ValueError:
            cod_cliente = "new"

        if cod_cliente in get_current_config().clientes_especiales.keys():
            cod_cliente = "new"

        cliente = maestro_terceros(filled_with=cod_cliente, once=True)

        if cliente is not None:
            self.rellenar_cliente(cliente)
            self._set_doctype_for_cliente()
            self._emit('cliente-set')
#}}}
    def on_vendedor_focus_in(self, widget):#{{{
        vendedor_code = widget.get_edit_text()
        if vendedor_code != u"" and vendedor_code in get_current_config().vendedores:
            self.save_current_document()
        # limpiar todos los campos
        self.clear_document()
        self.show_existing_cached()
        widget.set_edit_text(vendedor_code)
        highlight_focus_in(widget)
#}}}
    def on_vendedor_edit_done(self, widget, cod_vendedor=None):#{{{
        if cod_vendedor is None:
            cod_vendedor = self.vendedor_box.get_edit_text()
        self.hide_existing_cached()
        vendedor = get_current_config().vendedores.get(cod_vendedor, None)
        if vendedor:
            doctype, cliente = self.load_stored_document_for_vendedor(cod_vendedor)
            if doctype is None:
                self._w.widget_list[1].set_focus(1)
            else:
                self._emit('tipo-documento-set')
        else:
            show_error("El vendedor ingresado no existe, ingrese un usuario"
                       " correcto.")
#}}}
    def on_tipo_documento_edit_done(self, widget, tipo_documento=None):#{{{
        if tipo_documento is None:
            tipo_documento = self.tipo_documento_box.get_edit_text()
        doctype = get_current_config().documentos.get(tipo_documento, None)
        self.rellenar_tipo_documento(tipo_documento)
        if doctype:
            if doctype['has_body']:
                self._emit('tipo-documento-set')
            else:
                show_error("Este tipo de documento no se puede editar en esta pantalla.")
        else:
            show_error("El tipo de documento ingresado no existe, ingrese"
                       " un tipo de documento correcto.")
#}}}
#}}}
class DocumentItem(WidgetWrap):#{{{

    signals = ['calcular-total', 'item-done', 'delete-item',
               'check-modificar-precio', 'move-up', 'move-down']

    def __init__(self, obj=None):#{{{
        self._obj = None

        def _focus_out(w): self.calcular_total()
        def _item_done(w, c): self._emit("item-done")

        self.code_box = CodeBox(max_length=14)
        connect_signal(self.code_box, "edit-done", self.on_code_edit_done)
        connect_signal(self.code_box, "focus-in", highlight_focus_in)
        connect_signal(self.code_box, "focus-out", _focus_out)
        #connect_signal(self.code_box, "search-item", self.on_search_item)
        connect_signal(self.code_box, "check-can-move", self.on_check_can_move)

        self.descripcion = Text(u"", wrap='clip')

        self.cantidad = NumericInputBox(min_value=-9999.99, max_value=9999.99, default=1)
        self.cantidad.keypress = self._cantidad_keypress
        connect_signal(self.cantidad, "edit-done", _item_done)
        connect_signal(self.cantidad, "focus-in", highlight_focus_in)
        connect_signal(self.cantidad, "focus-out", _focus_out)

        self.precio = NumericInputBox(min_value=0, max_value=9999.99)
        self.precio.keypress = self._precio_keypress
        connect_signal(self.precio, "edit-done", _item_done)
        connect_signal(self.precio, "edit-cancel", lambda w: w.set_value(self._obj.precio))
        connect_signal(self.precio, "focus-in", highlight_focus_in)
        connect_signal(self.precio, "focus-out", _focus_out)

        self.total = NumericText()

        row = Columns([
            ('fixed', 14, self.code_box),
            ('fixed', 1, Divider()),
            self.descripcion,
            ('fixed', 1, Divider()),
            ('fixed', 8, self.cantidad),
            ('fixed', 1, Divider()),
            ('fixed', 8, self.precio),
            ('fixed', 1, Divider()),
            ('fixed', 9, self.total),
        ])

        self.__super.__init__(row)

        if obj:
            self.set_obj(obj)
#}}}
    def set_obj(self, obj):#{{{
        # obj == models.ItemDocumento or obj == models.Articulo
        self._obj = obj
        self.descripcion.set_text(obj.descripcion)
        self.precio.set_value(obj.precio)
        self.code_box.set_edit_text(obj.codigo)
        if isinstance(obj, ItemDocumento):
            self.cantidad.set_value(obj.cantidad)
        self.calcular_total()
#}}}
    def calcular_total(self):#{{{
        if self._obj is None:
            return
        total = self.cantidad.value * self.precio.value
        self.total.set_value(total)
        self._emit('calcular-total')
#}}}
    def _jump_to_cantidad(self):#{{{
        if not self.cantidad.edit_text:
            self.cantidad.set_value(1)
        self._w.set_focus(self.cantidad)
#}}}
    def _cantidad_keypress(self, size, key):#{{{
        # Monky patch
        wid = self.cantidad
        key = restrict_horizontal(wid, key)
        if not key:
            return
        if command_map[key] == 'cursor up':
            self._w.set_focus(self.code_box)
            return
        elif command_map[key] == 'cursor down':
            permiso = emit_signal(self, 'check-modificar-precio')
            if permiso is True:
                self._w.set_focus(self.precio)
            return
        return wid.__class__.keypress(wid, size, key)
#}}}
    def _precio_keypress(self, size, key):#{{{
        wid = self.precio
        key = restrict_moviment(wid, key)
        return wid.__class__.keypress(wid, size, key)
#}}}
    def keypress(self, size, key):#{{{
        if key == "ctrl d" and self.descripcion.get_text()[0] != u"":
            self._emit("delete-item")
        if key == "ctrl p" and self._obj is not None:
            self._emit("move-up")
            return None
        elif key == "ctrl l" and self._obj is not None:
            self._emit("move-down")
            return None
        return self.__super.keypress(size, key)
#}}}

    ### Signals handlers ###

    def on_code_edit_done(self, widget, codigo):#{{{
        if self._obj is None or self._obj.codigo != codigo:
            try:
                a = session.query(Articulo).filter(Articulo.codigo==smart_unicode(codigo)).one()
            except NoResultFound:
                return
            self.set_obj(a)
        self._jump_to_cantidad()
#}}}
#    def on_search_item(self, widget, first_key=None):#{{{
#        response = search_stock(first_key, multiple=True)
#        if response is not None:
#            self.set_obj(response)
#            self._jump_to_cantidad()
#            self.calcular_total()
#        return None
#}}}
    def on_check_can_move(self, widget):#{{{
        if widget.get_edit_text() == u"" and not self._obj:
            return True
        if self._obj is not None and widget.get_edit_text() == self._obj.codigo:
            return True
        return False
#}}}
#}}}
class DocumentLineItem(WidgetWrap):#{{{

    signals = ['calcular-total', 'item-done', 'delete-item', 'move-up', 'move-down']

    def __init__(self, desc=None):#{{{
        self._obj = desc

        self.descripcion = InputBox()
        self.descripcion.keypress = self._descripcion_keypress
        connect_signal(self.descripcion, "edit-done", self.on_descripcion_edit_done)

        self.cantidad = NumericInputBox(min_value=0, max_value=9999.99, default=1)
        self.cantidad.keypress = self._cantidad_keypress
        connect_signal(self.cantidad, "edit-done", self.on_cantidad_edit_done)
        connect_signal(self.cantidad, "focus-in", highlight_focus_in)

        self.precio = NumericInputBox(min_value=0, max_value=9999.99)
        self.precio.keypress = self._precio_keypress
        connect_signal(self.precio, "edit-done", self.on_precio_edit_done)
        connect_signal(self.precio, "focus-in", highlight_focus_in)

        self.total = NumericText()

        row = Columns([
            ('fixed', 3, Text("-->")),
            ('fixed', 1, Divider()),
            self.descripcion,
            ('fixed', 1, Divider()),
            ('fixed', 8, self.cantidad),
            ('fixed', 1, Divider()),
            ('fixed', 8, self.precio),
            ('fixed', 1, Divider()),
            ('fixed', 9, self.total),
        ])

        if desc is not None:
            self.descripcion.set_edit_text(desc)

        self.__super.__init__(row)
#}}}
    def calcular_total(self):#{{{
        if not all([self.cantidad.edit_text, self.precio.edit_text]):
            return
        total = self.cantidad.value * self.precio.value
        self.total.set_value(total)
        self._emit('calcular-total')
#}}}
    def _descripcion_keypress(self, size, key):#{{{
        wid = self.descripcion
        key = restrict_horizontal(wid, key)
        if wid.get_edit_text().strip() != self._obj:
            key = restrict_moviment(wid, key)
        if key == _finish_key:
            return key
        elif key == "tab":
            wid._emit("edit-done", wid.get_edit_text())
            return None
        return wid.__class__.keypress(wid, size, key)
#}}}
    def _cantidad_keypress(self, size, key):#{{{
        wid = self.cantidad
        key = restrict_horizontal(wid, key)
        if not key:
            return
        if command_map[key] == 'cursor up':
            if self.precio.get_edit_text() != u"":
                self._w.set_focus(self.descripcion)
            return
        elif command_map[key] == 'cursor down':
            self._w.set_focus(self.precio)
            return
        return wid.__class__.keypress(wid, size, key)
#}}}
    def _precio_keypress(self, size, key):#{{{
        wid = self.precio
        key = restrict_moviment(wid, key)
        return wid.__class__.keypress(wid, size, key)
#}}}
    def keypress(self, size, key):#{{{
        if key == "ctrl d" and self.precio.get_edit_text().strip():
            self._emit("delete-item")
        if key == "ctrl p" and self.descripcion.get_edit_text().strip() and\
                self.precio.get_edit_text().strip():
            self._emit("move-up")
            return None
        elif key == "ctrl l" and self.descripcion.get_edit_text().strip() and\
                self.precio.get_edit_text().strip():
            self._emit("move-down")
            return None
        return self.__super.keypress(size, key)
#}}}

    ### Signals handlers ###

    def on_descripcion_edit_done(self, widget, descripcion):#{{{
        if len(descripcion.strip()) > 0:
            self._obj = descripcion.strip()
            if not self.cantidad.edit_text:
                self.cantidad.set_value(1)
            self._w.set_focus(self.cantidad)
#}}}
    def on_cantidad_edit_done(self, widget, cantidad):#{{{
        self.calcular_total()
        self._w.set_focus(self.precio)
#}}}
    def on_precio_edit_done(self, widget, precio):#{{{
        if not precio:
            return
        self.calcular_total()
        self._emit("item-done")
#}}}
#}}}

class DocumentBody(WidgetWrap):#{{{

    signals = ['focus-cliente-box', 'focus-vendedor-box',
               'focus-tipo-documento-box', 'focus-descuento-box', 'focus-recargo-box',
               'show-iva-info', 'clear-iva-info', 'finish-document', 'print-temp-list']

    def __init__(self):#{{{
        self._has_permiso = False

        # FIXME: eliminar en 0.0.5
        # Ajustar el algoritmo de calculo de total: since: 0.0.3 until: 0.0.5
        if get_current_config().usar_nuevo_algoritmo:
            self.calcular_total = self._new_calcular_total
        else:
            self.calcular_total = self._old_calcular_total

        # header
        header = Columns([
            ('fixed', 14, Text("Código", align='center')),
            ('fixed', 1, Divider()),
            Text("Descripción", align='center'),
            ('fixed', 1, Divider()),
            ('fixed', 8, Text("Cantidad", align='right')),
            ('fixed', 1, Divider()),
            ('fixed', 8, Text("Precio", align='right')),
            ('fixed', 1, Divider()),
            ('fixed', 9, Text("Total", align='right')),
        ])
        header = AttrMap(header, 'document.header')

        # footer
        self.subtotal = NumericText(value=0)
        subtotal_row = Columns([
            ('fixed', 12, AttrMap(Text("Subtotal ", align="right"), 'document.subtotal.label')),
            ('fixed', 11, AttrMap(self.subtotal, 'document.subtotal.value')),
        ])

        self.descuento_label = Text("Descuento ", align='right')
        self.descuento = NumericText(value=0)
        descuento_row = Columns([
            ('fixed', 12, AttrMap(self.descuento_label, 'document.descuento.label')),
            ('fixed', 11, AttrMap(self.descuento, 'document.descuento.value')),
        ])

        self.total = NumericText(value=0)
        total_row = Columns([
            ('fixed', 12, AttrMap(Text("TOTAL ", align='right'), 'document.total.label')),
            ('fixed', 11, AttrMap(self.total, 'document.total.value')),
        ])

        vbox2 = Pile([
            AttrMap(subtotal_row, 'document.subtotal'),
            AttrMap(descuento_row, 'document.descuento'),
            AttrMap(total_row, 'document.total'),
        ])

        self.info_articulo = InfoArticulo()

        footer = Columns([
            AttrMap(self.info_articulo, 'document.info'),
            ('fixed', 23, vbox2),
        ])

        # body
        self.items = SimpleListWalker([])
        connect_signal(self.items, 'modified', self.update_info)

        self.list_box = ListBox(self.items)
        body = AttrMap(self.list_box, 'document.item_list')

        self.__super.__init__(Frame(body, header=header, footer=footer))

        self.set_descuento(None)
        self.add_item()
#}}}
    def _new_item(self, obj=None):#{{{
        new_item = DocumentItem(obj=obj)
        connect_signal(new_item, 'calcular-total', lambda w: self.set_descuento(None))
        connect_signal(new_item, 'calcular-total', lambda w: self.calcular_total())
        connect_signal(new_item, 'calcular-total', lambda w: self.update_info())
        connect_signal(new_item, 'item-done', lambda w: self.focus_next_item())
        connect_signal(new_item, 'delete-item', lambda w: self.reset_info())
        connect_signal(new_item, 'delete-item', lambda w: self.items.remove(w))
        connect_signal(new_item, 'delete-item', lambda w: self.set_descuento(None))
        connect_signal(new_item, 'delete-item', lambda w: self.check_last_item())
        connect_signal(new_item, 'check-modificar-precio', self.on_check_modificar_precio)
        connect_signal(new_item, 'move-up', self.on_move_up)
        connect_signal(new_item, 'move-down', self.on_move_down)
        connect_signal(new_item.code_box, 'search-item', self.on_search_item, new_item)
        connect_signal(new_item.code_box, 'switch-to-line-item', self.on_switch_to_line_item, new_item)
        return new_item
#}}}
    def _new_line_item(self, desc=None):#{{{
        new_item = DocumentLineItem(desc)
        connect_signal(new_item, 'calcular-total', lambda w: self.set_descuento(None))
        connect_signal(new_item, 'calcular-total', lambda w: self.calcular_total())
        connect_signal(new_item, 'calcular-total', lambda w: self.update_info())
        connect_signal(new_item, 'item-done', lambda w: self.focus_next_item())
        connect_signal(new_item, 'delete-item', lambda w: self.reset_info())
        connect_signal(new_item, 'delete-item', lambda w: self.items.remove(w))
        connect_signal(new_item, 'delete-item', lambda w: self.set_descuento(None))
        connect_signal(new_item, 'delete-item', lambda w: self.check_last_item())
        connect_signal(new_item, 'move-up', self.on_move_up)
        connect_signal(new_item, 'move-down', self.on_move_down)
        return new_item
#}}}
    def keypress(self, size, key):#{{{
        if key == "f4":
            self._emit("focus-cliente-box")
        elif key == "f3":
            self._emit("focus-vendedor-box")
        elif key == "tab":
            self._emit("focus-tipo-documento-box")
        elif key == "f5":
            self._emit("focus-descuento-box")
        elif key == "f6":
            self._emit("focus-recargo-box")
        elif key == "f8":
            self._emit("print-temp-list")
        elif key == 'ctrl r':
            self.reset_prices()
        elif key == _finish_key:
            # bubble down and check if we can finish
            can_finish = self.__super.keypress(size, key)
            if can_finish == _finish_key:
                self._emit("finish-document")
        else:
            return self.__super.keypress(size, key)
        return key
#}}}
    def clear_items(self):#{{{
        del self.items[:]
        self._has_permiso = False
        self.calcular_total()
#}}}
    def add_item(self, obj=None):#{{{
        new_item = self._new_item(obj)
        self.items.append(new_item)
#}}}
    def get_items(self):#{{{
        items = []
        for i in self.items:
            if i._obj is not None:
                if isinstance(i._obj, Articulo):
                    precio = i.precio.get_value() if i.precio.get_value() != i._obj.precio else None
                elif isinstance(i._obj, basestring):
                    precio = i.precio.get_value()
                else:
                    raise RuntimeError("Unknown item type '%s'" % type(i._obj).__name__)
                articulo = i._obj
                cantidad = i.cantidad.get_value()
                items.append(ItemData(articulo, cantidad, precio))
        return items
#}}}
    def get_items_for_cache(self):#{{{
        # Item: articulo_id, cantidad, precio
        items = []
        for i in self.items:
            if i._obj is not None:
                a = i._obj
                if isinstance(a, Articulo):
                    articulo = a.id
                    precio = i.precio.get_value() if i.precio.get_value() != a.precio else None
                elif isinstance(a, basestring):
                    articulo = a # descripción
                    precio = i.precio.get_value()
                else:
                    raise RuntimeError("Unknown item type '%s'" % type(a).__name__)
                cantidad = i.cantidad.get_value()
                items.append(CachedItem(articulo, cantidad, precio))
        return items
#}}}
    def set_items_from_cache(self, items):#{{{
        self.clear_items()
        for item in items:
            if isinstance(item.articulo_id, int):
                a = session.query(Articulo).filter(Articulo.id==item.articulo_id).one()
                new_item = self._new_item(obj=a)
                new_item.cantidad.set_value(item.cantidad)
                if item.precio is not None:
                    new_item.precio.set_value(item.precio)
                self.items.append(new_item)
                new_item.calcular_total()
            elif isinstance(item.articulo_id, basestring):
                new_item = self._new_line_item(item.articulo_id)
                new_item.cantidad.set_value(item.cantidad)
                new_item.precio.set_value(item.precio)
                self.items.append(new_item)
                new_item.calcular_total()
            else:
                raise RuntimeError("Unknown item type '%s'" % type(item.articulo_id).__name__)
        self.calcular_total()
        self.add_item() # item vacio para seguir agregando items manualmente
        last_index = len(self.items) - 1
        self.items.set_focus(last_index)
        self.items[last_index]._w.set_focus(0)
#}}}
    def focus_next_item(self):#{{{
        current_index = self.items.get_focus()[1]
        next_index = current_index + 1
        if len(self.items) < next_index+1:
            self.add_item()
        self.items.set_focus(next_index)
        next_item = self.items[next_index]
        if isinstance(next_item, DocumentItem):
            next_item._w.set_focus(0)
        else:
            next_item._w.set_focus(2)
#}}}
    def _new_calcular_total(self):
        discrimina = False
        if hasattr(self, '_tipo_documento') and self._tipo_documento:
            discrimina = get_current_config().documentos.get(self._tipo_documento, {'discrimina_iva': False})['discrimina_iva']

        acumulador_montos = []
        for item in self.items:
            acumulador_montos.append( item.total.get_value() )

        subtotal = sum(acumulador_montos)
        self.subtotal.set_value(subtotal)

        desc_label = "Descuento"
        if self._descuento > Decimal(0) and self._descuento >= subtotal:
            self._descuento = Decimal(0)
            show_error("El descuento no puede superar el monto total")
        elif self._descuento < Decimal(0):
            desc_label = "Recargo"
        self.descuento_label.set_text(desc_label)
        self.descuento.set_value(abs(self._descuento))

        total = subtotal - self._descuento
        self.total.set_value(total)

        if discrimina:
            gravado = (total / Decimal('1.21')).quantize(q2)
            iva = gravado * Decimal('0.21')
            self._emit('show-iva-info', gravado, iva)
        else:
            self._emit('clear-iva-info')

        return total

    def _old_calcular_total(self):#{{{
        discrimina = False
        if hasattr(self, '_tipo_documento') and self._tipo_documento:
            discrimina = get_current_config().documentos.get(self._tipo_documento, {'discrimina_iva': False})['discrimina_iva']

        acumulador_iva = []
        acumulador_montos = []

        if discrimina:
            for item in self.items:
                value = item.total.get_value()
                precio_base = (value / Decimal('1.21')).quantize(q) # redondeado a 2
                acumulador_iva.append( (precio_base * Decimal('0.21')).quantize(q2) )
                acumulador_montos.append( precio_base )
        else:
            for item in self.items:
                acumulador_montos.append( item.total.get_value() )

        subtotal = sum(acumulador_montos) + sum(acumulador_iva)

        self.subtotal.set_value(subtotal)

        desc_label = "Descuento "
        if self._descuento > Decimal(0) and self._descuento >= subtotal:
            self._descuento = Decimal(0)
            show_error("El descuento no puede superar el monto total")
        elif self._descuento < Decimal(0):
            desc_label = "Recargo "
        self.descuento_label.set_text(desc_label)
        self.descuento.set_value(abs(self._descuento))

        if discrimina:
            desc_base = (self._descuento / Decimal('1.21')).quantize(q)
            acumulador_iva.append( -(desc_base * Decimal('0.21')).quantize(q2) )
            acumulador_montos.append( -desc_base )
        else:
            acumulador_montos.append( -self._descuento )

        total = sum(acumulador_montos) + sum(acumulador_iva)
        self.total.set_value(total)

        if discrimina:
            gravado = sum(acumulador_montos)
            iva = sum(acumulador_iva)
            self._emit('show-iva-info', gravado, iva)
        else:
            self._emit('clear-iva-info')

        return total
#}}}
    def set_tipo_documento(self, doctype):#{{{
        self._tipo_documento = doctype
        self.calcular_total()
#}}}
    def get_descuento(self):#{{{
        return self._descuento
#}}}
    def set_descuento(self, value):#{{{
        if value is not None:
            self._descuento = value
        else:
            self._descuento = Decimal()
        self.calcular_total()
#}}}
    def update_info(self):#{{{
        item = self.items.get_focus()[0]
        if item and item._obj is not None:
            self.info_articulo.update(item._obj)
#}}}
    def reset_info(self):#{{{
        self.info_articulo.reset()
#}}}
    def reset_prices(self):#{{{
        for item in self.items:
            if isinstance(item, DocumentItem) and item._obj is not None:
                item.set_obj(item._obj)
                item.calcular_total()
#}}}
    def check_last_item(self):#{{{
        if len(self.items) < 1:
            self.add_item()
#}}}

    ### Signal handlers ###

    def on_check_modificar_precio(self):#{{{ # Called with emit_signal
        if not self._has_permiso:
            permiso = check_password("Modificar Precio")
            if permiso is True:
                self._has_permiso = permiso
            elif permiso is False:
                show_error("Ud. no tiene los permisos suficientes para modificar el precio.")
        return self._has_permiso
#}}}
    def on_move_up(self, widget):#{{{
        c = self.items.get_focus()[1]
        p = c - 1

        if p > -1:
            self.items[p:c+1] = reversed(self.items[p:c+1])
            self.items.set_focus(p)
#}}}
    def on_move_down(self, widget):#{{{
        c = self.items.get_focus()[1]
        n = c + 1

        if n < (len(self.items) - 1): # último item vacío
            self.items[c:n+1] = reversed(self.items[c:n+1])
            self.items.set_focus(n)
#}}}
    def on_search_item(self, widget, first_key=None, item=None):
        if item is not None:
            response = search_stock(first_key, multiple=True)
            if response:
                item.set_obj(response.pop(0))
                item._jump_to_cantidad()
                item.calcular_total()
                for a in response:
                    self.add_item(a)
        return None
    def on_switch_to_line_item(self, item):#{{{
        idx = self.items.index(item)
        self.items[idx] = self._new_line_item()
#}}}
#}}}
class DocumentFooter(WidgetWrap):#{{{

    def __init__(self):
        footer_text = ('footer.title', "Nobix %s" % VERSION)
        self.status = Text(footer_text, wrap='clip')
        status_width = len(footer_text[1])+1
        self.date = Text("", wrap='clip')
        self.extra_info = Text(u"", align='right', wrap='clip')

        self._clock_update_interval = get_current_config().clock_update_interval
        self._clock_fmt = get_current_config().clock_fmt
        clock_width = get_current_config().clock_width

        w = Columns([
            ('fixed', status_width, self.status),
            ('fixed', clock_width, AttrMap(self.date, 'footer.key')),
            self.extra_info,
        ], dividechars=2)

        self.__super.__init__(w)

    def update_date(self, main_loop=None, user_data=None):
        self.date.set_text(datetime.now().strftime(self._clock_fmt))
        if main_loop is not None:
            main_loop.set_alarm_in(self._clock_update_interval, self.update_date, user_data)
#}}}

# Dialogos
class ArticleSearchItem(SearchListItem):#{{{

    def __init__(self, item):
        self.__super.__init__([
            ('fixed', 10, Text(item.codigo, wrap='clip')),
            Text(item.descripcion, wrap='clip'),
            ('fixed', 8, NumericText(item.precio)),
        ])
#}}}
class ArticleSearchDialog(SearchDialog):#{{{
    title = u"BUSCAR ARTICULOS"
    subtitle = None

    def get_item_constructor(self):
        return ArticleSearchItem
#}}}
class ArticleSearchDialogExact(ArticleSearchDialog):#{{{
    subtitle = u"por descripción exacta"

    def get_query(self, term):
        if term.strip():
            query = session.query(Articulo).filter(Articulo.descripcion.startswith(smart_unicode(term)))
            query = query.filter(Articulo.es_activo==True).order_by(Articulo.descripcion)
            return query
#}}}
class ArticleSearchDialogByWord(ArticleSearchDialog):#{{{
    subtitle = u"por palabras"

    def get_query(self, term):
        if term.strip():
            terms = term.split()
            query = session.query(Articulo).filter(Articulo.es_activo==True).order_by(Articulo.descripcion)
            if get_current_config().case_sensitive_search:
                for t in terms:
                    query = query.filter(Articulo.descripcion.contains(smart_unicode(t)))
            else:
                for t in terms:
                    query = query.filter(Articulo.descripcion.ilike('%'+smart_unicode(t)+'%'))
            return query
#}}}
class ArticleSearchDialogByCode(ArticleSearchDialog):#{{{
    subtitle = u"por código (comodines)"

    def get_query(self, term):
        if term.strip():
            if '?' not in term and '*' not in term: term = term+'*'
            # Transform from GLOB pattern to LIKE pattern
            term = term.replace('?', '_').replace('*', '%')
            query = session.query(Articulo).filter(Articulo.codigo.like(smart_unicode(term)))
            query = query.filter(Articulo.es_activo==True).order_by(Articulo.codigo)
            return query
#}}}
class ArticleSearchDialogByGroup(ArticleSearchDialog):#{{{
    subtitle = u"por agrupación"

    def get_query(self, term):
        if term.strip():
            query = session.query(Articulo).filter(Articulo.agrupacion.startswith(smart_unicode(term)))
            query = query.filter(Articulo.es_activo==True).order_by(Articulo.descripcion)
            return query
#}}}
class ArticleSearchDialogBySupplier(ArticleSearchDialog):#{{{
    subtitle = u"por proveedor"

    def get_query(self, term):
        if term.strip():
            query = session.query(Articulo).filter(Articulo.proveedor.startswith(smart_unicode(term)))
            query = query.filter(Articulo.es_activo==True).order_by(Articulo.descripcion)
            return query
#}}}
class TerceroSearchItem(SearchListItem):#{{{

    def __init__(self, item):
        extra_info = (item.domicilio, item.localidad)
        if all(extra_info):
            info = " - ".join(extra_info)
        else:
            info = u"".join(extra_info)

        self.__super.__init__([
            ('fixed',  7, Text(unicode(item.codigo), wrap='clip')),
            ('fixed', 36, Text(item.nombre, wrap='clip')),
            Text(info, wrap='clip'),
        ])
#}}}
class TerceroSearchItemWithCuit(SearchListItem):#{{{

    def __init__(self, item):
        extra_info = (item.domicilio, item.localidad)
        if all(extra_info):
            info = " - ".join(extra_info)
        else:
            info = u"".join(extra_info)

        self.__super.__init__([
            ('fixed', 7, Text(unicode(item.codigo), wrap='clip')),
            ('fixed', 15, Text(unicode(item.cuit), wrap='clip')),
            ('fixed', 28, Text(item.nombre, wrap='clip')),
            ('fixed', 1, Divider()),
            Text(info, wrap='clip'),
        ])
#}}}
class TerceroSearchDialog(SearchDialog):#{{{

    def __init__(self, rel=None, **kwargs):
        self._rel = rel if rel is not None else u'C'
        self.title = u"BUSCAR %s" % (u'CLIENTE' if self._rel == u'C' else u'PROVEEDOR',)
        self.__super.__init__(**kwargs)

    def get_item_constructor(self):
        return TerceroSearchItem
#}}}
class TerceroSearchDialogExact(TerceroSearchDialog):#{{{
    subtitle = u"por nombre exacto"

    def get_query(self, term):
        if term.strip():
            query = session.query(Cliente).filter(Cliente.relacion==self._rel).order_by(Cliente.nombre)
            query = query.filter(Cliente.nombre.startswith(smart_unicode(term)))
            return query
#}}}
class TerceroSearchDialogByWord(TerceroSearchDialog):#{{{
    subtitle = u"por palabra"

    def get_query(self, term):
        if term.strip():
            terms = term.split()
            query = session.query(Cliente).filter(Cliente.relacion==self._rel).order_by(Cliente.nombre)
            if get_current_config().case_sensitive_search:
                for t in terms:
                    query = query.filter(Cliente.nombre.contains(smart_unicode(t)))
            else:
                for t in terms:
                    query = query.filter(Cliente.nombre.ilike('%'+smart_unicode(t)+'%'))
            return query
#}}}
class TerceroSearchDialogByCuit(TerceroSearchDialog):#{{{
    subtitle = u"por CUIT (comodines)"

    def get_query(self, term):
        if term.strip():
            if '?' not in term and '*' not in term: term = term+'*'
            # Transform from GLOB pattern to LIKE pattern
            term = term.replace('?', '_').replace('*', '%')
            query = session.query(Cliente).filter(Cliente.relacion==self._rel).order_by(Cliente.cuit)
            query = query.filter(Cliente.cuit.like(smart_unicode(term)))
            return query

    def get_item_constructor(self):
        return TerceroSearchItemWithCuit
#}}}

class DiscountDialog(Dialog):#{{{

    def __init__(self, recargo=False):
        discount_input = NumericInputBox(min_value=0, max_value=9999.99)
        discount_input.set_value(0)
        connect_signal(discount_input, 'focus-in', highlight_focus_in)
        connect_signal(discount_input, 'edit-done', self.on_edit_done)
        connect_signal(discount_input, 'edit-cancel', lambda w: self.quit())

        w = Columns([
            Text(" Monto: "),
            AttrMap(discount_input, 'dialog.descuento.input'),
            ('fixed', 1, Divider()),
        ])

        if recargo:
            title = "RECARGO"
        else:
            title = "DESCUENTO"

        self.__super.__init__(w,
                              title=title,
                              height=None,
                              width=22)
        self.attr_style = "dialog.descuento"
        self.title_attr_style = "dialog.descuento.title"

    def on_edit_done(self, widget, discount):
        self.dialog_result = widget.get_value()
        self.quit()
#}}}

## Implementacion del editor Maestro de Stock

class ActionBox(InputBox):#{{{

    actions = {
        'A': 'action-previous',
        'B': 'action-unsubscribe',
        'C': 'action-continue',
        'V': 'action-return',
        'M': 'action-modify-code',
    }

    signals = actions.values()

    def __init__(self):
        self.__super.__init__(max_length=1)
        connect_signal(self, 'edit-done', self.emit_action)

    def keypress(self, size, key):
        if key in ('enter', 'esc'):
            return self.__super.keypress(size, key)
        key = key.upper()
        self.emit_action(self, key.upper())
        return None

    def emit_action(self, widget, action):
        if action in self.actions.keys():
            self.set_edit_text(action)
            self.set_edit_pos(0)
            self._emit(self.actions[action])
#}}}
class MaestockCodeBox(InputBox):#{{{
    signals = ['search-item']

    def keypress(self, size, key):
        key = restrict_moviment(self, key)
        if key and key not in (_numbers + _commands):
            if self.edit_pos == 0 or self.highlight is not None:
                self._emit("search-item", key)
                return key
        return self.__super.keypress(size, key)

    def filter_input(self, text):
        return text.upper()
#}}}

ArticuloInformation = namedtuple('ArticuloInformation', "descripcion proveedor agrupacion precio vigencia")

class MaestroStock(Dialog):#{{{

    def __init__(self):#{{{

        self.set_prev_obj(None)
        self._vigencia_error_state = None

        def _edit_cancel(widget):#{{{
            self.focus_button(1)#}}}
        def _action_prev(widget):#{{{
            self.fill_with_data(self._prev_obj)
            self.on_next_focus(widget)#}}}

        self.codigo_box = MaestockCodeBox(max_length=14)
        connect_signal(self.codigo_box, 'focus-in', self.on_codigo_focus_in)
        connect_signal(self.codigo_box, 'edit-done', self.on_codigo_edit_done)
        connect_signal(self.codigo_box, 'edit-cancel', _edit_cancel)
        connect_signal(self.codigo_box, 'search-item', self.on_search_item)
        self.action_label = Text("")
        self.action_box = ActionBox()
        connect_signal(self.action_box, 'focus-in', self.show_instrucciones)
        connect_signal(self.action_box, 'focus-out', self.hide_instrucciones)
        connect_signal(self.action_box, 'action-return', self.on_action_return)
        connect_signal(self.action_box, 'action-continue', self.on_action_continue)
        connect_signal(self.action_box, 'action-previous', _action_prev)
        connect_signal(self.action_box, 'action-unsubscribe', self.on_action_baja)
        connect_signal(self.action_box, 'action-modify-code', self.on_action_modify_code)

        codigo_row = Columns([
            ('fixed', 12, AttrMap(Text("Código"), 'dialog.maestock.label')),
            ('fixed', 1, Divider()),
            ('fixed', 14, AttrMap(self.codigo_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
            ('fixed', 1, Divider()),
            AttrMap(self.action_label, 'dialog.maestock.action'),
            ('fixed', 1, AttrMap(self.action_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
        ])

        self.descripcion_box = InputBox(max_length=40)
        connect_signal(self.descripcion_box, 'edit-done', self.on_next_focus)
        connect_signal(self.descripcion_box, 'edit-cancel', _edit_cancel)
        descripcion_row = Columns([
            ('fixed', 12, AttrMap(Text("Descripción"), 'dialog.maestock.label')),
            ('fixed', 1, Divider()),
            ('fixed', 40, AttrMap(self.descripcion_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
        ])

        self.proveedor_box = InputBox(max_length=20)
        connect_signal(self.proveedor_box, 'edit-done', self.on_next_focus)
        connect_signal(self.proveedor_box, 'edit-cancel', _edit_cancel)
        proveedor_row = Columns([
            ('fixed', 12, AttrMap(Text("Proveedor"), 'dialog.maestock.label')),
            ('fixed', 1, Divider()),
            ('fixed', 20, AttrMap(self.proveedor_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
        ])

        self.agrupacion_box = InputBox(max_length=20)
        connect_signal(self.agrupacion_box, 'edit-done', self.on_next_focus)
        connect_signal(self.agrupacion_box, 'edit-cancel', _edit_cancel)
        agrupacion_row = Columns([
            ('fixed', 12, AttrMap(Text("Agrupación"), 'dialog.maestock.label')),
            ('fixed', 1, Divider()),
            ('fixed', 20, AttrMap(self.agrupacion_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
        ])

        self.precio_box = NumericInputBox(min_value=0, max_value=99999.99)
        connect_signal(self.precio_box, 'focus-in', self.on_precio_focus_in)
        connect_signal(self.precio_box, 'edit-done', self.on_next_focus)
        connect_signal(self.precio_box, 'edit-cancel', _edit_cancel)
        self.precio_error = Text(u"")
        precio_row = Columns([
            ('fixed', 12, AttrMap(Text("Precio"), 'dialog.maestock.label')),
            ('fixed', 1, Divider()),
            ('fixed', 9, AttrMap(self.precio_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
            AttrMap(self.precio_error, 'dialog.maestock.error')
        ])

        self.vigencia_box = DateSelectorBox()
        connect_signal(self.vigencia_box, 'focus-in', self.on_vigencia_focus_in)
        connect_signal(self.vigencia_box, 'focus-out', self.on_vigencia_focus_out)
        connect_signal(self.vigencia_box, 'edit-cancel', _edit_cancel)
        connect_signal(self.vigencia_box, 'edit-done', self.on_vigencia_edit_done)
        connect_signal(self.vigencia_box, 'bad-date-error', self.on_vigencia_error)
        self.vigencia_error = Text(u"")
        vigencia_row = Columns([
            ('fixed', 12, AttrMap(Text("Vigencia"), 'dialog.maestock.label')),
            ('fixed', 1, Divider()),
            ('fixed', 9, AttrMap(self.vigencia_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
            ('fixed', 1, Divider()),
            AttrMap(self.vigencia_error, 'dialog.maestock.error')
        ])

        self.instrucciones = Text(u"", align='right')

        self.content = Pile([
            codigo_row,
            descripcion_row,
            proveedor_row,
            agrupacion_row,
            precio_row,
            vigencia_row,
            AttrMap(self.instrucciones, 'dialog.maestock.instrucciones'),
            Divider(),
        ])

        #buttons = [("Grabar", self.save), ("Salir", self._quit)]
        buttons = [("Grabar", self.save), ("Salir", self.quit)]
        self.__super.__init__(self.content, buttons,
                              title="MAESTRO DE STOCK",
                              height=None,
                              width=55)
        self.attr_style = 'dialog.maestock'
        self.title_attr_style = 'dialog.maestock.title'
#}}}
    def show_instrucciones(self, *args):#{{{
        key = 'dialog.maestock.key'
        inst = [(key, 'C'), "ontinua  ", (key, 'V'), "uelve  "]
        if self._obj:
            inst.extend([(key, 'B'), "aja  "])
        inst.extend([(key, 'A'), "nterior  "])
        if self._obj:
            inst.extend([(key, 'M'), u"odifica código"])
        self.instrucciones.set_text(inst)
#}}}
    def hide_instrucciones(self, *args):#{{{
        self.instrucciones.set_text(u"")
#}}}
    def fill_with_data(self, obj):#{{{
        if obj is not None:
            self.descripcion_box.set_edit_text(obj.descripcion)
            self.proveedor_box.set_edit_text(obj.proveedor)
            self.agrupacion_box.set_edit_text(obj.agrupacion)
            self.precio_box.set_value(obj.precio)
            self.vigencia_box.set_value(obj.vigencia)
        else:
            self.descripcion_box.set_edit_text(u"")
            self.proveedor_box.set_edit_text(u"")
            self.agrupacion_box.set_edit_text(u"")
            self.precio_box.set_edit_text(u"")
            self.vigencia_box.set_edit_text(u"")
#}}}
    def save(self, *args):#{{{
        # can be connected as callback
        def _set_focus_on_code_box():
            self._pile.set_focus(0)
            self._pile.widget_list[0].set_focus(0)
            self.content.widget_list[0].set_focus(2)
            self.codigo_box.set_edit_text(u"")
            self.fill_with_data(None)

        if self.codigo_box.get_edit_text() == u"":
            _set_focus_on_code_box()
            return
        if self.precio_box.get_edit_text() == u"":
            self.precio_error.set_text(" No puede estar vacío")
            return
        if self.vigencia_box.get_edit_text() == u"":
            self.vigencia_error.set_text(" No puede estar vacío")
            return
        if not self.vigencia_box._check_date():
            return

        if self._obj:
            a = self._obj
        else:
            a = Articulo()
            a.codigo = self.codigo_box.get_edit_text()

        a.descripcion = self.descripcion_box.get_edit_text()
        a.proveedor = self.proveedor_box.get_edit_text()
        a.agrupacion = self.agrupacion_box.get_edit_text()
        a.precio = self.precio_box.get_value()
        a.vigencia = self.vigencia_box.get_value()

        if self._obj:
            self._obj = None
        else:
            session.add(a)
        self.set_prev_obj(a)
        session.commit()
        _set_focus_on_code_box()
#}}}
    def set_prev_obj(self, obj):#{{{
        if obj is not None:
            obj = ArticuloInformation(obj.descripcion, obj.proveedor,
                                      obj.agrupacion, obj.precio, obj.vigencia)
        self._prev_obj = obj
#}}}

    ### Signal Handlers ###

    def on_codigo_focus_in(self, widget):#{{{
        self.action_label.set_text(u"")
        self.action_box.set_edit_text(u"")
        highlight_focus_in(widget)
#}}}
    def on_codigo_edit_done(self, widget, code):#{{{
        if code != u"":
            # Fijar accion y cargar datos en el formulario
            q = session.query(Articulo).filter(Articulo.codigo==code)
            try:
                self._obj = q.one()
                action = "Modificar"
#                if self._obj.es_activo is False:
#                    action = "Alta"
                if self._prev_obj is None:
                    self.set_prev_obj(self._obj)
            except NoResultFound:
                self._obj = None
                action = "Nuevo"
            self.fill_with_data(self._obj)
            self.action_label.set_text(action)
            self.action_box.set_edit_text("C")
            self.content.widget_list[0].set_focus(5)
#}}}
    def on_search_item(self, widget, first_key=None):#{{{
        response = search_stock(first_key)
        if response:
            self._obj = response[0]
            self.codigo_box.set_edit_text(self._obj.codigo)
            self.fill_with_data(self._obj)
            self.action_label.set_text("Modificar")
            self.action_box.set_edit_text("C")
            self.content.widget_list[0].set_focus(5)
        return None
#}}}
    def on_next_focus(self, *args):#{{{
        c = self.content
        focus_index = c.widget_list.index(c.focus_item)
        c.set_focus(focus_index+1)
#}}}
    def on_action_continue(self, *args):#{{{
        self.set_prev_obj(self._obj)
        self.on_next_focus()
#}}}
    def on_action_baja(self, widget):#{{{
        if self._obj:
            cont = show_warning([u"Esta acción dará de baja al artículo ",
                ('dialog.warning.important', u"%s" % self._obj.codigo), u"\n\n¿Está seguro?\n"
                ], [(u"Aceptar", True), (u"Cancelar", False)], focus_button=0)
            if cont is not True:
                self.action_box.set_edit_text(u"C")
                return
            self._obj.codigo = "I" + self._obj.codigo
            self._obj.es_activo = False
            session.commit()
            self._obj = None
            self.set_prev_obj(None)
            self.on_action_return(widget)
#}}}
    def on_action_modify_code(self, widget):
        if self._obj:
            new_code = ModificaCodigo(self._obj).run()
            if not new_code:
                self.action_box.set_edit_text(u"C")
                return
            self.codigo_box.set_edit_text(new_code)
            self.on_codigo_edit_done(self.codigo_box, new_code)

    def on_action_return(self, widget):#{{{
        self.codigo_box.set_edit_text(u"")
        self.fill_with_data(None)
        self.content.widget_list[0].set_focus(2)
#}}}
    def on_precio_focus_in(self, widget):#{{{
        self.precio_error.set_text(u"")
        highlight_focus_in(widget)
#}}}
    def on_vigencia_focus_in(self, widget):#{{{
        if self._vigencia_error_state is None:
            self.vigencia_error.set_text(u"")
            highlight_focus_in(widget)
#}}}
    def on_vigencia_edit_done(self, widget, *text):#{{{

        if self._vigencia_error_state is not None:
            self.vigencia_error.set_text(self._vigencia_error_state)
            self._vigencia_error_state = None
            highlight_focus_in(widget)
            return
        self.vigencia_error.set_text(u"")
        self._check_futuro()
        self.focus_button(0)
#}}}
    def on_vigencia_focus_out(self, widget):#{{{
        self._vigencia_error_state = None
        self.vigencia_error.set_text(u"")
        self._check_futuro()
#}}}
    def on_vigencia_error(self, widget, msg):#{{{
        self._vigencia_error_state = msg
        self.vigencia_error.set_text(msg)
#}}}
    def _check_futuro(self):#{{{
        if self.vigencia_error.get_text()[0] == u"": # por las dudas!
            d = self.vigencia_box.value
            if d:
                f = date.today() + timedelta(days=1)
                if d >= f:
                    self.vigencia_error.set_text(u"CUIDADO: Fecha futura")
                else:
                    self.vigencia_error.set_text(u"")
#}}}
#}}}

class MaestockNewCodeBox(InputBox):#{{{
    signals = ['invalid-code']

    def keypress(self, size, key):
        if key and key not in (_numbers + _commands):
            if self.edit_pos == 0 or self.highlight is not None:
                return key
        return self.__super.keypress(size, key)

    def filter_input(self, text):
        return text.upper()
#}}}
class ModificaCodigo(Dialog):#{{{

    def __init__(self, obj):#{{{

        self._obj = obj

        row_orig_code = Columns([
            ('fixed', 12, AttrMap(Text("Código"), 'dialog.maestock.label')),
            ('fixed', 14, AttrMap(Text("%s" % obj.codigo), 'dialog.maestock.label')),
        ], dividechars=1)

        self.new_code_box = MaestockNewCodeBox(max_length=14)
        connect_signal(self.new_code_box, 'focus-out', self.on_code_focus_out)
        connect_signal(self.new_code_box, 'edit-done', self.on_code_edit_done)
        connect_signal(self.new_code_box, 'edit-cancel', lambda *w: self.focus_button(1))
        self.new_code_error = Text("")

        row_new_code = Columns([
            ('fixed', 12, AttrMap(Text(u"Nuevo Código"), 'dialog.maestock.label')),
            ('fixed', 14, AttrMap(self.new_code_box, 'dialog.maestock.input', 'dialog.maestock.input.focus')),
            AttrMap(self.new_code_error, 'dialog.maestock.error'),
        ], dividechars=1)

        self.content = Pile([
            row_orig_code,
            row_new_code,
            Divider(),
        ])

        #buttons = [("Grabar", self.save), ("Cancelar", self._quit)]
        buttons = [("Grabar", self.save), ("Cancelar", self.quit)]
        self.__super.__init__(self.content, buttons,
                              title=u"MODIFICA CÓDIGO",
                              height=None,
                              width=55)
        self.attr_style = 'dialog.maestock'
        self.title_attr_style = 'dialog.maestock.title'
#}}}
    def save(self, btn):#{{{
        new_code = self.new_code_box.get_edit_text()
        if not self._validar_nuevo_codigo(new_code):
            self._pile.set_focus(0)
            self._pile.widget_list[0].set_focus(1)
            self.content.widget_list[1].set_focus(1)
            return

        self._obj.codigo = new_code
        session.commit()
        self.dialog_result = new_code
        self.quit()
#}}}
    def _validar_nuevo_codigo(self, codigo):#{{{
        if codigo == u"":
            self.new_code_error.set_text(u"No puede estar vacío")
            return False

        try:
            session.query(Articulo).filter(Articulo.codigo==codigo).one()
        except NoResultFound:
            self.new_code_error.set_text(u"")
            return True
        self.new_code_error.set_text(u"El código ya esta en uso")
        return False
#}}}
    def on_code_focus_out(self, widget):#{{{
        self._validar_nuevo_codigo(widget.edit_text)
#}}}
    def on_code_edit_done(self, widget, code):#{{{
        if self._validar_nuevo_codigo(code):
            self.focus_button(0)
#}}}
#}}}

## Implementacion del editor de Maestro de Terceros

class MaeterCodeBox(InputBox):#{{{
    signals = ['request-new', 'search-client']

    def valid_char(self, ch):
        return len(ch) == 1 and ch in "0123456789"

    def filter_input(self, text):
        return text.upper()

    def keypress(self, size, key):
        key = restrict_moviment(self, key)
        if key:
            if key in string.letters:
                self._emit("search-client", "exact description", key)
                return key
            elif key == ".":
                self._emit("search-client", "word description")
                return key
            elif key == "*":
                self._emit("search-client", "cuit")
                return key
            elif key == 'ctrl n':
                self._emit('request-new')
                return
            return self.__super.keypress(size, key)
#}}}
class MaestroTerceros(Dialog):#{{{

    def __init__(self, titulo_rel=u'CLIENTES', rel=u'C', filled_with=None, once=False):#{{{

        self._rel = rel
        self._once = once

        def _edit_cancel(widget):
            self.focus_button(1)

        self.codigo_box = MaeterCodeBox(max_length=12)
        connect_signal(self.codigo_box, 'edit-done', self.on_codigo_edit_done)
        connect_signal(self.codigo_box, 'edit-cancel', _edit_cancel)
        connect_signal(self.codigo_box, 'request-new', lambda w: self.fill_with_data("new"))
        connect_signal(self.codigo_box, 'search-client', self.on_cliente_search)
        self.action_label = Text(u"")

        codigo_row = Columns([
            ('fixed', 13, AttrMap(Text(u"Código"), 'dialog.maeter.label')),
            ('fixed', 1, Divider()),
            ('fixed', 12, AttrMap(self.codigo_box, 'dialog.maeter.input', 'dialog.maeter.input.focus')),
            ('fixed', 1, Divider()),
            AttrMap(self.action_label, 'dialog.maeter.action'),
        ])

        self.nombre_box = InputBox(max_length=35)
        connect_signal(self.nombre_box, 'edit-done', self.on_next_focus)
        connect_signal(self.nombre_box, 'edit-cancel', _edit_cancel)
        nombre_row = Columns([
            ('fixed', 13, AttrMap(Text(u"Razón Social"), 'dialog.maeter.label')),
            ('fixed', 1, Divider()),
            ('fixed', 35, AttrMap(self.nombre_box, 'dialog.maeter.input', 'dialog.maeter.input.focus')),
        ])

        self.domicilio_box = InputBox(max_length=35)
        connect_signal(self.domicilio_box, 'edit-done', self.on_next_focus)
        connect_signal(self.domicilio_box, 'edit-cancel', _edit_cancel)
        domicilio_row = Columns([
            ('fixed', 13, AttrMap(Text("Domicilio"), 'dialog.maeter.label')),
            ('fixed', 1, Divider()),
            ('fixed', 35, AttrMap(self.domicilio_box, 'dialog.maeter.input', 'dialog.maeter.input.focus')),
        ])

        self.localidad_box = InputBox(max_length=20)
        connect_signal(self.localidad_box, 'edit-done', self.on_next_focus)
        connect_signal(self.localidad_box, 'edit-cancel', _edit_cancel)
        localidad_row = Columns([
            ('fixed', 13, AttrMap(Text("Localidad"), 'dialog.maeter.label')),
            ('fixed', 1, Divider()),
            ('fixed', 20, AttrMap(self.localidad_box, 'dialog.maeter.input', 'dialog.maeter.input.focus')),
        ])

        self.cp_box = InputBox(max_length=8)
        connect_signal(self.cp_box, 'edit-done', self.on_next_focus)
        connect_signal(self.cp_box, 'edit-cancel', _edit_cancel)
        cp_row = Columns([
            ('fixed', 13, AttrMap(Text("Código Postal"), 'dialog.maeter.label')),
            ('fixed', 1, Divider()),
            ('fixed', 8, AttrMap(self.cp_box, 'dialog.maeter.input', 'dialog.maeter.input.focus')),
        ])

        bgroup = []
        self.resp_buttons = dict([(k, RadioButton(bgroup, v['nombre'], False, self.on_radio_change, k))\
                                  for k, v in get_current_config().iva_resp_map.iteritems()])

        resp_row = GridFlow([AttrMap(i, 'dialog.radio', 'dialog.radio.focus')\
                                for i in self.resp_buttons.values() if len(i.label) <= 21],
                            26, 1, 0, 'left')
        #resp_row2 = Pile([AttrMap(i, 'dialog.radio', 'dialog.radio.focus')\
        #                  for i in self.resp_buttons.values() if len(i.label) > 21])
        self.resp_buttons[u'I'].state = True

        self.cuit_box = InputBox(max_length=13)
        connect_signal(self.cuit_box, 'edit-done', self.on_cuit_edit_done)
        connect_signal(self.cuit_box, 'edit-cancel', _edit_cancel)
        connect_signal(self.cuit_box, 'focus-out', self.on_cuit_focus_out)
        self.cuit_error = Text(u"")
        cuit_row = Columns([
            ('fixed', 5, AttrMap(Text("CUIT"), 'dialog.maeter.label')),
            ('fixed', 1, Divider()),
            ('fixed', 14, AttrMap(self.cuit_box, 'dialog.maeter.input', 'dialog.maeter.input.focus')),
            ('fixed', 1, Divider()),
            AttrMap(self.cuit_error, 'dialog.maeter.error'),
        ])

        self.content = Pile([
            codigo_row,
            nombre_row,
            domicilio_row,
            localidad_row,
            cp_row,
            Divider(),
            AttrMap(resp_row, 'dialog.maeter.group'),
            #AttrMap(resp_row2, 'dialog.maeter.group'),
            cuit_row,
            Divider(),
        ])

        #buttons = [("Grabar", self.save), ("Salir", self._quit)]
        buttons = [("Grabar", self.save), ("Salir", self.quit)]
        self.__super.__init__(self.content, buttons,
                              title="MAESTRO DE %s" % titulo_rel,
                              height=None,
                              width=56)
        self.attr_style = 'dialog.maeter'
        self.title_attr_style = 'dialog.maeter.title'

        self.fill_with_data(filled_with)
#}}}
    def save(self, *args):#{{{
        # 0 - codigo_box
        # 1 - nombre_box
        # 8 - cuit_box
        def _set_focus_on(index):
            self._pile.set_focus(0)
            self._pile.widget_list[0].set_focus(index)
            self.content.widget_list[index].set_focus(2)

        if self.codigo_box.edit_text == u"":
            _set_focus_on(0)
            return

        if self.nombre_box.edit_text == u"":
            _set_focus_on(1)
            return

        if self._validar_cuit(self.cuit_box.edit_text) is False:
            _set_focus_on(8)
            return

        if self._obj:
            c = self._obj
        else:
            c = Cliente(codigo=int(self.codigo_box.get_edit_text()))

        c.nombre = self.nombre_box.get_edit_text()
        c.domicilio = self.domicilio_box.get_edit_text()
        c.localidad = self.localidad_box.get_edit_text()
        c.codigo_postal = self.cp_box.get_edit_text()
        c.cuit = self.cuit_box.get_edit_text()
        c.relacion = self._rel

        for k, v in self.resp_buttons.iteritems():
            if v.state is True:
                c.responsabilidad_iva = k
                break

        if self._obj:
            self._obj = None
        else:
            session.add(c)
        session.commit()

        if self._once:
            #self.must_quit = True
            self.quit()
            return c

        _set_focus_on(0)
        self.fill_with_data(None)
        self.action_label.set_text(u"")
        self.codigo_box.edit_text = u""
#}}}
    def fill_with_data(self, obj):#{{{
        if isinstance(obj, Cliente):
            self.nombre_box.set_edit_text(obj.nombre)
            self.domicilio_box.set_edit_text(obj.domicilio)
            self.localidad_box.set_edit_text(obj.localidad)
            self.cp_box.set_edit_text(obj.codigo_postal)
            self.resp_buttons[obj.responsabilidad_iva].state = True
            self.cuit_box.set_edit_text(obj.cuit or u"")
            self._obj = obj
        elif isinstance(obj, basestring):
            if obj.startswith("new"):
                next_clinumber = get_next_clinumber(self._rel)
                self.fill_with_data(None)
                self.codigo_box.set_edit_text(next_clinumber)
                self.on_codigo_edit_done(self.codigo_box, next_clinumber)
            else:
                try:
                    clicode = int(obj)
                except ValueError:
                    clicode = None
                cli = session.query(Cliente).filter_by(codigo=clicode, relacion=self._rel).first()
                self.fill_with_data(cli)
                if cli is not None:
                    self.codigo_box.set_edit_text(cli.codigo)
                    self.on_codigo_edit_done(self.codigo_box, cli.codigo)
        else:
            self.nombre_box.set_edit_text(u"")
            self.domicilio_box.set_edit_text(u"")
            self.localidad_box.set_edit_text(u"")
            self.cp_box.set_edit_text(u"")
            self.resp_buttons[u'I'].state = True
            self.cuit_box.set_edit_text(u"")
            self._obj = None
#}}}

    ### Signal Hanlders ###

    def on_codigo_edit_done(self, widget, code):#{{{
        if code != u"":
            q = session.query(Cliente).filter(Cliente.codigo==int(code))
            q = q.filter(Cliente.relacion==self._rel)
            try:
                self._obj = q.one()
                action = "Modificar"
            except NoResultFound:
                self._obj = None
                action = "Nuevo"
            self.fill_with_data(self._obj)
            self.action_label.set_text(action)
            self.on_next_focus()
#}}}
    def on_codigo_focus_in(self, widget):#{{{
        self.action_label.set_text(u"")
        highlight_focus_in(widget)
#}}}
    def on_cliente_search(self, widget, search_by=None, first_key=None):#{{{
        response = search_terceros(search_by=search_by, first_key=first_key)
        if response:
            self.fill_with_data(response[0])
            self.codigo_box.set_edit_text(str(response[0].codigo))
            self.on_codigo_edit_done(self.codigo_box, str(response[0].codigo))
        return None
#}}}
    def on_next_focus(self, *args):#{{{
        c = self.content
        focus_index = c.widget_list.index(c.focus_item)
        c.set_focus(focus_index+1)
        if not c.focus_item.selectable():
            self.on_next_focus()
#}}}
    def on_radio_change(self, radio, state, resp):#{{{
        if state is True:
            for r in self.resp_buttons.itervalues():
                if r is not radio:
                    r.state = False
#}}}
    def on_cuit_edit_done(self, widget, cuit):#{{{
        if self._validar_cuit(cuit):
            self.focus_button(0)
#}}}
    def on_cuit_focus_out(self, widget):#{{{
        self._validar_cuit(widget.edit_text)
#}}}
    def _validar_cuit(self, cuit):#{{{
        if self.resp_buttons[u'C'].state is False:
            if cuit.strip() == u"":
                self.cuit_error.set_text("No puede estar vacío")
                return False
            elif validar_cuit(cuit) is False:
                self.cuit_error.set_text("Iválido")
                return False
        self.cuit_error.set_text(u"")
        return True

#        if self.resp_buttons[u'C'].state is True:
#            self.cuit_error.set_text(u"")
#            return True
#        else:
#            if cuit.strip() == u"":
#                self.cuit_error.set_text("No puede estar vacío")
#                return False
#            elif validar_cuit(cuit) is False:
#                self.cuit_error.set_text("Inválido")
#                return False
#
#            sefl.cuit_error.set_text(u"")
#            return True
#}}}
#}}}

class TaxItem(WidgetWrap):#{{{

    signals = ['tax-monto-set', 'tax-code-set', 'tax-code-void-set',
               'tax-item-done', 'tax-item-delete', 'tax-item-edit-cancel']

    def __init__(self):#{{{

        self._tax = None

        def _edit_cancel(widget):
            self._emit("tax-item-edit-cancel")

        self.tax_code = InputBox(max_length=3)
        self.tax_code.filter_input = lambda t: t.upper()
        connect_signal(self.tax_code, 'focus-in', highlight_focus_in)
        connect_signal(self.tax_code, 'focus-out', self.on_tax_code_focus_out)
        connect_signal(self.tax_code, 'edit-done', self.on_tax_code_edit_done)
        connect_signal(self.tax_code, 'edit-cancel', _edit_cancel)

        self.descripcion = Text(u"", wrap='clip')
        self.porcentaje = NumericText()
        self.monto_box = NumericInputBox(min_value=0, max_value=9999.99)
        connect_signal(self.monto_box, 'focus-in', highlight_focus_in)
        connect_signal(self.monto_box, 'focus-out', self.on_monto_box_focus_out)
        connect_signal(self.monto_box, 'edit-done', self.on_monto_box_edit_done)
        connect_signal(self.monto_box, 'edit-cancel', _edit_cancel)

        row = Columns([
            ('fixed', 4, AttrMap(self.tax_code, 'dialog.documento.tax.input',
                                 'dialog.documento.tax.input.focus')),
            AttrMap(self.descripcion, 'dialog.documento.tax.label'),
            ('fixed', 6, AttrMap(self.porcentaje, 'dialog.documento.tax.label')),
            ('fixed', 9, AttrMap(self.monto_box, 'dialog.documento.tax.input',
                                 'dialog.documento.tax.input.focus')),
        ], dividechars=1)

        self.__super.__init__(row)
#}}}
    def set_monto(self, val):#{{{
        if self._tax is not None:
            self.monto_box.set_value(val)
            self._emit('tax-monto-set', val)
#}}}
    def get_monto(self):#{{{
        return self.monto_box.get_value()
#}}}
    monto = property(get_monto, set_monto)

    def get_factor(self):#{{{
        return self.porcentaje.get_value()/100
#}}}
    factor = property(get_factor)

    def _set_tax(self, tax_code):#{{{
        self._tax = get_current_config().impuestos.get(tax_code, None)
        if self._tax is not None:
            self.tax_code.set_edit_text(self._tax['codigo'])
            self.descripcion.set_text(self._tax['nombre'])
            self.porcentaje.set_value(self._tax['alicuota'])
        else:
            self.tax_code.set_edit_text(u"")
            self.descripcion.set_text(u"")
            self.porcentaje.set_text(u"")
            self.monto_box.set_edit_text(u"")
        self._emit('tax-code-set')
#}}}
    def keypress(self, size, key):#{{{
        if key == "ctrl d":
            self._emit("tax-item-delete")
            return None
        return self.__super.keypress(size, key)
#}}}

    ### Signal Handlers ###

    def on_tax_code_edit_done(self, widget, tax_code):#{{{
        if tax_code in get_current_config().impuestos:
            self._set_tax(tax_code)
            self._w.set_focus(3)
        else:
            self._set_tax(None)
            self._emit("tax-code-void-set")
#}}}
    def on_tax_code_focus_out(self, widget):#{{{
        #self._set_tax(widget.get_edit_text())
        pass
#}}}
    def on_monto_box_edit_done(self, widget, monto):#{{{
        self.set_monto(widget.get_value())
        self._emit('tax-item-done')
#}}}
    def on_monto_box_focus_out(self, widget):#{{{
        self.set_monto(widget.get_value())
#}}}
#}}}

class EditorDocumentosEspeciales(Dialog):#{{{

    def __init__(self):#{{{

        self._fecha_error_state = None
        self._documento = None
        self._doctype = None
        self._tercero = None

        def _edit_cancel(widget):
            self.focus_button(1)
        def _neto_selectable():
            return bool(self._tercero.responsabilidad_iva == u'I' if self._tercero else False)
        def _total_selectable():
            return bool(self._tercero.responsabilidad_iva != u'I' if self._tercero else False)

        self.doctype = TipoDocumentoBox(max_length=3)
        connect_signal(self.doctype, 'focus-in', highlight_focus_in)
        connect_signal(self.doctype, 'edit-done', self.on_doctype_edit_done)
        connect_signal(self.doctype, 'edit-cancel', _edit_cancel)

        self.docnumber = IntegerInputBox(min_value=0, max_length=7, align='right')
        self.docnumber.keypress = self._docnumber_keypress
        connect_signal(self.docnumber, 'focus-in', highlight_focus_in)
        connect_signal(self.docnumber, 'edit-done', self.on_docnumber_edit_done)
        connect_signal(self.docnumber, 'edit-cancel', _edit_cancel)

        self.doctype_name = Text(u"", wrap='clip')
        self.action_label = Text(u"", align='right')

        comprobante_row = Columns([
            ('fixed', 14, AttrMap(Text("Comprobante", align='right'), 'dialog.documento.label')),
            ('fixed', 4, AttrMap(self.doctype, 'dialog.documento.input', 'dialog.documento.input.focus')),
            ('fixed', 7, AttrMap(self.docnumber, 'dialog.documento.input', 'dialog.documento.input.focus')),
            AttrMap(self.doctype_name, 'dialog.documento.label'),
            ('fixed', 9, AttrMap(self.action_label, 'dialog.documento.action')),
        ], dividechars=1)

        #self.fecha = DateInputBox()
        self.fecha = DateSelectorBox()
        connect_signal(self.fecha, 'focus-in', self.on_fecha_focus_in)
        connect_signal(self.fecha, 'focus-out', self.on_fecha_focus_out)
        connect_signal(self.fecha, 'edit-cancel', _edit_cancel)
        connect_signal(self.fecha, 'edit-done', self.on_fecha_edit_done)
        connect_signal(self.fecha, 'bad-date-error', self.on_fecha_error)
        self.fecha_error = Text(u"", wrap='clip')

        fecha_row = Columns([
            ('fixed', 14, AttrMap(Text("Fecha", align='right'), 'dialog.documento.label')),
            ('fixed', 8, AttrMap(self.fecha, 'dialog.documento.input', 'dialog.documento.input.focus')),
            AttrMap(self.fecha_error, 'dialog.documento.error'),
        ], dividechars=1)

        self.tercero_label = Text("Tercero", align='right')
        self.tercero_codigo = TerceroBox(max_length=5, align='right')
        connect_signal(self.tercero_codigo, 'focus-in', highlight_focus_in)
        connect_signal(self.tercero_codigo, 'focus-out', self.on_tercero_focus_out)
        connect_signal(self.tercero_codigo, 'edit-done', self.on_tercero_edit_done)
        connect_signal(self.tercero_codigo, 'edit-cancel', _edit_cancel)
        connect_signal(self.tercero_codigo, 'search-client', self.on_tercero_search)
        connect_signal(self.tercero_codigo, 'edit-cliente', self.on_tercero_edit_record)

        self.tercero_nombre = Text(u"", wrap='clip')
        tercero_row = Columns([
            ('fixed', 14, AttrMap(self.tercero_label, 'dialog.documento.label')),
            ('fixed', 8, AttrMap(self.tercero_codigo, 'dialog.documento.input', 'dialog.documento.input.focus')),
            AttrMap(self.tercero_nombre, 'dialog.documento.tercero'),
        ], dividechars=1)

        self.tercero_resp = Text(u"", wrap='clip')
        self.tercero_cuit = Text(u"", wrap='clip')
        tercero_info_row = Columns([
            ('fixed', 14, Divider()),
            AttrMap(self.tercero_resp, 'dialog.documento.tercero'),
            ('fixed', 13, AttrMap(self.tercero_cuit, 'dialog.documento.tercero')),
        ], dividechars=1)

        self.neto = NumericInputBox(min_value=0, max_value=99999.99, default=0)
        connect_signal(self.neto, 'focus-in', highlight_focus_in)
        connect_signal(self.neto, 'focus-out', self.on_neto_total_focus_out)
        connect_signal(self.neto, 'edit-done', self.on_neto_edit_done)
        connect_signal(self.neto, 'edit-cancel', _edit_cancel)

        neto_row = Columns([
            AttrMap(Text("Importe Neto", align='right'), 'dialog.documento.label'),
            ('fixed', 9, AttrMap(self.neto, 'dialog.documento.input', 'dialog.documento.input.focus')),
        ], dividechars=1)
        neto_row.selectable = _neto_selectable

        self.taxes = SimpleListWalker([])
        taxes_list = ListBox(self.taxes)

        self.total = NumericInputBox(min_value=0, max_value=99999.99, default=0)
        connect_signal(self.total, 'focus-in', highlight_focus_in)
        connect_signal(self.total, 'focus-out', self.on_neto_total_focus_out)
        connect_signal(self.total, 'edit-done', self.on_total_edit_done)
        connect_signal(self.total, 'edit-cancel', _edit_cancel)

        total_row = Columns([
            AttrMap(Text("Importe TOTAL", align='right'), 'dialog.documento.label'),
            ('fixed', 9, AttrMap(self.total, 'dialog.documento.input', 'dialog.documento.input.focus')),
        ], dividechars=1)
        total_row.selectable = _total_selectable

        self.participa_iva = CheckBox("Participa libro IVA")
        in_fmt = ('%m%y', '%m%Y', '%m/%y', '%m/%Y', '%m-%y', '%m-%Y', '%m.%y', '%m.%Y')
        #self.periodo_iva = DateInputBox(out_fmt="%m/%Y", in_fmt=in_fmt)
        self.periodo_iva = DateSelectorBox(out_fmt="%m/%Y", in_fmt=in_fmt)
        participa_iva_row = Columns([
            AttrMap(self.participa_iva, 'dialog.documento.input', 'dialog.documento.input.focus'),
            AttrMap(Text("Periodo", align='right'), 'dialog.documento.label'),
            ('fixed', 7, AttrMap(self.periodo_iva, 'dialog.documento.input', 'dialog.documento.input.focus')),
        ], dividechars=1)

        self.content = Pile([
            comprobante_row,
            fecha_row,
            tercero_row,
            tercero_info_row,
            Divider(),
            neto_row,
            Divider("─"),
            ('fixed', 3, AttrMap(taxes_list, 'dialog.documento.tax')),
            Divider("─"),
            total_row,
            Divider(),
            participa_iva_row,
            Divider(),
        ])

        #buttons = [("Grabar", self.save), ("Salir", self._quit)]
        buttons = [("Grabar", self.save), ("Salir", self.quit)]
        self.__super.__init__(self.content, buttons,
                              title="DOCUMENTOS ESPECIALES",
                              height=None,
                              width=65,
                              attr_style='dialog.documento',
                              title_attr_style='dialog.documento.title')
#}}}
    def save(self, *args):#{{{
        fecha = self.fecha.get_value()
        doctype = self._doctype
        tercero = self._tercero
        neto = self.neto.get_value()
        documento = self._documento

        periodo_iva = self.periodo_iva.get_value()

        resp_map = get_current_config().iva_resp_map
        resp = tercero.responsabilidad_iva
        if doctype['tipo'] not in resp_map[resp]['doctypes']:
            show_error(["El tipo de cliente ", ('dialog.warning.important', resp_map[resp]['label']),
                " no es compatible con el tipo de documento ", ('dialog.warning.important', doctype['tipo']),
                ".\n\nCambie el tipo de documento o el tipo de cliente."])
            return

        if self.docnumber.get_value() is None:
            show_error("Falta el número de documento")
            return

        if fecha is None:
            self.fecha_error.set_text("No puede estar vacío")
            return

        def _valid_tax(item):
            return item.tax_code.get_edit_text() in doctype['allowed_taxes']

        filtered_taxes = filter(_valid_tax, self.taxes)

        if len(filtered_taxes) < 1:
            show_error("No hay impuestos validos para este tipo de documento")
            return

        taxes = [Tasa(nombre=t.tax_code.get_edit_text(), monto=t.monto) for t in filtered_taxes]

        if documento is None:
            documento = Documento(tipo=doctype['tipo'], numero=self.docnumber.get_value(), fecha=fecha)
            session.add(documento)

        documento.neto = self.neto.get_value()
        documento.cliente = tercero
        documento.cliente_nombre = tercero.nombre
        documento.cliente_direccion = tercero.direccion
        if tercero.responsabilidad_iva == u'I':
            documento.cliente_cuit = tercero.cuit

        if self.participa_iva.state is True:
            documento.fiscal = doctype['libro_iva']
        else:
            documento.fiscal = None

        if periodo_iva is not None:
            if periodo_iva.month != documento.fecha.month or\
                    periodo_iva.year != documento.fecha.year:
                documento.periodo_iva = periodo_iva
            else:
                documento.periodo_iva = None
        else:
            documento.periodo_iva = None

        documento.tasas = taxes
        session.add_all(taxes)
        session.commit()

        self.reset_dialog()
        self._pile.set_focus(0)
        self.content.set_focus(0)
        self.content.widget_list[0].set_focus(1)
#}}}
    def reset_dialog(self):#{{{
        self._documento = None
        self._doctype = None
        self.doctype.set_edit_text(u"")
        self.docnumber.set_edit_text(u"")
        self.doctype_name.set_text(u"")
        self.action_label.set_text(u"")
        self.fecha.set_edit_text(u"")
        self.rellenar_tercero(None)
        self.clear_taxes()
        self.participa_iva.set_state(True)
        self.periodo_iva.set_edit_text(u"")
#}}}
    def rellenar_tercero(self, tercero=None):#{{{
        if isinstance(tercero, Cliente):
            self._tercero = tercero
            self.tercero_codigo.set_edit_text(tercero.codigo)
            self.tercero_nombre.set_text(tercero.nombre)
            resp_label = get_current_config().iva_resp_map[tercero.responsabilidad_iva]['label']
            self.tercero_resp.set_text(resp_label)
            self.tercero_cuit.set_text(tercero.cuit)
        else:
            self._tercero = None
            self.tercero_codigo.set_edit_text(u"")
            self.tercero_nombre.set_text(u"")
            self.tercero_resp.set_text(u"")
            self.tercero_cuit.set_text(u"")
#}}}
    def _try_load_document(self):#{{{
        doc_tipo = self._doctype['tipo']
        doc_number = self.docnumber.get_value()
        doc_date = self.fecha.get_value()

        try:
            doc = session.query(Documento).filter_by(tipo=doc_tipo,
                                                     numero=doc_number,
                                                     fecha=doc_date).one()
        except NoResultFound:
            self._documento = None
            self.action_label.set_text("Nuevo")
            self.rellenar_tercero(None)
            self.clear_taxes()
            return

        if doc == self._documento:
            return

        self._documento = doc
        self.taxes[:] = []

        self.action_label.set_text("Modificar")
        self.rellenar_tercero(self._documento.cliente)
        self.neto.set_value(self._documento.neto)
        for t in self._documento.tasas:
            self.add_tax_item(t.nombre, t.monto)
        self.calc_total()
        if self._documento.fiscal is not None:
            self.participa_iva.set_state(True)
        else:
            self.participa_iva.set_state(False)
        if self._documento.periodo_iva is not None:
            self.periodo_iva.set_value(self._documento.periodo_iva)
#}}}
    def clear_taxes(self):#{{{
        self.taxes[:] = []
        self.neto.set_edit_text(u"")
        self.total.set_edit_text(u"")
#}}}
    def add_tax_item(self, tax_code=None, monto=None):#{{{
        ti = TaxItem()
        connect_signal(ti, 'tax-monto-set', self.on_tax_monto_set)
        connect_signal(ti, 'tax-code-set', self.on_tax_code_set)
        connect_signal(ti, 'tax-code-void-set', self.on_tax_code_void_set)
        connect_signal(ti, 'tax-item-done', self.on_tax_item_done)
        connect_signal(ti, 'tax-item-delete', self.on_tax_item_delete)
        connect_signal(ti, 'tax-item-edit-cancel', lambda w: self.focus_button(1))
        self.taxes.append(ti)
        if tax_code is not None:
            ti._set_tax(tax_code)
            if monto is not None:
                ti.set_monto(monto)
#}}}
    def calc_taxes(self):#{{{
        if self._tercero:
            if self._tercero.responsabilidad_iva == u'I':
                neto = self.neto.get_value()
            else:
                total = self.total.get_value()
                if total is not None:
                    neto = total / (1 + sum(filter(None, [ti.factor for ti in self.taxes])))
                else:
                    neto = self.neto.get_value()
            for ti in self.taxes:
                ti.set_monto(neto*ti.factor)
            self.calc_total_or_neto()
#}}}
    def calc_total(self):#{{{
        if self.neto.get_value():
            total = self.neto.get_value() + sum(filter(None, [ti.monto for ti in self.taxes]))
            self.total.set_value(total)
#}}}
    def calc_neto(self):#{{{
        if self.total.get_value():
            neto = self.total.get_value() - sum(filter(None, [ti.monto for ti in self.taxes]))
            self.neto.set_value(neto)
#}}}
    def calc_total_or_neto(self):#{{{
        if self._tercero is not None:
            if self._tercero.responsabilidad_iva == u'I':
                self.calc_total()
            else:
                self.calc_neto()
#}}}
    def _check_futuro(self):#{{{
        if self.fecha_error.get_text()[0] == u"":
            d = self.fecha.value
            if d:
                f = date.today() + timedelta(days=1)
                if d >= f:
                    self.fecha_error.set_text("CUIDADO: Fecha futura")
                else:
                    self.fecha_error.set_text(u"")
#}}}
    def _docnumber_keypress(self, size, key):#{{{
        wid = self.docnumber
        if key == 'ctrl n':
            doctype = self.doctype.get_edit_text()
            if doctype != u"" and doctype in get_current_config().documentos:
                self.docnumber.set_value(get_next_docnumber(doctype))
                self.action_label.set_text("Nuevo")
                self.fecha.set_value(date.today())
                self.clear_taxes()
                self.on_next_focus()
        return wid.__class__.keypress(wid, size, key)
#}}}
    def _focus_neto(self):#{{{
        self.content.set_focus(5)
#}}}
    def _focus_taxes(self):#{{{
        self.content.set_focus(7)
#}}}
    def _focus_total(self):#{{{
        self.content.set_focus(9)
#}}}

    ### Signals Handlers ###

    def on_next_focus(self, *args):#{{{
        c = self.content
        focus_index = c.widget_list.index(c.focus_item)
        c.set_focus(focus_index+1)
        if not c.focus_item.selectable():
            self.on_next_focus()
#}}}
    def on_doctype_edit_done(self, widget, tipo_doc):#{{{
        doctype = get_current_config().documentos.get(tipo_doc, None)
        if doctype:
            if doctype['libro_iva']:
                if self._tercero and self._tercero.relacion != doctype['tercero']:
                    self.rellenar_tercero(None)
                self._doctype = doctype
                self.doctype_name.set_text(doctype['nombre'])
                self.clear_taxes()
                self.tercero_label.set_text("Cliente" if doctype['tercero'] == u'C' else "Proveedor")
                self.content.widget_list[0].set_focus(2)
            else:
                show_error("Este documento no se puede editar aquí.")
                highlight_focus_in(widget)
        else:
            show_error("El tipo de documento ingresado no existe, ingrese"
                       " un tipo de documento correcto.")
            highlight_focus_in(widget)
#}}}
    def on_docnumber_edit_done(self, widget, number):#{{{
        if number != u"":
            self._try_load_document()
            self.on_next_focus()
#}}}
    def on_fecha_focus_in(self, widget):#{{{
        if self._fecha_error_state is None:
            self.fecha_error.set_text(u"")
            highlight_focus_in(widget)
#}}}
    def on_fecha_focus_out(self, widget):#{{{
        self._fecha_error_state = None
        self.fecha_error.set_text(u"")
        self._check_futuro()
        self._try_load_document()
#}}}
    def on_fecha_edit_done(self, widget, *text):#{{{
        if self._fecha_error_state is not None:
            self.fecha_error.set_text(self._fecha_error_state)
            self._fecha_error_state = None
            highlight_focus_in(widget)
            return
        else:
            self.fecha_error.set_text(u"")
            self._try_load_document()
            self.on_next_focus()
#}}}
    def on_fecha_error(self, widget, msg):#{{{
        self._fecha_error_state = msg
        self.fecha_error.set_text(msg)
#}}}
    def on_tercero_focus_out(self, widget):#{{{
        try:
            codigo = int(widget.get_edit_text())
        except ValueError:
            self.rellenar_tercero(None)
            return

        if self._tercero is None or (self._tercero.codigo != codigo):
            try:
                c = session.query(Cliente).filter(Cliente.codigo==codigo)\
                                          .filter(Cliente.relacion==self._doctype['tercero']).one()
            except NoResultFound:
                self.rellenar_tercero(None)
                return
            self.rellenar_tercero(c)
#}}}
    def on_tercero_edit_done(self, widget, cod_tercero):#{{{
        try:
            c = session.query(Cliente).filter(Cliente.codigo==int(cod_tercero))\
                                      .filter(Cliente.relacion==self._doctype['tercero']).one()
        except (NoResultFound, ValueError):
            return
        self.rellenar_tercero(c)
        if self._tercero.responsabilidad_iva == u'I':
            self._focus_neto()
        else:
            self._focus_total()
#}}}
    def on_tercero_search(self, widget, search_by=None, first_key=None):#{{{
        response = search_terceros(search_by=search_by, rel=self._doctype['tercero'], first_key=first_key)
        if response:
            self.rellenar_tercero(response[0])
            self.on_next_focus()
        return None
#}}}
    def on_tercero_edit_record(self, widget, cod_tercero):#{{{
        try:
            cod_tercero = unicode(int(cod_tercero))
        except ValueError:
            cod_tercero = "new"

        if cod_tercero in get_current_config().clientes_especiales:
            cod_tercero = "new"

        tercero = maestro_terceros(filled_with=cod_tercero, once=True, rel=self._doctype['tercero'])

        if tercero is not None:
            self.rellenar_tercero(tercero)
            self.on_next_focus()
#}}}
    def on_neto_total_focus_out(self, widget):#{{{
        self.calc_taxes()
#}}}
    def on_neto_edit_done(self, widget, val):#{{{
        if not val:
            return
        if len(self.taxes) == 0:
            self.add_tax_item(tax_code=self._doctype['default_tax'])
        self._focus_taxes()
        self.taxes[0]._w.set_focus(0)
        self.calc_taxes()
#}}}
    def on_total_edit_done(self, widget, val):#{{{
        if not val:
            return
        if len(self.taxes) == 0:
            self.add_tax_item(tax_code=self._doctype['default_tax'])
        self._focus_taxes()
        self.taxes[0]._w.set_focus(0)
        self.calc_taxes()
#}}}

    # TaxItems signals hanlders
    def on_tax_monto_set(self, widget, monto):#{{{
        self.calc_total_or_neto()
#}}}
    def on_tax_code_set(self, widget):#{{{
        self.calc_taxes()
#}}}
    def on_tax_code_void_set(self, widget):#{{{
        self.focus_button(0)
#}}}
    def on_tax_item_done(self, widget):#{{{
        next_idx = self.taxes.get_focus()[1] + 1
        if next_idx == len(self.taxes):
            self.add_tax_item()
        self.taxes.set_focus(next_idx)
        self.taxes[next_idx]._w.set_focus(0)
#}}}
    def on_tax_item_delete(self, widget):#{{{
        idx = self.taxes.index(widget)
        del self.taxes[idx]
        self.calc_taxes()
#}}}
#}}}
class PriceBatchModifier(Dialog):#{{{

    def __init__(self):#{{{

        def _edit_cancel(widget):
            self.focus_button(1)

        self.agrupaciones = InputBox(max_length=50)
        self.agrupaciones.filter_input = lambda t: t.upper()
        connect_signal(self.agrupaciones, "focus-in", self.on_agrupaciones_focus_in)
        connect_signal(self.agrupaciones, "edit-done", self.on_agrupaciones_edit_done)
        connect_signal(self.agrupaciones, "edit-cancel", _edit_cancel)

        row_agrupaciones = Columns([
            ('fixed', 11, AttrMap(Text("Agrupación"), 'dialog.pricemodifier.label')),
            AttrMap(self.agrupaciones, 'dialog.pricemodifier.input', 'dialog.pricemodifier.input.focus'),
        ], dividechars=1)

        self.factor = NumericInputBox(min_value=0, max_value=10, digits=4, max_digits=4)
        connect_signal(self.factor, "focus-in", highlight_focus_in)
        connect_signal(self.factor, "edit-done", self.on_factor_edit_done)
        connect_signal(self.factor, "edit-cancel", _edit_cancel)

        self.cantidad_articulos = Text("", wrap='clip', align='right')
        row_factor = Columns([
            ('fixed', 11, AttrMap(Text("Factor"), 'dialog.pricemodifier.label')),
            ('fixed', 7, AttrMap(self.factor, 'dialog.pricemodifier.input', 'dialog.pricemodifier.input.focus')),
            AttrMap(Text(u"Artículos", align='right'), 'dialog.pricemodifier.label'),
            ('fixed', 7, AttrMap(self.cantidad_articulos, 'dialog.pricemodifier.input')),
        ], dividechars=1)

        self.content = Pile([
            row_agrupaciones,
            row_factor,
            Divider(),
        ])

        #buttons = [("Grabar", self.save), ("Salir", self._quit)]
        buttons = [("Grabar", self.save), ("Salir", self.quit)]
        self.__super.__init__(self.content, buttons,
                              title=u"MODIFICA PRECIOS por agrupación",
                              height=None,
                              width=65,
                              attr_style='dialog.pricemodifier',
                              title_attr_style='dialog.pricemodifier.title')
#}}}
    def save(self, btn):#{{{
        now = datetime.now()
        agrupaciones = self.agrupaciones.get_edit_text()
        if agrupaciones == "":
            self._pile.set_focus(0)
            self.content.set_focus(0)
            return
        agrupaciones = set([ag.strip() for ag in agrupaciones.split(",")])
        query = session.query(Articulo).filter(Articulo.es_activo==True)\
                       .filter(Articulo.agrupacion.in_(agrupaciones))
        qty = query.count()
        if qty < 1:
            self._pile.set_focus(0)
            self.content.set_focus(0)
            return

        factor = self.factor.get_value()
        if factor is None or factor < Decimal('0.00001'):
            self._pile.set_focus(0)
            self.content.set_focus(1)
            return

        message_waiter(u" Procesando información ... ")
        PriceBatchModifierPreview(agrupaciones, factor).run()
        cont = show_warning(u"¿Confirma esta modificación?\n",
                [(u"Sí", True), (u"No", False)], title="CONFIRMACIÓN", focus_button=1)
        if cont is not True:
            return

        for article in query:
            article.precio = (article.precio * factor).quantize(q)
            article.vigencia = now
        session.commit()
        self.quit()
#}}}
    def on_factor_edit_done(self, widget, text):#{{{
        if text != "":
            self.focus_button(0)
#}}}
    def on_agrupaciones_focus_in(self, widget):#{{{
        self.cantidad_articulos.set_text("")
#}}}
    def on_agrupaciones_edit_done(self, widget, text):#{{{
        if text == "":
            return None

        agrupaciones = set([ag.strip() for ag in text.split(",")])

        qty = session.query(Articulo).filter(Articulo.es_activo==True)\
                     .filter(Articulo.agrupacion.in_(agrupaciones)).count()
        self.cantidad_articulos.set_text(unicode(qty))
        self.content.set_focus(1)
#}}}
#}}}

from nobix.treetools import DictNode, TreeListWalker, TreeListBox

class PriceBatchModifierPreview(Dialog):#{{{

    def __init__(self, agrupaciones, factor):#{{{
        header = Pile([
            AttrMap(Text([('listado.title.important', u"Verificar modificación de Precios"),
                          u" (x %s)" % unicode(factor).replace(".",",")],
                align='center', wrap='clip'), 'listado.title'),
            AttrMap(Text(u"   %-14s %-40s  %8s  → %8s" % (
                    u"Código", u"Descripción", u"Original", u"Nuevo"
                ), wrap='clip'), 'listado.list_header'),
        ])

        key = 'listado.footer.important'
        footer = Text([
            (key, "+"), "/", (key, "-"), u" expandir/colapsar   ",
            (key, "ESC"), ",", (key, "ENTER"), ",",
            (key, "ESPACIO"), " o ", (key, "F10"),
            u" para continuar"], align='right')

        lista = TreeListBox(TreeListWalker(self.build_tree(agrupaciones, factor)))

        self.content = Frame(
                AttrMap(lista, 'listado.body'),
                header=header,
                footer=AttrMap(footer, 'listado.footer'))

        self.__super.__init__(self.content,
                height=('relative', 100),
                width=('relative', 100),
                with_border=False)
#}}}
    def keypress(self, key):#{{{
        if key in ('enter', 'esc', ' ', 'f10'):
            self.quit()
        return self.__super.keypress(key)
#}}}
    def build_tree(self, agrupaciones, factor):#{{{
        tree = []
        m = functools.partial(moneyfmt, sep='.', dp=',')
        base_query = session.query(Articulo).filter(Articulo.es_activo==True)
        for ag in agrupaciones:
            items = []
            for a in base_query.filter(Articulo.agrupacion==ag):
                items.append(u"%-14s %-40s  %8s  → %8s" %\
                        (a.codigo[:14], a.descripcion[:40], m(a.precio), m(a.precio*factor)))

            dn = DictNode({'display_text': "%s (%s)" % (ag, len(items)), 'childs': items})
            tree.append(dn)
        return tree
#}}}
#}}}

class ListPrinter(Dialog):#{{{
    content = None
    buttons = None

    _formatters = {#{{{
        'unicode': lambda d, f: unicode(d),
        'date': lambda d, f: d.strftime(f or _date_pattern) if isinstance(d, datetime) else unicode(d),
        'decimal': lambda d, f: moneyfmt(d, sep='.', dp=',') if isinstance(d, Decimal) else unicode(d),
    }#}}}
    _aligners = {#{{{
        'left': lambda s, w: s[:w].ljust(w),
        'center': lambda s, w: s[:w].center(w),
        'right': lambda s, w: s[:w].rjust(w),
    }#}}}

    def __init__(self, doctype, title, show_dialog=True):#{{{
        self.doctype = get_current_config().documentos.get(doctype, None)
        if self.doctype is None:
            show_error([u"El tipo de documento ", ('dialog.error.important', u"%s" % doctype),
                u" no existe, probablemente es un error en la configuración."])
            #self.must_quit = True
            self.quit()
            return

        if not show_dialog:
            res = self.imprimir()
            self.run = lambda *args: res
            return

        if self.content is None:
            self.content = Pile([Text("Default list printer content", align='center'), Divider()])

        if self.buttons is None:
            #self.buttons = [("Imprimir", self.imprimir), ("Salir", self._quit)]
            self.buttons = [("Imprimir", self.imprimir), ("Salir", self.quit)]

        self.__super.__init__(self.content, self.buttons,
                              title=title,
                              height=None,
                              width=65,
                              attr_style='dialog.listprinter',
                              title_attr_style='dialog.listprinter.title')
#}}}
    def _imprimir(self, data):#{{{

        if not hasattr(self, 'impresora'):
            impresora = self.select_printer()
            if impresora is None:
                return
            self.impresora = impresora

        total_count = data['doc_total_count'] = len(data['pages'])
        for i in xrange(total_count):
            data.update({
                'doc_count': i+1,
                'groups': data['pages'][i],
            })

            success, printed_data = self.impresora.run_list_print(data)
            if success:
                if 'warnings' in printed_data and printed_data['warnings']:
                    show_warning(
                        [u"La impresión fue exitosa pero el controlador envió el siguiente mensaje:\n\n",
                         ('dialog.warning.important', u"\n".join(printed_data['warnings'])), u'\n'])
            elif printed_data is not None:
                if not 'errors' in printed_data or not printed_data['errors']:
                    printed_data['errors'] = [u"Error desconocido"]
                show_error([u"Se produjo un error al imprimir:\n\n",
                            ('dialog.error.important', u"\n".join(printed_data['errors']))])
                break

        #self._quit()
        self.quit()
#}}}
    def select_printer(self):#{{{
        impresoras = printers.get_printers(self.doctype['printer'])
        if len(impresoras) > 1:
            idx = choose_printer(impresoras)
            if idx is None:
                return None
        else:
            idx = 0
        impresora = impresoras[idx]

        if not hasattr(impresora, 'run_list_print') or not callable(impresora.run_list_print):
            show_error([u"La impresora seleccionada ", ('dialog.error.important', u"%s" % impresora.name),
                " no puede imprimir el listado."])
            #self.must_quit = True
            self.quit()
            return None
        return impresora
#}}}
    def _build_base_data(self):#{{{
        data = dict((opt[6:], val) for opt, val in self.doctype.iteritems() if opt.startswith('print_'))
        data['title'] = self.doctype.get('nombre')
        return data
#}}}
    def _fetch_groups(self, grouped_by, grouper, cls, only_actives=True):#{{{
        query = session.query(cls).filter(getattr(cls, grouped_by).in_(grouper))
        if only_actives and hasattr(cls, 'es_activo'):
            query = query.filter(cls.es_activo==True)
        query = query.order_by(getattr(cls, grouped_by).asc(), cls.codigo.asc())
        return itertools.groupby(list(query), key=operator.attrgetter(grouped_by))
#}}}
    def _build_groups(self, groups):#{{{
        columns = self.doctype.get('columns', [])
        columns_headers = []
        for spec in columns:
            label, col, width, align, fmt = spec
            if align is None: align = "left"
            text = self._aligners[align](label or u"", width)
            columns_headers.append(text)
        columns_headers = u" ".join(columns_headers)

        grupos = []
        for group, objs in groups:
            items = []
            for art in list(objs):
                item = []
                for spec in columns:
                    label, col, width, align, fmt = spec
                    if align is None: align = "left"
                    if fmt is None: fmt = "unicode"
                    attr = getattr(art, col) if col is not None else ""
                    fmt_args = fmt.split(",")
                    fmt = fmt_args[0]
                    args = None
                    if len(fmt_args) == 2:
                        args = fmt_args[1]
                    val = self._formatters[fmt](attr, args)
                    val = self._aligners[align](val, width)
                    item.append(val)
                items.append(u" ".join(item))
            grupos.append((group, columns_headers, items))
        return grupos
#}}}
    def _pageize(self, groups, max_rows=32):#{{{
        pages = []
        while len(groups) > 0:
            rows = 0
            page = []

            while rows < max_rows:
                if len(groups) < 1: break
                group = groups.pop(0)
                title, header, items = group
                if title != "": rows += 2
                if header != "": rows += 1
                rest = max_rows - rows
                if rest > 0:
                    _in, _out = items[:rest], items[rest:]
                    if len(_out) > 0:
                        groups.insert(0, (title, header, _out))
                    if len(_in) > 0:
                        rows += len(_in)
                        page.append((title, header, _in))
                else:
                    groups.insert(0, group)
            pages.append(page)
        return pages
#}}}
    def imprimir(self, btn=None):#{{{
        raise NotImplementedError("This method must be implemented in subclasses")
#}}}
#}}}
class GroupListPrinter(ListPrinter):#{{{

    def __init__(self):#{{{

        self.agrupaciones = InputBox(max_length=50)
        self.agrupaciones.filter_input = lambda t: t.upper()
        connect_signal(self.agrupaciones, "focus-in", self.on_agrupaciones_focus_in)
        connect_signal(self.agrupaciones, "edit-done", self.on_agrupaciones_edit_done)
        connect_signal(self.agrupaciones, "edit-cancel", lambda w: self.focus_button(1))

        row_agrupaciones = Columns([
            ('fixed', 10, AttrMap(Text("Agrupación"), 'dialog.listprinter.label')),
            AttrMap(self.agrupaciones, 'dialog.listprinter.input', 'dialog.listprinter.input.focus'),
        ], dividechars=1)

        self.cantidad_articulos = Text("", wrap='clip', align='left')

        row_cantidad = Columns([
            ('fixed', 10, AttrMap(Text(u"Artículos", align="right"), 'dialog.listprinter.label')),
            ('fixed', 7, AttrMap(self.cantidad_articulos, 'dialog.listprinter.input')),
        ], dividechars=1)

        self.include_inactives = CheckBox(u"Incluir Inactivos", state=True,
                on_state_change=self.on_include_inactives_change)
        row_include_inactives = Columns([
            ('fixed', 10, Divider()),
            AttrMap(self.include_inactives, 'dialog.listprinter.label'),
        ], dividechars=1)

        self.content = Pile([
            row_agrupaciones,
            row_cantidad,
            row_include_inactives,
            Divider(),
        ])

        self.__super.__init__(AGRUP_LIST_DOCTYPE, "IMPRIME LISTA por agrupación")
#}}}
    def imprimir(self, btn=None):#{{{
        agrupaciones = self.agrupaciones.get_edit_text()
        if agrupaciones == "":
            self._pile.set_focus(0)
            self.content.set_focus(0)
            show_error("El campo agrupación no puede estar vacío")
            return

        message_waiter(u" Procesando información ... ")
        agrupaciones = set([ag.strip() for ag in agrupaciones.split(",")])
        qty = self._get_agrupaciones_query().count()
        if qty < 1:
            self._pile.set_focus(0)
            self.content.set_focus(0)
            return

        data = self._build_base_data()

        grouped = self.doctype.get('grouped')

        groups = self._fetch_groups(grouped, agrupaciones, Articulo, not self.include_inactives.get_state())
        groups = self._build_groups(groups)

        data['pages'] = self._pageize(groups, data['max_rows'])

        return self._imprimir(data)
#}}}

    def on_agrupaciones_focus_in(self, widget):#{{{
        self.cantidad_articulos.set_text("")
#}}}
    def on_agrupaciones_edit_done(self, widget, text):#{{{
        if text == "":
            return None
        self._update_articles_qty()
        self.focus_button(0)
#}}}
    def on_include_inactives_change(self, widget, new_state):
        self._update_articles_qty(include_inactives=new_state)

    def _update_articles_qty(self, include_inactives=None):
        qty = self._get_agrupaciones_query(include_inactives).count()
        self.cantidad_articulos.set_text(unicode(qty))

    def _get_agrupaciones_query(self, include_inactives=None):
        agrupaciones = set([ag.strip() for ag in self.agrupaciones.get_edit_text().split(",")])
        query = session.query(Articulo).filter(Articulo.agrupacion.in_(agrupaciones))
        if include_inactives is None:
            include_inactives = self.include_inactives.get_state()
        if include_inactives is False:
            query = query.filter(Articulo.es_activo==True)
        return query
#}}}

TempListArticleItem = namedtuple("TempListArticleItem", "codigo descripcion agrupacion proveedor "
                                 "vigencia cantidad precio")

class TemporaryListPrinter(ListPrinter):#{{{
    _default_prefix = u"ARTÍCULOS "
    _default_title = u"PARA PREPARAR"
    _default_postfix = u" (por %s)"

    def __init__(self, vendedor, items):#{{{
        self.vendedor = vendedor
        self.items = self._prepare_items(items)
        self.titulo = InputBox(edit_text=self._default_title, max_length=50)
        self.titulo.filter_input = lambda t: t.upper()
        connect_signal(self.titulo, "edit-done", lambda w, t: self.focus_button(0))
        connect_signal(self.titulo, "edit-cancel", lambda w: self.focus_button(1))

        row_titulo = Columns([
            ('fixed', 10, AttrMap(Text("Título", align='right'), 'dialog.listprinter.label')),
            AttrMap(self.titulo, 'dialog.listprinter.input', 'dialog.listprinter.input.focus'),
        ], dividechars=1)

        if len(self.items) < 6:
            msg = u"Esta seguro que quiere imprimir una lista tan corta?"
            extra = [Divider(),
                     Columns([
                         AttrMap(Text(msg, align='center', wrap='clip'), 'dialog.listprinter.error')
                     ])]
        else:
            msg = u""
            extra = []

        row_cantidad = Columns([
            ('fixed', 10, AttrMap(Text(u"Artículos", align="right"), 'dialog.listprinter.label')),
            ('fixed', 7, AttrMap(Text(u"%s" % len(items), wrap='clip'), 'dialog.listprinter.input')),
        ], dividechars=1)

        self.content = Pile([
            row_titulo,
            row_cantidad] + extra + [Divider()])

        self.__super.__init__("TEMP_LISTPRINT", "IMPRIME LISTA de artículos")
#}}}
    def imprimir(self, btn=None):#{{{
        titulo = self._default_prefix + self.titulo.get_edit_text()
        subtitle = self._default_postfix % self.vendedor
        data = self._build_base_data()
        data['title'] = titulo

        groups = self._build_groups([(subtitle, self.items)])
        data['pages'] = self._pageize(groups, data['max_rows'])

        return self._imprimir(data)
#}}}
    def _prepare_items(self, items):#{{{
        retval = []
        for item in items:
            articulo = item.articulo
            if isinstance(articulo, Articulo):
                a = TempListArticleItem(articulo.codigo, articulo.descripcion, articulo.agrupacion,
                        articulo.proveedor, articulo.vigencia, item.cantidad,
                        (articulo.precio if item.precio is None else item.precio))
            elif isinstance(articulo, basestring):
                a = TempListArticleItem("", articulo, "", "", "", item.cantidad, item.precio)
            else:
                raise RuntimeError("Unknown item type '%s'" % type(articulo).__name__)
            retval.append(a)
        return retval
#}}}
#}}}

class ReportListPrinter(ListPrinter):#{{{

    def __init__(self, start_date=None, end_date=None, period=None):#{{{
        self.period = period
        if start_date is None:
            start_date = period + relativedelta(day=1)
        self.start_date = start_date
        if end_date is None:
            end_date = period + relativedelta(day=31)
        self.end_date = end_date

        if period:
            self.stitle = " (periodo %s)" % period.strftime("%m/%Y")
        else:
            dfmt = "%d/%m/%y"
            self.stitle = " (%s - %s)" % (start_date.strftime(dfmt), end_date.strftime(dfmt))

        self.__super.__init__("REPORT_LISTPRINT", "IMPRIME REPORTE", show_dialog=False)
#}}}
    def get_date_condition(self):#{{{
        if self.period:
            date_condition = or_(
                Documento.periodo_iva==self.period,
                and_(Documento.periodo_iva==None,
                     Documento.fecha.between(self.start_date, self.end_date))
                )
        else:
            date_condition = or_(
                Documento.periodo_iva.between(self.start_date, self.end_date),
                and_(Documento.periodo_iva==None,
                     Documento.fecha.between(self.start_date, self.end_date))
            )
        return date_condition
#}}}
    def imprimir(self, btn=None):#{{{
        self.impresora = self.select_printer()
        if self.impresora is None:
            return

        message_waiter(u" Procesando información ... ")
        data = self._build_base_data()
        data['title'] = (u"Resumen de %s" % get_current_config().sucursal) + self.stitle
        data['pages'] = self._build_pages(data)

        return self._imprimir(data)
#}}}
    def _build_pages(self, data):#{{{

        FArticulo = namedtuple('FArticulo', "codigo descripcion agrupacion")

        pages = []

        include = {'venta': [u'FAC', u'FAA', u'NNC', u'NCA', u'REM'],
                   'compra': [u'VFA', u'VNC', u'VND']}
        aprox = [u'REM']
        m = functools.partial(moneyfmt, sep='.', dp=',')
        _ig = operator.itemgetter
        _zero = Decimal(0)

        date_condition = self.get_date_condition()
        query = session.query(Documento).filter(date_condition)\
                       .outerjoin(Documento.tasas)\
                       .outerjoin(Documento.items)\
                       .options(contains_eager(Documento.tasas))\
                       .options(contains_eager(Documento.items))

        total = {u'venta': _zero, u'compra': _zero}
        neto = {u'venta': _zero, u'compra': _zero}
        tasas = {u'venta': _zero, u'compra': _zero}
        tablas = {u'venta': {}, u'compra': {}}
        collector = defaultdict(list)
        vend_docs = defaultdict(lambda: defaultdict(list))
        vend_agrup = defaultdict(lambda: defaultdict(list))
        clie_docs = defaultdict(lambda: defaultdict(list))
        top_items = defaultdict(list)

        for doc in query:

            doctype = doc.tipo
            collector[doctype].append((doc.id, doc.total, doc.neto, sum([t.monto for t in doc.tasas])))
            vend_docs[doc.vendedor][doctype].append((doc.id, doc.total))
            if doc.cliente and doc.cliente.codigo > 50 and doc.cliente.relacion == u'C':
                clie_docs[doc.cliente][doctype].append((doc.id, doc.total))


            if doc.fiscal is not None:
                s = 1 if doc.fiscal[0] == '+' else -1
                col = doc.fiscal[1:]
                total[col] += s*doc.total
                neto[col] += s*doc.neto
                tasas[col] += s*sum([t.monto for t in doc.tasas])

                tablas[col][doc.tipo] = tablas[col].get(doc.tipo, []) +\
                                        [doc.total, doc.neto, sum([t.monto for t in doc.tasas])]

            if doc.tipo in (u'FAA', u'FAC', u'REM'):
                for item in doc.items:
                    key = item.articulo if item.articulo else FArticulo("", item.descripcion, "")
                    top_items[key].append((item.cantidad, item.precio))
                    vend_agrup[doc.vendedor][key.agrupacion].append((item.cantidad, item.precio, doc.tipo))

        # Ventas y Compras
        tots = dict([(t, [
            " ".join(["Total:".rjust(21), (" $ %12s" % m(total[t]))[:15]]),
            " ".join(["Neto:".rjust(21), (" $ %12s" % m(neto[t]))[:15]]),
            " ".join(["Impuestos:".rjust(21), (" $ %12s" % m(tasas[t]))[:15]])
        ]) for t in ("venta", "compra")])

        detail = dict([(t, ["%8s %3s $ %12s%s" % ("(%s)" % len(collector[i]), i,
            m(sum(map(operator.itemgetter(1), collector[i]))), "*" if i in aprox else "")
            for i in include[t] if i in collector
        ]) for t in ("venta", "compra")])

        # Page 1
        pages.append([(k, " ", ["%-48s %s" % (p, q) for p, q in
            itertools.izip_longest(tots[t], detail[t], fillvalue=" ")] + [""])
            for k, t in [("Ventas", "venta"), ("Compras", "compra")]])

        del collector
        del tots
        del detail
        del total, neto, tasas

        # Vendedores
        vdata = defaultdict(dict)
        vend = get_current_config().vendedores
        for vcode, vdocs in vend_docs.iteritems():
            vkey = vend[vcode]['nombre'] if vcode in vend else vcode
            ndata = dict([(k, (len(v), sum(map(operator.itemgetter(1), v)))) for k, v in vdocs.iteritems()])
            vdata[vkey].update(dict([
                (k, tuple(map(sum, zip(vdata[vkey].get(k, (0, _zero)), ndata.get(k, (0, _zero))))))\
                    for k in ndata]))

        for k, v in vdata.iteritems():
            v[u'FAC+FAA'] = tuple(map(sum, zip(v.get(u'FAC', (0, _zero)), v.get(u'FAA', (0, _zero)))))

        vdata = sorted([(k, v) for k, v in vdata.iteritems()], key=lambda e: e[1][u'FAC+FAA'][1], reverse=True)

        cols = (u'FAC+FAA', u'REM', u'PRE')

        pages[0].extend([("Vendedores",
            " ".ljust(24) + " ".join([s.center(21) for s in cols]),
            ["%22s: %s" % (name,
                " ".join([
                    (" %11s  %-7s" % ((m(vals[key][1]) if vals[key][1] else " "),
                                      (("(%s)%s" % (vals[key][0], ("*" if key in aprox else " ")))
                                          if vals[key][0] else " "))) if key in vals else ("%21s" % "")
                for key in cols])
            ) for name, vals in vdata if name] + [""])])

        # Clientes
        cdata = defaultdict(dict)
        for cliente, cdocs in clie_docs.iteritems():
            ndata = dict([(k, (len(v), sum(map(operator.itemgetter(1), v)))) for k, v in cdocs.iteritems()])
            cdata[cliente].update(dict([
                (k, tuple(map(sum, zip(cdata[cliente].get(k, (0, _zero)), ndata.get(k, (0, _zero))))))\
                    for k in ndata]))

        for k, v in cdata.iteritems():
            v[u'FAC+FAA'] = tuple(map(sum, zip(v.get(u'FAC', (0, _zero)), v.get(u'FAA', (0, _zero)))))

        cdata = sorted([(k, v) for k, v in cdata.iteritems()],
                       key=lambda e: e[1][u'FAC+FAA'][1]+e[1].get(u'REM', (0, _zero))[1]*Decimal('0.9'),
                       reverse=True)

        pages[0].extend([("Top 20 Clientes",
            " ".ljust(36) + " ".join([s.center(18) for s in cols]),
            ["%34s %s" % (unicode(c.nombre or '~')[:34],
                " ".join([
                    (" %11s %-5s" % ((m(vals[key][1]) if vals[key][1] else " "),
                                    (("(%s)%s" % (vals[key][0], ("*" if key in aprox else " ")))
                                        if vals[key][0] else " "))) if key in vals else ("%18s" % " ")
                for key in cols])
            ) for c, vals in cdata[:20]])])

        # Articulos
        for icode, idata in top_items.iteritems():
            top_items[icode] = map(sum, zip(*[(i[0], i[0]*i[1]) for i in idata]))

        qdata = sorted([(a, d) for a, d in top_items.iteritems()],
                key=lambda e: e[1][0], reverse=True)[:50]
        mdata = sorted([(a, d) for a, d in top_items.iteritems()],
                key=lambda e: e[1][1], reverse=True)[:50]

        del cdata, top_items, idata, icode

        header = u"%-14s %-40s  %-16s %9s %10s" % (u"Código", u"Descripción", u"Agrupación",
                                                   u"Cantidad", u"Total")

        # Page 2
        pages.append([
            (u"Top Artículos por Monto", header, [u"%-14s %-40s  %-16s %9s %10s" %\
                (a.codigo, a.descripcion[:40], a.agrupacion[:16], m(i[0], places=0), m(i[1]))
                for a, i in mdata[:25]]),
            (u"Top Artículos por Cantidad", header, [u"%-14s %-40s  %-16s %9s %10s" %\
                (a.codigo, a.descripcion[:40], a.agrupacion[:16], m(i[0], places=0), m(i[1]))
                for a, i in qdata[:25]]),
        ])

        del mdata, qdata

        mul = operator.mul

        gdata = defaultdict(lambda: defaultdict(dict))
        for vcode, vdocs in vend_agrup.iteritems():
            vkey = vend[vcode]['nombre'] if vcode in vend else vcode
            for gname, gitems in vdocs.iteritems():
                _items = []
                for dtype, ditems in itertools.groupby(sorted(gitems, key=_ig(2)), _ig(2)):
                    ii = list(ditems)
                    _items.append((dtype, sum(map(_ig(0), ii)), sum(map(mul, *zip(*map(_ig(0, 1), ii))))))
                vdocs[gname] = _items
                gdata[vkey][gname].update(dict([
                    (kk, (gdata[vkey][gname].get(kk, (_zero,))[0]+qq,
                          gdata[vkey][gname].get(kk, (None, _zero))[1]+mm)) for kk, qq, mm in _items
                ]))

        for vendedor, grupos in gdata.iteritems():
            for gname, items in grupos.iteritems():
                grupos[gname][u'FAC+FAA'] = tuple(map(sum, zip(items.get(u'FAC', (0, _zero)), items.get(u'FAA', (0, _zero)))))

        cols = [u'FAC+FAA', u'REM']

        # Page 3
        out_data = list([("%s" % name, # Titulo Grupo
             " ".ljust(12) + " ".join([s.rjust(11) for s in cols]), # Encabezado Grupo
             ["%-12s %s" % (agrup,
                 " ".join([
                     ("%10s%s" % ((m(vals[key][1]) if vals[key][1] else  " "), ("*" if key in aprox else " "))) if key in vals else ("%11s" % "")
                 for key in cols])
             ) for agrup, vals in sorted(gdata[name].iteritems(), key=_ig(0))])
            for name in map(_ig(0), vdata) if name])

        pre_out_data = [(n, h, i[:sum(divmod(len(i), 2))]) for n, h, i in out_data]
        od = dict([(n, i) for n, h, i in out_data])

        new_pages = self._pageize(pre_out_data, data['max_rows'])
        post_new_pages = []
        for page in new_pages:
            grps = []
            for n, h, i in page:
                rows = len(i)
                a, b, od[n] = od[n][:rows], od[n][rows:rows*2], od[n][rows*2:]
                grps.append((n, h+(" "*16)+h,
                    ["%s %13s %s" % (ia, "", ib) for ia, ib in itertools.izip_longest(a, b, fillvalue=" ")]))
            post_new_pages.append(grps)
        pages.extend(post_new_pages)

        return pages
#}}}
#}}}

def maestro_stock():#{{{
    permiso = check_password("Maestro de Stock")
    if permiso is True:
        ms = MaestroStock()
        ms.run()
#}}}
def search_stock(first_key=None, multiple=False):#{{{
    if first_key is None or first_key in string.letters: # exact description
        search_dialog = ArticleSearchDialogExact()
        if first_key: # esto solo tiene sentido aquí
            search_dialog.search_box.insert_text(first_key)
    elif first_key == ".":
        search_dialog = ArticleSearchDialogByWord()
    elif first_key == "*":
        search_dialog = ArticleSearchDialogByCode()
    elif first_key == "@":
        search_dialog = ArticleSearchDialogByGroup()
    elif first_key == "#":
        search_dialog = ArticleSearchDialogBySupplier()
    else:
        return None
    search_dialog.multiple_selection = multiple
    return search_dialog.run()
#}}}
def maestro_terceros(filled_with=None, once=False, rel=u'C'):#{{{
    title = 'CLIENTES' if rel == u'C' else 'PROVEEDORES'
    mt = MaestroTerceros(title, rel, filled_with=filled_with, once=once)
    return mt.run()
#}}}
def sec_maestro_terceros(filled_with=None, once=False, rel=u'C'):#{{{
    permiso = check_password("Maestro de %s" % ('Clientes' if rel==u'C' else 'Proveedores'))
    if permiso is True:
        return maestro_terceros(filled_with, once, rel)
#}}}
def search_terceros(search_by=None, rel=None, first_key=None):#{{{
    if search_by is None or search_by == "exact description":
        search_dialog = TerceroSearchDialogExact(rel=rel)
    elif search_by == "word description":
        search_dialog = TerceroSearchDialogByWord(rel=rel)
    elif search_by == "cuit":
        search_dialog = TerceroSearchDialogByCuit(rel=rel)
    else:
        return None

    if first_key is not None:
        search_dialog.search_box.insert_text(first_key)
    return search_dialog.run()
#}}}
def editor_documentos_especiales():#{{{
    ede = EditorDocumentosEspeciales()
    return ede.run()
#}}}
def sec_editor_documentos_especiales():#{{{
    permiso = check_password("Maestro de Documentos")
    if permiso is True:
        return editor_documentos_especiales()
#}}}
def price_batch_modifier():#{{{
    pbm = PriceBatchModifier()
    return pbm.run()
#}}}
def _list_printer(cls, *args, **kwargs):#{{{
    lp = cls(*args, **kwargs)
    return lp.run()
#}}}
def group_list_printer():#{{{
    return _list_printer(GroupListPrinter)
#}}}
def temporary_list_printer(vendedor, items):#{{{
    return _list_printer(TemporaryListPrinter, vendedor, items)
#}}}
def sec_price_batch_modifier():#{{{
    permiso = check_password("Modificar Precio")
    if permiso is True:
        return price_batch_modifier()
#}}}
def listados():#{{{
    from nobix.viewer import views_map

    available_lists = get_current_config().listados

    _lists = [l[1] for l in views_map if l[0] in available_lists]

    def _press(btn, user_data=None):
        if callable(user_data):
            d.dialog_result = user_data()
        else:
            d.dialog_result = user_data
        d.quit()

    buttons = [AttrMap(Button(p[0], on_press=_press, user_data=p[1]),
                       'dialog.chooselist.button', 'dialog.chooselist.button.focus')
               for p in list(_lists + [("Cancelar", None)])]

    pile = Padding(Pile(buttons), width=45, left=1, right=1)

    d = Dialog(pile, title="LISTADOS DISPONIBLES", height=None, width=49,
               attr_style="dialog.chooselist",
               title_attr_style="dialog.chooselist.title",
        )
    return d.run()
#}}}
def sec_listados():#{{{
    permiso = check_password("Ver Listados")
    if permiso is True:
        return listados()
#}}}
def imprimir_cierre_fiscal():#{{{
    impr = []
    for k, v in get_current_config().impresoras.iteritems():
        if v['type'] == u"fiscal":
            impr.append(k)

    impresoras = printers.get_printers(impr)

    impr = []
    for ip in list(impresoras):
        #impr.append(("Cierre X %s" % ip.name, lambda: ip.fiscal_close("X")))
        impr.append(("Cierre X %s (%x)" % (ip.name, id(ip)), (ip, "X")))
        impr.append(("Cierre Z %s (%x)" % (ip.name, id(ip)), (ip, "Z")))

    def _press(btn, user_data=None):
        d.dialog_result = user_data
        d.quit()

    buttons = [AttrMap(Button(p[0], on_press=_press, user_data=p[1]),
                       'dialog.chooselist.button', 'dialog.chooselist.button.focus')
               for p in list(impr + [("Cancelar", (None, None))])]# lambda: (None, None))])]

    pile = Padding(Pile(buttons), width=45, left=1, right=1)

    d = Dialog(pile, title="CIERRE IMPRESORA FISCAL", height=None, width=49,
               attr_style="dialog.chooselist",
               title_attr_style="dialog.chooselist.title",
        )

    printer, args = d.run()
    success, data = None, None

    if printer and args:
        success, data = printer.fiscal_close(args)

    if success:
        if 'warnings' in data and data['warnings']:
            show_warning([u"La impresión fue exitosa pero el controlador envió el siguiente mensaje:\n\n",
                ('dialog.warning.important', u"\n".join(data['warnings'])), u'\n'])
    elif data is not None:
        if not 'errors' in data or not data['errors']:
            data['errors'] = [u"Error desconocido"]
        show_error([u'Se produjo un error al imprimir:\n\n',
                    ('dialog.error.important', u"\n".join(data['errors'])),
                    u'\n\n'])
#}}}
def show_about():#{{{
    content = Pile([
        Padding(Text(u"Copyright (C) 2010  Augusto Roccasalva"), left=2, right=2),
        Divider(),
        Padding(Text(u"Este programa es software libre: usted puede redistribuirlo y/o"
            u" modificarlo bajo los términos de la Licencia Pública General GNU."), left=2, right=2),
        Divider(),
        Padding(Text(('dialog.about.key', u"http://www.rocctech.com.ar/nobix")), align='center'),
        Divider(),
    ])
    d = Dialog(content, title="Nobix %s" % VERSION,
               subtitle=[('dialog.about.lema', u"'Non nobis solum'")],
               height=None,
               width=48,
               attr_style='dialog.about',
               title_attr_style='dialog.about.title',
               with_border=False,
    )
    d._keypress = lambda k: d.quit()
    d.run()
#}}}

class PrintWizard(Dialog):#{{{

    def __init__(self, doc_data, doc_header):#{{{

        def _cliente_columns(label, input, input_len):#{{{
            label.set_align_mode('right')
            return Columns([
                ('fixed', 16, AttrMap(label, 'dialog.printwizard.cliente.label')),
                ('fixed', input_len, AttrMap(input, 'dialog.printwizard.cliente.input',
                                             'dialog.printwizard.cliente.input.focus')),
            ], dividechars=1)#}}}
        def _edit_cancel(widget):#{{{
            self.focus_button(1)#}}}

        self.doc_data = doc_data
        self.doc_header = doc_header
        self.doctype = get_current_config().documentos[doc_data.doctype]
        self.customer_doctype = u'C'

        self.cliente_nombre = InputBox(edit_text=doc_data.cliente.nombre, max_length=35)
        connect_signal(self.cliente_nombre, 'edit-done', self.on_next_focus)
        connect_signal(self.cliente_nombre, 'edit-cancel', _edit_cancel)

        self.cliente_domicilio = InputBox(edit_text=doc_data.cliente.domicilio, max_length=35)
        connect_signal(self.cliente_domicilio, 'edit-done', self.on_next_focus)
        connect_signal(self.cliente_domicilio, 'edit-cancel', _edit_cancel)

        self.cliente_localidad = InputBox(edit_text=doc_data.cliente.localidad, max_length=20)
        connect_signal(self.cliente_localidad, 'edit-done', self.on_next_focus)
        connect_signal(self.cliente_localidad, 'edit-cancel', _edit_cancel)

        self.cliente_cp = InputBox(edit_text=doc_data.cliente.codigo_postal, max_length=8)
        connect_signal(self.cliente_cp, 'edit-done', self.on_next_focus)
        connect_signal(self.cliente_cp, 'edit-cancel', _edit_cancel)

        self.cliente_cuit = InputBox(edit_text=(doc_data.cliente.cuit or u""), max_length=13)
        connect_signal(self.cliente_cuit, 'edit-done', self.on_cuit_edit_done)
        connect_signal(self.cliente_cuit, 'edit-cancel', _edit_cancel)
        connect_signal(self.cliente_cuit, 'focus-out', self.on_cuit_focus_out)
        self.cuit_error = Text(u"")

        resp_text = get_current_config().iva_resp_map[doc_data.cliente.responsabilidad_iva]['nombre']
        self.cliente_resp = Text(resp_text.upper())

        vendedor_row = _cliente_columns(Text("Vendedor:"),
                Text("%s - %s" % (doc_data.vendedor['codigo'], doc_data.vendedor['nombre'])), 36)

        cliente_nombre_row = _cliente_columns(Text("Nombre:"), self.cliente_nombre, 36)
        cliente_domicilio_row = _cliente_columns(Text("Domicilio:"), self.cliente_domicilio, 36)
        cliente_localidad_row = _cliente_columns(Text("Localidad:"), self.cliente_localidad, 21)
        cliente_cp_row = _cliente_columns(Text("Código Postal:"), self.cliente_cp, 9)
        cliente_resp_row = _cliente_columns(Text("Resp:"), self.cliente_resp, 36)

        cliente_cuit_row = Columns([
            ('fixed', 16, AttrMap(Text("CUIT:", align="right"), 'dialog.printwizard.cliente.label')),
            ('fixed', 14, AttrMap(self.cliente_cuit, 'dialog.printwizard.cliente.input',
                                  'dialog.printwizard.cliente.input.focus')),
            AttrMap(self.cuit_error, 'dialog.printwizard.error'),
        ], dividechars=1)

        self.count_articulos = Text(unicode(len(doc_data.items)), align='right')
        self.count_unidades = NumericText(value=sum([i.cantidad for i in doc_data.items]))
        self.total = NumericText(value=doc_data.total)

        total_row = Columns([
            AttrMap(Text("TOTAL:", align='right'), 'dialog.printwizard.total.label'),
            AttrMap(self.total, 'dialog.printwizard.total.input'),
        ], dividechars=1)

        articulos_row = Columns([
            Divider(),
            ('fixed', 10, AttrMap(Text(u"Artículos:", align='right'), 'dialog.printwizard.articulos.label')),
            ('fixed', 9, AttrMap(self.count_articulos, 'dialog.printwizard.articulos.input')),
        ], dividechars=1)

        total_row = Columns([
            ('fixed', 16, AttrMap(Text("TOTAL:", align='right'), 'dialog.printwizard.total.label')),
            ('fixed', 10, AttrMap(self.total, 'dialog.printwizard.total.input')),
            Divider(),
            ('fixed', 10, AttrMap(Text("Unidades:", align='right'), 'dialog.printwizard.articulos.label')),
            ('fixed', 9, AttrMap(self.count_unidades, 'dialog.printwizard.articulos.input')),
        ], dividechars=1)

        self.content = Pile([
            vendedor_row,
            Divider(),
            cliente_nombre_row,
            cliente_domicilio_row,
            cliente_localidad_row,
            cliente_cp_row,
            cliente_cuit_row,
            cliente_resp_row,
            Divider(),
            articulos_row,
            total_row,
            Divider(),
        ])

        # Monkey patch
        self.content.keypress = self._trap_keypress(self.content.keypress)

        buttons = [("IMPRIMIR", self.imprimir), ("Cancelar", self.cancelar)]
        self.__super.__init__(self.content, buttons,
                title=self.doctype['nombre'].upper(),
                height = None,
                width = 68,
            )

        self.attr_style = "dialog.printwizard"
        self.title_attr_style = "dialog.printwizard.title"
        self.subtitle_attr_style = "dialog.printwizard.subtitle"
#}}}
    def imprimir(self, btn):#{{{

        def _simple_calc_total(items):
            return sum(item.cantidad*(item.precio if item.precio is not None else item.articulo.precio)
                       for item in items)

        if self._validar_cuit(self.cliente_cuit.get_edit_text()) is False:
            self._pile.set_focus(0)
            self._pile.widget_list[0].set_focus(6)
            self.content.widget_list[6].set_focus(1)
            return

        impresoras = printers.get_printers(self.doctype['printer'])

        if len(impresoras) > 1:
            idx = choose_printer(impresoras)
            if idx is None:
                return
        else:
            idx = 0

        impresora = impresoras[idx]

        extra_opts = dict((opt[6:], val) for opt, val in self.doctype.iteritems() if opt.startswith('print_'))
        extra_opts.setdefault('docname', self.doctype.get('nombre'))
        extra_opts.setdefault('discrimina_iva', self.doctype.get('discrimina_iva'))
        customer = {
            'customer_name': self.cliente_nombre.get_edit_text(),
            'customer_domicilio': self.cliente_domicilio.get_edit_text(),
            'customer_localidad': self.cliente_localidad.get_edit_text(),
            'customer_cp': self.cliente_cp.get_edit_text(),
            'customer_cuit': self.cliente_cuit.get_edit_text(),
            'customer_resp': self.doc_data.cliente.responsabilidad_iva,
            'customer_doctype': self.customer_doctype,
        }

        extra_opts.update(customer)

        items = self.doc_data.items

        total_rows = len(items)
        doc_count = 0

        if extra_opts['max_rows'] is not None:
            max_rows = int(extra_opts['max_rows'])
            doc_total_count = int(total_rows / max_rows) + int(bool(total_rows % max_rows))
        else:
            max_rows = None
            doc_total_count = 1

        while len(items):
            doc_count += 1
            extra_opts['doc_count'] = doc_count
            extra_opts['doc_total_count'] = doc_total_count
            if max_rows is not None:
                citems, items = items[:max_rows], items[max_rows:]
            else:
                citems, items = items, []
            ctotal = _simple_calc_total(citems)
            if ctotal != Decimal(0):
                cdesc = (ctotal/(self.doc_data.total+self.doc_data.descuento)) * self.doc_data.descuento
            else:
                cdesc = Decimal(0)
            doc_data = self.doc_data._replace(items=citems, total=(ctotal-cdesc), descuento=cdesc)
            success, printed_data = impresora.print_doc(doc_data, extra_opts)
            if success:
                self.doc_header.store_printed_document(printed_data, doc_data)
                if 'warnings' in printed_data and printed_data['warnings']:
                    show_warning(
                        [u"La impresión fue exitosa pero el controlador envió el siguiente mensaje:\n\n",
                         ('dialog.warning.important', u"\n".join(printed_data['warnings'])), u'\n'])
            elif printed_data is not None:
                if not 'errors' in printed_data or not printed_data['errors']:
                    printed_data['errors'] = [u"Error desconocido"]
                show_error([u"Se produjo un error al imprimir:\n\n",
                            ('dialog.error.important', u"\n".join(printed_data['errors'])),
                            u"\n\nEl documento será conservado hasta que se solucione el error."])
                break

        #self.must_quit = True
        self.quit()
#}}}
    def cancelar(self, btn):#{{{
        #self.must_quit = True
        self.quit()
#}}}

    def _trap_keypress(self, original_keypress):#{{{
        def keypress(size, key):
            if key == _finish_key:
                self.focus_button(0)
                return None
            else:
                return original_keypress(size, key)
        return keypress
#}}}

    ### Signal Hanlders ###

    def on_next_focus(self, *args):#{{{
        c = self.content
        focus_index = c.widget_list.index(c.focus_item)
        c.set_focus(focus_index+1)
#}}}
    def on_cuit_edit_done(self, widget, cuit):#{{{
        if self._validar_cuit(cuit):
            self.focus_button(0)
#}}}
    def on_cuit_focus_out(self, widget):#{{{
        self._validar_cuit(widget.edit_text)
#}}}
    def _validar_cuit(self, cuit):#{{{
        needs_cuit = self.doctype['needs_cuit']
        if needs_cuit is True:
            if cuit.strip() == u"":
                self.cuit_error.set_text("No puede estar vacío")
                return False
            elif validar_cuit(cuit) is False:
                self.cuit_error.set_text("Inválido")
                return False
        self.cuit_error.set_text(u"")
        return True
#}}}
#}}}

class SpecialPrintWizard(PrintWizard):#{{{

    def __init__(self, doc_data, doc_header):#{{{

        def _cliente_columns(label, input, input_len):#{{{
            label.set_align_mode('right')
            return Columns([
                ('fixed', 16, AttrMap(label, 'dialog.printwizard.cliente.label')),
                ('fixed', input_len, AttrMap(input, 'dialog.printwizard.cliente.input',
                                             'dialog.printwizard.cliente.input.focus')),
            ], dividechars=1)#}}}
        def _edit_cancel(widget):#{{{
            self.focus_button(1)#}}}

        self.doc_data = doc_data
        self.doc_header = doc_header
        self.doctype = get_current_config().documentos[doc_data.doctype]

        if doc_data.cliente.nombre == get_current_config().clientes_especiales[u'1']['nombre']:
            cliente_nombre_txt = ""
        else:
            cliente_nombre_txt = doc_data.cliente.nombre
        self.cliente_nombre = InputBox(edit_text=cliente_nombre_txt, max_length=35)
        connect_signal(self.cliente_nombre, 'edit-done', self.on_nombre_edit_done)
        connect_signal(self.cliente_nombre, 'edit-cancel', _edit_cancel)
        connect_signal(self.cliente_nombre, 'focus-out', self.on_nombre_focus_out)
        self.nombre_error = Text(u"")

        self.cliente_domicilio = InputBox(edit_text=doc_data.cliente.domicilio, max_length=35)
        connect_signal(self.cliente_domicilio, 'edit-done', self.on_next_focus)
        connect_signal(self.cliente_domicilio, 'edit-cancel', _edit_cancel)

        self.cliente_localidad = InputBox(edit_text=doc_data.cliente.localidad, max_length=20)
        connect_signal(self.cliente_localidad, 'edit-done', self.on_next_focus)
        connect_signal(self.cliente_localidad, 'edit-cancel', _edit_cancel)

        self.cliente_cp = InputBox(edit_text=doc_data.cliente.codigo_postal, max_length=8)
        #connect_signal(self.cliente_cp, 'edit-done', self.on_next_focus)
        connect_signal(self.cliente_cp, 'edit-done', lambda *x: self.focus_button(0))
        connect_signal(self.cliente_cp, 'edit-cancel', _edit_cancel)

        self.cliente_cuit = InputBox(edit_text=(doc_data.cliente.cuit or u""), max_length=13)
        connect_signal(self.cliente_cuit, 'edit-done', self.on_cuit_edit_done)
        connect_signal(self.cliente_cuit, 'edit-cancel', _edit_cancel)
        connect_signal(self.cliente_cuit, 'focus-out', self.on_cuit_focus_out)
        self.cuit_error = Text(u"")

        resp_text = get_current_config().iva_resp_map[doc_data.cliente.responsabilidad_iva]['nombre']
        self.cliente_resp = Text(resp_text.upper())

        #cliente_nombre_row = _cliente_columns(Text("Nombre:"), self.cliente_nombre, 36)
        cliente_nombre_row = Columns([
            ('fixed', 16, AttrMap(Text(u"Nombre:", align='right'), 'dialog.printwizard.cliente.label')),
            ('fixed', 36, AttrMap(self.cliente_nombre, 'dialog.printwizard.cliente.input',
                                  'dialog.printwizard.cliente.input.focus')),
            #AttrMap(self.nombre_error, 'dialog.printwizard.error'),
        ], dividechars=1)
        cliente_nombre_error_row = Columns([
            ('fixed', 16, AttrMap(Text(u""), 'dialog.printwizard.cliente.label')),
            AttrMap(self.nombre_error, 'dialog.printwizard.error'),
        ])
        cliente_domicilio_row = _cliente_columns(Text("Domicilio:"), self.cliente_domicilio, 36)
        cliente_localidad_row = _cliente_columns(Text("Localidad:"), self.cliente_localidad, 21)
        cliente_cp_row = _cliente_columns(Text("Código Postal:"), self.cliente_cp, 9)
        cliente_resp_row = _cliente_columns(Text("Resp:"), self.cliente_resp, 36)

        bgroup = []
        self.cliente_doctype_buttons = dict([(k, RadioButton(bgroup, v['nombre_corto'], False, self.on_radio_change, k)) for k, v in get_current_config().customer_doctype_map.iteritems()])
        cliente_doctype =  GridFlow([AttrMap(i, 'dialog.radio', 'dialog.radio.focus')\
                                     for i in self.cliente_doctype_buttons.values() if len(i.label) <= 21],
                                     18, 1, 0, 'left')
        cliente_doctype_row = Columns([
            ('fixed', 16, AttrMap(Text(u"Tipo Documento:", align="right"), 'dialog.printwizard.cliente.label')),
            ('fixed', 46, AttrMap(cliente_doctype, 'dialog.maeter.group')),
        ], dividechars=1)
        self.cliente_doctype_buttons[2].state = True

        cliente_cuit_row = Columns([
            ('fixed', 16, AttrMap(Text(u"Número Doc.:", align="right"), 'dialog.printwizard.cliente.label')),
            ('fixed', 14, AttrMap(self.cliente_cuit, 'dialog.printwizard.cliente.input',
                                  'dialog.printwizard.cliente.input.focus')),
            AttrMap(self.cuit_error, 'dialog.printwizard.error'),
        ], dividechars=1)

        self.count_articulos = Text(unicode(len(doc_data.items)), align='right')
        self.count_unidades = NumericText(value=sum([i.cantidad for i in doc_data.items]))
        self.total = NumericText(value=doc_data.total)

#        total_row = Columns([
#            AttrMap(Text("TOTAL:", align='right'), 'dialog.printwizard.total.label'),
#            AttrMap(self.total, 'dialog.printwizard.total.input'),
#        ], dividechars=1)

#        vendedor_row = _cliente_columns(Text("Vendedor:"),
#                Text("%s - %s" % (doc_data.vendedor['codigo'], doc_data.vendedor['nombre'])), 36)

        articulos_row = Columns([
            ('fixed', 16, AttrMap(Text("Vendedor:", align='right'), 'dialog.printwizard.cliente.label')),
            ('fixed', 26, AttrMap(Text(("%s - %s" % (doc_data.vendedor['codigo'], doc_data.vendedor['nombre']))[:26]), 'dialog.printwizard.cliente.input')),
            Divider(),
            ('fixed', 10, AttrMap(Text(u"Artículos:", align='right'), 'dialog.printwizard.articulos.label')),
            ('fixed', 9, AttrMap(self.count_articulos, 'dialog.printwizard.articulos.input')),
        ], dividechars=1)

        total_row = Columns([
            ('fixed', 16, AttrMap(Text("TOTAL:", align='right'), 'dialog.printwizard.total.label')),
            ('fixed', 10, AttrMap(self.total, 'dialog.printwizard.total.input')),
            Divider(),
            ('fixed', 10, AttrMap(Text("Unidades:", align='right'), 'dialog.printwizard.articulos.label')),
            ('fixed', 9, AttrMap(self.count_unidades, 'dialog.printwizard.articulos.input')),
        ], dividechars=1)

        info_row = Text(('dialog.error.important', u"Esta factura debe consignar Nombre y Documento del cliente"), align='center')

        self.content = Pile([
            info_row,
            #Divider(),
            cliente_nombre_error_row,
            cliente_nombre_row,
            cliente_doctype_row,
            cliente_cuit_row,
            Divider(),
            cliente_domicilio_row,
            cliente_localidad_row,
            cliente_cp_row,
            cliente_resp_row,
            Divider(),
#            vendedor_row,
            articulos_row,
            total_row,
            Divider(),
        ])

        # Monkey patch
        self.content.keypress = self._trap_keypress(self.content.keypress)

        buttons = [("IMPRIMIR", self.imprimir), ("Cancelar", self.cancelar)]
        super(PrintWizard, self).__init__(self.content, buttons,
                title=self.doctype['nombre'].upper(),
                height = None,
                width = 68,
            )

        self.attr_style = "dialog.printwizard"
        self.title_attr_style = "dialog.printwizard.title"
        self.subtitle_attr_style = "dialog.printwizard.subtitle"
#}}}
    def on_radio_change(self, radio, state, doctype):#{{{
        if state is True:
            for r in self.cliente_doctype_buttons.itervalues():
                if r is not radio:
                    r.state = False
#}}}
    def imprimir(self, btn):#{{{
        for k, v in self.cliente_doctype_buttons.iteritems():
            if v.state is True:
                self.customer_doctype = k
                break

        if self._validar_nombre(self.cliente_nombre.get_edit_text()) is False:
            self._pile.set_focus(0)
            self._pile.widget_list[0].set_focus(2)
            self.content.widget_list[2].set_focus(1)
            return

        if self._validar_cuit(self.cliente_cuit.get_edit_text()) is False:
            self._pile.set_focus(0)
            self._pile.widget_list[0].set_focus(4)
            self.content.widget_list[4].set_focus(1)
            return

        return super(SpecialPrintWizard, self).imprimir(btn)
#}}}
    def on_nombre_edit_done(self, widget, nombre):#{{{
        if self._validar_nombre(nombre):
            self.on_next_focus()
            #self.focus_button(0)
#}}}
    def on_nombre_focus_out(self, widget):#{{{
        self._validar_nombre(widget.edit_text)
#}}}
    def on_cuit_edit_done(self, widget, cuit):#{{{
        if self._validar_cuit(cuit):
            self.on_next_focus()
            self.on_next_focus()
#}}}

    def _validar_cuit(self, cuit):#{{{
        if cuit.strip() == u'':
            self.cuit_error.set_text(u"No puede estar vacío")
            return False

        try:
            cuit = int(cuit)
        except ValueError:
            self.cuit_error.set_text(u"Inválido")
            return False

        if int(cuit) <= 100000:
            self.cuit_error.set_text(u"Inválido")
            return False

        self.cuit_error.set_text(u"")
        return True
#}}}
    def _validar_nombre(self, nombre):#{{{
        if nombre.strip() == u'':
            self.nombre_error.set_text(u" ↓ No puede estar vacío")
            return False
        elif len(nombre.split()) < 2:
            self.nombre_error.set_text(u" ↓ Ingrese Nombre y Apellido")
            return False
        self.nombre_error.set_text(u"")
        return True
#}}}
#}}}

class MainFrame(Frame):#{{{

    def __init__(self):#{{{
        global _finish_key
        _finish_key = get_current_config().finish_key

        def _focus_body(w): self.set_focus('body')

        self.doc_footer = DocumentFooter()
        self.doc_body = DocumentBody()
        connect_signal(self.doc_body, 'focus-cliente-box', self._focus_cliente_box)
        connect_signal(self.doc_body, 'focus-vendedor-box', self._focus_vendedor_box)
        connect_signal(self.doc_body, 'focus-tipo-documento-box', self._focus_tipo_documento_box)
        connect_signal(self.doc_body, 'focus-descuento-box', self._focus_descuento_box)
        connect_signal(self.doc_body, 'focus-recargo-box', self._focus_recargo_box)
        connect_signal(self.doc_body, 'show-iva-info', self._show_iva_info)
        connect_signal(self.doc_body, 'clear-iva-info', self._clear_iva_info)

        self.doc_header = DocumentHeader(self.doc_body)
        connect_signal(self.doc_header, 'tipo-documento-set', _focus_body)
        connect_signal(self.doc_header, 'cliente-set', _focus_body)

        super(MainFrame, self).__init__(
                AttrMap(self.doc_body, 'document'),
                AttrMap(self.doc_header, 'header'),
                AttrMap(self.doc_footer, 'footer')
            )

        self.doc_header.renew_document()
#}}}
    def keypress(self, size, key):#{{{
        #self.doc_footer.status.set_text(["Pressed: ", ('footer.key', '%s' % key)])
        if key == 'ctrl n':
            self.doc_header.renew_document()
        elif key == 'f10':
            self.doc_header.save_current_document()

            menu_items = self._build_menu_items()
            _width = max(len(i[0]) for i in menu_items)
            _height = len(menu_items)
            menu = Menu(menu_items, width=_width+2, height=_height+2,
                        align='right', valign='top', with_border=True)
            menu.run()

        # Only for test
#        elif key == 'f9':
#            return listados()
#            from nobix.viewer import views_map
#            return views_map[5][1][1]()
        else:
            return self.__super.keypress(size, key)
#}}}
    def _build_menu_items(self):#{{{
        from nobix.main import quit

        enabled_items = get_current_config().menu_items
        menu_items = []

        _menu_config_map = [
            ('maestro_clientes', ('Maestro de Clientes', maestro_terceros)),
            ('maestro_proveedores', ('Maestro de Proveedores', lambda: sec_maestro_terceros(rel=u'P'))),
            ('maestro_stock', ('Maestro de Stock', maestro_stock)),
            ('modificar_precios', ('Modificador de Precios', sec_price_batch_modifier)),
            ('documentos_especiales', ('Documentos Especiales', sec_editor_documentos_especiales)),
            ('ver_listados', ('Listados', listados)),
            ('cierre_fiscal', ('Cierre Fiscal', imprimir_cierre_fiscal)),
        ]

        for key, item in _menu_config_map:
            if key in enabled_items:
                menu_items.append(item)

        menu_items.append(('Salir (F10)', quit, 'f10'))
        menu_items.append(('Acerca de ...', show_about))
        return menu_items
#}}}
    def _focus_cliente_box(self, widget):#{{{
        # Focus a cliente_box
        self.set_focus('header')
        self.doc_header._w.set_focus_column(0)
#}}}
    def _focus_vendedor_box(self, widget):#{{{
        # Focus a vendedor_box
        self.set_focus('header')
        self.doc_header._w.set_focus_column(1)
        self.doc_header._w.widget_list[1].set_focus(0)
#}}}
    def _focus_tipo_documento_box(self, widget):#{{{
        # Focus a tipo_documento_box
        self.set_focus('header')
        self.doc_header._w.set_focus_column(1)
        self.doc_header._w.widget_list[1].set_focus(1)
#}}}
    def _focus_descuento_box(self, widget):#{{{
        # Show discount dialog and set discount
        dialog = DiscountDialog()
        discount = dialog.run()
        self.doc_body.set_descuento(discount)
#}}}
    def _focus_recargo_box(self, widget):#{{{
        dialog = DiscountDialog(recargo=True)
        recargo = dialog.run()
        self.doc_body.set_descuento(-recargo if recargo is not None else None)
#}}}
    def _show_iva_info(self, widget, gravado, iva):#{{{
        self.doc_footer.extra_info.set_text([
            ('footer.key', "I.G."), " ", ("$ %.2f" % gravado).replace(".", ","), "  ",
            ('footer.key', "I.V.A."), " ", ("$ %.2f" % iva).replace(".", ","),
        ])
#}}}
    def _clear_iva_info(self, widget):#{{{
        self.doc_footer.extra_info.set_text(u"")
#}}}
#}}}

# vim:foldenable:foldmethod=marker
