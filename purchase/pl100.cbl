       >>source free
*>***************************************************
*>                                                  *
*>               Payments Posting                   *
*>                                                  *
*>***************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         pl100.
*>**
*>    Author.             V B Coen FBCS, FIDM, FIDPM, 17/04/84
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Payments Posting.
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
*>                        acas029  ->
*>                         otm5MT.
*>**
*>    Error messages used.
*>                        PL002
*>                        PL132
*>                        PL137.
*>**
*>  Changes.
*> 24/09/84 Vbc - Support For Pl-Payments In Wssys4.
*> 22/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 03/04/09 vbc - IRS posting file support also in pl060.
*> 09/04/09 vbc - New feature Env variable ACAS_IRS.
*> 11/04/09 vbc - Bugs in page cnt & exit (section).
*> 13/04/09 vbc - make pay-ac post-cr instead of dr
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .13 Mod lpr.
*> 15/12/11 vbc - .14 Error msgs to SLnnn.Support for dates other than UK
*>                    Support for path+filenames and removed code dealing with Env vars
*>                    & setting up IRS path etc, as now done in menu program (sales)
*>                    Updated version to 3.01.nn
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 31/10/16 vbc - .15 Support for RDB on Value table instead of cobol files
*>                    using acas013.
*>                    Updated version to v3.02.
*> 10/01/18 vbc - .16 Support for RDB on (IRS) SPL posting file using acas008
*>                    & GL posting file using acas006
*>                    Replace all refs to maps99 for display msgs.
*>                    Updated FD/WS and replaced cobol verbs
*>                    for access to FH/DALs - OTM5.
*>                    Rem out move ITM3 -> oi-header as same area.
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
*>================================
*>
 copy "envdiv.cob".
 input-output            section.
*>-------------------------------
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
 77  prog-name           pic x(15)    value "PL100 (3.3.01)".
 77  exception-msg       pic x(25)    value spaces.
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
     03  WS-Sales-Record        pic x.
*>     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
*>     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
*>     03  WS-OTM5-Record         pic x.
*>
 01  ws-data.
     03  ws-reply        pic x                 value space.
     03  wx-reply        pic xxx               value spaces.
     03  xx              pic 99                value zero.
     03  i               pic 99                value zero.
     03  j               pic 99                value zero.
     03  k               pic 999               value zero.
     03  m               pic z(7)9.
     03  b               binary-char           value zero.
     03  c               binary-char           value zero.
     03  save-level-1    pic 9                 value zero.
     03  line-cnt        binary-char           value zero.
     03  n-deduct        binary-long           value zero.
     03  t-paid          pic s9(7)v99  comp-3  value zero.
     03  t-approp        pic s9(7)v99  comp-3  value zero.
     03  t-deduct        pic s9(7)v99  comp-3  value zero.
     03  j-paid          pic s9(7)v99  comp-3  value zero.
     03  j-approp        pic s9(7)v99  comp-3  value zero.
     03  j-deduct        pic s9(7)v99  comp-3  value zero.
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
     03  PL002          pic x(31) value "PL002 Note error and hit return".
*>     03  PL003          pic x(28) value "PL003 Hit Return To Continue".
*> Module specific
     03  PL132          pic x(32) value "PL132 Err on Batch file write : ".
     03  PL137          pic x(26) value "PL137 Payments Not Proofed".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
*> copy "wsoi.cob".
 copy "plwsoi5C.cob".
 copy "wspl.cob".
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
     03  filler          pic x(67)       value " Number   ---Date--- <-----------Supplier------------>  --Type-- ".
     03  filler          pic x(65)       value" Old Balance    New Balance    Payment   Deduction   Apportioned".
*>
 01  line-5.
     03  l5-batch        pic z9(4).
     03  l5-sl           pic x.
     03  l5-item         pic 999b.
     03  l5-date         pic x(11).
     03  l5-cust         pic x(8).
     03  l5-name         pic x(25).
     03  l5-marker       pic x(4)        value spaces.
     03  l5-type         pic x(10).
     03  l5-old-bal      pic z(6)9.99cr.
     03  filler          pic x(2)        value spaces.
     03  l5-new-bal      pic z(6)9.99cr.
     03  filler          pic x           value spaces.
     03  l5-paid         pic z(6)9.99b.
     03  filler          pic x           value spaces.
     03  l5-deduct       pic z(6)9.99b.
     03  filler          pic x(3)        value spaces.
     03  l5-approp       pic z(6)9.99b.
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
*>*******************************************************
*> bypass gl posting code also see line 101320          *
*>                                                      *
*>     move         level-1 to save-level-1.
*>     move         zero to level-1.
*>                                                      *
*>*******************************************************
     perform  zz070-Convert-Date.
     move     ws-date to l2-date.
*>
     if       p-flag-p not = 2
              display PL137   at 2301
              display PL002   at 2401
              accept ws-reply at 2433
              go to menu-exit
     end-if.
*>
 menu-return.
