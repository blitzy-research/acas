#include "indcomm.bas"
prgname$ = "NADPRINT    JAN.  22, 1980"
rem-----------------------------------------------------------------
rem
rem	    N A M E   A N D   A D D R E S S
rem		 F I L E   S Y S T E M
rem
rem	       P R I N T   P R O G R A M
rem
rem	   copyright (c) 1977,1978  APPLEWOOD COMPUTERS
rem      and Vincent B Coen  1979 - 2023
rem
rem	   UK version changes by Vincent B Coen & APPLEWOOD COMPUTERS
rem             Copyright (c) 1980 - 2025
rem
rem -----------------------------------------------------------------
program$="NADPRINT"
cpyrght$="COPYRIGHT (C) 1979-2025 APPLEWOOD COMPUTERS"
version.number$="VER: 3.01 UK"   rem **** UK version change ****
true = -1:false = 0:forever = true:return$ = ""
true%=true:false%=false
lines.per.page = 58
test.name$ = "*****"+"*****"+"*****"+"*****"+"*****"
file.nad.no = 1
back$="^":stop$=chr$(27):bell$=chr$(7)
null$=""
dim field.len(8)
dim nad$(8)
dim emsg$(11)
emsg$(1)="NAD300 FILE NOT FOUND"
emsg$(2)="NAD301 INVALID FIELD SPECIFIED"
emsg$(3)="NAD302 FIELD LENGTHS NOT EQUAL"
emsg$(4)="NAD303 STARTING LOCATION + LENGTH OF PATTERN OVERFLOWS FIELD LENGTH"
emsg$(5)="NAD304 FIRST STARTING LOCATION GREATER THAN LAST STARTING LOCATION"
emsg$(6)="NAD305 LAST STARTING LOCATION VALUE TOO LARGE"
emsg$(7)="NAD306 VALUE LESS THAN ONE"
emsg$(8)="NAD307 LOW VALUE GREATER THAN HIGH VALUE"
emsg$(9)="NAD308 RECORD NUMBER SPECIFIED OUT OF RANGE"
emsg$(10)="NAD309 "
emsg$(11)="NAD311 RECORD NUMBER SPECIFIED OUT OF RANGE"
field.len(1) = 30		rem  name
field.len(2) = 30		rem  addr1
field.len(3) = 25		rem  addr2
field.len(4) = 24		rem  city
field.len(5) = 0		rem  state not used in UK version ****
field.len(6) = 8		rem  postcode *** UK version change ****
field.len(7) = 13		rem  phone
field.len(8) = 127		rem  ref
dim out.date$(3)
def fn.date.out$(date$)
	out.date$(pr1.date.mo%)=mid$(date$,3,2)
	out.date$(pr1.date.dy%)=mid$(date$,5,2)
	out.date$(pr1.date.yr%)=mid$(date$,1,2)
	fn.date.out$=out.date$(1)+"/"+out.date$(2)+"/"+out.date$(3)
	return
fend
if pr1.date.format%=1 \  rem **** UK version changes here ****
	then	pr1.date.mo%=1:pr1.date.dy%=2:pr1.date.yr%=3
if pr1.date.format%=2 or pr1.date.format%=0 \
	then	pr1.date.mo%=2:pr1.date.dy%=1:pr1.date.yr%=3
5	rem-----here when going around again-------------------------
	line.cnt = 100
	page.cnt = 0
	record.number = 0
	not.flag = false
	number.selected = 0
	match.flag = false
	range.flag = false
100	REM----THIS IS THE PROGRAM DRIVER-----------------------------
	for m%=1 to 24:print:next m%	rem clear screen
	print tab(10);"nadprint"
	print:print:print
	gosub 10			REM  GET THE FILE NAME
	if stopit% then goto 999999
	if common.drive$=null$ \
		then	gosub 11 \	REM  GET THE DRIVE NAME
		else	drive$=common.drive$+":"
	if stopit% then goto 999999
	file.name$ = drive$ + file.name$ + ".nad"       REM BUILD FILE NAME
	if end #1 then 1000	REM  PRINT ERROR IF NO FILE
#include "indsize.bas"
	open file.name$ recl nad.rec.len as 1
	if end #1 then 5909		  rem  routine for normal eof
	print
	print tab(10);"Do you want to select records (Y or N)?";
	input ""; line in$
	if ucase$(in$)="Y" or ucase$(in$)="YES" \
		then	goto 105	\
		else	goto 200
105	rem----build selection parameters-------------------------
	gosub 2800			rem  get correct field
	if done then goto 200		REM  JUMP OUT OF ONLY RECORD # SELECTED
	gosub 2900			rem  get range or match
	print
	if range.flag  then  gosub 3000  :\    rem  range requests
		       else  gosub 3100        rem  match requests
