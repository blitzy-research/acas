rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYHRSEN - 7/DEC/79

crt.field.count% = 23	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  74,3,3,0,28,\       rem   IO fld #1
	  27,9,3,0,28,\       rem   IO fld #2
	  32,11,5,0,29,\       rem   IO fld #3
	  40,11,30,0,29,\	rem   IO fld #4
	  32,12,2,0,29,\       rem   IO fld #5
	  40,12,15,0,29,\	rem   IO fld #6
	  32,13,7,2,28,\       rem   IO fld #7
	  32,14,8,0,29,\       rem   IO fld #8
	  52,18,1,0,29,\       rem   IO fld #9
	  1,1,8,0,4,\	    rem   O fld #10
	  1,2,9,0,4,\	    rem   O fld #11
	  1,3,8,0,4,\	    rem   O fld #12
	  10,3,8,0,4,\	     rem   O fld #13
	  67,3,6,0,4,\	     rem   O fld #14
	  12,9,59,0,4,\       rem   O fld #15
	  14,10,57,0,4,\       rem   O fld #16
	  14,11,57,0,4,\       rem   O fld #17
	  14,12,57,0,4,\       rem   O fld #18
	  14,13,57,0,4,\       rem   O fld #19
	  14,14,57,0,4,\       rem   O fld #20
	  14,15,57,0,4,\       rem   O fld #21
	  14,16,57,0,4,\       rem   O fld #22
	  28,18,26,0,4
	  rem	O fld #23
crt.data$(14)="BATCH:"
crt.data$(15)="RECORD NUMBER [    ]--------------------------------------|"
crt.data$(16)="|                                                       |"
crt.data$(17)="|  EMPLOYEE NO.  [     ]                                |"
crt.data$(18)="|  RATE          [  ]                                   |"
crt.data$(19)="|  UNITS         [            ]                         |"
crt.data$(20)="|  DATE          [        ]                             |"
crt.data$(21)="|                                                       |"
crt.data$(22)="|-------------------------------------------------------|"
crt.data$(23)="DISPLAY EMPLOYEE NAMES [ ]"

i%=1
while i%<=23
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(10)=len(co.name$)
crt.x%(10)=fn.center%(co.name$,crt.columns%-2)
crt.data$(10)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(11)=len(sys.name$)
crt.x%(11)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(11)=sys.name$
crt.data$(12)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(13)=len(fun.name$)
crt.x%(13)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(13)=fun.name$

rem---------------------------------------------------------
