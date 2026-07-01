Rem $include "ipycomm"
Rem #include zcommon            rem 11/06/79
rem-----SYSTEM COMMONS---11/06/79---------------------------------------
common chained.from.root%     rem T/F true if called from menu
common chained%          rem T/F true if called from anybody
common chained.program.number%     rem 0-99 number of this program
common common.return.code%     rem 0 if ok, else 1,2,etc
common common.msg$         rem error msg for menu to print
common common.chaining.status$     rem genl info, codes are in include
common common.serial.number$     rem serial number, stupid
common common.date$         rem yymmdd   RUN date from menu
common common.drive%         rem internal drive where PR1 and PR2 files are
common true%,false%         rem -1, 0 for logical true, false
common sector.len%,pumpkin     rem  disk sector size, zserial constant
common tof$,quote$,bell$,comma$  rem character strings
common pound$, blank$         rem "#...#" and blanks
rem---------------------------------------------------------------------
Rem #include zdmscomm
REM    Nov.  6, 1979       -----------------------------------------
REM
REM    COMMON AREA FOR DMS VARIABLES (INCLUDING CRT CHARACTERISTICS)
REM    STANDARD
REM-----------------------------------------------------------------
%nolist
common    crt.sca$, crt.sca.row$, crt.sca.column$
common    crt.clear$
common    crt.foreground$, crt.background$, crt.clear.foreground$
common    crt.home.cursor$
common    crt.up.cursor$, crt.down.cursor$, crt.right.cursor$, crt.left.cursor$
common    crt.backspace$
common    crt.alarm$
common    crt.eol$, crt.eos$
common    crt.insert.line$, crt.delete.line$
common    crt.order.row.col%, crt.order.col.row%, crt.sca.order%
common    crt.sca.hex%, crt.sca.decimal%, crt.sca.format%
common    crt.rows%,crt.columns%
common    crt.row.xlate%(1), crt.column.xlate%(1)
common    crt.file%
common    crt.msg.header$, crt.msg.trailer$
common    crt.mult.backspaces$(1), crt.back.count$
common    crt.ctl.xlate$
common    crt.key.prefix%, crt.key.xlate$
common    crt.strnum%, crt.brktsgn%, crt.used%, crt.brt%, crt.io%
common    crt.sgn.fmt$(1),  crt.sgn.rd.fmt$(1)
common    crt.brkt.fmt$(1), crt.brkt.rd.fmt$(1)
common    crt.pad.fmt$(1),  crt.pad.rd.fmt$(1)
common    req.valid%, req.stopit%, req.cr%, req.back%, req.cancel%
common    req.next%, req.save%, req.adding%, req.delete%
common    asc.lspace%, asc.refresh%, asc.cr%, asc.del%
common    ctl.stopit$, ctl.cr$, ctl.back$, ctl.cancel$, ctl.next$
common    ctl.save$, ctl.adding$, ctl.delete$
common    crt.ctl.tbl$
common    crt.ctl.mask$(1)
%list
REM  END OF DMS COMMON    ----------------------------------------
REM
Rem #include ipycfile
rem 11/06/79  -- FILE NUMBERS, LENGTHS, NAMES IN COMMON ------
common hrs.file%, hrs.len%, hrs.name$
common emp.file%, emp.len%, emp.name$
common his.file%, his.len%, his.name$
common pay.file%, pay.len%, pay.name$
common pyo.file%, pyo.len%, pyo.name$
common chk.file%, chk.len%, chk.name$
common ckh.file%, ckh.len%, ckh.name$
common cho.file%, cho.len%, cho.name$
common coh.file%,        coh.name$
common act.file%, act.len%, act.name$
common ded.file%,        ded.name$
common pr1.file%,        pr1.name$
common pr2.file%,        pr2.name$
common swt.file%,        swt.name$
common lwt.file%,        lwt.name$
common cal.file%,        cal.name$
rem----------------------------------------------------------
Rem #include ipycpr1
common pr1.debugging%        rem 12/14/79
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
Rem #include ipycpr2
common pr2.year%        rem 12/02/79
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
Rem $include "ipyapcom"
common interval$        rem NOV. 1, 1979
common extension.intervals$
common from.slow.date$
common from.fast.date$
common to.date$
common week.based%
common month.based%
common apply.no%
prgname$="APPLY3     JAN.  17, 1980 "
rem----------------------------------------------------------
rem
rem    A  P  P  L  Y  3
rem
rem        CREATE CHECK FILE AND UPDATE HIS AND COH FILES
rem
rem    SECTION THREE OF PAYROLL CALCULATION PROGRAM
rem
rem    P A Y R O L L       S Y S T E M
rem
rem    COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="APPLY3"
function.name$="PAYROLL APPLICATION -- SECTION THREE"

Rem $include "ipyconst"
rem     JAN. 18, 1980
system$="PY":version$=" REL:1.0 "
system.name$="PAYROLL SYSTEM"
cpyrght$="COPYRIGHT (C) 1980, APPLEWOOD COMPUTERS "
dummy$="PYppppI00":null$="":asc.quote%= 34
dim crt.data$(0),crt.x%(0),crt.y%(0),crt.len%(0),crt.rd%(0),crt.attrib%(0)
    def fn.drive.out$(temp%)
        if temp% = 0    \
            then fn.drive.out$ = "@"        \
            else fn.drive.out$ = chr$(asc("A") + temp% - 1)
        return
    fend
    def fn.file.name.out$(c.name$,c.type$,c.drive%,c.password$,c.params$)=\
        fn.drive.out$(c.drive%)+":"+c.name$+"."+c.type$

Rem $include "zstring"
rem     Nov. 13, 1978
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

Rem $include "zdmssca"
rem----- NOV.  1,1979 --------------------------------------------------------
rem
rem    fn.crt.sca$        REM STANDARD
rem
rem-------------------------------------------------------------------------
%nolist
   def fn.crt.sca.row$(row%)
    if crt.sca.format% = crt.sca.hex%    \
      then    fn.crt.sca.row$ \
            = crt.sca.row$    \
                + chr$(crt.row.xlate%(row%)) \
      else    fn.crt.sca.row$ \
            = crt.sca.row$    \
                + str$(crt.row.xlate%(row%))
    return
    fend
   def fn.crt.sca.column$(column%)
    if crt.sca.format% = crt.sca.hex%    \
      then    fn.crt.sca.column$ \
            = crt.sca.column$    \
            + chr$(crt.column.xlate%(column%)) \
      else    fn.crt.sca.column$ \
            = crt.sca.column$    \
                + str$(crt.column.xlate%(column%))
    return
    fend
   def fn.crt.sca$(row%,column%)
    if crt.sca.order% = crt.order.row.col%    \
      then    fn.crt.sca$ = crt.sca$        \
                + fn.crt.sca.row$(row%) \
                + fn.crt.sca.column$(column%)    \
      else    fn.crt.sca$ = crt.sca$        \
                + fn.crt.sca.column$(column%)    \
                + fn.crt.sca.row$(row%)
    return
    fend
%list
rem--------------------------------------------------------------
Rem $include "zdmslit"
rem    Nov.  8, 1979       ------------------------------------------
rem
rem      fn.lit%(id%)
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
Rem $include "zdmsmsg"
rem    DEC. 02, 1979            ---------------------------------------
rem
rem    fn.msg%(text$)        REM STANDARD
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
Rem $include "zdmsemsg"
rem     NOV.  1,1979           -----------------------------------------------
rem
rem    fn.emsg%(emsg%)     REM STANDARD
rem
rem----------------------------------------------------------------------------
%nolist
   def fn.emsg%(emsg%)
    trash%= fn.msg%(bell$+emsg$(emsg%))
    common.msg$=emsg$(emsg%)
    return
fend
%list
Rem $include "zdmsclr"
rem    Nov. 18, 1979       ---------------------------------------------------
rem
rem    fn.clr%(id%)
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

rem----------------------------------------------------------
rem
rem    C O N S T A N T S
rem
rem----------------------------------------------------------

del.file%=1
glx.file%=2
glx.len%=116

dim emsg$(05)
emsg$(01)="PY561"               rem dummy msg for fre stmt
emsg$(02)="PY562 NOT PROPERLY CHAINED"
emsg$(03)="PY563 NET PAY EXCEEDS EMPLOYEE MAXIMUM"
emsg$(04)="PY564 NET PAY EXCEEDS SYSTEM LIMIT - CHECK WILL BE VOIDED"
emsg$(05)="PY565 NET PAY CALCULATED FOR LESS THAN ZERO - NO CHECK MADE"

