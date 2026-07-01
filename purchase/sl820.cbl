       >>source free
*>************************************************
*>                                               *
*>           Slautogen Proof Report              *
*>                                               *
*>   This program does NOT update ANY files for  *
*>                this report.                   *
*>                                               *
*>
*>   For Purchase - sl810 - 830 needs to be converted for puchase and
*>   program names changed to pl810 - 830.
*>   AS the need for PL appears not to be wanted by users as no one has
*>   asked for them development has Stopped / Paused.
*>
*>************************************************
*>
*>  CHANGES NEEDED -
*>  5.  CONSIDER USING CURRENT STOCK REC FOR PRICING DATA
*>  6.  DITTO FOR POSTING AS SUCH COULD WELL CHANGE OVER TIME.
*>  7.  ANY OTHERS NEEDED ?????
*>

 identification         division.
*>==============================
*>
      program-id.       sl820.
*>**
*>    Author.           Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 18/10/83
*>                      For Applewood Computers.
*>**
*>    Security.         Copyright (C) 1976-2025 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          SLautogen Proof Report and Analysis.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.   Maps04.
*>                      acas012 ->
*>                       salesMT
*>                      acas004 ->
*>                       slautogenMT
*>**
*>    Error messages used.
*>                      SL120
*>                      SL121
*>***
*>    Changes.
*> 12/05/23 vbc - .00 Created sl820 (Autogen Proof) from sl050.
*>                    Removed old change notes from (sl050).
*>                    Added Msg SL121. Chg using Invoice to SLautogen.
*>                    Include proformas and removed CR.Note and Receipt
*>                    processing.
*> 14/08/23 vbc - .01 Updated to include changes in sl050 3.02.19.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>*************************************************************************
*>
*>  From copyright.cob.
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 2024-04-16.
*>
*> These files and programs are part of the Applewood Computers Accounting
*> System and is Copyright (c) Vincent B Coen. 1976-2025 and later.
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
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 copy "fdprint.cob".  *>  x(132)
 working-storage section.
*>----------------------
 77  prog-Name           pic x(15) value "SL820 (3.3.00)".
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
*>     03  WS-Invoice-Record      pic x.  *> Used for SLautogen rec
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
 01  WS-data.
     03  test-product.
         05  filler      pic x.
             88  il-comment             value "/".
         05  filler      pic x(11).
     03  WS-reply        pic x.
     03  WS-error        pic 9          value zero.
         88  Sales-missing              value 1.
     03  a               pic 9          value zero.
     03  i               pic 99         value zero.
     03  j               pic 999        value zero.
     03  k               pic 99         value zero.
     03  l               pic 99         value zero.
     03  Total-group    occurs 4     comp-3.
         05 Total-ded    pic s9(8)v99.
         05 Total-gds    pic s9(8)v99.
         05 Total-car    pic s9(8)v99.
         05 Total-net    pic s9(8)v99.
         05 Total-VAT    pic s9(8)v99.
         05 Total-grs    pic s9(8)v99.
         05 Total-dis    pic s9(8)v99.
         05 Total-cvat   pic s9(8)v99    occurs 5.
     03  WS-Deduct-Amt   pic s999v99 comp-3 value zero.
     03  WS-Deduct-VAT   pic s999v99 comp-3 value zero.
     03  Line-cnt        binary-char        value zero.
     03  WS-Lines        pic 99             value zero.     *> 07/08/23
*>
 01  WS-Test-Date            pic x(10).
 01  WS-date-formats.
     03  WS-swap             pic xx.
     03  WS-Conv-Date        pic x(10).
     03  WS-date             pic x(10).
     03  WS-UK redefines WS-date.
         05  WS-days         pic xx.
         05  filler          pic x.
         05  WS-month        pic xx.
         05  filler          pic x.
         05  WS-year         pic x(4).
     03  WS-USA redefines WS-date.
         05  WS-usa-month    pic xx.
         05  filler          pic x.
         05  WS-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  WS-Intl redefines WS-date.
         05  WS-intl-year    pic x(4).
         05  filler          pic x.
         05  WS-intl-month   pic xx.
         05  filler          pic x.
         05  WS-intl-days    pic xx.
