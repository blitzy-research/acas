       >>source free
*>****************************************************************
*>               Employee Journal Detail Report                  *
*>                                                               *
*>                 Employee Detailed                             *
*>                                                               *
*>            pyjourn1 used for summary report                   *
*>                                                               *
*>            Uses RW (Report writer for prints)                 *
*>                                                               *
*>          Program names will be changed to pynnn               *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       pyjourn.  *> to be renamed pynnn later.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 14/04/2026.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Employee Journal Detail Report.
*>                       This program uses RW (Report Writer)
*>
*>                      Semi-sourced from Basic code from pyjourn.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.    IS IT ??
*>                      (CBL_) ACCEPT_NUMERIC.c as static.
*>
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
*>
*>**
*> Changes:
*> 14/04/2026 vbc - 1.0.00 Created - Started coding from pyjourn.
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
*> System and is Copyright (c) Vincent B Coen. 1979-2026 and later.
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
 copy "selpypay.cob".
 copy "selpyact.cob".
 copy "selpyded.cob".
 copy "selpychk.cob".

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
 copy "fdpypay.cob".
 copy "fdpyact.cob".
 copy "fdpyded.cob".
 copy "fdpychk.cob".

*>
 fd  Print-File
     reports are Employee-Detailed-Journal-Report
                 Company-Summary
                 Ledger-Account-Summary.
*>
 01  Print-Line              pic x(132).
*>
 01  Print-Detail-1.
     03  filler              pic x.
     03  PD1-Earn-Cat        pic 99.
     03  filler              pic x.
     03  PD1-Earn-Desc       pic x(15).          *> 19
     03  filler              pic x(5).           *> 24
     03  PD1-Earn-Amt        pic zzz,zz9.99.     *> 34
     03  filler              pic xxx.            *> 37
     03  PD1-Earn-Units      pic zz9.99.         *> 43
     03  filler              pic xx.             *> 45
     03  PD1-Divider-1       pic x.              *> 46
     03  filler              pic x(4).           *> 50
     03  PD1-Ded-Cat         pic 99.             *> 52
     03  filler              pic x.
     03  PD1-Ded-Desc        pic x(15).          *> 68
     03  filler              pic x(5).           *> 73
     03  PD1-Ded-Amt         pic zz9.99.         *> 78
     03  filler              pic x(8).           *> 84
     03  PD1-Divider-2       pic x.              *> 88
     03  filler              pic x(6).           *> 94
     03  PD1-Other-Cat       pic 99.             *> 96
     03  filler              pic x.
     03  PD1-Other-Desc      pic x(15).          *> 112
     03  filler              pic x(5).           *> 117
     03  PD1-Other-Amt       pic zz9.99.         *> 123
*>
 01  Print-Divides.
     03  filler              pic x(45).
     03  PD2-Divider-1       pic x.
     03  filler              pic x(41).
     03  PD2-Divider-2       pic x.
*>
 01  Print-Detail-3.
     03  filler              pic x(9).
     03  PD3-Title           pic x(7).
     03  PD3-Desc            pic x(15).
     03  PD3-Colon           pic x.
     03  PD3-Units           pic zz,zz9.99.
*>
 01  Print-Detail-4.
     03  filler              pic x(20).
     03  PD4-Title           pic x(11).
     03  PD4-Units           pic zz,zz9.99.
*>

*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "pyjourn (1.0.00)".  *> First release pre testing.
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
*> WS area for file layouts for headers etc
*>
*> Need the header fields from PAY rec, Gets updated
*>
 01  WS-Pay-Header-Record.
     03  WS-Pay-Hdr-No                   pic 9(7).           *> value zero.
     03  WS-Pay-Hdr-Interval             pic x.              *> w, m
     03  WS-Pay-Hdr-Last-Apply-No        pic 9(4)      comp.
     03  WS-Pay-Hdr-Last-Day-of-Last-Per pic 9(8)      comp. *> ccyymmdd
     03  WS-Pay-Hdr-Journal-Printed      pic x.              *> Y / N
     03  filler                          pic x(9).
*>  More ?

*>
 01  WS-Data.
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
     03  D                   pic 999      value zero.    *> to set up accounts table with "Unknown" in desc
     03  F                   pic 9        value zero.
     03  WS-Page-Lines       binary-char unsigned value 56.   *> Narrow reports as system is for Landscape used.
     03  WS-Rec-Cnt          pic 99       value zero.
     03  WS-Page-Cnt         pic 999      value zero.
     03  WS-Line-Cnt         pic 999      value 90.   *> Force heads at start
*>
 01  WS-File-Statuses.       *> from all file operations.
     03  PY-PR1-Status       pic xx.
     03  PY-Emp-Status       pic xx.
     03  PY-Pay-Status       pic xx.
     03  PY-Act-Status       pic xx.
     03  PY-Ded-Status       pic xx.
     03  PY-Chk-Status       pic xx.

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
 01  WS-Accumulators-1.                        *> From Pay fields accumed
     03  WS-Reg-Wages             pic s9(7)v99.
     03  WS-Other-Earn            pic s9(7)v99.
     03  WS-Gross                 pic s9(7)v99.
     03  WS-Fwt                   pic s9(7)v99.
     03  WS-Swt                   pic s9(7)v99.
     03  WS-Lwt                   pic s9(7)v99.
     03  WS-Fica                  pic s9(7)v99.
     03  WS-Sdi                   pic s9(7)v99.
     03  WS-Eic                   pic s9(7)v99.
     03  WS-Other-Ded             pic s9(7)v99.
     03  WS-Net                   pic s9(7)v99.
     03  WS-Employer-Cost         pic s9(7)v99.
     03  WS-Tips                  pic s9(7)v99.
     03  WS-Tips-Reported         pic s9(7)v99.
     03  WS-Co-Fica               pic s9(7)v99.
     03  WS-Co-Futa               pic s9(7)v99.
     03  WS-Co-SUI                pic s9(7)v99.
     03  WS-Comp-Earned           pic s9(7)v99.
     03  WS-Comp-Taken            pic s9(7)v99.
     03  WS-SL-Taken              pic s9(7)v99.
     03  WS-Vac-Taken             pic s9(7)v99.
     03  WS-MCare                 pic s9(7)v99.   *> NEW
*>
     03  WS-Sys                   pic s9(7)v99     occurs 5.
     03  WS-Emp                   pic s9(7)v99     occurs 3.
     03  WS-Units                 pic s9(7)v99     occurs 4.

     03  WS-Temp-Acct-Amt         pic s9(8)v99.
*>
 01  WS-Presets.
     03  WS-Rep-From-Date         pic x(10).   *> HAS TO BE SET UP
     03  WS-Rep-To-Date           pic x(10).
     03  WS-Check-Date            pic x(10).
     03  WS-Detail-Line           pic x.
     03  WS-Fast-and-Slow         pic x.
     03  WS-DR-CR                 pic xx.
     03  WS-First-Detail-Line     pic x.
     03  WS-Exemptions            pic x(60).
     03  WS-Temp-Edo              pic 9.
     03  WS-Detail-Description    pic x(15).
     03  WS-Last-Pay-Emp-No       pic 9(7).
     03  WS-SSN.
         05  WS-SSN-9             pic 999/99/9999.
*>
 01  WS-Accumulators-2.
     03  WS-Dist-Out              pic s9(7)v99     occurs 5.
     03  WS-Temp                  pic s9(7)v99.
*>
     03  WS-Batch-Total           pic s9(7)v99.
