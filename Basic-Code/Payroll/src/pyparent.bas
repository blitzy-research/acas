#include "ipycomm"
prgname$="PYPARENT   20-DEC-79"
REM----------------------------------------------------------------------
REM		PAYROLL   SYSTEM
REM		P A R A M E T E R
REM
REM		    E N T R Y
REM
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------
function.name$="PARAMETER ENTRY"
program$="PYPARENT"
REM
REM-------------------------------------
REM----- INCLUDED DATA STRUCTURES ------
REM-------------------------------------
#include "ipyconst"
#include "ipystat"

REM
REM----------------------------------
REM----- LOCAL DATA STRUCTURES ------
REM----------------------------------
REM
null$= ""
fields%=	   19			rem standard input fields
fld.selection%=    20
fld.sys.drive%=    22
fld.get.date%=	   21
lit.co.name%=	   23
lit.sys.name%=	   24
lit.todays.date%=  25
lit.fn.name%=	   26
lit.last.default%= 39
lit.last.mod%=	   40
lit.select1%=	   41
lit.select2%=	   42
lit.select3%=	   43
lit.get.selection%= 44
lit.get.date%=	   45
lit.sys.drive%=    46
lit.building.pr1%= 47
lit.building.pr2%= 48

dim interval$(4)
interval$(1)="SEMI-MONTHLY"
interval$(2)="MONTHLY"
interval$(3)="BIWEEKLY"
interval$(4)="WEEKLY"
dim tmp.interval%(4)

dim emsg$(20)
emsg$(01)="PY281  PROGRAM MUST BE SELECTED FROM THE PAYROLL MENU"
emsg$(02)="PY281  ONLY INTEGERS ARE ACCEPTED AT THIS FIELD"
emsg$(03)="PY283  THAT'S NOT AN ACCEPTABLE NUMERIC FORMAT FOR THIS FIELD"
emsg$(04)="PY284  DOUBLE QUOTES ARE INVALID CHARACTERS"
emsg$(05)="PY285  Y  AND  N  ARE THE ONLY ACCEPTABLE ENTRIES AT THIS FIELD"
emsg$(06)="PY286  THAT'S NOT A VALID DATE"
emsg$(07)="PY287  THAT'S NOT AN ACCEPTABLE ENTRY FOR THIS FIELD"
emsg$(08)="PY288  THAT'S NOT IN THE ACCEPTABLE RANGE FOR THIS FIELD"
emsg$(09)="PY289  THAT'S NOT A VALID PAYROLL SYSTEM ACCOUNT"
emsg$(10)="PY290  THE ACCOUNT ENTRY MODULE IS NOT ON THE PROGRAM DISK"
emsg$(11)="PY291  THAT PARAMETER ENTRY MODULE IS NOT ON THE PROGRAM DISK"
emsg$(12)="PY292  UNABLE TO UPDATE PARAMETER FILE AT END OF PROGRAM"
emsg$(13)="PY293  UNABLE TO UPDATE SECOND PARAMETER FILE AT END OF PROGRAM"
emsg$(14)="PY294  THAT'S NOT A VALID PAY INTERVAL"
emsg$(15)="PY295  COULDN'T CREATE THE PARAMETER FILE"
emsg$(16)="PY296  COULDN'T WRITE TO THE PARAMETER FILE"
emsg$(17)="PY297  COULDN'T CREATE THE SECOND PARAMETER FILE"
emsg$(18)="PY298  COULDN'T WRITE TO THE SECOND PARAMETER FILE"
emsg$(19)="PY299"
emsg$(20)="PY300  THE SYSTEM DRIVE MUST BE  A  OR  B"

REM
REM------------------------------------------
REM----- INCLUDED FUNCTION DEFINITIONS ------
REM------------------------------------------
REM
#include "zfilconv"
#include "znumeric"
#include "zstring"
#include "zparse"
#include "zeditdte"
#include "zdateio"
#include "zdspyorn"

REM
REM-----------------------
REM----- DMS SYSTEM ------
REM-----------------------

#include "zdms"
#include "zdmstest"
#include "zdmsused"
#include "zdmsclr"
#include "zdmsrst"


