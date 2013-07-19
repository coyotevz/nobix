<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->
<%page expression_filter = "x" />
<%
    d_fmt = '%d/%m/%Y'
    base_row = 1
    #item_base_y = 335.10352
    #item_base_y = 402.43042
    #item_base_y = 357.87399
    item_base_y = 379.07399
    item_base_height = 14
    footer_base_y = 860.58728
    footer_base_height = 12

    def tryint(q):
        q = q.normalize()
        prec = max(q.as_tuple().exponent, -2)
        return moneyfmt(q, places=-prec)
%>

<%def name="render_item(count, item)"><%doc>{{{</%doc>
  <% current_row = base_row + count; current_y = item_base_y + (count * item_base_height) %>
  <g id="row_${current_row}">
    <text id="qty_${current_row}" x="120.4742" y="${current_y}" sodipodi:linespacing="125%"
      style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:end;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:end;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono">
      <tspan sodipodi:role="line" id="qty_${current_row}_span" x="120.4742"
        y="${current_y}">${tryint(item.cantidad)}</tspan>
    </text>

    <%
        desc = ''
        if item.codigo:
          desc += '[' + item.codigo + '] '
        desc += item.descripcion
    %>

    <text id="description_${current_row}" x="127.56034" y="${current_y}" sodipodi:linespacing="125%"
      style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono">
      <tspan sodipodi:role="line" id="description_${current_row}_span" x="127.56034"
        y="${current_y}">${desc[:80]}</tspan>
    </text> 
  </g>
</%def><%doc>}}}</%doc>

