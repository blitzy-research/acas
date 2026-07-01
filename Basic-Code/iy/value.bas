%include iiycomm
prgname$="VALUE  18 OCTOBER, 1979 "
rem---------------------------------------------------------
rem
rem	  S T O C K  C O N T R O L
rem
rem	  V  A	L  U  E
rem
rem   COPYRIGHT (C) 1980-2009, Applewood Computers.
rem
rem---------------------------------------------------------

program$="VALUE"

%include iiyinit
dim emsg$(10)
emsg$(01)="IY501 INVALID PART NUMBER"
emsg$(02)="IY502 STARTING PART NUMBER GREATER THAN ENDING PART NUMBER"
emsg$(03)="IY503 PART FILE MOUNTED ON WRONG DRIVE"
emsg$(04)="IY504 UNEXPECTED END OF FILE ON PART FILE"
emsg$(05)="IY505 "
emsg$(06)="IY506 INVALID RESPONSE"
emsg$(07)="IY507"
emsg$(08)="IY508"
emsg$(09)="IY509"
emsg$(10)="IY510"

%include zstring
%include zinput
%include zdateio
%include zheading
%include zabort

rem june 18, 1979
dim sorted.part.records%(pr2.part.files%)
dim high.part.number$(pr2.part.files%)
dim deleted.recs%(pr2.part.files%)
dim last.update$(pr2.part.files%)

dim array$(pr1.array.size%,pr2.part.files%)
dim part.file%(3)
part.file%(1) = 3
part.file%(2) = 4
part.file%(3) = 5
%include iiyprt80

for file.ptr% = 1 to pr2.part.files%
        file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$+"101"

rem----- open file --------------------------

        if end #part.file%(file.ptr%)  then 2.59        rem end of file
        open file.name$ \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%

        open.files%=open.files%+1
        read    #part.file%(file.ptr%);\
%include iiyprt90

        if prt.drive$ <> pr2.part.drive$(file.ptr%)  then \
                print tab(5);bell$;emsg$(03):\
                common.msg$=emsg$(03)   :\
                goto 999.1              rem abend

        high.part.number$(file.ptr%)=prt.high.prt.no$
        deleted.recs%(file.ptr%)=prt.deleted.recs%
        last.update$(file.ptr%)=prt.last.update$
        sorted.part.records%(file.ptr%)=prt.no.recs%
next

goto  2.6               rem initialize crt

2.59 rem----- unexpected end of file ----------------------
print tab(5);bell$;emsg$(04)
common.msg$ = emsg$(04)
goto 999.1      rem abend

2.6 rem----- end of include ----------------------

lines% = 90
num$ = "###,### "
dol$ = "###,###.## "
t.dol$ = "##,"+dol$
gt.dol$ = "#,#"+t.dol$
form1$ = "&&& "+dol$+dol$+num$+t.dol$+dol$
form2$ = "&&& "+dol$+dol$+num$+num$+t.dol$+dol$
under$ = "----------------"
dunder$ = "================"
no.parts.msg$ = "THERE WERE NO ITEM NUMBERS WITHIN THE SPECIFIED RANGE"

gosub 50        rem get range of part numbers
if stopit%  then goto 999.2     rem premature burial

lprinter
rem----------------------------------
rem--------main program driver------------
more.parts% = true%
gosub 100       rem get first part
while more.parts%
        gosub 200       rem calculate average & accum.
        gosub 300       rem print line
        gosub 1200      rem get next part
wend

rem-------------------------------------------
rem-----------eoj--------------------------
gosub 400       rem print totals
if partial%  then gosub 450     rem print partial msg
print           rem coddle centronics
console
gosub 500       rem close part file(s)
%include zeoj

rem--------subroutine section---------------
30      rem-----validate part no-----
%include iiyprtno
        return

50      rem-----get range of part no's------
        partial% = false%
        desc$ = "STARTING"
        gosub 55        rem get #
        if stopit%  then return
        if invalid%  then goto 50
        start$ = new.part$
        start.len% = len%
        desc$ = "ENDING"
51      gosub 55        rem get #
        if stopit%  then return
        if back%  then goto 50
        if invalid%  then goto 51
        end$ = new.part$
        end.len% = len%
        if start$ = null$ or end$ = null$  then return
        if start$ > end$  then \
                print tab(5); bell$; emsg$(2) :\
                goto 50
        if end$ > high.part.number$(pr2.part.files%)  then \
                end$ = high.part.number$(pr2.part.files%)
        return

55      rem------get #-------
        invalid% = true%
        while invalid%
                if fn.input%(desc$+" ITEM NUMBER",10)  then \
                        gosub 60        rem look for cr, stop
                print
                if cr%  then \
                        new.part$ = null$ :\
                        len% = 0  :\
                        invalid% = false% :\
                        return
                gosub 30        rem validate part no
                if not part.invalid%  then \
                        partial% = true% :\
                        invalid% = false% :\
                        return
                print tab(5); bell$; emsg$(1)
        wend
        return

60      rem-----look for cr, stop------
        if stopit%  then goto 999.2     rem premature end
        if cr%  then return
        if back% and desc$ = "ENDING"  then return
        back% = false%
        invalid% = true%
        print tab(5); bell$; emsg$(6)
        return

100     rem-----get 1st part no------
        if start$ = null$  then \
                file.ptr% = 1 :\
                part.rec% = 1 :\
                gosub 1200    \ rem read next
           else \
                gosub 1000      rem read using part no
        startup$ = prt.number$
        return

