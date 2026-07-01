*>*******************************************
*>                                          *
*>    WS Definition For The Delivery File   *
*>                                          *
*>*******************************************
*> 133 bytes 26/03/09
*> 06/01/17 vbc - Taken from fsdel.cob
*>
 01  WS-Delivery-Record.
     03  WS-Deliv-Key.
         05  WS-Deliv-Key-Type        pic x.
             88  Deliv-Key-Del-Addr            value "D".
             88  Deliv-Key-Notes               value "N".
         05  WS-Deliv-Sales-Key.
           07  Deliv-Purchase-Key  pic x(7).
     03  Deliv-Name                pic x(30).
     03  Deliv-Address.
         05  Deliv-Addr1           pic x(48).
         05  Deliv-Addr2           pic x(48).
