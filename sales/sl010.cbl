       >>source free
*>************************************************
*>                                               *
*>     Sales  Ledger  Data-Base  Maintenance     *
*>                                               *
*>************************************************
*>
*>  PROGRAM INCLUDES TESTING CODE
*>    REMOVE AFTER / ON Completion.
*>
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         sl010.
*>**
*>    Author.             V B Coen FBCS, FIDM, FIDPM, 18/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Sales Ledger Customer File Maintenance
*>                        & Print.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     maps04.
*>                        maps09.
*>                        acas012
*>                         salesMT
*>                        acas014
*>                         deliveryMT
*>**
*>    Tables Used:
*>                        SALEDGER-REC (Sales)
*>                        DELIVERY-RECORD (Delivery)
*>    Files used:
*>                        Printer
*>**
*>    Error messages used.
*>                        SL002.
*>                        SL004
*>                        SL005
*>
*>                        SL101
*>                        SL102
*>                        SL103
*>                        SL104
*>                        SL105
*>                        SL106
*>                        SL107
*>                        SL108
*>                        SL109
*>                        SL110
*>                        SL111
*>                        SL112
*>**
*>    Changes.
*> 16/02/83 vbc - 240570-680:fixes date err on sales-last etc.
*> 20/03/83 vbc - 320210:fix on sales rec not found error.
*> 22/04/83 vbc - fix display deliv name ,310220.
*> 10/10/83 vbc - chg printer to use line-cnt,also clear display
*>                fault on cust setup.
*> 22/10/83 vbc - Conversion to cis cobol.
*> 30/10/83 vbc - Support new sales-file field create-date.
*> 01/03/84 vbc - Support sales-unapplied in customer-display.
*> 06/03/84 vbc - Support new sales file fields pay-average,active
*> 28/03/84 vbc - Worst: check for non zero on sales-unapplied when
*>                deleting.
*> 28/04/84 vbc - Support phone extention, telex on sales file.
*> 07/05/84 vbc - In setup-cust, clear for cust-no,displ cust if
*>                exists.
*> 12/07/84 vbc - Move escape box 5 chars right, remove display
*>                  headings from menu-input,clear screen on report
*> 28/02/85 vbc - Support for entry date on report matches.
*> 03/03/09 vbc - Migration to open cobol v3.00.00.
*> 16/03/09 vbc - New field - Notes which goes into del file so all fields
*>                move down one line in display-02. fixes bug 30.4
*> 25/03/09 vbc - Display & accept tidyups that was highlited by pl010.
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .14 Mod lpr.
*> 18/11/11 vbc - .15 Support for dates other than UK & clean up msgs
*> 19/11/11 vbc - .16 Error msgs to SLnnn, Cleanup error/bad code in slcreate
*>                    that missed testing!!
*> 08/12/11 vbc - .17 Changed delivery file to use indexed instead of relative,
*>                    easier to delete un-needed records and control size.
*>                    Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .18 Changed usage of Stk-Date-Form to the global field
*>                    Date-Form making former redundent.
*> 27/02/12 vbc - .19 Changed use of check-digit' in 'sales-key to sales-key
*>                    (7:1) for SQL processing.
*> 29/05/13 vbc - .20 Added changeable unapplied & current for test data on
*>                    cust. display with escape 'T'.
*> 24/10/16 vbc - .21 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*>                    Clean up some error/warning msgs getting rid of calls to
*>                    maps99.
*> 23/01/17 vbc       Dry testing completed with fixes.
*> 10/12/22 vbc   .22 Added para after some sections 4 GC 3.2 warning msgs.
*> 27/01/24 vbc - .23 Cosmetic/proc err - call using maps09 using customer-nos
*>                    instead of wsmaps09-ws as the full group item. found by
*>                    -d -g -ftraceall. - works without the runtime checks.
*> 15/03/24 vbc - .24 Added support for field Sales-Partial-Ship-Flag for input
*>                    display and reporting. Chg case for FUNCTION, UPPER-CASE.
*> 20/03/24 vbc - .25 Added Support for SL-BO-Default for create mode and as "N"
*>                    if not yet set to "N" or "Y".
*> 11/04/24 vbc - .26 Added tests for BO file when req for delete by chk for
*>                    same cust key present on BO file so can't delete.
*> 13/04/24 vbc - .27 Add support to change selected or all customers BO flag
*>                    to "Y" or "N".
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 17/04/24 vbc       Inserted a space after/before <<< >>> for SL109.
*> 18/04/24 vbc   .28 Fix bugs in new ga000 code perform should have been go to.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*> 20/10/25 vbc -    .01 In validate-address chg to support 5 delimiters in address.
*>                    WARNING - This may present problems else where. matches pl010.
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
 copy "selboitm.cob".  *> 11/04/24
 copy "selprint.cob".
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 copy "fdboitm.cob".  *> 11/04/24
 copy "fdprint.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL010 (3.3.01)".
 copy "print-spool-command.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
 copy "wsmaps09.cob".
*>
 copy "wssl.cob".
 copy "wsdel.cob".
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
*>     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
*>     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
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
     03  menu-reply      pic 9.
     03  ws-reply        pic x.
     03  a               pic 999.
     03  B               pic 9.
     03  y               pic 99.
     03  z               pic 9.
     03  error-flag      pic 9           value zero.
     03  escape-code     pic x.
     03  save-tag        binary-long.
     03  save-notes-tag  binary-long.
     03  print-out       pic x.
     03  d24-02          pic x           value space.
     03  d24-03          pic x           value space.
     03  d24-check.
         05  filler      pic x(13)       value "Check Digit {".
         05  d24-digit   pic x           value space.
         05  filler      pic x           value "}".
     03  a01-late-charg  pic x           value space.
     03  a01-dun-letter  pic x           value space.
     03  a01-Email-Let   pic x           value space.
     03  a01-Email-Stat  pic x           value space.
     03  a01-Email-Inv   pic x           value space.
     03  A01-Notes.
         05  a01-Notes-1     pic x(48)       value spaces.
         05  a01-Notes-2     pic x(48)       value spaces.
     03  A01-Deliv-Name  pic x(30)       value spaces.
     03  A01-Deliv-Address.
         05  A01-deliv-addr1 pic x(48)       value spaces.
         05  A01-deliv-addr2 pic x(48)       value spaces.
     03  cust-in         pic x(6)        value spaces.
     03  status-in       pic x           value space.
     03  credit-in       pic 99          value zero.
     03  credit-op       pic x           value space.
     03  invoice-in      pic 9(5)        value zero.
     03  invoice-op      pic x           value space.
     03  average-in      pic 9(5)        value zero.
     03  average-op      pic x           value space.
     03  overdue-in      pic 9(5)        value zero.
     03  overdue-op      pic x           value space.
     03  enter-date-in   pic x(10)       value spaces.
     03  enter-date-op   pic x           value space.
     03  ws-Local-Date   pic x(10)       value spaces.
     03  ws-Test-Date    pic x(10).
     03  truth           pic 9           value zero.
         88  a-true   value  1.
         88  a-false  value  0.
     03  customer-nos2   pic x(6)        value spaces.
     03  test-1          binary-long.
     03  test-2          binary-long.
     03  test-op         pic x.
     03  credit-heading.
         05  cr-operand  pic xx.
         05  cr-days     pic z9.
         05  filler      pic x(12)       value  " Days Credit".
     03  active-heading.
         05  act-operand pic xx.
         05  act-days    pic zzzz9.
         05  filler      pic x(9)        value  " Invoices".
     03  average-heading.
         05  av-operand  pic xx.
         05  av-days     pic zzzz9.
         05  filler      pic x(10)       value  " Av. Value".
     03  overdue-heading.
         05  ov-operand  pic xx.
         05  ov-days     pic zzzz9.
         05  filler      pic x(13)       value " Days Overdue".
     03  enter-date-heading.
         05  ed-operand  pic xx.
         05  ed-date     pic x(10).
         05  filler      pic x(11)       value " Entry Date".
     03  ws-enter-date   binary-long     value zero.
     03  address-line    pic x(32).
     03  display-bal     pic -(8)9.99.
     03  test-address    pic x(96).
     03  ws-spaces-30                    value spaces.
         05  ws-spaces-7 pic x(7).
         05  ws-spaces-13 pic x(13).
         05  filler      pic x(10).
     03  ws-eval-msg     pic x(25)       value spaces.
     03  intest          pic x.
     03  line-cnt        pic 99   comp   value zero.
     03  Customer-In     pic x(7).
     03  WS-BO-State     pic x           value "Y".
         88  WS-BO-Valid-State           values "Y" "N".
     03  WS-BO-Status    pic x           value space.
         88  WS-BO-Active                value "Y".
     03  ws-env-lines    pic 999       value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
