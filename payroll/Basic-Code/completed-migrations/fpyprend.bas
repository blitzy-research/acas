rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYPREND - 12/02/79

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
	  50,10,4,0,25,\       rem   IO fld #1
	  39,10,6,0,25,\       rem   IO fld #2
	  57,10,4,0,25,\       rem   IO fld #3
	  73,12,4,0,17,\       rem   IO fld #4
	  69,12,4,0,17,\       rem   IO fld #5
	  72,12,4,0,17,\       rem   IO fld #6
	  74,12,4,0,17,\       rem   IO fld #7
	  56,14,5,0,17,\       rem   IO fld #8
	  54,16,3,0,25,\       rem   IO fld #9
	  31,18,32,0,17,\	rem   IO fld #10
	  1,1,8,0,4,\	    rem   O fld #11
	  1,2,9,0,4,\	    rem   O fld #12
	  1,3,8,0,4,\	    rem   O fld #13
	  10,3,8,0,4,\	     rem   O fld #14
	  30,10,19,0,0,\       rem   O fld #15
	  24,10,32,0,0,\       rem   O fld #16
	  7,12,65,0,0,\       rem   O fld #17
	  11,12,57,0,0,\       rem   O fld #18
	  7,12,64,0,0,\       rem   O fld #19
	  5,12,68,0,0,\       rem   O fld #20
	  21,14,42,0,0,\       rem   O fld #21
	  24,14,31,0,0,\       rem   O fld #22
	  23,15,38,0,0,\       rem   O fld #23
	  28,16,32,0,0,\       rem   O fld #24
	  24,18,36,0,0
	  rem	O fld #25
crt.data$(15)="ENDING FOR THE YEAR"
crt.data$(16)="ENDING FOR THE        QUARTER OF"
crt.data$(17)="THE NEXT CHECK DATE MUST BE WITHIN JANUARY, FEBRUARY, OR MARCH OF"
crt.data$(18)="THE NEXT CHECK DATE MUST BE WITHIN APRIL, MAY, OR JUNE OF"
crt.data$(19)="THE NEXT CHECK DATE MUST BE WITHIN JULY, AUGUST, OR SEPTEMBER OF"
crt.data$(20)="THE NEXT CHECK DATE MUST BE WITHIN OCTOBER, NOVEMBER, OR DECEMBER OF"
crt.data$(21)="EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
crt.data$(22)="NOW PROCESSING EMPLOYEE NUMBER:"
crt.data$(23)="IF ALL PERIOD ENDING INFORMATION SHOWN"
crt.data$(24)="IS CORRECT, TYPE ""YES""   [   ]"
crt.data$(25)="TERMINATED EMPLOYEE IS BEING DELETED"

i%=1
while i%<=25
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(11)=len(co.name$)
crt.x%(11)=fn.center%(co.name$,crt.columns%-2)
crt.data$(11)=co.name$
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

rem---------------------------------------------------------
