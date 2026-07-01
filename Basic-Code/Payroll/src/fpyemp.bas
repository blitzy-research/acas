rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYEMP - 11/21/79

crt.field.count% = 41	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  19,5,5,0,29,\       rem   IO fld #1
	  27,6,30,0,29,\       rem   IO fld #2
	  27,7,30,0,29,\       rem   IO fld #3
	  27,8,30,0,29,\       rem   IO fld #4
	  27,9,18,0,29,\       rem   IO fld #5
	  55,9,2,0,29,\       rem   IO fld #6
	  65,9,5,0,29,\       rem   IO fld #7
	  27,10,13,0,29,\	rem   IO fld #8
	  20,12,11,0,29,\	rem   IO fld #9
	  20,13,25,0,29,\	rem   IO fld #10
	  20,14,8,0,29,\       rem   IO fld #11
	  20,15,1,0,29,\       rem   IO fld #12
	  72,12,1,0,29,\       rem   IO fld #13
	  70,13,3,0,29,\       rem   IO fld #14
	  71,14,2,0,25,\       rem   IO fld #15
	  17,17,8,0,29,\       rem   IO fld #16
	  63,17,10,0,29,\	rem   IO fld #17
	  17,18,8,0,29,\       rem   IO fld #18
	  56,22,3,0,29,\       rem   IO fld #19
	  1,1,8,0,4,\	    rem   O fld #20
	  1,2,9,0,4,\	    rem   O fld #21
	  1,3,8,0,4,\	    rem   O fld #22
	  10,3,8,0,4,\	     rem   O fld #23
	  2,5,72,0,4,\	     rem   O fld #24
	  5,6,69,0,4,\	     rem   O fld #25
	  5,7,69,0,4,\	     rem   O fld #26
	  5,8,69,0,4,\	     rem   O fld #27
	  5,9,69,0,4,\	     rem   O fld #28
	  5,10,69,0,4,\       rem   O fld #29
	  5,11,69,0,4,\       rem   O fld #30
	  5,12,69,0,4,\       rem   O fld #31
	  5,13,69,0,4,\       rem   O fld #32
	  5,14,46,0,4,\       rem   O fld #33
	  55,14,19,0,0,\       rem   O fld #34
	  5,15,46,0,4,\       rem   O fld #35
	  5,16,69,0,4,\       rem   O fld #36
	  5,17,69,0,4,\       rem   O fld #37
	  5,18,70,0,4,\       rem   O fld #38
	  14,20,53,0,0,\       rem   O fld #39
	  14,21,55,0,0,\       rem   O fld #40
	  14,22,46,0,0
	  rem	O fld #41
crt.data$(24)="EMPLOYEE NUMBER [     ] ------------------------------------------------"
crt.data$(25)="|     NAME           [                              ]               |"
crt.data$(26)="|     ADDRESS     1  [                              ]               |"
crt.data$(27)="|                 2  [                              ]               |"
crt.data$(28)="|             CITY   [                  ]  STATE [  ]  ZIP [     ]  |"
crt.data$(29)="|             PHONE  [             ]                                |"
crt.data$(30)="---------------------------------------------------------------------"
crt.data$(31)="SOC SEC NO.   [           ]                  |    PENSION (Y/N)   [ ]"
crt.data$(32)="BANK ACCT NO. [                         ]    |    JOB CODE      [   ]"
crt.data$(33)="BIRTH DATE    [        ]                     |"
crt.data$(34)="TAXING STATE   [  ]"
crt.data$(35)="SEX           [ ]                            |"
crt.data$(36)="---------------------------------------------------------------------"
crt.data$(37)="START DATE [        ]      |      EMPLOYMENT STATUS      [          ]"
crt.data$(38)="TERM. DATE [        ]      |      (A=ACTIVE, L=ON LEAVE, T=TERMINATED)"
crt.data$(39)="THE EMPLOYEE MASTER AND HISTORY FILES ARE NOT PRESENT"
crt.data$(40)="TYPE  ""RUN"" TO CREATE BOTH FILES.    PRESS THE ESCAPE"
crt.data$(41)="KEY TO RETURN TO THE PAYROLL SYSTEM MENU [   ]"

i%=1
while i%<=41
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(20)=len(co.name$)
crt.x%(20)=fn.center%(co.name$,crt.columns%-2)
crt.data$(20)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(21)=len(sys.name$)
crt.x%(21)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(21)=sys.name$
crt.data$(22)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(23)=len(fun.name$)
crt.x%(23)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(23)=fun.name$

rem---------------------------------------------------------
