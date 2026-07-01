%include iiycomm
prgname$="PARTENT  OCT. 19,1979 "
rem---------------------------------------------------------
rem
rem       I N V E N T O R Y
rem
rem       P  A  R  T  E  N  T
rem
rem   COPYRIGHT (C) 1979-2009, Applewood Computers
rem
rem---------------------------------------------------------

program$="PARTENT"

%include iiyinit

dim emsg$(30)
emsg$(01)="IY101  ITEM FILE FOUND FROM ABORTED RUN"
emsg$(02)="IY102  ITEM FILE NOT FOUND"
emsg$(03)="IY103  ITEM FILE MOUNTED ON WRONG DRIVE"
emsg$(04)="IY104  UNEXPECTED END OF FILE ON ITEM FILE"
emsg$(05)="IY105"
emsg$(06)="IY106  RENAME FAILED"
emsg$(07)="IY107  A QUOTE IS AN INVALID CHARACTER"
emsg$(08)="IY108  INVALID ITEM NUMBER"
emsg$(09)="IY109  NOT AN INTEGER"
emsg$(10)="IY110  NOT NUMERIC"
emsg$(11)="IY111  THAT'S NOT A VALID RESPONSE"
emsg$(12)="IY112  RENAME FAILED AT END"
emsg$(13)="IY113  INVALID ITEM FILE KEY"
emsg$(14)="IY114  ITEM NUMBER NOT FOUND"
emsg$(15)="IY115  A SORT WILL BE REQUIRED IF THIS ITEM IS ADDED"
emsg$(16)="IY116  ITEM NUMBER ALREADY IN FILE"
emsg$(17)="IY117  NO PR2 FILE FOUND"
emsg$(18)="IY118  RECORD NUMBER OUT OF RANGE"
emsg$(19)="IY119  INVALID ITEM NUMBER"
emsg$(20)="IY120  NO PR2 FILE FOUND"
emsg$(21)="IY121  THERE ARE NO VALID ITEM RECORDS. YOU'LL HAVE TO ADD SOME."
emsg$(22)="IY122  THE ITEM RECORD IS BEING DELETED"
emsg$(23)="IY123"
emsg$(24)="IY124"
emsg$(25)="IY125"
emsg$(26)="IY126"
emsg$(27)="IY127"
emsg$(28)="IY128"
emsg$(29)="IY129"
emsg$(30)="IY130"

%include znumeric
%include zparse
%include zdateio
%include zeditdte
%nolist                 rem include zdms
%include zdms
%list
%include zdmschar

a$ = "&"
cancel$="TRANSACTION CANCELLED"
digits%=6

REM----- LOOK FOR PR2 FILE --------------------
if size(common.drive$+":IYPR2.101") = 0  then \
        print tab(5);bell$;emsg$(20): \
        common.msg$=emsg$(20): \
        goto 999.1                      rem set common return and chain

REM----- DIMENSION VARIABLES FOR UP TO 3 ITEM FILES ------------
dim part.records%(3)
dim sorted.part.records%(3)
dim file.sorted%(3)
dim file.type$(3)
dim high.part.number$(3)
dim deleted.recs%(3)
dim last.update$(3)

dim array$(pr1.array.size%,pr2.part.files%)
dim array.used%(3)
dim part.file%(3)
part.file%(1) = 3
part.file%(2) = 4
part.file%(3) = 5

dim part.file.open%(3)
zero.records%=true%

%include iiyprt80
for file.ptr% = 1 to pr2.part.files%
        file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$

REM----- CHECK FOR CRASHED 101 FILE ----------------------------------
        if end #part.file%(file.ptr%)  then 21  rem check for valid sorted file
        open file.name$+"100"  \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        close part.file%(file.ptr%)
        print   tab(5);bell$;emsg$(01)
        common.msg$ = emsg$(01)
        goto    29.9                            rem error exit

21 REM----- CHECK FOR SORTED 101 FILE --------
        if end #part.file%(file.ptr%)  then 22
        open file.name$+"101"  \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        close part.file%(file.ptr%)
        trash% = rename(file.name$+"100",file.name$+"101")
        file.sorted%(file.ptr%) = true%
        file.type$(file.ptr%)="100"
        goto  26        rem delete unsorted file if found

