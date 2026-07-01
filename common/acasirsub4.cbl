       >>source free
*>***********************************************
*>                                              *
*>                 IRS   Posting                *
*>               File/Table Handler             *
*>                                              *
*>  The Program name is taken from the FILE-nn  *
*>       used in the cobol file select.         *
*>***********************************************
*>
 identification division.
 Program-Id.            acasirsub4.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             IRS Posting File Handler.
*>                      **************
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>**
*> Called Modules:
*>                      postingMT -
*>                                DAL (RDB Data Access Layer) or a variation
*>                      Selected via CDF etc [to be added].
*>**
*> Error Messages Used.
*>
*>                      IR901 Note error and hit return
*>                      IR902 Program Error: Temp rec =yyy < Posting-Rec = zzz
*>**
*> Version.             1.00 29/02/2012. Rewritten June 2016 after creating the DAL.
*>
*>**
*> Changes.
*> 15/11/16 vbc - .04 Taken from acasirsub1 & irsub4.
*> 24/11/16 vbc - .05 Extra function (6) for Delete-ALL records which
*>                    is the same as open output with a Cobol file.
*> 28/01/18 vbc - .06 Updated copy for using copybooks dir.
*> 25/02/18 vbc - .07 IR902 changed to correct file.
*> 28/02/18 vbc - .08 Added recs test for FH at ba012-Test-WS-Rec-Size-2
*> 29/04/18 vbc - .09 Resetting Cobol-File-Status for write,rewrite,delete, start.
*> 07/12/22 vbc - .10 Chgd Vars A & B to pic 999 toi keep GC v3.2 happy.
*> 10/12/22 vbc - .11 chg to perform ba-Process-RDBMS 2 remove GC warning msg from latest v3.2 code
*>                    WITH ba-Main-Exit chgd to exit section.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
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
     select  Posting-File    assign   File-36      *>  "post.dat"
                             organization indexed
                             access   dynamic
                             record   key-4
                             status   fs-reply.
*>
 data division.
 file section.
*>***********
*>
 fd  Posting-File.
*>
 01  Record-4.
     03  Key-4.
         05  Key-Number   pic 9(5).
     03  Post4-Code       pic xx.
     03  Post4-Date       pic x(8).
     03  Post4-DR         pic 9(5).
     03  Post4-CR         pic 9(5).
     03  Post4-Amount     pic s9(7)v99   sign is leading.
     03  Post4-Legend     pic x(32).
     03  Vat-AC-Def4      pic 99.
     03  Post4-Vat-Side   pic xx.
     03  Vat-Amount4      pic s9(7)v99   sign is leading.
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(20)  value "acasirsub4 (3.3.00)".
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
     03  IR901          pic x(31) value "IR901 Note error and hit return".
     03  IR902          pic x(32) value "IR902 Program Error: Temp rec = ".
*>
 Linkage Section.
*>**************
 copy "irswspost.cob".
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

                          Posting-Record

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
     move     13     to WS-Log-File-No.  *> Cobol/RDB, File/Table within sub System.
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
     move     zero   to  WE-Error                                   *> as in irsub4
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
     move     "OPEN IRS Postings File" to WS-File-Key.
     if       fn-input
              open input Posting-File
              if   Fs-Reply not = zero
                   move  1 to we-error
                   go to aa999-Main-Exit
              end-if
              move     "OPEN Input IRS Posting File" to WS-File-Key
      else
       if     fn-i-o
              open i-o Posting-File
              if       fs-reply not = zero
                       close       Posting-File
                       open output Posting-File           *> Doesnt create in i-o
                       close       Posting-File
                       open i-o    Posting-File
              end-if
              move     "OPEN I/O IRS Posting File" to WS-File-Key
       else
        if    fn-output
              open output Posting-File       *> caller should check fs-reply
              move     "OPEN Output IRS Posting File" to WS-File-Key
        else
         if   fn-extend                      *> Must not be used for ISAM files
*>              open extend Posting-File
              move 997 to WE-Error
              move 99  to FS-Reply
              go to aa999-main-exit
         end-if
        end-if
       end-if
     end-if.
     move     zero to Cobol-File-Status.
     if       fs-reply not = zero
              move 1 to we-error.
     go       to aa999-main-exit.        *> with test for dup processing
