rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYDED3 - 20-NOV-79|5:30PM

crt.field.count% = 60	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  3,6,1,0,29,\	     rem   IO fld #1
	  6,6,15,0,29,\       rem   IO fld #2
	  24,6,1,0,29,\       rem   IO fld #3
	  28,6,3,0,28,\       rem   IO fld #4
	  34,6,1,0,29,\       rem   IO fld #5
	  38,6,6,2,28,\       rem   IO fld #6
	  51,6,1,0,29,\       rem   IO fld #7
	  55,6,7,2,28,\       rem   IO fld #8
	  69,6,1,0,28,\       rem   IO fld #9
	  72,6,2,0,28,\       rem   IO fld #10
	  3,7,1,0,29,\	     rem   IO fld #11
	  6,7,15,0,29,\       rem   IO fld #12
	  24,7,1,0,29,\       rem   IO fld #13
	  28,7,3,0,28,\       rem   IO fld #14
	  34,7,1,0,29,\       rem   IO fld #15
	  38,7,6,2,28,\       rem   IO fld #16
	  51,7,1,0,29,\       rem   IO fld #17
	  55,7,7,2,28,\       rem   IO fld #18
	  69,7,1,0,28,\       rem   IO fld #19
	  72,7,2,0,28,\       rem   IO fld #20
	  3,8,1,0,29,\	     rem   IO fld #21
	  6,8,15,0,29,\       rem   IO fld #22
	  24,8,1,0,29,\       rem   IO fld #23
	  28,8,3,0,28,\       rem   IO fld #24
	  34,8,1,0,29,\       rem   IO fld #25
	  38,8,6,2,28,\       rem   IO fld #26
	  51,8,1,0,29,\       rem   IO fld #27
	  55,8,7,2,28,\       rem   IO fld #28
	  69,8,1,0,28,\       rem   IO fld #29
	  72,8,2,0,28,\       rem   IO fld #30
	  3,9,1,0,29,\	     rem   IO fld #31
	  6,9,15,0,29,\       rem   IO fld #32
	  24,9,1,0,29,\       rem   IO fld #33
	  28,9,3,0,28,\       rem   IO fld #34
	  34,9,1,0,29,\       rem   IO fld #35
	  38,9,6,2,28,\       rem   IO fld #36
	  51,9,1,0,29,\       rem   IO fld #37
	  55,9,7,2,28,\       rem   IO fld #38
	  69,9,1,0,28,\       rem   IO fld #39
	  72,9,2,0,28,\       rem   IO fld #40
	  3,10,1,0,29,\       rem   IO fld #41
	  6,10,15,0,29,\       rem   IO fld #42
	  24,10,1,0,29,\       rem   IO fld #43
	  28,10,3,0,28,\       rem   IO fld #44
	  34,10,1,0,29,\       rem   IO fld #45
	  38,10,6,2,28,\       rem   IO fld #46
	  51,10,1,0,29,\       rem   IO fld #47
	  55,10,7,2,28,\       rem   IO fld #48
	  69,10,1,0,28,\       rem   IO fld #49
	  72,10,2,0,28,\       rem   IO fld #50
	  1,1,8,0,4,\	    rem   O fld #51
	  1,2,9,0,4,\	    rem   O fld #52
	  1,3,8,0,4,\	    rem   O fld #53
	  10,3,8,0,4,\	     rem   O fld #54
	  1,5,74,0,4,\	     rem   O fld #55
	  1,6,74,0,4,\	     rem   O fld #56
	  1,7,74,0,4,\	     rem   O fld #57
	  1,8,74,0,4,\	     rem   O fld #58
	  1,9,74,0,4,\	     rem   O fld #59
	  1,10,74,0,4
	  rem	O fld #60
crt.data$(55)="USED  EARN/DED DESC   E/D ACCT. A/P   FACTOR   LIMITED   LIMIT    XLCD CAT"
crt.data$(56)="1[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"
crt.data$(57)="2[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"
crt.data$(58)="3[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"
crt.data$(59)="4[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"
crt.data$(60)="5[ ][               ] [ ] [   ] [ ] [          ] [ ] [            ][ ][  ]"

i%=1
while i%<=60
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(51)=len(co.name$)
crt.x%(51)=fn.center%(co.name$,crt.columns%-2)
crt.data$(51)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(52)=len(sys.name$)
crt.x%(52)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(52)=sys.name$
crt.data$(53)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(54)=len(fun.name$)
crt.x%(54)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(54)=fun.name$

rem---------------------------------------------------------