Rem $include "ipystat"
startup$        ="STARTUP"        rem   12/14/79
rebuild.pr1$        ="FIXPR1"
rebuild.pr2$        ="FIXPR2"
in.apply$        ="APPLICATION"
in.dedent$        ="DEDENT"
in.parent$        ="PARENTRY"
normal$         ="NORMAL"
default$        ="DEFAULTS"
quarter.end$        ="QEND"
year.end$        ="YEND"
Rem $include "ipydmemp"
dim emp.rate            (4)     rem 11/18/79
dim emp.sys.exempt%        (pr1.max.sys.eds%)
dim emp.dist.acct%        (pr1.max.dist.accts%)
dim emp.dist.percent        (pr1.max.dist.accts%)
dim emp.ed.desc$        (pr1.max.emp.eds%)
dim emp.ed.factor        (pr1.max.emp.eds%)
dim emp.ed.limit        (pr1.max.emp.eds%)
dim emp.ed.earn.ded$        (pr1.max.emp.eds%)
dim emp.ed.exclusion%        (pr1.max.emp.eds%)
dim emp.ed.amt.percent$     (pr1.max.emp.eds%)
dim emp.ed.limit.used%        (pr1.max.emp.eds%)
dim emp.ed.chk.cat%        (pr1.max.emp.eds%)
dim emp.ed.acct.no%        (pr1.max.emp.eds%)
Rem $include "ipydmchk"
dim chk.amt        (pr1.max.chk.cats%)         rem  9/12/79
Rem $include "ipydmhis"
dim his.qtd.sys         (pr1.max.sys.eds%)    rem  9/26/79
dim his.qtd.emp         (pr1.max.emp.eds%)
dim his.qtd.units        (4)
dim his.ytd.sys         (pr1.max.sys.eds%)
dim his.ytd.emp         (pr1.max.emp.eds%)
dim his.ytd.units        (4)
Rem $include "ipydmded"
dim ded.sys.used%        (pr1.max.sys.eds%)  rem 9/26/79
dim ded.sys.acct.no%        (pr1.max.sys.eds%)
dim ded.sys.chk.cat%        (pr1.max.sys.eds%)
dim ded.sys.desc$        (pr1.max.sys.eds%)
dim ded.sys.limit        (pr1.max.sys.eds%)
dim ded.sys.limit.used%     (pr1.max.sys.eds%)
dim ded.sys.factor        (pr1.max.sys.eds%)
dim ded.sys.earn.ded$        (pr1.max.sys.eds%)
dim ded.sys.amt.percent$    (pr1.max.sys.eds%)
dim ded.sys.exclusion%        (pr1.max.sys.eds%)
dim ded.fwt.mar.cutoff        (07)
dim ded.fwt.sin.cutoff        (07)
dim ded.fwt.mar.percent     (07)
dim ded.fwt.sin.percent     (07)
Rem $include "ipydmcoh"
dim coh.qtd.sys         (pr1.max.sys.eds%)     rem 12/02/79
dim coh.qtd.emp         (pr1.max.emp.eds%)
dim coh.qtd.units        (04)
dim coh.ytd.sys         (pr1.max.sys.eds%)
dim coh.ytd.emp         (pr1.max.emp.eds%)
dim coh.ytd.units        (04)
dim coh.date$            (12)
dim coh.tax            (12)
dim coh.q.tax            (04)
dim coh.q.fica.tax        (04)
dim coh.q.co.futa.liab        (04)
Rem $include "ipyckcat"
dim check.category%(pr1.max.ed.cats%)    rem   9/29/79
rem-----------------------------------------------------------
rem   check box 1 is gross pay.  It is the total of
rem   check boxes 2+3+4+5+6+7.
rem   check box 8 is net pay.  It is the difference
rem   between check box 1 and the sum of check
rem   boxes 9+10+11+12+13+14+15+16.
rem-----------------------------------------------------------
check.category%(01)=02       rem REGULAR PAY
check.category%(02)=03       rem OVERTIME PAY
check.category%(03)=04       rem SPECIAL OT PAY
check.category%(04)=05       rem COMMISSION
check.category%(05)=00       rem VACATION TAKEN      NOT ON CHECKS
check.category%(06)=00       rem SICK LVE TAKEN      NOT ON CHECKS
check.category%(07)=00       rem COMP TIME TAKEN      NOT ON CHECKS
check.category%(08)=00       rem COMP TIME EARND      NOT ON CHECKS
check.category%(09)=06       rem BONUS
check.category%(10)=07       rem TIPS COLLECTED
check.category%(11)=06       rem ADVANCE
check.category%(12)=06       rem SICK PAY
check.category%(13)=06       rem VACATION PAY
check.category%(14)=06       rem OTHER EXCLD PAY
check.category%(15)=06       rem EXPENSE REIMB
check.category%(16)=06       rem EIC
check.category%(17)=06       rem OTHER PAY
check.category%(18)=14       rem TIPS REPORTED
check.category%(19)=00       rem UNUSED
check.category%(20)=09       rem FWT
check.category%(21)=10       rem SWT
check.category%(22)=11       rem LWT
check.category%(23)=12       rem FICA
check.category%(24)=13       rem SDI
check.category%(25)=00       rem UNUSED
check.category%(26)=00       rem UNUSED
check.category%(27)=14       rem ADVANCE REPAY
check.category%(28)=09       rem FWT ADD-ON
check.category%(29)=10       rem SWT ADD-ON
check.category%(30)=11       rem LWT ADD-ON
check.category%(31)=12       rem FICA ADD-ON
check.category%(32)=00       rem UNUSED
check.category%(33)=00       rem SYS1 FROM DED FILE
check.category%(34)=00       rem SYS2 FROM DED FILE
check.category%(35)=00       rem SYS3 FROM DED FILE
check.category%(36)=00       rem SYS4 FROM DED FILE
check.category%(37)=00       rem SYS5 FROM DED FILE
check.category%(38)=00       rem EMP1 FROM EMP FILE
check.category%(39)=00       rem EMP2 FROM EMP FILE
check.category%(40)=00       rem EMP3 FROM EMP FILE
check.category%(41)=00       rem UNUSED
check.category%(42)=00       rem COMPANY FICA      NOT ON CHECKS
check.category%(43)=00       rem COMPANY FUTA      NOT ON CHECKS
check.category%(44)=00       rem COMPANY SUI      NOT ON CHECKS
check.category%(45)=00       rem UNUSED
check.category%(46)=00       rem OTHER CO COST      NOT ON CHECKS
check.category%(47)=00       rem UNUSED
check.category%(48)=00       rem UNUSED
check.category%(49)=00       rem UNUSED
check.category%(50)=16       rem OTHER DED
Rem $include "zdateio"
rem      May  10, 1979
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

Rem $include "fpyap3"
rem---------------------------------------------------------
rem    SET UP DMS SCREEN EQUATES    FPYAP3 - 11/20/79

crt.field.count% = 7       rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem    LEGEND:    X  Y  LEN  RD  ATTRIB
rem        STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data           \
      1,3,8,0,0,\        rem   O fld #1
      20,13,27,0,0,\       rem   O fld #2
      48,13,10,0,0,\       rem   O fld #3
      22,15,27,0,0,\       rem   O fld #4
      50,15,5,0,0,\       rem   O fld #5
      18,15,42,0,0,\       rem   O fld #6
      26,20,30,0,0
      rem    O fld #7
crt.data$(2)="CURRENT EMPLOYEE STATUS IS:"
crt.data$(3)="XXXXXXXXXX"
crt.data$(4)="PROCESSING EMPLOYEE NUMBER:"
crt.data$(5)="XXXXX"
crt.data$(6)="EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
crt.data$(7)="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

i%=1
while i%<=7
  read    crt.x%(i%),crt.y%(i%),\
    crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(function.name$)<=30 \
  then     fun.name$=fn.spread$(function.name$,1)  \
  else     fun.name$=function.name$
crt.len%(1)=len(fun.name$)
crt.x%(1)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(1)=fun.name$

rem---------------------------------------------------------

dim sys     (5)
dim emp     (3)
dim units    (4)
dim acct.amt    (pr2.no.acts%)
dim dist.amt    (pr1.max.dist.accts%)

def fn.decompose.date%(date$)
    dy%=val(mid$(date$,5,2))
    mo%=val(mid$(date$,3,2))
    yr%=val(mid$(date$,1,2))
    return
fend

def fn.quarter%(date$)
    trash%=fn.decompose.date%(date$)
    if mo%=01 or mo%=02 or mo%=03 then fn.quarter%=1:return
    if mo%=04 or mo%=05 or mo%=06 then fn.quarter%=2:return
    if mo%=07 or mo%=08 or mo%=09 then fn.quarter%=3:return
    if mo%=10 or mo%=11 or mo%=12 then fn.quarter%=4:return
fend

def fn.round(rr)=(int((rr*100)+.5))/100

rem----------------------------------------------------------
rem
rem    S E T        U P
rem
rem----------------------------------------------------------

gosub 200        rem display.set.up.screen

rem----------------------------------------------------------
rem
rem    B O J
rem
rem----------------------------------------------------------

gosub 210            rem can.we.run
if not ok% then goto 999.1

gosub 500            rem set up files
gosub 330            rem display.process.screen

rem----------------------------------------------------------
rem
rem    M A I N      D R I V E R
rem
rem----------------------------------------------------------

employee%=1
while employee%<=pr2.no.employees%
    gosub 400            rem process.employee
    employee%=employee%+1
    if pr1.debugging% \
        then    crt.data$(07)="free storage: "+str$(fre)  :\
            trash%=fn.lit%(07)
wend

rem----------------------------------------------------------
rem
rem    E N D      O F      J O B
rem
rem----------------------------------------------------------

gosub 800            rem write.pay.hdr
close pay.file%
gosub 783            rem delete pay 102
gosub 787            rem rename(pay.102=pay.101)
gosub 790            rem rename(pay.101=pay.100)
gosub 810            rem update his hdr
gosub 760            rem open,write,close coh file
if pr1.gl.used% \
    then    gosub 820 :\    rem create GJB file
        gosub 850 :\    rem write out GJB file
        gosub 860 :\    rem close GJB file

gosub 775            rem write chk hdr
gosub 990            rem close.all.files
gosub 995            rem rename(chk.101=chk.100)

Rem $include "zeoj"
rem    DEC. 02, 1979
999    rem-----normal end of job---------------
trash%=fn.msg%(function.name$+" COMPLETED")
common.return.code%=0
goto 999.3
999.1  rem-----abnormal end of job-------------
print using "&";fn.crt.sca$(crt.rows%-2, 1);left$(blank$, crt.columns%)
print using "&";fn.crt.sca$(crt.rows%-1, 1);"     "+function.name$+\
    " COMPLETED UNSUCCESSFULLY     "+crt.msg.trailer$
common.return.code%=1
goto 999.3
999.2  rem-----premature end of job------------
trash%=fn.msg%(function.name$+" TERMINATING AT OPERATOR'S REQUEST")
common.return.code%=2
999.3  rem-----return to menu or stop----------
if chained.from.root% \
    then    chain system$ \
    else    stop

rem----------------------------------------------------------
rem
rem    S U B R O U T I N E S
rem
rem----------------------------------------------------------

