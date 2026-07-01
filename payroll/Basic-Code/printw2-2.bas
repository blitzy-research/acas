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
prgname$="PRINTW2 10 JANUARY, 1979 "
rem---------------------------------------------------------
rem
rem      P A Y R O L L
rem
rem      P  R    I  N  T  W  2
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PRINTW2"
function.name$ = "FORM W2 PRINT"

Rem #include "ipyconst"
rem     JAN. 18, 1980
system$="PY":version$=" REL:1.0 "
system.name$="PAYROLL SYSTEM"
cpyrght$="COPYRIGHT (C) 1980, APPLEWOOD COMPUTERS "
dummy$="PYppppI00":null$="":asc.quote%= 34
dim crt.data$(0),crt.x%(0),crt.y%(0),crt.len%(0),crt.rd%(0),crt.attrib%(0)
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
Rem #include "zdmsused"
rem    NOV.  1, 1979       -------------------------------------
rem
rem    fn.set.used%(t.f%, id%)     REM STANDARD
rem
rem-------------------------------------------------------------
%nolist
def fn.set.used%(t.f%, id%)
    crt.attrib%(id%)= crt.attrib%(id%) and not crt.used%
    crt.attrib%(id%)= crt.attrib%(id%) or  (crt.used% and t.f%)
    return
fend
%list
Rem #include "zdmsbrt"
rem    NOV.  1, 1979       -------------------------------------
rem
rem    fn.set.brt%(t.f%, id%)        REM STANDARD
rem
rem-------------------------------------------------------------
%nolist
def fn.set.brt%(t.f%, id%)
    crt.attrib%(id%)= crt.attrib%(id%) and not crt.brt%
    crt.attrib%(id%)= crt.attrib%(id%) or  (crt.brt% and t.f%)
    return
fend
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
Rem #include "znumeric"
rem     Apr. 24, 1978
Rem #include znumber
rem    Jan. 13, 1979
def fn.num%(no$)
    if match(left$(pound$,len(no$)),no$,1)<>1 and len(no$)>0 \
        then   fn.num%=false% \
        else   fn.num%=true%
    return
fend


def fn.numeric%(no$,left.digits%,right.digits%)
    fn.numeric%=false%
    radix%=match(".",no$,1)
    if radix%=0 then \
        radix%=len(no$)+1
    hi$=left$(no$,radix%-1)
    lo$=right$(no$,len(no$)-radix%)
    if len(hi$)>left.digits% or \
       len(lo$)>right.digits% then \
        return
    if not fn.num%(hi$) or \
       not fn.num%(lo$) then \
        return
    fn.numeric%=true%
    return
fend

Rem #include "zckdigit"
rem      Nov. 21, 1978
def fn.ck.dig$(no$)
    sum%=0
    xx5%=1
    while xx5%<=len(no$)
        sum%=sum%+xx5%*val(mid$(no$,xx5%,1))
        xx5%=xx5%+1
    wend
    remainder%=sum%-(int(sum%/11)*11)
    if remainder%=10 then remainder%=0
    fn.ck.dig$=str$(remainder%)
    return
fend

Rem #include "zdmsconf"
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
Rem #include "zdmsabrt"
REM----- DEC. 14, 1979 -----------------------------------
REM
def fn.abort%        REM STANDARD
REM
REM-------------------------------------------------------
%nolist
fn.abort%=false%
if constat% = 0  \
    then   return
trash%= conchar%
crt.col%= 30: crt.row%= 20
crt.stop$="(TYPE ""STOP"" TO STOP PROGRAM)"
crt.continue$="(PRESS RETURN TO CONTINUE)"
console
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);crt.stop$
print using "&";fn.crt.sca$(crt.row%, crt.col%);crt.continue$;
if pr1.leading.crlf% then print
crt.count%= 0
while crt.count% < 5
    crt.print%= false%
    crt.data%= conchar%
    crt.count%= crt.count%+ 1
    if crt.data%= asc.cr% and crt.count%= 1 \
        then print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);\
         left$(blank$, len(crt.stop$)): \
         print using "&";fn.crt.sca$(crt.row%, crt.col%); \
         left$(blank$, len(crt.continue$)+5 ): \
         lprinter: RETURN
    if ucase$(chr$(crt.data%))<> mid$("STOP"+chr$(asc.cr%),crt.count%,1)\
        and crt.data%<> asc.lspace% and crt.data%<> asc.del% \
        then trash%=fn.msg%(bell$+system$+ \
        "018 PRESS RETURN OR TYPE ""STOP"" "):\
        print using "&";fn.crt.sca$(crt.row%, \
        crt.col%+len(crt.continue$)+crt.count%);crt.backspace$;: \
        crt.count%= crt.count%-1: crt.print%= true%
    if crt.data%= asc.del% or crt.data%= asc.lspace% \
        then  crt.count%= crt.count%-1
    if (crt.data%= asc.lspace% or crt.data%= asc.del%) and crt.count% > 0 \
        then  print using "&";fn.crt.sca$ \
        (crt.row%, crt.col%+len(crt.continue$)+crt.count%); \
        crt.backspace$; :crt.count%=crt.count%-1: crt.print%=true%
    if pr1.leading.crlf% and crt.print%  then print
