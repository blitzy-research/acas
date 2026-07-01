#include "ipycomm"
prgname$="PYSRTPRM      10-JAN-80"
#include "ipyconst"



rem---------------------------------------------------------
rem
rem	P A Y R O L L  S Y S T E M
rem
REM	P Y S R T P R M
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PYSRTPRM"
function.name$="SORT PARAMETERS"

REM----------------------------------------------------------
REM
REM	DMS SYSTEM
REM
REM-----------------------------------------------------------

#include "zdms"
#include "zstring"
#include "zdateio"
#include "ipystat"
#include "zfilconv"


dim emsg$(10)
emsg$(02)="     PY482 UNABLE TO CREATE PYHOURS.SRT"


rem	June 1, 1978
rem	dimension arrays
	pad$=chr$(0)
	maxkeys%=5
	dim srt.kpos%(maxkeys%)
	dim srt.klen%(maxkeys%)
	dim srt.kad$(maxkeys%)
	dim srt.kan$(maxkeys%)
	gosub 7725		rem clear srt arrays
	goto 7799		rem goto user code

7705	rem-----fill srt fields-----------
	srt.record$=""
	srt.record$=srt.record$+srt.in.drive$
	srt.record$=srt.record$+left$(srt.in.name$+"        ",8)
	srt.record$=srt.record$+left$(srt.in.type$+"   ",3)
	srt.record$=srt.record$+srt.out.drive$
	srt.record$=srt.record$+left$(srt.out.name$+"        ",8)
	srt.record$=srt.record$+left$(srt.out.type$+"   ",3)
	srt.record$=srt.record$+pad$
	srt.record$=srt.record$+chr$(srt.rec.length%)
	srt.record$=srt.record$+chr$(255)+pad$+pad$+pad$+pad$
	srt.record$=srt.record$+chr$(srt.backup.flag%)
	srt.record$=srt.record$+chr$(srt.disk.change.flag%)
	srt.record$=srt.record$+chr$(srt.console.flag%)
	srt.record$=srt.record$+srt.work.drive$
	for srt.x%=1 to maxkeys%
		srt.record$=srt.record$+chr$(srt.kpos%(srt.x%))
		srt.record$=srt.record$+chr$(srt.klen%(srt.x%))
		srt.record$=srt.record$+srt.kad$(srt.x%)
		srt.record$=srt.record$+srt.kan$(srt.x%)
	next srt.x%
	srt.record$=srt.record$+pad$+pad$+pad$+pad$+pad$+pad$+pad$+pad$
	return


7725	rem-----clear srt arrays-----------
	for srt.x%=1 to maxkeys%
		srt.kpos%(srt.x%)=0
		srt.klen%(srt.x%)=0
		srt.kad$(srt.x%)="A"
		srt.kan$(srt.x%)="N"
	next srt.x%
	return

7799	rem	user code

				srt.file% = 1
				delim$=":"
				token.limit% = 2
				drive.b$=chr$(2)
				drive.a$=chr$(1)
				flag.on%=1
				flag.off%=0
				backup%=flag.off%
				console.messages%=flag.off%
				srt.work.drive$=drive.a$
				stop$ = "STOP"



REM
REM	SCREEN SETUP
REM

#include "fpysrt"

	trash% = fn.put.all%(true%)



rem
rem	The following while/wend loop is the main processing
rem	routine.  The loop calls all of the major processing
rem	sections to create sort parameter files.
rem	These routines in turn call the minor processing functions.
rem


if pr1.debugging% then print "done init. fre=";fre
if pr1.debugging% then gosub 900		rem get console messages


while function$<>stop$
	gosub 20	REM SET UP HOURS SORT
	function$ = stop$
wend

#include "zeoj"



rem-------subroutines section------

20	rem-----make HOURS-----------------------------
	gosub 7725			rem clear srt arrays
	parm.name$="PYHOURS"
	gosub 300			rem create file
	gosub 310			rem get name srt info
	gosub 7705			rem file srt fields
	gosub 320			rem write srt file
	close srt.file%
	return

300	rem-----create file------------------------------
	if end #srt.file% then 399
	create fn.file.name.out$(parm.name$,"SRT",common.drive%,null$,null$) \
		as srt.file%
	if end #srt.file% then 400
	return

399	rem-----here on eof on create-------------------
	trash% = fn.emsg%(2)	REM UNABLE TO CREATE PYHOURS.SRT
	stop

400	rem-----here on eof on write---------------------
	trash% = fn.emsg%(2)	REM UNABLE TO CREATE PYHOURS.SRT
	stop

320	rem-----write srt file-----------------------------
	print #srt.file%;\
		srt.record$
	return

310	rem-----get name info----------------------------
	file.drive$ = chr$(pr1.hrs.drive%)
	srt.in.drive$= file.drive$
	srt.in.name$="pyhrs"
	srt.in.type$="001"
	srt.out.drive$= file.drive$
	srt.out.name$="pyhrs"
	srt.out.type$="101"
	srt.rec.length%= hrs.len%
	srt.backup.flag%=backup%
	srt.console.flag% = console.messages%
	srt.work.drive$=drive.a$
	gosub 311			rem get name key info
	return


311	rem-----get name key info--------------------------
	REM FIRST KEY IS TO INSURE HEADER COMES OUT FIRST
	srt.kpos%(1)=1
	srt.klen%(1)=1
	srt.kad$(1)="D"
	srt.kan$(1)="A"
	REM SECOND KEY IS EMPLOYEE NUMBER
	srt.kpos%(2)=2
	srt.klen%(2)=5
	srt.kad$(2)="A"
	srt.kan$(2)="A"
	return


900	rem-----debugging message-----
	console.messages% = 2
	return

end
