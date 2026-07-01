$include "ipycomm"
prgname$="DEDENT2      10-JAN-80"
$include "ipyconst"



rem----------------------------------------------------------------------
rem
rem		D E D U C T I O N
REM
REM		E N T R Y
REM
rem		FEDERAL WITHHOLDING TABLE ENTRY
REM		(DEDENT2)
REM
REM		(NOTE: THIS PROGRAM CREATED FROM DEDENTX)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "FEDERAL WITHHOLDING TABLE ENTRY"

rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------

$include "zdms"
$include "znumeric"
$include "zstring"
$include "zdateio"
$include "zfilconv"

$include "ipystat"
$include "ipydmded"

	dim emsg$(30)
	emsg$(1 ) = "     PY351 DEDENT MUST BE RUN FROM PY MENU"
	emsg$(2 ) = "     PY352 INVALID RESPONSE"
	emsg$(3 ) = "     PY353 PYDED - DEDUCTION FILE NOT PRESENT"
	emsg$(4 ) = "     PY354 IMPROPERLY FORMED NUMBER OR OUT OF RANGE"
	emsg$(5 ) = "     PY355 ANSWER MUST BE 'Y' OR 'N'"
	emsg$(6 ) = "     PY356 FWT CUTOFFS AND PERCENTS MUST BE IN ASCENDING ORDER"
	emsg$(7 ) = "     PY357 INVALID USE OF CONTROL CHARACTER"



program$ = "DEDENT2"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(1)	:\
			goto 999.2

rem
rem	read in DED file
rem

	if end #ded.file% then 500
	open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,null$,null$) \
		as ded.file%

rem
rem	file exists so read in and proceed
rem

	read #ded.file% ;	\
$include "ipyded"
	close ded.file%

rem
rem	get screen set up
rem

$include "fpyded2"
	trash% = fn.put.all%(false%)
	crt.io.field.count% = 29	REM COUNT OF INPUT FIELDS


rem
rem	display existing values
rem

	gosub 101
	gosub 102
	gosub 103
	gosub 104
	gosub 105
	gosub 106
	gosub 107
	gosub 108
	gosub 109
	gosub 110
	gosub 111
	gosub 112
	gosub 113
	gosub 114
	gosub 115
	gosub 116
	gosub 117
	gosub 118
	gosub 119
	gosub 120
	gosub 121
	gosub 122
	gosub 123
	gosub 124
	gosub 125
	gosub 126
	gosub 127
	gosub 128
	gosub 129



rem
rem	main input driver
rem

	field% = 1	rem start input driver at first field

 20	\
	trash% = fn.get%(3,field%)
	trash% = fn.msg%(null$) rem erase old error message
	ok% = true%	rem set flag that answer valid

	if in.status% = req.cancel% \
	   then goto 999	rem exit without updating file

	if in.status% = req.stopit% \
	   then \
		trash% = fn.msg%("     STOP REQUESTED") :\
		goto 900	rem do final consistancy check and exit

	if in.status% = req.cr% \
	   then goto 22 rem proceed to next field

	if in.status% = req.back% \
		then goto 24	rem proceed to previous field

	on field% gosub \ rem pick data checker by field
		201,	\
		202,	\
		203,	\
		204,	\
		205,	\
		206,	\
		207,	\
		208,	\
		209,	\
		210,	\
		211,	\
		212,	\
		213,	\
		214,	\
		215,	\
		216,	\
		217,	\
		218,	\
		219,	\
		220,	\
		221,	\
		222,	\
		223,	\
		224,	\
		225,	\
		226,	\
		227,	\
		228,	\
		229

	if not ok%	\
		then goto 20	rem if answer not okay re-enter same field

rem
rem	get set for next field
rem

 22	\
	field% = field% + 1
	if field% > crt.io.field.count% \
		then field% = 1
	goto 20 	rem main input driver

rem
rem	get set for previous field
rem

 24	\
	field% = field% - 1
	if field% < 1	\
		then field% = crt.io.field.count%
	goto 20 	rem main input driver

