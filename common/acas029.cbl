       >>source free
*>***********************************************
*>                                              *
*>               OTM5 (Open Item 5)             *
*>               File/Table Handler             *
*>                                              *
*>  The Program name is taken from the FILE-nn  *
*>       used in the cobol file select.         *
*>***********************************************
*>
 identification division.
 Program-Id.            acas029.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 - 2026 and later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Sales Invoice File Handler.
*>                      **************************
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>                      --------------------------------------------------- ^^^^^ ---------
*>
*>   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING   WARNING
*>
*>        This module came from acas019 Invoice).
*>
*>        Therefore they are the models for all other FH and DALs.
*>          This means that any bugs found in one of them that is NOT file specific code changes
*>            have to be added to all existing other FH and or DAL modules.
*>               This must be done immediately after all changes to any one so that no mods are
*>                    forgotten about.
*>
*>   **************************************** END OF WARNING ********************************
*>**
*> Called Modules:
*>                      otm5MT -
*>                                DAL (RDB Data Access Layer) or a variation
*>                      Selected via CDF etc [to be added].
*>
*>**
*> Error Messages Used.
*>
*>                      PL901 Note error and hit return
*>                      PL908 Program Error: Temp rec =yyy <Open-Item-Record-5 = zzz
*>**
*> Version.             1.00 29/02/2012. Rewritten June 2016 after creating the DAL.
*>
*>                      This module is the first of the ACAS File Handlers and
*>                      will act as the model for all the others which in turn
*>                      is lightly modelled on the irsub modules for IRS.
*>
*>
*> Changes.
*> 29/02/12 vbc - Created for Gnu Cobol v1.1 & v2.0. Code also to be tested with MF VC
*>                ** UNDER TEST ** but there again every thing is!
*> 17/05/16 vbc - Adding code for log file.
*>                Notes about error messages.
*> 24/06/16 vbc - Minor coding errors with a evaluate.
*> 02/07/16 vbc - .01 Missing DB params in system rec not moved to DB-xx in wsfnctn.
*> 04/08/16 vbc       Moved logging code into a new module to be called
*>                    from here and the InvoiceMT code.
*> 04/08/16 vbc - .02 Test on read for read next at end bypass moves etc.
*> 21/07/16 vbc - .03 Minor tidy up  of code & comments near the call to the DAL.
*>                    Extra module comments and notes.
*> 27/07/16 vbc - .04 Rem'd out some mv zero to fs-reply but don't think it is causing issues, may be
*> 24/10/16 vbc - .   ALL ACAS modules now using wsnames.cob in copybooks.
*> 25/01/17 vbc -     Taken from acas011 (stock).
*>                    copies of the FD, SELECT and ws copy code copied from the
*>                    Sales ledger source directly prefixed with 'sl'.
*> 07/01/18 vbc -     Taken from acas019 DAL & DAL named as otm5MT.
*> 28/02/18 vbc - .06 Added recs test for FH at ba012-Test-WS-Rec-Size-2.
*> 29/04/18 vbc - .07 Resetting Cobol-File-Status for write,rewrite,delete, start etc
*> 07/12/22 vbc - .08 Chgd Vars A & B to pic 999 toi keep GC v3.2 happy.
*> 10/12/22 vbc - .09 chg to perform ba-Process-RDBMS + goto exit, 2 remove GC warning msg
*>                    from latest v3.2 code WITH ba-Main-Exit chgd to exit section.
*> 17/02/23 vbc - .10 Missing period for move  999 to WE-Error in Open,
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              1. File and table WS record : -
*>    acas029 ONLY             WS-OTM5-Record = Contents of data record to be written/read
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
 copy "plseloi5.cob".

*>
 data division.
 file section.
*>***********
 copy "plfdoi5.cob".
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(17)  value "acas029 (3.3.00)".
*>
 77  ws-reply           pic x      value space.
*>
 77  A                  pic 9(4)             value zero.  *> A & B used in 1st test ONLY
 77  B                  pic 9(4)             value zero.  *>  in ba-Process-RDBMS
 77  Display-Blk        pic x(75)             value spaces.
 77  Cobol-File-Status  pic 9                 value zero.
     88  Cobol-File-Eof                       value 1.
 *>
 *> TESING data
 *>
 01  WS-Temp-ED.
     03  ws-temp-ed-1       pic x(7).    *> Cust #
     03  WS-Temp-ed-2       pic 9(8).    *> Inv  #
*>
 01  Error-Messages.
*> System Wide
*> Module Specific
     03  PL901          pic x(31) value "PL901 Note error and hit return".
     03  PL908          pic x(32) value "PL908 Program Error: Temp rec = ".
*>                                        yyy <Open-Item-Record-5 = zzz
*>
 Linkage Section.
*>**************
 copy "plwsoi.cob" replacing OI-Header by WS-OTM5-Record.
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

                          WS-OTM5-Record

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
     move     4      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Invoice used in FH logging
     move     15     to WS-Log-File-No.  *> RDB, File/Table
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
*>*****************************************
*> So we are processing Cobol Flat files. *
*>*****************************************
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
              open input Open-Item-File-5
              if   Fs-Reply not = zero
                   move 35 to fs-Reply
                   close Open-Item-File-5
                   go to aa999-Main-Exit
              end-if
      else
       if     fn-i-o
              open i-o Open-Item-File-5
              if       fs-reply not = zero
                       close       Open-Item-File-5
                       open output Open-Item-File-5           *> Doesnt create in i-o
                       close       Open-Item-File-5
                       open i-o    Open-Item-File-5
              end-if                                      *> file-status will NOT be updated   ????
       else
        if    fn-output                      *> should not need to be used
              open output Open-Item-File-5   *> caller should check fs-reply
        else
         if   fn-extend                      *> Must not be used for ISAM files
