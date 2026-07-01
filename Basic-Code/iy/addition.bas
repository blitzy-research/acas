%include iiycomm
prgname$="ADDITION 19 OCTOBER, 1979 "
rem----------------------------------------------------------
rem
rem       S T O C K  C O N T R O L
rem
rem	  A  D  D  I  T  I  O  N
rem
rem   COPYRIGHT (C) 1980-2009, Applewood Computers.
rem
rem---------------------------------------------------------

program$="ADDITION"

%include iiyinit
dim emsg$(30)
emsg$(01)="IY301 PART FILE FOUND FROM ABORTED RUN"
emsg$(02)="IY302 PART FILE NOT FOUND"
emsg$(03)="IY303 PART FILE MOUNTED ON WRONG DRIVE"
emsg$(04)="IY304 UNEXPECTED END OF FILE ON PART FILE"
emsg$(05)="IY305 DMS ERROR"
emsg$(06)="IY306 DMS ERROR"
emsg$(07)="IY307 "
emsg$(08)="IY308 PR2 FILE NOT FOUND"
emsg$(09)="IY309 TOO MANY DIGITS"
emsg$(10)="IY310 INVALID RESPONSE"
emsg$(11)="IY311 INVALID RESPONSE"
emsg$(12)="IY312 QUANTITY IN STOCK MUST BE BETWEEN ZERO AND 999,999"
emsg$(13)="IY313 CURRENT PERIOD STOCK ADDITIONS SET TO ZERO"
emsg$(14)="IY314 CURRENT PERIOD STOCK ADDITIONS SET TO 999,999"
emsg$(15)="IY315 "+pr1.to.date.period$+" TO DATE STOCK ADDITIONS SET TO ZERO"
emsg$(16)="IY316 "+pr1.to.date.period$+" TO DATE STOCK ADDITIONS SET TO 9,999,999"
emsg$(17)="IY317 CANNOT BE LESS THAN ZERO"
emsg$(18)="IY318 CANNOT EXCEED 999999"
emsg$(19)="IY319 INVALID DATE"
emsg$(20)="IY320 AUDIT FILE CREATE FAILED"
emsg$(21)="IY321 AUDIT FILE FOUND FROM PREVIOUS ABORTED RUN"
emsg$(22)="IY322 AUDIT FILE OPEN FAILED"
emsg$(23)="IY323 Y, N, OR ESCAPE ONLY"
emsg$(24)="IY324 NOT NUMERIC"
emsg$(25)="IY325 NULL AUDIT FILE FOUND"
emsg$(26)="IY326 PART VALUE SET TO 9,999,999.99"
emsg$(27)="IY327 AUDIT FILE OPEN FAILED AFTER SAVING FILES"
emsg$(28)="IY328 INVALID PART NUMBER"
emsg$(29)="IY329 INVALID PART KEY"
emsg$(30)="IY330 VALUE SET TO ZERO"

%include zstring
%include zdms
%include zdmschar
%include znumeric
%include zparse
%include zdateio
%include zeditdte

pr2.exists% = false%
pr2.file% = 2
pr2.name$ = common.drive$+":IYPR2.101"
if size(pr2.name$) = 0	then \
        print tab(5); bell$; emsg$(8) :\
        common.msg$ = emsg$(8) :\
        gosub 9  :\     rem close any open files
        goto 999.1      rem abend

gosub 10        rem audit file foolaround
if stopit%  then 999.2  rem premature burial
gosub 20        rem set up constants

gosub 820       rem update pr2 file

%include iiyprt11

dim crt.screen.buffer$(24)
if crt.init% = 2  then \
        print tab(5); bell$; emsg$(5) :\
        common.msg$ = emsg$(5) :\
        gosub 9 :\ rem close any open files
        goto 999.1      rem exit w/dms error
%include fiyadd rem get screen formatting

gosub 50        rem set up screen

rem----------main program driver------------------
more.additions% = true%
gosub 100       rem get first part
while more.additions%
        gosub 200       rem get changes
        gosub 600       rem write to file(s)
        gosub 100       rem get next part
wend
rem-----------end of main driver------------------

gosub 800       rem write audit hdr, rename files
rem---------end of job------------------
%include zeoj

rem---------subroutines----------------
%include iiyprt70       rem abend file close rtn

