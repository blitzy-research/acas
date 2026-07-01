%include iiycomm
prgname$="SORTPARM  19 OCTOBER, 1979 "
rem---------------------------------------------------------
rem
rem	  I N V E N T O R Y
rem
rem	  S  O	R  T  P  A  R  M
rem
rem   COPYRIGHT (C) 1979-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="SORTPARM"

%include iiyinit
%include iiysortf
%include zstring
%include zinput
%include zdateio
%include zheading
%include zyorn

dim emsg$(10)
emsg$(01)="IY491 INVALID RESPONSE"
emsg$(02)="IY492 DRIVE REFERENCE MUST BE A-Z"
emsg$(03)="IY493 UNABLE TO CREATE: "
emsg$(04)="IY494 UNABLE TO WRITE: "
emsg$(05)="IY495"
emsg$(06)="IY496"
emsg$(07)="IY497"
emsg$(08)="IY498"
emsg$(09)="IY499"
emsg$(10)="IY500"

gosub 10        rem initialize
if pr1.debugging%  then gosub 400       rem request console messages
dim in.drive$(pr2.part.files%), out.drive$(pr2.part.files%)
dim wk.drive$(pr2.part.files%), switch$(pr2.part.files%)

rem--------------------------------------
rem---------main driver-----------
for i% = 1 to pr2.part.files%
        gosub 110       rem print input file msg
        gosub 120       rem get work file drive
        gosub 130       rem ask if switch wanted
        gosub 140       rem get output file drive
        gosub 150       rem build srt file
next i%

if pr1.manu.used%  then gosub 160       rem build bom srt file
gosub 200       rem print sort instructions
rem------------------------------------------
rem-----------------------------------------
%include zeoj

rem--------subroutines--------------
10      rem------initialize-----
%include iiyprt80
        srt.file% = 1
        drive.b$ = chr$(2)
        drive.a$ = chr$(1)
        flag.on% = 1
        flag.off% = 0
        backup% = flag.off%
        console.messages% = flag.off%
        return

110     rem-----print input file msg-----
        print tab(10); "INPUT DRIVE FOR ITEM FILE # "; i%; "IS DRIVE "; \
                pr2.part.drive$(i%)
        in.drive$(i%) = pr2.part.drive$(i%)
        return

120     rem-----get workfile drive------
        desc$ = "WORKFILE"
        gosub 145       rem get drive
        wk.drive$(i%) = drive$
        return

130     rem-----ask if switch wanted------
        print tab(10); "DO YOU WANT TO SWITCH DISKS FOR ITEM FILE # "; \
                i%; " OUTPUT?"
132     if fn.input%("(Y OR N)",256)  then \
                gosub 135  :\   rem process weird responses
                goto 130
        gosub 136       rem plug in y/n
        if invalid%  then 132
        return

135     rem-----evaluate weird responses------
        if stopit%  then goto 999.2     rem prem end
        print tab(5); bell$; emsg$(1)
        return

136     rem----plug in y/n------
        invalid% = false%
        if uin$ = "Y" or uin$ = "YES"  then \
                switch$(i%) = "YES" :\
                change% = 1 :\
                return
        if uin$ = "N" or uin$ = "NO"  then \
                switch$(i%) = "NO"  :\
                change% = 0 :\
                return
        invalid% = true%
        return

140     rem-----get output drive-----
        if change% = 0  then \
                out.drive$(i%) = pr2.part.drive$(i%) :\
                return
        desc$ = "OUTPUT"
        gosub 145       rem get drive
        out.drive$(i%) = drive$
        return

145     rem-----get drive-----
        while true%
                if fn.input%(desc$+" FILE DRIVE",1)  then \
                        gosub 135 :\    rem process weird
                        goto 145
                if uin$ >= "A" and uin$ <= "Z"  then \
                        drive$ = uin$ :\
                        return
                print tab(5); bell$; emsg$(2)
        wend
        return

