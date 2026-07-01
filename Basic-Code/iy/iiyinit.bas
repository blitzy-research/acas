rem-----  aug. 22, 1979 ---------------------------------
%include iiyconst
%include zserial
if not chained.from.root%  then \
        print tab(5);bell$;"IY000  Program must be run from iy menu": \
        goto 999.1                      rem error exit

if pr1.bell.used%  then bell$=chr$(7) \
                   else bell$=null$

print using "&";crt.clear$

