       >>source free
*>*************************************************************
*>                                                            *
*>              Stock Item Additions & Deletions              *
*>                                                            *
*>   Automatics via stock menu NEEDS TO BE TESTED             *
*>   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^             *
*>                                                            *
*>*************************************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         st020.
*>**
*>    Author.             V.B.Coen, FBCS (ret)
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Stock Item Manual Movements - Additions, Deductions
*>                        Order entry and reporting for Back Orders.
*>**
*>    Called modules.
*>                        maps04.
*>                        acas010 ->
*>                         auditMT - Stock Audit table.
*>                        acas011 -> Stock file FH
*>                         stockMT - STOCK-REC RDB table.
*>**
*>    Error messages used.
*>                        ST000.
*>                        ST002.
*>                        ST003.
*>                        ST005.
*>                        ST006.
*>                        ST011.
*>
*>                        ST201.
*>                        ST202.
*>                        ST203.
*>                        ST204.
*>                        ST205.
*>                        ST206.
*>                        ST207.
*>                        ST208.
*>                        ST209.
*>                        ST210.
*>                        ST211.
*>                        ST212.
*>                        ST213.
*>                        ST214.
*>                        ST215.
*>                        ST216.
*>                        ST217.
*>                        ST218.
*>                        ST219.
*>                        ST220.
*>                        ST221.
*>
*>                        ST250.
*>                        ST251.
*>**
*> Changes:
*> 07/05/09 vbc - Rewritten in Cobol from scratch against v2 specs.
*> 10/05/09 vbc - Added in support for Barcode reader module & tested.
*> 27/05/09 vbc - Remove barcode module in OpenSource version so that
*>                support can be offered for the different versions
*>                  of Hardware but provide a dummy for menu.
*> 03/06/09 vbc - .07 Added support for Service only Flag.
*> 04/06/09 vbc - .08 Added Audit No in reports.
*> 05/06/09 vbc - .12 Added Report stock change totals for each print.
*> 06/06/09 vbc - .13 Reposition change totals.
*> 09/06/09 vbc - .14 Added missing WIP Quantity if any, to stock value.
*> 28/06/09 vbc - .15 Set Stk-Activity-Rep-Run (1) after running reports
*>                    Also increment batch no when clearing down Audit file.
*>                    Reset Stk-Audit-No to 1 on size error (max val = 255).
*> 15/07/09 vbc - .16 Modify menu option 4 subject to value of Stk-Period-Cur.
*>                    Batch no (Stk-Audit-No) used on proof rep and updated after
*>                    running end of period rep and clearing down audit file.
*>                    Amend manuals to reflect s/w changes.
*> 20/07/09 vbc - .17 Added function 5 to replace existing optional data, ie
*>                .18 dates ordered & due, quantities on order and backordered.
*> 19/08/09 vbc - .19 Added Standard and simple barcode processing based on a
*>                    WASP WLR8900 CCD LR via USB port. should work for any using
*>                    same port and protocol see code at da000 for more info.
*> 07/09/10 vbc - .20 Added extra functions for Cups print spool lpr as well as 2 copies etc.
*> 11/12/11 vbc -     Changed version from 1.00.xx to 3.01.xx, in keeping with the rest of ACAS
*>                .21 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 12/05/13 vbc - .22 Changed wsnames to in common as pl010 called in st010.
*> 13/05/13 vbc - .23 Added time to reports.
*> 14/05/13 vbc - .24 Commented out WS-month processing at aa020-DH-End in error along with the test!
*> 15/05/13 vbc - .25 Added processing in audit report for 'source' from invoicing and purchasing
*>                    in reports.
*> 16/05/13 vbc - .26 Changed wsnames using copybook and added msg ST219 to replace 201 if SF not created.
*> 25/05/13 vbc - .27 Added invoice / PO nos to add/ded audit reports with a change of heading & forced
*>                    Stock Value literal in adds & deducts report in case another report was run 1st
*>                    restored test for proc-month as YTD looks odd & changed the add statement (misused?)
*>                    for yearly figures.
*> 28/05/13 vbc - .28 (see .27) added credit note reporting see ea000.
*> 04/06/13 vbc - .29 Replaced Stk-Page-Lines with system Page-Lines.
*> 20/07/16 vbc - .30 Screen layout error when asking to delete audit file.
*> 21/07/16 vbc - .31 Replace Cobol file acces verbs with calls to FH and RDB
*>                    DAL. Precede references to Stock-Record, Stock-Key,
*>                    Stock-Abrev-Key, Stock-Desc by WS- to reflect that we
*>                    are only dealing with a WS record and the FD is now gone.
*>                    Stop using File-Status and replace with call to
*>                    "CBL_CHECK_FILE_EXIST" instead. Do same for all such
*>                    checks, sets etc to kill of usage dates back to floppies.
*>                    ST011 added. Update version to 3.02.
*> 26/07/16 vbc - .32 Added FH/DAL for audit file so all files I/O via a F.H.
*> 24/10/16 vbc - .33 ALL programs now using wsnames.cob in copybooks
*>                    Usage of maps99 deleted.
*> 12/03/18 vbc - .34 acasnnn copylib renaming acas000-open etc to comply with
*>                    rest of ACAS to (System-Open etc) removed unused field
*>                    WS var. error-code.
*>                    Chg ST000 to stock rec.
*> 16/03/18 vbc - .35 Added code for AUTORUN via stock menu which will print reports
*>                    for both Additions and Deletions and then delete Audit data
*>                    There will be no requests to do this so printer must be on
*>                    or spooler to print when it is turned on.
*> 05/05/23 vbc       NOTE - recs with Stock-Services-Flag = "Y" are ignored so
*>                    No additions or deductions occur. Already coded.
*> 16/08/23 vbc       Removed dead file processing verbs that were remarked out.
*> 20/03/24 vbc - .36 Deduct Qty received from Stock-Pre-Sales or zeroise Pre-Sales
*>                    if Qty is higher for both manual and barcode input.
*>                .37 If SL-BO flag = "Y" then on stock
*>                    additions / Stock item arrivals to warehouse etc, the BO
*>                    file is looked at and if exists will check if there is a
*>                    item record there and if so, flag it as stock arrived with
*>                    the date.  This can then be read by sl910 invoicing at
*>                    start and offer to process any BO orders with new stock
*>                    for invoice processing for all other than credit notes.
*>                    IT will update all BO records with the same stock #
*>                    providing new qty held is not > BO qty otherwise they are
*>                    ignored.
*>                    NOTE :  The BO file does NOT have a DB table as yet so no
*>                    FH or DAL has been created.  <<<<<<
*>                    WOULD NEED CODING FOR THIS BUT is a temporary file.
*> 30/03/24       .38 Update stock record Est-Date to today for new arriving
*>                    stock. move todays date in binary (since 1601) to
*>                    stock-Arrival-Date and in Barcode processing.
*>                .39 Updated BO processes to check all BO recs for same stk #
*>                    on updating - see last in #37.
*> 07/04/24       .40 Increased BO size to 72 incl. BO-Stk-Ref field.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/04/24 vbc   .41 On printing only open & close printer once and if on 1st
*>                    report line count > 5 and page no is odd force new page.
*> 28/04/24 vbc   .42 Chg test in BO stock-held < (WS-temp-) stock-held to
*>                    WS-Temp-Stock-Held not < BO-Stk-BO-Qty and not = zero
*> 29/04/24 vbc - .43 In ba010-Accept-Data1 full key should be WS-Stock-Key
*>                    WS-Days-Late chg s(4) & L4-Days-Late to zzz9 (increase
*>                    by 1).
*> 16/12/24 vbc - .44 Changed Page-Lines to WS-Page-Lines set at 56 as system
*>                    uses portrait - user may need to change this setting.
*>                    Extra display if WE-Error opening stock file.
*>                    On Stock-open tests more close to before goto exit.
*> 05/01/25 vbc   .45 Add read & rewrite param rec when updating status of
*>                    Stk-Activity-Rep-Run
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*>
*>
*>  << TODO >>
*>                 1. Need to add wip qty * bundle to co-joined stock no.
*>                    having updated wip qty et al. ?
*>                 2. Validate code to ensure conformance with updated spec
*>                    for order and procedure when calc & updating stock values.
*>
*>******************************************************************************
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
 copy "selboitm.cob".   *> BO item file Does not use FH, DALs
 copy "selprint.cob".
 data                    division.
*>================================
*>
 file section.
*>------------
*>
 copy "fdboitm.cob".   *> BO item file
 copy "fdprint.cob".
*>
 working-storage section.
*>-----------------------
*>
 77  Prog-Name           pic x(15)       value "ST020 (3.3.00)".
 copy "print-spool-command.cob".
 01  WS-Qty-Screen-Display6.
     03  WS-unit6        pic 9(6).
     03  WS-sign6        pic x.
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
 01  WS-amount-screen-display8.
     03  WS-poundsd8     pic 9(8).
     03  WS-period8      pic x     value ".".
     03  WS-penced8      pic v99.
 01  WS-amount-screen-accept8 redefines WS-amount-screen-display8.
     03  WS-pound8       pic 9(8).
     03  filler          pic x.
     03  WS-pence8       pic v99.
*>
 01  WS-amount-work8.
     03  amt-wk-pds8     pic 9(8).
     03  amt-wk-pence8   pic v99.
 01  WS-amount-ok8 redefines WS-amount-work8.
     03  amt-ok8         pic 9(8)v99.
*>
 01  work-fields.
     03  Menu-Reply      pic 9                   value zero.
     03  WS-Reply        pic x                   value space.
     03  Escape-Code     pic x                   value space.
     03  WS-Proc-Month.
         05  WS-Proc-Mth pic 99                  value zero.
             88  WS-Good-Month                   values 01 thru 12.
     03  WS-Proc-Date    pic x(10).
     03  WS-Current-Period pic x(8).         *> Week, Month Quarter
     03  WS-Test-Date    pic x(10).
     03  WS-stock-dates.
         05  WS-Stock-Order-Date pic x(10).
         05  WS-Stock-Order-Due  pic x(10).
     03  WS-Audit-Report-Lit pic x(33)           value spaces.
     03  WS-Days-Late    pic s9999               value zero.
     03  WS-Page-Lines   binary-char unsigned value 56.   *> 16/12/24 as system is for Portrait and Landscape used.
     03  Line-Cnt        binary-char unsigned    value 99.
     03  Page-Nos        binary-char unsigned    value zero.
     03  a               binary-char unsigned    value zero.
     03  i               binary-char unsigned    value zero.
     03  b               pic s9(7).
     03  WS-Audit-Count  binary-short unsigned   value zero.
