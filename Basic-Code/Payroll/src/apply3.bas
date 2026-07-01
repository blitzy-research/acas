$include "ipycomm"
$include "ipyapcom"
prgname$="APPLY3     JAN.  17, 1980 "
rem----------------------------------------------------------
rem
rem	A  P  P  L  Y  3
rem
rem		CREATE CHECK FILE AND UPDATE HIS AND COH FILES
rem
rem	SECTION THREE OF PAYROLL CALCULATION PROGRAM
rem
rem	P A Y R O L L	   S Y S T E M
rem
rem	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="APPLY3"
function.name$="PAYROLL APPLICATION -- SECTION THREE"

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
$include "zdmslit"
$include "zdmsmsg"
$include "zdmsemsg"
$include "zdmsclr"

rem----------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem----------------------------------------------------------

del.file%=1
glx.file%=2
glx.len%=116

dim emsg$(05)
emsg$(01)="PY561"               rem dummy msg for fre stmt
emsg$(02)="PY562 NOT PROPERLY CHAINED"
emsg$(03)="PY563 NET PAY EXCEEDS EMPLOYEE MAXIMUM"
emsg$(04)="PY564 NET PAY EXCEEDS SYSTEM LIMIT - CHECK WILL BE VOIDED"
emsg$(05)="PY565 NET PAY CALCULATED FOR LESS THAN ZERO - NO CHECK MADE"

$include "ipystat"
$include "ipydmemp"
$include "ipydmchk"
$include "ipydmhis"
$include "ipydmded"
$include "ipydmcoh"
$include "ipyckcat"
$include "zdateio"
$include "fpyap3"

dim sys 	(5)
dim emp 	(3)
dim units	(4)
dim acct.amt	(pr2.no.acts%)
dim dist.amt	(pr1.max.dist.accts%)

def fn.decompose.date%(date$)
	dy%=val(mid$(date$,5,2))
	mo%=val(mid$(date$,3,2))
	yr%=val(mid$(date$,1,2))
	return
fend

def fn.quarter%(date$)
	trash%=fn.decompose.date%(date$)
	if mo%=01 or mo%=02 or mo%=03 then fn.quarter%=1:return
	if mo%=04 or mo%=05 or mo%=06 then fn.quarter%=2:return
	if mo%=07 or mo%=08 or mo%=09 then fn.quarter%=3:return
	if mo%=10 or mo%=11 or mo%=12 then fn.quarter%=4:return
fend

def fn.round(rr)=(int((rr*100)+.5))/100

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
		then	crt.data$(07)="free storage: "+str$(fre)  :\
			trash%=fn.lit%(07)
wend

rem----------------------------------------------------------
rem
rem	E N D	  O F	  J O B
rem
rem----------------------------------------------------------

gosub 800			rem write.pay.hdr
close pay.file%
gosub 783			rem delete pay 102
gosub 787			rem rename(pay.102=pay.101)
gosub 790			rem rename(pay.101=pay.100)
gosub 810			rem update his hdr
gosub 760			rem open,write,close coh file
if pr1.gl.used% \
	then	gosub 820 :\	rem create GJB file
		gosub 850 :\	rem write out GJB file
		gosub 860 :\	rem close GJB file

gosub 775			rem write chk hdr
gosub 990			rem close.all.files
gosub 995			rem rename(chk.101=chk.100)

$include "zeoj"

rem----------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem----------------------------------------------------------

200	rem-----display set up screen------------------------
	trash%=fn.lit%(1)	rem function name
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
	trash%=fn.lit%(4)	rem PROCESSING EMPLOYEE NUMBER:
	trash%=fn.lit%(2)	rem CURRENT EMPLOYEE STATUS IS:
	return

400	rem-----process employee-----------------------------
	gosub 1000			rem clear.employee.accums
	gosub 1020			rem read.next.employee.record
	gosub 1010			rem display employee number
	gosub 1030			rem display employee status
	trash%=fn.msg%(null$)		rem clear error msg line

	if emp.status$="D"              \
		then	return

	if match(emp.pay.interval$,extension.intervals$,1)=0 \
		then	return

	gosub 1040			rem set up chk rec
	gosub 1050			rem read.matching.history.record

	while not pay.eof% and val(left$(pay.emp.no$,4))=employee%
		gosub 1060		rem process pay rec
		gosub 1070		rem select a pay rec
	wend

	gosub 1200			rem calculate gross and net
	gosub 1300			rem distribute to acct table
	gosub 1315			rem distribute offset amounts
	gosub 815			rem increment COH fields
	gosub 1320			rem update history record
	gosub 1330			rem write.history.record
	gosub 1335			rem test amt against maximums
	gosub 1340			rem generate check record
	return

