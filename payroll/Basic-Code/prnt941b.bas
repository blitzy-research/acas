#include "ipycomm"
common print.name%	rem for 941 print 15/nov/79
common tot.subj.to.with
common prev.qtr.adj,end.of.qtr$
common adj.total.inc.tax.with
common fica.non.tip.tax
common fica.tips.tax,total.fica.tax
common fica.adj,adj.fica.tax
common total.taxes,net.taxes

prgname$="PRNT941B  15 JAN., 1980 "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  P  R	I  N  T  9  4  1
rem
rem	   SECTION 2
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PRNT941B"
function.name$ = "FORM 941 PRINT"

#include "ipyconst"

#include "zdms"
#include "zdmsused"
#include "zdateio"
#include "zdmsconf"
#include "zdmsabrt"
#include "zfilconv"
#include "zstring"
#include "znumeric"
#include "zparse"
#include "zeditdte"
#include "zdspyorn"
#include "zbracket"

dim emsg$(14)
emsg$(01)="PY601 SYSTEM HAS NOT ACHIEVED QUARTER-END STATUS"
emsg$(02)="PY602 PR2 FILE NOT FOUND"
emsg$(03)="PY603 COH FILE NOT FOUND"
emsg$(04)="PY604 UNABLE TO WRITE PR2 FILE"
emsg$(05)="PY605 'Y' OR 'N' ONLY"
emsg$(06)="PY606 NOT NUMERIC"
emsg$(07)="PY607 INVALID DATE"
emsg$(08)="PY608"
emsg$(09)="PY609 INVALID RESPONSE"
emsg$(10)="PY610 PR2 FILE NOT FOUND--SECTION TWO"
emsg$(11)="PY611 UNABLE TO WRITE PR2--SECTION TWO"
emsg$(12)="PY612 COH FILE NOT FOUND--SECTION TWO"
emsg$(13)="PY613"

#include "fpy941b"

rem---------constants--------
null$ = ""
pw$ = null$	rem for future use
pm$ = null$
function.name$ = "FORM 941 PRINT"

print using "&"; crt.clear$
gosub 10	rem set up file accessing
gosub 20	rem find & open pr2
if stopit%  then goto 999.1	rem abend
gosub 30	rem find & open coh
if stopit%  then \
	close pr2.file%  :\
	goto 999.1	rem abend
gosub 40	rem set up field equates


rem----------------------------------------------------
rem-------MAIN PROCESSING------------------------
gosub 100	rem do calculations
gosub 550	rem display screen 2
gosub 210	rem get screen 2 data
trash% = fn.msg%("PROCEEDING TO PRINT SECTION")
for i% = 1 to 400
next i% 	rem keep msg flying
gosub 300	rem print form
rem------END OF MAIN PROCESSING-------------------
rem-----------------------------------------------------

if end.of.qtr$ <> "000000"  then \
	gosub 25	rem rewrite pr2
close pr2.file%


#include "zeoj"

rem-----------------------------------------------------
rem--------SUBROUTINES--------------------------------
rem-----set up routines-------
10	rem----set up file accessing------
	pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
       coh.file.name$=fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pm$)
	return

20	rem-----check on pr2-----
	if end #pr2.file%  then 29.9
	open pr2.file.name$  as pr2.file%
	if end #pr2.file%  then 29.99
	return

25	rem-----write new pr2----
	pr2.941.printed% = true%
	print #pr2.file%;\
#include "ipypr2"
	return

29.9	rem-----no pr2 file-----
	trash% = fn.emsg%(10)
	stopit% = true%
	return	rem  thud
29.99	rem-----unable to write pr2-----
	pr2.941.printed% = false%
	trash% =  fn.emsg%(11)
	goto 999.1	rem abend
	return

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
	trash% =  fn.emsg%(12)
	stopit% = true%
	return		rem crash
39.99	rem-----eof on coh-------

	return

40	rem-----field equates for screens------
	fld.overpay%	 = 49
	fld.real.tot%	 = 47
	fld.final.date%  = 50
	fld.final.dep%	 = 51
	fld.final.total% = 52
	fld.first.mo%	 = 39
	fld.second.mo%	 = 42
	fld.third.mo%	 = 45
	fld.new.overpay% = 53
	fld.taxes.due%	 = 54
	fld.prompt%	 = 55
	fld.prompt.resp% = 56
	start.lit%	 = 55
	end.lit%	 = 77
	return

