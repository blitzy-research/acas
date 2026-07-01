       >>source free
*>*****************************************************
*>                                                    *
*>         Purchase  Ledger Alpha - List Sort         *
*>                                                    *
*>     Some compilers do not have secondary keys      *
*>*****************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         pl165.
*>**
*>    Author.             S.J.Whine  Aidpm
*>                        Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 17/04/84
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.	           Purchase Ledger Supplier Alpha Sort.
*>**
*>    Version.            See prog-name in ws.
*>**
*>    Called Modules.
*>                        acas022  ->
*>                         purchMT
*>**
*>    Error messages used.
*>                        NONE
*>**
*>    Changes:
*> 22/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 04/04/09 vbc - Changed to always sort no questions, etc.
*> 15/12/11 vbc - .01 Support for path+filenames.
*>                    Updated version to 3.01.nn
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 09/12/22 vbc - .02 Added para to start of sections 4 GC 3.2 warning.
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
*>
 file-control.
*>-----------
*>
     select  sort-file       assign        file-21,
                             status        ss-reply.
*>
     select  sales-sort      assign        fn-sales,
                             access        sequential,
                             status        fs-reply.
*>
*> copy "selpl.cob".
*>
 i-o-control.
*>----------
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 sd  sort-file.
*>
 01  sort-record.
     03  sort-key        pic x(7).
     03  sort-name       pic x(30).

 fd  sales-sort.
*>
 01  sales-sort-record.
     03  sales-sort-key  pic x(7).
*>
*> copy "fdpl.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "PL165 (3.3.00)".
*>
 copy "wsfnctn.cob".
 copy "wspl.cob".
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
*>     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  fn-sales        pic x(12)       value "suppsort.inx".
*>
 01  ws-data.
     03  ss-reply        pic xx.
     03  ws-reply        pic x.
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
     if       not FS-Cobol-Files-Used    *> well use fn-Read-By-Name (31)
              goback returning 4
     end-if.
*>
     perform  Purch-Open-Input.        *>  open     input  purchase-file.
     open     output sales-sort.
*>
     sort     sort-file
               on  ascending key  sort-name
*>  sort-key     *> DONT THINK THIS IS NEEDED
               input procedure input-to-sort
               output procedure output-from-sort.
*>
     close    sales-sort.         *>  purchase-file
     perform  Purch-Close.
*>
 end-program.
     exit     program.
*>
 input-to-sort section.
 Input-To-Sort-Main.
     perform  Purch-Read-Next.        *> read purchase-file next record at end
     if       fs-reply = 10
              go to  its-exit.
*>
     move     WS-purch-key   to  sort-key.
     move     purch-name  to  sort-name.
     release  sort-record.
     go       to input-to-sort-Main.
*>
 its-exit.
     exit     section.
*>
 output-from-sort section.
 Output-From-Sort-Main.
     return   sort-file at end
              go to ofs-exit.
     move     sort-key to sales-sort-key.
     write    sales-sort-record.
     go       to output-from-sort-Main.
*>
 ofs-exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
