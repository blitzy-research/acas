README.TXT

This note applies to all products provided under the 'Basic-Code' base.
It includes :

NAD         - Name and address system

Order Entry - Basic OE system in use in the late 70's before the internet
              where orders are taken over the telephone.

IY          - Original Inventory  / Stock Control from around 1979/80.
              The (ACAS) Cobol version is Stock Control that made use of
              very few of the design elements from this version.

NAD           Name and address application as some of the include files are
              the same as used in IY, Payroll you might want to migrate this
              first - but check code between systems just in case.

Payroll     - Designed for the American market. Due to the design of tables
              for deductions and additions etc it can be used today with
              some tweaks but will still need work for today's USA standards.
              This product was never used for ACAS as it was totally rewritten
              for the UK market but that version has not been released as
              Open Source due to the maintenance requirements over any time
              period to match in with UK taxation requirements etc.

The code for these Basic applications is written to use CBASIC in on CPM.
The copyright and usage notices as used within the ACAS system, applies
to all these supplied. There is needless to say, no guarantees that it will
do as specified or documented but should do.

Documentation : These are supplied in the original format for the WP used at
the time, needless to say the WP is no longer available but used one under
CPM and MPM. Note that only the Payroll system has a manual set available and
is included under the doc folder. The other three do not as I cannot find them.
These have been updated using LibreOffice to create both a new source file and
a .pdf file both named as Provisional Payroll Manual.odt and .pdf.

If you decide to use a Basic compiler such as the Free Basic Compiler you will
need to make a number of changes to this code to match with what the FBC
accepts.

You should start with the include files that are small blocks of common code
that is used in all of the source files. Having converted them over, start
with the largest sources by size of file along with a notebook to record code
that needs changes and record said changes. After a while you should be able to
make up some automatic replace scripts depending on the text editor you are
using as this will cut down on the amount of time required for these changes
but it will not cover all the changes required.

Some of these source files includes usage of files where the path is specified
including a drive letter such as 'B:/' etc these need to be removed so it work
with the current directory, at least initially.
Most of this work has now been done and all source files changed to lower case
and like wise where seen, the sources have also been changed to use lower case
except the program names which are still as upper case to make them more
readable.

You should not have any other logic changes for the first pass of code changes.
Save such for pass two including that for replacing/removing the drive
specifiers etc.  Ignore any bugs you might spot other than that directly relate
to the program BUT I would recommend just making notes in the source code and
only do so once the complete code sets compiles cleanly first.
You should make notes on paper etc, of possible needed changes for pass two.

Payroll also has code in for security features including inserted a serial
number for the released version as a executable and you should consider
remarking all that out.

Avoid changes for the sake of them - if it is not needed skip it - saves time.
One area that might need changing is the paragraph / label names - Basic usually
uses numbers only but CBASIC allows for letters as well an example is 1170E1.
This is valid for CBASIC but might not be for FBC. Changing it but remember to
check for any occurrence else where in the code for its use. The same apples for
include code that uses them which will affect multiple sources and no I have not
spotted this in the includes but I did have a very quick pass through them.

In addition, in order to use the data within the ACAS system such as
IRS or General, Invoicing etc, you should make use of the FH (File Handler)
modules found in the common source directory as these are converted to C code
which can be read from most Basic compiled programs not not checked with FBC.

Another option is to just convert these programs to Cobol and again use the
F.H modules that in turn will call a DAL (Data Access Layer) module that will
process any Mysql or Mariadb database tables. Note that there is one FH and one
DAL for each Cobol ISAM (Indexed Sequential) file used in ACAS v3.2 onwards.

The copyright notices still apply, in that Applewood Computers and myself, so
remains as the holders but it is available to use by anyone for their own usage.

For commercial use, contact me using the email address below with your proposed
plans and requirements.

Good luck.

Vincent Coen
Written - August 2023.
Updated - September/October 2025 - Very minor changes.
Hatfield, UK
vbcoen@gmail.com