*>
     03  WSD-Stock-Key                           value spaces.
         05  WSD-Abrev-Stock   pic x(7).
         05  WSD-Stock-No-Long pic x(6).
*> 20/03/24
     03  WS-SL-BO-Flag   pic x.
         88  WS-BO-Used                          value "Y".
     03  WS-BO-Can-Be-Used
                         pic x.
         88  WS-BO-Usable                        value "Y".
     03  WS-BO-File-Open pic x                   value "N".
     03  WS-Temp-Stock-Held
                         pic s9(6)             value zero.
*>
     03  WS-z6           pic z(6).
     03  WS-z3           pic zz9.
     03  WS-Qty          pic s9(6)               value zero.
     03  WS-New-Qty      pic s9(6)               value zero.
     03  WS-Price        pic 9(6)v99     comp-3  value zero.
     03  WS-Value        pic s9(8)v99    comp-3  value zero.
     03  WS-Old-Value    pic s9(8)v99    comp-3  value zero.
     03  WS-New-Value    pic s9(8)v99    comp-3  value zero.
     03  WS-New-Cost     pic s9(6)v9999  comp-3  value zero.
     03  WS-Add-Total    pic s9(9)v99    comp-3  value zero.
     03  WS-Ded-Total    pic s9(9)v99    comp-3  value zero.
     03  WS-Total        pic zzz,zzz,zz9.99.
*>
     03  WS-Spaces-20    pic x(20)               value spaces.
     03  WS-Env-Lines    pic 999                 value zero.
     03  WS-Lines        binary-char  unsigned   value zero.
     03  WS-22-Lines     binary-char  unsigned   value zero.
     03  WS-23-Lines     binary-char  unsigned   value zero.
*>
 01  accept-Terminator-Array pic 9(4)            value zero.
     copy "screenio.cpy".
*>
 01  WS-Date-Formats.
     03  WS-Swap             pic xx.
     03  WS-Date             pic x(10).
     03  WS-UK redefines WS-Date.
         05  WS-days         pic xx.
         05  filler          pic x.
         05  WS-month        pic xx.
         05  filler          pic x.
         05  WS-year         pic x(4).
     03  WS-USA redefines WS-Date.
         05  WS-usa-month    pic xx.
         05  filler          pic x.
         05  WS-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  WS-Intl redefines WS-Date.
         05  WS-intl-year    pic x(4).
         05  filler          pic x.
         05  WS-intl-month   pic xx.
         05  filler          pic x.
         05  WS-intl-days    pic xx.
*>
 01  hdtime                            value spaces.
     03  hd-hh           pic xx.
     03  hd-mm           pic xx.
     03  hd-ss           pic xx.
     03  hd-uu           pic xx.
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
*> Print layouts
*>
 01  Line-1.
     03  l1-Program      pic x(16)     value spaces.
     03  filler          pic x(39)     value spaces.
     03  l1-title        pic x(42)     value "Stock Addition Report".
     03  filler          pic x(27)     value spaces.
     03  filler          pic x(5)      value "Page ".
     03  l1-Page         pic zz9.
*>
 01  Line-2.
     03  l2-User         pic x(61).
     03  l2-Batch        pic x(55)     value spaces.
     03  l2-Date         pic x(10).
     03  filler          pic x         value space.
     03  l2-HH           pic xx        value spaces.
     03  filler          pic x         value ":".
     03  l2-MM           pic xx        value spaces.
*>
 01  Line-3.
     03  filler          pic x(78)   value spaces.
     03  filler          pic x(9)    value "Change in".
*>
 01  Line-3b.
     03  l3-Proc-Lit     pic x(11)  value "Proc. Date".
     03  filler          pic x(57)  value
         "Stock Number  Description                         Qty    ".
     03  l3-Price-Lit    pic x(5)   value "Price".
     03  l3-Stock-Lit    pic x(19)  value "    Stock Value    ".
     03  l3-Dates-Lit    pic x(39)  value "Order Date    Date Due     Order Status".
*>
 01  Line-4.
     03  l4-Proc-Date    pic x(11).
     03  l4-Stock-Number pic x(14).        *> 25
     03  l4-Desc         pic x(32).        *> 57
     03  l4-Qty          pic z(6)9-.       *> 65
     03  l4-Cost         pic z(6)9.99-.    *> 76
     03  l4-Qty-B-ord redefines l4-Cost
                         pic bbz(5)9bbb.
     03  l4-New-Value    pic z(5),zz9.99-. *> 89
     03  filler          pic xxx          value spaces.
     03  l4-Source.
         05  l4-Date-Ordered pic x(13).
         05  l4-Date-Due     pic x(12).        *> 118
         05  l4-Days-Late    pic zzz9          blank when zero.
         05  l4-Lit-Late     pic x(10).        *> Days Late  131
*>
 copy "wsfnctn.cob".
 copy "wsstock.cob".     *> 3.02
 copy "wsaudit.cob".
 copy "wsmaps03.cob".
 copy "wsmaps09.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
*>     03  System-Record          pic x.
     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
*>     03  WS-Stock-Audit-Record  pic x.
*>     03  WS-Stock-Record        pic x.
     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide
     03  ST000          pic x(36) value "ST000 Error on Writing to Stock Rec.".
     03  ST002          pic x(36) value "ST002 Error on Writing to Audit File".
     03  ST003          pic x(27) value "ST003 Press return for Menu".
     03  ST005          pic x(18) value "ST005 Invalid Date".
     03  ST006          pic x(30) value "ST006 Press return to continue".
     03  ST011          pic x(33) value "ST011 Error on stockMT processing".
*> Module specific
     03  ST201          pic x(26) value "ST201 Stock File not found".
     03  ST202          pic x(26) value "ST202 Audit File not found".
     03  ST203          pic x(42) value "ST203 Abbreviated Stock number not present".
     03  ST204          pic x(45) value "ST204 Quantity cannot equal or exceed 999,999".
     03  ST205          pic x(45) value "ST205 Quantity in Stock cannot exceed 999,999".
     03  ST206          pic x(48) value "ST206 Quantity in Stock cannot be less than zero".
     03  ST207          pic x(43) value "ST207 Quantity can only end with space or -".
     03  ST208          pic x(42) value "ST208 CAUTION: Stock quantity will be zero".
     03  ST209          pic x(40) value "ST209 Stock Value set to Minimum. (Zero)".
     03  ST210          pic x(39) value "ST210 Current Deductions at Zero or < 0".
     03  ST211          pic x(39) value "ST211 To Date Deductions at Zero or < 0".
     03  ST212          pic x(49) value "ST212 Stock Value set to Maximum. (99,999,999.99)".
     03  ST213          pic x(23) value "ST213 Bad month in date".
     03  ST214          pic x(28) value "ST214 Stock Number not found".
     03  ST215          pic x(39) value "ST215 Current Additions at Zero or < 0".
     03  ST216          pic x(39) value "ST216 To Date Additions at Zero or < 0".
     03  ST217          pic x(27) value "ST217 Services only Product".
     03  ST218          pic x(53) value "ST218 Services only product so only quantity accepted".
     03  ST219          pic x(32) value "ST219 Stock File not yet created".
     03  ST220          pic x(25) value "SL220 Cannot open BO file".
     03  ST221          pic x(30) value "ST221 Error on Rewrite BO file".
*>
     03  ST250          pic x(13) value " (Order Date)".
     03  ST251          pic X(11) value " (Due Date)".
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
 01  To-Day             pic x(10).
*>
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 aa000-Core                 section.
*>*********************************
*>
     accept   WS-env-lines from lines.
     if       WS-env-lines < 24
              move  24 to WS-env-lines WS-lines
     else
              move  WS-env-lines to WS-lines
     end-if
     subtract 1 from WS-lines giving WS-23-lines.
     subtract 2 from WS-lines giving WS-22-lines.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
*> New for RDB
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-11    *> Stock file
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    display ST219 at line WS-23-lines col 1 with foreground-color 4 highlight
                    display ST003   at line WS-lines col 01
                    accept WS-reply at line WS-lines col 30
                    go to aa999-Exit
              end-if
     end-if
*>
*> New for BO processing 20/03/24
*>
     move     SL-BO-Flag  to WS-SL-BO-Flag.   *> BO in operation
     call     "CBL_CHECK_FILE_EXIST" using File-31  *> Currently, only file is used
                                           File-Info.
     if       Return-Code not = zero        *> not = zero - No file found
              move    "N" to WS-SL-BO-Flag
                             WS-BO-File-Open.     *> Turn it off as no file exists at this time
*>
     if       WS-BO-Used
              open  i-o BO-Stk-Itm-File
              if    FS-Reply not = zero    *> Should never happen as tested above
                    close  BO-Stk-Itm-File
                    display  ST220 at line WS-lines col 01
                    accept WS-reply at line WS-lines col 30
                    move  "N" to WS-BO-File-Open
                    go to aa999-Exit
              else
                    move  "Y" to WS-BO-File-Open
              end-if
     end-if.
*>
     perform  Stock-Open.
     if       FS-Reply not = zero
          or  WE-Error not = zero
              display ST201 at line WS-23-lines col 1 with foreground-color 4 highlight
              display FS-Reply at line WS-23-lines col 28 with foreground-color 2 highlight
              display "/" at line WS-23-lines col 30  with foreground-color 2
              display WE-Error at line WS-23-lines col 31 with foreground-color 2 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              perform Stock-Close
              go to aa999-Exit.
     move     zero to Menu-Reply.
     perform  zz070-Convert-Date.
     move     WS-Date to WS-Proc-Date.
*>
*> Set variable menu item (4)
*>
     if       Stk-Period-Cur = "Q"
              move "Quarter" to WS-Current-Period
     else
      if      Stk-Period-Cur = "W"
              move "Week" to WS-Current-Period
      else
              move "Month" to WS-Current-Period.
*>
     string   "(5)  End of "    delimited by size
              WS-Current-Period delimited by space
              " Audit Reports"  delimited by size  into WS-Audit-Report-Lit.
