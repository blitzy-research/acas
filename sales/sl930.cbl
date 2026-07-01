       >>source free
*>
*>    INVOICE PRINT
*>
*> THERE IS TEST CODE at all-print to force printing even if
*> INVOICES HAVE BEEN PRINTED SO THIS NEEDS TO BE REMOVED
*>   FOR PRODUCTION / SYSTEM TESTING.
*> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>  THIS PROGRAM MUST BE MODIFIED TO SUIT YOUR INVOICING STATIONERY
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>    Do so in conjunction with SL950 Delivery / Picking Note Print.
*>      and ensure testing with stationery or plain paper
*>
*>  FOR sending Emails as well as invoices, statements & late letters
*>    the delay before deleting the created temporary email files is
*>    in variable  WS-Sleep and is preset to 5 seconds at
*>    program EOJ (End of Job).
*>   Change this if time is wrong but allow extra 2 seconds just in
*>    case.
*>
*> Change variable WS-Emails-Both to zero if you only want to send
*>  emails if the sales record shows an email address and
*>  Email-Invoicing is set.   Default BOTH.
*>
*> PRODUCES TITLES ETC ON PLAIN PAPER
*>
*> MAKE SURE THERE IS A NOTE IN THE SALES Manual Regarding these notes.
*> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*> Changes as of 27 June 2023 and version 3.02.22::
*> Program operation has been changed to reflect usage of Emails using freely
*> available email clients, in that instead of directly creating a invoice
*> print to file or printer it opens it but all individual invoices are sent
*> first to a newly created email file that at end of invoice creation is
*> closed then reopened as INPUT and all records copied over to the invoice
*> where after it is closed and then the zz090-Issue-Email called.
*> This source code may need to be changed to reflect what ever client you are
*> using as currently set to use mailx.
*>
*> This order is important as the email client may not like the file still
*> being open as not being accessable.
*> At EOJ (End of Job) programs sleeps for predefined time current set as
*> 3 seconds, again to allow time for email client to send all email files out
*> before deleting all created files.
*> The Invoice file is closed for printing.
*> To Control this processing see the settings for the following variables :
*>
*> 03  WS-Email-Set    pic 9           value zero.   *> Set to 1 if sending email.
*>         88  WS-Send-Email               value 1.      *>  or should it be instead !!!
*>     03  WS-Sleep        pic 9           value 3.      *> at EOJ in secs to allow all emails to be issued
*>                                                        to the email client.
*>     03  WS-Emails-Both  pic 9           value 1.      *> Set to zero if only emails issued.
*>         88  WS-Emails-Only              value zero.
*>
*>  WS-Emails-Both when set to 1 (default) will send both emails and a printed invoice
*>    but if set to 0 (zero) will only send an email (recommended 1 as default)
*>  This only applies if the individual sales record was set up with an Email address
*>  AND the send email invoice.
*>
*> WS-Email-Set IF you wish to send Emails, set this to 1 instead of zero (default).
*>
*> WS-Sleep is set to 3 (seconds) as the time to wait before deleting the email
*> files and this allows some time for the email client to actual send the emails
*> out as the emails are actually files if the files are deleted it might not find
*> one or more such files when sending if there is a delay it the client processing
*> them.  IF you get errors being reporting that such files are missing from the
*> email client, you should INCREASE the time preset from 3 to a larger number
*> such as say 5 - 10, although 3 should be more than enough but for slower
*> systems it just might not be enough.
*>
*>  Having made changes to these or any other setting in the program you must
*>  re-compile it by running the supplied scripts in folder sales comp-sales.sh
*>  then in top level ACAS install-ACAS-preinstalled.sh if you have installed
*>  the system before or if the first time run instead install-ACAS.sh.
*>  NOTE that you should ONLY run this last script ONCE as it also updates the
*> file ./bashrc with extra setting for the ACAS environment. The script with
*> the ...preinstalled.sh etc should be used otherwise.
*>
*>*****************************************************************
*>                                                                *
*>               I N V O I C E   P R I N T                        *
*>                                                                *
*>       SUPPLIED IN SOURCE FOR MODIFICATION BY CUSTOMER          *
*>                                                                *
*> Applewood Computers offers a service to change this module     *
*>   to meet your invoicing requirements.                         *
*>  currently set to spool to lpt2 printer and assumes a matrix   *
*>      printer using preprinted stationery or a laser using      *
*>        a preloaded template & produces 2 copies per invoice    *
*>        but see changes .09 for more info on this.              *
*>*****************************************************************
*> Commercial version instead of printing created temp file for   *
*> each inv by a/c name then called a *txt to .pdf file converter *
*> then ran a emailer for customers that requested this method    *
*> of delivery.  These steps could also produce a invoice via     *
*> graphic template as an underlay similar to used for Laser      *
*> printers and this is used in place of the txt file.            *
*> This process also used in Statements and late letters.         *
*>                                                                *
*> A O/S version of the mailer is supplied but not the            *
*> graphic/txt file to .pdf as one used is a licensed product.    *
*> Still trying to find a free to use and supply version. See API *
*> code refs below.                                               *
*>  You can use the supplied script prtpdf.sh to convert the      *
*>  created Email file to a .pdf file if you install packages     *
*>   enscript & ghostscript-common                                *
*>                                                                *
*>  THIS PROGRAM MUST ALWAYS BE TESTED TO CONFIRM THAT IT WORKS   *
*>  TO YOUR REQUIREMENTS. Likewise sl950 (picking/packing sheets) *
*>   and for that matter Statements production sl190.             *
*>                                                                *
*>    Can be easily modified to also print to second printer in   *
*>    Dispatch Department etc for Picking Lists/Dispatch notes    *
*>    Also see sl950 that just prints Delivery/Picking notes      *
*>     AND this should be run first, before sl930.                *
*>     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                 *
*>*****************************************************************
*>  Adobe Reader API Code removed from this and the Dispatch      *
*>  modules, has been removed as they are non-free code and users *
*>  have to purchase it and the reader/Forms programs from Adobe. *
*>  I will try and relook at this as well as links to LibreOffice *
*>  that do a similar job in producing stylised documents instead *
*>  based on template forms etc when time is available.           *
*>*****************************************************************
*>
*>     Maximum Values that are printed as standard:
*>        Amounts line items 10M<   M = Million & '<' = 1 less than.
*>        Amounts Totals     100M<
*>        Quanities          1M<
*>        Line items per inv 25 =< from 15 and NOW USES SL-Invoice-Lines.
*>             18/03/2018.
*>*****************************************************************
*>
 identification          division.
