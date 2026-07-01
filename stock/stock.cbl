       >>source free
*>********************************************
*>                                           *
*>       Stock Control System  Menu          *
*>                                           *
*>********************************************
*>
 identification          division.
*>================================
*>
*>**
     program-id.         stock.
*>**
*>   Author.             V.B.Coen FBCS.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2009 - 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Remarks.            Stock System Menu.
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     maps01 - Encrypt/Decrypt (OpenSource version ONLY).
*>                       maps04 - Date testing and conversion.
*>                       acas000 ->  System Parameter FH
*>                        systemMT DAL.
*>**
*>   Error messages used.
*> System Wide
*>                       SY006.
*>                       SY007.
*>                       SY008.
*>                       SY009.
*>                       SY010.
*>                       SY011.
*>                       SY012.        *>  In proc-Get-Env-Set-files-cob
*>                       SY013.
*> Module Specific
*>                       ST403.    (From st040 via autorun).
*>**
*>   Changes.
*> 22/04/09 vbc - Rewritten in Cobol from scratch but skipped some of the weird stuff.
*> 01/06/09 vbc - Updated Stock info to Purchase, Sales, General & sys002.
*> 12/06/09 vbc - .05 Cosmetic Menu screen clean up.
*> 18/06/09 vbc - .06 Add st030 to menu
*> 06/08/10 vbc - .07 Force set env variables for Esc and other keys + other cosmetics.
*> 15/09/10 vbc - .09 mod to always use current year for (C) display.
*> 02/10/11 vbc - .10 Changed to Cbl-File-Details year to xx for OC v2.
*> 27/11/11 vbc - .11 Update Env processing and pass on to all ACAS called modules
*>                    Allow being called with one/two params for working dirs that overides
*>                    ACAS_LEDGERS and ACAS_IRS in case using temp practice/test directories.
*>                    Make backup script run via ~/bin directory so needs another env var (ACAS_BIN).
*> 11/12/11 vbc -     Changed version from 1.00.xx to 3.01.xx, in keeping with the rest of ACAS
*>                .12 Changed usage of Date-Form to the global field Date-Form making former redundent.
*> 20/12/11 vbc - .13 Missing 'into' when creating file paths and OC didnt comment
*> 17/04/13 vbc - .14 Force Invoicer = 2 when creating system.dat
*> 19/04/13 vbc - .15 Fix Bug in get-args that bypassed code - Dummy
*> 26/04/13 vbc - .16 Included version data for system record same as in sys002.
*> 12/05/13 vbc - .17 Changed wsnames to in common as pl010 called in st010.
*> 16/05/13 vbc - .18 Changed wsnames to in copybook see above.
*> 11/06/13 vbc - .19 Hidden ST060 import stock file data from menu
*>                    IF it is to be used must be unremarked out and compiled etc
*>                    and MODIFIED to match imported file specifications.
*> 22/09/15 vbc - .20 Added support for Param-Restrict & option Z.
*> 02/07/16 vbc - .21 Missed ST009 msg in 'Error messages used'.
*> 26/07/16 vbc -     Version Updated for RDB processing to match rest of stock system
*> 23/10/16 vbc - .22 Added system file/table access as now written.
*> 24/10/16 vbc - .23 ALL programs now using wsnames.cob in copybooks
*>                    When using RDB will also update the Cobol system file record
*>                    as that file and record will ALWAYS be present.
*>                    Changed get-Env stuff to a copybook using common msgs.
*> 29/10/16 vbc - .24 Clean up mapser proc as its a copy proc.Added more msgs.
*>                    Changed usage of Cbl-File-Details to File-Info (see .10)
*>                    Remove file-status checks for file exists code.
*>                    All updates made to active file system RDB or Cobol file not both
*>                    as when RDB in use the Cobol record only needed for basic RDB data.
*>                    Usage of maps99 redacted.
*> 24/10/16 vbc -     ALL programs now using wsnames.cob in copybooks.
*> 13/01/18 vbc - .25 Version now 3.02.
*> 05/02/18 vbc - .26 Dont close file pre calling sys002 as not open!!!
*> 12/03/18 vbc - .27 Removed msg SY010 not used, removed unused sys4, dflt and final
*>                    defs, added std ACAS Dummies-4 and acasnnn copylib renaming
*>                    acas000-open etc to comply with rest of ACAS (System-Open etc).
*> 13/03/18 vbc -     Adjusted code base to bring it inline with all other menu programs.
*> 14/03/18 vbc - .28 Added process to allow internal params via WS-Calling-Data
*>                    WS-Args (13) to start and pass extra info to a called program
*>                    In this case running st020 or st040 with answers to the start up
*>                    questions.
*>                    This way program can be started via crontab or better still via
*>                    Sales Ledger if end of month/beginning of new month.
*>                    Now need to make sure that the totals are being updated in SL
*>                    including invoice create, amend, delete.
*>                    Before running st040 must run st020 if audit report not done
*>                    {Stk-Activity-Rep-Run = zero}.
*>                    Added error msg SY012.
*> 19/03/18 vbc - .29 Added msg st403 when running in autorun mode for st040.
*> 14/04/18 vbc - .30 Remark out code for reading in rdb system data as file will
*>                    ALWAYS be up2date.
*>                    On request for system setup write out sys rec 1 to file
*>                    first & clean up overwrite. Doing this system wide.
*> 21/05/18 vbc - .31 Small change to the backup process at prerewrite
*>                    On menu exit do NOT display space as it forces a wait stop.
*> 28/05/18 vbc - .32 Added ws fields for env. columns and lines to verify minimums.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/12/24 vbc       Change menu ACCEPT to use UPPER and remove the function.
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
*>===============================
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
 *> copy "selsys.cob".
 data  division.
