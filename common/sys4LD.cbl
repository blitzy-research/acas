       >>source free
*>********************************************
*>                                           *
*>    sys4 Table Load via the System file    *
*>                 Record 4                  *
*>                 for MySQL                 *
*>                                           *
*>-------------------------------------------*
*>  This modules uses commit and rollback so *
*>  you MUST ensure that autocommit is OFF   *
*>   in the rdb settings. It is as default   *
*>   set ON.                                 *
*>********************************************
*>
 identification division.
 program-id.             sys4LD.
*>**
*>   author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, CPL.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Remarks.            sys4 RDB Table load from the System File Record 4
*>                       using the Mysql RDBMS.
*>                       For use with ACAS v3.02 and later only.
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     acas000    } For file and table access.
*>                       sys4MT   }
*>    Note FH (acas000) NOT called.
*>**
*>   Error messages used.
*>                       SY001.
*>                       SY001C.
*>                       SY004.
*>                       SY006.
*>                       SY007.
*>                       SY008.
*>                       SY009.
*>                       SY019
*>                       SL010.
*>                       SL011.
*>                       SL014.
*>                       SL015
*>                       SL018.
*>                       SL097.   NEW
*>                       SL098.   NEW
*>                       SL099.
*>**
*>   Changes.
*> 27/08/16 vbc - .06 Source taken from dfltLD.
*> 16/09/16 vbc   .07 Changes for this module that calls sys4MT directly
*>                    having set up the DB- fields as acas000 not called.
*> 23/09/16 vbc - .08 Cosmetic : Extra Displays for force update.
*>                    Removed logging. Test for empty sys4 record and
*>                    if so, inititalise it; JIC. 2 new msgs SL098 & SL097.
*> 05/10/16 vbc - .09 Extra tests on error and remove go to code so need test
*>                    after call for rs-reply <> zero
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 03/01/17 vbc - .10 Clean up displays & msgs.
*> 21/03/18 vbc - .11 Added WS-Calling-Data used in zz020 but not in Loader progs.
*> 19/05/19 vbc - .12 Support for program to be called via script & test for rdb.
*> 07/06/19 vbc - .13 Include test for 99 on write for non tested other error types.
*> 08/06/19 vbc - .14 Changed displays to go to module ACAS-Sysout as using display
*>                    create Escape sequences that looks messy and impossible to
*>                    read using 'less ' or even 'cat.
*> 02/07/23 vbc - .15 See UPDATE note in Remarks regarding acas.param.
*>                    call to new module, acas-get-params that reads file
*>                    acas.params
*>
*>                    adding WS blocks: WS-RDB-Return, WS-RDB-Vars
*>                    PD: after reading system file.
*> 09/07/23 vbc - .16 Chg SO-Print to 160 from 80 & replaced displays with SO-Print.
*>                    in test Sql-State = "2300" added  move zeros to FS-Reply WE-Error
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 2024-04-16.
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
*>*************************************************************************
*>
*>
 environment division.
*>-------------------
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
 copy "selsys.cob".
 data division.
*>------------
*>
 file section.
*>-----------
*>
 copy "fdsys.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(16)    value "sys4LD (3.3.00)".
 77  z                   binary-char  value zero.
 77  OS-Delimiter        pic x        value "/".
 77  ACAS_BIN            pic x(512)   value spaces.
 77  ACAS_LEDGERS        pic x(500)   value spaces.
 77  Arg-Number          pic 9        value zero.
*>
*> holds program parameter values from command line
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
 01  SO-Print            pic x(160)    value spaces.
