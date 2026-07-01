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
common print.name%    rem for 941 print 15/nov/79
common tot.subj.to.with
common prev.qtr.adj,end.of.qtr$
common adj.total.inc.tax.with
common fica.non.tip.tax
common fica.tips.tax,total.fica.tax
common fica.adj,adj.fica.tax
common total.taxes,net.taxes

prgname$="PRNT941B  15 JAN., 1980 "
rem---------------------------------------------------------
rem
rem      P A Y R O L L
rem
rem      P  R    I  N  T  9  4  1
rem
rem       SECTION 2
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PRNT941B"
function.name$ = "FORM 941 PRINT"

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

Rem #include "zparse"
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
Rem #include "zeditdte"
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

dim emsg$(14)
emsg$(01)="PY601 SYSTEM HAS NOT ACHIEVED QUARTER-END STATUS"
emsg$(02)="PY602 PR2 FILE NOT FOUND"
emsg$(03)="PY603 COH FILE NOT FOUND"
emsg$(04)="PY604 UNABLE TO WRITE PR2 FILE"
emsg$(05)="PY605 'Y' OR 'N' ONLY"
emsg$(06)="PY606 NOT NUMERIC"
emsg$(07)="PY607 INVALID DATE"
emsg$(08)="PY608"
emsg$(09)="PY609 INVALID RESPONSE"
emsg$(10)="PY610 PR2 FILE NOT FOUND--SECTION TWO"
emsg$(11)="PY611 UNABLE TO WRITE PR2--SECTION TWO"
emsg$(12)="PY612 COH FILE NOT FOUND--SECTION TWO"
emsg$(13)="PY613"

Rem #include "fpy941b"
rem---------------------------------------------------------
rem    SET UP DMS SCREEN EQUATES    FPY941B - 8/JAN/80

crt.field.count% = 82        rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem    LEGEND:    X  Y  LEN  RD  ATTRIB
rem        STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data           \
      34,3,7,2,20,\       rem   IO fld #1
      34,4,7,2,20,\       rem   IO fld #2
      34,5,7,2,20,\       rem   IO fld #3
      34,6,7,2,20,\       rem   IO fld #4
      34,8,7,2,20,\       rem   IO fld #5
      34,9,7,2,20,\       rem   IO fld #6
      34,10,7,2,20,\       rem   IO fld #7
      34,11,7,2,20,\       rem   IO fld #8
      34,13,7,2,20,\       rem   IO fld #9
      34,14,7,2,20,\       rem   IO fld #10
      34,15,7,2,20,\       rem   IO fld #11
      34,16,7,2,20,\       rem   IO fld #12
      50,3,8,0,29,\       rem   IO fld #13
      50,4,8,0,29,\       rem   IO fld #14
      50,5,8,0,29,\       rem   IO fld #15
      50,6,8,0,29,\       rem   IO fld #16
      50,8,8,0,29,\       rem   IO fld #17
      50,9,8,0,29,\       rem   IO fld #18
      50,10,8,0,29,\       rem   IO fld #19
      50,11,8,0,29,\       rem   IO fld #20
      50,13,8,0,29,\       rem   IO fld #21
      50,14,8,0,29,\       rem   IO fld #22
      50,15,8,0,29,\       rem   IO fld #23
      50,16,8,0,29,\       rem   IO fld #24
      62,3,7,2,28,\       rem   IO fld #25
      62,4,7,2,28,\       rem   IO fld #26
      62,5,7,2,28,\       rem   IO fld #27
      62,6,7,2,28,\       rem   IO fld #28
      62,8,7,2,28,\       rem   IO fld #29
      62,9,7,2,28,\       rem   IO fld #30
      62,10,7,2,28,\       rem   IO fld #31
      62,11,7,2,28,\       rem   IO fld #32
      62,13,7,2,28,\       rem   IO fld #33
      62,14,7,2,28,\       rem   IO fld #34
      62,15,7,2,28,\       rem   IO fld #35
      62,16,7,2,28,\       rem   IO fld #36
      34,7,7,2,20,\       rem   IO fld #37
      50,7,8,0,29,\       rem   IO fld #38
      62,7,7,2,28,\       rem   IO fld #39
      34,12,7,2,20,\       rem   IO fld #40
      50,12,8,0,29,\       rem   IO fld #41
      62,12,7,2,28,\       rem   IO fld #42
      34,17,7,2,20,\       rem   IO fld #43
      50,17,8,0,29,\       rem   IO fld #44
      62,17,7,2,28,\       rem   IO fld #45
      34,18,7,2,20,\       rem   IO fld #46
      62,18,7,2,28,\       rem   IO fld #47
      18,1,8,0,5,\         rem   IO fld #48
      62,2,7,2,28,\       rem   IO fld #49
      50,19,8,0,29,\       rem   IO fld #50
      62,19,7,2,28,\       rem   IO fld #51
      62,20,7,2,28,\       rem   IO fld #52
      18,21,7,2,28,\       rem   IO fld #53
      62,21,7,2,28,\       rem   IO fld #54
      12,13,23,0,1,\       rem   IO fld #55
      38,13,1,0,25,\       rem   IO fld #56
      1,1,70,0,4,\         rem   O fld #57
      1,2,74,0,4,\         rem   O fld #58
      2,3,73,0,4,\         rem   O fld #59
      2,4,73,0,4,\         rem   O fld #60
      2,5,73,0,4,\         rem   O fld #61
      2,6,73,0,4,\         rem   O fld #62
      4,7,18,0,4,\         rem   O fld #63
      2,8,73,0,4,\         rem   O fld #64
      2,9,73,0,4,\         rem   O fld #65
      2,10,73,0,4,\       rem   O fld #66
      2,11,73,0,4,\       rem   O fld #67
      4,12,19,0,4,\       rem   O fld #68
      2,13,73,0,4,\       rem   O fld #69
      2,14,73,0,4,\       rem   O fld #70
      2,15,73,0,4,\       rem   O fld #71
      2,16,73,0,4,\       rem   O fld #72
      4,17,18,0,4,\       rem   O fld #73
      1,18,18,0,4,\       rem   O fld #74
      1,19,74,0,4,\       rem   O fld #75
      1,20,60,0,4,\       rem   O fld #76
      1,21,60,0,4,\       rem   O fld #77
      37,13,3,0,0,\       rem   O fld #78
      3,1,8,0,0,\        rem   O fld #79
      3,2,9,0,0,\        rem   O fld #80
      3,3,8,0,0,\        rem   O fld #81
      12,3,8,0,0
      rem    O fld #82