wend
print using "&";fn.crt.sca$(crt.row%- 1, crt.col%);left$(blank$,len(crt.stop$))
print using "&";fn.crt.sca$(crt.row%,crt.col%);left$(blank$,len(crt.continue$)+5 )
fn.abort%=true%
return
fend
%list
Rem #include "zdspyorn"
rem    5-oct-79
rem
rem    function that converts a boolean value to a string
rem    'Y' or 'N'
rem
    def fn.dsp.yorn$(boolean.value%)
    if boolean.value%    \
       then fn.dsp.yorn$ = "Y"\
       else fn.dsp.yorn$ = "N"
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

def fn.leap.year%(year%)
    if (year%/4.0)-int(year%/4.0)=0 \
        then   fn.leap.year% = true% \
        else   fn.leap.year% = false%
    return
fend
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

Rem #include "zdateinc"
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
Rem #include "zflip"
def fn.name.flip$(name$)    REM 19-NOV-79
    temp% = match("*",name$,1)
    if temp% = 0 \
       then \
        fn.name.flip$ = name$ :\
        return \
       else \
        fn.name.flip$ = right$(name$,len(name$)-temp%) + \
           " " + left$(name$,temp%-1)
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
Rem #include "ipydmhis"
dim his.qtd.sys         (pr1.max.sys.eds%)    rem  9/26/79
dim his.qtd.emp         (pr1.max.emp.eds%)
dim his.qtd.units        (4)
dim his.ytd.sys         (pr1.max.sys.eds%)
dim his.ytd.emp         (pr1.max.emp.eds%)
dim his.ytd.units        (4)
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
Rem #include "fpyw2"
rem---------------------------------------------------------
rem    SET UP DMS SCREEN EQUATES    FPYW2 - 4/DEC/79

crt.field.count% = 40        rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem    LEGEND:    X  Y  LEN  RD  ATTRIB
rem        STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data           \
      10,8,1,0,29,\       rem   IO fld #1
      10,9,1,0,29,\       rem   IO fld #2
      10,10,1,0,29,\       rem   IO fld #3
      10,11,1,0,29,\       rem   IO fld #4
      28,13,1,0,28,\       rem   IO fld #5
      74,8,1,0,29,\       rem   IO fld #6
      74,10,2,0,28,\       rem   IO fld #7
      74,12,2,0,28,\       rem   IO fld #8
      74,14,2,0,28,\       rem   IO fld #9
      65,17,1,0,29,\       rem   IO fld #10
      31,16,5,0,25,\       rem   IO fld #11
      31,18,5,0,25,\       rem   IO fld #12
      28,17,5,0,25,\       rem   IO fld #13
      48,21,5,0,25,\       rem   IO fld #14
      1,1,8,0,4,\        rem   O fld #15
      1,2,9,0,4,\        rem   O fld #16
      1,3,8,0,4,\        rem   O fld #17
      10,3,8,0,4,\         rem   O fld #18
      3,6,75,0,4,\         rem   O fld #19
      39,7,1,0,4,\         rem   O fld #20
      8,8,16,0,4,\         rem   O fld #21
      39,8,37,0,4,\       rem   O fld #22
      8,9,21,0,4,\         rem   O fld #23
      39,9,1,0,4,\         rem   O fld #24
      8,10,23,0,4,\       rem   O fld #25
      39,10,38,0,4,\       rem   O fld #26
      8,11,20,0,4,\       rem   O fld #27
      39,11,1,0,4,\       rem   O fld #28
      39,12,38,0,4,\       rem   O fld #29
      11,13,29,0,4,\       rem   O fld #30
      39,14,38,0,4,\       rem   O fld #31
      3,15,75,0,4,\       rem   O fld #32
      39,16,1,0,4,\       rem   O fld #33
      39,17,28,0,4,\       rem   O fld #34
      39,18,1,0,4,\       rem   O fld #35
      3,19,75,0,4,\       rem   O fld #36
      5,16,32,0,0,\       rem   O fld #37
      5,18,32,0,0,\       rem   O fld #38
      9,17,25,0,0,\       rem   O fld #39
      19,21,28,0,0
      rem    O fld #40
