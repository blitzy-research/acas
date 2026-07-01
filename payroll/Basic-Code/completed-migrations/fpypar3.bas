rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYPAR3 - 11/18/79

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
	  22,7,1,0,29,\       rem   IO fld #1
	  22,8,1,0,29,\       rem   IO fld #2
	  22,9,1,0,29,\       rem   IO fld #3
	  50,7,1,0,29,\       rem   IO fld #4
	  50,8,1,0,29,\       rem   IO fld #5
	  50,9,1,0,29,\       rem   IO fld #6
	  74,7,1,0,29,\       rem   IO fld #7
	  74,8,1,0,29,\       rem   IO fld #8
	  74,9,1,0,29,\       rem   IO fld #9
	  33,12,1,0,29,\       rem   IO fld #10
	  33,13,1,0,29,\       rem   IO fld #11
	  32,14,2,0,29,\       rem   IO fld #12
	  33,15,1,0,29,\       rem   IO fld #13
	  19,18,1,0,29,\       rem   IO fld #14
	  37,18,8,0,29,\       rem   IO fld #15
	  15,19,30,0,29,\	rem   IO fld #16
	  74,12,1,0,29,\       rem   IO fld #17
	  74,13,1,0,29,\       rem   IO fld #18
	  63,14,7,2,28,\       rem   IO fld #19
	  72,17,3,0,29,\       rem   IO fld #20
	  72,18,3,0,29,\       rem   IO fld #21
	  66,21,1,0,29,\       rem   IO fld #22
	  1,1,8,0,4,\	    rem   O fld #23
	  1,2,9,0,4,\	    rem   O fld #24
	  1,3,8,0,4,\	    rem   O fld #25
	  10,3,8,0,4,\	     rem   O fld #26
	  20,5,41,0,4,\       rem   O fld #27
	  5,6,70,0,4,\	     rem   O fld #28
	  5,7,71,0,4,\	     rem   O fld #29
	  5,8,71,0,4,\	     rem   O fld #30
	  5,9,71,0,4,\	     rem   O fld #31
	  5,10,71,0,4,\       rem   O fld #32
	  7,11,65,0,4,\       rem   O fld #33
	  5,12,71,0,4,\       rem   O fld #34
	  5,13,71,0,4,\       rem   O fld #35
	  5,14,71,0,4,\       rem   O fld #36
	  5,15,71,0,4,\       rem   O fld #37
	  5,16,70,0,4,\       rem   O fld #38
	  6,17,70,0,4,\       rem   O fld #39
	  5,18,71,0,4,\       rem   O fld #40
	  5,19,43,0,4,\       rem   O fld #41
	  5,20,71,0,4,\       rem   O fld #42
	  11,21,57,0,4,\       rem   O fld #43
	  16,22,47,0,4
	  rem	O fld #44
crt.data$(27)="D I S K   D R I V E   A L L O C A T I O N"
crt.data$(28)="SINGLE RECORD FILES           STATIC  FILES            PAY CYCLE FILES"
crt.data$(29)="TAX TABLES      [ ]        PAYROLL ACCOUNTS [ ]        HOURS BATCH  [ ]"
crt.data$(30)="SYSTEM DED/EARN [ ]        EMPLOYEE MASTER  [ ]        PAY CHECK    [ ]"
crt.data$(31)="COMPANY HISTORY [ ]        EMPLOYEE HISTORY [ ]        PAY DETAIL   [ ]"
crt.data$(32)="-----------------------------------------------------------------------"
crt.data$(33)="G E N E R A L   L E D G E R      |      C H E C K   W R I T I N G"
crt.data$(34)="GL INTERFACE USED (Y OR N) [ ]     |  COMPUTER CHECK PRINT (Y OR N) [ ]"
crt.data$(35)="GL BATCH FILE OUTPUT DRIVE [ ]     |  VOID CHECKS OVER MAX (Y OR N) [ ]"
crt.data$(36)="GL COA FILE SUFFIX        [  ]     |  MAXIMUM AMOUNT     [            ]"
crt.data$(37)="GL DATA DRIVE              [ ]     |-----------------------------------"
crt.data$(38)="------------------------------------------|    PAYROLL SYSTEM ACCOUNTS"
crt.data$(39)="U S E R   D E F I N E D   P R O G R A M  |  OFFSET CASH  ACCOUNT [   ]"
crt.data$(40)="PROGRAM USED [ ]  PROGRAM NAME [        ] |  DEFAULT DIST ACCOUNT [   ]"
crt.data$(41)="DESC.    [                              ] |"
crt.data$(42)="-----------------------------------------------------------------------"
crt.data$(43)="DISTRIBUTE EMPLOYEE COST TO  1-5 GL ACCOUNTS (Y OR N) [ ]"
crt.data$(44)="(IF N, ONE ACCOUNT CAN BE ENTERED PER EMPLOYEE)"

i%=1
while i%<=44
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
