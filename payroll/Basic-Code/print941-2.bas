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
common prev.qtr.adj,  end.of.qtr$
common adj.total.inc.tax.with
common fica.non.tip.tax
common fica.tips.tax, total.fica.tax
common fica.adj,      adj.fica.tax
common total.taxes,   net.taxes

prgname$="PRINT941 15  JAN., 1980 "
rem---------------------------------------------------------
rem
rem      P A Y R O L L
rem
rem      P  R    I  N  T  9  4  1
rem
rem      SECTION ONE
rem
rem   COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS
rem
rem---------------------------------------------------------

program$="PRINT941"
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

dim emsg$(20)
emsg$(01)="PY601 SYSTEM HAS NOT ACHIEVED QUARTER-END STATUS"
emsg$(02)="PY602 PR2 FILE NOT FOUND"
emsg$(03)="PY603 COH FILE NOT FOUND"
emsg$(04)="PY604 UNABLE TO WRITE PR2 FILE"
emsg$(05)="PY605 'Y' OR 'N' ONLY"
emsg$(06)="PY606 NOT NUMERIC"
emsg$(07)="PY607 INVALID DATE"
emsg$(08)="PY608"
emsg$(09)="PY609"
emsg$(10)="PY610"
emsg$(11)="PY611"
emsg$(12)="PY612"
emsg$(13)="PY613"
emsg$(14)="PY614"
emsg$(15)="PY615"
emsg$(16)="PY616"
emsg$(17)="PY617"
emsg$(18)="PY618"
emsg$(19)="PY619"
emsg$(20)="PY620"

Rem #include "fpy941a"
rem---------------------------------------------------------
rem    SET UP DMS SCREEN EQUATES    FPY941A - 19/DEC/79

crt.field.count% = 43        rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem    LEGEND:    X  Y  LEN  RD  ATTRIB
rem        STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data           \
      12,4,43,0,5,\       rem   IO fld #1
      12,5,30,0,5,\       rem   IO fld #2
      57,5,8,0,5,\         rem   IO fld #3
      12,6,30,0,5,\       rem   IO fld #4
      57,6,10,0,5,\       rem   IO fld #5
      12,7,30,0,5,\       rem   IO fld #6
      12,8,23,0,5,\       rem   IO fld #7
      39,8,2,0,5,\         rem   IO fld #8
      45,8,5,0,5,\         rem   IO fld #9
      42,9,1,0,29,\       rem   IO fld #10
      62,10,5,0,28,\       rem   IO fld #11
      63,11,7,2,28,\       rem   IO fld #12
      63,12,7,2,28,\       rem   IO fld #13
      62,13,7,2,30,\       rem   IO fld #14
      63,14,7,2,28,\       rem   IO fld #15
      29,15,7,2,28,\       rem   IO fld #16
      63,15,7,2,28,\       rem   IO fld #17
      29,16,7,2,28,\       rem   IO fld #18
      63,16,7,2,28,\       rem   IO fld #19
      63,17,7,2,28,\       rem   IO fld #20
      62,18,7,2,30,\       rem   IO fld #21
      63,19,7,2,28,\       rem   IO fld #22
      63,20,7,2,28,\       rem   IO fld #23
      62,21,7,2,30,\       rem   IO fld #24
      63,22,7,2,28,\       rem   IO fld #25
      1,1,8,0,4,\        rem   O fld #26
      1,2,9,0,4,\        rem   O fld #27
      1,3,8,0,4,\        rem   O fld #28
      10,3,8,0,4,\         rem   O fld #29
      17,9,27,0,4,\       rem   O fld #30
      1,10,19,0,4,\       rem   O fld #31
      1,11,20,0,4,\       rem   O fld #32
      1,12,25,0,4,\       rem   O fld #33
      1,13,76,0,4,\       rem   O fld #34
      1,14,37,0,4,\       rem   O fld #35
      1,15,58,0,4,\       rem   O fld #36
      1,16,58,0,4,\       rem   O fld #37
      1,17,16,0,4,\       rem   O fld #38
      1,18,76,0,4,\       rem   O fld #39
      1,19,28,0,4,\       rem   O fld #40
      1,20,11,0,4,\       rem   O fld #41
      1,21,20,0,4,\       rem   O fld #42
      1,22,9,0,4
      rem    O fld #43