REM
REM-------------------------------------------
REM------ PROGRAM EXECUTION STARTS HERE ------
REM-------------------------------------------
REM
if not chained.from.root%	\
	then trash%=fn.emsg%(01): \
		goto 999.1

REM
REM--------------------------
REM----- SCREEN SET UP ------
REM--------------------------
REM
#include "fpypar"

trash%= fn.reset%
trash%= fn.lit%(lit.co.name%)
trash%= fn.lit%(lit.sys.name%)
if match(normal$, common.chaining.status$, 1)<> 0 \
	then trash%= fn.lit%(lit.todays.date%)
trash%= fn.lit%(lit.fn.name%)

REM
REM-----------------------------------------
REM----- CHECK FOR SYSTEM STARTUP FLAG -----
REM----- SET PARAMETER ENTRY FLAG      -----
REM-----------------------------------------
REM
first.time.thru%= false%
system.startup%=  false%
defaults.only%=   false%
rebuilding.pr1%=  false%
rebuilding.pr2%=  false%
if match(in.parent$, common.chaining.status$, 1)= 0 \
	then first.time.thru%= true%: \
	     common.chaining.status$= common.chaining.status$+ in.parent$
if match(default$, common.chaining.status$, 1)<> 0 and first.time.thru% \
	then defaults.only%= true%
if match(startup$, common.chaining.status$, 1)<> 0 and first.time.thru% \
	then system.startup%= true%
if match(rebuild.pr1$, common.chaining.status$, 1)<> 0 and first.time.thru% \
	then rebuilding.pr1%= true%
if match(rebuild.pr2$, common.chaining.status$, 1)<> 0 and first.time.thru% \
	then rebuilding.pr2%= true%

if system.startup% and not defaults.only% \
	then gosub 2000 			rem get system drive

if system.startup% and defaults.only% \
	then common.drive%= 2

if system.startup% or rebuilding.pr1% \
	then gosub 10100			rem build a default pr1
if error% then 999.1

if system.startup% or rebuilding.pr2% \
	then gosub 10200			rem build a default pr2
if error% then 999.1

if rebuilding.pr1% or rebuilding.pr2% or system.startup% \
	then trash%=fn.clr%(lit.building.pr1%): \
	     trash%=fn.clr%(lit.building.pr2%)

if defaults.only% then gosub 60: \	--- change company info
			goto 999


REM
REM-------------------------------
REM----- GET USER SELECTION ------
REM-------------------------------
REM
while true%
	trash%= fn.lit%(lit.select1%)
	trash%= fn.lit%(lit.select2%)
	trash%= fn.lit%(lit.select3%)
	trash%= fn.lit%(lit.get.selection%)
	no.reset.needed%= true%
	while no.reset.needed%
		trash%= fn.get%(1, fld.selection%)
		if in.status%= req.stopit% then 999
		user.selection%= val(in$)
		if user.selection%< 1  or  user.selection%> 3 \
			then trash%= fn.emsg%(08)
		if user.selection%= 2 or user.selection%= 3 \
			then gosub 20		rem select pypar2, pypar3
		if user.selection%= 1 \
		    then trash%= fn.clr%(lit.select1%): \
			 trash%= fn.clr%(lit.select2%): \
			 trash%= fn.clr%(lit.select3%): \
			 trash%= fn.clr%(lit.get.selection%): \
			 gosub 60: \	--- modify params, update pr1
			 no.reset.needed%= false%
		if error% then 999.1		rem error from update pr1
	wend
wend
REM----------------------------
 20 REM----- SELECT A SCREEN ------
REM----------------------------
if size(fn.file.name.out$(system$+"PAR"+in$,"INT", 0, password$,param$))=0\
	then trash%=fn.emsg%(11): RETURN
chain system$+"PAR"+in$
print "blooey": stop
REM
REM--------------------------------------------
 60 REM----- PARAMETER MODIFICATION LOOP ------