200    rem-----display set up screen------------------------
    trash%=fn.lit%(1)    rem function name
    trash%=fn.lit%(6)    rem EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY
    return

210    rem-----can we run?----------------------------------
    ok%=true%
    if match(in.apply$,common.chaining.status$,1)=0 \
        then    ok%=false%    :\
            trash%=fn.emsg%(02)
    return

330    rem-----display process screen-----------------------
    trash%=fn.clr%(6)
    trash%=fn.lit%(4)    rem PROCESSING EMPLOYEE NUMBER:
    trash%=fn.lit%(2)    rem CURRENT EMPLOYEE STATUS IS:
    return

400    rem-----process employee-----------------------------
    gosub 1000            rem clear.employee.accums
    gosub 1020            rem read.next.employee.record
    gosub 1010            rem display employee number
    gosub 1030            rem display employee status
    trash%=fn.msg%(null$)        rem clear error msg line

    if emp.status$="D"              \
        then    return

    if match(emp.pay.interval$,extension.intervals$,1)=0 \
        then    return

    gosub 1040            rem set up chk rec
    gosub 1050            rem read.matching.history.record

    while not pay.eof% and val(left$(pay.emp.no$,4))=employee%
        gosub 1060        rem process pay rec
        gosub 1070        rem select a pay rec
    wend

    gosub 1200            rem calculate gross and net
    gosub 1300            rem distribute to acct table
    gosub 1315            rem distribute offset amounts
    gosub 815            rem increment COH fields
    gosub 1320            rem update history record
    gosub 1330            rem write.history.record
    gosub 1335            rem test amt against maximums
    gosub 1340            rem generate check record
    return

500    rem-----set up files---------------------------------
    gosub 540            rem open existing pay file for input
    if pay.exists% \
        then    gosub 550 :\    rem get.pay.hdr
            gosub 560  \    rem get priming read
        else    pay.eof%=true%
    gosub 570            rem open emp.file
    gosub 580            rem read emp hdr
    gosub 590            rem open ded.file
    gosub 600            rem read ded file
    close ded.file%
    gosub 670            rem open his file
    gosub 680            rem read.his.hdr
    gosub 690            rem get act file
    gosub 700            rem get act hdr rec
    gosub 710            rem get coh file
    gosub 765            rem set COH fields for this run
    gosub 770            rem create new check file
    gosub 777            rem delete hrs.bak
    gosub 780            rem rename(hrs.bak=hrs)
    return

540    rem-----open pay file--------------------------------
    pay.exists%=false%
    if end #pay.file% then 541
    open fn.file.name.out$(pay.name$,"100",pr1.pyo.drive%,pw$,pms$) \
        recl pay.len%  as pay.file%
    pay.exists%=true%
541    rem-----here if pay file not present-----------------
    return

550    rem-----get pay hdr----------------------------------
    read #pay.file%,1;    \
Rem $include "ipypayhd"
        pay.hdr.no.recs%,\       rem 10/30/79
        pay.hdr.interval$,\
        pay.hdr.last.apply.no%,\
        pay.hdr.journal.printed%,\
        pay.hdr.last.day.of.last.per$,\
        pay.hdr.101,\
        pay.hdr.102,\
        pay.hdr.201$
    return

560    rem-----get pay priming read-------------------------
    pay.rec%=0
    gosub 1070            rem select a pay rec
    return

570    rem-----open emp file--------------------------------
    emp.exists%=false%
    if end #emp.file% then 571
    open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pms$) \
        recl emp.len%  as emp.file%
    emp.exists%=true%
571    rem-----here if emp file not present-----------------
    return

580    rem-----read emp hdr---------------------------------
    read #emp.file%,1;  \
Rem $include "ipyemphd"
        emp.hdr.no.recs%,\      rem 10/30/79
        emp.hdr.no.del.recs%,\
        emp.hdr.next.del.rec%,\
        emp.hdr.101,\
        emp.hdr.102,\
        emp.hdr.201$
    return

590    rem-----open ded file--------------------------------
    ded.exists%=false%
    if end #ded.file% then 591
    open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pw$,pms$) \
        as ded.file%
    ded.exists%=true%
591    rem-----here if ded file not present-----------------
    return

600    rem-----read ded file--------------------------------
    read #ded.file%; \
Rem $include "ipyded"
ded.fwt.used%,\           rem   10/04/79
ded.fwt.acct.no%,ded.fwt.allowance.amt,\
ded.fwt.mar.cutoff(01),ded.fwt.mar.percent(01),\
ded.fwt.mar.cutoff(02),ded.fwt.mar.percent(02),\
ded.fwt.mar.cutoff(03),ded.fwt.mar.percent(03),\
ded.fwt.mar.cutoff(04),ded.fwt.mar.percent(04),\
ded.fwt.mar.cutoff(05),ded.fwt.mar.percent(05),\
ded.fwt.mar.cutoff(06),ded.fwt.mar.percent(06),\
ded.fwt.mar.cutoff(07),ded.fwt.mar.percent(07),\
ded.fwt.sin.cutoff(01),ded.fwt.sin.percent(01),\
ded.fwt.sin.cutoff(02),ded.fwt.sin.percent(02),\
ded.fwt.sin.cutoff(03),ded.fwt.sin.percent(03),\
ded.fwt.sin.cutoff(04),ded.fwt.sin.percent(04),\
ded.fwt.sin.cutoff(05),ded.fwt.sin.percent(05),\
ded.fwt.sin.cutoff(06),ded.fwt.sin.percent(06),\
ded.fwt.sin.cutoff(07),ded.fwt.sin.percent(07),\
ded.swt.used%,ded.swt.acct.no%,\
ded.lwt.used%,ded.lwt.acct.no%,\
ded.fica.used%,\
ded.fica.acct.no%,ded.fica.rate,ded.fica.limit,\
ded.co.fica.used%,\
ded.co.fica.acct.no%,ded.co.fica.rate,ded.co.fica.limit,\
ded.sdi.used%,\
ded.sdi.acct.no%,ded.sdi.rate,ded.sdi.limit,\
ded.co.futa.used%,\
ded.co.futa.acct.no%,ded.co.futa.rate,ded.co.futa.limit,\
ded.co.futa.max.credit,\
ded.co.sui.used%,\
ded.co.sui.acct.no%,ded.co.sui.rate,ded.co.sui.limit,\
ded.eic.used%,\
ded.eic.acct.no%,ded.eic.rate,ded.eic.limit,\
ded.eic.excess.rate,ded.eic.excess.limit,\
ded.sys.used%(01),\
ded.sys.acct.no%(01),ded.sys.chk.cat%(01),ded.sys.desc$(01),\
ded.sys.limit(01),ded.sys.factor(01),ded.sys.earn.ded$(01),\
ded.sys.amt.percent$(01),ded.sys.exclusion%(01),ded.sys.limit.used%(01),\
ded.sys.used%(02),\
ded.sys.acct.no%(02),ded.sys.chk.cat%(02),ded.sys.desc$(02),\
ded.sys.limit(02),ded.sys.factor(02),ded.sys.earn.ded$(02),\
ded.sys.amt.percent$(02),ded.sys.exclusion%(02),ded.sys.limit.used%(02),\
ded.sys.used%(03),\
ded.sys.acct.no%(03),ded.sys.chk.cat%(03),ded.sys.desc$(03),\
ded.sys.limit(03),ded.sys.factor(03),ded.sys.earn.ded$(03),\
ded.sys.amt.percent$(03),ded.sys.exclusion%(03),ded.sys.limit.used%(03),\
ded.sys.used%(04),\
ded.sys.acct.no%(04),ded.sys.chk.cat%(04),ded.sys.desc$(04),\
ded.sys.limit(04),ded.sys.factor(04),ded.sys.earn.ded$(04),\
ded.sys.amt.percent$(04),ded.sys.exclusion%(04),ded.sys.limit.used%(04),\
ded.sys.used%(05),\
ded.sys.acct.no%(05),ded.sys.chk.cat%(05),ded.sys.desc$(05),\
ded.sys.limit(05),ded.sys.factor(05),ded.sys.earn.ded$(05),\
ded.sys.amt.percent$(05),ded.sys.exclusion%(05),ded.sys.limit.used%(05)
    return

670    rem-----open his file--------------------------------
    his.exists%=false%
    if end #his.file% then 671
    open fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pms$) \
        recl his.len%  as his.file%
    his.exists%=true%
671    rem-----here if his file not present-----------------
    return

680    rem-----read his hdr---------------------------------
    read #his.file%,1;     \
Rem $include "ipyhishd"
        his.hdr.no.recs%,\        rem  11/12/79
        his.hdr.last.to.date$,\
        his.hdr.101,\
        his.hdr.102,\
        his.hdr.201$
    return

690    rem-----get act file---------------------------------
    act.exists%=false%
    if end #act.file% then 691
    open fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pms$) \
        recl act.len%  as act.file%
    act.exists%=true%
691    rem-----here if act file not present-----------------
    return

700    rem-----get act hdr rec------------------------------
    read #act.file%,1;     \
Rem $include "ipyacthd"
        act.hdr.no.recs%     rem   9/12/79
    return

710    rem-----get coh file---------------------------------
    gosub 720            rem open coh if present
    if coh.exists% \
        then    gosub 730 :\    rem read coh file
            close coh.file% :\
        else    gosub 740 :\    rem create coh file
            close coh.file%  :\
            gosub 750 :\    rem initialize coh fields
            gosub 760    rem open,write,close coh rec
    return

720    rem-----open coh if present--------------------------
    coh.exists%=false%
    if end #coh.file% then 721
    open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
        as coh.file%
    coh.exists%=true%
721    rem-----here if coh file not present-----------------
    return

730    rem-----read coh file--------------------------------
    read #coh.file%;   \
