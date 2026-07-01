       >>source free
*>*************************************************
*>                                                *
*>           Payment  Data  Entry                 *
*>                                                *
*>*************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl080.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 18/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Payment Data Entry & Maintenance.
*>
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>
*>    Called Modules.     Maps04
*>                        acas012  ->
*>                         salesMT
*>                        acas019  ->
*>                         otm3MT.
*>**
*>    Error messages used.
*>                        SL116.
*>                        SL119.
*>                        SL121.
*>**
*>    Changes.
*>
*> 03/01/82 vbc - Check To See That All Invoices Are Posted.
*> 15/01/82 vbc - Increment Oi-P-C (Lines 300571&2  300660&70)
*> 08/02/83 vbc - 300790,300802,301162-66.
*> 19/02/83 Vbc - Allow Sales File To Be Updated By Turnover
*>                Figures Etc,(But Not Sales-Current>Done In Sl100)
*> 23/02/83 Vbc - Allow Payment Date To Over-Ride To-Days Date.
*> 26/02/83 Vbc - Force Sl115 To Sort By Setting Oi-3-Flag Before
*>                & After.
*> 25/03/83 Vbc - Accept Amount With Return, Check For Y & N More
*>                Data Etc.
*> 27/04/83 Vbc - Alter Apportion To Test Customer No Correctly To
*>                To Reduce Access And Run Times.
*> 30/04/83 Vbc - Remove Averaging & Movement Code Re Deductions.
*> 23/09/83 Vbc - Support Openitm Types 6 & 9, Clear Bug Allowing
*>                Pay-Paid > Pay-Value// Work-1.
*> 05/10/83 Vbc - Clean Up Displays In Various Areas.
*> 13/10/83 Vbc - Fix Bug On Not Closing Pd Inv If Paid Early
*>                    In Full.
*> 24/10/83 Vbc - Conversion To Cis Cobol.
*> 21/11/83 Vbc - Increase Batch No To 3 Digits.
*> 05/03/84 Vbc - Support For Sales-Unapplied.
*> 30/03/84 Vbc - Chg Payment Oi-Invoice To B-Nos*1000 + B-Item.
*> 13/04/84 Vbc - Chg Pay2high Maybe To Cover Paymt < Total Inv >
*>                 Total Inv - Deduct-Amt
*> 10/05/84 Vbc - Support Of Indexed Openitm File.
*> 16/05/84 Vbc - In Pay Details Display Inv Amt O/S At 21.
*> 25/09/84 Vbc - Check If Next-Batch = 0,Then Add 1.
*> 21/02/85 Vbc - Set S-Flag-P To 1
*> 05/03/85 Vbc - Replace Usage Of Next-Batch For First-Sl-Batch.
*> 03/03/09 vbc - Migration to Open GNU Cobol v3.00.00.
*> 19/03/09 vbc - Bug/Feature 30.6 allowed out thru Escape.
*> 25/11/11 vbc - .06 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .07 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .08 Changed usage of Stk-Date-Form to the global field
*>                    Date-Form making former redundent.
*> 24/10/16 vbc - .09 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*>                    Removed/replaced all refs to maps99 with displays
*>                    replaced file-status.
*> 23/01/17 vbc       Dry testing completed.
*> 07/02/17 vbc - .10 Updated FD/WS for 019 and replaced cobol verbs
*>                    for access to FH/DALs.
*> 10/12/22 vbc   .11 Added para after some sections 4 GC 3.2 warning msgs.
*> 03/04/23 vbc - .12 Using ws-lines for error msgs at start of prog.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
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
*> copy "selsl.cob".
*> copy "seloi3.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdsl.cob".
*> copy "fdoi3.cob".
 working-storage section.
*>----------------------
  77  prog-name           pic x(15)      value "SL080 (3.3.00)".
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 01  ws-amount-screen-display.
     03  ws-poundsd      pic 9(7).
     03  ws-period       pic x     value ".".
     03  ws-penced       pic v99.
 01  ws-amount-screen-accept redefines ws-amount-screen-display.
     03  ws-pound        pic 9(7).
     03  filler          pic x.
     03  ws-pence        pic v99.