*>
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "Purchase Cash Posting" at 0132 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
 acpt-xrply.
     display  "OK to post payment transactions (YES/NO) ? <   > enter {CR}"
                                                 at 1212 with foreground-color 2.
     move     spaces to wx-reply.
     accept   wx-reply at 1256 with foreground-color 6 update.
     move     function upper-case (wx-reply) to wx-reply.
     if       wx-reply = "NO"
              go to menu-exit.
     if       wx-reply not = "YES"
              go to acpt-xrply.
*>
     perform  Purch-Open.  *> open i-o open-item-file-5 purchase-file.
     perform  OTM5-Open.
*>
     if       G-L
              perform  BL-Open.
*>
     open     output print-file.
     move     zero  to  j.
     perform  headings.
*>
 loop.
     perform  OTM5-Read-Next.  *> read open-item-file-5 next record at end
     if       fs-reply = 10
              go to  main-end.
*>
 *>    move     open-item-record-5  to  oi-header.
*>
     if       oi-type not = 2 and not = 5 and not = 6
              go to loop.
*>
     if       oi-type = 2 and
              oi-b-nos not = zero and
              oi-b-item not = zero
              perform compute-purch-pay thru csp-exit
              move zeros to oi-b-nos oi-b-item oi-cr
*>             move oi-header to open-item-record-5
              perform OTM5-Rewrite   *> rewrite open-item-record-5
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
     move     oi-supplier  to  WS-Purch-Key  l5-cust.
*>
     move     space to ws-reply.
     perform  Purch-Read-Indexed.  *> read purchase-file   record invalid key
     if       fs-reply = 21
              move "X" to ws-reply.
     if       ws-reply = "X"
              move "Supplier Unknown" to l5-name
     else
              move purch-name to l5-name.
*>
     move     oi-b-nos  to  l5-batch.
     move     "/" to l5-sl.
     move     oi-b-item to  l5-item.
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
     subtract purch-unapplied from purch-current giving l5-old-bal.
     subtract oi-approp     from purch-current.
     subtract oi-deduct-amt from purch-current.
*>
     if       oi-paid not = oi-approp
              subtract oi-approp from oi-paid giving work-1
              add work-1 to purch-unapplied.
*>
     if       purch-current is negative
              multiply -1 by purch-current giving work-1
              add work-1 to purch-unapplied
              move zero to purch-current.
*>
     subtract purch-unapplied from purch-current giving l5-new-bal.
     move     oi-date  to  purch-last-pay.
*>
     if       oi-type = 5
              add oi-approp to t-approp
              add oi-paid   to t-paid pl-payments
              add oi-deduct-amt to t-deduct
     else
       if     oi-type = 6
              add oi-approp to j-approp
              add oi-paid   to j-paid
              add oi-deduct-amt to j-deduct.
*>
     move     oi-approp to oi-paid.
     perform  Purch-Rewrite.  *> rewrite  purch-record.
*>
*> Yes for a non existant Purchase rec the rewrite will fail so ignore error.
*>
     if       G-L
              perform  BL-Write.
     move     1  to  oi-status.
*>
     perform  OTM5-Rewrite.  *> rewrite open-item-record-5 from oi-header.
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
     perform  OTM5-Close.  *> close purchase-file open-item-file-5.
     perform  Purch-Close.
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
     call     "SYSTEM" using Print-Report.
*>
     add      j-deduct to t-deduct.
     if       t-deduct not = zero
              perform Value-Open            *> open i-o value-file
              perform analise-deductions    *> perform analise-deductions
              perform Value-Close.          *> close value-file.
*>
     if       g-l
              perform  bl-close.
*>
*>*******************************************
*>  >>> BYPASS CODE FOR G-L
*>
*>     move     save-level-1 to level-1.
*>
*>*******************************************
*>
     move     "Y"  to  oi-5-flag.
     move     zero  to  P-Flag-P.
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
              write print-record  from  line-1 after page
              write print-record  from  line-2 after 1
              move spaces to print-record
              write print-record after 1
     else
              write print-record  from  line-1 before 1
              write print-record  from  line-2 before 1.
     write    print-record  from  line-4 after 1.
     move     spaces  to  print-record.
     write    print-record  after 1.
     move     5 to line-cnt.
*>
 compute-purch-pay.
*>****************
*>
     if       oi-date-cleared = zero
              go to csp-exit.
*>
     subtract oi-date from oi-date-cleared giving work-a.
     move     zero to work-b.
*>
     if       purch-pay-activety not = zero
              multiply purch-pay-activety by purch-pay-average giving work-b.
*>
     add      work-a to work-b.
     add      1 to purch-pay-activety.
     divide   work-b by purch-pay-activety giving purch-pay-average.
*>
     if       work-a > purch-pay-worst
              move work-a to purch-pay-worst.
*>
 csp-exit.
     exit.
*>
 analise-deductions   section.
*>===========================
*>
     move     "Pzb" to va-code.
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.   *> read value-file  invalid key
     if       FS-Reply = 21
              go to main-exit.
*>
     subtract n-deduct from va-t-this.
     subtract n-deduct from va-t-year.
     subtract t-deduct from va-v-this.
     subtract t-deduct from va-v-year.
