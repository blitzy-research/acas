rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYW2 - 4/DEC/79

crt.field.count% = 40	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  10,8,1,0,29,\       rem   IO fld #1
	  10,9,1,0,29,\       rem   IO fld #2
	  10,10,1,0,29,\       rem   IO fld #3
	  10,11,1,0,29,\       rem   IO fld #4
	  28,13,1,0,28,\       rem   IO fld #5
	  74,8,1,0,29,\       rem   IO fld #6
	  74,10,2,0,28,\       rem   IO fld #7
	  74,12,2,0,28,\       rem   IO fld #8
	  74,14,2,0,28,\       rem   IO fld #9
	  65,17,1,0,29,\       rem   IO fld #10
	  31,16,5,0,25,\       rem   IO fld #11
	  31,18,5,0,25,\       rem   IO fld #12
	  28,17,5,0,25,\       rem   IO fld #13
	  48,21,5,0,25,\       rem   IO fld #14
	  1,1,8,0,4,\	    rem   O fld #15
	  1,2,9,0,4,\	    rem   O fld #16
	  1,3,8,0,4,\	    rem   O fld #17
	  10,3,8,0,4,\	     rem   O fld #18
	  3,6,75,0,4,\	     rem   O fld #19
	  39,7,1,0,4,\	     rem   O fld #20
	  8,8,16,0,4,\	     rem   O fld #21
	  39,8,37,0,4,\       rem   O fld #22
	  8,9,21,0,4,\	     rem   O fld #23
	  39,9,1,0,4,\	     rem   O fld #24
	  8,10,23,0,4,\       rem   O fld #25
	  39,10,38,0,4,\       rem   O fld #26
	  8,11,20,0,4,\       rem   O fld #27
	  39,11,1,0,4,\       rem   O fld #28
	  39,12,38,0,4,\       rem   O fld #29
	  11,13,29,0,4,\       rem   O fld #30
	  39,14,38,0,4,\       rem   O fld #31
	  3,15,75,0,4,\       rem   O fld #32
	  39,16,1,0,4,\       rem   O fld #33
	  39,17,28,0,4,\       rem   O fld #34
	  39,18,1,0,4,\       rem   O fld #35
	  3,19,75,0,4,\       rem   O fld #36
	  5,16,32,0,0,\       rem   O fld #37
	  5,18,32,0,0,\       rem   O fld #38
	  9,17,25,0,0,\       rem   O fld #39
	  19,21,28,0,0
	  rem	O fld #40
crt.data$(19)="---------------------------------------------------------------------------"
crt.data$(20)="|"
crt.data$(21)="1  ALL EMPLOYEES"
crt.data$(22)="|  PRINT STATE AND LOCAL AMOUNTS  [ ]"
crt.data$(23)="2  RANGE OF EMPLOYEES"
crt.data$(24)="|"
crt.data$(25)="3  TERMINATED EMPLOYEES"
crt.data$(26)="|  NUMBER OF FORMS PER EMPLOYEE   [  ]"
crt.data$(27)="4  A SINGLE EMPLOYEE"
crt.data$(28)="|"
crt.data$(29)="|  NUMBER OF LINES BETWEEN FORMS  [  ]"
crt.data$(30)="ENTER SELECTION [ ]         |"
crt.data$(31)="|  STARTING PRINT COLUMN          [  ]"
crt.data$(32)="------------------------------------|--------------------------------------"
crt.data$(33)="|"
crt.data$(34)="|        PRINT TEST FORM [ ]"
crt.data$(35)="|"
crt.data$(36)="---------------------------------------------------------------------------"
crt.data$(37)="STARTING EMPLOYEE NUMBER [     ]"
crt.data$(38)="ENDING EMPLOYEE NUMBER   [     ]"
crt.data$(39)="EMPLOYEE NUMBER   [     ]"
crt.data$(40)="NOW PRINTING EMPLOYEE NUMBER"

i%=1
while i%<=40
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(15)=len(co.name$)
crt.x%(15)=fn.center%(co.name$,crt.columns%-2)
crt.data$(15)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(16)=len(sys.name$)
crt.x%(16)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(16)=sys.name$
crt.data$(17)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(18)=len(fun.name$)
crt.x%(18)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(18)=fun.name$

rem---------------------------------------------------------
