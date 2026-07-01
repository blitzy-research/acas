       >>source free
       *>
       *> MORE to do for Input / Amend as fields missing
       *>  IS there ?
       *>
*>****************************************************************
*>                                                               *
*>                BACK  ORDER  PROCESSING                        *
*>                                                               *
*>           BO Reporting and Amendments & Deletions.            *
*>                                                               *
*>     THIS PROGRAM USES ACCEPT_NUMERIC C routine for Qty.       *
*>     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^        *
*>     Above routine remarked out as a pain to build into pl970  *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl970.
*>**
*>    Author.             New program By Vincent B Coen FBCS (Ret), FIDM, FIDPM,
*>                        21/03/2024 - Level 1 completed 28/03/2024
*>                        31/03/2024 - Level 2 completed 31/03/2024.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Back Order reporting and BO amend/deletions.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas011
*>                         stockMT.
*>                        acas012
*>                         salesMT
*>                        accept_numeric in C
*>
*>   CAlled Functions.
*>                        CBL_CHECK_FILE_EXIST.
*>                        INTEGER-OF-DATE.
*>                        SYSTEM.
*>
*>  For testing:          -> Used mainly for DB processing
*>                        fhlogger- File Access logging to Flat file.
*>**
*>    Error messages used.
*>     System Wide:
*>                        SL003
*>                        SL006
*>     Module specific:
*>                        SL194
*>                        SL195
*>                        SL196
*>                        SL201
*>                        SL202
*>                        SL203
*>                        SL204
*>                        SL207
*>                        SL208
*>                        SL209
*>                        SL210
*>                        SL211
*>                        SL212
*>                        SL213.
*>
*>                        SL215.
*>                        SL216.
*>                        SL217.
*>                        SL218.
*>**
*> Changes
*> 21/03/24 vbc - 3.02.00 Creation started today. Reports completed 24/03.
*> 25/03/24 vbc           Started on Amend / Delete mode hopefully.
*>                        Added Coding for ACCEPT_NUMERIC.
*> 28/03/24 vbc           Added code for display of sales cust and stock desc.
*>                        Added (28/03/2024) level 2 for Stock and sales rec
*>                        handling, done.
*>                        added 28th - check that print good then offer to clear
*>                        BO file.
*> 30/03/224 vbc      .01 For Amend record - Only allow for price and quantity
*>                        produce warning if price change occurred on amend.
*>                        Updated L8 & L9 for width and added Invoice type
*>                        Q! is it now correct?
*> 16/04/24 vbc           Copyright notice update superseding all previous notices.
*> 26/04/24 vbc       .02 Forgot to set WS-Printer-Status to "N" before finishing
*>                        in aa020-Menu-Input and 2nd head not printed.
*>                        Chg heads to 108 width.
*> 28/04/24 vbc       .03 Minor code chg for Headings
*> 22/08/24 vbc       .04 Added Time on reports, item serial # for reports and
*>                        for BO data accepts / amends.
*> 16/06/24 vbc       .05 Date/Time reporting < 6 plus space after date.
*> 17/02/25 vbc       .06 Zeroise WS-Page-No at start of each report, JIC it is rerun.
*> 19/02/25 vbc       .07 Adjust file open and file closes in CA000, some missing
*>                        minor cleanup of displays in SS and accepts.
*> 25/02/25 vbc       .08 Fine adjusts for display-03 etc.
*> 29/07/25 vbc       .09 Removed use of accept_numeric - cannot build it without
*>                        issues.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*> 01/03/26 vbc     .01 Replaced TEST-FORMATTED-DATETIME by TEST-DATE-YYYYMMDD
*>                      in ZZ080.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 16-04-2024.
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
 copy "selboitm.cob".
 copy "selprint.cob".
*>
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 copy "fdboitm.cob".
 copy "fdprint.cob".    *> 132 cols
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL970 (3.3.01)".
*>
 copy "print-spool-command.cob".
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "wssl.cob".
 copy "wsstock.cob".
 copy "wsboitm.cob".
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
     03  WS-Stock-Audit-Record  pic x.
*>     03  WS-Stock-Record        pic x.
*>     03  WS-Sales-Record        pic x.
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
 01  WS-data.
     03  Menu-Reply      pic x.
     03  WS-Reply        pic x.
     03  Z               pic 99.
     03  Escape-Code     pic x.
     03  WS-SL-BO-Flag   pic x.
         88  WS-BO-Used                  value "Y".
     03  WS-BO-Can-Be-Used pic x.
         88  WS-BO-Usable                value "Y".
     03  WS-Page-No      pic 9(4)        value zeros.
     03  WS-Line-No      pic 99          value 60.
     03  WS-Cust-No      pic x(7)        value spaces.
     03  WS-Item-No      pic x(13)       value spaces.
     03  WS-Printer-Status
                         pic x           value "N".     *> N = closed,  Y = open.
     03  WS-Ord-Date     pic x(10).                     *> for printing
     03  WS-Est-Date     pic x(10).                     *>   ditto
     03  WS-Data-Mode    pic x           value space.
         88  WS-Mode-Input               value "I".
         88  WS-Mode-Amend               value "A".
         88  WS-Mode-Delete              value "D".
         88  WS-Valid-Modes              values "A" "D" "I".
     03  WS-Sales-Flag   pic x           value "N".
     03  WS-Stock-Flag   pic x           value "N".
     03  WS-Serial-Slash pic x           value "/".   *> added 22/08/24
     03  WS-Disp-Price   pic z(6)9.99    value zero.
