       >>source free
*>************************************************
*>                                               *
*>             Invoice Proof Report              *
*>                                               *
*>   This program does NOT update ANY files for  *
*>                this report.                   *
*>                                               *
*>************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl050.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 18/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Proof Report and Analysis.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas012 ->
*>                         salesMT
*>                        acas016 ->
*>                         invoiceMT
*>**
*>    Error messages used.
*>                        SL120
*>                        SL121
*>***
*>   Changes.
*> 08/01/83 vbc - 100215,500421+,005280,005360-90,101062-64.
*> 19/01/83 vbc - 005365-70,005140-200,500412-415,428-430
*>                500438,480,860,765,890,900,850-60,765,890,900.
*>                101350d,60,500120,1304286-8,4380-4400,4500-40.
*>                5400-6000,5330-35,5350d,5362,100160-70.
*>                500540-50,100777,100930,101046-51,101050-17000.
*>                520000-522700,004350d-,100290.
*> 09/04/83 Vbc - Allow For Credit Notes Totals.
*> 23/09/83 Vbc - Mod Print Writes To Use Line-Cnt.
*> 01/10/83 Vbc - On Reading Sales Check If Rec Missing.
*> 22/10/83 Vbc - Conversion To Cis Cobol.
*> 11/05/84 Vbc - Report On Vat Codes.
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 14/03/09 vbc - Tidy up totals & keep on same page if enough space.
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .06 Mod lpr.
*> 24/11/11 vbc - .07 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .08 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .09 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 01/06/13 vbc - .10 Minor tidy up of code with no functional changes eg replace zeroise by initialize etc
*>                    Increase VAT codes reporting from 3 to 5 with test for non zero, just in case
*>                    tax codes [options 4 & 5] are used.
*> 24/10/16 vbc - .11 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing
*>                    but still need invoicing.
*>                    Replaced all refs to file-status as redundant.
*> 23/01/17 vbc       Dry testing completed.
*> 07/02/17 vbc - .12 Updated to use FH & DALs replacing usage for sil- for
*>                    il and sih- for ih-.
*> 16/04/17 vbc -     Dry tested against slinvoiceMT but only needs head recs.
*>                    Same issue as in sl020, consider new functions for heads.
*> 18/04/17 vbc - .13 Updated to use Invoice-Read-Next-Header where only the
*>                    Header is wanted (if test = zero then read-next.
*>                    Cuts down unneeded reads of table. FH is still the same.
*> 22/03/18 vbc - .14 Chg or added msgs for no data with file test
*>                    Chg program title and report head - same for SL050.
*>                    If called by xl150 do not stop for any errors.
*> 15/06/20 vbc - .15 Extra test for reply when opening sales file JIC not exist.
*> 12/05/23 vbc - .16 Added Msg SL121 and replaced to it for no SL file.
*>                    Chngd to reporting on Proformas & confirm reporting on
*>                    vat rates 4 & 5. Light code clean up.
*> 20/05/23 vbc - .17 To Match sl020 added line item reporting. Is it ok ?
*> 07/08/23 vbc - .18 Nope code moved to analysis-print & use IL data.
*>                WHEN FIXED, UPDATE sl820 & pl820
*> 13/08/23 vbc - .19 Added PA, Vat code & percentage to line items and remove
*>                    analysis line as no longer needed. renove 1 line printed
*>                    from heads, Removed zz050 code - not used.
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
 copy "selprint.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 copy "fdprint.cob".   *> x(132)
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL050 (3.3.00)".
 copy "print-spool-command.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
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
*>     03  WS-Invoice-Record      pic x.
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
 01  ws-data.
     03  test-product.
         05  filler      pic x.
             88  il-comment              value "/".
         05  filler      pic x(11).
     03  ws-reply        pic x.
     03  ws-error        pic 9           value zero.
         88  Sales-Missing               value 1.
     03  a               pic 9           value zero.
     03  i               pic 99          value zero.
     03  j               pic 999         value zero.
     03  k               pic 99          value zero.
     03  l               pic 99          value zero.
     03  total-group    occurs 4      comp-3.
         05 total-ded    pic s9(8)v99.
         05 total-gds    pic s9(8)v99.
         05 total-car    pic s9(8)v99.
         05 total-net    pic s9(8)v99.
         05 total-vat    pic s9(8)v99.
         05 total-grs    pic s9(8)v99.
         05 total-dis    pic s9(8)v99.
         05 total-cvat   pic s9(8)v99    occurs 5.
     03  ws-deduct-amt   pic s999v99 comp-3 value zero.
     03  ws-deduct-vat   pic s999v99 comp-3 value zero.
     03  line-cnt        binary-char        value zero.
     03  WS-Lines        pic 99             value zero.     *> 07/08/23
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
     03  SL120          pic x(57) value "SL120 No Transactions to proof! ...Press return for menu.".
     03  SL121          pic x(59) value "SL121 Sales Ledger file not found .. Press return for menu.".
*>
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                         pic x(137).
 copy "wssl.cob".
*>
 01  ws-group-lits.
     03  filler          pic x(17)      value "Receipts".
     03  filler          pic x(17)      value "Invoices".
     03  filler          pic x(17)      value "Credit Notes".
     03  filler          pic x(17)      value "Pro-Formas".
 01  filler  redefines ws-group-lits.
     03  ws-lit          pic x(17)   occurs 4.
*>
 01  line-1.
     03  l1-version      pic x(49)       value spaces.
     03  filler          pic x(75)       value "Unapplied Sales Transaction Report".
     03  filler          pic x(5)        value "Page ".
     03  l3-page         pic zz9.
*>
 01  line-2.
     03  l3-user         pic x(49)       value spaces.
     03  filler          pic x(34)       value spaces.
     03  filler          pic x(39)       value spaces.
     03  l1-date         pic x(10).
*>
 01  line-4.
     03  filler          pic x(65)       value "  Number ---Date--- <------------Customer------------>  --Type--".
     03  filler          pic x(9)        value spaces.
     03  filler          pic x(57)       value " Goods   Anal Vat      <---Net-->  <---Vat-->  <--Gross->".
*>
 01 Line-4B.
     03  filler          pic x(75)       value space.
     03  filler          pic x(08)       value spaces.
     03  filler          pic x(8)        value "<-Code->".
*>
 01  line-5.
     03  l5-nos          pic z(7)9b.
     03  l5-date         pic x(11).
     03  l5-cust         pic x(7)B.
     03  l5-name         pic x(25).
     03  l5-marker       pic x(2)        value spaces.
     03  l5-type         pic x(15).
     03  l5-goods        pic z(6)9.99cr.
     03  filler          pic x(13)       value spaces.
     03  l5-net          pic z(6)9.99cr.
     03  l5-vat          pic z(6)9.99cr.
     03  l5-gross        pic z(6)9.99cr.
*>
*> Line item print
*>
 01  Line-5B.
     03  filler          pic x(45)      value spaces.
     03  L5B-Item-Desc   pic x(25).
     03  l5B-Goods       pic z(6)9.99cr.
     03  filler          pic xx         value spaces.
     03  L5B-pa          pic xx         value spaces.
     03  filler          pic xx         value spaces.
     03  L5B-Vat-Code    pic 9.
     03  filler          pic x(6)       value spaces.
     03  l5B-Net         pic z(6)9.99cr.
     03  l5B-Vat         pic z(6)9.99cr.
     03  l5B-Gross       pic z(6)9.99cr.
*>
*> Totals by type
*>
 01  line-6.
     03  filler          pic x(7)         value spaces.
     03  filler          pic x(6)         value "Total".
     03  l6-lit          pic x(18).
     03  l6-goods        pic z(6)9.99cr.
     03  l6-disc         pic z(6)9.99cr.
     03  l6-ded          pic z(6)9.99cr.
     03  l6-carr         pic z(6)9.99cr.
     03  l6-net          pic z(6)9.99cr.
     03  l6-vat          pic z(6)9.99cr.
     03  l6-gross        pic z(6)9.99cr.
*>
 01  line-7.
     03  filler          pic x(36)      value spaces.
     03  filler          pic x(78)      value "Goods    Discount  Prompt Pay    Carriage         Net         Vat       Gross".
*>
 01  line-8.
     03  filler          pic x(9)        value "Vat Code".
     03  L8-Code-Number.
         05  l8-vat-code pic 9.
         05  filler      pic xxx         value spaces.
     03  L8-Vat-Type   redefines L8-Code-Number
                         pic xxxB.
     03  l8-vat-rate     pic z9.99.
     03  filler          pic x(5)        value "%".
     03  l8-amount1      pic z(7)9.99cr.
     03  l8-amount2      pic z(9)9.99cr.
     03  l8-amount3      pic z(9)9.99cr.
     03  l8-amount4      pic z(9)9.99cr.
*>
 01  line-9.
     03  filler          pic x(79)      value "V.A.T. Reconciliation       Receipts       Invoices   Credit Notes    Proformas".
*>
 01  line-a.
     03  filler          pic x(45)       value spaces.
     03  la-a            pic x(12).
     03  la-code         pic x(6).
     03  la-b            pic x(8).
     03  la-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  la-c            pic x(9).                   *> "Vat Code"
     03  la-vat          pic z.
*>
 01  line-b.
     03  filler          pic x(45)       value spaces.
     03  lb-a            pic x(12)       value spaces.
     03  lb-code         pic x(6).
     03  lb-b            pic x(8)        value spaces.
     03  lb-amount       pic z(6)9.99cr   blank when zero.
*>
 01  line-c.
     03  filler          pic x(45)       value spaces.
     03  lc-a            pic x(12).
     03  lc-code         pic x(6)        value spaces.
     03  lc-b            pic x(8)        value spaces.
     03  lc-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  lc-c            pic x(9).
     03  lc-vat          pic z.
*>
 01  line-d.
     03  filler          pic x(45)       value spaces.
     03  ld-a            pic x(12).
     03  ld-code         pic x(6)        value spaces.
     03  ld-b            pic x(8)        value spaces.
     03  ld-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  ld-c            pic x(9).
     03  ld-vat          pic z.
*>
 01  line-e.
     03  filler          pic x(45)       value spaces.
     03  le-a            pic x(12).
     03  le-code         pic x(6)        value spaces.
     03  le-b            pic x(8)        value spaces.
     03  le-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  le-c            pic x(9).
     03  le-vat          pic z.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
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
     move     zero to a.
     perform  4 times
              add  1 to a
              initialize Total-Group (a)
     end-perform
*>
     move     prog-name to l1-version.
     perform  zz070-Convert-Date.
     move     ws-date to l1-date.
     move     1  to File-Key-No.
*>
 Menu-Return.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Invoice Proof Report" at 0132  with foreground-color 2.
     display  ws-date at 0171 with foreground-color 2.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-16
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    display SL120   at 0501 with foreground-color 4
                    if     WS-Caller not = "xl150"    *> Might be called by XL150 EOC (End of Cycle)
                           accept ws-reply at 0563 with foreground-color 6
                    end-if
                    goback.                         *> As no transactions.
*>
     perform  Sales-Open-Input.
     if       FS-Reply not = zero
                    display SL121   at 0501 with foreground-color 4
                    if     WS-Caller not = "xl150"    *> Might be called by XL150 EOC
                           accept ws-reply at 0563 with foreground-color 6
                    end-if
                    goback.                         *> As no transactions.
*>
     open     output print-file.
*>
     move     zero  to  j.
     perform  headings-1.
     perform  Invoice-Open-Input.
*>
 Get-Invoice-Record.
     perform  Invoice-Read-Next.   *> read invoice-file  next record  at end
     if       fs-reply = 10
              go to  Main-End.
*>
*> Trap transactions which are already on the sales ledger & OTM file.
*>
     if       applied
              go to Get-Invoice-Record.
*>
     move     zero to l.
     move     ih-customer to ws-Sales-Key  l5-cust.
     move     space to ws-reply.

     perform  Sales-Read-Indexed.
     if       fs-reply  = 21
              move "X" to ws-reply.
*>
     if       ws-reply = "X"
              move "!! Customer Unknown" to l5-name
              move 1 to ws-error
     else
              move sales-name  to  l5-name.
*>
     move     ih-invoice  to  l5-nos.
     move     ih-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     ws-date  to  l5-date.
*>
     move     ih-deduct-amt to ws-deduct-amt.
     move     ih-deduct-vat to ws-deduct-vat.
*>
     if       ih-type = 3                		*> Cr. Note  for Header Rec
              multiply  -1  by  ih-net
              multiply  -1  by  ih-extra
              multiply  -1  by  ih-carriage
              multiply  -1  by  ih-vat
              multiply  -1  by  ih-c-vat
              multiply  -1  by  ih-e-vat
              multiply  -1  by  ih-discount
              multiply  -1  by  ws-deduct-amt
              multiply  -1  by  ws-deduct-vat.
*>
     if       ws-deduct-amt = zero or = spaces
              move  spaces  to  lb-a  lb-code
              move  zero    to  lb-amount ws-deduct-amt
     else
              move  "Late Charge "  to  lb-a
              move  spaces          to  lb-code
              move  ws-deduct-amt   to  lb-amount.
*>
     if       ih-discount = zero or = spaces
              move  spaces  to  lc-a  lc-code  lc-c
              move  zero    to  lc-amount  lc-vat ih-discount
     else
              move  "Discount    "  to lc-a
              move  spaces          to lc-code  lc-c
              move  ih-discount     to lc-amount
              move  zero            to lc-vat.
*>
     if       ih-carriage = zero or = spaces
              move  spaces  to  ld-a  ld-code  ld-c
              move  zero    to  ld-amount  ld-vat ih-Carriage
     else
              move  "Carriage    "  to  ld-a
              move  spaces          to  ld-code  ld-c
              move  ih-carriage     to  ld-amount
              if    ih-c-vat = zero
                    move  zero  to  ld-vat
              else
                    move  1  to  ld-vat.
*>
     if       ih-extra = zero or = spaces
              move  spaces  to  le-a  le-code  le-c
              move  zero    to  le-amount  le-vat ih-Extra
     else
              move  extra-desc to  le-a
              move  spaces     to  le-code
              move  ih-extra  to  le-amount
              if    ih-e-vat = zero
                    move  zero to  le-vat
              else
                    move  1  to  le-vat.
*>
     if       Ih-Type > 0 and < 5
              move     ih-Type to a
              move     ws-lit (a) to L5-Type.
*>
     add      ih-c-vat ih-e-vat to total-cvat (a, 1).
*>
     move     ih-net  to  l5-goods.
     add      ih-vat  ih-c-vat  ih-e-vat  ws-deduct-vat giving  l5-vat.
     add      ih-net  ih-extra  ih-carriage  ih-discount ws-deduct-amt giving  l5-net.
     add      ih-vat  ih-c-vat  ih-e-vat  ws-deduct-vat
              ih-net  ih-extra  ih-carriage  ih-discount ws-deduct-amt giving  l5-gross.
*>
     add      ih-net  to  total-gds (a).
     add      ih-discount  ih-extra  to  total-dis (a).
     add      ws-deduct-amt to total-ded (a).
     add      ih-carriage  to  total-car (a).
     add      ih-vat  ih-c-vat  ih-e-vat  ws-deduct-vat to  total-vat (a).
     add      ih-net  ih-extra  ih-carriage  ih-discount ws-deduct-amt to  total-net (a).
     add      ih-vat  ih-c-vat  ih-e-vat  ws-deduct-vat
              ih-net  ih-extra  ih-carriage  ih-discount
              ws-deduct-amt to  total-grs (a).
*>
     if       line-cnt > Page-Lines - 2
              perform headings-1.
*>
     write    print-record from line-5 after 2.
     add      2 to line-cnt.
*>
     move     zero to fs-Reply.
     move     ih-Lines to WS-Lines.
     perform  Analysis-Print  WS-Lines times.
     perform  Extra-Analysis.
     go       to Get-Invoice-Record.   *> process Line items from file
*>
 Main-End.
     perform  Sales-Close.
     perform  Invoice-Close.
*>
     if       line-cnt < Page-Lines - 16
              move spaces to print-record
              write print-record after 3
     else
              perform  main12
     end-if
     write    print-record from line-7 after 2.
     move     spaces to print-record.
     write    print-record after 1.
     move     zero to a.
     perform  4 times    *> chgd 12/5/23 from 3 to 4 proformas
              add   1 to a
              move  total-gds (a) to  l6-goods
              move  total-dis (a) to  l6-disc
              move  total-car (a) to  l6-carr
              move  total-net (a) to  l6-net
              move  total-vat (a) to  l6-vat
              move  total-grs (a) to  l6-gross
              move  total-ded (a) to  l6-ded
              move  ws-lit (a)    to  l6-lit
              write print-record from line-6 after 1
     end-perform
*>
     if       Sales-Missing                    *> Should never happen but ...
              move "Warning Record/s Missing In Sales File" to print-record
              write print-record after 2
              write print-record after 2.    *> yes twice
*>
     write    print-record from line-9 after 2.
     move     spaces to print-record.
     write    print-record after 1.
     move     zero to i.   *> moved from within the perform above
     perform  3 times      *> the three vat rates
              add   1 to i
              move  i to l8-vat-code
              move  vat-rate (i) to l8-vat-rate
              move  total-cvat (1, i) to l8-amount1
              move  total-cvat (2, i) to l8-amount2
              move  total-cvat (3, i) to l8-amount3
              move  total-cvat (4, i) to l8-amount4
              write print-record from line-8 after 1
     end-perform
     if       Vat-Rate (4) not = zero    *> test if local tax in use & print if so
         or   Vat-Rate (5) not = zero    *> Both - Not used in the UK (so far)
              perform  2 times
                       add   1 to i
                       move  i to l8-vat-code
                       move  vat-rate (i) to l8-vat-rate
                       move  total-cvat (1, i) to l8-amount1
                       move  total-cvat (2, i) to l8-amount2
                       move  total-cvat (3, i) to l8-amount3
                       move  total-cvat (4, i) to l8-amount4
                       write print-record from line-8 after 1
              end-perform
     end-if
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 Menu-Call.   exit program.
*>
 Headings-1 section.
*>*****************
*>
 Main12.
     add      1  to  j.
     move     j  to  l3-page.
*>
     move     usera  to  l3-user.
     if       j not = 1
              write print-record from line-1 after page
     else
              write print-record from line-1 after 1.
     write    print-record from line-2 after 1.
*>
 Cont-HDs.
     write    print-record from line-4 after 2.
     write    print-record from line-4B after 1.
     move     spaces  to  print-record.
     move     5 to line-cnt.
*>
 Analysis-Print          section.
*>==============================
*>
     if       fs-reply = 99			*> Just in case
              go to Main-Exit.
     perform  Invoice-Read-Next.
     if       fs-reply = 10
              move 99 to fs-Reply		*> Just in case
              go to Main-Exit.
*>
     move     il-product   to  test-product.
     if       il-comment
              go to  main-exit.
*>
     if       il-type = 3                 *> credit notes
              multiply -1 by il-net
              multiply -1 by il-vat.
*>
*> Process line items
*>
     if       line-cnt > Page-Lines - 2
              perform headings-1.
     if       ih-test not = zeros           *> JIC but SHOULD be line items
              move     spaces to Line-5B
              move     il-Description to L5B-Item-Desc
              move     il-Vat-Code    to L5B-Vat-Code
              move     il-pa          to L5B-pa
              move     il-net         to l5B-goods
              move     il-Net         to L5B-Net
              move     il-Vat         to L5B-Vat
              add      il-Net il-Vat giving L5B-Gross
              write    print-record from line-5B after 1
              add      1 to line-cnt.
*>
     move     il-pa       to la-code.
     move     il-net      to la-amount.
     move     il-vat-code to la-vat k.
     if       k > zero
              add il-vat  to total-cvat (a, k).
*>
     move  spaces     to la-a  la-b  la-c.
*>
 main-exit.   exit section.
*>********    ****
*>
 extra-analysis          section.
*>==============================
*>
     if       line-cnt > Page-Lines - 4
              perform headings-1.
*>
     if       lb-a  not equal  spaces
              write  print-record  from  line-b after 1
              add 1 to line-cnt
              move  spaces  to  lb-a.
*>
     if       lc-a  not equal  spaces
              write  print-record  from  line-c after 1
              add 1 to line-cnt
              move  spaces  to  lc-a.
*>
     if       ld-a  not equal  spaces
              write  print-record  from  line-d after 1
              add 1 to line-cnt
              move  spaces  to  ld-a.
*>
     if       le-a  not equal  spaces
              write  print-record  from  line-e after 1
              add 1 to line-cnt
              move  spaces  to  le-a.
*>
 main-exit.   exit section.
*>********    ****
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
 zz060-Exit.  exit section.
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
 zz070-Exit.  exit section.
*>
 maps04       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit. exit section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
