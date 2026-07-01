       >>source free
*>****************************************************
*>                                                   *
*>         L E D G E R    E N Q U I R Y              *
*>                                                   *
*>****************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         pl015.
*>**
*>    author.             V B Coen FBCS, FIDM, FIDPM
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Purchase Ledger Enquiry.
*>
*>**
*>    Version.            See Prog-Name In Ws.
*>
*>    Called Modules.     Maps04  (was 03).
*>                        acas022  ->
*>                         purchMT.
*>                        acas026  ->
*>                         pinvoiceMT.
*>                        acas029  ->
*>                         otm5MT.
*>**
*>    Tables Used:
*>                        Purchase
*>                        PInvoice
*>                        OTM5.
*>    Files used:
*>                        TEMP Work file.
*>                        Printer
*>**
*>    Error messages used.
*>                        PL111
*>                        PL112
*>                        PL113
*>                        PL114
*>                        PL115
*>                        PL116
*>                        PL117
*>                        PL118
*>                        PL119
*>                        PL120.
*>**
*>    Changes.
*> 19/06/84 Vbc - Support For 39 Entries On Screen,Ditto Prt,Make
*>                Code More Compact.
*> 14/07/84 Vbc - Test P-Flag-I In Setup-Work-File Routine.
*> 21/03/09 vbc - Migration to Open Cobol v3.00.00 & print spooling 4 Linux
*> 15/09/10 vbc - .06 change for print spool command
*> 12/12/11 vbc - .07 Error msgs to SLnnn.Support for dates other than UK
*>                    Support for path+filenames.
*>                    Updated version to 3.01.nn
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks.
*> 15/01/17 vbc - .08 All programs upgraded to v3.02 for RDB processing.
*>                    Remove references to File-Status - depleted.
*>                    Updated FD/WS and replaced cobol verbs
*>                    for access to FH/DALs.
*>                    Updated to use Invoice-Read-Next-Header as thats all
*>                    this program reads.
*> 06/11/17 vbc - .09 BUG - Was using ITM3 instead of ITM5 - der.
*> 29/12/17 vbc - .10 Redoing fd/ws group records etc as screwed up last time.
*>                    Same for all of the other programs that use Invoice and
*>                    OTM files/WS group areas etc.
*> 09/12/22 vbc - .11 Added para to start of section es-accept 4 GC 3.2 warning.
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
*>
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
 *> copy "selpinv.cob".
 *> copy "selpl.cob".
 *> copy "seloi5.cob".
*>
 copy "selprint.cob".
     select work-file  assign       file-21
                       access       dynamic
                       organization indexed
                       status       fs-reply
                       record key   work-key.
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdpinv2.cob".
*> copy "fdpl.cob".
*> copy "fdoi5.cob".
 fd  work-file.
*>
 01  work-record.
     03  work-key.
         05  work-supplier  pic x(7).
         05  work-invoice   binary-long.
     03  work-amount        pic s9(8)v99  comp-3.
*>
 fd  print-file.
*>
 01  print-record            pic x(80).
*>
 working-storage section.
*>-----------------------
 77  prog-name           pic x(15) value "PL015 (3.3.00)".
*>
*>
*> Ex fd block.
 copy "wsfdpinv2.cob".   *> ex fd def.
 copy "plwspl.cob".      *> ex fd def.
 copy "plwsoi5B.cob".     *> ex fd def
*>  WS.
 copy "print-spool-command-p.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
 copy "plwsoi.cob".
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
     03  WS-OTM3-Record         pic x.
