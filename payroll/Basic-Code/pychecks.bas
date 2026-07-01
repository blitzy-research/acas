#include "ipycomm"

prgname$="PYCHECKS  DECEMBER 27,1979 "
rem---------------------------------------------------------
rem
rem	  P A Y R O L L
rem
rem	  P  Y	C  H  E  C  K  S
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------
function.name$="CHECK WRITER"
program$="PYCHECKS"
REM
REM-------------------------------------
REM----- INCLUDED DATA STRUCTURES ------
REM-------------------------------------
REM
#include "ipyconst"
#include "ipydmchk"
#include "ipydmemp"

REM
REM--------------------------------------------
REM----- LOCALLY DEFINED DATA STRUCTURES ------
REM--------------------------------------------
last.check.no= val(pr2.last.check.no$)

net.amt%= 8

fld.test.form%	= 1
fld.last.check% = 2
fld.first.check%= 3
fld.cur.check%	= 4
fld.cur.emp%	= 5
fld.abort%	= 6

lit.test.form%	= 11
lit.aligned%	= 12
lit.last.check% = 13
lit.first.check%= 14
lit.cur.check%	= 15
lit.cur.emp%	= 16
lit.abort%	= 17
lit.continue%	= 18
lit.over.max%	= 19
lit.check.void% = 20
lit.all.checks% = 21


REM
REM--------------------------------
REM----- CHECK FORMAT ARRAYS ------
REM--------------------------------
REM
ckf.hdr.lines.per.check%= 42
ckf.hdr.items%= 30
ckf.hdr.accums%= 1

dim ckf.item%(ckf.hdr.items%), ckf.y%(ckf.hdr.items%), ckf.x%(ckf.hdr.items%)
dim ckf.len% (ckf.hdr.items%)
dim ckf.chk.cat%(ckf.hdr.items%), ckf.accum%(ckf.hdr.items%)
dim accumulator(ckf.hdr.accums%), ckf.accum.accums%(ckf.hdr.accums%)

ckf.item%(01)= 11: ckf.y%(01)= 02: ckf.x%(01)= 76: ckf.len%(01)= 05
ckf.item%(02)= 12: ckf.y%(02)= 06: ckf.x%(02)= 03: ckf.len%(02)= 05
ckf.item%(03)= 14: ckf.y%(03)= 06: ckf.x%(03)= 37: ckf.len%(03)= 06
ckf.item%(04)= 14: ckf.y%(04)= 06: ckf.x%(04)= 65: ckf.len%(04)= 05
ckf.item%(05)= 14: ckf.y%(05)= 06: ckf.x%(05)= 75: ckf.len%(05)= 05
ckf.item%(06)= 07: ckf.y%(06)= 08: ckf.x%(06)= 04: ckf.len%(06)= 11
ckf.item%(07)= 14: ckf.y%(07)= 08: ckf.x%(07)= 37: ckf.len%(07)= 06
ckf.item%(08)= 14: ckf.y%(08)= 08: ckf.x%(08)= 56: ckf.len%(08)= 05
ckf.item%(09)= 14: ckf.y%(09)= 08: ckf.x%(09)= 65: ckf.len%(09)= 05
ckf.item%(10)= 14: ckf.y%(10)= 08: ckf.x%(10)= 74: ckf.len%(10)= 06
ckf.item%(11)= 14: ckf.y%(11)= 12: ckf.x%(11)= 04: ckf.len%(11)= 05
ckf.item%(12)= 14: ckf.y%(12)= 12: ckf.x%(12)= 13: ckf.len%(12)= 03
ckf.item%(13)= 14: ckf.y%(13)= 12: ckf.x%(13)= 20: ckf.len%(13)= 05
ckf.item%(14)= 14: ckf.y%(14)= 12: ckf.x%(14)= 43: ckf.len%(14)= 04
ckf.item%(15)= 14: ckf.y%(15)= 12: ckf.x%(15)= 51: ckf.len%(15)= 04
ckf.item%(16)= 14: ckf.y%(16)= 12: ckf.x%(16)= 59: ckf.len%(16)= 04
ckf.item%(17)= 14: ckf.y%(17)= 14: ckf.x%(17)= 04: ckf.len%(17)= 05
ckf.item%(18)= 14: ckf.y%(18)= 14: ckf.x%(18)= 43: ckf.len%(18)= 04
ckf.item%(19)= 08: ckf.y%(19)= 17: ckf.x%(19)= 64: ckf.len%(19)= 08
ckf.item%(20)= 09: ckf.y%(20)= 18: ckf.x%(20)= 64: ckf.len%(20)= 08
ckf.item%(21)= 14: ckf.y%(21)= 18: ckf.x%(21)= 74: ckf.len%(21)= 06
ckf.item%(22)= 10: ckf.y%(22)= 24: ckf.x%(22)= 66: ckf.len%(22)= 08
ckf.item%(23)= 11: ckf.y%(23)= 24: ckf.x%(23)= 80: ckf.len%(23)= 05
ckf.item%(24)= 13: ckf.y%(24)= 30: ckf.x%(24)= 67: ckf.len%(24)= 06
ckf.item%(25)= 01: ckf.y%(25)= 33: ckf.x%(25)= 10: ckf.len%(25)= 30
ckf.item%(26)= 02: ckf.y%(26)= 34: ckf.x%(26)= 10: ckf.len%(26)= 30
ckf.item%(27)= 03: ckf.y%(27)= 35: ckf.x%(27)= 10: ckf.len%(27)= 30
ckf.item%(28)= 04: ckf.y%(28)= 36: ckf.x%(28)= 10: ckf.len%(28)= 18
ckf.item%(29)= 05: ckf.y%(29)= 36: ckf.x%(29)= 31: ckf.len%(29)= 02
ckf.item%(30)= 06: ckf.y%(30)= 36: ckf.x%(30)= 35: ckf.len%(30)= 05


