$include "ipycomm"
$include "ipyapcom"
prgname$="APPLY1     JAN. 16, 1980 "
rem----------------------------------------------------------
rem
rem	A  P  P  L  Y  1
rem
rem		S E T U P
rem
rem	SECTION ONE OF PAYROLL CALCULATION PROGRAM
rem
rem	P A Y R O L L	   S Y S T E M
rem
rem	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="APPLY1"
function.name$="PAYROLL APPLICATION -- SECTION ONE"

$include "ipyconst"
$include "zfilconv"
$include "zdms"
$include "zdmsclr"

rem----------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem----------------------------------------------------------

del.file%=1

dim emsg$(25)
emsg$(01)="PY501 INVALID DATE"
emsg$(02)="PY502 CHECK DATE IS NOT IN CURRENT QUARTER"
emsg$(03)="PY503 CHECK DATE IS NOT IN CURRENT YEAR"
emsg$(04)="PY504 MUST BE M OR W"
emsg$(05)="PY505 CURRENT CHECKS NOT PRINTED"
emsg$(06)="PY506 CHECK DATE EARLIER THAN PREVIOUS CHECK DATE"
emsg$(07)="PY507 PYPAY.100 FOUND"
emsg$(08)="PY508 CURRENT PAYROLL JOURNAL NOT PRINTED"
emsg$(09)="PY509 EMP FILE NOT FOUND"
emsg$(10)="PY510 DED FILE NOT FOUND"
emsg$(11)="PY511 SWT OR CALx FILE NOT FOUND"
emsg$(12)="PY512 LWT FILE NOT FOUND"
emsg$(13)="PY513 HIS FILE NOT FOUND"
emsg$(14)="PY514 YES, ESCAPE OR BACK ONLY"
emsg$(15)="PY515 ACT FILE NOT FOUND"
emsg$(16)="PY516 PR2 FILE NOT FOUND"
emsg$(17)="PY517 YES OR ESCAPE ONLY"
emsg$(18)="PY518 YES OR ESCAPE ONLY"
emsg$(19)="PY519 CAN'T APPLY.  QUARTER NEEDS ENDING"
emsg$(20)="PY520 CAN'T APPLY.  QUARTER NEEDS ENDING"
emsg$(21)="PY521 CAN'T APPLY.  YEAR NEEDS ENDING"
emsg$(22)="PY522 CURRENT REGISTER NOT PRINTED"
emsg$(23)="PY523 CHK.100 FILE FOUND"

$include "zdmsconf"
$include "ipystat"
$include "zparse"
$include "znumber"
$include "zdateio"
$include "zeditdte"
$include "zdateinc"
$include "zstring"
$include "ipydmemp"
$include "ipydmhis"
$include "ipydmchk"
$include "ipydmded"
$include "ipydmswt"
$include "ipydmcal"
$include "fpyap1"			rem define screen info

def fn.quarter%(date$)
	trash%=fn.decompose.date%(date$)
	if mo%=01 or mo%=02 or mo%=03 then fn.quarter%=1:return
	if mo%=04 or mo%=05 or mo%=06 then fn.quarter%=2:return
	if mo%=07 or mo%=08 or mo%=09 then fn.quarter%=3:return
	if mo%=10 or mo%=11 or mo%=12 then fn.quarter%=4:return
fend

def fn.in%(mask%,id%)
	cr%=false%:stopit%=false%:back%=false%:cancel%=false%
	getnext%=false%:save%=false%:adding%=false%:deleteit%=false%
	fn.in%=fn.get%(mask%,id%)
	if in.status%=req.valid% then valid.data%=true%:return
	if in.status%=req.cr% then cr%=true%:return
	if in.status%=req.stopit% then stopit%=true%:return
	if in.status%=req.back% then back%=true%:return
	if in.status%=req.cancel% then cancel%=true%:return
	if in.status%=req.next% then getnext%=true%:return
	if in.status%=req.save% then save%=true%:return
	if in.status%=req.adding% then adding%=true%:return
	if in.status%=req.delete% then deleteit%=true%:return
	print "baloney":stop
fend

