%include iiycomm
prgname$="ACTIVITY    OCT.  19, 1979 "
rem-----------------------------------------------------------
REM
REM     A C T I V I T Y
REM
REM     STOCK CONTROL ACTIVITY REPORT PROGRAM
REM
REM     COPYRIGHT (C) 1980-2009, Applewood Computers.
rem
rem-----------------------------------------------------------

program$="ACTIVITY"
%include iiyinit

dim emsg$(15)
emsg$(01)="IY511 PART FILE ON WRONG DRIVE"
emsg$(02)="IY512 UNEXPECTED EOF ON PART FILE"
emsg$(03)="IY513 PROGRAM MUST BE RUN FROM MENU"
emsg$(04)="IY514 OPTION NUMBER OUT OF RANGE"
emsg$(05)="IY515 INVALID PART NUMBER"
emsg$(06)="IY516 INVALID PART NUMBER"
emsg$(07)="IY517 ENDING PART NUMBER IS LESS THAN STARTING PART NUMBER"
emsg$(08)="IY518 PR2 FILE NOT FOUND"
emsg$(09)="IY519"

%include iiyprt12                       rem prt file opens
if abort% then goto 999.1

rem------------------------------------------------------------
rem
rem     F U N C T I O N      D E F I N I T I O N S
rem
rem------------------------------------------------------------

%include zstring
%include zdateio
%include zheading

rem------------------------------------------------------------
rem
rem     C O N S T A N T S
rem
rem------------------------------------------------------------

file.ptr%=1
part.rec%=0

hdr4$="STOCK ACTIVITY REPORT"
max.options%=6
line.cnt%=9999

rem------------------------------------------------------------
rem
rem     M A I N      D R I V E R
rem
rem------------------------------------------------------------

if not chained% \
        then    print bell$;tab(5);emsg$(03):goto 999.1

gosub 100                       rem get report options
if stopit% then goto 999.2

gosub 110                       rem create report header

gosub 130                       rem read and select prt rec
while not prt.eof%
        gosub 140               rem print detail line
        if stopit% then goto 990
        gosub 130               rem read and select prt rec
wend

if option%=1 \                  rem all parts printed
        then    gosub 150 :\    rem set pr2 flag
                gosub 160       rem write out pr2

990     rem-----here at eoj------------------------------------
        lprinter width 133:print:console

print:print:print

%include zeoj

rem------------------------------------------------------------
rem
rem     S U B R O U T I N E S
rem
rem------------------------------------------------------------

100     rem-----get report options-----------------------------
        gosub 102                               rem print option menu
        input "";line in$
        if in$<>null$ then in$=ucase$(in$)
        if in$=chr$(27) or in$="STOP" then stopit%=true%:return
        if in$=return$ then in$="1"             rem all parts is default
        if match(left$(pound$,len(in$)),in$,1)<>1 \
                then    print using "&";crt.clear$+bell$+   \
                        crt.msg.header$+emsg$(04)+crt.home.cursor$      :\
                        for i=1 to 200:next i           :\
                        goto 100
        option%=val(in$)
        if option%<1 or option%>max.options% \
                then    print using "&";crt.clear$+bell$+   \
                        crt.msg.header$+emsg$(04)+crt.home.cursor$      :\
                        for i=1 to 200:next i           :\
                        goto 100
        on option% gosub \
                107,\   rem all parts
                104,\   rem range
                105,\   rem current period
                106,\   rem to date period
                108,\   rem range current
                109     rem range to date
        if back% then goto 100
        return

102     rem-----print option menu------------------------------
        print using "&";crt.clear$
        print:print:print:print
        print tab(20);"SELECT AN ACTIVITY REPORT OPTION NUMBER"
        print:print:print
        print tab(15);"1    ALL ITEMS"
        print tab(15);"2    A RANGE OF ITEM NUMBERS"
        print tab(15);"3    ITEMS ACTIVE IN CURRENT "+pr1.current.period$
        print tab(15);"4    ITEMS ACTIVE IN "+pr1.to.date.period$+" TO DATE"
        print tab(15);"5    A RANGE OF ITEMS ACTIVE IN CURRENT "+   \
                                pr1.current.period$
        print tab(15);"6    A RANGE OF ITEMS ACTIVE IN "+   \
                                pr1.to.date.period$+" TO DATE"
        print:print:print
        print tab(20);"ENTER SELECTION NUMBER:  ";
        return

