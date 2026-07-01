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
prgname$="PYJOURN    JAN. 17, 1980 "
rem----------------------------------------------------------
rem
rem    P  Y  J  O  U  R  N
rem
rem    PRINT THE PAYROLL JOURNAL
rem
rem    F I R S T      S E C T I O N
rem
rem    P A Y R O L L       S Y S T E M
rem
rem    COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="PYJOURN"
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
emsg$(01)="PY761 PAY FILE NOT FOUND"
emsg$(02)="PY762 EMP FILE NOT FOUND"
emsg$(03)="PY763 ACT FILE NOT FOUND"
emsg$(04)="PY764 DED FILE NOT FOUND"
emsg$(05)="PY765 NET PAY EXCEEDS SYSTEM MAX. CHECK WILL BE VOIDED"
emsg$(06)="PY766 BATCH TOTAL NOT ZERO"
emsg$(07)="PY767 NET PAY LESS THAN ZERO. CHECK WILL BE VOIDED"

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
Rem #include "ipyedesc"
dim ed.desc.table$(pr1.max.ed.cats%)        rem  9/29/79
ed.desc.table$(01)="REGULAR PAY"
ed.desc.table$(02)="OVERTIME PAY"       rem from PR1 file
ed.desc.table$(03)="SPECIAL OT PAY"     rem from PR1 file
ed.desc.table$(04)="COMMISSION"         rem from PR1 file
ed.desc.table$(05)="VACATION TAKEN"
ed.desc.table$(06)="SICK LVE TAKEN"
ed.desc.table$(07)="COMP TIME TAKEN"
ed.desc.table$(08)="COMP TIME EARND"
ed.desc.table$(09)="BONUS"
ed.desc.table$(10)="TIPS COLLECTED"
ed.desc.table$(11)="ADVANCE"
ed.desc.table$(12)="SICK PAY"
ed.desc.table$(13)="VACATION PAY"
ed.desc.table$(14)="OTHER EXCLD PAY"
ed.desc.table$(15)="EXPENSE REIMB"
ed.desc.table$(16)="EIC"
ed.desc.table$(17)="OTHER PAY"
ed.desc.table$(18)="TIPS REPORTED"
ed.desc.table$(19)=""
ed.desc.table$(20)="FWT"
ed.desc.table$(21)="SWT"
ed.desc.table$(22)="LWT"
ed.desc.table$(23)="FICA"
ed.desc.table$(24)="SDI"
ed.desc.table$(25)=""
ed.desc.table$(26)=""
ed.desc.table$(27)="ADVANCE REPAY"
ed.desc.table$(28)="FWT ADD-ON"
ed.desc.table$(29)="SWT ADD-ON"
ed.desc.table$(30)="LWT ADD-ON"
ed.desc.table$(31)="FICA ADD-ON"
ed.desc.table$(32)=""
ed.desc.table$(33)="SYS1"          rem  from sys1
ed.desc.table$(34)="SYS2"          rem  from sys2
ed.desc.table$(35)="SYS3"          rem  from sys3
ed.desc.table$(36)="SYS4"          rem  from sys4
ed.desc.table$(37)="SYS5"          rem  from sys5
ed.desc.table$(38)="EMP1"          rem  from emp1
ed.desc.table$(39)="EMP2"          rem  from emp2
ed.desc.table$(40)="EMP3"          rem  from emp3
ed.desc.table$(41)=""
ed.desc.table$(42)="COMPANY FICA"
ed.desc.table$(43)="COMPANY FUTA"
ed.desc.table$(44)="COMPANY SUI"
ed.desc.table$(45)=""
ed.desc.table$(46)="OTHER CO COST"
ed.desc.table$(47)=""
ed.desc.table$(48)=""
ed.desc.table$(49)=""
ed.desc.table$(50)="OTHER DED"
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

dim acct.no$(pr2.no.acts%)
dim acct.amt(pr2.no.acts%)

dim units(4)
dim total.units(4)
dim sys(pr1.max.sys.eds%)
dim emp(pr1.max.emp.eds%)
dim dist.out(pr1.max.dist.accts%)