*>
*> For getting acas.param file data
*>
 01  WS-RDB-Return       pic 99       value zeros.
 01  WS-RDB-Vars                      value spaces.
     03  WS-Host-Name    pic x(64).
     03  WS-Implementation
                         pic x(64).
     03  WS-Password     pic x(64).
     03  WS-Base-Name    pic x(64).
     03  WS-Port-Number  pic x(4).
     03  WS-Socket       pic x(64).
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 copy "wssystem.cob" replacing System-Record by WS-System-Record
                               File-System-Used by WS-File-System-Used
                               File-Duplicates-In-Use by WS-File-Duplicates-In-Use
                               FS-Cobol-Files-Used by WS-FS-Cobol-Files-Used
                               FS-Duplicate-Processing by WS-FS-Duplicate-Processing
                               RDBMS-DB-Name by WS-RDBMS-DB-Name
                               RDBMS-User    by WS-RDBMS-User
                               RDBMS-Passwd  by WS-RDBMS-Passwd
                               RDBMS-Port    by WS-RDBMS-Port
                               RDBMS-Host    by WS-RDBMS-Host
                               RDBMS-Socket  by WS-RDBMS-Socket.
 copy "wssys4.cob".
 copy "wsfnctn.cob".
 copy "wsnames.cob".
 copy "wscall.cob".
*>
 01  Error-Messages.
*> System Wide
     03  SY001          pic x(26) value "SY001 System 1 read err = ".
     03  SY001D         pic x(27) value "SY001D System 4 read err = ".
     03  SY004          pic x(59) value "SY004 Problem with opening system file. Hit return to clear".
     03  SY006          pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY019          pic x(38) value "SY019 DB is not set up in Param file :".
*> Program specific
     03  SL010          pic x(30) value "SL010 Duplicate key/s found = ".
     03  SL011          pic x(37) value "SL011 Error on sys4MT processing".
     03  SL014          pic x(31) value "SL014 Error on writing table = ".
     03  SL015          pic x(34) value "SL015 Error opening Sys4 Table = ".
     03  SL018          pic x(22) value "SL018 RDBMS details : ".
     03  SL097          pic x(24) value "SL097 Record initialised".
     03  SL098          pic x(33) value "SL098 Forcing Rewrite as reqested".
     03  SL099          pic x(15) value "SL099 Ignoring.".
*>
 procedure division.
*>=================
*>
 aa000-main-start.
     perform  zz020-Get-Program-Args.
     move     Prog-Name to So-Print.
     perform  Call-Sysout.
     move     0      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock used in FH logging
     move     20     to WS-Log-File-no.  *> Cobol/RDB, File/Table within sub System. for FHlogger
*>
*>  Get the system param for the various RDB fields
*>
     open     input System-File.
     if       fs-reply not = zero
              display Prog-Name at 0101 with erase eos
              display SY001       at 0401
              display fs-reply    at 0428
              display SY004       at 0501
              close System-File
              move 128 to return-code
              goback.
     move     4 to rrn.
     read     System-File record.
     if       fs-reply not = zero
              display Prog-Name at 0101 with erase eos
              display SY001D         at 0401
              display fs-reply       at 0428
              display "Not set up ?" at 0431
              close System-File
              move 128 to return-code
              goback.
     move     System-Record to System-Record-4.
     move     1  to  rrn.
     read     System-File  record.       *> read the system parameter record (1)
     move     System-Record to WS-System-Record.
     if       fs-reply not = zero
              display SY001          at 0401
              display fs-reply       at 0428
              display "Not set up ?" at 0431
              close System-File
              move 128 to return-code
              goback.
*>
*>  Load up the DB settings from the system record as its not passed on.
*>
     if       RDBMS-DB-Name = spaces
         or   FS-Cobol-Files-Used
              display Prog-Name    *>  at 0101 with erase eos
              display SY019
              display "Cobol files in use ONLY"
              call     "acas-get-params" using WS-RDB-Return
                                               WS-RDB-Vars
              if       WS-RDB-Return = 8
                       display "acas.param file NOT found - Aborted"
                       close  System-File
                       goback
              end-if
              if       WS-RDB-Return = 1
                       display "Invalid keyword terminator found - Aborted"
                       close  System-File
                       goback
              end-if
              if       WS-RDB-Return = 2
                       display "Invalid keyword found - Aborted"
                       close  System-File
                       goback
              end-if
              if       WS-RDB-Return = zeros
                       display "acas-param file found and being used "
                       move     WS-Host-Name      to RDBMS-Host
                       move     WS-Implementation to RDBMS-User
                       move     WS-Password       to RDBMS-Passwd
                       move     WS-Base-Name      to RDBMS-DB-Name
                       move     WS-Port-Number    to RDBMS-Port
                       move     WS-Socket         to RDBMS-Socket
                      display "User = "   RDBMS-User
                      display "Host = "   RDBMS-Host
                      display "DBName = " RDBMS-DB-Name
                      display "Port = "   RDBMS-Port
                      display "Socket = " RDBMS-Socket
                       go to aa010-Proc-Override.
