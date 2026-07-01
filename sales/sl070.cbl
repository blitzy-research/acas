       >>source free
*>**********************************************************
*>                                                         *
*>            Product  Analysis  File  Maintenance         *
*>                                                         *
*>**********************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl070.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM 16/04/84
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.
*>                        acas013  ->
*>                         valueMT.
*>                        acas015  ->
*>                         analMT.
*>**
*>    Error messages used.
*>                        SL008
*>                        SL009
*>                        SL010
*>                        SL011
*>                        SLA12
*>                        SLA13
*>                        SLA14
*>**
*>
*>    Changes.
*> 31/03/84 Vbc - On Pa Setup Create Standard Va-Codes.
*> 03/05/84 Vbc - On Pa Setup Create Value File.
*> 31/05/84 Vbc - Support Graphic Screen.
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 03/03/09 vbc - Support long screens.
*> 02/06/09 vbc - A warning if any PA codes contain zero as a GL number.
*> 25/11/11 vbc - .07 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .08 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .09 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 12/05/13 vbc - .10 Force setup of Default group a, a1 for sales and purchases
*>                    as std codes.
*> 18/05/13 vbc - .11 Support for direct call from Stock to create default PA codes.
*> 24/07/16 vbc - .12 Support for RDB processing. at least for the analysis file/table...
*> 24/10/16 vbc - .13 ALL programs now using wsnames.cob in copybooks
*> 30/10/16 vbc - .14 Remove references to File-Status - discontinued.
*>                    Support for RDB value & Analysis records with file proc dropped.
*> 15/01/17 vbc - .15 All programs upgraded to v3.02 for RDB processing.
*>                    Removed refs to maps99.
*> 23/01/17 vbc       Dry testing completed.
*> 05/03/18 vbc - .16 Clean up error msgs removing the !! from ends and remove 'MT'
*>                    as usage of file may be in use.
*> 08/04/18 vbc - .17 Support for call by ACAS on init. system use where ws-Process-Func = 1.
*> 29/04/18 vbc - .18 Make zeroed GL values zero and not blank when
*>                    printing GL fields  giving all 6 GL A/C digits.
*> 03/04/23 vbc - .19 Change printer FD from 132 to 80 - same as pl070.
*> 04/05/23 vbc       Added some comment entries.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 18/01/25 vbc - .20 On tests for Value FS-Reply = 21 also test for 23 - JIC
*>                    Analysis will create for both Sales and Purchases.
*>                    Do same for pl070.
*> 24/08/25 vbc   .21 Minor adjusts for heads. Ditto pl070.
*>                    Make warnngs of zero a/c entries the same - PL & SL.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> These files and programs is part of the Applewood Computers Accounting
*> System and is copyright (c) Vincent B Coen. 1976-2026 and later.
*>
*> This program is now free software; you can redistribute it and/or modify it
*> under the terms of the GNU General Public License as published by the
*> Free Software Foundation; version 3 and later as revised for personal
*> usage only and that includes for use within a business but without
*> repackaging or for Resale in any way.
*>
*> Persons interested in repackaging, redevelopment for the purpose of resale or
*> distribution in a rental mode must get in touch with the copyright holder
*> with your commercial plans and proposals.
*>
*> ACAS is distributed in the hope that it will be useful, but WITHOUT
*> ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
*> FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
*> for more details. If it breaks, you own both pieces but I will endeavour
*> to fix it, providing you tell me about the problem.
*>
*> You should have received a copy of the GNU General Public License along
*> with ACAS; see the file COPYING.  If not, write to the Free Software
*> Foundation, 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
*>
*>*************************************************************************
*>
 environment             division.
*>===============================
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
*> copy "selanal.cob".
*> copy "selval.cob".
 copy "selprint.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdanal.cob".
*> copy "fdval.cob".
*>
 fd  print-file.
*>
 01  print-record            pic x(80).
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL070 (3.3.00)".
 copy "print-spool-command-p.cob".
 copy "wsfnctn.cob".
 copy "wsanal.cob".
 copy "wsval.cob".
*>
 01  ws-data.
     03  menu-reply      pic 9.
     03  ws-reply        pic x.
     03  a               pic 99.
     03  ws-err-flag     pic 9           value zero.
     03  Escape-Code     pic x.
     03  Print-Mode      pic x           value space.
         88  Print-All                   value "A".
     03  save-code       pic xxx.
     03  line-cnt        pic 99   comp  value zero.
