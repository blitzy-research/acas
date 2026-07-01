#include "ipycomm"
prgname$="PYPEREND   JAN. 16, 1980 "
rem----------------------------------------------------------
rem
rem	P  Y  P  E  R  E  N  D
rem
rem	PERIOD END PROGRAM
rem
rem	P A Y R O L L	   S Y S T E M
rem
rem	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="PYPEREND"
function.name$="PROCESS PERIOD ENDING"

#include "ipyconst"
#include "zfilconv"
#include "ipystat"
#include "zdms"
#include "zdmsclr"

rem----------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem----------------------------------------------------------

del.file%=1

dim emsg$(15)
emsg$(01)="PY721 EMP FILE NOT FOUND"
emsg$(02)="PY722 HIS FILE NOT FOUND"
emsg$(03)="PY723 COH FILE NOT FOUND"
emsg$(04)="PY724 UNEXPECTED EOF ON COH FILE"
emsg$(05)="PY725 PR2 FILE NOT FOUND"
emsg$(06)="PY726 CAN'T END YEAR.  FOURTH QUARTER NOT CLOSED"
emsg$(07)="PY727 CAN'T END YEAR.  FOURTH QUARTER NOT CLOSED"
emsg$(08)="PY728 CAN'T END YEAR.  940 NOT PRINTED"
emsg$(09)="PY729 CAN'T END YEAR.  W2 NOT PRINTED"
emsg$(10)="PY730 CAN'T END QUARTER.  NOT ENOUGH WEEK BASED APPLIES"
emsg$(11)="PY731 CAN'T END QUARTER.  NOT ENOUGH MONTH BASED APPLIES"
emsg$(12)="PY732 CAN'T END QUARTER.  941 NOT PRINTED"
emsg$(13)="PY733 CAN'T END YEAR.  JUST ENDED YEAR"
emsg$(14)="PY734 "
emsg$(15)="PY735 "

#include "zparse"
#include "znumber"
#include "zdateio"
#include "zeditdte"
#include "zdateinc"
#include "zstring"
#include "ipydmcoh"
#include "ipydmemp"
#include "ipydmhis"
#include "fpyprend"		rem define screen info
msg.fld%=10
conf.fld%=09

dim sys 	(5)
dim emp 	(3)
dim units	(4)

dim quarter.table$(04)
quarter.table$(01)="FIRST"
quarter.table$(02)="SECOND"
quarter.table$(03)="THIRD"
quarter.table$(04)="FOURTH"

rem----------------------------------------------------------
rem
rem	S E T	    U P
rem
rem----------------------------------------------------------

gosub 200		rem display.set.up.screen

rem----------------------------------------------------------
rem
rem	B E G I N N I N G	O F	  J O B
rem
rem----------------------------------------------------------

gosub 210			rem can.we.run
if not ok% then goto 999.1

gosub 500			rem set up files
gosub 400			rem determine which period
trash%=fn.clr%(21)		rem clear momentarily msg
if not ok% then goto 999.1
gosub 440			rem display period end msgs
gosub 450			rem request confirmation of period
if not ok% then goto 999.2
gosub 330			rem display.process.screen

rem----------------------------------------------------------
rem
rem	M A I N       D R I V E R
rem
rem----------------------------------------------------------

employee%=1
while employee%<=pr2.no.employees%
	gosub 2000			rem process.employee
	employee%=employee%+1
	if pr1.debugging% \
		then	trash%=fn.put%("free: "+str$(fre),msg.fld%)
wend

rem----------------------------------------------------------
rem
rem	E N D	  O F	  J O B
rem
rem----------------------------------------------------------

gosub 10000			rem update COH file
gosub 11000			rem update PR2 file

#include "zeoj"

rem----------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem----------------------------------------------------------

200	rem-----display set up screen------------------------
	trash%=fn.put.all%(false%)
	trash%=fn.lit%(21)   rem "EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
	return

210	rem-----can we run?----------------------------------
	ok%=true%
	return

