#include "ipycomm"
prgname$="PYPAR2   21-DEC-79"
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
' function.name$="DEFAULT EMPLOYEE DATA"
program$="PYPAR2"
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
fields%=22
lit.common.date%= 25
dim tmp.rate.name$(4)
dim emsg$(30)
emsg$(01)="PY311  PROGRAM MUST BE SELECTED FROM THE PARAMETER ENTRY MENU"
emsg$(02)="PY311  ONLY INTEGERS ARE ACCEPTED AT THIS FIELD"
emsg$(03)="PY313  THAT'S NOT AN ACCEPTABLE NUMERIC FORMAT FOR THIS FIELD"
emsg$(04)="PY314  DOUBLE QUOTES ARE INVALID CHARACTERS"
emsg$(05)="PY315  Y  AND  N  ARE THE ONLY ACCEPTABLE ENTRIES AT THIS FIELD"
emsg$(06)="PY316  THAT'S NOT A VALID DATE"
emsg$(07)="PY317  THAT'S NOT AN ACCEPTABLE ENTRY FOR THIS FIELD"
emsg$(08)="PY318  THAT'S NOT IN THE ACCEPTABLE RANGE FOR THIS FIELD"
emsg$(09)="PY319  THAT'S NOT A VALID PAYROLL SYSTEM ACCOUNT"
emsg$(10)="PY320"
emsg$(11)="PY321"
emsg$(12)="PY322  UNABLE TO UPDATE PARAMETER FILE AT END OF PROGRAM"
emsg$(13)="PY323  UNABLE TO UPDATE SECOND PARAMETER FILE AT END OF PROGRAM"
emsg$(14)="PY324  THAT'S NOT A VALID PAY INTERVAL"
emsg$(15)="PY325"
emsg$(16)="PY326"
emsg$(17)="PY327"
emsg$(18)="PY328"
emsg$(19)="PY329"
emsg$(20)="PY330"

REM
REM------------------------------------------
REM----- INCLUDED FUNCTION DEFINITIONS ------
REM------------------------------------------
REM
#include "zfilconv"
#include "znumeric"
#include "zstring"
#include "zparse"
#include "zdateio"
#include "zeditdte"
#include "zdspyorn"

REM
REM-----------------------
REM----- DMS SYSTEM ------
REM-----------------------

#include "zdms"
#include "zdmsused"
#include "zdmstest"


REM
REM-------------------------------------------
REM------ PROGRAM EXECUTION STARTS HERE ------
REM-------------------------------------------
REM
if not chained.from.root%  or \
  match(in.parent$, common.chaining.status$,1)= 0 \
	then trash%=fn.emsg%(01): \
		goto 999.1

if match(startup$, common.chaining.status$, 1)<> 0 \
	then system.startup%= true%
if match(rebuild.pr2$, common.chaining.status$, 1)<> 0 \
	then rebuilding.pr2%= true%

REM
REM----- SAVE PR1 AND PR2 VALUES ------
REM
tmp.s.used%	       =pr1.s.used%
tmp.last.day.of.last.s$=pr2.last.day.of.last.s$
tmp.m.used%	       =pr1.m.used%
tmp.last.day.of.last.m$=pr2.last.day.of.last.m$
tmp.b.used%	       =pr1.b.used%
tmp.last.day.of.last.b$=pr2.last.day.of.last.b$
tmp.w.used%	       =pr1.w.used%
tmp.last.day.of.last.w$=pr2.last.day.of.last.w$
tmp.default.vac.rate   =pr1.default.vac.rate
tmp.default.sl.rate    =pr1.default.sl.rate
for f%= 1 to 4
    tmp.rate.name$(f%)	=pr1.rate.name$(f%)