*>
 01  ws-amount-work.
     03  amt-wk-pds      pic 9(7).
     03  amt-wk-pence    pic v99.
 01  ws-amount-ok redefines ws-amount-work.
     03  amt-ok          pic 9(7)v99.
*>
*> copy "wsoi.cob".
 copy "wssl.cob".
 copy "slwsoi3.cob".
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
*>     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
*>     03  WS-OTM3-Record         pic x.
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
 01  ws-data.
     03  ws-reply        pic x.
     03  z               pic 99.
     03  to-day          pic x(10).
     03  c-check         pic 9.
         88  c-exists                          value  1.
     03  work-1          pic 9(7)v99    comp-3 value zero.
     03  work-2          pic 999v99     comp-3 value zero.
     03  work-3          pic 9(7)v99    comp-3 value zero.
     03  work-net        pic s9(7)v99   comp-3 value zero.
     03  work-ded        pic 999v99     comp-3 value zero.
     03  work-av         pic s9(14)     comp-3 value zero.
     03  display-8       pic z(6)9.99.
     03  display-s       pic z(6)9.99cr.
     03  display-5       pic zz9.99.
     03  display-n       pic z(4)9.
     03  display-inv     pic z(7)9.
     03  i               pic 99.
     03  j               pic 99.
     03  k               pic 999.
     03  approp-amount   pic 9(6)v99    comp-3  value zero.
     03  deduct-taken    pic 9(6)v99    comp-3  value zero.
     03  pay-customer    pic x(7).
     03  pay-date        binary-long.
     03  pay-value       pic 9(7)v99     comp-3 value zero.
     03  batch-value     pic 9(7)v99     comp-3 value zero.
     03  pay-paid        pic s9(7)v99    comp-3 value zero.
     03  test-amount     pic s9(7)v99    comp-3 value zero.
     03  address-A       pic x(96).
     03  address-line    pic x(36).
     03  ws-dash         pic x(80)              value all "-".
     03  transaction-type pic 9                 value zero.
         88 trans-payment                       value 5.
         88 trans-unapplied                     value 6.
     03  ws-env-lines    pic 999                value zero.
     03  ws-lines        binary-char unsigned   value zero.
     03  ws-23-lines     binary-char unsigned   value zero.
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
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
*>       NONE
*> Module specific
     03  SL116           pic x(38) value "SL116 Note: and hit return to continue".
     03  SL119           pic x(35) value "SL119 Sales Transactions Not Posted".
     03  SL121           pic x(52) value
                        "SL121 Invoices Not Posted; Payment Entry Not Allowed".
*>
 01  error-code          pic 999.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  today               pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          today
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
     move     today to to-day.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
     if       S-Flag-I = 1
              display SL121   at 0501
              display SL116   at line ws-lines col 1  *> 2401
              accept ws-reply at line ws-lines col 40 *> 2440
              go to main-exit.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-19    *> Open ITM3 file
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    display  SL119  at line ws-23-lines col 1  *> 2301
                    display  SL116  at line ws-lines col 1  *> 2401
                    accept ws-reply at line ws-lines col 40  *> 2440
                    go to main-exit
              end-if
     end-if.
*>
 display-heads.
*>
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "Payment Data Entry" at 0133  with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
*>
 dh-exit.
*>
     move     zero  to  k.
     perform  OTM3-Open.    *> open i-o open-item-file-3  sales-file
     perform  Sales-Open.
     perform  New-Payment.
     perform  OTM3-Close.   *> close open-item-file-3 sales-file
     perform  Sales-Close.
*>
 menu-exit.
*>********
*>
     perform  display-heads.
     add      1  to first-sl-batch.
     move     "Y" to oi-3-flag.
*>
 main-exit.
     exit     program.
*>
*>********************************************
*>                Procedures                 *
*>********************************************
*>
 New-Payment  section.
*>===================
*>
 New-Payment-Main.
     move     4  to  lin.
     perform  display-heads.
*>
     display  "****************************************" at 0441  with foreground-color 2.
     display  "*Date    [  /  /    ]*A/C Nos [       ]*" at 0541  with foreground-color 2.
     display  "***                                  ***" at 0641  with foreground-color 2.
     display  "*Value   {          }*Batch [     /   ]*" at 0741  with foreground-color 2.
     display  "****************************************" at 0841  with foreground-color 2.
