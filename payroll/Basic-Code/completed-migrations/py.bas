REM #include "ipycomm"
REM #include zcommon			rem 11/06/79
rem-----SYSTEM COMMONS---11/06/79---------------------------------------
common chained.from.root%        rem T/F true if called from menu
common chained%                  rem T/F true if called from anybody
common chained.program.number%   rem 0-99 number of this program
common common.return.code%       rem 0 if ok, else 1,2,etc
common common.msg$               rem error msg for menu to print
common common.chaining.status$   rem genl info, codes are in include
common common.serial.number$     rem serial number, stupid
common common.date$              rem yymmdd   RUN date from menu
common common.drive%             rem internal drive where PR1 and PR2 files are
common true%,false%              rem -1, 0 for logical true, false
common sector.len%,pumpkin       rem  disk sector size, zserial constant
common tof$,quote$,bell$,comma$  rem character strings
common pound$, blank$            rem "#...#" and blanks
rem---------------------------------------------------------------------

REM #include zdmscomm
REM	Nov.  6, 1979	   -----------------------------------------
REM
REM	COMMON AREA FOR DMS VARIABLES (INCLUDING CRT CHARACTERISTICS)
REM	STANDARD
REM-----------------------------------------------------------------
%nolist
common	crt.sca$, crt.sca.row$, crt.sca.column$
common	crt.clear$
common	crt.foreground$, crt.background$, crt.clear.foreground$
common	crt.home.cursor$
common	crt.up.cursor$, crt.down.cursor$, crt.right.cursor$, crt.left.cursor$
common	crt.backspace$
common	crt.alarm$
common	crt.eol$, crt.eos$
common	crt.insert.line$, crt.delete.line$
common	crt.order.row.col%, crt.order.col.row%, crt.sca.order%
common	crt.sca.hex%, crt.sca.decimal%, crt.sca.format%
common	crt.rows%,crt.columns%
common	crt.row.xlate%(1), crt.column.xlate%(1)
common	crt.file%
common	crt.msg.header$, crt.msg.trailer$
common	crt.mult.backspaces$(1), crt.back.count$
common	crt.ctl.xlate$
common	crt.key.prefix%, crt.key.xlate$
common	crt.strnum%, crt.brktsgn%, crt.used%, crt.brt%, crt.io%
common	crt.sgn.fmt$(1),  crt.sgn.rd.fmt$(1)
common	crt.brkt.fmt$(1), crt.brkt.rd.fmt$(1)
common	crt.pad.fmt$(1),  crt.pad.rd.fmt$(1)
common	req.valid%, req.stopit%, req.cr%, req.back%, req.cancel%
common	req.next%, req.save%, req.adding%, req.delete%
common	asc.lspace%, asc.refresh%, asc.cr%, asc.del%
common	ctl.stopit$, ctl.cr$, ctl.back$, ctl.cancel$, ctl.next$
common	ctl.save$, ctl.adding$, ctl.delete$
common	crt.ctl.tbl$
common	crt.ctl.mask$(1)
%list
REM  END OF DMS COMMON	----------------------------------------
REM

REM #include ipycfile
rem 11/06/79  -- FILE NUMBERS, LENGTHS, NAMES IN COMMON ------
common hrs.file%, hrs.len%, hrs.name$
common emp.file%, emp.len%, emp.name$
common his.file%, his.len%, his.name$
common pay.file%, pay.len%, pay.name$
common pyo.file%, pyo.len%, pyo.name$
common chk.file%, chk.len%, chk.name$
common ckh.file%, ckh.len%, ckh.name$
common cho.file%, cho.len%, cho.name$
common coh.file%,	        coh.name$
common act.file%, act.len%, act.name$
common ded.file%,   	    ded.name$
common pr1.file%,	        pr1.name$
common pr2.file%,    	    pr2.name$
common swt.file%,	        swt.name$
common lwt.file%,   	    lwt.name$
common cal.file%,   	    cal.name$
rem----------------------------------------------------------

REM #include ipycpr1
common pr1.debugging%		rem 12/14/79
common pr1.co.name$
common pr1.co.addr1$
common pr1.co.addr2$
common pr1.co.addr3$
common pr1.co.city$
common pr1.co.state$
common pr1.co.zip$
common pr1.co.phone$
common pr1.ded.drive%
common pr1.gld.drive%
common pr1.emp.drive%
common pr1.his.drive%
common pr1.hrs.drive%
common pr1.act.drive%
common pr1.glx.drive%
common pr1.chk.drive%
common pr1.tax.drive%
common pr1.pay.drive%
common pr1.pyo.drive%
common pr1.ckh.drive%
common pr1.coh.drive%
common pr1.cho.drive%
common pr1.offset.cash.acct%
common pr1.rate2.factor
common pr1.rate3.factor
common pr1.rate4.exclusion.type%
common pr1.rate.name$(1)
common pr1.min.wage
common pr1.check.printing.used%
common pr1.bell.suppressed%
common pr1.s.used%
common pr1.m.used%
common pr1.w.used%
common pr1.b.used%
common pr1.chk.history.used%
common pr1.void.chks.over.max%
common pr1.leading.crlf%
common pr1.console.width.poke.addr%
common pr1.jc.used%
common pr1.gl.used%
common pr1.default.pay.interval$
common pr1.default.dist.acct%
common pr1.default.pay.rate
common pr1.gl.file.suffix$
common pr1.default.norm.units
common pr1.default.hs.type$
common pr1.max.pay.factor
common pr1.default.vac.rate
common pr1.default.sl.rate
common pr1.fed.id$
common pr1.state.id$
common pr1.local.id$
common pr1.date.dy%,pr1.date.mo%,pr1.date.yr%
common pr1.lines.per.page%
common pr1.page.width%
common pr1.user.program.used%,pr1.user.program$,pr1.user.prog.desc$
common pr1.dist.used%
common pr1.max.chk.cats%  rem 11/06/79 these aren't in pr1 file
common pr1.max.dist.accts%
common pr1.max.sys.eds%
common pr1.max.emp.eds%
common pr1.max.ed.cats%
common pr1.void.check.amt
common pr1.max.swt.entries%
common pr1.lo.ded.chk.cat%
common pr1.hi.ded.chk.cat%
common pr1.lo.earn.chk.cat%
common pr1.hi.earn.chk.cat%

REM #include ipycpr2
common pr2.year%		rem 12/02/79
common pr2.last.sm.apply.no%, pr2.last.wb.apply.no%
common pr2.no.of.sm.applies%, pr2.no.of.wb.applies%
common pr2.hrs.batch.no%
common pr2.last.day.of.last.w$, pr2.last.day.of.last.b$
common pr2.last.day.of.last.s$, pr2.last.day.of.last.m$
common pr2.940.printed%, pr2.941.printed%, pr2.w2.printed%
common pr2.no.acts%
common pr2.no.active.emps%, pr2.no.employees%
common pr2.check.date$
common pr2.last.check.no$
common pr2.last.q.ended%
common pr2.just.closed.year%

prgname$="PY  JAN. 08,1980 "
rem---------------------------------------------------------
rem            This prog calls QSORT
rem	  P A Y R O L L
rem
rem	  P  Y
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------
function.name$="PROGRAM SELECTION"
program$="PY"

rem----- initialize disc directories -------------------------
initialize
rem----- console -----------------------------------------
console
rem----- set up chaining ---------------------------------
REM #include "ipychain"
%chain 100,14300,1100,5200		rem 01/18/80

REM--------------------------------------------------
REM----- LOCAL DATA FROM EXTERNAL SOURCE FILES ------
REM--------------------------------------------------

REM #include "ipyconst"
rem	 JAN. 18, 1980
system$="PY":version$=" REL:1.0 "
system.name$="PAYROLL SYSTEM"
cpyrght$="COPYRIGHT (C) 1980, APPLEWOOD COMPUTERS "
dummy$="PYppppI00":null$="":asc.quote%= 34
dim crt.data$(0),crt.x%(0),crt.y%(0),crt.len%(0),crt.rd%(0),crt.attrib%(0)

REM #include "ipystat"
startup$		="STARTUP"        rem   12/14/79
rebuild.pr1$	="FIXPR1"
rebuild.pr2$	="FIXPR2"
in.apply$		="APPLICATION"
in.dedent$		="DEDENT"
in.parent$		="PARENTRY"
normal$ 		="NORMAL"
default$		="DEFAULTS"
quarter.end$	="QEND"
year.end$		="YEND"