330	rem-----display process screen-----------------------
	trash%=fn.lit%(22)   rem "NOW PROCESSING EMPLOYEE NUMBER"
	return

400	rem-----determine which period-----------------------
	gosub 410			rem determine whether Q or Y
	if ending$="Y" and pr2.last.q.ended%<>4 \
		then	trash%=fn.emsg%(06):goto 999.1
	if ending$="Q" \
		then	gosub 420	rem determine which Q
	if ending$="Y" \
		then	gosub 430 \	rem determine if ok to end year
		else	gosub 435	rem determine if ok to end quarter
	if not ok% then return
	if ending$="Y" \
		then	new.year%=pr2.year%+1		:\
			return
	return

410	rem-----determine whether Q or Y---------------------
	if match(year.end$,common.chaining.status$,1)<>0 \
		then	ending$="Y":return
	if match(quarter.end$,common.chaining.status$,1)<>0 \
		then	ending$="Q":return
	print "Croak"
	stop

420	rem-----determine which Q----------------------------
	if pr2.last.q.ended%=4 \
		then	ending$="1"     :\
			return
	if pr2.last.q.ended%=3 \
		then	ending$="4"     :\
			return
	if pr2.last.q.ended%=2 \
		then	ending$="3"     :\
			return
	if pr2.last.q.ended%=1 \
		then	ending$="2"     :\
			return
	print "bonzaiiiiiiii"
	return

430	rem-----determine if ok to end year------------------
	if not pr2.940.printed% \
		then	trash%=fn.emsg%(08)	:\
			ok%=false%		:\
			return
	if not pr2.w2.printed% \
		then	trash%=fn.emsg%(09)	:\
			ok%=false%		:\
			return
	if pr2.just.closed.year% \
		then	trash%=fn.emsg%(13)	:\
			ok%=false%		:\
			return
	ok%=true%
	return

435	rem-----determine if ok to end quarter---------------
	if not pr2.941.printed% \
		then	trash%=fn.emsg%(12)	:\
			ok%=false%		:\
			return
	return

440	rem-----display period end msgs----------------------
	year$=str$(pr2.year%+1900)
	if ending$="Y" \
		then	trash%=fn.lit%(15)		:\
			trash%=fn.put%(year$,01)	:\
			year$=str$(new.year%+1900)	:\
		else	trash%=fn.lit%(16)		:\
			trash%=fn.put%(quarter.table$(val(ending$)),02) :\
			trash%=fn.put%(year$,03)
	if ending$="Y" \
		then	lit%=0		\
		else	lit%=val(ending$)
	if lit%=4 \
		then	lit%=1		:\
			year$=str$(val(year$)+1) \
		else	lit%=lit%+1
	trash%=fn.lit%(16+lit%)
	trash%=fn.put%(year$,03+lit%)
	return

450	rem-----get confirmation of ending period------------
	trash%=fn.lit%(23)
	trash%=fn.lit%(24)
	trash%=fn.get%(2,conf.fld%)	rem get a yes or no
	if in.uc$="YES" \
		then	ok%=true%	\
		else	ok%=false%
	trash%=fn.clr%(23)		rem clear request line
	trash%=fn.clr%(24)		rem clear request line
	return

500	rem-----set up files---------------------------------
	gosub 640			rem get.emp.file
	if not emp.exists% \
		then	trash%=fn.emsg%(01)   :\
			goto 999.1		\
		else	gosub 650	rem get emp hdr

	gosub 680			rem get.his.file
	if not his.exists% \
		then	trash%=fn.emsg%(02)   :\
			goto 999.1  \
		else	gosub 690	rem read.his.hdr

	gosub 700			rem get coh file
	if not coh.exists% \
		then	trash%=fn.emsg%(03)	:\
			goto 999.1		 \
		else	gosub 710 :\	rem read coh file
			close coh.file%
	return