*>
     03  WS-Total-Reg-Wages       pic s9(7)v99.  *> PY Co Summary part 1
     03  WS-Total-Other-Earn      pic s9(7)v99.
     03  WS-Total-Tips            pic s9(7)v99.
     03  WS-Total-Fwt             pic s9(7)v99.
     03  WS-Total-Swt             pic s9(7)v99.
     03  WS-Total-Lwt             pic s9(7)v99.
     03  WS-Total-Fica            pic s9(7)v99.
     03  WS-Total-Sdi             pic s9(7)v99.
     03  WS-Total-Other-Ded       pic s9(7)v99.
     03  WS-Total-Net             pic s9(7)v99.
*>
     03  WS-Total-Tips-Reported   pic s9(7)v99.  *> PY Co Summary part 2
     03  WS-Total-Co-Fica         pic s9(7)v99.
     03  WS-Total-Co-Futa         pic s9(7)v99.
     03  WS-Total-Co-Sui          pic s9(7)v99.
     03  WS-Total-Vac-Taken       pic s9(7)v99.
     03  WS-Total-SL-Taken        pic s9(7)v99.
     03  WS-Total-Comp-Taken      pic s9(7)v99.
     03  WS-Total-Comp-Earned     pic s9(7)v99.
     03  WS-Total-Eic             pic s9(7)v99.
     03  WS-Total-MCare           pic s9(7)v99.   *> NEW
     03  WS-Total-Units           pic s9(7)v99    occurs 4.  *> Vie PY-PR1-Rate-Name occcurs 4
*>
 01  WS-Total-Units               pic 9(4)v99.
*>
 01  WS-Emp-Accumulator.     *> For print lines with Earnings, Deductions and Others - Reset for new Emp;
     03  WS-Earn-Used             binary-char.     *> set up by 1 for all inst
     03  WS-Ded-Used              binary-char.     *> set up by 1 for all inst
     03  WS-Other-Used            binary-char.     *> set up by 1 for all inst
     03  WS-Option-Chk-Size       binary-char       value 16.  *> MUST be same # as Next occurs
     03  WS-All-Option-Block                      occurs 16.    *> Over sized.
         05  WS-Earn-Amt          pic s9(7)v99     comp-3.
         05  WS-Earn-Units        pic s9(7)v99     comp-3.  *> - 10
         05  WS-Earn-Desc         pic x(15).                *> 25
         05  filler               pic xxx.                  *> WB
*>
         05  WS-Ded-Amt           pic s9(7)v99     comp-3.
         05  WS-Ded-Desc          pic x(15).                *> + 20
*>
         05  WS-Other-Amt         pic s9(7)v99     comp-3.    *> 5
         05  WS-Other-Desc        pic x(15).                  *> 20
*>
*>
 01  WS-File-Status.  *> Set when opening file as can not exist
     03  WS-Chk-Exists            pic x  value "N".
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
 01  WS-Table1.
*>
*>       1=earning
*>       2=deduction
*>       3=other
     03  WS-Desc-Table.
         05  WS-ED-Descs    occurs 50.
             07  WS-EDO      pic 9.
             07  WS-ED-Desc  pic x(15).
     03  filler redefines WS-Desc-Table.
         05  filler          pic x(16) value "1REGULAR PAY".    *> from py-pr1-rate-name (1 - 4)
         05  filler          pic x(16) value "1OVERTIME PAY".   *> ditto
         05  filler          pic x(16) value "1SPECIAL OT PAY". *> ditto
         05  filler          pic x(16) value "1COMMISSION".     *> ditto
         05  filler          pic x(16) value "3VACATION TAKEN".  *>  NOT ON CHECKS  all rest from here
         05  filler          pic x(16) value "3SICK LVE TAKEN".  *>  NOT ON CHECKS  eg WS-ED-Desc
         05  filler          pic x(16) value "3COMP TIME TAKEN". *>  NOT ON CHECKS
         05  filler          pic x(16) value "3COMP TIME EARND". *>  NOT ON CHECKS
         05  filler          pic x(16) value "1BONUS".
         05  filler          pic x(16) value "1TIPS COLLECTED".
         05  filler          pic x(16) value "3ADVANCE".           *> 11
         05  filler          pic x(16) value "1SICK PAY".
         05  filler          pic x(16) value "1VACATION PAY".
         05  filler          pic x(16) value "1OTHER EXCLD PAY".
         05  filler          pic x(16) value "3EXPENSE REIMB".     *> 15
         05  filler          pic x(16) value "1EIC".
         05  filler          pic x(16) value "1OTHER PAY".
         05  filler          pic x(16) value "1TIPS REPORTED".
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "2FWT".
         05  filler          pic x(16) value "2SWT".
         05  filler          pic x(16) value "2LWT".
         05  filler          pic x(16) value "2FICA".
         05  filler          pic x(16) value "2SDI".
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "2ADVANCE REPAY".
         05  filler          pic x(16) value "2FWT ADD-ON".
         05  filler          pic x(16) value "2SWT ADD-ON".
         05  filler          pic x(16) value "2LWT ADD-ON".
         05  filler          pic x(16) value "2FICA ADD-ON".
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "0SYS1".           *>  from sys1   FROM DED FILE 33 ded-sys-desc
         05  filler          pic x(16) value "0SYS2".           *>  from sys2   FROM DED FILE    ded-sys-desc
         05  filler          pic x(16) value "0SYS3".           *>  from sys3   FROM DED FILE 35 ded-sys-desc
         05  filler          pic x(16) value "0SYS4".           *>  from sys4   FROM DED FILE    ded-sys-desc
         05  filler          pic x(16) value "0SYS5".           *>  from sys5   FROM DED FILE 37 ded-sys-desc
         05  filler          pic x(16) value "0EMP1".           *>  from emp1   FROM EMP FILE    emp-ed-desc
         05  filler          pic x(16) value "0EMP2".           *>  from emp2   FROM EMP FILE    emp-ed-desc
         05  filler          pic x(16) value "0EMP3".           *>  from emp3   FROM EMP FILE 40 emp-ed-desc
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "3COMPANY FICA".   *> NOT ON CHECKS
         05  filler          pic x(16) value "3COMPANY FUTA".   *> NOT ON CHECKS
         05  filler          pic x(16) value "3COMPANY SUI".    *> NOT ON CHECKS
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "3OTHER CO COST".  *> NOT ON CHECKS
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "3".
         05  filler          pic x(16) value "2OTHER DED".
*>

 01  WS-Account-Table                  value zero.
     03  WS-Account-Grp            occurs 99.
         05  WS-Acct-No      pic 99       comp.
         05  WS-Acct-GL      pic 9(6)     comp.
         05  WS-Acct-Amt     pic s9(9)v99 comp-3.       *> Yes well oversized.
*>



 01  Error-Messages.   *> ANY NEEDED ???
*> System Wide
     03  SY000           pic x(30) value "SY000 Completed Unsuccessfully".
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY002           pic x(31) value "SY002 Note error and hit Return".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*>
*> Module General
*>
     03  PY001           pic x(45) value "PY001 Payroll Parameter file does not exist -".
     03  PY002           pic x(32) value "PY002 Read PARAM record Error = ".
     03  PY003           pic x(31) value "PY003 Employee File not Found -".
*>
*> Module specific
*>
     03  PY760           pic x(24) value "PY760 Chk file not found".
     03  PY761           pic x(24) value "PY761 Pay file not found".
     03  PY762           pic x(24) value "PY762 Emp file not found".
     03  PY763           pic x(24) value "PY763 Act file not found".
     03  PY764           pic x(24) value "PY764 Ded file not found".
     03  PY765           pic x(54) value "PY765 Net pay exceeds system max. check will be voided".
     03  PY766           pic x(26) value "PY766 Batch total not zero".
     03  PY767           pic x(50) value "PY767 Net pay less than zero. check will be voided".