REM
REM-----------------------------
REM----- CHECK CATEGORIES ------
REM-----------------------------
REM
ckf.chk.cat%(03)= 02
ckf.chk.cat%(04)= 05
ckf.chk.cat%(05)= 06
ckf.chk.cat%(07)= 03
ckf.chk.cat%(08)= 04
ckf.chk.cat%(09)= 07
ckf.chk.cat%(10)= 01
ckf.chk.cat%(11)= 12
ckf.chk.cat%(12)= 10
ckf.chk.cat%(13)= 11
ckf.chk.cat%(14)= 14
ckf.chk.cat%(15)= 15
ckf.chk.cat%(16)= 16
ckf.chk.cat%(17)= 09
ckf.chk.cat%(18)= 13
ckf.chk.cat%(21)= 08
REM
REM------------------------
REM----- ACCUMULATORS -----
REM


REM----- ERROR MESSAGES -----

dim emsg$(30)
emsg$(01)="PY641  THIS MODULE MUST BE SELECTED FROM THE PAYROLL SYSTEM MENU"
emsg$(02)="PY642  THE SECOND PARAMETER FILE IS NOT ON THE SYSTEM DRIVE"
emsg$(03)="PY643  CHECK FILE WAS NOT RENAMED FOLLOWING EARLIER PROCESSING"
emsg$(04)="PY644  NO CHECK FILE FOUND"
emsg$(05)="PY645  CHECK FILE RENAME WAS UNSUCESSFUL"
emsg$(06)="PY646  THE CHECK FILE IS A NULL FILE"
emsg$(07)="PY647  UNABLE TO READ CHECK RECORD"
emsg$(08)="PY648  ERROR WHILE WRITING CHECK RECORD"
emsg$(09)="PY649  NO EMPLOYEE MASTER FILE FOUND"
emsg$(10)="PY650  THE EMPLOYEE FILE IS A NULL FILE"
emsg$(11)="PY651  UNABLE TO READ EMPLOYEE MASTER RECORD"
emsg$(12)="PY652  UNABLE TO UPDATE THE SECOND PARAMETER FILE"
emsg$(13)="PY653"
emsg$(14)="PY654"
emsg$(15)="PY655"
emsg$(16)="PY656"
emsg$(17)="PY657"
emsg$(18)="PY658"
emsg$(19)="PY659"
emsg$(20)="PY660  THAT'S NOT A VALID RESPONSE"
emsg$(21)="PY661  THAT'S NOT A VALID CHECK NUMBER"
emsg$(22)="PY662  ESC AND RETURN ARE THE ONLY RESPONSES ACCEPTED AT THIS FIELD"
emsg$(23)="PY663"
emsg$(24)="PY664"
emsg$(25)="PY665"
emsg$(26)="PY666"
emsg$(27)="PY667"
emsg$(28)="PY668"
emsg$(29)="PY669"
emsg$(30)="PY670"


