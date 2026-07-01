rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYAP1 - 12/21/79

crt.field.count% = 25	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  67,3,12,0,17,\       rem   IO fld #1
	  16,10,55,0,17,\	rem   IO fld #2
	  16,11,55,0,17,\	rem   IO fld #3
	  42,9,5,0,17,\       rem   IO fld #4
	  48,9,27,0,17,\       rem   IO fld #5
	  38,13,8,0,17,\       rem   IO fld #6
	  49,13,8,0,25,\       rem   IO fld #7
	  60,13,1,0,25,\       rem   IO fld #8
	  25,21,30,0,17,\	rem   IO fld #9
	  65,15,3,0,25,\       rem   IO fld #10
	  45,12,8,0,17,\       rem   IO fld #11
	  1,2,9,0,4,\	    rem   O fld #12
	  1,3,8,0,4,\	    rem   O fld #13
	  10,3,8,0,4,\	     rem   O fld #14
	  12,9,30,0,0,\       rem   O fld #15
	  20,13,38,0,0,\       rem   O fld #16
	  16,13,46,0,0,\       rem   O fld #17
	  18,15,42,0,0,\       rem   O fld #18
	  10,15,61,0,0,\       rem   O fld #19
	  17,23,43,0,0,\       rem   O fld #20
	  15,23,47,0,0,\       rem   O fld #21
	  21,23,36,0,0,\       rem   O fld #22
	  10,15,61,0,0,\       rem   O fld #23
	  25,12,19,0,0,\       rem   O fld #24
	  1,1,8,0,4
	  rem	O fld #25
crt.data$(15)="THE CURRENT EXTENSION INTERVAL"
crt.data$(16)="ENTER CHECK DATE (        ) [        ]"
crt.data$(17)="APPLY WHICH INTERVAL BASE (M=MONTH;W=WEEK) [ ]"
crt.data$(18)="EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
crt.data$(19)="IF ALL EXTENSION PARAMETERS ARE CORRECT, TYPE ""YES""   [   ]"
crt.data$(20)="NO CURRENT PAY TRANSACTION (HRS) FILE FOUND"
crt.data$(21)="THE CURRENT HRS BATCH FILE HAS NOT BEEN PROOFED"
crt.data$(22)="THE CURRENT COH FILE CANNOT BE FOUND"
crt.data$(23)="IF YOU WISH TO CONTINUE THE APPLICATION, TYPE ""YES""   [   ]"
crt.data$(24)="CURRENT CHECK DATE:"

i%=1
while i%<=25
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(12)=len(sys.name$)
crt.x%(12)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(12)=sys.name$
crt.data$(13)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(14)=len(fun.name$)
crt.x%(14)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(14)=fun.name$
if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(25)=len(co.name$)
crt.x%(25)=fn.center%(co.name$,crt.columns%-2)
crt.data$(25)=co.name$

rem---------------------------------------------------------
