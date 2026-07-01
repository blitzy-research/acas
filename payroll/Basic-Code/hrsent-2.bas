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
prgname$="HRSENT    18 JANUARY, 1979 "
rem----------------------------------------------------------
rem
rem    H  R  S  E  N  T
rem
rem    REGULAR HOURS ENTRY PROGRAM
rem
rem    P A Y R O L L       S Y S T E M
rem
rem    COPYRIGHT (C) 1979, APPLEWOOD COMPUTERS.
rem
rem----------------------------------------------------------

program$="HRSENT"
function.name$ = "PAY TRANSACTION ENTRY"

Rem #include "ipyconst"
rem     JAN. 18, 1980
system$="PY":version$=" REL:1.0 "
system.name$="PAYROLL SYSTEM"
cpyrght$="COPYRIGHT (C) 1980, APPLEWOOD COMPUTERS "
dummy$="PYppppI00":null$="":asc.quote%= 34
dim crt.data$(0),crt.x%(0),crt.y%(0),crt.len%(0),crt.rd%(0),crt.attrib%(0)
Rem #include "zserial"
rem      June 22, 1979
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
Rem #include "ipyokcat"
rem-----WHAT CAN BE ENTERED AT HRSENT SCREEN--12/7/79---------
rem     rate zero is also OK!
dim cat.ok.to.enter%(pr1.max.ed.cats%)
cat.ok.to.enter%(01)=true%    rem REGULAR PAY
cat.ok.to.enter%(02)=true%    rem OVERTIME PAY
cat.ok.to.enter%(03)=true%    rem SPECIAL OT PAY
cat.ok.to.enter%(04)=true%    rem COMMISSION
cat.ok.to.enter%(05)=true%    rem VACATION TAKEN
cat.ok.to.enter%(06)=true%    rem SICK LVE TAKEN
cat.ok.to.enter%(07)=true%    rem COMP TIME TAKEN
cat.ok.to.enter%(08)=true%    rem COMP TIME EARND
cat.ok.to.enter%(09)=true%    rem BONUS
cat.ok.to.enter%(10)=true%    rem TIPS COLLECTED
cat.ok.to.enter%(11)=true%    rem ADVANCE
cat.ok.to.enter%(12)=true%    rem SICK PAY
cat.ok.to.enter%(13)=true%    rem VACATION PAY
cat.ok.to.enter%(14)=true%    rem OTHER EXCLD PAY
cat.ok.to.enter%(15)=true%    rem EXPENSE REIMB
cat.ok.to.enter%(16)=false%    rem EIC
cat.ok.to.enter%(17)=true%    rem OTHER PAY
cat.ok.to.enter%(18)=true%    rem TIPS REPORTED
cat.ok.to.enter%(19)=false%    rem
cat.ok.to.enter%(20)=false%    rem FWT
cat.ok.to.enter%(21)=false%    rem SWT
cat.ok.to.enter%(22)=false%    rem LWT
cat.ok.to.enter%(23)=false%    rem FICA
cat.ok.to.enter%(24)=false%    rem SDI
cat.ok.to.enter%(25)=false%    rem
cat.ok.to.enter%(26)=false%    rem
cat.ok.to.enter%(27)=true%    rem ADVANCE REPAY
cat.ok.to.enter%(28)=true%    rem FWT ADD-ON
cat.ok.to.enter%(29)=true%    rem SWT ADD-ON
cat.ok.to.enter%(30)=true%    rem LWT ADD-ON
cat.ok.to.enter%(31)=true%    rem FICA ADD-ON
cat.ok.to.enter%(32)=false%    rem
cat.ok.to.enter%(33)=false%    rem SYS1
cat.ok.to.enter%(34)=false%    rem SYS2
cat.ok.to.enter%(35)=false%    rem SYS3
cat.ok.to.enter%(36)=false%    rem SYS4
cat.ok.to.enter%(37)=false%    rem SYS5
cat.ok.to.enter%(38)=false%    rem EMP1
cat.ok.to.enter%(39)=false%    rem EMP2
cat.ok.to.enter%(40)=false%    rem EMP3
cat.ok.to.enter%(41)=false%    rem
cat.ok.to.enter%(42)=false%    rem COMPANY FICA
cat.ok.to.enter%(43)=false%    rem COMPANY FUTA
cat.ok.to.enter%(44)=false%    rem COMPANY SUI
cat.ok.to.enter%(45)=false%    rem
cat.ok.to.enter%(46)=false%    rem OTHER CO COST (future use)
cat.ok.to.enter%(47)=false%    rem
cat.ok.to.enter%(48)=false%    rem
cat.ok.to.enter%(49)=false%    rem
cat.ok.to.enter%(50)=false%    rem OTHER DED
rem----------------------------------------------------------------
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
Rem #include "fpyhrsen"
rem---------------------------------------------------------
rem    SET UP DMS SCREEN EQUATES    FPYHRSEN - 7/DEC/79