REM
REM--------------------------------------------------------
REM----- GLOBAL DATA FOR ALL PAYROLL SYSTEM PROGRAMS ------
REM--------------------------------------------------------
REM
REM #include "zconst"
rem	 Jan. 18, 1980
true%=-1:false%=0:sector.len%=128:pumpkin=3950+77
tof$=chr$(12):quote$=chr$(34):bell$=chr$(7):comma$=","
pound$="##############"
blank$="                                                                                                                                "


REM
REM-------------------------------------------------------------
REM----- MORE GLOBAL DATA FOR ALL PAYROLL SYSTEM PROGRAMS ------
REM-------------------------------------------------------------
if pr1.bell.suppressed% then bell$= null$ \
			else bell$= chr$(7)

    hrs.file%=03:hrs.len%=32:      hrs.name$="PYHRS"
    emp.file%=04:emp.len%=701:     emp.name$="PYEMP"
    his.file%=05:his.len%=480:     his.name$="PYHIS"
    pay.file%=06:pay.len%=51:      pay.name$="PYPAY"
    pyo.file%=07:pyo.len%=pay.len%:pyo.name$="PYPAY"   rem output
    chk.file%=08:chk.len%=165:     chk.name$="PYCHK"
    ckh.file%=09:ckh.len%=165:     ckh.name$="PYCKH"
    cho.file%=10:cho.len%=ckh.len%:cho.name$="PYCKH"   rem output
    coh.file%=11:                  coh.name$="PYCOH"
    act.file%=12:act.len%=43:      act.name$="PYACT"
    ded.file%=13:                  ded.name$="PYDED"
    pr1.file%=14:                  pr1.name$="PYPR1"
    pr2.file%=15:                  pr2.name$="PYPR2"
    swt.file%=16:                  swt.name$="PYSWT"    rem +STATE$
    lwt.file%=18:                  lwt.name$="PYLWT"
    cal.file%=19:                  cal.name$="PYCAL"    rem +S,M,H,X
    gld.file%=17:gld.len%=51

REM
REM-----------------------
REM----- LOCAL DATA ------
REM-----------------------
REM
submit.file% = 1
end$= chr$(0)+ chr$(24H)

selections% =	     27
default.parameters%= 10
parameter.entry%=    09
user.prog%=	     27
fld.reset.date%= 08
fld.selection%=selections%+ 1
fld.get.date% =selections%+ 2
fld.error%    =selections%+ 3
fld.parent%   =selections%+ 4
lit.co.name%      = 32
lit.common.date%  = lit.co.name%+ 2
lit.select.offset%= lit.co.name%+ 3
lit.user.prog%    = lit.select.offset%+ user.prog%
lit.selection%    = lit.select.offset%+ selections%+ 1
lit.get.date%     = lit.select.offset%+ selections%+ 2
lit.error%        = lit.select.offset%+ selections%+ 3
lit.startup%      = lit.select.offset%+ selections%+ 4
lit.no.pr1%       = lit.select.offset%+ selections%+ 5
lit.no.pr2%       = lit.select.offset%+ selections%+ 6
lit.parent%       = lit.select.offset%+ selections%+ 7

dim module$(selections%), exception%(selections%)
module$(01)="hrsent"                            rem these tables are
module$(02)="hrsproof"                          rem in arbitrary program
module$(03)="pyhours"   : exception%(03)= 1     rem number order. the
module$(04)="apply1"                            rem module table contains
module$(05)="pyjourn"                           rem program module names
module$(06)="pychecks"                          rem for chaining purposes
module$(07)="pyrgstr"                           rem the exception table
module$(08)=""                                  rem contains the number
module$(09)="pyparent"                          rem to be used in an on gosub
module$(10)="pyparent"  : exception%(10)= 2
module$(11)="pyactent"                          rem for any exception procesing
module$(12)="dedent"                            rem sorts are such an exception
module$(13)="pysrtprm"
module$(14)="pyupdhis"
module$(15)="print941"
module$(16)="pyperend"  : exception%(16)= 3
module$(17)="printw2"
module$(18)="print940"
module$(19)="pyperend"  : exception%(19)= 4
module$(20)="empprint"
module$(21)="hisprint"
module$(22)="vacprint"
module$(23)="pyactprt"
module$(24)="empent"
module$(25)="empdent"
module$(26)="ratent"
module$(27)=""

dim emsg$(20)
emsg$(01)="PY101  ONE OF THE TWO PARAMETER ENTRY OPTIONS MUST BE SELECTED"
emsg$(02)="PY102  DMS ERROR"
emsg$(03)="PY103  ERROR DURING CHAIN TO SORT"
emsg$(04)="PY104  ERROR DURING CHAIN TO SORT"
emsg$(05)="PY105  THE PROGRAM IS NOT ON THE CURRENTLY LOGGED DISK"
emsg$(06)="PY106  THE SORT PARAMETER FILE IS NOT ON THE SYSTEM DISK"
emsg$(07)="PY107  UNABLE TO OPEN PARAMETER FILE"
emsg$(08)="PY108"
emsg$(09)="PY109  YES, NO  AND STOP ARE THE ONLY ACCEPTABLE ENTRIES"
emsg$(10)="PY110  INVALID SECOND PARAMETER FILE"
emsg$(11)="PY111  QSORT IS NOT ON THE CURRENTLY LOGGED DISK"
emsg$(12)="PY112  THAT'S NOT A VALID RESPONSE"
emsg$(13)="PY113"
emsg$(14)="PY114  THE SYSTEM DRIVE HAS NOT BEEN INITIALIZED"
emsg$(15)="PY115  INVALID DATE"
emsg$(16)="PY116  INVALID PARAMETER FILE"
emsg$(17)="PY117  OPERATOR REQUESTED RETURN TO MENU"
emsg$(18)="PY118  **ERROR**  THE PROGRAM WAS TERMINATED BEFORE COMPLETION"
emsg$(19)="PY119  THE PARAMETER ENTRY PROGRAM IS NOT ON THE PROGRAM DISK"
emsg$(20)="IY120"

REM
REM--------------------------------------------------------------------
REM----- PARAMETER DEFAULTS SET UP ONLY IF NOT CHAINED FROM ROOT ------
REM--------------------------------------------------------------------
REM
def fn.set.up.pr1.defaults%
    pr1.max.chk.cats%=16
    pr1.max.dist.accts%=5
    pr1.max.sys.eds%=5
    pr1.max.emp.eds%=3
    pr1.max.ed.cats%=50
    pr1.void.check.amt=5000.00
    pr1.max.swt.entries%=15
    pr1.date.mo%=1:pr1.date.dy%=2:pr1.date.yr%=3
    pr1.lo.ded.chk.cat%=9
    pr1.hi.ded.chk.cat%=16
    pr1.lo.earn.chk.cat%=2
    pr1.hi.earn.chk.cat%=7
    pr1.console.width.poke.addr%= 272
    pr1.leading.crlf%= true%
RETURN
fend

REM
REM---------------------------------------------------------------
REM----- DMS CONSTANTS SET UP ONLY IF NOT CHAINED FROM ROOT ------
REM---------------------------------------------------------------
REM
def fn.set.up.dms.constants%

REM #include "zdmscnst"
REM	DEC.  28, 1979	    --------------------------------------------
REM
REM    EQUATES NECESSARY FOR THE DMS SYSTEM (EXCLUDING CRT CHARACTERISTICS)
REM    STANDARD
REM-----------------------------------------------------------------------
%nolist
req.valid%=1:   req.stopit%=2:	  req.cr%=3:     req.back%=4:    req.cancel%=5
req.next%= 6:   req.save%=  7:    req.adding%=8: req.delete%=9
asc.lspace%=8:	asc.refresh%= 18: asc.cr%=13:    asc.del%= 127:  asc.quote%= 34

ctl.stopit$= chr$(27):	 ctl.cr$= chr$(13):    ctl.back$= chr$(2)
ctl.cancel$= chr$(24):	 ctl.next$= chr$(14):  ctl.save$= chr$(19)
ctl.adding$= chr$(1) :	 ctl.delete$=chr$(4)
crt.ctl.tbl$= ctl.stopit$+ctl.cr$+ctl.back$+ctl.cancel$+ctl.next$+ \
	      ctl.save$+ctl.adding$+ctl.delete$
