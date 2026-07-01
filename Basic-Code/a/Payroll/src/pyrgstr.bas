#include "ipycomm"
prgname$="PYRGSTR     16-JAN-80"
#include "ipyconst"


rem----------------------------------------------------------------------
rem
REM
REM		CHECK REGISTER
REM
REM		(PYRGSTR)
REM
REM	COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
REM
REM----------------------------------------------------------------------

function.name$ = "CHECK REGISTER"

REM
REM	FOLLOWING IS A GUIDE TO SUBROUTINES IN PYRGSTR
REM

REM	50	PROCESSING MESSAGE
REM	60	CLEAR SCREEN OF UNNEEDED FIELDS

REM	100	MAIN DRIVER FOR PRINTING CYCLE

REM	1000	PRINT HEADER
REM	1010	PRINT "REPORT CONTINUES"
REM	1020	PRINT "END OF REPORT"

REM	1100	PRINT CHECK REGISTER
REM	1190	PRINT TITLES

REM	2000	READ CHECK RECORD
REM	2200	PRINT CURRENT CHECK ON SCREEN



rem------------------------------------------------------------------
rem
rem		DMS SYSTEM
rem
rem--------------------------------------------------------------------

#include "zdms"
#include "zdmstest"
#include "zdmsclr2
#include "zdmsconf"
#include "zdmsabrt"
#include "zdmsused"
#include "zdmsbrt"

#include "zstring"
#include "zdateio"
#include "zfilconv"
#include "zflip"
#include "zheading"

#include "ipystat"
#include "ipydmchk"
#include "ipydmemp"


rem
rem	error messages
rem
	dim emsg$(30)
	emsg$(1) = "     PY701 INVALID RESPONSE"
	emsg$(2) = "     PY702 PROGRAM NOT RUN FROM MENU"
	emsg$(3) = "     PY703 INVALID USE OF CONTROL CHARACTER"
	emsg$(4) = "     PY704 UNEXPECTED END OF EMPLOYEE FILE"
	emsg$(5) = "     PY705 UNEXPECTED END OF CHECK FILE"


program$ = "PYRGSTR"

rem
rem	check that chained correctly
rem

	if not chained.from.root%	\
		then print tab(10);crt.alarm$,emsg$(2)	:\
			goto 999.2



rem
rem	get screen set up
rem

#include "fpyrgstr"

REM
REM	DEFINE SCREEN IDENTIFIERS
REM

	fld.now.processing% = 1
	lit.processing% = 6

	trash% = fn.put.all%(false%)	REM THROW SCREEN UP




rem
rem	open CHK file
rem

	if end #chk.file% then 998
	open fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,nul$,nul$)\
		recl chk.len% as chk.file%

rem
rem	file exists so read in header and proceed
rem

	read #chk.file% ,1;	\
#include "ipychkhd"

REM
REM	OPEN EMPLOYEE FILE
REM
	if end #emp.file% then 997
	open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,null$,null$) \
		recl emp.len% as emp.file%

REM
REM	INIT OTHER STUFF
REM

	line.count.limit% = pr1.lines.per.page%



REM
REM	CRT INPUT DRIVER
REM

	rgstr.printed% = false%
	while not rgstr.printed%
		gosub 50	REM PROCESSING MESSAGE
		gosub 100	REM MAIN PRINTING DRIVER
		gosub 60	REM CLEAR SCREEN OF PROCESSING MESSAGE
		rgstr.printed% = true%
	wend

	if stopit% or stop.print% \
	   then \
		close chk.file% : goto 999.2 \	REM OPERATOR REQUESTED EXIT
	   else \
		chk.hdr.register.printed% = true% :\	REM SET PRINTED FLAG
		print #chk.file% , 1; \
#include "ipychkhd"
	close chk.file%
	goto 999		REM NORMAL EXIT


 50	REM PROCESSING MESSAGE

	trash% = fn.lit%(lit.processing%)
	return

 60	REM CLEAR SCREEN OF UNNEEDED FIELDS UPON PROCESSING COMPLETION

	trash% = fn.clr%(fld.now.processing%)
	trash% = fn.clr%(lit.processing%)
	return



REM
REM	MAIN DRIVER FOR PRINTING PROCESSING
REM

 100
	page% = 0
	current.chk.record% = 1
	stop.print% = false%
	line.count% = line.count.limit% REM FORCE HEADING AT BEGGINGING
	lprinter

