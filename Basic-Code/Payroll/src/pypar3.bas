#include "ipycomm"
prgname$="PYPAR3   17-DEC-79"
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
function.name$="SYSTEM CONFIGURATION"
program$="PYPAR3"
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

dim emsg$(20)
emsg$(01)="PY331  PROGRAM MUST BE SELECTED FROM THE PARAMETER ENTRY MENU"
emsg$(02)="PY331  ONLY INTEGERS ARE ACCEPTED AT THIS FIELD"
emsg$(03)="PY333  THAT'S NOT AN ACCEPTABLE NUMERIC FORMAT FOR THIS FIELD"
emsg$(04)="PY334  DOUBLE QUOTES ARE INVALID CHARACTERS"
emsg$(05)="PY335  Y  AND  N  ARE THE ONLY ACCEPTABLE ENTRIES AT THIS FIELD"
emsg$(06)="PY336  THAT'S NOT A VALID DATE"
emsg$(07)="PY337  THAT'S NOT AN ACCEPTABLE ENTRY FOR THIS FIELD"
emsg$(08)="PY338  THAT'S NOT IN THE ACCEPTABLE RANGE FOR THIS FIELD"
emsg$(09)="PY339  THAT'S NOT A VALID PAYROLL SYSTEM ACCOUNT"
emsg$(10)="PY340"
emsg$(11)="PY341"
emsg$(12)="PY342  UNABLE TO UPDATE PARAMETER FILE AT END OF PROGRAM"
emsg$(13)="PY343"
emsg$(14)="PY344  THAT'S NOT A VALID DRIVE"
emsg$(15)="PY345"
emsg$(16)="PY346"
emsg$(17)="PY347"
emsg$(18)="PY348"
emsg$(19)="PY349"
emsg$(20)="PY350"

REM
REM------------------------------------------
REM----- INCLUDED FUNCTION DEFINITIONS ------
REM------------------------------------------
REM
#include "zfilconv"
#include "znumeric"
#include "zstring"
#include "zdateio"
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
if not chained.from.root% or match(in.parent$, common.chaining.status$, 1)=0 \
	then trash%=fn.emsg%(01): \
		goto 999.1

REM
REM----------------------------
REM----- SAVE PR1 VALUES ------
REM----------------------------
REM
tmp.tax.drive%= pr1.tax.drive%
tmp.ded.drive%= pr1.ded.drive%
tmp.coh.drive%= pr1.coh.drive%
tmp.act.drive%= pr1.act.drive%
tmp.emp.drive%= pr1.emp.drive%
tmp.his.drive%= pr1.his.drive%
tmp.hrs.drive%= pr1.hrs.drive%
tmp.chk.drive%= pr1.chk.drive%
tmp.pay.drive%= pr1.pay.drive%
tmp.pyo.drive%= pr1.pyo.drive%
tmp.gl.used%  = pr1.gl.used%
tmp.glx.drive%= pr1.glx.drive%
tmp.gl.file.suffix$	= pr1.gl.file.suffix$
tmp.gld.drive%= pr1.gld.drive%
tmp.user.program.used%	= pr1.user.program.used%
tmp.user.program$	= pr1.user.program$
tmp.user.prog.desc$	= pr1.user.prog.desc$
tmp.check.printing.used%= pr1.check.printing.used%
tmp.void.chks.over.max%= pr1.void.chks.over.max%
tmp.void.check.amt	= pr1.void.check.amt
tmp.offset.cash.acct%	= pr1.offset.cash.acct%
tmp.default.dist.acct% = pr1.default.dist.acct%
tmp.dist.used%	= pr1.dist.used%
REM
REM--------------------------
REM----- SCREEN SET UP ------
REM--------------------------
REM
#include "fpypar3"

REM
REM--------------------------
REM----- DISPLAY SCREEN ------
REM--------------------------
REM
if match(startup$, common.chaining.status$, 1)<> 0 \
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
	ok% = true%		     rem set flag that response is valid

	if in.status% = req.cancel%	\
		then gosub 60: \
		     goto 999.2 	rem exit without updating file

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

	if not ok%	\
		then trash%= fn.emsg%(msg%): \
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
REM-------------------------------
 60 REM----- RESTORE PR1 VALUES ------