*>
     move     1 to File-Key-No.
     perform  Value-Rewrite.  *> rewrite  value-record.
*>
     move     space  to  va-second.
     move     1 to File-Key-No.
     perform  Value-Read-Indexed. *> read value-file  invalid key
     if       FS-Reply = 21
              go to main-exit.
*>
     subtract n-deduct from va-t-this.
     subtract n-deduct from va-t-year.
     subtract t-deduct from va-v-this.
     subtract t-deduct from va-v-year.
     perform  Value-Rewrite. *> rewrite  value-record.
*>
 main-exit.   exit section.
*>
 bl-open      section.
*>===================
*>
     perform  GL-Batch-Open.               *> open i-o  batch-file.
*>
     move     bl-next-batch  to  WS-Batch-Nos.
     move     2  to  WS-Ledger.
     add      1  to  bl-next-batch.
     move     zero  to  batch-status cleared-status.
     move     Scycle to Bcycle.
     move     run-date  to  entered.
*>
     move     "Purchase Ledger Payments"  to  description.
     move     zero  to  bdefault
                        batch-def-ac
                        batch-def-pc
                        items
                        input-gross  input-vat
                        actual-gross actual-vat.
*>
     move     "DR"  to  convention.
     move     "PL"  to  batch-def-code.
     move     "I"   to  batch-def-vat.
     add      postings  1  giving  batch-start.
*>
     if       irs-used      *> will open as o/p if not exist
              perform SPL-Posting-Open-Extend  *>   open extend irs-post-file *> needed: -  bug in OC
     else                   *> will open as o/p if not exist
              perform GL-Posting-Open          *>  open i-o  Posting-file
     end-if.
*>
     move     batch-start  to  rrn.
*>
 main-exit.   exit section.
*>********    ****
*>
 bl-write     section.
*>===================
*>
*><<<<<<<<<<<<<<<<<<<<<<<<<<< READ THIS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
*>**********************************************************************
*>  This will write a posting record to GL or IRS for EACH line item   *
*>   in EACH invoice                                                   *
*> so, to use it, you MUST have set up the GL account number for EVERY *
*>  analysis code via pl070. It also assumes that you have followed    *
*>  the convention in IRS that default a/c 31 points to VAT input      *
*>  and default a/c 32 is VAT output tax.                              *
*>**********************************************************************
*>  u-date is in uk format
*>
     move     u-date (1:6) to post-date (1:6). *> using UK format
     move     u-date (9:2) to post-date (7:2).
     add      1       to items.
     move     items   to post-number.
     move     oi-paid to post-amount.
*>
*> using folio/invoice no + ' : ' supplier name instead of batch/item
*>  on posting file for both IRS & GL.
*>
     move     WS-Batch-nos  to  batch.
     move     oi-invoice to m.
     move     zero to b.
     inspect  m tallying b for leading space.
     subtract b from 8 giving c.
     add      1 to b.
     move     1  to  xx.
*>
     string   m (b:c)     delimited by size
              " : "       delimited by size
              purch-name  delimited by size into post-legend pointer  xx.
*>
     move     p-creditors  to  post-dr.
     move     bl-pay-ac    to  post-cr.
*>
     move     zero  to  dr-pc
                        cr-pc
                        vat-ac of WS-Posting-record
                        vat-pc
                        vat-amount.
*>
     move     spaces  to  post-vat-side.
*>
     add      post-amount  to  input-gross.
     add      post-amount  to  actual-gross.
*>
     move     "PL" to post-code in WS-Posting-record.
     move     "DR" to post-vat-side.
*>
     if       irs-used or IRS-Both-Used
              move WS-Post-key   to WS-IRS-Post-key
              move Post-Code in WS-Posting-Record
                                 to WS-IRS-Post-Code
              move post-date     to WS-IRS-post-date
              move Post-DR       to WS-IRS-Post-DR
*> Missing usage of DR-PC   for GL MUST be checked in GL ????
              move Post-CR       to WS-IRS-Post-CR
*> Missing usage of CR-PC   for GL MUST be checked in GL ????
              move Post-Amount   to WS-IRS-Post-Amount
              move Post-Legend   to WS-IRS-Post-Legend
              move 31            to WS-IRS-vat-ac-def
                                    Vat-PC         *> IS IT ???
              move Post-Vat-Side to WS-IRS-Post-Vat-Side
              move Vat-Amount    to WS-IRS-vat-amount
              perform  SPL-Posting-Write         *>  write irs-posting-record
     end-if
     if       IRS-Both-Used
           or G-L  *> (As set in params)
              move  RRN to WS-Post-RRN
              perform  GL-Posting-Write          *>  write posting-record
              add      1  to  RRN
     end-if
*>
     if       items = 99
              perform  bl-close
              perform  bl-open.
*>
 main-exit.   exit section.
*>********    ****
*>
 bl-close     section.
*>===================
*>
     perform  GL-Batch-Write.                 *> write    batch-record.
     if       fs-reply not = zero
              display PL132    at 2301
              perform Eval-Status
              display fs-reply at 2333
              display exception-msg at 2336
              display PL002                       at 2401 with foreground-color 2
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
