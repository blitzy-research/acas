#include "ipycomm"
common print.name%	rem for 941 print 15/nov/79
common tot.subj.to.with
common prev.qtr.adj,end.of.qtr$
common adj.total.inc.tax.with
common fica.non.tip.tax
common fica.tips.tax,total.fica.tax
common fica.adj,adj.fica.tax
common total.taxes,net.taxes

prgname$="PRINT941 15  JAN., 1980 "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  P  R	I  N  T  9  4  1
rem
rem	  SECTION ONE
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PRINT941"
function.name$ = "FORM 941 PRINT"

#include "ipyconst"
#include "zdms"
#include "zdateio"
#include "zdmsconf"
#include "zfilconv"
#include "zstring"
#include "znumeric"
#include "zparse"
#include "zeditdte"
#include "zdateinc"
#include "zdspyorn"

dim emsg$(20)
emsg$(01)="PY601 SYSTEM HAS NOT ACHIEVED QUARTER-END STATUS"
emsg$(02)="PY602 PR2 FILE NOT FOUND"
emsg$(03)="PY603 COH FILE NOT FOUND"
emsg$(04)="PY604 UNABLE TO WRITE PR2 FILE"
emsg$(05)="PY605 'Y' OR 'N' ONLY"
emsg$(06)="PY606 NOT NUMERIC"
emsg$(07)="PY607 INVALID DATE"
emsg$(08)="PY608"
emsg$(09)="PY609"
emsg$(10)="PY610"
emsg$(11)="PY611"
emsg$(12)="PY612"
emsg$(13)="PY613"
emsg$(14)="PY614"
emsg$(15)="PY615"
emsg$(16)="PY616"
emsg$(17)="PY617"
emsg$(18)="PY618"
emsg$(19)="PY619"
emsg$(20)="PY620"

#include "fpy941a"

rem---------constants--------
null$ = ""
pw$ = null$	rem for future use
pm$ = null$
SECTION2$ = "PRNT941B"  rem name of second section
print.name% = false%

print using "&"; crt.clear$
gosub 10	rem set up file accessing
gosub 15	rem ok to run?
if not ok%  then gosub 5	rem see if they still wanna go
gosub 20	rem find & open pr2
if stopit%  then goto 999.1	rem abend
gosub 30	rem find & open coh
if stopit%  then \
	close pr2.file%  :\
	goto 999.1	rem abend
gosub 40	rem set up field equates


rem----------------------------------------------------
rem-------MAIN PROCESSING------------------------
gosub 90	rem do screen 1 calc's
gosub 500	rem display screen 1
gosub 100	rem get screen 1 data
rem------END OF MAIN PROCESSING-------------------
rem-----------------------------------------------------
trash% = fn.msg%("PROCEEDING TO SECOND SECTION")

chain fn.file.name.out$(SECTION2$,"",0,pw$,pm$) rem goto 2nd half

#include "zeoj"

rem-----------------------------------------------------
rem--------SUBROUTINES--------------------------------
rem-----set up routines-------
5	rem-----still want to run?-----
	if not fn.confirmed%  then \
		goto 999.2	rem prem. end
	trash% = fn.msg%(null$)
	ok% = true%
	end.of.qtr$ = "000000"
	return

10	rem----set up file accessing------
	pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
       coh.file.name$=fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pm$)
	return

15	rem-----ok to run?-----
	ok% = true%
	trash% = fn.decompose.date%(pr2.check.date$)
	yr$ = right$(blank$+str$(yr%),2)
	end.of.qtr$ = common.date$
	if pr2.last.q.ended% = 4  then	\
		end.of.qtr$ = yr$+"0331"
	if pr2.last.q.ended% = 1  then \
		end.of.qtr$ = yr$+"0630"
	if pr2.last.q.ended% = 2  then \
		end.of.qtr$ = yr$+"0930"
	if pr2.last.q.ended% = 3  then \
		end.of.qtr$ = yr$+"1231"
	return