<svg id="svg2" width="210mm" height="297mm" version="1.1" xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   inkscape:version="0.48.2 r9819" sodipodi:docname="remito_preimpreso.svg">
   <title id="titulo">Remito Preimpreso</title>
   <sodipodi:namedview id="base" pagecolor="#ffffff" bordercolor="#666666" borderopacity="1.0"
     inkscape:pageopacity="0.0" inkscape:pageshadow="2" inkscape:zoom="1.0" inkscape:cx="377.58821"
     inkscape:cy="818.69486" inkscape:document-units="mm" inkscape:current-layer="layer1" showgrid="false"
     showguides="true" inkscape:guide-bbox="true" units="mm" inkscape:window-width="1680"
     inkscape:window-height="1050" inkscape:window-x="0" inkscape:window-y="0" inkscape:window-maximized="0">
     <!--{{{ guide lines -->
    <sodipodi:guide orientation="1,0" position="106.29921,800.7874" id="guide3069" />
    <sodipodi:guide orientation="0,1" position="106.29921,800.7874" id="guide3087" />
    <sodipodi:guide orientation="1,0" position="517.32283,903.54331" id="guide3089" />
    <sodipodi:guide orientation="0,1" position="517.32283,903.54331" id="guide3091" />
    <sodipodi:guide orientation="1,0" position="531.49606,800.7874" id="guide3093" />
    <sodipodi:guide orientation="1,0" position="35.433071,751.1811" id="guide3095" />
    <sodipodi:guide orientation="0,1" position="35.433071,751.1811" id="guide3099" />
    <sodipodi:guide orientation="1,0" position="116.92913,662.59843" id="guide3101" />
    <sodipodi:guide orientation="0,1" position="116.92913,662.59843" id="guide3103" />
    <sodipodi:guide orientation="1,0" position="120.47244,662.59843" id="guide3105" />
    <sodipodi:guide orientation="1,0" position="113.38583,662.59843" id="guide3107" />
    <!--}}}-->
  </sodipodi:namedview>
  <metadata id="metadata"><!--{{{-->
    <rdf:RDF>
      <cc:Work rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title>Remito Preimpreso</dc:title>
        <dc:date>20/09/2011</dc:date>
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
        <dc:description>Plantilla utlizada para la generación de Remitos preimpresos en Río Plomo, este archivo es procesado por mako para generar el documento final, se lo hace pasar por rsvg+cairo para generar el PDF o el PS según corresponda.</dc:description>
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

  <g id="layer1" inkscape:label="Capa 1" inkscape:groupmode="layer" transform="translate(0,-2.5390623e-6)">

    <g id="date_row" transform="translate(56.692635,-10.629923)"><!--{{{-->
      <text id="date" x="517.32281" y="170.07976" sodipodi:linespacing="125%"
        style="font-size:14px;font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono Bold">
        <tspan sodipodi:role="line" id="tspan2987" x="517.32281" y="170.07976">${docdate.strftime(d_fmt)}</tspan>
      </text>
    </g><!--}}}-->

    <g id="customer_block"><!--{{{-->

      <text id="customer_name" x="116.04729" y="272.83566" sodipodi:linespacing="125%"
        style="font-size:14px;font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono Bold">
        <tspan sodipodi:role="line" id="tspan2991" x="116.04729" y="272.83566">${customer_name[:60]}</tspan>
      </text>

      % if customer_domicilio is not UNDEFINED:
      <text id="customer_domicilio" x="115.95647" y="288.2659" sodipodi:linespacing="125%"
        style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono">
        <tspan sodipodi:role="line" id="tspan2995" x="115.95647" y="288.2659">${customer_domicilio[:60]}</tspan>
      </text>
      % endif

      % if customer_localidad is not UNDEFINED:
      <text id="customer_localidad" x="116.11468" y="301.48019" sodipodi:linespacing="125%"
        style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono">
        <tspan sodipodi:role="line" id="tspan2999" x="116.11468" y="301.48019">${customer_localidad[:60]}</tspan>
      </text>
      % endif

      <text id="cuit_info" x="537.72821" y="272.83566" sodipodi:linespacing="125%"
        style="font-size:14px;font-style:normal;font-variant:normal;font-weight:bold;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono Bold">
        <tspan sodipodi:role="line" id="tspan3003" x="537.72821" y="272.83566">${customer_cuit}</tspan>
      </text>

      <text id="resp_iva" x="572.86145" y="291.37109" sodipodi:linespacing="125%"
        style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono">
        <tspan sodipodi:role="line" id="tspan3007" x="572.86145" y="291.37109">${customer_resp_name}</tspan>
      </text>

    </g><!--}}}-->

    <!--{{{ TODO
    <text
       xml:space="preserve"
       style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono"
       x="532.02338"
       y="288.64566"
       id="text3009"
       sodipodi:linespacing="125%"><tspan
         sodipodi:role="line"
         id="tspan3011"
         x="532.02338"
         y="288.64566"
         style="font-size:12px;font-weight:normal;-inkscape-font-specification:Nobix DejaVu Sans Mono"><tspan
   style="font-size:12px;font-weight:bold;-inkscape-font-specification:Nobix DejaVu Sans Mono Bold"
   id="tspan3013">OC Nº:</tspan> 001-0040328</tspan></text>
    <text
       xml:space="preserve"
       style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono"
       x="531.49603"
       y="307.18109"
       id="text3009-7"
       sodipodi:linespacing="125%"><tspan
         sodipodi:role="line"
         id="tspan3011-8"
         x="531.49603"
         y="307.18109"
         style="font-size:12px;font-weight:normal;-inkscape-font-specification:Nobix DejaVu Sans Mono"><tspan
   style="font-size:12px;font-weight:bold;-inkscape-font-specification:Nobix DejaVu Sans Mono Bold"
   id="tspan3013-9">Factura Nº:</tspan> 001-0040328</tspan></text>
    <text
       xml:space="preserve"
       style="font-size:12px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-indent:0;text-align:start;text-decoration:none;line-height:125%;letter-spacing:0px;word-spacing:normal;text-transform:none;direction:ltr;block-progression:tb;writing-mode:lr-tb;text-anchor:start;baseline-shift:baseline;color:#000000;fill:#000000;fill-opacity:1;fill-rule:evenodd;stroke:none;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate;font-family:Nobix DejaVu Sans Mono;-inkscape-font-specification:Nobix DejaVu Sans Mono"
       x="106.29921"
       y="315.18109"
       id="text3039"
       sodipodi:linespacing="125%"><tspan
         sodipodi:role="line"
         id="tspan3041"
         x="106.29921"
         y="315.18109">Cuenta Corriente a 15 días</tspan></text>
  }}}-->

    <g id="document_items">
    % for count, item in enumerate(items):
      ${render_item(count, item)}
    % endfor
    </g>  
  </g>
</svg>
<!-- vim:foldenable:foldmethod=marker:ft=xml.mako:sw=2
-->