next f%
tmp.default.pay.rate   =pr1.default.pay.rate
tmp.rate2.factor       =pr1.rate2.factor
tmp.rate3.factor       =pr1.rate3.factor
tmp.rate4.exclusion.type%=pr1.rate4.exclusion.type%
tmp.default.pay.interval$=pr1.default.pay.interval$
tmp.default.hs.type$   =pr1.default.hs.type$
tmp.max.pay.factor     =pr1.max.pay.factor
tmp.default.norm.units =pr1.default.norm.units
REM
REM--------------------------
REM----- SCREEN SET UP ------
REM--------------------------
REM
#include "fpypar2"

REM
REM--------------------------
REM----- DISPLAY SCREEN ------
REM--------------------------
REM
if system.startup% \
	then trash%= fn.set.used%(false%, lit.common.date%)

trash%= fn.put.all%(false%)

REM
REM------------------------------------
REM----- DISPLAY EXISTING VALUES ------
REM------------------------------------
REM
	gosub 101
	gosub 102
	gosub 103
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
	gosub 116
	gosub 117
	gosub 118
	gosub 119
	gosub 120
	gosub 121
	gosub 122

REM
REM------------------------------
REM----- MAIN INPUT DRIVER ------
REM------------------------------
REM
	field% = 1	rem start input driver at first field

while true%
	REM------------------------------------------------
 20	REM----- LOOP UNTIL STOP OR CANCEL REQUESTED ------
	REM------------------------------------------------
	trash%= fn.get%(3, field%)
	trash%= fn.msg%(null$)	     rem erase old error message
	ok% = true%		     rem set flag that response is valid

	if in.status% = req.cancel%	\
		then gosub 60: \--- restore pr1 values
		     goto 999.2 rem exit without updating file

	if in.status% = req.stopit%	\
		then goto 900	rem do final consistancy check and exit

	if in.status% = req.cr% or in.status% = req.back%	\
		then goto 22	rem get next field

	on field% gosub 	\ rem pick data checker by field
		201,	\
		202,	\
		203,	\
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
		219,	\
		220,	\
		221,	\
		222

	if not ok%  then trash%= fn.emsg%(msg%): \
		     goto 20	rem if answer not okay re-enter same field
	REM
	REM---------------------------
 22	REM----- GET NEXT FIELD ------
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
 60 REM----- RESTORE PR1 VALUES ------
REM
pr1.s.used%	       =tmp.s.used%
pr2.last.day.of.last.s$=tmp.last.day.of.last.s$
pr1.m.used%	       =tmp.m.used%
pr2.last.day.of.last.m$=tmp.last.day.of.last.m$
pr1.b.used%	       =tmp.b.used%
pr2.last.day.of.last.b$=tmp.last.day.of.last.b$
pr1.w.used%	       =tmp.w.used%
pr2.last.day.of.last.w$=tmp.last.day.of.last.w$
pr1.default.vac.rate   =tmp.default.vac.rate
pr1.default.sl.rate    =tmp.default.sl.rate
for f%= 1 to 4
    pr1.rate.name$(f%)	=tmp.rate.name$(f%)
next f%
pr1.default.pay.rate   =tmp.default.pay.rate
pr1.rate2.factor       =tmp.rate2.factor
pr1.rate3.factor       =tmp.rate3.factor
pr1.rate4.exclusion.type%=tmp.rate4.exclusion.type%
pr1.default.pay.interval$=tmp.default.pay.interval$
pr1.default.hs.type$   =tmp.default.hs.type$
pr1.max.pay.factor     =tmp.max.pay.factor
pr1.default.norm.units	     =tmp.default.norm.units
RETURN

REM
REM-------------------------------------
REM----- DATA DISPLAY SUBROUTINES ------
REM-------------------------------------
REM
 101 REM----- SEMI MONTHLY USED------
REM
trash%= fn.put%(fn.dsp.yorn$(pr1.s.used%), 1)
RETURN
REM
 102 REM----- LAST SEMI-MONTH END ------
REM
trash%= fn.put%(fn.date.out$(pr2.last.day.of.last.s$), 2)
RETURN
REM
 103 REM----- MONTHLY USED ------
