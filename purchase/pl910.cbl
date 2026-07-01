       >>source free
*>********************************************************
*>                                                       *
*>           Payments - Due  File  Generation            *
*>                                                       *
*>********************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         pl910.
*>**
*>    Author.             V B Coen FBCS, FIDM, FIDPM,
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Payments Due.
*>
*>    Version.            See Prog-Name In Ws.
*>
*>    Called Modules.     Maps04.
*>                        acas022
*>                         purchMT
*>                        acas029
*>                         OTM5MT
*>                        acas032
*>                         paymentsMT
*>**
*>    Error messages used.
*>                        PL901 - LOGIC Error.
*>                        SY008.  All these are new -
*>                        PL902.
*>                        PL903.
*>                        PL904.
*>****
*>    Changes.
*> 13/11/82 Vbc - Paging On Reports Remove Page Flip At Eoj.
*> 25/04/84 Vbc - Major Changes To Logic Of Cheque-Gen.
*> 22/06/84 Vbc - Support Of Indexed Openitm File.
*> 29/06/84 Vbc - Remove References To Last-Read;Not Needed.
*> 19/07/84 Vbc - Invalid Key On Starts,Move To Pay-Value After
*>                 Prompt Test.
*> 22/03/09 vbc - 3.00.01 Migration to Open Cobol v3.00.00
*> 23/03/09 vbc -         Support for sortcode/account for Bacs etc.
*> 04/04/09 vbc -         Printing of payment method under 'M' C=cheque, B=Bacs.
*> 29/05/09 vbc -         Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc -     .05 Mod lpr.
*> 15/09/10 vbc -     .06 Change for print-spool.command.
*> 16/12/11 vbc -     .07 Error msgs to SLnnn. Support for dates other than UK
*>                        Support for path+filenames.
*>                        Updated version to 3.01.nn
*> 24/10/16 vbc - .       ALL programs now using wsnames.cob in copybooks.
*> 14/01/17 vbc - 3.01.08 Title changed from Cheque to Payments - same as report.
*> 11/01/18 vbc - 3.02.09 Updated for RDB and v3.02.
*> 16/04/24 vbc           Copyright notice update superseding all previous notices.
*> 20/04/24 vbc       .10 Added LOGIC to error message PL901.
*> 29/07/25 vbc       .11 Add tests for files not present on open & add new msgs.
*> 24/08/25 vbc       .12 Adjust Headings.
*> 01/09/25 vbc       .13 page cnt started at 2 chg Headings to test line-cnt and repos
*>                        date to be used in process.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
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
*> copy "selpl.cob".
*> copy "seloi5.cob".
*> copy "selpay.cob".
 copy "selprint.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdpl.cob".
*> copy "fdoi5.cob".
*> copy "fdpay.cob".
 copy "fdprint.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "PL910 (3.3.00)".
 copy "print-spool-command.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
 copy "plwsoi.cob".
*>
*> Ex FDs
*>
 copy "wspl.cob".     *> WS-Purch-Record.
 copy "plwsoi5B.cob".  *> Open-Item-Record-5.
 copy "plwspay.cob".  *> Pay-Record.
 01  WS-Pay-Record  redefines Pay-Record.
     03  filler     pic x(238).
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
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
*>     03  WS-Purch-Record        pic x.
*>     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
*>     03  WS-OTM5-Record         pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  ws-data.
     03  To-Be-Paid      binary-long             value zero.
     03  ws-Age-To-Pay   pic 99                  value zero.
     03  ws-reply        pic x.
     03  a               pic 99                  value zero.
     03  work-1          pic s9(6)v99    comp-3  value zero.
     03  p               pic 99                  value zero.
     03  inv-amount      pic s9(7)v99    comp-3  value zero.
     03  amount-out      pic s9(7)v99    comp-3  value zero.
     03  Line-Cnt        binary-char             value 90.
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
 01  Error-Messages.
*> System Wide
     03  SY008           pic x(39) value "SY008 Note message & Hit return to Quit".