Rem $include "ipycoh"
        coh.last.apply.no%,\        rem  12/02/79
        coh.interval$,coh.starting.up%,\
        coh.qtd.income.taxable,coh.qtd.other.taxable,\
        coh.qtd.other.nontaxable,coh.qtd.fica.taxable,\
        coh.qtd.tips,coh.qtd.net,coh.qtd.eic.credit,\
        coh.qtd.fwt.liab,coh.qtd.swt.liab,coh.qtd.lwt.liab,\
        coh.qtd.fica.liab,coh.qtd.sdi.liab,coh.qtd.co.futa.liab,\
        coh.qtd.co.fica.liab,coh.qtd.co.sui.liab,\
        coh.qtd.sys(01),coh.qtd.sys(02),coh.qtd.sys(03),\
        coh.qtd.sys(04),coh.qtd.sys(05),\
        coh.qtd.emp(01),coh.qtd.emp(02),coh.qtd.emp(03),\
        coh.qtd.other.ded,\
        coh.qtd.units(01),coh.qtd.units(02),\
        coh.qtd.units(03),coh.qtd.units(04),\
        coh.qtd.comp.time.earned,coh.qtd.comp.time.taken,\
        coh.qtd.vac.earned,coh.qtd.vac.taken,\
        coh.qtd.sl.earned,coh.qtd.sl.taken,\
        coh.ytd.income.taxable,coh.ytd.other.taxable,\
        coh.ytd.other.nontaxable,coh.ytd.fica.taxable,\
        coh.ytd.tips,coh.ytd.net,coh.ytd.eic.credit,\
        coh.ytd.fwt.liab,coh.ytd.swt.liab,coh.ytd.lwt.liab,\
        coh.ytd.fica.liab,coh.ytd.sdi.liab,coh.ytd.co.futa.liab,\
        coh.ytd.co.fica.liab,coh.ytd.co.sui.liab,\
        coh.ytd.sys(01),coh.ytd.sys(02),coh.ytd.sys(03),\
        coh.ytd.sys(04),coh.ytd.sys(05),\
        coh.ytd.emp(01),coh.ytd.emp(02),coh.ytd.emp(03),\
        coh.ytd.other.ded,\
        coh.ytd.units(01),coh.ytd.units(02),\
        coh.ytd.units(03),coh.ytd.units(04),\
        coh.ytd.comp.time.earned,coh.ytd.comp.time.taken,\
        coh.ytd.vac.earned,coh.ytd.vac.taken,\
        coh.ytd.sl.earned,coh.ytd.sl.taken,\
        coh.date$(01),coh.date$(02),coh.date$(03),coh.date$(04),\
        coh.date$(05),coh.date$(06),coh.date$(07),coh.date$(08),\
        coh.date$(09),coh.date$(10),coh.date$(11),coh.date$(12),\
        coh.tax(01),coh.tax(02),coh.tax(03),coh.tax(04),\
        coh.tax(05),coh.tax(06),coh.tax(07),coh.tax(08),\
        coh.tax(09),coh.tax(10),coh.tax(11),coh.tax(12),\
        coh.q.tax(01),coh.q.tax(02),coh.q.tax(03),coh.q.tax(04),\
        coh.q.fica.tax(01),coh.q.fica.tax(02),\
        coh.q.fica.tax(03),coh.q.fica.tax(04),\
        coh.q.co.futa.liab(1),coh.q.co.futa.liab(2),\
        coh.q.co.futa.liab(3),coh.q.co.futa.liab(4)
    return

740    rem-----create coh file------------------------------
    create fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
        as coh.file%
    return

750    rem-----initialize coh fields------------------------
    coh.last.apply.no%=        apply.no%
    coh.interval$=            interval$
    coh.starting.up%=        false%
    return

760    rem-----open,write,close coh record------------------
    gosub 720            rem open coh file
    print #coh.file%;    \
Rem $include "ipycoh"
        coh.last.apply.no%,\        rem  12/02/79
        coh.interval$,coh.starting.up%,\
        coh.qtd.income.taxable,coh.qtd.other.taxable,\
        coh.qtd.other.nontaxable,coh.qtd.fica.taxable,\
        coh.qtd.tips,coh.qtd.net,coh.qtd.eic.credit,\
        coh.qtd.fwt.liab,coh.qtd.swt.liab,coh.qtd.lwt.liab,\
        coh.qtd.fica.liab,coh.qtd.sdi.liab,coh.qtd.co.futa.liab,\
        coh.qtd.co.fica.liab,coh.qtd.co.sui.liab,\
        coh.qtd.sys(01),coh.qtd.sys(02),coh.qtd.sys(03),\
        coh.qtd.sys(04),coh.qtd.sys(05),\
        coh.qtd.emp(01),coh.qtd.emp(02),coh.qtd.emp(03),\
        coh.qtd.other.ded,\
        coh.qtd.units(01),coh.qtd.units(02),\
        coh.qtd.units(03),coh.qtd.units(04),\
        coh.qtd.comp.time.earned,coh.qtd.comp.time.taken,\
        coh.qtd.vac.earned,coh.qtd.vac.taken,\
        coh.qtd.sl.earned,coh.qtd.sl.taken,\
        coh.ytd.income.taxable,coh.ytd.other.taxable,\
        coh.ytd.other.nontaxable,coh.ytd.fica.taxable,\
        coh.ytd.tips,coh.ytd.net,coh.ytd.eic.credit,\
        coh.ytd.fwt.liab,coh.ytd.swt.liab,coh.ytd.lwt.liab,\
        coh.ytd.fica.liab,coh.ytd.sdi.liab,coh.ytd.co.futa.liab,\
        coh.ytd.co.fica.liab,coh.ytd.co.sui.liab,\
        coh.ytd.sys(01),coh.ytd.sys(02),coh.ytd.sys(03),\
        coh.ytd.sys(04),coh.ytd.sys(05),\
        coh.ytd.emp(01),coh.ytd.emp(02),coh.ytd.emp(03),\
        coh.ytd.other.ded,\
        coh.ytd.units(01),coh.ytd.units(02),\
        coh.ytd.units(03),coh.ytd.units(04),\
        coh.ytd.comp.time.earned,coh.ytd.comp.time.taken,\
        coh.ytd.vac.earned,coh.ytd.vac.taken,\
        coh.ytd.sl.earned,coh.ytd.sl.taken,\
        coh.date$(01),coh.date$(02),coh.date$(03),coh.date$(04),\
        coh.date$(05),coh.date$(06),coh.date$(07),coh.date$(08),\
        coh.date$(09),coh.date$(10),coh.date$(11),coh.date$(12),\
        coh.tax(01),coh.tax(02),coh.tax(03),coh.tax(04),\
        coh.tax(05),coh.tax(06),coh.tax(07),coh.tax(08),\
        coh.tax(09),coh.tax(10),coh.tax(11),coh.tax(12),\
        coh.q.tax(01),coh.q.tax(02),coh.q.tax(03),coh.q.tax(04),\
        coh.q.fica.tax(01),coh.q.fica.tax(02),\
        coh.q.fica.tax(03),coh.q.fica.tax(04),\
        coh.q.co.futa.liab(1),coh.q.co.futa.liab(2),\
        coh.q.co.futa.liab(3),coh.q.co.futa.liab(4)
    close coh.file%
    return

765    rem-----set COH fields for this run------------------
    coh.last.apply.no%=        apply.no%
    coh.interval$=            interval$
    coh.starting.up%=        false%

    quarter%=fn.quarter%(pr2.check.date$)
    trash%=fn.decompose.date%(pr2.check.date$)
    if dy%>=1 and dy%<=7    then    week%=1
    if dy%>=8 and dy%<=15    then    week%=2
    if dy%>=16 and dy%<=22    then    week%=3
    if dy%>=23        then    week%=4
    if mo%=1 or mo%=4 or mo%=7 or mo%=10    then    week%=week%
    if mo%=2 or mo%=5 or mo%=8 or mo%=11    then    week%=week%+4
    if mo%=3 or mo%=6 or mo%=9 or mo%=12    then    week%=week%+8
    coh.date$(week%)=pr2.check.date$
    return

770    rem-----create new check file for output-------------
    if pr1.debugging% \
        then    crt.data$(07)="CREATING CHK FILE"       :\
            trash%=fn.lit%(07)
    create fn.file.name.out$(chk.name$,"100",pr1.chk.drive%,pw$,pms$) \
        recl chk.len%  as chk.file%
    chk.hdr.no.recs%=0
    chk.hdr.interval$=left$(interval$,1)
    chk.hdr.apply.no%=apply.no%
    chk.hdr.register.printed%=false%
    chk.hdr.checks.printed%=false%
    chk.hdr.slow.from.date$=left$(from.slow.date$,6)
    chk.hdr.fast.from.date$=left$(from.fast.date$,6)
    chk.hdr.to.date$=left$(to.date$,6)
    gosub 775            rem write chk hdr
    return

775    rem-----write chk hdr--------------------------------
    print #chk.file%,1;     \
Rem $include "ipychkhd"
        chk.hdr.no.recs%,\         rem 10/30/79
        chk.hdr.interval$,\
        chk.hdr.apply.no%,\
        chk.hdr.register.printed%,\
        chk.hdr.checks.printed%,\
        chk.hdr.slow.from.date$,\
        chk.hdr.fast.from.date$,\
        chk.hdr.to.date$,\
        chk.hdr.101,\
        chk.hdr.102,\
        chk.hdr.201$
    return

777    rem-----delete hrs.bak-------------------------------
    if end #del.file% then 776
    open fn.file.name.out$(hrs.name$,"102",pr1.hrs.drive%,pw$,pms$) \
        as del.file%
    delete del.file%
776    rem-----here if del file not present-----------------
    return

780    rem-----rename(hrs.bak=hrs)--------------------------
    trash%=rename      \
        (fn.file.name.out$(hrs.name$,"102",pr1.hrs.drive%,pw$,pms$), \
         fn.file.name.out$(hrs.name$,"101",pr1.hrs.drive%,pw$,pms$))
    return