*>     03  WS-PInvoice-Record     pic x.
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
 01  ws-data.
     03  a               binary-char     value zero.
     03  b               binary-char     value zero.
     03  c               binary-char     value zero.
     03  l               binary-char     value zero.
     03  Screen-Size     binary-long     value zero.
     03  Screen-Start    binary-long     value zero.
     03  Screen-End      binary-long     value zero.
     03  ws-inv.
         05  ws-inv8     pic z(7)9.
     03  work-1          binary-long     value zero.
     03  amount-out      pic s9(8)v99  comp-3 value zero.
     03  inv-amount      pic s9(8)v99  comp-3 value zero.
     03  customer-in     pic x(7)        value space.
     03  work-file-data  pic x           value "N".
     03  ws-tinv         pic 9(8)        value zero.
     03  address-line    pic x(36).
     03  ws-desc         pic x(20)       value spaces.
*>
     03  ws-env-lines    pic 999         value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-21-lines     binary-char unsigned value zero.
     03  ws-20-lines     binary-char unsigned value zero.
     03  Body-lines      binary-char unsigned value zero.
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
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
*>       NONE
*> Module specific
     03  PL111          pic x(53) value "PL111 Error On Writing Work File. Hit Return To Abort".
     03  PL112          pic x(21) value "PL112 Can't open file".
     03  PL113          pic x(19) value "PL113 Can't find it".
     03  PL114          pic x(22) value "PL114 Record not found".
     03  PL115          pic x(22) value "PL115 Error On Rewrite".
     03  PL116          pic x(38) value "PL116 Note: and hit return to continue".
     03  PL117          pic x(35) value "PL117 No Work File Created..No Data".
     03  PL118          pic x(23) value "PL118 Work file Created".
     03  PL119          pic x(22) value "PL119 Only on invoices".
     03  PL120          pic x(38) value "PL120 Purchase Transactions Not Posted".
*>
 01  error-code          pic 999.
*>
 01  balances        comp-3.
     03  bal-0           pic s9(8)v99 value zero.
     03  bal-30          pic s9(8)v99 value zero.
     03  bal-60          pic s9(8)v99 value zero.
     03  bal-90          pic s9(8)v99 value zero.
     03  bal-t           pic s9(8)v99 value zero.
*>
 01  line-0.
     03  l0-version      pic x(16).
     03  filler          pic x(13)    value spaces.
     03  l0-title        pic x(23)  value "Purchase Ledger Enquiry".
     03  filler          pic x(18)  value spaces.
     03  l0-date         pic x(10).
*>
 01  line-1.
     03  line-1a.
         05  l1-lit      pic x(10)  value "Supplier:".
         05  l1-name     pic x(30).
     03  line-1b.
         05  filler      pic x(40)  value all "*".
*>
 01  line-2.
     03  line-2a.
         05  l2-lit      pic x(10)   value "Address :".
         05  l2-address  pic x(30).
     03  line-2b.
         05  filler      pic x(10)   value "* A/C No [".
         05  l2-account  pic x(7).
         05  filler      pic x       value "]".
         05  filler      pic x(10)   value "*Balance [".
         05  l2-balance  pic z(6)9.99.
         05  filler      pic xx      value "]*".
*>
 01  line-3.
     03  line-3a.
         05  filler       pic x(10)  value spaces.
         05  l3-address   pic x(30).
     03  line-3b.
         05  filler       pic x(10)  value "* Ytd    [".
         05  l3-ytd       pic z(6)9.
         05  filler       pic x(12)  value "]*Unapplied[".
         05  l3-unapplied pic z(5)9.99.
         05  filler       pic xx     value "]*".
*>
 01  line-4.
     03  line-4a.
          05  filler          pic x(10)       value spaces.
          05  l4-address      pic x(30).
     03  line-4b.
          05  filler          pic x(10)  value "* Credit [".
          05  l4-credit-limit pic z(6)9.
          05  filler          pic x(11)  value "]*Unposted[".
          05  l4-unposted     pic z(6)9.99.
          05  filler          pic xx     value "]*".
*>
 01  line-5.
     03  line-5a.
         05  filler      pic x(10)       value spaces.
         05  l5-address  pic x(30).
     03  line-5b.
         05  filler      pic x(40)       value all "*".