REM--------------------------------------------
REM----- SET UP TEMPORARY STORAGE ------
REM--------------------------------------
tmp.interval%(1)= pr1.s.used%
tmp.interval%(2)= pr1.m.used%
tmp.interval%(3)= pr1.b.used%
tmp.interval%(4)= pr1.w.used%
tmp.date.mo%= pr1.date.mo%
tmp.date.dy%= pr1.date.dy%
tmp.date.yr%= pr1.date.yr%
tmp.last.day.of.last.s$=pr2.last.day.of.last.s$
tmp.last.day.of.last.m$=pr2.last.day.of.last.m$
tmp.last.day.of.last.b$=pr2.last.day.of.last.b$
tmp.last.day.of.last.w$=pr2.last.day.of.last.w$
tmp.year%	 =pr2.year%
tmp.co.name$	 =pr1.co.name$
tmp.co.addr1$	 =pr1.co.addr1$
tmp.co.addr2$	 =pr1.co.addr2$
tmp.co.addr3$	 =pr1.co.addr3$
tmp.co.city$	 =pr1.co.city$
tmp.co.state$	 =pr1.co.state$
tmp.co.zip$	 =pr1.co.zip$
tmp.co.phone$	 =pr1.co.phone$
tmp.fed.id$	 =pr1.fed.id$
tmp.state.id$	 =pr1.state.id$
tmp.local.id$	 =pr1.local.id$
tmp.lines.per.page%=  pr1.lines.per.page%
tmp.bell.suppressed%= pr1.bell.suppressed%
tmp.debugging%	 =pr1.debugging%
tmp.leading.crlf%=pr1.leading.crlf%
REM
REM--------------------------
REM----- SET UP SCREEN ------
REM--------------------------
REM
for f%= lit.fn.name%+1 to lit.last.default%
	trash%= fn.lit%(f%)
next f%
if not defaults.only% \
	then for f%= lit.last.default%+1 to lit.last.mod%: \
		trash%= fn.lit%(f%): next f%
REM
REM------------------------------------
REM----- DISPLAY EXISTING VALUES ------
REM------------------------------------
REM
	gosub 101
	gosub 102
	gosub 103
	gosub 120
	gosub 104
	gosub 105
	gosub 106
	gosub 107
	gosub 108
	gosub 109
	gosub 110
	gosub 111
	gosub 112
	gosub 113
	gosub 114
	gosub 115
if not defaults.only% \
    then \
	gosub 116: \
	gosub 117: \
	gosub 118


REM
REM------------------------------------------------
REM----- MAIN INPUT DRIVER FOR PR1 FILE MODS ------
REM------------------------------------------------
REM
field% = 1	rem start input driver at first field

while true%
	REM------------------------------------------------
 65	REM----- LOOP UNTIL STOP OR CANCEL REQUESTED ------
	REM------------------------------------------------
	trash%= fn.get%(3, field%)
	ok% = true%		     rem set flag that response is valid

	if in.status% = req.cancel%	\
		then gosub 69:	\	--- restore pr1 values
		     gosub 68: \	--- restore screen
		     RETURN
	if in.status% = req.stopit%	\
		then gosub 900: \	--- update pr1 file
		     gosub 68:	\	--- restore screen
		     RETURN
	if in.status% = req.cr% or in.status% = req.back%	\
		then goto 67	rem get next field

	on field%  gosub		\ rem pick data checker by field
		201,	\
		202,	\
		203,	\
		220,	\
		204,	\
		205,	\
		206,	\
		207,	\
		208,	\
		209,	\
		210,	\
		211,	\
		212,	\
		213,	\
		214,	\
		215,	\
		216,	\
		217,	\
		218,	\
		219
	if not ok%	\
		then trash%=fn.emsg%(msg%): \
		     goto 65	rem if answer not okay re-enter same field
	REM
	REM---------------------------
 67	REM----- GET NEXT FIELD ------
	REM---------------------------
	REM
	selected%= false%
	while not selected%
		if in.status%= req.cr% or in.status%= req.valid% \
			then field%=field%+ 1 \
			else field%=field%- 1
		if field%> fields%  then field%= 1
		if field%< 1	    then field%= fields%
		if fn.test%(crt.used%, field%) then selected%= true%
	wend
wend
REM
REM---------------------------
 68 REM----- RESTORE SCREEN ------
REM---------------------------
REM
if defaults.only% then RETURN		rem no need to reset if not using menu

for f%= lit.fn.name%+1 to lit.last.mod%
	trash%= fn.clr%(f%)
next f%
for f%= 1 to fields%
	trash%= fn.set.used%(false%, f%)
