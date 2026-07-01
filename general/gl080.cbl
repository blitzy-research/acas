       >>source free
*>*****************************************************
*>                                                    *
*>            End  Of  Cycle  Processing              *
*>                                                    *
*>*****************************************************
*> WARNING THIS IS ARCHIVING TO a path that has a Usb memory stick
*>    or a specific directory (in which case it is up to the user
*>    to ensure that that directory is copied to a suitable medium
*>    after processing.
*> READ the Remarks section for more information.
*>****************************************************************
 identification          division.
*>===============================
*>
*>**
      Program-Id.         gl080.
*>**
*>    Author.             GL was written by Simon Whine MBCS, on behalf of
*>                        Applewood Computers and its group of Companies.
*>                        All changes/migrations by:
*>                        Vincent B. Coen FBCS, FIDM, FIDPM.
*>                        Converted To Cis January 85,
*>                        For Applewood Computers.
*>                        Written to supplement IRS to support larger numbers for
*>                        accounts to 10 digits nominal and subnominals and money
*>                        amounts to 100M - 1 for customers requiring a
*>                        comparable? but cheaper product than Oracle financials.
*>                        Reduced down some point later in time for accnts 6
*>                        digits and reduced money amounts.
*>**
*>    Security.           Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            End Of Cycle / Quarter Processing.
*>                        Clear down old posting records having made
*>                        an archive of them to a specified path,
*>                        eg a previously MOUNTED memory stick.
*>
*>                        This function will only run if Archiving is set to Yes
*>                        in the system parameter file under G/L for Cobol files.
*>                        It will also check if there are any non proofed or
*>                        posted batches present and exit with a message GL088.
*>
*>                        For RDB usage it is not needed as the RDB system will be
*>                        running back ups daily or more often assuming you have
*>                        turned on such back ups frequently, eg, hourly/daily.
*>                        However these is no difference in processing for RDB.
*>
*>                        However For Cobol file processing, this is a bit moot
*>                        assuming system makes a back up after processing, e.g.,
*>                        when exiting the system, this is the same for all
*>                        other systems such as sales, purchase, stock & irs,
*>
*>                        This process is a hold over from usage of floppies
*>                        as the main storage medium for all files.
*>                        It is, based on old systems converted to the original
*>                        Personal Computers and as of now.
*>
*>                        Note that IRS does not do this but retains the posting
*>                        until End of Year where it can be then cleared by user
*>                        after all ledgers have been printed.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     None.
*>**
*>    Error messages used.
*> System wide.
*>                        GL012 Note and hit Return
*> Module specific.
*>                        GL081 File Error On Writing Work/Post. Aborting Phase
*>                        GL082 Post record size not same as Work file
*>                        GL083 You need to fix this before continuing
*>                        GL084 Enter <0> to signify change made or <9> to abort this run :- [ ]
*>                        GL085 Ensure Archive USB Memory Stick is in path
*>                        GL086 Ensure you have done a file backup prior to running!!!
*>                        GL087 Hit Escape or press A to abort
*>                        GL088 Batches present that have NOT been proofed or posted !
*>**
*> Changes:
*> 28/01/09 vbc - Migration to Open Cobol.
*> 18/12/11 vbc - .02 Support for dates other than UK & clean up msgs
*>                    Error msgs to GLnnn,
*>                    Support for path+filenames.
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks.
*> 13/01/18 vbc - .03 Updated for v3.02 & FH & DALs.
*> 30/05/18 vbc - .04 Renamed all warning & error msgs also in Manual.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*> NOTE TESTING Code in the  disk-change  section
*> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
     select  archive    assign  file-2
                        access  sequential
                        status  fs-reply
                        organization  line sequential.
*>
     select  work-file  assign  file-21
                        access  sequential
                        organization  sequential
                        status  fs-reply.
*> copy "seledger.cob".
*> copy "selbatch.cob".
*> copy "selpost.cob".
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 fd  archive.
*>
 01  arc-trans-record.
     03  arc-batch       pic 9(5).
     03  arc-post        pic 9(5).
     03  arc-code        pic xx.
     03  arc-date        pic x(8).
     03  arc-ac          pic 9(6).
     03  arc-pc          pic 99.
     03  arc-amount      pic s9(8)v99.
     03  arc-legend      pic x(32).
     03  arc-c-ac        pic 9(6).
     03  arc-c-pc        pic 99.
*>
 fd  work-file.
*>
 01  work-file-record    pic x(101).     *> Was 96 added 5 for WS-Post-rrn (9(5).
*>
*> copy "fdledger.cob".
*> copy "fdbatch.cob".
*> copy "fdpost.cob".
*>
 working-storage section.
*>----------------------
*>
 77  prog-name           pic x(15)  value "gl080 (3.3.00)".
 77  y                   pic 99     value zero.
 77  a                   pic 99     value zero.
 77  keyed-reply         pic x      value space.
 77  ws-eval-msg         pic x(25)  value spaces.
*>
 01  Arg-Test            pic x(525) value spaces.
 copy "wsledger.cob".
 copy "wsbatch.cob".
 copy "wspost.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
*>     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
*>     03  WS-Ledger-Record       pic x.
*>     03  WS-Posting-Record      pic x.
*>     03  WS-Batch-Record        pic x.
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
 01  accept-terminator-array   pic 9(4).
     copy "screenio.cpy".
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
    03  GL012           pic x(25) value "GL012 Note and hit Return".
*> Module specific
    03  GL081           pic x(54) value "GL081 File Error On Writing Work/Post. Aborting Phase.".
    03  GL082           pic x(44) value "GL082 Post record size not same as Work file".
    03  GL083           pic x(44) value "GL083 You need to fix this before continuing".
    03  GL084           pic x(70) value "GL084 Enter <0> to signify change made or <9> to abort this run :- [ ]".
    03  GL085           pic x(48) value "GL085 Ensure Archive USB Memory Stick is in path".
    03  GL086           pic x(60) value "GL086 Ensure you have done a file backup prior to running!!!".
    03  GL087           pic x(36) value "GL087 Hit Escape or press A to abort".
    03  GL088           pic x(60) value "GL088 Batches present that have NOT been proofed or posted !".
*>
 copy "wsfnctn.cob".
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
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 gl080-Main section.
*>*****************
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
*>
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "End Of Cycle Processing" at 0130 with foreground-color 2.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
     display  usera at 0301 with foreground-color 3.
     move     1  to File-Key-No.
*>
     move     zero  to  a.
     move     scycle to lin2.
*>
*> Let check that a back up has been run first
*>
     display  GL085  at 0801 with foreground-color 3.
     display  GL086  at 0901 with foreground-color 3 highlight.
     display  GL087  at 1001 with foreground-color 3 highlight.
     move     space to keyed-reply.
     accept   keyed-reply at 1065 with update auto.
     if       cob-crt-status = cob-scr-esc
         or   keyed-reply = "A" or "a"
              goback.
*>
*> Good now we can process
*>
     display  "Phase - 1.  Batch Check" at 0801 with foreground-color 2 erase eos.
     perform  gl080a.
     if       a = 1
              display GL088 at 1501 with foreground-color 2
              display GL012 at 1701 with foreground-color 2
              move     space to keyed-reply
              accept   keyed-reply at 1065 with update auto
              go to  main-end.
*>
     if       archiving
              display "Phase - 2.  Transaction Archiving" at 0801 with foreground-color 2
              perform gl080b
     else
              display "Phase - 3.  Transaction Deletion" at 0801 with foreground-color 2
              perform gl080c.
*>
     perform  compress-post.
*>
     if       a = 9
          or  scycle <  period
              go to  main-end.
*>
     divide   scycle by period giving a rounded.
     multiply a  by  period  giving  y.
*>
     if       scycle not = y
              go to  main-end.
*>
     add      1  to scycle.
*>
     display  "Phase - 5.  End of Period Processing" at 0801 with foreground-color 2.
     perform  GL-Nominal-Open.                   *> open     i-o  ledger-file.
*>
 loop.
*>***
*>
     perform  GL-Nominal-Read-Next.               *> read     ledger-file  next record at end
     if       fs-reply = 10
              go to  loop-end.
     move     ledger-balance  to  ledger-q (a).
     if       current-quarter = 4
              move  ledger-balance  to  ledger-last.
     perform  GL-Nominal-Rewrite.                 *> rewrite  ledger-record.
     go       to loop.
*>
 loop-end.
*>*******
*>
     perform  GL-Nominal-Close.                   *> close    ledger-file.
     add      1  to  current-quarter.
     if       current-quarter = 5
              move  1  to  current-quarter.
     if       period = 3
        and   scycle > 12
              move 1 to scycle.
     if       period = 13
        and   scycle > 52
              move 1 to scycle.
*>
 main-end.
      goback.
*>
 gl080a section.
*>*************
*>
     display  "Checking Batches" AT 2301 with foreground-color 2.
     perform  GL-Batch-Open-Input.              *> open     input  batch-file.
*>
 loop.
*>***
*>
     perform  GL-Batch-Read-Next.               *> read     batch-file  next record  at end
     if       fs-reply = 10
              go to  end-run.
*>
     if       bcycle not = scycle
              go to  loop.
*>
     if       not status-closed
       and    not processed
              move  1  to  a.
*>
     go       to loop.
*>
 end-run.
*>******
*>
     perform  GL-Batch-Close.                    *> close    batch-file.
*>
 main-exit.   exit section.
*>********    ****
*>
 gl080b section.
*>*************
*>
     display  "Archiving.      Cycle - " at 2301  with foreground-color 2.
     display  lin2 at 2330         with foreground-color 2.
     display  "/ Batch - " at 2334 with foreground-color 2.
     display  "/ Item  - " at 2352 with foreground-color 2.
*>
     perform  disk-change.  *>   set up o/p path
*>
     if       a = 9
              go to  main-exit.
*>
     open     extend  archive.
     if       fs-reply not = zero   *> just in case extend wont create
              close archive         *>  a non-existent file
              open output archive.
     perform  GL-Batch-Open.                       *> open     i-o  batch-file.
*>
 loop.
*>***
*>
     perform  GL-Batch-Read-Next.                  *> read     batch-file  next record  at end
     if       fs-reply = 10
              go to  end-run.
*>
     if       bcycle not = scycle
              go to  loop.
*>
     perform  arc-process.
     perform  GL-Posting-Close.                     *> close    posting-file.
*>
     move     2         to  cleared-status.
     move     run-date  to  stored.
     move     zero      to  batch-start.
     perform  GL-Batch-Rewrite.                    *> rewrite  batch-record.
     go       to loop.
*>
 end-run.
*>******
*>
     close    archive.                             *> close batch-file
     perform  GL-Batch-Close.
*>
 main-exit.   exit section.
*>********    ****
*>
 arc-process        section.
*>-------------------------
*>
     display  WS-Batch-Nos at 2345 with foreground-color 2.
     move     WS-Batch-Nos  to  arc-batch.
     perform  GL-Posting-Open.                      *> open     i-o  posting-file.
*>
 loop.
*>***
*>
     perform  GL-Posting-Read-Next.                 *> read     posting-file  next record  at end
     if       fs-reply = 10
              go to  main-exit.
*>
     if       WS-Post-Key = zero
        or    batch  not = WS-Batch-Nos
              go to  loop.
*>
     display  post-number at 2364 with foreground-color 2.
*>
     move     batch        to  arc-batch.
     move     post-number  to  arc-post.
     move     post-code in WS-Posting-Record    to  arc-code.
     move     post-date    to  arc-date.
     move     post-legend  to  arc-legend.
*>
     move     post-dr      to  arc-ac.
     move     dr-pc        to  arc-pc.
     move     post-cr      to  arc-c-ac.
     move     cr-pc        to  arc-c-pc.
*>
     if       post-vat-side = "CR"
              add  post-amount  vat-amount  giving  arc-amount
     else
              move post-amount  to  arc-amount.
*>
     write    arc-trans-record.
*>
     move     post-cr      to  arc-ac.
     move     cr-pc        to  arc-pc.
     move     post-dr      to  arc-c-ac.
     move     dr-pc        to  arc-c-pc.
*>
     if       post-vat-side = "DR"
              add  post-amount  vat-amount  giving  arc-amount
     else
              move post-amount  to  arc-amount.
*>
     multiply arc-amount  by  -1  giving  arc-amount.
*>
     write    arc-trans-record.
*>
     if       vat-ac of WS-Posting-Record equal  zero
           or vat-amount = zero
              go to  by-pass.
*>
     move     vat-ac of WS-Posting-Record  to  arc-ac.
     move     vat-pc     to  arc-pc.
     move     vat-amount to  arc-amount.
*>
     if       post-vat-side = "CR"
              multiply  arc-amount  by  -1 giving arc-amount.
*>
     write    arc-trans-record.
*>
 by-pass.
*>******
*>
     perform  GL-Posting-Delete.                   *> delete   posting-file  record.
     go       to loop.
*>
 main-exit.   exit section.
*>********    ****
*>
 disk-change        section.
*>-------------------------
*>     Copied to gl080
*>     ***************
*>
*> Build path for archive file/s
*>    this set up for testing but need to change to accept
*>     path to usb memory stick (full path) but will work as is
*>       assuming users changes path and the system KNOWS about
*>         the memory stick
*>
     move     space to Arg-Test.                   *> this lot looks wrong !!!!!
     string   file-24        delimited by space   *> spaces
              "archives"     delimited by size
              file-defs-os-delimiter
                             delimited by size
                file-2      delimited by space  *> archive.dat
                            into Arg-Test.
     move     Arg-Test to file-2.
*>
     display  GL085 at 1201 with erase eol foreground-color 2.
     display  Gl084 at 1301 with erase eol foreground-color 2.
*>
 accept-option.
*>************
*>
     accept   a at 1369.
     if       a = 9
              go to  main-exit.
     if       a  not = zero
              go to  accept-option.
*>
*>  Hopefully can remove these after testing
*>
     display  "Current path/name is :" at 1401 with foreground-color 2 erase eol.
     display  file-2             at 1501 with foreground-color 2 erase eol.
     accept   file-2             at 1501 with foreground-color 2 update.
     if       file-2 (1:1) = space
              go to accept-option.
*>
 main-exit.   exit section.
*>********    ****
*>
 gl080c section.
*>*************
*>
     display  "Deleting.       Cycle - " at 2301 with foreground-color 2.
     display  lin2 at 2330 with foreground-color 2.
     display  "/ Batch - " at 2334 with foreground-color 2.
     display  "/ Item  - " at 2352 with foreground-color 2.
*>
     perform  GL-Batch-Open.                   *> open     i-o  batch-file.
*>
 loop.
*>***
*>
     perform  GL-Batch-Read-Next.              *> read     batch-file  next record  at end
     if       fs-reply = 10
              go to  end-run.
*>
     if       bcycle not = scycle
              go to  loop.
*>
     perform  del-process.
     perform  GL-Posting-Close.                *> close    posting-file.
*>
     move     2         to  cleared-status.
     move     run-date  to  stored.
     move     zero      to  batch-start.
*>
     perform  GL-Batch-Rewrite.                *> rewrite  batch-record.
     go       to loop.
*>
 end-run.
*>******
*>
     perform  GL-Batch-Close.                  *> close    batch-file.
*>
 main-exit.   exit section.
*>********    ****
*>
 del-process        section.
*>-------------------------
*>
*> Using RDB this step can be done with one SQL process to delete all with
*>   specific batch no but using Cobol this is not possible.
*>
     display  WS-Batch-Nos at 2345.
     perform  GL-Posting-Open.              *> open     i-o    posting-file.
*>
 loop.
*>***
*>
     perform  GL-Posting-Read-Next.         *> read     posting-file  next record  at end
     if       fs-reply = 10
              go to  main-exit.
*>
     if       WS-Post-Key = zero
        or    batch  not = WS-Batch-Nos
              go to  loop.
*>
     display  post-number at 2364 with foreground-color 2.
*>
     perform  GL-Posting-Delete.            *> delete   posting-file  record.
     go       to loop.
*>
 main-exit.   exit section.
*>********    ****
*>
 compress-post  section.
*>---------------------
*>
*>  First check if NOT running with Cobol files, if so skip section.
*>
     if       not FS-Cobol-Files-Used    *> Will use fn-Read-Next-Sorted-By-Batch (32)
              go to main-exit
     end-if.
*>
     display  "Phase - 4.  Posting Contraction " at 0801 with foreground-color 2.
*>
 Test-Work-File-Size-1.
*>
*>  Check files are same size
*>
     if       function length (WS-Posting-Record) not =
              function length (work-file-record)
              display GL082 at 1001 with foreground-color 3
              display GL083 at 1101 with foreground-color 3
              display GL012 at 1201 with foreground-color 3
              accept Keyed-Reply at 1227
              stop run.
*>
     perform  GL-Posting-Open-Input.          *> open     input  posting-file.
     open     output work-file.
*>
 loop1.
*>****
*>
     perform  GL-Posting-Read-Next.           *> read     posting-file next record at end
     if       fs-reply = 10
              go to loop1-end.
     if       fs-reply not = zero
              go to file-error.
     write    work-file-record from WS-Posting-Record.
     if       fs-reply not = zero
              go to file-error.
     go       to loop1.
*>
 loop1-end.
*>********
*>
     close    work-file.                       *> posting-file
     perform  GL-Posting-Close.
     open     input  work-file.
     perform  GL-Posting-Open-Output.               *> open     output posting-file.
*>
 loop2.
*>****
*>
     read     work-file at end
              go to loop2-end.
     if       fs-reply not = zero
              go to file-error.
     move     work-file-record to WS-Posting-Record.
     perform  GL-Posting-Write.           *> write    posting-record from work-file-record.
     if       fs-reply not = zero
              go to file-error.
     go       to loop2.
*>
 file-error.
*>*********
*>
     display  GL081 at 1501 with foreground-color 2.
     display  fs-reply at 1539 with foreground-color 2.
     perform  evaluate-message.
     display  ws-Eval-Msg at 1542.
     display  GL012 at 1601   with erase eol foreground-color 2.
     accept   Keyed-Reply at 1627.
     display  " " at 1601 with erase eol.
*>
 loop2-end.
*>********
*>
     close    work-file.             *>  posting-file.
     perform  GL-Posting-Close.
*>
 main-exit.
*>********
*>
     exit     section.
*>
 Evaluate-Message       Section.
*>=============================
*>
 copy "FileStat-Msgs.cpy" replacing MSG by ws-Eval-Msg
                                    STATUS by fs-reply.
*>
 Eval-Msg-Exit.  exit section.
*>************   ****
*>
 zz070-Convert-Date     section.
*>*****************************
*>
*>  Converts date in to-day to UK/USA/Intl date format
*>****************************************************
*> Input:   to-day
*> output:  ws-date as uk/US/Inlt date format
*>
     move     to-day to ws-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     to-day (7:4) to ws-Intl-Year.
     move     to-day (4:2) to ws-Intl-Month.
     move     to-day (1:2) to ws-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