500	rem-----set up files---------------------------------
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
	gosub 670			rem open his file
	gosub 680			rem read.his.hdr
	gosub 690			rem get act file
	gosub 700			rem get act hdr rec
	gosub 710			rem get coh file
	gosub 765			rem set COH fields for this run
	gosub 770			rem create new check file
	gosub 777			rem delete hrs.bak
	gosub 780			rem rename(hrs.bak=hrs)
	return

540	rem-----open pay file--------------------------------
	pay.exists%=false%
	if end #pay.file% then 541
	open fn.file.name.out$(pay.name$,"100",pr1.pyo.drive%,pw$,pms$) \
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

670	rem-----open his file--------------------------------
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

690	rem-----get act file---------------------------------
	act.exists%=false%
	if end #act.file% then 691
	open fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pms$) \
		recl act.len%  as act.file%
	act.exists%=true%
691	rem-----here if act file not present-----------------
	return

700	rem-----get act hdr rec------------------------------
	read #act.file%,1;     \
$include "ipyacthd"
	return

710	rem-----get coh file---------------------------------
	gosub 720			rem open coh if present
	if coh.exists% \
		then	gosub 730 :\	rem read coh file
			close coh.file% :\
		else	gosub 740 :\	rem create coh file
			close coh.file%  :\
			gosub 750 :\	rem initialize coh fields
			gosub 760	rem open,write,close coh rec
	return

720	rem-----open coh if present--------------------------
	coh.exists%=false%
	if end #coh.file% then 721
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
		as coh.file%
	coh.exists%=true%
721	rem-----here if coh file not present-----------------
	return

730	rem-----read coh file--------------------------------
	read #coh.file%;   \
$include "ipycoh"
	return

740	rem-----create coh file------------------------------
	create fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
		as coh.file%
	return

750	rem-----initialize coh fields------------------------
	coh.last.apply.no%=		apply.no%
	coh.interval$=			interval$
	coh.starting.up%=		false%
	return

760	rem-----open,write,close coh record------------------
	gosub 720			rem open coh file
	print #coh.file%;    \
$include "ipycoh"
	close coh.file%
	return

765	rem-----set COH fields for this run------------------
	coh.last.apply.no%=		apply.no%
	coh.interval$=			interval$
	coh.starting.up%=		false%

	quarter%=fn.quarter%(pr2.check.date$)
	trash%=fn.decompose.date%(pr2.check.date$)
	if dy%>=1 and dy%<=7	then	week%=1
	if dy%>=8 and dy%<=15	then	week%=2
	if dy%>=16 and dy%<=22	then	week%=3
	if dy%>=23		then	week%=4
	if mo%=1 or mo%=4 or mo%=7 or mo%=10	then	week%=week%
	if mo%=2 or mo%=5 or mo%=8 or mo%=11	then	week%=week%+4
	if mo%=3 or mo%=6 or mo%=9 or mo%=12	then	week%=week%+8
	coh.date$(week%)=pr2.check.date$
	return

770	rem-----create new check file for output-------------
	if pr1.debugging% \
		then	crt.data$(07)="CREATING CHK FILE"       :\
			trash%=fn.lit%(07)
	create fn.file.name.out$(chk.name$,"100",pr1.chk.drive%,pw$,pms$) \
		recl chk.len%  as chk.file%
	chk.hdr.no.recs%=0
	chk.hdr.interval$=left$(interval$,1)
	chk.hdr.apply.no%=apply.no%
	chk.hdr.register.printed%=false%
	chk.hdr.checks.printed%=false%
	chk.hdr.slow.from.date$=left$(from.slow.date$,6)
	chk.hdr.fast.from.date$=left$(from.fast.date$,6)
	chk.hdr.to.date$=left$(to.date$,6)
	gosub 775			rem write chk hdr
	return

775	rem-----write chk hdr--------------------------------
	print #chk.file%,1;	 \
$include "ipychkhd"
	return

777	rem-----delete hrs.bak-------------------------------
	if end #del.file% then 776
	open fn.file.name.out$(hrs.name$,"102",pr1.hrs.drive%,pw$,pms$) \
		as del.file%
	delete del.file%
776	rem-----here if del file not present-----------------
	return

780	rem-----rename(hrs.bak=hrs)--------------------------
	trash%=rename	  \
		(fn.file.name.out$(hrs.name$,"102",pr1.hrs.drive%,pw$,pms$), \
		 fn.file.name.out$(hrs.name$,"101",pr1.hrs.drive%,pw$,pms$))
	return

