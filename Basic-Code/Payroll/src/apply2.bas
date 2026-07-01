$include "ipycomm"
$include "ipyapcom"
prgname$="APPLY2     JAN.  17, 1980 "
rem----------------------------------------------------------
rem
rem	A  P  P  L  Y  2
rem
rem		EMPLOYEE CALCULATIONS
rem
rem	SECTION TWO OF PAYROLL CALCULATION PROGRAM
rem
rem	P A Y R O L L	   S Y S T E M
rem
rem	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="APPLY2"
function.name$="PAYROLL APPLICATION -- SECTION TWO"

$include "ipyconst"
	def fn.drive.out$(temp%)
		if temp% = 0	\
			then fn.drive.out$ = "@"        \
			else fn.drive.out$ = chr$(asc("A") + temp% - 1)
		return
	fend
	def fn.file.name.out$(c.name$,c.type$,c.drive%,c.password$,c.params$)=\
		fn.drive.out$(c.drive%)+":"+c.name$+"."+c.type$

$include "zstring"
$include "zdmssca"
$include "zdmsput"
$include "zdmslit"
$include "zdmsmsg"
$include "zdmsemsg"
$include "zdmsclr"

rem----------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem----------------------------------------------------------

rem	subscripts for accessing withholding tables
swt.table% =1
lwt.table% =2
cals.table%=3
calm.table%=4
calh.table%=5

dim emsg$(05)
emsg$(01)="PY551"               rem dummy message for fre stmt
emsg$(02)="PY552 NOT PROPERLY CHAINED"
emsg$(03)="PY553 HOURS TRANSACTION REJECTED FOR TERMINATED OR ON-LEAVE EMP"
emsg$(04)="PY554"

def fn.taxable(limit,ytd,current)
	max.taxable = limit - ytd
	excess = current - max.taxable
	if excess < 0 then excess = 0
	if max.taxable <= 0	\
		then	fn.taxable = 0	\
		else	fn.taxable = current - excess
	return
fend

def fn.max(a,b)
	if a > b	\
		then	fn.max = a	\
		else	fn.max = b
	return
fend

def fn.min(a,b)
	if a < b	\
		then	fn.min = a	\
		else	fn.min = b
	return
fend

def fn.ed.amt
	if amt.percent$="A" \
		then	fn.ed.amt=factor \
		else	fn.ed.amt=(factor/100)*ed.gross
	return
fend

def fn.ded.limit
	if net>=pyo.amt \
		then	fn.ded.limit=pyo.amt	\
		else	fn.ded.limit=net
	return
fend

def fn.round(rr)=(int((rr*100)+.5))/100

$include "ipystat"
$include "ipydmemp"
$include "ipydmhis"
$include "ipydmded"
$include "ipydmswt"
$include "ipydmcal"
$include "fpyap2"

dim sys(5)
dim emp(3)
dim units(4)

rem	The function used in STATE (SWT), LOCAL (LWT), and
rem	CALIFORNIA (CAL) tax calculations:
rem
rem   fn.withhold(agency%,annual.equiv.wage,allow%,allow.amt,num.entries%)
rem			returns annual equivalent withholding.
rem			agency% is 1 if SWT and 2 if LWT
rem			3 if CALSingle 4 if CALMarried 5 if CALHead
rem			num.entries refers to the number of
rem			entries in withholding table
rem

def fn.withhold(agency%,aew,allowances%,allowance.amt,num.entries%)
	loc.withhold = 0		rem local withholding accumulator
	index% = 1			rem place in table
	aew = aew - allowances% * allowance.amt
	while num.entries%> index%
		if aew>withhold.cutoff(index%,agency%)			\
			then	loc.withhold=loc.withhold+		\
				fn.min(aew-withhold.cutoff		\
				(index%,agency%),			\
				withhold.cutoff(index%+1,agency%)-	\
				withhold.cutoff(index%,agency%))*	\
				withhold.percent(index%,agency%)/100.0
		index%=index%+1
	wend
	if aew>withhold.cutoff(index%,agency%)			\
		then	loc.withhold=loc.withhold+		\
			(aew-withhold.cutoff(index%,agency%))*	\
			withhold.percent(index%,agency%)/100.0
	fn.withhold = loc.withhold
	return
fend

rem----------------------------------------------------------
rem
rem	S E T	    U P
rem
rem----------------------------------------------------------

gosub 200		rem display.set.up.screen

rem----------------------------------------------------------
rem
rem	B O J
rem
rem----------------------------------------------------------

gosub 210			rem can.we.run
if not ok% then goto 999.1

gosub 500			rem set up files
gosub 330			rem display.process.screen

rem----------------------------------------------------------
rem
rem	M A I N      D R I V E R
rem
rem----------------------------------------------------------

employee%=1
while employee%<=pr2.no.employees%
	gosub 400			rem process.employee
	employee%=employee%+1
	if pr1.debugging% \
		then	emsg$(01)="free storage: "+str$(fre)            :\
			trash%=fn.emsg%(01)
wend

rem----------------------------------------------------------
rem
rem	E N D	  O F	  J O B
rem
rem----------------------------------------------------------

gosub 800			rem write.pyo.hdr
gosub 840			rem update emp hdr
trash%=fn.clr%(04)		rem clear status literal
trash%=fn.clr%(01)		rem clear status message
gosub 860			rem close.all.files

chain fn.file.name.out$("apply3",null$,0,pw$,pms$)

$include "zeoj"

rem----------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem----------------------------------------------------------

200	rem-----display set up screen------------------------
	trash%=fn.lit%(3)	rem function name
	trash%=fn.lit%(6)	rem EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY
	return

