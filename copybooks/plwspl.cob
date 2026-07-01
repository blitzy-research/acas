*>**********************************************
*>         WS definition for                   *
*>  File Definition For The Purchase Ledger    *
*>                                             *
*>**********************************************
*> rec size 299 bytes  26/03/09
*> rec size 300 bytes  22/12/11
*> rec size 302 bytes  4/03/2012 checked by COBSTRUCT (PRIMA tool)
*> 13/09/15 changed 4 SQL Mig.
*>  taken from fdpl.cob 23/07/16
*> 15/01/18 Added Purch-Stats-Date with filler space.
*>
*> fd  Purchase-File.
*>
 01  WS-Purch-Record.
     03  WS-Purch-Key        pic x(7).   *> renamed but as Purch-key.
*>     03  filler   redefines WS-Purch-Key.
*>         05  array-k         pic x  occurs 6.
*>         05  check-digit     pic 9.
     03  purch-status        pic 9.
         88  supplier-live               value 1.
         88  supplier-dead               value 0.
     03  Purch-Notes-Tag     pic 9.
     03  Purch-Name          pic x(30).
     03  Purch-Address.
         05  purch-addr1     pic x(48).
         05  purch-addr2     pic x(48).
     03  purch-phone         pic x(13).
     03  purch-ext           pic x(4).
     03  purch-fax           pic x(13).
     03  purch-email         pic x(30).
     03  purch-discount      pic 99v99      comp.
     03  purch-credit        binary-char.
     03  purch-sortcode      binary-long.
     03  purch-accountno     binary-long.
     03  purch-limit         binary-long.
     03  purch-activety      binary-long.
     03  purch-last-inv      binary-long.
     03  purch-last-pay      binary-long.
     03  purch-average       binary-long.
     03  purch-create-date   binary-long.
     03  purch-pay-activety  binary-long.
     03  purch-pay-average   binary-long.
     03  purch-pay-worst     binary-long.
     03  Purch-Current       pic s9(8)v99   comp-3.
     03  purch-last          pic s9(8)v99   comp-3.
     03  Quarters.
         05  Turnover-q1     pic s9(8)v99   comp-3.
         05  Turnover-q2     pic s9(8)v99   comp-3.
         05  Turnover-q3     pic s9(8)v99   comp-3.
         05  Turnover-q4     pic s9(8)v99   comp-3.
     03  filler redefines Quarters.
         05  Pturnover-Q     pic s9(8)v99   comp-3 occurs  4.
     03  Purch-Unapplied     pic s9(8)v99   comp-3.
     03  Purch-Stats-Date    pic 9(4).             *> added 03/06/23 from wspl.
     03  filler              pic x(12).
*>