*>
     03  ws-env-lines    pic 999       value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-21-lines     binary-char unsigned value zero.
     03  ws-20-lines     binary-char unsigned value zero.
     03  ws-19-lines     binary-char unsigned value zero.
     03  ws-18-lines     binary-char unsigned value zero.
     03  ws-17-lines     binary-char unsigned value zero.
*>
 01  ws-Test-Date            pic x(10).
 01  ws-date-formats.
     03  ws-swap             pic xx.
     03  ws-Conv-Date        pic x(10).
     03  ws-date             pic x(10).
     03  ws-UK redefines ws-date.
         05  ws-days         pic xx.
         05  filler          pic x.
         05  ws-month        pic xx.
         05  filler          pic x.
         05  ws-year         pic x(4).
     03  ws-USA redefines ws-date.
         05  ws-usa-month    pic xx.
         05  filler          pic x.
         05  ws-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  ws-Intl redefines ws-date.
         05  ws-intl-year    pic x(4).
         05  filler          pic x.
         05  ws-intl-month   pic xx.
         05  filler          pic x.
         05  ws-intl-days    pic xx.
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
     03  WS-Stock-Record        pic x.
     03  WS-Sales-Record        pic x.
*>     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
*>     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  File-Info                          value zero.
     05 File-Size-Bytes  pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp.
     05 Mod-MO           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp.
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp. *> Always 00
*>
 01  Error-Messages.
*> System Wide
     03  SL008          pic x(30) value "SL008 P.A. Code Already Exists".
     03  SL009          pic x(36) value "SL009 P.A. Group Code Does Not Exist".
     03  SL010          pic x(43) value "SL010 P.A. Group Code Used As Analysis Code".
     03  SL011          pic x(30) value "SL011 P.A. Code Does Not Exist".
     03  SLA12          pic x(31) value "SLA12 Error on Anal processing".
     03  SLA13          pic x(25) value "SLA13 Hit return for Menu".
     03  SLA14          pic x(32) value "SLA14 Error on Value processing".
*> Module specific
*>       NONE
*>
 01  Error-Code          pic 999.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  line-1.   *> 78
     03  l1-version      pic x(31)       value spaces.
     03  filler          pic x(39)       value "Product Analysis Codes".
     03  filler          pic x(5)        value "Page ".
     03  l1-page         pic zz9.
*>
 01  line-2.   *> 78
     03  l2-user         pic x(30)       value spaces.
     03  filler          pic x(38)       value spaces.
     03  l2-date         pic x(10).
*>
 01  line-4.
     03  l5-led-lit      pic x(4)        value "Lgr".
     03  filler          pic x(59)       value "Code    GL.No.       <-----Description------>  Print".
     03  filler          pic x(6)        value  "-Type-".
*>
 01  line-6.
     03  filler          pic x           value space.
     03  l6-ledger       pic x           value spaces.
     03  filler          pic xxx         value space.
     03  l6-code         pic x(7).
     03  l6-gl           pic 9(6).
     03  filler          pic x(7)        value spaces.
     03  l6-desc         pic x(24)       value spaces.
     03  filler          pic x(4)        value spaces.
     03  l6-print        pic xxx.
     03  filler          pic x(7)        value spaces.
     03  l6-type         pic x(6).
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  to-day              pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 init01 section.
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines   to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-23-lines.
     subtract 2 from ws-lines giving ws-22-lines.
     subtract 3 from ws-lines giving ws-21-lines.
     subtract 4 from ws-lines giving ws-20-lines.
     subtract 5 from ws-lines giving ws-19-lines.
     subtract 6 from ws-lines giving ws-18-lines.
     subtract 7 from ws-lines giving ws-17-lines.
     move     prog-name to l1-version.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
     move     1 to File-Key-No.
*>
 *>    if       ws-Process-Func not = 1   *> Not Called by Stock or ACAS
 *>             display  " " at 0101 with erase eos.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15     *> anal
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    perform  P-A-Setup  *> Create default entries in Analysis and Value files
              end-if                    *> for Sales and Purchases
     end-if
     if       ws-Process-Func = 1       *> Called by Stock or ACAS to Create
              go to Menu-Exit.          *> default entries  so we are done
*>
 menu-return.
     move     zero  to  menu-reply.
     perform  display-heading.
