#include "ipycomm"
#include "ipyjrncm"
prgname$="PYJOURN    JAN. 17, 1980 "
rem----------------------------------------------------------
rem
rem	P  Y  J  O  U  R  N
rem
rem	PRINT THE PAYROLL JOURNAL
rem
rem	F I R S T      S E C T I O N
rem
rem	P A Y R O L L	   S Y S T E M
rem
rem	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="PYJOURN"
function.name$="PAYROLL JOURNAL PRINT"

#include "ipyconst"
#include "zfilconv"
#include "zdms"
#include "zdmsclr"

rem----------------------------------------------------------
rem
rem	C O N S T A N T S
rem
rem----------------------------------------------------------

dim emsg$(10)
emsg$(01)="PY761 PAY FILE NOT FOUND"
emsg$(02)="PY762 EMP FILE NOT FOUND"
emsg$(03)="PY763 ACT FILE NOT FOUND"
emsg$(04)="PY764 DED FILE NOT FOUND"
emsg$(05)="PY765 NET PAY EXCEEDS SYSTEM MAX. CHECK WILL BE VOIDED"
emsg$(06)="PY766 BATCH TOTAL NOT ZERO"
emsg$(07)="PY767 NET PAY LESS THAN ZERO. CHECK WILL BE VOIDED"

#include "zdateio"
#include "zstring"
#include "ipydmemp"
#include "ipydmded"
#include "ipyedesc"
#include "zbracket"
#include "zheading"
#include "fpyjrn"			rem define screen info

dim acct.no$(pr2.no.acts%)
dim acct.amt(pr2.no.acts%)

dim units(4)
dim total.units(4)
dim sys(pr1.max.sys.eds%)
dim emp(pr1.max.emp.eds%)
dim dist.out(pr1.max.dist.accts%)

dim edo%(pr1.max.ed.cats%)
rem    1=earning
rem    2=deduction
rem    3=other
edo%(01)=01	rem REGULAR PAY
edo%(02)=01	rem OVERTIME PAY
edo%(03)=01	rem SPECIAL OT PAY
edo%(04)=01	rem COMMISSION
edo%(05)=03	rem VACATION TAKEN     NOT ON CHECKS
edo%(06)=03	rem SICK LVE TAKEN     NOT ON CHECKS
edo%(07)=03	rem COMP TIME TAKEN    NOT ON CHECKS
edo%(08)=03	rem COMP TIME EARND    NOT ON CHECKS
edo%(09)=01	rem BONUS
edo%(10)=01	rem TIPS COLLECTED
edo%(11)=03	rem ADVANCE
edo%(12)=01	rem SICK PAY
edo%(13)=01	rem VACATION PAY
edo%(14)=01	rem OTHER EXCLD PAY
edo%(15)=03	rem EXPENSE REIMB
edo%(16)=01	rem EIC
edo%(17)=01	rem OTHER PAY
edo%(18)=01	rem TIPS REPORTED
edo%(19)=03	rem UNUSED
edo%(20)=02	rem FWT
edo%(21)=02	rem SWT
edo%(22)=02	rem LWT
edo%(23)=02	rem FICA
edo%(24)=02	rem SDI
edo%(25)=03	rem UNUSED
edo%(26)=03	rem UNUSED
edo%(27)=02	rem ADVANCE REPAY
edo%(28)=02	rem FWT ADD-ON
edo%(29)=02	rem SWT ADD-ON
edo%(30)=02	rem LWT ADD-ON
edo%(31)=02	rem FICA ADD-ON
edo%(32)=03	rem UNUSED
edo%(33)=00	rem SYS1 FROM DED FILE
edo%(34)=00	rem SYS2 FROM DED FILE
edo%(35)=00	rem SYS3 FROM DED FILE
edo%(36)=00	rem SYS4 FROM DED FILE
edo%(37)=00	rem SYS5 FROM DED FILE
edo%(38)=00	rem EMP1 FROM EMP FILE
edo%(39)=00	rem EMP2 FROM EMP FILE
edo%(40)=00	rem EMP3 FROM EMP FILE
edo%(41)=03	rem UNUSED
edo%(42)=03	rem COMPANY FICA       NOT ON CHECKS
edo%(43)=03	rem COMPANY FUTA       NOT ON CHECKS
edo%(44)=03	rem COMPANY SUI        NOT ON CHECKS
edo%(45)=03	rem UNUSED
edo%(46)=03	rem OTHER CO COST      NOT ON CHECKS
edo%(47)=03	rem UNUSED
edo%(48)=03	rem UNUSED
edo%(49)=03	rem UNUSED
edo%(50)=02	rem OTHER DED