REM========QTR END CHECKS NOT EXECUTED=================
	if pr1.m.used%	or  pr1.s.used%  then \
		gosub 16	rem check qtr end for mo & semimo
	if not ok%  then goto 15.9
	if pr1.b.used%	then \
		incr% = 14  :\
		gosub 17	rem check qtr end for biwk
	if not ok%  then goto 15.9
	if pr1.w.used%	then \
		incr% = 7   :\
		gosub 17	rem check qtr end for wk
15.9	if not ok%  then \
		trash% = fn.emsg%(1)
	return

16	rem-----check qtr end for mo & semimo----======NOT USED=========
	if pr2.last.sm.apply.no% <> 6  and \
	   pr2.last.sm.apply.no% <> 12 and \
	   pr2.last.sm.apply.no% <> 18 and \
	   pr2.last.sm.apply.no% <> 24	then \
		ok% = false%:RETURN
	if mo% < val(mid$(end.of.qtr$,3,2))  then \
		ok% = false%	rem make sure pyperend hasn't just been run
	return

17	rem-----check qtr end for biwk & wk----======NOT USED==============
	if fn.incr.date$(pr2.check.date$,incr%) <= end.of.qtr$ \
		then ok% = false%
	return

20	rem-----check on pr2-----
	if end #pr2.file%  then 29.9
	open pr2.file.name$  as pr2.file%
	close pr2.file%
	return

29.9	rem-----no pr2 file-----
	trash% = fn.emsg%(2)
	stopit% = true%
	return	rem  thud

30	rem-----check on coh & read-----
#include "ipydmcoh"

	if end #coh.file%  then 39.9
	open coh.file.name$  recl coh.len%  as coh.file%
	if end #coh.file%  then 39.99
	read #coh.file%;\
#include "ipycoh"
	close coh.file%
	return

39.9	rem-----no coh file------
	trash% =  fn.emsg%(3)
	stopit% = true%
	return		rem crash
39.99	rem-----eof on coh-------

	return

40	rem-----field equates for screens------
	fld.print.name%  = 10
	fld.prev.adj%	 = 14
	fld.adj.tax%	 = 15
	fld.fica.adj%	 = 21
	fld.adj.fica%	 = 22
	fld.total.taxes% = 23
	fld.eic%	 = 24
	fld.net%	 = 25
	return

90	rem-----do initial calculations-----
	rem-----and set defaults-------
	print.name% = true%
	prev.qtr.adj = 0.0
	fica.adj = 0.0

91	tot.subj.to.with = coh.qtd.income.taxable + coh.qtd.tips +\
		coh.qtd.other.taxable + coh.qtd.other.nontaxable
	adj.total.inc.tax.with = coh.qtd.fwt.liab + prev.qtr.adj
	fica.non.tip.tax = coh.qtd.fica.taxable*0.1226
	fica.tips.tax = coh.qtd.tips*0.0613
	total.fica.tax = fica.non.tip.tax + fica.tips.tax

92	adj.fica.tax = total.fica.tax + fica.adj
	total.taxes = adj.total.inc.tax.with + adj.fica.tax
	eic = - coh.qtd.eic.credit
	net.taxes = total.taxes + eic
	return

rem-------beginning of screen 1 driver---------
100	rem-----get data for screen 1------
110	rem-----print co name?-----
	field% = fld.print.name%
	bad.data% = true%
	gosub 120	rem get input
	if valid%   then gosub 130	rem check data & display
	if cr%	then goto 111		rem goto next field
	if back%  then goto 112 	rem wrap to last field
	if stopit%  then return
	if bad.data%  then goto 110	rem try it again

111	rem-----get prev. qtr. adj-----
	field% = fld.prev.adj%
	bad.data% = true%
	gosub 120		rem get input
	if valid%  then gosub 140	rem check data & display
	if stopit%  then return
	if cr%	then goto 112		rem goto next field
	if back%  then goto 110 	rem goto previous field
	if bad.data%  then goto 111	rem try again

112	rem-----get fica adjust-----
	field% = fld.fica.adj%
	bad.data% = true%
	gosub 120		rem get input
	if valid%  then gosub 150	rem check data & display
	if stopit%  then return
	if cr%	then goto 110		rem wrap to 1st field
	if back%  then goto 111 	rem prev field
	if bad.data%  then goto 112	rem try it again
	goto 110			rem from the top