*>
 date-input.
*>*********
*>
     perform  zz070-Convert-Date.
     display  ws-date at 0551 with foreground-color 3.
     accept   ws-date at 0551 with foreground-color 3 update.
*>
     if       ws-date = spaces
         or   cob-crt-status = cob-scr-esc
              go to  main-exit.
*>
     move     ws-date to ws-test-date.
     move     zero  to  u-bin.
     perform  zz050-Validate-Date.
     if       u-bin = zero
              go to  date-input.
*>
     move     u-bin  to  pay-date.
     move     u-date to  to-day.
*>
 customer-input.
*>*************
*>
     if       k  =  999
              display "Batch Closed..It is Full!  " at 1041 with foreground-color 2
              go to  main-exit.
*>
     move     spaces to pay-customer.
     accept   pay-customer at 0572 with foreground-color 3 update UPPER.
     display  pay-customer at 0572 with foreground-color 3.
*>
     if       pay-customer = spaces
              go to date-input.
     if       cob-crt-status = cob-scr-esc
              go to  main-exit.
*>
     move     1  to  c-check.
     move     pay-customer  to  WS-Sales-Key.
*>
     perform  Sales-Read-Indexed.     *>  read sales-file record invalid key
     if       fs-reply = 21
              move  zero  to  c-check.
*>
     if       not  c-exists
              go to  customer-input.
*>
     move     sales-address  to  address-a.
     display  sales-name at 0401 with foreground-color 3.
*>
     move     1  to  z.
     unstring address-a  delimited by sl-delim into  address-line count z pointer  z.
     display  address-line at 0501 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited by sl-delim into  address-line count z pointer  z.
     display  address-line at 0601 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited by sl-delim into  address-line count z pointer  z.
     display  address-line at 0701 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  into  address-line pointer  z.
     display  address-line at 0801 with foreground-color 3.
*>
     move     spaces  to  address-line.
*>
     move     sales-current  to  display-s.
     display  "Current Balance - " at 1001  with foreground-color 2.
     display  display-s at 1019 with foreground-color 3.
*>
     move     5 to transaction-type.
     if       sales-unapplied = zero
              go to value-input.
*>
     move     sales-unapplied to display-8 amt-ok.
     display  "Unapplied Balance - " at 0645 with foreground-color 2.
     display  display-8 at 0665   with foreground-color 3.
     display  "Do you wish to allocate the Unapplied Balance to this account?  [Y]" at 1601 with foreground-color 2.
     move     "Y" to ws-reply.
*>
 accept-unappl-reqst.
*>------------------
*>
     move     zero to cob-crt-status.
     accept   ws-reply at 1666 with foreground-color 6 update UPPER.
     if       cob-crt-status = cob-scr-esc
              go to New-Payment-Main.
     if       ws-reply not = "Y" and not = "N"
              go to accept-unappl-reqst.
     if       ws-reply = "N"
              display " " at 1601 with erase eol
              go to value-input.
*>
     move     6 to transaction-type.
     display  " " at 1601 with erase eol.
     move     0749 to curs.
*>
 accept-unappl-money.
*>------------------
*>
     perform  accept-money2.
     if       amt-ok = zero
              go to New-Payment-Main.
     if       amt-ok > sales-unapplied
              go to accept-unappl-money.
*>
     subtract amt-ok from sales-unapplied.
     move     amt-ok to pay-value.
     perform  Sales-Rewrite.                *>  rewrite  sales-record.
     go       to set-batch-item.
*>
 value-input.
*>**********
*>
     move     0749 to curs.
     perform  accept-money.
     move     amt-ok to pay-value.
     if       pay-value = zero
              go to customer-input.
     if       cob-crt-status = cob-scr-esc
              go to  main-exit.
*>
     move     1 to s-flag-p.
     add      pay-value  to  batch-value.
     move     batch-value  to  display-s.
     display  "Batch Total - " at 1041 with foreground-color 2.
     display  display-s at 1055 with foreground-color 3.
*>
 set-batch-item.
*>-------------
*>
     if       first-sl-batch = zero
              move 1 to first-sl-batch.
     move     first-sl-batch  to  display-n.
     add      1  to  k.
     display  display-n at 0770 with foreground-color 3.
     display  k at 0776 with foreground-color 3.
