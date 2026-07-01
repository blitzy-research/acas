*>*****************************************************
*>         Sales Ledger                               *
*>  WS Definition For The Deleted Invoice Nos Rec     *
*>                                                    *
*>*****************************************************
*> 19 bytes 04/04/09
*> 06/01/17 vbc - taken from fddnos
*>
01  WS-Del-Inv-Nos-Record.
     03  WS-Del-Inv-Nos     pic 9(8).
     03  Del-Inv-Dat        binary-long.
     03  Del-Inv-Cus        pic x(7).
*>