*>
 menu-input.
     display  "Select one of the following by number :- [ ]" at 0701 with foreground-color 2.
     display  "(1)  Set-up P/A records" at 1004       with foreground-color 2.
     display  "(2)  Amend/Delete P/A records" at 1204 with foreground-color 2.
     display  "(3)  Print P/A records" at 1404        with foreground-color 2.
     display  "(4)  Print All P/A records" at 1604    with foreground-color 2.
     display  "(5)  Display P/A records" at 1804      with foreground-color 2.
     display  "(9)  Return to system menu" at 2004    with foreground-color 2.
*>
     accept   menu-reply at 0743 with foreground-color 6 update auto.
*>
     if       menu-reply = 9
              go to  Menu-Exit.
     if       menu-reply  <  1  or  >  5
              go to  menu-input.
     perform  display-heading.
     if       menu-reply = 1
              perform  Create.
     if       menu-reply = 2
              perform  Amend.
     if       menu-reply = 3
              move spaces to l5-led-lit
              perform  Report1.
     if       menu-reply = 4
              move "Lgr" to l5-led-lit
              move "A" to Print-Mode
              perform  Report1.
     if       menu-reply = 5
              perform  Show.
     go       to menu-return.
*>
 aa101-Check-4-Errors.                       *> Analysis-Record - if any errors then msgs and exit module
     if       FS-Reply not = zero
              display SLA12            at 0601 with erase eos  *> acas015/analMT processing
              display "FS-Reply = "    at 0701
              display FS-Reply         at 0712
*>
              display "Keys = "        at 0720
              display va-code          at 0727
*>
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
 *>             if      FS-RDBMS-Used
 *>                     perform aa020-Rollback
 *>             end-if
              display SLA13 at 1101 with erase eol
              accept  Accept-Reply at 1135
              go to  Menu-Exit
     end-if.
*>
 aa102-Check-4-Errors.                       *> Value-Record - if any errors then msgs and exit module
     if       FS-Reply not = zero
              display SLA14            at 0601 with erase eos  *> acas013/valueMT processing
              display "FS-Reply = "    at 0701
              display FS-Reply         at 0712
*>
              display "Keys = "        at 0720
              display WS-Pa-Code       at 0727
*>
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
 *>             if      FS-RDBMS-Used
 *>                     perform aa020-Rollback
 *>             end-if
              display SLA13 at 1101 with erase eol
              accept  Accept-Reply at 1135
              go to  Menu-Exit
     end-if.
*>
 Menu-Exit.
     goback.
*>
*>****************************************************************
*>      P R O C E D U R E S                                      *
*>****************************************************************
*>
 Create       section.
*>===================
*>
     perform  Analysis-Open.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
 product-input.
     perform  display-outline.
     move     6  to  lin.
*>
 product-loop.
     move     spaces  to  pa-group.
     move     2 to cole.
     accept   pa-group at curs with foreground-color 3 update.
     if       pa-group = spaces
              go to  main-end.
*>
     move     "S" to pa-system.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.    *> read analysis-file not invalid key
     if       FS-Reply not = 21 and not = 23
              perform  product-display  of  Show
              display  SL008 at line ws-23-lines col 01 with foreground-color 3
              go       to product-loop.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
     move     WS-PA-Code  to  save-code.
     if       pa-second = space
              go to  get-details.
*>
     move     space    to  pa-second.
*>
     perform  Analysis-Read-Indexed. *> read analysis-file invalid key
     if       FS-Reply = 21 or = 23
              display  SL009 at line ws-23-lines col 01 with foreground-color 3
              go to  product-loop.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
     if       pa-gl not = zero
              display  SL010 at line ws-23-lines col 01 with foreground-color 3
              go to  product-loop.
     display  " " at line ws-23-lines col 01 with erase eol.
*>
 get-details.
     move     save-code  to  WS-PA-Code.
     move     zero       to  pa-gl.
     move     spaces     to  pa-desc.
*>
     perform  analysis-data.
*>
     move     "S"  to   Escape-Code.
     display  Escape-Code at line ws-18-lines col 77  with foreground-color 6.
     accept   Escape-Code at line ws-18-lines col 77  with foreground-color 6 update UPPER.
*>
 main-output.
     if       Escape-Code = "B"
              perform  get-pa-desc of analysis-data through  main-exit of analysis-data.
*>
     if       Escape-Code = "Q" or "K"
              go to  main-end.
*>
     perform  Analysis-Write.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
     add      1  to  lin.
*>
     if       lin  >  ws-22-lines
              perform  display-outline
              move  6  to  lin.
     go       to product-loop.
