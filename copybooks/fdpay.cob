*>*******************************************
*>                                          *
*>  File Definition For The Payments File   *
*>       For Purchase Ledger.               *
*>*******************************************
*> 237 bytes 26/03/09
*> 26/02/12 chngd bins to comps 4 sql, total size might be wrong
*>
 fd  Pay-File.
*>
 01  Pay-Record.
     03  Pay-Key.
         05  Pay-Supl-Key    pic x(7).
         05  Pay-Nos         pic 99.           *> was comp was binary-char.
     03  Pay-Cont            pic x.
     03  Pay-Date            pic 9(8)  comp.   *> was binary-long
     03  Pay-Cheque          pic 9(8)  comp.   *> was binary-long
     03  Pay-SortCode        pic 9(6)  comp.   *> was binary-long
     03  Pay-Account         pic 9(8)  comp.   *> was binary-long
     03  Pay-Gross           pic s9(7)v99    comp-3.
     03  filler                      occurs 9.
         05  Pay-Folio       pic 9(8)  comp.   *> was binary-long
         05  Pay-Period      pic 99    comp.   *> was binary-char
         05  Pay-Value       pic s9(7)v99    comp-3.
         05  Pay-Deduct      pic s999v99     comp-3.
         05  Pay-Invoice     pic x(10).
*>
