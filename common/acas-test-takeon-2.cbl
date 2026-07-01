       >>source free
*>************************************************************
*>                PURCHASE LEDGER                            *
*>         Special for P/L records being transferred         *
*>          to Purchase Ledger as cant use real P/L data.    *
*>   as it is the S/L data is 40+ years old so non valid     *
*>     with bad addresses, PC & phone nos.                   *
*>  It creates a Cobol file that can be then loaded into RDB *
*>              Uses the ACAS system record.                 *
*>  ======================================================== *
*>               THIS IS FOR TEST DATA ONLY....              *
*>************************************************************
*>
 identification division.
*>
 program-id.         takeon-2.
*>
 Author.             V B COEN FBCS.
*>**
*> Security.         Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                   Distributed under the GNU General Public License.
*>                   See the file COPYING for details.
*>**
 Date-written.       29 FEB 1988. Originally.
*>
 date-compiled.
*>
*> Version.          See PROG-NAME & DATE-COMP in WS.
*>**
*> Called Modules.   acas022   } For file and table access.
*>                   purchMT   }
*>                   fhlogger
*>                   maps03
*>                   maps09
*>
*>**
*> Changes.
*> 17/02/17 - .01 Taken from regs120 and others to build salesled
*>                level 1 test data.
*> 19/02/17 - .02 Clean out data without address info lines >1.
*>                Same showing those without phone nos & addr >1.
*>                Delete keys for those skipped to remove from existing
*>                File / table (If used).
*> 19/02/17 - .   Taken from takeon-1 (S/L) for use with P/L.
*> 25/09/19 - .03 Make all records have status zero - inactive.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>********************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supercedes all prior copyright notices & was updated 2024-04-16.
*>
*> These files and programs are part of the Applewood Computers Accounting
*> System and is Copyright (c) Vincent B Coen. 1976-2026 and later.
*>
*> This program is now free software; you can redistribute it and/or modify it
*> under the terms listed here and of the GNU General Public License as
*> published by the Free Software Foundation; version 3 and later as revised
*> for PERSONAL USAGE ONLY and that includes for use within a business but
*> EXCLUDES repackaging or for Resale, Rental or Hire in ANY way.
*>
*> Persons interested in repackaging, redevelopment for the purpose of resale or
*> distribution in a rental or hire mode must get in touch with the copyright
*> holder with your commercial plans and proposals.
*>
*> ACAS is distributed in the hope that it will be useful, but WITHOUT
*> ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
*> FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
*> for more details. If it breaks, you own both pieces but I will endeavour
*> to fix it, providing you tell me about the problem.
*>
*> You should have received a copy of the GNU General Public License along
*> with ACAS; see the file COPYING.  If not, write to the Free Software
*> Foundation, 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
*>
*>******************************************************************************
 environment division.
*>
 copy "envdiv.cob".
*>
 input-output section.
 file-control.
*>
 copy "selsys.cob".
*>
     select customersin     assign "customer.txt"
                            organization line sequential
                            status fs-reply.
*>
 DATA DIVISION.
 file section.
*>
 copy "fdsys.cob".
*>
 fd  CustomersIn.
*>
 01  customersin-record.
     03  prd-char        pic x   occurs 256.
*>
 working-storage section.
*>
 77  prog-name           pic x(20)    value "PL Takeon-2 3.3.00)".
 77  z                   binary-char  value zero.
 77  y                   binary-char  value zero.
 77  x                   binary-char  value zero.
 77  OS-Delimiter        pic x        value "/".
 77  ACAS_BIN            pic x(512)   value spaces.
 77  ACAS_LEDGERS        pic x(500)   value spaces.
 77  Arg-Number          pic 9        value zero.
*>
*> holds program parameter values from command line
*>
 01  Arg-Vals                         value spaces.
     03  Arg-Value       pic x(525)  occurs 2.
 01  Arg-Test            pic x(525)   value spaces.
*>
 01  work-fields.
     03  ws-Rec-Cnt-In   pic 9(4)     value zero.
     03  ws-Rec-Cnt-Out  pic 9(4)     value zero.
     03  ws-Rec-Cnt-R-Out pic 9(6)    value zero.
     03  ws-reply        pic x.
