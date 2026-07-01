       >>source free
*>*******************************************************
*>                                                      *
*>      WARNING, WARNING, WARNING - - - - - - - - - - - *
*>                                                      *
*>  THIS PROGRAM REQUIRES A LOT MORE TestING            *
*>                          ^^^                         *
*>   to verify that all defined requirements are met    *
*>    and work as expected considering all the changes  *
*>    made                                              *
*>                                                      *
*>  AND MORE CODING POSSIBLY !!!!!!!!!!!!!!!!           *
*>  06 FEBRARY 2023                                     *
*>                                                      *
*>             End Of Cycle Processing                  *
*>                                                      *
*>   This program updates records for :                 *
*>    Sales & Purchase (invoices, open items & ledgers) *
*>    and Value records both sales and purchase.        *
*>                                                      *
*>    Stock does not require any, all builtin. and for  *
*>    IRS & General only postings records and that is   *
*>    included for each one.                            *
*>    Also to be considered is auto running on the      *
*>    Start of a month or similar setting flags ?       *
*>    Likewise updates for RDB proc.    08/10/2016      *
*>                                                      *
*>  You MUST have run invoices and payment proofs,      *
*>   postings & analysis runs FIRST before running      *
*>   XL150 otherwise you will lose information / data.  *
*>                                                      *
*>  >>>  You must only run End of Cycle processing when *
*>   there is NO ONE else using the system.       <<<<< *
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ *
*>                                                      *
*>  These msut be run in order -
*>  1.  Sales proof,
*>  2.  Sales Picking/Packing note prints and this always *
*>    done  before invoices.
*>  3.  Sales Invoices prints
*>  4.  Sales proof report
*>  5.  Sales posting
*>
*>   Next the same for Purchase Ledger.
*>
*>    All analysis, customer reports for both systems.
*>
*>    This is also a good time to run of the Stock
*>    reports so you have end of period status on paper
*>    include the stock control report to verify stock
*>    holdings match the computer records.
*>    For any differences find out why and as needed
*>    update Stock control records via stock additions or
*>    Stock Deductions.
*>                                                      *
*>    End of cycle can be :                             *
*>         Monthly, Quarterly and more importantly      *
*>           EOY (End of Year).                         *
*>    For EOY it will reset the yearly stats for all    *
*>      Ledger records (both Live and dead) as well as  *
*>       the analysis totals. SO it it important that   *
*>       you have run off all ledger & analysis reports *
*>       for both Sales and Purchase                    *
*>       BEFORE running this program.                   *
*>                                                      *
*> Processing:                                          *
*>    For monthly & quarterly it will update records    *
*>       in the Ledgers, for invoices will delete line  *
*>       records and delete invoice headers if closed   *
*>       and paid.                                      *
*>       Note that there are two invoice files for each *
*>       ledger - the main, which contains invoice line *
*>       items and the header record - these are        *
*>       deleted after a proof report, invoices printed *
*>       and posted to the OTM file.
*>
*>       The second is                                  *
*>       OTM (Open Item File) which contains unpaid     *
*>       invoices and these are deleted after being     *
*>       paid and closed after months end & statement   *
*>       produced by email or printing.                 *
*>
*>       As Deleted records will still take up space in *
*>       the Cobol files are well as most RDBMS another *
*>       process is run at start of a new year to clear *
*>       these out by saving data to temp files and     *
*>       then reloading these files.                    *
*>
*>       This is a major reason for ensuring that Back  *
*>       Ups are run PRIOR to running XL150.            *
*>       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  *
*>                                                      *
*>    For users of the RDB data systems the data reload *
*>      is done using the RDB system itself by using    *
*>      the RDB utilities. See the RDB manuals.         *
*>                                                      *
*>      When running End of Cycle you must ensure that  *
*>      all proofing reports have been produced as well *
*>      as posting all invoices, payments and printing  *
*>      the analysis reports.                           *
*>                                                      *
*>    IF using Autorun you MUST ensure that all         *
*>    required computers are on likewise ALL required   *
*>    printers are on with plenty of paper.             *
*>
*>    These process could produce (if not already run,  *
*>    Proof reports for Sales and Purchase ledgers,     *
*>    Printed all outstanding :                         *
*>    Invoices and Purchase Orders, Sales Picking &     *
*>    Packing lists, Posting reports for both Sales and *
*>    Purchase Ledgers.                                 *
*>                                                      *
*> WARNING This program will only autorun sl130 & pl130 *
*>    but should have been run during normal processing *
*>    prior to running End of Cycle                     *
*>
*>    At end of month, as in before End of Day these    *
*>    processes should have been run prior to running   *
*>    xl150 System End of Cycle processing.             *
*>                                                      *
*>    YES, mentioned twice.                             *
*>
*>  If you do not follow these procedures you run the   *
*>   likely risk of losing data that you might rely on  *
*>   for quarterly and End of year ACcounting.          *
*>
*>  For this reason, this program will check as much as *
*>  possible that proofs and posting have occured when  *
*>  xl150 (End of Period processing) runs.              *
*>  NOTE that is cannot check if you have run data      *
*>  Backups which by default is run every time you exit *
*>  any of the systems.                                 *
*>                                                      *
*>*******************************************************
*>
 identification          division.
*>===============================
*>
*>**
     Program-Id.         xl150.
*>**
*>   Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM,
*>                       25/10/83,
*>                       For Applewood Computers.
*>**
*>   Remarks.            End of Cycle Processing.
*>
*>                       This program must be run before ANY ACAS processing
*>                       on the FIRST day of the month or the last day of the
*>                       current month after all processes have been run.
*>
*>                       TIMINGS: For small to medium business the total time
*>                       is within 10 minutes even on a slow system.
*>                       Current systems are within 1 - 3 minutes.
*>                       Yes, it is quick - subject to number of invoices
*>                       produced monthly (timing Based on < 2,500 per month)
*>                       with > 70% paid by end of month.
*>**
*>   Security.           Copyright (C) 1976-2026 and later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License
*>                       v2.0. Only. See the file COPYING for details.
*>
*>                       This does not give you the rights to sell or rent on this
*>                       software or any component of the same.
*>                       For such right contact the lead programmer as indicated at
*>                       inside front page of all manuals with your business proposals.
*>**
*>   Version.            See Prog-Name In Ws.
*>**
*>   Called Modules.
*>                       maps04.
*>                       ACas013 ->   --- Will run sl130 and pl130 if not run already
*>                        valueMT
*>                       ACas012 ->
*>                        salesMT
*>                       ACas019 ->
*>                        OTM3MT
*>                       ACas022 ->
*>                        purchMT
*>                       ACas029 ->
*>                        OTM5MT
*>
*>**
*>   Temporary files.
*>                       Invoice     -  Data cleared down after usage.
*>                       Open-Item   -  Data cleared down after usage.
*>                       Ledgers     -  Data cleared down after usage.
*>                                         for both sales and purchasing.
*>                                      E.g., zero size.
*>**
*>   Error messages used.
*>                       SL006
*>                       SL007
*>                       SL008
*>                       SL009
*>
*>                       XL001
*>
*>                       XL101
*>                       XL102
*>                       XL103
*>                       XL104
*>                       XL105
*>                       XL106
*>                       XL107
*>                       XL108
*>                       XL116
*>                       XL117.
*>                       XL118.
*>                       XL119.
*>**
*>   Error Codes.
*>                       WS-Term-Code = 3 for File status Error.
*>  Changes.
*>   ------ vbc -     To Zero Paid This Month (Oi-P-C)
*> 05/03/83 vbc -     Remove 92 day old PF invoices from invoice file.
*> 31/03/83 vbc -     Fix for new invoice file layout.
*> 21/02/83 vbc -     To strip closed records from invoice file.
*> 07/10/83 vbc -     Zap io-deduct-amt from payment records.
*> 25/10/83 vbc -     CIS Cobol conversion.
*> 09/12/83 vbc -     Change error messages to hit return.
*> 19/12/83 vbc -     Allow for system record 4.
*> 01/03/84 vbc -     Support Sales-Unapplied in phase1 routine.
*> 10/03/84 vbc -     Support for ih-day-book-flag.
*> 01/04/84 vbc -     If openitm3 inv closed delete inv from inv file
*>                    but only if SL-own-nos not = y.
*>                    At end of year kill value file,also ACcept pass
*>                    before starting & Test.
*> 17/05/84 vbc -     If end of quarter/year remove deleted records
*>                    from Sales-file. remove deleted recs from itm3.
*> 24/08/84 vbc -     Tidy up phase display,remove new year Test in phase 3.
*> 25/09/84 vbc -     Support for PL-payments in wssys4.
*> 08/03/85 vbc -     Build prog to include pl150 & sl150.
*> 13/02/02 vbc -     VA-Systems = p corrected & Y2K.
*> 29/01/09 vbc -     Migration to Open Cobol.
*> 19/03/09 vbc -     Updated Sales file layouts. 3.00.02.
*> 21/12/11 vbc - .03 Support for dates other than UK & clean up msgs
*>                    Error msgs to GLnnn,
*>                    Support for path+filenames.
*>                    replaced copies in common to sales, purchase etc
*>                    changing field names to suit.
*> 10/10/16 vbc - .04 Init. upgrades for RDB.  LOTS MORE NEEDED.
*>                    ACas013 Added replacing value file
*>                    Replace temp file records with fdsl & fdpl
*>                    renaming used fields in prog.
*> 14/01/18 vbc - .05 Update including RDB for v3.02.
*>   to               Removed usage of maps99 for displays.
*> 27/01/18           Added BA00-Value-Reset performed in phase-2B-End reducing
*>                    dup code and now only done once.
*>                    Cleaned up section and paragraph names.
*>                    For OTM3 and sales inv files update or delete it instead
*>                    of using temp files and re-creating data.
*>                    At start of New Year using themp files to flush indexes
*>                    and deleted records areas on disk.
*>                    Init Tests for non posted invoice, payments etc will
*>                    be displayed all at once if found, before terminating.
*>                    Removed usage of dummy file defs.
*>                    Added new error messages and better file status displays.
*>                    Cleaned them up to use standard routines.
*>                    Removed the check for own invoice nos so now deletes
*>                    as well (Sales Ledger). See comments for 01/04/84.
*>                    Value records are cleared down at New Year not deleted
*>                    as they will need to be recreated by system.
*>                    This does 'assume' that codes are not discontinued over time.
*>                    May need to review this decision.
*> 21/03/18 vbc - .06 Start Adding code for Autorun (also needed in PL, SL etc.
*> 22/03/18 vbc -     Extra code for running if needed pl130 and/or sl130 value
*>                    reports and these have been changed so they will not stop
*>                    if no file or data exists.
*> 18/06/20 vbc - .07 'Have you' warning message one line too high.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 30/12/24 vbc - .08 change WS-Temp-Code to use 8 not 12 as its pic 9.
*> 05/01/25 vbc       Changed sl130 and pl130 to read and rewrite param rec
*>                    after field change in each. This needs to be done for EVERY
*>                    ACAS program that does ANY param field changes.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>    TO BE CODED.
*>    ^^^^^^^^^^^
*>                    If using Autorun, will run any outstanding processes such as:
*>                    Sales invoice proof, printing (invoices and packing notes) & posting.
*>                    Purchase PO proof, print Purchase orders & then posting.
*>                    Only then will xl150 continue.
*>                    If not using Autorun will stop with error / warning messages if
*>                    needed to be Actioned.
*>
*>                    MORE CODING NEEDED !!!!!!
*>
*>                    IT IS NOT RECOMMENDED TO RUN XL150 in Autorun as there are required
*>                    processes that might well not have been run.
*>
*>   Functions Added: TO BE Added....
*>
*>                    IRS   ---- NO - done within at user request.
*>                    Stock ---- NO - done within at user request.
*>                    General -- NO - done within at user request.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 2024-04-16.
*>
*> These files and programs are part of the Applewood Computers ACcounting
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
*> to fix it, providing you tell me ABout the problem.
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
 input-output            Section.
*>------------------------------
*>
 file-control.
*>-----------
*>
 copy "slselois.cob".
*>
     select Temp-Sales-File     assign file-21
                                ACcess sequential
                                status FS-Reply.
*>
     select Temp-Purchase-File  assign file-21
                                ACcess sequential
                                status FS-Reply.
*>
     select Temp-Invoice-File   assign file-21,
                                ACcess sequential,
                                status FS-Reply.
*>
 data                    division.
*>===============================
*>
 file Section.
*>-----------
*>
 COPY "slfdois.cob".  *> this is the longer one by 5 bytes (118 -113)
*>
 copy "fdsl.cob"    replacing
                          Sales-File      by Temp-Sales-File
                          Sales-Record    by Temp-Sales-Record
                          Sales-Current   by Temp-sales-Current
                          Sales-Last      by temp-sales-Last
                          Sales-Unapplied by temp-sales-Unapplied
                          Sales-Status    by temp-Sales-Status
                          Sales-Average   by temp-sales-Average
                          Sales-Activety  by temp-sales-Activety
                          STurnover-Q     by temp-STurnover-Q.
*>
 fd  temp-invoice-file.
*>
 01  temp-invoice-record.
     03  temp-invoice-key   pic x(10).
     03  filler             pic x(128).  *> APPLIES TO Purchase only of 100 and SL of 137.
*>                                            So using the largest as sales ledger layout.
*>  Added 25/01/18
*>
 copy "fdpl.cob"   replacing
                          Purchase-File   by Temp-Purchase-File
                          Purch-Record    by Temp-Purch-Record
                          purch-current   by Temp-Purch-Current
                          purch-last      by temp-Purch-Last
                          purch-unapplied by temp-Purch-Unapplied
                          purch-status    by temp-Purch-status
                          purch-average   by temp-Purch-Average
                          purch-activety  by temp-Purch-Activety
                          pturnover-q     by temp-STurnover-Q.

 working-storage Section.
*>----------------------
 77  prog-name           pic x(14) value "xl150 (3.3.00)".
 77  OS-Delimiter        pic x        value "/".
 77  ACAS_BIN            pic x(512)   value spaces.  *> Added
 77  ACAS_LEDGERS        pic x(500)   value spaces.
 77  Arg-Number          pic 9        value zero.
 77  z                   binary-char  value zero.
 77  z9                  pic z(6)9    value zero.
*>
*> holds program parameter values from command line
 01  Arg-Vals                         value spaces.
     03  Arg-Value       pic x(525)  occurs 2.
 01  Arg-Test            pic x(525)   value spaces.
*>
*> Here for extra code to get args for Batch processing via crontab etc.
*>
 01  Saved-CD-Args       pic x(13).
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "wsval.cob".   *> DONE
*>
*> SL
*>
 COPY "wssl.cob".    *> WS-Sales-Record (WS-Sales-Key) of 300 bytes - Test length.
*>
 COPY "slwsoi3.cob".    *> WS-OTM3-Record, redefs o-t-m-3 & OI-Header (slwsoi)
*>   Moves to ; OR from  so remove these moves.  */
 copy "slwssoi.cob"  replacing
                    ==si-header==  by ==soi-header redefines WS-OTM3-Record==
                    si-invoice    by soi-invoice
                    si-type       by soi-type
                    si-p-c        by soi-p-c
                    si-s-closed   by ss-closed
                    si-deduct-amt by soi-deduct-amt
                    si-applied    by soi-applied.
*>
 COPY "slwsinv2.cob"  replacing
                          Invoice-Record by SInvoice-Record
                          Invoice-Key    by Sinvoice-Key
                          Invoice-Nos    by Sinvoice-Nos
                          Item-Nos       by Sitem-Nos.
 01  WS-Invoice-Record  redefines SInvoice-Record
                        pic x(137).      *> Needed for FH.
*>
 copy "slwsinv.cob".  *> Holds header (SInvoice-Header) and 40 lines (SInvoice-Bodies)
*>                        as sih-                           sil-
*> PL / BL
*>
 COPY "wspl.cob".    *> WS-Purch-Record (WS-Purch-Key) of 302 bytes - Test length.
*>
 COPY "plwsoi5B.cob".  *> WS-OTM5-Record
 copy "plwssoi.cob"  replacing
                    ==si-header==  by ==poi-header redefines WS-OTM5-Record==
                    si-header     by poi-header
                    si-invoice    by poi-invoice
                    si-type       by poi-type
                    si-p-c        by poi-p-c
                    si-s-closed   by ps-closed
                    si-deduct-amt by poi-deduct-amt
                    si-applied    by poi-applied.
*>
 COPY "plwspinv2.cob"   replacing
                          invoice-key    by Pinvoice-Key
                          invoice-nos    by Pinvoice-Nos
                          item-nos       by Pitem-Nos.
*>
 copy "plwspinv.cob"  replacing
       *>                invoice-header   by PInvoice-Header
                    ih-Test          by pih-Test
                    ih-type          by pih-type
                    applied          by papplied
                    ih-lines         by pih-lines
                    ih-day-book-flag by pih-day-book-flag.
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
     03  Default-Record         pic x.
     03  Final-Record           pic x.
*>     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.   *> for GL
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.   *> For IRS
     03  WS-Stock-Audit-Record  pic x.
     03  WS-Stock-Record        pic x.
*>     03  WS-Sales-Record        pic x. *> Sales ledger rec.
*>     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.   *> Sales delivery details rec.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
*>     03  WS-Purch-Record        pic x.  *> Purch ledger rec.
     03  WS-Pay-Record          pic x.
*>     03  WS-Invoice-Record      pic x.   *> Sales invoice rec.
*>     03  WS-OTM3-Record         pic x.
*>     03  WS-PInvoice-Record     pic x.   *> Purch invoice rec.
*>     03  WS-OTM5-Record         pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-Testing to zero to stop logging.
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
 01  WS-data.
     03  WS-Reply        pic x.
     03  WS-Passwd       pic x(4)        value spaces.
     03  WS-Backup-Calling-Data
                         pic x(28)       value spaces.
     03  new-quarter     pic 9           value zero.
     03  New-Year        pic 9           value zero.
     03  Test-invoice    pic 9(8)        value zero.
     03  a               pic 99.
     03  pf-Test         binary-long     value zero.
     03  inv-Test        pic 9(5)  comp  value zero.
     03  SL-EoC          pic 9           value zero.
     03  PL-EoC          pic 9           value zero.
*>
     03  WS-Value-System pic x           value space.
*>
     03  WS-Proc-Month.
         05  WS-Proc-Mth pic 99                  value zero.
             88  WS-Good-Month                   values 01 thru 12.
     03  WS-Value-ClearDown pic x        value "N".
*>
     03  WS-env-lines    pic 999              value zero.
     03  WS-lines        binary-char unsigned value zero.
     03  WS-22-lines     binary-char unsigned value zero.
     03  WS-23-lines     binary-char unsigned value zero.
*>
     03  WS-Found-Error  pic x           value space.  *> = Y if found on prerun Tests
     03  WS-Msg          pic x(24)       value spaces. *> See AB995-Eval-Status
     03  WS-File-Name    pic x(14)       value spaces. *>  Ditto.
     03  WS-Operation    pic x(7)        value spaces. *>  Ditto.
     03  Error-Code      pic 999         value zero.   *>  Ditto.
     03  WS-Error-Op     pic 99          value zero.   *>  Ditto.
*>
 01  WS-Test-Date            pic x(10).
 01  WS-Date-formats.
     03  WS-swap             pic xx.
     03  WS-Conv-Date        pic x(10).
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
 01  Error-Messages.
*> System Wide    Used are 6,7,8,9
     03  SY006           pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007           pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008           pic x(31) value "SY008 Note message & Hit return".
     03  SY009           pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
*>
     03  XL001          pic x(31) value "XL001 Aborting. Press return   ".
*>    03  XL011           pic x(25) value "XL011 Note and hit Return".
*> Module specific
     03  XL101          pic x(37) value "XL101 Proofed but NOT posted invoices".
     03  XL102          pic x(37) value "XL102 Proofed but NOT posted payments".
     03  XL103          pic x(37) value "XL103 Sales/Purchase Analysis NOT run".
     03  XL104          pic x(64) value "XL104 I'm confused: You appear to have rejected the run, Aborted".
     03  XL105          pic x(32) value "XL105 ERROR.... Processing file ".
     03  XL106          pic x(38) value "XL106 Purchase Transactions Not Posted".
     03  XL107          pic x(35) value "XL107 Sales Transactions Not Posted".
     03  XL108          pic x(45) value "XL108 Running Sales/Purchase Analysis reports".
     03  XL116          pic x(35) value "XL116 End of year; VALUE Data reset".
     03  XL117          pic x(27) value "XL117 Value Data on Update ".
     03  XL118.       *> 47 chars  Used for common file error reporting.
         05  filler     pic x(15) value "XL118 Error on ".
         05  XL118B     pic x(08) value spaces.    *> Open, Read, Write, delete, rewrite.
         05  filler     pic x(10) value "with File ".
         05  XL118C     pic x(14) value spaces.
                        *> Sales, Purchase, OTM3, OTM5, Sinvoice, Pinvoice.
     03  XL119          pic x(43) value "XL119 Error/s when running Analysis Report.".
*>
 linkage Section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wssys4.cob".
 copy "wsnames.cob".
*>
 01  To-Day              pic x(10).
*>
 procedure division using WS-Calling-Data
                          System-Record
                          System-Record-4
                          To-Day
                          File-Defs.
*>=======================================
 aa00-Main Section.
*>
*> Prior to being called, System param & the system total records have been
*>   read in and passed via linkage by sales, purchase.
*>         THIS program is only called by these two.14/01/18.
*>
*> During the run, program will check to see if RDB processing is on and if so
*>   reduce the usage of intermediate file processing by just deleting dead rows.
*>
*> For Cobol files the file clean ups will occur at start New Year only.
*>  and all temp files cleared done to zero size.
*>
*> So existing code modified to process for new quarter deleting dead records.
*>
*>  New Year processing to use intermediate Cobol files if processing files.
*>  For RDB will use a sql utility to clean up tables or the BAsic method of
*>   making a BAck up of the SQL and data and then restoring it.
*>
*>
     perform  zz020-Get-Program-Args.
*>
     Accept   WS-env-lines from lines.
     if       WS-env-lines < 24
              move  24 to WS-env-lines WS-lines
     else
              move  WS-env-lines to WS-lines
     end-if
     subtract 1 from WS-lines giving WS-23-lines.
     subtract 2 from WS-lines giving WS-22-lines.
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     perform  aa030-Display-Heads.
*>
*> get today as binary to use in compares with data files
*>
     move     zero  to  u-bin.
     move     to-day to u-Date.
     call     "maps04"  using  maps03-ws.
*>
 aa010-Acpt-Reply.
     move     space to WS-Found-Error.  *> JIC
     move     "N" to WS-Reply.
*>
*> First block is for AUTO run via sales or purchase menu program when given 2 params
*>   sales    NULL xl150spx
*>    OR
*>   purchase NULL xl150spx
*>
     if       function lower-case (WS-CD-Args (1:5)) not = "xl150"
              go to aa012-Display-Warnings.
*>
*>  So it is AUTO RUN
*>
     go       to aa015-Recheck-for-Issues.
*>
 aa012-Display-Warnings.
     display  "THIS PROGRAM IS DESTRUCTIVE - ENSURE YOU HAVE RUN A BACK UP FIRST" at 0301 with foreground-color 4 highlight.
     display  "WARNING: MAKE SURE THAT DATE IS AT END OF CYCLE. I.E., END OF MONTH" at 0501 with foreground-color 4.
     display  "All Invoices, Payments have been proofed & posted and Analysis reports run" at 0601 with foreground-color 4.
     display   "  For both Sales and Purchase Ledgers" at 0701 with foreground-color 4.
     display   "  That NO ONE else is using the ACAS system" at 0801 with foreground-color 4.
     display  "Have you made a Backup of ALL DATA FILES? If so; "               at 1012 with foreground-color 2.
     display  "Confirm end of Cycle Processing to be Run (Y/N) - [ ]" at 1112 with foreground-color 2.
     ACcept   WS-Reply at 1163 with foreground-color 6 update UPPER.
*>
     if       WS-Reply = "N"        *> WS-Term-Code = 2
              go to  aa990-Menu-Error.
*>
     if       WS-Reply not = "Y"
              go to aa010-Acpt-Reply.
     display  space at 0301 with erase eos.
*>
 aa015-Recheck-for-Issues.
*>
*> Check code changed so that all warnings will be displayed if problems found
*>  But first check for analysis reports as xl150 can be run from sales, purchase
*>      or standalone and if not, will run sl130 and/or pl130 if not run.
*>
     move     zeros to WS-Term-Code.
     if       S-Flag-A = 1             *> Sales    or
          or  P-Flag-A = 1             *> Purchase Analysis not run.
              display XL103   at 1401 with foreground-color 4
              display XL108   at 1501 with foreground-color 2
              if       S-Flag-A = 1
                       move WS-Calling-Data to WS-Backup-Calling-Data
                       move "sl130" to WS-Called
                       move "xl150" to WS-Caller
                       call WS-caller using  WS-calling-data
                                             System-Record
                                             to-day
                                             file-defs
              end-if
              move     WS-Term-Code to Return-Code
              if       P-Flag-A = 1
                       move WS-Calling-Data to WS-Backup-Calling-Data
                       move "pl130" to WS-Called
                       move "xl150" to WS-Caller
                       call WS-caller using  WS-calling-data
                                             System-Record
                                             to-day
                                             file-defs
              end-if
              Add      WS-Term-Code to Return-Code
              move     Return-Code to WS-Term-Code *> JIC there is a later Test for it
              if       Return-Code  > zero       *> had errors running pl130 or sl130
                       display XL119    at 1601 with foreground-color 4
                       display XL001    at 1701 with foreground-color 2
                       ACcept  WS-Reply at 1732 with foreground-color 2
                       go to aa990-Menu-Error
              end-if
              move WS-Backup-Calling-Data to WS-Calling-Data
     end-if
*>
*> Now the Errors that the user MUST fix, e.g., by running uncompleted processes.
*>
     if       S-Flag-I = 1      *> Sales Ledger    - Unposted invoices exist
        or    P-Flag-I = 1      *> Purchase Ledger - Unposted invoices exist
              display XL101 at 1101 with foreground-color 4
              move "Y" to WS-Found-Error
     end-if
     if      (S-Flag-P = 1 or 2)        *>  Sales   or
         or  (P-Flag-P = 1 or 2)        *>  Purchase payments Proofed not posted.
              display XL102 at 1201 with foreground-color 4
              move "Y" to WS-Found-Error
     end-if
*>
*> Check if errors found and ABort as I cannot know if amended invoices exist or any other
*>   reason for a invoice reprint via sl930 and likewise for packing/picking notes sl950
*>     Running is too risky so let user decide.
*>
      if      WS-Found-Error = "Y"
              display XL001 at 1301 with foreground-color 2   *> was 1301
              ACcept WS-Reply at 1331  with foreground-color 2 update
              go to aa990-Menu-Error.
*>
 aa020-Request-Ledgers.  *> automation by calling xl150 with arguments via BAsh command etc.
     if       function lower-case (WS-CD-Args (1:5)) = "xl150"
        if    (function lower-case (WS-CD-Args (6:1)) = "s"
           or function lower-case (WS-CD-Args (7:1)) = "s")
              move 1 to SL-EoC.    *> will run SL
*>
     if       function lower-case (WS-CD-Args (1:5)) = "xl150"
        if    (function lower-case (WS-CD-Args (6:1)) = "p"
           or function lower-case (WS-CD-Args (7:1)) = "p")
              move 1 to PL-EoC.    *> Will run PL
*>
     if       function lower-case (WS-CD-Args (1:5)) = "xl150"
        and   PL-EoC = zero
        and   SL-EoC = zero
              go to aa024-Test-EoC.
     if       function lower-case (WS-CD-Args (1:5)) = "xl150"
              go to aa025-OTM-Checks.
*>
     if       S-L
              display "Do you wish to run Sales Ledger? (Y/N) - [ ]"   at 1801 with foreground-color 2
              ACcept WS-Reply at 1843 with foreground-color 6 UPPER
              if  WS-Reply = "Y"
                  move 1 to SL-EoC.
     if       B-L
              display "Do you wish to run Purchase Ledger? (Y/N) - [ ]" at 1901 with foreground-color 2.
              ACcept WS-Reply at 1946 with foreground-color 6 UPPER
              if  WS-Reply = "Y"
                  move 1 to PL-EoC.
*>
 aa024-Test-EoC.
     if       zero = SL-EoC and PL-EoC             *> if none selected then user wants to quit.
              display XL104 at 0301 with foreground-color 4 erase eos
              go to aa990-Menu-Error.
*>
 aa025-OTM-Checks.
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-29     *> OTM5 (Purch)
                                                 File-Info
              if    return-code not = zero  and PL-EoC = 1   *> not = zero - No file found
                    display XL106   at 0501 with foreground-color 4 erase eos
                    move zero to PL-EoC.               *> As no transactions. Omit processing
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-19     *> OTM3 (Sales)
                                                 File-Info
              if    return-code not = zero and SL-EoC = 1    *> not = zero - No file found
                    display XL107   at 0601 with foreground-color 4 erase eos
                    move zero to SL-EoC.               *> As no transactions. Omit processing
*>
*> Final run check in case OTM3 or OTM5 not exist
*>
     if      zero = SL-EoC and PL-EoC             *> if none so quit.
             display XL106   at 0501 with foreground-color 4 erase eos
             display XL107   at 0601 with foreground-color 4
             go to aa990-Menu-Error.
*>
 aa030-Display-Heads.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "End of Cycle Processing" at 0130  with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-Date at 0171 with foreground-color 2.
     move     1  to File-Key-No.
*>
 aa040-Display-End.
     perform  BD00-Check-End-of-Cycle.
     if       SL-EoC = 1
              perform AB00-SL-Processing
              move u-bin to S-End-Cycle-Date.
     if       PL-EoC = 1
              perform AC00-PL-Processing
              move u-bin to BL-End-Cycle-Date.
*>
 aa050-EOY-Processing.
*>
*> New period / quarter / year has been done so now to remove dead records
*>  cleaning up indexes and empty space on Cobol files.
*>
*>  If using RDBMS tables then this is skipped as it will be handled by running
*>   a RDB BAckup  of tables and data then restoring.
*>  NOTE that the created SQL must contain DROP TABLES prior to reloading.
*>
     if       not FS-Cobol-Files-Used    *> I.e., RDBMS
              go to aa970-Menu-Exit.
*>
     if       New-Year not = 1           *> Only do at year end.
              go to aa970-Menu-Exit.
*>
 aa100-Phase-6.
*>
*> Get on with read / write to temp files and reload ISAM files.
*>   First Sales ledger, OTM3 and invoice files.
*>
*> Tests for all open, read, write on prime and temp files.
*>   Yes, a bit of over kill but JIC.
*>
     display  "6A - Sales" at 1207 with foreground-color 2.
     perform  Sales-Open-Input.
     if       FS-Reply not = zero
              perform aa812-Error-on-Open-Sales
              perform  Sales-Close
              go to aa991-File-Error-Exit
     end-if
     open     output Temp-Sales-File.
     if       FS-Reply not = zero
              perform  aa813-Error-on-Open-Temp-Sales
              close    Temp-Sales-File
              perform  Sales-Close
              go to aa991-File-Error-Exit
     end-if
*>
     perform  until FS-Reply = 10
              perform  Sales-Read-Next
              if       FS-Reply = 10   *> extra protection
                       exit perform
              end-if
              if       FS-Reply not = zero
                       perform  aa801-Error-on-Read-Sales
                       close    Temp-Sales-File
                       perform  Sales-Close
                       go to aa991-File-Error-Exit
              end-if
              write    Temp-Sales-Record from WS-Sales-Record
              if       FS-Reply not = zero
                       perform aa802-Error-on-Write-Temp-Sales
                       close    Temp-Sales-File
                       perform  Sales-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     close    Temp-Sales-File.
     perform  Sales-Close.
*>
     display  "B"  at 1208 with foreground-color 2.
     open     input Temp-Sales-File.
     if       FS-Reply not = zero
              perform  aa813-Error-on-Open-Temp-Sales
              close Temp-Sales-File
              go to aa991-File-Error-Exit
     end-if
     perform  Sales-Open-Output.
     if       FS-Reply not = zero
              perform aa812-Error-on-Open-Sales
              close   Temp-Sales-File
              perform Sales-Close
              go to aa991-File-Error-Exit
     end-if
     perform  until FS-Reply = 10
              read Temp-Sales-File into WS-Sales-Record at end
                   exit perform
              end-read
              if       FS-Reply not = zero
                       perform aa803-Error-on-Read-Temp-Sales
                       close   Temp-Sales-File
                       perform Sales-Close
                       go to aa991-File-Error-Exit
              end-if
              perform  Sales-Write
              if       FS-Reply not = zero
                       perform aa804-Error-on-Write-Sales
                       close   Temp-Sales-File
                       perform Sales-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     perform  Sales-Close.
     close    Temp-Sales-File.
     open     output Temp-Sales-File.     *> Clear the temp file. keep things tidy.
     close    Temp-Sales-File.
*>
 aa110-Phase-7.
     display  "7A" at 1207 with foreground-color 2.
     open     output Open-Item-File-S.
     if       FS-Reply not = zero
              perform aa815-Error-on-Open-Temp-OTM3
              close Open-Item-File-S
              go to aa991-File-Error-Exit
     end-if
     perform  OTM3-Open-Input.
     if       FS-Reply not = zero
              perform aa814-Error-on-Open-OTM3
              perform  OTM3-Close
              close Open-Item-File-S
              go to aa991-File-Error-Exit
     end-if
     perform  until FS-Reply = 10
              perform  OTM3-Read-Next
              if       FS-Reply = 10
                       exit perform
              end-if
              if       FS-Reply not = zero
                       perform aa800-Error-on-Read-OTM3
                       perform  OTM3-Close
                       close Open-Item-File-S
                       go to aa991-File-Error-Exit
              end-if
              write  Open-Item-Record-S from WS-OTM3-Record
              if       FS-Reply not = zero
                       perform aa806-Error-on-Write-Temp-OTM3
                       perform  OTM3-Close
                       close Open-Item-File-S
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     close    Open-Item-File-S.
     perform  OTM3-Close.
*>
     open     input Open-Item-File-S.
     if       FS-Reply not = zero
              perform aa815-Error-on-Open-Temp-OTM3
              close Open-Item-File-S
              go to aa991-File-Error-Exit
     end-if
     perform  OTM3-Open-Output.
     if       FS-Reply not = zero
              perform aa814-Error-on-Open-OTM3
              close Open-Item-File-S
              perform  OTM3-Close
              go to aa991-File-Error-Exit
     end-if
     display  "B" at 1208 with foreground-color 2.
     perform  until FS-Reply = 10
              read Open-Item-File-S into WS-OTM3-Record at end
                   exit perform
              end-read
              if       FS-Reply not = zero
                       perform aa807-Error-on-Read-Temp-OTM3
                       close Open-Item-File-S
                       perform  OTM3-Close
                       go to aa991-File-Error-Exit
              end-if
              perform  OTM3-Write
              if       FS-Reply not = zero
                       perform aa805-Error-on-Write-OTM3
                       close Open-Item-File-S
                       perform  OTM3-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     perform  OTM3-Close.
     close    Open-Item-File-S.
     open     output Open-Item-File-S.     *> Clear the temp OTM file.
     close    Open-Item-File-S.
*>
 aa120-Phase-8.
     display  "8A" at 1207 with foreground-color 2.
     perform  Invoice-Open-Input.    *> SALES
     if       FS-Reply not = zero
              perform aa816-Error-on-Open-SInvoices
              perform  Invoice-Close
              go to aa991-File-Error-Exit
     end-if
     open     output  Temp-Invoice-File.
     if       FS-Reply not = zero
              perform aa817-Error-on-Open-Temp-SInvoices
              close  Temp-Invoice-File
              perform  Invoice-Close
              go to aa991-File-Error-Exit
     end-if
*>
     perform  until FS-Reply = 10
              perform  Invoice-Read-Next
              if       FS-Reply = 10   *> extra protection
                       exit perform
              end-if
              if       FS-Reply not = zero
                       perform aa808-Error-on-Read-SInvoices
                       close  Temp-Invoice-File
                       perform  Invoice-Close
                       go to aa991-File-Error-Exit
              end-if
              write  Temp-Invoice-Record from WS-Invoice-Record
              if       FS-Reply not = zero
                       perform aa809-Error-on-Write-Temp-SInvoices
                       close  Temp-Invoice-File
                       perform  Invoice-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     close    Temp-Invoice-File.
     perform  Invoice-Close.
*>
     display  "B" at 1208 with foreground-color 2.
     open     Input Temp-Invoice-File.
     if       FS-Reply not = zero
              perform aa817-Error-on-Open-Temp-SInvoices
              close Temp-Invoice-File
              go to aa991-File-Error-Exit
     end-if
     perform  Invoice-Open-Output.
     if       FS-Reply not = zero
              perform aa816-Error-on-Open-SInvoices
              close Temp-Invoice-File
              perform Invoice-Close
              go to aa991-File-Error-Exit
     end-if
     perform  until FS-Reply = 10
              read Temp-Invoice-File into WS-Invoice-Record at end
                   exit perform
              end-read
              if       FS-Reply not = zero
                       perform aa810-Error-on-Read-Temp-SInvoices
                       close Temp-Invoice-File
                       perform Invoice-Close
                       go to aa991-File-Error-Exit
              end-if
              perform  Invoice-Write
              if       FS-Reply not = zero
                       perform aa811-Error-on-Write-SInvoices
                       close Temp-Invoice-File
                       perform Invoice-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     perform  Invoice-Close.
     close    Temp-Invoice-File.
     open     output Temp-Invoice-File.     *> Clear the temp invoice file. keep things tidy.
     close    Temp-Invoice-File.
*>
*>  PL
*>
 aa130-Phase-9.
     display  " 9A - Purchase" at 1207 with foreground-color 2.
*>
*> Get on with read /write to temp files and reload ISAM files.
*>   For Purchase Ledger, OTM5 and Pinvoice files.
*>
     perform  Purch-Open-Input.
     if       FS-Reply not = zero
              perform aa912-Error-on-Open-Purchase
              perform  Purch-Close
              go to aa991-File-Error-Exit
     end-if
     open     output Temp-Purchase-File.
     if       FS-Reply not = zero
              perform  aa913-Error-on-Open-Temp-Purchase
              close    Temp-Purchase-File
              perform  Purch-Close
              go to aa991-File-Error-Exit
     end-if
*>
     perform  until FS-Reply = 10
              perform  Purch-Read-Next
              if       FS-Reply = 10   *> extra protection
                       exit perform
              end-if
              if       FS-Reply not = zero
                       perform  aa901-Error-on-Read-Purchase
                       close    Temp-Purchase-File
                       perform  Purch-Close
                       go to aa991-File-Error-Exit
              end-if
              write    Temp-Purch-Record from WS-Purch-Record
              if       FS-Reply not = zero
                       perform aa902-Error-on-Write-Temp-Purchase
                       close    Temp-Purchase-File
                       perform  Purch-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     close    Temp-Purchase-File.
     perform  Purch-Close.
*>
     display  "B"  at 1209 with foreground-color 2.
     open     input Temp-Purchase-File.
     if       FS-Reply not = zero
              perform  aa913-Error-on-Open-Temp-Purchase
              close Temp-Purchase-File
              go to aa991-File-Error-Exit
     end-if
     perform  Purch-Open-Output.
     if       FS-Reply not = zero
              perform aa912-Error-on-Open-Purchase
              close   Temp-Purchase-File
              perform Purch-Close
              go to aa991-File-Error-Exit
     end-if
     perform  until FS-Reply = 10
              read Temp-Purchase-File into WS-Purch-Record at end
                   exit perform
              end-read
              if       FS-Reply not = zero
                       perform aa903-Error-on-Read-Temp-Purchase
                       close   Temp-Purchase-File
                       perform Purch-Close
                       go to aa991-File-Error-Exit
              end-if
              perform  Purch-Write
              if       FS-Reply not = zero
                       perform aa904-Error-on-Write-Purchase
                       close   Temp-Purchase-File
                       perform Purch-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     perform  Purch-Close.
     close    Temp-Purchase-File.
     open     output Temp-Purchase-File.     *> Clear the temp file.
     close    Temp-Purchase-File.
*>
 aa140-Phase-10.
     display  "10A" at 1207 with foreground-color 2.
     open     output Open-Item-File-S.
     if       FS-Reply not = zero
              perform aa915-Error-on-Open-Temp-OTM5
              close Open-Item-File-S
              go to aa991-File-Error-Exit
     end-if
     perform  OTM5-Open-Input.
     if       FS-Reply not = zero
              perform aa914-Error-on-Open-OTM5
              perform  OTM5-Close
              close Open-Item-File-S
              go to aa991-File-Error-Exit
     end-if
     perform  until FS-Reply = 10
              perform  OTM5-Read-Next
              if       FS-Reply = 10
                       exit perform
              end-if
              if       FS-Reply not = zero
                       perform aa900-Error-on-Read-OTM5
                       perform  OTM5-Close
                       close Open-Item-File-S
                       go to aa991-File-Error-Exit
              end-if
              write  Open-Item-Record-S from WS-OTM5-Record
              if       FS-Reply not = zero
                       perform aa906-Error-on-Write-Temp-OTM5
                       perform  OTM5-Close
                       close Open-Item-File-S
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     close    Open-Item-File-S.
     perform  OTM5-Close.
*>
     open     input Open-Item-File-S.
     if       FS-Reply not = zero
              perform aa915-Error-on-Open-Temp-OTM5
              close Open-Item-File-S
              go to aa991-File-Error-Exit
     end-if
     perform  OTM5-Open-Output.
     if       FS-Reply not = zero
              perform aa914-Error-on-Open-OTM5
              close Open-Item-File-S
              perform  OTM5-Close
              go to aa991-File-Error-Exit
     end-if
     display  "B" at 1209 with foreground-color 2.
     perform  until FS-Reply = 10
              read Open-Item-File-S into WS-OTM5-Record at end
                   exit perform
              end-read
              if       FS-Reply not = zero
                       perform aa907-Error-on-Read-Temp-OTM5
                       close Open-Item-File-S
                       perform  OTM5-Close
                       go to aa991-File-Error-Exit
              end-if
              perform  OTM5-Write
              if       FS-Reply not = zero
                       perform aa905-Error-on-Write-OTM5
                       close Open-Item-File-S
                       perform  OTM5-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     perform  OTM5-Close.
     close    Open-Item-File-S.
     open     output Open-Item-File-S.     *> Clear the temp OTM file.
     close    Open-Item-File-S.
*>
 aa150-Phase-11.
     display  "11A" at 1207 with foreground-color 2.
     perform  PInvoice-Open-Input.    *> PURCHASE
     if       FS-Reply not = zero
              perform aa916-Error-on-Open-PInvoices
              perform  PInvoice-Close
              go to aa991-File-Error-Exit
     end-if
     open     output  Temp-Invoice-File.
     if       FS-Reply not = zero
              perform aa917-Error-on-Open-Temp-PInvoices
              close  Temp-Invoice-File
              perform  PInvoice-Close
              go to aa991-File-Error-Exit
     end-if
*>
     perform  until FS-Reply = 10
              perform  PInvoice-Read-Next
              if       FS-Reply = 10   *> extra protection
                       exit perform
              end-if
              if       FS-Reply not = zero
                       perform aa908-Error-on-Read-PInvoices
                       close  Temp-Invoice-File
                       perform  PInvoice-Close
                       go to aa991-File-Error-Exit
              end-if
              write  Temp-Invoice-Record from WS-PInvoice-Record
              if       FS-Reply not = zero
                       perform aa909-Error-on-Write-Temp-PInvoices
                       close  Temp-Invoice-File
                       perform  PInvoice-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     close    Temp-Invoice-File.
     perform  PInvoice-Close.
*>
     display  "B" at 1209 with foreground-color 2.
     open     Input Temp-Invoice-File.
     if       FS-Reply not = zero
              perform aa917-Error-on-Open-Temp-PInvoices
              close Temp-Invoice-File
              go to aa991-File-Error-Exit
     end-if
     perform  PInvoice-Open-Output.
     if       FS-Reply not = zero
              perform aa916-Error-on-Open-PInvoices
              close Temp-Invoice-File
              perform PInvoice-Close
              go to aa991-File-Error-Exit
     end-if
     perform  until FS-Reply = 10
              read Temp-Invoice-File into WS-PInvoice-Record at end
                   exit perform
              end-read
              if       FS-Reply not = zero
                       perform aa910-Error-on-Read-Temp-PInvoices
                       close Temp-Invoice-File
                       perform PInvoice-Close
                       go to aa991-File-Error-Exit
              end-if
              perform  PInvoice-Write
              if       FS-Reply not = zero
                       perform aa911-Error-on-Write-PInvoices
                       close Temp-Invoice-File
                       perform PInvoice-Close
                       go to aa991-File-Error-Exit
              end-if
     end-perform
     perform  PInvoice-Close.
     close    Temp-Invoice-File.
     open     output Temp-Invoice-File.     *> Clear the temp invoice file.
     close    Temp-Invoice-File.
*>
     go       to aa970-Menu-Exit.           *> EOJ
*>
*> Error Routines used in aa-Main.
*>
*>   SL Error Routines.
*>
 aa800-Error-on-Read-OTM3.
     move     2 to WS-Operation.
     move     802 to Error-Code.
     perform  aa950-Display-File-Error.

 aa801-Error-on-Read-Sales.
     move     2 to WS-Operation.
     move     801 to Error-Code.
     perform  aa950-Display-File-Error.

 aa802-Error-on-Write-Temp-Sales.
     move     3 to WS-Operation.
     move     804 to Error-Code.
     perform  aa950-Display-File-Error.

 aa803-Error-on-Read-Temp-Sales.
     move     2 to WS-Operation.
     move     804 to Error-Code.
     perform  aa950-Display-File-Error.

 aa804-Error-on-Write-Sales.
     move     3 to WS-Operation.
     move     801 to Error-Code.
     perform  aa950-Display-File-Error.

 aa805-Error-On-Write-OTM3.
     move     3 to WS-Operation.
     move     802 to Error-Code.
     perform  aa950-Display-File-Error.

 aa806-Error-on-Write-Temp-OTM3.
     move     3 to WS-Operation.
     move     805 to Error-Code.
     perform  aa950-Display-File-Error.

 aa807-Error-on-Read-Temp-OTM3.
     move     2 to WS-Operation.
     move     805 to Error-Code.
     perform  aa950-Display-File-Error.

 aa808-Error-on-Read-SInvoices.
     move     2 to WS-Operation.
     move     803 to Error-Code.
     perform  aa950-Display-File-Error.

 aa809-Error-on-Write-Temp-SInvoices.
     move     3 to WS-Operation.
     move     806 to Error-Code.
     perform  aa950-Display-File-Error.

 aa810-Error-on-Read-Temp-SInvoices.
     move     2 to WS-Operation.
     move     806 to Error-Code.
     perform  aa950-Display-File-Error.

 aa811-Error-on-Write-SInvoices.
     move     3 to WS-Operation.
     move     803 to Error-Code.
     perform  aa950-Display-File-Error.

 aa812-Error-on-Open-Sales.
     move     1 to WS-Operation.
     move     801 to Error-Code.
     perform  aa950-Display-File-Error.

 aa813-Error-on-Open-Temp-Sales.
     move     1 to WS-Operation.
     move     804 to Error-Code.
     perform  aa950-Display-File-Error.

 aa814-Error-on-Open-OTM3.
     move     1 to WS-Operation.
     move     802 to Error-Code.
     perform  aa950-Display-File-Error.

 aa815-Error-on-Open-Temp-OTM3.
     move     1 to WS-Operation.
     move     805 to Error-Code.
     perform  aa950-Display-File-Error.

 aa816-Error-on-Open-SInvoices.
     move     1 to WS-Operation.
     move     803 to Error-Code.
     perform  aa950-Display-File-Error.

 aa817-Error-on-Open-Temp-SInvoices.
     move     1 to WS-Operation.
     move     806 to Error-Code.
     perform  aa950-Display-File-Error.
*>
*>  PL / BL Error Routines.
*>
 aa900-Error-on-Read-OTM5.
     move     2 to WS-Operation.
     move     808 to Error-Code.
     perform  aa950-Display-File-Error.

 aa901-Error-on-Read-Purchase.
     move     2 to WS-Operation.
     move     807 to Error-Code.
     perform  aa950-Display-File-Error.

 aa902-Error-on-Write-Temp-Purchase.
     move     3 to WS-Operation.
     move     810 to Error-Code.
     perform  aa950-Display-File-Error.

 aa903-Error-on-Read-Temp-Purchase.
     move     2 to WS-Operation.
     move     810 to Error-Code.
     perform  aa950-Display-File-Error.

 aa904-Error-on-Write-Purchase.
     move     3 to WS-Operation.
     move     807 to Error-Code.
     perform  aa950-Display-File-Error.

 aa905-Error-On-Write-OTM5.
     move     3 to WS-Operation.
     move     808 to Error-Code.
     perform  aa950-Display-File-Error.

 aa906-Error-on-Write-Temp-OTM5.
     move     3 to WS-Operation.
     move     811 to Error-Code.
     perform  aa950-Display-File-Error.

 aa907-Error-on-Read-Temp-OTM5.
     move     2 to WS-Operation.
     move     811 to Error-Code.
     perform  aa950-Display-File-Error.

 aa908-Error-on-Read-PInvoices.
     move     2 to WS-Operation.
     move     809 to Error-Code.
     perform  aa950-Display-File-Error.

 aa909-Error-on-Write-Temp-PInvoices.
     move     3 to WS-Operation.
     move     812 to Error-Code.
     perform  aa950-Display-File-Error.

 aa910-Error-on-Read-Temp-PInvoices.
     move     2 to WS-Operation.
     move     812 to Error-Code.
     perform  aa950-Display-File-Error.

 aa911-Error-on-Write-PInvoices.
     move     3 to WS-Operation.
     move     809 to Error-Code.
     perform  aa950-Display-File-Error.

 aa912-Error-on-Open-Purchase.
     move     1 to WS-Operation.
     move     807 to Error-Code.
     perform  aa950-Display-File-Error.

 aa913-Error-on-Open-Temp-Purchase.
     move     1 to WS-Operation.
     move     810 to Error-Code.
     perform  aa950-Display-File-Error.

 aa914-Error-on-Open-OTM5.
     move     1 to WS-Operation.
     move     808 to Error-Code.
     perform  aa950-Display-File-Error.

 aa915-Error-on-Open-Temp-OTM5.
     move     1 to WS-Operation.
     move     811 to Error-Code.
     perform  aa950-Display-File-Error.

 aa916-Error-on-Open-PInvoices.
     move     1 to WS-Operation.
     move     809 to Error-Code.
     perform  aa950-Display-File-Error.

 aa917-Error-on-Open-Temp-PInvoices.
     move     1 to WS-Operation.
     move     812 to Error-Code.
     perform  aa950-Display-File-Error.
*>
 aa950-Display-File-Error.
*>
*> Have WS-File-Name, WS-Operation and WS-Msg.
*>
     perform  AB995-Eval-Status.
     move     WS-Operation  to XL118B.
     move     WS-File-Name  to XL118C.
     display  XL118 at line WS-23-Lines col  1 with foreground-color 4 erase eos.
     display  XL001 at line WS-Lines    col  1 with foreground-color 4.
     ACcept   WS-Reply at line WS-Lines col 31 with foreground-color 2.
 *>    go       to aa991-File-Error-Exit.
*>
 aa970-Menu-Exit.
*>
*>  Really ?  This should already be set by sales and purchase
*>       When OTM3 and OTM5 has data or been created for files in
*>            sl060  and pl060. But as it only says run p/sl115 sort leave it.
*>
     if       SL-EoC = 1
              move "Y" to oi-3-flag. *> sl060 sets S-Flag-I=2,S-Flag-A=1
     if       PL-EoC = 1
              move "Y" to oi-5-flag. *> pl060 sets P-Flag-I=2(invoice lines),P-Flag-A=1(Applied recs)
*>
 aa980-Menu-Exit.
     goback.
*>
 aa990-Menu-Error.
     move     2 to WS-term-code.
     goback.
 *> was 14/01/18    go       to aa970-Menu-Exit.
*>
 aa991-File-Error-Exit.
     move     3 to WS-Term-Code.
     goback.
*>
*>******************************************************
*>                     Procedures                      *
*>******************************************************
*>
*> Sections :
*> AB00-SL-Processing
*> AC00-PL-Processing
*> AD00-kill-invoicep
*> AE00-Kill-Invoices
*> BA00-Value-Reset
*> BD00-Check-End-of-Cycle
*>
 AB00-SL-Processing           Section.
*>==============================
*>
     display  "Phase 1  - Sales" at 1201 with foreground-color 2.
     display  "*******" at 1301 with foreground-color 2.
     display  "Please wait." at 1501 with foreground-color 2.
*>
*> 1st. Read ledger recs & Update stats and move then to last etc and save recs
*>   setting accct to Dead if no activity
*> 2nd. Invoices & OTM3 - if OTM3 inv. closed delete rec and Inv. recs
*>
*>


*>     This is done quarterly? Monthly - could it only be yearly ?
*>  Processing Sales Ledger file & @ EOC reload ledger from temp file
*>   only will clear out deleted rec areas in index & file so temp
*>    process not needed for RDB processing NOR ISAM Cobol files.
*>
*>  LATER Code now skipped as ISAM recs will be updated or deleted and
*>   End of year the files will be clean up removing empty data areas on
*>    the hard drive/s. For RDB users run the RDB clean up process instead.
*>
     display "A" at 1208 with foreground-color 2.
     perform  Sales-Open.
*>
 AB010-Phase-1-Read.    *> Sales-Ledger file/record
     perform  Sales-Read-Next.
     if       FS-Reply = 10
              go to  AB020-Phase-1-End.
*> Not live ?
     if       Sales-Current = zero
         and  Sales-Last    = zero
         and  Sales-Unapplied = zero
              move zero to  Sales-Status.  *> no activity so Set status to Dead
*>
     if       Sales-Current is negative
              multiply -1 by Sales-Current
              ADd Sales-Current to Sales-Unapplied
              move zero to Sales-Current.
*>
     move     Sales-Current  to  Sales-Last.
*>
     if       new-quarter = 1
              move  zero  to  STurnover-Q (Current-Quarter).
*>
     if       New-Year = 1
              move zero to Sales-Average
                           Sales-Activety.
*>
     perform  Sales-Rewrite.
     if       FS-Reply not = zero
              go to AB998-Error-On-Sales-Rewrite.
     go to    AB010-Phase-1-Read.
*>
 AB020-Phase-1-End.
     perform  Sales-Close.
*>
*>  Now for OTM3 - Open Item & Sales invoices data
*>
     display  "2A" at 1207 with foreground-color 2.
*>
     perform  OTM3-Open.
     perform  Invoice-Open.
*>
 AB060-Phase-2-Read.
     perform  OTM3-Read-Next.
     if       FS-Reply = 10
              go to  AB070-Phase-2-End.
 *>     move     WS-OTM3-Record to Soi-Header.    *> is redefines
*>
     if       ss-closed
              perform AE00-Kill-Invoices    *> all for inv. no.
              perform  OTM3-Delete       *> new 19/01/18
              if       FS-Reply not = zero
                       go to AB997-Error-on-OTM3-Delete
              end-if
              go to AB060-Phase-2-Read.
*>
     if       soi-type = 1        *> receipt (not wanted)
 *> NEW CODE 19/01/18
              perform  OTM3-Delete
              if       FS-Reply not = zero
                       go to AB997-Error-on-OTM3-Delete
              end-if
              go to AB060-Phase-2-Read.
*>
     if       soi-type = 5 or 6   *> payment or Jnl unapplied cash
              move zero to soi-deduct-amt.
*>
     move     "Z" to soi-applied.             *> UC 18/01/18
     move     zero  to  soi-p-c.
*>
     perform  OTM3-Rewrite.
     if       FS-Reply not = zero
              go to AB996-Error-on-OTM3-Rewrite
     end-if
     go       to AB060-Phase-2-Read.
*>
 AB070-Phase-2-End.
     perform  OTM3-Close.
     perform  Invoice-Close.
*>
 AB100-Phase-3-Begin.
*>
*> Here we remove dead records
*>
     display  "3 " at 1207 with foreground-color 2.
     move     "S" to WS-Value-System.   *> see Test in Phase-3
     perform  BA00-Value-Reset.
     display  "4A" at 1207 with foreground-color 2.
*>
     subtract pf-retention from u-bin giving pf-Test.
     subtract 92           from u-bin giving inv-Test.
*>
     perform  Invoice-Open.             *> open     input  sinvoice-file.
 *>**    open     output temp-invoice-file.
*>
 AB110-Phase-4-Read.    *> Sales invoice file/record
     perform  Invoice-Read-Next.        *> read   sinvoice-file next record at end
     if       FS-Reply = 10
              go to AB140-Phase-4-End.
     move     SInvoice-Record to SInvoice-Header.
*>
     if       sih-Test not = zero              *> Keep it.
              go to AB110-Phase-4-Read.      *>   go to AB120-Copy-Record-Out.
*>
     if       not sapplied                     *> Keep it.
              go to AB110-Phase-4-Read.     *> go to AB120-Copy-Record-Out.
*>
     if       sih-type = 4 and              *> Kill out of date Proformas
              pf-Test > sih-Date           *> perform AB130-Skip-Reader sih-lines times
       if     FS-Cobol-Files-Used                     *>    go to AB120-Copy-Record-Out.
              perform  varying  Sitem-Nos from zero by 1
                        until   Sitem-Nos > Sih-Lines
                       perform  Invoice-Delete
              end-perform
       else
              perform  Invoice-Delete-All               *> delete all recs for inv
       end-if
       go to AB110-Phase-4-Read.
*>
     if       sih-type < 4
              move "B" to sih-day-book-flag.
*>
     if       sih-lines not = zero and
              sih-type = 2                  *> ACcount
                                   *> perform AB130-Skip-Reader sih-lines times
              perform  varying  Sitem-Nos from 1 by 1  *> do item-lines only
                         until   Sitem-Nos > Sih-Lines
                       perform  Invoice-Delete
              end-perform
              move zero to sih-lines
              move SInvoice-Header to SInvoice-Record
              perform  Invoice-Rewrite.       *> go to AB120-Copy-Record-Out.
              go to AB110-Phase-4-Read.
*>
     if       sih-type = 1 or 3             *> Receipt or Cr. Note
                                       *> perform AB130-Skip-Reader sih-lines times
       if     FS-Cobol-Files-Used                     *>    go to AB120-Copy-Record-Out.
              perform  varying  Sitem-Nos from zero by 1
                        until   Sitem-Nos > Sih-Lines
                       perform  Invoice-Delete
              end-perform
       else
              perform  Invoice-Delete-All               *> delete all recs for inv
       end-if
       go to AB110-Phase-4-Read.
*> ??
 *>    if       SL-own-nos not = "Y"
 *>             go to AB120-Copy-Record-Out.
*>
*> at this point if ih-type = 2 then ih-lines must be zero
*>
     if       sih-type = 2                  *> ACcount
        and   inv-Test > sih-Date
              perform Invoice-Delete
              go to AB110-Phase-4-Read.
*>
*> No longer used as file now ISAM
*>
 *> AB120-Copy-Record-Out.
 *>    move     SInvoice-Header to SInvoice-Record.
 *>    perform  Invoice-Rewrite.      *>  write    temp-invoice-record from SInvoice-Header.
 *>    go       to AB110-Phase-4-Read.
*>
 *> AB130-Skip-Reader.
 *>    perform     *>  perform  Invoice-Read-Next.            *> read     sinvoice-file next record at end
 *>    if       FS-Reply = 10
 *>             go to AB140-Phase-4-End.
*>
 AB140-Phase-4-End.
    *>   close    temp-invoice-file.            *> sinvoice-file
     perform  Invoice-Close.
*>
 AB170-Phase-6-Sys4-Reset.
*>
*>  Sales now finished.
*>
     display  "5 " at 1207 with foreground-color 2.
     move     SL-os-bal-This-month to SL-os-bal-Last-month.
     move     zeros to SL-os-bal-This-month       SL-variance
                       SL-invoices-This-month     SL-payments
                       SL-credit-deductions       SL-cn-unappl-This-month
                       SL-credit-notes-This-month.
     go       to AB999-main-exit.
 *>
 AB995-Eval-Status.
  copy "FileStat-Msgs.cpy" replacing STATUS by FS-Reply
                                     MSG by WS-Msg.
     if       Error-Code not zero
              evaluate  Error-Code
                when 801  move "Sales"         to WS-File-Name
                when 802  move "OTM3"          to WS-File-Name
                when 803  move "SInvoice"      to WS-File-Name
                when 804  move "Temp Sales"    to WS-File-Name
                when 805  move "Temp OTM3"     to WS-File-Name
                when 806  move "Temp SInvoice" to WS-File-Name
                when 807  move "Purchase"      to WS-File-Name
                when 808  move "OTM5"          to WS-File-Name
                when 809  move "PInvoice"      to WS-File-Name
                when 810  move "Temp Purchase" to WS-File-Name
                when 811  move "Temp OTM5"     to WS-File-Name
                when 812  move "Temp PInvoice" to WS-File-Name
                when other
                          move "Error in AB995" to WS-File-Name
              end-evaluate
     end-if
     if       WS-Error-Op not = zero
              evaluate WS-Error-Op
                when 1    move "Open "   to WS-Operation
                when 2    move "Read "   to WS-Operation
                when 3    move "Write"   to WS-Operation
                when 4    move "Rewrite" to WS-Operation
                when 5    move "Delete"  to WS-Operation
                when other
                          move "ab995bug" to WS-Operation
              end-evaluate
     end-if.
*>
 AB996-Error-on-OTM3-Rewrite.
     move     4   to WS-Operation.
     move     802 to Error-Code.
     perform  aa950-Display-File-Error.
     perform  OTM3-Close.
     perform  Invoice-Close.
     go       to aa990-Menu-Error.
 *>
 AB997-Error-on-OTM3-Delete.
     move     5   to WS-Operation.
     move     802 to Error-Code.
     perform  aa950-Display-File-Error.
     perform  OTM3-Close.
     perform  Invoice-Close.
     go       to aa990-Menu-Error.
*>
 AB998-Error-On-Sales-Rewrite.
     move     4   to WS-Operation.
     move     801 to Error-Code.
     perform  aa950-Display-File-Error.
     perform  Sales-Close.
     go       to aa990-Menu-Error.
*>
 AB999-main-exit.
     exit     Section.
*>
 AE00-Kill-Invoices Section.     *> In Sales invoice file/table.
*>=========================
*>
*> WE have the OTM3 record at this point.
*>
*> Orig code read record before deleting - now just delete them.
*> NOTE: For RDB we can delete in one perform.
*>
     if       soi-type not = 2     *>   ACcount - Only kill these
              go to AE999-Kill-Exit.
*>
     move     soi-invoice to Sinvoice-Nos.  *> set for header from OTM3-rec
     move     zeros       to Sitem-Nos.
*>
     perform  Invoice-Read-Indexed.           *> read     sinvoice-file invalid key
     if       FS-Reply not = zero
              go to AE010-Test-for-Subs.
     move     SInvoice-Record to SInvoice-Header.  *> Copy to WS area.
*>  Delete header
     if       FS-Cobol-Files-Used
              perform  Invoice-Delete                *> delete   sinvoice-file invalid key
     else
              perform  Invoice-Delete-All             *> delete all recs for inv
              go to AE999-Kill-Exit
     end-if
*>
*>  From here we only deal with Cobol file.
*>
     if       sih-lines = zero              *> no, none present
              go to AE999-Kill-Exit.
     perform  AE020-Actual-Delete sih-lines times.
     go       to AE999-Kill-Exit.
*>
 AE010-Test-for-Subs.                      *> used if header missing.
     ADd      1 to Sitem-Nos.
     perform  Invoice-Read-Indexed.            *> read     sinvoice-file invalid key
     if       FS-Reply = 21
              go to AE999-Kill-Exit.
     if       sinvoice-nos not = soi-invoice
              go to AE999-Kill-Exit.
     perform  Invoice-Delete.               *> delete   sinvoice-file invalid key
     if       FS-Reply = 21
              go to AE999-Kill-Exit.
     go       to AE010-Test-for-Subs.
*>
 AE020-Actual-Delete.
     Add      1 to Sitem-Nos.
     perform  Invoice-Delete.                  *> delete   sinvoice-file line recs.
*>
 AE999-Kill-Exit.
     exit     Section.
*>
 AC00-PL-Processing Section.
*>*************************
*>
     display  "Phase 1  - Purchase" at 1201 with foreground-color 2.
     display  "*******"             at 1301 with foreground-color 2.
     display  "Please Wait"         at 1501 with foreground-color 2 blink.
*>
 *>    if       new-quarter = 1
 *>             open output Temp-Purchase-File
 *>             open input  Purchase-file
              display "A" at 1208 with foreground-color 2
 *>      else
     perform  Purch-Open.        *>  open i-o  Purchase-file.
*>
 AC010-Phase-1-Read.    *> Purch-Ledger files/record
     perform  Purch-Read-Next.     *> read     Purchase-file  next record  at end
     if       FS-Reply = 10
              go to  AC020-Phase-1-End.
*>
     if       Purch-Current = zero
         and  Purch-Last    = zero
         and  Purch-Unapplied = zero
              move  zero  to  Purch-Status.
*>
     if       Purch-Current is negative
              multiply -1 by Purch-Current
              ADd Purch-Current to Purch-Unapplied
              move zero to Purch-Current.
*>
     move     Purch-Current  to  Purch-Last.
*>
     if       new-quarter = 1
              move  zero  to  PTurnover-Q (Current-Quarter).
*>
     if       New-Year = 1
              move zero to Purch-Average
                           Purch-Activety.
*>
     perform  Purch-Rewrite.           *> rewrite  Purch-record.
     if       FS-Reply not = zero
              go to AC998-Error-On-Purch-Rewrite.
     go       to    AC010-Phase-1-Read.
*>
 AC020-Phase-1-End.
     perform  Purch-Close.           *> close    Purchase-file.
*>
*> Now for OTM5 - Open Item & Purchase invoices data
*>
     display  "2A" at 1207 with foreground-color 2.
*>
     perform  OTM5-Open.    *>  Its I-O    *> open     input  WS-OTM5-Record.
     perform  Purch-Open.                  *> open     i-o pinvoice-file.
*>
 AC060-Phase-2-Read.
     perform  OTM5-Read-Next.    *> read     WS-OTM5-Record next record into poi-header at end
     if       FS-Reply = 10
              go to  AC070-Phase-2-End.
*>
*>  Data area is now a redefine. (poi-abc, etc)
*>
     if       ps-closed
              perform AD00-kill-invoicep     *> All for inv. no#
              perform  OTM5-Delete       *> new 19/01/18
              if       FS-Reply not = zero
                       go to AC997-Error-on-OTM5-Delete
              end-if
              go to AC060-Phase-2-Read.
     if       poi-type = 1             *> receipt (not wanted)
*> new code 26/01/18
              perform  OTM5-Delete
              if       FS-Reply not = zero
                       go to AC997-Error-on-OTM5-Delete
              end-if
              go to AC060-Phase-2-Read.
     if       poi-type = 5 or 6        *> payment or Jnl unapplied cash
              move zero to poi-deduct-amt.
*>
     move     "Z" to poi-applied.
     move     zero  to  poi-p-c.
*>
     perform  OTM5-Rewrite.
     if       FS-Reply not = zero
              go to AC996-Error-on-OTM5-Rewrite
     end-if
     go       to AC060-Phase-2-Read.
*>
 AC070-Phase-2-End.
     perform  OTM5-Close.    *> close    WS-OTM5-Record open-item-file-s pinvoice-file.
     perform  Pinvoice-Close.
     display  "2B" at 1207 with foreground-color 2.
*>
     display  "3 " at 1207 with foreground-color 2.
     move     "P" to WS-Value-System.   *> see Test in Phase-3
     perform  BA00-Value-Reset.         *> new 17/01/18.
     display  "4A" at 1207 with foreground-color 2.
*>
     perform  Pinvoice-Open.         *> open     input  pinvoice-file.
 *>**    open     output temp-invoice-file.
*>
 AC110-Phase-4-Read.    *> Purchase invoices file/record
     perform  Pinvoice-Read-Next.     *> read  pinvoice-file next record at end
     if       FS-Reply = 10
              go to  AC140-Phase-4-End.
     move     WS-PInvoice-Record to PInvoice-Header.
*>
     if       pih-Test not = zero         *> Keep it
              go to  AC110-Phase-4-Read.    *> go to AC120-Copy-Record-Out.
*>
     if       not papplied                *> Keep it.
              go to  AC110-Phase-4-Read.    *> go to AC120-Copy-Record-Out.
*>
     if       pih-type = 1 or 3             *> Receipt or Cr. Note
                             *>  perform AC130-Skip-Reader pih-lines times
       if     FS-Cobol-Files-Used                     *>    go to AC120-Copy-Record-Out.
              perform  varying  Pitem-Nos from zero by 1
                        until   Pitem-Nos > Pih-Lines
                       perform  PInvoice-Delete
              end-perform
       else
              perform  PInvoice-Delete-All               *> delete all recs for inv
       end-if
       go to AC110-Phase-4-Read.
*>
     if       pih-type < 4
              move "B" to pih-day-book-flag.
*>
*> Kill body lines (& count) keeping header
*>
     if       pih-lines not = zero and
              pih-type = 2
                          *> perform AC130-Skip-Reader pih-lines times
              perform  varying  Pitem-Nos from 1 by 1  *> do item-lines only
                         until   Pitem-Nos > Pih-Lines
                       perform  PInvoice-Delete
              end-perform
              move zero to pih-lines.
*>
*> at this point if PIH-type = 2 then PIH-lines must be zero
*>
 AC120-Copy-Record-Out.                 *> save the rec (rewrite)
     move     PInvoice-Header to WS-PInvoice-Record.
     perform  PInvoice-Rewrite.        *> write    temp-invoice-record from PInvoice-Header.
     go       to AC110-Phase-4-Read.
*>
 *> AC130-skip-reader.
 *>    read     pinvoice-file next record at end
 *>             go to AC140-Phase-4-End.
*>
 AC140-Phase-4-End.
     perform  PInvoice-Close.      *> close    pinvoice-file temp-invoice-file.
*>
 AC170-Phase-6-Sys4-Reset.
     display  "5 " at 1207 with foreground-color 2.
     move     PL-os-bal-This-month to PL-os-bal-Last-month.
     move     zeros to PL-os-bal-This-month       PL-variance
                       PL-invoices-This-month     PL-payments
                       PL-credit-deductions       PL-cn-unappl-This-month
                       PL-credit-notes-This-month.
     go       to  AC999-main-exit.
*>
 AC996-Error-on-OTM5-Rewrite.
     move     4   to WS-Operation.
     move     808 to Error-Code.
     perform  aa950-Display-File-Error.
     perform  OTM5-Close.
     perform  PInvoice-Close.
     go       to aa990-Menu-Error.
*>
 AC997-Error-on-OTM5-Delete.
     move     5   to WS-Operation.
     move     808 to Error-Code.
     perform  aa950-Display-File-Error.
     perform  OTM5-Close.
     perform  PInvoice-Close.
     go       to aa990-Menu-Error.
*>
 AC998-Error-On-Purch-Rewrite.
     move     4   to WS-Operation.
     move     807 to Error-Code.
     perform  aa950-Display-File-Error.
     perform  Purch-Close.
     go       to aa990-Menu-Error.
*>
 AC999-main-exit.
     exit     Section.
*>
 AD00-kill-invoicep Section.
*>=========================
*>
*> WE have the OTM5 record at this point.
*>
*> Orig code read record before deleting - now just delete them.
*> NOTE: For RDB we can delete in one perform.
*>
     if       poi-type not = 2     *>   ACcount - Only kill these
              go to AD999-Kill-Exit.
*>
     move     poi-invoice to Pinvoice-Nos.
     move     zeros       to Pitem-Nos.
*>
     perform  PInvoice-Read-Indexed.      *> read     pinvoice-file invalid key
     if       FS-Reply not = zero
              go to AD010-Test-for-Subs.
     move     WS-PInvoice-Record to PInvoice-Header.  *> Copy to WS area.
*>  Delete header
     if       FS-Cobol-Files-Used
              perform  PInvoice-Delete            *> delete pinvoice-file invalid key
     else
              perform  PInvoice-Delete-All             *> delete all recs for inv
              go to AD999-Kill-Exit
     end-if
*>
*>  From here we only deal with Cobol file.
*>
     if       pih-lines = zero
              go to AD999-Kill-Exit.
     perform  AD020-Actual-Delete pih-lines times.
     go       to AD999-Kill-Exit.
*>
 AD010-Test-for-Subs.
     ADd      1 to Pitem-Nos.
     perform  PInvoice-Read-Indexed.    *> read     pinvoice-file invalid key
     if       FS-Reply = 21
              go to AD999-Kill-Exit.
     if       Pinvoice-Nos not = poi-invoice
              go to AD999-Kill-Exit.
     perform  PInvoice-Delete.          *> delete   pinvoice-file invalid key
     if       FS-Reply = 21
              go to AD999-Kill-Exit.
     go       to AD010-Test-for-Subs.
*>
 AD020-Actual-Delete.
     ADd      1 to Pitem-Nos.
     perform  PInvoice-Delete.       *> delete   pinvoice-file.
*>
 AD999-Kill-Exit.
     exit     Section.
*>
 BD00-Check-End-of-Cycle      Section.
*>===================================
*>
     ADd      1  to  cyclea.
     if       period = 3
              perform  BD010-Monthly-Check
     else
      if      period = 13
              perform  BD020-Weekly-Check
       else
              perform  BD030-Query-Check.
*>
     go       to BD999-main-exit.
*>
 BD010-Monthly-Check.
     if       cyclea = 4  or  7  or 10
              ADd   1  to  Current-Quarter
              move  1  to  new-quarter
     else
      if      cyclea = 13
              move 1 to cyclea
                        Current-Quarter
                        New-Year
                        new-quarter.
*>
 BD020-Weekly-Check.
     if       cyclea = 14  or  27  or  40
              ADd   1  to  Current-Quarter
              move  1  to  new-quarter
     else
      if      cyclea = 53
              move 1 to cyclea
                        Current-Quarter
                        New-Year
                        new-quarter.
*>
 BD030-Query-Check.
*>
*> First Tests if in autorun using Args (8:1) = "y" or "n"
*>
     if       function lower-case (WS-CD-Args (1:5)) = "xl150"
       if     function lower-case (WS-CD-Args (8:1)) = "y"
              move "Y" to WS-Reply
       else
        if    function lower-case (WS-CD-Args (8:1)) = "n"
              move "N" to WS-Reply
        end-if
       end-if
       go     to BD032-Skip-Question
     end-if

     display  "Is this the end of a quarter (Y/N) - [ ]" at 1601 with foreground-color 2.
     ACcept   WS-Reply at 1639 with foreground-color 6.
     move     function upper-case (WS-Reply) to WS-Reply.
*>
 BD032-Skip-Question.
     if       WS-Reply = "N"
              go to  BD999-Main-Exit.
*>
     if       WS-Reply not = "Y"
              go to  BD030-Query-Check.
*>
     if       Current-Quarter not = 4
              ADd   1  to  Current-Quarter
              move  1  to  new-quarter
       else
              move 1 to cyclea
                        Current-Quarter
                        New-Year
                        new-quarter.
*>
 BD999-main-exit.
     exit     Section.
*>
 BA00-Value-Reset       Section.
*>*****************************
*>
*>  Reset the values in the Value file/table.
*>   performed for both Sales and Purchase data at END OF YEAR.
*>
*> Input-Flags.     WS-Value-System = "S" or "P"
*> Output.          Updated or deleted Value records.
*> Error-Cond.      Can exit or goto aa990-Menu-Error with WS-Term-Code = 2
*>                               then exit program.
*>
 BA000-Start.
     if       New-Year = 1                  *> clear down all data
        and   WS-Value-ClearDown = "N"
              perform Value-Open-Output                           *> open output value-file
              move    zero to WS-Count-Rows
              if      FS-RDBMS-Used              *> Extra step for RDB processing
                      perform  Value-Delete-All
                      move zero to File-Function
              end-if
              display XL116  at 1401 with foreground-color 2 underline
              if      FS-RDBMS-Used
                      move WS-Count-Rows  to Z9
                      display " Delete count = " at 1437 with foreground-color 4
                      Display Z9                 at 1453 with foreground-color 4
              end-if
              move    "Y" to WS-Value-ClearDown
              go to BA020-End
     end-if
     if       New-Year = 1                  *> clear down all data
        and   WS-Value-ClearDown = "Y"
              go to BA020-End
     end-if
*>
     perform  Value-Open.               *> open     i-o  value-file.
*>
 BA010-Read.        *> Not New Year.
     perform  Value-Read-Next.                  *> read value-file  next record   at end
     if       FS-Reply = 10
              go to  BA020-End.
*>
     if       VA-System not = WS-Value-System         *> = "S" here!
              go to BA010-Read.
*>
     move     VA-T-This  to  VA-T-Last.
     move     zero       to  VA-T-This.
     move     VA-V-This  to  VA-V-Last.
     move     zero       to  VA-V-This.
*>
     perform  Value-ReWrite.                   *> rewrite  value-record.
     if       FS-Reply not = zero
              display XL105  at line WS-22-Lines col 1 with foreground-color 4 highlight erase eos
              display XL117  at line WS-22-Lines col 35
                                                       with foreground-color 4 highlight
              display XL001           at line WS-23-Lines col 01 with foreground-color 4 highlight
              ACcept  WS-Reply        at line WS-23-Lines col 32
              perform Value-Close
              go to aa990-Menu-Error
     end-if
     go       BA010-Read.
*>
 BA020-End.
     perform  Value-Close.               *> close    value-file.
*>
 BA00-Exit.
     exit     section.
*>
 zz070-Convert-Date     Section.
*>*****************************
*>
*>  Converts date in to-day to UK/USA/Intl date format
*>****************************************************
*> Input:   to-day
*> output:  WS-Date as uk/US/Inlt date format
*>
     move     to-day to WS-Date.
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
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     to-day (7:4) to WS-Intl-Year.
     move     to-day (4:2) to WS-Intl-Month.
     move     to-day (1:2) to WS-Intl-Days.
*>
 zz070-Exit.
     exit     Section.
*>
 copy "Proc-Get-Env-Set-Files.cob".  *> Only uses ACAS_LEDGERS now
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
