       >>source free
*>***************************************************
*>                                                  *
*>         General - Ledger  System  Menu           *
*>--------------------------------------------------*
*>  NO Final Accounts or Garbage collector          *
*>   gl040, gl130           gl190
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^          *
*>  This sub system has yet to be retested since    *
*>  migration to GC, also the archiving & spooling  *
*>  functions need a good cleanup as they are not   *
*>  necessarily fit for purpose on Linux systems.   *
*>
*> Improved but needs more work - not sure that the *
*>  archiving system is needed other than for gl120 *
*>                                                  *
*>  SHOULD WE RETAIN THE POSTINGS BUT WITH CUTOFF   *
*>     DATE INFO IN PARAM FILE etc ?? or sim to IRS *
*>                                                  *
*>   Worried that this is taken from an old source  *
*>      version of the GL system.                   *
*>    IF SO WHERE IS IT?????                        *
*>                                                  *
*>    Manual needs a rewrite as cannot find the     *
*>     original in a useable condition.             *
*>       WORDSTAR and tex.                          *
*>                                                  *
*> In the meanwhile the Incomplete Records System   *
*>  (IRS) has been tested against the other         *
*>  elements of the ACAS system.                    *
*>***************************************************
*>
 identification          division.
*>================================
*>
      program-id.       general.
