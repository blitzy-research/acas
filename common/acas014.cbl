       >>source free
*>***********************************************
*>                                              *
*>                PL & SL Delivery              *
*>               File/Table Handler             *
*>                                              *
*>  The Program name is taken from the FILE-nn  *
*>       used in the cobol file select.         *
*>***********************************************
*>
 identification division.
 Program-Id.            acas014.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             PL & SL Delivery File Handler.
*>                      **************
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>                      --------------------------------------------------- ^^^^^ ---------
*>
*>   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING
*>
*>        This module has been taken from the first written acas011 (along with its DAL module)
*>          which was the first FH (cobol File Handler for I/O)
*>            and DAL (Data Access Layer) for RDBMS direct I/O processing and these two modules
*>                 are the first modules written (& tested) for the ACAS system and specifically
*>                  for stock control.
*>
*>        Therefore they are the models for all other FH and DALs.
*>          This means that any bugs found in one of them that is NOT file specific code changes
*>            have to be added to all existing other FH and or DAL modules.
*>               This must be done immediately after all changes to any one so that no mods are
*>                    forgotten about.
*>
*>   **************************************** END OF WARNING ********************************
*>
*>                      This modules does all Cobol file handling for the file
*>                                 (Delivery).
*>
*>                      If Cobol Flat files are in use (via the system parameter file settings)
*>                      which is passed via the wsfnctn (via copybook) / File-Access data block
*>                      via the application module and each FH & DAL.
*>                      It will read/write/delete/update/open/close as required and requested.
*>                      NOTE the same fields are used for ALL of the FL and DAL modules so
*>                      checking the error flags have to be done after each call before clearing.
*>
*>                      If RDBMS (Relational DataBase Management Systems) is in use it will call
*>                      the specific module to handle similar processing passing the equivelent
*>                      RDB (Relational DataBase) row as a Cobol file record (01 level) moving
*>                      row by row to the correct Cobol flat file fields as required.
*>                      These retrieve ALL columns and there fore the DAL modules cannot handle
*>                      processing for selective columns, e.g., only updating one field/column
*>                      as the whole record / row must be read or written to/from the RDB table.
*>
*>                      Module naming is based on the original irsubn FH the FH is therefore acasirs1
*>                       - the last one char
*>                      reflect the same number as one char in the 'irsubn' name.
*>
*>                      RDB DAL (Data Access Layer) modules are individually modified to handle:
*>                      MS SQL server, Mysql, DB2, Postgres and Oracle as available and tested.
*>                      These are contained in seperate directories for each RDB, eg
*>                       'MSSQL' (MS SQL Server), 'Mysql', 'DB2', 'Postgres'. 'Oracle'.
*>                       You need to compile from the correct directory for the specific
*>                       RDB you will use and have installed along with all of the development
*>                       libraries and include files etc using the correct pre-compiler tool
*>                       to process the 'EXEC SQL' code converting to Cobol calls etc.
*>
*>                      For specific SQL servers supported the pre-compiler system is included
*>                       where ever possible but for some, copyright reasons may prevent
*>                       inclusion. In some cases for one specific RDB more than one precompiler
*>                       is used as an experiment to help find the ideal one to use.
*>
*>                      In addition:
*>                        If the system has been set up to (see the System File set up via the
*>                        main menu module for each sub system), also process BOTH flat file
*>                        AND the correct rdb table/s,
*>                        it will write/delete/update etc to both but read from 1=Flat and be
*>                        overwritten by the rdb access. This was set up more for testing the
*>                        new code for both cobol files and the rdb accessing modules.
*>                       This can help in transferring the Cobol flat files to rdb tables but
*>                        see below regarding the Load programs/modules.
*>
*>                      If you wish to convert a running ACAS system over from Flat files
*>                      to RDBMS see below. However it is strongly recommended to not to use
*>                      the Duplicate processing of files/table as outlined above but:
*>
*>                      Included are LMs (Load Modules) to convert each ISAM
*>                      (Indexed Sequential) file to the rdb database tables if you wish to
*>                      convert the system in one hit, without using the Duplicate file/RDB
*>                      processing procedures. These will also need to be compiled from the
*>                      specific LM directory that contains the rdb DAL modules.
*>
*>                      A specific program or bash process will be created to use, that will run
*>                      each LM process for all existing Cobol files. These are created during
*>                      writing of the FH and DAL for each file/table if only to help in testing
*>                      them.
*>**
*> Called Modules:
*>                      deliveryMT -
*>                                DAL (RDB Data Access Layer) or a variation
*>                      Selected via CDF etc [to be added].
*>
*>**
*> Error Messages Used.
*>
*>                      AC901
*>                      AC903
*>**
*> Version.             1.00 29/02/2012. Rewritten June 2016 after creating the DAL.
*>
*>                      This module is a ACAS File Handlers and is taken from
*>                      the first one (acas001) and
*>                      is lightly remodelled on the irsub modules for IRS.
*>
*>
*> Changes.
*> 15/11/16 vbc - .04 Taken from acasirsub1 & irsub4.
*> 24/11/16 vbc - .05 Extra function (6) for Delete-ALL records which
*>                    is the same as open output with a Cobol file.
*> 04/01/17 vbc -     Taken from acas006 (glposting)
*> 28/02/18 vbc - .06 Added recs test for FH at ba012-Test-WS-Rec-Size-2
*>                    and removed msgs 906 & 7 renamed 901/2 to AC901/2.
*> 29/04/18 vbc - .07 Resetting Cobol-File-Status for write,rewrite,delete, start etc
*> 07/12/22 vbc - .08 Chgd Vars A & B to pic 999 toi keep GC v3.2 happy.
*> 10/12/22 vbc - .09 chg to perform ba-Process-RDBMS + goto exit, 2 remove GC warning msg
*>                    from latest v3.2 code WITH ba-Main-Exit chgd to exit section.
*> 31/05/23 vbc - .10 chgd WS-Log-File-No from 12 to 14.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              1. File and table WS record : -
*>    acas014 ONLY          WS-Delivery-Record = Contents of data record to be written/read
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
*>                                     99 = Indicates an error see WE-Error for more info
*>                          WE-Error   0    = Operation completed successfully
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
*>
*>       During testing a log file will be created containing datetime stamp, task and return codes
*>       for both FS-Reply and WE-Error and table used along with the RDB error number and message
*>         In this case for the
*>                Delivery File.
*>
*>       WARNING - This file could get large so needs manually deleting after examination.
*>
*>  Programmer note : CONSIDER WRITING A reporting program for this with report selection criteria.
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
 copy "seldel.cob".
