*>
*> Chg'd 16/01/09 money to 99M
*>
 01  Record-1.
     03  Key-1.
         05  Owning      pic 9(5).
         05  Sub-Nominal pic 9(5).
     03  Tipe            pic x.
         88 NL-Sub-AC               value "S".
     03  Record-Data.
         05  NL-Name     pic x(24).
         05  DR          pic 9(8)v99   comp.
         05  CR          pic 9(8)v99   comp.
         05  DR-Last     pic 9(8)v99   comp  occurs  4.
         05  CR-Last     pic 9(8)v99   comp  occurs  4.
         05  AC          pic x.
     03  filler  redefines  Record-Data.
         05  Rec-Pointer pic 9(5).
*>
