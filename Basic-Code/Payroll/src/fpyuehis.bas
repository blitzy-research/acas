rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYUEHIS - 12-DEC-79|1PM

crt.field.count% = 75	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  14,4,5,0,29,\       rem   IO fld #1
	  9,6,6,2,28,\	     rem   IO fld #2
	  29,6,6,2,28,\       rem   IO fld #3
	  51,6,6,2,28,\       rem   IO fld #4
	  69,6,6,2,28,\       rem   IO fld #5
	  29,7,6,2,28,\       rem   IO fld #6
	  51,7,6,2,28,\       rem   IO fld #7
	  69,7,6,2,28,\       rem   IO fld #8
	  29,8,6,2,28,\       rem   IO fld #9
	  51,8,6,2,28,\       rem   IO fld #10
	  69,8,6,2,28,\       rem   IO fld #11
	  29,9,6,2,28,\       rem   IO fld #12
	  51,9,6,2,28,\       rem   IO fld #13
	  9,11,6,2,28,\       rem   IO fld #14
	  24,11,6,2,28,\       rem   IO fld #15
	  39,11,6,2,28,\       rem   IO fld #16
	  54,11,6,2,28,\       rem   IO fld #17
	  69,11,6,2,28,\       rem   IO fld #18
	  9,12,6,2,28,\       rem   IO fld #19
	  24,12,6,2,28,\       rem   IO fld #20
	  39,12,6,2,28,\       rem   IO fld #21
	  69,12,6,2,28,\       rem   IO fld #22
	  24,13,6,2,28,\       rem   IO fld #23
	  39,13,6,2,28,\       rem   IO fld #24
	  54,13,6,2,28,\       rem   IO fld #25
	  69,13,6,2,28,\       rem   IO fld #26
	  9,15,6,2,28,\       rem   IO fld #27
	  29,15,6,2,28,\       rem   IO fld #28
	  51,15,6,2,28,\       rem   IO fld #29
	  69,15,6,2,28,\       rem   IO fld #30
	  29,16,6,2,28,\       rem   IO fld #31
	  51,16,6,2,28,\       rem   IO fld #32
	  69,16,6,2,28,\       rem   IO fld #33
	  29,17,6,2,28,\       rem   IO fld #34
	  51,17,6,2,28,\       rem   IO fld #35
	  69,17,6,2,28,\       rem   IO fld #36
	  29,18,6,2,28,\       rem   IO fld #37
	  51,18,6,2,28,\       rem   IO fld #38
	  9,20,6,2,28,\       rem   IO fld #39
	  24,20,6,2,28,\       rem   IO fld #40
	  39,20,6,2,28,\       rem   IO fld #41
	  54,20,6,2,28,\       rem   IO fld #42
	  69,20,6,2,28,\       rem   IO fld #43
	  9,21,6,2,28,\       rem   IO fld #44
	  24,21,6,2,28,\       rem   IO fld #45
	  39,21,6,2,28,\       rem   IO fld #46
	  69,21,6,2,28,\       rem   IO fld #47
	  24,22,6,2,28,\       rem   IO fld #48
	  39,22,6,2,28,\       rem   IO fld #49
	  54,22,6,2,28,\       rem   IO fld #50
	  69,22,6,2,28,\       rem   IO fld #51
	  50,4,30,0,25,\       rem   IO fld #52
	  1,1,8,0,4,\	    rem   O fld #53
	  1,2,9,0,4,\	    rem   O fld #54
	  1,3,8,0,4,\	    rem   O fld #55
	  10,3,8,0,4,\	     rem   O fld #56
	  6,4,14,0,4,\	     rem   O fld #57
	  26,5,30,0,4,\       rem   O fld #58
	  1,6,79,0,4,\	     rem   O fld #59
	  17,7,63,0,4,\       rem   O fld #60
	  1,8,79,0,4,\	     rem   O fld #61
	  23,9,39,0,4,\       rem   O fld #62
	  29,10,27,0,4,\       rem   O fld #63
	  1,11,79,0,4,\       rem   O fld #64
	  1,12,79,0,4,\       rem   O fld #65
	  1,13,79,0,4,\       rem   O fld #66
	  26,14,30,0,4,\       rem   O fld #67
	  1,15,79,0,4,\       rem   O fld #68
	  17,16,63,0,4,\       rem   O fld #69
	  1,17,79,0,4,\       rem   O fld #70
	  23,18,39,0,4,\       rem   O fld #71
	  29,19,27,0,4,\       rem   O fld #72
	  1,20,79,0,4,\       rem   O fld #73
	  1,21,79,0,4,\       rem   O fld #74
	  1,22,79,0,4
	  rem	O fld #75
crt.data$(57)="EMP NO:[     ]"
crt.data$(58)="QTD EARNINGS BY TAX CATEGORIES"
crt.data$(59)="INCOME:[          ]  OTHER:[          ] NO TAXES:[          ] FICA:[          ]"
crt.data$(60)="EIC CREDIT:[          ]     TIPS:[          ]  NET:[          ]"
crt.data$(61)="QTD TAXES WITHHELD:    FWT:[          ]      SWT:[          ]  LWT:[          ]"
crt.data$(62)="FICA:[          ]      SDI:[          ]"
crt.data$(63)="QTD EARNINGS AND DEDUCTIONS"
crt.data$(64)="SYS: 1:[          ] 2:[          ] 3:[          ] 4:[          ] 5:[          ]"
crt.data$(65)="EMP: 1:[          ] 2:[          ] 3:[          ] OTHER DEDUCTIONS:[          ]"
crt.data$(66)="UNITS BY PAY TYPE:  1:[          ] 2:[          ] 3:[          ] 4:[          ]"
crt.data$(67)="YTD EARNINGS BY TAX CATEGORIES"
crt.data$(68)="INCOME:[          ]  OTHER:[          ] NO TAXES:[          ] FICA:[          ]"
crt.data$(69)="EIC CREDIT:[          ]     TIPS:[          ]  NET:[          ]"
crt.data$(70)="YTD TAXES WITHHELD:    FWT:[          ]      SWT:[          ]  LWT:[          ]"
crt.data$(71)="FICA:[          ]      SDI:[          ]"
crt.data$(72)="YTD EARNINGS AND DEDUCTIONS"
crt.data$(73)="SYS: 1:[          ] 2:[          ] 3:[          ] 4:[          ] 5:[          ]"
crt.data$(74)="EMP: 1:[          ] 2:[          ] 3:[          ] OTHER DEDUCTIONS:[          ]"
crt.data$(75)="UNITS BY PAY TYPE:  1:[          ] 2:[          ] 3:[          ] 4:[          ]"

i%=1
while i%<=75
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(53)=len(co.name$)
crt.x%(53)=fn.center%(co.name$,crt.columns%-2)
crt.data$(53)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(54)=len(sys.name$)
crt.x%(54)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(54)=sys.name$
crt.data$(55)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(56)=len(fun.name$)
crt.x%(56)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(56)=fun.name$

rem---------------------------------------------------------