*>
 aa010-Display-Headings.
     move     zero to WS-Audit-Count Page-Nos.
     move     99 to Line-Cnt.
     if       Menu-Reply = 1
              perform aa030-Display-Head-Add
     else
      if      Menu-Reply = 2
              perform aa040-Display-Head-Del
      else
       if     Menu-Reply = 3
              perform aa050-Display-Head-Barcode-Add
       else
        if    Menu-Reply = 4
              perform aa060-Display-Head-EOM
        else
         if   Menu-Reply = 5
              perform aa080-Display-Head-Order
         else
              perform aa070-Display-Head-Menu.
*>
 aa020-DH-End.
     move     WS-Month to WS-Proc-Month.
     if       WS-Proc-Month not numeric or not WS-Good-Month
              display ST213 at line WS-23-lines col 1 with foreground-color 4 highlight
              display WS-Proc-Month at line WS-23-lines col 25 with foreground-color 2 highlight
              display WS-Date at line WS-23-lines col 28 with foreground-color 2 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to aa999-Exit.
     go       to aa100-Main-Menu.
*>
 aa030-Display-Head-Add.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock Additions Entry" at 0130 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
 aa040-Display-Head-Del.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock Deductions Entry" at 0130 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
 aa050-Display-Head-Barcode-Add.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock Barcode Additions Entry" at 0123 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
 aa060-Display-Head-EOM.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock End of Month Processing" at 0126 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
 aa070-Display-Head-Menu.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock Movements Menu" at 0131 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
 aa080-Display-Head-Order.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Stock Order Entry" at 0132 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-date at 0171 with foreground-color 2.
*>
 aa100-Main-Menu.
*>
*> First block is for AUTO run via stock menu program when given 2 params
*>   stock NULL st020
*>
     if       function lower-case (WS-CD-Args (1:5)) not = "st020"
              go to aa107-Main-Menu-Start.
*>
*>  So it is AUTO RUN
*>
     if       WS-CD-Args (6:1) = "5"
      if      Stk-Audit-Used = 1        *> zero = no audit, so report not avail
              move 5 to Menu-Reply
              go to aa120-Bypass-Accept-1
      else
              move    8 to WS-Term-Code                   *> Abort process
              perform Stock-Close                         *> stock file
              go to aa999-Exit.
*>
 aa107-Main-Menu-Start.
     display  "Select one of the following by number :- [ ]" at 0401 with foreground-color 2.
*>
     display  "(1)  Stock Additions Entry"       at 0604 with foreground-color 2.
     display  "(2)  Stock Deductons Entry"       at 0704 with foreground-color 2.
     display  "(3)  Stock Additions from Barcode Readers" at 0804 with foreground-color 2.
     display  "(4)  Stock Order Entry"           at 0904 with foreground-color 2.
     if       Stk-Audit-Used = 1
              display  WS-Audit-Report-Lit       at 1104 with foreground-color 2. *> OPTION 5
     display  "(9)  Return to System Menu"       at 1404 with foreground-color 2.
*>
 aa110-Accept-Loop.
     accept   Menu-Reply at 0443  with foreground-color 6 auto update.
     if       Menu-Reply = 9
              perform Stock-Close                         *> stock file
              if      WS-BO-File-Open = "Y"
                      close  BO-Stk-Itm-File
              end-if
              go to aa999-Exit.
     if       Menu-Reply = zero or > 5
              go to aa110-Accept-Loop.
*>
 aa120-Bypass-Accept-1.
*>
*>   Create audit cobol file if not exist
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-10    *> Audit file
                                                 File-Info
              end-call
              if       return-code not = zero               *> not = zero - No file found
                  and  Stk-Audit-Used = 1
                       perform Stock-Audit-Open-Output
                       perform Stock-Audit-Close
              end-if
     end-if
*>
     if       Stk-Audit-Used = 1
      if      (Menu-Reply > zero and < 5)
              perform   Stock-Audit-Open-Extend
      else
              perform   Stock-Audit-Open-Input
     end-if.
*>
     if       FS-Reply not = zero
              display ST202 at line WS-23-lines col 1 with foreground-color 4 highlight
              display FS-Reply at line WS-23-lines col 28 with foreground-color 2 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              perform Stock-Close
              go to aa999-Exit.
*>
     if       Menu-Reply = 1
              move  "Stock Addition Report" to l1-Title
              move  "Order Date    Date Due     Order Status" to l3-Dates-Lit
              move  "Proc. Date" to l3-Proc-Lit
              move  "Price" to l3-Price-Lit
              move  "    Stock Value    " to l3-Stock-Lit
              move spaces to l2-Batch
              open output Print-File
              perform  ba000-Process-Manual-Additions
              close Print-File
              if  Page-Nos not = zero
                  call  "SYSTEM" using Print-Report
              end-if
     else
      if      Menu-Reply = 2
              move  "Stock Deduction Report" to l1-Title
              move  spaces                   to l3-Dates-Lit  l3-Price-Lit l2-Batch
              move  "Proc. Date" to l3-Proc-Lit
              move  "    Stock Value    " to l3-Stock-Lit
              open  output Print-File
              perform  ca000-Process-Manual-Deductions
              close Print-File
              if  Page-Nos not = zero
                  call  "SYSTEM" using Print-Report
              end-if
      else
       if     Menu-Reply = 3                               *> use Barcode reader data to update stock & audit
              move spaces to l2-Batch
              open output Print-File
              perform  da000-Process-Barcode-Additions     *> this process need to be moded to match your kit
              close Print-File
              if    Page-Nos not = zero
                    call  "SYSTEM" using Print-Report
              end-if
       else
        if    Menu-Reply = 4
              move  "Stock Orders Update" to l1-Title
              move  "Order Date    Date Due" to l3-Dates-Lit
              move  "B'Qty" to l3-Price-Lit
              move  spaces to l3-Stock-Lit l3-Proc-Lit
              move  spaces to l2-Batch line-4
              open  output Print-File
              perform fa000-Process-Orders
              close Print-File
              if   Page-Nos not = zero
                   call  "SYSTEM" using Print-Report
              end-if
        else
         if   Menu-Reply = 5
          and Stk-Audit-Used = 1        *> zero = no audit, so report not avail
              move Stk-Audit-No to WS-z3
              string  "Batch "   delimited by size
                      WS-z3      delimited by size
                      into l2-Batch
              perform  ea000-Process-End-of-Month.
*>
     if       Stk-Audit-Used = 1
              perform  Stock-Audit-Close.
*>
     if       WS-CD-Args (6:1) = "5"                       *> If autorun we are done.
              perform Stock-Close
              go to aa999-Exit.

     move     zero to Menu-Reply.
     go       to aa010-Display-Headings.
*>
 maps04.
     call     "maps04" using maps03-ws.
*>
 aa999-Exit.
     goback.
*>
*>******************************************
*>                  Routines               *
*>******************************************
*>
 ba000-Process-Manual-Additions   section.
*>***************************************
*>
 ba005-New-Heads.
     perform  aa010-Display-Headings.
     display  " Stock Number    Description         Quantity    Price   Stk Qty   Stk Value"
                                                  at 0301 with foreground-color 2.
     perform  varying lin from 5 by 1 until lin > WS-22-lines
              move    1 to cole
              display "[             ]" at curs with erase eol foreground-color 2
              move    16 to cole
              display "{                    }" at curs with foreground-color 2
              move    38 to cole
              display "[       ]"     at curs with foreground-color 2
              move    47 to cole
              display "[         ]"   at curs with foreground-color 2
              move    58 to cole
              display "{      }"      at curs with foreground-color 2
              move    67 to cole
              display "[           ]" at curs with foreground-color 2
     end-perform
     move     4 to i.
*>
 ba010-Accept-Data1.
     add      1 to i.
     if       i > WS-22-lines
              perform  ba005-New-Heads  *> Was ba000-Process-Manual-Additions.  *> checked for end of screen & reset
              add      1 to i.
     move     spaces to WSD-Stock-Key.
     initialize WS-Stock-Audit-Record with filler.
     move     2 to cole.
     move     i to lin.
     accept   WSD-Stock-Key at curs with foreground-color 3 update UPPER.
     if       WSD-Stock-Key = spaces
           or Cob-Crt-Status = Cob-Scr-Esc
              go to ba999-Exit.
*>
*>   Redisplay as uppercase then get the stock record but might have abbrev. no.
*>
     display  WSD-Stock-Key at curs with foreground-color 3.
     if       WSD-Stock-No-Long = spaces
              move     WSD-Abrev-Stock to WS-Stock-Abrev-Key
              move     2 to File-Key-No             *>  1=stock-key, 2=Abrev, 3=Desc
              perform  Stock-Read-Indexed
              if       FS-Reply = 23 or = 21        *> invalid key but for RDB its 23
                       display ST203 at line WS-23-lines col 1 with foreground-color 4 highlight
                       subtract 1 from i
                       go to ba010-Accept-Data1
              end-if
     else
              move WSD-Stock-Key to WS-Stock-Key
              move     1 to File-Key-No
              perform  Stock-Read-Indexed
              if       FS-Reply = 23 or = 21
                       display ST214 at line WS-23-lines col 1 with foreground-color 4 highlight
                       subtract 1 from i
                       go to ba010-Accept-Data1
              end-if
     end-if
*>
*>  Have the required Stock record so get and show the desc
*>
     move     17 to cole.
     display  WS-Stock-Desc (1:20) at curs with foreground-color 3.
*>
*> Check for Services only flag (e.g., P&P etc) so ignore
*>
     if       Stock-Services-Flag = "Y"
              display ST217 at line WS-23-lines col 1 with foreground-color 2 highlight
              display WS-spaces-20 at curs
              subtract 1 from i
              go to ba010-Accept-Data1.
*>
     display  " " at line WS-23-lines col 1 with erase eol.  *> clear any prior errors
*>
*>  Quantity to add to stock next but use whats on order as guide
*>
 ba020-Accept-Qty.
     move     Stock-On-Order to WS-unit6.
     move     space to WS-sign6.
     move     39 to cole.
     accept   WS-Qty-Screen-Display6 at curs with foreground-color 3 update.
     if       WS-unit6 = zero
           or Cob-Crt-Status = Cob-Scr-Esc
           or Cob-Crt-Status = Cob-Scr-Key-Up
           or Cob-Crt-Status = Cob-Scr-Page-Up
              subtract 1 from i
              move 17 to cole
              display WS-spaces-20 at curs
              go to ba010-Accept-Data1.
