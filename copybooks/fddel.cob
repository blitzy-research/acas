*>*******************************************
*>                                          *
*>  File Definition For The Delivery File   *
*>                                          *
*>*******************************************
*> 133 bytes 26/03/09
 fd  Delivery-File.
*>
 01  Delivery-Record.
     03  Deliv-Key.
         05  Deliv-Key-Type        pic x.
             88  Deliv-Key-Del-Addr            value "D".
             88  Deliv-Key-Notes               value "N".
         05  Deliv-Sales-Key.
           07  Deliv-Purchase-Key  pic x(7).
     03  Deliv-Name                pic x(30).
     03  Deliv-Address.
         05  Deliv-Addr1           pic x(48).
         05  Deliv-Addr2           pic x(48).
*>
