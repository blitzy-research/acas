$include "ipycomm"
prgname$="EMPENT  DEC  20, 1979     "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  E  M	P  E  N  T
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------
REM
function.name$="EMPLOYEE ENTRY"
program$="EMPENT"
REM
REM------------------------------------
REM----- INCLUDED DATA STRUCTURES -----
REM------------------------------------
REM
$include "ipyconst"
$include "ipydmemp"
$include "ipydmhis"
REM
REM-------------------------------------------------------------------
REM----- PROGRAM SPECIFIC DATA STRUCTURES			 -----
REM----- EXCEPT EQUATES USING FUNCTION CALLS, WHICH CAN BE FOUND -----
REM----- FOLLOWING THE FUNCTION DEFINITION SECTION		-----
REM-------------------------------------------------------------------
REM
emp.rec%= 1
fields%=18
fld.term.date%=18
fld.startup%=  19
lit.startup1%= 39
lit.startup2%= 40
lit.startup3%= 41

dim status$(3)
status$(1)= "ACTIVE"
status$(2)= "ON LEAVE"
status$(3)= "TERMINATED"

dim emsg$(50)
emsg$(01)="PY131  THIS PROGRAM MODULE MUST BE SELECTED FROM THE PAYROLL MENU"
emsg$(02)="PY132  DOUBLE QUOTES ("") ARE INVALID CHARACTERS"
emsg$(03)="PY133  ONLY INTEGERS ARE ACCEPTED AT THIS FIELD"
emsg$(04)="PY134  THAT'S NOT AN ACCEPTABLE NUMERIC FORMAT FOR THIS FIELD"
emsg$(05)="PY135  VALID DATES ARE THE ONLY ACCEPTABLE ENTRIES AT THIS FIELD"
emsg$(06)="PY136  Y  OR  N  ARE THE ONLY ACCEPTABLE ENTRIES AT THIS FIELD"
emsg$(07)="PY137"
emsg$(08)="PY138  TYPE "" RUN "" TO CONTINUE, PRESS THE ESCAPE KEY TO STOP"
emsg$(09)="PY139  SYSTEM STARTUP DETECTED"
emsg$(10)="PY140  THERE IS NO EMPLOYEE FILE, BUT A HISTORY FILE EXISTS"
emsg$(11)="PY141  THE EMPLOYEE FILE IS INVALID OR IS A NULL FILE"
emsg$(12)="PY142  UNEXPECTED END OF FILE ON EMPLOYEE FILE"
emsg$(13)="PY143"
emsg$(14)="PY144"
emsg$(15)="PY145  UNABLE TO CREATE THE EMPLOYEE FILE - DISK WRITE-PROTECTED?"
emsg$(16)="PY146"
emsg$(17)="PY147"
emsg$(18)="PY148"
emsg$(19)="PY149"
emsg$(20)="PY150  THERE IS NO HISTORY FILE, BUT AN EMPLOYEE FILE EXISTS"
emsg$(21)="PY151  THE HISTORY FILE IS INVALID OR IS A NULL FILE"
emsg$(22)="PY152  UNABLE TO ADD THE HISTORY RECORD TO THE HISTORY FILE"
emsg$(23)="PY153"
emsg$(24)="PY154"
emsg$(25)="PY155  UNABLE TO CREATE THE HISTORY FILE - DISK WRITE-PROTECTED?"
emsg$(26)="PY156"
emsg$(27)="PY157"
emsg$(28)="PY158"
emsg$(29)="PY159"
emsg$(30)="PY160  UNABLE TO UPDATE THE SECOND PARAMETER FILE"
emsg$(31)="PY161  ERROR DURING FILE SAVE"
emsg$(32)="PY162"
emsg$(33)="PY163"
emsg$(34)="PY164"
emsg$(35)="PY165"
emsg$(36)="PY166"
emsg$(37)="PY167"
emsg$(38)="PY168"
emsg$(39)="PY169  THE SECOND PARAMETER FILE DOES NOT EXIST OR IS NULL"
emsg$(40)="PY170"
emsg$(41)="PY171  THAT'S NOT A VALID CONTROL RESPONSE"
emsg$(42)="PY172  THERE AREN'T THAT MANY EMPLOYEES ON THE SYSTEM"
emsg$(43)="PY173  THAT'S NOT A VALID EMPLOYEE NUMBER"
emsg$(44)="PY174  SOCIAL SECURITY NUMBERS MUST BE OF THE FORMAT 000-00-0000"
emsg$(45)="PY175  THE ONLY THING I KNOW ABOUT SEX IS   M  OR  F"
emsg$(46)="PY176  EMPLOYEE STATUS CAN BE  A(ACTIVE) L(ON LEAVE) T(TERMINATED)"
emsg$(47)="PY177"
emsg$(48)="PY178"
emsg$(49)="PY179"
emsg$(50)="PY180  THAT'S AN UNUSED EMPLOYEE NUMBER"

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
$include "znumber"
$include "zparse"
$include "zstring"
$include "zeditdte"
$include "zdateio"
$include "zckdigit"
$include "zdspyorn"
$include "zdms"
$include "zdmstest"
$include "zdmsclr"
REM
REM----------------------------------------------
REM----- DATA STRUCTURES THAT USE FUNCTIONS -----
REM---------------------------------------------
pr2.file.name$= \
    fn.file.name.out$(pr2.name$,"101",common.drive%,password$,params$)
