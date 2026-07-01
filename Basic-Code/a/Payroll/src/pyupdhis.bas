#include "ipycomm"
prgname$="PYUPDHIS     10-JAN-80"
#include "ipyconst"


rem----------------------------------------------------------------------
rem
REM
REM		E N T R Y
REM
REM		(PYUPDHIS)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "UPDATE EMPLOYEE'S HISTORY"

REM
REM	THE FOLLOWING IS A GUIDE TO SUBROUTINES IN PYUPDHIS
REM

REM	22	GOTO NEXT FIELD
REM	23	GOTO PREVIOUS FIELD

REM	100	DISPLAY ALL DATA FIELDS
REM	101-152 DISPLAY FIELDS 1 TO 52

REM	201	CHECK KEY FIELD FOR VALIDITY
REM	202-251 CHECK DATA FIELDS FOR VALIDITY

REM	300	GENERALISED DATA CHECKER

REM	600	READ CURRENT RECORD
REM	610	WRITE CURRENT RECORD

REM	700	DEFAULT FILE CREATION

REM	900	FINAL CONSISTANCY CHECKER



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
	emsg$(9) = "     PY929 HISTORY UPDATE MAY NOT RUN AFTER APPLY HAS RUN"
	emsg$(10)= "     PY930 EMPLOYEE FILE AND HISTORY FILE MUST BE PRESENT"
	emsg$(11)= "     PY931 INVALID OR NON-EXISTANT EMPLOYEE NUMBER"



program$ = "PYUPDHIS"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2



rem
rem	get screen set up
rem

#include "fpyuehis"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	key.field% = 1			rem init key field
	first.data.field% = 2		rem init first data field
	last.data.field% = 51
	data.field.count% = 51

	fld.emp.name% = 52

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP



REM
REM	CREATE COMPANY HISTORY FILE IF NOT PRESENT
REM

	if \
	 (size(fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,nul$,nul$))=0)\
	   then \
		gosub 700	REM CREATE DEFAULT COMPANY HISTORY FILE

REM
REM	VERIFY THAT OK TO RUN,CHECKING FLAG IN COMPANY HISTORY FILE
REM

	if end #coh.file% then 998
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,null$,null$) \
	   as coh.file%

	read #coh.file%; \
#include "ipycoh"

	if not coh.starting.up% \
	   then \
		trash% = fn.emsg%(9) :\
		goto 999.1	REM ERROR EXIT

	close coh.file%

REM
REM	CHECK THAT EMPLOYEE FILE AND HISTORY FILE PRESENT
REM

      if size(fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,null$,null$))=0\
      or size(fn.file.name.out$(his.name$,"101",pr1.his.drive%,null$,null$))=0\
	 then \
		trash% = fn.emsg%(10) :\
		goto 999.1	REM ERROR EXIT

REM
REM	OPEN EMPLOYEE FILE
REM

	if end #emp.file% then 998
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,null$,null$) \
	   recl emp.len% as emp.file%

rem
rem	open his file
rem

	if end #his.file% then 998
	open fn.file.name.out$(his.name$,"101",pr1.his.drive%,nul$,nul$)\
	   recl his.len% as his.file%

rem
rem	file exists so read in header and proceed
rem

	read #his.file% ,1;	\
#include "ipyhishd"

rem
rem	initialise flags and current record
rem
	his.current.record.no% = 1	rem init current record number
	gosub 600 : gosub 100		REM READ AND DISPLAY DEFAULT RECORD

REM
REM	MAIN INPUT DRIVER
REM
	field% = key.field%	rem start input driver at key field
	stopit% = false%
while not stopit%
rem
rem	handle key (record number) field seperately
rem
	if field% = key.field%	\
	   then \
		gosub 201	REM HANDLE KEY FIELD
	if stopit% \
	   then \
		goto 10 REM DONE GO DECIDE WHERE TO CHAIN TO

