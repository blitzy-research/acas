README.TXT

This code is for the Inventory (stock control) sub system used in conjunction
with the ACAS accounting system at v1.0. The compiler used was CBASIC in a CPM
and MPM platform.
The copyright and usage notices as used within the ACAS system, applies to this
code base.

Note that this and all of the other systems were written to use CPM & MPM where
usage was via a computer monitor / keyboard connected to the system via a serial
cable and there could be a lot of different users using the system at the same
time running different applications. Therefore the software has modules that
helps control the different models of these devices from many brands. This will
need to be changed/replaced using direct access to display and keyboard, etc.

Elsewhere there is a newer version of Stock Control totally written into Cobol
and is part of the current ACAS system.

This version has been supplied for your interest anyway.

If you decide to use a Basic compiler such as the Free Basic Compiler, it will
be needed to make a number of changes to this code to match with what the FBC
accepts. In addition, in order to use the data within the ACAS system such as
Stock Control, Invoicing etc, you should make use of the FH (File Handler)
modules found in the common source directory as these are converted to C code
by the Cobol compiler, which can be read from most Basic compiled programs.

See the pdf documents at the next higher folder for use with interaction with
C programming and Cobol modules for more information.

Another option is to just use the ACAS Stock control system as it has more
functionality.


Good luck.

Vincent Coen
August 2023.
October 2025 - Updated.
Hatfield, UK
vbcoen@gmail.com