22 REM----- CHECK FOR CRASHED 111 FILE ---------------------------
        if end #part.file%(file.ptr%)  then 23  rem check for sorted file
        open file.name$+"110"  \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        close part.file%(file.ptr%)
        print   tab(5);bell$;emsg$(01)
        common.msg$ = emsg$(01)
        goto    29.9                            rem error exit

23 REM----- CHECK FOR SORTED 111 FILE ----------------------
        if end #part.file%(file.ptr%)  then 24
        open file.name$+"111"  \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        close part.file%(file.ptr%)
        trash%=rename(file.name$+"110",file.name$+"111")
        file.sorted%(file.ptr%) = true%
        file.type$(file.ptr%)="110"
        goto  26        rem delete unsorted file if found

24 REM----- CHECK FOR CRASHED 001 FILE --------------------
        if end #part.file%(file.ptr%)  then 25  rem check for unsorted file
        open file.name$+"000"   \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%              \
                recs    sector.len%
        close part.file%(file.ptr%)
        print tab(5);bell$;emsg$(01)
        common.msg$ = emsg$(01)
        goto    29.9                            rem error exit

25 REM----- CHECK FOR UNSORTED 001 FILE -------------
        if end #part.file%(file.ptr%)  then 29  rem file not found
        open file.name$+"001"  \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        close part.file%(file.ptr%)
        trash% = rename(file.name$+"000",file.name$+"001")
        file.type$(file.ptr%)="000"
        goto 28                 rem open file

26 REM----- DELETE UNSORTED FILE IF SORTED FILE EXISTS -----------
        if end #part.file%(file.ptr%)  then 27
        open file.name$ + "001" as part.file%(file.ptr%)
        delete part.file%(file.ptr%)
27 REM----- DELETE CRASHED UNSORTED FILE IF SORTED FILE EXISTS -----
        if end #part.file%(file.ptr%)  then 28
        open file.name$ + "000" as part.file%(file.ptr%)
        delete part.file%(file.ptr%)

28 REM----- OPEN FILE --------------------------

        if end #part.file%(file.ptr%)  then 29.5        rem unexpected eof
        open file.name$+file.type$(file.ptr%) \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        part.file.open%(file.ptr%)=true%
        read    #part.file%(file.ptr%);\
%include iiyprt90

        if prt.drive$ <> pr2.part.drive$(file.ptr%)  then \
                print tab(5);bell$;emsg$(03):\
                common.msg$=emsg$(03)   :\
                goto 29.9                               rem error exit

        high.part.number$(file.ptr%)=prt.high.prt.no$
        deleted.recs%(file.ptr%)=prt.deleted.recs%
        last.update$(file.ptr%)=prt.last.update$
        part.records%(file.ptr%)=prt.no.recs%
        if file.sorted%(file.ptr%)  \
                then  sorted.part.records%(file.ptr%) = prt.no.recs%    \
                else  sorted.part.records%(file.ptr%) = 0
        if prt.no.recs% > prt.deleted.recs%  then \
                zero.records%=false%
next

goto  30                rem initialize crt

29 rem----- no file -------------------------------------------
print tab(5);bell$;emsg$(02)
common.msg$=emsg$(02)
goto 29.9                       rem error exit

29.5 REM----- UNEXPECTED END OF FILE ----------------------
print tab(5);bell$;emsg$(04)
common.msg$ = emsg$(04)

29.9 REM------ ERROR EXIT --------------------------------------
for f% = 1 to pr2.part.files%
        if part.file.open%(f%)  then \
                close part.file%(f%): \
                part.file.open%(f%)=false%
next
if pr2.open%  then close pr2.file%
goto 999.1              rem set error return and chain or stop

30 REM----- CRT INITIALIZE ----------------------
%include fiypart.bas

option.max%=crt.field.count%
file.ptr%=1

