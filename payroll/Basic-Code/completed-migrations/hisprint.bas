#include "ipycomm"
#include "ipyconst"
prgname$="HISPRINT  18 JAN., 1980"


rem----------------------------------------------------------------------
rem
REM
REM	      HISTORY PRINT
REM	      PAYROLL SYSTEM
REM		(HISPRINT)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "EMPLOYEE HISTORY REPORT"

REM
REM	FOLLOWING IS A GUIDE TO SUBROUTINES IN HISPRINT
REM

REM	50	processing message
REM	60	CLEAR SCREEN OF UNNEEDED FIELDS

REM	100	MAIN DRIVER FOR PRINTING CYCLE
REM	200	LOOKING FOR HIS FILE, READING HDR
REM	220	LOOK FOR EMP FILE, READ HDR
REM	250	LOOK FOR DED FILE, READ IT
REM	260	LOOK FOR COH FILE, READ IT

REM	1000	PRINT REPORT HEADER
REM	1010	PRINT "REPORT CONTINUES"
REM	1020	PRINT "END OF REPORT"

REM	1100	PRINT HISTORY FILE
REM	1150	PRINT E/D LINES

REM	2000	READ HISTORY FILE RECORD
REM	2100	READ EMPLOYEE FILE
REM	2200	PRINT EMPLOYEE NUMBER ON SCREEN



rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------
#include "zdms"
#include "zdmstest"
#include "zdmsclr"
#include "zdmsconf"
#include "zdmsabrt"
#include "zdmsused"
#include "zdmsbrt"

#include "zstring"
#include "zdateio"
#include "zfilconv"
#include "zflip"
#include "zheading"

#include "ipydmhis
#include "ipydmemp"
#include "ipydmded"
#include "ipydmcoh"


rem
rem	error messages
rem
	dim emsg$(10)	rem can go to 20
	emsg$(1) = "     PY801 INVALID RESPONSE"
	emsg$(2) = "     PY802 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY803 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY804 UNEXPECTED END OF HISTORY FILE"
	emsg$(5) = "     PY805 HISTORY FILE NOT FOUND"
	emsg$(6) = "     PY806 EMPLOYEE FILE NOT FOUND"
	emsg$(7) = "     PY807 UNEXPECTED END OF EMPLOYEE FILE"
	emsg$(8) = "     PY808 DEDUCTION FILE NOT FOUND"
	emsg$(9) = "     PY809 COMPANY HISTORY FILE NOT FOUND"

program$ = "HISPROOF"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2



rem
rem	get screen set up
rem

#include "fpyhisp"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	fld.now.processing% = 1
	lit.processing% = 6

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP


REM
REM	SEE IF HISTORY FILE PRESENT--IF YES, OPEN & READ HDR
REM
	gosub 200	rem don't bother returning if you can't find it

REM
REM	SEE IF EMPLOYEE FILE PRESENT--IF YES, OPEN & READ HDR
REM
	gosub 220	rem don't come back if not there

REM
REM	SEE IF DEDUCTION FILE PRESENT--IF YES, READ IT
REM
	gosub 250	rem don't show up again if not there


REM
REM	INIT OTHER STUFF
REM
	line.count.limit% = 60
	pw$ = null$	rem for use with trash 80, maybe
	pm$ = null$
	a$ = "& "
	amt$ = "#,###,###.## "
	sys$ = a$+amt$+amt$
	line2$ = a$+amt$+a$+amt$
	qtd.line$ = a$+amt$+amt$+amt$+amt$+amt$+amt$
	lines.per.emp% = 22

REM
REM	CRT INPUT DRIVER
REM

	rgstr.printed% = false%
	while not rgstr.printed%
		gosub 50	REM put up processing msg
		if stopit% then goto 10 REM EXIT REQUESTED

		gosub 100	REM MAIN PRINTING DRIVER
		gosub 60	REM CLEAR SCREEN OF PROCESSING MESSAGE
		rgstr.printed% = true%
	wend



REM
REM	EOJ PROCESSING
REM

 10
	if stopit% or stop.print% \
	   then \
		trash% = fn.msg%("     STOP REQUESTED")
 11	close his.file%
	close emp.file%

	if stop.print%	then 999.2	rem premature end

	goto 999		REM NORMAL EXIT

 50	REM put up processing msg

	trash% = fn.lit%(lit.processing%)
	return

 60	REM CLEAR SCREEN OF UNNEEDED FIELDS UPON PROCESSING COMPLETION

	trash% = fn.clr%(fld.now.processing%)
	trash% = fn.clr%(lit.processing%)
	return