dim crt.ctl.mask$(6)
crt.ctl.mask$(1)= ctl.stopit$
crt.ctl.mask$(2)= crt.ctl.mask$(1)+ctl.cr$+ctl.back$
crt.ctl.mask$(3)= crt.ctl.mask$(2)+ctl.cancel$
crt.ctl.mask$(4)= crt.ctl.mask$(2)+ctl.next$+ctl.save$+ctl.adding$
crt.ctl.mask$(5)= crt.ctl.mask$(4)+ctl.delete$
crt.ctl.mask$(6)= crt.ctl.mask$(2)+ctl.next$

crt.strnum%=1: crt.brktsgn%=2: crt.used%= 4:
crt.brt%=   8: crt.io%=     16

dim crt.sgn.fmt$(7)
crt.sgn.fmt$(1)= "#"
crt.sgn.fmt$(2)= "##"
crt.sgn.fmt$(3)= "###"
crt.sgn.fmt$(4)= "#,###"
crt.sgn.fmt$(5)= "##,###"
crt.sgn.fmt$(6)= "###,###"
crt.sgn.fmt$(7)= "#,###,###"

dim crt.brkt.fmt$(7)		    ,crt.pad.fmt$(7)
crt.brkt.fmt$(1)= "<#"              :crt.pad.fmt$(1)= " #"
crt.brkt.fmt$(2)= "<##"             :crt.pad.fmt$(2)= " ##"
crt.brkt.fmt$(3)= "<###"            :crt.pad.fmt$(3)= " ###"
crt.brkt.fmt$(4)= "<#,###"          :crt.pad.fmt$(4)= " #,###"
crt.brkt.fmt$(5)= "<##,###"         :crt.pad.fmt$(5)= " ##,###"
crt.brkt.fmt$(6)= "<###,###"        :crt.pad.fmt$(6)= " ###,###"
crt.brkt.fmt$(7)= "<#,###,###"      :crt.pad.fmt$(7)= " #,###,###"

dim crt.sgn.rd.fmt$(4)
crt.sgn.rd.fmt$(1)=".#"
crt.sgn.rd.fmt$(2)=".##"
crt.sgn.rd.fmt$(3)=".###"
crt.sgn.rd.fmt$(4)=".####"

dim crt.brkt.rd.fmt$(4),	crt.pad.rd.fmt$(4)
crt.brkt.rd.fmt$(1)=".#>"       :crt.pad.rd.fmt$(1)=".# "
crt.brkt.rd.fmt$(2)=".##>"      :crt.pad.rd.fmt$(2)=".## "
crt.brkt.rd.fmt$(3)=".###>"     :crt.pad.rd.fmt$(3)=".### "
crt.brkt.rd.fmt$(4)=".####>"    :crt.pad.rd.fmt$(4)=".#### "

crt.order.row.col% = -1
crt.order.col.row% = 0
crt.sca.decimal% = 1
crt.sca.hex% = 0
crt.file% = 20
rem-----------------------------
%list


RETURN
fend


Rem SKIP THIS
REM
REM-------------------------
REM----- SERIAL NUMBER -----
REM-------------------------
REM #include "zserial"
rem	  June 22, 1979
%nolist
sum.sum=0
sum.x%=1
while sum.x%<=len(cpyrght$)
	sum.sum=sum.sum+asc(mid$(cpyrght$,sum.x%,1))
	sum.x%=sum.x%+1
wend
if sum.sum<>pumpkin then \
	print bell$;tab(5);system$+"044 INVALID COMMAND SEQUENCE" :\
	stop
serial.number=(0fh and asc(mid$(dummy$,6,1)))
serial.number=serial.number+(0fh and asc(mid$(dummy$,5,1)))*16.0
serial.number=serial.number+(0fh and asc(mid$(dummy$,4,1)))*256.0
serial.number=serial.number+(0fh and asc(mid$(dummy$,3,1)))*4096.0
serial.number$=str$(serial.number)+chr$(asc(mid$(dummy$,7,1))+040h)+  \
				   chr$(asc(mid$(dummy$,8,1))+040h)+  \
				   chr$(asc(mid$(dummy$,9,1))+040h)
if chained% and common.serial.number$<>serial.number$ then \
	print bell$;tab(5);system$+"045 INVALID COMMAND SEQUENCE" :\
	stop
common.serial.number$=serial.number$
%list


REM
REM-----------------------------------------
REM----- INCLUDED FUNCTION DEFINITIONS -----
REM-----------------------------------------
REM
REM #include "zfilconv"
rem 22-oct-79 CPM FILE NAME FUNCTIONS
	def fn.drive.in%(temp$)
		fn.drive.in% = -1
		if len(temp$) <> 1 then return
		temp$=ucase$(temp$)
		if temp$ <> "@" and     \
		   (temp$ > "D" or temp$ < "A")\
			then return
		if temp$ = "@"          \
			then fn.drive.in% = 0	\
			else fn.drive.in% = asc(temp$) - asc("A") + 1
		return
	fend
	def fn.drive.out$(temp%)
		if temp% = 0	\
			then fn.drive.out$ = "@"        \
			else fn.drive.out$ = chr$(asc("A") + temp% - 1)
		return
	fend
	def fn.file.name.out$(c.name$,c.type$,c.drive%,c.password$,c.params$)=\
		fn.drive.out$(c.drive%)+":"+c.name$+"."+c.type$

REM #include "znumber"
rem	Jan. 13, 1979
def fn.num%(no$)
	if match(left$(pound$,len(no$)),no$,1)<>1 and len(no$)>0 \
		then   fn.num%=false% \
		else   fn.num%=true%
	return
fend


REM #include "zparse"
rem	Feb. 28, 1979
def fn.parse%(data$,delim$)
	goto .0071
.700	rem-----dim.1------------------------------
	dim.1%=true%
	if token.limit%=0 then token.limit%=5
	dim token$(token.limit%)
	return
.0071	if not dim.1% then gosub .700
	tok%=1:eos%=false%:posit%=1
	while not eos% and tok%<=token.limit%
		delim%=match(delim$,data$,posit%)
		if delim%=0 \
			then eos%=true% :\
			     token$(tok%)=mid$(data$,posit%,255) \
			else token$(tok%)=mid$(data$,posit%,delim%-posit%) :\
			     tok%=tok%+1 :\
			     posit%=delim%+1
	wend
	fn.parse%=tok%
	return
fend

REM #include "zstring"
rem	 Nov. 13, 1978
def fn.center%(a$,w%)=int%((w%-len(a$))/2)
def fn.pad$(a$,q%)=left$(a$+blank$,q%)
def fn.spread$(a$,q%)
	temp$=null$
	pad$=left$(blank$,q%)
	i%=1
	while i%<=len(a$)
		if mid$(a$,i%,1)=" " then temp$=temp$+pad$
		temp$=temp$+mid$(a$,i%,1)+pad$
		i%=i%+1
	wend
	fn.spread$=temp$
	return
fend

REM #include "zdateio"
rem	  May  10, 1979
def fn.date.in$=right$("00"+str$(yr%),2)+right$("00"+str$(mo%),2)+ \
	      right$("00"+str$(dy%),2)
dim out.date$(3)
def fn.date.out$(date$)
	out.date$(pr1.date.mo%)=mid$(date$,3,2)
	out.date$(pr1.date.dy%)=mid$(date$,5,2)
	out.date$(pr1.date.yr%)=mid$(date$,1,2)
	fn.date.out$=out.date$(1)+"/"+out.date$(2)+"/"+out.date$(3)
	return
fend

REM #include "zeditdte"
rem	  May  10, 1979
rem requires: zparse, znum
def fn.leap.year%(year%)
	if (year%/4.0)-int%(year%/4.0)=0 \
		then   fn.leap.year%=true% \
		else   fn.leap.year%=false%
	return
fend

def fn.edit.date%(date$)			rem parameter file date
	fn.edit.date%=false%			rem information must be
	if fn.parse%(date$,"/")<>3 then return  rem initialized for this
	for xx2%=1 to 3 				rem function to
	  if not fn.num%(token$(xx2%)) then return	rem work
	next xx2%					rem correctly
	mo%=val(token$(pr1.date.mo%))
	dy%=val(token$(pr1.date.dy%))
	yr%=val(token$(pr1.date.yr%))
	if mo%<1 or mo%>12 or \
	   dy%<1 or dy%>31 or \
	   yr%<1 or yr%>99 then return
	if (mo%=4 or mo%=6 or mo%=9 or mo%=11) and dy%>30 then return
	if mo%=2 and not fn.leap.year%(yr%) and dy%>28 then return
	if mo%=2 and fn.leap.year%(yr%) and dy%>29 then return
	fn.edit.date%=true%
	return
fend

