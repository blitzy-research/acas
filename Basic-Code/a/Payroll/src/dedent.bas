$include  "ipycomm"
prgname$="DEDENT    10-JAN-1980"
$include  "ipyconst"

rem----------------------------------------------------------------------
rem
rem		D E D U C T I O N
REM
REM		E N T R Y
REM
REM		(DEDENT)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "DEDUCTION ENTRY MENU"

rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------

$include  "zdms"
$include  "zdmsconf"
$include  "znumber"
$include  "zstring"
$include  "zdateio"
$include  "zfilconv"

$include  "ipystat"
$include  "ipydmded"

	dim emsg$(30)
	emsg$(1 ) = "     PY351 DEDENT MUST BE RUN FROM PY MENU"
	emsg$(3 ) = "     PY353 PYDED - DEDUCTION FILE NOT PRESENT"
	emsg$(4 ) = "     PY354 IMPROPERLY FORMED NUMBER OR OUT OF RANGE"
	emsg$(7 ) = "     PY357 INVALID USE OF CONTROL CHARACTER"


program$ = "DEDENT"
	if pr1.default.dist.acct% = 0 then pr1.default.dist.acct% = 1

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(1)	:\
			goto 999.2

rem
rem	get screen set up
rem

$include  "fpyded"
	trash% = fn.put.all%(false%)

REM
REM	STARTUP CONTROL
REM

	if match(in.dedent$,common.chaining.status$,1) = 0 and \
	   match(startup$,common.chaining.status$,1) <> 0 and \
	size(fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,null$,null$))=0 \
	   then \
		gosub 700	REM CREATE DED FILE

rem
rem	set chaining status to in dedent
rem

	common.chaining.status$ = common.chaining.status$ + in.dedent$

	if match(default$,common.chaining.status$,1) <> 0 \
	   then \	REM ONLY CREATE DED FILE FOR DEFAULT
		chain fn.file.name.out$("PYSRTPRM",null$,0,null$,null$)

rem
rem	check for DED file existance
rem

	if end #ded.file% then 500
	open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,null$,null$) \
		as ded.file%

rem
rem	file exists so close and proceed
rem

	close ded.file%


rem
rem	obtain desired action
rem

 100
 105	trash% = fn.get%(1,1)
	if pr1.debugging% \
	   then \
		trash% = fn.msg%("fre="+str$(fre))

	if in.status% = req.valid% \
		then goto 107	rem no control chars are valid if any data

	trash% = fn.msg%("     STOP REQUESTED")
	goto 997	REM GO DECIDE WHERE TO CHAIN TO

rem
rem	check data's validity
rem

 107
	if in$ = "1"    \
	   then \	rem standard deduction entry
		chain fn.file.name.out$("DEDENT1",null$,0,null$,null$)


	if in$ = "2"    \
	   then \	rem federal witholding table entry
		chain fn.file.name.out$("DEDENT2",null$,0,null$,null$)


	if in$ = "3"    \
	   then \	rem company earning/deduction entry
		chain fn.file.name.out$("DEDENT3",null$,0,null$,null$)

	trash% = fn.emsg%(4)	REM INVALID RESPONSE
	goto 105	rem invalid response to request again


rem
rem	ded file does not exist, so verify that this is okay
rem

 500	\
	trash% = fn.msg%("PYDED-DEDUCTION FILE DOES NOT EXIST,WILL BE CREATED")
	if not fn.confirmed%	\
	   then \
		goto 999	\rem user does not wish file creation
	   else \
		trash% = fn.put.all%(false%) :\ REM CLEAR SCREEN OF CONFIRM RESPONSE
		gosub 700	:\ REM CREATE DED FILE
		goto 100	REM GO GET RESPONSE

rem
rem	create and initialise PYDED file
rem

 700
	trash% = fn.msg%("     CREATING DEDUCTION FILE")
