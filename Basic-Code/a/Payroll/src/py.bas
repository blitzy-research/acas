#include "ipycomm"

prgname$="PY  JAN. 08,1980 "
rem---------------------------------------------------------
rem            This prog calls QSORT
rem	  P A Y R O L L
rem
rem	  P  Y
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------
function.name$="PROGRAM SELECTION"
program$="PY"

rem----- initialize disc directories -------------------------
initialize
rem----- console -----------------------------------------
console
rem----- set up chaining ---------------------------------
#include "ipychain"
REM--------------------------------------------------
REM----- LOCAL DATA FROM EXTERNAL SOURCE FILES ------
REM--------------------------------------------------
#include "ipyconst"
#include "ipystat"
REM
REM--------------------------------------------------------
REM----- GLOBAL DATA FOR ALL PAYROLL SYSTEM PROGRAMS ------
REM--------------------------------------------------------
REM
#include "zconst"
REM
REM-------------------------------------------------------------
REM----- MORE GLOBAL DATA FOR ALL PAYROLL SYSTEM PROGRAMS ------
REM-------------------------------------------------------------
if pr1.bell.suppressed% then bell$= null$ \
			else bell$= chr$(7)

    hrs.file%=03:hrs.len%=32:	   hrs.name$="PYHRS"
    emp.file%=04:emp.len%=701:	   emp.name$="PYEMP"
    his.file%=05:his.len%=480:	   his.name$="PYHIS"
    pay.file%=06:pay.len%=51:	   pay.name$="PYPAY"
    pyo.file%=07:pyo.len%=pay.len%:pyo.name$="PYPAY"   rem output
    chk.file%=08:chk.len%=165:	   chk.name$="PYCHK"
    ckh.file%=09:ckh.len%=165:	   ckh.name$="PYCKH"
    cho.file%=10:cho.len%=ckh.len%:cho.name$="PYCKH"   rem output
    coh.file%=11:		   coh.name$="PYCOH"
    act.file%=12:act.len%=43:	   act.name$="PYACT"
    ded.file%=13:		   ded.name$="PYDED"
    pr1.file%=14:		   pr1.name$="PYPR1"
    pr2.file%=15:		   pr2.name$="PYPR2"
    swt.file%=16:		   swt.name$="PYSWT"    rem +STATE$
    lwt.file%=18:		   lwt.name$="PYLWT"
    cal.file%=19:		   cal.name$="PYCAL"    rem +S,M,H,X
    gld.file%=17:gld.len%=51

REM
REM-----------------------
REM----- LOCAL DATA ------
REM-----------------------
REM
submit.file% = 1
end$= chr$(0)+ chr$(24H)

selections% =	     27
default.parameters%= 10
parameter.entry%=    09
user.prog%=	     27
fld.reset.date%= 08
fld.selection%=selections%+ 1
fld.get.date% =selections%+ 2
fld.error%    =selections%+ 3
fld.parent%   =selections%+ 4
lit.co.name%	  = 32
lit.common.date%  = lit.co.name%+ 2
lit.select.offset%= lit.co.name%+ 3
lit.user.prog%	  = lit.select.offset%+ user.prog%
lit.selection%	  = lit.select.offset%+ selections%+ 1
lit.get.date%	  = lit.select.offset%+ selections%+ 2
lit.error%	  = lit.select.offset%+ selections%+ 3
lit.startup%	  = lit.select.offset%+ selections%+ 4
lit.no.pr1%	  = lit.select.offset%+ selections%+ 5
lit.no.pr2%	  = lit.select.offset%+ selections%+ 6
lit.parent%	  = lit.select.offset%+ selections%+ 7