*>
 01  ws-amount-screen-display9.
     03  ws-poundsd9     pic 9(9).
     03  ws-period9      pic x     value ".".
     03  ws-penced9      pic v99.
 01  ws-amount-screen-accept9 redefines ws-amount-screen-display9.
     03  ws-pound9       pic 9(9).
     03  filler          pic x.
     03  ws-pence9       pic v99.
*>
 01  ws-amount-work9.
     03  amt-wk-pds9     pic 9(9).
     03  amt-wk-pence9   pic v99.
 01  ws-amount-ok9 redefines ws-amount-work9.
     03  amt-ok9         pic 9(9)v99.
*>
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
 01  error-code          pic 999.  *> Used.
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
*>
 01  Error-Messages.
*> System Wide
     03  SL002          pic x(31) value "SL002 Note error and hit return".
     03  SL004          pic x(20) value "SL004 Now Hit return".
     03  SL005          pic x(18) value "SL005 Invalid Date".
*> Module specific
     03  SL101          pic x(14) value "SL101 Addr Err".
     03  SL102          pic x(5)  value "Error".
     03  SL103          pic x(49) value "SL103 Sales Ledger files have not been set up yet".
     03  SL104          pic x(44) value "SL104 Do you wish to create them (Y/N) ? [ ]".
     03  SL105          pic x(37) value "SL105 Creating Sales & Delivery Files".
     03  SL106          pic x(31) value "SL106 Opening Sales file gives ".
     03  SL107          pic x(34) value "SL107 Opening Delivery file gives ".
     03  SL108          pic x(34) value "SL108 Abort Or Recover (A/R) : [ ]".
     03  SL109          pic x(53) value "SL109 <<< Can not Delete currently active account >>>".
     03  SL110          pic x(31) value "SL110 Response Must Be (Y or N)".
     03  SL111          pic x(31) value "SL111 Customer Record Not Found".
     03  SL112          pic x(36) value "SL112 Customer Record Already Exists".
*>
 01  line-1.  *> 132
     03  l1-version      pic x(57)       value spaces.
     03  filler          pic x(67)       value "Customer Listing".
     03  filler          pic x(5)        value "Page ".
     03  l1-page         pic zz9.
*>
 01  line-3.
     03  l3-user         pic x(40).
     03  filler          pic x(12)       value  "Report On : ".
     03  l3-report       pic x(70)       value  spaces.
     03  l3-date         pic x(10).
*>
 01  line-4.
     03  filler          pic x(127)      value
         "Customer  Status    <---------------Name & Address-------------->     ----Telephone" &
         "---- -----Fax----- BO  Late       Credit".
     03  filler          pic x(5)        value " Disc".
*>
 01  line-5.
     03  filler          pic x           value space.
     03  filler          pic x(103)      value "Number   ------".
     03  filler          pic x(28)       value "Chg  Let   Limit/Days    %".
*>
 01  line-6.
     03  l6-key          pic x(10).
     03  l6-status       pic x(10).
     03  l6-name         pic x(50).
     03  l6-phone        pic x(18).
     03  l6-fax          pic x(13).
     03  filler          pic xx          value spaces.
     03  L6-BO           pic xb.
     03  l6-charges      pic xb(4).
     03  l6-letter       pic xbb.
     03  l6-limit        pic z(6)9       blank when zero.
     03  l6-credit       pic zzz9bbb     blank when zero.
     03  l6-discount     pic z9.99       blank when zero.
*>
 01  line-7.
     03  filler          pic x(20)       value spaces.
     03  l7-address      pic x(112).
*>
 linkage section.
*>==============
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  to-day              pic x(10).
*>
 screen section.
*>=============
*>
*>   ALL Adjusted left 5 chars 29/11/11
*>
 01  display-02                  background-color cob-color-black
                                 foreground-color cob-color-green
                                                     blank screen.

     03  value "Customer Nos : ["    line  4 col  1.
*> >>>>>>>> customer no here <<<<<<<
     03  from d24-02          pic x  line  4 col 23.
     03  from d24-03          pic x          col 24.
     03  from d24-check       pic x(15)      col 26.
     03  value "Customer Name: ["    line  6 col  1.
     03  using sales-name  pic x(30) line  6 col 17.
     03  value "]"                   line  6 col 47.
     03  value "Addr: ["             line  7 col 10.
     03  using sales-addr1    pic x(48)      col 17.
     03  value "]"                   line  7 col 65.
     03  value "["                   line  8 col 16.
     03  using sales-addr2    pic x(48)      col 17.
     03  value "]"                   line  8 col 65.
     03  value "Delivery name: ["    line  9 col  1.
     03  using A01-deliv-name     pic x(30)  col 17.
     03  value "]"                           col 47.
     03  value "Addr: ["             line 10 col 10.
     03  using A01-deliv-addr1    pic x(48)  col 17.
     03  value "]"                           col 65.
     03  value "["                   line 11 col 16.
     03  using A01-deliv-addr2    pic x(48)  col 17.
     03  value "]"                           col 65.
     03  value "Customer Note: ["    line 12 col  1.
     03  using a01-Notes-1    pic x(48)      col 17.
     03  value "]"                           col 65.
     03  value "["                   line 13 col 16.
     03  using a01-Notes-2    pic x(48)      col 17.
     03  value "]"                           col 65.
     03  value "Telephone    : ["    line 14 col  1.
     03  using sales-phone    pic x(13)      col 17.
     03  value "]"                           col 30.
     03  value "Ext: ["                      col 32.
     03  using sales-ext      pic x(4)       col 38.
     03  value "]"                           col 42.
     03  value "Fax : ["                     col 45.
     03  using sales-fax      pic x(13)      col 52.
     03  value "]"                           col 65.
     03  value "Email Sales  : ["    line 15 col  1.
     03  using sales-email    pic x(30)      col 17.
     03  value "]"                           col 47.
     03  value "BO Allowed - ["              col 49.  *> added 15/03/24
     03  using Sales-Partial-Ship-Flag
                              pic x          col 63.
     03  value "] (Y or N)"                  col 64.
     03  value "Late charges : ["    line 16 col  1.
     03  using a01-late-charg  pic x         col 17.
     03  value "]"                           col 18.
     03  value "Minimum balance before late charge : ["
                                             col 26.
     03  using sales-late-min pic 9(4)       col 64.
     03  value "]"                           col 68.
     03  value "Late letters : ["    line 17 col  1.
     03  using a01-dun-letter  pic x         col 17.
     03  value "]"                           col 18.
     03  value "Maximum late charge"         col 26.
     03  value ": ["                         col 61.
     03  using sales-late-max pic 9(4)       col 64.
     03  value "]"                           col 68.
     03  value "Credit period: ["    line 18 col  1.
     03  using sales-credit   pic 99         col 17.
     03  value "]"                           col 19.
     03  value "EMail-Inv:["                 col 26.
     03  using a01-Email-Inv  pic x          col 37.
     03  value "]"                           col 38.
     03  value "Stat: ["                     col 40.
     03  using a01-EMail-Stat pic x          col 47.
     03  value "]"                           col 48.
     03  value "Dun : ["                     col 50.
     03  using a01-EMail-Let  pic x          col 57.
     03  value "]"                           col 58.
     03  value "Credit limit : ["    line 19 col  1.
     03  using sales-limit    pic 9(7)       col 17.
     03  value "] Discount : ["              col 24.
     03  using sales-discount pic 99.99      col 38.
     03  value "]"                           col 43.
     03  value "*******************" line 19 col 56.
     03  value "Unapplied Bal: {"    line 20 col  1.
     03  value "}"                           col 29.
     03  value "* Escape Code ["             col 56.