*>
 01  line-6.
     03  filler          pic x           value space.
     03  l6-lit1         pic x(06)       value "Number".
     03  filler          pic x(07)       value spaces.
     03  l6-lit2         pic x(04)       value "Date".
     03  filler          pic x(07)       value spaces.
     03  l6-lit3         pic x(11)       value "Description".
     03  filler          pic x(10)       value spaces.
     03  l6-lit4         pic x(08)       value "Invoiced".
     03  filler          pic x(08)       value spaces.
     03  l6-lit5         pic x(04)       value "Paid".
     03  filler          pic x(05)       value spaces.
     03  l6-lit6         pic x(07)       value "Balance".
*>
 01  line-7-19.
     03  l7-group  occurs 100.
         05  l7-invoice  pic z(7)9       blank when zero.
         05  l7-prompt   pic x.
         05  l7-hold     pic x.
         05  filler      pic x.
         05  l7-date     pic x(11).
         05  l7-desc     pic x(22).
         05  l7-amount   pic zzzzz,zz9.99.
         05  l7-paid     pic zzzzz,zz9.99.
         05  l7-balance  pic zzzzz,zz9.99.
*>
 01  line-20.
     03  l20-t1          pic x(17)   value "Total Outstanding".
     03  filler          pic x(10)   value spaces.
     03  l20-t2          pic x(7)    value "Current".
     03  filler          pic x(11)   value spaces.
     03  l20-t3          pic x(2)    value "30".
     03  filler          pic x(13)   value spaces.
     03  l20-t4          pic x(2)    value "60".
     03  filler          pic x(12)   value spaces.
     03  l20-t5          pic xxx     value "90+".
*>
 01  line-21.
     03  filler          pic x(5)        value spaces.
     03  l21-os          pic zz,zzz,zz9.99.
     03  l21-current     pic z(6),zzz,zz9.99.
     03  l21-bal30       pic zzzz,zzz,zz9.99.
     03  l21-bal60       pic zzzz,zzz,zz9.99.
     03  l21-bal90       pic zzzz,zzz,zz9.99.
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
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines   to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-23-lines.
     subtract 2 from ws-lines giving ws-22-lines.
     subtract 3 from ws-lines giving ws-21-lines.
     subtract 4 from ws-lines giving ws-20-lines.
     subtract 11 from ws-lines giving Body-Lines.
     move     to-day to ws-date.
     perform  zz070-Convert-Date.
     move     ws-date to l0-date.
     move     prog-name to l0-version.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
     move     1  to File-Key-No.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-29    *> Open ITM5 file
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    display PL120  at 2301
                    display PL116  at 2401
                    accept  Accept-Reply at 2440
                    go to menu-exit.
*>
*> First creates a list of active inv & cr. notes with total amt by cust & inv nos
*>
     perform  set-up-work-file.
     open     input work-file.
     perform  Purch-Open-Input.     *> open     input purchase-file open-item-file-5.
     perform  OTM5-Open-Input.
     perform  enquiry.
     close    work-file.         *>close    purchase-file open-item-file-5.
     perform  Purch-Close.
     perform  OTM5-Close.
     open     output work-file.                    *> clear down workfile, is this safe here?
     close    work-file.
*>
 menu-exit.
     exit     program.
*>
 maps04.
*>******
*>
     call     "maps04"  using  maps03-ws.
*>
*>****************************************************************
*>                     p r o c e d u r e s                       *
*>****************************************************************
*>
 enquiry                 section.
*>==============================
*>
 enquiry-Main.
 main001.
*>
     display  " " at 0101 with erase eos.
     display  prog-name at 0101 with foreground-color 2.
     display  "Purchase Ledger Enquiry" at 0129  with foreground-color 2.
     move     to-day to ws-date.
     perform  zz070-Convert-Date.
     display  ws-date at 0171    with foreground-color 2.
*>
 after-disp-heads.