783	rem-----delete pay 102-------------------------------
	if end #del.file% then 784
	open fn.file.name.out$(pay.name$,"102",pr1.pyo.drive%,pw$,pms$) \
		as del.file%
	delete del.file%
784	rem-----here if del file not present-----------------
	return

787	rem-----rename(pay.102=pay.101)----------------------
	trash%=rename	  \
		(fn.file.name.out$(pay.name$,"102",pr1.pyo.drive%,pw$,pms$), \
		 fn.file.name.out$(pay.name$,"101",pr1.pyo.drive%,pw$,pms$))
	return

790	rem-----rename(pay.101=pay.100)----------------------
	trash%=rename	  \
		(fn.file.name.out$(pay.name$,"101",pr1.pyo.drive%,pw$,pms$), \
		 fn.file.name.out$(pay.name$,"100",pr1.pyo.drive%,pw$,pms$))
	return

800	rem-----write pay hdr--------------------------------
	print #pay.file%,1;    \
$include "ipypayhd"
	return

810	rem-----update his hdr-------------------------------
	his.hdr.to.date$=to.date$
	return

815	rem-----increment COH accumulators-------------------
	coh.qtd.income.taxable=coh.qtd.income.taxable+income.taxable
	coh.qtd.other.taxable=coh.qtd.other.taxable+other.taxable
	coh.qtd.other.nontaxable=coh.qtd.other.nontaxable+other.nontaxable
	coh.qtd.fica.taxable=coh.qtd.fica.taxable+fica.taxable
	coh.qtd.tips=coh.qtd.tips+tips
	coh.qtd.net=coh.qtd.net+net
	coh.qtd.eic.credit=coh.qtd.eic.credit+eic
	coh.qtd.fwt.liab=coh.qtd.fwt.liab+fwt
	coh.qtd.swt.liab=coh.qtd.swt.liab+swt
	coh.qtd.lwt.liab=coh.qtd.lwt.liab+lwt
	coh.qtd.fica.liab=coh.qtd.fica.liab+fica
	coh.qtd.sdi.liab=coh.qtd.sdi.liab+sdi
	coh.qtd.co.futa.liab=coh.qtd.co.futa.liab+co.futa
	coh.qtd.co.fica.liab=coh.qtd.co.fica.liab+co.fica
	coh.qtd.co.sui.liab=coh.qtd.co.sui.liab+co.sui
	for i%=1 to pr1.max.sys.eds%
		coh.qtd.sys(i%)=coh.qtd.sys(i%)+sys(i%)
		coh.ytd.sys(i%)=coh.ytd.sys(i%)+sys(i%)
	next i%
	for i%=1 to pr1.max.emp.eds%
		coh.qtd.emp(i%)=coh.qtd.emp(i%)+emp(i%)
		coh.ytd.emp(i%)=coh.ytd.emp(i%)+emp(i%)
	next i%
	coh.qtd.other.ded=coh.qtd.other.ded+other.ded
	for i%=1 to 4
		coh.qtd.units(i%)=coh.qtd.units(i%)+units(i%)
		coh.ytd.units(i%)=coh.ytd.units(i%)+units(i%)
	next i%
	coh.qtd.comp.time.earned=coh.qtd.comp.time.earned+comp.earned
	coh.qtd.comp.time.taken=coh.qtd.comp.time.taken+comp.taken
	coh.qtd.vac.earned=coh.qtd.vac.earned+emp.vac.rate
	coh.qtd.vac.taken=coh.qtd.vac.taken+vac.taken
	coh.qtd.sl.earned=coh.qtd.sl.earned+emp.sl.rate
	coh.qtd.sl.taken=coh.qtd.sl.taken+sl.taken

	coh.ytd.income.taxable=coh.ytd.income.taxable+income.taxable
	coh.ytd.other.taxable=coh.ytd.other.taxable+other.taxable
	coh.ytd.other.nontaxable=coh.ytd.other.nontaxable+other.nontaxable
	coh.ytd.fica.taxable=coh.ytd.fica.taxable+fica.taxable
	coh.ytd.tips=coh.ytd.tips+tips
	coh.ytd.net=coh.ytd.net+net
	coh.ytd.eic.credit=coh.ytd.eic.credit+eic
	coh.ytd.fwt.liab=coh.ytd.fwt.liab+fwt
	coh.ytd.swt.liab=coh.ytd.swt.liab+swt
	coh.ytd.lwt.liab=coh.ytd.lwt.liab+lwt
	coh.ytd.fica.liab=coh.ytd.fica.liab+fica
	coh.ytd.sdi.liab=coh.ytd.sdi.liab+sdi
	coh.ytd.co.futa.liab=coh.ytd.co.futa.liab+co.futa
	coh.ytd.co.fica.liab=coh.ytd.co.fica.liab+co.fica
	coh.ytd.co.sui.liab=coh.ytd.co.sui.liab+co.sui
	coh.ytd.other.ded=coh.ytd.other.ded+other.ded
	coh.ytd.comp.time.earned=coh.ytd.comp.time.earned+comp.earned
	coh.ytd.comp.time.taken=coh.ytd.comp.time.taken+comp.taken
	coh.ytd.vac.earned=coh.ytd.vac.earned+emp.vac.rate
	coh.ytd.vac.taken=coh.ytd.vac.taken+vac.taken
	coh.ytd.sl.earned=coh.ytd.sl.earned+emp.sl.rate
	coh.ytd.sl.taken=coh.ytd.sl.taken+sl.taken

	coh.tax(week%)=coh.tax(week%)  +   ((fwt+fica+co.fica)-eic)
	return

