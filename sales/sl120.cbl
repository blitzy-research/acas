       >>source free
*>*********************************************
*>                                            *
*>           Aged Debtor Analysis             *
*>        or Aged Trial Balance               *
*>*********************************************
*> Note that sl110, 120 & 190 are similar.    *
*>                                            *
*>*********************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl120.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 25/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Aged Trial Balance/Debtor Analysis.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     maps04.
*>                        acas012  ->
*>                         salesMT
*>                        acas019  ->
*>                         otm3MT.     ONLY for Table processing.
*>**
*>    Error messages used.
*>                        SL003
*>                        SL151.
*>                        SL152.
*>                        SL153.
*>**
*>
*>    Changes.
*> 19/03/83 vbc - Use entered date to override system-date for
*>                 ageing.
*> 01/10/83 vbc - Use deduct-taken from payments for late chg
*>                 totals ie oi-deduct-amt.
*> 25/10/83 vbc - Cis cobol conversion.
*> 19/12/83 vbc - Allow for system record 4.
*> 16/01/84 vbc - Support oi-hold-flag.
*> 01/03/84 vbc - Support of sales-unapplied.
*> 30/03/84 vbc - Chg io-invoice checks.
*> 17/04/84 vbc - If openitm record skipped perform bypass-ageing.
*> 01/05/84 vbc - Unapplied cash= sales-unapplied if unapp&current
*>                 not zero.
*> 09/10/84 vbc - Chg read-sales-test, 2 c if non recpts present.
*> 03/03/09 vbc - Migration to open cobol v3.00.0.
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .03 Mod lpr.
*> 25/11/11 vbc - .04 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .05 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .06 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 29/05/13 vbc - .07 Clear a bug if OTM3 sorted file empty which should not arise but found in testing
*>                    so added error tests and msgs.
*> 24/10/16 vbc - .08 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 21/01/17 vbc - .09 Replace refs to maps99 by display msgs.
*> 25/01/17 vbc       Dry testing completed.
*> 09/02/17 vbc - .10 Updated FD/WS and replaced cobol verbs
*>                    for access to FH/DALs when not using Cobol files.
*>                    Sort requirements removed (sl165) when processing
*>                    RDB tables as the sort step removed in place of
*>                    read Table by Order.
*>                    Note: When using RDB tables there is no sorting,
*>                    Data is from selecting by order.
*> 10/12/22 vbc   .11 Added para after some sections 4 GC 3.2 warning msgs.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
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
*> copy "selsl.cob".
 copy "slselois.cob".
 copy "selprint.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdsl.cob".
 copy "slfdois.cob".
 copy "fdprint.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL120 (3.3.00)".
 77  Exception-Msg       pic x(25) value spaces.
 copy "print-spool-command.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*> copy "wsoi.cob".
 copy "slwsoi3.cob".
 copy "wssl.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
     03  Default-Record         pic x.
     03  Final-Record           pic x.
*>     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
     03  WS-Stock-Record        pic x.
*>     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
*>     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
     03  WS-Invoice-Record      pic x.
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
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
*>
 01  ws-data.
     03  menu-reply      pic 9.
     03  ws-reply        pic x.
     03  fs-reply2       pic 99.
     03  z               pic 99.
     03  y               pic 99.
     03  truth           pic 9 .
       88  a-true                         value  1.
       88  a-false                        value  0.
     03  first-time      pic 9            value zero.
     03  ws-spaces       pic x(80)        value spaces.
     03  st-date         pic x(8)         value spaces.
     03  work-1          pic s9(7)v99     value zero.
     03  work-2          pic s9(7)v99.
     03  display-8       pic z(5)9.99.
     03  display-5       pic zz9.99.
     03  a               pic s9(7) comp-3 value zero.
     03  b               pic s9(5) comp   value zero.
     03  i               pic 99.
     03  j               pic 99.
     03  k               pic 99.
     03  l-p             pic 99 value zero.
     03  customer-in     pic x(7)         value spaces.
     03  filler  redefines  customer-in.
       05  array-l       pic x  occurs  7.
     03  pay-date        binary-long.
     03  pay-value       pic s9(6)v99     value zero.
     03  pay-paid        pic s9(6)v99.
     03  last-read       pic x(7)         value spaces.
     03  page-nos        pic 99           value zero.
     03  line-cnt        pic 99           value 66.
     03  inv-amount      pic s9(7)v99     value zero.
     03  amount-out      pic s9(7)v99     value zero.
     03  entered-date    binary-long      value zero.
