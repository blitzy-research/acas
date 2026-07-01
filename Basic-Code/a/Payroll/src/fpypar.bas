rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYPAR - 12/26/79

crt.field.count% = 48	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  64,6,12,0,25,\       rem   IO fld #1
	  41,7,1,0,25,\       rem   IO fld #2
	  34,8,8,0,25,\       rem   IO fld #3
	  75,7,1,0,24,\       rem   IO fld #4
	  74,8,2,0,24,\       rem   IO fld #5
	  14,11,60,0,25,\	rem   IO fld #6
	  16,12,30,0,25,\	rem   IO fld #7
	  16,13,30,0,25,\	rem   IO fld #8
	  16,14,30,0,25,\	rem   IO fld #9
	  56,12,18,0,25,\	rem   IO fld #10
	  56,13,2,0,25,\       rem   IO fld #11
	  69,13,5,0,25,\       rem   IO fld #12
	  61,14,13,0,25,\	rem   IO fld #13
	  16,16,15,0,25,\	rem   IO fld #14
	  38,16,15,0,25,\	rem   IO fld #15
	  59,16,15,0,25,\	rem   IO fld #16
	  22,18,2,0,24,\       rem   IO fld #17
	  52,18,1,0,25,\       rem   IO fld #18
	  73,18,1,0,25,\       rem   IO fld #19
	  47,10,1,0,25,\       rem   IO fld #20
	  45,19,8,0,25,\       rem   IO fld #21
	  59,15,1,0,25,\       rem   IO fld #22
	  1,1,8,0,0,\	    rem   O fld #23
	  1,2,9,0,0,\	    rem   O fld #24
	  1,3,8,0,0,\	    rem   O fld #25
	  10,3,8,0,0,\	     rem   O fld #26
	  2,5,75,0,0,\	     rem   O fld #27
	  2,6,75,0,0,\	     rem   O fld #28
	  2,7,75,0,0,\	     rem   O fld #29
	  2,8,75,0,0,\	     rem   O fld #30
	  2,9,75,0,0,\	     rem   O fld #31
	  2,10,7,0,0,\	     rem   O fld #32
	  5,11,70,0,0,\       rem   O fld #33
	  5,12,70,0,0,\       rem   O fld #34
	  5,13,70,0,0,\       rem   O fld #35
	  5,14,70,0,0,\       rem   O fld #36
	  5,15,64,0,0,\       rem   O fld #37
	  5,16,70,0,0,\       rem   O fld #38
	  5,17,70,0,0,\       rem   O fld #39
	  5,18,70,0,0,\       rem   O fld #40
	  17,6,36,0,0,\       rem   O fld #41
	  17,7,50,0,0,\       rem   O fld #42
	  17,8,48,0,0,\       rem   O fld #43
	  29,10,20,0,0,\       rem   O fld #44
	  25,19,29,0,0,\       rem   O fld #45
	  20,15,41,0,0,\       rem   O fld #46
	  21,11,38,0,0,\       rem   O fld #47
	  21,13,38,0,0
	  rem	O fld #48
crt.data$(27)="---------------------------------------------------------------------------"
crt.data$(28)="PAY INTERVAL USED(S,M,W,B  IF MORE THAN ONE, SELECT SCREEN 2)[            ]"
crt.data$(29)="DATE FORM (1=MM/DD/YY, 2=DD/MM/YY)    [ ]         LAST QUARTER ENDED    [ ]"
crt.data$(30)="ENDING DAY OF LAST PAY PERIOD  [        ]              CURRENT YEAR    [  ]"
crt.data$(31)="---------------------------------------------------------------------------"
crt.data$(32)="COMPANY"
crt.data$(33)="NAME    [                                                            ]"
crt.data$(34)="ADDRESS 1 [                              ]  CITY  [                  ]"
crt.data$(35)="ADDRESS 2 [                              ]  STATE [  ]    ZIP  [     ]"
crt.data$(36)="ADDRESS 3 [                              ]  PHONE      [             ]"
crt.data$(37)="GOVT ID        FEDERAL                STATE                LOCAL"
crt.data$(38)="NUMBERS   [               ]     [               ]    [               ]"
crt.data$(39)="----------------------------------------------------------------------"
crt.data$(40)="LINES PER PAGE  [  ]    SUPPRESS CONSOLE BELL [ ]    DEBUGGING AID [ ]"
crt.data$(41)="1. COMPANY ID AND GENERAL PARAMETERS"
crt.data$(42)="2. PAY INTERVALS AND DEFAULT EMPLOYEE PAYROLL DATA"
crt.data$(43)="3. PAYROLL SYSTEM CONFIGURATION AND GL INTERFACE"
crt.data$(44)="SELECT A SCREEN  [ ]"
crt.data$(45)="ENTER TODAY'S DATE [        ]"
crt.data$(46)="ENTER THE SYSTEM FILE DRIVE  (A OR B) [ ]"
crt.data$(47)="BUILDING DEFAULT FIRST  PARAMETER FILE"
crt.data$(48)="BUILDING DEFAULT SECOND PARAMETER FILE"

i%=1
while i%<=48
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(23)=len(co.name$)
crt.x%(23)=fn.center%(co.name$,crt.columns%-2)
crt.data$(23)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(24)=len(sys.name$)
crt.x%(24)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(24)=sys.name$
crt.data$(25)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(26)=len(fun.name$)
crt.x%(26)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(26)=fun.name$

rem---------------------------------------------------------
