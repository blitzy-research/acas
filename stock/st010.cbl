       >>source free
*>*************************************************************
*>                                                            *
*>              Stock Item File Maintenance                   *
*>                                                            *
*>*************************************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         st010.
*>**
*>    Author.             V.B.Coen, FBCS
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Stock Item File Maintenance.
*>**
*>    Version.            See prog-name in Ws.
*>**
*>    Called modules.
*>                        maps04  - Date testing and conversion.
*>                        maps09  - Check Digit verify and creation, used for supplier.
*>                        acas011 - Stock file FH
*>                         stockMT - STOCK-REC RDB table.
*>                        acas015 - Analysis file FH
*>                         analMT  - Analysis Table.
*>                        acas022 - Purchase Ledger file FH
*>                         purchMT - Purchase Ledger Table.
*>                        SL070   - Sales Analysis codes set up - Defaults only.
*>  For testing:
*>                        fhlogger- File Access logging 2 Flat file.
*>**
*>    Error messages used.
*>                        ST000.
*>                        ST003.
*>                        ST005.
*>                        ST006.
*>                        ST008.
*>                        ST011.
*>                        ST012.
*>
*>                        ST101.
*>                        ST102.
*>                        ST103.
*>                        ST104.
*>                        ST105.
*>                        ST106.
*>                        ST107.
*>                        ST108.
*>                        ST109.
*>                        ST110.
*>                        ST111.
*>                        ST112.
*>                        ST113.
*>                        ST114.
*>                        ST115.
*>                        ST116.
*>                        ST117.
*>                        ST118.
*>                        ST119.
*>                        ST120.
*>**
*>    Changes:
*> 25/04/09 vbc - Rewritten in Cobol from scratch for GnuCobol against v2 specs.
*> 04/05/09 vbc - WIP changes in layout in screen and file.
*> 26/05/09 vbc - Added Stock location so no need to imbed into stock number.
*> 28/05/09 vbc -    .16 Added Function Renumber Stock Item.
*> 02/06/09 vbc -    .18 Added PA & SA Anal codes and anal file for sales/Purchase
*>                       support.
*> 03/06/09 vbc -    .20 Added Services only flag ie for Consultancy etc
*>                    so item does not require Qty ordered/backordered, cost etc
*>                    nor WIP values so WIPs are not printed.
*> 05/06/09 vbc -    .21 Include total record count on report.
*> 06/06/09 vbc -    .22 Added WIP stock to stock-value if in use.
*> 18/06/09 vbc -    .24 reversed PA and SA code in report to match input screen
*>                    Swap Stk Abrev and no. around.2 match st030.
*> 16/07/09 vbc -    .25 Using ST104 instead of 105, if purchase ledger not setup.
*> 17/07/09 vbc -    .26 Abbrev code does not need to pass maps09 as no check digit.
*> 24/07/09 vbc -    .27 Force record entry (1) if stockfile not setup
*>                       (file-status (11) not = 1) as per spec/manual.
*> 11/12/11 vbc -        Changed version from 1.00.xx to 3.01.xx, in keeping with
*>                       the rest of ACAS.
*>                   .28 Changed usage of Stk-Date-Form to the global field Date-Form
*>                       making former redundent.
*> 28/04/13 vbc -    .29 Force services flag to N on new record entry screen
*> 10/05/13 vbc -    .30 Added new function of display all records in Display Records
*>                        and new msg ST119.
*>                       Changed set up and amend procedures to correctly accept
*>                        amounts as screen section
*>                       doesnt using Display-01B / 01C (display only).
*> 12/05/13 vbc -    .31 Detect F1 on accept during stock setup (or amend)
*>                       and call pl010 to set up one or more suppliers.
*> 12/05/13 vbc -    .32 Changed wsnames to in common as pl010 called in st010.
*>                   .33 Bug in .31 display cleared some data.
*> 13/05/13 vbc -    .34 Added time to reports so that later reports on same day
*>                       can be seen.
*> 16/05/13 vbc -    .35 Changed wsnames to in copybook see above.
*> 25/05/13 vbc -    .36 Force call to SL070 if analysis file not set up & clean
*>                       up error recovery on opening same.
*> 04/06/13 vbc -    .37 Replaced Stk-WS-Page-Lines with system WS-Page-Lines.
*> 29/06/16 vbc -    .38 Replace Cobol file access verbs with calls to FH and RDB
*>                       DAL. Precede references to Stock-Record, Stock-Key,
*>                       Stock-Abrev-Key, Stock-Desc by WS- to reflect that we
*>                       are only dealing with a WS record and the FD is now gone.
*>                       Stop using File-Status and replace with call to
*>                       "CBL_CHECK_FILE_EXIST" instead. Do same for all such
*>                       checks, sets etc to kill of usage dates back to floppies.
*>                       ST011 added. Update version to 3.02.
*> 17/07/16 vbc -    .39 Bug in test for file exist should be zero if found.
*>                   .40 Initalise broken - moving spaces into numerics so doing
*>                       it the hard way !
*> 24/07/16 vbc -    .41 All file accessing now changed to use FH & RDB other
*>                       than the printer. versioning changed to 3.02 from 3.01.
*> 24/10/16 vbc -    .42 ALL programs now using wsnames.cob in copybooks.
*>                       Usage of maps99 removed.
*> 12/03/18 vbc -    .43 acasnnn copylib renaming acas000-open etc to comply with
*>                       rest of ACAS to (System-Open etc).
*>                       Chg ST000 to stock rec & comment grammar.
*> 20/04/18 vbc -    .44 Updated to support swapout of screen data when F1 is pressed.
*>                        a little experimental.
*> 21/04/18 vbc -    .45 With chg to wsfnctn set path of current dir so can del temp
*>                       screen save file.
*> 04/12/18 vbc -    .46 WS-Cob-Crt-Status was being used and it should have been
*>                       Cob-Crt-Status - compile fails as it has not been defined
*>                       for some time. Now how did that happen?
*> 27/06/20 VBC -    .47 Because of problems processing comp fields from the stock
*>                       record in Screen Section where values seem to be binary
*>                       spaces processing these vars as SS-xxx and moving back
*>                       and from the WS-Stock-Record pre and post accept & display
*>                       of Display-01, Display-02 also removed sign from the
*>                       WS stock record.
*> 29/06/20 vbc -    .48 msg ST108 Table chgd to Rec, ST003 longer.
*>                       Include extra 3 fields to code in .47.
*> 06/02/23 vbc -    .49 Included initialise stock-record in zz070 and elsewhere - JIC
*> 06/08/23 vbc -    .50 Added Display-F1-Display for display stk and clean up start
*>                       for display stk AND remove tests for F1 in Display-Stock.
*> 14/08/23 vbc -    .51 Using WS-Page-Lines set as 45 as reports are landscape.
*>                       User site to change if wrong for their printers.
*> 16/08/23 vbc -    .52 In fa020-Stock-Item-Accept added move 1 to File-Key chg
*>                       test for "*" to use fn-not-less-than instead of not-greater
*>                       as previous can not work.
*> 27/01/24 vbc -    .53 Wrong using in maps09 should be maps09-ws not customer-nos
*>                       found with -d -g etc, wow thats been there for ever - cosmetic.
*> 29/02/24 vbc -    .54 Reinstate individual move zeros/spaces instead of initialise
*>                       as it uses spaces for Stock-TD fields on GC v3.2.
*> 16/04/24 vbc          Copyright notice update superseding all previous notices.
*> 16/12/24 vbc -    .55 Changed WS-Page-Lines to 56 as reports are landscape.
*>                       User site to change if wrong for their printers.
*> 04/02/25 vbc - 3.2.56 Added WS-  to Stock-Location.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*> 15.10.25 vbc - 3.3.01 Msg 103 wrong description should be for Supplier. Manual
*>                       updated.
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
*> copy "selstock.cob".
*> copy "selpl.cob".
*> copy "selanal.cob".
 copy "selprint.cob".
 data                    division.
*>===============================
*>
 file section.
*>------------
*>
*> copy "fdstock.cob".
*> copy "fdpl.cob".
*> copy "fdanal.cob".
 copy "fdprint.cob".
*>
 working-storage section.
*>-----------------------
*>
 77  prog-name           pic x(15)       value "ST010 (3.3.01)".
*>
*>  This will print 1 copy to CUPS print spool specified on line 3
*>
 copy "print-spool-command.cob".
 01  WS-saved-stock-record pic x(400).
*>
*> Amount workfields
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
 01  WS-amount-screen-display7b.
     03  WS-poundsd7b    pic 9(7).
     03  WS-period7b     pic x     value ".".
     03  WS-penced7b     pic v9999.
 01  WS-amount-screen-accept7b redefines WS-amount-screen-display7b.
     03  WS-pound7b      pic 9(7).
     03  filler          pic x.
     03  WS-pence7b      pic v9999.
*>
 01  WS-amount-work7b.
     03  amt-wk-pds7b    pic 9(7).
     03  amt-wk-pence7b  pic v9999.
 01  WS-amount-ok7b redefines WS-amount-work7b.
     03  amt-ok7b        pic 9(7)v9999.
*>
 01  WS-amount-screen-display9.
     03  WS-poundsd9     pic 9(9).
     03  WS-period9      pic x     value ".".
     03  WS-penced9      pic v99.
 01  WS-amount-screen-accept9 redefines WS-amount-screen-display9.
     03  WS-pound9       pic 9(9).
     03  filler          pic x.
     03  WS-pence9       pic v99.
*>
 01  WS-amount-work9.
     03  amt-wk-pds9     pic 9(9).
     03  amt-wk-pence9   pic v99.
 01  WS-amount-ok9 redefines WS-amount-work9.
     03  amt-ok9         pic 9(9)v99.