dim module$(selections%), exception%(selections%)
module$(01)="hrsent"                            rem these tables are
module$(02)="hrsproof"                          rem in arbitrary program
module$(03)="pyhours"   : exception%(03)= 1     rem number order. the
module$(04)="apply1"                            rem module table contains
module$(05)="pyjourn"                           rem program module names
module$(06)="pychecks"                          rem for chaining purposes
module$(07)="pyrgstr"                           rem the exception table
module$(08)=""                                  rem contains the number
module$(09)="pyparent"                          rem to be used in an on gosub
module$(10)="pyparent"  : exception%(10)= 2
module$(11)="pyactent"                          rem for any exception procesing
module$(12)="dedent"                            rem sorts are such an exception
module$(13)="pysrtprm"
module$(14)="pyupdhis"
module$(15)="print941"
module$(16)="pyperend"  : exception%(16)= 3
module$(17)="printw2"
module$(18)="print940"
module$(19)="pyperend"  : exception%(19)= 4
module$(20)="empprint"
module$(21)="hisprint"
module$(22)="vacprint"
module$(23)="pyactprt"
module$(24)="empent"
module$(25)="empdent"
module$(26)="ratent"
module$(27)=""

dim emsg$(20)
emsg$(01)="PY101  ONE OF THE TWO PARAMETER ENTRY OPTIONS MUST BE SELECTED"
emsg$(02)="PY102  DMS ERROR"
emsg$(03)="PY103  ERROR DURING CHAIN TO SORT"
emsg$(04)="PY104  ERROR DURING CHAIN TO SORT"
emsg$(05)="PY105  THE PROGRAM IS NOT ON THE CURRENTLY LOGGED DISK"
emsg$(06)="PY106  THE SORT PARAMETER FILE IS NOT ON THE SYSTEM DISK"
emsg$(07)="PY107  UNABLE TO OPEN PARAMETER FILE"
emsg$(08)="PY108"
emsg$(09)="PY109  YES, NO  AND STOP ARE THE ONLY ACCEPTABLE ENTRIES"
emsg$(10)="PY110  INVALID SECOND PARAMETER FILE"
emsg$(11)="PY111  QSORT IS NOT ON THE CURRENTLY LOGGED DISK"
emsg$(12)="PY112  THAT'S NOT A VALID RESPONSE"
emsg$(13)="PY113"
emsg$(14)="PY114  THE SYSTEM DRIVE HAS NOT BEEN INITIALIZED"
emsg$(15)="PY115  INVALID DATE"
emsg$(16)="PY116  INVALID PARAMETER FILE"
emsg$(17)="PY117  OPERATOR REQUESTED RETURN TO MENU"
emsg$(18)="PY118  **ERROR**  THE PROGRAM WAS TERMINATED BEFORE COMPLETION"
emsg$(19)="PY119  THE PARAMETER ENTRY PROGRAM IS NOT ON THE PROGRAM DISK"
emsg$(20)="IY120"

REM
REM--------------------------------------------------------------------
REM----- PARAMETER DEFAULTS SET UP ONLY IF NOT CHAINED FROM ROOT ------
REM--------------------------------------------------------------------
REM
def fn.set.up.pr1.defaults%
    pr1.max.chk.cats%=16
    pr1.max.dist.accts%=5
    pr1.max.sys.eds%=5
    pr1.max.emp.eds%=3
    pr1.max.ed.cats%=50
    pr1.void.check.amt=5000.00
    pr1.max.swt.entries%=15
    pr1.date.mo%=1:pr1.date.dy%=2:pr1.date.yr%=3
    pr1.lo.ded.chk.cat%=9
    pr1.hi.ded.chk.cat%=16
    pr1.lo.earn.chk.cat%=2
    pr1.hi.earn.chk.cat%=7
    pr1.console.width.poke.addr%= 272
    pr1.leading.crlf%= true%
RETURN
fend

REM
REM---------------------------------------------------------------
REM----- DMS CONSTANTS SET UP ONLY IF NOT CHAINED FROM ROOT ------
REM---------------------------------------------------------------
REM
def fn.set.up.dms.constants%
#include "zdmscnst"

RETURN
fend