*>
 01  Error-Messages.
*> System Wide
*>       NONE
*> Module specific
     03  SL120          pic x(66) value "SL120 No Autogen Transactions to report! .. Press return for menu.".
     03  SL121          pic x(59) value "SL121 Sales Ledger file not found .. Press return for menu.".
*>
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                         pic x(137).
 copy "wssl.cob".
*>
 01  WS-group-lits.
     03  filler          pic x(17)      value "Receipts".
     03  filler          pic x(17)      value "Invoices".
     03  filler          pic x(17)      value "Credit Notes".
     03  filler          pic x(17)      value "Pro-Formas".
 01  filler  redefines WS-group-lits.
     03  WS-lit          pic x(17)   occurs 4.
*>
 01  Line-1.
     03  l1-version      pic x(44)      value spaces.
     03  filler          pic x(80)      value "  Sales Autogen Report".
     03  filler          pic x(5)       value "Page ".
     03  l3-page         pic zz9.
*>
 01  Line-2.
     03  l3-user         pic x(49)      value spaces.
     03  filler          pic x(34)      value spaces.
     03  filler          pic x(39)      value spaces.
     03  l1-date         pic x(10).
*>
 01  Line-4.
     03  filler          pic x(66)      value "Invoice  ---Date--- <------------Customer------------>  --Type--".
     03  filler          pic x(9)       value spaces.
     03  filler          pic x(57)      value "Goods   Anal Vat      <---Net-->  <---VAT-->  <--Gross->".
*>
 01 Line-4B.
     03  filler          pic x(75)       value space.
     03  filler          pic x(08)       value spaces.
     03  filler          pic x(8)        value "<-Code->".
*>
 01  Line-5.
     03  filler          pic x(9).
     03  l5-date         pic x(11).
     03  l5-cust         pic x(8).
     03  l5-Name         pic x(25).
     03  l5-marker       pic x(2)       value spaces.
     03  l5-type         pic x(15).
     03  l5-goods        pic z(6)9.99cr.
     03  filler          pic x(13)      value spaces.
     03  l5-net          pic z(6)9.99cr.
     03  l5-VAT          pic z(6)9.99cr.
     03  l5-gross        pic z(6)9.99cr.
*>
*> Line item print
*>
 01 Line-5B.
     03  filler          pic x(45)      value spaces.
     03  L5B-Item-Desc   pic x(25).
     03  l5B-Goods       pic z(6)9.99cr.
     03  filler          pic xx         value spaces.
     03  L5B-pa          pic xx         value spaces.
     03  filler          pic xx         value spaces.
     03  L5B-VAT-Code    pic 9.
     03  filler          pic x(6)       value spaces.
     03  l5B-Net         pic z(6)9.99cr.
     03  l5B-VAT         pic z(6)9.99cr.
     03  l5B-Gross       pic z(6)9.99cr.
*>
*> Totals by type
*>
 01  Line-6.
     03  filler          pic x(7)       value spaces.
     03  filler          pic x(6)       value "Total".
     03  l6-lit          pic x(18).
     03  l6-goods        pic z(6)9.99cr.
     03  l6-disc         pic z(6)9.99cr.
     03  l6-ded          pic z(6)9.99cr.
     03  l6-carr         pic z(6)9.99cr.
     03  l6-net          pic z(6)9.99cr.
     03  l6-VAT          pic z(6)9.99cr.
     03  l6-gross        pic z(6)9.99cr.
*>
 01  Line-7.
     03  filler          pic x(36)      value spaces.
     03  filler          pic x(78)      value "Goods    Discount  Prompt Pay    Carriage         Net         Vat       Gross".
*>
 01  Line-8.
     03  filler          pic x(9)       value "Vat Code".
     03  L8-Code-Number.
         05  l8-VAT-code pic 9.
         05  filler      pic xxx         value spaces.
     03  L8-VAT-Type   redefines L8-Code-Number
                         pic xxxB.
     03  l8-VAT-rate     pic z9.99.
     03  filler          pic x(5)       value "%".
     03  l8-amount1      pic z(7)9.99cr.
     03  l8-amount2      pic z(9)9.99cr.
     03  l8-amount3      pic z(9)9.99cr.
     03  l8-amount4      pic z(9)9.99cr.
