       >>source free
*>***************************************************
*>                                                  *
*>                 Cash Posting                     *
*>                                                  *
*>***************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl100.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 24/10/83
*>                        For Applewood Computers.
*>
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Cash Posting.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas006  ->  OR 008
*>                         glpostingMT
*>                        acas008  ->
*>                         slpostingMT   *> IRS postings
*>                        acas013  ->
*>                         valueMT
*>                        acas019  ->
*>                         otm3MT.
*>**
*>    Error messages used.
*>                        SL002
*>                        SL132
*>                        SL137.
*>**
*>Changes.
*> 01/10/83 Vbc - Accum & Print Totals For Pay Deduct Approp.
*> 07/10/83 Vbc - Check For Non Current Payments In Loop,
*>                Remove Zeroize Io-Deduct-Amt In Cust-Update
*>                Which Has Been Moved To Sl150.
*> 24/10/83 Vbc - Cis Cobol Conversion.
*> 02/03/84 Vbc - Support For Sales-Unapplied Sales-Pay (Etc).
*> 02/04/84 Vbc - Subtract Deduct-AmtS To Value-File.
*> 10/05/84 Vbc - Support For Indexed Openitm File.
*> 24/09/84 Vbc - Support For Sl-Payments In Wssys4.
*> 21/02/85 Vbc - Change S-Flag-P To 2 On If Test.
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 03/04/09 vbc - IRS posting file support also in sl060.
*> 10/04/09 vbc - New feature Env variable ACAS_IRS.
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .08 Mod lpr.
*> 25/11/11 vbc - .09 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .10 Support for path+filenames and removed code dealing with Env vars
*>                    & setting up IRS path etc, as now done in menu program (sales)
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .11 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 25/03/12 vbc - .12 Restored GL/IRS postings, not sure why it was turned off
*> 24/10/16 vbc - .13 ALL programs now using wsnames.cob in copybooks
*> 30/10/16 vbc - .14 Support for RDB on Value table instead of cobol files
*>                    using acas013. Updated version to v3.02.
*> 24/11/16 vbc - .15 Support for RDB on (IRS) SPL posting file using acas008
*>                    & GL posting file using acas006
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 21/01/17 vbc - .16 Replace all refs to maps99 for display msgs.
*> 25/01/17 vbc       Dry testing completed.
*> 09/02/17 vbc - .17 Updated FD/WS and replaced cobol verbs
*>                    for access to FH/DALs - OTM3.
*> 23/08/17 vbc - .18 Rem out move ITM3 -> oi-header as same area.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*> 05/10/25 vbc - 3.3.01 Changes to BL open write & close for better support of
*>                       IRS and/or GL as a bit buggy ditto for PL060.
*>                       STILL NEEDS TO BE CHECKED WITH GL AS 2 fields not used??
*>                       and not sure what GL does - it is possible that sending
*>                       extra data to the GL posting file will not work as GL
*>                       may well have already updated the NL recs with the
*>                       posted amounts. Another reason to NOT use GL but use
*>                       IRS only. Applies to pl60,100, sl060, 100.
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
*>------------
*>
 copy "selprint.cob".
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 copy "fdprint.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(15)   value "SL100 (3.3.01)".
 77  exception-msg       pic x(25)   value spaces.
 copy "print-spool-command.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
     03  Default-Record         pic x.
     03  Final-Record           pic x.
*>     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
*>     03  WS-Posting-Record      pic x.
*>     03  WS-Batch-Record        pic x.
*>     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
     03  WS-Stock-Record        pic x.