783    rem-----delete pay 102-------------------------------
    if end #del.file% then 784
    open fn.file.name.out$(pay.name$,"102",pr1.pyo.drive%,pw$,pms$) \
        as del.file%
    delete del.file%
784    rem-----here if del file not present-----------------
    return

787    rem-----rename(pay.102=pay.101)----------------------
    trash%=rename      \
        (fn.file.name.out$(pay.name$,"102",pr1.pyo.drive%,pw$,pms$), \
         fn.file.name.out$(pay.name$,"101",pr1.pyo.drive%,pw$,pms$))
    return

790    rem-----rename(pay.101=pay.100)----------------------
    trash%=rename      \
        (fn.file.name.out$(pay.name$,"101",pr1.pyo.drive%,pw$,pms$), \
         fn.file.name.out$(pay.name$,"100",pr1.pyo.drive%,pw$,pms$))
    return

800    rem-----write pay hdr--------------------------------
    print #pay.file%,1;    \
Rem $include "ipypayhd"
        pay.hdr.no.recs%,\       rem 10/30/79
        pay.hdr.interval$,\
        pay.hdr.last.apply.no%,\
        pay.hdr.journal.printed%,\
        pay.hdr.last.day.of.last.per$,\
        pay.hdr.101,\
        pay.hdr.102,\
        pay.hdr.201$
    return

810    rem-----update his hdr-------------------------------
    his.hdr.to.date$=to.date$
    return

815    rem-----increment COH accumulators-------------------
    coh.qtd.income.taxable=coh.qtd.income.taxable+income.taxable
    coh.qtd.other.taxable=coh.qtd.other.taxable+other.taxable
    coh.qtd.other.nontaxable=coh.qtd.other.nontaxable+other.nontaxable
    coh.qtd.fica.taxable=coh.qtd.fica.taxable+fica.taxable
    coh.qtd.tips=coh.qtd.tips+tips
    coh.qtd.net=coh.qtd.net+net
    coh.qtd.eic.credit=coh.qtd.eic.credit+eic
    coh.qtd.fwt.liab=coh.qtd.fwt.liab+fwt
    coh.qtd.swt.liab=coh.qtd.swt.liab+swt
    coh.qtd.lwt.liab=coh.qtd.lwt.liab+lwt
    coh.qtd.fica.liab=coh.qtd.fica.liab+fica
    coh.qtd.sdi.liab=coh.qtd.sdi.liab+sdi
    coh.qtd.co.futa.liab=coh.qtd.co.futa.liab+co.futa
    coh.qtd.co.fica.liab=coh.qtd.co.fica.liab+co.fica
    coh.qtd.co.sui.liab=coh.qtd.co.sui.liab+co.sui
    for i%=1 to pr1.max.sys.eds%
        coh.qtd.sys(i%)=coh.qtd.sys(i%)+sys(i%)
        coh.ytd.sys(i%)=coh.ytd.sys(i%)+sys(i%)
    next i%
    for i%=1 to pr1.max.emp.eds%
        coh.qtd.emp(i%)=coh.qtd.emp(i%)+emp(i%)
        coh.ytd.emp(i%)=coh.ytd.emp(i%)+emp(i%)
    next i%
    coh.qtd.other.ded=coh.qtd.other.ded+other.ded
    for i%=1 to 4
        coh.qtd.units(i%)=coh.qtd.units(i%)+units(i%)
        coh.ytd.units(i%)=coh.ytd.units(i%)+units(i%)
    next i%
    coh.qtd.comp.time.earned=coh.qtd.comp.time.earned+comp.earned
    coh.qtd.comp.time.taken=coh.qtd.comp.time.taken+comp.taken
    coh.qtd.vac.earned=coh.qtd.vac.earned+emp.vac.rate
    coh.qtd.vac.taken=coh.qtd.vac.taken+vac.taken
    coh.qtd.sl.earned=coh.qtd.sl.earned+emp.sl.rate
    coh.qtd.sl.taken=coh.qtd.sl.taken+sl.taken

    coh.ytd.income.taxable=coh.ytd.income.taxable+income.taxable
    coh.ytd.other.taxable=coh.ytd.other.taxable+other.taxable
    coh.ytd.other.nontaxable=coh.ytd.other.nontaxable+other.nontaxable
    coh.ytd.fica.taxable=coh.ytd.fica.taxable+fica.taxable
    coh.ytd.tips=coh.ytd.tips+tips
    coh.ytd.net=coh.ytd.net+net
    coh.ytd.eic.credit=coh.ytd.eic.credit+eic
    coh.ytd.fwt.liab=coh.ytd.fwt.liab+fwt
    coh.ytd.swt.liab=coh.ytd.swt.liab+swt
    coh.ytd.lwt.liab=coh.ytd.lwt.liab+lwt
    coh.ytd.fica.liab=coh.ytd.fica.liab+fica
    coh.ytd.sdi.liab=coh.ytd.sdi.liab+sdi
    coh.ytd.co.futa.liab=coh.ytd.co.futa.liab+co.futa
    coh.ytd.co.fica.liab=coh.ytd.co.fica.liab+co.fica
    coh.ytd.co.sui.liab=coh.ytd.co.sui.liab+co.sui
    coh.ytd.other.ded=coh.ytd.other.ded+other.ded
    coh.ytd.comp.time.earned=coh.ytd.comp.time.earned+comp.earned
    coh.ytd.comp.time.taken=coh.ytd.comp.time.taken+comp.taken
    coh.ytd.vac.earned=coh.ytd.vac.earned+emp.vac.rate
    coh.ytd.vac.taken=coh.ytd.vac.taken+vac.taken
    coh.ytd.sl.earned=coh.ytd.sl.earned+emp.sl.rate
    coh.ytd.sl.taken=coh.ytd.sl.taken+sl.taken

    coh.tax(week%)=coh.tax(week%)  +   ((fwt+fica+co.fica)-eic)
    return

820    rem-----create GJB file------------------------------
    gosub 900            rem delete GJB.BAK
    gosub 910            rem rename GJB.BAK<--GJB if there
    if from.fast.date$<from.slow.date$ \
        then    earliest.date$=from.fast.date$ \
        else    earliest.date$=from.slow.date$
    glx.date$=        fn.date.out$(common.date$)
    glx.reference$=     \
        "PY:"                           +\
        extension.intervals$        +\
        " "                             +\
        fn.date.out$(earliest.date$)    +\
        " TO "                          +\
        fn.date.out$(to.date$)

rem format of GJB reference field is:
rem        PY:aa #nn mm/dd/yy to mm/dd/yy
rem    where aa is extension interval letters
rem          nn is application number

    create fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,"100",\
        pr1.glx.drive%,pw$,pms$) \
        recl glx.len%        \
        as glx.file%
    return

850    rem-----write out GJB file---------------------------
    x%=1
    while x%<=pr2.no.acts%
        act.rec%=x%
        if acct.amt(act.rec%)=0 then goto 851    rem break
        gosub 870        rem read act rec
        gosub 880        rem build GJB record
        gosub 890        rem write GJB record
851
        x%=x%+1
    wend
    return

860    rem-----close GJB file-------------------------------
    close glx.file%
    return

870    rem-----read act rec---------------------------------
    read #act.file%,act.rec%+1;    \
Rem $include "ipyact"
        act.no$,\         rem 12/11/79
        act.desc$
    return

880    rem-----build GJB record-----------------------------
    gjb.co.no$=        "0"
    gjb.dept.no$=        right$(act.no$,2)
    gjb.acct.no$=        left$(act.no$,4)
    gjb.acct.name$=     left$(act.desc$+blank$,30)
    gjb.eff.date$=        glx.date$
    gjb.amt=        abs(acct.amt(act.rec%))
    gosub 883            rem determine GJB.DR.CR$
    gjb.ref$=        glx.reference$
    gjb.delete.flag=    false%
    return

883    rem-----determine GJB.DR.CR$-------------------------
    if left$(gjb.acct.no$,1)="0" or  \
       left$(gjb.acct.no$,1)="4" or  \
       left$(gjb.acct.no$,1)="5"     \
        then    debits.normal%=true%   \
        else    debits.normal%=false%
    if debits.normal%        \
        then    gjb.dr.cr$="D"  \
        else    gjb.dr.cr$="C"
    if acct.amt(act.rec%)<0 \
        then    gosub 885    rem swap dr/cr
    return

885    rem-----swap dr/cr-----------------------------------
    if gjb.dr.cr$="D" \
        then    gjb.dr.cr$="C" \
        else    gjb.dr.cr$="D"
    return

890    rem-----write GJB record-----------------------------
    gjb.rec%=gjb.rec%+1
    print #glx.file%,gjb.rec%;    \
        GJB.CO.NO$,\
        GJB.DEPT.NO$,\
        GJB.ACCT.NO$,\
        GJB.ACCT.NAME$,\
        GJB.EFF.DATE$,\
        GJB.AMT,\
        GJB.DR.CR$,\
        GJB.REF$,\
        GJB.DELETE.FLAG
    return

900    rem-----delete GJB.BAK-------------------------------
    if end #del.file% then 901
    open fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,\
        "101",pr1.glx.drive%,pw$,pms$)    \
        as del.file%
    delete del.file%
901    rem-----here if no bak file exists-------------------
    return

910    rem-----rename GJB.BAK<--GJB if there----------------
    trash%=rename      \
        (fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,        \
            "101",pr1.glx.drive%,pw$,pms$),                 \
         fn.file.name.out$("PGLGJB"+pr1.gl.file.suffix$,        \
            "100",pr1.glx.drive%,pw$,pms$))
    return

990    rem-----close all files------------------------------
    close chk.file%
    close emp.file%
    close his.file%
    return

995    rem-----rem rename(chk.101=chk.100)------------------
    trash%=rename      \
        (fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$), \
         fn.file.name.out$(chk.name$,"100",pr1.chk.drive%,pw$,pms$))
    return

