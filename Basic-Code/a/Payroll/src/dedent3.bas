$include "ipycomm"
prgname$="DEDENT3      10-JAN-80"
$include "ipyconst"



rem----------------------------------------------------------------------
rem
rem		D E D U C T I O N
REM
REM		E N T R Y
REM
REM		(DEDENT3)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$="SYSTEM EARNING AND DEDUCTION ENTRY"

rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------

$include "zdms"
$include "zdmstest"
$include "zdmsused"
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



program$ = "DEDENT3"
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

$include "fpyded3"

	crt.io.field.count% = 50
	trash% = fn.put.all%(false%)


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
	gosub 109
	gosub 107
	gosub 108
	gosub 106
	gosub 110
	gosub 105
	gosub 111
	gosub 112
	gosub 113
	gosub 114
	gosub 119
	gosub 117
	gosub 118
	gosub 116
	gosub 120
	gosub 115
	gosub 121
	gosub 122
	gosub 123
	gosub 124
	gosub 129
	gosub 127
	gosub 128
	gosub 126
	gosub 130
	gosub 125
	gosub 131
	gosub 132
	gosub 133
	gosub 134
	gosub 139
	gosub 137
	gosub 138
	gosub 136
	gosub 140
	gosub 135
	gosub 141
	gosub 142
	gosub 143
	gosub 144
	gosub 149
	gosub 147
	gosub 148
	gosub 146
	gosub 150
	gosub 145


rem
rem	main input driver
rem

	field% = 1	rem start input driver at first field

 20	\
	trash% = fn.get%(3,field%)
	ok% = true%	rem set flag that response is valid

	if pr1.debugging% \
	   then \
		trash% = fn.msg%("fre="+str$(fre))

	if in.status% = req.cancel% \
	   then goto 999	rem exit without updating file

	if in.status% = req.stopit% \
	   then \
		  trash% = fn.msg%("     STOP REQUESTED") :\
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
		209,	\
		207,	\
		208,	\
		206,	\
		210,	\
		205,	\
		211,	\
		212,	\
		213,	\
		214,	\
		219,	\
		217,	\
		218,	\
		216,	\
		220,	\
		215,	\
		221,	\
		222,	\
		223,	\
		224,	\
		229,	\
		227,	\
		228,	\
		226,	\
		230,	\
		225,	\
		231,	\
		232,	\
		233,	\
		234,	\
		239,	\
		237,	\
		238,	\
		236,	\
		240,	\
		235,	\
		241,	\
		242,	\
		243,	\
		244,	\
		249,	\
		247,	\
		248,	\
		246,	\
		250,	\
		245

	if not ok%	\
		then goto 20	rem if answer not okay re-enter same field


rem
rem	get set for next field
rem

 22	\
REM
REM	SKIP FIELDS IF DED NOT USED
REM
	cur.ded% = 0
	if field% - (field%/10)*10 = 1 \
	   then cur.ded% = (field%/10) + 1
	if cur.ded% = 0 then goto 22.1	REM TO CREATE NESTED IF
	if not ded.sys.used%(cur.ded%) \
	   then field% = field% + 9

 22.1	field% = field% + 1
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
REM
REM	SKIP FIELDS IF DED NOT USED
REM
	cur.ded% = 0
	if field% - (field%/10)*10 = 0 \
	   then cur.ded% = (field%/10)
	if cur.ded% = 0 then goto 24.1	REM TO CREATE NESTED IF
	if not ded.sys.used%(cur.ded%) \
	   then field% = field% - 9

 24.1	goto 20 	rem main input driver

