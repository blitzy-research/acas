*>*****************************************************
*>                                                    *
*>  File Definition For The Deleted Invoice Nos File  *
*>                                                    *
*>*****************************************************
*> 19 bytes 04/04/09
*>
 fd  Del-Inv-Nos-File.
*>
 01  Del-Inv-Nos-Record.
     03  Del-Inv-Nos        pic 9(8).
     03  Del-Inv-Dat        binary-long.
     03  Del-Inv-Cus        pic x(7).
*>
