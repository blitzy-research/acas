       >>source free
*>****************************************************************
*>               Print one 940 Form on plain paper               *
*>                                                               *
*>     This program computes RI - Rhode Island tax at section    *
*>      19 of the report - Should it not be in their State tax   *
*>       table  instead ?                                        *
*>      If so see code at                                        *
*>    RD - "19 Rhode Island Portion of 15c                       *
*>   and   code at arounbd 608 starting with :                   *
*>      if       PY-PR1-Co-State = "RI"                          *
*>                 move     WS-Tot-Taxable-Futa to WS-RI-Tax     *
*>      etc.                                                     *
*>                                                               *
*>   Temp program name may be py210 - coding from print940       *
*>                                                               *
*>    Prograam uses RW - Report Writer.                          *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       print940.
*>**
      Author.           Vincent B Coen FBCS, FIDM, FIDPM, 08/03/2026.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Print Form 940 Report for end of year processing.
*>                      Semi-sourced from Basic code from print940.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.   NONE other than SYSTEM to lpr.
*>**
*>    Functions Used:   NONE.
*>
*>    Files used :
*>                      pypr1.   Params  for PR2 data
*>                      pyded.   Deductions
*>                      pycoh.   Company History.
*>                      pyhis.   Employee History.
*>
*>    Error messages used.
*> System wide:
*>                      SY00.
*> Program specific:
*>                      PY00
*>                      PY
*>**
*> Changes:
*> 08/03/2026 vbc - 1.0.00 Coding starting.
*>                         After testing version will be set to v3.3.
*>                         WARNING: You MUST set the terminal program to be 80
*>                         cols wide and MORE than 27 lines deep and this is to
*>                         allow for the some of the extra lines beyond 24 to
*>                         be used as areas for the warning or error messages
*>                         to be displayed. 26 lines is the minimum.
*>                         This procedure must be applied at all times when
*>                         running Payroll.
*>                         For almost all terminal programs, can be achieved
*>                         by pulling the left and bottom edges of the terminal
*>                         screen with the mouse and holding right button and
*>                         pulling until the correct number is displayed, and
*>                         doing so, one at a time or pulling bottom right
*>                         corner.
*> 11/03/2026 vbc -        Coding Completed.
*>
*>*************************************************************************
*> Copyright Notice.
*> ****************
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
*> holder with your commercial plans and proposals to vbcoen@gmail.com.
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
*> SPECIAL-NAMES.
*>       CRT STATUS IS COB-CRT-STATUS.
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
*>
 input-output            section.
 file-control.
 copy "selpyparam1.cob".
 copy "selpyded.cob".
 copy "selpycoh.cob".
 copy "selpyhis.cob".
*>
 copy "selprint.cob".    *> 132
*>
 data                    division.
*>================================
*>
 file section.
*>
 copy "fdpyparam1.cob".
 copy "fdpyded.cob".
 copy "fdpycoh.cob".
 copy "fdpyhis.cob".
*>
 fd  Print-File
     reports are 940-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "PRINT940 (1.0.00)".  *> First release pre testing. Prog name will be changed.
*>
 copy "print-spool-command.cob".     *> CHECK PRN file for content Landscape mode
*>
*> copy "wsmaps03.cob". *> NEEDED ?
 copy "wsfnctn.cob".  *> NEEDED ?
*>
 copy "Test-Data-Flags.cob".  *> set sw-Testing to zero to stop logging.  *> NEEDED ?
*>
 01  WS-Data.
     03  Menu-Reply          pic x.
     03  PY-PR1-Status       pic xx       value zero.
     03  PY-Coh-Status       pic xx.
     03  PY-Ded-Status       pic xx       value zero.
     03  PY-His-Emp-Status   pic xx       value zero.
