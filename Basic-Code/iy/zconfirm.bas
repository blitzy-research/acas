rem      May   4, 1979
def fn.confirmed%
        while true%
                print tab(10);"Type ""run"" To Continue"
                print tab(10);"Type ""stop"" To Stop Program"
                print
                print tab(20);
                input ">";line in$
                if ucase$(in$)="run" then fn.confirmed%=true%:return
                if ucase$(in$)="stop" then fn.confirmed%=false%:return
        wend
fend

