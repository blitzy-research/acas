rem Oct. 18,1979
dim sorted.part.records%(pr2.part.files%)
dim high.part.number$(pr2.part.files%)
dim deleted.recs%(pr2.part.files%)
dim last.update$(pr2.part.files%)

dim array$(pr1.array.size%,pr2.part.files%)
dim part.file%(3)
part.file%(1) = 3
part.file%(2) = 4
part.file%(3) = 5
dim part.exists%(3)
part.dim%=true% 	rem flag to indicate that above has been dimensioned
%include iiyprt80

zero.records%=true%
for file.ptr% = 1 to pr2.part.files%
        file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$

        if end #part.file%(file.ptr%)  then 2           rem rename sorted file
        open file.name$+"100"  \                this checks for a crashed file
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        print   tab(5);bell$;emsg$(01)
        common.msg$ = emsg$(01)
        gosub   9                               rem close any open files
        goto    999.1                           rem error exit

2 rem----- rename sorted file ------------
        trash%=rename(file.name$+"100", file.name$+"101")

        if end #part.file%(file.ptr%)  then 2.59        rem unexpected eof
        open file.name$+"100" \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%
        part.exists%(file.ptr%)=true%
        read    #part.file%(file.ptr%);\
%include iiyprt90

        if prt.drive$ <> pr2.part.drive$(file.ptr%)  then \
                print tab(5);bell$;emsg$(03):\
                common.msg$=emsg$(03)   :\
                gosub 9         :\              close any open files
                goto 999.1                              rem error exit

        high.part.number$(file.ptr%)=prt.high.prt.no$
        deleted.recs%(file.ptr%)=prt.deleted.recs%
        last.update$(file.ptr%)=prt.last.update$
        sorted.part.records%(file.ptr%)=prt.no.recs%
        if prt.no.recs% > prt.deleted.recs%  then \
                zero.records%=false%
next
if not zero.records%  then 2.6          rem crt initialize

common.msg$="IY086  There are no valid item records"
print tab(5);bell$;common.msg$
if aud.exists%  then  aud.rename%=true% \
                else  aud.rename%=false%
gosub 9         rem close all files
for f%=1 to pr2.part.files%
        file.name$=pr2.part.drive$(f%)+":iyprt."
        trash%=rename(file.name$+"101", file.name$+"100")
next
audit.name$="iyaud."
if aud.rename%  then \
        trash%=rename(audit.name$+"001",audit.name$+"000")
goto 999.2              rem exit

2.59 rem----- unexpected end of file ----------------------
print tab(5);bell$;emsg$(04)
common.msg$ = emsg$(04)
gosub 9                         rem close any open files
goto 999.1                      rem error exit

2.6 rem----- crt initialise ----------------------