REM
REM	DEFINE DEFAULT ACCOUNTS
REM
	def.cash% = 1
	def.liab% = 2
	def.expense% = pr1.default.dist.acct%
	def.cost% = 4

	create fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,null$,null$) \
		as ded.file%
	ded.fwt.used%= true%
	ded.fwt.acct.no% = def.liab%
	ded.fwt.allowance.amt = 1000.
	ded.fwt.mar.cutoff(01) = 2400.
	ded.fwt.mar.percent(01) = 15.
	ded.fwt.mar.cutoff(02) = 6600.
	ded.fwt.mar.percent(02) = 18.
	ded.fwt.mar.cutoff(03) = 10900.
	ded.fwt.mar.percent(03) = 21.
	ded.fwt.mar.cutoff(04) = 15000.
	ded.fwt.mar.percent(04) = 24.
	ded.fwt.mar.cutoff(05) = 19200.
	ded.fwt.mar.percent(05) = 28.
	ded.fwt.mar.cutoff(06) = 23600.
	ded.fwt.mar.percent(06) = 32.
	ded.fwt.mar.cutoff(07) = 28900.
	ded.fwt.mar.percent(07) = 37.
	ded.fwt.sin.cutoff(01) = 1420.
	ded.fwt.sin.percent(01) = 15.
	ded.fwt.sin.cutoff(02) = 3300.
	ded.fwt.sin.percent(02) = 18.
	ded.fwt.sin.cutoff(03) = 6800.
	ded.fwt.sin.percent(03) = 21.
	ded.fwt.sin.cutoff(04) = 10200.
	ded.fwt.sin.percent(04) = 26.
	ded.fwt.sin.cutoff(05) = 14200.
	ded.fwt.sin.percent(05) = 30.
	ded.fwt.sin.cutoff(06) = 17200.
	ded.fwt.sin.percent(06) = 34.
	ded.fwt.sin.cutoff(07) = 22500.
	ded.fwt.sin.percent(07) = 39.
	ded.swt.used% = true%
	ded.swt.acct.no% = def.liab%
	ded.lwt.used% = false%
	ded.lwt.acct.no% = def.liab%
	ded.fica.used% = true%
	ded.fica.acct.no% = def.liab%
	ded.fica.rate = 6.13
	ded.fica.limit = 25900.
	ded.co.fica.used% = true%
	ded.co.fica.acct.no% = def.cost%
	ded.co.fica.rate = 6.13
	ded.co.fica.limit = 25900.
	ded.sdi.used% = false%
	ded.sdi.acct.no% = def.liab%
	ded.sdi.rate = 1.
	ded.sdi.limit = 6000.
	ded.co.futa.used% = true%
	ded.co.futa.acct.no% = def.cost%
	ded.co.futa.rate = 3.4
	ded.co.futa.limit = 6000.
	ded.co.futa.max.credit = 2.7
	ded.co.sui.used% = true%
	ded.co.sui.acct.no% = def.cost%
	ded.co.sui.rate = 0
	ded.co.sui.limit = 6000.
	ded.eic.used% = false%
	ded.eic.acct.no% = def.liab%
	ded.eic.rate = 10.
	ded.eic.limit = 5000.
	ded.eic.excess.rate = 12.5
	ded.eic.excess.limit = 6000.
	ded.sys.used%(01) = false%
	ded.sys.acct.no%(01) = def.expense%
	ded.sys.chk.cat%(01) = 7
	ded.sys.desc$(01) = null$
	ded.sys.limit(01) = 0
	ded.sys.factor(01) = 0
	ded.sys.earn.ded$(01) = "E"
	ded.sys.amt.percent$(01) = "A"
	ded.sys.exclusion%(01) = 1
	ded.sys.limit.used%(01) = true%
	ded.sys.used%(02) = false%
	ded.sys.acct.no%(02) = def.expense%
	ded.sys.chk.cat%(02) = 7
	ded.sys.desc$(02) = null$
	ded.sys.limit(02) = 0
	ded.sys.factor(02) = 0
	ded.sys.earn.ded$(02) = "E"
	ded.sys.amt.percent$(02) = "A"
	ded.sys.exclusion%(02) = 1
	ded.sys.limit.used%(02) = true%
	ded.sys.used%(03) = false%
	ded.sys.acct.no%(03) = def.expense%
	ded.sys.chk.cat%(03) = 7
	ded.sys.desc$(03) = null$
	ded.sys.limit(03) = 0
	ded.sys.factor(03) = 0
	ded.sys.earn.ded$(03) = "E"
	ded.sys.amt.percent$(03) = "A"
	ded.sys.exclusion%(03) = 1
	ded.sys.limit.used%(03) = true%
	ded.sys.used%(04) = false%
	ded.sys.acct.no%(04) = def.expense%
	ded.sys.chk.cat%(04) = 7
	ded.sys.desc$(04) = null$
	ded.sys.limit(04) = 0
	ded.sys.factor(04) = 0
	ded.sys.earn.ded$(04) = "E"
	ded.sys.amt.percent$(04) = "A"
	ded.sys.exclusion%(04) = 1
	ded.sys.limit.used%(04) = true%
	ded.sys.used%(05) = false%
	ded.sys.acct.no%(05) = def.expense%
	ded.sys.chk.cat%(05) = 7
	ded.sys.desc$(05) = null$
	ded.sys.limit(05) = 0
	ded.sys.factor(05) = 0
	ded.sys.earn.ded$(05) = "E"
	ded.sys.amt.percent$(05) = "A"
	ded.sys.exclusion%(05) = 1
	ded.sys.limit.used%(05) = true%

rem
rem	write out default DED file
rem

	print #ded.file% ;	\
$include  "ipyded"
	close ded.file%
	trash% = fn.msg%("     DEDUCTION FILE CREATION COMPLETE")
	return


REM
REM	DECIDE WHERE TO CHAIN TO
REM

 997
	if match(startup$,common.chaining.status$,1) = 0 \
	   then \
		goto 999 \	REM NORMAL EXIT
	   else \
		chain fn.file.name.out$("PYSRTPRM",null$,0,null$,null$)


$include  "zeoj"
	end

