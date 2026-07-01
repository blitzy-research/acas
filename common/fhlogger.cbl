       >>source free
*>
*> CDF STARTS
*>
*> This will turn ACAS file logging on or off through out the ACAS system
*>
*> On / off log control - applies to all calls.
*>
*>   This is logging off  so remove the '*>' and add '*>' to
*>         the other line starting with *>>> .
*>
*>>>DEFINE CONSTANT C-Logging-On   AS "N"
*>
*>   This is logging on
*>
>>DEFINE CONSTANT C-Logging-On   AS "Y"
*>
*> CDF ENDS
*>
*>***********************************************
*>                                              *
*>         Common File/Table Logger             *
*>               [ fhlogger ]                   *
*>***********************************************
*>
 identification division.
 Program-Id.            fhlogger.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 - 2026 and later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             File Logger for
*>                      Stock File / Table.
*>                      ******************
*>                      This and associated modules relate to
*>                      ACAS versions v3.02 and later.
*>**
*> WARNING:             This module will store the log file in the
*>                      CURRENT directory.
*>**
*> Called Modules:      None.
*>**
*> Called By:
*>                      acas0nn & acasirsubn - Cobol FHs.
*>                      xxxxxxMT - DAL (RDB Data Access Layer) or a variation
*>                                using JCs or dbpre SQL processor.
*>
*>**
*> Error Messages Used. FH901, 3.
*>
*>**
*> Version.             1.00 04/08/2016.
*>
*>
*> Changes.
*>                    Init coding.
*> 04/08/16 vbc - .01 Added SQL-Err & Msg to file.
*> 11/08/16 vbc - .02 Changed File Status to use FX-Reply to stop being overwritten
*> 27/07/16 vbc - .03 Zeroise recs out count after opening log file.  REMd out 29/07
*> 22/12/16 vbc - .04 Reversed pos of function and access & made function 99.
*> 27/12/16 vbc - .05 Added new field SQL-State to logging and likewise for fnctn.cob.
*>                    Needs total recompile for all.
*>                    New call added into cobmysqlapi(38) for it - Subject to Testing.
*> 30/12/16 vbc - .06 Increased key & msg fields that makes it a 512 byte record.
*> 23/06/20 vbc - .07 Added code to test if we are file logging and if not exit.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>********************************************************************************************
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
*>**********************************************************************************
*>
 environment division.
 copy "envdiv.cob".
*>
 input-output section.
 file-control.
*>
     select Log-File assign "fh-logger.txt"
                     organisation  line
                                  Sequential
                     status Fx-Reply.
*>
 data division.
 file section.
*>***********
*>
*>  This file is also used via the caller DAL & FH units to record
*>   all transactions (during testing) as well as reported
*>    error conditions.
*>
 FD  Log-File.
 01  Log-Record.
     03  Log-Date       pic 9(8).
     03  f1             pic x.        *> just spacers for viewing log file
     03  Log-Time       pic 9(8).
     03  f2             pic x.
     03  Log-System     pic 9.        *> 1=IRS, 2=GL, 3=Sales, 4=Purch, 5=Stock
     03  f3             pic x.
     03  Log-File-no    pic 99.       *> char 1 = flat, 2=RDB, char2== 1 = system, 2 = stock, 3 = ?
     03  f4             pic x.
     03  Log-FS-Error   pic 99.
     03  f5             pic x.
     03  Log-We-Error   pic 999.
     03  f6             pic x.
     03  Log-Function   pic 99.       *> 32
     03  f7             pic x.
     03  Log-Access     pic 9.
     03  f9             pic x.
     03  Log-Para       pic 999.
     03  f10            pic x.
     03  Log-Errno      pic x(5).     *> 44
     03  f8             pic x.
     03  Log-SQL-State  pic x(5).
     03  f11            pic x.
     03  Log-Key        pic x(64).    *> 109
     03  dollar1        pic x.        *>    $ spacer for viewing log file
     03  Log-Msg        pic x(176).    *> 286
     03  dollar2        pic x.        *> 287
     03  Log-Where      pic x(225).   *> 512
*>
 working-storage section.
*>**********************
*>
 77  prog-name          pic x(17)  value "fhloger (3.3.00)".
 77  Log-File-Open-Flag pic 9      value zero.
     88  LFOF-Closed               value zero.
     88  LFOF-Open                 value 1.
*>
 77  fx-reply           pic 99     value zeroes.
 77  WS-Logging-On      pic X      value C-Logging-On.
     88  File-Logging-Off          value "N".
 *>
 01  WS-CDT.
     03  CDT-Date       pic 9(8).   *> to Log-Date  cc yymmdd.
     03  CDT-Time       pic 9(8).   *> to Log-Time  hhmmssmm.
     03  CDT-Diff-HH    pic s99  sign leading separate.
     03  CBT-Diff-MM    pic 99.
*>
 01  Error-Messages.
*> System Wide
*> Module Specific
     03  FH901          pic x(31) value "FH901 Note error and hit return".
     03  FH903          pic x(34) value "FH903 Write failure on Log File = ".
*>
 Linkage Section.
*>**************
 copy "wsfnctn.cob".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 Procedure Division Using File-Access
                          ACAS-DAL-Common-data.
*>********************************************
*>
 Ca-Process-Logs    Section.
*>*************************
*>
 Ca010-Create-Log-Rec.
*>
*>  First test if FF and AT zero = close log file as requested by caller.
*>
     if       File-Function = zero
        and   Access-Type   = zero
         and  LFOF-Open
              move zero to Log-File-Open-Flag
              close Log-File
              go to ca999-exit
     end-if
*>
     if       File-Logging-Off
              go to ca999-Exit.
*>
     if       LFOF-Closed
              open extend Log-File
              if   fx-Reply not = zero
                   close Log-File
                   open output Log-File
              end-if
              move 1 to Log-File-Open-Flag
 *>             move zero to Log-File-Rec-Written
     end-if.
*>
     initialize Log-Record.
     move     space to f1 f2 f3 f4 f5 f6 f7 f8 f9 f10 f11.
     move     "$" to dollar1 dollar2.
     move     function Current-Date to WS-CDT.
     move     CDT-Date      to Log-Date.
     move     CDT-Time      to Log-Time.
     move     FS-Reply      to Log-FS-Error.
     move     WE-Error      to Log-WE-Error.
     move     ws-Log-System to Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock
*>
*>   need to change next one if used in the DAL, e.g., move "22" ...
*>
     move     WS-Log-File-no  to Log-File-no.     *> char 1 = 1 flat, 2 = Rdb; char 2 = file/table
     move     File-Function   to Log-Function.
     move     ws-No-Paragraph to Log-Para.
     move     Access-Type     to Log-Access.
     move     WS-File-Key     to Log-Key.         *> caller must move this or spaces !
     move     WS-Log-Where    to Log-Where.
     move     SQL-Err         to Log-Errno.
     move     SQL-Msg         to Log-Msg.
     move     SQL-State       to Log-SQL-State.
     write    Log-Record.
     if       FX-Reply not = zero         *> Poss. problems with open EXTEND - again!
              display  FH903    at 2301 with erase eol
              display  FX-Reply at 2335
              display  FH901    at 2401 with erase eol
              accept   Accept-Reply at 2433
              display  " "      at 2301 with erase eol
              display  " "      at 2401 with erase eol
              close    Log-File
              move     zero to Log-File-Open-Flag
              go to    ca999-Exit.
*>
     add      1 to Log-File-Rec-Written.
*>
 ca999-Exit.
     exit     program.
*>*********   *******
*>
 end program fhlogger.

