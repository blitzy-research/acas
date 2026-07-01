       >>source free
*>
*> THIS PROGRAM NEEDS TO BE TESTED DUE MAJOR CHANGES.
*>
*>     THIS IS FOR PICKING / DELIVERY NOTES
*>  THIS PROGRAM MAY NEED TO BE MODIFIED TO SUIT YOUR STATIONERY
*>            REQUIREMENTS
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>    Do so in conjunction with SL930 Invoice Print.
*>      and ensure testing with stationery of plain paper
*>
*> PRODUCES TITLES ETC ON EXPECTED PLAIN PAPER TO A INKJET or
*> LASER type printer.
*>
*>  This printer MUST be set up as SINGLE SIDED PRINTING even
*>  though the lpr command is set to that, for some printers it is ignored.
*>
*> It is best to have one Cups spool setting for printers used in portrait mode
*>   preset to single sided even if you have the same printer defined as double.
*>  while the other is set as duplex (double sided) printing.
*>
*> THE Above said, this program should not need any changes as it would notmally
*>  use plain paper only HOW EVER you may want to produce TWO copies of each
*>   document as it is currently set for only one.
*>
*>*****************************************************************
*>                                                                *
*>            DELIVERY NOTES and PICKING LIST PRINT               *
*>                                                                *
*>       SUPPLIED IN SOURCE FOR MODIFICATION BY CUSTOMER          *
*>                                                                *
*>  Print includes stock item storage locations.                  *
*>                                                                *
*> Applewood Computers offers a service to change this module     *
*>   along with the Invoicing, Statement print modules            *
*>   to meet your invoicing requirements.                         *
*>  currently set to spool to secondary (lpt3) printer & assumes  *
*>  a matrix printer using preprinted stationery or a laser using *
*>        a preloaded template                                    *
*>                                                                *
*>  This printer would normally be in the Dispatch/packing room   *
*>     as printer lpt-3.                                          *
*>*****************************************************************
*> This module does NOT print amounts only products, quantities   *
*>  and Locations.	                                               *
*>*****************************************************************
*>  WARNING:  THIS MODULE MUST BE RUN BEFORE INVOICE PRINTING     *
*>            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^     *
*>         as the invoice print updates the invoice records       *
*>         and hence this program will NOT find records           *
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  *
*>*****************************************************************
*>  Adobe Reader API Code and the Invoicing                       *
*>  modules has been removed as they are non-free code and users  *
*>  have to purchase it and the reader/Forms programs from Adobe. *
*>  I will try and relook at this as well as links to LibreOffice *
*>  that do a similar job in producing stylised documents instead *
*>  based on template forms etc when time is available.           *
*>*****************************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl950.
*>**
*>    Author.             V B Coen, FBCS, FIDM, FIDPM, 28/10/83 but taken from
*>                                                     Invoice print.
*>                        For Applewood Computers.
*>*
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Delivery and Packing list print.
*>**
*>    Version.            See Prog-Name In Ws.
*>
*>    Called Modules.     Maps04.
*>                        acas011  ->
*>                         stockMT.
*>                        acas012  ->       (Sales)
*>                         salesMT.
*>                        acas014  ->       (Delivery)
*>                         deliveryMT.
*>                        acas016  ->
*>                         invoiceMT.
*>**
*>    Error messages used.  These messages are remarked out, as page align is off.
*>                          You will need them if using continuous stationary.
*>                        SL003 hit return ...
*>                        SL200 Form alignment msg.
*>**
*> Changes
*> 24/03/12 vbc - .01 Migration to Open Cobol v3.01.nn and code added to match sl930.
*> 15/05/13 vbc - .02 Changed printer to prt-2 from prt-1 and removed double sided spooling.
*> 19/05/13 vbc - .03 Removed analysis file process and amounts etc as picking dont need them
*>                    Inserted company headings if needed (set by flag in parameter file, well
*>                    it will be when sys002 is changed).Update invoice record after running by
*>                    setting sih-status-P true.
*> 20/05/13 vbc - .04 Tidied up headings & added time to headings.
*> 30/05/13 vbc - .05 More tidying to match sl930 invoicing along with an total Item count.
*>                    Checked that all non-free API code from Adobe Reader is removed.
*> 24/10/16 vbc - .06 ALL programs now using wsnames.cob in copybooks
*> 30/10/16 vbc - .07 Support for RDB on  Stock tables
*>                    instead of cobol files
*>                    using acas011. Update version to v3.02
*>                      more to do, have renamed the calls for acas011
*>                      Stock to reduce any coding errors
*>                      as there will be a lot of them in this module.
*>                    Replace usage of File-Status/es to use call to
*>                    CBL_CHECK_FILE_EXIST - Now removed (08).
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 19/01/17 vbc - .08 Added remaining FH processing but excluding invoice.
*>                    Removed usage of maps99 - was for unused anal file.
*> 20/01/17 vbc -     Removed test for 'p' in sih-status-P & replace
*>                    literal Invoice for Picking etc. Remove references
*>                    to invoice-let as redundant.
*> 25/01/17 vbc       Dry testing completed.
*> 11/02/17 vbc - .09 Updated FD/WS for 016,019 and replaced cobol verbs
*>                    for access to FH/DALs.
*> 18/04/17 vbc - .10 Updated to use Invoice-Read-Next-Header where only the
*>                    Header is wanted (if test = zero then read-next.
*>                    Cuts down unneeded reads of table. FH is still the same.
*> 18/03/18 vbc - .11 With the addition of parm field SL-Invoice-Lines & in sys002
*>                    print inv programs will use it instead of a fixed 15/25.
*> 04/12/18 vbc - .12 Compiler doesn't like inline performs without an imperative
*>                    statement - changed to a continue.
*>                    Uses Company name/addr if SL-Comp-Pick = Y.
*> 19/02/23 vbc - .13 Change printline to 84 for mex size. sstop blank lines on
*>                    HP 7305.
*> 06/03/23 vbc - .14 In zz080-Setup-Company-Details if not spaces added VAT data to
*>                    Line-Company-Details8 and in headings-1 print it out as
*>                    last line in company name address details - hopefully centered.
*>                    Also done in sl930.
*> 07/03/23 vbc - .15 lpr copybook print-spool-command-p-dispatch.cob changed
*>                    as single-sided  Also applies to sl930 by using
*>                    print-spool-command-p-dispatch-2.cob for 2 copies, or -3
*>                    print-spool-command-p-dispatch-3.cob
*>                    Adjust size for printer FD to actual requirements.
*> 27/06/23 vbc - .16 Company heading changed to use C$JUSTIFY in ZZ090
*>                    same for sl930.
*> 07/08/23 vbc - .17 fix in zz090-Setup-Company-Details bland addr lines
*>                    within address. for both sl930 & sl950.
*>                    Adjust line-0-d less 1 char on 1st field.
*> 27/01/24 vbc - .18 Now using selprint-2.cpy and prt-3 and printing to
*>                    fit-to-page - JIC, added packed by line, replaced PSN3
*>                    by PSN. "Packed by " previously added.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 04/02/25 vbc - .19 Added WS-  to Stock-Location.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
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
 copy "selprint-2.cpy" replacing "prt-1" by "prt-3".	*> Dispatch printer
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 fd  print-file.
*>
 01  print-record            pic x(84).   *> was 102).
