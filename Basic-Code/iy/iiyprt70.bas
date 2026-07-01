rem----- July 30,1979 --------------------------------
9 rem----- close all open files ----------------------

if aud.exists%  then  close audit.file%
if pr2.exists%  then  close pr2.file%

if not part.dim%  then return           rem return if flag array
                                        rem not dimensioned
for f% = 1 to pr2.part.files%
        if part.exists%(f%)  then  close part.file%(f%)
next
return