210	rem-----can we run?----------------------------------
	ok%=true%
	if match(in.apply$,common.chaining.status$,1)=0 \
		then	ok%=false%	:\
			trash%=fn.emsg%(02)
	return

330	rem-----display process screen-----------------------
	trash%=fn.clr%(6)
	trash%=fn.lit%(5)	rem PROCESSING EMPLOYEE NUMBER:
	trash%=fn.lit%(4)	rem CURRENT EMPLOYEE STATUS IS:
	return

400	rem-----process employee-----------------------------
	gosub 1000			rem clear.employee.accums
	gosub 1020			rem read.next.employee.record
	gosub 1010			rem display employee number
	gosub 1030			rem display employee status
	if emp.status$="D"              \
		then	return

	if match(emp.pay.interval$,extension.intervals$,1)=0 \
		then	extend%=false%	\
		else	extend%=true%

	if extend% \
		then	gosub 1050	rem read.matching.history.record

	while not pay.eof% and val(left$(pay.emp.no$,4))=employee%
		if extend% \
			then	gosub 1060 \	rem process pay rec
			else	gosub 2012 :\	rem put pays into pyos
				gosub 2015	rem write new pyo rec
		gosub 1070		rem select a pay rec
	wend

	while not hrs.eof% and val(left$(hrs.emp.no$,4))=employee%
		if extend% \
			then	gosub 1090 \	rem process.hrs.rec
			else	gosub 1100	rem copy hrs rec
		hrs.rec%=hrs.rec%+1
		gosub 1110		rem get.hrs.rec
	wend

	if extend% \
		then	gosub 410 \	rem extend employee
		else	return
	return

410	rem-----extend employee------------------------------
	if emp.status$="T" \
		then	goto 411	rem skip extension
	gosub 1120			rem process.rate.zero
	if emp.status$="A" \
		then	gosub 1125	rem process auto units

	ed.gross=income.taxable+other.taxable+tips
	acceptable.type$="E"            rem earnings only
	if emp.status$="A" \
		then	gosub 1140 :\	rem process.systemwide.eds
			gosub 1150	rem process.recurring.emp.eds

	gross.taxable.pay=income.taxable+other.taxable+tips
	ed.gross=gross.taxable.pay
	comb.other.taxable=income.taxable+other.taxable+tips
	comb.ytd.other.taxable=his.ytd.income.taxable+		\
		his.ytd.other.taxable+his.ytd.tips

	gosub 1160			rem process fwt
	gosub 1170			rem process swt
	gosub 1180			rem process lwt
	gosub 1190			rem process fica
	gosub 1240			rem process sdi
	gosub 1200			rem process co fica
	gosub 1210			rem process co sui
	gosub 1220			rem process co futa
	gosub 1230			rem process eic

	gosub 1300			rem process.vacation
	gosub 1310			rem process.sick.leave

	gross.pay=income.taxable+other.taxable+other.nontaxable+eic+tips
	net=gross.pay-(tips.reported+fwt+swt+lwt+fica+sdi)

	acceptable.type$="D"            rem deductions only
	gosub 1140			rem process.systemwide.eds
	gosub 1150			rem process.recurring.emp.eds
411	rem-----here if terminated employee------------------
	gosub 1320			rem update employee record
	gosub 1330			rem write.employee.record
	return

500	rem-----set up files---------------------------------
	gosub 510			rem open hrs.file
	if hrs.exists% \
		then	gosub 520 :\	rem get hrs header rec
			gosub 530 \	rem get priming read
		else	hrs.eof%=true%
	gosub 540			rem open existing pay file for input
	if pay.exists% \
		then	gosub 550 :\	rem get.pay.hdr
			gosub 560  \	rem get priming read
		else	pay.eof%=true%
	gosub 570			rem open emp.file
	gosub 580			rem read emp hdr
	gosub 590			rem open ded.file
	gosub 600			rem read ded file
	close ded.file%
	if ded.swt.used% \
		then	gosub 610	rem open and read swt file(s)
	if ded.lwt.used% \
		then	gosub 640	rem open and read lwt file
	gosub 670			rem open his file
	gosub 680			rem read.his.hdr
	gosub 690			rem open new pyo file for output
	return

510	rem-----open hrs file--------------------------------
	hrs.exists%=false%
	if end #hrs.file% then 511
	open fn.file.name.out$(hrs.name$,"101",pr1.hrs.drive%,pw$,pms$) \
		recl hrs.len%  as hrs.file%
	hrs.exists%=true%
511	rem-----here if hrs file not present-----------------
	return

520	rem-----get hrs hdr----------------------------------
	read #hrs.file%,1;   \
$include "ipyhrshd"
	return

530	rem-----get hrs priming read-------------------------
	hrs.rec%=1
	gosub 1110			rem get hrs rec
	return

540	rem-----open pay file--------------------------------
	pay.exists%=false%
	if end #pay.file% then 541
	open fn.file.name.out$(pay.name$,"101",pr1.pay.drive%,pw$,pms$) \
		recl pay.len%  as pay.file%
	pay.exists%=true%
541	rem-----here if pay file not present-----------------
	return

550	rem-----get pay hdr----------------------------------
	read #pay.file%,1;    \
$include "ipypayhd"
	return

560	rem-----get pay priming read-------------------------
	pay.rec%=0
	gosub 1070			rem select a pay rec
	return

570	rem-----open emp file--------------------------------
	emp.exists%=false%
	if end #emp.file% then 571
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pms$) \
		recl emp.len%  as emp.file%
	emp.exists%=true%
571	rem-----here if emp file not present-----------------
	return

580	rem-----read emp hdr---------------------------------
	read #emp.file%,1;  \
$include "ipyemphd"
	return

590	rem-----open ded file--------------------------------
	ded.exists%=false%
	if end #ded.file% then 591
	open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pw$,pms$) \
		as ded.file%
	ded.exists%=true%