*>
 working-storage section.
*>----------------------
 77  prog-name               pic x(15) value "SL950 (3.3.00)".
*>
*> Change this to suite your requirements. This is set portrait, going to a
*>  different printer than normal
*>   and single sided within copybook
*>   see CUPS help on 'lpr' but change it within program not the copybook
*>
*>    WARNING print delivery/packing slips FIRST (sl950) before printing invoices.
*>       as you cannot do so after printing invoices.
*>    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
 copy "print-spool-command-invoice.cob" replacing     *>  ==PSN2== by ==PSN3==
                                                  "prt-1" by "prt-3".
*>
*> Also change for two (or more) copies per packing note or invoice,  if needed
*> I.e., one for customer, filing, sales deptartment etc, by using instead of
*> copy "print-spool-command-p-dispatch.cob" above, use
*>   copy "print-spool-command-p-dispatch-2.cob"  for two copies
*> or for three copies use
*>  copy "print-spool-command-p-dispatch-3.cob" instead of the above name.
*>

 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
                           *> was copy "wsinv.cob".
 copy "slwsinv.cob"  replacing Invoice-Line by Invoice-Lines. *> original with occ 40 for lines
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                                pic x(137).
 copy "wssl.cob".
 copy "wsdel.cob".
 copy "wsstock.cob".
