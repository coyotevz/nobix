.. _user-tareas-documento:

==================
Crear un Documento
==================

Como crear un documento nuevo?

.. insertar lo siguiente en una nueva página

=================
Un poco de teoria
=================

Campos de texto
---------------

*Campo* se le denomina a una casilla editable en donde el sistema espera que
ingresemos algún tipo de información, esta puede ser el código de algún
artículo, una fecha, el nombre de un cliente, una cantidad, etc.

Existen distintos tipos de campos con distintas restricciones y
comportamientos.

**Tipos de campos:**

* Código de Vendedor

* Tipo de Documento

* Código de Artículo

* Código de Cliente

* Código de Proveedor

* Cantidad

* Descripción

* Fecha

* Nombre

Cada uno de los campos enumerados aquí arriba tiene distintas caracteristicas y
capacidades. Por ejemplo un campo del tipo fecha, no aceptará que ingresemos
una fecha inválida y tiene la capacidad de ingresar la fecha actual si
presionamos la tecla `H`, también tiene la capacidad de aumentar o disminuir
el día, el mes o el año en forma individual con distintas combinaciones de
teclas.

Ventanas de Busqueda
--------------------

Existen distinas ventanas de busqueda. Búsqueda de Articulos y Búsqueda de
Cliente/Proveedor

Búsqueda de Artículos
~~~~~~~~~~~~~~~~~~~~~

Para buscar un artículo nos situamos en un campo del tipo *Código de Artículo*
y presionamos alguna de las teclas de seleccion del criterio de busqueda.

Una vez seleccionado el articulo presionamos `Enter` y el artículo será agregado
al documento en edición.

Búsqueda de Cliente/Proveedor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

bla, bla, bla ...

Selección Múltiple de Artículos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

En ocaciones es útil poder agregar varios de los artículos que aparecen en la
ventana de busqueda de artículos de una sola pasada. En este caso existe la
posibilidad de seleccionar todos los artículos que deseamos agregar al
documento, para ello simplemente presionamos la tecla `Insert`
sobre los artículos que queremos agregar al documento, el artículo cambiará su
representación para demostrar el estado de selección, en caso de querer
deseleccionar un articulo ya marcado debemos volver a presionar la tecla
`Insert` sobre el artículo en cuestión. En definitiva, la tecla `Insert`
produce un cambio en el estado de selección de un artículo.

::

    Seleccionado    <------`Insert`------->    No Seleccionado

.. note::

    Es importante aclarar que en cuanto se encuentre un artículo seleccionado
    solo aquellos artículos seleccionados se agregarán al documento, esto
    quiere decir que en tal caso el artículo que se encuentre *enfocado* no se
    insertará, como en el caso de que no exista selección.