591	rem-----here if ded file not present-----------------
	return

600	rem-----read ded file--------------------------------
	read #ded.file%; \
$include "ipyded"
	return

610	rem-----open and read swt file-----------------------
	if pr1.co.state$="CA" \
		then	suffix$="S" :\  rem single table
			agency%=cals.table%		:\
			gosub 632   :\	rem open CAL file
			gosub 634   :\	rem read CAL file
			close cal.file%  :\
			suffix$="M" :\  rem married table
			agency%=calm.table%		:\
			gosub 632   :\	rem open CAL file
			gosub 634   :\	rem read CAL file
			close cal.file%  :\
			suffix$="H" :\  rem head of house table
			agency%=calh.table%		:\
			gosub 632   :\	rem open CAL file
			gosub 634   :\	rem read CAL file
			close cal.file%  :\
			suffix$="X" :\  rem special table file
			gosub 632   :\	rem open CAL file
			gosub 635   : \ rem read special cal table file
			close cal.file%  :\
		else	agency%=swt.table%		:\	rem SWT
			gosub 620   :\	rem open swt file
			gosub 630   :\	rem read swt file
			close swt.file%
	return

620	rem-----open swt file--------------------------------
	swt.exists%=false%
	if end #swt.file% then 621
	open fn.file.name.out$(swt.name$+pr1.co.state$,"101",   \
		pr1.tax.drive%,pw$,pms$) \
		as swt.file%
	swt.exists%=true%
621	rem-----here if swt file not present-----------------
	return

630	rem-----read swt file--------------------------------
	read #swt.file%; \
$include "ipyswt"
	return

632	rem-----open cal file--------------------------------
	cal.exists%=false%
	if end #cal.file% then 633
	open fn.file.name.out$(cal.name$+suffix$,"101",   \
		pr1.tax.drive%,pw$,pms$) \
		as cal.file%
	cal.exists%=true%
633	rem-----here if cal file not present-----------------
	return

634	rem-----read cal file--------------------------------
	read #cal.file%;  \
$include "ipyswt"
	return

635	rem-----read special cal file------------------------
	read #cal.file%;  \
$include "ipycal"
	return

640	rem-----open and read lwt file-----------------------
	agency%=lwt.table%
	gosub 650			rem open lwt file
	gosub 660			rem read lwt file
	close lwt.file%
	return

650	rem-----open lwt file--------------------------------
	lwt.exists%=false%
	if end #lwt.file% then 651
	open fn.file.name.out$(lwt.name$,"101",pr1.tax.drive%,pw$,pms$) \
		as lwt.file%
	lwt.exists%=true%
651	rem-----here if lwt file not present-----------------
	return

660	rem-----read lwt file--------------------------------
	read #lwt.file%; \
$include "ipyswt"
	return

670	rem-----get his file---------------------------------
	his.exists%=false%
	if end #his.file% then 671
	open fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pms$) \
		recl his.len%  as his.file%
	his.exists%=true%
671	rem-----here if his file not present-----------------
	return

680	rem-----read his hdr---------------------------------
	read #his.file%,1;     \
$include "ipyhishd"
	return

690	rem-----open new pyo file for output-----------------
	open fn.file.name.out$(pyo.name$,"100",pr1.pyo.drive%,pw$,pms$) \
		recl pyo.len%  as pyo.file%
	temp%=pay.hdr.no.recs%
	gosub 700			rem read pyo hdr
	pyo.hdr.no.recs%=pay.hdr.no.recs%
	pay.hdr.no.recs%=temp%
	return

700	rem-----read pyo hdr---------------------------------
	read #pyo.file%,1;    \
$include "ipypayhd"
	return

800	rem-----write pyo hdr--------------------------------
	pay.hdr.no.recs%=pyo.hdr.no.recs%
	print #pyo.file%,1;    \
$include "ipypayhd"
	return

840	rem-----update emp hdr-------------------------------
	print #emp.file%,1;    \
$include "ipyemphd"
	return

860	rem-----close all files------------------------------
	close pyo.file%
	close emp.file%
	close his.file%
	return

1000	rem-----clear employee accums------------------------
	gross.taxable.pay	=zero
	income.taxable		=zero
	other.taxable		=zero
	other.nontaxable	=zero
	fica.taxable		=zero
	tips			=zero
	tips.reported		=zero
	net			=zero
	eic			=zero
	fwt			=zero
	swt			=zero
	lwt			=zero
	fica			=zero
	sdi			=zero
	sys(1)			=zero
	sys(2)			=zero
	sys(3)			=zero
	sys(4)			=zero
	sys(5)			=zero
	emp(1)			=zero
	emp(2)			=zero
	emp(3)			=zero
	other.ded		=zero
	units(0)		=zero
	units(1)		=zero
	units(2)		=zero
	units(3)		=zero
	units(4)		=zero
	vac.used		=zero
	vac.accum		=zero
	sl.used 		=zero
	sl.accum		=zero
	comp.used		=zero
	comp.accum		=zero
	co.fica 		=zero
	co.futa 		=zero
	co.sui			=zero
	auto.units.overridden%	=false%
	return

1010	rem-----display employee number----------------------
	trash%=fn.put%(emp.no$,2)
	return

1020	rem-----read next employee record--------------------
	read #emp.file%,employee%+1;	\
$include "ipyemp"
	return

1030	rem-----display employee status----------------------
	if last.emp.status$=emp.status$ \
		then	return
	last.emp.status$=emp.status$
	if emp.status$="A" \
		then	trash%=fn.put%("ACTIVE",1)      :\
			return
	if emp.status$="L" \
		then	trash%=fn.put%("ON-LEAVE",1)    :\
			return
	if emp.status$="T" \
		then	trash%=fn.put%("TERMINATED",1)  :\
			return
	if emp.status$="D" \
		then	trash%=fn.put%("DELETED",1)     :\
			return
	print "blooey":stop