crt.data$(19)="---------------------------------------------------------------------------"
crt.data$(20)="|"
crt.data$(21)="1  ALL EMPLOYEES"
crt.data$(22)="|  PRINT STATE AND LOCAL AMOUNTS  [ ]"
crt.data$(23)="2  RANGE OF EMPLOYEES"
crt.data$(24)="|"
crt.data$(25)="3  TERMINATED EMPLOYEES"
crt.data$(26)="|  NUMBER OF FORMS PER EMPLOYEE   [  ]"
crt.data$(27)="4  A SINGLE EMPLOYEE"
crt.data$(28)="|"
crt.data$(29)="|  NUMBER OF LINES BETWEEN FORMS  [  ]"
crt.data$(30)="ENTER SELECTION [ ]         |"
crt.data$(31)="|  STARTING PRINT COLUMN          [  ]"
crt.data$(32)="------------------------------------|--------------------------------------"
crt.data$(33)="|"
crt.data$(34)="|        PRINT TEST FORM [ ]"
crt.data$(35)="|"
crt.data$(36)="---------------------------------------------------------------------------"
crt.data$(37)="STARTING EMPLOYEE NUMBER [     ]"
crt.data$(38)="ENDING EMPLOYEE NUMBER   [     ]"
crt.data$(39)="EMPLOYEE NUMBER   [     ]"
crt.data$(40)="NOW PRINTING EMPLOYEE NUMBER"

i%=1
while i%<=40
  read    crt.x%(i%),crt.y%(i%),\
    crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then     co.name$=fn.spread$(pr1.co.name$,1)  \
  else     co.name$=pr1.co.name$
crt.len%(15)=len(co.name$)
crt.x%(15)=fn.center%(co.name$,crt.columns%-2)
crt.data$(15)=co.name$
if len(system.name$)<=30 \
  then     sys.name$=fn.spread$(system.name$,1)  \
  else     sys.name$=system.name$
crt.len%(16)=len(sys.name$)
crt.x%(16)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(16)=sys.name$
crt.data$(17)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then     fun.name$=fn.spread$(function.name$,1)  \
  else     fun.name$=function.name$
crt.len%(18)=len(fun.name$)
crt.x%(18)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(18)=fun.name$

rem---------------------------------------------------------

dim emsg$(20)
emsg$(01)="PY621 SYSTEM HAS NOT ACHIEVED YEAR-END STATE"
emsg$(02)="PY622 EMPLOYEE FILE NOT FOUND"
emsg$(03)="PY623 UNEXPECTED EOF ON EMPLOYEE FILE"
emsg$(04)="PY624 HISTORY FILE NOT FOUND"
emsg$(05)="PY625 UNEXPECTED EOF ON HISTORY FILE"
emsg$(06)="PY626 PR2 FILE NOT FOUND"
emsg$(07)="PY627 UNABLE TO WRITE TO PR2 FILE"
emsg$(08)="PY628 INVALID RESPONSE"
emsg$(09)="PY629 Y OR NO ONLY"
emsg$(10)="PY630 NUMERIC INTEGER ONLY"
emsg$(11)="PY631 INVALID CHECK DIGIT"
emsg$(12)="PY632 EMPLOYEE NUMBER TOO HIGH"
emsg$(13)="PY633 STARTING EMPLOYEE NUMBER CANNOT BE GREATER THAN ENDING NUMBER"
emsg$(14)="PY634 OUT OF RANGE"
emsg$(15)="PY635 THERE ARE NO TERMINATED EMPLOYEES IN THE FILE"
emsg$(16)="PY636"
emsg$(17)="PY637"
emsg$(18)="PY638"
emsg$(19)="PY639"
emsg$(20)="PY640"

REM--------CONSTANTS--------
a$ = "&"
disp% = 5    rem displacement for tabbing
col1% = disp% + 4
col2% = disp% + 21
col3% = disp% + 34
col4% = disp% + 49
col5% = disp% + 64
option% = 1
lines.to.next.form% = 4
forms.per.emp% = 1
print.local% = true%
dol$ = " ###,###.##"
line.9$ = a$+a$+a$+dol$
line.11$ = a$+dol$+dol$+dol$+dol$
line.13$ = a$+a$+dol$
line.15$ = dol$+dol$+a$
line.17$ = line.15$
pw$ = null$    rem may be used in future
pm$ = null$    rem  '   '  '   '    '
fld.all.emp%    = 1    :lit.all.emp%      = 21
fld.range.emp%    = 2    :lit.range.emp%   = 23
fld.term.emp%    = 3    :lit.term.emp%      = 25
fld.single.emp% = 4    :lit.single.emp%  = 27
fld.select%    = 5
fld.start.emp%    = 11    :lit.start.emp%   = 37
fld.end.emp%    = 12    :lit.end.emp%      = 38
fld.emp.num%    = 13    :lit.emp.num%      = 39
fld.print.local% = 6
fld.no.forms%    = 7
fld.no.lines%    = 8
fld.no.columns% = 9
fld.test.form%    = 10
fld.emp.no%    = 14    :lit.emp.no%      = 40