crt.field.count% = 23        rem number of screen fields
dim    crt.data$(crt.field.count%)
dim    crt.x%(crt.field.count%)
dim    crt.y%(crt.field.count%)
dim    crt.len%(crt.field.count%)
dim    crt.rd%(crt.field.count%)
dim    crt.attrib%(crt.field.count%)
rem    LEGEND:    X  Y  LEN  RD  ATTRIB
rem        STRNUM=1;BRKTSGN=2;USED=4;IO=16;BRT=8
data           \
      74,3,3,0,28,\       rem   IO fld #1
      27,9,3,0,28,\       rem   IO fld #2
      32,11,5,0,29,\       rem   IO fld #3
      40,11,30,0,29,\    rem   IO fld #4
      32,12,2,0,29,\       rem   IO fld #5
      40,12,15,0,29,\    rem   IO fld #6
      32,13,7,2,28,\       rem   IO fld #7
      32,14,8,0,29,\       rem   IO fld #8
      52,18,1,0,29,\       rem   IO fld #9
      1,1,8,0,4,\        rem   O fld #10
      1,2,9,0,4,\        rem   O fld #11
      1,3,8,0,4,\        rem   O fld #12
      10,3,8,0,4,\         rem   O fld #13
      67,3,6,0,4,\         rem   O fld #14
      12,9,59,0,4,\       rem   O fld #15
      14,10,57,0,4,\       rem   O fld #16
      14,11,57,0,4,\       rem   O fld #17
      14,12,57,0,4,\       rem   O fld #18
      14,13,57,0,4,\       rem   O fld #19
      14,14,57,0,4,\       rem   O fld #20
      14,15,57,0,4,\       rem   O fld #21
      14,16,57,0,4,\       rem   O fld #22
      28,18,26,0,4
      rem    O fld #23
crt.data$(14)="BATCH:"
crt.data$(15)="RECORD NUMBER [    ]--------------------------------------|"
crt.data$(16)="|                                                       |"
crt.data$(17)="|  EMPLOYEE NO.  [     ]                                |"
crt.data$(18)="|  RATE          [  ]                                   |"
crt.data$(19)="|  UNITS         [            ]                         |"
crt.data$(20)="|  DATE          [        ]                             |"
crt.data$(21)="|                                                       |"
crt.data$(22)="|-------------------------------------------------------|"
crt.data$(23)="DISPLAY EMPLOYEE NAMES [ ]"

i%=1
while i%<=23
  read    crt.x%(i%),crt.y%(i%),\
    crt.len%(i%),crt.rd%(i%),crt.attrib%(i%)
  i%=i%+1
wend

if len(pr1.co.name$)<=30 \
  then     co.name$=fn.spread$(pr1.co.name$,1)  \
  else     co.name$=pr1.co.name$
crt.len%(10)=len(co.name$)
crt.x%(10)=fn.center%(co.name$,crt.columns%-2)
crt.data$(10)=co.name$
if len(system.name$)<=30 \
  then     sys.name$=fn.spread$(system.name$,1)  \
  else     sys.name$=system.name$
crt.len%(11)=len(sys.name$)
crt.x%(11)=fn.center%(sys.name$,crt.columns%-2)
crt.data$(11)=sys.name$
crt.data$(12)=fn.date.out$(common.date$)
if len(function.name$)<=30 \
  then     fun.name$=fn.spread$(function.name$,1)  \
  else     fun.name$=function.name$
crt.len%(13)=len(fun.name$)
crt.x%(13)=fn.center%(fun.name$,crt.columns%-2)
crt.data$(13)=fun.name$

rem---------------------------------------------------------