*>
 *> 77  WS-Temp-Invoice-Record     pic x(140).  *> actual is 137.  NOT USED - YET.
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
*>     03  WS-Stock-Record        pic x.
*>     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
*>     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
*>     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  ws-data.
     03  test-product.
         05  filler      pic x.
             88  il-comment              value "/".
         05  filler      pic x(6).
     03  ws-reply        pic x.
     03  print-path      pic x.
     03  a               pic 99.
     03  c-check         pic 9.
         88  c-exists                    value 1.
     03  address-line    pic x(36).
     03  ws-Item-Count   pic 9(4)        value zero.
     03  i               pic 99.
     03  ii              pic 99.
     03  j               pic 99.
     03  k               pic 99.
     03  kk              pic 99.
     03  first-time      pic x           value "Y".
     03  ws-Time         pic 9(8)        value zero.
     03  h1              pic 99.  *> Co name  max 32
     03  h2              pic 99.  *> Addr 1   max 24
     03  h3              pic 99.  *> Addr 2   max 24
     03  h4              pic 99.  *> Addr 3   max 24
     03  h5              pic 99.  *> Addr 4   max 24
     03  h6              pic 99.  *> Postcode max 12
     03  h7              pic 99.  *> Country  max 24
     03  h97             binary-char.
     03  h98             binary-char.
     03  h99             binary-char.
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
*> 01  Error-Messages.
*> System Wide
*>     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
*> Module specific
*>     03  SL200          pic x(43) value "SL200 Re-Align Picking lists to Top of Form".
*>
 01  error-code          pic 999.
*>
 01  Line-Company-Details           value spaces.
     03  line-Company-Details1 pic x(91).
     03  line-Company-Details2 pic x(91).
     03  line-Company-Details3 pic x(91).
     03  line-Company-Details4 pic x(91).
     03  line-Company-Details5 pic x(91).
     03  line-Company-Details6 pic x(91).
     03  line-Company-Details7 pic x(91).
     03  line-Company-Details8 pic x(91).  *> VAT # line
*>
 01  line-0-a.
*> line 1
     03  l0-type         pic x(12).
*>
*> 01  line-0-b. NOT NEEDED
*> line 2
*>     03  l0-xs           pic x(12).
*>
 01  line-0-c.
*> line 3 - 62
     03  filler          pic x(37)       value spaces.
     03  l0-desc         pic x(25).
*>
 01  line-0-d.
*> line 5 - 84
     03  filler          pic x(17)       value spaces.
     03  l3-title        pic x(21)       value "Picking/Delivery Note".
     03  filler          pic x(18)       value spaces.
     03  filler          pic x(5)        value "Page ".
     03  l7-count-1      pic 9.
     03  filler          pic x(4)        value " of ".
     03  l7-count-2      pic 9.
     03  filler          pic x           value space.
     03  l3-date         pic x(10).
     03  filler          pic x           value space.
     03  l3-HH           pic 99.
     03  filler          pic x           value ":".
     03  l3-MM           pic 99.
*>
 01  line-0-e.
*> line 9  - 84
     03  filler          pic x(71)       value spaces.
     03  filler          pic x(5)        value "Inv: ".
     03  l3-invoice      pic z(7)9.
*>
 01  line-1.
*> line 10 - 65
*>     03  filler          pic x(05)       value spaces.
     03  l1-i-name       pic x(31).
     03  filler          pic x(4)        value spaces.
     03  l1-d-name       pic x(30).
*>
 01  line-2.
*> line 11 - 72
*>     03  filler          pic x(05)       value spaces.
     03  l2-i-line       pic x(31).
     03  filler          pic xxxx        value spaces.
     03  l2-d-line       pic x(30).
     03  filler          pic x(7)        value spaces.
