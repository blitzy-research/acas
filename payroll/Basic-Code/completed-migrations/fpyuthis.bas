rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYUTHIS - 4-DEC-79|4:30PM

crt.field.count% = 73	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  73,3,5,0,25,\       rem   IO fld #1
	  8,5,7,2,28,\	     rem   IO fld #2
	  27,5,7,2,28,\       rem   IO fld #3
	  49,5,7,2,28,\       rem   IO fld #4
	  67,5,7,2,28,\       rem   IO fld #5
	  27,6,7,2,28,\       rem   IO fld #6
	  49,6,7,2,28,\       rem   IO fld #7
	  67,6,7,2,28,\       rem   IO fld #8
	  27,7,7,2,28,\       rem   IO fld #9
	  49,7,7,2,28,\       rem   IO fld #10
	  67,7,7,2,28,\       rem   IO fld #11
	  27,8,7,2,28,\       rem   IO fld #12
	  49,8,7,2,28,\       rem   IO fld #13
	  7,10,7,2,28,\       rem   IO fld #14
	  22,10,7,2,28,\       rem   IO fld #15
	  37,10,7,2,28,\       rem   IO fld #16
	  52,10,7,2,28,\       rem   IO fld #17
	  67,10,7,2,28,\       rem   IO fld #18
	  7,11,7,2,28,\       rem   IO fld #19
	  22,11,7,2,28,\       rem   IO fld #20
	  37,11,7,2,28,\       rem   IO fld #21
	  67,11,7,2,28,\       rem   IO fld #22
	  22,12,7,2,28,\       rem   IO fld #23
	  37,12,7,2,28,\       rem   IO fld #24
	  52,12,7,2,28,\       rem   IO fld #25
	  67,12,7,2,28,\       rem   IO fld #26
	  8,15,7,2,28,\       rem   IO fld #27
	  27,15,7,2,28,\       rem   IO fld #28
	  49,15,7,2,28,\       rem   IO fld #29
	  67,15,7,2,28,\       rem   IO fld #30
	  27,16,7,2,28,\       rem   IO fld #31
	  49,16,7,2,28,\       rem   IO fld #32
	  67,16,7,2,28,\       rem   IO fld #33
	  27,17,7,2,28,\       rem   IO fld #34
	  49,17,7,2,28,\       rem   IO fld #35
	  67,17,7,2,28,\       rem   IO fld #36
	  27,18,7,2,28,\       rem   IO fld #37
	  49,18,7,2,28,\       rem   IO fld #38
	  7,20,7,2,28,\       rem   IO fld #39
	  22,20,7,2,28,\       rem   IO fld #40
	  37,20,7,2,28,\       rem   IO fld #41
	  52,20,7,2,28,\       rem   IO fld #42
	  67,20,7,2,28,\       rem   IO fld #43
	  7,21,7,2,28,\       rem   IO fld #44
	  22,21,7,2,28,\       rem   IO fld #45
	  37,21,7,2,28,\       rem   IO fld #46
	  67,21,7,2,28,\       rem   IO fld #47
	  22,22,7,2,28,\       rem   IO fld #48
	  37,22,7,2,28,\       rem   IO fld #49
	  52,22,7,2,28,\       rem   IO fld #50
	  67,22,7,2,28,\       rem   IO fld #51
	  1,1,8,0,4,\	    rem   O fld #52
	  1,2,9,0,4,\	    rem   O fld #53
	  1,3,8,0,4,\	    rem   O fld #54
	  10,3,8,0,4,\	     rem   O fld #55
	  26,4,30,0,4,\       rem   O fld #56
	  1,5,79,0,4,\	     rem   O fld #57
	  16,6,64,0,4,\       rem   O fld #58
	  1,7,79,0,4,\	     rem   O fld #59
	  22,8,40,0,4,\       rem   O fld #60
	  29,9,27,0,4,\       rem   O fld #61
	  1,10,79,0,4,\       rem   O fld #62
	  1,11,79,0,4,\       rem   O fld #63
	  1,12,79,0,4,\       rem   O fld #64
	  26,14,30,0,4,\       rem   O fld #65
	  1,15,79,0,4,\       rem   O fld #66
	  16,16,64,0,4,\       rem   O fld #67
	  1,17,79,0,4,\       rem   O fld #68
	  22,18,40,0,4,\       rem   O fld #69
	  29,19,27,0,4,\       rem   O fld #70
	  1,20,79,0,4,\       rem   O fld #71
	  1,21,79,0,4,\       rem   O fld #72
	  1,22,79,0,4
	  rem	O fld #73
crt.data$(56)="QTD EARNINGS BY TAX CATAGORIES"
crt.data$(57)="INCOME[            ]OTHER[            ]NO TAXES[            ]FICA[            ]"
crt.data$(58)="EIC CREDIT[            ]    TIPS[            ] NET[            ]"
crt.data$(59)="QTD TAXES WITHHELD:   FWT[            ]     SWT[            ] LWT[            ]"
crt.data$(60)="FICA[            ]     SDI[            ]"
crt.data$(61)="QTD EARNINGS AND DEDUCTIONS"
crt.data$(62)="SYS:1[            ]2[            ]3[            ]4[            ]5[            ]"
crt.data$(63)="EMP:1[            ]2[            ]3[            ]OTHER DEDUCTIONS[            ]"
crt.data$(64)="UNITS BY PAY TYPE: 1[            ]2[            ]3[            ]4[            ]"
crt.data$(65)="YTD EARNINGS BY TAX CATAGORIES"
crt.data$(66)="INCOME[            ]OTHER[            ]NO TAXES[            ]FICA[            ]"
crt.data$(67)="EIC CREDIT[            ]    TIPS[            ] NET[            ]"
crt.data$(68)="YTD TAXES WITHHELD:   FWT[            ]     SWT[            ] LWT[            ]"
crt.data$(69)="FICA[            ]     SDI[            ]"
crt.data$(70)="YTD EARNINGS AND DEDUCTIONS"
crt.data$(71)="SYS:1[            ]2[            ]3[            ]4[            ]5[            ]"
crt.data$(72)="EMP:1[            ]2[            ]3[            ]OTHER DEDUCTIONS[            ]"
crt.data$(73)="UNITS BY PAY TYPE: 1[            ]2[            ]3[            ]4[            ]"

i%=1
while i%<=73
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(52)=len(co.name$)
crt.x%(52)=fn.center%(co.name$,crt.columns%-2)
crt.data$(52)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(53)=len(sys.name$)
crt.x%(53)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(53)=sys.name$
crt.data$(54)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(55)=len(fun.name$)
crt.x%(55)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(55)=fun.name$

rem---------------------------------------------------------