REM
REM-------------------------
REM----- SERIAL NUMBER -----
REM-------------------------
#include "zserial"
REM
REM-----------------------------------------
REM----- INCLUDED FUNCTION DEFINITIONS -----
REM-----------------------------------------
REM
#include "zfilconv"
#include "znumber"
#include "zparse"
#include "zstring"
#include "zdateio"
#include "zeditdte"
#include "zsysdriv"

REM----- DMS FUNCTION DEFINITIONS ------
#include "zdmssca"
#include "zdmsinit"
#include "zdmsmsg"
#include "zdmsemsg"
#include "zdmslit"
#include "zdmsput"
#include "zdmsptal"
#include "zdmsget"
#include "zdmsclr"
#include "zdmsused"
#include "zdmsbrt"

REM
REM---------------------------------------
REM----- LOCAL FUNCTION DEFINITIONS  -----
REM---------------------------------------
def fn.get.pr2.drive%
	if size(fn.file.name.out$(system$+"PR2","101",1,password$,params$)) \
		then fn.get.pr2.drive%= 1 :RETURN
	if size(fn.file.name.out$(system$+"PR2","101",2,password$,params$)) \
		then fn.get.pr2.drive%= 2 :RETURN
	fn.get.pr2.drive%=-1 :RETURN
fend

REM
REM------------------------------------------
REM----- PROGRAM EXECUTION STARTS HERE ------
REM------------------------------------------
REM
while not chained.from.root% and not once.thru%
	REM---------------------------------------------------------------
	REM----- THIS IS THE FIRST OF TWO BLOCKS OF CODE WHICH WILL  -----
	REM----- BE EXECUTED EXACTLY ONCE IF NOT CHAINED FROM ROOT.  -----
	REM----- THIS BLOCK INITIALIZES THE DMS SYSTEM AND READS THE -----
	REM----- TWO PARAMETER FILES IF PRESENT.		     -----
	REM---------------------------------------------------------------
	print:print:print
	print tab(15);system.name$;version$;"     SERIAL NUMBER: ";serial.number$
	print
	print tab(10);cpyrght$
	print:print
	trash%= fn.set.up.dms.constants%
	trash%= fn.set.up.pr1.defaults%
	crt.init%=fn.crt.initialize%("CRT", null$)
	if crt.init% = 2 \
		then trash%=fn.emsg%(02): goto 999.1
	REM----- GET PR1 FILE, SET COMMON DRIVE ------
	gosub 101
	REM----- GET PR2 FILE, SET PR2 DRIVE IF NO PR2 ------
	gosub 102
	if error% then trash%= fn.emsg%(msg%): goto 999.1

	if pr1.leading.crlf% then poke pr1.console.width.poke.addr%, 255 \
			     else poke pr1.console.width.poke.addr%, 0

	if pr1.bell.suppressed% then bell$=null$ \
				else bell$=chr$(7)

	if fn.edit.date%(command$) \
		then common.date$=fn.date.in$

	once.thru%= true%
wend

REM
REM-------------------------------------------
REM----- INCLUDE SCREEN DEFINITION CODE ------
REM-------------------------------------------
REM
#include "fpymenu"


REM
REM----------------------------------------
REM----- DISPLAY PAYROLL MENU SCREEN ------
REM----------------------------------------
if pr1.user.program.used% \
	then crt.data$(lit.user.prog%)= "27.  "+pr1.user.prog.desc$: \
	     trash%= fn.set.used%(true%, lit.user.prog%): \
	     module$(user.prog%)=pr1.user.program$

if common.date$= null$ \
	then trash%=fn.set.used%(false%, lit.common.date%)
trash%= fn.put.all%(false%)