*>
     if       WS-unit6 > 999998
              display ST204 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ba020-Accept-Qty.
     if       (ws-unit6 + Stock-Held) > 999999
              display ST205 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ba020-Accept-Qty.
     if       WS-sign6 not = "-" and not = space
              display ST207 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ba020-Accept-Qty.
*>
*> Clear error line
*>
     display  " " at line WS-23-lines col 1 with erase eol.
     move     WS-unit6 to WS-qty.
     if       Stock-Pre-Sales < WS-Qty
              move     zero  to Stock-Pre-Sales
     else
              subtract WS-Qty from Stock-Pre-Sales.
*>
     if       WS-sign6 = "-"
              move   1 to Audit-Reverse-Transaction
              multiply -1 by WS-qty.
*>
     if       WS-qty + Stock-Held < zero
              display ST206 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ba020-Accept-Qty.
*>
*> If zero, issue caution and continue so it stays displayed until next line processed
*>
     if       WS-qty + Stock-Held = zero
              display ST208 at line WS-23-lines col 1 with foreground-color 4 highlight
              display ST006   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30.
*>
 ba030-Accept-Price.
     move     48 to cole.
     perform  zz200-accept-money6a thru zz200-accept-money6b.
     if       amt-ok6 = zero
              go to ba020-Accept-Qty.
     move     amt-ok6 to WS-price.
*>
*>  Got it all now, so process it.
*>
     if       Stk-Audit-Used = 1
              move     1 to Audit-Type         *> Additions
              move     WS-Stock-Key  to Audit-Stock-Key
              move     WS-Stock-Desc to Audit-Desc
              move     WS-qty        to Audit-Transaction-Qty
              move     WS-price      to Audit-Unit-Cost
     end-if
     move     WS-price to Stock-Last-Actual-Cost.
     if       Stock-Held not = zero
          or  Stock-Work-in-Progress not = zero
              compute WS-Old-Value = (Stock-Held + Stock-Work-in-Progress) * Stock-Cost
     else
              move zero to WS-Old-Value.
*>
     multiply WS-Qty by WS-Price giving WS-Value.
     if       Stk-Audit-Used = 1
              move     WS-Value to Audit-Stock-Value-Change.
     add      WS-Value WS-Old-Value giving WS-New-Value   on size error
              display ST212 at line WS-23-lines col 1 with foreground-color 4 highlight
              move 99999999.99 to WS-New-Value.
*>
*> Display updated quantity
*>
     add      WS-Qty Stock-Held giving WS-New-Qty.
     move     WS-New-Qty to WS-z6.
     move     59 to cole.
     display  WS-z6 at curs with foreground-color 3.
*>
*> Now for updating stock value
*>
     if       not Stock-Averaging
              move 68 to cole
              move WS-new-value to amt-ok8
              perform zz200-accept-money8c
              if    amt-ok8 not = zero
                    move amt-ok8 to WS-new-value.
*>
     divide   WS-New-Qty into WS-New-Value giving WS-New-Cost rounded.
*>
     if       Stock-Averaging
              move 67 to cole
              display "{           }" at curs with foreground-color 2
              add 1 to cole
              move WS-new-value  to amt-ok8
              move amt-wk-pds8   to WS-pound8
              move amt-wk-pence8 to WS-pence8
              display WS-amount-screen-display8 at curs with foreground-color 3.
*>
     if       Stk-Audit-Used = 1
              move Stk-Audit-No to Audit-No
              perform  zz900-Read-System-Param  *> 05/01/25
              move     zero      to Stk-Activity-Rep-Run
              perform  zz910-Rewrite-System-Param  *> 05/01/25
              move WS-Proc-Date to Audit-Process-Date
              perform  Stock-Audit-Write
              if    FS-Reply not = zero
                    display ST002 at line WS-23-lines col 1 with foreground-color 4 highlight
                    display FS-Reply at line WS-23-lines col 38 with foreground-color 2 highlight
                    display ST003   at line WS-lines col 01
                    accept WS-reply at line WS-lines col 30
                    go to ba999-Exit.
*>
*> WS-Qty can be negative
*>
     if       WS-Qty > zero
              subtract WS-Qty from Stock-On-Order
     else
              add WS-Qty to Stock-On-Order.
*>
     if       Stock-On-Order not = zero
              add Stock-On-Order to Stock-Back-Ordered
              move zero to Stock-On-Order.
*>
     if       Stock-Back-Ordered < zero
              move zero to Stock-Back-Ordered.
*>
*>  Accumulate Month and Year to Date (TD) quantities.
*>
     add      WS-Qty to Stock-Adds.
     add      WS-Qty to Stock-TD-Adds (ws-Proc-Mth).
     if       Stock-Adds < 1
              display ST215 at line WS-23-lines col 1 with foreground-color 4 highlight.
     if       Stock-TD-Adds (ws-Proc-Mth) < 1
              display ST216 at line WS-23-lines col 41 with foreground-color 4 highlight.
*>
 ba040-Setup-Print-Transaction.
*>
*>  Print report line
*>
     move     spaces to line-4.
     move     WS-Proc-Date    to l4-Proc-Date.
     move     WS-Stock-Key    to l4-Stock-Number.
     move     WS-Stock-Desc   to l4-Desc.
     move     WS-Qty          to l4-Qty.
     move     WS-Price        to l4-Cost.
     move     WS-Value        to l4-New-Value.
*>
     move     spaces to u-date.
     move     Stock-Order-Date to u-bin.
     perform  zz060-Convert-Date.
     move     WS-date to l4-Date-Ordered.
*>
     move     spaces to u-date.
     move     Stock-Order-Due to u-bin.
     perform  zz060-Convert-Date.
     move     WS-date to l4-Date-Due.
*>
*> Work out days from order to today (assuming goods arrived today)
*>
     move     to-day to u-date.
     move     zero to u-bin.
     perform  maps04.
*>
*> This test should never happen - yeh right !
*>
     if       u-bin = zero
              display ST005 at line WS-23-lines col 1 with foreground-color 4 highlight
              display u-date at line WS-23-lines col 20 with foreground-color 2 highlight.
*>
     if       Stock-Order-Due = zero
              move spaces to l4-Lit-Late.
     if       Stock-Order-Due not = zero
              subtract Stock-Order-Due from u-bin giving WS-Days-Late
              if  WS-Days-Late > zero
                  move WS-Days-Late to l4-Days-Late
                  move " Days Late" to l4-Lit-Late
              else
               if WS-Days-Late < zero
                  move WS-Days-Late to l4-Days-Late
                  move " Days Early" to l4-Lit-Late.
*>
*> Clear due and ordered dates if ordered stock zero and print transaction
*>
     if       Stock-On-Order = zero
          and Stock-Back-Ordered = zero
              move zero to Stock-Order-Date Stock-Order-Due.
*>
     if       Line-Cnt > WS-Page-Lines
              perform zz010-Print-Heads.
     write    print-record from line-4 after 1.
     add      1 to Line-Cnt.
*>
*>  Update Stock Record
*>
     move     WS-New-Value to Stock-Value.
     move     WS-New-Qty   to Stock-Held.
     move     WS-New-Cost  to Stock-Cost.
     move     U-Bin        to Stock-Arrived-Date.
     perform  Stock-Rewrite.
     if       FS-Reply not = zero
              display ST000 at line WS-23-lines col 1 with foreground-color 4 highlight
              display FS-Reply at line WS-23-lines col 38 with foreground-color 2 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to ba999-Exit.
*>
*> Process any BO records that apply to stk item if BO-Flag set & u-bin = To-Day in days from 1601/01/01 as = 1
*> Stock record is currernt present / stored
*>
     if       Stock-Held not > zero
              go to ba010-Accept-Data1   *> More arrivals ?
     end-if
     if       Stock-Services-Flag not = "Y"
       and    WS-BO-Used
              move     "Y" to WS-BO-Can-Be-Used  *> Testing use WS-BO-Usable (Y)
              move     WS-Stock-Key to BO-Stk-Item-No
              start    BO-Stk-Itm-File  key = BO-Stk-Item-No
              if       FS-Reply not = zeros      *> No such item so process done
                       go to ba010-Accept-Data1
              end-if
              move     Stock-Held to WS-Temp-Stock-Held *> don't process if out of stock now based on BO recs
              perform  until exit
                       read     BO-Stk-Itm-File NEXT at end
                                exit perform
                       end-read
                       if       BO-Stk-Item-No not = WS-Stock-Key
                                exit perform cycle  *> JIC out of stk # order MAY BE SHOULD BE exit perform but JIC
                       end-if
                       if       FS-Reply not = zeros  *> no more recs
                                exit perform
                       end-if
*>
*> valid record but only update BO recs if still have stock - at least on paper :)
*> as stock received might be less than all BO requirements at this time
*>
                       if       WS-Temp-Stock-Held not < BO-Stk-BO-Qty
                          and   WS-Temp-Stock-Held not = zero
                                move     "Y"   to BO-Stk-Arrived-Flag
                                move     U-Bin to BO-Stk-BO-Arr-Date
                                subtract BO-Stk-BO-Qty from WS-Temp-Stock-Held
                                rewrite  BO-Stk-Itm-Record
                                if       FS-Reply not = zero
                                         display  ST221 at line WS-23-Lines col 10
                                                   with foreground-color 4 highlight beep erase eos
                                         display  ST006 at line WS-Lines    col 1
                                                   with foreground-color 2 highlight
                                         accept   WS-Reply at line WS-Lines col 32
                                         exit perform
                                end-if
                                exit perform cycle
                       end-if  *> out of stock so cannot proc any more BO recs of same stk #
              end-perform
     end-if.
*>
     go       to ba010-Accept-Data1.
*>
 ba999-Exit.
     exit     section.
*>
 ca000-Process-Manual-Deductions  section.
*>***************************************
*>
     perform  aa010-Display-Headings.
     display  " Stock Number    Description         Quantity    Stk Qty"
                                                  at 0301 with foreground-color 2.
     perform  varying lin from 5 by 1 until lin > WS-22-lines
              move    1 to cole
              display "[             ]" at curs with erase eol foreground-color 2
              move    16 to cole
              display "{                    }" at curs with foreground-color 2
              move    38 to cole
              display "[       ]"     at curs with foreground-color 2
              move    47 to cole
              display "{      }"      at curs with foreground-color 2
     end-perform
     move     4 to i.
