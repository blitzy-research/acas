rem--------audit file reads---------
rem--------29 June,1979-------------
6.301   rem audit header read
        read #audit.file%, 1;\
%include iiyaud90
        return

6.302   rem audit sequential read
        read #audit.file%;\
%include iiyaud00
        return

6.303   rem audit random read
        read #audit.file%, aud.no.recs% + 1;\
%include iiyaud00
        return

