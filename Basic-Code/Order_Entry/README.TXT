README.TXT

This code as far as I remember has NOT been tested as there are some routines
that are not installed regarding Stock control and possibly others.

This code is for the Order Entry sub system used in conjunction with the
original ACAS accounting system. The compiler used was CBASIC in a CPM/MPM
platform.

The copyright and usage notices as used within the ACAS system, applies to OE.

It was written before the internet was available, to support orders received
via the post, telephone, fax and telex.

Somewhere there is/was code that was rewritten for another compiler and later
into Cobol but I cannot find any such code nor any documentation so you will
have to use the Basic code as such.

See the other README.TXT file in the top level folder for more information.

There are hooks to access a Cobol F.H. see later via the generated C code for
many of the files used in OE but note that within OE it does use a drive letter
as in a floppy drive, and this element should be removed so that just the
current active directory is used.

If you decide to use a Basic compiler such as the Free Basic Compiler, you will
need to make a number of changes to this code to match with what the FBC
accepts. In addition, in order to use the data within the ACAS system such as
Stock Control, Invoicing etc, you should make use of the FH (File Handler)
modules found in the common source directory as these are converted to C code
by the Cobol compiler, which can be read from most Basic compiled programs.

To do so, read the Cobol manual gnucobpg-a4.pdf and in Chapter 11.8.1 onwards
and 11.8.5 and also look at document GnuCOBOL_C_Interaction.pdf both of which
are in the next higher folder.

Another option is to just convert these programs to Cobol and again use the
F.H modules that in turn will call a DAL (Data Access Layer) module that will
process any Mysql or Mariadb database tables. Note that there is one FH and one
DAL for each Cobol ISAM (Indexed Sequential) file used in ACAS v3.02 onwards.

In addition there is a Cobol version of oe in the oe folder and this came from
a Tandy implementation that looks as if it was not released - well, testing
found lots of bugs at least using the gnucobol compiler. In addition there was
missing programs that I have written to add functionality to support the testing
at least. The idea was to consider adding oe into ACAS but it is short of
support for payments and the only additional function it had was some support
for Back Orders but this has now been fully implemented into ACAS within stock
control and Sales invoicing - so I have dropped that idea and all work has now
stopped but it does work within the system testing I conducted but not covered
all use cases.

Good luck.

Vincent Coen
August 2023    - first version.
September / October 2025 - Updated.
Hatfield, UK
vbcoen@gmail.com

