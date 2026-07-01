rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYEMPP - 13-DEC-79|NOON

crt.field.count% = 27	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  49,13,2,0,29,\       rem   IO fld #1
	  31,15,5,0,25,\       rem   IO fld #2
	  42,15,5,0,25,\       rem   IO fld #3
	  61,16,1,0,25,\       rem   IO fld #4
	  51,18,5,0,25,\       rem   IO fld #5
	  1,1,8,0,4,\	    rem   O fld #6
	  1,2,9,0,4,\	    rem   O fld #7
	  1,3,8,0,4,\	    rem   O fld #8
	  10,3,8,0,4,\	     rem   O fld #9
	  8,5,16,0,4,\	     rem   O fld #10
	  8,6,23,0,4,\	     rem   O fld #11
	  8,7,26,0,4,\	     rem   O fld #12
	  8,8,29,0,4,\	     rem   O fld #13
	  8,9,24,0,4,\	     rem   O fld #14
	  8,10,27,0,4,\       rem   O fld #15
	  8,11,28,0,4,\       rem   O fld #16
	  44,5,23,0,4,\       rem   O fld #17
	  44,6,25,0,4,\       rem   O fld #18
	  43,7,24,0,4,\       rem   O fld #19
	  43,8,26,0,4,\       rem   O fld #20
	  43,9,28,0,4,\       rem   O fld #21
	  43,10,25,0,4,\       rem   O fld #22
	  43,11,24,0,4,\       rem   O fld #23
	  19,13,33,0,4,\       rem   O fld #24
	  19,15,29,0,0,\       rem   O fld #25
	  19,16,44,0,0,\       rem   O fld #26
	  19,18,31,0,0
	  rem	O fld #27
crt.data$(10)="1. ALL EMPLOYEES"
crt.data$(11)="2. ALL WEEKLY EMPLOYEES"
crt.data$(12)="3. ALL BI-WEEKLY EMPLOYEES"
crt.data$(13)="4. ALL SEMI-MONTHLY EMPLOYEES"
crt.data$(14)="5. ALL MONTHLY EMPLOYEES"
crt.data$(15)="6. ALL WEEK BASED EMPLOYEES"
crt.data$(16)="7. ALL MONTH BASED EMPLOYEES"
crt.data$(17)="8. ALL HOURLY EMPLOYEES"
crt.data$(18)="9. ALL SALARIED EMPLOYEES"
crt.data$(19)="10. ALL ACTIVE EMPLOYEES"
crt.data$(20)="11. ALL ON-LEAVE EMPLOYEES"
crt.data$(21)="12. ALL TERMINATED EMPLOYEES"
crt.data$(22)="13. ALL DELETED EMPLOYEES"
crt.data$(23)="14. A RANGE OF EMPLOYEES"
crt.data$(24)="ENTER YOUR SELECTION NUMBER: [  ]"
crt.data$(25)="RANGE FROM [     ] TO [     ]"
crt.data$(26)="FULL INFORMATION OR SINGLE LINE (F OR S) [ ]"
crt.data$(27)="NOW PROCESSING EMPLOYEE NUMBER:"

i%=1
while i%<=27
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