*>
     display  "****************************************" at 0241 with foreground-color 2.
     display  "*A/C Nos [       ]*Balance [          ]*" at 0341 with foreground-color 2.
     display  "*Ytd    [        ]*Unapplied[         ]*" at 0441 with foreground-color 2.
     display  "*Credit [        ]*Unposted[          ]*" at 0541 with foreground-color 2.
     display  "****************************************" at 0641 with foreground-color 2.
*>
 main-display-end.
     move     spaces to customer-in.
     accept   customer-in at 0351 with foreground-color 3.
     if       customer-in = spaces
              go to main-exit.
     if       cob-crt-status = cob-scr-esc
              go to main-exit.
*>
     move     function upper-case (customer-in) to customer-in.
     display  customer-in at 0351 with foreground-color 3.
*>
     move     customer-in to WS-Purch-Key
                             OI-Supplier      oi5-supplier
                             l2-account
                             work-supplier.
     move     zero        to OI-Invoice       oi5-invoice
                             work-invoice
                             inv-amount.
     set      fn-not-less-than to true.
     perform  Purch-Start.       *> start purchase-file key not < WS-Purch-Key.
     set      fn-not-less-than to true.
     perform  OTM5-Start.        *> start open-item-file-5 key not < oi5-key.
     if       fs-reply not = zero          *> not = zero - No file found
              display PL120  at 2301
              display PL116  at 2401
              accept  Accept-Reply at 2440
              go to menu-exit.
*>
     if       work-file-data = "N"
              go to read-sales.
*>
     start    work-file  key not < work-key.
*>
 read-sales.
*>
     perform  Purch-Read-Next.         *> read purchase-file next record at end
     if       fs-reply = 10
              go to  main-display-end.
*>
     if       WS-Purch-Key not = customer-in
              go to main-display-end.
*>
     move     spaces to line-7-19.
     move     purch-name  to  l1-name.
*>
     move     1  to  a.
     move     spaces  to  address-line.
     unstring purch-address  delimited by  pl-delim into  address-line  count a  pointer  a.
     move     address-line  to  l2-address.
*>
     move     spaces  to  address-line.
     unstring purch-address  delimited by  pl-delim into  address-line  count a  pointer  a.
     move     address-line  to  l3-address.
*>
     move     spaces  to  address-line.
     unstring purch-address  delimited by  pl-delim into  address-line  count a  pointer  a.
     move     address-line  to  l4-address.
*>
     move     spaces to address-line.
     unstring purch-address  delimited by  pl-delim into  address-line  count a  pointer  a.
     move     address-line  to  l5-address.
*>
     display  line-1a at 0201 with foreground-color 2.
     display  line-2a at 0301 with foreground-color 2.
     display  line-3a at 0401 with foreground-color 2.
     display  line-4a at 0501 with foreground-color 2.
     display  line-5a at 0601 with foreground-color 2.
*>
     move     purch-current to l2-balance.
     move     purch-unapplied to l3-unapplied.
     add      pturnover-q (1) pturnover-q (2)
              pturnover-q (3) pturnover-q (4) giving l3-ytd.
     move     purch-limit to l4-credit-limit.
     move     zero        to l4-unposted   a.
*>
     perform  get-unposted.
*>
     display  l2-balance      at 0369 with foreground-color 3.
     display  l3-ytd          at 0451 with foreground-color 3.
     if       purch-unapplied not = zero
              display l3-unapplied at 0470 with foreground-color 3.
     display  l4-credit-limit at 0551 with foreground-color 3.
     if       inv-amount not = zero
              display l4-unposted at 0569 with foreground-color 3.
*>
*> PL020 has line6 displaying separate lits
*>
     display  line-6 at 0701 with foreground-color 2.
     move     zero to a b c.
*>
     multiply Body-Lines by 80 giving Screen-Size.
     move     1 to Screen-Start.
     move     Screen-Size to Screen-End.