820	rem-----create GJB file------------------------------
	gosub 900			rem delete GJB.BAK
	gosub 910			rem rename GJB.BAK<--GJB if there
	if from.fast.date$<from.slow.date$ \
		then	earliest.date$=from.fast.date$ \
		else	earliest.date$=from.slow.date$
	glx.date$=		fn.date.out$(common.date$)
	glx.reference$= 	\
		"PY:"                           +\
		extension.intervals$		+\
		" "                             +\
		fn.date.out$(earliest.date$)	+\
		" TO "                          +\
		fn.date.out$(to.date$)

rem format of GJB reference field is:
rem		PY:aa #nn mm/dd/yy to mm/dd/yy
rem	where aa is extension interval letters
rem	      nn is application number

	create fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,"100",\
		pr1.glx.drive%,pw$,pms$) \
		recl glx.len%		\
		as glx.file%
	return

850	rem-----write out GJB file---------------------------
	x%=1
	while x%<=pr2.no.acts%
		act.rec%=x%
		if acct.amt(act.rec%)=0 then goto 851	rem break
		gosub 870		rem read act rec
		gosub 880		rem build GJB record
		gosub 890		rem write GJB record
851
		x%=x%+1
	wend
	return

860	rem-----close GJB file-------------------------------
	close glx.file%
	return

870	rem-----read act rec---------------------------------
	read #act.file%,act.rec%+1;    \
$include "ipyact"
	return

880	rem-----build GJB record-----------------------------
	gjb.co.no$=		"0"
	gjb.dept.no$=		right$(act.no$,2)
	gjb.acct.no$=		left$(act.no$,4)
	gjb.acct.name$= 	left$(act.desc$+blank$,30)
	gjb.eff.date$=		glx.date$
	gjb.amt=		abs(acct.amt(act.rec%))
	gosub 883			rem determine GJB.DR.CR$
	gjb.ref$=		glx.reference$
	gjb.delete.flag=	false%
	return

883	rem-----determine GJB.DR.CR$-------------------------
	if left$(gjb.acct.no$,1)="0" or  \
	   left$(gjb.acct.no$,1)="4" or  \
	   left$(gjb.acct.no$,1)="5"     \
		then	debits.normal%=true%   \
		else	debits.normal%=false%
	if debits.normal%		\
		then	gjb.dr.cr$="D"  \
		else	gjb.dr.cr$="C"
	if acct.amt(act.rec%)<0 \
		then	gosub 885	rem swap dr/cr
	return

885	rem-----swap dr/cr-----------------------------------
	if gjb.dr.cr$="D" \
		then	gjb.dr.cr$="C" \
		else	gjb.dr.cr$="D"
	return

890	rem-----write GJB record-----------------------------
	gjb.rec%=gjb.rec%+1
	print #glx.file%,gjb.rec%;    \
		GJB.CO.NO$,\
		GJB.DEPT.NO$,\
		GJB.ACCT.NO$,\
		GJB.ACCT.NAME$,\
		GJB.EFF.DATE$,\
		GJB.AMT,\
		GJB.DR.CR$,\
		GJB.REF$,\
		GJB.DELETE.FLAG
	return

900	rem-----delete GJB.BAK-------------------------------
	if end #del.file% then 901
	open fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,\
		"101",pr1.glx.drive%,pw$,pms$)    \
		as del.file%
	delete del.file%
901	rem-----here if no bak file exists-------------------
	return

910	rem-----rename GJB.BAK<--GJB if there----------------
	trash%=rename	  \
		(fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,        \
			"101",pr1.glx.drive%,pw$,pms$),                 \
		 fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,        \
			"100",pr1.glx.drive%,pw$,pms$))
	return