*>
     03  PY768           pic x(31) value "PY768 Error Reading Pay file - ".
     03  PY769           pic x(31) value "PY769 Error Reading Emp file - ".
     03  PY770           pic x(31) value "PY770 Error Reading Act file - ".
     03  PY771           pic x(31) value "PY771 Error Reading Ded file - ".
     03  PY772           pic x(32) value "PY772 Unexpected eof on Pay file".   *> pyjourn1
     03  PY773           pic x(38) value "PY773 Error Accounts records exceed 99".
     03  PY774           pic x(31) value "PY774 Error Reading Chk file - ".
     03  PY775           pic x(40) value "PY775 Error Reading Act Header Record - ".
     03  PY776           pic x(42) value "PY776 Error Table Emp-Accumulator exceeded".
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
*> Print layouts to 132 cols Landscape lpr settings
*>
*>     reports are Employee-Detailed-Journal-Report
*>                 Company-Summary
*>                 Ledger-Account-Summary.
*>
 RD  Employee-Detailed-Journal-Report
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 6
     Last  Detail WS-Page-Lines.
*>
 01  Employee-Detailed-Journal-Head  Type Page Heading.
     03  line  1.
         05  col  50     pic x(40)         source UserA.
         05  col 108     pic x(10)         source U-Date.
         05  col 120     pic x(8)          source WSD-Time.
     03  line  2.
         05  col   1     pic x(17)         source Prog-Name.
         05  col  56     pic x(19)         value "ACAS Payroll System".
         05  col 124     pic x(5)          value "Page ".
         05  col 129     pic zz9           source Page-Counter.
     03  Line  3.
         05  col  54     pic x(22)         value "Payroll Journal Report".
     03  line  4.
         05  col   1     pic x(10)         value "Interval: ".
         05  col  10     pic x             source  WS-Pay-Hdr-Interval.   *> Hdr needs reading and store in WS
         05  col  54     pic x(23)         value "Employee Payroll Detail".
         05  col  98                       value "From: ".
         05  col 104     pic x(10)         source  WS-Rep-From-Date.
         05  col 116                       value "To: ".
         05  col 120     pic x(10)         source  WS-Rep-To-Date.
     03  line  5.
         05  col 108     pic x(12)         value "Check Date: ".
         05  col 120     pic x(10)         source  WS-Check-Date.
*>
 01  Employee-Detailed type is detail.
     03  line  6.
         05  col   1                       value "#".   *> Original looks to be a "*" but why ?
         05  col   2     pic 9(7)          source Emp-No.
         05  col  10     pic x(32)         source Emp-Search-Name.   *> but could be  Emp-Name.
         05  col  55     pic x(11)         source WS-SSN.            *> Set up for 999-99-9999 from EMP-SSN
         05  col  69     pic x(60)         source WS-Exemptions.
     03  line + 2.
         05  col   1                       value "-------------E a r n i n g s-------------".
         05  col  51                       value "------D e d u c t i o n s------".
         05  col  95                       value "-----------O t h e r-----------".
     03  line + 1.
         05  col  46                       value "|".
         05  col  88                       value "|".
*>
 *> 01  type control Footing Final.

 01  Employee-Detailed-Bottom type detail.
     03  line + 2.
         05  col   7                       value "Reg Wages".
         05  col  20                       value "Other Earn".
         05  col  37                       value "Tips".
         05  col  46                       value "FWT".
         05  col  55                       value "SWT".
         05  col  64                       value "LWT".
         05  col  73                       value "FICA".
         05  col  82                       value "SDI".
         05  col  95                       value "Other Deds".
         05  col 104                       value "Net".
*>
     03  line + 1.
         05  col   4    pic zzz,zz9.99     source WS-Reg-Wages.
         05  col  20    pic zzz,zz9.99      sum   WS-Other-Earn WS-EIC.
         05  col  35    pic zzz,zz9.99     source WS-Tips.
         05  col  45    pic zzz,zz9.99     source WS-FWT.
         05  col  55    pic zzz,zz9.99     source WS-SWT.
         05  col  65    pic zzz,zz9.99     source WS-LWT.
         05  col  75    pic zzz,zz9.99     source WS-FICA.
         05  col  85    pic zzz,zz9.99     source WS-SDI.
         05  col  95    pic zzz,zz9.99     source WS-Other-Ded.
         05  col 101    pic zzz,zz9.99     source WS-Net.
*>
     03  line + 1.
         05  col   7                       value "Gross".
         05  col  18                       value "Employer Exp".
         05  col  32                       value "Total Cost".
         05  col  60    pic 99             source Emp-Dist-Acct  present when Emp-Dist-Pcent (1) not = zero.
         05  col  62                       value ":"             present when Emp-Dist-Pcent (1) not = zero.
         05  col  63    pic 9(6)           source WS-Acct-No (Emp-Dist-Acct (1))   present when Emp-Dist-Pcent (1) not = zero.
         05  col  74    pic 99             source Emp-Dist-Acct  present when Emp-Dist-Pcent (2) not = zero.
         05  col  76                       value ":"             present when Emp-Dist-Pcent (2) not = zero.
         05  col  77    pic 9(6)           source WS-Acct-No (Emp-Dist-Acct (2))   present when Emp-Dist-Pcent (2) not = zero.
         05  col  88    pic 99             source Emp-Dist-Acct  present when Emp-Dist-Pcent (3) not = zero.
         05  col  90                       value ":"             present when Emp-Dist-Pcent (3) not = zero.
         05  col  91    pic 9(6)           source WS-Acct-No (Emp-Dist-Acct (3))   present when Emp-Dist-Pcent (3) not = zero.
         05  col 102    pic 99             source Emp-Dist-Acct  present when Emp-Dist-Pcent (4) not = zero.
         05  col 104                       value ":"             present when Emp-Dist-Pcent (4) not = zero.
         05  col 105    pic 9(6)           source WS-Acct-No (Emp-Dist-Acct (4))   present when Emp-Dist-Pcent (4) not = zero.
         05  col 116    pic 99             source Emp-Dist-Acct  present when Emp-Dist-Pcent (5) not = zero.
         05  col 118                       value ":"             present when Emp-Dist-Pcent (5) not = zero.
         05  col 119    pic 9(6)           source WS-Acct-No (Emp-Dist-Acct (5))   present when Emp-Dist-Pcent (5) not = zero.
*>
     03  line + 1.
         05  col   4    pic zzz,zz9.99      sum   WS-Gross   WS-EIC.
         05  col  20    pic zzz,zz9.99     source WS-Employer-Cost.     *> not this     WS-Reg-Wages WS-Other-Earn WS-Tips.
         05  col  35    pic zzz,zz9.99      sum  WS-Gross  WS-Employer-Cost.
         05  col  50                       value "Distribution:".
         05  Distribution             present when PY-PR1-Dist-Used = "Y".
           07  col  60  pic zzz,zz9.99                               present when Emp-Dist-Percent (1) not = zero source WS-Dist-Out (1).
           07  col  74  pic zzz,zz9.99                               present when Emp-Dist-Percent (2) not = zero source WS-Dist-Out (2).
           07  col  88  pic zzz,zz9.99                               present when Emp-Dist-Percent (3) not = zero source WS-Dist-Out (3).
           07  col 102  pic zzz,zz9.99                               present when Emp-Dist-Percent (4) not = zero source WS-Dist-Out (4).
           07  col 116  pic zzz,zz9.99                               present when Emp-Dist-Percent (5) not = zero source WS-Dist-Out (5).
