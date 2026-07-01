       >>source free
*>************************************************
*>                                               *
*>            Payment  Proof  Sort               *
*>                                               *
*>************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         pl090.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 17/04/84
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Payment Proof Sort.
*>*
*>    Version.            See Prog-Name & Date-Comped In Ws.
*>**
*>    Called Modules.
*>                        acas029  ->
*>                         otm5MT.
*>**
*>    Error messages used.
*>                        PL003
*>                        PL116
*>                        PL142
*>                        PL143.
*>**
*> Changes:
*>
*> 22/03/09 vbc - Migration to Open Cobol v3.00.00,
*> 03/04/09 vbc - Remove displays, not needed.
*> 15/12/11 vbc - .01 Support for path+filenames.
*>                    Updated version to 3.01.nn
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 09/01/18 vbc - .02 All programs upgraded to v3.02 for RDB processing.
*>                    Replaced refs to maps99 for display msgs.
*>                    Updated FD/WS and replaced cobol verbs
*>                    for access to FH/DALs.
*>                    Code to bypass if not using Cobol files as sort
*>                    not needed for tables as we do selective read.
*>                    Changed sort rec size to 113 after OI5 change.
*>                    Added some comments in remarks and removed unneeded
*>                    test condition that is tested (with exit) for previously.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 26/08/25 vbc   .03 Chg PL116 to PL006.
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
*>------------
*>
*> copy "seloi5.cob".
 copy "plselois.cob".
     select       sort-file   assign  file-21.
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdoi5.cob".
*>
 copy "plfdois.cob".
*>
 sd  sort-file.
*>
 01  sort-record.
     03  s-supplier       pic x(7).
     03  s-invoice        pic 9(8).  *> was binary-long.
     03  s-date           binary-long.
     03  s-batch                         comp.
         05  s-b-nos      pic 9(5).
         05  s-b-item     pic 999.
     03  s-type           pic 9.
     03  filler           pic x(87).  *> was 83 for rec 113.
*>
 working-storage section.
*>----------------------
 77  prog-name            pic x(15) value "PL090 (3.3.00)".
 77  ws-ITM5-Length       pic 999   value zero.
 77  ws-ITMS-Length       pic 999   value zero.
 77  ws-reply             pic x.
*>
 copy "wsfnctn.cob".
 copy "plwsoi5C.cob".
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
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
*>     03  WS-OTM5-Record         pic x.
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
     03  PL003           pic x(28) value "PL003 Hit Return To Continue".
     03  PL006           pic x(38) value "PL116 Note: and hit return to continue".
*> Module specific
     03  PL142           pic x(39) value "PL142 No Payments To Correct/Proof/Post".
     03  PL143           pic x(50) value "PL143 System Error - OTM5 and OTMS not the same - ".
     03  PL143B          pic x(11) value "& Sorted - ".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
*> 01  error-code          pic 999.
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
     if       not FS-Cobol-Files-Used    *> Will use fn-Read-Next-Sorted-By-Batch (32)
              goback returning 4
     end-if.
*>
*> Let make sure oi5 and ois are are same lengths.
*>
     display  prog-name at 0101 with erase eos.
     move     function length (Open-Item-Record-5) to ws-ITM5-Length.
     move     function length (Sort-Record)        to ws-ITMS-Length.
     if       ws-ITM5-Length NOT = ws-ITMS-Length
              display PL143    at 1201 with foreground-color 3 highlight *> 50
              display ws-ITM5-Length at 1252 with foreground-color 3
              display PL143B   at 1257 with foreground-color 3
              display ws-ITMS-Length at 1268 with foreground-color 3
              display PL006    at 1401 with foreground-color 3
              accept  ws-reply at 1440
              exit program
     end-if
*>
*> Good, we can continue
*>
     if       P-Flag-P = 0    *> do we have data ?
              display PL142  at 0501
              display PL003  at 2401
              accept ws-reply at 2430
              go to menu-exit.
*>
     move     "Y" to OI-5-Flag.
     perform  sorting-1.
*>
 menu-exit.
     goback.
*>
 sorting-1    section.
*>===================
*>
     sort     sort-file
              on ascending key  s-b-nos
                                s-b-item
              on descending key s-type
              on ascending key  s-date
                                s-invoice
              input procedure input-to-sort
              giving open-item-file-s.
*>
 main-exit.   exit section.
*>********    ****
*>
 input-to-sort  section.
*>=====================
*>
     perform  OTM5-Open-Input. *> open input  open-item-file-5.
     if       fs-reply not = zero
              perform  OTM5-Close  *>  close open-item-file-5
              open output open-item-file-s  *> create empty file
              close open-item-file-s
              go to main-exit.
*>
 process-input.
*>************
*>
     perform  OTM5-Read-Next.  *> read open-item-file-5 next record at end
     if       fs-reply = 10
              go to  end-of-input.
*>
     if       oi-type = 1 or 3
              go to process-input.
     if       zero = oi-b-nos and oi-b-item
              go to process-input.
*>
     release  sort-record from  open-item-record-5.
     go       to  process-input.
*>
 end-of-input.
*>***********
*>
     perform  OTM5-Close.  *> close    open-item-file-5.
*>
 main-exit.   exit section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