*>
*> Above also needs SL-BO-Flag = Y (Sales-BO-Set) for invoice usage.
*>
     03  WS-env-lines    pic 999         value zero.
     03  WS-lines        binary-char unsigned value zero.
     03  WS-accept-body  binary-char unsigned value 8.         *> set for 24 line screen (-1) but Not yet in use
     03  WS-23-lines     binary-char unsigned value zero.
*>
 copy "an-accept.ws".
*>
 01  WS-Temp-Date-YMD.
     03  WS-Temp-Date-YMD9   pic 9(8).
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
 01  hdtime                            value spaces.
     03  hd-hh           pic xx.
     03  hd-mm           pic xx.
     03  hd-ss           pic xx.
     03  hd-uu           pic xx.
*>
 01  WS-Tables.
     03  WS-I-Types      pic x(40)       value "Receipt Invoice Credit  Proforma        ". *> Credit not used here
     03  filler  redefines WS-I-Types.
         05  WS-Inv-Type pic x(8)  occurs 5.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
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
     03  SL194          pic x(19) value "SL194 Stock Read : ".
     03  SL195          pic x(22) value "SL195 Stock Rewrite : ".
     03  SL196          pic x(22) value "SL196 Record Not found".
     03  SL201          pic x(38) value "SL201 Custoner BO (Back Order) Not Set".
     03  SL202          pic x(54) value "SL202 Creating BO rec & Changed Qty to held on invoice".
     03  SL203          pic x(29) value "SL203 Err on Bo-Rec. Write : ".
     03  SL204          pic x(31) value "SL204 Err on Bo-Rec. Rewrite : ".
*>     03  SL205          pic x(41) value "SL205 Using Stock Held for quantity order".
*>     03  SL206          pic x(50) value "SL206 Computation overflow - Qty or cost too large".
     03  SL207          pic x(53) value "SL207 No data file bostkitm - Nothing to do - Exiting".
     03  SL208          pic x(33) value "SL208 Cust/Item not found - Retry".
     03  SL209          pic x(31) value "SL209 Cust/Item Present - Retry".
     03  SL210          pic x(41) value "SL210 Failed to delete record - Status : ".
     03  SL211          pic x(27) value "SL211 Bad Date - Order Date".
     03  SL212          pic x(27) value "SL212 Bad Date - Est.  Date".
     03  SL213          pic x(17) value "SL213 Prints OK ?".
*>     03  SL214          pic x(36) value "SL214 Can I clear down the BO file ?".
     03  SL215          pic x(57) value "Invalid Mode - I = Input, A = Amend, D = Delete or Escape".
     03  SL216          pic x(27) value "SL216 Answer must be N or Y".
     03  SL217          pic x(47) value "SL217 Warning: There has been a price change : ".
     03  SL218          pic x(41) value "SL218 Invoice type must be 1, 2 or 4 Only".
*>
 01  error-code          pic 999.
*>
*> Reporting line sources
*>
 01  Line-1.  *> 110
     03  L1-Name         pic x(34).
     03  filler          pic x(68)       value "Back Order Report by Customer".
     03  filler          pic x(5)        value "Page ".
     03  L1-Page         pic zz9.
*>
 01  Line-2.  *> 110
     03  L2-Name         pic x(34).
     03  filler          pic x(68)       value "Back Order Report by Item".
     03  filler          pic x(5)        value "Page ".
     03  L2-Page         pic zz9.
*>
 01  Line-3.  *> 110
     03  L3-User         pic x(34)       value spaces.
     03  filler          pic x(60)       value spaces.
     03  L3-Date         pic x(10).
     03  filler          pic x           value space.
     03  L3-HH           pic xx.   *> all added 22/08/24
     03  filler          pic x           value ":".
     03  L3-MM           pic xx.
*>
 01  Line-4.  *> By Customers #1
*>                                                                                                       111111111111111111111
*>    000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999000000000011111111112
*>    123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
     03  filler          pic x(113)       value
     " Customer   Item Number      Order       Original      Back Order      Est Arriv        Retail   Arrival Inv.Type".
*>
 01  Line-5.  *> By Customers #2