*>
 01  work-fields.
     03  Menu-Reply      pic 9.
     03  WS-reply        pic x.
     03  WS-menu         pic 9.
     03  Escape-Code     pic x.
     03  Line-Cnt        binary-char unsigned value zero. *> Increase or decrease by 3 for every stk item reported
     03  WS-Page-Lines   binary-char unsigned value 56.   *> 16/12/24 as system is for Portrait and Landscape used.
     03  Page-Nos        binary-char unsigned value zero.
     03  a               binary-char unsigned value zero.
     03  b               pic 9.
     03  c               pic 9.
     03  z1              pic 99 comp  value zero.
*>
     03  WS-Stock-Dates.
         05  WS-Stock-Order-Date pic x(10).
         05  WS-Stock-Order-Due  pic x(10).
     03  WS-Test-Date    pic x(10).
     03  WS-Contruct-Key pic x(13).
     03  WS-Temp-Stock-Key   pic x(13).    *> 1/07
     03  WS-Save-Stock-Key   pic x(13).
     03  WS-Save-Abrev-Key   pic x(7).
     03  WS-Temp-Abrev-Key.
         05  WS-Abrev-K2     pic x(6).
         05  WS-Abrev-Chk2   pic 9.
     03  WS-Stock-Supplier.
         05  filler          pic x(6).
         05  WS-Stock-Supp-7 pic x.
     03  WS-z6           pic z(6).
     03  WS-z6b          pic z(6).
     03  WS-z6c          pic z(6).
     03  WS-Rec-Total    pic zzz,zzz,zz9.
*>
     03  WS-env-lines    pic 999              value zero.
     03  WS-lines        binary-char unsigned value zero.
     03  WS-22-lines     binary-char unsigned value zero.
     03  WS-23-lines     binary-char unsigned value zero.
     03  WS-Rec-Cnt      binary-long unsigned value zero.
*>
 01  SS-Stock-Variables.
     03  SS-Stock-Construct-Bundle   pic 9(6).
     03  SS-Stock-Under-Construction pic 9(6).
     03  SS-Stock-Work-in-Progress   pic 9(6).
     03  SS-Stock-ReOrder-Pnt        pic 9(6).
     03  SS-Stock-Std-ReOrder        pic 9(6).
     03  SS-Stock-Back-Ordered       pic 9(6).
     03  SS-Stock-On-Order           pic 9(6).
     03  SS-Stock-Held               pic 9(6).
     03  SS-Stock-Pre-Sales          pic 9(6).
     03  SS-Stock-Retail             pic 9(7)v99.
     03  SS-Stock-Cost               pic 9(7)v9999.
     03  SS-Stock-Value              pic 9(9)v99.
*>
 01  accept-terminator-array pic 9(4)         value zero.
     copy "screenio.cpy".
*>
*> the following for GC and screen
*>
 01  wScreenName             pic x(256).
 01  wInt                    binary-long.
*>
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
*> Print layouts to 132 cols
*>
 01  Line-1.
     03  L1-Program      pic x(16)     value spaces.
     03  filler          pic x(41)     value spaces.
     03  filler          pic x(17)     value "Stock File Report".
     03  filler          pic x(50)     value spaces.
     03  filler          pic x(5)      value "Page ".
     03  L1-Page         pic zz9.
*>
 01  line-2.
     03  L2-User         pic x(40).
     03  filler          pic x(76)     value spaces.
     03  L2-Date         pic x(10).
     03  filler          pic x         value space.
     03  L2-HH           pic xx        value spaces.
     03  filler          pic x         value ":".
     03  L2-MM           pic xx        value spaces.
*>
 01  line-3.
     03  filler          pic x(132)  value
         "<------ Stock ------> Supplier  Location     Unit      Unit        Value    Number" &
         " <- ReOrder -> <------- Date ------>  Quantity On".
*>
 01  line-4.
     03  filler          pic x(132)  value
         "Abrev   Number         Number               Price      Cost        in Stk   in Stk" &
         "  Point    Qty   Ordered     Due      Order  B/Ord".
*>
 01  line-5.
     03  L5-Abbrev-Stock pic x(8).
     03  L5-Stock-Number pic x(14).
     03  L5-Supplier-No  pic x(8).         *> 30
     03  L5-Location     pic x(11).        *> 41
     03  L5-Retail       pic z(6)9.99.     *> 51
     03  L5-Cost         pic z(6)9.9999.   *> 63
     03  L5-Costx redefines L5-Cost.       *> helps to clear fraction of a penny/cent when zero
         05  filler      pic x(10).
         05  L5-Costz    pic xx.
     03  L5-Value        pic zzzzz,zz9.99. *> 75
     03  L5-Held         pic z(6)9.        *> 82
     03  L5-Reord-Pnt    pic z(6)9.        *> 89
     03  L5-Reord-Qty    pic z(6)9b.       *> 97
     03  L5-Date-Ordered pic x(11).        *> 108
     03  L5-Date-Due     pic x(10).        *> 118
     03  L5-Qty-Ordered  pic z(6)9.        *> 125
     03  L5-Qty-Back-Ord pic z(6)9.        *> 132
*>
 01  line-6.
     03  filler          pic x(5)   value spaces.
     03  filler          pic x(13)  value "Description: ".
     03  L6-Desc         pic x(32)  value spaces.
     03  filler          pic x(5)   value spaces.
     03  L6-vars         pic x(77).
*>
 copy "wsstock.cob".     *> 3.02
 copy "wspl.cob".
 copy "wsanal.cob".
 copy "wsfnctn.cob".     *> Used in acas011, stockMT
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
     03  WS-Stock-Audit-Record  pic x.
*>     03  WS-Stock-Record        pic x.
     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
*>     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
*>     03  WS-Purch-Record        pic x.
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
     03  ST000          pic x(36) value "ST000 Error on Writing to Stock Rec ".   *> ????
*>     03  ST000          pic x(36) value "ST000 Error on Writing to Stock File".
     03  ST000F          pic x(36) value "ST000 Error on Writing to Stock File".
     03  ST003          pic x(25) value "ST003 Hit return for Menu".
     03  ST005          pic x(18) value "ST005 Invalid Date".
     03  ST006          pic x(30) value "ST006 Press return to continue".
     03  ST008          pic x(31) value "ST008 Note message & Hit return".
     03  ST011          pic x(33) value "ST011 Error on stockMT processing".
     03  ST012          pic x(33) value "ST012 Error on purchMT processing".
*> Module Specific
     03  ST101          pic x(24) value "ST101 Supplier not found".
     03  ST102          pic x(46) value "ST102 Abbreviated Stock number Must be present".
     03  ST103          pic x(43) value "ST103 Supplier number Invalid - check digit".
 *>    03  ST103          pic x(38) value "ST103 Abbreviated Stock number Invalid".
     03  ST104          pic x(46) value "ST104 Purchase Ledger not yet set up, Aborting".
     03  ST105          pic x(41) value "ST105 Purchase Ledger not found, Aborting".
*>     03  ST106          pic x(45) value "ST106 Stock Table not yet used, nothing to do".
     03  ST106          pic x(41) value "ST106 Stock File not found, nothing to do".
     03  ST107          pic x(51) value "ST107 Cannot Delete record as non zero values exist".
     03  ST108          pic x(37) value "ST108 Delete failed on Stock Rec   = ".
*>     03  ST108          pic x(36) value "ST108 Delete failed on Stock File = ".
     03  ST109          pic x(50) value "ST109 Cannot Renumber record as Order values exist".
     03  ST110          pic x(44) value "ST110 Cannot find Sales Ledger Analysis Code".
     03  ST111          pic x(47) value "ST111 Cannot find Purchase Ledger Analysis Code".
     03  ST112          pic x(39) value "ST112 Analysis File not found, Aborting".
     03  ST113          pic x(49) value "ST113 Abbreviated Stock Number is already on file".
     03  ST114          pic x(28) value "ST114 Stock Number not found".
     03  ST115          pic x(38) value "ST115 Construct Stock Number not found".
     03  ST116          pic x(37) value "ST116 Stock Number is already on file".
     03  ST117          pic x(47) value "ST117 Stock Number/Abrev No. is already on file".
     03  ST118          pic x(51) value "ST118 Service Flag is set, so unused values cleared".
     03  ST119          pic x(32) value "ST119 No more records to display".
     03  ST120          pic x(33) value "ST120 Error on analMT processing".
*>
 01  error-code         pic 999    value zero.
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  to-day             pic x(10).
*>
 screen section.
*>**************
*>
 01  display-01                  background-color cob-color-black
                                 foreground-color cob-color-green erase eos.
     03  value "Stock Number     - [" line  4 col  1.
*>   03   using WS-Stock-Key pic x(13) col 21. has an accept verb to get info
     03  value "]"                            col 34.
     03  value "PL Fast key  - ["             col 41.