rem
rem	subroutines to display data fields
rem

 101
	trash% = fn.put%(str$(ded.fwt.allowance.amt),1)
	return

 102
	trash% = fn.put%(str$(ded.fwt.mar.cutoff(1)),2)
	return

 103
	trash% = fn.put%(str$(ded.fwt.mar.percent(1)),3)
	return

 104
	trash% = fn.put%(str$(ded.fwt.sin.cutoff(1)),4)
	return

 105
	trash% = fn.put%(str$(ded.fwt.sin.percent(1)),5)
	return

 106
	trash% = fn.put%(str$(ded.fwt.mar.cutoff(2)),6)
	return

 107
	trash% = fn.put%(str$(ded.fwt.mar.percent(2)),7)
	return

 108
	trash% = fn.put%(str$(ded.fwt.sin.cutoff(2)),8)
	return

 109
	trash% = fn.put%(str$(ded.fwt.sin.percent(2)),9)
	return

 110
	trash% = fn.put%(str$(ded.fwt.mar.cutoff(3)),10)
	return

 111
	trash% = fn.put%(str$(ded.fwt.mar.percent(3)),11)
	return

 112
	trash% = fn.put%(str$(ded.fwt.sin.cutoff(3)),12)
	return

 113
	trash% = fn.put%(str$(ded.fwt.sin.percent(3)),13)
	return

 114
	trash% = fn.put%(str$(ded.fwt.mar.cutoff(4)),14)
	return

 115
	trash% = fn.put%(str$(ded.fwt.mar.percent(4)),15)
	return

 116
	trash% = fn.put%(str$(ded.fwt.sin.cutoff(4)),16)
	return

 117
	trash% = fn.put%(str$(ded.fwt.sin.percent(4)),17)
	return

 118
	trash% = fn.put%(str$(ded.fwt.mar.cutoff(5)),18)
	return

 119
	trash% = fn.put%(str$(ded.fwt.mar.percent(5)),19)
	return

 120
	trash% = fn.put%(str$(ded.fwt.sin.cutoff(5)),20)
	return

 121
	trash% = fn.put%(str$(ded.fwt.sin.percent(5)),21)
	return

 122
	trash% = fn.put%(str$(ded.fwt.mar.cutoff(6)),22)
	return

 123
	trash% = fn.put%(str$(ded.fwt.mar.percent(6)),23)
	return

 124
	trash% = fn.put%(str$(ded.fwt.sin.cutoff(6)),24)
	return

 125
	trash% = fn.put%(str$(ded.fwt.sin.percent(6)),25)
	return

 126
	trash% = fn.put%(str$(ded.fwt.mar.cutoff(7)),26)
	return

 127
	trash% = fn.put%(str$(ded.fwt.mar.percent(7)),27)
	return

 128
	trash% = fn.put%(str$(ded.fwt.sin.cutoff(7)),28)
	return

 129
	trash% = fn.put%(str$(ded.fwt.sin.percent(7)),29)
	return



rem
rem	subroutines to check validity of data fields
rem

rem	allowance.amt

 201
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.allowance.amt = val(in$)
	gosub 101	rem redisplay field
	return

rem	mar.cutoff(1)

 202
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.mar.cutoff(1) = val(in$)
	gosub 102	rem redisplay field
	return

rem	mar.percent(1)

 203
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.mar.percent(1) = val(in$)
	gosub 103	rem redisplay field
	return

rem	sin.cutoff(1)

 204
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.sin.cutoff(1) = val(in$)
	gosub 104	rem redisplay field
	return

rem	sin.percent(1)

 205
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.sin.percent(1) = val(in$)
	gosub 105	rem redisplay field
	return

rem	mar.cutoff(2)

 206
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.mar.cutoff(2) = val(in$)
	gosub 106	rem redisplay field
	return

rem	mar.percent(2)

 207
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.mar.percent(2) = val(in$)
	gosub 107	rem redisplay field
	return

rem	sin.cutoff(2)

 208
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.sin.cutoff(2) = val(in$)
	gosub 108	rem redisplay field
	return

rem	sin.percent(2)

 209
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.sin.percent(2) = val(in$)
	gosub 109	rem redisplay field
	return

rem	mar.cutoff(3)

 210
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.mar.cutoff(3) = val(in$)
	gosub 110	rem redisplay field
	return

rem	mar.percent(3)

 211
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.mar.percent(3) = val(in$)
	gosub 111	rem redisplay field
	return

rem	sin.cutoff(3)

 212
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.sin.cutoff(3) = val(in$)
	gosub 112	rem redisplay field
	return

rem	sin.percent(3)

 213
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.sin.percent(3) = val(in$)
	gosub 113	rem redisplay field
	return

rem	mar.cutoff(4)

 214
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.mar.cutoff(4) = val(in$)
	gosub 114	rem redisplay field
	return

rem	mar.percent(4)

 215
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.mar.percent(4) = val(in$)
	gosub 115	rem redisplay field
	return

rem	sin.cutoff(4)

 216
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.sin.cutoff(4) = val(in$)
	gosub 116	rem redisplay field
	return

rem	sin.percent(4)

 217
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.sin.percent(4) = val(in$)
	gosub 117	rem redisplay field
	return

