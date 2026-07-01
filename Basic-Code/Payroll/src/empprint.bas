#include "ipycomm"
prgname$="EMPPRINT    16-JAN-80"
#include "ipyconst"


rem----------------------------------------------------------------------
rem
REM
REM		EMPLOYEE MASTER PRINT
REM
REM		(EMPPRINT)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "EMPLOYEE MASTER PRINT"

REM
REM	FOLLOWING IS A GUIDE TO SUBROUTINES IN EMPPRINT
REM

REM	20	GET SELECTION FROM USER
REM	30	GET RANGE
REM	40	GET FULL OR SINGLE MODE INFO
REM	50	PROCESSING MESSAGE
REM	60	CLEAR SCREEN OF UNNEEDED FIELDS

REM	100	MAIN DRIVER FOR PRINTING CYCLE

REM	1000	PRINT HEADER
REM	1010	PRINT "REPORT CONTINUES"
REM	1020	PRINT "END OF REPORT"

REM	1100	PRINT SELECTED EMPLOYEE FULL MODE
REM	1200	PRINT SELECTED EMP SINGLE LINE MODE
REM	1250	GET EMPLOYEE FIELDS PRINTABLE
REM	1290	PRINT SINGLE LINE TITLES
REM	1300	PRINT DELETED EMPLOYEE

REM	2000	READ EMPLOYEE RECORD
REM	2100	CHECK EMPLOYEE FOR SELECTION STATUS
REM	2200	PRINT CURRENT EMP.NO$ ON SCREEN

REM	3000	READ ACCOUNT RECORD



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

#include "znumeric"
#include "zstring"
#include "zdateio"
#include "zfilconv"
#include "zckdigit"
#include "zheading"
#include "zflip"
#include "zdspyorn"

#include "ipystat"
#include "ipydmemp"



rem
rem	error messages
rem
	dim emsg$(30)
	emsg$(1) = "     PY671 INVALID RESPONSE"
	emsg$(2) = "     PY672 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY673 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY674 UNEXPECTED END OF EMPLOYEE FILE"
	emsg$(5) = "     PY675 SELECTION MUST BE 1 TO 14"
	emsg$(6) = "     PY676 INVALID OR NON-EXISTANT EMPLOYEE NUMBER"
	emsg$(7) = "     PY677 FROM NUMBER MUST NOT BE GREATER THAN TO NUMBER"
	emsg$(8) = "     PY678 TO NUMBER MUST NOT TO BE LESS THAN FROM NUMBER"
	emsg$(9) = "     PY679 ANSWER MUST BE 'F' OR 'S'"
	emsg$(10)= "     PY680 UNEXPECTED END OF ACCOUNT FILE"
	emsg$(11)= "     PY681 INVALID ACCOUNT NUMBER"

REM
REM	SELECTED OPTION TABLE IS USED FOR HEADING REPORT
REM

	dim option.title$(14)

	option.title$(1)="ALL EMPLOYEES"
	option.title$(2)="ALL WEEKLY EMPLOYEES"
	option.title$(3)="ALL BI-WEEKLY EMPLOYEES"
	option.title$(4)="ALL SEMI-MONTHLY EMPLOYEES"
	option.title$(5)="ALL MONTHLY EMPLOYEES"
	option.title$(6)="ALL WEEK BASED EMPLOYEES"
	option.title$(7)="ALL MONTH BASED EMPLOYEES"
	option.title$(8)="ALL HOURLY EMPLOYEES"
	option.title$(9)="ALL SALARIED EMPLOYEES"
	option.title$(10)="ALL ACTIVE EMPLOYEES"
	option.title$(11)="ALL ON-LEAVE EMPLOYEES"
	option.title$(12)="ALL TERMINATED EMPLOYEES"
	option.title$(13)="ALL DELETED EMPLOYEES"
	option.title$(14)="A RANGE OF EMPLOYEES"

program$ = "EMPPRINT"
null$ = ""
nul$ = null$

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2



rem
rem	get screen set up
rem

#include "fpyempp"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	first.selection.lit.offset% = 9
	fld.select% = 1
	fld.from% = 2
	fld.to% = 3
	fld.full.single% = 4
	fld.now.processing% = 5

	lit.range% = 25
	lit.mode% = 26
	lit.processing% = 27

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP




rem
rem	open EMP file
rem

	if end #emp.file% then 998
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,null$,null$)\
		recl emp.len% as emp.file%