dim emsg$(18)    rem can go to 25
emsg$(01) = "PY051 EMPLOYEE FILE NOT FOUND ON DRIVE "+str$(pr1.emp.drive%)
emsg$(02) = "PY052 EMPLOYEE FILE IS NULL"
emsg$(03) = "PY053 Y OR N ONLY"
emsg$(04) = "PY054 INVALID RESPONSE"
emsg$(05) = "PY055 HOURS FILE OF TYPE 000 FOUND"
emsg$(06) = "PY056 MUST BE NUMERIC INTEGER"
emsg$(07) = "PY057 NOT NUMERIC"
emsg$(08) = "PY058 EXCEEDS NUMBER OF RECORDS ON HOURS FILE: "
emsg$(09) = "PY059 INVALID CONTROL CHARACTER"
emsg$(10) = "PY060 INVALID CHECK DIGIT"
emsg$(11) = "PY061 INVALID EMPLOYEE NUMBER"
emsg$(12) = "PY062 TRANS. CODE CANNOT BE LESS THAN ZERO OR GREATER THAN "+STR$(PR1.MAX.ED.CATS%)
emsg$(13) = "PY063 INVALID DATE"
emsg$(14) = "PY064 PR2 FILE NOT FOUND ON SYSTEM DRIVE"
emsg$(15) = "PY065 INVALID TRANSACTION CODE"
emsg$(16) = "PY066 THERE ARE NO HOURS FILE RECORDS"
emsg$(17) = "PY067 TERMINATED, DELETED, OR INVALID EMPLOYEE"
emsg$(18) = "PY068 TYPE 101 HOURS FILE RENAMED TO TYPE 102"


rem----------------------------------------------------------
rem
rem    C O N S T A N T S
rem
rem----------------------------------------------------------

a$ = "&"
cat.0$ = "REG AND OT PAY"
names% = true%
null$ = ""
pw$ = null$    rem for future use
pm$ = null$
hrs.eff.date$ = common.date$

rem----------------------------------------------------------
rem
rem    S E T        U P
rem
rem----------------------------------------------------------

gosub 30    rem throw up on screen
gosub 5     rem set up file accessing
gosub 20    rem get.hrs.file
if not ok%  then goto 999.1    rem  prem. end
gosub 10    rem employee names desired?
if stopit%  then goto 999.2    rem stop requested
if not ok%  then goto 999.1
if write.pr2%  then \
    gosub 6     rem try to open pr2--set ok% to false if ng
if not ok% then goto 999.1    rem abort
if stopit% then goto 999.2    rem premature.end
gosub 50    rem get rid of unwanted screen fields
if pr1.debugging%  then \
    trash% = fn.msg%("1  fre = "+str$(fre))

rem----------------------------------------------------------
rem
rem    M A I N      D R I V E R
rem
rem----------------------------------------------------------

gosub 100    rem process.input
gosub 600    rem rewrite hrs hdr, close & rename hrs
gosub 650    rem rewrite.pr2.file.if.needed

rem----------------------------------------------------------
rem
rem    E N D      O F      J O B
rem
rem----------------------------------------------------------

trash% = fn.msg%("STOP REQUESTED")

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
rem------set-up subroutines----------
5    rem------set up file accessing-------
      emp.file.name$=fn.file.name.out$(emp.name$,"101",pr1.emp.drive%,pw$,pm$)
      pr2.file.name$=fn.file.name.out$(pr2.name$,"101",common.drive%,pw$,pm$)
    return

6    rem------see if pr2 is present-----
    if end #pr2.file%  then 6.99
    open pr2.file.name$ as pr2.file%
    pr2.exists% = true%
    return

6.99    rem------no pr2 file------
    pr2.exists% = false%
    ok% = false%
    emsg% = 14
    gosub 99    rem display msg & display
    return

10    rem------get emp file if wanted------
    gosub 15    rem want names?
    if stopit%  then return     rem premature burial
    if not names%  then  return    rem  don't open EMP
    gosub 11    rem open EMP
    if not emp.exists%  then \
        trash% = fn.emsg%(01) :\
        ok% = false%    :\
        return
    gosub 12    rem read emp hdr
    gosub 13    rem dimension tables for emp reads
    emp.emp.name$ = null$
    return

11    rem-----open employee file-----
    if end #emp.file% then 11.9
    open emp.file.name$ recl emp.len%  as emp.file%
    emp.exists% = true%
    return

