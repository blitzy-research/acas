       >>source free
*>****************************************************************
*>                                                               *
*>              Sales  Ledger Database Alpha List                *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.         sl160.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 25/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Sales Ledger Customer File Print sorted on Alphabetic name using alt key Sales-Name.
*>                        Uses o/p from sl165 if using Cobol files else
*>                        it is a ordered set from rdb.
*>**
*>    Version.            see prog-name in ws.
*>**
*>    Called modules.     maps04
*>                        acas012  ->
*>                         salesMT
*>                        acas014  ->
*>                         deliveryMT
*>**
*>    Error messages used.
*>      System Wide
*>                        SL005
*>      Module specific
*>                        SL170
*>**
*>    Changes.
*> 28/02/85 vbc - Support for enter date in report selection.
*> 03/03/09 vbc - .12 Migration to Open Cobol v3.00.0.
*> 29/05/09 vbc - .13 Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .14 Mod lpr.
*> 25/11/11 vbc - .15 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .16 Support for path+filenames. clear sort file.
*> 09/12/11 vbc -     Updated version to 3.01.nn & adjust code for IS delivery file
*>                    Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 24/10/16 vbc - .17 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 16/01/17 vbc - .18 Sort requirements removed (sl165) when processing
*>                    RDB tables as the sort step removed in place of
*>                    read Table by Order.
*>                    This code needs to be copied to pl160 & purchase changed.
*>                    Note: When using RDB tables there is no sorting,
*>                    Data is from selecting by order.
*>
*> 25/01/17 vbc       Dry testing completed.
*> 15/03/24 vbc   .19 Added support for Sales-Partial-Ship-Flag.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 18/04/24 vbc   .20 Left off the BO head.
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
*> copy "selsl.cob".
*> copy "seldel.cob".
 copy "selprint.cob".
*>
     select  sales-sort      assign        fn-sales,
                             access        sequential,
                             status        fs-reply.
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 copy "fdprint.cob".
*> copy "fdsl.cob".
*> copy "fddel.cob".
*>
 fd  sales-sort.
*>
 01  sales-sort-record.
     03  sales-sort-key       pic x(7).
*>
 working-storage section.
*>----------------------
 77  prog-name          pic x(15) value "SL160 (3.3.00)".
 copy "print-spool-command.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
 copy "wsmaps09.cob".
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
 01  fn-sales            pic x(12)      value "custsort.tmp".
*>
 01  ws-data.
     03  ws-reply        pic x.
     03  Print-Type      pic x.
         88  PLabels                    value "L".
         88  PReport                    value "R".
     03  a               pic 99.
     03  y               pic 99.
     03  z               pic 9.
     03  save-tag        pic 9(5).
     03  print-out       pic x.
     03  Truth           pic 9.
       88  A-True   value  1.
       88  A-False  value  0.
     03  Test-1          binary-long.   *> was  pic 9(5).
     03  Test-2          binary-long.   *> was  pic 9(5).
     03  Test-Op         pic x.
     03  credit-heading.
       05  cr-operand    pic xx.
       05  cr-days       pic z9.
       05  filler        pic x(12)       value  " Days Credit".
     03  active-heading.
       05  act-operand   pic xx.
       05  act-days      pic zzzz9.
       05  filler        pic x(9)        value  " Invoices".
     03  average-heading.
       05  av-operand    pic xx.
       05  av-days       pic zzzz9.
       05  filler        pic x(10)       value  " Av. Value".
     03  overdue-heading.
       05  ov-operand    pic xx.
       05  ov-days       pic zzzz9.
       05  filler        pic x(13)       value " days overdue".
     03  enter-date-heading.
       05  ed-operand    pic xx.
       05  ed-date       pic x(8).
       05  filler        pic x(11)    value " Entry Date".
     03  ws-enter-date     binary-long  value zero.
     03  address-line    pic x(32).
     03  Test-address    pic x(92).
     03  line-cnt        pic 99   comp value zero.
     03  Customer-In     pic x(7).
*>
     03  Cust-In         pic x(6)         value spaces.
     03  Status-In       pic x            value space.
     03  Credit-In       pic 99           value zero.
     03  Credit-Op       pic x            value space.
     03  Invoice-In      pic 9(5)         value zero.
     03  Invoice-Op      pic x            value space.
     03  Average-In      pic 9(5)         value zero.
     03  Average-Op      pic x            value space.
     03  Overdue-In      pic 9(5)         value zero.
     03  Overdue-Op      pic x            value space.
     03  Enter-Date-In   pic x(10)        value spaces.
     03  Enter-Date-Op   pic x            value space.
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
 01  Error-Messages.