*>
 ca010-Accept-Data1.
     add      1 to i.
     if       i > WS-22-lines
              perform ca000-Process-Manual-Deductions.  *> check for end of screen & reset
     move     spaces to WSD-Stock-Key.
     initialize WS-Stock-Audit-Record.
     move     2 to cole.
     move     i to lin.
     accept   WSD-Stock-Key at curs with foreground-color 3 update.
     if       WSD-Stock-Key = spaces
           or Cob-Crt-Status = Cob-Scr-Esc
              go to ca999-Exit.
*>
     move     function upper-case (WSD-Stock-Key) to WSD-Stock-Key.
*>
*>   Redisplay as uppercase then get the stock record but might have abbrev. no.
*>
     display  WSD-Stock-Key at curs with foreground-color 3.
     if       WSD-Stock-No-Long = spaces
              move WSD-Abrev-Stock to WS-Stock-Abrev-Key
              move   2 to File-Key-No
              perform Stock-Read-Indexed
              if     FS-Reply = 23 or = 21           *> invalid key but for RDB its 23
                     display ST203 at line WS-23-lines col 1 with foreground-color 4 highlight
                     subtract 1 from i
                     go to ca010-Accept-Data1
              end-if
     else
              move WSD-Stock-Key to WS-Stock-Key
              move   1 to File-Key-No
              perform Stock-Read-Indexed
              if     FS-Reply = 23 or = 21           *> invalid key but for RDB its 23
                     display ST214 at line WS-23-lines col 1 with foreground-color 4 highlight
                     subtract 1 from i
                     go to ca010-Accept-Data1
              end-if
     end-if
*>
*>  Have the required Stock record so get and show the desc
*>
     move     17 to cole.
     display  WS-Stock-Desc (1:20) at curs with foreground-color 3.
     move     48 to cole.
     add      Stock-Work-in-Progress Stock-Held giving WS-Z6.
     display  WS-Z6 at curs with foreground-color 3.
     display  " " at line WS-23-lines col 1 with erase eol.  *> clear any prior errors
*>
*>  Quantity to subtract from stock next
*>
 ca020-Accept-Qty.
     move     zero  to WS-unit6.
     move     space to WS-sign6
     move     39 to cole.
     accept   WS-Qty-Screen-Display6 at curs with foreground-color 3 update.
     if       WS-unit6 = zero
           or Cob-Crt-Status = Cob-Scr-Esc
           or Cob-Crt-Status = Cob-Scr-Key-Up
           or Cob-Crt-Status = Cob-Scr-Page-Up
              subtract 1 from i
              move 17 to cole
              display WS-spaces-20 at curs
              go to ca010-Accept-Data1.
*>
     if       WS-unit6 > 999998
              display ST204 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ca020-Accept-Qty.
     if       WS-sign6 not = "-" and not = space
              display ST207 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ca020-Accept-Qty.
*>
*> clear error line
*>
     display  " " at line WS-23-lines col 1 with erase eol.
     move     WS-unit6 to WS-qty.
     if       WS-sign6 = "-"
              move 1 to Audit-Reverse-Transaction
              multiply -1 by WS-qty
              if  (ws-unit6 + Stock-Held) > 999999
                  display ST205 at line WS-23-lines col 1 with foreground-color 4 highlight
                  go to ca020-Accept-Qty.
*>
     if       Stock-Held - WS-qty < zero
              display ST206 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ca020-Accept-Qty
     else
              display  " " at line WS-23-lines col 1 with erase eol.
*>
*> Check for Services only flag so ignore
*>
     if       Stock-Services-Flag = "Y"
              display ST217 at line WS-23-lines col 1 with foreground-color 2 highlight
              subtract 1 from i
              go to ca010-Accept-Data1.
*>
*> if zero, issue caution and continue
*>
     if       Stock-Held - WS-Qty = zero
              display ST208 at line WS-23-lines col 1 with foreground-color 4 highlight
              display ST006   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              display " " at line WS-23-lines col 1 with erase eos.
*>
     move     48 to cole.
     subtract WS-Qty from Stock-Held giving WS-New-Qty.   *> neg values should add
     move     WS-New-Qty to WS-Z6.
     display  WS-Z6 at curs with foreground-color 3.
*>
*>  Got it all now so process it.
*>
     move     2 to Audit-Type.         *> Deductions
     move     WS-Stock-Key to Audit-Stock-Key.
     move     WS-Stock-Desc to Audit-Desc.
     move     WS-qty to Audit-Transaction-Qty.
     move     Stock-Cost to Audit-Unit-Cost.              *> IS THIS NEEDED else set to zero
     compute  Audit-Stock-Value-Change = WS-Qty * Stock-Cost * -1.
*>
     move     Stk-Audit-No to Audit-No.
     if       Stk-Audit-Used = 1
              perform  zz900-Read-System-Param     *> 05/01/25
              move zero         to Stk-Activity-Rep-Run
              perform  zz910-Rewrite-System-Param  *> 05/01/25
              move WS-Proc-Date to Audit-Process-Date
              perform  Stock-Audit-Write
              if    FS-Reply not = zero
                    display ST002 at line WS-23-lines col 1 with foreground-color 4 highlight
                    display FS-Reply at line WS-23-lines col 38 with foreground-color 2 highlight
                    display ST003   at line WS-lines col 01
                    accept WS-reply at line WS-lines col 30
                    go to ca999-Exit.
*>
*>  Accumulate Month and Year to Date (TD) quantities.
*>
     add      WS-Qty to Stock-Deducts.
     add      WS-Qty to Stock-TD-Deds (ws-Proc-Mth).
     if       Stock-Deducts < 1
              display ST210 at line WS-23-lines col 1 with foreground-color 4 highlight.
     if       Stock-TD-Deds (ws-Proc-Mth) < 1
              display ST211 at line WS-23-lines col 41 with foreground-color 4 highlight.
*>
 ca040-Setup-Print-Transaction.
*>
*>  print report line
*>
     move     spaces    to line-4.
     move     WS-Proc-Date    to l4-Proc-Date.
     move     WS-Stock-Key    to l4-Stock-Number.
     move     WS-Stock-Desc   to l4-Desc.
     move     WS-Qty          to l4-Qty.
     move     Audit-Stock-Value-Change  to l4-New-Value.
*>
     if       Line-Cnt > WS-Page-Lines
              perform zz010-Print-Heads.
     write    print-record from line-4 after 1.
     add      1 to Line-Cnt.
*>
*>  Update Stock Record
*>
     subtract WS-Qty from Stock-Held.
*>                                             needed even for NO stock-averaging
     compute Stock-Value = (Stock-Held + Stock-Work-in-Progress) * Stock-Cost on size error
               display ST212 at line WS-23-lines col 1 with foreground-color 4 highlight
               move 99999999.99 to Stock-Value.
*>
     perform  Stock-Rewrite.
     if       FS-Reply not = zero
              display ST000 at line WS-23-lines col 1 with foreground-color 4 highlight
              display FS-Reply at line WS-23-lines col 38 with foreground-color 2 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to ca999-Exit.
*>
     go       to ca010-Accept-Data1.
*>
 ca999-Exit.
     exit     section.
*>
 da000-Process-Barcode-Additions   section.
*>****************************************
*>
*>  Check this AFTER RE-CODING <<<<<<<<<<<<<<<<<<<<<***<<<<<<<<<<<<<<<<<<<<<<<<<<
*>-----------------------------------------------------------------------------------
*>
*>   Coding taken from the additions routine ba000 with most of the code still present
*>    in case you need to modify it.
*>
*> This element just reads the bar code and adds 1 to qty & increases stock value
*>  by the last unit price paid or if zero then the unit average stock price assuming
*>    averaging is in use otherwise
*> stock value is not changed.
*>  that said code for accept quantity & unit price has been left in but is bypassed
*>  and the bar codes are read in showing the normal manual display screen.
*>
*> It is assumed that the code reader is connected to the USB or keyboard PS/2 port
*>  and the scanned barcode is read as if coming from a keyboard with a CR (carriage return)
*> as tested using a WASP WLR8900 CCD LR (long range) USB scanner available from Wasp
*> Technologies Inc which are available in the UK and Europe. See SC manual for
*> additional information.
*> While this specific reader reads one code at a time and passes
*> the resulting code to the program along with CR some versions can hold in their memory
*> many hundreds of such codes each again, ending with a CR. The code as supplied still
*> supports that.
*>
*> Note that the scanners may need to be programmed to end each scanned barcode with a CR.
*> See the specific scanner manual for the method,
*> Another point: Some scanners also have a numeric keypad on them so the user can input a
*> product quantity. This module would need changing to support this.
*>
*> For all support to program or for programming a module/program to process bar code data,
*>  or for that matter any other changes or additions, a request should be made
*>  to Applewood Computers with details of hardware used, i.e., make, model & specs of
*>  bar code readers in use and data produced. This is a chargeable service.
*>
*> For contact details please see supplied manuals inside front page.
*>-----------------------------------------------------------------------------------
*>
     perform  aa010-Display-Headings.
     display  " Stock Number    Description         Quantity    Price   Stk Qty   Stk Value"
                                                  at 0301 with foreground-color 2.
     perform  varying lin from 5 by 1 until lin > WS-22-lines
              move    1 to cole
              display "[             ]" at curs with erase eol foreground-color 2
              move    16 to cole
              display "{                    }" at curs with foreground-color 2
              move    38 to cole
              display "[       ]"     at curs with foreground-color 2
              move    47 to cole
              display "[         ]"   at curs with foreground-color 2
              move    58 to cole
              display "{      }"      at curs with foreground-color 2
              move    67 to cole
              display "[           ]" at curs with foreground-color 2
     end-perform
     move     4 to i.
*>
 da010-Accept-Data1.
     add      1 to i.
     if       i > WS-22-lines                          *> check for end of screen & reset
              perform da000-Process-Barcode-Additions. *> by rerunning paragraph code.
     move     spaces to WSD-Stock-Key.
     initialize WS-Stock-Audit-Record.
     move     2 to cole.
     move     i to lin.
     accept   WSD-Stock-Key at curs with foreground-color 3 update.
     if       WSD-Stock-Key = spaces
           or Cob-Crt-Status = Cob-Scr-Esc
              go to da999-Exit.
*>
     move     function upper-case (WSD-Stock-Key) to WSD-Stock-Key.