11.9    rem-----can't open emp file------
    emp.exists% = false%
    emp.eof% = true%
    return

12    rem------read emp hdr-------
    if end #emp.file%  then 12.9    rem null emp file
    read #emp.file%,1; \
Rem #include "ipyemphd"
        emp.hdr.no.recs%,\      rem 10/30/79
        emp.hdr.no.del.recs%,\
        emp.hdr.next.del.rec%,\
        emp.hdr.101,\
        emp.hdr.102,\
        emp.hdr.201$
    if end #emp.file% then 12.99    rem normal eof
    return

12.9    rem-----emp end of file on hdr read-----
    emp.eof% = true%
    trash% = fn.emsg%(02)
    stopit% = true%
    return

12.99    rem-----normal emp eof-----
    emp.eof% = true%
    return

13    rem------dimension tables for emp reads------
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

    return

15    rem------want names?---------
    gosub 16    rem t/f
    if stopit%  then return     rem prem end
    if t%  then names% = true%
    if f%  then names% = false%
    trash% = fn.put%(fn.dsp.yorn$(names%),fld.name.disp%)
    return

16    rem-----enter t/f/cr/back/stopit-----------------------
    t%=false%:f%=false%:cr%=false%:stopit%=false%
    while true%
        trash% = fn.get%(2,fld.name.disp%)
        if in.status% = req.stopit%  then stopit% = true%:return
        if in.status% = req.cr%  then cr% = true%
        if in.uc$="Y" or in.uc$="T" or cr% \
            then t% = true%:return
        if in.uc$ = "N"  or in.uc$ = "F" \
            then    f%=true%:return
        emsg% = 4
        gosub 99    rem display msg & delay
    wend


20    rem------get.hrs.file--------
    trash% = fn.msg%("PLEASE WAIT...GETTING FILES")
    hrs.in$=fn.file.name.out$(hrs.name$,"000",pr1.hrs.drive%,pw$,pm$)
    hrs.out$=fn.file.name.out$(hrs.name$,"001",pr1.hrs.drive%,pw$,pm$)
    gosub 21    rem get.status.of.101
    gosub 22    rem get.status.of.001
    gosub 23    rem get.status.of.000
    gosub 23.5    rem get status of 102
    if hrs.000.exists% \
        then    emsg% = 5     :\
            gosub 99      :\  rem display msg & delay
            ok%=false%    :\
            return
    if hrs.001.exists% \
        then trash% = rename(hrs.in$,hrs.out$)
    if not hrs.001.exists% \
        then    gosub 24     rem create.000
    if hrs.101.exists% \
        then    gosub 25    rem rename 101--delete 102 if there
    gosub 26    rem open hrs file for 345th time
    gosub 27    rem  read.hdr.rec
    gosub 28    rem reset.proof.flags & write hdr
    trash% = fn.put%(str$(hrs.hdr.batch.no%),fld.batch.no%)
    ok%=true%
    trash% = fn.msg%(null$)
    return

21    rem-----get status of 101-----
    type$ = "101"
    gosub 29    rem open hrs
    if hrs.exists%    then \
        hrs.101.exists% = true% :\
        close hrs.file%
    return

22    rem-----get status of 001------
    type$ = "001"
    gosub 29    rem open
    if hrs.exists%    then \
        hrs.001.exists% = true% :\
        close hrs.file%
    return

23    rem-----get status of 000-----
    type$ = "000"
    gosub 29    rem open
    if hrs.exists%    then \
        hrs.000.exists% = true% :\
        close hrs.file%
    return
23.5    rem------get status of 102---------
    type$ = "102"
    gosub 29    rem open it
    if hrs.exists%    then \
        hrs.102.exists% = true% :\
        close hrs.file%
    return

24    rem-----create 000 file------
    if end # hrs.file%  then 29.99    rem normal eof
    create hrs.in$    recl hrs.len%  as hrs.file%
    hrs.000.exists% = true%
    hrs.hdr.batch.no% = pr2.hrs.batch.no% + 1
    hrs.hdr.no.recs% = 0
    close hrs.file%
    write.pr2%  = true%
    return

25    rem -----delete 102 hrs file, rename 101 to 102-----
    if hrs.102.exists%  then \
        type$ = "102" :\
        gosub 29      :\    rem open hrs as type 102
        delete hrs.file%    rem delete 102
      trash%=rename(fn.file.name.out$(hrs.name$,"102",pr1.hrs.drive%,pw$,pm$),\
         fn.file.name.out$(hrs.name$,"101",pr1.hrs.drive%,pw$,pm$))
    emsg% = 18
    gosub 99    rem display & delay
    return