10      rem------audit file fool around-----
        if not pr1.additions.audit.used%  then return
        aud.wk.name$ = pr1.audit.drive$+":IYAUD.000"
        aud.out.name$ = pr1.audit.drive$+":IYAUD.001"
        aud.f.type$ = "000"
        gosub 6.100     rem try to open 000 file
        if aud.exists%  then \
                print tab(5); bell$; emsg$(21) :\ rem blow up if 000 exists
                common.msg$ = emsg$(21) :\
                gosub 9 :\ rem close any open files
                goto 999.1
        aud.f.type$ = "001"
        gosub 6.100     rem try to open 001 file
        if not aud.exists%  then \
                gosub 16 :\     rem create audit file
                gosub 17 :\     rem write hdr
                return
        close audit.file%
        garbage% = rename(aud.wk.name$,aud.out.name$)   rem rename to 000
        gosub 11        rem open audit, read hdr
        if aud.eof%  then \     rem null file
                print tab(5); bell$; emsg$(25) :\
                common.msg$ = emsg$(25)  :\
                gosub 9  :\     rem close  any open files
                goto 999.1      rem abend
        gosub 12        rem proofed?
        gosub 13        rem decide what to do
        if stopit%  then \
                close audit.file%  :\
                garbage% = rename(aud.out.name$,aud.wk.name$) :\ rename to 001
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
                gosub 9 :\      rem close open files
                goto 999.1      rem abend
        gosub 6.301     rem read hdr
        return

12      rem-----proofed?------
        if aud.proofed%  then \
                print tab(10); "EXISTING AUDIT FILE HAS BEEN PROOFED" \
           else \
                print tab(10); "EXISTING AUDIT FILE HAS NOT BEEN PROOFED"
        print
        return

13      rem------decide on appropriate action-----
        add% = false%
        while true%
                if aud.add.run%  then \
                        gosub 14 \      rem request add
                   else \
                        print tab(10); "EXISTING AUDIT FILE IS NOT OF "+\
                                "ADDITIONS TYPE"
                print
                if stopit% or add%  then return
                gosub 14.5      rem request erase
                if stopit% or delete.ok%  then return
                if not aud.add.run%  then \
                        stopit% = true%:return
        wend
        return

14      rem-----add to existing file?------
        add% = false%
        while true%
                print tab(10); "ADD TO EXISTING FILE? (Y, N, OR ESC)";
                gosub 15        rem t/f
                if stopit%  then return
                if t%  then \
                        add% = true%: return
                if f%  then add% = false%:return
                print tab(5); bell$; emsg$(23)
        wend
        return

14.5    rem-----delete ok?------
        delete.ok% = false%
        while true%
                print tab(15); "ERASE IT? (Y, N, OR ESC)";
                gosub 15        rem t/f
                if stopit%  then return
                if t%  then \
                        delete.ok% = true% :return
                if f%  then \
                        delete.ok% = false% :return
                print tab(5); bell$; emsg$(23)
        wend
        return

15      rem-----enter t/f/cr/back/stopit-----------------------
        t%=false%:f%=false%:cr%=false%:back%=false%:stopit%=false%
                input "";line in$
                if in$<>null$ then in$=ucase$(in$)
                if in$=escape$ then stopit%=true%:return
                if in$=return$ then cr%=true%:return
                if in$=back$ then back%=true%:return
                if in$="Y" or in$="YES" or in$="T" or in$="TRUE" or in$="OK" \
                        then    t%=true%:return
                if in$="N" or in$="NO" or in$="F" or in$="FALSE" \
                        then    f%=true%:return
        return

16      rem-----create audit file------
        aud.f.type$ = "000"
        gosub 6.200     rem create
        if not aud.exists%  then \
                print tab(5); bell$; emsg$(20) :\
                common.msg$ = emsg$(20) :\
                gosub 9 :\  rem close open files
                goto 999.1
        aud.no.recs% = 0
        pr2.audit.number% = pr2.audit.number% + 1
        aud.proof.no% = 0
        return

17      rem-----write aud hdr------
        aud.proofed% = false%
        aud.add.run% = true%
        aud.dep.run% = false%
        aud.start.job% = false%
        aud.end.job% = false%
        aud.run.date$ = common.date$
        gosub 6.401     rem write audit hdr
        return

20      rem-----set up constants-----
        digits% = 6
        a$ = "&"
        cancel$ = "TRANSACTION CANCELLED"
        max.stk = 999999
        return