hdr1$="EMPLOYEE PAYROLL DETAIL"

def fn.name.flip$(name$)
	temp%=match("*",name$,1)
	if temp%=0 then fn.name.flip$=name$:return
	fn.name.flip$=					 \
		right$(name$,len(name$)-temp%)		+\
		" "                                     +\
		left$(name$,temp%-1)
	return
fend

def fn.round(rr)=(int((rr*100)+.5))/100

line.cnt%=1000			rem force a new page
page%=0 			rem this is in common, so initialize

gosub 12800			rem initialize common counters

rem----------------------------------------------------------
rem
rem	S E T	    U P
rem
rem----------------------------------------------------------

trash%=fn.put.all%(false%)	rem display.set.up.screen
gosub 500			rem set up files
gosub 510			rem put sys ed types in edo table
trash%=fn.lit%(08)		rem display.process.screen
gosub 6250			rem determine from dates

rem----------------------------------------------------------
rem
rem	M A I N       D R I V E R
rem
rem----------------------------------------------------------

gosub 3000			rem select a pay rec
while not pay.eof%
	last.pay.emp.no$=pay.emp.no$
	gosub 4000		rem get emp rec
	gosub 4100		rem put emp ed types in edo table
	gosub 5000		rem display employee number
	if pr1.debugging% \
		then	trash%=fn.put%("fre: "+str$(fre),03)
	gosub 6000		rem print employee demo line
	if stopit% then goto 99
	gosub 7000		rem clear accums
	while not pay.eof% and pay.emp.no$=last.pay.emp.no$
		gosub 8100	rem accumulate pay info
		gosub 9000	rem print detail line
		if stopit% then goto 99
		gosub 3000	rem select a pay rec

	wend
	gosub 11000		rem calc and print emp info
	gosub 12500		rem distribute offset amounts
	gosub 12700		rem accumulate company totals
	if stopit% then goto 99
wend

rem----------------------------------------------------------
rem
rem	E N D	  O F	  J O B
rem
rem----------------------------------------------------------

99	rem-----here if stop requested-----------------------

lprinter:print:console		rem for centronics printer

close pay.file%
close emp.file%
close act.file%

if stopit% then goto 999.2

chain fn.file.name.out$("pyjourn1",null$,0,pw$,pms$)

#include "zeoj"

rem----------------------------------------------------------
rem
rem	S U B R O U T I N E S
rem
rem----------------------------------------------------------

500	rem-----set up files---------------------------------
	gosub 610			rem get.pay.file
	if pay.exists% \
		then	gosub 620 :\	rem get.pay.hdr
		else	trash%=fn.emsg%(01)   :\
			goto 999.1
	gosub 640			rem get.emp.file
	if not emp.exists% \
		then	trash%=fn.emsg%(02)   :\
			goto 999.1

	gosub 720			rem get act file
	if not act.exists% \
		then	trash%=fn.emsg%(03)   :\
			goto 999.1
	gosub 730			rem read in act hdr
	gosub 740			rem read in act file
	gosub 750			rem get ded file
	if not ded.exists% \
		then	trash%=fn.emsg%(04)   :\
			goto 999.1
	gosub 760			rem read ded file
	close ded.file%
	gosub 800			rem get chk file
	if chk.exists% \
		then	gosub 810 :\	rem read chk hdr
			close chk.file%
	return

510	rem-----put sys ed types in edo table----------------
	for x%=1 to pr1.max.sys.eds%
		if ded.sys.earn.ded$(x%)="E" \
			then	edo%=1	\
			else	edo%=2
		edo%(32+x%)=edo%
	next x%
	return

