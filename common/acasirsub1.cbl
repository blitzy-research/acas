       >>source free
*>***********************************************
*>                                              *
*>            IRS  Nominal Ledger               *
*>               File/Table Handler             *
*>                                              *
*>  The Program name is taken from the FILE-nn  *
*>       used in the cobol file select.         *
*>***********************************************
*>
 identification division.
 Program-Id.            acasirsub1.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Nominal Ledger File Handler.
*>                      **************
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>**
*> Called Modules:
*>                      irsnominalMT -
*>                                DAL (RDB Data Access Layer) or a variation
*>                      Selected via CDF etc [to be added].
*>**
*> Error Messages Used.
*>                      IR901 Note error and hit return
*>                      IR902 Program Error: Temp rec = yyy < IRS-Nominal-Rec zzz
*>                      IR906 Link/record exists on owning write
*>                      IR907 Link/record exists on rewrite (S->O)
*>                      IR908 link/record exists on sub write
*>                      IR909 Link/record exists on owning write, rewriting
*>                      IR910 Rewrite failed as well
*>**
*> Version.             1.00 29/02/2012. Rewritten June 2016 after creating the DAL.
*>
*>                      This module is a ACAS File Handlers and is taken from
*>                      the first one (acas001) and
*>                      is lightly modelled on the irsub modules for IRS.
*>**
*> Changes.
*> 10/11/16 vbc - .04 Taken from ACAS FH stock.
*> 22/12/16 vbc - .05 Added extra code to handle open output which clears all data
*>                    for Cobol file and likewise set up DAL to do similar.
*>                .06 Added write-raw for nominalLD. Now will it work!
*> 28/01/18 vbc - .07 Updated copy for using copybooks dir.
*> 14/02/18 vbc - .08 Mapped error msgs to module specifics IR90n.
*> 28/02/18 vbc - .09 Added recs test for FH at ba012-Test-WS-Rec-Size-2
*> 20/04/18 vbc - .10 Move key to ws-file-key on error read indexed
*>                    Change code for open I/O NOT to close open output etc but give error cond
*>                    also give fs-reply to we-error if 47, 48, 49 to try and find error in caller
*>                    that is opening an already open file. Found it in irs030 (SL/PL posting file proc.
*> 23/04/18 vbc - .11 Extra code in open and read indexed.
*> 29/04/18 vbc - .12 Resetting Cobol-File-Status for write,rewrite,delete, start.
*> 07/12/22 vbc - .13 Chgd Vars A & B to pic 999 to keep GC v3.2 happy.
*> 10/12/22 vbc - .14 chg to perform ba-Process-RDBMS 2 remove GC warning msg from latest v3.2 code
*>                    WITH ba-Main-Exit chgd to exit section.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc - 3.3.00 Version update and builds reset.
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              1. File and table WS record : -
*>    acasirsub1 ONLY          WS-NL-Record = Contents of data record to be written/read
*>                          2. File-Access = File-Function as needed.
*>                              Access-Type   as needed.
*>                          3. File-Defs (File-Definitions) = Paths set up.
*>
*>    On Exit:          Linkage contains and apples to ALL FH and DAL modules:
*>    *******               Record = containing a read data record or table row
*>                          Fs-Reply = 0, 99 or other value where
*>                                     0  = Operation completed successfully
*>                                     10 = End of file
*>                                     21 = Invalid key | key not found
*>                                     47 = Open input  denied wrong perns to read from file
*>                                     48 = Open output denied wrong perns to write to file
*>                                     49 = Open I/O    denied wrong perns to read/write to file
*>                                     99 = Indicates an error see WE-Error for more info
*>                          WE-Error   0    = Operation completed successfully
*>                                     1+   = Failure to open IRS file
*>                                     2+   = Indexed IRS record not found
*>                                     3+   = IRS EOF reached
*>                                     999  = Undefined / unknown error
*>                                     998* = File-Key-No Out Of Range not 1.
*>                                     997* = Access-Type wrong (< 5 or > 8)
*>                                     996* = File Delete key out of range (not 1)
*>                                     995* = During Delete SQLSTATE not '00000' investigate using MSG-Err/Msg
*>                                     994* = During Rewrite,                     ^^ see above ^^
*>                                     990* = Unknown and unexpected error, again ^^ see above ^^
*>                                     989* = Unexpected error on Read-Indexed, investigate as above.
*>                                     911* = Rdb Error during initializing,
*>                                            possibly can not connect to database
*>                                             Check connect data and
*>                                             see SQL-Err & SQL-MSG
*>                                            Produced by Mysql-1100-Db-Error in copy
*>                                            module mysql-procedure.
*>                                     901  = File Def Record size not =< than ws record size
*>                                            Module needs ws definition changing to correct size
*>                                            FATAL, Stop using system, fix source code
*>                                            and recompile before using system again.
*>                                     Other = any other rdbms errors see specific
*>                                             (Rdbms) manual
*>                          SQL-Err  = Error code from RDBMS is set if above 2 are non zero
*>                          SQL-Msg  = Non space providing more info if SQL-Err non '00000'
*>                                     * = FS-Reply = 99.
*>                                     + = IRS FH & DAL Only.
*>
*>       During testing a log file will be created containing datetime stamp, task and return codes
*>       for both FS-Reply and WE-Error and table used along with the RDB error number and message
*>         In this case for the
*>                Nominal Ledger File.
*>
*>       WARNING - This file could get large so needs manually deleting after examination.
*>
*>******************************************************************************
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
*>**********************************************************************************
*>
 environment division.
 copy "envdiv.cob".
*>
 input-output section.
 file-control.
*>
     select nominal-ledger  assign       File-34   *> nl-file
                            organization indexed
                            access       dynamic
                            record       key-1
                            status       fs-reply.
*>
 data division.
 file section.
*>***********
 fd  nominal-ledger.
 copy "irsfdwsnl.cob".
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(20)  value "acasirsub1 (3.3.00)".
*>
 77  WS-Reply           pic x      value space.
*>
 77  A                  pic 9(4)   value zero.  *> A & B used in 1st test ONLY
 77  B                  pic 9(4)   value zero.  *>  in ba-Process-RDBMS
 77  Display-Blk        pic x(75)  value spaces.
 77  Cobol-File-Status  pic 9      value zero.
     88  Cobol-File-Eof            value 1.
*>
 01  Error-Messages.
*> STOPs - during testing and should NOT happen.
*>  Cobol File EOF-RN  - within Read-Next.
*>  Cobol File EOF-RNR - within Read-Next-Raw.
*>
*> System Wide
*> Module Specific
     03  IR901          pic x(31) value "IR901 Note error and hit return".
     03  IR902          pic x(32) value "IR902 Program Error: Temp rec = ".
     03  IR906          pic x(40) value "IR906 Link/record exists on owning write".
     03  IR907          pic x(42) value "IR907 Link/record exists on rewrite (S->O)".
     03  IR908          pic x(37) value "IR908 link/record exists on sub write".
     03  IR909          pic x(51) value "IR909 Link/record exists on owning write, rewriting".
     03  IR910          pic x(28) value "IR910 Rewrite failed as well".
*>
 Linkage Section.
*>**************
 copy "irswsnl.cob" replacing nl-record by WS-NL-Record.
*>
 copy "wssystem.cob".
*>
 copy "wsfnctn.cob".
*>
 copy "wsnames.cob".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 Procedure Division Using System-Record

                          WS-NL-Record

                          File-Access
                          File-Defs
                          ACAS-DAL-Common-data.
*>********************************************
*>
 aa-Process-Flat-File Section.
*>***************************
 aa010-main.
*>
*>  For logging only.
*>
     move     1      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock - used in FH logging
     move     11     to WS-Log-File-No.  *> Cobol/RDB, File/Table within sub System.
*>
*>   Now Test for valid key for start, read-indexed and delete
*>
     evaluate File-Function
              when  4   *> fn-read-indexed
              when  9   *> fn-start
                if     File-Key-No not = 1
                       move 998 to WE-Error       *> file seeks key type out of range        998
                       move 99 to fs-reply
                       go   to aa999-main-exit
                end-if
              when     8  *> fn-delete
                if     File-Key-No not = 1        *> 1  is only for RDB as Cobol does it on primary key
                       move 996 to WE-Error       *> file seeks key type out of range        996
                       move 99 to fs-reply
                       go   to aa999-main-exit
                end-if
     end-evaluate.
*>
*>    TAKEN from acasirsub4 22/12/16
*>
*>  Special to allow RDB equivilent of Open file as output
*>   therefore removing any existing records by doing a
*>     special Delete-All instead.
*>
     if       fn-Open and
              fn-output
         and  not FS-Cobol-Files-Used  *> RDB processing
 *>             set fn-delete-all to true
 *>             move zero to access-type
              perform ba-Process-RDBMS
              go to AA-Main-Exit
     end-if.
*>
*> Check if data files or RDBMS processing  !!
*>
     if       not FS-Cobol-Files-Used
              move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses    *> needed for DAL? not JC/dbpre versions
              perform ba-Process-RDBMS                                *>  Can't hurt
              go to AA-Main-Exit
     end-if.
*>
*> Test  Rec lengths first.
*>
     perform  ba012-Test-WS-Rec-Size-2.
*>
*>  File paths for Cobol File has already done in main menu module
*>
*>******************************************************************************
*> So we are processing Cobol Flat files, as Dup processing, or by themselves. *
*>    if reading, get it but will be overwritten by rdb processing if set,     *
*>      otherwise will write/rewrite/delete etc, to both formats               *
*>******************************************************************************
*>
     move     zero   to  WE-Error                                   *> as in irsub1
 *>  ?                      FS-Reply.
     move     spaces to SQL-Err SQL-Msg SQL-State.
*>
     evaluate File-Function
        when  1
              go to aa020-Process-Open
        when  2
              go to aa030-Process-Close
        when  3
              go to aa040-Process-Read-Next
        when  4
              go to aa050-Process-Read-Indexed
        when  5
              go to aa070-Process-Write
        when  7
              go to aa090-Process-Rewrite
        when  8
              go to aa080-Process-Delete
        when  9
              go to aa060-Process-Start
        when  13                                       *> fn-Read-Next-Raw
              go to aa045-Process-Read-Next-Raw
        when  15                                        *> fn-Write-Raw
              go to aa170-Process-Write-Raw
        when  other
              go to aa100-Bad-Function
     end-evaluate.
*>
*>  Should never get here but in case :(
     go       to aa100-Bad-Function.
*>
 aa020-Process-Open.
     move     spaces to WS-File-Key.     *> for logging
     move     201 to WS-No-Paragraph.
     if       fn-input
              open input Nominal-Ledger
              if   Fs-Reply not = zero
                   move  1 to we-error     *> as in irsub1
                   go to aa999-Main-Exit
              end-if
              move     "OPEN Input IRS NL File" to WS-File-Key
      else
       if     fn-i-o
              open i-o Nominal-Ledger
 *>             if       fs-reply not = zero
 *>                      close       Nominal-Ledger
 *>                      open output Nominal-Ledger           *> Doesnt create in i-o
 *>                      close       Nominal-Ledger
 *>                      open i-o    Nominal-Ledger
              if   fs-reply = 41                              *> already open so close and open
                   close Nominal-Ledger
                   go to aa020-Process-Open
              end-if
              if   fs-Reply = 47 or 48 or 49                  *> no perms to do requested (no write perms etc)
                   move  1 to we-error     *> as in irsub1
                   move     "OPEN I/O IRS NL File FAILED" to WS-File-Key
                   go to aa999-Main-Exit
              end-if
              if   fs-Reply not = zero
                   move  1 to we-error     *> as in irsub1
                   move     "OPEN I/O IRS NL File FAILED" to WS-File-Key
                   go to aa999-Main-Exit
              end-if
              move     "OPEN I/O IRS NL File" to WS-File-Key
       else
        if    fn-output
              open output Nominal-Ledger         *> caller should check fs-reply
              move     "OPEN Output IRS NL File" to WS-File-Key
        else
         if   fn-extend                      *> Must not be used for ISAM files
*>              open extend Nominal-Ledger
              move 997 to WE-Error
              move 99  to FS-Reply
              go to aa999-main-exit
         end-if
        end-if
       end-if
     end-if.
     move     zero to Cobol-File-Status.
     if       fs-reply not = zero
              move 1 to we-error.            *> JIC but shouldnt happen as tested for.
     go       to aa999-main-exit.            *> with test for dup processing
*>
 aa030-Process-Close.
     move     202 to WS-No-Paragraph.
     move     spaces to WS-File-Key.     *> for logging
     close    Nominal-Ledger.
*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
     move     zero to Cobol-File-Status.
     move     "CLOSE IRS NL File" to WS-File-Key.
     perform  aa999-main-exit.
     move     zero to  File-Function
                       Access-Type.              *> close log file
     perform  Ca-Process-Logs.
     go       to aa-main-exit.
*>
 aa040-Process-Read-Next.
*>
*>   Process READ next record ignoring Sub-Nominal pointers.
*> ?   This is processed after
*> ?   Start code as its really Start/Read next at point aa041
*>
     move     203 to WS-No-Paragraph.
     if       Cobol-File-Eof          *> This block should NOT occur
              move 10 to FS-Reply
                         WE-Error
              move 3 to WE-Error                 *> as in irsub1
              move spaces to
                             SQL-Err
                             SQL-Msg
              stop "Cobol File EOF-RN"               *> for testing because it should not have got here !!
              go to aa999-main-exit
     end-if.
*>
 aa041-Reread.
     read     Nominal-Ledger next record at end
              move 10 to WE-Error FS-Reply        *> EOF
              move 3 to WE-Error                 *> as in irsub1
              set Cobol-File-EoF to true
              move 1 to Cobol-File-Status         *> JIC above dont work :)
              initialize WS-NL-Record
              move "EOF" to WS-File-Key           *> for logging
              go to aa999-main-exit
     end-read.
     if       FS-Reply not = zero
              move   "Read Next failure on IRS NL File" to WS-File-Key
              go to aa999-main-exit.
     move     Record-1 to  WS-NL-Record.
*>
*> test to see if pointer record [ from irsub1 ]
*>
     if       Sub
              go to aa041-Reread.
*>
     move     NL-Key   to WS-File-Key.
     move     zeros to WE-Error FS-Reply.
     go to    aa999-main-exit.
*>
 aa045-Process-Read-Next-Raw.
*>
*>   Process READ next record.
*>     This process reads ALL records.
*>
     move     213 to WS-No-Paragraph.
     if       Cobol-File-Eof          *> This block should NOT occur
              move 10 to FS-Reply
                         WE-Error
              move 3 to WE-Error                 *> as in irsub1
              move spaces to
                             SQL-Err
                             SQL-Msg
              stop "Cobol File EOF-RNR"               *> for testing because it should not have got here !!
              go to aa999-main-exit
     end-if.
*>
     read     Nominal-Ledger next record at end
              move 10 to WE-Error FS-Reply        *> EOF
              move 3 to WE-Error                 *> as in irsub1
              set Cobol-File-EoF to true
              move 1 to Cobol-File-Status         *> JIC above dont work :)
              initialize WS-NL-Record
              move "EOF" to WS-File-Key           *> for logging
              go to aa999-main-exit
     end-read.
     if       FS-Reply not = zero
              move     "Read Raw failure on IRS NL File" to WS-File-Key
              go to aa999-main-exit.
     move     Record-1 to  WS-NL-Record.