*>
*>   Redisplay as uppercase then get the stock record but redundant as using barcodes.
*>
     display  WSD-Stock-Key at curs with foreground-color 3.
     move     WSD-Stock-Key to WS-Stock-Key
     move   1 to File-Key-No
     perform Stock-Read-Indexed
     if     FS-Reply = 23 or = 21           *> invalid key but for RDB its 23
            display ST214 at line WS-23-lines col 1 with foreground-color 4 highlight
            display "Missing Stock Record" at curs with foreground-color 3 highlight blink
            go to da010-Accept-Data1
     end-if
*>
*>  Have the required Stock record so get and show the desc
*>
     move     17 to cole.
     display  WS-Stock-Desc (1:20) at curs with foreground-color 3.
*>
*> Check for Services only flag so ignore
*>
     if       Stock-Services-Flag = "Y"
              display ST217 at line WS-23-lines col 1 with foreground-color 2 highlight
              display WS-spaces-20 at curs
              go to da010-Accept-Data1.
     display  " " at line WS-23-lines col 1 with erase eol.  *> clear any prior errors
*>
*> Bypass accept quantity but set as 1 and use filed last price paid for unit price
*>
     move     1 to WS-qty
                   WS-unit6.
     if       Stock-Last-Actual-Cost not = zero
              move  Stock-Last-Actual-Cost to Amt-ok6
                                              WS-price
     else
              move  Stock-Cost  to Amt-ok6
                                   WS-price.
*>
     move     39 to cole.
     display  WS-Qty-Screen-Display6 at curs with foreground-color 3.
     go       to da030-Accept-Price.
*>
*> da020 is bypassed as quantity 1 is 'assumed' for basic barcode readers.
*>
*>  Quantity to add to stock next but use whats on order as guide
*>
 da020-Accept-Qty.
     move     Stock-On-Order to WS-unit6.
     move     space to WS-sign6.
     move     39 to cole.
     accept   WS-Qty-Screen-Display6 at curs with foreground-color 3 update.
     if       WS-unit6 = zero
           or Cob-Crt-Status = Cob-Scr-Esc
           or Cob-Crt-Status = Cob-Scr-Key-Up
           or Cob-Crt-Status = Cob-Scr-Page-Up
              subtract 1 from i
              move 17 to cole
              display WS-spaces-20 at curs
              go to da010-Accept-Data1.
*>
     if       WS-unit6 > 999998
              display ST204 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to da020-Accept-Qty.
     if       (ws-unit6 + Stock-Held) > 999999
              display ST205 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to da020-Accept-Qty.
     if       WS-sign6 not = "-" and not = space
              display ST207 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to da020-Accept-Qty.
*>
*> Clear error line
*>
     display  " " at line WS-23-lines col 1 with erase eol.
     move     WS-unit6 to WS-qty.
     if       Stock-Pre-Sales < WS-Qty
              move     zero  to Stock-Pre-Sales
     else
              subtract WS-Qty from Stock-Pre-Sales.
*>
     if       WS-sign6 = "-"
              move 1 to Audit-Reverse-Transaction
              multiply -1 by WS-qty.
*>
     if       WS-qty + Stock-Held < zero
              display ST206 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to da020-Accept-Qty.
*>
*> If zero, issue caution and continue so it stays displayed until next line processed
*>
     if       WS-qty + Stock-Held = zero
              display ST208 at line WS-23-lines col 1 with foreground-color 4 highlight
              display ST006   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30.
*>
 da030-Accept-Price.
*>
*> Code bypassed but using Stock-Last-Actual-Cost & update stock value if used otherwise zero
*>   with no stock value update
*>
*>??     if       not Stock-Averaging
*>??              move zero to WS-Price
*>??                           WS-Value
*>??     go       to
*>
     move     48 to cole.
     move     amt-wk-pence6 to WS-pence6.
     move     amt-wk-pds6 to WS-pound6.
     display  WS-amount-screen-display6 at curs with foreground-color 3.
*>
*>
*>     perform  zz200-accept-money6c.
*>     if       amt-ok6 = zero
*>              go to da020-Accept-Qty.
*>     move     amt-ok6 to WS-price.
*>
*>  Got it all now so process it.
*>
     if       Stk-Audit-Used = 1
              move     1 to Audit-Type         *> Additions
              move     WS-Stock-Key to Audit-Stock-Key
              move     WS-Stock-Desc to Audit-Desc
              move     WS-qty to Audit-Transaction-Qty
              move     WS-price to Audit-Unit-Cost
     end-if
     move     WS-price to Stock-Last-Actual-Cost.
     if       Stock-Held not = zero
          or  Stock-Work-in-Progress not = zero
              compute WS-Old-Value = (Stock-Held + Stock-Work-in-Progress) * Stock-Cost
     else
              move zero to WS-Old-Value.
*>
     multiply WS-Qty by WS-Price giving WS-Value.
     if       Stk-Audit-Used = 1
              move     WS-Value to Audit-Stock-Value-Change.
     add      WS-Value WS-Old-Value giving WS-New-Value   on size error
              display ST212 at line WS-23-lines col 1 with foreground-color 4 highlight
              move 99999999.99 to WS-New-Value.
*>
*> Display updated quantity
*>
     add      WS-Qty Stock-Held giving WS-New-Qty.
     move     WS-New-Qty to WS-z6.
     move     59 to cole.
     display  WS-z6 at curs with foreground-color 3.
*>
*> Now for updating stock value
*>
     if       not Stock-Averaging
              move 68 to cole
              move WS-new-value to amt-ok8
              perform zz200-accept-money8c
              if    amt-ok8 not = zero
                    move amt-ok8 to WS-new-value.
*>
     divide   WS-New-Qty into WS-New-Value giving WS-New-Cost rounded.
*>
     if       Stock-Averaging
              move 67 to cole
              display "{           }" at curs with foreground-color 2
              add 1 to cole
              move WS-new-value to amt-ok8
              move amt-wk-pds8   to WS-pound8
              move amt-wk-pence8 to WS-pence8
              display WS-amount-screen-display8 at curs with foreground-color 3.
*>
     if       Stk-Audit-Used = 1
              move Stk-Audit-No to Audit-No
              perform  zz900-Read-System-Param     *> 05/01/25
              move zero         to Stk-Activity-Rep-Run
              perform  zz910-Rewrite-System-Param  *> 05/01/25
              move WS-Proc-Date to Audit-Process-Date
              perform  Stock-Audit-Write
              if    FS-Reply not = zero
                    display ST002 at line WS-23-lines col 1 with foreground-color 4 highlight
                    display FS-Reply at line WS-23-lines col 38 with foreground-color 2 highlight
                    display ST003   at line WS-lines col 01
                    accept WS-reply at line WS-lines col 30
                    go to da999-Exit.
*>
*> WS-Qty can be negative
*>
     if       WS-Qty > zero
              subtract WS-Qty from Stock-On-Order
     else
              add WS-Qty to Stock-On-Order.
*>
     if       Stock-On-Order not = zero
              add Stock-On-Order to Stock-Back-Ordered
              move zero to Stock-On-Order.
*>
     if       Stock-Back-Ordered < zero
              move zero to Stock-Back-Ordered.
*>
*>  Accumulate Month and Year to Date (TD) quantities.
*>
     add      WS-Qty to Stock-Adds.
     add      WS-Qty to Stock-TD-Adds (ws-Proc-Mth).
     if       Stock-Adds < 1
              display ST215 at line WS-23-lines col  1 with foreground-color 4 highlight.
     if       Stock-TD-Adds (ws-Proc-Mth) < 1
              display ST216 at line WS-23-lines col 41 with foreground-color 4 highlight.
*>
 da040-Setup-Print-Transaction.
*>
*>  Print report line
*>
     move     spaces to line-4.
     move     WS-Proc-Date to l4-Proc-Date.
     move     WS-Stock-Key    to l4-Stock-Number.
     move     WS-Stock-Desc   to l4-Desc.
     move     WS-Qty       to l4-Qty.
     move     WS-Price     to l4-Cost.
     move     WS-Value     to l4-New-Value.
*>
     move     spaces to u-date.
     move     Stock-Order-Date to u-bin.
     perform  zz060-Convert-Date.
     move     WS-date to l4-Date-Ordered.
*>
     move     spaces to u-date.
     move     Stock-Order-Due to u-bin.
     perform  zz060-Convert-Date.
     move     WS-date to l4-Date-Due.
*>
*> Work out days from order to today (assuming goods arrived today)
*>
     move     to-day to u-date.
     move     zero to u-bin.
     perform  maps04.
*>
*> This test should never happen
*>
     if       u-bin = zero
              display ST005  at line WS-23-lines col  1 with foreground-color 4 highlight
              display u-date at line WS-23-lines col 20 with foreground-color 2 highlight.
*>
     if       Stock-Order-Due = zero
              move spaces to l4-Lit-Late.
     if       Stock-Order-Due not = zero
              subtract Stock-Order-Due from u-bin giving WS-Days-Late
              if  WS-Days-Late > zero
                  move WS-Days-Late to l4-Days-Late
                  move " Days Late" to l4-Lit-Late
              else
               if WS-Days-Late < zero
                  move WS-Days-Late to l4-Days-Late
                  move " Days Early" to l4-Lit-Late.
*>
*> Clear due and ordered dates if ordered stock zero and print transaction
*>
     if       Stock-On-Order = zero
          and Stock-Back-Ordered = zero
              move zero to Stock-Order-Date Stock-Order-Due.
*>
     if       Line-Cnt > WS-Page-Lines
              perform zz010-Print-Heads.
     write    print-record from line-4 after 1.
     add      1 to Line-Cnt.
*>
*>  Update Stock Record
*>
     move     WS-New-Value to Stock-Value.
     move     WS-New-Qty   to Stock-Held.
     move     WS-New-Cost  to Stock-Cost.
     move     U-Bin      to Stock-Arrived-Date.
     perform  Stock-Rewrite.
     if       FS-Reply not = zero
              display ST000    at line WS-23-lines col  1 with foreground-color 4 highlight
              display FS-Reply at line WS-23-lines col 38 with foreground-color 2 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to da999-Exit.
*>
*> Process any BO records that apply to stk item if BO-Flag set & u-bin = To-Day in days from 1601/01/01 as = 1
*>
     if       Stock-Held not > zero
              go to da010-Accept-Data1
     end-if
     if       Stock-Services-Flag not = "Y"
       and    WS-BO-Used
              move  "Y" to WS-BO-Can-Be-Used  *> Testing use WS-BO-Usable (Y)
              move  WS-Stock-Key to BO-Stk-Item-No
              start BO-Stk-Itm-File  key = BO-Stk-Item-No
              if    FS-Reply not = zeros    *> No such item
                    go to da010-Accept-Data1
              end-if
              move     Stock-Held to WS-Temp-Stock-Held *> don't process if out of stock now based on BO recs
              perform  until exit
                       read     BO-Stk-Itm-File NEXT at end
                                exit perform
                       end-read
                       if       BO-Stk-Item-No not = WS-Stock-Key
                                exit perform cycle     *> JIC out of stk # order
                       end-if
                       if       FS-Reply not = zeros
                                exit perform
                       end-if