*> System Wide
     03  SL005          pic x(18) value "SL005 Invalid Date".
*> Module specific
     03  SL170          pic x(18) value "SL170 Not Found - ".
*>
 01  error-code          pic 999.
*>
 01  line-1.
     03  l1-name         pic x(51).
     03  filler          pic x(73)       value  "Customer Alphabetical Listing".
     03  filler          pic x(5)        value  "Page ".
     03  l3-page         pic zz9.
*>
 01  line-3.
     03  l3-user         pic x(40).
     03  filler          pic x(12)       value  "Report On : ".
     03  l3-report       pic x(70)       value  spaces.
     03  l1-date         pic x(10).
*>
 01  line-4.
     03  filler          pic x(127)      value
         "Customer  Status    <---------------Name & Address-------------->     ----Telephone---- -----Fax----- BO  Late       Credit".
     03  filler          pic x(5)        value "Disc ".
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
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  to-day              pic x(10).
*>
 screen section.
*>*************
*>
 01  display-03                  background-color cob-color-black
                                 foreground-color cob-color-green.
     03  from prog-name  pic x(15)                 line  1 col  1
                                                    blank screen.
     03  value "Customer File"                             col 34.
     03  from ws-date     pic x(10)                line  1 col 71.
     03  value "Report Attributes"                 line  3 col 32.
     03  value "Customer Number - ["               line  8 col  9.
     03  using Cust-In   pic x(6)                          col 28.
     03  value "]"                                         col 34.
     03  value "Enter characters in positions to match"    col 39.
     03  value "Status          - ["               line 10 col  9.
     03  using Status-In pic x                             col 28.
     03  value "]"                                         col 29.
     03  value "<L> Live;<D> Dormant;< > All"              col 39.
     03  value "Credit Period   - ["               line 12 col  9.
     03  using Credit-In pic 99                            col 28.
     03  value "]  ["                                      col 30.
     03  using Credit-Op pic x                             col 34.
     03  value "]"                                 line 12 col 35.
     03  value "Enter number of days & operator"           col 39.
     03  value "<L>  for credit periods < than"    line 13 col 43.
     03  value "<G>  for credit periods > than"    line 14 col 43.
     03  value "<E>  for credit periods = to"      line 15 col 43.
     03  value "Invoice Activity  ["               line 17 col  9.
     03  using Invoice-In pic 9(5)                         col 28.
     03  value "] ["                                       col 33.
     03  using Invoice-Op pic x                            col 36.
     03  value "]"                                         col 37.
     03  value "Enter number of invoices & operator"       col 39.
     03  value "Average Value   - ["               line 19 col  9.
     03  using Average-In pic 9(5)                         col 28.
     03  value "] ["                                       col 33.
     03  using Average-Op pic x                            col 36.
     03  value "]"                                         col 37.
     03  value "Enter invoice value & operator"            col 39.
     03  value "Overdue A/Cs    - ["               line 21 col  9.
     03  using Overdue-In pic 9(5)                         col 28.
     03  value "] ["                                       col 33.
     03  using Overdue-Op pic x                            col 36.
     03  value "]"                                         col 37.
     03  value "Enter number of days & operator"           col 39.
     03  value "Date Entered-["                    line 23 col  9.
     03  using Enter-Date-In pic x(10)                     col 23.
     03  value "] ["                                       col 33.
     03  using Enter-Date-Op pic x                         col 36.
     03  value "]"                                         col 37.
     03  value "Enter date & operator"                     col 39.
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 init01 section.
     move     prog-name to l1-name.
     perform  zz070-Convert-Date.
     move     ws-date to  l1-date.
     move     usera   to  l3-user.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
     move     1 to File-Key-No.
*>
     perform  Report1.
*>
 menu-exit.
     exit     program.
*>
*>************************************
*>            Procedures             *
*>************************************
*>
 Report1      section.
*>===================
*>
     perform  Sales-Open-Input.
     perform  Delivery-Open-Input.    *> open input  sales-file delivery-file.
*>
     perform  Report-Selection.
     perform  Report-Heading-setup.
     perform  Report-Produce.