*>     03  PL005          pic x(18) value "PL005 Invalid Date".
*> Module specific
     03  PL901          pic x(42) value "PL901 PE 910-01 LOGIC: Note and hit return".
     03  PL902          pic x(31) value "PL902 Purchase Ledger not Found".
     03  PL903          pic x(34) value "PL903 Purchase OTM5 file not Found".
     03  PL904          pic x(32) value "PL904 Payment file Error on Open".
*>
 01  balances.
     03  bal-0           pic 9(7)v99 value zero.
     03  bal-30          pic 9(7)v99 value zero.
     03  bal-60          pic 9(7)v99 value zero.
     03  bal-90          pic 9(7)v99 value zero.
     03  bal-t           pic 9(7)v99 value zero.
     03  tot-0           pic 9(7)v99 value zero.
     03  tot-30          pic 9(7)v99 value zero.
     03  tot-60          pic 9(7)v99 value zero.
     03  tot-90          pic 9(7)v99 value zero.
     03  tot-t           pic 9(7)v99 value zero.
*>
 01  line-1.
     03  l1-prog         pic x(54)       value spaces.
     03  filler          pic x(22)       value "Payments Due Report".
     03  filler          pic x(14)        value "= or Prior To".
     03  l1-prior-date   pic x(10).
     03  filler          pic x(24)       value spaces.
     03  filler          pic x(5)        value "Page ".
     03  l3-page         pic zz9.
*>
 01  line-2.
     03  l2-user         pic x(56)       value spaces.
     03  filler          pic x(19)       value spaces.
     03  filler          pic x(47)       value spaces.
     03  l1-date         pic x(10).
*>
 01  line-4.
     03  filler          pic x(38)     value " Number   Supplier".
     03  filler          pic x(94)     value
         "Folio M   Date       Invoice      Current       30 +  " &
         "      60 +        90 +      Total to Pay".
*>
 01  line-5.
     03  l5-key          pic x(10).
     03  l5-supplier     pic x(25).
     03  l5-folio        pic z(7)9b.
     03  l5-method       pic xb          value space.
     03  l5-date         pic x(12).
     03  l5-invoice      pic x(11).
     03  l5-0            pic z(6)9.99cr  blank when zero.
     03  l5-30           pic z(6)9.99cr  blank when zero.
     03  l5-60           pic z(6)9.99cr  blank when zero.
     03  l5-90           pic z(6)9.99cr  blank when zero.
     03  filler          pic xxxx        value spaces.
     03  l5-pay          pic z(6)9.99    blank when zero.
*>
 01  line-6.
     03  filler          pic x(69)       value "    Total".
     03  l6-0            pic z(6)9.99cr  blank when zero.
     03  l6-30           pic z(6)9.99cr  blank when zero.
     03  l6-60           pic z(6)9.99cr  blank when zero.
     03  l6-90           pic z(6)9.99cr  blank when zero.
     03  filler          pic xxxx        value spaces.
     03  l6-pay          pic z(6)9.99    blank when zero.
*>
 01  line-7.
     03  filler          pic x(69)       value spaces.
     03  filler          pic x(12)       value "  --------  ".
     03  filler          pic x(12)       value "  --------  ".
     03  filler          pic x(12)       value "  --------  ".
     03  filler          pic x(12)       value "  --------  ".
     03  filler          pic x(4)        value spaces.
     03  filler          pic x(12)       value "  ========".
*>
 linkage section.
*>==============
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
 01  to-day              pic x(10).
*>
 procedure  division using ws-calling-data
                           system-record
                           to-day
                           file-defs.
*>========================================
*>
 init section.
     move     prog-name to l1-prog.
     move     usera to  l2-user.
     perform  zz070-Convert-Date.
     move     ws-date to l1-date.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
     move     1 to File-Key-No.  *> Good for all files/tables used here.
