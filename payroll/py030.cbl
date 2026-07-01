       >>source free
*>****************************************************************
*>                  Hours Entry Proof Report                     *
*>                                                               *
*>            Uses RW (Report writer for prints)                 +
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       py030.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 07/04/2026.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Employee History Reporting.
*>                       This program uses RW (Report Writer) - I hope, as
*>                         very rusty using it.
*>
*>                      Semi-sourced from Basic code from empprint.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.   SYSTEM.
*>**
*>    Functions Used:
*>                      CURRENT-DATE.
*>                      TRIM.
*>    Files used :
*>                      pypr1.   Params
*>                      pyemp.   Employee Master.
*>                      pyhrs.   Hours transactions.
*>
*>    Error messages used.   CHANGES NEEDED <<<<<<<<<<
*> System wide:
*>                      SY001 - 5, 8, 10 - 14.  ??
*> Program specific:
*>                      PY001 - 7. ??
*>                      PY101 - 126. ??
*>                      PY 801 - 809 ??
*>                      PY 675 - 681 ??
*>**
*> Changes:
*> 07/04/2026 vbc - 1.0.00 Created - Started coding.
*>
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
 copy "selpyhrs.cob".
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
 copy "fdpyhrs.cob".
*>
 fd  Print-File
     reports are Employee-Hours-Proof-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "py030 (1.0.00)".  *> First release pre testing.
*>
*>  This will print 1 copy to CUPS print spool specified on line 3 override via setup at SOJ
*>
 copy "print-spool-command.cob".     *> CHECK PRN file for content Landscape mode  -  IS IT ?
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "Test-Data-Flags.cob".           *> set sw-Testing to zero to stop logging.
*>                                        ABOVE SHOULD BE OFF
*> REMARK OUT ANY IN USE
*>
 01  WS-Data.
     03  Menu-Reply          pic x.
     03  PY-PR1-Status       pic xx.
     03  PY-Emp-Status       pic xx.
     03  PY-Hrs-Status       pic xx.
*>
     03  WS-Reply            pic x.
     03  WS-Menu-Option      pic 99       value zero.
*>
     03  WS-Eval-Msg         pic x(25)    value spaces.
     03  WS-Env-Columns      pic 999      value zero.
     03  WS-Env-Lines        pic 999      value zero.
     03  WS-22-Lines         pic 99.
     03  WS-23-Lines         pic 99.
     03  WS-Lines            pic 99.
     03  WS-Page-Lines       binary-char unsigned value 56.   *> Narrow reports as system is for Landscape used.
     03  WS-Rec-Cnt          pic 99       value zero.
     03  WS-Page-Cnt         pic 999      value zero.
     03  WS-Line-Cnt         pic 999      value 90.   *> Force heads at start