40 REM----- MAIN DRIVER ---------------------
while true%
        if pr1.debugging%  then\
                print using a$;fn.crt.msg$(str$(fre)+" BYTES FREE")
        if zero.records%  then \
                print using a$;fn.crt.msg$(emsg$(21)): \
                adding%=true%
        if adding%  then option%=2 \
                    else option%=1

        modified% = false%
        part.number.changed% = false%
        update.in.place%=false%
        table.ptr%=0

        while option% = 1
                gosub   800             rem fn.crt.input
                if crt.end.char% = valid.data%  \
                        then gosub      10000   \part lookup
                        else gosub      100     rem primary control responses
                if stopit%  then 49             rem close files and exit
        wend
        done%=false%
        write.needed%=true%
        if adding%  then  gosub 500: \set default part record
                          gosub 900:    \display record
                          no.part.number%=true%
        while not done%
                gosub   800                     rem fn.crt.input
                if crt.end.char% <> valid.data% \
                        then    gosub   150     \general control responses
                        else    gosub   50      rem data edit and display
                if stopit%  then 49             rem close files and exit
                if option% > option.max%  then \
                        option% = 2
                if option% < 2  then option%=option.max%
        wend
        if not write.needed%  then 40   rem main program loop

        if part.number.changed% and not update.in.place%  then \
                gosub  600 : \          set array to null if used
                gosub  29000            rem delete record
        if (part.number.changed% and not update.in.place%) or adding%  then \
                gosub  20000            rem add a record
        if update.in.place%  then \
                prt.number$=new.part$
        if update.in.place% and table.ptr% > 0  then \
                array$(table.ptr%,file.ptr%)=prt.number$
        if modified% or update.in.place%  then \
                gosub  28000            rem write record
        if not part.number.changed% and not adding% and not modified% \
                then  print using a$;fn.crt.msg$("NOTHING CHANGED")
wend

49 REM----- CLOSE FILES AND RENAME AT END OF PROCESSING ----------------
print using a$; fn.crt.msg$("STOP REQUESTED")
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
        part.file.open%(file.ptr%)=false%
        if not file.sorted%(file.ptr%) \
                then  pr2.part.file.needs.sort% = true%
        if rename(pr2.part.drive$(file.ptr%)+part.f.name$+ \
                left$(file.type$(file.ptr%), 2)+"1", \
                pr2.part.drive$(file.ptr%)+part.f.name$+file.type$(file.ptr%))\
                = 0  then\
                print tab(5);bell$;emsg$(12): \
                        goto  999.1                     rem error exit
next

gosub 40000     rem update pr2 file

print using a$;crt.clear$

%include zeoj

50 rem----- edit data and display ----------------------
invalid.data%=false%
on option%-1  gosub\
        2000,   \part number
        3050,   \description
        3350,   \stock
        3200,   \reorder point
        3250,   \std reorder qty
        3150,   \retail price
        3500,   \inventory value
        3100,   \vendor
        3300,   \unit cost
        3700,   \qty on order
        3600,   \order date
        3650,   \order due
        3750,   \qty back ordered
        3400,   \wip
        3450    rem under construction
gosub 850               rem display in$
if not invalid.data%  then \
        option%=option%+1
return

100 rem----- edit primary field control responses -------
if crt.end.char% = return%  and record.read%  then\
        option% = 2 :return
if crt.end.char% = ctla%  then \
        record.read% = false% :adding% = true% :\
        gosub 600:              \ set array to null if used
        option% = 2:return
if crt.end.char% = ctlb%  then \
        gosub  13000:return     rem get previous record
if crt.end.char% = ctld% and record.read%  then \
        print using a$;fn.crt.msg$(emsg$(22)): \
        gosub  29000:return     rem delete record
if crt.end.char% = ctln%  then \
        gosub  12000:return
if crt.end.char% = ctlr%  then \
        gosub  820:return
if crt.end.char% = ctls%  then \
        gosub  700:return
if crt.end.char% = escape%  then \
        stopit%=true%: return

print using a$;fn.crt.msg$(emsg$(11))
return

150 rem----- check general control responses --------------------
invalid.data% = true%
if crt.end.char% = return% and (not adding% or not no.part.number%)  then  \
        option% = option% + 1: \
        return
if crt.end.char% = ctlb% and (not adding% or not no.part.number%)  then \
        option% = option% - 1:\
        return
if crt.end.char% = ctlr%  then \
        gosub 820       :\refresh screen
        return