*> valid record but only update BO recs if still have stock - at least on paper :)
                       if       WS-Temp-Stock-Held not < BO-Stk-BO-Qty and
                                WS-Temp-Stock-Held not = zero
                                move     "Y"   to BO-Stk-Arrived-Flag
                                move     U-Bin to BO-Stk-BO-Arr-Date
                                subtract BO-Stk-BO-Qty from WS-Temp-Stock-Held
                                rewrite  BO-Stk-Itm-Record
                                if       FS-Reply not = zero
                                         display  ST221 at line WS-23-Lines col 10
                                                   with foreground-color 4 highlight beep erase eos
                                         display  ST006 at line WS-Lines    col 1
                                                   with foreground-color 2 highlight
                                         accept   WS-Reply at line WS-Lines col 32
                                         exit perform
                                end-if
                                exit perform cycle
                       end-if  *> out of stock so cannot proc any more BO recs of same stk #
              end-perform
     end-if.
*>
     go       to da010-Accept-Data1.
*>
 da999-Exit.
     exit     section.
*>
 ea000-Process-End-of-Month  section.
*>**********************************
*>
*> New code for processing records from invoicing in Sales & if present update
*>   stock values in stock file.
*> and purchase order receipts if and when implemented.
*>
     display  "Printing" at 1337 with erase eos.
     open     output Print-File.
     perform  ea100-Print-Additions.
 *>    close    Print-File.               *> Force separate reports in case of double sided printing
 *>    if       Page-Nos not = zero
 *>             call  "SYSTEM" using Print-Report.
 *>    open     output Print-File.
     perform  ea200-Print-Deductions.
     close    Print-File.
     if       Page-Nos not = zero
              call  "SYSTEM" using Print-Report.
     perform  zz900-Read-System-Param.     *> 05/01/25
     move     1   to Stk-Activity-Rep-Run.
     perform  zz910-Rewrite-System-Param.  *> 05/01/25
*>
 ea010-Accept-Delete.
     if       WS-Process-Func = 5
              go to ea020-Bypass-Displays.
     move     "N" to WS-Reply.
     display  "Can I Delete the Audit File Now? [ ]" at 0401 with foreground-color 2 erase eos.
     display  " Making sure that Sales Invoicing and Purchase Ledger are NOT running"
                                                     at 0601 with foreground-color 4 highlight.
     display  "Check that Reports are complete first, before responding"
                                                     at 0802 with foreground-color 4 highlight blink.
     accept   WS-Reply at 0435 with foreground-color 3 update.
     move     function upper-case (ws-Reply) to WS-Reply.
     if       WS-Reply = "N"
              go to ea999-Exit.
     if       WS-Reply not = "Y"
              go to ea010-Accept-Delete.
*>
 ea020-Bypass-Displays.
     perform  Stock-Audit-Close.
     perform  Stock-Audit-Open-Output.
     perform  zz900-Read-System-Param. *> 05/01/25
     add      1 to Stk-Audit-No on size error
              move 1 to Stk-Audit-No.
     perform  zz910-Rewrite-System-Param. *> 05/01/25
*>
 ea999-Exit.
     exit     section.
*>
 ea100-Print-Additions     section.
*>********************************
*>
     perform  Stock-Audit-Close.
     perform  Stock-Audit-Open-Input.
     move     zero to Page-Nos WS-add-total WS-ded-total.
     move     99 to Line-Cnt.
     move     "Additions Stock Audit Report" to l1-Title.
     move     "Proc. Date" to l3-Proc-Lit.
     move     "Price"      to l3-Price-Lit.
     move     "    Stock Value    " to l3-Stock-Lit.
*>     move     spaces to l3-Dates-Lit.
     move    "Source/PO.no."  to l3-Dates-Lit.
     move     spaces to line-4.
*>
 ea110-Read-Record.
     perform  Stock-Audit-Read-Next.
     if       FS-Reply = 10     *> EOF
              go to ea120-Totals.
*>
*> Could have batch headers but not in use at this time
*>
     if       Del-Record or SL-Del-Record or SL-Credit-Record
              add  Audit-Stock-Value-Change to WS-Ded-Total.
*>
     if       not Add-Record and not PL-Add-Record
              go to ea110-Read-Record.
     move     Audit-Stock-Key          to l4-Stock-Number.
     move     Audit-Desc               to l4-Desc.
     move     Audit-Transaction-Qty    to l4-Qty.
     move     Audit-Unit-Cost          to l4-Cost.
     move     Audit-Stock-Value-Change to l4-New-Value.
     move     Audit-Process-Date       to l4-Proc-Date.
     add      Audit-Stock-Value-Change to WS-Add-Total.
     move     spaces                   to l4-Source.
     if       PL-Add-Record
              string "Purchasing/"     delimited by size
                     Audit-Invoice-PO  delimited by size
                                          into l4-Source.
*>
     if       Line-Cnt > WS-Page-Lines
              perform zz010-Print-Heads.
     write    Print-Record from line-4 after 1.
     add      1 to Line-Cnt.
     go       to ea110-Read-Record.
*>
 ea120-Totals.
     if       Line-Cnt > WS-Page-Lines - 7
              perform zz010-Print-Heads.
     move     spaces to Print-Record.
     move     WS-Add-Total to WS-Total.
     move     56 to a.
     string   " Total Additions   " delimited by size
              WS-Total              delimited by size into Print-Record pointer a.
     write    Print-Record after 3.
     move     spaces to Print-Record.
     move     WS-Ded-Total to WS-Total.
     move     56 to a.
     string   " Total Deductions  " delimited by size
              WS-Total              delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
     move     spaces to Print-Record (56:35).
     move     75 to a.
     string   "-------------- " delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
     add      WS-Add-Total WS-Ded-Total giving WS-Total.
     move     56 to a.
     string   " Total Changes     " delimited by size
              WS-Total              delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
     move     spaces to Print-Record (56:35).
     move     75 to a.
     string   "============== "  delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
*>
 ea199-Exit.
     exit     section.
*>
 ea200-Print-Deductions    section.
*>********************************
*>
     perform  Stock-Audit-Close.
     perform  Stock-Audit-Open-Input.
*>
*> Do a page feed if page-no is odd so new report starts on a new
*>  physical page assuming not using matrix printer - fairly safe these days.
*>
     if       Line-Cnt > 4 and  *> might be heads and totals.
              (Page-Nos = 1 or 3 or 5 or 7 or 9 or 11 or 13 or 15 or 17 or 19)
              move     spaces to Print-Record
              write    Print-Record before page.
*>
     move     zero to Page-Nos.
     move     99 to Line-Cnt.
     move     "Deductions Stock Audit Report" to l1-Title.
     move     "Proc. Date"          to l3-Proc-Lit.
     move     "    Stock Value    " to l3-Stock-Lit.
     move     spaces to l3-Dates-Lit.
*>     move     spaces to l3-Price-Lit.
     move    "Source/Inv.no."  to l3-Dates-Lit.
     move     spaces to line-4.
*>
 ea210-Read-Record.
     perform  Stock-Audit-Read-Next.
     if       FS-Reply = 10    *> EOF
              go to ea220-Totals.
*>
     if       not Del-record
          and not SL-Del-Record
          and not SL-Credit-Record
              go to ea210-Read-Record.
     move     Audit-Stock-Key          to l4-Stock-Number.
     move     Audit-Desc               to l4-Desc.
     move     Audit-Transaction-Qty    to l4-Qty.
     move     Audit-Stock-Value-Change to l4-New-Value.
     move     Audit-Process-Date       to l4-Proc-Date.
     move     spaces to l4-Source.
     if       SL-Del-Record
              string "Invoicing/"     delimited by size
                     Audit-Invoice-PO delimited by size
                                       into l4-Source.
     if       SL-Credit-Record
              string "Credit note/"       delimited by size
                     Audit-Invoice-PO     delimited by size
                     " for "              delimited by size
                     Audit-Cr-for-Invoice delimited by size
                                       into l4-Source.
*>
     if       Line-Cnt > WS-Page-Lines
              perform zz010-Print-Heads.
     write    print-record from line-4 after 1.
     add      1 to Line-Cnt.
     go       to ea210-Read-Record.
*>
 ea220-Totals.
     if       Line-Cnt > WS-Page-Lines - 7
              perform zz010-Print-Heads.
     move     spaces to Print-Record.
     move     WS-Add-Total to WS-Total.
     move     56 to a.
     string   " Total Additions   " delimited by size
              WS-Total              delimited by size into Print-Record pointer a.
     write    Print-Record after 3.
     move     spaces to Print-Record.
     move     WS-Ded-Total to WS-Total.
     move     56 to a.
     string   " Total Deductions  " delimited by size
              WS-Total              delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
     move     spaces to Print-Record (56:35).
     move     75 to a.
     string   "-------------- " delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
     add      WS-Add-Total WS-Ded-Total giving WS-Total.   *> THIS ASSUMES THAT DED IS NEG?
     move     56 to a.
     string   " Total Changes     " delimited by size
              WS-Total              delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
     move     75 to a.
     move     spaces to Print-Record (56:35).
     string   "============== "  delimited by size into Print-Record pointer a.
     write    Print-Record after 1.
*>
 ea299-Exit.
     exit     section.
*>
 fa000-Process-Orders   section.
*>*****************************
*>
*> Note that audit file is NOT updated only the stock file and that this process
*> replaces data, ie, quantities are REPLACED not added to
*>------------------------------------------------------------------------------
*>  So it is only used when Purchase Ledger is NOT passing this information on
*>   to Stock Control (or is not used).
*>
     perform  aa010-Display-Headings.
     display  " Stock Number   Description          Qty Ord Date Ordered  Date Due  " &
              "Back Qty"                at 0301 with foreground-color 2.
     perform  varying lin from 5 by 1 until lin > WS-22-lines
              move    1 to cole
              display "[             ]" at curs with erase eol foreground-color 2 *> stock no.
              move    16 to cole
              display "{                    }" at curs with foreground-color 2 *> desc (disp)
              move    38 to cole
              display "[      ]"       at curs with foreground-color 2  *> qty ordered
              move    46 to cole
              display "[          ]"   at curs with foreground-color 2  *> date ordered
              move    58 to cole
              display "[          ]"   at curs with foreground-color 2  *> date Due
              move    70 to cole
              display "[      ]"       at curs with foreground-color 2  *> qty B'ord
     end-perform
     move     4 to i.
