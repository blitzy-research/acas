#include "indcomm.bas"
prgname$="NAD     SEPT. 23, 1982 "
rem-----------------------------------------------------------
rem
rem	N  A  D        (M  E  N  U)
rem
rem	NAME AND ADDRESS SYSTEM (NAD) MENU
rem
rem	   copyright (c) 1977,1978  APPLEWOOD COMPUTERS
rem        and Vincent B Coen  1979 - 2025
rem
rem	   UK version changes by Vincent B Coen & APPLEWOOD COMPUTERS
rem             Copyright (c) 1980 - 2025
rem
rem-----------------------------------------------------------
program$="NAD"
function$="NAD System Menu"
#include "zfilconv.bas"
#include "indconst.bas"
dim emsg$(25)
emsg$(01)="NAD101 SUBPROGRAM NOT FOUND: "
emsg$(02)="NAD102 NOT NUMERIC"
emsg$(03)="NAD103 NOT ON MENU"
emsg$(04)="NAD104 INVALID DATE"
emsg$(05)="NAD105 INVALID RESPONSE"
emsg$(06)="NAD106 QSORT.COM NOT ON DISK"
emsg$(07)="NAD107 CORRECT .SRT FILE NOT ON DISK"
emsg$(08)="NAD108 UNEXPECTED EOF ON $$$ FILE"
emsg$(09)="NAD109 UNEXPECTED EOF ON $$$ FILE"
emsg$(10)="NAD110 INCORRECT LENGTH"
emsg$(11)="NAD111 INVALID CHARACTERS"
emsg$(12)="NAD112 TOO LONG"
emsg$(13)="NAD113 INVALID DRIVE"
emsg$(14)="NAD114 INCORRECT LENGTH"
emsg$(15)="NAD115 INVALID CHARACTERS"
emsg$(16)="NAD116 TOO LONG"
emsg$(17)="NAD117 INVALID DRIVE"
emsg$(18)="NAD118 NOT NUMERIC"
emsg$(19)="NAD119 OUT OF RANGE"
emsg$(20)="NAD120 EOF ON CREATE"
emsg$(21)="NAD121 EOF ON WRITE"
emsg$(22)="NAD122 "
rem------------------------------------------------------------
rem
rem	F U N C T I O N      D E F I N I T I O N S
rem
rem------------------------------------------------------------
#include "zparse.bas"
#include "znumber.bas"
def fn.leap.year%(year%)
	if (year%/4.0)-int%(year%/4.0)=0 \
		then   fn.leap.year%=true% \
		else   fn.leap.year%=false%
	return
fend
def fn.edit.date%(date$)			rem parameter file date
	fn.edit.date%=false%			rem information must be
	if fn.parse%(date$,"/")<>3 then return  rem initialized for this
	for xx2%=1 to 3 				rem function to
	  if not fn.num%(token$(xx2%)) then return	rem work
	next xx2%					rem correctly
	mo%=val(token$(pr1.date.mo%))
	dy%=val(token$(pr1.date.dy%))
	yr%=val(token$(pr1.date.yr%))
	if mo%<1 or mo%>12 or \
	   dy%<1 or dy%>31 or \
	   yr%<1 or yr%>99 then return
	if (mo%=4 or mo%=6 or mo%=9 or mo%=11) and dy%>30 then return
	if mo%=2 and not fn.leap.year%(yr%) and dy%>28 then return
	if mo%=2 and fn.leap.year%(yr%) and dy%>29 then return
	fn.edit.date%=true%
	return
fend
def fn.date.in$=right$("00"+str$(yr%),2)+right$("00"+str$(mo%),2)+ \
	      right$("00"+str$(dy%),2)
dim out.date$(3)
def fn.date.out$(date$)
	out.date$(pr1.date.mo%)=mid$(date$,3,2)
	out.date$(pr1.date.dy%)=mid$(date$,5,2)
	out.date$(pr1.date.yr%)=mid$(date$,1,2)
	fn.date.out$=out.date$(1)+"/"+out.date$(2)+"/"+out.date$(3)
	return
fend
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
		srt.file% = 15
		drive.b$=chr$(2)
		drive.a$=chr$(1)
		flag.on%=1
		flag.off%=0
		backup%=flag.off%
		console.messages%=flag.off%
		srt.work.drive$=drive.a$
		stop$ = "STOP"
rem------------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem------------------------------------------------------------
#include "indchain.bas"
pr1.max.drive$="F"
first.menu.item%=1
last.menu.item%=9
if pr1.date.format%=1 \
	then	pr1.date.mo%=1:pr1.date.dy%=2:pr1.date.yr%=3
if pr1.date.format%=2 or pr1.date.format%=0 \
	then	pr1.date.mo%=2:pr1.date.dy%=1:pr1.date.yr%=3