dim edo%(pr1.max.ed.cats%)
rem    1=earning
rem    2=deduction
rem    3=other
edo%(01)=01    rem REGULAR PAY
edo%(02)=01    rem OVERTIME PAY
edo%(03)=01    rem SPECIAL OT PAY
edo%(04)=01    rem COMMISSION
edo%(05)=03    rem VACATION TAKEN     NOT ON CHECKS
edo%(06)=03    rem SICK LVE TAKEN     NOT ON CHECKS
edo%(07)=03    rem COMP TIME TAKEN    NOT ON CHECKS
edo%(08)=03    rem COMP TIME EARND    NOT ON CHECKS
edo%(09)=01    rem BONUS
edo%(10)=01    rem TIPS COLLECTED
edo%(11)=03    rem ADVANCE
edo%(12)=01    rem SICK PAY
edo%(13)=01    rem VACATION PAY
edo%(14)=01    rem OTHER EXCLD PAY
edo%(15)=03    rem EXPENSE REIMB
edo%(16)=01    rem EIC
edo%(17)=01    rem OTHER PAY
edo%(18)=01    rem TIPS REPORTED
edo%(19)=03    rem UNUSED
edo%(20)=02    rem FWT
edo%(21)=02    rem SWT
edo%(22)=02    rem LWT
edo%(23)=02    rem FICA
edo%(24)=02    rem SDI
edo%(25)=03    rem UNUSED
edo%(26)=03    rem UNUSED
edo%(27)=02    rem ADVANCE REPAY
edo%(28)=02    rem FWT ADD-ON
edo%(29)=02    rem SWT ADD-ON
edo%(30)=02    rem LWT ADD-ON
edo%(31)=02    rem FICA ADD-ON
edo%(32)=03    rem UNUSED
edo%(33)=00    rem SYS1 FROM DED FILE
edo%(34)=00    rem SYS2 FROM DED FILE
edo%(35)=00    rem SYS3 FROM DED FILE
edo%(36)=00    rem SYS4 FROM DED FILE
edo%(37)=00    rem SYS5 FROM DED FILE
edo%(38)=00    rem EMP1 FROM EMP FILE
edo%(39)=00    rem EMP2 FROM EMP FILE
edo%(40)=00    rem EMP3 FROM EMP FILE
edo%(41)=03    rem UNUSED
edo%(42)=03    rem COMPANY FICA       NOT ON CHECKS
edo%(43)=03    rem COMPANY FUTA       NOT ON CHECKS
edo%(44)=03    rem COMPANY SUI        NOT ON CHECKS
edo%(45)=03    rem UNUSED
edo%(46)=03    rem OTHER CO COST      NOT ON CHECKS
edo%(47)=03    rem UNUSED
edo%(48)=03    rem UNUSED
edo%(49)=03    rem UNUSED
edo%(50)=02    rem OTHER DED

hdr1$="EMPLOYEE PAYROLL DETAIL"

def fn.name.flip$(name$)
    temp%=match("*",name$,1)
    if temp%=0 then fn.name.flip$=name$:return
    fn.name.flip$=                     \
        right$(name$,len(name$)-temp%)        +\
        " "                                     +\
        left$(name$,temp%-1)
    return
fend

def fn.round(rr)=(int((rr*100)+.5))/100

line.cnt%=1000            rem force a new page
page%=0             rem this is in common, so initialize

gosub 12800            rem initialize common counters

rem----------------------------------------------------------
rem
rem    S E T        U P
rem
rem----------------------------------------------------------

trash%=fn.put.all%(false%)    rem display.set.up.screen
gosub 500            rem set up files
gosub 510            rem put sys ed types in edo table
trash%=fn.lit%(08)        rem display.process.screen
gosub 6250            rem determine from dates

rem----------------------------------------------------------
rem
rem    M A I N       D R I V E R
rem
rem----------------------------------------------------------

gosub 3000            rem select a pay rec
while not pay.eof%
    last.pay.emp.no$=pay.emp.no$
    gosub 4000        rem get emp rec
    gosub 4100        rem put emp ed types in edo table
    gosub 5000        rem display employee number
    if pr1.debugging% \
        then    trash%=fn.put%("fre: "+str$(fre),03)
    gosub 6000        rem print employee demo line
    if stopit% then goto 99
    gosub 7000        rem clear accums
    while not pay.eof% and pay.emp.no$=last.pay.emp.no$
        gosub 8100    rem accumulate pay info
        gosub 9000    rem print detail line
        if stopit% then goto 99
        gosub 3000    rem select a pay rec

    wend
    gosub 11000        rem calc and print emp info
    gosub 12500        rem distribute offset amounts
    gosub 12700        rem accumulate company totals
    if stopit% then goto 99