dim dd$(3)
def fn.date.format$
	dd$(pr1.date.mo%)="MM":dd$(pr1.date.yr%)="YY":dd$(pr1.date.dy%)="DD"
	fn.date.format$=dd$(1)+"/"+dd$(2)+"/"+dd$(3)
	return
fend

def fn.odd%(temp%)
	if int%(temp%/2)*2=temp% then fn.odd%=false% else fn.odd%=true%
	return
fend

rem----------------------------------------------------------
rem
rem	S E T	    U P
rem
rem----------------------------------------------------------

gosub 200		rem display.set.up.screen

100

rem----------------------------------------------------------
	null$=				""
	interval$=			null$
	extension.intervals$=		null$
	from.slow.date$=		"000000"
	from.fast.date$=		"000000"
	to.date$=			"000000"
	week.based%=			false%
	month.based%=			false%
	apply.no%=			0
	month.from.date$=		"000000"
	semimonth.from.date$=		"000000"
	biweek.from.date$=		"000000"
	week.from.date$=		"000000"
	apply.incremented%=		false%
rem----------------------------------------------------------

new.m.date$=pr2.last.day.of.last.m$
new.s.date$=pr2.last.day.of.last.s$
new.w.date$=pr2.last.day.of.last.w$
new.b.date$=pr2.last.day.of.last.b$
new.last.wb.apply.no%=pr2.last.wb.apply.no%
new.last.sm.apply.no%=pr2.last.sm.apply.no%
new.no.of.wb.applies%=pr2.no.of.wb.applies%
new.no.of.sm.applies%=pr2.no.of.sm.applies%

rem----------------------------------------------------------
rem
rem	M A I N       D R I V E R
rem
rem----------------------------------------------------------

gosub 210			rem can.we.run
if not ok% then goto 999.1

back%=false%
gosub 220			rem determine base
if stopit% then goto 999.2
if back% then goto 100

gosub 1000			rem determine if period needs ending
if not ok% then goto 999.1

gosub 237			rem determine apply no
gosub 239			rem get interval$
gosub 240			rem display apply no
gosub 250			rem display extension intervals
gosub 260			rem display last days of extension intervals

gosub 270			rem request confirmation
if stopit% then goto 999.2
if back% \
	then	trash%=fn.clr%(01)		:\
		trash%=fn.clr%(02)		:\
		trash%=fn.clr%(03)		:\
		trash%=fn.clr%(04)		:\
		trash%=fn.clr%(05)		:\
		trash%=fn.clr%(15)		:\
		goto 100	rem start over again
110
gosub 290			rem request.check.date
if stopit% then goto 999.2
if back% then goto 100
trash%=fn.lit%(24)		rem CURRENT CHECK DATE:
trash%=fn.put%(fn.date.out$(check.date$),11)

gosub 300			rem determine proper quarter/year
if not ok% then goto 110

gosub 500			rem set up files
gosub 330			rem display.process.screen

rem----------------------------------------------------------
rem
rem	E N D	  O F	  J O B
rem
rem----------------------------------------------------------

pr2.check.date$=check.date$
pr2.last.day.of.last.m$=new.m.date$
pr2.last.day.of.last.s$=new.s.date$
pr2.last.day.of.last.w$=new.w.date$
pr2.last.day.of.last.b$=new.b.date$
pr2.last.sm.apply.no%=new.last.sm.apply.no%
pr2.last.wb.apply.no%=new.last.wb.apply.no%
pr2.no.of.wb.applies%=new.no.of.wb.applies%
pr2.no.of.sm.applies%=new.no.of.sm.applies%
gosub 850			rem rewrite pr2 file
gosub 870			rem delete hrs.001 if needed
trash%=fn.clr%(09)		rem clear row 21 on screen
trash%=fn.clr%(21)		rem clear row 23 on screen

common.chaining.status$=common.chaining.status$+in.apply$

chain fn.file.name.out$("APPLY2",null$,0,pw$,pms$)

$include "zeoj"

rem----------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem----------------------------------------------------------

200	rem-----display set up screen------------------------
	trash%=fn.put.all%(false%)
	return

210	rem-----can we run?----------------------------------
	ok%=true%
	return

