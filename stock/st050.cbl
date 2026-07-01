       >>source free
*>*************************************************************
*>                                                            *
*>            Stock Control File Compression                  *
*>                                                            *
*> This recreates the indexed Stock file ignoring deleted     *
*>      records and is not normally used except for           *
*>   maybe yearly or if a large number of items are deleted   *
*>    from the system which has a lot of items.               *
*>############################################################*
*>  Note that the program tests that the file record lengths  *
*>     are the same for both temp file and the stock file and *
*>     will produce a fatal error msg if not the same.        *
*>                                                            *
*>  This process will zeroise all of :
*>     Stock-Construct-Bundle
*>     Stock-Under-Construction
*>     Stock-Work-in-Progress
*>     Stock-Adds
*>     Stock-Deducts
*>     Stock-Wip-Adds
*>     Stock-Wip-Deds
*>     Stock-Last-Actual-Cost.
*>      and with C 1 through 12
*>         Stock-TD-Adds (C)
*>         Stock-TD-Deds (C)
*>         Stock-TD-Wip-Adds (C)
*>         Stock-TD-Wip-Deds (C)
*>  and do a compute  Stock-Value = Stock-Held * Stock-Cost.
*>  SO YOU SHOULD ONLY RUN AT END OF YEAR.
*>
*>*************************************************************
*>    This program is only for the Cobol Stock file and not   *
*>      for use with the RDB database system as RDB normal    *
*>      housekeeping takes care of such tasks.                *
*>                                                            *
*>  Therefore a test is made to check that the system param   *
*> File-System-Used = 0 or status FS-Cobol-Files-Used is true *
*>       otherwise it stops.                                  *
*>*************************************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         st050.
*>**
*>    Author.             V.B.Coen, FBCS
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Called modules.
*>                        acas011 -> Stock file FH
*>                         stockMT - STOCK-REC RDB table.
*>**
*>    Error messages used.
*>
*>                        ST000.
*>                        ST003.
*>
*>                        ST501.
*>                        ST502.
*>                        ST503.
*>                        ST504.
*>                        ST505.
*>                        ST506.
*>                        ST507.
*>**
*> Changes:
*> 29/06/09 vbc - .00 Written in Cobol from scratch against v2 specs.
*> 07/09/10 vbc - .00 Added notes with prog description above.
*> 27/11/11 vbc - .01 Added extra tests and display if errors found during
*>                    file processing, also added open/close on temp file
*>                    BUT remd out until testing complete <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
*> 11/12/11 vbc -     Changed version from 1.00.xx to 3.01.xx, in keeping with the rest of ACAS
*>                .02 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 12/05/13 vbc - .03 Changed wsnames to in common as pl010 called in st010.
*> 14/05/13 vbc - .04 Support for File recovery from existing temp file.
*> 16/05/13 vbc - .05 Changed wsnames to in copybook see above.
*> 22/05/13 vbc - .06 Added a stock value comp during process.
*> 21/07/16 vbc - .07 Test to ensure that Cobol files are used.
*>                    Added message ST507 if no cobol files and as this
*>                    program is NOT needed for RDB so it has Cobol file I/O only.
*> 24/10/16 vbc - .08 ALL programs now using wsnames.cob in copybooks.
*> 13/03/18 vbc - .09 Re comment for .07 made st050 use FH to standardise.
*>                    Removed unused field WS var. error-code.
*>                    Chg ST000 to stock rec.
*> 27/06/20 vbc - .10 Zeroes to WIP 9(6) fields on stock file.
*>                    fix bug on ba00 recovery with next after goto not skipped.
*>                    Add finish msg with totals displayed for both passes.
*> 08/12/22 vbc - .11 Chgd goto in ba000 to use para -Main 4 GC v3.2 warning.
*> 16/08/23 vbc       Remove remarked out old Cobol File verbs.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/12/24 vbc       Change ACCEPT X to force UPPER & remove function upper-case
*>                    in 2 instances.
*> 04/02/25 vbc - .12 Extra warning display before proceding regarding cleardown
*>                       on TD and other fields.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 2024-04-16.
*>
*> These files and programs are part of the Applewood Computers Accounting
*> System and is Copyright (c) Vincent B Coen. 1976-2026 and later.
*>
*> This program is now free software; you can redistribute it and/or modify it
*> under the terms listed here and of the GNU General Public License as
*> published by the Free Software Foundation; version 3 and later as revised
*> for PERSONAL USAGE ONLY and that includes for use within a business but
*> EXCLUDES repackaging or for Resale, Rental or Hire in ANY way.
*>
*> Persons interested in repackaging, redevelopment for the purpose of resale or
*> distribution in a rental or hire mode must get in touch with the copyright
*> holder with your commercial plans and proposals.
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
*>================================
*>
 copy "envdiv.cob".
 input-output            section.
*>-------------------------------
*>
 file-control.
*>------------
*>
     select   Temp-Stock-File      assign  file-9
                                   access  sequential
                                   status  fs-reply.

 data                    division.
*>================================
*>
 file section.
