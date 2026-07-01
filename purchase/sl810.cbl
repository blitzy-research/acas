       >>source free
*>
*>===================================================
*>  THIS PROGRAM IS NEW AND REQUIRES A FULL TEST !!!
*>
*>  THERE IS TEST CODE IN THIS PROGRAM - REMOVE AFTER <<<<<<<<<  IS THERE ?
*>
*>   For Purchase - sl810 - 830 needs to be converted for puchase and
*>   program names changed to pl810 - 830.
*>   AS the need for PL appears not to be wanted by users as no one has
*>   asked for them development has Stopped / Paused.
*>
*>***************************************************
*>                                                  *
*>  AUTOGEN ENTRY / AMEND from invoice Data         *
*>            Entry sl910 and heavily changed       *
*>                                                  *
*>***************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl810.
*>**
*>    Author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM,
*>                        Started code changes 15/05/2023
*>                        As can't find original code for AutoGen.
*>                        For Applewood Computers.
*>                        sl810 Autogen coded from sl910 15/04/2023 but heavily changed
*>                              and using same copyright.
*>**
*>    Security.           Copyright (C) 1976-2025 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            AutoGen Invoice Data Entry & Maintenance.
*>                        This program only produces Dummy Invoices for AutoGen.
*>                        No receipts, C.Notes, proformas etc.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas011  ->       (Stock)   XXXX
*>                         stockMT.
*>                        acas012  ->       (Sales)
*>                         salesMT.
*>                        acas014  ->       (Delivery)
*>                         deliveryMT.
*>                        acas015  ->       (Analysis) used for reading line items Anal codes
*>                         analMT.           for validation.
*>                        acas004  ->       (slautogen)
*>                         slautogenMT.
*>
*>                        SL070. Analysis codes set up - Defaults only.
*>                        Sl960. New customer create
*>**
*>    Function used keys:
*>                        F1  - Enter New customer process.
*>                        F2  - Stock - Read in order Next Stock Record.
*>                        F3  - Stock - Read specific Stock Record using Abbreviated key.
*>                        F5  - Stock - Read next by Description.
*>                        F6  - Stock - skip current order.
*>                        F8  - Use delivery address.
*>                  Data entry mode :
*>                        F2 - Mode Input.Heading 3
*>                        F3 - Mode Update.
*>                        F4 - Mode Delete.
*>**
*>    Error messages used.
*>     System Wide:
*>                        SL003
*>                        SL006
*>     Module specific:
*>                        SL180
*>                        SL186
*>                        SL187
*>                        SL192. *> P.A file does not exist
*>                        SL194.   Stock Read :         {error}
*>                        SL196.   Not on File
*>                        SL197.
*>****
*>  Changes.
*>
*> 15/05/23 vbc - .31 For sl810 autogen code create/build.
*>                .00 Removed the old changelog notes from sl910.
*> 19/05/23 vbc - .01 Add code to use SL-Next-Rec for invoice # in autogen
*>                    file rec
*> 08/06/23 vbc - .02 Escape to Abort and Return to Continue, wrong location.
*>                .03 On entry if input aborted forgot to subtract from SL-Next-Rec.
*> 28/07/23 vbc - .04 In Delete-Current-Record check for RDB & perform instead
*>                    SLautogen-delete-all.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 03/09/25 vbc       Started work on changes for purchase.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>****** NOTES ************
*>
*>>>>>>>>> ??? >>     For kbrd keys F2, 3, 5, 6  & 8 during stock data entry
*>                    For kbrd keys F9, F10 & F11 Program data mode
*>                                    - F9 - Entry, F10 - Update and F11 - Delete.
*>                    In Bypass-Product-Space-Tests at  Search on Desc
*>                    there are three code lines to display and accept
*>
*>                    a return on line 24 used for TESTING ONLY.
*>  >>->>>>           SO -> REMOVE AFTER TESTING <-  VINCENT!!!!
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
*> System and is Copyright (c) Vincent B Coen. 1980-2025 and later.
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
 data                    division.
*>===============================
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "PL810 (3.3.00)".
 77  Exception-Msg       pic x(25) value spaces.
*>
*> Data file Records here
*>
 copy "slwsinv.cob"  replacing Invoice-Line by Invoice-Lines. *> Dup name Holds sih (header) & sil (lines)
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                                pic x(137).
 copy "wsanal.cob".
 copy "wsdel.cob".
 copy "wssl.cob".
 copy "wsstock.cob".
*>
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
*> REMARK OUT, ANY IN USE
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
*>     03  WS-Stock-Record        pic x.
*>     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
*>     03  WS-Delivery-Record     pic x.  *> not needed
*>     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.  *> ditto
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
*>     03  WS-Invoice-Record      pic x.  *> Used for SLautogen rec
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  WS-data.
     03  test-product.
         05  filler      pic x.
             88  sil-comment             value "/".
         05  filler      pic x(12).
     03  Menu-Reply      pic 9.
     03  WS-reply        pic x.
     03  z               pic 99.
     03  c-check         pic 9.
         88  c-exists                    value  1.
     03  Address-A       pic x(96).
     03  address-line.
         05 add-line1    pic x(15).
         05 add-line2    pic x(21).
     03  WS-named        pic x           value space.
     03  WS-dash         pic x(80)       value all "-".
     03  work-1          pic 9(7)v99.
     03  work-n          pic 9(7)v99.
     03  work-d          pic 9(7)v99.
     03  display-8       pic z(5)9.99.
     03  display-9       pic z(6)9.99.
     03  Vat-Code-X.                           *> this for S, R, Z = Std,Reduced,Zero
         05  Vat-Code    pic 9.                *> 18/01/17
     03  i               pic 99.
     03  j               pic 99.
     03  k               pic 99.
     03  m               pic 99.
     03  Escape-Code     pic x.
     03  new-screen      pic 9(8).
*>
     03  WS-Entry-Mode   pic A                value space.
         88  WS-Valid-Modes                   values "E" "U" "D".
         88  Entry-Mode                       value "E".
         88  Amend-Mode                       value "U".
         88  Update-Mode                      value "U".
         88  Delete-Mode                      value "D".
*>
     03  WS-Next-Inv     pic 9(8)             value zero.
     03  WS-Service-Only pic x                value space.  *> Set to Y if only service line items present for invoice
     03  altypes         pic x(15)            value "Account <<<".
     03  filler redefines altypes.
         05 d-types      pic x(15).    *>  occurs 1.
     03  WS-vat-rate     pic 99v99.
     03  WS-pa           pic xx.
     03  WS-product      pic x(13).
     03  WS-Temp-Stock-Key                    value spaces.
         05  WS-Abrev-Stock   pic x(7).
         05  WS-Stock-No-Long pic x(6).
     03  WS-description  pic x(32).
     03  WS-qty          pic 9(5).
     03  WS-Net          pic 9(7)v99.
     03  WS-vat          pic 9(7)v99.
     03  WS-unit         pic 9(7)v99.
     03  WS-cr           pic 9(8).
     03  WS-dayes        pic 99.
     03  WS-Inv-Month.
         05  WS-Inv-Mth  pic 99.
     03  WS-Show-Delivery pic X.
