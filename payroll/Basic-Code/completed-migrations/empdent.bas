$include "ipycomm"
prgname$="EMPDENT  DEC. 12, 1979     "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  E  M	P  D  E  N  T
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------
REM
function.name$="EMPLOYEE DEDUCTION/EARNING AND COST DIST ENTRY"
program$="EMPDENT"
REM
REM------------------------------------
REM----- INCLUDED DATA STRUCTURES -----
REM------------------------------------
REM
$include "ipyconst"
$include "ipydmemp"
REM
REM-------------------------------------------------------------------
REM----- PROGRAM SPECIFIC DATA STRUCTURES			 -----
REM----- EXCEPT EQUATES USING FUNCTION CALLS, WHICH CAN BE FOUND -----
REM----- FOLLOWING THE FUNCOTION DEFINITION SECTION		 -----
REM-------------------------------------------------------------------
REM
left.digits%= 5
emp.rec%= 1
fields%=57		rem highest field number for data entry loop
fields.per.dist.acct%= 2
fields.per.emp.ed%= 10

total.field%=4
user.field.1%=5
dist.acct.field.1%=5
dist.pct.field.1%=6
sys.ex.1%=22
ed.field.1%=27
fld.dist.not.used%= 57

lit.dist.used1%   = 67
lit.dist.used2%   = 69
lit.dist.used3%   = 71
lit.dist.used4%   = 73
lit.dist.used5%   = 75
lit.dist.total%   = 77
lit.dist.not.used%= 85

dim emsg$(30)
emsg$(01)="PY241  THIS PROGRAM MODULE MUST BE SELECTED FROM THE PAYROLL MENU"
emsg$(02)="PY242  THAT'S NOT A VALID CONTROL RESPONSE"
emsg$(03)="PY243  THAT'S NOT A VALID CONTROL RESPONSE"
emsg$(04)="PY244"
emsg$(05)="PY245  ONLY INTEGERS ARE ACCEPTED AT THIS FIELD"
emsg$(06)="PY246  THAT'S NOT AN ACCEPTABLE NUMERIC FORMAT FOR THIS FIELD"
emsg$(07)="PY247  DOUBLE QUOTES ("") ARE INVALID CHARACTERS"
emsg$(08)="PY248  Y  AND  N   ARE THE ONLY ACCEPTABLE ENTRIES AT THIS FIELD"
emsg$(09)="PY249  THAT'S NOT A VALID DATE"
emsg$(10)="PY250  THE EMPLOYEE FILE WAS NOT FOUND"
emsg$(11)="PY251  THE EMPLOYEE FILE WAS NULL OR INVALID"
emsg$(12)="PY252  UNABLE TO READ THE EMPLOYEE RECORD -- END OF FILE FOUND"
emsg$(13)="PY253  UNABLE TO WRITE THE EMPLOYEE RECORD"
emsg$(14)="PY254"
emsg$(15)="PY255"
emsg$(16)="PY256  THAT'S NOT A VALID EMPLOYEE NUMBER"
emsg$(17)="PY257  THERE AREN'T THAT MANY EMPLOYEES ON THE SYSTEM"
emsg$(18)="PY258  THAT'S AN UNUSED EMPLOYEE NUMBER"
emsg$(19)="PY259  THERE ARE NO EMPLOYEES ON THE SYSTEM"
emsg$(20)="PY260"
emsg$(21)="PY261"
emsg$(22)="PY262"
emsg$(23)="PY263"
emsg$(24)="PY264  AN INVALID CHECK CATEGORY HAS BEEN ENTERED"
emsg$(25)="PY265  E AND D  ARE THE ONLY VALID ENTRIES AT THIS FIELD"
emsg$(26)="PY266  THERE ARE FOUR TAX EXCLUSION TYPES NUMBERED ONE THRU FOUR"
emsg$(27)="PY267  A AND P  ARE THE ONLY VALID ENTRIES AT THIS FIELD"
emsg$(28)="PY268  CHECK CATEGORIES CAN BE  2-7 (EARNINGS) OR 9-16 (DEDUCTIONS)"
emsg$(29)="PY269  THAT'S NOT A VALID PAYROLL SYSTEM ACCOUNT"
emsg$(30)="PY270  THE ACCOUNT DISTRIBUTION PERCENTAGES MUST TOTAL 100.0%"

