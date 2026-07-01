rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYUPAYM - 6-DEC-79|12:30PM

crt.field.count% = 57	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  28,5,7,2,28,\       rem   IO fld #1
	  46,5,8,0,29,\       rem   IO fld #2
	  28,6,7,2,28,\       rem   IO fld #3
	  46,6,8,0,29,\       rem   IO fld #4
	  28,7,7,2,28,\       rem   IO fld #5
	  46,7,8,0,29,\       rem   IO fld #6
	  28,8,7,2,28,\       rem   IO fld #7
	  46,8,8,0,29,\       rem   IO fld #8
	  28,9,7,2,28,\       rem   IO fld #9
	  46,9,8,0,29,\       rem   IO fld #10
	  28,10,7,2,28,\       rem   IO fld #11
	  46,10,8,0,29,\       rem   IO fld #12
	  28,11,7,2,28,\       rem   IO fld #13
	  46,11,8,0,29,\       rem   IO fld #14
	  28,12,7,2,28,\       rem   IO fld #15
	  46,12,8,0,29,\       rem   IO fld #16
	  28,13,7,2,28,\       rem   IO fld #17
	  46,13,8,0,29,\       rem   IO fld #18
	  28,14,7,2,28,\       rem   IO fld #19
	  46,14,8,0,29,\       rem   IO fld #20
	  28,15,7,2,28,\       rem   IO fld #21
	  46,15,8,0,29,\       rem   IO fld #22
	  28,16,7,2,28,\       rem   IO fld #23
	  46,16,8,0,29,\       rem   IO fld #24
	  12,18,7,2,28,\       rem   IO fld #25
	  29,18,7,2,28,\       rem   IO fld #26
	  46,18,7,2,28,\       rem   IO fld #27
	  63,18,7,2,28,\       rem   IO fld #28
	  12,19,7,2,28,\       rem   IO fld #29
	  29,19,7,2,28,\       rem   IO fld #30
	  46,19,7,2,28,\       rem   IO fld #31
	  63,19,7,2,28,\       rem   IO fld #32
	  12,20,7,2,28,\       rem   IO fld #33
	  29,20,7,2,28,\       rem   IO fld #34
	  46,20,7,2,28,\       rem   IO fld #35
	  63,20,7,2,28,\       rem   IO fld #36
	  1,1,8,0,4,\	    rem   O fld #37
	  1,2,9,0,4,\	    rem   O fld #38
	  1,3,8,0,4,\	    rem   O fld #39
	  10,3,8,0,4,\	     rem   O fld #40
	  26,4,28,0,4,\       rem   O fld #41
	  24,5,31,0,4,\       rem   O fld #42
	  24,6,31,0,4,\       rem   O fld #43
	  24,7,31,0,4,\       rem   O fld #44
	  24,8,31,0,4,\       rem   O fld #45
	  24,9,31,0,4,\       rem   O fld #46
	  24,10,31,0,4,\       rem   O fld #47
	  24,11,31,0,4,\       rem   O fld #48
	  24,12,31,0,4,\       rem   O fld #49
	  24,13,31,0,4,\       rem   O fld #50
	  24,14,31,0,4,\       rem   O fld #51
	  24,15,31,0,4,\       rem   O fld #52
	  24,16,31,0,4,\       rem   O fld #53
	  29,17,22,0,4,\       rem   O fld #54
	  3,18,73,0,4,\       rem   O fld #55
	  3,19,73,0,4,\       rem   O fld #56
	  3,20,73,0,4
	  rem	O fld #57
crt.data$(41)="FWT TAX PAYMENTS FOR QUARTER"
crt.data$(42)="1. [            ] ON [        ]"
crt.data$(43)="2. [            ] ON [        ]"
crt.data$(44)="3. [            ] ON [        ]"
crt.data$(45)="4. [            ] ON [        ]"
crt.data$(46)="5. [            ] ON [        ]"
crt.data$(47)="6. [            ] ON [        ]"
crt.data$(48)="7. [            ] ON [        ]"
crt.data$(49)="8. [            ] ON [        ]"
crt.data$(50)="9. [            ] ON [        ]"
crt.data$(51)="10.[            ] ON [        ]"
crt.data$(52)="11.[            ] ON [        ]"
crt.data$(53)="12.[            ] ON [        ]"
crt.data$(54)="QUARTERLY TAX PAYMENTS"
crt.data$(55)="FWT:  1.[            ] 2.[            ] 3.[            ] 4.[            ]"
crt.data$(56)="FICA: 1.[            ] 2.[            ] 3.[            ] 4.[            ]"
crt.data$(57)="FUTA: 1.[            ] 2.[            ] 3.[            ] 4.[            ]"

i%=1
while i%<=57
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(37)=len(co.name$)
crt.x%(37)=fn.center%(co.name$,crt.columns%-2)
crt.data$(37)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(38)=len(sys.name$)
crt.x%(38)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(38)=sys.name$
crt.data$(39)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(40)=len(fun.name$)
crt.x%(40)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(40)=fun.name$

rem---------------------------------------------------------
