Rem #include "ipycomm"
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
Rem #include "ipyjrncm"
common acct.amt(1)            rem 12/17/79
common total.units(1)
common dist.out(1)
common total.reg.wages
common total.other.earn
common total.tips
common total.tips.reported
common total.fwt
common total.swt
common total.lwt
common total.fica
common total.sdi
common total.eic
common total.other.ded
common total.net
common total.co.fica
common total.co.futa
common total.co.sui
common total.vac.taken
common total.sl.taken
common total.comp.taken
common total.comp.earned
common total.units(01)
common page%
common from.date$
common chk.hdr.to.date$
prgname$="PYJOURN1   JAN. 16, 1980 "
rem----------------------------------------------------------
rem
rem    P  Y  J  O  U  R  N  1
rem
rem    PRINT THE PAYROLL JOURNAL SUMMARIES
rem
rem    SECOND SECTION
rem
rem    P A Y R O L L       S Y S T E M
rem
rem    COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="PYJOURN1"
function.name$="PAYROLL JOURNAL PRINT"

Rem #include "ipyconst"
rem     JAN. 18, 1980
system$="PY":version$=" REL:1.0 "
system.name$="PAYROLL SYSTEM"
cpyrght$="COPYRIGHT (C) 1980, APPLEWOOD COMPUTERS "
dummy$="PYppppI00":null$="":asc.quote%= 34
dim crt.data$(0),crt.x%(0),crt.y%(0),crt.len%(0),crt.rd%(0),crt.attrib%(0)
Rem #include "zfilconv"
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
Rem #include "zdms"
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
Rem #include "zdmsclr"
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

dim emsg$(10)
emsg$(01)="PY771 ACT FILE NOT FOUND"
emsg$(02)="PY772 UNEXPECTED EOF ON PAY FILE"
emsg$(03)="PY773 BATCH TOTAL NOT ZERO"
emsg$(04)="PY774 "
emsg$(05)="PY775 "
emsg$(06)="PY776 "

Rem #include "zdateio"
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

Rem #include "zstring"
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

Rem #include "ipydmemp"
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
Rem #include "ipydmded"
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
Rem #include "zbracket"
rem    Jan. 19, 1979
def fn.bracket$(number,l.digits%,cents%)
    temp$="###,###,###,###,###"
    temp%=len(str$(abs(int(number))))
    temp$=right$(temp$,temp%+int%(temp%/3.5))
    if cents% then temp$=temp$+".##"
    temp%=l.digits%+int%(l.digits%/3.5)+(cents%*(-3))+2
    if number<0 then temp$="<"+temp$+">" else temp$=" "+temp$+" "
    fn.bracket$=right$(blank$+temp$,temp%)
    return
fend
Rem #include "zheading"
rem     Jan. 17, 1979
rem requires zstring,zdatei/o
def fn.hdr%(report$)
    print tof$
    page%=page%+1
    if page.width%=0 then page.width%=132
    if todays.date$=null$ then todays.date$=common.date$
    print tab(fn.center%(pr1.co.name$,page.width%));  \
        pr1.co.name$; \
        tab(page.width%-14); \
        "PAGE ";page%
    print tab(fn.center%(system.name$,page.width%));  \
        system.name$; \
        tab(page.width%-14); \
        "DATE ";fn.date.out$(todays.date$)
    print tab(fn.center%(report$,page.width%));report$
    fn.hdr%=3
    return
fend

Rem #include "fpyjrn"            rem define screen info
rem---------------------------------------------------------
rem    SET UP DMS SCREEN EQUATES    FPYJRN - 11/19/79

crt.field.count% = 12        rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem    LEGEND:    X  Y  LEN  RD  ATTRIB
rem        STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data           \
      51,15,5,0,17,\       rem   IO fld #1
      56,18,1,0,17,\       rem   IO fld #2
      25,20,31,0,17,\    rem   IO fld #3
      1,1,8,0,4,\        rem   O fld #4
      1,2,9,0,4,\        rem   O fld #5
      1,3,8,0,4,\        rem   O fld #6
      10,3,8,0,4,\         rem   O fld #7
      25,15,25,0,0,\       rem   O fld #8
      24,15,32,0,0,\       rem   O fld #9
      28,15,24,0,0,\       rem   O fld #10
      29,17,22,0,0,\       rem   O fld #11
      29,18,23,0,0
      rem    O fld #12
