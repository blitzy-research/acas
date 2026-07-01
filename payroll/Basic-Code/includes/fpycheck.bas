rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYCHECK - 12/8/79

crt.field.count% = 21	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  62,7,1,0,25,\       rem   IO fld #1
	  58,9,5,0,25,\       rem   IO fld #2
	  58,11,5,0,25,\       rem   IO fld #3
	  58,13,5,0,25,\       rem   IO fld #4
	  58,14,5,0,25,\       rem   IO fld #5
	  57,17,1,0,25,\       rem   IO fld #6
	  1,1,8,0,4,\	    rem   O fld #7
	  1,2,9,0,4,\	    rem   O fld #8
	  1,3,8,0,4,\	    rem   O fld #9
	  10,3,8,0,4,\	     rem   O fld #10
	  16,6,49,0,0,\       rem   O fld #11
	  16,7,50,0,0,\       rem   O fld #12
	  16,9,39,0,0,\       rem   O fld #13
	  16,11,48,0,0,\       rem   O fld #14
	  16,13,37,0,0,\       rem   O fld #15
	  16,14,39,0,0,\       rem   O fld #16
	  21,16,28,0,0,\       rem   O fld #17
	  21,17,38,0,0,\       rem   O fld #18
	  16,19,45,0,0,\       rem   O fld #19
	  26,20,26,0,0,\       rem   O fld #20
	  24,22,28,0,0
	  rem	O fld #21
crt.data$(11)="TYPE ""Y"" OR PRESS  RETURN  TO PRINT A TEST FORM"
crt.data$(12)="TYPE ""N"" WHEN THE FORMS ARE PROPERLY ALIGNED [ ]"
crt.data$(13)="THE LAST CHECK PRINTED WAS CHECK NUMBER"
crt.data$(14)="THE STARTING CHECK NUMBER WILL BE        [     ]"
crt.data$(15)="THE COMPUTER IS PRINTING CHECK NUMBER"
crt.data$(16)="THE CHECK IS PAYABLE TO EMPLOYEE NUMBER"
crt.data$(17)="PRESS THE ESCAPE KEY TO STOP"
crt.data$(18)="PRESS THE RETURN KEY TO CONTINUE   [ ]"
crt.data$(19)="THE CHECK AMOUNT EXCEEDS THE MAXIMUM ALLOWED."
crt.data$(20)="THIS CHECK WILL BE VOIDED."
crt.data$(21)="ALL CHECKS HAVE BEEN PRINTED"

i%=1
while i%<=21
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(7)=len(co.name$)
crt.x%(7)=fn.center%(co.name$,crt.columns%-2)
crt.data$(7)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(8)=len(sys.name$)
crt.x%(8)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(8)=sys.name$
crt.data$(9)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(10)=len(fun.name$)
crt.x%(10)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(10)=fun.name$

rem---------------------------------------------------------
