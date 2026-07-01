#include "ipycomm"
prgname$="PRINT940  17 JANUARY, 1980 "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  P  R	I  N  T  9  4  0
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PRINT940"
function.name$ = "FORM 940 PRINT"

#include "ipyconst"
#include "zdms"
#include "zdmsconf"
#include "zdmsabrt"
#include "zfilconv"
#include "znumber"
#include "zparse"
#include "zeditdte"
#include "zdateio"
#include "zdateinc"
#include "zstring"
#include "zheading"

dim emsg$(10)		REM CAN GO TO 20
emsg$(01)="PY581 PR2 FILE NOT FOUND"
emsg$(02)="PY582 COH FILE NOT FOUND"
emsg$(03)="PY583 DED FILE NOT FOUND"
emsg$(04)="PY584 SYSTEM HAS NOT ACHIEVED YEAR-END STATUS"
emsg$(05)="PY585 UNABLE TO WRITE TO PR2"
emsg$(06)="PY586 HIS FILE NOT FOUND"
emsg$(07)="PY587 UNEXPECTED EOF ON HIS FILE"
emsg$(08)="PY588 RETURN OR ESCAPE ONLY"
emsg$(09)="PY589"
emsg$(10)="PY590"

#include "fpy940"


print using "&"; crt.clear$     rem clear screen
for i% = 3 to 6
	trash% = fn.lit%(i%)
next i% 	rem display header

rem-------------constants---------------
pm$ = null$
pw$ = null$

gosub 5 	rem ok to run?--prem end if no
gosub 10	rem set up file accessing
gosub 20	rem get pr2
if stopit%  then goto 999.1	rem abend
gosub 30	rem get coh
if stopit%  then goto 999.1	rem abend
gosub 40	rem get ded
if stopit%  then goto 999.1	rem abend
gosub 50	rem get his
if stopit%  then goto 999.1	rem abend

REM---------------------------------------------
REM-----THIS HERE'S THE GIANT DRIVER-----------
gosub 100	rem do calculations
gosub 200	rem print
if yearend%  then \
	gosub 300	rem write pr2

REM-----EOJ---------------------
#include "zeoj"

REM---------------------------------------------------------------
REM---------SUBROUTINES-------------------------------------------

5	rem-----ok to run?-----
	yearend% = true%
	trash% = fn.decompose.date%(pr2.check.date$)
	yr$ = right$(blank$+str$(yr%),2)
	if pr2.last.q.ended% = 4  then	\
		end.of.qtr$ = yr$+"0331" \
	   else \
		end.of.qtr$ = common.date$
	return
REM=======YEAR END CHECKS NOT EXECUTED====================
	if pr1.m.used%	or  pr1.s.used%  then \
		gosub 16	rem check qtr end for mo & semimo
	if not yearend%  then goto 5.9
	if pr1.b.used%	then \
		incr% = 14  :\
		gosub 17	rem check qtr end for biwk
	if not yearend%  then goto 5.9
	if pr1.w.used%	then \
		incr% = 7   :\
		gosub 17	rem check qtr end for wk
5.9	if not yearend%  then \
		trash% = fn.emsg%(4) :\
		gosub 18	rem get confirmation to run
	return

16	rem-----check yr end for mo & semimo--=====NOT USED=======
	if pr2.last.sm.apply.no% <> 24	then \
		yearend% = false%
	return

17	rem-----check yr end for biwk & wk---======NOT USED=======
	if fn.incr.date$(pr2.check.date$,incr%) <= end.of.qtr$ \
		then yearend% = false%
	return

18	rem-----still want to run?-----
	if not fn.confirmed%  then \
		goto 999.2	rem prem. end
	trash% = fn.msg%(null$)
	return

REM---------------------------------------------------
REM----------file handling routines-----------------

10	rem-----set up file accessing-----
	pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pm$,pw$)
       coh.file.name$=fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pm$,pw$)
       ded.file.name$=fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pm$,pw$)
       his.file.name$=fn.file.name.out$(his.name$,"101",pr1.his.drive%,pm$,pw$)
       return

20	rem-----check on pr2-----
	if end #pr2.file%  then 29.9
	open pr2.file.name$  as pr2.file%
	close pr2.file%
	return

29.9	rem-----no pr2 file-----
	trash% = fn.emsg%(1)
	stopit% = true%
	return	rem  thud

30	rem-----check on coh & read-----
#include "ipydmcoh"

	if end #coh.file%  then 39.9
	open coh.file.name$  as coh.file%
	if end #coh.file%  then 39.99
	read #coh.file%;\
#include "ipycoh"
	close coh.file%
	return

39.9	rem-----no coh file------
	trash% =  fn.emsg%(2)
	stopit% = true%
	return		rem crash
39.99	rem-----eof on coh-------

	return

40	rem-----check on ded & read-----
#include "ipydmded"

	if end #ded.file%  then 49.9
	open ded.file.name$   as ded.file%
	if end #ded.file%  then 49.99
	read #ded.file%;\
#include "ipyded"
	close ded.file%
	return

