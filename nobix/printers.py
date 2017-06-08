#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from decimal import Decimal
from collections import namedtuple
from functools import partial

import cairo
import rsvg
import cups

from mako.template import Template
from unidecode import unidecode

from nobix.config import get_current_config
from nobix.models import Articulo
from nobix.exc import NobixPrinterError, NobixBadCuitError
from nobix.utils import get_hostname, get_username, moneyfmt, validar_cuit
from nobix.utils import get_next_docnumber as u_get_next_docnumber
from nobix.utils import wait_fiscal_answer, message_waiter
from nobix.labeler import Labeler, Label1, LabelerError

PrinterItemData = namedtuple('PrinterItemData', 'codigo descripcion cantidad precio total')
FiscalItemData = namedtuple('FiscalItemData', 'descripcion cantidad precio iva signo impint base')
DescuentoData = namedtuple('DescuentoData', 'descripcion monto signo base')

__all__ = ('get_printers', 'Printer')

_created_printers = {}
_printers_by_type = {} # filled by PrinterMeta
_template_cache = {}

_commands_to_log = [
    "\x39", # DailyClose
    "\x43", # Subtotal
    "\x44", # TotalTender
    "\x45", # CloseFiscalReceipt
]

# Hasar Fiscal Status Error Map
_hasar_fs = [
    (1<<0, u"Error en chequeo de memoria fiscal", False),
    (1<<1, u"Error en chequo de la memoria de trabajo", False),
    (1<<2, u"Carga de batería baja", True),
    (1<<3, u"Comando desconocido", False),
    (1<<4, u"Datos no válidos en un campo", False),
    (1<<5, u"Comando no válido para el estado fiscal actual", False),
    (1<<6, u"Desborde del Total", False),
    (1<<7, u"Memoria fiscal llena, bloqueada o dada de baja", False),
    (1<<8, u"Memoria fiscal a punto de llenarse", True),
    (1<<9, u"Terminal fiscal certificada", '<required>'),
    (1<<10, u"Terminal fiscal fiscalizada", '<required>'),
    (1<<11, u"Error en ingreso de fecha", False),
    (1<<12, u"Documento fiscal abierto", '<optional>'),
    (1<<13, u"Documento abierto", '<optional>'),
    #(1<<14, u"Reserved", '<optional>'),
    #(1<<15, u"Reserved", '<optional>'),
]

# Hasar Printer Status Error Map
_hasar_ps = [
    #(1<<0, u"Reserved", '<optional>'),
    #(1<<1, u"Reserved", '<optional>'),
    (1<<2, u"Error de Impresora", False),
    (1<<3, u"Impresora offline", False),
    (1<<4, u"Falta papel del diario", False),
    (1<<5, u"Falta papel de tickets", False),
    (1<<6, u"Buffer de impresora lleno", False),
    (1<<7, u"Buffer de impresora vacio", '<optional>'),
    (1<<8, u"Tapa de impresora abierta", True),
    #(1<<9, u"Reserved", '<optional>'),
    #(1<<10, u"Reserved", '<optional>'),
    #(1<<11, u"Reserved", '<optional>'),
    #(1<<12, u"Reserved", '<optional>'),
    #(1<<13, u"Reserved", '<optional>'),
    (1<<14, u"Cajon de dinero cerrado o ausente", '<optional>'),
    #(1<<15, u"Reserved", '<optional>'),
]

# Hasar Printer Aux Status Map
_hasar_as = [
]

# Some twiks
rsvg.set_default_dpi(72.0)


def get_printers(printers):#{{{
    global _created_printers

    if _created_printers == {}:
        create_printers()

    if printers == '*':
        return tuple(_created_printers.itervalues())

    if isinstance(printers, basestring) or printers is None:
        printers = (printers,)

    try:
        return tuple(_created_printers[name] for name in printers)
    except KeyError as e:
        raise NobixPrinterError("La impresora '%s' no existe."\
                " Revise su archivo de configuración." % e.args[0])
