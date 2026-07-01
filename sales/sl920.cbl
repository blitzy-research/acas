       >>source free
  *>
  *>  TEST the audit updating after an amendment to:
  *>   Invoices
  *>   Credit Notes.
  *>  While testing the rest of the program AND sl910.
  *>  Program updates stock records if any changes to quantity.
  *>
  *>==================================================
  *>
  *> PROGRAM IS NOT UPDATING STOCK MONTH YEARLY TOTALS ANYWHERE!!!!!
  *> but  IS NOW, as of .16) - 20/03/18
*>********************************************************
*>                                                       *
*>              Invoice  Maintenance (Amend)             *
*>                                                       *
*>    This program only works in invoice Batch mode.     *
*>                                                       *
*>********************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl920.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen, FBCS, FIDM, FIDPM 17/12/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Maintenance.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas010  ->
*>                         auditMT
*>                        acas011  ->
*>                         stockMT.
*>                        acas012  ->       (Sales)
*>                         salesMT.
*>                        acas014  ->       (Delivery)
*>                         deliveryMT.
*>                        acas015  ->       (Analysis)
*>                         analMT.
*>                        acas016  ->
*>                         invoiceMT.
*>                        acas019  ->
*>                         otm3MT.
*>
*>                        SL070. Analysis codes set up - Defaults only.
*>**
*>    Error messages used.
*>     System Wide:
*>                        SL003
*>                        SL006
*>     Module specific:
*>                        SL180
*>                        SL181
*>                        SL182
*>                        SL183
*>                        SL184
*>                        SL185
*>                        SL186
*>                        SL190
*>                        SL191
*>                        SL192
*>                        SL193
*>                        SL194
*>                        SL195
*>                        SL196
*>                        SL198
*>                        SL199
*>****
*>  Changes.
*> 04/03/83 Vbc - Changes To Fdinv.Cob And Cr-Notes.
*> 22/03/83 Vbc - Cr-Notes.
*> 30/03/83 Vbc - When Creating Invoices Check For Sl-Charges &
*>                Sales-Late (Late-Charges).
*> 30/04/83 Sjw - Accept Late Charges Only If Invoice WS-Named On
*>                Cr. Notes.
*> 02/05/83 Vbc - #.
*> 17/12/83 Vbc - Cis Cobol Conversion.
*> 18/01/84 Vbc - Fix Bugs In Delete Line & Record Routines.
*> 01/03/84 Vbc - Support Sales-Unapplied In Invoice-Details.
*> 10/03/84 Vbc - Scrap  Accept Of sih-Deduct-Vat(=0).
*> 16/11/84 Vbc - Fix Abort Graphic Screen In Invoice-Details.
*> 07/01/85 Vbc - Fix Bug Clear Screen In Cr-Notes.
*> 03/03/09 vbc - .02 Migration to Open Cobol v3.00.00.
*> 18/03/09 vbc - ,03 Bug/Feature 30.1 & 3 Escape out at any level.
*> 19/03/09 vbc - .04 Feature 30.5 Allow receipts to be amended if not posted.
*> 26/11/11 vbc - .05 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .06 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn, added support for IS delivery file
*> 11/12/11 vbc - .07 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 24/05/13 vbc - .08 Add in support for direct link to Stock Control with Stock and Audit files
*>                    in inv-level-2. Changed stk code 12>13, desc 24>32 removing pa code
*>                    & consider add new display field OS for Out of Stock but on order
*>                    with delivery expected in 7 days or less.
*> 24/10/16 vbc - .09 ALL programs now using wsnames.cob in copybooks
*> 30/10/16 vbc - .10 Support for RDB on  Analysis, Stock & Stock Audit tables
*>                    instead of cobol files
*>                    using acas010, acas011 & acas015. Update version to v3.02
*>                      more to do, have renamed the calls for acas010,11 & 15
*>                      Stock-Audit, Stock & Analysis to reduce any coding errors
*>                      as there will be a lot of them in this module.
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 18/01/17 vbc - .11 Added remaining FH processing but excluding invoice.
*> 19/01/17 vbc - .12 Added OTM3 file for use when amending Credit Notes.
*>                    Removed the Letter postfix after invoice nos when using
*>                    own invoice nos, as created for one customer many years
*>                    ago, which could cause issues when posting to ITM3.
*>                    2 B removed from the invoice file layout. <<<<<<
*>                    Added missing CR checks for amount O/S (in sl910).
*>                    Clears sih-Status-L (& P) for reprinting.
*> 25/01/17 vbc       Dry testing completed.
*> 10/02/17 vbc - .13 Updated FD/WS for 016,019 and replaced cobol verbs
*>                    for access to FH/DALs.
*> 17/04/17 vbc -     Dry check for slinvoiceMT.
*> 27/08/17 vbc - .14 Added SL198 & 199 to replace embedded msgs as per sl910
*>                    likewise SL196 in place of "Not Found" & "Not on file"
*> 17/03/18 vbc - .15 Added test for type = 4 (proformas) in Update-Stock-and
*>                   -Audit as we do not want to updates stock-held or do audit
*>                    until it is amended to a receipt or a invoice. Matches
*>                    sl910
*> 19/03/18 vbc - .16 Updated to use CIT-A and CIT-D to update the stock record
*>                    fields period and month within year totals.
*>
*>                    Just above Process-Stock-Record the multi copy of code
*>                    is abbreviated as indexed reads etc for stock or abbrev
*>                    key can be in a simpler code block now with orig rem.d out
*>                    ALSO there might be an issue at Get-Prod-Test if screen
*>                     is longer than 24 - TEST THIS warning in sl910.
*>
*>                    At the bottom of type-Input in invoice-details section
*>                    there is a disp and accept but not test for 0 or non zero
*>                    WHY NOT - TEST THIS and fix if needed. also sl910
*>
*> 10/12/22 vbc   .17 Added para after some sections 4 GC 3.2 warning msgs.
*> 09/05/23 vbc - .18 Near end of type-Input changed 2 None Zero or ESC To Abort
*>                    and next line to start at 40 instead of 60. ditto sl910,
*> 20/05/23 vbc -     sl810 WS-Show-Delivery changed from pic 9 to x (sane as
*>                    sl910).
*> 06/08/23 vbc   .19 Better support for service items set default qty = 1.
*>                    no further checking but check for audit as well
*>                    matches work for sl910.
*>                    Test for invoice type < 1 on invoice input.
*> 07/08/23 vbc - .20 Added mv 1 to File-Key-No before obtaining invoice #.
*>                 21 temp testing display for read indexed invoice #
*> 12/08/23 vbc   .22 Force VAT rate to S = Standard as default - user can chng.
*>                    In get-Vat support for accepting  S, R and Z and will
*>                    convert. same as in sl910 - forgot to put it in.
*> 17/03/24 vbc - .23 SL197 should be using SL186 - changed and 196 removed.
*> 12/04/24 vbc - .24 Removed any and all BO processing as pointless as any
*>                    such amendments can be done in sl970 via sales menu
*>                    T.A.4 and is too late for amend mode as BO recs updated.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 21/08/25 vbc - .25 On Get-Vat-Code (level-2) force upper csae on accept
*>                    Level 2 only.
*> 25/08/25 vbc   .26 On line totals line # missing.
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
*>
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL920 (3.3.00)".
 77  Exception-Msg       pic x(25) value spaces.
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 01  WS-amount-screen-display6.
     03  WS-poundsd6     pic 9(6).
     03  WS-period6      pic x     value ".".
     03  WS-penced6      pic v99.
 01  WS-amount-screen-accept6 redefines WS-amount-screen-display6.
     03  WS-pound6       pic 9(6).
     03  filler          pic x.
     03  WS-pence6       pic v99.
*>
 01  WS-amount-work6.
     03  amt-wk-pds6     pic 9(6).
     03  amt-wk-pence6   pic v99.
 01  WS-amount-ok6 redefines WS-amount-work6.
     03  amt-ok6         pic 9(6)v99.
*>
 01  WS-amount-screen-display7.
     03  WS-poundsd7     pic 9(7).
     03  WS-period7      pic x     value ".".
     03  WS-penced7      pic v99.
 01  WS-amount-screen-accept7 redefines WS-amount-screen-display7.
     03  WS-pound7       pic 9(7).
     03  filler          pic x.
     03  WS-pence7       pic v99.
*>
 01  WS-amount-work7.
     03  amt-wk-pds7     pic 9(7).
     03  amt-wk-pence7   pic v99.
 01  WS-amount-ok7 redefines WS-amount-work7.
     03  amt-ok7         pic 9(7)v99.
*>
 01  WS-discount-display.
     03  WS-disca1       pic 99.
     03  WS-disca2       pic x        value ".".
     03  WS-disca3       pic v99.
 01  WS-discount-accept redefines WS-discount-display.
     03  WS-discb1       pic 99.
     03  filler          pic x.
     03  WS-discb3       pic v99.
 01  WS-discount-work.
     03  WS-disc-wka     pic 99.
     03  WS-disc-wkb     pic v99.
 01  WS-discount redefines WS-discount-work  pic 99v99.
*>
 copy "slwsinv.cob"  replacing Invoice-Line by Invoice-Lines. *> Dup name, was wsinv.cob in sales
 copy "slwsinv2.cob" replacing Invoice-Record by WS-Invoice-Record.
 copy "slwsoi3.cob".