next f%
RETURN

REM
REM------------------------------
 69 REM----- HERE IF CANCELLED ------
REM------------------------------
REM
trash%= fn.msg%("CHANGES CANCELLED")
pr1.s.used% =tmp.interval%(1)
pr1.m.used% =tmp.interval%(2)
pr1.b.used% =tmp.interval%(3)
pr1.w.used% =tmp.interval%(4)
pr1.date.mo%= tmp.date.mo%
pr1.date.dy%= tmp.date.dy%
pr1.date.yr%= tmp.date.yr%
pr2.last.day.of.last.s$=tmp.last.day.of.last.s$
pr2.last.day.of.last.m$=tmp.last.day.of.last.m$
pr2.last.day.of.last.b$=tmp.last.day.of.last.b$
pr2.last.day.of.last.w$=tmp.last.day.of.last.w$
pr2.year%	 =tmp.year%
pr1.co.name$	 =tmp.co.name$
pr1.co.addr1$	 =tmp.co.addr1$
pr1.co.addr2$	 =tmp.co.addr2$
pr1.co.addr3$	 =tmp.co.addr3$
pr1.co.city$	 =tmp.co.city$
pr1.co.state$	 =tmp.co.state$
pr1.co.zip$	 =tmp.co.zip$
pr1.co.phone$	 =tmp.co.phone$
pr1.fed.id$	 =tmp.fed.id$
pr1.state.id$	 =tmp.state.id$
pr1.local.id$	 =tmp.local.id$
pr1.lines.per.page%=  tmp.lines.per.page%
pr1.bell.suppressed%= tmp.bell.suppressed%
pr1.debugging%	 =tmp.debugging%
pr1.leading.crlf%=tmp.leading.crlf%
RETURN

REM
REM--------------------------------------
REM----- FIELD DISPLAY SUBROUTINES ------
REM--------------------------------------
REM
 101 REM----- PAY INTERVAL ------
REM
if pr1.s.used% then interval%= 1		rem interval is a global flag
if pr1.m.used% then interval%= 2
if pr1.b.used% then interval%= 3
if pr1.w.used% then interval%= 4
if (pr1.s.used%+ pr1.m.used%+ pr1.b.used%+ pr1.w.used%)<> -1 \
	then interval%= 0
trash%=fn.put%(interval$(interval%), 1)
RETURN
REM
 102 REM----- DATE FORM ------
REM
trash%=fn.put%(str$(pr1.date.mo%), 2)
RETURN
REM
 103 REM----- ENDING DAY OF LAST PERIOD ------
REM
if interval%= 0 then RETURN
if interval%= 1 then out.date$= fn.date.out$(pr2.last.day.of.last.s$)
if interval%= 2 then out.date$= fn.date.out$(pr2.last.day.of.last.m$)
if interval%= 3 then out.date$= fn.date.out$(pr2.last.day.of.last.b$)
if interval%= 4 then out.date$= fn.date.out$(pr2.last.day.of.last.w$)
trash%=fn.put%(out.date$, 3)
RETURN
REM
 104 REM----- CURRENT YEAR ------
REM
trash%=fn.put%(str$(pr2.year%), 5)
RETURN
REM
 105 REM----- COMPANY NAME ------
REM
trash%=fn.put%(pr1.co.name$, 6)
RETURN
REM
 106 REM----- COMPANY ADDRESS LINE 1 ------
REM
trash%=fn.put%(pr1.co.addr1$, 7)
RETURN
REM
 107 REM----- COMPANY ADDRESS LINE 2 ------
REM
trash%=fn.put%(pr1.co.addr2$, 8)
RETURN
REM
 108 REM----- COMPANY ADDRESS LINE 3 ------
trash%=fn.put%(pr1.co.addr3$, 9)
RETURN
REM
 109 REM----- COMPANY CITY ------
REM
trash%=fn.put%(pr1.co.city$, 10)
RETURN
REM
 110 REM----- COMPANY STATE ------
REM
trash%=fn.put%(pr1.co.state$, 11)
RETURN
REM
 111 REM----- COMPANY ZIP CODE ------
REM
trash%=fn.put%(pr1.co.zip$, 12)
RETURN
REM
 112 REM----- COMPANY PHONE NUMBER ------