emp.file.name$= \
    fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,password$,param$)
his.file.name$= \
    fn.file.name.out$(his.name$,"101",pr1.his.drive%,password$,param$)
REM
REM-----------------------------------------------------
REM-----	      PROGRAM STARTUP		   -----
REM-----	 CHECK INITIALIZATION FLAG	   -----
REM-----   ENSURE THAT THE PR2 FILE IS AVAILABLE   -----
REM----- SET UP SCREEN, DISPLAY BACKGROUND	   -----
REM----- GET THE EMPLOYEE MASTER AND HISTORY FILES -----
REM----- BY OPEN FOLLOWED BY HEADER READ   OR	   -----
REM----- BY CREATE FOLLOWING CONFIRMATION	   -----
REM-----------------------------------------------------
REM
if not chained.from.root%  then \
	trash%=fn.emsg%(01): \
	goto 999.1				rem error exit

if size(pr2.file.name$)=0\
	then  trash%=fn.emsg%(39): \
	goto 999.1				rem error exit

REM
REM----- SCREEN DEFINITION INCLUDE --------------------
REM
$include "fpyemp"

trash%= fn.put.all%(false%)

gosub 51000			rem open emp, his files

if (his.exists% and not emp.exists%) then \
	trash%=fn.emsg%(10):error%= true%: goto 990	rem if only one of the
if (emp.exists% and not his.exists%) then \		rem two files exists
	trash%=fn.emsg%(20):error%= true%: goto 990	rem then error exit

while not his.exists% and not emp.exists%
	REM
	REM----- SYSTEM STARTUP  CREATE EMP, HIS FILES ------
	REM
	trash%= fn.emsg%(09)
	trash%= fn.lit%(lit.startup1%)
	trash%= fn.lit%(lit.startup2%)
	trash%= fn.lit%(lit.startup3%)
	continue%= false%
	while not continue%
		trash%= fn.get%(1, fld.startup%)
		if in.status%=req.stopit% \
		    then 999.2		rem they don't want to create the files
		if in.uc$= "RUN" then continue%= true% \
				 else trash%= fn.emsg%(08)
	wend
	gosub 60000	rem create his, emp files
	if error%  then 990			rem couldn't create them
	trash%= fn.clr%(lit.startup1%)
	trash%= fn.clr%(lit.startup2%)
	trash%= fn.clr%(lit.startup3%)
wend

if end #emp.file%  then 1011		rem exit on no emp header record
read #emp.file%, 1; \
$include "ipyemphdr"

if end #his.file%  then 1021		rem exit on no his header record
read #his.file%, 1; \
$include "ipyhishdr"