crt.data$(8)="PRINTING EMPLOYEE NUMBER:"
crt.data$(9)="PRINTING COMPANY PAYROLL SUMMARY"
crt.data$(10)="PRINTING ACCOUNT SUMMARY"
crt.data$(11)="HIT RETURN TO CONTINUE"
crt.data$(12)="HIT ESC TO END PRINTOUT"

i%=1
while i%<=12
  read    crt.x%(i%),crt.y%(i%),\
    crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then     co.name$=fn.spread$(pr1.co.name$,1)  \
  else     co.name$=pr1.co.name$
crt.len%(4)=len(co.name$)
crt.x%(4)=fn.center%(co.name$,crt.columns%-2)
crt.data$(4)=co.name$
if len(system.name$)<=30 \
  then     sys.name$=fn.spread$(system.name$,1)  \
  else     sys.name$=system.name$
crt.len%(5)=len(sys.name$)
crt.x%(5)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(5)=sys.name$
crt.data$(6)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then     fun.name$=fn.spread$(function.name$,1)  \
  else     fun.name$=function.name$
crt.len%(7)=len(fun.name$)
crt.x%(7)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(7)=fun.name$

rem---------------------------------------------------------

hdr2$="COMPANY PAYROLL SUMMARY"
hdr3$="LEDGER ACCOUNT SUMMARY"

def fn.round(rr)=(int((rr*100)+.5))/100

line.cnt%=1000            rem force a new page

rem----------------------------------------------------------
rem
rem    S E T        U P
rem
rem----------------------------------------------------------

gosub 500            rem set up files

rem----------------------------------------------------------
rem
rem    M A I N       D R I V E R
rem
rem----------------------------------------------------------

if pr1.debugging% \
    then    trash%=fn.put%("fre: "+str$(fre),03)

gosub 12000                rem print amount summary
if stopit% \
    then    goto 999.2
if pr1.dist.used% \
    then    gosub 13000        rem print account summary
if stopit% \
    then    goto 999.2

rem----------------------------------------------------------
rem
rem    E N D      O F      J O B
rem
rem----------------------------------------------------------

lprinter:print:console        rem for centronics printer

gosub 600            rem update pay hdr

if batch.total<>0 \
    then    trash%=fn.emsg%(03)    :\
        goto 999.1

Rem #include "zeoj"
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

500    rem-----set up files---------------------------------
    gosub 720            rem get act file
    if not act.exists% \
        then    trash%=fn.emsg%(01)   :\
            goto 999.1
    gosub 730            rem read in act hdr

    gosub 610            rem get pay file
    if not pay.exists% \
        then    trash%=fn.emsg%(02)    :\
            goto 999.1
    gosub 620            rem get pay hdr
    return

600    rem-----update pay hdr-------------------------------
    pay.hdr.journal.printed%=true%
    gosub 630            rem write pay hdr
    close pay.file%
    return

610    rem-----get pay file---------------------------------
    pay.exists%=false%
    if end #pay.file% then 611
    open fn.file.name.out$(pay.name$,"101",pr1.pay.drive%,pw$,pms$) \
        recl pay.len%  as pay.file%
    pay.exists%=true%
611    rem-----here if pay file not present-----------------
    return

620    rem-----get pay hdr----------------------------------
    read #pay.file%,1;    \
Rem #include "ipypayhd"
        pay.hdr.no.recs%,\       rem 10/30/79
        pay.hdr.interval$,\
        pay.hdr.last.apply.no%,\
        pay.hdr.journal.printed%,\
        pay.hdr.last.day.of.last.per$,\
        pay.hdr.101,\
        pay.hdr.102,\
        pay.hdr.201$
    return

630    rem-----update pay hdr-------------------------------
    print #pay.file%,1;    \
Rem #include "ipypayhd"
        pay.hdr.no.recs%,\       rem 10/30/79
        pay.hdr.interval$,\
        pay.hdr.last.apply.no%,\
        pay.hdr.journal.printed%,\
        pay.hdr.last.day.of.last.per$,\
        pay.hdr.101,\
        pay.hdr.102,\
        pay.hdr.201$
    return

720    rem-----get act file---------------------------------
    if pr1.debugging% \
        then trash%=fn.put%("GETTING ACT FILE",03)
    act.exists%=false%
    if end #act.file% then 721
    open fn.file.name.out$(act.name$,"101",pr1.act.drive%,pw$,pms$) \
        recl act.len%  as act.file%
    act.exists%=true%
