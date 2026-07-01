$include "ipycomm"
prgname$ = "DEDENT1          10-JAN-80"
$include "ipyconst"


rem----------------------------------------------------------------------
rem
rem		D E D U C T I O N
REM
REM		E N T R Y
REM
REM		(DEDENT1)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "STANDARD DEDUCTION RATES"

rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------

$include "zdms"
$include "znumeric"
$include "zstring"
$include "zdateio"
$include "zdspyorn"
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
	emsg$(8 ) = "     PY358 ANSWER MUST BE 'E' OR 'D'"
	emsg$(9 ) = "     PY359 ANSWER MUST BE 'A' OR 'P'"
	emsg$(10) = "     PY360 CHK CAT MUST BE 2-7 FOR EARNINGS, 9-16 FOR DEDUCTIONS"



program$ = "DEDENT1"
if pr2.no.acts% = 0 then pr2.no.acts% = 2

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then trash% = fn.emsg%(1) :\
			goto 999.2

rem
rem	get screen set up
rem

$include "fpyded1"

	trash% = fn.put.all%(false%)
	crt.io.field.count% = 33

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
	gosub 130
	gosub 131
	gosub 132
	gosub 133



rem
rem	main input driver
rem

	field% = 1	rem start input driver at first field

 20	\
	trash% = fn.get%(3,field%)
	ok% = true%	rem set flag that response is valid

	if in.status% = req.cancel% \
	   then goto 999	rem exit without updating file

	if in.status% = req.stopit% \
	   then \
		 trash% = fn.msg%("STOP REQUESTED") :\
		      goto 900	rem do final consistancy check and exit

	if in.status% = req.cr% \
	   then goto 22 rem proceed to next field

	if in.status% = req.back% \
	   then goto 24 rem proceed to previous field


	on field% gosub 	\ rem pick data checker by field
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
		229,	\
		230,	\
		231,	\
		232,	\
		233

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
	trash% = fn.put%(fn.dsp.yorn$(ded.fwt.used%),1)
	return

 102
	trash% = fn.put%(str$(ded.fwt.acct.no%),2)
	return

 103
	trash% = fn.put%(fn.dsp.yorn$(ded.swt.used%),3)
	return

 104

	trash% = fn.put%(str$(ded.swt.acct.no%),4)
	return

 105
	trash% = fn.put%(fn.dsp.yorn$(ded.lwt.used%),5)
	return

 106
	trash% = fn.put%(str$(ded.lwt.acct.no%),6)
	return

 107
	trash% = fn.put%(fn.dsp.yorn$(ded.fica.used%),7)
	return

 108
	trash% = fn.put%(str$(ded.fica.acct.no%),8)
	return

 109
	trash% = fn.put%(str$(ded.fica.rate),9)
	return

 110
	trash% = fn.put%(str$(ded.fica.limit),10)
	return

 111
	trash% = fn.put%(fn.dsp.yorn$(ded.co.fica.used%),11)
	return

 112
	trash% = fn.put%(str$(ded.co.fica.acct.no%),12)
	return

 113
	trash% = fn.put%(str$(ded.co.fica.rate),13)
	return

 114
	trash% = fn.put%(str$(ded.co.fica.limit),14)
	return

 115
	trash% = fn.put%(fn.dsp.yorn$(ded.sdi.used%),15)
	return

 116
	trash% = fn.put%(str$(ded.sdi.acct.no%),16)
	return

 117
	trash% = fn.put%(str$(ded.sdi.rate),17)
	return

 118
	trash% = fn.put%(str$(ded.sdi.limit),18)
	return

 119
	trash% = fn.put%(fn.dsp.yorn$(ded.co.futa.used%),19)
	return

 120
	trash% = fn.put%(str$(ded.co.futa.acct.no%),20)
	return

 121
	trash% = fn.put%(str$(ded.co.futa.rate),21)
	return

 122
	trash% = fn.put%(str$(ded.co.futa.limit),22)
	return

 123
	trash% = fn.put%(str$(ded.co.futa.max.credit),23)
	return

 124
	trash% = fn.put%(fn.dsp.yorn$(ded.co.sui.used%),24)
	return

 125
	trash% = fn.put%(str$(ded.co.sui.acct.no%),25)
	return

 126
	trash% = fn.put%(str$(ded.co.sui.rate),26)
	return

 127
	trash% = fn.put%(str$(ded.co.sui.limit),27)
	return

 128
	trash% = fn.put%(fn.dsp.yorn$(ded.eic.used%),28)
	return

 129
	trash% = fn.put%(str$(ded.eic.acct.no%),29)
	return

 130
	trash% = fn.put%(str$(ded.eic.rate),30)
	return

 131
	trash% = fn.put%(str$(ded.eic.limit),31)
	return

 132
	trash% = fn.put%(str$(ded.eic.excess.rate),32)
	return

 133
	trash% = fn.put%(str$(ded.eic.excess.limit),33)
	return


