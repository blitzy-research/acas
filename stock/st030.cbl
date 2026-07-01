       >>source free
*>*************************************************************
*>                                                            *
*>                  Stock Control Reporting                   *

*>  OPTION 7 NEEDS TO BE TESTED     <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

*>                                                            *
*>*************************************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         st030.
*>**
*>    Author.             V.B.Coen, FBCS
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Stock Reporting.
*>**
*>    Called modules.
*>                        maps04.
*>                        acas011 -> Stock file FH
*>                         stockMT - STOCK-REC RDB table.
*>**
*>    Error messages used.
*>
*>                        ST300.
*>                        ST301.
*>                        ST302.
*>                        ST303.
*>                        ST304.
*>                        ST305.
*>                        ST306.
*>                        ST307.
*>                        ST308.
*>                        ST309. NEW 01/02/25
*>                        ST310. NEW 01/02/25
*>                        ST311. NEW 03/02/25
*>                        ST313.
*>**
*> Changes:
*> 12/06/09 vbc - .00 Written in Cobol from scratch against v2 specs.
*> 18/06/09 vbc - .01 Test 1-Bugs in menus screens, report heads & added
*>                    support for alt key on desc.
*> 18/06/09 vbc - .02-5 Report layout tidy ups with more to follow, no doubt.
*> 19/06/09 vbc - .06 Wip on activity only if used & wip qty or wip history
*>                    nonzero.
*>                .08 Replace trailing spaces on Abrev-To with 'z'.
*> 25/06/09 vbc - .09-10 If range not used force start on Abrev key = 0 to make
*>                    all reads on stock file sequential by Abrev key. Clean up
*>                    positioning of subheadings ie 'All Items' etc, 1 col right.
*> 29/06/09 vbc - .11 Added Stock History report.
*> 22/07/09 vbc - .12/13 Understocked test wrong - Dont ask.
*> 07/09/10 vbc - .14/16 on opt 5 incorrect test for < 0 > 5
*>                    amended lpr to include cpi=12 & Cups printer spool.
*> 11/12/11 vbc -     Changed version from 1.00.xx to 3.01.xx, in keeping with the rest of ACAS
*>                .17 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 04/03/12 vbc - .18 Cleanup: Removed chk char from Stock-Abbrev-key and WS-Stock-Key 4 rdbms
*> 12/05/13 vbc - .19 Changed wsnames to in common as pl010 called in st010.
*> 13/05/13 vbc - .20 Added time to reports.
*> 16/05/13 vbc - .21 Changed wsnames to in copybook see above.
*> 04/06/13 vbc - .22 Replaced Stk-WS-Page-Lines with system WS-Page-Lines.
*> 21/07/16 vbc - .23 Replace Cobol file acces verbs with calls to FH and RDB
*>                    DAL. Precede references to Stock-Record, WS-Stock-Key,
*>                    WS-Stock-Abrev-Key, WS-Stock-Desc by WS- to reflect that we
*>                    are only dealing with a WS record and the FD is now gone.
*>                    Stop using File-Status and replace with call to
*>                    "CBL_CHECK_FILE_EXIST" instead. Do same for all such
*>                    checks, sets etc to kill of usage, dates back to floppies.
*>                    ST011 added. Update version to 3.02.
*> 24/10/16 vbc - .24 ALL programs now using wsnames.cob in copybooks.
*>                    Usage of maps99 redundant so removed.
*> 12/03/18 vbc - .25 acasnnn copylib renaming acas000-open etc to comply with
*>                    rest of ACAS to (System-Open etc) removed unused field
*>                    WS var. error-code.
*> 02/07/20 vbc - .26 Adjust heads for print range using space and not size.
*>                .27 On reports with FLG 'O' not used for zero stocks see
*>                    L35-Flag
*> 08/12/22 vbc - .28 Chgd goto in ZZ050 to use para -Main 4 GC v3.2 warning.
*> 14/08/23 vbc - .29 Added report by Description as option 6,
*>                    using WS-Page-Lines preset to 45 as reporting is Landscape.
*> 16/08/23 vbc       Removed old remarked out Cobol file verbs.
*> 25/02/24 vbc       Removed testing version of st030.cbl-SORT-2 not needed.
*> 30/03/24 vbc       WARNING THIS PROGRAM DOES NOT REPORT ON STOCK-ARRIVAL-DATE
*>                    DUE TO NOT ENOUGH SPACE ON A LINE OF 132 COLS.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 16/12/24 vbc - .30 Changed WS-Page-Lines to 56 as reports are landscape.
*>                    User site to change if wrong for their printers.
*> 26/01/25 vbc - .31 Added menu option 7 - Stock Report by Location so that
*>                    report can be used to verify by stock storage location
*>                    using new alt Stock key - Location.
*>                    RDBMS Record may need an update ? Done.
*>                    Ditto for FH and DAL.  Done.
*> 04/02/25 vbc - .32 Added 'WS-'  to Stock-Location.
*> 14/02/25           READY FOR TESTING - option 7 and from/too set with
*>                      ignore cnt = 3 on test data. DONE.
*>                    TEST code left in at zz025 that skipps doing a page or
*>                    double page break  - SHOULD be changed back if user needs it
*>                    but will use more paper per report.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
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
*>================================
*>
 file section.
*>------------
*>
 copy "fdprint.cob".
*>
 working-storage section.
*>-----------------------
*>
 77  Prog-Name               pic x(15)   value "ST030 (3.3.00)".
 copy "print-spool-command.cob".
 77  Report-Name             pic x(28)   value spaces.
*>
 01  work-fields.
     03  Menu-Reply          pic 9               value zero.
         88  Menu-Level-1-Valid-Options          values 1 thru 7 9.
     03  WS-Reply            pic 9               value zero.
     03  SS-Reply            pic 99              value zeros.
     03  WS-Proc-Month.
         05  WS-Proc-Mth     pic 99              value zero.
             88  WS-Good-Month                   values 01 thru 12.
     03  WS-Partial          pic 9               value zero.
     03  WS-First-Rec        pic 9               value zero.
     03  WS-Stock-From       pic x(13)           value spaces.
     03  WS-Stock-To         pic x(13)           value spaces.
     03  WS-Abrev-From       pic x(7)            value spaces.
     03  WS-Abrev-To         pic x(7)            value spaces.
*>
*> Location can be mixed case
*>
     03  WS-Location-Frm     pic x(10)           value spaces.  *> Used
     03  WS-Location-To      pic x(10)           value spaces.  *>  and used
     03  WS-Location-Not-Ignored
                             pic 9               value zero.    *>  OR used.in chars from left
     03  WS-Location-Frm-Cnt pic 99              value zero.    *> Computed from Loc Frm
     03  WS-Location-To-Cnt  pic 99              value zero.    *> Computed from Loc To
     03  WS-Double-Sided-Prt pic x               value "Y".
     03  WS-Current-Location pic x(10)           value low-values.
*>
     03  WS-3                pic 999.
     03  WS-z6               pic z(6).
     03  WS-z6b              pic z(6).
     03  WS-z6c              pic z(6).
     03  WS-Rec-Total        pic zzz,zzz,zz9.
     03  WS-Current-Period  pic x(10).
     03  WS-Todate-Period   pic x(16).
     03  WS-Total-Value     pic s9(9)v99 comp-3  value zero.
     03  WS-Total-Add    binary-long             value zero.
     03  WS-Total-Ded    binary-long             value zero.
     03  WS-WIP-Total-Add binary-long            value zero.
     03  WS-WIP-Total-Ded binary-long            value zero.
     03  WS-Rec-Cnt      binary-long  unsigned   value zero.
     03  WS-Page-Lines   binary-char  unsigned   value 56.   *> 16/12/24 as system is for Portrait.
     03  Line-Cnt        binary-char  unsigned   value 99.
     03  Page-Nos            pic 9(4)            value zero.
     03  A               binary-char  unsigned   value zero.
     03  B               binary-char  unsigned   value zero.
     03  C               binary-char  unsigned   value zero.
     03  R               binary-char  unsigned   value zero.
     03  X               binary-char  unsigned   value zero.
     03  Z               binary-char  unsigned   value zero.
*>
     03  WS-Lines        binary-char  unsigned   value zero.
     03  WS-22-Lines     binary-char  unsigned   value zero.
     03  WS-23-Lines     binary-char  unsigned   value zero.
     03  WS-env-Lines        pic 999             value zero.
*>
 01  accept-terminator-array pic 9(4)            value zero.
     copy "screenio.cpy".
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
     03  hd-hh               pic xx.
     03  hd-mm               pic xx.
     03  hd-ss               pic xx.
     03  hd-uu               pic xx.
*>
 01  File-Info                          value zero.
     05 File-Size-Bytes      pic 9(18) comp.
     05 Mod-DD               pic 9(2)  comp.
     05 Mod-MO               pic 9(2)  comp.
     05 Mod-YYYY             pic 9(4)  comp.
     05 Mod-HH               pic 9(2)  comp.
     05 Mod-MM               pic 9(2)  comp.
     05 Mod-SS               pic 9(2)  comp.
     05 filler               pic 9(2)  comp. *> Always 00
*>
*> Print layouts
*>
 01  Line-0a                 pic x(19) value "Items ranging from ".
 01  Line-0b                 pic x(9)  value " through ".
 01  Line-0C                 pic x(23) value "Locations ranging from ".
 01  Line-0D                 pic x(9)  value " through ".
*>
 01  Line-0                  pic x(100)    value spaces.
*>
*>
 01  Line-11.       *>  Valuation report
     03  l11-Program         pic x(16)     value spaces.
     03  filler              pic x(39)     value spaces.
     03  l11-title           pic x(42)     value "Stock Valuation Report".
     03  filler              pic x(27)     value spaces.
     03  filler              pic x(5)      value "Page ".
     03  l11-Page            pic zz9.
*>
 01  Line-12.
     03  l12-User            pic x(40).
     03  filler              pic x(76)     value spaces.
     03  l12-Date            pic x(10).
     03  filler              pic x         value space.
     03  L2-HH               pic xx        value spaces.
     03  filler              pic x         value ":".
     03  L2-MM               pic xx        value spaces.
*>
 01  Line-13.        *> Valuation Report
     03  filler              pic x(96)   value
         "<------- Stock ------>                                      Average       Replace     Stock     ".
     03  l13-Lit-Wip         pic xxx     value "WIP".
     03  filler              pic x(24)   value "     Value in    Retail".
*>
 01  Line-14.
     03  filler              pic x(96)   value
         "Abrev    Number         Description                           Cost          Cost        Qty     ".
     03  l14-Lit-WIP         pic xxx     value "Qty".
     03  filler              pic x(24)   value "     Stockroom    Price ".
