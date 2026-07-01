#include "ipycomm"
prgname$="PYACTENT     10-JAN-80"
#include "ipyconst"

REM----------------------------------------------------------------------
REM
REM
REM		E N T R Y
REM
REM		(PYACTENT)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "ACCOUNT ENTRY"

REM
REM	GUIDE TO SUBROUTINES IN PYACTENT
REM
REM	21	BY FIELD NUMBER SELECT VALIDATION ROUTINE
REM	22	GET SET FOR NEXT FIELD
REM	24	GET SET FOR PREVIOUS FIELD
REM
REM	100	DISPLAY ALL DATA FIELDS
REM	101-103 DISPLAY FIELDS 1-3
REM
REM	201	CHECK VALIDITY OF KEY FIELD
REM	201.100 DATA INPUT TO KEY FIELD
REM	201.200 GO BACK ONE RECORD
REM	201.300 GO FORWARD ONE RECORD
REM
REM	202-203 CHECK VALIDITY OF DATA FIELDS
REM
REM	400	INIT AND DISPLAY ALL FIELDS FOR ADDING MODE
REM	500	FILE DOES NOT EXIST SO ASK USER TO CONFIRM BEFORE CREATING
REM
REM	600	READ CURRENT RECORD
REM	610	WRITE CURRENT RECORD
REM	620	WRITE HEADER RECORD
REM	630	UPDATE PR2 FILE
REM	640	SWITCH DISKS TO OBTAIN GL CHART OF ACCOUNTS FILE
REM	650	RETURN DISKS TO ORIGINAL CONFIGURATION
REM
REM	700	CREATE DEFAULT ACCOUNT FILE
REM
REM	900	DO FINAL CONSISTANCY CHECKS AND WRITE OUT RECORD IF OK

rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------
#include "zdms"
#include "zdmstest"
#include "zdmsclr"
#include "zdmsconf"
#include "zdmsabrt"
#include "zdmsused"

#include "znumeric"
#include "zstring"
#include "zdateio"
#include "zdspyorn"
#include "zfilconv"


REM
REM	SPECIAL FUNCTIONS TO CHECK VALIDITY OF GL ACCOUNT NUMBERS
REM

def fn.read.coa.rand%(record%)
	fn.read.coa.rand%=false%
	read #gld.file%,record%; \
		COA.CO.NO$,\
		COA.DEPT.NO$,\
		COA.ACCT.NO$,\
		COA.ACCT.NAME$
	coa.acct$=coa.acct.no$+coa.dept.no$
	fn.read.coa.rand%=true%
.009	return
fend

def fn.gl.acct.lookup%(acct$)
	fn.gl.acct.lookup%=true%
	if not pr1.gl.used% then return
	lower%=0:upper%=no.coa.recs%+1
	while upper%-lower%>1
		hit%=int((upper%-lower%)/2)+lower%
		trash%=fn.read.coa.rand%(hit%)
		if acct$>coa.acct$ \
			then   lower%=hit% \
			else   upper%=hit%
		if acct$=coa.acct$ then \
			fn.gl.acct.lookup%=true%:return
	wend
	fn.gl.acct.lookup%=false%
	return
fend

def fn.good.acct%(in$)
	acct$=in$
	fn.good.acct%=false%
	if pr1.gl.used% and len(acct$) > 6 \
	   then \
		return
	if pr1.gl.used% and len(acct$) < 6 \
	   then \
		acct$ = left$(acct$+"000000",6)

	if not fn.num%(acct$) then return
	if mid$(acct$,4,1)="0" then return
	if not fn.gl.acct.lookup%(acct$) then return
	fn.good.acct%=true%
	return
fend

#include "ipystat"