*>
 01  line-3.
*> line 12 - 88 (max size)
*>     03  filler          pic x(05)       value spaces.
     03  l3-i-line       pic x(31).
     03  filler          pic xxxx        value spaces.
     03  l3-d-line       pic x(30).
     03  filler          pic x(5)        value spaces.
     03  filler          pic x(7)        value "Order:".
     03  l6-order        pic x(11).
*>
 01  line-4.
*> line 13 - 88
*>     03  filler          pic x(05)       value spaces.
     03  l4-i-line       pic x(31).
     03  filler          pic xxxx        value spaces.
     03  l4-d-line       pic x(30).
     03  filler          pic x(5)        value spaces.
     03  filler          pic x(7)        value " Ref :".
     03  l4-ref          pic x(11).
*>
 01  line-5.
*> line 14 - 84
*>     03  filler          pic x(05)       value spaces.
     03  l5-i-line       pic x(31).
     03  filler          pic xxxx        value spaces.
     03  l5-d-line       pic x(30).
     03  filler          pic x(5)        value spaces.
     03  filler          pic x(7)        value " A/C :".
     03  l6-account      pic x(7).
*>
 01  line-6.
*> line 15 - 65
*>     03  filler          pic x(05)       value spaces.
     03  l6-i-line       pic x(31).
     03  filler          pic xxxx        value spaces.
     03  l6-d-line       pic x(30).
*>
 01  line-7.
*> line 16-18 (3)
     03  filler          pic x(72)       value spaces.
*>
 01  line-7B.			*> plain invoice line heads - 82
     03  filler          pic x(11)       value "  Abrev #".
     03  filler          pic x(15)       value "Product Code".
     03  filler          pic x(34)       value "Item Description".
     03  filler          pic x(12)       value "   Qty".
     03  filler          pic x(10)       value "Location".
*>
 01  line-8    value spaces.
*> line 19-33 (15)  -  84
     03  filler          pic x(2)        value spaces.
     03  l8-Abrev        pic x(7)BB.
     03  l8-Product      pic x(13)BB.
     03  l8-Desc         pic x(32)BB.
     03  l8-qty          pic z(5)9       blank when zero.
     03  filler          pic x(6).
     03  l8-Loc          pic x(10)BB.
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
     if       full-invoicing = zero     *> Hmm, not sure about this for this program
              exit program.             *> but if no invoicing cant be using stock linked:)
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name3 to PSN.  *> was PSN3
     move     1 to File-Key-No.
     perform  zz070-Convert-Date.
     perform  zz090-Setup-Company-Details.
*>
 menu-return.
*>**********
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Delivery / Picking Note Print" at 0126 with foreground-color 2.
     display  ws-date at 0171 with foreground-color 2.
*>
     perform  Invoice-Open.
     perform  Stock-Open-Input.
     perform  Sales-Open-Input.
     perform  Delivery-Open-Input.
     open     output print-file.
*>
     if       pass-value not = 3
              go to  All-Print-start.
*>
     subtract 1  from  next-invoice  giving  invoice-nos.
     move     zero  to  item-nos.
*>
     perform  Invoice-Read-Indexed.
     if       fs-reply not = zero     *> chk if last inv. created is present.
              go to  main-end.
*>
     move     WS-Invoice-Record  to  sinvoice-header.
*>
     if       pending in sih-status
              perform  print-routine
              go to    main-end.
*>
     display  "Invoice Number - " at 0501 with foreground-color 2.
     display  sih-invoice at 0518 with foreground-color 3.
     display  "Already Produced!.....Re-Print  (Y/N) ? - [Y]" at 0601 with foreground-color 2.
*>
     move     "Y"  to  ws-reply.
     accept   ws-reply at 0644 with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
*>
     if       ws-reply = "Y"
              perform   print-routine.
*>
     display  " " at 0501 with erase eol.
     display  " " at 0601 with erase eol.
*>
     go       to main-end.
*>
 All-Print-start.
*>**************
*>
     display  "Print Or Re-Print.............  (P/R) ? - [P]" at 0701 with foreground-color 2.
     move     "P"  to  print-path
     accept   print-path at 0744 with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
