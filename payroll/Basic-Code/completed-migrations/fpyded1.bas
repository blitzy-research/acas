rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYDED1 - 20-NOV-79|12:50PM

crt.field.count% = 50	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  26,8,1,0,29,\       rem   IO fld #1
	  32,8,3,0,28,\       rem   IO fld #2
	  26,9,1,0,29,\       rem   IO fld #3
	  32,9,3,0,28,\       rem   IO fld #4
	  26,10,1,0,29,\       rem   IO fld #5
	  32,10,3,0,28,\       rem   IO fld #6
	  26,11,1,0,29,\       rem   IO fld #7
	  32,11,3,0,28,\       rem   IO fld #8
	  40,11,2,2,28,\       rem   IO fld #9
	  48,11,5,2,30,\       rem   IO fld #10
	  26,12,1,0,29,\       rem   IO fld #11
	  32,12,3,0,28,\       rem   IO fld #12
	  40,12,2,2,28,\       rem   IO fld #13
	  48,12,5,2,30,\       rem   IO fld #14
	  26,13,1,0,29,\       rem   IO fld #15
	  32,13,3,0,28,\       rem   IO fld #16
	  40,13,2,2,28,\       rem   IO fld #17
	  48,13,5,2,30,\       rem   IO fld #18
	  26,14,1,0,29,\       rem   IO fld #19
	  32,14,3,0,28,\       rem   IO fld #20
	  40,14,2,2,28,\       rem   IO fld #21
	  48,14,5,2,30,\       rem   IO fld #22
	  40,15,2,2,28,\       rem   IO fld #23
	  26,16,1,0,29,\       rem   IO fld #24
	  32,16,3,0,28,\       rem   IO fld #25
	  40,16,2,2,28,\       rem   IO fld #26
	  48,16,5,2,30,\       rem   IO fld #27
	  26,17,1,0,29,\       rem   IO fld #28
	  32,17,3,0,28,\       rem   IO fld #29
	  40,17,2,2,28,\       rem   IO fld #30
	  48,17,5,2,30,\       rem   IO fld #31
	  40,18,2,2,28,\       rem   IO fld #32
	  48,18,5,2,30,\       rem   IO fld #33
	  1,1,8,0,4,\	    rem   O fld #34
	  1,2,9,0,4,\	    rem   O fld #35
	  1,3,8,0,4,\	    rem   O fld #36
	  10,3,8,0,4,\	     rem   O fld #37
	  31,5,4,0,4,\	     rem   O fld #38
	  24,6,30,0,4,\       rem   O fld #39
	  16,8,20,0,4,\       rem   O fld #40
	  16,9,20,0,4,\       rem   O fld #41
	  16,10,20,0,4,\       rem   O fld #42
	  16,11,44,0,4,\       rem   O fld #43
	  16,12,44,0,4,\       rem   O fld #44
	  16,13,44,0,4,\       rem   O fld #45
	  16,14,44,0,4,\       rem   O fld #46
	  16,15,30,0,4,\       rem   O fld #47
	  16,16,44,0,4,\       rem   O fld #48
	  16,17,44,0,4,\       rem   O fld #49
	  16,18,44,0,4
	  rem	O fld #50
crt.data$(38)="ACCT"
crt.data$(39)="USED    NO      RATE     LIMIT"
crt.data$(40)="FWT:     [ ]   [   ]"
crt.data$(41)="SWT:     [ ]   [   ]"
crt.data$(42)="LWT:     [ ]   [   ]"
crt.data$(43)="FICA:    [ ]   [   ]   [     ] [           ]"
crt.data$(44)="CO FICA: [ ]   [   ]   [     ] [           ]"
crt.data$(45)="SDI:     [ ]   [   ]   [     ] [           ]"
crt.data$(46)="CO FUTA: [ ]   [   ]   [     ] [           ]"
crt.data$(47)="FUTA MAX STATE CREDIT: [     ]"
crt.data$(48)="CO SUI:  [ ]   [   ]   [     ] [           ]"
crt.data$(49)="EIC:     [ ]   [   ]   [     ] [           ]"
crt.data$(50)="EIC EXCESS:            [     ] [           ]"

i%=1
while i%<=50
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(34)=len(co.name$)
crt.x%(34)=fn.center%(co.name$,crt.columns%-2)
crt.data$(34)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(35)=len(sys.name$)
crt.x%(35)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(35)=sys.name$
crt.data$(36)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(37)=len(fun.name$)
crt.x%(37)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(37)=fun.name$

rem---------------------------------------------------------