rem
rem	error messages
rem
	dim emsg$(30)
	emsg$(1) = "     PY451 INVALID RESPONSE"
	emsg$(2) = "     PY452 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY453 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY454 UNEXPECTED END OF ACCOUNT FILE"
	emsg$(5) = "     PY455 RECORD INFORMATION IS NOT VALID"
	emsg$(6) = "     PY456 INVALID RECORD NUMBER"
	emsg$(9) = "     PY459 CHART OF ACCOUNTS FILE NOT FOUND,INSERT CORRECT DISK"
	emsg$(10)= "     PY460 UNEXPECTED END OF CHART OF ACCOUNTS FILE"
	emsg$(11)= "     PY461 INVALID ACCOUNT NUMBER"
	emsg$(12)= "     PY462 MISSING PR2 FILE, NOT UPDATED"
	emsg$(13)= "     PY463 ACCOUNT FILE NOT PRESENT,INSERT CORRECT DISK"



program$ = "PYACTENT"
if pr2.no.acts% = 0 then pr2.no.acts% = 4
if gld.file% = 0 then gld.file% = 20
if gld.len% = 0 then gld.len% = 51

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2


rem
rem	get screen set up
rem

#include "fpyacte"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	lit.place% = 13
	lit.replace% = 14.
	lit.type% = 15.
	fld.gld.drive% = 4
	fld.cont.response% = 5

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP


REM
REM	SWITCH DISKS TO OBTAIN CHART OF ACCOUNTS
REM

	if match(default$,common.chaining.status$,1) = 0 \
	   then \	REM NO DISK SWITCHING IN DEFAULT STARTUP
		gosub 640	REM GO SWITCH DISK

REM
REM	IF IN STARTUP CREATE DEFAULT ACCOUNT FILE
REM

	created.act.file% = false%	REM FLAG AS TO WHETHER PROGRAM CREATED
					REM THE ACCOUNT FILE,SET TO TRUE
					REM IN SUBROUTNE 700 CREATE DEFAULT ACT
	if match(startup$,common.chaining.status$,1) <> 0 and \
	size(fn.file.name.out$(act.name$,"101",pr1.act.drive%,nul$,nul$))=0 \
	   then \
		gosub 700	REM CREATE DEFAULT ACCT FILE

REM
REM	CREATE ACCOUNT FILE IF NOT PRESENT
REM

	if (size(fn.file.name.out$(act.name$,"101",pr1.act.drive%,nul$,nul$))=0)\
		and not created.act.file% \
	   then \
		gosub 500    REM CREATE DEFAULT ACCT FILE AFTER USER CONFIRMS

rem
rem	open ACT file
rem

	if end #act.file% then 998
	if not created.act.file% \
	   then \
	      open fn.file.name.out$(act.name$,"101",pr1.act.drive%,nul$,nul$)\
		recl act.len% as act.file%

rem
rem	file exists so read in header and proceed
rem

	read #act.file% ,1;	\
#include "ipyacthd"

REM
REM	IF IN DEFAULT STARTUP NO MORE NEED BE DONE
REM

	if match(default$,common.chaining.status$,1) <> 0 \
	   then \
		gosub 630 :\	REM UPDATE PR2 FILE
		goto 10 	REM GO DECIDE WHERE TO CHAIN TO



rem
rem	initialise flags and current record
rem
	record.data.valid% = false%	rem flag to indicate if current record
					rem data is valid
	act.current.record.no% = 1	rem init current record number
	key.field% = 1			rem init key field
	first.data.field% = 2		rem init first data field
	last.data.field% = 3
	data.field.count% = 3


REM
REM	THROW RECORD LITERALS ONTO SCREEN
REM

	for i% = 10 to 12
		trash% = fn.lit%(i%)
	next i%

REM
REM	READ IN FIRST RECORD AND DISPLAY
REM
	gosub	600	REM READ ACCOUNT
	gosub	100	REM DISPALY ACCOUNT


REM
REM	MAIN INPUT DRIVER
REM
	field% = key.field%	rem start input driver at key field
	stopit% = false%
while not stopit%
rem
rem	handle key (record number) field seperately
rem
	if field% = key.field%	\
	   then \
		gosub 201	REM HANDLE KEY FIELD
	if stopit% \
	   then goto 10 REM DONE GO DECIDE WHERE TO CHAIN TO

