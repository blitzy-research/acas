       >>source free
*> PROGRAM NOT NEEDED unless using very old versions of ACAS.
*>
*>  NEEDS TESTING and note cobc command line for this one:
*>
*>  ALSO OTM3 file needs converting and possibly OTM5.
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>  cobc -x -fstop-literal-statement=ok acasconvert3.cbl
*>
*>
 identification division.
 program-id.                 acasconvert3.
*>Author.                    Vincent B Coen, FBCS, FIDM, FIDPM. 02/05/09.
*>
*>Security.                  Copyright (C) 1982-2026, Vincent Bryan Coen.
*>                           Distributed under the GNU General Public License
*>                           v2.0. Only. See the file COPYING for details.
*>
*>Purpose.                   Convert ACAS SL Invoice file/s.
*>                           replacing second element of key from binary
*>                                to pic99.
*>
*>     This program and others starting with acasconvertn (n = 2 thru 99) is
*>     for updating the data file layouts from one version to the next when
*>     required.  File layout changes are kept to a minimum but some times
*>     it is necessary.
*>
*>     This program updates records in the invoice file only.
*>
*>     CHECK THAT THE 'OLD' INVOICE RECORD/S LAYOUT MATCHES YOUR CURRENT ONE
*>     IF NOT REPLACE WITH YOUR CURRENT ONE COPY & PASTE FROM COPYBOOKS
*>      IN THE SOURCE DIRECTORY of your old current version which you should
*>    have renamed as ACAS-3.01 [ if using the previous version ].
*>
*>
*>   WARNING:
*>    TAKE A BACK UP OF YOUR DATA FILES BEFORE RUNNING - twice.
*>    TAKE A BACK UP OF YOUR DATA FILES BEFORE RUNNING - YES twice.
*>
*>   IMPORTANT.
*>    Test with cobc flag -Wcorresponding when compiling
*>     E.g., cobc -x -Wcorresponding acasconvert2.cbl
*>
*>     If any fields or other warning are reported investigate before using.
*>
*> Updates:
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>*************************************************************************
*>
*> Copyright Notice.
*>*****************
*>
*> This file/program is part of the Applewood Computers Accounting System
*>   and is copyright (c) Vincent B Coen. 1976 - 2026 and later.
*>
*> This program is free software; you can redistribute it and/or modify it
*> under the terms of the GNU General Public License as published by the
*> Free Software Foundation; version 2 ONLY.
*>
*> Cobxref is distributed in the hope that it will be useful, but WITHOUT
*> ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
*> FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
*> for more details. If it breaks, you own both pieces but I will endeavour
*> to fix it, providing you tell me about the problem.
*>
*> You should have received a copy of the GNU General Public License along
*> with ACAS; see the file COPYING.  If not, write to the Free Software
*> Foundation, 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
*>*************************************************************************
*>
 environment division.
 configuration section.
 source-computer.        Linux.
 object-computer.        Linux.
 input-output section.
 file-control.
 copy "slselinv.cob".    *> New
 copy "slselinv.cob"  replacing Invoice-File by Old-Invoice-File
                                File-16      by Old-File-16
                                Invoice-Key  by Old-Invoice-Key.
*>
 data division.
 file section.
 copy "slfdinv2.cob".          *> Updated - New O/P- MMORE
*>
*>  Now for the OLD
*>
 fd  Old-Invoice-File.
*>
 01  Old-Invoice-Record.                  *> 137
    02  Old-Inv-Prime.                    *> 41 bytes.
     03  Old-Invoice-Key.
         05  Old-Invoice-Nos    pic 9(8).
         05  Old-Item-Nos       binary-char.
     03  Old-Invoice-Customer   pic x(7).
     03  Old-Invoice-Date       binary-long.
     03  filler             pic x(10).
     03  Old-Invoice-Type       pic 9.
     03  filler             pic x(10).
   02  Old-Inv-Sub-Prime.                 *> 96 bytes.
     03  filler             pic x(96).
*>

 working-storage section.
 77  prog-name          pic x(18)  value "IRSconv3 (3.3.00)".
 01  fs-reply           pic 99.
 01  rec-count          pic 9(4)   value zero.
 01  A                  pic s9(4)     comp    value zero.
 01  B                  pic s9(4)     comp    value zero.
 01  Rrn                binary-long.
 01  Display-Blk        pic x(78)             value spaces.
 01  Old-File-16        pic x(16)     value "invoice.dat.OLD".
*>
 01  Error-Messages.
     03  SY103    pic x(22) value "SY103 Rewrite Err 1 = ".
     03  SY104    pic x(26) value "SY104 Fix and Press Enter".
*>
 copy "wsnames.cob".
