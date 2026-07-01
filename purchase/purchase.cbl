       >>source free
*>
*>    Load16 may need changing for sort by custname (33) (see sales).
*>
*>
*>**************************************************
*>                                                 *
*>         Purchase  Ledger  System  Menu          *
*>                                                 *
*>**************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         purchase.
*>**
*>    Author.             V.B.Coen FBCS, FIDM, FIDPM
*>                        Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            P/L System Menu.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Calls:
*>                        Maps04
*>                        Sys002.
*>                        acas000  System Parameter file ->
*>                         systemMT  (DAL).
*>                        and all of the plnnn modules.
*>**
*>    Error messages used.
*>                        SY006
*>                        SY007
*>                        SY008
*>                        SY009.
*>                        SY010.
*>                        SY011.
*>                        SY013.
*> Module Specific.
*>**
*>   Changes.
*> 10/07/84 Vbc - Fix Display Head Positioning.
*> 25/09/84 Vbc - Support For Pl100 Using Wssys4.
*> 07/01/85 Vbc - Change Of Copyright Notice.
*> 28/04/85 Vbc - Change Of End Of Cycle Prog Name.
*> 01/04/09 vbc - Added pl190.
*> 04/04/09 vbc - Added pl165 sort before pl120 - Aged Cred Rep
*>                Clean up menu calls ie, renumbering.
*> 09/04/09 vbc - Run backup script at exit.
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 01/06/09 vbc - .08 Support for Stock & OE in Mapser
*> 04/06/09 vbc - .09 Minor display bug in menu
*> 14/09/10 vbc - .10 Added Cob Env variables presets.
*> 15/09/10 vbc - .11 mod to always use current year for (C) display.
*> 02/10/11 vbc - .12 Changed to Cbl-File-Details year to xx for OC v2.
*> 11/12/11 vbc - .13 Added support for other than UK date format
*>                    Update Env processing and pass on to all ACAS called modules
*>                    Allow being called with one/two params for working dirs that overides
*>                    ACAS_LEDGERS and ACAS_IRS in case using temp practice/test directories.
*>                    Make backup script run via ~/bin directory so needs another env var.
*>                    Updated version to 3.01.nn
*> 20/12/11 vbc - .14 Missing 'into' when creating file paths and OC didnt comment
*> 17/04/13 vbc - .15 Force Invoicer = 2 when creating system.dat
*> 19/04/13 vbc - .16 Fix Bug in get-args that bypassed code - Dummy
*> 26/04/13 vbc - .17 Included version data for system record same as in sys002.
*> 28/04/13 vbc - .18 Include test for file-8 in zz020.
*> 18/05/13 vbc - .19 Zero new fields in ws-calling-data. Used in SL070 if called by Stock.
*> 22/09/15 vbc - .20 Added support for Param-Restrict & option Z.
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*>                    Changed get-Env stuff to a copybook using common msgs.
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 16/01/17 vbc - .22 Removed dead call - maps99.
*>                    Change proc step for SL160 so no sort if RDB processing.
*>                    IS THERE OTHERS ??
*> 30/08/17 vbc - .23 Set wsnames to use default in copybook without the 'in ..'.
*> 01/09/17 vbc - .24 New code to update sys4 record or param record if
*>                    the called program could or does any changes to them.
*>                    removed the stop run after a goback - unneeded.
*>                    Chg load000 & load00 to perform/goback instead of go to.
*>                    also add after call to perform overwrite to update
*>                    any data changes in system or sys4 record data
*>                    depending on called program for load00.
*>                    Started work on removing calls to maps99 throughout
*>                    Purchase notes added per program.
*> 05/02/18 vbc - .25 Dont close file pre calling sys002 as not open!!!
*> 13/03/18 vbc -     Adjusted code base to bring it inline with all other menu programs.
*> 22/03/18 vbc - .26 Added process to allow internal params via WS-Calling-Data
*>                    WS-Args (13) to start and pass extra info to a called program
*>                    In this case running xl150 with answers to the start up
*>                    questions. (F = Forced run).
*>                    This way program can be started via crontab or better still via
*>                    Sales Ledger if end of month/beginning of new month.
*>                    xl150 End of cycle program should only be run if all reports
*>                    completed, i.e.,
*>                    Sales: Proof, Packing lists, Invoices, Value Analysis & Postings
*>                    and payments Proof and Postings.
*>                    Purchase: Proof, Purchase Orders, Value Analysis & Postings
*>                    and payments Proof and Postings, Cheques etc if required.
*>                    Force run will try to run all outstanding reports.
*> 14/04/18 vbc - .27 Remark out code for reading in rdb system data as file will
*>                    ALWAYS be up2date.
*>                    On request for system setup write out sys rec 1 to file first.
*>                    Adjust overwrite so that rdb if valid is processed
*>                    followed by the file. Doing this system wide.
*> 21/05/18 vbc - .28 Small change to the backup process at prerewrite
*>                    On menu exit do NOT display space as it forces a wait stop.
*> 28/05/18 vbc - .29 Added ws fields for env. columns and lines to verify minimums.
*> 31/05/23 vbc - .30 Added execution of pl830 first when Transactions Post selected
*>                    at para load08 - All 4 lines are currently remarked out until
*>                    the programs have been written.
*> 27/07/23 vbc - .31 Change title of menu option U to Invoice Sub-System
*>                    to standardise with SL.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/12/24 vbc       Change menu ACCEPT to use UPPER and remove the function.
*> 29.07.25 vbc   .32 Changed Menu option S, from Cheque to Payment to match
*>                    pl900.
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
 copy  "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>------------