REM
trash%= fn.put%(fn.dsp.yorn$(pr1.m.used%), 3)
RETURN
REM
 104 REM----- LAST MONTH END ------
REM
trash%= fn.put%(fn.date.out$(pr2.last.day.of.last.m$), 4)
RETURN
REM
 105 REM----- BIWEEKLY USED ------
REM
trash%= fn.put%(fn.dsp.yorn$(pr1.b.used%), 5)
RETURN
REM
REM
 106 REM----- LAST BIWEEK END ------
REM
trash%= fn.put%(fn.date.out$(pr2.last.day.of.last.b$), 6)
RETURN
 107 REM----- WEEKLY USED ------
REM
trash%= fn.put%(fn.dsp.yorn$(pr1.w.used%), 7)
RETURN
REM
 108 REM----- LAST WEEK END ------
REM
trash%= fn.put%(fn.date.out$(pr2.last.day.of.last.w$), 8)
RETURN
REM
 109 REM----- VACATION RATE ------
REM
trash%= fn.put%(str$(pr1.default.vac.rate), 9)
RETURN
REM
 110 REM----- SICK LEAVE RATE ------
REM
trash%= fn.put%(str$(pr1.default.sl.rate), 10)
RETURN
REM
 111 REM----- RATE 1 NAME  ------
REM
trash%= fn.put%(pr1.rate.name$(1), 11)
RETURN
REM
 112 REM----- DEFAULT RATE 1 ------
REM
trash%= fn.put%(str$(pr1.default.pay.rate), 12)
RETURN
REM
 113 REM----- RATE 2 NAME  ------
REM
trash%= fn.put%(pr1.rate.name$(2), 13)
RETURN
REM
 114 REM----- RATE 2 FACTOR ------
REM
trash%= fn.put%(str$(pr1.rate2.factor), 14)
RETURN
REM
 115 REM----- RATE 3 NAME  ------
REM
trash%= fn.put%(pr1.rate.name$(3), 15)
RETURN
REM
 116 REM----- RATE 3 FACTOR ------
REM
trash%= fn.put%(str$(pr1.rate3.factor), 16)
RETURN
REM
 117 REM----- RATE 4 NAME  ------
REM
trash%= fn.put%(pr1.rate.name$(4), 17)
RETURN
REM
 118 REM----- RATE 4 EXCLUSION TYPE ------
REM
trash%= fn.put%(str$(pr1.rate4.exclusion.type%), 18)
RETURN
REM
 119 REM----- DEFAULT PAY INTERVAL ------
REM
trash%= fn.put%(pr1.default.pay.interval$, 19)
RETURN
REM
 120 REM----- DEFAULT PAY TYPE ------
REM
trash%= fn.put%(pr1.default.hs.type$, 20)
RETURN
REM
 121 REM----- MAX PAY FACTOR ------
REM
trash%= fn.put%(str$(pr1.max.pay.factor), 21)
RETURN
REM
 122 REM----- NORMAL UNITS ------
REM
trash%= fn.put%(str$(pr1.default.norm.units), 22)
RETURN
REM
REM---------------------------------------------------
REM----- SINGLE FIELD DATA CHECKING SUBROUTINES ------
REM---------------------------------------------------
REM
REM
 201 REM----- SEMI MONTHLY USED------
REM
gosub 320
if ok% then pr1.s.used%= bool.val%
gosub 101
RETURN
REM
 202 REM----- LAST SEMI-MONTH END ------
REM
gosub 360
if ok% then pr2.last.day.of.last.s$= fn.date.in$
gosub 102
RETURN
REM
 203 REM----- MONTHLY USED ------
REM
gosub 320
if ok% then pr1.m.used%= bool.val%
gosub 103
RETURN
REM
 204 REM----- LAST MONTH END ------