*>
     03  WS-env-lines    pic 999         value zero.
     03  WS-lines        binary-char unsigned value zero.
     03  WS-Accept-body  binary-char unsigned value 8.         *> set for 24 line screen (-1) but Not yet in use
     03  WS-23-Lines     binary-char unsigned value zero.
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
*>
*> the following for GC and screen
*>
 01  wScreenName             pic x(256).
 01  wInt                    binary-long.
*>
 01  WS-Test-Date            pic x(10).
 01  WS-date-formats.
     03  WS-swap             pic xx.
     03  WS-Conv-Date        pic x(10).
     03  WS-date             pic x(10).
     03  WS-UK redefines WS-date.
         05  WS-days         pic xx.
         05  filler          pic x.
         05  WS-Month        pic xx.
         05  filler          pic x.
         05  WS-year         pic x(4).
     03  WS-USA redefines WS-date.
         05  WS-usa-Month    pic xx.
         05  filler          pic x.
         05  WS-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  WS-Intl redefines WS-date.
         05  WS-intl-year    pic x(4).
         05  filler          pic x.
         05  WS-intl-Month   pic xx.
         05  filler          pic x.
         05  WS-intl-days    pic xx.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  File-Info                          value zero.
     05 File-Size-Bytes  pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp.
     05 Mod-Mo           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp.
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp. *> Always 00
*>
 01  Error-Messages.  *> MAKE SURE THESE msgs ARE IN THE BUILDING and SALES manuals <<<<<<<<<<<<<<<<<<<<<<<<<<<<
*> System Wide
     03  CLR16          pic x(16) value spaces.
     03  CLR22          pic x(22) value spaces.
     03  CLR40          pic x(40) value spaces.
*>
     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
     03  SL006          pic x(43) value "SL006 Note Details & Hit Return to continue".
*> Module specific
     03  SL180          pic x(34) value "SL180 Err on Autogen Rec. write : ".
     03  SL186          pic x(30) value "SL186 P.A. Code Does Not Exist".
     03  SL187          pic x(38) value "SL187 Autogen Record not found on file".
     03  SL192          pic x(30) value "SL192 P.A. File Does Not Exist".
     03  SL194          pic x(19) value "SL194 Stock Read : ".
     03  SL196          pic x(22) value "SL196 Record Not found".
     03  SL197          pic x(30) value "SL197 Invalid mode - try again".
*>
 01  error-code          pic 999.
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
     accept   WS-env-lines from lines.
     if       WS-env-lines < 24
              move  24 to WS-env-lines WS-lines
     else
              move  WS-env-lines   to WS-lines.
     subtract 1 from WS-lines giving WS-23-Lines.
     subtract 15 from WS-23-Lines giving WS-Accept-Body.	*> gives no. of invoice item lines
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
 *>     perform  zz070-Convert-Date.   *> WS-date now local disp date
     move     1 to File-Key-No.
*>
*>  Set up delete file for screen save/restore.   ????????
*>
 *>    move     spaces to Path-Work.
 *>    string   ACAS-Path       delimited by space
 *>             "sl-temp.scr"   delimited by size
 *>                                into Path-Work.
*>
*>  Here is the code for it when ready to cut/paste in.
*>
*>
*> Experimental code here
*>
 *>    if       Cob-Crt-Status = Cob-Scr-F3
 *>             move     z"sl-temp.scr"  to wScreenName
 *>             call     "scr_dump"    using wScreenName returning wInt
 *>             perform  abc
 *>             call     "scr_restore" using wScreenName returning wInt
 *>             call     "CBL_DELETE_FILE" using Path-Work
 *>             go to xxx.

*>
*>  Open files
*>
     perform  Program-Start.
*>
 Main.
     initialize sinvoice-header with filler.
     move     space to WS-Service-Only.
     perform  Invoice-Details.
*>
     if       Escape-Code = "C"  *> from Invoice-Details
              go to  More-Data.
*>
     if       z not = zero
       or     Escape-Code = "Q"
              go to  Menu-Exit.
*>
     move     16  to  lin.
     move     1 to cole.
     display  " " at curs with erase eos.
*>
 Data-Input.
     initialize SInvoice-Bodies with filler.
*>
     move     zero to  i.
*>
     if       i-level-1
              perform  Inv-Level-1
     else
              perform  Inv-Level-2.
     if       Cob-Crt-Status = Cob-Scr-esc
              go to Main.
*>
     if       i not = 1
              perform End-Totals.
*>
 More-Data.
     display "Enter Further Autogen Invoices? (Y/N) [Y] " at line WS-lines col 29 with foreground-color 3.
     move     zero to Cob-Crt-Status.
     move     "Y" to WS-reply.
     accept   WS-reply at line WS-lines col 68  with foreground-color 6 update UPPER.
 *>    move     function upper-case (WS-reply) to WS-reply.
*>
     display  space at line WS-lines col 01 with erase eol.
*>
     if       WS-reply = "Y"
              go to Main.
     if       WS-reply not = "N"
              go to More-Data.
*>
 Menu-Exit.			*> Moved from program-start, silly place to have it
*>********
*>
     move     zero to  pass-value.
     perform  Sales-Close.          *>      close    sales-file
     perform  Delivery-Close.       *>               delivery-file
     perform  Analysis-Close.       *>               analysis-file.
     perform  SLautogen-Close.      *>      close    SLautogen-file
*>
     if       SL-Stock-Link = "Y"
 *>             perform Stock-Audit-Close.
              perform Stock-Close.         *>  close Stock-File  Stock-Audit
*>
     exit     program.
*>
*>****************************************************************
*>                 P R O C E D U R E S                           *
*>****************************************************************
*>
 Running-Totals section.
*>=====================
*>
     move     zero  to  sih-Net
                        sih-vat.
*>
     perform  varying k from 1 by 1 until k  >  i
              add sil-Net (k) to sih-Net
              add sil-vat (k) to sih-vat
     end-perform
*>
     move     sih-Net  to  display-9.
     if       i-level-1
              display display-9 at 1237 with foreground-color 3.
*>
     move     sih-vat  to  display-9.
     if       i-level-1
              display display-9 at 1255 with foreground-color 3.
*>
     add      sih-Net  sih-vat  giving  display-9.
*>
     if       i-level-1
              display display-9 at 1268 with foreground-color 3
     else
              display display-9 at 1270 with foreground-color 3.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Write-Details section.    *> RECHECK ALL THIS
*>====================
*>
     add      1  to  j.
     move     sih-invoice  to sil-invoice (j).
     move     j            to sil-line (j).
     move     sih-type     to sil-type (j).
     move     invoice-lines (j)  to  WS-Invoice-Record.  *> was line
     perform  SLautogen-Write.             *>  write    invoice-record.
     if       fs-reply not = zero
              perform Eval-Status
              display sl180         at line WS-23-Lines col 1 with erase eol foreground-color 4
              display fs-reply      at line WS-23-Lines col 36 with foreground-color 3
              display exception-msg at line WS-23-Lines col 39 with foreground-color 3
              display invoice-key   at line WS-23-Lines col 64 with foreground-color 3
              display sl006         at line WS-lines col 01 with foreground-color 3
              accept  WS-reply at line WS-lines col 44
              display " " at line WS-23-Lines col 1 with erase eos
     end-if.
