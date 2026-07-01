%include iiycomm
prgname$="IYPARENT  OCT  18,1979 "
rem---------------------------------------------------------
rem
rem       I N V E N T O R Y
rem
rem       I  Y  P  A  R  E  N  T
rem
rem   COPYRIGHT (C) 1979-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="IYPARENT"

dim emsg$(20)
emsg$(01)="IY201  THIS PROGRAM MUST BE RUN FROM THE IY MENU"
emsg$(02)="IY202  INVALID INPUT"
emsg$(03)="IY203"
emsg$(04)="IY204  INVALID DRIVE SPECIFIED"
emsg$(05)="IY205"
emsg$(06)="IY206  NO PARAMETER FILE. WILL CREATE DEFAULT FILE BEFORE CONTINUING"
emsg$(07)="IY207  UNEXPECTED END OF PARAMETER FILE"
emsg$(08)="IY208"
emsg$(09)="IY209"
emsg$(10)="IY210"
emsg$(11)="IY211"
emsg$(12)="IY212"
emsg$(13)="IY213"
emsg$(14)="IY214"
emsg$(15)="IY215"
emsg$(16)="IY216"
emsg$(17)="IY217"
emsg$(18)="IY218"
emsg$(19)="IY219"
emsg$(20)="IY220"

%nolist%        rem include b:zdms
%include zdms
%list
%include zdmschar
%include iiyconst
%include znumeric
%include zparse
%include zinput
%include zgetdate
%include zsysdriv
%include zdrive
%include zserial

if not chained.from.root%  then \
        print tab(5);bell$;emsg$(01) :\
        goto 999.1

common.drive$=fn.get.sys.drive$
pr1.file% = 1
if common.drive$=null$  then \
        print tab(5);bell$;emsg$(06):print: \
        gosub  1000                     rem create default files
if end #pr1.file%  then .009    rem unexpected end of file
goto .01

.009 rem----- unexpected end of file -----------
print tab(5);bell$;emsg$(07): goto 999.1        rem error exit

.01 rem----- here if parameter file exists --------
open  common.drive$ +":"+ system$ + "pr1.101"  as pr1.file%
read #pr1.file%; \
%include iiypr100

close pr1.file%
if pr1.bell.used% then bell$=chr$(7)

selection.max%=2
a$="&"
if common.date$=null$  then display.date$=left$(blank$, 8) \
                       else display.date$=fn.date.out$(common.date$)

gosub 640                       rem init primary menu

rem----- main program driver -------------------
while not end.wanted%
        option%=1
        gosub 600                       rem fn.crt.input
        selection%=0
        if crt.end.char% = valid.data% \
                then  gosub 7   \ edit user selection
                else  gosub 100 rem check control responses
        done%=false%
        if selection% > 0 and  selection% <= selection.max%  then \
                on selection%  gosub \
                        10,     \general parameters
                        30:     \  audit parameters
                gosub 655:      \  set arrays to null
                gosub 640       rem redisplay menu
wend

if end #pr1.file%  then .009    rem unexpected end of parameter file
open  common.drive$ +":"+ system$ + "pr1.101"  as pr1.file%
print #pr1.file%; \
%include iiypr100
close pr1.file%
print using "&";crt.clear$

if system.startup%  then \
        chain "PARTFILE"

%include zeoj

7 rem----- edit user selection -------------------------
num%=fn.num%(in$)
if not num%  then \
        print using a$;bell$+fn.crt.msg$(emsg$(02)): return
selection%=val(in$)
if selection% < 1 or selection% > selection.max%  then \
        print using a$;bell$+fn.crt.msg$(emsg$(02)): \
        selection%=0
return

10 rem----- general options -----------------------------
gosub 655               rem init screen buffer
rem include of background display
%include fiyparm1
%list
gosub 661               rem display general data
if pr1.debugging%  then \
        print using a$;fn.crt.msg$("BYTES FREE "+str$(fre))