REM
gosub 360
if ok% then pr2.last.day.of.last.m$= fn.date.in$
gosub 104
RETURN
REM
 205 REM----- BIWEEKLY USED ------
REM
gosub 320
if ok% then pr1.b.used%= bool.val%
gosub 105
RETURN
REM
REM
 206 REM----- LAST BIWEEK END ------
REM
gosub 360
if ok% then pr2.last.day.of.last.b$= fn.date.in$
gosub 106
RETURN
 207 REM----- WEEKLY USED ------
REM
gosub 320
if ok% then pr1.w.used%= bool.val%
gosub 107
RETURN
REM
 208 REM----- LAST WEEK END ------
REM
gosub 360
if ok% then pr2.last.day.of.last.w$= fn.date.in$
gosub 108
RETURN
REM
 209 REM----- VACATION RATE ------
REM
gosub 300
if ok% then pr1.default.vac.rate= val(in$)
gosub 109
RETURN
REM
 210 REM----- SICK LEAVE RATE ------
REM
gosub 300
if ok% then pr1.default.sl.rate= val(in$)
gosub 110
RETURN
REM
 211 REM----- RATE 1 NAME  ------
REM
gosub 350
if ok% then pr1.rate.name$(1)= in$
gosub 111
RETURN
REM
 212 REM----- DEFAULT RATE 1 ------
REM
gosub 300
if ok% then pr1.default.pay.rate= val(in$)
gosub 112
RETURN
REM
 213 REM----- RATE 2 NAME  ------
REM
gosub 350
if ok% then pr1.rate.name$(2)= in$
gosub 113
RETURN
REM
 214 REM----- RATE 2 FACTOR ------
REM
gosub 300
if ok% then pr1.rate2.factor= val(in$)
gosub 114
RETURN
REM
 215 REM----- RATE 3 NAME  ------
REM
gosub 350
if ok% then pr1.rate.name$(3)= in$
gosub 115
RETURN
REM
 216 REM----- RATE 3 FACTOR ------
REM
gosub 300
if ok% then pr1.rate3.factor= val(in$)
gosub 116
RETURN
REM
 217 REM----- RATE 4 NAME  ------
REM
gosub 350
if ok% then pr1.rate.name$(4)= in$
gosub 117
RETURN
REM
 218 REM----- RATE 4 EXCLUSION TYPE ------
REM
gosub 370
if ok% and val(in$)> 0 and val(in$)<5 \
	then ok%= true%: pr1.rate4.exclusion.type%= val(in$) \
	else ok%= false%: msg%= 8
RETURN
REM
 219 REM----- DEFAULT PAY INTERVAL ------
REM
if match(in.uc$, "SMBW", 1)= 0 \
	then msg%= 14: ok%= false% \
	else ok%= true%: pr1.default.pay.interval$= in.uc$
gosub 119
RETURN
REM
 220 REM----- DEFAULT PAY TYPE ------
REM
if match(in.uc$, "HS", 1)= 0 \
	then msg%= 14: ok%= false% \
	else ok%= true%: pr1.default.hs.type$= in.uc$
gosub 120
RETURN
REM
 221 REM----- MAX PAY FACTOR ------
REM
gosub 300
if ok% then pr1.max.pay.factor= val(in$)
gosub 121
RETURN
REM
 222 REM----- NORMAL UNITS ------
REM
gosub 300
if ok% then pr1.default.norm.units= val(in$)
gosub 122
RETURN

REM
REM----------------------------------------------
REM----- GENERAL DATA CHECKING SUBROUTINES ------
REM----------------------------------------------
REM----------------------------------------------
REM
REM----------------------------------------------
REM----- FN.NUMERIC(IN$, 5, 2)-------------------
REM----------------------------------------------
REM
 300
	ok% = fn.numeric%(in$,5,2)
	if not ok%	\
	   then msg%= 3
	RETURN

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
REM-----------------------------
REM----- CHECK VALID DATE ------
REM-----------------------------
REM
 360
	ok%= fn.edit.date%(in$)
	if not ok% then msg%= 6
	RETURN