crt.data$(30)="PRINT NAME AND ADDRESS  [ ]"
crt.data$(31)="NUMBER OF EMPLOYEES"
crt.data$(32)="TOTAL WAGES AND TIPS"
crt.data$(33)="TOTAL INCOME TAX WITHHELD"
crt.data$(34)="ADJUSTMENT OF WITHHELD INCOME TAX FROM PREVIOUS QUARTERS    [              ]"
crt.data$(35)="ADJUSTED TOTAL OF INCOME TAX WITHHELD"
crt.data$(36)="TAXABLE FICA WAGES PAID                     TIMES 12.26% ="
crt.data$(37)="TAXABLE TIPS REPORTED                       TIMES  6.13% ="
crt.data$(38)="TOTAL FICA TAXES"
crt.data$(39)="ADJUSTMENT OF FICA TAXES                                    [              ]"
crt.data$(40)="ADJUSTED TOTAL OF FICA TAXES"
crt.data$(41)="TOTAL TAXES"
crt.data$(42)="EARNED INCOME CREDIT"
crt.data$(43)="NET TAXES"

i%=1
while i%<=43
  read    crt.x%(i%),crt.y%(i%),\
    crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then     co.name$=fn.spread$(pr1.co.name$,1)  \
  else     co.name$=pr1.co.name$
crt.len%(26)=len(co.name$)
crt.x%(26)=fn.center%(co.name$,crt.columns%-2)
crt.data$(26)=co.name$
if len(system.name$)<=30 \
  then     sys.name$=fn.spread$(system.name$,1)  \
  else     sys.name$=system.name$
crt.len%(27)=len(sys.name$)
crt.x%(27)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(27)=sys.name$
crt.data$(28)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then     fun.name$=fn.spread$(function.name$,1)  \
  else     fun.name$=function.name$
crt.len%(29)=len(fun.name$)
crt.x%(29)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(29)=fun.name$

rem---------------------------------------------------------

rem---------constants--------
null$ = ""
pw$ = null$    rem for future use
pm$ = null$
SECTION2$ = "PRNT941B"  rem name of second section
print.name% = false%

print using "&"; crt.clear$
gosub 10    rem set up file accessing
gosub 15    rem ok to run?
if not ok%  then gosub 5    rem see if they still wanna go
gosub 20    rem find & open pr2
if stopit%  then goto 999.1    rem abend
gosub 30    rem find & open coh
if stopit%  then \
    close pr2.file%  :\
    goto 999.1    rem abend
gosub 40    rem set up field equates


rem----------------------------------------------------
rem-------MAIN PROCESSING------------------------
gosub 90    rem do screen 1 calc's
gosub 500    rem display screen 1
gosub 100    rem get screen 1 data
rem------END OF MAIN PROCESSING-------------------
rem-----------------------------------------------------
trash% = fn.msg%("PROCEEDING TO SECOND SECTION")

chain fn.file.name.out$(SECTION2$,"",0,pw$,pm$) rem goto 2nd half

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
5    rem-----still want to run?-----
    if not fn.confirmed%  then \
        goto 999.2    rem prem. end
    trash% = fn.msg%(null$)
    ok% = true%
    end.of.qtr$ = "000000"
    return

10    rem----set up file accessing------
    pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
       coh.file.name$=fn.file.name.out$(coh.name$,"101",pr1.coh.drive%,pw$,pm$)
    return

15    rem-----ok to run?-----
    ok% = true%
    trash% = fn.decompose.date%(pr2.check.date$)
    yr$ = right$(blank$+str$(yr%),2)
    end.of.qtr$ = common.date$
    if pr2.last.q.ended% = 4  then    \
        end.of.qtr$ = yr$+"0331"
    if pr2.last.q.ended% = 1  then \
        end.of.qtr$ = yr$+"0630"
    if pr2.last.q.ended% = 2  then \
        end.of.qtr$ = yr$+"0930"
    if pr2.last.q.ended% = 3  then \
        end.of.qtr$ = yr$+"1231"
    return
