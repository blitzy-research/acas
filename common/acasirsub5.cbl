       >>source free
*>***********************************************
*>                                              *
*>                   IRS  Final                 *
*>               File/Table Handler             *
*>                                              *
*>  The Program name is taken from the FILE-nn  *
*>       used in the cobol file select.         *
*>***********************************************
*>
 identification division.
 Program-Id.            acasirsub5.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             IRS Final File Handler.
*>                      **********************
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>**
*> Called Modules:
*>                      irsfinalMT -
*>                                DAL (RDB Data Access Layer) or a variation
*>                      Selected via CDF etc [to be added].
*>
*>**
*> Error Messages Used.
*>
*>                      IR901 Note error and hit return
*>                      IR902 Program Error: Temp rec =yyy < Final-Rec = zzz
*>                      IR921 Failure to read Final File rec. !
*>                      IR922 Failure to read Final File
*>                      IR923 Failure to open o/p Final File
*>                      IR924 Failure to write Final File
*>**
*> Version.             1.00 29/02/2012. Rewritten June 2016 after creating the DAL.
*>**
*> Changes.
*> 16/11/16 vbc - .05 Taken from acasirsub5 replacing irsub5.
*> 17/11/16 vbc -     Recoded to match irsub5.
*> 28/01/18 vbc - .06 Updated copy for using copybooks dir.
*> 14/02/18 vbc - .07 Mapped error msgs to module specifics IR90n.
*> 28/02/18 vbc - .08 Added recs test for FH at ba012-Test-WS-Rec-Size-2
*> 29/04/18 vbc - .09 Remarked out Open and Close processes as it only does
*>                    Read Next and Write which both open, read/write, close in
*>                    one operation. Removed tests for File-Key-No.
*> 07/12/22 vbc - .10 Chgd Vars A & B to pic 999 toi keep GC v3.2 happy.
*> 31/05/23 vbc - .11 chg WS-Log-File-No to 14.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
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
     select Final-File       assign file-37
                             organization line sequential,
                             access sequential,
                             status fs-reply.
*>
 data division.
 file section.
*>***********
 fd  Final-File.
*>
 01  Record-5            pic x(655).
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(20)  value "acasirsub5 (3.3.00)".
*>
 77  WS-Reply           pic x      value space.
 77  WS-Save-FS-Reply   pic 99     value zero.             *> These 2 for acasirsub3 & 5
 77  WS-Save-WE-Error   pic 999    value zero.
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
     03  IR921          pic x(39) value "IR921 Failure to read Final File rec. !".
     03  IR922          pic x(32) value "IR922 Failure to read Final File".
     03  IR923          pic x(36) value "IR923 Failure to open o/p Final File".
     03  IR924          pic x(33) value "IR924 Failure to write Final File".
*>
 Linkage Section.
*>**************
 copy "irswsfinal.cob".
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

                          Final-Record

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
     move     14     to WS-Log-File-No.  *> Cobol/RDB, File/Table within sub System.
*>
*> WARNING The modules acasirsub5 for Final as well as acasirsub3
*> for defaults has to be modified as IRS only does a read or write
*>   and not a direct open or close so
*>   it has to be done here when processing RDB.
*>
*>   For Cobol files these have been changed to do the same so direct
*>    calls to open and close are not needed or wanted.
*>     so return with fs-reply & we-error = zero.
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
*> So we are processing Cobol Flat files by themselves. *
*>******************************************************************************
*>
     move     zero   to  WE-Error             *> as in irsub5
     move     spaces to SQL-Err SQL-Msg SQL-State.
*>
     evaluate File-Function
        when  1                              *> JIC but not used for irsub3 & 5
*>              go to aa020-Process-Open
              move zero to FS-Reply WE-Error
              go to aa-Exit
        when  2                              *> JIC but not used for irsub3 & 5
*>              go to aa030-Process-Close
              move zero to FS-Reply WE-Error
              go to aa-Exit
        when  3
              go to aa040-Process-Read-Next
        when  5
        when  7                              *> write/rewrite can do the same
              go to aa070-Process-Write      *> as file is opened as output.
        when  other                          *> others are unused
              go to aa100-Bad-Function
     end-evaluate.
