#include "indcomm.bas"
prgname$ = "NADXTRAK   3    APR., 1980"
rem------------------------------------------------------------------
rem
rem	    N A M E   A N D   A D D R E S S
rem		 F I L E   S Y S T E M
rem
rem	     E X T R A C T   P R O G R A M
rem
rem	   copyright (c) 1977,1978  APPLEWOOD COMPUTERS
rem      AND Vincent B Coen.
rem
rem	   UK version changes by Vincent B Coen & Applewood Computers
rem         Copyright (c) 1980 - 2025
rem
rem -----------------------------------------------------------------
5	rem-----here on second time around---------------------------
	copyright$="Copyright (c) 1979-2025 Applewood Computers"
	version.number$=" NADXTRAK VERSION 3.01 UK"
	true = -1
	false = 0
	forever = true
	return$ = ""
	lf$ = chr$(10)
	lf4$ = lf$+lf$+lf$+lf$
	first.time = true
	lines.per.page = 58
	line.cnt = 100
	page.cnt = 0
	record.number = 0
	number.selected = 0
	test.name$ = "*****"+"*****"+"*****"+"*****"+"*****"
	s.b$ = "     " + "     " + "     " + "     " + "     "
	long.blank$ = s.b$ + s.b$ + s.b$ + s.b$ + s.b$ + "  "
	blank30$ = "        "
	change.ref.flag = false
	rename.needed = false
	file.nad.no = 1
	match.flag = false
	range.flag = false
	not.flag = false
	dim field.len(8)
	dim nad$(8)
	dim emsg$(11)
	emsg$(1) =  "NAD 300 -- FILE NOT FOUND"
	emsg$(2) =  "NAD 301 -- INVALID FIELD SPECIFIED"
	emsg$(3) =  "NAD 302 -- FIELD LENGTHS NOT EQUAL"
	emsg$(4) =  "NAD 303 -- STARTING LOCATION + LENGTH OF PATTERN" +  \
			      " OVERFLOWS FIELD LENGTH"
	emsg$(5) =  "NAD 304 -- FIRST STARTING LOCATION GREATER THAN LAST" + \
				" STARTING LOCATION"
	emsg$(6) =  "NAD 305 -- LAST STARTING LOCATION VALUE TOO LARGE"
	emsg$(7) =  "NAD 310 -- OUTPUT FILE EXISTS"
	emsg$(8) =  "NAD 312 -- INVALID REFERENCE LENGTH SPECIFIED"
	emsg$(9) =  "NAD 306 -- VALUE LESS THAN ONE"
	emsg$(10) = "NAD 307 -- LOW VALUE GREATER THAN HIGH VALUE"
	emsg$(11) = "NAD 311 -- RECORD NUMBER SPECIFIED OUT OF RANGE"
	field.len(1) = 30		rem  name
	field.len(2) = 30		rem  addr1
	field.len(3) = 30		rem  addr2
	field.len(4) = 24		rem  city
	field.len(5) = 0		rem  state *** NOT USED ON UK VERSION
	field.len(6) = 8		rem  postcode **** UK version change
	field.len(7) = 13		rem  phone
	field.len(8) = 127		rem  ref
100
	rem--- this is the program driver
	for m%=1 to 24:print:next m%
	print tab(10);"NAD EXTRACT"
	print:print:print:print
	name.of.file$ = " INPUT"
	gosub 10		REM  SET FILE NAME
	gosub 11		REM  SET DRIVE NAME
	in.file$ = file.name$
	in.drive$ = drive$
	file.name$ = drive$ + file.name$ + ".nad"       REM  BUILD NAME
	if end #1 then 1000
#include "indsize.bas"
	open file.name$ recl nad.rec.len as 1
	if end #1 then 5909		  rem  routine for normal eof
	print
