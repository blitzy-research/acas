*>*******************************************
*>                                          *
*>  Record Definition For Chk File          *
*>                                          *
*>     Uses Chk-Emp-No as key               *
*>*******************************************
*>  File size 76 bytes.
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 29/10/25 vbc - Created.
*> 02/02/26 vbc - One more Amt occurance = 16.
*> 11/04/26 vbc - Interval x -> 9.
*>
 01  PY-Chk-Record.
     03  Chk-Emp-No        pic 9(7).
     03  Chk-Interval 	   pic 9.
     03  Chk-Check-No      pic 9(6)     comp.
     03  Chk-Amt           pic 9(5)v99  comp-3  occurs 16.
*>
 01  PY-Chk-Hdr-Record.
     03  Chk-Hdr-No               pic 9(7).   *> value zero
     03  Chk-hdr-Interval         pic 9.
     03  Chk-hdr-Apply-No         pic 9(4)    comp.
     03  Chk-hdr-Slow-From-Date   pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-Fast-From-Date   pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-To-Date          pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-Register-Printed pic x.
     03  Chk-hdr-Checks-Printed   pic x.
*> 24 ?
     03  FILLER                   pic x(52).
