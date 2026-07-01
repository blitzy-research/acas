rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPY941A - 19/DEC/79

crt.field.count% = 43	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  12,4,43,0,5,\       rem   IO fld #1
	  12,5,30,0,5,\       rem   IO fld #2
	  57,5,8,0,5,\	     rem   IO fld #3
	  12,6,30,0,5,\       rem   IO fld #4
	  57,6,10,0,5,\       rem   IO fld #5
	  12,7,30,0,5,\       rem   IO fld #6
	  12,8,23,0,5,\       rem   IO fld #7
	  39,8,2,0,5,\	     rem   IO fld #8
	  45,8,5,0,5,\	     rem   IO fld #9
	  42,9,1,0,29,\       rem   IO fld #10
	  62,10,5,0,28,\       rem   IO fld #11
	  63,11,7,2,28,\       rem   IO fld #12
	  63,12,7,2,28,\       rem   IO fld #13
	  62,13,7,2,30,\       rem   IO fld #14
	  63,14,7,2,28,\       rem   IO fld #15
	  29,15,7,2,28,\       rem   IO fld #16
	  63,15,7,2,28,\       rem   IO fld #17
	  29,16,7,2,28,\       rem   IO fld #18
	  63,16,7,2,28,\       rem   IO fld #19
	  63,17,7,2,28,\       rem   IO fld #20
	  62,18,7,2,30,\       rem   IO fld #21
	  63,19,7,2,28,\       rem   IO fld #22
	  63,20,7,2,28,\       rem   IO fld #23
	  62,21,7,2,30,\       rem   IO fld #24
	  63,22,7,2,28,\       rem   IO fld #25
	  1,1,8,0,4,\	    rem   O fld #26
	  1,2,9,0,4,\	    rem   O fld #27
	  1,3,8,0,4,\	    rem   O fld #28
	  10,3,8,0,4,\	     rem   O fld #29
	  17,9,27,0,4,\       rem   O fld #30
	  1,10,19,0,4,\       rem   O fld #31
	  1,11,20,0,4,\       rem   O fld #32
	  1,12,25,0,4,\       rem   O fld #33
	  1,13,76,0,4,\       rem   O fld #34
	  1,14,37,0,4,\       rem   O fld #35
	  1,15,58,0,4,\       rem   O fld #36
	  1,16,58,0,4,\       rem   O fld #37
	  1,17,16,0,4,\       rem   O fld #38
	  1,18,76,0,4,\       rem   O fld #39
	  1,19,28,0,4,\       rem   O fld #40
	  1,20,11,0,4,\       rem   O fld #41
	  1,21,20,0,4,\       rem   O fld #42
	  1,22,9,0,4
	  rem	O fld #43
crt.data$(30)="PRINT NAME AND ADDRESS  [ ]"
crt.data$(31)="NUMBER OF EMPLOYEES"
crt.data$(32)="TOTAL WAGES AND TIPS"
crt.data$(33)="TOTAL INCOME TAX WITHHELD"
crt.data$(34)="ADJUSTMENT OF WITHHELD INCOME TAX FROM PREVIOUS QUARTERS    [              ]"
crt.data$(35)="ADJUSTED TOTAL OF INCOME TAX WITHHELD"
crt.data$(36)="TAXABLE FICA WAGES PAID                     TIMES 12.26% ="
crt.data$(37)="TAXABLE TIPS REPORTED                       TIMES  6.13% ="
crt.data$(38)="TOTAL FICA TAXES"
crt.data$(39)="ADJUSTMENT OF FICA TAXES                                    [              ]"
crt.data$(40)="ADJUSTED TOTAL OF FICA TAXES"
crt.data$(41)="TOTAL TAXES"
crt.data$(42)="EARNED INCOME CREDIT"
crt.data$(43)="NET TAXES"

i%=1
while i%<=43
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(26)=len(co.name$)
crt.x%(26)=fn.center%(co.name$,crt.columns%-2)
crt.data$(26)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(27)=len(sys.name$)
crt.x%(27)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(27)=sys.name$
crt.data$(28)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(29)=len(fun.name$)
crt.x%(29)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(29)=fun.name$

rem---------------------------------------------------------