*>
 copy "wsanal.cob".
 copy "wsaudit.cob".
 copy "wsdel.cob".
 copy "wssl.cob".
 copy "wsstock.cob".     *> 3.02
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
*>     03  WS-Stock-Audit-Record  pic x.
*>     03  WS-Stock-Record        pic x.
*>     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
*>     03  WS-Delivery-Record     pic x.
*>     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
*>     03  WS-Invoice-Record      pic x.
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
 01  WS-data.
     03  test-product.
         05  filler      pic x.
             88  sil-comment           value "/".
         05  filler      pic x(12).
     03  menu-reply      pic 9.
     03  WS-reply        pic x.
     03  z               pic 99.
     03  c-check         pic 9.
         88  c-exists                value  1.
     03  WS-delinv       pic 9       value zero.
         88  del-exists              value 1.
     03  address-A       pic x(96).
     03  address-line.
         05 add-line1    pic x(15).
         05 add-line2    pic x(21).
     03  WS-named        pic x           value " ".
     03  WS-dash         pic x(80)       value all "-".
     03  work-1          pic 9(7)v99.
     03  work-n          pic 9(7)v99.
     03  work-d          pic 9(7)v99.
     03  display-8       pic z(5)9.99.
     03  display-9       pic z(6)9.99.
     03  Vat-Code-X.                           *> this for S, R, Z = Std,Reduced,Zero
         05  Vat-Code    pic 9.                *> 18/01/17
     03  I               pic 99.
     03  J               pic 99.
     03  k               pic 99.
     03  m               pic 99.
     03  escape-code     pic x.
     03  new-screen      pic 9(8).
     03  altypes         pic x(60) value "Receipt <<<    Account <<<    Credit Note <<<Pro-Forma <<<".
     03  filler redefines altypes.
         05 d-types      pic x(15) occurs 4.
     03  WS-vat-rate     pic 99v99.
     03  WS-pa           pic xx.
     03  WS-product      pic x(13).
     03  WS-Temp-Stock-Key             value spaces.
         05  WS-Abrev-Stock   pic x(7).
         05  WS-Stock-No-Long pic x(6).
     03  WS-Temp-Invoice pic 9(8).
     03  WS-description  pic x(32).
     03  WS-qty          pic 9(5).
     03  WS-net          pic 9(7)v99.
     03  WS-vat          pic 9(7)v99.
     03  WS-unit         pic 9(6)v99.
     03  WS-cr           pic 9(8).
     03  WS-dayes        pic 99.
     03  WS-Inv-Month.
         05  WS-Inv-Mth  pic 99.
     03  WS-Show-Delivery pic x.
*>
     03  WS-Old-Product  pic x(13).     *> These hold line items prior to changes
     03  WS-Old-Qty      pic 9(5).	*> and new are tested against them for any changes & if needed
*>                                         the CIT tables are updated.
     03  WS-Old-Desc     pic x(32).	*> NOT USED
*>
     03  WS-env-lines    pic 999       value zero.
     03  WS-lines        binary-char unsigned value zero.
     03  WS-accept-body  binary-char unsigned value 8.         *> set for 24 line screen (-1)
     03  WS-23-lines     binary-char unsigned value zero.
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
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
 copy "Test-Data-Flags.cob".    *> set sw-testing to zero to stop logging.
*>
 01  Change-Item-Tables.        *> Initialised on 1st getting a invoice/receipt/Cr.note.
     03  CIT-New-Product     pic 9.       *> 0 = no & 1 yes
     03  Tab-A               pic 99.
     03  Tab-D               pic 99.
     03  CIT-Additions       occurs 40.	  *> items deleted from invoice (or quantity changed ??)
         05  CIT-A-Stock-Key pic x(13).
         05  CIT-A-Desc      pic x(32).
         05  CIT-A-Trans-Qty pic s9(6).	  *> if negative then qty was increased
     03  CIT-A               pic 99.      *> index for above table
*>
     03  CIT-Deletions       occurs 40.	  *> items added to invoice
         05  CIT-D-Stock-Key pic x(13).
         05  CIT-D-Desc      pic x(32).
         05  CIT-D-Trans-Qty pic s9(6).
     03  CIT-D               pic 99.      *> index for above table
*>
 01  Error-Messages.
*> System Wide
     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
     03  SL006          pic x(43) value "SL006 Note Details & Hit Return to continue".
*>
*> Module specific
     03  SL180          pic x(34) value "SL180 Err on Invoice Rec. Write : ".
     03  SL181          pic x(46) value "SL181 Invoice To Credit Does Not Exist On OTM5".
     03  SL182          pic x(31) value "SL182 Invoice To Credit Is Paid".
     03  SL183          pic x(42) value "SL183 Invoice To Credit Has Query Flag Set".
     03  SL184          pic x(75) value "SL184 You Can Only Credit Invoices. Not Receipts, Credit Notes Or Proformas".
     03  SL185          pic x(56) value "SL185 Credit of Prompt Pay/Late Charge will be Automatic".
     03  SL186          pic x(30) value "SL186 P.A. Code Does Not Exist".
     03  SL190          pic x(35) value "SL190 Error on Writing Audit record".
     03  SL191          pic x(33) value "SL191 Error on Stock rec. Rewrite".
     03  SL192          pic x(36) value "SL192 Err on Invoice rec. Rewrite : ".
     03  SL193          pic x(65) value "SL193 You Can Only Credit An Invoice With The Same Account Number".
     03  SL194          pic x(23) value "SL194 Invoice Not Found".
     03  SL195          pic x(52) value "SL195 Invoice Details Already Passed To Sales Ledger".
     03  SL196          pic x(17) value "SL196 Not on File".
*>     03  SL197          pic x(06) value "SL197".
     03  SL198          pic x(19) value "SL198 Stock Read : ".
     03  SL199          pic x(22) value "SL199 Stock Rewrite : ".
*>
 01  delete-test.
     03  delete-field    pic xx.
     03  filler          pic x(11).
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
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 init01 section.
*>*************
*>
     accept   WS-env-lines   from lines.
     if       WS-env-lines < 24
              move  24 to WS-env-lines WS-lines
     else
              move  WS-env-lines   to WS-lines
     end-if
     subtract 1 from WS-lines giving WS-23-lines.
     subtract 15 from WS-23-Lines giving WS-Accept-Body.	*> gives no. of invoice item lines
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     perform  zz070-Convert-Date.   *> WS-date now local disp date
     move     1 to File-Key-No.
*>
*>  Open files and check & setup if we have any deleted invoices
*>
     perform  Program-Start.
*>
 main.
*>***
*>
     initialize sInvoice-Bodies
                Change-Item-Tables.
     perform  invoice-details.
*>
     if       cob-crt-status = cob-scr-esc
       or     z not = zero
       or     escape-code = "Q"
              go to  menu-exit.
*>
     move     16  to  lin.
     perform  erase-screen.
*>
 data-Input.
*>*********
*>
     move     zero to   sih-p-c sih-net sih-vat.
*>
     move     zero to  i.
*>
     if       i-level-1
              perform  inv-level-1
     else
              perform  inv-level-2.
     if       cob-crt-status = cob-scr-esc
              go to main.
*>
     if       I not = 1
              perform End-Totals.
*>
 more-data.
*>
     display "Amend Further Invoices? (Y/N)  [Y]" at 1629 with foreground-color 2.
*>
     move     "Y"  to   WS-reply.
     accept   WS-reply at 1661 with foreground-color 6 update.
     move     function upper-case (WS-reply) to WS-reply.
*>
     display  " " at 1601 with erase eol.
*>
     if       WS-reply = "Y"
              go to main.
     if       WS-reply not = "N"
              go to more-data.
*>
 menu-exit.
*>********
*>
     move     zero to  pass-value.
     perform  Sales-Close.
     perform  Delivery-Close.       *> close sales-file delivery-file analysis-file
     perform  Analysis-Close.
     perform  Invoice-Close.     *> close    invoice-file.
     perform  OTM3-Close.         *>  close    Open-Item-File-3.
     if       SL-Stock-Link = "Y"
              perform Stock-Close          *> close Stock-File  Stock-Audit
              perform Stock-Audit-Close.
*>
     exit     program.
*>
*>****************************************************************
*>                  P R O C E D U R E S                          *
*>****************************************************************
*>
 Running-Totals          section.
*>==============================
*>
     display  I at 1223 with foreground-color 3.
     move     zero  to  sih-net
                        sih-vat.
*>
     perform  varying k from 1 by 1 until k > i
              if  sil-type (k) not = "D"
                  add sil-net (k)  to  sih-net
                  add sil-vat (k) to  sih-vat
     end-perform
*>
     move     sih-net  to  display-9.
     if       i-level-1
              display display-9 at 1237 with foreground-color 3.
*>
     move     sih-vat  to  display-9.
     if       i-level-1
              display display-9 at 1255 with foreground-color 3.
*>
     add      sih-net  sih-vat  giving  display-9.
*>
     if       i-level-1
              display display-9 at 1268 with foreground-color 3
     else
              display display-9 at 1270 with foreground-color 3.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 write-details           section.
*>==============================
*>
     add      1  to  j.
     move     sih-invoice       to sil-invoice (j).
     move     J                 to sil-line (j).
     move     sih-type          to sil-type (j).
     move     Invoice-Lines (j)  to WS-Invoice-Record.
*>
     perform  Invoice-Rewrite.        *> rewrite  invoice-record invalid key		*> could be extra item
     if       fs-reply not = zero
              perform Invoice-Write.  *>   write invoice-record. SHOULD NEVER HAPPEN unless extra item
*>
     if       fs-reply not = zero
              perform Eval-Status
              display sl180         at line WS-23-lines col 1 with erase eol foreground-color 4
              display fs-reply      at line WS-23-lines col 36 with foreground-color 3
              display exception-msg at line WS-23-lines col 39 with foreground-color 3
              display invoice-key   at line WS-23-lines col 64 with foreground-color 3
              display sl006         at line WS-lines col 01 with foreground-color 3
              accept  WS-reply      at line WS-lines col 30
              display " "           at line WS-23-lines col 1 with erase eos
     end-if.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Update-Stock-and-Audit section.        *> This is NOT the same as in SL910 as
*>=============================            it uses the CIT-A/D (Change-Item-Tables) tables
*>                                         after writing out the updated invoice
*>
*> Normal for Receipts(1) and Invoices (2) but reverse process for Credit Notes (3)
*>     ignoring proformas
*>
*> CIT-A processing is to :
*>   Hold values of existing Inv. or Credit note line items
*>  and at the end of amend process that has updated the CIT-A fields
*>  o/p new audit record/s as needed which will show the differences per
*>   line item. This way Auditing will always be correct after any amendments.
*>
*>  THIS IS TO BE TESTED as it is NEW CODE when linked Stock Control.
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
     if       SL-Stock-Link not = "Y"           *> Only process if linked to Stock Control
              go to Update-Stock-Exit.
     if       Sil-Type (j) = 4                  *> Ignore a proforma
              go to Update-Stock-Exit.
     if       CIT-A = zero                      *> If both tables are empty, then exit
       and    CIT-D = zero
              go to Update-Stock-Exit.
