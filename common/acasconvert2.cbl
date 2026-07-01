       >>source free
*> PROGRAM NOT NEEDED unless using very old versions of ACAS.
       *>
       *>  THIS NEEDS UPDATING TO CURRENT system.dat file layout.
       *>
 identification division.
 program-id.                 acasconvert2.
*>Author.                    Vincent B Coen, MBCS. 02/05/09.
*>
*>Security.                  Copyright (C) 1982-2026, Vincent Bryan Coen.
*>                           Distributed under the GNU General Public License
*>                           v2.0. Only. See the file COPYING for details.
*>
*>Purpose.                   Convert ACAS system file/s for Stock & OE.
*>                           from 1.2 to 1.3. updated 25/08/16.
*>
*>     This program and others starting with acasconvertn (n = 1 thru 99) is
*>     for updating the data file layouts from one version to the next when
*>     required.  File layout changes are kept to a minimum but some times
*>     it is necessary.
*>
*>     THIS Version updates the first system record ONLY as the record size
*>      is the same - extended size of RDBMS-SOCKET from 32 to 64 chars and
*>      area taken from the (expansion) FILLER just after it.
*>      This update is required for the new RDBMS additions to allow for
*>      RDB residing on another system/computer.
*>      IRS data block has fields removed eg fn-1 thru 5 etc.
*>
*>     CHECK THAT THE 'OLD' SYSTEM RECORD LAYOUT MATCHES YOUR CURRENT ONE
*>     IF NOT REPLACE WITH YOUR CURRENT ONE COPY & PASTE FROM COPYBOOKS
*>      IN THE SOURCE DIRECTORY.
*>
*>      These fields are not encrypted but can be if required using any 3rd
*>      party tool.
*>
*>   WARNING:
*>    TAKE A BACK UP OF YOUR DATA FILES BEFORE RUNNING - twice.
*>    TAKE A BACK UP OF YOUR DATA FILES BEFORE RUNNING - YES twice.
*>
*>    Test with cobc flag -Wcorresponding
*>
*> Updates
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
*> for more details. If it breaks, you own both pieces but I will endevor
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
 copy "selsys.cob".

 data division.
 file section.
 copy "fdsys.cob".
*>
*>
 working-storage section.
 77  prog-name          pic x(18)  value "IRSconv2 (3.3.00)".
 01  fs-reply           pic 99.
 01  rec-count          pic 9(4)   value zero.
 01  A                  pic s9(4)     comp    value zero.
 01  B                  pic s9(4)     comp    value zero.
 01  Rrn                binary-long.
 01  Display-Blk        pic x(78)             value spaces.
*>
 01  Error-Messages.
     03  SY103    pic x(22) value "SY103 Rewrite Err 1 = ".
     03  SY104    pic x(26) value "SY104 Fix and Press Enter".
*>
 copy "wsnames.cob".
*>
*> 25/06/16 vbc - Added RDBMS-Port & needs RDBMS-Host, RDBMS-Socket.
*>                Increased 'System-data' from 384 to 512 bytes & removed O/E
*>                  Block (128) as it is unused.
*> 26/06/16 vbc - Updated MySQL Load scripts ACASDB.sql in ACAS/mysql.
*>                  Prima is yet to be done !!!
*> 19/10/16 vbc - Changed PL-Approp-AC in IRS block from 9(5) to 9(6) for GL
*>                support & reduced filler by 1.
*>                With IRS data mapped into ACAS the IRS block can reduce to 32 bytes
*>                Just need to change all of the IRS programs to use ACAS fields but
*>                also NEED to change the date processing to use same in rest of ACAS
*>                and not binary days since 01/01/2000 and hold dates in dd/mm/yy form.
*>                Added 2 88s to Op-System for IRS.
*> 27/10/16 vbc - Changed level-5 to IRS instead of omitted O/E.
*>
 01  System-Record.
