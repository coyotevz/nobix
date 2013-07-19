#!/usr/bin/env python
# -*- coding: utf-8 -*-

from decimal import Decimal
from functools import partial
from itertools import chain
from collections import defaultdict

from sqlalchemy.exc import DataError
from urwid import Text, Columns, WidgetWrap, AttrMap, Divider, Padding
from dateutil.relativedelta import relativedelta

from nobix.db import Session
from nobix.models import Documento, ItemDocumento, Tasa
from nobix.treetools import TreeWidget, TreeNode, ParentNode
from nobix.utils import moneyfmt
from nobix.config import get_current_config

session = Session()
moneyfmt = partial(moneyfmt, sep='.', dp=',')

def tryint(q):
    q = q.normalize()
    prec = max(q.as_tuple().exponent, -2)
    return moneyfmt(q, places=-prec)

_doc = get_current_config().documentos
entrada = [t for t, d in _doc.iteritems() if d['stock'] == u'entrada']
salida = [t for t, d in _doc.iteritems() if d['stock'] == u'salida']
entsal = entrada + salida
mov = [t for t, d in _doc.iteritems() if (d['stock'] and t not in entsal)]

class BaseTreeWidget(TreeWidget):
    indent_cols = 1

    def __init__(self, node, expanded=True):
        self._node = node
        self._innerwidget = None
        self.is_leaf = not hasattr(node, 'get_first_child')
        self.expanded = expanded
        widget = self.get_indented_widget()
        # Se omite la inicializacion de TreeWidget
        WidgetWrap.__init__(self, widget)

    def selectable(self):
        return True

class DateNode(ParentNode):
    """Metadata storage for individual date"""
    def load_widget(self):
        return DateWidget(self, False)

    def load_child_keys(self):
        query = session.query(Documento.id).filter(Documento.fecha==self.get_value()).order_by(Documento.id)
        return [k[0] for k in query] + ['footer']

    def load_child_node(self, key):
        """Return a DocumentNode"""
        childdepth = self.get_depth() + 1
        if key == 'footer':
            return FooterDateNode(None, parent=self, key=key, depth=childdepth)
        doc = session.query(Documento).get(key)
        return DocumentNode(doc, parent=self, key=key, depth=childdepth)

    def get_accum(self):
        if hasattr(self, 'accum'):
            return self.accum
        self.accum = accum = defaultdict(Decimal)
        for key in self.get_child_keys():
            try:
                doc = session.query(Documento).get(key)
                accum[doc.tipo] += doc.total
            except DataError:
                session.rollback()
        accum['FAC+FAA'] = accum['FAC'] + accum['FAA']
        return accum

class DateWidget(BaseTreeWidget):
    """Widget for individual dates"""
    def load_inner_widget(self):
        d = self.get_node().get_value().strftime("%a %d/%b/%Y").decode("utf-8")
        return AttrMap(Columns([
            ('fixed', len(d)+2, Text(('listado.body.important.bold', d.title()), align='left')),
        ]), 'listado.body.important')

class DocumentNode(ParentNode):
    """Metadata storage for individial document"""
    def load_widget(self):
        return DocumentWidget(self, False)

    def load_child_keys(self):
        query = session.query(ItemDocumento.id).filter(ItemDocumento.documento==self.get_value())\
                                               .order_by(ItemDocumento.id)
        return ['header'] + [k[0] for k in query]

    def load_child_node(self, key):
        """Return DocumentItemNode"""
        childdepth = self.get_depth() + 1
        if key == 'header':
            return HeaderDocumentItemNode(None, parent=self, key=key, depth=childdepth)

        item = session.query(ItemDocumento).get(key)
        return DocumentItemNode(item, parent=self, key=key, depth=childdepth)

class DocumentWidget(BaseTreeWidget):
    """Widget for individual documents"""
    def get_indented_widget(self):
        widget = self.get_inner_widget()
        if not self.is_leaf:
            widget = AttrMap(Columns([('fixed', 1,
                [self.unexpanded_icon, self.expanded_icon][self.expanded]),
                widget], dividechars=1), 'listado.tree.docline', 'listado.tree.docline.focus')
        indent_cols = self.get_indent_cols()
        return Padding(widget, width=('relative', 100), left=indent_cols)

    def load_inner_widget(self):
        doc = self.get_node().get_value()
        return AttrMap(Columns([
            ('fixed', 3, Text("%s" % (doc.tipo,))),
            ('fixed', 6, Text("%s" % (doc.numero,), align='right')),
            Text("%s" % (doc.cliente_nombre or '',), align='left', wrap='clip'),
            ('fixed', 5, Text("%s" % (doc.hora.strftime("%H:%M"),))),
            ('fixed', 3, Text("%s" % (doc.vendedor or '',), align='right')),
            ('fixed', 6, Text("%s" % (moneyfmt(Decimal(sum([t.monto for t in doc.tasas]))),), align='right')),
            ('fixed', 6, Text("%s" % (moneyfmt(doc.descuento),), align='right')),
            ('fixed', 9, Text("%s" % (moneyfmt(doc.total),), align='right')),
        ], dividechars=1), 'listado.tree.docline', 'listado.tree.docline.focus')