*> value entered by individual display.
     03  value "] *"                         col 72.
     03  value "Current Bal  : {"    line 21 col  1.
*> value entered by individual display
     03  value "}"                           col 29.
     03  value "* <B> = Back      *"         col 56.
     03  value "Last invoice : {"    line 22 col  1.
*> value entered by individual display
     03  value "}"                           col 27.
     03  value "* <S> = Save      *"         col 56.
     03  value "Last payment : {"    line 23 col  1.
*> value entered by individual display
     03  value "}"                           col 27.
     03  value "* <Q> = Quit      *" line 23 col 56.
     03  value "*******************" line 24 col 56.
*>
 01  display-03                  background-color cob-color-black
                                 foreground-color cob-color-green.
     03  from prog-name  pic x(15)                 line  1 col  1
                                                    blank screen.
     03  value "Customer File"                             col 34.
     03  from ws-Local-Date     pic x(10)          line  1 col 71.
     03  value "Report Attributes"                 line  3 col 32.
*>
*> Adjusted left 6 chars 29/11/11
*>
     03  value "Customer Number - ["               line  8 col  3.
     03  using cust-in   pic x(6)                          col 22.
     03  value "]"                                         col 28.
     03  value "Enter characters in positions to match"    col 33.
     03  value "Status          - ["               line 10 col  3.
     03  using status-in pic x                             col 22.
     03  value "]"                                         col 23.
     03  value "<L> Live;<D> Dormant;< > All"              col 33.
     03  value "Credit Period   - ["               line 12 col  3.
     03  using credit-in pic 99                            col 22.
     03  value "]  ["                                      col 24.
     03  using credit-op pic x                             col 28.
     03  value "]"                                 line 12 col 29.
     03  value "Enter number of days & operator"           col 33.
     03  value "<L>  for credit periods < than"    line 13 col 37.
     03  value "<G>  for credit periods > than"    line 14 col 37.
     03  value "<E>  for credit periods = to"      line 15 col 37.
     03  value "Invoice Activity  ["               line 17 col  3.
     03  using invoice-in pic 9(5)                         col 22.
     03  value "] ["                                       col 27.
     03  using invoice-op pic x                            col 30.
     03  value "]"                                         col 31.
     03  value "Enter number of invoices & operator"       col 33.
     03  value "Average Value   - ["               line 19 col  3.
     03  using average-in pic 9(5)                         col 22.
     03  value "] ["                                       col 27.
     03  using average-op pic x                            col 30.
     03  value "]"                                         col 31.
     03  value "Enter invoice value & operator"            col 33.
     03  value "Overdue A/Cs    - ["               line 21 col  3.
     03  using overdue-in pic 9(5)                         col 22.
     03  value "] ["                                       col 27.
     03  using overdue-op pic x                            col 30.
     03  value "]"                                         col 31.
     03  value "Enter number of days & operator"           col 33.
     03  value "Date Entered-["                    line 23 col  3.
     03  using enter-date-in pic x(10)                     col 17.
     03  value "] ["                                       col 27.
     03  using enter-date-op pic x                         col 30.
     03  value "]"                                         col 31.
     03  value "Enter date & operator"                     col 33.
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
 init01 section.
*>
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines   to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-23-lines.
     move     prog-name to l1-version.
     move     to-day to u-date.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
     move     space to Print-Out.
     if       SL-BO-Default not = "Y" and not = "N"
              move     "N" to SL-BO-Default.      *>< JIC not yet set up
     if       SL-BO-Flag = "Y"  *> BO active in param rec
              open i-o BO-Stk-Itm-File
              If       FS-Reply not = zero
                       close BO-Stk-Itm-File
                       move     "N" to WS-BO-Status
              else
                       move     "Y" to WS-BO-Status.
*>
     move     1  to File-Key-No.
*>
     if       not S-L-Exists
              perform slcreate.
*>
 menu-return.
*>**********
*>
     move     zero  to  menu-reply.
     perform  display-heading.
*>
 menu-input.
*>*********
*>
     display  "Select one of the following by number :- [ ]" at 0701 with foreground-color 2.
     display  "(1)  Set-up Customer records"  at 1004  with foreground-color 2.
     display  "(2)  Amend Customer records"   at 1204  with foreground-color 2.
     display  "(3)  Delete Customer records"  at 1404  with foreground-color 2.
     display  "(4)  Print Customer records"   at 1604  with foreground-color 2.
     display  "(5)  Display Customer records" at 1804  with foreground-color 2.
     display  "(6)  Amend Back Order Status"  at 2004  with foreground-color 2.
     display  "(9)  Return to System Menu"    at 2204  with foreground-color 2.
     accept   menu-reply at 0743 with foreground-color 2 auto.
*>
     if       menu-reply = 9
              go to  Menu-Exit.
*>
     if       menu-reply  <  1  or  >  6
              go to  menu-input.
*>
     if       menu-reply = 1
              perform  ba000-Setup-Customers
     else
      if      menu-reply = 2
              perform  ca000-Amend-Customer
      else
       if     menu-reply = 3
              perform  da000-Delete-Customer
       else
        if    menu-reply = 4
              perform  ea000-Report-Customers
        else
         if   menu-reply = 5
              perform  fa000-Display-Customers
         else
          if  Menu-Reply = 6
              perform  ga000-Amend-BO-Status.
*>
     go       to menu-return.
*>
 menu-exit.
*>********
*>
     exit     program.
*>
 maps03.
*>*****
*>
     call     "maps04"  using  maps03-ws.
*>
 maps09.
*>*****
*>
     call     "maps09"  using  maps09-ws. *>  customer-code.
*>
 clear-error-line.
*>***************
*>
     display  " " at line ws-23-lines col 01 with erase eol.
*>
 clear-error-line-24.
*>******************
*>
     display  " " at line ws-lines    col 01 with erase eol.
*>
 test-escape  section.
*>===================
*>
     display  escape-code at 2071 with foreground-color 6.
*>
 get-escape.
*>*********
*>
     accept   escape-code at 2071 with foreground-color 6 update UPPER.
*>
     if       escape-code not = "B" and not = "S" and not = "Q"
                      and not = "K" and not = "D"
                      and not = "T"                           *> TESTING ONLY during cust. display
              go to get-escape.
*>
 main-exit.   exit section.
*>********    ****
*>
 display-heading         section.
*>==============================
*>
     display  " " at 0101 with foreground-color 2 erase eos.
*>
     move     spaces to d24-02 d24-check.
     move     "]" to d24-03.
*>
     if       menu-reply not = 4
              display prog-name at 0101 with foreground-color 2
              perform zz070-convert-date
              move    ws-date to ws-local-date
              display ws-date at 0171 with foreground-color 2.
*>
     if       menu-reply = zero
              display "Customer File Set-Up & Maintenance" at 0124 with foreground-color 2
              display "Function Menu" at 0434                     with foreground-color 2
              go to main-exit
     else
       if     menu-reply = 1
              display "Customer Record Creation"  at 0129 with foreground-color 2
              move "Check Digit { }" to d24-check
              move "]" to d24-02
              move space to d24-03
       else
        if    menu-reply = 2
              display "Customer Record Amendment" at 0129 with foreground-color 2
        else
         if   menu-reply = 3
              display "Customer Record Deletion"  at 0129 with foreground-color 2
         else
          if  menu-reply = 5
              display "Customer Record Display"   at 0129 with foreground-color 2
          else
           if Menu-Reply = 6
              display "Amend Back Order Status"   at 0129 with foreground-color 2.