104     rem-----range of parts---------------------------------
        print
        print tab(10);"ENTER STARTING ITEM NUMBER ";
        gosub 120                       rem get part number
        if part.invalid% \
                then    print bell$;tab(5);emsg$(05)  :\
                        goto 104
        if stopit% or back% then return
        if cr% then new.part$="          "
        start.part$=new.part$
104.1   print
        print tab(10);"ENTER ENDING ITEM NUMBER ";
        gosub 120                       rem get end part number
        if part.invalid% \
                then    print bell$;tab(5);emsg$(06)  :\
                        goto 104.1
        if stopit% then return
        if back% then goto 104
        if cr% then new.part$="zzzzzzzzzz"
        end.part$=new.part$
        if end.part$<start.part$ \
                then    print bell$;tab(5);emsg$(07):goto 104
        hdr3$="ITEM NUMBERS RANGING FROM "+start.part$+" THROUGH "+end.part$
        return

105     rem-----current period activity------------------------
        hdr3$="ITEMS ACTIVE IN CURRENT "+pr1.current.period$
        return

106     rem-----to date period activity------------------------
        hdr3$="ITEMS ACTIVE IN "+pr1.to.date.period$+" TO DATE"
        return

107     rem-----all parts--------------------------------------
        hdr3$="A L L     P A R T S"
        return

108     rem-----range in current period------------------------
        gosub 104                       rem range of parts
        hdr5$=hdr3$
        gosub 105                       rem current period activity
        return

109     rem-----range in period to date------------------------
        gosub 104                       rem range of parts
        hdr5$=hdr3$
        gosub 106                       rem to date period activity
        return

110     rem-----create report hdr------------------------------
        hdr1$="CURRENT "+pr1.current.period$+":"
        hdr2$=pr1.to.date.period$+" TO DATE:"
        return

120     rem-----get part number--------------------------------
        back%=false%:stopit%=false%:cr%=false%
        input "";line in$
        if in$=chr$(27) then stopit%=true%:return
        if in$=back$ then back%=true%:return
        if in$=return$ then cr%=true%:return
%include iiyprtno
        return

130     rem-----read and select prt rec------------------------
        selected%=false%
        while not selected%
                gosub 135                       rem get part.rec%
                if prt.eof% then return
                read #part.file%(file.ptr%),part.rec%+1;\
%include iiyprt00
                if not prt.deleted% \
                        then    gosub 190       rem select record
        wend
        return

135     rem-----get part.rec%----------------------------------
        part.rec%=part.rec%+1
        if part.rec%>part.records%(file.ptr%) \
                then    file.ptr%=file.ptr%+1   :\
                        part.rec%=1
        if file.ptr%>pr2.part.files% \
                then    prt.eof%=true%
        return

140     rem-----print detail line------------------------------
        gosub 170                               rem interruption
        if stopit% then return
        lprinter width 133
        if line.cnt%+1>pr1.lines.per.page% \
                then    gosub 180               rem print rpt hdr
        line.cnt%=line.cnt%+1
        print using "/23456789/";tab(01);prt.number$;
        print using "/2345678901234567890123456789/";tab(12);prt.desc$;
        print using "###,###";tab(43);prt.stock;
        print using "###,###.##";tab(51);prt.retail;
        print using "###,###.##";tab(62);prt.cost;
        if pr1.average.used% \
                then    print using "#,###,###.##";tab(73);prt.value;
        print using "###,###";tab(086);prt.stk.add;
        print using "###,###";tab(093);prt.stk.dep;
        print using "####,###";tab(100);prt.stk.add-prt.stk.dep;

        print using "#######";tab(109);prt.td.stk.add;
        print using "#######";tab(117);prt.td.stk.dep;
        print using "#######";tab(125);prt.td.stk.add-prt.td.stk.dep
        if pr1.manu.used% \
                then    gosub 141               rem wip detail line
        console
        return

141     rem-----wip detail line---------------------------------
        console
        gosub 170                               rem interruption
        if stopit% then return
        lprinter width 133

        line.cnt%=line.cnt%+1
        print tab(45);"WIP:";
        print using "###,###";tab(50);prt.wip;
        print tab(65);"WORK IN PROGRESS:";
        print using "###,###";tab(086);prt.wip.add;
        print using "###,###";tab(093);prt.wip.dep;
        print using "####,###";tab(100);prt.wip.add-prt.wip.dep

        print using "#,###,###";tab(109);prt.td.wip.add;
        print using "#,###,###";tab(117);prt.td.wip.dep;
        print using "##,###,###";tab(125);prt.td.wip.add-prt.td.wip.dep
        return