rem
rem	file exists so read in header and proceed
rem

	read #emp.file% ,1;	\
#include "ipyemphd"

REM
REM	OPEN ACCOUNT FILE AND READ IN HEADER
REM

	if end #act.file% then 997
	open fn.file.name.out$(act.name$,"101",pr1.act.drive%,null$,null$) \
		recl act.len% as act.file%

	read #act.file% , 1; \
#include "ipyacthd"

REM
REM	INIT OTHER STUFF
REM

	line.count.limit% = pr1.lines.per.page%
	deleted.option% = 13
	range.option% = 14



REM
REM	CRT INPUT DRIVER
REM

	while true%
		gosub 20	REM GET SELECTION
		if stopit% then goto 10 REM EXIT REQUESTED

		gosub 30	REM GET RANGE
		if stopit% then goto 10 REM EXIT REQUESTED

		gosub 40	REM FULL OR SINGLE MODE
		if stopit% then goto 10 REM EXIT REQUESTED

		gosub 50	REM PROCESSING MESSAGE

		gosub 100	REM MAIN PRINTING DRIVER

		gosub 60	REM CLEAR TEMP FIELDS FROM SCREEN
	wend

 10
	trash% = fn.msg%("     STOP REQUESTED")
	close emp.file%
	close act.file%
	goto 999		REM NORMAL EXIT



 20	REM GET SELECTION REQUEST FROM USER

	if selected.option% <> 0 \
	   then \	REM DIM OLD SELECTION
		trash% = fn.set.brt%(false%,first.selection.lit.offset% + \
			selected.option%) :\
		trash% = fn.lit%(first.selection.lit.offset% +selected.option%)

	ok% = false%
	while not ok%
		trash% = fn.clr%(1)	REM CLEAR OLD INPUT
		trash% = fn.get%(1,fld.select%)
		if pr1.debugging% \
		   then \
			trash% = fn.msg%("fre=" + str$(fre))

		if in.status% = req.stopit% \
		   then \
			stopit% = true% :\
			return

		if not fn.num%(in$) \
		   then \
			trash% = fn.emsg%(5) :\ REM MUST BE 1-14
			goto 20.1	REM GOTO END OF WHILE

		selected.option% = val(in$)
		if selected.option% < 1 or selected.option% > 14 \
		   then \
			trash% = fn.emsg%(5)	\	REM MUST BE 1-14
		   else \
			ok% = true% :\
			trash% = fn.put%(right$(" "+in$,2),1) :\
			trash% = fn.set.brt%(true%,first.selection.lit.offset%\
				+selected.option%) :\
			trash% =fn.lit%(first.selection.lit.offset%+ \
				selected.option%)
 20.1	wend
	return



 30	REM GET RANGE OF EMPLOYEES TO PRINT

	range.from% = 1
	range.to% = emp.hdr.no.recs%
	if selected.option% <> range.option% \
	   then \
		return	REM RANGE IS ALL EMPLOYEES UNLESS SPECIFIED

	REM GET CHECK DIGIT FORM OF DEFAULTS
	range.from$ = "00014"
	range.to$ = str$(range.to%)
	if len(range.to$) <> 4 \
	   then \
		range.to$ = left$("0000",4-len(range.to$)) + range.to$
	range.to$ = range.to$ + fn.ck.dig$(range.to$)

	trash% = fn.lit%(lit.range%)
	trash% = fn.set.used%(true%,fld.from%)
	trash% = fn.set.used%(true%,fld.to%)
	trash% = fn.put%(range.from$,fld.from%)
	trash% = fn.put%(range.to$,fld.to%)

	range.set% = false%
	while not range.set%
		gosub 30.1	REM GET FROM FIELD
		if stopit% then return
		gosub 30.2	REM GET TO FIELD
		if stopit% then return
	wend
	return

 30.1	REM GET AND CHECK FROM INPUT

	ok% = false%
	while not ok%
		trash% = fn.put%(range.from$,fld.from%)
		trash% = fn.get%(2,fld.from%)
		trash% = fn.msg%(null$) REM ERASE OLD ERROR MESSAGE

		if in.status% = req.cr% then return

		if in.status% = req.back% then return

		if in.status% = req.stopit% then stopit%=true% : return

		gosub 30.3	REM CHECK EMP NUMBER SYNTAX
		if not ok% then goto 30.E1	REM END OF WHILE

		if in.number% > range.to% \
		    then \
			trash% = fn.emsg%(7) :\ REM FROM > TO
			ok% = false% \
		    else \
			range.from$ = in$ :\
			range.from% = in.number%
 30.E1	wend
	return

 30.2	REM OBTAIN AND CHECK TO INPUT

	ok% = false%
	while not ok%
		trash% = fn.put%(range.to$,fld.to%)
		trash% = fn.get%(2,fld.to%)
		trash% = fn.msg%(null$) REM ERASE OLD ERROR MESSAGE

		if in.status% = req.cr% then range.set%=true% : return

		if in.status% = req.back% then return

		if in.status% = req.stopit% then stopit%=true% : return

		gosub 30.3	REM CHECK NUMBER SYNTAX
		if not ok% then goto 30.E2	REM END OF WHILE

		if in.number% < range.from% \
		   then \
			trash% = fn.emsg%(8) :\ REM TO < FROM
			ok% = false% \
		   else \
			range.to$ = in$ :\
			range.to% = in.number% :\
			range.set% = true%
 30.E2	wend
	return

 30.3	REM CHECK EMP NUMBER SYNTAX AND EXISTANCE

	if in.len% <> 5 \
	   then \
		trash% = fn.emsg%(6) :\ REM INVALID EMP NUMVBER
		return

	if fn.ck.dig$(left$(in$,4)) <> right$(in$,1) \
	   then \	REM INVALID CHECK DIGIT
		trash% = fn.emsg%(6) :\
		return

	in.number% = val(left$(in$,4))
	if in.number% < 1 or in.number% > emp.hdr.no.recs% \
	   then \	REM EMP NOT IN FILE
		trash% = fn.emsg%(6) :\
		return

	ok% = true%
	return



 40	REM GET FULL OR SINGLE LINE MODE

	trash% = fn.lit%(lit.mode%)
	trash% = fn.set.used%(true%,fld.full.single%)

	ok% = false%
	while not ok%
		trash% = fn.get%(1,fld.full.single%)
		trash% = fn.msg%(null$) REM ERASE OLD ERROR MESSAGE
		if in.status% = req.stopit% \
		   then \
			stopit% = true% :\
			return

		if in.uc$ = "F" or in.uc$ = "S" \
		   then \
			ok% = true% :\
			trash% = fn.put%(in.uc$,fld.full.single%) \
		   else \
			trash% = fn.emsg%(9)	REM MUST BE F OR S
	wend
	if in.uc$ = "F" \
	   then \
		full.single.mode% = 1	\	REM GOSUB VALUE
	   else \
		full.single.mode% = 2
	return



 50	REM PROCESSING MESSAGE

	trash% = fn.lit%(lit.processing%)
	return

 60	REM CLEAR SCREEN OF UNNEEDED FIELDS UPON PROCESSING COMPLETION

	if selected.option% = range.option% \
	   then \
		trash% = fn.clr%(fld.from%) :\
		trash% = fn.set.used%(false%,fld.from%) :\
		trash% = fn.clr%(fld.to%) :\
		trash% = fn.set.used%(false%,fld.to%) :\
		trash% = fn.clr%(lit.range%)

	trash% = fn.clr%(fld.full.single%)
	trash% = fn.clr%(lit.mode%)
	trash% = fn.clr%(fld.now.processing%)
	trash% = fn.clr%(lit.processing%)
	return



