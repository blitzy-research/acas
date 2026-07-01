*>*******************************************
*>                                          *
*>    WS definition for the General/Nominal *
*>             Ledger file                  *
*>                                          *
*>*******************************************
*> 27/01/09 vbc - file-id to select
*> 04/01/17 vbc - Taken from fdledger.
*> 07/01/17 vbc - Added new field ledger-key9.
*> 31/01/18 vbc - Resized to 126 bytes.
*>
 01  WS-Ledger-Record.
     03  WS-Ledger-Key.
         05  WS-Ledger-Nos    pic 9(6).
*>*******************************************
         05  filler  redefines  WS-Ledger-Nos.
             07  Ledger-n  pic 9(4).
             07  Ledger-s  pic 9(2).
*>*******************************************
         05  Ledger-PC     pic 9(2).
     03  WS-Ledger-Key9 redefines WS-Ledger-Key
                           pic 9(8).
     03  Ledger-Type       pic 9.
     03  Ledger-Place      pic x.
     03  Ledger-Level      pic 9.
     03  filler            pic x(5).
     03  Ledger-Name       pic x(24).
     03  Ledger-Balance    pic s9(8)v99   comp-3.
     03  Ledger-Last       pic s9(8)v99   comp-3.
     03  Quarters.
         05  Ledger-Q1     pic s9(8)v99   comp-3.
         05  Ledger-Q2     pic s9(8)v99   comp-3.
         05  Ledger-Q3     pic s9(8)v99   comp-3.
         05  Ledger-Q4     pic s9(8)v99   comp-3.
     03  filler redefines Quarters.
         05  Ledger-Q      pic s9(8)v99   comp-3   occurs  4.
     03  filler            pic x(50).
