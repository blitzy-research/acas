#include "ipycomm"
#include "ipyconst"
prgname$="PYACTPRT  18 DEC., 1979"


rem----------------------------------------------------------------------
rem
REM
REM	      ACCOUNT PRINT
REM	      PAYROLL SYSTEM
REM		(PYACTPRT)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "ACCOUNT FILE PRINT"

REM
REM	FOLLOWING IS A GUIDE TO SUBROUTINES IN PYACTPRT
REM

REM	50	'NOW PROCESSING' Message
REM	60	CLEAR SCREEN OF UNNEEDED FIELDS

REM	100	MAIN DRIVER FOR PRINTING CYCLE
REM	200	LOOKING FOR ACT FILE, READING HDR
REM	1000	PRINT HEADER
REM	1010	PRINT "REPORT CONTINUES"
REM	1020	PRINT "END OF REPORT"

REM	1100	PRINT ACCOUNT FILE
REM	1190	PRINT TITLES

REM	2000	READ ACCOUNT FILE RECORD
REM	2200	PRINT CURRENT ACCOUNT ON SCREEN



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


rem
rem	error messages
rem
	dim emsg$(5)	rem can go to 20
	emsg$(1) = "     PY961 INVALID RESPONSE"
	emsg$(2) = "     PY962 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY963 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY964 UNEXPECTED END OF ACCOUNT FILE"
	emsg$(5) = "     PY965 ACCOUNT FILE NOT FOUND"


program$ = "PYACTPRT"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2

rem
rem	get screen set up
rem

#include "fpyactp"	rem note----this one's on drive a----

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	fld.now.processing% = 1
	lit.processing% = 6

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP


REM
REM	SEE IF ACCOUNT FILE PRESENT--IF YES, OPEN & READ HDR
REM
	gosub 200	rem don't bother returning if you can't find it

REM
REM	INIT OTHER STUFF
REM
	line.count.limit% = 60
	pw$ = null$	rem for use with trash 80, maybe
	pm$ = null$

REM
REM	CRT INPUT DRIVER
REM

	rgstr.printed% = false%
	while not rgstr.printed%
		gosub 50	REM ALIGN MESSAGE
		if stopit% then goto 10 REM EXIT REQUESTED

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
 11	close act.file%
	if stop.print%	then goto 999.2 	rem premature end

	goto 999		REM NORMAL EXIT



 50	REM now processing msg

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
	current.act.record% = 1
	stop.print% = false%
	line.count% = line.count.limit% REM FORCE HEADING AT BEGGINGING
	lprinter

while not stop.print% and current.act.record% <= act.hdr.no.recs%
	gosub 2000	REM READ ACCOUNT RECORD
	gosub 2200	REM DISPLAY NUMBER ON SCREEN
	gosub 1100	REM PRINT ACCOUNT INFO
	if pr1.debugging% \
	   then \
		console :\
		trash% = fn.msg%("fre=" + str$(fre)) :\
		lprinter

	current.act.record% = current.act.record% + 1
wend

	if not stop.print% \
	   then \
		gosub 1020	REM PRINT END OF REPORT LINE

	console
	return


REM======E O J=============

#include "zeoj"


REM--------SUBROUTINES------------
200	rem-----look for act file-----
       act.file.name$=fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pm$)
	if end #act.file%  then 201
	open act.file.name$  recl act.len%  as act.file%
	if end #act.file%  then 202

	read #act.file%,1;\	rem header rec
#include "ipyacthd"

	return

201	rem-----no act file at all-----
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



 1100	REM PRINT ACCOUNT


	if line.count% + 2 > line.count.limit% \
	   then \
		gosub 1010 :\	REM CONTINUED LINE
		gosub 1000 :\	REM PRINT HEADER
		gosub 1190	REM PRINT TITLES

	line.count% = line.count% + 2
	print


	print using "### & &"; tab(41); current.act.record%; tab(63); \
		act.no$; tab(83); act.desc$
	stop.print% = fn.abort%

	return



 1190	REM PRINT TITLES

	print
	print tab(39); "ACCOUNT KEY"; tab(59); "ACCOUNT NUMBER"; tab(83); \
		"ACCOUNT NAME"
	print
	stop.print% = fn.abort%
	if stop.print% then return

	line.count% = line.count% + 3
	return



 2000	REM READ ACCOUNT RECORD

	read #act.file%,current.act.record% + 1; \
#include "ipyact"

	return



 2200	REM PUT ACCOUNT NUMBER ON SCREEN

	console
	trash% = fn.put%(str$(current.act.record%),fld.now.processing%)
	lprinter
	return

	end
