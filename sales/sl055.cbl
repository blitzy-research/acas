       >>source free
*>*****************************************************************
*>                                                                *
*>             INVOICE   POST - EXTRACT  ANALYSIS                 *
*>                                                                *
*>     Passes o/p ITM2 to sl060 from invoice records              *
*>     in a 2 step process                                        *
*>     having also update Analysis and value recs from invoice    *
*>      line items.                                               *
*>              This is part One.                                 *
*>*****************************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl055.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 18/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Proof Report Extract & Analysis.
*>                        Updates analysis values from body items and headers, invoice
*>                        and passes invoices to itm2 then sl060 is run via sales.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.
*>                        acas013  ->
*>                         valueMT.
*>                        acas015  ->
*>                         analMT.
*>                        acas016  ->
*>                         invoiceMT.
*>**
*>    File Used.
*>                        OTM2. TEMP (Only) Open Item File 2 - Preposting.
*>**
*>    Error messages used.
*>                        SL002.
*>                        SL121.
*>                        SL122.
*>                        SL123.
*>                        SL124
*>                        SL125.
*>                        SL126.
*>
*>    Changes:
*> 15/01/83 Sjw - 400420
*> 13/02/83 Vbc - 400432.
*> 21/02/83 Vbc - Check For Invoices Not Yet Printed.
*> 18/04/83 Vbc - On Credit Notes;Change Mult -1 From Ih To Io.
*> 26/04/83 Vbc - Zeroise Oi-Line After Writing Out Record.
*> 23/10/83 Vbc - Conversion To Cis Cobol.
*> 19/12/83 Vbc - Allow For System Record 4.
*> 01/01/84 Vbc - Support Oi-Hold-Flag.
*> 28/03/84 Vbc - Tidy Up Display Sign-On Message.
*> 31/03/84 Vbc - Only Inv Header Recs Are Copied To Openitm File.
*> 01/04/84 Vbc - Put Wsinv2 Into Fdinv=Fdinv2, & Dont Copy Into
*>                Ws On Reading, Writing ;Speed Prog.
*> 09/05/84 Vbc - Support For Indexed Openitm File
*> 09/10/84 Vbc - Insert Analysis Code From Sl130.
*> 13/11/84 Vbc - Extract:Applied Test Go To Main-Ex,(Exit).
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 24/11/11 vbc - .03 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .04 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .05 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 21/03/12 vbc - .06 Cosmetic, killed move/test on il-product/il-comment to just test product(1:1)
*>                    got rid of calls to maps99 except for a fail-fix-fail scenario !
*> 24/10/16 vbc - .07 ALL programs now using wsnames.cob in copybooks
*> 30/10/16 vbc - .08 Support for RDB on Value & Analysis tables instead of cobol files
*>                    using acas013 (Value) & acas015 (Analysis).
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*>                    Removed refs to file-status as redundant.
*>                    Replace refs to maps99 for displays.
*> 23/01/17 vbc       Dry testing completed.
*> 07/02/17 vbc - .09 Updated FD/WS for 016 and replaced cobol verbs
*>                    for access to FH/DALs.
*> 16/04/17 vbc -     Dry check for slinvoiceMT. Processes all Invoice recs.
*> 20/08/17 vbc - .10 Extra notes in Remarks section above on prog operation.
*> 22/03/18 vbc - .11 Dont stop if error when run by xl150.
*> 10/12/22 vbc   .12 Added para after some sections 4 GC 3.2 warning msgs.
*> 04/05/23 vbc - .13 Changed Eval-Status to a01-Eval-Status.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 18/01/25 vbc - .14 Replace SL123 with SL125 & 123 deleted.
*>                    Make da010-Read-Loop an inline perform.
*> 26/08/25 vbc   .15 Change description of Emergency anal. rec.
*>                    Added new msgs 124, 126 for it.
*>                    Added test for fs-reply on write itm2.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> These files and programs is part of the Applewood Computers Accounting
*> System and is copyright (c) Vincent B Coen. 1976-2026 and later.
*>
*> This program is now free software; you can redistribute it and/or modify it
*> under the terms of the GNU General Public License as published by the
*> Free Software Foundation; version 3 and later as revised for personal
*> usage only and that includes for use within a business but without
*> repackaging or for Resale in any way.
*>
*> Persons interested in repackaging, redevelopment for the purpose of resale or
*> distribution in a rental mode must get in touch with the copyright holder
*> with your commercial plans and proposals.
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
 input-output            section.
 file-control.
