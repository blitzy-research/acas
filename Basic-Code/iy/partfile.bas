%include iiycomm
prgname$="PARTFILE  OCT. 19,1979 "
rem---------------------------------------------------------
rem
rem       I N V E N T O R Y
rem
rem       P  A  R  T  F  I  L  E
rem
rem   COPYRIGHT (C) 1979-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="PARTFILE"

%include iiyinit

dim emsg$(20)
emsg$(01)="IY531  UNEXPECTED EOF ON ITEM FILE READ"
emsg$(02)="IY532  INVALID RESPONSE"
emsg$(03)="IY533  INVALID ITEM FILE PARAMETERS"
emsg$(04)="IY534  END OF FILE ON ITEM FILE CREATE"
emsg$(05)="IY535  THAT'S NOT THE RIGHT INPUT FILE"
emsg$(06)="IY536  NO INPUT FILE FOUND ON DRIVE A"
emsg$(07)="IY537  INVALID ITEM FILE"
emsg$(08)="IY538  THAT'S NOT THE RIGHT OUTPUT FILE"
emsg$(09)="IY539  UNEXPECTED EOF ON WRITE TO ITEM FILE"
emsg$(10)="IY540  NO OUTPUT FILE FOUND"
emsg$(11)="IY541  INVALID OUTPUT FILE FOUND"
emsg$(12)="IY542  THERE IS A ITEM FILE ON THE DISK ON DRIVE B"
emsg$(13)="IY543  THERE IS NO SECOND PARAMETER FILE ON THAT DISK"
emsg$(14)="IY544  UNABLE TO CREATE ITEM FILE. IS THE DISK WRITE-PROTECTED?"
emsg$(15)="IY545  UNABLE TO WRITE TO ITEM FILE"
emsg$(16)="IY546  INVALID DATE"
emsg$(17)="IY547  UNABLE TO CREATE PR2 FILE"
emsg$(18)="IY548  NO INPUT FILE FOUND ON DRIVE A"
emsg$(19)="IY549  INVALID ITEM FILE"
emsg$(20)="IY550  INVALID ITEM FILE"

REM------------------------------------------------------------------
REM-----  I N C L U D E S  ------------------------------------------
REM------------------------------------------------------------------

%nolist
%include zdms
%list
%include zdmschar
%include iiyprt80
%include znumber
%include zparse
%include zinput
%include zgetdate

REM------------------------------------------------------------------
REM-----                                               --------------
REM------------------------------------------------------------------

a$="&"
pr2.file%=2

1 REM----- GET COMMON DATE ------------------
if common.date$=null$  then \
        common.date$=fn.get.date$("TODAY'S")
if stopit%  then  999.2                 rem premature exit
if cr%  then \
        print tab(5);bell$;emsg$(16): goto 1    rem get common date

if size(common.drive$+":IYPR2.101")=0 \
        then system.startup%=true%: gosub 8200  \create pr2
        else system.startup%=false%

if system.startup% and not  par2.created%  then  999.1          rem error exit

yes%=false%: no%=false%

while not system.startup% and not (yes% or no%)
        print:print tab(10);"DO YOU WANT TO CHANGE ITEM FILE PARAMETERS? >";
        input ""; line in$
        if in$=null$ \
                then uin$=null$ \
                else uin$=ucase$(in$)
        if uin$=stop$  or uin$=escape$  then 999.2
        if uin$="Y" or uin$="YES"  then \
                yes%=true%
        if uin$="N" or uin$="NO"  then \
                no%=true%
        if not (yes% or no%)  then \
                print:print tab(5);"ANSWER MUST BE  YES OR  NO"
wend

old.part.files%=pr2.part.files%
dim old.part.drive$(3)
dim old.lo.number$(3)
for f% = 1 to pr2.part.files%
        old.part.drive$(f%)=pr2.part.drive$(f%)
        old.lo.number$(f%)=pr2.lo.number$(f%)
next