1000    rem-----clear employee accums------------------------
    gross.taxable.pay    =zero
    income.taxable        =zero
    other.taxable        =zero
    other.nontaxable    =zero
    fica.taxable        =zero
    tips            =zero
    tips.reported        =zero
    net            =zero
    eic            =zero
    fwt            =zero
    swt            =zero
    lwt            =zero
    fica            =zero
    sdi            =zero
    sys(1)            =zero
    sys(2)            =zero
    sys(3)            =zero
    sys(4)            =zero
    sys(5)            =zero
    emp(1)            =zero
    emp(2)            =zero
    emp(3)            =zero
    other.ded        =zero
    units(0)        =zero
    units(1)        =zero
    units(2)        =zero
    units(3)        =zero
    units(4)        =zero
    vac.taken        =zero
    sl.taken        =zero
    comp.taken        =zero
    comp.earned        =zero
    fwt            =zero
    swt            =zero
    lwt            =zero
    fica            =zero
    co.fica         =zero
    co.futa         =zero
    co.sui            =zero
    employer.costs        =zero
    return

1010    rem-----display employee number----------------------
    crt.data$(05)=emp.no$
    trash%=fn.lit%(5)
    return

1020    rem-----read next employee record--------------------
    read #emp.file%,employee%+1;    \
Rem $include "ipyemp"
        emp.no$,\           rem    12/02/79
        emp.status$,emp.hs.type$,emp.pay.interval$,\
        emp.taxing.state$,emp.job.code$,\
        emp.start.date$,emp.birth.date$,emp.term.date$,\
        emp.sex$,emp.marital$,emp.ssn$,\
        emp.pay.freq%,emp.emp.name$,\      rem last sort field
        emp.next.del%,emp.cur.apply.no%,emp.phone$,\
        emp.addr1$,emp.addr2$,emp.city$,emp.state$,emp.zip$,\
        emp.rate(1),emp.rate(2),emp.rate(3),emp.rate(4),\
        emp.auto.units,emp.normal.units,emp.max.pay,\
        emp.rate4.exclusion%,emp.eic.used%,\
        emp.cal.head.of.house%,emp.cal.ded.allow%,\
        emp.fwt.allow%,emp.swt.allow%,emp.lwt.allow%,\
        emp.pension.used%,emp.bank.acct.no$,\
        emp.fwt.exempt%,emp.swt.exempt%,emp.lwt.exempt%,\
        emp.fica.exempt%,emp.sdi.exempt%,\
        emp.co.futa.exempt%,emp.co.sui.exempt%,\
        emp.sys.exempt%(1),emp.sys.exempt%(2),emp.sys.exempt%(3),\
        emp.sys.exempt%(4),emp.sys.exempt%(5),\
        emp.vac.rate,emp.vac.accum,emp.vac.used,\
        emp.sl.rate,emp.sl.accum,emp.sl.used,\
        emp.comp.accum,emp.comp.used,\
        emp.dist.acct%(1),emp.dist.percent(1),\
        emp.dist.acct%(2),emp.dist.percent(2),\
        emp.dist.acct%(3),emp.dist.percent(3),\
        emp.dist.acct%(4),emp.dist.percent(4),\
        emp.dist.acct%(5),emp.dist.percent(5),\
        emp.ed.desc$(1),emp.ed.factor(1),emp.ed.limit(1),\
        emp.ed.earn.ded$(1),emp.ed.exclusion%(1),\
        emp.ed.amt.percent$(1),emp.ed.limit.used%(1),\
        emp.ed.chk.cat%(1),emp.ed.acct.no%(1), \
        emp.ed.desc$(2),emp.ed.factor(2),emp.ed.limit(2),\
        emp.ed.earn.ded$(2),emp.ed.exclusion%(2),\
        emp.ed.amt.percent$(2),emp.ed.limit.used%(2),\
        emp.ed.chk.cat%(2),emp.ed.acct.no%(2), \
        emp.ed.desc$(3),emp.ed.factor(3),emp.ed.limit(3),\
        emp.ed.earn.ded$(3),emp.ed.exclusion%(3),\
        emp.ed.amt.percent$(3),emp.ed.limit.used%(3),\
        emp.ed.chk.cat%(3),emp.ed.acct.no%(3)

    return

1030    rem-----display employee status----------------------
    if last.emp.status$=emp.status$ \
        then    return
    last.emp.status$=emp.status$
    if emp.status$="A" \
        then    crt.data$(03)="ACTIVE    "      :\
            trash%=fn.lit%(03)        :\
            return
    if emp.status$="O" or emp.status$="L" \
        then    crt.data$(03)="ON-LEAVE  "      :\
            trash%=fn.lit%(03)        :\
            return
    if emp.status$="T" \
        then    crt.data$(03)="TERMINATED"      :\
            trash%=fn.lit%(03)        :\
            return
    if emp.status$="D" \
        then    crt.data$(03)="DELETED   "      :\
            trash%=fn.lit%(03)        :\
            return
    print "blooey":stop

1040    rem-----set up check record--------------------------
    chk.emp.no$=emp.no$
    chk.interval$=emp.pay.interval$
    chk.check.no$="NONE "
    for n%=1 to pr1.max.chk.cats%
        chk.amt(n%)=zero
    next n%
    return

1050    rem-----read matching history record-----------------
    read #his.file%,employee%+1;    \
Rem $include "ipyhis"
        his.emp.no$,\           rem   9/25/79
        his.qtd.income.taxable,his.qtd.other.taxable,\
        his.qtd.other.nontaxable,his.qtd.fica.taxable,\
        his.qtd.tips,his.qtd.net,his.qtd.eic,\
        his.qtd.fwt,his.qtd.swt,\
        his.qtd.lwt,his.qtd.fica,his.qtd.sdi,his.qtd.sys(1),\
        his.qtd.sys(2),his.qtd.sys(3),his.qtd.sys(4),his.qtd.sys(5),\
        his.qtd.emp(1),his.qtd.emp(2),his.qtd.emp(3),\
        his.qtd.other.ded,\
        his.qtd.units(1),his.qtd.units(2),\
        his.qtd.units(3),his.qtd.units(4),\
        his.ytd.income.taxable,his.ytd.other.taxable,\
        his.ytd.other.nontaxable,his.ytd.fica.taxable,\
        his.ytd.tips,his.ytd.net,his.ytd.eic,\
        his.ytd.fwt,his.ytd.swt,\
        his.ytd.lwt,his.ytd.fica,his.ytd.sdi,his.ytd.sys(1),\
        his.ytd.sys(2),his.ytd.sys(3),his.ytd.sys(4),his.ytd.sys(5),\
        his.ytd.emp(1),his.ytd.emp(2),his.ytd.emp(3),\
        his.ytd.other.ded,\
        his.ytd.units(1),his.ytd.units(2),\
        his.ytd.units(3),his.ytd.units(4)
    return

1060    rem-----process pay rec------------------------------
    gosub 1390            rem accumulate amt for his and chk
    gosub 2020            rem accumulate amt for coh and his
    return

1070    rem-----select a pay rec-----------------------------
    pay.rec%=pay.rec%+1
    gosub 1080            rem get pay rec
    if pay.eof% then return
    while not pay.extended%
        pay.rec%=pay.rec%+1
        gosub 1080        rem get pay rec
        if pay.eof% then return
    wend
    return

1080    rem-----get pay rec----------------------------------
    if pay.rec%>pay.hdr.no.recs% then pay.eof%=true%:return
    read #pay.file%,pay.rec%+1;    \
Rem $include "ipypay"
        pay.emp.no$,\           rem  9/25/79
        pay.eff.date$,\
        pay.interval$,\
        pay.apply.no%,\
        pay.reporting.cat%,\
        pay.units,\
        pay.amt,\
        pay.extended%
    return

1200    rem-----calculate gross and net----------------------
    gross=income.taxable+other.taxable+other.nontaxable+tips
    net=(gross+eic)-(fwt+swt+lwt+fica+sdi+other.ded)
    return

1300    rem-----distribute to acct table---------------------
    gosub 1310            rem determine distributable pay
    for x%=1 to pr1.max.dist.accts%
        if emp.dist.percent(x%)<>0 \
            then    dist.amt(x%)=        \
                   fn.round((emp.dist.percent(x%)/100)* \
                   distributable.pay)
    next x%
    gosub 1312            rem assure that dist amts are exact
    for x%=1 to pr1.max.dist.accts%
        acct.amt(emp.dist.acct%(x%))=acct.amt(emp.dist.acct%(x%))+\
            dist.amt(x%)
    next x%
    return

1310    rem-----determine distributable pay------------------
    distributable.pay=     \
        income.taxable        +\
        other.taxable        +\
        other.nontaxable
    if true% \
        then    distributable.pay=distributable.pay+ \
                employer.costs
    if true% \
        then    distributable.pay=distributable.pay+ \
                (tips-tips.reported)
    return

1312    rem-----assure that dist amts are exact--------------
    temp=0
    for x%=1 to pr1.max.dist.accts%
        temp=temp+dist.amt(x%)
    next x%
    if temp=distributable.pay \
        then    return
    temp=distributable.pay-temp    rem temp is difference
    x%=1
    while emp.dist.percent(x%)=0
        x%=x%+1
    wend
    dist.amt(x%)=dist.amt(x%)+temp
    return

1315    rem-----distribute offset amounts--------------------

rem
rem              DR               CR
rem    EARNINGS     DIST(+)          CASH(-)
rem    WITHHELD     CASH(+)       LIAB.ACCT(+)
rem    CO.COSTS     DIST(+)       LIAB.ACCT(+)
rem    EIC         LIAB(-)          CASH(-)
rem
rem    CASH acct is from PR1
rem    DIST accts are from EMP record
rem    LIAB accts are from EMP record and DED file
rem    EIC.CREDIT.ACCT is from DED file

