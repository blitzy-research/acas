rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYPAR1 - 11/19/79

crt.field.count% = 44	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  22,7,1,0,29,\       rem   IO fld #1
	  62,7,8,0,29,\       rem   IO fld #2
	  22,8,1,0,29,\       rem   IO fld #3
	  62,8,8,0,29,\       rem   IO fld #4
	  22,9,1,0,29,\       rem   IO fld #5
	  62,9,8,0,29,\       rem   IO fld #6
	  22,10,1,0,29,\       rem   IO fld #7
	  62,10,8,0,29,\       rem   IO fld #8
	  30,14,5,2,28,\       rem   IO fld #9
	  30,15,5,2,28,\       rem   IO fld #10
	  5,16,15,0,29,\       rem   IO fld #11
	  30,16,5,2,28,\       rem   IO fld #12
	  5,17,15,0,29,\       rem   IO fld #13
	  30,17,5,2,28,\       rem   IO fld #14
	  5,18,15,0,29,\       rem   IO fld #15
	  30,18,5,2,28,\       rem   IO fld #16
	  5,19,15,0,29,\       rem   IO fld #17
	  38,19,1,0,29,\       rem   IO fld #18
	  45,21,1,0,29,\       rem   IO fld #19
	  45,22,1,0,29,\       rem   IO fld #20
	  65,21,5,2,28,\       rem   IO fld #21
	  65,22,5,2,28,\       rem   IO fld #22
	  1,1,8,0,4,\	    rem   O fld #23
	  1,2,9,0,4,\	    rem   O fld #24
	  1,3,8,0,4,\	    rem   O fld #25
	  10,3,8,0,4,\	     rem   O fld #26
	  6,5,67,0,4,\	     rem   O fld #27
	  6,6,67,0,4,\	     rem   O fld #28
	  6,7,67,0,4,\	     rem   O fld #29
	  6,8,67,0,4,\	     rem   O fld #30
	  6,9,67,0,4,\	     rem   O fld #31
	  6,10,67,0,4,\       rem   O fld #32
	  6,11,67,0,4,\       rem   O fld #33
	  15,12,45,0,4,\       rem   O fld #34
	  4,13,66,0,4,\       rem   O fld #35
	  5,14,65,0,4,\       rem   O fld #36
	  5,15,65,0,4,\       rem   O fld #37
	  2,16,57,0,4,\       rem   O fld #38
	  2,17,73,0,4,\       rem   O fld #39
	  2,18,73,0,4,\       rem   O fld #40
	  2,19,74,0,4,\       rem   O fld #41
	  2,20,74,0,4,\       rem   O fld #42
	  3,21,72,0,4,\       rem   O fld #43
	  3,22,72,0,4
	  rem	O fld #44
crt.data$(27)="-------------------------------------------------------------------"
crt.data$(28)="|               P A Y   I N T E R V A L   U S A G E               |"
crt.data$(29)="| SEMI-MONTHLY [ ] END OF LAST SEMI-MONTHLY PAY PERIOD [        ] |"
crt.data$(30)="| MONTHLY      [ ] END OF LAST MONTHLY PAY PERIOD      [        ] |"
crt.data$(31)="| BIWEEKLY     [ ] END OF LAST BIWEEKLY PAY PERIOD     [        ] |"
crt.data$(32)="| WEEKLY       [ ] END OF LAST WEEKLY PAY PERIOD       [        ] |"
crt.data$(33)="-------------------------------------------------------------------"
crt.data$(34)="D E F A U L T   E M P L O Y E E   V A L U E S"
crt.data$(35)="-- RATE NAME  -----------  DEFAULT  ------  DESCRIPTION  ---------"
crt.data$(36)="VACATION         RATE   [         ] (UNITS EARNED PER PAY PERIOD)"
crt.data$(37)="SICK LEAVE       RATE   [         ] (UNITS EARNED PER PAY PERIOD)"
crt.data$(38)="1 [               ] RATE   [         ] (DOLLARS PER UNIT)"
crt.data$(39)="2 [               ] FACTOR [         ] (RATE 1 * FACTOR = DEFAULT RATE 2)"
crt.data$(40)="3 [               ] FACTOR [         ] (RATE 1 * FACTOR = DEFAULT RATE 3)"
crt.data$(41)="4 [               ] EXCLUSION TYPE [ ] (RATE 4 CAN BE EXEMPTED FROM TAXES)"
crt.data$(42)="--------------------------------------------------------------------------"
crt.data$(43)="DEFAULT PAY INTERVAL (ANY USED INTERVAL) [ ]  MAX PAY FACTOR [         ]"
crt.data$(44)="DEFAULT PAY TYPE (H=HOURLY, S=SALARIED)  [ ]  NORMAL UNITS   [         ]"

i%=1
while i%<=44
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(23)=len(co.name$)
crt.x%(23)=fn.center%(co.name$,crt.columns%-2)
crt.data$(23)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(24)=len(sys.name$)
crt.x%(24)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(24)=sys.name$
crt.data$(25)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(26)=len(fun.name$)
crt.x%(26)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(26)=fun.name$

rem---------------------------------------------------------