no.progs%=(last.menu.item%-first.menu.item%)+1
dim prog$(no.progs%)
prog$(01)="nadentry"
prog$(02)="nadxtrak"
prog$(03)="nadprint"
prog$(04)="nadlabel"
prog$(05)=""
rem------------------------------------------------------------
rem
rem	M A I N      D R I V E R
rem
rem------------------------------------------------------------
if common.drive$=null$ \
	then	common.drive$=fn.get.drive$
if not chained% \
	then	command.line$=command$	:\
		common.date$="000000"   :\
		gosub 103		rem get a date
48
if chained% and common.return.code%<>0 \
	then	gosub 105 \		rem confirm
	else	confirmed%=true%
if not confirmed% \
	then	goto 999.7
49
gosub 100			rem request selection
if stopit% then goto 999.7
if selection%=5 \		rem sort by name
	then	gosub 200 :\	rem submit qsort by name
		goto 49 	rem here only if error
if selection%=6 \		rem sort by postcode
	then	gosub 210 :\	rem submit qsort by postcode
		goto 49 	rem here only if error
if selection%=7 \
	then	gosub 300 :\	rem create name srt file
		goto 49
if selection%=8 \
	then	gosub 315 :\	rem create postcode srt file
		goto 49
if selection%=9 \
	then	gosub 103 :\	rem get a date
		goto 49
if size(fn.file.name.out$(prog$(selection%),"INT",0,pw$,pms$))=0 then \
	print bell$;tab(5);emsg$(01);  \
		fn.file.name.out$(prog$(selection%),null$,0,pw$,pms$) :\
	chained%=true%	:\
	common.return.code%=9  :\
	goto 48
chained%=true%
chained.from.root%=true%
chain fn.file.name.out$(prog$(selection%),null$,0,pw$,pms$)
print "blooey"
stop
999.7
for m%=1 to 24:print:next m%		rem clear screen
print tab(5);"Stop requested"
print:print:print:print
chained.from.root%=false%
999.8
#include "zeoj.bas"
rem------------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem------------------------------------------------------------
100	rem-----request selection------------------------------
	gosub 101		rem display menu
100.1	print tab(15);"     Enter number of function desired   ";
	input "";line in$
	if in$=return$ then goto 100
	if in$=escape$ then stopit%=true%:return
	if match("#",in$,1)<>1 then \
		print bell$;tab(5);emsg$(02):goto 100.1
	selection%=val(in$)
	if selection%>last.menu.item% or selection%<first.menu.item% \
		then	print bell$;tab(5);emsg$(03) :\
			goto 100.1
	return
101	rem-----display menu-----------------------------------
	for m%=1 to 24:print:next m%
print "     ***************             N   A   D             ***************"
print "                    N A D      S Y S T E M      M E N U"
	print:print:print
	print
	print tab(20);"1     CREATE OR MODIFY A NAD FILE"
	print tab(20);"2     EXTRACT NAMES FROM ONE FILE TO ANOTHER"
	print tab(20);"3     PRINT A REPORT"
	print tab(20);"4     PRINT MAILING LABELS"
	print tab(20);"5     SORT BY LAST NAME"
	print tab(20);"6     SORT BY POSTCODE"
	print tab(20);"7     CREATE NAME SRT FILE"
	print tab(20);"8     CREATE POSTCODE SRT FILE"
	print tab(20);"9     CHANGE SYSTEM DATE"
	print tab(20);"ESC      STOP PROGRAM"
	print tab(20);"CR       REFRESH MENU"
	print:print:print
	print:print:print
	return
102	rem-----get new file definitions--------------------------
	return
103	rem-----get a date----------------------------------------
	if len(command.line$)>0 \
		then	in$=command.line$	:\
			command.line$=null$	:\
			goto 104
	if pr1.date.mo%=1 \
		then	temp$="(MM/DD/YY)" \
		else	temp$="(DD/MM/YY)"
	print
	print tab(10);"Current value:               ";   \
		fn.date.out$(common.date$)
	print tab(10);"Enter system date ";temp$;" ";
	input "";line in$
	if in$=return$ then return
104
	if in$="00/00/00" \
		then	common.date$="000000" :\
			return
	if not fn.edit.date%(in$) \
		then	print bell$;tab(5);emsg$(04):goto 103
	common.date$=fn.date.in$
	return
105	rem-----confirm--------------------------------------------
	print
	print bell$;tab(5);"Previous program ended abnormally"
	print tab(5);"Continue? (Y or N) ";
	gosub 106			rem get t/f
	if t% \
		then	confirmed%=true% \
		else	confirmed%=false%
	return
