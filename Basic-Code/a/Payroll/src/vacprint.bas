#include "ipycomm"
#include "ipyconst"
prgname$="VACPRINT  18 DEC., 1979"


rem----------------------------------------------------------------------
rem
REM
REM	      VACATION PRINT
REM	      PAYROLL SYSTEM
REM		(VACPRINT)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "VACATION REPORT"

REM
REM	FOLLOWING IS A GUIDE TO SUBROUTINES IN VACPRINT
REM

REM	50	put up processing msg
REM	60	CLEAR SCREEN OF UNNEEDED FIELDS

REM	100	MAIN DRIVER FOR PRINTING CYCLE
REM	200	LOOKING FOR EMP FILE, READING HDR

REM	1000	PRINT REPORT HEADER
REM	1010	PRINT "REPORT CONTINUES"
REM	1020	PRINT "END OF REPORT"

REM	1100	PRINT VACATION REPT

REM	2000	READ EMPLOYEE FILE RECORD
REM	2200	PRINT EMPLOYEE NUMBER ON SCREEN



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
#include "ipydmemp"

rem
rem	error messages
rem
	dim emsg$(10)	rem can go to 20
	emsg$(1) = "     PY821 INVALID RESPONSE"
	emsg$(2) = "     PY822 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY823 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY824 UNEXPECTED END OF EMPLOYEE FILE"
	emsg$(5) = "     PY825 EMPLOYEE FILE NOT FOUND"
	emsg$(6) = "     PY826 "
	emsg$(7) = "     PY827 "
	emsg$(8) = "     PY828 "

program$ = "VACPRINT"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2



rem
rem	get screen set up
rem

#include "fpyvac"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	fld.now.processing% = 1
	lit.processing% = 6

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP


REM
REM	SEE IF EMPLOYEE FILE PRESENT--IF YES, OPEN & READ HDR
REM
	gosub 200	rem don't bother returning if you can't find it


REM
REM	INIT OTHER STUFF
REM
	line.count.limit% = 60
	pw$ = null$	rem for use with trash 80, maybe
	pm$ = null$
	a$ = "& "
	amt$ = "#,###,###.## "
	rate$ = "###.## "
	line1$ = a$+a$+rate$+amt$+amt$+rate$+amt$+amt$
	line2$ = a$+a$+amt$+a$+amt$



REM
REM	CRT INPUT DRIVER
REM

	rgstr.printed% = false%
	while not rgstr.printed%
		gosub 50	REM PUT UP PROCESSING MSG
		gosub 100	REM MAIN PRINTING DRIVER
		gosub 60	REM CLEAR SCREEN OF PROCESSING MESSAGE
		rgstr.printed% = true%
	wend

REM
REM	EOJ PROCESSING
REM

 10
	if stopit% or stop.print% \
	   then \
		trash% = fn.msg%("     STOP REQUESTED")
 11	close emp.file%

	if stop.print%	then 999.2	rem premature end

	goto 999		REM NORMAL EXIT

 50	REM put up processssing msg

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
	current.emp.record% = 1
	stop.print% = false%
	line.count% = line.count.limit% REM FORCE HEADING AT BEGGINGING
	lprinter

while not stop.print% and current.emp.record% <= emp.hdr.no.recs%
	gosub 2000	REM READ EMPLOYEE RECORD
	gosub 2200	REM DISPLAY NUMBER ON SCREEN
	gosub 1100	REM PRINT VACATION INFO
	if pr1.debugging% \
	   then \
		console :\
		trash% = fn.msg%("fre=" + str$(fre)) :\
		lprinter

	current.emp.record% = current.emp.record% + 1
wend

	if not stop.print% \
	   then \
		gosub 1020	REM PRINT END OF REPORT LINE

	console
	return


REM======E O J=============

#include "zeoj"


REM--------SUBROUTINES------------
200	rem-----look for emp file-----
       emp.file.name$=fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pm$)
	if end #emp.file%  then 201
	open emp.file.name$  recl emp.len%  as emp.file%
	if end #emp.file%  then 202

	read #emp.file%,1;\	rem header rec
#include "ipyemphd"

	return

201	rem-----no emp file at all-----
	trash% = fn.emsg%(5)
	goto 999.1	rem goodbye

202	rem-----unexpected eof-------
	trash% = fn.emsg%(4)
	goto 999.1	rem aaaarrrgghhh


REM--------PRINT ROUTINES---------
 1000	REM PRINT HEADING
	line.count% = fn.hdr%(function.name$)
	return

 1010	REM PRINT *** REPORT CONTINUES ***
	if page% <> 0 \ REM SKIP CONTINUES MESSAGE IF REPORT HASN'T STARTED YET
	   then \
		print "     *** REPORT CONTINUES ***"
	return

 1020	REM PRINT *** END OF REPORT ***
	print
	print "     *** END OF REPORT ***"
	return

1090	rem------print titles-------
	print
	print tab(2); "EMPLOYEE"; tab(41); "VACATION    VACATION UNITS      "+\
		"VACATION        SICK LEAVE   SICK LEAVE        SICK LEAVE"
	print tab(3); "NUMBER    EMPLOYEE NAME"; tab(40); "ACCUM. RATE   "+ \
		"ACCUMULATED       UNITS USED      ACCUM. RATE   UNITS " + \
		"ACCUM.      UNITS USED"
	print
	line.count% = line.count% + 4
	return


 1100	REM PRINT HISTORY


	if line.count% + 2 > line.count.limit% \
	   then \
		gosub 1010 :\	REM CONTINUED LINE
		gosub 1000 :\	REM PRINT HEADER
		gosub 1090	rem print titles


	stop.print% = fn.abort%
	if stop.print%	then return
	print
	print using line1$; tab(3); emp.no$; tab(10); emp.emp.name$; tab(42);\
		emp.vac.rate; tab(54); emp.vac.accum; tab(71); emp.vac.used; \
		tab(90); emp.sl.rate; tab(101); emp.sl.accum; tab(118); \
		emp.sl.used
	stop.print% = fn.abort%
	if stop.print%	then return
	print using line2$;tab(15);status$;tab(40); "COMP. TIME ACCUMULATED:";\
		tab(64);emp.comp.accum; tab(87); "COMP. TIME USED:"; tab(105);\
		emp.comp.used
	print
	line.count% = line.count% + 4

	return


2000	rem------read employee record------

	read #emp.file%,current.emp.record% + 1; \
#include "ipyemp

	if emp.status$ = "D"  then status$ = "(DELETED)"
	if emp.status$ = "T"  then status$ = "(TERMINATED)"
	if emp.status$ = "A"  then status$ = "(ACTIVE)"
	if emp.status$ = "L"  then status$ = "(ON LEAVE)"
	emp.emp.name$ = fn.name.flip$(emp.emp.name$)

	return

 2200	REM PUT EMPLOYEE NUMBER ON SCREEN

	console
	trash% = fn.put%(emp.no$,fld.now.processing%)
	lprinter
	return

	end
