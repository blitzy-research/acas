       >>source free
*>****************************************************************
*>               Print 941 Forms on plain paper for              *
*>                 selected employees.                           *
*>                                                               *
*>   Temp program name may be py220 - coding from prnt941,941b   *
*>                                                               *
*>     Program uses RW - Report Writer. for 941b                 *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       print941.
*>**
      Author.           Vincent B Coen FBCS, FIDM, FIDPM, 28/03/2026.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Print Form 941 Report for end of year processing.
*>                      Semi-sourced from Basic code from print941,941b.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.   NONE other than SYSTEM to lpr.
*>**
*>    Functions Used:   NONE.
*>
*>    Files used :
*>                      pypr1.   Params  for PR2 data
*>                      pycoh.   Company History.
*>
*>    Error messages used.
*> System wide:
*>                      SY00.
*> Program specific:
*>                      PY00
*>                      PY
*>**
*> Changes:
*> 28/03/2026 vbc - 1.0.00 Coding starting.
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
 copy "selpycoh.cob".
*> copy "selpyemp.cob".
*> copy "selpyhis.cob".
*>
 copy "selprint.cob".    *> 132
*>
 data                    division.
*>================================
*>
 file section.
*>
 copy "fdpyparam1.cob".
 copy "fdpycoh.cob".
*> copy "fdpyemp.cob".
*> copy "fdpyhis.cob".
*>
 fd  Print-File
     report is 941-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "PRINT941 (1.0.00)".  *> First release pre testing. Prog name will be changed.
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
     03  PY-Coh-Status       pic xx       value zero.
 *>    03  PY-Emp-Status       pic xx       value zero.
 *>    03  PY-His-Emp-Status   pic xx       value zero.
*>
     03  WS-Reply            pic x.
     03  WS-Action           pic x        value space. *> Q(quit), B(ack) or C(ontinue)
         88  WS-Back                      value "B".
         88  WS-Continue                  value "C".
         88  WS-Quit                      value "Q".
         88  WS-Action-Valid              values "B" "C" "Q".
*>
     03  WS-Eval-Msg         pic x(25)    value spaces.
     03  WS-Env-Columns      pic 999      value zero.
     03  WS-Env-Lines        pic 999      value zero.
     03  WS-22-Lines         pic 99.
     03  WS-23-Lines         pic 99.
     03  WS-Lines            pic 99.
     03  A                   pic 99       value zero. *> used
     03  B                   pic 99       value zero. *> not used Yet
     03  C                   pic 99       value zero. *> not used Yet
     03  WS-Page-Lines       binary-char unsigned value 56. *> Narrow reports as system is for Landscape used.
     03  WS-Rec-Cnt          pic 99       value zero.
     03  WS-Page-Cnt         pic 999      value zero.
     03  WS-Line-Cnt         pic 999      value 90.         *> Force heads at start
*>
*>  Tables
*>
     03  WS-E-Qtrs.   *> NEEDED ?
         05  filler          pic 9(8)     value 00000331.
         05  filler          pic 9(8)     value 00000630.
         05  filler          pic 9(8)     value 00000930.
         05  filler          pic 9(8)     value 00001231.
     03  WS-Ending-Quarters redefines WS-E-Qtrs
                              occurs 4.
         05  WS-E-Q-Year     pic 9(4).      *> Needs to be preloaded with current year x 4
         05  WS-E-Q-mmdd     pic 9(4).
     03  WS-Qtr-1            pic x        value space.  *> Set to X for current qtr before printing.
     03  WS-Qtr-2            pic x        value space.  *> ditto  OR set to Y or N
     03  WS-Qtr-3            pic x        value space.  *> ditto
     03  WS-Qtr-4            pic x        value space.  *> ditto
*>
     03  WS-OK               pic x         value space.
     03  WS-Yr               pic 9(4).
     03  WS-Print-Name       pic x        value space.

     03  WS-Less-Than-2500   pic x        value space.
     03  WS-Monthly-Depositr pic x       value space.
