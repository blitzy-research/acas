rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPY941B - 8/JAN/80

crt.field.count% = 82	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  34,3,7,2,20,\       rem   IO fld #1
	  34,4,7,2,20,\       rem   IO fld #2
	  34,5,7,2,20,\       rem   IO fld #3
	  34,6,7,2,20,\       rem   IO fld #4
	  34,8,7,2,20,\       rem   IO fld #5
	  34,9,7,2,20,\       rem   IO fld #6
	  34,10,7,2,20,\       rem   IO fld #7
	  34,11,7,2,20,\       rem   IO fld #8
	  34,13,7,2,20,\       rem   IO fld #9
	  34,14,7,2,20,\       rem   IO fld #10
	  34,15,7,2,20,\       rem   IO fld #11
	  34,16,7,2,20,\       rem   IO fld #12
	  50,3,8,0,29,\       rem   IO fld #13
	  50,4,8,0,29,\       rem   IO fld #14
	  50,5,8,0,29,\       rem   IO fld #15
	  50,6,8,0,29,\       rem   IO fld #16
	  50,8,8,0,29,\       rem   IO fld #17
	  50,9,8,0,29,\       rem   IO fld #18
	  50,10,8,0,29,\       rem   IO fld #19
	  50,11,8,0,29,\       rem   IO fld #20
	  50,13,8,0,29,\       rem   IO fld #21
	  50,14,8,0,29,\       rem   IO fld #22
	  50,15,8,0,29,\       rem   IO fld #23
	  50,16,8,0,29,\       rem   IO fld #24
	  62,3,7,2,28,\       rem   IO fld #25
	  62,4,7,2,28,\       rem   IO fld #26
	  62,5,7,2,28,\       rem   IO fld #27
	  62,6,7,2,28,\       rem   IO fld #28
	  62,8,7,2,28,\       rem   IO fld #29
	  62,9,7,2,28,\       rem   IO fld #30
	  62,10,7,2,28,\       rem   IO fld #31
	  62,11,7,2,28,\       rem   IO fld #32
	  62,13,7,2,28,\       rem   IO fld #33
	  62,14,7,2,28,\       rem   IO fld #34
	  62,15,7,2,28,\       rem   IO fld #35
	  62,16,7,2,28,\       rem   IO fld #36
	  34,7,7,2,20,\       rem   IO fld #37
	  50,7,8,0,29,\       rem   IO fld #38
	  62,7,7,2,28,\       rem   IO fld #39
	  34,12,7,2,20,\       rem   IO fld #40
	  50,12,8,0,29,\       rem   IO fld #41
	  62,12,7,2,28,\       rem   IO fld #42
	  34,17,7,2,20,\       rem   IO fld #43
	  50,17,8,0,29,\       rem   IO fld #44
	  62,17,7,2,28,\       rem   IO fld #45
	  34,18,7,2,20,\       rem   IO fld #46
	  62,18,7,2,28,\       rem   IO fld #47
	  18,1,8,0,5,\	     rem   IO fld #48
	  62,2,7,2,28,\       rem   IO fld #49
	  50,19,8,0,29,\       rem   IO fld #50
	  62,19,7,2,28,\       rem   IO fld #51
	  62,20,7,2,28,\       rem   IO fld #52
	  18,21,7,2,28,\       rem   IO fld #53
	  62,21,7,2,28,\       rem   IO fld #54
	  12,13,23,0,1,\       rem   IO fld #55
	  38,13,1,0,25,\       rem   IO fld #56
	  1,1,70,0,4,\	     rem   O fld #57
	  1,2,74,0,4,\	     rem   O fld #58
	  2,3,73,0,4,\	     rem   O fld #59
	  2,4,73,0,4,\	     rem   O fld #60
	  2,5,73,0,4,\	     rem   O fld #61
	  2,6,73,0,4,\	     rem   O fld #62
	  4,7,18,0,4,\	     rem   O fld #63
	  2,8,73,0,4,\	     rem   O fld #64
	  2,9,73,0,4,\	     rem   O fld #65
	  2,10,73,0,4,\       rem   O fld #66
	  2,11,73,0,4,\       rem   O fld #67
	  4,12,19,0,4,\       rem   O fld #68
	  2,13,73,0,4,\       rem   O fld #69
	  2,14,73,0,4,\       rem   O fld #70
	  2,15,73,0,4,\       rem   O fld #71
	  2,16,73,0,4,\       rem   O fld #72
	  4,17,18,0,4,\       rem   O fld #73
	  1,18,18,0,4,\       rem   O fld #74
	  1,19,74,0,4,\       rem   O fld #75
	  1,20,60,0,4,\       rem   O fld #76
	  1,21,60,0,4,\       rem   O fld #77
	  37,13,3,0,0,\       rem   O fld #78
	  3,1,8,0,0,\	    rem   O fld #79
	  3,2,9,0,0,\	    rem   O fld #80
	  3,3,8,0,0,\	    rem   O fld #81
	  12,3,8,0,0
	  rem	O fld #82
crt.data$(57)="DEPOSIT PER END                  LIABILITY         DATE         AMOUNT"
crt.data$(58)="OVERPAYMENT FROM PREVIOUS QUARTER...........................[            ]"
crt.data$(59)="FIRST   | DAYS 1 THROUGH 7                     [        ]  [            ]"
crt.data$(60)="MONTH   | DAYS 8 THROUGH 15                    [        ]  [            ]"
crt.data$(61)="OF      | DAYS 16 THROUGH 22                   [        ]  [            ]"
crt.data$(62)="QUARTER | DAYS 23 THROUGH END                  [        ]  [            ]"
crt.data$(63)="FIRST MONTH TOTAL:"
crt.data$(64)="SECOND  | DAYS 1 THROUGH 7                     [        ]  [            ]"
crt.data$(65)="MONTH   | DAYS 8 THROUGH 15                    [        ]  [            ]"
crt.data$(66)="OF      | DAYS 16 THROUGH 22                   [        ]  [            ]"
crt.data$(67)="QUARTER | DAYS 23 THROUGH END                  [        ]  [            ]"
crt.data$(68)="SECOND MONTH TOTAL:"
crt.data$(69)="THIRD   | DAYS 1 THROUGH 7                     [        ]  [            ]"
crt.data$(70)="MONTH   | DAYS 8 THROUGH 15                    [        ]  [            ]"
crt.data$(71)="OF      | DAYS 16 THROUGH 22                   [        ]  [            ]"
crt.data$(72)="QUARTER | DAYS 23 THROUGH END                  [        ]  [            ]"
crt.data$(73)="THIRD MONTH TOTAL:"
crt.data$(74)="TOTAL FOR QUARTER:"
crt.data$(75)="FINAL DEPOSIT FOR QUARTER:......................[        ]  [            ]"
crt.data$(76)="TOTAL DEPOSITS FOR QUARTER:................................."
crt.data$(77)="OVERPAYMENT:....                  UNDEPOSITED TAXES DUE:...."
crt.data$(78)="[ ]"

i%=1
while i%<=82
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(79)=len(co.name$)
crt.x%(79)=fn.center%(co.name$,crt.columns%-2)
crt.data$(79)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(80)=len(sys.name$)
crt.x%(80)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(80)=sys.name$
crt.data$(81)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(82)=len(fun.name$)
crt.x%(82)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(82)=fun.name$

rem---------------------------------------------------------