wend

rem----------------------------------------------------------
rem
rem    E N D      O F      J O B
rem
rem----------------------------------------------------------

99    rem-----here if stop requested-----------------------

lprinter:print:console        rem for centronics printer

close pay.file%
close emp.file%
close act.file%

if stopit% then goto 999.2

chain fn.file.name.out$("pyjourn1",null$,0,pw$,pms$)

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
    gosub 610            rem get.pay.file
    if pay.exists% \
        then    gosub 620 :\    rem get.pay.hdr
        else    trash%=fn.emsg%(01)   :\
            goto 999.1
    gosub 640            rem get.emp.file
    if not emp.exists% \
        then    trash%=fn.emsg%(02)   :\
            goto 999.1

    gosub 720            rem get act file
    if not act.exists% \
        then    trash%=fn.emsg%(03)   :\
            goto 999.1
    gosub 730            rem read in act hdr
    gosub 740            rem read in act file
    gosub 750            rem get ded file
    if not ded.exists% \
        then    trash%=fn.emsg%(04)   :\
            goto 999.1
    gosub 760            rem read ded file
    close ded.file%
    gosub 800            rem get chk file
    if chk.exists% \
        then    gosub 810 :\    rem read chk hdr
            close chk.file%
    return

510    rem-----put sys ed types in edo table----------------
    for x%=1 to pr1.max.sys.eds%
        if ded.sys.earn.ded$(x%)="E" \
            then    edo%=1    \
            else    edo%=2
        edo%(32+x%)=edo%
    next x%
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

640    rem-----get emp file---------------------------------
    emp.exists%=false%
    if end #emp.file% then 641
    open fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pms$) \
        recl emp.len%  as emp.file%
    emp.exists%=true%
641    rem-----here if emp file not present-----------------
    return

720    rem-----get act file---------------------------------
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

740    rem-----read in act file-----------------------------
    act.rec%=1
    while act.rec%<=pr2.no.acts%
        gosub 745            rem read act record
        acct.no$(act.rec%)=act.no$
        act.rec%=act.rec%+1
    wend
    return

745    rem-----read act record------------------------------
    read #act.file%,act.rec%+1;\
Rem #include "ipyact"
        act.no$,\         rem 12/11/79
        act.desc$
    return

750    rem-----get ded file---------------------------------
    ded.exists%=false%
    if end #ded.file% then 751
    open fn.file.name.out$(ded.name$,"101",pr1.ded.drive%,pw$,pms$) \
        recl ded.len%  as ded.file%
    ded.exists%=true%
751    rem-----here if ded file not present-----------------
    return

760    rem-----read ded file--------------------------------
    read #ded.file%;      \
Rem #include "ipyded"
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

800    rem-----get chk file---------------------------------
    chk.exists%=false%
    if end #chk.file% then 801
    open fn.file.name.out$(chk.name$,"101",pr1.chk.drive%,pw$,pms$) \
        recl chk.len%  as chk.file%
    chk.exists%=true%
801    rem-----here if chk file not present-----------------
    return

810    rem-----get chk hdr----------------------------------
    read #chk.file%,1;    \
Rem #include "ipychkhd"
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

3000    rem-----select a pay rec-----------------------------
    pay.rec%=pay.rec%+1
    gosub 3100            rem get pay rec
    if pay.eof% then return
    while not pay.extended%
        pay.rec%=pay.rec%+1
        gosub 3100        rem get pay rec
        if pay.eof% then return
    wend
    return

3100    rem-----get pay rec----------------------------------
    if pay.rec%>pay.hdr.no.recs% then pay.eof%=true%:return
    read #pay.file%,pay.rec%+1;    \
Rem #include "ipypay"
        pay.emp.no$,\           rem  9/25/79
        pay.eff.date$,\
        pay.interval$,\
        pay.apply.no%,\
        pay.reporting.cat%,\
        pay.units,\
        pay.amt,\
        pay.extended%
    return

