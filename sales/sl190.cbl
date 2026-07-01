       >>source free
*>**************************************************************
*>                                                             *
*>      D U N N I N G   L E T T E R   P R O D U C T I O N      *
*>                                                             *
*>   This program produce 3 files for printing or passing to   *
*>    another program for printing as required                 *
*>    When originally written it created a file that was       *
*>     passed to MS Word in a sort/merge mail process that     *
*>       added the text for each letter type per customer      *
*>        record for letters 1, 2 & 3                          *
*>**************************************************************
*> NOTE: That sl110, 120 & 190 are similar.
*>  09/02/17 :-
*>   Set to use the sorted file if nothing else it will sort the
*>    letter reporting into Cust, date, invoice & type order.
*>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<*
*>    NEED TO TEST linking into LibreOffice Writer          <<<*<<
*>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<*
*> NOTE:  This program prints out the UK pound symbol so if    *
*>        you use something else change it to your symbol.     *
*>        See line starting with 'currency sign' (line 143)    *
*>  Also change the value at Locale-Currency-Symbol & around
*>    line 267 as:
 *>         05 lf-os        pic £(6)9.99.   *> 195
*>=============================================================*
*>                                                             *
*> If you are going to use comma delimited output then remark  *
*>  out line starting : go to Setup-comma-delimits-done        *
*>  if you need quoted fields                                  *
*>                                                             *
*>   This is on or around line 656.                            *
*>                                                             *
*>**************************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl190.
*>*
*>    Author.             V B Coen, FBCS, FIDM, FIDPM,
*>                        For Applewood Computers.
*>*
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Letter Production.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called modules.     maps04
*>                        acas012  ->
*>                         salesMT
*>                        acas019  ->
*>                         otm3MT.     ONLY for Table processing.
*>**
*>    Error messages used.
*>                        SL005.
*>                        SL120.
*>**
*>    Changes.
*> 31/03/83 Vbc - Correct Name, Address, Amount Of Letter.
*> 08/04/83 Vbc - Stop Closed Records Being Used For Letters.
*>                 Use All 3 Letter Files At Once.
*> 26/10/83 Vbc - Cis Cobol Conversion to WorkBench.
*> 01/03/84 Vbc - Support Sales-Unapplied In Read-Sales Routine.
*> 11/05/84 Vbc - Support For Indexed Openitm File.
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 25/11/11 vbc - .01 Error msgs to SLnnn.Support for dates other than UK
*> 08/12/11 vbc - .02 Support for path+filenames BUT letter files are to local directory.
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .03 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 27/02/12 vbc - .04 Changed use of array-k' in 'sales-key to WS-Sales-Key (y:1) for SQL processing.
*> 25/03/12 vbc - .05 Added quotes around all non-numerics, if word processor needs it.
*> 24/10/16 vbc - .06 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*>                    Merged error msgs in SL lists from maps99.
*> 21/01/17 vbc - .07 Extra comments for comma delimited fields
*>                    Fixed literal name holding the Currency symbol.
*> 25/01/17 vbc       Dry testing completed.
*> 09/02/17 vbc - .08 Updated FD/WS for 019 and replaced cobol verbs
*>                    for access to FH/DALs when not using Cobol files.
*>                    Sort requirements removed (sl115) when processing
*>                    RDB tables as the sort step removed in place of
*>                    read Table by Order.
*>                    Note: When using RDB tables there is no sorting,
*>                    Data is from selecting by order.
*> 14/04/17 vbc - .09 inspect for both dollar,  pound and euro.
*> 05/04/23 VBC - .10 MISSING MOVE AFTER ACCEPTING DATE err, why finger probs ?
*> 07/04/23 vbc - .11 Added extra code to get and save system record
*> 25/06/23 vbc -     Added section zz080-Issue-Email but not coded nor has vars setup.
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
 configuration section.
*> copy "envdiv.cob".
*>
 special-names.
*>************
*> CHANGE THIS TO YOUR CURRENCY or if dollars remark out,
*>  but also see value for Locale-Currency-Symbol in WS
*>   as this one is used instead of the one below & around line 250 as:
 *>         05 lf-os        pic £(6)9.99.   *> 195
*> replacing the "£" symbol with yours such as "$"
*>
*>
     currency sign '£'.