REM-------setting up-------
print using a$; crt.clear$    rem clear screen
gosub 50    rem throw up screen
first% = true%
gosub 5     rem set up file accessing
gosub 10    rem ok to run--stop if not ok
gosub 20    rem open EMP & read hdr--stop if not there
gosub 30    rem open HIS & read hdr---'   '   '    '
gosub 40    rem open PR2----- stop if not there

REM-------------------------------------------------------
REM----------MAIN DRIVER----------------------------------
WHILE true%
    gosub 190    rem clear optional fields
    gosub 100    rem do requests
    if start.emp.no% < 1  then start.emp.no% = 1
    if end.emp.no% > pr2.no.employees%  then \
        end.emp.no% = pr2.no.employees%
    gosub 180    rem set up emp no field
    if stopit% then \
        goto 901    rem  end
    lprinter
    emp.rec% = start.emp.no%

    while emp.rec% <= end.emp.no%    and not emp.eof%
        gosub 25    rem read emp.file
        if emp.eof%  then \
            goto 900    rem shouldn't happen unless term only
        gosub 35    rem read his file
        gosub 200    rem calculate & accumulate
        gosub 400    rem display emp no
        gosub 300    rem print form
        emp.rec% = emp.rec% + 1
    wend
900    console
WEND

901    if all.emp%  then \
        gosub 45    rem write new pr2


    gosub 500    rem close files
    if first%  then goto 999.2    rem prem.end
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

REM-----------------------------------------------
REM----------subroutines--------------------------
5    rem-----set up file accessing-----
       emp.file.name$=fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pm$)
       his.file.name$=fn.file.name.out$(his.name$,"101",pr1.his.drive%,pw$,pm$)
    pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
    return

10    rem-----ok to run?-----
    yearend% = true%
    trash% = fn.decompose.date%(pr2.check.date$)
    yr$ = right$(blank$+str$(yr%),2)
    if pr2.last.q.ended% = 4  then    \
        end.of.qtr$ = yr$+"1231" \
       else \
        end.of.qtr$ = common.date$
    return
REM====REST OF YR END CHECKS NOT EXECUTED===============
    if pr1.m.used%    or  pr1.s.used%  then \
        gosub 16    rem check qtr end for mo & semimo
    if not yearend%  then goto 5.9
    if pr1.b.used%    then \
        incr% = 14  :\
        gosub 17    rem check qtr end for biwk
    if not yearend%  then goto 5.9
    if pr1.w.used%    then \
        incr% = 7   :\
        gosub 17    rem check qtr end for wk
5.9    if not yearend%  then \
        trash% = fn.emsg%(1) :\
        gosub 18    rem get confirmation to run
    return

16    rem-----check yr end for mo & semimo----=====NOT USED=====
    if pr2.last.sm.apply.no% <> 24    then \
        yearend% = false%
    return

17    rem-----check yr end for biwk & wk--=========NOT USED=======
    if fn.incr.date$(pr2.check.date$,incr%) <= end.of.qtr$ \
        then yearend% = false%
    return

18    rem-----still want to run?---=======NOT USED=======
    if not fn.confirmed%  then \
        goto 999.2    rem prem. end
    trash% = fn.put.all%(true%)
    return


REM---------------------------------------------------
REM----------file handling routines-----------------
20    rem----open emp.file & read-------
    if end #emp.file%  then 29.9
    open emp.file.name$  recl emp.len%  as emp.file%
    if end #emp.file%  then 29.99
    read #emp.file%,1;\
Rem #include "ipyemphd"
        emp.hdr.no.recs%,\      rem 10/30/79
        emp.hdr.no.del.recs%,\
        emp.hdr.next.del.rec%,\
        emp.hdr.101,\
        emp.hdr.102,\
        emp.hdr.201$

    return

25    rem-----read employee record-----
    read #emp.file%,emp.rec%+1;\    rem account for hdr
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


    if emp.eof%  then return
    if emp.status$ = "D"  or \
      (emp.status$ = "L" and term.only%)  or \
      (emp.status$ = "A" and term.only%)  then \
        emp.rec% = emp.rec% + 1 :\
        goto 25
    emp.emp.name$ = fn.name.flip$(emp.emp.name$)
    return

29.9    rem-----emp file not found-----
    emsg% = 2
    gosub 99    rem display msg & delay
    goto 999.1    rem die, die, die
29.99    rem--------------- eof on emp-----
    emp.eof% = true%
    console
    if term.only% and no.forms% = 0  then \
        emsg% = 15  :\
        gosub 99    :\    rem display & delay
        return
    if term.only%  then return
    emsg% = 3
    gosub 99    rem display msg & stall
    close emp.file%, his.file%, pr2.file%
    goto 999.1    rem crash