*>
 data-input.
*>*********
*>
     perform  Payment-Appropriate.
     move     14  to  lin.
     perform  erase-screen.
*>
     display "Enter further payments (Y/N) ? [Y]" at 1629 with foreground-color 2.
*>
 more-data.
*>
     move     "Y"  to   ws-reply.
     accept   ws-reply at 1661 with foreground-color 6 update UPPER.
*>
     if       ws-reply = "Y"
              go to  New-Payment-Main.
     if       ws-reply not = "N"
              go to more-data.
     go       to main-exit.
*>
 accept-money.
*>-----------
*>
     move     zero to ws-poundsd amt-ok ws-penced.
     display  ws-amount-screen-display at curs with foreground-color 3.
     accept   ws-amount-screen-accept at curs  with foreground-color 3 update.
     move     ws-pound to amt-wk-pds.
     move     ws-pence to amt-wk-pence.
*>
 accept-money2.
*>------------
*>
     move     amt-wk-pence to ws-pence.
     move     amt-wk-pds to ws-pound.
     display  ws-amount-screen-display at curs with foreground-color 3.
     accept   ws-amount-screen-accept at curs  with foreground-color 3 update.
     move     ws-pound to amt-wk-pds.
     move     ws-pence to amt-wk-pence.
*>
 main-exit.   exit section.
*>
 Payment-Appropriate     section.
*>==============================
*>
     display   ws-dash at 1101 with foreground-color 2.
     display  "Inv.Nos  --Date--  --Amount--" at 1202  with foreground-color 2.
     display  "Deductable  ---Paid----" at 1233        with foreground-color 2.
     display  "Deduction Taken" at 1258                with foreground-color 2.
*>
     move     zero  to  approp-amount oi3-invoice.
     move     14  to  lin.
     move     pay-customer to oi3-customer.
     set      fn-not-less-than to true.
     perform  OTM3-Start.      *> start open-item-file-3 key not < oi3-key.
*>
 pay-loop.
*>*******
*>
     perform  OTM3-Read-Next.   *>  read open-item-file-3 next record  at end
     if       fs-reply = 10
              go to  main-end.
*>
  *>   move     open-item-record-3  to  oi-header. *> redefined.
*>
     if       oi-type not = 2
              go to  pay-loop.
*>
     if       oi-customer not = pay-customer
              go to main-end.
*>
     if       oi-b-nos not = zero
              go to pay-loop.
*>
     add      oi-net  oi-extra  oi-carriage  oi-vat oi-c-vat
              oi-discount  oi-e-vat giving work-net.
     add      oi-deduct-amt  oi-deduct-vat  giving work-ded.
     add      work-net work-ded giving test-amount.
     if       test-amount = oi-paid
        and   oi-status = zero
              move pay-date to oi-date-cleared
              move 1 to oi-status
              perform OTM3-Rewrite   *> rewrite open-item-record-3 from oi-header
              go to pay-loop.
*>
     if       test-amount  not >  oi-paid
              go to  pay-loop.
*>
 pay-details.
*>**********
*>
     move     1 to cole.
     display  " " at curs with erase eol.
     move     oi-invoice to display-inv.
     display  display-inv at curs with foreground-color 3.
*>
     move     oi-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     11 to cole.
     display  u-date at curs with foreground-color 3.
*>
     move     work-net to work-1.
     move     work-ded to work-2.
*>
     add      1  oi-deduct-days  to  u-bin.
     add      work-2  to  work-1.
     if       u-bin  >  pay-date
              subtract  work-2  from  work-1
              move  work-2  to  display-5
     else
              move  zero    to  display-5.
*>
     subtract oi-paid  from  work-1.
     move     work-1 to pay-paid.
     move     work-1  to  display-8.
     move     21 to cole.
     display  display-8 at curs with foreground-color 3.
*>
     move     35 to cole.
     display  display-5 at curs with foreground-color 3.
*>
     move     65 to cole.
     if       pay-paid = zero
              display "....Fully Paid  " at curs  with foreground-color 2
     else
              display " " at curs with erase eol.
*>
     if       pay-paid > pay-value
              subtract approp-amount from pay-value  giving pay-paid.