REM
REM	MAIN DRIVER FOR PRINTING PROCESSING
REM

 100
	current.emp.record% = range.from%
	stop.print% = false%
	line.count% = line.count.limit% REM FORCE HEADING AT BEGGINGING
	lprinter
	page% = 0

while not stop.print% and current.emp.record% <= range.to%
	gosub 2000	REM READ EMPLOYEE
	gosub 2200	REM DISPLAY EMP NUMBER ON SCREEN
	gosub 2100	REM CHECK SELECTION STATUS
	if pr1.debugging% \
	   then \
		console :\
		trash% = fn.msg%("fre="+str$(fre)) :\
		lprinter

	if not emp.is.selected% \
	   then \
		goto 100.1	REM GO TO NEXT EMPLOYEE

	if emp.is.deleted% and selected.option% <> deleted.option% \
	   then \
		gosub 1300	\ REM DELETED SINGLE LINE PRINT
	   else \
		on full.single.mode% gosub \
			1100, \ REM FULL PRINT
			1200	REM SINGLE LINE PRINT

 100.1	current.emp.record% = current.emp.record% + 1
wend

	if not stop.print% \
	   then \
		gosub 1020	REM PRINT END OF REPORT LINE

	console
	return



REM
REM	UNEXPECTED END OF ACCOUNT FILE
REM

 997
	console
	trash% = fn.emsg%(10)	REM UNEXPECTED END OF ACCOUNT FILE
	goto 999.1	REM ABNORMAL EXIT