*>
 01  ws-amount-screen-display.
     03  ws-poundsd      pic 9(6).
     03  ws-period       pic x     value ".".
     03  ws-penced       pic v99.
 01  ws-amount-screen-accept redefines ws-amount-screen-display.
     03  ws-pound        pic 9(6).
     03  filler          pic x.
     03  ws-pence        pic v99.
*>
 01  ws-amount-work.
     03  amt-wk-pds      pic 9(6).
     03  amt-wk-pence    pic v99.
 01  ws-amount-ok redefines ws-amount-work.
     03  amt-ok          pic 9(6)v99.
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
     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
*> Module specific
     03  SL151          pic x(35) value "SL151 Sales Transactions Not Posted".
     03  Sl152          pic x(33) value "SL152 Payments Proofed Not Posted".
     03  SL153          pic x(37) value "SL153 No Open invoice records present".
*>
 01  analysis                                   comp-3.
     03  inv-0              pic s9(6)     value zero.
     03  inv-30             pic s9(6)     value zero.
     03  inv-60             pic s9(6)     value zero.
     03  inv-90             pic s9(6)     value zero.
     03  tot-bal-0          pic s9(8)v99  value zero.
     03  tot-bal-30         pic s9(8)v99  value zero.
     03  tot-bal-60         pic s9(8)v99  value zero.
     03  tot-bal-90         pic s9(8)v99  value zero.
     03  tot-os-bal         pic s9(8)v99  value zero.
     03  tot-no-pay         pic s9(5)     value zero.
     03  tot-no-cr-bal      pic s9(5)     value zero.
     03  tot-acct-active    pic s9(5)     value zero.
     03  tot-acct-live      pic s9(5)     value zero.
     03  tot-no-late        pic s9(5)     value zero.
     03  tot-no-unapp-pay   pic s9(5)     value zero.
     03  tot-amt-late       pic s9(7)v99  value zero.
     03  tot-amt-pay        pic s9(7)v99  value zero.
     03  tot-amt-cr-bal     pic s9(7)v99  value zero.
     03  tot-amt-unapp-pay  pic s9(7)v99  value zero.
     03  tot-unappl-credits pic s9(7)v99  value zero.
     03  tot-sales-bal      pic s9(7)v99  value zero.
*>
 01  balances                                    comp-3.
     03  bal-0           pic s9(7)v99 value zero.
     03  bal-30          pic s9(7)v99 value zero.
     03  bal-60          pic s9(7)v99 value zero.
     03  bal-90          pic s9(7)v99 value zero.
     03  bal-t           pic s9(7)v99 value zero.
     03  bal-pay         pic s9(7)v99 value zero.

 01  line-1.
     03  l1-version      pic x(56)       value spaces.
     03  filler          pic x(68)       value "Aged Debtors Report".
     03  filler          pic x(5)        value "Page ".
     03  l1-page         pic zz9.
*>
 01  line-3.
     03  l3-user         pic x(56)       value spaces.
     03  l3-list.
         05  l3-lcur     pic x(18)       value "Current Period is ".
         05  l3-period   pic z9          blank when zero.
     03  filler          pic x(46)       value spaces.
     03  l3-date         pic x(10).
*>
 01  line-4.
     03  filler          pic x(132)      value "Customer  Name                           Telephone  " &
         "   Invoice     Date       Current         30         60    90 & Over   Payments".