*>     03  WS-Sales-Record        pic x.
*>     03  WS-Value-Record        pic x.
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
 01  ws-data.
     03  ws-reply        pic x.
     03  wx-reply        pic xxx   value spaces.
     03  xx              pic 99.
     03  i               pic 99.
     03  j               pic 99.
     03  k               pic 999.
     03  save-level-1    pic 9.
     03  line-cnt        binary-char           value zero.
     03  t-paid          pic s9(7)v99  comp-3  value zero.
     03  t-approp        pic s9(7)v99  comp-3  value zero.
     03  t-deduct        pic s9(7)v99  comp-3  value zero.
     03  j-paid          pic s9(7)v99  comp-3  value zero.
     03  j-approp        pic s9(7)v99  comp-3  value zero.
     03  j-deduct        pic s9(7)v99  comp-3  value zero.
     03  n-deduct        binary-long           value zero.
     03  work-1          pic s9(7)v99  comp-3  value zero.
     03  work-a          binary-long           value zero.
     03  work-b          binary-long           value zero.
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
     03  SL002          pic x(31) value "SL002 Note error and hit return".
*>     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
*> Module specific
     03  SL132          pic x(32) value "SL132 Err on Batch file write : ".
     03  SL137          pic x(26) value "SL137 Payments Not Proofed".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 copy "slwsoi3.cob".
*> copy "wsoi.cob".
 copy "wssl.cob".
 copy "wsbatch.cob".
 copy "wsval.cob".
 copy "wspost.cob".
 copy "wspost-irs.cob".
*>
 01  line-1.
     03  l1-name         pic x(56).
     03  filler          pic x(68)       value "Cash Posting Report".
     03  filler          pic x(5)        value "Page ".
     03  l1-page         pic zz9.
*>
 01  line-2.
     03  l2-user         pic x(56)       value spaces.
     03  filler          pic x(19)       value spaces.
     03  filler          pic x(47)       value spaces.
     03  l2-date         pic x(10).
*>
 01  line-4.
     03  filler          pic x(67)       value " Number   ---Date--  <------------Customer------------>  --Type-- ".
     03  filler          pic x(65)       value " Old Balance    New Balance    Payment   Deduction   Apportioned".
*>
 01  line-5.
     03  l5-batch        pic z(4)9.
     03  l5-slash        pic x.
     03  l5-item         pic 999b.
     03  l5-date         pic x(11).
     03  l5-cust         pic x(8).
     03  l5-name         pic x(25).
     03  l5-marker       pic x(4)        value spaces.
     03  l5-type         pic x(11).
     03  l5-old-bal      pic z(5)9.99cr.
     03  filler          pic x(3)        value spaces.
     03  l5-new-bal      pic z(5)9.99cr.
     03  filler          pic xx          value spaces.
     03  l5-paid         pic z(5)9.99b.
     03  filler          pic xx          value spaces.
     03  l5-deduct       pic z(5)9.99b.
     03  filler          pic x(4)        value spaces.
     03  l5-approp       pic z(5)9.99bb.
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
*>
 init01 section.
     move     prog-name to l1-name.
     move     Print-Spool-Name to PSN.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
*>*******************************************************  *> Turned back on 25/03/12
*> bypass gl posting code also see line 455             *
*>                                                      *
*>     move     level-1 to save-level-1.
*>     move     zero to level-1.
*>                                                      *
*>*******************************************************
     perform  zz070-Convert-Date.
     move     ws-date to l2-date.
*>
     if       S-Flag-P not = 2
              display SL137   at 2301
              display SL002   at 2401
              accept ws-reply at 2433
              go to menu-exit
     end-if.
*>
 menu-return.
*>
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "Sales Cash Posting" at 0133 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
*>
 acpt-xrply.
     display  "OK to Post Payment Transactions (YES/NO) ? [   ]"
                                                 at 1212 with foreground-color 2.
     move     spaces to wx-reply.
     accept   wx-reply at 1256 with foreground-color 6 update.
     move     function upper-case (wx-reply) to wx-reply.
     if       wx-reply = "NO"
              go to menu-exit.
     if       wx-reply not = "YES"
              go to acpt-xrply.
*>
     perform  OTM3-Open.        *> open i-o open-item-file-3 sales-file.
     perform  Sales-Open.
*>
     if       G-L
              perform  BL-Open.
*>
     open     output print-file.
     move     zero  to  j.
     perform  headings.
*>
 loop.
     perform  OTM3-Read-Next.       *> read open-item-file-3 next record at end
     if       fs-reply = 10
              go to  main-end.