*>
*>    THIS IS THE OLD RECORD LAYOUT in Working Storage.
*>
*>*******************************************
*>        wsinv.cob copied to copybooks as  *
*>         slwsinv.cob.                     *
*>                                          *
*>              In Sales                    *
*>  Working Storage For The Invoice Header  *
*>      Also See FDinv2.Cob                 *
*>*******************************************
*>   size 129 bytes 09/03/09
*>   size 134 bytes 24/03/12
*>   size 137 bytes 18/01/17
*> WARNING UPDATE all layouts for 5 byte increase (extra statuses)
*>
 01  SInvoice-Header.                         *> 137 bytes 18/01/17
   02 sih-prime.                              *> 41 bytes
     03  WS-Invoice-Key.
         05  sih-invoice   pic 9(8).
         05  sih-test      binary-char  value zero.  *>>> needs to be pic 99
     03  sih-customer.
         05  sih-nos       pic x(6).
         05  sih-check     pic 9.
     03  sih-date          binary-long.
     03  sih-order         pic x(10).
     03  sih-type          pic 9.
     03  sih-ref           pic x(10).
   02 Sih-Sub-Prime.                          *> 96 bytes
     03  sih-description   pic x(32).
     03  sih-fig                          comp-3.
         05  sih-p-c       pic s9(7)v99.
         05  sih-net       pic s9(7)v99.
         05  sih-extra     pic s9(7)v99.
         05  sih-carriage  pic s9(7)v99.
         05  sih-vat       pic s9(7)v99.
         05  sih-discount  pic s9(7)v99.
         05  sih-e-vat     pic s9(7)v99.
         05  sih-c-vat     pic s9(7)v99.
     03  sih-status        pic x.
         88  pending                           value "P".
         88  invoiced                          value "I".
         88  sapplied                          value "Z".
     03  sih-status-P      pic x.         *> Pick list Printed           space or P
     03  sih-status-L      pic x.         *> Invoice Printed             space or L
     03  sih-status-C      pic x.         *> Invoice Cleared             space or C   paid or credited or cleared/cancelled etc
     03  sih-status-A      pic x.         *> Invoice Applied to a/c      space or A
     03  sih-status-I      pic x.         *> Invoice Item lines Deleted  space or D
     03  sih-lines         binary-char.
     03  sih-deduct-days   binary-char.
     03  sih-deduct-amt    pic 999v99    comp.
     03  sih-deduct-vat    pic 999v99    comp.
     03  sih-days          binary-char.
     03  sih-cr            binary-long.
     03  sih-day-book-flag pic x               value space.
         88  day-booked                        value "B".
     03  sih-update        pic x.
         88  sih-analyised                     value "Z".
     03  filler            pic x.      *> Remove this
*>
*>*******************************************
*>                                          *
*>  Working Storage For The Invoice Lines   *
*>                                          *
*>*******************************************
*> 80 bytes each = 3200 bytes (17/05/13)
*> still valid 18/01/17
*>
 01  SInvoice-Bodies.
         05  sil-Key.                     *> 9 bytes
             07  sil-invoice pic 9(8).
             07  sil-line    binary-char.  *>>> needs to be pic 99
         05  sil-product     pic x(13).   *> +1 17/5/13
         05  sil-pa          pic xx.
         05  sil-qty         binary-short.
         05  sil-type        pic x.
         05  sil-description pic x(32).   *> +8 17/5/13
         05  sil-net         pic s9(7)v99   comp-3.
         05  sil-unit        pic s9(7)v99   comp-3.
         05  sil-discount    pic 99v99      comp.
         05  sil-vat         pic s9(7)v99   comp-3.
         05  sil-vat-code    pic 9.
         05  sil-update      pic x.
             88 sil-analyised                       value "Z".
         05  filler          pic xx.    *>  less 1 (pic x.)
*>
*>  Next useful to keep track of number of invoice-line entries.
*>        NOT YET USED.
*>
 01  Sinvoice-Line-Count   binary-char            value zero.

*>
 procedure division.
 AA000-Start.
*>
*>  delete invoice.dat.OLD file if exists then
*>  rename invoice.dat to invoice.dat.OLD
*>
     call "CBL_DELETE_FILE" using Old-File-16.  *> invoice.dat.OLD
     call "CBL_RENAME_FILE" using File-16  Old-File-16.
     if       return-code not = zero
              display "Error on Renaming Invoice File "
              stop "ST901 Note error and hit return to abort"
              stop run.
*>
     open     input Old-Invoice-file.
     if       fs-reply not = zero      *> JIC but should not happen as prev. will err.
              display "Error on opening Old Invoice File " fs-reply
              stop "ST901 Note error and hit return"
              close Old-Invoice-File
              stop run.
     open     output Invoice-File.
*>
*> now clear of any possible problems with the file - hopefully!
*>
     Display  prog-name " Starts".
*>
 AA010-Read.
     read     Old-Invoice-file next record.
     if       fs-reply = 10
              go to AA020-End.
*>
     if       fs-reply not = zero
              display "Error on Reading (Old) Invoice File " fs-reply
              stop "ST901 Note error and hit return for abort run"
              close Invoice-File
                    Old-Invoice-File
              stop run.
*>
     if       Old-Item-Nos not = zero                *> Inv lines read
              move Old-Invoice-Record to SInvoice-Bodies
              initialise Invoice-Line with filler
              move corresponding SInvoice-Bodies to Invoice-Line
              move sil-line to il-Line
              write  Invoice-Line
     else
              move Old-Invoice-Record to SInvoice-Header
              initialize Invoice-Header
              move corresponding SInvoice-Header to Invoice-Header
              move sih-Test  to ih-Test
              write  Invoice-Header
     end-if
     if       fs-reply not = zero
              display "Error on writing to (New) Invoice File " fs-reply
              stop "ST901 Note error and hit return for abort run"
              close Invoice-File
                    Old-Invoice-File
              stop run
     end-if
     go       to AA010-Read.
*>
 AA020-End.
     close    Old-Invoice-File
              Invoice-file.
     display "Invoice (Cobol flat) File Conversion to v3.02 completed "
     stop     run.
*>
