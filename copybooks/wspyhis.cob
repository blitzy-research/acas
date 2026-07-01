*>*******************************************
*>                                          *
*>  Record Definition For Employee          *
*>       History  File                      *
*>     Uses His-Emp-No as key               *
*>*******************************************
*>  File size 328 bytes. 27/03/26
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 29/10/25 vbc - Created.
*> 09/12/25 vbc - Added xtras DEDs for QTD & YTD
*> 17/03/26 vbc - MCare added for QTD & YTD.
*> 27/03/26 vbc - Change field order mcare, other-ded
*>
 01  PY-History-Record.
     03  His-Emp-No                    pic 9(7)   comp.
     03  His-QTD                                  comp-3.
         05  His-QTD-Income-Taxable    pic 9(7)v99.
         05  His-QTD-Other-Taxable     pic 9(7)v99.
         05  His-QTD-Other-NonTaxable  pic 9(7)v99.
         05  His-QTD-Fica-Taxable      pic 9(7)v99.
         05  His-QTD-Tips              pic 9(7)v99.
         05  His-QTD-Net               pic 9(7)v99.
         05  His-QTD-EIC               pic 9(7)v99.
         05  His-QTD-FWT               pic 9(7)v99.
         05  His-QTD-SWT               pic 9(7)v99.
         05  His-QTD-LWT               pic 9(7)v99.
         05  His-QTD-FICA              pic 9(7)v99.
         05  His-QTD-SDI               pic 9(7)v99.
         05  His-QTD-MCare             pic 9(7)v99.
         05  His-QTD-Other-Ded         pic 9(7)v99.
         05  His-QTD-Sys               pic 9(7)v99  occurs 5.
         05  His-QTD-Emp               pic 9(7)v99  occurs 3.
         05  His-QTD-Units             pic 9(7)v99  occurs 4.
         05  His-QTD-Extras            pic 9(7)v99  occurs 5. *> extra state/fed deductions enough ?
     03  His-YTD                                  comp-3.
         05  His-YTD-Income-Taxable    pic 9(7)v99.
         05  His-YTD-Other-Taxable     pic 9(7)v99.
         05  His-YTD-Other-NonTaxable  pic 9(7)v99.
         05  His-YTD-Fica-Taxable      pic 9(7)v99.
         05  His-YTD-Tips              pic 9(7)v99.
         05  His-YTD-Net               pic 9(7)v99.
         05  His-YTD-EIC               pic 9(7)v99.
         05  His-YTD-FWT               pic 9(7)v99.
         05  His-YTD-SWT               pic 9(7)v99.
         05  His-YTD-LWT               pic 9(7)v99.
         05  His-YTD-FICA              pic 9(7)v99.
         05  His-YTD-SDI               pic 9(7)v99.
         05  His-YTD-MCare             pic 9(7)v99.
         05  His-YTD-Other-Ded         pic 9(7)v99.
         05  His-YTD-Sys               pic 9(7)v99  occurs 5.
         05  His-YTD-Emp               pic 9(7)v99  occurs 3.
         05  His-YTD-Units             pic 9(7)v99  occurs 4.
         05  His-YTD-Extras            pic 9(7)v99  occurs 5. *> extra state/fed deductions enough ?
     03  filler                        pic x(4).
*>
*>   IS this header rec needed (Last-To-Date ? )
*>
 01  PY-History-Header.
     03  Hdr-His-No                    pic 9(7)   comp.   *> value zero.
     03  Hdr-His-Last-To-Date          pic 9(8)   comp.   *> ccyymmdd
     03  FILLER                        pic x(320).        *> Expansion ?
*>