*>
     display  Prog-Name at 0101 with foreground-color 2 erase eos.
     display  "Payments Due Reporting" at 0130       with foreground-color 2.
     display  ws-date at 0171 with foreground-color 2.
     display  "Current Age to Pay on is - [  ]" at 0501 with foreground-color 2.
     move     Age-To-Pay to WS-Age-To-Pay.
     display  ws-Age-To-Pay at 0529 with foreground-color 3.
     display  "is this correct (Y/N) ?  - [ ]" at 0701  with foreground-color 2.
     move     "Y"  to  ws-reply.
     accept   ws-reply at 0729 with foreground-color 6.
     move     function upper-case (ws-reply) to ws-reply.
*>
     if       ws-reply = "N"
              accept ws-Age-To-Pay at 0529 with foreground-color 3 UPDATE
              move ws-Age-To-Pay to Age-To-Pay.
*>
     subtract Age-To-Pay  from  Run-Date  giving  To-Be-Paid.
     move     To-Be-Paid to u-bin.
     perform  zz060-Convert-Date.
     move     ws-date to l1-prior-date.
     perform  Payment-Gen.
*>
 Menu-Exit.
*>
     exit     program.
*>
 Payment-Gen   section.
*>====================
*>
     perform  Purch-Open-Input.  *> open input purchase-file open-item-file-5.
     if       FS-Reply not = zeros
              display  PL902 at 0701 with foreground-color 2
              display  SY008 at 0801 with foreground-color 2
              accept   WS-Reply at 0841
              perform  Purch-Close
              go to Main-Exit
     end-if
     perform  OTM5-Open-Input.
     if       FS-Reply not = zeros
              display  PL903 at 0701 with foreground-color 2
              display  SY008 at 0801 with foreground-color 2
              accept   WS-Reply at 0841
              perform  OTM5-Close
              go to Main-Exit
     end-if
     open     output print-file.  *> pay-file.
     perform  Payments-Open-Output.
     if       FS-Reply not = zeros
              display  PL904 at 0701 with foreground-color 2
              display  SY008 at 0801 with foreground-color 2
              accept   WS-Reply at 0841
              perform  Payments-Close
              go to Main-Exit
     end-if
     perform  Headings.
*>
 Read-Purchase.
     perform  Purch-Read-Next. *>  read purchase-file  next  record at end
     if       fs-reply = 10
              go to  main-end.
*>
     if       purch-current not > zero
              go to Read-Purchase.
*>
     initialize pay-record.
     move     zero          to  oi5-invoice.
     move     WS-Purch-Key  to  oi5-supplier
                                l5-key
                                pay-supl-key.
     move     1  to  pay-nos.
     move     u-bin  to  pay-date.
     move     purch-name to  l5-supplier.
     if       purch-sortcode not = zero
              move purch-sortcode  to pay-sortcode
              move purch-accountno to pay-account
              move "B" to l5-method
     else
              move "C" to l5-method
     end-if
     move     1  to  a.
     set      fn-not-less-than to true.
     perform  OTM5-Start.   *> start open-item-file-5 key not < oi5-key.
*>
 Read-Open-Item.
     perform  OTM5-Read-Next.  *> read open-item-file-5 next record at end
     if       fs-reply = 10
              perform end-statement
              go to main-end.
*>
     move     open-item-record-5  to  oi-header.
     if       s-closed
         or   payment-held
         or   oi-b-nos not = zero
              go to Read-Open-Item.
*>
     if       oi-supplier not =  WS-Purch-Key
              go to  end-statement.
*>
*> O-I transaction is for this Supplier.
*>
     if       oi-type not = 2
              go to  Read-Open-Item.
*>
     if       oi-date  >  To-Be-Paid
              go to  Read-Open-Item.
*>
     move     oi-invoice  to  l5-folio  pay-folio (a).
     move     oi-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     ws-date   to  l5-date.
*>
     move     oi-ref to  l5-invoice  pay-invoice (a).
*>
*> invoices only here
*>
     add      oi-net oi-carriage oi-vat oi-c-vat giving inv-amount.
     subtract oi-paid  from  inv-amount          giving amount-out.
*>
     if       amount-out = zero
              go to Read-Open-Item.