REM
REM------------------------------------------
REM----- INCLUDED FUNCTION DEFINITIONS ------
REM------------------------------------------
REM
#include "zfilconv"
#include "znumber"
#include "zdateio"
#include "zstring"
#include "zflip"
REM
REM--------------------------------
REM----- DMS SYSTEM INCLUDES ------
REM--------------------------------
REM

#include "zdms"
#include "zdmsclr"


REM
REM------------------------------------------
REM----- PROGRAM EXECUTION STARTS HERE ------
REM------------------------------------------
REM
if not chained.from.root% then trash%= fn.emsg%(01): goto 999.1

if size(fn.file.name.out$(pr2.name$,"101",common.drive%,password$,params$))=0 \
	then trash%= fn.emsg%(02): goto 999.1

std.chk.name$=fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,password$,params$)
wrk.chk.name$=fn.file.name.out$(chk.name$,"100",pr1.chk.drive%,password$,params$)

if end #chk.file% then 2	rem branch ahead if no crashed file
open wrk.chk.name$ \
	as chk.file%
close chk.file%
trash%= fn.emsg%(03)
goto 999.1
REM
 2 REM----- HERE IF NO CRASHED CHECK FILE PRESENT ------
REM
if end #chk.file% then 1001
open std.chk.name$ \
	as    chk.file%
close chk.file%
trash%= rename(wrk.chk.name$, std.chk.name$)
if end #chk.file% then 1002
open wrk.chk.name$ \
	recl  chk.len% \
	as    chk.file%
if end #chk.file% then 1003
read #chk.file%, 1; \
#include "ipychkhdr"

if end #emp.file% then 1011
open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,password$,params$) \
	recl  emp.len% \
	as    emp.file%
if end #emp.file% then 1012
read #emp.file%, 1; \
#include "ipyemphdr"


REM
REM--------------------------
REM----- SET UP SCREEN ------
REM--------------------------
REM
#include "fpycheck"

trash%= fn.put.all%(false%)

REM
REM
 10 REM----- PRINT A TEST FORM AS MANY TIMES AS REQUIRED ------
REM
REM
trash%= fn.lit%(lit.test.form%)
trash%= fn.lit%(lit.aligned%)
more%= true%
while more%
	ok%= false%
	trash%= fn.get%(2, fld.test.form%)
	if in.status%= req.stopit% \
		then abort%= true%: goto 990	rem close files if stop req
	if in.uc$="Y" or in.status%= req.cr% \
		then ok%= true%: gosub 2000: \	--- load a test form
				 gosub 3000	rem print a check
	if in.uc$="N" \
		then ok%= true%: more%= false%
	if not ok% then trash%= fn.emsg%(20)
wend
trash%= fn.clr%(lit.test.form%)
trash%= fn.clr%(lit.aligned%)
REM
REM--------------------------------------------
REM----- ESTABLISH STARTING CHECK NUMBER ------
REM--------------------------------------------
REM
trash%= fn.lit%(lit.last.check%)
trash%= fn.lit%(lit.first.check%)
trash%= fn.put%(pr2.last.check.no$, fld.last.check%)
if last.check.no= 0 or last.check.no= 99999 \
	then first.check.no= 1 \
	else first.check.no= last.check.no+ 1