*>
*>  Should never get here but Just in case :(
     go       to aa100-Bad-Function.
*>
*> aa020-Process-Open.
*>     move     spaces to WS-File-Key.     *> for logging
*>     move     201 to WS-No-Paragraph.
*>     if       fn-input
*>              open input Final-File
*>              if   Fs-Reply not = zero  *> next 2 from irsub5
*>                   move 35 to fs-Reply
*>                   move  1 to we-error     *> NOT as in irsub5
*>                   go to aa999-Main-Exit
*>              end-if
*>      else
*>       if     fn-i-o or fn-Extend
*>              move 997 to WE-Error
*>              move 99  to FS-Reply
*>              go to aa999-main-exit
*>       else
*>        if    fn-output
*>              open output Final-File         *> caller should check fs-reply
*>        end-if
*>       end-if
*>     end-if.
*>     move     zero to Cobol-File-Status.
*>     if       fs-reply not = zero
*>              move 1 to we-error.
*>     go       to aa999-main-exit.            *> with test for dup processing
*>
*> aa030-Process-Close.
*>     move     202 to WS-No-Paragraph.
*>     move     spaces to WS-File-Key.     *> for logging
*>     close    Final-File.
*>*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
*>     move     zero to Cobol-File-Status.
*>     move     zero to  File-Function
*>                       Access-Type.              *> close log file
*>     go       to aa999-main-exit.
*>
 aa040-Process-Read-Next.
*>
*>   Process READ next record Really its just a Read (one record)
*>      NOTE change caller code to open first
*>
     move     203 to WS-No-Paragraph.
     open     input Final-File.
     if       Fs-Reply not = zero     *> NOT from irsub5
              close Final-File
              open output Final-File
              initialize Final-Record
              move    Final-Record to Record-5
              write   Record-5
              close   Final-File
              go to aa999-Main-Exit
     end-if
     initialize Final-Record.
     if       Cobol-File-Eof          *> This block should NOT occur
              move 10 to FS-Reply
                         WE-Error
              move 3 to WE-Error                 *> NOT as in irsub5
              move spaces to
                             SQL-Err
                             SQL-Msg
              stop "Cobol File EOF"               *> for testing because it should not have got here !!
              close Final-File
              go to aa999-main-exit
     end-if.
     read     Final-File next record at end
              display IR921 at 2301 with foreground-color 4
              move 10 to WE-Error FS-Reply        *> EOF
              move 3 to WE-Error                 *> as in irsub5
              set Cobol-File-EoF to true
              move 1 to Cobol-File-Status         *> JIC above dont work :)
              move "EOF" to WS-File-Key           *> for logging
              close Final-File
              go to aa999-main-exit
     end-read.
*>
     if       FS-Reply not = zero
              display IR922 at 2301 with foreground-color 4  *> red
               move 1 to we-error
              close Final-File
              go to aa999-main-exit
     end-if
     move     Record-5 to  Final-Record.
*>
     move     1   to WS-File-Key.
     move     zeros to WE-Error.
     move     "Open Final, Read, Close on 1" to WS-File-Key.
     close    Final-File.
     go to    aa999-main-exit.
*>
 aa070-Process-Write.
 *>
 *>  code changed to same as irsub5
 *>
     move     206 to WS-No-Paragraph.
 *>    move     Final-Record to Record-5.
     move     zeros to FS-Reply  WE-Error.
*>
*>  FROM irsub5 but will make open & close calls from caller if needed.
*>
     open     output Final-File.
     if       fs-reply not = zero
                 display IR923 at 2301 with foreground-color 4  *> red
                 move 1 to we-error
                 close Final-File
                 go to aa999-main-exit
     end-if
     write    Record-5 from Final-Record.
     if       FS-Reply not = zero
              display IR924 at 2301 with foreground-color 4  *> red
              move 1 to we-error
     end-if.
     close    Final-File.      *> same as irsub5
     move     "Open Final, Write, Close on 1" to WS-File-Key.
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
*> Check for RDB processing ??
*>
 *>    if       FS-Duplicate-Processing
 *>             go to ba-Process-rdbms
 *>    end-if.
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
     move     24 to WS-Log-File-no.        *> for FHlogger
*>
 ba012-Test-WS-Rec-Size-2.
