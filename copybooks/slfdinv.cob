*>*******************************************
*>            Sales                         *
*>  File Definition For The Invoice File    *
*>       Also See Fdinv2.Cob                *
*>*******************************************
*> record size 129 ?? bytes 03/03/09
*>     -  -  - 137 18/01/17 - size write but layout not.
*>     -  -  - 137 25/01/17 - same.
*>  Item-Nos changed from bin-char to pic 99. rec size the same.
*>
*> Taken from the SL copy in that src dir and prefixed by 'sl'.
*>
 fd  Invoice-File.
*>
 01  Invoice-Record.
    02  Inv-Prime.                    *> 42 bytes.
     03  Invoice-Key.
         05  Invoice-Nos    pic 9(8).
         05  Item-Nos       pic 99.
     03  Invoice-Customer   pic x(7).
     03  Invoice-Date       binary-long.
     03  filler             pic x(10).
     03  Invoice-Type       pic 9.
     03  filler             pic x(10).
   02  Inv-Sub-Prime.                 *> 95 bytes.
     03  filler             pic x(95).
*>