REM
REM----- SERIAL NUMBER -----
REM
$include "zserial"
REM
REM-----------------------------------------
REM----- INCLUDED FUNCTION DEFINITIONS -----
REM-----------------------------------------
REM
$include "zfilconv"
$include "znumeric"
$include "zstring"
$include "zdateio"
$include "zckdigit"
$include "zdspyorn"
$include "zflip"
%eject
REM
REM----- DMS SYSTEM ------
REM
$include "zdms"
$include "zdmsused"
$include "zdmstest"
$include "zdmsclr"
%list
REM
REM-----------------------------------------------------
REM-----	      PROGRAM STARTUP		   -----
REM-----	 CHECK INITIALIZATION FLAG	   -----
REM-----	     GET EMPLOYEE FILE		   -----
REM-----------------------------------------------------
REM
if not chained.from.root% \
	then trash%=fn.emsg%(01): \
		goto 999.1

if end #emp.file% then 1010		rem exit if no employee file
open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,password$,param$) \
	recl	emp.len% \
	as	emp.file%
if end #emp.file% then 1011		rem exit if no employee header record
read #emp.file%; \
$include "ipyemphdr"

if emp.hdr.no.recs%=0 \
	then trash%=fn.emsg%(19): \	can't run if no employees
	close emp.file%: \
	goto 999.1			rem so goto close files and exit

REM
REM----- INCLUDE SCREEN CODE
REM
$include "fpyempd"

if not pr1.dist.used% \
	then trash%= fn.set.used%(true%,  lit.dist.not.used%): \
	     trash%= fn.set.used%(false%, lit.dist.used1%): \
	     trash%= fn.set.used%(false%, lit.dist.used2%): \
	     trash%= fn.set.used%(false%, lit.dist.used3%): \
	     trash%= fn.set.used%(false%, lit.dist.used4%): \
	     trash%= fn.set.used%(false%, lit.dist.used5%): \
	     trash%= fn.set.used%(false%, lit.dist.total%)