REM #include "zsysdriv"
rem	  Nov. 06, 1979
def fn.get.sys.drive%
    if size(fn.file.name.out$(system$+"PR1","101", 1,password$,params$))<> 0\
	then fn.get.sys.drive%=1: RETURN
    if size(fn.file.name.out$(system$+"PR1","101", 2,password$,params$))<> 0\
	then fn.get.sys.drive%=2: RETURN
    fn.get.sys.drive%= -1: RETURN
fend


REM----- DMS FUNCTION DEFINITIONS ------
REM #include "zdmssca"
rem----- NOV.  1,1979 --------------------------------------------------------
rem
rem	fn.crt.sca$		REM STANDARD
rem
rem-------------------------------------------------------------------------
%nolist
   def fn.crt.sca.row$(row%)
	if crt.sca.format% = crt.sca.hex%	\
	  then	fn.crt.sca.row$ \
			= crt.sca.row$	\
				+ chr$(crt.row.xlate%(row%)) \
	  else	fn.crt.sca.row$ \
			= crt.sca.row$	\
				+ str$(crt.row.xlate%(row%))
	return
	fend
   def fn.crt.sca.column$(column%)
	if crt.sca.format% = crt.sca.hex%	\
	  then	fn.crt.sca.column$ \
			= crt.sca.column$	\
			+ chr$(crt.column.xlate%(column%)) \
	  else	fn.crt.sca.column$ \
			= crt.sca.column$	\
				+ str$(crt.column.xlate%(column%))
	return
	fend
   def fn.crt.sca$(row%,column%)
	if crt.sca.order% = crt.order.row.col%	\
	  then	fn.crt.sca$ = crt.sca$		\
				+ fn.crt.sca.row$(row%) \
				+ fn.crt.sca.column$(column%)	\
	  else	fn.crt.sca$ = crt.sca$		\
				+ fn.crt.sca.column$(column%)	\
				+ fn.crt.sca.row$(row%)
	return
	fend
%list
rem--------------------------------------------------------------

REM #include "zdmsinit"
rem	DEC. 02, 1979	  -----------------------------------------------------
rem
rem	fn.crt.cmdstr$
rem	fn.crt.initialize%(file$, disk$)
rem
rem----------------------------------------------------------------------------
%nolist
   def	fn.crt.cmdstr$
	if crt.temp$ = ""       \
	  then	fn.crt.cmdstr$ = "" :   \
		return
	crt.str$ = ""
	for crt.loop% = 1 to len (crt.temp$)
		crt.str$ = crt.str$	\
				+ chr$( asc(mid$(crt.temp$,crt.loop%,1)) \
					and 7fh)
		next
	fn.crt.cmdstr$ = crt.str$
	return
	fend

rem
rem----------------------------------------------------------------------------
rem
rem	fn.crt.initialize%	Initialize CRT display management interface
rem
rem----------------------------------------------------------------------------
rem
   def fn.crt.initialize% (crt.def.file$,crt.disk$)
	fn.crt.initialize% = 0
rem
rem---------------------------------------------------------------------------
rem
rem	CRT characteristics definition of a Hazeltine 1500 CRT terminal
rem
rem---------------------------------------------------------------------------
rem
	crt.leadin$ = chr$(126)
	crt.sca$ = crt.leadin$+chr$(17) 	rem set cursor address
	crt.sca.row$ = ""
	crt.sca.column$ = ""
	crt.sca.format% = crt.sca.hex%
	crt.sca.order% = crt.order.col.row%
	crt.clear$ = crt.leadin$ + chr$(28)	rem	clear screen
	crt.clear.foreground$ = crt.leadin$+chr$(29)	rem clear foreground
	crt.foreground$ = crt.leadin$+chr$(31)		rem begin foreground data
	crt.background$ = crt.leadin$+chr$(25)		rem begin background data
	crt.home$ = crt.leadin$+chr$(18)			rem home cursor
	crt.up.cursor$ = crt.leadin$+chr$(12)		rem up one row
	crt.down.cursor$ = crt.leadin$+chr$(11) 	rem down one row
	crt.right.cursor$ = chr$(16)			rem right one column
	crt.left.cursor$ = chr$(8)			rem left one column
	crt.backspace$ = chr$(8)+" "+chr$(8)            rem destructive backspace
	crt.alarm$ = chr$(7)				rem console alarm
	crt.eol$ = crt.leadin$+chr$(15)
	crt.eos$ = crt.leadin$+chr$(24)
	crt.delete.line$ = crt.leadin$+chr$(19)
	crt.insert.line$ = crt.leadin$+chr$(26)
rem
	crt.columns% = 80
	dim crt.column.xlate%(crt.columns%)
	for crt.loop% = 1 to 31
		crt.column.xlate%(crt.loop%) = 95 + crt.loop%
		next
	for crt.loop% = 32 to 80
		crt.column.xlate%(crt.loop%) = crt.loop% - 1
		next
rem
	crt.rows% = 24
	dim crt.row.xlate%(crt.rows%)
	for crt.loop% = 1 to crt.rows%
		crt.row.xlate% (crt.loop%) = 95 + crt.loop%
		next
	crt.msg.header$ = fn.crt.sca$(crt.rows%,10) + crt.background$
	crt.msg.trailer$ = fn.crt.sca$(crt.rows%-1,1)
	dim crt.mult.backspaces$(2)
	crt.mult.backspaces$(0)=""
	crt.mult.backspaces$(1)=crt.backspace$
	crt.mult.backspaces$(2)=crt.backspace$+crt.backspace$
		for crt.loop%=0 to 31
			crt.ctl.xlate$=crt.ctl.xlate$+chr$(crt.loop%)
			next
		for crt.loop%=0 to 31
			crt.back.count$=crt.back.count$+chr$(0)
			next
		for crt.loop%=32 to 127
			crt.back.count$=crt.back.count$+chr$(1)
			next
		crt.key.prefix%=-1
	if crt.def.file$ = ""   \
	  then	fn.crt.initialize% = 0 :	\
		return	\
	  else	crt.file$ = crt.def.file$ + ".def"
	if crt.disk$ <> ""      \
	  then	crt.file$ = crt.disk$ + ":" + crt.file$
	if end #crt.file%	\
	  then	50000.1
	open crt.file$ as crt.file%
	if end #crt.file%	\
	  then	50000.2
read #crt.file%;line crt.temp$
crt.sca$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.sca.row$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.sca.column$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.clear$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.foreground$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.background$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.clear.foreground$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.home.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.up.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.down.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.right.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.left.cursor$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.backspace$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.alarm$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.eol$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.eos$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.insert.line$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.delete.line$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.init.io.port.data$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
crt.init.console.data$=fn.crt.cmdstr$
	read #crt.file%;crt.sca.order%
	read #crt.file%;crt.sca.format%
	read #crt.file%;			\
		crt.rows%,		\
		crt.columns%
	dim crt.row.xlate%(crt.rows%)
	dim crt.column.xlate%(crt.columns%)
	for crt.loop% = 1 to crt.rows%
		read #crt.file%;crt.row.xlate%(crt.loop%)
		next
	for crt.loop% = 1 to crt.columns%
		read #crt.file%;crt.column.xlate%(crt.loop%)
		next
	read #crt.file%;		\
		crt.init.storage.count%,	\
		crt.init.subroutine.addr,	\
		crt.init.io.port%
	if crt.init.storage.count% > 0	\
	  then	for crt.loop% = 1 to crt.init.storage.count% :	\
		   read #crt.file%;	\
				crt.init.storage.addr,	\
				crt.init.storage.value% :	\
		   poke crt.init.storage.addr,crt.init.storage.value%
		   next
	crt.len% = len(crt.init.io.port.data$)
	if crt.len% > 0 \
	  then	for crt.loop% = 1 to crt.len%	:	\
		   out crt.init.io.port%,		\
			asc(mid$(crt.init.io.port.data$,crt.loop%,1)) : \
		   next
	if crt.init.console.data$ <> "" \
	  then	console :	\
		print using "&";crt.init.console.data$
read #crt.file%;line crt.trash$
	if end #crt.file%  then  50000.0
read #crt.file%;line crt.temp$
	crt.ctl.xlate$=fn.crt.cmdstr$
	if end #crt.file%  then  50000.2
read #crt.file%;line crt.temp$
	crt.back.count$=fn.crt.cmdstr$
read #crt.file%;line crt.temp$
	crt.key.xlate$=fn.crt.cmdstr$
	read #crt.file%; crt.key.prefix%