class DocumentItemNode(TreeNode):
    """Metadata storage for individual document item"""
    def load_widget(self):
        return DocumentItemWidget(self, False)

class DocumentItemWidget(BaseTreeWidget):
    """Widget for individual document item"""
    indent_cols = 0

    def load_inner_widget(self):
        item = self.get_node().get_value()
        return AttrMap(Columns([
            ('fixed', 14, Text("%s" % (item.codigo or '',))),
            Text("%s" % (item.descripcion,), align='left', wrap='clip'),
            ('fixed', 8, Text("%s" % (moneyfmt(item.cantidad),), align='right')),
            ('fixed', 8, Text("%s" % (moneyfmt(item.precio),), align='right')),
            ('fixed', 9, Text("%s" % (moneyfmt(item.precio*item.cantidad),), align='right')),
        ], dividechars=1), 'listado.tree.itemline', 'listado.tree.itemline.focus')

class HeaderDocumentItemNode(TreeNode):
    def load_widget(self):
        return HeaderDocumentItemWidget(self, False)

class HeaderDocumentItemWidget(DocumentItemWidget):

    def load_inner_widget(self):
        return AttrMap(Columns([
            ('fixed', 14, Text(u"Código", align='left')),
            Text(u"Descripción", align='left', wrap='clip'),
            ('fixed', 8, Text(u"Cantidad", align='right')),
            ('fixed', 8, Text(u"Precio", align='right')),
            ('fixed', 9, Text(u"Total", align='right')),
        ], dividechars=1), 'listado.tree.itemheader')

    def selectable(self):
        return False

class FooterDateNode(TreeNode):
    def load_widget(self):
        return FooterDateWidget(self, False)

class FooterDateWidget(HeaderDocumentItemWidget):

    def load_inner_widget(self):
        accum = self.get_node().get_parent().get_accum()
        accum['FAC+FAA'] = accum['FAC'] + accum['FAA']
        # order FAC+FAA, REM, PRE, SAL, ENT
        docorder = ['FAC+FAA', 'REM', 'PRE', 'SAL', 'ENT']
        tots = list(chain.from_iterable([('listado.tree.itemheader.important', "%s:" % k),
                                         ('listado.tree.itemheader.key', " %s" % moneyfmt(accum[k])), " | "]
                                         for k in docorder if accum[k] != 0))[:-1]
        return AttrMap(Columns([
            Text([u"Total día: "] + tots, wrap='clip'),
        ], dividechars=1), 'listado.tree.itemheader')

# Article tree elements
class ArticleNode(ParentNode):
    """Metadata storage for individual article"""
    def load_widget(self):
        return ArticleWidget(self, False)

    def load_child_keys(self):
        article, start_date, end_date = self.get_value()
        query = session.query(ItemDocumento.id).filter(ItemDocumento.articulo_id==article.id)\
                       .join(Documento).filter(Documento.tipo.in_(entsal+mov))\
                       .filter(Documento.fecha.between(start_date, end_date)).order_by(Documento.fecha.asc())
        return ['header'] + [k[0] for k in query]

    def load_child_node(self, key):
        childdepth = self.get_depth() + 1
        if key == 'header':
            return HeaderArticleItemNode(None, parent=self, key=key, depth=childdepth)

        doc_item = session.query(ItemDocumento).get(key)
        return ArticleItemNode(doc_item, parent=self, key=key, depth=childdepth)

class ArticleWidget(BaseTreeWidget):
    """Widget for individual articles"""
    def load_inner_widget(self):
        d = self.get_node().get_value()[0]
        return AttrMap(Columns([
            ('fixed', 14, Text(('listado.body.important.bold', d.codigo), align='left')),
            ('fixed', 6, Text(('listado.body.important.bold', tryint(d.existencia)), align='right')),
            ('fixed', 6, Text(('listado.body.important.bold', tryint(d.existencia_new)), align='right')),
            Text(d.descripcion),
        ], dividechars=1), 'listado.body.important')

class ArticleItemNode(TreeNode):
    """Metadata storage for inidividual article document item"""
    def load_widget(self):
        return ArticleItemWidget(self, False)

