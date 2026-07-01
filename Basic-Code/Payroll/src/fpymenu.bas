rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYMENU - 12/14/79

crt.field.count% = 69	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  6,5,1,0,25,\	     rem   IO fld #1
	  6,6,1,0,25,\	     rem   IO fld #2
	  6,7,1,0,25,\	     rem   IO fld #3
	  6,8,1,0,25,\	     rem   IO fld #4
	  6,9,1,0,25,\	     rem   IO fld #5
	  6,10,1,0,25,\       rem   IO fld #6
	  6,11,1,0,25,\       rem   IO fld #7
	  6,12,1,0,25,\       rem   IO fld #8
	  6,14,1,0,25,\       rem   IO fld #9
	  6,15,1,0,25,\       rem   IO fld #10
	  6,16,1,0,25,\       rem   IO fld #11
	  6,17,1,0,25,\       rem   IO fld #12
	  6,18,1,0,25,\       rem   IO fld #13
	  6,19,1,0,25,\       rem   IO fld #14
	  44,5,1,0,25,\       rem   IO fld #15
	  44,6,1,0,25,\       rem   IO fld #16
	  44,7,1,0,25,\       rem   IO fld #17
	  44,8,1,0,25,\       rem   IO fld #18
	  44,9,1,0,25,\       rem   IO fld #19
	  44,11,1,0,25,\       rem   IO fld #20
	  44,12,1,0,25,\       rem   IO fld #21
	  44,13,1,0,25,\       rem   IO fld #22
	  44,14,1,0,25,\       rem   IO fld #23
	  44,16,1,0,25,\       rem   IO fld #24
	  44,17,1,0,25,\       rem   IO fld #25
	  44,18,1,0,25,\       rem   IO fld #26
	  44,19,1,0,25,\       rem   IO fld #27
	  47,21,2,0,25,\       rem   IO fld #28
	  41,21,8,0,25,\       rem   IO fld #29
	  62,22,2,0,25,\       rem   IO fld #30
	  66,22,2,0,25,\       rem   IO fld #31
	  1,1,8,0,4,\	    rem   O fld #32
	  1,2,9,0,4,\	    rem   O fld #33
	  1,3,8,0,4,\	    rem   O fld #34
	  10,3,8,0,4,\	     rem   O fld #35
	  4,5,25,0,4,\	     rem   O fld #36
	  4,6,25,0,4,\	     rem   O fld #37
	  4,7,24,0,4,\	     rem   O fld #38
	  4,8,17,0,4,\	     rem   O fld #39
	  4,9,25,0,4,\	     rem   O fld #40
	  4,10,19,0,4,\       rem   O fld #41
	  4,11,24,0,4,\       rem   O fld #42
	  4,12,19,0,4,\       rem   O fld #43
	  4,14,19,0,4,\       rem   O fld #44
	  3,15,26,0,4,\       rem   O fld #45
	  3,16,18,0,4,\       rem   O fld #46
	  3,17,28,0,4,\       rem   O fld #47
	  3,18,32,0,4,\       rem   O fld #48
	  3,19,18,0,4,\       rem   O fld #49
	  41,5,31,0,4,\       rem   O fld #50
	  41,6,28,0,4,\       rem   O fld #51
	  41,7,20,0,4,\       rem   O fld #52
	  41,8,28,0,4,\       rem   O fld #53
	  41,9,25,0,4,\       rem   O fld #54
	  41,11,31,0,4,\       rem   O fld #55
	  41,12,25,0,4,\       rem   O fld #56
	  41,13,26,0,4,\       rem   O fld #57
	  41,14,23,0,4,\       rem   O fld #58
	  41,16,19,0,4,\       rem   O fld #59
	  41,17,37,0,4,\       rem   O fld #60
	  41,18,28,0,4,\       rem   O fld #61
	  41,19,25,0,0,\       rem   O fld #62
	  21,21,29,0,0,\       rem   O fld #63
	  21,21,29,0,0,\       rem   O fld #64
	  12,22,55,0,0,\       rem   O fld #65
	  9,21,60,0,0,\       rem   O fld #66
	  9,21,56,0,0,\       rem   O fld #67
	  9,21,53,0,0,\       rem   O fld #68
	  9,22,60,0,0
	  rem	O fld #69
crt.data$(36)="1.  PAY TRANSACTION ENTRY"
crt.data$(37)="2.  PAY TRANSACTION PROOF"
crt.data$(38)="3.  PAY TRANSACTION SORT"
crt.data$(39)="4.  APPLY PAYROLL"
crt.data$(40)="5.  PRINT PAYROLL JOURNAL"
crt.data$(41)="6.  PRINT PAYCHECKS"
crt.data$(42)="7.  PRINT CHECK REGISTER"
crt.data$(43)="8.  SET SYSTEM DATE"
crt.data$(44)="9.  PARAMETER ENTRY"
crt.data$(45)="10.  QUICK PARAMETER ENTRY"
crt.data$(46)="11.  ACCOUNT ENTRY"
crt.data$(47)="12.  DEDUCTION/EARNING ENTRY"
crt.data$(48)="13.  CREATE SORT PARAMETER FILES"
crt.data$(49)="14.  HISTORY ENTRY"
crt.data$(50)="15.  PRINT QUARTERLY 941 REPORT"
crt.data$(51)="16.  END THE CURRENT QUARTER"
crt.data$(52)="17.  PRINT W2 REPORT"
crt.data$(53)="18.  PRINT YEARLY 940 REPORT"
crt.data$(54)="19.  END THE CURRENT YEAR"
crt.data$(55)="20.  PRINT EMPLOYEE MASTER LIST"
crt.data$(56)="21.  PRINT HISTORY REPORT"
crt.data$(57)="22.  PRINT VACATION REPORT"
crt.data$(58)="23.  PRINT ACCOUNT LIST"
crt.data$(59)="24.  EMPLOYEE ENTRY"
crt.data$(60)="25.  EMPLOYEE DED/EARN AND COST DIST."
crt.data$(61)="26.  EMPLOYEE PAY RATE ENTRY"
crt.data$(62)="27.  USER DEFINED PROGRAM"
crt.data$(63)="ENTER A SELECTION NUMBER [  ]"
crt.data$(64)="ENTER TODAY'S DATE [        ]"
crt.data$(65)="RECORD THE ERROR MESSAGE NUMBER, THEN TYPE  ""OK"" [  ]"
crt.data$(66)="SYSTEM STARTUP -- IN ORDER TO INITIALIZE THE PAYROLL SYSTEM,"
crt.data$(67)="NO PARAMETER FILE -- A NEW PARAMETER FILE MUST BE BUILT."
crt.data$(68)="NO SECOND PARAMETER FILE -- A NEW FILE MUST BE BUILT."
crt.data$(69)="ONE OF THE TWO PARAMETER ENTRY OPTIONS MUST BE SELECTED [  ]"

i%=1
while i%<=69
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(32)=len(co.name$)
crt.x%(32)=fn.center%(co.name$,crt.columns%-2)
crt.data$(32)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(33)=len(sys.name$)
crt.x%(33)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(33)=sys.name$
crt.data$(34)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(35)=len(fun.name$)
crt.x%(35)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(35)=fun.name$

rem---------------------------------------------------------
