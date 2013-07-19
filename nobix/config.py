#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os import path
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
import imp

_default_documentos = {
    'nombre': None,
    'has_body': True,
    'need_pass': False,
    'printer': None,
    'libro_iva': False,
    'default_tax': None,
    'allowed_taxes': (),
    'discrimina_iva': False,
    'needs_cuit': False,
    'stock': False,
    'max_amount': None,
    'min_amount': None,
    'allowed_custom_items': False,
    'docnumber_generation': u'<from_db>',
    'print_copies': 1,
    'print_show_logo': False,
    'print_show_footer_legend': False,
    'print_docletter': u'X',
    'print_max_rows': None,
    'tercero': u'C', # Cliente.relacion
}

def parse_documentos(raw_dict):
    doc = {}
    for k, v in raw_dict.iteritems():
        d = _default_documentos.copy()
        d['tipo'] = k
        d.update(v)
        doc[k] = d
    return doc

_default_vendedores = {
    'nombre': None,
    'pass': None,
}

class VendedoresConfig(dict):

    def __getitem__(self, attr):
        item = super(VendedoresConfig, self).get(attr)
        if isinstance(item, dict):
            return item
        elif isinstance(item, basestring):
            return self[item]
        else:
            raise KeyError(attr)

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default

def parse_vendedores(raw_dict):
    vend = VendedoresConfig()
    for k, v in raw_dict.iteritems():
        if isinstance(v, dict):
            d = _default_vendedores.copy()
            d.update(v)
            vend[k] = d
        else:
            vend[k] = v
    return vend

def parse_impuestos(raw_dict):
    "Check and parse impuestos in configuration file."
    i = {}
    for k, v in raw_dict.iteritems():
        try:
            i[k] = v.copy()
            i[k].update({
                'codigo': k,
                'alicuota': Decimal(v['alicuota'])
            })
        except (KeyError, InvalidOperation) as e:
            raise ValueError(u"Impuestos inválidos: revise el impuesto %s,"
                             u" el error original fue %r" % (k, e))
    return i

def parse_color_palette(cp):
    return dict((c[0], tuple(c[1:])) for c in cp) if cp else None

def parse_date(value):
    if isinstance(value, date):
        return value
    elif isinstance(value, basestring):
        try:
            return date.fromordinal(datetime.strptime(value, "%Y-%m-%d").toordinal())
        except ValueError as e:
            print e
    return None

class Configuration(object):

    def merge(self, other):
        if not isinstance(other, Configuration):
            return

        for attr in other.__dict__.keys():
            sattr = getattr(self, attr)
            oattr = getattr(other, attr)

            if oattr is not None:
                if isinstance(sattr, dict):
                    sattr.update(getattr(other, attr))
                else:
                    sattr = getattr(other, attr)
                setattr(self, attr, sattr)

        if getattr(self, 'min_date', None) is None:
            self.min_date = date(1901, 1, 1)
        if getattr(self, 'max_date', None) is None:
            self.max_date = date(2099, 12, 31)

def read_config(config_path):
    global _config
    config_path = path.expanduser(config_path)
    config_path = path.expandvars(config_path)
    config_path = path.abspath(config_path)

    if not path.isfile(config_path):
        raise ValueError(u"'%s' no es un archivo" % config_path)

    config_filename = path.basename(config_path)
    config_file = open(config_path, "r")

    config_mod = imp.load_source(config_filename.replace(".", "_"), config_path, config_file)

    config = Configuration()

    config.documentos = parse_documentos(getattr(config_mod, 'documentos', {}))
    config.vendedores = parse_vendedores(getattr(config_mod, 'vendedores', {}))
    config.impuestos = parse_impuestos(getattr(config_mod, 'impuestos', {}))
    config.iva_resp_map = getattr(config_mod, 'iva_resp_map', None)
    config.customer_doctype_map = getattr(config_mod, 'customer_doctype_map', None)
    config.impresoras = getattr(config_mod, 'impresoras', None)
    config.database_uri = getattr(config_mod, 'database_uri', None)
    config.color_palette = parse_color_palette(getattr(config_mod, 'color_palette', None))

    config.default_doctype = getattr(config_mod, 'default_doctype', u'FAC')
    config.default_vendedor = getattr(config_mod, 'default_vendedor', u'001')
    config.default_cliente = getattr(config_mod, 'default_cliente', u'1')
    config.finish_key = getattr(config_mod, 'finish_key', 'end')
    config.clientes_especiales = getattr(config_mod, 'clientes_especiales', {})
    config.clock_update_interval = getattr(config_mod, 'clock_update_interval', 60)
    config.clock_fmt = getattr(config_mod, 'clock_fmt', '%d/%m/%y %H:%M')
    _clock_width = len(datetime.now().strftime(config.clock_fmt))
    config.clock_width = getattr(config_mod, 'clock_width', _clock_width)
    config.menu_items = getattr(config_mod, 'menu_items', None)
    config.listados = getattr(config_mod, 'listados', None)
    config.min_date = parse_date(getattr(config_mod, 'min_date', None))
    config.max_date = parse_date(getattr(config_mod, 'max_date', None))
    config.punto_venta = getattr(config_mod, 'punto_venta', None)
    config.sucursal = getattr(config_mod, 'sucursales', {}).get(config.punto_venta, None)
    config.usar_nuevo_algoritmo = getattr(config_mod, 'usar_nuevo_algoritmo', False)
    config.case_sensitive_search = getattr(config_mod, 'case_sensitive_search', True)
    config.manager_hostname = getattr(config_mod, 'manager_hostname', None)
    config.manager_port = getattr(config_mod, 'manager_port', None)

    return config

def load_config():
    global _config
    default_config_path = path.join(sys.prefix, 'share/nobix/config.py')
    global_config_path = '/etc/nobix/config.py'
    user_config_path = path.expanduser('~/.nobix.config.py')

    if not path.isfile(default_config_path):
        print(u"ERROR: Falta archivo de configuración: %s" % default_config_path)
        raise SystemExit()
    default_config = read_config(default_config_path)

    if path.isfile(global_config_path):
        global_config = read_config(global_config_path)
    else:
        global_config = None

    if path.isfile(user_config_path):
        user_config = read_config(user_config_path)
    else:
        user_config = None

    default_config.merge(global_config)
    default_config.merge(user_config)
    _config = default_config
    if _config.manager_hostname is None:
        _config.manager_hostname = 'localhost'
    if _config.manager_port is None:
        _config.manager_port = 18280
    return _config

def get_current_config():
    global _config
    return _config

_config = Configuration()