REM
REM	UNEXPECTED END OF EMPLOYEE FILE
REM

 998
	console
	trash% = fn.emsg%(4)	REM UNEXPECTED END OF EMPLOYEE FILE
	goto 999.1	REM ABNORMAL EXIT

#include "zeoj"



 1000	REM PRINT HEADING

	line.count% = fn.hdr%(function.name$)
	print tab(fn.center%(option.title$(selected.option%),page.width%)); \
		option.title$(selected.option%) ;
	print
	line.count% = line.count% + 2
	return


 1010	REM PRINT *** REPORT CONTINUES ***

	if page% <> 0 \ 	REM SKIP CONTINUES MESSAGE IF AT BEGGINGING
	   then \		REM OF REPORT
		print "     *** REPORT CONTINUES ***"
	return


 1020	REM PRINT *** END OF REPORT ***

	if page% = 0 \
	   then \
		gosub 1000 :\	REM PRINT HEADER
		print :\
		print tab(30);"*** NO EMPLOYEES MET SELECTION CRITERION ***" :\
		print

	print "     *** END OF REPORT ***"
	print
	return



 1100	REM FULL TOTAL DETAIL EMPLOYEE PRINT

	REM ONE EMPLOYEE TO A PAGE
	gosub 1010	REM CONTINUED LINE
	gosub 1000	REM PRINT HEADER
	stop.print% = fn.abort%
	if stop.print% then return

	gosub 1250	REM GET EMPLOYEE FIELDS PRINTABLE

	REM AND AWAY WE GO
	print
	print tab(39);"SOCIAL SECURITY"; \
		tab(69);"HEAD-OF"; \
		tab(87);"TAXING"; \
		tab(95);"PENSION"; \
		tab(107);"BANK ACCOUNT"
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(3);"NO."; \
		tab(11);"NAME AND ADDRESS"; \
		tab(43);"NUMBER"; \
		tab(56);"SEX"; \
		tab(60);"MARRIED"; \
		tab(68);"HOUSEHOLD"; \
		tab(79);"STATUS"; \
		tab(88);"STATE"; \
		tab(96);"PLAN"; \
		tab(110);"NUMBER"
	stop.print%=fn.abort%
	if stop.print% then return

	print
	REM NAME LINE
	print tab(2);emp.no$; \
		tab(9);fn.name.flip$(emp.emp.name$); \
		tab(41);emp.ssn$; \
		tab(57);emp.sex$; \
		tab(63);emp.marital$; \
		tab(71);head$; \	REM CONVERTED FIELD
		tab(77);status$; \	REM CONVERTED FIELD
		tab(89);pr1.co.state$; \REM emp.taxing.state$ NOT USED AT PRESENT
		tab(97);pension$; \	REM CONVERTED FIELD
		tab(103);emp.bank.acct.no$
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(9);emp.addr1$
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(9);emp.addr2$; \
		tab(50);"DATE"; \
		tab(99);"RATE"; \
		tab(108);"ACCUMULATED"; \
		tab(123);"USED"
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(9);emp.city$; \
		tab(28);emp.state$; \
		tab(31);emp.zip$; \
		tab(38);"BIRTH"; \
		tab(48);birth.date$; \	REM CONVERTED FIELD
		tab(59);"JOB CODE:"; \
		tab(69);emp.job.code$; \
		tab(83);"VACATION";
	print using "###,###.##"; \
		tab(93);emp.vac.rate; \
		tab(105);emp.vac.accum; \
		tab(117);emp.vac.used
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(12);emp.phone$; \
		tab(38);"START"; \
		tab(48);start.date$; \	REM CONVERTED FIELD
		tab(59);"INTERVAL:"; \
		tab(69);pay.interval$; \	REM CONVERTED FIELD
		tab(83);"SICK LEAVE";
	print using "###,###.##"; \
		tab(93);emp.sl.rate; \
		tab(105);emp.sl.accum; \
		tab(117);emp.sl.used
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(38);"TERMINATE"; \
		tab(48);terminated.date$; \	REM CONVERTED FIELD
		tab(59);"PAY TYPE:"; \
		tab(69);hs.type$; \	REM CONVERTED FIELD
		tab(83);"COMP TIME";
	print using "###,###.##"; \
		tab(105);emp.comp.accum; \
		tab(117);emp.comp.used
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(59);"PAY FREQUENCY: " + str$(emp.pay.freq%)
	stop.print% = fn.abort%
	if stop.print% then return


	print
	print tab(48);"PAY RATES"; \
		tab(101);"FWT  SWT  LWT"
	stop.print%=fn.abort%
	if stop.print% then return