4000    rem-----get emp rec----------------------------------
    emp.rec%=val(left$(pay.emp.no$,4))
    read #emp.file%,emp.rec%+1;    \
Rem #include "ipyemp"
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

4100    rem-----put emp ed types in edo table----------------
    for x%=1 to pr1.max.emp.eds%
        if emp.ed.earn.ded$(x%)="E" \
            then    edo%=1    \
            else    edo%=2
        edo%(37+x%)=edo%
    next x%
    return

5000    rem-----display employee number----------------------
    trash%=fn.put%(emp.no$,01)
    return

6000    rem-----print employee demo line---------------------
    gosub 6100            rem string together exempt flags
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print using \
"!/234/    /2345678901234567890123456789/    /234567890/   &";\
        exempt.flag$,\
        emp.no$,\
        fn.name.flip$(emp.emp.name$),\
        emp.ssn$,\
        exemptions$
    console
    return

6100    rem-----string together exempt flags-----------------
    exemptions$=null$
    if emp.fwt.exempt% then exemptions$=exemptions$+",FWT"
    if emp.swt.exempt% then exemptions$=exemptions$+",SWT"
    if emp.lwt.exempt% then exemptions$=exemptions$+",LWT"
    if emp.fica.exempt% then exemptions$=exemptions$+",FICA"
    if emp.sdi.exempt% then exemptions$=exemptions$+",SDI"
    if emp.co.futa.exempt% then exemptions$=exemptions$+",CO FUTA"
    if emp.co.sui.exempt% then exemptions$=exemptions$+",CO SUI"
    if emp.sys.exempt%(1) then exemptions$=exemptions$+",SYS1"
    if emp.sys.exempt%(2) then exemptions$=exemptions$+",SYS2"
    if emp.sys.exempt%(3) then exemptions$=exemptions$+",SYS3"
    if emp.sys.exempt%(4) then exemptions$=exemptions$+",SYS4"
    if emp.sys.exempt%(5) then exemptions$=exemptions$+",SYS5"
    if exemptions$=null$ \
        then    exempt.flag$=" "                        :\
            return                     \
        else    exempt.flag$="*"                        :\
            exemptions$="EXEMPT FROM: "             +\
             right$(exemptions$,len(exemptions$)-1)
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
    gosub 6220            rem print other hdr line

    lprinter
    print tab(112);"CHECK DATE: ";
    print fn.date.out$(pr2.check.date$)
    console
    line.cnt%=line.cnt%+1
    return


6220    rem-----print other hdr line-------------------------
    lprinter
    print "INTERVAL: ";
    print pay.hdr.interval$;
    print tab(fn.center%(hdr1$,pr1.page.width%));hdr1$;
    print tab(104);"FROM: ";
    print fn.date.out$(from.date$);
    print tab(120);"TO: ";
    print fn.date.out$(chk.hdr.to.date$)
    console
    line.cnt%=line.cnt%+1
    return

6250    rem-----determine from dates-------------------------
    if pr1.s.used% and pr1.m.used% or \
       pr1.w.used% and pr1.b.used% \
        then    fast.and.slow%=true% \
        else    fast.and.slow%=false%
    if not fast.and.slow% \
        then    gosub 6255 :\    rem get fast or slow date
            return
    if (pay.hdr.interval$="M" and pr1.s.used%) or \
       (pay.hdr.interval$="B" and pr1.w.used%) \
        then    from.date$=chk.hdr.slow.from.date$ \
        else    from.date$=chk.hdr.fast.from.date$
    return

6255    rem-----get fast or slow date------------------------
    if pay.hdr.interval$="S" or pay.hdr.interval$="W" \
        then    from.date$=chk.hdr.fast.from.date$
    if pay.hdr.interval$="B" or pay.hdr.interval$="M" \
        then    from.date$=chk.hdr.slow.from.date$
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

7000    rem-----clear accums---------------------------------
    reg.wages        =zero
    other.earn        =zero
    gross            =zero
    fwt            =zero
    swt            =zero
    lwt            =zero
    fica            =zero
    sdi            =zero
    eic            =zero
    other.ded        =zero
    net            =zero
    employer.cost        =zero
    tips            =zero
    tips.reported        =zero
    co.fica         =zero
    co.futa         =zero
    co.sui            =zero
    comp.earned        =zero
    comp.taken        =zero
    sl.taken        =zero
    vac.taken        =zero
    for i%=1 to 5
        sys(i%)     =zero
    next i%
    for i%=1 to 3
        emp(i%)     =zero
    next i%
    for i%=0 to 4
        units(i%)    =zero
    next i%
    first.detail.line%    =true%
    return