1050	rem-----read matching history record-----------------
	read #his.file%,employee%+1;	\
$include "ipyhis"
	return

1060	rem-----process pay rec------------------------------
	in.emp.no$=pay.emp.no$
	in.eff.date$=pay.eff.date$
	in.rate%=pay.reporting.cat%
	in.units=pay.units
	gosub 1390			rem process in rec
	return

1070	rem-----select a pay rec-----------------------------
	pay.rec%=pay.rec%+1
	gosub 1080			rem get pay rec
	if pay.eof% then return
	while pay.extended%
		pay.rec%=pay.rec%+1
		gosub 1080		rem get pay rec
		if pay.eof% then return
	wend
	return

1080	rem-----get pay rec----------------------------------
	if pay.rec%>pay.hdr.no.recs% then pay.eof%=true%:return
	read #pay.file%,pay.rec%+1;    \
$include "ipypay"
	return

1090	rem-----process hrs rec------------------------------
	in.emp.no$=hrs.emp.no$
	in.eff.date$=hrs.eff.date$
	in.rate%=hrs.rate%
	in.units=hrs.units
	gosub 1390			rem process in rec
	return

1100	rem-----copy hrs rec---------------------------------
	pyo.emp.no$=hrs.emp.no$
	pyo.eff.date$=hrs.eff.date$
	pyo.interval$=emp.pay.interval$
	pyo.apply.no%=apply.no%
	pyo.reporting.cat%=hrs.rate%
	pyo.units=hrs.units
	pyo.amt=0
	pyo.extended%=false%
	gosub 2015			rem write new.pay.rec
	return

1110	rem-----get hrs rec----------------------------------
	if hrs.eof% then return
	gosub 1111			rem read hrs rec
	if hrs.eof% then return
	if hrs.deleted% \
		then	hrs.rec%=hrs.rec%+1	:\
			goto 1110	rem read again
	return

1111	rem-----read hrs.rec---------------------------------
	if hrs.rec%>hrs.hdr.no.recs% then hrs.eof%=true%:return
	read #hrs.file%,hrs.rec%+1;    \
$include "ipyhrs"
	return

1120	rem-----process rate zero----------------------------
	if units(0)=0 then return
	rate2=units(0)-emp.normal.units
	if rate2>0 \
		then	rate1=emp.normal.units	\
		else	rate1=units(0)
	gosub 1135			rem set up pay fields
	pyo.amt=fn.round(rate1*emp.rate(1))
	pyo.reporting.cat%=01
	pyo.units=rate1
	gosub 2010			rem generate new pyo rec
	if rate2<=0 then return
	pyo.amt=fn.round(rate2*emp.rate(2))
	pyo.reporting.cat%=02
	pyo.units=rate2
	gosub 2010			rem generate new pyo rec
	return

1125	rem-----process auto units---------------------------
	if emp.auto.units=0 or auto.units.overridden% \
		then	return
	if emp.status$<>"A" \
		then	return
	gosub 1135			rem set up pay fields
	pyo.amt=fn.round(emp.auto.units*emp.rate(1))
	pyo.reporting.cat%=01
	pyo.units=emp.auto.units
	gosub 2010			rem generate new pyo rec
	return

1135	rem-----set up pay fields----------------------------
	pyo.emp.no$=emp.no$
	pyo.eff.date$=common.date$
	pyo.interval$=emp.pay.interval$
	pyo.apply.no%=apply.no%
	pyo.units=0
	pyo.amt=0
	pyo.extended%=true%
	pyo.reporting.cat%=0
	return

1140	rem-----process systemwide eds-----------------------
	for i%=1 to pr1.max.sys.eds%
		if ded.sys.earn.ded$(i%)<>acceptable.type$ \
			then	goto 1141		    rem wrong type
		if not ded.sys.used%(i%) then goto 1141     rem not used
		if emp.sys.exempt%(i%)	 then goto 1141     rem emp is exempt
		pyo.reporting.cat%=32+i%
		pyo.eff.date$=common.date$
		pyo.interval$=emp.pay.interval$
		pyo.apply.no%=apply.no%
		pyo.emp.no$=emp.no$
		pyo.units=1
		pyo.extended%=true%
		earn.ded$=ded.sys.earn.ded$(i%)
		limit.used%=ded.sys.limit.used%(i%)
		ed.limit=ded.sys.limit(i%)
		amt.percent$=ded.sys.amt.percent$(i%)
		factor=ded.sys.factor(i%)
		ytd.ed=his.ytd.sys(i%)
		gosub 1155		rem calc pyo amt
		if ded.sys.earn.ded$(i%)="D" \
			then	pyo.amt=fn.ded.limit  :\
				net=net-pyo.amt
		if pyo.amt<>0 \
			then	gosub 2010	rem generate new pyo rec
1141	next i%
	return

1150	rem-----process recurring emp eds--------------------
	for i%=1 to pr1.max.emp.eds%
		if emp.ed.earn.ded$(i%)<>acceptable.type$ \
			then	goto 1151		rem wrong type
		if emp.ed.chk.cat%(i%)=0 then goto 1151 rem not used
		pyo.reporting.cat%=37+i%
		pyo.eff.date$=common.date$
		pyo.interval$=emp.pay.interval$
		pyo.apply.no%=apply.no%
		pyo.emp.no$=emp.no$
		pyo.units=1
		pyo.extended%=true%
		earn.ded$=emp.ed.earn.ded$(i%)
		limit.used%=emp.ed.limit.used%(i%)
		ed.limit=emp.ed.limit(i%)
		amt.percent$=emp.ed.amt.percent$(i%)
		factor=emp.ed.factor(i%)
		ytd.ed=his.ytd.emp(i%)
		gosub 1155		rem calc pyo amt
		if emp.ed.earn.ded$(i%)="D" \
			then	pyo.amt=fn.ded.limit  :\
				net=net-pyo.amt
		if pyo.amt<>0 \
			then	gosub 2010	rem generate new pyo rec
