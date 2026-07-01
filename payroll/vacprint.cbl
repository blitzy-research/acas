       >>source free
*>****************************************************************
*>                  Employee Vacation Reporting                  *
*>                                                               *
*>            Uses RW (Report writer for prints)                 +
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       vacprint.  *> to be renamed pynnn later.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 2/02/2026.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Employee Vacation Reporting.
*>                       This program uses RW (Report Writer)
*>
*>                      Semi-sourced from Basic code from vacprint.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.    IS IT ??
*>                      (CBL_) ACCEPT_NUMERIC.c as static.
*>**
*>    Functions Used:
*>                      None.
*>    Files used :
*>                      pypr1.   Params
*>                      pyemp.   Employee Master.
*>
*>    Error messages used.
*> System wide:
*>                      SY001, 10 & 13
*> Program specific:
*>                      PY001 - 3.
*>**
*> Changes:
*> 02/02/2026 vbc - 1.0.00 Created - Started coding from empprint.
*> 02/02/2026 vbc          Completed but headings / details will be not aligned.
*>
*>**
*>*************************************************************************
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
*> with your commercial plans and proposals to vbcoen@gmail.com.
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
 environment             division.
*>================================
*>
 copy "envdiv.cob".
 SPECIAL-NAMES.
       CRT STATUS is COB-CRT-STATUS.
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
*>
 input-output            section.
 file-control.
 copy "selpyparam1.cob".
 copy "selpyemp.cob".
*>
 copy "selprint.cob".    *> 132
*>
 data                    division.
*>================================
*>
 file section.
*>
 copy "fdpyparam1.cob".
 copy "fdpyemp.cob".
*>
 fd  Print-File
     reports are Employee-Vacation-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "vacprint (1.0.00)".  *> First release pre testing.
*>
*>  This will print 1 copy to CUPS print spool specified on line 3 override via setup at SOJ
*>
 copy "print-spool-command.cob".     *> CHECK PRN file for content Landscape mode
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "Test-Data-Flags.cob".           *> set sw-Testing to zero to stop logging.
*>                                        ABOVE SHOULD BE OFF
*> REMARK OUT ANY IN USE
*>
 01  WS-Data.
     03  WS-Reply            pic x.
     03  PY-PR1-Status       pic xx.
     03  PY-Emp-Status       pic xx.
*>
     03  WS-Eval-Msg         pic x(25)    value spaces.
     03  WS-Env-Columns      pic 999      value zero.
     03  WS-Env-Lines        pic 999      value zero.
     03  WS-22-Lines         pic 99.
     03  WS-23-Lines         pic 99.
     03  WS-Lines            pic 99.
     03  A                   pic 99       value zero.
     03  B                   pic 99       value zero.
     03  C                   pic 99       value zero.
     03  D                   pic 999      value zero.    *> to set up accounts table with "Unknown" in desc
     03  F                   pic 9        value zero.
     03  WS-Page-Lines       binary-char unsigned value 56.   *> Narrow reports as system is for Landscape used.
     03  WS-Rec-Cnt          pic 99       value zero.
     03  WS-Page-Cnt         pic 999      value zero.
     03  WS-Line-Cnt         pic 999      value 90.   *> Force heads at start
*>
 01  WS-Test-YMD             pic 9(8).
 01  WS-Test-Date.
     03  WS-Test-Month       pic 99.
     03  WS-Test-Days        pic 99.
     03  WS-Test-Year        pic 9(4).
 01  WS-Test-Date9 redefines WS-Test-Date
                             pic 9(8).
*>
 01  WS-Temp-Date.
     03  WS-Temp-Year        pic 9(4).
     03  WS-Temp-Month       pic 99.
     03  WS-Temp-Days        pic 99.
 01  WS-Temp-Date9  redefines WS-Temp-Date
                             pic 9(8).  *> For direct moving 9(8) to Date.
*>
 01  WS-Date-Formats.
     03  WS-Swap             pic 99.
     03  WS-Conv-Date        pic x(10).
     03  WS-Date             pic x(10)   value "99/99/9999".
     03  WS-UK redefines WS-Date.   *> Other optional format
         05  WS-Days         pic 99.
         05  filler          pic x.
         05  WS-Month        pic 99.
         05  filler          pic x.
         05  WS-Year         pic 9(4).
     03  WS-USA redefines WS-Date.  *> Default format
         05  WS-USA-Month    pic 99.
         05  filler          pic x.
         05  WS-USA-Days     pic 99.
         05  filler          pic x.
         05  filler          pic 9(4).
     03  WS-Intl redefines WS-Date.   *> Not used.
         05  WS-Intl-Year    pic 9(4).
         05  filler          pic x.
         05  WS-Intl-Month   pic 99.
         05  filler          pic x.
         05  WS-Intl-Days    pic 99.