rem CALCULATE EARNINGS:
    acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)-\
        (gross-tips.reported)

rem CALCULATE WITHHOLDING:
    acct.amt(ded.fwt.acct.no%)=acct.amt(ded.fwt.acct.no%)+fwt
    acct.amt(ded.swt.acct.no%)=acct.amt(ded.swt.acct.no%)+swt
    acct.amt(ded.lwt.acct.no%)=acct.amt(ded.lwt.acct.no%)+lwt
    acct.amt(ded.fica.acct.no%)=acct.amt(ded.fica.acct.no%)+fica
    acct.amt(ded.sdi.acct.no%)=acct.amt(ded.sdi.acct.no%)+sdi
    total.withheld=fwt+swt+lwt+fica+sdi
    for i%=1 to pr1.max.sys.eds%
        if ded.sys.earn.ded$(i%)="D" \
            then    acct.amt(ded.sys.acct.no%(i%))=     \
                acct.amt(ded.sys.acct.no%(i%))+sys(i%)    :\
                total.withheld=total.withheld+sys(i%)
    next i%
    for i%=1 to pr1.max.emp.eds%
        if emp.ed.earn.ded$(i%)="D" \
            then    acct.amt(emp.ed.acct.no%(i%))=        \
                acct.amt(emp.ed.acct.no%(i%))+emp(i%)    :\
                total.withheld=total.withheld+emp(i%)
    next i%
    acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)+\
        total.withheld

rem CALCULATE EIC:
    acct.amt(ded.eic.acct.no%)=acct.amt(ded.eic.acct.no%)-eic
    acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)-\
        eic

rem CALCULATE COMPANY COSTS:
    acct.amt(ded.co.fica.acct.no%)=acct.amt(ded.co.fica.acct.no%)+\
        co.fica
    acct.amt(ded.co.futa.acct.no%)=acct.amt(ded.co.futa.acct.no%)+\
        co.futa
    acct.amt(ded.co.sui.acct.no%)=acct.amt(ded.co.sui.acct.no%)+\
        co.sui
    return

1320    rem-----update history record------------------------
    net=(income.taxable+other.taxable+other.nontaxable+tips+eic)-    \
        (fwt+swt+lwt+fica+sdi+other.ded)
    his.qtd.income.taxable=his.qtd.income.taxable    +income.taxable
    his.qtd.other.taxable=his.qtd.other.taxable    +other.taxable
    his.qtd.other.nontaxable=his.qtd.other.nontaxable+other.nontaxable
    his.qtd.fica.taxable=his.qtd.fica.taxable    +fica.taxable
    his.qtd.tips=his.qtd.tips        +tips
    his.qtd.net=his.qtd.net     +net
    his.qtd.eic=his.qtd.eic     +eic
    his.qtd.fwt=his.qtd.fwt     +fwt
    his.qtd.swt=his.qtd.swt     +swt
    his.qtd.lwt=his.qtd.lwt     +lwt
    his.qtd.fica=his.qtd.fica    +fica
    his.qtd.sdi=his.qtd.sdi     +sdi
    his.qtd.other.ded=his.qtd.other.ded        +other.ded
    his.ytd.income.taxable=his.ytd.income.taxable    +income.taxable
    his.ytd.other.taxable=his.ytd.other.taxable    +other.taxable
    his.ytd.other.nontaxable=his.ytd.other.nontaxable+other.nontaxable
    his.ytd.fica.taxable=his.ytd.fica.taxable    +fica.taxable
    his.ytd.tips=his.ytd.tips        +tips
    his.ytd.net=his.ytd.net         +net
    his.ytd.eic=his.ytd.eic         +eic
    his.ytd.fwt=his.ytd.fwt         +fwt
    his.ytd.swt=his.ytd.swt         +swt
    his.ytd.lwt=his.ytd.lwt         +lwt
    his.ytd.fica=his.ytd.fica        +fica
    his.ytd.sdi=his.ytd.sdi         +sdi
    his.ytd.other.ded=his.ytd.other.ded    +other.ded
    for x%=1 to 5
        his.qtd.sys(x%)=his.qtd.sys(x%) +sys(x%)
        his.ytd.sys(x%)=his.ytd.sys(x%) +sys(x%)
    next x%
    for x%=1 to 3
        his.qtd.emp(x%)=his.qtd.emp(x%) +emp(x%)
        his.ytd.emp(x%)=his.ytd.emp(x%) +emp(x%)
    next x%
    for x%=1 to 4
        his.qtd.units(x%)=his.qtd.units(x%)    +units(x%)
        his.ytd.units(x%)=his.ytd.units(x%)    +units(x%)
    next x%
    return

1330    rem-----write history record-------------------------
    print #his.file%,employee%+1;     \
Rem $include "ipyhis"
        his.emp.no$,\           rem   9/25/79
        his.qtd.income.taxable,his.qtd.other.taxable,\
        his.qtd.other.nontaxable,his.qtd.fica.taxable,\
        his.qtd.tips,his.qtd.net,his.qtd.eic,\
        his.qtd.fwt,his.qtd.swt,\
        his.qtd.lwt,his.qtd.fica,his.qtd.sdi,his.qtd.sys(1),\
        his.qtd.sys(2),his.qtd.sys(3),his.qtd.sys(4),his.qtd.sys(5),\
        his.qtd.emp(1),his.qtd.emp(2),his.qtd.emp(3),\
        his.qtd.other.ded,\
        his.qtd.units(1),his.qtd.units(2),\
        his.qtd.units(3),his.qtd.units(4),\
        his.ytd.income.taxable,his.ytd.other.taxable,\
        his.ytd.other.nontaxable,his.ytd.fica.taxable,\
        his.ytd.tips,his.ytd.net,his.ytd.eic,\
        his.ytd.fwt,his.ytd.swt,\
        his.ytd.lwt,his.ytd.fica,his.ytd.sdi,his.ytd.sys(1),\
        his.ytd.sys(2),his.ytd.sys(3),his.ytd.sys(4),his.ytd.sys(5),\
        his.ytd.emp(1),his.ytd.emp(2),his.ytd.emp(3),\
        his.ytd.other.ded,\
        his.ytd.units(1),his.ytd.units(2),\
        his.ytd.units(3),his.ytd.units(4)
    return


1335    rem-----test amt against maximums--------------------
    if net>emp.max.pay \
        then    trash%=fn.emsg%(03)
    if net>pr1.void.check.amt and pr1.void.chks.over.max% \
        then    trash%=fn.emsg%(04)
    return

1340    rem-----generate check record------------------------
    chk.amt(01)=   \            rem GROSS
        chk.amt(02)        +\
        chk.amt(03)        +\
        chk.amt(04)        +\
        chk.amt(05)        +\
        chk.amt(06)        +\
        chk.amt(07)

    chk.amt(08)=   \            rem NET
        chk.amt(01)        -\
        (chk.amt(09)        +\
         chk.amt(10)        +\
         chk.amt(11)        +\
         chk.amt(12)        +\
         chk.amt(13)        +\
         chk.amt(14)        +\
         chk.amt(15)        +\
         chk.amt(16))
    if chk.amt(01)=0 and chk.amt(02)=0 and chk.amt(03)=0 and \
       chk.amt(04)=0 and chk.amt(05)=0 and chk.amt(06)=0 and \
       chk.amt(07)=0 and chk.amt(08)=0 and chk.amt(09)=0 and \
       chk.amt(10)=0 and chk.amt(11)=0 and chk.amt(12)=0 and \
       chk.amt(13)=0 and chk.amt(14)=0 and chk.amt(15)=0 and \
       chk.amt(16)=0     \
        then    return
    if chk.amt(08)<0 \        rem net
        then    trash%=fn.emsg%(05)    :\
            return
    chk.hdr.no.recs%=chk.hdr.no.recs%+1
    print #chk.file%,chk.hdr.no.recs%+1;    \
Rem $include "ipychk"
        chk.emp.no$,\          rem 8/21/79
        chk.interval$,\
        chk.check.no$,\
        chk.amt(01),chk.amt(02),chk.amt(03),chk.amt(04),\
        chk.amt(05),chk.amt(06),chk.amt(07),chk.amt(08),\
        chk.amt(09),chk.amt(10),chk.amt(11),chk.amt(12),\
        chk.amt(13),chk.amt(14),chk.amt(15),chk.amt(16)
    return

1390    rem-----accumulate amt for his and chk---------------
rem
rem    This routine will accumulate the pay.amt
rem    that has just been read in into the fields required for
rem    updating some of the fields on the HIS file and for
rem    updating the chk.amt fields on the CHK file.
rem    Accumulation is based on the value
rem    of the PAY.REPORTING.CAT% variable.
rem    Note that there is no rate zero, but all other valid
rem    rates are accumulated.
rem
    on pay.reporting.cat% gosub \
        1401,\            rem rate 01
        1401,\            rem rate 02
        1401,\            rem rate 03
        1401,\            rem rate 04
        1402,\            rem rate 05 vacation taken
        1403,\            rem rate 06 sick leave taken
        1404,\            rem rate 07 comp time taken
        1405,\            rem rate 08 comp time earnd
        1406,\            rem rate 09 bonus
        1406,\            rem rate 10 tips collected
        1406,\            rem rate 11 advance
        1406,\            rem rate 12 sick pay
        1406,\            rem rate 13 vacation pay
        1406,\            rem rate 14 other excld pay
        1406,\            rem rate 15 expense reimb
        1413,\            rem rate 16 eic
        1406,\            rem rate 17 other pay
        1419,\            rem rate 18 tips reported
        1420,\            rem rate 19
        1408,\            rem rate 20 fwt
        1409,\            rem rate 21 swt
        1410,\            rem rate 22 lwt
        1411,\            rem rate 23 fica
        1412,\            rem rate 24 sdi
        1420,\            rem rate 25
        1420,\            rem rate 26
        1406,\            rem rate 27 advance repay
        1408,\            rem rate 28 fwt addon
        1409,\            rem rate 29 swt addon
        1410,\            rem rate 30 lwt addon
        1411,\            rem rate 31 fica addon
        1420,\            rem rate 32
        1414,\            rem rate 33 sys1
        1414,\            rem rate 34 sys2
        1414,\            rem rate 35 sys3
        1414,\            rem rate 36 sys4
        1414,\            rem rate 37 sys5
        1415,\            rem rate 38 emp1
        1415,\            rem rate 39 emp2
        1415,\            rem rate 40 emp3
        1420,\            rem rate 41
        1416,\            rem rate 42 company fica
        1417,\            rem rate 43 company futa
        1418,\            rem rate 44 company sui
        1420,\            rem rate 45
        1420,\            rem rate 46 other co cost
        1420,\            rem rate 47
        1420,\            rem rate 48
        1420,\            rem rate 49
        1420            rem rate 50 other ded
    return