*>******************
*>   System Data   *
*>******************
     03  System-Data-Block.                                  *>   384 changed to 512 bytes (25/06/16)
         05  System-Record-Version-Prime      binary-char.   *>  1
         05  System-Record-Version-Secondary  binary-char.   *>  3  Updated 25/08/16
         05  Vat-Rates                    comp.
             07 Vat-Rate-1   pic 99v99.                      *> Standard rate
             07 Vat-Rate-2   pic 99v99.                      *> Reduced rate
             07 Vat-Rate-3   pic 99v99.                      *> Minimal or exempt
             07 Vat-Rate-4   pic 99v99.   *> 2b used for local sales tax   Not UK
             07 Vat-Rate-5   pic 99v99.   *> 2b used for local sales tax   Not UK
         05  Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5.
         05  Cyclea          binary-char.  *> 99.
         05  Scycle Redefines cyclea  binary-char.
         05  Period          binary-char.  *> 99.
         05  Page-Lines      binary-char  unsigned. *> 999.
         05  Next-Invoice    binary-long. *> 9(8) comp.
         05  Run-Date        binary-long. *> 9(8) comp.
         05  Start-Date      binary-long. *> 9(8) comp.
         05  End-Date        binary-long. *> 9(8) comp.
         05  Suser.                             *> IRS
             07  Usera       pic x(32).
         05  User-Code       pic x(32).   *> encrypted username not used on OS versions so also b 4 client?
         05  Address-1       pic x(24).
         05  Address-2       pic x(24).
         05  Address-3       pic x(24).
         05  Address-4       pic x(24).
         05  Post-Code       pic x(12).   *> or ZipCode size should cover all countries
         05  Country         pic x(24).
         05  Print-Spool-Name pic x(48).
         05  File-Statuses.
             07  File-Status pic 9          occurs 32.
         05  Pass-Value      pic 9.
         05  Level.
             07  Level-1     pic 9.
                 88  G-L                    value 1.   *> General (Nominal) ledger
             07  Level-2     pic 9.
                 88  B-L                    value 1.   *> Purchase (Payables) ledger
             07  Level-3     pic 9.
                 88  S-L                    value 1.   *> Sales (Receivables) ledger
             07  Level-4     pic 9.
                 88  Stock                  value 1.   *> Stock Control (Inventory)
             07  Level-5     pic 9.
                 88  IRS                    value 1.   *> IRS used (instead of General).
             07  Level-6     pic 9.
                 88  Payroll                value 1.   *> Payroll
         05  Pass-Word       pic x(4).                 *>
         05  Host            pic 9.
             88  Multi-User                 value 1.
         05  Op-System       pic 9.
             88  valid-os-type            values 1 2 3 4 5 6.
             88  No-OS                    value zero.
             88  Dos                        value 1.
             88  Windows                    value 2.
             88  Mac                        value 3.
             88  Os2                        value 4.
             88  Unix                       value 5.
             88  Linux                      value 6.
             88  OS-Single                  values 1 2 4.
         05  Current-Quarter pic 9.
         05  RDBMS-Flat-Statuses.
             07  File-System-Used  pic 9.
                 88  FS-Cobol-Files-Used        value zero.
                 88  FS-RDBMS-Used              value 1.
*>                 88  FS-Oracle-Used             value 1.  *> THESE NOT IN USE
*>                 88  FS-MySql-Used              value 2.  *> ditto
*>                 88  FS-Postgres-Used           value 3.  *> ditto
*>                 88  FS-DB2-Used                value 4.  *> ditto
*>                 88  FS-MS-SQL-Used             value 5.  *> ditto
                 88  FS-Valid-Options           values 0 thru 1.    *> 5. (not in use unless 1-5)
             07  File-Duplicates-In-Use pic 9.
                 88  FS-Duplicate-Processing    value 1.
         05  Maps-Ser.      *> Not needed in OpenSource version, = 9999 (No Maintainence Contract]
             07  Maps-Ser-xx pic xx.        *> Allows for 36^2 * 100 customers
             07  Maps-Ser-nn binary-short.  *>       =  129600 - 2
         05  Date-Form       pic 9.
             88  Date-UK                    value 1.            *> dd/mm/yyyy
             88  Date-USA                   value 2.            *> mm/dd/yyyy
             88  Date-Intl                  value 3.            *> yyyy/mm/dd
             88  Date-Valid-Formats         values 1 2 3.
         05  Data-Capture-Used pic 9.
             88  DC-Cobol-Standard          value zero.
             88  DC-GUI                     value 1.
             88  DC-Widget                  value 2.
         05  RDBMS-DB-Name   pic x(12)      value "ACASDB".     *> change in setup
         05  RDBMS-User      pic x(12)      value "ACAS-User".  *> change in setup
         05  RDBMS-Passwd    pic x(12)      value "PaSsWoRd".   *> change in setup
         05  VAT-Reg-Number  pic x(11)      value spaces.
         05  Param-Restrict  pic x.                             *> Only via ACAS?
         05  RDBMS-Port      pic x(5)       value "3306".       *> change in setup
         05  RDBMS-Host      pic x(32)      value spaces.       *> change in setup
         05  RDBMS-Socket    pic x(64)      value spaces.       *> change in setup v3
         05  filler          pic x(34).                         *> for expansion v3