220	rem-----determine base-------------------------------
	extension.intervals$=null$
	intervals%=0
	if pr1.m.used% then intervals%=intervals%+1
	if pr1.s.used% then intervals%=intervals%+2
	if pr1.w.used% then intervals%=intervals%+4
	if pr1.b.used% then intervals%=intervals%+8
	on intervals% gosub \
		221,\			rem M
		222,\			rem S
		223,\			rem MS
		224,\			rem W
		225,\			rem MW
		226,\			rem SW
		227,\			rem MSW
		228,\			rem B
		229,\			rem MB
		230,\			rem SB
		231,\			rem MSB
		232,\			rem WB
		233,\			rem MWB
		234,\			rem SWB
		235			rem MSWB
	if month.based% \
		then	from.slow.date$=month.from.date$ :\
			from.fast.date$=semimonth.from.date$ \
		else	from.slow.date$=biweek.from.date$ :\
			from.fast.date$=week.from.date$
	if pr1.debugging% then trash%=fn.put%  \
		("EXTNSN INTRVLS: "+extension.intervals$,09)
	return

221	rem-----M--------------------------------------------
	month.based%=true%
	trash%=fn.decompose.date%(pr2.last.day.of.last.m$)
	mo%=fn.incr.month%(mo%)
	dy%=fn.last.day%(mo%,yr%)
	new.m.date$=fn.date.in$
	month.from.date$=fn.incr.date$(pr2.last.day.of.last.m$,1)
	if not apply.incremented% \
		then	new.last.sm.apply.no%=pr2.last.sm.apply.no%+2 :\
			new.no.of.sm.applies%=new.no.of.sm.applies%+2 :\
			to.date$=new.m.date$	:\
			apply.incremented%=true%
	extension.intervals$=extension.intervals$+"M"
	return

222	rem-----S--------------------------------------------
	month.based%=true%
	trash%=fn.decompose.date%(pr2.last.day.of.last.s$)
	if dy%=fn.last.day%(mo%,yr%) \
		then	mo%=fn.incr.month%(mo%) 	:\
			dy%=15				 \
		else	dy%=fn.last.day%(mo%,yr%)
	new.s.date$=fn.date.in$
	semimonth.from.date$=fn.incr.date$(pr2.last.day.of.last.s$,1)
	if not apply.incremented% \
		then	new.last.sm.apply.no%=pr2.last.sm.apply.no%+1 :\
			new.no.of.sm.applies%=new.no.of.sm.applies%+1 :\
			to.date$=new.s.date$	:\
			apply.incremented%=true%
	extension.intervals$=extension.intervals$+"S"
	return

223	rem-----MS-------------------------------------------
	month.based%=true%

rem  if the last apply no is odd, this apply no is even and vice versa
rem  if the last apply is odd, now apply BOTH S and M, if last was
rem    even, now apply only S.

	if fn.odd%(pr2.last.sm.apply.no%) \
		then	gosub 222 :\	rem S
			gosub 221  \	rem M
		else	gosub 222	rem S
	return

224	rem-----W--------------------------------------------
	week.based%=true%
	new.w.date$=fn.incr.date$(pr2.last.day.of.last.w$,7)
	week.from.date$=fn.incr.date$(pr2.last.day.of.last.w$,1)
	if not apply.incremented% \
		then	new.last.wb.apply.no%=pr2.last.wb.apply.no%+1 :\
			new.no.of.wb.applies%=new.no.of.wb.applies%+1 :\
			to.date$=new.w.date$	:\
			apply.incremented%=true%
	extension.intervals$=extension.intervals$+"W"
	return

225	rem-----MW-------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 224 :\	rem W
		else	gosub 221	rem M
	return

226	rem-----SW-------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 224 :\	rem W
		else	gosub 222	rem S
	return

227	rem-----MSW------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 224 :\	rem W
		else	gosub 223	rem MS
	return

228	rem-----B--------------------------------------------
	week.based%=true%
	new.b.date$=fn.incr.date$(pr2.last.day.of.last.b$,14)
	biweek.from.date$=fn.incr.date$(pr2.last.day.of.last.b$,1)
	if not apply.incremented% \
		then	new.last.wb.apply.no%=pr2.last.wb.apply.no%+2 :\
			new.no.of.wb.applies%=new.no.of.wb.applies%+2 :\
			to.date$=new.b.date$	:\
			apply.incremented%=true%
	extension.intervals$=extension.intervals$+"B"
	return