*>
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
*> copy "selsl.cob".
*> copy "seloi3.cob".
 copy "slselois.cob".
*>
     select  letter-file-1     assign        file-21-a,
                               organization  line sequential.
     select  letter-file-2     assign        file-21-b,
                               organization  line sequential.
     select  letter-file-3     assign        file-21-c,
                               organization  line sequential.

 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdsl.cob".
*> copy "fdoi3.cob".
 copy "slfdois.cob".
*>
 fd  letter-file-1.
*>
 01  letter-record-1     pic x(208).
*>
 fd  letter-file-2.
*>
 01  letter-record-2     pic x(208).
*>
 fd  letter-file-3.
*>
 01  letter-record-3     pic x(208).
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15) value "SL190 (3.3.00)".
*>
 77  Locale-Currency-Symbol pic x  value "£".  *> Change this for yours.
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*> copy "wsoi.cob".
 copy "slwsoi3.cob".
 copy "wssl.cob".
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
 77  si-date              binary-long          value zero.
*>
 01  ws-amount-screen-display.
     03  ws-poundsd      pic 9(6).
     03  ws-period       pic x     value ".".
     03  ws-penced       pic v99.
 01  ws-amount-screen-accept redefines ws-amount-screen-display.
     03  ws-pound        pic 9(6).
     03  filler          pic x.
     03  ws-pence        pic v99.
*>
 01  ws-amount-work.
     03  amt-wk-pds      pic 9(6).
     03  amt-wk-pence    pic v99.
 01  ws-amount-ok redefines ws-amount-work.
     03  amt-ok          pic 9(6)v99.
*>
 01  letter-work.
     03  lf-name         pic x(34).
     03  filler          pic x     value ",".
     03  lf-line1        pic x(34).
     03  filler          pic x     value ",".
     03  lf-line2        pic x(34).
     03  filler          pic x     value ",".
     03  lf-line3        pic x(34).
     03  filler          pic x     value ",".
     03  lf-line4        pic x(34).
     03  filler          pic x     value ",".
     03  lf-account      pic x(9).       *> 184
     03  filler          pic x     value ",".
     03  lf-os2.    *> Don't worry about this if your currently is pounds or dollars
*> see code at :  letter-out  where it is replaced by dollar or pound symbols.
*> If you use another one replace the test for pounds for your one.
*>
*>         05  lf-os       pic z(6)9.99.   *> 195
*>         05  lf-os       pic $(6)9.99.   *> 195  *> if using dollars uncommend this line
         05 lf-os        pic £(6)9.99.   *> 195       and comment out this one
     03  filler          pic x     value ",".      *>  Or change above line for your currency
     03  lf-date         pic x(12).       *> 208
*>
 01  letter-work2        pic x(208).
*>
 01  ws-data.
     03  letter-nos      pic 999      value zero.
     03  store-work      pic 9(6)v99  value zero.
     03  a               pic 99.
     03  b               pic 99.
     03  y               pic 99.
     03  truth           pic 9.
       88  a-true                     value  1.
       88  a-false                    value  0.
     03  address-A       pic x(96).
     03  address-line    pic x(36).
     03  work-1          pic s9(6)v99.
     03  customer-in     pic x(7).
     03  filler  redefines  customer-in.
       05  array-l       pic x  occurs  7.
     03  pay-date        binary-long.
     03  pay-value       pic s9(6)v99.
     03  last-read       pic x(7)        value spaces.
     03  ws-days-1       pic 99.
     03  ws-days-2       pic 99.
     03  ws-days-3       pic 99.
     03  ws-reply        pic x           value space.
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
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
*>
 01  Error-Messages.
*> System Wide
     03  SL005           pic x(30) value "SL005 Press Return To Continue".
*> Module specific
     03  SL120           pic x(35) value "SL120 Sales Transactions Not Posted".
*>
 01  error-code          pic 999.
*>
 01  filler.
     03  file-21-a       pic x(10)       value "letter.001".
     03  file-21-b       pic x(10)       value "letter.002".
     03  file-21-c       pic x(10)       value "letter.003".
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
     if       FS-Cobol-Files-Used
              call  "CBL_CHECK_FILE_EXIST" using File-19    *> Open ITM3 file
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    display SL120   at 2301
                    display SL005   at 2401
                    accept ws-reply at 2432
                    go       to menu-exit.