option%=1
10.00 rem----- loop thru parameters
while not done%         rem done set to true by 200
        gosub 600
        if crt.end.char%<>valid.data% \
                then gosub 200          \secondary control characters
                else on option% gosub   \
                        10.0,           \company name
                        11.0,           \current period
                        12.0,           \to date period
                        13.0,           \date form
                        14.0,           \page width
                        15.0,           \lines per page
                        16.0,           \average valuation
                        17.0,           \array size
                        18.0,           \bell used
                        19.0:           \debugging
                        gosub 620       rem display data
        if not invalid.data%  then \
                option% = option%+1
        if option% > crt.field.count%  then \
                option% = 1
        if option% < 1  then \
                option% = crt.field.count%
wend
return

10.0 rem----- company name ------------------
invalid.data% = false%
pr1.co.name$ = in$
return

11.0 rem----- current period ----------------
invalid.data% = false%
in$=ucase$(in$)
if in$="WEEK"  or in$="MONTH"  or in$="QUARTER"  then \
        pr1.current.period$=in$: return
invalid.data%=true%
in$=pr1.current.period$
print using a$;bell$+fn.crt.msg$(emsg$(02))
return

12.0 rem----- to date period -----------------
invalid.data%=false%
in$=ucase$(in$)
if in$="MONTH"  or in$="QUARTER" or in$="YEAR"  then \
        pr1.to.date.period$=in$: return
invalid.data%=true%
in$=pr1.to.date.period$
print using a$;bell$+fn.crt.msg$(emsg$(02))
return

13.0 rem----- date form ------------------
invalid.data%=false%
if in$="1"  then \
        pr1.date.mo%=1: pr1.date.dy%=2: pr1.date.yr%=3: \
        return
if in$="2"  then \
        pr1.date.mo%=2: pr1.date.dy%=1: pr1.date.yr%=3: \
        return
invalid.data%=true%
print using a$;fn.crt.msg$(emsg$(02))
in$=str$(pr1.date.mo%)
return

14.0 rem------ page width -----------
invalid.data%=false%
digits%=3
gosub 300       rem fn.num
if num%  then \
        pr1.page.width%=in.num: return
invalid.data%=true%
in$=str$(pr1.page.width%)
print using a$;bell$+fn.crt.msg$(emsg$(02))
return

15.0 rem------ lines per page -----------
invalid.data%=false%
digits%=3
gosub 300       rem fn.num
if num%  then \
        pr1.lines.per.page%=in.num: return
invalid.data%=true%
in$=str$(pr1.lines.per.page%)
print using a$;bell$+fn.crt.msg$(emsg$(02))
return

16.0 rem----- average valuation ---------
invalid.data%=false%
in$=ucase$(in$)
if in$="Y"  then \
        pr1.average.used%=true%: return
if in$="N"  then \
        pr1.average.used%=false%: return
invalid.data%=true%
print using a$;bell$+fn.crt.msg$(emsg$(02))
if pr1.debugging% \
        then in$="Y" \
        else in$="N"
return

17.0 rem----- array size --------------------------------
invalid.data%=false%
digits%=4
gosub 300               rem fn.num
if num%  then \
        pr1.array.size%=in.num: return
invalid.data%=true%
in$=str$(pr1.array.size%)
print using a$;bell$+fn.crt.msg$(emsg$(02))
return

18.0 rem----- bell used -----------------
invalid.data%=false%
in$=ucase$(in$)
if in$="Y"  then \
        pr1.bell.used%=true%: return
if in$="N"  then \
        pr1.bell.used%=false%: return
invalid.data%=true%
print using a$;bell$+fn.crt.msg$(emsg$(02))
if pr1.bell.used% \
        then in$="Y" \
        else in$="N"
return

19.0 rem----- debugging -----------------
invalid.data%=false%
in$=ucase$(in$)
if in$="Y"  then \
        pr1.debugging%=true%: return
if in$="N"  then \
        pr1.debugging%=false%: return
invalid.data%=true%
print using a$;bell$+fn.crt.msg$(emsg$(02))
if pr1.debugging% \
        then in$="Y" \
        else in$="N"
return

