%include iiycomm
prgname$="PARTPRNT 17 FEBRUARY,1982 "
rem---------------------------------------------------------
rem
rem       S T O C K  C O N T R O L
rem
rem       P  A  R  T  P  R  N  T
rem
rem   COPYRIGHT (C) 1980-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="PARTPRNT"

%include iiyinit

dim emsg$(20)
emsg$(01)="IY461 PART FILE FOUND FROM PREVIOUS ABORTED RUN"
emsg$(02)="IY462 PART FILE NOT FOUND"
emsg$(03)="IY463 PART FILE MOUNTED ON WRONG DRIVE"
emsg$(04)="IY464 UNEXPECTED END OF FILE ON PART FILE"
emsg$(05)="IY465 PART FILE RENAME FAILED"
emsg$(06)="IY466 DUPLICATE PART NUMBER FOUND ON DRIVE "
emsg$(07)="      RUN PARTENT TO DELETE"
emsg$(08)="IY468 PR2 FILE NOT FOUND"
emsg$(09)="IY469 INVALID RESPONSE"
emsg$(10)="IY470 INVALID PART NUMBER"
emsg$(11)="IY471 TYPE 111 PART FILE FOUND WHEN TYPE  101 PRESENT"
emsg$(12)="IY472"
emsg$(13)="IY473"
emsg$(14)="IY474"
emsg$(15)="IY475"
emsg$(16)="IY476"
emsg$(17)="IY477"
emsg$(18)="IY478"
emsg$(19)="IY479"
emsg$(20)="IY480"

pr2.file% = 2
pr2.name$ = common.drive$+":IYPR2.101"
if size(pr2.name$) = 0	then \
        print tab(5); bell$; emsg$(8) :\
        common.msg$ = emsg$(8)  :\
        goto 999.1

%include zabort
%include zstring
%include zinput
%include zdatei/o
%include zheading

rem next 3 lines changed for uk version
dol$ = "#####.## "
no$ = "###### "
form1$ = "& & & & & "+dol$+"#"+dol$+"####.## "+no$+no$+no$+"& & "+no$+"##### "
const$ = "UNDER CONSTRUCTION: "
wip$ = "IN WIP: "
Rem not used in UK version >descr$ = "DESCRIPTION: "
lines% = 90

rem--------open part files-----------
file.111% = false%
dim dup%(pr2.part.files%)
dim type$(pr2.part.files%)
dim part.exists%(3)
part.dim% = true%

dim part.records%(pr2.part.files%)
dim sorted.part.records%(pr2.part.files%)
dim sorted.record.add.count%(pr2.part.files%)
dim file.sorted%(pr2.part.files%)
dim high.part.number$(pr2.part.files%)
dim deleted.recs%(pr2.part.files%)
dim last.update$(pr2.part.files%)

dim array$(pr1.array.size%,pr2.part.files%)
dim array.used%(pr1.array.size%)
dim part.file%(3)
part.file%(1) = 3
part.file%(2) = 4
part.file%(3) = 5
%include iiyprt80

for file.ptr% = 1 to pr2.part.files%
        file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$

        if end #part.file%(file.ptr%)  then 2           rem rename sorted file
        open file.name$+"100"  \                this checks for a crashed file
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        print   tab(5);bell$;emsg$(01)
        common.msg$ = emsg$(01)
        goto    999.1                           rem error exit

2 rem-don't rename sorted file ------------
        part.111%=false%:part.101%=false%:part.001%=false%
        if size(file.name$+"001") <> 0  then \
                part.001% = true%
        if size(file.name$+"101") <> 0  then \
                part.101% = true%
        if size(file.name$+"111") <> 0  then \
                part.111%  = true% :\
                file.111% = true%

        if end #part.file%(file.ptr%)  then 2.2         rem ren unsorted file
        open file.name$+"000"   \               this checks for a crashed file
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%              \
                recs    sector.len%
        print tab(5);bell$;emsg$(01)
        common.msg$ = emsg$(01)
        goto    999.1                           rem error exit