*>
 *>    move     open-item-record-3  to  oi-header.
*>
     if       oi-type not = 2 and not = 5 and not = 6       *> invoices, payments, unapplied cash journal
              go to loop.
*>
     if       oi-type = 2 and
              oi-b-nos not = zero and
              oi-b-item not = zero
              perform compute-sales-pay thru csp-exit
              move zeros to oi-b-nos oi-b-item oi-cr        *> processed so clear batch info +
 *>              move oi-header to open-item-record-3
              perform OTM3-Rewrite       *> rewrite open-item-record-3
              go to loop.
*>
     if       s-closed or
              oi-type = 2
              go to  loop.
*>
     if       zero = oi-b-nos and oi-b-item
              go to loop.
*>
 cust-update.
*>**********
*>
     move     oi-customer  to  WS-Sales-Key  l5-cust.
*>
     move     space to ws-reply.
     perform  Sales-Read-Indexed.       *> read sales-file record invalid key
     if       fs-reply = 21
              move "X" to ws-reply.
     if       ws-reply = "X"
              move "!! Customer Unknown" to l5-name
     else
              move sales-name to l5-name.
*>
     move     oi-b-nos  to l5-batch.
     move     "/"       to l5-slash.
     move     oi-b-item to l5-item.
*>
     move     oi-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     u-date  to  l5-date.
*>
     move     oi-approp  to  l5-approp.
     move     oi-paid    to  l5-paid.
     move     oi-deduct-amt  to  l5-deduct.
*>
     if       oi-deduct-amt not = zero
              add 1 to n-deduct.
*>
     subtract sales-unapplied from sales-current giving l5-old-bal.
     subtract oi-approp from sales-current.
     subtract oi-deduct-amt  from  sales-current.
*>
     if       oi-paid not = oi-approp
              subtract oi-approp from oi-paid giving work-1
              add work-1 to sales-unapplied.
*>
     if       sales-current is negative
              multiply -1 by sales-current giving work-1
              add work-1 to sales-unapplied
              move zero to sales-current.
*>
     subtract sales-unapplied from sales-current giving l5-new-bal.
     move     oi-date  to  sales-last-pay.
*>
     if       oi-type = 5
              add oi-approp to t-approp
              add oi-paid   to t-paid sl-payments
              add oi-deduct-amt to t-deduct
      else
       if     oi-type = 6
              add oi-approp to j-approp
              add oi-paid   to j-paid
              add oi-deduct-amt to j-deduct.
*>
     move     oi-approp to oi-paid.
     perform  Sales-Rewrite.                   *> rewrite  sales-record.
*>
*> Yes for a non existant Sales rec the rewrite will fail so ignore error.
*>
     if       G-L
              perform  BL-Write.  *> what happens if using IRS ?
     move     1  to  oi-status.
*>
     perform  OTM3-Rewrite.    *> rewrite open-item-record-3 from oi-header.
*>
     if       oi-type = 6
              move "Cr Journal" to l5-type
     else
      if      oi-type = 5
              move "Payment"  to  l5-type.
     write    print-record  from  line-5 after 1.
     add      1 to line-cnt.
     if       line-cnt > Page-Lines
              perform  headings.
*>
     go       to loop.
*>
 main-end.
*>*******
*>
     perform  OTM3-Close.       *> close open-item-file-3 sales-file
     perform  Sales-Close.
*>
     move     spaces  to  line-5.
     move     "Payment Totals" to l5-name.
     move     t-approp to l5-approp.
     move     t-deduct to l5-deduct.
     move     t-paid   to l5-paid.
     write    print-record from line-5 after 3.
*>
     move     "Journal Totals" to l5-name.
     move     j-approp to l5-approp.
     move     j-deduct to l5-deduct.
     move     j-paid   to l5-paid.
     write    print-record from line-5 after 2.
     close    print-file.
     call     "SYSTEM" using print-report.
*>
     add      j-deduct to t-deduct.
     if       t-deduct not = zero
              perform Value-Open                *>   open i-o value-file
              perform analise-deductions
              perform Value-Close.              *>   close value-file.