REM-------------------------------
REM
pr1.tax.drive%= tmp.tax.drive%
pr1.ded.drive%= tmp.ded.drive%
pr1.coh.drive%= tmp.coh.drive%
pr1.act.drive%= tmp.act.drive%
pr1.emp.drive%= tmp.emp.drive%
pr1.his.drive%= tmp.his.drive%
pr1.hrs.drive%= tmp.hrs.drive%
pr1.chk.drive%= tmp.chk.drive%
pr1.pay.drive%= tmp.pay.drive%
pr1.pyo.drive%= tmp.pyo.drive%
pr1.gl.used%  = tmp.gl.used%
pr1.glx.drive%= tmp.glx.drive%
pr1.gl.file.suffix$	= tmp.gl.file.suffix$
pr1.gld.drive%= tmp.gld.drive%
pr1.user.program.used%	= tmp.user.program.used%
pr1.user.program$	= tmp.user.program$
pr1.user.prog.desc$	= tmp.user.prog.desc$
pr1.check.printing.used%= tmp.check.printing.used%
pr1.void.chks.over.max%= tmp.void.chks.over.max%
pr1.void.check.amt	= tmp.void.check.amt
pr1.offset.cash.acct%	= tmp.offset.cash.acct%
pr1.default.dist.acct% = tmp.default.dist.acct%
pr1.dist.used%	= tmp.dist.used%

REM
REM-------------------------------------
REM----- DATA DISPLAY SUBROUTINES ------
REM-------------------------------------
REM
 101 REM----- TAX TABLE DRIVE -----
REM
trash%=fn.put%(fn.drive.out$(pr1.tax.drive%), 1)
RETURN
REM
 102 REM----- SYSTEM DED/EARN DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.ded.drive%), 2)
RETURN
REM
 103 REM----- COMPANY HISTORY DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.coh.drive%), 3)
RETURN
REM
 104 REM----- PYAROLL ACCOUNTS DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.act.drive%), 4)
RETURN
REM
 105 REM----- EMPLOYEE MASTER DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.emp.drive%), 5)
RETURN
REM
 106 REM----- EMPLOYEE HISTORY DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.his.drive%), 6)
RETURN
REM
 107 REM----- HOURS BATCH DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.hrs.drive%), 7)
RETURN
REM
 108 REM----- PAYCHECK DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.chk.drive%), 8)
RETURN
REM
 109 REM----- PAY DETAIL DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.pay.drive%), 9)
RETURN
REM
 110 REM----- GL USED ------
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.gl.used%),10)
RETURN
REM
 111 REM----- GL BATCH OUTPUT DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.glx.drive%),11)
RETURN
REM
 112 REM----- GL COA FILE SUFFIX ------
REM
trash%=fn.put%(pr1.gl.file.suffix$, 12)
RETURN
REM
 113 REM----- GL DATA FILE DRIVE ------
REM
trash%=fn.put%(fn.drive.out$(pr1.gld.drive%),13)
RETURN
REM
 114 REM----- USER PROGRAM USED ------
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.user.program.used%),14)
RETURN
REM
 115 REM----- USER PROGRAM NAME ------
REM
trash%=fn.put%(pr1.user.program$, 15)
RETURN
REM
 116 REM----- USER PROGRAM DESCRIPTION ------
REM
trash%=fn.put%(pr1.user.prog.desc$, 16)
RETURN
REM
 117 REM----- COMPUTER CHECK PRINT ------
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.check.printing.used%),17)
RETURN
REM
 118 REM----- VOID CHECKS OVER MAX -----
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.void.chks.over.max%),18)
RETURN
REM
 119 REM----- MAXIMUM CHECK AMOUNT ------
REM
trash%=fn.put%(str$(pr1.void.check.amt), 19)
RETURN
REM
 120 REM----- OFFSET CASH ACCOUNT ------
REM
trash%=fn.put%(str$(pr1.offset.cash.acct%), 20)
RETURN
REM
 121 REM----- DEFAULT DISTRIBUTION ACCOUNT ------
REM
trash%=fn.put%(str$(pr1.default.dist.acct%), 21)
RETURN
REM
 122 REM----- COST DISTRIBUTION TO 5 ACCOUNTS ------
REM
trash%=fn.put%(fn.dsp.yorn$(pr1.dist.used%),22)
RETURN

REM
REM---------------------------------------------------
REM----- SINGLE FIELD DATA CHECKING SUBROUTINES ------
REM---------------------------------------------------
REM
REM
 201 REM----- TAX TABLE DRIVE -----
REM
gosub 380
if ok% then pr1.tax.drive%= drive%
gosub 101
RETURN
REM
 202 REM----- SYSTEM DED/EARN DRIVE ------
REM
gosub 380
if ok% then pr1.ded.drive%= drive%
gosub 102
RETURN
REM
 203 REM----- COMPANY HISTORY DRIVE ------