trash%=fn.put.all%(false%)
REM
REM----- MAIN ROUTINE -----
REM
while true%
    if pr1.debugging% \
	then trash%=fn.msg%("BYTES FREE "+str$(fre))
    field%= 1
    changing%=false%
    REM
    REM----- LOOP UNTIL USER WANTS TO CHANGE DATA IN THE RECORD -----
    REM
    while not changing%
	trash%=fn.get%(4, field%)
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
$include "ipyemp"
	if record.read% and emp.status$="D" \   --- if record is deleted
		then print using "&";bell$;fn.emsg%(18): \
		record.read%=false%
	if rec.wanted% and record.read% \
		then gosub 50000		rem display emp rec
    wend
    if pr1.dist.used% then field%=user.field.1% \
		      else field%=fields%
    done%=false%
    write.needed%=true%
    while not done%
	REM
 20	REM----- GET USER CHANGES -----
	REM
	invalid.data%=false%
	trash%=fn.get%(3, field%)
	if in.status%= req.valid% \
		then on (field%-user.field.1%)+1 gosub \
			5005,	\ 5 possible cost accounts
			5006,	\
			5005,	\
			5006,	\
			5005,	\
			5006,	\
			5005,	\
			5006,	\
			5005,	\
			5006,	\
			5016,	\ exempt from fica		 withholding
			5055,	\ exempt from futa
			5056,	\ exempt from sui
			5018,	\ exempt from sdi		 withholding
			5015,	\ exempt from federal income tax witholding
			5017,	\ exempt from state   income tax wh
			5019,	\ exempt from local   income tax wh
			5020,	\ 5 system deduction exempts
			5020,	\
			5020,	\
			5020,	\
			5020,	\
			5025,	\ 3 employee specific deductions/earnings,
			5026,	\ 10 elements per deduction
			5027,	\
			5028,	\
			5029,	\
			5030,	\
			5031,	\
			5032,	\
			5033,	\
			5034,	\
			5025,	\ 2nd ded/earn
			5026,	\
			5027,	\
			5028,	\
			5029,	\
			5030,	\
			5031,	\
			5032,	\
			5033,	\
			5034,	\
			5025,	\ 3rd ded/earn
			5026,	\
			5027,	\
			5028,	\
			5029,	\
			5030,	\
			5031,	\
			5032,	\
			5033,	\
			5034,	\
			5057:	\
			trash%=fn.put%(out$, field%) \
		else gosub 250
	if invalid.data% then trash%=fn.emsg%(msg%)
	bump%= 0
	if (in.status%= req.valid% and not invalid.data%) or \
	    in.status%= req.cr%  \
		then bump%= 1
	if in.status%= req.back% then bump%= -1
	selected%= false%
	while bump%<> 0 and not selected%
		field%= field%+ bump%
		if field% > fields% then field%=user.field.1%
		if field% < user.field.1% then field%=fields%
		if fn.test%(crt.used%, field%) then selected%= true%
	wend
    wend
    REM
    REM----- VALIDITY CHECK AT END ------
    REM
    if write.needed% and pr1.dist.used% and dist.total <> 100.0 \
	then field%= dist.acct.field.1%: \
	     trash%= fn.emsg%(30): \
	     done% = false%: goto 20		rem get changes
    for f%= 1 to pr1.max.emp.eds%
	num%= emp.ed.chk.cat%(f%)
	if write.needed% and num%<> 0 \
	 and (((num%<  pr1.lo.earn.chk.cat% or num%> pr1.hi.earn.chk.cat%) \
		and emp.ed.earn.ded$(f%)="E") \
	     or ((num%> pr1.hi.ded.chk.cat% or num%< pr1.lo.ded.chk.cat%) \
		and emp.ed.earn.ded$(f%)="D"))\
		then field%=ed.field.1%+ \
		     (f%*fields.per.emp.ed%)- 1: \
		     trash%= fn.emsg%(24): \
		     done% = false%: goto 20		rem get changes
    next f%

    REM
    REM----- WRITE RECORD IF CHANGES NOT CANCELED -----
    REM
    if end #emp.file% then 1013 	rem exit if unable to write
    if write.needed% \
	then print #emp.file%, emp.rec%; \
$include "ipyemp"

wend

200 REM----- PRIMARY CONTROL RESPONSES ------------------
rec.wanted%=false%
if in.status%= req.cr% and record.read%  then changing%=true%: RETURN
if in.status%= req.back% \
	then gosub 201: rec.wanted%=true%: RETURN
if in.status%= req.next% \
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
if emp.rec% < 2 then invalid.data%=true%
if emp.rec% > emp.hdr.no.recs%+1 then invalid.data%=true%
if invalid.data% then trash%=fn.emsg%(17): RETURN
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

$include "zeoj"

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
in$=ucase$(in$)
boolean.value%= false%
if in$="Y" then boolean.value%= true%
if in$<>"Y" and in$<>"N" \
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
REM
5005 REM----- DISTRIBUTION ACCOUNTS -----
acct.no%=val(in$)
cur.acct%=((field%-dist.acct.field.1%)/fields.per.dist.acct%)+1
if acct.no% <= pr2.no.acts%  and acct.no% > 0 \
	then emp.dist.acct%(cur.acct%)= acct.no% \
	else msg%=29: invalid.data%=true%
