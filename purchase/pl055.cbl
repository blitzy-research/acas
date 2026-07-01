       >>source free
*>***********************************************
*>                                              *
*>       Orders  Post - Extract, Analysis       *
*>                                              *
*>***********************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         pl055.
*>**
*>    Author.             V B Coen FBCS, FIDM, FIDPM, Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            PO (Orders) Proof Report Extract & Analysis.
*>**
*>    Version.            See Prog-Name & Date-Comped In Ws.
*>**
*>    Called Modules.
*>                        acas013  ->       (value)
*>                         valueMT.
*>                        acas015  ->       (analysis)
*>                         analMT.
*>                        acas026  ->       (Purchase Order Folios [invoices] )
*>                         PinvoiceMT.
*>
*>**
*>    Files used in RDB mode:
*>                        Open-Item-File4 for i/p to pl060.
*>**
*>    Error messages used.
*>                        PL003
*>                        PL006
*>                        PL201
*>                        PL202
*>                        PL203.
*>                        PL204.
*>**
*>    Changes.
*> 21/05/84 Vbc - Support For Indexed Open Itm File.
*> 01/10/84 Vbc - Insert Analysis Code From Pl130.
*> 22/03/09 vbc - Migration to Open Cobol v3.00.00
*> 28/03/09 vbc - On open extend otm4 if error open as output as bug in OC.
*> 13/12/11 vbc - .03 Error msgs to SLnnn.Support for dates other than UK (Neither used here)
*>                    Support for path+filenames.
*>                    Updated version to 3.01.nn
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 31/10/16 vbc - .04 Support for RDB on Value & Analysis tables
*>                    instead of cobol files
*>                    using acas013  acas015. Update version to v3.02
*> 07/01/18 vbc - .05 Support for RDB on all other tables.
*>                    Replaced use of maps99 with display if needed.
*>                    Now uses Proc-ACAS-FH-Calls.cob for all FH & DAL calls
*>                    Added in support for remaining FH & DALs.
*>                    Temp file OTM4 kept to pass on to pl060.
*> 22/03/18 vbc - .06 Dont stop if error when run by xl150.
*> 09/12/22 vbc - .07 Added para to start of sections 4 GC 3.2 warning.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/08/25 vbc   .08 Change description of Emergency anal. rec.
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
 file-control.
*>
*> copy "selanal.cob".
*> copy "selval.cob".
*> copy "selpinv.cob".
 copy "seloi4.cob".     *> Temp file only for i/p to pl060.
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdanal.cob".
*> copy "fdval.cob".
*> copy "fdpinv2.cob".
 copy "fdoi4.cob".
 copy "plwsoi.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15)    value "PL055 (3.3.00)".
 77  Exception-Msg       pic x(25)    value spaces.
*>
 copy "wsfnctn.cob".
*>
*>  Ex FDs
*>
 copy "wsval.cob".  *>   replacing Value-Record by WS-Value-Record
 copy "wsanal.cob". *>   replacing Analysis-Record by WS-Analysis-Record
                    *>             WS-Pa-Code by WS-Pa-Code.
 copy "plwspinv2.cob".
*>
*> REMARK OUT, ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
     03  Default-Record         pic x.
     03  Final-Record           pic x.
*>     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
     03  WS-Stock-Record        pic x.
     03  WS-Sales-Record        pic x.
*>     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
*>     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
*>     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  ws-data.
     03  ws-reply        pic x.
     03  Anal-Created    pic 9                  value zero.
     03  save-code       pic xxx.
     03  ws-inv-amt      pic s9(7)v99   comp-3  value zero.
     03  work-2          pic s9(7)v99   comp-3  value zero.
     03  work-3          pic s9(5)      comp    value zero.
     03  ws-vat-totalv   pic s9(7)v99   comp-3  value zero.
     03  ws-vatr-totalv  pic s9(7)v99   comp-3  value zero.
     03  ws-carr-totalv  pic s9(7)v99   comp-3  value zero.
     03  ws-disc-totalv  pic s9(7)v99   comp-3  value zero.
     03  ws-vat-totalt   pic s9(5)      comp    value zero.
     03  ws-vatr-totalt  pic s9(5)      comp    value zero.
     03  ws-carr-totalt  pic s9(5)      comp    value zero.
     03  ws-disc-totalt  pic s9(5)      comp    value zero.
     03  v-exists        pic 9.
     03  ws-env-lines    pic 999       value zero.
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
     03  PL003          pic x(28) value "PL003 Hit Return To Continue".
     03  PL006          pic x(43) value "PL006 Note Details & Hit Return to continue".