rem
rem	subroutines to check validity of data fields
rem

rem	ded.fwt.used%

 201
	gosub 320	rem check y or n
	if ok% then ded.fwt.used% = bool.val%
	gosub 101	rem display
	return

rem	ded.fwt.acct.no%

 202
	gosub 330	rem check acct no
	if ok% then ded.fwt.acct.no% = val(in$)
	gosub 102	rem display
	return

rem	ded.swt.used%

 203
	gosub 320	rem check y or n
	if ok% then ded.swt.used%  = bool.val%
	gosub 103	rem display
	return

rem	ded.swt.acct.no%

 204
	gosub 330	rem check acct no
	if ok% then ded.swt.acct.no% = val(in$)
	gosub 104	rem display
	return

rem	ded.lwt.used%

 205
	gosub 320	rem check y or n
	if ok% then ded.lwt.used% = bool.val%
	gosub 105	REM Display
	return

rem	ded.lwt.acct.no%

 206
	gosub 330	rem check acct no
	if ok% then ded.lwt.acct.no% = val(in$)
	gosub 106	REM display
	return

rem	ded.fica.used%

 207
	gosub 320	rem check y or n
	if ok% then ded.fica.used% = bool.val%
	gosub 107	rem display
	return

rem	ded.fica.acct.no%

 208
	gosub 330	rem check acct no
	if ok% then ded.fica.acct.no% = val(in$)
	gosub 108	rem display
	return

rem	ded.fica.rate

 209
	gosub 310	rem check rate
	if ok% then ded.fica.rate = val(in$)
	gosub 109	rem display
	return

rem	ded.fica.limit

 210
	gosub 300	rem check limit
	if ok% then ded.fica.limit  = val(in$)
	gosub 110	rem display
	return

rem	ded.co.fica.used%

 211
	gosub 320	rem check y or n
	if ok% then ded.co.fica.used% = bool.val%
	gosub 111	rem display
	return

rem	ded.co.fica.acct.no%

 212
	gosub 330	rem check acct no
	if ok% then ded.co.fica.acct.no% = val(in$)
	gosub 112	rem display
	return

rem	ded.co.fica.rate

 213
	gosub 310	rem check rate
	if ok% then ded.co.fica.rate = val(in$)
	gosub 113	rem display
	return

rem	ded.co.fica.limit

 214
	gosub 300	rem check limit
	if ok% then ded.co.fica.limit = val(in$)
	gosub 114
	return

rem	ded.sdi.used%

 215
	gosub 320	rem check y or n
	if ok% then ded.sdi.used% = bool.val%
	gosub 115	rem display
	return

rem	ded.sdi.acct.no%

 216
	gosub 330	rem check acct no
	if ok% then ded.sdi.acct.no% = val(in$)
	gosub 116	rem display
	return

rem	ded.sdi.rate

 217
	gosub 310	rem check rate
	if ok% then ded.sdi.rate = val(in$)
	gosub 117	rem display
	return

rem	ded.sdi.limit

 218
	gosub 300	rem chaeck limit
	if ok% then ded.sdi.limit = val(in$)
	gosub 118
	return

rem	ded.co.futa.used%

 219
	gosub 320	rem check y or n
	if ok% then ded.co.futa.used% = bool.val%
	gosub 119	rem display
	return

rem	ded.co.futa.acct.no%

 220
	gosub 330	rem check acct no
	if ok% then ded.co.futa.acct.no% = val(in$)
	gosub 120
	return

