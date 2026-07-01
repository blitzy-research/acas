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
prgname$="APPLY1     JAN. 16, 1980 "
rem----------------------------------------------------------
rem
rem    A  P  P  L  Y  1
rem
rem        S E T U P
rem
rem    SECTION ONE OF PAYROLL CALCULATION PROGRAM
rem
rem    P A Y R O L L       S Y S T E M
rem
rem    COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="APPLY1"
function.name$="PAYROLL APPLICATION -- SECTION ONE"

Rem $include "ipyconst"
rem     JAN. 18, 1980
system$="PY":version$=" REL:1.0 "
system.name$="PAYROLL SYSTEM"
cpyrght$="COPYRIGHT (C) 1980, APPLEWOOD COMPUTERS "
dummy$="PYppppI00":null$="":asc.quote%= 34
dim crt.data$(0),crt.x%(0),crt.y%(0),crt.len%(0),crt.rd%(0),crt.attrib%(0)
Rem $include "zfilconv"
rem 22-oct-79 CPM FILE NAME FUNCTIONS
    def fn.drive.in%(temp$)
        fn.drive.in% = -1
        if len(temp$) <> 1 then return
        temp$=ucase$(temp$)
        if temp$ <> "@" and     \
           (temp$ > "D" or temp$ < "A")\
            then return
        if temp$ = "@"          \
            then fn.drive.in% = 0    \
            else fn.drive.in% = asc(temp$) - asc("A") + 1
        return
    fend
    def fn.drive.out$(temp%)
        if temp% = 0    \
            then fn.drive.out$ = "@"        \
            else fn.drive.out$ = chr$(asc("A") + temp% - 1)
        return
    fend
    def fn.file.name.out$(c.name$,c.type$,c.drive%,c.password$,c.params$)=\
        fn.drive.out$(c.drive%)+":"+c.name$+"."+c.type$
Rem $include "zdms"
rem    Nov.  8, 1979         -----------------------------------
rem
rem    all functions needed for  DMS  except CRT characteristics definition
rem    and screen attribute and clear functions
rem
rem-------------------------------------------------------------
Rem #include zdmssca
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
Rem #include zdmsmsg
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
Rem #include zdmsemsg
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
Rem #include zdmslit
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
Rem #include zdmsput
rem    DEC. 02, 1979   --------------------------------------------------
rem
   def fn.put%(value$,id%)    REM STANDARD
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
50005.1 \    monetary data
    crt.num = val(value$)
    crt.l.d%=len(str$(abs(int(crt.num))))
    crt.temp%= len(crt.brkt.fmt$(crt.len%(id%)))+ \
        len(crt.brkt.rd.fmt$(crt.rd%(id%)))
    if crt.num < 0    \
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
Rem #include zdmsptal
rem    NOV. 13, 1979           ----------------------------------------------
rem
rem    fn.put.all%(i.o%)    REM STANDARD
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
Rem #include zdmsget
rem----- DEC. 28, 1979 --------------------------------------------------------
rem
rem    fn.get%(mask%, id%)        REM STANDARD
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
        if crt.data% = crt.key.prefix%    and not crt.key% \
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
      then    in.uc$= ucase$(in$): in.status%= req.valid%
    if crt.msg.issued% then trash%= fn.msg%(""): crt.msg.issued%= false%\
               else print using"&";crt.background$;
    return
    fend
rem--------------------------------------------------------------
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

dim emsg$(25)
emsg$(01)="PY501 INVALID DATE"
emsg$(02)="PY502 CHECK DATE IS NOT IN CURRENT QUARTER"
emsg$(03)="PY503 CHECK DATE IS NOT IN CURRENT YEAR"
emsg$(04)="PY504 MUST BE M OR W"
emsg$(05)="PY505 CURRENT CHECKS NOT PRINTED"
emsg$(06)="PY506 CHECK DATE EARLIER THAN PREVIOUS CHECK DATE"
emsg$(07)="PY507 PYPAY.100 FOUND"
emsg$(08)="PY508 CURRENT PAYROLL JOURNAL NOT PRINTED"
emsg$(09)="PY509 EMP FILE NOT FOUND"
emsg$(10)="PY510 DED FILE NOT FOUND"
emsg$(11)="PY511 SWT OR CALx FILE NOT FOUND"
emsg$(12)="PY512 LWT FILE NOT FOUND"
emsg$(13)="PY513 HIS FILE NOT FOUND"
emsg$(14)="PY514 YES, ESCAPE OR BACK ONLY"
emsg$(15)="PY515 ACT FILE NOT FOUND"
emsg$(16)="PY516 PR2 FILE NOT FOUND"
emsg$(17)="PY517 YES OR ESCAPE ONLY"
emsg$(18)="PY518 YES OR ESCAPE ONLY"
emsg$(19)="PY519 CAN'T APPLY.  QUARTER NEEDS ENDING"
emsg$(20)="PY520 CAN'T APPLY.  QUARTER NEEDS ENDING"
emsg$(21)="PY521 CAN'T APPLY.  YEAR NEEDS ENDING"
emsg$(22)="PY522 CURRENT REGISTER NOT PRINTED"
emsg$(23)="PY523 CHK.100 FILE FOUND"

