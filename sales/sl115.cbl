       >>source free
*>***************************************************
*>                                                  *
*>           Statement, Dunning & Trial Balance     *
*>                         Sort                     *
*>          [ sl110, sl120, sl190 ]                 *
*>***************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl115.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 24/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Pre Statement & Trail Balance Sort.
*>                        As used in sl110, sl120, sl190 if cobol files used.
*>                        Also used via by sl060
*>
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>
*>    Called Modules.
*>                        acas019  ->
*>                         otm3MT.     ONLY for Table processing.
*>**
*>    Error messages used.
*>                        SL003
*>                        SL151.
*>
*>**
*> Changes:
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 25/11/11 vbc - .01 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .02 Support for path+filenames.
*> 09/12/11 vbc - .03 Updated version to 3.01.nn
*> 02/06/13 vbc - .04 Added Sort file layout and size to 114 bytes.
*> 24/10/16 vbc - .05 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 21/01/17 vbc - .06 Replace refs to Maps99 by display msgs.
*> 25/01/17 vbc       Dry testing completed.
*> 09/02/17 vbc - .07 Updated FD/WS for 019 and replaced cobol verbs
*>                    for access to FH/DALs when not using Cobol files.
*>                    Sort requirements removed (sl110,120,190) when
*>                    processing RDB tables as the sort step removed
*>                    in place of read Table by Order.
*>                    Note: When using RDB tables there is no sorting,
*>                    Data is from selecting by order.
*> 23/08/17 vbc -     Dry tested.
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
 environment             division.
*>===============================
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
 file-control.
*>-----------
*> copy "seloi3.cob".
 copy "slselois.cob".
     select       sort-file   assign  file-21.
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*> copy "fdoi3.cob".
 copy "slfdois.cob".
 sd  sort-file.
*>
 01  sort-record.			*> 118 bytes (09/02/17)
     03  s-customer       pic x(7).
     03  s-invoice        pic 9(8).       *> was binary-long.
     03  s-date           binary-long.
     03  s-batch                         comp.
         05  s-b-nos      pic 9(5).
         05  s-b-item     pic 999.
     03  s-type           pic 9.
     03  filler           pic x(92).
*>
 working-storage section.
*>----------------------
 77  prog-name            pic x(15) value "SL115 (3.3.0)".
 77  ws-reply             pic x     value space.
*>
 copy "wsfnctn.cob".
 copy "slwsoi3.cob".
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
*>     03  WS-OTM3-Record         pic x.
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
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide
     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
*> Module specific
     03  SL151          pic x(35) value "SL151 Sales Transactions Not Posted".
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
*>=======================================
*>
 init01 section.
*>
*>  First check if not using Cobol files - then sort not needed.
*>
     if       not FS-Cobol-Files-Used    *> Will use fn-Read-By-Name (33)
              goback returning 4
     end-if.
*>
     if       oi-3-flag = "N"
              go to  menu-exit. *> using previous sorted file
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-19    *> Open ITM3 file
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    move     "Y" to oi-3-flag
                    display  SL151  at 2301
                    display  SL003  at 2401
                    accept ws-reply at 2430
                    go       to menu-exit.
*>
     perform  Sorting-1.
     move     "N"  to  oi-3-flag.
*>
 menu-exit.
     exit     program.
*>
 Sorting-1    section.
*>===================
*>
     sort     sort-file
              on  ascending key  s-customer
                                 s-date
                                 s-invoice
                                 s-type
              input procedure input-to-sort
              giving  open-item-file-s.
*>
 main-exit.   exit section.
*>********    ************
*>
 input-to-sort  section.
     perform  OTM3-Open-Input.     *> open  input open-item-file-3.
*>
 process-input.
     perform  OTM3-Read-Next.      *> read open-item-file-3 next record at end
     if       fs-reply = 10
              go to end-of-input.
*>
     release  sort-record from open-item-record-3.
     go       to process-input.
*>
 end-of-input.
     perform  OTM3-Close.          *> close open-item-file-3.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