721    rem-----here if act file not present-----------------
    return

730    rem-----read in act hdr------------------------------
    read #act.file%,1;    \
Rem #include "ipyacthd"
        act.hdr.no.recs%     rem   9/12/79
    return

6200    rem-----increment and test lines---------------------
    gosub 6205            rem test lines
    line.cnt%=line.cnt%+1
    return

6205    rem-----test lines-----------------------------------
    if line.cnt%>=pr1.lines.per.page%-2 \
        then    gosub 6210    rem do header
    return

6210    rem-----do header------------------------------------
    lprinter
    line.cnt%=fn.hdr%(fn.spread$(function.name$,1))+3
    console
    gosub 6300            rem check for interruption
    if stopit% then return
    if amount.summary% \
        then    gosub 6250    rem do amount summary header
    if account.summary% \
        then    gosub 6260    rem do account summary header
    return

6250    rem-----do amount  summary header--------------------
    trash%=fn.lit%(09)
    lprinter
    print "INTERVAL: ";
    print pay.hdr.interval$;
    print tab(fn.center%(hdr2$,pr1.page.width%));hdr2$;
    print tab(104);"FROM: ";
    print fn.date.out$(from.date$);
    print tab(120);"TO: ";
    print fn.date.out$(chk.hdr.to.date$)

    print tab(112);"CHECK DATE: ";
    print fn.date.out$(pr2.check.date$)
    line.cnt%=line.cnt%+1

    print
    console
    line.cnt%=line.cnt%+1
    return

6260    rem-----do account summary header--------------------
    trash%=fn.clr%(09)
    trash%=fn.lit%(10)
    lprinter
    print "INTERVAL: ";
    print pay.hdr.interval$;
    print tab(fn.center%(hdr3$,pr1.page.width%));hdr3$;
    print tab(104);"FROM: ";
    print fn.date.out$(from.date$);
    print tab(120);"TO: ";
    print fn.date.out$(chk.hdr.to.date$)

    print tab(112);"CHECK DATE: ";
    print fn.date.out$(pr2.check.date$)
    line.cnt%=line.cnt%+1

    print
    print tab(031);"ACCT";
    print tab(042);"GL";
    print tab(059);"A C C O U N T";
    print tab(092);"POSTED"

    print tab(032);"NO";
    print tab(041);"ACCT";
    print tab(062);"N A M E";
    print tab(092);"TOTAL"

    print
    console
    line.cnt%=line.cnt%+5
    return

6300    rem-----check for interruption-----------------------
    stopit%=false%
    if not constat% then return
    trash%=conchar%
    trash%=fn.lit%(11)
    trash%=fn.lit%(12)
    trash%=fn.get%(02,02)
    trash%=fn.clr%(11)
    trash%=fn.clr%(12)
    if in.status%=req.cr% \
        then    return
    if in.status%=req.stopit% \
        then    stopit%=true%
    if in.status%=req.back% \
        then    stopit%=true%
    return

9050    rem-----print a blank line---------------------------
    gosub 6200            rem increment and test lines
    lprinter
    print
    console
    return

11100    rem-----print units total----------------------------
    gosub 9050            rem a blank line
    units.total=0
    no.totals%=0
    for i%=1 to 4
        line.cnt%=line.cnt%+1
        gosub 6300        rem check for interruption
        if stopit% then return
        if total.units(i%)=0 \
            then    goto 11101    rem break
        no.totals%=no.totals%+1
        lprinter
        if no.totals%=1 \
            then    print tab(10);"TOTAL UNITS:";
        print using "/2345678901234/: ##,###.##";\
            tab(23),\
            pr1.rate.name$(i%),\
            total.units(i%)
        console
        grand.total.units=grand.total.units+total.units(i%)
11101
    next i%
    line.cnt%=line.cnt%+1
    gosub 6300            rem check for interruption
    if stopit% then return
    if no.totals%<=1 then return
    lprinter
    print using "    GRAND TOTAL UNITS: ##,###.##";\
        tab(23),\
        grand.total.units
    console
    return

