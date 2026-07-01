       >>source free
*>*************************************************
*>                                                *
*>    Purchase Order Data  Entry & Maintenance    *
*>                                                *
*>*************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         pl020.
*>**
*>    Author.             V B Coen, FBCS, FIDM, FIDPM  for Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Purchase Order Data Entry & Maintenance.
*>                        Uses level 1 Folio Data entry only so no SC linkage.
*>                        References to invoice = Folio, Credit Note = Debit Note.
*>
*>                        Although the program (& pl030) accepts receipt processing
*>                        it is NOT a usage type for PL so should not be used.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas015  ->       (analysis)
*>                         analMT.
*>                        acas022           (Purchase Ledger/Payables)
*>                         purchMT
*>                        acas023  ->       (DelInvNos)
*>                         delfolioMT.
*>                        acas026  ->       (Purchase Order Folios[invoices])
*>                         PinvoiceMT.
*>                        acas029  ->       (OTM5) Open Item File
*>                         otm5MT.
*>
*>                        Pl025. New supplier Create
*>**
*>    Error messages used.
*>                        PL003
*>                        PL006
*>                        PL180
*>                        PL181
*>                        PL182
*>                        PL183
*>                        PL184
*>                        PL185
*>                        PL190
*>                        PL191
*>                        PL192
*>****
*>  Changes.
*> 18/05/84 Vbc - Support Of Graphics.
*> 08/08/84 Vbc - In Inv-Details Set To 1 If Next-Folio = Zero
*> 08/08/84 Vbc - Open Files After Calling Pl025.
*> 07/01/85 Vbc - Fix Bug In Cr-Notes (Clear Screen).
*> 22/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 04/04/09 vbc - Support for F1 (or NEW) on supplier no. to create new
*>                account.  Added support for deleted folio no. and
*>                deleting record after re-use, matches SL910.
*> 12/12/11 vbc - .07 Error msgs to SLnnn.Support for dates other than UK
*>                    Support for path+filenames.
*>                    Updated version to 3.01.nn
*> 18/04/13 vbc - .08 Clear F1 display after supplier found. Matches sl010.
*> 30/04/15 vbc - .09 Changed file access for delinvoices (and for Sales sl910)
*>                    to ISAM - other modules need changing?
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 31/10/16 vbc - .10 Support for RDB on  Analysis tables
*>                    instead of Just cobol files
*>                    using acas015. Update version to v3.02
*> 29/04/17 vbc - .11 Replaced use of maps99.
*> 06/05/17           Now uses Proc-ACAS-FH-Calls.cob for all FH & DAL calls
*>                    Added in support for remaining FH & DALs.
*> 07/11/17 vbc - .12 Changed all ref for il (n) table to sil (n) n = 1 to 40.
*> 01/01/18 vbc - .13 Redoing fd/ws group records etc as screwed up last time.
*>                    Same for all of the other programs that use Invoice and
*>                    OTM files/WS group areas etc.
*> 29/03/18 vbc - .14 Change msg 180 from file to rec.
*>                    On CR notes changed check from invoice to OTM5 rec as
*>                    should not be issuing CR for unposted invoices - same
*>                    as SL and for the same reason. Just as well no one seems
*>                    to use this option but wrong anyway and if inv not found
*>                    Just offer re-input of inv.
*>                    Changed CR-Notes to use OTM5 file (& chk it exists) and
*>                    if inv not found Just offer re-input of inv.
*>                    Also added tests for on hold or closed & renamed err msgs
*> 09/12/22 vbc - .15 Added para to start of sections 4 GC 3.2 warning.
*> 10/03/24 vbc - .16 When writing out invoices/folios if status = dup key read
*>                    system rec & get next-folio, use it and add 1 then
*>                    rewrite rec.
*>                    Above will also happen if using a Del Inv. no as it still
*>                    has to get done. Yes this progran reads and rewrite system
*>                    rec.  Also as done in SL 910.  NEEDS TESTING.
*> 12/04/24 vbc - .17 Remove rem'd out old file access verbs and chg case for 1
*>                    char vars.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 23/04/24 vbc   .18 set I = 1 if zero for get-inv-1 as runtime test shows it as 0.
*>                    why has this never shown up before in normal running ?
*>                    Copied over from sl910 - JIC.
*> 05/01/25 vbc   .19 Add in missing read, rewrite system param rec after
*>                    updating Next-Folio.
*> 19/08/25 vbc   .20 See notes ^ for 04/04/09 Remove dup add 1 to next-folio.
*> 22/08/25 vbc - .21 Support for Vat-Code-X for S(tandard), R(educed), Z(ero)
*>                    In place of 1, 2, 3. To Match Sales ledger SL910,920
*>                    On error messages change 'Invoice' to 'Folio'.
*> 25/08/25 vbc   .22 On running totals missing line #.
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
*>------------
*>
 data                    division.
*>===============================
*>
 file section.
*>------------
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "PL020 (3.3.00)".
 77  Exception-Msg       pic x(25) value spaces.
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 01  WS-amount-screen-display6.
     03  WS-poundsd6     pic 9(6).
     03  WS-period6      pic x     value ".".
     03  WS-penced6      pic v99.
 01  WS-amount-screen-accept6 redefines WS-amount-screen-display6.
     03  WS-pound6       pic 9(6).
     03  filler          pic x.
     03  WS-pence6       pic v99.