if crt.end.char% = ctlx%  then \
        done%=true%: record.read%=false%: \
        write.needed%=false%: \
        print using a$;fn.crt.msg$(cancel$):\
        return
if crt.end.char%=escape% and option%=2 and zero.records% and \
                no.part.number%  then \
        stopit%=true%: \
        return
if adding% and crt.end.char%=escape% and option%=2 and no.part.number% then \
        adding%=false%: write.needed%=false%: done%=true%: \
        return
if crt.end.char% = escape%  then \
        done%=true%:\
        return
print using a$;fn.crt.msg$(emsg$(11))
return

300 rem----- check a part number -------------------
%include iiyprtno

400 rem----- fn.num --------------------------
num% = fn.num%(in$)
if not num%  then \
        print using a$;fn.crt.msg$(emsg$(09)) :return
in.num=val(in$)
return
420 rem----- fn.numeric ----------------------
numeric% = fn.numeric%(in$,left.digits%,right.digits%)
if not numeric%  then print using a$;fn.crt.msg$(emsg$(10)) :return
in.numeric=val(in$)
return

500 rem----- set part number to null ------------
part.key$=null$
new.part$=null$
prt.number$ = null$
prt.vendor$ = "00000"
prt.order.date$ = "000000"
prt.order.due$ = "000000"
prt.desc$ = null$
prt.construct = 0
prt.deleted% = false%
prt.retail = 0
prt.value = 0
prt.cost = 0
prt.reord.pt = 0
prt.std.reord = 0
prt.bk.order = 0
prt.on.order = 0
prt.stock = 0
prt.wip = 0
prt.stk.add = 0
prt.stk.dep = 0
prt.td.stk.add = 0
prt.td.stk.dep = 0
prt.wip.add = 0
prt.wip.dep = 0
prt.td.wip.add = 0
prt.td.wip.dep = 0
return

600 rem----- set array to null if used --------------------
for f%=1 to pr2.part.files%
        if file.sorted%(f%) and array.used%(f%)  then \
                for x% = 1 to pr1.array.size%: \
                        array$(x%,f%)=null$: \
                next
next
return

700 rem----- save files -----------------------
old.ptr%=file.ptr%
for file.ptr%= 1 to pr2.part.files%
        close part.file%(file.ptr%)
        part.file.open%(file.ptr%)=false%
        if end #part.file%(file.ptr%)  then 29.5        rem unexpected eof
        open pr2.part.drive$(file.ptr%)+part.f.name$+file.type$(file.ptr%) \
                recl    part.recl% \
                as      part.file%(file.ptr%) \
                buff    part.buff% \
                recs    sector.len%
        part.file.open%(file.ptr%)=true%
        read #part.file%(file.ptr%),1; \
%include iiyprt90

        prt.last.update$=last.update$(file.ptr%)
        prt.no.recs%=part.records%(file.ptr%)
        prt.deleted.recs%=deleted.recs%(file.ptr%)
        prt.high.prt.no$=high.part.number$(file.ptr%)
        print #part.file%(file.ptr%), 1; \
%include iiyprt90

        msg$=str$(prt.no.recs%)+" RECORDS SAVED ON DRIVE "+prt.drive$
        if prt.deleted.recs% > 1  then \
                msg$ = msg$+". DELETED RECORDS: "+str$(prt.deleted.recs%)
        print using a$;fn.crt.msg$(msg$)
next
file.ptr%=old.ptr%
gosub 40000             rem update pr2 file

return

800 rem------ fn.crt.input -----------------
in$ = fn.crt.input$(option%)
print using a$;fn.crt.msg$(null$)
return

810 rem----- clear data -----------------
trash% = fn.crt.clear.data%
return

820 rem----- refresh screen ------------
trash% = fn.crt.display.background%
trash% = fn.crt.refresh.data%
return

850 rem----- display in$, current field --------
trash%=fn.crt.display.data%(in$, option%)
return

900 rem----- display a part record --------------
rem remove for uk version ^^^^^^^gosub 901      rem part key
gosub 902       rem part number
gosub 903       rem part description
gosub 904       rem qty stock
gosub 905       rem reorder point
gosub 906       rem standard reorder quantity
gosub 907       rem retail price
gosub 908       rem inventory value
gosub 909       rem vendor number
gosub 910       rem unit cost
gosub 911       rem quantity on order
gosub 912       rem order date
gosub 913       rem order due date
gosub 914       rem qty back ordered
return