200
	print
	while true
		gosub 2200		rem  read and select record
		gosub 2300		REM  PRINT THE LINE
		gosub 8520		rem  look to see if interrupt
		if end.wanted  then  goto 5909	  rem  end the program
	wend
1000	rem--- come here if file not found on open----------------
	print tab(10);emsg$(1)
	for m%=1 to 1000:next m%	rem delay
	goto 100			rem  end of program
5909.1
5909
	rem--- normal eoj routine
	print tab(10);"Print finished"
	print
	print tab(10);"There were";number.selected;"records written"
	print
	if number.deleted > 1  then  \
		print tab(10);		:\
		print "There are";number.deleted;"Deleted records on the file."
999999
	close 1
	print:print:print
	print tab(10);"Print another NAD file? (Y or N) ";
	input "";line in$
	print
	if ucase$(in$)="Y" or ucase$(in$)="YES" \
		then	goto 5		rem do it again
	lprinter:print:console		rem for centronics printers
	if chained.from.root%	\ rem **** UK version change ****
	then chain "nad"        \ rem **** also fixes bug ****
	else stop
2100	rem----print the header------------------------------------
	lprinter
	print chr$(12)			rem form feed
	page.cnt = page.cnt + 1
	rem-----line one------------------------------------
	print tab(001);"FILE: ";
	print tab(007);file.name$;
company.name$="N A D  --  N A M E    A N D    A D D R E S S    S Y S T E M"
	x%=(132-len(company.name$))/2
	print tab(x% );company.name$;
	print tab(118);"PAGE: ";
	print tab(124);page.cnt
	rem-----line two------------------------------------
	report.name$="N A D    F I L E    P R I N T"
	x%=(132-len(report.name$))/2
	if chained.from.root%		\ rem **** UK version changes ****
	then print tab(x% );report.name$;	:\
	     print tab(118);"DATE: ";          :\ rem **** also fixes bug *****
	     print tab(124);fn.date.out$(common.date$) \
	else print tab(x% );report.name$
	rem-----line three----------------------------------
	print				rem blank line
	rem-----line four-----------------------------------
	print tab(001);"RECORD";
	rem **** UK version change ****
	rem-----line five-----------------------------------
	print tab(001);"NUMBER";
	print tab(012);"NAME";
	print tab(053);"ADDRESS";
	rem **** UK version change ****
	print tab(106);"POSTCODE";
	print tab(119);"PHONE NUMBER"
	rem-----line six------------------------------------
	print				rem blank line
	rem-----line seven----------------------------------
	print				rem blank line
	line.cnt=7
	console
	return
2200	rem--- read and select record-------------------------------
	while true
		gosub 5905			rem  read a record
		record.number = record.number + 1
		gosub 2400			rem  do we select this record?
		if selected then  \
			number.selected = number.selected + 1  :\
			return
	wend
2300	rem--- print the record--------------------------------------
	if line.cnt > lines.per.page  then  gosub 2100	rem  print the header
	lprinter
		print using "####";record.number;
	rem  deblank and set up name field
		name.length = len(nad.name$)
		length.left = 83 - name.length
		while name.length <> 0
			if mid$(nad.name$,name.length,1) = " "  \
				then  name.length = name.length -1  \
				else  goto 2305
		wend
2305
		nad.name$ = left$(nad.name$,name.length)
		REM -- REVERSE NAMES IF NECESSARY
		ps = match("*",nad.name$,1)
		if ps then   \
			split = name.length - ps      :\
			nad.name$ = right$(nad.name$,split) + " " +   \
				    left$(nad.name$,ps-1)
		print tab(9);nad.name$;
		if length.left > 58 or pos >= 37		\
				then   print "   ";     \
				else   print tab(37);
		print nad.addr1$;
		length.left = length.left - len(nad.addr1$)
		if length.left > 33  or  pos >= 65			\
				then   print "   ";                     \
				else   print tab(65);
		print nad.addr2$;
		length.left = length.left - len(nad.addr2$)
		if length.left > 15  or  pos >= 85			\
				then   print "   ";                     \
				else   print tab(85);
		print nad.city$;
		if pos >= 104	then   print " ";       \
				else   print tab(104);
		rem **** UK version change ****
		print tab(106);nad.zip$;   rem **** UK version ****
		print tab(119);nad.phone$
	if len(nad.ref$) <> 0	then  \
		print nad.ref$	:\
		line.cnt = line.cnt + 1
	print						rem  skip a line
	line.cnt = line.cnt + 2
	console
	return
5905	rem-----read nad file seq----------------
	eof.on.nad=false
	read #file.nad.no;\
#include "indnad.bas"
	return
#include "indrss.bas"
#include "indint.bas"
#include "inddrve.bas"