30      rem-----check part no-----
        part.invalid% = false%
        new.part$=ucase$(in$)
        len%=len(new.part$)
        for char% = 1 to len%
                character$ = mid$(new.part$,char%,1)
                if (character$ > "9" or character$ < "0") and\
                  (character$ > "Z" or character$ < "A") and\
                  character$ <> "/" and character$ <> "-" \
                then\
                        part.invalid%=true%: new.part$=prt.number$: return
        next
        new.part$=left$(new.part$+blank$,10)
        return

40      rem----- fn.num --------------------------
        num% = fn.num%(in$)
        if len(in$)>digits% or not num%  then \
                num%=false%: \
                print using a$;fn.crt.msg$(bell$+emsg$(09)) :return
        in.num=val(in$)
        return

42      rem----- fn.numeric ----------------------
        numeric% = fn.numeric%(in$,left.digits%,right.digits%)
        if not numeric%  then print using a$;fn.crt.msg$(bell$+emsg$(24)) :\
                return
        in.numeric=val(in$)
        return

50      rem -----set up screen-----
        num.prt.no%    = 2
        num.qty.add%   = 3
        num.unit.cost% = 4
        num.qty.ord%   = 5
        num.date.ord%  = 6
        num.date.due%  = 7
        num.qty.back%  = 8
        num.qty.stk%   = 9
        num.desc%      = 10
        num.batch%     = 1
        output% = fn.crt.display.data%(str$(pr2.audit.number%),num.batch%)
        return

100     rem-----get a part-----
        if pr1.debugging% \
                then print using "&";fn.crt.msg$(str$(fre)+" BYTES FREE")
        qty.added = 0
        field% = num.prt.no%
        while field% = num.prt.no%
                gosub 400       rem input data
                if crt.end.char% = valid.data%  then \
                        gosub 1000      \ rem find part
                  else \
                        gosub 500       rem check control chars
                if not more.additions%  then return
        wend
        return

150     rem-----display part record-----
        if prt.order.date$ = "000000"  then \
                order.date$ = null$ \
           else \
                order.date$ = fn.date.out$(prt.order.date$)
        if prt.order.due$ = "000000"  then \
                order.due$ = null$ \
           else \
                order.due$ = fn.date.out$(prt.order.due$)
        output% = fn.crt.display.data%(prt.number$,num.prt.no%)
        output% = fn.crt.display.data%(str$(prt.on.order),num.qty.ord%)
        output% = fn.crt.display.data%(str$(qty.added),num.qty.add%)
        output% = fn.crt.display.data%(order.date$,num.date.ord%)
        output% = fn.crt.display.data%(str$(prt.cost),num.unit.cost%)
        output% = fn.crt.display.data%(order.due$,num.date.due%)
        output% = fn.crt.display.data%(str$(prt.stock),num.qty.stk%)
        output% = fn.crt.display.data%(str$(prt.bk.order),num.qty.back%)
        output% = fn.crt.display.data%(prt.desc$,num.desc%)
        return

160     rem-----refresh screen------
        output% = fn.crt.display.background%
        output% = fn.crt.refresh.data%
        return


200     rem-----get changes-----
        max.field% = num.qty.back%
        field% = num.qty.add%
        write.it% = false%
        backout% = false%
        gosub 250       rem put prt values in new fields
        while field% > num.prt.no%
                invalid% = false%
                gosub 400       rem input data
        if crt.end.char% <> valid.data%  then \
                invalid% = true%        :\
                gosub 510               \ rem  look at ctrl chars
          else \
                on field%  gosub \
                        300,    \ rem error
                        305,    \ rem back to part no
                        310,    \ rem get qty added
                        320,    \ rem get unit cost
                        340,    \ rem change qty ordered
                        350,    \ rem change date ordered
                        350,    \ rem change date due
                        340,    \ rem change qty backordered
                        300,300   rem error
        if not invalid%  then \
                field% = field% + 1
        if field% > max.field%  then \
                field% = num.qty.add%
        wend
        gosub 360       rem  compute new value & put new fields in prt fields
        if save.stock > prt.stock  then backout% = true%
        return

250     rem-----put prt values in new values-------
        save.stock = prt.stock
        new.on.order = prt.on.order
        new.bk.order = prt.bk.order
        new.stk.add  = prt.stk.add
        new.td.stk.add = prt.td.stk.add
        return

300     rem-----error-----
        invalid% = true%
        field% = num.qty.add%
        write.it% = false%
        return

