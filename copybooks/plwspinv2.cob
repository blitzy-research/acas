*>*******************************************
*>                Purchase                  *
*>  WS   definition for the invoice file    *
*>   also see fdinv.cob                     *
*>  Taken from fdpinv2.cob                  *
*>*******************************************
*> record size 129 bytes 22/12/11
*>           = 100 less filler err. 06/05/17 item-nos > 99 from bin-char
*>
 01  WS-PInvoice-Record.
     03  Invoice-Key.
         05  Invoice-Nos  pic 9(8).
         05  Item-Nos     pic 99.   *> was  binary-char.
     03  Invoice-Supplier pic x(7).
     03  Invoice-Date     binary-long.
     03  Inv-Order        pic x(10).
     03  Invoice-Type     pic 9.
     03  filler           pic x(10).
     03  filler           pic x(58).     *> was x(88).  now rec  100
*>
 01  Invoice-Header redefines WS-PInvoice-Record.   *> 100 bytes
     03  ih-invoice       pic 9(8).
     03  ih-test          pic 99.    *> was binary-char.
     03  ih-supplier.
         05  ih-nos       pic x(6).
         05  ih-check     pic 9.
     03  ih-date          binary-long.
     03  ih-order         pic x(10).
     03  ih-type          pic 9.
     03  ih-ref           pic x(10).
     03  ih-fig                          comp-3.
         05  ih-p-c       pic s9(7)v99.
         05  ih-net       pic s9(7)v99.
         05  ih-extra     pic s9(7)v99.
         05  ih-carriage  pic s9(7)v99.
         05  ih-vat       pic s9(7)v99.
         05  ih-discount  pic s9(7)v99.
         05  ih-e-vat     pic s9(7)v99.
         05  ih-c-vat     pic s9(7)v99.
     03  ih-status        pic x.
         88  pending     values "p" "P".
         88  invoiced    values "i" "I".
         88  applied     values "z" "Z".
     03  ih-lines         binary-char.
     03  ih-deduct-days   binary-char.
     03  ih-deduct-amt    pic 999v99    comp.
     03  ih-deduct-vat    pic 999v99    comp.
     03  ih-days          binary-char.
     03  ih-cr            binary-long.
     03  ih-day-book-flag pic x.
         88  day-booked             values "b" "B".
     03  ih-update        pic x.
         88  ih-analyised           values "z" "Z".
*>     03  filler           pic x(30).          *> This appears to be empty of data on all rec types. 06/05/17
*>
 01  Invoice-Line  redefines WS-PInvoice-Record.     *> 75 bytes 06/05/17, 74 bytes 22/12/11
     03  il-invoice       pic 9(8).
     03  il-line          pic 99.    *> was binary-char.
     03  il-product       pic x(13).    *> +1 18/05/13
     03  il-pa            pic xx.
     03  filler           pic xx.       *> -1 18/05/13
     03  il-qty           binary-short.
     03  il-type          pic x.
     03  il-description   pic x(24).
     03  filler           pic xx.
     03  il-net           pic s9(7)v99   comp-3.
     03  il-unit          pic s9(7)v99   comp-3.
     03  il-discount      pic 99v99      comp.
     03  il-vat           pic s9(7)v99   comp-3.
     03  il-vat-code      pic 9.
     03  il-update        pic x.
         88 il-analyised          values "z" "Z".
*>
