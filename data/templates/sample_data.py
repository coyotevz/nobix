#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Datos de muestra para pasar a los templates en esta carpeta
"""

from collections import namedtuple
from datetime import datetime

HItem = namedtuple('Item', 'desc qty price tax sign ii base')

hasar615_data = {
    'headers': (
        #      <- 40                                 ->
        ('07', '                                      '),
        ('08', 'CDO CONTADO             Vend:      20 '),
        ('09', '                                      '),
        ('10', '10389     PEDRO B PALACIOS 1180       '),
    ),

    'footers': (
        ('11', 'Defensa Consumidor Mza. 08002226678   '),
        ('12', 'Gracias por su preferencia            '),
    ),

    'type': 'A',
    'cliente': 'MODENA AUTOMOTORA SRL         ',
    'cuit': '30640093842',
    'resp': 'I',

    'items': [
        #  <- 28                     ->
        (('10      GOMA FLOT. CONICA 3/',),
        #      <- 20             ->    <- 14       ->    <- 10   ->    < 4 >    1    <- 11    ->    1
         HItem('4                   ', '+001.000000000', '+000001.50', '21.00', 'M', '+0.00000000', 'T')),

        (('20      GOMA S/TAPA EXT.IDEA',),
         HItem('L                   ', '+001.000000000', '+000001.10', '21.00', 'M', '+0.00000000', 'T')),
        (('1045    SELLAROSCAS HIDRO3 X',),
         HItem(' 25 CC.             ', '+001.000000000', '+000005.20', '21.00', 'M', '+0.00000000', 'T')),
        (('1046    SELLAROSCAS HIDRO3 X',),
         HItem(' 50 CC.             ', '+001.000000000', '+000009.00', '21.00', 'M', '+0.00000000', 'T')),
        ((),
         HItem('Descuento           ', '+000.000000000', '+000000.66', '**.**', 'm', '+0.00000000', 'T')),
    ],
}

PItem = namedtuple('PItem', 'codigo descripcion cantidad precio total')

presupuesto_data = {
    'show_logo': True,
    'docletter': 'X',
    'docname': 'presupuesto',
    'doccopy': 'original',
    'docdate': datetime.today(),
    'docnumber': '5',
    'docpv': '3',
    'vendedor': '20 - Augusto Roccasalva',
    'customer_name': 'CARLOS ROCCASALVA',
    'customer_address': u'América 2869 - Bº Judicial',
    'items': [
        PItem(u'13513', u'TIRON CAÑO IPS 4x4 1/2', '1,00', '32,43', '32,43'),
        PItem(u'13519', u'TIRON CAÑO IPS 4x4 3/4', '1,00', '50,60', '50,60'),
        PItem(u'10113', u'CODO 90º HH 1/2 IPS', '5,00', '0,74', '3,70'),
        PItem(u'10119', u'CODO 90º HH 3/4 IPS', '5,00', '1,19', '5,90'),
    ],
    'document_total': '92,63',
    'show_footer_legend': True,
    'footer_lines': [
        'Linea de pie de prueba',
        'Otra linea',
    ],
}