*>



*>
 RD  Company-Summary
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 6
     Last  Detail WS-Page-Lines.
*>
 01  Company-Summary-Head Type Page Heading.
     03  line  1.
         05  col  50     pic x(40)         source UserA.
         05  col 108     pic x(10)         source U-Date.
         05  col 120     pic x(8)          source WSD-Time.
     03  line  2.
         05  col   1     pic x(17)         source Prog-Name.
         05  col  56     pic x(19)         value "ACAS Payroll System".
         05  col 124     pic x(5)          value "Page ".
         05  col 129     pic zz9           source Page-Counter.
     03  Line  3.
         05  col  54     pic x(22)         value "Payroll Journal Report".
     03  line  4.
         05  col   1     pic x(10)         value "Interval: ".
         05  col  10     pic x             source  WS-Pay-Hdr-Interval.   *> Hdr needs reading and store in WS
         05  col  58     pic x(23)         value "Company Payroll Summary".
         05  col  98                       value "From: ".
         05  col 104     pic x(10)         source  WS-Rep-From-Date.
         05  col 116                       value "To: ".
         05  col 120     pic x(10)         source  WS-Rep-To-Date.
     03  line  5.
         05  col 108     pic x(12)         value "Check Date: ".
         05  col 120     pic x(10)         source  WS-Check-Date.
*>
 01  Company-Summary-Detail type is detail.
     03  line + 3.
         05  col   5                       value "Total".
         05  col  18                       value "Total".
         05  col  31                       value "Total".
         05  col  44                       value "Total".
         05  col  57                       value "Total".
         05  col  70                       value "Total".
         05  col  83                       value "Total".
         05  col  96                       value "Total".
         05  col 109                       value "Total".
         05  col 122                       value "Total".
     03  line + 1.
         05  col   3                       value "Reg Wages".
         05  col  15                       value "Other Earn".
         05  col  32                       value "Tips".
         05  col  45                       value "FWT".
         05  col  58                       value "SWT".
         05  col  71                       value "LWT".
         05  col  84                       value "Fica".
         05  col  97                       value "SDI".
         05  col 106                       value "Other Deds".
         05  col 123                       value "Net".
     03  line + 1.
         05  col   3 pic zzz,zz9.99        source WS-Total-Reg-Wages.
         05  col  13 pic zzz,zz9.99        source WS-Total-Other-Earn.
         05  col  26 pic zzz,zz9.99        source WS-Total-Tips.
         05  col  39 pic zzz,zz9.99        source WS-Total-Fwt.
         05  col  52 pic zzz,zz9.99        source WS-Total-Swt.
         05  col  65 pic zzz,zz9.99        source WS-Total-Lwt.
         05  col  78 pic zzz,zz9.99        source WS-Total-Fica.
         05  col  91 pic zzz,zz9.99        source WS-Total-Sdi.
         05  col 104 pic zzz,zz9.99        source WS-Total-Other-Ded.
         05  col 117 pic zzz,zz9.99        source WS-Total-Net.
*>
     03  line + 2.
         05  col   5                       value "Total".
         05  col  18                       value "Total".
         05  col  31                       value "Total".
         05  col  44                       value "Total".
         05  col  57                       value "Total".
         05  col  70                       value "Total".
         05  col  83                       value "Total".
         05  col  96                       value "Total".
         05  col 109                       value "Total".
         05  col 122                       value "Total".
     03  line + 1.
         05  col   2                       value "Tips Report".
         05  col  17                       value "Co Fica".
         05  col  30                       value "Co Futa".
         05  col  44                       value "Co SUI".
         05  col  55                       value "Vac Taken".
         05  col  68                       value "SL Taken".
         05  col  80                       value "Comp Taken".
         05  col  93                       value "Comp Earned".
         05  col 108                       value "EIC".
         05  col 123                       value "MCare".    *> NEW
     03  line + 1.
         05  col   3 pic zzz,zz9.99        source WS-Total-Tips-Reported.
         05  col  13 pic zzz,zz9.99        source WS-Total-Co-Fica.
         05  col  26 pic zzz,zz9.99        source WS-Total-Co-Futa.
         05  col  39 pic zzz,zz9.99        source WS-Total-Co-Sui.
         05  col  52 pic zzz,zz9.99        source WS-Total-Vac-Taken.
         05  col  65 pic zzz,zz9.99        source WS-Total-Sl-Taken.
         05  col  78 pic zzz,zz9.99        source WS-Total-Comp-Taken.
         05  col  91 pic zzz,zz9.99        source WS-Total-Comp-Earned.
         05  col 104 pic zzz,zz9.99        source WS-Total-Eic.
         05  col 117 pic zzz,zz9.99        source WS-Total-MCare.  *> NEW
*>
     03  line + 2.             *> ALL CHECK ALIGNMENTS etc
         05  col   7                       value "Total Units:".
         05  col  20 pic x(15)             source PY-PR1-Rate-Name (1).  *> Regular  But bus can chg it - ditto other 3.
         05  col  40 pic zz,zz9.99         source WS-Total-Units (1).
     03  line + 1.
         05  col  20 pic x(15)             source PY-PR1-Rate-Name (2).  *> Overtime
         05  col  40 pic zz,zz9.99         source WS-Total-Units (2).
     03  line + 1.
         05  col  20 pic x(15)             source PY-PR1-Rate-Name (3).  *> Spec. Overtime
         05  col  40 pic zz,zz9.99         source WS-Total-Units (3).
     03  line + 1.
         05  col  20 pic x(15)             source PY-PR1-Rate-Name (4).  *> Commission ADDED from the cbasic version
         05  col  40 pic zz,zz9.99         source WS-Total-Units (4).
*>
     03  line + 1.
         05  col  20                       value "Grd Total Units".
         05  col  39 pic zzz,zz9.99        SUM  WS-Total-Units (1)
                                                WS-Total-Units (2)
                                                WS-Total-Units (3)
                                                WS-Total-Units (4).
*>
 RD  Ledger-Account-Summary
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 9
     Last  Detail WS-Page-Lines.
*>
 01  Ledger-Account-Summary-Head Type Page Heading.
     03  line  1.
         05  col  50     pic x(40)     source UserA.
         05  col 108     pic x(10)     source U-Date.
         05  col 120     pic x(8)      source WSD-Time.
     03  line  2.
         05  col   1     pic x(17)     source Prog-Name.
         05  col  56     pic x(19)     value "ACAS Payroll System".
         05  col 124     pic x(5)      value "Page ".
         05  col 129     pic zz9       source Page-Counter.
     03  Line  3.
         05  col  54     pic x(22)     value "Payroll Journal Report".
     03  line  4.
         05  col   1     pic x(10)     value "Interval: ".
         05  col  10     pic x         source  WS-Pay-Hdr-Interval.   *> Hdr needs reading and store in WS
         05  col  59     pic x(23)     value "Ledger Account Summary".
         05  col  98                   value "From: ".
         05  col 104     pic x(10)     source  WS-Rep-From-Date.
         05  col 116                   value "To: ".
         05  col 120     pic x(10)     source  WS-Rep-To-Date.
     03  line  5.
         05  col 108     pic x(12)     value "Check Date: ".
         05  col 120     pic x(10)     source  WS-Check-Date.
     03  line  6.
         05  col  31                   value "Acct".
         05  col  42                   value "GL".
         05  col  59                   value "Account".
         05  col  92                   value "Posted".
     03  line 7.
         05  col  32                   value "No".
         05  col  41                   value "Acct".
         05  col  62                   value "Name".
         05  col  92                   value "Total".
         05  col 102                   value "CD".
     03  line 9.
         05  col 1                     value " ".