REM========QTR END CHECKS NOT EXECUTED=================
    if pr1.m.used%    or  pr1.s.used%  then \
        gosub 16    rem check qtr end for mo & semimo
    if not ok%  then goto 15.9
    if pr1.b.used%    then \
        incr% = 14  :\
        gosub 17    rem check qtr end for biwk
    if not ok%  then goto 15.9
    if pr1.w.used%    then \
        incr% = 7   :\
        gosub 17    rem check qtr end for wk
15.9    if not ok%  then \
        trash% = fn.emsg%(1)
    return

16    rem-----check qtr end for mo & semimo----======NOT USED=========
    if pr2.last.sm.apply.no% <> 6  and \
       pr2.last.sm.apply.no% <> 12 and \
       pr2.last.sm.apply.no% <> 18 and \
       pr2.last.sm.apply.no% <> 24    then \
        ok% = false%:RETURN
    if mo% < val(mid$(end.of.qtr$,3,2))  then \
        ok% = false%    rem make sure pyperend hasn't just been run
    return

17    rem-----check qtr end for biwk & wk----======NOT USED==============
    if fn.incr.date$(pr2.check.date$,incr%) <= end.of.qtr$ \
        then ok% = false%
    return

20    rem-----check on pr2-----
    if end #pr2.file%  then 29.9
    open pr2.file.name$  as pr2.file%
    close pr2.file%
    return

29.9    rem-----no pr2 file-----
    trash% = fn.emsg%(2)
    stopit% = true%
    return    rem  thud

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
    trash% =  fn.emsg%(3)
    stopit% = true%
    return        rem crash
39.99    rem-----eof on coh-------

    return

40    rem-----field equates for screens------
    fld.print.name%  = 10
    fld.prev.adj%     = 14
    fld.adj.tax%     = 15
    fld.fica.adj%     = 21
    fld.adj.fica%     = 22
    fld.total.taxes% = 23
    fld.eic%     = 24
    fld.net%     = 25
    return

90    rem-----do initial calculations-----
    rem-----and set defaults-------
    print.name% = true%
    prev.qtr.adj = 0.0
    fica.adj = 0.0

91    tot.subj.to.with = coh.qtd.income.taxable + coh.qtd.tips +\
        coh.qtd.other.taxable + coh.qtd.other.nontaxable
    adj.total.inc.tax.with = coh.qtd.fwt.liab + prev.qtr.adj
    fica.non.tip.tax = coh.qtd.fica.taxable*0.1226
    fica.tips.tax = coh.qtd.tips*0.0613
    total.fica.tax = fica.non.tip.tax + fica.tips.tax

92    adj.fica.tax = total.fica.tax + fica.adj
    total.taxes = adj.total.inc.tax.with + adj.fica.tax
    eic = - coh.qtd.eic.credit
    net.taxes = total.taxes + eic
    return

rem-------beginning of screen 1 driver---------
100    rem-----get data for screen 1------
110    rem-----print co name?-----
    field% = fld.print.name%
    bad.data% = true%
    gosub 120    rem get input
    if valid%   then gosub 130    rem check data & display
    if cr%    then goto 111        rem goto next field
    if back%  then goto 112     rem wrap to last field
    if stopit%  then return
    if bad.data%  then goto 110    rem try it again

111    rem-----get prev. qtr. adj-----
    field% = fld.prev.adj%
    bad.data% = true%
    gosub 120        rem get input
    if valid%  then gosub 140    rem check data & display
    if stopit%  then return
    if cr%    then goto 112        rem goto next field
    if back%  then goto 110     rem goto previous field
    if bad.data%  then goto 111    rem try again

