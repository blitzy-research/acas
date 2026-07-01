#include "indcomm.bas"
prgname$="NADENTRY  4    APR., 1980 "
rem-------------------------------------------------------
rem
rem    Name and Address File Maintenance System
rem	   copyright (c) 1977,1978  APPLEWOOD COMPUTERS
rem        and Vincent B Coen  1979 - 2025
rem
rem	   UK version changes by Vincent B Coen & APPLEWOOD COMPUTERS
rem       Copyright (c) 1980 - 2025
rem
rem    E N T R Y       P R O G R A M
rem-------------------------------------------------------
version$="NADENTRY VER:3.01 UK"           rem **** UK version change ****
cpyrght$=" COPYRIGHT (C) 1979 - 2025 APPLEWOOD COMPUTERS"
stop$=chr$(27)
back$="^"
force.blank$="\"
file.nad.no=1
default.len=129
max.space=83
blank32$="                                "
blank128$=blank32$+blank32$+blank32$+blank32$
unused25$="*************************"
tof$=chr$(12):bell$=chr$(7)
return$="":null$=""
true=-1:false=0
true%=-1:false%=0
quote$=chr$(34):ctlz$=chr$(26)
changing=false
international$="."
dim emsg$(25)
emsg$(01)="NAD121 INVALID FUNCTION"
emsg$(02)="NAD122 RECORD NUMBER OUT OF RANGE"
emsg$(03)="NAD123 RECORD HAS BEEN DELETED"
emsg$(04)="NAD124 REFERENCE IS TOO LONG"
emsg$(05)="NAD125 UNEXPECTED EOF ON NAD FILE"
emsg$(06)="NAD126 EMBEDDED QUOTES NOT ALLOWED"
emsg$(07)="NAD127 RECORD NUMBER OUT OF RANGE"
emsg$(08)="NAD128 TRY AGAIN, THE LENGTH YOU ENTERED EXCEEDS THE MAXIMUM."
emsg$(09)="NAD129 INPUT TOO LONG"
emsg$(10)="NAD130 RECORD HAS BEEN DELETED"
emsg$(11)="NAD131"      rem UK version change *****
emsg$(12)="NAD132 EMBEDDED CONTROL-Z NOT ALLOWED"
emsg$(13)="NAD133 EMBEDDED LINE FEED NOT ALLOWED"
emsg$(14)="NAD134 TRY AGAIN, A FILE NAME CAN'T CONTAIN A .:*? OR SPACE."
emsg$(15)="NAD135 TRY AGAIN, A DRIVE MUST BE AN A, B, C, D, E, F, OR @."
emsg$(16)="NAD136 SORRY, CAN'T GO BACK AT FIRST REQUEST"
emsg$(17)="NAD137"
emsg$(18)="NAD138"
rem---------------------------------------------------------------
name.len			=25
addr1.len			=25
addr2.len			=18
city.len			=15
state.len			=0   rem **** UK version
zip.len 			=8   rem	 changes ****
phone.len			=13
def fn.pad$(a$,q)=left$(a$+blank128$,q)
def fn.trunc$(a$,q)=left$(a$,q)
def fn.invalid.chars%(string$)
	if match(ctlz$,string$,1)<>0			 \
		then	print tab(05);emsg$(12) 	:\
			fn.invalid.chars%=true%:return
	if match(quote$,string$,1)<>0			 \
		then	print tab(05);emsg$(06) 	:\
			fn.invalid.chars%=true%:return
	if match(lf$,string$,1)<>0			 \
		then	print tab(05);emsg$(13) 	:\
			fn.invalid.chars%=true%:return
	fn.invalid.chars%=false%
	return
fend
rem-----------------------------------------------------------------
rem
rem	S  E  T 	U  P
rem
rem-----------------------------------------------------------------
for m%=1 to 24:print:next m%
print "NADENTRY"
print:print:print:print
gosub 9 			rem perform file foolaround
rem-----------------------------------------------------------------
rem
rem	M A I N        D R I V E R
rem
rem-----------------------------------------------------------------
while function$<>stop$
	stopit%=false%:cr%=false%
	gosub 100		rem ENTER FUNCTION
	if function$="A" then \
		gosub 200		rem add
	if function$="D" then \
		gosub 300		rem delete
	if function$="C" then \
		gosub 400		rem change
	if function$="E" then \
		gosub 500		rem examine
	if function$="S" then \
		gosub 600		rem save
