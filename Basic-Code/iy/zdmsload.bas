rem-- may 22,1979 ----------------------------------------------------------
rem
rem     fn.crt.load.display%            load and display a crt screen definition
rem
rem     open screen format definition file, load parameters,
rem     and display screen definition on crt
rem
rem     parameters:     crt format definition file name
rem     parameters:     crt.file$       - crt format definition file name
rem
rem     return:         crt.format.fields%      - set to proper values
rem                     crt.format.def$ - crt background format strings
rem
rem--------------------------------------------------------------------------
rem
   def fn.crt.load.display%(crt.screen.file$,crt.disk$)
        fn.crt.load.display% = 0
        if end #crt.file%       \
          then  50000.3
        if crt.disk$ <> ""      \
          then  crt.file$ = crt.disk$ + ":" + crt.screen.file$  \
          else  crt.file$ = crt.screen.file$
        crt.file$ = crt.file$ + ".fmt"
        open crt.file$ as crt.file%     \
                buff(8) recs(128)
        if end #crt.file%       \
          then  50000.4
        if crt.field.count% > 0         \
          then  for crt.loop% = 1 to crt.field.count% : \
                        crt.buffer$(crt.loop%) = "" :   \
                        next
        read #crt.file%;crt.format.count%,crt.field.count%
        dim crt.format.fields%(crt.field.count%,3)
        dim crt.buffer$(crt.field.count%)
        crt.format.fields%(0,0) = crt.field.count%
        console
        for crt.loop% = 1 to crt.max.buffer.count%
                crt.screen.buffer$(crt.loop%) = ""
                next
        crt.buffer.count% = 1
        crt.screen.buffer$(1) = crt.clear$+crt.background$
        print using crt.using$;crt.screen.buffer$(1)
        for crt.loop% = 1 to crt.format.count%
                read #crt.file%;        \
                        crt.text.row%,          \
                        crt.text.column%,       \
                        crt.text$
                print using crt.using$; \
                        fn.crt.sca$(crt.text.row%,crt.text.column%);    \
                        crt.text$
                if len(crt.screen.buffer$(crt.buffer.count%))   \
                        + len (fn.crt.sca$(crt.text.row%,crt.text.column%)) \
                        + len (crt.text$)                       \
                                > 80                            \
                  then  crt.buffer.count% = crt.buffer.count% + 1
                crt.screen.buffer$ (crt.buffer.count%) =        \
                        crt.screen.buffer$ (crt.buffer.count%)  \
                        + fn.crt.sca$ (crt.text.row%, crt.text.column%) \
                        + crt.text$
                next
        for crt.loop% = 1 to crt.field.count%
                read #crt.file%;crt.format.fields%(crt.loop%,0),        \
                        crt.format.fields%(crt.loop%,1), \
                        crt.format.fields%(crt.loop%,2),        \
                        crt.format.fields%(crt.loop%,3)
                next
        close crt.file%
        return
50000.3 \
        fn.crt.load.display% = 1
        return
50000.4 \
        fn.crt.load.display% = 2
        close crt.file%
        return
        fend
rem
rem---------------------------------------------------------------------------

