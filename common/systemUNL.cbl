       >>source free
*>********************************************
*>                                           *
*>    System UnLoad via the System file      *
*>          For all four records             *
*>   As a backup to a seq file.              *
*>                                           *
*>********************************************
*>
 identification division.
 program-id.             SystemUNL.
*>**
*>   author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, CPL.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Written.            28 May 2023.
*>**
*>   Remarks.            This module only uses the System file but all four records.
*>
*>                       This outputs copy of file record/s from source as a ISAM
*>                       records to a Sequential file with extension of .seq and
*>                       acts as a back up use prognameRES to restore the file.
*>                       If the file exists but produces any errors because of
*>                       a bad file** etc, it will attempt to read the RDB table
*>                       instead, and a message to that effect will be issued.
*>
*>                       ** This can occur if a change of ISAM library is used
*>                       where the new one is incompatable with the old one.
*>
*>                       ALL program output goes to file SYS-DISPLAY.log as an
*>                       extended opened file. So after finishing reading,
*>                       delete it.
*>
*>                       This program creates FOUR records in ORDER :
*>                       Parameter
*>                       Default
*>                       Final
*>                       Totals - SL & PL.
*>
*>                       ALL RECORDS USE 1024 BYTES AS PER THE SIZE OF THE PARAM RECORD.
*>
*>                       For use with ACAS v3.02 and later only.
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     ACAS-Sysout
*>**
*>   Error messages used.
*>                       SY001A.
*>                       SY001B.
*>                       SY001C.
*>                       SY001D.
*>                       SY004.
*>                       SY006A, B, C & D.
*>                       SY007.
*>                       SY008.
*>                       SY009.
*>                       SY019.
*>                       SY020
*>**
*>   Changes.
*> 28/05/23 vbc - .00 systemUNL Source taken from systemLD and vers reset.
*>                .01 Logic adjust if rdb details in file rec etc.
*> 29/05/23 vbc - .02 Tidy up o/p to SYS-DISPLAY.log reporting DB status.
*> 30/05/23 vbc - .03 Add rec counts in, created and total out to rep file.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 07/03/25 vbc   .04 Removed add 1 to ws-Rec-Cnt-R-Out near end - wrong.
*> 19/09/25 vbc - 3.3.00 Version update and builds reset.
*> 15/10/25 vbc - 3.3.01 Updated error and test after write to match *RES progs
*>                       Test for rec 1 at start as need to abort if not found.
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
     select  System-File-Seq assign        "system.seq"
                             organization  sequential
                             status        FS-Reply.
*>
 data division.
*>------------
*>
 file section.
*>-----------
*>
 copy "fdsys.cob".
 fd   system-file-seq.
 copy "wssystem.cob"  replacing System-Record by System-Record-Seq
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
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(20)    value "SystemUNL (3.3.01)".
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
     03  ws-Rec-Cnt-In   pic 999       value zero.
     03  ws-Rec-Cnt-Out  pic 999       value zero.
     03  ws-Rec-Cnt-R-Out pic 999      value zero.
     03  ws-reply        pic x.
     03  WS-Temp-Text    pic x(40)    value spaces.
     03  WS-Dflt-Flag    pic 9        value 1.       *> record read
     03  WS-Final-Flag   pic 9        value 1.       *> ditto
     03  WS-Sys4-Flag    pic 9        value 1.       *> ditto
     03  WS-Rec-Length-1 pic 9(5)     value zero.
*>
 01  SO-Print            pic x(160)    value spaces.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 copy "wsdflt.cob".   *> rec 2 - defaults
 copy "wsfinal.cob".  *> rec 3 - Final accounts
 copy "wssys4.cob".   *> rec 4 - totals for sales and purchase
 copy "wsfnctn.cob".
 copy "wsnames.cob".
 copy "wscall.cob".
*>
 01  Error-Messages.
     03  SY001A         pic x(27) value "SY001A System 1 read err = ".
     03  SY001B         pic x(27) value "SY001B System 2 read err = ".
     03  SY001C         pic x(27) value "SY001C System 3 read err = ".
     03  SY001D         pic x(27) value "SY001D System 4 read err = ".
     03  SY004          pic x(38) value "SY004 Problem with opening system file".
     03  SY006A         pic x(40) value "SY006A Write error on .seq file rec 1 = ".
     03  SY006B         pic x(40) value "SY006B Write error on .seq file rec 2 = ".
     03  SY006C         pic x(40) value "SY006C Write error on .seq file rec 3 = ".
     03  SY006D         pic x(40) value "SY006D Write error on .seq file rec 4 = ".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY019          pic x(37) value "SY019 DB is NOT set up in Param file.".
     03  SY020          pic x(34) value "SY020 DB IS set up in Param file :".
*>
 procedure division.
*>=================
*>
 aa000-Main-Start.
     perform  zz020-Get-Program-Args.
     move     0      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock used in FH logging, 6=SL & PL
     move     10     to WS-Log-File-no.  *> for FHlogger
*>
*>  Get the system param for the various RDB fields
*>
     move     zeros to ws-Rec-Cnt-Out ws-Rec-Cnt-In.
 *>    display  Prog-Name at 0101 with erase eos.
     open     input System-File.
     if       fs-reply not = zero
              display SY001A    at 0401
              display fs-reply  at 0428
              display SY004     at 0501
              close System-File
              move 128 to return-code
              goback
     end-if
     initialise                    *> initialise all secondary records
              Default-Record
              Final-Record
              System-Record-4 with filler.
