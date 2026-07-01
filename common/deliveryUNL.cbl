       >>source free
*>********************************************
*>                                           *
*>   delivery  UnLoad                         *
*>   As a backup to a seq file.              *
*>                                           *
*>********************************************
*>
 identification division.
 program-id.             deliveryUNL.
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
*>   Remarks.            This module only uses the delivery    file.
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
*>  1/06/23 vbc - .00 deliveryUNL source taken from analysisUNL.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc - 3.3.00 Version update and builds reset.
*> 15/10/25 vbc - 3.3.01 Updated error and test after write to match *RES progs.
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
 copy "seldel.cob".
     select  delivery-File-Seq  assign        "delivery.seq"
                                organization  sequential
                                status        FS-Reply.
*>
 data division.
*>------------
*>
 file section.
*>-----------
*>
 copy "fddel.cob".
 fd  delivery-File-Seq.
 copy "wsdel.cob".
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(22)    value "deliveryUNL (3.3.01)".
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
     03  SY003          pic x(35) value "SY003 Problem reading batch file = ".
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
     move     6      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock used in FH logging, 6=SL & PL
     move     14     to WS-Log-File-no.  *> for FHlogger
*>
     move     spaces to SO-Print.
     string   Prog-Name " "
              "Cobol files in use " into SO-Print.
     perform Call-Sysout.
*>
*> BYPASS ALL THE STANDARD CODING AS JUST WRITE THE REC OUT
*>
     open     input    Delivery-File.
     if       FS-Reply not = zeros
              move     "No delivery file to process" to SO-Print
              perform  Call-Sysout
              close    Delivery-File
              move     "CLOSE " to SO-Print
              perform  Call-Sysout
              goback
     end-if.
     open     output   delivery-File-Seq.
     move     zeros to ws-Rec-Cnt-Out ws-Rec-Cnt-In.
*>
 aa010-Read-Recs.
     perform  forever
              read     Delivery-File next record at end
                       exit perform
              end-read
              if       FS-Reply not = zeros
                       string   SY003
                                FS-Reply
                                  into SO-Print
                       end-string
                       perform  Call-Sysout
                       exit perform
              end-if
              add      1 to WS-Rec-Cnt-In
              write    WS-Delivery-Record from Delivery-Record
              if       FS-Reply not = zero
                       move     spaces to SO-Print
                       string   SY006
                                FS-Reply into SO-Print
                       perform  Call-Sysout
                       display  SO-Print at 0701 with erase eol foreground-colour 2
                       exit perform
              end-if
              add      1 to WS-Rec-Cnt-Out
     end-perform.
*>
aa020-Finish-Off.
     close    delivery-File-Seq
              Delivery-File.
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