*>
 01  Line-15.
     03  l15-Abrev-Number    pic x(9).
     03  l15-Stock-Number    pic x(15).          *> 24
     03  l15-Desc            pic x(33).          *> 57
     03  l15-Ave-Cost        pic zzzzz,zz9.9999. *> 71
     03  filler redefines l15-Ave-Cost.
         05  filler          pic x(12).
         05  l15-blank-0     pic xx.
     03  l15-Cost            pic zzzzz,zz9.99.   *> 83
     03  l15-Qty             pic zzzz,zz9.          *> 91
     03  l15-Wip             pic z(7)9.          *> 99
     03  l15-Value           pic zzz,zzz,zz9.99. *> 113
     03  l15-Retail          pic zzzzz,zz9.99.   *> 125
*>
 01  Line-16-Total. *> Total
     03  filler              pic x(86)  value spaces.
     03  filler              pic x(13)  value "Total Value: ".
     03  l16-Value           pic zzz,zzz,zz9.99.
*>
 01  Line-16-Over.
     03  filler              pic x(99) value spaces.
     03  filler              pic x(14) value all "-".
*>
 01  Line-16-Under.
     03  filler              pic x(99) value spaces.
     03  filler              pic x(14) value all "=".
*>
*>
 01  Line-23.       *> Activity Report
     03  filler              pic x(72)   value "<------ Stock ------>                                  Current  Retail  ".
     03  L23-Lit-Average     pic x(13)   value " Average".  *> or "   Unit" (cost)
     03  L23-Lit-Val         pic x(9)    value "  Stock ".
     03  L23-Lit-Cur         pic x(19)   value "<- Current Period >".
     03  L23-Lit-YTD         pic x(19)   value "<- Year to Date -->".
*>
 01  Line-24.
     03  filler              pic x(86)  value "Abrev     Number      Description                       Stock   Price      Cost".
     03  L24-Lit-Val         pic x(11)  value "Value".
     03  filler              pic x(35)  value "Add   Ded    Net   Add   Ded    Net".
*>
 01  Line-25.
     03  L25-Abrev-Number    pic x(8).
     03  L25-Stock-Number    pic x(14).          *> 22
     03  L25-Desc.
         05  filler          pic x(28).
         05  L25-Lit-Wip     pic x(5).           *> 55
     03  L25-Qty             pic zzz,zz9.        *> 62
     03  L25-Retail          pic zzz,zz9.99.     *> 72
     03  L25-Ave-Cost        pic zzz,zz9.99.     *> 82
     03  L25-ValueX.
         05  L25-Value       pic zzzzz,zz9.99.   *> 94
     03  L25-Cur-Add         pic z(5)9.          *> 100
     03  L25-Cur-Ded         pic z(5)9.          *> 106
     03  L25-Cur-Net         pic z(5)9-.         *> 113
     03  L25-YTD-Add         pic z(5)9.          *> 119
     03  L25-YTD-Ded         pic z(5)9.          *> 125
     03  L25-YTD-Net         pic z(5)9-.         *> 132
*>
 01  Line-25B redefines Line-25.
     03  filler              pic x(77).
     03  L25b-Lit-Wip        pic x(17).  *> "Work In Progress:"
     03  filler              pic x(38).
*>
*>
 01  Line-33.           *> ReOrder Report
     03  filler              pic x(132)   value
         "<------ Stock ------>                                     Supp    Stock " &
         "< ReOrder >  Unit     On   <------- Date ------>    Bk   WIP".
*>
 01  Line-34.
     03  filler              pic x(132)  value
         "Abrev     Number     Flg Description                      Number   Qty  " &
         "  Pnt   Qty  Cost    Order  Ordered      Due       Ord   Qty".
*>
 01  Line-35.
     03  L35-Abrev-Number    pic x(8).
     03  L35-Stock-Number    pic x(14).          *> 22
     03  L35-Flag            pic x.
     03  filler              pic xx.             *> 25
     03  L35-Desc            pic x(33).          *> 58
     03  L35-Supplier        pic x(7).           *> 65
     03  L35-Qty             pic z(5)9.          *> 71
     03  L35-ReOrder-Pnt     pic z(5)9.          *> 77
     03  L35-Std-Reorder     pic z(5)9.          *> 83
     03  L35-Cost            pic z(5)9.99.       *> 92
     03  L35-On-Order        pic z(5)9b.         *> 99
     03  L35-Order-Date      pic x(11).
     03  L35-Order-Due       pic x(10).          *> 120
     03  L35-Back-Ordered    pic z(5)9.          *> 126
     03  L35-WIP             pic z(6).           *> 132
*>
*>
 01  line-43.             *> Stock Report  (as in st010 but with range facility) - OPTIONS 4 & 5
     03  filler              pic x(132)  value
         "<------ Stock ------> Supplier  Location     Unit      Unit        Value " &
         "   Number <- ReOrder -> <------- Date ------>  Quantity On".
*>
 01  line-44.
     03  filler              pic x(132)  value
         "Abrev   Number         Number               Price      Cost        in Stk" &
         "   in Stk  Point    Qty   Ordered     Due      Order  B/Ord".
*>
 01  line-45.
     03  l45-Abrev-Stock     pic x(8).
     03  l45-Stock-Number    pic x(14).
     03  l45-Supplier-No     pic x(8).           *> 30
     03  l45-Location        pic x(11).          *> 41
     03  l45-Retail          pic z(6)9.99.       *> 51
     03  l45-Cost            pic z(6)9.9999.     *> 63
     03  l45-Costx redefines l45-Cost.  *> helps to clear fraction of a penny/cent when zero
         05  filler          pic x(10).
         05  l45-Costz       pic xx.
     03  l45-Value           pic zzzzz,zz9.99.   *> 75
     03  l45-Held            pic z(6)9.          *> 82
     03  l45-Reord-Pnt       pic z(6)9.          *> 89
     03  l45-Reord-Qty       pic z(6)9b.         *> 97
     03  l45-Date-Ordered    pic x(11).          *> 108
     03  l45-Date-Due        pic x(10).          *> 118
     03  l45-Qty-Ordered     pic z(6)9.          *> 125
     03  l45-Qty-Back-Ord    pic z(6)9.          *> 132
*>
 01  line-46.
     03  filler              pic x(5)   value spaces.
     03  filler              pic x(13)  value "Description: ".
     03  l46-Desc            pic x(32)  value spaces.
     03  filler              pic x(5)   value spaces.
     03  l46-vars            pic x(77).
*>
*>
 01  Line-61.           *>  Report By Desc EB00
     03  filler              pic x(88)  value "Description                       Abrev    Number             Price      " &
                                           " Cost     Held".
*>
 01  Line-62.
     03  L62-Description     pic x(32)BB.        *> 34
     03  L62-Abrev           pic x(7)BB.         *> 43
     03  L62-Stock-Number    pic x(13)BB.        *> 58
     03  L62-Retail          pic z(6)9.99B.      *> 69
     03  L62-Cost            pic z(6)9.9999B.    *> 82
     03  L62-Held            pic z(4)9        blank when zero.       *> 87
     03  filler              pic x(5).           *> 92
     03  L62-Service         pic x(25).          *> 117
*>
*>
 01  Line-63.             *> History Report
     03  filler              pic x(132)  value "<------ Stock ------>" &
         " Description          This <----------------------------- History for the" &
         " Year ------------------------------->".
*>
 01  Line-64.
     03  filler              pic x(41)  value "Abrev   Number        ".
     03  L64-Lit-Period      pic x(07)  value "Quarter".  *> | " Month " | " Week  "
*>
 01  Line-65.
     03  L65-Abrev-Stock     pic x(8).
     03  L65-Stock-Number    pic x(14).              *> 22
     03  L65-Desc.
         05  filler          pic x(14).
         05  L65-Lit-Wip     pic x(4).
     03  filler              pic x.                  *> 41
     03  L65-This-Period     pic -(6)9.              *> (7)      48
     03  L65-This-Year       pic -(6)9   occurs 12.  *> (84)     132
*>
*>
 01  Line-71.     *> Location Report
     03  filler              pic x(96) value "  Location  Stock Number   Abrev    Description                       " &
                                            "Qty Held  Qty Diff.".
*>
 01  Line-72.
     03  L72-Location        pic x(10)BB.        *> 12
     03  L72-Stock-Number    pic x(13)BB.        *> 27
     03  L72-Abrev-Stock     pic x(7)BB.         *> 36
     03  L72-Desc            pic x(32)BB.        *> 70
     03  L72-Held            pic z(5)9BB.        *> 78
     03  L72-Held-Diff       pic x(18)  value spaces. *> 96
     *>                                  To be filled in, if different with - sign
     *>                                 - if less than printed quantity
*>
*>
 copy "wsstock.cob".     *> 3.2
 copy "wsfnctn.cob".
 copy "wsmaps03.cob".
 copy "wsmaps09.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at ZZ080-ACAS-Calls
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
*>  System wide
     03  ST006               pic x(30) value "ST006 Press return to continue".
*> Module specific
     03  ST300               pic x(32) value "ST300 Stock File not yet created".
     03  ST301               pic x(26) value "ST301 Stock File not found".
                                            *> should not happen as ST300 shown and prog exits - JIC
     03  ST302               pic x(60) value "ST302 There were no Stock numbers within the specified range".
     03  ST303               pic x(66) value "ST303 There were no Abrev Stock numbers within the specified range".
     03  ST304               pic x(53) value "ST304 You cannot specify both Stock AND Abrev numbers".
     03  ST305               pic x(42) value "ST305 Abbreviated Stock number not present".
     03  ST306               pic x(28) value "ST306 Stock Number not found".
     03  ST307               pic x(43) value "ST307 Stock From MUST be less than Stock To".
     03  ST308               pic x(43) value "ST308 Abrev From MUST be less than Abrev To".
     03  ST309               pic x(49) value "ST309 Location Ignored Count must be less than 9".
     03  ST310               pic x(30) value "ST310 Stock Location not found".
     03  ST311               pic x(56) value "ST311 There were no locations within the specified range".
     03  ST313               pic x(23) value "ST313 Bad month in date".
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
 01  To-Day             pic x(10).
*>
 Screen Section.
*>*************
*>
 01  display-01                  background-color cob-color-black  *> ReOrder Rep
                                 foreground-color cob-color-green.
     03  from Prog-Name          pic x(15)          line  1 col  1 blank screen.
     03  from Report-Name        pic x(28)                  col 26.
     03  from WS-Conv-Date       pic x(10)                  col 71.
     03  value "Report Attributes"                  line  3 col 32.
     03  value "Select an Report Option Number : [" line  5 col  1.
     03  using WS-Reply          pic 9                      col 35.
     03  value "]"                                          col 36.
     03  value "(1)   All Stock Items"              line  7 col 10.
     03  value "(2)   A Range of Items"             line  8 col 10.
     03  value "(3)   Items that are Understocked"  line  9 col 10.
     03  value "(4)   Range of Understocked Items"  line 10 col 10.
     03  value "(5)   Items, Not in Stock"          line 11 col 10.
     03  value "(6)   Range of Items, Not in Stock "
                                                    line 12 col 10.
     03  value "(7)   Items on Order"               line 13 col 10.
     03  value "(8)   Range of Items on Order"      line 14 col 10.
     03  value "(9)   Return to Main Menu"          line 16 col 10.
