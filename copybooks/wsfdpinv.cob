*>*******************************************
*>              Purchase                    *
*>  File Definition For The Invoice File    *
*>   Renamed in WS for v3.02 29/12/17       *
*>*******************************************
*> record size 100 bytes 26/03/09
*>             126 bytes 15/12/11 to match fdinv2
*>             129 bytes 22/12/11
*>             100 bytes 29/12/17.
*> fd  invoice-file.
*>
 01  WS-Pinvoice-record.
     03  invoice-key.
       05  invoice-nos   pic 9(8).
       05  item-nos      pic 99.  *> was binary-char.
     03  invoice-supplier pic x(7).
     03  invoice-date    binary-long.
     03  inv-order       pic x(10).
     03  invoice-type    pic 9.
     03  filler          pic x(10).     *> 42 to here.
     03  filler          pic x(58).
*>
