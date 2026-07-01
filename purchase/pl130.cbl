       >>source free
*>**********************************************
*>                                             *
*>         Purchase Analysis Report            *
*>                                             *
*>**********************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         pl130.
*>**
*>    Author.             V B Coen FBCS, FIDM, FIDPM, 17/04/84
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Product Analysis Report.
*>**
*>    Version.            See Prog-Name In Ws.
*>
*>    Called Modules.     acas013  ->
*>                         valueMT.

*>**
*>    Error messages used.
*>                        PL003
*>                        PL160
*>                        PL161.
*>**
*>    Changes.
*> 31/03/84 Vbc - Use Invoice-File Instead Of Openitm File.
*> 14/07/84 Vbc - Alter Header-Analysis Routine.
*> 05/08/84 Vbc - Use Invalid Key On Start.
*> 01/10/84 Vbc - Changed To Report Only,Rest Of Code To Pl055.
*> 22/03/09 vbc - Migration to Open Cobol v3.00.00
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .03 Mod lpr.
*> 15/12/11 vbc - .04 Error msgs to SLnnn.Support for dates other than UK
*>                    Support for path+filenames.
*>                    Updated version to 3.01.nn
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 10/01/18 vbc - .05 Support for RDB on Value tables instead of cobol files
*>                    using acas013.
*>                    All programs upgraded to v3.02 for RDB processing.
*>                    Added SL161 if not value data / file present
*>                    as cosmetic fix up.
*> 22/03/18 vbc - .06 Changed description of PL160 (as same in SL160).
*>                    If called by xl150 and errors occur when opening exit with
*>                    ws-Term-code = 12
*>                    or reading data (other than EOF) display error and goback.
*>                    Same done for sl130.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 30/12/24 vbc   .07 Change ws-Term-code from 12 to 9 its a pic 9.
*> 05/01/25 vbc   .08 Read in param rec update P-FLAG-A rewrite rec zz900 & 910.
*>                    Placed in Proc-ACAS-Param-Get-Rewrite.cob.
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
*>===============================
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
 copy "selprint.cob".
*> copy "selval.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 copy "fdprint.cob".
*> copy "fdval.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "PL130 (3.3.00)".
 copy "print-spool-command.cob".
 77  menu-reply          pic x     value space.
 77  Eval-Msg            pic x(25) value spaces.
*>
 copy "wsfnctn.cob".
 copy "wsmaps03.cob".
 copy "wsval.cob".
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
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  ws-data.
     03  ws-reply        pic x           value space.
     03  a               pic 99.
     03  work-1          pic 9(4)v9(4).
     03  line-cnt        binary-char     value 66.
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
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide
     03  PL003          pic x(28) value "PL003 Hit Return To Continue".
*> Module specific
     03  PL160          pic x(36) value "PL160 Error reading value records - ".
*>  Above is a suspected programming error but so far has never appeared
     03  PL161          pic x(38) value "PL161 No data, nothing to do - exiting".
*>
 01  line-1.
     03  l1-version      pic x(49)       value spaces.
     03  filler          pic x(75)       value  "              Purchase  Analysis".
     03  filler          pic x(6)        value  " Page ".
     03  l1-page         pic z9.
*>
 01  line-2.
     03  l2-user         pic x(49)       value  spaces.
     03  filler          pic x(32)       value  spaces.
     03  filler          pic x(41).
     03  l2-date         pic x(10).
*>
 01  line-4.
     03  filler          pic x(52)       value "Analysis  Type    <-----Description------>   <------".
     03  filler          pic x(42)       value "-Transactions------->   <----------------A".
     03  filler          pic x(38)       value "mount----------------->  % Period Mvmt".
*>
 01  line-5.
     03  filler          pic x(45)       value "  Code".
     03  filler          pic x(87)       value "Current   Previous   Y. to D      Current      Previous     Year to Date  Trans. Amount".
*>
 01  line-6.
     03  filler          pic xxx         value spaces.
     03  l6-code         pic x(6).
     03  l6-type         pic x(9).
     03  l6-desc         pic x(28).
     03  l6-t-c          pic zzzz9       blank when zero.
     03  filler          pic x(5)        value spaces.
     03  l6-t-p          pic zzzz9       blank when zero.
     03  filler          pic x(6)        value spaces.
     03  l6-t-y          pic zzzz9       blank when zero.
     03  filler          pic x(4)        value spaces.
     03  l6-a-c          pic z(7)9.99cr  blank when zero.
     03  l6-a-p          pic z(8)9.99cr  blank when zero.
     03  l6-a-y          pic z(8)9.99cr  blank when zero.
     03  l6-p-t          pic z(4)9.99    blank when zero.
     03  l6-p-a          pic zzz9.99     blank when zero.