*>
 01  display-02                  background-color cob-color-black  *> Activity Rep
                                 foreground-color cob-color-green.
     03  from Prog-Name          pic x(15)          line  1 col  1 blank screen.
     03  from Report-Name        pic x(28)                  col 26.
     03  from WS-Conv-Date       pic x(10)                  col 71.
     03  value "Report Attributes"                  line  3 col 32.
     03  value "Select an Report Option Number : [" line  5 col  1.
     03  using WS-Reply      pic 9                          col 35.
     03  value "]"                                          col 36.
     03  value "(1)   All Stock Items"              line  7 col 10.
     03  value "(2)   Range of Items"               line  8 col 10.
     03  value "(3)   Items Active in current "     line  9 col 10.
     03  from WS-Current-Period pic x(10)                   col 40.
     03  value "(4)   Items Active in "             line 10 col 10.
     03  from WS-Todate-Period  pic x(16)                   col 32.
     03  value "(5)   Range of active Items in Current "
                                                    line 11 col 10.
     03  from WS-Current-Period pic x(10)                   col 49.
     03  value "(6)   Range of active Items in "    line 12 col 10.
     03  from WS-Todate-Period  pic x(16)                   col 41.
     03  value "(9)   Return to Main Menu"          line 14 col 10.
*>
 01  display-03                  background-color cob-color-black  *> Valuation Rep
                                 foreground-color cob-color-green.
     03  from Prog-Name      pic x(15)              line  1 col  1 blank screen.
     03  from Report-Name    pic x(28)                      col 26.
     03  from WS-Conv-Date   pic x(10)                      col 71.
     03  value "Report Attributes"                  line  3 col 32.
     03  value "Leave fields blank to select All"   line  5 col 24 highlight.
     03  value "Select Stock no. or Abrev Stock no. but NOT both"
                                                    line  6 col 17 highlight.
     03  value "From Stock Number - ["              line  8 col  4.
     03  using WS-Stock-From pic x(13)                      col 25.
     03  value "]"                                          col 38.
     03  value "Enter characters in positions to match"     col 41.
     03  value "  To Stock Number - ["              line  9 col  4.
     03  using WS-Stock-To   pic x(13)                      col 25.
     03  value "]"                                          col 38.
     03  value "Enter characters in positions to match"     col 41.
     03  value "OR"                                 line 10 col 14 highlight.
     03  value "From Abrev Number - ["              line 11 col  4.
     03  using WS-Abrev-From pic x(7)                       col 25.
     03  value "]"                                          col 32.
     03  value "Enter characters in positions to match"     col 41.
     03  value "  To Abrev Number - ["              line 12 col  4.
     03  using WS-Abrev-To   pic x(7)                       col 25.
     03  value "]"                                          col 32.
     03  value "Enter characters in positions to match"     col 41.
*>
*> New 26/1/25 .31
*>
 01  display-04                  background-color cob-color-black  *> Location Rep
                                 foreground-color cob-color-green.
     03  from Prog-Name      pic x(15)              line  1 col  1 blank screen.
     03  from Report-Name    pic x(28)                      col 26.
     03  from WS-Conv-Date   pic x(10)                      col 71.
     03  value "Report Attributes"                  line  3 col 32.
     03  value "Leave these two fields blank, to select All"
                                                    line  5 col 24 highlight.
 *>
     03  value "From Location - ["                  line  8 col  4.
     03  using WS-Location-Frm pic x(10)                    col 21.
     03  value "]"                                          col 31.
     03  value "Enter characters in positions to match"     col 41.
     03  value "  To Location - ["                  line  9 col  4.
     03  using WS-Location-To  pic x(10)                    col 21.
     03  value "]"                                          col 31.
     03  value "Enter characters in positions to match"     col 41.
     03  value "OR"                                 line 10 col 14 highlight.
     03  value "Fixed characters to Ignore - ["     line 11 col  4.
     03  using WS-Location-Not-Ignored   pic 9              col 34.
     03  value "]"                                          col 35.
     03  value "First chars in pos for Page Break"          col 41.
*>
     03  value "Count must be between 0 to 9 & 0 will ignore ANY differences, No page breaks"
                                                    line 13 col 1.
     03  value "A change in these positions will force a new page"
                                                    line 15 col 4.
     03  value "Are you using double sided prints - ["
                                                    line 17 col 1.
     03  using WS-Double-Sided-Prt   pic x                  col 38.
     03  value "] {Y/N}"                                    col 39.
     03  value "(Y will force a New Page when page count is odd number)"
                                                    line 19 col 10.
*>
 procedure  division using WS-calling-data
                           system-record
                           to-day
                           file-defs.
*>****************************************
*>
 AA000-Core                 section.
*>*********************************
*>
     accept   WS-env-Lines from lines.
     if       WS-env-Lines < 24
              move  24 to WS-env-Lines WS-Lines
     else
              move  WS-env-Lines to WS-Lines
     end-if
     subtract 1 from WS-Lines giving WS-23-Lines.
     subtract 2 from WS-Lines giving WS-22-Lines.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
*> Get current date into locale format for display and printing
*>
     perform  ZZ070-Convert-Date.
     move     WS-Date to WS-Conv-Date.
     accept   hdtime from time.
     if       hdtime not = "00000000"
              move hd-hh to L2-HH
              move hd-mm to L2-MM.
*>
*> Set up period descriptives for screen and reports
*>
     move     spaces to WS-Current-Period
                        WS-Todate-Period.
*>
     if       Stk-Period-Cur = "Q"
              move "Quarter" to WS-Current-Period
                                L64-Lit-Period
     else
      if      Stk-Period-Cur = "W"
              move "Week" to WS-Current-Period
              move "   Week" to L64-Lit-Period
      else
              move "  Month" to L64-Lit-Period
              move "Month" to WS-Current-Period.
*>
     if       Stk-Period-dat = "M"
              move "Month To Date" to WS-Todate-Period
     else
      if      Stk-Period-dat = "Q"
              move "Quarter To Date" to WS-Todate-Period
      else
              move "Year To Date" to WS-Todate-Period.
*>
*> New for RDB
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-11  *> Stock file
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    display ST300 at line WS-23-Lines col 1 with foreground-color 4 highlight
                    display ST006   at line WS-Lines col 01
                    accept WS-Reply at line WS-Lines col 32
                    go to aa999-Exit
              end-if
     end-if
*>
     perform  Stock-Open.
     if       FS-Reply not = zero
              display ST301 at line WS-23-Lines col 1 with foreground-color 4 highlight
              display FS-Reply at line WS-23-Lines col 28 with foreground-color 2 highlight
              display ST006   at line WS-Lines col 01
              accept WS-Reply at line WS-Lines col 32
              perform Stock-Close
              go to aa999-Exit.
     move     zero to Menu-Reply.
     perform  Stock-Close.    *> open and close prior to each proc incase Start not used)
*>
*> Good, we now know the stock file exists
*>
 AA010-Display-Headings.
 *>
 *> First time used will use Reports Menu option
 *>
     move     zero to Page-Nos.
     move     99 to Line-Cnt.
     if       Menu-Reply = 1
              move "Stock Valuation Report"       to Report-Name
     else
      if      Menu-Reply = 2
              move "Stock Activity Report "       to Report-Name
      else
       if     Menu-Reply = 3
              move "Stock Re-Order Report "       to Report-Name
       else
        if    Menu-Reply = 4
              move " Stock History Report "       to Report-Name
        else
         if   Menu-Reply = 5
              move "     Stock Report     "       to Report-Name
         else
          if  Menu-Reply = 6
              move "Stock Report by Description"  to Report-Name
          else
           if Menu-Reply = 7    *> New 26/01/25
              move "Stock Report by Location"     to Report-Name
           else
              move "Stock Control - Reports Menu" to Report-Name.
*>
 AA020-Display-Heads.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     if       Menu-Reply = zero
              display  Report-Name at 0127 with foreground-color 2
     else
              display  Report-Name at 0130 with foreground-color 2.
     display  WS-Conv-Date at 0171 with foreground-color 2.
*>
 AA030-DH-End.
     move     to-day to WS-Date.
     move     WS-Month to WS-Proc-Month.
     if       WS-Proc-Month not numeric or not WS-Good-Month
              display ST313 at line WS-23-Lines col 1 with foreground-color 4 highlight
              display WS-Proc-Month at line WS-23-Lines col 25 with foreground-color 2 highlight
              display WS-Date at line WS-23-Lines col 28 with foreground-color 2 highlight
              display ST006   at line WS-Lines col 01
              accept WS-Reply at line WS-Lines col 32
              go to aa999-Exit.
*>
 aa100-Main-Menu.
     display  "Select one of the following by number :- [ ]" at 0401 with foreground-color 2
                                                                          erase eos.
*>
     display  "(1)  Valuation Report"            at 0604 with foreground-color 2.
     display  "(2)  Activity Report"             at 0704 with foreground-color 2.
     display  "(3)  Re-Order Report"             at 0804 with foreground-color 2.
     display  "(4)  Stock History Report"        at 0904 with foreground-color 2.
     display  "(5)  Stock Report"                at 1004 with foreground-color 2.
     display  "(6)  Stock Report by Description" at 1104 with foreground-color 2.
     display  "(7)  Stock Report by Location"    at 1204 with foreground-color 2.
     display  "(9)  Return to System Menu"       at 1404 with foreground-color 2.
*>
 aa110-Accept-Loop.
     move     zero to Menu-Reply.
     accept   Menu-Reply at 0443  with foreground-color 6 auto update.
     if       Menu-Reply = 9
              go to aa999-Exit.
     perform  AA010-Display-Headings.
     if       Menu-Reply not = 6
              perform  ZZ050-Report-Selection.
*> check if quit at level 1
 *>    if       WS-Reply = 9
 *>             go to AA020-Display-Heads.
     if       not Menu-Level-1-Valid-Options  *>  Menu-Reply = 9 OR (not > zero and < 8)
              go to aa110-Accept-Loop.
*>
     display  space at line WS-23-Lines col 1 with erase eol.
     perform  Stock-Open-Input.
*>
     open     output Print-File.
     evaluate Menu-Reply
              when     1
                       perform  BA000-Process-Valuations
              when     2
                       perform  CA000-Process-Activity
              when     3
                       perform  DA000-Process-ReOrder
              when     4
                       perform  FA000-Process-History
              when     5
                       perform  EA000-Process-Stock-Lists
              when     6
                       perform  EB000-Process-Stock-Desc
              when     7
                       perform  GA000-Process-Location
              when     other
                       move     zero to Menu-Reply
                       go       to AA010-Display-Headings
     end-evaluate.
     close    Print-File.
     perform  Stock-Close.
     if       Page-Nos not = zero   *> Don't print blank file
              call  "SYSTEM" using Print-Report.
     move     zero to Menu-Reply.
     go       to AA010-Display-Headings.  *> Might want other reports
