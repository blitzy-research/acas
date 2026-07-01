*>*******************************************
*>                                          *
*> 3 tables LWT, SWT, stax should be using  *
*>    just the one table as all are present *
*>                                          *
*>  Record-Definition For SWT Tax File      *
*>                                          *
*>  agency% is 1 if SWT                     *
*>         and 2 if LWT                     *
*>             3 if CAL Single              *
*>             4 if CAL Married             *
*>             5 if CAL Head                *
*>  num.entries refers to the number of     *
*>  entries in withholding table  NEEDED ?  *
*>                                          *
*>     Sequential file                      *
*>*******************************************
*>  File size 608 bytes.
*>
*> THESE FIELDs DEFINITIONS WILL NEED CHANGING
*>
*> 30/10/25 vbc - Created.
*>
 01  PY-SWT-Tax-Record.
     03  PY-SWT-Withhold-Deduction-Amount   pic 9(6)      comp.               *> (agency)
     03  PY-SWT-Withhold-Num-Entries        pic 9(6)      comp.               *> %(agency) NEEDED ?
     03  PY-SWT-Agency                                    comp-3  occurs 5.
         05  PY-SWT-Withhold-Cutoff         pic s9(5)v99          occurs 15.  *> (,agency)
         05  PY-SWT-Withhold-Percent        pic s9(5)v99          occurs 15.  *> (,agency)
*>