*>
 01  WS-Temp-System-Rec  pic x(2048).   *> Size overkill
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
     move     Print-Spool-Name to PSN.
     move     prog-name to l1-version.
     display  " " at 0101 with erase eos.
     display  l1-version at 0101 with foreground-color 2.
     display  "Purchase Analysis" at 0134 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
     move     ws-date to  l2-date.
     move     usera   to  l2-user.
     perform  Report1.
     perform  zz900-Read-System-Param. *> 05/01/25
     move     zero to P-Flag-A. *> Clear Purchase Analysis flag
     perform  zz910-Rewrite-System-Param. *> 05/01/25
*>
 menu-exit.
     exit     program.
*>
*>*************************************
*>            Procedures              *
*>*************************************
*>
 Report1      section.
     move     zeros to WS-Term-Code.
     perform  Value-Open-Input.     *>  open     input  value-file.
     if       fs-reply not = zero
              perform Value-Close      *> close value-file
              display PL161    at 2301
              if       WS-Caller not = "xl150"
                       display PL003    at 2401
                       accept menu-reply at 2431
              end-if
              go to  main-exit
     end-if
     open     output  print-file.
     move     zero  to  a.
     perform  headings thru head-exit.
*>
 read-loop.
     perform  Value-Read-Next.       *> read value-file  next record  at end
     if       FS-Reply = 10
              go to  end-report.
     if       fs-reply not = zero
              display PL160    at 2301
              display Eval-Msg at 2320
              if       WS-Caller not = "xl150"
                       display PL003    at 2440
                       accept menu-reply at 2470
              else
                       move    9 to WS-Term-Code  *> was 12 but is a pic 9
              end-if
              go to end-report
     end-if.
*>
     if       va-system not = "P"  *> Purchase only
              go to read-loop.
     if       va-second not = space and
              va-v-this = zero and
              va-v-year = zero
              go to read-loop.
*>
     if       va-second = space
       and    va-gl   = zero
              move    "Group"  to  l6-type
              perform headings thru head-exit
              move    spaces  to  print-record
              write   print-record after 1
              add     1 to line-cnt
     else
              move    " Detail" to  l6-type.
*>
     move     va-group  to  l6-code.
     move     va-desc   to  l6-desc.
*>
     move     va-t-this  to  l6-t-c.
     move     va-t-last  to  l6-t-p.
     move     va-t-year  to  l6-t-y.
     divide   va-t-this  by  va-t-last  giving  work-1.
     multiply work-1  by  100  giving  l6-p-t.
*>
     move     va-v-this  to  l6-a-c.
     move     va-v-last  to  l6-a-p.
     move     va-v-year  to  l6-a-y.
     divide   va-v-this  by  va-v-last  giving  work-1.
     multiply work-1  by  100  giving  l6-p-a.
*>
     write    print-record  from  line-6 after 1.
     add      1 to line-cnt.
     if       line-cnt > Page-Lines
              perform headings thru head-exit.
*>
     go       to read-loop.
*>
 Evaluate-Error-Msgs.
*>******************
*>
 copy "FileStat-Msgs.cpy" replacing status by fs-reply
                                       msg by Eval-Msg.
*>
 headings.
*>*******
*>
     if       line-cnt < Page-Lines - 8
              go to head-exit.
     add      1  to  a.
     move     a  to  l1-page.
     move     zero to line-cnt.
*>
     if       a not = 1
              write print-record  from  line-1 after page
              write print-record  from  line-2 after 1
              move  spaces  to  print-record
              write print-record after 1
     else
              write print-record  from  line-1 before 1
              write print-record  from  line-2 before 1
     end-if
     write    print-record  from  line-4 after 1.
     write    print-record  from  line-5 after 1.
     move     spaces  to  print-record.
     write    print-record after 1.
*>
 head-exit.
     exit.
*>
 end-report.
*>*********
*>
     close    print-file.      *> value-file
     perform  Value-Close.
     call     "SYSTEM" using Print-Report.
*>
 main-exit.
     goback.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   ws-test-date
*> output:  u-date/ws-date as uk date format
*>          u-bin not zero if valid date
*>
     move     ws-test-date to ws-date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-test-date.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz050-test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to ws-date.  *> swap Intl to UK form
     move     ws-test-date (1:4) to ws-Year.
     move     ws-test-date (6:2) to ws-Month.
     move     ws-test-date (9:2) to ws-Days.
*>
 zz050-test-date.
     move     ws-date to u-date.
     move     zero to u-bin.
     perform  maps04.
*>
 zz050-exit.
     exit     section.
*>
 zz060-Convert-Date        section.
*>********************************
*>
*>  Converts date in binary to UK/USA/Intl date format
*>****************************************************
*> Input:   u-bin
*> output:  ws-date as uk/US/Inlt date format
*>          u-date & ws-Date = spaces if invalid date
*>
     perform  maps04.
     if       u-date = spaces
              move spaces to ws-Date
              go to zz060-Exit.
     move     u-date to ws-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     u-date (7:4) to ws-Intl-Year.
     move     u-date (4:2) to ws-Intl-Month.
     move     u-date (1:2) to ws-Intl-Days.
*>
 zz060-Exit.
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
 copy "Proc-ACAS-Param-Get-Rewrite.cob".
*>
 maps04       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