112    rem-----get fica adjust-----
    field% = fld.fica.adj%
    bad.data% = true%
    gosub 120        rem get input
    if valid%  then gosub 150    rem check data & display
    if stopit%  then return
    if cr%    then goto 110        rem wrap to 1st field
    if back%  then goto 111     rem prev field
    if bad.data%  then goto 112    rem try it again
    goto 110            rem from the top

rem------end of screen 1 driver-----------


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

130    rem-----check print.name------
    if in.uc$ = "Y"  then print.name% = true%:bad.data% = false%
    if in.uc$ = "N"  then print.name% = false%:bad.data% = false%
    if bad.data%  then  emsg% = 5:gosub 400 rem print emsg & delay
    trash% = fn.put%(fn.dsp.yorn$(print.name%),field%)
    return

140    rem------check prev.qtr.adj-----
    gosub 155    rem check neg amt & numeric
    if not numeric%  then \
        trash% = fn.put%(str$(prev.qtr.adj),field%) :\
        return    rem redisplay old data
    bad.data% = false%
    prev.qtr.adj = val(in$)
    gosub 91    rem recompute amounts
    gosub 521    rem re-display
    return

145    rem-----check numeric------
    numeric% = fn.numeric%(in$,7,2)
    if not numeric%  then \
        emsg% = 6  :\
        gosub 400    rem print emsg w/delay
    return

150    rem-----check fica.adj------
    gosub 155    rem check neg amt & numeric
    if not numeric%  then \
        trash% = fn.put%(str$(fica.adj),field%) :\
        return        rem redisplay old value
    bad.data% = false%
    fica.adj = val(in$)
    gosub 92    rem recompute amounts
    gosub 522    rem redisplay
    return

155    rem-----check neg amt--------
    neg$ = in$
    neg% = false%
    if val(in$) < 0  then \
        neg% = true% :\
        in$ = right$(in$,(len(in$)-1))
    gosub 145    rem check numeric
    if not numeric%  then return
    if neg%  then in$ = neg$
    return

rem---------end of screen 1 subroutines------------------------

400    rem-------display emsg & delay-------
    trash% = fn.emsg%(emsg%)
    for i% = 1 to 300
    next i%
    trash% = fn.msg%(null$)
    return

500    rem------get screen 1-------
    trash% = fn.put.all%(false%)    rem display literals
    gosub 520    rem display screen 1 data and load values
    return

520    rem-----display screen 1 data & load values-------
    trash% = fn.put%(pr1.co.name$,1)
    trash% = fn.put%(pr1.co.addr1$,2)
    trash% = fn.put%(fn.date.out$(end.of.qtr$),3)
    trash% = fn.put%(pr1.co.addr2$,4)
    trash% = fn.put%(pr1.fed.id$,5)
    trash% = fn.put%(pr1.co.addr3$,6)
    trash% = fn.put%(pr1.co.city$,7)
    trash% = fn.put%(pr1.co.state$,8)
    trash% = fn.put%(pr1.co.zip$,9)
    trash% = fn.put%(fn.dsp.yorn$(print.name%),10)
    trash% = fn.put%(str$(pr2.no.employees%),11)
    trash% = fn.put%(str$(tot.subj.to.with),12)
    trash% = fn.put%(str$(coh.qtd.fwt.liab),13)

521    trash% = fn.put%(str$(prev.qtr.adj),14)
    trash% = fn.put%(str$(adj.total.inc.tax.with),15)
    trash% = fn.put%(str$(coh.qtd.fica.taxable),16)
    trash% = fn.put%(str$(fica.non.tip.tax),17)
    trash% = fn.put%(str$(coh.qtd.tips),18)
    trash% = fn.put%(str$(fica.tips.tax),19)
    trash% = fn.put%(str$(total.fica.tax),20)

522    trash% = fn.put%(str$(fica.adj),21)
    trash% = fn.put%(str$(adj.fica.tax),22)
    trash% = fn.put%(str$(total.taxes),23)
    trash% = fn.put%(str$(eic),24)
    trash% = fn.put%(str$(net.taxes),25)
    return
