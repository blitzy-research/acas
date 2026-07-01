%include iiycomm
prgname$="DEPLETE  OCT.   18, 1979 "
rem---------------------------------------------------------
rem
rem     D E P L E T E
rem
rem     INVENTORY STOCK DEPLETIONS PROGRAM
rem
rem   COPYRIGHT (C) 1979-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="DEPLETE"

%include iiyinit
dim emsg$(50)
emsg$(01)="IY351 PART FILE FOUND FROM ABORTED RUN"
emsg$(02)="IY352 PART FILE NOT FOUND"
emsg$(03)="IY353 PART FILE MOUNTED ON WRONG DRIVE"
emsg$(04)="IY354 UNEXPECTED END OF FILE ON PART FILE"
emsg$(05)="IY355 INVALID DEPLETION QUANTITY"
emsg$(06)="IY356 PR2 FILE NOT FOUND"
emsg$(07)="IY357 PART FILE RENAME FAILED"
emsg$(08)="IY358 PR2 FILE NOT FOUND"
emsg$(09)="IY359 UNEXPECTED EOF ON AUDIT FILE"
emsg$(10)="IY360 INVALID RESPONSE"
emsg$(11)="IY361 PART VALUE SET TO MIN. (ZERO)"
emsg$(12)="IY362 STOCK MAY NOT BE LESS THAN ZERO"
emsg$(13)="IY363 CURRENT DEPLETIONS AT MIN. (ZERO)"
emsg$(14)="IY364 CURRENT DEPLETIONS AT MAX. (9,999,999)"
emsg$(15)="IY365 YTD DEPLETIONS AT MIN. (ZERO)"
emsg$(16)="IY366 YTD DEPLETIONS AT MAX. (9,999,999)"
emsg$(17)="IY367 PART VALUE SET TO MAX. (9,999,999)"
emsg$(18)="IY368 STOCK MAY NOT EXCEED 999,999"
emsg$(19)="IY369 "
emsg$(20)="IY370 AUDIT FILE CREATE FAILED"
emsg$(21)="IY371 AUDIT FILE FOUND FROM PREVIOUS ABORTED RUN"
emsg$(22)="IY372 AUDIT FILE OPEN FAILED"
emsg$(23)="IY373 Y, N, OR ESCAPE ONLY"
emsg$(24)="IY374 AUDIT FILE RENAME FAILED"
emsg$(25)="IY375 AUDIT FILE RENAME FAILED"
emsg$(26)="IY376 AUDIT FILE RENAME FAILED"
emsg$(27)="IY377 OPEN FAILED"
emsg$(28)="IY378 INVALID PART NUMBER"
emsg$(29)="IY379 INVALID PART KEY"
emsg$(30)="IY380"

rem----------------------------------------------------------
rem
rem     F U N C T I O N       D E F I N I T I O N S
rem
rem----------------------------------------------------------

%include zstring
%nolist
%include zdms
%list
%include zdmschar
%include znumeric
%include zparse
%include zdateio
%include zeditdte

rem----------------------------------------------------------
rem
rem     C O N S T A N T S
rem
rem----------------------------------------------------------

digits% = 6
a$ = "&"
cancel.msg$="TRANSACTION CANCELLED"
max.stock = 999999
max.activity=9999999
back$="^"

search.file%=16
pr2.file% = 2
pr2.name$ = common.drive$+":iypr2.101"

rem----------------------------------------------------------
rem
rem     M A I N      P R O G R A M      D R I V E R
rem
rem----------------------------------------------------------

gosub 20                        rem get pr2 file status
if not ok% \
        then    print bell$;tab(5);emsg$(08) :\
                common.msg$=emsg$(08)  :\
                goto 999.1

gosub 10                                rem audit file foolaround
if stopit% then goto 999.2              rem exit without running
if not ok% then goto 999.9              rem abend on file wierdness

%include iiyprt11

%include fiydep                 rem get screen formatting
gosub 50                                rem set up screen

part.rec%=0:file.ptr%=1                 rem initialize for first get-rec

gosub 100                               rem get a part record

while not stopit%
        gosub 110                       rem deplete quantity
        if write.needed% \
                then    gosub 600  :\   rem write the new prt record
                        gosub 610       rem write the new audit record
        gosub 100                       rem get a part record
wend

print using a$;fn.crt.msg$("STOP REQUESTED")

gosub 800                               rem write audit hdr, rename files
gosub 820                               rem open, write, close  pr2

%include zeoj

999.9   rem-----here if bad eoj------------------------------
        gosub 9                         rem close files
        goto 999.1