*>
*> 01  WS-Process-Flags.
*>
     03  WS-Year-End         pic x        value "N".
     03  WS-End-of-Qtr       pic 9(8).    *> ccyymmdd
     03  WS-Qtr-End redefines WS-End-of-Qtr.
         05  WS-EoQ-Year     pic 9(4).
         05  WS-EoQ-Month    pic 99.
         05  WS-EoQ-Day      pic 99.
     03  WS-Common-Date      pic 9(8).    *> ccyymmdd of To-Day which is Local / default date format.
     03  WS-Deposit-End-Date.
         05  WS-DED-Month    pic 99       value zero.
         05  filler          pic x        value "/".
         05  WS-DED-Day      pic 99       value zero.
         05  filler          pic x        value "/".
         05  WS-DED-Year     pic 9(4)     value zero.
*>
*> Date variables etc
*>
 01  WS-Accumulator-Fields       value zeros.   *> NEEDED ??
     03  WS-Sub-EIC          pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-FWT          pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-FICA         pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-FICA-Gross   pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-Tips         pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-SWT          pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-LWT          pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-MCARE        pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-Gross        pic s9(7)v99   comp-3. *> ?
     03  WS-Sub-Totals       pic s9(7)v99   comp-3. *> ?

     03  WS-Adj-FICA-Tax     pic s9(7)v99   comp-3.   *> blk 91 + 92
     03  WS-Adj-Total-Inc-Tax-With
                             pic s9(7)v99   comp-3.
     03  WS-EIC              pic s9(7)v99   comp-3.
     03  WS-FICA-Adj         pic s9(7)v99   comp-3.
     03  WS-FICA-Non-Tip-Tax pic s9(7)v99   comp-3.
     03  WS-FICA-Tips-Tax    pic s9(7)v99   comp-3.
     03  WS-Net-Taxes        pic s9(7)v99   comp-3.
     03  WS-Prev-Qtr-Adj     pic s9(7)v99   comp-3.
     03  WS-Total-FICA-Tax   pic s9(7)v99   comp-3.
     03  WS-Total-Taxes      pic s9(7)v99   comp-3.
     03  WS-Tot-Subj-To-With pic s9(7)v99   comp-3.
     03  WS-No-of-Employees  pic zz,zz9.
     03  WS-Overpay          pic s9(7)v99   comp-3.
     03  WS-Real-Tot         pic s9(7)v99   comp-3.
     03  WS-Final-Tot        pic s9(7)v99   comp-3.
     03  WS-New-Overpay      pic s9(7)v99   comp-3.
     03  WS-Taxes-Due        pic s9(7)v99   comp-3.
     03  WS-First-Mo         pic s9(7)v99   comp-3.
     03  WS-Second-Mo        pic s9(7)v99   comp-3.
     03  WS-Third-Mo         pic s9(7)v99   comp-3.
     03  WS-Final-Date       pic x(10).           *> might be ccyymmdd
     03  WS-Final-Del        pic s9(7)v99   comp-3.
     03  WS-Real-First-Mo    pic s9(7)v99   comp-3.
     03  WS-Real-Second-Mo   pic s9(7)v99   comp-3.
     03  WS-Real-Third-Mo    pic s9(7)v99   comp-3.
     03  WS-Real-Coh-Tax     pic s9(7)v99   comp-3.
     03  WS-Total-For-Qtr    pic s9(7)v99   comp-3.
     03  WS-Real-Total-For-Qtr
                             pic s9(7)v99   comp-3.
     03  WS-Grand-Total-For-Qtr
                             pic s9(7)v99   comp-3.
     03  WS-Final-Dep-Date   pic 9(8).
     03  WS-Final-Deposit    pic s9(7)v99   comp-3.
*>
*>
 01  WS-Emp-Temp-Fields-for-RW.
     03  Tmp-his-ytd-gross   pic s9(9)v99   comp-3.    *> Temp field not in the HIS file record
     03  Tmp-his-ytd-fica-gross
                             pic s9(9)v99   comp-3.    *> Temp field not in the HIS file record
*>
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
     copy "an-accept.ws".  *> Support WS for ACCEPT_NUMERIC routine
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
     03  PY601           pic x(48) value "PY601 System has not achieved Quarter End status".
     03  PY602           pic x(24) value "PY602 PR2 file not found".
     03  PY603           pic x(24) value "PY603 COH file not found".
     03  PY604           pic x(33) value "PY604 Unable to write PR2 File - ".