*>
 01  WS-amount-work6.
     03  amt-wk-pds6     pic 9(6).
     03  amt-wk-pence6   pic v99.
 01  WS-amount-ok6 redefines WS-amount-work6.
     03  amt-ok6         pic 9(6)v99.
*>
 01  WS-amount-screen-display7.
     03  WS-poundsd7     pic 9(7).
     03  WS-period7      pic x     value ".".
     03  WS-penced7      pic v99.
 01  WS-amount-screen-accept7 redefines WS-amount-screen-display7.
     03  WS-pound7       pic 9(7).
     03  filler          pic x.
     03  WS-pence7       pic v99.
*>
 01  WS-amount-work7.
     03  amt-wk-pds7     pic 9(7).
     03  amt-wk-pence7   pic v99.
 01  WS-amount-ok7 redefines WS-amount-work7.
     03  amt-ok7         pic 9(7)v99.
*>
 01  WS-discount-display.
     03  WS-disca1       pic 99.
     03  WS-disca2       pic x        value ".".
     03  WS-disca3       pic v99.
 01  WS-discount-accept redefines WS-discount-display.
     03  WS-discb1       pic 99.
     03  filler          pic x.
     03  WS-discb3       pic v99.
 01  WS-discount-work.
     03  WS-disc-wka     pic 99.
     03  WS-disc-wkb     pic v99.
 01  WS-discount redefines WS-discount-work pic 99v99.
*>
*>  FD replacements in WS.
*>
 copy "wsanal.cob".     *>  replacing Analysis-Record by WS-Analysis-Record
                        *>           Pa-Code by WS-Pa-Code
 copy "wspl.cob".
 copy "plwsoi5C.cob".   *> WS-OTM5-Record.
 copy "wsfdpinv.cob".   *> replacing Invoice-Record by WS-PInvoice-Record.
 copy "wspdnos.cob".    *> replacing delinvnos-record by ws-del-inv-nos-record
                        *>           del-inv-nos by ws-del-inv-nos
*>
*> Now for WS - invoice table
*>
  copy "plwspinv.cob".     *> WS record data for head & 40 lines with il- & ih-
*>
*> REMARK OUT, ANY IN USE
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
     03  WS-Stock-Record        pic x.  *> If level 2 used
     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
*>     03  WS-Analysis-Record     pic x.
*>     03  WS-Del-Inv-Nos-Record  pic x.
*>     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
*>     03  WS-PInvoice-Record     pic x.
*>     03  WS-OTM5-Record         pic x.
*>
 01  WS-data.
     03  test-product.
         05  filler      pic x.
             88  il-comment              value "/".
         05  filler      pic x(11).
     03  menu-reply      pic 9.
     03  WS-reply        pic x.
     03  c-check         pic 9.
         88  c-exists                    value 1.
     03  WS-delinv       pic 9           value zero.
         88  del-exists                  value 1.
     03  address-line.
         05  add-line1   pic x(15).
         05  add-line2   pic x(21).
     03  WS-named        pic x           value " ".
     03  WS-dash         pic x(80)       value all "-".
     03  work-1          pic 9(7)v99.
     03  work-n          pic 9(7)v99.
     03  work-d          pic 9(7)v99.
     03  display-8       pic z(5)9.99.
     03  display-9       pic z(6)9.99.
     03  Vat-Code-X.                           *> this for S, R, Z = Std,Reduced,Zero
         05  Vat-Code    pic 9.                *> 21/08/25
     03  I               pic 99.
     03  J               pic 99.
     03  K               pic 99.
     03  M               pic 99.
     03  Z               pic 99.
     03  escape-code     pic x.
     03  new-screen      pic 9(8).
     03  altypes         pic x(45)       value "Receipt <<<    Account <<<    Credit Note <<<".
     03  filler redefines altypes.
         05  d-types     pic x(15) occurs 3.
     03  WS-vat-rate     pic 99v99.
     03  WS-pa           pic xx.
     03  WS-product      pic x(12).
     03  WS-description  pic x(24).
     03  WS-qty          pic 9(5).
     03  WS-net          pic 9(7)v99.
     03  WS-vat          pic 9(7)v99.
     03  WS-unit         pic 9(6)v99.
     03  WS-Cr           pic 9(8).
     03  WS-dayes        pic 99.
     03  WS-Using-Del-Inv-No pic x       value space.