610	rem-----get pay file---------------------------------
	pay.exists%=false%
	if end #pay.file% then 611
	open fn.file.name.out$(pay.name$,"101",pr1.pay.drive%,pw$,pms$) \
		recl pay.len%  as pay.file%
	pay.exists%=true%
611	rem-----here if pay file not present-----------------
	return

620	rem-----get pay hdr----------------------------------
	read #pay.file%,1;    \
#include "ipypayhd"
	return

640	rem-----get emp file---------------------------------
	emp.exists%=false%
	if end #emp.file% then 641
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pms$) \
		recl emp.len%  as emp.file%
	emp.exists%=true%
641	rem-----here if emp file not present-----------------
	return

720	rem-----get act file---------------------------------
	act.exists%=false%
	if end #act.file% then 721
	open fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pms$) \
		recl act.len%  as act.file%
	act.exists%=true%
721	rem-----here if act file not present-----------------
	return

730	rem-----read in act hdr------------------------------
	read #act.file%,1;    \
#include "ipyacthd"
	return

740	rem-----read in act file-----------------------------
	act.rec%=1
	while act.rec%<=pr2.no.acts%
		gosub 745			rem read act record
		acct.no$(act.rec%)=act.no$
		act.rec%=act.rec%+1
	wend
	return

745	rem-----read act record------------------------------
	read #act.file%,act.rec%+1;\
#include "ipyact"
	return

750	rem-----get ded file---------------------------------
	ded.exists%=false%
	if end #ded.file% then 751
	open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pw$,pms$) \
		recl ded.len%  as ded.file%
	ded.exists%=true%
751	rem-----here if ded file not present-----------------
	return

760	rem-----read ded file--------------------------------
	read #ded.file%;      \
#include "ipyded"
	return

800	rem-----get chk file---------------------------------
	chk.exists%=false%
	if end #chk.file% then 801
	open fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$) \
		recl chk.len%  as chk.file%
	chk.exists%=true%
801	rem-----here if chk file not present-----------------
	return

810	rem-----get chk hdr----------------------------------
	read #chk.file%,1;	\
#include "ipychkhd"
	return

3000	rem-----select a pay rec-----------------------------
	pay.rec%=pay.rec%+1
	gosub 3100			rem get pay rec
	if pay.eof% then return
	while not pay.extended%
		pay.rec%=pay.rec%+1
		gosub 3100		rem get pay rec
		if pay.eof% then return
	wend
	return

3100	rem-----get pay rec----------------------------------
	if pay.rec%>pay.hdr.no.recs% then pay.eof%=true%:return
	read #pay.file%,pay.rec%+1;    \
#include "ipypay"
	return

4000	rem-----get emp rec----------------------------------
	emp.rec%=val(left$(pay.emp.no$,4))
	read #emp.file%,emp.rec%+1;	\
#include "ipyemp"
	return

4100	rem-----put emp ed types in edo table----------------
	for x%=1 to pr1.max.emp.eds%
		if emp.ed.earn.ded$(x%)="E" \
			then	edo%=1	\
			else	edo%=2
		edo%(37+x%)=edo%
	next x%
	return

5000	rem-----display employee number----------------------
	trash%=fn.put%(emp.no$,01)
	return

6000	rem-----print employee demo line---------------------
	gosub 6100			rem string together exempt flags
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print using \
"!/234/    /2345678901234567890123456789/    /234567890/   &";\
		exempt.flag$,\
		emp.no$,\
		fn.name.flip$(emp.emp.name$),\
		emp.ssn$,\
		exemptions$
	console
	return

6100	rem-----string together exempt flags-----------------
	exemptions$=null$
	if emp.fwt.exempt% then exemptions$=exemptions$+",FWT"
	if emp.swt.exempt% then exemptions$=exemptions$+",SWT"
	if emp.lwt.exempt% then exemptions$=exemptions$+",LWT"
	if emp.fica.exempt% then exemptions$=exemptions$+",FICA"
	if emp.sdi.exempt% then exemptions$=exemptions$+",SDI"
	if emp.co.futa.exempt% then exemptions$=exemptions$+",CO FUTA"
	if emp.co.sui.exempt% then exemptions$=exemptions$+",CO SUI"
	if emp.sys.exempt%(1) then exemptions$=exemptions$+",SYS1"
	if emp.sys.exempt%(2) then exemptions$=exemptions$+",SYS2"
	if emp.sys.exempt%(3) then exemptions$=exemptions$+",SYS3"
	if emp.sys.exempt%(4) then exemptions$=exemptions$+",SYS4"
	if emp.sys.exempt%(5) then exemptions$=exemptions$+",SYS5"
	if exemptions$=null$ \
		then	exempt.flag$=" "                        :\
			return					 \
		else	exempt.flag$="*"                        :\
			exemptions$="EXEMPT FROM: "             +\
			 right$(exemptions$,len(exemptions$)-1)
	return