*>
*> copy "selsys.cob".
 Data  Division.
*>=============
*>
 File Section.
*>-----------
*>
*> copy "fdsys.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(18)    value "Purchase (3.3.00)".
 77  z                   binary-short value zero.
 77  Batch-Text          pic x(28)    value spaces.
 77  Script-Name         pic x(20)    value spaces.
 77  Run-Backup          pic x(512)   value spaces.  *> size changed
 77  Full-Backup-Script  pic x(512)   value spaces.
 77  OS-Delimiter        pic x        value "/".     *> Preset for *nix
 77  ACAS_BIN            pic x(512)   value spaces.  *> added
 77  ACAS_LEDGERS        pic x(500)   value spaces.
 77  Arg-Number          pic 9        value zero.
*>========================================================
*>  in case file layout upgrade is needed.
*>   Using a file update program.
*>
 copy "sys-params-versioning.cob".
*>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*> holds program parameter values from command line
 01  Arg-Vals                         value spaces.
     03  Arg-Value       pic x(525)  occurs 2.
 01  Arg-Test            pic x(525)   value spaces.
 01  Saved-CD-Args       pic x(13).
*>
 01  Backup-Sw           pic 9     value zero.
     88  Backup-Script-Found       value 1.
 01  Linux-Backup-Script-Name   pic x(20) value "acasbkup.sh".
 01  Windows-Backup-Script-Name pic x(20) value "acasbkup.bat".
 01  OS2-Backup-Script-Name     pic x(20) value "acasbkup.cmd".
*>
 01  File-Info                          value zero.       *> Layout as per GNU v2 manual
     05 File-Size-Bytes  pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp.    *> Mod date.
     05 Mod-MO           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp.    *> Mod time
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp. *> Always 00
*>
 01  ws-data.
     03  menu-reply      pic x        value "A".
     03  op-display      pic x(7).
*>
     03  letters-upper   pic x(26)    value "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
     03  letters.
         05  a-entry     pic x          occurs  26  indexed by q.
*>
     03  ws-reply        pic x.
     03  a               pic 99         comp.
     03  wsmaps-ser.
         05  wsmaps-ser-xx pic xx.
         05  wsmaps-ser-nn pic 9(4).
*>
     03  ws-env-columns  pic 999       value zero.
     03  ws-env-lines    pic 999       value zero.