while not stop.print% and current.chk.record% <= chk.hdr.no.recs%
	gosub 2000	REM READ CHECK
	gosub 2100	REM READ CORRESPONDING EMPLOYEE RECORD
	gosub 2200	REM DISPLAY NUMBER ON SCREEN
	gosub 1100	REM PRINT CHECK INFO

	if pr1.debugging% \
	   then \
		console :\
		trash% = fn.msg%("fre="+str$(fre)) :\
		lprinter

	current.chk.record% = current.chk.record% + 1
wend

	if not stop.print% \
	   then \
		gosub 1020	REM PRINT END OF REPORT LINE

	console
	return



REM
REM	UNEXPECTED END OF EMPLOYEE FILE
REM

 997
	console
	trash% = fn.emsg%(4)	REM UNEXPECTED END OF EMPLOYEE FILE
	goto 999.1	REM ABNORMAL EXIT

REM
REM	UNEXPECTED END OF CHECK FILE
REM

 998
	console
	trash% = fn.emsg%(5)	REM UNEXPECTED END OF CHECK FILE
	goto 999.1	REM ABNORMAL EXIT

#include "zeoj"



 1000	REM PRINT HEADING
	line.count% = fn.hdr%(function.name$)
	return

 1010	REM PRINT *** REPORT CONTINUES ***
	if page% <> 0 \ REM SKIP CONTINUES MESSAGE IF REPORT HASN'T STARTED YET
	   then \
		print "     *** REPORT CONTINUES ***"
	return

 1020	REM PRINT *** END OF REPORT ***
	if page% = 0 \	REM NO PAGES HENCE NO CHECKS
	   then \
		gosub 1000	:\	REM PRINT TITLES
		print	:\
		print tab(30);"*** NO CHECKS IN FILE ***" :\
		print

	print "     *** END OF REPORT ***"
	print
	return


 1100	REM CHECK PRINT

	if line.count% + 3 > line.count.limit% \
	   then \
		gosub 1010 :\	REM CONTINUED LINE
		gosub 1000 :\	REM PRINT HEADER
		gosub 1190	REM PRINT TITLES

	if stop.print% then return	REM PRINT TITLES CHECKS FN.ABORT

	print tab(2);chk.check.no$; \
		tab(12);chk.emp.no$;
	print using "##,###.##" ; \
		tab(43);chk.amt(1); \
		tab(54);chk.amt(2); \
		tab(65);chk.amt(3); \
		tab(76);chk.amt(4); \
		tab(87);chk.amt(5); \
		tab(98);chk.amt(6); \
		tab(109);chk.amt(7); \
		tab(120);chk.amt(8)
	stop.print% = fn.abort%
	if stop.print% then return

	print tab(12);fn.name.flip$(emp.emp.name$);
	print using "##,###.##"; \
		tab(43);chk.amt(9); \
		tab(54);chk.amt(10); \
		tab(65);chk.amt(11); \
		tab(76);chk.amt(12); \
		tab(87);chk.amt(13); \
		tab(98);chk.amt(14); \
		tab(109);chk.amt(15); \
		tab(120);chk.amt(16)
	stop.print% = fn.abort%
	if stop.print% then return

	print
	line.count% = line.count% + 3
	stop.print% = fn.abort% REM ALLOW USER TO ABORT PRINT
	return

 1190	REM PRINT TITLES
	print
	print tab(2);"CHECK NO"; \
		tab(12);"EMPLOYEE NO"; \
		tab(45);"GROSS"; \
		tab(54);left$(pr1.rate.name$(1),10); \
		tab(65);left$(pr1.rate.name$(2),10); \
		tab(76);left$(pr1.rate.name$(3),10); \
		tab(87);left$(pr1.rate.name$(4),10); \
		tab(99);"OTH PAY"; \
		tab(110);"OTH PAY"; \
		tab(121);"NET"
	stop.print% = fn.abort%
	if stop.print% then return

	print tab(12);"EMPLOYEE NAME";\
		tab(46);"FWT"; \
		tab(57);"SWT"; \
		tab(68);"LWT"; \
		tab(79);"FICA"; \
		tab(90);"SDI"; \
		tab(99);"OTH DED"; \
		tab(110);"OTH DED"; \
		tab(121);"OTH DED"
	stop.print% = fn.abort%

	line.count% = line.count% + 3
	return

 2000	REM READ CHECK RECORD

	read #chk.file%,current.chk.record% + 1; \
#include "ipychk"
	return

 2100	REM READ EMPLOYEE RECORD CORRESPONDING TO EMP NUMBER IN CHECK RECORD

	read #emp.file%,val(left$(chk.emp.no$,4)) + 1; \
#include "ipyemp"
	return



 2200	REM PUT CHECK NO ON SCREEN

	console
	trash% = fn.put%(chk.check.no$,fld.now.processing%)
	lprinter
	return

	end