*>
 read-open-item.
*>
     perform  OTM5-Read-Next.         *> read open-item-file-5 next record at end
     if       fs-reply not = zero
              go to end-statement.
*>
     if       OI-Supplier not =  WS-Purch-Key   *> oi5-Supplier
              go to  end-statement.
     move     open-item-record-5  to  oi-header.
*>
     add      1 to a.
     if       a > 100   *> was 39
              move ">> Screen Overflow <<" to l7-desc (100) *> was 39
              move 100 to a    *> was 40
              go to item-comp-1.
*>
     if       oi-type = 5 or 6
              move  zero  to  oi-invoice.
*>
     move     oi-invoice  to  l7-invoice (a).
*>
     move     oi-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     ws-date   to  l7-date (a).
*>
     if       oi-hold-flag not = space
              move "H" to l7-hold (a).
*>
     move     spaces  to  ws-desc.
     if       oi-type = 1
              move "Receipt " to ws-desc
     else
       if     oi-type = 2
              string  "Goods - "  delimited  by size  oi-ref delimited by "  " into ws-desc
       else
        if    oi-type = 3
              move oi-cr to ws-inv8
              string  "CN.Re Inv -" delimited by size ws-inv delimited by size into ws-desc
        else
         if   oi-type = 5
              move  "Payment"  to  ws-desc
         else
          if  oi-type = 6
              move "Journal Payment" to ws-desc.
     move     ws-desc to l7-desc (a).
*>
 item-comp-1.
*>
     add      oi-net oi-carriage oi-vat oi-c-vat giving  inv-amount.
     if       oi-type = 2
         and  oi-deduct-amt not = zero
              move "P" to l7-prompt (a)
              add oi-date oi-deduct-days giving work-1
              if   work-1 not < run-date
                   subtract oi-deduct-amt from inv-amount.
*>
     if       oi-type = 3
              multiply -1 by oi-paid.
     if       oi-type = 2 or 3
              subtract oi-paid from inv-amount giving  amount-out.
*>
     if       a > 3100  *> was 39
         and  (oi-type = 2 or 3)
              go to calc-age.
*>
     if       a > 100   *> was 39
              go to bypass-ageing.
*>
     if       oi-type = 2 or 3
              move amount-out to l7-balance (a).
     move     inv-amount to l7-amount (a).
     move     oi-paid to l7-paid (a).
*>
     if       oi-type = 1
              move inv-amount to l7-amount (a)  l7-paid (a)
              move zero to l7-balance (a)
              go to bypass-ageing.
*>
     if       oi-type = 5  or  6
              move zeros to l7-balance (a) l7-amount (a)
              go to bypass-ageing.
*>
 calc-age.
*>
     subtract oi-date  from  run-date  giving  work-1.
*>
*> now work out ageing
*>  (dont worry if paid in full - routine still works ok)
*>
     if       work-1  <  30
              add  amount-out  to  bal-0
     else
      if      work-1  <  60
              add  amount-out  to  bal-30
      else
       if     work-1  <  90
              add  amount-out  to  bal-60
       else
              add  amount-out  to  bal-90.
*>
     add      amount-out  to  bal-t.
*>
 bypass-ageing.
     go       to read-open-item.
*>
 end-statement.
*>************
*>
     display  line-7-19 (Screen-Start:Screen-End) at 0801 with foreground-color 2
     add Body-Lines to b.
     if     a > b
            add Screen-Size to Screen-Start
            add Screen-Size to Screen-End
            if b > 100
               subtract 100 from b   *>  = lines to display
               move 8000 to Screen-End
               subtract b from Body-Lines giving c
               add 1 to c
               add c 7 giving l
               display " " at line l col 1 with erase eos
            end-if
     end-if.
 disp-totals.
     display  line-20 at line ws-21-lines col 1 with foreground-color 2.
