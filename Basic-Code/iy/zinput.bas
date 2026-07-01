rem     june 28, 1979
def fn.input%(desc$,length%)
        cr%=false%:stopit%=false%:invalid%=false%:back%=false%
        if length%>255 \
                then   print tab(10);"Enter "+desc$+" "; \
                else   print tab(10);"Enter "+desc$+" ("+str$(length%)+") ";
        input "";line in$
        if in$= null$	\
                then   uin$ = null$   \
                else   uin$=ucase$(in$)
        if uin$=stop$ or uin$ = escape$   then stopit%=true%
        if in$ = ctlb$ or in$=back$  then back% = true%
        if in$=return$ then cr%=true%
        if match(quote$,in$,1)<>0 or	\
           match(ctlz$,in$,1)<>0 or	\
           match(lf$,in$,1)<>0 or	\
           len(in$)>length% then	 \
                invalid%=true%
        if stopit% or invalid% or cr% or back%	then \
                fn.input%=true% :\
                uin$=null$ :\
                in$=null$ :\
                return
        fn.input%=false%
        return
fend


