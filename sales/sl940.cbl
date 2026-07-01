       >>source free
*>****************************************************************
*>                                                               *
*>           I N V O I C E   D E L E T I O N                     *
*>                                                               *
*>  From the Invoice file / table Only not Open Item file/table. *
*>                                                               *
*>  Program will Add back all stock on deleted Invoice back to   *
*>    the stock items records.                                   *
*>****************************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl940.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 28/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Deletion.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas010  ->
*>                         auditMT
*>                        acas011  ->
*>                         stockMT.
*>                        acas012  ->       (Sales)
*>                         salesMT.
*>                        acas014  ->       (Delivery)
*>                         deliveryMT.
*>                        acas015  ->       (Analysis)
*>                         analMT.
*>                        acas016  ->       (Invoice)
*>                         invoiceMT.
*>                        acas017  ->       (DelInvNos)
*>                         sldelinvnosMT.
*>**
*>    Error messages used.
*>     System Wide:
*>                        SL003
*>                        SL006
*>     Module specific:
*>                        SL190
*>                        SL191
*>                        SL194
*>                        SL195
*>                        SL196  Invoice file does not exists yet - post some.
*>                        SL197
*>**
*> Changes
*> 03/03/09 vbc - .01 Migration to Open Cobol v3.00.00.
*> 26/11/11 vbc - .02 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .03 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn, support for IS delivery file
*> 11/12/11 vbc - .04 Changed usage of Stk-Date-Form to the global field Date-Form
*>                    making former redundent.
*> 24/10/16 vbc - .05 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 19/01/17 vbc - .06 Replaced usage of maps99 to displays.
*>                    Added remaining FH processing but excluding invoice.
*> 20/01/17 vbc       Removed references to invoice letter as redundant.
*> 25/01/17 vbc       Dry testing completed.
*> 10/02/17 vbc - .07 Updated FD/WS for 016 and replaced cobol verbs
*>                    for access to FH/DALs.
*> 30/08/17 vbc - .08 Added more display for information.
*> 19/03/18 vbc - .09 Added code to update stock recs period and yearly fields
*>                    before deleting the invoice line items as a one call for RDB
*>                    or one by one for Cobol File.
*> 21/03/18 vbc - .10 Added new msgs (update manuals), update for Audit and Stock
*>                    before deleting a invoice.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 17/12/24 vbc   .11 Missing Analys record was using dummy found with trace on.
*>                    On display SL194 overwrite of display data.
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
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
*> copy "selinv.cob".
*> copy "selsl.cob".
*> copy "seldel.cob".
*> copy "seldnos.cob".
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdinv.cob".
*> copy "fdsl.cob".
*> copy "fddel.cob".
*> copy "fddnos.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL940 (3.3.00)".
 77  Exception-Msg       pic x(25) value spaces.
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
 copy "slwsinv.cob" replacing Invoice-Line by Invoice-Lines. *> this is header and 40 lines table
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                                pic x(137).
 copy "wssl.cob".
 copy "wsdel.cob".
 copy "wsdnos".
 copy "wsaudit.cob".
 copy "wsstock.cob".     *> 3.02
 copy "wsanal.cob".   *> 17/12/24  missed
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
*>     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
*>     03  WS-Delivery-Record     pic x.
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
 01  ws-data.
     03  menu-reply      pic 9.
     03  ws-reply        pic x.
     03  a               pic 99.
     03  c-check         pic 9.
         88  c-exists                    value 1.
     03  address-A       pic x(96).
     03  address-line    pic x(36).
     03  i               pic 99.
     03  j               pic 99.
     03  k               pic 99.
     03  escape-code     pic x.
     03  WS-Inv-Month.
         05  WS-Inv-Mth  pic 99.
             88 WS-Valid-Mth   values 01 thru 12.
     03  WS-Temp-Stock-Key                    value spaces.
         05  ws-Abrev-Stock   pic x(7).
         05  ws-Stock-No-Long pic x(6).
     03  ws-env-lines    pic 999         value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
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
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
01  Error-Messages.
*> System Wide
     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
     03  SL006          pic x(43) value "SL006 Note Details & Hit Return to continue".
*> Module specific
     03  SL190          pic x(35) value "SL190 Error on Writing Audit record".
     03  SL191          pic x(33) value "SL191 Error on Stock rec. Rewrite".
     03  SL194          pic x(24) value "SL194 Invoice Not Found".
     03  SL195          pic x(52) value "SL195 Invoice Details Already Passed To Sales Ledger".
     03  SL196          pic x(37) value "SL196 Invoice File does Not yet Exist".
     03  SL197          pic x(22) value "SL197 Stock Rewrite : ".
*>
 01  error-code          pic 999.
*>
 linkage section.
*>***************
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
*>=======================================
*>
 init01 section.