*>=============
*>
 file section.
*>-----------
*>
 *> copy "fdsys.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(17)    value "Stock (3.3.00)".
 77  z                   binary-short value zero.
 77  Batch-Text          pic x(28)    value spaces.
 77  Script-Name         pic x(20)    value spaces.
 77  Run-Backup          pic x(512)   value spaces.  *> size changed
 77  Full-Backup-Script  pic x(512)   value spaces.
 77  OS-Delimiter        pic x        value "/".
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
     03  Arg-Value       pic x(525)  occurs 6.
 01  Arg-Test            pic x(525)   value spaces.
 01  Saved-CD-Args       pic x(13).
*>
 01  Backup-Sw           pic 9               value zero.
     88  Backup-Script-Found                 value 1.
 01  Linux-Backup-Script-Name   pic x(20)    value "acasbkup.sh         ".
 01  Windows-Backup-Script-Name pic x(20)    value "acasbkup.bat        ".
 01  OS2-Backup-Script-Name     pic x(20)    value "acasbkup.cmd        ".
*>
 01  File-Info                          value zero.       *> Layout as per GNU v2 manual
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
     03  menu-reply      pic x          value "A".
     03  op-display      pic x(7).
*>
     03  letters-upper   pic x(26)      value "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
     03  letters.
         05  a-entry     pic x        occurs 26 indexed by q.
*>
     03  ws-reply        pic x.
     03  a               pic 99        comp.
     03  wsmaps-ser.
         05  wsmaps-ser-xx pic xx.
         05  wsmaps-ser-nn pic 9(4).
*>
     03  ws-env-columns  pic 999       value zero.
     03  ws-env-lines    pic 999       value zero.
*>
 01  ws-date-formats.
     03  ws-swap             pic xx.
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
 copy "wsmaps01.cob".
 copy "wsmaps03.cob".
 copy "wscall.cob".
 copy "wstime.cob".
 copy "wsfnctn.cob".
 copy "wsnames.cob".
 copy "wssystem.cob".
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
     03  WS-Stock-Record        pic x.
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
     03  SY006          pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY010          pic x(46) value "SY010 Terminal program not set to length => 24".
     03  SY011          pic x(47) value "SY011 Error on systemMT processing, Fs-reply = ".
     03  SY012          pic x(34) value "SY012 Do not know that extra param".
     03  SY013          pic x(47) value "SY013 Terminal program not set to Columns => 80".
*> Module specific (from st040)
     03  ST403          pic x(27) value "ST403 Sub arg not 1, 2 or 3".
*>
 01  to-day             pic x(10).
*>
 01  WS-Temp-System-Rec  pic x(2048).   *> Size overkill
*>
 procedure division.
*>=================
*>
 aa000-General-Control  Section.
*>*****************************
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
     perform  zz020-Get-Program-Args.     *>  all in copybook Proc-ACAS-FH-Calls.cob
*>
 aa005-Open-System.                              *> First get system param cobol file
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.
     if       fs-reply not = zero
 *>             perform System-Close
              move    "sys002" to ws-called      *> create param file by requested info from user
              call    ws-called using ws-calling-data file-defs
              perform System-Open
     end-if.