2.2 rem-don't rename unsorted file ------------
        if part.111% and part.101%  then \
                print tab(5); bell$; emsg$(11) :\
                common.msg$ = emsg$(11) :\
                goto 999.1      rem abend
        if part.111%  then \
                file.sorted%(file.ptr%) = true% :\
                type$(file.ptr%) = "111" :\
                goto 2.5
        if part.101%  then \
                file.sorted%(file.ptr%) = true% :\
                type$(file.ptr%) = "101" :\
                goto 2.5
        if part.001%  then \
                file.sorted%(file.ptr%) = false% :\
                type$(file.ptr%) = "001" :\
                goto 2.5
        print tab(5); bell$; emsg$(02)
        common.msg$ = emsg$(02)
        goto 999.1      rem abend...no part files

2.5 rem----- open file --------------------------

        if end #part.file%(file.ptr%)  then 2.59        rem unexpected eof
        open file.name$+type$(file.ptr%) \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%

        part.exists%(file.ptr%) = true%
        read    #part.file%(file.ptr%);\
%include iiyprt90

        if prt.drive$ <> pr2.part.drive$(file.ptr%)  then \
                print tab(5);bell$;emsg$(03):\
                common.msg$=emsg$(03)   :\
                goto 999.1                              rem error exit

        high.part.number$(file.ptr%)=prt.high.prt.no$
        deleted.recs%(file.ptr%)=prt.deleted.recs%
        last.update$(file.ptr%)=prt.last.update$
        part.records%(file.ptr%)=prt.no.recs%
        if file.sorted%(file.ptr%)  \
                then  sorted.part.records%(file.ptr%) = prt.no.recs%    \
                else  sorted.part.records%(file.ptr%) = 0
next

goto  2.6               rem initialize crt

2.59 rem----- unexpected end of file ----------------------
print tab(5);bell$;emsg$(04)
common.msg$ = emsg$(04)
goto 999.1                      rem error exit

2.6 rem----- crt initialise ----------------------

print% = true%
if file.111%  then \
        gosub 10        rem suppress print request
if print% and not file.111%  then \
        gosub 50        rem get range of part no's
if stopit%  then \
        gosub 9  :\     rem close any open files
        goto 999.2      rem premature burial

rem-------------main driver-----------------------
lprinter
part.rec% = 1
file.ptr% = 1
more.parts% = true%
gosub 90        rem 1st get part
while more.parts%
        gosub 200       rem check for duplicates
        gosub 300       rem print line
        gosub 100       rem get part rec
wend
rem---------end of driver---------------------------

rem--------------eoj-----------------------------
gosub 390       rem print message if no parts in range
gosub 400       rem close files & rename
print           rem coddle centronics
console

999    rem-----normal end of job---------------
print:print:print
print tab(10);program$+" COMPLETED"
print:print:print
common.return.code%=0
goto 999.3
999.1  rem-----abnormal end of job-------------
print:print:print
print tab(10);program$+" COMPLETED UNSUCCESSFULLY"
print tab(10);system.name$ + " TERMINATING"
common.return.code%=1
print:print:print:print bell$
goto 999.3
999.2  rem-----premature end of job------------
print:print:print
print tab(10);program$+" ENDING PREMATURELY"
print:print:print
common.return.code%=2
999.3  rem-----return to menu or stop----------
if chained.from.root% \
        then    chain system$ \
        else    stop

rem----------subroutines section------------------
%include iiyprt70       rem close files on abend

10      rem-----suppress print------
        print:print
        while true%
                print
                print tab(10); "DO YOU WISH TO PRINT ITEM FILES?"
                if fn.input%("(Y OR N)",256)  then \
                        gosub 15        rem process weird responses
                if stopit%  then return
                if uin$ = "Y" or uin$ = "YES"  then \
                        print% = true%:return
                if uin$ = "N" or uin$ = "NO"  then \
                        print% = false%:return
                print tab(5); bell$; emsg$(9)
        wend
        return

15      rem------process weird responses------
        if cr%  then uin$ = "Y"
        return

30      rem-----validate part no------
%include iiyprtno

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
                if stopit% or back%  then return
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
                print tab(5); bell$; emsg$(10)
        wend
        return

