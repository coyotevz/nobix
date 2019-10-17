#!/usr/bin/env python
# -*- coding: utf-8 -*-

from socket import gethostname, getfqdn
from datetime import datetime
from decimal import Decimal

from urwid import Text, Filler

from nobix.mainloop import get_main_loop
from nobix.widget import Dialog, ErrorDialog, WarningDialog, SingleMessageDialog, PasswordDialog, \
                         WaitFiscalAnswer, SingleMessageWaiter

def get_username():
    import getpass
    return unicode(getpass.getuser())

def get_hostname():
    return unicode(getfqdn())

def get_elapsed_time(start, microseconds=False):
    """
    Format a time delta (datetime.timedelta) using the format DdHhMmS[.MS]s
    """
    delta = datetime.now() - start
    days = int(delta.days)
    hours, seconds = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if microseconds:
        seconds = seconds + float(delta.microseconds) / 1000 / 1000
    result = ''
    if days: result += '%dd' % days
    if days or hours: result += '%dh' % hours
    if days or hours or minutes: result += '%dm' % minutes
    if microseconds: result += '%.3fs' % seconds
    else: result += '%ds' % int(seconds)
    return result

def clear_screen():
    get_main_loop().screen.clear()

def show_error(message):
    e = ErrorDialog(message)
    return e.run()

def show_warning(message, buttons=[], **kwargs):
    w = WarningDialog(message, buttons, **kwargs)
    return w.run()

def show_message(message):
    pass

def message_waiter(message):
    dialog = SingleMessageWaiter(message, True)
    return dialog.run()

def check_password(for_action=None):
    p = PasswordDialog(for_action=for_action)
    return p.run()

def wait_fiscal_answer(filename, title=None, timeout=10, interval=0.1, data={}):
    wa = WaitFiscalAnswer(filename=filename, title=title, timeout=timeout, interval=interval, data=data)
    return wa.run()

def smart_unicode(s, encoding='utf-8', errors='strict'):
    """
    Adapted from django.utils.force_unicode utility.
    """
    if not isinstance(s, basestring):
        if hasattr(s, '__unicode__'):
            s = unicode(s)
        else:
            s = unicode(str(s), encoding, errors)
    elif not isinstance(s, unicode):
        s = s.decode(encoding, errors)
    return s

def validar_cuit(cuit):
    "from: http://python.org.ar/pyar/Recetario/ValidarCuit by Mariano Reingart"
    # validaciones minimas
    if len(cuit) != 13 or cuit[2] != "-" or cuit[11] != "-":
        return False

    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    cuit = cuit.replace("-", "") # remuevo barras

    # calculo el dígito verificador:
    aux = 0
    for i in xrange(10):
        aux += int(cuit[i])*base[i]

    aux = 11 - (aux - (int(aux/11) * 11))

    if aux == 11:
        aux = 0
    if aux == 10:
        aux = 9

    return aux == int(cuit[10])

def moneyfmt(value, places=2, curr='', sep=',', dp='.', pos='', neg='-', trailneg=''):
    # from http://docs.python.org/library/decimal.html#recipes
    """Convert Decimal to a money formatted string.

    places:   required number of places after the decimal point
    curr:     optional currency symbol before the sign (may be blank)
    sep:      optional grouping separator (comma, period, space, or blank)
    dp:       decimal point indicator (comma or period)
              only specify as blank when places is zero
    pos:      optional sign for positive numbers: '+', space or blank
    neg:      optional sign for negative numbers: '-', '(', space or blank
    trailneg: optional trailing minus indicator: '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places='0', sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,547.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailing='>')
    '<0.02>'
    """
    q = Decimal(10) ** -places # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = map(str, digits)
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places > 0:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return u''.join(reversed(result))

def convert2msdp(str_val):
    parts = str_val.split(".")
    parts[-1] = parts[-1].replace(",", ".")
    return u"".join(parts)

def convert2dp(str_val):
    return str_val.replace(".", "").replace(",",".")


## Deberia ir en otro lugar???
from collections import namedtuple

# Version que almacena el id del articulo
CachedItem = namedtuple('CachedItem', "articulo_id cantidad precio")

# Version que almacena una instancia de models.Articulo
ItemData = namedtuple('ItemData', "articulo cantidad precio")
DocumentData = namedtuple('DocumentData', "vendedor doctype cliente descuento total items")


#from nobix.schema import documentos, clientes
from nobix.models import Documento, Cliente
from sqlalchemy.sql import select

def get_next_docnumber(doctype):
    documentos = Documento.table
    s = select([documentos.c.numero], documentos.c.tipo==doctype,
               order_by=documentos.c.numero.desc(), limit=1)
    result = s.execute().fetchone()
    if result is None:
        return u'1'
    return unicode(result.numero + 1)

def get_next_clinumber(clitype):
    clientes = Cliente.table
    s = select([clientes.c.codigo], clientes.c.relacion==clitype,
                order_by=clientes.c.codigo.desc(), limit=1)
    result = s.execute().fetchone()
    if result is None:
        return u'1'
    return unicode(result.codigo + 1)

# OrderedSet implementation from
# http://code.activestate.com/recipes/576694/
# Requires python 2.6
import collections

class OrderedSet(collections.MutableSet):
    _KEY, _PREV, _NEXT = range(3)

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]     # sentinel node for doubly linked list
        self.map = {}               # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[self._PREV]
            curr[self._NEXT] = end[self._PREV] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[self._NEXT] = next
            next[self._PREV] = prev

    def __iter__(self):
        end = self.end
        curr = end[self._NEXT]
        while curr is not end:
            yield curr[self._KEY]
            curr = curr[self._NEXT]

    def __reversed__(self):
        end = self.end
        curr = end[self._PREV]
        while curr is not end:
            yield curr[self._KEY]
            curr = curr[self._PREV]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = next(reversed(self)) if last else next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return not self.isdisjoint(other)

    def __del__(self):
        self.clear()