1151	next i%
	return

1155	rem-----calc pyo amt---------------------------------
	if limit.used% \
		then	pyo.amt=fn.taxable(ed.limit,ytd.ed,fn.ed.amt) \
		else	pyo.amt=fn.ed.amt
	pyo.amt=fn.round(pyo.amt)
	return

1160	rem-----process fwt----------------------------------
	if not ded.fwt.used% then return
	if emp.fwt.exempt% then return
	annual.equivalent.wage=(income.taxable+tips)*emp.pay.freq%- \
		ded.fwt.allowance.amt*emp.fwt.allow%
	if emp.marital$="M" \
		then	gosub 1250	rem do married fwt
	if emp.marital$="S" \
		then	gosub 1260	rem do single fwt
	fwt=fwt/emp.pay.freq%
	pyo.reporting.cat%=20
	fwt=fn.round(fwt)
	pyo.amt=fwt
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1170	rem-----process swt----------------------------------
	if not ded.swt.used% then return
	if emp.swt.exempt% then return
	if pr1.co.state$="CA" \
		then	gosub 1173 \	rem do CAL tax
		else	gosub 1175	rem do all other states
	pyo.reporting.cat%=21
	swt=fn.round(swt)
	pyo.amt=swt
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1173	rem-----do CAL tax-----------------------------------
rem
rem	assign employee to one of four statuses:
rem		1 - single
rem		2 - married less than 2 allowances
rem		3 - married 2 or more allowances
rem		4 - head of houshold
rem
	if emp.marital$ = "S"   \
		then ded.status% = 1	\
		else ded.status% = 2
	if ded.status% = 2 and emp.swt.allow% > 1	\
		then ded.status% = 3
	if emp.cal.head.of.house%	\
		then ded.status% = 4

	annual.equivalent.wage = (income.taxable + tips) * emp.pay.freq%
	if annual.equivalent.wage<cal.low.income.exempt(ded.status%) \
		then	return

	annual.equivalent.wage=annual.equivalent.wage-		\
		cal.standard.deduction(ded.status%)

	if emp.marital$="M" \
		then	agency%=calm.table%   \
		else	agency%=cals.table%
	if emp.cal.head.of.house% \
		then	agency%=calh.table%

	if ded.status% <> 1	\
		then ded.status% = 2

	if emp.swt.allow%<=10 \
		then	s.allow%=emp.swt.allow% \
		else	s.allow%=10

	temp=(fn.withhold(agency%,annual.equivalent.wage,		\
		emp.cal.ded.allow%,cal.estimated.ded.amt,		\
		withhold.num.entries%(agency%))-	\
		cal.tax.credit(s.allow%,ded.status%))/		\
		emp.pay.freq%
	if temp>0 \			rem in CA, swt can get negative,
		then	swt=swt+temp	rem but this is undesireable.
	return

1175	rem-----do all other states--------------------------
	annual.equivalent.wage = (income.taxable + tips) * emp.pay.freq%
	if pr1.co.state$="NY" \
		then	gosub 1177	rem prepare for NY
	swt=swt+fn.withhold(swt.table%,annual.equivalent.wage,		\
		emp.swt.allow%,withhold.deduction.amount(swt.table%),	\
		withhold.num.entries%(swt.table%))/emp.pay.freq%
	return

	rem @@@@@@@@@@@@@@@@@@@@@@@@@@@
	rem!!!!!!ATTENTION!!!!!!! these stupid numbers might change!!
	rem @@@@@@@@@@@@@@@@@@@@@@@@@@@

1177	rem-----prepare for NY-------------------------------
	if annual.equivalent.wage<8750 \
		then	annual.equivalent.wage=annual.equivalent.wage-750 \
		else	annual.equivalent.wage=annual.equivalent.wage-1750
	return