*>
 01  Line-9.
     03  filler          pic x(79)      value "V.A.T. Reconciliation       Receipts       Invoices   Credit Notes   Proformas".
*>
 01  Line-a.
     03  filler          pic x(45)       value spaces.
     03  la-a            pic x(12).
     03  la-code         pic x(6).
     03  la-b            pic x(8).
     03  la-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  la-c            pic x(9).                   *> "Vat Code"
     03  la-VAT          pic z.
*>
 01  Line-b.
     03  filler          pic x(45)       value spaces.
     03  lb-a            pic x(12)       value spaces.
     03  lb-code         pic x(6).
     03  lb-b            pic x(8)        value spaces.
     03  lb-amount       pic z(6)9.99cr   blank when zero.
*>
 01  Line-c.
     03  filler          pic x(45)       value spaces.
     03  lc-a            pic x(12).
     03  lc-code         pic x(6)        value spaces.
     03  lc-b            pic x(8)        value spaces.
     03  lc-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  lc-c            pic x(9).
     03  lc-VAT          pic z.
*>
 01  Line-d.
     03  filler          pic x(45)       value spaces.
     03  ld-a            pic x(12).
     03  ld-code         pic x(6)        value spaces.
     03  ld-b            pic x(8)        value spaces.
     03  ld-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  ld-c            pic x(9).
     03  ld-VAT          pic z.
*>
 01  Line-e.
     03  filler          pic x(45)       value spaces.
     03  le-a            pic x(12).
     03  le-code         pic x(6)        value spaces.
     03  le-b            pic x(8)        value spaces.
     03  le-amount       pic z(6)9.99cr   blank when zero.
     03  filler          pic x(2)        value spaces.
     03  le-c            pic x(9).
     03  le-VAT          pic z.
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
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 init01 section.
     move     Print-Spool-Name to PSN.
     perform  4 times
              add  1 to a
              initialize Total-Group (a)
     end-perform
*>
     move     prog-Name to l1-version.
     perform  zz070-Convert-Date.
     move     WS-date to l1-date.
     move     1  to File-Key-No.
*>
 Menu-Return.
     display  Prog-Name        at 0101 with foreground-color 2 erase eos.
     display  "Autogen Report" at 0136 with foreground-color 2.
     display  WS-date          at 0171 with foreground-color 2.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-4
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    display SL120   at 0501 with foreground-color 4
                    if     WS-Caller not = "xl150"    *> Might be called by XL150 EOC (End of Cycle)
                           accept WS-reply at 0563 with foreground-color 6
                    end-if
                    goback.                         *> As no transactions.
*>
     perform  Sales-Open-Input.
     if       FS-Reply not = zero
                    display SL121   at 0501 with foreground-color 4
                    if     WS-Caller not = "xl150"    *> Might be called by XL150 EOC
                           accept WS-reply at 0563 with foreground-color 6
                    end-if
                    goback.                         *> As no transactions.
*>
     open     output print-file.
*>
     move     zero  to  j.
     perform  headings-1.
     perform  SLautogen-Open-Input.
*>
 Get-Invoice-Record.
     perform  SLautogen-Read-Next.
     if       fs-reply = 10
              go to  Main-End.
*>
     move     zero to l.
     move     ih-customer to WS-Sales-Key  l5-cust.
     move     space to WS-reply.

     perform  Sales-Read-Indexed.
     if       fs-reply  = 21
              move "X" to WS-reply.
*>
     if       WS-reply = "X"
              move "!! Customer Unknown" to l5-Name
              move 1 to WS-error
     else
              move Sales-Name  to  l5-Name.
*>
     move     ih-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     WS-date  to  l5-date.
*>
     move     ih-Deduct-Amt to WS-Deduct-Amt.
     move     ih-Deduct-VAT to WS-Deduct-VAT.
*>
     if       WS-Deduct-Amt = zero
              move  spaces  to  lb-a  lb-code
              move  zero    to  lb-amount
     else
              move  "Late Charge "  to  lb-a
              move  spaces          to  lb-code
              move  WS-Deduct-Amt   to  lb-amount.