103
	name.of.file$ = " OUTPUT"
	gosub 10
	if (file.name$ = "STOP") or (file.name$ = "stop")  then  \
					goto 999999	  rem  end the program
	gosub 11			REM  GET THE DRIVE REFERENCE
	if file.name$ = in.file$  then		 \
			out.file.name$ = drive$ + file.name$ + ".$$$"   :\
			rename.needed = true			  :\
			gosub 3600				  :\ delete bak
		else				\
			out.file.name$ = drive$ + file.name$ + ".nad"
	if size(out.file.name$) > 0  then  \
			print emsg$(7)	  :\
			goto 103
	print
	while true
		print tab(10);"Do you want to select records (Y or N)?";
		input ""; line ans$
		if (ans$ = "Y") or (ans$ = "y")  then  goto 105
		if (ans$ = "N") or (ans$ = "n")  then  goto 200
	wend
105
	rem -- build selection parameters
	gosub 2800			rem  get correct field
	if done then goto 200		REM  JUMP OUT IF ONLY REC # SELECTED
	gosub 2900			rem  get range or match
	print
	if range.flag  then  gosub 3000  :\    rem  range requests
		       else  gosub 3100        rem  match requests
200
	new.nad.rec.len = nad.rec.len
	print
	print tab(10);"Current reference field length is";field.len(8)
	print tab(10);"Type return if ok, enter new length if desired";
	input ""; line ans$
	if ans$ = ""  then  goto 205
	new.ref.leng = val(ans$)
	if (new.ref.leng < 0) or (new.ref.leng > 127)  then  \
				print emsg$(8)		    :\
				goto 200
	new.nad.rec.len = new.ref.leng + 129  rem **** UK version change *
	change.ref.flag = true
205
	create out.file.name$ recl new.nad.rec.len as 2
	print
	print tab(10);"Extract in progress";
	print
	while true
		gosub 2200		rem  read and select record
		gosub 5906		rem  write the line
	wend
1000
	rem--- come here if file not found on open
	print tab(10);emsg$(1)
	goto 100			rem  end of program
5909.1
5909
	rem--- normal eoj routine
	close 1,2
	if rename.needed  then	  \
		newname$ = in.drive$ + in.file$ + ".bak"                :\
		oldname$ = in.drive$ + in.file$ + ".nad"                :\
		nothing = rename(newname$,oldname$)	:\
		gosub 3610	:\    DELETE TYPE NAD IF NECESSARY
		newname$ = drive$ + file.name$ + ".nad"         :\
		oldname$ = drive$ + file.name$ + ".$$$"         :\
		nothing = rename(newname$,oldname$)
	print tab(10);"Print finished"
	print
	print tab(10);"There were";number.selected;"records written"
	print
	if number.deleted > 1  then  \
		print tab(10);"There are";number.deleted;                :\
		print "deleted records on the input file."
999999
	print:print:print
	print tab(10);"Extract another nad file? (Y or N) ";
	input "";line in$
	print
	if ucase$(in$)="Y" or ucase$(in$)="YES" \
		then	goto 5		rem do it again
	if chained.from.root%	\ rem **** UK version change ****
	then chain "nad"        \ rem **** also fixes bug ****
	else stop
2200
	rem--- read and select record
	while true
		gosub 5905			rem  read a record
		record.number = record.number + 1
		gosub 2400			rem  do we select this record?
		if selected then  \
			number.selected = number.selected + 1  :\
			return
	wend
#include "indrss.bas"
3600
	rem -- delete bak file if it exists
	if end #3 then 3600.1
	open in.drive$ +in.file$ + ".bak" as 3
	delete 3
3600.1
	return
3610
	REM -- DELETE TYPE NAD IF IT EXISTS
	if end #3  then  3610.1
	open drive$ + file.name$ + ".nad" as 3
	delete 3
3610.1
	return
5905	rem-----read nad file seq----------------
	eof.on.nad=false
	read #file.nad.no;\
#include "indnad.bas"
	return
5906	rem -- write nad file sequential
	nad.phone$ = left$(nad.phone$+"              ",13)
	if change.ref.flag  then  \
		nad.ref$ = nad.ref$ + long.blank$     :\
		nad.ref$ = left$(nad.ref$,new.ref.leng)
	print #2;  \
#include "indnad.bas"
	return
#include "inddrve.bas"

