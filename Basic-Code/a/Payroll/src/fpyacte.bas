rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYACTE - 3-JAN-80|11AM

crt.field.count% = 15	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  21,5,3,0,29,\       rem   IO fld #1
	  28,7,6,0,29,\       rem   IO fld #2
	  28,8,30,0,29,\       rem   IO fld #3
	  51,11,1,0,25,\       rem   IO fld #4
	  35,13,1,0,25,\       rem   IO fld #5
	  1,1,8,0,4,\	    rem   O fld #6
	  1,2,9,0,4,\	    rem   O fld #7
	  1,3,8,0,4,\	    rem   O fld #8
	  10,3,8,0,4,\	     rem   O fld #9
	  9,5,16,0,0,\	     rem   O fld #10
	  12,7,23,0,0,\       rem   O fld #11
	  12,8,47,0,0,\       rem   O fld #12
	  9,11,41,0,0,\       rem   O fld #13
	  9,11,43,0,0,\       rem   O fld #14
	  9,13,25,0,0
	  rem	O fld #15
crt.data$(10)="RECORD NO. [   ]"
crt.data$(11)="ACCOUNT NUMBER:[      ]"
crt.data$(12)="ACCOUNT NAME:  [                              ]"
crt.data$(13)="PLACE GL CHART OF ACCOUNTS FILE IN DRIVE:"
crt.data$(14)="REPLACE DISKETTES IN ORIGINAL CONFIGURATION"
crt.data$(15)="PRESS RETURN TO CONTINUE:"

i%=1
while i%<=15
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(6)=len(co.name$)
crt.x%(6)=fn.center%(co.name$,crt.columns%-2)
crt.data$(6)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(7)=len(sys.name$)
crt.x%(7)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(7)=sys.name$
crt.data$(8)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(9)=len(fun.name$)
crt.x%(9)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(9)=fun.name$

rem---------------------------------------------------------