305     rem-----back to part no-----
        field% = num.prt.no%
        invalid% = true%
        write.it% = false%
        return

310     rem-----get qty added-----
        temp = val(in$)
        out$ = in$
        if temp <> abs(temp)  then \
                in$ = str$(abs(temp))
        gosub 40        rem numeric integer?
        if not num%  then invalid% = true%:return
        qty.added = temp
        if prt.stock + qty.added < 0  or prt.stock + qty.added > 999999  then \
                print using a$; fn.crt.msg$(emsg$(12)) :\
                gosub 335  :\   rem stall
                invalid% = true% :\
                return
        output% = fn.crt.display.data%(out$,num.qty.add%)
        new.stock = prt.stock + qty.added
        gosub 325       rem do qty on order
        output% = fn.crt.display.data%(str$(new.stock),num.qty.stk%)
        write.it% = true%
        return

320     rem----- get unit cost-----
        left.digits% = 5        rem ?
        right.digits% = 2
        gosub 42        rem numeric ?
        if not numeric%  then invalid% = true%:return
        prt.cost = val(in$)
        output% = fn.crt.display.data%(in$,num.unit.cost%)
        write.it% = true%
        return

325     rem------change qty on order-----
        if qty.added < 0.0 then return   rem don't change order info if backout
        new.on.order = prt.on.order - qty.added
        if qty.added > 0.0  then \
                new.bk.order = prt.bk.order - qty.added
        if new.on.order < 0.0  then \
                new.on.order = 0.0
        if new.bk.order < 0.0  then \
                new.bk.order = 0.0
        output% = fn.crt.display.data%(str$(new.on.order),num.qty.ord%)
        output% = fn.crt.display.data%(str$(new.bk.order),num.qty.back%)
        return

330     rem-----accumulator foolaround-----
        new.stk.add = prt.stk.add + qty.added
        new.td.stk.add = prt.td.stk.add + qty.added
        if new.stk.add < 0  then \
                print using a$; fn.crt.msg$(emsg$(13)) :\
                gosub 335  :\   rem stall
                new.stk.add = 0
        if new.stk.add > max.stk  then \
                print using a$; fn.crt.msg$(emsg$(14)) :\
                gosub 335       :\      rem stall
                new.stk.add = max.stk
        if new.td.stk.add < 0  then \
                print using a$; fn.crt.msg$(emsg$(15)) :\
                gosub 335       :\      rem stall
                new.td.stk.add = 0
        if new.td.stk.add > 9999999  then \
                print using a$; fn.crt.msg$(emsg$(16)) :\
                gosub 335       :\      rem stall
                new.td.stk.add = max.stk
        return

335     rem-----stall for time-----
        for i% = 1 to 400
                garbage% = i%   rem stall
        next i%
        return

340     rem-----change qty ordered-----
        gosub 40        rem numeric integer?
        if not num%  then invalid% = true%:return
        temp = val(in$)
        if temp < 0  then \
                print using a$; fn.crt.msg$(emsg$(17)) :\
                gosub 335  :\   rem keep msg on screen a while
                invalid% = true% :\
                return
        if temp > max.stk  then \
                print using a$; fn.crt.msg$(emsg$(18)) :\
                gosub 335  :\   rem stall
                invalid% = true :\
                return
        if field% = num.qty.ord%  then \
                new.on.order = temp \
          else \
                new.bk.order = temp
        output% = fn.crt.display.data%(str$(temp),field%)
        write.it% = true%
        return

350     rem-----change dates-----
        date$ = null$
        if not fn.edit.date%(in$)  then \
                gosub 355       rem check out funny date
        if invalid%  then \
                gosub 351 :\    rem display old date
                return
        if date$ = null$  then \
                date$ = fn.date.in$
        if field% = num.date.ord%  then \
                prt.order.date$ = date$  \
          else \
                prt.order.due$ = date$
        if date$ = "000000"  then \
                disp.date$ = null$ \
          else \
                disp.date$ = fn.date.out$(date$)
        output% = fn.crt.display.data%(disp.date$,field%)
        write.it% = true%
        return

351     rem-----display old date-----
        if field% = num.date.ord%  then \
                date$ = prt.order.date$ \
           else \
                date$ = prt.order.due$
        output% = fn.crt.display.data%(fn.date.out$(date$),field%)
        return