*>
     initialize WS-Stock-Audit-Record.
     perform  varying Tab-A from 1 by 1 until Tab-A > CIT-A
              move 3                       to Audit-Type
              move Sih-Invoice             to Audit-Invoice-PO
              move WS-Date                 to Audit-Process-Date
              move CIT-A-Stock-Key (Tab-A) to Audit-Stock-Key
                                              WS-Temp-Stock-Key
              move CIT-A-Desc (Tab-A)      to Audit-Desc
              if   CIT-A-Trans-Qty (Tab-A) > zero	*> Sale has decreased
                   move CIT-A-Trans-Qty (Tab-A) to Audit-Transaction-Qty
                   move 1                  to Audit-Reverse-Transaction
              else
               if  CIT-A-Trans-Qty (Tab-A) < zero	*> sale has increased
                   multiply CIT-A-Trans-Qty (Tab-A) by -1 giving
                                             Audit-Transaction-Qty
               end-if
              end-if
*>
              if   Sil-Type (j) = 3	*> for Crs, switch the reverse flag
                if Audit-Reverse-Transaction = zero
                   move 1      to Audit-Reverse-Transaction
                   move 5      to Audit-Type
                   move Sih-cr to Audit-Cr-for-Invoice
                else
                   move zero to Audit-Reverse-Transaction
                end-if
              end-if
              move Stk-Audit-No           to Audit-No
*>
*> Now get the stock record
*>
              if   WS-Stock-No-Long = spaces
                   move WS-Abrev-Stock to WS-Stock-Abrev-Key
                   move  2 to File-Key-No
                   perform Stock-Read-Indexed  *> read Stock-File record key WS-Stock-Abrev-Key invalid key
                   if   FS-Reply = 21
                        move zero to Stock-Cost
                        move spaces to WS-Stock-Key
                   end-if                      *> end-read
              else
                   move WS-Temp-Stock-Key to WS-Stock-Key
                   move  1 to File-Key-No
                   perform Stock-Read-Indexed  *> read Stock-File key WS-Stock-Key invalid key
                   if   FS-Reply = 21
                        move zero to Stock-Cost
                        move spaces to WS-Stock-Key
                   end-if                      *> end-read
              end-if
              if   fs-reply not = zero
                   perform Eval-Status
                   display SL198         at line WS-23-lines col 1 with erase eol foreground-color 4
                   display fs-reply      at line WS-23-lines col 16 with foreground-color 3
                   display exception-msg at line WS-23-lines col 19 with foreground-color 3
                   display WS-Stock-Key  at 2064 with foreground-color 3
                   display sl006         at line WS-lines col 01 with foreground-color 3
                   accept  WS-reply      at line WS-lines col 30
                   display " "           at line WS-23-lines col 1 with erase eos
              end-if
*>
*> If we have great, but if not Stock-Cost is zero which helps it show up
*>    in proof reports
*>
              if   WS-Stock-Key not = spaces		*> we have a stock rec.
                   if       Sil-Type (j) not = 3	*> Its not a Credit note
                      and   Stock-Services-Flag not = "Y"
                    if      CIT-A-Trans-Qty (Tab-A) > zero	*> Sale has decreased
                            add CIT-A-Trans-Qty (Tab-A) to Stock-Held
                            compute  Audit-Stock-Value-Change =
                                     Audit-Transaction-Qty * Stock-Cost
                    else
                        if  CIT-A-Trans-Qty (Tab-A) < zero	*> sale has increased
                            subtract CIT-A-Trans-Qty (Tab-A) from Stock-Held
                            compute  Audit-Stock-Value-Change =
                                    Audit-Transaction-Qty * Stock-Cost * -1
                        end-if
                    end-if
                   end-if
                   if       Sil-Type (j) = 3		*> It is a Credit note
                      and   Stock-Services-Flag not = "Y"
                    if      CIT-A-Trans-Qty (Tab-A) < zero	*> Sale has Increased
                            add CIT-A-Trans-Qty (Tab-A) to Stock-Held
                            compute  Audit-Stock-Value-Change =
                                     Audit-Transaction-Qty * Stock-Cost
                    else
                     if     CIT-A-Trans-Qty (Tab-A) > zero	*> sale has Decreased
                            subtract CIT-A-Trans-Qty (Tab-A) from Stock-Held
                            compute  Audit-Stock-Value-Change =
                                     Audit-Transaction-Qty * Stock-Cost * -1
                     end-if
                    end-if
                   end-if
*>
*> This from sl910 but adds reversed for CR and receipts/invs as back in stock
*>
                   if       WS-Inv-Mth not < 1 or > 12
                     if      Sil-Type (j)  = 1 or 2                    *> Invoice and Recepts
                      if      CIT-A-Trans-Qty (Tab-A) > zero      *> Sale has decreased
                              add Audit-Transaction-Qty to Stock-Adds
                              add Audit-Transaction-Qty to Stock-TD-Adds (WS-Inv-Mth)
                      else
                          if  CIT-A-Trans-Qty (Tab-A) < zero      *> sale has increased
                              add Audit-Transaction-Qty to Stock-Deducts
                              add Audit-Transaction-Qty to Stock-TD-Deds (WS-Inv-Mth)
                          end-if
                      end-if
                     else
                     if      Sil-Type (j) = 3                         *> Credit Notes
                      if      CIT-A-Trans-Qty (Tab-A) < zero      *> Sale has Increased
                              add Audit-Transaction-Qty to Stock-Adds
                              add Audit-Transaction-Qty to Stock-TD-Adds (WS-Inv-Mth)
                      else
                        if    CIT-A-Trans-Qty (Tab-A) > zero      *> sale has Decreased
                              add Audit-Transaction-Qty to Stock-Deducts
                              add Audit-Transaction-Qty to Stock-TD-Deds (WS-Inv-Mth)
                        end-if
                      end-if
                     end-if    *> type = 3
                   end-if      *> inv-mth good
*>
                   if       Stock-Held < zero		*> Should NOT happen as testing in data entry but if a Cr?
                      and   Stock-Services-Flag not = "Y"
                            multiply -1 by Stock-Held
                            add Stock-Held to Stock-Pre-Sales
                            move zero to Stock-Held
                   end-if
                   if       Stock-Held > zero
                      and   Stock-Services-Flag not = "Y"
                            multiply Stock-Held by Stock-Cost giving Stock-Value
                   else
                            move zero to Stock-Value
                   end-if
                   move 1 to File-Key-No
                   perform  Stock-Rewrite          *> rewrite Stock-Record invalid key
                   if       FS-Reply = 21
                            display SL191    at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
                            display fs-reply at line WS-23-lines col 38 with foreground-color 2 highlight
                            display SL006    at line WS-lines col 1
                            accept WS-reply  at line WS-lines col 45
                   end-if                     *> end-rewrite
                   if       fs-reply not = zero
                            perform Eval-Status
                            display SL199         at line WS-23-lines col 1 with erase eol foreground-color 4
                            display fs-reply      at line WS-23-lines col 16 with foreground-color 3
                            display exception-msg at line WS-23-lines col 19 with foreground-color 3
                            display WS-Stock-Key  at 2064 with foreground-color 3
                            display sl006         at line WS-lines col 01 with foreground-color 3
                            accept  WS-reply      at line WS-lines col 30
                            display " "           at line WS-23-lines col 1 with erase eos
                   end-if
              end-if
*>
              if   Stk-Audit-Used = 1
                   move zero to Stk-Activity-Rep-Run		*> Need to run audit report
                   perform  Stock-Audit-Write    *> write WS-Stock-Audit-Record
                   if      fs-reply not = zero
                           perform Eval-Status
                           display SL190         at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
                           display fs-reply      at line WS-23-lines col 38 with foreground-color 2 highlight
                           display exception-msg at line WS-23-lines col 41 with foreground-color 3
                           display SL006         at line WS-lines col 1
                           accept WS-reply       at line WS-lines col 45
                   end-if
              end-if
     end-perform.
*>
*> Now we have processed Table CIT-A we have to do it all again for CIT-D
*>  and No, it is too complex to try and do it all in one (higher risk of bugs)
*>
     perform  varying Tab-D from 1 by 1 until Tab-D > CIT-D
              move 3                       to Audit-Type
              move Sih-Invoice             to Audit-Invoice-PO
              move WS-Date                 to Audit-Process-Date
              move CIT-D-Stock-Key (Tab-D) to Audit-Stock-Key
                                              WS-Temp-Stock-Key
              move CIT-D-Desc (Tab-D)      to Audit-Desc
              if   CIT-D-Trans-Qty (Tab-D) > zero		*> Sale has increased
                   move CIT-D-Trans-Qty (Tab-D) to Audit-Transaction-Qty
              end-if
*>
              if   Sil-Type (j) = 3	*> for Crs, switch the reverse flag
                if Audit-Reverse-Transaction = zero
                   move 1 to Audit-Reverse-Transaction
                   move 5      to Audit-Type
                   move Sih-cr to Audit-Cr-for-Invoice
                else
                   move zero to Audit-Reverse-Transaction
                end-if
              end-if
              move Stk-Audit-No           to Audit-No
*>
*> Now get the stock record
*>
              if   WS-Stock-No-Long = spaces
                   move WS-Abrev-Stock to WS-Stock-Abrev-Key
                   move  2 to File-Key-No
                   perform Stock-Read-Indexed  *> read Stock-File record key WS-Stock-Abrev-Key invalid key
                   if   FS-Reply = 21
                        move zero to Stock-Cost
                        move spaces to WS-Stock-Key
                   end-if                      *> end-read
              else
                   move WS-Temp-Stock-Key to WS-Stock-Key
                   move  1 to File-Key-No
                   perform Stock-Read-Indexed  *> read Stock-File key WS-Stock-Key invalid key
                   if   FS-Reply = 21
                        move zero to Stock-Cost
                        move spaces to WS-Stock-Key
                   end-if                      *> end-read
              end-if
              if   fs-reply not = zero
                   perform Eval-Status
                   display SL198         at line WS-23-lines col 1 with erase eol foreground-color 4
                   display fs-reply      at line WS-23-lines col 16 with foreground-color 3
                   display exception-msg at line WS-23-lines col 19 with foreground-color 3
                   display WS-Stock-Key  at 2064 with foreground-color 3
                   display sl006         at line WS-lines col 01 with foreground-color 3
                   accept  WS-reply      at line WS-lines col 30
                   display " "           at line WS-23-lines col 1 with erase eos
              end-if