REM
REM	DATA FIELD INPUT
REM
	if field% <> key.field% then \
		trash% = fn.get%(3,field%)
	ok% = true%	rem set flag that response is valid
REM
REM	IF VALID DATA RETURNED CHECK IT,ELSE TAKE CONTROL ACTION
REM
	if in.status% = req.valid% \
	   then gosub 21		REM GO CHECK DATA

	if in.status% = req.cr% \
	   then gosub 22	rem proceed to next field

	if in.status% = req.back% \
	   then gosub 24	rem proceed to previous field

	if in.status% = req.cancel% \
	     or (first.time.flag% and in.status% = req.stopit%) \
	   then \	rem exit from record without updateing
		field% = key.field%	:\ rem key field
		record.data.valid% = false%	:\
		while in.adding%	:\
			in.adding% = false% :\
			act.current.record.no%=act.current.record.no%-1 :\
			gosub 600	:\	REM READ IN RECORD
			gosub 100 :\	REM DISPLAY ALL FIELDS OF RECORD
		wend

	if in.status% = req.stopit% and not first.time.flag% \
	   then \
		gosub 900 \	rem do final validity check
	   else \
		first.time.flag% = false%
wend
REM
REM	DECIDE WHERE TO CHAIN TO
REM
 10	if match(startup$,common.chaining.status$,1) <> 0 \
	   then \
		trash% = fn.msg%("     "+function.name$+" COMPLETED") :\
		chain fn.file.name.out$("dedent",null$,0,null$,null$) \
	   else \
		goto 999	REM NORMAL EXIT


rem
rem	by field number select validation routine
rem

 21
	on field% gosub 	\ rem pick data checker by field
		201,	\rem first field should be handled seperately
		202,	\
		203

	if ok%	\
	   then gosub 22	REM PROCEED TO NEXT FIELD
	return



rem
rem	get set for next field
rem

 22	\
	field% = field% + 1
	if field% > crt.field.count%	\
	   then field% = 1	REM GET FIRST FIELD IF PAST LAST FIELD

	if field% = key.field% \
	   then goto 22 	REM SKIP PAST KEY FIELD
	if not fn.test%(crt.used%,field%) \
	   then goto 22 	REM SKIP PAST UNUSED FIELDS
	if not fn.test%(crt.io%,field%) \
	   then goto 22 	REM SKIP PAST OUTPUT ONLY FIELDS

	return			REM MAIN INPUT DRIVER

rem
rem	get set for previous field
rem

 24	\
	field% = field% - 1
	if field% < 1	\	REM GOTO LAST FIELD IF AT FIRST
		then field% = crt.field.count%

	if field% = key.field% \
	   then goto 24 	REM SKIP PAST KEY FIELD
	if not fn.test%(crt.used%,field%) \
	   then goto 24 	REM SKIP PAST UNUSED FIELDS
	if not fn.test%(crt.io%,field%) \
	   then goto 24 	REM SKIP PAST OUTPUT ONLY FIELDS

	return			REM MAIN INPUT DRIVER



rem
rem	subroutine to display all data fields
rem

 100
	gosub 101
	gosub 102
	gosub 103

	return



rem
rem	display of each individual field
rem

rem
rem	display record #
rem

 101
       trash%=fn.put%(right$(blank$+str$(act.current.record.no%),3),key.field%)
	return

 102
	trash% = fn.put%(act.no$,2)	REM ACCOUNT NUMBER
	return

 103
	trash% = fn.put%(act.desc$,3)	REM ACCOUNT NAME
	return



rem
rem	check validity of key field
rem

 201
	ok% = false%