crt.data$(57)="DEPOSIT PER END                  LIABILITY         DATE         AMOUNT"
crt.data$(58)="OVERPAYMENT FROM PREVIOUS QUARTER...........................[            ]"
crt.data$(59)=" FIRST   | DAYS 1 THROUGH 7                     [        ]  [            ]"
crt.data$(60)=" MONTH   | DAYS 8 THROUGH 15                    [        ]  [            ]"
crt.data$(61)=" OF      | DAYS 16 THROUGH 22                   [        ]  [            ]"
crt.data$(62)=" QUARTER | DAYS 23 THROUGH END                  [        ]  [            ]"
crt.data$(63)="   FIRST MONTH TOTAL:"
crt.data$(64)=" SECOND  | DAYS 1 THROUGH 7                     [        ]  [            ]"
crt.data$(65)=" MONTH   | DAYS 8 THROUGH 15                    [        ]  [            ]"
crt.data$(66)=" OF      | DAYS 16 THROUGH 22                   [        ]  [            ]"
crt.data$(67)=" QUARTER | DAYS 23 THROUGH END                  [        ]  [            ]"
crt.data$(68)="   SECOND MONTH TOTAL:"
crt.data$(69)=" THIRD   | DAYS 1 THROUGH 7                     [        ]  [            ]"
crt.data$(70)=" MONTH   | DAYS 8 THROUGH 15                    [        ]  [            ]"
crt.data$(71)=" OF      | DAYS 16 THROUGH 22                   [        ]  [            ]"
crt.data$(72)=" QUARTER | DAYS 23 THROUGH END                  [        ]  [            ]"
crt.data$(73)="   THIRD MONTH TOTAL:"
crt.data$(74)="TOTAL FOR QUARTER:"
crt.data$(75)="FINAL DEPOSIT FOR QUARTER:......................[        ]  [            ]"
crt.data$(76)="TOTAL DEPOSITS FOR QUARTER:................................."
crt.data$(77)="OVERPAYMENT:....                  UNDEPOSITED TAXES DUE:...."
crt.data$(78)="[ ]"