rem	ded.co.futa.rate

 221
	gosub 310	rem check rate
	if ok% then ded.co.futa.rate = val(in$)
	gosub 121	rem display
	return

rem	ded.co.futa.limit

 222
	gosub 300	rem check limit
	if ok% then ded.co.futa.limit = val(in$)
	gosub 122	rem display
	return

rem	ded.co.futa.max.credit

 223
	gosub 310	rem check rate
	if ok% then ded.co.futa.max.credit = val(in$)
	gosub 123	rem display
	return

rem	ded.co.sui.used%

 224
	gosub 320	rem check y or n
	if ok% then ded.co.sui.used% = bool.val%
	gosub 124	rem display
	return

rem	ded.co.sui.acct.no%

 225
	gosub 330	rem check acct no
	if ok% then ded.co.sui.acct.no% = val(in$)
	gosub 125	rem display
	return

rem	ded.co.sui.rate

 226
	gosub 310	rem check rate
	if ok% then ded.co.sui.rate = val(in$)
	gosub 126	rem display
	return

rem	ded.co.sui.limit

 227
	gosub 300	rem check limit
	if ok% then ded.co.sui.limit = val(in$)
	gosub 127	rem display
	return

rem	ded.eic.used%

 228
	gosub 320	rem check y or n
	if ok% then ded.eic.used% = bool.val%
	gosub 128	rem display
	return

rem	ded.eic.acct.no%

 229
	gosub 330	rem check acct no
	if ok% then ded.eic.acct.no% = val(in$)
	gosub 129	rem display
	return

rem	ded.eic.rate

 230
	gosub 310	rem check rate
	if ok% then ded.eic.rate = val(in$)
	gosub 130	rem display
	return

rem	ded.eic.limit

 231
	gosub 300	rem check limit
	if ok% then ded.eic.limit = val(in$)
	gosub 131	rem display
	return

rem	ded.eic.excess.rate

 232
	gosub 310	rem check rate
	if ok% then ded.eic.excess.rate = val(in$)
	gosub 132	rem display
	return

rem	ded.eic.excess.limit

 233
	gosub 300	rem check limit
	if ok% then ded.eic.excess.limit = val(in$)
	gosub 133	rem display
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
rem	subroutine to check in$ is percent value (i.e. xx.xxxxx)
rem

 310	\
	ok% = fn.numeric%(in$,2,2)
	if not ok%	\
	   then trash% = fn.emsg%(4)
	return

rem
rem	subroutine to check that in$ is "y" or "n" and set
rem	bool.val% true for y and false for n
rem

 320	\
	ok% = false%
	if ucase$(in$) = "Y"    \
		then	\
			ok% = true%	:\
			bool.val% = true%
	if ucase$(in$) = "N"    \
		then	\
			ok% = true%	:\
			bool.val% = false%
	if not ok%	\
	   then trash% = fn.emsg%(5)
	return

rem
rem	subroutine to check validity of account number
rem

 330	\
	ok% = fn.num%(in$)
	if not ok%	\
		then goto 330.9 rem print error message
	if val(in$) <> 0 and val(in$) <= pr2.no.acts%	\
	   then return	rem number ok

 330.9	trash% = fn.emsg%(4)
	ok% = false%
	return


rem
rem	ded file does not exist, so exit with error message
rem

 500	\
	trash% = fn.emsg%(3)
	goto 999.1		rem abnormal exit



rem
rem	do final consistancy checks of data and write out if okay
rem
 900	\
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
chain fn.file.name.out$("dedent",null$,0,null$,null$)
999.1  rem-----abnormal end of job-------------
trash%=fn.msg%(bell$+function.name$+" COMPLETED UNSUCCESSFULLY")
common.return.code%=1
goto 999.3
999.2  rem-----premature end of job------------
trash%=fn.msg%(function.name$+" TERMINATING AT OPERATOR'S REQUEST")
common.return.code%=2
999.3  rem-----return to menu or stop----------
if chained.from.root% \
  then	  chain fn.file.name.out$(system$,null$,0,null$,null$) \
  else	  stop

	end