*>
     03  WS-Name-Suffix      pic x(10).   *> = "(SALARIED)" or "(HOURLY)" -> after emp rev name
     03  WS-Desc             pic x(35).
     03  WS-Name-and-Suffix  pic x(43).
     03  WS-Eff-Date         pic x(10).
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
*> 01  WS-PR1-Dating           pic 9(8).
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
 01  WS-ED-Description-Table.
     03  filler          pic x(17) value "00Rate 0".
     03  filler          pic x(17) value "01Regular Pay".
     03  filler          pic x(17) value "02Overtime Pay".
     03  filler          pic x(17) value "03Special OT Pay".
     03  filler          pic x(17) value "04Commission".
     03  filler          pic x(17) value "05Vacation Taken".
     03  filler          pic x(17) value "06Sick Lve Taken".
     03  filler          pic x(17) value "07Comp Time Taken".
     03  filler          pic x(17) value "08Comp Time Earnd".
     03  filler          pic x(17) value "09Bonus".
     03  filler          pic x(17) value "10Tips Collected".
     03  filler          pic x(17) value "11Advance".
     03  filler          pic x(17) value "12Sick Pay".
     03  filler          pic x(17) value "13Vacation Pay".
     03  filler          pic x(17) value "14Other Excld Pay".
     03  filler          pic x(17) value "15Expense Reimb".
     03  filler          pic x(17) value "16Eic".
     03  filler          pic x(17) value "17Other Pay".
     03  filler          pic x(17) value "18Tips Reported".
     03  filler          pic x(17) value "19".
     03  filler          pic x(17) value "20Fwt".
     03  filler          pic x(17) value "21Swt".
     03  filler          pic x(17) value "22Lwt".
     03  filler          pic x(17) value "23Fica".
     03  filler          pic x(17) value "24Sdi".
     03  filler          pic x(17) value "25".
     03  filler          pic x(17) value "26".
     03  filler          pic x(17) value "27Advance Repay".
     03  filler          pic x(17) value "28Fwt Add-on".
     03  filler          pic x(17) value "29Swt Add-on".
     03  filler          pic x(17) value "30Lwt Add-on".
     03  filler          pic x(17) value "31Fica Add-on".
     03  filler          pic x(17) value "32".
     03  filler          pic x(17) value "33Sys1".
     03  filler          pic x(17) value "34Sys2".
     03  filler          pic x(17) value "35Sys3".
     03  filler          pic x(17) value "36Sys4".
     03  filler          pic x(17) value "37Sys5".
     03  filler          pic x(17) value "38Emp1".
     03  filler          pic x(17) value "39Emp2".
     03  filler          pic x(17) value "40Emp3".
     03  filler          pic x(17) value "41".
     03  filler          pic x(17) value "42Company Fica".
     03  filler          pic x(17) value "43Company Futa".
     03  filler          pic x(17) value "44Company Sui".
     03  filler          pic x(17) value "45".
     03  filler          pic x(17) value "46Other Co Cost".
     03  filler          pic x(17) value "47".
     03  filler          pic x(17) value "48".
     03  filler          pic x(17) value "49".
     03  filler          pic x(17) value "50Other Ded".        *>    Need 4 more for other and MCare
     03  filler          pic x(17) value "51Mcare".
     03  filler          pic x(17) value "52".
     03  filler          pic x(17) value "53".
     03  filler          pic x(17) value "54".                 *>      00 - 54  = 55 entries
 01  filler           redefines WS-ED-Description-Table.
     03  WS-ED-Desc-Table           occurs 55.
         05  WS-ED-No      pic 99.
         05  WS-ED-Desc    pic x(15).
*>
 01  Error-Messages.   *> ANY NEEDED ???
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
*>     03  SY002           pic x(31) value "SY002 Note error and hit Return".
*>     03  SY003           pic x(51) value "SY003 Aborting function - Note error and hit Return".
 *>    03  SY004           pic x(20) value "SY004 Now Hit Return".
 *>    03  SY005           pic x(18) value "SY005 Invalid Date".
 *>    03  SY008           pic x(32) value "SY008 Note message & Hit Return ".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*>     03  SY014           pic x(30) value "SY014 Press return to continue".
*>
*> Module General
*>
     03  PY001           pic x(45) value "PY001 Payroll Parameter file does not exist -".
     03  PY002           pic x(32) value "PY002 Read PARAM record Error = ".
 *>    03  PY004           pic x(29) value "PY004 To quit, use ESCape key".
*>
*> Module specific    <<<< REMOVE UNUSED
*>
     03  PY806           pic x(29) value "PY806 Employee File not Found".
     03  PY808           pic x(24) value "PY808 Hrs File not Found".
     03  PY810           pic x(31) value "PY810 Error rewrite Hrs File - ".
     03  PY811           pic x(38) value "PY811 Unexpected Error reading Emp - ".
*>
 01  Error-Code          pic 999.
*>
     copy "wspyhrs.cob"   replacing LEADING ==PY-Pay== by ==WS-Pay==
                                    LEADING ==Hrs==    by ==WS-Hrs==.
*> *>
 01  COB-CRT-Status      pic 9(4)         value zero.
     copy "screenio.cpy".
*>
 copy "wstime.cob".
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob"   replacing System-Record by WS-System-Record.
 copy "wsnames.cob".
*>
 01  To-Day              pic x(10).
*>
 Report section.    *> All NEEDS CHANGING