*>   03   using WS-Stock-Abrev-Key pic x(7)   col 57. has an accept verb to get info
     03  value "]"                            col 64.
     03  value "Desc ["               line  5 col  1.
     03  using WS-Stock-Desc pic x(32)        col  7 foreground-color 3.
     03  value "]"                            col 39.
     03  value "Stock Location ["             col 41.
     03  using WS-Stock-Location  pic x(10)   col 57 foreground-color 3.
     03  value "]"                            col 67.
     03  value "Supplier: 1 - ["      line  6 col  1.
     03  using Stock-Supplier-P1 pic x(7)     col 16 foreground-color 3.
     03  value "] : 2 - ["                    col 23.
     03  using Stock-Supplier-P2 pic x(7)     col 32 foreground-color 3.
     03  value "]"                            col 39.
     03  value ": 3 - ["                      col 50.
     03  using Stock-Supplier-P3 pic x(7)     col 57 foreground-color 3.
     03  value "]"                            col 64.
     03  value "Stock Qty        - [" line  7 col  1.
     03  using SS-Stock-Held     pic 9(6)     col 21 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Qty Ordered      - ["         col 41.
     03  using SS-Stock-On-Order pic 9(6)     col 61 foreground-color 3.
     03  value "]"                            col 67.
     03  value "Re-Order Point   - [" line  8 col  1.
     03  using SS-Stock-ReOrder-Pnt pic 9(6)  col 21 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Back Ordered     - ["         col 41.
     03  using SS-Stock-Back-Ordered pic 9(6) col 61 foreground-color 3.
     03  value "]"                            col 67.
     03  value "Re-Order Qty     - [" line  9 col  1.
     03  using SS-Stock-Std-ReOrder pic 9(6)  col 21 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Sales Orders O/S - ["         col 41.
     03  using SS-Stock-Pre-Sales pic 9(6)    col 61 foreground-color 3.
     03  value "]"                            col 67.
     03  value "Sales Anal. Code - [" line 10 col  1.
     03  using Stock-SA-Group pic xx          col 21 foreground-color 3.
     03  value "]"                            col 23.
     03  value "Purch Anal. Code - ["         col 41.
     03  using Stock-PA-Group pic xx          col 61 foreground-color 3.
     03  value "]"                            col 63.
     03  value "Services only Flag [" line 11 col  1.
     03  using Stock-Services-Flag pic x      col 21 foreground-color 3.
     03  value "] (Y/N)"                      col 22.
     03  value "Date Ordered - ["     line 12 col  1.
     03  using WS-Stock-Order-Date pic x(10)  col 17 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Date Due     - ["             col 41.
     03  using WS-Stock-Order-Due pic x(10)   col 57 foreground-color 3.
     03  value "]"                            col 67.
*>
*> Escape function box
*>
     03  value "*******************"  line 18 col 61 erase eol.
     03  value "* Escape Code [ ] *"  line 19 col 61 erase eol.
     03  value "* <B> = Back      *"  line 20 col 61 erase eol.
     03  value "* <S> = Save      *"  line 21 col 61 erase eol.
     03  value "* <Q> = Quit      *"  line 22 col 61 erase eol.
     03  value "*******************"  line 23 col 61 erase eol.
*>
 01  Display-01B                  background-color cob-color-black
                                 foreground-color cob-color-green.   *> Display for accepting money amounts
*> these values from accepts
     03  value "Retail Price - ["     line 13 col  1.
*>     03  using SS-Stock-Retail pic 9(7).99    col 17 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Cost   Price - ["             col 41.
*>     03  using SS-Stock-Cost pic 9(7).9999    col 57 foreground-color 3.
     03  value "]"                            col 69.
     03  value "Stock Value  - ["     line 14 col  1.
*>     03  using SS-Stock-Value pic 9(9).99     col 17 foreground-color 3.
     03  value "]"                            col 29.
*>
 01  Display-01C                  background-color cob-color-black
                                 foreground-color cob-color-green.   *> Display for money amounts (Display Only)
*> these values from accepts
     03  value "Retail Price - ["     line 13 col  1.
     03  using Stock-Retail pic 9(7).99       col 17 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Cost   Price - ["             col 41.
     03  using Stock-Cost pic 9(7).9999       col 57 foreground-color 3.
     03  value "]"                            col 69.
     03  value "Stock Value  - ["     line 14 col  1.
     03  using Stock-Value pic 9(9).99        col 17 foreground-color 3.
     03  value "]"                            col 29.
*>
*> used only if Stk-Manu-Used = 1
*>
 01  display-02                  background-color cob-color-black
                                 foreground-color cob-color-green.
     03  value "Optional - Work In Progress (BOMP) Data"
                                      line 15 col 21 highlight.
     03  value "Construct Bundle - [" line 16 col  1.
     03  using Stock-Construct-Bundle pic 9(6) col 21 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Construction   - ["           col 41.
     03  using Stock-Under-Construction pic 9(6)
                                              col 59 foreground-color 3.
     03  value "]"                            col 65.
     03  value "Work In Progress - [" line 17 col  1.
     03  using Stock-Work-in-Progress  pic 9(6)
                                              col 21 foreground-color 3.
     03  value "]"                            col 27.
     03  value "Construct Item - ["           col 41.
     03  using Stock-Construct-Item pic x(13) col 59 foreground-color 3.
     03  value "]"                            col 72.
*>
 01  Display-F1-Display          background-color cob-color-black
                                 foreground-color cob-color-green.
     03  value "stock # = *  = All stock, one at a time - ESC to quit"
                                      line 23 col 1 foreground-color 3.
*>
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 aa000-Core                 section.
*>*********************************
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
*>  Set up delete file for screen save/restore.
*>
     move     spaces to Path-Work.
     string   ACAS-Path       delimited by space
              "stk-temp.scr"  delimited by size
                                 into Path-Work.
*>
 aa010-Menu-Return.
     move     zero to Menu-Reply.
     perform  zz010-Display-Heading.
*>
 aa020-Menu-Input.
*>
*> New for RDB
*>
     if       FS-Cobol-Files-Used                *> Dup processing removed as redundant
              call  "CBL_CHECK_FILE_EXIST" using File-11
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    perform ba000-Setup-Stock       *> so force setup stock data
                    go to aa010-Menu-Return
              end-if
     end-if
*>
     display  "Select one of the following by number :- [ ]" at 0701 with foreground-color 2.
*>
     display  "(1)  Set-up Stock records"   at 0904 with foreground-color 2.
     display  "(2)  Amend Stock records"    at 1104 with foreground-color 2.
     display  "(3)  Delete Stock records"   at 1304 with foreground-color 2.
     display  "(4)  Renumber Stock records" at 1504 with foreground-color 2.
     display  "(5)  Display Stock records"  at 1704 with foreground-color 2.
     display  "(6)  Print Stock records"    at 1904 with foreground-color 2.
     display  "(9)  Return to System Menu"  at 2104 with foreground-color 2.
*>
     accept   Menu-Reply at 0743 with foreground-color 6 auto.
*>
     if       menu-reply = 9
              go to  aa999-Exit.
*>
     if       menu-reply < 1 or > 6
              go to  aa020-Menu-Input.
*>
     if       menu-reply = 1
              perform ba000-Setup-Stock
     else
      if      menu-reply = 2
              perform ca000-Amend-Stock
      else
       if     menu-reply = 3
              perform da000-Delete-Stock
       else
        if    Menu-Reply = 4
              perform ga000-Renumber-Stock
        else
         if   menu-reply = 6
              perform ea000-Report-Stock
         else
          if  menu-reply = 5
              perform fa000-Display-Stock.
*>
     go       to aa010-Menu-Return.
*>
 maps04.
     call     "maps04" using maps03-ws.
*>
 maps09.
     call     "maps09" using maps09-ws.   *> customer-code.  *> 27/01/24
*>
*> aa020-Rollback.
*>
*> These do not work during testing with mariadb, Non transactional model or
*>  autocommit set ON. Likewise if not using InnoDB but left in in case user
*>  switches using correct engine !!
*>
*>  In reality, using Cobol files they are commited so it is left as default
*> --------------------------------------------------------------------------
*>           exec sql
*>                rollback
*>           end-exec.
 *>    call     "MySQL_rollback".
*>     if       return-code not = zero
*>              display "Rollback failed " at 2301
*>              display return-code      at 2317
*>     end-if.
*>
*> aa030-Commit.            *> Not called
*>           exec sql
*>                commit
*>           end-exec.
*>     call     "MySQL_commit".
*>     if       return-code not = zero
*>              display "Commit failed " at 2301
*>              display return-code      at 2315
*>     end-if.
*>
 aa100-Check-4-Errors.                       *> Stock-Record - if any errors then msgs and exit module
     if       fs-reply not = zero
              display ST011            at 0601 with erase eos  *> acas011/StockMT processing
              display "Fs-reply = "    at 0701
              display fs-reply         at 0712
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
 *>             if      FS-RDBMS-Used
 *>                     perform aa020-Rollback
 *>             end-if
              display ST003 at 1101 with erase eol
              accept  Accept-Reply at 1135
              go to  aa999-Exit
     end-if.
*>
 aa101-Check-4-Errors.                       *> Purch-Record - if any errors then msgs and exit module
     if       fs-reply not = zero
              display ST012            at 0601 with erase eos  *> acas022/PurchMT processing
              display "Fs-reply = "    at 0701
              display fs-reply         at 0712
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
 *>             if      FS-RDBMS-Used
 *>                     perform aa020-Rollback
 *>             end-if
              display ST003 at 1101 with erase eol
              accept  Accept-Reply at 1135
              go to  aa999-Exit
     end-if.
*>
 aa102-Check-4-Errors.                       *> Anal-Record - if any errors then msgs and exit module
     if       fs-reply not = zero
              display ST120            at 0601 with erase eos  *> acas015/analMT processing
              display "Fs-reply = "    at 0701
              display fs-reply         at 0712
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
 *>             if      FS-RDBMS-Used
 *>                     perform aa020-Rollback
 *>             end-if
              display ST003 at 1101 with erase eol
              accept  Accept-Reply at 1135
              go to  aa999-Exit
     end-if.
*>
*>
 Clear-Error-Line.
     display  " " at line WS-23-lines col 01 with erase eol.
*>
 aa999-Exit.
     exit program.
*>
 ba000-Setup-Stock      section.
*>*****************************
*>
     perform  Purch-Open-Input.
     if       fs-reply not = zero
              display ST104 at line WS-23-lines col 1 with foreground-color 4 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              exit program
              go to ba999-exit.   *> safe guard
*>
     perform  Stock-Open.
     if       fs-reply not = zero
        or    WE-Error not zero
              Perform aa100-Check-4-Errors
              perform Purch-Close
              perform Stock-Close
              exit program
     end-if.
     move     "Y" to Stock-Control.
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    move 1 to WS-Process-Func
                              WS-Sub-Function
                    call "sl070" using WS-Calling-Data
                                       System-Record
                                       To-Day
                                       File-Defs
                    end-call
              end-if
     end-if
     perform  Analysis-Open-Input.
     if       fs-Reply not = zero
              perform  aa102-Check-4-Errors.
*>
 ba010-Display-Stock-Headings.
     perform  zz020-Display-Outline.
*>
     initialize WS-Stock-Record with filler.                  *> chgd 4 stock
     perform  zz070-Initialize-Stock-Record.
     move     spaces to WS-Stock-Key (13:1)
                        WS-Stock-Abrev-Key (7:1)
                        Customer-Code WS-Stock-Dates.
     move     "N" to Stock-Services-Flag.
*>
 ba020-Stock-Item-Accept.
     display  " " at 0467.
     accept   WS-Stock-Key at 0421 with foreground-color 3.
     if       WS-Stock-Key = spaces
          or  Cob-Crt-Status = Cob-Scr-Esc
              go to  ba998-Main-End.
     move     function upper-case (WS-Stock-Key) to WS-Temp-Stock-Key.           *> chgd 4 stock
     display  WS-Stock-Key at 0421 with foreground-color 3.
*>
 ba030-Stock-Abrev-Item-Accept.
     accept   WS-Stock-Abrev-Key at 0457 with foreground-color 3.
     if       Cob-Crt-Status = Cob-Scr-Esc
          or  Cob-Crt-Status = Cob-Scr-Page-Up
          or  Cob-Crt-Status = Cob-Scr-Key-Up
              go to ba020-Stock-Item-Accept
     end-if
     if       WS-Stock-Abrev-Key not = spaces
              move  function upper-case (WS-Stock-Abrev-Key) to WS-Stock-Abrev-Key
                                                                   Customer-Code
              display WS-Stock-Abrev-Key at 0457 with foreground-color 3
              perform  clear-error-line
     else
              display ST102 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ba030-Stock-Abrev-Item-Accept
     end-if
*>
*>  Check that keys do NOT exist
*>
     move     1 to File-Key-No.             *>  1=stock-key, 2=Abrev, 3=Desc
     perform  Stock-Read-Indexed.
     if       (fs-Reply not = 23 and not = 21)            *> invalid key but for RDB it's 23
              display ST113 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ba020-Stock-Item-Accept.
*>
     move     Customer-Code to WS-Stock-Abrev-Key.
     if       WS-Stock-Abrev-Key not = spaces
              move   2 to File-Key-No
              perform Stock-Read-Indexed
*>              read   Stock-File key is WS-Stock-Abrev-Key not invalid key
              if     (fs-Reply not = 23 and not = 21)           *> invalid key but for RDB its 23
                     display ST116 at line WS-23-lines col 1 with foreground-color 4 highlight
                     go to ba020-Stock-Item-Accept.
*>
*>  Now, we have unused Stock keys
*>
     perform  clear-error-line.
     move     customer-code to WS-Stock-Abrev-Key.
     move     WS-Temp-Stock-Key  to WS-Stock-Key.
     initialise SS-Stock-Variables.
*>
 ba040-Accept-Block.
     accept   Display-01.      *> get all data but not money fields
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to ba020-Stock-Item-Accept.
*>
*> If F3 allow set up of a supplier then redisplay heads and data be re-accepting data.
*>   question is, will f1 be detected?
*>
     if       Cob-Crt-Status = COB-SCR-F3
              move     zero to WS-term-code
              move     z"stk-temp.scr"  to wScreenName
              call     "scr_dump"    using wScreenName returning wInt
              call     "pl010" using WS-calling-data system-record to-day file-defs
              call     "scr_restore" using wScreenName returning wInt
              call     "CBL_DELETE_FILE" using Path-Work
 *>             perform  zz010-Display-Heading
 *>             display  Display-01
 *>             display  WS-Stock-Key at 0421 with foreground-color 3
 *>             display  WS-Stock-Abrev-Key at 0457 with foreground-color 3
              go       to ba040-Accept-Block.
*>
*>  If Suppliers included, they are now checked for presence on Purchase Ledger
*>
     move     zero to c.
     perform  varying b from 1 by 1 until b > 3
              if       Stock-Suppliers (b) not = spaces
                       move     function upper-case (Stock-Suppliers (b)) to Stock-Suppliers (b)
                                                                             WS-Stock-Supplier
                       perform  zz040-Check-for-Supplier
                       if       Error-Code not = zero
                                multiply b by 2 giving a
                                add      20 to a
                                if       c = zero    *> display only once
                                         move 1 to c
                                         display ST101
                                                    at line WS-23-lines col 1 with foreground-color 4 highlight
                                end-if
                                display b at line WS-23-lines col a with foreground-color 4 highlight
                       end-if
                       move     WS-Stock-Supplier to Stock-Suppliers (b)
              end-if
     end-perform
     if       c not = zero
              go to ba040-Accept-Block.
*>
     perform  Clear-Error-Line.
*>
*> If PA or SA anal codes present they are checked for on analysis file.
*>
     move     function lower-case (Stock-PA-Group) to Stock-PA-Group.
     display  Stock-PA-Group at 1057 with foreground-color 3.
     if       Stock-PA-Group not = spaces
              move "P" to Stock-PA-System
              move Stock-PA-Code to WS-PA-Code
              perform Analysis-Start
              if     fs-Reply = 21 or = 23
                     display ST111 at line WS-23-lines col 1 with foreground-color 4 highlight
                     go to ba040-Accept-Block
              end-if
              if       fs-Reply not = zero
                       perform  aa102-Check-4-Errors
              end-if
     end-if
*>
     move     function lower-case (Stock-SA-Group) to Stock-SA-Group.
     display  Stock-SA-Group at 1021 with foreground-color 3.
     if       Stock-SA-Group not = spaces
              move "S" to Stock-SA-System
              move Stock-SA-Code to WS-PA-Code
              perform  Analysis-Start
              if    FS-Reply = 21 or = 23
                    display ST110 at line WS-23-lines col 1 with foreground-color 4 highlight
                    go to ba040-Accept-Block
              end-if
              if       fs-Reply not = zero
                       perform  aa102-Check-4-Errors
              end-if     *>              end-start
     end-if
*>
*>   Display and get money fields then WIPs
*>
     perform zz090-Copy-From-SS.
     display Display-01C.
*>
 ba042-Get-Stock-Retail.
     move     13 to lin.
     move     17 to cole.
     move     Stock-Retail to amt-ok7.
     perform  zz030-accept-money7.
     move     amt-ok7 to Stock-Retail.  *> 9(7).99
 ba044-Get-Stock-Cost.
     move     57 to cole.
     move     Stock-Cost to amt-ok7b.
     perform  zz030-accept-money7b.
     move     amt-ok7b to Stock-Cost.   *> 9(7).9999
 ba046-Get-Stock-Value.
     move     14 to lin.
     move     17 to cole.
     move     Stock-Value to amt-ok9.
     perform  zz030-accept-money9c.
     move     amt-ok9 to Stock-Value.   *> 9(9).99
*>
     if       Stk-Manu-Used = 1
              accept Display-02.
*>
*>  Calc Stock-Value only if Stock-Averaging is set
*>
     if       Stock-Averaging
         and  Stock-Value = zero
         and  Stock-Cost not = zero
         and  Stock-Held not = zero
              multiply Stock-Held by Stock-Cost giving Stock-Value
              if Stk-Manu-Used = 1
                 compute Stock-Value = Stock-Value + (Stock-Cost * Stock-Work-in-Progress).
*>
     if       WS-Stock-Order-Date not = spaces
              move WS-Stock-Order-Date to WS-Test-Date
              perform zz050-Validate-Date
              if u-bin not = zero
                 move u-bin to Stock-Order-Date
                 display " " at 1228
              else
                 display ST005 at line WS-23-lines col 1 with foreground-color 4 highlight
                 display "*" at 1228 with foreground-color 4 highlight
                 go to ba040-Accept-Block
              end-if
     else
              move zero to Stock-Order-Date
     end-if
*>
     if       WS-Stock-Order-Due not = spaces
              move WS-Stock-Order-Due to WS-Test-Date
              perform zz050-Validate-Date
              if u-bin not = zero
                 move u-bin to Stock-Order-Due
                 display " " at 1268
              else
                 display ST005 at line WS-23-lines col 1 with foreground-color 4 highlight
                 display "*" at 1268 with foreground-color 4 highlight
                 go to ba040-Accept-Block
     else
              move zero to Stock-Order-Due.
*>
     display  space at 1228.  *> incase 1st was entered then spaces 2nd.
     display  space at 1268.
     perform  Clear-Error-Line.
*>
     if       Stock-Construct-Item not = spaces
              move    function upper-case (Stock-Construct-Item) to Stock-Construct-Item
                                                                    WS-Contruct-Key
              display Stock-Construct-Item at 1659 with foreground-color 3
              move    WS-Stock-Record to WS-Saved-Stock-Record
              move    WS-Contruct-Key to WS-Stock-Key
              move    1 to File-Key-No
*>              set     fn-Equal-to to true
              move    5 to Access-Type   *> =
              perform Stock-Start
              if      fs-Reply = 21                *> invalid key
                      display ST115 at line WS-23-lines col 1 with foreground-color 4 highlight
                      move  WS-saved-stock-record to WS-Stock-Record
                      go    to ba040-Accept-Block
              end-if
              move     WS-saved-stock-record to WS-Stock-Record
     end-if
*>
*> if stock-services-flag set clear down unneeded values inc. WIP & redisplay
*>
     if       Stock-Services-Flag not = space
              move function upper-case (Stock-Services-Flag) to Stock-Services-Flag.
     if       Stock-Services-Flag = "Y"
              move spaces to Stock-Construct-Item WS-Stock-Order-Due WS-Stock-Order-Date
              move zero to Stock-Construct-Bundle  Stock-Under-Construction
                           Stock-Work-in-Progress  Stock-ReOrder-Pnt
                           Stock-Std-ReOrder       Stock-Back-Ordered
                           Stock-On-Order          Stock-Pre-Sales
                           Stock-Value
                           Stock-Order-Due         Stock-Order-Date
              display  display-01
              display  display-01C
              if       Stk-Manu-Used = 1
                       display Display-02
              end-if
              display ST118 at line WS-23-lines col 1 with foreground-color 2 highlight
     end-if
     move     "S" to Escape-Code.
     perform  zz100-Test-Escape.
*>
 ba050-Main-Output.
     if       escape-code = "Q"
         or   Cob-Crt-Status = Cob-Scr-Esc
              go to  ba998-Main-End.
*>
     if       escape-code = "B"
         or   Cob-Crt-Status = Cob-Scr-Page-Up
          or  Cob-Crt-Status = Cob-Scr-Key-Up
              go to ba020-Stock-Item-Accept.
*>
     perform  Stock-Write.
     if       fs-reply not = zero  *> could be 22 (Dup key) or 99 (any other)
              display ST000 at line WS-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line WS-23-lines col 38 with foreground-color 4 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to ba998-Main-End.
*>
 *>    initialize WS-Stock-Record with filler.
     perform  zz070-Initialize-Stock-Record.
     move     spaces to WS-Stock-Dates.
     go       to ba010-Display-Stock-Headings.
*>
 ba998-Main-End.
     perform  Analysis-Close.
     perform  Purch-Close.
     perform  Stock-Close.
*>
 ba999-Exit.
     exit     section.
*>
 ca000-Amend-Stock          section.
*>*********************************
*>  can any of this be removed although purch is needed for supplier details ???????
     perform  Purch-Open-Input.
     if       fs-reply not = zero
              display ST105 at line WS-23-lines col 1 with foreground-color 4 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to ca999-exit.
*>
     perform  Stock-Open.
     if       fs-reply not = zero
        or    WE-Error not zero
              display ST106 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ca998-Main-End.
*>
     perform  Analysis-Open-Input.
     if       fs-reply not = zero
              display ST112 at line WS-23-lines col 1 with foreground-color 4 highlight
              perform Purch-Close        *> close Purchase-File   Stock-File
              perform Stock-Close
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to ca999-exit.
*>
 ca010-Display-Stock-Headings.
     perform  zz020-Display-Outline.
*>
 ca020-Stock-Item-Accept.
 *>    initialize WS-Stock-Record with filler.
     perform  zz070-Initialize-Stock-Record.
     move     spaces to WS-Stock-Key (13:1)
                        WS-Stock-Abrev-Key (7:1)
                        Customer-Code WS-Stock-Dates.
     display  " " at 0467.
     accept   WS-Stock-Key at 0421 with foreground-color 3.
     if       WS-Stock-Key = spaces
          or  Cob-Crt-Status = Cob-Scr-Esc
              go to  ca998-Main-End.
     move     function upper-case (WS-Stock-Key) to WS-Stock-Key
                                                    WS-Temp-Stock-Key.
*>
 ca030-Get-Record.
     move     1 to File-Key-No.             *>  1=stock-key, 2=Abrev, 3=Desc
     perform  Stock-Read-Indexed.
     if       fs-Reply = 23 or = 21
              display ST114 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ca020-Stock-Item-Accept.
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
     perform  Clear-Error-Line.
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
     end-if
*>
*> Redisplay, now dates are converted
*>
     perform  zz080-Copy-To-SS.
     display  display-01.
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
*>
 ca040-Accept-Block.
     accept   display-01.      *> get all data but not money fields
     If       Cob-Crt-Status = Cob-Scr-Esc
              go to ca020-Stock-Item-Accept.
*>
*> If F3 allow set up of a supplier then redisplay heads and data be re-accepting data.
*>   question is, will f1 be detected?
*>
     if       Cob-Crt-Status = COB-SCR-F3
              move     zero to WS-term-code
              move     z"stk-temp.scr"  to wScreenName
              call     "scr_dump"    using wScreenName returning wInt
              call     "pl010" using WS-calling-data system-record to-day file-defs
              call     "scr_restore" using wScreenName returning wInt
              call     "CBL_DELETE_FILE" using Path-Work
 *>             perform  zz010-Display-Heading
 *>             display  Display-01
 *>             display  WS-Stock-Key at 0421 with foreground-color 3
 *>             display  WS-Stock-Abrev-Key at 0457 with foreground-color 3
              go       to ca040-Accept-Block.
*>
*>  If Suppliers included, they are now checked for presence on Purchase Ledger
*>
     move     zero to c.
     perform  varying b from 1 by 1 until b > 3
              if       Stock-Suppliers (b) not = spaces
                       move     function upper-case (Stock-Suppliers (b)) to Stock-Suppliers (b)
                                                                             WS-Stock-Supplier
                       perform  zz040-Check-for-Supplier
                       if       Error-Code not = zero
                                multiply b by 2 giving a
                                add      20 to a
                                if       c = zero    *> display only once
                                         move 1 to c
                                         display ST101
                                                    at line WS-23-lines col 1 with foreground-color 4 highlight
                                end-if
                                display b at line WS-23-lines col a with foreground-color 4 highlight
                       end-if
                       move     WS-Stock-Supplier to Stock-Suppliers (b)
              end-if
     end-perform
     if       c not = zero
              go to ca040-Accept-Block.
*>
     perform  Clear-Error-Line.
*>
*> If PA or SA anal codes present they are checked for on analysis file.
*>
     move     function lower-case (Stock-PA-Group) to Stock-PA-Group.
     display  Stock-PA-Group at 1057 with foreground-color 3.
     if       Stock-PA-Group not = spaces
              move "P" to Stock-PA-System
              move Stock-PA-Code to WS-PA-Code
              perform Analysis-Start
              if   FS-Reply = 21 or = 23
                   display ST111 at line WS-23-lines col 1 with foreground-color 4 highlight
                   go to ca040-Accept-Block
              end-if
              if       fs-Reply not = zero
                       perform  aa102-Check-4-Errors
              end-if
     end-if
*>
     move     function lower-case (Stock-SA-Group) to Stock-SA-Group.
     display  Stock-SA-Group at 1021 with foreground-color 3.
     if       Stock-SA-Group not = spaces
              move "S" to Stock-SA-System
              move Stock-SA-Code to WS-PA-Code
              perform Analysis-Start
              if   FS-Reply = 21 or = 23
                   display ST110 at line WS-23-lines col 1 with foreground-color 4 highlight
                   go to ca040-Accept-Block
              end-if
              if       fs-Reply not = zero
                       perform  aa102-Check-4-Errors
              end-if     *>      end-start
     end-if
*>
*>   Display and get money fields then WIPs
*>
     perform zz090-Copy-From-SS.
     display Display-01C.
*>
 ca042-Get-Stock-Retail.
     move     13 to lin.
     move     17 to cole.
     move     Stock-Retail to amt-ok7.
     perform  zz030-accept-money7.
     move     amt-ok7 to Stock-Retail.  *> 9(7).99
 ca044-Get-Stock-Cost.
     move     57 to cole.
     move     Stock-Cost to amt-ok7b.
     perform  zz030-accept-money7b.
     move     amt-ok7b to Stock-Cost.   *> 9(7).9999
 ca046-Get-Stock-Value.
     move     14 to lin.
     move     17 to cole.
     move     Stock-Value to amt-ok9.
     perform  zz030-accept-money9c.
     move     amt-ok9 to Stock-Value.   *> 9(9).99
*>
     if       Stk-Manu-Used = 1
              accept Display-02.
*>
*>  Calc Stock-Value only if Stock-Averaging is set
*>
     if       Stock-Averaging
         and  Stock-Value = zero
         and  Stock-Cost not = zero
         and  Stock-Held not = zero
              multiply Stock-Held by Stock-Cost giving Stock-Value.
              if Stk-Manu-Used = 1
                 compute Stock-Value = Stock-Value + (Stock-Cost * Stock-Work-in-Progress).
*>
     if       WS-Stock-Order-Date not = spaces
              move WS-Stock-Order-Date to WS-Test-Date
              perform zz050-Validate-Date
              if u-bin not = zero
                 move u-bin to Stock-Order-Date
                 display " " at 1228
              else
                 display ST005 at line WS-23-lines col 1 with foreground-color 4 highlight
                 display "*" at 1228 with foreground-color 4 highlight
                 go to ca040-Accept-Block
     else     move zero to Stock-Order-Date.
*>
     if       WS-Stock-Order-Due not = spaces
              move WS-Stock-Order-Due to WS-Test-Date
              perform zz050-Validate-Date
              if u-bin not = zero
                 move u-bin to Stock-Order-Due
                 display " " at 1268
              else
                 display ST005 at line WS-23-lines col 1 with foreground-color 4 highlight
                 display "*" at 1268 with foreground-color 4 highlight
                 go to ca040-Accept-Block
     else     move zero to Stock-Order-Due.
*>
     display  " " at 1228.  *> incase 1st was entered then spaces 2nd.
     display  " " at 1268.
     perform  Clear-Error-Line.
*>
     if       Stock-Construct-Item not = spaces
              move    function upper-case (Stock-Construct-Item) to Stock-Construct-Item
                                                                    WS-Contruct-Key
              display Stock-Construct-Item at 1659 with foreground-color 3
              move    WS-Stock-Record to WS-saved-stock-record
              move    WS-Contruct-Key to WS-Stock-Key
              move    1 to File-Key-No
              move    5 to Access-Type   *> =
              perform Stock-Start
              if      fs-Reply = 21
                      display ST115 at line WS-23-lines col 1 with foreground-color 4 highlight
                      move   WS-saved-stock-record to WS-Stock-Record
                      go to ca040-Accept-Block
*>              end-start
              end-if
              move     WS-saved-stock-record to WS-Stock-Record
     end-if
*>
*> if stock-services-flag set clear down unneeded values inc. WIP & redisplay
*>
     if       Stock-Services-Flag not = space
              move function upper-case (Stock-Services-Flag) to Stock-Services-Flag.
     if       Stock-Services-Flag = "Y"
              move spaces to Stock-Construct-Item WS-Stock-Order-Due WS-Stock-Order-Date
              move zero to Stock-Construct-Bundle  Stock-Under-Construction
                           Stock-Work-in-Progress  Stock-ReOrder-Pnt
                           Stock-Std-ReOrder       Stock-Back-Ordered
                           Stock-On-Order          Stock-Pre-Sales
                           Stock-Value
                           Stock-Order-Due         Stock-Order-Date
              display  display-01
              display  display-01C
              if       Stk-Manu-Used = 1
                       display Display-02
              end-if
              display ST118 at line WS-23-lines col 1 with foreground-color 2 highlight
     end-if
     move     "S" to escape-code.
     perform  zz100-test-escape.
*>
 ca050-Main-Output.
     if       escape-code = "Q"
         or   Cob-Crt-Status = Cob-Scr-Esc
              go to  ca998-main-end.
*>
     if       escape-code = "B"
         or   Cob-Crt-Status = Cob-Scr-Page-Up
          or  Cob-Crt-Status = Cob-Scr-Key-Up
              go to ca020-Stock-Item-Accept.
*>
     perform  Stock-Rewrite.
     if       fs-reply not = zero
              display ST000 at line WS-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line WS-23-lines col 38 with foreground-color 4 highlight
              display ST003   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30
              go to ca998-main-end.
*>
 *>    initialize WS-Stock-Record with filler.
     perform  zz070-Initialize-Stock-Record.
     move     spaces to WS-Stock-Dates.
     go       to ca010-Display-Stock-Headings.
*>
 ca998-Main-End.
     perform  Purch-Close.
     perform  Analysis-Close.
     perform  Stock-Close.
*>
 ca999-Exit.
     exit     section.
*>
 da000-Delete-Stock         section.
*>*********************************
*>
     perform  Stock-Open.
     if       fs-reply not = zero
              perform Stock-Close
              display ST106 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to da999-Exit.
*>
 da010-Display-Stock-Headings.
     perform  zz020-Display-Outline.
*>
 da020-Stock-Item-Accept.
     move     spaces to WS-Stock-Key
                        WS-Stock-Abrev-Key
                        Customer-Code.
     display  space at 2361 with erase eol.
        perform  zz070-Initialize-Stock-Record.
        initialise SS-Stock-Variables.
     display  display-01.
     if       Stk-Manu-Used = 1
              display Display-02.
     accept   WS-Stock-Key at 0421 with foreground-color 3.
     if       WS-Stock-Key = spaces
          or  Cob-Crt-Status = Cob-Scr-Esc
              perform Stock-Close
              go to da999-Exit.
     move     function upper-case (WS-Stock-Key) to WS-Stock-Key
                                                 WS-Temp-Stock-Key.
     display  space at line WS-23-lines col 1 with erase eos.
*>
 da030-Get-Record.
*>     read     Stock-File record key WS-Stock-Key invalid key
     move     1 to File-Key-No.
     perform  Stock-Read-Indexed.
     if       fs-Reply = 21 or = 23              *> 23 for RDB
              display ST114 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to da020-Stock-Item-Accept.
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
     perform  Clear-Error-Line.
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
     end-if
*>
*> Redisplay now dates are converted
*>
      perform  zz080-Copy-To-SS.
     display  display-01.
     if       Stk-Manu-Used = 1
              display Display-02.
     display  "* <D> = Delete    *" at 2261 with foreground-color 2.
     display  "*******************" at 2361 with foreground-color 2.
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
*>
     if       Stock-On-Order not = zero
           or Stock-Held not = zero
           or Stock-Back-Ordered not = zero
              display ST107 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to da020-Stock-Item-Accept.
*>
     move     "D" to escape-code.
     perform  zz100-test-escape.
*>
     if       escape-code = "Q"
         or   Cob-Crt-Status = Cob-Scr-Esc
              go to  da999-Exit.
*>
     if       escape-code = "B" or = "S"
         or   Cob-Crt-Status = Cob-Scr-Page-Up
          or  Cob-Crt-Status = Cob-Scr-Key-Up
              go to da020-Stock-Item-Accept.
*>
     if       escape-code not = "D"
              go to  da010-Display-Stock-Headings.
*>
 da040-Accept-Delete.
     display  "Deleting Stock Item record, are you sure? [ ]"
                at line WS-22-lines col 1 with foreground-color 2 highlight.
     accept   WS-reply at line WS-22-lines col 44 with foreground-color 6.
     move     function upper-case (WS-reply) to WS-reply.
     if       WS-reply not = "Y" and not = "N"
              go to da040-Accept-Delete.
*>
     if       WS-reply = "N"
              go to da010-Display-Stock-Headings.
     display  " " at line WS-22-lines col 1 with erase eol.
*>
     move     1 to File-Key-No.
     perform  Stock-Delete.
*>
     if       fs-reply not = zero
              display ST108 at line WS-23-lines col 1 with foreground-color 4 highlight
              display fs-reply at line WS-23-lines col 37 with foreground-color 4 highlight
              display ST006   at line WS-lines col 01
              accept WS-reply at line WS-lines col 30.
*>
     go       to  da010-Display-Stock-Headings.
*>
 da999-Exit.
     exit     section.
*>
 ea000-Report-Stock         section.
*>*********************************
*>
*> Used here as a full print. For other options see st030 (Stock Reports)
*>
     perform  Stock-Open-Input.
     if       fs-reply not = zero
              close Print-File             *>  Stock-File
              perform Stock-Close
              display ST106 at line WS-23-lines col 1 with foreground-color 4 highlight
              exit section
     end-if
*>
     open     output Print-File.
     perform  ea200-Produce-Report.
     close    Print-File.
     perform  Stock-Close.
     call     "SYSTEM" using Print-Report.
*>
 ea999-exit.
     exit     section.
*>
 ea200-Produce-Report       section.
*>*********************************
*>
     move     99 to Line-Cnt.
     move     zero to Page-Nos WS-Rec-Cnt.
     move     Prog-Name to L1-Program.
     move     usera to L2-User.
     move     To-Day to u-Date.
     perform  zz020-convert-date.
     move     u-Date to L2-Date.
     accept   hdtime from time.
     if       hdtime not = "00000000"
              move hd-hh to L2-HH
              move hd-mm to L2-MM.
*>
 ea210-Read-Stock.
     perform  Stock-Read-Next.
     if       fs-Reply = 10                       *> EOF
              go to ea230-Totals.
*>
     perform  ea220-Heads.
     add      1 to WS-Rec-Cnt.
     move     spaces to line-5.
     move     WS-Stock-Key       to L5-Stock-Number.
     move     WS-Stock-Abrev-Key to L5-Abbrev-Stock.
     move     Stock-Supplier-P1  to L5-Supplier-No.
     move     Stock-Retail       to L5-Retail.
     move     Stock-Cost         to L5-Cost.
     if       L5-Costz = "00"
              move spaces to L5-Costz
     end-if
     if       Stock-Services-Flag not = "Y"
              move  Stock-Value        to L5-Value
              move  Stock-Held         to L5-Held
              move  Stock-ReOrder-Pnt  to L5-Reord-Pnt
              move  Stock-Std-ReOrder  to L5-Reord-Qty
              move  Stock-On-Order     to L5-Qty-Ordered
              move  Stock-Back-Ordered to L5-Qty-Back-Ord
     end-if
     move     WS-Stock-Location        to L5-Location.
     if       Stock-Order-Date not = zero
              move Stock-Order-Date to u-bin
              perform zz060-Convert-Date
              move WS-date to L5-Date-Ordered
     else
              move spaces to L5-Date-Ordered
     end-if
     if       Stock-Order-Due not = zero
              move Stock-Order-Due to u-bin
              perform zz060-Convert-Date
              move WS-date to L5-Date-Due
     else
              move spaces to L5-Date-Due
     end-if
     move     WS-Stock-Desc to L6-Desc.
     move     1 to a.
     move     spaces to L6-vars.
     if       Stock-Supplier-P2 not = spaces
           or Stock-Supplier-P3 not = spaces
              string "Secondary Suppliers" delimited by size into L6-vars pointer a
              if Stock-Supplier-P2 not = spaces
                  string " 1: "            delimited by size
                         Stock-Supplier-P2 delimited by size into L6-vars pointer a
              end-if
              if Stock-Supplier-P3 not = spaces
                  string " 2: "            delimited by size
                         Stock-Supplier-P3 delimited by size into L6-vars pointer a
              end-if
              add 2 to a
     end-if
     if       Stock-SA-Code not = spaces
              string "SA Code: "           delimited by size
                     Stock-SA-Group        delimited by size into L6-vars pointer a
              add 2 to a
     end-if
     if       Stock-PA-Code not = spaces
              string "PA Code: "           delimited by size
                     Stock-PA-Group        delimited by size into L6-vars pointer a
     end-if
*>
     if       Stock-Pre-Sales not = zero
              move Stock-Pre-Sales to WS-z6
              string "  Pre Sales :"       delimited by size
                     WS-z6                 delimited by size into L6-vars pointer a
     end-if
     if       Line-Cnt > 5
              move all "-" to print-record
              write print-record after 1
              write print-record from line-5 after 1
     else
              write print-record from line-5 after 2
     end-if
     write    print-record from line-6 after 1.
     add      3 to Line-Cnt.
     move     spaces to print-record.
     if       Stock-Services-Flag not = "Y"
          and (zero not = Stock-Construct-Bundle or not = Stock-Under-Construction
           or not = Stock-Work-in-Progress or Stock-Construct-Item not = spaces)
              move Stock-Construct-Bundle   to WS-z6
              move Stock-Under-Construction to WS-z6b
              move Stock-Work-in-Progress   to WS-z6c
              string "Construction Bundle :"    delimited by size
                     WS-z6                      delimited by size
                     "  WIP :"                  delimited by size
                     WS-z6c                     delimited by size
                     "  Under Construction :"   delimited by size
                     WS-z6b                     delimited by size
                     " For Constructed Item : " delimited by size
                     Stock-Construct-Item       delimited by size
                                into print-record
              end-string
              write  print-record after 1
              add 1 to Line-Cnt
     end-if
     if       Stock-Services-Flag = "Y"
              move "Services only Product" to print-record
              write  print-record after 1
              add 1 to Line-Cnt
     end-if
     go       to ea210-Read-Stock.
*>
 ea220-Heads.
     if       line-cnt > WS-Page-Lines
              add 1 to Page-Nos
              move Page-Nos to L1-Page
              if  Page-Nos not = 1
                  write print-record from line-1 after page
                  write print-record from line-2 after 1
                  move spaces to print-record
                  write print-record after 1
              else
                  write print-record from line-1 before 1
                  write print-record from line-2 before 1
              end-if
              write print-record from line-3 after 1
              write print-record from line-4 after 1
              move 5 to Line-Cnt
     end-if.
*>
 ea230-Totals.
     if       Line-Cnt > WS-Page-Lines - 2
              add 60 to Line-Cnt
              perform ea220-Heads.
     move     spaces to Print-Record.
     move     WS-Rec-Cnt to WS-Rec-Total.
     string   " Total Stock Records " delimited by size
              function trim (WS-Rec-Total leading) delimited by size into Print-Record.
     write    Print-Record after 2.

 ea299-Exit.
     exit     section.
*>
 fa000-Display-Stock        section.     *> Get rec load SS-  ??????
*>*********************************
*>
     perform  Stock-Open-Input.
     if       fs-reply not = zero
              perform Stock-Close
              display ST106 at line WS-23-lines col 1 with foreground-color 4 highlight
              display ST003 at line WS-lines col 1 with foreground-color 4 highlight
              go to fa999-Exit.
     move     1 to File-Key-No.             *>  1=stock-key, 2=Abrev, 3=Desc
*>
 fa010-Display-Stock-Headings.
     perform  zz020-Display-Outline.
*>
 fa020-Stock-Item-Accept.
     move     spaces to WS-Stock-Key
                        WS-Stock-Abrev-Key
                        Customer-Code.
     display  display-01.
     display  display-01C.
     display  Display-F1-Display.
     if       Stk-Manu-Used = 1
              display Display-02.
     accept   WS-Stock-Key at 0421 with foreground-color 3.
*>
*> test to see if can save function key values!!!
*>
     if       WS-Stock-Key = spaces
          or  Cob-Crt-Status = Cob-Scr-Esc
              perform Stock-Close
              go to fa999-Exit.
     if       WS-Stock-Key (1:1) = "*"
              move     1 to File-Key-No             *>  1=stock-key, 2=Abrev, 3=Desc
              move     spaces to WS-Stock-Key
              set      fn-not-less-than to true      *> chgd from not-greater  16/08/23
              perform  Stock-Start
              move     "*" to WS-Stock-Key.
     move     function upper-case (WS-Stock-Key) to WS-Stock-Key
                                                    WS-Temp-Stock-Key.
*>
 fa030-Get-Record.
*>
*>  if a * entered then we will go though all stock records sequentially
*>
     if       WS-Temp-Stock-Key (1:1) = "*"
              perform  Stock-Read-Next
              if       fs-Reply not = zeros           *> was   = 10     *> EOF   16/08/23
                       display ST119 at line WS-23-lines col 1 with foreground-color 4 highlight
                       display ST003 at line WS-lines col 1 with foreground-color 4 highlight
                       go to fa020-Stock-Item-Accept
              end-if
     else
              move     1 to File-Key-No             *>  1=stock-key, 2=Abrev, 3=Desc
              perform  Stock-Read-Indexed
              if       fs-Reply not = 00
                       display ST114 at line WS-23-lines col 1 with foreground-color 4 highlight
                       display ST003 at line WS-lines col 1 with foreground-color 4 highlight
                       go to fa020-Stock-Item-Accept
              end-if
     end-if
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
     perform  Clear-Error-Line.
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
     end-if
*>
*> Redisplay now dates are converted
*>
     perform  zz080-Copy-To-SS.
     display  display-01.
     display  display-01C.
     if       Stk-Manu-Used = 1
              display Display-02.
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
*>
     if       WS-Temp-Stock-Key = "*"
              move "N" to Escape-Code
              display "N> = Next  " at line 20 col 64 with foreground-color cob-color-green
     else
              move "S" to Escape-Code.
     perform  zz100-test-escape.
*>
     if       Escape-Code = "N"                  *> Get next record
              go to fa030-Get-Record.
     if       escape-code = "Q"
         or   Cob-Crt-Status = Cob-Scr-Esc
              perform Stock-Close
              go to  fa999-Exit.
*>
     go       to  fa010-Display-Stock-Headings.  *> S will redisplay heads etc
*>
 fa999-Exit.
     exit     section.
*>
 ga000-Renumber-Stock        section.
*>**********************************
*>
     perform  Stock-Open.
     if       fs-reply not = zero
              perform Stock-Close
              display ST106 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ga999-Exit.
*>
 ga010-Display-Stock-Headings.
     perform  zz020-Display-Outline.
*>
 ga020-Stock-Item-Accept.
     move     spaces to WS-Stock-Key
                        WS-Stock-Abrev-Key
                        Customer-Code.
     display  space at 2361 with erase eol.
     display  display-01.
     display  Display-01C.
     if       Stk-Manu-Used = 1
              display Display-02.
     accept   WS-Stock-Key at 0421 with foreground-color 3.
     if       WS-Stock-Key = spaces
          or  Cob-Crt-Status = Cob-Scr-Esc
              perform Stock-Close
              go to ga999-Exit.
     move     function upper-case (WS-Stock-Key) to WS-Stock-Key
                                                    WS-Temp-Stock-Key.
     display  space at line WS-23-lines col 1 with erase eos.
*>
 ga030-Get-Record.
*>     read     Stock-File record key WS-Stock-Key invalid key
     move     1 to File-Key-No.
     perform  Stock-Read-Indexed.
     if       fs-Reply = 23 or = 21
              display ST114 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ga020-Stock-Item-Accept.
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
     perform  Clear-Error-Line.
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
     end-if
*>
*> Redisplay now dates are converted
*>
     display  display-01.
     display  Display-01C.
     if       Stk-Manu-Used = 1
              display Display-02.
*>
*> Get and process new Stock and Abrev keys
*>
     display  "Stock Number     - [" at 1601 with foreground-color 2 erase eol.
     display  "]" at 1634 with foreground-color 2.
     display  "PL Fast key  - [" at 1641 with foreground-color 2.
     display  "]" at 1664 with foreground-color 2.
*>
     display  "* <R> = Renumber  *" at 2261 with foreground-color 2.
     display  "*******************" at 2361 with foreground-color 2.
     display  WS-Stock-Key at 0421 with foreground-color 3.
     display  WS-Stock-Abrev-Key at 0457 with foreground-color 3.
*>
     if       Stock-On-Order not = zero
           or Stock-Back-Ordered not = zero
              display ST109 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ga020-Stock-Item-Accept.
*>
     move     WS-Stock-Key to WS-Save-Stock-Key
                              WS-Temp-Stock-Key.
     move     WS-Stock-Abrev-Key to WS-Temp-Abrev-Key
                                    WS-Save-Abrev-Key.
*>
 ga040-Accept-New-Stock-No.
     accept   WS-Temp-Stock-Key at 1621 with foreground-color 3 update.
     if       WS-Temp-Stock-Key = spaces
           or Cob-Crt-Status = Cob-Scr-Esc
              go to ga010-Display-Stock-Headings.
*>
     move     function upper-case (WS-Temp-Stock-Key) to WS-Temp-Stock-Key.
     display  WS-Stock-Key at 1621 with foreground-color 3.
*>
     accept   WS-Temp-Abrev-Key at 1657 with foreground-color 3 update.
     if       Cob-Crt-Status = Cob-Scr-Esc
          or  Cob-Crt-Status = Cob-Scr-Page-Up
          or  Cob-Crt-Status = Cob-Scr-Key-Up
              go to ga040-Accept-New-Stock-No.
*>
     if       WS-Temp-Abrev-Key not = spaces
              move     function upper-case (WS-Temp-Abrev-Key) to WS-Temp-Abrev-Key
              perform  clear-error-line
     else
              display  ST102 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ga040-Accept-New-Stock-No.
*>
     move     "R" to   escape-code.
     perform  zz100-test-escape.
     if       escape-code = "Q"
         or   Cob-Crt-Status = Cob-Scr-Esc
              go to    ga999-Exit.
*>
     if       escape-code = "B" or = "S"
         or   Cob-Crt-Status = Cob-Scr-Page-Up
          or  Cob-Crt-Status = Cob-Scr-Key-Up
              go to    ga020-Stock-Item-Accept.
*>
     if       escape-code not = "R"
              go to    ga010-Display-Stock-Headings.
*>
 ga050-Accept-Renumber.
     display  "Renumbering Stock Item record, are you sure? [ ]"
                at line WS-22-lines col 1 with foreground-color 2 highlight.
     accept   WS-reply at line WS-22-lines col 47 with foreground-color 6 UPPER.
     if       WS-reply not = "Y" and not = "N"
              go to ga050-Accept-Renumber.
*>
     if       WS-reply = "N"
              go to ga010-Display-Stock-Headings.
     display  space at line WS-22-lines col 1 with erase eol.
*>
     move     WS-Temp-Stock-Key to WS-Stock-Key.
     move     WS-Temp-Abrev-Key to WS-Stock-Abrev-Key.
     perform  Stock-Write.
     if       fs-reply = 22
              display ST117 at line WS-23-lines col 1 with foreground-color 4 highlight
              go to ga040-Accept-New-Stock-No.
     if       fs-reply not = zero
              display  ST000    at line WS-23-lines col 1  with foreground-color 4 highlight
              display  "="      at line WS-23-lines col 37 with foreground-color 4 highlight
              display  fs-reply at line WS-23-lines col 39 with foreground-color 4 highlight
              display  ST003   at line WS-lines col 01
              accept   WS-reply at line WS-lines col 30
              perform  Stock-Close
              go to ga999-Exit.
*>
*>  Created record with new stock number so can delete old one
*>
     move     WS-Save-Stock-Key to WS-Stock-Key.
     move     WS-Save-Abrev-key to WS-Stock-Abrev-Key.
     perform  Stock-Delete.
     if       fs-reply not = zero
              display  ST108 at line WS-23-lines col 1 with foreground-color 4 highlight
              display  fs-reply at line WS-23-lines col 37 with foreground-color 4 highlight
              display  ST006   at line WS-lines col 01
              accept   WS-reply at line WS-lines col 30.
*>
     go       to  ga010-Display-Stock-Headings.
*>
 ga999-Exit.
     exit     section.
*>
*>****************************************************
*>               Common Routines Block               *
*>****************************************************
*>
 zz010-Display-Heading      section.
*>*********************************
*>
  *>   if       menu-reply not = 4
              display  prog-name at 0101 with foreground-color 2 erase eos
              perform  zz020-convert-date
              display  u-date    at 0171 with foreground-color 2
              display  usera     at 0301 with foreground-color 3.
*>
     if       menu-reply = zero
              display  "Stock File Set-Up & Maintenance" at 0124 with foreground-color 2
              display  "Function  Menu"         at 0434 with foreground-color 2
     else
       if     menu-reply = 1
              display  "Stock Record Creation"  at 0129 with foreground-color 2
       else
        if    menu-reply = 2
              display  "Stock Record Amendment" at 0129 with foreground-color 2
        else
         if   menu-reply = 3
              display  "Stock Record Deletion"  at 0129 with foreground-color 2
         else
          if  menu-reply = 5
              display  "Stock Record Display"   at 0129 with foreground-color 2.
*>
 zz010-Exit.
     exit     section.
*>
 zz020-Convert-Date  section.
*>**************************
*>
*> Convert from UK to selected form
*>
     move     to-day to u-date.
     if       Date-USA
              move u-date to WS-date
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              move WS-date to u-date
     end-if
     if       Date-Intl
              move "ccyy/mm/dd" to WS-date   *> swap Intl to UK form
              move u-date (7:4) to WS-Intl-Year
              move u-date (4:2) to WS-Intl-Month
              move u-date (1:2) to WS-Intl-Days
              move WS-date to u-date
     end-if.
*>
 zz020-exit.
     exit     section.
*>
 zz020-Display-Outline      section.
*>*********************************
*>
     perform  zz010-Display-Heading.
 *>    initialize WS-Stock-Record with filler.
     perform  zz070-Initialize-Stock-Record.
     move     spaces to WS-Stock-Key WS-Stock-Abrev-Key WS-Stock-Dates.
     display  Display-01.
*>     if       Stk-Manu-Used = 1
*>              display Display-02.
*>
 zz020-exit.
     exit     section.
*>
 zz030-common-routines      section.
*>*********************************
*>
 zz030-accept-money7.  *> USED
     move     amt-wk-pence7 to WS-pence7.
     move     amt-wk-pds7 to WS-pound7.
     display  WS-amount-screen-display7 at curs with foreground-color 3.
     accept   WS-amount-screen-accept7  at curs with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 zz030-accept-money7b.  *> USED
     move     amt-wk-pence7b to WS-pence7b.
     move     amt-wk-pds7b to WS-pound7b.
     display  WS-amount-screen-display7b at curs with foreground-color 3.
     accept   WS-amount-screen-accept7b  at curs with foreground-color 3 update.
     move     WS-pound7b to amt-wk-pds7b.
     move     WS-pence7b to amt-wk-pence7b.
*>
 zz030-accept-money9a.	*> Not used
     move     zero to WS-poundsd9 WS-penced9 amt-ok9.
*>
 zz030-accept-money9b.	*> Not used
     display  WS-amount-screen-display9 at curs with foreground-color 3.
     accept   WS-amount-screen-accept9  at curs with foreground-color 3 update.
     move     WS-pound9 to amt-wk-pds9.
     move     WS-pence9 to amt-wk-pence9.
*>
 zz030-accept-money9c.  *> USED
     move     amt-wk-pence9 to WS-pence9.
     move     amt-wk-pds9 to WS-pound9.
     display  WS-amount-screen-display9 at curs with foreground-color 3.
     accept   WS-amount-screen-accept9  at curs with foreground-color 3 update.
     move     WS-pound9 to amt-wk-pds9.
     move     WS-pence9 to amt-wk-pence9.
*>
 zz030-exit.
     exit     section.
*>
 zz040-Check-for-Supplier   section.
*>*********************************
*>
     move     zero to Error-Code.
     if       WS-Stock-Supplier = spaces
              go to zz040-Exit.
     if       WS-Stock-Supp-7 = space
              move     WS-Stock-Supplier to customer-code
              move     "C" to maps09-reply
              perform maps09
              if       maps09-reply not = "Y"
                       move 2 to Error-Code
                       display ST103 at line WS-23-lines col 1 with foreground-color 4 highlight
                       go to zz040-Exit
              else
                       move Customer-Code to WS-Stock-Supplier.
*>
     move     WS-Stock-Supplier to WS-Purch-Key
                                   WS-File-Key.
     move     5 to Access-Type.
     perform  Purch-Read-Indexed.
     if       FS-Reply  = zero       *> not = 23 and not = 21
              go to  zz040-Exit.
     move     1 to Error-Code.
     display  ST101 at line WS-23-lines col 1 with foreground-color 4 highlight.
*>
 zz040-Exit.
     exit     section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-test-date
*> output:  u-date/WS-date as uk date format
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
 zz070-Initialize-Stock-Record section.
*>
*> The simple process here is initialise WS-Stock-Record
*>   but some versions of the compiler this doesn't work.
*>      for v3.2 initialise does not work for Stock-TD fields as they
*>          are spaces.
*>     initialise WS-Stock-Record with filler.  *> JIC anything missed
     move     spaces to  WS-Stock-Key
                         WS-Stock-Abrev-Key
                         Stock-Suppliers-Group
                         WS-Stock-Desc
                         Stock-Construct-Item
                         WS-Stock-Location
                         Stock-PA-Code
                         Stock-SA-Code
                         Stock-Services-Flag.
*>
     move     zeros to   Stock-Last-Actual-Cost
                         Stock-Construct-Bundle
                         Stock-Under-Construction
                         Stock-Work-in-Progress
                         Stock-ReOrder-Pnt
                         Stock-Std-ReOrder
                         Stock-Back-Ordered
                         Stock-On-Order
                         Stock-Held
                         Stock-Pre-Sales
                         Stock-Retail
                         Stock-Cost
                         Stock-Value
                         Stock-Order-Due
                         Stock-Order-Date
                         Stock-Adds
                         Stock-Deducts
                         Stock-Wip-Adds
                         Stock-Wip-Deds.
*>
     perform  varying Z1 from 1 by 1 until Z1 > 12
              move     zeros to Stock-TD-Adds (Z1)
                                Stock-TD-Deds (Z1)
                                Stock-TD-Wip-Adds (Z1)
                                Stock-TD-Wip-Deds (Z1)
     end-perform.
*>
 zz070-Exit.
     exit     section.
*>
 zz080-Copy-To-SS  section.
*>************************
*>
     move     Stock-Construct-Bundle        to SS-Stock-Construct-Bundle.
     move     Stock-Under-Construction      to SS-Stock-Under-Construction.
     move     Stock-Work-in-Progress        to SS-Stock-Work-in-Progress.
     move     Stock-ReOrder-Pnt             to SS-Stock-ReOrder-Pnt.
     move     Stock-Std-ReOrder             to SS-Stock-Std-ReOrder.
     move     Stock-Back-Ordered            to SS-Stock-Back-Ordered.
     move     Stock-On-Order                to SS-Stock-On-Order.
     move     Stock-Held                    to SS-Stock-Held.
     move     Stock-Pre-Sales               to SS-Stock-Pre-Sales.
     move     Stock-Retail                  to SS-Stock-Retail.
     move     Stock-Cost                    to SS-Stock-Cost.
     move     Stock-Value                   to SS-Stock-Value.
*>
 zz080-Exit.
     exit     section.
*>
 zz090-Copy-From-SS  section.
*>**************************
*>
     move     SS-Stock-Construct-Bundle     to Stock-Construct-Bundle.
     move     SS-Stock-Under-Construction   to Stock-Under-Construction.
     move     SS-Stock-Work-in-Progress     to Stock-Work-in-Progress.
     move     SS-Stock-ReOrder-Pnt          to Stock-ReOrder-Pnt.
     move     SS-Stock-Std-ReOrder          to Stock-Std-ReOrder.
     move     SS-Stock-Back-Ordered         to Stock-Back-Ordered.
     move     SS-Stock-On-Order             to Stock-On-Order.
     move     SS-Stock-Held                 to Stock-Held.
     move     SS-Stock-Pre-Sales            to Stock-Pre-Sales.
     move     SS-Stock-Retail               to Stock-Retail.
     move     SS-Stock-Cost                 to Stock-Cost.
     move     SS-Stock-Value                to Stock-Value.
*>
 zz090-Exit.
     exit     section.
*>
 zz100-test-escape          section.
*>*********************************
*>
     display  escape-code at 1976 with foreground-color 6.
*>
 zz100-get-escape.
     accept   escape-code at 1976 with foreground-color 6 update UPPER.
*>
     if       escape-code not = "B" and not = "S" and not = "Q"
                      and not = "K" and not = "D" and not = "R"
                      and not = "C" and not = "N"
              go to zz100-get-escape.
*>
 zz100-exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
