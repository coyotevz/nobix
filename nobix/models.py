# -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.hybrid import hybrid_property

from nobix.exc import NobixModelError
from nobix.config import get_current_config
from nobix.lib.saw import SQLAlchemy, BaseQuery
from nobix.lib.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

def time_now():
    return datetime.now().time()


class TimestampMixin(object):

    created = db.Column(db.DateTime, default=datetime.now)
    modified = db.Column(db.DateTime, default=datetime.now,
                         onupdate=datetime.now)


class Documento(db.Model):
    __tablename__ = 'documentos'
    __table_args__ = (db.UniqueConstraint('tipo', 'fecha', 'numero'),)

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Unicode(3), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, default=time_now)
    numero = db.Column(db.Integer)
    vendedor = db.Column(db.UnicodeText)
    descuento = db.Column(db.Numeric(10, 2), default=Decimal(0))
    neto = db.Column(db.Numeric(10, 2), nullable=False)
    fiscal = db.Column(db.UnicodeText, default=None)
    periodo_iva = db.Column(db.Date, nullable=True, default=None)

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'),
                           nullable=False, index=True)
    cliente = db.relationship('Cliente', backref="documentos")

    # Info extra documento
    cliente_nombre = db.Column(db.UnicodeText)
    cliente_direccion = db.Column(db.UnicodeText)
    cliente_cuit = db.Column(db.UnicodeText, nullable=True)

    # taxes field added by Tax model
    # items field added by ItemDocumento model
    # payment field added by DocumentPayment model

    @db.validates('tipo')
    def validate_tipo(self, key, value):
        if value not in get_current_config().documentos.keys():
            raise NobixModelError(u"'%s' no es un tipo de documento válido" % value)
        return value

    @property
    def total(self):
        return Decimal(self.neto if self.neto is not None else 0) +\
               Decimal(sum(t.monto for t in self.taxes))

    def add_payment(self, pyment_code, amount, extra=None):
        pmethod = db.query(PaymentMethod)\
                    .filter(PaymentMethod.code==pyment_code).first()
        if pmethod is None:
            raise Exception("Payment method not allowed '%s'" % pyment_code)

        payment = self.payment
        if payment is None:
            payment = DocumentPayment(document=self)

        transaction = PaymentTransaction(doc_payment=payment,
                                         method=pmethod,
                                         amount=amount,
                                         extra_info=extra)

    def __repr__(self):
        return "<Documento %s %s %s '%s' %d items, $ %s>" %\
            (self.tipo, self.fecha.isoformat(), self.numero,
             self.cliente_nombre, len(self.items), self.total)


class ItemDocumento(db.Model):
    __tablename__ = 'items_documento'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.UnicodeText)
    descripcion = db.Column(db.UnicodeText, nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2))

    articulo_id = db.Column(db.Integer, db.ForeignKey('articulos.id'),
                            index=True)
    articulo = db.relationship('Articulo', backref="doc_items")

    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'),
                             nullable=False, index=True)
    documento = db.relationship(Documento, backref="items")

    def __repr__(self):
        return "<ItemDocumento '%s-%s' $ %s x %s>" %\
            (self.articulo.codigo, self.articulo.descripcion, self.precio,
             self.cantidad)


class Tax(db.Model):
    __tablename__ = 'tax'

    id = db.Column(db.Integer, primary_key=True)
    tax_code = db.Column(db.Unicode(3), nullable=False)
    taxable = db.Column(db.Numeric(10, 2), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    document_id = db.Column(db.Integer, db.ForeignKey('documentos.id'),
                             nullable=False, index=True)
    document = db.relationship(Documento, backref="taxes")

    def __repr__(self):
        return "<Tax '%s' $ %s>" % (self.tax_code, self.amount)


class Cliente(db.Model):
    __tablename__ = 'clientes'
    __table_args__ = (db.UniqueConstraint('codigo', 'relacion'),)

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Integer)
    nombre = db.Column(db.UnicodeText, nullable=False)
    domicilio = db.Column(db.UnicodeText)
    localidad = db.Column(db.UnicodeText)
    codigo_postal = db.Column(db.UnicodeText)
    responsabilidad_iva = db.Column(db.Enum(u'C', u'I', u'R', u'M', u'E', name='respiva_enum'),
                                    default=u'C')
    cuit = db.Column(db.UnicodeText)
    relacion = db.Column(db.Enum(u'C', u'P', name="rel_enum"), default=u'C')

    # documentos field added by Documento model

    @property
    def direccion(self):
        dir_data = self.domicilio, self.localidad
        if all(dir_data):
            d = " - ".join(dir_data)
        else:
            d = "".join(dir_data)
        if self.codigo_postal:
            d += " (%s)" % self.codigo_postal
        return d