*> 1st chk rec 1
     move     1 to rrn.
     read     system-file record.
     if       fs-reply not = zero
              display SY001A          at 0801
              display fs-reply        at 0828
              display "Not set up ?"  at 0831
              close System-File
              move 128 to return-code
              goback
     end-if
*>
     move     2 to rrn.
     read     System-File record into Default-Record.
     if       fs-reply not = zero
              display SY001B          at 0501
              display fs-reply        at 0528
              display "Not set up ?"  at 0531
              add     1 to ws-Rec-Cnt-R-Out
     else
              add     1 to ws-Rec-Cnt-In
     end-if
     move     3 to rrn.
     read     System-File record into Final-Record.
     if       fs-reply not = zero
              display SY001C          at 0601
              display fs-reply        at 0628
              display "Not set up ?"  at 0631
              add     1 to ws-Rec-Cnt-R-Out
     else
              add     1 to ws-Rec-Cnt-In
     end-if
     move     4 to rrn.
     read     System-File record into System-Record-4.
     if       fs-reply not = zero
              display SY001D         at 0701
              display fs-reply       at 0728
              display "Not set up ?" at 0731
              add     1 to ws-Rec-Cnt-R-Out
     else
              add     1 to ws-Rec-Cnt-In
     end-if
     move     1 to rrn.
     read     system-file record.
     if       fs-reply not = zero
              display SY001A          at 0801
              display fs-reply        at 0828
              display "Not set up ?"  at 0831
              close System-File
              move 128 to return-code
              goback
     end-if
     add      1 to ws-Rec-Cnt-In.
*>
*> For the system record we will ony write it out to .seq if present
*>  as well have no way to find the RDBMS details without it.
*>
*> but leave this lot in as it wil be used for other file types.
*>
*>  Load up the DB settings from the system record as its not passed on.
*>
*> TEMP CODE
 *>    move     FUNCTION LENGTH (System-Record)    to WS-Rec-Length-1.
 *>    move    spaces to SO-Print.
 *>    string
 *>             Prog-Name
 *>             " System rec size = "
 *>             WS-Rec-Length-1
 *>                 into SO-Print.
 *>    perform  Call-Sysout.
*>
     move     spaces to SO-Print.
     if       FS-Cobol-Files-Used
              string   Prog-Name " "
                       "Cobol file in use " into SO-Print
              perform Call-Sysout
     end-if
*>
     move     spaces to SO-Print.
     if       RDBMS-DB-Name = spaces
              string   Prog-Name
                       " "
                       SY019
                           into SO-Print
              end-string
     else
              string   Prog-Name
                       " "
                       SY020
                       " "
                      "DBName = " FUNCTION TRIM (RDBMS-DB-Name, TRAILING)
                      ","
                      "User = "   FUNCTION TRIM (RDBMS-User, TRAILING)
                      ","
                      "Port = "   FUNCTION TRIM (RDBMS-Port, TRAILING)
                      ","
                      "Host = "   FUNCTION TRIM (RDBMS-Host, TRAILING)
                      ","
                      "Socket = " FUNCTION TRIM (RDBMS-Socket, TRAILING)
                         into So-Print
              end-string.
     perform  Call-Sysout.
*>
     open     output system-file-seq.
     write    System-Record-Seq from System-Record.   *> rec 1
     if       FS-Reply not = zero
              move     spaces to SO-Print
              string   SY006A
                       FS-Reply into SO-Print
              perform  Call-Sysout
              display  SO-Print at 0701 with erase eol foreground-colour 2
     end-if
     write    System-Record-Seq from Default-Record.  *> rec 2
     if       FS-Reply not = zero
              move     spaces to SO-Print
              string   SY006B
                       FS-Reply into SO-Print
              perform  Call-Sysout
              display  SO-Print at 0701 with erase eol foreground-colour 2
     end-if
     write    System-Record-Seq from Final-Record.    *> rec 3
     if       FS-Reply not = zero
              move     spaces to SO-Print
              string   SY006C
                       FS-Reply into SO-Print
              perform  Call-Sysout
              display  SO-Print at 0701 with erase eol foreground-colour 2
     end-if
     write    System-Record-Seq from System-Record-4. *> rec 4
     if       FS-Reply not = zero
              move     spaces to SO-Print
              string   SY006D
                       FS-Reply into SO-Print
              perform  Call-Sysout
              display  SO-Print at 0701 with erase eol foreground-colour 2
     else
              add      1 to WS-Rec-Cnt-Out
     end-if
     move     4 to WS-Rec-Cnt-Out.
*>     add      1 to ws-Rec-Cnt-R-Out.
     close    System-File-Seq
              System-File.
     move     spaces to SO-Print.
     string
              "Records in = "
              ws-Rec-Cnt-In
              " Records Newly Created = "
              ws-Rec-Cnt-R-Out
              " Records Total out = "
              WS-Rec-Cnt-Out
                     into SO-Print.
     perform  Call-Sysout.
     move     "CLOSE " to SO-Print.
     perform  Call-Sysout.
     move     zero to Return-Code.
     goback.
*>
 copy "Proc-Get-Env-Set-Files.cob".  *> Only uses ACAS_LEDGERS now
*>
 Call-Sysout.
     call     "ACAS-Sysout" using SO-Print.
*>
