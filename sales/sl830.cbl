       >>source free
*>*****************************************************************
*>                                                                *
*>             Autogen   POST and  ANALYSIS                       *
*>                                                                *
*>    This process process the analysis  & Stock Audit files      *
*>    processing that does occurs in sl910 for invoices but has   *
*>    been removed from sl810.                                    *
*>                                                                *
*>  The next process is for Invoice Posting to be run to complete *
*>  the processing i.e., sl055 and sl060.                         *
*>                                                                *
*>*****************************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl830.
*>**
*>    Author.             Vincent B Coen FBCS, FIDM, FIDPM, 23/05/23,
*>                        For Applewood Computers.
*>**
*>    Security.           ACAS, Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Autogen Generate extract, report & Analysis.
*>                        Updates analysis values from body items and headers
*>                        and Stock file for autogen and passes newly generated
*>                        invoices if they are due to the invoice file for final
*>                        processing by the invoice post programa sl055 & 060.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Functions used:
*>                        DATE-OF-INTEGER
*>                        INTEGER-OF-DATE
*>**
*>    Called Modules.
*>                        acas004  ->
*>                         SLautogenMT.
*>                        acas016  ->
*>                         invoiceMT.
*>                        acas010  ->      (Stock-Audit)
*>                         auditMT
*>                        acas015  ->       (Analysis) used for reading line items Anal codes
*>                         analMT.           for validation.
*>                        acas011  ->       Stock
*>                         stockMT.
*>**
*>    Error messages used.
*>                        SL198.
*>                        SL199.
*>                        SL200.
*>                        SL201
*>
*>    Changes:
*> 23/05/23 vbc -  00 New program :
*> 23/05/23 vbc - .00 Generates Invoice records from Autogen to the invoice file
*>                    If a Autogen record is due to be created, updating :
*>                    Analysis, Audit (stock) stock records as needed.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
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
*>
 data                    division.
*>===============================
*>
 working-storage section.
*>----------------------
 77  Prog-Name           pic x(15)    value "SL830 (3.3.00)".
 77  Exception-Msg       pic x(25)    value spaces.
*>
 copy "wsmaps03.cob".
*>
 copy "wsfnctn.cob".
*>
 copy "wsanal.cob".
 copy "wsaudit.cob".
 copy "wsstock.cob".
 copy "wsdnos.cob".
*>
*> Autogen and Invoice-Record
 copy "slwsinv.cob"  replacing Invoice-Line by Invoice-Lines. *> Dup name Holds sih (header) & sil (lines)
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                         pic x(137).        *> THIS ONLY HAS ONE Line ITEM
*>
 copy "wsval.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
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
*>     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
*>     03  WS-Analysis-Record     pic x.
*>     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
*>     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
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
 01  WS-Data.
     03  Autogen-Status  pic 9           value zero.
         88  Autogen-EOF                 value 1.
     03  Autogen-Stored  pic 9           value zero.
     03  WS-Active-Invoice-No
                         pic 9(8)        value zero.  *> Temp hold for a deleted # or next inv. from SL parameter
*>
     03  WS-Invoice-Write-Error-Flag
                         pic x           value space.  *> if set errors occurred for a autogen record
     03  WS-Invoice-Errors
                         pic x           value space.  *> if set errors has occured during run
     03  WS-DELINV       pic 9           value zero.
         88  Del-Exists                  value 1.
*>
     03  WS-Autogen-Date                 value zero.   *> Used to convert sih-date (in binary)
         05  WS-Autogen-YYYY pic 9(4).
         05  WS-Autogen-MM   pic 99.
         05  WS-Autogen-DD   pic 99.
     03  WS-Autogen-Date9 redefines WS-Autogen-Date
                             pic 9(8).
*>
     03  WS-Temp-Stock-Key                    value spaces.
         05  WS-Abrev-Stock   pic x(7).
         05  WS-Stock-No-Long pic x(6).