*>
 01  line-5  value spaces.
     02  l5-f1.
     03  l5-account      pic x(9).
     03  l5-name         pic x(32).
     03  l5-telephone    pic x(13).
     02  l5-title.
     03  l5-invoice      pic z(7)9       blank when zero.
     03  l5-hold         pic x.
     03  l5-late-only    pic x.
     03  l5-date         pic x(10).
     02  l5-f2.
     03  l5-less         pic x.
     03  l5-bal-0        pic zzzzzz9.99cr.
     03  l5-greater      pic x.
     03  l5-bal-30       pic zzzzzzz9.99.
     03  l5-bal-60       pic zzzzzzz9.99.
     03  l5-bal-90       pic zzzzzz9.99.
     03  l5-less-1       pic x.
     03  l5-payments     pic zzzzzz9.99.
     03  l5-greater-1    pic x.
*>
 01  line-6.
     03  l6-lover        pic x(5)        value spaces.
     03  l6-over         pic zzz,zz9.99bb  blank when zero.
     03  filler          pic x(7)        value "Terms:".
     03  l6-credit       pic z9bb.
     03  filler          pic x(13)       value "Credit Limit:".
     03  l6-limit        pic zzzz,zz9.
     03  filler          pic x(6)        value spaces.
     03  l6-lbalance     pic x(8)        value "Balance:".
     03  l6-balance      pic zzzz,zz9.99.
     03  l6-bal-0        pic zzzz,zz9.99cr.
     03  l6-bal-30       pic zzzz,zz9.99.
     03  l6-bal-60       pic zzzz,zz9.99.
     03  l6-bal-90       pic zzzz,zz9.99.
     03  l6-payments     pic zzzz,zz9.99.
*>
 01  line-7.
     03  filler          pic x(29)       value spaces.
     03  filler          pic x(103)      value "Total       Current         30           60       90 & Over".
*>
 01  line-8.
     03  l8-head.
         05 l8-hd1       pic x                value space.
         05 l8-hd2       pic x(24).
     03  l8-tot          pic zzzz,zz9.99cr.
     03  l8-0            pic zzzz,zz9.99cr.
     03  l8-30           pic zzzz,zz9.99cr.
     03  l8-60           pic zzzz,zz9.99cr.
     03  l8-90           pic zzzz,zz9.99cr.
*>
 01  line-10 redefines line-8.
     03  l10-head        pic x(25).
     03  l10-tot         pic zzzz,zz9bbbbb.
     03  l10-0           pic zzzz,zz9bbbbb.
     03  l10-30          pic zzzz,zz9bbbbb.
     03  l10-60          pic zzzz,zz9bbbbb.
     03  l10-90          pic zzzz,zz9.
*>
 01  line-9.
     03  filler          pic x(29) value spaces.
     03  filler          pic x(19) value "Number       Amount".
*>
 01  line-11.
     03  filler          pic x(25) value spaces.
     03  l11-f1          pic x(13) value all "-".
     03  l11-f2          pic x(13) value all "-".
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wssys4.cob".
 copy "wsnames.cob".
*>
 01  to-day              pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          system-record-4
                          to-day
                          file-defs.
*>=======================================
 init01 section.
*>
     display  " " at 0101 with erase eos.
*>
     if       s-flag-p = 1
              display SL152   at 2301
              display SL003   at 2401
              accept ws-reply at 2430
              go to menu-ent.
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
     move     to-day to u-date.
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-19    *> Open ITM3 file
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    display SL151   at 2301
                    display SL003   at 2401
                    accept ws-reply at 2430
                    go       to menu-ent.
*>
     display  prog-name at 0202 with foreground-color 2 erase eos.
     display  "Aged Debtors Report" at 0231 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0271 with foreground-color 2.
*>
     perform  Trail-Balance.
     perform  Report-Analysis.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 menu-ent.
     exit     program.
*>
*>****************************************************************
*>      p r o c e d u r e s                                      *
*>****************************************************************
*>
 trail-balance           section.
