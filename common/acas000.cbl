       >>source free
*>***********************************************
*>                                              *
*>      System File/Table Handler               *
*>        for all four records                  *
*>                                              *
*>  The Program name is taken from the FILE-nn  *
*>       used in the cobol file select.         *
*>                                              *
*>  As this module only uses one file it is     *
*>   coded differently with one less params     *
*>    and other functional differences.         *
*>                                              *
*>***********************************************
*>
 identification division.
 Program-Id.            acas000.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2018-2026 and later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             System File Handler.
*>                      *******************
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>                      --------------------------------------------------- ^^^^^ ---------
*>
*>   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING
*>
*>        The module acas011 (along with stockMT) are the FH (cobol File Handler for I/O)
*>            and DAL (Data Access Layer) for RDBMS direct I/O processing and these two modules
*>                 are the first modules written (& tested) for the ACAS system and specifically
*>                  for stock control.
*>
*>        Therefore they are the modals for all other FH and DALs.
*>          This means that any bugs found in one of them that is NOT file specific code changes
*>            have to be added to all existing other FH and or DAL modules.
*>               This must be done immediately after all changes to any one so that no mods are
*>                    forgotten about.
*>
*>   **************************************** END OF WARNING ********************************
*>
*>                      This modules does all Cobol file handling for this file (System File).
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
*>                      Module naming is based on the File ID variable name and for the System
*>                      file which uses file-10  the FH is therefore acas000 1- the last two chars
*>                      reflect the same number as last two chars the 'file-nn' name.
*>
*>                      Did it have to be this way ? no but it is easy to see in the original
*>                      code the name in the select statement for the Cobol file.
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
*>                      systemMT,
*>                      dfltMT,
*>                      finalMT &
*>                      sys4MT -
*>                                DAL (RDB Data Access Layer) or a variation
*>                      Selected via CDF etc [to be added sometime ].
*>
*>**
*> Error Messages Used.
*>
*>                      AC901 Note error and hit return
*>                      AC902
*>**
*> Version.             1.00 29/02/2012. Rewritten June 2016 after creating the DAL.
*>
*>                      This module is the first of the ACAS File Handlers and
*>                      will act as the model for all the others which in turn
*>                      is lightly modelled on the irsub modules for IRS.
*>
*>
*> Changes.
*> 29/02/12 vbc - Created for GnuCobol v2.0+. Code also to be tested with MF VC
*>                ** UNDER TEST ** but there again every thing is!
*> 17/05/16 vbc - Adding code for log file.
*>                Notes about error messages.
*> 24/06/16 vbc - Minor coding errors with a evaluate.
*> 02/07/16 vbc - .01 Missing DB params in system rec not moved to DB-xx in wsfnctn.
*> 04/08/16 vbc       Moved logging code into a new module to be called
*>                    from here and the systemMT code.
*> 04/08/16 vbc - .02 Test on read for read next at end bypass moves etc.
*> 21/07/16 vbc - .03 Minor tidy up  of code & comments near the call to the DAL.
*>                    Extra module comments and notes.
*> 25/07/16 vbc -     Taken from acas011 with same versioning.
*> 27/07/16 vbc - .04 Rem'd out some mv zero to fs-reply but don't think it is causing issues, may be
*> 27/08/16 vbc -     Taken from acas010 with same versioning.
*> 26/09/16 vbc - .05 Updated as a fair number of changes / differences to the modal !
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 09/12/16 vbc - .06 Re-added test for normal file-access configs in addition to '66'.
*> 19/02/17 vbc - .07 For all calls to the DALs use system-record as the
*>                    contents will be moved to the correct record by caller.
*> 25/04/17 vbc - .08 Removed display for AC908 as not needed as produces err 35.
*> 03/02/18 vbc - .09 Moved 'Open' msg to start for OPEN
*>                    like wise msgs for the other operations for logging.
*> 04/02/18 vbc - .10 Clear before string access msg for logging.
*> 05/02/18 vbc - .11 Extra checks for file open & closewith new WE-Error msg (941).
*> 28/02/18 vbc - .12 Added recs test for FH at ba012-Test-WS-Rec-Size-2
*> 07/12/22 vbc - .13 Chgd Vars A & B to pic 999 toi keep GC v3.2 happy.
*> 10/12/22 vbc - .14 chg to perform ba-Process-RDBMS + goto exit, 2 remove GC warning msg
*>                    from latest v3.2 code WITH ba-Main-Exit chgd to exit section.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc - 3.3.00 Version update and builds reset.
*> 14/10/25 vbc - 3.3.01 Pre-Support for RRN (File-Key-No) = 5 for Payroll if ever used.
*>                       Notes in systemMT.scb updated as well.
*>
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              1. File and table WS record : -
*>    acas000                  System-Record = Contents of data record to be written/read
*>                             from ws-System-Record, Default-Record, Final-Record & System-Record-4.
*>                          2. File-Access = File-Function as needed.
*>                                        Access-Type   as needed.
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
*>                                     998* = File-Key-No Out Of Range not 1, 2 or 3 or 4.
*>                                     997* = Access-Type wrong (< 5 or > 8)
*>                                     996* = File Delete key out of range (not = 1 or 2)
*>                                     995* = During Delete SQLSTATE not '00000' investigate using MSG-Err/Msg
*>                                     994* = During Rewrite,                     ^^ see above ^^
*>                                     990* = Unknown and unexpected error, again ^^ see above ^^
*>                                     989* = Unexpected error on Read-Indexed, investigate as above.
*>                                     941  = File already opened.  with fs-reply = 41. Should not happen!
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
*>                System File.
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
 copy "selsys.cob".