30 rem----- audit parameters -------------------------------
gosub 655               rem init screen buffer
rem include for screen format
%include fiyparm2
%list
gosub 663               rem display data
option%=1
while not done%
        gosub 600               rem fn.crt.input
        if crt.end.char% <> valid.data% \
                then gosub 200          \secondary control characters
                else on option%  gosub  \
                        30.0,           \audit drive
                        31.0,           \additions audit
                        32.0:           \depletions audit
                        gosub 620       rem display data
        if not invalid.data%  then \
                option%=option%+1
        if option%>crt.field.count%  then \
                option%=1
        if option%<1  then \
                option%=crt.field.count%
wend
if pr1.additions.audit.used% or pr1.depletions.audit.used% or \
        pr1.start.job.audit.used% or pr1.start.job.audit.summary.used% or \
        pr1.end.job.audit.used%  or pr1.end.job.audit.summary.used% \
                then pr1.any.audit.used%=true% \
                else pr1.any.audit.used%=false%
return

30.0 rem----- audit drive ---------------------
invalid.data% = false%
in$=ucase$(in$)
if in$>="A"  and in$<="Z"  then \
        pr1.audit.drive$=in$: return
invalid.data%=true%
print using a$;bell$+fn.crt.msg$(emsg$(02))
in$=pr1.audit.drive$
return
31.0 rem----- additions audit used -----------------
invalid.data%=false%
in$=ucase$(in$)
if in$="Y"  then \
        pr1.additions.audit.used%=true%: return
if in$="N"  then \
        pr1.additions.audit.used%=false%: return
invalid.data%=true%
print using a$;bell$+fn.crt.msg$(emsg$(02))
if pr1.additions.audit.used% \
        then in$="Y" \
        else in$="N"
return
32.0 rem----- depletions audit used ------------------
invalid.data%=false%
in$=ucase$(in$)
if in$="Y"  then \
        pr1.depletions.audit.used%=true%: return
if in$="N"  then \
        pr1.depletions.audit.used%=false%: return
invalid.data%=true%
print using a$;bell$+fn.crt.msg$(emsg$(02))
if pr1.depletions.audit.used% \
        then in$="Y" \
        else in$="N"
return
33.0 rem----- start job audit used ----------------------
invalid.data%=false%
in$=ucase$(in$)
if in$="Y"  then \
        pr1.start.job.audit.used%=true%: \
        pr1.start.job.audit.summary.used%=false%: return
if in$="N"  then \
        pr1.start.job.audit.used%=false%: \
        pr1.start.job.audit.summary.used%=false%: return
if in$="S"  then \
        pr1.start.job.audit.used%=false%: \
        pr1.start.job.audit.summary.used%=true%: return
invalid.data%=true%
print using a$;bell$+fn.crt.msg$(emsg$(02))
if pr1.start.job.audit.summary.used%  then \
        in$="S": RETURN
if pr1.start.job.audit.used% \
        then in$="Y" \
        else in$="N"
return
34.0 rem----- end job audit -------------
invalid.data%=false%
in$=ucase$(in$)
if in$="Y"  then \
        pr1.end.job.audit.used%=true%: \
        pr1.end.job.audit.summary.used%=false%: return
if in$="N"  then \
        pr1.end.job.audit.used%=false%: \
        pr1.end.job.audit.summary.used%=false%: return
if in$="S"  then \
        pr1.end.job.audit.used%=false%: \
        pr1.end.job.audit.summary.used%=true%: return
invalid.data%=true%
print using a$;fn.crt.msg$(emsg$(02))
if pr1.end.job.audit.summary.used%  then \
        in$="S": RETURN
if pr1.end.job.audit.used% \
        then in$="Y" \
        else in$="n"
return

100 rem----- primary controls -----------------------------
if crt.end.char% = ctlr%  then \
        gosub 630: return       rem redisplay screen
if crt.end.char% = escape%  then \
        end.wanted%=true%: return
print using a$;fn.crt.msg$(emsg$(02))
return

200 rem----- secondary control characters -------
invalid.data%=true%
if crt.end.char%=return%  then option%=option%+1: return
if crt.end.char%=ctlb%  then option%=option%-1: return
if crt.end.char%=ctlr%  then gosub 630: return          rem refresh screen
if crt.end.char%=escape%  then done%=true%: return
print using a$;bell$+fn.crt.msg$(emsg$(02))
return

300 rem----- fn.num ----------------------
num%=fn.num%(in$)
in.num=val(in$)
return