if no%  then  squash%=true% \
        else  squash%=false%

if yes% or system.startup% \
        then gosub 20           rem part parameter loop

if system.startup%  then \
        gosub 6000                      rem create all part files
if error.during.create%  then  999.1    rem error exit

print using "&";crt.clear$

yes%=false%: no%=false%
while not system.startup% and not squash% and not (yes% or no%)
        print:print tab(10);"DO YOU WANT TO RECOPY THE ITEM FILES? >";
        input ""; line in$
        if in$=null$ \
                then uin$=null$ \
                else uin$=ucase$(in$)
        if uin$=stop$  or uin$=escape$  then 999.2
        if uin$="Y" or uin$="YES"  then \
                yes%=true%
        if uin$="N" or uin$="NO"  then \
                no%=true%
        if not (yes% or no%)  then \
                print:print tab(5);"ANSWER MUST BE  YES OR  NO"
wend

if yes%  then recopy%=true% \
         else recopy%=false%

if squash% or recopy%  then \
        gosub 2000                      rem copy all part files
if stopit%  then 19                     rem get program disk
if the.copy.blew.up%  then 19           rem get program disk

if modified%  then gosub 8500           rem update p2
if stopit% then 19              rem get program disk

19 rem----- get program disk ---------------------------
if size("IY.INT") = 0  then \
        print:print tab(10);"ENSURE THAT THE PROGRAM DISK IS ON THE CURRENTLY LOGGED DRIVE": \
        gosub 340:      \pause then initialize
        goto 19
if the.copy.blew.up% or stopit% \
        then gosub 8600                 rem restore pr2
if the.copy.blew.up%  then 999.1        rem error exit
if stopit%  then 999.2                  rem premature exit

%include zeoj

REM------------------------------------------------------------------
20 REM----- PART PARAMETER SUBROUTINE --------------------
REM------------------------------------------------------------------
gosub 660 rem load screen and display
gosub 670 rem display part parameters
no.fields%=crt.field.count%
field%=1

21 rem----- part parameter loop ----------------------
while not done%
        on field% gosub         \
                201,            \number of part files
                202,            \drive 1
                203,            \drive 2
                204,            \drive 2 low number
                205,            \drive 3
                206             rem drive 3 low number
        if field%>no.fields%  then \
                field%=1
        if field%<1  then \
                field%=no.fields%
wend
if pr2.part.files%>1  and (pr2.part.drive$(2)=pr2.part.drive$(1) \
    or pr2.lo.number$(2)<=left$(blank$,10))  then \
        done%=false%: print using a$;fn.crt.msg$(emsg$(03)): \
        goto 21                 rem part parameter loop
if pr2.part.files%=3  and (pr2.part.drive$(3)=pr2.part.drive$(2) or \
    pr2.part.drive$(3)=pr2.part.drive$(1) or \
    pr2.lo.number$(2)>=pr2.lo.number$(3))  then \
        done%=false%: print using a$;fn.crt.msg$(emsg$(03)): \
        goto 21                 rem part parameter loop
return

100 rem----- control characters -------
invalid.data%=true%
if crt.end.char%=return%  then field%=field%+1: return
if crt.end.char%=ctlb%  then field%=field%-1: return
if crt.end.char%=ctlr%  then gosub 630: return          rem refresh screen
if crt.end.char%=escape%  then done%=true%: return
print using a$;fn.crt.msg$(emsg$(02))
return

201 rem----- number of part files --------------------
gosub 600       rem get crt input
if crt.end.char%<>valid.data%  then  gosub 100: return
gosub  300              rem fn.num
if not num%  or in.num > 3 or in.num < 1  then \
        print using a$;fn.crt.msg$(emsg$(02)): \
        gosub 621: \
        return
if in.num = pr2.part.files%  then \
        print using a$;fn.crt.msg$("NOTHING CHANGED"): return