*>
*> If we have great, but if not Stock-Cost is zero which helps it show up in
*>    proof reports
*>
              if   WS-Stock-Key not = spaces		*> we have a stock rec.
               and Stock-Services-Flag not = "Y"
                   if       Sil-Type (j) not = 3	*> Its not a Credit note
                            add CIT-D-Trans-Qty (Tab-D) to Stock-Held
                            compute  Audit-Stock-Value-Change =
                                     Audit-Transaction-Qty * Stock-Cost
                   end-if		*> CIT-D is NEW items so not on CRs.
                   if       Sil-Type (j) = 3		*> It is a Credit note
                            subtract CIT-D-Trans-Qty (Tab-D) from Stock-Held
                            compute  Audit-Stock-Value-Change =
                                     Audit-Transaction-Qty * Stock-Cost * -1
                   end-if
*>
*> This from sl910 but adds reversed for CR and receipts/invs as back in stock
*>
                   if       WS-Inv-Mth not < 1 or > 12
                     if      Sil-Type (j)  = 1 or 2                    *> Invoice and Recepts
                              add CIT-D-Trans-Qty (Tab-D) to Stock-Adds
                              add CIT-D-Trans-Qty (Tab-D) to Stock-TD-Adds (WS-Inv-Mth)
                     else
                     if      Sil-Type (j) = 3                         *> Credit Notes
                              add CIT-D-Trans-Qty (Tab-D) to Stock-Deducts
                              add CIT-D-Trans-Qty (Tab-D) to Stock-TD-Deds (WS-Inv-Mth)
                     end-if    *> type = 3
                   end-if      *> inv-mth good
*>
*>
                   if       Stock-Held < zero		*> Should NOT happen as testing in data entry but if a Cr?
                      and   Stock-Services-Flag not = "Y"
                            multiply -1 by Stock-Held
                            add Stock-Held to Stock-Pre-Sales
                            move zero to Stock-Held
                   end-if
                   if       Stock-Held > zero
                      and   Stock-Services-Flag not = "Y"
                            multiply Stock-Held by Stock-Cost giving Stock-Value
                   else
                            move zero to Stock-Value
                   end-if
                   move 1 to File-Key-No
                   perform  Stock-Rewrite         *> rewrite  Stock-Record invalid key
                   if       FS-Reply = 21
                            display SL191    at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
                            display fs-reply at line WS-23-lines col 38 with foreground-color 2 highlight
                            display SL006    at line WS-lines col 1
                            accept WS-reply  at line WS-lines col 45
                   end-if                *> end-rewrite
                   if       fs-reply not = zero
                            perform Eval-Status
                            display SL199         at line WS-23-lines col 1 with erase eol foreground-color 4
                            display fs-reply      at line WS-23-lines col 16 with foreground-color 3
                            display exception-msg at line WS-23-lines col 19 with foreground-color 3
                            display WS-Stock-Key  at 2064 with foreground-color 3
                            display sl006         at line WS-lines col 01 with foreground-color 3
                            accept  WS-reply      at line WS-lines col 30
                            display " "           at line WS-23-lines col 1 with erase eos
                   end-if
              end-if
*>
              if   Stk-Audit-Used = 1
                   move zero to Stk-Activity-Rep-Run		*> Need to run audit report
                   perform  Stock-Audit-Write       *> write WS-Stock-Audit-Record
                   if      fs-reply not = zero
                           perform Eval-Status
                           display SL190         at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
                           display fs-reply      at line WS-23-lines col 38 with foreground-color 2 highlight
                           display exception-msg at line WS-23-lines col 41 with foreground-color 3
                           display SL006         at line WS-lines col 1
                           accept WS-reply       at line WS-lines col 45
                   end-if
              end-if
     end-perform.
*>
 Update-Stock-Exit.
     exit     section.
*>
 Eval-Status        section.
*>=========================
*>
*> With advent of moving to FH & DALs is this still needed?
*>   Problem is dealing with DAL processing but many msgs still can
*>    apply so we will leave it in without change.
*>
     move     spaces to exception-msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by Exception-Msg.
*>
 Main-Exit.   exit section.
*>
 read-details  section.
*>====================
*>
     move     zero to j.
     perform  sih-lines times
              add  1 to j
              move sih-invoice to invoice-nos
              move J to item-nos
              perform Invoice-Read-Next      *> read invoice-file
                                             *>  end-read
              move WS-Invoice-Record to Invoice-Lines (j)
     end-perform.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 net-compute             section.
*>==============================
*>
     multiply work-n  by  work-d  giving  work-1.
     divide   work-1  by  100     giving  work-1.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 comm-routines section.
*>********************
*>
 accept-money6a.
*>-------------
*>
     move     zero to WS-poundsd6 WS-penced6 amt-ok6.
*>
 accept-money6b.
*>-------------
*>
     display  WS-amount-screen-display6 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs   with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 accept-money6c.
*>-------------
*>
     move     amt-wk-pence6 to WS-pence6.
     move     amt-wk-pds6 to WS-pound6.
     display  WS-amount-screen-display6 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs   with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 accept-money7a.
*>-------------
*>
     move     zero to WS-poundsd7 WS-penced7 amt-ok7.
*>
 accept-money7b.
*>-------------
*>
     display  WS-amount-screen-display7 at curs with foreground-color 3.
     accept   WS-amount-screen-accept7  at curs  with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 accept-money7c.
*>-------------
*>
     move     amt-wk-pence7 to WS-pence7.
     move     amt-wk-pds7 to WS-pound7.
     display  WS-amount-screen-display7 at curs with foreground-color 3.
     accept   WS-amount-screen-accept7  at curs  with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 comm-exit.   exit.
*>--------    ----
*>
 inv-level-1  section.		*> No one should be using this consider scrapping and forcing invoicer =2 etc
*>===================
*>
     display  WS-dash        at 1101 with foreground-color 2.
     display  "Level 1"      at 1201 with foreground-color 2.
     display  "Line - "      at 1216 with foreground-color 2.
     display  "<          >" at 1236 with foreground-color 2.
     display  "<          >" at 1254 with foreground-color 2.
     display  "<          >" at 1267 with foreground-color 2.
     display  "Code"         at 1405 with foreground-color 2.
     display  "<---Net---->  Vat   Vat Amount  Gross Amount" at 1436 with foreground-color 2.
*>
 loop.
*>***
*>
     perform  Display-Outline-1 varying lin from 16 by 1 until lin not < WS-23-lines.
*>
*>     subtract 16 from WS-23-lines giving m.   *> 24 line screen
     subtract WS-Accept-Body from  i.		*> was m from i
     move     1 to j.
     display  I at 1223 with foreground-color 2.
     move     zero to cob-crt-status.   *> from sl910
     perform  Get-Data-1.
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
*>
     if       new-screen = 1
              go to loop.
*>
     if       sil-description (I) not = spaces
        and   I not = 40
*>       and  escape-code not = "Q"
              go to  loop.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Get-Data-1  section.     *> No one should be using this consider scrapping and forcing invoicer =2 etc
*>==================
*>
 Get-Data-1-Main.
     add      J  15  giving  lin.
     if       lin  > WS-23-lines
              subtract 1 from i
              move 1 to new-screen
              go to  Main-Exit.
*>
     move     zero to new-screen.
*>
 Get-Code.
*>*******
*>
     move     sil-pa (I) to WS-pa.
     move     7 to cole.
     display  WS-pa at curs with foreground-color 3.
     accept   WS-pa at curs with foreground-color 3 update.
*>
     if       WS-pa = spaces
              go to  Main-Exit.
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
*>
     if       WS-pa = "<<"
         and  I = 1
              go to Get-Code.
*>
     if       WS-pa = "<<"
              subtract  1  from  lin
              if    lin  >  15
                    subtract  1  from  i
                    subtract 1 from j
                    go to  Get-Code
              else
                    subtract WS-Accept-Body from  I    *> Was 8 Need to follow logic, can we use WS-Accept-Body ??
                    go to Get-Data-1-Main.
*>
     move     WS-pa to delete-test.
     if       delete-field = "**"
              perform clear-down-line
              subtract 1 from i
              perform Display-Outline-1
              go to Get-Code.
*>
     move     WS-pa to sil-pa (I) pa-group.
     move     "S" to pa-system.
     move     11 to cole.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     if       FS-Reply = 21
              display SL186 at line WS-23-lines col 1 with foreground-color 4 highlight beep
              go to  Get-Code.
     display  " " at line WS-23-lines col 1 with erase eol.
*>
     display  pa-desc at curs with foreground-color 3.
     move     pa-desc  to  sil-description (I).
*>
 get-net.
*>******
*>
     move     37 to cole.
     move     sil-net (I) to amt-ok7.
     perform  accept-money7c.
     if       amt-ok7 = zero
              go to Get-Code.
     move     amt-ok7 to sil-net (I) WS-net.
*>
 Get-Vat-Code.
*>***********
*>
     move     50 to cole.
     move     sil-vat-code (I) to vat-code.
     display  vat-code at curs with foreground-color 3.
     accept   vat-code at curs with foreground-color 3 update.
*>
     if       vat-code  >  3     *> last two are for non-UK sales tax
              go to  Get-Vat-Code.
*>
     move     vat-code  to  sil-vat-code (I).
     if       vat-code = zero
              move  zero  to  amt-ok6
     else
              move vat-rate (vat-code) to WS-vat-rate
              compute amt-ok6 rounded = (WS-net * WS-vat-rate) / 100.
*>
 get-vat-rate.
*>***********
*>
     move     56 to cole.
     perform  accept-money6c.
     move     amt-ok6 to sil-vat (I)
                         WS-vat.
*>
     add      WS-vat WS-net giving  display-9.
     move     68 to cole.
     display  display-9 at curs with foreground-color 3.