355     rem-----deal with wierd dates------
        invalid% = false%
        if ucase$(in$) = "NONE"  then \
                date$ = "000000" :\
                return
        print using a$; fn.crt.msg$(emsg$(19))
        invalid% = true%
        return

360     rem-----compute new value & plug in new fields------
        gosub 330       rem do accumulator foolaround
        if pr1.average.used%  then \
                gosub 365   :\  rem compute & round added value
                prt.value = prt.value + added.value
        if prt.value < 0.0  then \
                prt.value = 0.0  :\
                print using a$; fn.crt.msg$(bell$+emsg$(30)) :\
                gosub 335       rem stall
        if prt.value > 9999999.99  then \
                prt.value = 9999999.99: \
                print using a$;fn.crt.msg$(bell$+emsg$(26))  :\
                gosub 335       rem stall
        prt.stock = prt.stock + qty.added
        prt.on.order = new.on.order
        prt.bk.order = new.bk.order
        prt.stk.add = new.stk.add
        prt.td.stk.add = new.td.stk.add
        return

365     rem-----compute & round added value------
        temp = (qty.added*prt.cost*100.0)
        added.value = int(temp)
        added.value = added.value/100.0
        if added.value > 9999999.99  then \
                added.value = 9999999.99
        if added.value < -9999999.99  then \
                added.value = -9999999.99
        return

400     rem-----input data------
        in$ = fn.crt.input$(field%)
        print using a$; fn.crt.msg$(null$)
        return

500     rem-----check ctl chars, part no-------
        write.it% = false%
        invalid% = true%
        if crt.end.char% = ctln%  then \
                gosub 1200      :\ rem get next record
                return
        if crt.end.char% = ctlb%   then \
                gosub 1150      :\  rem get prev record
                return
        if crt.end.char% = return%  and record.read%  then \
                field% = num.qty.added% :\
                return
        if crt.end.char% = ctlr%  then \
                gosub 160       :\ rem refresh screen
                return
        if crt.end.char% = ctls%  then \
                gosub 700       :\ rem save files
                return
        if crt.end.char% = escape%  then \
                write.it% = false%  :\
                more.additions% = false%        :\
                field% = 99                     :\
                print using a$; fn.crt.msg$("STOP REQUESTED") :\
                return
        print using a$; fn.crt.msg$(emsg$(10))
        return

510     rem-----check ctl chars, other changes------
        if crt.end.char% = return%  then \
                field% = field% + 1  :\
                gosub 515       :\  rem check value of field
                return
        if crt.end.char% = ctlr%  then \
                gosub 160       :\ rem refresh screen
                return
        if crt.end.char% = ctlb%  then \
                field% = field% - 1   :\
                gosub 515       :\  rem check value of field
                return
        if crt.end.char% = escape%  then \
                field% = num.prt.no%    :\
                return
        if crt.end.char% = ctlx%  then \
                write.it% = false%      :\
                record.read%=false%     :\
                field% = num.prt.no%    :\
                print using a$; fn.crt.msg$(cancel$) :\
                return
        print using a$; fn.crt.msg$(emsg$(11))
        return

515     rem-----check value of field-----
        if field% < num.qty.add%   then field% = max.field%
        if field% > max.field%  then field% = num.qty.add%
        return

600     rem-----write to file(s)------
        if not write.it%  then return
        gosub 2800      rem write part rec
        if not pr1.additions.audit.used%  then return
        aud.prt.no$ = prt.number$
        aud.desc$ = prt.desc$
        aud.depletion% = false%
        aud.reverse.trans% = backout%
        aud.trans.qty = abs(qty.added)
        aud.value.chg = prt.cost*qty.added
        aud.unit.cost = prt.cost
        aud.no.recs% = aud.no.recs% + 1
        gosub 6.403     rem write audit record rand
        return

700     rem-----save files------
        save.ptr% = file.ptr%
        for file.ptr% = 1 to pr2.part.files%
                close part.file%(file.ptr%)
                part.exists%(file.ptr%) = false%
                gosub 710       rem re-open part file
        next file.ptr%
        file.ptr% = save.ptr%
        if not pr1.additions.audit.used%  then return
        close audit.file%
        aud.exists% = false%
        aud.f.type$ = "000"
        gosub 6.100     rem re-open audit file
        if not aud.exists%  then \
                print using a$; fn.crt.msg$(bell$+emsg$(27)) :\
                common.msg$ = emsg$(27) :\
                gosub 9 :\      rem close open files
                goto 999.1      rem abend
        gosub 6.401     rem write aud hdr
        return