*>
 main-end.
     perform  Analysis-Close.
*>
 main-exit.   exit section.
*>
 Amend        section.
*>===================
*>
     perform  Analysis-Open.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
 product-input.
     perform  display-outline.
     move     6  to  lin.
*>
 product-loop.
     move     2 to cole.
     move     spaces to pa-group.
     accept   pa-group at curs with foreground-color 3 update.
     if       pa-group = spaces
              go to  main-end.
*>
     move     "S" to pa-system.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed. *> read analysis-file  invalid key
     if       FS-Reply = 21 or = 23
              display  SL009 at line ws-23-lines col 01 with foreground-color 3
              go to  product-loop.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
     display  " " at line ws-23-lines col 1 with erase eol.
     perform  product-display  of  Show.
*>
 get-details.
     perform  analysis-data.
*>
     move     "S"  to   Escape-Code.
     display  Escape-Code at line ws-18-lines col 77  with foreground-color 6.
     accept   Escape-Code at line ws-18-lines col 77  with foreground-color 6 update UPPER.
*>
 main-output.
     if       Escape-Code = "B"
              perform  get-pa-desc of analysis-data  through  main-exit of analysis-data.
*>
     if       Escape-Code = "Q"
              go to    main-end.
*>
     if       Escape-Code = "K"
              move     1 to File-Key-No
              perform  Analysis-Delete
              if       FS-Reply not = zero
                       perform  aa101-Check-4-Errors
              end-if
     else
              perform  Analysis-Rewrite
              if       FS-Reply not = zero
                       perform  aa101-Check-4-Errors
              end-if
     end-if
*>
     add      1  to  lin.
     if       lin  >  ws-21-lines
              perform  display-outline
              move  6  to  lin.
     go to    product-loop.
*>
 main-end.
     perform  Analysis-Close.
*>
 main-exit.   exit section.
*>
 Report1      section.
*>===================
*>
     perform  Analysis-Open-Input.
     open     output  print-file.
     move     zero  to  a.
     perform  headings.
*>
 read-loop.
     perform  Analysis-Read-Next.
     if       FS-Reply = 10
              go to  end-report.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
*> AS PA-SYSTEM = P or S therefore 1st time read of S is eof for
*>  logical end of purchase records.  Do ALL Ledgers
*>
     if       pa-system not = "S"
        and   not Print-All
              go to read-loop.
*>
     if       pa-second = space
       and    pa-gl = zero
              move  spaces  to  print-record
              write print-record after 1
              add 1 to line-cnt
              move  "Group"  to  l6-type
              if  Print-All
                  move pa-system to l6-ledger
              end-if
     else
              move  "Detail" to  l6-type
              move space to l6-ledger
     end-if
     if       line-cnt > 70
              perform headings.
*>
     if       pa-second not = spaces
         and  pa-gl = zero
              move 1 to ws-err-flag.
     move     pa-group to  l6-code.
     move     pa-gl to l6-gl.
     move     pa-desc  to  l6-desc.
     move     pa-print  to  l6-print.
*>
     write    print-record  from  line-6 after 1.
     add      1 to line-cnt.
     if       line-cnt > 70
              perform  headings.
*>
     go       to read-loop.
*>
 headings.
     add      1  to  a.
     move     a  to  l1-page.
     perform  zz070-Convert-Date.
     move     ws-date to l2-date.
     move     usera to  l2-user.
*>
     if       a not = 1
              write print-record from line-1 after page
              move spaces to print-record
              write print-record after 1
     else
              write print-record from line-1 before 1.
     write    print-record  from  line-2 after 1.
     write    print-record  from  line-4 after 2.
     move     5 to line-cnt.
*>
 end-report.
     if       ws-err-flag not = zero
              move "Warning: One or more P.A. codes contain a zero value for IRS or GL numbers"
                              to print-record
              write print-record after 2.
*>
 main-end.
     close    print-file.
     perform  Analysis-Close.
     call     "SYSTEM" using Print-Report.
*>
 main-exit.   exit section.
*>
 Show         section.
*>===================
*>
     perform  Analysis-Open-Input.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
     move     6  to  lin.
     perform  display-outline.
     move     6  to  lin.
     display  "Enter <X> to exit or <Return> to continue...[ ]"  at line ws-23-lines col 31 with foreground-color 2.
*>
 Show-read.
     if       lin > ws-21-lines
              go to main-end.
