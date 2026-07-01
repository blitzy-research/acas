*>*******************************************
*>                                          *
*>  Working Storage for the Defaults Record *
*>      For GL                              *
*>*******************************************
*> Record 224 bytes but written as 1024 (system-record size) 07/11/10
*>   This is NOT the same as for IRS as DEF-ACAS is different size
*> 05/11/16 vbc - Changed to 32 (from 33).
*>    Record size 224 bytes from 231.
*>  Brought back to 33 and 231 bytes for posting program to
*>  match up with IRS change 01/05/18 in irs030.
*> included filler 15/10/25 now = 1024 as created by sys002
*>
 01  Default-Record.
     03  Def-Group                  occurs 33.
         05  Def-Acs         pic 9(4)v99 comp.
         05  Def-Codes       pic xx.
         05  Def-Vat         pic x.
     03  filler              pic x(793).   *>  total 1024
*>
