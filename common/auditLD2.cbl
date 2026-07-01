       >>source free
*>********************************************
*>                                           *
*>    Stock Table Load via the Stock file    *
*>                 for MySQL                 *
*>     Used as Modal for the others.         *
*>                                           *
*>-------------------------------------------*
*>  This modules uses commit and rollback so *
*>  you MUST ensure that autocommit is OFF   *
*>   in the rdb settings. It is as default   *
*>   set ON.                                 *
*>********************************************

*>
*>   Special uses read COBOL open, read, close for audit
*>
*>
 identification division.
 program-id.             auditLD.
*>**
*>   author.             V.B.Coen FBCS.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2016 - 2026, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Remarks.            Stock RDB Table load from the Stock File
*>                       using the Mysql RDBMS.
*>                       For use with ACAS v3.02 and later only.
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     acas010   } For file and table access.
*>                       auditMT   }
*>                       fhlogger
*>
*>**
*>   Error messages used.
*>                       SL001.
*>                       SL004.
*>                       SL008.
*>                       SL009.
*>                       SL010.
*>                       SL011.
*>                       SL012.
*>                       SL013.
*>                       SL014.
*>                       SL015.    *>  New 27/07/16
*>                       SL099.
*>**
*>   Changes.
*> 04/08/16 vbc - .01 Forgot to mv stock rec to ws - Der!
*>                    Move zero to File-Function & Access-Type to close
*>                    log file via fh-logger before last call to auditMT
*>                     at RDB close.
*>                    Hopefully will clear error 34.
*>                    LS bugs rearing it head again
*> 07/07/16 vbc - .02 Replace calls to acas010 for auditMT.
*>                    Will still need to test acas010 though !
*> 11/07/16 vbc - .03 Added Log rec count & removed clearing fs-reply.
*>                .04 Clear out un-needed testing displays.
*> 26/07/16 vbc -     Taken from stockLD with same versioning.
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
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
 copy "selaud.cob".
 data division.
*>------------
*>
 file section.
*>-----------
*>
 copy "fdsys.cob".
 copy "fdaudit.cob".
 working-storage section.
*>----------------------
 77  prog-name           pic x(17)    value "auditLD (3.3.00)".
 77  z                   binary-char  value zero.
 77  OS-Delimiter        pic x        value "/".
 77  ACAS_BIN            pic x(512)   value spaces.
 77  ACAS_IRS            pic x(500)   value spaces.
 77  ACAS_LEDGERS        pic x(500)   value spaces.
*>
 01  Arg-Test            pic x(525)   value spaces.
*>
 01  work-fields.
     03  ws-Rec-Cnt-In   pic 9(4)     value zero.
     03  ws-Rec-Cnt-Out  pic 9(4)     value zero.
     03  Ten-Cnt         pic 99  comp value zero.
     03  ws-Start-date.
         05  filler      pic x(8).
         05  Start-Time  pic 9(8).
         05  filler      pic X(5).
     03  ws-End-Date.
         05  filler      pic x(8).
         05  End-Time    pic 9(8).
         05  Lap-Time redefines End-Time.
             07  TT-HH   pic 99.
             07  TT-MM   pic 99.
             07  TT-SS   pic 99.
             07  TT-MS   pic 99.
         05  filler      pic x(5).
     03  ws-reply        pic x.
*>
 01  ACAS-DAL-Common-data.
*>
*>  log file reporting for testing
*>
     03  SW-Testing         pic 9      value 1.
         88  Testing-1                 value 1.
*>
*>  Testing only for displays ws-where etc in RDB DAL
*>
     03  SW-Testing-2       pic 9      value zero.
         88  Testing-2                 value 1.
*>
     03  Log-file-rec-written pic 9(6) value zero.    *> in both acas0nn and a DAL.
*>
 copy "wsaudit.cob".
 copy "wsfnctn.cob".
 copy "wsnames.cob" in "../copybooks".   *> uses the full version.

*>
 01  Error-Messages.
*> System Wide
     03  ST001          pic x(26) value "SL001 System 1 read err = ".
     03  ST004          pic x(59) value "SL004 Problem with opening system file. Hit return to clear".
     03  ST008          pic x(31) value "SL008 Note message & Hit return".
     03  ST009          pic x(53) value "SL009 Environment variables not yet set up : ABORTING".