*>
     if       print-path = "R"
              go to  All-Print-get-inv.
*>
 amend-request.
*>
     move     "N" to ws-reply.
     display  "Any Amended Invoices In This Batch? [N]" at 0901 with foreground-color 2.
     accept   ws-reply at 0938 with foreground-color 6 update UPPER.
     if       ws-reply = "Y"
              move zeros to first-sl-inv item-nos
              go to All-Print.
     if       ws-reply not = "N"
              go to amend-request.
*>
     if       first-sl-inv = zero
              go to  All-Print.
*>
     move     first-sl-inv  to  invoice-nos.
*>
 All-Print-go.
*>
     move     zero  to  first-sl-inv  item-nos.
*>
     move     1 to File-Key-No.
     set      fn-Not-Less-Than to true.
     perform  Invoice-Start.
*>
 All-Print.
*>********
*>
     perform  Invoice-Read-Next-Header.
     if       fs-reply = 10
              go to  main-end.
*>
     if       item-nos not = zero	*> find headers
              go to  All-Print.
*>
     move     WS-Invoice-Record  to  sinvoice-header.
*>
     if       sih-lines = zero and
              sapplied
              go to All-Print.
*>
     if       sih-status-P = "P"		*> Pick list printed
              go to All-Print.
     if       pending in sih-status		*> Invoices not yet printed but pick lists could have been !!!!
              perform  print-routine
              go to    All-Print.
*>
     if       print-path = "P"
              go to  All-Print.
*>
     if       sih-type > 2      *> ONLY print for invoices and receipts (prepaids)
              go to All-Print.
*>
*> Also the tests below really should be skipped
*>  as inv. printing is not relevant to pick lists BUT a reprint
*>          might be needed for amended invoices.
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
     display  "Invoice Number - " at 1101 with foreground-color 2.
     display  sih-invoice at 1118 with foreground-color 3.
     display  "Already Produced!.....Re-Print  (Y/N) ? - [Y]" at 1201 with foreground-color 2.
*>
     move     "Y"  to  ws-reply.
     accept   ws-reply at 1244 with foreground-color 6.
     move     function upper-case (ws-reply) to ws-reply.
*>
     if       ws-reply = "Y"
              perform   print-routine.
*>
     display  " " at 1101 with erase eol.
     display  " " at 1201 with erase eol.
*>
 All-Print-more.
*>
     display  "More To Print? [Y]" at 1101 with foreground-color 2.
     move     "Y" to ws-reply.
     accept   ws-reply at 1117 with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
     if       ws-reply = "N"
              go to main-end.
     if       ws-reply = "Y"
              go to All-Print-get-inv.
*>
     go       to All-Print-more.
*>
 All-Print-get-inv.
*>
     display  " " at 1301 with erase eol.
     move     zero to invoice-nos.
     display  "Give Lowest Invoice No. [        ]" at 1301 with foreground-color 2.
     accept   invoice-nos at 1326 with foreground-color 3 update.
     go       to All-Print-go.
*>
 main-end.
*>*******
*>
     perform  Invoice-Close.
     perform  Stock-Close.
     perform  Sales-Close.
     perform  Delivery-Close.
     close    print-file.
     call     "SYSTEM" using print-report.
*>
*>     if       pass-value = 3
*>              move 1 to s-flag-i.
     exit     program.
*>
 print-routine           section.
*>==============================
*>
     move     zero to ws-Item-Count.
     move     1  to  i.
     perform  sih-lines times
              perform  Invoice-Read-Next
              if       fs-reply = 10
                       exit perform
              end-if
              if   item-nos = zero
                   exit perform
              end-if
              move WS-Invoice-Record to Invoice-Lines (i)
              if   sil-type (i) = "D"
                   exit perform
              end-if
              add  1  to  i
     end-perform
*>
     subtract 1  from  i.
     move     spaces  to  line-0-a line-0-c.
*>
     subtract 1 from i giving ii.
     if       ii = 0
              move 1 to ii.
     divide   ii by  SL-Invoice-Lines   giving  l7-count-2.  *> was 15
     add      1  to  l7-count-2.
     move     1  to  l7-count-1.