Rem $include "zdmsconf"
REM     DEC. 14, 1979 ------------------------
REM
def fn.confirmed%        REM STANDARD
REM
REM--------------------------------------------
%nolist
fn.confirmed%=false%
crt.col%= 30: crt.row%= 20
crt.continue$="(TYPE ""RUN"" TO CONTINUE)"
crt.stop$="(TYPE ""STOP"" TO STOP PROGRAM)"
console
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);crt.stop$
print using "&";fn.crt.sca$(crt.row%, crt.col%);crt.continue$;
if pr1.leading.crlf% then print
crt.done%= false%
crt.count%= 0
crt.current$= null$
while not crt.done%
    crt.print%= false%
    crt.data%= conchar%
    crt.count%= crt.count%+ 1
    crt.char$= ucase$(chr$(crt.data%))
    crt.data%= asc(crt.char$)
    if crt.count%= 1 and crt.char$="S" \
        then crt.current$="STOP"+chr$(asc.cr%)
    if crt.count%= 1 and crt.char$="R" \
        then crt.current$="RUN"+chr$(asc.cr%)
    if crt.current$<> null$ \
        then crt.cur.char%= asc(mid$(crt.current$,crt.count%,1)) \
        else crt.cur.char%= -1
    if crt.data%= asc.del% or crt.data%= asc.lspace% \
        then crt.count%= crt.count%- 1
    if (crt.data%= asc.lspace% or crt.data%= asc.del%) and crt.count% > 0 \
        then  print using "&";fn.crt.sca$ \
        (crt.row%, crt.col%+len(crt.continue$)+crt.count%); \
        crt.backspace$; :crt.count%=crt.count%-1: crt.print%=true%
    if crt.data%<> crt.cur.char% and  \
        crt.data% <> asc.lspace% and crt.data%<> asc.del% \
        then trash%= fn.msg%(bell$+system$+"019 TYPE ""RUN"" OR TYPE ""STOP"""):\
        print using "&";fn.crt.sca$(crt.row%, \
        crt.col%+len(crt.continue$)+crt.count%);crt.backspace$;: \
        crt.count%= crt.count%-1: crt.print%= true%
    if pr1.leading.crlf% and crt.print%  then print
    if crt.count%= len(crt.current$) and crt.count%> 0 then crt.done%=true%
wend
if crt.count%= len("RUN")+1  then fn.confirmed%=true%
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);left$(blank$,len(crt.stop$))
print using "&";fn.crt.sca$(crt.row%, crt.col%);left$(blank$,len(crt.continue$)+5)
return
fend
%list
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
Rem $include "zparse"
rem    Feb. 28, 1979
def fn.parse%(data$,delim$)
    goto .0071
.700    rem-----dim.1------------------------------
    dim.1%=true%
    if token.limit%=0 then token.limit%=5
    dim token$(token.limit%)
    return
.0071    if not dim.1% then gosub .700
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
Rem $include "znumber"
rem    Jan. 13, 1979
def fn.num%(no$)
    if match(left$(pound$,len(no$)),no$,1)<>1 and len(no$)>0 \
        then   fn.num%=false% \
        else   fn.num%=true%
    return
fend

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

Rem $include "zeditdte"
rem      May  10, 1979
rem requires: zparse, znum
def fn.leap.year%(year%)
    if (year%/4.0)-int%(year%/4.0)=0 \
        then   fn.leap.year%=true% \
        else   fn.leap.year%=false%
    return
fend

def fn.edit.date%(date$)            rem parameter file date
    fn.edit.date%=false%            rem information must be
    if fn.parse%(date$,"/")<>3 then return  rem initialized for this
    for xx2%=1 to 3                 rem function to
      if not fn.num%(token$(xx2%)) then return    rem work
    next xx2%                    rem correctly
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


Rem $include "zdateinc"
rem-----ZDATEINC--10/25/79------------------------------------

def fn.decompose.date%(date$)
    dy%=val(mid$(date$,5,2))
    mo%=val(mid$(date$,3,2))
    yr%=val(mid$(date$,1,2))
    return
fend

def fn.last.day%(mo%,yr%)
    if mo%=1 or mo%=3 or mo%=5 or mo%=7 or mo%=8 or mo%=10 or mo%=12 \
        then    fn.last.day%=31:return
    if mo%=4 or mo%=6 or mo%=9 or mo%=11 \
        then    fn.last.day%=30:return
    if fn.leap.year%(yr%)  \
        then    fn.last.day%=29  \
        else    fn.last.day%=28
    return
fend

def fn.incr.year%(xx8%)
    xx8%=xx8%+1
    if xx8%>99 then xx8%=0
    fn.incr.year%=xx8%
    return
fend
def fn.incr.month%(xx9%)
    xx9%=xx9%+1
    if xx9%>12 \
        then    xx9%=1    :\
            yr%=fn.incr.year%(yr%)
    fn.incr.month%=xx9%
    return
fend
def fn.incr.date$(date$,bump%)
    trash%=fn.decompose.date%(date$)
    while bump%>0
        bump%=bump%-1
        dy%=dy%+1
        if dy%>fn.last.day%(mo%,yr%) \
            then    dy%=1  :\
                mo%=fn.incr.month%(mo%)
    wend
    fn.incr.date$=fn.date.in$
    return
fend
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
Rem $include "ipydmhis"
dim his.qtd.sys         (pr1.max.sys.eds%)    rem  9/26/79
dim his.qtd.emp         (pr1.max.emp.eds%)
dim his.qtd.units        (4)
dim his.ytd.sys         (pr1.max.sys.eds%)
dim his.ytd.emp         (pr1.max.emp.eds%)
dim his.ytd.units        (4)
Rem $include "ipydmchk"
dim chk.amt        (pr1.max.chk.cats%)         rem  9/12/79
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
Rem $include "ipydmswt"
dim withhold.deduction.amount(5)    rem 11/12/79
dim withhold.num.entries%(5)
dim withhold.cutoff(pr1.max.swt.entries%,5)
dim withhold.percent(pr1.max.swt.entries%,5)
Rem $include "ipydmcal"
dim cal.low.income.exempt    (04)      rem  09/29/79
dim cal.standard.deduction    (04)
dim cal.tax.credit        (10,02)
Rem $include "fpyap1"            rem define screen info
rem---------------------------------------------------------
rem    SET UP DMS SCREEN EQUATES    FPYAP1 - 12/21/79