*>
 *>    perform  Update-Stock-n-Audit.   *> NOT FOR AUTOGEN
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Read-Details section.    *> RECHECK ALL THIS
*>===================
*>
     move     zero to j.
     perform  sih-lines times
              add  1 to j
              move sih-invoice to invoice-nos   *>  IS THIS CORRECT
              move j to item-nos                *>  IS THIS CORRECT
              perform SLautogen-Read-Next
              if      FS-Reply = zeros
                      move WS-Invoice-Record to Invoice-Lines (j)
              end-if
     end-perform.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Eval-Status  section.
*>===================
*>
     move     spaces to exception-msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by exception-msg.
*>
 Main-Exit.   exit section.
*>************************
*>
 Comm-Routines section.
*>********************
*>
 Accept-Money6a.
*>-------------
*>
     move     zero to WS-poundsd6 WS-penced6 amt-ok6.
*>
 Accept-Money6b.
*>-------------
*>
     display  WS-amount-screen-display6 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs   with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 Accept-Money6c.
*>-------------
*>
     move     amt-wk-pence6 to WS-pence6.
     move     amt-wk-pds6   to WS-pound6.
     display  WS-amount-screen-display6 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept6  at curs   with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 Accept-Money7a.
*>-------------
*>
     move     zero to WS-poundsd7 WS-penced7 amt-ok7.
*>
 Accept-Money7b.
*>-------------
*>
     display  WS-amount-screen-display7 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept7  at curs   with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 Accept-Money7c.
*>-------------
*>
     move     amt-wk-pence7 to WS-pence7.
     move     amt-wk-pds7 to WS-pound7.
     display  WS-amount-screen-display7 at curs with foreground-color 3.
     accept   WS-amount-screen-accept7  at curs  with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 comm-exit.   exit section.
*>--------    ----
*>
 Inv-Level-1  section.
*>===================
*>
*> No one should be using this consider scrapping and forcing invoicer =2 etc
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
*>***
*>
     perform  varying lin from 16 by 1 until lin not < WS-23-Lines
              add      1  to  i
              move     1 to cole
              display  "(" at curs with erase eol foreground-color 2
              move     2 to cole
              display  i at curs with foreground-color 2
              move     4 to cole
              display  ") [  ]" at curs with foreground-color 2
              move     36 to cole
              display  "[          ] [ ]   {         } (" at curs with foreground-color 2
              move     78 to cole
              display  ")" at curs       with foreground-color 2
     end-perform
*>
*> i = no. lines on screen for items, then less 7 (24 line screen)
*>      why this way ,  no idea as against move 1 to i ?????
*>
*>     subtract 16 from WS-23-Lines giving m.       *> or move 1 to i
     subtract WS-Accept-Body  from  i.             *> was m from i
     move     1 to j.
     display  i at 1223 with foreground-color 3.
     move     zero to Cob-Crt-Status.
     perform  Get-Data-1.
     if       Cob-Crt-Status = Cob-Scr-esc
              go to Main-Exit.
*>
     if       new-screen = 1
              go to Loop.
*>
     if       sil-description (i) not = spaces
       and    i not = 40                      *> FIXED Invoice line limit ?  !!
              go to Loop.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Get-Data-1   section.
*>===================
*>
*> No one should be using this consider scrapping and forcing invoicer =2 etc
*>
 Get-Data-1-Main.
     add      j  15  giving  lin.
*>
     if       lin  >  WS-23-Lines
              subtract 1 from i
              move 1 to new-screen
              go to  Main-Exit.
*>
     move     zero to new-screen.
*>
 Get-Code.
     if       i  >  1
       and    sil-pa (i) = spaces
              move  sil-pa (i - 1)  to  sil-pa (i).
*>
     move     sil-pa (i) to WS-pa.
     move     7 to cole.
     display  WS-pa at curs with foreground-color 3.
     accept   WS-pa at curs with foreground-color 3 update.
     move     WS-pa to sil-pa (i) pa-group.
     move     spaces  to  sil-description (i).
*>
     if       WS-pa = spaces
              go to  Main-Exit.
     if       Cob-Crt-Status = Cob-Scr-esc
              go to Main-Exit.
*>
     if       WS-pa = "<<"
        and   i = 1
              go to Get-Code.
*>
     if       WS-pa = "<<"
              subtract  1  from  lin
              if    lin  >  15
                    subtract  1  from  i
                    subtract 1 from j
                    go to  Get-Code
              else
                    subtract WS-Accept-Body from  i          *> Was 8 Need to follow logic, can we use WS-Accept-Body ??
                    go to  Get-Data-1-Main.
     move     "S" to pa-system.
     move     11 to cole.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.     *> read analysis-file record invalid key
     if       FS-Reply = 21
              display SL186 at line WS-23-Lines col 1 with foreground-color 4 highlight beep
              go to  Get-Code.
     display  " " at line WS-23-Lines col 1 with erase eol.
*>
     display  PA-Desc at curs with foreground-color 3.
     move     PA-Desc  to  sil-description (i).
*>
 Get-Net.
     move     37 to cole.
     perform  Accept-Money7a thru Accept-Money7b.
     if       amt-ok7 = zero
              go to Get-Code.
     move     amt-ok7 to sil-Net (i) WS-Net.
*>
 Get-Vat-Code.
*>
*>  Only using 1st three as last 2 are for local sales tax but not in UK.
*>   NOTE that it is not currently programmed for (e.g., last 2).
*>
     move     50 to cole.
     accept   Vat-Code at curs with foreground-color 3 update.
*>
     if       Vat-Code  >  3
              go to  Get-Vat-Code.
*>
     move     Vat-Code  to  sil-Vat-Code (i).
     if       Vat-Code = zero
              move  zero  to  amt-ok6
       else
              move vat-rate (Vat-Code) to WS-vat-rate
              compute amt-ok6 rounded =  (WS-Net * WS-vat-rate) / 100.
*>
 Get-Vat-Rate.
     move     56 to cole.
     perform  Accept-Money6c.
     move     amt-ok6 to sil-vat (i) WS-vat.
*>
     add      WS-vat WS-Net giving  display-9.
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
 Inv-Level-2  section.
*>===================
*>
     display  WS-dash at 1101 with foreground-color 2.
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
 Loop.
     perform  varying lin from 16 by 1 until lin not < WS-23-Lines
              add     1  to  i
              move    1 to cole
              if      SL-Stock-Link = "N"		*> No stock then process PA code
                      display "[             ][  ][" at curs with foreground-color 2 erase eol
                      move    51 to cole
                      display   "][     ][          ][     ][ ]" at curs  with foreground-color 2
              else				*> ignore PA
                      display "[             ][" at curs with foreground-color 2 erase eol
                      move    49 to cole
                      display "]  [     ][          ][     ][ ]" at curs  with foreground-color 2
              end-if
     end-perform
*>
*> This is what the item capture displays look like & 1st is for non-linked
*>   stock Control:
*>
*>    Product    Code <---------Description-------->   Qty   Unit Price  Disc. Vat
*>[      12 >13 ][2 ][        24 >30                ][  5  ][  9>10    ][  5  ][1]
*> If STOCK LINKED:
*>    Product     <----------Description--------->    Qty   Unit Price  Disc. Vat
*>[      12 >13 ][        24 >32                  ]  [  5  ][  9>10    ][  5  ][1]
*>
*>     subtract 16 from WS-23-Lines giving m.  *> or move 1 to i = pos. in line item table
*>
     subtract WS-Accept-Body from i.                    *> m = WS-Accept-body
     move     1  to  j.