*>
     if       G-L
              perform  BL-Close.
*>
*>     move     save-level-1 to level-1.           *> Turned back on 25/03/12
*>*******************************************
*>  >>> BYPASS CODE FOR G-L
*>
*>     move     save-level-1 to level-1.
*>
*>*******************************************
*>
     move     "Y"  to  oi-3-flag.
     move     zero to S-Flag-P.
*>
 menu-exit.
     exit     program.
*>
 headings.
     add      1  to  j.
     move     j  to  l1-page.
     move     usera  to  l2-user.
*>
     if       j not = 1
              write print-record from line-1 after page
              write print-record  from  line-2 after 1
              move spaces to print-record
              write print-record after 1
     else
              write print-record  from  line-1 before 1
              write print-record  from  line-2 before 1.
     write    print-record from line-4 after 1.
     move     spaces to print-record.
     write    print-record after 1.
     move     5 to line-cnt.
*>
 compute-sales-pay.
*>****************
*>
     if       oi-date-cleared = zero
              go to csp-exit.
*>
     subtract oi-date from oi-date-cleared giving work-a.
     move     zero to work-b.
*>
     if       sales-pay-activety not = zero
              multiply sales-pay-activety by sales-pay-average giving work-b.
*>
     add      work-a to work-b.
     add      1 to sales-pay-activety.
     divide   work-b by sales-pay-activety giving sales-pay-average.
*>
     if       work-a > sales-pay-worst
              move work-a to sales-pay-worst.
*>
 csp-exit.
     exit.
*>
 analise-deductions   section.
*>===========================
*>
     move     "Szd" to va-code.
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.         *> read value-file  invalid key
     if       FS-Reply = 21
              go to main-exit.
*>
     subtract n-deduct from va-t-this.
     subtract n-deduct from va-t-year.
     subtract t-deduct from va-v-this.
     subtract t-deduct from va-v-year.
*>
     move     1 to File-Key-No.
     perform  Value-Rewrite.          *> rewrite  value-record.
*>
     move     space  to  va-second.
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.        *> read     value-file  invalid key
     if       FS-Reply = 21
              go to main-exit.
*>
     subtract n-deduct from va-t-this.
     subtract n-deduct from va-t-year.
     subtract t-deduct from va-v-this.
     subtract t-deduct from va-v-year.
     perform  Value-Rewrite.          *> rewrite  value-record.
*>
 main-exit.   exit section.
*>
 BL-Open      section.
*>===================
*>
     perform  GL-Batch-Open.               *> open     i-o  batch-file.
*>
     move     next-batch  to  WS-Batch-Nos.
     move     3  to WS-Ledger.
     add      1  to Next-Batch.
     move     zero  to  batch-status
                        cleared-status.
     move     Scycle to  Bcycle.
     move     run-date  to  entered.
*>
     move     "Sales Ledger Payments"  to  description.
     move     zero  to  bdefault
                        batch-def-ac
                        batch-def-pc
                        items
                        input-gross
                        input-vat
                        actual-gross
                        actual-vat.
*>
     move     "CR"  to  convention.
     move     "SL"  to  batch-def-code.
     move     "O"   to  batch-def-vat.
     add      postings  1  giving  Batch-Start.
*>
     if       irs-used OR IRS-Both-Used     *> will open as o/p if not exist
              perform SPL-Posting-Open-Extend  *>   open extend irs-post-file *> needed: -  bug in OC
              if  fs-reply not = zero               *> wont happen in FH
                  perform SPL-Posting-Close         *>    close irs-post-file
                  perform SPL-Posting-Open-Output   *>    open output irs-post-file
              end-if
     end-if
     if       IRS-Both-Used or G-L
              perform GL-Posting-Open          *>  open i-o  Posting-file
              if  fs-reply not = zero               *> wont happen in FH
                  perform GL-Posting-Close          *>   close posting-file
                  perform GL-Posting-Open-Output    *>   open output posting-file.
              end-if
     end-if.
*>
     move     Batch-Start  to  RRN.
*>
 main-exit.   exit section.
