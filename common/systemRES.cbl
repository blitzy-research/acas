       >>source free
*>********************************************
*>                                           *
*>    System REStore in the System file      *
*>          For all four records             *
*>   From  a seq file.                       *
*>                                           *
*>********************************************
*>
 identification division.
 program-id.             SystemRES.
*>**
*>   author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, CPL.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Written.            3 June 2023.
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
*>                       SY007.
*>                       SY008.
*>                       SY009.
*>                       SY019.
*>                       SY020
*>                       SY021 - 24
*>**
*>   Changes.
*> 28/05/23 vbc - .00 systemRES Source taken from systemLD and vers reset.
*>                .01 Logic adjust if rdb details in file rec etc.
*> 29/05/23 vbc - .02 Tidy up o/p to SYS-DISPLAY.log reporting DB status.
*> 30/05/23 vbc - .03 Add rec counts in, created and total out to rep file.
*> 03/06/23 vbc - .00 Created from systemUNL.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc - 3.3.00 Version update and builds reset.
*> 14/10/25 vbc - 3.3.01 Added SY021,24 for write errors. Need to add code to
*>                       all other routines - RES.
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
 77  prog-name           pic x(20)    value "SystemRES (3.3.01)".
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
     03  ws-Rec-Cnt-In   pic 9999       value zero.
     03  ws-Rec-Cnt-Out  pic 9999       value zero.
     03  ws-Rec-Cnt-R-Out pic 9999      value zero.
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
 copy "wssystem.cob"  replacing System-Record by WS-System-Record.
 copy "wsdflt.cob".   *> rec 2 - defaults
 copy "wsfinal.cob".  *> rec 3 - Final accounts
 copy "wssys4.cob".   *> rec 4 - totals for sales and purchase
 copy "wsfnctn.cob".
 copy "wsnames.cob".
 copy "wscall.cob".
*>
 01  Error-Messages.
     03  SY001A         pic x(28) value "SY001A System 1 read err = ".
     03  SY001B         pic x(28) value "SY001B System 2 read err = ".
     03  SY001C         pic x(28) value "SY001C System 3 read err = ".
     03  SY001D         pic x(28) value "SY001D System 4 read err = ".
     03  SY004          pic x(38) value "SY004 Problem with opening system file".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY019          pic x(37) value "SY019 DB is NOT set up in Param file.".
     03  SY020          pic x(34) value "SY020 DB IS set up in Param file :".
     03  SY021          pic x(27) value "SY021 System write 1 Err = ".
     03  SY022          pic x(27) value "SY022 System write 2 Err = ".
     03  SY023          pic x(27) value "SY023 System write 3 Err = ".
     03  SY024          pic x(27) value "SY024 System write 4 Err = ".
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
     move     zeros  to ws-Rec-Cnt-Out ws-Rec-Cnt-In.
     open     input System-File-Seq.
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display SY004     at 0401
              accept  fs-reply  at 0440
              close System-File
              move 128 to return-code
              goback
     end-if
     initialise                    *> initialise all secondary records in WS
              WS-System-Record
              Default-Record
              Final-Record
              System-Record-4 with filler.
*>
     read     system-file-Seq next record into WS-System-Record at end
              move 256 to return-code
              goback.
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display SY001A          at 0401
              display fs-reply        at 0428
              display "Not set up ?"  at 0431
     else
              add     1 to ws-Rec-Cnt-In
     end-if
     display System-record-Seq at 0101 with erase eos.
     display "System Rec" at 2201.
     display sy008 at 2301 with erase eol.
     accept fs-reply at 2334.
*>
     read     System-File-Seq next record into Default-Record.
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display SY001B          at 0501
              display fs-reply        at 0528
              display "Not set up ?"  at 0531
     else
              add     1 to ws-Rec-Cnt-In
     end-if
     display System-record-Seq at 0101 with erase eos.
     display "Default Rec" at 2201.
     display sy008 at 2301 with erase eol.
     accept fs-reply at 2334.
*>
     read     System-File-seq next record into Final-Record.
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display SY001C          at 0601
              display fs-reply        at 0628
              display "Not set up ?"  at 0631
     else
              add     1 to ws-Rec-Cnt-In
     end-if
     display System-record-Seq at 0101 with erase eos.
     display "Final Rec" at 2201.
     display sy008 at 2301 with erase eol.
     accept fs-reply at 2334.
*>
     read     System-File-seq next record into System-Record-4.
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display SY001D         at 0701
              display fs-reply       at 0728
              display "Not set up ?" at 0731
     else
              add     1 to ws-Rec-Cnt-In
     end-if
     display System-record-Seq at 0101 with erase eos.
     display "System 4 Rec" at 2201.
     display sy008 at 2301 with erase eol.
     accept fs-reply at 2334.
*>
     open     output System-File.
*>
     move     1 to rrn.
     write    System-Record from System-Record.   *> rec 1
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display  SY021          at 0701
              display  fs-reply       at 0728
     else
              add      1 to WS-Rec-Cnt-Out.
*>
     move     2 to rrn.
     write    System-Record from Default-Record.  *> rec 2
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display  SY022          at 0801
              display  fs-reply       at 0828
     else
              add      1 to WS-Rec-Cnt-Out.
*>
     move     3 to rrn.
     write    System-Record from Final-Record.    *> rec 3
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display  SY023          at 0901
              display  fs-reply       at 0928
     else
              add      1 to WS-Rec-Cnt-Out.
*>
     move     4 to rrn.
     write    System-Record from System-Record-4. *> rec 4
     if       fs-reply not = zero
              display  Prog-Name at 0101
              display  SY024          at 1001
              display  fs-reply       at 1028
     else
              add      1 to WS-Rec-Cnt-Out.
*>
     close    System-File-Seq
              System-File.
     move     spaces to SO-Print.
     string
              "Records in = "
              ws-Rec-Cnt-In
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
