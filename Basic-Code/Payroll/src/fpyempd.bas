rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYEMPD - 12/11/79

crt.field.count% = 85	    rem number of screen fields
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
	  26,5,30,0,29,\       rem   IO fld #2
	  64,5,11,0,29,\       rem   IO fld #3
	  27,15,3,2,24,\       rem   IO fld #4
	  11,10,3,0,24,\       rem   IO fld #5
	  27,10,3,2,24,\       rem   IO fld #6
	  11,11,3,0,24,\       rem   IO fld #7
	  27,11,3,2,24,\       rem   IO fld #8
	  11,12,3,0,24,\       rem   IO fld #9
	  27,12,3,2,24,\       rem   IO fld #10
	  11,13,3,0,24,\       rem   IO fld #11
	  27,13,3,2,24,\       rem   IO fld #12
	  11,14,3,0,24,\       rem   IO fld #13
	  27,14,3,2,24,\       rem   IO fld #14
	  54,9,1,0,29,\       rem   IO fld #15
	  54,10,1,0,29,\       rem   IO fld #16
	  54,11,1,0,29,\       rem   IO fld #17
	  54,12,1,0,29,\       rem   IO fld #18
	  74,9,1,0,29,\       rem   IO fld #19
	  74,10,1,0,29,\       rem   IO fld #20
	  74,11,1,0,29,\       rem   IO fld #21
	  46,15,1,0,29,\       rem   IO fld #22
	  52,15,1,0,29,\       rem   IO fld #23
	  58,15,1,0,29,\       rem   IO fld #24
	  64,15,1,0,29,\       rem   IO fld #25
	  70,15,1,0,29,\       rem   IO fld #26
	  3,20,1,0,29,\       rem   IO fld #27
	  6,20,15,0,29,\       rem   IO fld #28
	  24,20,1,0,29,\       rem   IO fld #29
	  28,20,3,0,28,\       rem   IO fld #30
	  34,20,1,0,29,\       rem   IO fld #31
	  38,20,6,2,28,\       rem   IO fld #32
	  51,20,1,0,29,\       rem   IO fld #33
	  55,20,7,2,28,\       rem   IO fld #34
	  69,20,1,0,29,\       rem   IO fld #35
	  72,20,2,0,28,\       rem   IO fld #36
	  3,21,1,0,29,\       rem   IO fld #37
	  6,21,15,0,29,\       rem   IO fld #38
	  24,21,1,0,29,\       rem   IO fld #39
	  28,21,3,0,28,\       rem   IO fld #40
	  34,21,1,0,29,\       rem   IO fld #41
	  38,21,6,2,28,\       rem   IO fld #42
	  51,21,1,0,29,\       rem   IO fld #43
	  55,21,7,2,28,\       rem   IO fld #44
	  69,21,1,0,29,\       rem   IO fld #45
	  72,21,2,0,28,\       rem   IO fld #46
	  3,22,1,0,29,\       rem   IO fld #47
	  6,22,15,0,29,\       rem   IO fld #48
	  24,22,1,0,29,\       rem   IO fld #49
	  28,22,3,0,28,\       rem   IO fld #50
	  34,22,1,0,29,\       rem   IO fld #51
	  38,22,6,2,28,\       rem   IO fld #52
	  51,22,1,0,29,\       rem   IO fld #53
	  55,22,7,2,28,\       rem   IO fld #54
	  69,22,1,0,29,\       rem   IO fld #55
	  72,22,2,0,28,\       rem   IO fld #56
	  22,11,3,0,24,\       rem   IO fld #57
	  1,1,8,0,4,\	    rem   O fld #58
	  1,2,9,0,4,\	    rem   O fld #59
	  1,3,8,0,4,\	    rem   O fld #60
	  10,3,8,0,4,\	     rem   O fld #61
	  1,5,62,0,4,\	     rem   O fld #62
	  2,6,74,0,4,\	     rem   O fld #63
	  2,7,70,0,4,\	     rem   O fld #64
	  2,8,70,0,4,\	     rem   O fld #65
	  2,9,74,0,4,\	     rem   O fld #66
	  2,10,32,0,4,\       rem   O fld #67
	  38,10,38,0,4,\       rem   O fld #68
	  2,11,32,0,4,\       rem   O fld #69
	  38,11,38,0,4,\       rem   O fld #70
	  2,12,32,0,4,\       rem   O fld #71
	  38,12,18,0,4,\       rem   O fld #72
	  2,13,32,0,4,\       rem   O fld #73
	  38,13,36,0,4,\       rem   O fld #74
	  2,14,32,0,4,\       rem   O fld #75
	  38,14,36,0,4,\       rem   O fld #76
	  17,15,5,0,4,\       rem   O fld #77
	  38,15,34,0,4,\       rem   O fld #78
	  1,16,74,0,4,\       rem   O fld #79
	  1,17,73,0,4,\       rem   O fld #80
	  1,19,74,0,4,\       rem   O fld #81
	  1,20,74,0,4,\       rem   O fld #82
	  1,21,74,0,4,\       rem   O fld #83
	  1,22,74,0,4,\       rem   O fld #84
	  6,11,20,0,0
	  rem	O fld #85
crt.data$(62)="EMPL NO. [     ]    NAME                                   SSN"
crt.data$(63)="--------------------------------------------------------------------------"
crt.data$(64)="C O S T   D I S T R I B U T I O N   |    E X E M P T I O N S   F R O M"
crt.data$(65)="O F   E M P L O Y E E   G R O S S   |     T A X    W I T H O L D I N G"
crt.data$(66)="A N D   E M P L O Y E R   C O S T   |  FICA EXEMPT [ ]  FEDERAL EXEMPT [ ]"
crt.data$(67)="ACCOUNT [   ]  PERCENT  [      ]"
crt.data$(68)="|  FUTA EXEMPT [ ]  STATE   EXEMPT [ ]"
crt.data$(69)="ACCOUNT [   ]  PERCENT  [      ]"
crt.data$(70)="|  SUI  EXEMPT [ ]  LOCAL   EXEMPT [ ]"
crt.data$(71)="ACCOUNT [   ]  PERCENT  [      ]"
crt.data$(72)="|  SDI  EXEMPT [ ]"
crt.data$(73)="ACCOUNT [   ]  PERCENT  [      ]"
crt.data$(74)="|  ---------------------------------"
crt.data$(75)="ACCOUNT [   ]  PERCENT  [      ]"
crt.data$(76)="|  EXEMPTIONS FROM SYSTEM DEDUCTIONS"
crt.data$(77)="TOTAL"
crt.data$(78)="|     1[ ]  2[ ]  3[ ]  4[ ]  5[ ]"
crt.data$(79)="--------------------------------------------------------------------------"
crt.data$(80)="E M P L O Y E E   S P E C I F I C   D E D U C T I O N S / E A R N I N G S"
crt.data$(81)="USED  EARN/DED DESC   E/D ACCT. A/P   FACTOR   LIMITED    LIMIT   XCLD CAT"
crt.data$(82)="1[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"
crt.data$(83)="2[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"
crt.data$(84)="3[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"
crt.data$(85)="ACCOUNT NUMBER [   ]"

i%=1
while i%<=85
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(58)=len(co.name$)
crt.x%(58)=fn.center%(co.name$,crt.columns%-2)
crt.data$(58)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(59)=len(sys.name$)
crt.x%(59)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(59)=sys.name$
crt.data$(60)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(61)=len(fun.name$)
crt.x%(61)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(61)=fun.name$

rem---------------------------------------------------------