*>
 01  hdtime                            value spaces.
     03  hd-hh               pic xx.
     03  hd-mm               pic xx.
     03  hd-ss               pic xx.
     03  hd-uu               pic xx.
*>
 01  Error-Messages.   *> ANY NEEDED ???
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*>
*> Module General
*>
     03  PY001           pic x(45) value "PY001 Payroll Parameter file does not exist -".
     03  PY002           pic x(32) value "PY002 Read PARAM record Error = ".
     03  PY003           pic x(31) value "PY003 Employee File not Found -".
*>
 01  Error-Code          pic 999.
*>
 01  COB-CRT-Status      pic 9(4)         value zero.
     copy "screenio.cpy".
*>
 copy "wstime.cob".
*>
 linkage section.
*>***************
*>
>>LISTING OFF   *> Just in case one day it works !!!
 copy "wscall.cob".
 copy "wssystem.cob"   replacing System-Record by WS-System-Record.
 copy "wsnames.cob".
>>LISTING ON
*>
 01  To-Day              pic x(10).
*>
 Report section.    *> All MAY NEED CHANGING
*>**************
*>
 RD  Employee-Vacation-Report
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 5
     Last  Detail WS-Page-Lines.
*>
 01  Report-Emp-Head-2  Type Page Heading.
*>
*> Print layouts to 132 cols Landscape
*>
     03  line  1.
         05  col  50     pic x(40)   source UserA.
         05  col 110     pic x(10)   source U-Date.
         05  col 122     pic x(8)    source WSD-Time.
     03  line  2.
         05  col   1     pic x(17)   source Prog-Name.
         05  col  51     pic x(19)   value "ACAS Payroll System".
         05  col 124     pic x(5)    value "Page ".
         05  col 129     pic zz9     source Page-Counter.
     03  Line  3.
         05  col  53     pic x(48)   value "Vacation Report".
     03  line  5.
         05  col   1                 value "------ Employee ------".
         05  col  38                 value "  Vacation    Vacation Units   Vacation     -----------  Sick Leave  -----------".
     03  line  6.
         05  col   1                 value "Number      Name".
         05  col   38                value "Accum. Rate   Accumulated     Units Used    Accum. Rate  Units Accum.   Units used".
*>
*> Above WILL be wrong
*>
 01  Emp-Detail type is detail.
     03  line + 2.
         05  col   1     pic 9(7)          source Emp-No.
         05  col  10     pic x(32)         source Emp-Name.
         05  col  39     pic zz,zz9.99     source Emp-Vac-Rate.
         05  col  48     pic zz,zz9.99     source Emp-Vac-Accum.
         05  col  62     pic zz,zz9.99     source Emp-Vac-Used.
         05  col  78     pic zz,zz9.99     source Emp-SL-Rate.
         05  col  86     pic zz,zz9.99     source Emp-SL-Accum.
         05  col 100     pic zz,zz9.99     source Emp-SL-Used.
     03  line + 2.
         05  col  15     pic x(12)         value "(Active)    "   present when Emp-Status = "A".
         05  col  15     pic x(12)         value "(Terminated)"   present when Emp-Status = "T".
         05  col  15     pic x(12)         value "(On-Leave)  "   present when Emp-Status = "L".
         05  col  15     pic x(12)         value "(Deleted)   "   present when Emp-Status = "D".
         05  col  40                       value "Comp. Time Accumulated:".
         05  col  61     pic zz,zz9.99  source Emp-Comp-Accum.
         05  col  84                       value "Comp. Time Used:".
         05  col  99     pic zz,zz9.99  source Emp-Comp-Used.
*>
*> Can we add these line to previous line and are we aligned from titles ??  <<<
*>

*>
 01  type control Footing Final line plus 2.
     03  col 1           pic x(34)         value "Total - Employee Account Records :".
     03  col 36          pic zzz9          source WS-Rec-Cnt.
*>
 procedure division using WS-Calling-Data  *> ACAS
                          WS-System-Record *> ACAS
                          To-Day           *> ACAS
                          File-Defs.       *> ACAS
*>
 aa000-Main                  section.
*>**********************************
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     CURRENT-DATE to WSE-Date-block.
     move     WSE-HH  to  WSD-HH.
     move     WSE-MM  to  WSD-MM.
     move     WSE-SS  to  WSD-SS.  *> WSD-Time
     move     Print-Spool-Name to PSN.  *> set ACAS prt spool for o/p
*>
*> Get current-date into locale format for display and printing
*>
     perform  ZZ070-Convert-Date.
     move     WS-Date to WS-Conv-Date.  *> Use for reporting etc.