*>
 01  Ledger-Account-Summary-Detail type is detail.
     03  line + 1.
         05  col  31  pic z9           source Act-No.
         05  col  40  pic 9(6)         source Act-GL-No.
         05  col  52  pic x(24)        source Act-Desc.
         05  col  88  pic z,zzz,zz9.99 source WS-Temp-Acct-Amt. *> from ???
         05  col 102  pic xx           source WS-DR-CR.         *> needs to be set after reading recs ?
*>
 01  type control Footing Final line plus 2.    *> Need to accumulate post amts to batch-totals with sign - truncated.
     03  col 70       pic x(34)         value "Batch Total :".
     03  col 87       pic zz,zzz,zz9.99 source WS-Batch-Total.
     03  col 99       pic xx            value "CR" present when WS-Batch-Total < zero.
     03  col 99       pic xx            value "DR" present when WS-Batch-Total > zero.
*>
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
     initialise
              WS-Account-Table
              WS-Presets
              WS-Accumulators-2
              WS-Accumulators-1.
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
              goback   returning 11
     end-if.
*>
 *>     close    PY-Param1-File.             *> Record still in WS area - LEAVE OPEN
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
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 2.
*>
     open     i-o PY-Accounts-File.   *> O/P only for header update - Pay-Hdr-Journal-Printed ( = "Y" ) - REMINDER
     if       PY-Act-Status not = zero
              display  PY763         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 3.
*>
     open     input PY-System-Deduction-File.
     if       PY-Ded-Status not = zero
              display  PY764         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-System-Deduction-File
                       PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 4.
     move     1 to RRN.
     read     PY-System-Deduction-File.
     if       PY-Ded-Status not = zero
              move     PY-Ded-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY771         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-Chk-Status at line WS-23-Lines col 32 foreground-color 4
              display  WS-Eval-Msg   at line WS-23-Lines col 35
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Check-File
                       PY-System-Deduction-File
                       PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 14.
*>
     open     input PY-Check-File.
     if       PY-Chk-Status not = zero
              display  PY760        at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Check-File
                       PY-System-Deduction-File
                       PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 5.
     move     "Y" to WS-Chk-Exists.
     move     zeros to Chk-Hdr-No.
     read     PY-Check-File.
     if       PY-Chk-Status not = zero
              move     PY-Chk-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY774         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-Chk-Status at line WS-23-Lines col 32 foreground-color 4
              display  WS-Eval-Msg   at line WS-23-Lines col 35
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Check-File
                       PY-System-Deduction-File
                       PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 15.
*>
     open     i-o PY-Pay-File.
     if       PY-Pay-Status not = zero
              display  PY761         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Pay-File
                       PY-Check-File
                       PY-System-Deduction-File
                       PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 6.
*>
*> Read & store header to update Pay-Hdr-Journal-Printed
*>   and need Pay-Hdr-Interval & 4 reports
*>
     move     zeros to Pay-Hdr-No.
     read     PY-Pay-File into WS-Pay-Header-Record.
     if       PY-Pay-Status not = "00"
              move     PY-Pay-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY775         at line WS-23-Lines col 1 with erase eos
              display  PY-PR1-Status at line WS-23-Lines col 41
              display  WS-Eval-Msg   at line WS-23-Lines col 44
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Pay-File
                       PY-Check-File
                       PY-System-Deduction-File
                       PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 16.
*>
*> load up Acct table ready to take on posted Amounts for the year
*>
*>??     perform
     initiate Employee-Detailed-Journal-Report.


     perform  forever
              read     PY-Accounts-File at end
                       exit perform
              end-read
              add      1 to D
              if       D > 99
                       display  PY773  at line WS-23-Lines col 1 foreground-color 4 erase eos
                       display  SY001         at line WS-Lines    col 1
                       accept   WS-Reply      at line WS-Lines    col 48 auto
                       close    PY-System-Deduction-File
                                PY-Check-File
                                PY-Accounts-File
                                PY-Employee-File
                                PY-Param1-File
                       move     1 to WS-Term-Code
                       goback   returning 13
              end-if
              move     Act-GL-No to WS-Acct-No  (Act-No)
              move     Act-Desc  to WS-Acct-GL  (Act-No)
              move     zeros     to WS-Acct-Amt (Act-No)
              exit perform cycle
     end-perform.
     close    PY-Accounts-File.   *> REMEMBER IT IS CLOSED when closing the other files.
*>
     open     output Print-File.   *> Used for all three reports
*>
*> MORE FILE OPEN etc ?   <<<<<<<<<<
*>
     move     zeros to WS-Page-Cnt.
     move     90    to WS-Line-Cnt.  *> Force heads 4 rep 1.
*>
*> Set heads
*>
     perform  ca010-Check-Date-2-Formatted.
     perform  ca020-From-Date-2-Formatted.
     perform  ca030-To-Date-2-Formatted.
*>
     start    PY-Pay-File FIRST.
     perform  forever
              read     PY-Pay-File at end
                       if       WS-Last-Pay-Emp-No not = zeros
                                perform  ba000-Print-Journal-Details
                       end-if
                       exit perform
              end-read
              if       Pay-Emp-No not = WS-Last-Pay-Emp-No
                       move     Pay-Emp-No to WS-Last-Pay-Emp-No
                       move     Pay-Emp-No to Emp-No
                       if       WS-Last-Pay-Emp-No not = zeros
                                perform  ba000-Print-Journal-Details
                       end-if
                       read     PY-Employee-File
                       if       PY-Emp-Status not = "00"
                                move     PY-Emp-Status to PY-PR1-Status
                                perform  ZZ040-Evaluate-Message
                                display  PY769         at line WS-23-Lines col 1 with erase eos
                                display  PY-PR1-Status at line WS-23-Lines col 41
                                display  WS-Eval-Msg   at line WS-23-Lines col 44
                                display  SY001         at line WS-Lines    col 1
                                accept   WS-Reply      at line WS-Lines    col 48 AUTO
                                close    PY-Pay-File
                                         PY-Check-File
                                         PY-System-Deduction-File
                                         PY-Accounts-File
                                         PY-Employee-File
                                         PY-Param1-File
                                move     1 to WS-Term-Code
                                goback   returning 16           *> MUST not happen
                       end-if
              end-if
*> 4100
              perform  varying  A from 1 by 1 until A > PY-PR1-Max-Emp-Eds or > 3
                       if       Emp-ED-Earn-Ded (A) = "E"
                                move     1 to WS-Temp-Edo
                       else
                                move     2 to WS-Temp-Edo
                       end-if
                       move     WS-Temp-Edo   to WS-Edo (37 + A)
              end-perform
*> 7000 - Clear accumulators
              initialize
                       WS-Accumulators-1
                       WS-Emp-Accumulator    *> For Earn, Ded and Other amt and desc
              move     "Y" to WS-Detail-Line  *> Needed ?
              move     "999/99/9999" to WS-SSN
              move     Emp-SSN  to WS-SSN-9
              inspect  WS-SSN replacing all "/" by "-"
              perform  ca000-6100         *> Set exemptions for Emp
              perform  ca000-8100         *>	Accumulate pay info
              perform  ca000-9150         *>    Get Pay detail description
*>
     end-perform.



*> CHANGES HERE

 *>     perform  aa050-Report-Vacation.


     close    PY-Employee-File  *> and all the others

     if       Page-Counter > zero           *> Don't print a empty report
              close Print-File
              call     "SYSTEM" using Print-Report.  *> Landscape
     go to aa000-EOJ.