crt.field.count% = 25        rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem    LEGEND:    X  Y  LEN  RD  ATTRIB
rem        STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data           \
      67,3,12,0,17,\       rem   IO fld #1
      16,10,55,0,17,\    rem   IO fld #2
      16,11,55,0,17,\    rem   IO fld #3
      42,9,5,0,17,\       rem   IO fld #4
      48,9,27,0,17,\       rem   IO fld #5
      38,13,8,0,17,\       rem   IO fld #6
      49,13,8,0,25,\       rem   IO fld #7
      60,13,1,0,25,\       rem   IO fld #8
      25,21,30,0,17,\    rem   IO fld #9
      65,15,3,0,25,\       rem   IO fld #10
      45,12,8,0,17,\       rem   IO fld #11
      1,2,9,0,4,\        rem   O fld #12
      1,3,8,0,4,\        rem   O fld #13
      10,3,8,0,4,\         rem   O fld #14
      12,9,30,0,0,\       rem   O fld #15
      20,13,38,0,0,\       rem   O fld #16
      16,13,46,0,0,\       rem   O fld #17
      18,15,42,0,0,\       rem   O fld #18
      10,15,61,0,0,\       rem   O fld #19
      17,23,43,0,0,\       rem   O fld #20
      15,23,47,0,0,\       rem   O fld #21
      21,23,36,0,0,\       rem   O fld #22
      10,15,61,0,0,\       rem   O fld #23
      25,12,19,0,0,\       rem   O fld #24
      1,1,8,0,4
      rem    O fld #25
crt.data$(15)="THE CURRENT EXTENSION INTERVAL"
crt.data$(16)="ENTER CHECK DATE (        ) [        ]"
crt.data$(17)="APPLY WHICH INTERVAL BASE (M=MONTH;W=WEEK) [ ]"
crt.data$(18)="EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
crt.data$(19)="IF ALL EXTENSION PARAMETERS ARE CORRECT, TYPE ""YES""   [   ]"
crt.data$(20)="NO CURRENT PAY TRANSACTION (HRS) FILE FOUND"
crt.data$(21)="THE CURRENT HRS BATCH FILE HAS NOT BEEN PROOFED"
crt.data$(22)="THE CURRENT COH FILE CANNOT BE FOUND"
crt.data$(23)="IF YOU WISH TO CONTINUE THE APPLICATION, TYPE ""YES""   [   ]"
crt.data$(24)="CURRENT CHECK DATE:"

i%=1
while i%<=25
  read    crt.x%(i%),crt.y%(i%),\
    crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(system.name$)<=30 \
  then     sys.name$=fn.spread$(system.name$,1)  \
  else     sys.name$=system.name$
crt.len%(12)=len(sys.name$)
crt.x%(12)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(12)=sys.name$
crt.data$(13)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then     fun.name$=fn.spread$(function.name$,1)  \
  else     fun.name$=function.name$
crt.len%(14)=len(fun.name$)
crt.x%(14)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(14)=fun.name$
if len(pr1.co.name$)<=30 \
  then     co.name$=fn.spread$(pr1.co.name$,1)  \
  else     co.name$=pr1.co.name$
crt.len%(25)=len(co.name$)
crt.x%(25)=fn.center%(co.name$,crt.columns%-2)
crt.data$(25)=co.name$

rem---------------------------------------------------------

def fn.quarter%(date$)
    trash%=fn.decompose.date%(date$)
    if mo%=01 or mo%=02 or mo%=03 then fn.quarter%=1:return
    if mo%=04 or mo%=05 or mo%=06 then fn.quarter%=2:return
    if mo%=07 or mo%=08 or mo%=09 then fn.quarter%=3:return
    if mo%=10 or mo%=11 or mo%=12 then fn.quarter%=4:return
fend

def fn.in%(mask%,id%)
    cr%=false%:stopit%=false%:back%=false%:cancel%=false%
    getnext%=false%:save%=false%:adding%=false%:deleteit%=false%
    fn.in%=fn.get%(mask%,id%)
    if in.status%=req.valid% then valid.data%=true%:return
    if in.status%=req.cr% then cr%=true%:return
    if in.status%=req.stopit% then stopit%=true%:return
    if in.status%=req.back% then back%=true%:return
    if in.status%=req.cancel% then cancel%=true%:return
    if in.status%=req.next% then getnext%=true%:return
    if in.status%=req.save% then save%=true%:return
    if in.status%=req.adding% then adding%=true%:return
    if in.status%=req.delete% then deleteit%=true%:return
    print "baloney":stop
fend

dim dd$(3)
def fn.date.format$
    dd$(pr1.date.mo%)="MM":dd$(pr1.date.yr%)="YY":dd$(pr1.date.dy%)="DD"
    fn.date.format$=dd$(1)+"/"+dd$(2)+"/"+dd$(3)
    return
fend

def fn.odd%(temp%)
    if int%(temp%/2)*2=temp% then fn.odd%=false% else fn.odd%=true%
    return
fend

rem----------------------------------------------------------
rem
rem    S E T        U P
rem
rem----------------------------------------------------------

gosub 200        rem display.set.up.screen

100

rem----------------------------------------------------------
    null$=                ""
    interval$=            null$
    extension.intervals$=        null$
    from.slow.date$=        "000000"
    from.fast.date$=        "000000"
    to.date$=            "000000"
    week.based%=            false%
    month.based%=            false%
    apply.no%=            0
    month.from.date$=        "000000"
    semimonth.from.date$=        "000000"
    biweek.from.date$=        "000000"
    week.from.date$=        "000000"
    apply.incremented%=        false%
rem----------------------------------------------------------