rem----------------------------------------------------------
rem
rem     s u b r o u t i n e s
rem
rem----------------------------------------------------------

10      rem------audit file fool around-----
        ok%=true%
        if not pr1.depletions.audit.used%  then return
        aud.wk.name$ = pr1.audit.drive$+":IYAUD.000"
        aud.out.name$ = pr1.audit.drive$+":IYAUD.001"
        gosub 30                        rem search for audit work file
        gosub 40                        rem search for audit out file
        if aud.wk.exists% then \
                print tab(5); bell$; emsg$(21) :\
                common.msg$ = emsg$(21) :\
                ok%=false%                      rem abend

        if not aud.out.exists% then \
                gosub 16 :\     rem create audit file
                gosub 17 :\     rem write hdr
                return
        gosub 18        rem rename to 000

        gosub 11        rem open audit, read hdr
        if not ok% then return
        gosub 12        rem proofed?

        gosub 13        rem decide what to do
        if stopit%  then \
                gosub 19 :\     rem rename to 001
                return          rem prem. end
        if delete.ok%  then \
                close audit.file% :\
                gosub 16        rem create new file...else add to old one

        gosub 17        rem print new hdr
        return

11      rem-----open aud file, read hdr------
        aud.f.type$ = "000"
        gosub 6.100     rem open
        if not aud.exists%  then \
                print tab(5); bell$; emsg$(22) :\
                common.msg$ = emsg$(22) :\
                ok%=false%                      rem abend
        gosub 6.301     rem read hdr
        if not ok% then \
                print tab(5);bell$;emsg$(09)  :\
                common.msg$=emsg$(09)  :\
                return
        return

12      rem-----proofed?------
        if aud.proofed%  then \
                print tab(10); "EXISTING AUDIT FILE HAS BEEN PROOFED" \
           else \
                print tab(10); "EXISTING AUDIT FILE HAS NOT BEEN PROOFED"
        return

13      rem------decide on appropriate action-----
        add% = false%
        while true%
                if aud.dep.run%  then \
                        gosub 14 \      rem request add
                   else \
                        print tab(10); "EXISTING AUDIT FILE IS NOT OF "+\
                                "DEPLETIONS TYPE"
                if stopit% or add%  then return
                gosub 14.5      rem request erase
                if stopit% or delete.ok%  then return
                if not aud.dep.run%  then \
                        stopit% = true%:return
        wend
        return

14      rem-----add to existing file?------
        add% = false%
        print tab(10); "ADD TO EXISTING FILE? (Y, N, OR ESC)";
        gosub 15        rem t/f
        if stopit%  then return
        if t%  \
                then    add% = true%    \
                else    add% = false%
        return

14.5    rem-----delete ok?------
        print tab(15); "ERASE IT? (Y, N, OR ESC)";
        gosub 15        rem t/f
        if t%  then \
                delete.ok% = true% \
           else \
                delete.ok% = false%
        return

15      rem-----enter t/f/cr/back/stopit-----------------------
        t%=false%:f%=false%:cr%=false%:back%=false%:stopit%=false%
        while true%
                input "";line in$
                if in$<>null$ then in$=ucase$(in$)
                if in$=escape$ then stopit%=true%:return
                if in$=return$ then cr%=true%:return
                if in$=back$ then back%=true%:return
                if in$="Y" or in$="YES" or in$="T" or in$="TRUE" or in$="OK" \
                        then    t%=true%:return
                if in$="N" or in$="NO" or in$="F" or in$="FALSE" \
                        then    f%=true%:return
                print bell$;tab(5);emsg$(23)
        wend

16      rem-----create audit file------
        aud.f.type$ = "000"
        gosub 6.200     rem create
        if not aud.exists%  then \
                print tab(5); bell$; emsg$(20) :\
                common.msg$ = emsg$(20) :\
                ok%=false%              rem abend
        aud.no.recs% = 0
        pr2.audit.number% = pr2.audit.number% + 1
        aud.proof.no%=0
        return

17      rem-----write aud hdr------
        aud.proofed% = false%
        aud.add.run% = false%
        aud.dep.run% = true%
        aud.start.job% = false%
        aud.end.job% = false%
        aud.run.date$ = common.date$
        gosub 6.401     rem write audit hdr
        return

18      rem-----rename output to work-------
        trash%=rename(aud.wk.name$,aud.out.name$)
        return

19      rem-----rename work to output-----
        trash%=rename(aud.out.name$,aud.wk.name$)
        return

