rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYDED2 - 19-NOV-79|3:35PM

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
	  44,6,5,2,30,\       rem   IO fld #1
	  17,10,5,2,30,\       rem   IO fld #2
	  32,10,2,2,28,\       rem   IO fld #3
	  44,10,5,2,30,\       rem   IO fld #4
	  59,10,2,2,28,\       rem   IO fld #5
	  17,11,5,2,30,\       rem   IO fld #6
	  32,11,2,2,28,\       rem   IO fld #7
	  44,11,5,2,30,\       rem   IO fld #8
	  59,11,2,2,28,\       rem   IO fld #9
	  17,12,5,2,30,\       rem   IO fld #10
	  32,12,2,2,28,\       rem   IO fld #11
	  44,12,5,2,30,\       rem   IO fld #12
	  59,12,2,2,28,\       rem   IO fld #13
	  17,13,5,2,30,\       rem   IO fld #14
	  32,13,2,2,28,\       rem   IO fld #15
	  44,13,5,2,30,\       rem   IO fld #16
	  59,13,2,2,28,\       rem   IO fld #17
	  17,14,5,2,30,\       rem   IO fld #18
	  32,14,2,2,28,\       rem   IO fld #19
	  44,14,5,2,30,\       rem   IO fld #20
	  59,14,2,2,28,\       rem   IO fld #21
	  17,15,5,2,30,\       rem   IO fld #22
	  32,15,2,2,28,\       rem   IO fld #23
	  44,15,5,2,30,\       rem   IO fld #24
	  59,15,2,2,28,\       rem   IO fld #25
	  17,16,5,2,30,\       rem   IO fld #26
	  32,16,2,2,28,\       rem   IO fld #27
	  44,16,5,2,30,\       rem   IO fld #28
	  59,16,2,2,28,\       rem   IO fld #29
	  1,1,8,0,4,\	    rem   O fld #30
	  1,2,9,0,4,\	    rem   O fld #31
	  1,3,8,0,4,\	    rem   O fld #32
	  10,3,8,0,4,\	     rem   O fld #33
	  24,6,32,0,4,\       rem   O fld #34
	  22,8,40,0,4,\       rem   O fld #35
	  17,9,48,0,4,\       rem   O fld #36
	  12,10,53,0,4,\       rem   O fld #37
	  12,11,53,0,4,\       rem   O fld #38
	  12,12,53,0,4,\       rem   O fld #39
	  12,13,53,0,4,\       rem   O fld #40
	  12,14,53,0,4,\       rem   O fld #41
	  12,15,53,0,4,\       rem   O fld #42
	  12,16,53,0,4,\       rem   O fld #43
	  16,18,47,0,4
	  rem	O fld #44
crt.data$(34)="ALLOWANCE AMOUNT:  [           ]"
crt.data$(35)="M A R R I E D                S I N G L E"
crt.data$(36)="WAGES OVER:   PERCENT      WAGES OVER:   PERCENT"
crt.data$(37)="1.  [           ]  [     ]     [           ]  [     ]"
crt.data$(38)="2.  [           ]  [     ]     [           ]  [     ]"
crt.data$(39)="3.  [           ]  [     ]     [           ]  [     ]"
crt.data$(40)="4.  [           ]  [     ]     [           ]  [     ]"
crt.data$(41)="5.  [           ]  [     ]     [           ]  [     ]"
crt.data$(42)="6.  [           ]  [     ]     [           ]  [     ]"
crt.data$(43)="7.  [           ]  [     ]     [           ]  [     ]"
crt.data$(44)="(Use ANNUAL tables from IRS CIRCULAR 'E' only!)"

i%=1
while i%<=44
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(30)=len(co.name$)
crt.x%(30)=fn.center%(co.name$,crt.columns%-2)
crt.data$(30)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(31)=len(sys.name$)
crt.x%(31)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(31)=sys.name$
crt.data$(32)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(33)=len(fun.name$)
crt.x%(33)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(33)=fun.name$

rem---------------------------------------------------------