new.m.date$=pr2.last.day.of.last.m$
new.s.date$=pr2.last.day.of.last.s$
new.w.date$=pr2.last.day.of.last.w$
new.b.date$=pr2.last.day.of.last.b$
new.last.wb.apply.no%=pr2.last.wb.apply.no%
new.last.sm.apply.no%=pr2.last.sm.apply.no%
new.no.of.wb.applies%=pr2.no.of.wb.applies%
new.no.of.sm.applies%=pr2.no.of.sm.applies%

rem----------------------------------------------------------
rem
rem    M A I N       D R I V E R
rem
rem----------------------------------------------------------

gosub 210            rem can.we.run
if not ok% then goto 999.1

back%=false%
gosub 220            rem determine base
if stopit% then goto 999.2
if back% then goto 100

gosub 1000            rem determine if period needs ending
if not ok% then goto 999.1

gosub 237            rem determine apply no
gosub 239            rem get interval$
gosub 240            rem display apply no
gosub 250            rem display extension intervals
gosub 260            rem display last days of extension intervals

gosub 270            rem request confirmation
if stopit% then goto 999.2
if back% \
    then    trash%=fn.clr%(01)        :\
        trash%=fn.clr%(02)        :\
        trash%=fn.clr%(03)        :\
        trash%=fn.clr%(04)        :\
        trash%=fn.clr%(05)        :\
        trash%=fn.clr%(15)        :\
        goto 100    rem start over again
110
gosub 290            rem request.check.date
if stopit% then goto 999.2
if back% then goto 100
trash%=fn.lit%(24)        rem CURRENT CHECK DATE:
trash%=fn.put%(fn.date.out$(check.date$),11)

gosub 300            rem determine proper quarter/year
if not ok% then goto 110

gosub 500            rem set up files
gosub 330            rem display.process.screen

rem----------------------------------------------------------
rem
rem    E N D      O F      J O B
rem
rem----------------------------------------------------------

pr2.check.date$=check.date$
pr2.last.day.of.last.m$=new.m.date$
pr2.last.day.of.last.s$=new.s.date$
pr2.last.day.of.last.w$=new.w.date$
pr2.last.day.of.last.b$=new.b.date$
pr2.last.sm.apply.no%=new.last.sm.apply.no%
pr2.last.wb.apply.no%=new.last.wb.apply.no%
pr2.no.of.wb.applies%=new.no.of.wb.applies%
pr2.no.of.sm.applies%=new.no.of.sm.applies%
gosub 850            rem rewrite pr2 file
gosub 870            rem delete hrs.001 if needed
trash%=fn.clr%(09)        rem clear row 21 on screen
trash%=fn.clr%(21)        rem clear row 23 on screen

common.chaining.status$=common.chaining.status$+in.apply$

chain fn.file.name.out$("APPLY2",null$,0,pw$,pms$)

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
    trash%=fn.put.all%(false%)
    return

210    rem-----can we run?----------------------------------
    ok%=true%
    return

220    rem-----determine base-------------------------------
    extension.intervals$=null$
    intervals%=0
    if pr1.m.used% then intervals%=intervals%+1
    if pr1.s.used% then intervals%=intervals%+2
    if pr1.w.used% then intervals%=intervals%+4
    if pr1.b.used% then intervals%=intervals%+8
    on intervals% gosub \
        221,\            rem M
        222,\            rem S
        223,\            rem MS
        224,\            rem W
        225,\            rem MW
        226,\            rem SW
        227,\            rem MSW
        228,\            rem B
        229,\            rem MB
        230,\            rem SB
        231,\            rem MSB
        232,\            rem WB
        233,\            rem MWB
        234,\            rem SWB
        235            rem MSWB
    if month.based% \
        then    from.slow.date$=month.from.date$ :\
            from.fast.date$=semimonth.from.date$ \
        else    from.slow.date$=biweek.from.date$ :\
            from.fast.date$=week.from.date$
    if pr1.debugging% then trash%=fn.put%  \
        ("EXTNSN INTRVLS: "+extension.intervals$,09)
    return

221    rem-----M--------------------------------------------
    month.based%=true%
    trash%=fn.decompose.date%(pr2.last.day.of.last.m$)
    mo%=fn.incr.month%(mo%)
    dy%=fn.last.day%(mo%,yr%)
    new.m.date$=fn.date.in$
    month.from.date$=fn.incr.date$(pr2.last.day.of.last.m$,1)
    if not apply.incremented% \
        then    new.last.sm.apply.no%=pr2.last.sm.apply.no%+2 :\
            new.no.of.sm.applies%=new.no.of.sm.applies%+2 :\
            to.date$=new.m.date$    :\
            apply.incremented%=true%
    extension.intervals$=extension.intervals$+"M"
    return

222    rem-----S--------------------------------------------
    month.based%=true%
    trash%=fn.decompose.date%(pr2.last.day.of.last.s$)
    if dy%=fn.last.day%(mo%,yr%) \
        then    mo%=fn.incr.month%(mo%)     :\
            dy%=15                 \
        else    dy%=fn.last.day%(mo%,yr%)
    new.s.date$=fn.date.in$
    semimonth.from.date$=fn.incr.date$(pr2.last.day.of.last.s$,1)
    if not apply.incremented% \
        then    new.last.sm.apply.no%=pr2.last.sm.apply.no%+1 :\
            new.no.of.sm.applies%=new.no.of.sm.applies%+1 :\
            to.date$=new.s.date$    :\
            apply.incremented%=true%
    extension.intervals$=extension.intervals$+"S"
    return

223    rem-----MS-------------------------------------------
    month.based%=true%

rem  if the last apply no is odd, this apply no is even and vice versa
rem  if the last apply is odd, now apply BOTH S and M, if last was
rem    even, now apply only S.

    if fn.odd%(pr2.last.sm.apply.no%) \
        then    gosub 222 :\    rem S
            gosub 221  \    rem M
        else    gosub 222    rem S
    return