*>
     move     bal-0   to  l21-current.
     move     bal-30  to  l21-bal30.
     move     bal-60  to  l21-bal60.
     move     bal-90  to  l21-bal90.
     move     bal-t   to  l21-os.
     display  line-21 at line ws-22-lines col 1 with foreground-color 2.
*>
 es-disp.
*>
     display  "Select: 'P'rint, 'N'ext enquiry, 'T'oggle query flag, "
                                            at line ws-lines col 01 with foreground-color 2.
     if       a > b
              display "'M'ore or 'E'nd [ ]" at line ws-lines col 55 with foreground-color 2
     else
              display "or 'E'nd [ ]"        at line ws-lines col 55 with foreground-color 2.
*>
 es-accept.
*>
     move     space to s1.
     move     65 to cole.
     if       a > b
              add 7 to cole.
     accept   s1 at line ws-lines col cole  with foreground-color 6 update auto.
     move     function upper-case (s1) to s1.
     if       cob-crt-status = cob-scr-esc
              go to main-exit.
     if       s1 = "E"
              go to main-exit.
     if       s1 = "M"
              go to end-statement.
     if       s1 = "P"
              perform print-screen
              go to es-disp.
     if       s1 = "N"
              move zero to bal-0 bal-30 bal-60 bal-90 bal-t
              go to enquiry-Main.
     if       s1 = "T"
              perform set-query-flag
              go to es-disp.
     go       to es-accept.
*>
 main-exit.   exit section.
*>********    ****
*>
 print-screen            section.
*>==============================
*>
     open     output print-file.
*>
     write    print-record from line-0 after 1.  *> ex page
*>
Heads1.
     write    print-record from line-1 after 1.
     write    print-record from line-2 after 1.
     write    print-record from line-3 after 1.
     write    print-record from line-4 after 1.
     write    print-record from line-5 after 1.
     write    print-record from line-6 after 1.
*>
 Heads2.
     perform  varying l from 1 by 1 until l > a
              move l7-group (l) to print-record
              write print-record after 1
              if  l = 59
                  write print-record from line-0 after page
                  perform Heads1
     end-perform
     write    print-record from line-20 after 2.
     write    print-record from line-21 after 2.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 main-exit.   exit section.
*>
 set-up-work-file  section.
*>========================
*>
*>  Create work file with unapplied invoices/cr. notes etc so we can
*>    show them with current invoice/payments per supplier
*>
     perform  main001.
     move     14 to lin.
     move     zero to cole.
     move     zero to a.
     if       p-flag-i not = 1
              go to eof-test.
     open     output work-file.
     perform  PInvoice-Open-Input.       *> open  input  invoice-file.
*>
     if       fs-reply not = zero
              close work-file            *> invoice-file
              perform PInvoice-Close
              go to main004-exit.
*>
 read-invoice.
*>
     perform  PInvoice-Read-Next-Header.        *> read     invoice-file next record at end
     if       fs-reply = 10
              go to invoice-eof.
*>
     if       ih-test not = zero
              go to read-invoice.
     if       ih-status = "z"
              go to read-invoice.
     if       ih-type = 1 or 4
              go to read-invoice.
*>
     move     ih-invoice  to work-invoice.
     move     ih-supplier to work-supplier.
     add      ih-net ih-carriage ih-vat ih-c-vat
                giving work-amount.
*>
     if       ih-type = 3
              multiply -1 by work-amount.
*>
     write    work-record.
     if       fs-reply not = zero
              display PL111 at line ws-lines col 1 with foreground-color 4
              accept s1 at line ws-lines col 53 with foreground-color 6
              close work-file           *> invoice-file
              perform PInvoice-Close
              go to menu-exit.
*>
     add      1 to a.
     if       a > 9
              move zero to a
              add  1 to cole
              display "." at curs with foreground-color 3.
     if       cole > 79
              add 1 to lin
              move zero to cole.
*>
     go       to read-invoice.
