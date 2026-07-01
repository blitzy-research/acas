#include "ipycomm"
prgname$="PYTOTHIS      9-JAN-80"
#include "ipyconst"


rem----------------------------------------------------------------------
rem
REM
REM		E N T R Y
REM
REM		(PYTOTHIS)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "TOTAL EMPLOYEE HISTORIES"

REM
REM	THE FOLLOWING IS A GUIDE TO SUBROUTINES IN PYTOTHIS
REM

REM	600	READ CURRENT RECORD



rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------
#include "zdms"
#include "zdmsclr"
#include "zdmsabrt"
#include "zstring"
#include "zdateio"
#include "zfilconv"
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


program$ = "PYTOTHIS"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2


rem
rem	get screen set up
rem

#include "fpytoth"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP



REM
REM	OPEN AND READ COMPANY HISTORY FILE
REM

	if end #coh.file% then 998
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,null$,null$) \
	   as coh.file%

	read #coh.file%; \
#include "ipycoh"

	close coh.file%


REM
REM	ZERO TOTALING FIELDS
REM

	coh.qtd.income.taxable = 0
	coh.qtd.other.taxable = 0
	coh.qtd.other.nontaxable = 0
	coh.qtd.fica.taxable = 0
	coh.qtd.tips = 0
	coh.qtd.net = 0
	coh.qtd.eic.credit = 0
	coh.qtd.fwt.liab = 0
	coh.qtd.swt.liab = 0
	coh.qtd.lwt.liab = 0
	coh.qtd.fica.liab = 0
	coh.qtd.sdi.liab = 0
	coh.qtd.sys(01) = 0
	coh.qtd.sys(02) = 0
	coh.qtd.sys(03) = 0
	coh.qtd.sys(04) = 0
	coh.qtd.sys(05) = 0
	coh.qtd.emp(01) = 0
	coh.qtd.emp(02) = 0
	coh.qtd.emp(03) = 0
	coh.qtd.other.ded = 0
	coh.qtd.units(01) = 0
	coh.qtd.units(02) = 0
	coh.qtd.units(03) = 0
	coh.qtd.units(04) = 0

	coh.ytd.income.taxable = 0
	coh.ytd.other.taxable = 0
	coh.ytd.other.nontaxable = 0
	coh.ytd.fica.taxable = 0
	coh.ytd.tips = 0
	coh.ytd.net = 0
	coh.ytd.eic.credit = 0
	coh.ytd.fwt.liab = 0
	coh.ytd.swt.liab = 0
	coh.ytd.lwt.liab = 0
	coh.ytd.fica.liab = 0
	coh.ytd.sdi.liab = 0
	coh.ytd.sys(01) = 0
	coh.ytd.sys(02) = 0
	coh.ytd.sys(03) = 0
	coh.ytd.sys(04) = 0
	coh.ytd.sys(05) = 0
	coh.ytd.emp(01) = 0
	coh.ytd.emp(02) = 0
	coh.ytd.emp(03) = 0
	coh.ytd.other.ded = 0
	coh.ytd.units(01) = 0
	coh.ytd.units(02) = 0
	coh.ytd.units(03) = 0
	coh.ytd.units(04) = 0

	coh.ytd.comp.time.earned = 0
	coh.ytd.comp.time.taken = 0
	coh.ytd.vac.earned = 0
	coh.ytd.vac.taken = 0
	coh.ytd.sl.earned = 0
	coh.ytd.sl.taken = 0

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


REM
REM	MAIN INPUT DRIVER
REM
while his.current.record.no% <= his.hdr.no.recs%
	gosub 600	rem read history and employee record
	trash% = fn.put%(emp.no$,1)	REM THROW RECORD BEING PROCESSED ON SCREEN
	REM TOTAL ALL APPLICABLE FIELDS

