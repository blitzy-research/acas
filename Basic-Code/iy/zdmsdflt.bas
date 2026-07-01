rem
rem---------------------------------------------------------------------------
rem
rem     CRT characteristics definition of a Hzeltine 1500 CRT terminal
rem
rem---------------------------------------------------------------------------
rem
        crt.leadin$ = chr$(126)
        crt.sca$ = crt.leadin$+chr$(17)         rem set cursor address
        crt.sca.row$ = ""
        crt.sca.column$ = ""
        crt.sca.format% = crt.sca.hex%
        crt.sca.order% = crt.order.col.row%
        crt.clear$ = crt.leadin$+chr$(18)+crt.leadin$+chr$(23)	rem clear screen
        crt.clear.foreground$ = crt.leadin$+chr$(29)    rem clear foreground
        crt.foreground$ = crt.leadin$+chr$(31)          rem begin foreground data
        crt.background$ = crt.leadin$+chr$(25)          rem begin background data
        crt.home$ = crt.leadin$+chr$(18)                        rem home cursor
        crt.up.cursor$ = crt.leadin$+chr$(12)           rem up one row
        crt.down.cursor$ = crt.leadin$+chr$(11)         rem down one row
        crt.right.cursor$ = chr$(16)                    rem right one column
        crt.left.cursor$ = chr$(8)                      rem left one column
        crt.backspace$ = chr$(8)+" "+chr$(8)            rem destructive backspace
        crt.alarm$ = chr$(7)                            rem console alarm
        crt.eol$ = crt.leadin$+chr$(15)
        crt.eos$ = crt.leadin$+chr$(24)
        crt.delete.line$ = crt.leadin$+chr$(19)
        crt.insert.line$ = crt.leadin$+chr$(26)
rem
        crt.columns% = 80
        dim crt.column.xlate%(crt.columns%)
        for crt.loop% = 1 to 31
                crt.column.xlate%(crt.loop%) = 95 + crt.loop%
                next
        for crt.loop% = 32 to 80
                crt.column.xlate%(crt.loop%) = crt.loop% - 1
                next
rem
        crt.rows% = 24
        dim crt.row.xlate%(crt.rows%)
        for crt.loop% = 1 to crt.rows%
                crt.row.xlate% (crt.loop%) = 95 + crt.loop%
                next