#}}}
def create_printers():#{{{
    global _created_printers

    # Special printer
    _created_printers[None] = NullPrinter("No imprimir")

    for name, options in get_current_config().impresoras.iteritems():
        _type = options.get('type')
        cls = _printers_by_type[_type]
        options = dict((key.replace(_type+'_', ''), value) for key, value in options.iteritems()
                        if key.startswith(_type+'_'))
        _created_printers[name] = cls(name, options)
#}}}
def get_template(filename):#{{{
    global _template_cache
    if filename not in _template_cache:
        _template_cache[filename] = Template(filename=filename,# module_directory="/tmp/mako_modules",
                input_encoding="utf-8", output_encoding="utf-8")
    return _template_cache[filename]
#}}}

def get_next_docnumber(doctype):#{{{
    if get_current_config().documentos[doctype]['docnumber_generation'] == '<from_db>':
        return u_get_next_docnumber(doctype)
    return None
#}}}
def prepare_items(items):#{{{
    retval = []
    for item in items:
        if isinstance(item.articulo, Articulo):
            precio = item.precio if item.precio is not None else item.articulo.precio
            retval.append(PrinterItemData(item.articulo.codigo, item.articulo.descripcion, item.cantidad,
                          precio, item.cantidad * precio))
        elif isinstance(item.articulo, basestring):
            retval.append(PrinterItemData("", item.articulo, item.cantidad, item.precio,
                                          item.precio * item.cantidad))
        else:
            raise RuntimeError(u"Unknown item type '%s'" % type(item.articulo).__name)
    return retval
#}}}
def build_out_filename(doc_data, data, options):#{{{
    doc_conf = get_current_config().documentos[doc_data.doctype]
    docdate = data['docdate']
    filename_data = {
        'date': unicode(docdate.strftime('%Y-%m-%d')), 'time': unicode(docdate.strftime('%H%M%S')),
        'date_year': unicode(docdate.strftime('%Y')), 'date_month': unicode(docdate.strftime('%m')),
        'date_day': unicode(docdate.strftime('%d')), 'time_hour': unicode(docdate.strftime('%H')),
        'username': get_username(), 'hostname': get_hostname(), 'docname': options.docname,
        'docnumber': data.get('docnumber', u''), 'docpv': options.docpv, 'doc_count': options['doc_count'],
        'customer_name': options.customer_name, 'codigo': doc_data.vendedor['codigo'],
    }

    if options.printer_type in ('cups', 'file'):
        out_dir = options.store % filename_data
        base_filename = options.filename if options.filename is not None else u'%(date)s-%(time)s-%(username)s-%(codigo)s-%(docnumber)s'
        out_filename = base_filename % filename_data
    elif options.printer_type == 'fiscal':
        out_dir = options.input % filename_data
        base_filename = options.filename if options.filename is not None\
                else u'%(username)s_%(hostname)s_%(date)s_%(time)s_%(doc_count)s.dat'
        out_filename = base_filename % filename_data
    else:
        out_dir = "/tmp"
        out_filename = u'Nobix_%(username)s@%(hostname)s-%(docnumber)s-%(date)s%(time)s' % filename_data

    if not os.path.exists(out_dir):
        os.makedirs(out_dir, mode=0775)
    return os.path.join(out_dir, out_filename)
#}}}

def _parse_status(status, status_map):#{{{
    ret = []
    x = int(status, 2)
    for value, message, cont in status_map:
        if cont == '<required>':
            if (value & x) != value:
                ret.append(("[REQ] %s" % message, False))
        elif isinstance(cont, bool):
            if (value & x) == value:
                ret.append((message, cont))
    return ret
#}}}
def _parse_fiscal_status(fiscal_status, fiscal_status_map=_hasar_fs):#{{{
    return _parse_status(fiscal_status, fiscal_status_map)
#}}}
def _parse_printer_status(printer_status, printer_status_map=_hasar_ps):#{{{
    return _parse_status(printer_status, printer_status_map)
#}}}
def _parse_aux_status(aux_status, aux_status_map=_hasar_as):#{{{
    return _parse_status(aux_status, aux_status_map)
#}}}

class options_map(dict):#{{{

    def __getattr__(self, name):
        return self.get(name)
#}}}