1180	rem-----process lwt----------------------------------
	if not ded.lwt.used% then return
	if emp.lwt.exempt% then return
	annual.equivalent.wage = (income.taxable + tips ) * emp.pay.freq%
	if (match("NEW YORK",ucase$(pr1.co.city$),1)<>0 or      \
	    match("N.Y.",ucase$(pr1.co.city$),1)<>0 or          \
	    match("N. Y.",ucase$(pr1.co.city$),1)<>0 or         \
	    match("NYC",ucase$(pr1.co.city$),1)<>0) and         \
	    pr1.co.state$="NY"                                  \
		then	gosub 1177		rem prepare for NYC
	lwt=lwt+fn.withhold(lwt.table%,annual.equivalent.wage,		\
		emp.lwt.allow%,withhold.deduction.amount(lwt.table%),	\
		withhold.num.entries%(lwt.table%))/emp.pay.freq%
	pyo.reporting.cat%=22
	lwt=fn.round(lwt)
	pyo.amt=lwt
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1190	rem-----process fica---------------------------------
	if not ded.fica.used% then return
	if emp.fica.exempt% then return
	fica = fica+(ded.fica.rate/100 * fn.taxable(ded.fica.limit,	\
		his.ytd.fica.taxable+his.ytd.tips,fica.taxable+tips))
	pyo.reporting.cat%=23
	fica=fn.round(fica)
	pyo.amt=fica
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1200	rem-----process co fica------------------------------
	if not ded.co.fica.used% then return
	if emp.fica.exempt% then return
	co.fica = ded.co.fica.rate/100. * fn.taxable(ded.co.fica.limit, \
		his.ytd.fica.taxable,fica.taxable)
	pyo.reporting.cat%=42
	co.fica=fn.round(co.fica)
	pyo.amt=co.fica
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1210	rem-----process co sui-------------------------------
	if not ded.co.sui.used% then return
	if emp.co.sui.exempt% then return
	co.sui = ded.co.sui.rate/100. * fn.taxable(ded.co.sui.limit,	\
		comb.ytd.other.taxable, comb.other.taxable )
	pyo.reporting.cat%=44
	co.sui=fn.round(co.sui)
	pyo.amt=co.sui
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1220	rem-----process co futa------------------------------
	if not ded.co.futa.used% then return
	if emp.co.futa.exempt% then return
	cur.taxable = fn.taxable(ded.co.futa.limit, \
		comb.ytd.other.taxable , comb.other.taxable)
	co.futa = ded.co.futa.rate/100. * cur.taxable	\
		- fn.min(ded.co.futa.max.credit/100. * cur.taxable , co.sui)
	pyo.reporting.cat%=43
	co.futa=fn.round(co.futa)
	pyo.amt=co.futa
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1230	rem-----process eic----------------------------------
	if not ded.eic.used% then return
	if not emp.eic.used% then return
	annual.equivalent.wage = comb.other.taxable * emp.pay.freq%
	eic = fn.min(annual.equivalent.wage,ded.eic.limit) * ded.eic.rate/100.
	if annual.equivalent.wage > ded.eic.excess.limit	\
		then eic = eic - ded.eic.excess.rate/100. *	\
			(annual.equivalent.wage - ded.eic.excess.limit)
	if eic < 0	\
		then eic = 0
	eic = eic / emp.pay.freq%
	pyo.reporting.cat%=16
	eic=fn.round(eic)
	pyo.amt=eic
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1240	rem-----process sdi----------------------------------
	if not ded.sdi.used% then return
	if emp.sdi.exempt% then return
	sdi = ded.sdi.rate/100. * fn.taxable(ded.sdi.limit,    \
			comb.ytd.other.taxable,comb.other.taxable)
	pyo.reporting.cat%=24
	sdi=fn.round(sdi)
	pyo.amt=sdi
	pyo.units=1
	if pyo.amt<>0 \
		then	gosub 2010	rem generate new pyo rec
	return

1250	rem-----do married fwt-------------------------------
	for i% = 1 to 6
		if annual.equivalent.wage>ded.fwt.mar.cutoff(i%)	\
			then	fwt=fwt+fn.min(annual.equivalent.wage-	\
				ded.fwt.mar.cutoff(i%), 		\
				ded.fwt.mar.cutoff(i%+1)-		\
				ded.fwt.mar.cutoff(i%))*		\
				ded.fwt.mar.percent(i%)/100.0
	next i%
	if annual.equivalent.wage>ded.fwt.mar.cutoff(7) 		\
		then	fwt=fwt+					\
			(annual.equivalent.wage-ded.fwt.mar.cutoff(7))* \
			ded.fwt.mar.percent(7)/100.0
	return

1260	rem-----do single fwt--------------------------------
	for i% = 1 to 6
		if annual.equivalent.wage>ded.fwt.sin.cutoff(i%)	\
			then	fwt=fwt+fn.min(annual.equivalent.wage-	\
				ded.fwt.sin.cutoff(i%), 		\
				ded.fwt.sin.cutoff(i%+1)-		\
				ded.fwt.sin.cutoff(i%))*		\
				ded.fwt.sin.percent(i%)/100.0
	next i%
	if annual.equivalent.wage>ded.fwt.sin.cutoff(7) 		\
		then	fwt=fwt+					\
		   (annual.equivalent.wage-ded.fwt.sin.cutoff(7))*	\
		   ded.fwt.sin.percent(7)/100.0
	return

1300	rem-----process vacation-----------------------------
	vac.accum=vac.accum+emp.vac.rate
	return

1310	rem-----process sick leave---------------------------
	sl.accum=sl.accum+emp.sl.rate
	return

1320	rem-----update employee record-----------------------
	emp.cur.apply.no%=apply.no%
	emp.vac.accum=emp.vac.accum+vac.accum
	emp.vac.used=emp.vac.used+vac.used
	emp.sl.accum=emp.sl.accum+sl.accum
	emp.sl.used=emp.sl.used+sl.used
	emp.comp.accum=emp.comp.accum+comp.accum
	emp.comp.used=emp.comp.used+comp.used
	return

1330	rem-----write employee record------------------------
	print #emp.file%,employee%+1;  \
$include "ipyemp"
	return