class ArticleItemWidget(BaseTreeWidget):
    """Widget for individual document article item"""
    indent_cols = 0

    def load_inner_widget(self):
        movicon = " "
        item = self.get_node().get_value()
        doc = item.documento
        if doc.tipo in entrada:
            #movicon = u"→"
            movicon = u">"
        elif doc.tipo in salida:
            #movicon = u"←"
            movicon = u"<"
        return AttrMap(Columns([
            ('fixed', 8, Text("%s" % (tryint(item.cantidad),), align='right')),
            ('fixed', 1, Text(movicon)),
            ('fixed', 10, Text("%s" % doc.fecha.strftime("%d/%m/%Y"))),
            ('fixed', 5, Text("%s" % doc.hora.strftime("%H:%M"))),
            ('fixed', 3, Text("%s" % doc.tipo)),
            ('fixed', 6, Text("%s" % doc.numero, align='right')),
            ('fixed', 3, Text("%s" % doc.vendedor, align='right')),
            ('fixed', 8, Text("%s" % moneyfmt(item.precio), align='right')),
        ], dividechars=1), 'listado.tree.itemline', 'listado.tree.itemline.focus')

class HeaderArticleItemNode(TreeNode):
    def load_widget(self):
        return HeaderArticleItemWidget(self, False)

class HeaderArticleItemWidget(ArticleItemWidget):

    def load_inner_widget(self):
        return AttrMap(Columns([
            ('fixed', 8, Text(u"Cantidad", align='left')),
            ('fixed', 1, Divider()),
            ('fixed', 10, Text(u"Fecha", align='right')),
            ('fixed', 5, Text(u"Hora", align='right')),
            ('fixed', 3, Text(u"Tip")),
            ('fixed', 6, Text(u"Número")),
            ('fixed', 3, Text(u"Ven")),
            ('fixed', 8, Text(u"Precio", align='right')),
        ], dividechars=1), 'listado.tree.itemheader')

    def selectable(self):
        return False

# Client history nodes
class ClientMonthNode(ParentNode):

    def load_widget(self):
        return ClientMonthWidget(self, False)

    def load_child_keys(self):
        cliente, month = self.get_value()
        s, e = month + relativedelta(day=1), month + relativedelta(day=31)
        query = session.query(Documento.id).filter(Documento.cliente_id==cliente.id).filter(Documento.fecha.between(s, e))
        return [k[0] for k in query] + ['footer']

    def load_child_node(self, key):
        childdepth = self.get_depth() + 1
        if key == 'footer':
            return FooterClientDocumentNode(None, parent=self, key=key, depth=childdepth)
        doc = session.query(Documento).get(key)
        return ClientDocumentNode(doc, parent=self, key=key, depth=childdepth)

    def get_accum(self):
        accum = defaultdict(Decimal)
        for key in self.get_child_keys():
            try:
                doc = session.query(Documento).get(key)
                accum[doc.tipo] += doc.total
            except DataError:
                session.rollback()
        return accum

class ClientMonthWidget(BaseTreeWidget):
    def load_inner_widget(self):
        month = self.get_node().get_value()[1]
        d = month.strftime("%b/%Y").decode("utf-8")
        return AttrMap(Columns([
            ('fixed', len(d)+2, Text(('listado.body.important.bold', d.title()), align='left')),
        ]), 'listado.body.important')

class ClientDocumentNode(DocumentNode):
    def load_widget(self):
        doc = self.get_value()
        return ClientDocumentWidget(self, False)

class ClientDocumentWidget(DocumentWidget):
    def load_inner_widget(self):
        doc = self.get_node().get_value()
        return AttrMap(Columns([
            ('fixed', 3, Text("%s" % (doc.tipo,))),
            ('fixed', 6, Text("%s" % (doc.numero,), align='right')),
            ('fixed', 3, Text("%s" % (doc.vendedor or '',), align='right')),
            ('fixed', 6, Text("%s" % (moneyfmt(Decimal(sum([t.monto for t in doc.tasas]))),), align='right')),
            ('fixed', 6, Text("%s" % (moneyfmt(doc.descuento),), align='right')),
            ('fixed', 9, Text(('listado.body.key', "%s" % (moneyfmt(doc.total),)), align='right')),
            Divider(),
            ('fixed', 6, Text("%s" % (doc.fecha.strftime("%d/%m"),), align='left')),
            ('fixed', 5, Text("%s" % (doc.hora.strftime("%H:%M"),))),
        ], dividechars=1), 'listado.tree.docline', 'listado.tree.docline.focus')

class FooterClientDocumentNode(TreeNode):
    def load_widget(self):
        return FooterClientDocumentWidget(self, False)

class FooterClientDocumentWidget(BaseTreeWidget):
    indent_cols = 0
    def load_inner_widget(self):
        accum = self.get_node().get_parent().get_accum()
        tots = list(chain.from_iterable([('listado.tree.itemheader.important', "%s:" % k),
                                         ('listado.tree.itemheader.key', " %s" % moneyfmt(v)), " | "]
                                         for k, v in sorted(accum.iteritems())))[:-1]
        return AttrMap(Columns([
            Text(["Total mes: "] + tots, wrap='clip'),
        ], dividechars=1), 'listado.tree.itemheader')

    def selectable(self):
        return False
