README.TXT

This code is for the Payroll sub system that "could" possibly be used in
conjunction with the ACAS accounting system.

The compiler used was CBASIC in CPM & MPM platforms.
The copyright and usage notices as used within the ACAS system, applies Payroll.

This Payroll system is geared towards the American market and has NOT been
updated since around 1980/1. It was written for use with CPM and VDU
monitors/keyboard so will need to be changed to work with *nix systems such as
Linux.

In fact might require a fair bit of work !

If you decide to do so use use the Basic compiler - Free Basic Compiler it will
be needed to make a number of changes to this code to match with what the FBC
accepts.

You should start with the include files that are small blocks of common code
that is used in many of the source files. Having converted them over start with
the largest sources by size of file along with a notebook to record code that
needs changes and record said changes. After a while you should be able to make
up some automatic replace scripts depending on the text editor you are using as
this will cut down on the amount of time required for these changes but it will
not cover all the changes required.

Some of these source file includes usage of files where the path is specified
including a drive letter such as 'B:/' etc these need to be removed so it work
with the current directory, at least initially.

{
NOTES as of 7 October 2025:

1. I have changed all basic source files to lower case AND changed includes to
lower case and in a form that should be accepted by FBC.

2. Changed within program sources to use lower case when chaining to next
program but have left the internal name to upper.

3. Where spotted changed file names also to lower case.

4. All includes have been changed to NOT use drive letters.

5. When spotted done the same for file drive letters but I know I have missed
many.

But be warned I may have missed more /others so source needs to go through the
compiler to check.

For the manual : Looked at using the tex Text sources into a simple word
processing  document using LibreOffice Open Doc format which can be read by MS
word if using a modern one say dated from 2019 and no I have not checked as I
do not.  This is ongoing see file "Provisional Payroll Manual.pdf" &.odt.

}

In addition in order to use the data within the ACAS system such as
IRS or General, Invoicing etc, you should make use of the FH (File Handler)
modules found in the common source directory as these are converted to C code
which can be read from most Basic compiled programs.

Another option is to just convert these programs to Cobol and again use the
F.H modules that in turn will call a DAL (Data Access Layer) module that will
process any Mysql or Mariadb database tables. Note that there is one FH and one
DAL for each Cobol ISAM (Indexed Sequential) file used in ACAS v3.2 and onwards.

As of November 2025, I have started programming / coding for a Payroll system
written in Cobol for initially the USA market only. Possible additions are
Canada and the UK markets. Why?, well gives me something to do. You will need
to go to the ACAS-3.3/payroll folder to find the work in progress but be warned
The coding is not yet completed and there has only been minimal testing and that
for the payroll parameter and other system data entry programs.
As programs have been coded the payroll menu program has been updated to call
each one - again absolutely no testing as yet as coding is still continuing.
Note that Payroll does not use MySql or Mariadb Data Bases so only ISAM and
for parameter data etc, relative file processing.  If user would like that you
will need to get in touch regarding this although some tables have been designed
but are of course subject to change as coding develops.

The copyright notices still apply in that myself and Applewood Computers remain
as the holders but it is available to use by anyone for their own usage Only.
It cannot be rented, sold for any purpose without entering into an agreement
with myself - see email address to use to send your business proposals.

This applies to the whole of the ACAS system as well as all of the Basic code.

Good luck.

Vincent Coen
October 2025.
Hatfield, UK
vbcoen@gmail.com