rem
rem	subroutines to display data fields
rem

 101	trash%=fn.put%(fn.dsp.yorn$(ded.sys.used%(1)),1)
	return

 102	trash%=fn.put%(ded.sys.desc$(1),2)
	return

 103	trash%=fn.put%(ded.sys.earn.ded$(1),3)
	return

 104	trash%=fn.put%(str$(ded.sys.acct.no%(1)),4)
	return

 105	trash%=fn.put%(str$(ded.sys.chk.cat%(1)),10)
	return

 106	trash%=fn.put%(str$(ded.sys.limit(1)),8)
	return

 107	trash%=fn.put%(str$(ded.sys.factor(1)),6)
	return

 108	trash%=fn.put%(fn.dsp.yorn$(ded.sys.limit.used%(1)),7)
	return

 109	trash%=fn.put%(ded.sys.amt.percent$(1),5)
	return

 110	trash%=fn.put%(str$(ded.sys.exclusion%(1)),9)
	return

 111	trash%=fn.put%(fn.dsp.yorn$(ded.sys.used%(2)),11)
	return

 112	trash%=fn.put%(ded.sys.desc$(2),12)
	return

 113	trash%=fn.put%(ded.sys.earn.ded$(2),13)
	return

 114	trash%=fn.put%(str$(ded.sys.acct.no%(2)),14)
	return

 115	trash%=fn.put%(str$(ded.sys.chk.cat%(2)),20)
	return

 116	trash%=fn.put%(str$(ded.sys.limit(2)),18)
	return

 117	trash%=fn.put%(str$(ded.sys.factor(2)),16)
	return

 118	trash%=fn.put%(fn.dsp.yorn$(ded.sys.limit.used%(2)),17)
	return

 119	trash%=fn.put%(ded.sys.amt.percent$(2),15)
	return

 120	trash%=fn.put%(str$(ded.sys.exclusion%(2)),19)
	return

 121	trash%=fn.put%(fn.dsp.yorn$(ded.sys.used%(3)),21)
	return

 122	trash%=fn.put%(ded.sys.desc$(3),22)
	return

 123	trash%=fn.put%(ded.sys.earn.ded$(3),23)
	return

 124	trash%=fn.put%(str$(ded.sys.acct.no%(3)),24)
	return

 125	trash%=fn.put%(str$(ded.sys.chk.cat%(3)),30)
	return

 126	trash%=fn.put%(str$(ded.sys.limit(3)),28)
	return

 127	trash%=fn.put%(str$(ded.sys.factor(3)),26)
	return

 128	trash%=fn.put%(fn.dsp.yorn$(ded.sys.limit.used%(3)),27)
	return

 129	trash%=fn.put%(ded.sys.amt.percent$(3),25)
	return

 130	trash%=fn.put%(str$(ded.sys.exclusion%(3)),29)
	return

 131	trash%=fn.put%(fn.dsp.yorn$(ded.sys.used%(4)),31)
	return

 132	trash%=fn.put%(ded.sys.desc$(4),32)
	return

 133	trash%=fn.put%(ded.sys.earn.ded$(4),33)
	return

 134	trash%=fn.put%(str$(ded.sys.acct.no%(4)),34)
	return

 135	trash%=fn.put%(str$(ded.sys.chk.cat%(4)),40)
	return

 136	trash%=fn.put%(str$(ded.sys.limit(4)),38)
	return

 137	trash%=fn.put%(str$(ded.sys.factor(4)),36)
	return

 138	trash%=fn.put%(fn.dsp.yorn$(ded.sys.limit.used%(4)),37)
	return

 139	trash%=fn.put%(ded.sys.amt.percent$(4),35)
	return

 140	trash%=fn.put%(str$(ded.sys.exclusion%(4)),39)
	return

 141	trash%=fn.put%(fn.dsp.yorn$(ded.sys.used%(5)),41)
	return

 142	trash%=fn.put%(ded.sys.desc$(5),42)
	return

 143	trash%=fn.put%(ded.sys.earn.ded$(5),43)
	return

 144	trash%=fn.put%(str$(ded.sys.acct.no%(5)),44)
	return

 145	trash%=fn.put%(str$(ded.sys.chk.cat%(5)),50)
	return

 146	trash%=fn.put%(str$(ded.sys.limit(5)),48)
	return

 147	trash%=fn.put%(str$(ded.sys.factor(5)),46)
	return

 148	trash%=fn.put%(fn.dsp.yorn$(ded.sys.limit.used%(5)),47)
	return

 149	trash%=fn.put%(ded.sys.amt.percent$(5),45)
	return

 150	trash%=fn.put%(str$(ded.sys.exclusion%(5)),49)
	return



rem
rem	subroutines to check validity of data fields
rem