*>**
*>    Author.           GL was written by Simon Whine MBCS, on behalf of
*>                      Applewood Computers and its group of Companies.
*>                      All changes/migrations by:
*>                      Vincent B. Coen FBCS, FIDM, FIDPM.
*>
*>                      Written to supplement IRS to support larger numbers for
*>                      accounts to 10 digits nominal and subnominals and money
*>                      amounts to 100M - 1 for customers requiring a
*>                      comparable? but cheaper product than Oracle financials.
*>                      Reduced down some point later in time for accnts 6
*>                      digits and reduced money amounts.
*>**
*>    Security.         Copyright (C) 1976-2026 & later Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          G/L System Menu.
*>                      GL is based in part from irs that pre-dates it in that it
*>                      uses default accounting to prevent out of balance
*>                      accounts using similar / same code.
*>
*>                      However after that, GL moves away from IRS because of
*>                      support of Multiple Profit Centres or Branch accounting.
*>                      This support make G/L more complex in design and
*>                      therefore to use. design in part based on two older
*>                      system in use from the 70s.
*>                      It requires an accountancy background to design the CoA
*>                      for the user company so that all processing and printed
*>                      reports behave & look correct as required by the user.
*>
*>                      This will require extensive testing of the CoA to ensure
*>                      that the results come out as needed.
*>
*>                      For usage of a General / Nominal Ledger system that does
*>                      not require MPC or Branch support it is recommended to
*>                      use the IRS system instead, although both can be used at
*>                      the same time as the other systems, Sales, Purchase,
*>                      Stock etc will issue posting to both, one or other at the
*>                      same time providing that the account numbers match each
*>                      other as set up in the system parameter file where such
*>                      posting are sent to. Might be easier said than done.
*>
*>                      Another primary issue is the way GL handles the postings
*>                      and the postings records - As is SL060 & 100 and PL060
*>                      and PL100 will post transactions of SL invoices and
*>                      payments and PL tranactions and payments to IRS and/or
*>                      GL and while for IRS they go into a different file which
*>                      is posted via an IRS menu option to the IRS posting
*>                      record and updates the Nominal accounts at the same time
*>                      IRS also has a process that will clear down all account
*>                      totals and using the posting records repost to the
*>                      accounts.   GL does NOT have this facility and it needs
*>                      to be examined if sending of posting data to its posting
*>                      file directly is the correct waay of doing this process.
*>
*>                      I suspect it is not as GL may well work same as IRS in
*>                      processing new posting entries both to the posting file
*>                      AND the nominal ledger accounts which would get broken
*>                      if SL and PL sends this data to this file and not a
*>                      secondary file that gets read and the GL postings and NL
*>                      updated.   Date 5 October Vincent Coen.
*>
*>                      IF this needs to be changed then SL060,100, PL060,100
*>                      will needs changes in BL-Write routines and possibly
*>                      others in that block of code.
*>**
*>    Version.          See prog-name & date-comped in ws.
*>
*>    Called Modules.
*>                      maps04. (Replaces 3)
*>                      Sys002.
*>                      acas000  System Parameter file ->
*>                       systemMT  (DAL).
*>                      and all of the glnnn modules.
*>**
*>    Error messages used.
*> System Wide
*>                      SY006
*>                      SY007
*>                      SY008
*>                      SY009.
*>                      SY010.
*>                      SY011.
*>                      SY013.
*> Module Wide
*>                      GL005
*>****
*>    Changes.
*> 27/01/09 vbc - Migration to Open Cobol for v2.53 -> v3.00.0.
*>                Encrypt/Decrypt & security encoding removed for Open source versions.
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 01/06/09 vbc - Support for Stock & OE in Mapser, removed Payroll, O/E.
*> 14/09/10 vbc - Added Cob Env variables presets.
*> 02/10/11 vbc - .06 Added from acas ledgers to test for ACAS environment vars
*>                    but left commented out as not sure its needed.
*> 18/12/11 vbc - .07 Force set env variables for Esc and other keys + other cosmetics.
*>                    mod to always use current year for (C) display.
*>                    Changed to Cbl-File-Details year to xx for OC v2.
*>                    Update Env processing and pass on to all ACAS called modules
*>                    Allow being called with one/two params for working dirs that overides
*>                    ACAS_LEDGERS and ACAS_IRS in case using temp practice/test directories.
*>                    Make backup script run via ~/bin directory so needs another env var (ACAS_BIN).
*>                    Maintain version 3.00.xx until some testing has been completed
*> 24/02/12 vbc - .08 After running gl020 (defaults) save system file and reload it.
*> 17/04/13 vbc - .09 Force Invoicer = 2 when creating system.dat
*> 19/04/13 vbc - .10 Fix Bug in get-args that bypassed code - Dummy
*> 26/04/13 vbc - .11 Included version data for system record same as in sys002 & force Date entry on 1st starting
*>                    and started work system wide to use rdbms instead of or addition to, cobol flat files
*>                    and replace all batch type processing on G/L similar to IRS.
*> 22/09/15 vbc - .12 Added support for Param-Restrict & option Z.
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 27/10/16 vbc - .13 added extra in set-paths to stop dup path set up.
*>                    Changed get-Env stuff to a copybook using common msgs.
*> 13/01/18 vbc - .14 Updated for v3.02 & FH & DALs. No FH/DAL changes done.
*>                    Replaced usage of maps99 for displays.
*>                    Removed encrypted password code for O/S versions.
*>                    Cleaned up start of processing to match sales, purchase etc.
*>                    Like wise at end of processing for overwrite etc.
*>                    Removed refs to ACAS_IRS, error-code, maps01 and dead messages GLnnn.
*>                    Added read and rewrite default-record at start/end.
*> 29/01/18 vbc - .15 Added remd out hooks for misssing gl040, 130 & 190
*>                    must do these after initial testing.
*> 05/02/18 vbc - .16 Dont close file pre calling sys002 as not open!!!
*> 13/03/18 vbc -     Adjusted code base to bring it inline with all other menu programs.
*> 14/04/18 vbc - .17 Remark out code for reading in rdb system data as file will ALWAYS
*>                    be up2date. On request for system setup write out sys rec 1,2 & 4
*>                    to file first. Adjust overwrite so that rdb if valid is processed
*>                    followed by the file. Doing this system wide.
*> 21/05/18 vbc - .18 Small changes to the backup process at prerewrite as did not run.
*> 23/05/18 vbc - .19 Backup bug found on quit wrong branch to overrewrite
*>                     should have been pre-overrewrite.
*>                    On menu exit do NOT display space as it forces a wait stop.
*> 28/05/18 vbc - .20 Added ws fields for env. columns and lines to verify minimums.
*>                    Should do this for all other system menu programs. <<<<<<<
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/12/24 vbc       Change menu ACCEPT to use UPPER and remove the function.
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
 77  prog-name           pic x(17)    value "General (3.3.00)".
 77  z                   binary-short value zero.
 77  s1x                 pic x        value space.
 77  Batch-Text          pic x(28)    value spaces.
 77  Script-Name         pic x(20)    value spaces.
 77  Run-Backup          pic x(512)   value spaces.  *> size changed
 77  Full-Backup-Script  pic x(512)   value spaces.
 77  OS-Delimiter        pic x        value "/".     *> Preset for Linux/unix etc
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
     05 filler           pic 9(2)  comp.    *> Always 00