*>
     if       RDBMS-DB-Name = spaces
         or   FS-Cobol-Files-Used
              display Prog-Name at 0101 with erase eos
              display SY019
              if  FS-Cobol-Files-Used
                  display "Cobol files in use ONLY"
              end-if
              display "DBName = " RDBMS-DB-Name
              display "User = "   RDBMS-User
              display "Port = "   RDBMS-Port
              display "Host = "   RDBMS-Host
              display "Socket = " RDBMS-Socket
              stop "SY008 Note message & Hit return"
              close System-File
              move 64 to Return-Code
              goback.
*>
 aa010-Proc-Override.
*>
*>  Over-ride processes for acas000/sys4MT for Dup modes
*>
     move     zero to File-System-Used
                      File-Duplicates-In-Use
                      FA-File-System-Used
                      FA-File-Duplicates-In-Use.   *>  Cobol file in use
     move     zero to Log-file-rec-written.        *> for logging.
*>
     move     1 to File-Key-No.
     move     1 to File-System-Used
                   FA-File-System-Used.            *> RDB in use
     perform  acas000-Open.                        *> Open/Init RDB via FH - acas000
     if       fs-reply not = zero
              move spaces to SO-Print
              string   SL015
                          into SO-Print
              perform call-Sysout
              move    "CLOSE   " to SO-Print
              perform call-Sysout
              go to aa999-Finish.
     go       to aa010-Read.
*>
 acas000.    *> Uses sys4MT DAL and NOT the F.H.
*>     call     "acas000" using
*>                              File-Defs
     call     "sys4MT" using
                                File-Access
                                ACAS-DAL-Common-data
                                System-Record-4.
*>
 acas000-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas000.
     perform  aa100-Check-4-Errors.
*>
 acas000-Close.
     set      fn-Close to true.
     perform  acas000.
*>
 acas000-Write.
     set      fn-Write to true.
     perform  acas000.
*>
 acas000-ReWrite.
     set      fn-re-write to true.
     perform  acas000.
*>
*>  We will Rollback on any errors but Mysql has to be set up to do it
*>      otherwise as normally it is set to autocommit !!!!!
*>
*> Note that if not set up, the rollback or commit might throw up an error
*>  (but coding that reports it, has been remarked out)
*>   which can be ignored unless you thought autocommit was set up.
*>
 aa010-Read.
     add      1 to ws-Rec-Cnt-In.
*>
     move     1 to File-System-Used     *> acas0nn set to process RDB
                   FA-File-System-Used.