out$=str$(emp.dist.acct%(cur.acct%))
RETURN

5006 REM----- DISTRIBUTION PERCENTAGES -----
cur.pct%=((field%-dist.pct.field.1%)/2)+1
dist.total= dist.total- emp.dist.percent(cur.pct%)
gosub 2020
if not invalid.data% \
	then  emp.dist.percent(cur.pct%)= val(in$)
dist.total= dist.total+ emp.dist.percent(cur.pct%)
trash%=fn.put%(str$(dist.total), total.field%)
out$=str$(emp.dist.percent(cur.pct%))
RETURN

REM
5015 REM----- FEDERAL EXEMPT -----
REM
gosub 2040
if not invalid.data% \
	then emp.fwt.exempt%= boolean.value%
out$=fn.dsp.yorn$(emp.fwt.exempt%)
RETURN

REM
5016 REM----- FICA EXEMPT -----
REM
gosub 2040
if not invalid.data% \
	then emp.fica.exempt%= boolean.value%
out$=fn.dsp.yorn$(emp.fica.exempt%)
RETURN

REM
5017 REM----- STATE EXEMPT -----
REM
gosub 2040
if not invalid.data% \
	then emp.swt.exempt%= boolean.value%
out$=fn.dsp.yorn$(emp.swt.exempt%)
RETURN

REM
5018 REM----- STATE DISABILITY EXEMPT -----
REM
gosub 2040
if not invalid.data% \
	then emp.sdi.exempt%=boolean.value%
out$=fn.dsp.yorn$(emp.sdi.exempt%)
RETURN

REM
5019 REM----- LOCAL WITHOLDING EXEMPT -----
REM
gosub 2040
if not invalid.data% \
	then emp.lwt.exempt%= boolean.value%
out$=fn.dsp.yorn$(emp.lwt.exempt%)
RETURN

REM
5020 REM----- SYSTEM DEDUCTION EXEMPTS -----
REM
cur.sys%= field%-(sys.ex.1%-1)
gosub 2040
if not invalid.data% \
	then emp.sys.exempt%(cur.sys%)= boolean.value%
out$=fn.dsp.yorn$(emp.sys.exempt%(cur.sys%))
RETURN

REM
 5025 REM----- EMPLOYEE DED/EARN USED ------
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
gosub 2040		rem check yorn, return bool.val%
if invalid.data% then out$= fn.dsp.yorn$(emp.ed.chk.cat%(cur.ed%)): RETURN
if emp.ed.earn.ded$(cur.ed%)= "D" \
	then default.chk.cat%= 16: default.acct%= 2 \
	else default.chk.cat%=	7: default.acct%= 3
if boolean.value% and emp.ed.chk.cat%(cur.ed%)= 0 \
	then emp.ed.chk.cat%(cur.ed%)= default.chk.cat%: \
	     emp.ed.acct.no%(cur.ed%)= default.acct%: gosub 50005
if not boolean.value% \
	then emp.ed.chk.cat%(cur.ed%)= 0: gosub 50010
out$=fn.dsp.yorn$(emp.ed.chk.cat%(cur.ed%))
RETURN

REM
5026 REM----- EMPLOYEE DEDUCTION DESCRIPTION -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
if match(quote$, in$, 1) \
	then invalid.data%=true%: msg%=07 \
	else emp.ed.desc$(cur.ed%)=in$
out$=emp.ed.desc$(cur.ed%)
RETURN

REM
5027 REM----- EARNING OR DEDUCTION -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
in$=ucase$(in$)
if match(in$, "ED", 1)\
	then emp.ed.earn.ded$(cur.ed%)=in$ \
	else invalid.data%=true%: msg%=25
if emp.ed.earn.ded$(cur.ed%)= "D" \
	then emp.ed.chk.cat%(cur.ed%)= 16: emp.ed.acct.no%(cur.ed%)= 2 \
	else emp.ed.chk.cat%(cur.ed%)=	7: emp.ed.acct.no%(cur.ed%)= 3