229	rem-----MB-------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 228 :\	rem B
		else	gosub 221	rem M
	return

230	rem-----SB-------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 228 :\	rem B
		else	gosub 222	rem S
	return

231	rem-----MSB------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 228 :\	rem B
		else	gosub 223	rem MS
	return

232	rem-----WB-------------------------------------------
	week.based%=true%

rem  if the last apply no is odd, this apply no is even and vice versa
rem  if the last apply is odd, now apply BOTH W and B, if last was
rem    even, now apply only W.

	if fn.odd%(pr2.last.wb.apply.no%) \
		then	gosub 224 :\	rem W
			gosub 228  \	rem B
		else	gosub 224	rem W
	return

233	rem-----MWB------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 232 :\	rem WB
		else	gosub 221	rem M
	return

234	rem-----SWB------------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 232 \	rem WB
		else	gosub 222	rem S
	return

235	rem-----MSWB-----------------------------------------
	gosub 370			rem request base
	if stopit% or back% then return
	if week.based% \
		then	gosub 232 \	rem WB
		else	gosub 223	rem MS
	return

237	rem-----determine apply no---------------------------
	if week.based% \
		then	apply.no%=new.last.wb.apply.no% \
		else	apply.no%=new.last.sm.apply.no%
	return

239	rem-----get interval$--------------------------------
	if len(extension.intervals$)=1 \
		then	interval$=extension.intervals$	:\
			return
	if match("W",extension.intervals$,1)<>0 and      \
	   match("B",extension.intervals$,1)<>0          \
		then	interval$="B"                   :\
			return
	if match("M",extension.intervals$,1)<>0 and      \
	   match("S",extension.intervals$,1)<>0          \
		then	interval$="M"                   :\
			return
	print "death rattle"
	stop

240	rem-----display apply no-----------------------------
	trash%=fn.put%("APPLY NO:"+str$(apply.no%),1)   rem upper right corner
	return

250	rem-----display extension intervals------------------
	trash%=fn.lit%(15)	rem	"CURRENT EXTENSION INTERVAL"
	if len(extension.intervals$)=1 \
		then	trash%=fn.put%(" IS",4)    \
		else	trash%=fn.put%("S ARE",4)
	out$=null$
	if match("M",extension.intervals$,1)<>0 \
		then	out$=out$+" AND MONTHLY"
	if match("S",extension.intervals$,1)<>0 \
		then	out$=out$+" AND SEMI-MONTHLY"
	if match("W",extension.intervals$,1)<>0 \
		then	out$=out$+" AND WEEKLY"
	if match("B",extension.intervals$,1)<>0 \
		then	out$=out$+" AND BI-WEEKLY"
	out$=right$(out$,len(out$)-5)
	trash%=fn.put%(out$,5)
	return

260	rem-----display last days of extension intervals-----
rem		CURRENT WEEK IS FROM MM/DD/YY THROUGH MM/DD/YY
rem		CURRENT SEMI-MONTH IS FROM MM/DD/YY THROUGH MM/DD/YY
	if match("M",extension.intervals$,1)<>0 \
		then	trash%=fn.put%				\
			("CURRENT MONTH IS FROM "+              \
			fn.date.out$(month.from.date$)+ 	\
			" THROUGH "+fn.date.out$(to.date$),2)
	if match("S",extension.intervals$,1)<>0 \
		then	trash%=fn.put%				\
			("CURRENT SEMI MONTH IS FROM "+          \
			fn.date.out$(semimonth.from.date$)+	\
			" THROUGH "+fn.date.out$(to.date$),3)
	if match("W",extension.intervals$,1)<>0 \
		then	trash%=fn.put%				\
			("CURRENT WEEK IS FROM "+               \
			fn.date.out$(week.from.date$)+		\
			" THROUGH "+fn.date.out$(to.date$),2)
	if match("B",extension.intervals$,1)<>0 \
		then	trash%=fn.put%				\
			("CURRENT BIWEEK IS FROM "+             \
			fn.date.out$(biweek.from.date$)+	\
			" THROUGH "+fn.date.out$(to.date$),3)
	return

