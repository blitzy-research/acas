rem-----audit file open-----
rem-----7 august, 1979-------
6.100   aud.eof% = true%
        aud.exists% = false%
%include iiyaud80
        aud.name$ = pr1.audit.drive$+":"+system$+"AUD"+"."+aud.f.type$
        if end #audit.file%  then 6.109
        open aud.name$ \
                recl    audit.recl% \
                as      audit.file% \
                buff    audit.buff% \
                recs    sector.len%
        if end #audit.file%  then 6.108
        aud.exists% = true%
        aud.eof% = false%
        return
6.108   aud.eof% = true%
6.109   return