pr2.part.files%=in.num
modified%=true%
if pr2.part.files% < 3  then \
        pr2.part.drive$(3)=null$: pr2.lo.number$(3)=null$: \
        gosub 625: gosub 626
if pr2.part.files% < 2  then \
        pr2.part.drive$(2)=null$: gosub 623: \
        pr2.lo.number$(2)=null$: gosub 624
field%=field%+1
return

202 rem----- part drive 1 -------------------------------
gosub 600
if crt.end.char%<>valid.data%  then \
        gosub 100: return
in$=ucase$(in$)
if in$<"A"  or in$>"Z"  then \
        print using a$;fn.crt.msg$(emsg$(02)): \
        gosub 622: return
modified%=true%
pr2.part.drive$(1)=in$
gosub 622
field%=field%+1
return

203 rem----- part drive 2 ---------------------
if pr2.part.files%=1 and crt.end.char%=ctlb%  then field%=field%-1: return
if pr2.part.files%=1  then field%=field%+1: return
gosub 600
if crt.end.char%<>valid.data%  then \
        gosub 100: return
in$=ucase$(in$)
if in$<"A"  or in$>"Z"  then \
        print using a$;fn.crt.msg$(emsg$(02)): \
        gosub 623: return
modified%=true%
pr2.part.drive$(2)=in$
gosub 623
field%=field%+1
return

204 rem----- part file 2 low number -------------------------
if pr2.part.files%=1 and crt.end.char%=ctlb%  then field%=field%-1: return
if pr2.part.files%=1  then field%=field%+1: return
gosub 600       rem fn.input
if crt.end.char%<>valid.data%  then \
        gosub 100: return
gosub  320              rem check part number
if part.invalid%  then \
        print using a$;fn.crt.msg$(emsg$(02)): \
        gosub 624: return
modified%=true%
pr2.lo.number$(2)=new.part$
gosub 624
field%=field%+1
return

205 rem----- part drive 3 ---------------------
if pr2.part.files%<3 and crt.end.char%=ctlb%  then field%=field%-1: return
if pr2.part.files%<3  then field%=field%+1: return
gosub 600
if crt.end.char%<>valid.data%  then \
        gosub 100: return
in$=ucase$(in$)
if in$<"A"  or in$>"Z"  then \
        print using a$;fn.crt.msg$(emsg$(02)): \
        gosub 625: return
modified%=true%
pr2.part.drive$(3)=in$
gosub 625
field%=field%+1
return

206 rem----- part file 3 low number -------------------------
if pr2.part.files%<3 and crt.end.char%=ctlb%  then field%=field%-1: return
if pr2.part.files%<3  then field%=field%+1: return
gosub 600
if crt.end.char%<>valid.data%  then \
        gosub 100: return
gosub  320              rem check part number
if part.invalid%  then \
        print using a$;fn.crt.msg$(emsg$(02)): \
        gosub 626: return
modified%=true%
pr2.lo.number$(3)=new.part$
gosub 626
field%=field%+1
return

300 rem----- fn.num ----------------------
num%=fn.num%(in$)
in.num=val(in$)
return

320 rem----- part number -------------------
%include iiyprtno

340 rem----- pause then initialize --------------
input "          THEN PRESS RETURN >";line in$
if in$<>null$  then \
        in$=ucase$(in$)
if in$=stop$ or in$=escape$  then \
        stopit%=true%: return
initialize
return

600 rem----- fn.crt.input -----------------
in$=fn.crt.input$(field%)
print using a$;fn.crt.msg$(null$)
return

621 rem----- display number of part files --------------
trash%=fn.crt.display.data%(str$(pr2.part.files%),1)
return
622 rem----- display part drive 1 --------------
trash%=fn.crt.display.data%(pr2.part.drive$(1),2)
return
623 rem----- display part drive 2 --------------
trash%=fn.crt.display.data%(pr2.part.drive$(2),3)
return
624 rem----- display part file two low number ----------
trash%=fn.crt.display.data%(pr2.lo.number$(2),4)
return
625 rem----- display part file three --------------
trash%=fn.crt.display.data%(pr2.part.drive$(3),5)
return
626 rem----- display part file three low number --------
trash%=fn.crt.display.data%(pr2.lo.number$(3),6)
return

