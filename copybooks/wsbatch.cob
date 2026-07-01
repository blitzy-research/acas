*>*****************************************
*>                                        *
*>  WS Definition for the Batch file      *
*>   taken from fdBatch                   *
*>                                        *
*>*****************************************
*> 96 bytes 26/03/09
*> 98 bytes 20/12/11 (no, dont understand as I count 96)
*>   but function length (Batch-record) says 98?
*> 06/01/17 vbc - WS Batch taken from fdBatch for RDB.
*> 09/01/17 vbc - Added batch-key9.
*>
 01  WS-Batch-Record.
     03  WS-Batch-Key.
         05  WS-Ledger          pic 9.
             88  GL-Batch                   value 1.
             88  PL-Batch                   value 2.
             88  SL-Batch                   value 3.
         05  WS-Batch-Nos       pic 9(5).
     03  WS-Batch-Key9 redefines WS-Batch-Key
                             pic 9(6).
*>
     03  Items               pic 99.
*>
     03  Batch-Status        pic 9.
         88  Status-Open                    value 0.
         88  Status-Closed                  value 1.
*>
     03  Cleared-Status      pic 9.
         88  Waiting                        value 0.
         88  Processed                      value 1.
         88  Archived                       value 2.
*>
     03  Bcycle              pic 99.
     03  Dates.
         05  Entered         binary-long.
         05  Proofed         binary-long.
         05  Posted          binary-long.
         05  Stored          binary-long.
     03  Amounts                         comp-3.
         05  Input-Gross     pic 9(9)v99.
         05  Input-Vat       pic 9(9)v99.
         05  Actual-Gross    pic 9(9)v99.
         05  Actual-Vat      pic 9(9)v99.
     03  Description         pic x(24).
*>
     03  posting-data.
         05  bDefault        pic 99.
         05  Convention      pic xx.
         05  Batch-Def-AC    pic 9(6).
         05  Batch-Def-PC    pic 99.
         05  Batch-Def-Code  pic xx.
         05  Batch-Def-Vat   pic x.
     03  Batch-Start         pic 9(5).
*>