*>
     03  WS-Reply            pic x.
     03  WS-Eval-Msg         pic x(25)    value spaces.
     03  WS-Env-Columns      pic 999      value zero.
     03  WS-Env-Lines        pic 999      value zero.
     03  WS-22-Lines         pic 99.
     03  WS-23-Lines         pic 99.
     03  WS-Lines            pic 99.
     03  A                   pic 99       value zero.
     03  B                   pic 99       value zero.
     03  C                   pic 99       value zero.
     03  WS-Page-Lines       binary-char unsigned value 56. *> Narrow reports as system is for Landscape used.
     03  WS-Rec-Cnt          pic 99       value zero.
     03  WS-Page-Cnt         pic 999      value zero.
     03  WS-Line-Cnt         pic 999      value 90.         *> Force heads at start
*>
 01  WS-Process-Flags.
     03  WS-Year-End         pic x        value "N".
     03  WS-End-of-Qtr       pic 9(8).    *> ccyymmdd
     03  WS-Qtr-End redefines WS-End-of-Qtr.
         05  WS-EoQ-Year     pic 9(4).
         05  WS-EoQ-Month    pic 99.
         05  WS-EoQ-Day      pic 99.
     03  WS-Common-Date      pic 9(8).    *> ccyymmdd of To-Day which is Local / default date format.
*>
*> Date variables etc
*>
 01  WS-Accumulator-Fields       value zeros.
     03  WS-Over-6k          pic s9(9)v99   comp-3.
     03  WS-Tot-Renum-Paid   pic s9(9)v99   comp-3.
     03  WS-Pay              pic s9(9)v99   comp-3.
     03  WS-Exempt           pic s9(9)v99   comp-3.
     03  WS-Gross-Pay        pic s9(9)v99   comp-3.
     03  WS-Contrib-at-2-7   pic s9(9)v99   comp-3.
     03  WS-Contrib-at-Rate  pic s9(9)v99   comp-3.
     03  WS-AddL-Credits     pic s9(9)v99   comp-3.
     03  WS-Actual-Contrib   pic s9(9)v99   comp-3.
     03  WS-Tot-Tent-Cred    pic s9(9)v99   comp-3.
     03  WS-Tot-Taxable-Futa pic s9(9)v99   comp-3.
     03  WS-Gross-Fed-Tax    pic s9(9)v99   comp-3.
     03  WS-Maximum-Cred     pic s9(9)v99   comp-3.
     03  WS-Smaller          pic s9(9)v99   comp-3.
     03  WS-RI-Tax           pic s9(9)v99   comp-3.
     03  WS-RI-Cred          pic s9(9)v99   comp-3.
     03  WS-Cred-Allowable   pic s9(9)v99   comp-3.
     03  WS-Net-Fed-Tax      pic s9(9)v99   comp-3.
     03  WS-Tot-Deposited    pic s9(9)v99   comp-3.
     03  WS-Balance-Due      pic s9(9)v99   comp-3.
     03  WS-OverPay          pic s9(9)v99   comp-3.
*>
     03  WS-Rate.
         05  WS-Rate9        pic 99.99.
         05  filler          pic x      value "%".
     03  WS-Max-Rate.
         05  WS-Max-Rate9    pic 99.99.
         05  filler          pic x      value "%".
*>
 01  WS-Test-Date            pic x(10).
 01  WS-Test-YMD             pic 9(8).
 01  WS-PR1-Dating           pic 9(8).
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
*> 01  COB-CRT-Status      pic 9(4)         value zero.   *> NEEDED ?
*>     copy "screenio.cpy".
*>
 copy "wstime.cob".
*>
 01  Error-Messages.   *>   CHANGE FOR PROG
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY002           pic x(31) value "SY002 Note error and hit Return".
     03  SY003           pic x(51) value "SY003 Aborting function - Note error and hit Return".
     03  SY004           pic x(20) value "SY004 Now Hit Return".
     03  SY005           pic x(18) value "SY005 Invalid Date".
     03  SY008           pic x(32) value "SY008 Note message & Hit Return ".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
     03  SY014           pic x(30) value "SY014 Press return to continue".