*>                                                                                                       111111111111111111111
*>    000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999000000000011111111112
*>    123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
     03  filler          pic x(110)       value
     "  Number                                 Invoice       Qty   Date        Date            Price    Flag".
*>     A123456    1234567890123 1234567890     12345678 999,999  ccyy/mm/dd  ccyy/mm/dd  z,zzz,zz9.99     Y    Proforma
*>                                        /zz
 01  Line-6.  *> By Items #1
*>                                                                                                       111111111111111111111
*>    000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999000000000011111111112
*>    123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
     03  filler          pic x(113)       value
     " Item Number    Customer     Order      Original      Back Order      Est Arriv        Retail   Arrival Inv.Type".
*>
 01  Line-7.  *> By Items #2
*>                                                                                                       111111111111111111111
*>    000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999000000000011111111112
*>    123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
     03  filler          pic x(110)       value
     "                 Number                 Invoice       Qty   Date        Date            Price    Flag".
*>     1234567890123  A123456   1234567890  12345678 999,999 ccyy/mm/dd  ccyy/mm/dd  z,zzz,zz9.99      Y    Receipt
*>
*>
 01  Line-8. *> Data by Customer
     03  filler              pic x.
     03  L8-Cust             pic x(7).
     03  filler              pic x(4).
     03  L8-Item-No          pic x(13).      *> 25
     03  L8-Slash            pic x.          *> 26 added 22/08/24
     03  L8-Serial-No        pic 99b   Blank when zero.  *> 29 added 22/08/24 = +3 to the line
     03  L8-PO               pic x(10)b.      *> 40
     03  L8-Orig-Inv         pic x(8)b.       *> 49
     03  L8-Qty              pic zzz,zz9bb.   *> 58
     03  L8-Ord-Date         pic x(10)bb.     *> 70   Multi format
     03  L8-Arr-Date         pic x(10)b.      *> 81   Multi format
     03  L8-Price            pic z,zzz,zz9.99. *> 93
     03  filler              pic x(6).        *> 99
     03  L8-Flag             pic xbbbb.       *> 104
     03  L8-Inv-Type         pic x(8).        *> 112
*>
 01  Line-9. *> Data by Items
     03  filler              pic x.
     03  L9-Item-No          pic x(13).     *> 14
     03  L9-Slash            pic x.         *> 15
     03  L9-Serial-No        pic 99b  Blank when zero.       *> 18
     03  L9-Cust             pic x(7).        *> 25
     03  filler              pic xx.          *> 27
     03  L9-PO               pic x(10)bbb.    *> 40
     03  L9-Orig-Inv         pic x(8)b.       *> 49
     03  L9-Qty              pic zzz,zz9bb.   *> 58
     03  L9-Ord-Date         pic x(10)bb.     *> 70   Multi format
     03  L9-Arr-Date         pic x(10)b.     *> 81   Multi format
     03  L9-Price            pic z,zzz,zz9.99. *> 93
     03  filler              pic x(6).        *> 99
     03  L9-Flag             pic xbbbb.       *> 105  Y or N
     03  L9-Inv-Type         pic x(8).        *> 112
*>
 01  COB-CRT-Status          pic 9(4)         value zero.
 copy "screenio.cpy".
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  To-Day              pic x(10).
*>
 screen section.
*>*************
*>
 01  Display-02                  background-color cob-color-black
                                 foreground-color cob-color-green
                                                     blank line. *>  was screen.
*>
     03  value " Mode - ["                   line 4 col 1.
     03  using WS-Data-Mode   pic x                 col 10 foreground-color 3.
     03  value "] I = Input, A = Amend, D = Delete or Escape to quit"        col 11.
*>
*>              000000000111111111122222222223333333333444444444455555555556666666666777777777788888888889999999999
*>              123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
     03  value "Cust.   Item Number  (S#)   Order   ------ BO ------    Price    Arr Inv." line 5 col  1.
     03  value "Number                                Qty  Date                  Flg Type" line 6 col  1.
*>
 01  Display-03                                      Blank Line.
     03  using WS-BO-Stk-Cust-No  pic x(7)   line 8 col  1.
     03  using WS-BO-Stk-Item-No  pic x(13)         col  9.
     03  value ":"                pic x             col 22. *> added this & next for serial # but blank if not used
     03  using WS-BO-Serial       pic 99            col 23.
     03  using WS-BO-Stk-PO       pic x(10)         col 26.
     03  using WS-BO-Stk-BO-Qty   pic 9(6)          col 37.
     03  using WS-Ord-Date        pic x(10)         col 44.       *> From WS area
     03  using WS-BO-Stk-Price    pic z(6)9.99      col 55.
     03  using WS-BO-Stk-Arrived-Flag pic x         col 67.
     03  using WS-BO-Stk-Inv-Type pic 9             col 71.       *> 1=Receipt, 2=Invoice, 4=Proforma
     03  value "="                pic x             col 72.
     03  using WS-Inv-Type (WS-BO-Stk-Inv-Type)     col 73  pic x(8).