i%=1
while i%<=82
  read    crt.x%(i%),crt.y%(i%),\
    crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then     co.name$=fn.spread$(pr1.co.name$,1)  \
  else     co.name$=pr1.co.name$
crt.len%(79)=len(co.name$)140
crt.x%(79)=fn.center%(co.name$,crt.columns%-2)
crt.data$(79)=co.name$
if len(system.name$)<=30 \
  then     sys.name$=fn.spread$(system.name$,1)  \
  else     sys.name$=system.name$
crt.len%(80)=len(sys.name$)
crt.x%(80)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(80)=sys.name$
crt.data$(81)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then     fun.name$=fn.spread$(function.name$,1)  \
  else     fun.name$=function.name$
crt.len%(82)=len(fun.name$)
crt.x%(82)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(82)=fun.name$

rem---------------------------------------------------------

rem---------constants--------
null$ = ""
pw$ = null$    rem for future use
pm$ = null$
function.name$ = "FORM 941 PRINT"

print using "&"; crt.clear$
gosub 10    rem set up file accessing
gosub 20    rem find & open pr2
if stopit%  then goto 999.1    rem abend
gosub 30    rem find & open coh
if stopit%  then \
    close pr2.file%  :\
    goto 999.1    rem abend
gosub 40    rem set up field equates


rem----------------------------------------------------
rem-------MAIN PROCESSING------------------------
gosub 100    rem do calculations
gosub 550    rem display screen 2
gosub 210    rem get screen 2 data
trash% = fn.msg%("PROCEEDING TO PRINT SECTION")
for i% = 1 to 400
next i%     rem keep msg flying
gosub 300    rem print form
rem------END OF MAIN PROCESSING-------------------
rem-----------------------------------------------------

if end.of.qtr$ <> "000000"  then \
    gosub 25    rem rewrite pr2
close pr2.file%


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

rem-----------------------------------------------------
rem--------SUBROUTINES--------------------------------
rem-----set up routines-------
10    rem----set up file accessing------
    pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
       coh.file.name$=fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pm$)
    return

20    rem-----check on pr2-----
    if end #pr2.file%  then 29.9
    open pr2.file.name$  as pr2.file%
    if end #pr2.file%  then 29.99
    return

25    rem-----write new pr2----
    pr2.941.printed% = true%
    print #pr2.file%;\
#include "ipypr2"
    return

29.9    rem-----no pr2 file-----
    trash% = fn.emsg%(10)
    stopit% = true%
    return    rem  thud
29.99    rem-----unable to write pr2-----
    pr2.941.printed% = false%
    trash% =  fn.emsg%(11)
    goto 999.1    rem abend
    return

30    rem-----check on coh & read-----
Rem #include "ipydmcoh"
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

    if end #coh.file%  then 39.9
    open coh.file.name$  recl coh.len%  as coh.file%
    if end #coh.file%  then 39.99
    read #coh.file%;\
Rem #include "ipycoh"
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

39.9    rem-----no coh file------
    trash% =  fn.emsg%(12)
    stopit% = true%
    return        rem crash
39.99    rem-----eof on coh-------

    return

40    rem-----field equates for screens------
    fld.overpay%     = 49
    fld.real.tot%     = 47
    fld.final.date%  = 50
    fld.final.dep%     = 51
    fld.final.total% = 52
    fld.first.mo%     = 39
    fld.second.mo%     = 42
    fld.third.mo%     = 45
    fld.new.overpay% = 53
    fld.taxes.due%     = 54
    fld.prompt%     = 55
    fld.prompt.resp% = 56
    start.lit%     = 55
    end.lit%     = 77
    return

