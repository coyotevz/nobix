#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial
from itertools import groupby, chain
from operator import itemgetter
from collections import defaultdict
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

# for experimental tree views
from multiprocessing import Process, Queue

from urwid import Text, Columns, Pile, AttrMap, Divider, Frame, ListBox, SolidFill, CheckBox
from urwid import connect_signal
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy.orm.exc import NoResultFound

from nobix.db import Session
from nobix.config import get_current_config
from nobix.models import Documento, ItemDocumento, Articulo, Cliente
from nobix.widget import Dialog, DateSelectorBox, InputBox
from nobix.sqlwalker import QueryWalker
from nobix.utils import moneyfmt, check_password, message_waiter, show_error
from nobix.ui import group_list_printer, ReportListPrinter, MaeterCodeBox, search_terceros, highlight_focus_in

session = Session()
moneyfmt = partial(moneyfmt, sep='.', dp=',')

# temp functions
def highlight_focus_in(widget):
    widget.highlight = 0, len(widget._edit_text)

class Listado(Dialog):#{{{

    def __init__(self, title=None, stitle=None, list_header=None):#{{{
        self._check_methods()

        query = self.build_query()
        max_rows = self.build_max_rows()

        self.walker = QueryWalker(query, self.formatter, max_rows, self.row_adapter, self.result_callback)
        querylist = ListBox(self.walker)

        header_row = []
        title_row = []

        if title:
            title_row.append(('listado.title.important', title))
        if stitle:
            title_row.append(stitle)

        if len(title_row) > 0:
            header_row.append(AttrMap(Text(title_row, align='center', wrap='clip'), 'listado.title'))

        if list_header:
            header_row.append(AttrMap(list_header, 'listado.list_header'))

        if len(header_row) > 0:
            header = Pile(header_row)
        else:
            header = None

        footer = Text("Calculando ...")
        self.short_footer = None
        self.large_footer = None
        self._current_footer = 0

        self.content = Frame(
                AttrMap(querylist, 'listado.body'),
                header=header,
                footer=AttrMap(footer, 'listado.footer'))

        self.__super.__init__(self.content,
                height=('relative', 100),
                width=('relative', 100),
                with_border=False)
#}}}
    def _check_methods(self):#{{{
        for meth in ('build_query', 'build_max_rows', 'formatter', 'row_adapter', 'result_callback'):
            method = getattr(self, meth, None)
            if not method:
                raise NotImplementedError("'%s' must be implemented in subclasses of Listado" % meth)
            if not callable(method):
                raise RuntimeError("'%s.%s' must be callable method to run properly" %\
                        (type(self).__name__, meth))
#}}}
    def keypress(self, key):#{{{
        if key in ('enter', 'esc', ' ', 'f10'):
            self.quit()
        elif key in ('v', 'V'):
            self.switch_footer()
        return self.__super.keypress(key)
#}}}
    def configure_subloop(self, subloop):#{{{
        self.walker.connect_watcher(subloop)
#}}}
    def quit(self, *args):#{{{
        self.walker.stop_workers()
        return self.__super.quit(*args)
#}}}
    def switch_footer(self):#{{{
        if self.large_footer and self.short_footer:
            self.content.set_footer((self.short_footer, self.large_footer)[self._current_footer])
            self._current_footer = 1 - (1 * self._current_footer)
#}}}
    def run(self):#{{{
        message_waiter(" Procesando información ... ")
        return self.__super.run()
#}}}
#}}}