*>
 maps04.
     call     "maps04" using maps03-ws.
*>
 aa999-Exit.
     exit     program.
*>
*>***********************************************
*>                  Routines                    *
*>***********************************************
*>
 BA000-Process-Valuations section.
*>*******************************
*>
     if       WS-Abrev-To not = spaces
              perform varying a from 7 by -1 until a < 2 or WS-Abrev-To (a:1) not = space
                      move "z" to WS-Abrev-To (a:1)
              end-perform
     end-if
     if       WS-Stock-From not = spaces
              move WS-Stock-From to WS-Stock-Key
              move   1 to File-Key-No
              set   fn-not-less-than to true     *> Access-Type = 8
              perform Stock-Start
              if    FS-Reply = 21
                    display ST306 at line WS-23-Lines col 1 with foreground-color 4 highlight
                    display ST006   at line WS-Lines col 01
                    accept WS-Reply at line WS-Lines col 32
                    move zero to Access-Type
                    go to ba999-Exit
              end-if
     end-if.
*>
     if       WS-Abrev-From not = spaces
              move WS-Abrev-From to WS-Stock-Abrev-Key
              if   WS-Stock-Abrev-Key (7:1) = space
                   move 0 to WS-Stock-Abrev-Key (7:1)
              end-if
              move   2 to File-Key-No
              set   fn-not-less-than to true     *> Access-Type = 8
              perform Stock-Start
              if    FS-Reply = 21
                    display ST305 at line WS-23-Lines col 1 with foreground-color 4 highlight
                    display ST006   at line WS-Lines col 01
                    accept WS-Reply at line WS-Lines col 32
                    move zero to Access-Type
                    go to ba999-Exit
              end-if
     end-if
     if       WS-Partial = zero
              move  zeros to WS-Stock-Abrev-Key
              move   2 to File-Key-No
              set   fn-not-less-than to true     *> Access-Type = 8
              perform Stock-Start
     end-if
     move     zero to Access-Type.
     move     zero to WS-Total-Value.
     move     spaces to line-15.
*>
 BA010-Read-Rec.
     perform  Stock-Read-Next.
     if       FS-Reply = 10
              go to BA030-Finish-Report.
*>
*> next 2 in case start does not work and its a partial list and before from keys
*>
     if       WS-Stock-From not = spaces
         and  WS-Stock-From > WS-Stock-Key
              go to BA010-Read-Rec.
     if       WS-Abrev-From not = spaces
         and  WS-Abrev-From > WS-Stock-Abrev-Key
              go to BA010-Read-Rec.
*>
     if       Stock-Services-Flag = "Y"     *> IGNORE services
              go to BA010-Read-Rec.
*>
*> next 2 if partial list and past the to keys
*>
     if       WS-Stock-To not = spaces
         and  WS-Stock-Key > WS-Stock-To
              go to BA030-Finish-Report.
*>
     if       WS-Abrev-To not = spaces
         and  WS-Stock-Abrev-Key > WS-Abrev-To
              go to BA030-Finish-Report.
*>
*> Now we can deal with printing the record
*>
 BA020-Print-Rec.
     perform  ZZ010-Print-Heads.
     move     WS-Stock-Abrev-Key to l15-Abrev-Number.
     move     WS-Stock-Key       to l15-Stock-Number.
     move     WS-Stock-Desc      to l15-Desc.
     move     Stock-Last-Actual-Cost to l15-Cost.
     move     Stock-Cost      to l15-Ave-Cost.
     move     Stock-Held      to l15-Qty.
     move     Stock-Value     to l15-Value.
     move     Stock-Retail    to l15-Retail.
     if       l15-Blank-0 = "00"
              move spaces to l15-Blank-0
     end-if
     if       Stk-Manu-Used = 1
              move Stock-Work-in-Progress to l15-Wip
     end-if
     write    Print-Record from Line-15 after 1.
     add      Stock-Value to WS-Total-Value.
     add      1 to Line-Cnt.
     go       to BA010-Read-Rec.
*>
 BA030-Finish-Report.
*>
*> On current page. Enough extra lines for total and if Partial report,
*>      extra 2 lines for from/to line
*>
     if       Page-Nos = zero
        and   (spaces not = WS-Stock-From or not = WS-Stock-To)
              display ST302 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to ba999-Exit.
     if       Page-Nos = zero
        and   (spaces not = WS-Abrev-From or not = WS-Abrev-To)
              display ST303 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to ba999-Exit.
*>
     if       Line-Cnt > WS-Page-Lines - 4
              move 99 to Line-Cnt
              perform ZZ010-Print-Heads.
*>
     move     WS-Total-Value to l16-Value.
     write    Print-Record from Line-16-Over after 2.
     write    Print-Record from Line-16-Total after 1.
     write    Print-Record from Line-16-Under after 1.
*>
 ba999-Exit.
     exit     section.
*>
 CA000-Process-Activity section.
*>*****************************
*>
     if       WS-Abrev-To not = spaces
              perform varying a from 7 by -1 until a < 2 or WS-Abrev-To (a:1) not = space
                      move "z" to WS-Abrev-To (a:1)
              end-perform
     end-if
     move     spaces to line-25.
     if       WS-Stock-From not = spaces
              move WS-Stock-From to WS-Stock-Key
              move    1 to File-Key-No
              set     fn-not-less-than to true         *>    move    8 to Access-Type   *> not <
              perform Stock-Start
              if      FS-Reply = 21                *> invalid key
                      display ST306 at line WS-23-Lines col 1 with foreground-color 4 highlight
                      display ST006   at line WS-Lines col 01
                      accept WS-Reply at line WS-Lines col 32
                      go to ca999-Exit
              end-if
     end-if
*>
     if       WS-Abrev-From not = spaces
              move    WS-Abrev-From to WS-Stock-Abrev-Key
              if      WS-Stock-Abrev-Key (7:1) = space
                      move 0 to WS-Stock-Abrev-Key (7:1)
              end-if
              move    2 to File-Key-No
              set     fn-not-less-than to true         *>    move    8 to Access-Type   *> not <
              perform Stock-Start
              if      FS-Reply = 21                *> invalid key
                      display ST305 at line WS-23-Lines col 1 with foreground-color 4 highlight
                      display ST006   at line WS-Lines col 01
                      accept WS-Reply at line WS-Lines col 30
                      go to ca999-Exit
              end-if
     end-if
     if       WS-Partial = zero
              move  zeros to WS-Stock-Abrev-Key
              move    2 to File-Key-No
              set     fn-not-less-than to true         *>    move    8 to Access-Type   *> not <
              perform Stock-Start
     end-if.
     move     zero to Access-Type.
*>
 CA010-Read-Rec.
     perform  Stock-Read-Next.
     if       FS-Reply = 10
              go to CA030-Finish-Report.
*>
     if       WS-Reply = 1
              go to CA020-Print-Rec.
*>
*> next 2 in case start does not work and its a partial list and before from keys
*>
     if       WS-Stock-From not = spaces
         and  WS-Stock-From > WS-Stock-Key
              go to CA010-Read-Rec.
     if       WS-Abrev-From not = spaces
         and  WS-Abrev-From > WS-Stock-Abrev-Key
              go to CA010-Read-Rec.
*>
*> now for other report variations
*>
     if       WS-Reply = 3 or 5  *> Activity in current period
         and  zero = Stock-Adds and Stock-Deducts and Stock-Wip-Adds and Stock-Wip-Deds
              go to CA010-Read-Rec.
*>
     move     zero to WS-Total-Add WS-Total-Ded.
     move     zero to WS-WIP-Total-Add WS-WIP-Total-Ded.
     perform  varying a from 1 by 1 until a > 12
              add  Stock-TD-Adds (a)      to WS-Total-Add
              add  Stock-TD-Deds (a)      to WS-Total-Ded
              add  Stock-TD-Wip-Adds (a)  to WS-WIP-Total-Add
              add  Stock-TD-Wip-Deds (a)  to WS-WIP-Total-Ded
     end-perform
*>
     if       WS-Reply = 4 or 6  *> Activity in period to date
         and  zero = WS-Total-Add and WS-Total-Ded and WS-WIP-Total-Add and WS-WIP-Total-Ded
              go to CA010-Read-Rec.
*>
*> next 2 if partial list and past the to keys
*>
     if       WS-Stock-To not = spaces
         and  WS-Stock-Key > WS-Stock-To
              go to CA030-Finish-Report.
*>
     if       WS-Abrev-To not = spaces
         and  WS-Stock-Abrev-Key > WS-Abrev-To
              go to CA030-Finish-Report.
*>
 CA020-Print-Rec.
*>
*> Now we can deal with printing the record
*>
     perform  ZZ020-Print-Heads.
     move     WS-Stock-Abrev-Key           to L25-Abrev-Number.
     move     WS-Stock-Key                 to L25-Stock-Number.
     move     WS-Stock-Desc                to L25-Desc.
     if       Stock-Averaging
              move  Stock-Cost             to L25-Ave-Cost
              move  Stock-Value            to L25-Value
     else
              move  spaces                 to L25-ValueX
              move  Stock-Last-Actual-Cost to L25-Ave-Cost
     end-if
     move     Stock-Held                   to L25-Qty.
     move     Stock-Retail                 to L25-Retail.
     move     Stock-Adds                   to L25-Cur-Add.
     move     Stock-Deducts                to L25-Cur-Ded.
     subtract Stock-Deducts from Stock-Adds giving L25-Cur-Net.
*>
     move     WS-Total-Add                 to L25-YTD-Add.
     move     WS-Total-Ded                 to L25-YTD-Ded.
     subtract WS-Total-Ded from WS-Total-Add giving L25-YTD-Net.
     write    Print-Record from Line-25 after 1.
     add      1 to Line-Cnt.
     if       Stk-Manu-Used = 1
         and  (Stock-Work-in-Progress not = zero
          or  Stock-Wip-Adds not = zero or Stock-Wip-Deds not = zero
          or  WS-WIP-Total-Add not = zero or WS-WIP-Total-Ded not = zero)
              move spaces to line-25
              move "Work in Progress:"    to L25b-Lit-Wip
              move Stock-Work-in-Progress to L25-Qty
              move "WIP:"                 to L25-Lit-Wip
              move Stock-Wip-Adds         to L25-Cur-Add
              move Stock-Wip-Deds         to L25-Cur-Ded
              subtract Stock-Wip-Deds from Stock-Wip-Adds giving L25-Cur-Net
              move WS-WIP-Total-Add       to L25-YTD-Add
              move WS-WIP-Total-Ded       to L25-YTD-Ded
              subtract WS-WIP-Total-Ded from WS-WIP-Total-Add giving L25-YTD-Net
              write Print-Record from Line-25 after 1
              add  1 to Line-Cnt
     end-if
     go       to CA010-Read-Rec.