*>
 aa010-Get-System-Recs.
     move     zeros to File-System-Used          *> again in case RDB setup
                       File-Duplicates-In-Use.   *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Read-Indexed.               *> Read Cobol file
     if       fs-reply not = zero                *> should NOT happen
              perform System-Close
              move    "sys002" to ws-called    *> create param file by requested info from user
              call    ws-called using ws-calling-data file-defs
              perform System-Open
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
*>              move     1 to File-Key-No
*>              perform  System-Open                          *> It could be values 1 thru 5 when the other RDBs are programmed for
*>              perform  System-Read-Indexed                  *> get the record from the RDB table
*>              if       fs-reply not = zero                  *> but if error we have a problem such as someone forgot to run system load modules.
*>                       move WS-Temp-System-Rec to System-Record   *> restore saved cobol file rec
*>                       perform System-Write                 *> So create RDB row in SYSTEM-REC from the Cobol file data
*>                       if      fs-reply not = zero
*>                               display SY011 at 2301 with erase eos
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
*> Check if Analysis file exists and heopfully some anal codes within.
*>  If not, run program to create the defaults one's.
*>
     call     "CBL_CHECK_FILE_EXIST" using File-15      *> Analysis
                                           File-Info.
     if       return-code not = zero                        *> not = zero - No file found
              move 1 to ws-Process-Func
              call "sl070" using ws-calling-data system-record to-day file-defs
     end-if
*>
     move     run-date to u-bin.
     call     "maps04" using maps03-ws.
     move     u-date to to-day.
     perform  zz060-Convert-Date.
*>
     if       not Stock
              set Stock to true.
*>
     if       op-system = zero
              move "O/S" to op-display.
     if       Linux    move "Linux"   to op-display
     else if  Windows  move "Windows" to op-display
     else if  Mac      move "Mac"     to op-display
     else if  OS2      move "OS/2"    to op-display
     else if  Unix     move "Unix"    to op-display
     else if  Dos      move "Dos"     to op-display.
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
*> 14/03/18 New code.
*>
*> Check to see if WS-Calling-Data set to auto to run a program (st0020 or st040).
*>  A field within takes on the value of param 2 that is supplied when calling
*>   stock where param 1 must be one of the following :
*>     ACAS_LEDGERS=path   OR 'NONE' OR 'NO' OR 'NULL' (Case dont care),
*>         where param 2 must be st020 or st040 (case dont care).
*> Then next chars are, for st040, 5n (n=1,2,3) = menu function 5 option 1, 2 or 3.
*>    ditto             for st020,
*>  But check if audit reports has been run if not, do so.
*>
     if       WS-CD-Args (1:5) = "st040"
       if     WS-CD-Args (7:1) < 1 or > 3           *> (6:1) dont care but should be 1.
              display st403  at 0101 with erase eos
              go to  aa070-Pre-OverRewrite.
*>
     if       WS-CD-Args (1:5) = "st020" or "st040"
      if      Stk-Activity-Rep-Run = zero           *> Process audit reports 1st
        and   Stk-Audit-Used = 1                    *> if not run and Audit is used
              move     WS-CD-Args  to Saved-CD-Args             *> save them for 040
              move     spaces  to WS-CD-Args
              move     "st020" to WS-CD-Args (1:5)
              move     "stock" to WS-Caller
              move     zeros   to WS-Term-Code
              move     spaces  to WS-Del-Link
              move     5       to WS-Process-Func   *> Audit report only
              move     zero    to WS-Sub-Function   *> doesnt matter as char 6,7 in CD-ARGS has it
              perform  Load00
              if       ws-term-code > 7
                       go to aa070-Pre-OverRewrite  *> save current param record & abort
              end-if
              move     Saved-CD-Args to WS-CD-Args  *> restore originals
      end-if
     end-if
     if       WS-CD-Args (1:5) = "st040"
              move     "st040" to WS-Called
              move     "stock" to WS-Caller
              move     zeros   to WS-Term-Code
              move     spaces  to WS-Del-Link
              move     zero    to WS-Process-Func
              move     zero    to WS-Sub-Function   *> doesnt matter as char 6,7 in CD-ARGS has it
              perform  Load00
              go to    aa070-Pre-OverRewrite
     end-if
*>
     move     zeros to ws-Process-Func ws-Sub-Function.
     if       menu-reply = "A"
              go to load01.
*>
 aa030-display-menu.
     display  usera at 0101 with erase eos foreground-color 3.
     move     to-day to u-date.
     move     "stock" to ws-caller.
     move     spaces to ws-called ws-del-link menu-reply.
     move     zeros to ws-term-code.
     move     maps-ser-nn to curs2.
     display  maps-ser-xx at 2474 with foreground-color 3.
     display  curs2 at 2476 with foreground-color 3.
     display  "Copyright (c) 1976-" at 2401 with foreground-color 3.
     display  wse-year at 2420 with foreground-color 3.
     display  " Applewood Computers" at 2424 with foreground-color 3.
*>
 aa035-Conv-Date.
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
 aa035-Conv-Date-End.
     display  u-date at 0171 with foreground-color 3.
*>
 aa040-Display-Go.
*>
     display  prog-name at 0301 with foreground-color 2.
     display  "Stock Control System Menu"    at 0328 with foreground-color 2.
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
              perform aa035-Conv-Date
              display u-date at 0370 with foreground-color 2.