990	rem-----close all files------------------------------
	close chk.file%
	close emp.file%
	close his.file%
	return

995	rem-----rem rename(chk.101=chk.100)------------------
	trash%=rename	  \
		(fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$), \
		 fn.file.name.out$(chk.name$,"100",pr1.chk.drive%,pw$,pms$))
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
	vac.taken		=zero
	sl.taken		=zero
	comp.taken		=zero
	comp.earned		=zero
	fwt			=zero
	swt			=zero
	lwt			=zero
	fica			=zero
	co.fica 		=zero
	co.futa 		=zero
	co.sui			=zero
	employer.costs		=zero
	return

1010	rem-----display employee number----------------------
	crt.data$(05)=emp.no$
	trash%=fn.lit%(5)
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
		then	crt.data$(03)="ACTIVE    "      :\
			trash%=fn.lit%(03)		:\
			return
	if emp.status$="O" or emp.status$="L" \
		then	crt.data$(03)="ON-LEAVE  "      :\
			trash%=fn.lit%(03)		:\
			return
	if emp.status$="T" \
		then	crt.data$(03)="TERMINATED"      :\
			trash%=fn.lit%(03)		:\
			return
	if emp.status$="D" \
		then	crt.data$(03)="DELETED   "      :\
			trash%=fn.lit%(03)		:\
			return
	print "blooey":stop

1040	rem-----set up check record--------------------------
	chk.emp.no$=emp.no$
	chk.interval$=emp.pay.interval$
	chk.check.no$="NONE "
	for n%=1 to pr1.max.chk.cats%
		chk.amt(n%)=zero
	next n%
	return

1050	rem-----read matching history record-----------------
	read #his.file%,employee%+1;	\
$include "ipyhis"
	return

1060	rem-----process pay rec------------------------------
	gosub 1390			rem accumulate amt for his and chk
	gosub 2020			rem accumulate amt for coh and his
	return

1070	rem-----select a pay rec-----------------------------
	pay.rec%=pay.rec%+1
	gosub 1080			rem get pay rec
	if pay.eof% then return
	while not pay.extended%
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

1200	rem-----calculate gross and net----------------------
	gross=income.taxable+other.taxable+other.nontaxable+tips
	net=(gross+eic)-(fwt+swt+lwt+fica+sdi+other.ded)
	return

1300	rem-----distribute to acct table---------------------
	gosub 1310			rem determine distributable pay
	for x%=1 to pr1.max.dist.accts%
		if emp.dist.percent(x%)<>0 \
			then	dist.amt(x%)=		\
				   fn.round((emp.dist.percent(x%)/100)* \
				   distributable.pay)
	next x%
	gosub 1312			rem assure that dist amts are exact
	for x%=1 to pr1.max.dist.accts%
		acct.amt(emp.dist.acct%(x%))=acct.amt(emp.dist.acct%(x%))+\
			dist.amt(x%)
	next x%
	return

1310	rem-----determine distributable pay------------------
	distributable.pay=     \
		income.taxable		+\
		other.taxable		+\
		other.nontaxable
	if true% \
		then	distributable.pay=distributable.pay+ \
				employer.costs
	if true% \
		then	distributable.pay=distributable.pay+ \
				(tips-tips.reported)
	return

1312	rem-----assure that dist amts are exact--------------
	temp=0
	for x%=1 to pr1.max.dist.accts%
		temp=temp+dist.amt(x%)
	next x%
	if temp=distributable.pay \
		then	return
	temp=distributable.pay-temp	rem temp is difference
	x%=1
	while emp.dist.percent(x%)=0
		x%=x%+1
	wend
	dist.amt(x%)=dist.amt(x%)+temp
	return

1315	rem-----distribute offset amounts--------------------

rem
rem			  DR		       CR
rem	EARNINGS	 DIST(+)	      CASH(-)
rem	WITHHELD	 CASH(+)	   LIAB.ACCT(+)
rem	CO.COSTS	 DIST(+)	   LIAB.ACCT(+)
rem	EIC		 LIAB(-)	      CASH(-)
rem
rem	CASH acct is from PR1
rem	DIST accts are from EMP record
rem	LIAB accts are from EMP record and DED file
rem	EIC.CREDIT.ACCT is from DED file

rem CALCULATE EARNINGS:
	acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)-\
		(gross-tips.reported)