*>==============================
*>
     display  "****************************************" at 0441 with foreground-color 2.
     display  "*Date    [  /  /    ]                  *" at 0541 with foreground-color 2.
     display  "*A/C Nos [       ]                   ***" at 0641 with foreground-color 2.
     display  "*Value  [         ]*                   *" at 0741 with foreground-color 2.
     display  "****************************************" at 0841 with foreground-color 2.
*>
 main-display-end.
*>
     display  "Notes" at 1201 with foreground-color 2.
     display  "*****" at 1301 with foreground-color 2.
     display  " (1)  -  <Date>  :  Appears on listing" at 1501  with foreground-color 2.
     display  " (2)  -  <A/C>   :  A/c's to match for printing"	at 1601 with foreground-color 2.
     display  " (3)  -  <Value> :  Minimum o/s to print" at 1701 with foreground-color 2.
*>
 date-input.
     move     zero to cob-crt-status.
     display  ws-date at 0551 with foreground-color 3.
     accept   ws-date at 0551 with foreground-color 3 update.
     if       ws-date = spaces
              go to main-exit.
     move     ws-date to ws-test-date.
     perform  zz050-Validate-Date.
     if       u-bin = zero
              go to  date-input.
*>
     move     ws-date  to  l3-date.   *> was WS-test-date 10/01/18
     move     u-bin to entered-date.
*>
 customer-input.
     accept   customer-in at 0651 with foreground-color 3.
     move     function upper-case (customer-in) to customer-in.
*>
 value-input.
     move     0750 to curs.
     perform  accept-money.
     move     amt-ok to pay-value.
*>
     open     output print-file.
     move     zero  to  page-nos.
     perform  headings-1.
     perform  Sales-Open-Input.           *> open     input sales-file.
*>
     if       FS-Cobol-Files-Used
              open     input  open-item-file-s
              if       fs-reply not = zero
                       close open-item-file-s
                       open input open-item-file-s
                       display SL153  at 2450    *> No Open invoice records present
              end-if
     else
              perform  OTM3-Open-Input
 *>             if       fs-reply not = zero
 *>                      perform OTM3-Close
 *>                      go to Main-End
 *>             end-if
     end-if
*>
 *>    open     input open-item-file-s.
 *>    if       fs-reply not = zero
 *>             close open-item-file-s
 *>             open output open-item-file-s
 *>             close open-item-file-s
 *>             open input open-item-file-s
 *>             display SL153  at 2450.        *> No Open invoice records present
*>
     if       customer-in = spaces
              go to read-perform.
     move     customer-in to WS-Sales-Key.
     set      fn-not-less-than to true.
     move     1  to File-Key-No.
     perform  Sales-Start.            *> start sales-file key not < WS-Sales-Key invalid key
     if       fs-reply = 21
              move 1 to y.
     inspect  customer-in replacing all spaces by "Z".
*>
 read-perform.
     perform  read-sales.
*>
     if       fs-reply = 99 or = 10
              go to  main-end.
*>
     if       last-read = WS-Sales-Key
              go to roi-1.
*>
 read-open-item.
     if       last-read > WS-Sales-Key
              go to read-perform.
*>
     if       fs-reply2 = 99
              go to end-statement.
*>
     if       NOT FS-Cobol-Files-Used
              perform OTM3-Read-Next-Sorted-By-Cust
              if      fs-reply not = zero     *> = 10
                      move 99 to fs-reply2
                      go to    end-statement
              end-if
              go to Read-Loop-Tests
     end-if
*>
     read     open-item-file-s at end
              move 99 to fs-reply2
              go to    end-statement.
     if       fs-reply not = zero
              go to    end-statement.
*>
     move     open-item-record-s  to  oi-header.
*>
 Read-Loop-Tests.
     move     oi-customer  to  last-read.
*>
     if       last-read  >  WS-Sales-Key
              go to  end-statement.
*>
     if       last-read  not equal  WS-Sales-Key
              perform bypass-ageing
              go to  read-open-item.
 roi-1.