*> Program specific
     03  SL010          pic x(30) value "SL010 Duplicate key/s found = ".
     03  SL011          pic x(33) value "SL011 Error on auditMT processing".
     03  SL012          pic x(33) value "SL012 Error opening Audit File = ".
     03  SL013          pic x(30) value "SL013 Error on reading file = ".
     03  SL014          pic x(31) value "SL014 Error on writing table = ".
     03  SL015          pic x(34) value "SL015 Error opening Audit Table = ".
     03  SL099          pic x(15) value "SL099 Ignoring.".
*>
 procedure division.
*>=================
*>
 aa000-main-start.
     perform  zz020-Get-Program-Args.
     move     function current-date to ws-Start-date.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     move     5      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock used in FH logging
     move     23     to WS-Log-File-No.  *> RDB, File/Table
*>
*>  Get the system param for the various RDB fields
*>
     open     input System-File.
     if       fs-reply not = zero
              display ST001 fs-reply
              display ST004
              close System-File
              goback
     end-if
     move     1 to rrn.
     read     system-file record.
     if       fs-reply not = zero
              display ST001 fs-reply
              close System-File
              goback
     end-if
*>
*> >>>>>>>>>>>>>>>>>>>>>>>>>   Done in acas010    <<<<<<<<<<<<<<<<<<<<<<
*>  Load up the DB settings from the system record as its not passed on.
*>
*>     move     RDBMS-DB-Name to DB-Schema.
*>     move     RDBMS-User    to DB-UName.
*>     move     RDBMS-Passwd  to DB-UPass.
*>     move     RDBMS-Port    to DB-Port.
*>     move     RDBMS-Host    to DB-Host.
*>     move     RDBMS-Socket  to DB-Socket.
*>
*>
*>  Over-ride processes for acas010/auditMT for Dup modes
*>
     move     zero to File-System-Used
                      File-Duplicates-In-Use
                      FA-File-System-Used
                      FA-File-Duplicates-In-Use.   *>  Cobol file in use
*>
 *>    perform  acas010-Open-Input.      *> open input Cobol stock FILE
     open  input Stock-Audit.
     if    fs-reply not = zero
           display SL012
           stop "SL008 Note message & Hit return"
           close system-file
           goback.
*>
     move     1 to File-System-Used
                   FA-File-System-Used.            *> RDB in use
     perform  acas010-Open.                        *> Open/Init RDB via FH - acas010
     if       FS-Reply not = zero
              display SL015
              close System-File
              goback
     end-if.
     move     zero to Access-Type.
     go       to aa010-Read.
*>
 acas010.
     call     "acas010" using System-Record
                              WS-Stock-Audit-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas010-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas010.
     perform  aa100-Check-4-Errors.
*>
 acas010-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas010.
     perform  aa100-Check-4-Errors.
*>
 acas010-Close.
     set      fn-Close to true.
     perform  acas010.
*>
 acas010-Read-Next.
     set      fn-Read-Next to true.
     perform  acas010.
*>
 acas010-Write.
     set      fn-Write to true.
     perform  acas010.
*>
*>  We will Rollback on any errors but Mysql has to be set up to do it
*>      otherwise as normally it is set to autocommit !!!!!
*>
 aa010-Read.
     move     0 to File-System-Used
                   FA-File-System-Used.            *> Cobol file in use
 *>    perform  acas010-Read-Next.
 *>    if       fs-Reply = 10                        *> EOF
     read    Stock-Audit at end
            move 10 to fs-reply
              go to aa999-Finish .
 *>    end-if
*>
     if       FS-Reply not = zero
              display SL013 at 2301 with highlight erase eol
              display fs-reply at 2325  with highlight
              perform aa020-Rollback
              go to aa999-Finish
     end-if
*>
     add      1 to ws-Rec-Cnt-In.
     add      1 to Ten-Cnt.
     if       Ten-Cnt = 10          *> each period is a count for 10 input records.
              move zero to Ten-Cnt
              display "." no advancing
     end-if
*>
     move     1 to File-System-Used     *> acas0nn set to process RDB
                   FA-File-System-Used.
     perform  acas010-Write.
     if       fs-reply = 22                    *> Check for dup key/record and continue at least while testing
         or   SQL-Err (1:4) = "1062"
              display SL010        at 2001 with foreground-color 2 highlight erase eol
              display WS-File-Key  at 2031 with foreground-color 2 highlight
              display SL099        at 2101
              go to aa010-Read
     end-if