*>
*> Module General ?
*>
     03  PY011           pic x(36) value "PY011 Re/Write PARAM record Error = ".
     03  PY012           pic x(32) value "PY012 Read PARAM record Error = ".
     03  PY013           pic x(39) value "PY013 See manual for NL accounts needed".
     03  PY014           pic x(29) value "PY014 To quit, use ESCape key".
     03  PY015           pic x(40) value "PY015 F1 for display of current accounts".
     03  PY016           pic x(40) value "PY016 No records to show, return to quit".
     03  PY017           pic x(45) value "PY017 No more records to show, return to quit".
     03  PY018           pic x(31) value "PY018 Write DED record Error = ".
     03  PY019           pic x(30) value "PY019 Read DED record Error = ".
     03  PY020           pic x(33) value "PY020 Rewrite DED record Error = ".
     03  PY021           pic x(30) value "PY021 Read CoH Record Error = ".

     03  PY119           pic x(20) value "PY119 Must be Y or N".
     03  PY120           pic x(38) value "PY120 Do you wish to Continue (Y/N) - ".
*>
*> Module specific
*>   from print940
*>
     03  PY581           pic x(24) value "PY581 PR2 File not found".
     03  PY582           pic x(24) value "PY582 COH File not found".
     03  PY583           pic x(24) value "PY583 DED File not found".
     03  PY584           pic x(45) value "PY584 System has not achieved Year End Status".
     03  PY585           pic x(28) value "PY585 Unable to write to PR2".
     03  PY586           pic x(24) value "PY586 HIS File not found".
*>
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob"   replacing System-Record by WS-System-Record.
 copy "wsnames.cob".
*>
 01  To-Day              pic x(10).   *> In local format nn/nn/yyyy
*>
 Report section.    *> All MAY NEED CHANGING
*>**************
*>
 RD  940-Report
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 5
     Last  Detail WS-Page-Lines.
*>
 01  940-Detail type is detail.
     03  line 3.
         05  col 25 pic x(60)    source PY-PR1-Co-Name.
     03  line 4.
         05  col 25 pic x(32)    source PY-PR1-Co-Address-1.
     03  line 5.
         05  col 25 pic x(32)    source PY-PR1-Co-Address-2.
     03  line 6.
         05  col 25 pic x(32)    source PY-PR1-Co-Address-3.
         05  col 70 pic x(15)    source PY-PR1-Fed-ID.
     03  line 7.
         05  col 25 pic x(32)    source PY-PR1-Co-Address-4.
         05  col 60 pic xx       source PY-PR1-Co-State.
         05  col 63 pic x(10)    source PY-PR1-Co-Zip.
     03  line 10.
         05  col  6     value
             "1          2             3                 4        " &
             "      5           6              7             8              9".
     03  line 10.
         05  col 14     value
             "State ID      Taxable       Experience Rate  Experi"  &
	         "ence Contributions  Contributions   Additional    Contributions".
     03  line 11.
         05  col   1    value
             "   State      Number       Payroll        From       To      Rate       At ".
         05  col  76  pic z9.99            source WS-Max-Rate.
         05  col  81    value "     At Real Rate     Credits       To State".
     05  line + 2.
         05  col   5  pic xx               source PY-PR1-Co-State.
         05  col   9  pic x(15)            source PY-PR1-State-ID.
         05  col  25  pic zzz,zzz,zz9.99   source WS-Gross-Pay.
         05  col  40                       value "01/01/".
         05  col  46  pic 9(4)             source WSE-Year.
         05  col  50                       value "12/31/".
         05  col  56  pic 9(4)             source WSE-Year.
         05  col  62  pic x(6)             source WS-Rate.
         05  col  70  pic zzz,zzz,zz9.99   source WS-Contrib-at-2-7.
         05  col  85  pic zzz,zzz,zz9.99   source WS-Contrib-at-Rate.
         05  col 100  pic zzz,zzz,zz9.99   source WS-AddL-Credits.
         05  col 115  pic zzz,zzz,zz9.99   source WS-Actual-Contrib.