*>
     perform  Running-Totals.
*>
     add      1 to j.
     add      1  to  i.
     go       to Get-Data-1-Main.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 inv-level-2             section.
*>==============================
*>
     display  WS-dash                 at 1101 with foreground-color 2.
     if       SL-Stock-Link not = "Y"
              display  "Level 2"      at 1201 with foreground-color 2
     else
              display  "Stock Linked" at 1201 with foreground-color 2.
     display  "Line - "               at 1216 with foreground-color 2.
     display  "Net <          >"      at 1227 with foreground-color 2.
     display  "Vat <          >"      at 1244 with foreground-color 2.
     display  "Invoice <          >"  at 1261 with foreground-color 2.
     if       SL-Stock-Link = "N"		*> No stock then process PA code
              display  "Product    Code <---------Description-------->   Qty   Unit Price  Disc. Vat"
                                     at 1405 with foreground-color 2
     else
              display  "Product     <----------Description--------->    Qty   Unit Price  Disc. Vat"
                                     at 1405 with foreground-color 2.
*>
 loop.
*>***
*>
     perform  Display-Outline-2 varying lin from 16 by 1 until lin not < WS-23-lines.
*>
*>     subtract 16 from WS-23-lines giving m.   *>  move 1 to i
     subtract WS-Accept-Body from i.		*>  was m
     move     1  to  j.
*>
     display  I at 1223 with foreground-color 2.
*>
     move     zero to CIT-A CIT-D TAB-A TAB-D.
     perform  Get-Data-2.
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
*>
     if       new-screen = 1
              go to  loop.
*>
     if       WS-product not = spaces
        and   I not = 40			*> max no. of items per invoice
*>       and   escape-code not = "Q"
              go to loop.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Get-Data-2              section.
*>==============================
*>
*>**********************************************************************
*>  This section will accept invoice line data if SC (stock control)   *
*>  is NOT linked in param file. If it is linked, will only request:   *
*>  Stock code or if entered chars = 7 or less, Abrev code so can      *
*>  search same if using F3 to find 1st then using F2 for next record. *
*>  in place of the return key.                                        *
*>  Also will allow search on description using F6 in stock code entry *
*>  and then will accept a description using F5 to search 1st and for  *
*>  next records.   CHANGE TO SUIT CODE                                *
*>                                                                     *
*>  For Vat Code, will also Accept S(tandard), R(educed) & Z(ero) in   *
*>   place of 1, 2, 3 respectively but will be replaced with 1, 2, 3.  *
*>**********************************************************************
*>
 Get-Data-2-Main.
     add      J  15  giving  lin.
     if       lin  > WS-23-lines - 1
              subtract  1  from  i
              move  1  to  new-screen
              go to  Main-Exit.
*>
     move     zero  to  new-screen.
*>
 Get-Product.
*>**********
*>
     move     2 to cole.
     move     sil-product (I) to WS-product.
     display  WS-product at curs with foreground-color 3.
     accept   WS-product at curs with foreground-color 3 update.
*>
     if       WS-product = spaces
              go to Main-Exit.
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
*>
     move     function upper-case (WS-product) to WS-product.
     move     WS-product to test-product.
     add      1 to CIT-A.                   *> items deleted from an invoice or qty changed
*>
     if       WS-product = sil-Product (I)  *> No Change
      if      SL-Stock-Link = "N"           *> so forget table
              subtract 1 from CIT-A
              go to Get-Code
      else                                  *> SAME Stock Item
              move     zero to CIT-New-Product
              move     WS-product          to CIT-A-Stock-Key (CIT-A)
              move     sil-Description (I) to CIT-A-Desc (CIT-A)
              move     17 to cole                *> 4 Desc.
              display  sil-Description (I) at curs with foreground-color 3
              move     WS-Product to WS-Temp-Stock-Key
              move     sil-Qty (I)         to CIT-A-Trans-Qty (CIT-A)
              perform  Get-Simple-Stock      *> 12/08/23
              go to Get-Qty                  *> Desc does not change against product
      end-if
     end-if
*>
     if       sil-comment
              move WS-product to sil-product (I)
              move zero to sil-net (I) sil-qty (I) sil-vat (I)
              go to  Get-Desc.
*>
     if       WS-product = "<<          "
              subtract  1  from  lin
              go to Get-Prod-Test.
*>
*> If here we have a change of product but only interested for Audit if stock linked
*>
     if       SL-Stock-Link = "Y"            *> Save original item details in deleted table
              move     sil-Product (I)     to CIT-A-Stock-Key (CIT-A)
              move     sil-Description (I) to CIT-A-Desc (CIT-A)
              move     sil-Qty (I)         to CIT-A-Trans-Qty (CIT-A)
*>                                                         Thats the original, now for the new
              add      1 to CIT-D
              move     1 to CIT-New-Product
              move     WS-Product to CIT-D-Stock-Key (CIT-D)  *> still need qty & desc
     end-if
     move     WS-product to sil-product (I).     *> NOW NEED TO GET Stock item from the Stock file etc <<<<<<<<<<<
     if       WS-Product (1:2) = "**"            *> deleted line
              subtract 1 from CIT-D
              move zero to CIT-New-Product
              go to Get-Code.                    *> to process a deleted line
     if       SL-Stock-Link = "N"
              go to Get-Code.
*>
*>>>>>> Now process stock file etc <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
*>
     move     17 to cole.                *> 4 Desc.
*>
*> Search nearest Abrev key and read next ..
*>  When this is tested we can wrap this and next together with a F3 test then a if F2 or F3 test
*>
     if       cob-crt-status = cob-scr-F3                *> search Abrev then read next & thereafter F2 until wanted
              move WS-Abrev-Stock to WS-Stock-Abrev-Key
              move  2 to File-Key-No
              set   fn-not-less-than to true
              perform Stock-Start                  *> start Stock-File key not < WS-Stock-Abrev-Key invalid key
              if    FS-Reply = 21 or = 23
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              perform Stock-Read-Next
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to sil-product (I)    *> have we the right one?
              display WS-Stock-Desc at curs with foreground-color 3
              go to Get-Product
     end-if
*>
     if       cob-crt-status = cob-scr-F2
              perform Stock-Read-Next
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to sil-product (I)    *> have we the right one?
              display WS-Stock-Desc at curs with foreground-color 3
              go to Get-Product
     end-if
*>
*> Search on Desc. but has dup keys so disp. Abrev. code & F5 for next on description
*>  When this is tested we can wrap this and next together with a F6 test then a if F5 or F6 test
*>
     if       cob-crt-status = cob-scr-F6
              move    sil-description (I) to WS-description
              accept  WS-description at curs with foreground-color 3 update
              move WS-Description to WS-Stock-Desc
              move  3 to File-Key-No
              set fn-not-less-than to true
              perform Stock-Start     *> start Stock-File key not < WS-Stock-Desc invalid key
              if    FS-Reply = 21
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              perform Stock-Read-Next
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to sil-product (I)    *> Got the right one? Show desc, stock held & retail price
                                      WS-Product
              display WS-Stock-Desc at curs with foreground-color 3 highlight
              move Stock-Held to WS-Qty
              if       Stock-Services-Flag = "Y"
                       move 1 to WS-Qty
              end-if
              display WS-Qty at line lin col 53 with foreground-color 3 highlight
              accept WS-reply at 2410            *> TESTING ONLY
              move Stock-Retail to amt-ok7
              move amt-wk-pds7   to WS-pound7
              move amt-wk-pence7 to WS-pence7
              display WS-amount-screen-display7 at line lin col 60 with foreground-color 3 highlight
              go to Get-Product
     end-if
*>
     if       cob-crt-status = cob-scr-F5         *> Read next on Desc.
              perform Stock-Read-Next
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to sil-product (I)    *> Got the right one? Show desc, stock held & retail price
                                      WS-Product
              display WS-Stock-Desc at curs with foreground-color 3 highlight
              move Stock-Held to WS-Qty
              if       Stock-Services-Flag = "Y"
                       move 1 to WS-Qty
              end-if
              display WS-Qty at line lin col 53 with foreground-color 3 highlight
              move Stock-Retail to amt-ok7
              move amt-wk-pds7   to WS-pound7
              move amt-wk-pence7 to WS-pence7
              display WS-amount-screen-display7 at line lin col 60 with foreground-color 3 highlight
              go to Get-Product
     end-if.
*>
 Get-Simple-Stock.
*>
*> So, no special function just search for entered key
*>
     if       WS-Stock-No-Long = spaces
              move WS-Abrev-Stock to WS-Stock-Abrev-Key
              move 2 to File-Key-No
     else
              move WS-Temp-Stock-Key to WS-Stock-Key
              move 1 to File-Key-No
     end-if
     perform  Stock-Read-Indexed
     if       FS-Reply = 21 or = 23
              move SL196 to WS-Stock-Desc
              display WS-Stock-Desc at curs with foreground-color 4
              go to Get-Product
     end-if.
*>
 GSS-End.
*> can shorten code now so rem out next block vbc 27/08/17
*>
 *>    else
 *>             perform Stock-Read-Indexed   *> read Stock-File key WS-Stock-Key invalid key
 *>             if   FS-Reply = 21
 *>                  move SL196 to WS-Stock-Desc
 *>                  display WS-Stock-Desc at curs with foreground-color 4
 *>                  go to Get-Product
 *>             end-if
 *>    end-if
     perform  Test-For-Read-Stock.
*>
 Process-Stock-Record.
*>
*>  Have the required Stock record so get and show the desc
*>
     move     17 to cole.        *> Desc.
     move     Stock-sa-Group to WS-pa
                                pa-group
                                sil-pa (I).
     display  WS-Stock-Desc   at curs with foreground-color 3.
     move     WS-Stock-Desc to WS-description
                               sil-description (I)
                               CIT-D-Desc (CIT-D).
     move     Stock-Retail  to amt-ok7.
     move     Stock-Retail  to WS-Unit.
     move     amt-wk-pds7   to WS-pound7.
     move     amt-wk-pence7 to WS-pence7.
     display  WS-amount-screen-display7 at line lin col 60 with foreground-color 3.
     move     Stock-Held to WS-qty.
     if       Stock-Services-Flag = "Y"
              move 1 to WS-Qty
     end-if
     go       to Get-Qty.          *> Bypass manual input code as comes from stock record