*>
     if       fs-reply not = zero              *> Anything else
              display SL014         at 2001 with foreground-color 2 highlight erase eol
              display fs-reply      at 2032 with foreground-color 2 highlight
              display "WE-Error = " at 2101 with foreground-color 2 highlight
              display WE-Error      at 2111 with foreground-color 2 highlight
              perform aa020-Rollback
              display ST008 at 2201 with erase eol
              accept  Accept-Reply at 2235
              go to aa999-Finish
     end-if
     add      1 to ws-Rec-Cnt-Out.
     go       to aa010-Read.
*>
 aa020-Rollback.
*>
*> These do not work during testing with mariadb - Non transactional model or autocommit set ON
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
              display SL011            at 1401   *> acas010/auditMT processing"
              display "Fs-reply = "    at 1501
              display fs-reply         at 1512
              display "WE-Error = "    at 1601
              display  WE-Error        at 1612
              perform aa020-Rollback
              display ST008 at 1701 with erase eol
              accept  Accept-Reply at 1735
              go to aa999-Finish
     end-if.
*>
 aa999-Finish.
     display  "Record count  in = " at 0601 with erase eol.
     display  ws-Rec-Cnt-In         at 0620.
     display  "Record count out = " at 0641.
     display  ws-Rec-Cnt-Out        at 0660.
     display  "Log Records out  = " at 0701 with erase eol.
     display  Log-File-Rec-Written  at 0720.
     move     1 to File-System-Used
                   FA-File-System-Used.
     move     zero to Access-Type.
     move     2 to File-Function.
     perform  acas010-Close.                     *> Close RDB
     close    System-File.
     move     zero to File-System-Used
                   FA-File-System-Used.
 *>    perform  acas010-close.    *> Close cobol stock file
     close stock-audit.
     move     zero to  File-Function
                       Access-Type.              *> close log file
     call     "fhlogger" using File-Access
                               ACAS-DAL-Common-data.
     move     function current-date to ws-End-date.
     subtract Start-Time from End-Time.
     display  "Elapsed time was " at 0801 with erase eol.
     display  TT-HH              at 0818.
     display  ":"                at 0820.
     display  TT-MM              at 0821
     display  ":"                at 0823
     display  TT-SS              at 0824
     display  ":"                at 0826
     display  TT-MS              at 0827.
     Display  "EOJ - Load Stock Audit Table" at 1001 with erase eol.
 *>    if       FS-Reply = zero or = 10
 *>             perform aa030-Commit
 *>    end-if
     display " ".
     stop     "Check totals then hit return to end".
     goback.
*>
 zz010-Get-Env-Set-Files section.
*>******************************
*>
     accept   ACAS_LEDGERS from Environment "ACAS_LEDGERS".
     accept   ACAS_IRS     from Environment "ACAS_IRS".
     accept   ACAS_BIN     from Environment "ACAS_BIN".
*>
     if       ACAS_IRS (1:1) = space
           or ACAS_LEDGERS (1:1) = spaces
           or ACAS_BIN (1:1) = spaces
              display ST009   at 0505 with erase eos highlight
              display ST008   at 1210 with  foreground-color 3 highlight
              accept ws-reply at 1243
              stop run
     end-if
     if       ACAS_LEDGERS (1:1) = "/"   *> Its Linux/Unix/OSX
              move "/" to OS-Delimiter
     end-if
     if       ACAS_LEDGERS (1:1) = "\"   *> Its Windoz/Dos-Box
              move "\" to OS-Delimiter
     end-if.
*>
 zz010-GESF-Exit.
     exit     section.
*>
 zz020-Get-Program-Args      section.
*>**********************************
*>
     perform  zz010-Get-Env-Set-Files.          *> This must be set so get it 1st + need os-delimiter
*>
 zz020-Set-the-Paths.
     move     zero to z.
     perform  File-Defs-Count times
              add 1 to z
              move space to Arg-Test
              string ACAS_LEDGERS          delimited by space
                     OS-Delimiter          delimited by size
                     System-File-Names (z) delimited by space
                                             into Arg-Test
              end-string
              move     Arg-Test to System-File-Names (z)
     end-perform
     move     zero to z.
*>
 zz020-Exit.
     exit   section.
*>