*>
     close    print-file.             *>   sales-sort.  (Closed on read at end)
     perform  Sales-Close.
     perform  Delivery-Close.         *> close    sales-file delivery-file.
     call     "SYSTEM" using Print-Report.
     if       FS-Cobol-Files-Used             *> Make it a null file
              open     output sales-sort      *>  but only if processing
              close    sales-sort             *>   Cobol files.
     end-if.
*>
 main-exit.   exit.
*>
*>****************************************************************
*>       S e r v i c e    R o u t i n e s                        *
*>****************************************************************
*>
 Report-Selection            section.
*>==================================
*>
     move     spaces to Cust-In Status-In Credit-Op Invoice-Op
                        Average-Op Overdue-Op Enter-Date-Op
                        Enter-Date-In print-out.
*>
     move     zero to Credit-In Invoice-In Average-In Overdue-In.
     display  display-03.
*>
 Accept-Data.
*>**********
*>
     accept   display-03.
     move     function upper-case (Cust-In) to Cust-In.
     move     Cust-In to Customer-In.
     if       Customer-In not = spaces
              inspect Customer-In replacing all spaces by "Z".
*>
     move     function upper-case (Status-In) to Status-In.
     if       Status-In not = "L"
                    and not = "D"
                    and not = space
              go to  Accept-Data.
*>
     move     function upper-case (Credit-Op) to Credit-Op.
     if       Credit-Op not = "L"
                    and not = "G"
                    and not = "E"
                    and not = space
              go to  Accept-Data.
*>
     move     function upper-case (Invoice-Op) to Invoice-Op.
     if       Invoice-Op not = "L"
                     and not = "G"
                     and not = "E"
                     and not = space
              go to  Accept-Data.
*>
     move     function upper-case (Average-Op) to Average-Op.
     if       Average-Op not = "L"
                     and not = "G"
                     and not = "E"
                     and not = space
              go to  Accept-Data.
*>
     move     function upper-case (Overdue-Op) to Overdue-Op.
     if       Overdue-Op not = "L"
                     and not = "G"
                     and not = "E"
                     and not = space
              go to  Accept-Data.
*>
     move     function upper-case (Enter-Date-Op) to Enter-Date-Op.
     if       Enter-Date-Op not = "L"
                        and not = "G"
                        and not = "E"
                        and not = space
              go to  Accept-Data.
*>
     if       Enter-Date-In = spaces
              go to main-end.
     move     Enter-Date-In to ws-Test-date.
     perform  zz050-Validate-Date.
     if       u-bin = zero
              display SL005 at 2361  with foreground-color 2    *> this msg may NOT get seen
              go to Accept-Data.
*>
     display  " " at 2368 with erase eol.
     move     u-bin  to ws-enter-date.
*>
 Main-End.    exit section.
*>
 Report-Produce              section.
*>==================================
*>
     if       FS-Cobol-Files-Used
              open     input   sales-sort.
     open     output  print-file.
     move     zero  to  a.
     perform  Headings.
*>
 Read-Loop.
*>********
*>
*> Here we have two choices
*> 1: If using files (Cobol), so work via the sort file (from sl165)
*>    to help select records then read the Sales file.
*> 2: If NOT using files but RDB tables then process via ORDERED sales ledger
*>     table by SALES-NAME therefore only work with the one row
*>      [instead of 2 files].
*>
*> This way we get rid of a sort for Table processing as all done in RDBMS.
*>
     if       NOT FS-Cobol-Files-Used
              perform Sales-Read-Next-Sorted-By-Name
              if      fs-reply not = zero        *>   = 10
                      go to  End-Report
              end-if
              go to Read-Loop-Tests
     end-if
     read     sales-sort record at end
              close Sales-Sort
              go to  End-Report.
*>
     move     sales-sort-key  to  WS-Sales-Key.
*>
 Read-Loop-Tests.
     if       Customer-In not = spaces
         and  WS-Sales-Key < Customer-In
              go to Read-Loop.
*>
     if       Customer-In not = spaces
         and  WS-Sales-Key > Cust-In
              go to Read-Loop.
*>
     if       NOT FS-Cobol-Files-Used          *> we have the record
              go   to Select-Criteria-Tests-Continued.
*>
     perform  Sales-Read-Indexed.    *> read sales-file invalid key
     if       fs-reply = 21                *> tested for but should not happen.
              display SL170        at 2301 with foreground-color 4
              display WS-Sales-Key at 2319 with foreground-color 4
              go to  Read-Loop.
     display  " " at 2301 with erase eol.