901 rem----- display item key
trash% = fn.crt.display.data%(part.key$ ,1)
return
902 rem----- display item number -----------------------
trash% = fn.crt.display.data%(new.part$, 2)
return
909 rem----- display supplier number -------------------------
trash% = fn.crt.display.data%(prt.vendor$ ,9)
return
912 rem----- display order date ------------
if prt.order.date$>"000000"  then  date$=fn.date.out$(prt.order.date$) \
                             else  date$=null$
trash% = fn.crt.display.data%(date$ ,12)
return
913 rem----- display order due date ---------------------------------
if prt.order.due$>"000000"  then  date$=fn.date.out$(prt.order.due$) \
                             else  date$=null$
trash% = fn.crt.display.data%(date$ ,13)
return
903 rem----- display item description -----------------------------
trash% = fn.crt.display.data%(prt.desc$ ,3)
return
915 rem----- display
trash% = fn.crt.display.data%(str$(prt.construct),num.construct%)
return
907 rem----- display retail price -------------------------
trash% = fn.crt.display.data%(str$(prt.retail),7)
return
908 rem----- display inventory value ------------------
trash% = fn.crt.display.data%(str$(prt.value),8)
return
910 rem----- display unit cost -------------------------
trash% = fn.crt.display.data%(str$(prt.cost),10)
return
905 rem----- display reorder point ----------------------------
trash% = fn.crt.display.data%(str$(prt.reord.pt),5)
return
906 rem----- display standard reorder quantity --------------------
trash% = fn.crt.display.data%(str$(prt.std.reord),6)
return
911 rem----- display quantity on order --------------------------
trash% = fn.crt.display.data%(str$(prt.on.order),11)
return
914 rem----- display quantity back ordered ----------------
trash% = fn.crt.display.data%(str$(prt.bk.order),14)
return
904 rem----- display stockroom quantity --------------------
trash% = fn.crt.display.data%(str$(prt.stock), 4)
return
916 rem----- display
trash% = fn.crt.display.data%(str$(prt.wip),num.wip%)
return

rem---------------------------------------------------
rem----- include to find a item by binary search ------
rem-----------------------------------------------------
%include iiysirch

2000 rem----- edit a item number to be added to the database ------
update.in.place%=false%
part.number.changed%=false%

gosub 300                       rem check part number

if part.invalid%  then \
        in$=prt.number$:        \ display part number
        invalid.data%=true%: \
        print using a$;fn.crt.msg$(emsg$(08)):\
        return
if new.part$ = prt.number$  then  \
        in$=prt.number$:        \
        print using a$;fn.crt.msg$("NOTHING CHANGED") :\
        return
if pr2.part.files% = 1 or new.part$ < pr2.lo.number$(2)  then \
        add.file.ptr% = 1: goto 2001            rem prepare to add
if pr2.part.files% = 2 or new.part$ < pr2.lo.number$(3) \
        then  add.file.ptr% = 2 \
        else  add.file.ptr% = 3
2001 rem----- prepare to add ----------------------
add.rec%=part.records%(add.file.ptr%)+2
if file.sorted%(add.file.ptr%) \
        then previous.part$=high.part.number$(add.file.ptr%) \
        else previous.part$=null$
next.part$=left$(blank$, 11)

if not adding% and add.file.ptr%=file.ptr%  then \
        gosub 2200              rem see if part number can be updated in place
if not adding% and \
    (previous.part$<new.part$ and next.part$>new.part$)  then \
        update.in.place%=true%
if previous.part$=new.part$ or next.part$=new.part$ \
        then print using a$;fn.crt.msg$(emsg$(16)): \
        invalid.data%=true%: in$=prt.number$: return    rem display part number
if (previous.part$>new.part$ or next.part$<new.part$) \
        and file.sorted%(add.file.ptr%)  then \
                print using a$;fn.crt.msg$(emsg$(15))
if update.in.place% \
        then part.key$= "@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1) \
        else part.key$= "@"+pr2.part.drive$(add.file.ptr%)+str$(add.rec%-1)