*>**************
*>
 RD  Employee-Hours-Proof-Report
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 5
     Last  Detail WS-Page-Lines.
*>
*> Print layouts to 132 cols Landscape
*>
 01  Hours-Proof-Heads Type is Page Heading.
     03  line 1.
         05  col  50  pic x(40)      source UserA.
         05  col 110  pic x(10)      source WS-Date.  *> IS this correct format ?  Check report
         05  col 122  pic x(8)       source WSD-Time.
     03  line 2.
         05  col  1   pic x(17)      source Prog-Name.
         05  col 51   pic x(19)      value "ACAS Payroll System".
         05  col 124  pic x(5)       value "Page ".
         05  col 129  pic zz9        source Page-Counter.
     03  Line 3.
         05  col 53   pic x(53)      value "Transaction Hours Report".
     03  line 5.
         05  col 15   pic x(9)       value "Batch No:".
         05  col 25   pic zz9        source WS-Hrs-Batch-No.
     03  line 6.
         05  col 15   pic x(10)      value "Proof No:".
         05  col 25   pic zz9        source WS-Hrs-Proof-No.
     03  line 8.
         05  col  6                  value "Employee".
         05  col 59                  value "Effective".
         05  col 80                  value "Transaction".
     03  line 9.
         05  col  7                  value "Number".
         05  col 19                  value "Employee Name".
         05  col 62                  value "Date".
         05  col 76                  value "Units".
         05  col 84                  value "Code".
         05  col 90                  value "Description".
*>
 01  Hours-Proof-Detail type is detail.
     03  line + 1.
         05  col  7   pic 9(7)       source Hrs-Emp-No.
         05  col 17   pic x(32)      source WS-Name-and-Suffix.
         05  col 60   pic x(10)      source WS-Date.
         05  col 71   pic zz,zz9.99  source Hrs-Units.
         05  col 85   pic z9         source Hrs-Trans-Code.
         05  col 90   pic x(35)      source WS-Desc.
*>
 01  Hours-Proof-Foot Type Report Footing.
     03  line + 2.
         05  col 5      pic x(23)    value "Total Records printed: ".
         05  col 29     pic zzz9     source WS-Rec-Cnt.
*>
 01  type control Footing Final line plus 2.   *> ?? Needed ??

     03  col 1           pic x(25)         value "Total - Account Records :".
     03  col 26          pic zzz9          source WS-Rec-Cnt.
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
*> Check for files and Quit if any are missing or there is no data for Emp or History etc.
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
              goback   returning 1
     end-if.
*>
     close    PY-Param1-File.             *> Record still in WS area
     move     zero  to  Return-Code.
*>
     open     input    PY-Employee-File.
     if       PY-Emp-Status not = "00"
              display  PY806         at line WS-23-Lines col 1 with erase eos
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
                       PY-Employee-File
              move     16 to WS-Term-Code
              goback   returning 2
     end-if.
     open     input    PY-Pay-Transactions-File.
     if       PY-Hrs-Status not = "00"
              if       PY-Hrs-Status not = "00"
                       move     PY-Hrs-Status to PY-PR1-Status
                       perform  ZZ040-Evaluate-Message
                       display  PY808         at line WS-23-Lines col 1 with erase eos
                       display  PY-PR1-Status at line WS-23-Lines col 26
                       display  WS-Eval-Msg   at line WS-23-Lines col 29
                       display  SY001         at line WS-Lines    col 1
                       accept   WS-Reply      at line WS-Lines    col 48 AUTO
                       close    PY-Param1-File
                                PY-Employee-File
                                PY-Pay-Transactions-File
                       move     16 to WS-Term-Code
                       goback   returning 3
              end-if
     end-if.
     close        PY-Pay-Transactions-File.
     open     i-o PY-Pay-Transactions-File.  *> needed to update header rec
*>
     move     zeros to WS-Page-Cnt.
     move     90    to WS-Line-Cnt.
*> Read Trans header
     move     zero to WS-Hrs-Head-Key.
     read     PY-Pay-Transactions-File into WS-Pay-Header-Record
              key WS-Hrs-Head-Key.
     open     output Print-File.
     perform  aa050-Report.
     perform  aa000-Fin.