*>
 data division.
 file section.
*>***********
 copy "fdsys.cob".
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(17)    value "acas000 (3.3.01)".
*>
 77  ws-reply           pic x      value space.
*>
 77  A                  pic 9(4)              value zero.  *> A & B used in 1st test ONLY
 77  B                  pic 9(4)              value zero.  *>  in ba-Process-RDBMS
 77  Display-Blk        pic x(75)             value spaces.
 77  Cobol-File-Status  pic 9                 value zero.
     88  Cobol-File-Eof                       value 1.
*>
 01  Error-Messages.
*> System Wide
*> Module Specific
     03  AC901          pic x(31) value "AC901 Note error and hit return".
     03  AC902          pic x(32) value "AC902 Program Error: Temp rec = ".
*>                                        yyy < System-Rec = zzz
*>
 Linkage Section.
*>**************
*>
*> Fields renamed as wsssytem also in FD.
*>
 copy "wssystem.cob" replacing System-Record by WS-System-Record
                               File-System-Used        by WS-File-System-Used
                               File-Duplicates-In-Use  by WS-File-Duplicates-In-Use
                               FS-Cobol-Files-Used     by WS-FS-Cobol-Files-Used
                               FS-RDBMS-Used           by WS-FS-RDBMS-Used
                               FS-Duplicate-Processing by WS-FS-Duplicate-Processing
                               RDBMS-Flat-Statuses     by WS-RDBMS-Flat-Statuses.
*>
*> Here are the other three records held as relative, in the system file
*>   OOPS, not actually used here or by a call.
*>
*> copy "wsdflt.cob".
*> copy "wsfinal.cob".
*> copy "wssys4.cob".
*>
 copy "wsfnctn.cob".
*>
 copy "wsnames.cob".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 Procedure Division Using *>      System-Record

                          WS-System-Record   *> with images for the other three record types as same size

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
     move     0      to WS-Log-System.   *> 0 = Params, 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock, 4 FH logging
     move     10     to WS-Log-File-No.  *> RDB, File/Table
*>
*>   Now Test for valid key for read-indexed : -
*>    1 = params rec, 2 = default rec,
*>    3 = final rec & 4 = system totals rec.
*>
     evaluate File-Function
              when  4   *> fn-read-indexed
              when  5   *> fn-write
              when  7   *> fn-re-write
                if     File-Key-No < 1 or > 5     *> Chg 14/10/25 to support PY
                       move 998 to WE-Error       *> file seeks key type out of range        998
                       move 99 to fs-reply
                       go   to aa999-main-exit
                end-if
     end-evaluate.
*>
*> Check if data files or RDBMS processing or are we doing both !!
*>
*>   All programming must be directly requested, ONLY.
*>
*>  Unique for acas000 ONLY we check for FA-RDBMS status in wsfnctn as the ones in system-record
*>   can be altered to direct acas000 to process the other processing mode (cobol / RDB)
*>    as well as the system-record being temporarily over-written by the other record types being
*>     read or written out
*>      so a value of 66 in FA-RDBMS means take that value for mode (rdb) instead otherwise it is 00.
*>
     if       FA-RDBMS-Flat-Statuses = "66"     *> same as Cobol-File-Used = 1 = RDB (wsfnctn)
              perform ba-Process-RDBMS            *>   MUST CHANGE ALL OTHER MODULES
              go to AA-Main-Exit
     end-if