26    rem-----open the hrs file for the last time------
    type$ = "000"
    gosub 29    rem open
    return

27    rem------read hdr rec-------
    read #hrs.file%,1; \
Rem #include "ipyhrshd"
        hrs.hdr.no.recs%,\     rem  10/30/79
        hrs.hdr.batch.no%,\
        hrs.hdr.proof.no%,\
        hrs.hdr.proofed%,\
        hrs.hdr.101

    return

28    rem------reset header flags & write hdr-------
    hrs.hdr.proof.no% = 0
    hrs.hdr.proofed% = false%
    print #hrs.file%,1; \
Rem #include "ipyhrshd"
        hrs.hdr.no.recs%,\     rem  10/30/79
        hrs.hdr.batch.no%,\
        hrs.hdr.proof.no%,\
        hrs.hdr.proofed%,\
        hrs.hdr.101

    return

29    rem-----try to open hrs-----
       hrs.file.name$=fn.file.name.out$(hrs.name$,type$,pr1.hrs.drive%,pw$,pm$)
    hrs.exists% = false%
    if end # hrs.file% then 29.9    rem no file
    open hrs.file.name$  recl hrs.len%  as hrs.file%
    if end #hrs.file%  then 29.99    rem normal eof
    hrs.exists% = true%
    return

29.9    rem-----open failed on hrs-----
    hrs.exists% = false%
    return

29.99    rem-----normal eof on hrs-------
    hrs.eof% = true%
    return

30    rem-----set up &  display screen-------
    fld.batch.no%  = 1
    fld.rec.no%    = 2
    fld.emp.no%    = 3
    fld.emp.name%  = 4
    fld.units%     = 7
    fld.rate%      = 5
    fld.desc%      = 6
    fld.date%      = 8
    fld.name.disp% = 9
    trash% = fn.put.all%(false%)    rem literals only
    trash% = fn.put%(fn.dsp.yorn$(names%),fld.name.disp%)
    return

40    rem----- fn.num --------------------------
    num% = fn.num%(in$)
    if len(in$)>digits% or not num%  then \
        num%=false%: \
        trash% = fn.emsg%(06) :RETURN
    in.num=val(in$)
    return

42    rem----- fn.numeric ----------------------
    numeric% = fn.numeric%(in$,left.digits%,right.digits%)
    if not numeric%  then trash% = fn.emsg%(07) :\
        return
    in.numeric=val(in$)
    return

50    rem-----set up dms screen fields-----
    trash% = fn.clr%(23)
    trash% = fn.clr%(fld.name.disp%)
    if not names%  then \
        trash% = fn.clr%(fld.emp.name%)
    return

99    rem-----display emsg & delay------
    trash% = fn.emsg%(emsg%)
    for i% = 1 to 250
    next i%
    return

rem------main driver subroutines--------
100    rem-----process.input------
    first.time%=true%
    write.needed%=true%
    if repeating% then goto 110
    gosub 300    rem get.record.number
    if stopit% then return
    if good.rec% and cr% then goto 120
    if not good.rec% and cr% \
        then  goto 100    rem goto process.input
    if back% then gosub 310 :\   rem get.prev.rec:
        goto 100      rem  process.input
    if next% then gosub 320 :\  rem   get.next.rec:
        goto 100      rem process.input
    if delete% and good.rec% then  gosub 330  :\    rem  delete.rec:
        good.rec% = false%    :\
        goto 100    rem process.input
    if save%   then goto 100
    if adding% then repeating%=true%

110    rem-----here if we are already repeating----------------
    if repeating% \
        then    gosub 400  :\    rem get next available
            gosub 410  :\    rem get defaults
            good.rec%=true%   :\
            gosub 450  :\    rem display record
            goto 120
    if not ok% \
        then    good.rec%=false%  :\
            goto 100    rem goto process.input
    gosub 325    rem read & display hrs
    goto 100    rem process.input

120    rem-----here if changing or adding----------------------
    gosub 200    rem get.data
    if hrs.emp.no$ = null$    then write.needed% = false%
    gosub 290    rem reset.flags
    if write.needed% \
        then    gosub 550  \    rem write.rec
        else    good.rec%=false%
    goto 100    rem process.input