*>

 aa000-EOJ.
     if       WS-Batch-Total not = zero
              display  PY766    at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  " Completed Unsuccessfully" at line ws-Lines col 1
              display  SY002    at line WS-Lines col 1
              accept   WS-Reply at line WS-Lines col 33
              goback   returning 16.
     goback.
*>
 ba000-Print-Journal-Details  section.
*>***********************************
*>
     generate Employee-Detailed.  *> Top end only
*>
*> Use table as src to print details for Earn, Ded and Other  - THIS NEEDS TESTING against test data using manual
*>
     perform  varying  A from 1 by 1 until A > 16
              if       A > 16
                       exit perform
              initialise
                       Print-Detail-1
              if       A > WS-Earn-Used  *> Chk if all other tables entrries are empty
                and      > WS-Ded-Used
                and      > WS-Other-Used
                       exit perform
              end-if
              move     "|"  to PD1-Divider-1
                               PD1-Divider-2
              if       A not > WS-Earn-Used
                       move     WS-Earn-Desc  (A) to PD1-Earn-Desc
                       move     WS-Earn-Amt   (A) to PD1-Earn-Amt
                       move     WS-Earn-Units (A) to PD1-Earn-Units
              end-if
              if       A not > WS-Ded-Used
                       move     WS-Ded-Desc   (A) to PD1-Ded-Desc
                       move     WS-Ded-Amt    (A) to PD1-Ded-Amt
              end-if
              if       A not > WS-Other-Used
                       move     WS-Other-Desc (A) to PD1-Other-Desc
                       move     WS-Other-Amt  (A) to PD1-Other-Amt
              end-if
              write    Print-Detail-1 after 1
              add      1  to Line-Counter
              exit perform cycle
     end-perform.
     move     spaces to Print-Divides.
     move     "|"  to PD2-Divider-1
                      PD2-Divider-2.
     write    Print-Detail-1 after 1.
     add      1  to Line-Counter.
     move     zeros to WS-Temp-Total-Units.
     perform  varying A from 1 by 1 until A > 4
              move     spaces to Print-Line
              if       A = 1
                       move    "Units:" to PD3-Title
              end-if
              if       WS-Earn-Desc (A) (1:4) not = spaces
                       move     WS-Earn-Desc  (A) to PD3-Desc
                       move     ":"               to PD3-Colon
                       move     WS-Earn-Units (A) to PD3-Units
                       add      WS-Earn-Units (A) to WS-Temp-Total-Units
                       write    Print-Detail-3 after 1
                       add      1  to Line-Counter
                       add      WS-Units (A) to WS-Units-Total
                       exit perform cycle
              end-if
              exit perform
     end-perform
     if       WS-Earn-Desc (2) (1:4) not = spaces
              move     spaces to Print-Line
              move     "Total Units:" to PD4-Title
              move     WS-Total-Units to PD4-Units
              write    Print-Detail-4 after 1
              add      1  to Line-Counter
              move     spaces to Print-Line.
*> 11250
     add      WS-Tips WS-Other-Earn WS-Reg-Wages to WS-Gross.
     add      WS-Gross WS-EIC to WS-Net
     subtract WS-FWT WS-SWT WS-LWT WS-Fica WS-SDI WS-Other-Ded from WS-Net.
     move     WS-Gross-Tips-Reported to WS-Gross.    *> Why overwrite gross ?
*>



*>
     generate Employee-Detailed-Bottom.  *> The rest  from REG WAGES line + 2


*>
 ba000-Exit.   exit section.
*>
 ca000-Routines               section.  *> May be enbedded ??
*>***********************************
*>
 ca000-6100                   section. *> USED
*>***********************************
     move     "Exempt from: " to WS-Exemptions.
     move     14  to C.
     if       Emp-FWT-Exempt = "Y"
              string   "FWT," into WS-Exemptions pointer C.
     if       Emp-SWT-Exempt = "Y"
              string   "SWT," into WS-Exemptions pointer C.
     if       Emp-LWT-Exempt = "Y"
              string   "LWT," into WS-Exemptions pointer C.
     if       Emp-FICA-Exempt = "Y"
              string   "FICA," into WS-Exemptions pointer C.
     if       Emp-SDI-Exempt = "Y"
              string   "SDI," into WS-Exemptions pointer C.
     if       Emp-CO-FUTA-Exempt = "Y"
              string   "CO-FUTA," into WS-Exemptions pointer C.
     if       Emp-CO-SUI-Exempt = "Y"
              string   "CO-SUI," into WS-Exemptions pointer C.
     perform  varying F from 1 by 1 until F > 5
              if       Emp-SYS-Exempt (F) = "Y"
                       string   "SYS"
                                 F
                                 ","
                                into WS-Exemptions pointer C
                       end-string
     end-perform.
     if       C > 14
         and  WS-Exemptions (C - 1:1) = ","
              move     space to  WS-Exemptions (C - 1:1).  *> remove last comma
     if       C = 14
              move     spaces to WS-Exemptions (1:12)
     end-if.
*>
 ca000-8100                   section. *> USED
*>***********************************
*>	Accumulate pay info
*>
*> This routine will accumulate the pay-amt & Units that has just been read in.
*>
*> Accumulation is based on the value of the PAY.REPORTING.CAT% variable.
*> Note that there is no rate zero, but all other VALID rates are accumulated.
*>
     evaluate Pay-Reporting-Cat
     when = 1  add     Pay-Units to WS-Units (1)
               add     Pay-Amt   to WS-Reg-Wages
*>
     when = 2 or = 3 or = 4
               add 	   Pay-Units to WS-Units (Pay-Reporting-Cat)
               add     Pay-Amt   to WS-Other-Earn

     when = 5  add     Pay-Units to WS-Vac-Taken
     when = 6  add     Pay-Units to WS-SL-Taken
     when = 7  add     Pay-Units to WS-Comp-Taken
     when = 8  add     Pay-Units to WS-Comp-Earned
     when = 9 or = 11 or = 12 or = 13 or = 14 or = 15 or = 17
               add     Pay-Amt   to WS-Other-Earn
     when = 10 add     Pay-Amt   to WS-Tips
     when = 16 add     Pay-Amt   to WS-EIC
     when = 18 add     Pay-Amt   to WS-Tips
                                    WS-Tips-Reported
                                    WS-Other-Ded

     when = 20 or = 28
               add     Pay-Amt   to WS-FWT
     when = 21 or = 29
               add     Pay-Amt   to WS-SWT
     when = 22 or = 30
               add     Pay-Amt   to WS-LWT
     when = 23 or = 31
               add     Pay-Amt   to WS-FICA
     when = 24 add     Pay-Amt   to WS-SDI
     when = 27 add     Pay-Amt   to WS-Other-Ded
     when = 33 or 34 or 35 or 36 or 37
               add     Pay-Amt   to WS-Sys (Pay-Reporting-Cat - 32)
               if      Ded-Sys-Earn-Ded (Pay-Reporting-Cat - 32) = "E"
                       add  Pay-Amt  to WS-Other-Earn
               else
                       add  Pay-Amt  to WS-Other-Ded
               end-if
     when = 38 or 39 or 40
               add     Pay-Amt   to WS-Emp (Pay-Reporting-Cat - 37)
               if      Emp-Ed-Earn-Ded (Pay-Reporting-Cat - 37) = "E"
                       add  Pay-Amt  to WS-Other-Earn
               else
                       add  Pay-Amt  to WS-Other-Ded
               end-if
     when = 42 add  Pay-Amt  to WS-CO-Fica
                                WS-Employer-Cost
     when = 43 add  Pay-Amt  to WS-CO-Futa
                                WS-Employer-Cost
     when = 44 add  Pay-Amt  to WS-CO-SUI
                                WS-Employer-Cost
     end-evaluate.
