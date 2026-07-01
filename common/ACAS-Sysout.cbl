       >>source free
*>
 identification division.
 program-id.             ACAS-Sysout.
*>**
*>   author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, CPL.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2019 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Remarks.            Takes output from calling routine and writes to
*>                       a unique output text file then space fills input
*>                       in the common input field.
*>                       This avoids one with ESCape sequences so
*>                       that it can be read by user.
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     none.
*>   Called by.          systemLD and other RDBMS load programs.
*>
*>**
*>   Error messages used.
*>**
*>   Changes.
*> 08/06/19 vbc - .00 Written.
*> 28/05/23 vbc - .01 Increased record from 80 to 160.
*> 29/05/23 vbc   .02 Issue a 'Process Ended' msg on getting a 'CLOSE' - keeps it tidy.
*> 11/07/23 vbc - .03 Added date/time to each msg.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>
*>*************************************************************************
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
*>*************************************************************************
*>
*>
 environment division.
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
       select  Screen-Output  assign "SYS-DISPLAY.log"
                              organization line sequential
                              file status FS-Status.
 data division.
 file section.
 fd  Screen-Output.
 01  SO-Record.
     03  SO-Log-Date    pic 9(8).
     03  f1             pic x.        *> just spacers for viewing log file
     03  SO-Log-Time    pic 9(8).
     03  f2             pic x.
     03  SO-Print       pic x(160).
*>
 working-storage section.
 77  prog-name          pic x(21)    value "ACAS-Sysout (3.3.00)".
 77  File-Status        pic 9        value zero.
     88  SO-Open                      value 1.
     88  SO-Closed                    value zero.
 77  FS-Status          pic 99       value zero.
*>
 01  WS-CDT.
     03  CDT-Date       pic 9(8).   *> to Log-Date  cc yymmdd.
     03  CDT-Time       pic 9(8).   *> to Log-Time  hhmmssmm.
     03  CDT-Diff-HH    pic s99  sign leading separate.
     03  CBT-Diff-MM    pic 99.
*>
 linkage section.
 01  LS-SO-Print        pic x(160).
*>
 procedure division using LS-SO-Print.
     move     function Current-Date to WS-CDT.
     move     CDT-Date      to SO-Log-Date.
     move     CDT-Time      to SO-Log-Time.
     move     spaces to F1 F2.
     if       SO-Closed
              perform zz010-Open-File
              go to AA010-Process.
*>
     if       LS-SO-Print (1:6) = "CLOSE "
       and    SO-Open
              move     "Process Ended." to SO-Print
              move     CDT-Date      to SO-Log-Date
              move     CDT-Time      to SO-Log-Time
              move     spaces to F1 F2
              write    SO-Record
              close    Screen-Output
              set      SO-Closed to true
              move     spaces to LS-SO-Print   *> JIC it is reused
              goback
     end-if.
*>
 AA010-Process.
     move     LS-SO-Print to SO-Print.
     move     CDT-Date      to SO-Log-Date.
     move     CDT-Time      to SO-Log-Time.
     move     spaces to F1 F2.
     write    SO-Record.
     move     spaces to LS-SO-Print.
     goback.
*>
 zz010-Open-File.
     open     extend Screen-Output.
     if       FS-Status not = zero
              close Screen-Output
              open output Screen-Output
     end-if
     set SO-Open to true.
*>