*>
 copy "wsmaps03.cob".   *> for maps04
 copy "wscall.cob".
 copy "wstime.cob".
 copy "wsfnctn.cob".
 copy "wssystem.cob".
 copy "wssys4.cob"   replacing System-Record-4 by WS-System-Record-4.
 copy "wsdflt.cob".
 copy "wsfinal.cob".
 copy "wsnames.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
*>     03  System-Record       pic x.
*>     03  Default-Record         pic x.
*>     03  Final-Record           pic x.
*>     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
     03  WS-Stock-Record        pic x.
     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-OTM5-Record         pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
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
     03  SY006           pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007           pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008           pic x(31) value "SY008 Note message & Hit return".
     03  SY009           pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 24".
     03  SY011           pic x(47) value "SY011 Error on systemMT processing, Fs-reply = ".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*> Module specific
*>
 01  error-code          pic 999    value zero.
 01  to-day              pic x(10).
*>
 01  WS-Temp-System-Rec  pic x(2048).   *> Size overkill
*>
 procedure division.
*>*****************
*>
 Purchase-Main.
*>************
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
*>
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     function current-date to wse-date-block.
*>
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              display SY010    at 0101 with erase eos
              accept  ws-reply at 0133
              goback.
     accept   ws-env-Columns from Columns.
     if       ws-Env-Columns < 80
              display SY013    at 0101 with erase eos
              accept  ws-reply at 0133
              goback.
*>
     perform  zz020-Get-Program-Args.
*>
 Open-System.                *> First get system param cobol file
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.
     if       fs-reply not = zero
 *>             perform System-close
              move    "sys002" to ws-called    *> create param file by requested info from user
              call    ws-called using ws-calling-data file-defs
              perform System-open
     end-if.
*>
 aa010-Get-System-Recs.
     move     zeros to File-System-Used         *> again in case RDB setup
                       File-Duplicates-In-Use,  *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     4 to File-Key-No.
     perform  System-Read-Indexed.        *> Read Cobol file sys totals
     move     System-Record to WS-System-Record-4.
     move     1 to File-Key-No.
     perform  System-Read-Indexed.        *> Read Cobol file params
     if       fs-reply not = zero          *> should NOT happen as done in
              perform System-close          *> open-system
              move    "sys002" to ws-called    *> create param file by requested info from user
              call    ws-called using ws-calling-data file-defs
              perform System-open
              go to aa010-Get-System-Recs
     end-if.
     move     System-Record to WS-Temp-System-Rec.   *> save in case of sys-rec-4 overwrite
*>
*> BY PASS THIS CODE AS THE FILE WILL ALWAYS BE CURRENT.
*>
*>  We now have the param file along with RDB information so -
*>  Check if RDB in use & if so, close Cobol file and open
*>   and read the RDB system-rec but if recs do not exist
*>    write using the Cobol file versions.
*>
*>     if       File-System-Used NOT = zero      *> RDB in use ( could be values 1 thru 5 but currently only 1)
*>              move     File-System-Used to Arg-Number       *> save value from param in Cobol file
*>              move     zero to File-System-Used             *> so we can close the cobol file
*>              perform  System-Close                         *>  close cobol file
*>              move     Arg-Number to File-System-Used       *> restore value from param in cobol file
*>              move     "66" to FA-RDBMS-Flat-Statuses       *> Force RDB processing
*>              move     4 to File-Key-No
*>              perform  System-Open                          *> It could be values 1 thru 5 when the other RDBs are programmed for
*>              perform  System-Read-Indexed                  *> Read in RDB table sys totals
*>              if       fs-reply = zero
*>                       move System-Record to WS-System-Record-4  *> overwrite cobol rec.
*>              end-if
*>              move     1 to File-Key-No
*>              perform  System-Read-Indexed                  *> get the record from the RDB table
*>              if       fs-reply not = zero                  *> but if error we have a problem such as someone forgot to run system load modules.
*>                       move WS-Temp-System-Rec to System-Record   *> restore saved cobol file rec
*>                       perform System-Write                 *> So create RDB row in SYSTEM-REC from the Cobol file data
*>                       if      fs-reply not = zero
*>                               display SY011    at 2301 with erase eos
*>                               display fs-reply at 2348
*>                               display SY008    at 2401
*>                               accept  ws-Reply at 2432
*>                               perform System-Close
*>                               goback
*>                       end-if
*>              end-if
*>     end-if.
     perform  System-Close.