trash%= fn.put%(right$("000000"+str$(first.check.no), 5), fld.first.check%)
ok%= false%
while not ok%
	trash%= fn.get%(2, fld.first.check%)
	if in.status%= req.stopit% \
		then abort%= true%: goto 990	rem close files if stop req
	if in.status%= req.back%   then  10	rem print test forms
	if in.status%= req.cr%	   then ok%= true%
	if in.status%= req.valid% \
		then num%= fn.num%(in$): \
		     check.no= val(in$)
	if num% and check.no>=1 and check.no<=99999 \
		then ok%= true%: first.check.no= check.no: \
		     trash%= fn.put%(right$("000000"+str$(first.check.no), 5),\
		     fld.first.check%)

	if not ok% then trash%= fn.emsg%(21)
wend

REM
REM
REM----- CLEAR CHECK REGISTER FLAG IN CHECK HEADER -----
REM
REM
chk.hdr.register.printed%= false%
print #chk.file%, 1; \
#include "ipychkhdr"

REM
REM--------------------------------------
REM---- SET UP MAIN PROCESSING LOOP -----
REM--------------------------------------
REM
trash%= fn.lit%(lit.cur.check%)
trash%= fn.lit%(lit.cur.emp%)
cur.check.no= first.check.no
chk.rec%= 1
REM
REM------------------------------------
REM----- MAIN CHECK WRITING LOOP ------
REM------------------------------------
REM
while chk.rec%< chk.hdr.no.recs%+ 1
    chk.rec%= chk.rec%+ 1
    if end #chk.file% then 1004
    read #chk.file%, chk.rec%; \
#include "ipychk"

    while chk.check.no$= "NONE "
	REM-------------------------------------------------------------------
	REM----- CODE EXECUTED EXACTLY ONCE IF A CHECK IS TO BE WRITTEN ------
	REM-------------------------------------------------------------------
	check.written%= true%
	REM
	REM------------------------------------
	REM----- SET UP TO PRINT A CHECK ------
	REM------------------------------------
	REM
	chk.check.no$= right$("000000"+str$(cur.check.no), 5)

	REM--------------------------------------------------------
	REM----- PUT CHECK NUMBER, EMPLOYEE NUMBER ON SCREEN ------
	REM--------------------------------------------------------
	trash%= fn.put%(chk.check.no$, fld.cur.check%)
	trash%= fn.put%(chk.emp.no$,   fld.cur.emp%)
	REM
	REM------------------------------------------------
	REM----- WARN THAT VOID CHECK IF APPROPRIATE ------
	REM------------------------------------------------
	REM
	if pr1.void.chks.over.max% and chk.amt(net.amt%)> pr1.void.check.amt \
		then check.voided%= true%: \
		     trash%= fn.lit%(lit.over.max%): \
		     trash%= fn.lit%(lit.check.void%)
	REM
	REM---------------------------------
	REM----- READ EMPLOYEE RECORD ------
	REM---------------------------------
	REM
	if end #emp.file% then 1013
	read #emp.file%, val(left$(chk.emp.no$, 4))+ 1; \
#include "ipyemp"

	REM
	REM---------------------------------------------------
	REM----- REWRITE CHECK RECORD WITH CHECK NUMBER ------
	REM---------------------------------------------------
	REM
	if end #chk.file% then 1005
	print #chk.file%, chk.rec%; \
#include "ipychk"

	REM---------------------------------------------------------
	REM----- ACCUMULATE ANY SPECIAL TOTALS, PRINT A CHECK ------
	REM---------------------------------------------------------
	gosub 2500		rem accumulate
	gosub 2600		rem accumulate accumulators

	if check.voided% \
		then emp.emp.name$="*********** VOID **********": \
		     chk.amt(net.amt%)= 0.0

	gosub 3000		rem print a check

	last.check.no= cur.check.no
	cur.check.no= cur.check.no+ 1
	if cur.check.no> 99999 then cur.check.no= 1

	if abort% then 990	rem check print interrupted, stop requested
    wend
    REM-----------------------------------------------------------
    REM----- IF CHECK WAS VOIDED, CLEAR MESSAGES FROM SCREEN -----
    REM-----------------------------------------------------------
    REM
    if check.voided% \
	then check.voided%= false%: \
	     trash%= fn.clr%(lit.over.max%): \
	     trash%= fn.clr%(lit.check.void%)