50000.0 \
	close crt.file%
	crt.msg.header$ = fn.crt.sca$(crt.rows%,10) + crt.background$
	crt.msg.trailer$ = fn.crt.sca$(crt.rows%-1,1)
	crt.mult.backspaces$(0)=""
	crt.mult.backspaces$(1)=crt.backspace$
	crt.mult.backspaces$(2)=crt.backspace$+crt.backspace$
	return
50000.1 \
	fn.crt.initialize% = 1
	return
50000.2 \
	fn.crt.initialize% = 2
	close crt.file%
	return
	fend
%list

REM #include "zdmsmsg"
rem	DEC. 02, 1979		    ---------------------------------------
rem
rem	fn.msg%(text$)		REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
rem
   def fn.msg%(text$)
	crt.msg.issued%= true%
	print using "&"; crt.msg.header$                \
			+ left$ (text$+blank$, crt.columns%-15) \
			+ crt.msg.trailer$
	return
fend
%list

REM #include "zdmsemsg"
rem	 NOV.  1,1979	       -----------------------------------------------
rem
rem	fn.emsg%(emsg%) 	REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
   def fn.emsg%(emsg%)
	trash%= fn.msg%(bell$+emsg$(emsg%))
	common.msg$=emsg$(emsg%)
	return
fend
%list

REM #include "zdmslit"
rem	Nov.  8, 1979	   ------------------------------------------
rem
rem	  fn.lit%(id%)
rem
rem------------------------------------------------------------------
%nolist
def fn.lit%(id%)
	if crt.brt% and crt.attrib%(id%) \
		then print using "&";crt.foreground$;
	print using "&";fn.crt.sca$(crt.y%(id%), crt.x%(id%)); \
		crt.data$(id%); crt.background$
	crt.attrib%(id%)= crt.attrib%(id%) or crt.used%
	return
fend
%list

REM #include "zdmsput"
rem    DEC. 02, 1979   --------------------------------------------------
rem
   def fn.put%(value$,id%)	REM STANDARD
rem
rem----------------------------------------------------------------------
%nolist
	crt.data$(id%)= value$
	print using "&";fn.crt.sca$(crt.y%(id%), crt.x%(id%));
	crt.attrib%(id%)= crt.attrib%(id%) or crt.used%
	if crt.brt% and crt.attrib%(id%) \
		then print using "&";crt.foreground$;
	if (crt.strnum% and crt.attrib%(id%)) or (crt.io% and crt.attrib%(id%))=0 \
		then print using "&";left$(value$+blank$, crt.len%(id%)); \
			crt.background$: RETURN
	if crt.brktsgn% and crt.attrib%(id%) \
		then gosub 50005.1 \
		else gosub 50005.2
	print using "&";crt.background$
	return
50005.1 \	monetary data
	crt.num = val(value$)
	crt.l.d%=len(str$(abs(int(crt.num))))
	crt.temp%= len(crt.brkt.fmt$(crt.len%(id%)))+ \
		len(crt.brkt.rd.fmt$(crt.rd%(id%)))
	if crt.num < 0	\
	    then print using right$(blank$+crt.brkt.fmt$(crt.l.d%)+ \
		crt.brkt.rd.fmt$(crt.rd%(id%)), crt.temp%);abs(crt.num) \
	    else print using right$(blank$+crt.pad.fmt$(crt.l.d%)+ \
		crt.pad.rd.fmt$(crt.rd%(id%)), crt.temp%); crt.num
	return

50005.2
	print using crt.sgn.fmt$(crt.len%(id%))+crt.sgn.rd.fmt$(crt.rd%(id%));\
		val(value$)
	return
fend
%list

REM #include "zdmsptal"
rem	NOV. 13, 1979	       ----------------------------------------------
rem
rem	fn.put.all%(i.o%)	REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
def fn.put.all%(i.o%)
    console
    print using "&";crt.clear$;crt.background$
    for crt.f%= 1 to crt.field.count%
      if (crt.attrib%(crt.f%) and crt.io%)= 0 and (crt.attrib%(crt.f%) and crt.used%) \
	then trash%= fn.lit%(crt.f%)
    next
    if not i.o% then RETURN
    for crt.f%= 1 to crt.field.count%
      if (crt.attrib%(crt.f%) and crt.io%)<> 0 and (crt.attrib%(crt.f%) and crt.used%) \
	then trash%= fn.put%(crt.data$(crt.f%), crt.f%)
    next
   RETURN
fend
%list
rem---------------------------------------------------------------------------

REM #include "zdmsget"
rem----- DEC. 28, 1979 --------------------------------------------------------
rem
rem	fn.get%(mask%, id%)		REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
   def fn.get%(mask%, id%)
	console
	if crt.rd%(id%)> 0 \
		then crt.limit%=crt.len%(id%)+crt.rd%(id%)+1 \
		else crt.limit%=crt.len%(id%)
	print using "&";        \
		fn.crt.sca$(crt.y%(id%),crt.x%(id%));crt.foreground$;
	if pr1.leading.crlf% then print
	in$=null$
	in.uc$=null$
	in.status%= 0
	in.len%= 0
	crt.done%=false%
	crt.valid.control%=0
	while not crt.done%
		crt.print%= false%
		crt.data% = conchar%
		crt.temp.back% = asc(mid$(crt.back.count$, crt.data%+1, 1))
		if crt.data% < 32  then \
			crt.data% = asc(mid$(crt.ctl.xlate$, crt.data%+1, 1))
		if crt.key%  then \
			crt.data% = asc(mid$(crt.key.xlate$, crt.data%+1, 1))
		if crt.data% = crt.key.prefix%	and not crt.key% \
			then  crt.key% = true% \
			else  crt.key% = false%
		if crt.temp.back% <> 0 and (crt.key% or crt.data% < 32) \
			then crt.print%= true%: \
				print using "&";fn.crt.sca$(crt.y%(id%), \
				crt.x%(id%)+crt.loop%+crt.temp.back%); \
				crt.mult.backspaces$(crt.temp.back%);
		if crt.data% = asc.del% \
			then crt.data% = asc.lspace%
		if crt.data%= asc.lspace% and in.len%> 0 \
			then crt.print%= true%: \
			  print using "&"; fn.crt.sca$(crt.y%(id%), \
			  crt.x%(id%)+in.len%);crt.backspace$; :\
			  in.len%= in.len% - 1: in$= left$(in$,in.len%)
		if crt.data%= asc.refresh% \
			then crt.print%= true%: trash%=fn.put.all%(true%): \
			  print using "&"; \
			  fn.crt.sca$(crt.y%(id%),crt.x%(id%)); \
			  crt.foreground$; : in.len%=0: in$=null$
		if crt.data%< 32 and crt.data%<> asc.lspace% and \
			crt.data%<> asc.refresh% and in.len%= 0 \
		  then crt.valid.control%= match(chr$(crt.data%), \
			crt.ctl.mask$(mask%), 1)
		if (crt.data%=asc.cr% and in.len%<>0) or crt.valid.control%<>0\
			then crt.done%=true%
		if not crt.done% and crt.data%< 32 and crt.data%<>asc.lspace% \
		  and crt.data%<> asc.refresh% and crt.valid.control%= 0\
			then crt.print%= true%: trash%= fn.msg% \
			(bell$+system$+"016 CONTROL CHARACTER NOT ACCEPTED"): \
			print using "&"; \
			fn.crt.sca$(crt.y%(id%), crt.x%(id%)+in.len%); \
			crt.foreground$;
		if crt.data% <> asc.cr% and crt.data% <> asc.lspace% and \
		  in.len% >= crt.limit% \
			then crt.print%= true%: trash%= fn.msg% \
			(bell$+system$+"017  LENGTH LIMIT EXCEEDED"): \
			print using "&"; \
			fn.crt.sca$(crt.y%(id%),crt.x%(id%)+in.len%+1); \
			crt.backspace$;crt.foreground$;
		if crt.data% = asc.quote% \
			then crt.print%= true%: trash%= fn.msg% \
			(bell$+system$+"018  QUOTES ARE INVALID CHARACTERS"): \
			print using "&"; \
			fn.crt.sca$(crt.y%(id%),crt.x%(id%)+in.len%+1); \
			crt.backspace$;crt.foreground$;
		if crt.data%>= 32 and crt.data%<> asc.quote% and \
		  not crt.key% and in.len%< crt.limit% \
			then in$= in$+ chr$(crt.data%): in.len%= in.len%+ 1
		if pr1.leading.crlf% and crt.print% then print
	wend
	in.status%= match(chr$(crt.data%), crt.ctl.tbl$, 1)+ 1
	if in.len% > 0 \
	  then	in.uc$= ucase$(in$): in.status%= req.valid%
	if crt.msg.issued% then trash%= fn.msg%(""): crt.msg.issued%= false%\
			   else print using"&";crt.background$;
	return
	fend