*>
     accept   ws-env-lines from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines   to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-23-lines.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
     perform  program-start.
     perform  Invoice-Open.              *> open i-o    invoice-file.
     perform  Sales-Open-Input.          *> open input  sales-file.
     perform  Delivery-Open-Input.       *> open input  delivery-file.
     perform  DelInvNos-Open.            *> open extend Del-Inv-Nos-file. [ Now I/O ]
*> new 19/03--
     perform  Stock-Open.
     perform  Stock-Audit-Open.
     perform  Analysis-Open.
*>
 done-open.
     move     spaces to escape-code.
     initialize SInvoice-Bodies.   *> Sil-Data (occ 40).
     perform  invoice-details.
*>
     if       escape-code = "Q"
              go to  main-exit.
*>
     move     1 to cole.
     display  " " at 1601 with erase eos.
*>
 data-input.
*>**********
*>
     display  "Delete Further Invoices (Y/N) ? [Y]" at 1629 with foreground-color 2.
*>
     move     "Y"  to   ws-reply.
     accept   ws-reply at 1662 with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
     display  " " at 1601 with erase eol.
     if       ws-reply = "Y"
              go to done-open.
*>
 main-exit.
*>********
*>
     perform  Sales-Close.       *> close sales-file delivery-file Del-Inv-Nos-file.
     perform  Delivery-Close.
     perform  DelInvNos-Close.
     perform  Invoice-Close.       *> close    invoice-file.
*> new 19/03--
     perform  Stock-Close.
     perform  Stock-Audit-Close.
     perform  Analysis-Close.
     exit     program.
*>
*>****************************************************
*>                    Procedures                     *
*>****************************************************
*>
 Delete-Details section.
*>=====================
*>
*> Used with Cobol files only.
*>
     move     zero  to  j.
     perform  sih-lines times
              add    1 to j
              move   sih-invoice to invoice-nos
              move   j to item-nos
              perform Invoice-Delete     *> delete invoice-file
     end-perform.
*>
 main-exit.   exit section.
*>********    ****
*>
 Read-Details  section.
*>====================
*>
*> Uses read next but if problem, can use read indexed just a bit faster.
*> Having read each in process audit update.
*>
     move     zero to j.
     perform  sih-lines times
              add      1 to j
              move     sih-invoice to invoice-nos
              move     j to item-nos
              perform  Invoice-Read-Next
              move     WS-Invoice-Record to Invoice-Lines (j)
              perform  Update-Stock-n-Audit
     end-perform.
*>
 main-exit.   exit section.
*>********    ****
*>
 Update-Stock-n-Audit section.
*>===========================
*>
*>  This procedure update ONE line entry from the Invoice-Lines record.
*>    and is called for every entry.
*>
*> Only processes if linked to Stock Control and not proforma
*>  This section only creates an Audit record and updates
*>   Stock record quantity held (Stock-Held) and Stock-Value then
*>    updates the stock rec history current period and by month
*>
*>    This block taken from SL910 (data entry), so if in error chg sl910.
*>
*>    These routines do the reverse of code in sl910 regarding invoice rec type.
*>
     if       SL-Stock-Link not = "Y"
              go to Update-Stock-Exit.
     if       Sih-Type   = 4
              go to Update-Stock-Exit.
*>
*> Normal for Receipts(1) and Invoices (2) but reverse process for
*>      Credit Notes (3) AND Proformas are ignored.
*>
     initialize WS-Stock-Audit-Record.
     move     3                   to Audit-Type.
     move     Sih-Invoice         to Audit-Invoice-PO.
     move     ws-Date             to Audit-Process-Date.
     move     Sil-Product (j)     to Audit-Stock-Key
                                     WS-Temp-Stock-Key.
     move     Sil-Description (j) to Audit-Desc.
     move     sil-qty (j)         to Audit-Transaction-Qty.
     move     zero                to Audit-Unit-Cost.
     if       Sil-Type (j) = 3
              move 5        to Audit-Type
              move zero     to Audit-Reverse-Transaction   *> was 1
              move Sih-cr   to Audit-Cr-for-Invoice
     else
              move 1        to Audit-Reverse-Transaction   *> was zero
     end-if
     move     Stk-Audit-No  to Audit-No.
*>
*> Get the Stock record
*>
     if       ws-Stock-No-Long = spaces
              move ws-Abrev-Stock to WS-Stock-Abrev-Key
              move  2 to File-Key-No
              perform Stock-Read-Indexed      *> read Stock-File record key WS-Stock-Abrev-Key invalid key
              if   FS-Reply = 21 or 23
                   move zero to Stock-Cost
                   move spaces to WS-Stock-Key
              end-if                           *> end-read
     else
              move WS-Temp-Stock-Key to WS-Stock-Key
              move  1 to File-Key-No
              perform Stock-Read-Indexed    *> read Stock-File key WS-Stock-Key invalid key
              if   FS-Reply = 21 or 23
                   move zero to Stock-Cost
                   move spaces to WS-Stock-Key
              end-if                                *> end-read
     end-if