*>
*>   Back to work as we have the RDB rec if in use otherwise the Cobol one
*>    regardless the system file/table is now closed with recs saved in WS.
*>
     move     run-date to u-bin.
     call     "maps04" using maps03-ws.
     move     u-date to to-day.
     perform  zz060-Convert-Date.
*>
     if       not B-L
              set B-L to true.
*>
     if       op-system = zero
              move "O/S" to op-display.
     if       linux   move "Linux"   To op-display
     else if  Windows move "Windows" To op-display
     else if  Mac     move "Mac"     To op-display
     else if  OS2     move "OS/2"    To op-display
     else if  unix    move "Unix"    To op-display
     else if  dos     move "Dos"     To op-display.
*>
     if       Dos or Windows
              move Windows-Backup-Script-Name to Script-Name
     else if  OS2
              move OS2-Backup-Script-Name     to Script-Name
     else if  Linux or Unix or Mac
              move Linux-Backup-Script-Name   to Script-Name.
*>
     string   ACAS_BIN     delimited by space
              OS-Delimiter delimited by size
              Script-Name  delimited by space  into Run-Backup
     end-string
     call     "CBL_CHECK_FILE_EXIST" using Run-Backup
                                           File-Info
     end-call
     if       Return-Code not = zero
*>          and Batch-Text (1:1) not = space
              move "No BackUp Script in Bin" to Batch-Text
     else
              move 1 to Backup-Sw
              string "Using "    delimited by size
                     Script-Name delimited by space into Batch-Text
     end-if
*>
*>
*> 22/03/18 New code (from stock).
*>
*> Check to see if WS-Calling-Data set to auto to run a program (st0020 or st040).
*>  A field within takes on the value of param 2 that is supplied when calling
*>   stock where param 1 must be one of the following :
*>     ACAS_LEDGERS=path   OR 'NONE' OR 'NO' OR 'NULL' (Case dont care),
*>         where param 2 must be xl150 or ? (case dont care).
*> Then next chars are, for xl150,
*>   E.g., 'xl150spx' s = Run Sales EOC, p = Run Purchase EOC.
*>                    x is y for End of Quarter or n for not EoQ.
*>
*> Here code for any others that MUST be run before.  VBC new code ??
*>
      if      WS-CD-Args (1:5) = "xl150"
              move     "xl150"    to WS-Called
              move     "purchase" to WS-Caller
              move     zeros      to WS-Term-Code
              move     spaces     to WS-Del-Link
              move     zero       to WS-Process-Func
              move     zero       to WS-Sub-Function
              perform  Load00
              go to    Pre-OverRewrite
     end-if
*>
     move     zeros to ws-Process-Func ws-Sub-Function.
     if       menu-reply = "A"            *> menu run for 1st time in run unit ONLY
              go to load01.
*>
 display-menu.
     display  usera at 0101 with erase eos foreground-color 3.
     move     to-day to u-date.
     move     "purchase" to ws-caller.
     move     spaces to ws-called ws-del-link menu-reply.
     move     zeros to ws-term-code.
     move     maps-ser-nn to curs2.
     display  maps-ser-xx at 2474 with foreground-color 3.
     display  curs2 at 2476 with foreground-color 3.
     display  "Copyright (c) 1976-" at 2401 with foreground-color 3.
     display  wse-year at 2420 with foreground-color 3.
     display  " Applewood Computers" at 2424 with foreground-color 3.
*>
 Conv-date.
