rem       May. 16, 1979
%include iiyconst
%include znumeric
%include zparse
%include zinput
%include zgetdate
%include zsysdriv
if chained.from.root%  then 1   rem end of include
common.drive$=fn.get.sys.drive$
emsg.0$ = "IY000 NO PARAMETER FILE"
if common.drive$=null$ then \
        print tab(5);bell$;emsg.0$ :\
        common.msg$ = emsg.0$:\
        goto 999.1              rem exit paragraph
pr1.file% = 1
if end #pr1.file%  then .09     rem no parameter file
open  common.drive$ +":"+ system$ + "pr1.101"  as pr1.file%
dim pr1.part.drive$(3)
dim pr1.lo.number$(3)
read #pr1.file%; \
%include iiypr100

close pr1.file%
        print:print:print
        print system$;version$
        print program$
        print:print:print
        print tab(10);pr1.co.name$
        print
.02 rem----- get common date ------------------------
common.date$ = fn.get.date$("TODAY'S")

if cr%  then  \
        print tab(5);"INVALID DATE" :goto .02  rem get common date
if stopit%  then   999.2        rem operator requested exit

goto 1          rem end of include

.09 rem------ here if no parameter file -------------
print tab(5);bell$;emsg.0$
common.msg$ = emsg.0$
goto 999.1              rem exit paragraph

1 rem----- here if chained from root -----------
if pr1.bell.used% then bell$=chr$(7)

