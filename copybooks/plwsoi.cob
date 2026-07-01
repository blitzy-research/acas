*>*********************************************
*>               Purchase    in purchase      *
*>  Working Storage For The Open Item Header  *
*>                                            *
*>*********************************************
*> record size 109 bytes 26/03/09
*> 07/04/09 vbc - Clean up level nos & layout 17/5/13 again
*> 24/04/17 VBC changed size to 113 from 109 after
*>          changing Inv from L-bin to 9(8)
*>          Moved OI-Invoice into OI-Key
*>
 01  OI-Header.
     03  OI-Key.
         05  OI-Customer.
             07  OI-Supplier.
                 09  OI-Nos   Pic X(6).
                 09  OI-Check Pic 9.
         05  OI-Invoice       Pic 9(8).      *> Was Binary-long.  *> and inv was outside the key
     03  OI-Date         Binary-long.
     03  OI-Batch                        Comp.
         05  OI-B-Nos    Pic 9(5).
         05  OI-B-Item   Pic 999.
     03  OI-Type         pic 9.
*>
*>                              ***********************************
*>                              * 1  =  Receipt                   *
*>                              * 2  =  Account Invoice           *
*>                              * 3  =  Cr. Note                  *
*>                              * 4  =  Proforma                  *
*>                              * 5  =  Payment                   *
*>                              * 6  =  Journal-Unapplied Cash    *
*>                              * 7  =  Journal Type B (Not Used) *
*>                              * 9  =  Old Payments              *
*>                              ***********************************
*>
     03  OI-ref          pic x(10).
     03  OI-order        pic x(10).
     03  OI-hold-flag    pic x.
         88  payment-held                      value "H".
     03  OI-unapl        pic x.
     03  filler                          comp-3.
         05  OI-P-C      pic s9(7)v99.
         05  OI-Net      pic s9(7)v99.
         05  OI-Approp redefines OI-Net
                         pic s9(7)v99.
         05  OI-Extra    pic s9(7)v99.
         05  OI-Carriage pic s9(7)v99.
         05  OI-Vat      pic s9(7)v99.
         05  OI-Discount pic s9(7)v99.
         05  OI-E-Vat    pic s9(7)v99.
         05  OI-C-Vat    pic s9(7)v99.
         05  OI-Paid     pic s9(7)v99.
     03  OI-Status       pic 9.
         88  S-Open                            value zero.
         88  S-Closed                          value 1.
     03  OI-Deduct-Days  binary-char.
     03  OI-Deduct-Amt   pic s999v99    comp.
     03  OI-Deduct-Vat   pic s999v99    comp.
     03  OI-Days         binary-char.
     03  OI-CR           binary-long.
     03  OI-Applied      pic x.
     03  OI-Date-Cleared binary-long.
*>
