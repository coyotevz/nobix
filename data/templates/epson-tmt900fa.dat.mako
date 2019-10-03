## cancelo comprobantes abiertos
-1 0A07|0000
-1 0B07|0000
## abro comprobante
0 0B01|0000|${customer_name}||${customer_address}|||${customer_doctype}|${customer_cuit}|${customer_resp}||||
\
% for lines, item in fitems:
0 0B02|4000\
% for line in (['', '', '', '', item.descripcion]+lines)[-5:]:
|${line}\
% endfor
|${moneyfmt4_epson(item.cantidad)}|${moneyfmt4_epson(item.precio)}|${item.iva.replace('.', '')}|0|0|||0|7|7
% endfor
% if desc is not UNDEFINED:
0 0B03|0000
<%
  if customer_resp == 'I': monto = desc.monto/Decimal('1.21')
  else: monto = desc.monto
%>
% if desc.signo == 'm':
0 0B04|0000|${desc.descripcion}|${moneyfmt(monto).replace('.','')}||DESC|7
% elif desc.signo == 'M':
0 0B04|0001|${desc.descripcion}|${moneyfmt(monto).replace('.','')}||AJUS|7
% endif
% endif
0 0B06|0003|1|${vendedor}|2|Defensa al Consumidor Mza. 0800-222-6678||