*>
 sread.
     perform  Analysis-Read-Next.
     if       FS-Reply = 10
              move ws-lines  to  lin
              go to  accept-of-show.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
*> AS PA-SYSTEM = P or S therefore 1st time read of S is eof for
*>  logical end of purchase records.
*>
     if       pa-system not = "S"
              go to sread.
*>
*>  Above is different in PL070 re: ws-lines to lin
*>
 product-display.
     move     2 to cole.
     display  pa-group at curs with foreground-color 3.
     move     8 to cole.
     display  pa-gl at curs with foreground-color 3.
     move     20 to cole.
     display  pa-desc at curs with foreground-color 3.
*>
     if       pa-second = space
       and    pa-gl = zero
              move "Group"  to l6-type
     else
              move "Detail" to l6-type.
     move     48 to cole.
     display  pa-print at curs with foreground-color 3.
     move     55 to cole.
     display  l6-type at curs with foreground-color 3.
*>
 accept-of-show.
     add      1  to  lin.
     if       lin  <  ws-22-lines
              go to  Show-read.
*>
     accept   ws-reply at line ws-23-lines col 76  with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
     if       lin > ws-23-lines
              go to main-end.
     if       ws-reply not = "X"
              perform display-outline
              move 6 to lin
              go to Show-read.
*>
 main-end.
     perform  Analysis-Close.
*>
 main-exit.   exit section.
*>
*>****************************************************************
*>       S E R V I C E    R O U T I N E S                        *
*>****************************************************************
*>
 display-heading         section.
*>==============================
*>
     display  prog-name at 0101 with erase eos foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
*>
     if       menu-reply =  0
              display "Product Analysis File Set-Up & Maintenance" at 0120 with foreground-color 2
              display "Function  Menu" at 0434         with foreground-color 2.
*>
     if       menu-reply =  1
              display "Set-Up P/A Records" at 0132     with foreground-color 2.
*>
     if       menu-reply =  2
              display "Amend/Delete P/A Records" at 0129 with foreground-color 2.
*>
     if       menu-reply =  3
              display "Print P/A Records" at 0132  with foreground-color 2.
*>
     if       menu-reply = 4
              display "Print All P/A Records" at 0132 with foreground-color 2.
*>
     if       menu-reply =  5
              display "Display P/A Records" at 0131 with foreground-color 2.
*>
 main-exit.   exit section.
*>
 display-outline         section.
*>==============================
*>
     display  "Code   G/L Nos          Description" at 0401  with foreground-color 2.
     display  "Ref" at 0448 with foreground-color 2.
     display  "Type" at 0456 with foreground-color 2.
     move     6 to lin.
     move     1 to cole.
*>
 main-loop.
     display  "[  ]  [      ]    [                        ]  [   ]          " at curs with foreground-color 2.
*>
     add      1  to  lin.
     if       lin < ws-23-lines
              go to  main-loop.
*>
     if       menu-reply not = 5
              display "*******************" at line ws-17-lines col 62 with foreground-color 2
              display "*" at line ws-18-lines col 62  with foreground-color 2
              display "*" at line ws-18-lines col 80  with foreground-color 2
              display "*" at line ws-19-lines col 62  with foreground-color 2
              display "*" at line ws-19-lines col 80  with foreground-color 2
              display "*" at line ws-20-lines col 62  with foreground-color 2
              display "*" at line ws-20-lines col 80  with foreground-color 2
              display "*" at line ws-21-lines col 62  with foreground-color 2
              display "*" at line ws-21-lines col 80  with foreground-color 2
              display "*" at line ws-22-lines col 62  with foreground-color 2
              display "*" at line ws-22-lines col 80  with foreground-color 2
              display "*******************"  at line ws-23-lines col 62 with foreground-color 2.
*>
     if       menu-reply not = 5
              display "Escape Code [ ]" at line ws-18-lines col 64 with foreground-color 2
              display "<B> = Back" at line ws-19-lines col 64      with foreground-color 2
              display "<S> = Save" at line ws-20-lines col 64      with foreground-color 2
              display "<Q> = Quit" at line ws-21-lines col 64      with foreground-color 2
              display "<K> = Deleted" at line ws-22-lines col 64   with foreground-color 2.
*>
 main-exit.   exit section.
*>
 analysis-data           section.
*>==============================
*>
     move     8 to cole.
     accept   pa-gl at curs with foreground-color 3 update.