rem	mar.cutoff(5)

 218
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.mar.cutoff(5) = val(in$)
	gosub 118	rem redisplay field
	return

rem	mar.percent(5)

 219
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.mar.percent(5) = val(in$)
	gosub 119	rem redisplay field
	return

rem	sin.cutoff(5)

 220
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.sin.cutoff(5) = val(in$)
	gosub 120	rem redisplay field
	return

rem	sin.peercent(5)

 221
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.sin.percent(5) = val(in$)
	gosub 121	rem rredisplay field
	return

rem	mar.cutoff(6)

 222

	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.mar.cutoff(6) = val(in$)
	gosub 122	rem redisplay field
	return

rem	mar.percent(6)

 223
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.mar.percent(6) = val(in$)
	gosub 123	rem redisplay field
	return

rem	sin.cutoff(6)

 224
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.sin.cutoff(6) = val(in$)
	gosub 102	rem redisplay field
	return

rem	sin.percent(6)

 225
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.sin.percent(6) = val(in$)
	gosub 125	rem redisplay field
	return

rem	mar.cutoff(7)


 226
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.mar.cutoff(7) = val(in$)
	gosub 126	rem redisplay field
	return

rem	mar.percent(7)

 227
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.mar.percent(7) = val(in$)
	gosub 127	rem redisplay field
	return

rem	sin.cutoff(7)

 228
	gosub 300	rem valid amount?
	if ok%	\
		then ded.fwt.sin.cutoff(7) = val(in$)
	gosub 128	rem redisplay field
	return

rem	sin.percent(7)

 229
	gosub 310	rem valid rate(percent)?
	if ok%	\
		then ded.fwt.sin.percent(7) = val(in$)
	gosub 129	rem redisplay field
	return



rem
rem	subroutine to check in$ is dollar value (i.e. xxxxx.xx)
rem

 300	\
	ok% = fn.numeric%(in$,5,2)
	if not ok%	\
		then trash% = fn.emsg%(4)
	return

rem
rem	subroutine to check in$ is percent value (i.e. xx.xx)
rem

 310	\
	ok% = fn.numeric%(in$,2,2)
	if not ok%	\
		then trash% = fn.emsg%(4)
	return


rem
rem	ded file does not exist, so exit with error message
rem

 500	\
	trash% = fn.emsg%(3)	REM DED FILE DOES NOT EXIST
	goto 999.1		rem abnormal exit


rem
rem	do final consistancy checks of data and write out if okay
rem
 900	\

rem
rem	fwt cutoff amounts and percents must be in increasing order
rem

	for i% = 2 to 7
		if ded.fwt.mar.cutoff(i%) <= ded.fwt.mar.cutoff(i%-1)	\
		   then \
			trash% = fn.emsg%(6) :\
			field% = i% * 4 - 2	:\ rem set field to erroneous
			goto 20 	rem return to main input driver

		if ded.fwt.mar.percent(i%) <= ded.fwt.mar.percent(i%-1) \
		   then \
			trash% = fn.emsg%(6) :\
			field% = i% * 4 - 1	:\ rem set field to erroneous
			goto 20 	rem return to main input driver

		if ded.fwt.sin.cutoff(i%) <= ded.fwt.sin.cutoff(i%-1)	\
		   then \
			trash% = fn.emsg%(6) :\
			field% = i% * 4 	:\ rem set field to erroneous
			goto 20 	rem return to main input driver

		if ded.fwt.sin.percent(i%) <= ded.fwt.sin.percent(i%-1) \
		   then \
			trash% = fn.emsg%(6) :\
			field% = i% * 4 + 1	:\ rem set field to erroneous
			goto 20 	rem return to main input driver

	next i%

	gosub	998	rem write out DED file
	goto 999	rem normal exit


rem
rem	write out DED file subroutine
rem

 998	\
	open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,null$,null$) \
		as ded.file%
	print #ded.file% ;	\
$include "ipyded"
	close ded.file%
	return


rem	Nov. 18, 1979
999    rem-----normal end of job---------------
trash%=fn.msg%(function.name$+" COMPLETED")
common.return.code%=0
chain fn.file.name.out$("DEDENT",null$,0,null$,null$)
999.1  rem-----abnormal end of job-------------
trash%=fn.msg%(bell$+function.name$+" COMPLETED UNSUCCESSFULLY")
common.return.code%=1
goto 999.3
999.2  rem-----premature end of job------------
trash%=fn.msg%(function.name$+" TERMINATING AT OPERATOR'S REQUEST")
common.return.code%=2
999.3  rem-----return to menu or stop----------
if chained.from.root% \
	then	chain fn.file.name.out$(system$,null$,0,null$,null$) \
	else	stop

	end