class Articulo(db.Model):
    __tablename__ = 'articulos'

    #: the product is available and can be used on a |purchase|/|sale|
    STATUS_AVAILABLE = u'STATUS_AVAILABLE'

    #: the product is closed, that is, it sill eixsts for references, but it
    #: should not be possible to create |purchase|/|sale| with it
    STATUS_CLOSED = u'STATUS_CLOSED'

    #: the product is suspended, that is, it sill exists for future references
    #: but it should not be possible to create a |purchase|/|sale| with it
    #: until back to available status.
    STATUS_SUSPENDED = u'STATUS_SUSPENDED'

    _statuses = {
        STATUS_AVAILABLE: u'Disponible',
        STATUS_CLOSED: u'Cerrado',
        STATUS_SUSPENDED: u'Suspendido',
    }

    TYPE_PERMANENT = u'TYPE_PERMANENT'
    TYPE_ON_REQUEST = u'TYPE_ON_REQUEST'
    TYPE_CONSIGMENT = u'TYPE_CONSIGMENT'

    _product_types = {
        TYPE_PERMANENT: u'Permanente',
        TYPE_ON_REQUEST: u'Bajo Pedido',
        TYPE_CONSIGMENT: u'Consignación',
    }

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.Unicode(14), nullable=False, unique=True)
    descripcion = db.Column(db.UnicodeText, nullable=False)
    proveedor = db.Column(db.UnicodeText)
    agrupacion = db.Column(db.UnicodeText)
    vigencia = db.Column(db.DateTime)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    tax_code = db.Column(db.Unicode(3), nullable=False)
    status = db.Column(db.UnicodeText, nullable=False)
    product_type = db.Column(db.UnicodeText, nullable=False)

    existencia = db.Column(db.Numeric(10, 2), default=Decimal(0))

    # doc_items field added by ItemDocumento model

    @db.validates('status')
    def validate_status(self, key, status):
        assert status in self._statuses
        return status

    @db.validates('product_type')
    def validate_product_type(self, key, product_type):
        assert product_type in self._product_types
        return product_type

    @property
    def status_str(self):
        return self._statuses.get(self.status)

    @property
    def product_type_str(self):
        return self._product_types.get(self.product_type)

    def increase_stock(self, branch, quantity, type):
        product_stock = self.stock_query.filter_by(branch=branch).one()
        product_stock.increase(quantity, type)

    def decrease_stock(self, branch, quantity, type):
        product_stock = self.stock_query.filter_by(branch=branch).one()
        product_stock.decrease(quantity, type)


    def __repr__(self):
        return u"<Articulo (%s|%s) codigo=%s '%s' $ %s>" % (self.status, self.product_type, self.codigo, self.descripcion, str(self.precio).replace('.', ','))


class Cache(db.Model):
    __tablename__ = 'cache'
    __table_args__ = (db.UniqueConstraint('vendedor', 'username', 'hostname'),)

    id = db.Column(db.Integer, primary_key=True)
    vendedor = db.Column(db.Unicode(3), nullable=False)
    username = db.Column(db.Unicode(64), nullable=False)
    hostname = db.Column(db.Unicode(64), nullable=False)
    doctype = db.Column(db.UnicodeText)
    descuento = db.Column(db.Numeric(10, 2), default=Decimal(0))
    total = db.Column(db.Numeric(10, 2), default=Decimal(0))

    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'),
                           index=True)
    cliente = db.relationship(Cliente)

    modified = db.Column(db.DateTime, nullable=False, default=datetime.now,
                         onupdate=datetime.now)
    items = db.Column(db.PickleType, default=None)


# New tables for version 0.10

class Branch(db.Model):
    __tablename__ = 'branch'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    address = db.Column(db.UnicodeText)

    def __repr__(self):
        return "<Branch(%s, %s)" % (self.name, self.address)


class ProductPriceHistory(db.Model):
    __tablename__ = 'product_price_history'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('articulos.id'))
    product = db.relationship(Articulo, backref="price_history")

    date = db.Column(db.DateTime, default=datetime.now)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return "<ProductPriceHistory d=%s p=%s>" % (self.date, self.price)

#: listener for price change
def _product_price_set(target, value, oldvalue, initiator):
    """Creates an entry in product price history table."""
    if oldvalue == value:
        return
    hist = ProductPriceHistory(product=target, price=value)
    db.add(hist)

db.event.listen(Articulo.precio, 'set', _product_price_set)