gosub 50005
out$=emp.ed.earn.ded$(cur.ed%)
RETURN

REM
5028 REM----- ACCOUNT FOR DEDUCTION ------
REM
acct.no%= val(in$)
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
if acct.no% <= pr2.no.acts%  and acct.no% > 0 \
	then emp.ed.acct.no%(cur.ed%)= acct.no% \
	else msg%=29: invalid.data%=true%
out$= str$(emp.ed.acct.no%(cur.ed%))
RETURN

REM
5029 REM----- E/D AMOUNT OR PERCENT -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
in$=ucase$(in$)
if match(in$, "AP", 1)\
	then emp.ed.amt.percent$(cur.ed%)=in$ \
	else invalid.data%=true%: msg%=27
out$=emp.ed.amt.percent$(cur.ed%)
RETURN

REM
5030 REM----- DEDUCTION FACTOR -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
left.digits%= 6
gosub 2020
left.digits%= 5
if not invalid.data% \
	then emp.ed.factor(cur.ed%)=val(in$)
out$=str$(emp.ed.factor(cur.ed%))
RETURN

REM
5031 REM----- LIMIT ON E/D USED -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
gosub 2040
if not invalid.data% \
	then emp.ed.limit.used%(cur.ed%)= boolean.value%
out$=fn.dsp.yorn$(emp.ed.limit.used%(cur.ed%))
RETURN

REM
5032 REM----- EARNING/DEDUCTION LIMIT -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
left.digits%= 7
gosub 2020
left.digits%= 5
if not invalid.data% \
	then emp.ed.limit(cur.ed%)=val(in$)
out$=str$(emp.ed.limit(cur.ed%))
RETURN

REM
5033 REM----- E/D TAX EXCLUSION TYPE -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
num%=val(in$)
if num% > 0 and num% <= 4 \
	then emp.ed.exclusion%(cur.ed%)=val(in$) \
	else invalid.data%=true%: msg%=26
out$=str$(emp.ed.exclusion%(cur.ed%))
RETURN

REM
5034 REM----- E/D CHECK CATEGORY -----
REM
cur.ed%=((field%-ed.field.1%)/fields.per.emp.ed%)+1
num%=val(in$)
if   (num%>= pr1.lo.earn.chk.cat% and num%<= pr1.hi.earn.chk.cat%) \
  or (num%<= pr1.hi.ded.chk.cat%  and num%>= pr1.lo.ded.chk.cat%) \
	then emp.ed.chk.cat%(cur.ed%)=val(in$) \
	else invalid.data%=true%: msg%=28
out$=str$(emp.ed.chk.cat%(cur.ed%))
RETURN

REM
5055 REM----- FUTA EXEMPT -----
REM
gosub 2040
if not invalid.data% \
	then emp.co.futa.exempt%= boolean.value%
out$=fn.dsp.yorn$(emp.co.futa.exempt%)
RETURN

REM
5056 REM----- SUI EXEMPT -----
REM
gosub 2040
if not invalid.data% \
	then emp.co.sui.exempt%= boolean.value%
out$=fn.dsp.yorn$(emp.co.sui.exempt%)
RETURN

REM
5057 REM----- DISTRIBUTION ACCOUNT 100.00% ONLY -----
REM
acct.no%= val(in$)
if acct.no%> pr2.no.acts% or acct.no%< 1 \
	then invalid.data%= true%: msg%= 29: \
	else emp.dist.acct%(1)= acct.no%
out$=str$(emp.dist.acct%(1))
RETURN

50000 REM----- DISPLAY SOME OF THE EMPLOYEE RECORD -----
trash%=fn.put%( 	    emp.no$		, 1)
trash%=fn.put%(fn.name.flip$(emp.emp.name$)	, 2)
trash%=fn.put%( 	    emp.ssn$		, 3)
if pr1.dist.used% \
    then gosub 50020 \
    else trash%=fn.put%(str$(emp.dist.acct%(1)),  fld.dist.not.used%)