*>
     display  space at 0101 with erase eos.
     display  prog-name at 0202 with erase eos foreground-color 2.
     display  "Letter Production" at 0233 with foreground-color 2.
     perform  zz070-Convert-Date.
     display  ws-date at 0271 with foreground-color 2.
*>
     open     output letter-file-1 letter-file-2 letter-file-3.
     perform  Statements.
     close    letter-file-1 letter-file-2 letter-file-3.
*>
 menu-exit.
*>********
*>
     exit     program.
*>
*>****************************************************************
*>      P R O C E D U R E S                                      *
*>****************************************************************
*>
 statements              section.
*>==============================
*>
     display  "****************************************" at 0441 with foreground-color 2.
     display  "*Date    [  /  /    ]                  *" at 0541 with foreground-color 2.
     display  "*A/C Nos   [       ]                 ***" at 0641 with foreground-color 2.
     display  "*Value  [         ]*                   *" at 0741 with foreground-color 2.
     display  "****************************************" at 0841 with foreground-color 2
*>
     display  "ESC to quit" at 0952.
 *>    go       to main-display-end.
*>
 main-display-end.
*>
     display  "Notes" at 1201 with foreground-color 2.
     display  "*****" at 1301 with foreground-color 2.
     display  " (1) - <A/C>   :  A/Cs To Match For Printing" at 1501 with foreground-color 2.
     display  " (2) - <Value> :  Minimum O/S To Print" at 1601   with foreground-color 2.
*>
 date-input.
*>*********
*>
     display  ws-date at 0551 with foreground-color 3.
     accept   ws-date at 0551 with foreground-color 3 update.

     if       ws-date = spaces
              go to main-exit.
     if       cob-crt-status = COB-SCR-ESC
              go to main-exit.
     display  space at 0952 with erase eol.  *> remove msg for ESC to quit
     move     ws-date to ws-test-date.
     perform  zz050-Validate-Date.
     if       u-bin  equal  zero
              go to  date-input.
     move     u-bin   to  pay-date.
*>
 customer-input.
*>*************
*>
     accept   customer-in at 0653 with foreground-color 3.
     move     function upper-case (customer-in) to customer-in.
*>
 value-input.
*>**********
*>
     move     0750 to curs.
     perform  accept-money.
     move     amt-ok to pay-value.
*>
 amounts-input.
*>************
*>
*> Here we need to read the system file (in case of any changes)
*>
     perform  zz100-Get-System-Record.   *> refresh rec 1
     move     sl-days-1 to ws-days-1.
     move     sl-days-2 to ws-days-2.
     move     sl-days-3 to ws-days-3.
     display "Low Date    - [  ]" at 1820 with foreground-color 2.
     display "Medium Date - [  ]" at 1920 with foreground-color 2.
     display "High Date   - [  ]" at 2020 with foreground-color 2.
     display  ws-days-1 at 1835 with foreground-color 2.
     display  ws-days-2 at 1935 with foreground-color 2.
     display  ws-days-3 at 2035 with foreground-color 2.
*>
     accept   ws-days-1 at 1835 with foreground-color 3.
     accept   ws-days-2 at 1935 with foreground-color 3.
     accept   ws-days-3 at 2035 with foreground-color 3.
     move     ws-days-1 to sl-days-1.
     move     ws-days-2 to sl-days-2.
     move     ws-days-3 to sl-days-3.
*>
*> Here we need to rewrite the system file for changes of sl-days-1,2 & 3.
*>
     perform  zz110-Update-System-Rec.  *> save changes
*>
     if       FS-Cobol-Files-Used
              open     input  open-item-file-s
              if       fs-reply not = zero
                       close   open-item-file-s
                       open output  open-item-file-s
                       close   open-item-file-s
                       open     input  open-item-file-s
              end-if
     else
              perform  OTM3-Open-Input
     end-if
     perform  Sales-Open-Input.
*>
 read-sales.
*>*********
*>
     perform  Sales-Read-Next.           *> read sales-file next record at end
     if       fs-reply = 10
              go to  main-end.
*>
     if       not dunning-letters
              go to read-sales.
*>
     subtract sales-unapplied from sales-current.
*>
     if       sales-current < 0.01   *> Do not process amount below this (0.01)
              go to read-sales.      *> change this to stop reminders for small amounts