*>
 01  ws-data.
     03  a               pic 9999   binary.
     03  b               pic 9999.
     03  c               pic 9(4)   value zero.
     03  d               pic 9(4)   value zero.
     03  e               pic 9(4)   value zero.
     03  f               pic 9      value zero.
     03  Short-Address   pic 9(4)   value zero.
     03  No-Phone-Nos    pic 9(4)   value zero.
     03  Deleted-Recs    pic 9(4)   value zero.
     03  ws-Test-Date    pic x(10).
     03  ws-swap             pic xx.
     03  ws-Conv-Date        pic x(10).
     03  ws-date             pic x(10).
     03  ws-UK redefines ws-date.
         05  ws-days         pic xx.
         05  filler          pic x.
         05  ws-month        pic xx.
         05  filler          pic x.
         05  ws-year         pic x(4).
     03  ws-USA redefines ws-date.
         05  ws-usa-month    pic xx.
         05  filler          pic x.
         05  ws-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  ws-Intl redefines ws-date.
         05  ws-intl-year    pic x(4).
         05  filler          pic x.
         05  ws-intl-month   pic xx.
         05  filler          pic x.
         05  ws-intl-days    pic xx.
*>
     03  ws-name-addr.  *> Have to break down last addr line 4 trail postcode
         05  ws-name     pic x(32).
         05  ws-addr1    pic x(32).
         05  ws-addr2    pic x(32).
         05  ws-addr3    pic x(32).
         05  ws-addr4    pic x(32).
         05  ws-addr5    pic x(32).
         05  ws-contact  pic x(32).   *> was 27
         05  ws-cust-telno pic x(13).
         05  ws-type     pic x.
         05  ws-DateX.
             07  ws-Date9 pic 9(8).
         05  ws-addr-level pic 9.
         05  ws-tmp-addr1 pic x(32).
         05  ws-tmp-PC   pic x(12).
     03  ws-Cust-Code.                 *> Will become purch key
         05  filler      pic x       value "P".
         05  ws-code5    pic x(5).
         05  filler      pic x       value zero.
     03  ws-tmp-telno2   pic x(13).
     03  ws-Tmp-Date     pic x(8)    value spaces.
     03  ws-Tmp-BinDate  binary-long  value zero.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 copy "wscall.cob".
 copy "wspl.cob".
 copy "wsmaps03.cob".
 copy "wsmaps09.cob".
 copy "wsfnctn.cob".
 copy "wsnames.cob".
*>
 01  Error-Messages.
*> System Wide
     03  ST001          pic x(26) value "SL001 System 1 read err = ".
     03  ST004          pic x(59) value "SL004 Problem with opening system file. Hit return to clear".
     03  SY006          pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
*> Program specific
     03  SL010          pic x(30) value "SL010 Duplicate key/s found = ".
     03  SL011          pic x(33) value "SL011 Error on purchMT processing".
     03  SL012          pic x(33) value "SL012 Error opening purch File = ".
     03  SL013          pic x(30) value "SL013 Error on reading file = ".
     03  SL014          pic x(31) value "SL014 Error on writing table = ".
     03  SL015          pic x(34) value "SL015 Error opening purch Table = ".
     03  SL096          pic x(37) value "SL096 SL Delimiter not set - Aborting".
     03  SL097          pic x(29) value "SL097 No purch file present".
     03  SL099          pic x(15) value "SL099 Ignoring.".
*>
 procedure  division.
 la-proc-control        section.
*>*****************************
*>
 la-main.
*>
        DISPLAY  prog-name       AT 0101 with erase eos.
        DISPLAY  "Purch TAKE-ON" AT 0129.
*>
*>  Get the system param for the various default Cust fields
*>
     perform  zz020-Get-Program-Args.
     open     input System-File.
     if       fs-reply not = zero
              display ST001 fs-reply
              display ST004
              close System-File
              goback
     end-if
     move     1 to rrn.
     read     system-file record.
     if       fs-reply not = zero
              display ST001 fs-reply
              close System-File
              goback
     end-if
*>
*>  Check that PL-Delim is set (not space)
*>
     if       PL-Delim = spaces
              display SL096 at 0501
              display SY008          at 0601
              accept ws-reply        at 0632
              perform acas022-Close
              goback.
*>
     close    System-File.
     perform  lc-extract.
     stop     run.
*>
 lc-extract          section.
*>**************************
*>
 lc-main.
*>
     perform  lcb-proc-customers.
*>
 lc999-exit.  exit.
*>*********   ****
*>
 lcb-proc-customers    section.
*>*****************    *******
*>
 lcb010-main.
*>
     open     input customersin.
     move     zero to b.