30    rem-----open his file & read hdr-----
    if end #his.file%  then 39.9
    open his.file.name$  recl his.len%  as his.file%
    if end #his.file%  then 39.99
    read #his.file%,1;\
Rem #include "ipyhishd"
        his.hdr.no.recs%,\        rem  11/12/79
        his.hdr.last.to.date$,\
        his.hdr.101,\
        his.hdr.102,\
        his.hdr.201$

    return

35    rem-----read his record-----
    read #his.file%,emp.rec%+1;\    rem account for hdr
Rem #include "ipyhis"
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

    his.ytd.fica.gross = his.ytd.fica.taxable
    his.ytd.gross = his.ytd.income.taxable + his.ytd.other.taxable + \
            his.ytd.other.nontaxable + his.ytd.tips
    return

39.9    rem-----no his file------
    emsg% = 4
    gosub 99    rem display msg
    close emp.file%
    goto 999.1    rem crash
39.99    rem-----unexpected eof on his-------
    if term.only% and no.forms% = 0 \
        then return
    console
    emsg% = 5
    gosub 99    rem display msg
    close emp.file%, his.file%, pr2.file%
    goto 999.1    rem pfffffft

40    rem-----open pr2-----
    if end #pr2.file%  then 49.9
    open pr2.file.name$  as pr2.file%
    if end #pr2.file%  then 49.99
    return

45    rem-----write new pr2----
    if not yearend%  then return
    pr2.w2.printed% = true%
    print #pr2.file%;\
#include "ipypr2"
    return

49.9    rem-----no pr2 file-----
    emsg% = 6
    gosub 99    rem display emsg
    close emp.file%, his.file%
    goto 999.1    rem thud
49.99    rem-----unable to write pr2-----
    pr2.w2.printed% = false%
    emsg% = 7
    gosub 99    rem display msg
    close emp.file%, his.file%, pr2.file%
    goto 999.1    rem abend
REM------------end of file accessing-----------------
50    rem-----put up screen & get defaults-----
    start.lit% = 15
    end.lit% = 36
    for i% = start.lit% to end.lit%
        trash% = fn.lit%(i%)
    next i%
    trash% = fn.put%(fn.dsp.yorn$(print.local%),fld.print.local%)
    trash% = fn.put%(str$(forms.per.emp%),fld.no.forms%)
    trash% = fn.put%(str$(lines.to.next.form%),fld.no.lines%)
    trash% = fn.put%(str$(disp%),fld.no.columns%)
    trash% = fn.put%(fn.dsp.yorn$(true%),fld.test.form%)
    return

99    rem-----display emsg & stall-----
    trash% = fn.emsg%(emsg%)
    for i% = 1 to 300
    next i%
    return

REM-------------request subroutines-----------------
100    rem-----request print options-------
    field% = fld.select%
    while field% < fld.start.emp%
101        gosub 100.9    rem get input
        if stopit%  then return
        if cr% or back%  then \
            gosub 102    :\ rem change fld no
            goto 101    rem try again
        if not valid%  then \
            goto 101    \ rem do again
        else \
            on field% gosub \
                100.99,100.99,100.99,100.99, \    rem error
                105,    \  rem print option
                130,    \  rem print state & local info
                120,    \  rem number of forms
                160,    \  rem number of lines betw. forms
                170,    \  rem starting print column
                140,    \  rem test form
                100.99,100.99,100.99,100.99    rem error
        if valid%  then field% = field% + 1
        if stopit%  then return
    wend
    return

100.9    rem-----get data-----
    gosub 100.91    rem clear flags
    trash% = fn.get%(2,field%)
    if in.status% = req.valid%  then valid% = true%:return
    if in.status% = req.stopit%  then stopit% = true%:return
    if in.status% = req.cr%  then cr% = true%:return
    if in.status% = req.back%  then back% = true%
    return

100.91    rem-----clear flags------
    valid% = false%
    stopit% = false%
    cr% = false%
    back% = false%
    return

100.99    rem-----invalid field number-----
    field% = fld.select%
    valid% = false%
    return

102    rem----change field number-----
    if cr%    then field% = field% + 1
    if back%  then field% = field% - 1
    if field% > fld.test.form%  then \
        field% = fld.select%
    if field% < fld.select%  then \
        field% = fld.test.form%
    return

105    rem-----get selection--------
    gosub 106    rem check option
    trash% = fn.put%(str$(option%),fld.select%)
    if not valid%  then return
    on option% gosub    111, \    rem all emps
                112, \    rem range of emps
                113, \    rem all terminated
                114    rem one emp
    field% = fld.select%
    first% = false%
    if start.emp.no% <> 1  or \
       end.emp.no% <> pr2.no.employees%  then \
        partial% = true%
    return