224    rem-----W--------------------------------------------
    week.based%=true%
    new.w.date$=fn.incr.date$(pr2.last.day.of.last.w$,7)
    week.from.date$=fn.incr.date$(pr2.last.day.of.last.w$,1)
    if not apply.incremented% \
        then    new.last.wb.apply.no%=pr2.last.wb.apply.no%+1 :\
            new.no.of.wb.applies%=new.no.of.wb.applies%+1 :\
            to.date$=new.w.date$    :\
            apply.incremented%=true%
    extension.intervals$=extension.intervals$+"W"
    return

225    rem-----MW-------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 224 :\    rem W
        else    gosub 221    rem M
    return

226    rem-----SW-------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 224 :\    rem W
        else    gosub 222    rem S
    return

227    rem-----MSW------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 224 :\    rem W
        else    gosub 223    rem MS
    return

228    rem-----B--------------------------------------------
    week.based%=true%
    new.b.date$=fn.incr.date$(pr2.last.day.of.last.b$,14)
    biweek.from.date$=fn.incr.date$(pr2.last.day.of.last.b$,1)
    if not apply.incremented% \
        then    new.last.wb.apply.no%=pr2.last.wb.apply.no%+2 :\
            new.no.of.wb.applies%=new.no.of.wb.applies%+2 :\
            to.date$=new.b.date$    :\
            apply.incremented%=true%
    extension.intervals$=extension.intervals$+"B"
    return

229    rem-----MB-------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 228 :\    rem B
        else    gosub 221    rem M
    return

230    rem-----SB-------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 228 :\    rem B
        else    gosub 222    rem S
    return

231    rem-----MSB------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 228 :\    rem B
        else    gosub 223    rem MS
    return

232    rem-----WB-------------------------------------------
    week.based%=true%

rem  if the last apply no is odd, this apply no is even and vice versa
rem  if the last apply is odd, now apply BOTH W and B, if last was
rem    even, now apply only W.

    if fn.odd%(pr2.last.wb.apply.no%) \
        then    gosub 224 :\    rem W
            gosub 228  \    rem B
        else    gosub 224    rem W
    return

233    rem-----MWB------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 232 :\    rem WB
        else    gosub 221    rem M
    return

234    rem-----SWB------------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 232 \    rem WB
        else    gosub 222    rem S
    return

235    rem-----MSWB-----------------------------------------
    gosub 370            rem request base
    if stopit% or back% then return
    if week.based% \
        then    gosub 232 \    rem WB
        else    gosub 223    rem MS
    return

237    rem-----determine apply no---------------------------
    if week.based% \
        then    apply.no%=new.last.wb.apply.no% \
        else    apply.no%=new.last.sm.apply.no%
    return

239    rem-----get interval$--------------------------------
    if len(extension.intervals$)=1 \
        then    interval$=extension.intervals$    :\
            return
    if match("W",extension.intervals$,1)<>0 and      \
       match("B",extension.intervals$,1)<>0          \
        then    interval$="B"                   :\
            return
    if match("M",extension.intervals$,1)<>0 and      \
       match("S",extension.intervals$,1)<>0          \
        then    interval$="M"                   :\
            return
    print "death rattle"
    stop

240    rem-----display apply no-----------------------------
    trash%=fn.put%("APPLY NO:"+str$(apply.no%),1)   rem upper right corner
    return

250    rem-----display extension intervals------------------
    trash%=fn.lit%(15)    rem    "CURRENT EXTENSION INTERVAL"
    if len(extension.intervals$)=1 \
        then    trash%=fn.put%(" IS",4)    \
        else    trash%=fn.put%("S ARE",4)
    out$=null$
    if match("M",extension.intervals$,1)<>0 \
        then    out$=out$+" AND MONTHLY"
    if match("S",extension.intervals$,1)<>0 \
        then    out$=out$+" AND SEMI-MONTHLY"
    if match("W",extension.intervals$,1)<>0 \
        then    out$=out$+" AND WEEKLY"
    if match("B",extension.intervals$,1)<>0 \
        then    out$=out$+" AND BI-WEEKLY"
    out$=right$(out$,len(out$)-5)
    trash%=fn.put%(out$,5)
    return

260    rem-----display last days of extension intervals-----
rem        CURRENT WEEK IS FROM MM/DD/YY THROUGH MM/DD/YY
rem        CURRENT SEMI-MONTH IS FROM MM/DD/YY THROUGH MM/DD/YY
    if match("M",extension.intervals$,1)<>0 \
        then    trash%=fn.put%                \
            ("CURRENT MONTH IS FROM "+              \
            fn.date.out$(month.from.date$)+     \
            " THROUGH "+fn.date.out$(to.date$),2)
    if match("S",extension.intervals$,1)<>0 \
        then    trash%=fn.put%                \
            ("CURRENT SEMI MONTH IS FROM "+          \
            fn.date.out$(semimonth.from.date$)+    \
            " THROUGH "+fn.date.out$(to.date$),3)
    if match("W",extension.intervals$,1)<>0 \
        then    trash%=fn.put%                \
            ("CURRENT WEEK IS FROM "+               \
            fn.date.out$(week.from.date$)+        \
            " THROUGH "+fn.date.out$(to.date$),2)
    if match("B",extension.intervals$,1)<>0 \
        then    trash%=fn.put%                \
            ("CURRENT BIWEEK IS FROM "+             \
            fn.date.out$(biweek.from.date$)+    \
            " THROUGH "+fn.date.out$(to.date$),3)
    return

270    rem-----request confirmation-------------------------
    trash%=fn.lit%(19)
271
    trash%=fn.in%(2,10)        rem get a yes or no
    if stopit% or back% \
        then    trash%=fn.clr%(19)    :\
            return
    if in.uc$<>"YES" \
        then    trash%=fn.emsg%(14)    :\
            trash%=fn.put%(null$,10)    :\
            goto 271    rem retry
    trash%=fn.clr%(19)        rem clear request line
    return