6200	rem-----increment and test lines---------------------
	gosub 6205			rem test lines
	line.cnt%=line.cnt%+1
	return

6205	rem-----test lines-----------------------------------
	if line.cnt%>=pr1.lines.per.page%-2 \
		then	gosub 6210	rem do header
	return

6210	rem-----do header------------------------------------
	lprinter
	line.cnt%=fn.hdr%(fn.spread$(function.name$,1))+3
	console
	gosub 6300			rem check for interruption
	if stopit% then return
	gosub 6220			rem print other hdr line

	lprinter
	print tab(112);"CHECK DATE: ";
	print fn.date.out$(pr2.check.date$)
	console
	line.cnt%=line.cnt%+1
	return


6220	rem-----print other hdr line-------------------------
	lprinter
	print "INTERVAL: ";
	print pay.hdr.interval$;
	print tab(fn.center%(hdr1$,pr1.page.width%));hdr1$;
	print tab(104);"FROM: ";
	print fn.date.out$(from.date$);
	print tab(120);"TO: ";
	print fn.date.out$(chk.hdr.to.date$)
	console
	line.cnt%=line.cnt%+1
	return

6250	rem-----determine from dates-------------------------
	if pr1.s.used% and pr1.m.used% or \
	   pr1.w.used% and pr1.b.used% \
		then	fast.and.slow%=true% \
		else	fast.and.slow%=false%
	if not fast.and.slow% \
		then	gosub 6255 :\	rem get fast or slow date
			return
	if (pay.hdr.interval$="M" and pr1.s.used%) or \
	   (pay.hdr.interval$="B" and pr1.w.used%) \
		then	from.date$=chk.hdr.slow.from.date$ \
		else	from.date$=chk.hdr.fast.from.date$
	return

6255	rem-----get fast or slow date------------------------
	if pay.hdr.interval$="S" or pay.hdr.interval$="W" \
		then	from.date$=chk.hdr.fast.from.date$
	if pay.hdr.interval$="B" or pay.hdr.interval$="M" \
		then	from.date$=chk.hdr.slow.from.date$
	return

6300	rem-----check for interruption-----------------------
	stopit%=false%
	if not constat% then return
	trash%=conchar%
	trash%=fn.lit%(11)
	trash%=fn.lit%(12)
	trash%=fn.get%(02,02)
	trash%=fn.clr%(11)
	trash%=fn.clr%(12)
	if in.status%=req.cr% \
		then	return
	if in.status%=req.stopit% \
		then	stopit%=true%
	if in.status%=req.back% \
		then	stopit%=true%
	return

7000	rem-----clear accums---------------------------------
	reg.wages		=zero
	other.earn		=zero
	gross			=zero
	fwt			=zero
	swt			=zero
	lwt			=zero
	fica			=zero
	sdi			=zero
	eic			=zero
	other.ded		=zero
	net			=zero
	employer.cost		=zero
	tips			=zero
	tips.reported		=zero
	co.fica 		=zero
	co.futa 		=zero
	co.sui			=zero
	comp.earned		=zero
	comp.taken		=zero
	sl.taken		=zero
	vac.taken		=zero
	for i%=1 to 5
		sys(i%) 	=zero
	next i%
	for i%=1 to 3
		emp(i%) 	=zero
	next i%
	for i%=0 to 4
		units(i%)	=zero
	next i%
	first.detail.line%	=true%
	return

