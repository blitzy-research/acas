*>*******************************************
*>                                          *
*>  WS Definition For The GL Posting Record *
*>                                          *
*>*******************************************
*> 98 bytes 26/03/09
*> 96 bytes 20/12/11 (leading sign removed)
*> 04/01/17 - created wspost.cob from fdpost.cob for
*>            GL.
*> 06/01/17 - Added WS-P-rrn to replace relative processing.
*>
 01  WS-Posting-Record.
     03  WS-Post-rrn        pic 9(5).
     03  WS-Post-Key.
         05  Batch       pic 9(5).
         05  Post-Number pic 9(5).
     03  Post-Code       pic xx.      *> 12
     03  Post-Date       pic x(8).    *> 20
     03  Post-DR         pic 9(6).    *> 26
     03  DR-PC           pic 99.
     03  Post-CR         pic 9(6).    *> 34
     03  CR-PC           pic 99.      *> 36
     03  Post-Amount     pic s9(8)v99.  *> 46
     03  Post-Legend     pic x(32).     *> 76
     03  Vat-AC          pic 9(6).      *> 82
     03  Vat-PC          pic 99.
     03  Post-Vat-Side   pic xx.        *> 86
     03  Vat-Amount      pic s9(8)v99.  *> 96
*>