wend
rem-----------------------------------------------------------------
rem
rem	E  O  J
rem
rem-----------------------------------------------------------------
nad.recs=no.recs
close file.nad.no
print:print:print
print tab(10);"NADENTRY completed"
print:print:print
if	chained.from.root%	\  rem **** UK version changes ****
	then chain "nad"        \  rem **** also fixes bug  ****
	else stop
rem-----------------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem-----------------------------------------------------------------
100	rem-----ENTER FUNCTION----------------------------------
	print
	while not adding
		print tab(10);"Enter function (A,C,D,E,S OR ESC)";
		input "";line function$
		function$=ucase$(function$)
		if function$="ADDING" then \
				function$="A" :\
				adding=true
		if function$="CHANGING" then \
				function$="C" :\
				adding=true
		if function$="DELETING" then \
				function$="D" :\
				adding=true
		if function$="A" OR \
			function$="D" OR \
			function$="C" OR \
			function$="E" or \
			function$="S" or \
			function$=stop$ then \
				return
		print tab(5);emsg$(1)
	wend
	return
200	rem-----A  D  D-------------------------------------------
	changes.done=false
	gosub 210		rem FIND NEXT AVAILABLE
	rec.nad.no=next.available
	gosub 1000		rem print NADDR NUMBER
	gosub 1150		rem CLEAR IN'S
	gosub 1200			rem move in's to nad's
	gosub 1110			rem clear all field flags
	gosub 1100		rem ENTER DEMOGRAPHIC DATA
	if in.name$=stop$ then \
		return
	gosub 1500			rem put old + changes in nad's
	gosub 2955			rem pad name field
	gosub 5907		rem WRITE NAD RANDOM
	no.recs=no.recs+1
	return
210	rem-----find next available-------------------------------
	next.available=no.recs+1
	return
300	rem-----D E L E T E---------------------------------------
	gosub 1300		rem REQUEST NADDR NUMBER
	if stopit% \
		then	adding=false	:\
			return
	if cr%	then	in.nad.no=1
	gosub 1900		rem VERIFY RECORD
	if not rec.exist.flag then \
		print tab(5);emsg$(10) :\
		return
	gosub 1410			rem print nad.name$
	gosub 1415			rem is delete ok?
	if not ok% then return
	format.no=in.nad.no
	gosub 1400		rem FORMAT NADDR RECORD
	return
400	rem-----C H A N G E----------------------------------------
	changing=true
	field1=true
	field2=true
	field3=true
	field4=true
	field5=true
	field6=true
	field7=true
	field8=true
	changes.done=false
	gosub 1300		rem REQUEST NADDR NUMBER
	if stopit% \
		then	adding=false	:\
			changing=false	:\
			return
	if cr%	then	in.nad.no=1
	gosub 1900		rem RECORD VERIFY
	if not rec.exist.flag then \
		print tab(5);emsg$(3) :\
		changing=false :\
		return
	gosub 2950			rem deblank name field
	gosub 1150		rem CLEAR IN'S
	gosub 1100		rem ENTER DEMOGRAPHIC DATA
	if in.name$=stop$ then \
		changing=false :\
		adding=false :\
		return
	gosub 1500		rem PUT OLD + CHANGES IN NAD'S
	gosub 2955		rem pad name field
	gosub 5907		rem WRITE NAD RAND
	changing=false
	return
500	rem-----e x a m i n e-----------------------------------
	exam.no=0
	print:print
	print tab(10);"E X A M I N E"
	while true
		gosub 510		rem request input
		if ans$=stop$ then \
				return
		gosub 530		rem display requested records
	wend
510	rem-----request input---------------------------
	print
	input "";line ans$
	if ans$=return$ then \
		times=1 :\
		exam.no=exam.no+1 :\
		return
	if ans$=stop$ then \
		return
	comma=match(",",ans$,1)
	exam.no=int(val(ans$))
	if comma=0 then \
		times=1 :\
		return
	ans$=right$(ans$,len(ans$)-comma)
	times=int(val(ans$))
	if times<1 then times=1
	return
530	rem-----display requested records-------------------
	bad.input=true
	while exam.no>0 and exam.no<=no.recs
		bad.input=false
		rec.nad.no=exam.no
		gosub 5904		rem read nad rand
		if nad.name$=unused25$ then \
			gosub 530.1 \	rem print deleted
		else \
			gosub 530.2	rem print record
		times=times-1
		if times=0 then \
				return
		gosub 8520		rem get constat
		if end.wanted then \
				return
		exam.no=exam.no+1
	wend
	if not bad.input or ans$=return$ then \
		print "         End of file" :\
		return
	print tab(5);emsg$(7)
	return
