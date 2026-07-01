*>*****************************************************
*>             Purchase Ledger                        *
*>  WS   Definition For The Deleted Invoice Nos File  *
*>      Taken from fdpdos.cob                         *
*>*****************************************************
*> 19 bytes 26/03/09
*> FD & 01 Changed Slightly 07/01/17
*> 29/04/17 vbc chngaed names for rec & key.
*>
 01  WS-Del-Inv-Nos-Record.     *> this and next name changes.
     03  WS-Del-Inv-Nos  pic 9(8).
     03  Del-Inv-Dat     binary-long.
     03  Del-Inv-Cus     pic x(7).
*>