8100	rem-----accumulate pay info--------------------------
rem
rem	This routine will accumulate the pay.amt
rem	that has just been read in.
rem	Accumulation is based on the value
rem	of the PAY.REPORTING.CAT% variable.
rem	Note that there is no rate zero, but all other valid
rem	rates are accumulated.
rem
	on pay.reporting.cat% gosub \
		8101,\			rem rate 01
		8102,\			rem rate 02
		8102,\			rem rate 03
		8102,\			rem rate 04
		8105,\			rem rate 05 vacation taken
		8106,\			rem rate 06 sick leave taken
		8107,\			rem rate 07 comp time taken
		8108,\			rem rate 08 comp time earnd
		8109,\			rem rate 09 bonus
		8110,\			rem rate 10 tips collected
		8109,\			rem rate 11 advance
		8109,\			rem rate 12 sick pay
		8109,\			rem rate 13 vacation pay
		8109,\			rem rate 14 other excld pay
		8109,\			rem rate 15 expense reimb
		8116,\			rem rate 16 eic
		8109,\			rem rate 17 other pay
		8118,\			rem rate 18 tips reported
		8151,\			rem rate 19
		8120,\			rem rate 20 fwt
		8121,\			rem rate 21 swt
		8122,\			rem rate 22 lwt
		8123,\			rem rate 23 fica
		8124,\			rem rate 24 sdi
		8151,\			rem rate 25
		8151,\			rem rate 26
		8127,\			rem rate 27 advance repay
		8120,\			rem rate 28 fwt addon
		8121,\			rem rate 29 swt addon
		8122,\			rem rate 30 lwt addon
		8123,\			rem rate 31 fica addon
		8151,\			rem rate 32
		8133,\			rem rate 33 sys1
		8133,\			rem rate 34 sys2
		8133,\			rem rate 35 sys3
		8133,\			rem rate 36 sys4
		8133,\			rem rate 37 sys5
		8138,\			rem rate 38 emp1
		8138,\			rem rate 39 emp2
		8138,\			rem rate 40 emp3
		8151,\			rem rate 41
		8142,\			rem rate 42 company fica
		8143,\			rem rate 43 company futa
		8144,\			rem rate 44 company sui
		8151,\			rem rate 45
		8151,\			rem rate 46 other co cost
		8151,\			rem rate 47
		8151,\			rem rate 48
		8151,\			rem rate 49
		8151			rem rate 50 other ded
	return

8101	rem-----rate 01--------------------------------------
	units(1)=units(1)+pay.units
	reg.wages=reg.wages+pay.amt
	return

8102	rem-----rate 02,03,04--------------------------------
	units(pay.reporting.cat%)=units(pay.reporting.cat%)+pay.units
	other.earn=other.earn+pay.amt
	return

8105	rem-----rate 05 vacation taken-----------------------
	vac.taken=vac.taken+pay.units
	return

8106	rem-----rate 06 sick leave taken---------------------
	sl.taken=sl.taken+pay.units
	return

8107	rem-----rate 07 comp time taken----------------------
	comp.taken=comp.taken+pay.units
	return

8108	rem-----rate 08 comp time earned---------------------
	comp.earned=comp.earned+pay.units
	return

8109	rem-----rate 09 other normal pay types---------------
	other.earn=other.earn+pay.amt
	return

8110	rem-----rate 10 tips collected-----------------------
	tips=tips+pay.amt
	return

8116	rem-----rem rate 16 eic------------------------------
	eic=eic+pay.amt
	return

8118	rem-----rate 18 tips reported------------------------
	tips=tips+pay.amt
	tips.reported=tips.reported+pay.amt
	other.ded=other.ded+pay.amt
	return

8120	rem-----rem rate 20 fwt------------------------------
	fwt=fwt+pay.amt
	return

8121	rem-----rem rate 21 swt------------------------------
	swt=swt+pay.amt
	return

8122	rem-----rem rate 22 lwt------------------------------
	lwt=lwt+pay.amt
	return

8123	rem-----rem rate 23 fica-----------------------------
	fica=fica+pay.amt
	return

8124	rem-----rem rate 24 sdi------------------------------
	sdi=sdi+pay.amt
	return

8127	rem-----rem advance repay rate 27--------------------
	other.ded=other.ded+pay.amt
	return