*>
     03  WS-env-lines    pic 999       value zero.
     03  WS-lines        binary-char unsigned value zero.
     03  WS-22-lines     binary-char unsigned value zero.  *> not yet in use - L2 proc
     03  WS-23-lines     binary-char unsigned value zero.
     03  WS-accept-body  binary-char unsigned value 8.         *> set for 24 line screen (-1)  not yet in use - L2 proc
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
*>
 01  WS-Test-Date            pic x(10).
 01  WS-Date-formats.
     03  WS-swap             pic xx.
     03  WS-Conv-Date        pic x(10).
     03  WS-Date             pic x(10).
     03  WS-UK redefines WS-Date.
         05  WS-days         pic xx.
         05  filler          pic x.
         05  WS-month        pic xx.
         05  filler          pic x.
         05  WS-year         pic x(4).
     03  WS-USA redefines WS-Date.
         05  WS-usa-month    pic xx.
         05  filler          pic x.
         05  WS-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  WS-Intl redefines WS-Date.
         05  WS-intl-year    pic x(4).
         05  filler          pic x.
         05  WS-intl-month   pic xx.
         05  filler          pic x.
         05  WS-intl-days    pic xx.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
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
     03  PL180          pic x(32) value "PL180 Err on Folio Rec. write : ".
     03  PL181          pic x(44) value "PL181 Folio To Credit Does Not Exist On ITM5".
     03  PL182          pic x(29) value "PL182 Folio To Credit Is Paid".
     03  PL183          pic x(40) value "PL183 Folio To Credit Has Query Flag Set".
     03  PL184          pic x(62) value "PL184 You Can Only Credit Invoices. Not Receipts, Credit Notes".
     03  PL185          pic x(56) value "PL185 Credit of Prompt Pay/Late Charge will be Automatic".
     03  PL190          pic x(62) value "PL190 You can only credit a Folio with the same account number".
     03  PL191          pic x(30) value "PL191 P.A. File Does Not Exist".
     03  PL192          pic x(30) value "PL192 P.A. Code Does Not Exist".
     03  PL193          pic x(22) value "PL193 No such Supplier".
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
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 init01 section.
     accept   WS-env-lines   from lines.
     if       WS-env-lines < 24
              move  24 to WS-env-lines WS-lines
     else
              move  WS-env-lines   to WS-lines
     end-if
     subtract 1 from WS-lines giving WS-23-lines.
     subtract 2 from WS-lines giving WS-22-lines.         *> next 2 from sl910 - not yet used
     subtract 15 from WS-22-Lines giving WS-Accept-Body.	*> gives no. of Invoice Item lines
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     perform  zz070-Convert-Date.   *> WS-Date now local disp date
     move     1 to File-Key-No.
*>
     perform  program-start.
*>
 main.
     initialize Pinvoice-header.
     perform  invoice-details
*>
     if       Z not = zero
       or     escape-code = "Q"
              go to  Main-Exit.
*>
     move     16  to  lin.
     move     1 to cole.
     display  space at curs with erase eos.
*>
 data-input.
     initialize Pinvoice-Bodies.
     move     zero to ih-deduct-days ih-deduct-amt ih-discount
                      ih-p-c ih-net ih-vat.
*>
     move     zero to  I.
 *>    If       I-level-1
 *>             perform  Inv-Level-1
 *>    else
 *>             perform  Inv-Level-2.   *> THIS IS NOT INCLUDED HERE
     perform  inv-level-1.
     if       cob-crt-status = cob-scr-esc
              go to main.
*>
     if       I not = 1
              perform End-Totals.
*>
 more-data.
     display "Enter Further PO's? (Y/N) [Y] " at line WS-lines col 29 with foreground-color 2.
     move     zero to cob-crt-status.
     move     "Y"  to   WS-reply.
     accept   WS-reply at line WS-lines col 56 with foreground-color 6 update UPPER.
     display  space at line WS-lines col 01 with erase eol.
*>
     if       WS-reply = "Y"
              go to main.
     if       WS-reply not = "N"
              go to more-data.
*>
 Main-Exit.
     go to    menu-exit  of  program-start.
*>
*>****************************************************************
*>                P R O C E D U R E S                            *
*>****************************************************************
*>
 running-totals          section.
*>==============================
*>
     display  I at 1223 with foreground-color 3.
     move     zero  to  ih-net
                        ih-vat.
*>
     perform  varying K from 1 by 1 until K > i
              add il-net (K) to ih-net
              add il-vat (K) to ih-vat
     end-perform
*>
     move     ih-net  to  display-9.
     display  display-9 at 1237 with foreground-color 3.
*>
     move     ih-vat  to  display-9.
     display  display-9 at 1255 with foreground-color 3.
*>
     add      ih-net  ih-vat  giving  display-9.
*>
     display  display-9 at 1268 with foreground-color 3.
     go       to Main-Exit.
*>
 Main-Exit.   exit section.
*>
 write-details           section.
*>==============================
*>
     add      1  to  J.
*>
     move     ih-invoice  to  il-invoice (J).
     move     J  to  il-line (J).
     move     ih-type to il-type (J).
     move     invoice-line (J)  to  WS-PInvoice-Record.
     perform  PInvoice-Write.
*>
     if       fs-reply not = zero
              perform Eval-Status
              display pl180         at 2001 with erase eol foreground-color 4
              display fs-reply      at 2036 with foreground-color 3
              display exception-msg at 2039 with foreground-color 3
              display invoice-key   at 2064 with foreground-color 3
              display pl006         at 2101 with foreground-color 3
              accept  WS-reply at 2130
              display space at 2001 with erase eol
              display space at 2101 with erase eol.
*>
 Main-Exit.   exit section.
*>
 Eval-Status        section.
*>=========================
*>
     move     spaces to exception-msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by exception-msg.
*>
 Main-Exit.   exit section.
*>************************
*>
 comm-routines section.