150     rem-----build part srt's------
        gosub 7725      rem clear sort array's
        parm.name$ = common.drive$+":"+"PART"+str$(i%)+".SRT"
        gosub 300       rem create file
        gosub 155       rem get part file name info
        gosub 156       rem get part file key info
        gosub 7705      rem fill srt fields
        gosub 320       rem write srt file
        close srt.file%
        return

155     rem-----get part file name info-----
        srt.in.drive$ =chr$(asc(in.drive$(i%))-64)
        srt.in.name$ = "IYPRT"
        srt.in.type$ = "001"
        srt.out.drive$ = chr$(asc(out.drive$(i%))-64)
        srt.out.name$ = "IYPRT"
        srt.out.type$ = "111"
        srt.rec.length% = part.recl%
        srt.backup.flag% = backup%
        srt.console.flag% =console.messages%
        srt.work.drive$ = chr$(asc(wk.drive$(i%))-64)
        srt.disk.change.flag% = change%
        return

156     rem-----part key info-----
        srt.kpos%(1) = 1
        srt.klen%(1) = 1
        srt.kad$(1)  = "D"
        srt.kan$(1)  = "N"
        srt.kpos%(2) = 2
        srt.klen%(2) = 10
        srt.kad$(2)  = "A"
        srt.kan$(2)  = "A"
        return

160     rem-----build bom srt file------
return rem not implemented
        gosub 7725      rem clear srt arrays
        parm.name$ = common.drive$+":"+"BOM.SRT"
        gosub 300       rem create srt file
        gosub 165       rem get bom name info
        gosub 166       rem get bom key info
        gosub 7705      rem fill srt fields
        gosub 320       rem write srt file
        close srt.file%
        return

165     rem-----get bom name info-----
return  rem not implemented

166     rem-----get bom key info-----
return  rem not implemented

200     rem-----print sorting instructions------
        print tab(10); "PRINT SORT PARAMETERS?";
        if not fn.yorn%(true%)  and not cr%  then return
        page% = 0
        page.width% = 80
        input "ALIGN FORMS IN PRINTER AND PUSH RETURN"; line trash$
        lprinter
        lines% = fn.hdr%("SORTING PROCEDURES")
        print:print
        print tab(7); "ITEM"; tab(16); "SORTFILE"; tab(29); "INPUT"; tab(39);\
                "OUTPUT"; tab(50); "WORKFILE"; tab(63); "SWITCH"
        print tab(7); "FILE"; tab(18); "NAME"; tab(29); "DRIVE"; tab(40); \
                "DRIVE"; tab(51); "DRIVE"; tab(64); "DISKS"
        print
        for i% = 1 to pr2.part.files%
                print tab(8); str$(i%); tab(16); "PART"+str$(i%)+".SRT"; \
                        tab(31); in.drive$(i%); tab(42); out.drive$(i%); \
                        tab(54); wk.drive$(i%); tab(65); switch$(i%)
                print
        next i%
        if pr1.manu.used%  then \
                print tab(7);"BOM";tab(17);"BOM.SRT"; tab(31); pr1.bom.drive$;\
                tab(42); pr1.bom.drive$; tab(54); pr1.bom.drive$; tab(65);"NO"
        print   rem coddle centronics
        console
        return

300     rem-----create srt file-----
        if end #srt.file%  then 301
        create parm.name$ as srt.file%
        if end #srt.file%  then 302
        return

301     rem-----here on unsuccessful create------
        print tab(5); bell$; emsg$(3); parm.name$
        goto 999.1      rem abend

302     rem -----here on bad write------
        print tab(5); bell$; emsg$(4); parm.name$
        goto 999.1      rem abend
        return

320     rem------write srt file-----
        print #srt.file%;\
                srt.record$
        return

400     rem-----debugging massages-----
        print
        print tab(10); "WANT CONSOLE MESSAGES? (Y OR N)";
        if fn.yorn%(false%)  then \
                console.messages% = 2
        if stopit%  then goto 999.2     rem bail out
        return
end

