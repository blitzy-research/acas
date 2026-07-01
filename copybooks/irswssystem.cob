*>*******************************************
*>                                          *
*>  Working Storage for the System File     *
*>   Incomplete Records System ONLY         *
*>                                          *
*>*******************************************
*> 256 bytes (01/03/09)
*> 288 bytes 21/09/10 - added print-spool-name
*> 312 bytes 21/11/11 - Added first-time-flag, two extra vat rates and 15 byte filler
*> 256 bytes 30/11/16 - Removed system file names as using ACAS / tables.
*>                      With this record created by irs.cbl
*>
 01  system-record.
     03  run-date           pic x(8).
     03  suser              pic x(24).
     03  client             pic x(24). *> 56
     03  address-1          pic x(24). *> 80
     03  address-2          pic x(24).
     03  address-3          pic x(24). *> 128
     03  address-4          pic x(24). *> 152
     03  start-date         pic x(8).  *> 160
     03  end-date           pic x(8).  *> 168
      03  system-ops       pic x.     *> 169
     03  pass-word          pic x(4).  *> 173
     03  next-post          pic 9(5).  *> 178
     03  vat-rates.
         05  vat            pic 99v99. *> 182   *> Standard
         05  vat2           pic 99v99. *> 186   *> reduced 1 [not yet used]
         05  vat3           pic 99v99. *> 190   *> reduced 2 [not yet used]
     03  vat-group redefines vat-rates.
         05  vat-psent      pic 99v99    occurs 3.
     03  pass-value         pic 9.
     03  save-sequ          pic 9.     *> 191
     03  system-work-group  pic x(18). *> 209
     03  PL-App-Created     pic x.     *> 210
     03  PL-Approp-AC       pic 9(5).  *> 215
     03  Print-Spool-Name   pic x(32). *> 247
     03  First-Time-FLag    pic 9.     *> 248
     03  filler             pic 9(7).  *> 255
     03  filler             pic x.     *> 256