105.5    rem-----get lit #-----
    if option% = fld.all.emp%  then \
        lit% = lit.all.emp%
    if option% = fld.range.emp%  then \
        lit% = lit.range.emp%
    if option% = fld.term.emp%  then \
        lit% = lit.term.emp%
    if option% = fld.single.emp%  then \
        lit% = lit.single.emp%
    return

106    rem-----check option------
    if not first%  then \
        gosub 106.5    rem clear brt field & clear emp no flds
    valid% = true%
    digits% = 1
    gosub 126    rem verify numeric int
    if not num%  then \
        valid% = false% :\
        return
    if in.num% > 0    and in.num% <= 4  then \
        option% = in.num%  :\
        gosub 107    :\ rem set brtness & display arrow
        return
    emsg% = 14
    gosub 99    rem display emsg & delay
    valid% = false%
    return

106.5    rem-----clear brt fields & clear emp no flds------
    if option% = 0    then return
    gosub 105.5    rem get lit no
    trash% = fn.set.brt%(false%,lit%)
    trash% = fn.put%(null$,option%)
    trash% = fn.lit%(lit%)
    if option% = 1 or option% = 3  then return
    gosub 190    rem clear optional fields
    return

107    rem-----set brt & display arrow------
    gosub 105.5    rem gt lit #
    trash% = fn.set.brt%(true%,lit%)
    trash% = fn.lit%(lit%)
    trash% = fn.put%(">",option%)
    return

111    rem------all employees------
    all.emp% = true%
    term.only% = false%
    start.emp.no% = 1
    end.emp.no% = pr2.no.employees%
    return

112    rem-----range of emps------
    all.emp% = false%
    term.only% = false%
    trash% = fn.set.used%(true%,fld.start.emp%)
    trash% = fn.set.used%(true%,fld.end.emp%)
    trash% = fn.set.used%(true%,lit.start.emp%)
    trash% = fn.set.used%(true%,lit.end.emp%)
    trash% = fn.lit%(lit.start.emp%)
    trash% = fn.lit%(lit.end.emp%)
    trash% = fn.put%("00014",fld.start.emp%)
    emp$ = right$("000"+str$(pr2.no.employees%),4)
    ck.dig$ = fn.ck.dig$(emp$)
    trash% = fn.put%(emp$+ck.dig$,fld.end.emp%)

112.1    rem---starting emp no-----
    field%    = fld.start.emp%
    gosub 100.9    rem get data
    if stopit% or back%  then \
        stopit% = false% :\
        valid% = false%  :\
        return
    if cr%    then gosub 112.7    :\  rem plug in default
        goto 112.2    rem get ending number
    gosub 112.9    rem validate emp no
    if emp.invalid%  then goto 112.1    rem try again
    start.emp.no% = emp.rec%

112.2    rem----- ending emp no---------
    field% = fld.end.emp%
    gosub 100.9    rem get data
    if stopit%  then valid% = false%:return
    if cr%    then gosub 112.7    :\  rem plug in default
        return
    if back%  then goto 112.1    rem get starting no
    gosub 112.9    rem validate emp no
    if emp.invalid%  then goto 112.2    rem try again
    end.emp.no% = emp.rec%
    if start.emp.no% > end.emp.no%    then \
        emsg% = 13    :\
        gosub 99    :\  rem display
        goto 112.1    rem try again

112.7    rem------plug in def or max-----
    if field% = fld.start.emp%  then \
        emp.rec% = 1 \
       else \
        emp.rec% = pr2.no.employees%
    return

112.9    rem-----validate emp no------
    emp.invalid% = false%
    digits% = 5
    gosub 126    rem validate num int
    if not num%  then \
        emp.invalid% = true%:return
    emp$ = left$(in$,4)
    if right$(in$,1) <> fn.ck.dig$(emp$)  then \
        emp.invalid% = true%  :\
        emsg% = 11  :\
        gosub 99    :\    rem display
        return
    emp.rec% = val(emp$)
    if emp.rec% > pr2.no.employees%  then \
        emp.invalid% = true%  :\
        emsg% = 12    :\
        gosub 99    rem display
    return

113    rem-----all terminated emps-----
    all.emp% = false%
    start.emp.no% = 1
    end.emp.no% = pr2.no.employees%
    term.only% = true%
    return

114    rem-----one employee------
    all.emp% = false%
    term.only% = false%
    trash% = fn.set.used%(true%,fld.emp.num%)
    trash% = fn.set.used%(true%,lit.emp.num%)
    trash% = fn.lit%(lit.emp.num%)
114.1    gosub 114.9    rem get emp.no
    if stopit%  then stopit% = false%:valid% = false%:return
    gosub 112.9    rem validate number
    if emp.invalid%  then goto 114.1    rem try again
    start.emp.no% = emp.rec%
    end.emp.no% = emp.rec%
    valid% = true%
    return