*>
     03  PY605           pic x(55) value "PY605 Bad value in PR2-Last-Q-Ended - BUG - Aborting - ".
*>
     03  PY608           pic x(31) value "PY608 Error Reading COH File - ".
     03  PY609           pic x(31) value "PY609 Error Reading PR2 File - ".
     03  PY610           pic x(33) value "PY610 Error Rewriting COH File - ".
     03  PY611           pic x(33) value "PY611 Error Rewriting PR2 File - ".

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
 RD  941-Report
     control      Final
     Page Limit   WS-Page-Lines
     First Detail 3
     Last  Detail WS-Page-Lines.
*>
*> WARNING: Line # and Col #  can change from year to year for all fields
*>  and this section may well need changes when the new W-2 form becomes available
*>
*>  Line offset based on above First Detail number and is always subject to
*>  testing - i.e., running a test print.
*>
*>  Therefore these layouts may well need changes and the program recompiled to
*>  match up with any new W-2 forms. Same applies to ALL form layouts.
*>
*>  MAY ONLY apply when printing on to pre-printed stationary
*>
 01  941-Detail type is detail.    *> REPEAT generate WS-RS-Emp-Forms-Cnt TIMES
*>                                   2026 form BUT it is not printer friendly
*>                                    eg not 10 per inch ditto 6 lines per inch.
     03  line 5.
         05  col  19         pic x(15)        source PY-PR1-Fed-ID.
     03  line 7.
         05  col  17         pic x(34)        source PY-PR1-Co-Name.
         05  col  56         pic x            value "X" present when WS-Qtr-1 = "Y".
     03  line 8.
         05  col  56         pic x            value "X" present when WS-Qtr-2 = "Y".
     03  line 9.
         05  col  15         pic x(36)        source PY-PR1-Trade-Name.
     03  line 10.
         05  col  56         pic x            value "X" present when WS-Qtr-3 = "Y".
     03  line 11.
         05  col  10         pic x(32)        source PY-PR1-Co-Address-1.
         05  col  56         pic x            value "X" present when WS-Qtr-4 = "Y".
     03  line 12.
         05  col  10         pic x(32)        source PY-PR1-Co-Address-2.
     03  line 13.
         05  col  10         pic x(32)        source PY-PR1-Co-Address-3.
         05  col  36         pic xx           source PY-PR1-Co-State.
         05  col  42         pic x(10)        source PY-PR1-Co-Zip.
     03  line 16 col 10      pic x(32)        source PY-PR1-Co-Address-4
                                               present when PY-PR1-Co-Address-4  not = spaces.
     03  line 23 col 59      pic zz,zz9       source PY-PR2-No-Active-Emps.
     03  line 25 col 59      pic z,zzz,zz9.99 source WS-Tot-Subj-To-With. *> wages,tips and other compens
     03  line 27 col 59      pic z,zzz,zz9.99 source Coh-QTD-Fwt-Liab.    *> Fed income tax withheld
     03  line 31.  *> taxable SS wages
 *>        05  col  28         pic z,zzz,zz9.99 source   *> 5a
 *>        05  col  47         pic z,zzz,zz9.99 source
 *>    03  line 32.  *> taxable SS tips
 *>        05  col  28         pic z,zzz,zz9.99 source   *> 5b
 *>        05  col  47         pic z,zzz,zz9.99 source
 *>    03  line 34.  *> taxable mcare wages & tips
 *>        05  col  28         pic z,zzz,zz9.99 source   *> 5c
 *>        05  col  47         pic z,zzz,zz9.99 source
 *>    03  line 36.  *> taxable wages/tips subj xtra mcare tax withholding -
 *>        05  col  28         pic z,zzz,zz9.99 source   *> 5d
 *>        05  col  47         pic z,zzz,zz9.99 source
 *>    03  line 38  col  59    pic z,zzz,zz9.99 source   *>  5e
 *>    03  line 40  col  59    pic z,zzz,zz9.99 source   *>  5f
 *>    03  line 41  col  59    pic z,zzz,zz9.99 source   *>  6
 *>    03  line 43  col  59    pic z,zzz,zz9.99 source   *>  7
 *>    03  line 44  col  59    pic z,zzz,zz9.99 source   *>  8
 *>    03  line 46  col  59    pic z,zzz,zz9.99 source   *>  9
 *>    03  line 47  col  59    pic z,zzz,zz9.99 source   *>  10
 *>    03  line 49  col  59    pic z,zzz,zz9.99 source   *>  11
 *>    03  line 50  col  59    pic z,zzz,zz9.99 source   *>  12
 *>    03  line 52  col  59    pic z,zzz,zz9.99 source   *>  13
 *>    03  line 54  col  59    pic z,zzz,zz9.99 source   *>  14
 *>    03  line 55.
 *>        05  col  38    pic zzz9.99      source   *>  15a
 *>        05  col  59    pic x            source   *> X apply to next return
 *>        05  col  65    pic x            source   *> X send a refund