8100    rem-----accumulate pay info--------------------------
rem
rem    This routine will accumulate the pay.amt
rem    that has just been read in.
rem    Accumulation is based on the value
rem    of the PAY.REPORTING.CAT% variable.
rem    Note that there is no rate zero, but all other valid
rem    rates are accumulated.
rem
    on pay.reporting.cat% gosub \
        8101,\            rem rate 01
        8102,\            rem rate 02
        8102,\            rem rate 03
        8102,\            rem rate 04
        8105,\            rem rate 05 vacation taken
        8106,\            rem rate 06 sick leave taken
        8107,\            rem rate 07 comp time taken
        8108,\            rem rate 08 comp time earnd
        8109,\            rem rate 09 bonus
        8110,\            rem rate 10 tips collected
        8109,\            rem rate 11 advance
        8109,\            rem rate 12 sick pay
        8109,\            rem rate 13 vacation pay
        8109,\            rem rate 14 other excld pay
        8109,\            rem rate 15 expense reimb
        8116,\            rem rate 16 eic
        8109,\            rem rate 17 other pay
        8118,\            rem rate 18 tips reported
        8151,\            rem rate 19
        8120,\            rem rate 20 fwt
        8121,\            rem rate 21 swt
        8122,\            rem rate 22 lwt
        8123,\            rem rate 23 fica
        8124,\            rem rate 24 sdi
        8151,\            rem rate 25
        8151,\            rem rate 26
        8127,\            rem rate 27 advance repay
        8120,\            rem rate 28 fwt addon
        8121,\            rem rate 29 swt addon
        8122,\            rem rate 30 lwt addon
        8123,\            rem rate 31 fica addon
        8151,\            rem rate 32
        8133,\            rem rate 33 sys1
        8133,\            rem rate 34 sys2
        8133,\            rem rate 35 sys3
        8133,\            rem rate 36 sys4
        8133,\            rem rate 37 sys5
        8138,\            rem rate 38 emp1
        8138,\            rem rate 39 emp2
        8138,\            rem rate 40 emp3
        8151,\            rem rate 41
        8142,\            rem rate 42 company fica
        8143,\            rem rate 43 company futa
        8144,\            rem rate 44 company sui
        8151,\            rem rate 45
        8151,\            rem rate 46 other co cost
        8151,\            rem rate 47
        8151,\            rem rate 48
        8151,\            rem rate 49
        8151            rem rate 50 other ded
    return

8101    rem-----rate 01--------------------------------------
    units(1)=units(1)+pay.units
    reg.wages=reg.wages+pay.amt
    return

8102    rem-----rate 02,03,04--------------------------------
    units(pay.reporting.cat%)=units(pay.reporting.cat%)+pay.units
    other.earn=other.earn+pay.amt
    return

8105    rem-----rate 05 vacation taken-----------------------
    vac.taken=vac.taken+pay.units
    return

8106    rem-----rate 06 sick leave taken---------------------
    sl.taken=sl.taken+pay.units
    return

8107    rem-----rate 07 comp time taken----------------------
    comp.taken=comp.taken+pay.units
    return

8108    rem-----rate 08 comp time earned---------------------
    comp.earned=comp.earned+pay.units
    return

8109    rem-----rate 09 other normal pay types---------------
    other.earn=other.earn+pay.amt
    return

8110    rem-----rate 10 tips collected-----------------------
    tips=tips+pay.amt
    return

8116    rem-----rem rate 16 eic------------------------------
    eic=eic+pay.amt
    return

8118    rem-----rate 18 tips reported------------------------
    tips=tips+pay.amt
    tips.reported=tips.reported+pay.amt
    other.ded=other.ded+pay.amt
    return

8120    rem-----rem rate 20 fwt------------------------------
    fwt=fwt+pay.amt
    return

8121    rem-----rem rate 21 swt------------------------------
    swt=swt+pay.amt
    return