*>
     if       ih-discount = zero
              move  spaces  to  lc-a  lc-code  lc-c
              move  zero    to  lc-amount  lc-VAT
     else
              move  "Discount    "  to lc-a
              move  spaces          to lc-code  lc-c
              move  ih-discount     to lc-amount
              move  zero            to lc-VAT.
*>
     if       ih-carriage = zero
              move  spaces  to  ld-a  ld-code  ld-c
              move  zero    to  ld-amount  ld-VAT
     else
              move  "Carriage    "  to  ld-a
              move  spaces          to  ld-code  ld-c
              move  ih-carriage     to  ld-amount
              if    ih-c-VAT = zero
                    move  zero  to  ld-VAT
              else
                    move  1  to  ld-VAT.
*>
     if       ih-extra = zero
              move  spaces  to  le-a  le-code  le-c
              move  zero    to  le-amount  le-VAT
     else
              move  extra-desc to  le-a
              move  spaces     to  le-code
              move  ih-extra  to  le-amount
              if    ih-e-VAT = zero
                    move  zero to  le-VAT
              else
                    move  1  to  le-VAT.
*>
     if       Ih-Type > 0 and < 5
              move     ih-Type to a
              move     WS-lit (a) to L5-Type.
*>
     add      ih-c-VAT ih-e-VAT to Total-cvat (a, 1).
*>
     move     ih-net  to  l5-goods.
     add      ih-VAT  ih-c-VAT  ih-e-VAT  WS-Deduct-VAT giving  l5-VAT.
     add      ih-net  ih-extra  ih-carriage  ih-discount WS-Deduct-Amt giving  l5-net.
     add      ih-VAT  ih-c-VAT  ih-e-VAT  WS-Deduct-VAT
              ih-net  ih-extra  ih-carriage  ih-discount WS-Deduct-Amt giving  l5-gross.
*>
     add      ih-net  to  Total-gds (a).
     add      ih-discount  ih-extra  to  Total-dis (a).
     add      WS-Deduct-Amt to Total-ded (a).
     add      ih-carriage  to  Total-car (a).
     add      ih-VAT  ih-c-VAT  ih-e-VAT  WS-Deduct-VAT to  Total-VAT (a).
     add      ih-net  ih-extra  ih-carriage  ih-discount WS-Deduct-Amt to  Total-net (a).
     add      ih-VAT  ih-c-VAT  ih-e-VAT  WS-Deduct-VAT
              ih-net  ih-extra  ih-carriage  ih-discount
              WS-Deduct-Amt to  Total-grs (a).
*>
     if       Line-cnt > Page-Lines - 2
              perform headings-1.
*>
     write    print-record from Line-5 after 2.
     add      2 to Line-cnt.
*>
     move     zero to fs-Reply.
     move     ih-Lines to WS-Lines.
     perform  Analysis-Print  WS-Lines times.
     perform  Extra-Analysis.
     go       to Get-Invoice-Record.
*>
 Main-End.
     perform  Sales-Close.
     perform  SLautogen-Close.
*>
     if       Line-cnt < Page-Lines - 16
              move spaces to print-record
              write print-record after 3
     else
              perform  main12
     end-if
     write    print-record from Line-7 after 2.
     move     spaces to print-record.
     write    print-record after 1.
     move     zero to a.
     perform  4 times
              add   1 to a
              move  Total-gds (a) to  l6-goods
              move  Total-dis (a) to  l6-disc
              move  Total-car (a) to  l6-carr
              move  Total-net (a) to  l6-net
              move  Total-VAT (a) to  l6-VAT
              move  Total-grs (a) to  l6-gross
              move  Total-ded (a) to  l6-ded
              move  WS-lit (a)    to  l6-lit
              write print-record from Line-6 after 1
     end-perform
*>
     if       Sales-missing                    *> Should never happen but ...
              move "Warning Record/s Missing In Sales File" to print-record
              write print-record after 2
              write print-record after 2.    *> yes twice