*>
     03  line 4 on next page.
         05  col   4    pic x(50)        source PY-PR1-Co-Name.
         05  col  53    pic x(15)        source PY-PR1-Fed-ID.
     03  line 8.  *> this or next option NOT BOTH
         05  col  13    pic x            value "X" present when WS-Less-Than-2500 = "Y".
     03  Box-16                                    present when WS-Monthly-Depositr = "Y".
         05  line 12  col  13    pic x   value "x" present when WS-Monthly-Depositr = "Y".
 *>        05  line 15  col  30    pic z,zzz,zz9.99 source    *> tax liab mth 1 in current qtr
 *>        05  line 17  col  30    pic z,zzz,zz9.99 source    *> tax liab mth 2 in current qtr
 *>        05  line 18  col  30    pic z,zzz,zz9.99 source    *> tax liab mth 3 in current qtr
 *>        05  line 20  col  30    pic z,zzz,zz9.99 source    *> Total liab for qtr MUST = box 12
*>
*> Rest is written by hand0
*>

         05  line + 1.
             07  col  16         pic x(32)        source PY-PR1-Co-Address-4.
             07  col  41         pic xx           source Coh-QTD-FICA-Taxable. *> Fed in.tax withheld all wages


     03  No-Comp-Address present when  WS-Print-Name = "N".
         05  line 5.
             07  col   1         pic x            value space.
*>
  *>   03  line + 2.
  *>       05  col  69   *>   ?????????
     03  line + 1.
         05  col  69             pic z,zzz,zz9.99 source Coh-QTD-FWT-Liab.
     03  line + 1.
         05  col   7                              value "(".
         05  col   8             pic z,zzz,zz9.99 source WS-Prev-QTR-Adj. *> should be ABS to make it neg
         05  col  20                              value ")".
     03  line + 1
         05  col  69             pic z,zzz,zz9.99 source WS-Adj-Total-Inc-Tax-With.
     03  line + 1.
         05  col  37             pic z,zzz,zz9.99 source Coh-QTD-FICA-Taxable.
         05  col  69                              value "(".
         05  col  70             pic z,zzz,zz9.99 source WS-FICA-Non-Tip-Tax.
         05  col  82                              value ")".
     03  line + 1.
         05  col  37             pic z,zzz,zz9.99 source Coh-QTD-Tips.
         05  col  69                              value "(".
         05  col  70             pic z,zzz,zz9.99 source WS-FICA-Tips-Tax.
         05  col  82                              value ")".
     03  line + 1 col  69        pic z,zzz,zz9.99 source WS-Total-FICA-Tax.
     03  line + 1.
         05  col  69                              value "(".
         05  col  70             pic z,zzz,zz9.99 source WS-FICA-Adj.
         05  col  82                              value ")".
     03  line + 1
         05  col  69             pic z,zzz,zz9.99 source WS-Adj-FICA-Tax.
     03  line + 1.
         05  col  69             pic z,zzz,zz9.99 source WS-Total-Taxes.
     03  line + 1.
         05  col  69                              value "(".
         05  col  70             pic z,zzz,zz9.99 source Coh-QTD-EIC-Credit.
         05  col  82                              value ")".
     03  line + 1.
         05  col  69             pic z,zzz,zz9.99 source WS-Net-Taxes.
     03  line 1 on next page.   *> End-of Qtr
         05  col  20             pic 99           source WS-EoQ-Month present when PY-PR1-Date-Format = 2.
         05  col  20             pic 99           source WS-EoQ-Day   present when PY-PR1-Date-Format = 1.
         05  col  22                               value "/".
         05  col  23             pic 99           source WS-EoQ-Day   present when PY-PR1-Date-Format = 2.
         05  col  23             pic 99           source WS-EoQ-Month present when PY-PR1-Date-Format = 1.
         05  col  25                               value "/".
         05  col  26             pic 9(4)         source WS-EoQ-Year.
     03  line + 1.
         05  col  56             pic z,zzz,zz9.99 source WS-Overpay.
     03  line + 1.
 *>        05  col  34             pic z,zzz,zz9.99 source

         05  col  34             pic z,zzz,zz9.99 source Coh-Tax (1).
 *>        05  col  46             pic z,zzz,zz9.99 source
 *>        05  col  56             pic z,zzz,zz9.99 source


 *>        05  col  34             pic z,zzz,zz9.99 source