530.1	rem-----print deleted-----------------------
	print
	print using "##,###              Deleted";exam.no
	return
530.2	rem-----print record------------------------
	print
	gosub 2950			rem deblank name
	name$=nad.name$
	gosub 720			rem flip name
	if flipped then nad.name$=name$
	print using "##,###   &";exam.no,nad.name$
	print using "         &";nad.addr1$
	print using "         &";nad.addr2$
	print using "         &  &  &  &";      \
		nad.city$,nad.state$,nad.zip$,nad.phone$
	print using "         &";nad.ref$
	return
600	rem-----save------------------------
	print
	nad.recs=no.recs
	close file.nad.no
	gosub 13.2			rem open the nad file
	print tab(10);"Number of nad records saveD:  ";no.recs
	return
1000	rem-----print NADDR NUMBER---------------------------
	print
	print using "   Record number is ##,###";next.available
	return
1100	rem-----ENTER DEMO DATA---------------------------------
	gosub 3000		rem ENTER NAME
	if in.name$=stop$ then \
		adding=false :\
		return
	if changes.done then \
		return
1100.1	rem
	gosub 3200		rem ENTER addr1
	if go.back then \
		changing=true :\
		goto 1100
	if changes.done then \
		return
1100.2	rem
	gosub 3300		rem ENTER addr2
	if go.back then \
		changing=true :\
		goto 1100.1
	if changes.done then \
		return
1100.3	rem
	gosub 3400		rem ENTER addr3
	if go.back then \
		changing=true :\
		goto 1100.2
	if changes.done then \
		return
1100.4	rem
	gosub 3500		rem ENTER STATE note not used for UK version
	if go.back then \
		changing=true :\
		goto 1100.3
	if changes.done then \
		return
1100.5	rem
	gosub 3600		rem ENTER POSTCODE   UK version ****
	if go.back then \
		changing=true :\
		goto 1100.4
	if changes.done then \
		return
1100.6	rem
	gosub 3800		rem ENTER PHONE
	if go.back then \
		changing=true :\
		goto 1100.5
	if changes.done then \
		return
	gosub 3900		rem ENTER reference string
	if go.back then \
		changing=true :\
		goto 1100.6
	return
1110	rem-----clear all field flags----------------
	field1=false
	field2=false
	field3=false
	field4=false
	field5=false
	field6=false
	field7=false
	field8=false
	return
1150	rem-----CLEAR IN'S--------------------------------------
	in.name$=return$
	in.addr1$=return$
	in.addr2$=return$
	in.city$=return$
	in.state$=return$
	in.zip$=return$
	in.phone$=return$
	in.ref$=return$
	return
1200	rem-----MOVE IN'S TO NAD'S-----------------------------
	nad.name$=in.name$
	nad.addr1$=in.addr1$
	nad.addr2$=in.addr2$
	nad.city$=in.city$
	nad.state$=in.state$
	nad.zip$=in.zip$
	nad.phone$=in.phone$
	nad.ref$=in.ref$
	return
1300	rem-----ENTER NADDR NUMBER-------------------------
	cr%=false%:stopit%=false%
	print
	print tab(10);"Enter record number";
	input "";line in$
	if ucase$(in$)=stop$ \
		then	stopit%=true%	:\
			return
	if ucase$(in$)=return$ \
		then	cr%=true%	:\
			return
	in.nad.no=int(val(in$))
	if in.nad.no>0 and in.nad.no<=no.recs \
		then	return
	print tab(5);emsg$(2)
	goto 1300
1415	rem-----is delete ok?---------------
	print tab(10);"Type ""D"" If OK to Delete ";
	input "";line in$
	if ucase$(in$)="D" \
		then	ok%=true%	\
		else	ok%=false%
	return
1400	rem-----FORMAT NADDR RECORD------------------------
	rec.nad.no=format.no
	gosub 1700		rem MOVE unused'S TO NAD'S
	gosub 5907		rem WRITE NAD FILE RAND
	return
1410	rem-----print nad.name--------------------------------
	print
	gosub 2950			rem deblank name field
	name$=nad.name$
	gosub 720			rem flip name
	if flipped then nad.name$=name$
	print tab(10);"Name: ";nad.name$
	return
