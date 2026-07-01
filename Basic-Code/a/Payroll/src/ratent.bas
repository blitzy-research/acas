#include "ipycomm"
prgname$="RATENT  DEC. 26,1979 "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  R  A	T  E  N  T
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------
REM
REM----- INCLUDED DATA STRUCTURES -----
REM
function.name$="EMPLOYEE RATE AND WITHHOLDING ENTRY"
program$="RATENT"

#include "ipyconst"
#include "ipydmemp"

REM
REM----- DATA STRUCTURES -----
REM
left.digits%= 5

fields%=28

fld.user.1%=4
fld.rate2%= 7
fld.rate3%= 8
fld.max.pay%= 13
fld.ca.head%= 19
fld.ca.sp.allow%= 20

lit.rate1%= 39
lit.rate2%= 41
lit.rate3%= 43
lit.rate4%= 45
lit.ca.1%= 47
lit.ca.2%= 49
lit.ca.3%= 51
lit.ca.4%= 53

all.valid.interval$= "WBSM"
dim interval.used%(4),		pay.frequency%(4)
interval.used%(1)= pr1.w.used%: pay.frequency%(1)= 52
interval.used%(2)= pr1.b.used%: pay.frequency%(2)= 26
interval.used%(3)= pr1.s.used%: pay.frequency%(3)= 24
interval.used%(4)= pr1.m.used%: pay.frequency%(4)= 12

dim emsg$(40)
emsg$(01)="PY201  THIS PROGRAM MODULE MUST BE SELECTED FROM THE PAYROLL MENU"
emsg$(02)="PY202  THAT'S NOT A VALID CONTROL RESPONSE"
emsg$(03)="PY203  THAT'S NOT A VALID CONTROL RESPONSE"
emsg$(04)="PY204"
emsg$(05)="PY205  ONLY INTEGERS ARE ACCEPTED AT THIS FIELD"
emsg$(06)="PY206  THAT'S NOT AN ACCEPTABLE NUMERIC FORMAT FOR THIS FIELD"
emsg$(07)="PY207  DOUBLE QUOTES ("") ARE INVALID CHARACTERS"
emsg$(08)="PY208  Y  AND  N   ARE THE ONLY ACCEPTABLE ENTRIES AT THIS FIELD"
emsg$(09)="PY209  THAT'S NOT A VALID DATE"
emsg$(10)="PY210  THE EMPLOYEE FILE WAS NOT FOUND"
emsg$(11)="PY211  THE EMPLOYEE FILE WAS NULL OR INVALID"
emsg$(12)="PY212  UNABLE TO READ THE EMPLOYEE RECORD -- END OF FILE FOUND"
emsg$(13)="PY213  UNABLE TO WRITE THE EMPLOYEE RECORD"
emsg$(14)="PY214"
emsg$(15)="PY215"
emsg$(16)="PY216  THAT'S NOT A VALID EMPLOYEE NUMBER"
emsg$(17)="PY217  THERE AREN'T THAT MANY EMPLOYEES ON THE SYSTEM"
emsg$(18)="PY218  THAT'S AN UNUSED EMPLOYEE NUMBER"
emsg$(19)="PY219  THERE ARE NO EMPLOYEES ON THE SYSTEM"
emsg$(20)="PY220"
emsg$(21)="PY221  H AND S  ARE THE ONLY VALID ENTRIES AT THIS FIELD"
emsg$(22)="PY222  THAT'S NOT ONE OF THE PAY INTERVALS CURRENTLY USED"
emsg$(23)="PY223  M  AND  S  ARE THE ONLY VALID ENTRIES AT THIS FIELD"
emsg$(24)="PY224"
emsg$(25)="PY225"
emsg$(26)="PY226  THERE ARE FOUR TAX EXCLUSION TYPES NUMBERED ONE THRU FOUR"
emsg$(27)="PY227"
emsg$(28)="PY228"
emsg$(29)="PY229  THIS EMPLOYEE HAS BEEN EXEMPTED FROM FEDERAL TAX WITHHOLDING"
emsg$(30)="PY230  THIS EMPLOYEE HAS BEEN EXEMPTED FROM STATE TAX WITHHOLDING"
emsg$(31)="PY231  THIS EMPLOYEE HAS BEEN EXEMPTED FROM LOCAL TAX WITHHOLDING"
REM
REM----- SERIAL NUMBER -----
REM
#include "zserial"