rem--------------------------------------------------------------
%list

REM #include "zdmsclr"
rem	Nov. 18, 1979	   ---------------------------------------------------
rem
rem	fn.clr%(id%)
rem
rem---------------------------------------------------------------------------
%nolist
   def fn.clr%(id%)
	console
	if crt.attrib%(id%) and crt.io% \
		then crt.data$(id%)= null$
	crt.attrib%(id%)= crt.attrib%(id%) and not crt.used%
	print using "&"; \
	    fn.crt.sca$(crt.y%(id%), crt.x%(id%));
	if (crt.strnum% and crt.attrib%(id%)) or (crt.io% and crt.attrib%(id%))=0 \
		then print using "&";left$(blank$, crt.len%(id%)): RETURN
	if crt.brktsgn% and crt.attrib%(id%) \
	    then crt.temp%= len(crt.brkt.fmt$(crt.len%(id%)))+ \
		len(crt.brkt.rd.fmt$(crt.rd%(id%))) \
	    else crt.temp%= len(crt.sgn.fmt$(crt.len%(id%)))+ \
		len(crt.sgn.rd.fmt$(crt.rd%(id%)))
	print using "&";left$(blank$, crt.temp%)
	return
	fend
rem--------------------------------------------------------------------------
%list

REM #include "zdmsused"
rem	NOV.  1, 1979	   -------------------------------------
rem
rem	fn.set.brt%(t.f%, id%)		REM STANDARD
rem
rem-------------------------------------------------------------
%nolist
def fn.set.brt%(t.f%, id%)
	crt.attrib%(id%)= crt.attrib%(id%) and not crt.brt%
	crt.attrib%(id%)= crt.attrib%(id%) or  (crt.brt% and t.f%)
	return
fend
%list

REM #include "zdmsbrt"
rem	NOV.  1, 1979	   -------------------------------------
rem
rem	fn.set.brt%(t.f%, id%)		REM STANDARD
rem
rem-------------------------------------------------------------
%nolist
def fn.set.brt%(t.f%, id%)
	crt.attrib%(id%)= crt.attrib%(id%) and not crt.brt%
	crt.attrib%(id%)= crt.attrib%(id%) or  (crt.brt% and t.f%)
	return
fend
%list


REM
REM---------------------------------------
REM----- LOCAL FUNCTION DEFINITIONS  -----
REM---------------------------------------
def fn.get.pr2.drive%
	if size(fn.file.name.out$(system$+"PR2","101",1,password$,params$)) \
		then fn.get.pr2.drive%= 1 :RETURN
	if size(fn.file.name.out$(system$+"PR2","101",2,password$,params$)) \
		then fn.get.pr2.drive%= 2 :RETURN
	fn.get.pr2.drive%=-1 :RETURN
fend

REM
REM------------------------------------------
REM----- PROGRAM EXECUTION STARTS HERE ------
REM------------------------------------------
REM
while not chained.from.root% and not once.thru%
	REM---------------------------------------------------------------
	REM----- THIS IS THE FIRST OF TWO BLOCKS OF CODE WHICH WILL  -----
	REM----- BE EXECUTED EXACTLY ONCE IF NOT CHAINED FROM ROOT.  -----
	REM----- THIS BLOCK INITIALIZES THE DMS SYSTEM AND READS THE -----
	REM----- TWO PARAMETER FILES IF PRESENT.		     -----
	REM---------------------------------------------------------------
	print:print:print
	print tab(15);system.name$;version$;"     SERIAL NUMBER: ";serial.number$
	print
	print tab(10);cpyrght$
	print:print
	trash%= fn.set.up.dms.constants%
	trash%= fn.set.up.pr1.defaults%
	crt.init%=fn.crt.initialize%("CRT", null$)
	if crt.init% = 2 \
		then trash%=fn.emsg%(02): goto 999.1
	REM----- GET PR1 FILE, SET COMMON DRIVE ------
	gosub 101
	REM----- GET PR2 FILE, SET PR2 DRIVE IF NO PR2 ------
	gosub 102
	if error% then trash%= fn.emsg%(msg%): goto 999.1

	if pr1.leading.crlf% then poke pr1.console.width.poke.addr%, 255 \
			     else poke pr1.console.width.poke.addr%, 0

	if pr1.bell.suppressed% then bell$=null$ \
				else bell$=chr$(7)

	if fn.edit.date%(command$) \
		then common.date$=fn.date.in$

	once.thru%= true%
wend

REM
REM-------------------------------------------
REM----- INCLUDE SCREEN DEFINITION CODE ------
REM-------------------------------------------
REM

REM #include "fpymenu"
rem---------------------------------------------------------
rem	SET UP DMS SCREEN EQUATES    FPYMENU - 12/14/79

crt.field.count% = 69	    rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem	LEGEND:    X  Y  LEN  RD  ATTRIB
rem	    STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data		   \
	  6,5,1,0,25,\	     rem   IO fld #1
	  6,6,1,0,25,\	     rem   IO fld #2
	  6,7,1,0,25,\	     rem   IO fld #3
	  6,8,1,0,25,\	     rem   IO fld #4
	  6,9,1,0,25,\	     rem   IO fld #5
	  6,10,1,0,25,\       rem   IO fld #6
	  6,11,1,0,25,\       rem   IO fld #7
	  6,12,1,0,25,\       rem   IO fld #8
	  6,14,1,0,25,\       rem   IO fld #9
	  6,15,1,0,25,\       rem   IO fld #10
	  6,16,1,0,25,\       rem   IO fld #11
	  6,17,1,0,25,\       rem   IO fld #12
	  6,18,1,0,25,\       rem   IO fld #13
	  6,19,1,0,25,\       rem   IO fld #14
	  44,5,1,0,25,\       rem   IO fld #15
	  44,6,1,0,25,\       rem   IO fld #16
	  44,7,1,0,25,\       rem   IO fld #17
	  44,8,1,0,25,\       rem   IO fld #18
	  44,9,1,0,25,\       rem   IO fld #19
	  44,11,1,0,25,\       rem   IO fld #20
	  44,12,1,0,25,\       rem   IO fld #21
	  44,13,1,0,25,\       rem   IO fld #22
	  44,14,1,0,25,\       rem   IO fld #23
	  44,16,1,0,25,\       rem   IO fld #24
	  44,17,1,0,25,\       rem   IO fld #25
	  44,18,1,0,25,\       rem   IO fld #26
	  44,19,1,0,25,\       rem   IO fld #27
	  47,21,2,0,25,\       rem   IO fld #28
	  41,21,8,0,25,\       rem   IO fld #29
	  62,22,2,0,25,\       rem   IO fld #30
	  66,22,2,0,25,\       rem   IO fld #31
	  1,1,8,0,4,\	    rem   O fld #32
	  1,2,9,0,4,\	    rem   O fld #33
	  1,3,8,0,4,\	    rem   O fld #34
	  10,3,8,0,4,\	     rem   O fld #35
	  4,5,25,0,4,\	     rem   O fld #36
	  4,6,25,0,4,\	     rem   O fld #37
	  4,7,24,0,4,\	     rem   O fld #38
	  4,8,17,0,4,\	     rem   O fld #39
	  4,9,25,0,4,\	     rem   O fld #40
	  4,10,19,0,4,\       rem   O fld #41
	  4,11,24,0,4,\       rem   O fld #42
	  4,12,19,0,4,\       rem   O fld #43
	  4,14,19,0,4,\       rem   O fld #44
	  3,15,26,0,4,\       rem   O fld #45
	  3,16,18,0,4,\       rem   O fld #46
	  3,17,28,0,4,\       rem   O fld #47
	  3,18,32,0,4,\       rem   O fld #48
	  3,19,18,0,4,\       rem   O fld #49
	  41,5,31,0,4,\       rem   O fld #50
	  41,6,28,0,4,\       rem   O fld #51
	  41,7,20,0,4,\       rem   O fld #52
	  41,8,28,0,4,\       rem   O fld #53
	  41,9,25,0,4,\       rem   O fld #54
	  41,11,31,0,4,\       rem   O fld #55
	  41,12,25,0,4,\       rem   O fld #56
	  41,13,26,0,4,\       rem   O fld #57
	  41,14,23,0,4,\       rem   O fld #58
	  41,16,19,0,4,\       rem   O fld #59
	  41,17,37,0,4,\       rem   O fld #60
	  41,18,28,0,4,\       rem   O fld #61
	  41,19,25,0,0,\       rem   O fld #62
	  21,21,29,0,0,\       rem   O fld #63
	  21,21,29,0,0,\       rem   O fld #64
	  12,22,55,0,0,\       rem   O fld #65
	  9,21,60,0,0,\       rem   O fld #66
	  9,21,56,0,0,\       rem   O fld #67
	  9,21,53,0,0,\       rem   O fld #68
	  9,22,60,0,0
	  rem	O fld #69