270	rem-----request confirmation-------------------------
	trash%=fn.lit%(19)
271
	trash%=fn.in%(2,10)		rem get a yes or no
	if stopit% or back% \
		then	trash%=fn.clr%(19)	:\
			return
	if in.uc$<>"YES" \
		then	trash%=fn.emsg%(14)	:\
			trash%=fn.put%(null$,10)	:\
			goto 271	rem retry
	trash%=fn.clr%(19)		rem clear request line
	return

290	rem-----request check date---------------------------
	trash%=fn.lit%(16)	rem "ENTER CHECK DATE (        ) "
	trash%=fn.put%(fn.date.format$,6)
292
	trash%=fn.in%(2,7)
	if back% or stopit% then return
	if not fn.edit.date%(in$) \
		then	trash%=fn.emsg%(01)   :\
			trash%=fn.clr%(7)     :\
			goto 292
	in.date$=fn.date.in$
	if in.date$<pr2.check.date$ \
		then	trash%=fn.emsg%(06)   :\
			trash%=fn.clr%(7)     :\
			goto 292
	check.date$=in.date$
	trash%=fn.clr%(16)
	return

300	rem-----determine proper quarter/year----------------
	ok%=true%
	temp%=fn.quarter%(check.date$)
	if temp%=1 \
		then	temp%=4  \
		else	temp%=temp%-1
	if pr2.last.q.ended%<>temp%		\
		then	trash%=fn.emsg%(02)   :\
			ok%=false%
	trash%=fn.decompose.date%(check.date$)
	if pr2.year%<>yr% \
		then	trash%=fn.emsg%(03)   :\
			ok%=false%
	return

330	rem-----display process screen-----------------------
	trash%=fn.lit%(18)   rem "EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
	trash%=fn.clr%(21)	rem HRS file status msg
	return

370	rem-----two bases used-------------------------------
	trash%=fn.lit%(17)
		rem "APPLY WHICH INTERVAL BASE? (M=MONTH;W=WEEK) [ ]"
	trash%=fn.in%(2,8)
	if stopit% then return
	if back% then return
	if in.uc$<>"M" and in.uc$<>"W" \
		then	trash%=fn.emsg%(04)   :\
			goto 370
	if in.uc$="M" \
		then	month.based%=true%  :\
			week.based%=false%
	if in.uc$="W" \
		then	month.based%=false% :\
			week.based%=true%
	trash%=fn.clr%(17)
	return

500	rem-----set up files---------------------------------
	gosub 505			rem is chk.100 present?
	if chk.exists% \
		then	trash%=fn.emsg%(23)	:\
			goto 999.1
	gosub 510			rem get.chk.101  status
	if chk.exists% \
		then	gosub 520	rem get.chk.hdr
	if not pr1.check.printing.used% \
		then	chk.hdr.checks.printed%=true%

	if chk.exists% and not chk.hdr.checks.printed% \
			then	trash%=fn.emsg%(05)   :\
				goto 999.1
	if chk.exists% and not chk.hdr.register.printed%		\
			then	trash%=fn.emsg%(22)   :\
				goto 999.1

	if chk.exists% \
		then	close chk.file%
	gosub 530			rem delete chk.bak if present
	if chk.exists% \
		then	gosub 540	rem rename(chk.bak=chk)
	gosub 550			rem get.hrs.file
	if hrs.exists% \
		then	gosub 560 :\	rem get.hrs.hdr
			ok%=true% :\
			close hrs.file%  \
		else	gosub 580 :\	rem request confirmation
			hrs.hdr.proofed%=true%
	if not ok% or stopit% \
		then	goto 999.2
	if not hrs.hdr.proofed% \
		then	gosub 590 \	rem request.confirmation
		else	ok%=true%
	if not ok% or stopit% \
		then	goto 999.2
	gosub 600			rem is PAY.100 present?
	if not ok% \
		then	trash%=fn.emsg%(07)   :\
			goto 999.1

	gosub 610			rem get.pay.file
	if pay.exists% \
		then	gosub 620 :\	rem get.pay.hdr
			close pay.file%  \
		else	pay.hdr.journal.printed%=true%
	if not pay.hdr.journal.printed% \
		then	trash%=fn.emsg%(08)   :\
			goto 999.1

	gosub 640			rem get.emp.file
	if not emp.exists% \
		then	trash%=fn.emsg%(09)   :\
			goto 999.1
	close emp.file%

	gosub 650			rem get.ded.file
	if not ded.exists% \
		then	trash%=fn.emsg%(10)   :\
			goto 999.1
	gosub 655			rem read ded file
	close ded.file%

	if ded.swt.used% \
		then	gosub 660	rem get swt file
	if not swt.exists% and ded.swt.used% \
		then	trash%=fn.emsg%(11)   :\
			goto 999.1

	if ded.lwt.used% \
		then	gosub 670	rem get swt file
	if not lwt.exists% and ded.lwt.used% \
		then	trash%=fn.emsg%(12)   :\
			goto 999.1
	if lwt.exists% \
		then	close lwt.file%

	gosub 680			rem get.his.file
	if not his.exists% \
		then	trash%=fn.emsg%(13)   :\
			goto 999.1  \
		else	gosub 690 :\	rem read.his.hdr
			close his.file%

	gosub 700			rem get coh file
	if not coh.exists% \
		then	gosub 710 :\	rem request confirmation
		else	ok%=true% :\
			close coh.file%
	if not ok% or stopit% \
		then	goto 999.2

	gosub 720			rem get act file
	if not act.exists% \
		then	trash%=fn.emsg%(15)   :\
			goto 999.1 \
		else	close act.file%

	gosub 740			rem create new.pyo.file
	close pyo.file%
	return