*>
 data division.
 file section.
*>***********
*>
 copy "fddel.cob".
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(20)  value "acas014 (3.3.00)".
*>
 77  WS-Reply           pic x      value space.
*>
 77  A                  pic 9(4)             value zero.  *> A & B used in 1st test ONLY
 77  B                  pic 9(4)             value zero.  *>  in ba-Process-RDBMS
 77  Display-Blk        pic x(75)             value spaces.
 77  Cobol-File-Status  pic 9                 value zero.
     88  Cobol-File-Eof                       value 1.
*>
 01  Error-Messages.
*> System Wide
*> Module Specific
     03  AC901          pic x(31) value "AC901 Note error and hit return".
     03  AC903          pic x(32) value "AC903 Program Error: Temp rec = ".
*>                                        yyy < Delivery-Rec = zzz
*>
 Linkage Section.
*>**************
 copy "wsdel.cob".
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

                          WS-Delivery-Record

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
     move     6      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock, 6=PL & SL, - used in FH logging
     move     14     to WS-Log-File-No.  *> Cobol/RDB, File/Table within sub System.
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
*>  Special to allow RDB equivilent of Open file as output
*>   therefore removing any existing records by doing a
*>     special Delete-All instead.
*>
     if       fn-Open and
              fn-output
         and  not FS-Cobol-Files-Used  *> RDB processing
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
 *>    move     zero   to  WE-Error
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
        when  other                     *> 6 is unused
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
              open input Delivery-File
              if   Fs-Reply not = zero
                   move 35 to fs-Reply
                   close Delivery-File
                   go to aa999-Main-Exit
              end-if
      else
       if     fn-i-o
              open i-o Delivery-File
              if       fs-reply not = zero
                       close       Delivery-File
                       open output Delivery-File           *> Doesnt create in i-o
                       close       Delivery-File
                       open i-o    Delivery-File
              end-if
       else
        if    fn-output
              open output Delivery-File       *> caller should check fs-reply
        else
         if   fn-extend                      *> Must not be used for ISAM files
*>              open extend Delivery-File
              move 997 to WE-Error
              move 99  to FS-Reply
              go to aa999-main-exit
         end-if
        end-if
       end-if
     end-if.
     move     zero to Cobol-File-Status.
     move     "OPEN S/PL Delivery file" to WS-File-Key.
     if       fs-reply not = zero
              move 999 to we-error.
     go       to aa999-main-exit.        *> with test for dup processing
*>
 aa030-Process-Close.
     move     202 to WS-No-Paragraph.
     move     spaces to WS-File-Key.     *> for logging
     close    Delivery-File.
*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
     move     zero to Cobol-File-Status.
     move     "CLOSE S/PL Delivery file" to WS-File-Key.
     perform  aa999-main-exit.
     move     zero to  File-Function  *> REMOVE THIS IF FILE CLOSED FIRST
                       Access-Type.      *> close log file
     perform  Ca-Process-Logs.
     go       to aa-main-exit.
