*>*******************************************
*>                                          *
*>  Working Storage for the Posting File    *
*>                                          *
*>*******************************************
*>> Chg 16/01/09 money to 9M
*>
 01  Posting-Record.
     03  Post-Key        pic 9(5).
     03  Post-Code       pic xx.
     03  Post-Date       pic x(8).
     03  Post-DR         pic 9(5).
     03  Post-CR         pic 9(5).
     03  Post-Amount     pic s9(7)v99  sign is leading.
     03  Post-Legend     pic x(32).
     03  Vat-AC-Def      pic 99.
     03  Post-Vat-Side   pic xx.
     03  Vat-Amount      pic s9(7)v99   sign is leading.
*>
