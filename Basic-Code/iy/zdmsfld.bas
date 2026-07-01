rem---------------------------------------------------------------------------
rem
rem     fn.crt.field$           read data from keyboard into display field
rem
rem     parameters:     crt.field% - field number
rem
rem     return:         crt.field$ - field contents
rem
rem----------------------------------------------------------------------------
rem
   def  fn.crt.field$ (crt.field%)
        console
        crt.text$ = crt.buffer$(crt.field%)
        crt.input% = crt.true%
        crt.warning.hold% = crt.warning.limit%
        while crt.input%
                crt.warning.limit% = crt.warning.hold%
                crt.field$ = fn.crt.input$(crt.field%)
                if crt.end.char% <> 15h and crt.end.char% <> 18h        \
                  then  crt.input% = crt.false% \
                  else  crt.dummmy% = fn.crt.display.data% (crt.text$, crt.field%)
                wend
        if crt.field$ = ""      \
          then  crt.field$ = crt.text$
        if crt.field.modified%  \
          then  crt.dummy% = fn.crt.display.data% (crt.field$, crt.field%)
        if crt.field$ = ""      \
          then  fn.crt.field$ = ""      \
          else  fn.crt.field$ = crt.field$
        return
        fend