8133	rem-----rem sys eds----------------------------------
	sys(pay.reporting.cat%-32)=sys(pay.reporting.cat%-32)+pay.amt
	if ded.sys.earn.ded$(pay.reporting.cat%-32)="E" \
		then	other.earn=other.earn+pay.amt \
		else	other.ded=other.ded+pay.amt
	return

8138	rem-----rem emp eds----------------------------------
	emp(pay.reporting.cat%-37)=emp(pay.reporting.cat%-37)+pay.amt
	if emp.ed.earn.ded$(pay.reporting.cat%-37)="E" \
		then	other.earn=other.earn+pay.amt \
		else	other.ded=other.ded+pay.amt
	return

8142	rem-----rem rate 42 co fica--------------------------
	co.fica=co.fica+pay.amt
	employer.cost=employer.cost+pay.amt
	return

8143	rem-----rem rate 43 co futa--------------------------
	co.futa=co.futa+pay.amt
	employer.cost=employer.cost+pay.amt
	return

8144	rem-----rem rate 44 co sui---------------------------
	co.sui=co.sui+pay.amt
	employer.cost=employer.cost+pay.amt
	return

8151	rem-----invalid rates--------------------------------
	print "blooooey"
	stop

9000	rem-----print detail line----------------------------
	if first.detail.line% \
		then	first.detail.line%=false%	:\
			gosub 9100	rem print detail header
	gosub 9150			rem get detail description
	gosub 9170			rem get comp,vac,sl amt
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	on edo%(pay.reporting.cat%) gosub \
		9200,\			rem print earning line
		9300,\			rem print deduction line
		9400			rem print other line
	print				rem trailing crlf for detail line
	console
	return

9050	rem-----print a blank line---------------------------
	gosub 6200			rem increment and test lines
	lprinter
	print
	console
	return

9100	rem-----print detail header--------------------------
	gosub 9050			rem print a blank line
	if stopit% then return
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print using "&";    \
		tab(001);"-------------E A R N I N G S-------------";
	print using "&";    \
		tab(051);"------D E D U C T I O N S------";
	print using "&";    \
		tab(095);"-----------O T H E R-----------"
	console
	gosub 9600			rem print separator line
	if stopit% then return
	return

9150	rem-----get detail description-----------------------
	if pay.reporting.cat%>=01 and \
	   pay.reporting.cat%<=04 \
		then	detail.description$=	\
				pr1.rate.name$(pay.reporting.cat%)  :\
			return

	if pay.reporting.cat%>=33 and \
	   pay.reporting.cat%<=37 \
		then	detail.description$=	\
				ded.sys.desc$(pay.reporting.cat%-32)  :\
			return

	if pay.reporting.cat%>=38 and \
	   pay.reporting.cat%<=40 \
		then	detail.description$=	\
				emp.ed.desc$(pay.reporting.cat%-37)  :\
			return

	detail.description$=ed.desc.table$(pay.reporting.cat%)
	return

9170	rem-----get comp,vac,sl amt--------------------------
	if pay.reporting.cat%>=5 and pay.reporting.cat%<=8 \
		then	pay.amt=pay.units
	return

9200	rem-----print earning line---------------------------
	tab.location%=02
	gosub 9500			rem print details
	print using " ##,###.##";      \
		pay.units;
	print tab(046);"|";             rem print vertical separator
	print tab(088);"|";             rem print vertical separator
	return

9300	rem-----print deduction line-------------------------
	print tab(046);"|";             rem print vertical separator
	tab.location%=51
	gosub 9500			rem print details
	print tab(088);"|";             rem print vertical separator
	return

9400	rem-----print other line-----------------------------
	print tab(046);"|";             rem print vertical separator
	print tab(088);"|";             rem print vertical separator
	tab.location%=95
	gosub 9500			rem print details
	return

9500	rem-----print details--------------------------------
	print using "## /2345678901234/";     \
		tab(tab.location%),\
		pay.reporting.cat%,\
		detail.description$;
	print using " "+fn.bracket$(pay.amt,6,true%);     \
		abs(pay.amt);
	return

9600	rem-----print separator line-------------------------
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print tab(046);"|";             rem print vertical separator
	print tab(088);"|";             rem print vertical separator
	print				rem trailing crlf
	console
	return