640	rem-----get emp file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING EMP FILE",msg.fld%)
	emp.exists%=false%
	if end #emp.file% then 641
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pms$) \
		recl emp.len%  as emp.file%
	emp.exists%=true%
641	rem-----here if emp file not present-----------------
	return

650	rem-----get emp hdr----------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING EMP HDR",msg.fld%)
	read #emp.file%,1;     \
#include "ipyemphd"
	return

680	rem-----get his file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING HIS FILE",msg.fld%)
	his.exists%=false%
	if end #his.file% then 681
	open fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pms$) \
		recl his.len%  as his.file%
	his.exists%=true%
681	rem-----here if his file not present-----------------
	return

690	rem-----read his hdr---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING HIS HDR",msg.fld%)
	read #his.file%,1;     \
#include "ipyhishd"
	return

700	rem-----get coh file---------------------------------
	if pr1.debugging% then trash%=fn.put%("GETTING COH FILE",msg.fld%)
	coh.exists%=false%
	if end #coh.file% then 701
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
		as coh.file%
	coh.exists%=true%
701	rem-----here if coh file not present-----------------
	return

710	rem-----read coh file--------------------------------
	if pr1.debugging% then trash%=fn.put%("READING COH FILE",msg.fld%)
	read #coh.file%;   \
#include "ipycoh"
	return

2000	rem-----process employee-----------------------------
	gosub 3000			rem read emp rec
	gosub 2100			rem display employee number
	gosub 3100			rem read his rec
	gosub 3200			rem clear emp rec
	gosub 3300			rem clear his rec
	gosub 3400			rem write emp rec
	if ending$="Y" and deleted% \
		then	gosub 3420 :\	rem connect del ptrs
			pr2.no.active.emps%=pr2.no.active.emps%-1
	gosub 3500			rem write his rec
	return

2100	rem-----display employee number----------------------
	trash%=fn.put%(emp.no$,08)
	return

3000	rem-----read emp rec---------------------------------
	if pr1.debugging% then trash%=fn.put%("READING EMP REC",msg.fld%)
	read #emp.file%,employee%+1;	\
#include "ipyemp"
	return

3100	rem-----read his rec---------------------------------
	if pr1.debugging% then trash%=fn.put%("READING HIS REC",msg.fld%)
	read #his.file%,employee%+1;	\
#include "ipyhis"
	return

3200	rem-----clear emp rec--------------------------------
	if ending$="Y" \
		then	emp.vac.accum=emp.vac.accum-emp.vac.used	:\
			emp.vac.used=0					:\
			emp.sl.accum=emp.sl.accum-emp.sl.used		:\
			emp.sl.used=0					:\
			emp.comp.accum=emp.comp.accum-emp.comp.used	:\
			emp.comp.used=0
	gosub 3210			rem update status
	return

3210	rem-----update status--------------------------------
	if emp.status$="T"  and ending$="Y" \
		then	emp.status$="D"         :\
			trash%=fn.lit%(25)	:\	rem DELETING
			deleted%=true%		\
		else	trash%=fn.clr%(25)	:\
			deleted%=false%
	return

3300	rem-----clear his rec--------------------------------
	if ending$="Y" \
		then	gosub 3310 \	rem clear ytd fields
		else	gosub 3320	rem clear qtd fields
	return

3310	rem-----clear ytd fields-----------------------------
	his.ytd.income.taxable		=0
	his.ytd.other.taxable		=0
	his.ytd.other.nontaxable	=0
	his.ytd.fica.taxable		=0
	his.ytd.tips		=0
	his.ytd.net		=0
	his.ytd.eic		=0
	his.ytd.fwt		=0
	his.ytd.swt		=0
	his.ytd.lwt		=0
	his.ytd.fica		=0
	his.ytd.sdi		=0
	his.ytd.sys(1)		=0
	his.ytd.sys(2)		=0
	his.ytd.sys(3)		=0
	his.ytd.sys(4)		=0
	his.ytd.sys(5)		=0
	his.ytd.emp(1)		=0
	his.ytd.emp(2)		=0
	his.ytd.emp(3)		=0
	his.ytd.other.ded		=0
	his.ytd.units(1)		=0
	his.ytd.units(2)		=0
	his.ytd.units(3)		=0
	his.ytd.units(4)		=0
	return