1401    rem-----rate 01,02,03,04-----------------------------
    units(pay.reporting.cat%)=units(pay.reporting.cat%)+pay.units
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    return

1402    rem-----rate 05 vacation taken-----------------------
    vac.taken=vac.taken+pay.units
    return
1403    rem-----rate 06 sick leave taken---------------------
    sl.taken=sl.taken+pay.units
    return
1404    rem-----rate 07 comp time taken----------------------
    comp.taken=comp.taken+pay.units
    return
1405    rem-----rate 08 comp time earned---------------------
    comp.earned=comp.earned+pay.units
    return

1406    rem-----rate 09 other normal pay types---------------
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    return

1408    rem-----rem rate 28 fwt addon------------------------
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    fwt=fwt+pay.amt
    return

1409    rem-----rem rate 29 swt addon------------------------
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    swt=swt+pay.amt
    return

1410    rem-----rem rate 30 lwt addon------------------------
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    lwt=lwt+pay.amt
    return

1411    rem-----rem rate 31 fica addon-----------------------
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    fica=fica+pay.amt
    return

1412    rem-----rem rate 24 sdi------------------------------
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    sdi=sdi+pay.amt
    return

1413    rem-----rem rate 16 eic------------------------------
    chk.amt(check.category%(pay.reporting.cat%))=  \
        chk.amt(check.category%(pay.reporting.cat%))+pay.amt
    eic=eic+pay.amt
    return

1414    rem-----rem sys eds----------------------------------
    chk.amt(ded.sys.chk.cat%(pay.reporting.cat%-32))=  \
        chk.amt(ded.sys.chk.cat%(pay.reporting.cat%-32))+pay.amt
    sys(pay.reporting.cat%-32)=sys(pay.reporting.cat%-32)+pay.amt
    return

1415    rem-----rem emp eds----------------------------------
    chk.amt(emp.ed.chk.cat%(pay.reporting.cat%-37))=  \
        chk.amt(emp.ed.chk.cat%(pay.reporting.cat%-37))+pay.amt
    emp(pay.reporting.cat%-37)=emp(pay.reporting.cat%-37)+pay.amt
    return

1416    rem-----rem rate 42 co fica--------------------------
    co.fica=co.fica+pay.amt
    employer.costs=employer.costs+pay.amt
    return

1417    rem-----rem rate 43 co futa--------------------------
    co.futa=co.futa+pay.amt
    employer.costs=employer.costs+pay.amt
    return

1418    rem-----rem rate 44 co sui---------------------------
    co.sui=co.sui+pay.amt
    employer.costs=employer.costs+pay.amt
    return

1419    rem-----tips reported--------------------------------
    gosub 1406            rem tips collected
    temp%=pay.reporting.cat%
    pay.reporting.cat%=10
    gosub 1406            rem tips
    pay.reporting.cat%=temp%
    return

1420    rem-----invalid rates--------------------------------
    print "blooooey"
    stop

2020    rem-----accumulate pay amt for coh and his-----------
rem
rem    This rtn accumulates pay amounts in
rem    their proper accumulators for updating the COH file and some
rem    of the fields on the HIS file.
rem
rem    The following are the accumulators to be used:
rem        income.taxable
rem        other.taxable
rem        other.nontaxable
rem        fica.taxable      (does not include tips)
rem        tips collected
rem        tips reported
rem
rem    gross pay  = income.taxable+other.taxable+other.nontaxable+tips
rem
rem    accumulation codes are as follows:
rem        2030 - do not accumulate
rem        2040 - income.taxable,fica.taxable    (exclusion type 1)
rem        2050 - income.taxable            (exclusion type 2)
rem        2060 - other.taxable,fica.taxable    (exclusion type 3)
rem        2070 - other.nontaxable         (exclusion type 4)
rem        2080 - by applicable exclusion type as above
rem        2090 - tips collected
rem        2100 - tips reported
rem
    on pay.reporting.cat% gosub \
        2040,    \ (01)="REGULAR PAY"
        2040,    \ (02)="OVERTIME PAY"       \ from PR1 file
        2040,    \ (03)="SPECIAL OT PAY"     \ from PR1 file
        2080,    \ (04)="COMMISSION"         \ from PR1 file
        2030,    \ (05)="VACATION TAKEN"
        2030,    \ (06)="SICK LVE TAKEN"
        2030,    \ (07)="COMP TIME TAKEN"
        2030,    \ (08)="COMP TIME EARND"
        2040,    \ (09)="BONUS"
        2090,    \ (10)="TIPS COLLECTED"
        2030,    \ (11)="ADVANCE"
        2040,    \ (12)="SICK PAY"
        2040,    \ (13)="VACATION PAY"
        2070,    \ (14)="OTHER EXCLD PAY"
        2030,    \ (15)="EXPENSE REIMB"
        2030,    \ (16)="EIC"
        2040,    \ (17)="OTHER PAY"
        2100,    \ (18)="TIPS REPORTED"
        2030,    \ (19)=""
        2030,    \ (20)="FWT"
        2030,    \ (21)="SWT"
        2030,    \ (22)="LWT"
        2030,    \ (23)="FICA"
        2030,    \ (24)="SDI"
        2030,    \ (25)=""
        2030,    \ (26)=""
        2030,    \ (27)="ADVANCE REPAY"
        2030,    \ (28)="FWT ADD-ON"
        2030,    \ (29)="SWT ADD-ON"
        2030,    \ (30)="LWT ADD-ON"
        2030,    \ (31)="FICA ADD-ON"
        2030,    \ (32)=""
        2080,    \ (33)="SYS1"          \  from sys1
        2080,    \ (34)="SYS2"          \  from sys2
        2080,    \ (35)="SYS3"          \  from sys3
        2080,    \ (36)="SYS4"          \  from sys4
        2080,    \ (37)="SYS5"          \  from sys5
        2080,    \ (38)="EMP1"          \  from emp1
        2080,    \ (39)="EMP2"          \  from emp2
        2080,    \ (40)="EMP3"          \  from emp3
        2030,    \ (41)=""
        2030,    \ (42)="COMPANY FICA"
        2030,    \ (43)="COMPANY FUTA"
        2030,    \ (44)="COMPANY SUI"
        2030,    \ (45)=""
        2030,    \ (46)="OTHER CO COST"
        2030,    \ (47)=""
        2030,    \ (48)=""
        2030,    \ (49)=""
        2030    rem  (50)="OTHER DED"
    return

2030    rem-----do not accumulate----------------------------
    return

2040    rem-----income.taxable,fica.taxable-type 1-----------
    if emp.fwt.exempt% and emp.fica.exempt% \
        then    goto 2070    rem totally exempt (type 4)
    if emp.fwt.exempt% \
        then    goto 2060    rem FED exempt (type 3)
    if emp.fica.exempt% \
        then    goto 2050    rem SOC SEC exempt (type 2)
    income.taxable=income.taxable+pay.amt
    fica.taxable=fica.taxable+pay.amt
    return

2050    rem-----income.taxable-type 2------------------------
    income.taxable=income.taxable+pay.amt
    return

2060    rem-----other.taxable,fica.taxable-type 3------------
    other.taxable=other.taxable+pay.amt
    fica.taxable=fica.taxable+pay.amt
    return

2070    rem-----other.nontaxable-type 4----------------------
    other.nontaxable=other.nontaxable+pay.amt
    return

2080    rem-----by applicable exclusion type as above--------
    if pay.reporting.cat%=4 \
        then    exclusion.type%=emp.rate4.exclusion% :\
            gosub 2110   :\     rem accumulate
            return
    if pay.reporting.cat%>=33 and \
       pay.reporting.cat%<=37     \
        then    gosub 2082   :\     rem do sys ed
            return
    if pay.reporting.cat%>=38 and \
       pay.reporting.cat%<=40     \
        then    gosub 2084   :\     rem do emp ed
            return
    print "bloooey"
    stop

2082    rem-----do sys ed-----------------------------------
    if ded.sys.earn.ded$(pay.reporting.cat%-32)="E" \
        then    exclusion.type%=ded.sys.exclusion%    \
                (pay.reporting.cat%-32)     :\
            gosub 2110    \     rem accumulate
        else    other.ded=other.ded+pay.amt
    return

2084    rem-----do emp ed-----------------------------------
    if emp.ed.earn.ded$(pay.reporting.cat%-37)="E" \
        then    exclusion.type%=emp.ed.exclusion%    \
                (pay.reporting.cat%-37)     :\
            gosub 2110    \     rem accumulate
        else    other.ded=other.ded+pay.amt
    return

2090    rem-----tips collected-------------------------------
    tips=tips+pay.amt
    return

2100    rem-----tips reported--------------------------------
    tips=tips+pay.amt
    tips.reported=tips.reported+pay.amt
    other.ded=other.ded+pay.amt
    return

2110    rem-----accumulate-----------------------------------
    on exclusion.type% gosub \
        2040,\        rem type 1
        2050,\        rem type 2
        2060,\        rem type 3
        2070        rem type 4
    return
