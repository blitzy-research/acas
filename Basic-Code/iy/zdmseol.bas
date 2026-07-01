rem----------------------------------------------------------------------------
rem
rem	fn.crt.eol$             Erase to end of line
rem
rem----------------------------------------------------------------------------

   def	fn.crt.eol% (row%, column%)
        if crt.eol$ <> ""       \
          then  print fn.crt.sca$ (row%,column%) + crt.eol$ :   \
                return
        crt.temp% = crt.columns% - column% + 1
        if crt.temp% > 65       \
          then  print fn.crt.sca$ (row%,column%)        \
                                + left$(crt.blank$,65)  :       \
                print  fn.crt.sca$ (row%,column%+65)    \
                                + left$ (crt.blank$,crt.temp%-65) \
          else  print fn.crt.sca$ (row%,column%)        \
                        + left$ (crt.blank$,crt.temp%)
        return
        fend

