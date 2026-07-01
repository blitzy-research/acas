       >>source free
*>
*>  CDF constants - Change If needed for BO Table size but should be enough  :-
*>                  likewise for Item-Table
*>
>>DEFINE CONSTANT   X-BO-Table-Size  AS  500   *> # of Back Orders at ANY one time
>>DEFINE CONSTANT   X-Itm-Table-Size AS  100   *> # of DIFFERENT Stock items on BO
>>DEFINE CONSTANT   X-BO-Delete-Size AS   50   *> # of BO Delete table entries per invoice

*> End of CDF constants
*>
*>  THERE IS TEST CODE IN THIS PROGRAM - REMOVE AFTER see zz210  <<<<<<<<<
*>         as prevents the deleting of BO records so thay can be reused.
*>
*>  This program Is very similar to sl810 (autogen)
*> so consider any changes to both but not for BO processing as not needed.
*>
*>***************************************************
*>                                                  *
*>               Invoice  Data  Entry               *
*>                                                  *
*>  This program Is used for both Batch & Immediate *
*>   Invoice printing, Pass-Value = 3 = Immediate   *
*>      then finish - one Invoice only.             *
*>                                                  *
*>***************************************************
*>
 Identification          division.
*>===============================
*>
      program-id.         sl910.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen, FBCS, FIDM, FIDPM 12/11/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Data Entry & Maintenance.