while not chained.from.root%
	REM----------------------------------------------------------------
	REM----- CODE EXECUTED EXACTLY ONCE IF NOT CHAINED FROM ROOT ------
	REM----- FORCE PARAMETER ENTRY SELECTION IF EITHER OR BOTH   ------
	REM----- PARAMETER FILES ARE NOT PRESENT.		     ------
	REM----------------------------------------------------------------
	chained.from.root%=true%
	chained%=true%

	if common.drive%= -1 and pr2.drive%= -1 \
		then common.chaining.status$= startup$: \
		     trash%=fn.lit%(lit.startup%): \
		     need.parent%= true%

	if common.drive%= -1 and pr2.drive%<>-1 \
		then common.chaining.status$= rebuild.pr1$: \
		     common.drive%= pr2.drive%: \
		     trash%=fn.lit%(lit.no.pr1%): \
		     need.parent%= true%

	if common.drive%<> -1 and pr2.drive%= -1 \
		then common.chaining.status$= rebuild.pr2$: \
		     trash%=fn.lit%(lit.no.pr2%): \
		     need.parent%= true%
	while need.parent%
		REM------------------------------------------------------
		REM----- ONE OR BOTH PARAMETER FILES ARE MISSING    -----
		REM----- USER MUST CHAIN TO PARAMETER ENTRY OR STOP -----
		REM------------------------------------------------------
		trash%= fn.lit%(lit.parent%)
		chained.program.number%= parameter.entry%
		gosub 60
		chained.program.number%= default.parameters%
		gosub 60
		got%= false%
		while not got%
		    trash%= fn.get%(1, fld.parent%)
		    if in.status%= req.stopit% then 999.2
		    selection%= val(in$)
		    if selection%= parameter.entry% or \
		       selection%= default.parameters% \
			then got%= true%: \
			else trash%= fn.emsg%(01)
		wend
		chain.to$=fn.file.name.out$(module$(selection%),"INT", \
		    cur.log.drive%,password$,param$)
		if size(chain.to$)= 0 \
			then trash%=fn.emsg%(19): goto 999.1
		if selection%= parameter.entry% \
			then chained.program.number%= default.parameters% \
			else chained.program.number%= parameter.entry%
		gosub 65
		chained.program.number%= selection%
		gosub 60
		if selection%= default.parameters% \
			then common.chaining.status$= \
			     common.chaining.status$+ default$
		REM----- EXIT HERE IF PARAMETER ENTRY CALLED ------
		chain chain.to$
	wend
	REM
	REM----- GET COMMON DATE IF NOT ENTERED ON COMMAND LINE ------
	REM
	if common.date$= null$ \
		then gosub 70
	if stopit% then 999.2

wend

REM
REM--------------------------------------------------
REM----- FOLLOWING MENU SET UP, EXECUTION WILL ------
REM----- CONTINUE HERE IF CHAINED FROM ROOT    ------
REM--------------------------------------------------
REM
if chained.program.number% > 0 \
	then  gosub 60			rem display program returned from

REM----- PICK UP AN ERROR RETURN ------
if common.return.code%= 1 \
	then gosub 90		rem get user to record message number

REM
REM-----------------------------------------------
REM----- SET UP FOR NORMAL PROGRAM SELECTION -----
REM-----------------------------------------------
REM
trash%= fn.lit%(lit.selection%)