*>
*>  O-I transaction is for this customer.
*>
     if       oi-type = 1  or = 4
              go to  read-open-item.
*>
*> Can safely ignore receipts & pro-formas.
*>
     if       line-cnt > Page-Lines
              perform headings-1.
     if       oi-type = 5 or = 6
              move zero to oi-invoice.
     move     oi-invoice  to  l5-invoice.
     move     oi-hold-flag to l5-hold.
*>
     move     oi-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     ws-date   to  l5-date.
*>
*> Invoices only here
*>
     add      oi-net  oi-extra  oi-carriage
              oi-vat  oi-discount  oi-e-vat
              oi-deduct-amt oi-deduct-vat
              oi-c-vat    giving  inv-amount.
*>
     if       oi-type = 2
              subtract   oi-paid  from  inv-amount giving  amount-out.
*>
*> Cr. notes only here.
*>
     if       oi-type = 3
              add  oi-paid  to  inv-amount
              move  inv-amount  to  l5-bal-0
              perform check-zero
              go to bypass-ageing.
*>
*> Payments  only here.
*>
     if       oi-type = 5  or  6
              add   oi-paid  to  bal-pay
*>  subtract oi-approp from bal-pay
              perform check-zero
              go to bypass-ageing.
*>
     subtract oi-date  from  entered-date  giving  work-1.
*>
*> Now work out ageing
*> (dont worry if paid in full - routine still works ok)
*>   Also force credit balance into current
*>
     if       amount-out = zero
              move 0 to b
     else     move 1 to b.
*>
     if       amount-out is negative
              move 1 to work-1.
*>
     if       work-1  <  30
              add  amount-out  to  bal-0
              move amount-out to l5-bal-0
              perform check-zero
              add amount-out to tot-bal-0
              add b to inv-0
     else
      if      work-1  <  60
              add  amount-out  to  bal-30
              move amount-out to l5-bal-30
              add amount-out to tot-bal-30
              add b to inv-30
      else
       if     work-1  <  90
              add  amount-out  to  bal-60
              move amount-out to l5-bal-60
              add amount-out to tot-bal-60
              add b to inv-60
       else
              move amount-out to l5-bal-90
              add  amount-out to tot-bal-90
              add b to inv-90
              add  amount-out  to  bal-90.
*>
     add      amount-out  to  bal-t.
*>
 bypass-ageing.
*>
*> ie payment
*>
     if       oi-type = 5 or 6
         and  oi-deduct-amt not = zero
              add oi-deduct-amt to tot-amt-late
              add 1 to tot-no-late.
     if       oi-type = 5 or 6
              add  oi-paid  to  tot-amt-pay
              add  1  to  tot-no-pay.
*>
 bypass-age-go.
     if       oi-type = 3 and
              inv-amount not = zero
              add inv-amount to tot-unappl-credits.
*>
     if       oi-type = 2 and
              amount-out = oi-deduct-amt and
              amount-out not = zero
              move "L" to l5-late-only
      else
              move space to l5-late-only.
*>
     move     zero to amount-out.
*>
*> Now to print. What joy!!!!!!.
*>
     if       l5-account not = spaces
              write print-record from ws-spaces after 1
              add 1 to line-cnt.
     write    print-record  from  line-5 after 1.
     add      1 to line-cnt.
*>
*> Loop back for next item.
*>
     move     spaces  to  line-5.
     go       to read-open-item.
*>
*> Can only get here at the end of a statement.
*>
 end-statement.
*>************
*>
     move     bal-0   to  l6-bal-0.
     move     bal-30  to  l6-bal-30.
     move     bal-60  to  l6-bal-60.
     move     bal-90  to  l6-bal-90.
     move     bal-pay to  l6-payments.
*>
     if       l6-lbalance not = spaces
              write print-record  from  line-6 after 1
              write print-record  from  ws-spaces after 1
              move spaces to l6-lbalance
              add 2 to line-cnt.