crt.data$(36)="1.  PAY TRANSACTION ENTRY"
crt.data$(37)="2.  PAY TRANSACTION PROOF"
crt.data$(38)="3.  PAY TRANSACTION SORT"
crt.data$(39)="4.  APPLY PAYROLL"
crt.data$(40)="5.  PRINT PAYROLL JOURNAL"
crt.data$(41)="6.  PRINT PAYCHECKS"
crt.data$(42)="7.  PRINT CHECK REGISTER"
crt.data$(43)="8.  SET SYSTEM DATE"
crt.data$(44)="9.  PARAMETER ENTRY"
crt.data$(45)="10.  QUICK PARAMETER ENTRY"
crt.data$(46)="11.  ACCOUNT ENTRY"
crt.data$(47)="12.  DEDUCTION/EARNING ENTRY"
crt.data$(48)="13.  CREATE SORT PARAMETER FILES"
crt.data$(49)="14.  HISTORY ENTRY"
crt.data$(50)="15.  PRINT QUARTERLY 941 REPORT"
crt.data$(51)="16.  END THE CURRENT QUARTER"
crt.data$(52)="17.  PRINT W2 REPORT"
crt.data$(53)="18.  PRINT YEARLY 940 REPORT"
crt.data$(54)="19.  END THE CURRENT YEAR"
crt.data$(55)="20.  PRINT EMPLOYEE MASTER LIST"
crt.data$(56)="21.  PRINT HISTORY REPORT"
crt.data$(57)="22.  PRINT VACATION REPORT"
crt.data$(58)="23.  PRINT ACCOUNT LIST"
crt.data$(59)="24.  EMPLOYEE ENTRY"
crt.data$(60)="25.  EMPLOYEE DED/EARN AND COST DIST."
crt.data$(61)="26.  EMPLOYEE PAY RATE ENTRY"
crt.data$(62)="27.  USER DEFINED PROGRAM"
crt.data$(63)="ENTER A SELECTION NUMBER [  ]"
crt.data$(64)="ENTER TODAY'S DATE [        ]"
crt.data$(65)="RECORD THE ERROR MESSAGE NUMBER, THEN TYPE  ""OK"" [  ]"
crt.data$(66)="SYSTEM STARTUP -- IN ORDER TO INITIALIZE THE PAYROLL SYSTEM,"
crt.data$(67)="NO PARAMETER FILE -- A NEW PARAMETER FILE MUST BE BUILT."
crt.data$(68)="NO SECOND PARAMETER FILE -- A NEW FILE MUST BE BUILT."
crt.data$(69)="ONE OF THE TWO PARAMETER ENTRY OPTIONS MUST BE SELECTED [  ]"

i%=1
while i%<=69
  read	crt.x%(i%),crt.y%(i%),\
	crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then	 co.name$=fn.spread$(pr1.co.name$,1)  \
  else	 co.name$=pr1.co.name$
crt.len%(32)=len(co.name$)
crt.x%(32)=fn.center%(co.name$,crt.columns%-2)
crt.data$(32)=co.name$
if len(system.name$)<=30 \
  then	 sys.name$=fn.spread$(system.name$,1)  \
  else	 sys.name$=system.name$
crt.len%(33)=len(sys.name$)
crt.x%(33)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(33)=sys.name$
crt.data$(34)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then	 fun.name$=fn.spread$(function.name$,1)  \
  else	 fun.name$=function.name$
crt.len%(35)=len(fun.name$)
crt.x%(35)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(35)=fun.name$

rem---------------------------------------------------------


REM
REM----------------------------------------
REM----- DISPLAY PAYROLL MENU SCREEN ------
REM----------------------------------------
if pr1.user.program.used% \
	then crt.data$(lit.user.prog%)= "27.  "+pr1.user.prog.desc$: \
	     trash%= fn.set.used%(true%, lit.user.prog%): \
	     module$(user.prog%)=pr1.user.program$

if common.date$= null$ \
	then trash%=fn.set.used%(false%, lit.common.date%)
trash%= fn.put.all%(false%)


while not chained.from.root%
	REM----------------------------------------------------------------
	REM----- CODE EXECUTED EXACTLY ONCE IF NOT CHAINED FROM ROOT ------
	REM----- FORCE PARAMETER ENTRY SELECTION IF EITHER OR BOTH   ------
	REM----- PARAMETER FILES ARE NOT PRESENT.		     ------
	REM----------------------------------------------------------------
	chained.from.root%=true%
	chained%=true%

	if common.drive%= -1 and pr2.drive%= -1 \
		then common.chaining.status$= startup$: \
		     trash%=fn.lit%(lit.startup%): \
		     need.parent%= true%

	if common.drive%= -1 and pr2.drive%<>-1 \
		then common.chaining.status$= rebuild.pr1$: \
		     common.drive%= pr2.drive%: \
		     trash%=fn.lit%(lit.no.pr1%): \
		     need.parent%= true%

	if common.drive%<> -1 and pr2.drive%= -1 \
		then common.chaining.status$= rebuild.pr2$: \
		     trash%=fn.lit%(lit.no.pr2%): \
		     need.parent%= true%
	while need.parent%
		REM------------------------------------------------------
		REM----- ONE OR BOTH PARAMETER FILES ARE MISSING    -----
		REM----- USER MUST CHAIN TO PARAMETER ENTRY OR STOP -----
		REM------------------------------------------------------
		trash%= fn.lit%(lit.parent%)
		chained.program.number%= parameter.entry%
		gosub 60
		chained.program.number%= default.parameters%
		gosub 60
		got%= false%
		while not got%
		    trash%= fn.get%(1, fld.parent%)
		    if in.status%= req.stopit% then 999.2
		    selection%= val(in$)
		    if selection%= parameter.entry% or \
		       selection%= default.parameters% \
			then got%= true%: \
			else trash%= fn.emsg%(01)
		wend
		chain.to$=fn.file.name.out$(module$(selection%),"INT", \
		    cur.log.drive%,password$,param$)
		if size(chain.to$)= 0 \
			then trash%=fn.emsg%(19): goto 999.1
		if selection%= parameter.entry% \
			then chained.program.number%= default.parameters% \
			else chained.program.number%= parameter.entry%
		gosub 65
		chained.program.number%= selection%
		gosub 60
		if selection%= default.parameters% \
			then common.chaining.status$= \
			     common.chaining.status$+ default$
		REM----- EXIT HERE IF PARAMETER ENTRY CALLED ------
		chain chain.to$
	wend
	REM
	REM----- GET COMMON DATE IF NOT ENTERED ON COMMAND LINE ------
	REM
	if common.date$= null$ \
		then gosub 70
	if stopit% then 999.2

wend

REM
REM--------------------------------------------------
REM----- FOLLOWING MENU SET UP, EXECUTION WILL ------
REM----- CONTINUE HERE IF CHAINED FROM ROOT    ------
REM--------------------------------------------------
REM
if chained.program.number% > 0 \
	then  gosub 60			rem display program returned from

REM----- PICK UP AN ERROR RETURN ------
if common.return.code%= 1 \
	then gosub 90		rem get user to record message number

REM
REM-----------------------------------------------
REM----- SET UP FOR NORMAL PROGRAM SELECTION -----
REM-----------------------------------------------
REM
trash%= fn.lit%(lit.selection%)