*>------------
*>
 fd  Temp-Stock-File.
 01  Temp-Stock-Record.
     03  filler          pic x(400).
*>
 working-storage section.
*>-----------------------
*>
 77  Prog-Name           pic x(15)       value "ST050 (3.3.00)".
 77  Eval-Msg            pic x(25)       value spaces.
*>
 01  work-fields.
     03  ws-Reply        pic x                   value space.
     03  ws-Recovery     pic x                   value "N".
     03  a               pic 9999.
     03  b               pic 9999.
     03  c               pic 9(4).
     03  ws-lines        binary-char  unsigned   value zero.
     03  ws-22-lines     binary-char  unsigned   value zero.
     03  ws-23-lines     binary-char  unsigned   value zero.
     03  ws-env-lines    pic 999                 value zero.
*>
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
 copy "wsfnctn.cob".
 copy "wsstock.cob".     *> 3.02
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
*>     03  System-Record          pic x.
     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
*>     03  WS-Stock-Record        pic x.
     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
*>
 01  Error-Messages.
     03  ST000          pic x(36) value "ST000 Error on Writing to Stock Rec.".
     03  ST003          pic x(27) value "ST003 Press return for Menu".
*> Module specific
     03  ST501          pic x(26) value "ST501 Stock File not found".
     03  ST502          pic x(17) value "ST502 Y or N only".
     03  ST503          pic x(29) value "ST503 Error opening temp file".
     03  ST504          pic x(32) value "ST504 Error writing to temp file".
     03  ST505          pic x(55) value "ST505 Error: Length of Stock File not same as Temp File".
     03  ST506          pic x(30) value "ST506 Error opening Stock File".
     03  ST507          pic x(47) value "ST507 Cobol Files not used, only RDB - Aborting".
*>
 01  Error-Code         pic 999    value zero.
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
 01  To-Day             pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 aa000-Core                 section.
*>*********************************
*>
     accept   ws-env-lines from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-23-lines.
     subtract 2 from ws-lines giving ws-22-lines.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
*> Get current date into locale format for display
*>
     perform  zz070-Convert-Date.
     move     ws-Date to ws-Conv-Date.
*>
*>  Check that Stock file record length is same as Temp file layout
*>      if not program, MUST be changed to fix and recompiled
*>
     move     function length (WS-Stock-Record) to a.
     move     function length (Temp-Stock-Record) to b.
     if       a not = b
              display " " at 0401 with erase eos
              display ST505 at 0401 with foreground-color 4 highlight
              display "Stock File = " at 0601 with foreground-color 2
              display a at 0614 with foreground-color 2 highlight
              display "Temp  File = " at 0701 with foreground-color 2
              display b     at 0714 with foreground-color 2 highlight
              display ST003 at 0801
              accept ws-reply at 0830
              go to aa999-Exit.
*>
     if       not FS-Cobol-Files-Used                  *> dup processing now removed as redundant.
              display ST507   at 0101 with foreground-color 2 erase eos
              display " "     at 0201
              display ST003   at 0301
              accept ws-reply at 0330
              go to aa999-Exit.
*>
 aa010-Questions.
     move     zero to a b.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock Compression Utility" at 0128 with foreground-color 2.
     display  ws-Conv-Date at 0171 with foreground-color 2.
     display  "Not needed for RDBMS processing  !" at 0310  with foreground-color 4 highlight.
     display  "This process will clean up the Stock File of deleted records"       at 0410 with foreground-color 2.
     display  "Is this a recovery from a previous run of this process - [ ] (N/Y)" at 0610 with foreground-color 2.
*>
 aa020-Recovery.
     move     "N" to ws-Recovery.
     accept   ws-Recovery at 0668 with foreground-color 6 update UPPER.
     if       ws-Recovery not = "N" and not = "Y"
              display ST502 at line ws-23-lines col 1 with foreground-color 4 highlight
              go to aa020-Recovery.
*>
 aa030-U-Sure.
     display  "This program will cleardown All TD fields and other yearly/period totals"
                            at 0810 with foreground-color 2 highlight.
*>
     display  "Confirm you wish this to happen & that you have a backup [ ] (N/Y)" at 1010 with foreground-color 2.
     move     "N" to ws-Reply.
     accept   ws-Reply at 1068 with foreground-color 6 update UPPER.
     if       ws-Reply not = "N" and not = "Y"
              display ST502 at line ws-23-lines col 1 with foreground-color 4 highlight
              go to aa030-U-Sure.
     if       ws-Reply = "N"
              go to aa999-Exit.
     display  space at line ws-23-lines col 1 with erase eol.
*>
     if       ws-Recovery = "Y"
              display  "Recreating Stock file from temp file as requested" at 1210
                                                with foreground-color 2 highlight erase eol
              perform   ba010-Build-Stock thru ba999-exit
              go to aa999-exit.
*>
     perform  Stock-Open-Input.
     if       fs-reply not = zero
              display ST501 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 28 with foreground-color 2 highlight
              perform  ba030-Eval-Status
              display Eval-Msg at line ws-23-lines col 31 with foreground-color 2 highlight
              display ST003   at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
              go to aa999-Exit.