*>
*> Set-up for the next one then zeroise counter fields.
*>
*> Now as promised some zeroising.
*>
     move     zero  to  bal-0   bal-30
                        bal-60  bal-90
                        bal-pay bal-t.
*>
*> Loop time.......get another punter.
*>
 end-statement-end.
*>
 item-end.
*>
     go       to read-perform.
*>
*> Above forces all sales records to be read & counted
*>
 accept-money.
*>-----------
*>
     move     zero to ws-poundsd amt-ok ws-penced.
     display  ws-amount-screen-display at curs.
     accept   ws-amount-screen-accept at curs.
     move     ws-pound to amt-wk-pds.
     move     ws-pence to amt-wk-pence.
*>
 main-end.
*>*******
*>
     if       FS-Cobol-Files-Used
              close    open-item-file-s          *>  sales-file.
     else
              perform OTM3-Close
     end-if
     perform  Sales-Close.
*>
 main-exit.   exit.
*>********    ****
*>
 headings-1              section.
*>==============================
*>
     if       line-cnt < Page-Lines
              go to main-exit.
     add      1  to  page-nos.
     move     page-nos  to  l1-page.
     move     prog-name to  l1-version.
     move     usera     to  l3-user.
     if       line-cnt not = 99
              move scycle to  l3-period.
*>
     if       page-nos not = 1
              write print-record from line-1 after page
              move  spaces  to  print-record
              write print-record after 1
     else
              write print-record from line-1 before 1
     end-if
     write    print-record  from  line-3 after 1.
     write    print-record  from  line-4 after 2.
     move     zero to line-cnt.
*>
 main-exit.   exit section.
*>********    ****
*>
 report-analysis          section.
*>===============================
*>
     move     "Account Statistics  " to l3-list.
     move     spaces to line-4.
     move     99 to line-cnt.
     perform  headings-1.
     write    print-record from line-7 after 1.
     write    print-record from ws-spaces after 1.
     move     "Number Of Invoices" to l10-head.
     move     inv-0  to l10-0.
     move     inv-30 to l10-30.
     move     inv-60 to l10-60.
     move     inv-90 to l10-90.
     add      inv-0 inv-30 inv-60 inv-90 giving a.
     move     a to l10-tot.
     write    print-record from line-10 after 1.
     move     "Amount" to l8-head.
     move     tot-bal-0  to l8-0.
     move     tot-bal-30 to l8-30.
     move     tot-bal-60 to l8-60.
     move     tot-bal-90 to l8-90.
     add      tot-bal-0 tot-bal-30 tot-bal-60 tot-bal-90 giving tot-os-bal.
*>
*>    Note that TOT-OS-BAL does NOT include credit balances.
*>
     move     tot-os-bal to l8-tot work-2.
     write    print-record from line-8 after 1.
     move     "% of O/S Invoices" to l8-head.
     move     100 to l8-tot.
     compute  work-1 rounded = (tot-bal-0 * 100) / work-2.
     move     work-1 to l8-0.
     compute  work-1 rounded = (tot-bal-30 * 100) / work-2.
     move     work-1 to l8-30.
     compute  work-1 rounded = (tot-bal-60 * 100) / work-2.
     move     work-1 to l8-60.
     compute  work-1 rounded = (tot-bal-90 * 100) / work-2.
     move     work-1 to l8-90.
     write    print-record from line-8 after 1.
     move     "Average O/S Amount" to l8-head.
     move     zero to l8-0 l8-30 l8-60 l8-90.
     if       inv-0 not = zero
              divide tot-bal-0 by inv-0 giving l8-0.
     if       inv-30 not = zero
              divide tot-bal-30 by inv-30 giving l8-30.
     if       inv-60 not = zero
              divide tot-bal-60 by inv-60 giving l8-60.
     if       inv-90 not = zero
              divide tot-bal-90 by inv-90 giving l8-90.
     divide   work-2 by a giving l8-tot.
     write    print-record from line-8 after 1.
     write    print-record from line-9 after 3.
     move     spaces to line-8.
     move     "Unapplied Cash" to l8-head.
     move     tot-amt-unapp-pay to l8-0.
     move     tot-no-unapp-pay to l10-tot.
     write    print-record from line-8 after 2.
     move     "Payments" to l8-head.
     move     sl-payments to l8-0.
     move     tot-no-pay  to l10-tot.
     write    print-record from line-8 after 1.
     move     "Credit Balances" to l8-head.
     move     tot-no-cr-bal to l10-tot.
     move     tot-amt-cr-bal to l8-0.
     write    print-record from line-8 after 1.
     move     "Late Charges" to l8-head.
     move     tot-amt-late to l8-0.
     move     tot-no-late to l10-tot.
     write    print-record from line-8 after 1.
     move     spaces to line-8.
     move     "Number of Live Accounts" to l10-head.
     move     tot-acct-live to l10-tot.
     write    print-record from line-10 after 1.
     move     "Number of Active Accounts" to l10-head.
     move     tot-acct-active to l10-tot.
     write    print-record from line-10 after 1.
     move     "% Active" to l8-head.
     compute  work-1 = (tot-acct-active * 100) / tot-acct-live.
     move     work-1 to l8-tot.
     write    print-record from line-8 after 1.