*>
 Get-Prod-Test.   *> THESE TESTS LOOK WRONG IF SCREEN LONGER THAN 24 LINES <<<<< (in sl910)
*>************        So to be tested for
*>
     if       I = 1
              add 1 to lin
              go to Get-Product.
*>
     if       lin  >  15
              subtract  1  from  i
              subtract  1  from  j
              go to  Get-Product
      else
              subtract WS-Accept-Body from I           *> instead of 8 can we use WS-Accept-Body ??
              go to Get-Data-2-Main.
*>
 clear-down-line.
*>**************
*>
*> Clear deleted item by moving down 1 line at a time reducing line count by 1
*>  every time a line item is deleted.
*>
     perform  varying z from I by 1 until z > 39
              move Invoice-Lines (z + 1) to Invoice-Lines (z)
              move z to sil-line (z)
     end-perform
*>
     move     zero to z.
     if       I not > sih-lines			*> Check that the deleted line is not the last item
              move sih-invoice to invoice-nos
              move sih-lines  to  item-nos
              perform  Invoice-Delete           *> delete the last item (that was)
              subtract 1 from sih-lines.
*>
 Get-Code.
     move     sil-product (I) to delete-test.
     if       delete-field = "**"
              perform clear-down-line
              subtract 1 from i
              perform Display-Outline-2
              go to Get-Product.
*>
     move     sil-pa (I) to WS-pa.
     move     17 to cole.
     display  WS-pa at curs with foreground-color 3.
     accept   WS-pa at curs with foreground-color 3 update.
*>
     if       WS-pa = spaces
              go to  Get-Product.
     move     "S" to pa-system.
     move     WS-pa to pa-group sil-pa (I).
     move     21 to cole.                       *> disp error in desc.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     if       FS-Reply not = zero
              display SL186 at curs with foreground-color 4
              go to  Get-Code.
*>
 Get-Desc.
     if       SL-Stock-Link = "Y"
              move 17 to cole
     else
              move 21 to cole.
     move     sil-description (I) to WS-description.
     display  WS-description at curs with foreground-color 3.
     accept   WS-description at curs with foreground-color 3 update.
*>
     if       WS-description = space
              move "B" to escape-code
     else
              move space to escape-code.
     if       escape-code = "B"
         and  sil-comment
              go to Get-Product.
     if       escape-code = "B"
              go to  Get-Code.
*>
     move     WS-description to sil-description (I).
     if       sil-comment
              go to  Jump-Totals.
*>
 Get-Qty.
     move     sil-qty (I) to WS-qty.
     move     53 to cole.
     if       Stock-Services-Flag = "Y"
              move 1 to WS-Qty
     end-if
     display  WS-qty at curs with foreground-color 3.
     accept   WS-qty at curs with foreground-color 3 update.
*>
     if       WS-qty = zero
      and     SL-Stock-Link = "Y"
              go to Recomp-Net. 		*> deleting this transaction so zero qty
     if       WS-qty = zero
              go to Get-Desc.
     if       SL-Stock-Link = "Y"         	*> make sure not selling more stock than held
       and    WS-qty > Stock-Held
        and   Stock-Services-Flag not = "Y"
              move Stock-Held to WS-Qty
              go to Get-Qty.
*>
     if       SL-Stock-Link = "Y"		*> bypass accept unit price
       and    CIT-New-Product = 1
              move WS-Qty              to CIT-D-Trans-Qty (CIT-D)
              go to Recomp-Net.
     if       SL-Stock-Link = "Y"		*> bypass accept unit price
       and    CIT-New-Product = zero
       and    WS-Qty = Sil-Qty (I)
              if    CIT-A = zero
                    move  1 to CIT-A
              end-if
              initialize CIT-Additions (CIT-A)	*> No change so clear the table entry
              subtract 1 from CIT-A		*> as only possible changes discount & vat does not effect stock
              go to Recomp-Net.
     if       SL-Stock-Link = "Y"		*> bypass accept unit price
       and    CIT-New-Product = zero
       and    WS-Qty not = Sil-Qty (I)		*> We have a change in qty
              subtract WS-Qty from Sil-Qty (I) giving CIT-A-Trans-Qty (CIT-A)
*>              if  CIT-A-Trans-Qty > zero	*> selling less to return unused/sold as reverse trans
     end-if.    *> Any thing else needed ???????

*>
 Get-Unit.
     move     60 to cole.
     move     sil-unit (I) to amt-ok6.
     perform  accept-money6c.
     if       amt-ok6 = zero
              go to Get-Qty.
     move     amt-ok6 to WS-unit.
*>
 Recomp-Net.
     if       WS-Qty = zero
              if       I > zero   *> JIC
                       initialise Invoice-Lines (I) *> clear down any above entered data for item line
                       subtract 1 from I
              end-if
              go to Get-Data-2
     end-if.
*>
     multiply WS-qty by  WS-unit giving  WS-net on size error
              display  "SizEr" at curs with blink foreground-color 4.
              go to Get-Qty.
*>
     move     WS-net to  display-9 sil-net (I).
     move     WS-qty to sil-qty (I).
     move     WS-unit to sil-unit (I).
     display  display-9 at 1232 with foreground-color 3.
*>
 Get-Disc.
     move     sil-discount (I) to  WS-discount.
     move     72 to cole.
     move     WS-disc-wka to WS-disca1.
     move     WS-disc-wkb to WS-disca3.
     display  WS-discount-display at curs with foreground-color 3.
     accept   WS-discount-accept  at curs with foreground-color 3 update.
     move     WS-discb1 to WS-disc-wka.
     move     WS-discb3 to WS-disc-wkb.
*>
     move     WS-discount to  work-d sil-discount (I).
     move     WS-net to  work-n.
*>
     perform  net-compute.
*>
     subtract work-1  from  WS-net.
*>
     move     WS-net to sil-net (I) display-9.
     display  display-9 at 1232 with foreground-color 3.
*>
 Get-Vat-Code.
     move     "S" to Vat-Code-X.  *> 12/8/23  for Standard rate
     move     79 to cole.
     move     sil-vat-code (I) to vat-code.
     display  vat-code-X at curs with foreground-color 3.
     accept   vat-code-X at curs with foreground-color 3 update UPPER.
*>
*>   Accept S, R and Z replacing with 1, 2 & 3.      Rating
*>
     if       Vat-Code-X = "S"                   *> Standard code 1
              move 1 to Vat-Code
      else
       if     Vat-Code-X = "R"                   *> Reduced  code 2
              move 2 to Vat-Code
        else
         if   Vat-Code-X = "Z"                   *> Zero     code 3
              move 3 to Vat-Code.
*>
     if       vat-code < 1 or > 3                *> using 1st three as last 2 are Sales tax, Not used in the UK.
              go to  Get-Vat-Code.                *> so change test for 'not = 4 or 5' instead of '> 3'
*>
     move     vat-code  to  sil-vat-code (I).
*>
     if       vat-code = zero
              move  zero  to  WS-vat
     else
              move vat-rate (vat-code) to WS-vat-rate
              compute  WS-vat rounded = (WS-net * WS-vat-rate) / 100.
*>
     move     WS-vat to  display-9 sil-vat (I).
     display  display-9 at 1249 with foreground-color 3.
*>
     perform  Running-Totals.
*>
 Jump-Totals.
     add      1  to  j.
     add      1  to  i.
     go       to Get-Data-2-Main.
*>
 Test-For-Read-Stock.
     if       fs-reply not = zero
              perform Eval-Status
              display SL198    at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
              display fs-reply at line WS-23-lines col 20 with foreground-color 2 highlight
              display exception-msg at line WS-23-lines col 24 with foreground-color 3
              display SL006 at line WS-lines col 1
              accept WS-reply at line WS-lines col 45
     end-if.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 erase-screen            section.
*>==============================
*>
     move     1 to cole.
     display  space at curs with erase eos.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 End-Totals              section.
*>==============================
*>
 End-Totals-Main.
     perform  total-screen.
*>
     move     15  to  lin.
     perform  erase-screen.
*>
     display  "*********************" at 1660  with foreground-color 2
     display  "*" at 1760 with foreground-color 2
     display  "*" at 1760 with foreground-color 2
     display  "*" at 1860 with foreground-color 2
     display  "*" at 1880 with foreground-color 2
     display  "*" at 1960 with foreground-color 2
     display  "*" at 1980 with foreground-color 2
     display  "*********************" at 2060 with foreground-color 2
*>
     display  "Invoice Ok To Store?" at 1761 with foreground-color 2.
     display  "(Y/N)  [Y]" at 1967 with foreground-color 2.
*>
 confirmation.
*>***********
*>
     move     "Y"  to   WS-reply.
     accept   WS-reply at 1975 with foreground-color 6 update.
     move     function upper-case (WS-reply) to WS-reply.
*>
     if       WS-reply = "N"
              go to End-Totals-Main.
*>
     if       WS-reply not = "Y"
              go to  confirmation.
*>
     move     "P"  to  sih-status.
     move     space to sih-status-P
                       sih-Status-L.  *> 20/01/17
     subtract 1  from  i.
     move     I    to  sih-lines.
*>
     move     SInvoice-Header  to  WS-Invoice-Record.
     perform  Invoice-Rewrite.            *>  rewrite  invoice-record.
     if       fs-reply not = zero
              perform Eval-Status
              display sl192         at line WS-23-lines col  1 with erase eol foreground-color 4
              display fs-reply      at line WS-23-lines col 36 with foreground-color 3
              display exception-msg at line WS-23-lines col 39 with foreground-color 3
              display invoice-key   at line WS-23-lines col 64 with foreground-color 3
              display sl006         at line WS-lines    col  1 with foreground-color 3
              accept  WS-reply      at line WS-lines    col 30
              display " "           at line WS-23-lines col  1 with erase eos
     end-if
*>
     move     zero to  j.
     perform  write-details  I  times.
     perform  Update-Stock-And-Audit.
     move     1 to s-flag-i.
     move     11  to  lin.
     perform  erase-screen.