*>
     if       Page-Counter > zero           *> Don't print a empty report
              close Print-File
              call     "SYSTEM" using Print-Report.  *> Landscape
              goback.
*>
 aa000-Fin.
     move     "Y"  to WS-Hrs-Proofed.
     add      1    to WS-Hrs-Proof-No.
     move     zero to WS-Hrs-Head-Key.
     rewrite  PY-Pay-Header-Record from WS-Pay-Header-Record.
     if       PY-Hrs-Status not = "00"
              display  PY810                at line WS-22-Lines col 1
                                               foreground-color 6 erase eos
              display  PY-Hrs-Status        at line WS-22-Lines col 32
              move     PY-Hrs-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  WS-Eval-Msg          at line WS-22-Lines col 35
              display  SY001                at line WS-Lines col 1
              accept   WS-Reply             at line WS-Lines col 48.
*>
     close    PY-Param1-File
              PY-Employee-File
              PY-Pay-Transactions-File.
*>
 aa000-Exit.  Exit section.
*>
 aa050-Report       section.
*>*************************
*>
*> At this point Emp is opened for input and Print-File for output.
*>  treat Hrs recs as primary
*>
     move     zero to WS-Rec-Cnt.
     subtract 1 from Page-Lines giving WS-Page-Lines.  *> Could be the same ??  <<<<
*>
     initiate Employee-Hours-Proof-Report.
     perform  forever
              read     PY-Pay-Transactions-File next record
              if       PY-Hrs-Status not = "00"    *> assuming EOF
                       exit perform
              end-if
              add      1 to WS-Rec-Cnt
              if       Hrs-Emp-No not = Emp-No
                       move     Hrs-Emp-No to Emp-No
                       read     PY-Employee-File key Emp-No
                       if       PY-Emp-Status not = "00"   *> EOF
                                display  PY811 at line WS-23-Lines col 1 erase eos
                                display  PY-Emp-Status at line WS-23-Lines col 39
                                move     PY-Emp-Status to PY-PR1-Status
                                perform  ZZ040-Evaluate-Message
                                display  WS-Eval-Msg          at line WS-23-Lines col 42
                                display  SY001                at line WS-Lines col 1
                                accept   WS-Reply             at line WS-Lines col 48
                                exit perform
                       end-if
              end-if
              if       Emp-HS-Type = "S"
                       move     "(Salaried)" to WS-Name-Suffix
              else
                       move     "(Hourly)"   to WS-Name-Suffix
              end-if
              move     spaces  to WS-Desc
              if       Hrs-Trans-Code = zero
                       string  TRIM (WS-ED-Desc (1))
                               " and "
                               TRIM (WS-ED-Desc (2))   into WS-Desc
              else
                       move WS-ED-Desc (Hrs-Trans-Code) to WS-Desc
              end-if
              move     spaces to WS-Name-and-Suffix
              string   TRIM (Emp-Search-Name)
                       TRIM (WS-Name-Suffix)    into WS-Name-and-Suffix
              end-string
              move     Hrs-Effective-Date  to WS-Temp-Date9
              perform  zz050-Convert-Date
              generate Employee-Hours-Proof-Report
     end-perform.
     terminate
              Employee-Hours-Proof-Report.
*>
 aa050-Exit.  exit section.
*>
 ZZ040-Evaluate-Message      Section.
*>**********************************
*>
*> For PY-PR1 parameter file anfd other using PR-PR1-Status.
*>
     copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
                                        STATUS by PY-PR1-Status.
*>
     exit     section.
*>
 zz050-Convert-Date          section.
*>**********************************
*>
*> Input:  WS-Temp-Date9.
*> Output: WS-Date as 99/99/9999
*>
     move     "99/99/9999" to WS-Date.
     if       PY-PR1-Date-Format = 2    *> USA mm/dd/ccyy
              string   WS-Temp-Month "/" WS-Temp-Days "/" WS-Temp-Year
                       into WS-Date
     else
              string   WS-Temp-Days "/" WS-Temp-Month "/" WS-Temp-Year
                       into WS-Date.
*>
     exit     section.
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
