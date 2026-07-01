rem----- July 30, 1979 -------------
def fn.abort%
        fn.abort%=false%
        if constat% = 0  \
                then   return  \
                else   status% = conchar%
        console
        print tab(10);"(TYPE ""STOP"" TO STOP PROGRAM)"
        print tab(10);"(Press return to continue)";
        input "";line in$
        if in$<>null$  then in$=ucase$(in$)
        if in$=stop$ or in$=escape$ \
                then fn.abort%=true%  \
                else lprinter
        return
fend


