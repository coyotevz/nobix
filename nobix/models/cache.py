# -*- coding: utf-8 -*-

from datetime import datetime
from . import db


class Cache(db.Model):
    __tablename__ = 'cache'
    __table_args__ = (
        db.UniqueConstraint('salesman', 'username', 'hostname'),
    )

    id = db.Column(db.Integer, primary_key=True)
    vendedor = db.Column('salesman', db.Unicode(3), nullable=False)
    username = db.Column(db.Unicode(64), nullable=False)
    hostname = db.Column(db.Unicode(64), nullable=False)
    doctype = db.Column(db.UnicodeText(3))
    descuento = db.Column('discount', db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)
    cliente_id = db.Column('customer_id', db.Integer, db.ForeignKey('customer.id'),
                           index=True)
    cliente = db.relationship('Cliente', lazy='joined')
    modified = db.Column(db.DateTime, nullable=False, default=datetime.now,
                         onupdate=datetime.now)
    items = db.Column(db.PickleType, default=None)
