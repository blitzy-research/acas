#include "ipycomm"
prgname$="PYUPDLI     10-JAN-80"
#include "ipyconst"


rem----------------------------------------------------------------------
rem
REM
REM		UPDATE COMPANY LIABILITIES
REM
REM		(PYUPDLI)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "UPDATE COMPANY LIABILITIES"

REM
REM	THE FOLLOWING IS A GUIDE TO SUBROUTINES IN PYUPDLI
REM

REM	22	GOTO NEXT FIELD
REM	23	GOTO PREVIOUS FIELD

REM	100	DISPLAY ALL DATA FIELDS
REM	101-118 DISPLAY FIELDS 1 TO 18

REM	201-218 CHECK DATA FIELDS FOR VALIDITY

REM	300	GENERALISED DATA CHECKER



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

#include "znumeric"
#include "zstring"
#include "zdateio"
#include "zdspyorn"
#include "zfilconv"
#include "zckdigit"
#include "ipystat"
#include "ipydmhis"
#include "ipydmcoh"
#include "ipydmemp"

rem
rem	error messages
rem
	dim emsg$(30)
	emsg$(1) = "     PY921 INVALID RESPONSE"
	emsg$(2) = "     PY922 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY923 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY924 UNEXPECTED END OF FILE"
	emsg$(5) = "     PY925 NON-NUMERIC INPUT OR EXCEEDS 999,999.99"
	emsg$(6) = "     PY926 INVALID RECORD NUMBER"
	emsg$(7) = "     PY927 MAY NOT MOVE BACKWARDS FROM FIRST RECORD"
	emsg$(8) = "     PY928 MAY NOT MOVE TO NEXT RECORD FROM LAST RECORD"
	emsg$(9) = "     PY929 HISTORY UPDATE MAY NOT RUN AFTER APPY HAS RUN"
	emsg$(10)= "     PY930 EMPLOYEE FILE AND HISTORY FILE MUST BE PRESENT"
	emsg$(11)= "     PY931 INVALID OR NON-EXISTANT EMPLOYEE NUMBER"
	emsg$(13)= "     PY933 NON-NUMERIC INPUT OR EXCEEDS 9,999,999.99"



program$ = "PYUPDLI"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2

rem
rem	get screen set up
rem

#include "fpyucoli"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	first.data.field% = 1		rem init first data field
	last.data.field% = 18
	data.field.count% = 18

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP


REM
REM	READ IN COMPANY HISTORY FILE
REM

	if end #coh.file% then 998
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,null$,null$) \
	   as coh.file%

	read #coh.file%; \
#include "ipycoh"

	close coh.file%
	gosub 100	REM DISPLAY ALL DATA FIELDS


REM
REM	MAIN INPUT DRIVER
REM
	stopit% = false%
	field% = first.data.field%
while not stopit%

REM
REM	DATA FIELD INPUT
REM
	trash% = fn.get%(3,field%)
	ok% = true%	rem set flag that response is valid
REM
REM	IF VALID DATA RETURNED CHECK IT,ELSE TAKE CONTROL ACTION
REM
	if in.status% = req.valid% \
	   then gosub 21		REM GO CHECK DATA

	if in.status% = req.cr% \
	   then gosub 22	rem proceed to next field

	if in.status% = req.back% \
	   then gosub 24	rem proceed to previous field

	if in.status% = req.cancel% \
	   then \	rem exit from record without updateing
		stopit% = true% :\
		cancelit% = true%

	if in.status% = req.stopit% \
	   then \
		stopit% = true% :\
		trash% = fn.msg%("     STOP REQUESTED")
wend


REM
REM	EOJ PROCESSING
REM
	if end #coh.file% then 998
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,null$,null$) \
	   as coh.file%

	if not cancelit% \
	   then \
		print #coh.file%; \
#include "ipycoh"

	close coh.file%
	trash% = fn.msg%("     "+function.name$+" COMPLETED")
	chain fn.file.name.out$("pyupdmen",null$,0,null$,null$)



rem
rem	by field number select validation routine
rem

 21
	on field% gosub 	\ rem pick data checker by field
		201,	\
		202,	\
		203, \
		204, \
		205, \
		206, \
		207, \
		208, \
		209, \
		210, \
		211, \
		212, \
		213, \
		214, \
		215, \
		216, \
		217, \
		218

	if ok%	\
	   then gosub 22	REM PROCEED TO NEXT FIELD
	return

rem
rem	get set for next field
rem

 22	\
	field% = field% + 1
	if field% > crt.field.count%	\
	   then field% = 1	REM GET FIRST FIELD IF PAST LAST FIELD

	if field% = key.field% \
	   then goto 22 	REM SKIP PAST KEY FIELD
	if not fn.test%(crt.used%,field%) \
	   then goto 22 	REM SKIP PAST UNUSED FIELDS
	if not fn.test%(crt.io%,field%) \
	   then goto 22 	REM SKIP PAST OUTPUT ONLY FIELDS

	return			REM MAIN INPUT DRIVER