REM
REM----- INCLUDED FUNCTIONS -----
REM
#include "zfilconv"
#include "znumeric"
#include "zparse"
#include "zeditdte"
#include "zdateio"
#include "zckdigit"
#include "zstring"
#include "zdspyorn"
#include "zflip"

REM
REM----- DMS SYSTEM -------
REM
#include "zdms"
#include "zdmsused"
#include "zdmstest"
REM
REM----- PROGRAM STARTUP
REM
if not chained.from.root% \
	then trash%=fn.emsg%(01): \
		goto 999.1

REM
REM----- INCLUDE SCREEN CODE
REM
#include "fpyrate"

crt.data$(lit.rate1%)= left$(pr1.rate.name$(1)+blank$, 15)
crt.data$(lit.rate2%)= left$(pr1.rate.name$(2)+blank$, 15)
crt.data$(lit.rate3%)= left$(pr1.rate.name$(3)+blank$, 15)
crt.data$(lit.rate4%)= left$(pr1.rate.name$(4)+blank$, 15)

if pr1.co.state$<> "CA" \
	then trash%=fn.set.used%(false%, fld.ca.head%): \
	     trash%=fn.set.used%(false%, fld.ca.sp.allow%): \
	     trash%=fn.set.used%(false%, lit.ca.1%): \
	     trash%=fn.set.used%(false%, lit.ca.2%): \
	     trash%=fn.set.used%(false%, lit.ca.3%): \
	     trash%=fn.set.used%(false%, lit.ca.4%)

trash%=fn.put.all%(false%)
REM
REM-------------------------------
REM----- OPEN EMPLOYEE FILE ------
REM-------------------------------
REM
if end #emp.file% then 1010		rem exit if no employee file
open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,password$,param$) \
	recl	emp.len% \
	as	emp.file%
if end #emp.file% then 1011		rem exit if no employee header record
read #emp.file%; \
#include "ipyemphdr"

if emp.hdr.no.recs%=0 \
	then trash%=fn.emsg%(19): \	--- can't run if no employees
	     close emp.file%: \
	     goto 999.1 		rem error exit

REM
REM----- MAIN ROUTINE -----
REM
while true%
    if pr1.debugging% \
	then trash%=fn.msg%("BYTES FREE "+str$(fre))
    changing%=false%
    REM
    REM----- LOOP UNTIL USER WANTS TO CHANGE DATA IN THE RECORD -----
    REM
    while not changing%
	trash%=fn.get%(4, 1)
	if in.status%=req.valid% \
		then gosub 220 \		--- check employee number
		else gosub 200			rem check control responses
	if stopit% then 990			rem exit on stop requested
	REM
	REM----- IF A RECORD IS WANTED, GET IT -----
	if end #emp.file% then 1012		rem exit if unable to read emp
	if rec.wanted% \
		then record.read%=true%: \
		read #emp.file%, emp.rec%; \
#include "ipyemp"
	if record.read% and emp.status$="D" \   --- if record is deleted
		then trash%=fn.emsg%(18): \
		record.read%=false%
	if rec.wanted% and record.read% \
		then gosub 50000		rem display emp rec
    wend
    field%=fld.user.1%
    done%=false%
    write.needed%=true%
    REM
    REM----- GET USER CHANGES -----
    REM
    while not done%
	invalid.data%=false%
	trash%=fn.get%(3, field%)
	if in.status%=req.valid% \
		then on field%-3 gosub \
			5004,	\
			5005,	\
			5006,	\
			5007,	\
			5008,	\
			5009,	\
			5010,	\
			5011,	\
			5012,	\
			5013,	\
			5014,	\
			5015,	\
			5016,	\
			5017,	\
			5018,	\
			5019,	\
			5020,	\
			5021,	\
			5022,	\
			5023,	\
			5024,	\
			5025,	\
			5026,	\
			5027,	\
			5028:	\
			trash%=fn.put%(out$, field%) \
		else gosub 250
	if invalid.data% then trash%=fn.emsg%(msg%)
	if (in.status%=req.valid% and not invalid.data%) or \
	    in.status%=req.cr%	or in.status%=req.back% \
		then selected%=false% \
		else selected%=true%
	while not selected%
		if in.status%=req.valid%  or in.status%=req.cr%  \
			then field%= field%+ 1
		if in.status%=req.back% then field%= field%- 1
		if field%< fld.user.1% then field%= fields%
		if field%> fields% then field%= fld.user.1%
		if fn.test%(crt.used%, field%) then selected%=true%
	wend
    wend
    REM
    REM----- WRITE RECORD IF CHANGES NOT CANCELED -----
    REM
    if end #emp.file% then 1013 	rem exit if unable to write
    if write.needed% \
	then print #emp.file%, emp.rec%; \