*>********************
*>
 accept-money6c.
     move     amt-wk-pence6 to WS-pence6.
     move     amt-wk-pds6 to WS-pound6.
     display  WS-amount-screen-display6 at curs with foreground-color 3.
     accept   WS-amount-screen-accept6 at curs  with foreground-color 3 update.
     move     WS-pound6 to amt-wk-pds6.
     move     WS-pence6 to amt-wk-pence6.
*>
 accept-money7a.
     move     zero to WS-poundsd7 WS-penced7 amt-ok7.
*>
 accept-money7b.
     display  WS-amount-screen-display7 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept7 at curs   with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 accept-money7c.
     move     amt-wk-pence7 to WS-pence7.
     move     amt-wk-pds7 to WS-pound7.
     display  WS-amount-screen-display7 at curs  with foreground-color 3.
     accept   WS-amount-screen-accept7 at curs   with foreground-color 3 update.
     move     WS-pound7 to amt-wk-pds7.
     move     WS-pence7 to amt-wk-pence7.
*>
 comm-exit.   exit section.
*>--------    ----
*>
 inv-level-1  section.
*>===================
*>
     display  WS-dash        at 1101 with foreground-color 2.
     display  "Level 1"      at 1201 with foreground-color 2.
     display  "Line - "      at 1216 with foreground-color 2.        *> 23 for # - 2 digit ?
     display  "[          ]" at 1236 with foreground-color 2.
     display  "[          ]" at 1254 with foreground-color 2.
     display  "[          ]" at 1267 with foreground-color 2.
     display  "Code"         at 1405 with foreground-color 2.
     display  "<---Net----> Vat   Vat Amount  Gross Amount" at 1436 with foreground-color 2.
*>
 loop.
     perform  varying lin from 16 by 1 until lin not < WS-23-lines
              add      1  to  i
              move     1 to cole
              display  "(" at curs with erase eol foreground-color 2
              move     2 to cole
              display  I at curs with foreground-color 2
              move     4 to cole
              display  ") [  ]" at curs with foreground-color 2
              move     36 to cole
              display  "[          ] [ ]   {         } (" at curs with foreground-color 2
              move     78 to cole
              display  ")" at curs with foreground-color 2
     end-perform
*>
*> I = no. lines on screen for items, then less 7 (24 line screen)
*>      why this way ,  no idea as against move 1 to I ?????
*>
     subtract 16 from WS-23-lines giving M.  *> or move 1 to i
     subtract M  from  I.                    *>
     move     1 to J.
     if       I = zero
              move  1 to I.
     display  I at 1223 with foreground-color 3.
     move     zero to cob-crt-status.
     perform  Get-Data-1.
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
*>
     if       new-screen = 1
              go to loop.
*>
     if       il-description (I) not = spaces
        and   I not = 40
              go to  loop.
*>
 Main-Exit.   exit section.
*>
 Get-Data-1   section.
*>===================
*>
 Get-Data-1-Main.
     add      J  15  giving  lin.
*>
     if       lin  >  WS-23-lines
              subtract 1 from i
              move 1 to new-screen
              go to  Main-Exit.
*>
     move     zero to new-screen.
*>
 get-code.
     if       I > 1
         and  il-pa (I) = spaces
              move il-pa (I - 1) to il-pa (I).
*>
     move     il-pa (I) to WS-pa.
     move     7 to cole.
     display  WS-pa at curs with foreground-color 3.
     accept   WS-pa at curs with foreground-color 3 update.
     if       WS-pa = spaces
              go to  Main-Exit.
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
     move     WS-pa to il-pa (I) pa-group.
     move     spaces to il-description (I).
*>
     if       WS-pa = "<<"
         and  I = 1
              go to get-code.
*>
     if       WS-pa = "<<"
              subtract  1  from  lin
              if    lin  >  15
                    subtract  1  from  I
                    subtract 1 from J
                    go to  get-code
              else
                    subtract  8  from  I
                    go to  Get-Data-1-Main.
     move     "P" to pa-system.
     move     11 to cole.
*>     read     analysis-file  record  invalid key
     move     1 to File-Key-No.
     perform  Analysis-Read-Indexed.
     if       FS-Reply = 21 or = 23
              display PL192 at line WS-23-Lines col 1 with foreground-color 4 BEEP
              go to  get-code.
     display  " " at line WS-23-Lines col 1 with erase eol.
*>
     display  pa-desc at curs with foreground-color 3.
     move     pa-desc to il-description (I).
*>
 get-net.
     move     37 to cole.
     perform  accept-money7a thru accept-money7b.
     if       amt-ok7 = zero
              go to get-code.
     move     amt-ok7 to il-net (I) WS-net.
*>
 Get-Vat-Code.
*>
*>  Only using 1st three as last 2 are for local sales tax (not in UK)
*>   NOTE that Is Is not currently programmed for (e.g., last 2).
*>
     move     "S" to Vat-Code-X.
     move     50 to cole.
     display  Vat-Code-X at curs with foreground-color 3.
     accept   Vat-Code-X at curs with foreground-color 3 update UPPER.
*>
*>   Accept S, R and Z replacing with 1, 2 & 3.      Rating   %   - Effective (supposed )
*>
     If       Vat-Code-X = "S"                   *> Standard code 1 (20% - 21/08/25)
              move 1 to Vat-Code
      else
       If     Vat-Code-X = "R"                   *> Reduced  code 2 (05% - 21/08/25)
              move 2 to Vat-Code
        else
         If   Vat-Code-X = "Z"                   *> Zero     code 3 (00% - 21/08/25)
              move 3 to Vat-Code.