*> 01  W2-Detail type is detail. *> From basic code REPEAT generate WS-RS-Emp-Forms-Cnt TIMES
*>     03  line 3.    *> 310
*>         05  col  26  pic x(15)          source PY-PR1-State-ID.

 screen       section.
*>*******************
*>
*> two lines are replaced with a blanl line as values not required for inkjet/laser printers.
*>  WARNING using RW may not work for such printers - cannot test with these as not used in Development.
*>
 01  SS-Data-Screen1 background-color cob-color-black
                     foreground-color cob-color-green
                     erase eos.
     03  from  Prog-Name  pic x(17)                              line  1 col  1 foreground-color 2.
     03  value "Print 941 Liability"                                     col 29.
     03  from  To-Day     pic x(10)                                      col 71 foreground-color 2.
     03  from  Usera      pic x(32)                              line  2 col  1.
     03  value "Deposit per End"                                                       line  3 col 1.
     03  from  WS-Deposit-End-Date                                                     line  3 col 18.
     03  value "      Liability      Date       Amount"                                line  3 col 28.
     03  value "Overpayment From Previous Quarter.......................  [         ]" line  4 col 1.
     03  value " First     | Days 1 Through 7    nnnnnnn.nn   [          ][         ]" line  5 col 1.
     03  value " Month     | Days 8 Through 15   nnnnnnn.nn   [          ][         ]" line  6 col 1.
     03  value " Of        | Days 16 Through 22  nnnnnnn.nn   [          ][         ]" line  7 col 1.
     03  value " Quarter   | Days 23 Through End nnnnnnn.nn   [          ][         ]" line  8 col 1.
     03  value "   First Month Total:"                                                 line  9 col 1.
     03  value " Second    | Days 1 Through 7    nnnnnnn.nn   [          ][         ]" line 10 col 1.
     03  value " Month     | Days 8 Through 15   nnnnnnn.nn   [          ][         ]" line 11 col 1.
     03  value " Of        | Days 16 Through 22  nnnnnnn.nn   [          ][         ]" line 12 col 1.
     03  value " Quarter   | Days 23 Through End nnnnnnn.nn   [          ][         ]" line 13 col 1.
     03  value "   Second Month Total:"                                                line 14 col 1.
     03  value " Third     | Days 1 Through 7    nnnnnnn.nn   [          ][         ]" line 15 col 1.
     03  value " Month     | Days 8 Through 15   nnnnnnn.nn   [          ][         ]" line 16 col 1.
     03  value " Of        | Days 16 Through 22  nnnnnnn.nn   [          ][         ]" line 17 col 1.
     03  value " Quarter   | Days 23 Through End nnnnnnn.nn   [          ][         ]" line 18 col 1.
     03  value "   Third Month Total:"                                                 line 19 col 1.
     03  value "Total For Quarter:               nnnnnnn.nn   [          ][         ]" line 20 col 1.
     03  value "Final Deposit For Quarter:....................[          ][         ]" line 21 col 1.
     03  value "Total Deposits For Quarter:...............................[         ]" line 22 col 1.
     03  value "Overpayment:....                  Undeposited Taxes Due:..[         ]" line 23 col 1.

     03  value "[ ]"                                                                   line 24 col 10. *> ??