*>
*> Test  Rec lengths first.
*>
     perform  ba012-Test-WS-Rec-Size-2.
*>
*>
 *>    if       not WS-FS-Cobol-Files-Used              *> in system-record [ not = zero ]
 *>             move WS-RDBMS-Flat-Statuses             *> move WS S-R data to FD S-R
 *>                        to FA-RDBMS-Flat-Statuses    *> needed for DAL? not JC/dbpre versions
 *>             go to ba-Process-RDBMS                  *> Do NOT overwrite as poss. non header rec
 *>   end-if.
*>  ????
*>  File paths for Cobol File has already done in main menu module
*>
     move     spaces to SQL-Err SQL-Msg SQL-State.
*>
     evaluate File-Function
        when  1
              go to aa020-Process-Open
        when  2
              go to aa030-Process-Close
        when  4
              go to aa050-Process-Read-Indexed       *> Read relative, keys are 1 thru 4
        when  5
              go to aa070-Process-Write
        when  7
              go to aa090-Process-ReWrite
        when  other                          *> 6 is spare / unused, no delete (8) or start (9)
              go to aa100-Bad-Function
     end-evaluate.
*>
*>  Should never get here but in case :(
     go       to aa100-Bad-Function.
*>
 aa020-Process-Open.
     move    "OPEN SYSTEM File" to WS-File-Key
     move     201 to WS-No-Paragraph.
     move     zero to FS-Reply WE-Error.  *> 03/02/18
*>
     if       Cobol-File-Status = 1
              move "Already OPENed SYSTEM File" to WS-File-Key
              move 941 to WE-Error
              move 41  to FS-Reply
              go to aa999-Main-Exit
     end-if.
*>
     if       fn-input
              open input System-File
              if   Fs-Reply not = zero
                   move 35 to fs-Reply   *> remove display for 908
 *>                  close System-File
                   go to aa999-Main-Exit
              end-if
      else
       if     fn-i-o
              open i-o System-File
              if       fs-reply not = zero                 *> this block was in st010 at ba000-Setup-Stock
                       close       System-File
                       open output System-File             *> Doesnt create in i-o or does it.
                       close       System-File             *> if not, code for it
                       open i-o    System-File
              end-if                                       *> file-status will NOT be updated   ????
       else
        if    fn-output                                    *> should not need to be used
              open output System-File                      *> caller should check fs-reply
        else
         if   fn-extend                                    *> Must not be used for ISAM files - IT ISNT
*>              open extend System-File
              move 997 to WE-Error
              move 99 to fs-reply
              go   to aa999-main-exit
         end-if
        end-if
       end-if
     end-if.
     move     1 to Cobol-File-Status.                      *> file open.
     if       fs-reply not = zero
              move 999 to we-error.
     go       to aa999-main-exit.            *> with test for dup processing
*>
 aa030-Process-Close.
     move     202 to WS-No-Paragraph.
     move     spaces to WS-File-Key.         *> for logging
     move     zero to FS-Reply WE-Error.  *> 03/02/18
     if       Cobol-File-Status = 1
              close    System-File
              move     "CLOSE SYSTEM File" to WS-File-Key
     else
              move     "Already CLOSED: SYSTEM File" to WS-File-Key
     end-if
     move     zero to Cobol-File-Status.                   *> File closed.
     perform  aa999-main-exit.
     move     zero to  File-Function
                       Access-Type.              *> close log file
     perform  Ca-Process-Logs.
     go       to aa-main-exit.
*>
 aa050-Process-Read-Indexed.
*>
*> Process according to key number (1 thru 4) caller must issue MOVE
*>
*> Could put in test for file open,  and likewise for write & rewrite ?
*>    BUT SHOULD NOT BE NEEDED.
*>
     move     204 to WS-No-Paragraph.
     move     File-Key-No to rrn.
     move     spaces to WS-File-Key.
     string   "Read Indexed " File-Key-No into WS-File-Key.  *> 03/02/18
     move     zero to FS-Reply WE-Error.  *> 03/02/18
     read     System-File record into WS-System-Record.
     go       to aa999-main-exit.
*>
 aa070-Process-Write.   *> write to the relative record subject to File-Key-No  caller must issue MOVE
     move     206   to WS-No-Paragraph.
     move     zeros to FS-Reply  WE-Error.
     move     spaces to WS-File-Key.
     string   "Write " File-Key-No into WS-File-Key.  *> 03/02/18
     move     File-Key-No  to rrn.
     write    System-Record from WS-System-Record.
     go       to aa999-main-exit.
*>
 aa090-Process-Rewrite.   *> rewrite to the relative record subject to File-Key-No  caller must issue MOVE
*>
     move     208 to WS-No-Paragraph.
     move     zeros to FS-Reply  WE-Error.
     move     File-Key-No  to rrn.
     move     spaces to WS-File-Key.
     string   "Rewrite " File-Key-No into WS-File-Key.  *> 03/02/18
     rewrite  System-Record from WS-System-Record.
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
*> Now have processed cobol flat file .
*>
 aa-Exit.
     exit program.
*>
 ba-Process-RDBMS section.
*>***********************
*>
*>********************************************************************
*>  Here we call the relevent RDBMS module for each of the tables    *
*>   which will include processing any other joined tables as needed *
*>   internally.                                                     *
*>********************************************************************
*>
 ba010-Test-WS-Rec-Size.
*>
*>     Test on very first call only  (So do NOT use var A & B again)
*>       Lets test that Data-record size is = or > than declared Rec in DAL
*>          as we cant adjust at compile/run time due to ALL Cobol compilers ?
*>
     move     20 to WS-Log-File-no.        *> for FHlogger
*>
 ba012-Test-WS-Rec-Size-2.
*>
     if       A = zero                        *> so it is being called first time
              move     function Length (
                                        WS-System-Record
                                                 ) to A
              move     function length (
                                        System-Record
                                                 ) to B
              if   A < B                      *> COULD LET caller module deal with these errors !!!!!!!
                   move 901 to WE-Error       *> 901 Programming error; temp rec length is wrong caller must stop
                   move 99 to fs-reply        *> allow for last field ( FILLER) not being present in layout.
              end-if
              if       WE-Error = 901                  *> record length wrong so display error, accept and then stop run.
                       move spaces to Display-Blk
                       string AC902          delimited by size
                              A              delimited by size
                              " < "       delimited by size
                              "System-Rec = " delimited by size
                              B              delimited by size    into Display-Blk
                       end-string
                       display Display-Blk at 2301 with erase eol     *> BUT WILL REMIND ME TO SET IT UP correctly
                       display AC901 at 2401 with erase eol
                       if  Testing-1
                           perform Ca-Process-Logs
                       end-if
                       accept Accept-Reply at 2433
                       go to ba-rdbms-exit
              end-if
*>
*>  Not a error comparing the length of records so - -
*>  Load up the DB settings from the system record from COBOL file as its not passed on
*>           hopefully once is enough  :)
*>
              move     RDBMS-DB-Name in System-Record  to DB-Schema
              move     RDBMS-User    in System-Record  to DB-UName
              move     RDBMS-Passwd  in System-Record  to DB-UPass
              move     RDBMS-Port    in System-Record  to DB-Port
              move     RDBMS-Host    in System-Record  to DB-Host
              move     RDBMS-Socket  in System-Record  to DB-Socket
     end-if.