100    rem----calc's for 2nd screen-----
    overpay = 0.0
    for i% = 1 to 3
        sum.amt = 0.0
        k% = (i% - 1)*4
        for j% = 1 to 4
            sum.amt = sum.amt + coh.tax(j% + k%)
        next j%
        if i% = 1  then \
            first.mo = sum.amt :\
            real.first.mo = sum.amt
        if i% = 2  then \
            second.mo = sum.amt :\
            real.second.mo = sum.amt
        if i% = 3  then \
            third.mo = sum.amt :\
            real.third.mo = sum.amt
    next i%
    dim real.coh.tax(12)
    for i% = 1 to 12
        real.coh.tax(i%) = coh.tax(i%)
        if coh.date$(i%) = "000000"  then \
           coh.date$(i%) = null$
    next i%
    j% = 0
    gosub 105    rem get wk no
    first.mo$ = coh.date$(wk.no%)
    j% = 4
    gosub 105    rem get wk no
    second.mo$ = coh.date$(wk.no%)
    j% = 8
    gosub 105    rem get wk no
    third.mo$ = coh.date$(wk.no%)

    total.for.qtr = first.mo+second.mo+third.mo
    real.total.for.qtr = real.first.mo+real.second.mo+real.third.mo
    final.dep.date$ = null$
    final.deposit = 0.0
    grand.total.for.qtr = real.total.for.qtr + final.deposit
    gosub 110    rem calculate over/due charges
    return

105    rem-----get wk no-------
    k% = 4
    while k% > 0
        wk.no% = j% + k%
        if coh.date$(wk.no%) <> null$  then return
        k% = k% - 1
    wend
    return

110    rem-----calculate over/due taxes-----
    taxes.due = net.taxes - grand.total.for.qtr
    new.overpay = grand.total.for.qtr - net.taxes
    if taxes.due < 0.0  then taxes.due = 0.0
    if new.overpay < 0.0  then new.overpay = 0.0
    return

120    rem------get data-------
    valid%    = false%
    stopit% = false%
    cr%    = false%
    back%    = false%
    trash%    = fn.get%(2,field%)  rem mask 2 accepts cr,back,esc ctl-chars
    if in.status% = req.valid%  then valid% = true%:return
    if in.status% = req.stopit%  then stopit% = true%:return
    if in.status% = req.cr%  then cr% = true%:return
    if in.status% = req.back%  then back% = true%
    return

145    rem-----check numeric------
    numeric% = fn.numeric%(in$,7,2)
    if not numeric%  then \
        emsg% = 6  :\
        gosub 400    rem print emsg w/delay
    return
rem---------end of screen 1 subroutines------------------------

rem-----beginning of screen 2 driver----------
210    rem-----get data for screen 2------
    field% = fld.overpay%
    bad.data% = true%
    gosub 120    rem get data
    if valid%  then gosub 240    rem check overpay
    if stopit%  then return
    if cr%    then goto 220        rem 1st field of first mo.
    if back%  then goto 235     rem jump around table
    if bad.data%  then goto 210    rem try this one again

220    rem----get table data----
    coh.tab% = 1
    while coh.tab% <=12
        field% = coh.tab% + 12        rem date column
        date% = true%
        bad.data% = true%
221        gosub 120        rem get data
        if valid%   then gosub 260    rem check date & display
        if stopit%  then return
        if back% or cr%  then gosub 250 rem check table co-ords
        if back%  then goto 222     rem amt field of prev wk
        if bad.data%  then goto 221    rem try this one again

222        field% = coh.tab% + 24        rem amt column
        date% = false%
        bad.data% = true%
223        gosub 120        rem get data
        if valid%  then gosub 270    rem check amt & display
        if stopit%  then return
        if back% or cr%  then gosub 250 rem check table co-ords
        if back%  then goto 221     rem date field of same wk
        if bad.data%  then goto 223    rem try this one again

        coh.tab% = coh.tab% + 1     rem move to next wk
    wend

230    rem---get final date & final amt-----
    field% = fld.final.date%
    bad.data% = true%
231    gosub 120        rem get data
    if valid%  then gosub 260    rem check date & display
    if stopit%  then return
    if cr%    then goto 235        rem final amt
    if back%  then \
        field% = 36  :\
        coh.tab% = 12  :\
        goto 223        rem amt field, last wk
    if bad.data%  then goto 231

235    rem----final amt-------
    bad.data% = true%
    field% = fld.final.dep%
236    gosub 120    rem get data
    if valid%  then gosub 280    rem check amt & display
    if stopit%  then return
    if cr%    then goto 210        rem to overpay fld
    if back%  then goto 230     rem to final date
    if bad.data%  then goto 236    rem try this one again
    goto 210            rem back to top of screen