505	rem-----get chk.100 status---------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING CHK.100",09)
	chk.exists%=false%
	if end #chk.file% then 506
	open fn.file.name.out$(chk.name$,"100",pr1.chk.drive%,pw$,pms$) \
		recl chk.len%  as chk.file%
	chk.exists%=true%		rem this is an error!
506	rem-----here if chk file not present-----------------
	return

510	rem-----get chk.101  status--------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING CHK FILE",09)
	chk.exists%=false%
	if end #chk.file% then 511
	open fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$) \
		recl chk.len%  as chk.file%
	chk.exists%=true%
511	rem-----here if chk file not present-----------------
	return

520	rem-----get chk hdr----------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING CHK HDR",09)
	read #chk.file%,1;    \
$include "ipychkhd"
	return

530	rem-----delete chk.bak if present--------------------
	if pr1.debugging% then trash%=fn.put%("GETTING CHK.BAK",09)
	if end #del.file% then 531
	open fn.file.name.out$(chk.name$,"102",pr1.chk.drive%,pw$,pms$) \
		recl chk.len%  as del.file%
	if pr1.debugging% then trash%=fn.put%("DELETING CHK.BAK",09)
	delete del.file%
531	rem-----here if chk file not present-----------------
	return

540	rem-----rename(chk.bak=chk)--------------------------
	if pr1.debugging% then trash%=fn.put%("RENAMING CHK.BAK <-CHK",09)
	trash%=rename	  \
		(fn.file.name.out$(chk.name$,"102",pr1.chk.drive%,pw$,pms$), \
		 fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$))
	return

550	rem-----get hrs file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING HRS FILE",09)
	hrs.exists%=false%
	if end #hrs.file% then 551
	open fn.file.name.out$(hrs.name$,"101",pr1.hrs.drive%,pw$,pms$) \
		recl hrs.len%  as hrs.file%
	hrs.exists%=true%
551	rem-----here if hrs file not present-----------------
	return

560	rem-----get hrs hdr----------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING HRS HDR",09)
	read #hrs.file%,1;   \
$include "ipyhrshd"
	return

580	rem-----display status msg---------------------------
	trash%=fn.lit%(20)		rem "NO CURRENT HRS FILE FOUND"
581
	trash%=fn.lit%(23)
	rem IF YOU WANT TO CONTINUE THE APPLICATION, TYPE "YES"   [   ]
	trash%=fn.in%(1,10)
	if stopit% \
		then	trash%=fn.clr%(23)	:\
			trash%=fn.clr%(20)	:\
			return
	if in.uc$="YES" \
		then	ok%=true%			\
		else	trash%=fn.emsg%(17)		:\
			trash%=fn.put%(null$,10)	:\
			goto 581		rem retry
	trash%=fn.clr%(23)
	trash%=fn.clr%(21)
	return