*>
     03  WS-Inv-Month.
         05  WS-Inv-Mth  pic 99.
*>
     03  J               pic 99.
*>
     03  Bin-To-Date     binary-long   value zero.  *> holds todays date in binary
     03  Bin-Minimum     binary-long   value zero.  *> holds todays date minus CC-Min-Date
     03  Bin-Maximum     binary-long   value zero.  *> holds todays date plus CC-Max-Date
*>
 01  WS-Temp-Run-Date        pic 9(8)          value zero.
 01  ws-Test-Date            pic x(10).
 01  WS-Locale-Run-Date      pic x(10)         value spaces.
 01  WS-Date-Formats.
     03  WS-Swap             pic xx.
     03  WS-Conv-Date        pic x(10).
     03  WS-Date             pic x(10).
     03  ws-UK redefines WS-Date.
         05  ws-days         pic xx.
         05  filler          pic x.
         05  ws-Month        pic xx.
         05  filler          pic x.
         05  ws-Year         pic x(4).
     03  ws-USA redefines WS-Date.
         05  ws-usa-Month    pic xx.
         05  filler          pic x.
         05  ws-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  ws-Intl redefines WS-Date.
         05  ws-Intl-Year    pic x(4).
         05  filler          pic x.
         05  ws-Intl-Month   pic xx.
         05  filler          pic x.
         05  ws-Intl-days    pic xx.
*>
 01  Error-Messages.
*> System Wide
*>       NONE
*> Module specific
*>  NEW
     03  SL198           pic x(39) value "SL198 Failure to Rewrite Autogen record".
     03  SL199           pic x(38) value "SL199 Failure to Delete Autogen record".
     03  SL200           pic x(40) value "SL200 Failure to Write Invoice record - ".
     03  SL201           pic x(46) value "SL201 There has been failures writing Invoices".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
*> Now for CONSTANTS used within program that are used for the date range
*>  to be checked for. This can be changed and sl830 recompiled...
*>
*> As set, they give a four day window in order to cover weekend and Bank holidays
*>  when ACAS, sales and this program may well NOT be run.
*>
*> CONSIDER adding a Sales parameter that executes this program say via CRONTAB
*> or another job scheduler. This way it will auto run when there is no one in
*>  office - Providing the system is on 24/7. IT DOES NOT MEAN THAT the invoice
*>   posting program is run or that the invoice print program is run !!!
*>
*> If these programs also need to auto run then the printers that will be used
*>  for invoice and Packing/Delivery notes MUST be turned on 24/7 with enough
*>    paper for any prints so that staff can process then when they are working.
*>  Such printers when not used are set to low power consumption after a few
*>  minutes of no activity.
*>
*> The drawback to this, is that the date printed may not be today's date.
*>
 01  CC-Min-Date         pic 9   value 2. *> Days backwards to be in range of today
 01  CC-Max-Date         pic 9   value 2. *> Days forwards  to be in range of today
*>
linkage       section.
*>-------------------
*>
 copy "wsnames.cob".
 copy "wscall.cob".
 copy "wssystem.cob".
*>
 01  To-Day              pic x(10).
*>
 procedure division using WS-Calling-Data
                          System-Record
                          To-Day
                          File-Defs.
*>=======================================
*>
 aa000-Main   section.
*>===================
*>
     if       SL-Autogen not = "Y"    *> SL Autogen not in use
              goback.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     perform  zz070-Convert-Date.   *> WS-Date now local disp date
     move     WS-Date to WS-Locale-Run-Date.
*>
     display  Prog-Name at 0101 with foreground-color 2 erase eos.
     display  "Autogen Posting"  at 0132  with foreground-color 2.
     display  WS-Locale-Run-Date at 0171 with foreground-color 2.
     display  "Running...."      at 1235 with foreground-color 3.
     perform  zz010-Open-Files.