rem------end of screen 1 driver-----------


120	rem------get data-------
	valid%	= false%
	stopit% = false%
	cr%	= false%
	back%	= false%
	trash%	= fn.get%(2,field%)  rem mask 2 accepts cr,back,esc ctl-chars
	if in.status% = req.valid%  then valid% = true%:return
	if in.status% = req.stopit%  then stopit% = true%:return
	if in.status% = req.cr%  then cr% = true%:return
	if in.status% = req.back%  then back% = true%
	return

130	rem-----check print.name------
	if in.uc$ = "Y"  then print.name% = true%:bad.data% = false%
	if in.uc$ = "N"  then print.name% = false%:bad.data% = false%
	if bad.data%  then  emsg% = 5:gosub 400 rem print emsg & delay
	trash% = fn.put%(fn.dsp.yorn$(print.name%),field%)
	return

140	rem------check prev.qtr.adj-----
	gosub 155	rem check neg amt & numeric
	if not numeric%  then \
		trash% = fn.put%(str$(prev.qtr.adj),field%) :\
		return	rem redisplay old data
	bad.data% = false%
	prev.qtr.adj = val(in$)
	gosub 91	rem recompute amounts
	gosub 521	rem re-display
	return

145	rem-----check numeric------
	numeric% = fn.numeric%(in$,7,2)
	if not numeric%  then \
		emsg% = 6  :\
		gosub 400	rem print emsg w/delay
	return

150	rem-----check fica.adj------
	gosub 155	rem check neg amt & numeric
	if not numeric%  then \
		trash% = fn.put%(str$(fica.adj),field%) :\
		return		rem redisplay old value
	bad.data% = false%
	fica.adj = val(in$)
	gosub 92	rem recompute amounts
	gosub 522	rem redisplay
	return

155	rem-----check neg amt--------
	neg$ = in$
	neg% = false%
	if val(in$) < 0  then \
		neg% = true% :\
		in$ = right$(in$,(len(in$)-1))
	gosub 145	rem check numeric
	if not numeric%  then return
	if neg%  then in$ = neg$
	return

rem---------end of screen 1 subroutines------------------------

400	rem-------display emsg & delay-------
	trash% = fn.emsg%(emsg%)
	for i% = 1 to 300
	next i%
	trash% = fn.msg%(null$)
	return

500	rem------get screen 1-------
	trash% = fn.put.all%(false%)	rem display literals
	gosub 520	rem display screen 1 data and load values
	return

520	rem-----display screen 1 data & load values-------
	trash% = fn.put%(pr1.co.name$,1)
	trash% = fn.put%(pr1.co.addr1$,2)
	trash% = fn.put%(fn.date.out$(end.of.qtr$),3)
	trash% = fn.put%(pr1.co.addr2$,4)
	trash% = fn.put%(pr1.fed.id$,5)
	trash% = fn.put%(pr1.co.addr3$,6)
	trash% = fn.put%(pr1.co.city$,7)
	trash% = fn.put%(pr1.co.state$,8)
	trash% = fn.put%(pr1.co.zip$,9)
	trash% = fn.put%(fn.dsp.yorn$(print.name%),10)
	trash% = fn.put%(str$(pr2.no.employees%),11)
	trash% = fn.put%(str$(tot.subj.to.with),12)
	trash% = fn.put%(str$(coh.qtd.fwt.liab),13)

521	trash% = fn.put%(str$(prev.qtr.adj),14)
	trash% = fn.put%(str$(adj.total.inc.tax.with),15)
	trash% = fn.put%(str$(coh.qtd.fica.taxable),16)
	trash% = fn.put%(str$(fica.non.tip.tax),17)
	trash% = fn.put%(str$(coh.qtd.tips),18)
	trash% = fn.put%(str$(fica.tips.tax),19)
	trash% = fn.put%(str$(total.fica.tax),20)

522	trash% = fn.put%(str$(fica.adj),21)
	trash% = fn.put%(str$(adj.fica.tax),22)
	trash% = fn.put%(str$(total.taxes),23)
	trash% = fn.put%(str$(eic),24)
	trash% = fn.put%(str$(net.taxes),25)
	return