class ProductStock(db.Model, TimestampMixin):
    __tablename__ = 'product_stock'

    #: Product that this tock belong
    product_id = db.Column(db.Integer, db.ForeignKey('articulos.id'),
                           primary_key=True)
    product = db.relationship(Articulo, backref='stock')
    product_query = db.relationship(Articulo, backref=db.backref('stock_query',
                                                                 lazy='dynamic'))

    #: branch which the stock is stored
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'),
                             primary_key=True)
    branch = db.relationship(Branch, backref='stocks')

    #: current fisical quantity for this stock item
    quantity = db.Column(db.Numeric(10, 2), nullable=False)

    #: logic quantity for this stock item
    logic_quantity = db.Column(db.Numeric(10, 2))

    #: 'transactions' field added by StockTransaction model

    def increase(self, quantity, type):
        assert (type in StockTransaction.types)

        self.quantity += quantity
        st = StockTransaction(product_stock=self, quantity=quantity, type=type)
        db.session.add(st)

    def decrease(self, quantity, type):
        assert (type in StockTransaction.types)

        self.quantity -= quantity
        st = StockTransaction(product_stock=self, quantity=quantity, type=type)
        db.session.add(st)

    def __repr__(self):
        return "<ProductStock(%s, %s, %s)>" %\
                (self.product.codigo, self.branch.name, self.quantity)


class StockTransaction(db.Model):
    """This class stores information about all transactions made in the stock

    Everytime a roduct has stock increased or decreased, an object of this
    class will be created, registering the quantity, cost, responsible and
    reason for the transaction.
    """
    __tablename__ = 'stock_transaction'
    __table_args__ = (db.ForeignKeyConstraint(['product_id', 'branch_id'],
        ['product_stock.product_id', 'product_stock.branch_id']),)

    #: the transaction is an initial stock adjustment. Note that with this
    #: transaction, there is no related object.
    TYPE_INITIAL = u'TYPE_INITIAL'

    #: the transaction is a sale
    TYPE_SALE = u'TYPE_SALE'

    #: the transaction is a return of a sale
    TYPE_RETURNED_SALE = u'TYPE_RETURNED_SALE'

    #: the transaction is the cancellation of a sale
    TYPE_CANCELED_SALE = u'TYPE_CANCELED_SALE'

    #: the transaction is the receival of a purchase
    TYPE_RECEIVED_PURCHASE = u'TYPE_RECEIVED_PURCHASE'

    #: the transaction is a return of a purchase
    TYPE_RETURNED_PURCHASE = u'TYPE_RETURNED_PURCHASE'

    #: the transaction is a return of a loan
    TYPE_RETURNED_LOAN = u'TYPE_RETURNED_LOAN'

    #: the transaction is a loan
    TYPE_LOAN = u'TYPE_LOAN'

    #: the transaction is a stock decrease
    TYPE_STOCK_DECREASE = u'TYPE_STOCK_DECREASE'

    #: the transaction is a transfer from a branch
    TYPE_TRANSFER_FROM = u'TYPE_TRANSFER_FROM'

    #: the transaction is a trasfer to a branch
    TYPE_TRANSFER_TO = u'TYPE_TRANSFER_TO'

    #: the transaction is the adjustment of an inventory
    TYPE_INVENTORY_ADJUST = u'TYPE_INVENTORY_ADJUST'

    #: the transaction is a stock decrease by product failure
    TYPE_FAILURE_DECREASE = u'TYPE_FAILURE_DECREASE'

    types = {
        TYPE_INITIAL: u'Stock inicial',
        TYPE_SALE: u'Venta',
        TYPE_RETURNED_SALE : u'Devolución de Venta',
        TYPE_CANCELED_SALE : u'Devolución por cancelación de Venta',
        TYPE_RECEIVED_PURCHASE : u'Recepción de Compra',
        TYPE_RETURNED_PURCHASE : u'Devolución de Compra',
        TYPE_RETURNED_LOAN : u'Devolución de prestamo',
        TYPE_LOAN: u'Prestamo',
        TYPE_STOCK_DECREASE: u'Disminución de stock',
        TYPE_TRANSFER_FROM: u'Transferencia recibida',
        TYPE_TRANSFER_TO: u'Transferencia enviada',
        TYPE_INVENTORY_ADJUST: u'Ajuste por inventario',
        TYPE_FAILURE_DECREASE: u'Disminución por Producto fallado',
    }

    id = db.Column(db.Integer, primary_key=True)

    #: the date and time the transaction was made
    date = db.Column(db.DateTime, default=datetime.now)

    #: the product stock used in this transaction
    product_id = db.Column(db.Integer, nullable=False) # composite fk
    branch_id = db.Column(db.Integer, nullable=False)  # composite fk

    product_stock = db.relationship(
        ProductStock, backref=db.backref('transactions', lazy="dynamic"),
        primaryjoin="and_("
            "StockTransaction.product_id==ProductStock.product_id,"
            "StockTransaction.branch_id==ProductStock.branch_id)"
    )

    #: the stock cost of the transaction on the time it was made
    stock_cost = db.Column(db.Numeric(10, 2))

    #: The quantity that was removed or added to the stock.
    #: Positive value if the stock was increased, negative if decreased.
    quantity = db.Column(db.Numeric(10, 2), nullable=False)

    #: the type of transaction
    type = db.Column(db.UnicodeText, nullable=False)

    @db.validates('type')
    def validate_type(self, key, type):
        assert type in self.types.keys()
        return type

    def get_description(self):
        return self.types[self.type]

    def __repr__(self):
        return "<StockTransaction(%s, %s, %s, %s)>" %\
            (self.get_description(), self.quantity,
             self.product_stock.product.codigo, self.product_stock.branch.name)