106	rem-----enter t/f/cr/back/stopit-----------------------
	t%=false%:f%=false%:cr%=false%:back%=false%:stopit%=false%
	input "";line in$
	if in$<>null$ then in$=ucase$(in$)
	if in$=escape$ then stopit%=true%:return
	if in$=return$ then cr%=true%:return
	if in$=back$ then back%=true%:return
	if in$="Y" or in$="YES" or in$="T" or in$="TRUE" or in$="OK" \
		then	t%=true%:return
	if in$="N" or in$="NO" or in$="F" or in$="FALSE" \
		then	f%=true%:return
	print bell$;tab(5);emsg$(05)
	goto 106
117	rem-----enter in$--------------------------------------
	stopit%=false%:cr%=false%:back%=false%
	input "";line in$
	if in$<>null$ \
		then	uin$=ucase$(in$) \
		else	uin$=in$
	if uin$=escape$ then stopit%=true%:return
	if uin$=back$ then back%=true%:return
	if in$=return$ then cr%=true%:return
	return
200	rem-----submit qsort by name----------------------------
	sort.param$="NAME"
	gosub 220			rem build $$$ file
	stop
210	rem-----submit qsort by postcode------------------------
	sort.param$="POSTCODE"
	gosub 220			rem build $$$ file
	stop
220	rem-----build $$$ file----------------------------------
	end$= chr$(0)+ chr$(24H)
	submit.file%=17
REM------------------------------------------------------
REM----- SORTS SHOULD EXIT THRU THIS ROUTINE   -----
REM----- WHICH BUILDS A COMMAND FILE AND STOPS ----------
REM------------------------------------------------------
REM
if size(fn.file.name.out$("QSORT","com",0,password$,params$))= 0  then \
	print bell$;tab(05);emsg$(06) :\
	RETURN
if size(fn.file.name.out$(sort.param$,"srt",common.drive%,password$,params$)) \
	= 0  then \
	print bell$;tab(05);emsg$(07) :\
	RETURN
REM----- CREATE COMMAND FILE -----
if end #submit.file%  then 9090
create fn.file.name.out$("$$$","sub", 1,password$,params$) \
	recl 80H  as submit.file%
run.menu$ = "CRUN2 "+system$+" " + fn.date.out$(common.date$)
REM----- PRINT TO COMMAND FILE -----
if end #submit.file%  then 9091
print using "&"; #submit.file% ; chr$(len(run.menu$)) + run.menu$ + end$
srt$ = "QSORT " + \
    fn.file.name.out$(sort.param$,"srt",common.drive%,password$,params$)
print using "&";#submit.file% ; chr$(len(srt$)) + srt$ + end$
	close submit.file%
	stop
9090	rem----- here if eof on submit file create -----------------
	print bell$;tab(05);emsg$(08)
	RETURN
9091	rem----- here if eof on submit file build -----------------
	print bell$;tab(05);emsg$(09)
	close submit.file%
	RETURN
300	rem-----create name srt file-------------------------------
	for m%=1 to 24:print:next m%	rem clear screen
	gosub 305			rem request file info
	if back% or stopit% then return
	gosub 7725			rem clear srt arrays
	parm.name$="NAME"
	gosub 3000			rem create file
	gosub 3100			rem get name srt info
	gosub 7705			rem file srt fields
	gosub 3300			rem write srt file
	print:print
	print tab(10);"Name sort parameter file created"
	print:print
	close srt.file%
	return
305	rem-----request file info----------------------------------
	gosub 400			rem request input file name
	if back% then return
	if stopit% then return
306
	gosub 420			rem request input file type
	if back% then goto 305
	if stopit% then return
307
	gosub 440			rem request input file drive
	if back% then goto 306
	if stopit% then return
308
	gosub 460			rem request output file name
	if back% then goto 307
	if stopit% then return
309
	gosub 480			rem request output file type
	if back% then goto 308
	if stopit% then return
310
	gosub 500			rem request output file drive
	if back% then goto 309
	if stopit% then return
	gosub 600			rem request file length
	if back% then goto 310
	if stopit% then return
	return
315	rem-----create postcode srt file--------------------------------
	for m%=1 to 24:print:next m%	rem clear screen
	gosub 305			rem request file info
	if back% or stopit% then return
	gosub 7725			rem clear srt arrays
	parm.name$="POSTCODE"
	gosub 3000			rem create file
	gosub 3200			rem get name srt info
	gosub 7705			rem file srt fields
	gosub 3300			rem write srt file
	print:print
	print tab(10);"Postcode sort parameter file created"
	print:print
	close srt.file%
	return