*>
     If       Vat-Code < 1 or > 5                *> using 1st three as last 2 are Sales tax, Not used In the UK but USA ?. 11/09/24
              go to  Get-Vat-Code.
*>
     move     Vat-Code  to  il-Vat-Code (I).
*>
     If       Vat-Code = zero
              move  zero  to  Amt-OK6
     else
              move VAT-Rate (Vat-Code) to WS-VAT-Rate
              compute  Amt-OK6 rounded = (WS-Net * WS-VAT-Rate) / 100.
*>
     move     WS-VAT to  Display-9 il-VAT (I).
*>
 get-vat-rate.
     move     56 to cole.
     perform  accept-money6c.
     move     Amt-OK6 to Il-Vat (I) WS-Vat.
*>
     add      WS-Vat WS-Net giving  Display-9.
     move     68 to cole.
     display  Display-9 at curs with foreground-color 3.
*>
     perform  Running-Totals.
*>
     add      1 to J.
     add      1  to  I.
     go       to Get-Data-1-Main.
*>
 Main-Exit.   exit section.
*>
 erase-screen section.
*>===================
*>
     move     1 to cole.
     display  space at curs with erase eos.
*>
 Main-Exit.   exit section.
*>
 End-Totals   section.
*>===================
*>
 End-Totals-Main.
     move     zero to cob-crt-status.
     perform  Total-Screen.
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
*>
     move     15  to  lin.
     perform  erase-screen.
*>
     display  "*********************" at 1660  with foreground-color 2.
     display  "*" at 1760 with foreground-color 2.
     display  "*" at 1780 with foreground-color 2.
     display  "*" at 1860 with foreground-color 2.
     display  "*" at 1880 with foreground-color 2.
     display  "*" at 1960 with foreground-color 2.
     display  "*" at 1980 with foreground-color 2.
     display  "*********************" at 2060    with foreground-color 2.
*>
     display  "Order ok to store" at 1761      with foreground-color 2.
     display  "(Y/N) ? [Y]" at 1968 with foreground-color 2.
*>
 confirmation.
     move     "Y"  to   WS-reply.
     accept   WS-reply at 1977 with foreground-color 6 update UPPER.
*>
     if       cob-crt-status = cob-scr-esc
              go to Main-Exit.
*>
     if       WS-reply = "N"
              go to  End-Totals-Main.
*>
     if       WS-reply not = "Y"
              go to  confirmation.
*>
     move     "P"  to  ih-status.
     subtract 1  from  I.
     move     I    to  ih-lines.
*>
     move     Pinvoice-header  to  WS-PInvoice-Record.
*>
 Retry-Write-PInv-Rec.
     perform  PInvoice-Write.
     if       FS-Reply = 22       *> Key exists get next folio & same param rec
              perform  zz100-Read-System-Record
              move     Next-Folio to Ih-Invoice  *> was updated
                                     invoice-nos  *> details recs updated
              add      1 to Next-Folio
              perform  zz110-Write-System-Record
              go to    Retry-Write-PInv-Rec
     end-if
     if       fs-reply not = zero                  *> for the pinvoice write but not key exists
              perform Eval-Status
              display pl180         at line WS-23-lines col  1 with erase eol foreground-color 4
              display fs-reply      at line WS-23-lines col 36 with foreground-color 3
              display exception-msg at line WS-23-lines col 39 with foreground-color 3
              display invoice-key   at line WS-23-lines col 64 with foreground-color 3
              display pl006         at line WS-lines    col  1 with foreground-color 3
              accept  WS-reply      at line WS-lines    col 30
              display "  "          at line WS-23-lines col  1 with erase eos
     end-if
*>
     move     zero to  J.
     perform  write-details  I  times.
*>
     if       del-exists
              perform  DelInvNos-Delete.  *> No care if reply not = 0
*>
     move     11  to  lin.
     move     1 to p-flag-i.
     perform  erase-screen.
*>
 Main-Exit.   exit section.
*>
 Total-Screen section.
*>===================
*>
 Total-Screen-Main.
     move     1 to cole.
     move     11 to lin.
     display  space at curs with erase eos.
     display  WS-dash at 1101        with foreground-color 2.
     display  "Level 1" at 1201      with foreground-color 2.
     display  "<---Net---->   <---Vat--->" at 1225  with foreground-color 2.
     display  "<---Gross-->     Days" at 1254       with foreground-color 2.
     display  "Sub-Totals" at 1404   with foreground-color 2.
     display  "{          }   {         }" at 1425  with foreground-color 2.
     display  "{          }     [  ]" at 1454       with foreground-color 2.
*>
     display  "Prompt Payment Disc" at 1704         with foreground-color 2.
     display  "[          ]" at 1725 with foreground-color 2.
     display  "{          }     [  ]" at 1754       with foreground-color 2.
*>
     display  "Shipping & Handling" at 1904         with foreground-color 2.
     display  "[          ]   [         ]" at 1925  with foreground-color 2.
     display  "{          }" at 1954 with foreground-color 2.