*>
*>  Over-ride processes for acas022/purchMT for Dup modes
*>    we are only writing to Cobol file
*>
     move     zero to File-System-Used
                      File-Duplicates-In-Use
                      FA-File-System-Used
                      FA-File-Duplicates-In-Use.   *>  Cobol file in use
     move     zero to Log-file-rec-written.        *> for logging.
*>
     move     1 to File-Key-No.
     perform  acas022-Open.    *> For I/O
     if       fs-reply not = zero
              display SL012  at 0501
              display fs-reply at 0534
              display SY008          at 0601
              accept ws-reply        at 0632
              perform acas022-Close
              goback.
     move     zero to Access-Type.
*>
 lcb020-read.
     read     customersin at end
              close customersin   *> customersout
              perform acas022-Close
              display "Purchase Rec max size = " AT 1401 with erase eos
              display b at 1425
              display "Purchase count = " at 1501
              display C at 1518
              display "Max Addr length " at 1601
              display d at 1617
              display "Record written Short" at 1701
              display E   at 1722
              display "Short Addr count = " at 1801
              display Short-Address         at 1820
              display "No Phone # count = " at 1901
              display No-Phone-Nos          at 1920
              display "Deleted Rec cnt  = " at 2001
              display Deleted-Recs          at 2020
              display "Records in = "       at 2101
              display ws-rec-Cnt-In         at 2115
              display "Records Out = "      at 2201
              display ws-Rec-Cnt-Out        at 2215
              display "Records Rewritten = "  at 2301
              display ws-Rec-Cnt-R-Out        at 2322
              display "Note counts and hit return" at 2401
              accept ws-Reply at 2427
              go to lcb999-exit.
*>
     move     zero to f.       *> clear overflow flag
     add      1 to ws-Rec-Cnt-In.
*>
*> Init salesled record and load defaults (from system rec)
*>
     initialise WS-Purch-Record with filler.
     initialise ws-name-addr.
     initialise ws-code5.
     move     30        to  Purch-Credit.
     move     40.00     to  Purch-Discount.
     move     1000      to  Purch-Limit.
     move     run-date  to  Purch-Create-Date.
     move     0         to  Purch-Status.              *> Inactive
*>
     move     2 to a.
     unstring customersin-record delimited by "'," into ws-code5 pointer a.
*>
     add      1 to a.
     unstring customersin-record delimited by "'," into ws-name pointer a.
     add      1 to a.
     unstring customersin-record delimited by "'," into ws-addr1 pointer a.
     add      1 to a.
     unstring customersin-record delimited by "'," into ws-addr2 pointer a.
     add      1 to a.
     unstring customersin-record delimited by "'," into ws-addr3 pointer a.
     add      1 to a.
     unstring customersin-record delimited by "'," into ws-addr4 pointer a.
     add      1 to a.
     unstring customersin-record delimited by "'," into ws-contact pointer a.
     add      1 to a.
     unstring customersin-record delimited by "'," into ws-cust-telno pointer a.
     add      1 to a.              *> next not wanted.
     unstring customersin-record delimited by "'," into ws-type pointer a.
     add      1 to a.
     unstring customersin-record delimited by "'" into ws-DateX pointer a.
*>
     move     function upper-case (ws-cust-code) to Customer-Nos.
     move     "C"  to  maps09-reply.
     perform  maps09.
     move     Customer-Code to WS-Purch-Key.    *> now got check digit
*>
*>  If valid date convert to binary  otherwise leave as todays date
*>    moved earlier.
*>
     if       ws-DateX not = "00/00/00"
              move     ws-DateX (1:6) to ws-test-date (1:6)
              move     ws-DateX (7:2) to ws-test-date (9:2)
              if       ws-Date9 (7:2) > 30
                       move     "19" to ws-test-date (7:2)
              else
                       move     "20" to ws-test-date (7:2)
              end-if
              perform  zz050-Validate-Date
              if       u-bin not = zero
                       move  u-bin to Purch-Create-Date.
*>
*>  Clean up phone no. size 13 chars
*>
     move     1  to y.
     move     1  to z.
     move     spaces to ws-tmp-telno2.
*>
 lcb030-ReDo.
     if       z > 13
              go to lcb040-Done.
     if       ws-cust-telno (z:1) = "(" or ")" or space
              add 1 to z
              go to lcb030-ReDo.
     move     ws-cust-telno (z:1) to ws-tmp-Telno2 (y:1).
     add      1 to y.
     add      1 to z.
     if       z < 14
              go to lcb030-ReDo.