*>
     display  "Select one of the following by letter  :- [ ]" at 0601 with foreground-color 2.
*>
     display  "(A)  Date Entry"                  at 1004 with foreground-color 2.
     display  "(B)  Stock Item Maintenance"      at 1104 with foreground-color 2.
     display  "(C)  Stock Movements"             at 1204 with foreground-color 2.
     display  "(D)  Reports"                     at 1044 with foreground-color 2.
     display  "(E)  End of Cycle Processing"     at 1144 with foreground-color 2.
     display  "(F)  *Stock File Import"          at 1244 with foreground-color 2.
     display  "(X)  Exit to "                    at 1304 with foreground-color 2.
     display  op-display                         at 1317 with foreground-color 2.
     display  Batch-Text                         at 1345 with foreground-color 2.
     display  "(Y)  Stock File Compression"      at 1404 with foreground-color 2.
     if       Param-Restrict not = "Y"
              display  "(Z)  System Set Up"      at 1444 with foreground-color 2.

*>
 aa050-Accept-Loop.
     accept   menu-reply at 0644  with foreground-color 6 auto UPPER.
*>
     if       menu-reply = "X"
              go to aa070-Pre-OverRewrite.
*>
     if       menu-reply = "Z" and
              Param-Restrict = "Y"
              display  "Not permitted" at 2331 with foreground-color 2
              go to aa030-display-menu.
*>
     move     zero to z.
     move     letters-upper to letters.
     set      q  to  1.
     search   a-entry
              when a-entry (q) = menu-reply
              set z to q.
     if       z = zero
              go to aa050-Accept-Loop.
     go       to aa090-Load-It.
*>
 aa060-Call-System-Setup.                                *>  Cobol or RDB closed
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     zero to ws-term-code.
     move     1 to File-Key-No.
     perform  System-Open.
     perform  System-Rewrite.                           *> in case of any changes
     perform  System-Close.
*>
     move     "sys002" to ws-called.
     call     ws-called using ws-calling-data file-defs.
     if       ws-term-code > 7                           *> sys002 only terminates with 0
              stop run.
     go       to aa005-Open-System.
*>
 aa070-Pre-OverRewrite.                                  *> Exit requested
 *>
 *> ST020 can update Stk-Audit-No.
 *>
     move     1 to File-Key-No.
     if       File-System-Used NOT = zero   *> Force RDB processing
              move     "66" to FA-RDBMS-Flat-Statuses
              perform  System-Open
              perform  System-Rewrite
              perform  System-Close
     end-if
*>
*> Now Force File processing to keep both same.
*>
     move     "00" to FA-RDBMS-Flat-Statuses
     perform  System-Open
     perform  System-Rewrite
     perform  System-Close
*>
     if       not Backup-Script-Found
              goback.
*>
     if       Linux or Unix or Mac
              string "nohup " delimited by size
                      Run-Backup delimited by space
                    " 0</dev/null &>/dev/null &" delimited by size     into Full-Backup-Script
              end-string
     else
      if      Dos or Windows                             *> whats the correct string to add
              move Script-Name to Full-Backup-Script
      else
       if     OS2                                        *> whats the correct string to add
              move Script-Name to Full-Backup-Script.
     call     "SYSTEM" using Full-Backup-Script.
     goback.
*>
 aa090-Load-It.
     move     space to menu-reply.
     go       to load01 load02 load03 load04 load05 load06 loader
                 loader loader loader loader loader loader loader
                 loader loader loader loader loader loader loader
                 loader loader aa070-Pre-OverRewrite load25 aa060-Call-System-Setup
              depending on z.
*>
 loader.
     go       to aa030-display-menu.
*>
 load00.
     move     zero to ws-term-code.
     call     ws-called using ws-calling-data
                              system-record
                              to-day
                              file-defs.
 Load00-No-Jump.
     if       ws-term-code > 7
              go to aa070-Pre-OverRewrite.
*>
 load00-exit.
     go       to aa030-display-menu.
*>
 load01.
     move     "st000" to ws-called.
     go       to load00.
*>
 load02.
     move     "st010" to ws-called.
     go       to load00.
*>
 load03.
     move     "st020" to ws-called.
     go       to load00.
*>
 load04.
     move     "st030" to ws-called.
     go       to load00.
*>
 load05.
     move     "st040" to ws-called.
     go       to load00.
*>
 load06.
     move     "st060" to ws-called.
     go       to load00.
*>
 load25.
     move     "st050" to ws-called.
     go       to load00.
*>
 loadsr.
     display  "Sorry not available - Requests to ACAS support" at 2327 with foreground-color 2.
     go       to aa050-Accept-Loop.
*>
 aa999-exit.
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