290    rem-----request check date---------------------------
    trash%=fn.lit%(16)    rem "ENTER CHECK DATE (        ) "
    trash%=fn.put%(fn.date.format$,6)
292
    trash%=fn.in%(2,7)
    if back% or stopit% then return
    if not fn.edit.date%(in$) \
        then    trash%=fn.emsg%(01)   :\
            trash%=fn.clr%(7)     :\
            goto 292
    in.date$=fn.date.in$
    if in.date$<pr2.check.date$ \
        then    trash%=fn.emsg%(06)   :\
            trash%=fn.clr%(7)     :\
            goto 292
    check.date$=in.date$
    trash%=fn.clr%(16)
    return

300    rem-----determine proper quarter/year----------------
    ok%=true%
    temp%=fn.quarter%(check.date$)
    if temp%=1 \
        then    temp%=4  \
        else    temp%=temp%-1
    if pr2.last.q.ended%<>temp%        \
        then    trash%=fn.emsg%(02)   :\
            ok%=false%
    trash%=fn.decompose.date%(check.date$)
    if pr2.year%<>yr% \
        then    trash%=fn.emsg%(03)   :\
            ok%=false%
    return

330    rem-----display process screen-----------------------
    trash%=fn.lit%(18)   rem "EMPLOYEE PROCESSING WILL BEGIN MOMENTARILY"
    trash%=fn.clr%(21)    rem HRS file status msg
    return

370    rem-----two bases used-------------------------------
    trash%=fn.lit%(17)
        rem "APPLY WHICH INTERVAL BASE? (M=MONTH;W=WEEK) [ ]"
    trash%=fn.in%(2,8)
    if stopit% then return
    if back% then return
    if in.uc$<>"M" and in.uc$<>"W" \
        then    trash%=fn.emsg%(04)   :\
            goto 370
    if in.uc$="M" \
        then    month.based%=true%  :\
            week.based%=false%
    if in.uc$="W" \
        then    month.based%=false% :\
            week.based%=true%
    trash%=fn.clr%(17)
    return

500    rem-----set up files---------------------------------
    gosub 505            rem is chk.100 present?
    if chk.exists% \
        then    trash%=fn.emsg%(23)    :\
            goto 999.1
    gosub 510            rem get.chk.101  status
    if chk.exists% \
        then    gosub 520    rem get.chk.hdr
    if not pr1.check.printing.used% \
        then    chk.hdr.checks.printed%=true%

    if chk.exists% and not chk.hdr.checks.printed% \
            then    trash%=fn.emsg%(05)   :\
                goto 999.1
    if chk.exists% and not chk.hdr.register.printed%        \
            then    trash%=fn.emsg%(22)   :\
                goto 999.1

    if chk.exists% \
        then    close chk.file%
    gosub 530            rem delete chk.bak if present
    if chk.exists% \
        then    gosub 540    rem rename(chk.bak=chk)
    gosub 550            rem get.hrs.file
    if hrs.exists% \
        then    gosub 560 :\    rem get.hrs.hdr
            ok%=true% :\
            close hrs.file%  \
        else    gosub 580 :\    rem request confirmation
            hrs.hdr.proofed%=true%
    if not ok% or stopit% \
        then    goto 999.2
    if not hrs.hdr.proofed% \
        then    gosub 590 \    rem request.confirmation
        else    ok%=true%
    if not ok% or stopit% \
        then    goto 999.2
    gosub 600            rem is PAY.100 present?
    if not ok% \
        then    trash%=fn.emsg%(07)   :\
            goto 999.1

    gosub 610            rem get.pay.file
    if pay.exists% \
        then    gosub 620 :\    rem get.pay.hdr
            close pay.file%  \
        else    pay.hdr.journal.printed%=true%
    if not pay.hdr.journal.printed% \
        then    trash%=fn.emsg%(08)   :\
            goto 999.1

    gosub 640            rem get.emp.file
    if not emp.exists% \
        then    trash%=fn.emsg%(09)   :\
            goto 999.1
    close emp.file%

    gosub 650            rem get.ded.file
    if not ded.exists% \
        then    trash%=fn.emsg%(10)   :\
            goto 999.1
    gosub 655            rem read ded file
    close ded.file%

    if ded.swt.used% \
        then    gosub 660    rem get swt file
    if not swt.exists% and ded.swt.used% \
        then    trash%=fn.emsg%(11)   :\
            goto 999.1

    if ded.lwt.used% \
        then    gosub 670    rem get swt file
    if not lwt.exists% and ded.lwt.used% \
        then    trash%=fn.emsg%(12)   :\
            goto 999.1
    if lwt.exists% \
        then    close lwt.file%

    gosub 680            rem get.his.file
    if not his.exists% \
        then    trash%=fn.emsg%(13)   :\
            goto 999.1  \
        else    gosub 690 :\    rem read.his.hdr
            close his.file%

    gosub 700            rem get coh file
    if not coh.exists% \
        then    gosub 710 :\    rem request confirmation
        else    ok%=true% :\
            close coh.file%
    if not ok% or stopit% \
        then    goto 999.2

    gosub 720            rem get act file
    if not act.exists% \
        then    trash%=fn.emsg%(15)   :\
            goto 999.1 \
        else    close act.file%

    gosub 740            rem create new.pyo.file
    close pyo.file%
    return

505    rem-----get chk.100 status---------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING CHK.100",09)
    chk.exists%=false%
    if end #chk.file% then 506
    open fn.file.name.out$(chk.name$,"100",pr1.chk.drive%,pw$,pms$) \
        recl chk.len%  as chk.file%
    chk.exists%=true%        rem this is an error!
506    rem-----here if chk file not present-----------------
    return