49.9	rem-----no ded file------
	trash% =  fn.emsg%(3)
	stopit% = true%
	return		rem crash
49.99	rem-----eof on ded-------

	return

50	rem-----open his file & read hdr-----
	if end #his.file%  then 59.9
	open his.file.name$  recl his.len%  as his.file%
	if end #his.file%  then 59.99
#include "ipydmhis"

	read #his.file%,1;\
#include "ipyhishd"

	return

55	rem-----read his record-----
	read #his.file%,his.rec%+1;\	rem account for hdr
#include "ipyhis"

	return

59.9	rem-----no his file------
	trash% = fn.emsg%(6)
	stopit% = true%
	return

59.99	rem-----unexpected eof on his-------
	console
	trash% = fn.emsg%(7)
	goto 999.1	rem abend

100	rem------do calculations------
	gosub 150	rem read his file & accumulate
	trash% = fn.put%(null$,2)
	trash% = fn.put%("DOING CALCULATIONS",1)
	for i% = 1 to 400
	next i% 	rem keep msg flying
	exempt = over.6k + coh.ytd.other.nontaxable
	rate$ = str$(ded.co.sui.rate)+"%"
	max.rate$ = str$(ded.co.futa.max.credit)+"%"
	ded.co.futa.rate = ded.co.futa.rate*.01    rem into decimal fraction
	ded.co.futa.max.credit = ded.co.futa.max.credit*.01
	ded.co.sui.rate = ded.co.sui.rate*.01
	gross.pay = coh.ytd.income.taxable + coh.ytd.other.taxable+coh.ytd.tips
	contrib.at.2.7 = gross.pay*ded.co.futa.max.credit
	contrib.at.rate = gross.pay*ded.co.sui.rate
	addl.credits = contrib.at.2.7 - contrib.at.rate
	if addl.credits < 0.0  then \
		addl.credits = 0.0
	actual.contrib = contrib.at.rate  REM should equal coh.ytd.co.sui.liab
	tot.tent.cred = addl.credits + actual.contrib
	tot.taxable.futa = tot.remun.paid - exempt
	gross.fed.tax = tot.taxable.futa*ded.co.futa.rate
	maximum.cred = tot.taxable.futa*ded.co.futa.max.credit
	if tot.tent.cred < maximum.cred  then \
		smaller = tot.tent.cred \
	   else \
		smaller = maximum.cred
	if pr1.co.state$ <> null$  then state$ = ucase$(pr1.co.state$)
	if state$ = "RI"  then \
		ri.tax = tot.taxable.futa :\
		ri.cred = ri.tax*.003  \
	   else \
		ri.tax = 0.0:ri.cred = 0.0
	cred.allowable = smaller - ri.cred
	net.fed.tax = gross.fed.tax - cred.allowable
	tot.deposited = 0.0
	for i% = 1 to 4
		tot.deposited = tot.deposited + coh.q.co.futa.liab(i%)
	next i%
	balance.due = net.fed.tax - tot.deposited
	if balance.due < 0  then \
		overpay = -balance.due :\
		balance.due = 0.0	\
	   else \
		overpay = 0.0
	return

150	rem-----read his & accumulate-----
	tot.remun.paid = 0.0
	over.6k = 0.0
	his.rec% = 1
	trash% = fn.put%("READING EMPLOYEE HISTORY RECORD NUMBER:",1)
	while his.rec% <= pr2.no.employees%
		gosub 55	rem read his file
		trash% = fn.put%(his.emp.no$,2)
		pay = his.ytd.income.taxable + his.ytd.other.taxable + \
		      his.ytd.other.nontaxable + his.ytd.tips
		tot.remun.paid = tot.remun.paid + pay
		if pay > ded.co.futa.limit  then \
			over.6k = over.6k + pay - ded.co.futa.limit
		his.rec% = his.rec% + 1
	wend
	close his.file%
	return