REM
REM----------------------------------------------------------------
REM-----		   MAIN ROUTINE 		      -----
REM----- ADD RECORDS TO THE EMPLOYEE MASTER AND HISTORY FILES -----
REM----- OR EXAMINE EMPLOYEE DEMOGRAPHIC INFORMATION IN THE   -----
REM----- EMPLOYEE MASTER FILE				      -----
REM----------------------------------------------------------------
REM
100 REM-----
while true%
    if pr1.debugging% then trash%=fn.msg%("BYTES FREE "+str$(fre))

    changing%=false%
    REM------------------------------------------------------------------------
    REM----- LOOP UNTIL A PRIMARY CONTROL RESPONSE INDICATES STOP WANTED, -----
    REM----- ADDING WANTED OR (RECORD READ AND CHANGES WANTED)		  -----
    REM------------------------------------------------------------------------
    while not adding% and not changing%
	trash%=fn.get%(4, 1 )
	if in.status%=req.valid% \
		then gosub  220 \		--- check employee number
		else gosub  200 		rem check primary controls
	if stopit%  \
	    then  trash%=fn.msg%("STOP REQUESTED"): goto 900
	if error%  \
		then  trash%=fn.emsg%(31): \
		goto 990	rem exit on error from file save
	REM
	REM----- READ AND DISPLAY A RECORD ------
	REM
	if rec.wanted%	then \
		gosub 50820: \
		record.read%=true%
	if error% then 990			rem unexpected eof on emp read
	if record.read% and emp.status$="D" \   rem can't modify unused records
		then record.read%=false%: \
		trash%=fn.emsg%(50)
	if rec.wanted% and record.read% \
		then gosub 50000		rem display emp record
    wend
    REM
    REM----- IF ADDING RECORDS GET A RECORD NUMBER, SET DEFAULTS
    REM
    if adding%	\
	then gosub 50200: \	--- get record number, set defaults
	     nothing.entered%= true% rem exit adding only when nothing entered
    if error%	then 990		rem eof on reading next del rec
    REM 					--- ALL CONTROL CHARACTERS
    REM----- LOOP UNTIL USER DONE OR CANCELS	--- HANDLED BY CONTROL CHAR
    REM 					--- SUBROUTINE
    field%= 2					REM ALL DATA EDITSUBROUTINES
    done%=false%				REM PASS A STRING BACK IN OUT$
    write.needed%=true% 		REM TO BE DISPLAYED, AND
							    REM PASS ANY ERROR MESSAGE
    while not done%				REM BACK IN MSG$
	invalid.data%=false%
	trash%=fn.get%(3, field%)
	if in.status%= req.valid% \
		then nothing.entered%= false%: \ --- disable exit adding mode
		     on field%-1  gosub \ --- data edit
			5002,	\
			5003,	\
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
			5018:	\
			trash%=fn.put%(out$, field%) \
		else  gosub 250 	rem check control responses

	if invalid.data% \
		then trash%= fn.emsg%(msg%)
	selected%= false%
	while not selected% and not done% and not invalid.data%
		if in.status%= req.cr%	or in.status%= req.valid% \
			then field%= field%+ 1
		if in.status%= req.back% then field%= field%-1
		if field%< 2 then field%= fields%
		if field%> fields% then field%= 2
		if fn.test%(crt.used%, field%) then selected%= true%
	wend
    wend
    REM
    REM----- WRITE RECORDS IF NEEDED ----------------------------
    REM
    if not write.needed% then 100	rem top of loop

    if adding% and add.to.end% \			--- on adding a new
      then  emp.hdr.no.recs%=emp.hdr.no.recs%+1 	rem record to the emp

    if adding% and not add.to.end% \			--- on recycling
      then emp.hdr.no.del.recs%=emp.hdr.no.del.recs%-1:\--- unused existing
	emp.hdr.next.del.rec%=next.del% 		rem emp and his records

    gosub 50830 				rem write employee record
    if error% then 990				rem unexpected eof on emp

    if adding% \
	then his.hdr.no.recs%=emp.hdr.no.recs%: \
	his.rec%=emp.rec%: gosub 50730		rem write history record
    if error% then 990				rem unexpected eof on his
wend

200 REM----- PRIMARY CONTROL RESPONSES ------------------
rec.wanted%=false%
if in.status%=req.cr% and record.read%	then changing%= true%: RETURN
if in.status%=req.adding% \
	then trash%=fn.msg%("ADDING EMPLOYEE MASTER AND HISTORY RECORDS"): \
	     adding%=true%: record.read%=false%: RETURN
if in.status%=req.back% and emp.hdr.no.recs%>0 \
	then gosub 201: rec.wanted%=true%: RETURN
if in.status%=req.next% and emp.hdr.no.recs%>0 \
	then gosub 202: rec.wanted%=true%: RETURN
if in.status%=req.save% then gosub 61000: RETURN
if in.status%=req.stopit% then stopit%=true%: RETURN
trash%= fn.emsg%(41)
RETURN

201 REM----- GET PREVIOUS RECORD -----
emp.rec%=emp.rec%-1
if emp.rec%<2 then emp.rec%=emp.hdr.no.recs%+1
RETURN
202 REM----- GET NEXT RECORD -----
emp.rec%=emp.rec%+1
if emp.rec%>emp.hdr.no.recs%+1 then emp.rec%=2
RETURN

