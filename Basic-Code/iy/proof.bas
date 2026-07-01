%include iiycomm
prgname$="PROOF     OCT.  18, 1979 "
rem-----------------------------------------------------------
rem
rem     P R O O F
rem
rem     STOCK CONTROL AUDIT PROOF PRINT PROGRAM
rem
rem     COPYRIGHT (C) 1980-2009, Applewood Computers.
rem
rem-----------------------------------------------------------

program$="PROOF"

%include iiyinit

dim emsg$(15)
emsg$(01)="IY521 PROGRAM MUST BE CALLED FROM MENU"
emsg$(02)="IY522 PROGRAM CAN'T RUN. NO AUDITING REQUESTED"
emsg$(03)="IY523 AUDIT FILE NOT FOUND"
emsg$(04)="IY524"
emsg$(05)="IY525"

rem------------------------------------------------------------
rem
rem     F U N C T I O N      D E F I N I T I O N S
rem
rem------------------------------------------------------------

%include zstring
%include zdateio
%include zheading
%include zbracket

rem------------------------------------------------------------
rem
rem     C O N S T A N T S
rem
rem------------------------------------------------------------

%include iiyaud80
aud.f.type$="001"

line.cnt%=9999

rem------------------------------------------------------------
rem
rem     M A I N      D R I V E R
rem
rem------------------------------------------------------------

if not chained% \
        then    print bell$;tab(5);emsg$(01):goto 999.1

if not pr1.any.audit.used%  \
        then    print bell$;tab(5);emsg$(02)  :\
                common.msg$=emsg$(02)         :\
                goto 999.8

gosub 100                       rem open aud file
if not aud.exists% \
        then    print bell$;tab(5);emsg$(03)  :\
                common.msg$=emsg$(03)         :\
                goto 999.8

REM *** CHANGE TO SUM ADDITIONS AND DEPLETIONS - GIVES CUM CHANGE ***
REM *** UK FIX 6/4/82 SRC ***

        cum.aud.val.chg=0

gosub 110                       rem read aud hdr
gosub 120                       rem create report header

gosub 130                       rem read aud rec
while not aud.eof%
        gosub 140               rem print detail line
        if stopit% then goto 999.8
        gosub 130               rem read aud rec
wend

close audit.file%
gosub 150                       rem set aud hdr rec flags
gosub 160                       rem write aud hdr rec

999.8
print:print:print

rem *** cum change cont***
        lprinter
        print : print
        print tab(90); "TOTAL"; TAB(98); cum.aud.val.chg
        console

%include zeoj

rem------------------------------------------------------------
rem
rem     s u b r o u t i n e s
rem
rem------------------------------------------------------------

100     rem-----open aud file----------------------------------
%include iiyaud10
        return

110     rem-----read aud hdr-----------------------------------
        read #audit.file%,1;   \
%include iiyaud90
        return

120     rem-----create report hdr------------------------------
        rpt2$="CANCELLED TRANSACTION"
        if aud.add.run% \
                then    rpt.name$="A D D I T I O N S     P R O O F"     :\
                        rpt1$="ADDITIONS"                               :\
                else    rpt.name$="D E P L E T I O N S     P R O O F"   :\
                        rpt1$="DEPLETIONS"
        hdr3$="BATCH NUMBER "+str$(pr2.audit.number%)+   \
                ", PROOF NUMBER "+str$(aud.proof.no%+1)+  \
                " FOR TRANSACTIONS DATED "+fn.date.out$(aud.run.date$)
        return

130     rem-----read aud rec-----------------------------------
        if end #audit.file% then 131
        read #audit.file%;  \
%include iiyaud00
        return

131     rem-----here at eof on aud file------------------------
        aud.eof%=true%
        return

140     rem-----print detail line------------------------------
        gosub 170                               rem interruption
        if stopit% then return
        lprinter
        if line.cnt%>pr1.lines.per.page% \
                then    gosub 180               rem print rpt hdr
        line.cnt%=line.cnt%+1
        print using "/23456789/";tab(12);aud.prt.no$;
        print using "/2345678901234567890123456789/";tab(27);aud.desc$;
        print using "##,###,###";tab(62);aud.trans.qty;
        if not aud.dep.run% \
                then    print using "##,###,###.##";tab(79);aud.unit.cost;
        if pr1.average.used% \
                then    CUM.AUD.VAL.CHG=CUM.AUD.VAL.CHG+AUD.VALUE.CHG: \
                        print using fn.bracket$(aud.value.chg,8,true%);  \
                                tab(94);abs(aud.value.chg);
        if aud.reverse.trans% \
                then    print tab(111);rpt2$ \
                else    print
        console
        return

150     rem-----set aud hdr rec flags--------------------------
        aud.proofed%=true%
        aud.proof.no%=aud.proof.no%+1
        return

160     rem-----write aud hdr rec------------------------------
        gosub 100                               rem open aud file
        print #audit.file%,1;  \
%include iiyaud90
        close audit.file%
        return

170     rem----------------------------------------------------
        if constat%=0 then return
        trash%=conchar%
        print
        print tab(5);"HIT ESC TO ABORT PRINTOUT"
        print tab(5);"HIT RETURN TO CONTINUE";
        input "";line in$
        if in$=chr$(27) then stopit%=true%
        return

180     rem-----print rpt hdr----------------------------------
        line.cnt%=fn.hdr%(rpt.name$)+8
        print tab(fn.center%(hdr3$,page.width%));hdr3$
        print

        print tab(65);rpt1$;
        if not aud.dep.run% \
                then    print tab(87);"UNIT";
        print tab(99);"CHANGE IN"

        print tab(13);"ITEM NO.";
        print tab(29);"D E S C R I P T I O N";
        print tab(65);"QUANTITY";
        if not aud.dep.run% \
                then    print tab(87);"COST";
        print tab(98);"STOCK VALUE"

        print
        return