3320	rem-----clear qtd fields-----------------------------
	his.qtd.income.taxable		=0
	his.qtd.other.taxable		=0
	his.qtd.other.nontaxable	=0
	his.qtd.fica.taxable		=0
	his.qtd.tips		=0
	his.qtd.net		=0
	his.qtd.eic		=0
	his.qtd.fwt		=0
	his.qtd.swt		=0
	his.qtd.lwt		=0
	his.qtd.fica		=0
	his.qtd.sdi		=0
	his.qtd.sys(1)		=0
	his.qtd.sys(2)		=0
	his.qtd.sys(3)		=0
	his.qtd.sys(4)		=0
	his.qtd.sys(5)		=0
	his.qtd.emp(1)		=0
	his.qtd.emp(2)		=0
	his.qtd.emp(3)		=0
	his.qtd.other.ded		=0
	his.qtd.units(1)		=0
	his.qtd.units(2)		=0
	his.qtd.units(3)		=0
	his.qtd.units(4)		=0
	return

3400	rem-----write emp rec--------------------------------
	if pr1.debugging% then trash%=fn.put%("WRITING EMP REC",msg.fld%)
	print #emp.file%,employee%+1;	\
#include "ipyemp"
	return

3420	rem-----connect del ptrs-----------------------------
	emp.hdr.no.del.recs%=emp.hdr.no.del.recs%+1
	deleted.emp%=employee%
	if last.del.rec%=0 \
		then	emp.hdr.next.del.rec%=deleted.emp%	\
		else	employee%=last.del.rec% 	:\
			gosub 3000			:\  rem read emp rec
			emp.next.del%=deleted.emp%		:\
			gosub 3400		rem write emp rec
	employee%=deleted.emp%
	last.del.rec%=deleted.emp%
	gosub 3430				rem write emp hdr
	return

3430	rem-----write emp hdr--------------------------------
	if pr1.debugging% then trash%=fn.put%("WRITING EMP HDR",msg.fld%)
	print #emp.file%,1;	\
#include "ipyemphd"
	return

3500	rem-----write his rec--------------------------------
	if pr1.debugging% then trash%=fn.put%("WRITING HIS REC",msg.fld%)
	print #his.file%,employee%+1;	\
#include "ipyhis"
	return

10000	rem-----update COH file------------------------------
	if ending$="Y" \
		then	gosub 10300	\	rem clear YTD accums
		else	gosub 10200		rem clear QTD accums
	gosub 10100			rem write COH file
	return

10100	rem-----write COH file-------------------------------
	if pr1.debugging% then trash%=fn.put%("OPENING COH FILE",msg.fld%)
	if end #coh.file% then 10101
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
		as coh.file%
	if pr1.debugging% then trash%=fn.put%("WRITING COH FILE",msg.fld%)
	print #coh.file%;    \
#include "ipycoh"
	close coh.file%
	return

10101	rem-----here if COH file not found-------------------
	trash%=fn.emsg%(04)
	goto 999.1

