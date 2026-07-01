       >>source free
*>********************************************
*>                                           *
*>   irsnominal  UnLoad                         *
*>   As a backup to a seq file.              *
*>                                           *
*>********************************************
*>
 identification division.
 program-id.             irsnominalUNL2.
*>**
*>   author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, CPL.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2016 - 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Written.            31 May 2023.
*>**
*>   Remarks.            This module only uses the irsnominal    file.
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
*>                       For use with ACAS v3.02 and later only.
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     ACAS-Sysout
*>**
*>   Error messages used.
*>                       SY003.
*>                       SY006.
*>                       SY007.
*>                       SY008.
*>                       SY009.
*>**
*>   Changes.
*>  1/06/23 vbc - .00 irsnominalUNL source taken from analysisUNL.
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
     select nominal-ledger  assign       File-34   *> nl-file
                            organization indexed
                            access       dynamic
                            record       NL-key
                            status       fs-reply.
*>
     select  irsnominal-File-Seq  assign      "irsacnts.seq"
                                organization  line sequential
                                status        FS-Reply.
*>
 data division.
*>------------
*>
 file section.
*>-----------
*>
 fd  nominal-ledger.
 01  Nominal-Record.
     03  NL-Key.
         05  NL-Owning      pic 9(5).
         05  NL-Sub-Nominal pic 9(5).
     03  NL-Type            pic x.
         88  Owner                   value is "O".
         88  Sub                     value is "S".
     03  NL-Data.
         05  NL-Name        pic x(24).
         05  NL-DR          pic 9(8)v99   comp.
         05  NL-CR          pic 9(8)v99   comp.
         05  NL-DR-Last-1     pic 9(8)V99   comp.
         05  NL-DR-Last-2     pic 9(8)V99   comp.
         05  NL-DR-Last-3     pic 9(8)V99   comp.
         05  NL-DR-Last-4     pic 9(8)V99   comp.
         05  NL-CR-Last-1     pic 9(8)V99   comp.
         05  NL-CR-Last-2     pic 9(8)V99   comp.
         05  NL-CR-Last-3     pic 9(8)V99   comp.
         05  NL-CR-Last-4     pic 9(8)V99   comp.
         05  NL-AC          pic x.
     03  filler  redefines  NL-Data.
         05  NL-Pointer     pic 9(5).
 fd  irsnominal-File-Seq.
*>
 01  WS-Nominal-Record.
     03  NL-Key.
         05  NL-Owning      pic 9(5).
         05  NL-Sub-Nominal pic 9(5).
     03  NL-Type            pic x.
         88  Owner                   value is "O".
         88  Sub                     value is "S".
     03  NL-Data.
         05  NL-Name        pic x(24).  *> 35
         05  NL-DR          pic 9(8).99.  *> 11+11+44+44+1 111+35 146
         05  NL-CR          pic 9(8).99.  *> 22 57
         05  NL-DR-Last-1     pic 9(8).99. *> 44
         05  NL-DR-Last-2     pic 9(8).99. *> 44
         05  NL-DR-Last-3     pic 9(8).99. *> 44
         05  NL-DR-Last-4     pic 9(8).99. *> 44
         05  NL-CR-Last-1     pic 9(8).99. *> 44
         05  NL-CR-Last-2     pic 9(8).99. *> 44
         05  NL-CR-Last-3     pic 9(8).99. *> 44
         05  NL-CR-Last-4     pic 9(8).99. *> 44
         05  NL-AC          pic x.
     03  filler  redefines  NL-Data.
         05  NL-Pointer     pic 9(5).
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(24)    value "irsnominalUNL2 (3.3.00)".
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
     03  ws-reply        pic x.
*>
 01  SO-Print            pic x(160)    value spaces.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 copy "wsfnctn.cob".
 copy "wsnames.cob".
 copy "wscall.cob".
*>
 01  Error-Messages.
     03  SY003          pic x(40) value "SY003 Problem reading irsnominal file = ".
     03  SY006          pic x(30) value "SYS06 Write error on .seq file".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
*>
 procedure division.
*>=================
*>
 aa000-Main-Start.
     perform  zz020-Get-Program-Args.
     move     1      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock used in FH logging, 6=SL & PL
     move     11     to WS-Log-File-no.  *> for FHlogger
*>
     move     spaces to SO-Print.
     string   Prog-Name " "
              "Cobol files in use " into SO-Print.
     perform Call-Sysout.
*>
*> BYPASS ALL THE STANDARD CODING AS JUST WRITE THE REC OUT
*>
     open     input    Nominal-Ledger.
     if       FS-Reply not = zeros
              move     "No irsnominal file to process" to SO-Print
              perform  Call-Sysout
              close    Nominal-Ledger
              move     "CLOSE " to SO-Print
              perform  Call-Sysout
              goback
     end-if.
     open     output   irsnominal-File-Seq.
     move     zeros to ws-Rec-Cnt-In ws-Rec-Cnt-Out.
*>
 aa010-Read-Recs.
     perform  forever
              read     Nominal-Ledger next record at end
                       go to aa020-Finish-Off
              end-read
              if       FS-Reply not = zeros
                       string   SY003
                                FS-Reply
                                  into SO-Print
                       end-string
                       perform  Call-Sysout
                       go to aa020-Finish-Off
              end-if
              add      1 to WS-Rec-Cnt-In
              initialise WS-Nominal-Record
              move     corresponding Nominal-Record to WS-Nominal-Record
              write    WS-Nominal-Record
 *>             write    WS-Nominal-Record from Nominal-Record
              if       FS-Reply not = zero
                       move spaces to SO-Print
                       string   SY006
                                " "
                                FS-Reply
                                   into SO-Print
                       perform  Call-Sysout
                       display WS-Nominal-Record at 0101 with erase eos
                       display Sy008 at 0301
                       accept WS-Reply at 0334
                       go to aa020-Finish-Off
              end-if
              add      1 to WS-Rec-Cnt-Out
     end-perform.
*>
aa020-Finish-Off.
     close    irsnominal-File-Seq
              Nominal-Ledger.
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
 copy "Proc-Get-Env-Set-Files.cob".  *> Only uses ACAS_irsnominalS now
*>
 Call-Sysout.
     call     "ACAS-Sysout" using SO-Print.
*>