*>
     perform  ba000-Process-Autogen.
     if       WS-Invoice-Errors = "Y"
              display SL201 at 1610 with foreground-color 5.
*>
     perform  zz020-Close-All-Files.
*>
 aa999-Exit.  goback.
*>
 ba000-Process-Autogen  section.
*>=============================
*>
 ba000-Main.
*>
*> Need to get current date as binary since 1601/01/01
*>
     accept   WS-Temp-Run-Date from DATE YYYYMMDD.
     move     function INTEGER-OF-DATE (WS-Temp-Run-Date) to Bin-To-Date.  *> bin date since 1600/12/31
     subtract CC-Min-Date from Bin-To-Date giving Bin-Minimum.
     Add      CC-Max-Date to   Bin-To-Date giving Bin-Maximum.
*>
*> Can now test autogen date is within range of Bin-Minimum and Bin-Maximum
*> for action if NOT ALREADY PROCESSED AND that Freq is valid today
*> IF, sih-Last-Date is not within same range (indicated it has already been processed.
*>
*>  ALL Invoice DATA is using sih and sil to store the invoice/Autogen record
*>
 ba010-Read-Autogen.
     move     zero to Autogen-Status
                      FS-Reply
                      Autogen-Stored.
     move     space to WS-Invoice-Errors.    *> Records ANY write errors on Invoice file
     perform  until Autogen-EOF
              if       NOT Autogen-Stored = 1  *> We Have a record in WS-Invoice-Record
                       perform  SLautogen-Read-Next
              end-if
              if       FS-Reply not = zero   *> IS THIS RIGHT ???????? and above statements
                       move  1 to Autogen-Status   *> Autogen-EOF so proces rec leave perform
                       move  zero to Autogen-Stored
                       perform  zz040-Generate-Invoice
                       perform  ba020-Check-For-Write-Errors
                       exit perform
              end-if
*>
              if       Item-Nos = zero        *> read a header but have item lines from the last header
                and    J not = zero
                       if       sih-Date not < Bin-Minimum
                         and    sih-Date not > Bin-Maximum
                                perform  zz040-Generate-Invoice
                                perform  ba020-Check-For-Write-Errors
                                exit perform cycle
                       end-if
*>
                       move     1 to Autogen-Stored
                       move     zero to J
                       initialise SInvoice-Bodies with filler
                       move     WS-Invoice-Record to Sinvoice-Header
                       exit perform cycle
              end-if
*>
              if       Item-Nos = zero
                       move     zero to J
                       move     zero to Autogen-Stored
                       initialise SInvoice-Bodies with filler
                       move     WS-Invoice-Record to Sinvoice-Header
                       exit perform cycle
              end-if
*>
              if       Item-Nos not = zero    *> Not a header record
                       add      1 to J
                       move     WS-Invoice-Record to Invoice-Lines (J)
                       exit perform cycle
              end-if
*>
              if       sih-Date not < Bin-Minimum
                and    sih-Date not > Bin-Maximum
                       perform  zz040-Generate-Invoice
                       perform  ba020-Check-For-Write-Errors
                       exit perform cycle
     end-perform.
     go to ba999-Exit.
*>
 ba020-Check-For-Write-Errors.
     if       WS-Invoice-Write-Error-Flag = "Y"
              display SL200 at 1510 with foreground-color 5 erase eol
              display Invoice-Key at 1550 with foreground-color 2.
*>
*> We have finished processing Autogen Records
*>
 ba999-Exit.  exit section.
*>
 zz010-Open-Files  section.
*>========================
*>
     perform  Value-Open-Input.
     if       fs-reply not = zero
              perform Value-Close
              perform Value-Open-Output
     end-if
     perform Value-Close.
*>
     if       FS-Cobol-Files-Used             *> create autogen if not exist.
              call  "CBL_CHECK_FILE_EXIST" using File-4       *> SaAutogen
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    perform  SLautogen-Open-Output    *> open output SLautogen-file
                    perform  SLautogen-Close          *> close SLautogen-file
                    move     "Y" to SL-Autogen
                    move     1   to SL-Next-Rec    *> SIMILAR TO NEXT INVOICE #
                    goback                         *> as nothing to do
              end-if
*>
              call  "CBL_CHECK_FILE_EXIST" using File-15   *> Analysis
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                                                    *> This should have happened in sl910 invoice create
                    move 1 to ws-Process-Func ws-Sub-Function    *> Create default entries in Analysis
                    call "sl070" using WS-Calling-Data           *>   and Value files
                                       System-Record
                                       To-Day
                                       File-Defs
              end-if
*>
              call  "CBL_CHECK_FILE_EXIST" using File-16      *> Invoice
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    perform  Invoice-Open-Output    *> open output invoice-file
                    perform  Invoice-Close          *> close invoice-file
              end-if
*>
              if     Stk-Audit-Used = 1
                     call  "CBL_CHECK_FILE_EXIST" using File-10      *> Stock audit file
                                                        File-Info
                     if    return-code not = zero          *> not = zero - No file found
                           perform Stock-Audit-Open-Output
                     else
                           perform Stock-Audit-Open-Extend
                     end-if
                     perform Stock-Audit-Close
              end-if
     end-if.
     perform  SLAutogen-Open.
     perform  Invoice-Open.
     perform  Stock-Audit-Open.
     perform  Analysis-Open.
     perform  Value-Open.
     perform  DelInvNos-Open.
     if       FS-Reply = zero
              move     1 to WS-DELINV.
*>
*>
 zz010-Exit.  exit section.
*>*********
*>
 zz020-Close-All-Files section.
*>============================
*>
     perform  SLAutogen-Close.
     perform  Invoice-Close.
     perform  Stock-Audit-Close.
     perform  Analysis-Close.
     perform  Value-Close.
     perform  DelInvNos-Close.
*>
*> ANY MORE ???
*>
 zz020-Exit.  exit section.
*>*********
*>
 zz030-get-a-deleted-invoice section.
*>==================================
*>
     if       not Del-Exists
              go to zz030-Terminate.
 zz030-Start.
     move     zeros to WS-Del-Inv-Nos.
     move     1 to File-Key-No.
     set      fn-not-less-than to true.
     perform  DelInvNos-Start.
*>     start    Del-Inv-Nos-File key not < WS-Del-Inv-Nos invalid key
     if       fs-reply = 21 or 23
              go to zz030-Terminate.
*>
 zz030-Read.
     perform  DelInvNos-Read-Next.
     if       fs-reply = 10
              go to zz030-Close.
     if       WS-Del-Inv-Nos = zero
              go to zz030-Read.
     move     WS-Del-Inv-Nos to WS-Active-Invoice-No.  *> del rec will be deleted after o/p of invoice.
     perform  DelInvNos-Delete.
     go       to zz030-Exit.
*>
 zz030-Close.
*>
*> If open as output clear down file and if RDB *MT deletes all records with
*>  key below 99999999 so same thing
*>
     perform  DelInvNos-Close.
     perform  DelInvNos-Open-Output.
*>
 zz030-Terminate.
     move     Next-Invoice to WS-Active-Invoice-No.
     add      1 to Next-Invoice.
     move     zero to WS-DELINV.
*>
 zz030-Exit.  exit section.
*>
 zz040-Generate-Invoice section.
*>=============================
*>
*> Dont forget to update sih-date for the next Autogen invoice due date
*>    and then rewrite autogen record
*>
*> Processing logic::
*>
*> On entry there is a Header record and one or more line items present, number is in J
*>   as a total count of line items.
*>
 *> Update sih-Last-Date with sih-Date - YES I know there is a 4 day spread but
 *>      should be OK.
*>
*>  Create an invoice record for every line body record as well as the Header record.
*>  Remember to NOT include content of sih-Order but space fill the invoice sih-order
*>   prior to rewrite (use
*>    move Sinvoice-Header to WS-Invoice-Record
*>    move spaces to ih-Order
*>
*>  As each line item (body) is processed also call zz045-Update-Analysis as well
*>
*>  After processing the last line item? Compute the date of the next submission date
*>   into sih-Date based on sih-Freq - remember to convert the bin date to yyyymmdd
*>    first to work the next date out.  Then update sih-date and rewrite the header
*>      record, Ignoring the line item records.
*>

*> Check for repeat count if non zero AND NOT 99 ( repeat count is ignored )
     if       sih-Repeat = zero          *> Recurring invoice is now dead and can be deleted
              move     Sinvoice-Header to WS-Invoice-Record
              perform  SLautogen-Delete
              if       FS-Reply not = zero
                       display SL199 at 1310 with foreground-color 5 erase eol
                       end-if
              perform  varying J from 1 by 1 until J > sih-Lines
                       move     Invoice-Lines (J) to WS-Invoice-Record
                       perform  SLautogen-Delete
                       if       FS-Reply not = zero
                                display SL199 at 1410 with foreground-color 5 erase eol
                       end-if
              end-perform
     end-if
     If       sih-Repeat not = zero AND not = 99
              subtract 1 from sih-Repeat.   *>  And continue
*>
*> Create Header
*>
     move     space to WS-Invoice-Write-Error-Flag.
     move     SInvoice-Header to WS-Invoice-Record.
     move     spaces to ih-Order.
     perform  zz030-get-a-deleted-invoice.     *> if exist get it else use Next-Invoice
     move     WS-Active-Invoice-No to Invoice-Nos.
     move     zeros to Item-Nos.               *> Header marker
     perform  Invoice-Write.
     if       FS-Reply not = zeros
              move "Y" to WS-Invoice-Errors
              move "Y" to WS-Invoice-Write-Error-Flag.
*>
*> Now process Line Items
*>
     perform  varying J from 1 by 1 until J > sih-Lines
              if      J > sih-Lines
                      exit perform
              end-if
              move     Invoice-Lines (J) to WS-Invoice-Record
              move     WS-Active-Invoice-No to Invoice-Nos
              move     J to Item-Nos    *> yes overriding one in Autogen JIC it is out of order
              perform  Invoice-Write
              if       FS-Reply not = zeros
                       move "Y" to WS-Invoice-Errors
                       move "Y" to WS-Invoice-Write-Error-Flag
              end-if
              perform  zz045-Update-Analysis   *> run varying J from 1 until  J > ih-Lines
     end-perform.
*>
*> Now Update next autogen date based on Freq
*>
*>     get date in yyyymmdd form   convert back using INTEGER-OF-DATE
*>
     move     FUNCTION DATE-OF-INTEGER (sih-Date) to WS-Autogen-Date9.
     if       Sih-Yearly
              add      1 to WS-Autogen-YYYY
     end-if
     if       Sih-Monthly
              add      1 to WS-Autogen-MM
              if       WS-Autogen-MM > 12
                       move     1 to WS-Autogen-MM
                       add      1 to WS-Autogen-YYYY
              end-if
     end-if
     if       Sih-Quarterly
              add      3 to WS-Autogen-MM
              if       WS-Autogen-MM > 12
                       subtract 12 from WS-Autogen-MM
                       add      1  to   WS-Autogen-YYYY
              end-if
     end-if
*>
*>  These are to help testing, as daily would not be used in Autogen
*>   recurring invoicing
*>
     if       sih-Daily or sih-Testing
              add      1 to WS-Autogen-DD
              if       WS-Autogen-MM = 2
                and    WS-Autogen-DD > 28
                       move     1 to WS-Autogen-DD
                       add      1 to WS-Autogen-MM
              else
               if      (WS-Autogen-MM = 9 or = 4 or = 6 or = 11)
                 and   WS-Autogen-DD > 30
                       move     1 to WS-Autogen-DD
                       add      1 to WS-Autogen-MM
               else
                if     WS-Autogen-DD > 31
                       move     1 to WS-Autogen-DD
                       add      1 to WS-Autogen-MM
                       if       WS-Autogen-MM > 12
                                move     1 to WS-Autogen-MM
                                move     1 to WS-Autogen-DD
                       end-if
                end-if
               end-if
              end-if
     end-if
     move     Sih-Date to Sih-Last-Date.    *> Save the old date  This date is plus or minus 2
     move     FUNCTION INTEGER-OF-DATE (WS-Autogen-Date9) to Sih-Date.
     move     SInvoice-Header to WS-Invoice-Record.
     perform  SLautogen-Rewrite.
     if       FS-Reply not = zero
              display  SL198  at 1210 with foreground-color 5 erase eol.
*>
 zz040-Exit.  exit section.
*>
 zz045-Update-Analysis section.
*>============================
*>
*> THIS PROCESSES LINE ITEMS using the O/P record pre writing it out
*>
*> Removed all file error displays and waits as can run unattended.
*>
*> Only process if linked to Stock Control & Invoices
*>  This section only creates an Audit record and updates
*>   Stock record quantity held (Stock-Held) and Stock-Value
*>
*>  ALSO UPDATE THE STOCK REC HISTORY CURRENT PERIOD AND BY Month ?.
*>
     if       SL-Stock-Link not = "Y"
              go to zz045-Exit.
     if       Sih-Type not = 2       *> Not for 4-Proformas, 3 - CR.Notes and
              go to zz045-Exit.      *> But 'Might' be for 1 - receipts at some point ??
*>
     initialize WS-Stock-Audit-Record.           *> using O/P rec in ws-invoice-record
     move     3                   to Audit-Type.
     move     il-Invoice          to Audit-Invoice-PO.
     move     WS-Locale-Run-Date  to Audit-Process-Date.  *> Using the Locale run date format via zz070
     move     il-Product          to Audit-Stock-Key
                                     WS-Temp-Stock-Key.
     move     il-Description      to Audit-Desc.
     move     il-Qty              to Audit-Transaction-Qty.
     move     zero                to Audit-Unit-Cost.
     move     zero                to Audit-Reverse-Transaction.
     move     Stk-Audit-No        to Audit-No.   *> Batch #, updated in Stock Control
*>
*> Get the stock record
*>
     if       WS-Stock-No-Long = spaces
              move WS-Abrev-Stock to WS-Stock-Abrev-Key
              move  2 to File-Key-No
              perform Stock-Read-Indexed      *> read Stock-File record key WS-Stock-Abrev-Key invalid key
              if   FS-Reply = 21
                   move zero to Stock-Cost
                   move spaces to WS-Stock-Key
              end-if                           *> end-read
     else
              move WS-Temp-Stock-Key to WS-Stock-Key
              move  1 to File-Key-No
              perform Stock-Read-Indexed    *> read Stock-File key WS-Stock-Key invalid key
              if   FS-Reply = 21
                   move zero to Stock-Cost
                   move spaces to WS-Stock-Key
              end-if                                *> end-read
     end-if
*>
*> If we have great, but if not Stock-Cost is zero which helps it
*>     show up in proof reports (sil-type same as sih-type so use later - less ram)
*>
     if       WS-Stock-Key not = spaces		*> we have a stock rec.
              compute  Audit-Stock-Value-Change = Audit-Transaction-Qty * Stock-Cost * -1
              subtract Audit-Transaction-Qty from Stock-Held
*>
              if       Stock-Held < zero
                       multiply -1 by Stock-Held
                       add Stock-Held to Stock-Pre-Sales
                       move zero to Stock-Held
              end-if
              if       Stock-Held > zero
                       multiply Stock-Held by Stock-Cost giving Stock-Value
              else
                       move zero to Stock-Value
              end-if
*>
*>    Similar for sl920 (amend) and sl940 (Delete) invoices but reversed.
*>
*> Update record period and Month in Year totals but check that WS-Inv-Mth is valid.
*>    [ All values positive ] Note that stock fields are not signed and a credit
*>                  could be different Month - WIP stock is NOT sold!
*>
              if       WS-Inv-Mth not < 1 or > 12
                       add Audit-Transaction-Qty to Stock-Deducts
                       add Audit-Transaction-Qty to Stock-TD-Deds (WS-Inv-Mth)
              end-if
*>
              move 1 to File-Key-No
              perform  Stock-Rewrite      *> rewrite  WS-Stock-Record invalid key
     end-if
*>
     if       Stk-Audit-Used = 1
              move zero to Stk-Activity-Rep-Run	   *> Need to run audit report
              perform  Stock-Audit-Write           *> write Stock-Audit-Record
     end-if.
*>
 zz045-Exit.  exit section.
*>
 zz050-Validate-Date        section.
*>=================================
*>
*>  Converts USA/Intl to UK date format for processing.
*>****************************************************
*> Input:   ws-test-date
*> output:  u-date/WS-Date as uk date format
*>          u-bin not zero if valid date
*>
     move     ws-test-date to WS-Date.
     if       Date-Form = zero
              move WS-Month to WS-Inv-Month    *> done again for UK - but JIC 4 zz150 Analysis processing
              move 1 to Date-Form.
     if       Date-UK
              move WS-Month to WS-Inv-Month
              go to zz050-Test-Date.
     if       Date-USA                *> swap Month and days
              move ws-days to WS-Swap
              move ws-Month to ws-days
              move WS-Swap to ws-Month
              move WS-Month to WS-Inv-Month
              go to zz050-Test-Date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to WS-Date.  *> swap Intl to UK form
     move     ws-test-date (1:4) to ws-Year.
     move     ws-test-date (6:2) to ws-Month.
     move     WS-Month to WS-Inv-Month
     move     ws-test-date (9:2) to ws-Days.
*>
 zz050-Test-Date.
     move     WS-Date to u-date.
     move     zero to u-bin.
     perform  maps04.
*>
 zz045-Exit.
     exit     section.
*>
 zz060-Convert-Date        section.
*>================================
*>
*>  Converts date in binary to UK/USA/Intl date format
*>****************************************************
*> Input:   u-bin
*> output:  WS-Date as uk/US/Inlt date format
*>          u-date & WS-Date = spaces if invalid date
*>
     perform  maps04.
     if       u-date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     u-date to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap Month and days
              move ws-days to WS-Swap
              move ws-Month to ws-days
              move WS-Swap to ws-Month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     u-date (7:4) to ws-Intl-Year.
     move     u-date (4:2) to ws-Intl-Month.
     move     u-date (1:2) to ws-Intl-Days.
*>
 zz060-Exit.
     exit     section.
*>
 zz070-Convert-Date        section.
*>================================
*>
*>  Converts date in To-Day to UK/USA/Intl date format
*>****************************************************
*> Input:   To-Day
*> output:  WS-Date as uk/US/Inlt date format
*>
     move     To-Day to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> swap Month and days
              move ws-days to WS-Swap
              move ws-Month to ws-days
              move WS-Swap to ws-Month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     To-Day (7:4) to ws-Intl-Year.
     move     To-Day (4:2) to ws-Intl-Month.
     move     To-Day (1:2) to ws-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
 zz900-Evaluate-Message Section.
*>==============================
*>
 copy "FileStat-Msgs.cpy" replacing MSG by Exception-Msg
                                    STATUS by FS-Reply.
*>
 Eval-Msg-Exit.  exit section.
*>
 maps04       section.
*>===================
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
*>LISTING OFF
 copy "Proc-ACAS-FH-Calls.cob".
*>LISTING ON
*>