*>
*> Convert from UK to selected form
*>
     if       Date-Form not > zero and < 4
              move 1 to Date-Form.
     if       Date-USA
              move u-date to ws-date
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              move ws-date to u-date
     end-if
     if       Date-Intl
              move "ccyy/mm/dd" to ws-date   *> swap Intl to UK form
              move u-date (7:4) to ws-Intl-Year
              move u-date (4:2) to ws-Intl-Month
              move u-date (1:2) to ws-Intl-Days
              move ws-date to u-date
     end-if.
*>
 conv-date-end.
     display  u-date at 0171 with foreground-color 3.
*>
 display-go.
*>
     display  prog-name at 0301 with foreground-color 2.
     display  "Purchase Ledger System Menu" at 0326 with foreground-color 2.
*>
     accept   wsb-time from time.
     if       wsb-time not = "00000000"
              move wsb-hh to wsd-hh
              move wsb-mm to wsd-mm
              move wsb-ss to wsd-ss
              display "at "    at 0355 with foreground-color 2
              display wsd-time at 0358 with foreground-color 2.
*>
     accept   wsa-date from date.
     if       wsa-date not = "000000"
              move wsa-yy to u-year
              move wsa-mm to u-month
              move wsa-dd to u-days
              display "on " at 0367 with foreground-color 2
              perform conv-date
              display u-date at 0370 with foreground-color 2.
*>
     display  "Select one of the following by letter  :- [ ]" at 0601 with foreground-color 2.
*>
     display  "(A)  Date Entry"                   at 1004 with foreground-color 2.
     display  "(B)  Supplier File Maintenance"    at 1104 with foreground-color 2.
     display  "(C)  Purchase Ledger Enquiry"      at 1204 with foreground-color 2.
     display  "(D)  Purchase Transactions Input"  at 1304 with foreground-color 2.
     display  "(E)  Purchase Transactions Amend"  at 1404 with foreground-color 2.
     display  "(F)  Purchase Transactions Delete" at 1504 with foreground-color 2.
     display  "(G)  Purchase Transactions Proof"  at 1604 with foreground-color 2.
     display  "(H)  Purchase Transactions Post"   at 1704 with foreground-color 2.
     display  "(I)  Payment Input"                at 1804 with foreground-color 2.
     display  "(J)  Payment Amend"                at 1904 with foreground-color 2.
     display  "(K)  Payment Proof"                at 2004 with foreground-color 2.
     display  "(L)  Payment Post"                 at 2104 with foreground-color 2.
     display  "(M)  Set-Up Purchase Analysis Codes" at 2204 with foreground-color 2.
     display  "(N)  Purchase Analysis Report"     at 1044 with foreground-color 2.
     display  "(O)  Purchase Day Book"            at 1144 with foreground-color 2.
     display  "(P)  Aged Creditors Report"        at 1244 with foreground-color 2.
     display  "(Q)  Alphabetical Supplier List"   at 1344 with foreground-color 2.
     display  "(R)  Supplier Turnover Report"     at 1444 with foreground-color 2.
     display  "(S)  Payments System"              at 1544 with foreground-color 2.
     display  "(T)  End Of Cycle Processing"      at 1644 with foreground-color 2.
     display  "(U)  Transaction Sub-System"       at 1744 with foreground-color 2.
     display  "(V)  Supplier File Dump"           at 1844 with foreground-color 2.
     display  "(X)  Exit to "                     at 1944 with foreground-color 2.
     display  op-display                          at 1957 with foreground-color 2.
     display  batch-text                          at 2049 with foreground-color 2.
*>     display  "(Y)  File Fix Up"                at 2144 with foreground-color 2.
     if       Param-Restrict not = "Y"
              display  "(Z)  System Set Up"       at 2244 with foreground-color 2.
*>
 accept-loop.
*>
     accept   menu-reply at 0644 with foreground-color 6 auto UPPER.
*>
     if       menu-reply = "X"
              go to pre-overrewrite.