*>
 CA030-Finish-Report.
     if       Page-Nos = zero
        and   (spaces not = WS-Stock-From or not = WS-Stock-To)
              display ST302 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to ca999-Exit.
     if       Page-Nos = zero
        and   (spaces not = WS-Abrev-From or not = WS-Abrev-To)
              display ST303 at line WS-23-Lines col 1 with foreground-color 4 highlight.
*>
 ca999-Exit.
     exit     section.
*>
 DA000-Process-ReOrder section.
*>****************************
*>
     if       WS-Abrev-To not = spaces
              perform varying a from 7 by -1 until a < 2 or WS-Abrev-To (a:1) not = space
                      move "z" to WS-Abrev-To (a:1)
              end-perform
     end-if
     move     spaces to line-35.
     if       WS-Stock-From not = spaces
              move WS-Stock-From to WS-Stock-Key
              move    1 to File-Key-No
              set     fn-not-less-than to true       *>  move    8 to Access-Type   *> =
              perform Stock-Start
              if      FS-Reply = 21
                      display ST306 at line WS-23-Lines col 1 with foreground-color 4 highlight
                      display ST006   at line WS-Lines col 01
                      accept WS-Reply at line WS-Lines col 30
                      go to da999-Exit
              end-if
     end-if
*>
     if       WS-Abrev-From not = spaces
              move WS-Abrev-From to WS-Stock-Abrev-Key
              if   WS-Stock-Abrev-Key (7:1) = space
                   move 0 to WS-Stock-Abrev-Key (7:1)
              end-if
              move    2 to File-Key-No
              set     fn-not-less-than to true       *>  move    8 to Access-Type   *> =
              perform Stock-Start
              if      FS-Reply = 21
                      display ST305 at line WS-23-Lines col 1 with foreground-color 4 highlight
                      display ST006   at line WS-Lines col 01
                      accept WS-Reply at line WS-Lines col 32
                      go to da999-Exit
              end-if
     end-if
     if       WS-Partial = zero
              move  zeros to WS-Stock-Abrev-Key
              move    2 to File-Key-No
              set     fn-not-less-than to true         *>    move    8 to Access-Type   *> not <
              perform Stock-Start
              move     zero to Access-Type
     end-if.
*>
 DA010-Read-Rec.
     perform  Stock-Read-Next.
     if       FS-Reply = 10
              go to DA030-Finish-Report.
*>
     if       WS-Reply = 1              *>  All items
              go to DA020-Print-Rec.
     if       Stock-Services-Flag = "Y"  *> ignore 'services' records
              go to DA010-Read-Rec.
*>
*> next 2 in case start does not work and its a partial list and before from keys
*>
     if       WS-Stock-From not = spaces
         and  WS-Stock-From > WS-Stock-Key
              go to DA010-Read-Rec.
     if       WS-Abrev-From not = spaces
         and  WS-Abrev-From > WS-Stock-Abrev-Key
              go to DA010-Read-Rec.
*>
*> now for other report variations
*>
     if       WS-Reply = 2              *> all items in range
              go to DA013-End-Range-Test.
*>
     if       (WS-Reply = 3 or 4)  *> Understocked
         and  (Stock-ReOrder-Pnt < Stock-Held)
              go to DA010-Read-Rec.
*>
     if       (WS-Reply = 5 or 6)  *> no Stock
         and  (Stock-Held not = zero)
              go to DA010-Read-Rec.
*>
     if       (WS-Reply = 7 or 8)  *> On Order
         and  (Stock-On-Order = zero
         and  Stock-Back-Ordered = zero
         and  Stock-Order-Date = zero
         and  Stock-Order-Due  = zero)
              go to DA010-Read-Rec.
*>
*> Record passed specific tests, so can be included in report subject to next one
*>
 DA013-End-Range-Test.
*>
*> next 2 if partial list and past the to keys
*>
     if       WS-Stock-To not = spaces
         and  WS-Stock-Key > WS-Stock-To
              go to DA030-Finish-Report.
*>
     if       WS-Abrev-To not = spaces
         and  WS-Stock-Abrev-Key > WS-Abrev-To
              go to DA030-Finish-Report.
*>
 DA020-Print-Rec.
*>
*> Now we can deal with printing the record for all within scope
*>
     perform  ZZ030-Print-Heads.
     move     WS-Stock-Abrev-Key              to L35-Abrev-Number.
     move     WS-Stock-Key                    to L35-Stock-Number.
     move     WS-Stock-Desc                   to L35-Desc.
     move     space                           to L35-Flag.
     if       Stock-Held = zero
              move "O" to L35-Flag
     else
      if      Stock-Held < Stock-ReOrder-Pnt
              move "U" to L35-Flag.
*>
     if       Stock-Services-Flag = "Y"
              move space to L35-Flag.
*>
     if       Stock-Averaging
              move  Stock-Cost             to L35-Cost
     else
              move  Stock-Last-Actual-Cost to L35-Cost
     end-if
     move     Stock-Held                   to L35-Qty.
     move     Stock-Supplier-P1            to L35-Supplier.
     move     Stock-ReOrder-Pnt            to L35-ReOrder-Pnt.
     move     Stock-Std-ReOrder            to L35-Std-ReOrder.
     move     Stock-On-Order               to L35-On-Order.
     move     Stock-Back-Ordered           to L35-Back-Ordered.
     if       Stk-Manu-Used = 1
              move Stock-Work-in-Progress  to L35-WIP
     end-if
     if       Stock-Order-Date not = zero
              move Stock-Order-Date to u-bin
              perform ZZ060-Convert-Date
              move WS-date to L35-Order-Date
     else
              move spaces to L35-Order-Date
     end-if
     if       Stock-Order-Due not = zero
              move Stock-Order-Due to u-bin
              perform ZZ060-Convert-Date
              move WS-date to L35-Order-Due
     else
              move spaces to L35-Order-Due
     end-if
     write    Print-Record from Line-35 after 1.
     add      1 to Line-Cnt.
     go       to DA010-Read-Rec.
*>
 DA030-Finish-Report.
     if       Page-Nos = zero
        and   (spaces not = WS-Stock-From or not = WS-Stock-To)
              display ST302 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to da999-Exit.
     if       Page-Nos = zero
        and   (spaces not = WS-Abrev-From or not = WS-Abrev-To)
              display ST303 at line WS-23-Lines col 1 with foreground-color 4 highlight.
*>
 da999-Exit.
     exit     section.
*>
 EA000-Process-Stock-Lists section.
*>********************************
*>
     if       WS-Abrev-To not = spaces
              perform varying a from 7 by -1 until a < 2 or WS-Abrev-To (a:1) not = space
                      move "z" to WS-Abrev-To (a:1)
              end-perform
     end-if
     if       WS-Stock-From not = spaces
              move WS-Stock-From to WS-Stock-Key
              move    1 to File-Key-No
              set     fn-not-less-than to true       *>  move    8 to Access-Type   *> =
              perform Stock-Start
              if      FS-Reply = 21
                      display ST306 at line WS-23-Lines col 1 with foreground-color 4 highlight
                      display ST006   at line WS-Lines col 01
                      accept WS-Reply at line WS-Lines col 32
                      go to ea999-Exit
              end-if
     end-if
*>
     if       WS-Abrev-From not = spaces
              move WS-Abrev-From to WS-Stock-Abrev-Key
              if   WS-Stock-Abrev-Key (7:1) = space
                   move 0 to WS-Stock-Abrev-Key (7:1)
              end-if
              move    2 to File-Key-No
              set     fn-not-less-than to true       *>  move    8 to Access-Type   *> =
              perform Stock-Start
              if      FS-Reply = 21
                      display ST305 at line WS-23-Lines col 1 with foreground-color 4 highlight
                      display ST006   at line WS-Lines col 01
                      accept WS-Reply at line WS-Lines col 32
                      go to ea999-Exit
              end-if
     end-if
     if       WS-Partial = zero
              move  zeros to WS-Stock-Abrev-Key
              move    2 to File-Key-No
              set     fn-not-less-than to true         *>    move    8 to Access-Type   *> not <
              perform Stock-Start
              move     zero to Access-Type
     end-if
     move     spaces to line-45.
     move     zero to WS-Rec-Cnt.
*>
 EA010-Read-Rec.
     perform  Stock-Read-Next.
     if       FS-Reply = 10
              go to EA030-Totals.
*>
*> next 2 in case start does not work and its a partial list and before from keys
*>
     if       WS-Stock-From not = spaces
         and  WS-Stock-From > WS-Stock-Key
              go to EA010-Read-Rec.
     if       WS-Abrev-From not = spaces
         and  WS-Abrev-From > WS-Stock-Abrev-Key
              go to EA010-Read-Rec.
*>
*> next 2 if partial list and past the to keys
*>
     if       WS-Stock-To not = spaces
         and  WS-Stock-Key > WS-Stock-To
              go to EA030-Totals.
*>
     if       WS-Abrev-To not = spaces
         and  WS-Stock-Abrev-Key > WS-Abrev-To
              go to EA030-Totals.
*>
*> Now we can deal with printing the record
*>
 EA020-Print-Rec.
     perform  ZZ040-Print-Heads.
     add      1 to WS-Rec-Cnt.
     move     spaces to line-45.
     move     WS-Stock-Key          to l45-Stock-Number.
     move     WS-Stock-Abrev-Key    to l45-Abrev-Stock.
     move     Stock-Supplier-P1  to l45-Supplier-No.
     move     Stock-Retail       to l45-Retail.
     move     Stock-Cost         to l45-Cost.
     if       l45-Costz = "00"
              move spaces to l45-Costz
     end-if
     if       Stock-Services-Flag not = "Y"
              move  Stock-Value        to l45-Value
              move  Stock-Held         to l45-Held
              move  Stock-ReOrder-Pnt  to l45-Reord-Pnt
              move  Stock-Std-ReOrder  to l45-Reord-Qty
              move  Stock-On-Order     to l45-Qty-Ordered
              move  Stock-Back-Ordered to l45-Qty-Back-Ord
     end-if
     move     WS-Stock-Location        to l45-Location.
     if       Stock-Order-Date not = zero
              move Stock-Order-Date to u-bin
              perform ZZ060-Convert-Date
              move WS-date to l45-Date-Ordered
     else
              move spaces to l45-Date-Ordered
     end-if
     if       Stock-Order-Due not = zero
              move Stock-Order-Due to u-bin
              perform ZZ060-Convert-Date
              move WS-date to l45-Date-Due
     else
              move spaces to l45-Date-Due
     end-if
     move     WS-Stock-Desc to l46-Desc.
     move     1 to a.
     move     spaces to l46-vars.
     if       Stock-Supplier-P2 not = spaces
           or Stock-Supplier-P3 not = spaces
              string "Secondary Suppliers" delimited by size into l46-vars pointer a
              if Stock-Supplier-P2 not = spaces
                  string " 1: "            delimited by size
                         Stock-Supplier-P2 delimited by size into l46-vars pointer a
              end-if
              if Stock-Supplier-P3 not = spaces
                  string " 2: "            delimited by size
                         Stock-Supplier-P3 delimited by size into l46-vars pointer a
              end-if
              add 2 to a
     end-if
     if       Stock-SA-Code not = spaces
              string "SA Code: "           delimited by size
                     Stock-SA-Group        delimited by size into l46-vars pointer a
              add 2 to a
     end-if
     if       Stock-PA-Code not = spaces
              string "PA Code: "           delimited by size
                     Stock-PA-Group        delimited by size into l46-vars pointer a
     end-if