11000	rem-----calc and print emp info----------------------
	gosub 9600			rem print separator line
	gosub 11100			rem print units total
	if stopit% then return
	gosub 6205			rem test lines
	gosub 11200			rem print wages and deds line
	if stopit% then return
	if net>emp.max.pay \
		then	gosub 11110	rem print over max warning
	if stopit% then return
	if net>pr1.void.check.amt and pr1.void.chks.over.max% \
		then	gosub 11120	rem print void message
	if stopit% then return
	if net<0 \
		then	gosub 11130	rem print under zero message
	if stopit% then return
	gosub 11300			rem calc distribution
	gosub 11400			rem print distribution line
	if stopit% then return
	return

11100	rem-----print units total----------------------------
	gosub 6205			rem test lines
	units.total=0
	no.totals%=0
	for i%=1 to 4
		line.cnt%=line.cnt%+1
		gosub 6300		rem check for interruption
		if stopit% then return
		if units(i%)=0 \
			then	goto 11101	rem break
		no.totals%=no.totals%+1
		lprinter
		if no.totals%=1 \
			then	print tab(10);"UNITS:";
		print using "/2345678901234/: ##,###.##";\
			tab(17),\
			pr1.rate.name$(i%),\
			units(i%)
		console
		units.total=units.total+units(i%)
11101
	next i%
	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	if no.totals%<=1 then return
	lprinter
	print using "    TOTAL UNITS: ##,###.##";\
		tab(17),\
		units.total
	console
	gosub 9050			rem a blank line
	return

11110	rem-----print over max warning-----------------------
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print \
"*** NET PAY EXCEEDS EMPLOYEE MAXIMUM"
	console
	return

11120	rem-----print void message---------------------------
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	trash%=fn.emsg%(05)
	lprinter
	print \
"*** VOID *** NET PAY EXCEEDS SYSTEM MAXIMUM *** CHECK WILL BE VOIDED ***"
	console
	return

11130	rem-----print under zero message---------------------
	gosub 6200			rem increment and test lines
	gosub 6300			rem check for interruption
	if stopit% then return
	trash%=fn.emsg%(07)
	lprinter
	print \
"*** VOID *** NET PAY IS LESS THAN ZERO *** NO CHECK WILL BE ISSUED ***"
	console
	return

11200	rem-----print wages and deds line--------------------
	gosub 11250			rem calculate gross + net pay
	gosub 11210			rem print hdr and amounts
	return

11210	rem-----print hdr and amounts------------------------
	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print " ";                      rem extra leading blank
	print using " /2345678901/";\
		"   REG WAGES",\
		"  OTHER EARN",\
		"      TIPS  ",\
		"      FWT   ",\
		"      SWT   ",\
		"      LWT   ",\
		"      FICA  ",\
		"      SDI   ",\
		"  OTHER DEDS",\
		"      NET   "
	console

	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print " ";                      rem extra leading blank
	print using "  ###,###.## ";            \
			reg.wages;		\
			other.earn+eic; 	\
			tips;			\
			fwt;			\
			swt;			\
			lwt;			\
			fica;			\
			sdi;			\
			other.ded;
	print using " "+fn.bracket$(net,6,true%);abs(net);
	print				rem trailing crlf
	console
	return

11250	rem-----calc gross and net pay-----------------------
	gross=(reg.wages+other.earn+tips)
	net=(gross+eic)-(fwt+swt+lwt+fica+sdi+other.ded)
	gross=gross-tips.reported
	return

11300	rem-----calc distribution and accum------------------
	gosub 11310			rem determine distributable pay
	for x%=1 to pr1.max.dist.accts%
		dist.out(x%)=					\
			fn.round((emp.dist.percent(x%)/100)*	\
			distributable.pay)			:\
	next x%
	gosub 11320			rem assure that dist amts are exact
	for x%=1 to pr1.max.dist.accts%
		acct.amt(emp.dist.acct%(x%))=		\
			acct.amt(emp.dist.acct%(x%))+	\
			dist.out(x%)
	next x%
	return

11310	rem-----determine distributable pay------------------
	distributable.pay=(gross+employer.cost)
	return

