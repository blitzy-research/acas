*>*******************************************
*>             Sales                        *
*>       WS replacement of                  *
*>  (File Definition) For The Invoice File  *
*>                                          *
*>*******************************************
*> record size 129 bytes 09/03/09
*>        size 134 bytes 17/05/13 to match wsinv
*>        size 137 bytes 25/01/17
*>
*> WARNING UPDATE all layouts for 5 byte increase (extra statuses)
*>
*> 26/01/17 - Taken from the SL copy in that src dir and prefixed by 'sl'.
*>   Removed lowercase values so just using UC
*>   Removed all references to invoice-letter as redundant.
*>    same to all programs.
*>
*> 29/01/17 replaced item-nos from bin-char to pic 99.
*> 04/02/17 Taken from fdinv2.cob with FD removed.
*> 03/03/24 - in SInvoice-Bodies sil-Back-Ordered replaces the last field
*>            (FILLER) - set to B for a BO item. Matches slwsinv.cob.
*>            Redefines of il-Order for recurring support. Needed ??
*>            No Changes to Record size.
*>
*>  NEED TO DO A SIZING CHECK for all INVOICE copybooks.
*>
 01  Invoice-Record.                        *> 137
     03  Invoice-Key.
         05  Invoice-Nos    pic 9(8).
         05  Item-Nos       pic 99.          *> was binary-char.
     03  Invoice-Customer   pic x(7).
     03  Invoice-Date       binary-long.
     03  Filler             pic x(10).
     03  Invoice-Type       pic 9.
     03  filler             pic x(10).
     03  filler             pic x(95).
*>
 01  Invoice-Header  redefines Invoice-Record.       *> 137 bytes
    02  ih-prime.          *> 42 ??? bytes
     03  ih-invoice         pic 9(8).
     03  ih-test            pic 99.          *> was binary-char.
     03  ih-customer.
         05  ih-nos         pic x(6).
         05  ih-check       pic 9.
     03  ih-date            binary-long.     *> For autogen next date due
     03  ih-order           pic x(10).       *> New changes 24/3/23 for Autogen/recurring invoices
     03  filler redefines ih-order.
         05  ih-Freq        pic x.
             88  ih-Yearly    value "Y".
             88  ih-Monthly   value "M".
             88  ih-Quarterly value "Q".
             88  ih-Daily     value "D".     *> These two are only for testing.
             88  ih-Testing   value "D".     *>  So NOT documented and removed after tests.
             88  ih-Valid-Freqs  values "Y" "M" "Q" "D".   *> Last one D, for TESTING ONLY so remove after
         05  ih-Repeat      pic 99.
         05  filler         pic xxx.
         05  ih-Last-Date binary-long.   *> 4 bytes date an invoice was generated/posted
     03  ih-type            pic 9.
     03  ih-ref             pic x(10).
   02 ih-sub-prime.        *> 95 ??? bytes
     03  ih-description     pic x(32).
     03  ih-fig                             comp-3.
         05  ih-p-c         pic s9(7)v99.
         05  ih-net         pic s9(7)v99.
         05  ih-extra       pic s9(7)v99.
         05  ih-carriage    pic s9(7)v99.
         05  ih-vat         pic s9(7)v99.
         05  ih-discount    pic s9(7)v99.
         05  ih-e-vat       pic s9(7)v99.
         05  ih-c-vat       pic s9(7)v99.
     03  ih-status          pic x.
         88  pending                            value "P".
         88  invoiced                           value "I".
         88  applied                            value "Z".
     03  ih-status-P        pic x.         *> Pick list Printed           space or P
     03  ih-status-L        pic x.         *> Invoice Printed             space or L
     03  ih-status-C        pic x.         *> Invoice Cleared             space or C   paid or credited or cleared/cancelled etc
     03  ih-status-A        pic x.         *> Invoice Applied to a/c      space or A
     03  ih-status-I        pic x.         *> Invoice Item lines deleted  space or D
     03  ih-lines           binary-char.
     03  ih-deduct-days     binary-char.
     03  ih-deduct-amt      pic 999v99    comp.
     03  ih-deduct-vat      pic 999v99    comp.
     03  ih-days            binary-char.
     03  ih-cr              binary-long.
     03  ih-day-book-flag   pic x.
         88  day-booked                         value "B".
     03  ih-update          pic x.
         88  ih-analyised                       value "Z".
*>
 01  Invoice-Line   redefines Invoice-Record.  *> Header.    *> 80
     05  il-invoice         pic 9(8).
     05  il-line            pic 99.          *> was binary-char.
     05  il-product         pic x(13).   *> +1 17/5/13
     05  il-pa              pic xx.
     05  il-qty             binary-short.
     05  il-type            pic x.
     05  il-description     pic x(32).
     05  il-net             pic s9(7)v99   comp-3.
     05  il-unit            pic s9(7)v99   comp-3.
     05  il-discount        pic 99v99      comp.
     05  il-vat             pic s9(7)v99   comp-3.
     05  il-vat-code        pic 9.
     05  il-update          pic x.
         88 il-analyised                      value "Z".
     05  il-Back-Ordered    pic x.       *> value space, or B for a BO item.
*>       05  filler          pic x.          *> was pic xx.
*>