*>
     display  i at 1223 with foreground-color 2.
*>
     perform  Get-Data-2.
     if       Cob-Crt-Status = Cob-Scr-esc
              go to Main-Exit.
*>
     if       new-screen = 1
              go to  Loop.
*>
     if       WS-product not = spaces
       and    i not = 40			*> max no. of items per invoice
              go to  Loop.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Get-Data-2   section.
*>===================
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
*>  IT DOES NOT ACCEPT codes 4 and 5                                   *
*>**********************************************************************
*>
 Get-Data-2-Main.
     add      j  15  giving  lin.
     if       lin  >  WS-23-Lines - 1
              subtract  1  from  i
              move  1  to  new-screen
              go to  Main-Exit.
*>
     move     zero  to  new-screen.
*>
 Get-Product.
     if       i  >  1
       and    sil-product (i) = spaces
              move  sil-product (i - 1) to sil-product (i).  *> display prev entered code for new line
*>                                                              to save typing
     display  i at 1223 with foreground-color 2.             *> disp line # on summary line
     move     2 to cole.
     move     sil-product (i) to WS-product.
     accept   WS-product at curs with foreground-color 3 update.
*>
     move     spaces  to  sil-description (i).
*>
*> Process description accept & search via start / read next if F6 detected
*>
     if       Cob-Crt-Status = Cob-Scr-F6
              go to Bypass-Product-Space-Tests.
*>
     if       WS-product = spaces
              go to Main-Exit.
     if       Cob-Crt-Status = Cob-Scr-esc
              go to Main-Exit.
*>
 Bypass-Product-Space-Tests.
     move     function upper-case (WS-product) to WS-product.
     move     WS-product to sil-product (i)
                            test-product
                            WS-Temp-Stock-Key.
*>
     if       sil-comment
              move zero to WS-Net WS-unit WS-qty
              go to  Get-desc.
*>
     if       WS-product = "<<           "
              subtract  1  from  lin
              go to Get-prod-test.
*>
     if       SL-Stock-Link not = "Y"    *> continue with old code to accept all data
              go to Get-Code.
     move     17 to cole.                *> 4 Desc.
*>
*> Search nearest Abrev key and read next ..
*>  When this is tested we can wrap this and next together
*>    with a F3 test then a if F2 or F3 test
*>
*> Leaving these embedded literals in to help in dry testing etc
*>   instead of replacing with fixed SLnnn vars.
*>
     if       Cob-Crt-Status = Cob-Scr-F3
 *>
 *> Search Abrev then read next & thereafter F2 until wanted
 *>
              move WS-Abrev-Stock to WS-Stock-Abrev-Key
              move  2 to File-Key-No
              set fn-not-less-than to true
              perform Stock-Start              *> start Stock-File key not < WS-Stock-Abrev-Key invalid key
              if    FS-Reply = 21
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-product
              end-if             *> end-start
              perform Stock-Read-Next        *> read  Stock-File next record at end
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-product
              end-if                         *> end-read
              move WS-Stock-Abrev-Key to sil-product (i)    *> have we the right one?
              display WS-Stock-Desc at curs with foreground-color 3
              go to Get-Product
     end-if
*>
     if       Cob-Crt-Status = Cob-Scr-F2                *> read next record
              perform Stock-Read-Next      *> read  Stock-File next record at end
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-product
              end-if                       *> end-read
              move WS-Stock-Abrev-Key to sil-product (i)    *> have we the right one?
              display WS-Stock-Desc at curs with foreground-color 3
              go to Get-Product
     end-if
*>
*> Search on Desc. but has dup keys so disp. Abrev. code
*>    & F5 for next on description
*>  When this is tested we can wrap this and next together with a
*>      F6 test then a if F5 or F6 test
*>
     if       Cob-Crt-Status = Cob-Scr-F6
              move    sil-description (i) to WS-description
              accept  WS-description at curs with foreground-color 3 update
              move WS-Description to WS-Stock-Desc
              move  3 to File-Key-No         *> start Stock-File key not < WS-Stock-Desc invalid key
              set fn-not-less-than to true
              perform Stock-Start
              if    FS-Reply = 21
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if                      *> end-start
              perform Stock-Read-Next     *> read  Stock-File next record at end
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-Product
              end-if                      *> end-read
              move WS-Stock-Abrev-Key to sil-product (i)    *> Got the right one? Show desc, stock held & retail price
                                         WS-Product
              display WS-Stock-Desc at curs with foreground-color 3 highlight
              move Stock-Held to WS-Qty
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
     if       Cob-Crt-Status = Cob-Scr-F5      *> Read next on Desc.
              perform Stock-Read-Next         *> read  Stock-File next record at end
              if    FS-Reply = 10
                    move SL196 to WS-Stock-Desc
                    display WS-Stock-Desc at curs with foreground-color 4
                    go to Get-product
              end-if                        *> end-read
              move WS-Stock-Abrev-Key to sil-product (i)    *> Got the right one? Show desc, stock held & retail price
                                      WS-Product
              display WS-Stock-Desc at curs with foreground-color 3 highlight
              move Stock-Held to WS-Qty
              display WS-Qty at line lin col 53 with foreground-color 3 highlight
              move Stock-Retail to amt-ok7
              move amt-wk-pds7   to WS-pound7
              move amt-wk-pence7 to WS-pence7
              display WS-amount-screen-display7 at line lin col 60 with foreground-color 3 highlight
              go to Get-Product
     end-if
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
     perform  Stock-Read-Indexed    *> read Stock-File record key WS-Stock-Abrev-Key invalid key
     if       FS-Reply = 21
              move SL196 to WS-Stock-Desc
              display WS-Stock-Desc at curs with foreground-color 4
              go to Get-product
     end-if                        *> end-read
*>
*> can shorten code now so rem out next block vbc 27/08/17
*>
 *>    else
 *>             perform Stock-Read-Indexed    *> read Stock-File key WS-Stock-Key invalid key
 *>             if   FS-Reply = 21
 *>                  move SL196 to WS-Stock-Desc
 *>                  display WS-Stock-Desc at curs with foreground-color 4
 *>                  go to Get-product
 *>             end-if                        *> end-read
 *>    end-if
     perform  Test-For-Read-Stock.
*>
 Process-Stock-Record.
*>
*>  Have the required Stock record so get and show the desc
*>
*>     if       WS-Stock-Desc not = SL196
*>              display WS-pa        at line lin col 17 with foreground-color 3
     move     17 to cole.        *> Desc.
     move     Stock-sa-Group to WS-pa pa-group sil-pa (i).
     display  WS-Stock-Desc   at curs with foreground-color 3.
     move     WS-Stock-Desc    to WS-description sil-description (i).
     move     Stock-Retail  to amt-ok7.
     move     Stock-Retail  to WS-Unit.
     move     amt-wk-pds7   to WS-pound7.
     move     amt-wk-pence7 to WS-pence7.
     display  WS-amount-screen-display7 at line lin col 60 with foreground-color 3.
 *>    move     Stock-Held to WS-qty. *> sl810
     move     1 to WS-Qty.    *> Autogen change
     if       Stock-Services-Flag not = "Y"
              move  "N" to WS-Service-Only.
     go       to Get-Qty.          *> Bypass manual input code as comes from stock record
