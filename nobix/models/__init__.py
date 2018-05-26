# -*- coding: utf-8 -*-

from datetime import datetime
from nobix.lib.saw import SQLAlchemy


db = SQLAlchemy()


def time_now():
    return datetime.now().time()


from .document import Documento
from .item import ItemDocumento
from .tax import Tasa
from .product import Articulo
from .customer import Cliente
from .cache import Cache