*>***************
*>   G/L Data   *
*>***************
     03  General-Ledger-Block.               *> 80 bytes
         05  P-C             pic x.
             88  Profit-Centres             value "P".
             88  Branches                   value "B".
         05  P-C-Grouped     pic x.
             88  Grouped                    value "Y".
         05  P-C-Level       pic x.
             88  Revenue-Only               value "R".
         05  Comps           pic x.
             88  Comparatives               value "Y".
         05  Comps-Active    pic x.
             88  Comparatives-Active        vaLUE "Y".
         05  M-V             pic x.
             88  Minimum-Validation         vaLUE "Y".
         05  Arch            pic x.
             88  Archiving                  value "Y".
         05  Trans-Print     pic x.
             88  Mandatory                  value "Y".
         05  Trans-Printed   pic x.
             88  Trans-Done                 value "Y".
         05  Header-Level    pic 9.
         05  Sales-Range     pic 9.
         05  Purchase-Range  pic 9.
         05  Vat             pic x.
             88  Auto-Vat                   value "Y".
         05  Batch-Id        pic x.
             88  Preserve-Batch             value "Y".
         05  Ledger-2nd-Index pic x.                     *> But file uses SINGLE INDEX only ???
             88  Index-2                    value "Y".
         05  IRS-Instead     pic x.
             88  IRS-Used                   value "Y".
             88  IRS-Both-Used              value "B".   *> 26/11/16
         05  Ledger-Sec      binary-short.  *> 9(4) comp
         05  Updates         binary-short.  *> 9(4) comp
         05  Postings        binary-short.  *> 9(4) comp
         05  Next-Batch      binary-short.  *> 9(4) comp  should be unsigned used for all ledgers
         05  Extra-Charge-Ac binary-long.   *> 9(8) comp
         05  Vat-Ac          binary-long.   *> 9(8) comp
         05  Print-Spool-Name2 pic x(48).
*>******************
*>   P(B)/L Data   *
*>******************
     03  Purchase-Ledger-Block.              *> 88 bytes
         05  Next-Folio      binary-long.   *> 9(8) comp
         05  BL-Pay-Ac       binary-long.   *> 9(8) comp
         05  P-Creditors     binary-long.   *> 9(8) comp
         05  BL-Purch-Ac     binary-long.   *> 9(8) comp
         05  BL-End-Cycle-Date binary-long.   *> 9(8) comp
         05  BL-Next-Batch   binary-short.   *> 9(4) comp  should be unsigned - unused ?
         05  Age-To-Pay      binary-char.   *> 9(4) comp should be unsigned
         05  Purchase-Ledger pic x.
             88  P-L-Exists                 value "Y".
         05  PL-Delim        pic x.
         05  Entry-Level     pic 9.
         05  P-Flag-A        pic 9.
         05  P-Flag-I        pic 9.
         05  P-Flag-P        pic 9.
         05  PL-Stock-Link   pic x.
         05  Print-Spool-Name3 pic x(48).
         05  filler          pic x(10).