510    rem-----get chk.101  status--------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING CHK FILE",09)
    chk.exists%=false%
    if end #chk.file% then 511
    open fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$) \
        recl chk.len%  as chk.file%
    chk.exists%=true%
511    rem-----here if chk file not present-----------------
    return

520    rem-----get chk hdr----------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING CHK HDR",09)
    read #chk.file%,1;    \
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

530    rem-----delete chk.bak if present--------------------
    if pr1.debugging% then trash%=fn.put%("GETTING CHK.BAK",09)
    if end #del.file% then 531
    open fn.file.name.out$(chk.name$,"102",pr1.chk.drive%,pw$,pms$) \
        recl chk.len%  as del.file%
    if pr1.debugging% then trash%=fn.put%("DELETING CHK.BAK",09)
    delete del.file%
531    rem-----here if chk file not present-----------------
    return

540    rem-----rename(chk.bak=chk)--------------------------
    if pr1.debugging% then trash%=fn.put%("RENAMING CHK.BAK <-CHK",09)
    trash%=rename      \
        (fn.file.name.out$(chk.name$,"102",pr1.chk.drive%,pw$,pms$), \
         fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$))
    return

550    rem-----get hrs file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING HRS FILE",09)
    hrs.exists%=false%
    if end #hrs.file% then 551
    open fn.file.name.out$(hrs.name$,"101",pr1.hrs.drive%,pw$,pms$) \
        recl hrs.len%  as hrs.file%
    hrs.exists%=true%
551    rem-----here if hrs file not present-----------------
    return

560    rem-----get hrs hdr----------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING HRS HDR",09)
    read #hrs.file%,1;   \
Rem $include "ipyhrshd"
        hrs.hdr.no.recs%,\     rem  10/30/79
        hrs.hdr.batch.no%,\
        hrs.hdr.proof.no%,\
        hrs.hdr.proofed%,\
        hrs.hdr.101
    return

580    rem-----display status msg---------------------------
    trash%=fn.lit%(20)        rem "NO CURRENT HRS FILE FOUND"
581
    trash%=fn.lit%(23)
    rem IF YOU WANT TO CONTINUE THE APPLICATION, TYPE "YES"   [   ]
    trash%=fn.in%(1,10)
    if stopit% \
        then    trash%=fn.clr%(23)    :\
            trash%=fn.clr%(20)    :\
            return
    if in.uc$="YES" \
        then    ok%=true%            \
        else    trash%=fn.emsg%(17)        :\
            trash%=fn.put%(null$,10)    :\
            goto 581        rem retry
    trash%=fn.clr%(23)
    trash%=fn.clr%(21)
    return

590    rem-----request confirmation-------------------------
    trash%=fn.lit%(21)
            rem "THE CURRENT HRS BATCH FILE HAS NOT BEEN PROOFED."
591
    trash%=fn.lit%(23)
    rem IF YOU WANT TO CONTINUE THE APPLICATION, TYPE "YES"   [   ]
    trash%=fn.in%(1,10)
    if stopit% \
        then    trash%=fn.clr%(23)    :\
            trash%=fn.clr%(21)    :\
            return
    if in.uc$="YES" \
        then    ok%=true% \
        else    trash%=fn.emsg%(17)    :\
            trash%=fn.put%(null$,10)    :\
            goto 591        rem retry
    trash%=fn.clr%(23)
    trash%=fn.clr%(21)
    return

600    rem-----is PAY.100 present?--------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING PAY.100",09)
    ok%=true%
    if end #del.file% then 601
    open fn.file.name.out$(pay.name$,"100",pr1.pay.drive%,pw$,pms$) \
        as del.file%
    ok%=false%
601    rem-----here if 100 file not present-----------------
    return

610    rem-----get pay file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING PAY.101",09)
    pay.exists%=false%
    if end #pay.file% then 611
    open fn.file.name.out$(pay.name$,"101",pr1.pay.drive%,pw$,pms$) \
        recl pay.len%  as pay.file%
    pay.exists%=true%
611    rem-----here if pay file not present-----------------
    return

620    rem-----get pay hdr----------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING PAY HDR",09)
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

640    rem-----get emp file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING EMP FILE",09)
    emp.exists%=false%
    if end #emp.file% then 641
    open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pms$) \
        recl emp.len%  as emp.file%
    emp.exists%=true%
641    rem-----here if emp file not present-----------------
    return

650    rem-----get ded file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING DED FILE",09)
    ded.exists%=false%
    if end #ded.file% then 651
    open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pw$,pms$) \
        as ded.file%
    ded.exists%=true%
651    rem-----here if ded file not present-----------------
    return

655    rem-----read ded file--------------------------------
    read #ded.file%;  \
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

660    rem-----get swt file---------------------------------
    if pr1.co.state$="CA" \
        then    gosub 662 \    rem open CAL files
        else    gosub 664    rem open SWT file
    return

662    rem-----open CAL files-------------------------------
    swt.exists%=true%
    suffix$="S"                     rem single table
    if pr1.debugging% then trash%=fn.put%("GETTING CALS FILE",09)
    gosub 666            rem open CAL file
    if not cal.exists% then swt.exists%=false%:return
    close cal.file%
    suffix$="M"                     rem married table
    if pr1.debugging% then trash%=fn.put%("GETTING CALM FILE",09)
    gosub 666            rem open CAL file
    if not cal.exists% then swt.exists%=false%:return
    close cal.file%
    suffix$="H"                     rem head of house table
    if pr1.debugging% then trash%=fn.put%("GETTING CALH FILE",09)
    gosub 666            rem open CAL file
    if not cal.exists% then swt.exists%=false%:return
    close cal.file%
    suffix$="X"                     rem special table file
    if pr1.debugging% then trash%=fn.put%("GETTING CALX FILE",09)
    gosub 666            rem open CAL file
    if not cal.exists% then swt.exists%=false%:return
    close cal.file%
    return

