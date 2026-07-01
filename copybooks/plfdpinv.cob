*>*******************************************
*>              Purchase                    *
*>  File Definition For The Invoice File    *
*>                                          *
*>*******************************************
*> record size 100 bytes 26/03/09
*>             126 bytes 15/12/11 to match fdinv2
*>             129 bytes 22/12/11
*>             100 bytes 08/01/18 less filler err. item-nos bin -> 99.
 fd  Invoice-File.
*>
 01  Invoice-Record.
     03  invoice-key.
         05  invoice-nos pic 9(8).
         05  item-nos    pic 99.  *> was binary-char.
     03  invoice-supplier pic x(7).
     03  invoice-date    binary-long.
     03  inv-order       pic x(10).
     03  invoice-type    pic 9.
     03  filler          pic x(10).
     03  filler          pic x(58).   *> was x(88). now rec 100
*>