rem------incoming data facilities---------
200    rem------get.data-------
    in$=hrs.emp.no$
    gosub 250    rem get.emp.no
    if stopit% and first.time%  \
        then    repeating%=false% :\
            write.needed% = false%
    first.time%=false%
    if stopit% then return
    if invalid.emp%  then \
        emsg% = 17    :\
        gosub 99        rem display & delay
    if cancel% or invalid.emp%  then write.needed%=false%:return
    if back%  then goto 230
    if cr%    then goto 210
    if not ok% \
        then    trash% = fn.put%(hrs.emp.no$,fld.emp.no%) :\
            invalid.emp% = false%    :\
            goto 200    rem get.data
    hrs.emp.no$=in$
    trash% = fn.put%(hrs.emp.no$,fld.emp.no%)
    if names%  then \
        gosub 560  :\    read emp file
        trash% = fn.put%(emp.emp.name$,fld.emp.name%)
    if invalid.emp%  then  \
        write.needed% = false% :\
        goto 200    rem if term. or deleted go no furthr


210    rem-----get rate--------------------------------------
    in$=str$(hrs.rate%)
    gosub 270    rem get.rate
    if stopit% then return
    if back% then goto 200
    if cr%    then goto 220
    if cancel% then write.needed%=false%:return
    if not ok% \
        then    trash% = fn.put%(str$(hrs.rate%),fld.rate%):\
            goto 210
    hrs.rate% = cat%
    trash% = fn.put%(str$(hrs.rate%),fld.rate%)
    trash% = fn.put%(desc$,fld.desc%)

220    rem-----get units-------------------------------------
    in$=str$(hrs.units)
    gosub 260    rem get.rate
    if stopit% then return
    if back% then goto 210
    if cr%    then goto 230
    if cancel% then write.needed%=false%:return
    if not ok% \
        then   trash% = fn.put%(str$(hrs.units),fld.units%):\
            goto 220    rem display old value & try again
    hrs.units = in.numeric
    trash% = fn.put%(str$(hrs.units),fld.units%)

230    rem-----get effective date----------------------------
    in$=fn.date.out$(hrs.eff.date$)
    gosub 280    rem fet.eff.date
    if stopit% then return
    if back% then goto 220
    if cr%    then goto 200
    if cancel% then write.needed%=false%:return
    if not ok% \
        then    trash%=fn.put%(fn.date.out$(hrs.eff.date$),fld.date%):\
            goto 230
    trash% = fn.put%(in$,fld.date%)
    hrs.eff.date$=fn.date.in$
    goto 200    rem get.data

250    rem-----get employee number-----
    field% = fld.emp.no%
    gosub 350    rem get data
    if valid%  then \
        gosub 255    rem check emp #
    return

255    rem-----edit employee number-----
    ok% = true%
    digits% = 5
    gosub 40    rem check num int.
    if not num%  then  ok%=false%:return
    if len(in$) <> 5  then \
        ok% = false% :\
        emsg% = 10   :\
        gosub 99     :\ rem display & delay
        return
    emp$ = left$(in$,4)
    if right$(in$,1) <> fn.ck.dig$(emp$)  then \
        ok% = false% :\
        emsg% = 10   :\
        gosub 99     :\ rem display & delay
        return
    emp.rec% = val(emp$)
    if emp.rec% > pr2.no.employees%  or   \
       emp.rec% < 1      then \
        ok% = false% :\
        emsg% = 11   :\
        gosub 99     :\ rem display & delAy
        return
    write.needed% = true%
    invalid.emp% = false%
    return

260    rem-----get units------
    field% = fld.units%
    gosub 350    rem get data
    if valid% then \
        gosub 265    rem check units
    return

265    rem-----edit units-------
    ok% = true%
    left.digits% = 5
    right.digits% = 2
    gosub 42    rem check numeric
    if not numeric%  then ok% = false%
    return

270    rem-----get rate-------
    field% = fld.rate%
    gosub 350    rem get data
    if valid%  then \
        gosub 275    rem check rate
    return

