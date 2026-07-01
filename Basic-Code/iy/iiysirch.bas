rem aug.  8,1979

1700 rem------------------------------------------------------
        rem -- search part file for correct starting record

        saved.part$ = new.part$
        lower% = 0
        upper% = pr1.array.size% + 1
        lower.rec% = 1
        int.invalid% = false%
if pr2.part.files% = 1  or   saved.part$ < pr2.lo.number$(2) then  \
        file.ptr% = 1 :\
        goto 1705
if pr2.part.files% = 2  or   saved.part$ < pr2.lo.number$(3) \
        then  file.ptr% = 2 \
        else  file.ptr% = 3
1705
        if sorted.part.records%(file.ptr%)<1  \
                then int.invalid% = true%: return \
                else upper.rec% = sorted.part.records%(file.ptr%)+2
1710 rem------------------------------
        rem -- do the binary search

        y% = upper% - lower%
        if y% = 1 then  goto 1780      rem  no more table space
        new.element% = int((y%/2) + .5) + lower%

        x% = upper.rec% - lower.rec%
        if x% = 1  then \
                int.invalid% = true%    :\
                return
        part.rec% = int((x%/2) + .5) + lower.rec%

        search.part$ = array$(new.element%,file.ptr%)
        if search.part$ = ""  then  gosub 1790
        if search.part$ = saved.part$  then  return  rem  found it
        if search.part$ < saved.part$  then  lower.rec% = part.rec%  :\
                                             lower% = new.element%  :\
                                       else  upper.rec% = part.rec%  :\
                                             upper% = new.element%
        goto 1710

1780 rem----------------------------------
        rem -- array elements  diff = 1
        search.part$=null$
        while search.part$ <> saved.part$
                x% = upper.rec%-lower.rec%
                if x%=1  then \
                        int.invalid%=true%: \
                        return
                part.rec% = int((x%/2)+ .5)+ lower.rec%
                gosub 1800                      rem read record
                search.part$=prt.number$
                if search.part$ < saved.part$  \
                        then lower.rec% = part.rec% \
                        else upper.rec% = part.rec%
        wend
return  rem -- found it!

1790 rem----------------------------------
        rem -- get new element in array

        gosub 1800                              rem read a record
        array$(new.element%,file.ptr%) = prt.number$
        search.part$ = prt.number$
        return

1800 rem----------------------------------
        rem -- read a record

read #part.file%(file.ptr%),part.rec%;\
%include iiyprt00

return