710     rem-----open part files-----
        type$ = "100"
        if end #part.file%(file.ptr%)  then 2.59
        open file.name$+type$ \
                recl    part.recl%      \
                as      part.file%(file.ptr%) \
                buff    part.buff%      \
                recs    sector.len%
        part.exists%(file.ptr%) = true%
        return

800     rem-----rename files-----
        if pr1.additions.audit.used%  then \
                gosub 810       rem do audit hdr & rename
        for file.ptr% = 1 to pr2.part.files%
                gosub 815       rem rename part file
        next file.ptr%
        return

810     rem-----write audit hdr & rename-----
        gosub 6.401     rem write hdr
        close audit.file%
        aud.exists% = false%
        garbage% =  rename(aud.out.name$,aud.wk.name$)
        return

815     rem-----rename prt.files-----
        read #part.file%(file.ptr%),1;\ rem read hdr
%include iiyprt90
        prt.last.update$ = common.date$
        print #part.file%(file.ptr%),1;\        rem write hdr
%include iiyprt90
        file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$
        close part.file%(file.ptr%)
        part.exists%(file.ptr%) = false%
        garbage% = rename(file.name$+"101",file.name$+"100")
        return

820     rem-----write pr2--------
        pr2.activity.report.run% = false%
        pr2.last.update$ = common.date$
        if end #pr2.file%  then 820.1
        open pr2.name$ as pr2.file%
        pr2.exists% = true%
        if end #pr2.file%  then 820.2
        print #pr2.file%; \
%include iiypr200
        close pr2.file%
        pr2.exists% = false%
        return

820.1   rem----no pr2------
        pr2.exists% = false%
        print using a$; fn.crt.msg$(bell$+emsg$(8))
        gosub 9         rem close any files left open
        goto 999.1      rem abend
820.2   rem-----normal pr2 eof-----
        return

1000 rem----- part lookup -------------------------
record.read% = false%
int.invalid% = false%
key.invalid% = false%
old.rec% = part.rec%
old.ptr% = file.ptr%

gosub 30                                rem check part number
if part.invalid%  \
        then gosub  1100        \read by file key,record number
        else gosub  1700:       rem search by part number

if int.invalid%  then  \
        part.rec% = old.rec%: file.ptr% = old.ptr%:\
        print using a$;fn.crt.msg$(emsg$(28)): \
        return
if key.invalid%  then  \
        part.rec% = old.rec%: file.ptr% = old.ptr%: \
        print using a$;fn.crt.msg$(emsg$(29)): \
        return
gosub 1800              rem read a record
if prt.deleted%  then \
        print using a$;fn.crt.msg$("REFERENCE TO DELETED ITEM"): \
        return
record.read% = true%
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
if file.ptr%>pr2.part.files% then file.ptr%=1
part.rec% = part.rec% + 1
while part.rec% > sorted.part.records%(file.ptr%)+1
        if file.ptr% = pr2.part.files%  then\
                file.ptr% = 0   rem force to 1st rec of 1st file
        part.rec% = 2:file.ptr% =file.ptr% + 1
wend

gosub 1800                      rem read record
if prt.deleted%  then 1200      rem next record
record.read% = true%
gosub 150                       rem display record
return

rem ----- include to read by binary search ------------
%include iiysirch

2800 rem----- write a record -----------------
if pr1.debugging%  then \
        print using "&";fn.crt.msg$("ITEM RECORD "+str$(part.rec%))
print #part.file%(file.ptr%), part.rec%; \
%include iiyprt00

return

rem-----------includes--------------
%include iiyaud10
%include iiyaud20

rem--------audit file reads---------
rem--------29 june,1979-------------
6.301   rem audit header read
        read #audit.file%, 1;\
%include iiyaud90
        return

6.302   rem audit sequential read
        read #audit.file%;\
%include iiyaud00
        return

6.303   rem audit random read
        read #audit.file%, aud.no.recs% + 1;\
%include iiyaud00
        return

rem-----audit file writes-------
rem-------29 june,1979---------
6.401   rem write audit header
        print #audit.file%, 1;\
%include iiyaud90
        return

6.402   rem write audit sequential
        print #audit.file%;\
%include iiyaud00
        return

6.403   rem write audit random
        print #audit.file%, aud.no.recs% + 1;\
%include iiyaud00
        return

end