*>
*> test to see if pointer record [ from irsub1 ]
*>      OMITTED as reading all records RAW
 *>    if       Sub
 *>             go to aa041-Reread.
*>
     move     NL-Key   to WS-File-Key.
     move     zeros to WE-Error FS-Reply.
     go to    aa999-main-exit.
*>
*>   The next block will never get executed unless performed  so is it needed ?
*>
 aa047-Eval-Keys.
     evaluate File-Function      *> Set up keys just for logging
              when  4             *> fn-read-indexed
              when  5             *> fn-write
              when  7             *> fn-re-write
              when  8             *> fn-delete
              when  9             *> fn-start
                    evaluate  File-Key-No
                              when   1
                                     move   NL-Key  to WS-File-Key
                                                       Key-1
                              when   other
                                     move   spaces  to WS-File-Key
                    end-evaluate
              when  other
                    move   spaces  to WS-File-Key
     end-evaluate.
*>
 aa050-Process-Read-Indexed.
*>
*>   Coding from original irsub1
*>
*> copy the key to main file area
*> if retrieve record by key set up for Owning or Sub-Nominal
*>    pointer record
*>
     move     204 to WS-No-Paragraph.
 *>    perform  aa047-Eval-keys.
*>
 aa051-Reread.
     move     NL-Key to Key-1.         *> in case of goto Reread
     read     Nominal-Ledger    invalid key
              move 21 to we-error fs-reply
              move  2 to we-error      *> from irsub1
              move  NL-Key to WS-File-Key
              go to aa999-main-exit
     end-read
     move  Record-1  to WS-NL-Record.
     move  NL-Key    to WS-File-Key.
     move  zero      to FS-Reply WE-Error.