*>
*>     if       sih-type = 2		*> Do not know why this here as it bypasses other if tests
*>              go to  get-customer.
*>
     if       sih-type = 1
              move  "Receipt Pick"  to l0-type
     else
      if      sih-type = 2
              move  "Invoice Pick"  to l0-type.
*>
 get-customer.
*>***********
*>
     move     1 to File-Key-No.
     move     sih-customer  to  WS-Sales-Key.
     perform  Sales-Read-Indexed.
*>
     if       delivery-tag  >  zero
              move  "D"          to WS-Deliv-Key-Type
              move  WS-Sales-Key to WS-Deliv-Sales-Key
              perform  Delivery-Read-Indexed.
*>
     move     spaces to l1-i-name l1-d-name l2-i-line  l2-d-line
                        l3-i-line  l3-d-line l4-i-line  l4-d-line
                        l5-i-line  l5-d-line l6-i-line  l6-d-line.
*>
     move     sales-name  to  l1-i-name.
*>
     move     1  to  a.
     unstring sales-address delimited by sl-delim into  l2-i-line count a  pointer a.
     unstring sales-address delimited by sl-delim into  l3-i-line count a  pointer a.
     unstring sales-address delimited by sl-delim into  l4-i-line count a  pointer a.
     unstring sales-address delimited by sl-delim into  l5-i-line count a  pointer a.
     unstring sales-address delimited by sl-delim into  l6-i-line          pointer a.
*>
     if       delivery-tag = zero
              go to  heading-details.
*>
     move     deliv-name  to  l1-d-name.
*>
     move     1  to  a.
     unstring deliv-address  delimited by sl-delim into  l2-d-line  count a  pointer a.
     unstring deliv-address  delimited by sl-delim into  l3-d-line  count a  pointer a.
     unstring deliv-address  delimited by sl-delim into  l4-d-line  count a  pointer a.
     unstring deliv-address  delimited by sl-delim into  l5-d-line  count a  pointer a.
     unstring deliv-address  delimited by sl-delim into  l6-d-line           pointer a.
*>
 heading-details.
*>**************
*>
     move     sih-invoice  to  l3-invoice.
*>
     move     sih-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     ws-date  to  l3-date.
*>
     move     sih-customer  to l6-account.
     move     sih-ref       to l4-ref.
     move     sih-order     to l6-order.
*>
     perform  headings-1.
*>
     move     1  to k.
     move     SL-Invoice-Lines to j.   *> was 15 then 25 to  j.  matrix values with sub &
*>                                        totals etc lets try 10 more
*>     move     25 to j.               *> 15  to  j.  matrix values with sub
*>                                       & totals etc lets try 10 more
*>					   as should fit a page  - TEST
 loop.
*>****
*>
     move     sil-product (k) to test-product.
     if       il-comment
              move spaces to line-8.
*>
     if       i-level-2
              move  sil-description (k) to l8-desc.	*> updated by stock data if linked
*>
     if       il-comment
              go to print-bypass.
*>
     if       i-level-2			                                    *> Do basics
              move  sil-qty (k)         to l8-qty
              add   sil-qty (k)         to ws-Item-Count		    *> track no. of items
              move  sil-product (k)     to l8-product
                                           WS-Stock-Key
              if    SL-Stock-Link = "Y"
*>                    read  Stock-File record key WS-Stock-Key invalid key  *> now for the bonus ball !
                    move 1 to File-Key-No
                    perform Stock-Read-Indexed
                    if      FS-Reply = 21
                            move sil-product (k) to WS-Stock-Abrev-Key
                            move 2 to File-Key-No
                            perform Stock-Read-Indexed
                            if      FS-Reply = 21
                                    move spaces to WS-Stock-Key
                            end-if    *> end-read
                    end-if       *> end-read
                    if   WS-Stock-Key not = spaces		   *> Stock in use and rec found
                         move WS-Stock-Key       to l8-Product
                         move WS-Stock-Abrev-Key to l8-Abrev
                         move WS-Stock-Location  to l8-Loc
                         move WS-Stock-Desc      to l8-Desc
                    end-if
              end-if
     end-if.