220 REM----- CHECK EMPLOYEE NUMBER FOR VALIDITY --------------
rec.wanted%=false%
if not fn.num%(in$) or len(in$)<>5 or fn.ck.dig$(left$(in$,4))<>right$(in$,1) \
	then trash%=fn.emsg%(43): RETURN

emp.rec%=val(left$(in$, 4))+1
invalid.data%=false%
if emp.rec% < 2  or  emp.rec% > emp.hdr.no.recs%+ 1 \
	then invalid.data%=true%: trash%= fn.emsg%(42): RETURN
rec.wanted%=true%
RETURN

250 REM----- CHECK SECONDARY CONTROL CHARACTERS --------------
if in.status%=req.cr%  or  in.status%=req.back%  \
	then RETURN
if in.status%=req.cancel%   \
	then done%=true%: record.read%=false%: write.needed%=false%: RETURN

if in.status%=req.stopit% and field%=2 and adding% and nothing.entered% \
	then trash%=fn.msg%("EXIT ADDING MODE"): \
	     adding%=false%: write.needed%=false%: done%=true%: RETURN

if in.status%=req.stopit% then done%=true%: RETURN
invalid.data%=true%
msg%= 41
RETURN

REM
REM--------------------------------------
900 REM----- STOP REQUESTED BY USER -----
REM--------------------------------------
REM
gosub 51900	rem update header records

if error% then trash%=fn.emsg%(32): goto 990

gosub 53000			rem update pr2 file

if error% then trash%=fn.emsg%(30)

REM
REM---------------------------------------------
990 REM----- CLOSE ANY OPEN FILES AND EXIT -----
REM---------------------------------------------
REM
if emp.exists% then close emp.file%
if his.exists% then close his.file%

if error% then 999.1

$include  "zeoj"
REM
REM------------------------------------------------------
REM----- END OF FILE CONDITIONS FROM MAIN LINE CODE -----
REM------------------------------------------------------
REM
1011 REM----- EXIT IF UNABLE TO READ EMPLOYEE HEADER RECORD -----
trash%=fn.emsg%(11)
error%= true%
goto 990

1021 REM----- EXIT IF UNABLE TO READ HIS HEADER RECORD ---------
trash%=fn.emsg%(21)
error%= true%
goto 990
REM
REM-----------------------------------------
REM----- GENERAL DATA EDIT SUBROUTINES -----
REM-----------------------------------------
REM
2010 REM----- MATCH QUOTES -----
if match(quote$, in$, 1) \
	then msg%= 02: invalid.data%=true%
RETURN

2030 REM----- EDIT DATE -----
if fn.edit.date%(in$) \
	then in$=fn.date.in$ \
	else msg%= 05: invalid.data%=true%
RETURN

REM
REM----------------------------------------------------------
REM----- DATA EDIT SUBROUTINES THAT AREN'T GENERALIZED ------
REM----- AND EMPLOYEE RECORD FIELD UPDATES	       ------
REM----------------------------------------------------------
REM
5002 REM----- EMPLOYEE NAME ------
gosub 2010
if not invalid.data% \
	then emp.emp.name$=in$
out$=emp.emp.name$
RETURN

5003 REM----- EMPLOYEE ADDRESS LINE 1 -----
gosub 2010
if not invalid.data% \
	then emp.addr1$=in$
out$=emp.addr1$
RETURN

5004 REM----- EMPLOYEE ADDRESS LINE 2 -----
gosub 2010
if not invalid.data% \
	then emp.addr2$=in$
out$=emp.addr2$
RETURN

5005 REM----- CITY -----
gosub 2010
if not invalid.data% \
	then emp.city$=in$
out$=emp.city$
RETURN

5006 REM----- STATE -----
gosub 2010
if not invalid.data% \
	then emp.state$=in.uc$
out$=emp.state$
RETURN

5007 REM----- ZIP CODE -----
gosub 2010
if not invalid.data% \
	then emp.zip$=in$
out$=emp.zip$
RETURN

5008 REM----- PHONE NUMBER -----
gosub 2010
if not invalid.data% \
	then emp.phone$=in$
out$=emp.phone$
RETURN

