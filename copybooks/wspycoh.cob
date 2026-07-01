*>*******************************************
*>                                          *
*>  Record Definition For Company History   *
*>              File                        *
*>     Uses RRN         as  relative key    *
*>   BUT could be Apply-No                  *
*>*******************************************
*>  File size 612 bytes
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 30/10/25 vbc - Created.
*> 04/12/25 vbc - Some fields chgd to 9 from x etc & get rid of tabs.
*> 27/03/26 vbc - + 60 bytes new fields added (mcare & extras)
*> 04/04/26 vbc - Extra 40 bytes for Other-Ded from 1 to occ 5.
*>                No doubt more may be needed.
*>
 01  PY-Comp-Hist-Record.
  *>   03  RRN                      pic 9.                 *> Possibly needs to use Apply-No
     03  Coh-Interval                 pic x.
     03  Coh-Starting-Up              pic x.              *> on 1st starting set to Y, after 1st apply set to N but is this CORRECT ?
*>                                                           Should the tests relate to specific Emp His / Emp records ?
*>
     03  Coh-Last-Apply-No            pic 9(4) comp.      *> Possibly the KEY and not RRN then can be removed if multiple records??
     03  Coh-QTD                                  comp-3.
         05  Coh-QTD-Income-Taxable   pic 9(7)v99.
         05  Coh-QTD-Other-Taxable    pic 9(7)v99.
         05  Coh-QTD-Other-NonTaxable pic 9(7)v99.
         05  Coh-QTD-Fica-Taxable     pic 9(7)v99.
         05  Coh-QTD-Tips             pic 9(7)v99.
         05  Coh-QTD-Net              pic 9(7)v99.
         05  Coh-QTD-Eic-Credit       pic 9(7)v99.
         05  Coh-QTD-Fwt-Liab         pic 9(7)v99.
         05  Coh-QTD-Swt-Liab         pic 9(7)v99.
         05  Coh-QTD-Lwt-Liab         pic 9(7)v99.
         05  Coh-QTD-Fica-Liab        pic 9(7)v99.
         05  Coh-QTD-Sdi-Liab         pic 9(7)v99.
         05  Coh-QTD-Co-Futa-Liab     pic 9(7)v99.
         05  Coh-QTD-Co-Fica-Liab     pic 9(7)v99.
         05  Coh-QTD-Co-Sui-Liab      pic 9(7)v99.
         05  Coh-QTD-MCare            pic 9(7)v99.  *> New
         05  Coh-QTD-Other-Ded        pic 9(7)v99   occurs 5.
         05  Coh-QTD-Sys              pic 9(7)v99   occurs 5.
         05  Coh-QTD-Emp              pic 9(7)v99   occurs 3.
         05  Coh-QTD-Units            pic 9(7)v99   occurs 4.
         05  Coh-QTY-Extras           pic 9(7)v99   occurs 5. *> NEW extra state/fed deductions enough ?
         05  Coh-QTD-Comp-Time-Earned pic 9(7)v99.
         05  Coh-QTD-Comp-Time-Taken  pic 9(7)v99.
         05  Coh-QTD-Vac-Earned       pic 9(7)v99.
         05  Coh-QTD-Vac-Taken        pic 9(7)v99.
         05  Coh-QTD-Sl-Earned        pic 9(7)v99.
         05  Coh-QTD-Sl-Taken         pic 9(7)v99.
     03  Coh-YTD                                  comp-3.
         05  Coh-YTD-Income-Taxable   pic 9(7)v99.
         05  Coh-YTD-Other-Taxable    pic 9(7)v99.
         05  Coh-YTD-Other-NonTaxable pic 9(7)v99.
         05  Coh-YTD-Fica-Taxable     pic 9(7)v99.
         05  Coh-YTD-Tips             pic 9(7)v99.
         05  Coh-YTD-Net              pic 9(7)v99.
         05  Coh-YTD-Eic-Credit       pic 9(7)v99.
         05  Coh-YTD-Fwt-Liab         pic 9(7)v99.
         05  Coh-YTD-Swt-Liab         pic 9(7)v99.
         05  Coh-YTD-Lwt-Liab         pic 9(7)v99.
         05  Coh-YTD-Fica-Liab        pic 9(7)v99.
         05  Coh-YTD-Sdi-Liab         pic 9(7)v99.
         05  Coh-YTD-Co-Futa-Liab     pic 9(7)v99.
         05  Coh-YTD-Co-Fica-Liab     pic 9(7)v99.
         05  Coh-YTD-Co-Sui-Liab      pic 9(7)v99.
         05  Coh-QTD-MCare            pic 9(7)v99.    *> New
         05  Coh-YTD-Other-Ded        pic 9(7)v99   occurs 5.
         05  Coh-YTD-Sys              pic 9(7)v99   occurs 5.
         05  Coh-YTD-Emp              pic 9(7)v99   occurs 3.
         05  Coh-YTD-Units            pic 9(7)v99   occurs 4.
         05  Coh-YTY-Extras           pic 9(7)v99   occurs 5. *> NEW extra state/fed deductions enough ?
         05  Coh-YTD-Comp-Time-Earned pic 9(7)v99.
         05  Coh-YTD-Comp-Time-Taken  pic 9(7)v99.
         05  Coh-YTD-Vac-Earned       pic 9(7)v99.
         05  Coh-YTD-Vac-Taken        pic 9(7)v99.
         05  Coh-YTD-Sl-Earned        pic 9(7)v99.
         05  Coh-YTD-Sl-Taken         pic 9(7)v99.
     03  Coh-Date-Tax.
         05  Coh-Date                 pic 9(8)     comp    occurs 12.   *>  ccyymmdd
         05  Coh-Tax                  pic 9(7)v99  comp-3  occurs 12.
     03  Coh-Q-Taxes.
         05  Coh-Q-Tax                pic 9(7)v99  comp-3  occurs 4.
         05  Coh-Q-Fica-Tax           pic 9(7)v99  comp-3  occurs 4.
         05  Coh-Q-Co-Futa-Liab       pic 9(7)v99  comp-3  occurs 4.
     03  Coh-All-Q-Taxes redefines Coh-Q-Taxes.    *> Used in py930 for data I/P and ???
         05  Coh-All-Q-Tax            pic 9(7)v99  comp-3  occurs 12.
*>