*>
 Main-Exit.   exit section.
*>********    *****
*>
 total-screen            section.
*>==============================
*>
     move     1 to cole.
     move     11 to lin.
     display  " " at curs with erase eos.
     display  WS-dash at 1101 with foreground-color 2.
*>
     if       i-level-1
              move  1  to  menu-reply
     else
              move  2  to  menu-reply.
*>
     display  "Level "   at 1201 with foreground-color 2.
     display  menu-reply at 1207 with foreground-color 2.
     display  "<---Net---->   <---Vat--->" at 1225 with foreground-color 2.
     display  "<---Gross-->     Days"      at 1254 with foreground-color 2.
     display  "Sub-Totals"                 at 1404 with foreground-color 2.
     display  "{          }   {         }" at 1425 with foreground-color 2.
     display  "{          }     [  ]"      at 1454 with foreground-color 2.
*>
     display  Extra-Desc                   at 1504 with foreground-color 2.
     display  "[          ]   [         ]" at 1525 with foreground-color 2.
     display  "{          }"               at 1554 with foreground-color 2.
*>
     display  "Shipping & Handling"        at 1604 with foreground-color 2.
     display  "[          ]   [         ]" at 1625 with foreground-color 2.
     display  "{          }"               at 1654 with foreground-color 2.
*>
     display  "Late Charge"                at 1704 with foreground-color 2.
     display  "[          ]              " at 1725 with foreground-color 2.
     display  "{          }     [  ]"      at 1754 with foreground-color 2.
*>
     display  "------------   -----------" at 1825 with foreground-color 2.
     display  "------------"               at 1854 with foreground-color 2.
*>
     display  "Itemised Totals"            at 1904 with foreground-color 2.
     display  "{          }   {         }" at 1925 with foreground-color 2.
     display  "{          }"               at 1954 with foreground-color 2.
*>
     move     sih-net  to  display-9.
     display  display-9 at 1426 with foreground-color 3.
*>
     move     sih-vat  to  display-8.
     display  display-8 at 1441 with foreground-color 3.
*>
     add      sih-net  sih-vat  giving  display-9.
     display  display-9 at 1455 with foreground-color 3.
*>
 get-days.
*>*******
*>
     move     sih-days to WS-dayes.
     display  WS-dayes at 1472 with foreground-color 3.
     if       sih-type not = 2
*>              move zero to sih-days		*> its a proforma so leave it & unchanged
              go to get-extra.
*>
     accept   WS-dayes at 1472 with foreground-color 3 update.
     move     WS-dayes to sih-days.
*>
 get-extra.
*>********
*>
     if       Extra-Type = space
              move zero to sih-extra sih-e-vat
              go to get-carriage.
*>
     if       Extra-Rate not = zero
              compute  sih-extra = (sih-net * Extra-Rate) / 100
     else
              move  zero  to  sih-extra.
*>
     move     1526 to curs.
     move     sih-extra to amt-ok7.
     perform  accept-money7c.
     move     amt-ok7 to sih-extra.
*>
 get-extra-vat.
*>************
*>
     if       sih-extra = zero
              move  zero to  sih-e-vat
              go to get-carriage.
*>
     compute  amt-ok6 = sih-extra  *  vat-rate-1  /  100.
*>
     move     1541 to curs.
     perform  accept-money6c.
     move     amt-ok6 to sih-e-vat.
*>
     add      sih-extra  sih-e-vat  giving  display-9.
     display  display-9 at 1555 with foreground-color 3.
*>
     if       discount
         and  sih-extra not = zero
              multiply -1 by sih-extra
              multiply -1 by sih-e-vat.
*>
 get-carriage.
*>***********
*>
     move     1626 to curs.
     move     sih-carriage to amt-ok7.
     perform  accept-money7c.
     move     amt-ok7 to sih-carriage.
     compute  amt-ok6 rounded = sih-carriage * vat-rate-1 / 100.
*>
*> Note That Vat-Rate-1 Must Be Standard Rate For P & P
*>
 get-carriage-vat.
*>***************
*>
     move     1641 to curs.
     perform  accept-money6c.
     move     amt-ok6 to sih-c-vat.
     add      sih-carriage  sih-c-vat  giving  display-9.
     display  display-9 at 1655 with foreground-color 3.
*>
 get-deduct-amt.
*>*************
*>
     if       (sih-type not = 2  and not = 3)		*> Invoices, Credit Notes
          or  not late-charges
          or  WS-named = "Z"
              move  zero  to  sih-deduct-amt  sih-deduct-vat  sih-deduct-days
              go to  Main-Exit.
*>
     compute  amt-ok7 =  sih-net  /  10.
*>
     if       amt-ok7 <  4
              move  4  to  amt-ok7.
*>
     move     1726 to curs.
     perform  accept-money7c.
     move     amt-ok7 to sih-deduct-amt.
*>
 get-deduct-vat.
*>*************
*>
     move     zero to sih-deduct-vat.
*>
     add      sih-net  sih-extra  sih-carriage  sih-deduct-amt  giving  display-9.
     display  display-9 at 1926 with foreground-color 3.
*>
     add      sih-vat  sih-e-vat  sih-c-vat  sih-deduct-vat   giving  display-8.
     display  display-8 at 1941 with foreground-color 3.
*>
     add      sih-net  sih-extra  sih-carriage  sih-deduct-amt
              sih-vat  sih-e-vat  sih-c-vat  sih-deduct-vat    giving  display-9.
     display  display-9 at 1955 with foreground-color 3.
*>
 get-deduct-days.
*>**************
*>
     move     sih-days  to  WS-dayes.
     display  WS-dayes at 1772 with foreground-color 3.
     accept   WS-dayes at 1772 with foreground-color 3 update.
     move     WS-dayes to sih-deduct-days.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 invoice-details section.
*>======================
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Invoicing Data Amend" at 0132 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
     display  "****************************************" at 0441 with foreground-color 2.
     display  "*Date   [  /  /    ]*                  *" at 0541 with foreground-color 2.
     display  "*A/C Nos   [       ]*Ref   [          ]*" at 0641 with foreground-color 2.
     display  "*Invoice  [        ]*Order [          ]*" at 0741 with foreground-color 2.
     display  "****************************************" at 0841 with foreground-color 2.
     display  "F8 = Only Show delivery details on 'A/C nos' entry" at 0911 with foreground-color 2.
     display  "Type [ ]  <1> = Receipt; <2> = Account; <3> = Credit Note; <4> = Pro-Forma"
                                                         at 1001 with foreground-color 2.
*>
 invoice-enter.
*>************
*>
     move     1 to File-Key-No.
     move     zero to sih-invoice.
     display  sih-invoice at 0752 with foreground-color 3.
     accept   sih-invoice at 0752 with foreground-color 3 update.
     if       sih-invoice = zero
           or cob-crt-status = cob-scr-esc
              move 1 to z
              go to Main-Exit.
*>
     move     zero         to  item-nos.
     move     sih-invoice  to  invoice-nos.
     perform  Invoice-Read-Indexed.
     if       fs-reply not = zero
              display SL194 at 1640 with foreground-color 4
              display "fs-reply = " at 1665   *> TEMP VALUE FOR TESTING
              display FS-Reply at 1676
              display WS-invoice-key at 1705  *> VALID
              display invoice-key at 1725
              go to invoice-enter.
     move     WS-Invoice-Record to SInvoice-Header.
     display  " " at 1640 with erase eol.
*>
     if       sih-status = "Z" or "z"      *> Applied to OTM3
              display SL195 at 1601 with foreground-color 4 erase eol
              go to invoice-enter.
*>
     display  " " at 1601 with erase eol.
     move     sih-date to u-bin.
     perform  zz060-Convert-Date.   *> now have WS-date
     perform  Read-Details.
*>
 date-Input.
*>*********
*>
     display  WS-date at 0550 with foreground-color 3.
     accept   WS-date at 0550 with foreground-color 3 update.
     if       cob-crt-status = cob-scr-esc
         or   WS-date = spaces
              move 1 to z
              go to  Main-Exit.
*>
     move     WS-date to WS-Test-Date.
     perform  zz050-Validate-Date.
     if       u-bin = zero
              go to  date-Input.
*>
     move     u-bin  to sih-date.
*>
 customer-Input.
*>*************
*>
     display  sih-customer at 0653 with foreground-color 3.
     accept   sih-customer at 0653 with foreground-color 3 update UPPER.
 *>    move     function upper-case (sih-customer) to sih-customer.
*>
     if       cob-crt-status = cob-scr-esc
         or   sih-customer = spaces
              move  "Q"  to  escape-code
              go to  Main-Exit.
     if       Cob-Crt-Status = Cob-Scr-F8
              move "Y" to WS-Show-Delivery
     else
              move "N" to WS-Show-Delivery
     end-if
*>
     move     1  to  c-check.
*>
     move     sih-customer  to  WS-Sales-Key.
*>
     move     1 to File-Key-No.
     perform  Sales-Read-Indexed.
     if       fs-reply = 21
              move  zero  to  c-check.
*>
     if       not  c-exists
              go to  customer-Input.
*>
     if       delivery-tag = zero	*> Only show delivery details if F8 pressed instead of
       or     WS-Show-Delivery = "N"	*> accept on cust no. input
              go to  customer-setup.
*>
     move     "D"          to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Read-Indexed.
     if       fs-reply = 21
              move  zero  to  delivery-tag
              go to  customer-setup.
*>
     move     deliv-address to address-A.
*>
     go       to customer-display.
*>
 customer-setup.
*>*************
*>
     move     sales-address  to  address-A.
*>
 customer-display.
*>****************
*>
     if       delivery-tag = zero
              display sales-name at 0301 with foreground-color 3
     else
              display deliv-name at 0301 with foreground-color 3.
*>
     move     1  to  z.
     unstring address-A  delimited  by  sl-delim into  address-line count z pointer  z.
     display  address-line at 0401 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-A  delimited  by  sl-delim into  address-line count z pointer  z.
     display  address-line at 0501 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-A  delimited  by  sl-delim into  address-line count z pointer  z.
     display  address-line at 0601 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-A  delimited  by  sl-delim into  address-line count z pointer  z.
     display  address-line at 0701 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-A into  address-line  pointer  z.
     display  address-line at 0801 with foreground-color 3.