1500	rem-----PUT OLD + CHANGES IN NAD'S---------------------
	if not variable.length then goto 1510
	if in.name$<>return$ then \
		nad.name$=in.name$
	if in.addr1$<>return$ then \
		nad.addr1$=in.addr1$
	if in.addr2$<>return$ then \
		nad.addr2$=in.addr2$
	if in.city$<>return$ then \
		nad.city$=in.city$
	if in.state$<>return$ then \
		nad.state$=in.state$
	if international then nad.state$=null$
	if in.zip$<>return$ then \
		nad.zip$=in.zip$
	if in.phone$<>return$ then \
		nad.phone$=in.phone$
	if in.ref$<>return$ then \
		nad.ref$=in.ref$
	if match(left$(blank32$,len(nad.name$)),nad.name$,1)=1 then \
		nad.name$=return$
	if match(left$(blank32$,len(nad.addr1$)),nad.addr1$,1)=1 then \
		nad.addr1$=return$
	if match(left$(blank32$,len(nad.addr2$)),nad.addr2$,1)=1 then \
		nad.addr2$=return$
	if match(left$(blank32$,len(nad.city$)),nad.city$,1)=1 then \
		nad.city$=return$
	if len(nad.zip$)=8 then nad.state$=null$
	if nad.state$=null$ then \
		nad.zip$=fn.pad$(nad.zip$,8.0) rem **** UK version change *
	return
1510	rem-----here if at 1500 and not variable length--------------
	if in.name$<>return$ then \
		nad.name$=fn.pad$(in.name$,name.len) \
	else \
		nad.name$=fn.trunc$(nad.name$,name.len)
	if in.addr1$<>return$ then \
		nad.addr1$=fn.pad$(in.addr1$,addr1.len) \
	else \
		nad.addr1$=fn.trunc$(nad.addr1$,addr1.len)
	if in.addr2$<>return$ then \
		nad.addr2$=fn.pad$(in.addr2$,addr2.len) \
	else \
		nad.addr2$=fn.trunc$(nad.addr2$,addr2.len)
	if in.city$<>return$ then \
		nad.city$=fn.pad$(in.city$,city.len) \
	else \
		nad.city$=fn.trunc$(nad.city$,city.len)
	if in.state$<>return$ then \
		nad.state$=in.state$
	if international then nad.state$=null$
	if in.zip$<>return$ then \
		nad.zip$=in.zip$
	if in.phone$<>return$ then \
		nad.phone$=in.phone$
	if in.ref$<>return$ then \
		nad.ref$=in.ref$
	if len(nad.zip$)=8 then nad.state$=null$
	if nad.state$=null$ then \
		nad.zip$=fn.pad$(nad.zip$,8.0)	rem **** UK version change *
	return
1700	rem-----MOVE unused'S TO NAD'S-----------------------------
	nad.name$=unused25$
	nad.addr1$=left$(blank32$,25)
	nad.addr2$=left$(blank32$,18)
	nad.city$=left$(blank32$,15)
	return
1900	rem-----RECORD VERIFY---------------------------------
	rec.nad.no=in.nad.no
	gosub 5904		rem READ NAD FILE RANDOM
	if nad.name$=unused25$ \
		then	rec.exist.flag=false \
		else	rec.exist.flag=true
	return
2900	rem-----calc space left-------------------
	space.used=0
	if in.name$=return$ then \
		space.used=space.used+len(nad.name$) \
	else \
		space.used=space.used+len(in.name$)
	if in.addr1$=return$ then \
		space.used=space.used+len(nad.addr1$) \
	else \
		space.used=space.used+len(in.addr1$)
	if in.addr2$=return$ then \
		space.used=space.used+len(nad.addr2$) \
	else \
		space.used=space.used+len(in.addr2$)
	if in.city$=return$ then \
		space.used=space.used+len(nad.city$) \
	else \
		space.used=space.used+len(in.city$)
	space.left=max.space-space.used
	return
2950	rem-----deblank name field-------------------
	i%=len(nad.name$)
	if i%=0 then return
	if i%>30 then i%=30
	while mid$(nad.name$,i%,1)=" " and i%>1
		i%=i%-1
	wend
	nad.name$=left$(nad.name$,i%)
	return
2955	rem-----pad name field-----------------------
	if not variable.length then \
		nad.name$=fn.pad$(nad.name$,name.len) :\
		return
	changing=true
	gosub 2900			rem calc space left
	while space.left
		nad.name$=nad.name$+" "
		space.left=space.left-1
	wend
	return