REM
REM-------------------------------
10 REM----- MAIN DRIVER LOOP -----
REM-------------------------------
while true%
	trash%=fn.clr%(fld.selection%)
	trash%=fn.get%(1, fld.selection%)
	gosub 65		rem clear data
	if in.status%=req.stopit%  then 999	rem end of program

	num%=fn.num%(in$)
	if not num%  then \
		trash%=fn.emsg%(12): goto 10
	selected%=val(in$)
	if selected%= fld.reset.date% \
		then trash%= fn.clr%(lit.selection%): \
		     gosub 70: \		rem get system date
		     trash%= fn.lit%(lit.selection%): \
		     goto  10
	if selected% < 1  or selected% > selections% \
	   or (selected%= user.prog% and not pr1.user.program.used%) \
		then trash%=fn.emsg%(12): goto 10
	that.cant.run%=false%
	common.return.code%=0
	chained.program.number%=selected%
	common.msg$=null$
	common.chaining.status$=normal$
	gosub 60		rem display selection

	REM----- any exception processing takes place here ---------------

	if exception%(chained.program.number%) then \
		on exception%(chained.program.number%)	gosub \
		1001, \ 	--- sort hours batch
		 301,	\	--- set default flag in common
		 302,	\	--- set quarter end flag in common
		 303		rem set year end flag in common

	if that.cant.run%  then \
		trash%=fn.emsg%(msg%): goto 10

	REM----- chain ----------------------------------------
	chain.to$=fn.file.name.out$(module$(chained.program.number%),"INT", \
	0,password$,params$)
	if size(chain.to$)<> 0 then \
		chain chain.to$

	trash%=fn.emsg%(05)
	gosub 65	rem clear data
wend

999    rem-----normal end of job---------------
print using "&";crt.clear$
print:print:print
print tab(10);function.name$+" COMPLETED"
print:print:print
stop
999.1  rem-----abnormal end of job-------------
print:print:print
print tab(10);system.name$+" TERMINATING"
print:print:print:print bell$
stop
999.2  rem-----premature end of job------------
print using "&";crt.clear$
print:print:print
print tab(10);system.name$+" ENDING AT OPERATORS REQUEST"
print:print:print
stop

REM
REM------------------------
REM----- SUBROUTINES ------
REM------------------------
REM
REM---------------------------------
60 REM----- DISLAY A SELECTION -----
REM---------------------------------
trash%=fn.set.brt%(true%, lit.select.offset%+ chained.program.number%)
trash%=fn.lit%(lit.select.offset%+ chained.program.number%)
trash%=fn.put%(">",chained.program.number%)
RETURN
REM
REM-------------------------
65 REM----- CLEAR DATA -----
REM-------------------------
if chained.program.number% > 0 \
  then trash%=fn.set.brt%(false%,lit.select.offset%+chained.program.number%):\
       trash%=fn.lit%(lit.select.offset%+ chained.program.number%): \
       trash%=fn.clr%(chained.program.number%): \
       chained.program.number%= 0
RETURN
REM
REM----------------------------
 70 REM----- SET SYSTEM DATE ------
REM----------------------------
REM
trash%= fn.lit%(lit.get.date%)
ok%= false%
while not ok%
	trash%=fn.get%(1, fld.get.date%)
	if in.status%= req.stopit% then stopit%= true%: ok%= true%
	if in.status%= req.cr% and common.date$<> null$ then ok%= true%
	if in.status%= req.valid% and fn.edit.date%(in$) \
	    then common.date$= fn.date.in$: ok%= true%: \
		 trash%= fn.put%(fn.date.out$(common.date$), lit.common.date%)
	if ok%	then trash%=fn.clr%(lit.get.date%) \
		else trash%= fn.emsg%(15): \
		     trash%= fn.clr%(fld.date%)
wend
RETURN
REM
REM------------------------------------------
90 REM----- GET ERROR CODE CONFIRMATION -----
REM------------------------------------------
read%=false%
trash%=fn.lit%(lit.error%)
while not read%
	if common.msg$=null$ \
		then trash%=fn.emsg%(18) \
		else trash%=fn.msg%(bell$+common.msg$)

	trash%=fn.get%(0, fld.error%)
	if in.uc$="OK" \
		then read%=true%
wend
trash%=fn.clr%(lit.error%)
RETURN

REM
REM-----------------------------------
101 REM----- GET PARAMETER FILE ------
REM-----------------------------------
REM
dim pr1.rate.name$(4)

common.drive%= fn.get.sys.drive%
if common.drive%= -1 then RETURN

trash%= fn.msg%("LOADING FIRST PARAMETER FILE")