*>
*> This screen processed first
*>
 01  SS-Data-Screen2 background-color cob-color-black
                     foreground-color cob-color-green
                     erase eos.
     03  from  Prog-Name  pic x(17)                              line  1 col  1 foreground-color 2.
     03  value "Print 941 Liability"                                     col 29.
     03  from  To-Day     pic x(10)                                      col 71 foreground-color 2.
     03  from  Usera      pic x(32)                              line  2 col  1.
     03  from PY-PR1-Co-Name       pic x(60)                                            line  4 col  7.*>#1
     03  from WS-Ending-Quarters (PY-PR2-Last-Q-Ended)    pic x(10)                     line  4 col 69.*>#3
     03  from PY-PR1-Fed-ID        pic x(15)                                            line  6 col 67.*>#5
     03  from PY-PR1-Co-Address-1  pic x(32)                                            line  7 col  7.*>#2
     03  from PY-PR1-Co-Address-2  pic x(32)                                            line  8 col  7.*>#4
     03  from PY-PR1-Co-Address-3  pic x(32)                                            line  9 col  7.*>#6
     03  from PY-PR1-Co-Address-4  pic x(32)                                            line 10 col  7.*>#7
     03  from PY-PR1-Co-State      pic xx                                               line 10 col  42.*>#8
     03  from PY-PR1-Co-Zip        pic x(10)                                            line 10 col  45.*>#9
*>
     03  value "Print Name And Address  [ ]"                                            line 11 col 1.
 *>    03  using WS-Print-Name       pic x                                              line 11 col 26. #10
*>
     03  value "01 Number of Employees                                         {        }" line 12 col 1.
     03  from PY-PR2-No-Employees pic z(7)9                                                line 12 col 68. *>#11
     03  value "02 Total Wages and Tips                                     [        .  ]" line 13 col 1.
     03  from  WS-Tot-Subj-To-With  pic z(7)9.99                                           line 13 col 65. *>#12
 *>  from  Coh-QTD-Income-Taxable + Coh-QTD-Tips + Coh-QTD-Other-Taxable + Coh-QTD-Other-NonTaxable
     03  value "03 Total Income Tax Withheld                                [           ]" line 14 col 1.
     03  from  Coh-QTD-FWT-Liab     pic z(7)9.99                                           line 14 col 65. *>#13
     03  value "Adjustment of Withheld Income Tax from Previous Quarters    [           ]" line 15 col 1.
     03  using WS-Prev-Qtr-Adj      pic z(7)9.99                                           line 15 col 65. *>#14US
 *>  prev.qtr.adj  from ZEROS
     03  value "Adjusted Total of Income Tax Withheld                       [           ]" line 16 col 1.
     03  from  WS-Adj-Total-Inc-Tax-With pic z(7)9.99                                      line 16 col 65. *>#15
*>        from  Coh-QTD-FWT-Liab  WS-Prev-QTR-Adj
     03  value "Taxable FICA Wages Paid                                     [           ]" line 17 col 1.
     03  from  Coh-QTD-FICA-Taxable pic z(7)9.99                                           line 17 col 65. *>#16
     03  value "Taxable Tips Reported                                       [           ]" line 18 col 1.
     03  from  WS-FICA-Tips-Tax     pic z(7)9.99                                           line 18 col 65.*>#17
*>  fica.non.tip.tax ABOVE LOOKS WRONG
*> Coh-QTD-Tips * 0.0613
 *>          from Coh-QTD-Fica-Taxable * 0.1226

     03  value "Total FICA Taxes                                            [           ]" line 19 col 1.
     03  from  WS-Total-FICA-Tax    pic z(7)9.99                                           line 19 col 65.*>??#20
 *>   from WS-FICA-Non-Tip-Tax    WS-FICA-Tips-Tax
     03  value "Adjustment of FICA Taxes                                    [           ]" line 20 col 1.