*>
 print-bypass.
*>
     write    print-record  from  line-8 after 1.
     add      1  to  k.
*>
     if       k  >  i		                            *> End of invoice
*>              compute  k = ((l7-count-2 * 25)  -  i) + 2	*> was 15
              compute  k = ((l7-count-2 * SL-Invoice-Lines) - i) + 2        *> was 15 then 25
              go to  total-print-2.
*>
     if       k  >  j
              move  k  to  kk
              move  2  to  k
*>              add  25 to j					*> 15  to  j
              add  SL-Invoice-Lines to j                        *> 15 then 25 to  j
              add  1   to  l7-count-1
              move kk  to  k
*>              move  spaces  to  print-record         *> THESE 2 NOT NEED FOR NON MATRIX
*>              write  print-record  after 13  lines   *> & PRE-PRINTED STATIONERY
              perform  headings-1.
*>
     go       to loop.
*>
 total-print-2.
*>************
*>
*>  Dont need this for NON matrix type printers / line printers.
*>
*>     move     spaces  to  print-record.
*>     write    print-record after k  lines.
*>     write    print-record after 13.
*>
     move     spaces to Line-8.
     move     ws-Item-Count to l8-Qty.
     move     "                Total Item Count" to l8-Desc.
     write    print-record from Line-8 after 3 lines.
*>
*> Packed By Note.
*>
     move     spaces to Line-8.
     move     "Packed by ............" to L8-Desc.
     write    print-record from Line-8 after 3 lines.
*>
     if       sih-status-P not = "P"
              move "P" to sih-status-P				*> we have printed pick list
              move sinvoice-header to WS-Invoice-Record
              perform Invoice-Rewrite.
*>
 main-exit.   exit section.
*>********    ****
*>
 headings-1                section.
*>================================
*>
*> May need to change this first block depending on page layout/size etc.
*>  with the first-time test
*>
     accept   ws-Time from time.
     move     ws-Time (1:2) to l3-HH.
     move     ws-Time (3:2) to l3-MM.
*>
     if       SL-Comp-Pick				*> print Co. address details
      if      first-time = "Y"           		*> Dont print a blank page
              write Print-Record from line-Company-Details1 after 1
      else
              write Print-Record from line-Company-Details1 after page
      end-if
     end-if
     if       SL-Comp-Pick
              write Print-Record from line-Company-Details2 after 1
              write Print-Record from line-Company-Details3 after 1
              write Print-Record from line-Company-Details4 after 1
              write Print-Record from line-Company-Details5 after 1
              write Print-Record from line-Company-Details6 after 1
              write Print-Record from line-Company-Details7 after 1
              if    VAT-Reg-Number (1:4) not = spaces
                    write Print-Record from line-Company-Details8 after 1
              end-if
              write print-record from line-0-a after 1
     end-if
     if       not SL-Comp-Pick
      if      first-time = "Y"
              write    print-record  from  line-0-a after 4
      else
              move spaces to print-record
              write print-record after page
              write print-record from line-0-a after 4
      end-if
     end-if
*>
     write    print-record  from  line-0-c after 2.
     write    print-record  from  line-0-d after 1.
     write    print-record  from  line-0-e after 2.
     write    print-record  from  line-1 after 1.
     write    print-record  from  line-2 after 1.
     write    print-record  from  line-3 after 1.
     write    print-record  from  line-4 after 1.
     write    print-record  from  line-5 after 1.
     write    print-record  from  line-6 after 1.
     write    print-record  from  line-7 after 2.
     write    print-record  from  line-7B after 1.
     move     "N"  to  first-time.
*>
 main-exit.   exit section.
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
 zz090-Setup-Company-Details section.
*>**********************************
*>
*>  First get no. of chars in each field
*>
     if       not SL-Comp-Pick			*> test if company heads are wanted
              exit section.