20      rem-----get pr2 file--------------------------------------
        size.pr2%=size(pr2.name$)
        if size.pr2%=0 \
                then    ok%=false% \
                else    ok%=true%
        return

30      rem-----search for audit work file------------------------
        if end #search.file% then 31
        open aud.wk.name$ as search.file%
        aud.wk.exists%=true%
        close search.file%
        return

31      rem-----here if aud out file not found--------------------
        aud.wk.exists%=false%
        return

40      rem-----search for audit out file-------------------------
        if end #search.file% then 41
        open aud.out.name$ as search.file%
        aud.out.exists%=true%
        close search.file%
        return

41      rem-----here if aud out file not found--------------------
        aud.out.exists%=false%
        return

50      rem -----set up screen-----
        num.batch%     = 1
        num.prt.no%    = 2
        num.dep.no%    = 3
        num.qty.stk%   = 4
        num.desc%      = 5
        output% = fn.crt.display.data%(str$(pr2.audit.number%),num.batch%)
        return

100     rem-----get a part record------------------------------
        while true%
                gosub 105                       rem get a part number
                if stopit% then return
                if cr% then return
        wend
        return

105     rem-----get a part number------------------------------
        ok%=true%:cr%=false%:stopit%=false%:back%=false%
        in$=fn.crt.input$(num.prt.no%)
        print using a$;fn.crt.msg$(null$)
        if crt.end.char%=valid.data% \
                then    gosub 1000 :\   rem read part record
                        current$=in$  :\
                        return    \
                else    in$=current$
        if crt.end.char% = ctln%  then \
                gosub 1200      :\ rem get next record
                return
        if crt.end.char% = ctlb%   then \
                gosub 1150      :\  rem get prev record
                return
        if crt.end.char% = return%  and record.read%  then \
                cr%=true%   :\
                return
        if crt.end.char% = ctlr%  then \
                gosub 160       :\ rem refresh screen
                return
        if crt.end.char% = ctls%  then \
                gosub 700       :\ rem save files
                return
        if crt.end.char% = escape%  then \
                stopit%=true%                   :\
                return
        print using a$; fn.crt.msg$(bell$+emsg$(10))
        return

110     rem-----deplete quantity-------------------------------
        ok%=true%
        write.needed%=true%
        gosub 115                       rem get deplete quan
        if not ok% then goto 110
        if cancel% \
                then    print using a$;fn.crt.msg$(cancel.msg$) :\
                        write.needed%=false%  :\
                        return
        if cr% or stopit%  then write.needed%=false%:return
        gosub 120                       rem deplete current stock
        if not ok% then write.needed%=false%
        return

115     rem-----get deplete quan-------------------------------
        ok%=true%:cr%=false%:stopit%=false%:back%=false%
        deplete.quan=0
        in$=fn.crt.input$(num.dep.no%)
        print using a$;fn.crt.msg$(null$)
        if crt.end.char%=valid.data% \
                then    gosub 130   :\          rem edit depletion quan
                        trash%=fn.crt.display.data%(str$(deplete.quan),  \
                                        num.dep.no%)   :\
                        return    \
                else    trash%=fn.crt.display.data%(null$,num.dep.no%)
        if crt.end.char% = ctlb%   then \
                cr%=true        :\              rem end this trans
                return
        if crt.end.char% = return%  then \      rem return
                cr%=true%   :\
                return
        if crt.end.char% = ctlr%  then \
                gosub 160       :\              rem refresh screen
                return
        if crt.end.char% = escape%  then \
                stopit%=true%                   :\
                return
        if crt.end.char%=ctlx% then   \         rem cancel
                cancel%=true%:return
        print using a$; fn.crt.msg$(bell$+emsg$(10))
        return

120     rem-----deplete current stock---------------------------
        temp=prt.stock-deplete.quan
        if temp<0 \
                then    print using a$;fn.crt.msg$(bell$+emsg$(12)) :\
                        ok%=false%  :\
                        return
        if temp>max.stock \
                then    print using a$;fn.crt.msg$(bell$+emsg$(18)) :\
                        ok%=false%   :\
                        return
        if deplete.quan<0 \
                then    backout%=true%   \
                else    backout%=false%
        gosub 140                       rem reduce stock value
        prt.stock=temp
        trash%=fn.crt.display.data%(str$(prt.stock),num.qty.stk%)
        gosub 125                       rem adjust activity accums
        return