while not ok%
	trash% = fn.get%(4,key.field%)

	if in.status% = req.valid% \
	   then gosub 201.100		REM GO CHECK RECORD NUMBER

	if in.status% = req.cr% \
	   then \
		field% = first.data.field%	:\	rem first data field
		record.data.valid% = true% :\	REM DATA FROM FILE IS VALID
		ok% = true%

	if in.status% = req.stopit%	\ rem exit with backup
	   then \
		trash% = fn.msg%("     STOP REQUESTED") :\
		gosub 620	:\	rem write header record
		gosub 630	:\	REM UPDATE PR2 FILE
		close act.file% :\
		gosub 650	:\	REM RETURN DISKS TO NORMAL PLACEMENT
		stopit% = true% :\
		in.status% = 0	:\	REM FAIL ALL OTHER STATUS TESTS
		ok% = true%

	if in.status% = req.cancel%	\ rem cancel
	   then \
		close act.file% :\
		gosub 650	:\	REM RETURN DISKETTES TO ORIGINAL PLACES
		stopit% = true% :\
		ok% = true%

	if in.status% = req.adding%	\ rem enter adding mode
	   then \
		act.current.record.no% = act.hdr.no.recs% + 1	:\ rem next available record
		gosub 400	:\	rem set default values
		field% = first.data.field%	:\	rem first data field
		first.time.flag% = true% :\	REM FLAG TO ALLOW EXIT FROM
				\REM ADDING MODE IN FIRST FIELD FIRST TIME
		record.data.valid% = false%	:\	rem data not validity checked
		in.adding% = true% :\
		ok% = true%

	if in.status% = req.save%	\ rem save current state
	   then \
		gosub 620	:\	rem write header record
		gosub 630	:\	rem write pr2 file
		ok% = true%

	if in.status% = req.back%	\ rem move one record back
	   then \
		in.adding% = false%	:\
		gosub 201.200		rem go one record back

	if in.status% = req.next%	\ rem go forward one record
	   then \
		gosub 201.300		rem go forward one field

wend
	return

rem
rem	data input to key field
rem

 201.100

	in.adding% = false%
	if not fn.num%(in$)	\
	   then \	rem is not valid record number
		trash% = fn.emsg%(6)	:\	REM INVALID RECORD NUMBER
		gosub 101	:\ rem redisplay current record number
		return

	if val(in$) > act.hdr.no.recs% or val(in$) < 1	\ rem record too small
	   then \				rem or too large
		trash% = fn.emsg%(6)	:\	REM INVALID RECORD NUMBER
		gosub	101	:\ rem redisplay old record number
		return

	act.current.record.no% = val(in$)
	gosub 600	rem read record in
	gosub 100	rem display record data
	record.data.valid% = true%	rem data is valid since from file
	return



rem
rem	subroutine go back one record
rem

 201.200
	if act.current.record.no% = 1	\ rem at first record
	   then \
		act.current.record.no% = act.hdr.no.recs% \
	   else \
		act.current.record.no% = act.current.record.no% - 1

	gosub 600	rem read record
	gosub 100	rem display record data
	record.data.valid% = true%	rem data from file is valid
	return

rem
rem	go forward one record
rem

 201.300
	if act.current.record.no% + 1 > act.hdr.no.recs% \ rem at last record
	   then \
		act.current.record.no% = 1 \
	   else \
		act.current.record.no% = act.current.record.no% + 1

	gosub 600	rem get data record
	gosub 100	rem display record data
	record.data.valid% = true%	rem data from file is valid
	return




 202	REM CHECK ACCOUNT NUMBER

	if fn.good.acct%(in$) \
	   then \
		act.no$ = left$(acct$ + blank$,6) :\
		record.data.valid% = true% :\
		ok% = true% \
	   else \
		ok% = false% :\
		trash% = fn.emsg%(11)	REM INVALID ACCOUNT NUMBER
	gosub 102	REM DISPLAY

	if ok% and pr1.gl.used% \
	   then \	REM SET ACCOUNT NAME TO BE FROM CHART OF ACCOUNTS FILE
		act.desc$ = coa.acct.name$ :\
		gosub 103	REM DISPLAY ACCOUNT NAME
	return

 203	REM CHECK ACCOUNT NAME

	act.desc$ = in$
	gosub 103	REM DISPLAY
	ok% = true%
	return



