This peace of Software mainly helps to interprete several different description formats for can-communication.
Some of these formats can be written also. There is some outdated german Documentation at [http://eduard-broecker.de/Software/canmatrix.html](my personal homepage)

As a sideeffect, this software helps to convert between can-matrix-description formats.
You can for example convert a autosar system description (.arxml) to an candb++ - File (.dbc).

Therefor this software includes a "Python Can Matrix Object" which describes the can-communication and the needed objects (Boardunits, Frames, Signals, Values, ...)

There are some import- and some export-functions for this object.

supported file formats for import:
* .dbc (candb / [Vector](vector.com))
* .dbf ([Busmaster](https://rbei-etas.github.io/busmaster/) (open source!))
* .kcd ([kayak](http://kayak.2codeornot2code.org/) (open source!))
* .arxml ([autosar](autosar.org) system description)
* .yaml (dump of the python object)
* .xls(x) (excel xls-import, works with .xls-file generated by this lib)
* .sym ([peak](http://www.peak-system.com) pcan can description)
 
supported file formats for export:
 * .dbc 
 * .dbf
 * .kcd
 * .xls(x)
 * .json
 * .arxml (very basic implementation)
 * yaml (dump of the python object)
 * sym

***

 xlwt and xlrd for .xls-support is included this is from [http://www.python-excel.org/]
 xlsxwriter is for xlsx-export-support [https://github.com/jmcnamara/XlsxWriter]

***

There is an example included to generate Busmaster Simulation out of canmatrix-Object. 

***

Fileformats:
* dbc: there are 2 commandline-options for dbc-files:

  --dbcCharset=CHARSET

	set charset for dbc-file

  --dbcCommentCharset=CHARSET

	set charset for comments in dbc-file 
	
***
Requirements for use:
* You need lxml library for arxml- and kcd-support. 
* You need yaml library for yaml-support

On windows I use "active python" and installed lxml-package from active python
 
./convert.py some-matrix.dbc some-matrix.dbf

./convert.py some-matrix.arxml some-matrix.dbc

***


Have Fun,
feel free to contact me for any suggestions
Eduard

