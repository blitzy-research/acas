       >>source free
*>*******************************************************
*>                                                      *
*>            Payments - Due  File  Amendment           *
*>                                                      *
*>*******************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         pl920.
*>**
*>    Author.             V B Coen FBCS, FIDM, FIDPM,
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Payments Due Amendment.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas022
*>                         purchMT
*>                        acas032
*>                         paymentsMT
*>**
*>    Error messages used.
*>                        NONE
*>**
*>    Changes:
*> 22/03/09 vbc - 3.00.00 Migration to Open Cobol v3.00.00
*> 16/12/11 vbc -         Error msgs to SLnnn.Support for dates other than UK
*>                        Support for path+filenames.
*>                3.01.nn Updated version to 3.01.nn
*> 24/10/16 vbc - .       ALL programs now using wsnames.cob in copybooks.
*> 14/01/17 vbc -     .04 Change prog title to Payments from Cheque.
*> 11/01/18 vbc - 3.02.05 Updated to v3.02 using RDB.
*> 16/04/24 vbc           Copyright notice update superseding all previous notices.
*> 29/08/25 vbc       .06 Add test for FS-Reply =  21 to include = 23 as well.
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
*> copy "selpl.cob".
*> copy "selpay.cob".
 data                    division.
*>===============================
*>
 file section.
*>------------
*>
*> copy "fdpl.cob".
*> copy "fdpay.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "PL920 (3.3.00)".
 copy "wsfnctn.cob".
 copy "plwsoi.cob".
*>
*> Ex FDs
*>
 copy "wspl.cob".     *> WS-Purch-Record.
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
     03  WS-OTM5-Record         pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  ws-data.
     03  y               pic 9.
     03  z               pic 99.
     03  display-8       pic z(6)9.99.
     03  display-folio   pic z(7)9.
     03  ws-pay-nos      pic 99        value zero.
     03  ws-pay-invoice  pic x(10).
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
 copy "wsmaps03.cob".
*>
*> 01  Error-Messages.
*> System Wide
*>     03  PL005          pic x(18) value "PL005 Invalid Date".
*> Module specific
*>     NONE
*>
 linkage section.
*>==============
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
 init section.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Payment Due Amendment" at 0130 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
     move     1 to File-Key-No.  *> Good for all files/tables used here.
     perform  Payment-Amend.
     perform  Purch-Close.
     perform  Payments-Close. *> close purchase-file pay-file.
*>
 menu-exit.
     exit     program.
*>
 Payment-Amend section.
*>====================
*>
     perform  Purch-Open-Input. *>  open input purchase-file.
     perform  Payments-Open.    *> open i-o   pay-file.
*>
 read-purchase.
     display  "Supplier - [       /  ]" at 0501  with foreground-color 2.
     perform  varying z from 1 by 1 until z > 9
              add     8  z  giving  lin
              move    1 to cole
              display z at curs with foreground-color 3
              move    3 to cole
              display "   {        } [          ]" at curs  with foreground-color 2
     end-perform.
*>
 get-key.
     move     spaces to pay-supl-key.
     accept   pay-supl-key at 0513 with foreground-color 3 UPPER.
 *>    move     function upper-case (pay-supl-key) to pay-supl-key.
*>
     if       pay-supl-key = spaces
              go to  main-exit.
*>
     move     01  to  ws-pay-nos.
     accept   ws-pay-nos at 0521 with foreground-color 3 update.
     move     ws-pay-nos to pay-nos.
*>
     perform  Payments-Read-Indexed.  *>  read     pay-file invalid key
     if       fs-reply = 21 or = 23
              go to  get-key.
*>
     move     pay-supl-key  to  WS-Purch-Key.
     perform  Purch-Read-Indexed.  *>  read purchase-file invalid key
     if       fs-reply = 21 or = 23
              go to get-key.
     display  purch-name at 0526 with foreground-color 3.
*>
     perform  varying z from 1 by 1 until z > 9
              add  8  z  giving  lin
              move pay-folio (z) to display-folio
              move pay-value (z) to display-8
              move 7 to cole
              display  display-folio at curs  with foreground-color 3
              move 18 to cole
              display display-8 at curs with foreground-color 3
              move    32 to cole
              move    pay-invoice (z) to ws-pay-invoice
              display ws-pay-invoice at curs with foreground-color 3
     end-perform.
*>
 get-change.
*>*********
*>
     display  "Gross - [           ]" at 0556  with foreground-color 2.
     move     pay-gross  to  display-8.
     display  display-8 at 0565 with foreground-color 3.
     display  "line to alter - [ ]" at 2201 with foreground-color 2.
     accept   y at 2218 with foreground-color 6.
*>
     if       y = zero
              go to  write-back.
*>
     if       pay-value (y) = zero
              go to  get-change.
*>
     add      8  y  giving  lin.
     subtract pay-value (y) from pay-gross.
*>
     move     18 to cole.
     move     pay-value (y) to amt-ok.
     perform  accept-money2.
     move     amt-ok to pay-value (y).
     add      pay-value (y)  to  pay-gross.
     go       to get-change.
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
     display  ws-amount-screen-display at curs  with foreground-color 3.
     accept   ws-amount-screen-accept at curs   with foreground-color 3 update.
     move     ws-pound to amt-wk-pds.
     move     ws-pence to amt-wk-pence.
*>
 write-back.
*>*********
*>
     perform  Payments-Rewrite. *>  rewrite  pay-record.
     go       to get-key.
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