rem	ded.sys.used%(1)

 201
	gosub	320	rem check y or n
	if ok% then ded.sys.used%(1) = bool.val%
	gosub 101	rem display
	return

rem	ded.sys.desc$(1)

 202
	ded.sys.desc$(1) = in$	rem no checking done of description
	gosub	102	rem display
	return

rem	ded.sys.earn.ded$(1)

 203
	gosub	340	rem check that "e" or "d"
	if ok% then ded.sys.earn.ded$(1) = in$

	REM SET DEFAULT ACCOUNTS AND CHECK CATAGORIES
	if ok% and in$ = "E" \
	   then ded.sys.acct.no%(1) = pr1.default.dist.acct% :\
		ded.sys.chk.cat%(1) = 7 REM DEFAULT EARNING CHECK CATAGORY
	if ok% and in$ = "D" \
	   then ded.sys.acct.no%(1) = 2 :\REM DEFAULT ACCRUED LIABILITY ACCOUNT
		ded.sys.chk.cat%(1) = 16 REM DEFAULT DEDUCTION CHECK CATAGORY
	REM DISPLAY NEW ACCOUNT NUMBER AND CHECK CATAGORY
	if ok% \
	   then \
		gosub 104 :\	REM DISPLAY ACCOUNT
		gosub 105	REM DISPLAY CHECK CATAGORY

	gosub	103	rem display
	return

rem	ded.sys.acct.no%(1)

 204
	gosub	330	rem check acct no
	if ok% then ded.sys.acct.no%(1) = val(in$)
	gosub	104	rem display
	return

rem	ded.sys.chk.cat%(1)

 205
	earn.ded.index% = 1	rem index of earning.deduction string for
				rem validating check catagory
	gosub	350	rem check check catagory
	if ok% then ded.sys.chk.cat%(1) = val(in$)
	gosub	105	rem display
	return

rem	ded.sys.limit(1)

 206
	gosub	310	rem check limit
	if ok% then ded.sys.limit(1) = val(in$)
	gosub	106	rem display
	return

rem	ded.sys.factor(1)

 207
	gosub	300	rem check factor
	if ok% then ded.sys.factor(1) = val(in$)
	gosub	107	rem display
	return

rem	ded.sys.limit.used%(1)

 208
	gosub	320	rem check y or n
	if ok% then ded.sys.limit.used%(1) = bool.val%
	gosub	108	rem display
	return

rem	ded.sys.amt.percent$(1)

 209
	gosub	360	rem check that a or p
	if ok% then ded.sys.amt.percent$(1) = in$
	gosub	109	rem display
	return

rem	ded.sys.exclusion%(1)

 210
	gosub	370	rem check that valid exclusion code
	if ok% then ded.sys.exclusion%(1) = val(in$)
	gosub	110	rem display
	return


rem	ded.sys.used%(2)

 211
	gosub	320	rem check y or n
	if ok% then ded.sys.used%(2) = bool.val%
	gosub 111	rem display
	return

rem	ded.sys.desc$(2)

 212
	ded.sys.desc$(2) = in$	rem no checking done of description
	gosub	112	rem display
	return

rem	ded.sys.earn.ded$(2)

 213
	gosub	340	rem check that "e" or "d"
	if ok% then ded.sys.earn.ded$(2) = in$

	REM SET DEFAULT ACCOUNTS AND CHECK CATAGORIES
	if ok% and in$ = "E" \
	   then ded.sys.acct.no%(2) = pr1.default.dist.acct% :\
		ded.sys.chk.cat%(2) = 7 REM DEFAULT EARNING CHECK CATAGORY
	if ok% and in$ = "D" \
	   then ded.sys.acct.no%(2) = 2 :\REM DEFAULT ACCRUED LIABILITY ACCOUNT
		ded.sys.chk.cat%(2) = 16 REM DEFAULT DEDUCTION CHECK CATAGORY
	REM DISPLAY NEW ACCOUNT NUMBER AND CHECK CATAGORY
	if ok% \
	   then \
		gosub 114 :\	REM DISPLAY ACCOUNT
		gosub 115	REM DISPLAY CHECK CATAGORY

	gosub	113	rem display
	return