100	rem----calc's for 2nd screen-----
	overpay = 0.0
	for i% = 1 to 3
		sum.amt = 0.0
		k% = (i% - 1)*4
		for j% = 1 to 4
			sum.amt = sum.amt + coh.tax(j% + k%)
		next j%
		if i% = 1  then \
			first.mo = sum.amt :\
			real.first.mo = sum.amt
		if i% = 2  then \
			second.mo = sum.amt :\
			real.second.mo = sum.amt
		if i% = 3  then \
			third.mo = sum.amt :\
			real.third.mo = sum.amt
	next i%
	dim real.coh.tax(12)
	for i% = 1 to 12
		real.coh.tax(i%) = coh.tax(i%)
		if coh.date$(i%) = "000000"  then \
		   coh.date$(i%) = null$
	next i%
	j% = 0
	gosub 105	rem get wk no
	first.mo$ = coh.date$(wk.no%)
	j% = 4
	gosub 105	rem get wk no
	second.mo$ = coh.date$(wk.no%)
	j% = 8
	gosub 105	rem get wk no
	third.mo$ = coh.date$(wk.no%)

	total.for.qtr = first.mo+second.mo+third.mo
	real.total.for.qtr = real.first.mo+real.second.mo+real.third.mo
	final.dep.date$ = null$
	final.deposit = 0.0
	grand.total.for.qtr = real.total.for.qtr + final.deposit
	gosub 110	rem calculate over/due charges
	return

105	rem-----get wk no-------
	k% = 4
	while k% > 0
		wk.no% = j% + k%
		if coh.date$(wk.no%) <> null$  then return
		k% = k% - 1
	wend
	return

110	rem-----calculate over/due taxes-----
	taxes.due = net.taxes - grand.total.for.qtr
	new.overpay = grand.total.for.qtr - net.taxes
	if taxes.due < 0.0  then taxes.due = 0.0
	if new.overpay < 0.0  then new.overpay = 0.0
	return

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

145	rem-----check numeric------
	numeric% = fn.numeric%(in$,7,2)
	if not numeric%  then \
		emsg% = 6  :\
		gosub 400	rem print emsg w/delay
	return
rem---------end of screen 1 subroutines------------------------

rem-----beginning of screen 2 driver----------
210	rem-----get data for screen 2------
	field% = fld.overpay%
	bad.data% = true%
	gosub 120	rem get data
	if valid%  then gosub 240	rem check overpay
	if stopit%  then return
	if cr%	then goto 220		rem 1st field of first mo.
	if back%  then goto 235 	rem jump around table
	if bad.data%  then goto 210	rem try this one again

220	rem----get table data----
	coh.tab% = 1
	while coh.tab% <=12
		field% = coh.tab% + 12		rem date column
		date% = true%
		bad.data% = true%
221		gosub 120		rem get data
		if valid%   then gosub 260	rem check date & display
		if stopit%  then return
		if back% or cr%  then gosub 250 rem check table co-ords
		if back%  then goto 222 	rem amt field of prev wk
		if bad.data%  then goto 221	rem try this one again

222		field% = coh.tab% + 24		rem amt column
		date% = false%
		bad.data% = true%
223		gosub 120		rem get data
		if valid%  then gosub 270	rem check amt & display
		if stopit%  then return
		if back% or cr%  then gosub 250 rem check table co-ords
		if back%  then goto 221 	rem date field of same wk
		if bad.data%  then goto 223	rem try this one again

		coh.tab% = coh.tab% + 1 	rem move to next wk
	wend

230	rem---get final date & final amt-----
	field% = fld.final.date%
	bad.data% = true%
231	gosub 120		rem get data
	if valid%  then gosub 260	rem check date & display
	if stopit%  then return
	if cr%	then goto 235		rem final amt
	if back%  then \
		field% = 36  :\
		coh.tab% = 12  :\
		goto 223		rem amt field, last wk
	if bad.data%  then goto 231

235	rem----final amt-------
	bad.data% = true%
	field% = fld.final.dep%
236	gosub 120	rem get data
	if valid%  then gosub 280	rem check amt & display
	if stopit%  then return
	if cr%	then goto 210		rem to overpay fld
	if back%  then goto 230 	rem to final date
	if bad.data%  then goto 236	rem try this one again
	goto 210			rem back to top of screen