class PrinterMeta(type):#{{{

    def __init__(cls, name, bases, ns):
        type.__init__(cls, name, bases, ns)
        if hasattr(cls, '_type'):
            t = getattr(cls, '_type')
            _printers_by_type[t] = cls
#}}}
class Printer(object):#{{{
    __metaclass__ = PrinterMeta
    # _type attribute required for subclasses to be registered
    _ext = "_nobix"

    def __init__(self, name, options={}):#{{{
        self.name = name
        self.opts = options
        self.opts['printer_type'] = self._type
#}}}
    def print_doc(self, doc_data, opts={}):#{{{
        options = options_map(self.opts)
        options.update(opts)
        resp_map = get_current_config().iva_resp_map

        # some defaults
        if options.vendedor_fmt is None:
            options['vendedor_fmt'] = '%(codigo)s'

        options['vendedor'] = options.vendedor_fmt % {'nombre': doc_data.vendedor['nombre'],
                                                      'codigo': doc_data.vendedor['codigo']}
        del options['vendedor_fmt']

        # build context data
        data = {
            'docnumber': get_next_docnumber(doc_data.doctype),
            'docdate': datetime.now(),
            'document_total': doc_data.total,
            'items': prepare_items(doc_data.items),
            'descuento': doc_data.descuento or None,
            'customer_resp_name': resp_map[doc_data.cliente.responsabilidad_iva]['nombre_corto']
        }

        options['out_filename'] = self._check_extension(build_out_filename(doc_data, data, options))
        data.update(options)

        return self.run_print(data)
#}}}
    def run_print(self, data):#{{{
        raise NotImplementedError("Este método debe ser implementado")
#}}}
    def _check_extension(self, filename):#{{{
        name, ext = os.path.splitext(filename)
        if ext[1:] != self._ext:
            ext = "." + self._ext
        return name + ext
#}}}
    def __repr__(self):#{{{
        return "<%s.%s('%s') options=%r>" % (type(self).__module__, type(self).__name__, self.name, self.opts)
#}}}
#}}}

class NullPrinter(Printer):#{{{
    _type = None

    def run_print(self, data):
        return True, data
#}}}

class FiscalPrinter(Printer):#{{{
    _type = "fiscal"
    _ext = "dat"

    def run_print(self, data):#{{{
        data = self._complete_data(data)

        tmpl = get_template(data['template'])
        result = tmpl.render_unicode(**data)
        result = unidecode(result)

        with open(data['out_filename'], "w") as out:
            result = result.replace("|", "\x1c")
            out.write(result)

        response_filename = os.path.splitext(data['out_filename'])[0]+'.ans'

        title = u"Imprimiendo en %s" % self.name
        if data['doc_total_count'] > 1:
            title += u"\n%d de %d documentos" % (data['doc_count'], data['doc_total_count'])

        if not wait_fiscal_answer(response_filename, title=title, timeout=data['timeout']):
            if os.path.exists(data['out_filename']):
                data['errors'] = [u"El programa encargado de imprimir puede estar apagado o muy sobrecargado"]
                os.unlink(data['out_filename'])
            else:
                data['errors'] = [u"No se encontró el archivo de respuesta"]
            return False, data

        return self._read_response(response_filename, data)
#}}}
    def fiscal_close(self, type_=u'X'):#{{{
        outfilename = os.path.join(self.opts['input'],
                'cierre%s_%s.dat' % (type_, datetime.now().strftime("%y%m%d-%H%M")))

        response_filename = os.path.splitext(outfilename)[0]+'.ans'
        title = u"Imprimiento Cierre %s en %s" % (type_, self.name)

        with open(outfilename, "w") as out:
            for lineno in ('08', '09', '10', '11', '12', '13', '14'):
                out.write("]\x1c%s\x1c\x7f\n" % lineno)
            out.write("\x39\x1c%s" % type_.upper())

        if not wait_fiscal_answer(response_filename, title=title, timeout=self.opts['timeout']):
            if os.path.exists(outfilename):
                errors = [u"El programa encargado de imprimir puede estar apagado o muy sobrecargado"]
                os.unlink(outfilename)
            else:
                errors = [u"No se encontró el archivo de respuesta"]
            return False, {'errors': errors}

        return self._read_response(response_filename, {})