630 rem----- refresh screen -------------------
trash%=fn.crt.display.background%
trash%=fn.crt.refresh.data%
return

660 rem----- load screen and display -------------------
%include fiyfile
return

670 rem----- display part file parameters -------------
gosub 621
gosub 622
gosub 623
gosub 624
gosub 625
gosub 626
return

rem------------------------------------------------------------------
2000 rem----- copy all part files ----------------------
rem------------------------------------------------------------------
in.file%=3: out.file%=4: new.rec%=0: first.time.thru%=true%
part.limit$=null$
dim part.records%(old.part.files%)
dim high.part.number$(pr2.part.files%)

print:print
print tab(15);"THE ITEM FILES WILL BE COPIED IN TURN FROM DRIVE A"
print tab(15);"ONTO DRIVE B. PLEASE BE CAREFUL TO CHANGE DISKS"
print tab(15);"EXACTLY AS SPECIFIED BY THE PROMPTS."
print:print
for in.ptr%=1 to old.part.files%
        A.msg$="PLACE THE OLD ITEM FILE THAT RAN ON DRIVE "+ \
                old.part.drive$(in.ptr%)+" ON DRIVE A"
        if first.time.thru% \
                then out.ptr%=1: \
                     B.msg$="PLACE A NEW DISK ON DRIVE B": \
                     gosub 2200 \       rem open input,create output files
                else close out.file%: \
                     close in.file%: \
                     B.msg$="DO NOT CHANGE THE DISK ON DRIVE B": \
                     gosub 2400         rem open the input,output files
        if stopit% or the.copy.blew.up%  then return
        first.time.thru%=false%
        part.rec%=2
        while part.rec% <= part.records%(in.ptr%)+1
                read #in.file%,part.rec%;\
%include iiyprt00
                if prt.number$ >= part.limit$  then \
                        close in.file%: \
                        gosub 2700: \                   rem close output file
                        out.ptr%=out.ptr%+1: \
                        A.msg$="DO NOT CHANGE THE DISK ON DRIVE A": \
                        B.msg$="PLACE A NEW DISK ON DRIVE B": \
                        gosub 2200                      rem create output file
                if stopit% or the.copy.blew.up%  then return
                if prt.number$<=high.part.number$(out.ptr%) and \
                               not prt.deleted% then \
                        close in.file%: close out.file%: \
                        print tab(5);bell$;emsg$(20): \
                        common.msg$=emsg$(20): \
                        the.copy.blew.up%=true%: \
                        return
                if not prt.deleted%  then \
                        high.part.number$(out.ptr%)=prt.number$: \
                        new.rec%=new.rec%+1: \
                        print #out.file%, new.rec%; \
%include iiyprt00
                part.rec%=part.rec%+1
        wend
next in.ptr%

gosub 2700              rem close last part file
return

2090 rem----- unexpected eof on part file read -----------------
print tab(5);bell$;emsg$(01)
close in.file%
close out.file%
the.copy.blew.up%=true%
common.msg$=emsg$(01)
return

2091 rem----- unexpected eof on write to part file -----------------
close in.file%
close out.file%
print tab(5);bell$;emsg$(09)
the.copy.blew.up%=true%
common.msg$=emsg$(09)
return

2200 rem----- open a part file for read, create a part file --------
print:
print tab(10);"THE ITEM FILE THAT WILL RUN ON DRIVE "; \
        pr2.part.drive$(out.ptr%);" WILL BE BUILT ON DRIVE B"
print tab(10);a.msg$
print tab(10);b.msg$
gosub 340       rem pause then initialize
if stopit%  then return