*>
     move     46 to cole.
     move     pay-paid to amt-ok.
     perform  accept-money2.
     move     amt-ok to pay-paid.
*>
     if       pay-paid = zero
              move  zero  to  pay-paid display-s
              move 46 to cole
              display display-s at curs with foreground-color 3
              move 65 to cole
              display "....No Change  " at curs  with foreground-color 2
              go to  end-line-2.
*>
     move     first-sl-batch  to  oi-b-nos.
     move     k  to  oi-b-item.
*>
 get-agreement.
*>************
*>
*>  If payment within discount term, discount has been
*>    subtracted from work-1
*>
     add      pay-paid  to  approp-amount.
*>
     if       approp-amount  >  pay-value
              go to  payment-2-high.
*>
     if       pay-paid = work-1
              move pay-date to oi-date-cleared
              move 1  to  oi-status
              if  u-bin  >  pay-date
                  move zero  to  oi-deduct-amt  oi-deduct-vat
                  add  work-2  to  deduct-taken
              end-if
              go to  end-line
     end-if
*>
*>   I.e., not paid within discount term & amt paid not = inv amt
*>     o/s (with deduct amt)
*>
     if       u-bin  not >  pay-date
              subtract  work-2  from  work-1.
     if       pay-paid > work-1
              go to payment-2-high-maybe.
     if       pay-paid not = work-1
              go to  end-line.
*>
*>   I.e., Amt paid < inv amt o/s
*>
     move     "Y"  to  ws-reply.
     move     65 to cole.
     display  ws-reply at curs with foreground-color 6.
     accept   ws-reply at curs with foreground-color 6 update UPPER.
*>
     if       ws-reply = "Y"
              move pay-date to oi-date-cleared
              move 1  to  oi-status
              add  work-2  to  deduct-taken
              move  zero  to  oi-deduct-amt  oi-deduct-vat.
*>
 end-line.
*>*******
*>
     add      pay-paid  to  oi-paid.
     add      pay-paid  to  oi-p-c.
     multiply 100 by pay-paid giving oi-cr.
     add      oi-deduct-amt oi-deduct-vat to work-net.
     if       oi-paid = work-net
              move pay-date to oi-date-cleared
              move 1 to oi-status.
*>
     perform OTM3-Rewrite.   *> rewrite open-item-record-3 from oi-header.
*>
 end-line-2.
*>
     add      1  to  lin.
     if       lin  >  23
              move  14  to  lin.
*>
     if       approp-amount  not <  pay-value
              go to  main-end.
     go       to pay-loop.
*>
 payment-2-high-maybe.
*>*******************
*>
*>   Check for paying late charge within time limit.
*>
     add      work-2 to work-1.
     if       pay-paid > work-1
              go to payment-2-high.
*>
     go       to end-line.
*>
 payment-2-high.
*>*************
*>
     subtract pay-paid  from  approp-amount.
     move     65 to cole.
     display  "Payment Too High" at curs with foreground-color 2.
     go       to pay-details.
*>
 main-end.
*>*******
*>
     move     zero to oi-extra oi-carriage oi-vat oi-discount
                      oi-e-vat  oi-c-vat  oi-status.
     move     zero to oi-cr oi-days oi-deduct-vat
                      oi-deduct-days oi-p-c.
     move     spaces to oi-description oi-applied oi-unapl
                         oi-hold-flag.
     move     pay-customer  to  oi-customer.
     move     pay-date  to  oi-date.
     move     transaction-type to  oi-type.
     move     pay-value to  oi-paid.
     move     approp-amount  to  oi-approp.
     move     deduct-taken   to  oi-deduct-amt.
     move     first-sl-batch  to  oi-b-nos.
     move     k  to  oi-b-item.
     multiply oi-b-nos by 1000 giving oi-invoice.
     add      oi-b-item to oi-invoice.
*>
     perform  OTM3-Write.      *> write open-item-record-3 from oi-header.
     move     zero  to  approp-amount  deduct-taken.
*>
 main-exit.   exit section.
*>********    ****.
*>
 erase-screen            section.
*>==============================
*>
     move     1 to cole.
     display  " " at curs with erase eos.
*>
 main-exit.   exit section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>****************************************************
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