*>===============================
*>
      program-id.         sl930.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen, FBCS, FIDM, FIDPM 28/10/83
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Print.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     Maps04.
*>                        acas012  ->       (Sales)
*>                         salesMT.
*>                        acas014  ->       (Delivery)
*>                         deliveryMT.
*>                        acas016  ->
*>                         invoiceMT.
*>                        SL070. Analysis codes set up - Defaults only.
*>**
*>    Error messages used.  These messages are remarked out, as page align is off.
*>                        SL003 hit return ...
*>                        SL200  Form alignment msg. ->  Used for continuous stationery only.
*>                        SL201  Error creating email file.
*>                        SL202  Hit return to Abort.
*>**
*> Changes
*> 03/03/09 vbc - .01 Migration to Open Cobol v3.00.00.
*> 10/03/09 vbc - .02 Minor adjustment for A4 paper after 1st page
*>                    also needs some added code for 10 point printing instead
*>                    of 12 or change laser via script prior to printing and
*>                    again afterwards.  Done, see print-spool-command.cob
*> 11/03/09 vbc - .03 Re-added extra discount/charge line in totals
*>                    for some reason missing on this version.
*> 13/03/09 vbc - .03 Added extra-print flag to print or not see above.
*> 07/09/10 vbc - .04 Mod lpr.
*> 26/11/11 vbc - .05 Error msgs to SLnnn. Support for dates other than UK
*> 08/12/11 vbc - .06 Support for path+filenames.
*> 09/12/11 vbc -     Updated version to 3.01.nn, support for IS delivery file
*> 11/12/11 vbc - .07 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 24/03/12 vbc - .08 Support for printing to 2 printers but remd out
*> 19/05/13 vbc - .09 Added in sil-Status-L (future proofing) at total-print-4 & show 'Invoice'for same
*>                    and produces two copies of each invoice with one for filing. You will need to change
*>                    copy "print-spool-command-p.cob" from "-# 2 " to "-# 3 " for three copies etc or
*>                       "-# 1 " for one (or remove it).
*>                    Note that sl950 just prints picking lists.
*> 22/05/13 vbc - .10 Tidied up headings & added time to headings along with changes made to sl930.
*> 29/05/13 vbc - .11 More tidyup of inv heads for plain paper invoices and no doubt more needed.
*>                    Checked that all non-free API code from Adobe Reader is removed.
*> 04/06/13 vbc - .12 Using Print details from Print-Spool-Name2 with PSN2 in prt-2.
*> 24/10/16 vbc - .13 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc - .   All programs upgraded to v3.02 for RDB processing.
*> 19/01/17 vbc - .14 Converted usage of maps99 to displays.
*>                    Added FH/DAL processing for file processing
*>                    Invoice files to be done.
*>                    Removed P.A. file test as it is NOT used here.
*> 20/01/17 vbc       Removed all references to invoice-let as redundant.
*>                    See sl910 & sl920.
*> 25/01/17 vbc       Dry testing completed.
*> 10/02/17 vbc - .15 Updated FD/WS for 016 and replaced cobol verbs
*>                    for access to FH/DALs.
*> 18/04/17 vbc - .16 Updated to use Invoice-Read-Next-Header where only the
*>                    Header is wanted (if test = zero then read-next.
*>                    Cuts down unneeded reads of table. FH is still the same.
*> 18/03/18 vbc - .17 With the addition of parm field SL-Invoice-Lines & in sys002
*>                    print inv programs will use it instead of a fixed 15/25.
*> 04/12/18 vbc - .18 Compiler doesn't like inline performs without an imperative
*>                    statement - changed to a continue.
*> 16/06/20 vbc - .19 Uses Company name/addr if SL-Comp-Inv = Y.was wrong (pick)
*> 18/02/23 vbc - .20 Changed print-line to 88 max text line
*>                    Support for printfile names instead of prt-1 but will default
*>                    to it.
*> 06/03/23 vbc - .21 In zz080-Setup-Company-Details if not spaces added VAT data to
*>                    Line-Company-Details8 and in headings-1 print it out as
*>                    last line in company name address details - hopefully centered.
*>                    Also done in sl950.
*> 07/03/23 vbc - .22 lpr copybook print-spool-command-p-dispatch.cob changed
*>                    for single-sided  Also applies to sl930
*>                    by using print-spool-command-p-dispatch-2 or -3 for multi copies
*> 25/06/23 vbc *     Added zz090-Issue-Email but not coded up and no vars set up.
*> 26/06/23           Next is also for programs sl110 and sl190.
*>                    Extra coding to support sending of emails but not complete as
*>                    it cannot be tested on dev system.
*>                    Company heading changed to use C$JUSTIFY in ZZ080
*>                     same for sl950.
*> 07/08/23 vbc - .23 fix in zz090-Setup-Company-Details bland addr lines
*>                    within address. for both sl930 & sl950.
*>                    Adjust line-0-d less 1 char on 1st field.
*> 27/01/24 vbc - .24 Omit using Credit Terms if not printing Invoice at
*>                    total-print. Inv # missing - reduced size of line to 80
*>                    by using fit-to-page - JIC.
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
*> copy "selinv.cob".
*> copy "selsl.cob".
*> copy "seldel.cob".
*>
*> 18/02/23
 copy "selprint-2.cpy".  *>  replacing "prt-1" by "prt-2". Invoice printer
*>
     select  Email-Print-File   assign       PP-Email-File
                                organization line sequential
                                status       PRT-Status.
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
*> copy "fdinv.cob".
*> copy "fdsl.cob".
*> copy "fddel.cob".
*>
 fd  Print-File.
*>
 01  Print-Record            pic x(88).  *> 18/2/23 was x(102) get rid of space lines between text
*>
*> Used for individual email texts all WRITE's for printing switched to using this
*>  at end of Invoice file closed then opened for input to read each record and copy out
*>  out to the primary Print-File.
*>  All files with name starting as "Email-Text-nnnnnnnnnnnnnn" are deleted prior to EOJ
*>    after sleeping for up to 5 seconds to allow time for all emails to be sent.
*>
 fd  Email-Print-File.
 01  Email-Print-Record      pic x(88). *> was 80 - now matches printer.
*>
 working-storage section.
*>----------------------
 77  prog-name               pic x(15) value "SL930 (3.3.00)".
*>
*> Change this to suite your requirements. This is set portrait,
*>   see CUPS help on 'lpr' but change it within program not the copybook
*>
*> Now changed to use the fit to page copybook -less hassle.
*>
 copy "print-spool-command-invoice.cob" replacing "prt-1" by "prt-2".
*> copy "print-spool-command-p-dispatch.cob" replacing "prt-1" by "prt-2".
*>
*>  "-# 2 ". replace "" if needed also needs the ""prt-1" by "prt-2"
*> Also change for two (or more) copies per invoice,  if needed
*> I.e., one for customer, filing, sales department etc, by using instead of
*> copy "print-spool-command-p-dispatch.cob" use
*>  copy "print-spool-command-p-dispatch-2.cob"
*> for two copies or for three copies use
*>  copy "print-spool-command-p-dispatch-3.cob".
*>
*> this one or next ONLY, not both & '-# 2' means 2 copies (1 cust, 1 file).
*>
*>    WARNING print delivery/packing slips FIRST (sl950) before printing
*>     invoices. as you cannot do so after printing invoices.
*>
*> Another option is to leave the setting for only one copy to be printed and
*> to use a copier of a three in one printer to produce copies of all printed
*> invoices for the sales team to file prior to sending them.
*>    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
                *>   was copy "wsinv.cob". This is the invoice table sih / l-
 copy "slwsinv.cob"  replacing Invoice-Line by Invoice-Lines. *> original with occ 40 for lines
*> RDB / File records.
 copy "slwsinv2.cob".
 01  WS-Invoice-Record  redefines Invoice-Record
                                pic x(137).
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
*>     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
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
 01  WS-Current-Time.
*> From accept xx from microsecond-time 8 chars but only 6 is more than likely created
     03 CDT-Hour         PIC 9(2).  *> chgd to use only 2 Mill as original produces nothing
     03 CDT-Minutes      PIC 9(2).
     03 CDT-Seconds      PIC 9(2).
     03 CDT-Mill         pic 9(8).
*>
 01  WS-Email-Data.
     03  WS-Email-Command pic x(768).
     03  WS-Email-Subject pic x(256).
     03  WS-Email-Body    pic x(256).

 01  ws-data.
*>
*>  These three are for email processing only
*>
     03  WS-Email-Set    pic 9           value zero.   *> Set to 1 if sending email.
         88  WS-Send-Emails              value 1.      *>  or should it be instead !!!
     03  WS-Sleep        pic 9           value 3.      *> at EOJ in secs to allow all emails to be issued
*>                                                        to the email client.
     03  WS-Emails-Both  pic 9           value 1.      *> Set to zero if only emails issued.
         88  WS-Emails-Only              value zero.
     03  WS-Email-Sent   pic 9           value zero.  *> set to 1 = emails have been sent
*>
     03  PP-Email-File.
         05  filler      pic X(12)       value "sl930-Email-".
         05  PP-Emails-Time
                         pic 9(14)       value zeros.
*>
     03  Test-Product.
         05  filler      pic x.
             88  il-comment              value "/".
         05  filler      pic x(6).
     03  WS-Reply        pic x.
     03  PRT-Status      pic 99.
     03  print-path      pic x.
     03  a               pic 99.
     03  c-check         pic 9.
         88  c-exists                    value 1.
     03  address-line    pic x(36).
     03  work-n          pic 9(6)v99.
     03  work-v          pic 9(6)v99.
     03  i               pic 99.
     03  ii              pic 99.
     03  j               pic 99.
     03  k               pic 99.
     03  kk              pic 99.
     03  ws-Time         pic 9(8)        value zero.
     03  first-time      pic x           value "Y".
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
 01  Error-Messages.
*> System Wide
     03  SL003          pic x(28) value "SL003 Hit Return To Continue".
*> Module specific
     03  SL200          pic x(37) value "SL200 Re-Align Invoice To Top Of Form".  *> Matrix type printers only
     03  SL201          pic x(34) value "SL201 Error creating Email file - ".
     03  SL202          pic x(25) value "SL202 Hit return to Abort".
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
*> line 1 - 14
*>     03  filler          pic x(44)       value spaces.
     03  l0-type         pic x(14).
*>
 01  line-0-b.
*> line 2 - 14
*>     03  filler          pic x(44)       value spaces.
     03  l0-xs           pic x(14).
*>
 01  line-0-c.
*> line 3 - 62
     03  filler          pic x(37)       value spaces.
     03  l0-desc         pic x(25).			*> not a vat inv notice
*>
 01  line-0-d.
*> line 5  85 chars
     03  filler          pic x(25)       value spaces.
     03  l3-title        pic x(7)        value "INVOICE".
     03  filler          pic x(25)       value spaces.
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
*> line 9  85 chars
     03  filler          pic x(66)       value spaces.
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
*> line 12  88 chars
*>     03  filler          pic x(05)       value spaces.
     03  l3-i-line       pic x(31).
     03  filler          pic xxxx        value spaces.
     03  l3-d-line       pic x(30).
     03  filler          pic x(5)        value spaces.
     03  filler          pic x(7)        value "Order:".
     03  l6-order        pic x(11).
*>
 01  line-4.
*> line 13  88 chars
*>     03  filler          pic x(05)       value spaces.
     03  l4-i-line       pic x(31).
     03  filler          pic xxxx        value spaces.
     03  l4-d-line       pic x(30).
     03  filler          pic x(5)        value spaces.
     03  filler          pic x(7)        value " Ref :".
     03  l4-ref          pic x(11).
*>
 01  line-5.
*> line 14  84 chars
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
 01  line-7B.			*> plain invoice line heads - 87
     03  filler          pic x(14)       value "Product Code  ".
     03  filler          pic x(30)       value "Item Description".
     03  filler          pic x(6)        value "   Qty".
     03  filler          pic x(10)       value "      Cost".
     03  l7B-Disc        pic x(7)        value "  Disc ".	*> This should be clear when no disc
     03  filler          pic x(10)       value "      Net".
     03  filler          pic x(10)       value "      Vat".
*>
 01  line-8.
*> line 19-33 (15)  87 chars but should be 89 (desc x32)
     03  l8-product      pic x(13)B      value spaces.
     03  l8-desc         pic x(30).                          *> 44  Chopped last 2
     03  l8-qty          pic z(5)9       blank when zero.    *> 50
     03  l8-unit         pic z(6)9.99    blank when zero.    *> 60
     03  l8-discount     pic zz9.99      blank when zero.    *> 66
     03  l8-percent      pic x.				     *> 67
     03  l8-net          pic z(6)9.99    blank when zero.      *> 77
     03  l8-vat          pic z(6)9.99    blank when zero.      *> 87
*>
 01  line-9.
*> line 35,37  87 chars
     03  l9-terms        pic x(14)       value "Credit Terms: ".   *> blank when not used.
     03  l9-days         pic zz9         blank when zero.
     03  filler          pic x(24)       value spaces.		*> 41
     03  l9-desc         pic x(24).				*> 65
     03  l9-net          pic -(7)9.99    blank when zero.		*> 76
     03  l9-vat          pic -(7)9.99    blank when zero.		*> 87
*>
 01  line-10.
*> line 40
     03  filler          pic x(14)       value spaces.
     03  l10-terms       pic x(16)       value "Prompt pay time:".
     03  l10-days        pic zz9         blank when zero.
*>
 01  line-11.
*> line 41 - 87
     03  filler          pic x(13)       value spaces.
     03  l11-amount      pic zzz9.99     blank when zero.	*> 20
     03  filler          pic x(45)       value spaces.		*> 65
     03  l11-net         pic z(7)9.99    blank when zero.		*> 76
     03  l11-vat         pic z(7)9.99    blank when zero.		*> 87
*>
 01  line-12.
*> line 43
     03  filler          pic x(65)       value spaces.
     03  l10-Gross-Lit   pic x(11)       value "Total Due: ".
     03  l10-gross       pic z(7)9.99.
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
 init01 section.
     if       full-invoicing = zero    *> invoicing NOT turned on
              goback                   *>  in Set up params.
     end-if
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
*> 18/02/2023 SPECIAL CODE FOR TESTING (FILE:) so that the print file is saved
*>     NOT IN sl950  - also see in menu-return
*>
     if       Print-Spool-Name2 (1:5) not = "FILE:" and not = spaces  *> 18/2/23
              move     Print-Spool-Name2 to PSN2
      else   if Print-Spool-Name2 (1:5) = "FILE:"
              move Print-Spool-Name2 (6:30) to PP-Print-File-Name.
*>
     move     1 to File-Key-No.
     perform  zz070-Convert-Date.
     perform  zz080-Setup-Company-Details.
*>
 menu-return.
*>***********
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Invoice Printing" at 0134 with foreground-color 2.
     display  ws-date at 0171 with foreground-color 2.
*>
*>  advise printing to file if Print-Spool-Name2 (1:5) = "FILE:"
*>
     if       Print-Spool-Name2 (1:5) = "FILE:"
              display "Warning: Printing to File: " at 0205 with foreground-color 3
              display PP-Print-File-Name            at 0232.
*>
*>     display  "You will need to manually spool 'prt-2'" at 0320 with foreground-color 2 highlight.
*>
     perform  Invoice-Open.          *>  open     i-o    invoice-file.
     if       fs-reply = 35              *> No invoice file/data yet so quit.
              goback.
     perform  Sales-Open-Input.          *> open input sales-file delivery-file.
     perform  Delivery-Open-Input.
     open     output print-file.
*>
     if       pass-value not = 3
              go to  all-print-start.
*>
*> Print one invoice as immediate print requested in sl910.
*>
     subtract 1  from  next-invoice  giving  invoice-nos.
     move     zero  to  item-nos.
*>
     move     1 to File-Key-No.
     perform  Invoice-Read-Indexed.   *> read invoice-file  record invalid key
     if       fs-reply not = zero
              go to  main-end.
*>
     move     WS-Invoice-Record  to  sinvoice-header. *> To table
*>
     if       pending in sih-status
       or     sih-status-L not = "L"     *> Invoice NOT printed.
              perform  print-routine
              go to    main-end.
*>
     display  "Invoice Number - " at 0501 with foreground-color 2.
     display  sih-invoice at 0518 with foreground-color 3.
     display  "Already Invoiced!.....Re-Print  (Y/N) ? - [Y]" at 0601 with foreground-color 2.
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
 all-print-start.   *> Batch printing (normal)
*>***************
*>
     display  "Print Or Re-Print.............  (P/R) ? - [P]" at 0701 with foreground-color 2.
     move     "P"  to  print-path
     accept   print-path at 0744 with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
*>
     if       print-path = "R"
              go to  all-print-get-inv.
*>
 amend-request.
*>
     move     "N" to ws-reply.
     display  "Any Amended Invoices In This Batch? [N]" at 0901 with foreground-color 2.
     accept   ws-reply at 0938 with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
     if       ws-reply = "Y"
              move zeros to first-sl-inv item-nos
              go to all-print.
     if       ws-reply not = "N"
              go to amend-request.
*>
     if       first-sl-inv = zero
              go to  all-print.
*>
     move     first-sl-inv  to  invoice-nos.
*>
 all-print-go.
*>
     move     zero  to  first-sl-inv  item-nos.
*>
     move     1 to File-Key-No.
     set      fn-Not-Less-Than to true.
     perform  Invoice-Start.   *> start invoice-file key not < invoice-key.
*>
 all-print.
*>*********
*>
     perform  Invoice-Read-Next-Header.    *> read invoice-file next record at end
     if       fs-reply = 10
              go to  main-end.
*>
     if       item-nos not = zero	*> find headers
              go to  all-print.
*>
     move     WS-Invoice-Record  to  sinvoice-header. *> to Table
*>
     if       sih-lines = zero and
              sapplied
              go to all-print.
*>
     if       pending in sih-status
              perform  print-routine
              go to    all-print.
*>
     if       print-path = "P"
              go to  all-print.
*>
*> Here is test to ensure that Invoices have NOT been printed before,
*>  but is remed out for testing
*>   and this test should go up above 'if pending' and/or that test
*>    be modified
*> Also the tests below really should be skipped as inv. printing is
*>  not relevant to pick lists [ this one IS invoice printing ]
*>
*>     if       ih-status-L = "L"     *> Invoice printed.
*>              go to All-Print.
*>
     display  "Invoice Number - " at 1101 with foreground-color 2.
     display  sih-invoice at 1118 with foreground-color 3.
     display  "Already Invoiced!.....Re-Print  (Y/N) ? - [Y]" at 1201 with foreground-color 2.
*>
     move     "Y"  to  ws-reply.
     accept   ws-reply at 1244 with foreground-color 6.
     move     function upper-case (ws-reply) to ws-reply.
*>
     if       ws-reply = "Y"
              perform   Print-Routine.
*>
     display  " " at 1101 with erase eol.
     display  " " at 1201 with erase eol.
*>
 all-print-more.
*>
     display  "More To Print? [Y]" at 1101 with foreground-color 2.
     move     "Y" to ws-reply.
     accept   ws-reply at 1117 with foreground-color 6 update.
     move     function upper-case (ws-reply) to ws-reply.
     if       ws-reply = "N"
              go to main-end.
     if       ws-reply = "Y"
              go to all-print-get-inv.
*>
     go       to all-print-more.
*>
 all-print-get-inv.
*>
     display  " " at 1301 with erase eol.
     move     zero to invoice-nos.
     display  "Give Lowest Invoice No. [        ]" at 1301 with foreground-color 2.
     accept   invoice-nos at 1326 with foreground-color 3 update.
     go       to all-print-go.
*>
 Main-End.
*>********
*>
     perform  Invoice-Close.    *> close invoice-file sales-file delivery-file.
     perform  Sales-Close.
     perform  Delivery-Close.
     close    Print-File.
     if       Print-Spool-Name2 (1:5) not = "FILE:"  *> Need to keep the file
              call     "SYSTEM" using print-report.
*>
*> Sleep for default seconds to allow time to send last emails
*> Then delete all email files.
*>

*> Temp for testing remark these 3 lines out. it can create a lot of files starting with "sl930-Email"
*>
 *>    if       WS-Email-Sent = 1
 *>             call     "C$SLEEP" using WS-Sleep  *> allow a few seconds for email client to finish
 *>             call     "CBL_DELETE_FILE" using "sl930-Email-*".  *> remove the old email attachment files
*>
     if       pass-value = 3
              move 1 to s-flag-i.
     exit     program.
*>
 Print-Routine           section.
*>===============================
*>
     move     1  to  i.
     perform  sih-lines times
              perform  Invoice-Read-Next     *> read invoice-file next record at end
              if       fs-reply = 10
                       exit perform
              end-if                         *> end-read
              if   item-nos = zero
                   exit perform
              end-if
              move WS-Invoice-Record to Invoice-Lines (i)
              if   sil-type (i) = "D"  *> Should not happen (sl920 ?)
                   exit perform
              end-if
              add  1  to  i
     end-perform
*>
     subtract 1  from  i.                       *> Now i = sih-lines = # of item lines
     move     spaces  to  line-0-a line-0-b line-0-c.
*>
     subtract 1 from i giving ii.
     if       ii = 0
              move 1 to ii.
*>     divide   ii by  25  giving  l7-count-2.           *> was 15
     divide   ii by  SL-Invoice-Lines  giving  l7-count-2.  *> 18/03/18
     add      1  to  l7-count-2.
     move     1  to  l7-count-1.
*>
*>     if       sih-type = 2                   *> Do not know why this here as it bypasses
*>              go to  get-customer.           *>    other if tests
*>
     move           "  =======" to  l0-xs.	*> for Invoices & receipts
*>
     if       sih-type = 1
              move  "  Receipt"  to  l0-type
     else
      if      sih-Type = 2
              move  "  Invoice"  to l0-Type
      else
       if     sih-type = 3
              move  "Credit Note" to  l0-type
              move  "===========" to  l0-xs
       else
              move  "  Pro-Forma" to  l0-type
              move  "  =========" to  l0-xs
              move "This is not a VAT Invoice" to l0-desc.
*>
 get-customer.
*>************
*>
     move     1 to File-Key-No.
     move     sih-customer  to  WS-Sales-Key.
     perform  Sales-Read-Indexed.           *> read     sales-file  record.
*>
*> Here added code for processing EMAILS - 27/06/23 3.02.23
*>  1st create email file-name with unique name
*>
     initialise
              WS-Current-Time.
     accept   WS-Current-Time from TIME.  *> MICROSECOND-TIME. - not working
     move     WS-Current-Time to PP-Emails-Time.
     open     output Email-Print-File.
     if       PRT-Status not = zero
              display  SL201 at 1201 with erase eos
              stop     SL202
              close    Email-Print-File
              go to    Main-End.
*>
     if       delivery-tag  >  zero
              move  "D"          to WS-Deliv-Key-Type
              move  WS-Sales-Key to WS-Deliv-Sales-Key
              perform  Delivery-Read-Indexed.      *> read delivery-file record.
*>
     move     spaces to l1-i-name  l1-d-name l2-i-line  l2-d-line
                        l3-i-line  l3-d-line l4-i-line  l4-d-line
                        l5-i-line  l5-d-line l6-i-line  l6-d-line.
*>
     move     sales-name  to  l1-i-name.
*>
     move     1  to  a.
     unstring sales-address  delimited by SL-Delim into  l2-i-line count a  pointer a.
     unstring sales-address  delimited by SL-Delim into  l3-i-line count a  pointer a.
     unstring sales-address  delimited by SL-Delim into  l4-i-line count a  pointer a.
     unstring sales-address  delimited by SL-Delim into  l5-i-line count a  pointer a.
     unstring sales-address  delimited by SL-Delim into  l6-i-line          pointer a.
*>
     if       delivery-tag = zero
              go to  heading-details.
*>
     move     deliv-name  to  l1-d-name.
*>
     move     1  to  a.
     unstring deliv-address  delimited by SL-Delim into  l2-d-line  count a  pointer a.
     unstring deliv-address  delimited by SL-Delim into  l3-d-line  count a  pointer a.
     unstring deliv-address  delimited by SL-Delim into  l4-d-line  count a  pointer a.
     unstring deliv-address  delimited by SL-Delim into  l5-d-line  count a  pointer a.
     unstring deliv-address  delimited by SL-Delim into  l6-d-line           pointer a.
*>
 heading-details.
*>***************
*>
     move     sih-invoice  to  l3-invoice.
*>
     move     sih-date  to  u-bin.
     perform  zz060-Convert-Date.
     move     ws-date  to  l3-date.
*>
     move     sih-customer  to  l6-account.
     move     sih-ref       to  l4-ref.
     move     sih-order     to  l6-order.
*>
     perform  headings-1.
*>
     move     1   to  k.
     move     SL-Invoice-Lines to J.     *> Using SL-Invoice-Lines instead of fixed 25 or 15.
*>     move     25  to  j.	*> 15  to  j.  matrix values with sub & totals etc lets try
*>				   10 more as should fit a page  - TEST
*>                                     then max. 25 line items per invoice page.
     move     zero to  work-n  work-v.
*>
 loop.
*>****
*>
     move     sil-product (k) to test-product.
     if       il-comment
              move spaces to line-8.
*>
     if       i-level-2
              move  sil-description (k)  to  l8-desc.
*>
     if       il-comment
              move zero to l8-qty l8-unit l8-discount l8-vat l8-net
              go to print-bypass.
*>
     if       i-level-2
              move  sil-qty  (k)     to  l8-qty
              move  sil-unit (k)     to  l8-unit
              move  sil-product (k)  to  l8-product
              move  sil-discount (k) to  l8-discount
     else
              move  zero  to  l8-qty
              move  zero  to  l8-unit
              move  zero  to  l8-discount
              move  spaces to l8-product.
*>
     if       i-level-2
       and    sil-discount (k)  >  0
              move  "%"       to l8-percent
              move  "  Disc " to l7B-Disc
     else
              move  spaces   to l7B-Disc
              move  space    to l8-percent.
*>
     move     sil-net (k)   to  l8-net.
     move     sil-vat (k)   to  l8-vat.
*>
 print-bypass.
*>
     write    Email-Print-Record  from  line-8 after 1.
*>
     add      sil-net (k)   to  work-n.
     add      sil-vat (k)   to  work-v.
     add      1  to  k.
*>
     if       k  >  i                                               *> # sih-lines = # line items 4 cust.
*>              compute  k = ((l7-count-2 * 25)  -  i) + 2	*> was 15
              compute  k = ((l7-count-2 * SL-Invoice-Lines) - i) + 2        *> 25 was 15
              go to  total-print.
*>
     if       k  >  j
              move  k  to  kk
              move  2  to  k
*>              add  25  to  j		                                    *> 15  to  j
              add  SL-Invoice-Lines  to  j                          *> (see above) 25  to  j
              add  1   to  l7-count-1
              perform  total-print
              move kk  to  k
  *>            move  spaces  to  Email-Print-Record                *> THESE 2 NOT NEED FOR NON MATRIX
  *>            write  Email-Print-Record  after 13  lines          *> & PRE-PRINTED STATIONERY
              perform  headings-1.
*>
     go       to loop.
*>
 total-print.
*>**********
*>
     move     spaces  to  l9-desc.
     move     work-n  to  l9-net
     move     work-v  to  l9-vat.
     move     sih-days to  l9-days.
     if       sih-type = 2
              move     "Credit Terms: " to l9-terms
     else
              move     spaces to L9-Terms.
*>
     write    Email-Print-Record from line-9 after k  lines.
     move     zero   to l9-days.
     move     spaces to l9-Terms.
*>
 total-print-2.
*>************
*>
     if       zero = sih-deduct-amt and sih-deduct-vat
              write Email-Print-Record from line-7 after 1
              go to total-print-3.
*>
     move     "Late Payment Surcharge" to l9-desc.
     move     spaces         to l9-Terms.
     move     sih-deduct-vat to l9-vat.
     move     sih-deduct-amt to l9-net.
*>
     write    Email-Print-Record  from  line-9 after 1.
     move     spaces  to l9-desc.
*>
 total-print-3.
*>************
*>
     if       Extra-Print = "N"
         or   (zero = sih-extra and sih-e-vat)
              write Email-Print-Record from line-7 after 1
              go to total-print-4.
*>
     move     spaces      to l9-Terms.
     move     Extra-Desc  to l9-desc.
     move     sih-e-vat   to l9-vat.
     move     sih-extra   to l9-net.
*>
     write    Email-Print-Record  from  line-9 after 1.
*>
 total-print-4.
*>************
*>
     move     spaces     to l9-Terms.
     move     spaces     to l9-desc.
     move     sih-c-vat  to l9-vat.
     move     sih-carriage to l9-net.
*>
     write    Email-Print-Record  from  line-9 after 2  lines.
*>
     if       sales-credit = zero
              move  zero  to  l10-days
                              l11-amount
              move spaces to  l10-Terms
     else
              move "Prompt pay time:" to L10-Terms
              move  sih-deduct-days  to  l10-days.
*>
     if       sih-deduct-amt = zero
              move spaces to  l10-terms
              move  zero  to  l10-days.
*>
     add      sih-deduct-amt  sih-deduct-vat                   giving  l11-amount.
     add      sih-vat  sih-e-vat  sih-c-vat  sih-deduct-vat    giving  l11-vat.
     add      sih-net  sih-extra  sih-carriage  sih-deduct-amt giving  l11-net.
     add      sih-vat  sih-e-vat  sih-c-vat  sih-deduct-vat
              sih-net  sih-extra  sih-carriage  sih-deduct-amt giving  l10-gross.
*>
     write    Email-Print-Record  from  line-10 after 1.
     write    Email-Print-Record  from  line-11 after 1.
     write    Email-Print-Record  from  line-12 after 2.
*>
     move     spaces  to  print-record
                          Email-Print-Record.
*>
*> Omitted for plain paper or preprinted invoice not having a payslip section
*>   at the bottom
*>     write    Email-Print-Record after 5.
*>
     if       not sapplied
              move "I" to sih-status
              move "L" to sih-Status-L      *> Invoice printed.
              move sinvoice-header to WS-Invoice-Record
              perform Invoice-Rewrite.        *>  rewrite invoice-record.
*>
*> Copy email records to invoice printer
*>
     close    Email-Print-File.
*>
*> CURRENTLY WILL send an invoice if doing email - JIC email not the same was payment dept. etc.
*>
*> Could have a test if going to do an email and WS-Emails-Only set do NOT do up to end-perform:
*>
     open     input Email-Print-File
     perform  forever
              read     Email-Print-File at end
                       close    Email-Print-File
                       exit perform
              end-read
              write    Print-Record from Email-Print-Record
     end-perform.
*>
*> Before this step you could convert these files to a .PDF file with the same name
*>  but ending in .pdf say using prtpdf script, and if so modify the zz090 routine
*>   that match it doing this prior to the perform zz090-Issue-Email.
*>
     if       WS-Send-Emails
        and   Sales-Email (1:8) not = spaces
        and   Email-Invoicing
              perform zz090-Issue-Email
              move    1 to WS-Email-Sent.
*>
 main-exit.   exit section.
*>********    ****
*>
 Headings-1                section.
*>================================
*>
*> May need to change this first block depending on page layout/size etc
*>   and the business headings printed if not using preprinted stationary.
*>  with the first-time test
*>
     accept   ws-Time from time.       *> This time info so that dup inv can
     move     ws-Time (1:2) to l3-HH.  *> be found when reading the o/p to
     move     ws-Time (3:2) to l3-MM.  *> ensure only the latest is sent.
*>                                        THIS IS A MANUAL PROCESS:
     if       SL-Comp-Inv 			*> print Bus. address details
              if      first-time = "Y"          *> Dont print a blank page
                      write Email-Print-Record from line-Company-Details1 after 1
              else
                      write Email-Print-Record from line-Company-Details1 after page
              end-if
              write Email-Print-Record from line-Company-Details2 after 1
              write Email-Print-Record from line-Company-Details3 after 1
              write Email-Print-Record from line-Company-Details4 after 1
              write Email-Print-Record from line-Company-Details5 after 1
              write Email-Print-Record from line-Company-Details6 after 1
              write Email-Print-Record from line-Company-Details7 after 1
              if    VAT-Reg-Number (1:4) not = spaces
                    write Email-Print-Record from line-Company-Details8 after 1
              end-if
              write Email-Print-Record from line-0-a after 1
     end-if
     if       not SL-Comp-Inv
              if      first-time = "Y"
                      write    Email-Print-Record  from  line-0-a after 4
              else
                      move spaces to print-record
                      write Email-Print-Record after page
                      write Email-Print-Record from line-0-a after 4
              end-if
     end-if
*>
     write    Email-Print-Record  from  line-0-b after 1.
     write    Email-Print-Record  from  line-0-c after 2.
     write    Email-Print-Record  from  line-0-d after 1.
     write    Email-Print-Record  from  line-0-e after 2.
     write    Email-Print-Record  from  line-1 after 1.
     write    Email-Print-Record  from  line-2 after 1.
     write    Email-Print-Record  from  line-3 after 1.
     write    Email-Print-Record  from  line-4 after 1.
     write    Email-Print-Record  from  line-5 after 1.
     write    Email-Print-Record  from  line-6 after 1.
     write    Email-Print-Record  from  line-7 after 2.
     write    Email-Print-Record  from  line-7B after 1.	*> Line heads for plain invoices
*>
     if       first-time not = "Y"
              go to  main-exit.
*>
*>  This block is not needed if you spool to a laser/inkjet that uses
*>   single sheet paper.
*>   Otherwise unremark (remove the '*>' tags) for this block that contains
*>    Cobol lines if using a Line or matrix type printer ONLY with continuous
*>     invoice stationery so that you can align the paper correctly.
*>     but not for inkjet, lasers or other similar printers as there is nothing
*>     to align.
*>  REMOVE THE "*>" for the next 18 lines if needed.
*>     display  "Invoice Correctly Aligned.....  (Y/N) ? - [Y]" at 1401 with foreground-color 2.
*>
*>     move     "Y"  to  ws-reply.
*>     accept   ws-reply at 1444 with foreground-color 6 update.
*>     move     function upper-case (ws-reply) to ws-reply.
*>
*>     if       ws-reply = "Y"
*>              go to  main-end.
*>
*>     display  SL200  at 1601 with foreground-color 2.
*>     display  SL003  at 1801 with foreground-color 2.
*>
*>     accept   ws-reply at 1831.
*>     display  " " at 1401 with erase eol.
*>     display  " " at 1601 with erase eol.
*>     display  " " at 1801 with erase eol.
*>
*>     go       to headings-1.
*>
 main-pre-end.
*>***********
*>
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
 zz080-Setup-Company-Details section.
*>**********************************
*>
*>  This block is for NOT using preprinted stationary - Invoices.
*>  also see headings-1 but remarked out the perform lines of headings-1
*>   if not needed.
*>
*> >>>>> CODE CHANGED SO NEED TO TEST THIS BLOCK  26/06/23
*>
*>  First get no. of chars in each field
*>
     if       not SL-Comp-Inv 			*> test if company heads are wanted
              exit section.
*>
     move     spaces to Line-Company-Details.
*>
 *>    perform  varying h1 from 32 by -1 until h1 = 1
 *>                                      or     usera (h1:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h2 from 24 by -1 until h2 = 1
 *>                                      or Address-1 (h2:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h3 from 24 by -1 until h3 = 1
 *>                                      or Address-2 (h3:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h4 from 24 by -1 until h4 = 1
 *>                                      or Address-3 (h4:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h5 from 24 by -1 until h5 = 1
 *>                                      or Address-4 (h5:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h6 from 12 by -1 until h6 = 1
 *>                                      or Post-Code (h6:1) not = space
 *>             continue
 *>    end-perform
 *>    perform  varying h7 from 24 by -1 until h7 = 1
 *>                                      or Country   (h7:1) not = space
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
*> Vat detail line and is required for invoices in the UK and EU
*>   Change  chars "GB" to match your country if needed.
*>
     if       VAT-Reg-Number (1:4) not = spaces
              string   "VAT Number: GB"   delimited by size *> chg if country different from UK
                       VAT-Reg-Number     delimited by size  *>  to match up with yours.
                        into line-Company-Details8
              end-string
              CALL "C$JUSTIFY" using line-Company-Details8, "C".
*>
 zz080-Exit.  Exit Section.
*>*********
*>
 zz090-Issue-Email  section.
*>*************************
*>
*> This one for mailx, YOU MUST SET UP the password and/or other credentials
*>  for this email address to your email service provider via the configuration
*>  files usually stored in the *nix /etc folder for this to work.
*>
     move     spaces to WS-Email-Data.
     string   "Your invoice from "        delimited by size
              FUNCTION TRIM (Suser TRAILING)
              " "                         delimited by size
              "is attached. Should you have any problems with this please email admin at: "
              FUNCTION TRIM (Company-Email TRAILING)
              ". We thank you for your business and we hope to see you again soon." delimited by size
                             into WS-Email-Body.
     string   "'Your new Invoice from "   delimited by size
              FUNCTION TRIM (Suser TRAILING)
              "'"                         delimited by size
                             into WS-Email-Subject.
*>
     STRING   "echo "
              FUNCTION TRIM (WS-Email-Body TRAILING)
              " | mailx -r "              delimited by size
              FUNCTION TRIM (Company-Email TRAILING)
              " -s "                      delimited by size
              FUNCTION TRIM (WS-Email-Subject TRAILING)
              " -a "                      delimited by size
              FUNCTION TRIM (PP-Email-File TRAILING)
              " "                         delimited by size
              FUNCTION TRIM (Sales-Email TRAILING)
              x"00"                       DELIMITED BY SIZE
                     INTO WS-Email-Command.
     call     "SYSTEM" using WS-Email-Command.
     if       Return-Code not = zeros
              display "Email process is reporting failure - " Return-Code.
*>
*> Example using mutt : Again assumes you have set up the config files for it.
*>
*> STRING "echo "
*>        FUNCTION TRIM (WS-Email-Body TRAILING)
*>        " | mutt " DELIMITED BY SIZE
*>        " -s '"    DELIMITED BY SIZE
*>        FUNCTION TRIM (WS-Email-Subject TRAILING)
*>        "' -a "    DELIMITED BY SIZE
*>        FUNCTION TRIM (PP-Email-File TRAILING)
*>        " -- "     DELIMITED BY SIZE
*>        FUNCTION TRIM (Sales-Email TRAILING)
*>        INTO WS-EMAIL-COMMAND.
*>
*>   There are a lot of others to choice from including claws.
*>
 zz090-Exit.  exit section.
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