400	rem-----request input file name--------------------------
	print
	print tab(10);"Enter name of file to be sorted (1-8 chars) ";
	gosub 117			rem get in$
	if back% or stopit% then return
	if in$=null$ or len(in$)>8 then \
		print bell$;tab(5);emsg$(10):goto 400
	if match(".",in$,1)>0 or        \
	   match(" ",in$,1)>0 or        \
	   match("*",in$,1)>0 or        \
	   match("\?",in$,1)>0 or       \
	   match(":",in$,1)>0 then      \
		print bell$;tab(5);emsg$(11):goto 400
	in.name$=ucase$(in$)
	return
420	rem-----request input file type--------------------------
	in.type$="nad"
	return
440	rem-----request input file drive-------------------------
	print
	print tab(10);"Enter input file drive (@,A-F;RET=CURLOG) ";
	gosub 117			rem get in$
	if back% or stopit% then return
	if len(in$)>1 \
		then	print bell$;tab(05);emsg$(12):goto 440
	if in$<>null$ then in$=ucase$(in$)
	if in$=return$ then in$="@"
	if in$<"@" or in$>pr1.max.drive$ then \
		print bell$;tab(5);emsg$(13):goto 440
	in.drive%=fn.drive.in%(in$)
	return
460	rem-----request output file name-------------------------
	print
	print tab(10);"Enter name of sorted output file (1-8 chars) ";
	gosub 117			rem get in$
	if back% or stopit% then return
	if in$=null$ or len(in$)>8 then \
		print bell$;tab(5);emsg$(14):goto 460
	if match(".",in$,1)>0 or        \
	   match(" ",in$,1)>0 or        \
	   match("*",in$,1)>0 or        \
	   match("\?",in$,1)>0 or       \
	   match(":",in$,1)>0 then      \
		print bell$;tab(5);emsg$(15):goto 460
	out.name$=ucase$(in$)
	return
480	rem-----request output file type-------------------------
	out.type$="nad"
	return
500	rem-----request output file drive------------------------
	print
	print tab(10);"Enter sorted output file drive (@,A-F;RET=CURLOG) ";
	gosub 117			rem get in$
	if back% or stopit% then return
	if len(in$)>1 \
		then	print bell$;tab(05);emsg$(16):goto 500
	if in$<>null$ then in$=ucase$(in$)
	if in$=return$ then in$="@"
	if in$<"@" or in$>pr1.max.drive$ then \
		print bell$;tab(5);emsg$(17):goto 500
	out.drive%=fn.drive.in%(in$)
	return
600	rem-----request file length------------------------------
	print
	print tab(10);"Enter length of nad file reference field (0-127) ";
	gosub 117			rem get in$
	if back% or stopit% then return
	if in$=return$ then in$="0"
	if not fn.num%(in$) \
		then	print bell$;tab(5);emsg$(18):goto 600
	in%=val(in$)
	if in%<0 or in%>127 \
		then	print bell$;tab(5);emsg$(19):goto 600
	nad.len%=129+in%
	return
3000	rem-----create file------------------------------
	if end #srt.file% then 3099
	create fn.file.name.out$(parm.name$,"srt",common.drive%,null$,null$) \
		as srt.file%
	if end #srt.file% then 4000
	return
3099	rem-----here on eof on create-------------------
	print bell$;tab(5);emsg$(20)
	stop
4000	rem-----here on eof on write---------------------
	print bell$;tab(5);emsg$(21)
	stop
3300	rem-----write srt file-----------------------------
	print #srt.file%;\
		srt.record$
	return
3100	rem-----get name info----------------------------
	in.drive$=chr$(in.drive%)
	srt.in.drive$= in.drive$
	srt.in.name$=in.name$
	srt.in.type$=in.type$
	out.drive$=chr$(out.drive%)
	srt.out.drive$= in.drive$
	srt.out.name$=out.name$
	srt.out.type$=out.type$
	srt.rec.length%= nad.len%
	srt.backup.flag%=backup%
	srt.console.flag% = console.messages%
	srt.work.drive$=drive.a$
	gosub 3110			rem get name key info
	return
3110	rem-----get name key info--------------------------
	srt.kpos%(1)=1
	srt.klen%(1)=30
	srt.kad$(1)="A"
	srt.kan$(1)="A"
	return
3200	rem-----get postcode info----------------------------
	in.drive$=chr$(in.drive%)
	srt.in.drive$= in.drive$
	srt.in.name$=in.name$
	srt.in.type$=in.type$
	out.drive$=chr$(out.drive%)
	srt.out.drive$= in.drive$
	srt.out.name$=out.name$
	srt.out.type$=out.type$
	srt.rec.length%= nad.len%
	srt.backup.flag%=backup%
	srt.console.flag% = console.messages%
	srt.work.drive$=drive.a$
	gosub 3220			rem get name key info
	return
3220	rem-----get zip key info--------------------------
	srt.kpos%(1)=100
	srt.klen%(1)=8
	srt.kad$(1)="A"
	srt.kan$(1)="A"
	return

