rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYSRT - 11-DEC-79|3PM

crt.field.count% = 5	   rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  1,1,8,0,4,\	    rem   O fld #1
	  1,2,9,0,4,\	    rem   O fld #2
	  1,3,8,0,4,\	    rem   O fld #3
	  10,3,8,0,4,\	     rem   O fld #4
	  23,6,38,0,4
	  rem	O fld #5
crt.data$(5)="SETTING UP TRANSACTION SORT PARAMETERS"

i%=1
while i%<=5
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(1)=len(co.name$)
crt.x%(1)=fn.center%(co.name$,crt.columns%-2)
crt.data$(1)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(2)=len(sys.name$)
crt.x%(2)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(2)=sys.name$
crt.data$(3)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(4)=len(fun.name$)
crt.x%(4)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(4)=fun.name$

rem---------------------------------------------------------