wend
REM
REM----------------------------------------------------------
REM----- UPDATE HEADER -- ALL CHECKS HAVE BEEN PRINTED ------
REM----------------------------------------------------------
REM
if check.written% then lprinter:print:console	rem centronics hiccup

trash%= fn.lit%(lit.all.checks%)
chk.hdr.checks.printed%= true%
print #chk.file%, 1; \
#include "ipychkhdr"

REM
REM---------------------------------------------
 990 REM----- EOJ    CLOSE FILES AND EXIT ------
REM---------------------------------------------
REM
if abort% then trash%= fn.msg%("STOP REQUESTED")

close emp.file%
close chk.file%
trash%= rename(std.chk.name$, wrk.chk.name$)

if end #pr2.file% then 1020
open fn.file.name.out$(pr2.name$, "101", common.drive%, pw$, pm$) \
	as pr2.file%

pr2.last.check.no$= right$("000000"+str$(last.check.no), 5)

print #pr2.file%; \
#include "ipypr2"
close pr2.file%

if abort% then 999.2

#include "zeoj"

REM
REM
 1001 REM----- NO CHECK FILE ------
REM
REM
trash%= fn.emsg%(04)
goto 999.1
REM
REM
 1002 REM----- RENAME FAILED ON CHECK FILE ------
REM
REM
trash%= fn.emsg%(05)
goto 999.1
REM
REM
 1003 REM----- NO CHECK HEADER RECORD ------
REM
REM
trash%= fn.emsg%(06)
close chk.file%
goto 999.1
REM
REM
 1004 REM----- UNEXPECTED EOF ON CHECK FILE ------
REM
REM
trash%= fn.emsg%(07)
close chk.file%
close emp.file%
goto 999.1
REM
REM
 1005 REM----- UNABLE TO WRITE TO CHECK FILE ------
REM
REM
trash%= fn.emsg%(08)
close chk.file%
close emp.file%
goto 999.1
REM
REM
REM
 1011 REM----- NO EMPLOYEE MASTER FILE ------
REM
REM
trash%= fn.emsg%(09)
close chk.file%
goto 999.1
REM
REM
 1012 REM----- NO EMPLOYEE MASTER HEADER RECORD ------
REM
REM
trash%= fn.emsg%(10)
close chk.file%
close emp.file%
goto 999.1
REM
REM
 1013 REM----- UNEXPECTED EOF ON EMPLOYEE MASTER FILE READ ------
REM
REM
trash%= fn.emsg%(11)
close emp.file%
close chk.file%
goto 999.1
REM
REM-------------------------------------------
 1020 REM----- EOF ON PR2 UPDATE AT END ------
REM-------------------------------------------
REM
trash%= fn.emsg%(12)
goto 999.1

REM
REM------------------------
REM----- SUBROUTINES ------
REM------------------------
REM
REM--------------------------------------------
 2000 REM----- LOAD AND PRINT A TEST FORM ------
REM--------------------------------------------
REM
emp.emp.name$="***** VOID **** TEST FORM ****"
emp.addr1$   ="12345 TEST STREET ************"
emp.addr2$   ="***** ADDRESS LINE TWO *******"
emp.city$    ="****** CITY ******"
emp.state$   ="XX"
emp.zip$     ="00000"
emp.ssn$     ="*TEST FORM*"
chk.check.no$="VOID*"
chk.emp.no$="*VOID"
chk.amt(net.amt%)= 0.0
RETURN
REM
    REM--------------------------------------
 2500 REM----- ACCUMULATE SPECIAL TOTALS ------
    REM--------------------------------------
REM
for f%= 1 to ckf.hdr.items%
    if ckf.accum%(f%) > 0  and ckf.chk.cat%(f%) > 0 \
	then accumulator(ckf.accum%(f%))= \
	     accumulator(ckf.accum%(f%))+ chk.amt(ckf.chk.cat%(f%))
next f%
RETURN
REM
    REM
 2600 REM----- ACCUMULATE ACCUMULATORS ------
    REM