*>                        OTM3 Is used to check status of Invoices when Issuing CR.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas010  ->       (Stock-Audit)
*>                         auditMT
*>                        acas011  ->       (Stock)
*>                         stockMT.
*>                        acas012  ->       (Sales)
*>                         salesMT.
*>                        acas014  ->       (Delivery)
*>                         deliveryMT.
*>                        acas015  ->       (Analysis)
*>                         analMT.
*>                        acas017  ->       (DelInvNos)
*>                         sldelinvnosMT.
*>                        acas016  ->       (Invoices)
*>                         InvoiceMT.
*>                        acas019  ->       (OTM3) Open Item File
*>                         otm3MT.
*>
*>                        SL070. Analysis codes set up - Defaults only.
*>                        Sl930. Invoice print
*>                        Sl960. New Customer create
*>**
*>    Function used keys:
*>                        F1 - Enter New Customer process.
*>                        F2 - Stock - Read In order Next Stock Record.
*>                        F3 - Stock - Read specific Stock Record using Abbreviated key
*>                        F5 - Stock - Read next by Description
*>                        F6 - Stock - skip current order.
*>                        F8 - Use delivery address
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
*>                        SL190. *> Writing error to Stock Audit
*>                        SL191. *> Rewrite error on Stock record
*>                        SL192. *>
*>                        SL193.    Not same Customer
*>                        SL194.   Stock Read :         {error}
*>                        SL195.   Stock Rewrite :      {error}
*>                        SL196.   Not on File
*>                        SL201    Customer BO Not set     *> 17/03/24
*>                        SL202    Creating BO rec, changed Qty to held on Invoice  *> 17/03/24
*>                        SL203.   Err on BO write
*>                        SL205.   Info: using stock Held
*>                        SL206.   Comp overflow
*>                        SL207.   BO Table size exceeded - increase & recomp.
*>                        SL208.   Aborting BO processing this time.
*>                        SL209 - SL221.
*>****
*>  Changes.
*> 04/03/83 Vbc - Changes To Fdinv.Cob And Cr-Notes.
*> 22/03/83 Vbc - Cr-Notes.
*> 30/03/83 Vbc - When Creating Invoices Check For Sl-Charges &
*>                Sales-Late (Late-Charges).
*> 30/04/83 Sjw - Accept Late Charges Only If Invoice WS-Named On
*>                Cr. Notes.
*> 02/05/83 Vbc - #.
*> 13/10/83 Vbc - Use Deleted Invoice Nos If Available.
*> 17/11/83 Vbc - Cis Cobol Conversion.
*> 24/02/84 Vbc - Clear WS-Named Before Usage.
*> 01/03/84 Vbc - Support Of Sales-Unapplied In Invoice-Details.
*> 10/03/84 Vbc - Support Of sih-Day-Book-Flag.
*> 12/05/84 Vbc - Support Of Graphics,If Cn Check Openitm File.
*> 16/11/84 Vbc - Fix Abort Graphics Screen In Invoice-Details.
*> 07/01/85 Vbc - Fix Bug Clear Screen In Cr-Notes.
*> 03/03/09 vbc - .04 Migration to Open Cobol v3.00.00.
*> 16/03/09 vbc - .05 Bug/Feature 30.1 & 3 escape out at any level.
*> 04/04/09 vbc - .06 Support for F1 (or NEW) on Customer no. to create new
*>                    account. Sales & Purchase ledger both match function.
*>                    Changed usage of deleted folio nos. by
*>                    deleting record after re-use, matches PL020.
*> 26/11/11 vbc - .07 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .08 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .09 Changed usage of Stk-Date-Form to global Date-Form making former redundent.
*> 17/04/13 vbc       Note change regarding Invoicer setting = 2 did not reflect sl910 ?
*>                    Clear display for F1 key after accepting a valid cust no.
*> 15/05/13 vbc - .10 Add In support for direct link to Stock Control with Stock and Audit files
*>                    In Inv-Level-2. Changed stk code 12>13, desc 24>32 removing pa code
*>                    and consider add new display field OS for Out of Stock but on order
*>                    with delivery expected In 7 days or less
*>		      MORE?????
*>                    [all this also In sl920 and need to look at 930 - 960 for any needed changes]
*> 22/05/13 vbc - .11 Bug fixes from 09/10.
*>                .12 Ditto, missing stock-value computation.
*> 24/05/13 vbc - .13 Changed coding to use WS-accept-body Instead of '8' for larger screens
*>                    than 24 lines. Added Invoice to Audit record.
*>                    NEED TO CHECK CREDIT NOTE PROCESSING FOR REQUIREMENT FOR AUDIT FILE &
*>                    STOCK FILE PROCESSING!!
*> 30/04/15 vbc - .14 Changed file access for delinvoices (and for purchase pl020)
*>                    to ISAM - other modules need changing?
*> 24/10/16 vbc - .15 ALL programs now using wsnames.cob In copybooks
*> 30/10/16 vbc - .16 Support for RDB on  Analysis, Stock & Stock Audit tables
*>                    Instead of cobol files
*>                    using acas010, acas011 & acas015. Update version to v3.02
*>                    more to do, have renamed the calls for acas010,11 & 15
*>                    Stock-Audit, Stock & Analysis to reduce any coding errors
*>                    as there will be a lot of them In this module.
*> 15/01/17 vbc - .17 All programs upgraded to v3.02 for RDB processing.
*>                    -------------------------------------------------
*>                    Removed maps99 processing.
*>                    OTher RDB processing added - still Invoicing O/S.
*> 17/01/17 vbc - .18 Migrated all but Invoice & ITM3 files to FH & DAL.
*> 18/01/17 vbc - .19 Support for Vat-Code-X for S(tandard), R(educed), Z(ero)
*>                    In place of 1, 2, 3.
*> 20/01/17 vbc - .20 Removed the Letter postfix after Invoice nos when using
*>                    own Invoice nos, as created for one Customer many years
*>                    ago, which could cause Issues when posting to ITM3.
*>                    2 B removed from the Invoice file layout.
*> 25/01/17 vbc       Dry testing completed.
*> 10/02/17 vbc - .21 Updated FD/WS for 016,019 and replaced cobol verbs
*>                    for access to FH/DALs.
*> 17/04/17 vbc -     Dry checked for slinvoiceMT.
*> 27/08/17 vbc - .22 Added Message SL194 - Stock Read : {a read error}
*>                           and    SL195 - Stock Rewrite : {a write error}
*>                    Instead of embedded msg/s.
*>                    Using SL194 In Test-For-Read-Stock Instead of embedded.
*>                    likewise SL196 In place of "Not Found" and "End of file".
*> 05/03/18 vbc - .23 Removed unused msgs 187, 188, 189 changed description of some msgs.
*> 17/03/18 vbc - .24 Added test for type = 4 (proformas) In Update-Stock-n-Audit
*>                    as we do not want to update stock-held or do audit until
*>                    It Is amended to a receipt or a Invoice. Matches sl920.
*> 19/03/18 vbc - .25 Pre-rewrite of update stock-adds/deducts & stock-TD-adds/deds.
*>                    Similar block must be In sl920 and sl940. Copy block to sl940
*> 21/04/18 vbc - .26 Updated to support swapout of screen data when F1 Is pressed.
*>                     a little experimental.
*>                    With chg to wsfnctn set path of current dir so can del temp
*>                    screen save file. NOT YET CODED IN and NOT added to sl920.
*>                .27 No Idea!
*> 27/01/23 vbc - .28 For SL006 accepts moved loc to 45.
*>
*>                    Just above Process-Stock-Record the multi copy of code
*>                    Is abbreviated as Indexed reads etc for stock or abbrev
*>                    key can be In a simpler code block now with orig rem.d out
*>                    ALSO there might be an Issue at Get-Prod-Test If screen
*>                     Is longer than 24 - TEST THIS. <<<<<<
*>
*> 10/12/22 vbc   .29 Added para after some sections 4 GC 3.2 warning msgs.
*> 17/02/23 vbc   .30 Force VAT rate to S = Standard as default - user can chng.
*> 09/05/23 vbc - .31 Near end of type-Input changed 2 None Zero or ESC To Abort
*>                    and next line to start at 40 Instead of 60.
*> 20/05/23 vbc -     Change WS-Show-Delivery from pic 9 to X.
*> 06/08/23 vbc   .32 Better support for service Items set default qty = 1.
*>                    no further checking but check for audit as well.
*>                    Test for Invoice type < 1 on Invoice Input.
*> 10/03/24 vbc - .33 When writing out Invoices If status = dup key read system
*>                    rec & get next-invoice, use It and add 1 then rewrite rec.
*>                    Above will also happen If using a Del Inv. no. as It still
*>                    has to get done. Yes this progran reads and rewrite system
*>                    rec.  Need to do same In PL folio creation.  NEEDS TESTING
*> 17/03/24 vbc - .34 Add support for BO (back orders) providing the param rec
*>                    field SL-BO-Flag = "Y" and only applies to SL Customers
*>                    with field Sales-Partial-Ship-Flag = "Y". [Also for sl920
*>                    no kill it ].
*>                    All BO processing here, st020, sl970 Only use File
*>                    processing and not FH / DAL as only the 3 programs involved.
*>                    Also BO processing is expected to be temporary in nature.
*>
*>                    Added new file bostkitm to process BO records. [zz120]
*>                    SL192 should be using SL186 - changed and 192 removed.
*>                    If stock-held = zero & BO not zero use zero for Invoice-no
*>                    Stock linked MUST be "Y" for BO processing.
*>                    Also see WS-BO-Stocked
*>                    At start of program run BO file processing if and newly
*>                    arrived stock
*>                    Remove all direct file processing using open,close,
*>                    read etc. NEEDS A CLOSE EXAMININATION.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/04/24 vbc   .35 Fix missing code for dealing with BO processing where
*>                    stock < than needed so needs a new BO record AFTER old
*>                    deleted. Using a serial no after the cust-itm fields to
*>                    deal with it allows for up to 10 additions and traps if >
*>                    10 with err msg Should !, never happen.
*> 23/04/24 vbc   .36 set I = 1 if zero for get-inv-1 & 2 as runtime test shows
*>                    it as 0. why has this never shown up before in normal
*>                    running although possibly as a result of using -D -G for
*>                    the compile ?
*>                    In Confirmation remark out add 1 to next-invoice
*> 25/04/24 vbc - .37 Save and then restore Pass-Value before read and rewrite
*>                    of system rec.
*>                    Clean up some of these remarks as some went over cc80.
*>                .38 Clear down desc in Data-2 if Qty zero and BO active` where
*>                    a return to get product happens.
*> 29/04/24 vbc   .39 Chg BO head data from color 1 to 3 - I can't read them.
*>                    Ditto for Line # change all to 2 (green) as 1 was blue.
*>                    For BO display cust address etc.
*> 07/06/24 vbc   .40 Using WS-22-Lines and for accept-body - ws-22-lines
*>                    instead of 23 so screen size should be > 26 set by user.
*>                    BO code changes & support sort by date if stock > BO
*>                    orders AND only one stock item is Back Ordered.
*> 20/08/24 vbc       Dry testing BO coding.
*> 11/09/24 vbc   .41 Support for VAT-Rates 4 & 5 + extra coding for BO processing.
*> 14/09/24 vbc       Finish off coding for BO to remove invoiced BO records
*>                    currently remarked out to save reinputting test data
*> 14/09/24 vbc       More new error SL msgs added 201 - 220. Add to manuals
*> 12/12/24 vbc       Extra code in BO proc. for Qty = zero chk for "D" then
*>                    Delete BO record.
*> 16/12/24 vbc   .42 Display heads before showing BO info.
*>                .43 In BO I not reset to 1 after screen display perform.
*> 05/01/25 vbc   .44 Add in missing read. rewrite param file upding next-invoice
*> 17/02/25 vbc   .45 Init Invoice-Header and details before running BO processing
*>                    and when starting to accept data for a new BO rec.
*> 21/08/25 vbc - .46 On Get-Vat-Code (level-2) force upper csae on accept
*>                    Level 2 data only.
*> 25/08/25 vbc   .47 On line totals line # missing.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>****** MORE NOTES ************
*>
*>>>>>>>>> ??? >>     For kbrd keys F2, 3, 5, 6 during stock data entry
*>                    In Bypass-Product-Space-Tests at  Search on Desc
*>                    there are three code lines to display and accept
*>                    a return on line 24 used for TESTING ONLY.
*>  >>->>>>           SO -> REMOVE AFTER TESTING <-  VINCENT!!!!
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> These files and programs Is part of the Applewood Computers Accounting
*> System and Is copyright (c) Vincent B Coen. 1976-2026 and later.
*>
*> This program Is now free software; you can redistribute It and/or modify It
*> under the terms of the GNU General Public License as published by the
*> Free Software Foundation; version 3 and later as revised for personal
*> usage only and that Includes for use within a business but without
*> repackaging or for Resale In any way.
*>
*> Persons Interested In repackaging, redevelopment for the purpose of resale or
*> distribution In a rental mode must get In touch with the copyright holder
*> with your commercial plans and proposals before hand.
*>
*> ACAS Is distributed In the hope that It will be useful, but WITHOUT
*> ANY WARRANTY; without even the Implied warranty of MERCHANTABILITY or
*> FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
*> for more details. If It breaks, you own both pieces but I will endeavour
*> to fix It, providing you tell me about the problem.
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
 Input-output            section.
*>------------------------------
*>
 file-control.
*>------------
*>
 copy "selboitm.cob".    *> NOT using FH or DAL modules at all.
*>
 data                    division.
*>===============================
*>
 file section.
*>------------
*>
  *> This MUST be same content / size as fdboitm.cob and wsboitm.cob, i.e., 72 bytes.
 copy "fdboitm.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL910 (3.3.00)".
 77  Exception-Msg       pic x(25) value spaces.
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
*> REMARK OUT, ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
*>     03  System-Record          pic x.  *> added 10/03/24
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
*>     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
*>     03  WS-Invoice-Record      pic x.
*>     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  WS-data.
     03  test-product.
         05  filler      pic x.
             88  Sil-comment             value "/".
         05  filler      pic x(12).
     03  WS-Pass-Value   pic 9.
     03  menu-reply      pic 9.
     03  WS-reply        pic x.
     03  C-Check         pic 9.
         88  c-exists                    value  1.
     03  WS-delinv       pic 9           value zero.
         88  del-exists                  value 1.
     03  Address-A       pic x(96).
     03  address-line.
         05 add-line1    pic x(15).
         05 add-line2    pic x(21).
     03  WS-named        pic x           value " ".
     03  WS-dash         pic x(80)       value all "-".
     03  work-1          pic 9(7)v99.
     03  work-n          pic 9(7)v99.
     03  work-d          pic 9(7)v99.
     03  Display-8       pic z(5)9.99.
     03  Display-9       pic z(6)9.99.
     03  Vat-Code-X.                           *> this for S, R, Z = Std,Reduced,Zero
         05  Vat-Code    pic 9.                *> 18/01/17
     03  I               pic 99.
     03  J               pic 99.
     03  K               pic 99.
     03  M               pic 99.
     03  Z               pic 99.
     03  escape-Code     pic x.
     03  new-screen      pic 9(8).
     03  altypes         pic x(60)
          value "Receipt <<<    Account <<<    Credit Note <<<Pro-Forma <<<".
     03  filler redefines altypes.
         05 D-Types      pic x(15) occurs 4.
     03  WS-VAT-Rate     pic 99v99.
     03  WS-PA           pic xx.
     03  WS-product      pic x(13).
     03  WS-Temp-Stock-Key                    value spaces.
         05  WS-Abrev-Stock
                         pic x(7).
         05  WS-Stock-No-Long
                         pic x(6).
     03  WS-Temp-Invoice pic 9(8).
     03  WS-Temp-Cust    pic x(7)             value spaces. *> Used for BO processing zz200
     03  WS-BO-Stk-Item-Cnt
                         pic 9(4)             value zero. *> Count of # of items on BO now in stock
     03  WS-Tmp-BO-Price pic z(6)9.99.
     03  WS-Tmp-Stk-Price
                         pic z(6)9.99.
     03  WS-BO-Default-Post
                         pic 99.99            value zero.
     03  WS-Description  pic x(32).
     03  WS-Qty          pic 9(5).
     03  WS-Net          pic 9(7)v99.
     03  WS-VAT          pic 9(7)v99.
     03  WS-Unit         pic 9(7)v99.
     03  WS-CR           pic 9(8).
     03  WS-Dayes        pic 99.
     03  WS-Inv-Month.
         05  WS-Inv-Mth  pic 99.
     03  WS-Show-Delivery pic x.
     03  WS-Using-Del-Inv-No pic x       value space.
     03  WS-SL-BO-Flag   pic x.
         88  WS-BO-Used                  value "Y".
     03  WS-BO-Can-Be-Used pic x.
         88  WS-BO-Usable                value "Y".
*>  NOT CURRENTLY USED
     03  WS-BO-Stocked   pic x           value "N".
         88  WS-BO-Stock-Avail           value "Y".  *> ONLY If BO-Stk file has any recs with BO-Stk-Arrived-Flag = "Y"
*> NOT YET USED
     03  WS-BO-Processing pic x          value space.
     03  WS-BO-Date-Order-Processing
                         pic x           value space.
         88  WS-BO-Process-By-Date       value "Y".   *> stock qty < Back Orders.
     03  WS-BO-Date-Cnt  pic 999         value zero.
     03  WS-Display6-1   pic z(5)9.
     03  WS-Display6-2   pic z(5)9.
     03  WS-Display3-1   pic zz9.                     *> used in zz200 BO processing
     03  WS-Display3-2   pic zz9.                     *> used in zz200 BO processing
     03  WS-Display2-2   pic z9.
*>
*> Above also needs SL-BO-Flag = Y (Sales-BO-Set) for Invoice usage.
*>
     03  WS-env-lines    pic 999         value zero.
     03  WS-lines        binary-char unsigned value zero.
     03  WS-accept-body  binary-char unsigned value 8.         *> set for 24 line screen (-1)
     03  WS-22-lines     binary-char unsigned value zero.
     03  WS-23-lines     binary-char unsigned value zero.
*>
*> Table holds BO records that have Arrived = "Y" with Quantities on order
*>  (accumulated for all orders for specific item) and stock held
*>
 01  Item-Table.
     03  WS-Item-Table-Cnt        pic 9(4)    value zero.
     03  WS-Item-Table-Used       pic 9(4)    value zero.
     03  WS-Item-Table-Size       pic 999     value X-Itm-Table-Size.
     03  WS-Item-Table.
         05  WS-Items                  occurs X-Itm-Table-Size.   *> MUST be same as WS-Item-Table-Size
             07  WS-Item-No       pic x(13).
             07  WS-Date-Flag     pic x.
                 88  WS-Date-Mode            value "Y".
             07  WS-Stock-Held    pic 9(6)  comp.
             07  WS-Total-Ordered pic 9(6)  comp.
*>
*> Holds all valid BO records containing Arrived-Flag = "Y"
*>
 01  BO-Table.
     03  BO-Table-Size            pic 9(4)    value X-BO-Table-Size.  *> This MUST be same as the occurs below.
     03  BO-Table-Used            pic 9(4)    value zero. *> Table active size
     03  BO-Table-Cnt             pic 9(4)    value zero. *> Table position #
*>
     03  BOT-All-Records.  *> This MUST be same content / size as fdboitm.cob and wsboitm.cob, i.e., 72 bytes.
         05  BOT-Record                occurs X-BO-Table-Size.  *> All recs are 72 chars so all start on word boundary
             07  BOT-Cust-Itm-No.                   *> Primary Key
                 09  BOT-Stk-Cust-No  pic x(7).     *> Alt key 2
                 09  BOT-Stk-Item-No  pic x(13).    *> Alt Key 2
                 09  BOT-Serial       pic 99.
             07  BOT-Stk-PO           pic x(10).
             07  BOT-Stk-Ref          pic x(10).
             07  BOT-Stk-Orig-Inv-No  pic 9(8).
             07  BOT-Stk-BO-Qty       pic 9(6).     *> 56
             07  BOT-Stk-BO-Arr-Date  binary-long.
             07  BOT-Stk-Order-Date   binary-long.  *> 64
             07  BOT-Stk-Price        pic 9(7)v99 comp-3.  *> 69
             07  BOT-Stk-Arrived-Flag pic x.
             07  BOT-Stk-Inv-Type     pic 9.
             07  filler               pic x.
*>
*> Records invoiced (transactions) for a given invoice # then cleared down for the next BOT record/s
*>
 01  BO-Invoiced-Table.
     03  BO-Invoiced-Size             pic 99      value X-BO-Delete-Size. *> This MUST be same as the occurs below.
     03  BO-Invoiced-Used             pic 99      value zero.
     03  BO-Invoiced-Cnt              pic 99      value zero.
     03  BO-Invoiced-All-Records.
         05  BO-Invoiced-Record        occurs X-BO-Delete-Size.  *> preset as 50
             07  BO-Invoiced-Cust-Item-No
                                      pic X(22).
*>
*> The following for GC and screen NOT IN USE with code rem;d out as not needed.
*>
 01  wScreenName             pic x(256).
 01  wInt                    binary-long.
*>
*> Date variables for processing
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
*> Used to test if a file exists (only if files are processed against RDBMS
*>  tables
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
 01  Error-Messages.
*> System Wide
     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
     03  SL006          pic x(43) value "SL006 Note Details & Hit Return to continue".
*> Module specific
     03  SL180          pic x(34) value "SL180 Err on Invoice Rec. write : ".
     03  SL181          pic x(46) value "SL181 Invoice To Credit Does Not Exist On OTM3".
     03  SL182          pic x(31) value "SL182 Invoice To Credit Is Paid".
     03  SL183          pic x(42) value "SL183 Invoice To Credit Has Query Flag Set".
     03  SL184          pic x(75) value "SL184 You Can Only Credit Invoices. Not Receipts, Credit Notes Or Proformas".
     03  SL185          pic x(56) value "SL185 Credit of Prompt Pay/Late Charge will be Automatic".
     03  SL186          pic x(30) value "SL186 P.A. Code Does Not Exist".
     03  SL190          pic x(35) value "SL190 Error on Writing Audit record".
     03  SL191          pic x(33) value "SL191 Error on Stock rec. Rewrite".
*>     03  SL192          pic x(06) value "SL192 ".
     03  SL193          pic x(65) value "SL193 You Can Only Credit An Invoice With The Same Account Number".
     03  SL194          pic x(19) value "SL194 Stock Read : ".
     03  SL195          pic x(22) value "SL195 Stock Rewrite : ".
     03  SL196          pic x(22) value "SL196 Record Not found".
     03  SL201          pic x(38) value "SL201 Customer BO (Back Order) Not Set".
     03  SL202          pic x(54) value "SL202 Creating BO rec & Changed Qty to held on Invoice".
     03  SL203          pic x(29) value "SL203 Err on Bo-Rec. Write : ".
*> sl204 not used In 910.
     03  SL205          pic x(41) value "SL205 Using Stock Held for quantity order".
     03  SL206          pic x(50) value "SL206 Computation overflow - Qty or cost too large".
     03  SL207          pic x(54) value "SL207 BO Table Exceeded - Increase and recompile sl910".
     03  SL208          pic x(42) value "SL208 Aborting BO Invoice build processing".
     03  SL209          pic x(38) value "SL209 BO Price not same as Stock-Price".
     03  SL210          pic x(43) value "SL210 Price to use ? B (BO) or S (Stock) - ".
     03  SL211          pic x(41) value "SL211 No such Customer - BO entry ignored".
     03  SL212          pic x(49) value "SL212 WARNING BO records for customer are deleted".
     03  SL213          pic x(57) value "SL213 BO Item Table Exceeded - Increase & recompile sl910".
     03  SL214          pic x(53) value "Process Back Orders as there are nnn to Invoice ? [ ]". *> nn = cc34
     03  SL215          pic x(46) value "Would you like to see a list of BO items ? [ ]".
     03  SL216          pic x(65) value "There are nnn / nnn items that need to be processed in DATE order".
     03  SL217          pic x(69) value "Do you wish to force processing in Customer / item order Only (Y/N) ?".
     03  SL218          pic x(63) value "SL218 BO Invoiced table exceeded - Increase and recompile sl910".
     03  SL219          pic x(36) value "SL219 Delete failed for BO Record - ".
     03  SL220          pic x(73) value "SL220 Quantity zero - Select D = Delete BO Rec, or S = Skip this time [ ]".
     03  SL221          pic x(66) value "SL221 Entering D, will delete the BO record so check you want this".
*>
*> 01  Error-Code         pic 999   value zero.   *> NOT used.
*>
*> Copy books
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
 copy "slwsinv.cob"  replacing Invoice-Line by Invoice-Lines. *> Dup name uses 40 lines In Bodies
 copy "slwsinv2.cob".
*>
 01  WS-Invoice-Record  redefines Invoice-Record *>  Sinle line
                                pic x(137).
 copy "slwsoi3.cob".
 copy "wsanal.cob".
 copy "wsaudit.cob".
 copy "wsdel.cob".
 copy "wsdnos.cob".
 copy "wssl.cob".
 copy "wsstock.cob".     *> 3.02
*>
  *> This MUST be same content / size as fdboitm.cob and BOT Table, i.e., 72 bytes.
*> copy "wsboitm.cob".  *> MIGHT BE NEEDED for BO processing ??? IS IT ? - NO <<
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
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
 01  to-day              pic x(10).
*>
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 Init01 section.
*>*************
*>
     accept   WS-env-lines from lines.
     If       WS-env-lines < 24
              move  24 to WS-env-lines WS-lines
     else
              move  WS-env-lines   to WS-lines
     end-if
     subtract 1 from WS-lines giving WS-23-lines.
     subtract 2 from WS-lines giving WS-22-lines.
     subtract 15 from WS-22-Lines giving WS-Accept-Body.	*> gives no. of Invoice Item lines
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     perform  zz070-Convert-Date.   *> WS-date now local disp date
     move     1 to File-Key-No.
*>
*>  Set up delete file for screen save/restore. THIS only works for *nix not Windows
*>   so will need a replacement routines BUT this is not used at this time.
*>
     move     spaces to Path-Work.
     string   ACAS-PAth       delimited by space
              "sl-temp.scr"   delimited by size
                                 Into Path-Work.
*>
*>  Here Is the code for It when ready to cut/paste In.
*>   BUT only for sl910 not amend sl920.
*>
*> Experimental code here
*>
 *>    If       Cob-Crt-Status = Cob-Scr-F3
 *>             move     z"sl-temp.scr"  to wScreenName
 *>             call     "scr_dump"    using wScreenName returning wInt
 *>             perform  abc
 *>             call     "scr_restore" using wScreenName returning wInt
 *>             call     "CBL_DELETE_FILE" using Path-Work
 *>             go to xxx.

*>
*>  Open files and check & setup If we have any deleted Invoices
*>
     perform  Program-Start.
     If       sl-own-nos = "Y"
              move zero to WS-delinv.
*>
*> Process BO records if exists other wise normal Invoice processing
*>   but first do display head
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Invoicing Data Entry" at 0132           with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
     move     zero to Return-Code.
     Initialize
              SInvoice-Header
              SInvoice-Bodies.
*>
     perform  zz200-Build-From-BO.  *> THIS NEEDS TO BE TESTED <<<<<< >>  STILL IN TEST
     if       Return-Code > 3       *> test for BO table exceeded so EOJ
              go to Menu-Exit.
*>
 Main.
     Initialize
              SInvoice-Header.
     perform  Invoice-Details.
*>
     If       Z not = zero
       or     escape-Code = "Q"
              go to  Menu-Exit.
*>
     move     16  to  lin.
     move     1 to cole.
     display  " " at curs with erase eos.
*>
 Data-Input.
     Initialize
              SInvoice-Bodies.
*>
     move     zero to  I.
     If       I-level-1
              perform  Inv-Level-1
     else
              perform  Inv-Level-2.
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to main.
*>
     If       I not = 1
              perform End-Totals.
*>
 More-Data.
     display "Enter Further Invoices? (Y/N) [Y] " at line WS-lines col 29 with foreground-color 3.
     move     zero to Cob-Crt-Status.
     move     "Y" to WS-reply.
     accept   WS-reply at line WS-lines col 60  with foreground-color 6 update.
     move     function upper-case (WS-reply) to WS-reply.
*>
     display  " " at line WS-lines col 01 with erase eol.
*>
     If       WS-reply = "Y"
              go to main.
     If       WS-reply not = "N"
              go to More-Data.
*>
 Menu-Exit.			*> Moved from Program-Start, silly place to have It
     perform  zz080-Close-All-Files
     exit     program.
*>
*>****************************************************************
*>                 P R O C E D U R E S                           *
*>****************************************************************
*>
 Running-Totals section.
*>=====================
*>
     display  I at 1223 with foreground-color 3.
     move     zero  to  sih-Net
                        sih-VAT.
*>
     perform  varying K from 1 by 1 until K  >  I
              add Sil-Net (k) to sih-Net
              add Sil-VAT (k) to sih-VAT
     end-perform
*>
     move     sih-Net  to  Display-9.
     If       I-level-1
              display Display-9 at 1237 with foreground-color 3.
*>
     move     sih-VAT  to  Display-9.
     If       I-level-1
              display Display-9 at 1255 with foreground-color 3.
*>
     add      sih-Net  sih-VAT  giving  Display-9.
*>
     If       I-level-1
              display Display-9 at 1268 with foreground-color 3
     else
              display Display-9 at 1270 with foreground-color 3.
*>
 Main-Exit.
     exit     section.
*>
 Write-Details section.
*>====================
*>
     add      1  to  J.
     move     sih-invoice  to Sil-invoice (J).
     move     J            to Sil-line (J).
     move     sih-type     to Sil-type (J).
     move     Invoice-lines (J)  to  WS-Invoice-Record.  *> was line
     perform  Invoice-Write.
     If       fs-reply not = zero
              perform Eval-Status
              display sl180         at line WS-23-lines col 1 with erase eol foreground-color 4
              display fs-reply      at line WS-23-lines col 36 with foreground-color 3
              display exception-msg at line WS-23-lines col 39 with foreground-color 3
              display Invoice-key   at line WS-23-lines col 64 with foreground-color 3
              display sl006         at line WS-lines col 01 with foreground-color 3
              accept  WS-reply at line WS-lines col 44
              display " " at line WS-23-lines col 1 with erase eos
     end-if
*>
*> Now delete the BO record as completed as invoice is saved 12/04/24
*>   we can have fails on delete and that is OK
*>
     if       BO-Table-Cnt not = zero and
              WS-BO-Processing = "Y"
              move     Sih-Customer    to BO-Stk-Cust-No
              move     Sil-Product (J) to BO-Stk-Item-No
              delete   BO-Stk-Itm-File record.
*>
     perform  Update-Stock-n-Audit.
*>
 Main-Exit.
     exit     section.
*>
 Update-Stock-n-Audit section.
*>===========================
*>
*> Only process If linked to Stock Control and not proforma
*>  This section only creates an Audit record and updates
*>   Stock record quantity held (Stock-Held) and Stock-Value
*>
*>  ALSO UPDATE THE STOCK REC HISTORY CURRENT PERIOD AND BY MONTH ?.
*>
     If       SL-Stock-Link not = "Y"
              go to Update-Stock-Exit.
     If       Sih-Type   = 4
              go to Update-Stock-Exit.
*>
*> Normal for Receipts(1) and Invoices (2) but reverse process for
*>      Credit Notes (3) AND Proformas are Ignored.
*>
     Initialize WS-Stock-Audit-Record.
     move     3                   to Audit-Type.
     move     Sih-Invoice         to Audit-Invoice-PO.
     move     WS-Date             to Audit-Process-Date.
     move     Sil-Product (J)     to Audit-Stock-Key
                                     WS-Temp-Stock-Key.
     move     Sil-Description (J) to Audit-Desc.
     move     Sil-Qty (J)         to Audit-Transaction-Qty.
     move     zero                to Audit-Unit-Cost.
     If       Sil-Type (J) = 3
              move 5      to Audit-Type
              move 1      to Audit-Reverse-Transaction
              move Sih-cr to Audit-Cr-for-Invoice
     else
              move zero to Audit-Reverse-Transaction
     end-if
     move     Stk-Audit-No        to Audit-No.
*>
*> Get the stock record
*>
     If       WS-Stock-No-Long = spaces
              move WS-Abrev-Stock to WS-Stock-Abrev-Key
              move  2 to File-Key-No
              perform Stock-Read-Indexed      *> read Stock-File record key WS-Stock-Abrev-Key Invalid key
              If   FS-Reply = 21
                   move zero to Stock-Cost
                   move spaces to WS-Stock-Key
              end-if
     else
              move WS-Temp-Stock-Key to WS-Stock-Key
              move  1 to File-Key-No
              perform Stock-Read-Indexed    *> read Stock-File key WS-Stock-Key Invalid key
              If   FS-Reply = 21
                   move zero to Stock-Cost
                   move spaces to WS-Stock-Key
              end-if
     end-if
*>
*> As stock Items are checked this should not happen
*>     but It Is a multi user system
*>
     If       fs-reply not = zero
              perform Eval-Status
              display SL194           at line WS-23-lines col 1 with erase eol foreground-color 4
              display fs-reply        at line WS-23-lines col 16 with foreground-color 3
              display exception-msg   at line WS-23-lines col 19 with foreground-color 3
              display WS-Stock-Key       at 2064 with foreground-color 3
              display sl006           at line WS-lines col 01 with foreground-color 3
              accept  WS-reply        at line WS-lines col 44
              display " "             at line WS-23-lines col 1 with erase eos
     end-if
*>
*> If we have great, but If not Stock-Cost Is zero which helps It
*>          show up In proof reports (Sil-type same as sih-type so use later - less ram)
*>
     If       WS-Stock-Key not = spaces		*> we have a stock rec.
              If       Sih-Type = 1 or = 2
                 and   Stock-Services-Flag not = "Y"
                       compute  Audit-Stock-Value-Change = Audit-Transaction-Qty
                                    * Stock-Cost * -1
                       subtract Audit-Transaction-Qty from Stock-Held
              else
               If      Sih-Type = 3		*> Credit note
                 and   Stock-Services-Flag not = "Y"
                       compute  Audit-Stock-Value-Change = Audit-Transaction-Qty
                                    * Stock-Cost
                       add Audit-Transaction-Qty to Stock-Held
               end-if
              end-if
*>
*> Should NOT happen as tested In data entry
*>
              If       Stock-Held < zero
                 and   Stock-Services-Flag not = "Y"
                       multiply -1 by Stock-Held
                       add Stock-Held to Stock-Pre-Sales
                       move zero to Stock-Held
              end-if
              If       Stock-Held > zero
                 and   Stock-Services-Flag not = "Y"
                       multiply Stock-Held by Stock-Cost giving Stock-Value
              else
                       move zero to Stock-Value
              end-if
*>
*>    Similar for sl920 (amend) and sl940 (Delete) Invoices but reversed.
*>
*> Update record period and month In year totals but check that WS-Inv-Mth Is valid.
*>    [ All values positive ] Note that stock fields are not signed and a credit
*>                            could be different month - WIP stock Is NOT sold!
*>
              If       WS-Inv-Mth not < 1 or > 12
                If     Sih-Type = 1 or 2                    *> Invoice and Recepts
                       add Audit-Transaction-Qty to Stock-Deducts
                       add Audit-Transaction-Qty to Stock-TD-Deds (WS-Inv-Mth)
                else
                 If    Sih-Type = 3                         *> Credit Notes
                       add Audit-Transaction-Qty to Stock-Adds
                       add Audit-Transaction-Qty to Stock-TD-Adds (WS-Inv-Mth)
                 end-if
                end-if
              end-if
*>
              move 1 to File-Key-No
              perform  Stock-Rewrite
              If       FS-Reply = 21
                       display SL191    at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
                       display fs-reply at line WS-23-lines col 38 with foreground-color 2 highlight
                       display SL006    at line WS-lines col 1
                       accept WS-reply  at line WS-lines col 45
              end-if
              If       fs-reply not = zero
                       perform Eval-Status
                       display SL195         at line WS-23-lines col 1 with erase eol foreground-color 4
                       display fs-reply      at line WS-23-lines col 22 with foreground-color 3
                       display exception-msg at line WS-23-lines col 25 with foreground-color 3
                       display WS-Stock-Key  at 2064 with foreground-color 3
                       display sl006         at line WS-lines col 01 with foreground-color 3
                       accept  WS-reply      at line WS-lines col 44
                       display " "           at line WS-23-lines col 1 with erase eos
              end-if
     end-if
*>
     If       Stk-Audit-Used = 1
              move zero to Stk-Activity-Rep-Run	   *> Need to run audit report
              perform  Stock-Audit-Write
              If       fs-reply not = zero
                       perform Eval-Status
                       display SL190         at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
                       display fs-reply      at line WS-23-lines col 38 with foreground-color 2 highlight
                       display exception-msg at line WS-23-lines col 41 with foreground-color 3
                       display SL006         at line WS-lines col 1
                       accept WS-reply       at line WS-lines col 45
              end-if
     end-if.
*>
 Update-Stock-Exit.
     exit     section.
*>
 Eval-Status  section.
*>===================
*>
     move     spaces to exception-msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by exception-msg.
*>
 Main-Exit.
     exit     section.
*>
 comm-routines section.
*>********************
*>
 Accept-Money6a.
     move     zero to WS-poundsd6 WS-penced6 amt-ok6.
*>
 Accept-Money6b.
     display  WS-amount-screen-display6 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs   with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 Accept-Money6c.
     move     amt-wk-pence6 to WS-pence6.
     move     amt-wk-pds6   to WS-pound6.
     display  WS-amount-screen-display6 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs   with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 Accept-Money7a.
     move     zero to WS-poundsd7 WS-penced7 amt-ok7.
*>
 Accept-Money7b.
     display  WS-amount-screen-display7 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept7  at curs   with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 Accept-Money7c.
     move     amt-wk-pence7 to WS-pence7.
     move     amt-wk-pds7 to WS-pound7.
     display  WS-amount-screen-display7 at curs with foreground-color 3.
     accept   WS-amount-screen-accept7  at curs  with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 comm-exit.
     exit     section.
*>
 Inv-Level-1  section.
*>===================
*>
*> No one should be using this, so consider scrapping and forcing Invoicer = 2 etc
*>
     display  WS-dash        at 1101 with foreground-color 2.
     display  "Level 1"      at 1201 with foreground-color 2.
     display  "Line - "      at 1216 with foreground-color 2.
     display  "[          ]" at 1236 with foreground-color 2.
     display  "[          ]" at 1254 with foreground-color 2.
     display  "[          ]" at 1267 with foreground-color 2.
     display  "Code"         at 1405 with foreground-color 2.
     display  "<---Net---->  Vat   Vat Amount  Gross Amount" at 1436 with foreground-color 2.
*>
 Loop.
     perform  varying lin from 16 by 1 until lin not < WS-23-lines
              add      1  to  I
              move     1 to cole
              display  "(" at curs with erase eol foreground-color 2
              move     2 to cole
              display  I at curs with foreground-color 2
              move     4 to cole
              display  ") [  ]" at curs with foreground-color 2
              move     36 to cole
              display  "[          ] [ ]   {         } (" at curs with foreground-color 2
              move     78 to cole
              display  ")" at curs with foreground-color 2
     end-perform
*>
*> I = no. lines on screen for Items, then less 7 (24 line screen)
*>      why this way ,  no Idea as against move 1 to I ?????
*>
*>     subtract 16 from WS-23-lines giving m.       *> or move 1 to I
     subtract WS-Accept-Body  from  I.             *> was M from I
     move     1 to J.
     display  I at 1223 with foreground-color 3.
     move     zero to Cob-Crt-Status.
     perform  Get-Data-1.
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to Main-Exit.
*>
     If       new-screen = 1
              go to Loop.
*>
     If       Sil-Description (I) not = spaces
       and    I not = 40
              go to Loop.
*>
 Main-Exit.
     exit     section.
*>
 Get-Data-1   section.
*>===================
*>
*> No one should be using this consider scrapping and forcing Invoicer = 2 etc
*>
 Get-Data-1-Main.
     add      J  15  giving  lin.
*>
     If       lin  >  WS-23-lines
              subtract 1 from I
              move 1 to new-screen
              go to  Main-Exit.
*>
     move     zero to new-screen.
*>
 Get-Code.
     If       I  >  1
       and    Sil-PA (I) = spaces
              move  Sil-PA (I - 1)  to  Sil-PA (I).
*>
     if       I = zero
              move  1 to I.
     move     Sil-PA (I) to WS-PA.
     move     7 to cole.
     display  WS-PA at curs with foreground-color 3.
     accept   WS-PA at curs with foreground-color 3 update.
     move     WS-PA to Sil-PA (I) pa-group.
     move     spaces  to  Sil-Description (I).
*>
     If       WS-PA = spaces
              go to  Main-Exit.
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to Main-Exit.
*>
     If       WS-PA = "<<"
        and   I = 1
              go to Get-Code.
*>
     If       WS-PA = "<<"
              subtract  1  from  lin
              If    lin  >  15
                    subtract  1  from  I
                    subtract 1 from j
                    go to  Get-Code
              else
                    subtract WS-Accept-Body from  I          *> Was 8 Need to follow logic, can we use WS-Accept-Body ??
                    go to  Get-Data-1-Main.
     move     "S" to pa-system.
     move     11 to cole.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     If       FS-Reply = 21
              display SL186 at line WS-23-lines col 1 with foreground-color 4 highlight beep
              go to  Get-Code.
     display  " " at line WS-23-lines col 1 with erase eol.
*>
     display  pa-Desc at curs with foreground-color 3.
     move     pa-Desc  to  Sil-Description (I).
*>
 Get-Net.
     move     37 to cole.
     perform  Accept-Money7a thru Accept-Money7b.
     If       amt-ok7 = zero
              go to Get-Code.
     move     amt-ok7 to Sil-Net (I) WS-Net.
*>
 Get-Vat-Code.
*>
*>  Only using 1st three as last 2 are for local sales tax but not In UK.
*>   NOTE that Is Is not currently programmed for (e.g., last 2).
*>
     move     50 to cole.
     accept   Vat-Code at curs with foreground-color 3 update.
*>
     If       Vat-Code  >  3
              go to  Get-Vat-Code.
*>
     move     Vat-Code  to  Sil-Vat-Code (I).
     If       Vat-Code = zero
              move  zero  to  amt-ok6
       else
              move VAT-Rate (Vat-Code) to WS-VAT-Rate
              compute amt-ok6 rounded =  (WS-Net * WS-VAT-Rate) / 100.
*>
 Get-VAT-Rate.
     move     56 to cole.
     perform  Accept-Money6c.
     move     amt-ok6 to Sil-VAT (I) WS-VAT.
*>
     add      WS-VAT WS-Net giving  Display-9.
     move     68 to cole.
     display  Display-9 at curs with foreground-color 3.
*>
     perform  Running-Totals.
*>
     add      1 to J.
     add      1  to  I.
     go       to Get-Data-1-Main.
*>
 Main-Exit.
     exit     section.
*>
 Inv-Level-2  section.
*>===================
*>
*> This, is the default standard and always used with Stock Control where
*> level 1 does not use it.
*>
     display  WS-dash at 1101 with foreground-color 2.
     If       SL-Stock-Link not = "Y"
              display  "Level 2"      at 1201 with foreground-color 2
     else
              display  "Stock Linked" at 1201 with foreground-color 2.
     display  "Line - "               at 1216 with foreground-color 2.
     display  "Net <          >"      at 1227 with foreground-color 2.
     display  "Vat <          >"      at 1244 with foreground-color 2.
     display  "Invoice <          >"  at 1261 with foreground-color 2.
     If       SL-Stock-Link = "N"		*> No stock then process PA code
              display  "Product    Code <---------Description-------->   Qty   Unit Price  Disc. Vat"
                                     at 1405 with foreground-color 2
     else
              display  "Product     <----------Description--------->    Qty   Unit Price  Disc. Vat"
                                     at 1405 with foreground-color 2.
*>
 loop.
     perform  varying lin from 16 by 1 until lin not < WS-23-lines
              add      1  to  I
              move     1 to cole
              If       SL-Stock-Link = "N"		*> No stock then process PA code
                       display "[             ][  ][" at curs with foreground-color 2 erase eol
                       move    51 to cole
                       display   "][     ][          ][     ][ ]" at curs  with foreground-color 2
              else				*> Ignore PA
                       display "[             ][" at curs with foreground-color 2 erase eol
                       move    49 to cole
                       display "]  [     ][          ][     ][ ]" at curs  with foreground-color 2
              end-if
     end-perform
*>
*> This Is what the Item capture displays look like & 1st Is for non-linked
*>   stock Control:
*>
*>    Product    Code <---------Description-------->   Qty   Unit Price  Disc. Vat
*>[      12 >13 ][2 ][        24 >30                ][  5  ][  9>10    ][  5  ][1]
*> If STOCK LINKED:
*>    Product     <----------Description--------->    Qty   Unit Price  Disc. Vat
*>[      12 >13 ][        24 >32                  ]  [  5  ][  9>10    ][  5  ][1]
*>
*>     subtract 16 from WS-23-lines giving m.  *> or move 1 to I = pos. In line Item table
*>
     subtract WS-Accept-Body from I.                    *> M = WS-accept-body
     move     1  to  J.
*>
     display  I at 1223 with foreground-color 3.
*>
     perform  Get-Data-2.
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to Main-Exit.
*>
     If       new-screen = 1
              go to  loop.
*>
     If       WS-product not = spaces
       and    I not = 40			*> max no. of Items per Invoice
              go to  loop.
*>
 Main-Exit.
     exit     section.
*>
 Get-Data-2   section.
*>===================
*>
*>**********************************************************************
*>  This section will accept Invoice line data If SC (stock control)   *
*>  Is NOT linked In param file. If It Is linked, will only request:   *
*>  Stock code or If entered chars = 7 or less, Abrev code so can      *
*>  search same If using F3 to find 1st then using F2 for next record. *
*>  In place of the return key.                                        *
*>  Also will allow search on description using F6 In stock code entry *
*>  and then will accept a description using F5 to search 1st and for  *
*>  next records.   CHANGE TO SUIT CODE                                *
*>                                                                     *
*>  For Vat Code, will also Accept S(tandard), R(educed) & Z(ero) In   *
*>   place of 1, 2, 3 respectively but will be replaced with 1, 2, 3.  *
*>  Note that codes 4 & 5 are not coded for as 1, 2 & 3 can be used    *
*>  for other taxation classes such as sales tax etc.                  *
*>**********************************************************************
*>
 Get-Data-2-Main.
     add      J  15  giving  lin.
     If       lin  > WS-23-lines - 1
              subtract  1  from  I
              move  1  to  new-screen
              go to  Main-Exit.
*>
     move     zero  to  new-screen.
*>
 Get-Product.
     If       I  >  1
       and    Sil-product (I) = spaces
              move  Sil-product (I - 1) to Sil-product (I).  *> display prev entered code for new line
*>                                                              to save typing
     if       I = zero
              move  1 to I.
     display  I at 1223 with foreground-color 3.             *> disp line # on summary line
     move     2 to cole.
     move     Sil-product (I) to WS-product.
     display  WS-product at curs with foreground-color 3.
     accept   WS-product at curs with foreground-color 3 update.
*>
     move     spaces  to  Sil-Description (I).
*>
*> Process description accept & search via start / read next If F6 detected
*>
     If       Cob-Crt-Status = cob-scr-F6
              go to Bypass-Product-Space-Tests.
*>
     If       WS-product = spaces
              go to Main-Exit.
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to Main-Exit.
*>
 Bypass-Product-Space-Tests.
     move     function upper-case (WS-product) to WS-product.
     move     WS-product to Sil-product (I)
                            test-product
                            WS-Temp-Stock-Key.
*>
     If       Sil-comment
              move zero to WS-Net WS-Unit WS-Qty
              go to  Get-Desc.
*>
     If       WS-product = "<<           "
              subtract  1  from  lin
              go to Get-Prod-Test.
*>
     If       SL-Stock-Link not = "Y"    *> continue with old code to accept all data
              go to Get-Code.
     move     17 to cole.                *> 4 Desc.
*>
*> Search nearest Abrev key and read next ..
*>  When this Is tested we can wrap this and next together
*>    with a F3 test then a If F2 or F3 test
*>
     If       Cob-Crt-Status = cob-scr-F3
 *>
 *> Search Abrev then read next & thereafter F2 until wanted
 *>
              move WS-Abrev-Stock to WS-Stock-Abrev-Key
              move  2 to File-Key-No
              set fn-not-less-than to true
              perform Stock-Start              *> start Stock-File key not < WS-Stock-Abrev-Key Invalid key
              If    FS-Reply = 21
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              perform Stock-Read-Next
              If    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to Sil-product (I)    *> have we the right one?
              display WS-Stock-Desc at curs with foreground-color 3
              go to Get-Product
     end-if
*>
     If       Cob-Crt-Status = cob-scr-F2                *> read next record
              perform Stock-Read-Next
              If    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to Sil-product (I)    *> have we the right one?
              display WS-Stock-Desc at curs with foreground-color 3
              go to Get-Product
     end-if
*>
*> Search on Desc. but has dup keys so disp. Abrev. code
*>    & F5 for next on description
*>  When this Is tested we can wrap this and next together with a
*>      F6 test then a If F5 or F6 test
*>
     If       Cob-Crt-Status = cob-scr-F6
              move    Sil-Description (I) to WS-Description
              accept  WS-Description at curs with foreground-color 3 update
              move WS-Description to WS-Stock-Desc
              move  3 to File-Key-No         *> start Stock-File key not < WS-Stock-Desc Invalid key
              set fn-not-less-than to true
              perform Stock-Start
              If    FS-Reply = 21
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              perform Stock-Read-Next
              If    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to Sil-product (I)    *> Got the right one? Show desc, stock held & retail price
                                      WS-Product
              display WS-Stock-Desc at curs with foreground-color 3 highlight
              move Stock-Held to WS-Qty
              If       Stock-Services-Flag = "Y"
                       move 1 to WS-Qty
              end-if
              display WS-Qty at line lin col 53 with foreground-color 3 highlight
              display "Hit return (for testing)" at 2401  *> TESTING ONLY
              accept WS-reply at 2425            *> TESTING ONLY
              display " " at 2401 with erase eol *> TESTING ONLY
              move Stock-Retail to amt-ok7
              move amt-wk-pds7   to WS-pound7
              move amt-wk-pence7 to WS-pence7
              display WS-amount-screen-display7 at line lin col 60 with foreground-color 3 highlight
              go to Get-Product
     end-if
*>
     If       Cob-Crt-Status = cob-scr-F5      *> Read next on Desc.
              perform Stock-Read-Next
              If    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if
              move WS-Stock-Abrev-Key to Sil-product (I)    *> Got the right one? Show desc, stock held & retail price
                                      WS-Product
              display WS-Stock-Desc at curs with foreground-color 3 highlight
              move Stock-Held to WS-Qty
              If       Stock-Services-Flag = "Y"
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
     If       WS-Stock-No-Long = spaces
              move WS-Abrev-Stock to WS-Stock-Abrev-Key
              move 2 to File-Key-No
     else
              move WS-Temp-Stock-Key to WS-Stock-Key
              move 1 to File-Key-No
     end-if
     perform  Stock-Read-Indexed
     If       FS-Reply = 21 or = 23
              move SL196 to WS-Stock-Desc
              display WS-Stock-Desc at curs with foreground-color 4
              go to Get-Product
     end-if.
*>
 GSS-End.
*> can shorten code now so rem out next block vbc 27/08/17
*>
 *>    else
 *>             perform Stock-Read-Indexed    *> read Stock-File key WS-Stock-Key Invalid key
 *>             If   FS-Reply = 21
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
     move     Stock-SA-Group to WS-PA
                                pa-group
                                Sil-PA (I).
     display  WS-Stock-Desc   at curs with foreground-color 3.
     move     WS-Stock-Desc to WS-Description
                               Sil-Description (I).
     move     Stock-Retail  to amt-ok7.
     move     Stock-Retail  to WS-Unit.
     move     amt-wk-pds7   to WS-pound7.
     move     amt-wk-pence7 to WS-pence7.
     display  WS-amount-screen-display7 at line lin col 60 with foreground-color 3.
     move     Stock-Held to WS-Qty.
     If       Stock-Services-Flag = "Y"
              move 1 to WS-Qty
     end-if
     go       to Get-Qty.          *> Bypass manual Input code as comes from stock record
*>
 Get-Prod-Test.   *> THESE TESTS LOOK WRONG IF SCREEN LONGER THAN 24 LINES <<<<< TEST for this
     If       I = 1
              add 1 to lin
              go to Get-Product.
*>
     If       lin  >  15
              subtract  1  from  I
              subtract  1  from  j
              go to  Get-Product
      else
              subtract WS-Accept-Body from I           *> Instead of 8 can we use WS-Accept-Body ??
              go to  Get-Data-2-Main.
*>
 Get-Code.
     If       I  >  1
       and    Sil-PA (I) = spaces
              move  Sil-PA (I - 1)  to  Sil-PA (I).
*>
     move     Sil-PA (I) to WS-PA.
     move     17 to cole.
     display  WS-PA at curs with foreground-color 3.
     accept   WS-PA at curs with foreground-color 3 update.
*>
     move     spaces  to  Sil-Description (I).
*>
     If       WS-PA = spaces
              go to  Get-Product.
*>
     move     WS-PA to pa-group Sil-PA (I).
     move     "S" to pa-system.
     move     21 to cole.                         *> disp error In desc.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     If       FS-Reply = 21
              display SL186 at curs  with foreground-color 4
              go to  Get-Code.
*>
 Get-Desc.
     If       I  >  1
         and  Sil-Description (I) = spaces
         and  not  Sil-comment
              move  Sil-Description (I - 1) to  Sil-Description (I).
*>
     If       SL-Stock-Link = "Y"
              move 17 to cole
     else
              move 21 to cole.
     move     Sil-Description (I) to WS-Description.
     display  WS-Description at curs with foreground-color 3.
     accept   WS-Description at curs with foreground-color 3 update.
*>
     move     WS-Description to Sil-Description (I).
     If       WS-Description = spaces
              move "B" to escape-Code
     else
              move space to escape-Code.
     If       escape-Code = "B"
         and  Sil-comment
              go to Get-Product.
     If       escape-Code = "B"
              go to  Get-Code.
*>
     If       Sil-comment
              go to  Jump-Totals.
*>
 Get-Qty.
     If       SL-Stock-Link = "N"		*> If It Is shown = current stock
              move     zero to WS-Qty.
     move     53 to cole.
     If       Stock-Services-Flag = "Y"
              move 1 to WS-Qty
     end-if
     display  WS-Qty at curs with foreground-color 3.
     accept   WS-Qty at curs with foreground-color 3 update.
*>
     If       WS-Qty = zero
              go to Get-Desc.
*>
     If       Stock-Services-Flag not = "Y"
       and    WS-BO-Used
       and    Sales-BO-Set
              move  "Y" to WS-BO-Can-Be-Used.  *> Testing use WS-BO-Usable (Y)

     If       SL-Stock-Link = "Y"         *> make sure not selling more stock than held
       and    WS-Qty > Stock-Held
       and    not WS-BO-Usable
              move Stock-Held to WS-Qty   *> max value Is stock held
              display  SL201 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to Get-Qty
     else
              display " " at line WS-23-lines col 1 with erase eol.  *> clear any msg SL201
*>
     If       SL-Stock-Link = "Y"    *> bypass accept unit price
              go to Recomp-Net.
*>
 Get-Unit.
     move     60 to cole.
     perform  Accept-Money7a thru Accept-Money7b.
     If       amt-ok7 = zero
              go to Get-Qty.
     move     amt-ok7 to WS-Unit.
*>
 Recomp-Net.
     If       SL-Stock-Link = "Y"         *> make sure not selling more stock than held - 19/03/24
       and    WS-Qty > Stock-Held
       and    WS-BO-Usable
              If       Stock-Held = zero
                       move     zero to WS-Temp-Invoice
              end-if
              perform  zz120-Build-BO-Record   *> but not for credit notes
              move     Stock-Held to WS-Qty
              display  SL205 at line ws-23-Lines col 1 with foreground-color 4 highlight beep
              If       WS-Qty = zero
                       If       I > zero   *> JIC
                                Initialise Invoice-Lines (I) *> clear down any above entered data for Item line
                                if  I > 1
                                    subtract 1 from I
                                    if  I = zero
                                        move 1 to I
                                    end-if
                                end-if
                       end-if
                       move    15 to cole
                       display "][" at curs with foreground-color 2 erase eol
                       move    49 to cole
                       display "]  [     ][          ][     ][ ]" at curs  with foreground-color 2
                       go to Get-Data-2.
*>
     multiply WS-Qty by  WS-Unit giving  WS-Net
           on size error
              display  "SizER" at curs with blink foreground-color 4
              display  SL206 at line ws-23-Lines col 1 with foreground-color 4 highlight beep
              go to Get-Qty
           not on size error
              display   "     " at curs
              display   " " at line ws-23-Lines col 1 with erase eol.
*>
     move     WS-Net to  Display-9 Sil-Net (I).
     move     WS-Qty to Sil-Qty (I).
     move     WS-Unit to Sil-Unit (I).
     display  Display-9 at 1232 with foreground-color 3.
*>
 Get-Disc.
     move     Sales-Discount  to  WS-discount.
     move     72 to cole.
     move     WS-disc-wka to WS-disca1.
     move     WS-disc-wkb to WS-disca3.
     display  WS-discount-display at curs with foreground-color 3.
     accept   WS-discount-accept  at curs with foreground-color 3 update.
     move     WS-discb1 to WS-disc-wka.
     move     WS-discb3 to WS-disc-wkb.
*>
     move     WS-discount to  work-d Sil-discount (I).
     move     WS-Net to  work-n.
*>
     multiply work-n by work-d giving work-1
     divide   work-1 by 100    giving work-1
*>
     subtract work-1  from  WS-Net.
*>
     move     WS-Net to Sil-Net (I) Display-9.
     display  Display-9 at 1232 with foreground-color 3.
*>
 Get-Vat-Code.
     move     "S" to Vat-Code-X.  *> 17/2/23  for Standard rate
     move     79 to cole.
     display  Vat-Code-X at curs with foreground-color 3.
     accept   Vat-Code-X at curs with foreground-color 3 update UPPER.
*>
*>   Accept S, R and Z replacing with 1, 2 & 3.      Rating   %   - Effective (supposed )
*>
     If       Vat-Code-X = "S"                   *> Standard code 1 (20% - 01/01/17)
              move 1 to Vat-Code
      else
       If     Vat-Code-X = "R"                   *> Reduced  code 2 (05% - 01/01/17)
              move 2 to Vat-Code
        else
         If   Vat-Code-X = "Z"                   *> Zero     code 3 (00% - 01/01/17)
              move 3 to Vat-Code.
*>
     If       Vat-Code < 1 or > 5                *> using 1st three as last 2 are Sales tax, Not used In the UK but USA ?. 11/09/24
              go to  Get-Vat-Code.
*>
     move     Vat-Code  to  SIl-Vat-Code (I).
*>
     If       Vat-Code = zero
              move  zero  to  WS-VAT
     else
              move VAT-Rate (Vat-Code) to WS-VAT-Rate
              compute  WS-VAT rounded = (WS-Net * WS-VAT-Rate) / 100.
*>
     move     WS-VAT to  Display-9
                         SIl-VAT (I).
     display  Display-9 at 1249 with foreground-color 3.
*>
     perform  Running-Totals.
*>
 Jump-Totals.
     add      1  to  J.
     add      1  to  I.
     go       to Get-Data-2-Main.
*>
 Test-For-Read-Stock.
     If       fs-reply not = zero
              perform Eval-Status
              display SL194    at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
              display fs-reply at line WS-23-lines col 21 with foreground-color 2 highlight
              display exception-msg at line WS-23-lines col 24 with foreground-color 3
              display SL006 at line WS-lines col 1
              accept WS-reply at line WS-lines col 45
     end-if.
*>
 Main-Exit.
     exit     section.
*>
 End-Totals   section.
*>==================
*>
 End-Totals-Main.
     move     zero to Cob-Crt-Status.
     perform  Total-Screen.
     If       Cob-Crt-Status = Cob-Scr-Esc
              if       WS-BO-Processing = "Y"  *> THIS MAY NOT APPEAR ????
                       display SL212 at 1501 with foreground-color 4
                                                  highlight BEEP
                                                  erase  eol
              end-if
              go to Main-Exit.
*>
     move     15  to  lin.
     move     1 to cole.
     display  " " at curs with erase eos.
*>
     display  "*********************" at 1660  with foreground-color 2
     display  "*" at 1760 with foreground-color 2
     display  "*" at 1780 with foreground-color 2
     display  "*" at 1860 with foreground-color 2
     display  "*" at 1880 with foreground-color 2
     display  "*" at 1960 with foreground-color 2
     display  "*" at 1980 with foreground-color 2
     display  "*********************" at 2060 with foreground-color 2.
*>
     display  "Invoice Ok to" at 1761 with foreground-color 2.
     If       Pass-Value = 2
              display "Store" at 1775 with foreground-color 2
     else
              display "Print" at 1775 with foreground-color 2.
     display  "(Y/N) ? [Y]" at 1968 with foreground-color 2.
*>
 Confirmation.
     move     "Y"  to   WS-reply.
     accept   WS-reply at 1977 with foreground-color 6 update.
     move     function upper-case (WS-reply) to WS-reply.
*>
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to Main-Exit.
*>
     If       WS-reply = "N"
              go to  End-Totals-Main.
*>
     If       WS-reply not = "Y"
              go to  Confirmation.
*>
     move     "P"  to  sih-status.
     move     space to sih-status-P.
     subtract 1  from  I.
     move     I    to  sih-lines.
*>
     move     SInvoice-Header  to  WS-Invoice-Record.  *> was Invoice-record
*>
 Retry-Write-PInv-Rec.
     perform  Invoice-Write.
     If       FS-Reply = 22       *> Key exists so reread field/record, yes Ignore any Del-inv-nos
              perform  zz100-Read-System-Record
              move     Next-Invoice to Ih-Invoice
                                       Sih-Invoice  *> details recs updated
              add      1 to Next-Invoice
              perform  zz110-Write-System-Record
              go to    Retry-Write-PInv-Rec
     end-if
     If       fs-reply not = zero
              perform Eval-Status
              display sl180         at line WS-23-lines col  1 with erase eol foreground-color 4
              display fs-reply      at line WS-23-lines col 36 with foreground-color 3
              display exception-msg at line WS-23-lines col 39 with foreground-color 3
              display Invoice-key   at line WS-23-lines col 64 with foreground-color 3
              display sl006         at line WS-lines    col  1 with foreground-color 3
              accept  WS-reply      at line WS-lines    col 44
              display " "           at line WS-23-lines col  1 with erase eos.
*>
     move     zero to  J.
     perform  Write-Details  I  times.
*>
*>  Set for sl930   Invoice print
*>
     If       First-SL-Inv = zero
       and    Pass-Value not = 3   *> Batch
              move  sih-invoice to  First-SL-Inv.
*>
     If       del-exists
              perform DelInvNos-Delete.
*>
     If       Pass-Value = 3  *> One off invoice and print
              go to ET-Print.
*>
     move     1 to S-Flag-I.
     move     11  to  lin.
     move     1 to cole.
     display  " " at curs with erase eos.
     go       to Main-Exit.
*>
 ET-Print.
     perform  Invoice-Close.
     perform  OTM3-Close.
*>
     perform  Sales-Close.
     perform  Delivery-Close.
     perform  DelInvNos-Close.
     perform  Analysis-Close.
     If       SL-Stock-Link = "Y"
              perform  Stock-Close
              perform  Stock-Audit-Close
     end-if
*>
*>  Now call print Invoice program as received a Immediate print request
*>
     call     "sl930" using WS-calling-data
                            system-record
                            to-day
                            file-defs.
     exit     program.
*>
 Main-Exit.
     exit     section.
*>
 Total-Screen section.
*>===================
*>
     move     1 to cole.
     move     11 to lin.
     display  " " at curs with erase eos.
     display  WS-dash at 1101 with foreground-color 2.
*>
     If       I-level-1
              move  1  to  menu-reply
     else
              move  2  to  menu-reply.
*>
     display  "Level "   at 1201 with foreground-color 2.
     display  menu-reply at 1207 with foreground-color 2.
     display  "<---Net---->   <---VAT--->" at 1225 with foreground-color 2.
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
     move     sih-Net  to  Display-9.
     display  Display-9 at 1426 with foreground-color 3.
*>
     move     sih-VAT  to  Display-8.
     display  Display-8 at 1441 with foreground-color 3.
*>
     add      sih-Net  sih-VAT  giving  Display-9.
     display  Display-9 at 1455 with foreground-color 3.
*>
 Get-Days.
     move     zero to sih-days sih-carriage.
     If       sih-type = 2
              move sales-credit  to  sih-days
     else If  sih-type = 4
              move pf-retention to sih-days.
     move     sih-days to WS-Dayes.
     If       sih-type not = 2
              display WS-Dayes at 1472 with foreground-color 3
              go to Get-Extra.
*>
     display  WS-Dayes at 1472 with foreground-color 3.
     accept   WS-Dayes at 1472 with foreground-color 3 update.
     move     WS-Dayes to sih-days.
*>
 Get-Extra.
     If       Extra-Type = space
              move zero to sih-extra sih-e-VAT
              go to Get-Carriage.
*>
     If       Extra-Rate not = zero
              compute  sih-extra = (sih-Net * extra-rate) / 100
     else
              move  zero  to  sih-extra.
*>
     move     1526 to curs.
     move     sih-extra to amt-ok7.
     perform  Accept-Money7c.
     move     amt-ok7 to sih-extra.
*>
 Get-Extra-VAT.
     If       sih-extra = zero
              move  zero to  sih-e-VAT
              go to Get-Carriage.
*>
     compute  amt-ok6 = sih-extra  *  VAT-Rate-1  /  100.
*>
     move     1541 to curs.
     perform  Accept-Money6c.
     move     amt-ok6 to sih-e-VAT.
*>
     add      sih-extra  sih-e-VAT  giving  Display-9.
     display  Display-9 at 1555 with foreground-color 3.
*>
     If       discount
         and  sih-extra not = zero
              multiply -1 by sih-extra
              multiply -1 by sih-e-VAT.
*>
 Get-Carriage.
     move     1626 to curs.
     perform  Accept-Money7a thru Accept-Money7b.
     move     amt-ok7 to sih-carriage.
     compute  amt-ok6 rounded = sih-carriage * VAT-Rate-1 / 100.
*>
*> Note that VAT-Rate-1 must be standard rate for p & p
*>
 Get-Carriage-VAT.
     move     1641 to curs.
     perform  Accept-Money6c.
     move     amt-ok6 to sih-c-VAT.
     add      sih-carriage  sih-c-VAT  giving  Display-9.
     display  Display-9 at 1655 with foreground-color 3.
*>
 Get-Deduct-Amt.
     If       WS-named = "A"
        and   oi-Net = sih-Net
        and   oi-VAT = sih-VAT
        and   oi-carriage = sih-carriage
              move "Z" to WS-named.
*>
     If       (sih-type not = 2  and not = 3)       *> Invoices, Credit Notes
          or  not late-charges
          or  WS-named = "Z"
              move zero to sih-deduct-amt sih-deduct-VAT sih-deduct-days
              go to  Main-Exit.
*>
     compute  amt-ok7 =  sih-Net  /  10.
*>
     If       amt-ok7 <  4
              move  4  to  amt-ok7.
*>
     move     1726 to curs.
     perform  Accept-Money7c.
     move     amt-ok7 to sih-deduct-amt.
*>
 Get-Deduct-VAT.
     move     zeros to sih-deduct-VAT.
*>
     add      sih-Net  sih-extra  sih-carriage  sih-deduct-amt giving  Display-9.
     display  Display-9 at 1926 with foreground-color 3.
*>
     add      sih-VAT  sih-e-VAT  sih-c-VAT  sih-deduct-VAT giving  Display-8.
     display  Display-8 at 1941 with foreground-color 3.
*>
     add      sih-Net  sih-extra  sih-carriage  sih-deduct-amt
              sih-VAT  sih-e-VAT  sih-c-VAT  sih-deduct-VAT   giving  Display-9.
     display  Display-9 at 1955 with foreground-color 3.
*>
 Get-Deduct-Days.
     move     sih-days  to  WS-Dayes.
     display  WS-Dayes at 1772 with foreground-color 3.
     accept   WS-Dayes at 1772 with foreground-color 3 update.
     move     WS-Dayes to sih-deduct-days.
*>
 Main-Exit.
     exit     section.
*>
 Invoice-Details section.
*>======================
*>
 Invoice-Details-Main.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Invoicing Data Entry" at 0132           with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
     display  "****************************************" at 0441 with foreground-color 2.
     display  "*Date  [  /  /    ]*                   *" at 0541 with foreground-color 2.
     display  "*A/C Nos  [       ]*Ref    [          ]*" at 0641 with foreground-color 2.
     display  "*Invoice [        ]*Order  [          ]*" at 0741 with foreground-color 2.
     display  "****************************************" at 0841 with foreground-color 2.
     display  "F1 = Setup new Customer; F8 = Only Show delivery details" at 0911 with foreground-color 2.
     display  "Type [ ]  <1> = Receipt; <2> = Account; <3> = Credit Note; <4> = Pro-Forma"
                                                         at 1001  with foreground-color 2.
*>
 Date-Input.
     display  WS-date at 0549 with foreground-color 3.
     accept   WS-date at 0549 with foreground-color 3 update.
*>
     If       Cob-Crt-Status = Cob-Scr-Esc
         or   WS-date = spaces
              move 1 to z
              go to  Main-Exit.
*>
     move     WS-date to WS-test-date.
     perform  zz050-Validate-Date.
     If       u-bin = zero
              go to  Date-Input.
*>
*> Now WS-Inv-Month (as XX) and WS-Inv-Mth (as 99), contains active month for Invoicing
*>  so we will use that for stk totals In month within year.
*>
     move     WS-test-date to WS-date.  *> still need orig. disp date as WS-date now UK
     move     u-bin  to  sih-date.
*>
 Customer-Input.
     move     spaces  to  sih-Customer.
     move     zero to Cob-Crt-Status.
     accept   sih-Customer at 0652 with foreground-color 3 update.
     move     function upper-case (sih-Customer) to sih-Customer.
*>
     If       Cob-Crt-Status = Cob-Scr-F8
              move "Y" to WS-Show-Delivery
     else
              move "N" to WS-Show-Delivery
     end-if.
*>
 Customer-Test.
     If       sih-Customer = "NEW"
         or   Cob-Crt-Status = Cob-Scr-F1
              go to New-Customer.
*>
     If       sih-Customer = spaces
              move  "Q"  to  escape-Code
              go to  Main-Exit.
*>
     move     1  to  C-Check.
     move     sih-Customer  to WS-Sales-Key.
*>
     move     1 to File-Key-No.
     perform  Sales-Read-Indexed.
     If       fs-reply = 21 or = 23
              move  zero  to  C-Check.
*>
     If       not  c-exists
              display  "No such Customer" at 0401 with foreground-color 3
              go to  Customer-Input.
     display  "                " at 0401.
*>
     display  "                        " at 0911.  *> Clear F1 comment Only
*>
     If       sl-own-nos = "Y"
              go to Get-inv.
*>
     move     zeros to Sih-Invoice.
     If       Del-Exists
              perform  Get-a-Deleted-Invoice.
     If       Sih-Invoice = zeros
              perform zz100-Read-System-Record
              move next-invoice  to  sih-invoice
                                     WS-Temp-Invoice
              add  1 to Next-Invoice          *> Remove same code else where <<
              perform zz110-Write-System-Record.
*>
     display  sih-invoice at 0751 with foreground-color 3.
     go       to Jump-1.
*>
 Get-inv.
     accept   sih-invoice at 0751 with foreground-color 3 update.
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to Customer-Input.
*>
 try-again.
     move     zero to sih-test.
     move     sih-invoice  to  Invoice-nos.
     move     sih-test     to  Item-nos.
     perform  Invoice-Read-Indexed.
     If       fs-reply not = zero
              go to Jump-1.
     display  "Invoice Exists Re-Enter" at 0701  with foreground-color 2.
     go       to Get-Inv.
*>
 Jump-1.
     If       delivery-tag = zero	*> Only show delivery details If F8 pressed Instead of
       or     WS-Show-Delivery = "N"	*> accept on cust no. Input
              go to Customer-Setup.
*>
     move     "D"          to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Read-Indexed.
     If       fs-reply = 21
              move  zero  to  delivery-tag
              go to  Customer-Setup.
*>
     move     deliv-address to address-a.
     go       to Customer-display.
*>
 Customer-Setup.
     move     sales-address  to  address-a.
*>
 Customer-display.
     If       delivery-tag = zero
              display sales-name at 0301 with foreground-color 3
     else
              display deliv-name at 0301 with foreground-color 3.
*>
     move     1  to  Z.
     unstring address-a  delimited  by  sl-delim
                  Into  address-line  count Z  pointer  Z.
     display  address-line at 0401 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim
                  Into  address-line  count Z  pointer  Z.
     display  address-line at 0501 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim
                  Into  address-line  count Z  pointer  Z.
     display  address-line at 0601 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim
                  Into  address-line  count Z  pointer  Z.
     display  address-line at 0701 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  Into  address-line   pointer  Z.
     display  address-line at 0801 with foreground-color 3.
*>
     move     spaces  to  address-line.
*>
 ref-input.
     move     spaces to sih-ref sih-order.
     accept   sih-ref at 0669 with foreground-color 3 update.
*>
 order-input.
     accept   sih-order at 0769 with foreground-color 3 update.
*>
 type-input.
     move     zero to sih-type.
     accept   sih-type at 1007 with foreground-color 3 update.
     move     space to WS-named.
     If       sih-type = zero
              go to Invoice-Details-Main.
*>
     If       sih-type  >  4 or < 1
              go to  type-input.
*>
     move     D-Types (sih-type) to add-line1.
     display  " " at 1001 with erase eol.
     display  ">>> " at 1031 with foreground-color 2.
     display  add-line1 at 1035 with foreground-color 2.
*>
     move     zero to sih-cr.
     If       sih-type = 3
              perform  cr-note
              If    escape-Code = "Q"
                    go to  Invoice-Details-Main.
*>
     move     zero to Z.
*>
     If       sih-type = 1  or  >  2
              go to  Main-Exit.
*>
*>  Type 2 (Account) only
*>
     move     zero  to  we-error.
*>
     subtract sales-unapplied from sales-current.
*>
     If       sales-current  >  zero
              subtract sales-last-inv from run-date giving  work-1
              If work-1  >  sales-credit
              display "Overdue Balance <<<" at 1648   with foreground-color 2 highlight
              move  999  to  we-error.
*>
     If       sales-current  >  sales-limit
              display "Balance Exceeds Credit Limit <<<" at 1725 with foreground-color 2 highlight
              move  998  to  we-error.
*>
     If       sales-credit not > zero
          or  sales-limit  not > zero
              display "No Longer an Account Customer <<<" at 1825 with foreground-color 2 highlight
              move  997  to  we-error.
*>
     If       we-error = zero
              go to  Main-Exit.
*>
     display  ">>> Warning! "      at 1635 with foreground-color 2  highlight.
     display  "**********************" at 1958  with foreground-color 2.
     display  "*" at 2058 with foreground-color 2.
     display  "*" at 2158 with foreground-color 2.
     display  "*" at 2079 with foreground-color 2.
     display  "*" at 2179 with foreground-color 2.
     display  "**********************" at 2258  with foreground-color 2.
*>
     display  "None Zero or ESC To Abort" at 2040 with foreground-color 2.
     display  "Return To Continue" at 2140 with foreground-color 2.
     move     zero to Z.
     accept   Z at 2260 with foreground-color 6 update.
     If       Cob-Crt-Status = Cob-Scr-Esc
              move 1 to z
                        Cob-Crt-Status.
     go       to Main-Exit.
*>
 New-Customer.
     perform  OTM3-Close.
     perform  Invoice-Close.
*>
     perform  Sales-Close.
     perform  DelInvNos-Close.
     perform  Delivery-Close.
     perform  Analysis-Close.
     If       SL-Stock-Link = "Y"
              perform  Stock-Close.
     If       Stk-Audit-Used = 1
              perform Stock-Audit-Close.
*>
*> Call SL cust create program for New Customer.
*>
     call     "sl960" using WS-calling-data system-record to-day.
     perform  Program-Start.
     go       to Invoice-Details-Main.
*>
 Main-Exit.
     exit     section.
*>
 Get-a-Deleted-Invoice section.
*>============================
*>
     If       not Del-Exists
              go to l70ad-Terminate.
 l70ab-Read.
*>
*> 30/4/15 new code for ISAM Instead of seq
*>
     move     zeros to WS-Del-Inv-Nos.
     move     zeros to sih-invoice.  *> so we can test for It
     move     1 to File-Key-No.
     set      fn-not-less-than to true.
     perform  DelInvNos-Start.
*>     start    Del-Inv-Nos-File key not < WS-Del-Inv-Nos Invalid key
     If       fs-reply = 21 or 23
              go to l70ad-terminate.
*>
 l70ab-Read-2.
     perform  DelInvNos-Read-Next.
     If       fs-reply = 10
              move     "N" to WS-Using-Del-Inv-No
              go to l70ac-Close.
     If       WS-Del-Inv-Nos = zero
              go to l70ab-Read-2.
     move     WS-Del-Inv-Nos to sih-invoice.  *> del rec will be deleted after o/p of Invoice.
     display  "Using Deleted Invoice Numbers" at 0345  with foreground-color 2 blink.
     move     "Y" to WS-Using-Del-Inv-No.
     go       to l70ae-Exit.
*>
 l70ac-Close.
*>
*> If open as output clear down file and If RDB *MT deletes all records with
*>  key below 99999999 so same thing
*>
     perform  DelInvNos-Close.
     perform  DelInvNos-Open-Output.
     display  "                             " at 0345.
*>
 l70ad-Terminate.
*>
 *>    move     next-invoice to sih-invoice.
     move     zero to WS-delinv.
*>
 l70ae-Exit.
     exit     section.
*>
 CR-Note      section.
*>===================
*>
*>  CRs are only processed against posted Invoices, hence using OTM3.
*>
 main.
     display  " " at 1201 with erase eol.
     display  " " at 1301 with erase eol.
     display  " " at 1401 with erase eol.
     display  " " at 1501 with erase eol.
     display  " " at 1601 with erase eol.
*>
 main-input.
     display  "Invoice To Credit - [        ]" at 1201 with foreground-color 2.
*>
     move     zero  to  WS-CR.
*>
     accept   WS-CR at 1222 with foreground-color 3 update.
     If       Cob-Crt-Status = Cob-Scr-Esc
              move "Q" to escape-Code
              go to Main-Exit.
     move     WS-CR to sih-cr.
     If       sih-cr = zero
              move  "Z"  to  WS-named
              go to  no-inv-restart
     else
              move  space  to  WS-named.
*>
     If       sih-cr = 99999999
              move "Q" to escape-Code
              go to Main-Exit
     else
              move space to escape-Code.
*>
     move     sih-cr       to  oi3-invoice.
     move     sih-Customer to  oi3-Customer.
*>
     move     1 to File-Key-No.
     perform  OTM3-Read-Indexed.     *> Error cant find the Invoice
     If       fs-reply not = zero
              display SL181 at line WS-23-lines col 01 with foreground-color 2 highlight
              go to  main.
*>
     display  space at line WS-23-lines col 01 with erase eol.
     If       oi-type not = 2               *> Error can only credit Posted Invoices
              display SL184  at line WS-23-lines col 01 with foreground-color 2 highlight
              go to main-input.
*>
     If       s-closed			*> Error Invoice Is Paid
              display SL182  at 1301  with foreground-color 2 highlight
              go to main-input
     else
              display " " at line WS-23-lines col 01 with erase eol.
*>
     If       oi-hold-flag = "Q"	*> Warning Invoice has query flag set but we can continue
              display SL183  at line WS-23-lines col 01  with foreground-color 2 highlight.
*>
     If       Invoice-Customer not = WS-Sales-Key    *> cant happen
              display SL193  at 1301 with foreground-color 4
              go to main-input.
*>
     move     oi-date to u-bin.
     add      1 oi-deduct-days to u-bin.
     If       u-bin > sih-date
              move "A" to WS-named.
*>
     add      oi-deduct-VAT to oi-deduct-amt.
     add      oi-extra oi-carriage oi-deduct-amt oi-Net
              oi-VAT oi-c-VAT oi-e-VAT to oi-discount.
     subtract oi-PAid from oi-discount.
*>
     display  "Amount O/S on Invoice Is " at 1401   with foreground-color 2.
     move     oi-discount to Display-9.
     display  Display-9  at 1426 with foreground-color 3.
     move     oi-deduct-amt to Display-8.
     display  "of which" at 1437 with foreground-color 2.
     display  Display-8  at 1446 with foreground-color 3.
     display  "is Late Charges" at 1456 with foreground-color 2.
     If       WS-named = "A"
              display SL185 at 1510 with foreground-color 2.
     display  SL006  at 1626.
     accept   WS-reply  at 1670.
*>
 No-Inv-Restart.
     perform  main.       *> Clear screen lines 12 - 16
*>
 Main-Exit.
   exit section.
*>
 Program-Start section.
*>====================
*>
     display  " " at 0101 with erase eos.
     move     to-day to u-date.          *> In UK date form
*>
*> New for BO processing 17/03/24
*>
     move     SL-BO-Flag  to WS-SL-BO-Flag.   *> BO In operation ? (will set (or not WS-BO-Used)
*>
     If       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15        *> Analysis
                                                 File-Info
              If    return-Code not = zero          *> not = zero - No file found
                    move 1 to WS-Process-Func
                              WS-Sub-Function
                    call "sl070" using WS-calling-data  *> Create Anal default recs
                                       system-record
                                       to-day
                                       file-defs
                    call  "CBL_CHECK_FILE_EXIST" using File-15   *> Only If the call failed
                                                       File-Info *> SHOULD NEVER happen but JIC
                    If    return-Code not = zero          *> not = zero - No file found
                          display   SL186 at 2301
                          display   SL003 at 2401
                          accept WS-Reply at 2430
                    end-if
              end-if
     end-if
*>
     perform  Sales-Open.
     perform  Delivery-Open.          *> these 2 are open I-O to force creation.
     perform  Analysis-Open.
     If       SL-Stock-Link = "Y" and  *> Create if not exist
              WS-BO-Used               *> If BO flag set and linked to stock set
              open     I-O BO-Stk-Itm-File
              If       FS-Reply not = zero
                       close BO-Stk-Itm-File
                       open output BO-Stk-Itm-File
                       close BO-Stk-Itm-File
                       open  I-O BO-Stk-Itm-File.
*>
*> Create Invoice & ITM3 files If do not exist.
*>
     If       FS-Cobol-Files-Used             *> create Invoice If not exist.
              call  "CBL_CHECK_FILE_EXIST" using File-16      *> Invoice
                                                 File-Info
              If    return-Code not = zero          *> not = zero - No file found
                    perform  Invoice-Open-Output
                    perform  Invoice-Close
              end-if
              call  "CBL_CHECK_FILE_EXIST" using File-19      *> create ITM3 If not exist
                                                 File-Info
              If    return-Code not = zero        *> not = zero - No file found
                    perform OTM3-Open-Output
                    perform OTM3-Close
              end-if
     end-if
*>
     move     zero  to  menu-reply.
     perform  Invoice-Open.
     perform  OTM3-Open-Input.
     perform  DelInvNos-Open.
     move     1 to WS-delinv.           *> could be just created as code will clear It If empty.
*>
*> If linked open Stock & Audit file
*>
     If       SL-Stock-Link = "Y"
       If     FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-11        *> Stock file
                                                 File-Info
              end-call
              If    return-Code not = zero          *> not = zero - No file found
                    perform Stock-Open-Output
                    perform Stock-Close
              end-if
              perform Stock-Open                   *> open I-o  stock-file   Thats ok we just wont find any Items
              If     Stk-Audit-Used = 1
                     call  "CBL_CHECK_FILE_EXIST" using File-10        *> Stock audit file
                                                        File-Info
                     end-call
                     If    return-Code not = zero          *> not = zero - No file found
                           perform Stock-Audit-Open-Output
                     else
                           perform Stock-Audit-Open-Extend
                     end-if
              end-if
       end-if
     end-if.
*>
 Main-Exit.
     exit     section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-test-date
*> output:  u-date/WS-date as uk date format
*>          u-bin not zero If valid date
*>
     move     WS-test-date to WS-date.
     If       Date-Form = zero
              move WS-Month to WS-Inv-Month    *> done again for UK - but JIC
              move 1 to Date-Form.
     If       Date-UK
              move WS-Month to WS-Inv-Month
              go to zz050-test-date.
     If       Date-USA                *> swap month and days
              move WS-days  to WS-swap
              move WS-month to WS-days
              move WS-swap  to WS-month
              move WS-Month to WS-Inv-Month
              go to zz050-test-date.
*>
*> So Its International date format
*>
     move     "dd/mm/ccyy" to WS-date.  *> swap Intl to UK form
     move     WS-test-date (1:4) to WS-Year.
     move     WS-test-date (6:2) to WS-Month.
     move     WS-Month           to WS-Inv-Month
     move     WS-test-date (9:2) to WS-Days.
*>
 zz050-test-date.
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
*>  Converts date In binary to UK/USA/Intl date format
*>****************************************************
*> Input:   u-bin
*> output:  WS-date as uk/US/Inlt date format
*>          u-date & WS-Date = spaces If Invalid date
*>
     perform  maps04.
     If       u-date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     u-date to WS-date.
*>
     If       Date-Form = zero
              move 1 to Date-Form.
     If       Date-UK
              go to zz060-Exit.
     If       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              go to zz060-Exit.
*>
*> So Its International date format
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
*>  Converts date In to-day to UK/USA/Intl date format
*>****************************************************
*> Input:   to-day
*> output:  WS-date as uk/US/Inlt date format
*>
     move     to-day to WS-date.
*>
     If       Date-Form = zero
              move 1 to Date-Form.
     If       Date-UK
              go to zz070-Exit.
     If       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              go to zz070-Exit.
*>
*> So Its International date format
*>
     move     "ccyy/mm/dd" to WS-date.  *> swap Intl to UK form
     move     to-day (7:4) to WS-Intl-Year.
     move     to-day (4:2) to WS-Intl-Month.
     move     to-day (1:2) to WS-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
 zz080-Close-All-Files section.
*>****************************
*>
     perform  Sales-Close.
     perform  Delivery-Close.
     perform  Analysis-Close.
     close    BO-Stk-Itm-File.
     perform  Invoice-Close.
     perform  OTM3-Close.
     perform  DelInvNos-Close.
     move     zero to  Pass-Value.
     If       SL-Stock-Link = "Y"
              perform Stock-Close
              perform Stock-Audit-Close
              close    BO-Stk-Itm-File.
*>
 zz080-Exit.
     exit     section.
*>
*> Used when next-invoice and saving It when creating Invoice recs.
*>
 zz100-Read-System-Record  section.
*>********************************
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.  *> Only use param FILE
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     Pass-Value to WS-Pass-Value.  *> save sys rec fld for rewrite as not saved yet.
     move     1 to File-Key-No.
     perform  System-Open-Input.
*>
     move     1 to File-Key-No.
     perform  System-Read-Indexed.        *> Read Cobol file params, no tests as opened In sales.
     perform  System-Close.
*>
 zz100-Exit.
     exit     section.
*>
 zz110-Write-System-Record  section.
*>*********************************
*>
     If       File-System-Used NOT = zero   *> Force RDB processing
              move     "66" to FA-RDBMS-Flat-Statuses
              move     1 to File-Key-No
              move     WS-Pass-Value to Pass-Value  *> restore it
              perform  System-Open
              move     1 to File-Key-No
              perform  System-Rewrite
              perform  System-Close
     end-if.
*>
*> Now do the same for the Cobol file.
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     1 to File-Key-No.
     move     WS-Pass-Value to Pass-Value.  *> restore it.
     perform  System-Open.                       *> Open cobol file params as I/O
     move     1 to File-Key-No.
     perform  System-Rewrite.                    *> Update Cobol file params
     perform  System-Close.                      *> Close the Cobol param file.
*>
 zz110-Exit.
     exit     section.
*>
 zz120-Build-BO-Record  section.
*>*****************************
*>
*> No processing for Credit Notes
*> Invoice-no = zero If stock-held = zero WITH no Inv Item line created.
*>
*> If we get an write error, retry adding 1 to serial up to 98 times
*>   then give up with a error message
*>
     move     zero to Return-Code.
     If       Sih-Type = 3  *> Not for CN's.
              go to zz120-Exit.
*>
     Initialise
              BO-Stk-Itm-Record with filler.
     move     Sih-Customer    to BO-Stk-Cust-No.
     move     Sil-Product (I) to BO-Stk-Item-No.
     move     zero            to BO-Serial.
     move     Sih-Type        to BO-Stk-Inv-Type.
     move     Sih-Order       to BO-Stk-PO.
     move     Sih-Ref         to BO-Stk-Ref.
     move     WS-Temp-Invoice to BO-Stk-Orig-Inv-No.
     subtract WS-Qty from Stock-Held giving BO-Stk-BO-Qty.
     move     Stock-Order-Due to BO-Stk-BO-Arr-Date. *> days since 1601 ?.
     move     Sih-Date        to BO-Stk-Order-Date.  *> Today, days since 1601.
     move     Stock-Retail    to BO-Stk-Price.       *> current price
     write    BO-Stk-Itm-Record.
     If       FS-Reply  not = zero
              perform  until FS-Reply = zero
                       add      1 to BO-Serial
                       write    BO-Stk-Itm-Record
                       if       FS-Reply = zeros
                                exit perform
                       end-if
                       if       BO-Serial > 98   *> It should never happen cust ordered 98 times for same item #
                                perform Eval-Status
                                display SL203         at line WS-23-lines col 1 with foreground-color 4 highlight erase eol
                                display fs-reply      at line WS-23-lines col 30 with foreground-color 2 highlight
                                display exception-msg at line WS-23-lines col 33 with foreground-color 3
                                display BO-Cust-Itm-No at line WS-23-lines col 59 with foreground-color 3
                                display SL006         at line WS-lines    col 1
                                accept WS-reply       at line WS-lines    col 45
                                move    4 to Return-Code
                                exit perform
                       end-if
                       exit perform cycle
              end-perform
     end-if.
*>
 zz120-Exit.
     exit     section.
*>
 zz200-Build-From-BO  section.
*>***************************
*>
*> Process BO (Back Orders) if present but only if new stock has
*> arrived via st020 Stock Addition processing which updates any
*> and all existing BO records that have a matching stock item.
*>
*> Such BO records, are deleted after processing a new invoice, Proforma or
*> receipt.
*>
*> Two tables are used BO-Table 1 and 2 and initialised at start with keys set
*> as all 9's and other fields spaces or zeros depending on field type via
*> INITIALISE.
*> BO records are read and stored in BO table 1, sorted by Customer/Stock item.
*> This allows (if present) multi stock items to be processed for the same
*> customer in one hit but see later.
*>
*> BO Table 1 is read and for each unique Stock Item BO-Table 2 is created and
*> Stock item record read, onhold stock stored & ordered qty added to.
*> Table is sorted by item number.
*>
*>  For Table 1 - if stock onhold is not < ordered table 1 sorted by cust/item
*> else left as sorted by order date and ALL processing done by Date only.
*>
*> This might need changing but that means looking for all items order for
*> specific customer CANNOT occur- - [ Swings and roundabout syndrome ].
*>
*> Although it could be possible to just process table 1 for only items that
*>  are short of stock and these are only processed by date with all others
*>  assuming more than one item still present and re-sorted by cust/item
*> This is not done at present as just makes it more complex.
*>
     If       NOT WS-BO-Used
              go to zz200-Exit.  *> Quit if BO NOT In use
*>
     move     low-values to BO-Cust-Itm-No.
     move     zeros  to BO-Table-Used  *> active table in use count
                        Return-Code.   *> Needed if need next table entry at
                                       *> top level inline perform
     move     spaces to WS-Temp-Cust.  *> Records current cust # to test for change of #
*>
*> Init each table entry then set key to high-values/all 9's so sort places them at end
*> of the table.
*>
     perform  varying BO-Table-Cnt from 1 by 1
              until BO-Table-Cnt > BO-Table-Size
              Initialise
                       BOT-Record (BO-Table-Cnt) with filler
              move     high-values to BOT-Cust-Itm-No (BO-Table-Cnt)
     end-perform.
     perform  varying WS-Item-Table-Used from 1 by 1
              until WS-Item-Table-Used > WS-Item-Table-Size
              move     all "9" to WS-Item-No      (WS-Item-Table-Used)
              move     space  to WS-Date-Flag     (WS-Item-Table-Used)
              move     zeros  to WS-Total-Ordered (WS-Item-Table-Used)
                                 WS-Stock-Held    (WS-Item-Table-Used)
     end-perform.
     move     zero   to WS-Item-Table-Used
                        BO-Invoiced-Used.
     move     zero   to BO-Table-Cnt.
     move     spaces to WS-Temp-Stock-Key.
*>
*> Get the BO records and store if Arrived-Flag = "Y"
*>  as they can be processed now.
*>
     start    BO-Stk-Itm-File FIRST.
     perform  until exit
              read     BO-Stk-Itm-File next record at end
                       exit perform
              end-read
              If       FS-Reply not = zero   *> EOF & JIC
                       exit perform
              end-if
              If       BO-Stk-Arrived-Flag = "Y"
                       add      1  to BO-Table-Used
                       If       BO-Table-Used > BO-Table-Size
                                display  " " at 0101 with erase eos
                                display  SL207 at 1201 with foreground-color 4 highlight beep
                                display  SL208 at 1401 with foreground-color 2
                                display  SL006 at 1501 with foreground-color 2
                                accept   WS-Reply at 1545
                                move     4 to Return-Code
                                exit perform
                       end-if
                       move     BO-Stk-Itm-Record to BOT-Record (BO-Table-Used)
              end-if
              exit     perform cycle
     end-perform.
*>
*> Have now loaded table of all BO records that have NEWLY arrived stock
*>
     If       Return-Code = 4       *> Table size too small so quit process as
              move     "N" to WS-BO-Processing
              go to    zz200-Exit.  *> needs a recompile with larger Table size although preset to 500.
*>
     If       BO-Table-Used = zero    *> No BO records with new stock so quit BO process
              move     "N" to WS-BO-Processing
              go to    zz200-Exit.
*>
*> Sort First by Stock Item Number if we have > 1
*>
     move     zero to Return-Code.
     if       BO-Table-Used = 1       *> sort not needed
              move     1 to WS-Item-Table-Used
              move     BOT-Stk-Item-No (1) to WS-Item-No (1)
              move     BOT-Stk-BO-Qty  (1) to WS-Total-Ordered (1)
     else
              sort     BOT-Record on ascending key BOT-Stk-Item-No
              move     zero   to BO-Table-Cnt
                                 WS-Item-Table-Used
              perform  until BO-Table-Cnt not < BO-Table-Used
                       add      1  to BO-Table-Cnt
                       if       BO-Table-Cnt > BO-Table-Used
                                display  " " at 0101 with erase eos
                                display  SL213 at 1201 with foreground-color 4 highlight beep
                                display  SL208 at 1401 with foreground-color 2
                                display  SL006 at 1501 with foreground-color 2
                                accept   WS-Reply at 1545
                                move     4 to Return-Code
                                exit perform
                       end-if
                       if       WS-Temp-Stock-Key not = BOT-Stk-Item-No (BO-Table-Cnt)
                                add      1  to WS-Item-Table-Used
                                move     BOT-Stk-Item-No (BO-Table-Cnt)
                                                      to WS-Temp-Stock-Key
                                                         WS-Item-No (WS-Item-Table-Used)
                                move     BOT-Stk-BO-Qty  (BO-Table-Cnt)
                                                      to WS-Total-Ordered (WS-Item-Table-Used)
                       else
                                add      BOT-Stk-BO-Qty  (BO-Table-Cnt)
                                                      to WS-Total-Ordered (WS-Item-Table-Used)
                       end-if
                       exit perform cycle
              end-perform   *> Table holds total back ordered per item #
     end-if.
     If       Return-Code = 4       *> Table size too small so quit process as
              move     "N" to WS-BO-Processing
              go to    zz200-Exit.  *> needs a recompile with larger Table size although preset to 500.
*>
*>
*> Now have table containing Total Qty per stock item BO, so we
*> can now check if this total is LESS than the arrived stock via stock records.
*> If NOT should process in DATE order instead of customer order.
*>
     move     zero to Return-Code.
     if       WS-Item-Table-Used > zero
              perform  varying  WS-Item-Table-Cnt from 1 by 1
                          until WS-Item-Table-Cnt > WS-Item-Table-Used
                       move     WS-Item-No (WS-Item-Table-Cnt)  to WS-Stock-Key
                       move     1 to File-Key-No
                       perform  Stock-Read-Indexed
                       If       FS-Reply not = zeros   *> Should not really happen but ...
                                perform Test-For-Read-Stock  *> display the problem
                                move   8 to Return-Code
                                exit perform
                       end-if
                       move     Stock-Held to WS-Stock-Held (WS-Item-Table-Cnt)
                       if       WS-Total-Ordered (WS-Item-Table-Cnt) > WS-Stock-Held (WS-Item-Table-Cnt)
                                move     "Y" to WS-BO-Date-Order-Processing
                                                WS-Date-Flag (WS-Item-Table-Cnt)
                                add      1 to WS-BO-Date-Cnt
                       end-if
                       exit     perform cycle
              end-perform
     end-if
     if       Return-Code = 8              *> bad status reading stock record so quit
              move     "N" to WS-BO-Processing
              go to zz200-Exit.
*>
*> Sort second by Customer / Item no
*>
     If       BO-Table-Used > 1  *> Don't sort for < 2
       and    not WS-BO-Process-By-Date
              sort     BOT-Record on ascending key BOT-Cust-Itm-No
              move     "Y" to WS-BO-Processing
     end-if
*>
*> Also see further down for question and test..
*>
*> Now have table In sorted order of Items within Cust no so order Is cust no.
*> Item no.  This way only need to check change of cust no.
*> and as unused entries have high-values, they will be at end of table after
*> sort.
*>
*> At this point there ARE BO items to process.
*>
*> IF any BO Stock items Qty > Stock-Held then we process only by DATE in order
*> to be fair to earlest orders before the latest.
*>
*> Next display notice that there are BO record to process - Process BO's?
*>  Then if needed one or more items Held
*> stock is less than total BO orders all will be processed by Date only.
*>  Offer to provide a BO item list with :
*>  Item #, Short Description, BO Order total, Item Held #. Flash aly where stock not enough
*>
*> so ask (SL214) if BO processing to procede with # of items that can be done.
*> If Yes then offer to display the items that can be processed (SL215).
*>
     move     BO-Table-Used to WS-Display3-1.
     display  SL214 at 0401 with erase eos foreground-color 2.
     display  WS-Display3-1 at 0434 with foreground-color 3
     move     "Y" to WS-Reply.
     accept   WS-Reply at 0452 update UPPER.
     if       WS-Reply not = "Y"
              move     "N" to WS-BO-Processing
              go to zz200-Exit.
*>
     display  SL215  at 0401 with erase eol foreground-color 2.
     move     "Y" to WS-Reply.

     accept   WS-Reply at 0445 update UPPER.
*>
*> This perform, takes care if display area less than number of items available
*> then continue from line 6 until completed. Displays if Date mode needed (YES).
*>
     if       WS-Reply = "Y"
*> Do Sub heads
              display  "Item Number "   at 0401  with erase eos foreground-color 3
              display  " Held      Ord" at 0416  with foreground-color 3
              display  "Date"           at 0431  with foreground-color 3
              display  "Mode"           at 0531  with foreground-color 3
*> Now the data
              move     zero to WS-Item-Table-Cnt
              move     5    to Lin
              Initialize SInvoice-Header
              Initialize SInvoice-Bodies
              perform  until exit
                       add      1 to WS-Item-Table-Cnt
                       if       WS-Item-Table-Cnt > WS-Item-Table-Used
                                display  SL006    at line WS-23-Lines col 1 with foreground-color 2
                                move     space to WS-Reply
                                accept   WS-Reply at line WS-23-Lines col 45 with foreground-color 2
                                exit perform   *> List finished as all displayed
                       end-if
                       add      1 to Lin
                       move     WS-Stock-Held    (WS-Item-Table-Cnt) to WS-Display6-1
                       move     WS-Total-Ordered (WS-Item-Table-Cnt) to WS-Display6-2
                       display  WS-Item-No   (WS-Item-Table-Cnt) at line Lin col 01 with foreground-color 2
                       display  WS-Display6-1                    at line Lin col 16 with foreground-color 2
                       display  WS-Display6-2                    at line Lin col 23 with foreground-color 2
                       if       WS-Date-Flag (WS-Item-Table-Cnt) = "Y"
                                display  WS-Display6-1           at line Lin col 16 with foreground-color 3 HIGHLIGHT
                                display  "YES"                   at line Lin col 32 with foreground-color 3 HIGHLIGHT
                       end-if
                       if       Lin = WS-22-Lines
                                display  SL006    at line WS-23-Lines col 1 with foreground-color 2
                                move     space to WS-Reply
                                accept   WS-Reply at line WS-23-Lines col 45 with foreground-color 2
                                if       WS-Item-Table-Cnt not < WS-Item-Table-Used
                                         exit perform         *> stops dup SL006 etc as could happen.
                                end-if
                                move     5 to Lin
                                display  space at 0601 with erase eos
                       end-if
                       exit perform cycle
              end-perform
              display  space at 0401 with erase eos
     end-if.
*>
     move     To-Day to U-Date.
     move     zero   to U-Bin.
     perform  maps04.       *> Now U-Bin has days since 1601 for To-Day
     If       U-Bin = zero   *> Should never happen but JIC
              perform  zz080-Close-All-Files
              stop     "Date code In ZZ200 broken - aborted - press return to quit"
              stop     run.
*>
*> Ask if processing by DATE, if not turn date proc OFF and resort as cust / item
*>
     if       WS-BO-Process-By-Date
          and BO-Table-Used > 1          *> other table ?, nope keep using primary
              move     WS-BO-Date-Cnt     to WS-Display3-1
              move     WS-Item-Table-Used to WS-Display3-2
              display  SL216    at 0401 with erase eos foreground-color 2
              display  WS-Display3-1 at 0411  with foreground-color 3
              display  WS-Display3-2 at 0417  with foreground-color 3
              display  SL217         at 0601  with foreground-color 2
              move     space to WS-Reply
              accept   WS-Reply at 0671 with foreground-color 3 UPPER
              if       WS-Reply = "Y"
                       move     "N" to WS-BO-Date-Order-Processing
                       sort     BOT-Record on ascending key BOT-Cust-Itm-No
                       move     "Y" to WS-BO-Processing
              end-if
     end-if
*>
*> Start of Primary BO Item processing
*>
     move     zero to Return-Code
                      BO-Invoiced-Used
                      BO-Invoiced-Cnt   *> so far not used
                      BO-Table-Cnt.
     perform  until exit                *> get next table rec then Invoice -- TOP Level inline perform
              add      1 to BO-Table-Cnt
              If       BO-Table-Cnt > BO-Table-Used
                       move     "N" to WS-BO-Processing
                       exit perform
              end-if
              If       BOT-Stk-Cust-No (BO-Table-Cnt) not = WS-Temp-Cust
                       move     BOT-Stk-Cust-No (BO-Table-Cnt) to WS-Temp-Cust   *> save for compare against change of cust
              end-if
*>
*> Create header rec based In Invoice-Details
*>
              Initialize SInvoice-Header with filler
              move     U-Bin            to Sih-Date
              move     BOT-Stk-Cust-No (BO-Table-Cnt)  to Sih-Customer
                                                          WS-Sales-Key
              move     1  to C-Check
              move     1  to File-Key-No
              perform  Sales-Read-Indexed    *> JIC Cust. now deleted but should not happen
              If       fs-reply not = zeros  *> as delete routine in sl010 checks for BO recs
                       display  SL211 at 0401 with foreground-color 4
                       move     BOT-Stk-Cust-No (BO-Table-Cnt) to WS-Temp-Cust  *> MAY BE SPACES ???
                       exit perform cycle
              end-if
              display  "                " at 0401
              display  "                        " at 0911
*>
              move     zeros to Sih-Invoice
              If       Del-Exists
                       perform  Get-a-Deleted-Invoice
              end-if
              move     zero         to Sih-Test
              perform  until exit  *> Get a new Invoice # if sih-invoice = 0 (no deleted invoices)
                       If       Sih-Invoice = zeros
                                perform  zz100-Read-System-Record
                                move     next-invoice  to  sih-invoice
                                                           WS-Temp-Invoice
                                add      1 to Next-Invoice          *> Remove same code else where
                                perform  zz110-Write-System-Record
                       end-if
                       move     sih-invoice  to  Invoice-nos
                       move     sih-test     to  Item-nos
                       perform  Invoice-Read-Indexed
                       If       fs-reply not = zero   *> Rec not present thats good
                                exit perform
                       else
                                move     zero to Sih-Invoice
                                exit     perform cycle  *> get next Inv # as It is present
                       end-if
              end-perform
*>
*> Have a good Invoice # in Sih_invoice
*>
              move     BOT-Stk-PO       (BO-Table-Cnt) to Sih-Order
              move     BOT-Stk-Ref      (BO-Table-Cnt) to Sih-Ref
              move     BOT-Stk-Inv-Type (BO-Table-Cnt) to Sih-Type
              Initialise SInvoice-Bodies  *> No Filler present
*>
              display  prog-name at 0101 with foreground-color 2 erase eos
              perform  zz070-Convert-Date
              display  WS-date at 0171 with foreground-color 2
              display  "Back Order Processing" at 0229 with foreground-color 2
              display  "****************************************" at 0441 with foreground-color 2
              display  "*                  *                   *" at 0541 with foreground-color 2
              display  "*A/C Nos  <       >*Ref    [          ]*" at 0641 with foreground-color 2
              display  "*Invoice <        >*Order  [          ]*" at 0741 with foreground-color 2
              display  "****************************************" at 0841 with foreground-color 2
              display  "Type [ ]  <1> = Receipt; <2> = Account; <4> = Pro-Forma"
                                                         at 1001  with foreground-color 2
*>
              display  Sih-Customer at 0652 with foreground-color 3
              display  Sih-Invoice  at 0751 with foreground-color 3
              display  Sih-Ref      at 0669 with foreground-color 3
              display  Sih-Order    at 0769 with foreground-color 3
              display  Sih-Type     at 1007 with foreground-color 3
              display  ws-dash      at 1101 with foreground-color 2
*>
              move     Sih-Customer  to WS-Sales-Key
              move     1 to File-Key-No
              perform  Sales-Read-Indexed
              move     Sales-Address  to  Address-A
              perform  Customer-Display  *> Display  name & address
*>
              display  "Stock Linked" at 1201 with foreground-color 2
              display  "Line - "               at 1216 with foreground-color 2
              display  "Net <          >"      at 1227 with foreground-color 2
              display  "Vat <          >"      at 1244 with foreground-color 2
              display  "Invoice <          >"  at 1261 with foreground-color 2
              display  "Product     <----------Description--------->    Qty   Unit Price  Disc. Vat"
                                               at 1405 with foreground-color 2
*>
*>  This all assumes that screen length Is always less than # of Items per cust.
*>  otherwise this WILL need CHANGING.
*>
              move     zero to I
              perform  zz300-Display-Outline-2 varying lin from 16 by 1
                                                until lin not < ws-23-lines
              subtract WS-Accept-Body from I                    *> M = WS-accept-body
              move     1  to  J
              add      J  14  giving  lin  *> minus 1 to allow for the ADD
*>
              move     1 to I
*>
              display  I at 1223 with foreground-color 3  *> Line # for item #
*>   Get-data-2-main
              perform  until exit
                       if       BO-Table-Cnt > BO-Table-Used
                                move     "N" to WS-BO-Processing
                                exit perform   *> Ditto ^^
                       end-if
                       if       BOT-Stk-Cust-No (BO-Table-Cnt) not = WS-Temp-Cust
                                exit perform
                       end-if                *> Should never happen as tested 1st level perform
                       add      1 to Lin
                       move     2 to cole
                       move     BOT-Stk-Item-No (BO-Table-Cnt)  to WS-Product
                                                                   Sil-Product (I)
                                                                   Test-Product
                                                                   WS-Temp-Stock-Key
                       display  WS-Product at curs with foreground-color 2
*>
*>   Get stock rec (Get-Simple-Stock)
*>
                       move     spaces  to  Sil-Description (I)
                       If       WS-Stock-No-Long = spaces
                                move WS-Abrev-Stock to WS-Stock-Abrev-Key
                                move 2 to File-Key-No
                       else
                                move WS-Temp-Stock-Key to WS-Stock-Key
                                move 1 to File-Key-No
                       end-if
                       perform  Stock-Read-Indexed
                       If       FS-Reply = 21 or = 23   *> Should never happen - BUT JIC
                                move SL196 to WS-Stock-Desc
                                move     spaces         to WS-PA
                                                           PA-group
                                                           Sil-PA (I)
                       else
                                move     Stock-SA-Group to WS-PA
                                                           PA-group
                                                           Sil-PA (I)
                       end-if
*>
                       move     17 to cole        *> Desc
                       display  WS-Stock-Desc   at curs with foreground-color 3
                       move     WS-Stock-Desc to WS-Description
                                                 Sil-Description (I)
                       move     BOT-Stk-BO-Qty (BO-Table-Cnt) to WS-Qty
                       move     53 to cole        *> QTY
                       If       Stock-Services-Flag = "Y"
                                move 1 to WS-Qty
                       end-if
 *>                      display  WS-Qty at curs with foreground-color 3
                       accept   WS-Qty at curs with foreground-color 3 update
                       If       WS-Qty = zero       *> Cancel/Ignore BO transaction on zero or Escape
                         OR     Cob-Crt-Status = Cob-Scr-Esc
                                If       I > zero   *> JIC
                                         move     "S" to WS-Reply     *> Skip this time
                                         display  SL220 at line WS-23-Lines col 1 with foreground-color 4 with erase eos
                                         display  SL221 at line WS-Lines col 5 with foreground-color 3 Highlight
                                         accept   WS-Reply at line WS-23-Lines col 72
                                                           with foreground-color 3 UPPER UPDATE
                                         if       WS-Reply = "D"
                                                  move BOT-Cust-Itm-No (BO-Invoiced-Cnt)  to BO-Cust-Itm-No
                                                  delete   BO-Stk-Itm-File record  *> Dont care if invalid, hopefully
                                         end-if  *> otherwise, it is Skip it, this time
                                         display  space at line WS-23-Lines col 1 with erase eos
                                         Initialise Invoice-Lines (I)  *> clear down any above entered data
                                         subtract 1 from I             *>  for Item line
                                end-if
                                if       BO-Table-Cnt + 1 > BO-Table-Used
                                         if       I > 1
                                                  perform  End-Totals  *> does P&P etc.
                                                  perform  zz210-Delete-BO-Records
                                         end-if
                                         move     2 to Return-Code  *> exit top perform
                                         exit     perform   *> I = 1 = no transactions
                                end-if
                                add      1 to BO-Table-Cnt
                                if       BOT-Stk-Cust-No (BO-Table-Cnt) not = WS-Temp-Cust
                                         move     1 to Return-Code
                                         exit     perform
                                end-if
                       end-if                *> Should never happen as tested 1st level perform
                       if       BO-Table-Cnt > BO-Table-Used
                                move     "N" to WS-BO-Processing
                                move     2 to Return-Code
                                exit perform
                       end-if
*>
                       move     60 to cole  *> Unit Price
                       move     Stock-Retail to WS-Tmp-Stk-Price
*>
*>  What to do If BO price and stock not the same  ??
*>
                       move     "B" to WS-Reply
*>
*> Set default as using BO price, Reply = B or S = Stock price
*>
                       If       BOT-Stk-Price (BO-Table-Cnt) not = Stock-Retail
                                move     BOT-Stk-Price (BO-Table-Cnt) to WS-Tmp-BO-Price
                                move     Stock-Retail to WS-Tmp-Stk-Price
                                display  SL209 at line WS-23-Lines col 1 with foreground-color 4
                                                                         highlight beep erase eol
                                display  SL003 at line WS-Lines  col 1   with foreground-color 2
                                accept   WS-Reply at line WS-Lines col 30 with foreground-color 3
                                                                               UPDATE
                                display  "BO Price - "    at line WS-23-Lines col 1
                                                             with foreground-color 2 erase eos
                                display  WS-Tmp-BO-Price  at line WS-23-Lines col 12
                                                             with foreground-color 2
                                display  "Stock Price - " at line WS-23-Lines col 35
                                                             with foreground-color 2
                                display  WS-Tmp-Stk-Price at line WS-23-Lines col 49
                                display  SL210 at line WS-Lines col 1 with foreground-color 2
                                If       BOT-Stk-Inv-Type (BO-Table-Cnt) not = 1 and not = 2
                                         move     "S" to WS-Reply  *> Using stock price for proformas else BO rec price
                                else
                                         move     "B" to WS-Reply
                                end-if
                                accept   WS-Reply at line WS-Lines col 45 with foreground-color 3
                                                                               UPPER UPDATE
*>  NET
                                If       WS-Reply = "B"
                                         multiply WS-Qty by BOT-Stk-Price (BO-Table-Cnt) giving WS-Net
                                         display  WS-Tmp-BO-Price at curs with foreground-color 3
                                         move     BOT-Stk-Price (BO-Table-Cnt) to WS-Unit
                                else
                                         multiply WS-Qty by Stock-Retail giving WS-Net
                                         display  WS-Tmp-Stk-Price at curs with foreground-color 3
                                         move     Stock-Retail to WS-Unit
                                end-if
                       else             *> BO and Stock price the same
                                multiply WS-Qty by Stock-Retail giving WS-Net
                                move     Stock-Retail to WS-Unit
                                display  WS-Tmp-Stk-Price at curs with foreground-color 3
                       end-if
                       move     WS-Qty  to Sil-Qty (I)
                       move     WS-Net  to Sil-Net (I)
                                           Display-9
                       move     WS-Unit to Sil-Unit (I)
                       display  Display-9 at 1232 with foreground-color 3
*>
*>  Discount
*>
                       move     Sales-Discount  to  WS-discount
                       move     72 to cole
                       move     WS-disc-wka to WS-disca1
                       move     WS-disc-wkb to WS-disca3
                       display  WS-discount-display at curs with foreground-color 3
                       accept   WS-discount-accept  at curs with foreground-color 3 update
                       move     WS-discb1 to WS-disc-wka
                       move     WS-discb3 to WS-disc-wkb
                       move     WS-discount to  work-d Sil-discount (I)
                       move     WS-Net to  work-n
                       multiply work-n by work-d giving work-1
                       divide   work-1 by 100    giving work-1
                       subtract work-1  from  WS-Net
                       move     WS-Net to Sil-Net (I) Display-9
                       display  Display-9 at 1232 with foreground-color 3
*>
*>   VAT
*>
                       move     "S" to Vat-Code-X  *> 17/2/23  for Standard rate
                       move     79 to cole
                       display  Vat-Code-X at curs with foreground-color 3
                       accept   Vat-Code-X at curs with foreground-color 3 update
*>
                       If       Vat-Code-X = "S"    *> Standard code 1
                                move 1 to Vat-Code
                        else
                         If     Vat-Code-X = "R"    *> Reduced  code 2
                                move 2 to Vat-Code
                          else
                           If   Vat-Code-X = "Z"    *> Zero     code 3
                                move 3 to Vat-Code
                           end-if
                         end-if
                       end-if  *> Otherwise assuming it is 1, 2 or 3 but could be 4 or 5 for say USA
*> using 1st three as last 2 are Sales tax, Not 4 UK but used outside UK, EU & AUZ etc so supported
                       If       Vat-Code < 1 or > 5  *> so change test for 'not
                                move 3 to Vat-Code   *> = 4 or 5' Instead of '> 3'
                       end-if
                       move     Vat-Code  to  Sil-Vat-Code (I)
*>
                       If       Vat-Code = zero
                                move  zero  to  WS-VAT
                       else
                                move VAT-Rate (Vat-Code) to WS-VAT-Rate
                                compute  WS-VAT rounded = (WS-Net * WS-VAT-Rate) / 100
                       end-if
*>
                       move     WS-VAT to  Display-9
                                           Sil-VAT (I)
                       display  Display-9 at 1249 with foreground-color 3
                       perform  Running-Totals    *> GOOD for Inline so display for line 12
*>
                       add      1  to  J  *> Display line
                       add      1  to  I  *> inv body no
*>
                       add      1  to  BO-Invoiced-Used
                       if       BO-Invoiced-Used > BO-Invoiced-Size   *> size 50 for 1 cust, should never happen but JIC
                                display  " " at 0101 with erase eos
                                display  SL218 at 1201 with foreground-color 4 highlight beep
                                display  "("   at 1265 with foreground-color 4
                                display  BO-Invoiced-Size at 1266 with foreground-color 4
                                display  ")"   at 1268 with foreground-color 4
                                display  SL208 at 1401 with foreground-color 2
                                display  SL006 at 1501 with foreground-color 2
                                accept   WS-Reply at 1545
                                move     8 to Return-Code
                                exit perform
                       end-if
                       move     BOT-Cust-Itm-No (BO-Table-Cnt) to BO-Invoiced-Record (BO-Invoiced-Used)
*>
                       if       BO-Table-Cnt + 1 > BO-Table-Used
                                if       I > 1
                                         perform  End-Totals
                                         perform  zz210-Delete-BO-Records
                                end-if
                                move     2 to Return-Code  *> exit top perform
                                exit     perform   *> I = 1 = no transactions
                       end-if

                        if      BOT-Stk-Cust-No (BO-Table-Cnt + 1) not = WS-Temp-Cust
                          and   I > 1
                                perform  End-Totals
                                perform  zz210-Delete-BO-Records
                                move     1 to Return-Code  *> get next BO table record
                                exit     perform
                        end-if
              end-perform
              if       Return-Code = 1  *> Top level perform get next BO table rec (& store cust-no -> ws-temp-cust)
                       exit perform cycle
              end-if
              if       Return-Code = 2   *> no more table entries, exit top perform
                       move     "N" to WS-BO-Processing
                       exit perform
              end-if
              if       Return-Code = 8   *> BO-invoiced table exceeded - BO process aborted
                       move     "N" to WS-BO-Processing
                       exit perform
              end-if
     end-perform.
*>
 zz200-Exit.
     exit     section.
*>
 zz210-Delete-BO-Records   section.
*>********************************
*>
*> FOR early TESTING JUST EXIT
*>     REMOVE AFTER    <***
     go to zz210-Exit.
*>
     perform  varying  BO-Invoiced-Cnt from 1 by 1
              until    BO-Invoiced-Cnt > BO-Invoiced-Used
              move     BO-Invoiced-Cust-Item-No (BO-Invoiced-Cnt)  to BO-Cust-Itm-No
              delete   BO-Stk-Itm-File record   invalid key   *> No, should never happen but JIC (may be a coding bug)
                       display  SL219          at line WS-23-Lines col 1 with foreground-color 4 erase eos
                       move     spaces to Exception-Msg
                       string   BO-Stk-Cust-No "/" BO-Stk-Item-No "/" BO-Serial
                                  into Exception-Msg
                       display  Exception-Msg  at line  WS-23-Lines col 37 with foreground-color 4
                       display  SL006          at line  WS-Lines    col 1  with foreground-color 2
                       accept   WS-Reply at line WS-Lines col 45
              end-delete
     end-perform.
*>
 zz210-Exit.
     exit     section.
*>
 zz300-Display-Outline-2   section.
*>********************************
*>
     add      1  to  I.
     move     1 to cole.
     display  "[             ][" at curs with foreground-color 2 erase eol.
     move     49 to cole.
     display  "]  [     ][          ][     ][ ]" at curs  with foreground-color 2.
*>
 zz300-Exit.
     exit     section.
*>
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