*> Module specific
     03  PL201          pic x(57) value "PL201 Analyst records with desc, 'Emergency Name' created".
     03  PL202          pic x(36) value "PL202 You will need to update these".
     03  PL203          pic x(30) value "PL203 P.A. File Does Not Exist".
     03  PL204          pic x(40) value "PL204 Error writing to Open Item 4 File ".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  error-code          pic 999.
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wssys4.cob".
 copy "wsnames.cob".
*>
 01  to-day              pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          system-record-4
                          to-day
                          file-defs.
*>=======================================
*>
 mainline section.
*>===============
*>
     accept   ws-env-lines   from lines.
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
*>     open     input value-file.  *> creates if not exist via acas013
     perform  Value-Open.
*>              close value-file
*>              open  output  value-file.
*>     close    value-file.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15
                                                 File-Info
              end-call
              if    return-code not = zero          *> not = zero - No file found
                                                    *> This should have happened in sl910 invoice create
                    move 1 to ws-Process-Func ws-Sub-Function
                    call "sl070" using ws-calling-data
                                       system-record
                                       to-day
                                       file-defs
                    end-call
                    call  "CBL_CHECK_FILE_EXIST" using File-15
                                                       File-Info
                    if    return-code not = zero          *> not = zero - No file found
                          display   PL203 at 2301
                          display   PL003 at 2401
                          if     WS-Caller not = "xl150"  *> unlikely as sl070 was run.
                                 accept WS-Reply at 2430
                          end-if
                          move 8 to WS-Term-Code
                          goback
                    end-if
              end-if
     end-if
     move     1 to File-Key-No.
*>
     display  prog-name at 0101 with foreground-color 2 with erase eos.
     display  "Invoice Post Extract" at 0133 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
*>
     perform  PInvoice-Open. *>  open  i-o invoice-file value-file analysis-file.
     perform  Value-Open.
     perform  Analysis-Open.
     open     extend  open-item-file-4.
     if       fs-reply not = zero
              close open-item-file-4
              open output open-item-file-4.
*>
 read-loop.
     perform  PInvoice-Read-Next. *> read     invoice-file next record at end
     if       FS-Reply not = zero
              go to  close-files.
*>
     if       ih-test = zero
              go to header-analysis.
*>
     if       il-analyised
              go to  read-loop.
*>
     move     "P" to va-system.
     move     il-pa to  va-group.
     move     1  to  v-exists.
*>
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.  *> read     value-file  invalid key
     if       fs-reply = 21
              perform  create
              move zero to v-exists.
*>
     add      1  to  va-t-this.
     add      1  to  va-t-year.
     if       il-type not = 3
              add il-net to  va-v-this va-v-year
     else
              subtract il-net from va-v-this va-v-year.
*>
     if       v-exists = zero
              perform Value-Write    *> write  value-record
     else
              perform Value-Rewrite  *> rewrite  value-record.
     end-if
*>
     if       va-second = space
              go to read-loop.
*>
     move     space  to  va-second.
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.  *> read     value-file  invalid key
     if       FS-Reply = 21
              go to read-loop.
*>
     add      1  to  va-t-this.
     add      1 to va-t-year.
     if       il-type not = 3
              add il-net to  va-v-this va-v-year
     else
              subtract il-net from va-v-this va-v-year.
     move     1 to File-Key-No.
     perform  Value-Rewrite.  *> rewrite  value-record.