60      rem-----look for cr, stop------
        if stopit%  then return         rem premature end
        if cr%  then return
        if back% and desc$ = "ENDING"  then return
        back% = false%
        invalid% = true%
        print tab(5); bell$; emsg$(9)
        return

90      rem-----get 1st part no------
        if start$ = null$  then \
                file.ptr% = 1 :\
                part.rec% = 1 :\
                gosub 100    \ rem read next
           else \
                gosub 95        rem read using part no
        startup$ = prt.number$
        return

95      rem----- part lookup -------------------------
        part.rec% = 2
        if pr2.part.files% = 1  or start$ < pr2.lo.number$(2)  then \
                file.ptr% = 1 :\
                goto 95.1
        if pr2.part.files% = 2  or start$ < pr2.lo.number$(3)  then \
                file.ptr% = 2 else file.ptr% = 3
95.1
        while left$(start$,start.len%) > left$(prt.number$,start.len%)
                gosub 100               rem read a record
        wend                            rem do seq. until start found
        if prt.deleted%  then \
                gosub 100       rem  get next rec
        record.read% = true%
        part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
        return

100     rem-----get part-----
        part.rec% = part.rec% + 1
        while part.rec% > part.records%(file.ptr%) + 1
                if file.ptr% = pr2.part.files%	then \
                        more.parts% = false% :\
                        return
                part.rec% = 2
                file.ptr% = file.ptr% + 1
        wend
        read #part.file%(file.ptr%),part.rec%;\
%include iiyprt00

        if prt.deleted%  then goto 100
        if end$ <> null$  and \
           (left$(end$,end.len%)) < (left$(prt.number$,end.len%))  then \
                more.parts% = false%
        return

200     rem-----check for duplicate part #'s------
        if prt.number$ = print.number$	then \
                dup%(file.ptr%) = true% :\
                ast$ = "**"
        print.number$ = prt.number$
        print.vendor$ = prt.vendor$
        print.order.date$ = prt.order.date$
        print.order.due$  = prt.order.due$
        print.desc$   = prt.desc$
        print.construct = prt.construct
        print.deleted% = prt.deleted%
        print.retail  = prt.retail
        print.value   = prt.value
        print.cost    = prt.cost
        print.reord.pt= prt.reord.pt
        print.std.reord = prt.std.reord
        print.bk.order= prt.bk.order
        print.on.order= prt.on.order
        print.stock   = prt.stock
        print.wip     = prt.wip
        print.drive$  = pr2.part.drive$(file.ptr%)
        print.rec%    = part.rec% - 1
        return

300     rem------print line------
        if not print% and ast$ = null$	then \
                return  rem don't print if not duplicate
        if fn.abort%  then goto 999.2	rem abort
        if lines% >= pr1.lines.per.page%  then \
                gosub 350       rem do title
        print using form1$; tab(1);ast$;tab(3);print.drive$;tab(5);\
           print.number$; tab(16); print.desc$; tab(47); print.vendor$; tab(53); print.retail; \
           tab(62); print.value; tab(72); print.cost; tab(80); print.stock; \
           tab(87); print.reord.pt; tab(94); print.std.reord; tab(101); \
fn.date.out$(print.order.date$);tab(110);fn.date.out$(print.order.due$); \
           tab(119); print.on.order; tab(126); print.bk.order
        lines%=lines%+2
        if pr1.manu.used%  then \
                print using "&"+no$+"&"+no$;tab(53);wip$; tab(62); print.wip; \
                   tab(72); const$; tab(93); print.construct:\
                lines%=lines%+1
        ast$ = null$
        return

350     rem-----do title ------------
        lines% = fn.hdr%(fn.spread$("ITEM FILE PRINT",1)) + 7
        print
        print tab(3); "DV"; tab(8); "ITEM"; tab(19); "DESCRIPTION"; TAB(46); \
           "SUPPLIER"; tab(56); "PRICE"; tab(66); "VALUE"; tab(74); "COST"; \
           tab(82); "NO.IN"; tab(92); "REORDER"; tab(103);\
           "DATE"; tab(113); "DATE"; tab(121); "QUANTITY ON"
        print tab(49); "NO."; tab(82); \
           "STOCK"; tab(89); "POINT"; tab(98); "QTY"; tab(102); \
           "ORDERED"; tab(113); "DUE"; tab(121); "ORDER"; tab(130); "B/O"
        print
        return