*>
     03  line + 3.
         05  col  11                       value "Totals".
         05  col  25  pic zzz,zzz,zz9.99   source WS-Gross-Pay.
         05  col 100  pic zzz,zzz,zz9.99   source WS-AddL-Credits.
         05  col 115  pic zzz,zzz,zz9.99   source WS-Actual-Contrib.
*>
     03  line + 3.
         05  col  55                       value "10 Total Tentative Credit (Column 8 Plus Column 9):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Tot-Tent-Cred.
     03  line + 1.
         05  col  55                       value "11 Total Remuneration:".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Tot-Renum-Paid.
     03  line + 3.
         05  col  25                       value "14b Total Exempt Remuneration:".
         05  col  90  pic zzz,zzz,zz9.99   source WS-Exempt.
     03  line + 1.
         05  col  25                       value "15c Total Taxable Futa Wages (Subtract 14b From Line 11):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Tot-Taxable-Futa.
     03  line + 1.
         05  col  25                       value "16 Gross Federal Tax (15c X .034):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Gross-Fed-Tax.
     03  line + 1.
         05  col  25                       value "17 Maximum Credit (15c X .027):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Maximum-Cred.
     03  line + 1.
         05  col  25                       value "18 Smaller of Lines 10 and 17):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Smaller.
     03  line + 1.
         05  col  25                       value "19 Rhode Island Portion of 15c:".
         05  col 115  pic zzz,zzz,zz9.99   source WS-RI-Cred.
     03  line + 1.
         05  col  25                       value "20 Credit Allowable (Subtract Line 19 From Line 18):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Cred-Allowable.
     03  line + 1.
         05  col  25                       value "21 Net Federal Tax (Subtract Line 20 From Line 16):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Net-Fed-Tax.
     03  line + 3.
         05  col  25                       value "Federal Tax Deposits".
     03  line + 1.
         05  col  15                       value "Quarter     Liability     Date of     Amount of".
     03  line + 1.
         05  col  27                       value "By Period     Deposit      Deposit".
     03  line + 1.
         05  col  17                       value "First".
         05  col  25  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (1).
         05  col  40                       value "03/31/".
         05  col  46  pic 9(4)             source WSE-Year.
         05  col  51  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (1).
     03  line + 1.
         05  col  16                       value "Second".
         05  col  25  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (2).
         05  col  40                       value "06/30/".
         05  col  46  pic 9(4)             source WSE-Year.
         05  col  51  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (2).
     03  line + 1.
         05  col  17                       value "Third".
         05  col  25  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (3).
         05  col  40                       value "09/30/".
         05  col  46  pic 9(4)             source WSE-Year.
         05  col  51  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (3).
     03  line + 1.
         05  col  16                       value "Fourth".
         05  col  25  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (4).
         05  col  40                       value "12/31/".
         05  col  46  pic 9(4)             source WSE-Year.
         05  col  51  pic zzz,zzz,zz9.99   source Coh-Q-Co-Futa-Liab (4).
     03  line + 2.
         05  col  25                       value "22 Total Federal Taxes Deposited:".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Tot-Deposited.
     03  line + 1.
         05  col  25                       value "23 Balance Due (Subtract Line 22 From Line 21):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-Balance-Due.
     03  line + 1.
         05  col  25                       value "24 Overpayment (Subtract Line 21 From Line 22):".
         05  col 115  pic zzz,zzz,zz9.99   source WS-OverPay.
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
     move     Current-Date to WSE-Date-block.
     move     WSE-Date-9  to WS-Test-YMD.
     move     Print-Spool-Name to PSN.  *> set ACAS prt spool for o/p
