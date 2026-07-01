*>*******************************************
*>        wsinv.cob copied to copybooks as  *
*>         slwsinv.cob.                     *
*>                                          *
*>              In Sales                    *
*>  Working Storage For The Invoice Header  *
*>      Also See FDinv2.Cob                 *
*>*******************************************
*>   size 129 bytes 09/03/09
*>   size 134 bytes 24/03/12
*>   size 137 bytes 18/01/17
*> WARNING UPDATE all layouts for 5 byte increase (extra statuses)
*> 02/05/23 - updated for Autogen see below sih-Order
*> 03/03/24 - in SInvoice-Bodies sil-Back-Ordered replaces the last field
*>            (FILLER) - set to B for a BO item.
*>            Addded lowercase values for some values - JIC.
*>
 01  SInvoice-Header.                         *> 137 bytes 18/01/17
   02 sih-prime.                              *> 42 bytes
     03  WS-Invoice-Key.
         05  sih-invoice   pic 9(8).
         05  sih-test      pic 99  value zero.  *> WAS binary-char
     03  sih-customer.
         05  sih-nos       pic x(6).
         05  sih-check     pic 9.
     03  sih-date          binary-long.       *> For autogen next date due
     03  sih-order         pic x(10).         *> New changes 24/3/23 for Autogen/recurring invoices
     03  filler redefines sih-order.
         05  sih-Freq      pic x.
             88  Sih-Yearly    value "Y".
             88  Sih-Monthly   value "M".
             88  Sih-Quarterly value "Q".
             88  sih-Daily     value "D".     *> These two are only for testing.
             88  sih-Testing   value "D".     *>  So NOT documented and removed after tests.
             88  sih-Valid-Freqs  values "Y" "M" "Q" "D".   *> Last one D, for TESTING ONLY so remove after
         05  sih-Repeat    pic 99.
         05  filler        pic xxx.
         05  sih-Last-Date binary-long.   *> 4 bytes date an invoice was generated/posted
     03  sih-type          pic 9.
     03  sih-ref           pic x(10).
   02 Sih-Sub-Prime.                          *> 95 bytes
     03  sih-description   pic x(32).
     03  sih-fig                          comp-3.
         05  sih-p-c       pic s9(7)v99.
         05  sih-net       pic s9(7)v99.
         05  sih-extra     pic s9(7)v99.
         05  sih-carriage  pic s9(7)v99.
         05  sih-vat       pic s9(7)v99.
         05  sih-discount  pic s9(7)v99.
         05  sih-e-vat     pic s9(7)v99.
         05  sih-c-vat     pic s9(7)v99.
     03  sih-status        pic x.
         88  pending                           values "P" "p".
         88  invoiced                          values "I" "i".
         88  sapplied                          values "Z" "z".
     03  sih-status-P      pic x.         *> Pick list Printed           space or P
     03  sih-status-L      pic x.         *> Invoice Printed             space or L
     03  sih-status-C      pic x.         *> Invoice Cleared             space or C   paid or credited or cleared/cancelled etc
     03  sih-status-A      pic x.         *> Invoice Applied to a/c      space or A
     03  sih-status-I      pic x.         *> Invoice Item lines Deleted  space or D
     03  sih-lines         binary-char.   *> No. of following body line recs
     03  sih-deduct-days   binary-char.
     03  sih-deduct-amt    pic 999v99    comp.
     03  sih-deduct-vat    pic 999v99    comp.
     03  sih-days          binary-char.
     03  sih-cr            binary-long.
     03  sih-day-book-flag pic x               value space.
         88  day-booked                        values "B" "b".
     03  sih-update        pic x.
         88  sih-analyised                     values "Z" "z".
*>
*>*******************************************
*>                                          *
*>  Working Storage For The Invoice Lines   *
*>                                          *
*>*******************************************
*> 80 bytes each = 3200 bytes (17/05/13)
*> still valid 18/01/17
*>
 01  SInvoice-Bodies.
     03  Invoice-Line                    occurs 40.
         05  sil-Key.                      *> 10 bytes
             07  sil-invoice pic 9(8).
             07  sil-line    pic 99.       *> was binary-char.
         05  sil-product     pic x(13).    *> +1 17/5/13 - 23
         05  sil-pa          pic xx.       *> 25
         05  sil-qty         binary-short. *> 2 - 27
         05  sil-type        pic x.        *> 28
         05  sil-description pic x(32).    *> +8 17/5/13 60
         05  sil-net         pic s9(7)v99   comp-3.
         05  sil-unit        pic s9(7)v99   comp-3.
         05  sil-discount    pic 99v99      comp. *> 2
         05  sil-vat         pic s9(7)v99   comp-3. *> 18 - 77
         05  sil-vat-code    pic 9.
         05  sil-update      pic x.
             88 sil-analyised                       value "Z".
         05  sil-Back-Ordered
                             pic x.       *> value space, or B for a BO item.
*>         05  filler          pic x.          *> was pic xx.
*>