REM
REM	NOW TO RATE WAD OF STUFF
REM
	print tab(8);"CURRENT APPLY NO:"; \
		tab(26);str$(emp.cur.apply.no%); \
		tab(32);pr1.rate.name$(1);
	print using "###,###.##"; \
		tab(47);emp.rate(1);
	print tab(62);"NUMBER OF WITHOLDING ALLOWANCES:";
	print using "###"; \
		tab(101);emp.fwt.allow%; \
		tab(106);emp.swt.allow%; \
		tab(111);emp.lwt.allow%;
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(32);pr1.rate.name$(2);
	print using "###,###.##"; \
		tab(47);emp.rate(2);
	print tab(62);"NUMBER OF DEDUCTION ALLOWANCES (CAL):";
	print using "###"; \
		tab(106);emp.cal.ded.allow%
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(32);pr1.rate.name$(3);
	print using "###,###.##"; \
		tab(47);emp.rate(3)
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(32);pr1.rate.name$(4);
	print using "###,###.##"; \
		tab(47);emp.rate(4);
	print tab(62);"TAX EXEMPTIONS:";

	REM OBTAIN EXEMPTION STRING
	exempt$ = null$
	if emp.fwt.exempt% then exempt$ = exempt$ + "FWT "
	if emp.swt.exempt% then exempt$ = exempt$ + "SWT "
	if emp.lwt.exempt% then exempt$ = exempt$ + "LWT "
	if emp.fica.exempt% then exempt$ = exempt$ + "FICA "
	if emp.sdi.exempt% then exempt$ = exempt$ + "SDI "
	if emp.co.futa.exempt% then exempt$ = exempt$ + "FUTA "
	if emp.co.sui.exempt% then exempt$ = exempt$ + "SUI "
	for i% = 1 to pr1.max.sys.eds%
		if emp.sys.exempt%(i%) \
		   then exempt$ = exempt$ + "SYS" + str$(i%) + " "
	next i%

	print tab(79);exempt$
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(32);"MAXIMUM";
	print using "###,###.##"; \
		tab(47);emp.max.pay;
	if emp.eic.used% \
	   then \
		eic$ = "ELIGIBLE" \
	   else \
		eic$ = "INELIGIBLE"
	print tab(62);"EARNED INCOME CREDIT: "+eic$
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(62);pr1.rate.name$(4)+" EXCLUSION CODE: "+ \
		str$(emp.rate4.exclusion%)
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(32);"AUTO GENERATED UNITS: " + str$(emp.auto.units); \
		tab(62);"NORMAL PAY UNITS: " + str$(emp.normal.units)
	print
	stop.print%=fn.abort%
	if stop.print% then return


REM
REM	PRINT EMPLOYEE SPECIFIC DEDUCTIONS
REM

	print tab(63);"EMPLOYEE SPECIFIC DEDUCTIONS"
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(36);"DESCRIPTION                  ACCT            FACTOR              LIMIT    XCLD CHECK CATEGORY"
	stop.print%=fn.abort%
	if stop.print% then return

	print
	for i% = 1 to pr1.max.emp.eds%
		if emp.ed.chk.cat%(i%) = 0 \
		   then \
			print tab(22);"NOT";
		print tab(26);"USED"; \
			tab(31);str$(i%); \
			tab(32);":";
		print tab(34);emp.ed.desc$(i%);
		if emp.ed.earn.ded$(i%) = "E" \
		   then \
			print tab(52);"Earning"; \
		   else \
			print tab(52);"Deduction";
		print using "###"; tab(64);emp.ed.acct.no%(i%);
		if emp.ed.amt.percent$(i%) = "A" \
		   then \
			print tab(70);"Amount"; \
		   else \
			print tab(70);"Percent";
		print using "###,###.##";tab(78);emp.ed.factor(i%);
		if emp.ed.limit.used%(i%) \
		   then \
			print tab(89);"Limited"; \
		   else \
			print tab(89);"No Limit";
		print using "#,###,###.##";tab(99);emp.ed.limit(i%);
		print tab(113);str$(emp.ed.exclusion%(i%));
		print using "##";tab(117);emp.ed.chk.cat%(i%)
		stop.print%=fn.abort%
		if stop.print% then return
	next i%