*>
*> Create common-date in ccyymmdd form.
*>   assuming To-Day is in Locale format ie USA mm.dd/ccyy
*>
     move     To-Day (7:4)      to WS-Common-Date (1:4).
     if       PY-PR1-Date-Format = 2
              move To-Day (1:2) to WS-Common-Date (5:2)  *> mm
              move To-Day (4:2) to WS-Common-Date (7:2)  *> dd
     else
              move To-Day (4:2) to WS-Common-Date (5:2)  *> mm
              move To-Day (1:2) to WS-Common-Date (7:2). *> dd
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
*> Set up error message areas on screen anyway
*>
     subtract 2 from WS-Env-Lines giving WS-22-Lines.
     subtract 1 from WS-Env-Lines giving WS-23-Lines.
     move     WS-Env-Lines to WS-Lines.
*>
*> Open all files if any missing Abort.
*> For all files other than His-Emp read only record.
*>
     move     1 to RRN.
     open     i-o      PY-Param1-File.
     if       PY-PR1-Status not = "00"      *> Does not exist yet so lets create it & write rec
              close    PY-Param1-File
              display  PY581 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              move     16 to WS-Term-Code
              goback   returning 1.
*>
     read     PY-Param1-File key RRN.
     if       PY-PR1-Status not = "00"
              perform  ZZ040-Evaluate-Message
              display  PY012         at line WS-23-Lines col 1 with erase eos
              display  PY-PR1-Status at line WS-23-Lines col 33
              display  WS-Eval-Msg   at line WS-23-Lines col 36
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
              move     16 to WS-Term-Code
              goback   returning 1.
*>
*>  Check if ok to run  - other tests remarked out in basic code
*>
     move     "Y" to WS-Year-End.
*>
     if       PY-PR2-Last-Q-Ended = 4
              move     WS-Test-YMD  to WS-End-of-Qtr
              if       WS-EoQ-Month = 12
                       add      1 to WS-EoQ-Year  *> incr year for new yr
              end-if
              move     0331     to WS-End-of-Qtr (5:4)
     else
              move     WS-Common-Date to WS-End-of-Qtr.
*>
 display "End of Qtr now " WS-End-of-Qtr.   *> FOR TESTING ONLY
*>
*> Extra checks NOT RUN.  [ bypassed in basic code ]
*>
 *>    perform  zz100-Extra-Year-End-Checks. NOT PRESENT in Code Base.
*>
     open     input   PY-Comp-Hist-File.
     if       PY-Coh-Status not = zeros
              display  PY582 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
              move     16 to WS-Term-Code
              goback   returning 2.
     move     1 to RRN.
*>
     read     PY-Comp-Hist-File key RRN.
     if       PY-Coh-Status not = zeros
              display  PY021 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
              move     16 to WS-Term-Code
              goback   returning 2.
     close    PY-Comp-Hist-File.    *> Data record in FD area.
*>
     open     input    PY-System-Deduction-File.
     if       PY-Ded-Status not = zeros
              display  PY583 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
                       PY-System-Deduction-File
              move     16 to WS-Term-Code
              goback   returning 3.
*>
     move     1 to RRN.
     read     PY-System-Deduction-File key RRN.
     if       PY-Ded-Status not = zeros
              display  PY019 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
                       PY-System-Deduction-File
              move     16 to WS-Term-Code
              goback   returning 4.
     close    PY-System-Deduction-File.  *> Data record in FD area
*>
     open     input    PY-History-File.
     if       PY-His-Emp-Status not = zeros
              display  PY586 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
                       PY-System-Deduction-File
                       PY-History-File
              move     16 to WS-Term-Code
              goback   returning 4.
*>
*> Will be Reading Emp History in main body
*>
     initialise
              WS-Accumulator-Fields.
     move     zeros to WS-Tot-Renum-Paid
                       WS-Over-6k.
*>
     perform  forever
              read     PY-History-File next record at end
                       close    PY-History-File
                       exit     perform
              end-read
*> Acccumulate
              add      His-YTD-Income-Taxable
                       His-YTD-Other-Taxable
                       His-YTD-Other-NonTaxable
                       His-YTD-Tips  giving WS-Pay
              add      WS-Pay   to  WS-Tot-Renum-Paid
              if       WS-Pay > Ded-Co-Futa-Limit
                       compute   WS-Over-6k = WS-Pay - Ded-Co-Futa-Limit
              end-if