275    rem-----edit rate-----
    ok% = true%
    digits% = 2
    gosub 40    rem check num int.
    if not num%  then ok% = false%:return
    cat% = val(in$)
    if cat% = 0  then \
        desc$ = cat.0$ :\
        return        rem jump around range check
    if cat% > 0  and cat% < 5  then \
        desc$ = pr1.rate.name$(cat%)  :\
        return
    if cat% > pr1.max.ed.cats%  or \
       cat% < 0  then \
        ok% = false%  :\
        trash% = fn.emsg%(12) :\
        return
    if not cat.ok.to.enter%(cat%)  then \
        ok% = false%  :\
        trash% = fn.emsg%(15)
    desc$ = ed.desc.table$(cat%)
    return

280    rem-----get eff. date-----
    field% = fld.date%
    gosub 350    rem get data
    if valid%  then \
        gosub 285    rem check date
    return

285    rem-----edit eff. date------
    ok% = true%
    if not fn.edit.date%(in$)  then \
        ok% = false% :\
        trash% = fn.emsg%(13)
    return

290    rem-----reset flags-------
    valid%     = false%
    stopit%  = false%
    cr%     = false%
    back%     = false%
    next%     = false%
    cancel%  = false%
    save%     = false%
    delete%  = false%
    return

rem-----record number facilities-------------
300    rem-----get record number-------
    field% = fld.rec.no%
    gosub 340    rem get data
    if valid%  then \
        adding% = false%  :\    rem turn off add if rec no used
        gosub 305 \    rem validate rec no
       else \
        gosub 360    rem stopit or save msg
    return

305    rem-----edit record number------
    ok% = true%
    digits% = 4
    in$ = str$(val(in$))
    gosub 40    rem num int?
    if not num%  then good.rec% = false%:return
    if val(in$) > hrs.hdr.no.recs%    then \
        trash% = fn.msg%(bell$+emsg$(08)+ \
           str$(hrs.hdr.no.recs%)+" IS MAX") :\
        ok% = false% :\
        trash% = fn.put%(null$,fld.rec.no%)  :\
        return
    hrs.rec% = val(in$)
    return

310    rem-----get previous record-----
    if hrs.hdr.no.recs% < 1  then \
        gosub 321  :\    rem no records
        return
    hrs.rec% = hrs.rec% - 1
    if hrs.rec% < 1  then \
        hrs.rec% = hrs.hdr.no.recs%
    gosub 325    rem read hrs file & display
    return

320    rem-----get next record-------
    if hrs.hdr.no.recs% < 1  then \
        gosub 321 :\    rem no records
        return
    hrs.rec% = hrs.rec% + 1
    if hrs.rec% > hrs.hdr.no.recs%    then \
        hrs.rec% = 1
    gosub 325    rem read hrs file & display
    return

321    rem-----no hrs recs-----
    emsg% = 16
    gosub 99    rem display msg & delay
    ok% = false%
    good.rec% = false%
    return

325    rem-----read & display hrs rec-----
    good.rec% = true%
    gosub 500    rem read hrs.file
    if hrs.deleted%  then \
        emp.emp.name$ = "DELETED RECORD" :\
        desc$ = "DELETED"  :\
        good.rec% = false%
    gosub 450    rem dispplay rec
    return

330    rem-----delete an hrs record------
    hrs.deleted% = true%
    adding% = false%
    gosub 550    rem write rec
    hrs.deleted% = false%
    trash% = fn.msg%("RECORD NUMBER "+str$(hrs.rec%)+" DELETED")
    return

340    rem-----get rec.no data-------
    gosub 290    rem reset flags
    trash% = fn.get%(5,field%)    rem accept any ctl-char but cancel
    gosub 341    rem check valid,stopit,cr,back
    if in.status% = req.next%  then next% = true%:return
    if in.status% = req.save%  then save% = true%:return
    if in.status% = req.adding%  then adding% = true%:return
    if in.status% = req.delete%  then delete% = true%:return
    return

341    rem-----check valid,stopit,back,cr-------
    if in.status% = req.valid%  then valid% = true%:return
    if in.status% = req.stopit%  then stopit% = true%:return
    if in.status% = req.cr%  then cr% = true%:return
    if in.status% = req.back%  then back% = true%
    return

350    rem-----get other data-----
    gosub 290    rem reset flags
    trash% = fn.get%(3,field%)    rem accepts valid,stopit,cr,back,cancel
    gosub 341    rem check valid,stopit,cr,back
    if in.status% = req.cancel%  then cancel% = true%
    return

