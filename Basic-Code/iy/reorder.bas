%include iiycomm
prgname$="REORDER  OCT. 19,1979 "
rem---------------------------------------------------------
rem
rem       S T O C K  C O N T R O L
rem
rem       R  E	O  R  D  E  R
rem
rem   COPYRIGHT (C) 1980-2009, Applewood Computers.
rem
rem---------------------------------------------------------

program$="REORDER"

%include iiyinit
%include znumber
%include zinput
%include zdateio
%include zstring
%include zheading
%include zabort

dim emsg$(20)
emsg$(01)="IY441  PART FILE MOUNTED ON WRONG DRIVE"
emsg$(02)="IY442  UNEXPECTED EOF ON PART FILE"
emsg$(03)="IY443  THAT'S NOT A VALID RESPONSE"
emsg$(04)="IY444  INVALID PART NUMBER"
emsg$(05)="IY445"
emsg$(06)="IY446"
emsg$(07)="IY447"
emsg$(08)="IY448"
emsg$(09)="IY449"
emsg$(10)="IY450"
emsg$(11)="IY451"
emsg$(12)="IY452"
emsg$(13)="IY453"
emsg$(14)="IY454"
emsg$(15)="IY455"
emsg$(16)="IY456"
emsg$(17)="IY457"
emsg$(18)="IY458"
emsg$(19)="IY459"
emsg$(20)="IY460"

qty.out$="###,###"
low$=null$
high$="zzzzzzzzzz"
low.heading$="UNDERSTOCKED ITEMS"
zero.heading$="ITEMS NOT IN STOCK"
reorder.heading$="ITEMS ON ORDER"

line.count%=1000
err%=false%

10 rem------ get user options -----------------------
low.wanted%=false%
zero.wanted%=false%
reorder.info.wanted%=false%
all.wanted%=false%

print:print
if err%  then \
        print using "&";crt.clear$: \
        print tab(5);bell$;emsg$(03)\
         else print
err%=false%

print:print
print tab(25);"REORDER REPORT OPTIONS"
print
print tab(20);"1  ALL ITEMS"
print tab(20);"2  A RANGE OF ITEMS"
print tab(20);"3  ITEMS THAT ARE UNDERSTOCKED"
print tab(20);"4  A RANGE OF UNDERSTOCKED ITEMS"
print tab(20);"5  ITEMS THAT ARE NOT IN STOCK"
print tab(20);"6  A RANGE OF ITEMS THAT ARE NOT IN STOCK"
print tab(20);"7  ITEMS ON ORDER"
print tab(20);"8  A RANGE OF ITEMS ON ORDER"
print

print tab(20);"ENTER A SELECTION NUMBER >";
input ""; line in$
if in$<>null$  then \
        in$=ucase$(in$)

if in$=stop$ or in$=escape$  then  999.2        rem operator requested exit

num%=fn.num%(in$)
selection%=val(in$)
if not num%  or selection%<1  or selection%>8  then \
        err%=true%:  goto 10            rem display report options

if selection% = 1 or selection% = 2  then \
        all.wanted%=true%
if selection% = 3 or selection% = 4  then \
        low.wanted%=true%
if selection% = 5 or selection% = 6  then \
        zero.wanted%=true%
if selection% = 7  or  selection% = 8  then \
        reorder.info.wanted%=true%

if selection% = 1 or selection% = 3 or selection% = 5 or selection% = 7 then \
                        low.part$=null$: high.part$="zzzzzzzzzz": \
                        goto 15         rem open part files

12 rem----- part number to start --------------------------
print
x%=fn.input%("ITEM NUMBER TO START", 256)
if stopit%  then   999.2                rem operator requested exit
if back%  then 10                       rem report options
if cr%  then  low.part$=null$
if not x%  then \
        gosub 90: low.part$=new.part$           rem part number
if invalid% or part.invalid%  then \
        print: print tab(5);bell$;emsg$(04): goto 12   rem part number to start

13 rem----- part number to stop ---------------------------
print
x%=fn.input%("ITEM NUMBER TO STOP", 256)
if cr%  then high.part$="zzzzzzzzzz"
if stopit%  then 999.2
if back%  then 12                       rem part to start
if not x%  then \
        gosub 90: high.part$=new.part$          rem part number
if invalid% or part.invalid% or high.part$<low.part$  then \
        print: print tab(5);bell$;emsg$(04): goto 13    rem part number to stop

15 rem----- open item files ------------------------------

%include iiyprt12

if abort%  then 990             rem close files

if low.part$ = low$ \
        then  low.print$= "THE FIRST ITEM" \
        else  low.print$= low.part$
if high.part$ = high$ \
        then  high.print$= "THE LAST ITEM" \
        else  high.print$= high.part$