class DocumentPayment(db.Model):
    """Defines payments in separate model to integrate with old documents that
    don't know about payments.
    """
    __tablename__ = 'document_payment'
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documentos.id'),
                            nullable=False)
    document = db.relationship(Documento,
                               backref=db.backref("payment", uselist=False))
    expiration = db.Column(db.DateTime)

    # transactions field added by PaymentItems model

    @property
    def balance(self):
        return self.document.total - sum([p.amount for p in self.transactions])

    def __repr__(self):
        return "<DocumentPayment %s %s = $ %s/%s>" %\
            (self.document.tipo, self.document.numero,
             sum([p.amount for p in self.transactions]), self.document.total)


class PaymentMethod(db.Model):
    __tablename__ = 'payment_method'

    CREDIT_CARD = u'CREDIT_CARD'
    DEBIT_CARD = u'DEBIT_CARD'
    CASH = u'CASH'
    BANK_TRANSFER = u'BANK_TRANSFER'
    CHECK = u'CHECK'
    INTERNAL_CREDIT = u'INTERNAL_CREDIT'

    _method_types = {
        CREDIT_CARD: u'Tarjeta de Crédito',
        DEBIT_CARD: u'Tarjeta de Débito',
        CASH: u'Efectivo',
        BANK_TRANSFER: u'Transferencia Bancaria',
        CHECK: u'Cheque',
        INTERNAL_CREDIT: u'Crédito Interno',
    }

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.UnicodeText, unique=True)
    name = db.Column(db.UnicodeText)
    method_type = db.Column(db.UnicodeText, nullable=False)

    # transactions field added by PaymentTransaction model

    @db.validates('method_type')
    def validates_method_type(self, key, method_type):
        assert method_type in self._method_types
        return method_type

    def __repr__(self):
        return "<PaymentMethod '%s' %s>" % (self.code, self.name)


class PaymentTransaction(db.Model, TimestampMixin):
    __tablename__ = 'payment_transaction'
    id = db.Column(db.Integer, primary_key=True)
    doc_payment_id = db.Column(db.Integer, db.ForeignKey('document_payment.id'),
                               nullable=False)
    doc_payment = db.relationship(DocumentPayment, backref='transactions')
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'),
                          nullable=False)
    method = db.relationship(PaymentMethod, backref='transactions')
    extra_info = db.Column(db.UnicodeText)

    def __repr__(self):
        return "<PaymentTransaction %s, $ %s (%s)>" %\
            (self.method.name, self.amount, self.created.isoformat())


class UserQuery(BaseQuery):

    def authenticate(self, login, password):
        if not (password and login):
            return None, False
        user = self.filter(User.username==login).first()
        return user, (user.check_password(password) if user else False)


class User(db.Model, TimestampMixin):
    __tablename__ = 'user'
    query_class = UserQuery

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.UnicodeText, nullable=False)
    last_name = db.Column(db.UnicodeText)
    username = db.Column(db.Unicode(60), unique=True, nullable=False)
    _pw_hash = db.Column('pw_hash', db.Unicode(80))

    # TODO: relates with roles & permissions
    #

    @hybrid_property
    def password(self):
        return self._pw_hash

    @password.setter
    def password(self, password):
        self._pw_hash = unicode(generate_password_hash(password))

    def check_password(self, password):
        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    def __repr__(self):
        return "<User %s '%s, %s'>" % (self.username, self.last_name,
                                       self.first_name)