coh.qtd.income.taxable = coh.qtd.income.taxable + his.qtd.income.taxable
coh.qtd.other.taxable = coh.qtd.other.taxable + his.qtd.other.taxable
coh.qtd.other.nontaxable = coh.qtd.other.nontaxable + his.qtd.other.nontaxable
coh.qtd.fica.taxable = coh.qtd.fica.taxable + his.qtd.fica.taxable
coh.qtd.tips = coh.qtd.tips + his.qtd.tips
coh.qtd.net = coh.qtd.net + his.qtd.net
coh.qtd.eic.credit = coh.qtd.eic.credit + his.qtd.eic
coh.qtd.fwt.liab = coh.qtd.fwt.liab + his.qtd.fwt
coh.qtd.swt.liab = coh.qtd.swt.liab + his.qtd.swt
coh.qtd.lwt.liab = coh.qtd.lwt.liab + his.qtd.lwt
coh.qtd.fica.liab = coh.qtd.fica.liab + his.qtd.fica
coh.qtd.sdi.liab = coh.qtd.sdi.liab + his.qtd.sdi
coh.qtd.sys(1) = coh.qtd.sys(1) + his.qtd.sys(1)
coh.qtd.sys(2) = coh.qtd.sys(2) + his.qtd.sys(2)
coh.qtd.sys(3) = coh.qtd.sys(3) + his.qtd.sys(3)
coh.qtd.sys(4) = coh.qtd.sys(4) + his.qtd.sys(4)
coh.qtd.sys(5) = coh.qtd.sys(5) + his.qtd.sys(5)
coh.qtd.emp(1) = coh.qtd.emp(1) + his.qtd.emp(1)
coh.qtd.emp(2) = coh.qtd.emp(2) + his.qtd.emp(2)
coh.qtd.emp(3) = coh.qtd.emp(3) + his.qtd.emp(3)
coh.qtd.other.ded = coh.qtd.other.ded + his.qtd.other.ded
coh.qtd.units(1) = coh.qtd.units(1) + his.qtd.units(1)
coh.qtd.units(2) = coh.qtd.units(2) + his.qtd.units(2)
coh.qtd.units(3) = coh.qtd.units(3) + his.qtd.units(3)
coh.qtd.units(4) = coh.qtd.units(4) + his.qtd.units(4)

coh.ytd.income.taxable = coh.ytd.income.taxable + his.ytd.income.taxable
coh.ytd.other.taxable = coh.ytd.other.taxable + his.ytd.other.taxable
coh.ytd.other.nontaxable = coh.ytd.other.nontaxable + his.ytd.other.nontaxable
coh.ytd.fica.taxable = coh.ytd.fica.taxable + his.ytd.fica.taxable
coh.ytd.tips = coh.ytd.tips + his.ytd.tips
coh.ytd.net = coh.ytd.net + his.ytd.net
coh.ytd.eic.credit = coh.ytd.eic.credit + his.ytd.eic
coh.ytd.fwt.liab = coh.ytd.fwt.liab + his.ytd.fwt
coh.ytd.swt.liab = coh.ytd.swt.liab + his.ytd.swt
coh.ytd.lwt.liab = coh.ytd.lwt.liab + his.ytd.lwt
coh.ytd.fica.liab = coh.ytd.fica.liab + his.ytd.fica
coh.ytd.sdi.liab = coh.ytd.sdi.liab + his.ytd.sdi
coh.ytd.sys(1) = coh.ytd.sys(1) + his.ytd.sys(1)
coh.ytd.sys(2) = coh.ytd.sys(2) + his.ytd.sys(2)
coh.ytd.sys(3) = coh.ytd.sys(3) + his.ytd.sys(3)
coh.ytd.sys(4) = coh.ytd.sys(4) + his.ytd.sys(4)
coh.ytd.sys(5) = coh.ytd.sys(5) + his.ytd.sys(5)
coh.ytd.emp(1) = coh.ytd.emp(1) + his.ytd.emp(1)
coh.ytd.emp(2) = coh.ytd.emp(2) + his.ytd.emp(2)
coh.ytd.emp(3) = coh.ytd.emp(3) + his.ytd.emp(3)
coh.ytd.other.ded = coh.ytd.other.ded + his.ytd.other.ded
coh.ytd.units(1) = coh.ytd.units(1) + his.ytd.units(1)
coh.ytd.units(2) = coh.ytd.units(2) + his.ytd.units(2)
coh.ytd.units(3) = coh.ytd.units(3) + his.ytd.units(3)
coh.ytd.units(4) = coh.ytd.units(4) + his.ytd.units(4)

coh.ytd.comp.time.earned = coh.ytd.comp.time.earned + emp.comp.accum
coh.ytd.comp.time.taken = coh.ytd.comp.time.taken + emp.comp.used

coh.ytd.vac.earned = coh.ytd.vac.earned + emp.vac.accum
coh.ytd.vac.taken = coh.ytd.vac.taken + emp.vac.used

coh.ytd.sl.earned = coh.ytd.sl.earned + emp.sl.accum
coh.ytd.sl.taken = coh.ytd.sl.taken + emp.sl.used

	his.current.record.no% = his.current.record.no% + 1

wend


REM
REM	WRITE OUT TOTALED COMPANY HISTORY
REM

	if end #coh.file% then 998
	open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,null$,null$) \
	   as coh.file%
	print #coh.file%; \
#include "ipycoh"

REM
REM	EOJ PROCESSING
REM
 10
	close his.file% : close emp.file% : close coh.file%

	trash% = fn.msg%("     " + function.name$ + " COMPLETED")

	chain fn.file.name.out$("pyupdmen",null$,0,null$,null$)



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
rem	unexpected end of file
rem

 998	\
	trash% = fn.emsg%(4)	REM UNEXPECTED END OF FILE
	goto 999.1	rem abnormal exit


#include "zeoj"

	end