*>
 get-pa-desc.
     move     20 to cole.
     accept   pa-desc  at curs with foreground-color 3 update.
*>
 get-pa-print.
     if       menu-reply = 1
              move  pa-group to  pa-print.
     move     48 to cole.
     accept   pa-print at curs with foreground-color 3 update.
*>
 main-exit.   exit section.
*>
 P-A-Setup               section.
*>==============================
*>
*> Create default entries for Analysis and Value files on Sales and Purchases
*>
     perform  Value-Open.
     perform  Analysis-Open-Output.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*> SALES
     move     zeros  to pa-gl.
     move     spaces to pa-print.
     move     "S" to pa-system.
     move     "v " to pa-group.
     move     "VAT Control" to pa-desc.
     perform  create-value.
     move     "vi" to pa-group.
     move     "VAT Input Invoices/CN's" to pa-desc.
     perform  create-value.
     move     "vj" to pa-group.
     move     "VAT Input Receipts" to pa-desc.
     perform  create-value.
     move     "z " to pa-group.
     move     "Computer Control" to pa-desc.
     perform  create-value.
     move     "zc" to pa-group.
     move     "Sales Carriage Charges" to pa-desc.
     move     "P&P"   to pa-print.
     perform  create-value.
     move     "zd" to pa-group.
     move     "Sales Late Charges" to pa-desc.
     move     "LCG"   to pa-print.
     perform  create-value.
     move     "vo" to pa-group.
     move     spaces   to pa-print.
     move     "VAT Output Invoices/CN's" to pa-desc.
     perform  create-value.
     move     "vp" to pa-group.
     move     "VAT Output Receipts" to pa-desc.
     perform  create-value.
     move     "a " to pa-group.
     move     "Default Group" to pa-desc.
     perform  create-value.
     move     "a1" to pa-group.
     move     "Default Sales" to pa-desc.
     perform  create-value.
*>
*> PURCHASE
*>
     move     "P" to pa-system.
     move     "za" to pa-group.
     move     "Purch Carriage Charges" to pa-desc.
     move     "P&P"   to pa-print.
     perform  create-value.
     move     "zb" to pa-group.
     move     "Purch Late Charges" to pa-desc.
     move     "LCG"   to pa-print.
     perform  create-value.
     move     spaces  to pa-print.
     move     "a " to pa-group.
     move     "Default Group" to pa-desc.
     perform  create-value.
     move     "a1" to pa-group.
     move     "Default Purchases" to pa-desc.
     perform  create-value.
     move     "a2" to PA-Group.
     move     "Purch for Stock" to pa-desc.
     perform  create-value.
     move     "a3" to PA-Group.
     move     "Purch for Office Furnit"  to pa-desc.
     perform  create-value.
     move     "a4" to PA-Group.
     move     "Purch for Office Consum"  to pa-desc.
     perform  create-value.
     move     "a5" to PA-Group.
     move     "Purch for Office Equipmt" to pa-desc.
     perform  create-value.
     move     "a6" to PA-Group.
     move     "Purch for Office Autos"   to pa-desc.
     perform  create-value.
     move     "a7" to PA-Group.
     move     "Purch for Travel" to pa-desc.
     perform  create-value.
*>
     perform  Value-Close.
     perform  Analysis-Close.
*>
     if       ws-Process-Func not = 1
              display  " " at line ws-23-lines col 01 with erase eol.
     go       to main-exit.
*>
 Create-Value.
*>
     move     WS-PA-Code to VA-Code.
*>     read     value-file invalid key
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.
     if       FS-Reply = 21 or = 23
              move WS-Analysis-Record to WS-Value-Record
              move zero to VA-V-This va-v-last VA-V-Year
                           VA-T-This VA-T-Last VA-T-Year
              perform  Value-Write
              if       FS-Reply not = zero
                       perform  aa102-Check-4-Errors
              end-if
     end-if
*>
     perform  Analysis-Write.
     if       FS-Reply not = zero
              perform  aa101-Check-4-Errors.
*>
 main-exit.   exit section.
*>
 zz070-Convert-Date        section.
*>********************************
*>
*>  Converts date in to-day to UK/USA/Intl date format
*>****************************************************
*> Input:   to-day
*> output:  ws-date as uk/US/Inlt date format
*>
     move     to-day to ws-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     to-day (7:4) to ws-Intl-Year.
     move     to-day (4:2) to ws-Intl-Month.
     move     to-day (1:2) to ws-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