class LibroIVA(Listado):#{{{

    def __init__(self, start_date=None, end_date=None, period=None):#{{{
        self.period = period
        if start_date is None:
            start_date = period + relativedelta(day=1)
        self.start_date = start_date
        if end_date is None:
            end_date = period + relativedelta(day=31)
        self.end_date = end_date

        title = "Libro IVA"
        if period:
            stitle = " (periodo %s)" % period.strftime("%m/%Y")
        else:
            stitle = " (%s - %s)" % (start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y"))

        list_header = Columns([
            ('fixed', 8, Text("Fecha", align='center')),
            ('fixed', 6, Text("Número", align='right')),
            ('fixed', 3, Text("Doc", align='center')),
            Text("Razón Social", align='left'),
            ('fixed', 10, Text("Total", align='right')),
            ('fixed', 10, Text("Neto", align='right')),
            ('fixed', 9, Text("Impuesto", align='right')),
        ], dividechars=1)

        self.__super.__init__(title=title, stitle=stitle, list_header=list_header)
#}}}
    def formatter(self, row):#{{{
        s = 1 if row.fiscal in ('+venta', '-compra') else -1
        return Columns([
            ('fixed', 8, Text("%s" % (row.fecha.strftime("%d/%m/%y"),))),
            ('fixed', 6, Text("%s" % (row.numero,), align='right')),
            ('fixed', 3, Text("%s" % (row.tipo,))),
            Text("%s" % (row.cliente_nombre,), align='left', wrap='clip'),
            ('fixed', 10, Text("%s" % (moneyfmt(s*row.total),), align='right')),
            ('fixed', 10, Text("%s" % (moneyfmt(s*row.neto),), align='right')),
            ('fixed', 9, Text("%s" % (moneyfmt(s*Decimal(sum([t.monto for t in row.tasas]))),), align='right')),
        ], dividechars=1)
#}}}
    def row_adapter(self, row):#{{{
        return (row.fiscal, row.total, row.neto, [(t.nombre, t.monto) for t in row.tasas])
#}}}
    def _preprocess_result(self, result):#{{{
        data = defaultdict(dict)
        data['tasas'] = defaultdict(dict)
        k0 = itemgetter(0)
        k1 = itemgetter(1)

        for g, val in groupby(sorted(result, key=k0), key=k0):
            l = list(val)
            data['total'][g] = list(map(k1, l))
            data['neto'][g] = list(map(itemgetter(2), l))
            for n, m in groupby(sorted(chain(*list(map(itemgetter(3), l))), key=k0), key=k0):
                data['tasas'][g][n] = list(map(k1, m))

        return data
#}}}
    def result_callback(self, result):#{{{
        imp = get_current_config().impuestos
        data = self._preprocess_result(result)

        total_ventas = Decimal(sum(data['total'].get('+venta', [])) - sum(data['total'].get('-venta', [])))
        total_compras = Decimal(sum(data['total'].get('+compra', [])) - sum(data['total'].get('-compra', [])))

        gravado_ventas = Decimal(sum(data['neto'].get('+venta', [])) - sum(data['neto'].get('-venta', [])))
        gravado_compras = Decimal(sum(data['neto'].get('+compra', [])) - sum(data['neto'].get('-compra', [])))

        _total_doc = Text(["Total documentos: ", ('listado.footer.important', "%s" % len(result))])

        self.short_footer = AttrMap(Columns([
            _total_doc,
            ('fixed', 3, Text([('listado.footer.important', "^^^")])),
        ], dividechars=1), 'listado.footer')

        large_items = []

        c = len(data['total'].get('+compra', [])) + len(data['total'].get('-compra', []))
        v = len(data['total'].get('+venta', [])) + len(data['total'].get('-venta', []))

        tc = [k for k, v in imp.items() if v['operacion'] == 'compra']
        tv = [k for k, v in imp.items() if v['operacion'] == 'venta']

        if c > 0:
            citems = [Text(["Importe Gravado: ",
                            ('listado.footer.important', "$ %11s" % moneyfmt(gravado_compras))],
                           align='right')]

            for cod in tc:
                if (cod in data['tasas']['+compra'] or cod in data['tasas']['-compra']):
                    m = Decimal( sum(data['tasas']['+compra'].get(cod, []))
                                -sum(data['tasas']['-compra'].get(cod, [])))
                    citems.append(Text([imp[cod]['nombre']+': ',
                        ('listado.footer.important', "$ %11s" % moneyfmt(m))
                    ], align='right'))

            large_items.append(Columns([
                ('fixed', 25, AttrMap(Text([('listado.footer.key', "Compras: "),
                                            ('listado.footer.important', "$ %11s" % moneyfmt(total_compras))
                                      ]), 'listado.footer')),
                AttrMap(Pile(citems), 'listado.footer'),
                ], dividechars=1))

        if c > 0 and v > 0:
            large_items.append(Divider("─"))

        if v > 0:
            vitems = [Text(["Importe Gravado: ",
                            ('listado.footer.important', "$ %11s" % moneyfmt(gravado_ventas))],
                           align='right')]

            for cod in tv:
                if (cod in data['tasas']['+venta'] or cod in data['tasas']['-venta']):
                    m = Decimal( sum(data['tasas']['+venta'].get(cod, []))
                                -sum(data['tasas']['-venta'].get(cod, [])))
                    vitems.append(Text([imp[cod]['nombre']+': ',
                        ('listado.footer.important', "$ %11s" % moneyfmt(m))
                    ], align='right'))

            large_items.append(Columns([
                ('fixed', 25, AttrMap(Text([('listado.footer.key', "Ventas: "),
                                            ('listado.footer.important', " $ %11s" % moneyfmt(total_ventas))
                                      ]), 'listado.footer')),
                AttrMap(Pile(vitems), 'listado.footer'),
                ], dividechars=1))

        large_items.append(AttrMap(Columns([_total_doc,
            ('fixed', 3, Text([('listado.footer.important', "vvv")]))], dividechars=1), 'listado.footer'))

        self.large_footer = Pile(large_items)

        self.switch_footer()
#}}}
    def _build_sub_query(self):#{{{
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

        return session.query(Documento).filter(Documento.fiscal!=None).\
                       filter(date_condition).\
                       order_by(Documento.fecha.asc(), Documento.tipo.asc(), Documento.numero.asc())
#}}}
    def build_max_rows(self):#{{{
        return self._build_sub_query().count()
#}}}
    def build_query(self):#{{{
        return self._build_sub_query().outerjoin(Documento.tasas).options(contains_eager(Documento.tasas))
#}}}
#}}}
class SubDiarioVentas(Listado):#{{{

    def __init__(self, start_date=None, end_date=None, period=None):#{{{
        self.period = period
        if start_date is None:
            start_date = period + relativedelta(day=1)
        self.start_date = start_date
        if end_date is None:
            end_date = period + relativedelta(day=31)
        self.end_date = end_date

        self._current_date = None
        self._count = defaultdict(int)
        self._tot_day = 0
        self._doc_tracker = set()

        title = "Subdiario de ventas"
        if period:
            stitle = " (periodo %s)" % period.strftime("%m/%Y")
        else:
            stitle = " (%s - %s)" % (start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y"))

        list_header = Columns([
            ('fixed', 6, Text("Número", align='center')),
            ('fixed', 3, Text("Tip", align='center')),
            Text("Razón Social", align='left'),
            ('fixed', 3, Text("Ven", align='center')),
            ('fixed', 6, Text("Items", align='center')),
            ('fixed', 6, Text("Impues", align='center')),
            ('fixed', 6, Text("Descue", align='center')),
            ('fixed', 9, Text("Total", align='right')),
        ], dividechars=1)

        self.__super.__init__(title=title, stitle=stitle, list_header=list_header)
#}}}
    def formatter(self, row):#{{{

        _key = (row.fecha, row.tipo, row.numero)
        if _key in self._doc_tracker:
            return None
        self._doc_tracker.add(_key)

        date = row.fecha
        formatted = Columns([
            ('fixed', 6, Text("%s" % (row.numero,), align='right')),
            ('fixed', 3, Text("%s" % (row.tipo,))),
            Text("%s" % (row.cliente_nombre or '',), align='left'),
            ('fixed', 3, Text("%s" % (row.vendedor or '',), align='right')),
            ('fixed', 6, Text("%s" % (moneyfmt(Decimal(sum([i.cantidad for i in row.items]))),),
                              align='right')),
            ('fixed', 6, Text("%s" % (moneyfmt(Decimal(sum([t.monto for t in row.tasas]))),), align='right')),
            ('fixed', 6, Text("%s" % (moneyfmt(row.descuento),), align='right')),
            ('fixed', 9, Text("%s" % (moneyfmt(row.total),), align='right')),
        ], dividechars=1)

        if self._current_date and self._current_date == date:
            return formatted
        else:
            d = "%s" % date.strftime("%A, %d de %B del %Y")
            self._current_date = date
            return Pile([
                AttrMap(Columns([
                    Divider("─"),
                    ('fixed', len(d)+2, Text(('listado.body.important.bold', d), align='center')),
                    Divider("─")
                ]), 'listado.body.important'),
                formatted])
#}}}
    def row_adapter(self, row):#{{{
        return (row.vendedor, row.total, row.fecha, row.tipo, row.numero)
#}}}
    def result_callback(self, result):#{{{
        result = set(result)
        vend = get_current_config().vendedores
        data = defaultdict(list)
        k0 = itemgetter(0)
        k1 = itemgetter(1)

        for g, val in groupby(sorted(result, key=k0), key=k0):
            n = vend[g]['nombre'] if g in vend else g
            l = list(val)
            data[n].extend(list(map(k1, l)))

        _total_doc = Text(["Total documentos: ", ('listado.footer.important', "%s" % len(result))])

        self.short_footer = AttrMap(Columns([
            _total_doc,
            ('fixed', 3, Text([('listado.footer.important', "^^^")])),
        ], dividechars=1), 'listado.footer')

        _totals = sorted([(n, Decimal(sum([_f for _f in val if _f]))) for n, val in data.items()],
                         key=k1, reverse=True)
        large_items = [AttrMap(Columns([
            ('fixed', 35, Text(str(n or '~')+':', align='right')),
            AttrMap(Text(" %11s" % moneyfmt(val), align='left'), 'listado.footer.important'),
        ]), 'listado.footer') for n, val in _totals]
        large_items.append(AttrMap(Columns([
            ('fixed', 35, Text("Total:", align='right')),
            AttrMap(Text(" %11s" % moneyfmt(Decimal(sum(map(k1, _totals)))), align='left'),
                    'listado.footer.important'),
        ]), 'listado.footer.key'))
        large_items.append(AttrMap(Columns([_total_doc,
            ('fixed', 3, Text([('listado.footer.important', "vvv")]))], dividechars=1), 'listado.footer'))

        self.large_footer = Pile(large_items)
        self.switch_footer()
#}}}
    def _build_sub_query(self):#{{{
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

        return session.query(Documento).filter(Documento.fiscal!=None).\
                       filter(date_condition).\
                       filter(Documento.tipo.in_(['FAA', 'FAC'])).\
                       order_by(Documento.fecha.asc(), Documento.numero.asc())
#}}}
    def build_max_rows(self):#{{{
        return self._build_sub_query().count()
#}}}
    def build_query(self):#{{{
        return self._build_sub_query().outerjoin(Documento.tasas).options(contains_eager(Documento.tasas)).\
                                       outerjoin(Documento.items).options(contains_eager(Documento.items))
#}}}
#}}}

class SelectDateRange(Dialog):#{{{

    def __init__(self, title=None, cls=None):#{{{
        if cls is None:
            cls = type('Dummy', (object,), {'run': lambda *a: None})
        self.cls = cls

        self._desde_err = None
        self._hasta_err = None

        _edit_cancel = lambda *w: self.focus_button(1)
        _edit_ok = lambda *w: self.focus_button(0)
        def _focus_hasta(*w):
            self.content.set_focus(1)

        self.desde = DateSelectorBox(out_fmt="%d/%m/%Y")
        err = ('desde_error', '_desde_err')
        connect_signal(self.desde, 'focus-in', self.on_fecha_focus_in, err)
        connect_signal(self.desde, 'focus-out', self.on_fecha_focus_out, err)
        connect_signal(self.desde, 'edit-cancel', _edit_cancel)
        connect_signal(self.desde, 'edit-done', self.on_fecha_edit_done, err+(_focus_hasta,))
        connect_signal(self.desde, 'bad-date-error', self.on_fecha_error, err)
        self.desde_error = Text("", wrap='clip')

        self.hasta = DateSelectorBox(out_fmt="%d/%m/%Y")
        err = ('hasta_error', '_hasta_err')
        connect_signal(self.hasta, 'focus-in', self.on_fecha_focus_in, err)
        connect_signal(self.hasta, 'focus-out', self.on_fecha_focus_out, err)
        connect_signal(self.hasta, 'edit-cancel', _edit_cancel)
        connect_signal(self.hasta, 'edit-done', self.on_fecha_edit_done, err+(_edit_ok,))
        connect_signal(self.hasta, 'bad-date-error', self.on_fecha_error, err)
        self.hasta_error = Text("", wrap='clip')

        desde_row = Columns([
            ('fixed', 14, AttrMap(Text("Desde", align='right'), 'dialog.selectdate.label')),
            ('fixed', 11, AttrMap(self.desde, 'dialog.selectdate.input', 'dialog.selectdate.input.focus')),
            AttrMap(self.desde_error, 'dialog.selectdate.error'),
        ], dividechars=1)

        hasta_row = Columns([
            ('fixed', 14, AttrMap(Text("Hasta", align='right'), 'dialog.selectdate.label')),
            ('fixed', 11, AttrMap(self.hasta, 'dialog.selectdate.input', 'dialog.selectdate.input.focus')),
            AttrMap(self.hasta_error, 'dialog.selectdate.error'),
        ], dividechars=1)

        self.content = Pile([
            desde_row,
            hasta_row,
            Divider(),
        ])

        t = "Rango de Fechas"
        if title:
            t += " - %s" % title

        # Set initial dates
        self.desde.set_value(date.today()+relativedelta(day=1)) # Principio de mes
        self.hasta.set_value(date.today()+relativedelta(day=31)) # Fin de mes

        buttons = [("Continuar", self.run_list), ("Cancelar", self._quit)]

        self.__super.__init__(self.content, buttons,
                title=t,
                height=None,
                width=60,
                attr_style='dialog.selectdate',
                title_attr_style='dialog.selectdate.title')
#}}}
    def run_list(self, *args):#{{{
        subdialog = self.cls(start_date=self.desde.get_value(), end_date=self.hasta.get_value())
        self.dialog_result = subdialog.run()
        self.quit()
#}}}

    ### Signals Handlers ###

    def on_fecha_focus_in(self, widget, err):#{{{
        (errwidget, errstate) = err
        if getattr(self, errstate) is None:
            getattr(self, errwidget).set_text("")
            widget.highlight = 0, len(widget._edit_text)
#}}}
    def on_fecha_focus_out(self, widget, err):#{{{
        (errwidget, errstate) = err
        setattr(self, errstate, None)
        getattr(self, errwidget).set_text("")
#}}}
    def on_fecha_edit_done(self, widget, value, err):#{{{
        (errwidget, errstate, cb) = err
        if getattr(self, errstate) is not None:
            getattr(self, errwidget).set_text(getattr(self, errstate))
            setattr(self, errstate, None)
            widget.highlight = 0, len(widget._edit_text)
            return
        getattr(self, errwidget).set_text("")
        cb()
#}}}
    def on_fecha_error(self, widget, msg, err):#{{{
        (errwidget, errstate) = err
        setattr(self, errstate, msg)
        getattr(self, errwidget).set_text(msg)
#}}}
#}}}
class SelectPeriod(SelectDateRange):#{{{

    def __init__(self, title=None, cls=None):#{{{
        if cls is None:
            cls = type('Dummy', (object,), {'run': lambda *a: None})
        self.cls = cls

        self._periodo_err = None

        _edit_ok = lambda *w: self.focus_button(0)

        in_fmt = ('%m%y', '%m%Y', '%m/%y', '%m/%Y', '%m-%y', '%m-%Y', '%m.%y', '%m.%Y')
        self.periodo = DateSelectorBox(in_fmt=in_fmt, out_fmt="%m/%Y")
        err = ('periodo_error', '_periodo_err')
        connect_signal(self.periodo, 'focus-in', self.on_fecha_focus_in, err)
        connect_signal(self.periodo, 'focus-out', self.on_fecha_focus_out, err)
        connect_signal(self.periodo, 'edit-cancel', lambda *w: self.focus_button(1))
        connect_signal(self.periodo, 'edit-done', self.on_fecha_edit_done, err+(_edit_ok,))
        connect_signal(self.periodo, 'bad-date-error', self.on_fecha_error, err)
        self.periodo_error = Text("", wrap='clip')

        periodo_row = Columns([
            ('fixed', 14, AttrMap(Text("Periodo", align='right'), 'dialog.selectdate.label')),
            ('fixed', 11, AttrMap(self.periodo, 'dialog.selectdate.input', 'dialog.selectdate.input.focus')),
        ], dividechars=1)

        self.content = Pile([
            periodo_row,
            Divider(),
        ])

        t = "Periodo"
        if title:
            t += " - %s" % title

        self.periodo.set_value(date.today()+relativedelta(day=1))

        buttons = [("Continuar", self.run_list), ("Cancelar", self._quit)]

        Dialog.__init__(self, self.content, buttons,
                title=t,
                height=None,
                width=60,
                attr_style='dialog.selectdate',
                title_attr_style='dialog.selectdate.title')
#}}}
    def run_list(self, *args):#{{{
        subdialog = self.cls(period=self.periodo.get_value())
        self.dialog_result = subdialog.run()
        self.quit()
#}}}
#}}}
class SelectArticlesDateRange(SelectDateRange):#{{{

    def __init__(self, title=None, cls=None):#{{{
        if cls is None:
            cls = type('Dummy', (object,), {'run': lambda *a: None})
        self.cls = cls

        self._desde_err = None
        self._hasta_err = None

        _edit_cancel = lambda *w: self.focus_button(1)
        _edit_ok = lambda *w: self.focus_button(0)
        def _focus_hasta(*w):
            self.content.set_focus(2)

        self.articulos = InputBox()
        self.articulos.filter_input = lambda t: t.upper()
        connect_signal(self.articulos, "edit-done", self.on_articulos_edit_done)
        connect_signal(self.articulos, "edit-cancel", _edit_cancel)

        self.desde = DateSelectorBox(out_fmt="%d/%m/%Y")
        err = ('desde_error', '_desde_err')
        connect_signal(self.desde, 'focus-in', self.on_fecha_focus_in, err)
        connect_signal(self.desde, 'focus-out', self.on_fecha_focus_out, err)
        connect_signal(self.desde, 'edit-cancel', _edit_cancel)
        connect_signal(self.desde, 'edit-done', self.on_fecha_edit_done, err+(_focus_hasta,))
        connect_signal(self.desde, 'bad-date-error', self.on_fecha_error, err)
        self.desde_error = Text("", wrap='clip')

        self.hasta = DateSelectorBox(out_fmt="%d/%m/%Y")
        err = ('hasta_error', '_hasta_err')
        connect_signal(self.hasta, 'focus-in', self.on_fecha_focus_in, err)
        connect_signal(self.hasta, 'focus-out', self.on_fecha_focus_out, err)
        connect_signal(self.hasta, 'edit-cancel', _edit_cancel)
        connect_signal(self.hasta, 'edit-done', self.on_fecha_edit_done, err+(_edit_ok,))
        connect_signal(self.hasta, 'bad-date-error', self.on_fecha_error, err)
        self.hasta_error = Text("", wrap='clip')

        articulos_row = Columns([
            ('fixed', 14, AttrMap(Text("Artículos", align='right'), 'dialog.selectdate.label')),
            AttrMap(self.articulos, 'dialog.selectdate.input', 'dialog.selectdate.input.focus'),
        ], dividechars=1)

        desde_row = Columns([
            ('fixed', 14, AttrMap(Text("Desde", align='right'), 'dialog.selectdate.label')),
            ('fixed', 11, AttrMap(self.desde, 'dialog.selectdate.input', 'dialog.selectdate.input.focus')),
            AttrMap(self.desde_error, 'dialog.selectdate.error'),
        ], dividechars=1)

        hasta_row = Columns([
            ('fixed', 14, AttrMap(Text("Hasta", align='right'), 'dialog.selectdate.label')),
            ('fixed', 11, AttrMap(self.hasta, 'dialog.selectdate.input', 'dialog.selectdate.input.focus')),
            AttrMap(self.hasta_error, 'dialog.selectdate.error'),
        ], dividechars=1)

        self.include_inactives = CheckBox("Incluir Desactivados", state=True)
        include_inactives_row = Columns([
            ('fixed', 14, Divider()),
            AttrMap(self.include_inactives, 'dialog.selectdate.label'),
        ], dividechars=1)

        self.content = Pile([
            articulos_row,
            desde_row,
            hasta_row,
            include_inactives_row,
            Divider(),
        ])

        t = "Artículos y Rango de Fechas"
        if title:
            t += " - %s" % title

        # Set initial dates
        self.desde.set_value(date(2001, 0o1, 0o1)) # FIXME: hardcoded > Principio de actividad
        self.hasta.set_value(date.today()+relativedelta(day=31)) # Fin de mes

        buttons = [("Continuar", self.run_list), ("Cancelar", self._quit)]

        Dialog.__init__(self, self.content, buttons,
                title=t,
                height=None,
                width=60,
                attr_style='dialog.selectdate',
                title_attr_style='dialog.selectdate.title')
#}}}
    def run_list(self, *args):
        art_list = self.get_articles()
        if not art_list:
            show_error(["Los artículos ingresados no producen ningún resultado válido, ",
                        "ingrese ", ('dialog.warning.important', "artículos"), " o ",
                        ('dialog.warning.important', "grupos"), " correctos."])
            self._pile.set_focus(0)
            self.content.set_focus(0)
            return
        subdialog = self.cls(start_date=self.desde.get_value(),
                             end_date=self.hasta.get_value(),
                             articles=art_list)
        self.dialog_result = subdialog.run()
        self.quit()

    def get_articles(self):
        arts = []
        code_list = set([c.strip() for c in self.articulos.get_edit_text().split(",")])
        agrup_list = [c[1:] for c in code_list if c.startswith('@')]
        code_list = code_list.difference(agrup_list)
        query = session.query(Articulo)
        if self.include_inactives.get_state() is False:
            query = query.filter(Articulo.es_activo==True)
        if code_list:
            art = query.filter(Articulo.codigo.in_(code_list)).all()
            order = dict([(v, i) for i, v in enumerate(code_list)])
            art.sort(cmp=lambda a, b: cmp(order[a.codigo], order[b.codigo]))
            arts.extend(art)
        if agrup_list:
            art = query.filter(Articulo.agrupacion.in_(agrup_list)).order_by(Articulo.codigo).all()
            order = dict([(v, i) for i, v in enumerate(agrup_list)])
            art.sort(cmp=lambda a, b: cmp(order[a.agrupacion], order[b.agrupacion]))
            arts.extend(art)
        return arts

    def on_articulos_edit_done(self, widget, text):
        self.content.set_focus(1)
#}}}

class SelectClient(Dialog):

    def __init__(self, title=None, cls=None):
        if cls is None:
            cls = type('Dummy', (object,), {'__init__': lambda *a, **k: None, 'run': lambda *a: None})
        self.cls = cls
        self._obj = None

        _edit_cancel = lambda *w: self.focus_button(1)

        self.codigo_box = MaeterCodeBox(max_length=12, align='right')
        connect_signal(self.codigo_box, 'focus-in', highlight_focus_in),
        connect_signal(self.codigo_box, 'edit-done', self.on_codigo_edit_done)
        connect_signal(self.codigo_box, 'edit-cancel', _edit_cancel)
        connect_signal(self.codigo_box, 'search-client', self.on_client_search)

        self.nombre = Text('')

        client_row = Columns([
            ('fixed', 8, AttrMap(Text("Cliente", align='right'), 'dialog.selectdate.label')),
            ('fixed', 6, AttrMap(self.codigo_box, 'dialog.selectdate.input', 'dialog.selectdate.input.focus')),
            AttrMap(self.nombre, 'dialog.selectdate.label'),
        ], dividechars=1)

        self.content = Pile([
            client_row,
            Divider(),
        ])

        buttons = [("Continuar", self.run_list), ("Cancelar", self.quit)]

        self.__super.__init__(self.content, buttons,
                title=title or '<Falta titulo>',
                height=None,
                width=60,
                attr_style='dialog.selectdate',
                title_attr_style='dialog.selectdate.title')

    def run_list(self, *args):
        if not self._obj:
            self._pile.set_focus(0)
            self.content.set_focus(0)
            return
        subdialog = self.cls(cliente=self._obj)
        self.dialog_result = subdialog.run()
        self.quit()

    def on_codigo_edit_done(self, widget, code):
        if code != "":
            query = session.query(Cliente).filter(Cliente.codigo==int(code))
            query = query.filter(Cliente.relacion=="C")
            try:
                self._obj = query.one()
                self.codigo_box.set_edit_text(self._obj.codigo)
                self.nombre.set_text(self._obj.nombre + " - " + self._obj.direccion)
                self.focus_button(0)
            except NoResultFound:
                self._obj = None
                self.nombre.set_text("")

    def on_client_search(self, widget, search_by=None, first_key=None):
        response = search_terceros(search_by=search_by, first_key=first_key)
        if response:
            self.codigo_box.set_edit_text(str(response[0].codigo))
            self.nombre.set_text(str(response[0].nombre))
            self.on_codigo_edit_done(self.codigo_box, str(response[0].codigo))
        return None


class ListadoAdapter(object):#{{{

    def __init__(self, adapted):
        self._adapted = adapted

    def __call__(self, *args, **kwargs):
        return self._adapted(*args, **kwargs)
#}}}

### Lista en árbol EXPERIMENTAL
from nobix.treetools import TreeListWalker, TreeListBox
from nobix.treeviewer import DateNode, ArticleNode, ClientMonthNode

class SubDiarioVentasTree(Dialog):#{{{

    def __init__(self, start_date=None, end_date=None, period=None):#{{{
        self.period = period
        if start_date is None:
            start_date = period + relativedelta(day=1)
        self.start_date = start_date
        if end_date is None:
            end_date = period + relativedelta(day=31)
        self.end_date = end_date

        title = "Subdiario de ventas"
        if period:
            stitle = " (periodo %s)" % period.strftime("%m/%Y")
        else:
            stitle = " (%s - %s)" % (start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y"))

        list_header = Columns([
            ('fixed', 2, Divider()),
            ('fixed', 3, Text("Tip", align='center')),
            ('fixed', 6, Text("Número", align='center')),
            Text("Razón Social", align='left'),
            ('fixed', 5, Text("Hora", align='left')),
            ('fixed', 3, Text("Ven", align='right')),
            ('fixed', 6, Text("Impues", align='right')),
            ('fixed', 6, Text("Descue", align='right')),
            ('fixed', 9, Text("Total".upper(), align='right')),
        ], dividechars=1)

        title_row = [('listado.title.important', title), stitle]
        header_row = [
            AttrMap(Text(title_row, align='center', wrap='clip'), 'listado.title'),
            AttrMap(list_header, 'listado.list_header'),
        ]

        header = Pile(header_row)
        footer = Text("Calculando ...")
        self.short_footer = None
        self.large_footer = None
        self._current_footer = 0

        query = session.query(Documento.fecha).filter(Documento.fecha.between(start_date, end_date))\
                                              .order_by(Documento.fecha).distinct()

        treestore = TreeListWalker([DateNode(k[0]) for k in query])
        treebox = TreeListBox(treestore)

        self.content = Frame(
                AttrMap(treebox, 'listado.body'),
                header=header,
                footer=AttrMap(footer, 'listado.footer'))

        self.configure_subprocess()

        self.__super.__init__(self.content,
                height=('relative', 100),
                width=('relative', 100),
                with_border=False)
#}}}
    def keypress(self, key):#{{{
        if key in ('enter', 'esc', ' ', 'f10'):
            self.quit()
        elif key in ('v', 'V'):
            self.switch_footer()
        return self.__super.keypress(key)
#}}}
    def switch_footer(self):#{{{
        if self.large_footer and self.short_footer:
            self.content.set_footer((self.short_footer, self.large_footer)[self._current_footer])
            self._current_footer = 1 - (1 * self._current_footer)
#}}}
    def run(self):#{{{
        message_waiter(" Procesando información ... ")
        self._subprocess.start()
        return self.__super.run()
#}}}
    def configure_subprocess(self):#{{{
        self._subquery = session.query(Documento)\
                                .filter(Documento.fecha.between(self.start_date, self.end_date))\
                                #.filter(Documento.tipo.in_([u'FAC', u'FAA'])).order_by(Documento.fecha)
        self._qout = Queue()
        self._subprocess = Process(target=self.execute_query, args=(self._qout,))
#}}}
    def configure_subloop(self, loop):#{{{
        self._loop = loop
        self._handle = loop.event_loop.watch_file(self._qout._reader, self.result_callback)
#}}}
    def execute_query(self, qout):#{{{
        from sqlalchemy import create_engine
        fresh_engine = create_engine(get_current_config().database_uri)
        self._subquery.session.bind = fresh_engine
        qout.put([(d.vendedor, d.total, d.tipo) for d in self._subquery])
        qout.close()
#}}}
    def result_callback(self):#{{{
        result = self._qout.get()
        vend = get_current_config().vendedores
        data = defaultdict(lambda: defaultdict(list))
        k0 = itemgetter(0)
        k1 = itemgetter(1)
        k2 = itemgetter(2)
        cols = ('FAC+FAA', 'REM', 'PRE')

        for vcode, docs in groupby(sorted(result, key=k0), key=k0):
            vname = vend[vcode]['nombre'] if vcode in vend else vcode
            for dtype, docs in groupby(sorted(docs, key=k2), key=k2):
                data[vname][dtype].extend(list(map(k1, docs)))

        _totals_by_type = defaultdict(int)
        for vname, dtype in data.items():
            dtype['FAC+FAA'] = dtype.get('FAC', []) + dtype.get('FAA', [])
            for c in cols:
                _totals_by_type[c] = _totals_by_type[c] + len(dtype.get(c, []))

        _totals_by_type = [(c, _totals_by_type[c]) for c in cols]

        _total_docs_row = ["Total documentos: ", ('listado.footer.important', "%s" % len(result)), "  ("]
        for k, v in _totals_by_type:
            _total_docs_row.extend(["%s: " % k, ('listado.footer.important', "%d" % v), "   "])
        del _total_docs_row[-1]
        _total_docs_row.append(")")

        _total_docs_row = Text(_total_docs_row, wrap='clip')

        self.short_footer = AttrMap(Columns([
            _total_docs_row,
            ('fixed', 3, Text([('listado.footer.important', "^^^")])),
        ], dividechars=1), 'listado.footer')

        def _t(e):
            return sum(e[1]['FAC+FAA']) + Decimal('0.9')*sum(e[1]['REM'])

        def _nozero(docs):
            return sum([sum(docs[c]) for c in cols]) > 0

        _totals = sorted([(vname, docs) for vname, docs in data.items() if _nozero(docs)],
                          key=_t, reverse=True)

        large_items = [AttrMap(Columns([Text('', wrap='clip')] + [
            ('fixed', 11, Text('%s' % c, align='right')) for c in cols] + [
            ('fixed', 5, Divider()),
        ], dividechars=1), 'listado.footer')]

        large_items.extend([AttrMap(Columns([Text(str(vname or '~')+':', align='right')] + [
            ('fixed', 11, AttrMap(Text("%11s" % moneyfmt(Decimal(sum(dtype[c]))), align='left', wrap='clip'),
                                  'listado.footer.important')) for c in cols] + [
            ('fixed', 5, Divider()),
        ], dividechars=1), 'listado.footer') for vname, dtype in _totals])

        def _tot_col(col):
            return Decimal(sum([sum(dtype[col]) for _, dtype in _totals]))

        large_items.append(AttrMap(Columns([Text("Total:", align='right'),] + [
            ('fixed', 11, AttrMap(Text("%11s" % moneyfmt(_tot_col(c)), align='left', wrap='clip'),
                'listado.footer.important')) for c in cols ] + [
            ('fixed', 5, Divider()),
        ], dividechars=1), 'listado.footer.key'))

        large_items.append(AttrMap(Columns([ _total_docs_row,
            ('fixed', 3, Text([('listado.footer.important', "vvv")])), ], dividechars=1), 'listado.footer'))

        self.large_footer = Pile(large_items)
        self.switch_footer()
        self._loop.event_loop.remove_watch_file(self._handle)
        self._loop.draw_screen()
#}}}
#}}}

class MovimientosArticuloTree(Dialog):

    def __init__(self, start_date=None, end_date=None, period=None, articles=[]):
        self.period = period
        if start_date is None:
            start_date = period + relativedelta(day=1)
        self.start_date = start_date
        if end_date is None:
            end_date = period + relativedelta(day=31)
        self.end_date = end_date

        title = "(EXPERIMENTAL) Movimiento de Artículos"
        if period:
            stitle = " (periodo %s)" % period.strftime("%m/%Y")
        else:
            stitle = " (%s - %s)" % (start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y"))

        list_header = Columns([
            ('fixed', 1, Divider()),
            ('fixed', 14, Text("Código", align='left')),
            ('fixed', 6, Text("Existencias"[:6], align='right')),
            ('fixed', 6, Text("byMoviment"[:6], align='right')),
            Text("Descripción"),
        ], dividechars=1)

        title_row = [('listado.title.important', title), stitle]
        header_row = [
            AttrMap(Text(title_row, align='center', wrap='clip'), 'listado.title'),
            AttrMap(list_header, 'listado.list_header'),
        ]

        header = Pile(header_row)
        #footer = Text("Calculando ...")
        key = 'listado.footer.important'
        footer = Text([
            (key, "+"), "/", (key, "-"), " expandir/colapsar   ",
            (key, "ESC"), ",", (key, "ENTER"), ",",
            (key, "ESPACIO"), " o ", (key, "F10"),
            " para continuar"], align='right')
        self.short_footer = None
        self.large_footer = None
        self._current_footer = 0

        treestore = TreeListWalker([ArticleNode((k, start_date, end_date)) for k in articles])
        treebox = TreeListBox(treestore)

        self.content = Frame(
                AttrMap(treebox, 'listado.body'),
                header=header,
                footer=AttrMap(footer, 'listado.footer'))

        self.configure_subprocess()

        self.__super.__init__(self.content,
                height=('relative', 100),
                width=('relative', 100),
                with_border=False)

    def configure_subprocess(self):
        pass

    def keypress(self, key):
        if key in ('enter', 'esc', ' ', 'f10'):
            self.quit()
        return self.__super.keypress(key)

class ClientHistory(Dialog):

    def __init__(self, cliente):
        title = "(EXPERIMENTAL) Historia de %s" % cliente.nombre

        list_header = Columns([
            ('fixed', 2, Divider()),
            ('fixed', 3, Text("Tip", align='center')),
            ('fixed', 6, Text("Número", align='center')),
            ('fixed', 3, Text("Ven", align='right')),
            ('fixed', 6, Text("Impues", align='right')),
            ('fixed', 6, Text("Descue", align='right')),
            ('fixed', 9, Text("Total".upper(), align='right')),
            Divider(),
            ('fixed', 6, Text("Fecha", align='left')),
            ('fixed', 5, Text("Hora", align='left')),
        ], dividechars=1)

        title_row = [('listado.title.important', title), " beta"]
        header_row = [
            AttrMap(Text(title_row, align='center', wrap='clip'), 'listado.title'),
            AttrMap(list_header, 'listado.list_header'),
        ]

        header = Pile(header_row)
        key = 'listado.footer.important'
        footer = Text([
            (key, "+"), "/", (key, "-"), " expandir/colapsar   ",
            (key, "ESC"), ",", (key, "ENTER"), ",",
            (key, "ESPACIO"), " o ", (key, "F10"),
            " para continuar"], align='right')

        query = session.query(Documento.fecha).filter(Documento.cliente==cliente).order_by(Documento.fecha)
        months = sorted(session.query(func.date_part("month", Documento.fecha),
                                      func.date_part("year", Documento.fecha)
                                      ).filter(Documento.cliente_id==cliente.id).distinct().all(),
                        key=itemgetter(1, 0))

        treestore = TreeListWalker([ClientMonthNode((cliente, date(int(m[1]), int(m[0]), 1))) for m in months])
        treebox = TreeListBox(treestore)

        self.content = Frame(
                AttrMap(treebox, 'listado.body'),
                header=header,
                footer=AttrMap(footer, 'listado.footer'))

        self.__super.__init__(self.content,
                height=('relative', 100),
                width=('relative', 100),
                with_border=False)

    def keypress(self, key):
        if key in ('enter', 'esc', ' ', 'f10'):
            self.quit()
        return self.__super.keypress(key)

def sec_view(name, func):#{{{
    def _checker():
        permiso = check_password(name)
        if permiso is True:
            return func()
    return _checker
#}}}
def unsec_view(name, func):#{{{
    return func
#}}}

views_map = (
    ('libro_iva_periodo', ('Libro IVA por periodo',
        sec_view("Ver libro IVA", SelectPeriod('Libro IVA', LibroIVA).run))),
    ('libro_iva_fechas', ('Libro IVA por fecha',
        sec_view("Ver libro IVA", SelectDateRange('Libro IVA', LibroIVA).run))),
#    ('subdiario_periodo', ('Sub-diario de Ventas por periodo',
#        sec_view(u"Ver sub-diario", SelectPeriod('Sub-diario Ventas', SubDiarioVentas).run))),
    ('subdiario_periodo_tree', ('Sub-diario de Ventas por periodo',
        sec_view("Sub-diario de Ventas", SelectPeriod('Sub-diario Ventas', SubDiarioVentasTree).run))),
#    ('subdiario_fechas', ('Sub-diario de Ventas por fecha',
#        sec_view(u"Ver sub-diario", SelectDateRange('Sub-diario Ventas', SubDiarioVentas).run))),
    ('subdiario_fechas_tree', ('Sub-diario de Ventas por fecha',
        sec_view("Sub-diario de Ventas", SelectDateRange('Sub-diario Ventas', SubDiarioVentasTree).run))),
    ('movimientos_fecha', ('Movimientos por fecha (EXPERIMENTAL)',
        sec_view("Ver movimientos", SelectArticlesDateRange('Movimientos (EXPERIMENTAL)', MovimientosArticuloTree).run))),
    ('historial_clientes', ('Historial clientes (EXPERIMENTAL)',
        sec_view("Ver historial clientes", SelectClient('Clientes (EXPERIMENTAL)', ClientHistory).run))),
    ('listado_por_agrupacion', ('Imprime Artículos por Agrupación',
        unsec_view("Imprimir Artículos", group_list_printer))),
    ('resumen_periodo', ('Imprime Resumen Mensual',
        sec_view("Imprimir Resumen", SelectPeriod('Resumen', ListadoAdapter(ReportListPrinter)).run))),
    ('resumen_fecha', ('Imprime Resumen por fecha',
        sec_view("Imprimir Resumen", SelectDateRange('Resumen', ListadoAdapter(ReportListPrinter)).run))),
)

# vim:foldenable:foldmethod=marker