*>
 01  Display-04-Cust-Stock.
     03  value "Customer - {"                 line 10 col  1     Blank Line.
     03  using Sales-Name         pic x(30)           col 13.
     03  value "}"                                    col 43.
     03  value "Stock Desc - {"               line 11 col  1     Blank Line.
     03  using WS-Stock-Desc      pic x(32)           col 15.
     03  value "}"                                    col 47.
*>
*> ABOVE WILL NEED CHANGES AND CLEAR OUT COMMENT RULERS AFTER TESTING
*>
*>
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 aa000 section.
*>************
*>
 aa000-Main.
     accept   WS-env-lines from lines.
     if       WS-env-lines < 24
              move  24 to WS-env-lines WS-lines
     else
              move  WS-env-lines   to WS-lines
     end-if
     subtract 1 from WS-lines giving WS-23-lines.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     accept   HDTime from TIME.
     if       HDTime not = "00000000"
              move hd-hh to L3-HH
              move hd-mm to L3-MM.
*>
*>  Have we a BO file ? if not display msgs and quit
*>
     display  space at 0101 with erase eos.
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-31    *> bostkitm file
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                or  File-Size-Bytes = zero          *> No data if exists
                    display  SL207    at 1210 with foreground-color 4 highlight
                    display  SL006    at 1410 with foreground-color 4 beep
                    accept   WS-Reply at 1455 with foreground-color 3
                    goback
              end-if
     end-if.
*>
*> Fill header info
*>
     move     Prog-Name to L1-Name
                           L2-Name.
     move     Usera  to  L3-User.
     perform  zz070-Convert-Date.   *> WS-date now LOCAL display date
     move     WS-Date to L3-Date.
     move     Print-Spool-Name to PSN.
*>
*> Next 5 for ACCEPT_NUMERIC processing
*>
     move     zeros to AN-Error-Code
                       AN-Return-Code.
     SET      AN-FG-IS-GREEN  TO TRUE.
     SET      AN-BG-IS-BLACK  TO TRUE.
     SET      AN-FG2-IS-CYAN  TO TRUE.
*>
     SET      AN-MODE-IS-UPDATE   TO TRUE.  *> could be AN-MODE-IS-NO-UPDATE
*>
 aa010-Menu.
     move     zero  to  Menu-Reply.
     display  Prog-Name at 0101 with erase eos foreground-color 2.
     display  "BO Reporting and Amendments Menu" at 0134 with foreground-color 2.
     display  ws-date at 0171 with foreground-color 2.
*>
 aa010-Sub-Menu.
     display  "Select one of the following by number :- [ ]"  at 0501 with foreground-color 2 erase eos.
     display  "(1)  Report All Back Orders by Customer And by Item "  at 0711 with foreground-color 2.
     display  "(2)  Report BO by Customers"      at 0811 with foreground-color 2.
     display  "(3)  Report BO by Stock Items"    at 0911 with foreground-color 2.
     display  "(4)  Amend or Delete Back Orders" at 1011 with foreground-color 2.
     display  "(X)  Return To System menu"       at 1211 with foreground-color 2.
*>
 aa020-Menu-Input.
     move     1 to Menu-Reply.
     accept   Menu-Reply at 0543 with foreground-color 6 auto UPPER.
*>
     if       Menu-Reply  = "X"
              if       WS-Printer-Status = "Y"
                       move "N" to WS-Printer-Status
                       close Print-File
              end-if
              call     "SYSTEM" using Print-Report  *> Landscape
              go to aa000-Menu-Exit.
*>
     if       Menu-Reply = 1 or = 2 or = 3
              perform  ba000-Reports
              go to aa020-Menu-Input.
*>
     if       Menu-Reply = 4
              perform  CA000-Amend.
     go       to       aa010-Sub-Menu.
*>
 AA000-Menu-Exit.
     goback.
*>
 ba000-Reports section.
*>********************
*>
 ba010-Main.
     if       WS-Printer-Status = "N"
              open     output Print-File
              move     "Y" to WS-Printer-Status.
*>
     if       Menu-Reply = 1     *> Cust & Item reports
              perform  ba020-Cust-Report thru ba020-Exit
              perform  ba030-Item-Report thru ba030-Exit
              go to    ba999-Exit.
*>
     if       Menu-Reply =  2
              perform  ba020-Cust-Report thru ba020-Exit
              go to    ba999-Exit.
*>
     perform  ba030-Item-Report thru ba030-Exit.
     go to    ba999-Exit.
