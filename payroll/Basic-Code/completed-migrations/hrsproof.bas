#include "ipycomm"
prgname$="HRSPROOF     16-JAN-80"
#include "ipyconst"


rem----------------------------------------------------------------------
rem
REM
REM		HOURS PROOF
REM
REM		(HRSPROOF)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "TRANSACTION PROOF"

REM
REM	FOLLOWING IS A GUIDE TO SUBROUTINES IN HRSPROOF
REM

REM	50	PROCESSING MESSAGE
REM	60	CLEAR SCREEN OF UNNEEDED FIELDS

REM	100	MAIN DRIVER FOR PRINTING CYCLE

REM	1000	PRINT HEADER
REM	1010	PRINT "REPORT CONTINUES"
REM	1020	PRINT "END OF REPORT"

REM	1100	PRINT TRANSACTION PROOF
REM	1190	PRINT TITLES

REM	2000	READ HOURS RECORD AND ASSOCIATED EMPLOYEE RECORD
REM	2200	PRINT CURRENT TRANSACTION ON SCREEN



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
#include "zdmsbrt"

#include "zstring"
#include "zdateio"
#include "zfilconv"
#include "zflip"
#include "zheading"

#include "ipystat"
#include "ipydmemp"
#include "ipyedesc"



rem
rem	error messages
rem
	dim emsg$(30)
	emsg$(1) = "     PY781 INVALID RESPONSE"
	emsg$(2) = "     PY782 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY783 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY784 UNEXPECTED END OF TRANSACTION FILE"
	emsg$(5) = "     PY785 UNEXPECTED END OF EMPLOYEE FILE"


program$ = "HRSPROOF"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2



rem
rem	get screen set up
rem

#include "fpyhrsp"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	fld.now.processing% = 1
	lit.processing% = 6

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP



REM
REM	SEE IF TRANSACTION(HOURS) FILE PRESENT
REM

	if size(fn.file.name.out$(hrs.name$,"001",pr1.hrs.drive%,null$,null$))=0\
	   then \
		trash% = fn.msg%("TRANSACTION FILE NOT PRESENT," + \
		   function.name$ + " RETURNING TO MENU") :\
		goto 999.3	REM EXIT TO CHAIN BACK TO MENU WITH NO MESSAGE

rem
rem	open HRS file
rem

	if end #hrs.file% then 998
	open fn.file.name.out$(hrs.name$,"001",pr1.hrs.drive%,nul$,nul$)\
		recl hrs.len% as hrs.file%

rem
rem	file exists so read in header and proceed
rem

	read #hrs.file% ,1;	\
#include "ipyhrshd"

REM
REM	OPEN EMPLOYEE FILE
REM
	if end #emp.file% then 997
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,null$,null$) \
		recl emp.len% as emp.file%

REM
REM	INIT OTHER STUFF
REM
	hrs.hdr.proof.no% = hrs.hdr.proof.no% + 1
	line.count.limit% = 60

	REM STUFF DESCRIPTION TABLE FROM PR1
	for i% = 1 to 4
		ed.desc.table$(i%) = pr1.rate.name$(i%)
	next i%



REM
REM	CRT INPUT DRIVER
REM

	rgstr.printed% = false%
	while not rgstr.printed%
		gosub 50	REM PROCESSING MESSAGE
		gosub 100	REM MAIN PRINTING DRIVER
		gosub 60	REM CLEAR SCREEN OF PROCESSING MESSAGE
		rgstr.printed% = true%
	wend

REM
REM	EOJ PROCESSING
REM

	if stopit% or stop.print% \
	   then \
		trash% = fn.msg%("     STOP REQUESTED") :\
		close hrs.file% : close emp.file% :\
		goto 999.2	REM EXIT AT OPERATOR REQUEST

	hrs.hdr.proofed% = true%	REM SET PROOFED FLAG
	print #hrs.file% , 1; \
#include "ipyhrshd"
	close hrs.file%
	close emp.file%
	goto 999		REM NORMAL EXIT



 50	REM PROCESSING MESSAGE

	trash% = fn.lit%(lit.processing%)
	return

 60	REM CLEAR SCREEN OF UNNEEDED FIELDS UPON PROCESSING COMPLETION

	trash% = fn.clr%(fld.now.processing%)
	trash% = fn.clr%(lit.processing%)
	return



REM
REM	MAIN DRIVER FOR PRINTING PROCESSING
REM

 100
	page% = 0
	current.hrs.record% = 1
	stop.print% = false%
	line.count% = line.count.limit% REM FORCE HEADING AT BEGGINGING
	lprinter