rem CALCULATE WITHHOLDING:
	acct.amt(ded.fwt.acct.no%)=acct.amt(ded.fwt.acct.no%)+fwt
	acct.amt(ded.swt.acct.no%)=acct.amt(ded.swt.acct.no%)+swt
	acct.amt(ded.lwt.acct.no%)=acct.amt(ded.lwt.acct.no%)+lwt
	acct.amt(ded.fica.acct.no%)=acct.amt(ded.fica.acct.no%)+fica
	acct.amt(ded.sdi.acct.no%)=acct.amt(ded.sdi.acct.no%)+sdi
	total.withheld=fwt+swt+lwt+fica+sdi
	for i%=1 to pr1.max.sys.eds%
		if ded.sys.earn.ded$(i%)="D" \
			then	acct.amt(ded.sys.acct.no%(i%))= 	\
				acct.amt(ded.sys.acct.no%(i%))+sys(i%)	:\
				total.withheld=total.withheld+sys(i%)
	next i%
	for i%=1 to pr1.max.emp.eds%
		if emp.ed.earn.ded$(i%)="D" \
			then	acct.amt(emp.ed.acct.no%(i%))=		\
				acct.amt(emp.ed.acct.no%(i%))+emp(i%)	:\
				total.withheld=total.withheld+emp(i%)
	next i%
	acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)+\
		total.withheld

rem CALCULATE EIC:
	acct.amt(ded.eic.acct.no%)=acct.amt(ded.eic.acct.no%)-eic
	acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)-\
		eic

rem CALCULATE COMPANY COSTS:
	acct.amt(ded.co.fica.acct.no%)=acct.amt(ded.co.fica.acct.no%)+\
		co.fica
	acct.amt(ded.co.futa.acct.no%)=acct.amt(ded.co.futa.acct.no%)+\
		co.futa
	acct.amt(ded.co.sui.acct.no%)=acct.amt(ded.co.sui.acct.no%)+\
		co.sui
	return

1320	rem-----update history record------------------------
	net=(income.taxable+other.taxable+other.nontaxable+tips+eic)-	\
	    (fwt+swt+lwt+fica+sdi+other.ded)
	his.qtd.income.taxable=his.qtd.income.taxable	+income.taxable
	his.qtd.other.taxable=his.qtd.other.taxable	+other.taxable
	his.qtd.other.nontaxable=his.qtd.other.nontaxable+other.nontaxable
	his.qtd.fica.taxable=his.qtd.fica.taxable	+fica.taxable
	his.qtd.tips=his.qtd.tips		+tips
	his.qtd.net=his.qtd.net 	+net
	his.qtd.eic=his.qtd.eic 	+eic
	his.qtd.fwt=his.qtd.fwt 	+fwt
	his.qtd.swt=his.qtd.swt 	+swt
	his.qtd.lwt=his.qtd.lwt 	+lwt
	his.qtd.fica=his.qtd.fica	+fica
	his.qtd.sdi=his.qtd.sdi 	+sdi
	his.qtd.other.ded=his.qtd.other.ded		+other.ded
	his.ytd.income.taxable=his.ytd.income.taxable	+income.taxable
	his.ytd.other.taxable=his.ytd.other.taxable	+other.taxable
	his.ytd.other.nontaxable=his.ytd.other.nontaxable+other.nontaxable
	his.ytd.fica.taxable=his.ytd.fica.taxable	+fica.taxable
	his.ytd.tips=his.ytd.tips		+tips
	his.ytd.net=his.ytd.net 		+net
	his.ytd.eic=his.ytd.eic 		+eic
	his.ytd.fwt=his.ytd.fwt 		+fwt
	his.ytd.swt=his.ytd.swt 		+swt
	his.ytd.lwt=his.ytd.lwt 		+lwt
	his.ytd.fica=his.ytd.fica		+fica
	his.ytd.sdi=his.ytd.sdi 		+sdi
	his.ytd.other.ded=his.ytd.other.ded	+other.ded
	for x%=1 to 5
		his.qtd.sys(x%)=his.qtd.sys(x%) +sys(x%)
		his.ytd.sys(x%)=his.ytd.sys(x%) +sys(x%)
	next x%
	for x%=1 to 3
		his.qtd.emp(x%)=his.qtd.emp(x%) +emp(x%)
		his.ytd.emp(x%)=his.ytd.emp(x%) +emp(x%)
	next x%
	for x%=1 to 4
		his.qtd.units(x%)=his.qtd.units(x%)	+units(x%)
		his.ytd.units(x%)=his.ytd.units(x%)	+units(x%)
	next x%
	return

1330	rem-----write history record-------------------------
	print #his.file%,employee%+1;	 \
$include "ipyhis"
	return


1335	rem-----test amt against maximums--------------------
	if net>emp.max.pay \
		then	trash%=fn.emsg%(03)
	if net>pr1.void.check.amt and pr1.void.chks.over.max% \
		then	trash%=fn.emsg%(04)
	return

