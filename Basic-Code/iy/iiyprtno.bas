rem----- may 18,1979   check a part number -------------------
part.invalid% = false%
new.part$=ucase$(in$)
len%=len(new.part$)
for char% = 1 to len%
        character$ = mid$(new.part$,char%,1)
        if (character$ > "9" or character$ < "0") and\
           (character$ > "Z" or character$ < "A") and\
           character$ <> "/" and character$ <> "-" \
           then\
                part.invalid%=true%: new.part$=prt.number$: return
next
new.part$=left$(new.part$+blank$,10)
return