*>
     if       menu-reply = "Z" and
              Param-Restrict = "Y"
              display  "Not permitted" at 2331 with foreground-color 2
              go to display-menu.
*>
     move     zero to z.
     move     letters-upper  to  letters.
     set      q  to  1.
     search   a-entry
              when  a-entry (q) = menu-reply
              set z to q.
     if       z = zero
              go to accept-loop.
     go       to load-it.
*>
 call-system-setup.
*>*****************
*>
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     zero to ws-term-code.
     move     1 to File-Key-No.
     perform  System-Open.
     perform  System-Rewrite.                           *> in case of any changes
     move     4 to File-Key-No.
     move     WS-System-Record-4 to System-Record.
     perform  System-Rewrite.         *> In case of any changes
     perform  System-Close.
     move     "sys002" to ws-called.
     call     ws-called using ws-calling-data file-defs.
     if       ws-term-code > 7
              stop run.
     go       to Open-System.
*>
 pre-overrewrite.
     if       not Backup-Script-Found
              go to overrewrite.
*>
     if       Linux or Unix or Mac
              string "nohup " delimited by size
                      Run-Backup delimited by space
                    " 0</dev/null &>/dev/null &" delimited by size into Full-Backup-Script
              end-string
     else
      if      Dos or Windows
              move Script-Name to Full-Backup-Script
      else
       if     OS2
              move Script-Name to Full-Backup-Script.
     perform  overrewrite.
     call     "SYSTEM" using Full-Backup-Script.
     goback.
*>
 overrewrite.                                    *> save to RDB or file.
     if       File-System-Used NOT = zero        *> Force RDB processing
              move     "66" to FA-RDBMS-Flat-Statuses
              move     1 to File-Key-No
              perform  System-Open
              move     1 to File-Key-No
              move     System-Record to WS-Temp-System-Rec
              perform  System-Rewrite            *> In case of any changes
              move     4 to File-Key-No
              move     WS-System-Record-4 to System-Record
              perform  System-Rewrite            *> In case of any changes
              perform  System-Close
              move     WS-Temp-System-Rec to System-Record
     end-if.
*>
*> Now do the same for the Cobol file.
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open.                       *> Open cobol file params as I/O
     move     1 to File-Key-No.
     move     System-Record to WS-Temp-System-Rec
     perform  System-Rewrite.                    *> Update Cobol file params
     move     4 to File-Key-No.
     move     WS-System-Record-4 to System-Record.
     perform  System-rewrite.                    *> Update Cobol file sys totals
     move     WS-Temp-System-Rec to System-Record
     perform  System-Close.                      *> Close the Cobol param file.
*>
 overclose.
     goback.
*>
 load-it.
*>*******
*>
     move     space to menu-reply.
     go       to load01 load02 load03 load04 load05 load06 load07
                 load08 load09 load10 load11 load12 load13 load14
                 load15 load16 load17 load18 load19 load20 load21
                 load22 loader loader loadsr call-system-setup
              depending on z.
*>
 loader.
*>-------
*>
     go       to display-menu.
*>
 load00.
*>------
*>
     move     zero to ws-term-code.
     call     ws-called using ws-calling-data
                              system-record
                              to-day
                              file-defs
     end-call
     if       ws-term-code < 8
        and   (ws-called = "pl000" or "pl020" or "pl030" or "pl080" or "pl085"
                        or "pl090" or "pl090" or "pl100" or "pl115" or "pl180"
                        or "pl190")
              perform overrewrite.     *> Update sys4 and system recs in case of changes.
     if       ws-term-code > 7      *> Got a serious (reported) error
              go to overrewrite.
*>
 load00-exit.
*>
     go       to display-menu.
*>
 load000.
*>------
*>
     move     zero to ws-term-code.
     call     ws-called using ws-calling-data
                              system-record
                              WS-system-record-4
                              to-day
                              file-defs
     end-call
     if       ws-term-code < 8  *> for pl055 & 060, xl150
              perform overrewrite.    *> Update sys4 and system recs in case of changes.
     if       ws-term-code > 7      *> Got a serious (reported) error
              go to overrewrite.