rem
rem	get set for previous field
rem

 24	\
	field% = field% - 1
	if field% < 1	\	REM GOTO LAST FIELD IF AT FIRST
		then field% = crt.field.count%

	if field% = key.field% \
	   then goto 24 	REM SKIP PAST KEY FIELD
	if not fn.test%(crt.used%,field%) \
	   then goto 24 	REM SKIP PAST UNUSED FIELDS
	if not fn.test%(crt.io%,field%) \
	   then goto 24 	REM SKIP PAST OUTPUT ONLY FIELDS

	return			REM MAIN INPUT DRIVER

rem
rem	subroutine to display all data fields
rem

 100
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
	return



rem
rem	display of each individual field
rem

 101	trash% = fn.put%(str$(coh.qtd.co.fica.liab),1) : return

 102	trash% = fn.put%(str$(coh.qtd.co.futa.liab),2) : return

 103	trash% = fn.put%(str$(coh.qtd.co.sui.liab),3) : return

 104	trash% = fn.put%(str$(coh.ytd.co.fica.liab),4) : return

 105	trash% = fn.put%(str$(coh.ytd.co.futa.liab),5) : return

 106	trash% = fn.put%(str$(coh.ytd.co.sui.liab),6) : return

 107	trash% = fn.put%(str$(coh.qtd.vac.earned),7) : return

 108	trash% = fn.put%(str$(coh.qtd.vac.taken),8) : return

 109	trash% = fn.put%(str$(coh.qtd.sl.earned),9) : return

 110	trash% = fn.put%(str$(coh.qtd.sl.taken),10) : return

 111	trash% = fn.put%(str$(coh.qtd.comp.time.earned),11) : return

 112	trash% = fn.put%(str$(coh.qtd.comp.time.taken),12) : return

 113	trash% = fn.put%(str$(coh.ytd.vac.earned),13) : return

 114	trash% = fn.put%(str$(coh.ytd.vac.taken),14) : return

 115	trash% = fn.put%(str$(coh.ytd.sl.earned),15) : return

 116	trash% = fn.put%(str$(coh.ytd.sl.taken),16) : return

 117	trash% = fn.put%(str$(coh.ytd.comp.time.earned),17) : return

 118	trash% = fn.put%(str$(coh.ytd.comp.time.taken),18) : return


REM
REM	DATA CHECKERS
REM

 201	gosub 300
	if ok% then coh.qtd.co.fica.liab = val(in$)
	gosub 101 : return

 202	gosub 300
	if ok% then coh.qtd.co.futa.liab = val(in$)
	gosub 102 : return

 203	gosub 300
	if ok% then coh.qtd.co.sui.liab = val(in$)
	gosub 103 : return

 204	gosub 300
	if ok% then coh.ytd.co.fica.liab = val(in$)
	gosub 104 : return

 205	gosub 300
	if ok% then coh.ytd.co.futa.liab = val(in$)
	gosub 105 : return

 206	gosub 300
	if ok% then coh.ytd.co.sui.liab = val(in$)
	gosub 106 : return

 207	gosub 300
	if ok% then coh.qtd.vac.earned = val(in$)
	gosub 107 : return

 208	gosub 300
	if ok% then coh.qtd.vac.taken = val(in$)
	gosub 108 : return

 209	gosub 300
	if ok% then coh.qtd.sl.earned = val(in$)
	gosub 109 : return

 210	gosub 300
	if ok% then coh.qtd.sl.taken = val(in$)
	gosub 110 : return

 211	gosub 300
	if ok% then coh.qtd.comp.time.earned = val(in$)
	gosub 111 : return

 212	gosub 300
	if ok% then coh.qtd.comp.time.taken = val(in$)
	gosub 112 : return

 213	gosub 300
	if ok% then coh.ytd.vac.earned = val(in$)
	gosub 113 : return

 214	gosub 300
	if ok% then coh.ytd.vac.taken = val(in$)
	gosub 114 : return

 215	gosub 300
	if ok% then coh.ytd.sl.earned = val(in$)
	gosub 115 : return

 216	gosub 300
	if ok% then coh.ytd.sl.taken = val(in$)
	gosub 116 : return

 217	gosub 300
	if ok% then coh.ytd.comp.time.earned = val(in$)
	gosub 117 : return

 218	gosub 300
	if ok% then coh.ytd.comp.time.taken = val(in$)
	gosub 118 : return


REM
REM	GENERALISED DATA CHECKERS
REM

 300	REM CHECK THAT IN FORM #,###,###.## FROM INPUT

	ok% = fn.numeric%(in$,7,2)
	if not ok% \
	   then trash% = fn.emsg%(13) REM NOT NUMERIC OR EXCCEDS 9,999,999.99
	return



rem
rem	unexpected end of file
rem

 998	\
	trash% = fn.emsg%(4)	REM UNEXPECTED END OF FILE
	goto 999.1	rem abnormal exit



#include "zeoj"

	end