1390	rem-----process in rec-------------------------------
rem
rem	This routine will process either a PAY record or an HRS
rem	record that has just been read in.  The ON GOSUB processing
rem	is mostly a determination of the PAY.AMT for the transaction.
rem	The rest of the fields in the record are assigned values
rem	after the ON GOSUB.  The processing is
rem	determined by the value of the IN.RATE% variable which
rem	is either the PAY.REPORTING.CAT% of previously read and
rem	copied records, or the HRS.RATE% field of fresh HRS records.
rem	Note that paragraphs exist only for those rates that are
rem	valid entry rates in the HRSENT program.
rem
rem	Valid processing paragraphs are:
rem		1400	rate 0 hours
rem		1401	regular rates (1 thru 4)
rem		1402	vacation taken
rem		1403	sick leave taken
rem		1404	comp time taken
rem		1405	comp time earned
rem		1406	other explicit pay types
rem		1407	advance repay
rem		1408	fwt addon
rem		1409	swt addon
rem		1410	lwt addon
rem		1411	fica addon
rem		1420	invalid rates (error)
rem
	if emp.status$="L" and in.rate%<=4 \
		then	trash%=fn.emsg%(03)	:\
			return
	if emp.status$="T" \
		then	trash%=fn.emsg%(03)	:\
			return
	on in.rate%+1 gosub \
		1400,\			rem rate 00
		1401,\			rem rate 01
		1401,\			rem rate 02
		1401,\			rem rate 03
		1401,\			rem rate 04
		1402,\			rem rate 05 vacation taken
		1403,\			rem rate 06 sick leave taken
		1404,\			rem rate 07 comp time taken
		1405,\			rem rate 08 comp time earnd
		1406,\			rem rate 09 bonus
		1406,\			rem rate 10 tips collected
		1406,\			rem rate 11 advance
		1406,\			rem rate 12 sick pay
		1406,\			rem rate 13 vacation pay
		1406,\			rem rate 14 other excld pay
		1406,\			rem rate 15 expense reimb
		1420,\			rem rate 16 eic
		1406,\			rem rate 17 other pay
		1406,\			rem rate 18 tips reported
		1420,\			rem rate 19
		1420,\			rem rate 20 fwt
		1420,\			rem rate 21 swt
		1420,\			rem rate 22 lwt
		1420,\			rem rate 23 fica
		1420,\			rem rate 24 sdi
		1420,\			rem rate 25
		1420,\			rem rate 26
		1407,\			rem rate 27 advance repay
		1408,\			rem rate 28 fwt addon
		1409,\			rem rate 29 swt addon
		1410,\			rem rate 30 lwt addon
		1411,\			rem rate 31 fica addon
		1420,\			rem rate 32
		1420,\			rem rate 33 sys1
		1420,\			rem rate 34 sys2
		1420,\			rem rate 35 sys3
		1420,\			rem rate 36 sys4
		1420,\			rem rate 37 sys5
		1420,\			rem rate 38 emp1
		1420,\			rem rate 39 emp2
		1420,\			rem rate 40 emp3
		1420,\			rem rate 41
		1420,\			rem rate 42 company fica
		1420,\			rem rate 43 company futa
		1420,\			rem rate 44 company sui
		1420,\			rem rate 45
		1420,\			rem rate 46 other co cost
		1420,\			rem rate 47
		1420,\			rem rate 48
		1420,\			rem rate 49
		1420			rem rate 50 other ded

	pyo.reporting.cat%=in.rate%
	pyo.eff.date$=in.eff.date$
	pyo.interval$=emp.pay.interval$
	pyo.apply.no%=apply.no%
	pyo.emp.no$=in.emp.no$
	pyo.units=in.units
	pyo.extended%=true%
	if in.rate%<>0 \
		then	gosub 2010	rem generate.new.pyo.rec
	return

1400	rem-----rate 00--------------------------------------
	units(in.rate%)=units(in.rate%)+in.units
	auto.units.overridden%=true%
	pyo.amt=0
	return

1401	rem-----rate 01,02,03,04-----------------------------
	units(in.rate%)=units(in.rate%)+in.units
	if in.rate%=1 then auto.units.overridden%=true%
	pyo.amt=in.units*emp.rate(in.rate%)
	return

1402	rem-----rate 05 vacation taken-----------------------
	pyo.amt=0
	vac.used=vac.used+in.units
	return

1403	rem-----rate 06 sick leave taken---------------------
	pyo.amt=0
	sl.used=sl.used+in.units
	return

1404	rem-----rate 07 comp time taken----------------------
	pyo.amt=0
	comp.used=comp.used+in.units
	return

1405	rem-----rate 08 comp time earnd----------------------
	pyo.amt=0
	comp.accum=comp.accum+in.units
	return

1406	rem-----rate 09 other normal pay types---------------
	pyo.amt=in.units
	in.units=1
	return

1407	rem-----rem rate 27 advance repay--------------------
	pyo.amt=in.units
	in.units=1
	return

1408	rem-----rem rate 28 fwt addon------------------------
	pyo.amt=in.units
	fwt=fwt+in.units
	in.units=1
	return

1409	rem-----rem rate 29 swt addon------------------------
	pyo.amt=in.units
	swt=swt+in.units
	in.units=1
	return

1410	rem-----rem rate 30 lwt addon------------------------
	pyo.amt=in.units
	lwt=lwt+in.units
	in.units=1
	return

1411	rem-----rem rate 31 fica addon-----------------------
	pyo.amt=in.units
	fica=fica+in.units
	in.units=1
	return

1420	rem-----invalid rates--------------------------------
	print "blooooey"
	stop

2010	rem-----generate new pyo rec-------------------------
	gosub 2020			rem accumulate pyo amt
	gosub 2015			rem write new pyo rec
	return

2012	rem-----put pays into pyos---------------------------
	pyo.emp.no$		=pay.emp.no$
	pyo.eff.date$		=pay.eff.date$
	pyo.interval$		=pay.interval$
	pyo.apply.no%		=pay.apply.no%
	pyo.reporting.cat%	=pay.reporting.cat%
	pyo.units		=pay.units
	pyo.amt 		=pay.amt
	pyo.extended%		=pay.extended%
	return

2015	rem-----write new pyo rec----------------------------
	pyo.hdr.no.recs%=pyo.hdr.no.recs%+1
	print #pyo.file%,pyo.hdr.no.recs%+1; \
$include "ipypyo"
	return

