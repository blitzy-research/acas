#include "ipycomm"
prgname$="PYUPDMEN   10-JAN-80"
#include "ipyconst"

rem----------------------------------------------------------------------
rem
REM
REM		COMPANY UPDATE MENU
REM
REM		(PYUPDMEN)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "COMPANY HISTORY UPDATE MENU"

rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------

#include "zdms"
#include "zdmsconf"
#include "znumber"
#include "zstring"
#include "zdateio"
#include "zfilconv"

#include "ipystat"
#include "ipydmded"

	dim emsg$(30)
	emsg$(1 ) = "     PY922 PROGRAM NOT RUN FROM MENU"
	emsg$(2 ) = "     PY921 INVALID RESPONSE"



program$ = "PYUPDMEN"
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

#include "fpyupdm"
	trash% = fn.put.all%(false%)

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
	goto 999	REM NORMAL EXIT

rem
rem	check data's validity
rem

 107
	if in$ = "1"    \
	   then \	REM UPDATE EMP HISTORY TOTALS
		chain fn.file.name.out$("pyupdth",null$,0,null$,null$)


	if in$ = "2"    \
	   then \	REM UPDATE LIABILITIES AND COMP TIME ETC
		chain fn.file.name.out$("pyupdli",null$,0,null$,null$)


	if in$ = "3"    \
	   then \	REM UPDATE PAYMENT RECORDS
		chain fn.file.name.out$("pyupdpm",null$,0,null$,null$)

	trash% = fn.emsg%(2)	REM INVALID RESPONSE
	goto 105	rem invalid response to request again


#include "zeoj"
	end