REM
REM-------------------------------
10 REM----- MAIN DRIVER LOOP -----
REM-------------------------------
while true%
	trash%=fn.clr%(fld.selection%)
	trash%=fn.get%(1, fld.selection%)
	gosub 65		rem clear data
	if in.status%=req.stopit%  then 999	rem end of program

	num%=fn.num%(in$)
	if not num%  then \
		trash%=fn.emsg%(12): goto 10
	selected%=val(in$)
	if selected%= fld.reset.date% \
		then trash%= fn.clr%(lit.selection%): \
		     gosub 70: \		rem get system date
		     trash%= fn.lit%(lit.selection%): \
		     goto  10
	if selected% < 1  or selected% > selections% \
	   or (selected%= user.prog% and not pr1.user.program.used%) \
		then trash%=fn.emsg%(12): goto 10
	that.cant.run%=false%
	common.return.code%=0
	chained.program.number%=selected%
	common.msg$=null$
	common.chaining.status$=normal$
	gosub 60		rem display selection

	REM----- any exception processing takes place here ---------------

	if exception%(chained.program.number%) then \
		on exception%(chained.program.number%)	gosub \
		1001, \ 	--- sort hours batch
		 301,	\	--- set default flag in common
		 302,	\	--- set quarter end flag in common
		 303		rem set year end flag in common

	if that.cant.run%  then \
		trash%=fn.emsg%(msg%): goto 10

	REM----- chain ----------------------------------------
	chain.to$=fn.file.name.out$(module$(chained.program.number%),"INT", \
	0,password$,params$)
	if size(chain.to$)<> 0 then \
		chain chain.to$

	trash%=fn.emsg%(05)
	gosub 65	rem clear data
wend

999    rem-----normal end of job---------------
print using "&";crt.clear$
print:print:print
print tab(10);function.name$+" COMPLETED"
print:print:print
stop
999.1  rem-----abnormal end of job-------------
print:print:print
print tab(10);system.name$+" TERMINATING"
print:print:print:print bell$
stop
999.2  rem-----premature end of job------------
print using "&";crt.clear$
print:print:print
print tab(10);system.name$+" ENDING AT OPERATORS REQUEST"
print:print:print
stop

REM
REM------------------------
REM----- SUBROUTINES ------
REM------------------------
REM
REM---------------------------------
60 REM----- DISLAY A SELECTION -----
REM---------------------------------
trash%=fn.set.brt%(true%, lit.select.offset%+ chained.program.number%)
trash%=fn.lit%(lit.select.offset%+ chained.program.number%)
trash%=fn.put%(">",chained.program.number%)
RETURN
REM
REM-------------------------
65 REM----- CLEAR DATA -----
REM-------------------------
if chained.program.number% > 0 \
  then trash%=fn.set.brt%(false%,lit.select.offset%+chained.program.number%):\
       trash%=fn.lit%(lit.select.offset%+ chained.program.number%): \
       trash%=fn.clr%(chained.program.number%): \
       chained.program.number%= 0
RETURN
REM
REM----------------------------
 70 REM----- SET SYSTEM DATE ------
REM----------------------------
REM
trash%= fn.lit%(lit.get.date%)
ok%= false%
while not ok%
	trash%=fn.get%(1, fld.get.date%)
	if in.status%= req.stopit% then stopit%= true%: ok%= true%
	if in.status%= req.cr% and common.date$<> null$ then ok%= true%
	if in.status%= req.valid% and fn.edit.date%(in$) \
	    then common.date$= fn.date.in$: ok%= true%: \
		 trash%= fn.put%(fn.date.out$(common.date$), lit.common.date%)
	if ok%	then trash%=fn.clr%(lit.get.date%) \
		else trash%= fn.emsg%(15): \
		     trash%= fn.clr%(fld.date%)
wend
RETURN
REM
REM------------------------------------------
90 REM----- GET ERROR CODE CONFIRMATION -----
REM------------------------------------------
read%=false%
trash%=fn.lit%(lit.error%)
while not read%
	if common.msg$=null$ \
		then trash%=fn.emsg%(18) \
		else trash%=fn.msg%(bell$+common.msg$)

	trash%=fn.get%(0, fld.error%)
	if in.uc$="OK" \
		then read%=true%
wend
trash%=fn.clr%(lit.error%)
RETURN

REM
REM-----------------------------------
101 REM----- GET PARAMETER FILE ------
REM-----------------------------------
REM
dim pr1.rate.name$(4)

common.drive%= fn.get.sys.drive%
if common.drive%= -1 then RETURN

trash%= fn.msg%("LOADING FIRST PARAMETER FILE")

if end #pr1.file%  then 101.38	rem no parameter file
open  fn.file.name.out$(system$+"PR1","101",common.drive%,password$,param$) \
	as pr1.file%

if end #pr1.file%  then 101.39	rem invalid parameter file
read #pr1.file%; \
#include "ipypr1"

close pr1.file%
RETURN

101.38 REM------ NO PARAMETER FILE -------------
msg%=07
error%= true%
RETURN

101.39 REM----- INVALID PARAMETER FILE --------------
msg%=16
error%= true%
RETURN

REM
REM-------------------------
 102 REM----- GET PR2 FILE ------
REM-------------------------
REM
if common.drive%= -1 \
	then pr2.drive%= fn.get.pr2.drive% \
	else pr2.drive%= common.drive%

if pr2.drive%= -1 then RETURN

trash%= fn.msg%("LOADING SECOND PARAMETER FILE")

if end #pr2.file%  then 102.28	rem no pr2 file
open  fn.file.name.out$(system$+"PR2","101",pr2.drive%,password$,params$) \
	as pr2.file%
if end #pr2.file%  then 102.29	rem invalid pr2.file
read #pr2.file%; \
REM #include "ipypr2"
common pr2.year%		rem 12/02/79
common pr2.last.sm.apply.no%, pr2.last.wb.apply.no%
common pr2.no.of.sm.applies%, pr2.no.of.wb.applies%
common pr2.hrs.batch.no%
common pr2.last.day.of.last.w$, pr2.last.day.of.last.b$
common pr2.last.day.of.last.s$, pr2.last.day.of.last.m$
common pr2.940.printed%, pr2.941.printed%, pr2.w2.printed%
common pr2.no.acts%
common pr2.no.active.emps%, pr2.no.employees%
common pr2.check.date$
common pr2.last.check.no$
common pr2.last.q.ended%
common pr2.just.closed.year%


close pr2.file%
RETURN

102.28 REM------ NO PR2 FILE BUT PR1 FILE IS PRESENT -------------
pr2.drive%= -1
trash%= fn.msg%("NO SECOND PARAMETER FILE FOUND")
RETURN
102.29 REM----- INVALID PR2 FILE --------------------
msg%=10
error%= true%
RETURN

REM
REM--------------------------------------------
 301 REM----- SET DEFAULT FLAG IN COMMON ------
REM--------------------------------------------
REM
common.chaining.status$= common.chaining.status$+default$
RETURN

REM
REM------------------------------------------------
 302 REM----- SET QUARTER END FLAG IN COMMON ------
REM------------------------------------------------
REM
common.chaining.status$= common.chaining.status$+quarter.end$
RETURN

REM
REM-----------------------------------------------
 303 REM----- SET YEAR END FLAG IN COMMON   ------
REM-----------------------------------------------
REM
common.chaining.status$= common.chaining.status$+year.end$
RETURN


REM
REM-----------------------------------
REM----- SORTS ARE HANDLED HERE ------
REM-----------------------------------
REM
REM---------------------------------------
1001 REM----- SORT HOURS BATCH FILE ------
REM---------------------------------------
sort.param$=module$(chained.program.number%)
gosub 9000		rem should exit thru this subroutine
that.cant.run%=true%
RETURN
REM
REM------------------------------------------------------
9000 REM----- SORTS SHOULD EXIT THRU THIS ROUTINE   -----
REM----- WHICH BUILDS A COMMAND FILE AND STOPS ----------
REM------------------------------------------------------
REM
if size(fn.file.name.out$("QSORT","COM",0,password$,params$))= 0  then \
	msg%=11: RETURN
if size(fn.file.name.out$(sort.param$,"SRT",common.drive%,password$,params$)) \
	= 0  then \
	msg%=06 : RETURN

REM----- CREATE COMMAND FILE -----
if end #submit.file%  then 9090
create fn.file.name.out$("$$$","SUB", 1,password$,params$) \
	recl 80H  as submit.file%
run.menu$ = "CRUN2 "+system$+" " + fn.date.out$(common.date$)

REM----- PRINT TO COMMAND FILE -----
if end #submit.file%  then 9091
print using "&"; #submit.file% ; chr$(len(run.menu$)) + run.menu$ + end$

srt$ = "QSORT " + \
    fn.file.name.out$(sort.param$,"SRT",common.drive%,password$,params$)

print using "&";#submit.file% ; chr$(len(srt$)) + srt$ + end$
close submit.file%
print using "&"; crt.clear$
stop

9090 rem----- here if eof on submit file create -----------------
msg%=03
RETURN
9091 rem----- here if eof on submit file build -----------------
msg%=04
close submit.file%
RETURN