*>
     open     output Temp-Stock-File.
     if       fs-reply not = zero
              display ST503 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 31 with foreground-color 2 highlight
              perform  ba030-Eval-Status
              display Eval-Msg at line ws-23-lines col 34 with foreground-color 2 highlight
              display ST003   at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
              go to aa999-Exit.
*>
     display  "Updating your Stock file as requested" at 1210 with foreground-color 2 highlight erase eol.
*>
     perform  ba000-Process-Stock-Comp.
     go       to aa999-Exit.
*>
 aa999-Exit.
     display  "Check totals and hit return to quit" at 1801 with erase eol.
     move     space to ws-reply.
     accept   ws-reply at 1836.
     goback.
*>
*>***********************************************
*>                  Routines                    *
*>***********************************************
*>
 ba000-Process-Stock-Comp    section.
*>**********************************
*>
 ba000-Process-Stock-Comp-Main.
     perform  Stock-Read-Next.
     if       FS-Reply = 10
              perform Stock-Close
              close Temp-Stock-File
              display "Stock in : " at 1401 with erase eol
              display a  at 1412
              display  "temp stock out : " at 1431
              display b at 1448
              move   zero to a b
              go to ba010-Build-Stock.
*>
     compute  Stock-Value = Stock-Held * Stock-Cost.
*>
*> Here any record clean ups if needed - You might want to NOT do any of these !
*>
     move     zeros to Stock-Construct-Bundle
                       Stock-Under-Construction
                       Stock-Work-in-Progress
                       Stock-Adds
                       Stock-Deducts
                       Stock-Wip-Adds
                       Stock-Wip-Deds
                       Stock-Last-Actual-Cost.
     perform  varying C from 1 by 1 until C > 12
              move zeros to Stock-TD-Adds (C)
                            Stock-TD-Deds (C)
                            Stock-TD-Wip-Adds (C)
                            Stock-TD-Wip-Deds (C)
     end-perform.
     add      1 to a.
*>
     write    Temp-Stock-Record from WS-Stock-Record.
     if       fs-Reply not = zero
              display ST504 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 34 with foreground-color 2 highlight
              perform  ba030-Eval-Status
              display Eval-Msg at line ws-23-lines col 37 with foreground-color 2 highlight
              display ST003   at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
              perform Stock-Close              *> close Stock-File
              close Temp-Stock-File
              go to ba999-Exit.
     add      1 to b.
     go       to ba000-Process-Stock-Comp-Main.
*>
 ba010-Build-Stock.
     open     input Temp-Stock-File.
     if       fs-reply not = zero
              display ST503 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 31 with foreground-color 2 highlight
              perform  ba030-Eval-Status
              display Eval-Msg at line ws-23-lines col 34 with foreground-color 2 highlight
              display ST003   at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
              go to ba999-Exit.
*>
     perform  Stock-Open-Output.
     if       fs-reply not = zero
              display ST506 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 32 with foreground-color 2 highlight
              perform  ba030-Eval-Status
              display Eval-Msg at line ws-23-lines col 35 with foreground-color 2 highlight
              display ST003   at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
              close Temp-Stock-File
              go to ba999-Exit.
*>
 ba020-Read-Temp.
     read     Temp-Stock-File at end
              close Temp-Stock-File
              perform  Stock-Close
              open output Temp-Stock-File
              close Temp-Stock-File
              display "Temp stock in : " at 1601
              display a at 1617
              display "New stock out : " at 1631
              display b at 1647
              go to ba999-Exit.
     add      1 to a.
*>
*>  This error should never happen unless HDD error as new file will be = or smaller than original
*>
     move     Temp-Stock-Record to WS-Stock-Record.
     perform  Stock-Write.         *> write    Stock-Record from Temp-Stock-Record invalid key
     if       FS-Reply = 21 or = 22
              display ST000 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 38 with foreground-color 2 highlight
              perform  ba030-Eval-Status
              display Eval-Msg at line ws-23-lines col 41 with foreground-color 2 highlight
              display ST003   at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
                 display WS-Stock-Key at line ws-lines col 41
                 display WS-Stock-Abrev-Key at line ws-lines col 55
                 go to ba020-Read-Temp.

  *>            perform Stock-Close
  *>            close Temp-Stock-File
  *>            go to ba999-Exit.
*>
     if       fs-Reply not = zero
              display ST000 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 38 with foreground-color 2 highlight
              perform  ba030-Eval-Status
              display Eval-Msg at line ws-23-lines col 41 with foreground-color 2 highlight
              display ST003   at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
                 display WS-Stock-Key at line ws-lines col 41
                 display WS-Stock-Abrev-Key at line ws-lines col 55
                 go to ba020-Read-Temp.

   *>           perform Stock-Close
   *>           close Temp-Stock-File
   *>           go to ba999-Exit.
     add      1 to b.
     go       to ba020-Read-Temp.
*>
 ba030-Eval-Status.
 copy "FileStat-Msgs.cpy"   replacing STATUS by fs-Reply
                                      MSG by Eval-Msg.
*>
 ba999-Exit.
     exit     section.
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