*>********    ****
*>
 BL-Write     section.
*>===================
*>
*><<<<<<<<<<<<<<<<<<<<<<<<<<< READ THIS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
*>**********************************************************************
*>  This will write a posting record to GL or IRS for EACH line item   *
*>   in EACH invoice GL implies IRS, i.e., of or both.                 *
*> so, to use it, you MUST have set up the GL account number for EVERY *
*>  analysis code via Sl070. It also assumes that you have followed    *
*>  the convention in IRS that default a/c 31 points to VAT input      *
*>  and default a/c 32 is VAT output tax. The same applies to General. *
*>**********************************************************************
*>  u-date is in uk format
*>
     move     u-date (1:6) to post-date (1:6).
     move     u-date (9:2) to post-date (7:2).
     add      1       to  items.
     move     items   to  post-number.
     move     oi-paid to  post-amount.
*>
*> THIS DOES NOT APPEAR THE SAME as SL060 and PL060/PL100
*>
     move     1  to  xx.
     move     oi-b-nos to batch.
     string   batch delimited by size into post-legend pointer xx.
     move     WS-Batch-Nos  to  batch.
     string   "/" delimited by size into post-legend pointer xx.
     move     oi-b-item to k.
     string   k delimited by size into post-legend pointer xx.
     string   "  :  "   delimited  by size into post-legend pointer xx.
     string   sales-name delimited by size into post-legend pointer xx.
*>
     move     S-Debtors    to  post-cr.
     move     SL-Pay-AC    to  post-dr.
*>
     move     zero  to  dr-pc
                        cr-pc
                        VAT-AC of WS-Posting-record
                        vat-pc
                        VAT-Amount.
*>
     move     spaces  to  post-vat-side.
*>
     add      post-amount  to  input-gross.
     add      post-amount  to  actual-gross.
*>
     move     "SL"  to  post-code in WS-Posting-Record.
     move     "CR" to post-vat-side.
*>
     if       irs-used or IRS-Both-Used
              move Batch         to WS-IRS-Batch
              move Post-Number   to WS-IRS-Post-Number
              move Post-Code in WS-Posting-Record
                                 to WS-IRS-Post-Code
              move post-date     to WS-IRS-post-date
              move Post-DR       to WS-IRS-Post-DR
*> Missing usage of DR-PC   for GL MUST be checked in GL ????
              move Post-CR       to WS-IRS-Post-CR
*> Missing usage of CR-PC   for GL MUST be checked in GL ????
              move Post-Amount   to WS-IRS-Post-Amount
              move Post-Legend   to WS-IRS-Post-Legend
              move 32            to WS-IRS-vat-ac-def
                                    Vat-PC         *> IS IT ???
              move Post-Vat-Side to WS-IRS-Post-Vat-Side
              move Vat-Amount    to WS-IRS-vat-amount
              perform  SPL-Posting-Write         *>  write irs-posting-record
     end-if.
     if       IRS-Both-Used
           or G-L  *> (As set in params)
              move  RRN to WS-Post-RRN
              perform  GL-Posting-Write          *>  write posting-record
              add      1  to  RRN
     end-if.
*>
     if       items = 99
              perform  BL-Close
              perform  BL-Open.
*>
 main-exit.   exit section.
*>********    ****
*>
 BL-Close     section.
*>===================
*>
     perform  GL-Batch-Write.                 *> write    batch-record.
     if       fs-reply not = zero
              display SL132    at 2301
              perform Eval-Status
              display fs-reply at 2333
              display exception-msg at 2336
              display  SL002                       at 2401 with foreground-color 2
              accept ws-reply at 2430.
     if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
              move     RRN  to  postings.     *> Why ?
     perform  GL-Batch-Close.                   *>    close    Batch-file.
     if       IRS-Used OR IRS-Both-Used
              perform SPL-Posting-Close.      *>  close irs-post-file
     if       IRS-Both-Used or G-L
              perform GL-Posting-Close.       *>    close posting-file.
*>
 main-exit.   exit section.
*>
 Eval-Status        section.
*>=========================
*>
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by exception-msg.
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