5009 REM----- SOCIAL SECURITY NUMBER -----
dashes%=fn.parse%(in$, "-")
digit$=token$(1) + token$(2) + token$(3)
if dashes%<> 3 or not fn.num%(digit$) \
    or len(token$(1))<> 3 or len(token$(2))<> 2 or len(token$(3))<>4 \
	then msg%= 44: invalid.data%=true% \
	else emp.ssn$=in$
out$=emp.ssn$
RETURN

5010 REM----- BANK ACCOUNT NUMBER -----
gosub 2010
if not invalid.data% \
	then emp.bank.acct.no$=in$
out$=emp.bank.acct.no$
RETURN

5011 REM----- BIRTH DATE -----
gosub 2030
if not invalid.data% \
	then emp.birth.date$=fn.date.in$
out$=fn.date.out$(emp.birth.date$)
RETURN

5012 REM----- SEX (YES OR NO) -----
if match(in.uc$, "MF", 1)\
	then emp.sex$=in.uc$ \
	else msg%= 45: invalid.data%=true%
out$=emp.sex$
RETURN

5013 REM----- PENSION USED -----
posit%= match(in.uc$, "YN", 1)
if posit%= 1 then emp.pension.used%=true%
if posit%= 2 then emp.pension.used%=false%
if posit%= 0 \
	then msg%= 06: invalid.data%=true%
out$=fn.dsp.yorn$(emp.pension.used%)
RETURN

5014 REM----- JOB CODE -----
gosub 2010
if not invalid.data% \
	then emp.job.code$=left$(in.uc$+blank$, 3)
out$=emp.job.code$
RETURN

5015 REM----- TAXING STATE -----
gosub 2010
if not invalid.data% \
	then emp.taxing.state$=left$(in.uc$+blank$, 2)
out$=emp.taxing.state$
RETURN

5016 REM----- START DATE -----
gosub 2030
if not invalid.data% \
	then emp.start.date$=fn.date.in$
out$=fn.date.out$(emp.start.date$)
RETURN

5017 REM----- EMPLOYMENT STATUS -----
posit%= match(in.uc$, "ALT", 1)
if posit%> 0 and in.len%= 1 \
	then emp.status$=in.uc$ \
	else msg%= 46: invalid.data%=true%: \
	     posit%= match(emp.status$, "ALT", 1)
if emp.status$= "T" and not invalid.data% \
    then  emp.term.date$= common.date$: \
    trash%= fn.put%(fn.date.out$(emp.term.date$),fld.term.date%)
out$=status$(posit%)
RETURN

5018 REM----- TERMINATION DATE -----
gosub 2030
if not invalid.data% \
	then emp.term.date$=fn.date.in$
if in.uc$="NONE" \
	then emp.term.date$="000000": invalid.data%= false%
if emp.term.date$="000000" \
	then out$= null$ \
	else out$=fn.date.out$(emp.term.date$)
RETURN

50000 REM----- DISPLAY AN EMPLOYEE MASTER RECORD --------------
trash%=fn.put%(     emp.no$		 , 1)
trash%=fn.put%(     emp.emp.name$	 , 2)
trash%=fn.put%(     emp.addr1$		 , 3)
trash%=fn.put%(     emp.addr2$		 , 4)
trash%=fn.put%(     emp.city$		 , 5)
trash%=fn.put%(     emp.state$		 , 6)
trash%=fn.put%(     emp.zip$		 , 7)
trash%=fn.put%(     emp.phone$		 , 8)
trash%=fn.put%(     emp.ssn$		 , 9)
trash%=fn.put%(     emp.bank.acct.no$	 ,10)
trash%=fn.put%(fn.date.out$(emp.birth.date$), 11)
trash%=fn.put%(     emp.sex$		 ,12)
trash%=fn.put%(fn.dsp.yorn$(emp.pension.used%)	 ,13)
trash%=fn.put%(     emp.job.code$	 ,14)
trash%=fn.put%(fn.date.out$(emp.start.date$),16)
trash%=fn.put%(     status$(match(emp.status$, "ALT", 1)), 17)
if emp.term.date$="000000" \
	then out.date$= null$ \
	else out.date$= fn.date.out$(emp.term.date$)