*>
*> As stock items are checked this should not happen
*>     but it is a multi user system
*>
     if       fs-reply not = zero
              perform Eval-Status
              display SL194           at line ws-23-lines col 1 with erase eol foreground-color 4
              display fs-reply        at line ws-23-lines col 26 with foreground-color 3
              display exception-msg   at line ws-23-lines col 29 with foreground-color 3
              display WS-Stock-Key       at 2064 with foreground-color 3
              display sl006           at line ws-lines col 01 with foreground-color 3
              accept  ws-reply        at line ws-lines col 45
              display " "             at line ws-23-lines col 1 with erase eos
     end-if
*>
*> If we have great, but if not Stock-Cost is zero which helps it
*>          show up in proof reports (sil-type same as sih-type so use later - less ram)
*>
     if       WS-Stock-Key not = spaces         *> we have a stock rec.
              if       Sih-Type = 3             *> was 1 or 2             *> Credit note
                       compute  Audit-Stock-Value-Change = Audit-Transaction-Qty
                                    * Stock-Cost * -1
                       subtract Audit-Transaction-Qty from Stock-Held
              else
               if      Sih-Type = 1 or = 2      *> Was = 3
                       compute  Audit-Stock-Value-Change = Audit-Transaction-Qty
                                    * Stock-Cost
                       add Audit-Transaction-Qty to Stock-Held
               end-if
              end-if
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
*> Update record period and month in year totals but check that WS-Inv-Mth is valid.
*>    [ All values should be positive ]
*>       and    could be different month - WIP stock is NOT sold!
*>
              if       WS-Inv-Mth not < 1 or > 12
                if     Sih-Type = 3                         *> Credit Notes  WAS 1 or 2
                       add Audit-Transaction-Qty to Stock-Deducts
                       add Audit-Transaction-Qty to Stock-TD-Deds (WS-Inv-Mth)
                else
                 if    Sih-Type = 1 or 2                    *> Invoice and Recepts  WAS 3
                       add Audit-Transaction-Qty to Stock-Adds
                       add Audit-Transaction-Qty to Stock-TD-Adds (WS-Inv-Mth)
                 end-if
                end-if
              end-if
*>
              move 1 to File-Key-No
              perform  Stock-Rewrite      *> rewrite  WS-Stock-Record invalid key
              if       FS-Reply = 21 or 23
                       display SL191    at line ws-23-lines col 1 with foreground-color 4 highlight erase eol
                       display fs-reply at line ws-23-lines col 38 with foreground-color 2 highlight
                       display SL006    at line ws-lines col 1
                       accept ws-reply  at line ws-lines col 45
              end-if                         *> end-rewrite
              if       fs-reply not = zero
                       perform Eval-Status
                       display SL197         at line ws-23-lines col 1 with erase eol foreground-color 4
                       display fs-reply      at line ws-23-lines col 22 with foreground-color 3
                       display exception-msg at line ws-23-lines col 25 with foreground-color 3
                       display WS-Stock-Key  at 2064 with foreground-color 3
                       display sl006         at line ws-lines col 01 with foreground-color 3
                       accept  ws-reply      at line ws-lines col 30
                       display " "           at line ws-23-lines col 1 with erase eos
              end-if
     end-if
*>
     if       Stk-Audit-Used = 1
              move zero to Stk-Activity-Rep-Run    *> Need to run audit report
              perform  Stock-Audit-Write           *> write Stock-Audit-Record
              if       fs-reply not = zero
                       perform Eval-Status
                       display SL190         at line ws-23-lines col 1 with foreground-color 4 highlight erase eol
                       display fs-reply      at line ws-23-lines col 38 with foreground-color 2 highlight
                       display exception-msg at line ws-23-lines col 41 with foreground-color 3
                       display SL006         at line ws-lines col 1
                       accept ws-reply       at line ws-lines col 45
              end-if
     end-if.
*>
 Update-Stock-Exit.
     exit     section.
*>
 Eval-Status  section.
*>===================
*>
     move     spaces to exception-msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by exception-msg.
*>
 main-exit.   exit section.
*>************************
*>
 Program-Start  section.
*>=====================
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-16      *> Invoice
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                    display SL196    at 2301
                    display SL003    at 2401
                    accept  ws-reply at 2440
                    exit program
     end-if
*>
     move     to-day to u-date.
*>
 menu-return.
*>**********
*>
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "Invoicing Data Deletion" at 0131 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
*>
 main-exit.   exit section.
*>********    ****
*>
 invoice-details         section.