11210    rem-----print hdr and amounts------------------------
    line.cnt%=line.cnt%+1
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print " ";                      rem extra leading blank
    print using " /2345678901/";\
        "   REG WAGES",\
        "  OTHER EARN",\
        "      TIPS  ",\
        "      FWT   ",\
        "      SWT   ",\
        "      LWT   ",\
        "      FICA  ",\
        "      SDI   ",\
        "  OTHER DEDS",\
        "      NET   "
    console

    line.cnt%=line.cnt%+1
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print " ";                      rem extra leading blank
    print using "  ###,###.## ";            \
            total.reg.wages;\
            total.other.earn;\
            total.tips;\
            total.fwt;\
            total.swt;\
            total.lwt;\
            total.fica;\
            total.sdi;\
            total.other.ded;
    print using " "+fn.bracket$(total.net,6,true%);abs(total.net);
    print                rem trailing crlf
    console
    return

12000    rem-----print amount summary-------------------------
    account.summary%=false%
    amount.summary%=true%
    line.cnt%=1000
    gosub 9050            rem print a blank line
    gosub 9050            rem print a blank line
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print " ";                      rem extra leading blank
    tot$="     TOTAL  "
    print using " /2345678901/";\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$

    gosub 11210            rem print hdr and amounts
    if stopit% then return
    lprinter            rem console is set in 11210

    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    print                rem a blank line

    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    print " ";                      rem extra leading blank
    print using " /2345678901/";\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$,\
        tot$

    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    print " ";                      rem extra leading blank
    print using " /2345678901/";\
        "TIPS REPORTD",\
        "    CO FICA ",\
        "    CO FUTA ",\
        "     CO SUI ",\
        "  VAC TAKEN ",\
        "   SL TAKEN ",\
        "  COMP TAKEN",\
        " COMP EARNED",\
        "      EIC   "

    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    print " ";                      rem extra leading blank
    print using "  ###,###.## ";    \
            total.tips.reported;    \
            total.co.fica;        \
            total.co.futa;        \
            total.co.sui;        \
            total.vac.taken;    \
            total.sl.taken;     \
            total.comp.taken;    \
            total.comp.earned;    \
            total.eic;
    print                rem trailing crlf
    console

    gosub 11100            rem print units total
    if stopit% then return
    return

13000    rem-----print account summary------------------------
    read #act.file%,1;        rem rewind act file
    gosub 730            rem read act hdr
    line.cnt%=1000
    account.summary%=true%
    amount.summary%=false%
    batch.total=0
    for act%=1 to pr2.no.acts%
        if acct.amt(act%)=0 \
            then    goto 13001    rem break
        gosub 13100            rem print account line
        if stopit% then return
        if dr.cr$="DR" \
            then    batch.total=batch.total+abs(acct.amt(act%)) \
            else    batch.total=batch.total-abs(acct.amt(act%))
13001
    next act%
    gosub 13200            rem print batch total line
    if stopit% then return
    return

13100    rem-----print account line---------------------------
    act.rec%=act%
    gosub 13110            rem read act record
    gosub 13120            rem determine DR or CR
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print using "###";\
        tab(31),\
        act%;
    print using "/2345/";\
        tab(40),\
        act.no$;
    print using "/2345678901234567890123456789/";\
        tab(52),\
        act.desc$;
    print using "#,###,###.##";\
        tab(88),\
        abs(acct.amt(act%));
    print using "//";\
        tab(105),\
        dr.cr$
    console
    return

13110    rem-----read act rec---------------------------------
    read #act.file%,act.rec%+1;    \
Rem #include "ipyact"
        act.no$,\         rem 12/11/79
        act.desc$
    return

13120    rem-----determine DR or CR---------------------------
    if left$(act.no$,1)="0" or  \
       left$(act.no$,1)="4" or  \
       left$(act.no$,1)="5"     \
        then    debits.normal%=true%   \
        else    debits.normal%=false%
    if debits.normal%        \
        then    dr.cr$="DR"  \
        else    dr.cr$="CR"
    if acct.amt(act.rec%)<0 \
        then    gosub 13125    rem swap dr/cr
    return

13125    rem-----swap dr/cr-----------------------------------
    if dr.cr$="DR" \
        then    dr.cr$="CR" \
        else    dr.cr$="DR"
    return

13200    rem-----print batch total line-----------------------
    gosub 9050            rem print a blank line
    if stopit% then return
    gosub 6200            rem increment and test lines
    if batch.total<0 \
        then    dr.cr$="CR" \
        else    dr.cr$="DR"
    if batch.total=0 \
        then    dr.cr$=null$
    lprinter
    print tab(70);       \
        "BATCH TOTAL:";
    print using " #,###,###.##     //";             \
        tab(87),\
        abs(batch.total),\
        dr.cr$
    console
rem batch.total is tested in EOJ driver
    return