*>
 ba015-Test-Ends.
*>
*>   HERE we need a CDF [Compiler Directive] to select the correct DAL based
*>     on the pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<<  ? >>>>>
*>        Do this after system testing and pre code release.
*>
*>  NOW SET UP FOR JC pre-sql compiler system.
*>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
*>
     evaluate File-Key-No
        when  1
              call     "systemMT" using File-Access
                                        ACAS-DAL-Common-data
                                        WS-System-Record
              end-call
        when  2
              call     "dfltMT" using   File-Access
                                        ACAS-DAL-Common-data
                                        WS-System-Record *> Default-Record
              end-call
        when  3
              call     "finalMT" using  File-Access
                                        ACAS-DAL-Common-data
                                        WS-System-Record *> Final-Record
              end-call
        when  4
              call     "sys4MT" using   File-Access
                                        ACAS-DAL-Common-data
                                        WS-System-Record *> System-Record-4
              end-call
        when  5          *> support for PY may be
              call     "systemMT" using File-Access
                                        ACAS-DAL-Common-data
                                        WS-System-Record
              end-call
     end-evaluate.
*>
*>   Any errors leave it to caller to recover from
*>
 ba-rdbms-exit.
     exit     section.
*>   ****     *******
*>
 Ca-Process-Logs.     *> Not called on DAL access as it does it already
*>**************
*>
     call     "fhlogger" using File-Access
                               ACAS-DAL-Common-data.
*>
 ca-Exit.     exit.
*>
 end program acas000.