if end #pr1.file%  then 101.38	rem no parameter file
open  fn.file.name.out$(system$+"PR1","101",common.drive%,password$,param$) \
	as pr1.file%

if end #pr1.file%  then 101.39	rem invalid parameter file
read #pr1.file%; \
#include "ipypr1"

close pr1.file%
RETURN

101.38 REM------ NO PARAMETER FILE -------------
msg%=07
error%= true%
RETURN

101.39 REM----- INVALID PARAMETER FILE --------------
msg%=16
error%= true%
RETURN

REM
REM-------------------------
 102 REM----- GET PR2 FILE ------
REM-------------------------
REM
if common.drive%= -1 \
	then pr2.drive%= fn.get.pr2.drive% \
	else pr2.drive%= common.drive%

if pr2.drive%= -1 then RETURN

trash%= fn.msg%("LOADING SECOND PARAMETER FILE")

if end #pr2.file%  then 102.28	rem no pr2 file
open  fn.file.name.out$(system$+"PR2","101",pr2.drive%,password$,params$) \
	as pr2.file%
if end #pr2.file%  then 102.29	rem invalid pr2.file
read #pr2.file%; \
#include "ipypr2"

close pr2.file%
RETURN

102.28 REM------ NO PR2 FILE BUT PR1 FILE IS PRESENT -------------
pr2.drive%= -1
trash%= fn.msg%("NO SECOND PARAMETER FILE FOUND")
RETURN
102.29 REM----- INVALID PR2 FILE --------------------
msg%=10
error%= true%
RETURN

REM
REM--------------------------------------------
 301 REM----- SET DEFAULT FLAG IN COMMON ------
REM--------------------------------------------
REM
common.chaining.status$= common.chaining.status$+default$
RETURN

REM
REM------------------------------------------------
 302 REM----- SET QUARTER END FLAG IN COMMON ------
REM------------------------------------------------
REM
common.chaining.status$= common.chaining.status$+quarter.end$
RETURN

REM
REM-----------------------------------------------
 303 REM----- SET YEAR END FLAG IN COMMON   ------
REM-----------------------------------------------
REM
common.chaining.status$= common.chaining.status$+year.end$
RETURN


REM
REM-----------------------------------
REM----- SORTS ARE HANDLED HERE ------
REM-----------------------------------
REM
REM---------------------------------------
1001 REM----- SORT HOURS BATCH FILE ------
REM---------------------------------------
sort.param$=module$(chained.program.number%)
gosub 9000		rem should exit thru this subroutine
that.cant.run%=true%
RETURN
REM
REM------------------------------------------------------
9000 REM----- SORTS SHOULD EXIT THRU THIS ROUTINE   -----
REM----- WHICH BUILDS A COMMAND FILE AND STOPS ----------
REM------------------------------------------------------
REM
if size(fn.file.name.out$("QSORT","COM",0,password$,params$))= 0  then \
	msg%=11: RETURN
if size(fn.file.name.out$(sort.param$,"SRT",common.drive%,password$,params$)) \
	= 0  then \
	msg%=06 : RETURN

REM----- CREATE COMMAND FILE -----
if end #submit.file%  then 9090
create fn.file.name.out$("$$$","SUB", 1,password$,params$) \
	recl 80H  as submit.file%
run.menu$ = "CRUN2 "+system$+" " + fn.date.out$(common.date$)

REM----- PRINT TO COMMAND FILE -----
if end #submit.file%  then 9091
print using "&"; #submit.file% ; chr$(len(run.menu$)) + run.menu$ + end$

srt$ = "QSORT " + \
    fn.file.name.out$(sort.param$,"SRT",common.drive%,password$,params$)

print using "&";#submit.file% ; chr$(len(srt$)) + srt$ + end$
close submit.file%
print using "&"; crt.clear$
stop

9090 rem----- here if eof on submit file create -----------------
msg%=03
RETURN
9091 rem----- here if eof on submit file build -----------------
msg%=04
close submit.file%
RETURN
