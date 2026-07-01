rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYRATE - 12/7/79

crt.field.count% = 58	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  11,5,5,0,29,\       rem   IO fld #1
	  25,5,30,0,29,\       rem   IO fld #2
	  64,5,11,0,29,\       rem   IO fld #3
	  33,8,1,0,29,\       rem   IO fld #4
	  33,9,1,0,29,\       rem   IO fld #5
	  25,11,5,2,28,\       rem   IO fld #6
	  25,12,5,2,28,\       rem   IO fld #7
	  25,13,5,2,28,\       rem   IO fld #8
	  25,14,5,2,28,\       rem   IO fld #9
	  33,15,1,0,28,\       rem   IO fld #10
	  25,16,5,2,28,\       rem   IO fld #11
	  25,17,5,2,28,\       rem   IO fld #12
	  24,18,6,2,28,\       rem   IO fld #13
	  74,9,1,0,29,\       rem   IO fld #14
	  73,10,2,0,28,\       rem   IO fld #15
	  73,11,2,0,28,\       rem   IO fld #16
	  73,12,2,0,28,\       rem   IO fld #17
	  74,13,1,0,29,\       rem   IO fld #18
	  74,16,1,0,29,\       rem   IO fld #19
	  73,17,2,0,28,\       rem   IO fld #20
	  25,20,5,2,28,\       rem   IO fld #21
	  49,20,5,2,28,\       rem   IO fld #22
	  66,20,5,2,28,\       rem   IO fld #23
	  25,21,5,2,28,\       rem   IO fld #24
	  49,21,5,2,28,\       rem   IO fld #25
	  66,21,5,2,28,\       rem   IO fld #26
	  49,22,5,2,28,\       rem   IO fld #27
	  66,22,5,2,28,\       rem   IO fld #28
	  1,1,8,0,4,\	    rem   O fld #29
	  1,2,9,0,4,\	    rem   O fld #30
	  1,3,8,0,4,\	    rem   O fld #31
	  10,3,8,0,4,\	     rem   O fld #32
	  2,5,61,0,4,\	     rem   O fld #33
	  1,6,75,0,4,\	     rem   O fld #34
	  4,7,68,0,4,\	     rem   O fld #35
	  1,8,67,0,4,\	     rem   O fld #36
	  1,9,75,0,4,\	     rem   O fld #37
	  1,10,75,0,4,\       rem   O fld #38
	  1,11,15,0,4,\       rem   O fld #39
	  19,11,57,0,4,\       rem   O fld #40
	  1,12,15,0,4,\       rem   O fld #41
	  19,12,57,0,4,\       rem   O fld #42
	  1,13,15,0,4,\       rem   O fld #43
	  19,13,57,0,4,\       rem   O fld #44
	  1,14,15,0,4,\       rem   O fld #45
	  19,14,18,0,4,\       rem   O fld #46
	  39,14,37,0,4,\       rem   O fld #47
	  1,15,36,0,4,\       rem   O fld #48
	  39,15,37,0,4,\       rem   O fld #49
	  1,16,36,0,4,\       rem   O fld #50
	  39,16,37,0,4,\       rem   O fld #51
	  1,17,36,0,4,\       rem   O fld #52
	  39,17,37,0,4,\       rem   O fld #53
	  1,18,75,0,4,\       rem   O fld #54
	  6,19,56,0,4,\       rem   O fld #55
	  4,20,72,0,4,\       rem   O fld #56
	  4,21,72,0,4,\       rem   O fld #57
	  4,22,72,0,4
	  rem	O fld #58
crt.data$(33)="EMPL NO [     ]   NAME                                    SSN"
crt.data$(34)="---------------------------------------------------------------------------"
crt.data$(35)="PAY INTERVAL  AND  PAY RATES    |        T A X   W I T H O L D I N G"
crt.data$(36)="PAY TYPE (H=HOURLY,S=SALARIED) [ ] |            A L L O W A N C E S"
crt.data$(37)="PAY INTERVAL (S=SEMI-MONTHLY,  [ ] |  MARITAL STATUS(M=MARRIED,S=SINGLE)[ ]"
crt.data$(38)="(M=MONTHLY, W=WEEKLY, B=BIWEEKLY)  |          FEDERAL  WH  ALLOWANCES  [  ]"
crt.data$(39)="pr1.rate.nameS1"
crt.data$(40)="RATE [         ] |          STATE    WH  ALLOWANCES  [  ]"
crt.data$(41)="pr1.rate.nameS2"
crt.data$(42)="RATE [         ] |          LOCAL    WH  ALLOWANCES  [  ]"
crt.data$(43)="pr1.rate.nameS3"
crt.data$(44)="RATE [         ] |  EARNED INCOME CREDIT USED (Y OR N)[ ]"
crt.data$(45)="pr1.rate.nameS4"
crt.data$(46)="RATE [         ] |"
crt.data$(47)="S T A T E   O F   C A L I F O R N I A"
crt.data$(48)="RATE 4 TAX EXCLUSION TYPE(1-4) [ ] |"
crt.data$(49)="S P E C I A L   I N F O R M A T I O N"
crt.data$(50)="AUTOGEN UNITS          [         ] |"
crt.data$(51)="HEAD OF HOUSEHOLD         (Y OR N)[ ]"
crt.data$(52)="NORMAL UNITS           [         ] |"
crt.data$(53)="SPECIAL  WITHOLDING ALLOWANCES   [  ]"
crt.data$(54)="MAXIMUM PAY           [          ] |---------------------------------------"
crt.data$(55)="(VAC. AND S.L.  RATES ARE UNITS EARNED PER PAY INTERVAL)"
crt.data$(56)="VACATION     RATE   [         ] ACCUMULATED [         ] USED [         ]"
crt.data$(57)="SICK LEAVE   RATE   [         ] ACCUMULATED [         ] USED [         ]"
crt.data$(58)="COMPENSATORY TIME               ACCUMULATED [         ] USED [         ]"

i%=1
while i%<=58
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(29)=len(co.name$)
crt.x%(29)=fn.center%(co.name$,crt.columns%-2)
crt.data$(29)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(30)=len(sys.name$)
crt.x%(30)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(30)=sys.name$
crt.data$(31)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(32)=len(fun.name$)
crt.x%(32)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(32)=fun.name$

rem---------------------------------------------------------
