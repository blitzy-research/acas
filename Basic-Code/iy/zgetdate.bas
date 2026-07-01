rem      May  10, 1979
%include b:zeditdte
%include b:zdatei/o
rem requires zinput.bas
dim dd$(3)
def fn.get.date$(desc$)
        dd$(pr1.date.mo%)="MM":dd$(pr1.date.yr%)="YY":dd$(pr1.date.dy%)="DD"
        date.form$=dd$(1)+"/"+dd$(2)+"/"+dd$(3)
        trash% = fn.input%(desc$+" DATE ("+date.form$+") " ,256)
        while not fn.edit.date%(in$)
                if cr% or stopit%   then fn.get.date$ = null$ : return
                print tab(5);bell$; system$ + "005 Invalid Date"
                trash%=fn.input%(desc$+" Date ("+date.form$+") ",256)
        wend
        fn.get.date$=fn.date.in$
        return
fend

