       >>source free
*>***********************************************
*>                                              *
*>       Recurring Sales Invoice (AUTOGEN)      *
*>               File/Table Handler             *
*>                                              *
*>  The Program name is taken from the FILE-nn  *
*>       used in the cobol file select.         *
*> -------------------------------------------- *
*>***********************************************
*>
 identification division.
 Program-Id.            acas004.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2023 - 2026 and later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             SL Autogen File Handler.
*>                      Taken from acas016 the Sales Invoice File Handler.
*>                      *************************************************
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>                      --------------------------------------------------- ^^^^^ ---------
*>
*>   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING
*>
*>  Any bugs found in this module mean that all the others must also be
*>    checked including acas004.
*>
*>   **************************************** END OF WARNING ********************************
*>**
*> Called Modules:
*>                      slautogenMT -
*>                          DAL (RDB Data Access Layer) or a variation
*>                      Selected via CDF etc [to be added].
*>**
*> Error Messages Used.
*>
*>                      SL901 Note error and hit return
*>                      SL902 Program Error: Temp rec =yyy < Invoice-Rec = zzz
*>**
*> Version.             1.00 29/02/2012. Rewritten June 2016 after creating the DAL.
*>                      acas004 created from acas016 April 2023.
*>
*> Changes.
*> 17/02/23 vbc - .10 Missing period for move  999 to WE-Error in Open,
*> 17/04/23 vbc - .00 Set for acas004 from acas016. reset version no.
*> 20/05/23 vbc - .01 Match acas016 for move  Agen-Invoice-Key  to WS-File-Key.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              1. File and table WS record : -
*>    acas004 ONLY             WS-Invoice-Record = Contents of data record to be written/read
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
*>                                     998* = File-Key-No Out Of Range not 1, 2 or 3.
*>                                     997* = Access-Type wrong (< 5 or > 8)
*>                                     996* = File Delete key out of range (not = 1 or 2)
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
*>                Invoice File.
*>
*>       WARNING - This file could get large so needs manually deleting after examination.
*>
*>  Programmer note : CONSIDER WRITING A reporting program for this
*>                    with report selection criteria.
*>*****************************************************************
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
 copy "slSELautogen.cob".
*>
 data division.
 file section.
*>***********
 copy "slFDautogen.cob".
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(17)  value "acas004 (3.3.00)".
*>
 77  ws-reply           pic x      value space.
*>
 77  A                  pic 9(4)   value zero.  *> A & B used in 1st test ONLY
 77  B                  pic 9(4)   value zero.  *>  in ba-Process-RDBMS
 77  Display-Blk        pic x(75)  value spaces.
 77  Cobol-File-Status  pic 9      value zero.
     88  Cobol-File-Eof            value 1.
 *>
 *> TESING data
 *>
*> 01  WS-Temp-ED.
*>     03  ws-temp-ed-1   pic 9(8).
*>     03  WS-Temp-ed-2   pic 99.
*>
 01  Error-Messages.
*> System Wide
*> Module Specific
     03  SL901          pic x(31) value "SL901 Note error and hit return".
     03  SL902          pic x(32) value "SL902 Program Error: Temp rec = ".
*>                                        yyy < Invoice-Rec = zzz
*>
 Linkage Section.
*>**************
 copy "slwsinv.cob" replacing SInvoice-Header by WS-Invoice-Record
                              SInvoice-Bodies by WS-Invoice-Bodies.
*>
*> IS ABOVE STILL OK for AUTOgen ?
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

                          WS-Invoice-Record

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
     move     3      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging
     move     16     to WS-Log-File-No.  *> RDB, File/Table
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
                if     File-Key-No not = 1
                       move 996 to WE-Error       *> file seeks key type out of range        996
                       move 99 to fs-reply
                       go   to aa999-main-exit
                end-if
     end-evaluate.
*>
*> Check if data files or RDBMS processing
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
*>******************************************
*> So we are processing Cobol Flat files   *
*>******************************************
*>
*>  ?   move     zero   to  WE-Error
 *>  ?                      FS-Reply.
     move     spaces to SQL-Err SQL-Msg SQL-State.