REM
REM	DATA FIELD INPUT
REM
	if field% <> key.field% then \
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
		field% = key.field%	:\ rem key field

	if in.status% = req.stopit% \
	   then \
		gosub 900	rem do final validity check
wend
REM
REM	DECIDE WHERE TO CHAIN TO
REM
 10
	close his.file% : close emp.file%

	if cancelit% \
	   then goto 999.2 \	REM OPERATOR REQUEST EXIT
	   else \
		trash% = fn.msg%("     "+function.name$+ \
		   " COMPLETED") :\
		chain fn.file.name.out$("PYTOTHIS",null$,0,null$,null$)



rem
rem	by field number select validation routine
rem

 21
	on field% gosub 	\ rem pick data checker by field
		201,	\rem first field should be handled seperately
		202, \
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
		218, \
		219, \
		220, \
		221, \
		222, \
		223, \
		224, \
		225, \
		226, \
		227, \
		228, \
		229, \
		230, \
		231, \
		232, \
		233, \
		234, \
		235, \
		236, \
		237, \
		238, \
		239, \
		240, \
		241, \
		242, \
		243, \
		244, \
		245, \
		246, \
		247, \
		248, \
		249, \
		250, \
		251

	if ok%	\
	   then gosub 22	REM PROCEED TO NEXT FIELD
	return

rem
rem	get set for next field
rem

 22	\
	field% = field% + 1
	if field% > last.data.field%	\
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
		then field% = last.data.field%

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
	gosub 152
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
	gosub 134
	gosub 135
	gosub 136
	gosub 137
	gosub 138
	gosub 139
	gosub 140
	gosub 141
	gosub 142
	gosub 143
	gosub 144
	gosub 145
	gosub 146
	gosub 147
	gosub 148
	gosub 149
	gosub 150
	gosub 151
	return


rem
rem	display of each individual field
rem