*>
     if       Stock-Pre-Sales not = zero
              move Stock-Pre-Sales to WS-z6
              string "  Pre Sales :"       delimited by size
                     WS-z6                 delimited by size into l46-vars pointer a
     end-if
     if       Line-Cnt > 6
              move all "-" to Print-Record
              write Print-Record after 1
              write Print-Record from line-45 after 1
              add   2 to Line-Cnt
     else
              add   1 to Line-Cnt
              write Print-Record from line-45 after 1
     end-if
     write    Print-Record from line-46 after 1.
     add      1 to Line-Cnt.
     move     spaces to Print-Record.
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
                                into Print-Record
              end-string
              write  Print-Record after 1
              add 1 to Line-Cnt
     end-if
     if       Stock-Services-Flag = "Y"
              move "Services only Product" to Print-Record
              write  Print-Record after 1
              add 1 to Line-Cnt
     end-if
     go       to EA010-Read-Rec.
*>
 EA030-Totals.
     if       Page-Nos = zero
        and   (spaces not = WS-Stock-From or not = WS-Stock-To)
              display ST302 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to ea999-Exit.
     if       Page-Nos = zero
        and   (spaces not = WS-Abrev-From or not = WS-Abrev-To)
              display ST303 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to ea999-Exit.
*>
     if       Line-Cnt > WS-Page-Lines - 3
              add 60 to Line-Cnt
              perform ZZ040-Print-Heads.
     move     spaces to Print-Record.
     move     WS-Rec-Cnt to WS-Rec-Total.
     string   " Total stock records Printed " delimited by size
              function trim (ws-Rec-Total leading) delimited by size into Print-Record.
     write    Print-Record after 3.
*>
 ea999-Exit.
     exit     section.
*>
 EB000-Process-Stock-Desc section.
*>*******************************
*>
     move     spaces to Line-62.
     move     spaces to WS-Stock-Desc.
     move     3 to File-Key-No.
     set      fn-not-less-than to true.
     perform  Stock-Start.
     move     zero to WS-Rec-Cnt.
*>
 EB010-Read-Rec.
     move     3 to File-Key-No.
     perform  Stock-Read-Next.
     if       FS-Reply = 10
              go to EB030-Totals.
*>
*> Now we can deal with printing the record
*>
 EB020-Print-Rec.
     perform  ZZ035-Print-Heads.
     add      1 to WS-Rec-Cnt.
*>
     move     WS-Stock-Key             to L62-Stock-Number.
     move     WS-Stock-Abrev-Key       to L62-Abrev.
     MOVE     WS-Stock-Desc            to L62-Description.
     move     Stock-Retail             to L62-Retail.
     move     Stock-Cost               to L62-Cost.
     if       Stock-Services-Flag not = "Y"
              move  Stock-Held         to L62-Held
              move  spaces to L62-Service
     else
              move zero to L62-Held
              move "Services only Product" to L62-Service.

     write    Print-Record from Line-62 after 1.
     add      1 to Line-Cnt.
     move     spaces to Print-Record.
     go       to EB010-Read-Rec.
*>
 EB030-Totals.
     if       Line-Cnt > WS-Page-Lines - 3
              add 60 to Line-Cnt
              perform ZZ035-Print-Heads.
     move     spaces to Print-Record.
     move     WS-Rec-Cnt to WS-Rec-Total.
     string   " Total stock records Printed " delimited by size
              function trim (ws-Rec-Total leading) delimited by size into Print-Record.
     write    Print-Record after 2.
*>
 EB999-Exit.  exit section.
*>
 FA000-Process-History section.
*>****************************
*>
     if       WS-Abrev-To not = spaces
              perform  varying a from 7 by -1 until a < 2 or WS-Abrev-To (a:1) not = space
                       move "z" to WS-Abrev-To (a:1)
              end-perform
     end-if
     if       WS-Stock-From not = spaces
              move     WS-Stock-From to WS-Stock-Key
              move     1 to File-Key-No
              set      fn-not-less-than to true       *>  move    8 to Access-Type   *> =
              perform  Stock-Start
              if       FS-Reply = 21
                       display ST306 at line WS-23-Lines col 1 with foreground-color 4 highlight
                       display ST006   at line WS-Lines col 01
                       accept WS-Reply at line WS-Lines col 32
                       go to FA999-Exit
              end-if
     end-if
*>
     if       WS-Abrev-From not = spaces
              move     WS-Abrev-From to WS-Stock-Abrev-Key
              if       WS-Stock-Abrev-Key (7:1) = space
                       move zero to WS-Stock-Abrev-Key (7:1)
              end-if
              move     2 to File-Key-No
              set      fn-not-less-than to true       *>  move    8 to Access-Type   *> =
              perform  Stock-Start
              if       FS-Reply = 21
                       display ST305 at line WS-23-Lines col 1 with foreground-color 4 highlight
                       display ST006   at line WS-Lines col 01
                       accept WS-Reply at line WS-Lines col 32
                       go to FA999-Exit
              end-if
     end-if
     if       WS-Partial = zero
              move     zeros to WS-Stock-Abrev-Key
              move     2 to File-Key-No
              set      fn-not-less-than to true         *>    move    8 to Access-Type   *> not <
              perform  Stock-Start
              move     zero to Access-Type
     end-if
     move     zero     to WS-Rec-Cnt c.
     move     spaces   to Line-65.
*>
 FA010-Read-Rec.
     perform  Stock-Read-Next.
     if       FS-Reply = 10
              go to FA030-Finish-Report.
*>
*> next 2 in case start does not work and its a partial list and before from keys
*>
     if       WS-Stock-From not = spaces
         and  WS-Stock-From > WS-Stock-Key
              go to FA010-Read-Rec.
     if       WS-Abrev-From not = spaces
         and  WS-Abrev-From > WS-Stock-Abrev-Key
              go to FA010-Read-Rec.
*>
*> next 2 if partial list and past the to keys
*>
     if       WS-Stock-To not = spaces
         and  WS-Stock-Key > WS-Stock-To
              go to FA030-Finish-Report.
*>
     if       WS-Abrev-To not = spaces
         and  WS-Stock-Abrev-Key > WS-Abrev-To
              go to FA030-Finish-Report.
*>
*> Now we can deal with printing the record
*>
 FA020-Print-Rec.
     add      1 to WS-Rec-Cnt.
     perform  ZZ045-Print-Heads.
     move     WS-Stock-Abrev-Key to L65-Abrev-Stock.
     move     WS-Stock-Key       to L65-Stock-Number.
     move     WS-Stock-Desc      to L65-Desc.
     add      Stock-Adds Stock-Deducts giving L65-This-Period.
     perform  varying a from 1 by 1 until a > 12
              add Stock-TD-Adds (a) Stock-TD-Deds (a) giving L65-This-Year (a)
     end-perform
     write    Print-Record from Line-65 after 1.
     add      1 to Line-Cnt.
*>
     if       Stk-Manu-Used = 1
              move     spaces to Line-65
              move     zero to b                     *> dont bother printing WIPs if all zero
              if       Stock-Wip-Adds not = zero
                or     Stock-Wip-Deds not = zero
                       move 1 to b
              end-if
              perform  varying a from 1 by 1 until a > 12
                       if       Stock-TD-WIP-Adds (a) not = zero
                         or     Stock-TD-WIP-Deds (a) not = zero
                                move 1 to b
                       end-if
              end-perform
              if       b not = zero
                       add      Stock-Wip-Adds Stock-Wip-Deds giving L65-This-Period
                       perform  varying a from 1 by 1 until a > 12
                                add Stock-TD-WIP-Adds (a) Stock-TD-WIP-Deds (a)
                                                          giving L65-This-Year (a)
                       end-perform
                       move     "WIP:" to L65-Lit-Wip
                       write    Print-Record from Line-65 after 1
                       add      1 to Line-Cnt
                       move     1 to c
              end-if
     end-if
     go       to FA010-Read-Rec.
*>
 FA030-Finish-Report.
*>
*> On current page. Enough extra lines for total and if Partial report,
*>      extra 2 lines for from/to line
*>
     if       Page-Nos = zero
        and   (spaces not = WS-Stock-From or not = WS-Stock-To)
              display ST302 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to FA999-Exit.
     if       Page-Nos = zero
        and   (spaces not = WS-Abrev-From or not = WS-Abrev-To)
              display ST303 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to FA999-Exit.
*>
     if       Line-Cnt > WS-Page-Lines - 5
              add 60 to Line-Cnt
              perform ZZ045-Print-Heads.
     move     spaces to Print-Record.
     move     WS-Rec-Cnt to WS-Rec-Total.
     string   " Total stock records Printed " delimited by size
              function trim (ws-Rec-Total leading) delimited by size into Print-Record.
     write    Print-Record after 2.
*>
     if       Stk-Manu-Used = 1
         and  c = zero
              move "WIP records were present but none had data" to Print-Record
              write Print-Record after 2.
*>
 FA999-Exit.
     exit     section.
*>
 GA000-Process-Location section.