*>
 Get-Prod-Test.   *> THESE TESTS LOOK WRONG IF SCREEN LONGER THAN 24 LINES <<<<<
     if       i = 1
              add 1 to lin
              go to Get-product.
*>
     if       lin  >  15
              subtract  1  from  i
              subtract  1  from  j
              go to  Get-product
      else
              subtract WS-Accept-Body from i           *> instead of 8 can we use WS-Accept-Body ??
              go to  Get-Data-2-Main.
*>
 Get-Code.
     if       i  >  1
       and    sil-pa (i) = spaces
              move  sil-pa (i - 1)  to  sil-pa (i).
*>
     move     sil-pa (i) to WS-pa.
     move     17 to cole.
     accept   WS-pa at curs with foreground-color 3 update.
*>
     move     spaces  to  sil-description (i).
*>
     if       WS-pa = spaces
              go to  Get-product.
*>
     move     WS-pa to pa-group sil-pa (i).
     move     "S" to pa-system.
     move     21 to cole.                         *> disp error in desc.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.      *> read analysis-file record invalid key
     if       FS-Reply = 21
              display SL186 at curs  with foreground-color 4
              go to  Get-Code.
*>
 Get-Desc.
     if       i  >  1
         and  sil-description (i) = spaces
         and  not  sil-comment
              move  sil-description (i - 1) to  sil-description (i).
*>
     if       SL-Stock-Link = "Y"
              move 17 to cole
     else
              move 21 to cole.
     move     sil-description (i) to WS-description.
     display  WS-description at curs with foreground-color 3.
     accept   WS-description at curs with foreground-color 3 update.
*>
     move     WS-description to sil-description (i).
     if       WS-description = space
              move "B" to Escape-Code
     else
              move space to Escape-Code.
     if       Escape-Code = "B"
         and  sil-comment
              go to Get-product.
     if       Escape-Code = "B"
              go to  Get-Code.
*>
     if       sil-comment
              go to  jump-totals.
*>
 Get-Qty.
     if       SL-Stock-Link = "N"		*> if it is shown = current stock
              move     zero to WS-qty.
     move     53 to cole.
     display  WS-qty at curs with foreground-color 3.
     accept   WS-qty at curs with foreground-color 3 update.
*>
     if       WS-qty = zero
              go to Get-desc.
     if       SL-Stock-Link = "Y"         *> make sure not selling more stock than held
       and    WS-qty > Stock-Held
              move Stock-Held to WS-Qty
              go to Get-Qty.
*>
     if       SL-Stock-Link = "Y"    *> bypass accept unit price
              go to Recomp-Net.
*>
 Get-Unit.
     move     60 to cole.
     perform  Accept-Money7a thru Accept-Money7b.
     if       amt-ok7 = zero
              go to Get-qty.
     move     amt-ok7 to WS-unit.
*>
 Recomp-Net.
     multiply WS-qty by  WS-unit giving  WS-Net on size error
              display  "SizER" at curs with blink foreground-color 4
              go to Get-qty.
*>
     move     WS-Net to  display-9 sil-Net (i).
     move     WS-qty to sil-qty (i).
     move     WS-unit to sil-unit (i).
     display  display-9 at 1232 with foreground-color 3.
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
     move     WS-discount to  work-d sil-discount (i).
     move     WS-Net to  work-n.
*>
     multiply work-n by work-d giving work-1
     divide   work-1 by 100    giving work-1
*>
     subtract work-1  from  WS-Net.
*>
     move     WS-Net to sil-Net (i) display-9.
     display  display-9 at 1232 with foreground-color 3.
*>
 Get-Vat-Code.
     move "S" to Vat-Code-X.  *> 17/2/23  for Standard rate
     move     79 to cole.
     display  Vat-Code-X at curs with foreground-color 3.
     accept   Vat-Code-X at curs with foreground-color 3 update.
*>
*> THIS NEEDS Adding to for rates 4 and 5.
*>
*>
*>   Accept S, R and Z replacing with 1, 2 & 3.      Rating   %   - Effective
*>
     if       Vat-Code-X = "S"                   *> Standard code 1 (20% - 01/01/17)
              move 1 to Vat-Code
      else
       if     Vat-Code-X = "R"                   *> Reduced  code 2 (05% - 01/01/17)
              move 2 to Vat-Code
        else
         if   Vat-Code-X = "Z"                   *> Zero     code 3 (00% - 01/01/17)
              move 3 to Vat-Code.
*>
     if       Vat-Code < 1 or > 3                *> using 1st three as last 2 are Sales tax, Not used in the UK.
              go to  Get-Vat-Code.                *> so change test for 'not = 4 or 5' instead of '> 3'
*>
     move     Vat-Code  to  sil-Vat-Code (i).
*>
     if       Vat-Code = zero
              move  zero  to  WS-vat
       else
              move vat-rate (Vat-Code) to WS-vat-rate
              compute  WS-vat rounded =  (WS-Net * WS-vat-rate) / 100.
*>
     move     WS-vat to  display-9 sil-vat (i).
     display  display-9 at 1249 with foreground-color 3.
*>
     perform  Running-Totals.
*>
 Jump-Totals.
     add      1  to  j.
     add      1  to  i.
     go to    Get-Data-2-Main.
*>
*> CAN IT BE USED FOR OTHER FILES  (SL194 os for Stock file) ??????
*>
 Test-For-Read-Stock.
     if       fs-reply not = zero
              perform Eval-Status
              display SL194    at line WS-23-Lines col 1 with foreground-color 4 highlight erase eol
              display fs-reply at line WS-23-Lines col 21 with foreground-color 2 highlight
              display exception-msg at line WS-23-Lines col 24 with foreground-color 3
              display SL006 at line WS-lines col 1
              accept WS-reply at line WS-lines col 45
     end-if.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 End-Totals   section.
*>===================
*>
 End-Totals-Main.
     move     zero to Cob-Crt-Status.
     perform  Total-Screen.
     if       Cob-Crt-Status = Cob-Scr-esc
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
     display  "Invoice ok to Store" at 1761 with foreground-color 2.
     display  "(Y/N) ? [Y]" at 1868 with foreground-color 2.
     display  " ESC to Quit" at 1964 with foreground-color 2.
*>
 Confirmation.
*>***********
*>
     move     "Y"  to   WS-reply.
     accept   WS-reply at 1977 with foreground-color 6 UPPER update.
 *>    move     function upper-case (WS-reply) to WS-reply.
*>
     if       Cob-Crt-Status = Cob-Scr-esc
              move  "Q"  to  Escape-Code
              go to Main-Exit.
*>
     if       WS-reply = "N"
              go to  End-Totals-Main.
*>
     if       WS-reply not = "Y"
              go to  Confirmation.
*>
     move     "P"  to  sih-status.
 *>    move     space to sih-status-P.