*>
 main-exit.   exit section.
*>********    ****
*>
 customer-display   section.
*>*************************
*>
     if       late-charges
              move  "Y" to a01-late-charg
     else
              move  "N" to a01-late-charg.
*>
     if       dunning-letters
              move  "Y" to a01-dun-letter
     else
              move  "N" to a01-dun-letter.
*>
     if       Email-Invoicing
              move "Y" to a01-Email-Inv
     else
              move "N" to a01-Email-Inv.
     if       Email-Statementing
              move "Y" to a01-Email-Stat
     else
              move "N" to a01-Email-Stat.
     if       Email-Dunning
              move "Y" to a01-Email-Let
     else
              move "N" to a01-Email-Let.
     if       menu-reply = 1
              move WS-Sales-Key (7:1) to d24-digit
*>              move check-digit of WS-Sales-Key to d24-digit
     else
              move WS-Sales-Key (7:1) to d24-02.
*>              move check-digit of WS-Sales-Key to d24-02.
*>
     if       Sales-Partial-Ship-Flag = space
              move "N" to Sales-Partial-Ship-Flag.
     display  display-02.
     if       menu-reply = 1 or 2
              go to cd-exit.
*>
     move     sales-unapplied to display-bal.
     display  display-bal at 2017 with foreground-color 2.
*>
     move     sales-current  to  display-bal.
     display  display-bal at 2117 with foreground-color 2.
*>
     if       sales-last-inv not = zero
              move sales-last-inv  to  u-bin
              perform zz060-Convert-Date
              display ws-date at 2217 with foreground-color 2.
*>
     if       sales-last-pay not = zero
              move sales-last-pay  to  u-bin
              perform zz060-Convert-Date
              display ws-date at 2317 with foreground-color 2.
*>
 cd-exit.
     exit     section.
*>
 Display-Outline         section.
*>==============================
*>
     perform  display-heading.
     initialize WS-Sales-Record
                WS-Delivery-Record.
     move     spaces to a01-late-charg
                        a01-dun-letter
                        a01-Email-Let
                        a01-Email-Stat
                        a01-Email-Inv
                        a01-deliv-name
                        a01-Deliv-Address
                        a01-Notes.
     display  display-02.
*>
 main-exit.   exit section.
*>********    ****
*>
 customer-data           section.
*>==============================
*>
 Customer-Data-Main.
     move     zero to error-flag.
     display  display-02.
     accept   display-02.
*>
     move     sales-address  to  test-address.
     perform  validate-address.
*>
     if       a-false
              display SL101 at 0766 with foreground-color 4
              move 1 to error-flag
      else
              display space at 0766 with erase eol
     end-if
*>
     if       A01-deliv-name = spaces
       and    A01-deliv-Address = spaces
        and   delivery-tag not = zero
              move WS-Sales-Key to WS-Deliv-Sales-Key
              move "D"          to WS-Deliv-Key-Type
              perform Delivery-Delete     *> delete delivery-file invalid key
              if     fs-Reply not = zero
                     move zero to delivery-tag
              end-if
     end-if
*>
     if       A01-deliv-Name = spaces
       and    A01-deliv-Address = spaces
              move  zero  to  delivery-tag
              go to bypass-deliv-test
     end-if
*>
     move     A01-deliv-address  to  test-address.
     perform  validate-address.
*>
     if       a-false
              display SL101 at 1066 with foreground-color 4
              move 1 to error-flag
      else
              display " " at 1066 with erase eol
     end-if
*>
     if       A01-deliv-address not = spaces
              move 1 to Delivery-Tag.
*>
 bypass-deliv-test.
*>****************
*>
     if       A01-Notes = spaces
         and  Notes-Tag not = zero
              move WS-Sales-Key to WS-Deliv-Sales-Key
              move "N"          to WS-Deliv-Key-Type
              perform  Delivery-Delete        *> delete delivery-file invalid key
              if       fs-reply not = zero
                       move zero to Notes-tag
              end-if
     end-if
*>
*>  yes I know, but just in case!!
*>
     if       A01-Notes = spaces
              move zero to Notes-Tag
     else
              move 1 to Notes-Tag
     end-if.
*>
 Bypass-Notes-Test.
*>****************
*>
     move     a01-late-charg to ws-reply.
     perform  validate-response.
*>
     if       a-true
              move  z  to  sales-late
              display ws-spaces-7 at 1619
     else
              move 1 to error-flag
              display SL102 at 1619 with foreground-color 4.
*>
     move     FUNCTION UPPER-CASE (Sales-Partial-Ship-Flag) to Sales-Partial-Ship-Flag.
     if       Sales-Partial-Ship-Flag = space
              move "N" to Sales-Partial-Ship-Flag.
     if       Sales-Partial-Ship-Flag = "Y" or
                                      = "N"
              display " " at 1575
     else
              move 1 to Error-Flag
              display "*" at 1575 with foreground-color 4.
*>
     move     a01-dun-letter to ws-reply.
     perform  validate-response.
*>
     if       a-true
              display ws-spaces-7 at 1719
              move  z  to  sales-dunning
     else
              move 1 to error-flag
              display SL102 at 1719 with foreground-color 4.
*>
     move     a01-Email-Inv to ws-reply.
     perform  validate-response.
     if       a-true
              display " " at 1839
              move z to Email-Invoice
     else
              move 1 to error-flag
              display "*" at 1839 with foreground-color 4.
*>
     move     a01-Email-Stat to ws-reply.
     perform  validate-response.
     if       a-true
              display " " at 1849
              move z to Email-Statement
     else
              move 1 to error-flag
              display "*" at 1849 with foreground-color 4.
*>
     move     a01-Email-Let to ws-reply.
     perform  validate-response.
     if       a-true
              display " " at 1859
              move z to Email-Letters
     else
              move 1 to error-flag
              display "*" at 1859 with foreground-color 4.
*>
     if       error-flag not = zero
              go to customer-data-Main.
*>
 main-exit.   exit section.
*>********    ****
*>
 validate-address        section.
*>==============================
*>
     move     zero  to  a.
*>
     inspect  test-address  tallying a for all SL-Delim.
*>
     if       a  >  5  or  <  1
              move  zero  to  truth
     else
              move  1  to  truth.
*>
     move     zero  to  a.
     inspect  test-address tallying a for characters before initial SL-Delim.
*>
*> Check for basic report/label limits
*>
     if       a  >  30
              move  zero  to  truth.
*>
 main-exit.   exit section.
*>********    ****
*>
 validate-response       section.
*>==============================
*>
     move     1  to  truth.
*>
     move     FUNCTION UPPER-CASE (ws-reply) to ws-reply.
     if       ws-reply = "Y"
              move  1  to  z
     else
      if      ws-reply = "N"
              move  zero  to  z
      else
              move  zero  to  truth.
*>
     if       a-false
              display SL110   at 2301
              display SL002   at 2401
              accept ws-reply at 2440
              go to main-exit.
*>
     perform  clear-error-line-24.
*>
 main-exit.   exit section.
*>********    ****
*>
 Accept-Key              section.
*>==============================
*>
     move     spaces to WS-Sales-Key.
*>
     accept   WS-Sales-Key at 0417 with foreground-color 3 UPPER.
*>
     move     zero  to  error-code.
*>
     if       WS-Sales-Key = spaces
              move  999  to  error-code
              go to  main-exit.
*>
     move     zero to     save-tag
                          save-notes-tag.               *> force clear
     perform  Sales-Read-Indexed.
     if       FS-reply = 21
              display SL111  at 2301
              move spaces to  customer-code
              go to  main-exit.