*>
 copy "seloi2.cob".
*> copy "selinv.cob".
*> copy "selval.cob".
*> copy "selanal.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>
 copy "fdoi2.cob".
 copy "slwsoi.cob".
*> copy "fdinv2.cob".
*> copy "fdval.cob".
*> copy "fdanal.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15)    value "SL055 (3.3.00)".
 77  Exception-Msg       pic x(25)    value spaces.
*>
 copy "wsfnctn.cob".
 copy "wsval.cob".  *>      replacing VA-Code    by WS-VA-Code.
 copy "wsanal.cob".
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                                pic x(137).
*>
*> REMARK OUT ANY IN USE
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
 01  error-code          pic 999.
*>
 01  ws-data.
     03  ws-reply        pic x.
     03  ws-p-flag       pic 9                value zero.
     03  ws-Anal-Flag    pic 9                value zero. *> 1 = anal rec created
     03  save-code       pic xxx.
     03  v-exists        pic 9.
     03  ws-inv-amt      pic s9(7)v99  comp-3 value zero.
     03  work-2          pic s9(7)v99  comp-3 value zero.
     03  ws-vat-totalv   pic s9(7)v99  comp-3 value zero.
     03  ws-vatr-totalv  pic s9(7)v99  comp-3 value zero.
     03  ws-carr-totalv  pic s9(7)v99  comp-3 value zero.
     03  ws-disc-totalv  pic s9(7)v99  comp-3 value zero.
     03  work-3          pic s9(5)     comp   value zero.
     03  ws-vat-totalt   pic s9(5)     comp   value zero.
     03  ws-vatr-totalt  pic s9(5)     comp   value zero.
     03  ws-carr-totalt  pic s9(5)     comp   value zero.
     03  ws-disc-totalt  pic s9(5)     comp   value zero.
     03  b               pic 99        comp   value zero.
     03  c               pic 99        comp   value zero.
     03  ws-env-lines    pic 999       value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
     03  ws-Todays-Year.
         05  WS-Todays-Year9 pic 9(4)          value zero.
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
*>       NONE
     03  SL002          pic x(31) value "SL002 Note error and hit return".
*> Module specific
     03  SL121          pic x(40) value "SL121 Error writing to Open Item 2 File ".
     03  SL122          pic x(51) value "SL122 Unprinted Invoices Exist. Correct & Run Again".
     03  SL123          pic x(57) value "SL123 Analyst records with desc, 'Emergency Name' created".
     03  SL124          pic x(29) value "SL124 Analysis record created".
     03  SL125          pic x(34) value "SL125 Analysis File Does Not Exist".
     03  SL126          pic x(35) value "SL126 You will need to update this".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
linkage section.
*>**************
*>
 01  to-day              pic x(10).
 copy "wsnames.cob".

 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wssys4.cob".
*>
 procedure division using ws-calling-data
                          system-record
                          system-record-4
                          to-day
                          file-defs.
*>=======================================
*>
*> Declaratives.
*>
*> File-Error-On-OTM2 section.
*>
*>     use after error procedure on open-item-file-2.
*> a00-OTM2-Error-1.
*>     if       fs-reply not = zero
*>              perform  a01-Eval-Status
*>              display  SL121         at line ws-23-lines col 1
*>              display  fs-reply      at line ws-23-lines col 41
*>              display  Exception-Msg at line ws-23-lines col 44
*>              display  SL002         at line ws-lines col 01
*>              accept   ws-reply      at line ws-lines col 33
*>     end-if
*>     goback.
*>
*> a01-Eval-Status.
*>==============
*>
*>     move     spaces to exception-msg.
*> copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
*>                                     msg    by exception-msg.
*>
*> main-exit.   exit.
*>
*> end declaratives.
*>
 da000-mainline section.