*>==============================
*>
     display  "****************************************" at 0441 with erase eol foreground-color 2.
     display  "*Date   [  /  /    ]*                  *" at 0541 with erase eol foreground-color 2.
     display  "*A/C Nos   [       ]*                 **" at 0641 with erase eol foreground-color 2.
     display  "*Invoice  [        ]*Order [          ]*" at 0741 with erase eol foreground-color 2.
     display  "****************************************" at 0841 with erase eol foreground-color 2.
     display  "**   Only for the unposted Invoices   **" at 0941 with erase eol foreground-color 2.
     display  "Type [ ]  <1> = Receipt; <2> = Account; <3> = Credit Note; <4> = Pro-Forma"
                                                         at 1001 with foreground-color 2.
     display  "Zero invoice to quit"  at 1201 with foreground-color 2.
*>
 invoice-enter.
*>************
*>
     accept   sih-invoice at 0752 with foreground-color 3 update.
     display  " " at 1601 with erase eol.
     if       sih-invoice = zero
              move  "Q"  to  escape-code
              go to  main-exit.
*>
     move     sih-invoice  to  invoice-nos.
     move     zero  to  item-nos.
*>
*> Read the Invoice Header Rec
*>
     perform  Invoice-Read-Indexed.     *> read invoice-file  invalid key
     if       fs-reply not = zero
              display SL194 at 1640 with foreground-color 4
              go to  invoice-enter.
*>
     move     WS-Invoice-Record  to  sinvoice-header.
*>
     if       sih-status = "Z"   or "z"
              display SL195 at 1601 with foreground-color 4 erase eol
              go to  invoice-enter.
     move     sih-date to u-bin.
     perform  zz060-Convert-Date.                          *> in ws-date
     display  sih-customer at 0653 with foreground-color 3.
*>
     move     1  to  c-check.
     move     sih-customer  to  WS-Sales-Key.
     move     1  to File-Key-No.
     perform  Sales-Read-Indexed.           *> read sales-file  record  invalid key
     if       fs-reply = 21 or 23
              move  zero  to  c-check.
*>
     if       delivery-tag = zero
              go to  customer-setup.
*>
     move     "D"          to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Read-Indexed.          *> read delivery-file  invalid
     if       fs-reply = 21 or 23
              move  zero  to  delivery-tag
              go to  customer-setup.
*>
     move     deliv-address to  address-a.
     go       to customer-display.
*>
 customer-setup.
*>*************
*>
     move     sales-address  to  address-a.
*>
 customer-display.
*>***************
*>
     if       delivery-tag = zero
              display sales-name at 0401 with foreground-color 3
     else
              display deliv-name at 0401 with foreground-color 3
     end-if
     move     1  to  a.
     unstring address-a  delimited  by  sl-delim into  address-line count a pointer  a.
     display  address-line at 0501 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim into  address-line count a pointer  a.
     display  address-line at 0601 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a  delimited  by  sl-delim into  address-line count a pointer  a.
     display  address-line at 0701 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring address-a              into  address-line  pointer  a.
     display  address-line at 0801 with foreground-color 3.
*>
     move     spaces  to  address-line.
*>
     display  ws-date at 0550 with foreground-color 3.
     display  sih-order at 0769 with foreground-color 3.
     display  sih-type at 1007 with foreground-color 3.
     display  "Invoice To Be Deleted (Y/N) - [ ]" at 1601 with foreground-color 2.
     move     "N" to ws-reply.
     accept   ws-reply at 1632 with foreground-color 6 update UPPER.
     if       ws-reply not = "Y"
              go to  main-exit.
*>
*>  Need to read in all line recs and update stats one by one
*>    and the stock rec.
*>
     perform  Read-Details.                 *> Get all item lines and update audit & stock recs
     if       not FS-Cobol-Files-Used
              perform Invoice-Delete-All    *> Delete All for invoice # using RDB
     else
              perform  Invoice-Delete       *>  delete   invoice-file -> Deleting Header
              perform  Delete-Details.
*>
*> Save the deleted inv # for re-use in sl910.
*>
     move     sih-invoice  to  WS-Del-Inv-Nos.
     move     sih-date     to  del-inv-dat.
     move     sih-customer to  del-inv-cus.
*>
     perform  DelInvNos-Write.        *> write    WS-Del-Inv-Nos-record.
*>
 main-exit.   exit.
*>********    ****
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
              move WS-Month to WS-Inv-Month
              move 1 to Date-Form.
     if       Date-UK
              move WS-Month to WS-Inv-Month
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              move WS-Month to WS-Inv-Month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     u-date (7:4) to ws-Intl-Year.
     move     u-date (4:2) to ws-Intl-Month.
     move     WS-Intl-Month to WS-Inv-Month
     move     u-date (1:2) to ws-Intl-Days.
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
