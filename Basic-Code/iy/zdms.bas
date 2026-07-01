rem----- AUG. 21,1979 ---------------------------------------------------------
rem
rem             AI-80 Display Management System
rem
rem             Basic Common Program Interface Functions
rem
rem----------------------------------------------------------------------------
rem
rem	copyright l978  -       Arkenstone, Inc.
rem                             785 Market St.	Suite 515
rem                             San Francisco, Ca. 94103
rem                             (415)-957-1468
rem
rem----------------------------------------------------------------------------
rem     v01-01          P. Carleton             June 14,1979
rem     ----------------------------------------------------
rem     removed fn.crt.ident
rem---------------------------------------------------------------------
rem
   def fn.crt.dummy%            rem this contains dummy dimension statements
        dim crt.row.xlate%(1)
        dim crt.column.xlate%(1)
        dim crt.format.fields% (1,1)
        dim crt.screen.buffer$(1)
        dim crt.buffer$(1)
        return
        fend

rem--------------------------------------------------------------------------
rem
rem     fn.crt.dim.screen.buffer$       used to dimension screen buffer
rem
rem---------------------------------------------------------------------------

   def  fn.crt.dim.screen.buffer$ (max%)
        if crt.max.buffer.count% > 0    \       eliminate any existing strings
          then  for crt.loop% = 1 to crt.max.buffer.count% : \
                  crt.screen.buffer$ (crt.loop%) = ""
                  next
        if max% > 0     \
          then  crt.max.buffer.count% = max%    \
          else  crt.max.buffer.count% = 50
        dim crt.screen.buffer$ (crt.max.buffer.count%)
        return
        fend

rem----------------------------------------------------------------------------
rem
rem     fn.crt.sca$             set CRT cursor address to row & column
rem
rem----------------------------------------------------------------------------

   def fn.crt.sca.row$(row%)
        if crt.sca.format% = crt.sca.hex%       \
          then  crt.dummy$      \
                        = crt.sca.row$  \
                                + chr$(crt.row.xlate%(row%)) : \
                fn.crt.sca.row$ = crt.dummy$
        if crt.sca.format% = crt.sca.decimal%   \
          then  crt.dummy$      \
                        = crt.sca.row$  \
                                + str$(crt.row.xlate%(row%)) : \
                fn.crt.sca.row$ = crt.dummy$
        return
        fend
   def fn.crt.sca.column$(column%)
        if crt.sca.format% = crt.sca.hex%       \
          then  crt.dummy$      \
                        = crt.sca.column$       \
                        + chr$(crt.column.xlate%(column%)) : \
                fn.crt.sca.column$ = crt.dummy$
        if crt.sca.format% =crt.sca.decimal%    \
          then  crt.dummy$      \
                        = crt.sca.column$       \
                                + str$(crt.column.xlate%(column%)) : \
                fn.crt.sca.column$ = crt.dummy$
        return
        fend
   def fn.crt.sca$(row%,column%)
        if crt.sca.order% = crt.order.row.col%  \
          then  fn.crt.sca$ = crt.sca$          \
                                + fn.crt.sca.row$(row%) \
                                + fn.crt.sca.column$(column%)   \
          else  fn.crt.sca$ = crt.sca$          \
                                + fn.crt.sca.column$(column%)   \
                                + fn.crt.sca.row$(row%)
        return
        fend
rem----------------------------------------------------------------------------
rem
rem             AI-80 Display Management System
rem
rem             Standard Program Interface Functions
rem
rem----------------------------------------------------------------------------
rem
rem     copyright l978  -       Arkenstone, Inc.
rem                             785 Market St.	Suite 515
rem                             San Francisco, Ca. 94103
rem                             (415)-957-1468
rem
rem----------------------------------------------------------------------------
rem	V01-01          P. Carleton             June 11,1979
rem	----------------------------------------------------
rem	added code to translate control characters
rem----------------------------------------------------------------------------
rem
rem     fn.crt.msg$             print informational message in the standard
rem                             CRT message display area
rem
rem----------------------------------------------------------------------------
rem
   def fn.crt.msg$ (crt.text$)
        if crt.msg.issued% = crt.true%  \
          then  print using crt.using$; \
                        crt.msg.header$;        \
                        left$(crt.blank$,crt.columns%-15);      \
                        crt.msg.trailer$
        crt.dummy$ = crt.msg.header$            \
                        + left$ (crt.text$,crt.columns%-15)     \
                        + crt.msg.trailer$
        fn.crt.msg$ = crt.dummy$
        if crt.text$ <> ""      \
          then  crt.msg.issued% = crt.true%     \
          else  crt.msg.issued% = crt.false%
        return
        fend