*>
     evaluate File-Function
        when  1
              go to aa020-Process-Open
        when  2
              go to aa030-Process-Close
        when  3
        when  34                             *> fn-Read-Next-Header ???
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
        when  other                          *> 6 is spare / unused
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
              open input Agen-Invoice-File
              if   Fs-Reply not = zero
                   move 35 to fs-Reply
                   close Agen-Invoice-File
                   go to aa999-Main-Exit
              end-if
      else
       if     fn-i-o
              open i-o Agen-Invoice-File
              if       fs-reply not = zero              *> this block was in st010 at ba000-Setup-Invoice
                       close       Agen-Invoice-File
                       open output Agen-Invoice-File           *> Doesnt create in i-o
                       close       Agen-Invoice-File
                       open i-o    Agen-Invoice-File
              end-if                                      *> file-status will NOT be updated   ????
       else
        if    fn-output                      *> should not need to be used
              open output Agen-Invoice-File         *> caller should check fs-reply
        else
         if   fn-extend                      *> Must not be used for ISAM files
*>              open extend Agen-Invoice-File
              move 997 to WE-Error
              move 99  to FS-Reply
              go to aa999-main-exit
         end-if
        end-if
       end-if
     end-if.
*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
     move     zero to Cobol-File-Status.
     move     "OPEN SL AUTOGEN File" to WS-File-Key.
     if       fs-reply not = zero
              move  999 to WE-Error.
     go       to aa999-main-exit.            *> with test for dup processing
*>
 aa030-Process-Close.
     move     202 to WS-No-Paragraph.
     move     spaces to WS-File-Key.     *> for logging
     close    Agen-Invoice-File.
*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
     move     zero to Cobol-File-Status.
     move     "CLOSE SL AUTOGEN File" to WS-File-Key
     perform  aa999-main-exit.
     move     zero to  File-Function
                       Access-Type.              *> close log file
     perform  Ca-Process-Logs.
     go       to aa-main-exit.
*>
 aa040-Process-Read-Next.
*>
*>   Process READs, 1st is read next then read by key This is processed after
*>    Start code as its really Start/Read next
*>
     move     203 to WS-No-Paragraph.
     if       Cobol-File-Eof
              move 10 to FS-Reply
                         WE-Error
              move spaces to Agen-Invoice-Key
                             SQL-Err
                             SQL-Msg
              stop "Cobol File EOF"               *> for testing
              go to aa999-main-exit
     end-if
*>
     read     Agen-Invoice-File next record at end
              move 10 to we-error fs-reply        *> EOF
              set Cobol-File-EoF to true
              move 1 to Cobol-File-Status         *> JIC above dont work :)
              initialize Agen-Invoice-Record
              move "EOF" to WS-File-Key           *> for logging
              go to aa999-main-exit
     end-read.
     if       FS-Reply not = zero
              go to aa999-main-exit.
     move     Agen-Invoice-Record to WS-Invoice-Record.
     move     Agen-Invoice-Key  to WS-File-Key.
     move     zeros to WE-Error.
     go to    aa999-main-exit.
*>
 aa045-Eval-Keys.
     evaluate File-Function      *> Set up keys just for logging
              when  4             *> fn-read-indexed
              when  5             *> fn-write
              when  7             *> fn-re-write
              when  8             *> fn-delete    For delete can ignore Desc key
              when  9             *> fn-start
                    evaluate  File-Key-No
                              when   1
                                     move   WS-Invoice-Key     to Agen-Invoice-Key
                                     move   Agen-Invoice-Key   to WS-File-Key

                              when   other
                                     move   spaces             to WS-File-Key
                    end-evaluate
              when  other
                    move   spaces    to WS-File-Key
     end-evaluate.
*>
 aa050-Process-Read-Indexed.