rem	ded.sys.acct.no%(2)

 214
	gosub	330	rem check acct no
	if ok% then ded.sys.acct.no%(2) = val(in$)
	gosub	114	rem display
	return

rem	ded.sys.chk.cat%(2)

 215
	earn.ded.index% = 2	rem index of earning.deduction string for
				rem validating check catagory
	gosub	350	rem check check catagory
	if ok% then ded.sys.chk.cat%(2) = val(in$)
	gosub	115	rem display
	return

rem	ded.sys.limit(2)

 216
	gosub	310	rem check limit
	if ok% then ded.sys.limit(2) = val(in$)
	gosub	116	rem display
	return

rem	ded.sys.factor(2)

 217
	gosub	300	rem check factor
	if ok% then ded.sys.factor(2) = val(in$)
	gosub	117	rem display
	return

rem	ded.sys.limit.used%(2)

 218
	gosub	320	rem check y or n
	if ok% then ded.sys.limit.used%(2) = bool.val%
	gosub	118	rem display
	return

rem	ded.sys.amt.percent$(2)

 219
	gosub	360	rem check that a or p
	if ok% then ded.sys.amt.percent$(2) = in$
	gosub	119	rem display
	return

rem	ded.sys.exclusion%(2)

 220
	gosub	370	rem check that valid exclusion code
	if ok% then ded.sys.exclusion%(2) = val(in$)
	gosub	120	rem display
	return


rem	ded.sys.used%(3)

 221
	gosub	320	rem check y or n
	if ok% then ded.sys.used%(3) = bool.val%
	gosub 121	rem display
	return

rem	ded.sys.desc$(3)

 222
	ded.sys.desc$(3) = in$	rem no checking done of description
	gosub	122	rem display
	return

rem	ded.sys.earn.ded$(3)

 223
	gosub	340	rem check that "e" or "d"
	if ok% then ded.sys.earn.ded$(3) = in$

	REM SET DEFAULT ACCOUNTS AND CHECK CATAGORIES
	if ok% and in$ = "E" \
	   then ded.sys.acct.no%(3) = pr1.default.dist.acct% :\
		ded.sys.chk.cat%(3) = 7 REM DEFAULT EARNING CHECK CATAGORY
	if ok% and in$ = "D" \
	   then ded.sys.acct.no%(3) = 2 :\REM DEFAULT ACCRUED LIABILITY ACCOUNT
		ded.sys.chk.cat%(3) = 16 REM DEFAULT DEDUCTION CHECK CATAGORY
	REM DISPLAY NEW ACCOUNT NUMBER AND CHECK CATAGORY
	if ok% \
	   then \
		gosub 124 :\	REM DISPLAY ACCOUNT
		gosub 125	REM DISPLAY CHECK CATAGORY

	gosub	123	rem display
	return

rem	ded.sys.acct.no%(3)

 224
	gosub	330	rem check acct no
	if ok% then ded.sys.acct.no%(3) = val(in$)
	gosub	124	rem display
	return

rem	ded.sys.chk.cat%(3)

 225
	earn.ded.index% = 3	rem index of earning.deduction string for
				rem validating check catagory
	gosub	350	rem check check catagory
	if ok% then ded.sys.chk.cat%(3) = val(in$)
	gosub	125	rem display
	return

rem	ded.sys.limit(3)

 226
	gosub	310	rem check limit
	if ok% then ded.sys.limit(3) = val(in$)
	gosub	126	rem display
	return

rem	ded.sys.factor(3)

 227
	gosub	300	rem check factor
	if ok% then ded.sys.factor(3) = val(in$)
	gosub	127	rem display
	return

rem	ded.sys.limit.used%(3)

 228
	gosub	320	rem check y or n
	if ok% then ded.sys.limit.used%(3) = bool.val%
	gosub	128	rem display
	return

rem	ded.sys.amt.percent$(3)

 229
	gosub	360	rem check that a or p
	if ok% then ded.sys.amt.percent$(3) = in$
	gosub	129	rem display
	return

rem	ded.sys.exclusion%(3)

 230
	gosub	370	rem check that valid exclusion code
	if ok% then ded.sys.exclusion%(3) = val(in$)
	gosub	130	rem display
	return