*>
     move     "z"  to  il-update.
     perform  PInvoice-Rewrite.    *> rewrite  invoice-record.
     go       to read-loop.
*>
 header-analysis.
*>**************
*>
     if       ih-analyised and applied
              go to read-loop.
*>
     perform  extract.
*>
     if       ih-analyised
              perform  PInvoice-Rewrite  *> rewrite invoice-record
              go to read-loop.
*>
     add      ih-c-vat ih-vat giving work-2.
     if       ih-type = 3
              multiply -1 by work-2.
     if       work-2 not = zero and
              ih-type not = 1
              add 1 to ws-vat-totalt
              add work-2 to ws-vat-totalv.
     if       work-2 not = zero and
              ih-type = 1
              add 1 to ws-vatr-totalt
              add work-2 to ws-vatr-totalv.
     move     ih-carriage to work-2.
     if       ih-type = 3
              multiply -1 by work-2.
     if       work-2 not = zero
              add 1 to ws-carr-totalt
              add work-2 to ws-carr-totalv.
     move     ih-deduct-amt to work-2.
     if       work-2 not = zero
              add 1 to ws-disc-totalt
              add work-2 to ws-disc-totalv.
*>
     move     "z" to ih-update.
     perform  PInvoice-Rewrite.  *>  rewrite  invoice-record.
     go       to read-loop.
*>
 close-files.
*>**********
*>
     move     "P" to va-system.
     move     "vi" to va-group.
     move     ws-vat-totalt to work-3.
     move     ws-vat-totalv to work-2.
     perform  store-specials
     move     "vj" to va-group.
     move     ws-vatr-totalt to work-3.
     move     ws-vatr-totalv to work-2.
     perform  store-specials
     move     "za" to va-group.
     move     ws-carr-totalt to work-3.
     move     ws-carr-totalv to work-2.
     perform  store-specials
     move     "zb" to va-group.
     move     ws-disc-totalt to work-3.
     move     ws-disc-totalv to work-2.
     perform  store-specials
     perform  PInvoice-Close.  *> close   invoice-file analysis-file value-file
     perform  Value-Close.
     perform  Analysis-Close.
     close    open-item-file-4.
*>
     if       Anal-Created not = zero
              display PL201 at 1201 with foreground-color 2
              display PL202 at 1401 with foreground-color 2
              if     WS-Caller not = "xl150"
                     display PL006 at 1601 with foreground-color 2
                     accept ws-reply at 1645
              end-if
              goback.                           *> Yep, I know but just in case extra code goes here!
*>
 menu-exit.
     goback.
*>
*>****************************************************
*>                   Procedures                      *
*>****************************************************
*>
 create       section.
*>===================
*>
 Create-Main.
     move     va-code  to  WS-Pa-Code.
*>
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.   *> read     analysis-file  invalid key
     if       FS-Reply = 21 or = 23
              go to  Create-Anal.
*>
     move     WS-Analysis-record  to  WS-Value-record.
     move     zero  to  va-t-this  va-t-last va-t-year
                        va-v-this  va-v-last va-v-year.
*>
     if       va-second = space
              go to  main-exit.
*>
     move     va-code  to  save-code.
*>
     move     space    to  va-second.
     move     va-code  to  WS-Pa-Code.
*>
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.  *> read     analysis-file  invalid key
     if       FS-Reply = 21
              move  save-code  to  WS-Pa-Code
              go to  main-exit.
*>
     move     WS-Analysis-record  to  WS-Value-record
     move     zero  to  va-t-this  va-t-last  va-t-year
                        va-v-this  va-v-last  va-v-year.
*>
     perform  Value-Write.  *> write    value-record.
*>
     move     save-code  to  va-code  WS-Pa-Code.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.  *> read     analysis-file  invalid key
     if       FS-Reply = 21
              go to  main-exit.
*>
     move     WS-Analysis-record  to  WS-Value-record
     move     zero  to  va-t-this  va-t-last  va-t-year
                        va-v-this  va-v-last  va-v-year.
