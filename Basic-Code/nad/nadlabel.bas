#include "indcomm.bas"
prgname$ = "NADLABEL  FEB.   12, 1980"
rem-----------------------------------------------------------------
rem
rem	    N A M E   A N D   A D D R E S S
rem		 F I L E   S Y S T E M
rem
rem	       L A B E L   P R O G R A M
rem
rem	   copyright (c) 1977,1978  APPLEWOOD COMPUTERS
rem        and Vincent B Coen  1979 - 2025
rem
rem	   UK version changes by Vincent B Coen & APPLEWOOD COMPUTERS
rem              Copyright (c) 1980 - 2025
rem
rem -----------------------------------------------------------------
program$="NADLABEL"
cpyrght$="COPYRIGHT (C) 1979 - 2025 APPLEWOOD COMPUTERS."
version$="VER: 3.01 UK"
true = -1:false = 0:forever = true
return$ = ""
true%=true:false%=false
back$="^"
stop$=chr$(27)
null$=""
bell$=chr$(7)
lines.per.page = 58
test.name$ = "*****"+"*****"+"*****"+"*****"+"*****"
file.nad.no = 1
dim field.len(8)
dim nad$(8)
dim nad.field$(5,4)  rem **** UK version change ****
dim tab.loc(4)
dim emsg$(20)
emsg$(1)= "NAD300 FILE NOT FOUND"
emsg$(2)= "NAD301 INVALID FIELD SPECIFIED"
emsg$(3)= "NAD302 FIELD LENGTHS NOT EQUAL"
emsg$(4)= "NAD303 STARTING LOCATION + LENGTH OF PATTERN OVERFLOWS FIELD LENGTH"
emsg$(5)= "NAD304 FIRST STARTING LOCATION GREATER THAN LAST STARTING LOCATION"
emsg$(6)= "NAD305 LAST STARTING LOCATION VALUE TOO LARGE"
emsg$(7)= "NAD320 INVALID LOCATION SPECIFIED"
emsg$(8)= "NAD321 TRY AGAIN, I CAN ONLY SKIP 5 THROUGH 50 LINES BETWEEN LABELS"
emsg$(9)= "NAD306 VALUE LESS THAN ONE"
emsg$(10)="NAD307 LOW VALUE GREATER THAN HIGH VALUE"
emsg$(11)="NAD311 RECORD NUMBER SPECIFIED OUT OF RANGE"
emsg$(12)="NAD312 TRY AGAIN, ONLY 1 THROUGH 25 DUPLICATIONS ALLOWED"
emsg$(13)="NAD313 TRY AGAIN, YOUR ANSWER WAS NOT A NUMBER"
emsg$(14)="NAD314 TRY AGAIN, I CAN ONLY PRINT 1 THROUGH 4 LABELS ACROSS"
emsg$(15)="NAD315 TRY AGAIN, YOUR ANSWER WAS NOT A NUMBER"
emsg$(16)="NAD316 TRY AGAIN, YOUR ANSWER WAS NOT A NUMBER"
emsg$(17)="NAD317 RECORD NUMBER SPECIFIED OUT OF RANGE"
emsg$(18)="NAD318 RECORD NUMBER SPECIFIED OUT OF RANGE"
field.len(1) = 30		rem  name
field.len(2) = 30		rem  addr1
field.len(3) = 25		rem  addr2
field.len(4) = 24		rem  city
field.len(5) = 0		rem  state not used on UK version ****
field.len(6) = 8		rem  postcode **** UK version change ****
field.len(7) = 13		rem  phone
field.len(8) = 127		rem  ref
5	rem-----here on second time around---------------------------
	match.flag = false
	range.flag = false
	not.flag = false
	dup.wanted = false
	line.cnt = 100
	page.cnt = 0
	record.number = 0
	number.selected = 0
	tab.loc(1) = 1
	number.across = 1
	number.read = 0
	eof.flag = false
	skips.wanted = 3
	envelopes.wanted = false
100	REM----THIS IS THE PROGRAM DRIVER-----------------------------
	for m%=1 to 24:print:next m%
	print tab(10);"NADLABEL"
	print:print:print
	gosub 10			REM  GET THE FILE NAME
	if stopit% then goto 999999
	if common.drive$=null$ \
		then	gosub 11 \	REM  GET THE DRIVE NAME
		else	drive$=common.drive$+":"
	if stopit% then goto 999999
	file.name$ = drive$ + file.name$ + ".nad"       rem  append file type
	if end #1 then 1000		 rem  print error if no file
#include "indsize.bas"
	open file.name$ recl nad.rec.len as 1
	if end #1 then 5909.1		  rem  routine for normal eof
	print
		print tab(10);"Do you want to select records (Y or N)?";
		input ""; line in$
		if ucase$(in$)="Y" or ucase$(in$)="YES" \
			then	goto 105 \
			else	goto 200
