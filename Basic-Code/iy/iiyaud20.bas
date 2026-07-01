rem-----audit file create------
rem-----8 august, 1979-----------
6.200   aud.eof% = false%
        aud.exists% = false%
%include iiyaud80
        aud.name$ = pr1.audit.drive$+":"+system$+"AUD"+"."+aud.f.type$
        if end #audit.file%  then 6.208
        create aud.name$ \
                recl    audit.recl% \
                as      audit.file% \
                buff    audit.buff% \
                recs    sector.len%
        aud.exists% = true%
        return
6.208   aud.eof% = true%
        return