*>
*> Pointer has been read if sub
*>
     if       Sub
              move NL-Owning  to NL-Sub-Nominal
              move NL-Pointer to NL-Owning
              go to aa051-Reread.
     move     zero to Cobol-File-Status.
     go       to aa999-main-exit.
*>
 aa060-Process-Start.
*>
*>  Check for Param error 1st on start   WARNING Not logging starts
*>
     move     205 to WS-No-Paragraph.
     move     zeros to fs-reply
                       WE-Error.
     move     zero to Cobol-File-Status.
     move     NL-Key to WS-File-Key
                        Key-1.
     move     zero   to Sub-Nominal.
*>
     if       access-type < 5 or > 8                   *> NOT using 'not >'
              move 998 to WE-Error                     *> 998 Invalid calling parameter settings
              go to aa999-main-exit
     end-if
*>
*>  Now do Start primary key before read-next
*>
     if       fn-equal-to
              start Nominal-Ledger key = Key-1 invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub1
                    go to aa999-main-exit
              end-start
     end-if
     if       fn-not-less-than
              start Nominal-Ledger key not < Key-1 invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub1
                    go to aa999-main-exit
              end-start
     end-if
     if       fn-greater-than
              start Nominal-Ledger key > Key-1 invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub1
                    go to aa999-main-exit
              end-start
     end-if