200     rem-----calculate average & accum------
        if prt.stock <= 0.0  then \
                stock = 1 \
           else \
                stock = prt.stock
        if pr1.manu.used%  then \
                wip = prt.wip \
           else \
                wip = 0.0
        average = prt.value/(stock+prt.wip)
        stock.val = prt.cost*stock
        wip.val   = prt.cost*prt.wip
        tot.val   = tot.val + prt.value
rem following variables not used at this time
        tot.stock.val = tot.stock.val + stock.val
        tot.wip.val   = tot.wip.val + wip.val
        tot.tot.val   = tot.tot.val + tot.val
        return

300     rem-----print line-----
        if fn.abort%  then goto 999.2   rem prem end
        if lines% > pr1.lines.per.page%  then \
                gosub 310       rem do hdr
        if pr1.manu.used%  then \
                gosub 350  :\ rem do manu line
                return
        print using form1$; tab(7); part.key$; tab(18); prt.number$; tab(33); \
             prt.desc$; tab(68); average; tab(81); prt.cost; tab(95); \
             prt.stock; tab(104); prt.value; tab(119); prt.retail
        lines% = lines% + 1
        return

310     rem------do hdr------
        lines% = fn.hdr%(fn.spread$("VALUATION REPORT",1)) + 8
        print:print
        if pr1.manu.used%  then \
                gosub 360 :\ rem do manu hdr
                return
        print tab(7); "RECORD"; tab(21); "ITEM"; tab(72); "AVERAGE"; tab(82); \
           "REPLACEMENT";tab(96);"STOCKROOM"; tab(109); "VALUE IN"; tab(124);\
           "RETAIL"
        print tab(7); "NUMBER"; tab(20); "NUMBER"; tab(33); "DESCRIPTION"; \
           tab(74); "COST"; tab(85); "COST"; tab(96); "QUANTITY"; tab(109);\
           "STOCKROOM"; tab(124); "PRICE"
        print
        return

350     rem-----print manu line-----
        print using form2$; tab(2); part.key$; tab(11); prt.number$; tab(24);\
           prt.desc$; tab(54); average; tab(66); prt.cost; tab(81); prt.stock;\
           tab(92); prt.wip; tab(102); prt.value; tab(117); prt.retail
        lines% = lines% + 1
        return

360     rem-----print manu hdr-----
        print tab(2); "RECORD"; tab(14); "ITEM"; tab(58); "AVERAGE"; tab(67);\
           "REPLACEMENT"; tab(80); "STOCKROOM"; tab(94); "QUANTITY"; tab(109);\
           "TOTAL"; tab(121); "RETAIL"
        print tab(2); "NUMBER"; tab(13); "NUMBER"; tab(24); "DESCRIPTION"; \
           tab(60); "COST"; tab(70); "COST"; tab(80); "QUANTITY"; tab(94); \
           "IN WIP"; tab(109); "VALUE"; tab(121); "PRICE"
        print
        return

400     rem-----print total line-----
        if lines% = 90	then \
                console :\  rem don't print total line if no recs printed
                print tab(10); no.parts.msg$ :\
                common.msg$ = no.parts.msg$  :\
                partial% = false%   :\
                rETURN
        if pr1.manu.used%  then \
                gosub 410  :\  rem do manu total
                return
        print
        print tab(102); under$
        print using "&"+gt.dol$;tab(87);"TOTAL VALUE:";tab(102); tot.val
        print tab(102); dunder$
        print
        return

410     rem-----print manu total line -------
        print
        print  tab(100); under$
        print using "&"+gt.dol$; tab(85); "TOTAL VALUE:"; \
            tab(100); tot.val
        print tab(100); dunder$
        return

450     rem-----print partial msg-----
        if start$ = null$  then start$ = startup$
        if end$ = null$  then end$ = prt.number$
        print
        print tab(20); "THIS IS A PARTIAL LISTING COVERING ITEM NUMBER "; \
                start$; " THROUGH ITEM NUMBER "; end$
        print
        return

500     rem-----close part files------
        for file.ptr% = 1 to pr2.part.files%
                close part.file%(file.ptr%)
        next file.ptr%
        return

1000    rem----- part lookup -------------------------
        part.rec% = 2
        if pr2.part.files% = 1  or start$ < pr2.lo.number$(2)  then \
                file.ptr% = 1 :\
                goto 1001
        if pr2.part.files% = 2  or start$ < pr2.lo.number$(3)  then \
                file.ptr% = 2 else file.ptr% = 3
1001
        while left$(start$,start.len%) > left$(prt.number$,start.len%)
                gosub 1200              rem read a record
        wend                            rem do seq. until start found
        if prt.deleted%  then \
                gosub 1200      rem  get next rec
        record.read% = true%
        part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
        return


1200    rem----- get next record ------------------------
        if part.rec%=0  then part.rec% = 1
        old.file.ptr%=file.ptr%
        old.rec%=part.rec%
        part.rec% = part.rec% + 1
        while part.rec% > sorted.part.records%(file.ptr%)+1
                if file.ptr% = pr2.part.files%  then\
                        more.parts% = false% :\
                        part.rec% = old.rec%: file.ptr%=old.file.ptr%:return
                part.rec% = 2:file.ptr% =file.ptr% + 1
        wend

        gosub 1400      rem read part file
        if prt.deleted%  then 1200      rem skip deleted rec
        if end$ <> null$  and \
          (left$(end$,end.len%) < left$(prt.number$,end.len%))  then \
                more.parts% = false% :\
                return

        record.read% = true%
        part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
        return

1400    rem-----read part file-----
        read #part.file%(file.ptr%),part.rec%;\
%include iiyprt00
        return

end