10200	rem-----clear QTD accums-----------------------------
	coh.q.co.futa.liab(val(ending$))=coh.qtd.co.futa.liab
	coh.q.tax(val(ending$)) 	=coh.qtd.fwt.liab
	coh.q.fica.tax(val(ending$))	=coh.qtd.fica.liab+coh.qtd.co.fica.liab

	coh.qtd.income.taxable		=0
	coh.qtd.other.taxable		=0
	coh.qtd.other.nontaxable	=0
	coh.qtd.fica.taxable		=0
	coh.qtd.tips			=0
	coh.qtd.net			=0
	coh.qtd.eic.credit		=0
	coh.qtd.fwt.liab		=0
	coh.qtd.swt.liab		=0
	coh.qtd.lwt.liab		=0
	coh.qtd.fica.liab		=0
	coh.qtd.sdi.liab		=0
	coh.qtd.co.futa.liab		=0
	coh.qtd.co.fica.liab		=0
	coh.qtd.co.sui.liab		=0
	for i%=1 to pr1.max.sys.eds%
		coh.qtd.sys(i%) 	=0
	next i%
	for i%=1 to pr1.max.emp.eds%
		coh.qtd.emp(i%) 	=0
	next i%
	coh.qtd.other.ded		=0
	for i%=1 to 4
		coh.qtd.units(i%)	=0
	next i%
	coh.qtd.comp.time.earned	=0
	coh.qtd.comp.time.taken 	=0
	coh.qtd.vac.earned		=0
	coh.qtd.vac.taken		=0
	coh.qtd.sl.earned		=0
	coh.qtd.sl.taken		=0
	for i%=1 to 12
		coh.date$(i%)		="000000"
		coh.tax(i%)		=0
	next i%
	return

10300	rem-----clear YTD accums-----------------------------
	coh.ytd.income.taxable		=0
	coh.ytd.other.taxable		=0
	coh.ytd.other.nontaxable	=0
	coh.ytd.fica.taxable		=0
	coh.ytd.tips			=0
	coh.ytd.net			=0
	coh.ytd.eic.credit		=0
	coh.ytd.fwt.liab		=0
	coh.ytd.swt.liab		=0
	coh.ytd.lwt.liab		=0
	coh.ytd.fica.liab		=0
	coh.ytd.sdi.liab		=0
	coh.ytd.co.futa.liab		=0
	coh.ytd.co.fica.liab		=0
	coh.ytd.co.sui.liab		=0
	for i%=1 to pr1.max.sys.eds%
		coh.ytd.sys(i%) 	=0
	next i%
	for i%=1 to pr1.max.emp.eds%
		coh.ytd.emp(i%) 	=0
	next i%
	coh.ytd.other.ded		=0
	for i%=1 to 4
		coh.ytd.units(i%)	=0
	next i%
	coh.ytd.comp.time.earned	=0
	coh.ytd.comp.time.taken 	=0
	coh.ytd.vac.earned		=0
	coh.ytd.vac.taken		=0
	coh.ytd.sl.earned		=0
	coh.ytd.sl.taken		=0
	for i%=1 to 12
		coh.date$(i%)		="000000"
		coh.tax(i%)		=0
	next i%
	for i%=1 to 4
		coh.q.tax(i%)		=0
		coh.q.fica.tax(i%)	=0
		coh.q.co.futa.liab(i%)	=0
	next i%
	return

11000	rem-----update PR2 file------------------------------
	if ending$="Y" \
		then	gosub 11200 \	rem clear for year
		else	gosub 11300	rem clear for quarter
	gosub 11100			rem write PR2 file
	return

11100	rem-----write PR2 file-------------------------------
	if pr1.debugging% then trash%=fn.put%("OPENING PR2 FILE",msg.fld%)
	if end #pr2.file% then 11101
	open fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pms$) \
		as pr2.file%
	if pr1.debugging% then trash%=fn.put%("WRITING PR2 FILE",msg.fld%)
	print #pr2.file%;     \
#include "ipypr2"
	close pr2.file%
	return
11101	rem-----here if pr2 file not present-----------------
	trash%=fn.emsg%(05)
	goto 999.1

11200	rem-----clear for year-------------------------------
	pr2.last.year.ended%=pr2.year%
	pr2.year%=pr2.year%+1
	pr2.940.printed%=false%
	pr2.w2.printed%=false%
	pr2.just.closed.year%=true%
	return

11300	rem-----clear for quarter----------------------------
	pr2.last.q.ended%=val(ending$)
	pr2.941.printed%=false%
	pr2.just.closed.year%=false%
	pr2.no.of.wb.applies%=0
	pr2.no.of.sm.applies%=0
	return