rem------end of screen 2 driver---------------

240	rem-----check overpayment-------
	gosub 145	rem check numeric
	if not numeric%  then \
		trash% = fn.put%(str$(overpay),field%) :\
		return
	bad.data% = false%
	overpay = val(in$)
	start% = 1
	end% = 12
	gosub 275	rem add weekly amts
	real.total.for.qtr = amt + overpay
	grand.total.for.qtr = real.total.for.qtr + final.deposit
	gosub 110	rem figure taxes due/over
	trash% = fn.put%(in$,field%)
	trash% = fn.put%(str$(real.total.for.qtr),fld.real.tot%)
	gosub 245	rem display other changed fields
	return

245	rem-----display other changes fields-----
	trash% = fn.put%(str$(grand.total.for.qtr),fld.final.total%)
	trash% = fn.put%(str$(taxes.due),fld.taxes.due%)
	trash% = fn.put%(str$(new.overpay),fld.new.overpay%)
	return

250	rem------check table co-ords for back%-----
	if cr%	then bad.data% = false% 	rem allow to fall through
	if back% and date%  then \
		coh.tab% = coh.tab% - 1 :\	rem decrement wk if in date fld
		field% = field% + 11	:\
		date% = false%
	if back% and not date%	then \
		field% = field% - 12	:\	rem decrement fld if in amt fld
		date% = true%
	if field% < 13 or coh.tab% < 1	then \
		goto 210		rem out of table & to top of screen
	return

260	rem-----check date--------
	invalid% = false%
	if not fn.edit.date%(in$)  then \
		gosub 265 \	rem check funny date
	   else \
		date$ = fn.date.in$
	if invalid%  then \
		trash% = fn.put%(crt.data$(field%),field%) :\
		return
	bad.data% = false%
	trash% = fn.put%(fn.date.out$(date$),field%)
	if field% = 16	then \
		trash% = fn.put%(fn.date.out$(date$),38) rem 1st mo
	if field% = 20	then \
		trash% = fn.put%(fn.date.out$(date$),41)  rem 2nd mo
	if field% = 24	then \
		trash% = fn.put%(fn.date.out$(date$),44)  rem 3rd mo
	return

265	rem------check funny date------
	if in$ = null$	or \
	   in.uc$ = "NONE"  then \
		in$ = null$ :\
		date$ = null$ :\
		return
	emsg% = 7
	gosub 400	rem display emsg & delay
	invalid% = true%
	return

270	rem------check amts--------
	gosub 145	rem check numeric
	if not numeric%  then \
		trash% = fn.put%(str$(real.coh.tax(coh.tab%)),field%) :\
		return
	bad.data% = false%
	real.coh.tax(coh.tab%) = val(in$)
	if coh.tab% < 5  then \ 	rem first mo
		start% = 1	 :\
		end% = 4	 :\
		gosub 275	 :\  rem add weeks
		mo.field% = fld.first.mo%  :\
		mo.amt = amt
	if coh.tab% > 4  and coh.tab% < 9  then \
		start% = 5	 :\
		end% = 8	 :\
		gosub 275	 :\  rem add weeks
		mo.field% = fld.second.mo%  :\
		mo.amt = amt
	if coh.tab% > 8  then \
		start% = 9	:\
		end%   = 12	:\
		gosub 275	:\  rem add weeks
		mo.field% = fld.third.mo%  :\
		mo.amt = amt
	start% = 1
	end% = 12
	gosub 275	rem add weeks
	real.total.for.qtr = amt + overpay
	grand.total.for.qtr = real.total.for.qtr + final.deposit
	gosub 110	rem figure taxes due/over
	trash% = fn.put%(in$,field%)
	trash% = fn.put%(str$(mo.amt),mo.field%)
	trash% = fn.put%(str$(real.total.for.qtr),fld.real.tot%)
	gosub 245	rem display other fields
	return

275	rem-----add weekly amts-------
	amt = 0.0
	for i% = start% to end%
		amt = amt + real.coh.tax(i%)
	next i%
	return

