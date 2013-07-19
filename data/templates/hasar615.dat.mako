% for idx, header in headers:
]|${idx}|${header}
% endfor
b|${customer_name}|${customer_cuit}|${customer_resp}|${customer_doctype}
@|${docletter}|T
% for lines, item in fitems:
% for line in lines:
A|${line}|0
% endfor
B|${item.descripcion}|${moneyfmt(item.cantidad)}|${moneyfmt(item.precio)}|${item.iva}|${item.signo}|${item.impint}|0|${item.base}
% endfor
% if desc is not UNDEFINED:
T|${desc.descripcion}|${moneyfmt(desc.monto)}|${desc.signo}|0|${desc.base}
% endif
C|p|0|0
D|CONTADO|0.00|T|0
% for idx, footer in footers:
]|${idx}|${footer}
% endfor
E