*>
     move     204 to WS-No-Paragraph.
     perform  aa045-Eval-keys.
     move     zero to Cobol-File-Status.
     if       File-Key-No = 1
              read     Agen-Invoice-File key WS-Invoice-Key       invalid key
                       move 21 to we-error fs-reply
              end-read
              if       fs-Reply = zero
                       move     Agen-Invoice-Record to WS-Invoice-Record
                       move     Agen-Invoice-Key  to WS-File-Key

              else
                       initialize WS-Invoice-Record
                       move "Failed action" to WS-File-Key
              end-if
              go       to aa999-main-exit
     end-if.
     move     998 to WE-Error       *> file seeks key type out of range but should never get here       998
     move     99 to fs-reply
     go       to aa999-main-exit.
*>
 aa060-Process-Start.
*>
*>  Check for Param error 1st on start
*>
     move     205 to WS-No-Paragraph.
     perform  aa045-Eval-keys.
     move     zeros to fs-reply
                       WE-Error.
     move     zero to Cobol-File-Status.
*>
     if       access-type < 5 or > 8                   *> NOT using 'not >'
              move 998 to WE-Error                     *> 998 Invalid calling parameter settings
              go to aa999-main-exit
     end-if
*>
*>  Now do Start primary key before read-next ?
*>
     move     WS-Invoice-Key to Agen-Invoice-Key.
     if       File-Key-No = 1
        and   fn-equal-to
              start Agen-Invoice-File key = Agen-Invoice-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
        and   fn-less-than
              start Agen-Invoice-File key < Agen-Invoice-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
        and   fn-greater-than
              start Agen-Invoice-File key > Agen-Invoice-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
        and   fn-not-less-than
              start Agen-Invoice-File key not < Agen-Invoice-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
              move     Agen-Invoice-Key  to WS-File-Key.
*>
     go       to aa999-main-exit.
*>
 aa070-Process-Write.
     move     206 to WS-No-Paragraph.
     move     WS-Invoice-Record to Agen-Invoice-Record.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     write    Agen-Invoice-Record invalid key
              move 22 to FS-Reply
     end-write.
     move     Agen-Invoice-Key  to WS-File-Key.
     go       to aa999-main-exit.
*>
 aa080-Process-Delete.
     move     207 to WS-No-Paragraph.
     move     WS-Invoice-Record to Agen-Invoice-Record.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     delete   Agen-Invoice-File record invalid key
              move 21 to FS-Reply
     end-delete.
     move     Agen-Invoice-Key  to WS-File-Key.
     go       to aa999-main-exit.
*>
 aa090-Process-Rewrite.
*>
     move     208 to WS-No-Paragraph.
     move     WS-Invoice-Record to Agen-Invoice-Record.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     rewrite  Agen-Invoice-Record invalid key
              move 21 to FS-Reply
     end-rewrite
     move     Agen-Invoice-Key  to WS-File-Key.
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
 ba010-Test-WS-Rec-Size.   *> THIS IS WRONG FOR AUTOGEN <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<, ***********
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
                                        WS-Invoice-Record
                                                 ) to A
              move     function length (
                                        Agen-Invoice-Record
                                                 ) to B
              if   A < B                      *> COULD LET caller module deal with these errors !!!!!!!
                   move 901 to WE-Error       *> 901 Programming error; temp rec length is wrong caller must stop
                   move 99 to fs-reply        *> allow for last field ( FILLER) not being present in layout.
              end-if
              if       WE-Error = 901                  *> record length wrong so display error, accept and then stop run.
                       move spaces to Display-Blk
                       string SL902          delimited by size
                              A              delimited by size
                              " < "          delimited by size
                              "Agen-Invoice-Rec = " delimited by size
                              B              delimited by size    into Display-Blk
                       end-string
                       display Display-Blk at 2301 with erase eol     *> BUT WILL REMIND ME TO SET IT UP correctly
                       display SL901 at 2401 with erase eol
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
*>
*>   HERE we need a CDF [Compiler Directive] to select the correct DAL based
*>     on the pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<<  ? >>>>>
*>        Do this after system testing and pre code release.
*>
*>  NOW SET UP FOR JC pre-sql compiler system.
*>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
*>
     call     "slautogenMT" using File-Access
                                  ACAS-DAL-Common-data

                                  WS-Invoice-Record
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
 end program acas004.