*>
     move     spaces to Line-Company-Details.
 *>    perform  varying h1 from 32 by -1 until h1 = 1 or     usera (h1:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h2 from 24 by -1 until h2 = 1 or Address-1 (h2:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h3 from 24 by -1 until h3 = 1 or Address-2 (h3:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h4 from 24 by -1 until h4 = 1 or Address-3 (h4:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h5 from 24 by -1 until h5 = 1 or Address-4 (h5:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h6 from 12 by -1 until h6 = 1 or Post-Code (h6:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h7 from 24 by -1 until h7 = 1 or Country   (h7:1) not = space
 *>             continue
 *>    end-perform
*>
 *>    divide   91 by 2 giving h98.      *> size of print lines here = 45, yes I know its rounded down
*>
 *>    divide   h1 by 2 giving h99.
 *>    add      1  to h99.
 *>    move     usera     (1:h1) to line-Company-Details1 (h98 - h99:h1).
 *>    divide   h2 by 2 giving h99.
 *>    add      1  to h99.
 *>    move     Address-1 (1:h2) to line-Company-Details2 (h98 - h99:h2).
 *>    divide   h3 by 2 giving h99.
 *>    add      1  to h99.
 *>    move     Address-2 (1:h3) to line-Company-Details3 (h98 - h99:h3).
 *>    divide   h4 by 2 giving h99.
 *>    add      1  to h99.
 *>    move     Address-3 (1:h4) to line-Company-Details4 (h98 - h99:h4).
 *>    divide   h5 by 2 giving h99.
 *>    add      1  to h99.
 *>    move     Address-4 (1:h5) to line-Company-Details5 (h98 - h99:h5).
 *>    divide   h6 by 2 giving h99.
 *>    add      1  to h99.
 *>    move     Post-Code (1:h6) to line-Company-Details6 (h98 - h99:h6).
 *>    divide   h7 by 2 giving h99.
 *>    add      1  to h99.
 *>    move     Country   (1:h7) to line-Company-Details7 (h98 - h99:h7).
*>
*>  Use C$JUSTIFY instead of all this coding.
*>
     move     Usera     to Line-Company-Details1.
     move     Address-1 to line-Company-Details2.
     move     Address-2 to line-Company-Details3.
     move     Address-3 to line-Company-Details4.
     move     Address-4 to line-Company-Details5.
     move     Post-Code to line-Company-Details6.
     move     Country   to line-Company-Details7.
*> Backflow - simple !
     if       Line-Company-Details4 (1:20) = spaces
              move Line-Company-Details5 to Line-Company-Details4
              move Line-Company-Details6 to Line-Company-Details5
              move Line-Company-Details7 to Line-Company-Details6
              move spaces to Line-Company-Details7.
     if       Line-Company-Details5 (1:20) = spaces
              move Line-Company-Details6 to Line-Company-Details5
              move Line-Company-Details7 to Line-Company-Details6
              move spaces to Line-Company-Details7.
     if       Line-Company-Details6 (1:20) = spaces
              move Line-Company-Details7 to Line-Company-Details6
              move spaces to Line-Company-Details7.
*>
     call     "C$JUSTIFY" using Line-Company-Details1 "C".
     call     "C$JUSTIFY" using Line-Company-Details2 "C".
     call     "C$JUSTIFY" using Line-Company-Details3 "C".
     call     "C$JUSTIFY" using Line-Company-Details4 "C".
     call     "C$JUSTIFY" using Line-Company-Details5 "C".
     if       Line-Company-Details6 (1:10) not = spaces
              call     "C$JUSTIFY" using Line-Company-Details6 "C".
     if       Line-Company-Details7 (1:10) not = spaces
              call     "C$JUSTIFY" using Line-Company-Details7 "C".
*>
*> Vat detail line - Legally this does not need to be produced for packing notes
*>  so you could comment this out by using "*>" at start of each of these 6 lines
*> CHANGE  chars "GB" to match your country if needed.
*>
     if       VAT-Reg-Number (1:4) not = spaces
              string   "VAT Number: GB"   delimited by size   *> Chg 'GB' for your country code if needed
                       VAT-Reg-Number     delimited by size
                        into line-Company-Details8
              end-string
              CALL "C$JUSTIFY" using line-Company-Details8, "C".
*>
 zz090-Exit.  Exit Section.
*>*********
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
