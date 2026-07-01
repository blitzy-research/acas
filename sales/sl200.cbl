       >>source free
*>****************************************************************
*>                                                               *
*>       I N V O I C E   D E L E T I O N   R E P O R T           *
*>                 But only if any exist.                        *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.         sl200.
*>**
*>    Author.             V.B.Coen  FBCS, FIDM, FIDPM,
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Deletion Report.
*>**
*>    Called Modules.     Maps04.
*>                        acas017  ->
*>                         sldelinvnosMT
*>**
*>    Error messages used.
*>                        NONE
*>**
*> Changes:
*>  unknown vbc - Program added at customer requests
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 19/03/09 vbc - .01 Added 'None to report' when needed.
*> 25/11/11 vbc - .02 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .03 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .04 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 24/10/16 vbc - .05 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 21/01/17 vbc - .06 Files converting to use FH - Completed.
*> 25/01/17 vbc       Dry testing completed.
*> 19/03/18 vbc - .07 Removed dup 'none to report' msg on printer.
*> 09/06/23 vbc - .08 In End-Program - the test should be 'NOT = zero' as it
*>                    signals end of file (10) etc and didnot produce msg
*>                    'None to Report'.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/12/24 vbc - .09 Add 2nd head line and move titles to align up.
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
*>================================
*>
 copy "envdiv.cob".
 input-output            section.
*>-------------------------------
*>
 file-control.
*>------------
*>
 copy "selprint.cob".
*> copy "seldnos.cob".
 data                    division.
*>================================
*>
 file section.
*>------------
*>
 copy "fdprint.cob" replacing ==x(132)== by ==x(80)==.
*>
 01 line-1.
     03  filler        pic xxx.
     03  pinv-nos      pic z(9)9.
     03  filler        pic x(5).
     03  pinv-date     pic x(10).
     03  filler        pic x(3).
     03  pinv-cus      pic x(7).
*>
 01  Head-Line.
     03  P1-Version    pic x(15).
     03  filler        pic x(14).
     03  P1-Title      pic x(23).
     03  filler        pic x(21).
     03  P1-Tit-Page   pic x(5).
     03  P1-Page       pic z9.
*>
 01  Head-Line-2.
     03  P2-Comp-Name  pic x(32).
     03  filler        pic x(38).
     03  P2-Date       pic x(10).
*>
*> copy "fddnos.cob".
*>
 working-storage section.
*>-----------------------
 77  prog-name           pic x(15)    value "SL200 (3.3.00)".
 copy "print-spool-command-p.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
 copy "wsdnos.cob".
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
*>     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  ws-data.
     03  ws-reply        pic x.
     03  line-cnt        pic 99  comp value zero.
     03  page-cnt        pic 99  comp value zero.
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
*> 01  Error-Messages.
*> System Wide
*>     NONE
*> Module specific
*>     NONE
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
 start-program.
*>*************
*>
     open     output print-file.
     move     spaces to print-record.
     perform  headings-1.
     perform  DelInvNos-Open-Input.       *> open     input del-inv-nos-file.
     if       fs-reply not = zero
              go to end-program.
*>
 main-read.
*>*********
*>
     perform  DelInvNos-Read-Next.         *>  read del-inv-nos-file at end
     if       fs-reply = 10
              go to end-program.
     move     del-inv-dat to u-bin.
     perform  zz060-Convert-Date.
     move     ws-date to pinv-date.
*>
     move     WS-del-inv-nos to pinv-nos.
     move     del-inv-cus    to pinv-cus.
*>
     write    print-record after 1.
     add      1 to line-cnt.
     if       line-cnt > 70
              perform Headings-1.
     go       to main-read.
*>
 Headings-1.
*>
     move     spaces to Head-Line.
     add      1 to Page-Cnt.
     move     Page-Cnt to P1-Page.
     move     "Page" to P1-Tit-Page.
     perform  zz070-Convert-Date.
     move     "Invoice Deletion Report" to P1-Title.
     move     Prog-Name to P1-Version.
     move     4 to Line-Cnt.
     if       Page-Cnt not = 1
              write Print-Record after page
     else
              write Print-Record after 1.
     move     spaces to Head-Line-2.
     move     Usera to P2-Comp-Name.
     move     WS-Date to P2-Date.
     write    Print-Record after 1.
     move     "   Invoice No        Date      Cust No" to print-record.
     write    Print-Record after 2.
     move     spaces to Print-Record.
     write    Print-Record after 1.
*>
 End-Program.
*>***********
*>
     if       fs-reply not = zero
       and    page-cnt = 1 and line-cnt = 4
              move "       None to Report" to print-record
              write print-record after 1.
     close    print-file.                *> del-inv-nos-file
     perform  DelInvNos-Close.
     move     Print-Spool-Name to PSN.
     call     "SYSTEM" using Print-Report.
*>
 main-term.
     exit program.
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
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     u-date (7:4) to ws-Intl-Year.
     move     u-date (4:2) to ws-Intl-Month.
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
