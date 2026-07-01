*>*******************************************
*>                                          *
*>  WS   Definition For The Payments File   *
*>       For Purchase Ledger.               *
*>*******************************************
*> 237 bytes 26/03/09
*> 26/02/12 chngd bins to comps 4 sql, total size might be wrong
*> 11/01/18 238 bytes from test-length.
*>
 01  WS-Pay-Record.
     03  WS-Pay-Key.
         05  WS-Pay-Supl-Key pic x(7).
         05  WS-Pay-Nos      pic 99.           *> was comp was binary-char
     03  WS-Pay-Cont         pic x.
     03  WS-Pay-Date         pic 9(8)  comp.   *> was binary-long.
     03  WS-Pay-Cheque       pic 9(8)  comp.   *> was binary-long.
     03  WS-Pay-SortCode     pic 9(6)  comp.   *> was binary-long.
     03  WS-Pay-Account      pic 9(8)  comp.   *> was binary-long.
     03  WS-Pay-Gross        pic s9(7)v99    comp-3.
*>
     03  filler                      occurs 9.
         05  WS-Pay-Folio    pic 9(8)  comp.   *> was binary-long.
         05  WS-Pay-Period   pic 99    comp.   *> was binary-char.
         05  WS-Pay-Value    pic s9(7)v99    comp-3.
         05  WS-Pay-Deduct   pic s999v99     comp-3.
         05  WS-Pay-Invoice  pic x(10).
*>