#include "ipyemp"

wend

200 REM----- PRIMARY CONTROL RESPONSES ------------------
rec.wanted%=false%
if in.status%=req.cr% and record.read%	then changing%=true%: RETURN
if in.status%=req.back% \
	then gosub 201: rec.wanted%=true%: RETURN
if in.status%=req.next% \
	then gosub 202: rec.wanted%=true%: RETURN
if in.status%=req.stopit% then stopit%=true%: RETURN
trash%=fn.emsg%(02)
RETURN

201 REM----- GET PREVIOUS RECORD -----
emp.rec%=emp.rec%-1
if emp.rec%<2 then emp.rec%=emp.hdr.no.recs%+1
RETURN
202 REM----- GET NEXT RECORD -----
if emp.rec%=0 then emp.rec%=1
emp.rec%=emp.rec%+1
if emp.rec%>emp.hdr.no.recs%+1 then emp.rec%=2
RETURN

220 REM----- CHECK EMPLOYEE NUMBER FOR VALIDITY --------------
rec.wanted%=false%
if not fn.num%(in$) or len(in$)<>5 or fn.ck.dig$(left$(in$,4))<>right$(in$,1) \
	then trash%=fn.emsg%(16): RETURN

emp.rec%=val(left$(in$, 4))+1
invalid.data%=false%
if emp.rec% < 2 or emp.rec% > emp.hdr.no.recs%+ 1 \
	then trash%=fn.emsg%(17): RETURN
rec.wanted%=true%
RETURN

250 REM----- CHECK SECONDARY CONTROL CHARACTERS --------------
if in.status%=req.cr% or in.status%=req.back% then RETURN
if in.status%=req.cancel%   \
	then done%=true%: record.read%=false%: write.needed%=false%: RETURN
if in.status%=req.stopit% then done%=true%: RETURN
trash%=fn.emsg%(03)
RETURN

990 REM----- CLOSE EMPLOYEE FILE -----
trash%=fn.msg%("STOP REQUESTED")
close emp.file%

#include "zeoj"

1010 REM----- NO EMPLOYEE FILE -----
trash%=fn.emsg%(10)
goto 999.1

1011 REM----- NO EMPLOYEE FILE HEADER -----
trash%=fn.emsg%(11)
close emp.file%
goto 999.1

1012 REM----- UNABLE TO GET EMPLOYEE RECORD -----
trash%=fn.emsg%(12)
close emp.file%
goto 999.1

1013 REM----- UNABLE TO WRITE EMPLOYEE RECORD -----
trash%=fn.emsg%(13)
close emp.file%
goto 999.1

REM
REM-----------------------------------------
REM----- GENERAL DATA EDIT SUBROUTINES -----
REM-----------------------------------------
REM
2020 REM-----  NUMERIC DATA   LEFT.DIGITS%  CAN BE SET BY CALLER -----
REM-----	 BUT SHOULD BE RESTORED TO  5  BY CALLER	-----
if not fn.numeric%(in$, left.digits%, 2) \
	then invalid.data%=true%: msg%=06
RETURN
2040 REM-----	Y  OR  N   -----
boolean.value%= false%
if in.uc$="Y" then boolean.value%= true%
if in.uc$<>"Y" and in.uc$<>"N" \
	then invalid.data%=true%: msg%=08
RETURN
2050 REM-----  INTEGER DATA  -----
if not fn.num%(in$) \
	then invalid.data%=true%: msg%=05
RETURN

REM
REM---------------------------------------------
REM-----  FIELD SPECIFIC DATA SUBROUTINES  -----
REM---------------------------------------------
REM
5004 REM----- PAY TYPE: HOURLY OR SALARIED -----
REM
if in.uc$= "H" or in.uc$= "S" \
	then emp.hs.type$=in.uc$ \
	else invalid.data%= true%: msg%= 21
out$=emp.hs.type$
RETURN