280	rem-----check final dep & display--------
	gosub 145	rem check numeric
	if not numeric%  then \
		trash% = fn.put%(str$(final.deposit),fld.final.dep%) :\
		return
	bad.data% = false%
	final.deposit = val(in$)
	grand.total.for.qtr = real.total.for.qtr + final.deposit
	gosub 110	rem figure new.over/due taxes
	trash% = fn.put%(in$,field%)
	gosub 245	rem display other fields
	return
rem-------end of screen 2 subroutines--------------------------


300	rem-----print form-------------------
	print using "&"; crt.clear$
	gosub 310	rem set used flags
	disp% = 0	rem displacement from left edge
	amt$ = "#,###,###.## "
	amt.tab% = disp% + 69
	brkt.tab% = amt.tab% -1
	names% = disp% + 16
	col1% = disp% + 34
	col2% = disp% + 46
	col3% = disp% + 56
	table$ = amt$ +"&" +amt$
	again% = true%
   while again%
	gosub 350	rem test alignment?
	print:print
	if print.name%	then \
		print using "&";tab(names%);left$(pr1.co.name$+blank$,43) :\
		print using "&&";tab(names%);pr1.co.addr1$;tab(disp%+50);\
		  fn.date.out$(end.of.qtr$) :\
		print using "&&";tab(names%);pr1.co.addr2$;tab(disp%+58);\
		  pr1.fed.id$  :\
		print using "&";tab(names%);pr1.co.addr3$  :\
		print using "&&&";tab(names%);pr1.co.city$;tab(disp%+41);\
		    pr1.co.state$;tab(disp%+45);pr1.co.zip$  \
	  else \
		print:print:print:print:print
	print:print:print
	print using "##,###"; tab(disp%+72);pr2.no.active.emps%
	print
	print using amt$;tab(amt.tab%);tot.subj.to.with
	print using amt$;tab(amt.tab%);coh.qtd.fwt.liab
	print using fn.bracket$(prev.qtr.adj,7,true%);tab(brkt.tab%);\
		abs(prev.qtr.adj)
	print using amt$;tab(amt.tab%);adj.total.inc.tax.with
	print using amt$+amt$;tab(disp%+37);coh.qtd.fica.taxable;\
		tab(brkt.tab%);fica.non.tip.tax
	print using amt$+amt$;tab(disp%+37);coh.qtd.tips;\
		tab(brkt.tab%);fica.tips.tax
	print using amt$;tab(amt.tab%);total.fica.tax
	print using fn.bracket$(fica.adj,7,true%);tab(brkt.tab%);abs(fica.adj)
	print using amt$;tab(amt.tab%);adj.fica.tax
	print using amt$;tab(amt.tab%);total.taxes
	print using fn.bracket$(-coh.qtd.eic.credit,7,true%);tab(brkt.tab%);\
		coh.qtd.eic.credit
	print using amt$;tab(amt.tab%);net.taxes
	if fn.abort%  then gosub 390	rem abort printout
	rem-----print screen 2 info-------
	print using "&";tab(disp%+20);fn.date.out$(end.of.qtr$)
	print using amt$; tab(col3%);overpay

	for i% = 1 to 4
		print using table$;tab(col1%);coh.tax(i%);tab(col2%);\
		    crt.data$(i%+12);tab(col3%);real.coh.tax(i%)
	next i%
	print using table$;tab(col1%);first.mo;tab(col2%);crt.data$(38);\
		tab(col3%);real.first.mo

	for i% = 5 to 8
		print using table$;tab(col1%);coh.tax(i%);tab(col2%);\
		    crt.data$(i%+12);tab(col3%);real.coh.tax(i%)
	next i%
	print using table$;tab(col1%);second.mo;tab(col2%);crt.data$(41);\
		tab(col3%);real.second.mo

	for i% = 9 to 12
		print using table$;tab(col1%);coh.tax(i%);tab(col2%);\
		    crt.data$(i%+12);tab(col3%);real.coh.tax(i%)
	next i%
	print using table$;tab(col1%);third.mo;tab(col2%);crt.data$(44);\
		tab(col3%);real.third.mo

	print using amt$+amt$;tab(col1%);total.for.qtr;tab(col3%-1);\
		real.total.for.qtr
	print
	print using "&"+amt$;tab(col2%);crt.data$(50),tab(col3%);final.deposit
	print
	print using amt$;tab(amt.tab%);grand.total.for.qtr
	print:print
	print using amt$;tab(amt.tab%);taxes.due
	print
	print using amt$;tab(disp%+36);new.overpay
	print:print:print:print
	print using "&";tab(disp%+9);fn.date.out$(common.date$)
	print:print:print
	gosub 360	rem  do it again?
   wend
	return

