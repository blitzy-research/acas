       >>source free
*>********************************************
*>                                           *
*>    OTM5 Table Load via the PL OTM5        *
*>                  file                     *
*>                 for MySQL                 *
*>                                           *
*>********************************************
*>
 identification division.
 program-id.             otm5LD.
*>**
*>   author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, CPL.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2020 - 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Remarks.            PL OTM5 RDB Table load from the PL OTM5 File
*>                       using the Mysql RDBMS.
*>                       For use with ACAS v3.02 and later only.
*>**
*>   System.             4.
*>   File/Table.         15.
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     acas029   } For file and table access.
*>                       otm5MT    }
*>                       fhlogger
*>
*>**
*>   Error messages used.
*>                       SY001.
*>                       SY004.
*>                       SY006.
*>                       SY007.
*>                       SY008.
*>                       SY009.
*>                       SY019.
*>                       PL910.
*>                       PL911.
*>                       PL912.
*>                       PL913.
*>                       PL914.
*>                       PL915.
*>                       PL918.
*>                       PL919.
*>                       PL997.
*>                       PL998.
*>                       PL999.
*>**
*>   Changes.
*> 14/11/16 vbc - .05 Taken from analLD.
*> 03/01/17 vbc - .06 Clean up displays & msgs.
*> 08/01/18 vbc - .07 Taken from otm3LD.
*>                    Load programs use the system param FILE for
*>                    all RDB params. changed msgs to PL9nn from SL9nn.
*> 21/03/18 vbc - .08 Added WS-Calling-Data used in zz020 but not in Loader progs.
*> 21/05/19 vbc - .09 Support for program to be called via script & test for rdb.
*> 07/06/19 vbc - .10 Include test for 99 on write for non tested other error types.
*> 09/06/19 vbc - .11 Changed displays to go to module ACAS-Sysout as using display
*>                    create Escape sequences that looks messy and impossible to
*>                    read using 'less ' or even 'cat.
*> 02/07/23 vbc - .12 See UPDATE note in Remarks regarding acas.param.
*>                    call to new module, acas-get-params that reads file
*>                    acas.params
*>
*>                    adding WS blocks: WS-RDB-Return, WS-RDB-Vars
*>                    PD: after reading system file.
*> 09/07/23 vbc - .13 Chg SO-Print to 160 from 80 & replaced displays with SO-Print.
*>                    in test Sql-State = "2300" added  move zeros to FS-Reply WE-Error
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
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
 77  prog-name           pic x(22)    value "otm5LD (3.3.00)".
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
*>  Record definition for Cobol file here:
*>
 copy "plwsoi.cob".
 01  WS-OTM5-Record redefines OI-Header
                         pic x(118).
 *>
 copy "wsfnctn.cob".
 copy "wsnames.cob".
 copy "wscall.cob".
*>
 01  Error-Messages.
*> System Wide
     03  SY001          pic x(26) value "SY001 System 1 read err = ".
     03  SY004          pic x(59) value "SY004 Problem with opening system file. Hit return to clear".
     03  SY006          pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY019          pic x(38) value "SY019 DB is not set up in Param file :".
*> Program specific
     03  PL910          pic x(30) value "PL910 Duplicate key/s found = ".
     03  PL911          pic x(39) value "PL911 Error on otm5MT processing".
     03  PL912          pic x(36) value "PL912 Error opening OTM5 File = ".
     03  PL913          pic x(30) value "PL913 Error on reading file = ".
     03  PL914          pic x(31) value "PL914 Error on writing table = ".
     03  PL915          pic x(33) value "PL915 Error opening OTM5 Table = ".
     03  PL918          pic x(22) value "PL918 RDBMS details : ".
     03  PL919          pic x(24) value "PL919 No Data - aborting".
     03  PL997          pic x(30) value "PL997 No OTM5 file present".
     03  PL998          pic x(15) value "PL998 Rewriting".
     03  PL999          pic x(15) value "PL999 Ignoring.".
*>
 procedure division.
*>=================
*>
 aa000-main-start.
     perform  zz020-Get-Program-Args.
     move     Prog-Name to So-Print.
     perform  Call-Sysout.
     move     4      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 6=PL & SL, 5=Invoice used in FH logging
     move     15     to WS-Log-File-No.  *> Cobol/RDB, File/Table within sub System.11=Invoice
*>
*>  Get the system param for the various RDB fields
*>
     open     input System-File.
     if       fs-reply not = zero
              display Prog-Name at 0101 with erase eos
              display SY001     at 0401
              display fs-reply  at 0428
              display SY004     at 0501
              close System-File
              move 128 to return-code
              goback.
     move     1 to rrn.     *> Read the system parameter record (1)
     read     system-file record.
     if       fs-reply not = zero
              display Prog-Name at 0101 with erase eos
              display SY001           at 0401
              display fs-reply        at 0428
              display "Not set up ?"  at 0431
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
              close System-File
              move 64 to Return-Code
              goback.
*>
 aa010-Proc-Override.
*>
*>  Over-ride processes for acas029/InvoiceMT for Dup modes
*>
     move     zero to File-System-Used
                      File-Duplicates-In-Use
                      FA-File-System-Used
                      FA-File-Duplicates-In-Use.   *> Cobol file in use
     move     zero to Log-file-rec-written.        *>  for logging.