while not stop.print% and current.hrs.record% <= hrs.hdr.no.recs%
	gosub 2000	REM READ TRANSACTION AND CORRESPONDING EMP RECORD
	gosub 2200	REM DISPLAY NUMBER ON SCREEN
	gosub 1100	REM PRINT TRANSACTION INFO
	if pr1.debugging% \
	   then \
		console :\
		trash% = fn.msg%("fre=" + str$(fre)) :\
		lprinter

	current.hrs.record% = current.hrs.record% + 1
wend

	if not stop.print% \
	   then \
		gosub 1020	REM PRINT END OF REPORT LINE

	console
	return



REM
REM	UNEXPECTED END OF EMPLOYEE FILE
REM

 997
	console
	trash% = fn.emsg%(5)	REM UNEXPECTED END OF EMPLOYEE FILE
	goto 999.1	REM ABNORMAL EXIT

REM
REM	UNEXPECTED END OF TRANSACTION FILE
REM

 998
	console
	trash% = fn.emsg%(4)	REM UNEXPECTED END OF TRANSACTION FILE
	goto 999.1	REM ABNORMAL EXIT

#include "zeoj"



 1000	REM PRINT HEADING
	line.count% = fn.hdr%(function.name$)
	return

 1010	REM PRINT *** REPORT CONTINUES ***
	if page% <> 0 \ REM SKIP CONTINUES MESSAGE IF REPORT HASN'T STARTED YET
	   then \
		print "     *** REPORT CONTINUES ***"
	return

 1020	REM PRINT *** END OF REPORT ***

	if page% = 0 \
	   then \
		gosub 1000 :\ REM NO TRANSACTIONS SO PRINT TITLES
		print :\
		print "                   *** NO TRANSACTIONS ***" :\

	print
	print "     *** END OF REPORT ***"
	print
	return



 1100	REM PRINT TRANSACTION


	if line.count% + 2 > line.count.limit% \
	   then \
		gosub 1010 :\	REM CONTINUED LINE
		gosub 1000 :\	REM PRINT HEADER
		gosub 1190	REM PRINT TITLES

	if stop.print% then return	REM PRINT TITLES CHECKS FN.ABORT

	line.count% = line.count% + 2
	print

	REM IF DELETED ONLY PRINT DELETED STUFF
	if hrs.deleted% \
	   then \
		print tab(5);"DELETED TRANSACTION" :\
		stop.print% = fn.abort% :\
		return

	if emp.hs.type$ = "H" \
	   then \
		name.suffix$ = "(HOURLY)" \
	   else \
		name.suffix$ = "(SALARIED)"

	print tab(9);hrs.emp.no$; \
		tab(17);fn.name.flip$(emp.emp.name$) + name.suffix$; \
		tab(60);fn.date.out$(hrs.eff.date$);
	print using "###,###.##";tab(71);hrs.units;
	print using "##";tab(85);hrs.rate%;
	if hrs.rate% = 0 \
	   then \
		desc$ = ed.desc.table$(1)+" AND "+ed.desc.table$(2) \
	   else \
		desc$ = ed.desc.table$(hrs.rate%)

	print tab(90);desc$
	stop.print% = fn.abort%

	return



 1190	REM PRINT TITLES

	print
	print tab(15);"BATCH NO:"; \
		tab(25);str$(hrs.hdr.batch.no%)
	stop.print% = fn.abort%
	if stop.print% then return

	print tab(15);"PROOF NO:"; \
		tab(25);str$(hrs.hdr.proof.no%)
	stop.print% = fn.abort%
	if stop.print% then return

	print
	print tab(8);"EMPLOYEE"; \
		tab(59);"EFFECTIVE"; \
		tab(80);"TRANSACTION"
	stop.print% = fn.abort%
	if stop.print% then return

	print tab(9);"NUMBER"; \
		tab(19);"EMPLOYEE NAME"; \
		tab(62);"DATE"; \
		tab(76);"UNITS"; \
		tab(84);"CODE"; \
		tab(90);"DESCRIPTION"
	stop.print% = fn.abort%

	line.count% = line.count% + 9
	return



 2000	REM READ TRANSACTION(HOURS) RECORD AND ASSOCIATED EMPLOYEE

	read #hrs.file%,current.hrs.record% + 1; \
#include "ipyhrs"

	if emp.no$ <> hrs.emp.no$ \	REM CHECK IF EMPLOYEE ALREADY READ IN
	   then \
		read #emp.file%,val(left$(hrs.emp.no$,4)) + 1; \
#include "ipyemp"

	return



 2200	REM PUT EMPLOYEE NUMBER ON SCREEN

	console
	trash% = fn.put%(hrs.emp.no$,fld.now.processing%)
	lprinter
	return

	end