rem	ded.sys.used%(4)

 231
	gosub	320	rem check y or n
	if ok% then ded.sys.used%(4) = bool.val%
	gosub 131	rem display
	return

rem	ded.sys.desc$(4)

 232
	ded.sys.desc$(4) = in$	rem no checking done of description
	gosub	132	rem display
	return

rem	ded.sys.earn.ded$(4)

 233
	gosub	340	rem check that "e" or "d"
	if ok% then ded.sys.earn.ded$(4) = in$

	REM SET DEFAULT ACCOUNTS AND CHECK CATAGORIES
	if ok% and in$ = "E" \
	   then ded.sys.acct.no%(4) = pr1.default.dist.acct% :\
		ded.sys.chk.cat%(4) = 7 REM DEFAULT EARNING CHECK CATAGORY
	if ok% and in$ = "D" \
	   then ded.sys.acct.no%(4) = 2 :\REM DEFAULT ACCRUED LIABILITY ACCOUNT
		ded.sys.chk.cat%(4) = 16 REM DEFAULT DEDUCTION CHECK CATAGORY
	REM DISPLAY NEW ACCOUNT NUMBER AND CHECK CATAGORY
	if ok% \
	   then \
		gosub 134 :\	REM DISPLAY ACCOUNT
		gosub 135	REM DISPLAY CHECK CATAGORY

	gosub	133	rem display
	return

rem	ded.sys.acct.no%(4)

 234
	gosub	330	rem check acct no
	if ok% then ded.sys.acct.no%(4) = val(in$)
	gosub	134	rem display
	return

rem	ded.sys.chk.cat%(4)

 235
	earn.ded.index% = 4	rem index of earning.deduction string for
				rem validating check catagory
	gosub	350	rem check check catagory
	if ok% then ded.sys.chk.cat%(4) = val(in$)
	gosub	135	rem display
	return

rem	ded.sys.limit(4)

 236
	gosub	310	rem check limit
	if ok% then ded.sys.limit(4) = val(in$)
	gosub	136	rem display
	return

rem	ded.sys.factor(4)

 237
	gosub	300	rem check factor
	if ok% then ded.sys.factor(4) = val(in$)
	gosub	137	rem display
	return

rem	ded.sys.limit.used%(4)

 238
	gosub	320	rem check y or n
	if ok% then ded.sys.limit.used%(4) = bool.val%
	gosub	138	rem display
	return

rem	ded.sys.amt.percent$(4)

 239
	gosub	360	rem check that a or p
	if ok% then ded.sys.amt.percent$(4) = in$
	gosub	139	rem display
	return

rem	ded.sys.exclusion%(4)

 240
	gosub	370	rem check that valid exclusion code
	if ok% then ded.sys.exclusion%(4) = val(in$)
	gosub	140	rem display
	return


rem	ded.sys.used%(5)

 241
	gosub	320	rem check y or n
	if ok% then ded.sys.used%(5) = bool.val%
	gosub 141	rem display
	return

rem	ded.sys.desc$(5)

 242
	ded.sys.desc$(5) = in$	rem no checking done of description
	gosub	142	rem display
	return

rem	ded.sys.earn.ded$(5)

 243
	gosub	340	rem check that "e" or "d"
	if ok% then ded.sys.earn.ded$(5) = in$

	REM SET DEFAULT ACCOUNTS AND CHECK CATAGORIES
	if ok% and in$ = "E" \
	   then ded.sys.acct.no%(5) = pr1.default.dist.acct% :\
		ded.sys.chk.cat%(5) = 7 REM DEFAULT EARNING CHECK CATAGORY
	if ok% and in$ = "D" \
	   then ded.sys.acct.no%(5) = 2 :\REM DEFAULT ACCRUED LIABILITY ACCOUNT
		ded.sys.chk.cat%(5) = 16 REM DEFAULT DEDUCTION CHECK CATAGORY
	REM DISPLAY NEW ACCOUNT NUMBER AND CHECK CATAGORY
	if ok% \
	   then \
		gosub 144 :\	REM DISPLAY ACCOUNT
		gosub 145	REM DISPLAY CHECK CATAGORY

	gosub	143	rem display
	return