*>
 ba020-Cust-Report.
     open     input    BO-Stk-Itm-File.
     if       FS-Reply not = zero
              display  "BO Open Failure = " at line ws-23-lines col 1 with erase eos
              display  FS-Reply at line ws-23-lines col 19
              display  SL006    at line ws-Lines col 1
              accept   WS-Reply at line ws-lines col 45
              close    BO-Stk-Itm-File
              go to    ba020-Exit.
     move     60       to WS-Line-No.
     move     zero     to WS-Page-No.
     start    BO-Stk-Itm-File FIRST.
     perform  until exit
              read     BO-Stk-Itm-File next at end
                       close   BO-Stk-Itm-File
                       exit perform
              end-read
              if       FS-Reply not = zero
                       close   BO-Stk-Itm-File
                       exit perform
              end-if
              perform  ba110-Move-Cust
              exit     perform cycle
     end-perform.
*>
 ba020-Exit.
     exit.
*>
 ba030-Item-Report.
     open     input    BO-Stk-Itm-File.
     if       FS-Reply not = zero
              display  "BO Open Failure = " at line ws-23-lines col 1 with erase eos
              display  FS-Reply at line ws-23-lines col 19
              display  SL006    at line ws-Lines col 1
              accept   WS-Reply at line ws-lines col 45
              close    BO-Stk-Itm-File
              go to    ba030-Exit.
     move     60       to WS-Line-No.
     move     zero     to WS-Page-No.
     start    BO-Stk-Itm-File FIRST.   *>  key BO-Stk-Item-No.
     perform  until exit
              read     BO-Stk-Itm-File next at end
                       close   BO-Stk-Itm-File
                       exit perform
              end-read
              if       FS-Reply not = zero
                       close   BO-Stk-Itm-File
                       exit perform
              end-if
              perform  ba120-Move-Item
              exit     perform cycle
     end-perform.
*>
 ba030-Exit.
     exit.
*>
 ba999-Exit.
     exit     section.
*>
 bb100-Cust-Heads  section.
*>************************
*>
     if       WS-Line-No not > Page-Lines
              go to bb100-Exit.
     add      1 to WS-Page-No.
     move     WS-Page-No to L1-Page.
     if       WS-Page-No = 1
              write    Print-Record from Line-1 before 1
              write    Print-Record from Line-3 before 1
              write    Print-Record from Line-4 after 1
              write    Print-Record from Line-5 after 1
     else
              write    Print-Record from Line-1 after page
              write    Print-Record from Line-3 after 1
              write    Print-Record from Line-4 after 2
              write    Print-Record from Line-5 after 1
     end-if
     move     spaces to Print-Record.
     write    Print-Record after 1.
     move     6 to WS-Line-No.
*>
 bb100-Exit.  exit  section.
*>
 bc100-Item-Heads  section.
*>************************
*>
     if       WS-Line-No not > Page-Lines
              go to bc100-Exit.
     add      1 to WS-Page-No.
     move     WS-Page-No to L2-Page.
     if       WS-Page-No = 1
              write    Print-Record from Line-2 before 1
              write    Print-Record from Line-3 before 1
              write    Print-Record from Line-6 after 1
              write    Print-Record from Line-7 after 1
     else
              write    Print-Record from Line-2 after page
              write    Print-Record from Line-3 after 1
              write    Print-Record from Line-6 after 2
              write    Print-Record from Line-7 after 1
     end-if
     move     spaces to Print-Record.
     write    Print-Record after 1.
     move     6 to WS-Line-No.
*>
 bc100-Exit.  exit  section.
*>
 ba110-Move-Cust    section.
*>*************************
*>
     perform  bb100-Cust-Heads.
     move     spaces              to Line-8.
     move     BO-Stk-Cust-No      to L8-Cust.
     move     BO-Stk-Item-No      to L8-Item-No.
     if       BO-Serial not = zero
              move     ":"        to L8-Slash
              move     BO-Serial  to L8-Serial-No
     else
              move     space      to L8-Slash.
*>
     move     BO-Stk-PO           to L8-PO.
     move     BO-Stk-Orig-Inv-No  to L8-Orig-Inv.
     move     BO-Stk-BO-Qty       to L8-Qty.
*>
     move     BO-Stk-BO-Arr-Date  to U-Bin
     perform  zz060-Convert-Date
     move     WS-Date             to L8-Arr-Date.
     move     BO-Stk-Order-Date   to U-Bin
     perform  zz060-Convert-Date
     move     WS-Date             to L8-Ord-Date.
*>
     move     BO-Stk-Price        to L8-Price.
     move     BO-Stk-Arrived-Flag to L8-Flag.
     if       BO-Stk-Inv-Type not < 1 and not > 4
              move     WS-Inv-Type (BO-Stk-Inv-Type) to L8-Inv-Type
     else
              move     "UNKNOWN" to L8-Inv-Type.