8122    rem-----rem rate 22 lwt------------------------------
    lwt=lwt+pay.amt
    return

8123    rem-----rem rate 23 fica-----------------------------
    fica=fica+pay.amt
    return

8124    rem-----rem rate 24 sdi------------------------------
    sdi=sdi+pay.amt
    return

8127    rem-----rem advance repay rate 27--------------------
    other.ded=other.ded+pay.amt
    return

8133    rem-----rem sys eds----------------------------------
    sys(pay.reporting.cat%-32)=sys(pay.reporting.cat%-32)+pay.amt
    if ded.sys.earn.ded$(pay.reporting.cat%-32)="E" \
        then    other.earn=other.earn+pay.amt \
        else    other.ded=other.ded+pay.amt
    return

8138    rem-----rem emp eds----------------------------------
    emp(pay.reporting.cat%-37)=emp(pay.reporting.cat%-37)+pay.amt
    if emp.ed.earn.ded$(pay.reporting.cat%-37)="E" \
        then    other.earn=other.earn+pay.amt \
        else    other.ded=other.ded+pay.amt
    return

8142    rem-----rem rate 42 co fica--------------------------
    co.fica=co.fica+pay.amt
    employer.cost=employer.cost+pay.amt
    return

8143    rem-----rem rate 43 co futa--------------------------
    co.futa=co.futa+pay.amt
    employer.cost=employer.cost+pay.amt
    return

8144    rem-----rem rate 44 co sui---------------------------
    co.sui=co.sui+pay.amt
    employer.cost=employer.cost+pay.amt
    return

8151    rem-----invalid rates--------------------------------
    print "blooooey"
    stop

9000    rem-----print detail line----------------------------
    if first.detail.line% \
        then    first.detail.line%=false%    :\
            gosub 9100    rem print detail header
    gosub 9150            rem get detail description
    gosub 9170            rem get comp,vac,sl amt
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    on edo%(pay.reporting.cat%) gosub \
        9200,\            rem print earning line
        9300,\            rem print deduction line
        9400            rem print other line
    print                rem trailing crlf for detail line
    console
    return

9050    rem-----print a blank line---------------------------
    gosub 6200            rem increment and test lines
    lprinter
    print
    console
    return

9100    rem-----print detail header--------------------------
    gosub 9050            rem print a blank line
    if stopit% then return
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print using "&";    \
        tab(001);"-------------E A R N I N G S-------------";
    print using "&";    \
        tab(051);"------D E D U C T I O N S------";
    print using "&";    \
        tab(095);"-----------O T H E R-----------"
    console
    gosub 9600            rem print separator line
    if stopit% then return
    return

9150    rem-----get detail description-----------------------
    if pay.reporting.cat%>=01 and \
       pay.reporting.cat%<=04 \
        then    detail.description$=    \
                pr1.rate.name$(pay.reporting.cat%)  :\
            return

    if pay.reporting.cat%>=33 and \
       pay.reporting.cat%<=37 \
        then    detail.description$=    \
                ded.sys.desc$(pay.reporting.cat%-32)  :\
            return

    if pay.reporting.cat%>=38 and \
       pay.reporting.cat%<=40 \
        then    detail.description$=    \
                emp.ed.desc$(pay.reporting.cat%-37)  :\
            return

    detail.description$=ed.desc.table$(pay.reporting.cat%)
    return

9170    rem-----get comp,vac,sl amt--------------------------
    if pay.reporting.cat%>=5 and pay.reporting.cat%<=8 \
        then    pay.amt=pay.units
    return

9200    rem-----print earning line---------------------------
    tab.location%=02
    gosub 9500            rem print details
    print using " ##,###.##";      \
        pay.units;
    print tab(046);"|";             rem print vertical separator
    print tab(088);"|";             rem print vertical separator
    return

9300    rem-----print deduction line-------------------------
    print tab(046);"|";             rem print vertical separator
    tab.location%=51
    gosub 9500            rem print details
    print tab(088);"|";             rem print vertical separator
    return

9400    rem-----print other line-----------------------------
    print tab(046);"|";             rem print vertical separator
    print tab(088);"|";             rem print vertical separator
    tab.location%=95
    gosub 9500            rem print details
    return