*>
     if       fn-less-than         *> Not used in irsub1
              start Nominal-Ledger key < Key-1 invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub1
                    go to aa999-main-exit
              end-start
     end-if
*>
*> Now go back and read next record [ from irsub1 ]
*>
     perform  aa999-main-exit.   *> logging
     go       to aa041-Reread.
*>
 aa070-Process-Write.
     move     206 to WS-No-Paragraph.
     move     WS-NL-Record to Record-1.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     move     NL-Key to WS-File-Key.
     write    Record-1 invalid key
              move 22 to FS-Reply    *> rest is from irsub1
              display IR906 at 2401 with foreground-color 4
              accept WS-Reply at 2438.    *> TESTING
     if       Owner
              go  to aa999-main-exit.
*>
*> Extra processing for sub-nominal.    From irsub1
*>
     move     "O" to NL-Type.
     move     WS-NL-Record to Record-1.
     rewrite  Record-1 invalid key
              display IR907 at 2401 with foreground-color 4
              accept WS-Reply at 2432.    *> TESTING
*>
*>  Extra code to stop zero keys  21/12/16
*>
     if       NL-Sub-Nominal = zero
              go to aa999-Main-Exit.
*>
     move     NL-Owning      to NL-Pointer.
     move     NL-Sub-Nominal to NL-Owning.
     move     zero           to NL-Sub-Nominal.
     move     "S"            to NL-Type.
     move     WS-NL-Record to Record-1.
     write    Record-1 invalid key
              display IR908 at 2401 with foreground-color 4
              accept WS-Reply at 2435.    *> TESTING
     move     NL-Owning  to NL-Sub-Nominal.   *> Do not know why this was missed out
     move     NL-Pointer to NL-Owning.        *>  but restored incase used by caller
     move  NL-Key to WS-File-Key.
     go       to aa999-main-exit.