REM
for f%= 1 to ckf.hdr.accums%
accumulator(ckf.accum.accums%(f%))= \
accumulator(ckf.accum.accums%(f%))+ accumulator(f%)
next f%
RETURN

REM
REM-------------------------------
 3000 REM----- PRINT A CHECK -----
REM-------------------------------
REM
line.no%= 1
lprinter
for f%= 1 to ckf.hdr.items%
    need.response%= false%
    if constat% then need.response%= true%: console: trash%= conchar%: \
		     trash%= fn.lit%(lit.abort%): \
		     trash%= fn.lit%(lit.continue%)
    while need.response%
	trash%= fn.get%(2, fld.abort%)
	if in.status%= req.stopit% then abort%= true%: RETURN
	if in.status%= req.cr% \
		then need.response%= false%: \
		     trash%= fn.clr%(lit.abort%): \
		     trash%= fn.clr%(lit.continue%): \
		     lprinter \
		else trash%= fn.emsg%(22)
    wend
    while ckf.y%(f%)> line.no%
	print
	line.no%= line.no%+ 1
    wend
    if ckf.x%(f%)>= pos  \
	then print tab(ckf.x%(f%));
    if ckf.len%(f%) > 2 \
	then cur.str.format$= left$("/"+blank$, ckf.len%(f%)-2)+"/" \
	else cur.str.format$= "//"
    cur.num.format$= left$(pound$, ckf.len%(f%))+".##"
    on ckf.item%(f%) gosub \
		3101, \
		3102, \
		3103, \
		3104, \
		3105, \
		3106, \
		3107, \
		3108, \
		3109, \
		3110, \
		3111, \
		3112, \
		3113, \
		3114
next f%
while line.no%<= ckf.hdr.lines.per.check%
	print
	line.no%= line.no%+ 1
wend
console
RETURN


REM--------------------------------
 3101 REM----- EMPLOYEE NAME ------
REM--------------------------------
REM
print fn.name.flip$(emp.emp.name$);

RETURN

REM
REM
REM------------------------------------------
 3102 REM----- EMPLOYEE ADDRESS LINE 1 ------
REM------------------------------------------
REM
print emp.addr1$;

RETURN

REM
REM
REM--------------------------
 3103 REM-----
REM--------------------------
REM
print emp.addr2$;

RETURN

REM
REM
REM--------------------------
 3104 REM-----
REM--------------------------
REM
print emp.city$;

RETURN

REM
REM
REM--------------------------
 3105 REM-----
REM--------------------------
REM
print emp.state$;

RETURN

REM
REM
REM--------------------------
 3106 REM-----
REM--------------------------
REM
print emp.zip$;

RETURN

REM
REM
REM--------------------------
 3107 REM-----
REM--------------------------
REM
print emp.ssn$;

RETURN

REM
REM
REM--------------------------
 3108 REM-----
REM--------------------------
REM
if chk.interval$= "W" or chk.interval$= "S" \
	then print fn.date.out$(chk.hdr.fast.from.date$); \
	else print fn.date.out$(chk.hdr.slow.from.date$); \

RETURN

REM
REM
REM--------------------------
 3109 REM-----
REM--------------------------
REM
print fn.date.out$(chk.hdr.to.date$);

RETURN

REM
REM
REM--------------------------
 3110 REM-----
REM--------------------------
REM
print fn.date.out$(pr2.check.date$);

RETURN

REM
REM
REM--------------------------
 3111 REM-----
REM--------------------------
REM
print chk.check.no$;

RETURN

REM
REM
REM--------------------------
 3112 REM-----
REM--------------------------
REM
print chk.emp.no$;

RETURN

REM
REM
REM--------------------------
 3113 REM-----
REM--------------------------
REM
print using "$$"+right$(cur.num.format$, len(cur.num.format$)-2); \
     chk.amt(net.amt%);

RETURN

REM
REM
REM--------------------------
 3114 REM-----
REM--------------------------
REM
print using cur.num.format$; chk.amt(ckf.chk.cat%(f%));

RETURN