9500    rem-----print details--------------------------------
    print using "## /2345678901234/";     \
        tab(tab.location%),\
        pay.reporting.cat%,\
        detail.description$;
    print using " "+fn.bracket$(pay.amt,6,true%);     \
        abs(pay.amt);
    return

9600    rem-----print separator line-------------------------
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print tab(046);"|";             rem print vertical separator
    print tab(088);"|";             rem print vertical separator
    print                rem trailing crlf
    console
    return

11000    rem-----calc and print emp info----------------------
    gosub 9600            rem print separator line
    gosub 11100            rem print units total
    if stopit% then return
    gosub 6205            rem test lines
    gosub 11200            rem print wages and deds line
    if stopit% then return
    if net>emp.max.pay \
        then    gosub 11110    rem print over max warning
    if stopit% then return
    if net>pr1.void.check.amt and pr1.void.chks.over.max% \
        then    gosub 11120    rem print void message
    if stopit% then return
    if net<0 \
        then    gosub 11130    rem print under zero message
    if stopit% then return
    gosub 11300            rem calc distribution
    gosub 11400            rem print distribution line
    if stopit% then return
    return

11100    rem-----print units total----------------------------
    gosub 6205            rem test lines
    units.total=0
    no.totals%=0
    for i%=1 to 4
        line.cnt%=line.cnt%+1
        gosub 6300        rem check for interruption
        if stopit% then return
        if units(i%)=0 \
            then    goto 11101    rem break
        no.totals%=no.totals%+1
        lprinter
        if no.totals%=1 \
            then    print tab(10);"UNITS:";
        print using "/2345678901234/: ##,###.##";\
            tab(17),\
            pr1.rate.name$(i%),\
            units(i%)
        console
        units.total=units.total+units(i%)
11101
    next i%
    line.cnt%=line.cnt%+1
    gosub 6300            rem check for interruption
    if stopit% then return
    if no.totals%<=1 then return
    lprinter
    print using "    TOTAL UNITS: ##,###.##";\
        tab(17),\
        units.total
    console
    gosub 9050            rem a blank line
    return

11110    rem-----print over max warning-----------------------
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print \
"*** NET PAY EXCEEDS EMPLOYEE MAXIMUM"
    console
    return

11120    rem-----print void message---------------------------
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    trash%=fn.emsg%(05)
    lprinter
    print \
"*** VOID *** NET PAY EXCEEDS SYSTEM MAXIMUM *** CHECK WILL BE VOIDED ***"
    console
    return

11130    rem-----print under zero message---------------------
    gosub 6200            rem increment and test lines
    gosub 6300            rem check for interruption
    if stopit% then return
    trash%=fn.emsg%(07)
    lprinter
    print \
"*** VOID *** NET PAY IS LESS THAN ZERO *** NO CHECK WILL BE ISSUED ***"
    console
    return

11200    rem-----print wages and deds line--------------------
    gosub 11250            rem calculate gross + net pay
    gosub 11210            rem print hdr and amounts
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
            reg.wages;        \
            other.earn+eic;     \
            tips;            \
            fwt;            \
            swt;            \
            lwt;            \
            fica;            \
            sdi;            \
            other.ded;
    print using " "+fn.bracket$(net,6,true%);abs(net);
    print                rem trailing crlf
    console
    return

11250    rem-----calc gross and net pay-----------------------
    gross=(reg.wages+other.earn+tips)
    net=(gross+eic)-(fwt+swt+lwt+fica+sdi+other.ded)
    gross=gross-tips.reported
    return

11300    rem-----calc distribution and accum------------------
    gosub 11310            rem determine distributable pay
    for x%=1 to pr1.max.dist.accts%
        dist.out(x%)=                    \
            fn.round((emp.dist.percent(x%)/100)*    \
            distributable.pay)            :\
    next x%
    gosub 11320            rem assure that dist amts are exact
    for x%=1 to pr1.max.dist.accts%
        acct.amt(emp.dist.acct%(x%))=        \
            acct.amt(emp.dist.acct%(x%))+    \
            dist.out(x%)
    next x%
    return

11310    rem-----determine distributable pay------------------
    distributable.pay=(gross+employer.cost)
    return