125     rem-----adjust activity accums------------------------------
        temp=prt.stk.dep+deplete.quan
        if temp<=0 \
                then    print using a$;fn.crt.msg$(bell$+emsg$(13)) :\
                        for i=1 to 400:next i   :\
                        prt.stk.dep=0   \
                else    prt.stk.dep=temp
        if temp>=max.activity \
                then    print using a$;fn.crt.msg$(bell$+emsg$(14)) :\
                        for i=1 to 400:next i   :\
                        prt.stk.dep=max.activity  \
                else    prt.stk.dep=temp
        temp=prt.td.stk.dep+deplete.quan
        if temp<=0 \
                then    print using a$;fn.crt.msg$(bell$+emsg$(15)) :\
                        for i=1 to 400:next i   :\
                        prt.td.stk.dep=0    \
                else    prt.td.stk.dep=temp
        if temp>=max.activity \
                then    print using a$;fn.crt.msg$(bell$+emsg$(16)) :\
                        for i=1 to 400:next i   :\
                        prt.td.stk.dep=max.activity   \
                else    prt.td.stk.dep=temp
        return

130     rem-----edit depletion quan-----------------------------
        if left$(in$,1)="-" \
                then    in$=right$(in$,len(in$)-1)      :\
                        neg%=true%                       \
                else    neg%=false%
        if not fn.num%(in$) or len(in$)>digits% \
                then    print using a$;fn.crt.msg$(bell$+emsg$(05)) :\
                        ok%=false%:return
        deplete.quan=val(in$)
        if neg% then deplete.quan=deplete.quan*(-1)
        return

140     rem-----reduce stock value------------------------------
        if not pr1.average.used% then return
        if prt.stock<>0 \
                then    average.value=prt.value/prt.stock :\
                        delta.value=average.value*deplete.quan \
                else    average.value=0  :\
                        delta.value=0
        delta.value=(int(delta.value*100))/100
        if prt.value-delta.value<0 \
                then    print using a$;fn.crt.msg$(bell$+emsg$(11))  :\
                        delta.value=prt.value
        if prt.value-delta.value>9999999 \
                then    print using a$;fn.crt.msg$(bell$+emsg$(17))  :\
                        delta.value=-(9999999-prt.value)
        prt.value=prt.value-delta.value
        return

150     rem-----display part record-----
        output% = fn.crt.display.data%(prt.number$,num.prt.no%)
        output% = fn.crt.display.data%(null$,num.dep.no%)
        output% = fn.crt.display.data%(str$(prt.stock),num.qty.stk%)
        output% = fn.crt.display.data%(prt.desc$,num.desc%)
        return

160     rem-----refresh screen------
        output% = fn.crt.display.background%
        output% = fn.crt.refresh.data%
        return

600     rem-----write to file(s)------
        print #part.file%(file.ptr%), part.rec%; \
%include iiyprt00
        return

610     rem-----write the new audit record---------------------------
        if not pr1.depletions.audit.used%  then return
        aud.prt.no$ = prt.number$
        aud.desc$ = prt.desc$
        aud.depletion% = true%
        aud.reverse.trans% = backout%
        aud.trans.qty = abs(deplete.quan)
        if pr1.average.used% \
                then    aud.value.chg=delta.value \
                else    aud.value.chg=0
        aud.unit.cost = prt.cost
        aud.no.recs% = aud.no.recs% + 1
        gosub 6.403     rem write audit record rand
        return

700     rem-----save files------
        print using a$;fn.crt.msg$("SAVING FILES")
        for file.ptr% = 1 to pr2.part.files%
                close part.file%(file.ptr%)
                gosub 710       rem re-open part file
        next file.ptr%
        part.rec%=0:file.ptr%=1         rem initialize for first get-rec
        if not pr1.depletions.audit.used%  then return
        gosub 820       rem update pr2
        gosub 6.401     rem write new hdr
        close audit.file%
        aud.f.type$ = "000"
        gosub 6.100     rem re-open audit file
        if not aud.exists%  then \
                print using a$; fn.crt.msg$(bell$+emsg$(27)) :\
                common.msg$ = emsg$(27) :\
                goto 999.9      rem abend
        print using a$;fn.crt.msg$("RECORDS SAVED: "+str$(aud.no.recs%))
        return

710     rem-----open part files-----
        type$ = "100"
        if end #part.file%(file.ptr%)  then 2.59
        open file.name$+type$ \
                recl    part.recl%      \
                as      part.file%(file.ptr%) \
                buff    part.buff%      \
                recs    sector.len%
        return

800     rem-----rename files-----
        if pr1.depletions.audit.used%  then \
                gosub 810       rem do audit hdr & rename
        for file.ptr% = 1 to pr2.part.files%
                gosub 815       rem rename part file
        next file.ptr%
        return