3000	rem-----ENTER NAME----------------------------------
	if not field1 then changing=false
	gosub 2900			rem calc space left
	if changing then \
		space.left=space.left+len(nad.name$)
	if space.left>30 then \
		space.left=30
	if not variable.length then \
		space.left=name.len
	go.back=false
	print
	if changing then \
		print tab(10);nad.name$
3010	rem-----
	print tab(10);"Enter Name (";str$(space.left);")";
	input "";line in.name$
	if in.name$=stop$ and function$="C" then \
		changes.done=true :\
		in.name$=return$ :\
		return
	if in.name$=back$ \
		then	print tab(5);emsg$(16) :\
			goto 3010
	if in.name$=stop$ then return
	if in.name$=return$ and changing then \
		return
	if fn.invalid.chars%(in.name$) \
		then	goto 3010
	if len(in.name$)>space.left then \
		print tab(5);emsg$(9) :\
		goto 3010
	name$=in.name$
	gosub 720			rem flip name
	if flipped then print tab(10);name$
	if not variable.length then \
		in.name$=fn.pad$(in.name$,name.len)
	field1=true
	return
3200	rem-----ENTER ADDRESS LINE 1-------------------------------
	if not field2 then changing=false
	gosub 2900			rem calc space left
	if changing then \
		space.left=space.left+len(nad.addr1$)
	if space.left>30 then \
		space.left=30
	if not variable.length then \
		space.left=addr1.len
	go.back=false
	print
	if changing then \
		print tab(10);nad.addr1$
3210	rem-----
	print tab(10);"Enter line one of address (";str$(space.left);")";
	input "";line in.addr1$
	if in.addr1$=stop$ and function$="C" then \
		changes.done=true :\
		in.addr1$=return$ :\
		return
	if in.addr1$=stop$ \
		then	print tab(5);bell$;emsg$(17) :\
			goto 3210
	if in.addr1$=return$ and changing then \
		return
	if in.addr1$=back$ then \
		go.back=true :\
		in.addr1$=return$ :\
		gosub 1500 :\		rem put old+changes in nad's
		return
	if fn.invalid.chars%(in.addr1$) \
		then	goto 3210
	if len(in.addr1$)>space.left then \
		print tab(5);emsg$(9) :\
		goto 3210
	if not variable.length then \
		in.addr1$=fn.pad$(in.addr1$,addr1.len)
	field2=true
	return
3300	rem-----ENTER ADDRESS LINE TWO---------------------------
	if not field3 then changing=false
	gosub 2900			rem calc space left
	if changing then \
		space.left=space.left+len(nad.addr2$)
	if space.left>30 then \
		space.left=30
	if not variable.length then \
		space.left=addr2.len
	go.back=false
	print
	if changing then \
		print tab(10);nad.addr2$
3310	rem-----
	print tab(10);"Enter line two of address (";str$(space.left);")";
	input "";line in.addr2$
	if in.addr2$=stop$ and function$="C" then \
		changes.done=true :\
		in.addr2$=return$ :\
		return
	if in.addr2$=stop$ \
		then	print tab(5);bell$;emsg$(17) :\
			goto 3310
	if in.addr2$=return$ and changing then \
		return
	if in.addr2$=back$ then \
		go.back=true :\
		in.addr2$=return$ :\
		gosub 1500 :\		rem put old+changes in nad's
		return
	if fn.invalid.chars%(in.addr2$) \
		then	goto 3310
	if len(in.addr2$)>space.left then \
		print tab(5);emsg$(9) :\
		goto 3310
	if not variable.length then \
		in.addr2$=fn.pad$(in.addr2$,addr2.len)
	field3=true
	return
3400	rem-----ENTER CITY/ADDR3-(UK version)--------------------
	if not field4 then changing=false
	gosub 2900			rem calc space left
	if changing then \
		space.left=space.left+len(nad.city$)
	if space.left>24 then \
		space.left=24
	if not variable.length then \
		space.left=city.len
	go.back=false
	print
	if changing then \
		print tab(10);nad.city$
3410	rem-----
	print tab(10);"Enter line three of address (";str$(space.left);")";
	input "";line in.city$
	if in.city$=stop$ and function$="C" then \
		changes.done=true :\
		in.city$=return$ :\
		return
	if in.city$=stop$ \
		then	print tab(5);bell$;emsg$(17) :\
			goto 3410
	if in.city$=return$ and changing then \
		return
	if in.city$=back$ then \
		go.back=true :\
		in.city$=return$ :\
		gosub 1500 :\		rem put old+changes in nad's
		return
	if fn.invalid.chars%(in.city$) \
		then	goto 3410
	if len(in.city$)>space.left then \
		print tab(5);emsg$(9) :\
		goto 3410
	if not variable.length then \
		in.city$=fn.pad$(in.city$,city.len)
	field4=true
	return