*>
*> ie no. of days o/s.
*>
     subtract oi-date  from  Run-Date  giving  work-1.
*>
*>  Are we in time to take prompt pay discount ?
*>
     if       oi-deduct-days not < work-1
              subtract oi-deduct-amt from amount-out
              move oi-deduct-amt to pay-deduct (a)
              if   amount-out = zero
                   go to Read-Open-Item
              else
               if   amount-out < zero
                    display PL901 at 2301 with foreground-color 4
                    accept ws-reply at 2346
                    go to Read-Open-Item.
*>
*>  Above 2 lines checks for overpayment last time run ???
*>    this should Never Ever happen...... otherwise a bug
*>
*> now work out ageing
*>
     move     amount-out  to  pay-value (a).
     if       work-1  <  30
              add  amount-out  to  bal-0
              move  0  to  pay-period (a)
     else
      if      work-1  <  60
              add  amount-out  to  bal-30
              move  30  to  pay-period (a)
      else
       if     work-1  <  90
              move  60  to  pay-period (a)
              add  amount-out  to  bal-60
       else
              move  90  to  pay-period (a)
              add  amount-out  to  bal-90.
*>
     add      amount-out  to  bal-t.
     move     zero  to  amount-out.
*>
     move     bal-0  to  l5-0.
     move     bal-30 to  l5-30.
     move     bal-60 to  l5-60.
     move     bal-90 to  l5-90.
     move     bal-t  to  l5-pay  pay-gross.
*>
     add      bal-0  to  tot-0.
     add      bal-30 to  tot-30.
     add      bal-60 to  tot-60.
     add      bal-90 to  tot-90.
*>
     write    print-record  from  line-5 after 1.
     add      1 to Line-Cnt.
     if       Line-Cnt > Page-Lines
              perform Headings.
*>
     move     zero  to  bal-0  bal-30  bal-60  bal-90.
     move     space to  l5-key  l5-supplier.
*>
*> now loop back for next item....
*>
     add      1  to  a.
     if       a  >  9
              move  1  to  a
              move "C" to pay-cont
              perform Payments-Write  *> write pay-record
              move zero to pay-gross
              add 1 to pay-nos.
*>
     go       to Read-Open-Item.
*>
*> can only get here at the end of a statement.
*>
 End-Statement.
*>
     if       a not = 1
              perform Payments-Write  *> write pay-record
              move  1  to  a.
*>
     if       Line-Cnt > Page-Lines
              perform Headings.
*>     else
*>        if    bal-t not = zero
*>              add 1 to Line-Cnt
*>              move spaces  to  print-record
*>              write print-record after 1.
*>
     move     zero to bal-t.
*>
 ES-Exit.
     go       to Read-Purchase.
*>
 Main-End.
*>
     move     tot-0  to  l6-0.
     move     tot-30 to  l6-30.
     move     tot-60 to  l6-60.
     move     tot-90 to  l6-90.
     add      tot-0 tot-30 tot-60 tot-90 giving l6-pay.
*>
     write    print-record from line-7 after 1.
     write    print-record from line-6 after 1.
     close    print-file.    *> open-item-file-5 purchase-file pay-file.
     perform  OTM5-Close.
     perform  Purch-Close.
     perform  Payments-Close.
     call     "SYSTEM" using Print-Report.
*>
 Main-Exit.   exit section.
*>
 Headings     section.
*>===================
*>
     if       Page-Lines > Line-Cnt
              go to Main-Exit.             *> 01/09/25 page cnt started at 2.
     add      1  to  p.
     move     p  to  l3-page.
*>
     if       p not = 1
              write print-record from line-1 after page
              write print-record from line-2 after 1
              move  spaces to print-record
              write print-record after 1
     else
              write print-record from line-1 before 1
              write print-record from line-2 before 1
     end-if
     write    print-record from line-4 after 1.
     move     spaces  to  print-record.
     write    print-record  after 1.
     move     5 to Line-Cnt.
*>
 main-exit.   exit section.
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