REM
REM	MAIN DRIVER FOR PRINTING PROCESSING
REM

 100
	page% = 0
	current.his.record% = 1
	stop.print% = false%
	line.count% = line.count.limit% REM FORCE HEADING AT BEGINNING
	lprinter

while not stop.print% and current.his.record% <= his.hdr.no.recs%
	gosub 2000	REM READ HISTORY RECORD
	gosub 2100	REM READ EMPLOYEE FILE
	gosub 2200	REM DISPLAY NUMBER ON SCREEN
	gosub 1100	REM PRINT HISTORY INFO
	if pr1.debugging% \
	   then \
		console :\
		trash% = fn.msg%("fre=" + str$(fre)) :\
		lprinter

	current.his.record% = current.his.record% + 1
wend

	if not stop.print% \
	   then \
		gosub 260   :\	rem find & open coh--die if not there
		gosub 1200  :\	rem print coh info (not implemented yet)
		gosub 1020	REM PRINT END OF REPORT LINE

	console
	return


REM======E O J=============
close emp.file%,his.file%

#include "zeoj"


REM--------SUBROUTINES------------
200	rem-----look for his file-----
       his.file.name$=fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pm$)
	if end #his.file%  then 201
	open his.file.name$  recl his.len%  as his.file%
	if end #his.file%  then 202

	read #his.file%,1;\	rem header rec
#include "ipyhishd"

	return

201	rem-----no his file at all-----
	trash% = fn.emsg%(5)
	goto 999.1	rem goodbye

202	rem-----unexpected eof-------
	trash% = fn.emsg%(4)
	close his.file%, emp.file%
	goto 999.1	rem aaaarrrgghhh

220	rem-----look for emp file, read hdr-----
       emp.file.name$=fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pm$)
	if end #emp.file%  then 229.9
	open emp.file.name$  recl emp.len%  as emp.file%
	if end #emp.file%  then 229.99

	read #emp.file%,1;\	rem header rec
#include "ipyemphd"

	return

229.9	rem-----emp file not found-----
	trash% = fn.emsg%(6)
	close his.file%
	goto 999.1	rem die, die, die
229.99	rem-----unexpected eof on emp-----
	console
	trash% = fn.emsg%(7)
	close his.file%, emp.file%
	goto 999.1	rem crash


250	rem-----look for ded file, read if there------
       ded.file.name$=fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pw$,pm$)
	if end #ded.file%  then 259.9
	open ded.file.name$  as ded.file%

	read #ded.file%; \
#include "ipyded"

	close ded.file%
	return

259.9	rem-----no ded file------
	trash% = fn.emsg%(8)
	close his.file%, emp.file%
	goto 999.1	rem thud

260	rem-----look for coh file, read if there------
       coh.file.name$=fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pm$)
	if end # coh.file%  then 269.9
	open coh.file.name$ as coh.file%
	read # coh.file%;\
#include "ipycoh"

	close coh.file%
	return

269.9	rem-----no coh.file-----
	trash% = fn.emsg%(9)
	close his.file%, emp.file%
	goto 999.1	rem die like a dog

REM--------PRINT ROUTINES---------
 1000	REM PRINT HEADING
	line.count% = fn.hdr%(function.name$)
	return

 1010	REM PRINT *** REPORT CONTINUES ***
	if page% <> 0 \ REM SKIP CONTINUES MESSAGE IF REPORT HASN'T STARTED YET
	   then \
		print "     *** REPORT CONTINUES ***"
	return

 1020	REM PRINT *** END OF REPORT ***
	print
	print "     *** END OF REPORT ***"
	return


 1100	REM PRINT HISTORY
	if line.count% + lines.per.emp% > line.count.limit% \
	   then \
		gosub 1010 :\	REM CONTINUED LINE
		gosub 1000	REM PRINT HEADER

	line.count% = line.count% + 2

	print:print
	print  tab(5); "EMPLOYEE NUMBER: "; tab(25); \
		his.emp.no$; tab(35); "NAME: "; tab(42); emp.emp.name$; \
		tab(75); status$
	print using line2$; tab(10); "NET QTD INCOME:"; tab(26); \
		his.qtd.net; tab(45); "NET YTD INCOME"; tab(62);his.ytd.net
	stop.print% = fn.abort%
	if stop.print%	then return
	print
	print tab(17);"TAXABLE             OTHER              OTHER";tab(94); \
		"FICA             FEDERAL"
	print tab(18);"INCOME            TAXABLE            UNTAXED         "+\
		"      TIPS            TAXABLE        WITHHOLDING"
	print using qtd.line$; tab(2);"QTD AMOUNT";tab(14);his.qtd.income.taxable;\
	       tab(33);his.qtd.other.taxable;tab(52);his.qtd.other.nontaxable;\
		tab(71);his.qtd.tips;tab(90);his.qtd.fica.taxable;tab(109); \
		his.qtd.fwt
	print using qtd.line$; tab(2);"YTD AMOUNT";tab(14);his.ytd.income.taxable;\
	       tab(33);his.ytd.other.taxable;tab(52);his.ytd.other.nontaxable;\
		tab(71);his.ytd.tips;tab(90);his.ytd.fica.taxable;tab(109); \
		his.ytd.fwt
	stop.print% = fn.abort%
	if stop.print%	then return
	print
	print tab(18);"STATE              LOCAL";tab(111);"OTHER"
	print tab(15); "WITHHOLDING        WITHHOLDING             FICA"; \
		tab(78);"SDI"; tab(97); "EIC"; tab(110); "DEDUCTIONS"
	print using qtd.line$; tab(2);"QTD AMOUNT";tab(14);his.qtd.swt; \
	       tab(33);his.qtd.lwt;tab(52);his.qtd.fica; \
		tab(71);his.qtd.sdi; tab(90);his.qtd.eic; tab(109); \
		his.qtd.other.ded
	print using qtd.line$; tab(2);"YTD AMOUNT";tab(14);his.ytd.swt; \
	       tab(33);his.ytd.lwt;tab(52);his.ytd.fica;\
		tab(71);his.ytd.sdi;tab(90);his.ytd.eic; tab(109); \
		his.ytd.other.ded
	gosub 1150	rem do ed lines
	print:print
	line.count% = line.count% + 15 + lines%

	return

