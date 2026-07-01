rem     May  16, 1979
def fn.get.drive%(desc$)
        xx%=fn.input%(desc$+" DRIVE",1)
        while invalid% or ((uin$<"A" or uin$>"Z") and not xx%)
                print tab(5);bell$;system$ + "002 INVALID "+desc$+" DRIVE"
                xx%=fn.input%(desc$+" DRIVE",1)
        wend
        fn.get.drive%=xx%
        drive$=uin$
        return
fend