#}}}

    def _read_response(self, filename, data):#{{{
        ferrors = []
        perrors = []
        data['errors'] = []
        data['warnings'] = []

        resp = open(filename, "r")
        if self.opts['logfile']:
            try:
                log = open(self.opts['logfile'], "a")
            except IOError:
                log = None
                data['warnings'] = [u"No se puede escribir log en '%s'" % self.opts['logfile']]

        for line in resp:
            elements = line.strip().split("|")
            cmd, ps, fs = elements[:3]

            perr = _parse_printer_status(ps)
            ferr = _parse_fiscal_status(fs)

            if all(c for m, c in perr+ferr):
                if cmd == u"\x45": # CloseFiscalReceipt
                    try:
                        data['docnumber'] = unicode(elements[3])
                    except IndexError:
                        data['errors'].append(u"Respuesta mal formada:\n(%r)" % line.strip())

            if log:
                d, l = datetime.now().strftime("%Y%m%d %H:%M:%S"), line.strip()
                if cmd in _commands_to_log and len(perr+ferr) < 1:
                    log.write("%s [I] %s\n" % (d, l))
                elif perr or ferr:
                    log.write("%s [E] %s err/warn:%r\n" % (d, l, (perr+ferr)))


            ferrors.extend(ferr)
            perrors.extend(perr)
        resp.close()
        if log: log.close()

        errors = list(set(ferrors)) + list(set(perrors))
        success = all(c for m, c in errors)
        data['errors'].extend([m for m, c in errors if c is False])
        data['warnings'].extend([m for m, c in errors if c is True])

        os.unlink(filename)

        data['last_fiscal_status'] = unicode(fs)
        data['last_printer_status'] = unicode(ps)
        return success, data
#}}}
    def _complete_data(self, data):#{{{
        resp_map = get_current_config().iva_resp_map
        data['moneyfmt'] = partial(moneyfmt, sep=u'')

        needs_cuit = resp_map[data['customer_resp']]['needs_cuit']

        if needs_cuit:
            if not validar_cuit(data['customer_cuit']):
                raise NobixBadCuitError(u"El CUIT no es válido, no se debería llegar a este "
                                        u"punto con un CUIT inválido")
            data['customer_cuit'] = data['customer_cuit'].replace("-", "")
        else:
            data['customer_cuit'] = data['customer_cuit'] or u"00000000000"

        data['fitems'] = self._format_items(data)
        l = [data['customer_domicilio'], data['customer_localidad']]

        if data['descuento']:
            if data['descuento'] > Decimal(0):
                label = u'Descuento'
                monto = data['descuento']
                signo = 'm'
            else:
                label = u'Recargo'
                monto = abs(data['descuento'])
                signo = 'M'
            data['desc'] = DescuentoData(label[:20], monto, signo, 'T')

        data['headers'] = []

        domicilio = (u'%s' % " - ".join(l) if all(l) else "".join(l))[:40]
        if domicilio and data['customer_cp']:
            domicilio += " (%s)" % (data['customer_cp'],)

        if domicilio:
            data['headers'].append(('09', domicilio))
        else:
            # Borramos el contenido anterior
            data['headers'].append(('09', '\x7f'))

        data['headers'].append(('10', (u'Vendedor: %s' % data['vendedor'])[:40]))

        data['footers'] = [
            ('13', u'Defensa al Consumidor Mza. 0800-222-6678'),
            ('14', u'Gracias por su preferencia'.center(40)),
        ]

        return data
#}}}
    def _format_items(self, data):#{{{
        fitems = []
        # 3x28 + 1x20
        for item in data['items']:
            code = item.codigo[:7].ljust(8)
            s = code + item.descripcion
            lines = []
            if len(s) <= 20:
                desc = s
            else:
                while len(s):
                    s, l = s[28:], s[:28]
                    lines.append(l)
                    if len(s) <= 20:
                        desc = s
                        break
                lines = lines[:3]
            # Necesita almenos un caracter de descripcion
            if not desc: desc = " "
            fitems.append((lines, FiscalItemData(desc, item.cantidad, item.precio, '21.00', 'M', '0.00', 'T')))