150     rem-----set pr2 flag-----------------------------------
        pr2.activity.report.run%=true%
        return

160     rem-----write out pr2----------------------------------
        pr2.file%=2
        if end #pr2.file% then 161
        open common.drive$+":IYPR2.101" as pr2.file%
        print #pr2.file%; \
%include iiypr200
        close pr2.file%
        return

161     rem-----here if no pr2 file found----------------------
        print bell$;tab(5);emsg$(08)
        common.msg$=emsg$(08)
        goto 999.1                      rem this is a bad error

170     rem-----interruption-----------------------------------
        if constat%=0 then return
        trash%=conchar%
        print
        print tab(5);"HIT ESC TO ABORT PRINTOUT"
        print tab(5);"HIT RETURN TO CONTINUE";
        input "";line in$
        if in$<>null$ then in$=ucase$(in$)
        if in$=chr$(27) or in$="STOP" then stopit%=true%
        return

180     rem-----print rpt hdr----------------------------------
        line.cnt%=fn.hdr%(rpt.name$)+9
        print tab(fn.center%(hdr4$,page.width%));hdr4$
        print tab(fn.center%(hdr3$,page.width%));hdr3$
        if option%=5 or option%=6 \
                then    print tab(fn.center%(hdr5$,page.width%));hdr5$ :\
                        line.cnt%=line.cnt%+1
        print

        print tab(44);"CURRENT";
        print tab(55);"RETAIL";
        print tab(67);"UNIT";
        if pr1.average.used% \
                then    print tab(78);"STOCK";
        print tab(90);hdr1$;
        print tab(113);hdr2$;
        print tab(02);"ITEM.NO.";
        print tab(14);"D E S C R I P T I O N";
        print tab(45);"STOCK";
        print tab(56);"PRICE";
        print tab(67);"COST";
        vc1$="+ADD+"
        vc2$="-DEP-"
        vc3$="CHANGE"
        if pr1.average.used% \
                then    print tab(78);"VALUE";
                        print tab(88);vc1$;
                        print tab(95);vc2$;
                        print tab(102);vc3$;
                        print tab(111);vc1$;
                        print tab(119);vc2$;
                        print tab(126);vc3$
        print
        return

190     rem-----select record-----------------------------------
        on option% gosub \
                210,\           rem all parts
                195,\           rem range
                200,\           rem active this period
                205,\           rem active to date
                220,\           rem range active this period
                230             rem range active to date
        if left$(prt.number$,len(end.part$)) > end.part$  then \
                prt.eof% = true%
        return

195     rem-----range-------------------------------------------
        if left$(prt.number$,len(start.part$))>=start.part$ and    \
           left$(prt.number$,len(end.part$))<=end.part$ \
                then    selected%=true% \
                else    selected%=false%
        return

200     rem-----active this period------------------------------
        if prt.stk.add<>0 or prt.stk.dep<>0 or \
           prt.wip.add<>0 or prt.wip.dep<>0 \
                then    selected%=true%  \
                else    selected%=false%
        return

205     rem-----active to date----------------------------------
        if prt.td.stk.add<>0 or prt.td.stk.dep<>0 or \
           prt.td.wip.add<>0 or prt.td.wip.dep<>0    \
                then    selected%=true%  \
                else    selected%=false%
        return

210     rem-----all parts---------------------------------------
        selected%=true%
        return

220     rem-----range active this period------------------------
        if left$(prt.number$,len(start.part$))>=start.part$ and    \
           left$(prt.number$,len(end.part$))<=end.part$ \
                then    sel1%=true% \
                else    sel1%=false%
        if prt.stk.add<>0 or prt.stk.dep<>0 or \
           prt.wip.add<>0 or prt.wip.dep<>0 \
                then    sel2%=true%  \
                else    sel2%=false%
        selected%=sel1% and sel2%
        return

230     rem-----range active to date----------------------------
        if left$(prt.number$,len(start.part$))>=start.part$ and    \
           left$(prt.number$,len(end.part$))<=end.part$ \
                then    sel1%=true% \
                else    sel1%=false%
        if prt.td.stk.add<>0 or prt.td.stk.dep<>0 or \
           prt.td.wip.add<>0 or prt.td.wip.dep<>0    \
                then    sel2%=true%  \
                else    sel2%=false%
        selected%=sel1% and sel2%
        return