REM
REM	PRINT COST DISTRIBUTION INFO
REM

	print
	print tab(63);"COST DISTRIBUTION"
	stop.print%=fn.abort%
	if stop.print% then return

	print tab(50);"ACCT"; \
		tab(67);"NAME"; \
		tab(87);"PERCENT"
	stop.print%=fn.abort%
	if stop.print% then return

	print
	for i% = 1 to pr1.max.dist.accts%
		if emp.dist.percent(i%) = 0 \
		   then goto 1100.9	REM SKIP PRINTING IF ZERO DISTRIBUTION
		print using "###";tab(51);emp.dist.acct%(i%);
		current.act.record% = emp.dist.acct%(i%)
		if current.act.record% = 0 or \ REM DONT READ ACCOUNT ZERO
		current.act.record%>act.hdr.no.recs% \REM BEYOND LEGAL ACCOUNTS
		   then \
			act.desc$ = "*** INVALID ACCT ***" :\
			console :\
			trash% = fn.emsg%(11) :\ REM INVALID ACCOUNT
			lprinter	:\
		   else \
			gosub 3000	REM READ ACCOUNT RECORD
		print tab(56);act.desc$;
		print using "###.##";tab(87);emp.dist.percent(i%)
		stop.print% = fn.abort%
		if stop.print% then return
 1100.9 next i%

	print
	line.count% = line.count% + 37
	return



 1200	REM PRINT SELECTED EMPLOYEE IN SHORT MODE

	if line.count% + 2 > line.count.limit% \
	   then \
		gosub 1010 :\	REM CONTINUED LINE
		gosub 1000 :\	REM PRINT HEADER
		gosub 1290	REM PRINT TITLES

	if stop.print% then return	REM PRINT TITLES CHECKS FN.ABORT

	gosub 1250	REM GET FIELDS PRINTABLE

	print	tab(2);emp.no$; \
		tab(8);fn.name.flip$(emp.emp.name$); \
		tab(39);emp.ssn$; \
		tab(51);pay.interval$; \
		tab(64);status$; \
		tab(75);hs.type$; \
		tab(82);emp.phone$; \
		tab(96);start.date$; \
		tab(105);birth.date$;
	print using "##,###.##"; tab(114);emp.rate(1);
	print tab(127);emp.job.code$
	print

	line.count% = line.count% + 2
	stop.print%=fn.abort%
	return