#        if data['descuento']:
#            if data['descuento'] > Decimal(0):
#                label = u'Descuento'
#                monto = data['descuento']
#                signo = 'm'
#            else:
#                label = u'Recargo'
#                monto = abs(data['descuento'])
#                signo = 'M'
#            fitems.append(([], FiscalItemData(label, Decimal(0), monto, '**.**', signo, '0.00', 'T')))

        return fitems
#}}}
#}}}
class FilePrinter(Printer):#{{{
    _type = "file"
    _ext = "pdf"
    surface_cls = cairo.PDFSurface

    def run_print(self, data):#{{{

        message_waiter(u" Procesando información ... ")
        data['moneyfmt'] = partial(moneyfmt, sep='.', dp=',')

        tmpl = get_template(data['template'])
        result = tmpl.render(**data)

        #fname = os.path.basename(data['template'].rpartition('.')[0])
        #with file("/home/augusto/"+fname, "w") as out:
        #    out.write(result)

        handler = rsvg.Handle(data=result)
        surface = self.surface_cls(data['out_filename'], handler.props.width, handler.props.height)
        ctx = cairo.Context(surface)
        ctx.scale(0.8, 0.8)

        handler.render_cairo(ctx)
        ctx.show_page()
        surface.finish()

        return True, data
#}}}
    def run_list_print(self, doc_data):
        data = options_map(self.opts)
        data.update(doc_data)

        docdate = datetime.now()
        data['docdate'] = docdate

        filename_data = {
            'username': get_username(), 'hostname': get_hostname(), 'docname': data.docname,
            'date': unicode(docdate.strftime('%Y-%m-%d')), 'time': unicode(docdate.strftime('%H%M%S')),
            'doc_count': data['doc_count'],
        }
        out_dir = data['store']
        out_filename = u'%(docname)s_%(date)s_%(time)s_%(username)s_%(doc_count)s' % (filename_data)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, mode=0775)
        data['out_filename'] = self._check_extension(os.path.join(out_dir, out_filename))

        return self.run_print(data)
#}}}
class CupsPrinter(FilePrinter):#{{{
    _type = "cups"
    _ext = "ps"
    surface_cls = cairo.PSSurface

    def run_print(self, data):#{{{
        success, data = super(CupsPrinter, self).run_print(data)

        def _set_cups_password(prompt):
            return data['password']

        if success is False:
            return success, data

        if data['server'] is not None:
            cups.setServer(data['server'])

        if data['port'] is not None:
            cups.setPort(data['port'])

        if data['user'] is not None:
            cups.setUser(data['user'])
            if data['password'] is not None:
                cups.setPasswordCB(_set_cups_password)

        try:
            c = cups.Connection()
        except RuntimeError as e:
            data['errors'] = e.args
            return False, data
        try:
            job_id = c.printFile(data['printer'], data['out_filename'], data['out_filename'],
                    {'copies': str(data['copies'])})
        except cups.IPPError as e:
            data['errors'] = e.args
            return False, data
        return True, data
#}}}
#}}}


class TagPrinter(Printer):
    _type = "tag"

    def run_print(self, data):
        message_waiter("Procesando información ... ")

        lsize = data['size']['paper']
        idVendor = data['idVendor']
        idProduct = data['idProduct']

        labeler = Labeler(label_size=lsize, idVendor=idVendor, idProduct=idProduct)

        for item in data['items']:
            labeler.add_label(Label1(code=item.codigo, desc=item.descripcion[:40], qty=item.cantidad))

#        import pprint
#        with open('/home/augusto/labels.log', "w") as out:
#            out.write(labeler.render().encode('utf-8', 'ignore'))
#            out.write('\n'*3)
#            out.write(pprint.pformat(data))

        try:
            labeler.printout()
            retval = True
        except LabelerError as error:
            data['errors'] = [error.args[0]]
            retval = False

        return retval, data




# vim:foldenable:foldmethod=marker