REM
trash%=fn.put%(pr1.co.phone$, 13)
RETURN
REM
 113 REM----- COMPANY FEDERAL ID NUMBER ------
REM
trash%=fn.put%(pr1.fed.id$, 14)
RETURN
REM
 114 REM----- COMPANY STATE ID NUMBER ------
REM
trash%=fn.put%(pr1.state.id$, 15)
RETURN
REM
 115 REM----- COMPANY LOCAL ID NUMBER ------
REM
trash%=fn.put%(pr1.local.id$, 16)
RETURN
REM
 116 REM----- LINES PER PAGE ------
REM
trash%=fn.put%(str$(pr1.lines.per.page%), 17)
RETURN
REM
 117 REM----- SUPPRESS CONSOLE BELL ------
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.bell.suppressed%), 18)
RETURN
REM
 118 REM----- DEBUGGING ------
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.debugging%), 19)
RETURN
REM
 119 REM----- LEADING CRLF IN CBASIC ------
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.leading.crlf%), 20)
RETURN
REM
 120 REM----- LAST QUARTER ENDED ------
REM
trash%=fn.put%(str$(pr2.last.q.ended%), 04)
RETURN

REM
REM-------------------------------------
REM----- DATA EDIT SUBROUTINES ------
REM-------------------------------------
REM
 201 REM----- PAY INTERVAL ------
REM
old.interval%= interval%
interval%= match(in.uc$, "SMBW", 1)
if interval%<> 0 and in.len%= 1 \
	then ok%= true% \
	else ok%= false%: msg%= 14: interval%= old.interval%: \
	     gosub 101: RETURN
if interval%= 1 then pr1.s.used%= true%: pr1.default.pay.interval$= "S" \
		else pr1.s.used%= false%
if interval%= 2 then pr1.m.used%= true%: pr1.default.pay.interval$= "M" \
		else pr1.m.used%= false%
if interval%= 3 then pr1.b.used%= true%: pr1.default.pay.interval$= "B" \
		else pr1.b.used%= false%
if interval%= 4 then pr1.w.used%= true%: pr1.default.pay.interval$= "W" \
		else pr1.w.used%= false%
gosub 103
gosub 101
RETURN
REM
 202 REM----- DATE FORM ------
REM
if val(in$) < 1 or val(in$) > 2 \
   then ok%= false%: msg%= 8 \
   else ok%= true%: pr1.date.mo%= val(in$)
if pr1.date.mo%= 1 then pr1.date.dy%= 2 \
		   else pr1.date.dy%= 1
gosub 102
RETURN
REM
 203 REM----- ENDING DAY OF LAST PERIOD ------
REM
if fn.edit.date%(in$) \
	then ok%= true%: date$= fn.date.in$ \
	else ok%= false%: msg%= 6: gosub 104: RETURN

if interval%= 1 then pr2.last.day.of.last.s$= date$
if interval%= 2 then pr2.last.day.of.last.m$= date$
if interval%= 3 then pr2.last.day.of.last.b$= date$
if interval%= 4 then pr2.last.day.of.last.w$= date$
gosub 103
RETURN
REM
 204 REM----- CURRENT YEAR ------
REM
gosub 370      rem integer
if ok% then pr2.year%= val(in$)
gosub 104
RETURN
REM
 205 REM----- COMPANY NAME ------
REM
gosub 350		rem match quotes
if ok% then pr1.co.name$= in$
gosub 105
RETURN
REM
 206 REM----- COMPANY ADDRESS LINE 1 ------
REM
gosub 350
if ok% then pr1.co.addr1$= in$
gosub 106
RETURN
REM
 207 REM----- COMPANY ADDRESS LINE 2 ------
REM
gosub 350
if ok% then pr1.co.addr2$= in$
gosub 107
RETURN
REM
 208 REM----- COMPANY ADDRESS LINE 3 ------
REM
gosub 350
if ok% then pr1.co.addr3$= in$
gosub 108
RETURN
REM
 209 REM----- COMPANY CITY ------
REM
gosub 350
if ok% then pr1.co.city$= in$
gosub 109
RETURN
REM
 210 REM----- COMPANY STATE ------