*>
     perform  clear-error-line.
     move     WS-Sales-Key  to  customer-code.
*>
*>  Check for Delivery address
*>
     if       delivery-tag not = zero
              move     WS-Sales-Key to WS-Deliv-Sales-Key
              move     "D"          to WS-Deliv-Key-Type
              perform Delivery-Read-Indexed
              if      fs-reply = 21
                          move zero  to  delivery-tag
                          move "Record not found"  to A01-deliv-name
                          move space               to A01-Deliv-Address
              else             *>  not invalid key
                          move deliv-name     to A01-deliv-name
                          move deliv-address  to A01-Deliv-Address
                          move 1              to save-tag  delivery-tag
     end-if
*>
*>  Check for Notes
*>
     if       Notes-Tag not = zero
              move     WS-Sales-Key to WS-Deliv-Sales-Key
              move     "N"          to WS-Deliv-Key-Type
              perform Delivery-Read-Indexed
              if      fs-reply = 21
                          move zero  to  Notes-tag
                          move "Record Not Found" to A01-Notes-1
                          move spaces             to A01-Notes-2
              else   *>    not invalid key
                          move Deliv-Address to A01-Notes
                          move 1     to save-notes-tag
                                        notes-tag
     end-if.
*>
 main-exit.   exit section.
*>********    ****
*>
 ba000-Setup-Customers   section.
*>==============================
*>
     perform  Sales-Open.
     perform  Delivery-Open.
*>
 customer-input.
*>*************
*>
     move     spaces to a01-Notes.
     perform  Display-Outline.
*>
 customer-accept.
*>**************
*>
     move     spaces to customer-nos.
     accept   customer-nos at 0417 with foreground-color 3 UPPER.
     if       customer-nos = spaces
              go to  main-end.
     display  customer-nos at 0417 with foreground-color 3.
*>
     perform  clear-error-line.
*>
     move     "C"  to  maps09-reply.
     perform  maps09.
     if       maps09-reply not = "Y"
              go to  customer-accept.
*>
     move     customer-code  to  WS-Sales-Key.
 *>    read     sales-file  not invalid key        *>    Therefore, Record already exists
     perform  Sales-Read-Indexed.
     if       FS-Reply not = 21
              display SL112  at 2301
              perform  customer-display
              go       to customer-accept.
*>
 customer-details.
*>***************
*>
     if       menu-reply = 1
              display check-digit of maps09-ws at 0439 with foreground-color 3.
*>
     display  ws-spaces-30 at 2101.
     display  ws-spaces-30 at 2201.
     display  ws-spaces-30 at 2301.
     initialize WS-Sales-Record
                WS-Delivery-Record.          *>  and grab defaults from system file
     move     customer-code to WS-Sales-Key.
     move     SL-BO-Default to Sales-Partial-Ship-Flag.
     move     sl-charges to  sales-late.
     move     sl-dunning to  sales-dunning.
     move     sl-credit  to  sales-credit.
     move     sl-disc    to  sales-discount.
     move     sl-min     to  sales-late-min.
     move     sl-max     to  sales-late-max.
     move     sl-limit   to  sales-limit.
     move     run-date   to  sales-create-date.
     move     1          to  sales-status.              *> Live
*>
 get-details.
*>***********
*>
     perform  customer-display.
     perform  customer-data.
*>
     move     "S"  to   escape-code.
     perform  test-escape.
*>
 main-output.
*>***********
*>
     if       escape-code = "B"
              go to get-details.
*>
     if       escape-code = "Q"
              go to  main-end.
*>
 *>    we know that rec doesnt exist and file is open so no test
     perform  Sales-Write.
*>
     if       delivery-tag  not = zero
              move   WS-Sales-Key to WS-Deliv-Sales-Key
              move   "D"          to WS-Deliv-Key-Type
              move   A01-deliv-name    to deliv-name
              move   A01-deliv-address to deliv-address
              perform Delivery-Write.
*>
     if       Notes-Tag not = zero
              move   WS-Sales-Key to WS-Deliv-Sales-Key
              move   "N"          to WS-Deliv-Key-Type
              move   spaces    to deliv-name
              move   A01-Notes to deliv-address
              perform Delivery-Write.
*>
     initialize WS-Sales-Record
                WS-Delivery-Record.
     go       to customer-input.
*>
 main-end.
*>*******
*>
     perform  Sales-Close.
     perform  Delivery-Close.
*>
 main-exit.   exit section.
*>********    ****
*>
 ca000-Amend-Customer  section.
*>============================
*>
     perform  Sales-Open.
     perform  Delivery-Open.
*>
 customer-input.
*>*************
*>
     perform  Display-Outline.
*>
 customer-accept.
*>**************
*>
     perform  Accept-Key.
*>
     if       error-code = 999
              go to  main-end.
*>
     if       customer-code = spaces
              go to  customer-accept.
*>
     move     delivery-tag  to  save-tag.
     move     Notes-Tag     to  save-Notes-Tag.
     if       Email-Invoice not = 0 and not = 1
              move zero to Email-Invoice Email-Statement Email-Letters.
*>
 get-details.
*>**********
*>
     perform  customer-display.
     perform  customer-data.
     move     "S"  to   escape-code.
     perform  test-escape.
*>
 main-output.
*>**********
*>
     if       escape-code = "B"
              go to get-details.
*>
     if       escape-code = "Q"
              go to  customer-input.
*>
*>  Now deal with delivery Address
*>
     move     "D"           to WS-Deliv-Key-Type.
     move     WS-Sales-Key  to WS-Deliv-Sales-Key.
     move     A01-deliv-name    to deliv-name.
     move     A01-deliv-address to deliv-address.
*>
     if       delivery-tag  not = zero
       and    save-tag = zero
 *>  THIS STUFF FOR DEBUGGING, REMOVE AFTER
              perform Delivery-Write
              if       fs-reply not = zero
                       display "write deliverytag " at line ws-23-lines col 1
                       display fs-reply at line ws-23-lines col 20
                       perform evaluate-message
                       display ws-Eval-Msg at line ws-23-lines col 23
                       display SL002        at line ws-lines col 1
                       accept  Accept-Reply at line ws-lines col 20
                       display " " at line ws-23-lines col 1 with erase eos
*>
                       perform Delivery-Rewrite
              end-if
     else
      if      delivery-tag  not = zero
 *>  THIS STUFF FOR DEBUGGING, REMOVE AFTER
              perform Delivery-Rewrite
              if       fs-reply not = zero
                       display "rewrite deliverytag " at line ws-23-lines col 1
                       display fs-reply at line ws-23-lines col 20
                       perform evaluate-message
                       display ws-Eval-Msg at line ws-23-lines col 23
                       display SL002       at line ws-lines col 1
                       accept  Accept-Reply at line ws-lines col 20
                       display " " at line ws-23-lines col 1 with erase eos.
*>
     if       delivery-tag = zero
       and    save-tag  not = zero
 *>    THIS STUFF FOR DEBUGGING, REMOVE AFTER
              perform Delivery-Delete
              if      fs-reply not = zero
                      display "Delete deliverytag " at line ws-23-lines col 1
                      display fs-reply at line ws-23-lines col 20
                      perform evaluate-message
                      display ws-Eval-Msg at line ws-23-lines col 23
                      display SL002       at line ws-lines col 1
                      accept  Accept-Reply at line ws-lines col 20
                      display " " at line ws-23-lines col 1 with erase eos.
*>
*>  Now deal with Notes
*>
     move     "N"            to WS-Deliv-Key-Type.
     move     WS-Sales-Key   to WS-Deliv-Sales-Key.
     move     spaces      to deliv-name.
     move     A01-Notes   to deliv-address.