3500	rem-----ENTER STATE-------------------------------------
	rem **** UK version changes here ****
	rem
	field5=true
	in.state$=null$
	international=true
	return
	rem
	rem **** UK version changes end here ****
	rem
3510	rem-----
	rem **** UK version makes this section redundant ****
3600	rem-----ENTER POSTCODE---------UK version ****----------
	if not field6 then changing=false
	go.back=false
	print
	if changing then \
		print tab(10);nad.zip$
3610	rem-----
	print tab(10);"Enter post code (8)";  rem **** UK version change ****
	input "";line in.zip$
	if in.zip$=stop$ and function$="C" then \
		changes.done=true :\
		in.zip$=return$ :\
		goto 3612
	if in.zip$=stop$ \
		then	print tab(5);bell$;emsg$(17) :\
			goto 3610
	if in.zip$=return$ and changing then \
		goto 3612
	if in.zip$=back$ then \
		go.back=true :\
		in.zip$=return$ :\
		gosub 1500 :\		rem put old+changes in nad's
		return
3611	rem-----
		max.length=8  rem **** UK version changes ****
	if len(in.zip$)>max.length then \
		print tab(5);emsg$(9) :\
		goto 3610
	if fn.invalid.chars%(in.zip$) \
		then	goto 3610
		in.zip$=fn.pad$(in.zip$,8.0)  rem **** UK version changes ****
	field6=true
	return
3612	rem
	if international then return
	rem **** UK version changes ****
3800	rem-----ENTER PHONE-----------------------------------
	if not field7 then changing=false
	go.back=false
	print
	if changing then \
		print tab(10);nad.phone$
3810	rem-----
	print tab(10);"Enter phone";
	input "";line in.phone$
	if in.phone$=stop$ and function$="C" then \
		changes.done=true :\
		in.phone$=return$ :\
		return
	if in.phone$=stop$ \
		then	print tab(5);bell$;emsg$(17) :\
			goto 3810
	if in.phone$=return$ and changing then \
		return
	if in.phone$=back$ then \
		go.back=true :\
		in.phone$=return$ :\
		gosub 1500 :\		rem put old+changes in nad's
		return
	if fn.invalid.chars%(in.phone$) \
		then	goto 3810
	if len(in.phone$)>13 then \
		print tab(5);emsg$(9) :\
		goto 3810
	in.phone$=left$(in.phone$+blank32$,13)
	field7=true
	return
3900	rem-----enter reference string-------------------------
	if not field8 then changing=false
	go.back=false
	print
	if ref.len<1	\
		then	in.ref$=return$ :\
			return
	print tab(26); \
		left$(	\
".........1....1....2.....2....3....3....4....5....5....6....6",        \
		ref.len)
	print tab(26); \
		left$(	\
"1234567890....5....0.....5....0....5....0....5....0....5....0",        \
		ref.len)
	if changing then \
		print tab(26);nad.ref$
3910	rem-----
	print tab(10);"Enter reference";
	input "";line in.ref$
	if in.ref$=stop$ and function$="C" then \
			changes.done=true :\
			in.ref$=return$ :\
			return
	if in.ref$=stop$ \
		then	print tab(5);bell$;emsg$(17) :\
			goto 3910
	if in.ref$=return$ and changing then \
			return
	if in.ref$=back$ then \
			go.back=true :\
			in.ref$=return$ :\
		gosub 1500 :\		rem put old+changes in nad's
			return
	if fn.invalid.chars%(in.ref$) \
		then	goto 3910
	if len(in.ref$)>ref.len then \
			print tab(5);emsg$(4) :\
			goto 3910
	gosub 800			rem substitute chars
	in.ref$=left$(in.ref$+blank128$,ref.len)
	field8=true
	return
rem--------------------------------------------------------------
9	rem-----perform file foolaround--------------------------
	while true
		gosub 10		rem ask file name
		gosub 11		rem ask file drive
		gosub 12		rem is the file there?
		if nad.exists then \
			gosub 13 :\	rem get file info
			gosub 830 :\	rem display reference length
			return
		gosub 14		rem request create
		if create.wanted then \
			gosub 15 :\	rem create the new file
			return
	wend
