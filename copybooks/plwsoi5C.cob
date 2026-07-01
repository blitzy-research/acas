*>*******************************************
*>          WS from the                     *
*>  File Definition For The Open Item File  *
*>       Rec size 113 Bytes.                *
*>*******************************************
*>     record size 109 bytes 26/03/09
*> 24/04/17 VBC changed size to 113 from 109 after
*>          changing Inv from L-bin to 9(8)
*>
 01  WS-OTM5-Record         pic x(113).
*>
 01  Open-Item-Record-5    redefines WS-OTM5-Record.
     03  oi5-key.
         05 oi5-supplier    pic x(7).
         05 oi5-invoice     PIC 9(8).        *> Was binary-long.  *> 15
     03  oi5-date           binary-long.     *> 19
     03  filler             pic x(94).       *> 113
*>
 copy "plwsoi.cob" replacing ==OI-Header==
                     by ==OI-Header redefines WS-OTM5-Record==.
*>
