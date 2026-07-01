*>*******************************************
*>                                          *
*>  Record-Definition For California File   *
*>                                          *
*>     Sequential file                      *
*>*******************************************
*>  File size 116 bytes.
*>
*> THESE FIELDs DEFINITIONS WILL NEED CHANGING
*>
*> 30/10/25 vbc - Created-
*>
 01  PY-California-Tax-Record.
     03  PY-Calx-Cal-Estimated-Ded-Amt  pic s9(5)v99   comp-3.
     03  PY-Calx-Cal-Low-Income-Exempt  pic s9(5)v99   comp-3   occurs 4.
     03  PY-Calx-Cal-Standard-Deduction pic s9(5)v99   comp-3   occurs 4.
     03  PY-Calx-Cal-Tax-Credits                       comp-3   occurs 10.
         05  PY-Calx-Cal-Tax-Credit     pic s9(5)v99            occurs 2.
*>
