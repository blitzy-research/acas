*>*******************************************
*>                                          *
*>  File Definition For The Open Item File  *
*>                                          *
*>*******************************************
*>     record size 109 bytes 26/03/09
*>                 113 bytes 07/01/18      
 fd  open-item-file-5.
*>
 01  open-item-record-5.
     03  oi5-key.
         05 oi5-supplier    pic x(7).
         05 oi5-invoice     pic 9(8).   *> was binary-long.
     03  oi5-date           binary-long.
     03  filler             pic x(94).