*>
     move     1 to File-Key-No.
     perform  acas029-Open-Input.      *> open input Cobol OTM5 FILE
     if       FS-Reply = 35
              move Prog-Name to SO-Print.
              perform call-Sysout
              move spaces to SO-Print
              string   PL997
                       " Terminating nothing to do"
                          into SO-Print
              perform call-Sysout
              move    "CLOSE   " to SO-Print
              perform call-Sysout
              close System-File
              perform acas029-Close
              goback.
     if       FS-Reply not = zero
              move Prog-Name to SO-Print.
              perform call-Sysout
              move spaces to SO-Print
              string  PL912
                      " FS-Reply = "
                      FS-Reply  into SO-Print
              perform call-Sysout
              move    "CLOSE   " to SO-Print
              perform call-Sysout
              close System-File
              perform acas029-Close
              move 16 to return-code
              goback.
*>
     move     1 to File-System-Used
                   FA-File-System-Used.            *> RDB in use
     perform  acas029-Open-Output.              *> Open/Init RDB via FH - Invoice
     if       FS-Reply not = zero
              move    PL915 to SO-Print
              perform call-Sysout
              move "CLOSE   " to SO-Print
              perform call-Sysout
              close System-File
              perform acas029-Close
              move zero to File-System-Used
                           File-Duplicates-In-Use
              perform acas029-Close
              goback.
     go       to aa010-Read.
*>
 acas029.
     call     "acas029" using System-Record
                              WS-OTM5-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas029-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas029.
     perform  aa100-Check-4-Errors.
*>
 acas029-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas029.
     perform  aa100-Check-4-Errors.
*>
 acas029-Open-Output.
     set      fn-open  to true.
     set      fn-output to true.
     perform  acas029.
     perform  aa100-Check-4-Errors.
*>
 acas029-Close.
     set      fn-Close to true.
     perform  acas029.
*>
 acas029-Read-Next.
     set      fn-Read-Next to true.
     perform  acas029.
*>
 acas029-Write.
     set      fn-Write to true.
     perform  acas029.
*>
 acas029-Rewrite.
     set      fn-re-write to true.
     perform  acas029.
*>
 aa010-Read.
     move     zero to File-System-Used
                      FA-File-System-Used.            *> Cobol file in use
     perform  acas029-Read-Next.
     if       fs-Reply = 10                        *> EOF
              go to aa999-Finish.
*>
     if       FS-Reply not = zero
              move spaces to SO-Print
              string  PL913
                      fs-reply  into SO-Print
              perform call-Sysout
 *>             perform aa020-Rollback
              go to aa999-Finish.
*>
     add      1 to ws-Rec-Cnt-In.
*>
     move     1 to File-System-Used     *> acas0nn set to process RDB
                   FA-File-System-Used.
     perform  acas029-Write.
     if       Sql-State = "23000"  *> Dup key (rec already present)
         or   fs-reply = 22  or = 99                    *> Check for dup key/record and continue at least while testing
         or   SQL-Err (1:4) = "1062"
                         or = "1022"
              move    zeros to FS-Reply
                               WE-Error
              perform acas029-Rewrite  *> in case it has been rerun.
              if      FS-Reply not = zero
                      move spaces to SO-Print
                      string PL914
                              WS-File-Key into SO-Print
                      perform call-Sysout
                      move    PL999 to SO-Print
                      perform call-Sysout
              else
                      add 1 to ws-Rec-Cnt-R-Out
              end-if
              go to aa010-Read
     end-if
*>
     if       FS-Reply not = zero
              move spaces to SO-Print
              string PL914 FS-Reply into SO-Print
              perform Call-Sysout
              move spaces to SO-Print
              string "WE-Error = " WE-Error into SO-Print
              perform Call-Sysout
              move spaces to SO-Print
              string PL918 SQL-Err into SO-Print
              perform Call-Sysout
              move SQL-Msg to SO-Print
              perform Call-Sysout
              move SQL-State to SO-Print
              perform Call-Sysout
 *>             perform aa020-Rollback
              move 16 to return-code                        *> rdb problem?
              go to aa999-Finish.
     add      1 to ws-Rec-Cnt-Out.
     go       to aa010-Read.
*>
 aa020-Rollback.
*>
*> These do not work during testing with mariadb - Non transactional model or autocommit set ON
*>
*>           exec sql
*>                rollback
*>           end-exec.
     call     "MySQL_rollback".
*>     if       return-code not = zero
*>              display "Rollback failed " at 0501
*>              display return-code        at 0517
*>     end-if.
*>
 aa030-Commit.
*>           exec sql
*>                commit
*>           end-exec.
     call     "MySQL_commit".
*>     if       return-code not = zero
*>              display "Commit failed " at 0501
*>              display return-code      at 0515
*>     end-if.
*>
 aa100-Check-4-Errors.
     if       fs-reply not = zero
                  move   PL911 to SO-Print
                  perform call-Sysout
                  move spaces to SO-Print
                  string "FS-Replay = " FS-Reply into SO-Print
                  perform Call-Sysout
                  move spaces to SO-Print
                  string "WE-Error = " WE-Error into SO-Print
                  perform Call-Sysout
                  move SQL-Err to SO-Print
                  perform Call-Sysout
                  move SQL-Msg to SO-Print
                  perform Call-Sysout
                  move SQL-State to SO-Print
                  perform Call-Sysout
 *>             perform aa020-Rollback
              go to aa999-Finish
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
     perform  acas029-Close.                     *> Close RDB
     close    System-File.
     move     zero to File-System-Used
                   FA-File-System-Used.
     perform  acas029-close.    *> Close cobol OTM5 file
     move     "EOJ - Load PL OTM5 Table" to So-Print.
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