rem
rem	display record #
rem

 101
	trash% = fn.put%(emp.no$,key.field%)
	return

 102	trash% = fn.put%(str$(his.qtd.income.taxable),2) : return

 103	trash% = fn.put%(str$(his.qtd.other.taxable),3) : return

 104	trash% = fn.put%(str$(his.qtd.other.nontaxable),4) : return

 105	trash% = fn.put%(str$(his.qtd.fica.taxable),5) : return

 106	trash% = fn.put%(str$(his.qtd.eic),6) : return

 107	trash% = fn.put%(str$(his.qtd.tips),7) : return

 108	trash% = fn.put%(str$(his.qtd.net),8) : return

 109	trash% = fn.put%(str$(his.qtd.fwt),9) : return

 110	trash% = fn.put%(str$(his.qtd.swt),10) : return

 111	trash% = fn.put%(str$(his.qtd.lwt),11) : return

 112	trash% = fn.put%(str$(his.qtd.fica),12) : return

 113	trash% = fn.put%(str$(his.qtd.sdi),13) : return

 114	trash% = fn.put%(str$(his.qtd.sys(1)),14) : return

 115	trash% = fn.put%(str$(his.qtd.sys(2)),15) : return

 116	trash% = fn.put%(str$(his.qtd.sys(3)),16) : return

 117	trash% = fn.put%(str$(his.qtd.sys(4)),17) : return

 118	trash% = fn.put%(str$(his.qtd.sys(5)),18) : return

 119	trash% = fn.put%(str$(his.qtd.emp(1)),19) : return

 120	trash% = fn.put%(str$(his.qtd.emp(2)),20) : return

 121	trash% = fn.put%(str$(his.qtd.emp(3)),21) : return

 122	trash% = fn.put%(str$(his.qtd.other.ded),22) : return

 123	trash% = fn.put%(str$(his.qtd.units(1)),23) : return

 124	trash% = fn.put%(str$(his.qtd.units(2)),24) : return

 125	trash% = fn.put%(str$(his.qtd.units(3)),25) : return

 126	trash% = fn.put%(str$(his.qtd.units(4)),26) : return

 127	trash% = fn.put%(str$(his.ytd.income.taxable),27) : return

 128	trash% = fn.put%(str$(his.ytd.other.taxable),28) : return

 129	trash% = fn.put%(str$(his.ytd.other.nontaxable),29) : return

 130	trash% = fn.put%(str$(his.ytd.fica.taxable),30) : return

 131	trash% = fn.put%(str$(his.ytd.eic),31) : return

 132	trash% = fn.put%(str$(his.ytd.tips),32) : return

 133	trash% = fn.put%(str$(his.ytd.net),33) : return

 134	trash% = fn.put%(str$(his.ytd.fwt),34) : return

 135	trash% = fn.put%(str$(his.ytd.swt),35) : return

 136	trash% = fn.put%(str$(his.ytd.lwt),36) : return

 137	trash% = fn.put%(str$(his.ytd.fica),37) : return

 138	trash% = fn.put%(str$(his.ytd.sdi),38) : return

 139	trash% = fn.put%(str$(his.ytd.sys(1)),39) : return

 140	trash% = fn.put%(str$(his.ytd.sys(2)),40) : return

 141	trash% = fn.put%(str$(his.ytd.sys(3)),41) : return

 142	trash% = fn.put%(str$(his.ytd.sys(4)),42) : return

 143	trash% = fn.put%(str$(his.ytd.sys(5)),43) : return

 144	trash% = fn.put%(str$(his.ytd.emp(1)),44) : return

 145	trash% = fn.put%(str$(his.ytd.emp(2)),45) : return

 146	trash% = fn.put%(str$(his.ytd.emp(3)),46) : return

 147	trash% = fn.put%(str$(his.ytd.other.ded),47) : return

 148	trash% = fn.put%(str$(his.ytd.units(1)),48) : return

 149	trash% = fn.put%(str$(his.ytd.units(2)),49) : return

 150	trash% = fn.put%(str$(his.ytd.units(3)),50) : return

 151	trash% = fn.put%(str$(his.ytd.units(4)),51) : return

 152	trash% = fn.put%(emp.emp.name$,fld.emp.name%) : return



rem
rem	check validity of key field
rem

 201
	ok% = false%
while not ok%
	trash% = fn.get%(4,key.field%)

	if in.status% = req.adding% \
	   then \
		trash% = fn.emsg%(1)	REM ILLEGAL RESPONSE

	if in.status% = req.valid% \
	   then gosub 201.100		REM GO CHECK RECORD NUMBER

	if in.status% = req.cr% \
	   then \
		field% = first.data.field%	:\	rem first data field
		ok% = true%

	if in.status% = req.stopit%	\ rem exit with backup
	   then \
		trash% = fn.msg%("     STOP REQUESTED") :\
		stopit% = true% :\
		ok% = true%

	if in.status% = req.cancel%	\ rem cancel
	   then \
		stopit% = true% :\
		cancelit% = true% :\
		ok% = true%

	if in.status% = req.back%	\ rem move one record back
	   then \
		gosub 201.200		rem go one record back

	if in.status% = req.next%	\ rem go forward one record
	   then \
		gosub 201.300		rem go forward one field

wend
	return

rem
rem	data input to key field
rem

 201.100	REM GET AND CHECK EMPLOYEE NUMBER FROM INPUT

	ok% = false%
	REM CHECK EMP NUMBER SYNTAX AND EXISTANCE

	if in.len% <> 5 \
	   then \
		trash% = fn.emsg%(11) :\	REM INVALID EMP NUMVBER
		return

	if fn.ck.dig$(left$(in$,4)) <> right$(in$,1) \
	   then \	REM INVALID CHECK DIGIT
		trash% = fn.emsg%(11) :\
		return

	his.current.record.no% = val(left$(in$,4))
	if his.current.record.no%<1 or his.current.record.no%>his.hdr.no.recs%\
	   then \	REM EMP NOT IN FILE
		trash% = fn.emsg%(11) :\
		return

	ok% = true%
	gosub 600	REM READ DATA RECORD
	gosub 100	REM DISPLAY DATA
	return