*>
 invoice-eof.
*>
     perform  PInvoice-Close.           *> close    invoice-file work-file.
     close    work-file.
*>
 eof-test.
*>
     if       lin = 14 and cole = zero and a = zero
              display PL117 at 1801 with foreground-color 2
     else
              move "Y" to work-file-data
              display Pl118 at 1801 with foreground-color 2.
*>
 main004-exit.
     exit     section.
*>
 get-unposted  section.
*>====================
*>
     if       work-file-data = "N"
              go to main005-finish.
*>
 read-work.
*>
     read     work-file next record at end
              go to main005-finish.
     if       customer-in not = work-supplier
              go to main005-finish.
     add      work-amount to inv-amount.
     go       to read-work.
*>
 main005-finish.
*>
     move     inv-amount to l4-unposted.
*>
 main005-exit.
     exit     section.
*>
 set-query-flag section.
*>======================
*>
     move     zeros to ws-tinv.
     display  "For Account:        . Give invoice no. to toggle" &
              " [        ]" at line ws-23-lines col 1 with foreground-color 2.
     display  customer-in line ws-23-lines col 14 with foreground-color 3.
*>
 accept006.
*>
     accept   ws-tinv at line ws-23-lines col 51 with foreground-color 3 update.
     if       ws-tinv = zero
              go to main006-exit.
*>
     display  " " at line ws-23-lines col 01 with erase eol.
     perform  OTM5-Close.            *>  close    open-item-file-5.
*>
 open006.
*>
     perform  OTM5-Open.        *>  open     i-o open-item-file-5.
     if       fs-reply not = zero
              display PL112 at line ws-23-lines col 1 with foreground-color 4
              go to error006.
*>
     move     customer-in to oi5-supplier.
     move     ws-tinv to oi5-invoice.
     perform  OTM5-Read-Indexed.       *> read     open-item-file-5 invalid key
     if       fs-reply = 21
              display PL113 at line ws-23-lines col 1 with foreground-color 4
              go to error006.
*>
     if       oi5-invoice not = ws-tinv
       or     oi5-supplier not = customer-in
              display PL114 at line ws-23-lines col 1 with foreground-color 4
              go to error006.
*>
     move     open-item-record-5 to oi-header.
     if       oi-type not = 2
              display PL119 at line ws-23-lines col 1 with foreground-color 2
              go to error006.
     if       oi-hold-flag = space
              move "H" to oi-hold-flag
      else
              move space to oi-hold-flag.
*>
     move     oi-Header to Open-Item-Record-5.
     perform  OTM5-Rewrite.        *> rewrite  open-item-record-5 from oi-header invalid key
     if       fs-reply = 21 or 22
          or  WE-Error - 994
              display PL115 at line ws-23-lines col 1 with foreground-color 4
              go to error006.
*>
     go       to finish006.
*>
 error006.
*>
     display  PL116 at line ws-lines col 1 with foreground-color 2.
     accept   s1 at line ws-lines col 34 with foreground-color 6
     display  " " at line ws-23-lines col 1 with erase eol.
*>
 finish006.
*>
     perform  OTM5-Close.            *> close    open-item-file-5.
     perform  OTM5-Open-Input.       *> open     input open-item-file-5.
*>
 main006-exit.
     exit     section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   ws-test-date
*> output:  u-date/ws-date as uk date format
*>          u-bin not zero if valid date
*>
     move     ws-test-date to ws-date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-test-date.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz050-test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to ws-date.  *> swap Intl to UK form
     move     ws-test-date (1:4) to ws-Year.
     move     ws-test-date (6:2) to ws-Month.
     move     ws-test-date (9:2) to ws-Days.
*>
 zz050-test-date.
     move     ws-date to u-date.
     move     zero to u-bin.
     perform  maps04.
*>
 zz050-exit.
     exit     section.
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
 copy "Proc-ACAS-FH-Calls.cob".
*>