rem----- open a part file for read ------------------------------
if end #in.file%  then 2290
open "A:IYPRT.101" \
        recl    part.recl%      \
        as      in.file%        \
        buff    part.buff%      \
        recs    sector.len%
if end #in.file%  then 2291
read #in.file%; \
%include iiyprt90

if prt.drive$ <> old.part.drive$(in.ptr%)  then \
        print tab(5);bell$;emsg$(05): \
        close in.file%: goto 2200

part.records%(in.ptr%)=prt.no.recs%

rem----- create a part file on drive b ----------------------
prt.drive$=pr2.part.drive$(out.ptr%)
prt.last.update$="RECOPY"
prt.high.prt.no$=""
prt.no.recs%=0
prt.deleted.recs%=0
if size("B:IYPRT.*") <> 0 \
        then print tab(5);bell$;emsg$(12): \
        close in.file%: \
        goto 2200
if end #out.file%  then 2292
create "B:IYPRT.100" \
        recl    part.recl% \
        as      out.file%  \
        buff    part.buff% \
        recs    sector.len%
if end #out.file%  then 2293
print #out.file%; \
%include iiyprt90
if out.ptr%=pr2.part.files% \
        then  part.limit$="zzzzzzzzzz" \
        else  part.limit$=pr2.lo.number$(out.ptr%+1)
new.rec%=1

rem ----- set eof for copy loop -----------------------
if end #out.file%  then 2091
if end #in.file%  then 2090
return

2290 rem----- no input part file ------------------------------
print tab(5);bell$;emsg$(06)
goto 2200

2291 rem----- no input part file header ------------------------------
print tab(5);bell$;emsg$(07)
close in.file%
the.copy.blew.up%=true%
common.msg$=emsg$(07)
return

2292 rem----- end of file on create --------------------------
print tab(5);bell$;emsg$(14)
close in.file%
goto 2200

2293 rem----- end of file on header write -----------------------
print tab(5);bell$;emsg$(15)
close in.file%
close out.file%
the.copy.blew.up%=true%
common.msg$=emsg$(15)
return

rem------------------------------------------------------------------
2400 rem----- open part files for write, read -----------------------
rem------------------------------------------------------------------
print:print tab(10);a.msg$
print tab(10);b.msg$
gosub 340       rem pause then initialize
if stopit%  then return

rem----- open a part file for read ------------------------------
if end #in.file%  then 2490
open "A:IYPRT.101" \
        recl    part.recl%      \
        as      in.file%        \
        buff    part.buff%      \
        recs    sector.len%
if end #in.file%  then 2491
read #in.file%; \
%include iiyprt90

if prt.drive$ <> old.part.drive$(in.ptr%)  then \
        print tab(5);bell$;emsg$(05): \
        close in.file%: goto 2400

part.records%(in.ptr%)=prt.no.recs%

rem----- open output file for write ------------------------------
if end #out.file%  then  2492
open "B:IYPRT.100" \
        recl    part.recl%      \
        as      out.file%       \
        buff    part.buff%      \
        recs    sector.len%
if end #out.file%  then 2493
read #out.file%; \
%include iiyprt90

if prt.drive$ <> pr2.part.drive$(out.ptr%)  or \
    prt.last.update$<>"RECOPY" then \
        print tab(5);bell$;emsg$(08): \
        close out.file%: close in.file%: goto 2400

rem ----- set eof for copy loop ----------------------------
if end #in.file%  then 2090
if end #out.file% then 2091
return

2490 rem----- no input part file ------------------------------
print tab(5);bell$;emsg$(18)
goto 2400

2491 rem----- no input part file header ------------------------------
print tab(5);bell$;emsg$(19)
close in.file%
the.copy.blew.up%=true%
common.msg$=emsg$(19)
return

2492 rem----- no part file ------------------------------
print tab(5);bell$;emsg$(10)
close in.file%
goto 2400

2493 rem----- no part file header ------------------------------
print tab(5);bell$;emsg$(11)
close out.file%
close in.file%
the.copy.blew.up%=true%
common.msg$=emsg$(11)
return