*>
*> See if we have an empty record, lets make sure it is initialised
*>
     if       zero = sl-os-bal-last-month
          and        sl-os-bal-this-month
          and        sl-invoices-this-month
          and        sl-credit-notes-this-month
          and        sl-variance
          and        sl-credit-deductions
          and        sl-cn-unappl-this-month
          and        sl-payments
          and        pl-os-bal-last-month
          and        pl-os-bal-this-month
          and        pl-invoices-this-month
          and        pl-credit-notes-this-month
          and        pl-variance
          and        pl-credit-deductions
          and        pl-cn-unappl-this-month
          and        pl-payments
              initialise System-Record-4 with filler
              move   1 to sl4-spare1
                          sl4-spare2
                          sl4-spare3
                          sl4-spare4
     end-if                                    *> Should not be needed but ..
     perform  acas000-Write.
     if       Sql-State = "23000"  *> Dup key (rec already present)
         or   fs-reply = 22  or = 99                    *> Check for dup key/record
         or   SQL-Err (1:4) = "1062"
                         or = "1022"
              move    zeros to FS-Reply
                               WE-Error
              perform acas000-ReWrite
              if    FS-Reply not = zero
                    move spaces to SO-Print
                    string SL014
                           WS-File-Key into SO-Print
                    perform call-Sysout
              else
                    add 1 to ws-Rec-Cnt-R-Out
              end-if
              go to aa999-Finish
     end-if
*>
     if       fs-reply not = zero              *> Anything else
          or  WE-Error not = zero              *>   28/09/16
              move spaces to SO-Print
              string SL014 FS-Reply into SO-Print
              perform Call-Sysout
              move spaces to SO-Print
              string "WE-Error = " WE-Error into SO-Print
              perform Call-Sysout
              move spaces to SO-Print
              string SL018 SQL-Err into SO-Print
              perform Call-Sysout
              move SQL-Msg to SO-Print
              perform Call-Sysout
              move SQL-State to SO-Print
              perform Call-Sysout
 *>             perform aa020-Rollback
              go to aa999-Finish
     end-if
     add      1 to ws-Rec-Cnt-Out.
     go       to aa999-Finish.    *> only have one record.
*>
 aa020-Rollback.
*>
*> These do not work during testing with mariadb - Non transactional model
*>    or autocommit set ON
*>
*>           exec sql
*>                rollback
*>           end-exec.
     call     "MySQL_rollback".
*>     if       return-code not = zero
*>              display "Rollback failed " at 2301
*>              display return-code      at 2317
*>     end-if.
*>
 aa030-Commit.
*>           exec sql
*>                commit
*>           end-exec.
     call     "MySQL_commit".
*>     if       return-code not = zero
*>              display "Commit failed " at 2301
*>              display return-code      at 2315
*>     end-if.
*>
 aa100-Check-4-Errors.
     if       fs-reply not = zero
              move SL011 to SO-Print
              perform Call-Sysout
              move spaces to SO-Print
              string "FS-Reply = " FS-Reply into SO-Print
              perform call-Sysout
              move SQL-Err to SO-Print
              perform Call-Sysout
              move SQL-Msg to SO-Print
              perform Call-Sysout
              move SQL-State to SO-Print
              perform Call-Sysout
 *>             perform aa020-Rollback
     end-if.
*>
 aa999-Finish.
     move     spaces to SO-Print.
     string   "Rec cnt  in = " ws-Rec-Cnt-In
              " Rec cnt out = " ws-Rec-Cnt-Out
              " Rec Cnt rewrite = " ws-Rec-Cnt-R-Out into SO-Print.
     perform  Call-Sysout.
     move     spaces to SO-Print.
     string   "Log Recs out   = " Log-File-Rec-Written into SO-Print.
     perform  Call-Sysout.
     move     spaces to SO-Print.
     move     1 to File-System-Used
                   FA-File-System-Used.
     move     zero to Access-Type.
     move     2 to File-Function.
     if WE-Error not = 911
        perform  acas000-Close.                     *> Close RDB
*>
     close    System-File.
     move     zero to  File-Function
                       Access-Type.              *> close log file
 *>    call     "fhlogger" using File-Access
 *>                              ACAS-DAL-Common-data.
     move     "EOJ - Load Sys4 Table" to So-Print.   *> at 2001 with erase eol.
     perform  Call-Sysout.
     move     "CLOSE   " to SO-Print.
     perform  Call-Sysout.
     goback.
*>
 copy "Proc-Get-Env-Set-Files.cob".  *> Only uses ACAS_LEDGERS now
*>
 Call-Sysout.
     call     "ACAS-Sysout" using SO-Print.
*>