REM
REM	GET EMPLOYEE FIELDS PRINTABLE
REM
 1250

	REM GET INTERVAL PRINTABLE
	if emp.pay.interval$ = "W" then pay.interval$ = "Weekly"
	if emp.pay.interval$ = "B" then pay.interval$ = "Bi-weekly"
	if emp.pay.interval$ = "S" then pay.interval$ = "Semi-monthly"
	if emp.pay.interval$ = "M" then pay.interval$ = "Monthly"

	REM GET STATUS PRINTABLE
	if emp.status$ = "A" then status$ = "Active"
	if emp.status$ = "L" then status$ = "On leave"
	if emp.status$ = "T" then status$ = "Terminated"
	if emp.status$ = "D" then status$ = "Deleted"

	REM GET HOURS TYPE PRINTABLE
	if emp.hs.type$ = "H" \
	   then \
		hs.type$ = "Hourly" \
	   else \
		hs.type$ = "Salary"

	REM GET DATES PRINTABLE
	start.date$ = fn.date.out$(emp.start.date$)
	birth.date$ = fn.date.out$(emp.birth.date$)
	termination.date$ = fn.date.out$(emp.term.date$)

	REM GET HEAD OF HOUSEHOLD PRINTABLE
	if emp.cal.head.of.house% \
	   then \
		head$ = "YES" \
	   else \
		head$ = "NO"

	REM GET PENSION PRINTABLE
	if emp.pension.used% \
	   then \
		pension$ = "YES" \
	   else \
		pension$ = "NO"

	return



 1290	REM PRINT SHORT MODE TITLES

	print
	print tab(3);"NO."; \
		tab(10);"NAME"; \
		tab(42);"S.S.N."; \
		tab(50);"PAY INTERVAL"; \
		tab(64);"STATUS"; \
		tab(76);"TYPE"; \
		tab(84);"PHONE"; \
		tab(97);"START"; \
		tab(106);"BIRTH"; \
		tab(117);"RATE 1"; \
		tab(125);"JOB CODE"
	stop.print% = fn.abort%

	line.count% = line.count% + 2
	return



 1300	REM PRINT DELETED EMPLOYEE

	if line.count% + 2 < line.count.limit% \
		then goto 1300.1	REM DON'T BOTHER WITH NEW HEADER

	gosub 1010	REM PRINT CONTINUES MESSAGE
	gosub 1000	REM PRINT HEADER
	if full.single.mode% = 2 \	REM SINGLE MODE
	   then \
		gosub 1290	REM PRINT SHORT MODE TITLES

	if stop.print% then return	REM PRINT TITLES CHECKS FN.ABORT

 1300.1 REM DO ACTUAL PRINTING
	print	tab(2);emp.no$; \
		tab(12);"DELETED EMPLOYEE:("; \
		tab(31);fn.name.flip$(emp.emp.name$); \
		tab(61);") (Number availible for reuse.)"
	print
	stop.print% = fn.abort%
	line.count% = line.count% + 2
	return



 2000	REM READ EMPLOYEE RECORD

	read #emp.file%,current.emp.record% + 1; \
#include "ipyemp"
	return



 2100	REM CHECK EMPLOYEE FOR SELECTION STATUS AND SET DELETED FLAG

	emp.is.selected% = false%

	on selected.option% gosub \
		2100.1, \ REM ALL
		2100.2, \ REM WEEKLY
		2100.3, \ BI-WEEKLY
		2100.4, \ SEMI-MONTHLY
		2100.5, \ MONTHLY
		2100.6, \ WEEK BASED
		2100.7, \ MONTH BASED
		2100.8, \ HOURLY
		2100.9, \ SALARIED
		2100.10, \ ACTIVE
		2100.11, \ ON-LEAVE
		2100.12, \ TERMINATED
		2100.13, \ DELETED
		2100.1		REM RANGE OF ALL

	if emp.status$ = "D" \
	   then \
		emp.is.deleted% = true% \
	   else \
		emp.is.deleted% = false%

	return



REM
REM	SELECTION SUBROUTINES
REM

 2100.1 REM ALL

	emp.is.selected% = true% : return

 2100.2 REM WEEKLY

	if emp.pay.interval$ = "W" then emp.is.selected%=true%
	return

 2100.3 REM BI-WEEKLY

	if emp.pay.interval$ = "B" then emp.is.selected%=true%
	return

 2100.4 REM SEMI-MONTHLY

	if emp.pay.interval$ = "S" then emp.is.selected%=true%
	return

 2100.5 REM MONTHLY

	if emp.pay.interval$ = "M" then emp.is.selected%=true%
	return

 2100.6 REM WEEK BASED

	if emp.pay.interval$="W" or emp.pay.interval$="B" \
	   then emp.is.selected% = true%
	return

 2100.7 REM MONTH BASED

	if emp.pay.interval$="S" or emp.pay.interval$="M" \
	   then emp.is.selected% = true%
	return

 2100.8 REM HOURLY

	if emp.hs.type$ = "H" then emp.is.selected%=true%
	return

 2100.9 REM SALARIED

	if emp.hs.type$ = "S" then emp.is.selected%=true%
	return

 2100.10	REM ACTIVE

	if emp.status$ = "A" then emp.is.selected%=true%
	return

 2100.11	REM ON-LEAVE

	if emp.status$ = "L" then emp.is.selected%=true%
	return

 2100.12	REM TERMINATED

	if emp.status$ = "T" then emp.is.selected%=true%
	return

 2100.13	REM DELETED

	if emp.status$ = "D" then emp.is.selected%=true%
	return



 2200	REM PUT EMP NO ON SCREEN

	console
	trash% = fn.put%(emp.no$,fld.now.processing%)
	lprinter
	return


 3000	REM READ AN ACCOUNT RECORD

	read #act.file% , current.act.record% + 1 ; \
#include "ipyact"
	return

	end