trash%=fn.put%(out.date$,18)
RETURN
REM
REM---------------------------------------------------------------
50200 REM-----	   GET NEXT AVAILABLE RECORD NUMBER	     -----
REM-----  CHECK INTERNAL FILE LINKAGE FOR UNUSED RECORDS     -----
REM-----	SET DEFAULT VALUES FOR HIS, EMP 	     -----
REM---------------------------------------------------------------
REM
add.to.end%=false%
if emp.hdr.no.del.recs%<=0 \
	then emp.rec%=emp.hdr.no.recs%+2:\
		add.to.end%=true%: \
	else emp.rec%=emp.hdr.next.del.rec%+1 :\
		gosub 50820		rem read employee file

if error% then RETURN			rem eof on employee file read

next.del%=emp.next.del%
emp.next.del%=0

emp.no$=right$("0000"+str$(emp.rec%-1), 4)
emp.no$=emp.no$+fn.ck.dig$(emp.no$)
his.emp.no$=emp.no$		rem this the only history field that's non-zero

emp.status$		="A"
emp.hs.type$		=pr1.default.hs.type$
emp.pay.interval$	=pr1.default.pay.interval$
emp.taxing.state$	="  "
emp.job.code$		="   "
emp.start.date$ 	=common.date$
emp.birth.date$ 	="000000"
emp.term.date$		="000000"
emp.sex$		="N"
emp.marital$		="S"
emp.ssn$		="   -  -    "
if emp.pay.interval$= "W" or emp.pay.interval$= "B" \
  then emp.cur.apply.no%= pr2.last.wb.apply.no%: \
	   emp.pay.freq%= 52 \
  else emp.cur.apply.no%= pr2.last.sm.apply.no%: \
	   emp.pay.freq%= 24
if emp.pay.interval$= "B" or emp.pay.interval$= "M" \
	then emp.pay.freq%= emp.pay.freq%/2
emp.emp.name$		=null$
emp.phone$		=null$
emp.addr1$		=null$
emp.addr2$		=null$
emp.city$		=null$
emp.state$		=null$
emp.zip$		=null$
for f%= 1 to 4
	emp.rate(f%)	= 0
next f%
emp.rate(1)		=pr1.default.pay.rate
if emp.hs.type$= "H" \
	then emp.rate(2)=pr1.default.pay.rate*pr1.rate2.factor: \
	     emp.rate(3)=pr1.default.pay.rate*pr1.rate3.factor
emp.auto.units		=0
emp.normal.units	=pr1.default.norm.units
emp.max.pay		=emp.rate(1)*pr1.max.pay.factor*emp.normal.units
emp.rate4.exclusion%	=pr1.rate4.exclusion.type%
emp.eic.used%		=false%
emp.cal.head.of.house%	=false%
emp.cal.ded.allow%	=0
emp.fwt.allow%		=0
emp.swt.allow%		=0
emp.lwt.allow%		=0
emp.pension.used%	=false%
emp.bank.acct.no$	=null$
emp.fwt.exempt% 	=false%
emp.swt.exempt% 	=false%
emp.lwt.exempt% 	=false%
emp.fica.exempt%	=false%
emp.sdi.exempt% 	=false%
for f%= 1 to pr1.max.sys.eds%
    emp.sys.exempt%(f%) =false%
next f%
emp.vac.rate		=pr1.default.vac.rate
emp.vac.accum		=0
emp.vac.used		=0
emp.sl.rate		=pr1.default.sl.rate
emp.sl.accum		=0
emp.sl.used		=0
emp.comp.accum		=0
emp.comp.used		=0
for f%= 1 to pr1.max.dist.accts%
	emp.dist.acct%(f%)=pr1.default.dist.acct%
	emp.dist.percent(f%)=0
next
emp.dist.percent(1)=100.0
for f%= 1 to pr1.max.emp.eds%
	emp.ed.desc$(f%)	=null$
	emp.ed.factor(f%)	=0
	emp.ed.limit(f%)	=0
	emp.ed.earn.ded$(f%)	="D"
	emp.ed.exclusion%(f%)	=1
	emp.ed.amt.percent$(f%) ="A"
	emp.ed.limit.used%(f%)	=false%
	emp.ed.chk.cat%(f%)	=0
	emp.ed.acct.no%(f%)	=pr1.default.dist.acct%
next f%

gosub 50000		rem display some of this
RETURN

REM
REM--------------------------------------------
REM----- EMPLOYEE HISTORY FILE DATA WRITE -----
REM--------------------------------------------
REM
50709 REM----- UNEXPECTED EOF ON HISTORY FILE -----
REM
trash%=fn.emsg%(22)
error%=true%
RETURN

REM
50730 REM----- HISTORY FILE WRITE -----
REM
if end #his.file% then 50709
print #his.file%, his.rec%; \
$include "ipyhis"
RETURN

