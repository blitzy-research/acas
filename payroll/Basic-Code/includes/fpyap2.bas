rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYAP2 - 11/13/79

crt.field.count% = 6	   rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  48,13,10,0,17,\	rem   IO fld #1
	  50,15,5,0,17,\       rem   IO fld #2
	  1,3,8,0,0,\	    rem   O fld #3
	  20,13,27,0,0,\       rem   O fld #4
	  22,15,27,0,0,\       rem   O fld #5
	  18,15,42,0,0
	  rem	O fld #6
crt.data$(4)="CURRENT EMPLOYEE STATUS IS:"
crt.data$(5)="PROCESSING EMPLOYEE NUMBER:"
crt.data$(6)="EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"

i%=1
while i%<=6
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(3)=len(fun.name$)
crt.x%(3)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(3)=fun.name$

rem---------------------------------------------------------