*>
 01  ws-data.
     03  menu-reply      pic x          value "A".   *> force Date entry on first starting
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
 copy "wsmaps03.cob".
 copy "wscall.cob".
 copy "wstime.cob".
 copy "wsfnctn.cob".
 copy "wssystem.cob".
 copy "wssys4.cob"   replacing System-Record-4 by WS-System-Record-4.
 copy "wsdflt.cob".       *> Only used by mapser / gl020
 copy "wsfinal.cob".      *> Only used by mapser
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
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
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
*> Module Wide
     03  GL005           pic x(36) value "GL005 No Archive File found, Aborted".
*>
 01  to-day              pic x(10).
*>
 01  WS-Temp-System-Rec  pic x(2048).   *> Size overkill
*>
 procedure division.
*>=================
*>
 General-Control  Section.
*>***********************
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
*>
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     function current-date to wse-date-block.
     perform  zz020-Get-Program-Args.
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
 Open-System.                                   *> First get system param cobol file
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.
     if       fs-reply not = zero
 *>             perform System-Close
              move    "sys002" to ws-called     *> create param file by requesting info from user
              call    ws-called using ws-calling-data file-defs
              perform System-Open
     end-if.
*>
 aa010-Get-System-Recs.
     move     zeros to File-System-Used         *> again in case RDB setup
                       File-Duplicates-In-Use.  *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     4 to File-Key-No.
     perform  System-Read-Indexed.        *> Read Cobol file sys totals
     move     System-Record to WS-System-Record-4.
*>
     move     2 to File-Key-No.
     perform  System-Read-Indexed.        *> Read Cobol file defaults
     move     System-Record to Default-Record.
*>
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
*>                       move     System-Record to WS-System-Record-4 *> overwrite cobol rec.
*>              end-if
*>              move     2 to File-Key-No
*>              perform  System-Read-Indexed                 *> get the record from the RDB table
*>              if       fs-reply = zero
*>                       move     System-Record to Default-Record
*>              end-if
*>              move     1 to File-Key-No
*>              perform  System-Read-Indexed                 *> get the record from the RDB table
*>              if       fs-reply not = zero                  *> but if error we have a problem such as someone forgot to run system load modules.
*>                       move WS-Temp-System-Rec to System-Record   *> restore saved cobol file rec
*>                       perform System-Write                *> So create RDB row in SYSTEM-REC from the Cobol file data
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
     if       scycle = zero
              go to call-system-setup.
*>
     move     run-date to u-bin.
     call     "maps04" using maps03-ws.
     move     u-date to to-day.
     perform  zz060-Convert-Date.
*>
     if       not G-L
              set G-L to true.
*>
     if       op-system = zero
              move "O/S"     to op-display.
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
     move     zeros to ws-Process-Func ws-Sub-Function.
     if       menu-reply = "A"
              go to load01.
*>
 display-menu.
     display  usera at 0101 with foreground-color 3 erase eos.
     move     to-day to u-date.
     move     "general" to ws-caller.
     move     spaces to ws-called ws-del-link menu-reply.
     move     zeros to ws-term-code.
     display  maps-ser-xx at 2474 with foreground-color 3.
     move     maps-ser-nn to curs2.
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
     display  "General Ledger System Menu" at 0328 with foreground-color 2.