*>
 aa040-Process-Read-Next.
*>
*>    This is processed after
*>    Start code as its really Start/Read next at point aa041
*>
     move     203 to WS-No-Paragraph.
     if       Cobol-File-Eof          *> This block should NOT occur
              move 10 to FS-Reply
                         WE-Error
              move zeros to WS-Deliv-Key
              move spaces to
                             SQL-Err
                             SQL-Msg
              stop "Cobol File EOF"               *> for testing
              go to aa999-main-exit
     end-if.
*>
 aa041-Reread.
     read     Delivery-File next record at end
              move 10 to WE-Error FS-Reply        *> EOF
              set Cobol-File-EoF to true
              move 1 to Cobol-File-Status         *> JIC above dont work :)
              initialize WS-Delivery-Record
              move "EOF" to WS-File-Key           *> for logging
              go to aa999-main-exit
     end-read.
     if       FS-Reply not = zero
              go to aa999-main-exit.
     move     Delivery-Record to  WS-Delivery-Record.
     move     Deliv-Key   to WS-File-Key.
     move     zeros to WE-Error.
     go to    aa999-main-exit.
*>
 aa050-Process-Read-Indexed.
*>
     move     204 to WS-No-Paragraph.
     move     zero to Cobol-File-Status.
*>
 aa051-Reread.
     move     WS-Deliv-Key to Deliv-Key WS-File-Key.
     read     Delivery-File    invalid key
              move 21 to we-error fs-reply
              go to aa999-main-exit
     end-read
     move     Delivery-Record  to  WS-Delivery-Record.
     move     Deliv-Key to WS-File-Key.
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
     move     WS-Deliv-Key to WS-File-Key
                              Deliv-Key.
*>
     if       access-type < 5 or > 8                   *> NOT using 'not >'
              move 998 to WE-Error                     *> 998 Invalid calling parameter settings
              go to aa999-main-exit
     end-if
*>
*>  Now do Start primary key before read-next
*>
     if       fn-equal-to
              start Delivery-File key = Deliv-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       fn-not-less-than
              start Delivery-File key not < Deliv-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       fn-greater-than
              start Delivery-File key > Deliv-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
*>
     if       fn-less-than
              start Delivery-File key < Deliv-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
*>
*> Now go back and read next record  ??  or just exit ?  <<<<<<<<<
*>   IS SL USING START if so HOW ????
*>
     go       to aa999-main-exit.   *> logging
 *>    go       to aa041-Reread.
*>
 aa070-Process-Write.
     move     206 to WS-No-Paragraph.
     move     WS-Delivery-Record to Delivery-Record.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     move     Deliv-Key to WS-File-Key.
     write    Delivery-Record invalid key
              go to  aa999-main-exit.   *> logging
     move     Deliv-Key to WS-File-Key.
     go       to aa999-main-exit.
*>
 aa080-Process-Delete.
     move     207 to WS-No-Paragraph.
     move     WS-Deliv-Key to Deliv-Key.
     move     WS-Deliv-Key to WS-File-Key.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
*>
*> Delete record and pointer if neccessary
*>
     delete   Delivery-File record.
     go       to aa999-main-exit.
*>
 aa090-Process-Rewrite.
*>
     move     208 to WS-No-Paragraph.
     move     WS-Delivery-Record to Delivery-Record.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     move     Deliv-Key to WS-File-Key.
     rewrite  Delivery-Record.
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
*>
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
     move     22 to WS-Log-File-no.        *> for FHlogger
*>
 ba012-Test-WS-Rec-Size-2.
*>
     if       A = zero                        *> so it is being called first time
              move     function Length (
                                         WS-Delivery-Record
                                                 ) to A
              move     function length (
                                        Delivery-Record
                                                 ) to B
              if   A < B                      *> COULD LET caller module deal with these errors !!!!!!!
                   move 901 to WE-Error       *> 901 Programming error; temp rec length is wrong caller must stop
                   move 99 to fs-reply        *> allow for last field ( FILLER) not being present in layout.
              end-if
              if       WE-Error = 901                  *> record length wrong so display error, accept and then stop run.
                       move spaces to Display-Blk
                       string AC903          delimited by size
                              A              delimited by size
                              " < "          delimited by size
                              "Delivery-Rec = " delimited by size
                              B              delimited by size    into Display-Blk
                       end-string
                       display Display-Blk at 2301 with erase eol     *> BUT WILL REMIND ME TO SET IT UP correctly
                       display AC901 at 2401 with erase eol
                       move  Display-Blk to SQL-Msg
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
*>  NOW SET UP FOR JC pre-sql compiler system.
*>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
*>
 ba020-Process-DAL.
     call     "deliveryMT" using File-Access
                                  ACAS-DAL-Common-data

                                  WS-Delivery-Record
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
 end program acas014.