*>
     if       Notes-Tag not = zero
        and   save-notes-tag = zero
 *>  THIS STUFF FOR DEBUGGING, REMOVE AFTER
              perform Delivery-Write
              if      fs-reply not = zero
                      display "write notes tag " at line ws-23-lines col 1
                      display fs-reply  at line ws-23-lines col 20
                      perform evaluate-message
                      display ws-Eval-Msg at line ws-23-lines col 23
                      display SL002       at line ws-lines col 1
                      accept  Accept-Reply at line ws-lines col 20
                      display " " at line ws-23-lines col 1 with erase eos
              end-if
     else
      if      Notes-Tag not = zero
 *>   THIS STUFF FOR DEBUGGING, REMOVE AFTER
              perform Delivery-Rewrite
              if      fs-reply not = zero
                      display "Rewrite notes tag " at line ws-23-lines col 1
                      display fs-reply
                      perform evaluate-message
                      display ws-Eval-Msg at line ws-23-lines col 23
                      display SL002       at line ws-lines col 1
                      accept  Accept-Reply at line ws-lines col 20
                      display " " at line ws-23-lines col 1 with erase eos
              end-if.
*>
     if       Notes-Tag = zero
       and    save-notes-tag  not = zero
 *>    THIS STUFF FOR DEBUGGING, REMOVE AFTER
              perform Delivery-Delete
              if      fs-reply not = zero
                      display "Delete notes tag " at line ws-23-lines col 1
                      display fs-reply
                      perform evaluate-message
                      display ws-Eval-Msg at line ws-23-lines col 23
                      display SL002       at line ws-lines col 1
                      accept  Accept-Reply at line ws-lines col 20
                      display space at line ws-23-lines col 1 with erase eos
              end-if.
*>
 *>                 tags should be set already
     perform  Sales-Rewrite.
     if       fs-reply not = zero
                      display "Rewrite Sales Rec " at line ws-23-lines col 1
                      display fs-reply
                      perform evaluate-message
                      display ws-Eval-Msg at line ws-23-lines col 23
                      display SL002       at line ws-lines col 1
                      accept  Accept-Reply at line ws-lines col 20
                      display " " at line ws-23-lines col 1 with erase eos
     end-if.
     go       to customer-input.
*>
 main-end.
*>*******
*>
     perform  Sales-Close.
     perform  Delivery-Close.
*>
 main-exit.   exit section.
*>********    ****
*>
 Evaluate-Message        Section.
*>==============================
*>
 copy "FileStat-Msgs.cpy" replacing MSG by ws-Eval-Msg
                                    STATUS by fs-reply.
*>
 Eval-Msg-Exit.  exit section.
*>************   ************
*>
 da000-Delete-Customer  section.
*>=============================
*>
     perform  Sales-Open.
     perform  Delivery-Open.
*>
 customer-input.
     perform  Display-Outline.
     display  "D> = Dormant" at 2159 with foreground-color 2.
     display  "K> = Kill " at 2259 with foreground-color 2.
*>
 customer-accept.
     perform  Accept-Key.  *> get sales cust key
*>
     if       error-code = 999
              go to  main-end.
*>
     if       customer-code = spaces
              go to  customer-accept.
*>
 get-details.
     perform  customer-display.
*>
     move     "K"  to   escape-code.
     perform  test-escape.
*>
     if       escape-code = "Q"
              go to  main-end.
*>
     move     spaces to BO-Cust-Itm-No.
     if       WS-BO-Active
              move     WS-Sales-Key to BO-Stk-Cust-No
              move     low-values   to BO-Stk-Item-No
              start    BO-Stk-Itm-File KEY not < BO-Cust-Itm-No
              read     BO-Stk-Itm-File next record.
*>
     if       sales-current not = zero
          or  sales-unapplied not = zero
          OR  BO-Stk-Cust-No = WS-Sales-Key
              display SL109  at 0501 with foreground-color 4
              go to  customer-accept.
*>
     display  " " at 0501 with erase eol.
*>
     if       escape-code = "D"
              move  zero  to  sales-status
              perform Sales-Rewrite.
*>
     if       escape-code  not = "K"
              go to  customer-input.
*>
 main-output.
*>**********
*>
*>  Delete and dont bother checking if present as delete will fail so no prob.
*>
     move     "D"          to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Delete.
     move     "N"          to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Delete.
     perform  Sales-Delete.
*>
 main-end.
*>*******
*>
     perform  Sales-Close.
     perform  Delivery-Close.
*>
 main-exit.   exit section.
*>********    ****
*>
 ea000-Report-Customers  section.
*>==============================
*>
     perform  Report-Selection.
     perform  Report-Heading-Setup.
     perform  Produce-Report.
*>
 main-end.
*>
     perform  Sales-Close.
     perform  Delivery-Close.
*>
 main-exit.   exit section.
*>********    ****
*>
 ga000-Amend-BO-Status   section.
*>==============================
*>
     perform  Sales-Open.
*>
 ga010-Customer-Input.
     perform  display-heading.
     move     "Y" to WS-BO-State. *> preset but others will use last used.
*>
 ga020-Customer-Accept.
     display  "Customer account for search and change [       ]" at 0401
                                                    with foreground-color 2
                                                    erase eol.
     display  "BO State [ ]" at 0461 with foreground-color 2.
     display  "Escape = Quit, one or more chars process group of customers, or 7 Chars for one"
                                                at 0701
                                                with foreground-color 4 erase eol.
     accept   Customer-In at 0441 with foreground-color 3 UPPER.
     if       Cob-CRT-Status = Cob-Scr-Esc
              go to ga990-Quit.
     accept   WS-BO-State at 0471 with foreground-color 3 UPPER update.
     if       not WS-BO-Valid-State
              display  "Invalid State not Y or N" at line WS-23-Lines col 1
                                   with foreground-color 4 highlight beep erase eol
              go to ga020-Customer-Accept
     end-if
     display  " " at line WS-23-Lines col 1 with erase eos  *> clear any err/warn msgs
*>
     move     Customer-In to WS-Sales-Key.  *> In sales key in rec
*>
 ga100-Process.
     move     FUNCTION STORED-CHAR-LENGTH (Customer-In) to B.
     if       B > 7       *> JIC
              stop     "Error in function STORED-CHAR-LENGTH"
              go to    ga990-Quit.
     if       B < 7   *> group range select
              go to    ga110-Process-Block-Selections
     else                    *> doing just one
              perform  Sales-Read-Indexed
              if       FS-reply not = zeros
                       display SL111 at line WS-23-Lines col 1 with foreground-color 4
                                                               highlight beep erase eol
                       move spaces to  Customer-In
                       go to  ga010-Customer-Input
              end-if
              move     WS-BO-State to Sales-Partial-Ship-Flag
              perform  Sales-Rewrite
    end-if.
    go        to ga020-Customer-Accept.
*>
 ga110-Process-Block-Selections.  *> being performed
*>
*> Customer-IN is less than 7 so do all of same first chars present
*>
     if       Customer-IN not = spaces
              set      fn-not-less-than to true
              perform  Sales-Start
              if       fs-reply not = zero
                       display  "No records match criteria" at line WS-23-Lines col 1
                                    with foreground-color 4 highlight beep erase eol
                       go to    ga020-Customer-Accept
              else
                       display  " " at line WS-23-Lines col 1 erase eol
              end-if
              perform  until exit
                       perform  Sales-Read-Next
                       if       FS-Reply not = zeros
                                display " EoF - Requested Process Completed" at line WS-23-Lines col 1
                                                        with foreground-color 2 beep erase eol
                                exit perform
                       end-if
                       if       WS-Sales-Key (1:B) not = Customer-In (1:B)
                                display " Requested Selection Range Process Completed" at line WS-23-Lines col 1
                                                        with foreground-color 2 beep erase eol
                                exit perform
                       end-if
                       move     WS-BO-State to Sales-Partial-Ship-Flag
                       perform  Sales-Rewrite
                       exit     perform cycle
              end-perform
     else   *> we do all of them
              perform  until exit
                       perform  Sales-Read-Next
                       if       FS-Reply not = zeros
                                display " Requested process completed" at line WS-23-Lines col 1
                                                        with foreground-color 2 beep erase eol
                                exit perform
                       end-if
                       move     WS-BO-State to Sales-Partial-Ship-Flag
                       perform  Sales-Rewrite
                       exit     perform cycle
              end-perform
     end-if
     go to    ga020-Customer-Accept.