if not adding%  then \
        part.number.changed%=true%
gosub 901       rem display part key
in$=new.part$
no.part.number%=false%
return

2200 rem------ see if part number can be updated in place ----------------
table.ptr%=0
saved.rec%=part.rec%
if part.rec%<3  or part.rec%>sorted.part.records%(file.ptr%)+1  then \
        previous.part$=null$: goto 2250         rem check next higher record
part.rec%=part.rec%-1
gosub 1800              rem read a record
previous.part$=prt.number$

2250 rem----- check next higher record ------------------------
if saved.rec%>sorted.part.records%(file.ptr%)  then \
        next.part$=left$(blank$, 11): goto 2270  rem check array
part.rec%=saved.rec%+1
gosub 1800              rem read part record
next.part$=prt.number$

2270 rem----- check array ----------------------------------
if part.rec%<>saved.rec%  then \
        part.rec%=saved.rec%: gosub 1800: \read a part record
        gosub 900                       rem display part record
if previous.part$>=new.part$ or next.part$<=new.part$  then return

lower%=0
upper%=pr1.array.size%+1
2273 rem----- look up part number in array ---------------
x%=upper%-lower%
if x%=1 \
        then return \
        else y%=int%((x%/2)+.5)+lower%
if array$(y%,file.ptr%)= prt.number$  then \
        table.ptr%=y%: return
if array$(y%,file.ptr%)= null$  then  return
if array$(y%, file.ptr%)> prt.number$  \
        then upper% = y% \
        else lower% = y%
goto 2273               rem look up part number

3050 rem----- edit part desc ---------
if match(quote$,in$,1) <> 0  then \
        in$=prt.desc$: \
        invalid.data%=true%: \
        print using a$;fn.crt.msg$(emsg$(07)): return
if prt.desc$ <> in$  then \
        prt.desc$ = in$ :\
        modified% = true%
return

3100 rem----- vendor number
gosub 400               rem fn.num
if match(left$(pound$,5),in$,1) <> 1  then \
        print using a$;fn.crt.msg$("THAT'S NOT A VALID VENDOR NUMBER"): \
        invalid.data% = true%: in$=prt.vendor$:return

if prt.vendor$ <> in$  then \
        prt.vendor$ = in$ :\
        modified% = true%
return

3150 rem  retail price
left.digits%=5:right.digits%=2
gosub 420               rem fn.numeric
if not numeric%  then  invalid.data% = true%: in$=str$(prt.retail):return
if prt.retail <> in.numeric  then \
        prt.retail = in.numeric :\
        modified% = true%
return

3200 rem  reorder point
gosub 400               rem fn.num
if not num%  then  invalid.data% = true%: in$=str$(prt.reord.pt):return
if prt.reord.pt <> in.num  then \
        prt.reord.pt = in.num :\
        modified% = true%
return

3250 rem  standard reorder quantity
gosub 400               rem fn.num
if not num%  then  invalid.data% = true%: in$=str$(prt.std.reord):return
if prt.std.reord <> in.num  then \
        prt.std.reord = in.num :\
        modified% = true%
return

3300 rem  unit cost
left.digits%=5:right.digits%=2
gosub 420               rem fn.numeric
if not numeric%  then  invalid.data% = true%: in$=str$(prt.cost):return
if prt.cost <> in.numeric  then \
        prt.cost = in.numeric :\
        modified% = true%
return

3350 rem  stock
gosub 400               rem fn.num
if not num%  then  invalid.data% = true%: in$=str$(prt.stock):return
if prt.stock <> in.num  then \
        prt.stock = in.num :\
        modified% = true%
return

3400 rem  wip
gosub 400               rem fn.num
if not num%  then  invalid.data% = true%: in$=str$(prt.wip):return
if prt.wip <> in.num  then \
        prt.wip = in.num :\
        modified% = true%
return

3450 rem  under construction
gosub 400               rem fn.num
if not num%  then  invalid.data% = true%: in$=str$(prt.construct):return
if prt.construct <> in.num  then \
        prt.construct = in.num :\
        modified% = true%
return

