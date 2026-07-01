*>*******************************************
*>                                          *
*>  File Definition For The Open Item File  *
*>      Rec Size 118 Bytes                  *
*>*******************************************
*> updated 20/08/17 114 -> 118.
*>
 fd  Open-Item-File-3.
*>
 01  Open-Item-Record-3.
     03  OI3-Key.
         05 OI3-Customer    pic x(7).
         05 OI3-Invoice     pic 9(8).   *> was binary-long.   *> 11
     03  OI3-Date           binary-long.   *> 19 was 15
     03  filler             pic x(99).     *> 118 was 114
*>