*>***************
*>   S/L Data   *
*>***************
     03  Sales-Ledger-Block.                 *> 128 bytes
         05  Sales-Ledger    pic x.
             88  S-L-Exists                 value "Y".
         05  SL-Delim        pic x.
         05  Oi-3-Flag       pic x.             *> 'Y' used in sl060 why?
         05  Cust-Flag       pic x.
         05  Oi-5-Flag       pic x.
         05  S-Flag-Oi-3     pic x.             *> 'z' when otm3 created, used in sl060 why? NO LONGER USED
         05  Full-Invoicing  pic 9.
         05  S-Flag-A        pic 9.             *> '1' used in sl060 why?
         05  S-Flag-I        pic 9.             *> '2' used in sl060 why?
         05  S-Flag-P        pic 9.
         05  SL-Dunning      pic 9.
         05  SL-Charges      pic 9.
         05  Sl-Own-Nos      pic x.
         05  SL-Stats-Run    pic 9.
         05  Sl-Day-Book     pic 9.
         05  invoicer        pic 9.
             88  I-Level-0                  value 0.  *> show totals only (no net & vat) not used?
             88  I-Level-1                  value 1.  *> Show net, vat
             88  I-Level-2                  value 2.  *> show Details + vat etc looks wrong in sl910 totals only (no net & vat)
             88  Not-Invoicing              value 9.  *> show totals only (no net & vat) but not found yet nor level 3 (see sl900)
         05  Extra-Desc      pic x(14).
         05  Extra-Type      pic x.
             88  Discount                   value "D".
             88  Charge                     value "C".
         05  Extra-Print     pic x.
         05  SL-Stock-Link   pic x.
         05  SL-Stock-Audit  pic x.
             88  Stock-Audit-On             value "Y".   *> Invoicing will create an audit record (15/05/13)
         05  SL-Late-Per     pic 99v99    comp.
         05  SL-Disc         pic 99v99    comp.
         05  Extra-Rate      pic 99v99    comp.
         05  SL-Days-1       binary-char.  *> 999  comp.
         05  SL-Days-2       binary-char.  *> 999  comp.
         05  SL-Days-3       binary-char.  *> 999  comp.
         05  SL-Credit       binary-char.  *> 999  comp.
         05  filler          binary-short.   *> No longer used.
         05  SL-Min          binary-short.  *> 9999  comp.
         05  SL-Max          binary-short.  *> 9999  comp.
         05  PF-Retention    binary-short.  *> 9999  comp.
         05  First-Sl-Batch  binary-short.  *> 9999  comp.   *>unused ?
         05  First-Sl-Inv    binary-long.   *> 9(8) comp.
         05  SL-Limit        binary-long.   *> 9(8) comp.
         05  SL-Pay-Ac       binary-long.   *> 9(8) comp.
         05  S-Debtors       binary-long.   *> 9(8) comp.
         05  SL-Sales-Ac     binary-long.   *> 9(8) comp.
         05  S-End-Cycle-Date binary-long.   *> 9(8) comp.
         05  SL-Comp-Head-Pick Pic x.
             88  SL-Comp-Pick               value "Y".
         05  SL-Comp-Head-Inv  pic x.
             88  SL-Comp-Inv                value "Y".
         05  SL-Comp-Head-Stat pic x.
             88  SL-Comp-Stat               value "Y".
         05  SL-Comp-Head-Lets pic x.
             88  SL-Comp-Lets               value "Y".
         05  SL-VAT-Printed  pic x.
             88  SL-VAT-Prints              value "Y".
         05  filler          pic x(45).      *>  just in case
*>***************
*> Stock Data   *
*>***************
*>
     03  Stock-Control-Block.                *> 88 bytes
         05  Stk-Abrev-Ref   pic x(6).
         05  Stk-Debug       pic 9.          *> T/F (1/0).
         05  Stk-Manu-Used   pic 9.          *> T/F (Bomp/Wip)
         05  Stk-OE-Used     pic 9.          *> T/F.
         05  Stk-Audit-Used  pic 9.          *> T/F.
         05  Stk-Mov-Audit   pic 9.          *> T/F.
         05  Stk-Period-Cur  pic x.          *> M=Monthly, Q=Quarterly, Y=Yearly
         05  Stk-Period-dat  pic x.          *>  --  ditto  --
         05  filler          pic x.          *> was stk-date-form
         05  Stock-Control   pic x.
             88  Stock-Control-Exists   value "Y".
         05  Stk-Averaging   pic 9.          *> T/F.
             88  Stock-Averaging        value 1.
         05  Stk-Activity-Rep-Run pic 9.     *> T/F.  =17 bytes 0=no, 1=add, 2=del, 3=both
         05  filler          pic x.          *> slack byte
         05  Stk-Page-Lines  binary-char unsigned.  *> 9999 comp. Taken from Print-Lines
         05  Stk-Audit-No    binary-char unsigned.  *> 9999 comp.
         05  filler          pic x(68).             *> 64    (just in case)