*>
     move     spaces  to  address-line.
*>
 ref-Input.
*>********
*>
     display  sih-ref at 0669 with foreground-color 3.
     accept   sih-ref at 0669 with foreground-color 3 update.
*>
 order-Input.
*>**********
*>
     display  sih-order at 0769 with foreground-color 3.
     accept   sih-order at 0769 with foreground-color 3 update.
*>
 type-Input.
*>*********
*>
     display  sih-type at 1007 with foreground-color 3.
     accept   sih-type at 1007 with foreground-color 3 update.
*>
     if       sih-type = zero
              go to Main-Exit.
*>
     if       sih-type  >  4 or < 1
              go to  type-Input.
*>
     if       sih-type = 3
              perform  cr-note
              if  escape-code = "Q"
                  go to  type-Input.
*>
     move     zero to z.
*>
     if       sih-type  >  2
              go to  Main-Exit.
*>
*>  Type 2 (Account) only
*>
     move     zero  to  we-error.
*>
     subtract sales-unapplied from sales-current.
*>
     if       sales-current  >  zero
              subtract sales-last-inv from run-date giving  work-1
              if work-1  >  sales-credit
              display "Overdue Balance <<<" at 1648 with foreground-color 2 highlight
              move  999  to  we-error.
*>
     if       sales-current  >  sales-limit
              display "Balance Exceeds Credit Limit <<<" at 1725 with foreground-color 2 highlight
              move  998  to  we-error.
*>
     if       sales-credit not > zero
          or  sales-limit  not > zero
              display "No Longer an Account Customer <<<" at 1825 with foreground-color 2 highlight
              move  997  to  we-error.
*>
     if       we-error = zero
              go to  Main-Exit.
*>
     display  ">>> Warning! " at 1635 with foreground-color 2 highlight.
     display  "**********************" at 1958 with foreground-color 2
     display  "*" at 2058 with foreground-color 2
     display  "*" at 2158 with foreground-color 2
     display  "*" at 2079 with foreground-color 2
     display  "*" at 2179 with foreground-color 2
     display  "**********************" at 2258 with foreground-color 2
*>
     display  "None Zero or ESC To Abort" at 2040 with foreground-color 2.
     display  "Return To Continue" at 2140 with foreground-color 2.
*>
     move     zero to z.
     accept   z at 2260 with foreground-color 3 update.
     if       cob-crt-status = cob-scr-esc
              move 1 to z   cob-crt-status.
     go       to Main-Exit.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 cr-note             section.
*>==========================
*>
*>  CRs are only processed against posted invoices, hence using OTM3.
*>
 Main.
     display  " " at 1201 with erase eol.
     display  " " at 1301 with erase eol.
     display  " " at 1401 with erase eol.
     display  " " at 1501 with erase eol.
     display  " " at 1601 with erase eol.
*>
 Main-Input.
*>*********
*>
     display  "Invoice To Credit - [        ]" at 1201 with foreground-color 2.
*>
     move     sih-cr to  WS-cr.
*>
     display  WS-cr at 1222 with foreground-color 3.
     accept   WS-cr at 1222 with foreground-color 3 update.
     if       cob-crt-status = cob-scr-esc
              move "Q" to escape-code
              go to Main-Exit.
     move     WS-cr to sih-cr.
     if       sih-cr = zero
              move  "Z"  to  WS-named
              go to  no-inv-restart
     else
              move  space to  WS-named.
*>
     if       sih-cr = 99999999
              move "Q" to escape-code
              go to Main-Exit
     else
              move space to escape-code.
*>
     move     sih-cr       to  oi3-invoice.     *> for ITM3
     move     sih-customer to  oi3-customer.    *> for ITM3
*>
     move     1 to File-Key-No.
     perform  OTM3-Read-Indexed.      *> Error cant find the invoice
     if       fs-reply not = zero
              display SL181 at line WS-23-lines col 01 with foreground-color 2 highlight
              go to  Main.
*>
     display  space at line WS-23-lines col 01 with erase eol.
     if       oi-type not = 2               *> Error can only credit Posted invoices
              display SL184  at line WS-23-lines col 01 with foreground-color 2 highlight
              go to Main-Input.
*>
     if       s-closed                  *> Error invoice is Paid
              display SL182  at 1301  with foreground-color 2 highlight
              go to Main-Input
     else
              display " " at line WS-23-lines col 01 with erase eol.
*>
     if       oi-hold-flag = "Q"        *> Warning Invoice has query flag set but we can continue
              display SL183  at line WS-23-lines col 01  with foreground-color 2 highlight.
*>
     if       invoice-customer not = WS-Sales-Key
              display SL193  at 1301 with foreground-color 4
              go to Main-Input.
*>
     move     oi-date to u-bin.
     add      1 oi-deduct-days to u-bin.
     if       u-bin > sih-date
              move "A" to WS-named.
*>
     add      oi-deduct-vat to oi-deduct-amt.
     add      oi-extra oi-carriage oi-deduct-amt oi-net
              oi-vat oi-c-vat oi-e-vat to oi-discount.
     subtract oi-paid from oi-discount.
*>
     display  "Amount O/S on Invoice is " at 1401   with foreground-color 2.
     move     oi-discount to display-9.
     display  display-9 at 1426 with foreground-color 3.
     move     oi-deduct-amt to display-8.
     display  "of which" at 1437 with foreground-color 2.
     display  display-8  at 1446 with foreground-color 3.
     display  "is Late Charges" at 1456 with foreground-color 2.
     if       WS-named = "A"
              display SL185 at 1510 with foreground-color 2.
     display  SL006  at 1626.
     accept   WS-reply  at 1661.
*>
 No-Inv-Restart.
     perform  Main.       *> Clear screen lines 12 - 16
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Program-Start section.
*>====================
*>
     display  " " at 0101 with erase eos.
     move     to-day to u-date WS-Test-Date.
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15   *> Analysis
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    move 1 to WS-Process-Func WS-Sub-Function
                    call "sl070" using WS-calling-data
                                       system-record
                                       to-day
                                       file-defs
                    call  "CBL_CHECK_FILE_EXIST" using File-15       *> Only if the call failed for some unknown reason
                                                       File-Info
                    if    return-code not = zero          *> not = zero - No file found
                          display SL186   at 2301
                          display SL003   at 2401
                          accept WS-reply at 2430
                    end-if
              end-if
     end-if
*>
*> Create Invoice & ITM3 files if do not exist but as requested Amend invoices, it should be !
*>    JIC
*>
     if       FS-Cobol-Files-Used             *> create invoice if not exist.
              call  "CBL_CHECK_FILE_EXIST" using File-16      *> Invoice
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    perform  Invoice-Open-Output
                    perform  Invoice-Close
              end-if
              call  "CBL_CHECK_FILE_EXIST" using File-19      *> create ITM3 if not exist
                                                 File-Info
              if    return-code not = zero        *> not = zero - No file found
                    perform OTM3-Open-Output
                    perform OTM3-Close
              end-if
     end-if
*>
*> if linked open Stock & Audit file
*>
     if       SL-Stock-Link = "Y"
       if     FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-11           *> Stock
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    perform Stock-Open-Output
                    perform Stock-Close
              end-if
              perform Stock-Open      *> Thats ok we just wont find any items!
              if     Stk-Audit-Used = 1
                     call  "CBL_CHECK_FILE_EXIST" using File-10    *> Stock-Audit
                                                        File-Info
                     end-call
                     if    return-code not = zero          *> not = zero - No file found
                           perform Stock-Audit-Open-Output
                     else
                           perform Stock-Audit-Open-Extend
                     end-if
              end-if
       end-if
     end-if
*>
*>
*> Made sure needed files exist although most should be present but - JIC so open files/tables.
*>
     perform  Invoice-Open.
     perform  OTM3-Open-Input.     *> .12 for ITM3 support in Cr notes.
*>
     perform  Sales-Open-Input.
     perform  Delivery-Open-Input.
     perform  Analysis-Open-Input.
*>
 Menu-Return.
*>**********
*>
     move     zero  to  menu-reply.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Display-Outline-1       section.
*>==============================
*>
     add      1  to  i.
     move     1 to cole.
     display  "(" at curs with erase eol foreground-color 2.
     move     2 to cole.
     display  I at curs with foreground-color 2.
     move     4 to cole.
     display  ") [  ]" at curs with foreground-color 2.
     move     36 to cole.
     display  "[          ] [ ]   {         } (" at curs with foreground-color 2.
     move     78 to cole.
     display  ")" at curs with foreground-color 2.
*>
 Main-Exit52a. exit section.
*>***********  ************
*>
 Display-Outline-2       section.
*>===============================
*>
     add      1  to  i.
     move     1 to cole.
     if       SL-Stock-Link = "N"		*> No stock then process PA code
              display "[             ][  ][" at curs with foreground-color 2 erase eol
              move    51 to cole
              display   "][     ][          ][     ][ ]" at curs  with foreground-color 2
     else				*> ignore PA
              display "[             ][" at curs with foreground-color 2 erase eol
              move    49 to cole
              display "]  [     ][          ][     ][ ]" at curs  with foreground-color 2
     end-if.
*>
 Main-Exit52b.     exit section.
*>=============================
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-Test-Date
*> output:  u-date/WS-date as uk date format
*>          u-bin not zero if valid date
*>
     move     WS-Test-Date to WS-date.
     if       Date-Form = zero
              move WS-Month to WS-Inv-Month    *> done again for UK - but JIC
              move 1 to Date-Form.
     if       Date-UK
              move WS-Month to WS-Inv-Month
              go to zz050-Test-Date.
     if       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              move WS-Month to WS-Inv-Month
              go to zz050-Test-Date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to WS-date.  *> swap Intl to UK form
     move     WS-Test-Date (1:4) to WS-Year.
     move     WS-Test-Date (6:2) to WS-Month.
     move     WS-Month           to WS-Inv-Month
     move     WS-Test-Date (9:2) to WS-Days.
*>
 zz050-Test-Date.
     move     WS-date to u-date.
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
 zz060-Exit.
     exit     section.
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