*>
*> Terminal-Sizing.
*>
     perform  forever
              accept   WS-Env-Lines   from lines
              if       WS-Env-Lines < 28
                       display  SY010    at 0101 with erase eos
                       accept   WS-Reply at 0133
                       move     8 to WS-Term-Code
                       exit perform cycle
              end-if
              accept   WS-Env-Columns from Columns
              if       WS-Env-Columns < 80
                       display  SY013    at 0101 with erase eos
                       accept   WS-Reply at 0130
                       move     8 to WS-Term-Code
                       exit perform cycle
              end-if
     end-perform.
*>
*> Set up error message areas on screen - assumes terninal set for => 28 deep
*>  and must be 80 wide   BUT only needs depth of 24 or more.
*>
     subtract 2 from WS-Env-Lines giving WS-22-Lines.
     subtract 1 from WS-Env-Lines giving WS-23-Lines.
     move     WS-Env-Lines to WS-Lines.
     move     zero         to WS-Term-Code.
*>
 aa010-Open-PY-Files.
*>
*> Check for files and Quit if any are missing or there is no data for Emp.
*>
*>  Param file not really needed for this program ?
*>
     open     input PY-Param1-File.
     if       PY-PR1-Status not = "00"      *> Does not exist yet so lets create it & write rec
              perform  ZZ040-Evaluate-Message
              display  PY001         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-PR1-Status at line WS-23-Lines col 47
              display  WS-Eval-Msg   at line WS-23-Lines col 50
              display  SY001         at line WS-Lines    col 1 foreground-color 2
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 1        *> == no param file
     end-if.
*>
*> Get PY params data for line count etc
*>
     move     1        to RRN.
     read     PY-Param1-File key RRN
     if       PY-PR1-Status not = "00"
              perform  ZZ040-Evaluate-Message
              display  PY002         at line WS-23-Lines col 1 with erase eos
              display  PY-PR1-Status at line WS-23-Lines col 33
              display  WS-Eval-Msg   at line WS-23-Lines col 36
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 6
     end-if.
*>
     close    PY-Param1-File.             *> Record still in WS area
     move     zero  to  Return-Code.
*>
     open     input    PY-Employee-File.    *> Now OPEN
     if       PY-Emp-Status not = zero
              move     PY-Emp-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY003         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-Emp-Status at line WS-23-Lines col 33 foreground-color 4
              display  WS-Eval-Msg   at line WS-23-Lines col 36
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Employee-File
              move     1 to WS-Term-Code
              goback   returning 3.
*>
     move     zeros to WS-Page-Cnt.
     move     90    to WS-Line-Cnt.
*>
     open     output Print-File.
     perform  aa050-Report-Vacation.
     close    PY-Employee-File.
     if       Page-Counter > zero           *> Don't print a empty report
              close Print-File
              call     "SYSTEM" using Print-Report  *> Landscape
              goback
     end-if.
*>
 aa000-Exit.  Exit section.
*>
 ZZ040-Evaluate-Message      Section.
*>**********************************
*>
*> For PY-PR1 parameter file anfd other using PR-PR1-Status.
*>
     copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
                                        STATUS by PY-PR1-Status.
*>
 ZZ040-Eval-Msg-Exit.
     exit     section.
*>
 aa050-Report-Vacation     section.
*>********************************
*>
*> At this point Emp is opened for input and Print-File for output.
*>
     move     zero to WS-Rec-Cnt.
     subtract 1 from Page-Lines giving WS-Page-Lines.  *> Could be the same ??  <<<<
*>
     initiate Employee-Vacation-Report.
     perform  forever
              read     PY-Employee-File next record
              if       PY-Emp-Status not = "00"   *> EOF
                       exit perform
              end-if
              add      1 to WS-Rec-Cnt
              generate Emp-Detail
     end-perform.
     terminate
              Employee-Vacation-Report.
*>
 aa050-Exit.  exit section.
*>
 zz070-Convert-Date          section.
*>**********************************
*>
*>  Converts date in WSE-Date to UK/USA/Intl date format using current-date
*>*************************************************************************
*> Input:   WSE-Date via CURRENT-DATE
*> output:  WS-Date as uk/US/Inlt date format
*>
*> first create in UK date
     move     WSE-Year  to WS-Year.
     move     WSE-Month to WS-Month.
     move     WSE-Days  to WS-Days.

*>
     if       Date-Form = zero
              move 1 to Date-Form.
*>
     if       Date-UK          *> nothing to do as in UK format
              go to zz070-Exit.
     if       Date-USA                *> Swap month and days
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> Swap to Intl
     move     WSE-Year  to WS-Intl-Year.
     move     WSE-Month to WS-Intl-Month.
     move     WSE-Days  to WS-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