*>
 Select-Criteria-Tests-Continued.
     if       Status-In = "L"
      and     customer-dead
              go to  Read-Loop
     else
       if     Status-In = "D"
        and   customer-live
              go to  Read-Loop.
*>
     if       Credit-Op not = space
              move  Credit-In     to  Test-1
              move  sales-credit  to  Test-2
              move  Credit-Op     to  Test-Op
              perform  Test-Num
              if    A-False
                    go to  Read-Loop.
*>
     if       Invoice-Op not = space
              move  Invoice-In     to  Test-1
              move  sales-activety to  Test-2
              move  Invoice-Op     to  Test-Op
              perform  Test-Num
              if    A-False
                    go to  Read-Loop.
*>
     if       Average-Op not = space
              move  Average-In    to  Test-1
              move  sales-average to  Test-2
              move  Average-Op    to  Test-Op
              perform  Test-Num
              if    A-False
                    go to  Read-Loop.
*>
     if       Overdue-Op not = space
        and   sales-current  >  0.00
              move  Overdue-In    to  Test-1
              subtract  sales-last-inv  from  run-date giving  Test-2
              move  Overdue-Op    to  Test-Op
              perform  Test-Num
              if    A-False
                    go to  Read-Loop.
*>
     if       Enter-Date-Op not = space
              move  ws-enter-date     to  Test-1
              move  sales-create-date to  Test-2
              move  Enter-Date-Op     to  Test-Op
              perform  Test-Num
              if    A-False
                    go to  Read-Loop.
*>
     perform  Listing.
     go       to Read-Loop.
*>
 Test-Num.
*>*******
*>
     move     function upper-case (Test-Op) to Test-Op.
     if       Test-Op = " "
              move  1  to  Truth
       else
              move  0  to  Truth.
*>
     if       Test-Op = "L"
       and    Test-2  <  Test-1
              move  1  to  Truth.
*>
     if       Test-Op = "G"
       and    Test-2  >  Test-1
              move  1  to  Truth.
*>
     if       Test-Op = "E"
       and    Test-2  =  Test-1
              move  1  to  Truth.
*>
 Headings.
*>*******
*>
     add      1  to  a.
     move     a  to  l3-page.
     if       a not = 1
              write print-record  from  line-1 after page
              write print-record  from  line-3 after 1
              move  spaces  to  print-record
              write print-record after 1
     else
              write print-record  from  line-1 before 1
              write print-record  from  line-3 before 1
     end-if
     write    print-record  from  line-4 after 2.
     write    print-record  from  line-5 after 1.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     6 to line-cnt.
*>
 Listing.
*>******
*>
     if       line-cnt > Page-Lines
              perform Headings.
     move     WS-Sales-Key  to  l6-key.
*>
     if       customer-live
              move  "Active"  to  l6-status
     else
              move  "Dormant" to  l6-status.
*>
     move     sales-name     to  l6-name.
     move     sales-address  to  l7-address.
     inspect  l7-address  replacing  all  sl-delim  by  ",".
     if       sales-ext = spaces
              move sales-phone to l6-phone
       else
              move 1 to y
              string sales-phone delimited by "  "
                                 into l6-phone with pointer y
              add 1 to y
              if  Sales-Ext not = spaces
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
     if       line-cnt > Page-Lines - 3
              perform Headings.
*>
     write    print-record  from  line-6 after 1.
     write    print-record  from  line-7 after 1.
*>
     if       delivery-tag  >  zero
              perform  Delivery-Print.
     if       Notes-Tag > zero
              perform  Notes-Print.
*>
     move     spaces to print-record.
     write    print-record after 1.
     add      3 to line-cnt.
     if       line-cnt > Page-Lines
              perform Headings.
*>
 Delivery-Print.
*>*************
*>
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     move     "D"       to WS-Deliv-Key-Type.
*>
     perform  Delivery-Read-Indexed.        *> read delivery-file  invalid key
     if       fs-reply = 21
              move  "Record not found"  to deliv-name
                                           deliv-address.
*>
     move     "   Deliver"   to  l6-key.
     move     "y Address"    to  l6-status.
*>
     move     deliv-name     to  l6-name.
     move     deliv-address  to  l7-address.
     inspect  l7-address  replacing  all  sl-delim  by  ",".
*>
     move     spaces  to  l6-phone
                          l6-charges
                          L6-BO
                          l6-letter.
     move     zero    to  l6-limit
                          l6-credit
                          l6-discount.
