%include iiycomm
prgname$="IY  OCT. 19,1979 "
rem---------------------------------------------------------
rem
rem       I N V E N T O R Y
rem
rem       IY
rem
rem   COPYRIGHT (C) 1979-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="IY"

rem----- initialize disc directories -------------------------
initialize
rem----- console -----------------------------------------
console
rem----- set up chaining ---------------------------------
%chain 100,13600,0,3200

dim emsg$(20)
emsg$(01)="IY421  NO PARAMETER FILE"
emsg$(02)="IY422  DMS ERROR"
emsg$(03)="IY423  ERROR DURING CHAIN TO SORT"
emsg$(04)="IY424  ERROR DURING CHAIN TO SORT"
emsg$(05)="IY425  THE PROGRAM IS NOT ON THE CURRENTLY LOGGED DISK"
emsg$(06)="IY426  THE SORT PARAMETER FILE IS NOT ON THE SYSTEM DISK"
emsg$(07)="IY427  ERROR DURING CHAIN TO SORT"
emsg$(08)="IY428"
emsg$(09)="IY429  THIS PROGRAM CAN ONLY BE RUN ON VERIFIED SORTED ITEM FILES"
emsg$(10)="IY430  INVALID SECOND PARAMETER FILE"
emsg$(11)="IY431  QSORT IS NOT ON THE CURRENTLY LOGGED DISK"
emsg$(12)="IY432  THAT'S NOT A VALID RESPONSE"
emsg$(13)="IY433  NO SECOND PARAMETER FILE. CHAINING TO PARTFILE"
emsg$(14)="IY434  THE SYSTEM DRIVE HAS NOT BEEN INITIALIZED"
emsg$(15)="IY435  INVALID DATE"
emsg$(16)="IY436  INVALID PARAMETER FILE"
emsg$(17)="IY437  OPERATOR REQUESTED RETURN TO MENU"
emsg$(18)="IY438  **ERROR**  THE PROGRAM WAS TERMINATED BEFORE COMPLETION"
emsg$(19)="IY439  TRANSACTION HISTORY IS NOT CURRENTLY RECORDED"
emsg$(20)="IY440"

%include iiyconst
%include zserial
%include znumeric
%include zparse
%include zinput
%include zgetdate
%include zsysdriv

%nolist                 rem include zdms,zdmsinit
%include zdms
%include zdmsinit
%list
%include zdmschar

if chained.from.root%  then  \
        goto 1          rem init crt display

rem----- code executed if not chained from root ----------------
chained.from.root%=true%
chained%=true%
common.drive$=fn.get.sys.drive$

crt.init%=fn.crt.initialize%("CRT", null$)
if crt.init% = 2  then \
        print tab(5); bell$ ; emsg$(2) :goto 999.1

dim pr2.part.drive$(3)
dim pr2.lo.number$(3)

if common.drive$=null$ then \
        common.option%=8: chain "IYPARENT"
pr1.file% = 1
if end #pr1.file%  then .38     rem no parameter file
open  common.drive$ +":"+ system$ + "pr1.101"  as pr1.file%
if end #pr1.file%  then .39     rem invalid parameter file
read #pr1.file%; \
%include iiypr100

close pr1.file%
        print:print:print
        print cpyrght$
        print
        print system$;version$;"    SERIAL NUMBER: ";serial.number$
        print:print:print
        print tab(10);pr1.co.name$
        print

pr2.file% = 2
if end #pr2.file%  then .28     rem no pr2 file
open  common.drive$ +":"+ system$ + "pr2.101"  as pr2.file%
if end #pr2.file%  then .29     rem invalid pr2.file
read #pr2.file%; \
%include iiypr200

close pr2.file%
goto 1                  rem same as if chained from root

.28 rem------ here if no pr2 file -------------
print tab(5);bell$;emsg$(13)
chain "PARTFILE"        rem error exit

.29 rem----- invalid pr2.file --------------------
print tab(5);bell$;emsg$(10)
goto 999.1                      rem error exit

.38 rem------ here if no parameter file -------------
print tab(5);bell$;emsg$(01)
goto 999.1              rem exit paragraph

.39 rem----- invalid parameter file --------------
print tab(5);bell$;emsg$(16)
goto 999.1                      rem error exit

1 rem----- here if chained from root ----------------------
if pr1.bell.used% then bell$=chr$(7) \
                  else bell$=null$
if common.drive$=null$  then \
        print tab(5);bell$;emsg$(14): \
        goto 999.1                      rem error exit
if fn.edit.date%(command$)  then \
        common.date$=fn.date.in$

1.02 rem----- get common date ------------------------
if common.date$=null$  then \
        common.date$ = fn.get.date$("TODAY'S")
if cr%  then  \
        print tab(5);bell$;emsg$(15) :goto 1.02  rem get common date
if stopit%  then   999.2        rem operator requested exit

%include fiymenu
%list

rem----- pick up any error return ---------------
if common.return.code% <> 0 and common.msg$<>null$  then \
        print using "&";bell$;fn.crt.msg$(common.msg$)
if common.return.code% = 2 and common.msg$=null$  then \
        print using "&";fn.crt.msg$(emsg$(17))
if common.return.code% = 1 and common.msg$=null$  then \
        print using "&";bell$;fn.crt.msg$(emsg$(18))
common.msg$=null$
common.return.code%=0

rem----- data -----------------------------
submit.file% = 1
sorts% = 1
programs% = 12
option.max% = sorts% + programs%
end$ = chr$(0) + chr$ (24h)

if common.option% > 0 and common.option% <= option.max%  then \
        trash%=fn.crt.display.data%(">", common.option%)