*>
 ga990-Quit.
     display  " " at 0401 with erase eos.
     perform  Sales-Close.
*>
 Main-Exit.   exit section.
*>

 fa000-Display-Customers section.
*>==============================
*>
     perform  Delivery-Open-Input.
     perform  Sales-Open.
*>
 customer-input.
*>*************
*>
     perform  Display-Outline.
*>
 customer-accept.
*>
     perform  Accept-Key.
*>
     if       error-code = 999
              go to  main-end.
*>
     if       customer-code = spaces
              go to  customer-accept.
*>
     perform  customer-display.
*>
 accept-of-show.
*>*************
*>
     move     "S" to escape-code.
     perform  test-escape.
*>
*> TEST CODE ONLY
*>
     if       Escape-Code = "T"
              move     20 to lin
              move     17 to cole
              move     Sales-Unapplied to amt-ok9
              perform  zz030-accept-money9c
              move     amt-ok9 to Sales-Unapplied
              move     21 to lin
              move     17 to cole
              move     Sales-Current to amt-ok9
              perform  zz030-accept-money9c
              move     amt-ok9 to Sales-Current
              perform Sales-Rewrite
     end-if
*>
     if       Escape-Code not = "Q"
              go to  customer-input.
*>
 main-end.
*>*******
*>
     perform  Sales-Close.
     perform  Delivery-Close.
*>
 main-exit.   exit section.
*>********    ****
*>
 report-selection        section.
*>==============================
*>
     perform  Sales-Open-Input.
     perform  Delivery-Open-Input.
*>
     move     spaces to cust-in status-in credit-op invoice-op
                        average-op overdue-op enter-date-op
                        enter-date-in print-out.
*>
     move     zero to credit-in invoice-in average-in overdue-in ws-enter-date.
     display  display-03.
*>
 accept-data.
*>**********
*>
     accept   display-03.
     move     FUNCTION UPPER-CASE (cust-in) to cust-in.
     move     cust-in to customer-in.
     move     FUNCTION UPPER-CASE (status-in) to status-in.
     if       status-in not = "L" and not = "D" AND not = space
              go to  accept-data.
*>
     move     FUNCTION UPPER-CASE (credit-op) to credit-op.
     if       credit-op not = "L" and not = "G" and not = "E" and not = space
              go to  accept-data.
*>
     move     FUNCTION UPPER-CASE (invoice-op) to invoice-op.
     if       invoice-op not = "L" and not = "G" and not = "E" and not = space
              go to  accept-data.
*>
     move     FUNCTION UPPER-CASE (average-op) to average-op.
     if       average-op not = "L" and not = "G" and not = "E" and not = space
              go to  accept-data.
*>
     move     FUNCTION UPPER-CASE (overdue-op) to overdue-op.
     if       overdue-op not = "L" and not = "G" and not = "E" and not = space
              go to  accept-data.
*>
     move     FUNCTION UPPER-CASE (enter-date-op)   to enter-date-op.
     if       enter-date-op not = "L" and not = "G" AND not = "E" and not = space
              go to  accept-data.
*>
     if       enter-date-in = spaces
              go to main-end.
     move     zero to u-bin.
     move     enter-date-in to ws-test-date.  *> was u-date
     perform  zz050-Validate-Date.
     if       u-bin = zero
              display SL005 at 2362 with foreground-color 4
              go to accept-data.
     display  " " at 2362 with erase eol.
     move     u-bin to ws-enter-date.
*>     move     u-date to enter-date-in.     *> not sure about this, means that say intl date is now uk????
*>
 main-end.    exit section.
*>*******     *****
*>
 produce-report          section.
*>==============================
*>
     open     output  print-file.
     move     zero to a.
     perform  headings.
*>
     if       Customer-In = spaces
              go to read-loop.
     move     Customer-In to WS-Sales-Key.
     set      fn-not-less-than to true.
     perform  Sales-Start.
     if       fs-reply = 21
              move 1 to a.
     inspect  Customer-In replacing all space by "Z".
*>
 read-loop.
*>********
*>
     perform  Sales-Read-Next.
     if       fs-reply = 10
              go to  end-report.
     if       fs-reply not = zero
              go to end-report.
*>
     if       status-in = "L"
       and    customer-dead
              go to  read-loop.
     if       status-in = "D"
       and    customer-live
              go to  read-loop.
*>
     if       Customer-In not = spaces
        and   WS-Sales-Key > customer-in
              go to end-report.
*>
     if       credit-op not = space
              move  credit-in     to  test-1
              move  sales-credit  to  test-2
              move  credit-op     to  test-op
              perform  test-num
              if    a-false
                    go to  read-loop.
*>
     if       invoice-op not = space
              move  invoice-in     to  test-1
              move  sales-activety to  test-2
              move  invoice-op     to  test-op
              perform  test-num
              if    a-false
                    go to  read-loop.
*>
     if       average-op not = space
              move  average-in    to  test-1
              move  sales-average to  test-2
              move  average-op    to  test-op
              perform  test-num
              if    a-false
                    go to  read-loop.
*>
     if       overdue-op not = space
        and   sales-current  > 0.00
              move  overdue-in    to  test-1
              subtract sales-last-inv from run-date giving test-2
              move  overdue-op    to  test-op
              perform  test-num
              if    a-false
                    go to  read-loop.
*>
     if   enter-date-op not = space
          move  ws-enter-date     to  test-1
          move  sales-create-date to  test-2
          move  enter-date-op     to  test-op
          perform  test-num
          if    a-false
                go to  read-loop.
*>
     perform  listing.
     go       to read-loop.
*>
 test-num.
*>*******
*>
     if       test-op  = space
              move  1  to  truth
     else
              move  0  to  truth.
*>
     if       test-op = "L"
       and    test-2  <  test-1
              move  1  to  truth.
*>
     if       test-op = "G"
       and    test-2  >  test-1
              move  1  to  truth.
*>
     if       test-op = "E"
       and    test-2  =  test-1
              move  1  to  truth.
*>
 headings.
*>*******
*>
     add      1  to  a.
     move     a  to  l1-page.
     if       a not = 1
              write print-record  from  line-1 after page
              write print-record  from  line-3 after 1
              move  spaces  to  print-record
              write print-record after 1
     else
              write print-record  from  line-1 before 1
              write print-record  from  line-3 before 1
     end-if
     write    print-record  from  line-4 after 1.
     write    print-record  from  line-5 after 1.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     6 to line-cnt.
*>
 Listing.
*>******
*>
     if       line-cnt > Page-Lines
              perform  headings.
     move     WS-Sales-Key  to  l6-key.
*>
     if       customer-live
              move  "Active"  to  l6-status
     else
              move  "Dormant" to  l6-status.
*>
     move     spaces         to  l6-phone.
     move     sales-name     to  l6-name.
     move     sales-address  to  l7-address.
     inspect  l7-address  replacing  all  SL-Delim  by  ",".
     if       sales-ext = spaces
              move sales-phone to l6-phone
     else
              move 1 to y
              string sales-phone delimited by "  "
                            into l6-phone with pointer y
              subtract 1 from y
              string "x"       delimited by size
                     sales-ext delimited by size
                            into l6-phone with pointer y.
*>
     move     sales-fax to l6-fax.
     move     Sales-Partial-Ship-Flag to L6-BO.
*>
     if       late-charges
              move  "Y"     to  l6-charges
     else
              move  spaces  to  l6-charges.