*>=====================
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
     perform  Value-Open-Input.
     if       fs-reply not = zero
              perform Value-Close
              perform Value-Open-Output
     end-if
     perform Value-Close.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15   *> Analysis
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                                                    *> This should have happened in sl910 invoice create
                    move 1 to ws-Process-Func ws-Sub-Function    *> Create default entries in Analysis
                    call "sl070" using ws-calling-data           *> and Value files
                                       system-record
                                       to-day
                                       file-defs
                    call  "CBL_CHECK_FILE_EXIST" using File-15   *> only if user aborts
                                                       File-Info *> creation
                    if    return-code not = zero          *> not = zero - No file found Only if the call failed for some unknown reason
                          display  SL125  at 2301
                          display  SL002  at 2401
                          if     WS-Caller not = "xl150"  *> unlikely as sl070 was run.
                                 accept WS-Reply at 2435
                          end-if
                          move 8 to WS-Term-Code
                          goback
                    end-if
              end-if
     end-if
     move     1 to File-Key-No.
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Invoice Post Extract" at 1201  with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0171 with foreground-color 2.
*>
     perform  Invoice-Open.
     perform  Value-Open.
     perform  Analysis-Open.
     open     extend open-item-file-2.
     if       fs-reply not = zero
              close open-item-file-2
              open output open-item-file-2.
*>
 da010-Read-Loop.
     perform  until FS-Reply = 10    *> changed 18/01/25 for clean up using inline perform
              perform  Invoice-Read-Next
              if       fs-reply = 10
                       go to da040-Close-Files
              end-if
              if       ih-test = zero
                       exit perform   *> Header-Analysis
              end-if
              if       il-analyised
                       exit perform cycle
              end-if
              if       il-product (1:1) = "/"		*> comment only
                       exit perform cycle
              end-if
              move     "S"   to va-system
              move     il-pa to va-group
              move     1     to v-exists
              move     1 to File-Key-No
              perform  Value-Read-Indexed
              if       fs-reply = 21 or = 23
                       perform  db000-Create
                       move zero to v-exists
              end-if
              add      1  to  VA-T-This
              add      1  to  VA-T-Year
              if       il-type not = 3			*> Cr. notes
                       add il-net to  VA-V-This
                       add il-net to  VA-V-Year
              else
                       subtract il-net from VA-V-This
                       subtract il-net from VA-V-Year
              end-if
              if       v-exists  = zero
                       perform  Value-Write
              else
                       perform  Value-Rewrite
              end-if
              if       va-second  = space
                       exit perform cycle
              end-if
              move     space  to  va-second
              move     1 to File-Key-No
              perform  Value-Read-Indexed
              if       fs-reply = 21 or = 23
                       exit perform cycle
              end-if
              add      1 to VA-T-This
              add      1 to VA-T-Year
              if       il-type not = 3
                       add il-net to  VA-V-This
                       add il-net to  VA-V-Year
              else
                       subtract il-net from VA-V-This
                       subtract il-net from VA-V-Year
              end-if
              perform  Value-Rewrite
              move     "Z"  to  il-update 		*> Analysied flag changed from z (1/6/13)
              perform  Invoice-Rewrite
              exit     perform cycle
     end-perform.
*>
 da020-Header-Analysis.				*> Headers only
     if       ih-analyised and applied
              go to da010-Read-Loop.
*>
     if       ih-type = 4                	*> Proforma's
              go to da030-Skip-Invoice.
*>
     if       pending
       or     ih-status-L not = "L"
              move 1 to ws-p-flag
              go to da030-Skip-Invoice.
*>
     perform  dd000-Extract.
*>
     if       ih-analyised
              perform  Invoice-Rewrite
              go to da010-Read-Loop.
*>
     add      ih-c-vat ih-vat ih-e-vat giving work-2.
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
     if       ih-type = 3
              multiply -1 by work-2.
     if       work-2 not = zero
              add 1 to ws-disc-totalt
              add work-2 to ws-disc-totalv.