REM
REM----------------------------------------------------
REM----- EMPLOYEE MASTER FILE DATA READ AND WRITE -----
REM----------------------------------------------------
REM
50809 REM----- UNEXPECTED EOF ON EMPLOYEE FILE -----
REM
error%=true%
trash%=fn.emsg%(12)
RETURN

REM
50820 REM----- EMPLOYEE FILE READ -----
REM
if end #emp.file% then 50809
read #emp.file%, emp.rec%; \
$include "ipyemp"
RETURN

REM
50830 REM----- EMPLOYEE FILE WRITE -----
REM
if end #emp.file% then 50809
print #emp.file%, emp.rec%; \
$include  "ipyemp"
RETURN

REM
REM-----------------------------------------------------
51000 REM----- OPEN EMPLOYEE MASTER, HISTORY FILES -----
REM-----------------------------------------------------
REM
emp.exists%=false%
his.exists%=false%
if end #emp.file%  then  51010			rem open his file
open	emp.file.name$ \
	recl	emp.len% \
	as	emp.file%
emp.exists%=true%		rem local flag that employee file exists

51010 REM----- OPEN HISTORY FILE ------------------
if end #his.file% then 51019	rem ensure borh emp and his files present
open	his.file.name$ \
	recl	his.len% \
	as	his.file%
his.exists%=true%			rem local flag if his file exists
RETURN

51019 REM----- NO HISTORY FILE -----
RETURN

REM
REM------------------------------------------------
51900 REM----- UPDATE EMP, HIS HEADER RECORDS -----
REM------------------------------------------------
REM
if end #emp.file% then 51909	rem set error flag
print #emp.file%, 1; \
$include "ipyemphdr"

if end #his.file% then 51909	rem set error flag
print #his.file%, 1;\
$include "ipyhishdr"
RETURN

51909 REM----- ERROR ON HEADER RECORD UPDATE -----
error%=true%
RETURN

REM
REM----------------------------------------------
53000 REM----- UPDATE SECOND PARAMETER FILE -----
REM----------------------------------------------
REM
pr2.exists%=false%
if end #pr2.file% then 53030	rem set error flag if bad update
open	pr2.file.name$ \
	as pr2.file%
if end #pr2.file% then 53033	rem close pr2 and set error flag

pr2.no.employees%=emp.hdr.no.recs%
pr2.no.active.emps%=emp.hdr.no.recs%- emp.hdr.no.del.recs%

print #pr2.file%;\
$include "ipypr2"
close pr2.file%
RETURN

53030 REM----- BAD SECOND PARAMETER FILE UPDATE -----
error%=true%
RETURN

53033 REM----- BAD UPDATE
close pr2.file%
error%=true%
RETURN

REM
REM-------------------------------------------------------------
60000 REM------ CREATE EMPLOYEE MASTER AND HISTORY FILES -------
REM-----	     WRITE A HEADER FOR EACH		 -------
REM-------------------------------------------------------------
REM
if end #emp.file% then 60015		rem error if unable to create emp file
create	emp.file.name$ \
	recl	emp.len% \
	as	emp.file%
emp.exists%=true%		rem local flag that employee file exists

if end #his.file% then 60025		rem error if unable to create his file
create his.file.name$ \
	recl	his.len% \
	as	his.file%
his.exists%=true%		rem local flag that history file exists

gosub 51900			rem print header records

RETURN

60015 REM----- ERROR IF UNABLE TO CREATE EMP FILE ------
trash%=fn.emsg%(15)
error%=true%
RETURN

60025 REM----- ERROR IF UNABLE TO CREATE HIS FILE ------
trash%=fn.emsg%(25)
error%=true%
RETURN

REM
REM---------------------------------------------
61000 REM-----	      SAVE FILES	   -----
REM-----  EMPLOYEE MASTER, HISTORY, FILES, -----
REM-----     AND SECOND PARAMETER FILE	   -----
REM---------------------------------------------
REM
trash%= fn.msg%("SAVING FILES")

close emp.file%
close his.file%

gosub 51000			rem open emp, his files

if not emp.exists% or not his.exists% \
	then error%=true%: RETURN

gosub 51900				rem header record update

if error% then RETURN

gosub 53000				rem update pr2 file

trash%= fn.msg%(str$(emp.hdr.no.recs%)+" RECORDS SAVED")
RETURN
