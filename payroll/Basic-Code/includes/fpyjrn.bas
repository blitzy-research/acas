rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYJRN - 11/19/79

crt.field.count% = 12	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  51,15,5,0,17,\       rem   IO fld #1
	  56,18,1,0,17,\       rem   IO fld #2
	  25,20,31,0,17,\	rem   IO fld #3
	  1,1,8,0,4,\	    rem   O fld #4
	  1,2,9,0,4,\	    rem   O fld #5
	  1,3,8,0,4,\	    rem   O fld #6
	  10,3,8,0,4,\	     rem   O fld #7
	  25,15,25,0,0,\       rem   O fld #8
	  24,15,32,0,0,\       rem   O fld #9
	  28,15,24,0,0,\       rem   O fld #10
	  29,17,22,0,0,\       rem   O fld #11
	  29,18,23,0,0
	  rem	O fld #12
crt.data$(8)="PRINTING EMPLOYEE NUMBER:"
crt.data$(9)="PRINTING COMPANY PAYROLL SUMMARY"
crt.data$(10)="PRINTING ACCOUNT SUMMARY"
crt.data$(11)="HIT RETURN TO CONTINUE"
crt.data$(12)="HIT ESC TO END PRINTOUT"

i%=1
while i%<=12
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(4)=len(co.name$)
crt.x%(4)=fn.center%(co.name$,crt.columns%-2)
crt.data$(4)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(5)=len(sys.name$)
crt.x%(5)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(5)=sys.name$
crt.data$(6)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(7)=len(fun.name$)
crt.x%(7)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(7)=fun.name$

rem---------------------------------------------------------