REM
5005 REM----- PAY INTERVAL ------
REM
interval%= match(in.uc$, all.valid.interval$, 1)
if interval%<> 0 \
	then emp.pay.interval$= in.uc$: \
	     emp.pay.freq%= pay.frequency%(interval%) \
	else invalid.data%=true%: msg%=22
out$=emp.pay.interval$
RETURN

REM
5006 REM----- REGULAR PAY RATE -----
REM
if emp.rate(1)= 0.0  and emp.hs.type$="H" \
	then recalculate%= true% \
	else recalculate%= false%
gosub 2020
if not invalid.data% \
	then emp.rate(1)=val(in$)
out$=str$(emp.rate(1))

if recalculate% and not invalid.data% \
    then emp.rate(2)= emp.rate(1)*pr1.rate2.factor: \
     emp.rate(3)= emp.rate(1)*pr1.rate3.factor: \
     emp.max.pay= emp.rate(1)*emp.normal.units*pr1.max.pay.factor: \
     trash%=fn.put%(str$(emp.rate(2)), fld.rate2%): \
     trash%=fn.put%(str$(emp.rate(3)), fld.rate3%): \
     trash%=fn.put%(str$(emp.max.pay), fld.max.pay%)
RETURN

REM
5007 REM----- OVERTIME PAY RATE -----
REM
gosub 2020
if not invalid.data% \
	then emp.rate(2)=val(in$)
out$=str$(emp.rate(2))
RETURN

REM
5008 REM----- SPECIAL OVERTIME RATE ---
REM
gosub 2020
if not invalid.data% \
	then emp.rate(3)=val(in$)
out$=str$(emp.rate(3))
RETURN

REM
5009 REM----- COMMISSION RATE -----
REM
gosub 2020
if not invalid.data% \
	then emp.rate(4)=val(in$)
out$=str$(emp.rate(4))
RETURN

REM
5010 REM----- RATE 4 TAX XCLU TYPE  -----
REM
num%= val(in$)
if num%< 1  or	num%> 4 \
	then invalid.data%= true%: msg%= 26 \
	else emp.rate4.exclusion%= num%
out$= str$(emp.rate4.exclusion%)
RETURN

REM
5011 REM----- AUTOGEN UNITS -----
REM
gosub 2020
if not invalid.data% \
	then emp.auto.units= val(in$)
out$=str$(emp.auto.units)
RETURN

REM
5012 REM----- NORMAL UNITS -----
REM
gosub 2020
if not invalid.data% \
	then emp.normal.units=val(in$)
if emp.hs.type$= "H" \
	then emp.max.pay= emp.rate(1)*emp.normal.units*pr1.max.pay.factor: \
	trash%=fn.put%(str$(emp.max.pay), fld.max.pay%)
out$=str$(emp.normal.units)
RETURN

REM
5013 REM----- MAXIMUM PAY -----
REM
left.digits%= 6
gosub 2020
left.digits%= 5
if not invalid.data% \
	then emp.max.pay=val(in$)
out$=str$(emp.max.pay)
RETURN

REM
5014 REM----- MARRIED OR SINGLE -----
REM
if match(in.uc$, "MS", 1)<> 0 \
	then emp.marital$=in.uc$ \
	else invalid.data%=true%: msg%=23
out$=emp.marital$
RETURN

REM
5015 REM----- FEDERAL WITHHOLDING ALLOWANCES -----
REM
gosub 2050
if emp.fwt.exempt% and val(in$)<> 0 \
	then invalid.data%= true%: msg%=29
if not invalid.data%\
	then emp.fwt.allow%=val(in$)
out$=str$(emp.fwt.allow%)
RETURN

REM
5016 REM----- STATE WITHOLDING -----
REM
gosub 2050
if emp.swt.exempt% and val(in$)<> 0 \
	then invalid.data%= true%: msg%=30
if not invalid.data%\
	then emp.swt.allow%=val(in$)
out$=str$(emp.swt.allow%)
RETURN

REM
5017 REM----- LOCAL WITHOLDING ALLOWANCES -----
REM
gosub 2050
if emp.lwt.exempt% and val(in$)<> 0 \
	then invalid.data%= true%: msg%=31
if not invalid.data%\
	then emp.lwt.allow%=val(in$)
out$=str$(emp.lwt.allow%)
RETURN

REM
5018 REM----- EIC USED -----
REM
gosub 2040
if not invalid.data% \
	then emp.eic.used%= boolean.value%
out$=fn.dsp.yorn$(emp.eic.used%)
RETURN

