*>*******************************************
*>              WS from the                 *
*>  File Definition For The Open Item File  *
*>      Rec Size 118 Bytes                  *
*>*******************************************
*> 08/02/17 VBC changed size to 118 (from 114) after
*>          changing Inv from Bin to 9(8)
*>
 01  WS-OTM3-Record         pic x(118).
*>
 01  Open-Item-Record-3  redefines WS-OTM3-Record.
     03  OI3-Key.
         05 OI3-Customer    pic x(7).
         05 OI3-Invoice     PIC 9(8).     *> Was binary-long.   *> 15
     03  OI3-Date           binary-long.   *> 19
     03  filler             pic x(99).     *> 118
*>
 copy "slwsoi.cob" replacing ==OI-Header==
               by ==OI-Header redefines WS-OTM3-Record==.
*>
