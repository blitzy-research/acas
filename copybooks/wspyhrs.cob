*>*******************************************
*>                                          *
*>  Record Definition For Pay Transactions  *
*>           File                           *
*>     Uses Hrs-Key of Emp-No/Hrs-Code as   *
*>                        key               *
*>*******************************************
*>  File size 24 bytes each.
*>
*> 28/10/25 vbc - Created.
*> 07.04.26 vbc - Chg rate to 99 and moved 2 below Emp-No
*>                creating a new key. It is ASSUMED that there is NO
*>                need for more than one entry for a given Trans Code.
*>                OK, will need to have another field for hrs-Serial that
*>                starts at zero AND same size for the header added.
*>                Size increased from 20 to 24 (units).
*>
 01  PY-Pay-Transactions-Record.
     03  Hrs-Key.
         05  Hrs-Emp-No      pic 9(7).
         05  Hrs-Trans-Code  pic 99.
         05  Hrs-Rate redefines Hrs-Trans-Code
                             pic 99.        *> Temporary in case used in error
     03  Hrs-Effective-Date  pic 9(8).      *> ccyymmdd
     03  Hrs-Units           pic s9(5)v99   comp-3.
 *>    03  Hrs-Deleted         pic x.       *> not really NEEDED ???
     03  filler              pic xx.        *> filled to 24 bytes
*>
*> 14 bytes + filler of 6 = 20 to match. the next rec may not be needed ?
*>
 01  PY-Pay-Header-Record.
     03  Hrs-Head-Key        pic 9(9).      *> Always value zero.
     03  Hrs-No-Recs         binary-short unsigned.
     03  Hrs-Batch-No        binary-short unsigned.
     03  Hrs-Proof-No        binary-short unsigned.
     03  Hrs-Proofed         pic x.         *> Space or N and Y for proofed
     03  filler              pic x(8).      *> filled to 24 bytes
*>