390     rem-----print message if no parts in range-------
        no.part.msg$ = "THERE WERE NO ITEM NUMBERS WITHIN THE SPECIFIED RANGE"
        if partial% and lines% = 90  then \
                console   :\
                print tab(10); no.part.msg$ :\
                common.msg$ = no.part.msg$  :\
                print% = false%
        return

400     rem-----part file close & rename------
        if partial%  then \
                gosub 450 \     rem print partial msg
           else \
                gosub 410       rem do foot
for file.ptr% = 1 to pr2.part.files%
        read #part.file%(file.ptr%),1;\
%include iiyprt90
        if last.update$(file.ptr%) > pr2.last.update$  then \
                pr2.last.update$ = last.update$(file.ptr%)
        prt.last.update$=last.update$(file.ptr%)
        prt.no.recs%=part.records%(file.ptr%)
        prt.deleted.recs%=deleted.recs%(file.ptr%)
        prt.high.prt.no$=high.part.number$(file.ptr%)
        print  #part.file%(file.ptr%),1;\
%include iiyprt90

        close part.file%(file.ptr%)

        if not partial%  then \
                gosub 420       rem print statistics

        if dup%(file.ptr%)  then \
                gosub 500 \     rem rename to 111
           else \
                gosub 550       rem rename to 101
next
if partial%  then return        rem don't set sort needed flag if whole file

pr2.part.file.sort.needed% = false%
for i% = 1 to pr2.part.files%	rem hasn't been read
        if type$(i%) <> "101"  then \
                pr2.part.file.sort.needed% = true%
next i%

open  common.drive$ +":"+ system$ + "pr2.101"  as pr2.file%
print #pr2.file%; \
%include iiypr200

close pr2.file%
return

410     rem-----do foot-----
        if not print%  then return
        form2$ = "& #### ####"
        if fn.abort%  then goto 999.2	rem abort
        if lines% > pr1.lines.per.page% - 7  then \
                lines% = fn.hdr%(fn.spread$("FILE STATISTICS",1)) + 4
        print
        print tab(54); "DISK"; tab(65); "TOTAL"; tab(76); "DELETED"
        print tab(54); "DRIVE"; tab(64); "RECORDS"; tab(76); "RECORDS"
        print
        return

420     rem-----print stats-----
        if not print%  then return
        if fn.abort%  then goto 999.2
        print using form2$; tab(56); pr2.part.drive$(file.ptr%); tab(65); \
            part.records%(file.ptr%); tab(77); deleted.recs%(file.ptr%)
        return

450     rem-----print partial msg-----
        if not print%  then return
        if start$ = null$  then start$ = startup$
        if end$ = null$  then end$ = prt.number$
        print
        print tab(20); "THIS IS A PARTIAL LISTING COVERING ITEM NUMBER "; \
                start$; " THROUGH ITEM NUMBER "; end$
        print
        return

500     rem-----rename if dup------
        console
        print tab(5); bell$; emsg$(6); pr2.part.drive$(file.ptr%)
        print tab(5); bell$; emsg$(7)
        common.msg$=emsg$(06)
        lprinter
        if partial%  then return
        if type$(file.ptr%) = "111"  then return
        if rename(pr2.part.drive$(file.ptr%)+part.f.name$+"111", \
                 pr2.part.drive$(file.ptr%)+part.f.name$+type$(file.ptr%)) =0 \
                then print tab(5); bell$; emsg$(5) :\
                     goto 999.1 	rem abend
        type$(file.ptr%) = "111"
        return

550     rem-----rename if not dup-----
        if partial%  then return
        if type$(file.ptr%) <> "111"  then return       rem don't rename unsrtd
        if rename(pr2.part.drive$(file.ptr%)+part.f.name$+"101", \
                pr2.part.drive$(file.ptr%)+part.f.name$+type$(file.ptr%)) = 0 \
               then  print tab(5); bell$; emsg$(5) :\
                     goto 999.1 rem abend
        type$(file.ptr%) = "101"
        return

end

