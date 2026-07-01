*>*********************************************
*>            Sales   in sales                *
*>  Working Storage For The Open Item Header  *
*>                                            *
*>*********************************************
*> record size 118 bytes 08/02/17 inv bin -> 9(8)
*>
 01  OI-Header.
     02  OI-key.
         03  OI-Customer.
             05  OI-Nos       pic x(6).
             05  OI-Check     pic 9.
         03  OI-Invoice       pic 9(8).   *> was binary-long.
     02  filler.
         03  OI-Date          binary-long.
         03  OI-Batch                        comp.
             05  OI-B-Nos     pic 9(5).
             05  OI-B-Item    pic 999.
         03  OI-Type          pic 9.
*>
*>                              ***********************************
*>                              *  1  =  Receipt                  *
*>                              *  2  =  Account                  *
*>                              *  3  =  Cr. Note                 *
*>                              *  4  =  Proforma (Not used)      *
*>                              *  5  =  Payment                  *
*>                              *  6  =  Journal-Unapplied Cash   *
*>                              *  7  =  Journal Type B (Not Used)*
*>                              *  9  =  Old Payments             *
*>                              ***********************************
*>
         03  OI-Description   pic x(25).
         03  OI-Hold-flag     pic x.                 *> Q(uery)
         03  OI-Unapl         pic x.
         03  filler                          comp-3.
             05  OI-P-C       pic s9(7)v99.
             05  OI-Net       pic s9(7)v99.
             05  OI-Approp redefines OI-Net
                              pic s9(7)v99.
             05  OI-Extra     pic s9(7)v99.
             05  OI-Carriage  pic s9(7)v99.
             05  OI-Vat       pic s9(7)v99.
             05  OI-Discount  pic s9(7)v99.
             05  OI-E-Vat     pic s9(7)v99.
             05  OI-C-Vat     pic s9(7)v99.
             05  OI-Paid      pic s9(7)v99.
         03  OI-Status        pic 9.
             88  S-Open                         value zero.
             88  S-Closed                       value 1.      *> Paid
         03  OI-Deduct-Days   binary-Char.
         03  OI-Deduct-Amt    pic s999v99    comp.
         03  OI-Deduct-Vat    pic s999v99    comp.
         03  OI-Days          binary-Char.
         03  OI-Cr            binary-long.
         03  OI-Applied       pic x.
         03  OI-Date-Cleared  binary-long.
*>