*>
     accept   wsb-time from time.
     if       wsb-time not = "00000000"
              move wsb-hh to wsd-hh
              move wsb-mm to wsd-mm
              move wsb-ss to wsd-ss
              display "at " at 0355 with foreground-color 2
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
     display  "(A)  Date Entry"                  at 1004  with foreground-color 2.
     display  "(B)  Chart Of Accounts"           at 1104  with foreground-color 2.
     display  "(C)  Default Account Maintenance" at 1204  with foreground-color 2.
     display  "(D)* Final Accounts Set-Up"       at 1304  with foreground-color 2.
     display  "(E)  Enter Transactions"          at 1404  with foreground-color 2.
     display  "(F)  Proof/Modify Transactions"   at 1504  with foreground-color 2.
     display  "(G)  Batch Status Report"         at 1604  with foreground-color 2.
*>
     display  "(H)  Transaction Posting"         at 1044  with foreground-color 2.
     display  "(I)  End Of Cycle Processing"     at 1144  with foreground-color 2.
     display  "(J)  Print Trial Balance"         at 1244  with foreground-color 2.
     display  "(K)  Print P&L and Balance Sheet" at 1344  with foreground-color 2.
     display  "(L)  Print Ledgers"               at 1444  with foreground-color 2.
     display  "(M)* Print Final Accounts"        at 1544  with foreground-color 2.
     display  "(X)  Exit to "                    at 1704  with foreground-color 2.
     display  Op-Display                         at 1717  with foreground-color 2.
     display  Batch-Text                         at 1745  with foreground-color 2.
*>     display  "(Y)*  File Garbage Collector"   at 1804  with foreground-color 2. *> change when done
     if       Param-Restrict not = "Y"
              display  "(Z)  System Set Up" At 1844       with foreground-color 2.
*>
 accept-loop.
*>
     accept   menu-reply at 0644  with foreground-color 6 auto UPPER.
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
     move     letters-upper to letters.
     set      q  to  1.
     search   a-entry
              when a-entry (q) = menu-reply
              set z to q.
     if       z = zero
              go to accept-loop.
     go       to load-it.
*>
 call-system-setup.
*>****************
*>
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     zero to ws-term-code.
     move     1 to File-Key-No.
     perform  System-Open.
     perform  System-Rewrite.                    *> in case of any changes
     move     2 to File-Key-No.
     move     Default-Record to System-Record.
     perform  System-Rewrite.
     move     4 to File-Key-No.
     move     WS-System-Record-4 to System-Record.
     perform  System-Rewrite.                    *> Update Cobol file sys totals
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
      if      Dos or Windows                              *> whats the correct string to add
              move Script-Name to Full-Backup-Script
      else
       if     OS2                                         *> whats the correct string to add
              move Script-Name to Full-Backup-Script.
     perform  overrewrite.
     call     "SYSTEM" using Full-Backup-Script.
     goback.
*>
*> Overrewrite saves the system param record in case of any changes after processing
*>  the requested process / program.
*>
 overrewrite.                                  *> save to RDB or file.
     if       File-System-Used NOT = zero   *> Force RDB processing
              move     "66" to FA-RDBMS-Flat-Statuses
              move     1 to File-Key-No
              perform  System-Open
              move     1 to File-Key-No
              move     System-Record to WS-Temp-System-Rec
              perform  System-Rewrite
              move     2 to File-Key-No
              move     Default-Record to System-Record
              perform  System-Rewrite
              move     4 to File-Key-No
              move     WS-System-Record-4 to System-Record
              perform  System-Rewrite
              perform  System-Close
              move     WS-Temp-System-Rec to System-Record
     end-if.
*>
*> Now do the same for the Cobol file.
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to FA-RDBMS-Flat-Statuses.    *> Force Cobol file proc.
     move     1 to File-Key-No.
     perform  System-Open.                       *> Open cobol file params as I/O
     move     1 to File-Key-No.
     move     System-Record to WS-Temp-System-Rec.
     perform  System-Rewrite.                    *> Update Cobol file params
     move     2 to File-Key-No.
     move     Default-Record to System-Record.
     perform  System-Rewrite.
     move     4 to File-Key-No.
     move     WS-System-Record-4 to System-Record.
     perform  System-Rewrite.                    *> Update Cobol file sys totals
     move     WS-Temp-System-Rec to System-Record.
     perform  System-Close.                      *> Close the Cobol param file.