if low.part$ > low$  or  high.part$ < high$  then \
        range$="ITEMS FROM "+low.print$+" THROUGH "+high.print$

file.ptr%=1
part.rec%=2
while prt.number$<low.part$  and file.ptr% <= open.files%
        record.align.needed%=true%
        if part.rec% > part.records%(file.ptr%)+1 \
                then file.ptr%=file.ptr%+1: part.rec%=2 \
                else gosub 1000:        \read a part record
                        part.rec%=part.rec%+1
wend
if record.align.needed%  then \
        part.rec%=part.rec%-1

rem----- main loop ------------------------------------
while file.ptr% <= open.files%  and not limit.reached%
        while part.rec% <= part.records%(file.ptr%)+1
                gosub 1000              rem read
                if prt.number$ > high.part$  then \
                        limit.reached%=true%: goto 990  rem end of job
                if prt.deleted%  then  20       rem next record
                if all.wanted%  then \
                        gosub 50: \print a line
                        goto  20                rem next record
                if prt.stock = 0 and zero.wanted%  then \
                        gosub 50: \print a line
                        goto 20                 rem next record
                if prt.stock < prt.reord.pt  and low.wanted%  then \
                        gosub 50: \print a line
                        goto 20                 rem next record
                if (prt.on.order<>0 or prt.bk.order<>0 or prt.order.date$> \
                        "000000" or prt.order.due$>"000000") and \
                        reorder.info.wanted%  then \
                                gosub 50        rem print a line
20 rem----- next record---------------------------------
                if stopit%  then 990    rem end of job
                part.rec%=part.rec%+1
        wend
        file.ptr%=file.ptr%+1
        part.rec%=2
wend

990 rem------ end of job -------------------------------
file.ptr%=1
while file.ptr% <= open.files%
        close part.file%(file.ptr%)
        file.ptr%=file.ptr%+1
wend
if any.print%  then print       rem centronix hiccup
if stopit%  then 999.2          rem premature end
if abort%  then 999.1           rem error exit

%include zeoj

50 rem----- print a item record ------------------------
x%=fn.abort%
if x%  then stopit%=true%: \
            return
any.print%=true%                rem flag for centronix hiccup
lprinter
line.count%=line.count%+1
if pr1.manu.used%  then line.count%=line.count%+1

if line.count% > pr1.lines.per.page%  then \
        gosub  55               rem print heading

part.key$= pr2.part.drive$(file.ptr%) + ":"
flag$=null$
if prt.stock < prt.reord.pt  then \
        flag$="U"
if prt.stock = 0  then \
        flag$="O"
print tab(8);flag$; \
        tab(12); part.key$; \
        tab(14); prt.number$; \
        tab(25); prt.desc$;
print using qty.out$;   tab(56); prt.stock; \
                        tab(64); prt.reord.pt; \
                        tab(72); prt.std.reord;
print   tab(82); prt.vendor$;
print using "##,###.##"; tab(87); prt.cost;
print using qty.out$;   tab(97); prt.on.order;
if prt.order.date$ > "000000"  then \
        print   tab(105); fn.date.out$(prt.order.date$);
if prt.order.due$ > "000000"  then \
        print   tab(114); fn.date.out$(prt.order.due$);
print using qty.out$;   tab(123); prt.bk.order;
if pr1.manu.used% \
        then print using "QUANTITY IN WORK IN PROGRESS "+qty.out$; \
                tab(27); prt.wip
console
return

55 rem----- heading ------------------------------
line.count%=fn.hdr%(fn.spread$("REORDER REPORT", 1)) + 3
if low.part$ > low$  or  high.part$ < high$  then \
        line.count%=line.count%+1: \
        print tab(fn.center%(range$, pr1.page.width%));range$
if low.wanted%  then \
        line.count%=line.count%+1: \
        print tab(fn.center%(low.heading$, pr1.page.width%));low.heading$
if zero.wanted%  then \
        line.count%=line.count%+1: \
        print tab(fn.center%(zero.heading$, pr1.page.width%));zero.heading$
if reorder.info.wanted%  then \
        line.count%=line.count%+1: \
        print tab(fn.center%(reorder.heading$, pr1.page.width%)); \
                reorder.heading$
print
print "     STOCK     ITEM         D E S C R I P T I O N         ";
print "ON   REORDER   STD   SUPPLIER    UNIT     ON    DATE     ";
print "DATE     BACK"

print "     FLAG     NUMBER";
print tab(56);
print "   HAND   POINT  REORDER   NO.      COST   ORDER  ";
print "ORDERED   DUE     ORDERED"
print
line.count%=line.count%+4
return

90 rem----- check a part number ------------------
%include iiyprtno
return

1000 rem----- read a record -------------------------
read #part.file%(file.ptr%), part.rec%; \
%include iiyprt00

return