1150	rem-----do e/d lines-----
	stop.print% = fn.abort%
	if stop.print%	then return
	max% = 4	rem minimum # of lines
	if pr1.max.sys.eds% > max%  then \
		max% = pr1.max.sys.eds%
	print
	if pr1.max.sys.eds% > 0  then \
		print tab(8); "SYSTEM E/D'S   QTD" ; tab(36); "YTD";
	if pr1.max.emp.eds% > 0  then \
		print tab(45); "EMPLOYEE E/D'S"; tab(66);"QTD"; tab(79); "YTD";
	print tab(88); "STANDARD RATE UNITS"; tab(109); "QTD"; tab(122); "YTD"

	i% = 1
	while i% <= max%
		if pr1.max.sys.eds% >= i%  then \
			print using sys$; ded.sys.desc$(i%); \
				tab(16); his.qtd.sys(i%); \
				tab(29); his.ytd.sys(i%);
		if pr1.max.emp.eds% >= i%  then \
			print using sys$; tab(43); emp.ed.desc$(i%); \
				tab(59); his.qtd.emp(i%); \
				tab(72); his.ytd.emp(i%);
		if i% <= 4  then \
			print using sys$; tab(86); pr1.rate.name$(i%); \
				tab(102); his.qtd.units(i%); \
				tab(115); his.ytd.units(i%) \
		   else  print
		stop.print% = fn.abort%
		if stop.print%	then return
		i% = i% + 1
	wend
	lines% = max% + 2
	return



1200	rem-----print coh info--------
	title$ = "COMPANY HISTORY"
	gosub 1010	rem print cont'd line
	gosub 1000	rem print title
	print
	print tab(fn.center%(title$,132)); title$
	print
	print using line2$; tab(10); "NET QTD INCOME:"; tab(26); \
		coh.qtd.net; tab(45); "NET YTD INCOME"; tab(62);coh.ytd.net
	stop.print% = fn.abort%
	if stop.print%	then return
	qtd.line$ = qtd.line$ + amt$
	print
	print tab(20);"TAXABLE           OTHER            OTHER";tab(88); \
		"FICA           FEDERAL          STATE"
	print tab(21);"INCOME          TAXABLE          UNTAXED       "+\
		"   TIPS           TAXABLE        WITHHOLDING     WITHHOLDING"
	print using qtd.line$; tab(2);"QTD AMOUNT";tab(14);coh.qtd.income.taxable;\
	       tab(31);coh.qtd.other.taxable;tab(48);coh.qtd.other.nontaxable;\
		tab(65);coh.qtd.tips;tab(82);coh.qtd.fica.taxable;tab(99); \
		coh.qtd.fwt.liab; tab(116); coh.qtd.swt.liab
	print using qtd.line$; tab(2);"YTD AMOUNT";tab(14);coh.ytd.income.taxable;\
	       tab(31);coh.ytd.other.taxable;tab(48);coh.ytd.other.nontaxable;\
		tab(65);coh.ytd.tips;tab(82);coh.ytd.fica.taxable;tab(99); \
		coh.ytd.fwt.liab; tab(116); coh.ytd.swt.liab
	stop.print% = fn.abort%
	if stop.print%	then return
	print
	qtd.line$ = qtd.line$ + amt$
	print tab(18);"LOCAL";tab(45);"COMPANY";tab(118);"OTHER"
	print tab(15); "WITHHOLDING";tab(33);"FICA";tab(47);"FICA"; \
		tab(62);"SDI";tab(76); "EIC"; tab(89);"FUTA";tab(104); \
		"SUI"; tab(114); "DEDUCTIONS"
	print using qtd.line$; tab(2);"QTD AMOUNT";tab(13);coh.qtd.lwt.liab; \
	       tab(27);coh.qtd.fica.liab; tab(41);coh.qtd.co.fica.liab; \
		tab(55);coh.qtd.sdi.liab;tab(69);coh.qtd.eic.credit;tab(83);\
		coh.qtd.co.futa.liab; tab(97); coh.qtd.co.sui.liab; \
		tab(111); coh.qtd.other.ded
	print using qtd.line$; tab(2);"YTD AMOUNT";tab(13);coh.ytd.lwt.liab; \
	       tab(27);coh.ytd.fica.liab; tab(41);coh.ytd.co.fica.liab;\
	       tab(55);coh.ytd.sdi.liab;tab(69);coh.ytd.eic.credit;tab(83); \
	       coh.ytd.co.futa.liab; tab(97); coh.ytd.co.sui.liab;  \
	       tab(111); coh.ytd.other.ded
	print