*>
     if       WS-Cust-No not = BO-Stk-Cust-No
              move     BO-Stk-Cust-No to WS-Cust-No
              write    Print-Record from Line-8 after 2
              add      2 to WS-Line-No
     else
              write    Print-Record from Line-8 after 1
              add      2 to WS-Line-No
     end-if.
*>
 ba110-Exit.
     exit     section.
*>
 ba120-Move-Item    section.
*>*************************
*>
     perform  bc100-Item-Heads.
     move     spaces              to Line-9.
     move     BO-Stk-Cust-No      to L9-Cust.
     move     BO-Stk-Item-No      to L9-Item-No.
     if       BO-Serial not = zero
              move     ":"        to L9-Slash
              move     BO-Serial  to L9-Serial-No
     else
              move space          to L9-Slash.
*>
     move     BO-Stk-PO           to L9-PO.
     move     BO-Stk-Orig-Inv-No  to L9-Orig-Inv.
     move     BO-Stk-BO-Qty       to L9-Qty.
*>
     move     BO-Stk-BO-Arr-Date  to U-Bin
     perform  zz060-Convert-Date
     move     WS-Date             to L9-Arr-Date.
     move     BO-Stk-Order-Date   to U-Bin
     perform  zz060-Convert-Date
     move     WS-Date             to L9-Ord-Date.
*>
     move     BO-Stk-Price        to L9-Price.
     move     BO-Stk-Arrived-Flag to L9-Flag.
     if       BO-Stk-Inv-Type not < 1 and not > 4
              move     WS-Inv-Type (BO-Stk-Inv-Type) to L9-Inv-Type
     else
              move     "UNKNOWN" to L9-Inv-Type.
*>
     if       WS-Item-No not = BO-Stk-Item-No
              move     BO-Stk-Item-No to WS-Item-No
              write    Print-Record from Line-9 after 2
              add      2 to WS-Line-No
     else
              write    Print-Record from Line-9 after 1
              add      2 to WS-Line-No
     end-if.
*>
 ba120-Exit.
     exit     section.
*>
 CA000-Amend     section.
*>**********************
*>
*> Used for Input and Amend modes
*>
 CA010-Main.
     open     i-o      BO-Stk-Itm-File.
     perform  Stock-Open-Input.
     if       FS-Reply not = zero
              move   "N" to WS-Stock-Flag
     else
              move   "Y" to WS-Stock-Flag.
     perform  Sales-Open-Input.
     if       FS-Reply not = zero
              move   "N" to WS-Sales-Flag
     else
              move   "Y" to WS-Sales-Flag.
*>
     display   " " at 0401 with erase eos.
     display   Display-02.
*>
 CA020-Get-Mode.
     move     space to WS-Data-Mode.
     display  " " at 1201 with erase eol.  *> Clear Deletes DONE msg if there.
     accept   Display-02.
     move     FUNCTION UPPER-CASE (WS-Data-Mode) to WS-Data-Mode.
     if       not WS-Valid-Modes and
              Cob-Crt-Status not = Cob-Scr-Esc
              display  SL215 at line WS-Lines col 1 with foreground-color 4  *> Invalid mode
              go to CA020-get-Mode.
*>
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to ca998-Exit.            *> close open files then exit
     display  WS-Data-Mode at line 4 col 10.
     display  " " at 0412 with erase eol.
     display  " " at line WS-Lines col 1 with erase eol.
*>
 CA030-Get-Key.
     display  spaces at line 8 col 1 with erase eol.
     initialise
              WS-BO-Stk-Itm-Record with filler.         *> BO WS record.
     accept   WS-BO-Stk-Cust-No at 0801 with foreground-color 3 UPPER.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to ca998-Exit.
*>
     accept   WS-BO-Stk-Item-No at 0809 with foreground-color 3 UPPER.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to ca998-Exit.
     display  " " at 0412 with erase eol.
     display  " " at line WS-Lines col 1 erase eol.
*>
     move     WS-BO-Cust-Itm-No to BO-Cust-Itm-No.
     move     zeros to FS-Reply.
     read     BO-Stk-Itm-File  KEY
                               BO-Cust-Itm-No.
     move     BO-Stk-Itm-Record to WS-BO-Stk-Itm-Record.
*>
*> If valid rec is in both areas otherwise on in WS-BO etc.
*>
     if       (WS-Mode-Amend or
              WS-Mode-Delete) and
              FS-Reply not = zeroes
              display  SL208 at line WS-Lines col 10 with foreground-color 4
                                                          highlight beep
              display  FS-Reply at line WS-Lines col 45 with foreground-color 3
              go to CA030-Get-Key.
*>
     if       WS-Mode-Input and
              FS-Reply = zeroes
              display  SL209 at line WS-Lines col 10 with foreground-color 4
                                                          highlight beep
              go to CA030-Get-Key.
     display  " " at line WS-Lines col 10 erase eol.
