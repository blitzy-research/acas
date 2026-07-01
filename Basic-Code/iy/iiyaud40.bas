rem-----audit file writes-------
rem-------29 june,1979---------
6.401   rem write audit header
        print #audit.file%, 1;\
%include iiyaud90
        return

6.402   rem write audit sequential
        print #audit.file%;\
%include iiyaud00
        return

6.403   rem write audit random
        print #audit.file%, aud.no.recs% + 1;\
%include iiyaud00
        return