105	rem -- build selection parameters-----------------------
	gosub 2800			rem  get correct field
	if done then goto 200		REM  JUMP OUT IF ONLY RECORD SELECTED
	gosub 2900			rem  get range or match
	print
	if range.flag  then  gosub 3000  :\    rem  range requests
		       else  gosub 3100        rem  match requests
200	rem-----request standard labels---------------------------
	print
	print tab(05);"STANDARD LABELS ARE:  1 LABEL PER NAME"
	print tab(05);"                      1 LABEL ACROSS"
	print tab(05);"                      PRINT STARTS IN COLUMN ONE"
	print tab(05);"                      6 LINES BETWEEN LABELS (1 INCH)"
	print tab(10);"Do you want standard labels? (Y,N,E=Envelopes) ";
	input ""; line in$
	in$=ucase$(in$)
	if in$ = "Y" or in$=return$ \
		then	goto 220
	if in$ = "N"  \
		then	goto 205
	if in$ = "E" \
		then	envelopes.wanted = true :\
			goto 205
205	rem-----request number of labels per name---------------------
	print
	print tab(10);"Enter number of labels per name ";
	input "";line in$
	if in$=return$ then in$="1"
	if in$=back$ then goto 200
	if match(left$("#####",len(in$)),in$,1)<>1 \
		then	print tab(5);bell$;emsg$(09) :\
			goto 205
	dup.number = val(in$)
	if dup.number<1 or dup.number>25 \
		then	print tab(5);bell$;emsg$(12) :\
			goto 205
	if dup.number > 1  then  dup.wanted = true
	last.loc = 0
207	rem-----request number of labels across--------------------
	print tab(10);"Enter number of labels across page (RET=1) ";
	input "";line in$
	if in$=return$ then in$="1"
	if in$=back$ then goto 205
	if match(left$("#####",len(in$)),in$,1)<>1 \
		then	print tab(5);bell$;emsg$(13) :\
			goto 207
	number.across=val(in$)
	if number.across<1 or number.across>04 \
		then	print tab(5);bell$;emsg$(14) :\
			goto 207
	tab.loc(00)=1
	tab.loc(01)=1		rem establish defaults
	tab.loc(02)=31
	tab.loc(03)=61
	tab.loc(04)=91
	for x%=1 to number.across
208
		print
		print tab(10);"Current value: ";
		print tab.loc(x%)
		print tab(10);"Enter starting print location of label ";
		print x%;
		input ""; line in$
		if in$=stop$ \
			then	goto 210		rem exit, done
		if in$=return$ \
			then	goto 209		rem break
		if in$=back$ and x%=1 \
			then	goto 207
		if in$=back$ and x%>1 \
			then	x%=x%-1 :\
				goto 208
		if match(left$("#####",len(in$)),in$,1)<>1 \
			then	print tab(5);bell$;emsg$(15) :\
				goto 208
		location%=val(in$)
		if location%<tab.loc(x%-1) or location%>103  \
			then	print tab(5);bell$;emsg$(07) :\
				goto 208
		tab.loc(x%)=location%
209
	next x%
210	rem-----request vertical spacing---------------------------
	skips%=6			rem default
	print
	print tab(10);"Current value: ";
	print skips%
	print tab(10);"Enter label vertical spacing in lines (5-50) ";
	input "";line in$     rem **** UK version change above ****
	if in$=return$ then in$=str$(skips%)
	if match(left$("#####",len(in$)),in$,1)<>1 \
		then	print tab(5);bell$;emsg$(16) :\
			goto 210
	skips%=val(in$)
	if skips%<3 or skips%>50 \
		then	print tab(5);bell$;emsg$(08) :\
			goto 210
	skips.wanted = skips% - 5  rem **** UK version change ****
220	rem-----print labels-------------------------------------
	print
	if not envelopes.wanted    then    \
		gosub 2100	    rem  print test form
	print
	while true
		gosub 2200		rem  read and select record
		gosub 2320		rem  deblank the name field
		gosub 8520		rem  look to see if interrupt
		if (eof.flag) or (end.wanted)  then  \
			gosub 2300  :\	     print the labels
			goto 5909	rem  end the program
		if dup.wanted  then  gosub 2325 \   move data dup.number times
			       else  gosub 2350  rem  move the data
		if number.read >= number.across  then  \
			gosub 2300	rem  print the labels
	wend
1000	rem--- come here if file not found on open------------------
	print tab(10);emsg$(1)
	for m%=1 to 1000:next m%	rem delay
	goto 100			rem  end of program
5909.1
	eof.flag = true
	return
5909
	rem--- normal eoj routine
	print
	print tab(10);"Print finished"
	print
	print tab(10);"There were";number.selected;"records written"
	print
	if number.deleted > 1  then  \
		print tab(10);		:\
		print "There are";number.deleted;"Deleted records on the file."