310	rem-----set used flags------
	for i% = 1 to crt.field.count%
		trash% =fn.set.used%(false%,i%)
	next i%
	trash% = fn.set.used%(true%,fld.prompt%)
	trash% = fn.set.used%(true%,fld.prompt.resp%)
	for i% = 79 to 82
		trash% = fn.set.used%(true%,i%)
		trash% = fn.lit%(i%)
	next i%
	trash% = fn.set.used%(true%,78)
	return

350	rem-----align forms------
	prompt$ = "PRINT ALIGNMENT MARKS?"
	trash% = fn.put%(prompt$,fld.prompt%)
	trash% = fn.lit%(78)
	while true%
		gosub 370	rem get answer
		lprinter
		if yes% or cr%	then gosub 380		rem print marks
		if no%	then return
	wend
	return

360	rem-----again?-------
	again% = false%
	console
	prompt$ = "PRINT ANOTHER FORM?"
	trash% = fn.put%(prompt$,fld.prompt%)
	gosub 370	rem get answer
	if yes%  then again% = true%
	return

370	rem-----get answer------
	field% = fld.prompt.resp%
	yes% = false%
	no% = false%
	gosub 120	rem get data
	if cr%	then return
	if in.uc$ = "Y"  then \
		yes% = true% :\
		trash% = fn.put%(in.uc$,fld.prompt.resp%) :\
		return
	if in.uc$ = "N"  then \
		no% = true% :\
		trash% = fn.put%(in.uc$,fld.prompt.resp%) :\
		return
	if stopit%  then gosub 390	rem display msg & go bye-bye
	trash% = fn.put%(null$,fld.prompt.resp%)
	emsg% = 9
	gosub 400	rem display emsg & delay
	goto 370	rem try it again
	return

380	rem-----print alignment marks------
	print tab(disp%+3);"|_____________________________________________________________________________|"
	return

390	rem------print stop req & stop------
	trash% = fn.msg%("STOP REQUESTED")
	close pr2.file%
	goto 999.2	rem prem end
	return

400	rem-----display emsg & delay-----
	trash% = fn.emsg%(emsg%)
	for i% = 1 to 450
	next i%
	trash% = fn.msg%(null$)
	return

550	rem-----get screen 2------
	for i% = start.lit% to end.lit%
		trash% = fn.lit%(i%)	rem display literals
	next i%
	gosub 560	rem display screen 2 data & load
	return

560	rem-------display screen 2 data & load values------
	trash% = fn.put%(fn.date.out$(end.of.qtr$),48)
	trash% = fn.put%(str$(overpay),fld.overpay%)
rem monthly tables
	for i% = 1 to 12
		trash% = fn.put%(str$(coh.tax(i%)),i%)
		if coh.date$(i%) <> null$  then \
			trash% = fn.put%(fn.date.out$(coh.date$(i%)),i%+12) \
		   else \
			trash% = fn.put%(null$,i%+12)
		trash% = fn.put%(str$(coh.tax(i%)),i%+24)
	next i%
	trash% = fn.put%(str$(first.mo),37)
	trash% = fn.put%(fn.date.out$(first.mo$),38)
	trash% = fn.put%(str$(real.first.mo),39)
	trash% = fn.put%(str$(second.mo),40)
	trash% = fn.put%(fn.date.out$(second.mo$),41)
	trash% = fn.put%(str$(real.second.mo),42)
	trash% = fn.put%(str$(third.mo),43)
	trash% = fn.put%(fn.date.out$(third.mo$),44)
	trash% = fn.put%(str$(real.third.mo),45)
rem rest of screen
	trash% = fn.put%(str$(total.for.qtr),46)
	trash% = fn.put%(str$(real.total.for.qtr),47)
	trash% = fn.put%(fn.date.out$(common.date$),50)
	trash% = fn.put%(str$(final.deposit),51)
	trash% = fn.put%(str$(grand.total.for.qtr),52)
	trash% = fn.put%(str$(taxes.due),54)
	trash% = fn.put%(str$(new.overpay),53)
	return