*>
     if       pay-value not = zero
        and   sales-current  <  pay-value
              go to  read-sales.
*>
     if       customer-in  not = spaces
              move  1  to  truth
              perform test-array varying y from 1 by 1   until y > 6
              if    a-false
                    go to  read-sales.
*>
     move     sales-address  to  address-A.
     move     spaces to address-line.
*>
     move     1  to  a.
     unstring address-A  delimited  by  sl-delim into  address-line count a pointer  a.
     move     address-line  to  lf-line1.
*>
     move     spaces  to  address-line.
     unstring address-A  delimited  by  sl-delim into  address-line count a pointer  a.
     move     address-line  to  lf-line2.
*>
     move     spaces  to  address-line.
     unstring address-A  delimited  by  sl-delim into  address-line count a pointer  a.
     move     address-line  to  lf-line3.
*>
     move     spaces to address-line.
     unstring address-A  delimited  by  sl-delim into  address-line count a pointer  a.
     move     address-line  to  lf-line4.
*>
 read-open-item.
*>*************
*>
*> Here we have two choices
*> 1: If using files (Cobol), work via the sort file
*>    to help select records then read the Sales file.
*> 2: If using RDB tables, then process via ORDERED OTM3
*>     table  therefore only work with the one table & row
*>      [instead of 2 files].
*>
*> This way we get rid of a sort for Table processing as all done in RDBMS.
*>
     if       last-read = spaces
              if       NOT FS-Cobol-Files-Used
                       perform OTM3-Read-Next-Sorted-By-Cust  *> not really it is ordered
                       if      fs-reply not = zero     *> = 10   cust,date,inv,type
                               perform  End-Statement
                               perform OTM3-Close
                               go to Main-End
                       end-if
                       go to Read-Loop-Tests
              end-if
              read  open-item-file-s  record at end
                    perform  End-Statement
                    close    open-item-file-s
                    go to    Main-End
     end-if
*>
     move     open-item-record-s  to  oi-header.
*>
 Read-Loop-Tests.
     move     oi-customer  to  last-read.
*>
     if       last-read  >  WS-Sales-Key
              go to  end-statement.
*>
     if       last-read  not =  WS-Sales-Key
              move  spaces  to  last-read
              go to  read-open-item.
*>
*> Here then o-i transaction is for this customer.
*>
     if       oi-type  not = 2                   *> not invoices / account?
              move  spaces  to  last-read
              go to  read-open-item.
*>
     if       s-closed
              move spaces to last-read
              go to read-open-item.
*>
     subtract oi-date  from  pay-date  giving  work-1.
*>
     if       work-1 >  store-work
              move  work-1  to  store-work
              if    oi-date  >  si-date
                    move  oi-date  to  si-date.
*>
*> Loop back for next item....
*>
     move     spaces  to  last-read.
     go       to read-open-item.
*>
*> Can only get here at the end of a statement.
*>
 end-statement.
*>************
*>
*>
*> Loop time.......get another punter.
*>
     if       store-work not < sl-days-1
              perform  letter-out.
*>
     move     zero  to  store-work  si-date.
*>
 end-statement-end.
*>
     go       to read-sales.
*>
 accept-money.
*>-----------
*>
     move     zero to ws-poundsd amt-ok ws-penced.
     display  ws-amount-screen-display at curs.
     accept   ws-amount-screen-accept at curs.
     move     ws-pound to amt-wk-pds.
     move     ws-pence to amt-wk-pence.
*>
 main-end.
*>*******
*>
     if       FS-Cobol-Files-Used             *> Make it a null file
              open  output open-item-file-s
              close open-item-file-s
     end-if
     perform  Sales-Close.
*>
 main-exit.   exit section.
*>********    ****
*>
 test-array              section.
*>==============================
*>
     if       a-false
              next sentence
     else
      if      array-l (y)  equal  space
              next sentence
      else
*>              if  array-l (y)  not = array-k (y)
             if     array-l (y) not = WS-Sales-Key (y:1)
                  move  zero  to  truth.
*>
 main-exit.   exit section.
*>********    ****
*>
 letter-out               section.
*>===============================
*>
*>******************************************************************
*> WARNING:                                                        *
*>  This routine processes a fixed format comma delimited file     *
*>  that does NOT use "" around alpha data eg, name and address    *
*>                 modify it if needed                             *
*>******************************************************************
*>
     if       store-work < sl-days-2
              move  1  to  letter-nos
     else
              if    store-work  <  sl-days-3
                    move  2  to  letter-nos
      else
                    move  3  to  letter-nos.