200	rem-----print-------
	amt$ = "#,###,###.## "
	a$ = "& "
	line$ = a$+amt$
	form1$ = a$+a$+amt$+a$+a$+a$+amt$+amt$+amt$+amt$
	yr$ = right$("0"+str$(pr2.year%),2)
	gosub 205	rem do printer msg
	lprinter
	trash% = fn.hdr%(function.name$)
	print:print
	print tab(25); pr1.co.name$
	print tab(25); pr1.co.addr1$
	print tab(25); pr1.co.addr2$
	print tab(25); pr1.co.addr3$; tab(70); pr1.fed.id$
	print tab(25); pr1.co.city$; tab(60);pr1.co.state$;tab(63); pr1.co.zip$
	gosub 400	  rem check abort
	print:print
	print tab(6);"1          2             3                 4        " +\
		"      5           6              7             8              9"
	print tab(14);"STATE ID      TAXABLE       EXPERIENCE RATE  EXPERI"+\
	      "ENCE CONTRIBUTIONS  CONTRIBUTIONS   ADDITIONAL    CONTRIBUTIONS"
	PRINT TAB(4);"STATE      NUMBER       PAYROLL        FROM       TO  "+\
		"    RATE       AT "+max.rate$+"     AT REAL RATE    " +\
		" CREDITS       TO STATE"
	print
	print using form1$; tab(5); pr1.co.state$; tab(9); pr1.state.id$; \
		tab(25); gross.pay; tab(40); "01/01/"+yr$; tab(50); \
		"12/31/"+yr$; tab(62);  rate$; tab(70); contrib.at.2.7; \
		tab(85); contrib.at.rate; tab(100); addl.credits; tab(115); \
		actual.contrib

	gosub 400		rem check abort
	print:print
	print using line$+amt$+amt$; tab(11); "TOTALS:"; tab(25); gross.pay; \
		tab(100); addl.credits; tab(115); actual.contrib
	print
	print using line$; tab(55); "10 TOTAL TENTATIVE CREDIT (COLUMN 8 "+\
		"PLUS COLUMN 9):"; TAB(115); tot.tent.cred
	print using line$; tab(55); "11 TOTAL REMUNERATION:"; tab(115); \
		tot.remun.paid
	gosub 400	rem check abort
	print:print
	print using line$; tab(25); "14b TOTAL EXEMPT REMUNERATION:"; tab(90);\
		exempt
	print using line$; tab(25); "15c TOTAL TAXABLE FUTA WAGES (SUBTRACT "+\
		"14b FROM LINE 11):"; tab(115); tot.taxable.futa
	print using line$; tab(25); "16 GROSS FEDERAL TAX (15c x .034):"; \
		tab(115); gross.fed.tax
	print using line$; tab(25); "17 MAXIMUM CREDIT (15c x .027):"; \
		tab(90); maximum.cred
	print using line$; tab(25); "18 SMALLER OF LINES 10 AND 17):"; \
		tab(90); smaller
	print using line$+line$; tab(25); "19 RHODE ISLAND PORTION OF 15c:"; \
		tab(63); ri.tax; tab(79); "x .003 ="; tab(90); ri.cred
	print using line$; tab(25); "20 CREDIT ALLOWABLE (SUBTRACT LINE 19 "+\
		"FROM LINE 18):"; tab(115); cred.allowable
	print using line$; tab(25); "21 NET FEDERAL TAX (SUBTRACT LINE 20 "+ \
		"FROM LINE 16):"; TAB(115); net.fed.tax
	gosub 400	rem check abort
	print:print
	print tab(25); "FEDERAL TAX DEPOSITS"
	print tab(15); "QUARTER     LIABILITY     DATE OF     AMOUNT OF"
	print tab(27); "BY PERIOD     DEPOSIT      DEPOSIT"
	print using line$+line$;tab(17);"FIRST";tab(25);coh.q.co.futa.liab(1);\
		tab(40); "03/31/"+yr$; tab(51); coh.q.co.futa.liab(1)
	print using line$+line$;tab(16);"SECOND";tab(25);coh.q.co.futa.liab(2);\
		tab(40); "06/30/"+yr$; tab(51); coh.q.co.futa.liab(2)
	print using line$+line$;tab(17);"THIRD";tab(25);coh.q.co.futa.liab(3);\
		tab(40); "09/30/"+yr$; tab(51); coh.q.co.futa.liab(3)
	print using line$+line$;tab(16);"FOURTH";tab(25);coh.q.co.futa.liab(4);\
		tab(40); "12/31/"+yr$; tab(51); coh.q.co.futa.liab(4)
	gosub 400	rem check abort
	print
	print using line$; tab(25); "22 TOTAL FEDERAL TAXES DEPOSITED:"; \
		TAB(115); tot.deposited
	print using line$; tab(25); "23 BALANCE DUE (SUBTRACT LINE 22 FROM "+\
		"LINE 21):"; tab(115); balance.due
	print using line$; tab(25); "24 OVERPAYMENT (SUBTRACT LINE 21 FROM "+\
		"LINE 22):"; tab(115); overpay
	print:print:print
	console
	return

205	rem-----do printer msg-----
	trash% = fn.put%("WHEN PRINTER IS READY, HIT RETURN",1)
206	trash% = fn.get%(2,2)
	if in.status% = req.stopit%  then \
		gosub 410	rem print msg & stop
	if in.status% = req.valid%  or \
	   in.status% = req.back%  then \
		trash% = fn.emsg%(8) :\
		for i% = 1 to 300	:\
		next i% 		:\  rem keep msg up for a bit
		trash% = fn.msg%(null$) :\
		goto 206
	return

300	rem-----write pr2-------
	open pr2.file.name$ as pr2.file%
	if end #pr2.file%  then 300.9
	pr2.940.printed% = true%
	print #pr2.file%;\
#include "ipypr2"

	return

300.9	rem----unable to write pr2-----
	trash% = fn.emsg%(5)
	goto 999.1	rem abend
	return

400	rem------check abort----------
	if fn.abort%  then \
		gosub 410	rem print msg & stop
	return

410	rem-----print msg & stop------
	trash% = fn.msg%("STOP REQUESTED")
	goto 999.2	rem prem end
	return
end