*>
     display  "------------   -----------" at 2225  with foreground-color 2.
     display  "------------" at 2254 with foreground-color 2.
*>
     display  "Itemised Totals" at 2304 with foreground-color 2.
     display  "{          }   {         }" at 2325  with foreground-color 2.
     display  "{          }" at 2354  with foreground-color 2.
*>
     move     ih-net  to  display-9.
     display  display-9 at 1426 with foreground-color 3.
*>
     move     ih-vat  to  display-8.
     display  display-8 at 1441 with foreground-color 3.
*>
     add      ih-net  ih-vat  giving  display-9.
     display  display-9 at 1455 with foreground-color 3.
*>
 get-days.
     move     zero to ih-days ih-carriage.
     if       ih-type = 2
              move purch-credit to ih-days.
     move     ih-days to WS-dayes.
     display  WS-dayes at 1472 with foreground-color 3.
     if       ih-type not = 2
              go to get-carriage.
*>
     accept   WS-dayes at 1472 with foreground-color 3 update.
     move     WS-dayes to ih-days.
*>
 get-extra.
     move     zero to ih-extra ih-e-vat ih-deduct-amt
                      ih-deduct-vat ih-deduct-days.
     move     1726 to curs.
     move     ih-deduct-amt to amt-ok7.
     perform  accept-money7c.
     if       amt-ok7 not < 1000
              go to get-extra.
     move     amt-ok7 to ih-deduct-amt display-9.
*>
     if       ih-deduct-amt equal  zero
              go to get-carriage.
*>
     display  display-9 at 1755 with foreground-color 3.
     display  WS-dayes at 1772 with foreground-color 3.
     accept   WS-dayes at 1772 with foreground-color 3 update.
     move     WS-dayes to ih-deduct-days.
*>
 get-carriage.
     move     1926 to curs.
     perform  accept-money7a thru accept-money7b.
     move     amt-ok7 to ih-carriage.
     compute  amt-ok6 rounded  = ih-carriage * vat-rate-1 / 100.
*>
*> Note that vat-rate-1 must be standard rate for p & p
*>
 get-carriage-vat.
     move     1941 to curs.
     perform  accept-money6c.
     move     amt-ok6 to ih-c-vat.
     add      ih-carriage  ih-c-vat  giving  display-9.
     display  display-9 at 1955 with foreground-color 3.
*>
     add      ih-net ih-carriage giving  display-9.
     display  display-9 at 2326 with foreground-color 3.
*>
     add      ih-vat ih-c-vat giving  display-8.
     display  display-8 at 2341 with foreground-color 3.
*>
     add      ih-net ih-carriage ih-vat ih-c-vat giving display-9.
     display  display-9 at 2355 with foreground-color 3.
     display  "ok  [ ]" at 2374 with foreground-color 2.
     accept   WS-reply at 2379 with foreground-color 3 UPPER.
     if       WS-reply not = "Y"
              go to Total-Screen-Main.
*>
 Main-Exit.   exit section.
*>
 invoice-details section.
*>=======================
*>
 Invoice-Details-Main.
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "Order Data Entry" at 0133               with foreground-color 2.
     perform  zz070-Convert-Date.
     display  WS-Date at 0171 with foreground-color 2.
*>
     display  "****************************************" at 0441 with foreground-color 2.
     display  "*Date [  /  /    ]*A/C Nos    [       ]*" at 0541 with foreground-color 2.
     display  "**                *Order   [          ]*" at 0641 with foreground-color 2. *> ORd = 69
     display  "*Folio  {        }*Ref/Inv [          ]*" at 0741 with foreground-color 2. *> inv = Ref =  69
     display  "****************************************" at 0841 with foreground-color 2.
     display  "F1 = Setup new Supplier" at 0911                  with foreground-color 2.
     display   "Type [ ]  <1> = Receipt; <2> = Account; <3> = Credit Note"
                                                         at 1001 with foreground-color 2.
*>
 Date-Input.
     display  WS-Date at 0548 with foreground-color 3.
     accept   WS-Date at 0548 with foreground-color 3 update.
*>
     if       cob-crt-status = cob-scr-esc
        or    WS-Date = spaces
              move 1 to z
              go to  Main-Exit.
*>
     move     WS-Date to WS-Test-Date.
     perform  zz050-Validate-Date.
     if       U-Bin = zero
              go to  Date-Input.
*>
     move     U-Bin  to  ih-date.
     move     WS-Date to WS-Test-Date.  *> still need orig. disp date as WS-Date now UK
*>
 Supplier-Input.
     move     zero to cob-crt-status.
     move     spaces to ih-supplier.
     accept   ih-supplier at 0572 with foreground-color 3 UPPER.
*>
 Supplier-Test.
     if       Ih-Supplier = "NEW"
         or   Cob-Crt-Status = Cob-Scr-F1
              go to new-supplier.
*>
     if       ih-supplier = spaces
              move  "Q"  to  escape-code
              go to  Main-Exit.
*>
     move     1  to  c-check.
     move     ih-supplier  to  WS-Purch-Key.
*>
     move     1 to File-Key-No.
     perform  Purch-Read-Indexed.
     if       FS-Reply not = zero
              move  zero  to  c-check.
*>
     if       not  c-exists
              display  PL193 line WS-23-lines col 1 with foreground-color 4
                                                         erase eol BEEP
              go to  Supplier-Input.