rem
rem---------------------------------------------------------------------------
rem
rem     fn.crt.input$           basic field data input function. this is
rem                             primarily for use by other functions as
rem                             certain editting functions are not implemented
rem                             at this level (eg, ctl-x / ctl-u support)
rem
rem                             see fn.crt.field$ for user-oriented input
rem
rem----------------------------------------------------------------------------
rem
   def fn.crt.input$ (crt.field%)
        crt.field.modified% = crt.false%
        if crt.field% < 1  or crt.field% > crt.field.count%     \
          then  fn.crt.input$ = "" :    \
                crt.errcode% = 1 :      \
                return  \
          else  crt.errcode% = 0
        crt.row% = crt.format.fields%(crt.field%,0)
        crt.column% = crt.format.fields%(crt.field%,1)
        console
        crt.limit% = crt.format.fields%(crt.field%,2)
        print using crt.using$; \
                fn.crt.sca$(crt.row%,crt.column%);crt.foreground$
        crt.data$ = ""
        crt.flag% = crt.true%
        crt.loop% = 0
        while crt.flag%
                crt.data% = conchar%
                crt.temp.back% = asc(mid$(crt.back.count$, crt.data%+1, 1))
                if crt.data% < 32  then \
                        crt.data% = asc(mid$(crt.ctl.xlate$, crt.data%+1, 1))
                if crt.key%  then \
                        crt.data% = asc(mid$(crt.key.xlate$, crt.data%+1, 1))
                if crt.data% = crt.key.prefix%  and not crt.key% \
                        then  crt.key% = crt.true% \
                        else  crt.key% = crt.false%
                if crt.temp.back% <> 0 and (crt.key% or crt.data% < 32) then \
                        print using crt.using$; fn.crt.sca$(crt.row%, \
                                crt.column%+crt.loop%+crt.temp.back%); \
                                crt.mult.backspaces$(crt.temp.back%)
                if crt.data% = 7fh      \
                  then  crt.data% = 8
                if crt.data% < 32 and crt.data% <> 8 and not crt.key% \
                  then  crt.flag% = crt.false% :        \
                        crt.end.char% = crt.data%
                if crt.data% = 8        \
                         and crt.loop% > 0      \
                  then  crt.loop% = crt.loop% - 1 :     \
                        crt.data$ = left$(crt.data$,crt.loop%)  :       \
                        print using crt.using$; \
                                fn.crt.sca$(crt.row%,crt.column%+len(crt.data$)); \
                                " ";crt.backspace$
                if crt.data% >= 32 and crt.data% <> crt.key.prefix%     \
                  then  crt.data$ = crt.data$ + chr$(crt.data%) :       \
                        crt.field.modified% = crt.true% :       \
                        crt.loop% = crt.loop% + 1
                if crt.warning.limit% > 0       \
                        and crt.alarm$ <> ""            \
                        and crt.loop% = crt.warning.limit%      \
                  then  print crt.msg.header$;  \
                                crt.alarm$;     \
                                crt.msg.trailer$;        \
                                crt.foreground$         : \
                        print fn.crt.sca$ (crt.row%, crt.column% + crt.loop%)
                if crt.loop% >= crt.limit%      \
                  then  crt.flag% = crt.false% :        \
                        crt.end.char% = 0dh
                wend
        crt.warning.limit% = 0
        if crt.data$ = ""       \
                and crt.end.char% = 0dh \
          then  crt.end.char% = 0
        if crt.data$ = ""       \
          then  fn.crt.input$ = ""      \
          else  fn.crt.input$ = crt.data$
        return
        fend
