*>*******************************************
*>                                          *
*>  Working Storage for the Defaults File   *
*>                                          *
*>*******************************************
*> rec 256 bytes 15/02/09
*> Rec 264 bytes 06/05/18 - to support temp. default 33 in postings (irs030).
 01  Default-Record.
     03  Def-Group                  occurs 33.
         05  Def-Acs         pic 9(5).
         05  Def-Codes       pic xx.
         05  Def-Vat         pic x.
*>
