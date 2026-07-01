*>*******************************************
*>                                          *
*>  Working Storage for the Nominal Ledger  *
*>                                          *
*>*******************************************
*> Chgd 16/01/09 money to 99M
*>
 01  NL-Record.
     03  NL-Key.
         05  NL-Owning      pic 9(5).
         05  NL-Sub-Nominal pic 9(5).
     03  NL-Type            pic x.
         88  Owner                   value is "O".
         88  Sub                     value is "S".
     03  NL-Data.
         05  NL-Name        pic x(24).
         05  NL-DR          pic 9(8)v99   comp.
         05  NL-CR          pic 9(8)v99   comp.
         05  NL-DR-Last     pic 9(8)v99   comp  occurs  4.
         05  NL-CR-Last     pic 9(8)v99   comp  occurs  4.
         05  NL-AC          pic x.
     03  filler  redefines  NL-Data.
         05  NL-Pointer     pic 9(5).
*>