*>
 load000-exit.
*>
     go       to display-menu.
*>
 load01.
*>------
*>
     move     "pl000" to ws-called.
     go       to load00.
*>
 load02.
*>------
*>
     move     "pl010" to ws-called.
     go       to load00.
*>
 load03.
*>-------
*>
     move     "pl015" to ws-called.
     go       to load00.
*>
 load04.
*>------
*>
     move     "pl020" to ws-called.
     go       to load00.
*>
 load05.
*>------
*>
     move     "pl030" to ws-called.
     go       to load00.
*>
 load06.
*>------
*>
     move     "pl040" to ws-called.
     go       to load00.
*>
 load07.
*>------
*>
     move     "pl050" to ws-called.
     go       to load00.
*>
 load08.
*>------
*>
 *>    move     "pl830" to WS-Called.   *> In case autogen is use
 *>    perform  load000.
 *>    if       ws-term-code not = zero
 *>             go to display-menu.
     move     "pl055" to ws-called.
     perform  load000.
     move     "pl060" to ws-called.
     go       to load000.
*>
 load09.   *> Pay enter
*>------
*>
     move     "pl080" to ws-called.
     go       to load00.
*>
 load10.   *> pay Amend
*>------
*>
     move     "pl085" to ws-called.
     go       to load00.
*>
 load11.
*>------
*>
     if       FS-Cobol-Files-Used    *> well use fn-Read-By-Batch (32)
              move     "pl090" to ws-called
              perform  load00
     end-if
     move     "pl095" to ws-called.
     go       to load00.
*>
 load12.
*>------
*>
     move     "pl100" to ws-called.
     go       to load000.
*>
 load13.
*>------
*>
     move     "pl070" to ws-called.
     go       to load00.
*>
 load14.
*>------
*>
     move     "pl130" to ws-called.
     go       to load00.
*>
 load15.
*>------
*>
     move     "pl140" to ws-called.
     go       to load00.
*>
 load16.
*>------
*>
*>  THIS MAY NEED changing when using RDB call by custname etc. (33)
*>
     move     zero to error-code.
     move     "pl165" to ws-called.        *> Purchase name sort
     perform  load00.
     move     "Y" to oi-5-flag.
     move     "pl115" to ws-called.        *> OTM5 sort
     perform  load00.
     if       error-code = zero
              move  "pl120" to ws-called   *> Aged anal report
              go  to load000.
     go       to display-menu.
*>
 load17.
*>------
*>
     if       FS-Cobol-Files-Used    *> well use fn-Read-By-Name (31)
              move  "pl165" to ws-called   *> purch file name sort
              perform load00
     end-if
     move     "pl160" to ws-called.
     go       to load00.
*>
 load18.
*>------
*>
     move     "pl170" to ws-called.
     go       to load00.
*>
 load19.
*>------
*>
     move     "pl900" to ws-called.
     go       to load00.
*>
 load20.
*>------
*>
     if       ws-term-code = 3
              go to load20a.
*>
     move     "pl140" to ws-called.
     perform  load00.
*>
 load20a.
*>
     move     "xl150" to ws-called.
     perform  load000.
     if       ws-term-code = 2 or 3
              go to display-menu.
     if       ws-term-code = 1
              move "pl130" to ws-called
              perform load00
              move zero to ws-term-code
              go to load20a.
*>
     go       to display-menu.
*>
 load21.
*>------
*>
     move     "pl180" to ws-called.
     go       to load00.
*>
 load22.
*>------
*>
     move     "pl190" to ws-called.
     go       to load00.
*>
 loadsr.
*>------
*>
     display  "Sorry not available" at 2331 with foreground-color 2.
     go       to accept-loop.
*>
 main-exit.
     goback.
*>
 copy "Proc-Get-Env-Set-Files.cob".
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