*>
     if       customer-in not = spaces
              go to main-exit.
*>
     move     spaces to line-10.
     move     "  Reconciliation Data" to l10-head.
     write    print-record from line-10 after 3.
     move     spaces to l10-head.
     write    print-record from line-10 after 1.
     move     sl-os-bal-last-month to l8-tot.
     move     "Balance Brought Forward" to l10-head.
     write    print-record from line-10 after 1.
     move     sl-invoices-this-month to l8-tot.
     move     "Plus: Invoices Posted" to l10-head.
     write    print-record from line-10 after 1.
*>     move     "      Unapplied CN Bal's" TO L10-HEAD.
*>     multiply -1 by sl-cn-unappl-this-month giving tot-bal-60.
*>     move     tot-bal-60 to l8-tot.
*>     write    print-record from line-10 after 1.
     add      sl-os-bal-last-month
              sl-invoices-this-month
*> tot-bal-60
                                     giving tot-bal-0.
     write    print-record from line-11 after 1.
     move     spaces to line-10.
     move     tot-bal-0 to l8-0.
     write    print-record from line-10 after 1.
     move     spaces to line-10.
     move     sl-credit-notes-this-month to l8-tot.
     move     "Less: Credit Notes Posted" to l10-head.
     write    print-record from line-10 after 2.
     move     sl-payments to l8-tot.
     move     "      Payments Posted" to l10-head.
     write    print-record from line-10 after 1.
     move     tot-amt-late to l8-tot.
     move     "      Pay Late Chgs Taken" to l10-head.
     write    print-record from line-10 after 1.
     move     "      CN Late Chgs Taken" to l10-head.
     move     sl-credit-deductions to l8-tot.
     write    print-record from line-10 after 1.
     write    print-record from line-11 after 1.
     add      tot-amt-late   sl-payments
              sl-credit-notes-this-month
              sl-credit-deductions       giving tot-bal-30.
     move     spaces to line-10.
     move     tot-bal-30 to l8-0.
     write    print-record from line-10 after 1.
     move     spaces to l11-f1.
     write    print-record from line-11 after 2.
     subtract tot-bal-30 from tot-bal-0.
     move     "Balance Carried Forward" to l10-head.
     move     tot-bal-0 to l8-0 sl-os-bal-this-month.
     write    print-record from line-10 after 1.
     move     all "=" to l11-f2.
     write    print-record from line-11 after 1.
     move     spaces to line-8.
     subtract tot-bal-0 from tot-sales-bal giving sl-variance.
     move     sl-variance to l8-tot.
     if       sl-variance not = zero
              move "Out Of Balance" to l8-hd2
              add sl-variance to sl-os-bal-this-month
              write print-record from line-10 after 2.
*>
 main-exit.
     exit     section.