rem
rem	subroutine to initialise and display all data fields for adding
rem	mode
rem

 400
	act.no$ = null$
	act.desc$ = null$
	gosub	100	rem display all data fields
	return

REM
REM	ACCOUNT FILE DOES NOT EXIST SO ASK USER TO CONFIRM BEFORE CREATING
REM

 500
	trash% = fn.msg%("     ACCOUNT FILE DOES NOT EXIST,DEFAULT WILL BE CREATED")
	if not fn.confirmed% \
	   then \
		goto 999 \	REM USER DOES NOT WISH FILE CREATION
	   else \
		gosub 700	REM CREATE DEFAULT ACCOUNT FILE

	return



rem
rem	read current record
rem
 600
	read #act.file% , act.current.record.no% + 1;	\
#include "ipyact"
	return

rem
rem	write current record
rem
 610
	print#act.file% , act.current.record.no% + 1;	\
#include "ipyact"
	return

rem
rem	write header record
rem
 620
	print #act.file% , 1;	\
#include "ipyacthd"
	return

REM
REM	UPDATE PR2 FILE
REM
 630
	pr2.no.acts% = act.hdr.no.recs%
	if end #pr2.file% then 630.E1
	open fn.file.name.out$(pr2.name$,"101",common.drive%,null$,null$) \
	  as pr2.file%
	print #pr2.file%; \
#include "ipypr2"
	close pr2.file%
	return

 630.E1
	trash% = fn.emsg%(12)	REM MISSING PR2 FILE,NOT UPDATED
	return



REM
REM	SWITCH DISKS TO OBTAIN GL CHART OF ACCOUNTS FILE
REM

 640
	if not pr1.gl.used% \
	  then \
		return

	gld.open% = false%
	coa.name$ = "pglcoa" + pr1.gl.file.suffix$
	REM THROW SWITCHING PROMPTS ONTO SCREEN
	trash% = fn.lit%(lit.place%)
	trash% = fn.put%(fn.drive.out$(pr1.gld.drive%),fld.gld.drive%)
	trash% = fn.set.used%(true%,fld.gld.drive%)
	trash% = fn.lit%(lit.type%)
 640.2
	trash% = fn.get%(2,fld.cont.response%)	REM GET RESPONSE
	if in.status% = req.stopit% \
	   then \			REM USER REQUESTED EXIT
		gosub 650 :\	REM ALLOW USER TO SWITCH DISKS BACK TO ORIGINAL POSITION
		goto 999.2	REM EXIT

	initialize
	if size(fn.file.name.out$(coa.name$,"101",pr1.gld.drive%,\
	   null$,null$)) = 0 \
	   then \
		trash% = fn.emsg%(9) :\ REM COA FILE NOT PRESENT
		goto 640.2	REM ALLOW TO SWITHC AGAIN

	if end #gld.file% then 640E1
	open fn.file.name.out$(coa.name$,"101",pr1.gld.drive%,null$,null$) \
		recl gld.len% as gld.file%
	gld.open% = true%