999999	rem-----e  o  j-----------------------------------------
	close 1
	print:print:print
	print tab(10);"Print labels for another nad file? (Y or N) ";
	input "";line in$
	print
	if ucase$(in$)="Y" or ucase$(in$)="YES" \
		then	goto 5		rem do it again
	lprinter:print:console		rem for centronics printers
	if chained.from.root%	\ rem **** UK version change ****
	then chain "NAD"        \ rem also fixes bug ****
	else stop
2100	REM----PRINT A TEST FORM-------------------------------
	while true%
		print tab(10);		\
		  "Would you like a dummy form printed? (Y or N;RET=N) ";
		input ""; line in$
		in$=ucase$(in$)
		if in$ = "N" or in$=return$ \
			then	return
		number.read = 0     rem **** UK version changes ****
		nad.name$	= "Dr. Peter X. Parker"
		nad.addr1$	= "134 West Street"
		nad.addr2$	= "Ilford"
		nad.city$	= "Essex"
		nad.state$	= ""
		nad.zip$	= "IG11 8NT"
		for i = 1 to number.across
			gosub 2350
		next i
		gosub 2300		REM  PRINT LABELS
	wend
2200	rem--- read and select record-------------------------------
	while true
		gosub 5905			rem  read a record
		if eof.flag   then  return	rem  return on end of file
		record.number = record.number + 1
		gosub 2400			rem  do we select this record?
		if selected then  \
			number.selected = number.selected + 1  :\
			return
	wend
2300	rem--- print the labels----------------------------------
	if number.read = 0  then  return       rem  must have been eof
	if envelopes.wanted  then  gosub 2375
	lprinter
	for j = 1 to 5	     rem ***** UK version changes here ****
		for i = 1 to number.read
			print tab(tab.loc(i));
			print nad.field$(j,i);
		next i
		print
		gosub 8505		REM  CHECK CONSOLE STATUS
		if end.wanted  then goto 5909
	next j
		rem **** UK version change ****
	for i = 1 to skips.wanted
		print
	next i
	number.read = 0
	console
	return
2320
	rem -- deblank the name field
	name.length = len(nad.name$)
	while name.length <> 0
		if mid$(nad.name$,name.length,1) = " "  \
			then  name.length = name.length - 1	\
			else  goto 2321
	wend
2321
	nad.name$ = left$(nad.name$,name.length)
	REM -- REVERSE NAMES IF NECESSARY
	ps = match("*",nad.name$,1)
	if ps then  \
		split = name.length - ps   :\
		nad.name$ = right$(nad.name$,split) + " " +  \
			    left$(nad.name$,ps-1)
	return
2325
	rem -- if duplicate labels wanted come here to move and print them
	for loop.count = 1 to dup.number
	   gosub 2350
	   if number.read >= number.across  then  gosub 2300  rem  print labels
	next loop.count
	return
2350
	rem -- move routine
	number.read = number.read + 1
	x = number.read
		nad.field$(1,x) = nad.name$
		nad.field$(2,x) = nad.addr1$
		nad.field$(3,x) = nad.addr2$
		nad.field$(4,x) = nad.city$
		nad.field$(5,x) = nad.zip$  rem **** UK version change ****
		rem **** UK version change ****
		f2blnk$ = "                         "
		f3blnk$ = "                  "
		f4blnk$ = "               "
		if match("?",nad.field$(2,x),1) = 0   or                \
		   match(f2blnk$,nad.field$(2,x),1) = 1  then  \
			nad.field$(2,x) = nad.field$(1,x)		:\
			nad.field$(1,x) = " "
		if match("?",nad.field$(3,x),1) = 0   or                \
		   match(f3blnk$,nad.field$(3,x),1) = 1  then  \
			nad.field$(3,x) = nad.field$(2,x)		:\
			nad.field$(2,x) = nad.field$(1,x)		:\
			nad.field$(1,x) = " "
	rem **** UK version additions here ****
		if match("?",nad.field$(4,x),1) = 0   or                \
		   match(f4blnk$,nad.field$(4,x),1) = 1  then  \
			nad.field$(4,x) = nad.field$(3,x)		:\
			nad.field$(3,x) = nad.field$(2,x)		:\
			nad.field$(2,x) = nad.field$(1,x)		:\
			nad.field$(1,x) = " "
	return
2375
	rem -- pause for envelopes
	print tab(10);"insert next envelope";
	print tab(10);"Hit return key to continue";
	input ""; line ans$
	return
5905	rem-----read nad file-------------------------------------
	eof.on.nad=false
	read #file.nad.no;\
#include "indnad.bas"
	return
8505	console
	gosub 8520
	if end.wanted  then return
	lprinter
	return
#include "indrss.bas"
#include "indint.bas"
#include "inddrve.bas"