590	rem-----request confirmation-------------------------
	trash%=fn.lit%(21)
			rem "THE CURRENT HRS BATCH FILE HAS NOT BEEN PROOFED."
591
	trash%=fn.lit%(23)
	rem IF YOU WANT TO CONTINUE THE APPLICATION, TYPE "YES"   [   ]
	trash%=fn.in%(1,10)
	if stopit% \
		then	trash%=fn.clr%(23)	:\
			trash%=fn.clr%(21)	:\
			return
	if in.uc$="YES" \
		then	ok%=true% \
		else	trash%=fn.emsg%(17)	:\
			trash%=fn.put%(null$,10)	:\
			goto 591		rem retry
	trash%=fn.clr%(23)
	trash%=fn.clr%(21)
	return

600	rem-----is PAY.100 present?--------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING PAY.100",09)
	ok%=true%
	if end #del.file% then 601
	open fn.file.name.out$(pay.name$,"100",pr1.pay.drive%,pw$,pms$) \
		as del.file%
	ok%=false%
601	rem-----here if 100 file not present-----------------
	return

610	rem-----get pay file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING PAY.101",09)
	pay.exists%=false%
	if end #pay.file% then 611
	open fn.file.name.out$(pay.name$,"101",pr1.pay.drive%,pw$,pms$) \
		recl pay.len%  as pay.file%
	pay.exists%=true%
611	rem-----here if pay file not present-----------------
	return

620	rem-----get pay hdr----------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING PAY HDR",09)
	read #pay.file%,1;    \
$include "ipypayhd"
	return

640	rem-----get emp file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING EMP FILE",09)
	emp.exists%=false%
	if end #emp.file% then 641
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pms$) \
		recl emp.len%  as emp.file%
	emp.exists%=true%
641	rem-----here if emp file not present-----------------
	return

650	rem-----get ded file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING DED FILE",09)
	ded.exists%=false%
	if end #ded.file% then 651
	open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pw$,pms$) \
		as ded.file%
	ded.exists%=true%
651	rem-----here if ded file not present-----------------
	return

655	rem-----read ded file--------------------------------
	read #ded.file%;  \
$include "ipyded"
	return

660	rem-----get swt file---------------------------------
	if pr1.co.state$="CA" \
		then	gosub 662 \	rem open CAL files
		else	gosub 664	rem open SWT file
	return

662	rem-----open CAL files-------------------------------
	swt.exists%=true%
	suffix$="S"                     rem single table
	if pr1.debugging% then trash%=fn.put%("GETTING CALS FILE",09)
	gosub 666			rem open CAL file
	if not cal.exists% then swt.exists%=false%:return
	close cal.file%
	suffix$="M"                     rem married table
	if pr1.debugging% then trash%=fn.put%("GETTING CALM FILE",09)
	gosub 666			rem open CAL file
	if not cal.exists% then swt.exists%=false%:return
	close cal.file%
	suffix$="H"                     rem head of house table
	if pr1.debugging% then trash%=fn.put%("GETTING CALH FILE",09)
	gosub 666			rem open CAL file
	if not cal.exists% then swt.exists%=false%:return
	close cal.file%
	suffix$="X"                     rem special table file
	if pr1.debugging% then trash%=fn.put%("GETTING CALX FILE",09)
	gosub 666			rem open CAL file
	if not cal.exists% then swt.exists%=false%:return
	close cal.file%
	return

664	rem-----open swt file--------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING SWT FILE",09)
	swt.exists%=false%
	if end #swt.file% then 665
	open fn.file.name.out$(swt.name$+pr1.co.state$,"101",   \
		pr1.tax.drive%,pw$,pms$) \
		as swt.file%
	swt.exists%=true%
665	rem-----here if swt file not present-----------------
	return

666	rem-----open cal file--------------------------------
	cal.exists%=false%
	if end #cal.file% then 667
	open fn.file.name.out$(cal.name$+suffix$,"101",   \
		pr1.tax.drive%,pw$,pms$) \
		as cal.file%
	cal.exists%=true%