1250	rem-----do co e/d/lines-----
	stop.print% = fn.abort%
	if stop.print%	then return
	max% = 4	rem minimum # of lines
	if pr1.max.sys.eds% > max%  then \
		max% = pr1.max.sys.eds%
	print
	if pr1.max.sys.eds% > 0  then \
		print tab(8); "SYSTEM E/D'S   QTD" ; tab(36); "YTD";
	if pr1.max.emp.eds% > 0  then \
		print tab(45); "EMPLOYEE E/D'S"; tab(66);"QTD"; tab(79); "YTD";
	print tab(88); "STANDARD RATE UNITS"; tab(109); "QTD"; tab(122); "YTD"

	i% = 1
	while i% <= max%
		if pr1.max.sys.eds% >= i%  then \
			print using sys$; ded.sys.desc$(i%); \
				tab(16); coh.qtd.sys(i%); \
				tab(29); coh.ytd.sys(i%);
		if pr1.max.emp.eds% >= i%  then \
			print using sys$; tab(43); emp.ed.desc$(i%); \
				tab(59); coh.qtd.emp(i%); \
				tab(72); coh.ytd.emp(i%);
		if i% <= 4  then \
			print using sys$; tab(86); pr1.rate.name$(i%); \
				tab(102); coh.qtd.units(i%); \
				tab(115); coh.ytd.units(i%) \
		   else  print
		stop.print% = fn.abort%
		if stop.print%	then return
		i% = i% + 1
	wend
	lines% = max% + 2
1260	rem----- do qtr depos info-------
	depos$ = "## & "+amt$
	print:print
	print tab(18);"QUARTER-MONTH FWT AND FICA LIABILITY"; tab(73); \
		"TAX LIABILITIES BY QUARTER"
	print tab(17); "QTR-MONTH   DATE ENDED     AMOUNT"; tab(65); \
		"QTR         FWT         FICA          FUTA"
	print
	for i% = 1 to 4
		print using depos$+"# "+amt$+amt$+amt$; tab(21); i%; \
		      tab(29); fn.date.out$(coh.date$(i%)); tab(40); \
		      coh.tax(i%); tab(65); i%; tab(70); coh.q.tax(i%); \
		      tab(83); coh.q.fica.tax(i%); tab(97); \
		      coh.q.co.futa.liab(i%)
	next i%
	for i% = 5 to 12
	    print using depos$;tab(21);i%;tab(29);fn.date.out$(coh.date$(i%));\
		tab(40); coh.tax(i%)
	next i%
	return



 2000	REM READ HISTORY RECORD

	read #his.file%,current.his.record% + 1; \
#include "ipyhis"

	return



2100	rem------read employee record------

	read #emp.file%,current.his.record% + 1; \
#include "ipyemp"

	if emp.status$ = "D"  then status$ = "(DELETED)"
	if emp.status$ = "T"  then status$ = "(TERMINATED)"
	if emp.status$ = "A"  then status$ = "(ACTIVE)"
	if emp.status$ = "L"  then status$ = "(ON LEAVE)"
	emp.emp.name$ = fn.name.flip$(emp.emp.name$)

	return

 2200	REM PUT EMPLOYEE NUMBER ON SCREEN

	console
	trash% = fn.put%(his.emp.no$,fld.now.processing%)
	lprinter
	return

	end