rem
rem--------------------------------------------------------------------------
rem
rem     fn.crt.display.data%            write data into CRT display field
rem
rem     parameters:     crt.field% - field number
rem                     crt.field$      - field contents
rem
rem     return:         none
rem
rem----------------------------------------------------------------------------
rem
   def fn.crt.display.data% (field$,field%)
        crt.buffer$ (field%) = field$
        print using crt.using$; \
                fn.crt.sca$(crt.format.fields%(field%,0),       \
                        crt.format.fields%(field%,1));  \
                crt.foreground$;
        on crt.format.fields%(field%,3) \
                        gosub   50005.1,        \ character
                                50005.2,        \ integer
                                50005.3         rem monetary
        print using crt.using$;crt.background$
        return
50005.1 rem character data
        crt.field$=left$(field$+crt.blank$, \
                crt.format.fields%(field%,2))
        print crt.field$;
        return
50005.2 rem     integer data
        crt.tmp$=right$(crt.format$, \
                crt.digits%(crt.format.fields%(field%,2)))
        print using crt.tmp$;val(field$);
        return
50005.3 \       monetary data
        crt.num = val(field$)
        crt.len% = crt.digits%(crt.format.fields%(field%,2)-3)+5
        crt.temp.fmt$=right$(crt.format$, \
                crt.digits%(len(str$(abs(int(crt.num))))))+".##"
        if crt.num < 0  \
                then  crt.temp.fmt$ = "<"+crt.temp.fmt$+">"  \
                else  crt.temp.fmt$ = " "+crt.temp.fmt$+" "
        crt.temp.fmt$=right$(crt.blank$+crt.temp.fmt$, crt.len%)
        print using crt.temp.fmt$; abs(crt.num);
        return
        fend
rem----------------------------------------------------------------------------
rem
rem             AI-80 Display Management System
rem
rem             Miscellaneous Interface Functions
rem
rem----------------------------------------------------------------------------
rem
rem     copyright l978  -       Arkenstone, Inc.
rem                             785 Market St.	Suite 515
rem                             San Francisco, Ca. 94103
rem                             (415)-957-1468
rem
rem----------------------------------------------------------------------------
rem
rem
rem--------------------------------------------------------------------------
rem
rem     fn.crt.display.background%      display fixed (or background) portion
rem                                     of CRT display screen
rem
rem                                     note: the entire screen will be cleared
rem                                             by this operation
rem
rem----------------------------------------------------------------------------
rem
   def fn.crt.display.background%
        console
        for crt.loop% = 1 to crt.buffer.count%
                print using crt.using$; \
                         crt.screen.buffer$(crt.loop%)
                next
        print using crt.using$; \
                fn.crt.sca$ (crt.format.fields%(1,0),crt.format.fields%(1,1))
        return
        fend
rem
rem---------------------------------------------------------------------------
rem
rem     fn.crt.clear.data%      clear all foreground data fields
rem
rem---------------------------------------------------------------------------
rem
   def fn.crt.clear.data%
        console
        for crt.loop% = 1 to crt.field.count%
                crt.buffer$ (crt.loop%) = ""
                next
        if crt.clear.foreground$ <> ""  \
          then  print using crt.using$;crt.clear.foreground$: return
        for crt.loop% = 1 to crt.field.count%
                crt.len%=crt.format.fields%(crt.loop%,2)
                if crt.format.fields%(crt.loop%,3) = 2  then \
                        crt.len%=crt.digits%(crt.len%)
                if crt.format.fields%(crt.loop%,3) = 3  then \
                        crt.len%=crt.digits%(crt.len%-3)+5
                print using crt.using$; \
                        fn.crt.sca$ (crt.format.fields%(crt.loop%,0), \
                                  crt.format.fields%(crt.loop%,1)); \
                        left$ (crt.blank$, crt.len%)
                next
        return
        fend
rem
rem--------------------------------------------------------------------------
rem
rem     fn.crt.refresh.data%    re-display all foreground data fields
rem
rem--------------------------------------------------------------------------
rem
   def fn.crt.refresh.data%
        console
        for crt.loop% = 1 to crt.field.count%
                crt.dummy% = fn.crt.display.data% (crt.buffer$(crt.loop%),crt.loop%)
                next
        return
        fend