REM
REM-------------------
REM----- FN.NUM ------
REM-------------------
REM
 370
	ok% = fn.num%(in$)
	if not ok%	\
	   then msg%= 2
	RETURN

REM
  REM---------------------------------------------------
   REM-----	  NORMAL END OF JOB		   ------
900 REM----- OPEN WRITE TO AND CLOSE PARAMETER FILE ------
   REM---------------------------------------------------
REM
trash%= fn.msg%("STOP REQUESTED")

if end #pr1.file% then 1002
open fn.file.name.out$(pr1.name$,"101",common.drive%,password$,params$) \
	 as pr1.file%
print #pr1.file% ;	\
#include "ipypr1"
close pr1.file%

REM
REM-------------------------------------------------------------------
REM----- IF BUILDING NEW PR2 FILE THEN ADJUST LAST APPLY NUMBER ------
REM-------------------------------------------------------------------
REM
if (system.startup% or rebuilding.pr2%) and \
	(pr1.m.used% and pr1.s.used%) \
	then gosub 2001
if (system.startup% or rebuilding.pr2%) and \
	(pr1.b.used% and pr1.w.used%) \
	then gosub 2002

if end #pr2.file% then 1003
open fn.file.name.out$(pr2.name$,"101",common.drive%,password$,params$) \
	 as pr2.file%
print #pr2.file% ;	\
#include "ipypr2"
close pr2.file%

trash%=fn.msg%(function.name$+" COMPLETED")
common.return.code%=0
goto 999.3

REM
REM-------------------------------
REM----- PROGRAM EXITS HERE ------
REM-------------------------------
REM
999.1  REM----- ERROR EXIT   RETURN TO MENU ------
trash%=fn.msg%(bell$+program$+" COMPLETED UNSUCCESSFULLY")
common.return.code%=1
if chained.from.root% \
	then	chain system$ \
	else	stop

999.2  REM----- OPERATOR REQUESTED EXIT -------
trash%=fn.msg%("THE PARAMETER FILE WILL NOT BE CHANGED")
common.return.code%=2
REM
   REM----------------------------
999.3  REM----- NORMAL EXIT ------
   REM----------------------------
REM
chain system$+"parent"

REM
REM---------------------------------------------
REM----- ABNORMAL EOJ FROM MAIN LINE CODE ------
REM---------------------------------------------
REM
REM-----------------------------------------------------------
REM----- PARAMETER FILE NOT FOUND AT EOJ, SO ERROR EXIT ------
REM-----------------------------------------------------------
REM
 1002
	trash%= fn.emsg%(12)
	goto 999.1
REM
REM------------------------------------------------------------------
REM----- SECOND PARAMETER FILE NOT FOUND AT EOJ, SO ERROR EXIT ------
REM------------------------------------------------------------------
REM
 1003
	trash%= fn.emsg%(13)
	goto 999.1

REM
REM----------------------------------------------------------------
 2001 REM----- ADJUST LAST APPLY NUMBER SO THAT SLOW APPLIES ------
      REM----- ( MONTHLY ) WILL BE EVEN NUMBERED	     ------
REM----------------------------------------------------------------
REM
if pr2.last.day.of.last.s$> pr2.last.day.of.last.m$ \
	then pr2.last.sm.apply.no%= 1 \
	else pr2.last.sm.apply.no%= 0
RETURN

REM
REM----------------------------------------------------------------
 2002 REM----- ADJUST LAST APPLY NUMBER SO THAT SLOW APPLIES ------
      REM----- ( BI-WEEKLY ) WILL BE EVEN NUMBERED	     ------
REM----------------------------------------------------------------
REM
if pr2.last.day.of.last.w$> pr2.last.day.of.last.b$ \
	then pr2.last.wb.apply.no%= 1 \
	else pr2.last.wb.apply.no%= 0
RETURN