3500 rem  value
left.digits%=9:right.digits%=2
gosub 420               rem fn.numeric
if not numeric%  then  invalid.data% = true%: in$=str$(prt.value):return
if prt.value <> in.numeric  then \
        prt.value = in.numeric :\
        modified% = true%
return

3600 rem date ordered
if prt.order.date$>"000000"  then display$=fn.date.out$(prt.order.date$) \
                             else display$=null$
if ucase$(in$)="NONE"  then \
        in$="000000"
date% = fn.edit.date%(in$)
if not date% and in$ <> "000000" \
        then    print using a$;fn.crt.msg$("INVALID DATE"):\
                invalid.data% = true%: in$=display$: \
                return \
        else    temp$ = fn.date.in$
if prt.order.date$ <> temp$ \
        then prt.order.date$ = temp$ :\
             modified% = true%
if prt.order.date$ > "000000"  then in$=fn.date.out$(prt.order.date$) \
                               else in$=null$
return

3650 rem date order is due
if prt.order.due$>"000000"  then display$=fn.date.out$(prt.order.due$) \
                             else display$=null$
if ucase$(in$)="NONE"  then \
        in$="000000"
date% = fn.edit.date%(in$)
if not date% and in$ <> "000000" \
        then    print using a$;fn.crt.msg$("INVALID DATE"):\
                invalid.data% = true%: in$=display$: \
                return \
        else    temp$ = fn.date.in$
if prt.order.due$ <> temp$ \
        then prt.order.due$ = temp$ :\
             modified% = true%

if prt.order.due$>"000000"  then in$=fn.date.out$(prt.order.due$) \
                             else in$=null$
return


3700 rem  qty on order
gosub 400               rem fn.num
if not num%  then  invalid.data% = true%: in$=str$(prt.on.order): return
if prt.on.order <> in.num  then \
        prt.on.order = in.num :\
        modified% = true%
return

3750 rem  qty back ordered
gosub 400               rem fn.num
if not num%  then  invalid.data% = true%: in$=str$(prt.bk.order): return
if prt.bk.order <> in.num  then \
        prt.bk.order = in.num :\
        modified% = true%

return

10000 rem----- item lookup -------------------------
record.read% = false%
if left$(in$,1) = "@" \
        then gosub  11000       \read by file key,record number
        else gosub  10500       rem search by part number
if int.invalid%  then  \
        return

gosub 1800              rem read a record
if prt.deleted%  then \
        print using a$;fn.crt.msg$("REFERENCE TO DELETED ITEM"): \
        return
record.read% = true%
part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
new.part$=prt.number$
gosub 900                       rem display a part record
return

10500 rem----- check if valid  item number  get record number ----------
int.invalid%=false%
gosub 300               rem check part number
if part.invalid%  then \
        print using a$;fn.crt.msg$(emsg$(19)): \
        int.invalid%=true%: \
        return
gosub 1700              rem heuristic binary search
array.used%(file.ptr%)=true%
if int.invalid%  then \
        print using a$;fn.crt.msg$(emsg$(14))
return

11000 rem----- read by file key, record number ----------------

int.invalid% = false%
key$ = ucase$(mid$(in$,2,1))

if key$ > "9" or key$ < "0"  \
        then  part.record$ = right$(in$,len(in$)-2)\
        else  key$ = pr2.part.drive$(1):part.record$=right$(in$,len(in$)-1)

if match(left$(pound$,len(part.record$)),part.record$,1) <> 1  then \
        print using a$;fn.crt.msg$(emsg$(13)): \
        int.invalid% = true%:return

part.rec% = val(part.record$)+1

for file.ptr% = 1 to pr2.part.files%
        if key$ = pr2.part.drive$(file.ptr%)  then 11100   rem key valid
next
print using a$;fn.crt.msg$(emsg$(13))
int.invalid% = true%
return

11100 rem----- here if key valid -------------------

if part.rec% > part.records%(file.ptr%)+1 or part.rec% < 2  then \
        print using a$;fn.crt.msg$(emsg$(18)): \
        int.invalid% = true%
return

12000 rem----- get next record ------------------------
if part.rec%=0  then part.rec% = 1
old.file.ptr%=file.ptr%
old.rec%=part.rec%
first%=true%