*>
     move     "Z" to ih-update.
     perform  Invoice-Rewrite.
     go       to da010-Read-Loop.
*>
 da030-Skip-Invoice.
     add      1 to invoice-nos.
     move     zeros to item-nos.
     set      fn-not-less-than to true.
     perform  Invoice-Start.        *>  start invoice-file key not < invoice-key invalid key
     if       fs-reply = 21 or = 23
              go to da040-Close-Files.
     go       to da010-Read-Loop.
*>
 da040-Close-Files.
     move     "Svo" to va-code.
     move     ws-vat-totalt to work-3.
     move     ws-vat-totalv to work-2.
     perform  dc000-Store-Specials
     move     "vp" to va-group.
     move     ws-vatr-totalt to work-3.
     move     ws-vatr-totalv to work-2.
     perform  dc000-Store-Specials
     move     "zc" to va-group.
     move     ws-carr-totalt to work-3.
     move     ws-carr-totalv to work-2.
     perform  dc000-Store-Specials
     move     "zd" to va-group.
     move     ws-disc-totalt to work-3.
     move     ws-disc-totalv to work-2.
     perform  dc000-Store-Specials
     perform  Invoice-Close.
     perform  Value-Close.
     perform  Analysis-Close.
     close    open-item-file-2.
*>
     if       ws-p-flag not = zero   *> Unprinted invoice are present
              display SL122        at line ws-23-lines col 1
              if     WS-Caller not = "xl150"
                     display SL002        at line ws-lines    col 1
                     accept  ws-reply     at line ws-lines    col 33
              end-if
              goback.               *> Yep, I know but just in case extra code goes here!
*>
     if       ws-Anal-Flag not = zero
              display SL123 at 1201 with foreground-color 2
              display SL126 at 1401 with foreground-color 2
              if     WS-Caller not = "xl150"
                     display SL002 at 1601 with foreground-color 2
                     accept ws-reply at 1633
              end-if
              goback.                           *> Yep, I know but just in case extra code goes here!
*>
 da999-Menu-Exit.
     goback.
*>
*>****************************************************************
*>      P R O C E D U R E S                                      *
*>****************************************************************
*>
 db000-Create section.
*>===================
*>
 DB000-Create-Main.
     move     va-code  to  WS-PA-Code.
*>
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     if       FS-Reply = 21 or = 23
              go to db010-Create-Anal.
*>
     move     WS-Analysis-Record  to WS-Value-Record
     move     zero  to  VA-T-This  va-t-last VA-T-Year
                        VA-V-This  va-v-last VA-V-Year.
*>
     if       va-second  = space
              go to db999-Main-Exit.
*>
     move     va-code  to  save-code.
*>
     move     space    to  va-second.
     move     va-code  to  WS-PA-Code.
*>
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     if       FS-Reply = 21
              move  save-code  to  WS-PA-Code
              go to db999-Main-Exit.
*>
     move     WS-Analysis-Record  to WS-Value-Record
     move     zero  to  VA-T-This  va-t-last  VA-T-Year
                        VA-V-This  va-v-last  VA-V-Year.
*>
     perform  Value-Write.
*>
     move     save-code  to  va-code  WS-PA-Code.
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     if       FS-Reply = 21
              go to  db999-Main-Exit.
*>
     move     WS-Analysis-Record  to WS-Value-Record
     move     zero  to  VA-T-This  va-t-last  VA-T-Year
                        VA-V-This  va-v-last  VA-V-Year.
*>
     go       to db999-Main-Exit.
*>
 db010-Create-Anal.
     move     va-code to WS-PA-Code.
     move     zero to pa-gl.
     move     spaces to pa-print.
     move     "Emergency Name - Missing" to pa-desc.
     move     1 to File-Key-No.
     perform  Analysis-Write.
     if       pa-second not = space
              move space to pa-second
              perform  Analysis-Write.
     move     1 to ws-Anal-Flag.
     go       to db000-Create-Main.