*>
 ca000-9150         section.
*>*************************
*> 9150	get detail description
*>
     if       Pay-Reporting-Cat > zero and < 5
              move     PY-PR1-Rate-Name (Pay-Reporting-Cat)
                                        to WS-Detail-Description
     else
*>
      if      Pay-Reporting-Cat > 32 and < 38
              subtract 32 from  Pay-Reporting-Cat giving B
              move     Ded-Sys-Desc (B) to WS-Detail-Description
              if       WS-Earn-Used not < WS-Option-Chk-Size
                       perform  ca000-Error-1            *> Will goback with err code 32
              end-if
*>
              if       Ded-Sys-Earn-Ded (B) = "E"
                       add      1        to WS-Earn-Used
                       if       WS-Earn-Used > WS-Option-Chk-Size
                                perform  ca000-Error-1            *> Will goback with err code 32
                       end-if
                       move     WS-Detail-Description  to WS-Earn-Desc (WS-Earn-Used)
                       move     Pay-Amt                to WS-Earn-Amt (WS-Earn-Used)
                       move     Pay-Units              to WS-Earn-Units (WS-Earn-Used)
              else
               if      Ded-Sys-Earn-Ded (B) = "D"
                       add      1 to WS-Ded-Used    *> Size = 16 so should never happen unless range of cats increased > 16
                       if       WS-Ded-Used > WS-Option-Chk-Size
                                perform  ca000-Error-1
                       end-if
                       move     WS-Detail-Description  to WS-Ded-Desc (WS-Ded-Used)
                       move     Pay-Amt                to WS-Ded-Amt (WS-Ded-Used)
               end-if
              end-if
      else
       if     Pay-Reporting-Cat > 37 and < 41
              subtract 37 from Pay-Reporting-Cat giving B
              move     Emp-ED-Desc (B)  to WS-Detail-Description
              add      1 to WS-Ded-Used
              if       WS-Ded-Used > WS-Option-Chk-Size
                       perform  ca000-Error-1
              end-if
              move     Pay-Amt               to WS-Ded-Amt (WS-Ded-Used)
              move     WS-Detail-Description to WS-Ded-Desc (WS-Ded-Used)
       else  *> Assuming here all else is for Other ???
              add      1 to WS-Other-Used
              if       WS-Other-Used > WS-Option-Chk-Size
                       perform  ca000-Error-1
              end-if
*>
              move     WS-ED-Desc (Pay-Reporting-Cat) to WS-Other-Desc (WS-Other-Used)      *> WS-Detail-Description.
              move     Pay-Amt               to WS-Other-Amt (WS-Other-Used).
*>
*> 9170 ---- Anything else to do with these ?????
     if       Pay-Reporting-Cat > 4 and < 9
              move     Pay-Units to Pay-Amt
     end-if.
*>
 9150-exit.   exit section.
*>


*> 01  WS-Emp-Accumulator.     *> For print lines with Earnings, Deductions and Others - Reset for new Emp;
*>     03  WS-Option-Clk-Size       binary-char       value 16.  *> MUST be same # as Next occurs
*>     03  WS-Earn-Used             binary-char.*> set up by 1 for all inst
*>     03  WS-Ded-Used              binary-char.*> set up by 1 for all inst
*>     03  WS-Other-Used            binary-char.     *> set up by 1 for all inst
*>     03  WS-All-Option-Block                      occurs 16.    *> Over sized.
*>         05  WS-Earn-Amt          pic s9(7)v99     comp-3.
*>         05  WS-Earn-Units        pic s9(7)v99     comp-3.
*>         05  WS-Earn-Desc         pic x(15).
*>         05  filler               pic xxx.       *> WB
*>
*>         05  WS-Ded-Amt           pic s9(7)v99     comp-3.
*>         05  WS-Ded-Desc          pic x(15).
*>
*>         05  WS-Other-Amt         pic s9(7)v99     comp-3.
*>         05  WS-Other-Desc        pic x(15).

*>
 ca000-11110                  section.
*>***********************************
     move     "*** NET PAY EXCEEDS EMPLOYEE MAXIMUM" to Print-Line.
     write    Print-Line after 1.
     add      1 to Line-Counter.
*>
 ca000-11120                  section.
*>***********************************
     move     PY765  to Print-Line.
     write    Print-Line after 1.
     add      1 to Line-Counter.
*>
 ca000-11130                  section.
*>***********************************
     move     PY767  to Print-Line.
     write    Print-Line after 1.
     add      1 to Line-Counter.
*>
 ca000-11250                  section.
*>***********************************



 ca000-12500                  section.
*>***********************************
*>
*>  -----distribute offset amounts--------------------
*>
*>               DR		       CR
*>	EARNINGS     DIST(+)       CASH(-)
*>	WITHHELD	 CASH(+)       LIAB.ACCT(+)
*>	CO.COSTS	 DIST(+)       LIAB.ACCT(+)
*>	EIC	         LIAB(-)       CASH(-)
*>
*>	CASH acct is from PR1
*>	DIST accts are from EMP record
*>	LIAB accts are from EMP record and DED file
*>	EIC.CREDIT.ACCT (LIAB) is from DED file
*>
*> Calculate Earnings:
*>
     if       PY-PR1-Offset-Cash-Acct  not = zero
              subtract WS-Gross from  WS-Acct-Amt (PY-PR1-Offset-Cash-Acct).
*>
*> Calculate Withholding:
*>
     add      WS-FWT  to WS-Acct-Amt (Ded-Fwt-Acct-No).
     add      WS-SWT  to WS-Acct-Amt (Ded-Swt-Acct-No).
     add      WS-LWT  to WS-Acct-Amt (Ded-Lwt-Acct-No).
     add      WS-Fica to WS-Acct-Amt (Ded-Fica-Acct-No).
     add      WS-SDI  to WS-Acct-Amt (Ded-SDI-Acct-No).
     add      WS-FWT
              WS-SWT
              WS-LWT
              WS-Fica
              WS-SDI        to WS-Total-Withhold.
*>
     perform  varying A from 1 by 1 until A > PY-PR1-Max-Sys-Eds
              if       Ded-Sys-Earn-Ded (A) = "D"
                       add      WS-Acct-Amt (Ded-Sys-Acct-No (A))
                                WS-Sys (A)
                                WS-Total-Withheld
                                  to WS-Acct-Amt (Ded-Sys-Acct-No (A))
                       add      WS-Sys (A) to  WS-Total-Withheld
     end-perform
     perform  varying A from 1 by 1 until A > PY-PR1-Max-Emp-Eds
              if       Ded-Ed-Earn-Ded (A) = "D"
                       add      WS-Acct-Amt (Emp-Ed-Acct-No (A))
                                WS-Emp (A)
                                  to WS-Acct-Amt (Emp-Ed-Acct-No (A))
                       add      WS-Emp (A) to  WS-Total-Withheld
     end-perform
     add      WS-Total-Witheld    to WS-Acct-No (PY-PR1-Offset-Cash-Acct)
*>
*> Calculate EIC:
*>
     subtract WS-EIC from WS-Acct-No (Ded-Eic-Acct-No).
     subtract WS-EIC from WS-Acct-No (PY-PR1-Offset-Cash-Acct).