1340	rem-----generate check record------------------------
	chk.amt(01)=   \			rem GROSS
		chk.amt(02)		+\
		chk.amt(03)		+\
		chk.amt(04)		+\
		chk.amt(05)		+\
		chk.amt(06)		+\
		chk.amt(07)

	chk.amt(08)=   \			rem NET
		chk.amt(01)		-\
		(chk.amt(09)		+\
		 chk.amt(10)		+\
		 chk.amt(11)		+\
		 chk.amt(12)		+\
		 chk.amt(13)		+\
		 chk.amt(14)		+\
		 chk.amt(15)		+\
		 chk.amt(16))
	if chk.amt(01)=0 and chk.amt(02)=0 and chk.amt(03)=0 and \
	   chk.amt(04)=0 and chk.amt(05)=0 and chk.amt(06)=0 and \
	   chk.amt(07)=0 and chk.amt(08)=0 and chk.amt(09)=0 and \
	   chk.amt(10)=0 and chk.amt(11)=0 and chk.amt(12)=0 and \
	   chk.amt(13)=0 and chk.amt(14)=0 and chk.amt(15)=0 and \
	   chk.amt(16)=0     \
		then	return
	if chk.amt(08)<0 \		rem net
		then	trash%=fn.emsg%(05)	:\
			return
	chk.hdr.no.recs%=chk.hdr.no.recs%+1
	print #chk.file%,chk.hdr.no.recs%+1;	\
$include "ipychk"
	return

1390	rem-----accumulate amt for his and chk---------------
rem
rem	This routine will accumulate the pay.amt
rem	that has just been read in into the fields required for
rem	updating some of the fields on the HIS file and for
rem	updating the chk.amt fields on the CHK file.
rem	Accumulation is based on the value
rem	of the PAY.REPORTING.CAT% variable.
rem	Note that there is no rate zero, but all other valid
rem	rates are accumulated.
rem
	on pay.reporting.cat% gosub \
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
		1413,\			rem rate 16 eic
		1406,\			rem rate 17 other pay
		1419,\			rem rate 18 tips reported
		1420,\			rem rate 19
		1408,\			rem rate 20 fwt
		1409,\			rem rate 21 swt
		1410,\			rem rate 22 lwt
		1411,\			rem rate 23 fica
		1412,\			rem rate 24 sdi
		1420,\			rem rate 25
		1420,\			rem rate 26
		1406,\			rem rate 27 advance repay
		1408,\			rem rate 28 fwt addon
		1409,\			rem rate 29 swt addon
		1410,\			rem rate 30 lwt addon
		1411,\			rem rate 31 fica addon
		1420,\			rem rate 32
		1414,\			rem rate 33 sys1
		1414,\			rem rate 34 sys2
		1414,\			rem rate 35 sys3
		1414,\			rem rate 36 sys4
		1414,\			rem rate 37 sys5
		1415,\			rem rate 38 emp1
		1415,\			rem rate 39 emp2
		1415,\			rem rate 40 emp3
		1420,\			rem rate 41
		1416,\			rem rate 42 company fica
		1417,\			rem rate 43 company futa
		1418,\			rem rate 44 company sui
		1420,\			rem rate 45
		1420,\			rem rate 46 other co cost
		1420,\			rem rate 47
		1420,\			rem rate 48
		1420,\			rem rate 49
		1420			rem rate 50 other ded
	return

1401	rem-----rate 01,02,03,04-----------------------------
	units(pay.reporting.cat%)=units(pay.reporting.cat%)+pay.units
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	return

1402	rem-----rate 05 vacation taken-----------------------
	vac.taken=vac.taken+pay.units
	return
1403	rem-----rate 06 sick leave taken---------------------
	sl.taken=sl.taken+pay.units
	return
1404	rem-----rate 07 comp time taken----------------------
	comp.taken=comp.taken+pay.units
	return
1405	rem-----rate 08 comp time earned---------------------
	comp.earned=comp.earned+pay.units
	return

1406	rem-----rate 09 other normal pay types---------------
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	return

1408	rem-----rem rate 28 fwt addon------------------------
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	fwt=fwt+pay.amt
	return

1409	rem-----rem rate 29 swt addon------------------------
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	swt=swt+pay.amt
	return

1410	rem-----rem rate 30 lwt addon------------------------
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	lwt=lwt+pay.amt
	return

1411	rem-----rem rate 31 fica addon-----------------------
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	fica=fica+pay.amt
	return