*>
 lcb040-Done.
     move     ws-tmp-telno2  to ws-cust-telno.
     if       ws-Cust-Telno (1:5) = zeros
         or   ws-Cust-Telno = "000-0000"
              move spaces to WS-Cust-Telno
              add 1 to No-Phone-Nos
              perform lcb080-Delete-Rec
              go to lcb020-read
     end-if
     move     WS-Cust-Telno to Purch-Phone.
*>
     if       a > b                    *> Just noting max record size
              move a to b.
*>
*>  Now clean last addr field to break out the postcode.
*>    as xyz and finished with, can use them ignoring addr1
*>
     move     zero to z.
     move     spaces to ws-tmp-addr1 ws-tmp-PC.
*>
     if       ws-addr3  = spaces
              unstring   ws-addr2 delimited by "  "
                          into ws-tmp-addr1
                               ws-tmp-PC
              end-unstring
              move spaces to ws-addr2
     else
      if      ws-addr4  = spaces
              unstring   ws-addr3 delimited by "  "
                          into ws-tmp-addr1
                               ws-tmp-PC
              end-unstring
              move spaces to ws-addr3
      else
        if    ws-addr4 not = spaces
              unstring   ws-addr4 delimited by "  "
                          into ws-tmp-addr1
                               ws-tmp-PC
              end-unstring
              move spaces to ws-addr4.
*>
*> Quick clean for '"' replacing with space to stop SQL errors
*>
     inspect  ws-addr1  replacing all quotes by space.
     inspect  ws-addr2  replacing all quotes by space.
     inspect  ws-addr3  replacing all quotes by space.
     inspect  ws-addr4  replacing all quotes by space.
     move     function trim (ws-addr1, leading) to ws-addr1.
     move     function trim (ws-addr2, leading) to ws-addr2.
     move     function trim (ws-addr3, leading) to ws-addr3.
     move     function trim (ws-addr4, leading) to ws-addr4.
*>
*> Test for no addresses in data so skip. Test for it 1st
*>
     if       spaces = ws-addr4
                 and = ws-addr3
                 and = ws-addr2
              add    1 to Short-Address
              perform lcb080-Delete-Rec
              go to lcb020-read
     end-if.
*>
 lcb050-Load-Address.
     move     spaces to Purch-Address.
     if       z > 95        *> got overflow before on try 1
              move 1 to z   *> so ignore contact name
              move ws-name  to Purch-Name
     else
              move     1 to z
              if       ws-contact not = spaces
                       move     ws-contact to  Purch-Name
                       string   ws-name      delimited by "  "
                                PL-Delim     delimited by size
                                                   into Purch-Address
                                                   pointer z
                         on overflow
 *>                              display "OVERFLOW contact name"    AT 0501 with erase eos
 *>                              display Purch-Address at 0601
 *>                              display ws-addr1 at 0701
 *>                              display PL-Delim  at 0801
 *>                              display Purch-Address at 0901
 *>                              display "PE 0??" at 1001 with erase eos
                               go to lcb050-Load-Address
                       end-string
              else
                       move     ws-name    to  Purch-Name
              end-if
     end-if.
*>
*>  addr1 should not be spaces.
*>
 lcb060-Abbrev-Address.
     string   ws-addr1     delimited by "  "
              PL-Delim     delimited by size
                                          into Purch-Address
                                          pointer z
              on overflow
                      display "OVERFLOW addr 1"    AT 0501 with erase eos
                      display Purch-Address at 0601
                      display ws-addr1 at 0701
                      display PL-Delim  at 0801
                      display Purch-Address at 0901
                      display " " at 1001 with erase eos
                      stop "PE 1??"
                      perform acas022-Close
                      close Customersin
                      goback.
     if       ws-addr2 not = spaces
              string   ws-addr2     delimited by "  "
                       PL-Delim     delimited by size
                                          into Purch-Address
                                          pointer z
              on overflow
                      display "OVERFLOW addr 2"    AT 0501 with erase eos
                      display Purch-Address at 0601
                      display " " at 0701 with erase eos
                      stop "PE 2??"
                      perform acas022-Close
                      close Customersin
                      goback.
     if       ws-addr3 not = spaces
              string   ws-addr3     delimited by "  "
                       PL-Delim     delimited by size
                                          into Purch-Address
                                          pointer z
              on overflow
                      display "OVERFLOW addr 3"    AT 0501 with erase eos
                      display Purch-Address at 0601
                      display " " at 0701 with erase eos
                      stop "PE 3??"
                      perform acas022-Close
                      close Customersin
                      goback.
     if       ws-addr4 not = spaces
              string   ws-addr4     delimited by "  "
                       PL-Delim     delimited by size
                                          into Purch-Address
                                          pointer z
              on overflow