*>
     write    print-record  from  line-6 after 1.
     write    print-record  from  line-7 after 1.
     add      2 to line-cnt.
*>
 Notes-Print.
     move     WS-Sales-Key to WS-Deliv-Sales-Key.
     move     "N"       to WS-Deliv-Key-Type.
     perform  Delivery-Read-Indexed.        *> read delivery-file invalid key
     if       fs-reply = 21
              move  "Record not found"  to deliv-name
                                           deliv-address.
*>
     string   "Notes: "     delimited by size
              deliv-address delimited by size into l7-address.
     write    print-record from line-7 after 1.
     add      1 to line-cnt.
*>
 End-Report.
*>*********
*>
 main-exit.   exit section.
*>********    ****
*>
 Report-Heading-Setup  section.
*>============================
*>
     move     1  to  y.
     move     spaces  to  l3-report.
*>
     if       Status-In = spaces  and  Credit-Op
                      and  Invoice-Op   and  Average-Op
                      and  Overdue-Op   and  Customer-In
              string  "All"  delimited by size
                               into  l3-report  with  pointer  y
     else
              string  "Matched"  delimited by size
                               into  l3-report  with  pointer  y.
*>
     add      1  to  y.
*>
     if       Status-In = "L"
              string  "Live"    delimited by size
                               into  l3-report  with  pointer  y.
     if       Status-In = "D"
              string  "Dormant" delimited by size
                               into  l3-report  with  pointer  y.
*>
     add      1  to  y.
*>
     if       Credit-Op = "L"
              move    "< "  to  cr-operand.
     if       Credit-Op = "G"
              move    "> "   to  cr-operand.
     if       Credit-Op = "E"
              move    "= "  to  cr-operand.
*>
     if       Credit-Op not = space
              move  Credit-In  to  cr-days
              string  credit-heading  delimited by size
                               into  l3-report  with  pointer  y.
*>
     add      1  to  y.
*>
     if       Invoice-Op = "L"
              move    "< "  to  act-operand.
     if       Invoice-Op = "G"
              move    "> "   to  act-operand.
     if       Invoice-Op = "E"
              move    "= "  to  act-operand.
*>
     if       Invoice-Op not = space
              move  Invoice-In  to  act-days
              string  active-heading  delimited by size
                               into  l3-report  with  pointer  y.
*>
     add      1  to  y.
*>
     if       Average-Op = "L"
              move    "< "  to  av-operand.
     if       Average-Op = "G"
              move    "> "   to  av-operand.
     if       Average-Op = "E"
              move    "= "  to  av-operand.
*>
     if       Average-Op not = space
              move  Average-In  to  av-days
              string  average-heading  delimited by size
                               into  l3-report  with  pointer  y.
*>
     add      1  to  y.
*>
     if       Overdue-Op = "L"
              move    "< "  to  ov-operand.
     if       Overdue-Op = "G"
              move    "> "   to  ov-operand.
     if       Overdue-Op = "E"
              move    "= "  to  ov-operand.
*>
     if       Overdue-Op not = space
              move  Overdue-In  to  ov-days
              string  overdue-heading delimited by size
                               into  l3-report  with  pointer  y.
*>
     add      1  to  y.
*>
     if       Enter-Date-Op = "L"
              move    "< "  to  ed-operand.
     if       Enter-Date-Op = "G"
              move    "> "   to  ed-operand.
     if       Enter-Date-Op = "E"
              move    "= "  to  ed-operand.
*>
     if       Enter-Date-Op not = space
              move  Enter-Date-In  to  ed-date
              string  enter-date-heading  delimited by size
                               into  l3-report  with  pointer  y.
*>
     add      1  to  y.
*>
     if       Cust-In not = spaces
              string  " Keys Matching - " delimited by size
                      Cust-In             delimited by size
                               into  l3-report  with  pointer  y.
*>
 main-exit.   exit section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>****************************************************
*> Input:   ws-Test-date
*> output:  u-date/ws-date as uk date format
*>          u-bin not zero if valid date
*>
     move     ws-Test-date to ws-date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-Test-date.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz050-Test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to ws-date.  *> swap Intl to UK form
     move     ws-Test-date (1:4) to ws-Year.
     move     ws-Test-date (6:2) to ws-Month.
     move     ws-Test-date (9:2) to ws-Days.
*>
 zz050-Test-date.
     move     ws-date to u-date.
     move     zero to u-bin.
     perform  maps04.
*>
 zz050-exit.
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