12001 rem----- loop to get next record ------------------
part.rec% = part.rec% + 1
while part.rec% > part.records%(file.ptr%)+1
        if file.ptr%=pr2.part.files% and not first%  then \
                print using a$;fn.crt.msg$(emsg$(21)): return
        if file.ptr% = pr2.part.files%  then\
                file.ptr%=0: first%=false%
        part.rec% = 2:file.ptr% =file.ptr% + 1
wend

gosub 1800                      rem read record
if prt.deleted%  then 12001     rem loop to get next record

record.read% = true%
part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
new.part$=prt.number$
gosub 900                       rem display record
return

13000 rem----- get previous record ------------------------
if part.rec%=0  then part.rec% = 1
old.file.ptr%=file.ptr%
old.rec%=part.rec%
first%=true%

13001 rem----- loop to get a previous record ------------------
part.rec% = part.rec% - 1
while part.rec% < 2
        if file.ptr%=1 and not first%  then \
                print using a$;fn.crt.msg$(emsg$(21)): return
        if file.ptr% = 1  then\
                file.ptr%=pr2.part.files%+1: first%=false%
        file.ptr% =file.ptr% - 1: part.rec% = part.records%(file.ptr%)+1
wend

gosub 1800                      rem read record
if prt.deleted%  then 13001     rem loop to get a prev record

record.read% = true%
part.key$="@"+pr2.part.drive$(file.ptr%)+str$(part.rec%-1)
new.part$=prt.number$
gosub 900                       rem display record
return

20000 rem----- add a record ------------------
part.rec% = add.rec%
file.ptr% = add.file.ptr%
prt.number$ = new.part$
if high.part.number$(file.ptr%) < prt.number$ and \
    file.sorted%(file.ptr%)  then \
    sorted.part.records%(file.ptr%)=sorted.part.records%(file.ptr%)+1
if high.part.number$(file.ptr%) < prt.number$ \
    then high.part.number$(file.ptr%) = prt.number$
if high.part.number$(file.ptr%) > prt.number$ and file.sorted%(file.ptr%)\
    then print using a$;fn.crt.msg$("FILE BEING RENAMED AS UNSORTED"):\
                gosub 30000             \rename file

gosub 28000                                     rem write record
part.records%(file.ptr%) = part.records%(file.ptr%)+1
zero.records%=false%
return

28000 rem----- write a record -----------------
last.update$(file.ptr%)=common.date$
print #part.file%(file.ptr%), part.rec%; \
%include iiyprt00

return

29000 rem----- delete a record -----------------

prt.deleted% = true%
gosub 28000                     rem write a record
prt.deleted% = false%
record.read% = false%
deleted.recs%(file.ptr%) = deleted.recs%(file.ptr%)+1
if part.records%(1)<=deleted.recs%(1) and part.records%(2)<=deleted.recs%(2) \
        and part.records%(3)<=deleted.recs%(3)   then \
                        zero.records%=true%: option%=2
return

30000 rem----- rename file -------------------------

close part.file%(file.ptr%)
part.file.open%(file.ptr%)=false%
file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$
trash%=rename(file.name$+"000",file.name$+file.type$(file.ptr%))
file.sorted%(file.ptr%)=false%
file.type$(file.ptr%)="000"
if end #part.file%(file.ptr%)  then 30009       rem close files on error exit
open file.name$+"000" \
        recl part.recl% \
        as  part.file%(file.ptr%) \
        buff part.buff% \
        recs sector.len%
pr2.part.file.sort.needed%=true%
gosub 40000             rem update pr2 file
return

30009 rem----- here if rename fails ----------------------------
print using a$;fn.crt.msg$(bell$+emsg$(06))
common.msg$=emsg$(06)
goto 29.9               rem close files and exit

40000 rem----- open write and close pr2 file ------------
pr2.file%=2
if end #pr2.file%  then 40009   rem error message and exit
open  common.drive$ +":"+ system$ + "pr2.101"  as pr2.file%
pr2.open%=true%
print #pr2.file%; \
%include iiypr200

close pr2.file%
pr2.open%=false%
return

40009 rem----- eof on pr2 file ---------------------------
print using a$;fn.crt.msg$(emsg$(17))
common.msg$=emsg$(17)
goto 29.9       rem error exit

end