11320	rem-----assure that dist amts are exact--------------
	temp=0
	for x%=1 to pr1.max.dist.accts%
		temp=temp+dist.out(x%)
	next x%
	if temp=distributable.pay \
		then	return
	temp=distributable.pay-temp	rem temp is difference
	x%=1
	while emp.dist.percent(x%)=0
		x%=x%+1
	wend
	dist.out(x%)=dist.out(x%)+temp
	return

11400	rem-----print distribution line----------------------
	line.cnt%=line.cnt%+1
	lprinter
	print				rem print a blank line
	console
	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print " ";                      rem leading blank
	print using " /2345678901/";      \
		"    GROSS   ",\
		"EMPLOYER EXP",\
		" TOTAL COST ",\
		"            ",\
		"            ";
	if pr1.dist.used% \
		then	gosub 11440 \	rem print dist headers
		else	print		rem trailing crlf
	console
	line.cnt%=line.cnt%+1
	gosub 6300			rem check for interruption
	if stopit% then return
	lprinter
	print " ";                      rem extra leading blank
	print using "  ###,###.## ";            \
			gross+eic;			\
			employer.cost;		\
			distributable.pay;
	if pr1.dist.used% \
		then	gosub 11450 \	rem print dist amounts
		else	print		rem trailing crlf
	print:print:print:print
	line.cnt%=line.cnt%+4
	console
	return

11440	rem-----print dist headers----------------------------
	for x%=1 to pr1.max.dist.accts%
		if emp.dist.percent(x%)<>0 \
			then	print using "  ###:/2345/ ";    \
				emp.dist.acct%(x%),		\
				acct.no$(emp.dist.acct%(x%));
	next x%
	return

11450	rem-----print dist amounts----------------------------
	print	    "         DISTRIBUTION:   ";
	for x%=1 to pr1.max.dist.accts%
		if emp.dist.percent(x%)<>0 \
			then	print using " "+fn.bracket$             \
					(dist.out(x%),6,true%); \
					abs(dist.out(x%));
	next x%
	print				rem trailing crlf
	return

12500	rem-----distribute offset amounts--------------------
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
rem	EIC.CREDIT.ACCT (LIAB) is from DED file

rem CALCULATE EARNINGS:
	acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)-\
		gross

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

12700	rem-----accumulate company totals--------------------
	total.reg.wages 	=total.reg.wages+	reg.wages
	total.other.earn	=total.other.earn+	other.earn
	total.tips		=total.tips+		tips
	total.tips.reported	=total.tips.reported+	tips.reported
	total.fwt		=total.fwt+		fwt
	total.swt		=total.swt+		swt
	total.lwt		=total.lwt+		lwt
	total.fica		=total.fica+		fica
	total.sdi		=total.sdi+		sdi
	total.other.ded 	=total.other.ded+	other.ded
	total.net		=total.net+		net
	total.eic		=total.eic+		eic
	total.co.fica		=total.co.fica+ 	co.fica
	total.co.futa		=total.co.futa+ 	co.futa
	total.co.sui		=total.co.sui+		co.sui
	total.vac.taken 	=total.vac.taken+	vac.taken
	total.sl.taken		=total.sl.taken+	sl.taken
	total.comp.taken	=total.comp.taken+	comp.taken
	total.comp.earned	=total.comp.earned+	comp.earned
	total.units(01) 	=total.units(01)+	units(01)
	total.units(02) 	=total.units(02)+	units(02)
	total.units(03) 	=total.units(03)+	units(03)
	total.units(04) 	=total.units(04)+	units(04)
	return

12800	rem-----initialize common counters-------------------
	total.reg.wages 	=zero
	total.other.earn	=zero
	total.tips		=zero
	total.tips.reported	=zero
	total.fwt		=zero
	total.swt		=zero
	total.lwt		=zero
	total.fica		=zero
	total.sdi		=zero
	total.other.ded 	=zero
	total.net		=zero
	total.eic		=zero
	total.co.fica		=zero
	total.co.futa		=zero
	total.co.sui		=zero
	total.vac.taken 	=zero
	total.sl.taken		=zero
	total.comp.taken	=zero
	total.comp.earned	=zero
	total.units(1)		=zero
	total.units(2)		=zero
	total.units(3)		=zero
	total.units(4)		=zero
	return