664    rem-----open swt file--------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING SWT FILE",09)
    swt.exists%=false%
    if end #swt.file% then 665
    open fn.file.name.out$(swt.name$+pr1.co.state$,"101",   \
        pr1.tax.drive%,pw$,pms$) \
        as swt.file%
    swt.exists%=true%
665    rem-----here if swt file not present-----------------
    return

666    rem-----open cal file--------------------------------
    cal.exists%=false%
    if end #cal.file% then 667
    open fn.file.name.out$(cal.name$+suffix$,"101",   \
        pr1.tax.drive%,pw$,pms$) \
        as cal.file%
    cal.exists%=true%
667    rem-----here if cal file not present-----------------
    return

670    rem-----get lwt file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING LWT FILE",09)
    lwt.exists%=false%
    if end #lwt.file% then 671
    open fn.file.name.out$(lwt.name$,"101",pr1.tax.drive%,pw$,pms$) \
        as lwt.file%
    lwt.exists%=true%
671    rem-----here if lwt file not present-----------------
    return

680    rem-----get his file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING HIS FILE",09)
    his.exists%=false%
    if end #his.file% then 681
    open fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pms$) \
        recl his.len%  as his.file%
    his.exists%=true%
681    rem-----here if his file not present-----------------
    return

690    rem-----read his hdr---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING HIS HDR",09)
    read #his.file%,1;     \
Rem $include "ipyhishd"
        his.hdr.no.recs%,\        rem  11/12/79
        his.hdr.last.to.date$,\
        his.hdr.101,\
        his.hdr.102,\
        his.hdr.201$
    return

700    rem-----get coh file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING COH FILE",09)
    coh.exists%=false%
    if end #coh.file% then 701
    open fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pms$) \
        as coh.file%
    coh.exists%=true%
701    rem-----here if coh file not present-----------------
    return

710    rem-----request confirmation-------------------------
    trash%=fn.lit%(22)
            rem "THE CURRENT COH FILE CANNOT BE FOUND."
711
    trash%=fn.lit%(23)
    rem IF YOU WANT TO CONTINUE THE APPLICATION, TYPE "YES"   [   ]
    trash%=fn.in%(1,10)
    if stopit% \
        then    trash%=fn.clr%(23)    :\
            trash%=fn.clr%(22)    :\
            return
    if in.uc$="YES" \
        then    ok%=true% \
        else    trash%=fn.emsg%(18)    :\
            trash%=fn.put%(null$,10)    :\
            goto 711        rem retry
    trash%=fn.clr%(23)
    trash%=fn.clr%(22)
    return

720    rem-----get act file---------------------------------
    if pr1.debugging% then trash%=fn.put%("GETTING ACT FILE",09)
    act.exists%=false%
    if end #act.file% then 721
    open fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pms$) \
        recl act.len%  as act.file%
    act.exists%=true%
721    rem-----here if act file not present-----------------
    return

740    rem-----create new pay file--------------------------
    if pr1.debugging% then trash%=fn.put%("CREATING NEW PAY",09)
    create fn.file.name.out$(pay.name$,"100",pr1.pyo.drive%,pw$,pms$) \
        recl pyo.len%  as pyo.file%
    pay.hdr.no.recs%=0
    pay.hdr.interval$=interval$
    pay.hdr.last.apply.no%=apply.no%
    pay.hdr.journal.printed%=false%
    pay.hdr.last.day.of.last.per$=to.date$
    gosub 800            rem write pay hdr
    return

800    rem-----write pay hdr--------------------------------
    if pr1.debugging% then trash%=fn.put%("WRITING PAY HDR",09)
    print #pyo.file%,1;    \
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

850    rem-----rewrite pr2 file-----------------------------
    if pr1.debugging% then trash%=fn.put%("WRITING PR2 FILE",09)
    if end #pr2.file% then 851
    open fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pms$) \
        as pr2.file%
    print #pr2.file%;     \
Rem $include "ipypr2"
        pr2.year%        rem 12/02/79
        pr2.last.sm.apply.no%, pr2.last.wb.apply.no%
        pr2.no.of.sm.applies%, pr2.no.of.wb.applies%
        pr2.hrs.batch.no%
        pr2.last.day.of.last.w$, pr2.last.day.of.last.b$
        pr2.last.day.of.last.s$, pr2.last.day.of.last.m$
        pr2.940.printed%, pr2.941.printed%, pr2.w2.printed%
        pr2.no.acts%
        pr2.no.active.emps%, pr2.no.employees%
        pr2.check.date$
        pr2.last.check.no$
        pr2.last.q.ended%
        pr2.just.closed.year%
    close pr2.file%
    return
851    rem-----here if pr2 file not present-----------------
    trash%=fn.emsg%(16)
    goto 999.1

870    rem-----delete HRS.001 if needed---------------------
    if not hrs.exists% \    rem if no 101 file, then leave 001 alone
        then    return
    if end #del.file% then 871
    open fn.file.name.out$(hrs.name$,"001",pr1.hrs.drive%,pw$,pms$) \
        as del.file%
    delete del.file%
871    rem-----here if del file not present-----------------
    return

1000    rem-----determine if period needs ending-------------
    ok%=true%
    if week.based% and pr2.no.of.wb.applies%>14 \
        then    trash%=fn.emsg%(19)    :\
            ok%=false%        :\
            return
    if month.based% and pr2.no.of.sm.applies%>06 \
        then    trash%=fn.emsg%(20)    :\
            ok%=false%        :\
            return
    if pr2.last.q.ended%=4 and not pr2.just.closed.year% \
        then    trash%=fn.emsg%(21)    :\
            ok%=false%        :\
            return
    return