*>     03  Order-Entry-Block.                         *> 128 bytes
*>         05  filler-Dummy    pic x(128).          *> space moved to System block as un-used v1.2
     03  IRS-Entry-Block.                       *> NEW 12/06/13
         05  Client             pic x(24).      *>              24      *> Not needed as will use suser
         05  Next-Post          pic 9(5).       *>              29                                                  N   5
         05  Vat-Rates2.                                             *> these can be replaced by the other VAT blk
             07  vat1           pic 99v99.      *>              33   *> Standard  changed from vat (11/06/13)
             07  vat2           pic 99v99.      *>              37   *> reduced 1 [not yet used]
             07  vat3           pic 99v99.      *>              41   *> reduced 2 [not yet used]
         05  Vat-Group redefines Vat-Rates2.
             07  Vat-Psent      pic 99v99    occurs 3.
         05  IRS-Pass-Value     pic 9.           *>             42  (Was Pass-Value in IRS system file)
         05  Save-Sequ          pic 9.           *>             43
         05  System-Work-Group  pic x(18).       *>             61
         05  PL-App-Created     pic x.           *>             62
         05  PL-Approp-AC6      pic 9(6).        *>             68   changed for GL support if needed ?. Both needed in RDB
         05  filler redefines PL-Approp-AC6.
             07  PL-Approp-AC   pic 9(5).        *>                   For IRS
             07  filler         pic 9.
         05  1st-Time-Flag      pic 9.           *>             69    (was First-Time-Flag in IRS system file)      N  32
         05  filler             pic x(59).       *>             128  Old fn-1 to 5 files
     03  IRS-Data-Block redefines IRS-Entry-Block.
         05  filler-dummy4   pic x(128).
*>
 procedure division.
 AA000-Start.
*>
*>   1st check that the record is exactly the same size for old and new
*>     if not STOP
*>
*>
     display  " " at 0101 with erase eos.
     move     function Length (
                               Old-System-Record
                                                ) to A.
     move     function length (
                               System-Record
                                               ) to B.
     if       A not = B
              move spaces to Display-Blk
              string "Old and new system record size not equal, Old = "
                                    delimited by size
                     A              delimited by size
                     " "            delimited by size
                     "New Rec = "   delimited by size
                     B              delimited by size    into Display-Blk
              end-string
              display Display-Blk at 2301 with erase eol
              display "ST901 Note error and hit return" at 2401 with erase eol
              accept FS-Reply at 2433
              stop run
     end-if
*>
     open     i-o system-file.
     if       fs-reply not = zero
              display "Error on opening i-o System File " fs-reply
              display "ST901 Note error and hit return"
              accept FS-Reply
              stop run.
*>
*> now clear of any possible problems with the file - hopefully!
*>
     Display  prog-name " Starts".
*>
 AA010-Read.
     move     1  to  rrn.
     read     system-file into Old-System-Record.
     if       fs-reply not = zero
              display "Record 1 NOT found - Aborting err code = ", fs-reply
              stop " Read above msg and hit return to continue !"
              close system-file
              stop run.
*>
     initialize System-Record.                  *> in case of new fields
     move     corresponding Old-System-Record to System-Record.
*>
 *> TEST WITH COBC FLAG -Wcorresponding should see (new) RDB fields
*>
*>     Now V1.3
*>
     move     1   to System-Record-Ver-Prime in System-Record.
     move     3   to System-Record-Version-Secondary in System-Record.
*>
*>== just to confirm versions is now 1.3
*>
    display   " new Version is " System-Record-Version-Prime     in System-Record
              "."                System-Record-Version-Secondary in System-Record.
*>
     move     1 to rrn.
     rewrite  System-Record.
*>
     perform  Disk-Error-Display.
*>
     close    system-file.
     if       fs-reply = zero
              display "System (Cobol flat) File Conversion completed "
              display " Remember to go through system setup to confirm all data"
              stop    " Hit return to close ".
*>
     stop     run.
*>
 Disk-Error-Display.
     if       fs-reply not = zero
              display SY103 at 0310 with erase eos
              display fs-reply at 0334
              display " " at 0401
              perform Disk-error.
*>
 Disk-Error.
     display  SY104 at 2401.
     accept   fs-reply at 2428.
*>