REM
5019 REM----- CALIFORNIA HEAD OF HOUSE -----
REM
gosub 2040
if not invalid.data% \
	then emp.cal.head.of.house%= boolean.value%
out$=fn.dsp.yorn$(emp.cal.head.of.house%)
RETURN

REM
5020 REM----- CALIFORNIA WITHOLDING ALLOWANCES -----
REM
gosub 2050
if not invalid.data%\
	then emp.cal.ded.allow%=val(in$)
out$=str$(emp.cal.ded.allow%)
RETURN

REM
5021 REM----- VACATION RATE -----
REM
gosub 2020
if not invalid.data% \
	then emp.vac.rate=val(in$)
out$=str$(emp.vac.rate)
RETURN

REM
5022 REM----- VACATION ACCUMULATED -----
REM
gosub 2020
if not invalid.data% \
	then  emp.vac.accum=val(in$)
out$=str$(emp.vac.accum)
RETURN

REM
5023 REM----- VACATION USED -----
REM
gosub 2020
if not invalid.data% \
	then  emp.vac.used=val(in$)
out$=str$(emp.vac.used)
RETURN

REM
5024 REM----- SICK LEAVE RATE -----
REM
gosub 2020
if not invalid.data% \
	then emp.sl.rate=val(in$)
out$=str$(emp.sl.rate)
RETURN

REM
5025 REM----- SICK LEAVE ACCUMULATED ------
REM
gosub 2020
if not invalid.data% \
	then  emp.sl.accum=val(in$)
out$=str$(emp.sl.accum)
RETURN

REM
5026 REM----- SICK TIME USED -----
REM
gosub 2020
if not invalid.data% \
	then  emp.sl.used=val(in$)
out$=str$(emp.sl.used)
RETURN

REM
5027 REM----- COMPENSATION TIME ACCUMULATED -----
REM
gosub 2020
if not invalid.data% \
	then  emp.comp.accum=val(in$)
out$=str$(emp.comp.accum)
RETURN

REM
5028 REM----- COMPENSATION TIME USED -----
REM
gosub 2020
if not invalid.data% \
	then  emp.comp.used=val(in$)
out$=str$(emp.comp.used)
RETURN

50000 REM----- DISPLAY SOME OF THE EMPLOYEE RECORD -----
trash%=fn.put%( 	    emp.no$		, 1)
trash%=fn.put%(fn.name.flip$(emp.emp.name$)	, 2)
trash%=fn.put%( 	    emp.ssn$		, 3)
trash%=fn.put%( 	    emp.hs.type$	, 4)
trash%=fn.put%( 	    emp.pay.interval$	, 5)
trash%=fn.put%( 	    emp.marital$	,14)
trash%=fn.put%(        str$(emp.fwt.allow%)	,15)
trash%=fn.put%(        str$(emp.rate(1))	,06)
trash%=fn.put%(        str$(emp.swt.allow%)	,16)
trash%=fn.put%(        str$(emp.rate(2))	,07)
trash%=fn.put%(        str$(emp.lwt.allow%)	,17)
trash%=fn.put%(        str$(emp.rate(3))	,08)
trash%=fn.put%(fn.dsp.yorn$(emp.eic.used%)	,18)
trash%=fn.put%(        str$(emp.rate(4))	,09)
trash%=fn.put%(        str$(emp.rate4.exclusion%),10)
trash%=fn.put%(        str$(emp.auto.units)	,11)
trash%=fn.put%(        str$(emp.normal.units)	,12)
if pr1.co.state$= "CA" \
	then trash%=fn.put%(fn.dsp.yorn$(emp.cal.head.of.house%),19): \
	     trash%=fn.put%(	    str$(emp.cal.ded.allow%)	,20)
trash%=fn.put%(        str$(emp.max.pay)	,13)
trash%=fn.put%(        str$(emp.vac.rate)	,21)
trash%=fn.put%(        str$(emp.vac.accum)	,22)
trash%=fn.put%(        str$(emp.vac.used)	,23)
trash%=fn.put%(        str$(emp.sl.rate)	,24)
trash%=fn.put%(        str$(emp.sl.accum)	,25)
trash%=fn.put%(        str$(emp.sl.used)	,26)
trash%=fn.put%(        str$(emp.comp.accum)	,27)
trash%=fn.put%(        str$(emp.comp.used)	,28)
RETURN
