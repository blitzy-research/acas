rem Aug.  7,1979
dim part.records%(pr2.part.files%)
dim high.part.number$(pr2.part.files%)
dim deleted.recs%(pr2.part.files%)
dim last.update$(pr2.part.files%)

dim array$(pr1.array.size%,pr2.part.files%)
dim part.file%(3)
part.file%(1) = 3
part.file%(2) = 4
part.file%(3) = 5
%include iiyprt80
abort%=false%
for file.ptr% = 1 to pr2.part.files%
        file.name$ = pr2.part.drive$(file.ptr%)+part.f.name$+"101"

rem----- open file --------------------------

        if end #part.file%(file.ptr%)  then 2.59        rem end of file
        open file.name$ \
                recl    part.recl%      \
                as      part.file%(file.ptr%)   \
                buff    part.buff%      \
                recs    sector.len%

        open.files%=open.files%+1
        read    #part.file%(file.ptr%);\
%include iiyprt90

        if prt.drive$ <> pr2.part.drive$(file.ptr%)  then \
                print tab(5);bell$;emsg$(01):\
                common.msg$=emsg$(01)   :\
                abort%=true%:   goto 2.6        rem end of include

        high.part.number$(file.ptr%)=prt.high.prt.no$
        deleted.recs%(file.ptr%)=prt.deleted.recs%
        last.update$(file.ptr%)=prt.last.update$
        part.records%(file.ptr%)=prt.no.recs%
next

goto  2.6               rem end of include

2.59 rem----- unexpected end of file ----------------------
print tab(5);bell$;emsg$(02)
common.msg$ = emsg$(02)
abort%=true%

2.6 rem----- end of include ----------------------