*> Calulations
              add      WS-Over-6k
                       Coh-YTD-Other-NonTaxable giving WS-Exempt
              move     Ded-Co-SUI-Rate         to WS-Rate9
              move     Ded-Co-Futa-Max-Credit  to WS-Max-Rate9
              add      Coh-YTD-Income-Taxable
                       Coh-YTD-Other-Taxable
                       Coh-YTD-Tips
                                                giving WS-Gross-Pay
              multiply WS-Gross-Pay by Ded-Co-Futa-Max-Credit
                                                giving WS-Contrib-at-2-7
              multiply WS-Gross-Pay by Ded-Co-SUI-Rate
                                                giving WS-Contrib-at-Rate
              compute  WS-AddL-Credits = WS-Contrib-at-2-7 - WS-Contrib-at-Rate
              if       WS-AddL-Credits negative
                       move     zero to WS-AddL-Credits
              end-if
              move     WS-Contrib-at-Rate to WS-Actual-Contrib   *> should equal coh.ytd.co.sui.liab
              compute  WS-Tot-Tent-Cred =  WS-AddL-Credits + WS-Actual-Contrib
              compute  WS-Tot-Taxable-Futa = WS-Tot-Renum-Paid - WS-Exempt
              compute  WS-Gross-Fed-Tax = WS-Tot-Taxable-Futa * Ded-Co-Futa-Rate
              compute  WS-Maximum-Cred  = WS-Tot-Taxable-Futa * Ded-Co-Futa-Max-Credit
              if       WS-Tot-Tent-Cred < WS-Maximum-Cred
                       move     WS-Tot-Tent-Cred to  WS-Smaller
              else
                       move     WS-Maximum-Cred  to  WS-Smaller
              end-if
*> Not sure about this as should be processed via RI State tax.
              if       PY-PR1-Co-State = "RI"                     *> Rhode Island,  what is this?,  still valid ?
                       move     WS-Tot-Taxable-Futa to WS-RI-Tax
                       multiply WS-RI-Tax by 0.375 giving WS-RI-Cred   *> RI Tax at 3.75%  IS this valid ?
              else
                       move     zero to WS-RI-Tax
                                        WS-RI-Cred
              end-if
              compute  WS-Cred-Allowable = WS-Smaller - WS-RI-Cred
              compute  WS-Net-Fed-Tax    = WS-Gross-Fed-Tax - WS-Cred-Allowable
              move     zero to WS-Tot-Deposited
                       A
              perform  4 times
                       add      1 to A
                       add      Coh-Q-Co-Futa-Liab (A) to WS-Tot-Deposited
              end-perform
              compute  WS-Balance-Due = WS-Net-Fed-Tax - WS-Tot-Deposited
              if       WS-Balance-Due negative
                       multiply WS-Balance-Due by -1 giving WS-Overpay
                       move     zero to WS-Balance-Due
              end-if
     end-perform.
*>
*>  Now print the 940
*>
     open     output Print-File.
     initiate 940-Report.
     generate 940-Detail.
     terminate
              940-Report.
*>
     close    Print-File.
     call     "SYSTEM" using Print-Report.  *> Landscape
*>
*> Finish off
*>
     if       WS-Year-End not = "Y"   *> from basic code and always set
              close    PY-Param1-File
              goback.
*>
     move     "Y" to PY-PR2-940-Printed.
     move     1 to RRN.
     rewrite  PY-Param1-Record.
     if       PY-PR1-Status not = zeros
              perform  ZZ040-Evaluate-Message
              display  PY011         at line WS-23-Lines col 1 with erase eos
              display  PY-PR1-Status at line WS-23-Lines col 37
              display  WS-Eval-Msg   at line WS-23-Lines col 40
              display  SY002         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
              move     16 to WS-Term-Code
              goback   returning 11.
*>
     close    PY-Param1-File.
     goback.
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