114.9    rem----get emp no, mask 1-----
    stopit% = false%
    valid% = false%
    trash% = fn.get%(1,fld.emp.num%)
    if in.status% = req.valid%  then valid% = true%:return
    if in.status% = req.stopit%  then stopit% = true%
    return

120    rem-----request # of copies-------
    digits% = 2
    gosub 126    rem check num integer
    if not num%  then valid% = false%
    if in.num% < 1 or in.num% > 10    then \
        valid% = false%  :\
        emsg% = 14    :\
        gosub 99    rem display msg
    if valid%  then forms.per.emp% = in.num%
    trash% = fn.put%(str$(forms.per.emp%),fld.no.forms%)
    return

126    rem-----check numeric integer------
    num% = fn.num%(in$)
    if len(in$)>digits% or not num%  then \
        num%=false%: \
        in.num% = 0 :\
        emsg% = 10  :\
        gosub 99    rem dislpay
    in.num% = val(in$)
    return

130    rem-----request print state & local amts------
    gosub 139    rem check response
    if t%  then print.local% = true%
    if f%  then print.local% = false%
    trash% = fn.put%(fn.dsp.yorn$(print.local%),fld.print.local%)
    return

139    rem-----check y/n-------
    t%=false%:f%=false%
    if in.uc$ = "Y"  or in.uc$ = "T" \
        then    t%=true%:return
    if in.uc$ = "N"  or in.uc$ = "F" \
        then    f%=true%:return
    valid% = false%
    emsg% = 9
    gosub 99    rem display emsg
    return

140    rem-----request test form-----
    test.form% = true%
    gosub 139    rem check response
    if t%  then test.form% = true%
    if f%  then test.form% = false%
    trash% = fn.put%(fn.dsp.yorn$(test.form%),fld.test.form%)
    if test.form%  then \
        valid% = false% :\
        gosub 145  :\    rem get test data
        lprinter  :\
        gosub 300 :\    rem print form
        console
    return

145    rem-----phony values for test form------
    emp.emp.name$    = "NOAH COUNT, ESQ."
    emp.addr1$    = "123456 789th AVE."
    emp.addr2$    = "APARTMENT 98765"
    emp.city$    = "CHICAGO"
    emp.state$    = "IL"
    emp.zip$    = "12345"
    subtotal$    = null$
    his.ytd.eic    = 111111.11
    emp.ssn$    = "000-00-0000"
    his.ytd.fwt    = 222222.22
    his.ytd.gross    = 333333.33
    his.ytd.fica    = 444444.44
    his.ytd.fica.gross = 555555.55
    emp.pension$    = "Y"
    his.ytd.tips    = 666666.66
    his.ytd.swt    = 777777.77
    his.ytd.gross    = 888888.88
    his.ytd.lwt    = 999999.99
    return


160    rem------how many lines betw forms------
    digits% = 2
    gosub 126    rem check num int
    if not num%  then valid% = false%
    if in.num% < 1    or in.num% > 99  then \
        valid% = false% :\
        emsg% = 14    :\
        gosub 99    rem display emsg & delay
    if valid%  then lines.to.next.form% = in.num%
    trash% = fn.put%(str$(lines.to.next.form%),fld.no.lines%)
    return

170    rem-----get displacement from left edge-------
    digits% = 2
    gosub 126    rem check num int
    if not num%  then valid% = false%
    if in.num% < 1    or in.num% > 50  then \
        valid% = false%  :\
        emsg% = 14     :\
        gosub 99    rem display & delay
    if valid%  then \
        disp% = in.num% :\
        col1% = disp% + 4  :\
        col2% = disp% + 21 :\
        col3% = disp% + 34 :\
        col4% = disp% + 49 :\
        col5% = disp% + 64
    trash% = fn.put%(str$(disp%),fld.no.columns%)
    return

180    rem------set up emp no field--------
    trash% = fn.set.used%(true%,fld.emp.no%)
    trash% = fn.set.used%(true%,lit.emp.no%)
    trash% = fn.lit%(lit.emp.no%)
    return

190    rem-----clear optional fields-------
    trash% = fn.clr%(fld.start.emp%)
    trash% = fn.clr%(lit.start.emp%)
    trash% = fn.clr%(lit.end.emp%)
    trash% = fn.clr%(fld.end.emp%)
    trash% = fn.clr%(lit.emp.num%)
    trash% = fn.clr%(fld.emp.num%)
    trash% = fn.clr%(lit.emp.no%)
    trash% = fn.clr%(fld.emp.no%)
    return

199    rem-----premature burial-----
    gosub 500    rem close files
    trash% = fn.msg%("STOP REQUESTED")
    goto 999.2    rem prem end
    return

rem----------end of requests-------------------------

