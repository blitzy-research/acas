rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYUPDM - 4-DEC-79|3:30PM

crt.field.count% = 9	   rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  53,13,1,0,28,\       rem   IO fld #1
	  1,1,8,0,4,\	    rem   O fld #2
	  1,2,9,0,4,\	    rem   O fld #3
	  1,3,8,0,4,\	    rem   O fld #4
	  10,3,8,0,4,\	     rem   O fld #5
	  19,7,34,0,4,\       rem   O fld #6
	  19,8,44,0,4,\       rem   O fld #7
	  19,9,27,0,4,\       rem   O fld #8
	  28,13,27,0,4
	  rem	O fld #9
crt.data$(6)="1.  UPDATE EMPLOYEE HISTORY TOTALS"
crt.data$(7)="2.  UPDATE COMPANY LIABILITIES,VACATION ETC."
crt.data$(8)="3.  UPDATE PAYMENTS HISTORY"
crt.data$(9)="ENTER SELECTION NUMBER: [ ]"

i%=1
while i%<=9
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(2)=len(co.name$)
crt.x%(2)=fn.center%(co.name$,crt.columns%-2)
crt.data$(2)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(3)=len(sys.name$)
crt.x%(3)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(3)=sys.name$
crt.data$(4)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(5)=len(fun.name$)
crt.x%(5)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(5)=fun.name$

rem---------------------------------------------------------