rem------------------------------------------------------------
2700 rem----- close and rename part files ---------------------
rem------------------------------------------------------------
prt.no.recs%=new.rec%-1
prt.deleted.recs%=0
prt.drive$=pr2.part.drive$(out.ptr%)
prt.high.prt.no$=high.part.number$(out.ptr%)
prt.last.update$=common.date$
print #out.file%, 1; \
%include iiyprt90
close out.file%
trash%=rename("B:IYPRT.101","B:IYPRT.100")
print
print tab(10);"THE NEW ITEM FILE THAT WILL RUN ON DRIVE "; \
   pr2.part.drive$(out.ptr%);" IS NOW COMPLETE"
print
RETURN

REM------------------------------------------------------------------
6000 REM----- CREATE ALL PART FILES -------------------------------
REM------------------------------------------------------------------
print using a$;fn.crt.msg$("CHECK FOR ITEM FILES")
part.file.created%=false%
prt.last.update$=common.date$
for f% = 1 to pr2.part.files%
        prt.drive$ = pr2.part.drive$(f%)
        if size(prt.drive$+part.f.name$+"*") <> 0   then 50.01 rem next
        print using a$;fn.crt.msg$("ITEM FILE BEING CREATED ON DRIVE " \
                +prt.drive$)
        if end #f%  then  50.02
        create prt.drive$+part.f.name$+"101" \
                recl    part.recl%      \
                as      f%              \
                buff    part.buff%      \
                recs    sector.len%
        print #f%; \
%include iiyprt90

        part.file.created%=true%
        close f%

50.01 rem----- next part file -----------------------
next
if not part.file.created%  then \
        print using a$;fn.crt.msg$("ALL ITEM FILES PRESENT")
for f%= 1 to 100: next
return

50.02 rem----- eof on create ------------------------
print using a$;fn.crt.msg$(emsg$(04))
error.during.create%= true%
common.msg$=emsg$(04)
return

rem------------------------------------------------------------------
8200 rem----- create default parameter file -----------
rem------------------------------------------------------------------
dim pr2.part.drive$(3)
dim pr2.lo.number$(3)
pr2.part.files%=1
pr2.part.drive$(1)="B"
pr2.part.drive$(2)=null$
pr2.part.drive$(3)=null$
pr2.lo.number$(2)=null$
pr2.lo.number$(3)=null$
pr2.audit.number%=0
pr2.activity.report.run%=0
pr2.part.file.sort.needed%=0
pr2.last.update$=common.date$

par2.created%=false%

if end #pr2.file%  then 8209         rem eof on pr2 create
create common.drive$+":IYPR2.101" as pr2.file%
print #pr2.file%; \
%include iiypr200

close pr2.file%
par2.created%=true%
return

8209 rem----- eof on pr2 create -------------------------
print tab(5);bell$;emsg$(17)
common.msg$=emsg$(17)
return

rem------------------------------------------------------------------
8500 rem----- update parameter file ---------------------
rem------------------------------------------------------------------
if size(common.drive$+":IYPR2.101") = 0  then \
    print: \
    print tab(10);"ENSURE THAT THE SYSTEM DISK IS IN DRIVE ";common.drive$:\
    gosub 340   rem pause then initialize
if stopit%  then RETURN
pr2.file%=2
if end #pr2.file%  then 8509
open common.drive$+":IYPR2.101"  as pr2.file%
print #pr2.file%; \
%include iiypr200
close pr2.file%
RETURN

8509 REM----- PARAMETER FILE NOT FOUND --------------------------
print tab(5);bell$;emsg$(13)
goto 8500

8600 REM----- RESTORE PR2 FILE --------
for f%= 1 to 3
        pr2.part.drive$(f%)= old.part.drive$(f%)
        pr2.lo.number$(f%)=  old.lo.number$(f%)
next
pr2.part.files%= old.part.files%
RETURN

