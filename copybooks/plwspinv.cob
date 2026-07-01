*>*******************************************
*>          In Purchase                     *
*>  Working Storage For The Invoice Header  *
*>     Temporary processing.                *
*>*******************************************
*> record size 100 bytes  06/05/17   26/03/09
*>
 01  PInvoice-Header.
     03  ih-prime.   *> 42 bytes  +1 06/05/17
         05  WS-Invoice-Key.    *> added 08/01/18.
             07  ih-Invoice   pic 9(8).
             07  ih-Test      pic 99     value zero.    *> was binary-char   value zero.
         05  ih-Supplier.
             07  ih-Nos       pic x(6).
             07  ih-Check     pic 9.
         05  ih-Date          binary-long.
         05  ih-order.           *>    pic x(10).    *> New changes 18/5/23 for Autogen
             07  ih-Freq      pic x.
                 88  ih-Yearly    value "Y".
                 88  ih-Monthly   value "M".
                 88  ih-Quarterly value "Q".
                 88  ih-Daily     value "D".     *> These two are only for testing.
                 88  ih-Testing   value "D".     *>  So NOT documented and removed after tests.
                 88  ih-Valid-Freqs  values "Y" "M" "Q" "D".   *> LAst one for TESTING ONLY so remove after
             07  ih-Repeat    pic 99.
             07  filler       pic xxx.
             07  ih-Last-Date binary-long.   *> 4 bytes date an invoice was generated/posted
         05  ih-Type          pic 9.
         05  ih-Ref           pic x(10).  *> 42
     03  ih-sub-prime.                  *> 58 bytes 06/05/17
         05  ih-Fig                          comp-3.   *> 40 bytes
             07  ih-p-c       pic s9(7)v99.
             07  ih-net       pic s9(7)v99.
             07  ih-extra     pic s9(7)v99.
             07  ih-carriage  pic s9(7)v99.
             07  ih-vat       pic s9(7)v99.
             07  ih-discount  pic s9(7)v99.
             07  ih-e-vat     pic s9(7)v99.
             07  ih-c-vat     pic s9(7)v99.   *> 40
         05  ih-status        pic x.
             88  pending               values "P" "p".
             88  invoiced              values "I" "i".
             88  applied               values "Z" "z".
         05  ih-lines         binary-char.
         05  ih-deduct-days   binary-char.  *> 43
         05  ih-deduct-amt    pic 999v99    comp.  *> 4
         05  ih-deduct-vat    pic 999v99    comp.
         05  ih-days          binary-char.
         05  ih-cr            binary-long.  *> 4
         05  ih-day-book-flag pic x   value space.
             88  day-booked            values "B" "b" .
         05  ih-update        pic x.
             88  ih-analyised          values "Z" "z".
*>
*>         05  filler           pic x.
*>         05 filler pic x(29).  *> not used for WS as its a filler 2 match header
*>
*>******************************************
*>                                         *
*>  Working Storage For The Invoice Lines  *
*>                                         *
*>******************************************
*> 75 bytes each - 3000 bytes 02/11/10- line +1 & filler remd so same size.
*>
 01  Pinvoice-Bodies.  *> was lines.
     03  invoice-line                   occurs 40.
         05  il-Key.        *> New 08/10/18
             07  il-invoice   pic 9(8).
             07  il-line      pic 99.     *> was binary-char.
         05  il-product       pic x(13).   *> +1 to match wspinv2
         05  il-pa            pic xx.
         05  filler           pic xx.      *> -1 to match wspinv2
         05  il-qty           binary-short.
         05  il-type          pic x.
         05  il-description   pic x(24).
         05  filler           pic xx.  *> 56
         05  il-net           pic s9(7)v99   comp-3.
         05  il-unit          pic s9(7)v99   comp-3.
         05  il-discount      pic 99v99      comp.
         05  il-vat           pic s9(7)v99   comp-3.
         05  il-vat-code      pic 9.
         05  il-update        pic x.
             88 il-analyised          values "z" "Z".  *> using Z hopefully.
 *>
*>       05  filler         pic x.   *> rounding filler for WS only
*>
