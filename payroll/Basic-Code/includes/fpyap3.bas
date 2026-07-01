rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYAP3 - 11/20/79

crt.field.count% = 7	   rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  1,3,8,0,0,\	    rem   O fld #1
	  20,13,27,0,0,\       rem   O fld #2
	  48,13,10,0,0,\       rem   O fld #3
	  22,15,27,0,0,\       rem   O fld #4
	  50,15,5,0,0,\       rem   O fld #5
	  18,15,42,0,0,\       rem   O fld #6
	  26,20,30,0,0
	  rem	O fld #7
crt.data$(2)="CURRENT EMPLOYEE STATUS IS:"
crt.data$(3)="XXXXXXXXXX"
crt.data$(4)="PROCESSING EMPLOYEE NUMBER:"
crt.data$(5)="XXXXX"
crt.data$(6)="EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
crt.data$(7)="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

i%=1
while i%<=7
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(1)=len(fun.name$)
crt.x%(1)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(1)=fun.name$

rem---------------------------------------------------------
