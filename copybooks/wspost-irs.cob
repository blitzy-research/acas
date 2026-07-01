*>*******************************************
*>                                          *
*>  File Definition for irs Postings File   *
*>   within IRS FROM SL (SL100) & PL100     *
*>            SL060, PL060 & irs030         *
*> This is NOT the same as the internal IRS *
*>   posting file                           *
*>*******************************************
*> Chg 16/01/09 money to 9M
*>  again 28/03/09 for IRS-batch-item
*>  Taken from the fd copybook 24/11/16
*>
 01  WS-IRS-Posting-Record.
     03  WS-IRS-Post-Key.
         05  WS-IRS-Batch       pic 9(5).
         05  WS-IRS-Post-Number pic 9(5).
     03  WS-IRS-Post-Code       pic xx.
     03  WS-IRS-Post-Date       pic x(8).
     03  WS-IRS-Post-DR         pic 9(5).
     03  WS-IRS-Post-CR         pic 9(5).
     03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.
     03  WS-IRS-Post-Legend     pic x(32).
     03  WS-IRS-Vat-AC-Def      pic 99.
     03  WS-IRS-Post-Vat-Side   pic xx.
     03  WS-IRS-Vat-Amount      pic s9(7)v99   sign leading.
*>