*>                      display "OVERFLOW addr 4"    AT 0501 with erase eos
*>                      display Purch-Address at 0601
*>                      display " " at 0701
*>                      display "PE 4??" at 0801 with erase eos
                      move 1 to f
                      go to lcb050-Load-Address.
*>
     if       ws-Tmp-Addr1 not = spaces
              string   ws-Tmp-addr1 delimited by "  "
                       PL-Delim     delimited by size
                                          into Purch-Address
                                          pointer z
              on overflow
                 if   f not = zero
                      add 1 to E
                      go to lcb070-Write
                 else
*>                      display "OVERFLOW tmp addr"    AT 0501 with erase eos
*>                      display Purch-Address at 0601
*>                      display " " at 0701
*>                      display "PE 5??" at 0801 with erase eos
                      move 1 to f
                      go to lcb050-Load-Address.
*>
     if       ws-Tmp-PC not = spaces
              string   ws-Tmp-PC    delimited by "  "
                       PL-Delim     delimited by size
                                          into Purch-Address
                                          pointer z
              on overflow
                 if   f not = zero
                      add 1 to E
                      go to lcb070-Write
                 else
*>                      display "OVERFLOW tmp PC"    AT 0501 with erase eos
*>                      display Purch-Address at 0601
*>                      display " " at 0701
*>                      display "PE 6??" at 0801 with erase eos
                      move 1 to f
                      go to lcb050-Load-Address.
*>
 lcb070-Write.
     if       z > d
              move z to d.
*>
     move     1 to File-Key-No.
     perform  acas022-Write.
     if       FS-Reply not = zero
              perform  acas022-Rewrite
              add      1 to ws-Rec-Cnt-R-Out
     else
              add      1 to ws-Rec-Cnt-Out
     end-if
     add      1 to c.
*>
*>  code to remove SL keys from P/L - derr - ONE OFF
*>
     move     "S" to WS-Purch-Key (1:1)
     perform  acas022-Delete.
     go       to lcb020-read.
*>
 lcb080-Delete-Rec.
     move     1 to File-Key-No.
     perform  acas022-Delete.       *> Not bothering with tests, dont care.
     add      1 to Deleted-Recs.
*>
 acas022.
     call     "acas022" using System-Record
                              WS-Purch-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas022-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas022.
     perform  aa100-Check-4-Errors.
*>
 acas022-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas022.
     perform  aa100-Check-4-Errors.
*>
 acas022-Close.
     set      fn-Close to true.
     perform  acas022.
*>
 acas022-Read-Next.
     set      fn-Read-Next to true.
     perform  acas022.
*>
 acas022-Write.
     set      fn-Write to true.
     perform  acas022.
*>
 acas022-Rewrite.
     set      fn-re-Write to true.
     perform  acas022.
*>
 acas022-Delete.
     set      fn-Delete to true.
     perform  acas022.
*>
 aa100-Check-4-Errors.
     if       fs-reply not = zero
              display SL011            at 0801   *> acas022/purchMT processing
              display "Fs-reply = "    at 0901
              display fs-reply         at 0912
              display "WE-Error = "    at 1001
              display  WE-Error        at 1012
              display SQL-Err          at 1101
              display SQL-Msg          at 1201
              display SY008 at 1701 with erase eol
              accept  Accept-Reply at 1735
              display " " at 0801 with erase eos
              go to lcb999-exit
     end-if.
*>
 maps03.
*>*****
*>
     call     "maps04"  using  maps03-ws.
*>
 maps09.
*>*****
*>
     call     "maps09"  using  customer-code.
*>
 lcb999-exit. exit.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   ws-test-date
*> output:  u-date/ws-date as uk date format
*>          u-bin not zero if valid date
*>
     inspect  ws-test-date replacing all "." by "/".
     inspect  ws-test-date replacing all "," by "/".
     inspect  ws-test-date replacing all "-" by "/".
*>
     move     ws-test-date to ws-date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-test-date.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz050-test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to ws-date.  *> swap Intl to UK form
     move     ws-test-date (1:4) to ws-Year.
     move     ws-test-date (6:2) to ws-Month.
     move     ws-test-date (9:2) to ws-Days.
*>
 zz050-test-date.
     move     ws-date to u-date.
     move     zero to u-bin.
     perform  maps03.
*>
 zz050-exit.
     exit     section.
*>
 copy "Proc-Get-Env-Set-Files.cob".
*>