10	rem-----ask file name--------------------------------------
	print
	print tab(10);"Enter file name ";
	input "";line in$
	in$=ucase$(in$)
	if match("*",in$,1)<>0 or       \
	   match(".",in$,1)<>0 or       \
	   match(":",in$,1)<>0 or       \
	   match(" ",in$,1)<>0 or       \
	   match("\?",in$,1)<>0         \
		then	print tab(05);bell$;emsg$(14)	:\
			goto 10
	file.name$=left$(in$+blank32$,8)
	return
11	rem-----ask for drive---------------------
	print
	print tab(10);"Enter drive (@,A-F;RET=CURLOG) ";
	input "";line in$
	in$=ucase$(in$)
	if in$=return$ then in$="@"
	if in$="A" or in$="B" or in$="C" or         \
	   in$="D" or in$="E" or in$="F" or in$="@" \
		then	drive$=in$+":"   :\
			return
	print tab(05);bell$;emsg$(15)
	goto 11
12	rem-----is the file there?--------------------------------
	if end #8 then 12.1
	nad.exists=false
	open drive$+file.name$+".nad" as 8
	nad.exists=true
12.1	rem-----here if file not found----------------------------
	return
13	rem-----get file info-------------------------------------
	gosub 13.1			rem open nad as unblocked file
	gosub 730			rem get ref len and whether fixed
	file.nad.len=default.len+ref.len
	no.recs=nad.recs
	close file.nad.no
	gosub 13.2			rem open nad file as blocked
	gosub 740			rem find number of records on file
	gosub 760			rem set eof branch to error
	return
13.1	rem-----open nad as unblocked file-----------
	open drive$+file.name$+".nad" as file.nad.no
	return
13.2	rem-----open nad file as blocked-------------
	open drive$+file.name$+".nad" recl file.nad.len as file.nad.no
	if end #file.nad.no then 5909		rem normal eof branch
	return
14	rem-----request create new nad file------------
	print
	print tab(05);"I can't find any file by the name of: "; \
				file.name$;"  ";                \
				"On disk ";drive$
	print
	print tab(10);"I will create a new file by this name if you"
	print tab(10);"will type ""CREATE""."
	print tab(10);"If there has been a mistake, hit return and you"
	print tab(10);"Can retype the file name and drive.  ";
	input "";line ans$
	if ucase$(ans$)="CREATE" then \
			create.wanted=true :\
			return
	if ans$=return$ then \
			create.wanted=false :\
			return
	print bell$;tab(05);"I only understand ""CREATE"" or RETURN."
	goto 14
15	rem-----create nad file--------------------
	gosub 15.1			rem enter length of ref$
	gosub 830			rem display ref length
	gosub 780			rem ask if variable length
	file.nad.len=default.len+ref.len
	gosub 15.2			rem create the file
	no.recs=0
	nad.recs=no.recs
	close file.nad.no
	gosub 13.2			rem open nad file
	return
15.1	rem-----enter length of ref$------------------
	print
	print tab(10);"Enter the desired reference field length for this"
	print tab(10);"File.  the reference field can be from 1 to 127"
	print tab(10);"Characters long.  enter a zero (or hit return)"
	print tab(10);"If no reference field is desired. ";
	input "";line ref.len$
	ref.len=val(ref.len$)
	if default.len+ref.len<=256 then \  rem **** UK version change ****
		return
	print tab(5);emsg$(8)
	print tab(5);"The maximum reference length: ";256-default.len
	goto 15.1 rem **** UK version change line above ****
15.2	rem-----create nad file------------------------
	create drive$+file.name$+".nad" recl file.nad.len as file.nad.no
	if end #file.nad.no then 5909			rem normal eof branch
	return
5909	rem-----eof on nad file-----------------
	eof.on.nad=true
	return
720	rem-----flip name-------------------------------
	name$=left$(name$,30)
	flipped=false
	ast.loc%=match("*",name$,1)
	if ast.loc%<=1 or ast.loc%=len(name$) then return
	name$=right$(name$,len(name$)-ast.loc%)+" "+left$(name$,ast.loc%-1)
	flipped=true
	return
730	rem-----get ref len and whether fixed-----------------
	gosub 5905			rem read nad seq
	ref.len=len(nad.ref$)
	if len(nad.name$)<>name.len or \
	   len(nad.addr1$)<>addr1.len or \
	   len(nad.addr2$)<>addr2.len or \
	   len(nad.city$)<>city.len then \
		variable.length=true \
	else \
		gosub 780		rem ask if variable length
	return