*>
 aa030-Process-Close.
     move     202 to WS-No-Paragraph.
     move     spaces to WS-File-Key.     *> for logging
     move     "Close IRS Postings File" to WS-File-Key.
     close    Posting-File.
*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
     move     zero to Cobol-File-Status.
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
              move 3 to WE-Error                 *> as in irsub4
              move spaces to
                             SQL-Err
                             SQL-Msg
              stop "Cobol File EOF"               *> for testing because it should not have got here !!
              go to aa999-main-exit
     end-if.
*>
 aa041-Reread.
     read     Posting-File next record at end
              move 10 to WE-Error FS-Reply        *> EOF
              move 3 to WE-Error                 *> as in irsub4
              set Cobol-File-EoF to true
              move 1 to Cobol-File-Status         *> JIC above dont work :)
              initialize Posting-Record
              move "EOF" to WS-File-Key           *> for logging
              go to aa999-main-exit
     end-read.
     move     Record-4 to  Posting-Record.
*>
     move     Post-Key   to WS-File-Key.
     move     zeros to WE-Error.
     go to    aa999-main-exit.
*>
 aa050-Process-Read-Indexed.
*>
*>   Coding from original irsub4
*>
*> copy the key to main file area
*> if retrieve record by key set up for Owning or Sub-Nominal
*>    pointer record
*>
     move     204 to WS-No-Paragraph.
*>
 aa051-Reread.
     move     Post-Key to Key-Number.         *> in case of goto Reread
     read     Posting-File    invalid key
              move 21 to we-error fs-reply
              move  2 to we-error      *> from irsub4
              go to aa999-main-exit
     end-read
     move     Record-4  to  Posting-Record.
     move     Post-Key to WS-File-Key.
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
     move     Post-Key to WS-File-Key
                        Key-Number.
*>
     if       access-type < 5 or > 8                   *> NOT using 'not >'
              move 998 to WE-Error                     *> 998 Invalid calling parameter settings
              go to aa999-main-exit
     end-if
*>
*>  Now do Start primary key before read-next
*>
     if       fn-equal-to
              start Posting-File key = Key-Number invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub4
                    go to aa999-main-exit
              end-start
     end-if
     if       fn-not-less-than
              start Posting-File key not < Key-Number invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub4
                    go to aa999-main-exit
              end-start
     end-if
     if       fn-greater-than
              start Posting-File key > Key-Number invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub4
                    go to aa999-main-exit
              end-start
     end-if
*>
     if       fn-less-than         *> Not used in irsub4
              start Posting-File key < Key-Number invalid key
                    move 21 to Fs-Reply
                    move 2 to we-error     *> from irsub4
                    go to aa999-main-exit
              end-start
     end-if
*>
*> Now go back and read next record [ from irsub4 ]
*>
     perform  aa999-main-exit.   *> logging
     go       to aa041-Reread.
*>
 aa070-Process-Write.
     move     206 to WS-No-Paragraph.
     move     Posting-Record to Record-4.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     move     Post-Key to WS-File-Key.
     write    Record-4 invalid key
              add 1 to Post-Key
              go to aa070-Process-Write.
     move     Post-Key to WS-File-Key.
     go       to aa999-main-exit.
*>
 aa080-Process-Delete.
     move     207 to WS-No-Paragraph.
     move     Post-Key to Key-Number.
     move     Post-Key to WS-File-Key.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
*>
*> Delete record and pointer if neccessary
*>
     delete   Posting-File record.
     go       to aa999-main-exit.
*>
 aa090-Process-Rewrite.
*>
     move     208 to WS-No-Paragraph.
     move     Posting-Record to Record-4.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     move     Post-Key to WS-File-Key.
     rewrite  Record-4.
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
     move     23 to WS-Log-File-no.        *> for FHlogger
*>
 ba012-Test-WS-Rec-Size-2.
*>
     if       A = zero                        *> so it is being called first time
              move     function Length (
                                         Posting-Record
                                                 ) to A
              move     function length (
                                        Record-4
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
                              "IRS-Posting-Rec = " delimited by size
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
*>  NOW SET UP FOR JC pre-sql compiler system.
*>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
*>
 ba020-Process-DAL.
     call     "irspostingMT" using File-Access
                                   ACAS-DAL-Common-data

                                   Posting-Record
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
 end program acasirsub4.