*>
*> Calculate Company Costs:
*>
     add      WS-Co-Fica          to WS-Acct-No (Ded-Co-Fica-Acct-No).
     add      WS-Co-Futa          to WS-Acct-No (Ded-Co-Futa-Acct-No).
     add      WS-Co-Sui           to WS-Acct-No (Ded-Co-Sui-Acct-No).
*>
 ca000-12700                  section.
*>***********************************
*>
*> Accumulate company totals
*>
     add      WS-Reg-Wages      to WS-Total-Reg-Wages.
     add      WS-Other-Earn     to WS-Total-Other-Earn.
     add      WS-Tips           to WS-Total-Tips.
     add      WS-Tips-Reported  to WS-Total-Tips-Reported.
     add      WS-FWT            to WS-Total-FWT.
     add      WS-SWT            to WS-Total-SWT.
     add      WS-LWT            to WS-Total-SWT.
     add      WS-FICA           to WS-Total-FICA.
     add      WS-SDI            to WS-Total-SDI.
     add      WS-Other-Ded      to WS-Total-Other-Ded.
     add      WS-Net            to WS-Total-Net.
     add      WS-Eic            to WS-Total-Eic.
     add      WS-Co-Fica        to WS-Total-Co-Fica.
     add      WS-Co-Futa        to WS-Total-Co-Futa.
     add      WS-Co-Sui         to WS-Total-Co-Sui.
     add      WS-Vac-Taken      to WS-Total-Vac-Taken.
     add      WS-SL-Taken       to WS-Total-SL-Taken.
     add      WS-Comp-Taken     to WS-Total-Comp-Taken.
     add      WS-Comp-Earned    to WS-Total-Comp-Earned.
     perform  varying A from 1 by 1 until A > 4
              add      WS-Units (A) to WS-Total-Units (A)
     end-perform.
*>
 ca000-11300                  section.
*>***********************************
*> -----calc distribution and accum------------------
 ca000-11310.
*> -----determine distributable pay------------------
*>
     add      WS-Gross WS-Employer-Cost giving WS-Distributable-Pay.
     perform  varying A from 1 by 1 until A > PY-PR1-Max-Dist-Acct
              if       Emp-Dist-Percent (A) not = zero
                       compute WS-Dist-Out (A) rounded = (Emp-Dist-Percent (A) / 100) * WS-Distributable-Pay
              end-if
     end-perform.
     perform  forever    *>  assure that dist amts are exact  11320
              move     zero to WS-Temp
              perform  varying  B from 1 by 1 until B > PY-PR1-Max-Dist-Accts
                       add      WS-Dist-Out (B) to WS-Temp
              end-perform
              if       WS-Temp = WS-Distributable-Pay
                       exit perform
              end-if
              subtract WS-Temp from WS-Distributable-Pay giving WS-Temp
              perform  varying  B from 1 by 1 until B > PY-PR1-Max-Dist-Acct
                       add      WS-Temp to WS-Dist-Out (B)


                       add      WS-Dist-Out (B) to WS-Acct-Amt (Enp-Dist-Acct) (B)

  THIS MAKE NO SENSE  -REVISIT

     end-perform

	gosub 11320			rem coding

	for x%=1 to pr1.max.dist.accts%
		acct.amt(emp.dist.acct%(x%))=		\
			acct.amt(emp.dist.acct%(x%))+	\
			dist.out(x%)
	next x%
	return


11320	rem-----assure that dist amts are exact--------------
	temp=0
	for x%=1 to pr1.max.dist.accts%
		temp=temp+dist.out(x%)
	next x%
	if temp=distributable.pay \
		then	return
	temp=distributable.pay-temp	rem temp is difference
	x%=1
	while emp.dist.percent(x%)=0
		x%=x%+1
	wend
	dist.out(x%)=dist.out(x%)+temp
	return

 ca000-11310                  section.
*>***********************************


 ca000-11320                  section.
*>***********************************


 ca010-Check-Date-2-Formatted section. *> USED
     move     PY-PR2-Check-Date to WS-Temp-Date9.
     perform  zz070-Convert-Date.
     move     WS-Date to WS-Check-Date.
*>
 ca020-From-Date-2-Formatted  section.
*>***********************************
*> 6250
     if       (PY-PR1-S-Used = "Y" and   PY-PR1-M-Used = "Y")
        or    (PY-PR1-W-Used = "Y" and   PY-PR1-B-Used = "Y")
              move     "Y" to WS-Fast-and-Slow
     else
              move     "N" to WS-Fast-and-Slow.
*>
     if       WS-Fast-and-Slow = "N" *> 6255
              if       Pay-Hdr-Interval = "S" or = "W"
                       move     Chk-Hdr-Fast-From-Date to WS-Temp-Date9
              end-if
              if       Pay-Hdr-Interval = "B" or = "M"
                       move     Chk-Hdr-Slow-From-Date to WS-Temp-Date9
              end-if
              perform  zz070-Convert-Date
              move     WS-Date to WS-Check-Date
              go to ca020-exit
     end-if
     if       Pay-Hdr-Interval = "M" and PY-PR1-S-Used = "Y"
        or    Pay-Hdr-Interval = "B" and PY-PR1-W-Used = "Y"
              move     Chk-Hdr-Slow-From-Date to WS-Temp-Date9
     else
              move     Chk-Hdr-Fast-From-Date to WS-Temp-Date9
     end-if
     perform  zz070-Convert-Date.
     move     WS-Date to WS-Rep-From-Date.
*>
 ca020-Exit.  exit section.
*>
 ca000-Error-1                section.
*>***********************************
     if       WS-Earn-Used > WS-Option-Chk-Size
              display  PY776 at line WS-22-Lines col 1 foreground-color 4
              display  SY001 at line WS-23-Lines col 1
              accept   WS-Reply at line WS-23-Lines col 48
              close    PY-Pay-File
                       PY-Check-File
                       PY-System-Deduction-File
                       PY-Accounts-File
                       PY-Employee-File
                       PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 32.           *> MUST not happen
*>
 ca030-To-Date-2-Formatted    section. *> USED
*>***********************************
     move     Chk-Hdr-To-Date to WS-Temp-Date9.
     perform  zz070-Convert-Date.
     move     WS-Date to WS-Rep-To-Date.
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
*> aa050-Report-Vacation     section.   *> REPLACE ALL
*>********************************
*>
*> At this point Emp is opened for input and Print-File for output.
*>
*>     move     zero to WS-Rec-Cnt.
*>     subtract 1 from Page-Lines giving WS-Page-Lines.  *> Could be the same ??  <<<<
*>
 *>    initiate Employee-Detailed-Journal-Report.
 *>    perform  forever
 *>             read     PY-Employee-File next record
 *>             if       PY-Emp-Status not = "00"   *> EOF
 *>                      exit perform
 *>             end-if
 *>             add      1 to WS-Rec-Cnt
 *>             generate Emp-Detail
 *>    end-perform.
 *>    terminate
 *>             Employee-Detailed-Journal-Report.
*>
 *> aa050-Exit.  exit section.
*>
 zz070-Convert-Date          section.
*>**********************************
*>   Routine changed for program
*>
*>  Input:  WS-Temp-Date9 in ccyymmdd.
*> Output:  WS-Date      in locale format defined by PY-PR1-Date-Format
*>
     move     WS-Temp-Year  to WS-Year.
     if       PY-PR1-Date-Format = 2   *> USA
              move     WS-Temp-Month to WS-USA-Month
              move     WS-Temp-Days  to WS-USA-Days
     else                               *> UK - dd/mm/ccyy
              move     WS-Temp-Month to WS-Month
              move     WS-Temp-Days  to WS-Days.
*>
 zz070-Exit.
     exit     section.
*>
