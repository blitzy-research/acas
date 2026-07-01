       >>source free
*> PROGRAM NOT NEEDED unless using very old versions of ACAS.

 identification division.
 program-id.                 acasconvert1.
*>Author.                    Vincent B Coen, MBCS. 06/05/18.
*>
*>Security.                  Copyright (C) 2020-2026, Vincent Bryan Coen.
*>                           Distributed under the GNU General Public License
*>                           v2.0. Only. See the file COPYING for details.
*>
*>Purpose.                   Convert an existing ACAS IRS default file only.
*>
*>
*>     This program and others starting with acasconvertn (n = 1 thru 99) is
*>     for updating the data file layouts from one version to the next when
*>     required.  File layout changes are kept to a minimum but some times
*>     it is necessary.
*>
*>     THIS Version updates the IRS Default record ONLY as the record size
*>      now supports default 33 which is ONLY a place holder used in the
*>      irs030 posting program for a tempoarary default and is discarded
*>      when the posting program finishes.
*>     The program renames file to irsdflt.saved before processing.
*>
*>     There is NO change to the RDB table.
*>
*>   WARNING:
*>    TAKE A BACK UP OF YOUR DATA FILES BEFORE RUNNING - twice.
*>    TAKE A BACK UP OF YOUR DATA FILES BEFORE RUNNING - twice.
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
     select Old-Default-File assign "irsdflt.saved"      *> file-35
                             organization line sequential,
                             access sequential,
                             status fs-reply.
*>
     select New-Default-File assign "irsdflt.dat"
                             organization line sequential,
                             access sequential,
                             status fs-reply.
*>
 data division.
 file section.
*>
 fd  Old-Default-File.
 01  Old-Default-Record.
     03  Def-Acs         pic 9(5)   occurs  32.
     03  Def-Codes       pic xx     occurs  32.
     03  Def-Vat         pic x      occurs  32.
*>
 fd  New-Default-File.
 01  New-Default-Record.
     03  New-Def-Group              occurs 33.
         05  New-Def-Acs   pic 9(5).
         05  New-Def-Codes pic xx.
         05  New-Def-Vat   pic x.

 working-storage section.
 77  prog-name          pic x(18)  value "IRSconv1 (3.3.00)".
 01  fs-reply           pic 99.
 01  rec-count          pic 9(4)   value zero.
 01  A                  pic s9(4)     comp    value zero.
 01  B                  pic s9(4)     comp    value zero.
 01  Display-Blk        pic x(78)             value spaces.
 01  WS-Reply           pic x                 value space.
*>
 01 file-info.
     05 File-Size-In-Bytes PIC 9(18) COMP.
     05 Mod-DD   PIC 9(2) COMP.       *> Modification Date
     05 Mod-MO   PIC 9(2) COMP.
     05 Mod-YYYY PIC 9(4) COMP.
     05 Mod-HH   PIC 9(2) COMP.       *> Modification Time
     05 Mod-MM   PIC 9(2) COMP.
     05 Mod-SS   PIC 9(2) COMP.
     05 FILLER   PIC 9(2) COMP.       *> Always 00
*>
 01  Error-Messages.
     03  SY991    pic x(26) value "SY991 Fix and Press Enter".
*>
 copy "wsnames.cob".
*>
 procedure division.
 AA000-Start.
*>
*>   First check that irsdflt.saved does not exist then rename the file to .saved
*>
     call     "CBL_CHECK_FILE_EXIST" USING "irsdflt.saved" file-info.
     if       Return-Code = zero
              display "Found 'Saved' IRS Default File - irsdflt.saved"  return-code
              display SY991
              accept WS-Reply
              stop run.
     call     "CBL_RENAME_FILE" USING "irsdflt.dat" "irsdflt.saved".
     if       return-code not = zero
              display "Cannot rename 'IRS Default File from irsdflt.dat to irsdflt.saved"  return-code
              display SY991
              accept WS-Reply
              stop run.
*>
     open     input Old-Default-File.
     if       fs-reply not = "00"
              display "Error on opening input 'irsdflt.saved " fs-reply
              stop run.
*>
*> now clear of any possible problems with the file - hopefully!
*>
     Display  prog-name " Starts" at 0101 with erase eos.
*>
     open     output New-Default-File.
     if       fs-reply not = zero
              display "Error on opening ouput 'irsdflt.dat" fs-reply
              close Old-Default-File
              stop run.

 AA010-Read.
     read     Old-Default-File.
     if       fs-reply not = zero
              display "Record NOT found - Aborting err code = " fs-reply
              close Old-Default-File
              display SY991
              accept WS-Reply
              stop run.
*>
     initialize New-Default-Record.                  *> in case of new fields
     move     zero to A.
     perform  32 times
              add 1 to a
              move   Def-Acs   (a)  to  New-Def-Acs   (a)
              move   Def-Codes (a)  to  New-Def-Codes (a)
              move   Def-Vat   (a)  to  New-Def-Vat   (a)
     end-perform.
     write    New-Default-Record.
     if       fs-reply not = zero
              display "Error on writing new default record = " fs-reply
              close Old-Default-File New-Default-File
              display SY991
              accept WS-Reply
              stop run.
*>
     close    Old-Default-File New-Default-File.
     Display  prog-name " Ends Successfully" at 0101.
     goback.
*>
