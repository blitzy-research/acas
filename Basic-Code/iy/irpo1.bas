rem       june 14, 1979
%include irpo2
%include irpo4
if not chained% then for x%=1 to 24:print:next x%       rem clear screen
if not chained% then common.drive$=fn.get.sys.drive$
%include irpo5
if not chained% \
  then  print:print:print               :\
        print cpyrght$                  :\
        print                           :\
        print system$;version$;"     SERIAL NUMBER: ";serial.number$ :\
        print program$                  :\
        print:print:print               :\
        print                            \
  else  for x%=1 to 24:print:next x%                    rem clear screen
if pr1.bell.suppressed% then bell$=null$