rem
rem	subroutine go back one record
rem

 201.200
	if his.current.record.no% = 1	\ rem at first record
	   then \
		his.current.record.no% = his.hdr.no.recs% \
	   else \
		his.current.record.no% = his.current.record.no% - 1

	gosub 600	rem read record
	gosub 100	rem display record data
	record.data.valid% = true%	rem data from file is valid
	return

rem
rem	go forward one record
rem

 201.300
	if his.current.record.no% + 1 > his.hdr.no.recs% \ rem at last record
	   then \
		his.current.record.no% = 1 \
	   else \
		his.current.record.no% = his.current.record.no% + 1

	gosub 600	rem get data record
	gosub 100	rem display record data
	record.data.valid% = true%	rem data from file is valid
	return



 202	gosub 300
	if ok% then his.qtd.income.taxable = val(in$)
	gosub 102 : return

 203	gosub 300
	if ok% then his.qtd.other.taxable = val(in$)
	gosub 103 : return

 204	gosub 300
	if ok% then his.qtd.other.nontaxable = val(in$)
	gosub 104 : return

 205	gosub 300
	if ok% then his.qtd.fica.taxable = val(in$)
	gosub 105 : return

 206	gosub 300
	if ok% then his.qtd.eic = val(in$)
	gosub 106 : return

 207	gosub 300
	if ok% then his.qtd.tips = val(in$)
	gosub 107 : return

 208	gosub 300
	if ok% then his.qtd.net = val(in$)
	gosub 108 : return

 209	gosub 300
	if ok% then his.qtd.fwt = val(in$)
	gosub 109 : return

 210	gosub 300
	if ok% then his.qtd.swt=val(in$)
	gosub 110 : return

 211	gosub 300
	if ok% then his.qtd.lwt=val(in$)
	gosub 111 : return

 212	gosub 300
	if ok% then his.qtd.fica=val(in$)
	gosub 112 : return

 213	gosub 300
	if ok% then his.qtd.sdi=val(in$)
	gosub 113 : return

 214	gosub 300
	if ok% then his.qtd.sys(1)=val(in$)
	gosub 114 : return

 215	gosub 300
	if ok% then his.qtd.sys(2)=val(in$)
	gosub 115 : return

 216	gosub 300
	if ok% then his.qtd.sys(3)=val(in$)
	gosub 116 : return

 217	gosub 300
	if ok% then his.qtd.sys(4)=val(in$)
	gosub 117 : return

 218	gosub 300
	if ok% then his.qtd.sys(5)=val(in$)
	gosub 118 : return

 219	gosub 300
	if ok% then his.qtd.emp(1)=val(in$)
	gosub 119 : return

 220	gosub 300
	if ok% then his.qtd.emp(2)=val(in$)
	gosub 120 : return

 221	gosub 300
	if ok% then his.qtd.emp(3)=val(in$)
	gosub 121 : return

 222	gosub 300
	if ok% then his.qtd.other.ded=val(in$)
	gosub 122 : return

 223	gosub 300
	if ok% then his.qtd.units(1)=val(in$)
	gosub 123 : return

 224	gosub 300
	if ok% then his.qtd.units(2)=val(in$)
	gosub 124 : return

 225	gosub 300
	if ok% then his.qtd.units(3)=val(in$)
	gosub 125 : return

 226	gosub 300
	if ok% then his.qtd.units(4)=val(in$)
	gosub 126 : return

 227	gosub 300
	if ok% then his.ytd.income.taxable=val(in$)
	gosub 127 : return

 228	gosub 300
	if ok% then his.ytd.other.taxable=val(in$)
	gosub 128 : return

 229	gosub 300
	if ok% then his.ytd.other.nontaxable=val(in$)
	gosub 129 : return

 230	gosub 300
	if ok% then his.ytd.fica.taxable=val(in$)
	gosub 130 : return

 231	gosub 300
	if ok% then his.ytd.eic=val(in$)
	gosub 131 : return

 232	gosub 300
	if ok% then his.ytd.tips=val(in$)
	gosub 132 : return

 233	gosub 300
	if ok% then his.ytd.net=val(in$)
	gosub 133 : return

 234	gosub 300
	if ok% then his.ytd.fwt=val(in$)
	gosub 134 : return

 235	gosub 300
	if ok% then his.ytd.swt=val(in$)
	gosub 135 : return

 236	gosub 300
	if ok% then his.ytd.lwt=val(in$)
	gosub 136 : return

 237	gosub 300
	if ok% then his.ytd.fica=val(in$)
	gosub 137 : return

 238	gosub 300
	if ok% then his.ytd.sdi=val(in$)
	gosub 138 : return

 239	gosub 300
	if ok% then his.ytd.sys(1)=val(in$)
	gosub 139 : return

 240	gosub 300
	if ok% then his.ytd.sys(2)=val(in$)
	gosub 140 : return

 241	gosub 300
	if ok% then his.ytd.sys(3)=val(in$)
	gosub 141 : return

 242	gosub 300
	if ok% then his.ytd.sys(4)=val(in$)
	gosub 142 : return

 243	gosub 300
	if ok% then his.ytd.sys(5)=val(in$)
	gosub 143 : return

 244	gosub 300
	if ok% then his.ytd.emp(1)=val(in$)
	gosub 144 : return

 245	gosub 300
	if ok% then his.ytd.emp(2)=val(in$)
	gosub 145 : return

 246	gosub 300
	if ok% then his.ytd.emp(3)=val(in$)
	gosub 146 : return

 247	gosub 300
	if ok% then his.ytd.other.ded=val(in$)
	gosub 147 : return

 248	gosub 300
	if ok% then his.ytd.units(1)=val(in$)
	gosub 148 : return

 249	gosub 300
	if ok% then his.ytd.units(2)=val(in$)
	gosub 149 : return

 250	gosub 300
	if ok% then his.ytd.units(3)=val(in$)
	gosub 150 : return

 251	gosub 300
	if ok% then his.ytd.units(4)=val(in$)
	gosub 151 : return