rem------end of screen 2 driver---------------

240    rem-----check overpayment-------
    gosub 145    rem check numeric
    if not numeric%  then \
        trash% = fn.put%(str$(overpay),field%) :\
        return
    bad.data% = false%
    overpay = val(in$)
    start% = 1
    end% = 12
    gosub 275    rem add weekly amts
    real.total.for.qtr = amt + overpay
    grand.total.for.qtr = real.total.for.qtr + final.deposit
    gosub 110    rem figure taxes due/over
    trash% = fn.put%(in$,field%)
    trash% = fn.put%(str$(real.total.for.qtr),fld.real.tot%)
    gosub 245    rem display other changed fields
    return

245    rem-----display other changes fields-----
    trash% = fn.put%(str$(grand.total.for.qtr),fld.final.total%)
    trash% = fn.put%(str$(taxes.due),fld.taxes.due%)
    trash% = fn.put%(str$(new.overpay),fld.new.overpay%)
    return

250    rem------check table co-ords for back%-----
    if cr%    then bad.data% = false%     rem allow to fall through
    if back% and date%  then \
        coh.tab% = coh.tab% - 1 :\    rem decrement wk if in date fld
        field% = field% + 11    :\
        date% = false%
    if back% and not date%    then \
        field% = field% - 12    :\    rem decrement fld if in amt fld
        date% = true%
    if field% < 13 or coh.tab% < 1    then \
        goto 210        rem out of table & to top of screen
    return

260    rem-----check date--------
    invalid% = false%
    if not fn.edit.date%(in$)  then \
        gosub 265 \    rem check funny date
       else \
        date$ = fn.date.in$
    if invalid%  then \
        trash% = fn.put%(crt.data$(field%),field%) :\
        return
    bad.data% = false%
    trash% = fn.put%(fn.date.out$(date$),field%)
    if field% = 16    then \
        trash% = fn.put%(fn.date.out$(date$),38) rem 1st mo
    if field% = 20    then \
        trash% = fn.put%(fn.date.out$(date$),41)  rem 2nd mo
    if field% = 24    then \
        trash% = fn.put%(fn.date.out$(date$),44)  rem 3rd mo
    return

265    rem------check funny date------
    if in$ = null$    or \
       in.uc$ = "NONE"  then \
        in$ = null$ :\
        date$ = null$ :\
        return
    emsg% = 7
    gosub 400    rem display emsg & delay
    invalid% = true%
    return

270    rem------check amts--------
    gosub 145    rem check numeric
    if not numeric%  then \
        trash% = fn.put%(str$(real.coh.tax(coh.tab%)),field%) :\
        return
    bad.data% = false%
    real.coh.tax(coh.tab%) = val(in$)
    if coh.tab% < 5  then \     rem first mo
        start% = 1     :\
        end% = 4     :\
        gosub 275     :\  rem add weeks
        mo.field% = fld.first.mo%  :\
        mo.amt = amt
    if coh.tab% > 4  and coh.tab% < 9  then \
        start% = 5     :\
        end% = 8     :\
        gosub 275     :\  rem add weeks
        mo.field% = fld.second.mo%  :\
        mo.amt = amt
    if coh.tab% > 8  then \
        start% = 9    :\
        end%   = 12    :\
        gosub 275    :\  rem add weeks
        mo.field% = fld.third.mo%  :\
        mo.amt = amt
    start% = 1
    end% = 12
    gosub 275    rem add weeks
    real.total.for.qtr = amt + overpay
    grand.total.for.qtr = real.total.for.qtr + final.deposit
    gosub 110    rem figure taxes due/over
    trash% = fn.put%(in$,field%)
    trash% = fn.put%(str$(mo.amt),mo.field%)
    trash% = fn.put%(str$(real.total.for.qtr),fld.real.tot%)
    gosub 245    rem display other fields
    return

275    rem-----add weekly amts-------
    amt = 0.0
    for i% = start% to end%
        amt = amt + real.coh.tax(i%)
    next i%
    return

280    rem-----check final dep & display--------
    gosub 145    rem check numeric
    if not numeric%  then \
        trash% = fn.put%(str$(final.deposit),fld.final.dep%) :\
        return
    bad.data% = false%
    final.deposit = val(in$)
    grand.total.for.qtr = real.total.for.qtr + final.deposit
    gosub 110    rem figure new.over/due taxes
    trash% = fn.put%(in$,field%)
    gosub 245    rem display other fields
    return