REM
gosub 380
if ok% then pr1.coh.drive%= drive%
gosub 103
RETURN
REM
 204 REM----- PYAROLL ACCOUNTS DRIVE ------
REM
gosub 380
if ok% then pr1.act.drive%= drive%
gosub 104
RETURN
REM
 205 REM----- EMPLOYEE MASTER DRIVE ------
REM
gosub 380
if ok% then pr1.emp.drive%= drive%
gosub 105
RETURN
REM
 206 REM----- EMPLOYEE HISTORY DRIVE ------
REM
gosub 380
if ok% then pr1.his.drive%= drive%
gosub 106
RETURN
REM
 207 REM----- HOURS BATCH DRIVE ------
REM
gosub 380
if ok% then pr1.hrs.drive%= drive%
gosub 107
RETURN
REM
 208 REM----- PAYCHECK DRIVE ------
REM
gosub 380
if ok% then pr1.chk.drive%= drive%
gosub 108
RETURN
REM
 209 REM----- PAY DETAIL DRIVE ------
REM
gosub 380
if ok% then pr1.pay.drive%= drive%: \
	    pr1.pyo.drive%= drive%
gosub 109
RETURN
REM
 210 REM----- GL USED ------
REM
gosub 320
if ok% then pr1.gl.used%= bool.val%
gosub 110
RETURN
REM
 211 REM----- GL BATCH OUTPUT DRIVE ------
REM
gosub 380
if ok% then pr1.glx.drive%= drive%
gosub 111
RETURN
REM
 212 REM----- GL COA FILE SUFFIX ------
REM
gosub 350
if ok% then pr1.gl.file.suffix$= in.uc$
gosub 112
RETURN
REM
 213 REM----- GL DATA FILE DRIVE ------
REM
gosub 380
if ok% then pr1.gld.drive%= drive%
gosub 113
RETURN
REM
 214 REM----- USER PROGRAM USED ------
REM
gosub 320
if ok% then pr1.user.program.used%= bool.val%
gosub 114
RETURN
REM
 215 REM----- USER PROGRAM NAME ------
REM
gosub 350
if ok% then pr1.user.program$= in.uc$
gosub 115
RETURN
REM
 216 REM----- USER PROGRAM DESCRIPTION ------
REM
gosub 350
if ok% then pr1.user.prog.desc$= in.uc$
gosub 116
RETURN
REM
 217 REM----- COMPUTER CHECK PRINT ------
REM
gosub 320
if ok% then pr1.check.printing.used%= bool.val%
gosub 117
RETURN
REM
 218 REM----- VOID CHECKS OVER MAX -----
REM
gosub 320
if ok% then pr1.void.chks.over.max%= bool.val%
gosub 118
RETURN
REM
 219 REM----- MAXIMUM CHECK AMOUNT ------
REM
gosub 300
if ok% then pr1.void.check.amt= val(in$)
gosub 119
RETURN
REM
 220 REM----- OFFSET CASH ACCOUNT ------
REM
gosub 330
if ok% then pr1.offset.cash.acct%= val(in$)
gosub 120
RETURN
REM
 221 REM----- DEFAULT DISTRIBUTION ACCOUNT ------
REM
gosub 330
if ok% then pr1.default.dist.acct%= val(in$)
gosub 121
RETURN
REM
 222 REM----- COST DISTRIBUTION TO 5 ACCOUNTS ------
REM
gosub 320
if ok% then pr1.dist.used%= bool.val%
gosub 122
RETURN

REM
REM----------------------------------------------
REM----- GENERAL DATA CHECKING SUBROUTINES ------
REM----------------------------------------------
REM----------------------------------------------
REM
REM----------------------------------------------
REM----- FN.NUMERIC(IN$, 7, 2)-------------------
REM----------------------------------------------
REM
 300
	ok% = fn.numeric%(in$,7,2)
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
REM---------------------------------------------
REM----- CHECK VALIDITY OF ACCOUNT NUMBER ------
REM---------------------------------------------
REM
 330
	ok%= fn.num%(in$)
	if not ok%	\
		then msg%= 2: RETURN
	if val(in$)<= 0 or val(in$)> pr2.no.acts%	\
	   then msg%= 9: ok%= false%
	RETURN
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
REM----------------------------------
REM----- CHECK FOR VALID DRIVE ------
REM----------------------------------
REM
 380
	drive%= fn.drive.in%(in.uc$)
	if drive%= -1  then ok%= false%: msg%= 14 \
			else ok%= true%
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