rem----- main driver loop --------------------------
while true%
        gosub 60        rem fn.crt.input
        if crt.end.char% <> valid.data%  \
                then gosub 10   \check control responses
                else gosub 20   rem edit response
wend

10 rem----- check control responses ------------------
if crt.end.char%=ctlr%  then \
        x% = fn.crt.display.background%: return
if crt.end.char%=escape%  then 999              rem end of program

print using "&";bell$; fn.crt.msg$(emsg$(12))
return

20 rem----- edit responses ------------------------
num%=fn.num%(in$)
if not num%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(12)): return
common.option%=val(in$)
if common.option% < 1  or common.option% > option.max%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(12)): return
trash%=fn.crt.display.data%(">", common.option%)
print using "&";fn.crt.msg$(null$)
on common.option%  gosub \
        100,105,        \add to, deplete inventory
        110,            \transaction proof
        120,            \reorder report
        130,            \inventory value report
        140,145,        \activity report, accumulator update
        150,155,        \parameter entry, sort parameter entry
        160,            \part entry
        1001,           \sort part file
        165,            \part file print
        170             rem recopy part files
gosub 65        rem clear data

return

60 rem----- fn.crt.input ---------------------------
in$=fn.crt.input$(option.max%+1)
gosub 65                rem clear data
print using "&";fn.crt.msg$(null$)
return

65 rem----- clear data ------------------------
trash%=fn.crt.clear.data%
return

999    rem-----normal end of job---------------
print using "&";crt.clear$
print:print:print
print tab(10);program$+" COMPLETED"
print:print:print
stop
999.1  rem-----abnormal end of job-------------
print:print:print
print tab(10);program$+" COMPLETED UNSUCCESSFULLY"
print tab(10);system.name$ + " TERMINATING"
print:print:print:print bell$
stop
999.2  rem-----premature end of job------------
print:print:print
print tab(10);program$+" ENDING PREMATURELY"
print:print:print
stop

100 rem----- additions to inventory------
if pr2.part.file.sort.needed%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(09)): return
if size("ADDITION.INT") <> 0 then \
        chain "ADDITION"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
105 rem----- DEPLETE OF inventory-
if pr2.part.file.sort.needed%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(09)): return
if size("DEPLETE.INT") <> 0 then \
        chain "DEPLETE"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
110 rem----- proof of transactions --------------
if not pr1.any.audit.used%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(19)): RETURN
if size("PROOF.INT") <> 0 then \
        chain "PROOF"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
120 rem----- reorder report -----
if pr2.part.file.sort.needed%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(09)): RETURN
if size("REORDER.INT") <> 0 then \
        chain "REORDER"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
130 rem----- value report ------------
if pr2.part.file.sort.needed%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(09)): RETURN
if size("VALUE.INT") <> 0 then \
        chain "VALUE"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
140 rem----- activity report -----
if pr2.part.file.sort.needed%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(09)): RETURN
if size("ACTIVITY.INT") <> 0 then \
        chain "ACTIVITY"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
145 rem----- update accumulators -------
if pr2.part.file.sort.needed%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(09)): RETURN
if size("UPDATE.INT") <> 0 then \
        chain "UPDATE"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
150 rem----- parameter entry ----------
if size("IYPARENT.INT") <> 0 then \
        chain "IYPARENT"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
155 rem----- SORT parameter file creation ------------
if size("SORTPARM.INT") <> 0 then \
        chain "SORTPARM"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
160 rem----- part entry -------------
if size("PARTENT.INT") <> 0 then \
        chain "PARTENT"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
165 rem----- part print -------------
if size("PARTPRNT.INT") <> 0 then \
        chain "PARTPRNT"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return
170 rem----- squash ----------
if pr2.part.file.sort.needed%  then \
        print using "&";bell$;fn.crt.msg$(emsg$(09)): RETURN
if size("PARTFILE.INT") <> 0 then \
        chain "PARTFILE"
print using "&"; bell$;fn.crt.msg$(emsg$(05))
return

REM----- SORTS ------------------------
REM------------------------------------
1001 rem----- part file sort ----------
if size("QSORT.COM") = 0  then \
        print using "&";bell$;fn.crt.msg$(emsg$(11)): RETURN
if size(common.drive$ + ":" + "PART1.SRT") = 0  then \
        print using "&";bell$; fn.crt.msg$(emsg$(06)) : return
gosub 10000	rem create submit file
if sub.eof%  then \
        sub.eof%=false%: RETURN
vob.srt$ = "QSORT " + common.drive$ + ":" + "PART1"
if end #submit.file%  then 1009
print using "&";#submit.file% ; chr$(len(vob.srt$)) + vob.srt$ + end$
close submit.file%
print using "&"; crt.clear$
stop
1009 REM----- END OF FILE WHEN WRITING LAST LINE OF SUBMIT -----------
print using "&";bell$;fn.crt.msg$(emsg$(04))
close submit.file%
RETURN

10000 rem----- create submit file --------------------------------
if end #submit.file%  then 10090
create "A:$$$.SUB"  recl 80H  as submit.file%
run.menu$ = "CRUN2 "+system$+" " + fn.date.out$(common.date$)
if end #submit.file%  then 10091
print using "&"; #submit.file% ; chr$(len(run.menu$)) + run.menu$ + end$
return
10090 rem----- here if eof on submit file create -----------------
print using "&";fn.crt.msg$(emsg$(03))
sub.eof%=true%
RETURN
10091 rem----- here if eof on submit file build -----------------
print using "&";bell$;fn.crt.msg$(emsg$(07))
close submit.file%
sub.eof%=true%
RETURN