*>
 read-sales   section.
*>*******************
*>
 Read-Sales-Main.
     perform  Sales-Read-Next.            *> read     sales-file  next  record at end
     if       fs-reply = 10
              move 99  to  fs-reply
              go to  main-end.
*>
     if       fs-reply not = zero
              move 99 to fs-reply
              go to main-end.
*>
     if       customer-in not = spaces
        and   WS-Sales-Key > customer-in
              move 99 to fs-reply
              go to main-end.
*>
     add      1 to tot-acct-live.
     add      sales-current to tot-sales-bal.
*>
     if       sales-unapplied not = zero
        and   sales-current not = zero
              add sales-unapplied to tot-amt-unapp-pay
              add 1 to tot-no-unapp-pay.
*>
     if       sales-unapplied not = zero
              subtract sales-unapplied from tot-sales-bal
              subtract sales-unapplied from sales-current.
*>
     if       sales-current negative
              add 1 to tot-no-cr-bal
              add sales-current to tot-amt-cr-bal.
*>
     perform  read-sales-test.
     if       a-false
              go to read-sales-Main.
*>
     add      1 to tot-acct-active.
     move     sales-name  to  l5-name.
     move     WS-Sales-Key  to  l5-account.
     move     sales-phone  to  l5-telephone.
     move     sales-current  to  l6-balance.
     move     "Balance:" to l6-lbalance.
     move     spaces     to l6-lover.
     move     sales-credit  to  l6-credit.
     move     sales-limit   to  l6-limit.
     if       sales-current > sales-limit
              subtract sales-limit from sales-current giving l6-over
              move "Over:" to l6-lover
     else     move zero to l6-over.
     if       sales-current is negative
              move "Cr Bal:" to l6-lbalance.
     perform  headings-1.
     if       sales-unapplied = zero
              go to main-end.
     move     sales-unapplied to l5-payments.
     move     "Unapplied Cash" to l5-title.
     add      sales-unapplied to bal-pay.
     write    print-record from line-5 after 2.
     move     spaces to line-5.
     add      2 to line-cnt.
     if       last-read not = WS-Sales-Key
              perform  end-statement.
     go       to main-end.
*>
 read-sales-test.
*>**************
*>
     move     1 to truth.
*>
     if       sales-current = zero
              move zero to truth.
*>
     if       sales-last-pay > sales-last-inv
              move sales-last-pay to pay-date
       else   move sales-last-inv to pay-date.
*>
     if       sales-current = zero
      and     pay-date > s-end-cycle-date
              move 1 to truth.
*>
     if       sales-current = zero and
              sales-last-pay not = zero and
              sales-last-pay = sales-last-inv
              move zero to truth
              perform test-for-inv.
*>
     if       pay-value not = zero
        and   sales-current  <  pay-value
              move zero to truth.
*>
 main-end.
*>*******
*>
     go       to main-exit.
*>
 test-for-inv.
*>***********
*>
     if       last-read = WS-Sales-Key
       and    oi-type not = 1
              move 1 to truth.
*>
 main-exit.   exit section.
*>********    *****
*>
 check-zero              section.
*>==============================
*>
     if       oi-type = 3
              go to test2.
     if       oi-type = 5 or 6
              go to test3.
     if       amount-out = zero
              move "<" to l5-less
              move ">" to l5-greater
              move oi-paid to l5-bal-0.
     go       to main-exit.
*>
 test2.
     if       inv-amount = zero
              move "<" to l5-less
              move ">" to l5-greater
              multiply oi-paid by -1 giving l5-bal-0.
     go       main-exit.
*>
 test3.
     if       oi-paid = oi-approp
              move "<" to l5-less-1
              move ">" to l5-greater-1
              move oi-paid to l5-payments
      else
              subtract oi-approp from oi-paid giving l5-payments.
*>
 main-exit.   exit section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*****************************************************
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
 main-exit.   exit section.
*>************************
 copy "Proc-ACAS-FH-Calls.cob".
*>