*>
*> Get and display the itm desc and cust name
*>
     move     1 to File-Key-No.
     move     WS-BO-Stk-Item-No to WS-Stock-Key.
     if       WS-Stock-Flag = "Y"
              perform  Stock-Read-Indexed
              if       fs-Reply = 23 or = 21
                       move  "Not Found " to WS-Stock-Desc.
*>
     move     WS-BO-Stk-Cust-No  to  WS-Sales-Key.
     if       WS-Sales-Flag = "Y"
              perform  Sales-Read-Indexed.
              if       FS-Reply = 21 or = 23
                       move  "Not Found " to Sales-Name.
*>
     display  Display-04-Cust-Stock.
*>
 CA040-Get-Confirm-Delete.
     if       WS-Mode-Delete
              move    "N" to WS-Reply
              display "Confirm Delete (Y/N) - [ ]" at 1201 with foreground-color 2
                                                                erase eol
              accept  WS-Reply at 1225 with foreground-color 3 update UPPER
              if      WS-Reply not = "Y" and not = "N"
                      display SL216 at 1230 with foreground-color 4 highlight beep  *> Y OR N !
                      go to CA040-Get-Confirm-Delete
              end-if
              if      WS-Reply = "Y"
                      move    WS-BO-Cust-Itm-No to BO-Cust-Itm-No
                      delete  BO-Stk-Itm-File Record
                      if      FS-Reply not = zero
                              display  SL210 at 1201 with foreground-color 4
                                                          erase eol highlight beep
                              display FS-Reply at 1242
                              display SL003    at 1245
                              accept  WS-Reply at 1275
                      end-if
              end-if
              go to CA020-Get-Mode.
*>
*> Must be WS-Mode-Amend or WS-Mode-Input
*>
     if       WS-Mode-Input
              if       Date-UK
                       move     "dd/mm/ccyy" to WS-Ord-Date *> all in WS area
              else
               if      Date-USA
                       move     "mm/dd/ccyy" to WS-Ord-Date
               else
                       move     "ccyy/mm/dd" to WS-Ord-Date
               end-if
              end-if
              move     5 to WS-BO-Stk-Inv-Type        *> For display-03 for spaces
     else    *> Using temp dates in local format converting from binary since 1601
              move     WS-BO-Stk-BO-Arr-Date to U-Bin
              perform  zz060-Convert-Date
              move     WS-Date to WS-Est-Date             *> Not used for displays here
              move     WS-BO-Stk-Order-Date to U-Bin
              perform  zz060-Convert-Date
              move     WS-Date to WS-Ord-Date             *> In WS area Only
     end-if.  *>  Now local date format
     display  Display-03.
     if       WS-Mode-Input
              accept   WS-BO-Stk-PO       at 0826 with foreground-color 3 Update
              accept   WS-BO-Stk-BO-Qty   at 0837 with foreground-color 3 Update. *> could use accept_numeric routine
*>
 CA050-Get-Ord-Date.
     display  WS-Ord-Date at 0844 with foreground-color 3.
     if       WS-Mode-Input
              accept   WS-Ord-Date  at 0844 with foreground-color 3 Update  *> using  WS temp field
              if       WS-Ord-Date (1:2) not = zeros and   *> test date for valid range
                                         not = spaces and
                                         not = "dd"   and
                                         not = "mm"   and
                                         not = "cc"
                       move     WS-Ord-Date to WS-Test-Date
                       perform  zz080-Convert-Local-To-Bin-Date
                       if       Return-Code not = zeros
                                display  SL211 at line ws-lines col 1 with foreground-color 4 highlight
                                                                           erase eol
                                go to CA050-Get-Ord-Date
                       else
                                display " " at line WS-Lines col 1 erase eol
                       end-if.
              move     FUNCTION INTEGER-OF-DATE (WS-Temp-Date-YMD9) to WS-BO-Stk-Order-Date.
*>
 CA060-Get-Est-Date.
     move     Stock-Retail to WS-BO-Stk-Price.  *> Preload the price for input
*>
     if       WS-Mode-Amend and
              WS-BO-Stk-Price not = Stock-Retail
              display  " " at 0855 with erase eol
              move     Stock-Retail to WS-Disp-Price
              display  SL217   at 1310 with foreground-color 4 highlight beep
              display  WS-Disp-Price at 1357 with foreground-color 4
              display  "Stock Price" at 1369 with foreground-color 2
     else
              display " " at 1310 erase eol.
*>
 CA070-Get-Inv-Type.
     display  " " at 0855 with erase eol.
     accept   WS-BO-Stk-Inv-Type  at 0872 with foreground-color 3 update.
     if       WS-BO-Stk-Inv-Type not = 1 and not = 2 and not = 4
              display  SL218  at line WS-23-Lines col 1 with foreground-color 4
                                                             highlight beep
              go to CA070-Get-Inv-Type
     else
              display " " at 1310 erase eol.