REM
gosub 350
if ok% then pr1.co.state$= in.uc$
gosub 110
RETURN
REM
 211 REM----- COMPANY ZIP CODE ------
REM
gosub 350
if ok% then pr1.co.zip$= in$
gosub 111
RETURN
REM
 212 REM----- COMPANY PHONE NUMBER ------
REM
gosub 350
if ok% then pr1.co.phone$= in$
gosub 112
RETURN
REM
 213 REM----- COMPANY FEDERAL ID NUMBER ------
REM
gosub 350
if ok% then pr1.fed.id$= in$
gosub 113
RETURN
REM
 214 REM----- COMPANY STATE ID NUMBER ------
REM
gosub 350
if ok% then pr1.state.id$= in$
gosub 114
RETURN
REM
 215 REM----- COMPANY LOCAL ID NUMBER ------
REM
gosub 350
if ok% then pr1.local.id$= in$
gosub 115
RETURN
REM
 216 REM----- LINES PER PAGE ------
REM
gosub 370
if ok% then pr1.lines.per.page%= val(in$)
gosub 116
RETURN
REM
 217 REM----- SUPPRESS CONSOLE BELL ------
REM
gosub 320
if ok% then pr1.bell.suppressed%= bool.val%
gosub 117
RETURN
REM
 218 REM----- DEBUGGING ------
REM
gosub 320
if ok% then pr1.debugging%= bool.val%
gosub 118
RETURN
REM
 219 REM----- CBASIC VERSION PRIOR TO 2.05 -------
REM
gosub 320
if ok% then pr1.leading.crlf%= bool.val%
if pr1.leading.crlf% then poke pr1.console.width.poke.addr%,255 \
		     else poke pr1.console.width.poke.addr%,  0
gosub 119
RETURN
REM
 220 REM----- LAST QUARTER ENDED ------
REM
num%= val(in$)
if num%<= 4 and num%> 0 \
	then pr2.last.q.ended%= num% \
	else ok%= false%: msg%= 08
gosub 120
RETURN

REM
REM----------------------------------------------
REM----- GENERAL DATA CHECKING SUBROUTINES ------
REM----------------------------------------------
REM----------------------------------------------
REM
REM-----------------------------------------------
REM----- CHECK "Y" OR "N", RETURN BOOL.VAL% ------
REM-----------------------------------------------
REM
 320
	ok% = false%
	if in.uc$ = "Y" \
		then	\
			ok% = true%	:\
			bool.val% = true%
	if in.uc$ = "N" \
		then	\
			ok% = true%	:\
			bool.val% = false%
	if not ok%	\
	   then msg%= 5
	return
REM
REM------------------------------------
REM----- CHECK FOR DOUBLE QUOTES ------
REM------------------------------------
REM
 350
	if match(quote$, in$, 1)<> 0 \
		then ok%= false%: msg%= 4 \
		else ok%= true%
	RETURN
REM
REM-------------------
REM----- FN.NUM ------
REM-------------------
REM
 370
	ok% = fn.num%(in$)
	if not ok%	\
	   then msg%= 2: RETURN
	RETURN

REM
  REM---------------------------------------------------
   REM-----	  END OF DATA MODIFICATION	   ------
900 REM----- OPEN WRITE TO AND CLOSE PARAMETER FILE ------
   REM---------------------------------------------------
REM
trash%= fn.msg%("STOP REQUESTED")

if end #pr1.file% then 902
open fn.file.name.out$(pr1.name$,"101",common.drive%,password$,params$) \
	 as pr1.file%
print #pr1.file% ;	\
#include "ipypr1"
close pr1.file%

if end #pr2.file% then 903
open fn.file.name.out$(pr2.name$,"101",common.drive%,password$,params$) \
	 as pr2.file%
print #pr2.file% ;	\
#include "ipypr2"
close pr2.file%
RETURN
REM
REM-----------------------------------------------------------
REM----- PARAMETER FILE NOT FOUND AT EOJ, SO ERROR EXIT ------
REM-----------------------------------------------------------
REM
 902
trash%= fn.emsg%(12)
error%= true%
RETURN

REM
REM------------------------------------------------------------------
REM----- SECOND PARAMETER FILE NOT FOUND AT EOJ, SO ERROR EXIT ------
REM------------------------------------------------------------------
REM
 903