REM
REM	FIND LENGTH OF COA FILE
REM

	trash%=fn.msg%("     FINDING NUMBER OF ENTRIES IN CHART OF ACCOUNTS FILE")
	if end #gld.file% then .009
	no.coa.recs% = 4000	REM FIRST APPROXIMATION
	while not fn.read.coa.rand%(no.coa.recs%)
		no.coa.recs% = no.coa.recs% / 2
		if no.coa.recs% = 0 then no.coa.recs% = 1
	wend

	if pr1.debugging% then trash%=fn.msg%("first="+str$(no.coa.recs%))
	if end #gld.file% then 640.4	REM PREPARE FOR SEQUENTIAL READS
					REM TO FIND EXACT END OF FILE
	no.coa.recs% = no.coa.recs% - 1
	eof% = false%
	while not eof%
		eof% = true%
		read #gld.file%; \
			coa.co.no$,\
			coa.dept.no$,\
			coa.acct.no$,\
			coa.acct.name$
		eof% = false%
 640.4		no.coa.recs% = no.coa.recs% + 1
	wend
	if pr1.debugging% then trash%=fn.msg%("final="+str$(no.coa.recs%))

	if end #gld.file% then 640E1

	REM CLEAR TEMP SCREEN STUFF
	trash% = fn.clr%(lit.place%)
	trash% = fn.clr%(fld.gld.drive%)
	trash% = fn.set.used%(false%,fld.gld.drive%)
	trash% = fn.clr%(lit.type%)
	trash% = fn.clr%(fld.cont.response%)

	return

 640E1
	trash% = fn.emsg%(10)	REM UNEXPECTED END OF COA FILE
	gosub 650	REM ALLOW TO RETURN DISKS TO PROPER PLACE
	goto 999.1	REM ERROR EXIT



REM
REM	RETURN DISKS TO ORGINAL CONFIGURATION
REM

 650
	if not pr1.gl.used% \
	   then \
		return

	if gld.open% \
	   then \
		close gld.file%
	REM THROW; INSTRUCTIONS ON SCREEN
	trash% = fn.lit%(lit.replace%)
	trash% = fn.lit%(lit.type%)
	trash% = fn.get%(2,fld.cont.response%)
	initialize

	REM GET GARBAGE OFF SCREEN
	trash% = fn.clr%(lit.replace%)
	trash% = fn.clr%(lit.type%)
	trash% = fn.clr%(fld.cont.response%)

	return



REM
REM	CREATE DEFAULT ACCOUNT FILE
REM

 700
	trash% = fn.msg%("     CREATING DEFAULT ACCOUNT FILE")
	no.def.acts% = 4	REM NUMBER OF DEFAULT ACCOUNTS
	dim def.num$(no.def.acts%)
	dim def.name$(no.def.acts%)

	def.num$(1) = "011100"
	def.name$(1) = "CASH"

	def.num$(2) = "121100"
	def.name$(2) = "ACCRUED LIABILITY"

	def.num$(3) = "411100"
	def.name$(3) = "SALARY EXPENSE"

	def.num$(4) = "131100"
	def.name$(4) = "ACCRUED PAYROLL COST LIAB"

	create fn.file.name.out$(act.name$,"101",pr1.act.drive%,null$,null$) \
	   recl act.len% as act.file%

	act.hdr.no.recs% = no.def.acts%
	gosub 620	REM WRITE HEADER

	for i% = 1 to no.def.acts%
		act.no$ = def.num$(i%)
		act.desc$ = def.name$(i%)
		act.current.record.no% = i%
		gosub 610	REM WRITE ACT RECORD
	next i%

	gosub 630	REM UPDATE PR2 FILE
	trash% = fn.msg%("     DEFAULT CREATION COMPLETE")
	created.act.file% = true%	REM SET FLAG THAT ACTFILE CREATED
					REM INTERNALLY TO PROGRAM
	return


rem
rem	do final consistancy checks of data and write out if okay
rem
 900	\
	if not record.data.valid%	\
	   then \
		trash% = fn.emsg%(5) :\ REM RECORD DATA INVALID
		return		rem main driver

	gosub 610	rem write record
	if in.adding%	\
	   then \
		act.hdr.no.recs% = act.current.record.no% :\
		act.current.record.no% = act.current.record.no% + 1 :\
		record.data.valid% = false%	:\
		gosub 400	:\ rem init unused record
		field% = first.data.field%	:\ rem first data field
		first.time.flag%=true% \ REM ALLOW EXIT FIRST TIME FROM FIRST FIELD
	   else \
		field% = key.field%	rem key(record #) field

	return



rem
rem	unexpected end of file
rem

 998	\
	trash% = fn.emsg%(4)	REM UNEXPECTED END OF FILE
	goto 999.1	rem abnormal exit



#include "zeoj"
	end