*>
     go       to main-exit.
*>
 Create-Anal.
     move     va-code to WS-Pa-Code.
     move     zero to pa-gl.
     move     spaces to pa-print.
     move     "Emergency Name - Missing" to pa-desc.
     move     1 to File-Key-No.
     perform  Analysis-Write.          *> write    analysis-record.
     if       pa-second not = space
              move space to pa-second
              perform Analysis-Write.  *> write analysis-record.
     move     1 to Anal-Created.
     go       to create-Main.
*>
 main-exit.   exit section.
*>
 store-specials  section.
*>======================
*>
     move     1  to  v-exists.
*>
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.  *> read     value-file  invalid key
     if       FS-Reply = 21
              perform  create
              move zero to v-exists.
*>
     add      work-3 to  va-t-this.
     add      work-3 to  va-t-year.
     add      work-2 to  va-v-this.
     add      work-2 to  va-v-year.
*>
     if       v-exists = zero
              perform Value-Write     *> write  value-record
     else
              perform Value-Rewrite.  *> rewrite value-record.
*>
     move     space  to  va-second.
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.  *> read     value-file  invalid key
     if       FS-Reply = 21
              go to main-exit.
*>
     add      work-3 to  va-t-this.
     add      work-3 to  va-t-year.
     add      work-2 to  va-v-this.
     add      work-2 to  va-v-year.
     perform  Value-Rewrite.  *> rewrite  value-record.
*>
 main-exit.   exit section.
*>
 extract section.
*>==============
*>
*> only Process header records, drop pro-formas.
*>   ignore records which have already been copied.
*>
     if       applied
              go to  main-exit.
*>
      initialise OI-Header.   *> 07/01/18  JIC
     move     ih-supplier to  oi-supplier.
     move     ih-invoice  to  oi-invoice.
     move     ih-date     to  oi-date.
     move     zero        to  oi-b-nos oi-b-item.
     move     ih-type     to  oi-type.
     move     ih-ref      to  oi-ref.
     move     ih-order    to  oi-order.
     move     zero        to  oi-p-c.
     move     ih-net      to  oi-net.
     move     zero        to  oi-extra.
     move     ih-carriage to  oi-carriage.
     move     ih-vat      to  oi-vat.
     move     zero        to  oi-discount.
     move     ih-c-vat    to  oi-c-vat.
     move     zero        to  oi-e-vat.
     move     zero        to  oi-paid.
     move     ih-deduct-amt  to  oi-deduct-amt.
     move     zero           to  oi-deduct-vat.
     move     ih-deduct-days to  oi-deduct-days.
     move     ih-days     to  oi-days.
     move     zero        to  oi-status oi-date-cleared.
     move     space       to  oi-applied oi-hold-flag.
*>
     if       ih-type = 3
              multiply  -1  by  oi-net
              multiply  -1  by  oi-carriage
              multiply  -1  by  oi-vat
              multiply  -1  by  oi-c-vat.
*>
     move     ih-cr to oi-cr.
*>
     if       ih-type not = 1
              add ih-net ih-carriage ih-vat ih-c-vat giving ws-inv-amt.
     if       ih-type = 2
              add ws-inv-amt to pl-invoices-this-month.
     if       ih-type = 3
              add ws-inv-amt to pl-credit-notes-this-month.
*>
     move     "Z"  to  ih-status.   *> 07/01/18 was "z"
     write    open-item-record-4.
     if       fs-reply not = zero
              perform  a01-Eval-Status
              display  PL204         at line ws-23-lines col 1
              display  fs-reply      at line ws-23-lines col 41
              display  Exception-Msg at line ws-23-lines col 44
              display  PL006         at line ws-lines col 01
              accept   ws-reply      at line ws-lines col 45
     end-if.
*>
 main-exit.   exit.
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
 a01-Eval-Status section.
     move     spaces to exception-msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by exception-msg.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