740	rem-----find number of records on file-------------
	print
	print tab(10); "Please wait---counting records in file"
	end% = false%
rem------since crun2, at least 2.05 and earlier, gets lost when
rem------trying to read files > 1/2 meg, we are forced to resort
rem------to the following baroque method:  1 1/2 * highest first
rem------record no * record length cannot exceed 1/2 meg....
	highest.read = 342666/file.nad.len
	no.recs = int(highest.read)
	if pr1.debugging%  then \
		print "first rec no = "; no.recs
	eof.on.nad=true
	while eof.on.nad
		gosub 750		rem read randomly
		if eof.on.nad  then \
			no.recs = int(no.recs/2)
	wend
	if pr1.debugging%  then \
		print "first = "; no.recs
	rec.incr% = int(no.recs/2)
	no.recs = no.recs + rec.incr%
	while true%
		gosub 750		rem read random
		gosub 755		rem increment/decrement rec no
		if end%  then RETURN
	wend
	return
750	rem-----read nad file randomly-----------------------
	if no.recs=0 then no.recs=1
	rec.nad.no=no.recs
	gosub 5904			rem read nad rand
	return
755	rem-----increment/decrement no.recs--------
	if pr1.debugging%  then \
		print "755 no.recs = "; no.recs
	rec.incr% = int(rec.incr%/2)
	if rec.incr% = 0 and not eof.on.nad  then \
		end% = true%  :\
		RETURN
	if rec.incr% = 0  then \
		rec.incr% = 1
	if eof.on.nad  then \
		no.recs = no.recs - rec.incr% \
	   else \
		no.recs = no.recs + rec.incr%
	return
760	rem-----set eof branch to error-----------------------
	if end #file.nad.no then 770
	return
770	rem-----here on abnormal eof--------------------------
	print
	print tab(5);bell$;emsg$(05)
	stop
780	rem-----ask if variable length-------------------------
	print
	print tab(10);"Variable length? (Y or N) ";
	gosub 6.000			rem enter y or n
	if yes% or cr% then variable.length=true
	return
800	rem-----substitute chars-------------------------------
	gosub 810			rem substitute from nad.ref$
	gosub 820			rem substitute blanks
	return
810	rem-----substitute from nad.ref$-----------------------
	i%=1
	while i%<=len(nad.ref$)
		if len(in.ref$)<i% then \
			in.ref$=in.ref$+ \
			  right$(nad.ref$,len(nad.ref$)-len(in.ref$)) :\
			return
		if mid$(in.ref$,i%,1)=" " then \
			in.ref$=left$(in.ref$,i%-1)+ \
			  mid$(nad.ref$,i%,1) + \
			  right$(in.ref$,len(in.ref$)-i%)
		i%=i%+1
	wend
	return
820	rem-----substitute blanks-------------------------------
	i%=1
	while i%<=len(in.ref$)
		if mid$(in.ref$,i%,1)=force.blank$ then \
			in.ref$=left$(in.ref$,i%-1)+" "+ \
			  right$(in.ref$,len(in.ref$)-i%)
		i%=i%+1
	wend
	return
830	rem-----display ref length------------------------------
	print
	print tab(10);"Reference field length:    ";ref.len
	print tab(10);"Total record length:       ";ref.len+129
	print tab(10);"Number of records in file: ";no.recs
	return	rem **** UK version change 2 lines above ****
5905	rem-----read nad file seq----------------
	eof.on.nad=false
	read #file.nad.no;\
#include "indnad.bas"
	return
5904	rem-----read nad file random-------------
	eof.on.nad=false
	read #file.nad.no,rec.nad.no; \
#include "indnad.bas"
	return
5907	rem-----write nad file rand--------------
	print #file.nad.no,rec.nad.no;\
#include "indnad.bas"
	return
6.000	rem-----edit yes,no----------------------------------
	yes%=false%:no%=false%:cr%=false%
	input ""; line in$
	in$=ucase$(in$)
	if in$="Y" or in$="YES"         \
		then	yes%=true%	:\
			return
	if in$="N" or in$="NO"          \
		then	no%=true%	:\
			return
	if in$=return$			\
		then	cr%=true%	:\
			return
	print bell$;tab(5); "(Y or N ONLY)  ";
	goto 6.000
#include "indint.bas"