*>*****************************
*>
*>  SEE ZZ025 for page break coding that is current changed for write 1 or two lines on change of location
*>   instead of a page or double page (on odd page #) for testing to reduce wasting paper.
*>
     move     zero to WS-Rec-Cnt
                      C.
     move     spaces to Line-72.
     move     low-values to WS-Current-Location.
*>
*> 1st time through Line-cnt will be > 99
*>
     if       WS-Location-Frm-Cnt > 0
              move     WS-Location-Frm to WS-Stock-Location
     else
              move     low-values      to WS-Stock-Location.
*>
     move     4 to File-Key-No.
     set      fn-greater-than to true.
     perform  Stock-Start.
     if       FS-Reply = 21 or = 23
              display ST310 at line WS-23-Lines col 1 with foreground-color 4 highlight
              display ST006   at line WS-Lines col 01
              accept WS-Reply at line WS-Lines col 32
              go to GA999-Exit.
*>
 GA010-Read-Rec.
     perform  until FS-Reply = 10
              perform  Stock-Read-Next
              if       FS-Reply = 10
                       exit perform
              end-if
              if       WS-Current-Location = low-values  *> Only done the once
                       move     WS-Stock-Location to WS-Current-Location
              end-if
              if       WS-Location-To-Cnt not = zero
                and    WS-Stock-Location (1:WS-Location-To-Cnt) >
                                            WS-Location-To (1:WS-Location-To-Cnt)
                       exit perform
              end-if
              if       WS-Location-Frm-Cnt not = zero
                and    WS-Stock-Location (1:WS-Location-Frm-Cnt) <
                                            WS-Location-Frm (1:WS-Location-Frm-Cnt)
                       exit perform cycle     *> Skip record
              end-if
*>
*> Have a record in range if Frm / To in use
*> Now we can deal with printing the record
*>
              perform  ZZ025-Print-Heads
              move     WS-Stock-Abrev-Key to L72-Abrev-Stock
              move     WS-Stock-Key       to L72-Stock-Number
              move     WS-Stock-Desc      to L72-Desc
              move     WS-Stock-Location  to L72-Location
              move     Stock-Held         to L72-Held
*>
              write    Print-Record from Line-72 after 1
              add      1 to WS-Rec-Cnt
              add      1 to Line-Cnt
 *>             move     WS-Stock-Location  to WS-Current-Location
*> above is in wrong place
              exit perform cycle
     end-perform.
*>
 GA030-Finish-Report.
*>
*> On current page. Enough extra lines for total,
*>
     if       Page-Nos = zero
              display ST311 at line WS-23-Lines col 1 with foreground-color 4 highlight
              go to GA999-Exit.
*>
     if       Line-Cnt > WS-Page-Lines - 7
              move 250 to Line-Cnt
              perform ZZ025-Print-Heads.
*>
     move     spaces to Print-Record.
     move     WS-Rec-Cnt to WS-Rec-Total.
     string   " Total Stock records Printed " delimited by size
              function trim (ws-Rec-Total leading) delimited by size into Print-Record.
     write    Print-Record after 2.
     move     " Date / Time Stock Check Completed :                                 By"
              to Print-Record.
     write    Print-Record after 3.
     move     " Date / Time Stock Added/Removed from Stock Control :                By"
              to Print-Record.
     write    Print-Record after 2.
*>
*> Next two only for testing
*>
 *>    display  ST006        at line WS-23-Lines col 1 with foreground-color 4 erase eos.
 *>    accept   Accept-Reply at line WS-23-Lines col 32.
*>
 GA999-Exit.
     exit     section.
*>
*>***********************************************
*>           Common Routines                    *
*>***********************************************
*>
 ZZ002-Print-Head-Top      section.
*>********************************
*>
     add      1            to Page-Nos.
     move     Prog-Name    to l11-Program.
     move     Page-Nos     to l11-Page.
     move     Usera        to l12-User.
     move     WS-Conv-Date to l12-Date.
     move     Report-Name  to l11-Title.
     if       Page-Nos not = 1
              write Print-Record from Line-11 after page
              move Line-12 to Print-Record
              if    b > 1
                    move Line-0 (1:b) to Print-Record (a:b)
              end-if
              write Print-Record after 1
              move  spaces to Print-Record
              write Print-Record after 1
     else
              write Print-Record from Line-11 before 1
              move Line-12 to Print-Record
              if    b > 1
                    move Line-0 (1:b) to Print-Record (a:b)
              end-if
              write Print-Record before 1
     end-if
     move     6 to Line-Cnt.
*>
     move     spaces to Print-Record
                        line-0.
 ZZ002-Exit.
     exit     section.
*>
 ZZ004-String-Range        section.
*>********************************
*>
*>      b is set prior to call
*> Insert 'Items ranging from '
*>
     string   Line-0a            delimited by size into Line-0 pointer b.
*> Insert stock-from or 'Start'
     if       spaces not = WS-Stock-From or not = WS-Stock-To
              if  WS-Stock-From = spaces
                  string "Start"       delimited by size into Line-0 pointer b
              else
                  string WS-Stock-From delimited by space into Line-0 pointer b
              end-if
*> Insert 'through'
              string Line-0b           delimited by size into Line-0 pointer b
*> Insert stock-to or 'End'
              if  WS-Stock-To = spaces
                  string "End"         delimited by size into Line-0 pointer b
              else
                  string WS-Stock-To   delimited by space into Line-0 pointer b
              end-if
     else
*>
*>  Must be Abrev so do similar as above but abrev may be missing trailing chars
*>
              if WS-Abrev-From = spaces
                  string "Start"       delimited by size into Line-0 pointer b
              else
                  string function trim (ws-Abrev-From trailing)
                                       delimited by space into Line-0 pointer b
              end-if
              string Line-0b           delimited by size into Line-0 pointer b
              if  WS-Abrev-To = spaces
                  string "End"         delimited by size into Line-0 pointer b
              else
                  string WS-Abrev-To   delimited by space into Line-0 pointer b
              end-if
     end-if
     compute a = (132 - b + 2) / 2.
*>
 ZZ004-Exit.
     exit     section.
*>
 ZZ006-String-Range        section.
*>********************************
*>
*>      b is set prior to call   <<<<<
*> Insert 'Locations ranging from '
*>
     string   Line-0C                  delimited by size into Line-0 pointer b.
*> Insert Location-From or 'Start'
     if       spaces not = WS-Location-Frm or not = WS-Location-To
              if  WS-Location-Frm = spaces
                  string "Start"       delimited by size into Line-0 pointer b
              else
                  string function trim (WS-Location-Frm trailing)
                                       delimited by space into Line-0 pointer b
              end-if
*> Insert 'through'
              string Line-0D           delimited by size  into Line-0 pointer b
*> Insert Location-To or 'End'
              if  WS-Location-To = spaces
                  string "End"         delimited by size  into Line-0 pointer b
              else
                  string function trim (WS-Location-To trailing)
                                       delimited by space into Line-0 pointer b
              end-if
     end-if.
*>
*>  Chars # to cause double page break (if page ' Odd) else single page break.
*>
     if       WS-Location-Not-Ignored > zero
              string ", field size for page break : "
                                       delimited by size into Line-0 pointer b
              string WS-Location-Not-Ignored
                                       delimited by size into Line-0 pointer b
     else
              string ", field size for page break : Not Used"
                                       delimited by size into Line-0 pointer b
     end-if
     compute a = (132 - b + 2) / 2.
*>
 ZZ006-Exit.
     exit     section.
*>
 ZZ010-Print-Heads         section.
*>********************************
*>      Valuation
*>
     if       Line-Cnt not > WS-Page-Lines
              go to ZZ010-Exit.
     move     1 to b.
     move     spaces to Line-0.
     if       WS-Partial = 1
              perform ZZ004-String-Range
     else
              string "All Items"       delimited by size into Line-0 pointer b
              compute a = (132 - b + 2) / 2.
     perform  ZZ002-Print-Head-Top.
*>
     if       Stk-Manu-Used = zero
              move spaces to l13-Lit-WIP l14-Lit-WIP
     else
              move "WIP"  to l13-Lit-WIP
              move "Qty"  to l14-Lit-WIP
     end-if
     write    Print-Record from Line-13 after 1.
     write    Print-Record from Line-14 after 1.
*>
     move     spaces to Print-Record.
     write    Print-Record after 1.
*>
 ZZ010-Exit.
     exit     section.
*>
 ZZ020-Print-Heads         section.
*>********************************
*>    Activity
*>
     if       Line-Cnt not > WS-Page-Lines
              go to ZZ020-Exit.
*>
*> Build report Sub title based on sub menu selection and print it + field heads
*>
     move     1 to b.
     if       WS-Reply = 1 or 2
              string "All" delimited by size into Line-0 pointer b
     end-if
     if       WS-Reply = 3 or 5
              string "Active in Current "   delimited by size
                     WS-Current-Period      delimited by " " into Line-0 pointer b
     end-if
     if       WS-Reply = 4 or 6
              string "Active in "           delimited by size
                     WS-Todate-Period       delimited by "  "
                     " To Date"             delimited by size into Line-0 pointer b
     end-if
     add      1 to b.
     if       WS-Partial = 1
              perform ZZ004-String-Range
     else
              string "Items" delimited by size into Line-0 pointer b
              compute  a = (132 - b + 2) / 2
     end-if  *>  Next bit should work with any compiler (unless you know better)
     perform  ZZ002-Print-Head-Top.
*>
     if       Stock-Averaging
              move " Average" to L23-Lit-Average
              move " Stock"   to L23-Lit-Val
              move "Value"    to L24-Lit-Val
     else
              move "   Unit"  to L23-Lit-Average
              move spaces     to L23-Lit-Val L24-Lit-Val
     end-if
*>
*>  Set up period and to date heads
*>
     if       Stk-Period-Cur = "Q"
              move "< Current Quarter >" to L23-Lit-Cur
     else
      if      Stk-Period-Cur = "W"
              move "<- Current Week -->" to L23-Lit-Cur
      else
              move "<- Current Month ->" to L23-Lit-Cur.

     if       Stk-Period-Dat = "Q"
              move "< Quarter to Date >" to L23-Lit-YTD
     else
              move "<- Year to Date -->" to L23-Lit-YTD.
*>
     write    Print-Record from Line-23 after 1.
     write    Print-Record from Line-24 after 1.
     move     spaces to Print-Record.
     write    Print-Record after 1.
*>
 ZZ020-Exit.
     exit     section.
*>
 ZZ025-Print-Heads         section.
*>********************************
*>
*>     Location
*>
*>
*>  SEE code for page break coding that is current changed for write 1 or two lines on change of location
*>   instead of a page or double page (on odd page #) for testing to reduce wasting paper.
*>
*>   TEST CODE PRESENT so that paper not wasted.
*>
     if       WS-Location-Not-Ignored > zero
     and      Page-Nos > zero
     and      WS-Stock-Location (1:WS-Location-Not-Ignored) not =
              WS-Current-Location (1:WS-Location-Not-Ignored)
              add      10 Page-Nos giving Z       *> So forcing a remainder value but not really needed
              divide   2 into Z giving X Remainder R
              if       WS-Double-Sided-Prt = "Y"
               and     R > zero               *> we have an ODD Page number
                       add      2 to Line-Cnt    *> ONLY FOR TESTING and not using after page
                       move     spaces to Print-Record
 *>                      write    Print-Record after page  *> AFTER TESTING
                       write    Print-Record after 2     *> page  *> FOR TESTING remove after
 *>                      move     128  to Line-Cnt         *> AFTER TESTING add back.
              else
               if      WS-Double-Sided-Prt = "N"  *> do a blank line
                and    R > zero               *> we have an ODD Page number
  *>                     add      128 to Line-Cnt    *> AFTER TESTING
                       add      1 to Line-Cnt           *> These 3 for TESTING
                       move     spaces to Print-Record
                       write    Print-Record after 1
               end-if
              end-if
              move     WS-Stock-Location  to WS-Current-Location
     end-if
*>
     if       Line-Cnt not > WS-Page-Lines
              go to ZZ025-Exit.
*>
*> Build report Sub title based on sub menu selection and print it + field heads
*>
     move     1 to b.
     if       WS-Partial = 1
              perform ZZ006-String-Range
     else
              string "All Items"       delimited by size into Line-0 pointer b
              compute a = (132 - b + 2) / 2.
     perform  ZZ002-Print-Head-Top.
*>
     write    Print-Record from Line-71 after 1.
     move     spaces to Print-Record.
     write    Print-Record after 1.
*>
 ZZ025-Exit.
     Exit     section.
*>
 ZZ030-Print-Heads         section.
*>********************************
*>     Reorder
*>
     if       Line-Cnt not > WS-Page-Lines
              go to ZZ030-Exit.
*>
*> Build report Sub title based on sub menu selection and print it + field heads
*>
     move     1 to b.
     if       WS-Reply = 1 or 2
              string "All " delimited by size into Line-0 pointer b
     end-if
     if       WS-Reply = 3 or 4
              string "Understocked " delimited by size into Line-0 pointer b
     end-if
     if       WS-Reply = 5 or 6
              string "Not in Stock " delimited by size into Line-0 pointer b
     end-if
     if       WS-Reply = 7 or 8
              string "On Order " delimited by size into Line-0 pointer b
     end-if
     if       WS-Partial = 1
              perform ZZ004-String-Range
     else
              string "Items" delimited by size into Line-0 pointer b
              compute  a = (132 - b + 2) / 2
     end-if
     perform  ZZ002-Print-Head-Top.
*>
     write    Print-Record from Line-33 after 1.
     write    Print-Record from Line-34 after 1.
     move     spaces to Print-Record.
     write    Print-Record after 1.
*>
 ZZ030-Exit.
     Exit     section.
*>
 ZZ035-Print-Heads         section.
*>********************************
*>
*>  Stock Lists by Description
*>
     if       Line-Cnt not > WS-Page-Lines
              go to ZZ035-Exit.
*>
     move     1 to b.
     string   "All Items"       delimited by size into Line-0 pointer b
              compute a = (132 - b + 2) / 2.
     perform  ZZ002-Print-Head-Top.
*>
     write    Print-Record from Line-61 after 1.
     move     spaces to Print-Record.
     write    Print-Record after 1.
     move     5 to Line-Cnt.
*>
 ZZ035-Exit.  exit section.
*>
 ZZ040-Print-Heads         section.
*>********************************
*>
*>  Stock Lists
*>
     if       Line-Cnt not > WS-Page-Lines
              go to ZZ040-Exit.
*>
     move     1 to b.
     if       WS-Partial = 1
              perform ZZ004-String-Range
     else
              string "All Items"       delimited by size into Line-0 pointer b
              compute a = (132 - b + 2) / 2.
     perform  ZZ002-Print-Head-Top.
*>
     write    Print-Record from Line-43 after 1.
     write    Print-Record from Line-44 after 1.
     move     spaces to Print-Record.
     write    Print-Record after 1.
*>
 ZZ040-Exit.
     exit     section.
*>
 ZZ045-Print-Heads         section.
*>********************************
*>
*> Stock History
*>
     if       Line-Cnt not > WS-Page-Lines
              go to ZZ045-Exit.
*>
     move     1 to b.
     if       WS-Partial = 1
              perform ZZ004-String-Range
     else
              string "All Items"       delimited by size into Line-0 pointer b
              compute a = (132 - b + 2) / 2.
     perform  ZZ002-Print-Head-Top.
*>
     write    Print-Record from Line-63 after 1.
     write    Print-Record from Line-64 after 1.
     move     spaces to Print-Record.
     write    Print-Record after 1.
*>
 ZZ045-Exit.
     exit     section.
*>
 ZZ050-Report-Selection  section.
*>******************************
 ZZ050-Report-Selection-Main.
*>
*>  Common for all reports
*>
     move     spaces to WS-Stock-From WS-Stock-To
                        WS-Abrev-From WS-Abrev-To
                        WS-Location-Frm WS-Location-To.
     move     zeroes to WS-Partial WS-First-Rec WS-Reply
                        WS-Location-Not-Ignored
                        WS-Location-Frm-Cnt
                        WS-Location-To-Cnt.
*>
     if       Menu-Reply = 1    *> Valuation report, only get stk no. range
              go to ZZ050-Get-Disp-03.
     if       Menu-Reply = 3    *> ReOrder reports
              go to ZZ050-Get-Disp-01.
     if       Menu-Reply = 4 or = 5    *> Stock item or History report
              go to ZZ050-Get-Disp-03.
     if       Menu-Reply = 7           *> By Location / range of locations
              go to ZZ050-Get-Disp-04.
     if       Menu-Reply = 6           *> should not get here !
              go to ZZ050-Exit.
*>
*> If here, its a Activity report  (2)
*>
     accept   display-02.
     if       WS-Reply = 9
              go to ZZ050-Exit.
     if       WS-Reply < 1 or > 6
              go to ZZ050-Report-Selection-Main.
     if       WS-Reply = 2 or 5 or 6   *>  2(range), 5(Range current period), 6(range todate)
              go to ZZ050-Get-Disp-03.
*>
*> now left with 1 (All), 3 All current period) & 4 (All, Period to date)
*>
     go       to ZZ050-Exit.
*>
 ZZ050-Get-Disp-01.
*>
*>  Setup for Reorder
*>
     accept   display-01.
     if       WS-Reply = 9
              go to ZZ050-Exit.
     if       WS-Reply < 1
              go to ZZ050-Get-Disp-01.
     if       WS-Reply = 2 or 4 or 6 or 8  *> 2(range), 4(Range understock), 6(range unstock)
                                           *> 8 (Range on Order)
              go to ZZ050-Get-Disp-03.
*>
*> now left with 1 (All), 3 All understocked), 5 (All, unstocked) & 7 (all on order)
*>
     go       to ZZ050-Exit.