trash%= fn.emsg%(13)
error%= true%
RETURN

REM
 999 REM----- GET COMMON DATE IF NULL (ON SYSTEM STARTUP OR REBUILD PR1, PR2)
REM
while common.date$= null$
    trash%= fn.lit%(lit.get.date%)
    trash%= fn.get%(0, fld.get.date%)
    if fn.edit.date%(in$) \
	then common.date$= fn.date.in$ \
	else trash%=fn.emsg%(6)
wend
REM
REM-----------------------
REM----- NORMAL EOJ ------
REM-----------------------
REM
trash%=fn.msg%(function.name$+" COMPLETED")
common.return.code%=0
goto 999.3

REM
REM-------------------------------
REM----- PROGRAM EXITS HERE ------
REM-------------------------------
REM
999.1  REM----- ERROR EXIT   RETURN TO MENU ------
trash%=fn.msg%(bell$+function.name$+" COMPLETED UNSUCCESSFULLY")
common.return.code%=1
goto 999.3
999.2  REM----- OPERATOR REQUESTED EXIT -------
trash%=fn.msg%("THE PARAMETER FILE WILL NOT BE CHANGED")
common.return.code%=2
REM
   REM----------------------------
999.3  REM----- NORMAL EXIT ------
   REM----------------------------
REM
if match(startup$, common.chaining.status$, 1)= 0 or common.return.code%= 1 \
	then module$= system$ \
	else module$= system$+"actent"
chain.to$= fn.file.name.out$(module$, "INT", 0,pw$,pm$)\

if size(chain.to$)=0\
	then trash%=fn.emsg%(10): goto 999.1
chain chain.to$
print "blooey":stop

REM
REM---------------------------------------------
REM----- ABNORMAL EOJ FROM MAIN LINE CODE ------
REM---------------------------------------------

REM
REM----------------------------------------------
REM----- SUBROUTINES NOT USED BY MAIN LOOP ------
REM----------------------------------------------
REM
  REM----------------------------------
 2000 REM------ GET SYSTEM DRIVE ------
  REM----------------------------------
REM
trash%=fn.lit%(lit.sys.drive%)
if common.drive%< 0 then common.drive%= 2
trash%=fn.put%(fn.drive.out$(common.drive%), fld.sys.drive%)
drive.entered%= false%
while not drive.entered%
	trash%= fn.get%(2, fld.sys.drive%)
	if in.status%= req.stopit% \
		then trash%= fn.msg%(system.name$+" TERMINATING"): \
		     STOP
	if in.status%= req.valid% \
		then common.drive%= fn.drive.in%(in.uc$)
	if common.drive%< 1 or common.drive%> 2 or in.status%= req.back% \
		then trash%= fn.emsg%(20) \
		else drive.entered%= true%
wend
trash%= fn.clr%(fld.sys.drive%)
trash%= fn.clr%(lit.sys.drive%)
RETURN

REM
   REM--------------------------------------------
10100 REM----- BUILD DEFAULT PARAMETER FILE ------
   REM--------------------------------------------