810     rem-----write audit hdr & rename-----
        gosub 6.401     rem write hdr
        close audit.file%
        trash%= rename(aud.out.name$,aud.wk.name$)
        return

815     rem-----rename prt.files-----
        read #part.file%(file.ptr%),1;\ rem read hdr
%include iiyprt90
        prt.last.update$ = common.date$
        print #part.file%(file.ptr%),1;\        rem write hdr
%include iiyprt90
        file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$
        close part.file%(file.ptr%)
        if not rename(file.name$+"101",file.name$+"100")  then \
                print using a$; fn.crt.msg$(bell$+emsg$(7)) :\
                common.msg$ = emsg$(7) :\
                goto 999.9      rem abend
        return

820     rem-----write pr2--------
        pr2.activity.report.run% = false%
        pr2.last.update$ = common.date$
        if end #pr2.file% then 821
        open pr2.name$ as pr2.file%
        print #pr2.file%; \
%include iiypr200
        close pr2.file%
        return

821     rem-----here if pr2 file not found-------------------
        print using a$;fn.crt.msg$(bell$+emsg$(06))
        ok%=false%
        return

1000    rem----- part lookup -------------------------
record.read% = false%
int.invalid% = false%
key.invalid% = false%
old.rec% = part.rec%
old.ptr% = file.ptr%

if left$(in$,1)="@" \
        then    gosub 1100   :\         rem read file by rel rec no
        else    new.part$=left$(ucase$(in$)+blank$,10)    :\
                gosub 1700              rem search by part number
if int.invalid%  then  \
        part.rec% = old.rec%: file.ptr% = old.ptr%:\
        print using a$;fn.crt.msg$(bell$+emsg$(28)): \
        return
if key.invalid%  then  \
        part.rec% = old.rec%: file.ptr% = old.ptr%: \
        print using a$;fn.crt.msg$(bell$+emsg$(29)): \
        return
gosub 1800              rem read a record
if prt.deleted%  then \
        print using a$;fn.crt.msg$("REFERENCE TO DELETED ITEM"): \
        return
record.read% = true%
part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
gosub 150                       rem display a part record
return

1100 rem----- read by file key , record number ---------------

key.invalid% = false%
key$ = ucase$(mid$(in$,2,1))

if key$ > "9" or key$ < "0"  \
        then  part.record$ = right$(in$,len(in$)-2)\
        else  key$ = pr2.part.drive$(1):part.record$=right$(in$,len(in$)-1)

if match(left$(pound$,len(part.record$)),part.record$,1) <> 1  then \
        key.invalid% = true%:return

part.rec% = val(part.record$)+1

for file.ptr% = 1 to pr2.part.files%
        if key$ = pr2.part.drive$(file.ptr%)  then 1100.1   rem key valid
next
key.invalid% = true%
return

1100.1 rem----- here if key valid -------------------

if part.rec% > sorted.part.records%(file.ptr%)+1 or part.rec% < 2  then \
        key.invalid% = true%
return

1150    rem---------get previous part----------
        part.rec% = part.rec% - 1
        while part.rec% < 2
                file.ptr% = file.ptr% - 1
                if file.ptr% < 1  then \
                        file.ptr% = pr2.part.files%
                part.rec% = sorted.part.records%(file.ptr%)+1
        wend
        gosub 1800      rem read part file
        if prt.deleted%  then 1150      rem get prev part
        record.read% = true%
        part.key$ = "@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
        gosub 150       rem display part
        return

1200 rem----- get next record ------------------------
if part.rec%=0  then part.rec% = 1
part.rec% = part.rec% + 1
while part.rec% > sorted.part.records%(file.ptr%)+1
        if file.ptr% = pr2.part.files%  then\
                file.ptr% = 0   rem force to 1st rec of 1st file
        part.rec% = 2:file.ptr% =file.ptr% + 1
wend

gosub 1800                      rem read record
if prt.deleted%  then 1200      rem next record
record.read% = true%
part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
gosub 150                       rem display record
return

rem ----- include to read by binary search ------------
%include iiysirch

rem-----------includes--------------
%include iiyaud10
%include iiyaud20

6.301   rem audit header read
        if end #audit.file% then 63011
        read #audit.file%, 1;\
%include iiyaud90
        ok%=true%
        return

63011   rem-----here if no hdr rec found-----------------------
        ok%=false%
        return

6.401   rem write audit header
        print #audit.file%, 1;\
%include iiyaud90
        return

6.403   rem write audit random
        print #audit.file%, aud.no.recs% + 1;\
%include iiyaud00
        return

%include iiyprt70