*>
 db999-Main-Exit.
     exit     section.
*>
 dc000-Store-Specials  section.
*>============================
*>
     move     1  to  v-exists.
*>
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.
     if       fs-Reply = 21
              perform  db000-Create
              move zero to v-exists.
*>
     add      work-3 to  VA-T-This.
     add      work-3 to  VA-T-Year.
     add      work-2 to  VA-V-This.
     add      work-2 to  VA-V-Year.
*>
     if       v-exists  = zero
              perform  Value-Write
     else
              perform  Value-Rewrite.
*>
     move     space  to  va-second.
     move     1 to File-Key-No.
     perform  Value-Read-Indexed.
     if       FS-Reply = 21
              go to dc999-Main-Exit.
*>
     add      work-3 to  VA-T-This.
     add      work-3 to  VA-T-Year.
     add      work-2 to  VA-V-This.
     add      work-2 to  VA-V-Year.
     perform  Value-Rewrite.
*>
 dc999-Main-Exit.
     exit     section.
*>
 dd000-Extract section.
*>====================
*>
*> Only process header records here, drop pro-formas.
*>  ignore records which have already been copied.
*>
     if       applied
              go to dd999-Main-Ex.
*>
     initialize oi-header with filler.
     move     ih-p-c      to  oi-p-c.
     move     ih-invoice  to  oi-invoice.
     move     ih-customer to  oi-customer.
     move     ih-date     to  oi-date.
     move     zero        to  oi-b-nos oi-b-item.
     move     ih-order    to  oi-description.
     move     ih-net      to  oi-net.
     move     ih-extra    to  oi-extra.
     move     ih-carriage to  oi-carriage.
     move     ih-vat      to  oi-vat.
     move     ih-c-vat    to  oi-c-vat.
     move     ih-e-vat    to  oi-e-vat.
     move     ih-discount to  oi-discount.
     move     zero        to  oi-paid.
     move     ih-deduct-amt  to oi-deduct-amt.
     move     ih-deduct-vat  to oi-deduct-vat.
     move     ih-deduct-days to oi-deduct-days.
     move     zero        to  oi-status oi-date-cleared oi-days.   *> hmm, initialised, not needed but acts as a note
     move     ih-type     to  oi-type.				   *> oi-days is credit terms, status = open
     move     space to oi-applied oi-unapl oi-hold-flag.
*>
     if       ih-type  = 3                                       *>  Cr. Notes
              multiply -1  by  oi-deduct-amt
              multiply -1  by  oi-deduct-vat
              multiply -1  by  oi-net
              multiply -1  by  oi-extra
              multiply -1  by  oi-carriage
              multiply -1  by  oi-vat
              multiply -1  by  oi-c-vat
              multiply -1  by  oi-e-vat
              multiply -1  by  oi-discount.
*>
     move     ih-cr to oi-cr.
*>
     if       ih-type not = 1                                    *> not Receipts
              add ih-net ih-extra ih-carriage ih-discount ih-vat
                  ih-c-vat ih-e-vat ih-deduct-amt ih-deduct-vat
                     giving ws-inv-amt.
     if       ih-type = 2                                        *> Invoice
              add ws-inv-amt to sl-invoices-this-month.
     if       ih-type = 3                                        *> Cr. Note
              add ws-inv-amt to sl-credit-notes-this-month.
*>
     move     "Z"  to ih-status.
     move     "A"  to ih-status-A.
     write    oi-header.    *> OTM2
     if       fs-reply not = zero
              perform  a01-Eval-Status
              display  SL121         at line ws-23-lines col 1
              display  fs-reply      at line ws-23-lines col 41
              display  Exception-Msg at line ws-23-lines col 44
              display  SL002         at line ws-lines col 01
              accept   ws-reply      at line ws-lines col 33
     end-if.
*>
 dd999-Main-Ex.
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
 a01-Eval-Status section.
     move     spaces to exception-msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by exception-msg.
*>
 a01-exit.    exit section.

 copy "Proc-ACAS-FH-Calls.cob".
*>
