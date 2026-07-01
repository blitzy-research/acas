rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYUCOLI - 6-DEC-79|11AM

crt.field.count% = 37	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  17,7,7,2,28,\       rem   IO fld #1
	  37,7,7,2,28,\       rem   IO fld #2
	  56,7,7,2,28,\       rem   IO fld #3
	  17,9,7,2,28,\       rem   IO fld #4
	  37,9,7,2,28,\       rem   IO fld #5
	  56,9,7,2,28,\       rem   IO fld #6
	  37,13,7,2,28,\       rem   IO fld #7
	  56,13,7,2,28,\       rem   IO fld #8
	  37,14,7,2,28,\       rem   IO fld #9
	  56,14,7,2,28,\       rem   IO fld #10
	  37,15,7,2,28,\       rem   IO fld #11
	  56,15,7,2,28,\       rem   IO fld #12
	  37,19,7,2,28,\       rem   IO fld #13
	  56,19,7,2,28,\       rem   IO fld #14
	  37,20,7,2,28,\       rem   IO fld #15
	  56,20,7,2,28,\       rem   IO fld #16
	  37,21,7,2,28,\       rem   IO fld #17
	  56,21,7,2,28,\       rem   IO fld #18
	  1,1,8,0,4,\	    rem   O fld #19
	  1,2,9,0,4,\	    rem   O fld #20
	  1,3,8,0,4,\	    rem   O fld #21
	  10,3,8,0,4,\	     rem   O fld #22
	  20,5,45,0,4,\       rem   O fld #23
	  33,6,15,0,4,\       rem   O fld #24
	  11,7,58,0,4,\       rem   O fld #25
	  35,8,12,0,4,\       rem   O fld #26
	  11,9,58,0,4,\       rem   O fld #27
	  26,11,28,0,4,\       rem   O fld #28
	  41,12,24,0,4,\       rem   O fld #29
	  16,13,53,0,4,\       rem   O fld #30
	  16,14,53,0,4,\       rem   O fld #31
	  16,15,53,0,4,\       rem   O fld #32
	  21,17,43,0,4,\       rem   O fld #33
	  41,18,24,0,4,\       rem   O fld #34
	  16,19,53,0,4,\       rem   O fld #35
	  16,20,53,0,4,\       rem   O fld #36
	  16,21,53,0,4
	  rem	O fld #37
crt.data$(23)="COMPANY LIABILITIES(NOT TOTALED FROM HISTORY)"
crt.data$(24)="QUARTER TO DATE"
crt.data$(25)="FICA:[            ] FUTA:[            ] SUI:[            ]"
crt.data$(26)="YEAR TO DATE"
crt.data$(27)="FICA:[            ] FUTA:[            ] SUI:[            ]"
crt.data$(28)="QUARTER TO DATE(NOT TOTALED)"
crt.data$(29)="EARNED             TAKEN"
crt.data$(30)="VACATION TIME:      [            ]     [            ]"
crt.data$(31)="SICK LEAVE:         [            ]     [            ]"
crt.data$(32)="COMP TIME:          [            ]     [            ]"
crt.data$(33)="YEAR TO DATE(TOTALED FROM EMPLOYEE RECORDS)"
crt.data$(34)="EARNED             TAKEN"
crt.data$(35)="VACATION TIME:      [            ]     [            ]"
crt.data$(36)="SICK LEAVE:         [            ]     [            ]"
crt.data$(37)="COMP TIME:          [            ]     [            ]"

i%=1
while i%<=37
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(19)=len(co.name$)
crt.x%(19)=fn.center%(co.name$,crt.columns%-2)
crt.data$(19)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(20)=len(sys.name$)
crt.x%(20)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(20)=sys.name$
crt.data$(21)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(22)=len(fun.name$)
crt.x%(22)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(22)=fun.name$

rem---------------------------------------------------------
