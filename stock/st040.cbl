       >>source free
*>*************************************************************
*>                                                            *
*>        Stock Control Reset Period and Year Totals          *
*>                                                            *
*>   This program will clear down month cycle in year         *
*>    set as broken down in months 01 through 12.             *
*>    if day < 05 (last month) or this month if day > 04,     *
*>      i.e., 27+ And/Or current period.                      *
*>                                                            *
*>   Normally when doing Month within yearly totals period    *
*>   would also be done if period = Weekly or Monthly as set  *
*>   in system params under Stock control entries.            *
*>                                                            *
*>  This program can be directly called (via stock) using a   *
*>   Autorun process by giving two params to stock as in :    *
*>    stock NULL st0405n  (5=clear down total values          *
*>   2nd digit n is what to clear 1 = period,                 *
*>                                2 = month within year,      *
*>                                3 = both.                   *
*>                                                            *
*>    All recs are done including whose with                  *
*>     Stock-Services-Flag set to "Y"                         *
*>                                                            *
*>*************************************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         st040.
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
*>                        ST401.
*>                        ST402.
*>                        ST403.
*>**
*> Changes:
*> 28/06/09 vbc - .00 Written in Cobol from scratch against v2 specs.
*> 21/07/09 vbc - .02 Program title change.
*> 11/12/11 vbc -     Changed version from 1.00.xx to 3.01.xx, in keeping
*>                     with the rest of ACAS
*>                .03 Changed usage of Stk-Date-Form to the global field
*>                     Date-Form making former redundent.
*> 12/05/13 vbc - .04 Changed wsnames to in common as pl010 called in st010.
*> 16/05/13 vbc - .05 Changed wsnames to in copybook see above.
*> 25/05/13 vbc - .06 Test for Activity-Rep-Run wrong shoud be for zero.
*> 21/07/16 vbc - .07 Replace Cobol file acces verbs with calls to FH and RDB
*>                    DAL. Precede references to Stock-Record, Stock-Key,
*>                    Stock-Abrev-Key, Stock-Desc by WS- to reflect that we
*>                    are only dealing with a WS record and the FD is now gone.
*>                    Stop using File-Status and replace with call to
*>                    "CBL_CHECK_FILE_EXIST" instead. Do same for all such
*>                    checks, sets etc to kill of usage dates back to floppies.
*>                    ST011 added. Update version to 3.02.
*> 10/10/16 vbc - .08 Clean up update msgs for file & table.
*> 24/10/16 vbc - .09 ALL programs now using wsnames.cob in copybooks
*>                    Use of maps99 is depleted.
*> 12/03/18 vbc - .10 acasnnn copylib renaming acas000-open etc to comply with
*>                    rest of ACAS to (System-Open etc) removed unused field
*>                    WS var. error-code.
*>                    Chg ST000 to stock rec.
*> 16/03/18 vbc - .11 Added code for AUTORUN via stock menu which will print reports
*>                    for both Additions and Deletions and then delete Audit data
*>                    There will be no requests to do this so printer must be on
*>                    or spooler, to print when it is turned on.
*>                    For period (which can be week, month, quarter etc)
*>                    it clears values to zero ready for accumulations for new period.
*>                    where and taken from todays date, if day < 5 month is last month
*>                    else this month (day > 27).
*>                    Normal usage would run on 1st on month via cron etc.
*> 19/03/18 vbc - .12 Added msg ST403 if CD-Args (7:1) when in autorun not in range 1-3.
*>                    displayed and then job aborted. if autorun via cron with mail set
*>                    then will appear as a msg to ACAS admin user.
*> 08/12/22 vbc - .13 Chgd goto in ba000 to use para -Main 4 GC v3.2 warning.
*> 16/08/23 vbc       Removed old remarked out cobol file verbs.
*> 15/03/24 vbc   .14 Change case of function and (low/upp)er-case.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/12/24 vbc       For all ACCEPT X use UPPER & remove function upper-case.
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
*> copy "selstock.cob".
 data                    division.
*>================================
*>
 file section.
*>------------
*>
*> copy "fdstock.cob".
*>
 working-storage section.
*>-----------------------
*>
 77  Prog-Name           pic x(15)       value "ST040 (3.3.00)".
*>
 01  work-fields.
     03  ws-Reply-Year    pic x                   value space.
         88 Clear-Year                            value "Y".
     03  ws-Reply-Period  pic x                   value space.
         88 Clear-Period                          value "Y".
     03  WS-Period-Update pic x                   value "Y".    *> Y = good month
     03  WS-Current-Month.
         05  WS-Cur-Mth   pic 99                  value 01.
     03  WS-Current-Day.
         05  WS-Cur-Day   pic 99                  value 01.
     03  ws-Reply         pic x                   value space.

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
 copy "wsstock.cob".     *> 3.02
 copy "wsfnctn.cob".
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
 01  Error-Messages.
     03  ST000          pic x(36) value "ST000 Error on Writing to Stock Rec.".
     03  ST003          pic x(27) value "ST003 Press return for Menu".
*> Module specific
     03  ST401          pic x(26) value "ST401 Stock File not found".
     03  ST402          pic x(17) value "ST402 Y or N only".
     03  ST403          pic x(27) value "ST403 Sub arg not 1, 2 or 3".
*>
 linkage section.
*>***************
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
     if       FUNCTION LOWER-CASE (WS-CD-Args (1:5)) not = "st040"
              go to aa010-Questions.
*> Next may need to be in quotes
     if       WS-CD-Args (7:1) < 1 or > 3    *> Bad option set should appear in msg to user.
              display ST403 at 0101 with erase eos
              move 8 to WS-Term-Code
              goback.
*>
*>  Needed for period updates, 1st check for valid mth and day - JIC.
*>  Day and month taken from todays date, so if day > 27 its for next month
*>   and if < 05 then this month but not tested for.
*>
     if       WS-Cur-Mth < 01 or > 12
         or   WS-Cur-Day < 01 or > 31
              move "N" to WS-Period-Update
     else
              move "Y" to WS-Period-Update
     end-if
     if       WS-Period-Update = "Y"
        and   WS-Cur-Day > 27                    *> should be run on 1st of new month but . .
              add 1 to WS-Cur-Mth                *>  could be last working day of mth
              if   WS-Cur-Mth > 12               *> Adjust for mth 01 so Dec last year
                   move 01 to WS-Cur-Mth.          *> otherwise its current month
*>
 aa010-Questions.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock Activity Reset" at 0131 with foreground-color 2.
     display  ws-Conv-Date at 0171 with foreground-color 2.
*>
*> First block is for AUTO run via stock menu program when given 2 params
*>   stock NULL st0401n (n=1, 2, 3)
*>
     if       FUNCTION LOWER-CASE (WS-CD-Args (1:5)) not = "st040"
              go to aa015-Questions-2.
*>
*>  So it is AUTO RUN, check processes to run and ignoring char (6:1).
*>
     if       WS-CD-Args (7:1) = "1" or "3"
              set Clear-Period to true
              go to  aa040-Process-All.
     if       WS-CD-Args (7:1) = "2"
              set Clear-Year to true    *> Clears month in year totals
              go to  aa040-Process-All.
*>
 aa015-Questions-2.
     display  "Can I clear this " at 0410 with foreground-color 2.
     if       Stk-Period-Cur = "Q"
              display "Quarter" at 0427 with foreground-color 2
     else
      if      Stk-Period-Cur = "W"
              display "   Week" at 0427 with foreground-color 2
      else
       if     Stk-Period-Cur = "M"
              display "  Month" at 0427 with foreground-color 2
       else   display "Not Set" at 0427 with foreground-color 2. *> Appears its a BUG in sys002
*>
     display  " Period Totals? [ ] (N/Y)" at 0434 with foreground-color 2.
     display  "Can I clear End of Month Totals on Stock records [ ] (N/Y)" at 0610 with foreground-color 2.
*>
 aa020-Accept-Loop.
     move     "N" to ws-Reply-Year ws-Reply-Period.
     accept   ws-Reply-Period at 0451  with foreground-color 6 update UPPER.
     if       ws-Reply-Period not = "Y" and not = "N"
              display ST402 at line ws-23-lines col 1 with foreground-color 4 highlight
              go to aa020-Accept-Loop.
     accept   ws-Reply-Year at 0660  with foreground-color 6 update UPPER.
     if       ws-Reply-Year not = "Y" and not = "N"
              display ST402 at line ws-23-lines col 1 with foreground-color 4 highlight
              go to aa020-Accept-Loop.
     display  " " at line ws-23-lines col 1 with erase eol.
     if       not Clear-Year and not Clear-Period
              go to aa999-Exit.
*>
     if       Clear-Period
              display "Will Clear Period totals" at 0801 with foreground-color 3 highlight.
     if       Clear-Year
              display "Will Clear Month totals"  at 1001 with foreground-color 3 highlight.
*>
 aa030-U-Sure.
     if       STK-Activity-Rep-Run = zero
              display "You have NOT run audit reports" at line ws-23-lines col 1 with foreground-color 6 highlight
              display ST003  at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
              go to aa999-Exit.
*>
     display  "Have you made backups of your data and are you sure?  [ ] (N/Y)"
                                       at 1210 with foreground-color 2 highlight.
     move     "N" to ws-Reply.
     accept   ws-Reply at 1265 with foreground-color 6 update UPPER.
     if       ws-Reply not = "N" and not = "Y"
              display ST402 at line ws-23-lines col 1 with foreground-color 4 highlight
              go to aa030-U-Sure.
     if       ws-Reply = "N"
              go to aa999-Exit.
     display  " " at line ws-23-lines col 1 with erase eol.
*>
 aa040-Process-All.
*>
*> New for RDB
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-11
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    display ST401 at line ws-23-lines col 1 with foreground-color 4 highlight
                    display fs-reply at line ws-23-lines col 28 with foreground-color 2 highlight
                    display ST003  at line ws-lines col 01
                    accept ws-reply at line ws-lines col 30
                    go to aa999-Exit
              end-if
     end-if.
     perform  Stock-Open.
     if       fs-reply not = zero
                    display ST401 at line ws-23-lines col 1 with foreground-color 4 highlight
                    display fs-reply at line ws-23-lines col 28 with foreground-color 2 highlight
                    display ST003  at line ws-lines col 01
                    accept ws-reply at line ws-lines col 30
                    go to aa999-Exit
     end-if
*>
     if       FS-Cobol-Files-Used
              display  "Updating Stock file as requested"
                                             at 1210 with foreground-color 2 highlight erase eol.
     if       File-System-Used > zero
              display  "Updating Stock table as requested"
                                             at 1310 with foreground-color 2 highlight erase eol.
*>
     perform  ba000-Clear-Totals.
     go       to aa999-Exit.
*>
 aa999-Exit.
     goback.
*>
*>***********************************************
*>                  Routines                    *
*>***********************************************
*>
 ba000-Clear-Totals    section.
*>****************************
*>
 ba000-Clear-Totals-Main.
     perform  Stock-Read-Next.
     if       fs-reply = 10
              perform Stock-Close
              go to ba999-Exit.
*>
     if       Clear-Year              *> clears specific month depending on day no.
        and   WS-Period-Update = "Y"                   *> test for good date
              move zeros to Stock-TD-Adds     (WS-Cur-Mth)
              move zeros to Stock-TD-Deds     (WS-Cur-Mth)
              move zeros to Stock-TD-Wip-Adds (WS-Cur-Mth)
              move zeros to Stock-TD-Wip-Deds (WS-Cur-Mth).
*>
     if       Clear-Period                             *> be it week, month, quarter etc.
              initialize Stock-Mthly-Running-Totals.   *> yep, name is wrong should be period!
*>
     perform  Stock-Rewrite.
     if       fs-Reply not = zero
              display ST000 at line ws-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line ws-23-lines col 38 with foreground-color 2 highlight
              display ST003  at line ws-lines col 01
              accept ws-reply at line ws-lines col 30
              perform Stock-Close
              go to ba999-Exit.
     go       to ba000-Clear-Totals-Main.
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
*> output:  ws-date as uk/US/Inlt date format  AND
*>  WS-Current-Day and -Month as xx as ws-cur-Day & -Mth as 99.
*>    Special for this program.
*>
     move     to-day to ws-date.
*>
     if       Date-Form = zero
              move WS-Month to WS-Current-Month
              move WS-Days  to WS-Current-Day
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> swap month and days
              move WS-days  to WS-Swap
              move WS-month to WS-Days
              move WS-Days  to WS-Current-Day
              move WS-swap  to WS-Month
              move WS-Month to WS-Current-Month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     to-day (7:4) to WS-Intl-Year.
     move     to-day (4:2) to WS-Intl-Month
                              WS-Current-Month.
     move     to-day (1:2) to WS-Intl-Days
                              WS-Current-Day.
*>
 zz070-Exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