*>
     display  "                       " at 0911.    *> Clear F1 display
     display  space at line WS-23-lines col 1 with erase eol.
     move     zeros to Ih-Invoice.
     if       del-exists
              perform Get-a-Deleted-Invoice.
     if       Ih-Invoice = zeros
              perform zz100-Read-System-Record
              if      Next-Folio = zero
                      move 1 to Next-Folio
              end-if
              move Next-Folio  to  Ih-invoice
              add  1 to Next-Folio          *> Remove same code else where <<<<<<<<<<<<<<<<<<<<<<<
              perform zz110-Write-System-Record.
*>
     display  ih-invoice at 0750 with foreground-color 3.  *> Is folio-no
*>
     display  purch-name at 0301 with foreground-color 3.
*>
     move     1  to  z.
     unstring purch-address  delimited  by  pl-delim   into  address-line  count Z  pointer  z.
     display  address-line at 0401 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring purch-address  delimited  by  pl-delim   into  address-line  count Z  pointer  z.
     display  address-line at 0501 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring purch-address  delimited  by  pl-delim   into  address-line  count Z  pointer  z.
     display  address-line at 0601 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring purch-address  delimited  by  pl-delim   into  address-line  count Z  pointer  z.
     display  address-line at 0701 with foreground-color 3.
*>
     move     spaces  to  address-line.
     unstring purch-address   into  address-line  pointer  z.
     display  address-line at 0801 with foreground-color 3.
*>
     move     spaces  to  address-line.
*>
     move     spaces to ih-ref ih-order.
     accept   ih-order at 0669 with foreground-color 3.
*>
     accept   ih-ref at 0769 with foreground-color 3.  *> In invoice field
*>
 type-input.
     move     zero to ih-type.
     accept   ih-type at 1007 with foreground-color 3.
     move     space to WS-named.
     if       ih-type = zero
              go to invoice-details-Main.
*>
     if       ih-type  >  3 or = zero
              go to  type-input.
     display  space at 1001 with erase eol.
     display  ">>> " at 1031 with foreground-color 2.
     move     d-types (ih-type) to add-line1.
     display  add-line1 at 1035 with foreground-color 2.
     move     zero to ih-cr.
     if       ih-type = 3
              perform  CR-Note
              if    escape-code = "Q"
                    go to  invoice-details-Main.
*>
     move     zero to z.
     go       to Main-Exit.
*>
 new-supplier.
     perform  Purch-Close.
     perform  PInvoice-Close.
     perform  Analysis-Close.
     call     "pl025" using WS-calling-data system-record to-day file-defs.
     perform  program-start.
     go       to invoice-details-Main.
*>
 Main-Exit.   exit section.
*>
 Get-a-Deleted-Invoice section.
*>============================
*>
     if       not del-exists
              go to l70ad-terminate.
 l70ab-read.
*>---------
*>
*> 30/4/15 new code for ISAM instead of seq
*>
     move     zeros to WS-Del-Inv-Nos.
     move     zeros to ih-invoice.  *> so we can test for it
     move     1 to File-Key-No.
     set      fn-not-less-than to true.
     perform  DelInvNos-Start.
*>     start    Del-Inv-Nos-File key not < WS-Del-Inv-Nos invalid key
     if       FS-Reply not = zero
              go to l70ad-terminate.
*>
 l70ab-read-2.
     perform  DelInvNos-Read-Next.
     if       fs-reply = 10
              move     "N" to WS-Using-Del-Inv-No
              go to l70ac-close.
     if       WS-Del-Inv-Nos = zero
              go to l70ab-read-2.
     move     WS-Del-Inv-Nos to ih-invoice.  *> del rec will be deleted after o/p of PO.
     display  "Using Deleted Folio Numbers" at 0345 with foreground-color 2 blink.
     move     "Y" to WS-Using-Del-Inv-No.
     go       to l70ae-exit.
*>
 l70ac-close.
*>
*> If open as output clear down file and if RDB *MT deletes all records with
*>  key below 99999999 so same thing
*>
     perform  DelInvNos-Close.
     perform  DelInvNos-Open-Output.
     display  "                             " at 0345.
*>
 l70ad-terminate.
*>
 *>    move     next-invoice to ih-invoice.
     move     zero to ws-delinv.
*>
 l70ae-exit.
     exit     section.
*>
 CR-Note      section.
*>===================
*>
*>  CRs are only processed against posted invoices, hence using OTM5.
*>
 main.
     display  space at 1201 with erase eol.
     display  space at 1301 with erase eol.
     display  space at 1401 with erase eol.
     display  space at 1501 with erase eol.
     display  space at 1601 with erase eol.
*>
 main-input.
     display  "Folio # to Credit - [        ]" at 1201  with foreground-color 2.
*>
     move     zero  to  WS-Cr.
*>
     accept   WS-Cr at 1222 with foreground-color 3 update.
     if       cob-crt-status = cob-scr-esc
              move "Q" to escape-code
              go to Main-Exit.
     move     WS-Cr to ih-cr.
     if       ih-cr = zero
              move  "Z"  to  WS-named
              go to  no-inv-restart
     else
              move  space  to  WS-named.
