       >>source free
*>****************************************************************
*>               Print W-2 Forms on plain paper for              *
*>                 selected employees.                           *
*>                                                               *
*>   Temp program name may be py220 - coding from printw2        *
*>                                                               *
*>    Prograam uses RW - Report Writer.                          *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       printw2.
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
*> 12/03/2026 vbc - 1.0.00 Coding starting.
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
 copy "selpyemp.cob".
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
 copy "fdpyemp.cob".
 copy "fdpyhis.cob".
*>
 fd  Print-File
     report is w2-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "PRINTw2 (1.0.00)".  *> First release pre testing. Prog name will be changed.
*>
 copy "print-spool-command-p.cob".     *> CHECK PRN file for content Portrait mode
*>
*> copy "wsmaps03.cob". *> NEEDED ?
 copy "wsfnctn.cob".  *> NEEDED ?
*>
 copy "Test-Data-Flags.cob".  *> set sw-Testing to zero to stop logging.  *> NEEDED ?
*>
 01  WS-Data.
     03  Menu-Reply          pic x.
     03  PY-PR1-Status       pic xx       value zero.
     03  PY-Emp-Status       pic xx       value zero.
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
     03  WS-RS-From-Emp      pic 9(7)     value zeros.
     03  WS-RS-To-Emp        pic 9(7)     value zeros.
     03  WS-RS-Single-Emp    pic 9(7)     value zero.    *> fld.single.emp% = 4	:lit.single.emp%  = 27
     03  WS-RS-Term-Emp      pic x        value space.   *> fld.term.emp%	= 3	:lit.term.emp%	  = 25
     03  WS-RS-Report-Type   pic x        value space.        *> Selected option 1 - 4
     03  WS-RS-State-Local   pic x        value "N".          *> print State & local amts  fld.print.local% = 6
     03  WS-RS-Emp-Forms-Cnt pic 99       value zero.         *> @ forms per emplyee (# copies)
 *>    03  WS-RS-Start-Prt-Col pic 99       value 1.            *> Default 1 = start col 1.
 *>    03  WS-RS-No-Lines-Between-Forms
 *>                            pic 99       value zero.         *> standard FF if zero.
     03  WS-RS-Prt-Test-Form pic x        value "N".          *> Print a test form for paper alignment (if matrix prt) - fld.test.form%	= 10
     03  WS-All-Emp          pic x        value "N".          *> set to "Y" if ALL employees reported on via start up setting & menu.
*>
*> RW cannot handle doing this
*>
*> 01  WS-Line-Positioning.
*>     03  WS-Disp             pic 99       value 5.    *> Default 5   OR IS IT as against 0 ?
*>     03  WS-Col1             pic 99       value 4.  *> + WS-Disp. *>.   *> NEED TO SET THESE AFTER acxepting Menu screen <<<<<<
*>     03  WS-Col2             pic 99       value 21. *> + WS-Disp.
*>     03  WS-Col3             pic 99       value 34. *> + WS-Disp.
*>     03  WS-Col4             pic 99       value 49. *> + WS-Disp.
*>     03  WS-Col5             pic 99       value 64. *> + WS-Disp.

*> REMINDER
*> col1% = disp% + 4
*> col2% = disp% + 21
*> col3% = disp% + 34
*> col4% = disp% + 49
*> col5% = disp% + 64

*>
 01  WS-Process-Flags.
     03  WS-Test-Form        pic x       value "N".
     03  WS-Pnt-Local-Amount pic x       value "N".  *> Print state and Local amounts?
     03  WS-Forms-Per-Emp    pic 9       value 1.    *> Default.
     03  WS-Printed-Per-Emp  pic 99      value zero. *> Cnt printed so far   NOT USED
     03  WS-Lines-2-Next-Frm pic 99      value 99.   *> Default Not needed for non matrix printers set as 99 to ignore
*>
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
     03  WS-Sub-EIC          pic s9(9)v99   comp-3.
     03  WS-Sub-FWT          pic s9(9)v99   comp-3.
     03  WS-Sub-FICA         pic s9(9)v99   comp-3.
     03  WS-Sub-FICA-Gross   pic s9(9)v99   comp-3.
     03  WS-Sub-Tips         pic s9(9)v99   comp-3.
     03  WS-Sub-SWT          pic s9(9)v99   comp-3.
     03  WS-Sub-LWT          pic s9(9)v99   comp-3.
     03  WS-Sub-MCARE        pic s9(9)v99   comp-3.
     03  WS-Sub-Gross        pic s9(9)v99   comp-3.
     03  WS-Sub-Totals       pic s9(9)v99   comp-3.
*>
*>
 01  WS-Emp-Temp-Fields-for-RW.
     03  Tmp-his-ytd-gross   pic s9(9)v99   comp-3.    *> Temp field not in the HIS file record
     03  Tmp-his-ytd-fica-gross
                             pic s9(9)v99   comp-3.    *> Temp field not in the HIS file record
*>
*> MORE ?
     03  WS-Emp-SSN          pic 999/99/9999.
     03  WS-Emp-SSN-X.
         05  filler          pic 999.
         05  WS-Emp-Slash1   pic x.    *> Needs to have '-' to sl 1 & 2 pre printing.
         05  filler          pic 99.
         05  WS-Emp-Slash2   pic x.
         05  filler          pic 9(4).
*>
         03  WS-Emp-Rev-Name                 value spaces.  *> frm Emp-Name
             05  WS-Emp-First-Nm pic x(16).
             05  WS-Emp-Surname  pic x(16).
             05  WS-Emp-Sufx     pic xx.
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
 01  COB-CRT-Status      pic 9(4)         value zero.   *> NEEDED ?
     copy "screenio.cpy".
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
     03  SY015           pic x(20) value "SY015 Must be Y or N".
     03  SY016           pic x(38) value "SY016 Do you wish to Continue (Y/N) - ".
*>
*> Module General ?  ANY NEEDED
*>
     03  PY011           pic x(36) value "PY011 Re/Write PARAM record Error = ".
     03  PY012           pic x(32) value "PY012 Read PARAM record Error = ".
     03  PY014           pic x(29) value "PY014 To quit, use ESCape key".

*>
*> Module specific
*>   from printw2
*>
     03  PY621           pic x(44) value "PY621 System has not achieved Year-End state".
     03  PY622           pic x(29) value "PY622 Employee File not found".
     03  PY623           pic x(37) value "PY623 Unexpected EOF on Employee File".
     03  PY624           pic x(28) value "PY624 History File not found".
     03  PY625           pic x(36) value "PY625 Unexpected eof on History File".
     03  PY626           pic x(24) value "PY626 PR1 File not found".
     03  PY627           pic x(33) value "PY627 Unable to write to PR1 File".
     03  PY628           pic x(22) value "PY628 Invalid response".
     03  PY629           pic x(18) value "PY629 Y or NO Only".
 *>    03  PY630           pic x(26) value "PY630 Numeric integer Only".
 *>    03  PY631           pic x(25) value "PY631 Invalid check digit".
     03  PY632           pic x(30) value "PY632 Employee number too high".
     03  PY633           pic x(56) value "PY633 Starting employee number cannot be > ending number".
     03  PY634           pic x(18) value "PY634 Out of range".   *> 1 thru 50
     03  PY635           pic x(51) value "PY635 There are no Terminated employees in the File".
     03  PY636           pic x(35) value "PY636 Error Reading History File - ".
     03  PY637           pic x(36) value "PY637 Error Reading Employee File - ".
     03  PY638           pic x(53) value "PY638 From Employee number cannot be > than To number".
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
*>*************
*>
 RD  W2-Report
     control      Final
     Page Limit   WS-Page-Lines
 *>    Heading      1
     First Detail 7
     Last  Detail WS-Page-Lines.
*>
*> WARNING: Line # and Col #  can change from year to year for all fields
*>  and this section may well need changes when the new W-2 form becomes available
*>
*>  Line offset based on above First Detail number and is always subject to
*>  testing - i.e., running a test print.
*>
*>  Therefore these layouts may well need changes and the program recompiled to
*>  match up with any new W-2 forms
*>
*>  ONLY applies when printing on to pre-printed stationary
*>
*> 01  W2-Detail type is detail.    *> As per W-2 form for 2026.---  REPEAT generate WS-RS-Emp-Forms-Cnt TIMES
*>                                   CURRENTLY REMARKED OUT AS USING one from cbasic 1980-ish
*>                                   in order to get data sources etc.
*>     03  line 1.
*>         05  col  20  pic x(11)        source WS-Emp-SSN-X.   *> pre moves first
*>     03  line 3.
*>         05  col   4  pic pic x(15)    source PY-PR1-Fed-ID.
*>         05  col  43  pic zzz,zz9.99    *> SUM His-YTD-Income-Taxable   His-YTD-Other-Taxable
*>                                               His-YTD-Other-NonTaxable His-YTD-Tips.   *> sub.gross
*>         05  col  59  pic zzz,zz9.99   source His-YTD-FWT.
*>     03  line 5.
*>         05  col   4  pic x(32)        source PY-PR1-Trade-Name.
*>         05  col  43  pic zzz,zz9.99   source ss wages
*>         05  col  59  pic zzz,zz9.99   source ss tax withheld
*>     03  line 6.
*>         05  col   4  pic x(32)        source PY-PR1-Co-Address-1.
*>     03  line 7.
*>         05  col   4  pic x(32)        source PY-PR1-Co-Address-2.
*>         05  col  43  pic zzz,zz9.99   source mcare wages & tips
*>         05  col  59  pic zzz,zz9.99   source His-YTD-MCare.
*>     03  line 8.
*>         05  col   4  pic x(32)        source PY-PR1-Co-Address-3.
*>     03  line 9.
*>         05  col   4  pic xx           source PY-PR1-Co-State.
*>         05  col   7  pic x(10)        source PY-PR1-Co-Zip.
*>         05  col  43  pic zzz,zz9.99   source SS tips
*>         05  col  59  pic zzz,zz9.99   source allocated tips
*> *>    03  line 11.
*> *>        05  col   4  pic x(20)        source 'control number' ???
*> *>        05  col  59  pic zzz,zz9.99   source dependant care benefits
*>     03  line 12.
*>         05  col  43  pic x(8)         source non qualified plans
*>     03  line 13.
*>         05  col   4  pic x(16)        source WS-Emp-First-Nm.      *> 1st name & init 2 be extracted Emp-Name
*>         05  col  16  pic x(15)        source       *> surname      *> Emp-Search-name or emp-name
*>         05  col  36  pic xx           source       *> Suffix       *> Ditto if surname has edditional text after
*>         05  col  59  pic xxxbx(10)    source       *> Box 12/a ?
*>     03  line 14.
*>         05  col  44  pic x            source       *> Stat emp x
*>         05  col  49  pic x            source       *> retirement plan
*>         05  col  54  pic x            source       *> 3rd pty sick pay
*>     03  line 15.
*>         05  col   4  pic x(32)        source Emp-Address-1.
*>         05  col  59  pic xxxbx(10)    source       *> box 12b
*>     03  line 16.
*>         05  col   4  pic x(32)        source Emp-Address-2.
*>         05  col  43  pic x(14)        source       *> box 14a line 1
*>     03  line 17.
*>         05  col   4  pic x(32)        source Emp-Address-3.
*>         05  col  43  pic x(14)        source       *> box 14a line 2
*>         05  col  59  pic xxxbx(10)    source       *> box 12c
*>     03  line 18.
*>         05  col   4  pic x(32)        source Emp-Address-4.
*>         05  col  43  pic x(14)        source       *> box 14a line 3
*>     03  line 19.
*>         05  col   4  pic xx           source Emp-State.
*>         05  col   7  pic x(10)        source Emp-Zip.
*>         05  col  59  pic xxxbx(10)    source       *> box 12d
*>     03  line 20.
*>         05  col  43  pic x(6)bx(6)    source       *> box 14b
*>     03  line 22.  *> Employers state details
*>         05  col   4  pic xx           source PY-PR1-Co-State. *> box 15
*>         05  col   7  pic x(15)        source PY-PR1-State-ID. *> ditto
*>         05  col  21  pic zzz,zz9.99    *> SUM His-YTD-Income-Taxable   His-YTD-Other-Taxable
 *>                                              His-YTD-Other-NonTaxable His-YTD-Tips.   *> sub.gross
*>         05  col  32  pic zzz,zz9.99   source His-YTD-SWT.      *> box 17 state income tax      other ??
*>         05  col  43  pic zzz,zz9.99    *> SUM His-YTD-Income-Taxable   His-YTD-Other-Taxable
 *>                                              His-YTD-Other-NonTaxable His-YTD-Tips.   *> sub.gross
 *>                                                                  box 18 local wages, tips etc His-YTD-LWT ???
*>         05  col  54  pic zz,zz9.99    source  His-YTD-LWT.      *> box 19
*>         05  col  65  x(5)             source       *> box 20 Locality name       ???
*> *>
*> *> Line 24 - Employers Secondary State details  not used in PY at least yet but is it needed ??
*> *>
*> *>    03  line 24.
*> *>
*> *>        05  col   4  pic xx           source PY-PR1-Co-State. *> box 15
*> *>        05  col   7  pic x(15)        source PY-PR1-State-ID. *> ditto
*> *>        05  col  21  pic zzz,zz9.99   source       *> box 16 state wages, tips etc
*> *>        05  col  32  pic zzz,zz9.99   source       *> box 17 state income tax
*> *>        05  col  43  pic zzz,zz9.99   source       *> box 18 local wages, tips etc
*> *>        05  col  54  pic zz,zz9.99    source       *> box 19 local income tax
*> *>        05  col  65  x(5)             source       *> box 20 Locality name
*>

 *>       col1% = disp% + 4  :\
 *>       col2% = disp% + 21 :\
 *>       col3% = disp% + 34 :\
 *>       col4% = disp% + 49 :\
 *>       col5% = disp% + 64

 01  W2-Detail type is detail. *> From basic code REPEAT generate WS-RS-Emp-Forms-Cnt TIMES
     03  line 3.    *> 310
         05  col  26  pic x(15)          source PY-PR1-State-ID.
     03  line + 2.
         05  col   4  pic x(34)          source PY-PR1-Trade-Name. *> Caution check form field length
     03  line + 1.
         05  col   4  pic x(32)          source PY-PR1-Co-Address-1.
     03  line + 1.
         05  col   4  pic x(32)          source PY-PR1-Co-Address-2.
         05  col  34  pic x(15)          source PY-PR1-Fed-ID.
     03  line + 1.
         05  col   4  pic x(32)          source PY-PR1-Co-Address-3.
     03  line + 1.
         05  col   4  pic x(32)          source PY-PR1-Co-Address-4
                                           present when PY-PR1-Co-Address-4 not = spaces.
*>
*> Employee data
*>

 *>   his.ytd.fica.gross = his.ytd.fica.taxable



     03  line + 1.
         05  col   4  pic xx             source PY-PR1-Co-State.
         05  col + 10 pic x(10)          source PY-PR1-Co-Zip.
         05  col + 21 pic zzz,zzz,zz9.99 source His-YTD-EIC.
*>
     03  line + 2.
         05  col   4  pic x(11)          source WS-Emp-SSN-X.  *> created after reading Emp rec
         05  col  21  pic zzz,zzz,zz9.99 source His-YTD-FWT.
         05  col  34  pic zzz,zzz,zz9.99 source Tmp-his-ytd-gross.
*>       Equals                            SUM His-YTD-Income-Taxable   His-YTD-Other-Taxable
*>                                             His-YTD-Other-NonTaxable His-YTD-Tips.   *> sub.gross
*>
         05  col  49  pic zzz,zzz,zz9.99 source His-YTD-FICA.
         05  col  64  pic zzz,zzz,zz9.99 source Tmp-his-ytd-FICA-Gross. *> both tmp flds are the same RECHECK ALL fields HERE
 *> SUM His-YTD-Income-Taxable   His-YTD-Other-Taxable
 *>     His-YTD-Other-Nontaxable His-YTD-Tips
*>
     03  line + 2.
         05  col   4  pic x(32)          source Emp-Name.
         05  col  34  pic x              source Emp-Pension-Used.
         05  col  64  pic zzz,zzz,zz9.99 source His-YTD-Tips.
     03  line + 2.
         05  col   4  pic x(32)          source Emp-Address-1.
     03  line + 1                         present when WS-Pnt-Local-Amount = "Y".
         05  col  34  pic zzz,zzz,zz9.99 source His-YTD-SWT.
         05  col  49  pic zzz,zzz,zz9.99 source Tmp-his-ytd-gross.
  *>    Equals                             SUM His-YTD-Income-Taxable   His-YTD-Other-Taxable
  *>                                           His-YTD-Other-NonTaxable His-YTD-Tips.   *> sub.gross
         05  col  64  pic xx             source PY-PR1-Co-State.
     03  line + 1
             col   4  pic x(32)          source Emp-Address-2.
     03  line + 1
             col   4  pic x(32)          source Emp-Address-3.
     03  line + 1.
         05  col   4  pic x(32)          source Emp-Address-4.
     03  line + 1                          present when WS-Pnt-Local-Amount = "Y".
         05  col  34  pic zzz,zzz,zz9.99 source His-YTD-LWT.
         05  col  49  pic zzz,zzz,zz9.99 source Tmp-his-ytd-gross.
*>       Equals                            SUM His-YTD-Income-Taxable   His-YTD-Other-Taxable
*>                                             His-YTD-Other-NonTaxable His-YTD-Tips.   *> sub.gross
         05  col  64  pic x(24)          source PY-PR1-Co-Address-4
                                          present when PY-PR1-Co-Address-4 not = spaces.
     03  line + 1.
         05  col   4  pic xx             source Emp-State.
         05  col  14  pic x(10)          source Emp-Zip.
*> Sub total form element


     03  line + 2                         present when WS-Pnt-Local-Amount = "Y".
         05  col  34  pic zzz,zzz,zz9.99 source WS-Sub-LWT.
         05  col  49  pic zzz,zzz,zz9.99 source WS-Sub-Gross.
         05  col  64  pic x(24)          source PY-PR1-Co-Address-3
                                          present when PY-PR1-Co-Address-4 = spaces.
         05  col  64  pic x(24)          source PY-PR1-Co-Address-4
                                          present when PY-PR1-Co-Address-4 not = spaces.
*>





 screen section.
*>*************
*>
*> two lines are replaced with a blanl line as values not required for inkjet/laser printers.
*>  WARNING using RW may not work for such printers - cannot test with these as not used in Development.
*>
 01  SS-Menu-Options background-color cob-color-black
                     foreground-color cob-color-green
                     erase eos.
     03  from  Prog-Name  pic x(17)                              line  1 col  1 foreground-color 2.
     03  value "Print W-2 Reports"                                       col 31.
     03  from  To-Day     pic x(10)                                      col 71 foreground-color 2.
     03  from  Usera      pic x(32)                              line  3 col  1.
*>
     03  value
         "                             Employee Selection"                               line  5 col  1.
03 value "-------------------------------------+--------------------------------------"  line  6 col  1.
03 value "                                     |"                                        line  7 col  1.
03 value "     1  All Employees                |  Print State and Local Amounts  [ ]"    line  8 col  1.
03 value "     2  Range of Employees           |"                                        line  9 col  1.
03 value "     3  Terminated Employees         |  Number of Forms Per Employee   [ ]"    line 10 col  1.
03 value "     4  A Single Employee            |"                                        line 11 col  1.
*> 03 value "                                     |  Number of Lines Between Forms  [  ]"   line 12 col  1.
03  value "                                    |"                                        line 12 col  1. *> instead of above
03 value "        Enter Selection [ ]          |"                                        line 13 col  1.
*> 03 value "                                     |  Starting Print Column          [  ]"   line 14 col  1.
03 value "                                     |"                                        line 14 col  1. *> instead of above
03 value "-------------------------------------+--------------------------------------"  line 15 col  1.
03 value "  Starting Employee Number [       ] |"                                        line 16 col  1.
03 value "      Employee Number   [       ]    |        Print Test Form [ ]"             line 17 col  1.
03 value "  Ending Employee Number   [       ] |"                                        line 18 col  1.
03 value "-------------------------------------+--------------------------------------"  line 19 col  1.
*>
*> Manual accepts as order is top left select, top right 4, then left to right.
*>
 *>    03  using WS-RS-Report-Type            pic x                line 13 col 26 foreground-color 3.
 *>    03  using WS-RS-State-Local            pic x                line  8 col 73 foreground-color 3.
 *>    03  using WS-RS-Emp-Forms-Cnt          pic 9                line 10 col 73 foreground-color 3.
*> *>    03  using WS-RS-No-Lines-Between-Forms pic 99               line 12 col 73 foreground-color 3.
*> *>    03  using WS-RS-Start-Prt-Col          pic 99               line 14 col 73 foreground-color 3.
 *>    03  using WS-RS-From-Emp               pic 9(7)             line 16 col 29 foreground-color 3.
 *>    03  using WS-RS-Single-Emp             pic 9(7)             line 17 col 26 foreground-color 3.
 *>    03  using WS-RS-Prt-Test-Form          pic x                line 17 col 64 foreground-color 3. *> UPPER
 *>    03  using WS-RS-To-Emp                 pic 9(7)             line 18 col 29 foreground-color 3.
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
              display  PY626 at line WS-23-Lines col 1 foreground-color 6 erase eos
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
*> This code block does not update any fields in PR1 PR2 NOW but might later
*> if program is updated for additional tests etc.
*>
     move     WS-Common-Date to WS-Test-YMD
     if       PY-PR2-Last-Q-Ended = 4
              move     WS-Test-YMD  to WS-End-of-Qtr
              if       WS-EoQ-Month = 01
                       subtract 1 from WS-EoQ-Year  *> decr year for last yr as running in new year
              end-if
              move     1231     to WS-End-of-Qtr (5:4)
     else
              move     WS-Common-Date to WS-End-of-Qtr.
*>
 display "End of Qtr now " WS-End-of-Qtr.   *> FOR TESTING ONLY
*>
     open     input    PY-Employee-File.
     if       PY-Emp-Status not = zeros
              display  PY622 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Employee-File
                       PY-Param1-File
              move     16 to WS-Term-Code
              goback   returning 2.

*>
     open     input    PY-History-File.
     if       PY-His-Emp-Status not = zeros
              display  PY624 at line WS-23-Lines col 1 foreground-color 6
                                                       erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Employee-File
                       PY-History-File
                       PY-Param1-File
              move     16 to WS-Term-Code
              goback   returning 3.
*>
*> Get values for Emp start, end and other values testing as we go - start again if error found
*>
     perform  forever
              display  SS-Menu-Options
              accept   WS-RS-State-Local   at line 8  col 73 UPPER UPDATE foreground-color 3
              if       WS-RS-State-Local not = "Y" and not = "N"
                       display  PY629      at line WS-23-Lines col 1 erase eos
                       exit perform cycle
              else  *> clr error msg
                       display  space      at line WS-23-Lines col 1 erase eos
              end-if
              accept   WS-RS-Emp-Forms-Cnt at line 10 col 73 UPDATE foreground-color 3
              if       WS-RS-Emp-Forms-Cnt < 1
                       display  PY634      at line WS-23-Lines col 1 erase eos
                       exit perform cycle
              else
                       display  space      at line WS-23-Lines col 1 erase eos
              end-if
*>              accept   WS-RS-No-Lines-Between-Forms at line 12 col 73 UPDATE foreground-color 3
              accept   WS-RS-Report-Type   at line 13 col 26 UPDATE foreground-color 3
              if       WS-RS-Report-Type < 1 or > 4
                       display  PY634      at line WS-23-Lines col 1 erase eos
                       exit perform cycle
              else
                       display  space      at line WS-23-Lines col 1 erase eos
              end-if
*>              accept   WS-RS-Start-Prt-Col at line 14 col 73 foreground-color 3
              if       WS-RS-Report-Type = 2
                       accept   WS-RS-From-Emp      at line 16 col 29 UPDATE foreground-color 3
              end-if
              accept   WS-RS-Prt-Test-Form at line 17 col 64 UPPER UPDATE foreground-color 3
              if       WS-RS-Prt-Test-Form not = "Y" and not = "N"
                       display  PY629      at line WS-23-Lines col 1 erase eos
                       exit perform cycle
              else  *> clr error msg
                       display  space      at line WS-23-Lines col 1 erase eos
              end-if
*>
              if       WS-RS-Report-Type = 4  *> Single employee
                       accept   WS-RS-Single-Emp at line 17 col 26 UPDATE foreground-color 3
                       exit perform
              end-if
*>
              if       WS-RS-Report-Type = 2
                       accept   WS-RS-To-Emp        at line 18 col 29 UPDATE foreground-color 3
              end-if
*> Test for from / to correct ranges
              if       WS-RS-Report-Type = 2                     *> Range > test
                and    WS-RS-From-Emp > WS-RS-To-Emp
                       display  PY633      at line WS-23-Lines col 1 erase eos
                       exit perform cycle
              else  *> clr error msg
                       display  space      at line WS-23-Lines col 1 erase eos
              end-if
*>
              if       WS-RS-Report-Type = 2                     *> Range < test
                and    WS-RS-To-Emp < WS-RS-From-Emp
                       display  PY638      at line WS-23-Lines col 1 erase eos
                       exit perform cycle
              else  *> clr error msg
                       display  space      at line WS-23-Lines col 1 erase eos
              end-if
*>
              if       WS-RS-Report-Type = 4                     *> Single Emp check exist
                       move     zeros to PY-Emp-Status
                                         PY-His-Emp-Status
                       move     WS-RS-Single-Emp  to His-Emp-No
                                                     Emp-No
                       start    PY-History-File  key = His-Emp-No
                       start    PY-Employee-File key = Emp-No
                       if       PY-His-Emp-Status not = zeros
                           or   PY-Emp-Status not = zeros
                                display  "**"  at line 17 col 33  foreground-color 6 blink
                                display  PY634 at line WS-23-Lines col 1 erase eos
                                exit perform cycle
                       else
                                display  space      at line WS-23-Lines col 1 erase eos
                                display  "  "       at line 17 col 33
                       end-if
              end-if
*>
              if       WS-RS-Report-Type = 2                     *> Range check they exist
                       move     zeros to PY-Emp-Status
                                         PY-His-Emp-Status
                       if       WS-RS-From-Emp not = zeros
                                move     WS-RS-From-Emp  to His-Emp-No
                                                            Emp-No
                                start    PY-History-File  key = His-Emp-No
                                start    PY-Employee-File key = Emp-No
                                if       PY-His-Emp-Status not = zeros
                                    or   PY-Emp-Status not = zeros
                                         display  "**"  at line 16 col 33  foreground-color 6 blink
                                         display  PY634 at line WS-23-Lines col 1 erase eos
                                         exit perform cycle
                                else
                                         display  "  "       at line 16 col 33
                                         display  space      at line WS-23-Lines col 1 erase eos
                                end-if
                       end-if
                       move     zeros to PY-Emp-Status
                                         PY-His-Emp-Status
                       if       WS-RS-To-Emp not = zeros
                                move     WS-RS-To-Emp  to His-Emp-No
                                                          Emp-No
                                start    PY-History-File  key = His-Emp-No
                                start    PY-Employee-File key = Emp-No
                                if       PY-His-Emp-Status not = zeros
                                    or   PY-Emp-Status not = zeros
                                         display  "**"  at line 18 col 33  foreground-color 6 blink
                                         display  PY634 at line WS-23-Lines col 1 erase eos
                                         exit perform cycle
                                else
                                         display  "  "       at line 18 col 33
                                         display  space      at line WS-23-Lines col 1 erase eos
                                end-if
                       end-if
              end-if
     end-perform.
*>
*> All params for program tested and pass
*>



*>
*> Will be Reading Emp & History in main body
*>
     initialise
              WS-Accumulator-Fields.   *> Do we really need these ?
*>
     open     output Print-File.
     initiate W2-Report.
*>
*> Check for test print
*>
     if       WS-RS-Prt-Test-Form = "Y"
              perform  zz100-Test-Form-Setup.

     if       WS-RS-Report-Type = 2
              move     zeros to PY-His-Emp-Status
              move     WS-RS-From-Emp  to His-Emp-No
                                          Emp-No
              start    PY-History-File  key = His-Emp-No
              if       PY-His-Emp-Status not = zeros
                       start    PY-History-File  key not < His-Emp-No
              end-if
     end-if.
     if       WS-RS-Report-Type = 4
              move     WS-RS-Single-Emp  to His-Emp-No
                                            Emp-No
              start    PY-History-File  key = His-Emp-No
              if       PY-His-Emp-Status not = zeros   *> Request for single Emp failed
                       display  PY634    at line WS-23-Lines foreground-color 6 erase eos
                       display  SY001    at line WS-Lines col 1
                       accept   WS-Reply at line WS-Lines col 48
                       close    PY-Employee-File
                                PY-History-File
                                PY-Param1-File
                       goback
              end-if
     end-if.
*>
     perform  forever
              if       WS-RS-Prt-Test-Form not = "Y"
                       read     PY-History-File next record at end
                                close    PY-History-File
                                exit     perform
                       end-read
              else
                       move     zeros to PY-His-Emp-Status
              end-if
*> Acccumulate
              if       PY-His-Emp-Status not = zero  *> Selected Emp # not found
                       display  PY636 at line WS-23-Lines col 1 foreground-color 6
                                                               erase eos
                       display  PY-His-Emp-Status at line WS-23-Lines col 36
                       move     PY-His-Emp-Status to PY-PR1-Status
                       display  WS-Eval-Msg   at line WS-23-Lines col 39
                       display  SY003         at line WS-Lines    col 1
                       accept   WS-Reply      at line WS-Lines    col 52 AUTO
                       close    PY-Employee-File
                                PY-History-File
                                Print-File
                                PY-Param1-File
                       move     16 to WS-Term-Code
                       goback   returning 5
              end-if
              if       WS-RS-Prt-Test-Form not = "Y"
               and     WS-RS-Report-Type = 2
                and    His-Emp-No > WS-RS-To-Emp   *> Finished printing Range of Emp
                       exit perform
              end-if
*> CHECK these vars against the test form vars <<<<<<<<<<<<<<<<<<<<
              if       WS-RS-Prt-Test-Form not = "Y"
                       move     His-YTD-FICA-Taxable to  Tmp-his-ytd-fica-gross  *> needed for test form print
                       add      His-YTD-Income-Taxable   His-YTD-Other-Taxable
                                His-YTD-Other-NonTaxable His-YTD-Tips          *> sub.gross
                                                   giving Tmp-his-ytd-gross
*>
              if       WS-RS-Prt-Test-Form not = "Y"
                       move     His-Emp-No to Emp-No
                       read     PY-Employee-File key Emp-No
                       if       PY-Emp-Status not = zero
*>
*> Most likely 23 = key not found could be a major problem, so abort run as no point continuing
*>
                                display  PY637 at line WS-22-Lines col 1 foreground-color 6
                                                                         erase eos
                                display  PY-Emp-Status   at line WS-22-Lines col 37
                                move     PY-Emp-Status to PY-PR1-Status
                                display  WS-Eval-Msg     at line WS-22-Lines col 40
                                display  "For Employee " at line WS-23-Lines col 1
                                display  Emp-No          at line WS-23-Lines col 14
                                display  SY003           at line WS-Lines    col 1
                                accept   WS-Reply        at line WS-Lines    col 52 AUTO
                                close    PY-Employee-File
                                         PY-History-File
                                         Print-File
                                         PY-Param1-File
                                move     16 to WS-Term-Code
                                goback   returning 5
                       end-if
              end-if
*>
*> can now generate report for Emp
*>
              if       WS-RS-Prt-Test-Form not = "Y"
                       if       WS-RS-Report-Type = 3
                          and   Emp-Status not = "T"
                                exit perform cycle
                       end-if
              end-if
              if       WS-RS-Prt-Test-Form not = "Y"
                       if       WS-RS-Emp-Forms-Cnt not = zero
                                perform  WS-RS-Emp-Forms-Cnt times  *> could be 1, 2 or more - we test for zero on i/p
                                         generate W2-Detail
                                end-perform
                                exit perform cycle
                       end-if
              else
                       generate W2-Detail
                       exit  perform
              end-if
     end-perform.
     terminate
              W2-Report.
*>
     close    Print-File.
     call     "SYSTEM" using Print-Report.  *>
*>
*> Finish off   NEEDED ?
*>
     if       WS-RS-Prt-Test-Form not = "Y"
              if       WS-Year-End not = "Y"   *> from basic code and always set
                 or    WS-All-Emp not = "Y"    *> we did not print all employees so not setting WS-Printed
                       close    PY-Employee-File
                                PY-History-File
                                Print-File
                                PY-Param1-File
                       display  PY621    at line WS-23-Lines col 1 foreground-color 6
                       display  SY001    at line WS-Lines    col 1
                       accept   WS-Reply at line WS-Lines    col 48 AUTO
                       goback   returning 8
              end-if
              move     "Y" to PY-PR2-W2-Printed
              move     1 to RRN
              rewrite  PY-Param1-Record
              if       PY-PR1-Status not = zeros
                       perform  ZZ040-Evaluate-Message
                       display  PY011         at line WS-23-Lines col 1 with erase eos
                       display  PY-PR1-Status at line WS-23-Lines col 37
                       display  WS-Eval-Msg   at line WS-23-Lines col 40
                       display  SY002         at line WS-Lines    col 1
                       accept   WS-Reply      at line WS-Lines    col 48 AUTO
                       close    PY-Param1-File
                       move     16 to WS-Term-Code
                       goback   returning 11
              end-if
     end-if.
*>
     close    PY-Param1-File.
     close    PY-Employee-File
              PY-History-File.
     goback.
*>
 ZZ040-Evaluate-Message      Section.
*>**********************************
*>
*> For PY-PR1 parameter file anfd other using PR-PR1-Status.
*>
     copy "FileStat-Msgs-2.cpy" replacing MSG  by WS-Eval-Msg
                                        STATUS by PY-PR1-Status.
*>
 ZZ040-Eval-Msg-Exit.
     exit     section.
*>
 zz100-Test-Form-Setup       section.
*>**********************************
*>
     if       WS-RS-Prt-Test-Form = "N"
              go to zz100-Exit.
     initialise
              PY-Employee-Record
              PY-History-Record.
     move     "NOAH COUNT, ESQ."  to Emp-Name.
     move     "123456 789th AVE." to Emp-Address-1.
     move     "APARTMENT 98765"   to Emp-Address-2.
     move     "CHICAGO"           to Emp-Address-3.
     move     "IL"                to Emp-State.
     move     "12345"             to Emp-Zip.
     move     111111.11           to His-YTD-Eic.
     move     123456789           to Emp-SSN.
     move     "Y"                 to Emp-Pension-Used
     move     222222.22           to His-YTD-FWT.
     move     333333.33           to Tmp-his-ytd-gross.
     move     444444.44           to His-YTD-FICA.
     move     555555.55           to Tmp-his-ytd-fica-gross.
     move     666666.66           to His-YTD-Tips.
     move     777777.77           to His-YTD-SWT.
     move     888888.88           to His-YTD-Other-Taxable.
     move     999999.99           to His-YTD-LWT.
     move     zeros               to WS-Sub-Totals.
*> missed
     move     151.12              to His-YTD-Income-Taxable.
     move     323.23              to His-YTD-Other-NonTaxable.
     move     123456              to Emp-No.
*>
*>  Any more to add ?
*>
 zz100-Exit.  exit section.
*>
