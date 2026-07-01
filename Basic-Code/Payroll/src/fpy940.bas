rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPY940 - 31/DEC/79

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
	  11,13,39,0,21,\	rem   IO fld #1
	  51,13,5,0,21,\       rem   IO fld #2
	  1,1,8,0,4,\	    rem   O fld #3
	  1,2,9,0,4,\	    rem   O fld #4
	  1,3,8,0,4,\	    rem   O fld #5
	  10,3,8,0,4
	  rem	O fld #6

i%=1
while i%<=6
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(3)=len(co.name$)
crt.x%(3)=fn.center%(co.name$,crt.columns%-2)
crt.data$(3)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(4)=len(sys.name$)
crt.x%(4)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(4)=sys.name$
crt.data$(5)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(6)=len(fun.name$)
crt.x%(6)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(6)=fun.name$

rem---------------------------------------------------------