*>
     if       ih-cr = 99999999
              move "Q" to escape-code
              go to Main-Exit
     else
              move space to escape-code.
*>
     move     ih-supplier to oi5-supplier.
     move     ih-cr       to oi5-invoice.
*>
     move     1 to File-Key-No.
     perform  OTM5-Read-Indexed.
     if       fs-reply not = zero
              display PL181 at line WS-23-lines col 01 with foreground-color 4 BEEP
              go to  Main.     *> was check-inv-no-ok.
*>
     display  space at line WS-23-lines col 01 with erase eol.
     if       invoice-type not = 2
              display PL184 at line WS-23-lines col 01 with foreground-color 4 BEEP
              go to main-input.
*>
     if       s-closed                  *> Error invoice is Paid
              display PL182  at line WS-23-lines col 01 with foreground-color 2 highlight BEEP
              go to main-input
     else
              display space at line WS-23-lines col 01 with erase eol.
*>
     if       oi-hold-flag = "Q"        *> Warning Invoice has query flag set but we can continue
              display PL183  at line WS-23-lines col 01  with foreground-color 2 highlight.
*>
     if       invoice-supplier not = WS-Purch-Key    *> cant happen
              display PL190 at line WS-23-lines col 01 with foreground-color 4
              go to main-input.
*>
 No-Inv-Restart.
     perform  main.       *> Clear screen lines 12 - 16
*>
 Main-Exit.
     exit     section.
*>
 Program-Start section.
*>====================
*>
     display  space at 0101 with erase eos.
     move     to-day to U-Date.          *> in UK date form
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-15        *> Analysis
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    move 1 to WS-Process-Func WS-Sub-Function
                    call "pl070" using WS-calling-data
                                       system-record
                                       to-day
                                       file-defs
                    call  "CBL_CHECK_FILE_EXIST" using File-15   *> Only if the call failed
                                                       File-Info
                    if    return-code not = zero          *> not = zero - No file found
                          display   PL191 at 2301
                          display   PL003 at 2401
                          accept WS-Reply at 2430
                    end-if
              end-if
     end-if
*>
     perform  Purch-Open.
     perform  Analysis-Open.
*>
*> Create Invoice (PO) file if not exist.
*>
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-26      *> Invoice
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    perform  PInvoice-Open-Output
                    perform  PInvoice-Close
              end-if
     end-if
*>
     move     zero  to  menu-reply.
     perform  PInvoice-Open.
     perform  DelInvNos-Open.
     move     1 to WS-delinv.        *> above forces file creation.
     go       to Main-Exit.
*>
 menu-exit.
     move     zero to  pass-value.
     perform  Purch-Close.
     perform  PInvoice-Close.
     perform  Analysis-Close.
*>
     goback.
*>
 Main-Exit.   exit section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-Test-Date
*> output:  U-Date/WS-Date as uk date format
*>          U-Bin not zero if valid date
*>
     move     WS-Test-Date to WS-Date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-test-date.
     if       Date-USA                *> swap month and days
              move WS-days  to WS-swap
              move WS-month to WS-days
              move WS-swap  to WS-month
              go to zz050-test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to WS-Date.  *> swap Intl to UK form
     move     WS-Test-Date (1:4) to WS-Year.
     move     WS-Test-Date (6:2) to WS-Month.
     move     WS-Test-Date (9:2) to WS-Days.
*>
 zz050-test-date.
     move     WS-Date to U-Date.
     move     zero    to U-Bin.
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
*> Input:   U-Bin
*> output:  WS-Date as uk/US/Inlt date format
*>          U-Date & WS-Date = spaces if invalid date
*>
     perform  maps04.
     if       U-Date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     U-Date to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move WS-days  to WS-swap
              move WS-month to WS-days
              move WS-swap  to WS-month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     U-Date (7:4) to WS-Intl-Year.
     move     U-Date (4:2) to WS-Intl-Month.
     move     U-Date (1:2) to WS-Intl-Days.
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
*> output:  WS-Date as uk/US/Inlt date format
*>
     move     to-day to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> swap month and days
              move WS-days  to WS-swap
              move WS-month to WS-days
              move WS-swap  to WS-month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     to-day (7:4) to WS-Intl-Year.
     move     to-day (4:2) to WS-Intl-Month.
     move     to-day (1:2) to WS-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
*> Used when next-invoice and saving it when creating invoice recs.
*>
 zz100-Read-System-Record  section.
*>********************************
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.  *> Only use param FILE
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.
*>
     move     1 to File-Key-No.
     perform  System-Read-Indexed.
     perform  System-Close.
*>
 zz100-Exit.
     exit     section.
*>
 zz110-Write-System-Record  section.
*>*********************************
*>
     if       File-System-Used NOT = zero   *> Force RDB processing
              move     "66" to FA-RDBMS-Flat-Statuses
              move     1 to File-Key-No
              perform  System-Open
              move     1 to File-Key-No
              perform  System-Rewrite
              perform  System-Close
     end-if.
*>
*> Now do the same for the Cobol file.
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open.                       *> Open cobol file params as I/O
     move     1 to File-Key-No.
     perform  System-Rewrite.                    *> Update Cobol file params
     perform  System-Close.                      *> Close the Cobol param file.
*>
 zz110-Exit.
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