11320    rem-----assure that dist amts are exact--------------
    temp=0
    for x%=1 to pr1.max.dist.accts%
        temp=temp+dist.out(x%)
    next x%
    if temp=distributable.pay \
        then    return
    temp=distributable.pay-temp    rem temp is difference
    x%=1
    while emp.dist.percent(x%)=0
        x%=x%+1
    wend
    dist.out(x%)=dist.out(x%)+temp
    return

11400    rem-----print distribution line----------------------
    line.cnt%=line.cnt%+1
    lprinter
    print                rem print a blank line
    console
    line.cnt%=line.cnt%+1
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print " ";                      rem leading blank
    print using " /2345678901/";      \
        "    GROSS   ",\
        "EMPLOYER EXP",\
        " TOTAL COST ",\
        "            ",\
        "            ";
    if pr1.dist.used% \
        then    gosub 11440 \    rem print dist headers
        else    print        rem trailing crlf
    console
    line.cnt%=line.cnt%+1
    gosub 6300            rem check for interruption
    if stopit% then return
    lprinter
    print " ";                      rem extra leading blank
    print using "  ###,###.## ";            \
            gross+eic;            \
            employer.cost;        \
            distributable.pay;
    if pr1.dist.used% \
        then    gosub 11450 \    rem print dist amounts
        else    print        rem trailing crlf
    print:print:print:print
    line.cnt%=line.cnt%+4
    console
    return

11440    rem-----print dist headers----------------------------
    for x%=1 to pr1.max.dist.accts%
        if emp.dist.percent(x%)<>0 \
            then    print using "  ###:/2345/ ";    \
                emp.dist.acct%(x%),        \
                acct.no$(emp.dist.acct%(x%));
    next x%
    return

11450    rem-----print dist amounts----------------------------
    print        "         DISTRIBUTION:   ";
    for x%=1 to pr1.max.dist.accts%
        if emp.dist.percent(x%)<>0 \
            then    print using " "+fn.bracket$             \
                    (dist.out(x%),6,true%); \
                    abs(dist.out(x%));
    next x%
    print                rem trailing crlf
    return

12500    rem-----distribute offset amounts--------------------
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
rem    EIC.CREDIT.ACCT (LIAB) is from DED file

rem CALCULATE EARNINGS:
    acct.amt(pr1.offset.cash.acct%)=acct.amt(pr1.offset.cash.acct%)-\
        gross

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

12700    rem-----accumulate company totals--------------------
    total.reg.wages     =total.reg.wages+    reg.wages
    total.other.earn    =total.other.earn+    other.earn
    total.tips        =total.tips+        tips
    total.tips.reported    =total.tips.reported+    tips.reported
    total.fwt        =total.fwt+        fwt
    total.swt        =total.swt+        swt
    total.lwt        =total.lwt+        lwt
    total.fica        =total.fica+        fica
    total.sdi        =total.sdi+        sdi
    total.other.ded     =total.other.ded+    other.ded
    total.net        =total.net+        net
    total.eic        =total.eic+        eic
    total.co.fica        =total.co.fica+     co.fica
    total.co.futa        =total.co.futa+     co.futa
    total.co.sui        =total.co.sui+        co.sui
    total.vac.taken     =total.vac.taken+    vac.taken
    total.sl.taken        =total.sl.taken+    sl.taken
    total.comp.taken    =total.comp.taken+    comp.taken
    total.comp.earned    =total.comp.earned+    comp.earned
    total.units(01)     =total.units(01)+    units(01)
    total.units(02)     =total.units(02)+    units(02)
    total.units(03)     =total.units(03)+    units(03)
    total.units(04)     =total.units(04)+    units(04)
    return

12800    rem-----initialize common counters-------------------
    total.reg.wages     =zero
    total.other.earn    =zero
    total.tips        =zero
    total.tips.reported    =zero
    total.fwt        =zero
    total.swt        =zero
    total.lwt        =zero
    total.fica        =zero
    total.sdi        =zero
    total.other.ded     =zero
    total.net        =zero
    total.eic        =zero
    total.co.fica        =zero
    total.co.futa        =zero
    total.co.sui        =zero
    total.vac.taken     =zero
    total.sl.taken        =zero
    total.comp.taken    =zero
    total.comp.earned    =zero
    total.units(1)        =zero
    total.units(2)        =zero
    total.units(3)        =zero
    total.units(4)        =zero
    return