*>
 overclose.
     goback.
*>
 load-it.
*>******
*>
     move     space to menu-reply.
     go       to load01 load02 load03 loadsr load05 load06 load07
                 load08 load09 load10 load11 load12 loader loader
                 loader loader loader loader loader loader loader
                 loader loader loader loadsr call-system-setup
              depending on z.
*>
 loader.
*>-----
*>
     go       to display-menu.
*>
 load00.
*>-----
*>
     move     zero to ws-term-code.
     call     ws-called using ws-calling-data
                              system-record
                              to-day
                              file-defs
     end-call
     if       ws-term-code > 7
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
                              default-record
                              to-day
                              file-defs.
     if       ws-term-code > 7
              go to overrewrite.
*>
 load000-exit.
*>
     go       to display-menu.
*>
 load01.
*>-----
*>
     move     "gl000" to ws-called.
     go       to load00.
*>
 load02.
*>-----
*>
     move     "gl030" to ws-called.
     go       to load00.
*>
 load03.
*>-----
*>
     move     "gl020" to ws-called.
*>     go       to load000.
*>
*> after updating default, below should be run instead of above ??
*>    to update system record (Defaults)
*>

     perform  load000.
     perform  overrewrite.
     perform  aa010-get-system-recs.
     go       to display-menu.
*>
 load04.
*>*****
*>   Final accounts Set Up
*>
*>       NOT BUILT as not currently needed for GL but rec 3 will need to be read in.
*>
     move     "gl040" to ws-called.
     perform  load000.
     perform  overrewrite.
     perform  aa010-get-system-recs.
     go       to display-menu.
 load05.
*>-----
*>
     move     "gl050" to ws-called.
     perform  load000.
     perform  overrewrite.
     perform  aa010-get-system-recs.
     go       to display-menu.
*>
 load06.
*>-----
*>
     move     "gl051" to ws-called.
     perform  load00.
     perform  overrewrite.
     perform  aa010-get-system-recs.
     go       to display-menu.
*>
 load07.
*>-----
*>
     move     "gl060" to ws-called.
     go       to load00.
*>
 load08.
*>-----
*>
     move     "gl070" to ws-called.
     perform  load00.
     if       ws-term-code = 5
              go to display-menu.
     move     "gl071" to ws-called.
     perform  load00.
     move     "gl072" to ws-called.
     go       to load00.
*>
 load09.
*>-----
*>
     move     "gl080" to ws-called.
     go       to load00.
*>
 load10.
*>-----
*>
     move     "gl090" to ws-called.
     go       to load00.
*>
 load11.
*>-----
*>
     move     "gl120" to ws-called.
     go       to load00.
*>
 load12.
*>-----
*>
*>     if       not archiving
*>              display "Sorry you are not archiving post data" at 2322
*>              go to accept-loop.
*>
     move     "gl100" to ws-called.
     perform  load00.
     if       ws-term-code = 5
              go to accept-loop.
     if       ws-term-code = 4
              move space to ws-reply
              display space   at 0101 with erase eos
              display GL005 at 0510 with foreground-colour 2
              display SY008 at 0710 with foreground-colour 2
              accept ws-reply at 0744
              go to display-menu
     end-if
     move     "gl105" to ws-called.
     go       to load00.
*>
 load13.
*>
*>     Print Final Accounts
*>
*>        NOT BUILT as not needed for GL but rec 3 will need to be read in.
*>
     move     "gl130" to ws-called.
     go       to load00.
*>
 load25.
*>-----
*>
*>  File Garbage Collector
*>
*>     NOT YET BUILT Is it needed ?
*>
     move     "gl190" to ws-called.
     go       to load00.
*>
 loadsr.
*>-----
*>
     display  "Sorry not available" at 2327 with foreground-color 2.
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