rem-------end of screen 2 subroutines--------------------------


300    rem-----print form-------------------
    print using "&"; crt.clear$
    gosub 310    rem set used flags
    disp% = 0    rem displacement from left edge
    amt$ = "#,###,###.## "
    amt.tab% = disp% + 69
    brkt.tab% = amt.tab% -1
    names% = disp% + 16
    col1% = disp% + 34
    col2% = disp% + 46
    col3% = disp% + 56
    table$ = amt$ +"&" +amt$
    again% = true%
   while again%
    gosub 350    rem test alignment?
    print:print
    if print.name%    then \
        print using "&";tab(names%);left$(pr1.co.name$+blank$,43) :\
        print using "&&";tab(names%);pr1.co.addr1$;tab(disp%+50);\
          fn.date.out$(end.of.qtr$) :\
        print using "&&";tab(names%);pr1.co.addr2$;tab(disp%+58);\
          pr1.fed.id$  :\
        print using "&";tab(names%);pr1.co.addr3$  :\
        print using "&&&";tab(names%);pr1.co.city$;tab(disp%+41);\
            pr1.co.state$;tab(disp%+45);pr1.co.zip$  \
      else \
        print:print:print:print:print
    print:print:print
    print using "##,###"; tab(disp%+72);pr2.no.active.emps%
    print
    print using amt$;tab(amt.tab%);tot.subj.to.with
    print using amt$;tab(amt.tab%);coh.qtd.fwt.liab
    print using fn.bracket$(prev.qtr.adj,7,true%);tab(brkt.tab%);\
        abs(prev.qtr.adj)
    print using amt$;tab(amt.tab%);adj.total.inc.tax.with
    print using amt$+amt$;tab(disp%+37);coh.qtd.fica.taxable;\
        tab(brkt.tab%);fica.non.tip.tax
    print using amt$+amt$;tab(disp%+37);coh.qtd.tips;\
        tab(brkt.tab%);fica.tips.tax
    print using amt$;tab(amt.tab%);total.fica.tax
    print using fn.bracket$(fica.adj,7,true%);tab(brkt.tab%);abs(fica.adj)
    print using amt$;tab(amt.tab%);adj.fica.tax
    print using amt$;tab(amt.tab%);total.taxes
    print using fn.bracket$(-coh.qtd.eic.credit,7,true%);tab(brkt.tab%);\
        coh.qtd.eic.credit
    print using amt$;tab(amt.tab%);net.taxes
    if fn.abort%  then gosub 390    rem abort printout
    rem-----print screen 2 info-------
    print using "&";tab(disp%+20);fn.date.out$(end.of.qtr$)
    print using amt$; tab(col3%);overpay

    for i% = 1 to 4
        print using table$;tab(col1%);coh.tax(i%);tab(col2%);\
            crt.data$(i%+12);tab(col3%);real.coh.tax(i%)
    next i%
    print using table$;tab(col1%);first.mo;tab(col2%);crt.data$(38);\
        tab(col3%);real.first.mo

    for i% = 5 to 8
        print using table$;tab(col1%);coh.tax(i%);tab(col2%);\
            crt.data$(i%+12);tab(col3%);real.coh.tax(i%)
    next i%
    print using table$;tab(col1%);second.mo;tab(col2%);crt.data$(41);\
        tab(col3%);real.second.mo

    for i% = 9 to 12
        print using table$;tab(col1%);coh.tax(i%);tab(col2%);\
            crt.data$(i%+12);tab(col3%);real.coh.tax(i%)
    next i%
    print using table$;tab(col1%);third.mo;tab(col2%);crt.data$(44);\
        tab(col3%);real.third.mo

    print using amt$+amt$;tab(col1%);total.for.qtr;tab(col3%-1);\
        real.total.for.qtr
    print
    print using "&"+amt$;tab(col2%);crt.data$(50),tab(col3%);final.deposit
    print
    print using amt$;tab(amt.tab%);grand.total.for.qtr
    print:print
    print using amt$;tab(amt.tab%);taxes.due
    print
    print using amt$;tab(disp%+36);new.overpay
    print:print:print:print
    print using "&";tab(disp%+9);fn.date.out$(common.date$)
    print:print:print
    gosub 360    rem  do it again?
   wend
    return