*>
     if       A = zero                        *> so it is being called first time
              move     function Length (
                                         Final-Record
                                                 ) to A
              move     function length (
                                        Record-5
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
                              "IRS-Final-Rec = " delimited by size
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
*>
*>   HERE we need a CDF [Compiler Directive] to select the correct DAL based
*>     on the pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<<  ? >>>>>
*>        Do this after system testing and pre code release.
*>
*>  NOW SET UP FOR JC pre-sql compiler system.
*>   DAL-Datablock not needed unless using RDBMS DAL from Prima & MS Sql
*>
*>  Here we do non standard DAL things to handle open & close pre / post
*>   to calls for Read and write.
*>
     if       fn-open                                  *> Open ignore
              move    zero to FS-Reply WE-Error
              go      to ba-RDBMS-Exit
     end-if
     if       fn-close                                 *> Close ignore & close logger
              move    zero to File-Function
                              Access-Type
              perform Ca-Process-Logs
              go      to ba-RDBMS-Exit
     end-if
*>
     if       fn-read-next
              set     fn-Open  to true
              set     fn-Input to true
              perform ba020-Call-DAL                   *> open
              perform Ca-Process-Logs
              if      Fs-Reply not = zero
                   or WE-Error not = zero
                      go to ba-rdbms-Exit
              end-if
              set     fn-Read-Next to true
              perform ba020-Call-DAL                   *> Read
              move    FS-Reply to WS-Save-FS-Reply     *> save the statuses
              move    WE-Error to WS-Save-WE-Error
              perform Ca-Process-Logs                  *> temp only during testing
              if      FS-Reply not = zero
                  or  WE-Error not = zero
                      go      to ba-RDBMS-Exit
              end-if
              set     fn-Close to true
              perform ba020-Call-DAL
              perform Ca-Process-Logs                  *> temp only during testing
              move    WS-Save-FS-Reply to FS-Reply     *> restore them
              move    WS-Save-WE-Error to WE-Error
              move    "Open, Read, Close" to WS-File-key
              perform Ca-Process-Logs                  *> temp only during testing
              go      to ba-RDBMS-Exit
     end-if.
     if       fn-Write
              set     fn-Open  to true
              set     fn-I-O to true
              perform ba020-Call-DAL                   *> Open
              if      Fs-Reply not = zero
                   or WE-Error not = zero
                      go to ba-rdbms-Exit
              end-if
              set     fn-Write to true
              perform ba020-Call-DAL                   *> write
              move    FS-Reply to WS-Save-FS-Reply     *> save the statuses
              move    WE-Error to WS-Save-WE-Error
              set     fn-Close to true
              perform ba020-Call-DAL
              move    WS-Save-FS-Reply to FS-Reply     *> restore them
              move    WS-Save-WE-Error to WE-Error
              if      (fs-Reply not = zero or
                      WE-Error not = zero)
                      move    "Open, Write failed, Close" to WS-File-Key
                      perform Ca-Process-Logs            *> temp only during testing
                      set     fn-Re-write to true
                      move zero to fs-reply we-error   *> clear if used in write
              else
                      go      to ba-RDBMS-Exit
     end-if.
*>
     if       fn-Re-write
              set     fn-Open  to true
              set     fn-I-O to true
              perform ba020-Call-DAL                   *> Open
              if      Fs-Reply not = zero
                   or WE-Error not = zero
                      go to ba-rdbms-Exit
              end-if
              set     fn-Re-write to true
              perform ba020-Call-DAL                   *> write
              move    FS-Reply to WS-Save-FS-Reply     *> save the statuses
              move    WE-Error to WS-Save-WE-Error
              set     fn-Close to true
              perform ba020-Call-DAL
              move    WS-Save-FS-Reply to FS-Reply     *> restore them
              move    WS-Save-WE-Error to WE-Error
              move    "Open, Rewrite, Close" to WS-File-key
              perform Ca-Process-Logs                  *> temp only during testing
              go      to ba-RDBMS-Exit
     end-if.
*>
*> In case of bad call action that was missed.
*>
     move     999 to WE-Error.
     move     99  to FS-Reply.
     go       to ba-RDBMS-Exit.
*>
 ba020-Call-DAL.
     call     "irsfinalMT" using File-Access
                                ACAS-DAL-Common-data

                                Final-Record
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
 end program acasirsub5.