*>
     write    print-record from Line-9 after 2.
     move     spaces to print-record.
     write    print-record after 1.
     move     zero to i.		*> moved from within the perform above
     perform  3 times   *> the three vat rates
              add   1 to i
              move  i to l8-VAT-code
              move  vat-rate (i) to l8-VAT-rate
              move  Total-cvat (1, i) to l8-amount1
              move  Total-cvat (2, i) to l8-amount2
              move  Total-cvat (3, i) to l8-amount3
              move  Total-cvat (4, i) to l8-amount4
              write print-record from Line-8 after 1
     end-perform
     if       Vat-Rate (4) not = zero    *> test if local tax in use & print if so
         or   Vat-Rate (5) not = zero    *>  Both - Not used in the UK (so far)
              perform  2 times
                       add   1 to i
                       move  i to l8-VAT-code
                       move  vat-rate (i) to l8-VAT-rate
                       move  Total-cvat (1, i) to l8-amount1
                       move  Total-cvat (2, i) to l8-amount2
                       move  Total-cvat (3, i) to l8-amount3
                       move  Total-cvat (4, i) to l8-amount4
                       write print-record from Line-8 after 1
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
              write print-record from Line-1 after page
     else
              write print-record from Line-1 after 1.
     write    print-record from Line-2 after 1.
*>
 Cont-HDs.
     write    print-record from Line-4 after 2.
     write    print-record from Line-4B after 1.
     move     spaces  to  print-record.
     move     5 to Line-cnt.
*>
 Analysis-Print          section.
*>==============================
*>
     if       fs-reply = 99			*> Just in case
              go to Main-Exit.
     perform  SLautogen-Read-Next.
     if       fs-reply = 10
              move 99 to fs-Reply		*> Just in case
              go to Main-Exit.
*>
     move     il-product   to  test-product.
     if       il-comment
              go to  main-exit.
*>
*> Process line items
*>
     if       Line-cnt > Page-Lines - 2
              perform headings-1.
     if       ih-test not = zeros           *> JIC but SHOULD be line items
              move     spaces to Line-5B
              move     il-description to L5B-Item-Desc
              move     il-VAT-Code    to L5B-VAT-Code
              move     il-pa          to L5B-pa
              move     il-net         to l5B-goods
              move     il-Net         to L5B-Net
              move     il-VAT         to L5B-VAT
              add      il-Net il-VAT giving L5B-Gross
              write    print-record from Line-5B after 1
              add      1 to Line-cnt.
*>
     move     il-pa       to la-code.
     move     il-net      to la-amount.
     move     il-VAT-code to la-VAT k.
     if       k > zero
              add il-VAT  to Total-cvat (a, k).
*>
     move  spaces     to la-a  la-b  la-c.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Extra-Analysis          section.
*>==============================
*>
     if       Line-cnt > Page-Lines - 4
              perform headings-1.
*>
     if       lb-a  not equal  spaces
              write  print-record  from  Line-b after 1
              add 1 to Line-cnt
              move  spaces  to  lb-a.
*>
     if       lc-a  not equal  spaces
              write  print-record  from  Line-c after 1
              add 1 to Line-cnt
              move  spaces  to  lc-a.
*>
     if       ld-a  not equal  spaces
              write  print-record  from  Line-d after 1
              add 1 to Line-cnt
              move  spaces  to  ld-a.
*>
     if       le-a  not equal  spaces
              write  print-record  from  Line-e after 1
              add 1 to Line-cnt
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
*> output:  WS-date as uk/US/Inlt date format
*>          u-date & WS-Date = spaces if invalid date
*>
     perform  maps04.
     if       u-date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     u-date to WS-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-date.  *> swap Intl to UK form
     move     u-date (7:4) to WS-Intl-Year.
     move     u-date (4:2) to WS-Intl-Month.
     move     u-date (1:2) to WS-Intl-Days.
*>
 zz060-Exit.  exit section.
*>
 zz070-Convert-Date        section.
*>********************************
*>
*>  Converts date in to-day to UK/USA/Intl date format
*>****************************************************
*> Input:   to-day
*> output:  WS-date as uk/US/Inlt date format
*>
     move     to-day to WS-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-date.  *> swap Intl to UK form
     move     to-day (7:4) to WS-Intl-Year.
     move     to-day (4:2) to WS-Intl-Month.
     move     to-day (1:2) to WS-Intl-Days.
*>
 zz070-Exit.  exit section.
*>
 Maps04       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit. exit section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