1412	rem-----rem rate 24 sdi------------------------------
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	sdi=sdi+pay.amt
	return

1413	rem-----rem rate 16 eic------------------------------
	chk.amt(check.category%(pay.reporting.cat%))=  \
		chk.amt(check.category%(pay.reporting.cat%))+pay.amt
	eic=eic+pay.amt
	return

1414	rem-----rem sys eds----------------------------------
	chk.amt(ded.sys.chk.cat%(pay.reporting.cat%-32))=  \
		chk.amt(ded.sys.chk.cat%(pay.reporting.cat%-32))+pay.amt
	sys(pay.reporting.cat%-32)=sys(pay.reporting.cat%-32)+pay.amt
	return

1415	rem-----rem emp eds----------------------------------
	chk.amt(emp.ed.chk.cat%(pay.reporting.cat%-37))=  \
		chk.amt(emp.ed.chk.cat%(pay.reporting.cat%-37))+pay.amt
	emp(pay.reporting.cat%-37)=emp(pay.reporting.cat%-37)+pay.amt
	return

1416	rem-----rem rate 42 co fica--------------------------
	co.fica=co.fica+pay.amt
	employer.costs=employer.costs+pay.amt
	return

1417	rem-----rem rate 43 co futa--------------------------
	co.futa=co.futa+pay.amt
	employer.costs=employer.costs+pay.amt
	return

1418	rem-----rem rate 44 co sui---------------------------
	co.sui=co.sui+pay.amt
	employer.costs=employer.costs+pay.amt
	return

1419	rem-----tips reported--------------------------------
	gosub 1406			rem tips collected
	temp%=pay.reporting.cat%
	pay.reporting.cat%=10
	gosub 1406			rem tips
	pay.reporting.cat%=temp%
	return

1420	rem-----invalid rates--------------------------------
	print "blooooey"
	stop

2020	rem-----accumulate pay amt for coh and his-----------
rem
rem	This rtn accumulates pay amounts in
rem	their proper accumulators for updating the COH file and some
rem	of the fields on the HIS file.
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
	on pay.reporting.cat% gosub \
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
	if emp.fwt.exempt% and emp.fica.exempt% \
		then	goto 2070	rem totally exempt (type 4)
	if emp.fwt.exempt% \
		then	goto 2060	rem FED exempt (type 3)
	if emp.fica.exempt% \
		then	goto 2050	rem SOC SEC exempt (type 2)
	income.taxable=income.taxable+pay.amt
	fica.taxable=fica.taxable+pay.amt
	return

2050	rem-----income.taxable-type 2------------------------
	income.taxable=income.taxable+pay.amt
	return

2060	rem-----other.taxable,fica.taxable-type 3------------
	other.taxable=other.taxable+pay.amt
	fica.taxable=fica.taxable+pay.amt
	return

2070	rem-----other.nontaxable-type 4----------------------
	other.nontaxable=other.nontaxable+pay.amt
	return

2080	rem-----by applicable exclusion type as above--------
	if pay.reporting.cat%=4 \
		then	exclusion.type%=emp.rate4.exclusion% :\
			gosub 2110   :\ 	rem accumulate
			return
	if pay.reporting.cat%>=33 and \
	   pay.reporting.cat%<=37     \
		then	gosub 2082   :\ 	rem do sys ed
			return
	if pay.reporting.cat%>=38 and \
	   pay.reporting.cat%<=40     \
		then	gosub 2084   :\ 	rem do emp ed
			return
	print "bloooey"
	stop

2082	rem-----do sys ed-----------------------------------
	if ded.sys.earn.ded$(pay.reporting.cat%-32)="E" \
		then	exclusion.type%=ded.sys.exclusion%	\
				(pay.reporting.cat%-32) 	:\
			gosub 2110    \ 	rem accumulate
		else	other.ded=other.ded+pay.amt
	return

2084	rem-----do emp ed-----------------------------------
	if emp.ed.earn.ded$(pay.reporting.cat%-37)="E" \
		then	exclusion.type%=emp.ed.exclusion%	\
				(pay.reporting.cat%-37) 	:\
			gosub 2110    \ 	rem accumulate
		else	other.ded=other.ded+pay.amt
	return

2090	rem-----tips collected-------------------------------
	tips=tips+pay.amt
	return

2100	rem-----tips reported--------------------------------
	tips=tips+pay.amt
	tips.reported=tips.reported+pay.amt
	other.ded=other.ded+pay.amt
	return

2110	rem-----accumulate-----------------------------------
	on exclusion.type% gosub \
		2040,\		rem type 1
		2050,\		rem type 2
		2060,\		rem type 3
		2070		rem type 4
	return