310 rem----- fn.numeric -------------------
numeric%=fn.numeric%(in$,left.digits%,right.digits%)
if not numeric%  then return
in.numeric=val(in$)
return

600 rem----- fn.crt.input -----------------
in$=fn.crt.input$(option%)
print using a$;fn.crt.msg$(null$)
return

620 rem----- display in$ -----------------
trash%=fn.crt.display.data%(in$,option%)
return

630 rem----- refresh screen -------------------
trash%=fn.crt.display.background%
trash%=fn.crt.refresh.data%
return

640 rem----- load primary menu ------------------
%include fiyparm0
%list
return

655 rem----- set arrays to null -------------------
for crt.loop%=1 to crt.buffer.count%
        crt.screen.buffer$(crt.loop%)=null$
next
for crt.loop%=1 to crt.field.count%
        crt.buffer$(crt.loop%)=null$
next
return

661 rem----- display general parameters ----------------

trash%=fn.crt.display.data%(pr1.co.name$,1)
trash%=fn.crt.display.data%(pr1.current.period$,2)
trash%=fn.crt.display.data%(pr1.to.date.period$,3)
trash%=fn.crt.display.data%(str$(pr1.date.mo%),4)
trash%=fn.crt.display.data%(str$(pr1.page.width%),5)
trash%=fn.crt.display.data%(str$(pr1.lines.per.page%),6)
if pr1.average.used%  \
        then x$="Y"  \
        else x$="N"
trash%=fn.crt.display.data%(x$,7)
trash%=fn.crt.display.data%(str$(pr1.array.size%),8)
if pr1.bell.used%  \
        then x$="Y" \
        else x$="N"
trash%=fn.crt.display.data%(x$,9)
if pr1.debugging%  \
        then x$="Y" \
        else x$="N"
trash%=fn.crt.display.data%(x$,10)
return

663 rem----- DISPLAY AUDIT PARAMETERS ----------------
trash%=fn.crt.display.data%(pr1.audit.drive$,1)
if pr1.additions.audit.used% \
        then x$="Y" \
        else x$="N"
trash%=fn.crt.display.data%(x$,2)
if pr1.depletions.audit.used% \
        then x$="Y" \
        else x$="N"
trash%=fn.crt.display.data%(x$,3)
return

rem--if pr1.start.job.audit.summary.used%  then \
rem--   x$="S"
rem--if pr1.start.job.audit.used% \
rem--   then x$="Y"
rem--if not pr1.start.job.audit.used%  and  not pr1.start.job.audit.summary.used% \
rem--   then x$="N"
rem--trash%=fn.crt.display.data%(x$,4)
rem--if pr1.end.job.audit.summary.used%  then \
rem--   x$="S"
rem--if pr1.end.job.audit.used% \
rem--   then x$="Y"
rem--if not pr1.end.job.audit.used%  and  not pr1.end.job.audit.summary.used% \
rem--   then x$="N"
rem--trash%=fn.crt.display.data%(x$,5)
rem--return

1000 reM----- create default parameter file -----------
pr1.co.name$ = "LPE STOCK CONTROL SYSTEM"
pr1.debugging% = false%
pr1.crt.def.file$ = "CRT"
pr1.any.audit.used% = true%
pr1.additions.audit.used%  = true%
pr1.depletions.audit.used%  = true%
pr1.audit.drive$ = "B"
pr1.array.size% = 100
pr1.current.period$="MONTH"
pr1.to.date.period$="YEAR"
pr1.lines.per.page%=60
pr1.page.length%=66
pr1.page.width%=132
pr1.date.mo% = 2 :pr1.date.dy% = 1 :pr1.date.yr% = 3

1000.1 REM----- GET SYSTEM DRIVE -----------------------
x%=fn.get.drive%("SYSTEM")
if stopit%  then 999.2          rem operator requested exit
if cr% or (drive$ <> "A" and drive$ <> "B")  then \
        print tab(5);bell$;emsg$(04):\
        goto 1000.1
common.drive$=drive$
create common.drive$+":IYPR1.101"  as pr1.file%

print #pr1.file%; \
%include iiypr100

close pr1.file%

system.startup%=true%
return