360    rem-----check ctl chars (rec no)-----
    if stopit%  then \
        trash% = fn.msg%("STOP REQUESTED") :\
        return
    if save%  then \
        gosub 420  :\    rem save files
        return
    return

rem-----hrs file handling-------
400    rem-----get spot for new rec-----
    hrs.rec% = hrs.hdr.no.recs% + 1
    return

410    rem-----get default values------
    hrs.units   = 0.0
    hrs.rate%   = 0
    desc$        = cat.0$
    return

420    rem-----save hrs file=====
    gosub 555    rem write hrs hdr
    close hrs.file%
    gosub 26    rem re-open hrs file
    trash% = fn.msg%(str$(hrs.hdr.no.recs%)+" RECORDS SAVED")
    return

450    rem-----display data------
    trash% = fn.put%(str$(hrs.rec%),fld.rec.no%)
    trash% = fn.put%(hrs.emp.no$,fld.emp.no%)
    if names%  then \
        trash% = fn.put%(emp.emp.name$,fld.emp.name%)
    trash% = fn.put%(str$(hrs.rate%),fld.rate%)
    trash% = fn.put%(desc$,fld.desc%)
    trash% = fn.put%(str$(hrs.units),fld.units%)
    trash% = fn.put%(fn.date.out$(hrs.eff.date$),fld.date%)
    return


rem------reads & writes---------
500    rem-----read an hrs rec------
    if pr1.debugging%  then \
        trash% = fn.msg%("500  fre = "+str$(fre))
    read #hrs.file%,hrs.rec%+1; \
Rem #include "ipyhrs"
        hrs.emp.no$,\           rem 12-oct-79
        hrs.eff.date$,\
        hrs.rate%,\
        hrs.units,\
        hrs.deleted%
    if hrs.deleted%  then \
        trash%=fn.msg%("RECORD "+str$(hrs.rec%)+" HAS BEEN DELETED."):\
        good.rec% = false% :\
        return
    gosub 501    rem get name & desc
    return

501    rem-----get name & desc-------
    emp.emp.name$ = null$
    if hrs.rate% = 0  then \
        desc$ = cat.0$
    if hrs.rate% > 0  and hrs.rate% < 5  then \
        desc$ = pr1.rate.name$(hrs.rate%)
    if hrs.rate% >= 5  then \
        desc$ = ed.desc.table$(hrs.rate%)
    if names%  then gosub 560    rem  read emp file
    return

550    rem-----write an hrs rec------
    print #hrs.file%,hrs.rec%+1; \
Rem #include "ipyhrs"
        hrs.emp.no$,\           rem 12-oct-79
        hrs.eff.date$,\
        hrs.rate%,\
        hrs.units,\
        hrs.deleted%

    if adding%  then\
        hrs.hdr.no.recs% = hrs.hdr.no.recs% + 1
    return

555    rem-----write hrs hdr-----
    print #hrs.file%,1; \
Rem #include "ipyhrshd"
        hrs.hdr.no.recs%,\     rem  10/30/79
        hrs.hdr.batch.no%,\
        hrs.hdr.proof.no%,\
        hrs.hdr.proofed%,\
        hrs.hdr.101
    return

560    rem-----read emp file-------
    if pr1.debugging%  then \
        trash% = fn.msg%("560  fre = "+str$(fre))
    emp.rec% = val(left$(hrs.emp.no$,4))
    invalid.emp% = false%
    read #emp.file%, emp.rec%+1; \
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


    if emp.status$ = "T"  then \
        emp.emp.name$ = "TERMINATED EMPLOYEE" :\
        invalid.emp% = true%
    if emp.status$ = "D"  then \
        emp.emp.name$ = "DELETED EMPLOYEE"  :\
        invalid.emp% = true%
    if emp.status$ = "L"  then \
        emp.emp.name$ = "EMPLOYEE ON LEAVE"
    emp.emp.name$ = fn.name.flip$(emp.emp.name$)
    return

rem------eoj routines-------
600    rem-----rename hrs file------
    gosub 555    rem write hrs hdr
    close hrs.file%
    trash% = rename(hrs.out$,hrs.in$)
    return

650    rem-----rewrite pr2-----
    if not write.pr2%  then return
    pr2.hrs.batch.no% = hrs.hdr.batch.no%
    print #pr2.file%; \
Rem #include "ipypr2"
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
end