REM-------------processing routines------------------
200    rem-----calculations & accumulations-----
    sub.eic     = sub.eic + his.ytd.eic
    sub.fwt     = sub.fwt + his.ytd.fwt
    sub.fica    = sub.fica + his.ytd.fica
    sub.fica.gross    = sub.fica.gross + his.ytd.fica.gross
    sub.tips    = sub.tips + his.ytd.tips
    sub.swt     = sub.swt + his.ytd.swt
    sub.lwt     = sub.lwt + his.ytd.lwt
    sub.gross    = sub.gross + his.ytd.gross
    return

300    rem-----print form-----
    printed.per.emp% = 0
    while printed.per.emp% < forms.per.emp%
        gosub 305    rem check abort
        gosub 310    rem print co name & addr
        print using line.9$;tab(col1%);pr1.co.city$;tab(disp%+24);\
            pr1.co.state$;tab(disp%+27);pr1.co.zip$;tab(col3%); \
            his.ytd.eic
        print
        print using line.11$;tab(col1%);emp.ssn$;tab(col2%); \
            his.ytd.fwt;tab(col3%);his.ytd.gross;tab(col4%);\
            his.ytd.fica;tab(col5%);his.ytd.fica.gross
        print
        print using line.13$;tab(col1%);emp.emp.name$;tab(col3%); \
            emp.pension$;tab(col5%);his.ytd.tips
        print
        print using a$;tab(col1%);emp.addr1$;
        if print.local%  then \
            print using line.15$;tab(col3%);his.ytd.swt; \
                tab(col4%);his.ytd.gross;tab(col5%); \
                pr1.co.state$ \
           else  print    rem suppress rest of line
        print using a$;tab(col1%);emp.addr2$
        print using a$;tab(col1%);emp.city$;
        if print.local%  then \
            print using line.17$;tab(col3%);his.ytd.lwt; \
                tab(col4%);his.ytd.gross;tab(col5%); \
                pr1.co.city$  \
           else  print
        print using a$+a$;tab(col1%);emp.state$;tab(disp%+10);emp.zip$
        gosub 360    rem space to next form
        printed.per.emp% = printed.per.emp% + 1
        if test.form%  then return
    wend
    no.forms% = no.forms% + 1
    if no.forms% >= 41  then \
        gosub 350    rem do subtotal form
    return

305    rem-----abort print?-----_
    if fn.abort%  then \
        gosub 199    rem premature end
    if crt.data% = asc.cr% and crt.count% = 1 \
        then  trash% = fn.put.all%(true%) :\ rem only re-display
              lprinter    rem  screen if abort msg appeared
    return

310    rem-----do emp addr lines------
    gosub 305    rem check abort
    print:print
    print using a$;tab(disp%+26);pr1.state.id$
    print
    print using a$+a$;tab(col1%);left$(pr1.co.name$+blank$,30); \
        tab(disp%+36);subtotal$
    print using a$;tab(col1%);pr1.co.addr1$
    print using a$+a$;tab(col1%);pr1.co.addr2$;tab(col3%);pr1.fed.id$
    print using a$;tab(col1%);pr1.co.addr3$
    return

350    rem-----do subtotal form-----
    gosub 305    rem check abort
    subtotal$ = "X"
    gosub 310    rem do co name & addr
    print using line.9$;tab(col1%);pr1.co.state$;tab(disp%+10); \
        pr1.co.zip$;tab(col3%);sub.eic
    print
    print using line.11$;null$;tab(col2%);sub.fwt;tab(col3%);sub.gross; \
        tab(col4%);sub.fica;tab(col5%);sub.fica.gross
    print
    print using line.13$;null$;null$;tab(col5%);sub.tips
    print
    if print.local%  then \
        print using line.15$;tab(col3%);sub.swt;tab(col4%);sub.gross;\
            tab(col5%);pr1.co.state$  \
       else  print
    print
    if print.local%  then \
        print using line.17$;tab(col3%);sub.lwt;tab(col4%);sub.gross;\
            tab(col5%);pr1.co.city$  \
       else  print
    print
    gosub 360    rem space to next form
    no.forms% = 0
    gosub 370    rem zero accum's
    subtotal$ = null$
    return

360    rem-----space to next form-----
    for i% = 1 to lines.to.next.form%
        print
    next i%
    return

370    rem-----zero accum's-----
    sub.eic     = 0
    sub.fwt     = 0
    sub.fica    = 0
    sub.fica.gross    = 0
    sub.tips    = 0
    sub.swt     = 0
    sub.lwt     = 0
    sub.gross    = 0
    return

400    rem-----print emp.no on screen-----
    console
    trash% = fn.put%(emp.no$,fld.emp.no%)
    lprinter
    return

rem-----------end of processing routines-----------------

500    rem-----close files-----
    close emp.file%
    close his.file%
    close pr2.file%
    return