310    rem-----set used flags------
    for i% = 1 to crt.field.count%
        trash% =fn.set.used%(false%,i%)
    next i%
    trash% = fn.set.used%(true%,fld.prompt%)
    trash% = fn.set.used%(true%,fld.prompt.resp%)
    for i% = 79 to 82
        trash% = fn.set.used%(true%,i%)
        trash% = fn.lit%(i%)
    next i%
    trash% = fn.set.used%(true%,78)
    return

350    rem-----align forms------
    prompt$ = "PRINT ALIGNMENT MARKS?"
    trash% = fn.put%(prompt$,fld.prompt%)
    trash% = fn.lit%(78)
    while true%
        gosub 370    rem get answer
        lprinter
        if yes% or cr%    then gosub 380        rem print marks
        if no%    then return
    wend
    return

360    rem-----again?-------
    again% = false%
    console
    prompt$ = "PRINT ANOTHER FORM?"
    trash% = fn.put%(prompt$,fld.prompt%)
    gosub 370    rem get answer
    if yes%  then again% = true%
    return

370    rem-----get answer------
    field% = fld.prompt.resp%
    yes% = false%
    no% = false%
    gosub 120    rem get data
    if cr%    then return
    if in.uc$ = "Y"  then \
        yes% = true% :\
        trash% = fn.put%(in.uc$,fld.prompt.resp%) :\
        return
    if in.uc$ = "N"  then \
        no% = true% :\
        trash% = fn.put%(in.uc$,fld.prompt.resp%) :\
        return
    if stopit%  then gosub 390    rem display msg & go bye-bye
    trash% = fn.put%(null$,fld.prompt.resp%)
    emsg% = 9
    gosub 400    rem display emsg & delay
    goto 370    rem try it again
    return

380    rem-----print alignment marks------
    print tab(disp%+3);"|_____________________________________________________________________________|"
    return

390    rem------print stop req & stop------
    trash% = fn.msg%("STOP REQUESTED")
    close pr2.file%
    goto 999.2    rem prem end
    return

400    rem-----display emsg & delay-----
    trash% = fn.emsg%(emsg%)
    for i% = 1 to 450
    next i%
    trash% = fn.msg%(null$)
    return

550    rem-----get screen 2------
    for i% = start.lit% to end.lit%
        trash% = fn.lit%(i%)    rem display literals
    next i%
    gosub 560    rem display screen 2 data & load
    return

560    rem-------display screen 2 data & load values------
    trash% = fn.put%(fn.date.out$(end.of.qtr$),48)
    trash% = fn.put%(str$(overpay),fld.overpay%)
rem monthly tables
    for i% = 1 to 12
        trash% = fn.put%(str$(coh.tax(i%)),i%)
        if coh.date$(i%) <> null$  then \
            trash% = fn.put%(fn.date.out$(coh.date$(i%)),i%+12) \
           else \
            trash% = fn.put%(null$,i%+12)
        trash% = fn.put%(str$(coh.tax(i%)),i%+24)
    next i%
    trash% = fn.put%(str$(first.mo),37)
    trash% = fn.put%(fn.date.out$(first.mo$),38)
    trash% = fn.put%(str$(real.first.mo),39)
    trash% = fn.put%(str$(second.mo),40)
    trash% = fn.put%(fn.date.out$(second.mo$),41)
    trash% = fn.put%(str$(real.second.mo),42)
    trash% = fn.put%(str$(third.mo),43)
    trash% = fn.put%(fn.date.out$(third.mo$),44)
    trash% = fn.put%(str$(real.third.mo),45)
rem rest of screen
    trash% = fn.put%(str$(total.for.qtr),46)
    trash% = fn.put%(str$(real.total.for.qtr),47)
    trash% = fn.put%(fn.date.out$(common.date$),50)
    trash% = fn.put%(str$(final.deposit),51)
    trash% = fn.put%(str$(grand.total.for.qtr),52)
    trash% = fn.put%(str$(taxes.due),54)
    trash% = fn.put%(str$(new.overpay),53)
    return