*>
 ZZ050-Get-Disp-03.
     accept   display-03.
     move     function upper-case (ws-Stock-From) to WS-Stock-From.
     move     function upper-case (ws-Stock-To)   to WS-Stock-To.
     move     function upper-case (ws-Abrev-From) to WS-Abrev-From.
     move     function upper-case (ws-Abrev-To)   to WS-Abrev-To.
*>
*> Cant have both Stock and Abrev in any combination
*>
     if       (ws-Stock-From not = spaces and WS-Abrev-From not = spaces)
          or  (ws-Stock-To   not = spaces and WS-Abrev-To   not = spaces)
          or  (ws-Stock-From not = spaces and WS-Abrev-To   not = spaces)
          or  (ws-Stock-To   not = spaces and WS-Abrev-From not = spaces)
              display ST304 at line WS-23-Lines col 1 with foreground-color 4 highlight
              display ST006   at line WS-Lines col 01
              accept WS-Reply at line WS-Lines col 32
              go to ZZ050-Get-Disp-03.
*>
     if       WS-Stock-From not = spaces and WS-Stock-To not = spaces
         and  WS-Stock-From > WS-Stock-To
              display ST307 at line WS-23-Lines col 1 with foreground-color 4 highlight
              display ST006   at line WS-Lines col 01
              accept WS-Reply at line WS-Lines col 32
              go to ZZ050-Get-Disp-03.
*>
     if       WS-Abrev-From not = spaces and WS-Abrev-To not = spaces
         and  WS-Abrev-From > WS-Abrev-To
              display ST308 at line WS-23-Lines col 1 with foreground-color 4 highlight
              display ST006   at line WS-Lines col 01
              accept WS-Reply at line WS-Lines col 32
              go to ZZ050-Get-Disp-03.
*>
     if       WS-Stock-From not = spaces or WS-Stock-To not = spaces
           or WS-Abrev-From not = spaces or WS-Abrev-To not = spaces
              move 1    to WS-Partial
     else
              move zero to WS-Partial.
*>
     go       to ZZ050-Exit.
*>
 ZZ050-Get-Disp-04.
*>
*> CAUTION: Stock location can be mixed case
*>
     accept   Display-04 with UPDATE.
     move     Function UPPER-CASE (WS-Location-Frm) to WS-Location-Frm.
     move     Function UPPER-CASE (WS-Location-To)  to WS-Location-To.
     move     Function UPPER-CASE (WS-Double-Sided-Prt) to WS-Double-Sided-Prt.
     if       WS-Double-Sided-Prt = space
       or     (WS-Double-Sided-Prt not = "N" and not = "Y")
              move     "N" to WS-Double-Sided-Prt.   *> JIC
     if       WS-Location-Not-Ignored > 8
              display  ST309 at line WS-22-Lines col 1 with foreground-colour 4
                                                            highlight erase EOS
              display  ST006 at line WS-23-Lines col 1
              accept   WS-Reply at line WS-23-Lines col 32
              go to ZZ050-Get-Disp-04.
*>
     if       WS-Location-Frm (1:4) not = spaces
              perform  varying WS-Location-Frm-Cnt from 10 by -1
                         until WS-Location-Frm-Cnt < 2
                       if      WS-Location-Frm-Cnt < 2   *> JIC
                               exit perform
                       end-if
                       if      WS-Location-Frm (WS-Location-Frm-Cnt:1) = space
                               exit perform cycle
                       end-if
              end-perform.
     if       WS-Location-To (1:4) not = spaces
              perform  varying WS-Location-To-Cnt from 10 by -1
                         until WS-Location-To-Cnt < 2
                       if      WS-Location-To-Cnt < 2   *> JIC
                               exit perform
                       end-if
                       if      WS-Location-To (WS-Location-To-Cnt:1) = space
                               exit perform cycle
                       end-if
              end-perform.
     if       WS-Location-Frm (1:4) = spaces
      and     WS-Location-To  (1:4) = spaces
              move   zero to WS-Partial
     else
      if      WS-Location-Frm-Cnt > 0
       or     WS-Location-To-Cnt > 0
              move   1 to WS-Partial
      else
              move   zero to WS-Partial.
*>
      if      WS-Partial = 1
              display  "Processing Partial Start/End locations" at line WS-22-Lines col 1
                                                                 with foreground-color 4 erase eos
      else
              display  "NOT processing Partial Locations"       at line WS-22-Lines col 1
                                                                 with foreground-color 4 erase eos.
*>
 ZZ050-Exit.
     exit     section.
*>
 ZZ060-Convert-Date        section.
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
              go to ZZ060-Exit.
     move     u-date to WS-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to ZZ060-Exit.
     if       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              go to ZZ060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-date.  *> swap Intl to UK form
     move     u-date (7:4) to WS-Intl-Year.
     move     u-date (4:2) to WS-Intl-Month.
     move     u-date (1:2) to WS-Intl-Days.
*>
 ZZ060-Exit.
     exit     section.
*>
 ZZ070-Convert-Date        section.
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
              go to ZZ070-Exit.
     if       Date-USA                *> swap month and days
              move WS-days to WS-swap
              move WS-month to WS-days
              move WS-swap to WS-month
              go to ZZ070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-date.  *> swap Intl to UK form
     move     to-day (7:4) to WS-Intl-Year.
     move     to-day (4:2) to WS-Intl-Month.
     move     to-day (1:2) to WS-Intl-Days.
*>
 ZZ070-Exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
