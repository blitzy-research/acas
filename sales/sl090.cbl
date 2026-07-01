       >>source free
*>***********************************************
*>                                              *
*>             Payment Proof Sort               *
*>                                              *
*>        Only used for Cobol files             *
*>***********************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl090.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 18/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Payment Proof Sort
*>                        but only for Cobol files (not rdb).
*>                        O/p used by sl095 Only.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.
*>                        acas019  ->
*>                         otm3MT.
*>**
*>    Error messages used.
*>                        SL003
*>                        SL116
*>                        SL142
*>                        SL143.
*>**
*> Changes:
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 08/12/11 vbc - .01 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 02/06/13 vbc - .02 Test to make sure that i/p & o/p records are the same size.
*> 24/10/16 vbc - .03 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 21/01/17 vbc - .04 Replaced refs to maps99 for display msgs.
*> 25/01/17 vbc       Dry testing completed.
*> 07/02/17 vbc - .05 Updated FD/WS for 019 and replaced cobol verbs
*>                    for access to FH/DALs.
*>                    Code to bypass if not using Cobol files as sort
*>                    not needed for tables as we do selective read.
*>                    Changed sort rec size to 118 after OI3 change.
*> 22/08/17 vbc -     Added some comments in remarks and removed unneeded
*>                    test condition that is tested (with exit) for previously.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
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
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
*> copy "seloi3.cob".
 copy "slselois.cob".
*>
     select       sort-file   assign  file-21.
 data                    division.
*>===============================
*>
 file section.
*>------------
*>
*> copy "fdoi3.cob".
*>
 copy "slfdois.cob".
*>
 sd  sort-file.
*>
 01  Sort-Record.                         *> 118.
     03  s-customer       pic x(7).
     03  s-invoice        pic 9(8).           *> was binary-long.
     03  s-date           binary-long.
     03  s-batch                         comp.
       05  s-b-nos        pic 9(5).
       05  s-b-item       pic 999.
     03  s-type           pic 9.
     03  filler           pic x(92).
*>
 working-storage section.
*>----------------------
 77  prog-name            pic x(15) value "SL090 (3.3.00)".
 77  ws-ITM3-Length       pic 999   value zero.
 77  ws-ITMS-Length       pic 999   value zero.
 77  ws-reply             pic x.
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
 01  Error-Messages.
*> System Wide
     03  SL003           pic x(28) value "SL003 Hit Return To Continue".
*> Module specific
     03  SL116           pic x(38) value "SL116 Note: and hit return to continue".
     03  SL142           pic x(39) value "SL142 No Payments To Correct/Proof/Post".
     03  SL143           pic x(50) value "SL143 System Error - OTM3 and OTMS not the same - ".
     03  SL143B          pic x(11) value "& Sorted - ".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
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
     if       not FS-Cobol-Files-Used  *> Will use fn-Read-Next-Sorted-By-Batch (32)
              goback returning 4
     end-if.
*>
*> Let make sure oi3 and ois are are same lengths.
*>
     display  prog-name at 0101 with erase eos.
     move     function length (Open-Item-Record-3) to ws-ITM3-Length.
     move     function length (Sort-Record)        to ws-ITMS-Length.
     if       ws-ITM3-Length NOT = ws-ITMS-Length
              display SL143    at 1201 with foreground-color 3 highlight *> 50
              display ws-ITM3-Length at 1252 with foreground-color 3
              display SL143B   at 1257 with foreground-color 3
              display ws-ITMS-Length at 1268 with foreground-color 3
              display SL116    at 1401 with foreground-color 3
              accept  ws-reply at 1440
              exit program
     end-if
*>
*> Good, we can continue
*>
     if       S-Flag-P = 0    *> do we have data ?
              display SL142  at 0501
              display SL003  at 2401
              accept ws-reply at 2430
              go to menu-exit.
*>
     move     "Y" to oi-3-flag.
     perform  sorting-1.
*>
 menu-exit.
     exit     program.
*>
 sorting-1    section.
*>===================
*>
     sort     sort-file
              on  ascending key   s-b-nos
                                  s-b-item
              on  descending key  s-type
              on  ascending key   s-date
                                  s-invoice
              input procedure is input-to-sort
              giving  open-item-file-s.
*>
 main-exit.   exit section.
*>********    ****
*>
 input-to-sort           section.
*>==============================
*>
     perform  OTM3-Open-Input.        *> open input  open-item-file-3.
     if       fs-reply not = zero
              perform  OTM3-Close     *> close open-item-file-3
              open output open-item-file-s  *> create empty file
              close open-item-file-s
              go to main-exit.
*>
 process-input.
*>************
*>
     perform  OTM3-Read-Next.     *>  read open-item-file-3 next record at end
     if       fs-reply = 10
              go to  end-of-input.
*>
     if       oi-type = 1 or 3                    *> Ignore Receipts & Cr. Notes
              go to process-input.
     if       zero = oi-b-nos and oi-b-item       *> batch data zero so no payments
              go to process-input.
*>
     release  sort-record from  open-item-record-3.
     go       to  process-input.
*>
 end-of-input.
*>***********
*>
     perform  OTM3-Close.    *> close  open-item-file-3.
*>
 main-exit.   exit section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