667	rem-----here if cal file not present-----------------
	return

670	rem-----get lwt file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING LWT FILE",09)
	lwt.exists%=false%
	if end #lwt.file% then 671
	open fn.file.name.out$(lwt.name$,"101",pr1.tax.drive%,pw$,pms$) \
		as lwt.file%
	lwt.exists%=true%
671	rem-----here if lwt file not present-----------------
	return

680	rem-----get his file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING HIS FILE",09)
	his.exists%=false%
	if end #his.file% then 681
	open fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pms$) \
		recl his.len%  as his.file%
	his.exists%=true%
681	rem-----here if his file not present-----------------
	return

690	rem-----read his hdr---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING HIS HDR",09)
	read #his.file%,1;     \
$include "ipyhishd"
	return

700	rem-----get coh file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING COH FILE",09)
	coh.exists%=false%
	if end #coh.file% then 701
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
		as coh.file%
	coh.exists%=true%
701	rem-----here if coh file not present-----------------
	return

710	rem-----request confirmation-------------------------
	trash%=fn.lit%(22)
			rem "THE CURRENT COH FILE CANNOT BE FOUND."
711
	trash%=fn.lit%(23)
	rem IF YOU WANT TO CONTINUE THE APPLICATION, TYPE "YES"   [   ]
	trash%=fn.in%(1,10)
	if stopit% \
		then	trash%=fn.clr%(23)	:\
			trash%=fn.clr%(22)	:\
			return
	if in.uc$="YES" \
		then	ok%=true% \
		else	trash%=fn.emsg%(18)	:\
			trash%=fn.put%(null$,10)	:\
			goto 711		rem retry
	trash%=fn.clr%(23)
	trash%=fn.clr%(22)
	return

720	rem-----get act file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING ACT FILE",09)
	act.exists%=false%
	if end #act.file% then 721
	open fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pms$) \
		recl act.len%  as act.file%
	act.exists%=true%
721	rem-----here if act file not present-----------------
	return

740	rem-----create new pay file--------------------------
	if pr1.debugging% then trash%=fn.put%("CREATING NEW PAY",09)
	create fn.file.name.out$(pay.name$,"100",pr1.pyo.drive%,pw$,pms$) \
		recl pyo.len%  as pyo.file%
	pay.hdr.no.recs%=0
	pay.hdr.interval$=interval$
	pay.hdr.last.apply.no%=apply.no%
	pay.hdr.journal.printed%=false%
	pay.hdr.last.day.of.last.per$=to.date$
	gosub 800			rem write pay hdr
	return

800	rem-----write pay hdr--------------------------------
	if pr1.debugging% then trash%=fn.put%("WRITING PAY HDR",09)
	print #pyo.file%,1;    \
$include "ipypayhd"
	return

850	rem-----rewrite pr2 file-----------------------------
	if pr1.debugging% then trash%=fn.put%("WRITING PR2 FILE",09)
	if end #pr2.file% then 851
	open fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pms$) \
		as pr2.file%
	print #pr2.file%;     \
$include "ipypr2"
	close pr2.file%
	return
851	rem-----here if pr2 file not present-----------------
	trash%=fn.emsg%(16)
	goto 999.1

870	rem-----delete HRS.001 if needed---------------------
	if not hrs.exists% \	rem if no 101 file, then leave 001 alone
		then	return
	if end #del.file% then 871
	open fn.file.name.out$(hrs.name$,"001",pr1.hrs.drive%,pw$,pms$) \
		as del.file%
	delete del.file%
871	rem-----here if del file not present-----------------
	return

1000	rem-----determine if period needs ending-------------
	ok%=true%
	if week.based% and pr2.no.of.wb.applies%>14 \
		then	trash%=fn.emsg%(19)	:\
			ok%=false%		:\
			return
	if month.based% and pr2.no.of.sm.applies%>06 \
		then	trash%=fn.emsg%(20)	:\
			ok%=false%		:\
			return
	if pr2.last.q.ended%=4 and not pr2.just.closed.year% \
		then	trash%=fn.emsg%(21)	:\
			ok%=false%		:\
			return
	return