*> ?? adj.fica.tax   fica.tips.tax
     03  using  WS-FICA-ADJ          pic z(7)9.99                                           line 20 col 65.*>#21US
 *>     from zeros
     03  value "Adjusted Total of FICA Taxes                                [           ]" line 21 col 1.
     03  from  WS-Adj-FICA-Tax      pic z(7)9.99                                           line 21 col 65.*>#22
 *>  from WS-FICA-ADJ     WS-Total-FICA-Tax
     03  value "06 Total Taxes                                              [           ]" line 22 col 1.
     03  from  WS-Total-Taxes       pic z(7)9.99                                           line 22 col 65.*>#23
 *>  from  WS-FICA-Adj     WS-Adj-Total-Inc-Tax-With
     03  value "Earned Income Credit                                        [           ]" line 23 col 1.
     03  from  WS-EIC               pic -(7)9.99                                           line 23 col 65.*>#24
 *>   from  (- Coh-QTD-EIC-Credit) ABOVE is SIGNED
     03  value "12 Net Taxes                                                [           ]" line 24 col 1.
     03  from  WS-Net-Taxes         pic z(7)9.99                                           line 24 col 65.*>#25
 *>  From WS-Total-Taxes  WS-EIC
*>
     03  value "Continue (C), Go back (B) or Quit (Q) - [ ]"                               line 25 col 1.
*>  using WS-Action  pic x    2542

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
     if       PY-PR1-Date-Format = 2 *> USA
              move To-Day (1:2) to WS-Common-Date (5:2)  *> mm
              move To-Day (4:2) to WS-Common-Date (7:2)  *> dd
     else              *> UK dd/mm/yyyy
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
*> Pre setup params for accept_numeric routine
*>
     move     zeros to AN-Error-Code
                       AN-Return-Code.
     SET      AN-FG-IS-Green    to TRUE.
     SET      AN-BG-IS-Black    to TRUE.
     SET      AN-FG2-IS-Cyan    to TRUE.
     SET      AN-Mode-IS-Update to TRUE.    *> could be AN-MODE-IS-NO-UPDATE to

*>
*> Set up any presets
*>
     perform  varying A from 1 by 1 until A > 4
              move     PY-PR2-Year to WS-E-Q-Year (A)
     end-perform.

*> Open all files if any missing Abort.
*> For all files other than His-Emp read only record.
*>
     move     1 to RRN.
     open     i-o      PY-Param1-File.
     if       PY-PR1-Status not = "00"      *> Does not exist yet so lets create it & write rec
              display  PY602 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Param1-File
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
     open     i-o PY-Comp-Hist-File.
     if       PY-Coh-Status not = zeros
              display  PY603 at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  SY001 at line WS-Lines    col 1
              accept   WS-Reply at line WS-Lines col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
              move     16 to WS-Term-Code
              goback   returning 2.
*>
     move     1 to RRN.
     read     PY-Comp-Hist-File.
     if       PY-Coh-Status not = "00"
              move     PY-Coh-Status  to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY608         at line WS-23-Lines col 1 with erase eos
              display  PY-PR1-Status at line WS-23-Lines col 32
              display  WS-Eval-Msg   at line WS-23-Lines col 35
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
              move     16 to WS-Term-Code
              goback   returning 3.
*> 15
     move     "Y" to WS-OK.
     move     WS-Common-Date to WS-End-Of-Qtr.        *> ccyymmdd
     move     PY-PR2-Check-Date (1:4)  to WS-Yr.   *> ccyy [mmdd]
     perform  varying A from 1 by 1 until A > 4
              move     WS-Yr to WS-E-Q-Year (A)
     end-perform.
*>
     if       PY-PR2-Last-Q-Ended  < 1 or > 4
              display  PY605               at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  PY-PR2-Last-Q-Ended at line WS-23-Lines col 56
              display  SY001               at line WS-Lines    col 1
              accept   WS-Reply            at line WS-Lines col 48 AUTO
              close    PY-Param1-File
                       PY-Comp-Hist-File
              move     16 to WS-Term-Code
              goback   returning 4.
*>
     move     WS-Ending-Quarters (PY-PR2-Last-Q-Ended) to WS-End-of-Qtr.
*> end 15
 aa090-Zeroise.