2020	rem-----accumulate pyo amt---------------------------
rem
rem	This rtn is an ON GOSUB used to accumulate pay amounts in
rem	their proper accumulators.  The accumulated amounts are
rem	used for withholding calculations.  (in APPLY3, these same
rem	calculations are used for HIS file updating.
rem
rem	The following are the accumulators to be used:
rem		income.taxable
rem		other.taxable
rem		other.nontaxable
rem		fica.taxable	  (does not include tips)
rem		tips collected
rem		tips reported
rem
rem	gross pay  = income.taxable+other.taxable+other.nontaxable+tips
rem
rem	accumulation codes are as follows:
rem		2030 - do not accumulate
rem		2040 - income.taxable,fica.taxable	(exclusion type 1)
rem		2050 - income.taxable			(exclusion type 2)
rem		2060 - other.taxable,fica.taxable	(exclusion type 3)
rem		2070 - other.nontaxable 		(exclusion type 4)
rem		2080 - by applicable exclusion type as above
rem		2090 - tips collected
rem		2100 - tips reported
rem
	on pyo.reporting.cat% gosub \
		2040,	\ (01)="REGULAR PAY"
		2040,	\ (02)="OVERTIME PAY"       \ from PR1 file
		2040,	\ (03)="SPECIAL OT PAY"     \ from PR1 file
		2080,	\ (04)="COMMISSION"         \ from PR1 file
		2030,	\ (05)="VACATION TAKEN"
		2030,	\ (06)="SICK LVE TAKEN"
		2030,	\ (07)="COMP TIME TAKEN"
		2030,	\ (08)="COMP TIME EARND"
		2040,	\ (09)="BONUS"
		2090,	\ (10)="TIPS COLLECTED"
		2030,	\ (11)="ADVANCE"
		2040,	\ (12)="SICK PAY"
		2040,	\ (13)="VACATION PAY"
		2070,	\ (14)="OTHER EXCLD PAY"
		2030,	\ (15)="EXPENSE REIMB"
		2030,	\ (16)="EIC"
		2040,	\ (17)="OTHER PAY"
		2100,	\ (18)="TIPS REPORTED"
		2030,	\ (19)=""
		2030,	\ (20)="FWT"
		2030,	\ (21)="SWT"
		2030,	\ (22)="LWT"
		2030,	\ (23)="FICA"
		2030,	\ (24)="SDI"
		2030,	\ (25)=""
		2030,	\ (26)=""
		2030,	\ (27)="ADVANCE REPAY"
		2030,	\ (28)="FWT ADD-ON"
		2030,	\ (29)="SWT ADD-ON"
		2030,	\ (30)="LWT ADD-ON"
		2030,	\ (31)="FICA ADD-ON"
		2030,	\ (32)=""
		2080,	\ (33)="SYS1"          \  from sys1
		2080,	\ (34)="SYS2"          \  from sys2
		2080,	\ (35)="SYS3"          \  from sys3
		2080,	\ (36)="SYS4"          \  from sys4
		2080,	\ (37)="SYS5"          \  from sys5
		2080,	\ (38)="EMP1"          \  from emp1
		2080,	\ (39)="EMP2"          \  from emp2
		2080,	\ (40)="EMP3"          \  from emp3
		2030,	\ (41)=""
		2030,	\ (42)="COMPANY FICA"
		2030,	\ (43)="COMPANY FUTA"
		2030,	\ (44)="COMPANY SUI"
		2030,	\ (45)=""
		2030,	\ (46)="OTHER CO COST"
		2030,	\ (47)=""
		2030,	\ (48)=""
		2030,	\ (49)=""
		2030	rem  (50)="OTHER DED"
	return

2030	rem-----do not accumulate----------------------------
	return

2040	rem-----income.taxable,fica.taxable-type 1-----------
	income.taxable=income.taxable+pyo.amt
	fica.taxable=fica.taxable+pyo.amt
	return

2050	rem-----income.taxable-type 2------------------------
	income.taxable=income.taxable+pyo.amt
	return

2060	rem-----other.taxable,fica.taxable-type 3------------
	other.taxable=other.taxable+pyo.amt
	fica.taxable=fica.taxable+pyo.amt
	return

2070	rem-----other.nontaxable-type 4----------------------
	other.nontaxable=other.nontaxable+pyo.amt
	return

2080	rem-----by applicable exclusion type as above--------
	if pyo.reporting.cat%=4 \
		then	exclusion.type%=emp.rate4.exclusion% :\
			gosub 2110   :\ 	rem accumulate
			return
	if pyo.reporting.cat%>=33 and \
	   pyo.reporting.cat%<=37     \
		then	gosub 2082   :\ 	rem do sys ed
			return
	if pyo.reporting.cat%>=38 and \
	   pyo.reporting.cat%<=40     \
		then	gosub 2084   :\ 	rem do emp ed
			return
	print "bloooey"
	stop

2082	rem-----do sys ed-----------------------------------
	if ded.sys.earn.ded$(pyo.reporting.cat%-32)="E" \
		then	exclusion.type%=ded.sys.exclusion%	\
				(pyo.reporting.cat%-32) 	:\
			gosub 2110    \ 	rem accumulate
		else	other.ded=other.ded+pyo.amt
	return

2084	rem-----do emp ed-----------------------------------
	if emp.ed.earn.ded$(pyo.reporting.cat%-37)="E" \
		then	exclusion.type%=emp.ed.exclusion%	\
				(pyo.reporting.cat%-37) 	:\
			gosub 2110    \ 	rem accumulate
		else	other.ded=other.ded+pyo.amt
	return

2090	rem-----tips collected-------------------------------
	tips=tips+pyo.amt
	return

2100	rem-----tips reported--------------------------------
	tips=tips+pyo.amt
	tips.reported=tips.reported+pyo.amt
	return

2110	rem-----accumulate-----------------------------------
	on exclusion.type% gosub \
		2040,\		rem type 1
		2050,\		rem type 2
		2060,\		rem type 3
		2070		rem type 4
	return