*>
     if       dunning-letters
              move  "Y"     to  l6-letter
     else
              move  spaces  to  l6-letter.
*>
     move     sales-limit   to  l6-limit.
     move     sales-credit  to  l6-credit.
     move     sales-discount to l6-discount.
*>
     if       line-cnt > Page-Lines - 5
              perform headings.
     write    print-record  from  line-6 after 1.
     write    print-record  from  line-7 after 1.
*>
     if       delivery-tag  >  zero
              perform  delivery-print.
     if       Notes-Tag > zero
              perform  notes-print.
*>
     move     spaces  to  print-record.
     write    print-record after 1.
     add      3 to line-cnt.
     move     "Y" to Print-Out.
*>
 delivery-print.
*>*************
*>
     move     "D"       to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Read-Indexed.
     if       fs-reply not = zero
              move "Record Not Found" to deliv-name.
*>
     move     "   Deliver"   to  l6-key.
     move     "y Address"    to  l6-status.
     move     deliv-name     to  l6-name.
     move     deliv-address  to  l7-address.
     if       Deliv-Name not = "Record Not Found"
              inspect  l7-address  replacing  all  SL-Delim  by  ",".
*>
     move     spaces  to  l6-phone  l6-fax
                          l6-charges
                          l6-letter.
     move     zero    to  l6-limit
                          l6-credit
                          l6-discount.
*>
     write    print-record  from  line-6 after 1.
     write    print-record  from  line-7 after 1.
     add      2 to line-cnt.
*>
 notes-print.
     move     "N"       to WS-Deliv-Key-Type.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     perform  Delivery-Read-Indexed,
     if       fs-reply not = zero
              move "Record Not Found" to deliv-Address.
*>
     move     spaces to l7-address.
     string   "Notes: " delimited by size
              deliv-address delimited by "  " into l7-address.
     write    print-record from line-7 after 1.
     add      1 to line-cnt.
*>
 end-report.
*>*********
*>
 main-end.
*>*******
*>
     close    print-file.
     if       Print-Out = "Y"
              call "SYSTEM" using Print-Report.
*>
 main-exit.   exit section.
*>********    ****
*>
 report-heading-setup    section.
*>==============================
*>
     perform  zz070-convert-date.
     move     ws-date to l3-date.
     move     usera  to  l3-user.
     add      1      to  y.
     move     spaces to  l3-report.
*>
     if       status-in = spaces  and  credit-op
         and  invoice-op   and  average-op
         and  overdue-op   and  customer-in
              string  "All"  delimited by size
                          into  l3-report with  pointer  y
     else
              string  "Matched"  delimited by size
                          into  l3-report with  pointer  y.
*>
     add      1  to  y.
*>
     if       status-in = "L"
              string  "Live"     delimited by size
                          into  l3-report with  pointer  y.
     if       status-in = "D"
              string  "Dormant"  delimited by size
                          into  l3-report with  pointer  y.
*>
     add      1  to  y.
*>
     if       credit-op = "L"
              move    "< "  to  cr-operand.
     if       credit-op = "G"
              move    "> "  to  cr-operand.
     if       credit-op = "E"
              move    "= "  to  cr-operand.
*>
     if       credit-op  not = space
              move  credit-in  to  cr-days
              string  credit-heading  delimited by size
                              into  l3-report with  pointer  y.
*>
     add      1  to  y.
*>
     if       invoice-op = "L"
              move    "< "  to  act-operand.
     if       invoice-op = "G"
              move    "> "  to  act-operand.
     if       invoice-op = "E"
              move    "= "  to  act-operand.
*>
     if       invoice-op  not = space
              move  invoice-in  to  act-days
              string  active-heading  delimited by size
                               into  l3-report with  pointer  y.
*>
     add      1  to  y.
*>
     if       average-op = "L"
              move    "< "  to  av-operand.
     if       average-op = "G"
              move    "> "  to  av-operand.
     if       average-op = "E"
              move    "= "  to  av-operand.
*>
     if       average-op  not = space
              move  average-in  to  av-days
              string  average-heading  delimited by size
                              into  l3-report with  pointer  y.
*>
     add      1  to  y.
*>
     if       overdue-op = "L"
              move    "< "  to  ov-operand.
     if       overdue-op = "G"
              move    "> "  to  ov-operand.
     if       overdue-op = "E"
              move    "= "  to  ov-operand.
*>
     if       overdue-op  not = space
              move  overdue-in  to  ov-days
              string  overdue-heading  delimited by size
                              into  l3-report with  pointer  y.
*>
     add      1  to  y.
*>
     if       enter-date-op = "L"
              move    "< "  to  ed-operand.
     if       enter-date-op = "G"
              move    "> "  to  ed-operand.
     if       enter-date-op = "E"
              move    "= "  to  ed-operand.
*>
     if       enter-date-op  not = space
              move  enter-date-in  to  ed-date
              string  enter-date-heading  delimited by size
                             into  l3-report with  pointer  y.
*>
     add      1  to  y.
*>
     if       Customer-In  not = spaces
              string  " Keys Matching - " delimited by size
                      Customer-In         delimited by size
                             into  l3-report with  pointer  y.
*>
 main-exit.   exit section.
*>********    *****
*>
 slcreate     section.
*>===================
*>
 SLcreate-Main.
     perform  display-heading.
     display  SL103  at 1201 with foreground-color 4.
     display  SL104  at 1301 with foreground-color 2.
     move     space to ws-reply.
     accept   ws-reply at 1343 with foreground-color 6 update UPPER.
     if       ws-reply = "N"
              exit program.
     if       ws-reply not = "Y"
              go to slcreate-Main.
*>
     display  SL105  at 1506 with foreground-color 2.
     perform  Sales-Open-Output.
     if       fs-reply not = zero
              display SL106    at 1201 with erase eol
              display fs-reply at 1234
              display SL004    at 1237
              accept  ws-reply at 1258
              perform Sales-Close   *> close sales-file
              go to main-exit.
     perform  Delivery-Open-Output.
     if       fs-reply not = zero
              display SL107    at 1201 with erase eol
              display fs-reply at 1237
              display SL004    at 1240
              accept  ws-reply at 1261
              perform Delivery-Close
              go to main-exit.
*>
     perform  Sales-Close.
     perform  Delivery-Close.
     move     "Y" to sales-ledger.
*>
 main-exit.   exit section.
*>
*>
 zz030-common-routines      section.
*>*********************************
*>
 zz030-accept-money9c.
     move     amt-wk-pence9 to ws-pence9.
     move     amt-wk-pds9 to ws-pound9.
     display  ws-amount-screen-display9 at curs with foreground-color 3.
     accept   ws-amount-screen-accept9  at curs with foreground-color 3 update.
     move     ws-pound9 to amt-wk-pds9.
     move     ws-pence9 to amt-wk-pence9.
*>
 zz030-exit.
     exit     section.
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
              go to zz050-Test-Date.
     if       Date-USA                *> swap month and days
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              go to zz050-Test-Date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to WS-Date.  *> swap Intl to UK form
     move     WS-Test-Date (1:4) to WS-Year.
     move     WS-Test-Date (6:2) to WS-Month.
     move     WS-Test-Date (9:2) to WS-Days.
*>
 zz050-Test-Date.
     move     WS-Date to U-Date.
     move     zero to U-Bin.
     perform  maps03.
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
     perform  maps03.
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
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
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
 zz070-Convert-Date          section.
*>**********************************
*>
*>  Converts date in To-Day to UK/USA/Intl date format using ACAS param
*>*********************************************************************
*> Input:   To-Day
*> output:  WS-Date as uk/US/Inlt date format
*>
     move     To-Day to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> Swap month and days
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> Swap Intl to UK form
     move     To-Day (7:4) to WS-Intl-Year.
     move     To-Day (4:2) to WS-Intl-Month.
     move     To-Day (1:2) to WS-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