*>
 aa080-Process-Delete.
     move     207 to WS-No-Paragraph.
     move     NL-Key to Key-1.             *> NOT in irsub1 ??
     move  NL-Key to WS-File-Key.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
*>
*> Delete record and pointer if neccessary
*>
     delete   Nominal-Ledger record.
     if       Owner
              go       to aa999-main-exit.
*>
*> Delete the pointer
*>
     move     NL-Sub-Nominal to NL-Owning.
     move     zero           to NL-Sub-Nominal.
     move     NL-Key         to Key-1.
     delete   Nominal-Ledger record.
     go       to aa999-main-exit.
*>
 aa090-Process-Rewrite.
*>
     move     208 to WS-No-Paragraph.
     move     WS-NL-Record to Record-1.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     move  NL-Key to WS-File-Key.
     rewrite  Record-1.
     go       to aa999-main-exit.
*>
 aa170-Process-Write-Raw.
*>
*>  Just will write no with no tests for owner or sub
*>   used with nominalLD
*>
     move     216 to WS-No-Paragraph.
     move     WS-NL-Record to Record-1.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     move     NL-Key to WS-File-Key.
     write    Record-1 invalid key
              move 22 to FS-Reply    *> rest is from irsub1
              display IR909 at 2401 with foreground-color 4
              accept WS-Reply at 2448        *> TESTING
              rewrite  Record-1 invalid key
                  display IR910   at 2401 with foreground-color 4
                  accept WS-Reply at 2432    *> TESTING
     end-write.
     go       to aa999-main-exit.
