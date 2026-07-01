*>**********************************************
*>                                             *
*>    WS Definition For The Purchase Ledger    *
*>               Record.                       *
*>**********************************************
*> rec size 299 bytes  26/03/09
*> rec size 300 bytes  22/12/11
*> rec size 302 bytes  4/03/2012 checked by COBSTRUCT (PRIMA tool)
*> 13/09/15 changed 4 SQL Mig.
*>  taken from fdpl.cob 23/07/16
*> 15/01/18 Added Purch-Stats-Date with filler space.
*>
 01  WS-Purch-Record.
     03  WS-Purch-Key        pic x(7).
*>     03  filler   redefines WS-Purch-Key.
*>         05  Array-k         pic x  occurs 6.
*>         05  Check-Digit     pic 9.
     03  Purch-Status        pic 9.
         88  Supplier-live               value 1.
         88  Supplier-dead               value 0.
     03  Purch-Notes-Tag     pic 9.
     03  Purch-Name          pic x(30).
     03  Purch-Address.
         05  Purch-Addr1     pic x(48).
         05  Purch-Addr2     pic x(48).
     03  Purch-Phone         pic x(13).
     03  Purch-Ext           pic x(4).
     03  Purch-Fax           pic x(13).
     03  Purch-Email         pic x(30).
     03  Purch-Discount      pic 99v99      comp.    *> RDB comp-3
     03  Purch-Credit        binary-char.  *> were pic 99
     03  Purch-SortCode      binary-long.  *> all these were pic 9(8) comp
     03  Purch-Accountno     binary-long.
     03  Purch-Limit         binary-long.
     03  Purch-Activety      binary-long.
     03  Purch-Last-inv      binary-long.
     03  Purch-Last-pay      binary-long.
     03  Purch-Average       binary-long.
     03  Purch-Create-Date   binary-long.
     03  Purch-Pay-Activety  binary-long.
     03  Purch-Pay-Average   binary-long.
     03  Purch-Pay-Worst     binary-long.
     03  Purch-Current       pic s9(8)v99   comp-3.
     03  Purch-Last          pic s9(8)v99   comp-3.
     03  Quarters.
         05  Turnover-q1     pic s9(8)v99   comp-3.
         05  Turnover-q2     pic s9(8)v99   comp-3.
         05  Turnover-q3     pic s9(8)v99   comp-3.
         05  Turnover-q4     pic s9(8)v99   comp-3.
     03  filler redefines Quarters.
         05  PTurnover-q     pic s9(8)v99   comp-3 occurs  4.
     03  Purch-Unapplied     pic s9(8)v99   comp-3.
     03  Purch-Stats-Date    pic 9(4).             *> added 15/01/18.
     03  filler              pic x(12).
*>