*>
 fa010-Accept-Data1.
     add      1 to i.
     if       i > WS-22-lines                        *> check for end of screen & redraw
              perform fa000-Process-Orders.
     move     spaces to WSD-Stock-Key.
     move     2 to cole.
     move     i to lin.
     accept   WSD-Stock-Key at curs with foreground-color 3 update.
     if       WSD-Stock-Key = spaces
           or Cob-Crt-Status = Cob-Scr-Esc
              go to fa999-Exit.
*>
     move     function upper-case (WSD-Stock-Key) to WSD-Stock-Key.
*>
*>   Redisplay as uppercase then get the stock record but might have abbrev. no.
*>
     display  WSD-Stock-Key at curs with foreground-color 3.
     if       WSD-Stock-No-Long = spaces
              move WSD-Abrev-Stock to WS-Stock-Abrev-Key
              move   2 to File-Key-No
              perform Stock-Read-Indexed
              if     FS-Reply = 23 or = 21
                     display ST203 at line WS-23-lines col 1 with foreground-color 4 highlight
                     subtract 1 from i
                     go to fa010-Accept-Data1
              end-if
     else
              move WSD-Stock-Key to WS-Stock-Key
              move     1 to File-Key-No             *>  1=stock-key, 2=Abrev, 3=Desc
              perform  Stock-Read-Indexed
              if     FS-Reply = 23 or = 21           *> invalid key but for RDB its 23
                     display ST214 at line WS-23-lines col 1 with foreground-color 4 highlight
                     subtract 1 from i
                     go to fa010-Accept-Data1
              end-if
     end-if
*>
*>  Have the required Stock record so get and show the desc
*>
     move     17 to cole.
     display  WS-Stock-Desc (1:20) at curs with foreground-color 3.
*>
*> Check for Services only flag so ignore
*>
     if       Stock-Services-Flag = "Y"
              display ST217 at line WS-23-lines col 1 with foreground-color 2 highlight
              display WS-spaces-20 at curs
              subtract 1 from i
              go to fa010-Accept-Data1.
     display  " " at line WS-23-lines col 1 with erase eol.  *> clear any prior errors
     move     space to WS-sign6.
*>
*>  Quantity on order
*>
 fa020-Accept-Qty.
     move     Stock-On-Order to WS-unit6.
     move     39 to cole.
     accept   WS-unit6 at curs with foreground-color 3 update.
     if       Cob-Crt-Status = Cob-Scr-Esc
           or Cob-Crt-Status = Cob-Scr-Key-Up
           or Cob-Crt-Status = Cob-Scr-Page-Up
              subtract 1 from i
              move 17 to cole
              display WS-spaces-20 at curs
              go to fa010-Accept-Data1.
*>
     if       WS-unit6 > 999998
              display ST204 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to fa020-Accept-Qty.
*>
*> Clear error line
*>
     display  " " at line WS-23-lines col 1 with erase eol.
     move     WS-unit6 to Stock-On-Order.
*>
*> Convert dates pre display and accept
*>
     if       Stock-Order-Date not = zero
              move Stock-Order-Date to u-bin
              perform zz060-Convert-Date
              move WS-date to WS-Stock-Order-Date
     else
              move spaces to WS-Stock-Order-Date
     end-if
     if       Stock-Order-Due not = zero
              move Stock-Order-Due to u-bin
              perform zz060-Convert-Date
              move WS-date to WS-Stock-Order-Due
     else
              move spaces to WS-Stock-Order-Due
     end-if.
*>
 fa030-Accept-Date-Ord.
     move     47 to Cole.
     accept   WS-Stock-Order-Date at curs with foreground-color 3 update.
     if       WS-Stock-Order-Date not = spaces
              move WS-Stock-Order-Date to WS-Test-Date
              perform zz050-Validate-Date
              if u-bin not = zero
                 move u-bin to Stock-Order-Date
              else
                 display ST005 at line WS-23-lines col 1  with foreground-color 4 highlight
                 display ST250 at line WS-23-lines col 19 with foreground-color 4 highlight
                 go to fa030-Accept-Date-Ord
     else
              move zero to Stock-Order-Date.
*>
 fa040-Accept-Date-Due.
     move     59 to Cole.
     accept   WS-Stock-Order-Due at curs with foreground-color 3 update.
     if       WS-Stock-Order-Due not = spaces
              move WS-Stock-Order-Due to WS-Test-Date
              perform zz050-Validate-Date
              if       u-bin not = zero
                       move u-bin to Stock-Order-Due
              else
                       display ST005 at line WS-23-lines col 1  with foreground-color 4 highlight
                       display ST251 at line WS-23-lines col 19 with foreground-color 4 highlight
                       go to fa040-Accept-Date-Due
              end-if        *> 16/08/23 as it looks messy and wrong without it
     else
              move zero to Stock-Order-Due.
*>
     display  " " at line WS-23-lines col 1 with erase eol.
*>
 fa050-Accept-B-ord.
     move     Stock-Back-Ordered to WS-unit6.
     move     71 to cole.
     accept   WS-unit6 at curs with foreground-color 3 update.
*>
     if       WS-unit6 > 999998
              display ST204 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to fa050-Accept-B-ord.
*>
*> Clear error line
*>
     display  " " at line WS-23-lines col 1 with erase eol.
     move     WS-unit6 to Stock-Back-Ordered.
*>
 fa060-Setup-Print-Transaction.
*>
*>  Print report line
*>
     move     spaces to line-4.
     move     WS-Stock-Key       to l4-Stock-Number.
     move     WS-Stock-Desc      to l4-Desc.
     move     Stock-On-Order     to l4-Qty.
     move     Stock-Back-Ordered to l4-Qty-B-ord.
*>
     move     spaces to u-date.
     move     Stock-Order-Date to u-bin.
     perform  zz060-Convert-Date.
     move     WS-date to l4-Date-Ordered.
*>
     move     spaces to u-date.
     move     Stock-Order-Due to u-bin.
     perform  zz060-Convert-Date.
     move     WS-date to l4-Date-Due.
*>
     if       Line-Cnt > WS-Page-Lines
              perform zz010-Print-Heads.
     write    print-record from line-4 after 1.
     add      1 to Line-Cnt.
*>
*>  Update Stock Record
*>
     perform  Stock-Rewrite.
     if       FS-Reply not = zero
              display ST000 at line WS-23-lines col 1 with foreground-color 4 highlight
              display FS-Reply at line WS-23-lines col 38 with foreground-color 2 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to fa999-Exit.
*>
     go       to fa010-Accept-Data1.
*>
 fa999-Exit.
     exit     section.
*>
 zz010-Print-Heads         section.
*>********************************
*>
     if       Line-Cnt not > WS-Page-Lines
              go to zz010-Exit.
     move     prog-name to l1-Program.
     add      1 to Page-Nos.
     move     Page-Nos to l1-Page.
     move     Usera to l2-User.
     perform  zz070-Convert-Date.
     move     WS-date to l2-Date.
     accept   hdtime from time.
     if       hdtime not = "00000000"
              move hd-hh to l2-HH
              move hd-mm to l2-MM.
     if       Page-Nos not = 1
              write print-record from Line-1 after page
              write print-record from Line-2 after 1
              move  spaces to print-record
              write print-record after 1
     else
              write print-record from Line-1 before 1
              write print-record from Line-2 before 1
     end-if
     move     6 to Line-Cnt.
     if       Menu-Reply not = 5
              write print-record from Line-3 after 1
     else
              subtract 1 from Line-Cnt.
     write    print-record from Line-3b after 1.
     move     spaces to print-record.
     write    print-record after 1.
*>
 zz010-Exit.
     Exit     section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-test-date
*> output:  u-date/ws-date as uk date format
*>          u-bin not zero if valid date
*>
     move     WS-test-date to WS-date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-test-date.
     if       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              go to zz050-test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to WS-date.  *> swap Intl to UK form
     move     WS-test-date (1:4) to WS-Year.
     move     WS-test-date (6:2) to WS-Month.
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
 zz100-test-escape          section.
*>*********************************
*>
     display  escape-code at 1876 with foreground-color 6.
*>
 zz100-get-escape.
     accept   escape-code at 1876 with foreground-color 6 update.
     move     function upper-case (escape-code) to escape-code.
*>
     if       escape-code not = "B" and not = "S" and not = "Q"
                      and not = "K" and not = "D"
              go to zz100-get-escape.
*>
 zz100-exit.
     exit     section.
*>
 zz200-comm-routines section.
*>**************************
*>
 zz200-accept-money6a.
     move     zero to WS-poundsd6 WS-penced6 amt-ok6.
*>
 zz200-accept-money6b.
     display  WS-amount-screen-display6 at curs with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
*> this updates existing value in amt-ok6
*>
 zz200-accept-money6c.
     move     amt-wk-pence6 to WS-pence6.
     move     amt-wk-pds6 to WS-pound6.
     display  WS-amount-screen-display6 at curs with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 zz200-accept-money8a.
     move     zero to WS-poundsd8 WS-penced8 amt-ok8.
*>
 zz200-accept-money8b.
     display  WS-amount-screen-display8 at curs with foreground-color 3.
     accept   WS-amount-screen-accept8  at curs with foreground-color 3 update.
     move     WS-pound8 to amt-wk-pds8.
     move     WS-pence8 to amt-wk-pence8.
*>
*> this updates existing value in amt-ok8
*>
 zz200-accept-money8c.
     move     amt-wk-pence8 to WS-pence8.
     move     amt-wk-pds8 to WS-pound8.
     display  WS-amount-screen-display8 at curs with foreground-color 3.
     accept   WS-amount-screen-accept8  at curs with foreground-color 3 update.
     move     WS-pound8 to amt-wk-pds8.
     move     WS-pence8 to amt-wk-pence8.
*>
 zz200-comm-exit.
     exit     section.
*>
 copy "Proc-ACAS-Param-Get-Rewrite.cob".
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