*>
*> 90
*>
     move     "Y" to WS-Print-Name.
     move     zeros  to WS-Prev-QTR-Adj
                        WS-Fica-Adj.
 aa091-Compute.
*>
*> 91
*>
     add      Coh-QTD-Income-Taxable Coh-QTD-Tips
              Coh-QTD-Other-Taxable  Coh-QTD-Other-NonTaxable
                    giving WS-Tot-Subj-To-With.
     add      Coh-QTD-FWT-Liab       WS-Prev-QTR-Adj
                    giving WS-Adj-Total-Inc-Tax-With.
     compute  WS-FICA-Non-Tip-Tax = Coh-QTD-Fica-Taxable * 0.1226.
     compute  WS-FICA-Tips-Tax = Coh-QTD-Tips * 0.0613
     add      WS-FICA-Non-Tip-Tax    WS-FICA-Tips-Tax
                    giving WS-Total-FICA-Tax.
 aa092-Compute.
*>
*> 92
*>
     add      WS-FICA-ADJ     WS-Total-FICA-Tax
                    giving WS-Adj-FICA-Tax.
     add      WS-FICA-Adj     WS-Adj-Total-Inc-Tax-With
                    giving WS-Total-Taxes.
     compute  WS-EIC = - Coh-QTD-EIC-Credit.
     add      WS-Total-Taxes  WS-EIC
                    giving WS-Net-Taxes.
*> 500 & 100/110
 aa100-display-screen.
     display  SS-Data-Screen1.
     accept   WS-Print-Name at 1126 UPDATE UPPER.
     if       WS-Print-Name not = "Y"
                        and not = "N"
              display  SY015 at line WS-23-Lines col 1 foreground-color 6
                                     BEEP erase eos
              go to aa100-display-screen
     else
              display  space at line WS-23-Lines col 1 erase eos
     end-if.
*> 111
*> Get Prev-QTR-ADJ   15 col 65
*>
     move     15 to AN-LINE.
     move     65 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Prev-Qtr-Adj
                                            by REFERENCE AN-ACCEPT-NUMERIC.
 *>    perform  AN-Test-Status
 *>    if       COB-CRT-Status = COB-SCR-ESC   *> Quit Sub process
 *>             exit perform
 *>    end-if
     perform  aa091-Compute.
     display  SS-Data-Screen1.
*>
*> 112
*> Get FICA ADJ   15 col 65
*>
     move     20 to AN-LINE.
     move     65 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-FICA-ADJ
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     perform  aa092-Compute.
     display  SS-Data-Screen1.
*>
     perform  forever
              accept   WS-Action at 2542 foreground-color 3 UPPER
              if       not WS-Action-Valid
                       exit perform cycle
              end-if
     end-perform.
     if       WS-Back
              go to aa090-Zeroise.
     if       WS-Quit
              go to ba200-EOJ.
*>
*> Must be continue
*>
 ba000-Phase-2 section.
*>********************
*>100, 550 & 210 then 300 print form
 ba010-Calcs.




     if       WS-End-of-Qtr not = zeros
              move     1 to RRN
              rewrite  PY-Param1-Record
              if       PY-PR1-Status not = zeros
                       display  PY011         at line WS-23-Lines col 1 with erase eos
                       display  PY-PR1-Status at line WS-23-Lines col 33
                       display  WS-Eval-Msg   at line WS-23-Lines col 36
                       display  SY001         at line WS-Lines    col 1
                       accept   WS-Reply      at line WS-Lines    col 48 AUTO
                       close    PY-Param1-File
                                PY-Comp-Hist-File
                       move     16 to WS-Term-Code
                       goback   returning 5.
*>
 ba200-EOJ.
     close    PY-Param1-File.
     close    PY-Comp-Hist-File.
     goback.
*>
 zz000-Common    section.
*>**********************
*>
*> Common routines.
*>
     copy "an-accept.pl".
*>
 ZZ040-Evaluate-Message      Section.
*>**********************************
*>
*> For PY-PR1 parameter file anfd other using PR-PR1-Status.
*>
     copy "FileStat-Msgs-2.cpy" replacing MSG  by WS-Eval-Msg
                                        STATUS by PY-PR1-Status.
*>
     exit     section.
*>