*>
 CA080-Price.
     if       WS-Mode-Input OR
              (WS-Mode-Amend AND
              WS-BO-Stk-Inv-Type = 2 or = 4)  *> Amend/Onput, invoice or proforma only, otherwise price is fixed
 *>             MOVE     8   TO AN-LINE   *> as cust. has prepaid or pre-ordered against price
 *>             MOVE     55  TO AN-COLUMN
*>              set      AN-MODE-IS-UPDATE TO TRUE
 *>             call     static "ACCEPT_NUMERIC" using by REFERENCE WS-BO-Stk-Price    *> HAD STATIC
 *>                                                    by REFERENCE AN-ACCEPT-NUMERIC
 *>             perform  AN-Test-Status.
              accept   WS-Disp-Price at 0855 foreground-color 3 UPDATE
              move     WS-Disp-Price to WS-BO-Stk-Price
     end-if
*>
     if       WS-Mode-Input
              write    BO-Stk-Itm-Record from WS-BO-Stk-Itm-Record
              if       FS-Reply NOT = zero     *> Should not happen but ...
                       display  SL203 at line WS-23-Lines col 1 with foreground-color 4
                                                                 highlight beep erase eos
                       display  FS-Reply at line WS-23-Lines col 30 with foreground-color 3
                                                                 highlight beep
                       display  SL006  at line WS-Lines col 1
                       accept   WS-Reply at line WS-Lines col 45
                       display " " at line WS-Lines col 1 with erase eol
              end-if
              go to CA020-Get-Mode.
*>
     rewrite  BO-Stk-Itm-Record from WS-BO-Stk-Itm-Record.
     if       FS-Reply NOT = zero     *> Should not happen but ...
              display  SL204 at line WS-23-Lines col 1 with foreground-color 4
                                                        highlight beep erase eos
              display  FS-Reply at line WS-23-Lines col 32 with foreground-color 3
                                                        highlight beep
              display  SL006  at line WS-Lines col 1
              accept   WS-Reply at line WS-Lines col 45
*> OK try it, but should not work
              write    BO-Stk-Itm-Record from WS-BO-Stk-Itm-Record.
     go       to  CA020-Get-Mode.
*>
 ca998-Exit.
     if       WS-Sales-Flag = "Y"
              perform  Sales-Close.
     if       WS-Stock-Flag = "Y"
              perform  Stock-Close.
     close    BO-Stk-Itm-File.

 ca999-Exit.
     exit     section.
*>
 zz060-Convert-Date    section.
*>****************************
*>
*>  Converts date in binary to UK/USA/Intl date format
*>****************************************************
*> Input:   u-bin
*> output:  WS-date as uk/US/Inlt date format
*>          u-date & WS-Date = spaces if invalid date
*>
     perform  maps04.  *> date now dd.mm.yyyy
     if       u-date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     u-date to WS-date.   *> UK date
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move WS-days  to WS-swap
              move WS-month to WS-days
              move WS-swap  to WS-month
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
 zz070-Convert-Date    section.
*>****************************
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
              move WS-days  to WS-swap
              move WS-month to WS-days
              move WS-swap  to WS-month
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
 zz080-Convert-Local-To-Bin-Date  section.
*>***************************************
*>
*> Input:  WS-Test-Date =  Local date
*> Output: U-Bin  days since 1601
*>
     move     WS-Test-Date to WS-Date.
     if       Date-USA                *> swap month and days
              move WS-Year      to WS-Temp-Date-YMD (1:4)
              move WS-USA-Month to WS-Temp-Date-YMD (5:2)
              move WS-USA-Days  to WS-Temp-Date-YMD (7:2)
              go to zz080-Conv-Common-Date.
     if       Date-UK
              move WS-Year      to WS-Temp-Date-YMD (1:4)
              move WS-Month     to WS-Temp-Date-YMD (5:2)
              move WS-Days      to WS-Temp-Date-YMD (7:2)
              go to zz080-Conv-Common-Date.
*>
*> Must be intl
*>
     move     WS-Intl-Year  to WS-Temp-Date-YMD (1:4).
     move     WS-Intl-Month to WS-Temp-Date-YMD (5:2).
     move     WS-Intl-Days  to WS-Temp-Date-YMD (7:2).
*>
 zz080-Conv-Common-Date.
*>
*> Date now yyyymmdd
*> function was TEST-FORMATTED-DATETIME
*>
     move     FUNCTION TEST-DATE-YYYYMMDD (WS-Temp-Date-YMD9) to Return-Code.
     if       Return-Code not = zero
              go to zz080-Exit.
     move     FUNCTION INTEGER-OF-DATE (WS-Temp-Date-YMD9) to U-Bin.
     move     zero to Return-Code.
*>
 zz080-Exit.  exit section.
*>
 maps04             section.
*>*************************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
 copy "an-accept.pl".
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