trash%=fn.put%(fn.dsp.yorn$(emp.fica.exempt%)	,15)
trash%=fn.put%(fn.dsp.yorn$(emp.co.futa.exempt%)	,16)
trash%=fn.put%(fn.dsp.yorn$(emp.co.sui.exempt%) ,17)
trash%=fn.put%(fn.dsp.yorn$(emp.sdi.exempt%)	,18)
trash%=fn.put%(fn.dsp.yorn$(emp.fwt.exempt%)	,19)
trash%=fn.put%(fn.dsp.yorn$(emp.swt.exempt%)	,20)
trash%=fn.put%(fn.dsp.yorn$(emp.lwt.exempt%)	,21)
for f%= 0 to pr1.max.sys.eds%- 1
 trash%=fn.put%(fn.dsp.yorn$(emp.sys.exempt%(f%+1)),sys.ex.1%+ f%)
next f%
for cur.ed%= 1 to pr1.max.emp.eds%
	trash%= fn.put%(fn.dsp.yorn$(emp.ed.chk.cat%(cur.ed%)), \
	   ed.field.1%+ (cur.ed%-1)*fields.per.emp.ed%)
	if emp.ed.chk.cat%(cur.ed%)= 0 \
		then gosub 50010 \
		else gosub 50005
next cur.ed%

RETURN

REM
50005 REM----- DISPLAY A USED EMP EARN/DED ------
REM
 f%=cur.ed%- 1
 g%=cur.ed%
 trash%=fn.put%(	emp.ed.desc$(g%)	    ,28+ f%*fields.per.emp.ed%)
 trash%=fn.put%(	emp.ed.earn.ded$(g%)	    ,29+ f%*fields.per.emp.ed%)
 trash%=fn.put%(	str$(emp.ed.acct.no%(g%))   ,30+ f%*fields.per.emp.ed%)
 trash%=fn.put%(	emp.ed.amt.percent$(g%)     ,31+ f%*fields.per.emp.ed%)
 trash%=fn.put%(	str$(emp.ed.factor(g%))     ,32+ f%*fields.per.emp.ed%)
 trash%=fn.put%(fn.dsp.yorn$(emp.ed.limit.used%(g%)),33+ f%*fields.per.emp.ed%)
 trash%=fn.put%(	str$(emp.ed.limit(g%))	    ,34+ f%*fields.per.emp.ed%)
 trash%=fn.put%(	str$(emp.ed.exclusion%(g%)) ,35+ f%*fields.per.emp.ed%)
 trash%=fn.put%(	str$(emp.ed.chk.cat%(g%))   ,36+ f%*fields.per.emp.ed%)
RETURN
REM
 50010 REM----- DISPLAY AN UNUSED EMP EARN/DED ------
REM
 f%=cur.ed%- 1
 trash%=fn.clr%(28+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(29+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(30+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(31+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(32+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(33+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(34+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(35+ f%*fields.per.emp.ed%)
 trash%=fn.clr%(36+ f%*fields.per.emp.ed%)
RETURN

REM
REM----------------------------------------------------------
 50020 REM----- DISPLAY MULTIPLE DISTRIBUTION ACCOUNTS ------
REM----------------------------------------------------------
REM
dist.total=0
for f%=0 to pr1.max.dist.accts%-1
	trash%=fn.put% \
		(str$(emp.dist.acct%(f%+1)), dist.acct.field.1%+(f%*fields.per.dist.acct%))
	trash%=fn.put% \
		(str$(emp.dist.percent(f%+1)), dist.pct.field.1%+(f%*fields.per.dist.acct%))
	dist.total= dist.total+ emp.dist.percent(f%+1)
next f%
trash%=fn.put%(str$(dist.total) 	 ,total.field%)
RETURN