rem	ded.sys.acct.no%(5)

 244
	gosub	330	rem check acct no
	if ok% then ded.sys.acct.no%(5) = val(in$)
	gosub	144	rem display
	return

rem	ded.sys.chk.cat%(5)

 245
	earn.ded.index% = 5	rem index of earning.deduction string for
				rem validating check catagory
	gosub	350	rem check check catagory
	if ok% then ded.sys.chk.cat%(5) = val(in$)
	gosub	145	rem display
	return

rem	ded.sys.limit(5)

 246
	gosub	310	rem check limit
	if ok% then ded.sys.limit(5) = val(in$)
	gosub	146	rem display
	return

rem	ded.sys.factor(5)

 247
	gosub	300	rem check factor
	if ok% then ded.sys.factor(5) = val(in$)
	gosub	147	rem display
	return

rem	ded.sys.limit.used%(5)

 248
	gosub	320	rem check y or n
	if ok% then ded.sys.limit.used%(5) = bool.val%
	gosub	148	rem display
	return

rem	ded.sys.amt.percent$(5)

 249
	gosub	360	rem check that a or p
	if ok% then ded.sys.amt.percent$(5) = in$
	gosub	149	rem display
	return

rem	ded.sys.exclusion%(5)

 250
	gosub	370	rem check that valid exclusion code
	if ok% then ded.sys.exclusion%(5) = val(in$)
	gosub	150	rem display
	return



rem
rem	subroutine to check factor (###,###.##)
rem

 300	\
	ok% = fn.numeric%(in$,6,2)
	if not ok%	\
	   then trash% = fn.emsg%(4)
	return

rem
rem	subroutine to check limit (#,###,###.##)
rem

 310	\
	ok% = fn.numeric%(in$,7,2)
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
rem	subroutine to check that answer is E or D
rem

 340	\
	ok% = false%
	in$ = ucase$(in$)
	if in$ = "E" or in$ = "D"       \
	   then ok% = true%
	if not ok%	\
	   then trash% = fn.emsg%(8)
	return

rem
rem	subroutine to validify check catagory
rem		if earning may be 2 to 7
rem		if deduction may be 9 to 16
rem

350	\
	ok% = fn.num%(in$)
	if not ok%	\
	   then 	\
		print trash% = fn.emsg%(4)	:\
		return

	if ded.sys.earn.ded$(earn.ded.index%) = "E" and \
		val(in$) >= 2 and val(in$) <= 7 	\
	   then return

	if ded.sys.earn.ded$(earn.ded.index%) = "D" and \
		val(in$) >= 9 and val(in$) <= 16	\
	   then return

	ok% = false%
	trash% = fn.emsg%(10)
	return

rem
rem	subroutine to check that A or P
rem

 360	\
	ok% = false%
	in$ = ucase$(in$)
	if in$ = "A" or in$ = "P"       \
	   then 	\
		ok% = true%	:\
		return

	trash% = fn.emsg%(9)
	return

rem
rem	subroutine to check that valid exclusion code(1 to 4)
rem

 370	\
	ok% = fn.num%(in$)
	if not ok%	\
	   then goto 370.9	rem print error message
	if val(in$) >= 1 and val(in$) <= 4	\
	   then return
 370.9	ok% = false%
	trash% = fn.emsg%(4)
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

rem
rem	verify check catagory codes are valid
rem
	for i% = 1 to 5
		if ded.sys.chk.cat%(i%) >= 2 and	\
		   ded.sys.chk.cat%(i%) <= 7 and	\
		   ded.sys.earn.ded$(i%) = "E"          \
		then goto 920	rem valid

		if ded.sys.chk.cat%(i%) >= 9 and	\
		   ded.sys.chk.cat%(i%) <= 16 and	\
		   ded.sys.earn.ded$(i%) = "D"          \
		then goto 920	rem valid

rem	report error and return to input

		trash% = fn.emsg%(10)
		field% = i% *10 	rem field to reenter chk catagory
		goto 20 	rem main input driver
 920	next i%

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
   then   chain fn.file.name.out$(system$,null$,0,null$,null$) \
   else   stop
	end