REM
trash%= fn.lit%(lit.building.pr1%)
REM
REM----------------------------
REM----- SET UP DEFAULTS ------
REM----------------------------
pr1.debugging%=    false%
pr1.co.name$=	   "STRUCTURED SYSTEMS GROUP, INC."
pr1.co.addr1$=	   "5204 CLAREMONT AVENUE"
pr1.co.addr2$=	   null$
pr1.co.addr3$=	   null$
pr1.co.city$=	   "OAKLAND"
pr1.co.state$=	   "CA"
pr1.co.zip$=	   "94618"
pr1.co.phone$=	   "(415) 547-1567"
pr1.gld.drive%=    1
pr1.ded.drive%=    2
pr1.emp.drive%=    2
pr1.his.drive%=    2
pr1.hrs.drive%=    2
pr1.act.drive%=    2
pr1.glx.drive%=    2
pr1.chk.drive%=    2
pr1.tax.drive%=    2
pr1.pay.drive%=    2
pr1.pyo.drive%=    2
pr1.glx.drive%=    2
pr1.ckh.drive%=    2
pr1.coh.drive%=    2
pr1.cho.drive%=    2
pr1.offset.cash.acct%= 1
pr1.rate2.factor=  1.5
pr1.rate3.factor=  2.0
pr1.rate4.exclusion.type%= 1
pr1.rate.name$(1)= "REGULAR"
pr1.rate.name$(2)= "OVERTIME"
pr1.rate.name$(3)= "SPEC. OVERTIME"
pr1.rate.name$(4)= "COMMISSION"
pr1.min.wage=	   0
pr1.check.printing.used%= true%
pr1.bell.suppressed%= false%
pr1.s.used%=	   true%
pr1.m.used%=	   false%
pr1.w.used%=	   false%
pr1.b.used%=	   false%
pr1.chk.history.used%= false%
pr1.void.chks.over.max%= false%
pr1.leading.crlf%= pr1.leading.crlf%	rem set by menu driver
pr1.jc.used%=	   false%
pr1.gl.used%=	   false%
pr1.default.pay.interval$="S"
pr1.default.dist.acct%= 3
pr1.default.pay.rate= 1.0
pr1.gl.file.suffix$=  "SS"
pr1.default.norm.units= 1.0
pr1.default.hs.type$= "S"
pr1.max.pay.factor=   3.0
pr1.default.vac.rate= 0.42
pr1.default.sl.rate=  0.21
pr1.fed.id$=	 "FEDERAL ID"
pr1.state.id$=	 "STATE ID"
pr1.local.id$=	 "LOCAL ID"
pr1.date.dy%=	  2
pr1.date.mo%=	  1
pr1.date.yr%=	  3
pr1.lines.per.page%=  60
pr1.page.width%=      132
pr1.user.program.used%= false%
pr1.user.program$=    null$
pr1.user.prog.desc$=	null$
pr1.dist.used%= 	true%

REM
REM-----------------------------------
REM----- PARAMETER FILE CREATE	------
REM-----------------------------------
REM
if end #pr1.file% then 10105
create fn.file.name.out$(pr1.name$,"101",common.drive%,password$,params$) \
	 as pr1.file%
if end #pr1.file% then 10106
print #pr1.file% ;	\
#include "ipypr1"
close pr1.file%

RETURN

REM
10105 REM----- CAN'T CREATE PR1 ------
REM
trash%= fn.emsg%(15)
error%= true%
RETURN
REM
10106 REM----- CAN'T WRITE PR1 ------
REM
close pr1.file%
trash%= fn.emsg%(16)
error%= true%
RETURN

REM
   REM--------------------------------------------
10200 REM----- BUILD DEFAULT SECOND PARAMETER FILE ------
   REM--------------------------------------------
REM
trash%=fn.lit%(lit.building.pr2%)
REM
REM----------------------------
REM----- SET UP DEFAULTS ------
REM----------------------------
pr2.year%=		80
pr2.last.sm.apply.no%=	0
pr2.last.wb.apply.no%=	0
pr2.hrs.batch.no%=	0
pr2.last.day.of.last.w$="791231"
pr2.last.day.of.last.b$="791231"
pr2.last.day.of.last.s$="791231"
pr2.last.day.of.last.m$="791231"
pr2.940.printed%=	false%
pr2.941.printed%=	false%
pr2.w2.printed%=	false%
pr2.no.acts%=		4
pr2.no.active.emps%=	0
pr2.no.employees%=	0
pr2.check.date$=	"000000"
pr2.last.check.no$=	"00000"
pr2.last.q.ended%=	4
pr2.just.closed.year%=	true%

REM
REM-----------------------------------------
REM----- SECOND PARAMETER FILE CREATE ------
REM-----------------------------------------
if end #pr2.file% then 10207
create fn.file.name.out$(pr2.name$,"101",common.drive%,password$,params$) \
	 as pr2.file%
if end #pr2.file% then 10208
print #pr2.file% ;	\
#include "ipypr2"
close pr2.file%
RETURN
REM
10207 REM----- CAN'T CREATE PR2 ------
REM
trash%= fn.emsg%(17)
error%= true%
RETURN
REM
10208 REM----- CAN'T WRITE PR2 ------
REM
close pr2.file%
trash%= fn.emsg%(18)
error%= true%
RETURN