*>
     move     sales-name  to  lf-name.
     move     WS-Sales-Key  to  lf-account.
     move     sales-current  to  lf-os.
     inspect  lf-name replacing all "," by ";".     *> Get rid of commas as we
     inspect  lf-line1 replacing all "," by ";".    *>  may not be using quotes
     inspect  lf-line2 replacing all "," by ";".
     inspect  lf-line3 replacing all "," by ";".
     inspect  lf-line4 replacing all "," by ";".
     inspect  lf-os2   replacing first "$"          *> covers for dollar
              by Locale-Currency-Symbol.
     inspect  lf-os2   replacing first "£"          *> covers for UK pound
              by Locale-Currency-Symbol.
*>
*> Change currency symbol if needed in literal above if not pound or dollar
*>
     move     si-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     ws-date  to  lf-date.
*>
     go       to Setup-comma-delimits-done.
*>
*>  Comment above line if comma delimited records need quotes around
*>    all non-numerics
*>
 Setup-comma-delimits.
    move      1 to b.
    move      spaces to letter-work2.
    string    quote         delimited by size
              lf-name       delimited by "  "
              quote         delimited by size
              ","           delimited by size
              quote         delimited by size
              lf-line1      delimited by "  "
              quote         delimited by size
              ","           delimited by size
              quote         delimited by size
              lf-line2      delimited by "  "
              quote         delimited by size
              ","           delimited by size
              quote         delimited by size
              lf-line3      delimited by "  "
              quote         delimited by size
              ","           delimited by size
              quote         delimited by size
              lf-line4      delimited by "  "
              quote         delimited by size
              ","           delimited by size
              quote         delimited by size
              WS-Sales-Key     delimited by size
              quote         delimited by size
              ","           delimited by size
              lf-os2        delimited by size         *> this can produce leading spaces
              quote         delimited by size
              ","           delimited by size
              quote         delimited by size
              ws-date       delimited by size
              quote         delimited by size  into letter-work2 pointer b
     end-string
     move     letter-work2 to letter-work.
*>
 Setup-comma-delimits-done.
*>
*>
     if       letter-nos = 1
              write letter-record-1  from  letter-work
     else
      if      letter-nos = 2
              write letter-record-2  from  letter-work
      else
              write letter-record-3  from  letter-work.
*>
 main-exit.   exit section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>****************************************************
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
 zz080-Issue-Email  section.
*>*************************
*>
*> This one for mailx - the variables not created !
*>
  *>   STRING   "echo "
  *>            FUNCTION TRIM (mail-body TRAILING)
  *>            " | mailx -r "
  *>            FUNCTION TRIM (mail-from-address TRAILING)
  *>            " -s "
  *>            FUNCTION TRIM (mail-subject TRAILING)
  *>            " -a "
  *>            FUNCTION TRIM (mail-attachment-filename TRAILING)
  *>            " "
  *>            FUNCTION TRIM (mail-to-address TRAILING)
  *>            x"00" DELIMITED BY SIZE
  *>                   INTO mail-command.
*>
 zz080-Exit.  exit section.
*>
 zz100-Get-System-Record   section.
*>********************************
*>
 zz100-Open-System.                *> First get system param cobol file
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.
     if       fs-reply not = zero
 *>             perform System-Close    *> SHOULDNT THIS BE USED ?
              move    "sys002" to ws-called    *> create param file by requested info from user
              call    ws-called using ws-calling-data file-defs
              perform  System-Open        *>  ditto
     end-if.
*>
 zz100-Get-Rec-1.
     move     zeros to File-System-Used         *> again in case RDB setup
                       File-Duplicates-In-Use.  *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Read-Indexed.        *> Read Cobol file params
     if       fs-reply not = zero          *> should NOT happen as done in
              perform System-Close          *> open-system
              move    "sys002" to ws-called    *> create param file by requested info from user
              call    ws-called using ws-calling-data file-defs
              perform System-Open
              go to zz100-Get-Rec-1
     end-if.
*>
 zz100-exit.
     exit     section.
*>
 zz110-Update-System-Rec   section.
*>********************************
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
 zz110-exit.
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