REM
REM	GENERALISED DATA CHECKERS
REM

 300	REM CHECK THAT IN FORM ###,###.## FROM INPUT

	ok% = fn.numeric%(in$,6,2)
	if not ok% \
	   then trash% = fn.emsg%(5) REM NOT NUMERIC OR EXCCEDS 999,999.99
	return

rem
rem	read current record
rem
 600
	read #his.file% , his.current.record.no% + 1;	\
#include "ipyhis"

REM
REM	READ ASSOCIATED EMPLOYEE RECORD
REM

	read #emp.file% , his.current.record.no% + 1; \
#include "ipyemp"

	return

rem
rem	write current record
rem
 610
	print #his.file% , his.current.record.no% + 1;	\
#include "ipyhis"
	return



REM
REM	CREATE DEFAULT FILE
REM

 700

	create fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,null$,null$) \
	   as coh.file%

	coh.starting.up% = true%
	print #coh.file% ; \
#include "ipycoh"
	close coh.file%
	trash% = fn.msg%("     DEFAULT COMPANY HISTORY FILE CREATION COMPLETE")
	return


rem
rem	do final consistancy checks of data and write out if okay
rem
 900	\
	gosub 610	rem write record
	field% = key.field%	rem key(record #) field
	return

rem
rem	unexpected end of file
rem

 998	\
	trash% = fn.emsg%(4)	REM UNEXPECTED END OF FILE
	goto 999.1	rem abnormal exit



#include "zeoj"

	end
