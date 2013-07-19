<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->
<%page expression_filter = "x"/>
<%
    global last_y, counter
    d_fmt = "%d/%m/%Y %H:%M"
    page_fmt = u"Página %s de %s"
    item_base_height = 14
    last_y = item_base_y = 48.133667 - item_base_height
    counter = 0
    fontsizes = {
      'normal': 12,
      'big': 14,
      'subtitle': 16,
    }
    rowlengths = {
      12: 96,
      14: 83,
      16: 50,
    }
%>

<%def name="render_row(row_content, font_weight='normal', font_size=12, extra_height=0, x=23.470703, anchor='start', align='start')"><%doc>{{{</%doc>
<% global last_y, counter; last_y += item_base_height + extra_height; counter += 1 %>
<% row_length = rowlengths[font_size] %>
<text id="text${counter}" xml:space="preserve" x="${x}" y="${last_y}" sodipodi:linespacing="100%"
  style="font-size:${font_size}px;font-style:normal;font-variant:normal;font-weight:${font_weight};font-stretch:normal;text-align:${align};line-height:100%;writing-mode:lr-tb;text-anchor:${anchor};color:#000000;fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.5;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono">
  <tspan sodipodi:role="line" id="tspan${counter}" x="${x}" y="${last_y}">${row_content[:row_length]}</tspan>
</text>
</%def>
## }}}
<%def name="render_group_title(title)"><%doc>{{{</%doc>
  ${render_row(title[:50].center(50), font_size=fontsizes['subtitle'], extra_height=10, x=372.04382, anchor='middle', align='center')}
</%def>
## }}}
<%def name="render_list_header(content, style='normal')"><%doc>{{{</%doc>
  ${render_row(content, font_weight='bold', font_size=fontsizes[style], extra_height=5)}
</%def>
## }}}
<%def name="render_list_row(content, style='normal')"><%doc>{{{</%doc>
  ${render_row(content, font_size=fontsizes[style])}
</%def>
## }}}
<%def name="render_group(title, columns, items)"><%doc>{{{</%doc>
    % if title != "":
    ${render_group_title(title)}
    % endif
    % if columns != "":
    ${render_list_header(columns)}
    % endif
    % for item in items:
      ${render_row(item)}
    % endfor
</%def>
## }}}
<%def name="render_page_number(current, total)"><%doc>{{{</%doc>
<text id="page_number" xml:space="preserve" sodipodi:linespacing="100%" y="1028.5692" x="23.51416"
  style="font-size:9px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-align:start;line-height:100%;writing-mode:lr-tb;text-anchor:start;color:#000000;fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.5;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono">
  <tspan y="1028.5692" x="23.51416" id="page_tspan" sodipodi:role="line">${page_fmt % (current, total)}</tspan>
</text>
</%def>
## }}}

<svg xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:svg="http://www.w3.org/2000/svg"
  xmlns="http://www.w3.org/2000/svg" xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
  xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="210mm" height="297mm" id="svg2"
  version="1.1" inkscape:version="0.47 r22583" sodipodi:docname="lista_agrupaciones.svg">
  <sodipodi:namedview id="base" pagecolor="#ffffff" bordercolor="#666666" borderopacity="1.0"
    inkscape:pageopacity="0.0" inkscape:pageshadow="2" inkscape:zoom="1.3531463" inkscape:cx="314.66815"
    inkscape:cy="813.17805" inkscape:document-units="px" inkscape:current-layer="layer1" showgrid="false"
    inkscape:window-width="1680" inkscape:window-height="975" inkscape:window-x="0" inkscape:window-y="25"
    inkscape:window-maximized="1" showguides="true" inkscape:guide-bbox="true" />
  <metadata id="metadata"><!--{{{-->
    <rdf:RDF>
      <cc:Work rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title>Lista</dc:title>
        <dc:date>18/06/2010</dc:date>
        <dc:creator>
          <cc:Agent>
            <dc:title>Augusto Roccasalva</dc:title>
          </cc:Agent>
        </dc:creator>
        <dc:rights>
          <cc:Agent>
            <dc:title>Augusto Roccasalva</dc:title>
          </cc:Agent>
        </dc:rights>
        <dc:language>es-ar</dc:language>
        <dc:description>Plantilla utilizada para las listas de Río Plomo, este archivo es procesado por mako para generar el documento final, se lo hace pasar por rsvg+cairo para generar el PDF o el PS según corresponda.</dc:description>
        <cc:license rdf:resource="http://creativecommons.org/licenses/by-nc/3.0/" />
      </cc:Work>
      <cc:License rdf:about="http://creativecommons.org/licenses/by-nc/3.0/">
        <cc:permits rdf:resource="http://creativecommons.org/ns#Reproduction" />
        <cc:permits rdf:resource="http://creativecommons.org/ns#Distribution" />
        <cc:requires rdf:resource="http://creativecommons.org/ns#Notice" />
        <cc:requires rdf:resource="http://creativecommons.org/ns#Attribution" />
        <cc:prohibits rdf:resource="http://creativecommons.org/ns#CommercialUse" />
        <cc:permits rdf:resource="http://creativecommons.org/ns#DerivativeWorks" />
      </cc:License>
    </rdf:RDF>
  </metadata><!--}}}-->

  <g inkscape:label="Capa 1" inkscape:groupmode="layer" id="layer1">

    <g id="header_lines"><!--{{{-->
      <text id="date_row" xml:space="preserve" x="722.22754" y="33.156128" sodipodi:linespacing="100%"
        style="font-size:13px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-align:end;line-height:100%;writing-mode:lr-tb;text-anchor:end;color:#000000;fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.5;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Bitstream Vera Sans">
        <tspan sodipodi:role="line" id="tspan3594" x="722.22754" y="33.156128">${docdate.strftime(d_fmt)}</tspan>
      </text>

      <text id="title_row" xml:space="preserve" x="372.04333" y="34.13562" sodipodi:linespacing="100%"
        style="font-size:16px;font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;text-align:center;line-height:100%;writing-mode:lr-tb;text-anchor:middle;color:#000000;fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.5;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Bitstream Vera Sans Bold">
        <tspan x="372.04333" y="34.13562" style="marker:none" id="tspan2925">${title[:44].center(44)}</tspan>
      </text>
    </g><!--}}}-->

    % for grpname, columns, items in groups:
    ${render_group(grpname, columns, items)}
    % endfor

    ${render_page_number(doc_count, doc_total_count)}
  </g>
</svg>
<!-- vim:foldenable:foldmethod=marker:ft=xml.mako:sw=2
-->