*>
 aa100-Bad-Function.
*>
*> Houston; We have a problem
*>
     move     999 to WE-Error.                         *> 999
     move     99  to fs-reply.
*>
 aa999-main-exit.
     if       Testing-1
              perform Ca-Process-Logs
     end-if.
*>
 aa-main-exit.
*>
*> Now have processed cobol flat file,  so ..
 aa-Exit.
     exit program.
*>
 ba-Process-RDBMS section.
*>***********************
*>
*>********************************************************************
*>  Here we call the relevent RDBMS module for this table            *
*>   which will include processing any other joined tables as needed *
*>********************************************************************
*>
 ba010-Test-WS-Rec-Size.
*>
*>     Test on very first call only  (So do NOT use var A & B again)
*>       Lets test that Data-record size is = or > than declared Rec in DAL
*>          as we cant adjust at compile/run time due to ALL Cobol compilers ?
*>
     move     21 to WS-Log-File-no.        *> for FHlogger
*>
 ba012-Test-WS-Rec-Size-2.
*>
     if       A = zero                        *> so it is being called first time
              move     function Length (
                                         WS-NL-Record
                                                 ) to A
              move     function length (
                                        Record-1
                                                 ) to B
              if   A < B                      *> COULD LET caller module deal with these errors !!!!!!!
                   move 901 to WE-Error       *> 901 Programming error; temp rec length is wrong caller must stop
                   move 99 to fs-reply        *> allow for last field ( FILLER) not being present in layout.
              end-if
              if       WE-Error = 901                  *> record length wrong so display error, accept and then stop run.
                       move spaces to Display-Blk
                       string IR902          delimited by size
                              A              delimited by size
                              " < "          delimited by size
                              "IRS-Nominal-Rec = " delimited by size
                              B              delimited by size    into Display-Blk
                       end-string
                       display Display-Blk at 2301 with erase eol     *> BUT WILL REMIND ME TO SET IT UP correctly
                       display IR901 at 2401 with erase eol
                       if  Testing-1
                           perform Ca-Process-Logs
                       end-if
                       accept Accept-Reply at 2433
                       go to ba-rdbms-exit
              end-if
*>
*>  Not a error comparing the length of records so - -
*>  Load up the DB settings from the system record as its not passed on
*>           hopefully once is enough  :)
*>
              move     RDBMS-DB-Name to DB-Schema
              move     RDBMS-User    to DB-UName
              move     RDBMS-Passwd  to DB-UPass
              move     RDBMS-Port    to DB-Port
              move     RDBMS-Host    to DB-Host
              move     RDBMS-Socket  to DB-Socket
     end-if.
*>
 ba015-Test-Ends.
*>
*>  First check if there is an open output and if so open 1st then
*>   we need to force a DELETE-ALL call to the DAL. [ Backup code ].
*>
     if       fn-Open
        and   fn-Output
              perform ba020-Process-Dal
              set fn-Delete-All to true
     end-if.
*>
*>   HERE we need a CDF [Compiler Directive] to select the correct DAL based
*>     on the pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<<  ? >>>>>
*>        Do this after system testing and pre code release.
*>
*>  NOW SET UP FOR JCs pre-sql compiler system.
*>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
*>
 ba020-Process-DAL.
     call     "irsnominalMT" using File-Access
                                   ACAS-DAL-Common-data

                                   WS-NL-Record
     end-call.
*>
*>   Any errors leave it to caller to recover from
*>
 ba-rdbms-exit.
     exit     section.
*>   ****     *******
*>
 Ca-Process-Logs. *> Not called on DAL access as it does it already
*>**************
*>
     call     "fhlogger" using File-Access
                               ACAS-DAL-Common-data.
*>
 ca-Exit.     exit.
*>
*>
 end program acasirsub1.
