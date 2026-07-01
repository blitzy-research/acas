rem----- July 30, 1979 -----------------------------
def fn.yorn%(cr.default%)
        good%=false%:no%=false%:yes%=false%:cr%=false%
        while not good%
                input "";line in$
                if in$=return$ then cr%=true%
                if in$<>null$  then in$=ucase$(in$)
                if in$=stop$  or in$=escape$  then stopit%=true%
                if in$="Y" or in$="YES" then yes%=true%
                if in$="N" or in$="NO" then no%=true%
                if yes% or no% or stopit%  then good%=true%
                if cr% and cr.default%<>not.accepted% then \
                        good%=true%
                if not good% then print tab(10);"(Y OR N ONLY) ";
        wend
        if no% then fn.yorn%=false%:return
        if yes% then fn.yorn%=true%:return
        fn.yorn%=cr.default%
        return
fend

