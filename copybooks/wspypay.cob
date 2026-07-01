*>*******************************************
*>                                          *
*>  Record Definition For Pay File          *
*>                                          *
*>     Uses Pay-Emp-No as key               *
*>*******************************************
*>  File size 25 bytes.
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 29/10/25 vbc - Created.
*> 10/04/26 vbc - Added xtra comments.
*> 14/04/26 vbc - Chg Interval to x, Extended to x from xx, Cat to 9 frm xx
*>                & repos size now 24.
*> 22/04/26 vbc - Changed key to have Emp-No and Reporting-Cat.
*>                Above subject to processing for Apply1,2 & 3.
*>                File could be Seqential ?. size = 25
*>
 01  PY-Pay-Record.
     03  Pay-Emp-No-Cat.
         05  Pay-Emp-No               pic 9(7).
         05  Pay-Reporting-Cat        pic 99.             *> 01 - 50 via pyjourn, check its right ? for both see APPLY1, 2 & 3.
     03  Pay-Interval                 pic x.              *> w, m
     03  Pay-Apply-No                 pic 9(4)      comp.
     03  Pay-Eff-Date                 pic 9(8)      comp. *> ccyymmdd - 16
     03  Pay-Units                    pic s9(5)v99  comp-3.  *> 20
     03  Pay-Amt                      pic s9(5)v99  comp-3.  *> 24
     03  Pay-Extended                 pic x.               *> is this right ? N or Y - false / true  = 25
*>
 01  PY-Pay-Header.
     03  Pay-Hdr-No                   pic 9(7).           *> value zero.
     03  Pay-Hdr-Dummy-Cat            pic 99.
     03  Pay-Hdr-Interval             pic x.              *> w, m
     03  Pay-Hdr-Last-Apply-No        pic 9(4)      comp.
     03  Pay-Hdr-Last-Day-of-Last-Per pic 9(8)      comp. *> ccyymmdd
     03  Pay-Hdr-Journal-Printed      pic x.              *> Y / N
     03  FILLER                       pic x(8).           *> 25
