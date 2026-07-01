%include iiycomm
prgname$="UPDATE 18 OCTOBER, 1979 "
rem---------------------------------------------------------
rem
rem	  I N V E N T O R Y
rem
rem	  U  P	D  A  T  E
rem
rem   COPYRIGHT (C) 1979-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="UPDATE"

%include iiyinit
%include zconfirm
%include zinput

dim emsg$(20)
emsg$(01)="IY401 ITEM FILE FOUND FROM PREVIOUS ABORTED RUN"
emsg$(02)="IY402 ITEM FILE NOT FOUND"
emsg$(03)="IY403 ITEM FILE MOUNTED ON WRONG DRIVE"
emsg$(04)="IY404 UNEXPECTED END OF FILE ON ITEM FILE"
emsg$(05)="IY405 PR2 FILE NOT FOUND OR NULL"
emsg$(06)="IY406 ACTIVITY REPORT HAS NOT BEEN RUN"
emsg$(07)="IY407 INVALID RESPONSE"
emsg$(08)="IY408 Y, YES, N, OR NO ONLY"
emsg$(09)="IY409 ITEM FILE RENAME FAILED"
emsg$(10)="IY410"
emsg$(11)="IY411"
emsg$(12)="IY412"
emsg$(13)="IY413"
emsg$(14)="IY414"
emsg$(15)="IY415"
emsg$(16)="IY416"
emsg$(17)="IY417"
emsg$(18)="IY418"
emsg$(19)="IY419"
emsg$(20)="IY420"

pr2.file% = 2
pr2.name$ = common.drive$+":IYPR2.101"
if size(pr2.name$) = 0	then \
        print tab(5); bell$; emsg$(5) :\
        common.msg$ = emsg$(5)  :\
        goto 999.1      rem abend

if not pr2.activity.report.run%  then \
        gosub 10        rem offer option to stop

gosub 20        rem determine which accum's to zero
if stopit%  then goto 999       rem doesn't want to do anything

%include iiyprt11

rem--------------------------------------------------------
rem----------main driver-------------------
part.rec% = 1
file.ptr% = 1
more.recs% = true%
gosub 100       rem get record
while more.recs%
        gosub 200       rem zero accum's
        gosub 300       rem write rec
        gosub 100       rem get record
wend
rem----------end of driver-----------------
rem---------------------------------------------------------

rem--------------------------------------------------------
rem-----------eoj--------------------------
gosub 400       rem close & rename part file(s)
gosub 500       rem write to pr2


%include zeoj

rem---------------------------------------------------------
rem----------subroutines--------------------

%include iiyprt70       rem close files on abend

10      rem-----offer option to stop------
        print tab(5); bell$; emsg$(6)
        if not fn.confirmed%  then \    rem prem end
                common.msg$ = emsg$(6) :\
                goto 999.2
        return

20      rem------request accum's to be zeroed-------
        dim zero%(4)
        for i% = 1 to 4
                zero%(i%) = 0
        next i%
        req% = 1
        max.req% = 2    rem set this to 4 when wip implemented

21      while req% <= max.req%
                if req% > 2  then \
                        wip$ = "WIP " \
                   else \
                        wip$ = null$
                if req% = 1  or req% = 3  then \
                        per$ = pr1.current.period$ \
                   else \
                        per$ = pr1.to.date.period$
                print
                print tab(5); "ZERO "+wip$+"ACCUMULATORS FOR "+per$+"?"
                if fn.input%("(Y OR N)",256)  then \
                        gosub 25  :\    rem process funny responses
                        goto 21
                gosub 26        rem set flag array
                if invalid%  then goto 21
                req% = req% + 1
        wend
        gosub 30        rem set accum flags
        return

25      rem-----process funny responses-----
        if stopit%  then goto 999.2     rem premature end
        if ctlb% and req% > 1  then \
                req% = req% - 1 :\
                return
        print tab(5); bell$; emsg$(7)
        return

26      rem-----set flag array-----
        invalid% = false%
        if uin$ = "Y" or uin$ = "YES"  then \
                zero%(req%) = true% : return
        if uin$ = "N" or uin$ = "NO"  then \
                zero%(req%) = false% : return
        print tab(5); bell$; emsg$(8)
        invalid% = true%
        return

30      rem-----set accum flags-----
        zero.cur%     = zero%(1)
        zero.td%      = zero%(2)
        zero.wip.cur% = zero%(3)
        zero.wip.td%  = zero%(4)
        if zero.cur% = false%  and zero.td% = false%  and \
           zero.wip.cur% = false%  and zero.wip.td% = false%  then \
                stopit% = true% :\
                print tab(10); "NO ACCUMULATORS WILL BE CHANGED"
        return

100     rem-----get record-----
        part.rec% = part.rec% + 1
        while part.rec% > sorted.part.records%(file.ptr%) + 1
                if file.ptr% = pr2.part.files%  then \
                        more.recs% = false% :\
                        return
                part.rec% = 2
                file.ptr% = file.ptr% + 1
        wend

        read #part.file%(file.ptr%),part.rec%;\
%include iiyprt00

        if prt.deleted%  then goto 100
        return

200     rem-----zero accum's------
        if zero.cur%  then \
                prt.stk.add = 0.0 :\
                prt.stk.dep = 0.0
        if zero.td%  then \
                prt.td.stk.add = 0.0 :\
                prt.td.stk.dep = 0.0
        if zero.wip.cur%  then \
                prt.wip.add = 0.0 :\
                prt.wip.dep = 0.0
        if zero.wip.td%  then \
                prt.td.wip.add = 0.0 :\
                prt.td.wip.dep = 0.0
        return

300     rem-----write part record------
        print #part.file%(file.ptr%),part.rec%;\
%include iiyprt00

        return

400     rem-----close & rename part file(s)------
        for file.ptr% = 1 to pr2.part.files%
                gosub 450       rem write hdr
                file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$
                close part.file%(file.ptr%)
                part.exists%(file.ptr%) = false%
                garbage% =  rename(file.name$+"101",file.name$+"100")
        next file.ptr%
        return

450     rem-----write part header-------
        read #part.file%(file.ptr%),1;\ rem read hdr
%include iiyprt90
        prt.last.update$ = common.date$
        print #part.file%(file.ptr%),1;\
%include iiyprt90
        return

500     rem-----write pr2------
        pr2.activity.report.run% = false%
        if end #pr2.file%  then 501
        open pr2.name$ as pr2.file%
        pr2.exists% = true%
        if end #pr2.file%  then 502
        print #pr2.file%;\
%include iiypr200

        close pr2.file%
        pr2.exists% = false%
        return

501     rem-----null or missing pr2--------
        pr2.exists% = false%
        print tab(5); bell$; emsg$(5)
        common.msg$ = emsg$(5)
        gosub 9         rem close any open files
        goto 999.1      rem abend
502     rem-----normal end on pr2-------
        return
end