*>
*>        JIC normal stock items are present (turns this to space or "N"
*>          Do NOT print picking/delivery note, marked as already done.
*>
     if       WS-Service-Only = "Y" or = space
              move     "P" to sih-status-P.
     subtract 1  from  i.
     move     i    to  sih-lines.
*>
     move     sinvoice-header  to  WS-Invoice-Record.  *> was invoice-record
     if       Entry-Mode
              perform  SLautogen-Write       *>  write    SLautogen-record.
     else
       if     Amend-Mode
              perform  SLautogen-Rewrite.
*>
     if       fs-reply not = zero
              perform Eval-Status
              display sl180         at line WS-23-Lines col  1 with erase eol foreground-color 4
              display fs-reply      at line WS-23-Lines col 36 with foreground-color 3
              display exception-msg at line WS-23-Lines col 39 with foreground-color 3
              display invoice-key   at line WS-23-Lines col 64 with foreground-color 3
              display sl006         at line WS-lines    col  1 with foreground-color 3
              accept  WS-reply      at line WS-lines    col 44
              display " "           at line WS-23-Lines col  1 with erase eos
     end-if
*>
     move     zero to  j.
     perform  Write-Details  i  times.
*>
     move     1 to s-flag-i.
     move     11  to  lin.
     move     1 to cole.
     display  " " at curs with erase eos.
*>
     go       to Main-Exit.
*>
 Main-Exit.   exit section.
*>********    *****
*>
 Total-Screen section.
*>===================
*>
     move     1 to cole.
     move     11 to lin.
     display  " " at curs with erase eos.
     display  WS-dash at 1101 with foreground-color 2.
*>
     if       i-level-1
              move  1  to  Menu-Reply
     else
              move  2  to  Menu-Reply.
*>
     display  "Level "   at 1201 with foreground-color 2.
     display  Menu-Reply at 1207 with foreground-color 2.
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
     move     sih-Net  to  display-9.
     display  display-9 at 1426 with foreground-color 3.
*>
     move     sih-vat  to  display-8.
     display  display-8 at 1441 with foreground-color 3.
*>
     add      sih-Net  sih-vat  giving  display-9.
     display  display-9 at 1455 with foreground-color 3.
*>
 Get-Days.
     move     zero to sih-days sih-carriage.
     if       sih-type = 2
              move sales-credit  to  sih-days
     else if  sih-type = 4
              move pf-retention to sih-days.
     move     sih-days to WS-dayes.
     if       sih-type not = 2
              display WS-dayes at 1472 with foreground-color 3
              go to Get-extra.
*>
     display  WS-dayes at 1472 with foreground-color 3.
     accept   WS-dayes at 1472 with foreground-color 3 update.
     move     WS-dayes to sih-days.
*>
 Get-Extra.
     if       Extra-Type = space
              move zero to sih-extra sih-e-vat
              go to Get-carriage.
*>
     if       Extra-Rate not = zero
              compute  sih-extra = (sih-Net * extra-rate) / 100
     else
              move  zero  to  sih-extra.
*>
     move     1526 to curs.
     move     sih-extra to amt-ok7.
     perform  Accept-Money7c.
     move     amt-ok7 to sih-extra.
*>
 Get-Extra-Vat.
     if       sih-extra = zero
              move  zero to  sih-e-vat
              go to Get-carriage.
*>
     compute  amt-ok6 = sih-extra  *  vat-rate-1  /  100.
*>
     move     1541 to curs.
     perform  Accept-Money6c.
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
 Get-Carriage.
     move     1626 to curs.
     perform  Accept-Money7a thru Accept-Money7b.
     move     amt-ok7 to sih-carriage.
     compute  amt-ok6 rounded = sih-carriage * vat-rate-1 / 100.
*>
*> Note that vat-rate-1 must be standard rate for p & p
*>
 Get-Carriage-Vat.
     move     1641 to curs.
     perform  Accept-Money6c.
     move     amt-ok6 to sih-c-vat.
     add      sih-carriage  sih-c-vat  giving  display-9.
     display  display-9 at 1655 with foreground-color 3.
*>
 Get-Deduct-Amt.
  *>   if       WS-named = "A"
  *>      and   oi-Net = sih-Net
  *>      and   oi-vat = sih-vat
  *>      and   oi-carriage = sih-carriage
  *>            move "Z" to WS-named.
*>
 *>    if       (sih-type not = 2  and not = 3)       *> Invoices, Credit Notes
     if       not Late-Charges
              move zero to sih-deduct-amt sih-deduct-vat sih-deduct-days
              go to  Main-Exit.
 *>         or  not late-charges
 *>         or  WS-named = "Z"
 *>             move zero to sih-deduct-amt sih-deduct-vat sih-deduct-days
 *>             go to  Main-Exit.
*>
     compute  amt-ok7 =  sih-Net  /  10.      *> Use default discount of 10% can be overridden
*>
     if       amt-ok7 <  4      *> DEFAULT MINIMUM Deduct amount Should this be changed ???????
              move  4  to  amt-ok7.      *> and for sl910/20
*>
     move     1726 to curs.
     perform  Accept-Money7c.
     move     amt-ok7 to sih-deduct-amt.
*>
 Get-Deduct-Vat.
     move     zeros to sih-deduct-vat.
*>
     add      sih-Net  sih-extra  sih-carriage  sih-deduct-amt giving  display-9.
     display  display-9 at 1926 with foreground-color 3.
*>
     add      sih-vat  sih-e-vat  sih-c-vat  sih-deduct-vat giving  display-8.
     display  display-8 at 1941 with foreground-color 3.
*>
     add      sih-Net  sih-extra  sih-carriage  sih-deduct-amt
              sih-vat  sih-e-vat  sih-c-vat  sih-deduct-vat   giving  display-9.
     display  display-9 at 1955 with foreground-color 3.
*>
 Get-Deduct-Days.
     move     sih-days  to  WS-dayes.
     display  WS-dayes at 1772 with foreground-color 3.
     accept   WS-dayes at 1772 with foreground-color 3 update.
     move     WS-dayes to sih-deduct-days.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Invoice-Details section.
*>======================
*>
 Invoice-Details-Main.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Recurring Invoicing Data Entry" at 0127           with foreground-color 2. *> COB-COLOR-GREEN
     perform  zz070-Convert-Date.        *> convert date to LOCALE format
     display  WS-date at 0171 with foreground-color 2.
*>
     display  "****************************************" at 0341 with foreground-color 2.
     display  "* Mode  [ ] [E=Entry, Update, Delete]   " at 0441 with foreground-color 2.
     display  "*         or E=F2, U=F3, D=F4           " at 0541 with foreground-color 2.
     display  "             ESC to quit                " at 0641 with foreground-color 2.
     display  "----------------------------------------" at 0741 with foreground-color 2.
*>
     move     "E" to WS-Entry-Mode.
     accept   WS-Entry-Mode  at 0450 with foreground-color 3 update upper. *> COB-COLOR-CYAN
     if       Cob-Crt-Status = Cob-Scr-F2
              move "E" to WS-Entry-Mode
     else
       if     Cob-Crt-Status = Cob-Scr-F3
              move "U" to WS-Entry-Mode
       else
         if   Cob-Crt-Status = Cob-Scr-F4
              move "D" to WS-Entry-Mode
         else
          if  Cob-Crt-Status = Cob-Scr-Esc
              move  "Q"  to  Escape-Code
              go to  Main-Exit
          else
           if not WS-Valid-Modes
              display "SL197 Invalid mode - try again"   at 0401  with foreground-color 2 BEEP
              go to Invoice-Details-Main.
     display  CLR40  at 0401.
*>
     if       Entry-Mode or Update-Mode
              display  "*A/C Nos  [       ]*Rec.   [        ]  *" at 0441 with foreground-color 2 erase eos
              display  "*Repeat # [  ]     *Freq   [ ] [Y,M,Q ]*" at 0541 with foreground-color 2
              display  "*Date  [  /  /    ]*Ref    [          ]*" at 0641 with foreground-color 2
              display  "****************************************" at 0741 with foreground-color 2
              display  "F1 = Setup new Customer; F8 = Only Show delivery details (at A/C entry)"
                                                                  at 0907 with foreground-color COB-COLOR-MAGENTA
              display  "Remember to Set date to FIRST of month"   at 1001 with foreground-color 5
              display  "Type [ ]  <2> = Account"                  at 1201 with foreground-color 2.
*>
     if       Delete-Mode
              display  "*A/C Nos  [       ]*Rec.   [        ]  *" at 0441 with foreground-color 2 erase eos
              display  "****************************************" at 0541 with foreground-color 2.
*>
 Customer-Input.
     move     spaces  to  sih-customer.
     move     zero to Cob-Crt-Status.
     accept   sih-customer at 0452 with foreground-color 3 update UPPER.
     display  space at col 1 line WS-23-Lines with erase eol. *> Clr SL187
     if       Cob-Crt-Status = Cob-Scr-F1
              go to New-Customer.
*>
     if       Cob-Crt-Status = Cob-Scr-F8
              move "Y" to WS-Show-Delivery
     else
              move "N" to WS-Show-Delivery.
*>
 Customer-Test.
     if       sih-customer = spaces
       or     Cob-Crt-Status = Cob-Scr-Esc
              move  "Q"  to  Escape-Code
              go to  Main-Exit.
*>
     move     1  to  c-check.
     move     sih-customer  to WS-Sales-Key.
*>
     move     1 to File-Key-No.
     perform  Sales-Read-Indexed.       *> read sales-file record invalid key
     if       fs-reply = 21
              move  zero  to  c-check.
*>
     if       not  c-exists
              display  "No such Customer" at 0401 with foreground-color 3
              go to  Customer-Input.
     display  CLR16 at 0401.
     display  space at 0901 with erase eol.  *> Clear F1 comment line
*>
 Delivery-Read.
     if       delivery-tag = zero     *> Only show delivery details if F8 pressed instead of
       or     WS-Show-Delivery = "N"  *> accept on cust no. input (here there is no del addr data)
              go to Customer-Setup.
*>
     move     "D"          to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Read-Indexed.          *> read delivery-file invalid key
     if       fs-reply = 21
              move  zero  to  delivery-tag
              go to  Customer-Setup.
*>
     move     deliv-address to address-a.
     display  "Delivery Address" at 0302 with foreground-color 3.
     go       to Customer-Display.
*>
 Customer-Setup.
     display  CLR16 at 0302 with foreground-color 3.
     move     sales-address  to  address-a.
*>
 Customer-Display.
     if       delivery-tag = zero
              display sales-name at 0301 with foreground-color 3
     else
              display deliv-name at 0301 with foreground-color 3.
*>
     move     1  to  z.
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim
                  into  address-line  count z  pointer  z.
     display  address-line at 0401 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim
                  into  address-line  count z  pointer  z.
     display  address-line at 0501 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim
                  into  address-line  count z  pointer  z.
     display  address-line at 0601 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim
                  into  address-line  count z  pointer  z.
     display  address-line at 0701 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  into  address-line   pointer  z.
     display  address-line at 0801 with foreground-color 3.
*>
     move     spaces  to  address-line.
*>
 Check-For-Delete-Amend.
     if       Delete-Mode or Amend-Mode
              move     zero to sih-Test
                               sih-Invoice
              accept   sih-Invoice  at 0469 with foreground-color 3 update
              if       sih-Invoice = zero
                or     Cob-Crt-Status = Cob-Scr-Esc
                       move  "Q"  to  Escape-Code
                       go to  Main-Exit
              end-if
              move     1 to File-Key-No
              move     sih-Invoice to Invoice-Nos
              move     zero to Item-Nos
              perform  SLautogen-Read-Indexed    *> Get header record
              if       fs-reply not = zero   *> was = 21mariadb-10.5.20-1.mga8.x86_64
                       display  SL187 at col 1 line WS-23-Lines with foreground-color 5 BEEP *> Magenta
                       go to   Check-For-Delete-Amend
              end-if
              display  space at  col 1 line WS-23-Lines with erase eol  *> Clr error line
              if       Delete-Mode
                       go to  Delete-Current-Record
              end-if
              perform  Read-Details
     end-if.
*>
*> Now Amend
*>
 Get-Invoice-No.
     if       Entry-Mode
              move     SL-Next-Rec  to WS-Next-Inv
              display  WS-Next-Inv at 0469 with foreground-color 7       *> White
              add      1 to SL-Next-Rec.                             *> remember to deduct one if entry aborted OR add after write
*>
*>
*> Now have header get Invoice lines for same invoice nos
*> Data present for Amend or initialised for Entry (but have invoice-nos)
*>
 Repeat-Count-Input.
     display  "Repeat option values : "  at 1501.
     display  "99 = NO Repeated operations (option ignored)" at 1601.
     display  "00 = Record WILL BE DELETED" at 1701.
     display  "01 - 96 number of repeated invoice generations before record is deleted" at 1801.
     accept   sih-Repeat at 0552 with foreground-color 3 update.
     if       sih-Repeat not numeric
              display  "Not numeric " at col 1 line WS-23-Lines  with foreground-color 3 BEEP
              go to Repeat-Count-Input.
     display  CLR16 (1:12)  at col 1 line WS-23-Lines.
     display  space at 1501 with erase eol.
     display  space at 1601 with erase eol.
     display  space at 1701 with erase eol.
     display  space at 1801 with erase eol.
*>
 Freq-Input.
 *>    move     "Y" to Sih-Freq.    *> For yearly
     accept   Sih-Freq at 0569 with foreground-color 3 update UPPER.
     if       not sih-Valid-Freqs
              display "Freq invalid try again" at col 1 line WS-23-Lines  with foreground-color 3 BEEP
              go to Freq-Input.
     display  CLR22 at col 1 line WS-23-Lines.
*>
 Date-Input.
     if       Update-Mode   *>  convert bin date to display for updating HERE
              move     sih-Date to U-Bin
              perform  zz060-Convert-Date.
*> Check date in right format on screen
     accept   WS-date at 0649 with foreground-color 3 update.
     if       Cob-Crt-Status = Cob-Scr-esc
         or   WS-date = spaces
              move 1 to z
              go to  Main-Exit.
*>
     move     WS-date to WS-test-date.
     perform  zz050-Validate-Date.
     if       u-bin = zero
              go to  Date-Input.
     display  space  at 1001 with erase eol.  *> Clear date reminder display
*>
*> Taking date as is so can be any during a month - NO TEST OR CHANGE
*>
     move     WS-test-date to WS-date.  *> still need orig. disp date as WS-date now UK
     move     u-bin  to  sih-date.
*>
 Ref-Input.
     accept   sih-ref at 0669 with foreground-color 3 update.
*>
*>  CAN WE NOT JUST FORCE THIS AS 2 ????
*>
 Type-Input.
     move     2 to sih-type.
     accept   sih-type at 1207 with foreground-color 3 update.
     move     space to WS-named.
     if       sih-type = zero
              go to Invoice-Details-Main. *> restart input
*>
     if       sih-type  not = 2
              display  "Type must be 2 (Invoice)" at 1236 with foreground-color 3
              go to  Type-Input.
     display  space at 1236 with erase eol.
*>
     move     d-types  to add-line1.            *> JIC others added
     display  space at 1201 with erase eol.
     display  ">>> " at 1231 with foreground-color 2.
     display  add-line1 at 1235 with foreground-color 2.
*>
     move     zero to sih-cr.
     move     zero to z.
*>
*>  Type 2 (Account) only
*>
*>   Leave this in for the moment as not sure it is NOT needed
*>     but mention process in manual!
*>
     move     zero  to  we-error.
*>
     subtract sales-unapplied from sales-current.
*>
     if       sales-current  >  zero
              subtract sales-last-inv from run-date giving  work-1
              if work-1  >  sales-credit
              display "Overdue Balance <<<" at 1648   with foreground-color 2 highlight
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
     display  ">>> Warning! "      at 1635 with foreground-color 2  highlight.
     display  "**********************" at 1958  with foreground-color 2.
     display  "*" at 2058 with foreground-color 2.
     display  "*" at 2158 with foreground-color 2.
     display  "*" at 2080 with foreground-color 2.
     display  "*" at 2180 with foreground-color 2.
     display  "**********************" at 2258  with foreground-color 2.
*>
     display  "ESC To Abort" at 2160 with foreground-color 2.
     display  "Return To Continue" at 2060 with foreground-color 2.
     move     zero to z.
     accept   z at 2174 with foreground-color 6 update.
     if       Cob-Crt-Status = Cob-Scr-esc
              move 1 to z
                        Cob-Crt-Status
              subtract 1 from SL-Next-Rec
              go       to Main-Exit.
*>
 Delete-Current-Record.
*>
*>  We do NOT record deleted record # - they are not reused as not needed for audit purposes.
*>
     display  "Confirm you wish to delete this Autogen record Y/N [ ]"
                                                  at col 1 line WS-23-Lines with foreground-color 5. *> Magenta
     accept   WS-Reply at col 53 line WS-23-Lines with foreground-color 2 UPPER BEEP.
     if       WS-Reply not = "Y" and not = "N"
              display "Try again using (Y/N)" at col 61 line WS-23-Lines with foreground-color 2 BEEP.
              go to Delete-Current-Record.
     display space at col 1 line WS-23-Lines with erase eol.
     if       WS-Reply = "Y"
              move     1 to File-Key-No
              move     Sinvoice-Header to WS-Invoice-Record
              if       not FS-Cobol-Files-Used
                       perform  SLautogen-Delete-All
              else
                       perform  SLautogen-Delete
                       move     sih-Invoice to Invoice-Nos
                       move     zero to j
                       perform  sih-lines times
                                add      1 to J
                                move     J to Item-Nos
                                perform  SLautogen-Delete
                       end-perform
              end-if
     end-if
     display  space  at col 1 line WS-23-Lines with erase eol.
     move     "C" to Escape-Code.  *> See if there is mnore to do.
     go to    Main-Exit.
*>
 New-Customer.
     perform  SLautogen-Close.
*>
     perform  Sales-Close.               *> close sales-file
     perform  Delivery-Close.            *> close delivery-file
     perform  Analysis-Close.            *> close analysis-file
     if       SL-Stock-Link = "Y"
              perform  Stock-Close.      *> close Stock-File.
 *>    if       Stk-Audit-Used = 1
 *>             perform Stock-Audit-Close. *> close Stock-Audit.
*>
*> Call SL cust create program for New customer.
*>
     call     "sl960" using WS-calling-data system-record to-day.
     perform  program-start.
     go       to Invoice-Details-Main.
*>
 Main-Exit.   exit section.
*>********    ****
*>
 Program-Start section.
*>====================
*>
     display  space at 0101 with erase eos.
     move     to-day to u-date.          *> in UK date form
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15        *> Analysis Needed for sl820 ? & sl830
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    move 1 to WS-Process-Func WS-Sub-Function
                    call "sl070" using WS-calling-data
                                       system-record
                                       to-day
                                       file-defs
                    call  "CBL_CHECK_FILE_EXIST" using File-15   *> Only if the call failed
                                                       File-Info
                    if    return-code not = zero          *> not = zero - No file found
                          display   SL192 at 2301
                          display   SL003 at 2401
                          accept WS-Reply at 2430
                    end-if
              end-if
     end-if
*>
     perform  Sales-Open.             *> open input sales-file delivery-file analysis-file.
     perform  Delivery-Open.          *> these 2 are open I-O to force creation.
     perform  Analysis-Open.
*>
*> Create autogen file if not exist and set autogen flag and (system rec) next-inv field.
*>
     if       FS-Cobol-Files-Used             *> create Autogen if not exist.
              call  "CBL_CHECK_FILE_EXIST" using File-4       *> slautogen
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    perform  SLautogen-Open-Output    *> open output SLautogen-file
                    perform  SLautogen-Close          *> close SLautogen-file
                    move     "Y" to SL-Autogen
                    move     1   to SL-Next-Rec    *> SIMILAR TO NEXT INVOICE #
              end-if                               *> as file is ISAM
     end-if
*>
     move     zero  to  Menu-Reply.
     perform  SLautogen-Open.             *>  open i-o SLautogen-file.
*>
*> if linked open Stock & Audit file
*>
     if       SL-Stock-Link = "Y"
       if     FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-11        *> Stock file
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    perform Stock-Open-Output      *>  open output stock-file  *> OC doesnt create in i-o - possible bug
                    perform Stock-Close            *>  close       stock-file
              end-if
              perform Stock-Open                   *> open i-o  stock-file   Thats ok we just wont find any items
       end-if
     end-if.
*>
 Main-Exit.   exit section.
*>********    ****
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
              move WS-Month to WS-Inv-Month    *> done again for UK - but JIC
              move 1 to Date-Form.
     if       Date-UK
              move WS-Month to WS-Inv-Month
              go to zz050-test-date.
     if       Date-USA                *> swap month and days
              move WS-days  to WS-swap
              move WS-Month to WS-days
              move WS-swap  to WS-Month
              move WS-Month to WS-Inv-Month
              go to zz050-test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to WS-date.  *> swap Intl to UK form
     move     WS-test-date (1:4) to WS-Year.
     move     WS-test-date (6:2) to WS-Month.
     move     WS-Month           to WS-Inv-Month
     move     WS-test-date (9:2) to WS-Days.
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
              move WS-Month to WS-days
              move WS-swap to WS-Month
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
              move WS-Month to WS-days
              move WS-swap to WS-Month
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
 Maps04       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