*>              open extend Open-Item-File-5
              move 997 to WE-Error
              move 99  to FS-Reply
              go to aa999-main-exit
         end-if
        end-if
       end-if
     end-if.
*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
     move     zero to Cobol-File-Status.
     move     "OPEN SL OTM5 File" to WS-File-Key.
     if       fs-reply not = zero
              move  999 to WE-Error.
     go       to aa999-main-exit.            *> with test for dup processing
*>
 aa030-Process-Close.
     move     202 to WS-No-Paragraph.
     move     spaces to WS-File-Key.     *> for logging
     close    Open-Item-File-5.
*> 27/07/16 16:30     move     zeros to FS-Reply WE-Error.
     move     zero to Cobol-File-Status.
     move     "CLOSE SL OTM5 File" to WS-File-Key
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
              move spaces to OI5-Key
                             SQL-Err
                             SQL-Msg
              stop "Cobol File EOF"               *> for testing
              go to aa999-main-exit
     end-if
*>
     read     Open-Item-File-5 next record at end
              move 10 to we-error fs-reply        *> EOF
              set Cobol-File-EoF to true
              move 1 to Cobol-File-Status         *> JIC above dont work :)
              initialize Open-Item-Record-5
              move "EOF" to WS-File-Key           *> for logging
              go to aa999-main-exit
     end-read.
     if       FS-Reply not = zero
              go to aa999-main-exit.
     move     Open-Item-Record-5 to WS-OTM5-Record.
     perform  aa041-Move-Inv-Data.
     move     zeros to WE-Error.
     go to    aa999-main-exit.
*>
 aa041-Move-Inv-Data.
     move     OI5-Invoice  to WS-Temp-ED-2.
     move     OI5-Supplier to WS-Temp-ED-1.
     move     WS-Temp-ED   to WS-File-Key.
*>
*>   The next block will never get executed unless performed  so is it needed ?
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
                                     move   OI-Key     to OI5-Key
                                     perform aa041-Move-Inv-Data
                              when   other
                                     move   spaces     to WS-File-Key
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
              read     Open-Item-File-5 key OI5-Key       invalid key
                       move 21 to we-error fs-reply
              end-read
              if       fs-Reply = zero
                       move     Open-Item-Record-5 to WS-OTM5-Record
                       perform  aa041-Move-Inv-Data
              else
                       initialize WS-OTM5-Record
                       move "Failed action" to WS-File-Key
              end-if
              go       to aa999-main-exit
     end-if.
     move     998 to WE-Error       *> file seeks key type out of range but
     move     99 to fs-reply        *>        should never get here       998
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
     move     OI-Key to OI5-Key.      *> copy WS to file
     if       File-Key-No = 1
        and   fn-equal-to
              start Open-Item-File-5 key = OI5-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
        and   fn-less-than
              start Open-Item-File-5 key < OI5-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
        and   fn-greater-than
              start Open-Item-File-5 key > OI5-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
        and   fn-not-less-than
              start Open-Item-File-5 key not < OI5-Key invalid key
                    move 21 to Fs-Reply
                    go to aa999-main-exit
              end-start
     end-if
     if       File-Key-No = 1
              perform  aa041-Move-Inv-Data
     else                                    *> changed for acas029 others ?
              move     998 to WE-Error       *> file seeks key type out of range but
              move     99 to fs-reply.        *>        should never get here       998
     go       to aa999-main-exit.
*>
 aa070-Process-Write.
     move     206 to WS-No-Paragraph.
     move     WS-OTM5-Record to Open-Item-Record-5.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     write    Open-Item-Record-5 invalid key
              move 22 to FS-Reply
     end-write.
     perform  aa041-Move-Inv-Data.
     go       to aa999-main-exit.
*>
 aa080-Process-Delete.
     move     207 to WS-No-Paragraph.
     move     WS-OTM5-Record to Open-Item-Record-5.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     delete   Open-Item-File-5 record invalid key
              move 21 to FS-Reply
     end-delete.
     perform  aa041-Move-Inv-Data.
     go       to aa999-main-exit.
*>
 aa090-Process-Rewrite.
*>
     move     208 to WS-No-Paragraph.
     move     WS-OTM5-Record to Open-Item-Record-5.
     move     zeros to FS-Reply  WE-Error.
     move     zero to Cobol-File-Status.
     rewrite  Open-Item-Record-5 invalid key
              move 21 to FS-Reply
     end-rewrite
     perform  aa041-Move-Inv-Data.
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
     move     25 to WS-Log-File-no.        *> for FHlogger
*>
 ba012-Test-WS-Rec-Size-2.
*>
     if       A = zero                        *> so it is being called first time
              move     function Length (
                                        WS-OTM5-Record
                                                 ) to A
              move     function length (
                                        Open-Item-Record-5
                                                 ) to B
              if   A < B                      *> COULD LET caller module deal with these errors !!!!!!!
                   move 901 to WE-Error       *> 901 Programming error; temp rec length is wrong caller must stop
                   move 99 to fs-reply        *> allow for last field ( FILLER) not being present in layout.
              end-if
              if       WE-Error = 901                  *> record length wrong so display error, accept and then stop run.
                       move spaces to Display-Blk
                       string PL908          delimited by size
                              A              delimited by size
                              " < "          delimited by size
                              "OTM5-Record = " delimited by size
                              B              delimited by size    into Display-Blk
                       end-string
                       display Display-Blk at 2301 with erase eol     *> BUT WILL REMIND ME TO SET IT UP correctly
                       display PL901 at 2401 with erase eol
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
     call     "otm5MT" using  File-Access
                                  ACAS-DAL-Common-data

                                  WS-OTM5-Record
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
 end program acas029.
