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
*>C  copy "envdiv.cob".
 configuration section.
 source-computer.      Linux.
 object-computer.      Linux.
*> special-names.
*>     console is crt.
 SPECIAL-NAMES.
       CRT STATUS is COB-CRT-STATUS.
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
*>
 input-output            section.
 file-control.
*>C  copy "selpyparam1.cob".
*>
*> Payroll param-1 (USA)
*>
     select  PY-Param1-File  assign        File-47
                             access        dynamic
                             organization  is relative
                             relative key  is RRN
                             status        PY-PR1-Status.
*>C  copy "selpyemp.cob".
*>
*> Payroll Employee (USA)
*>
     select  PY-Employee-File
                             assign               File-43
                             access               dynamic
                             organization         indexed
                             record key is        Emp-No
                             alternate record key Emp-Search-Name with duplicates
                             status               PY-Emp-Status.
*>
*>C  copy "selpypay.cob".
*>
*> Payroll Pay
*>
     select  PY-Pay-File
                             assign        File-46
                             access        dynamic
                             organization  indexed
                             record key is Pay-Emp-No
                             status        PY-Pay-Status.
*>
*>C  copy "selpyact.cob".
*>
*> Payroll Accounts
*>
     select  PY-Accounts-File
                             assign        File-39
                             access        dynamic
                             organization  indexed
                             record key is Act-No
                             status        PY-Act-Status.
*>
*>C  copy "selpyded.cob".
*>
*> Payroll Deductions (USA)
*>
     select  PY-System-Deduction-File
                             assign        File-42
                             access        dynamic
                             organization  is relative
                             relative key  is RRN
                             status        PY-Ded-Status.
*>
*>C  copy "selpychk.cob".
*>
*> Payroll Check
*>
     select  PY-Check-File
                             assign        File-40
                             access        dynamic
                             organization  indexed
                             record key is Chk-Emp-No
                             status        PY-Chk-Status.
*>

*>
*>C  copy "selprint.cob".    *> 132
*>
*> removed org line seq as causing double line printing in OC CE
*>
       select  print-file     assign        "prt-1"
                              organization line sequential.
*>
 data                    division.
*>================================
*>
 file section.
*>
*>C  copy "fdpyparam1.cob".
*>*******************************************
*>                                          *
*>  File Definition For Payroll Param  File *
*>                                          *
*>*******************************************
*>   Record Size 1024 Bytes (13/10/25)
*>   see wspyparam1.cob for later updates
*>
 fd  PY-Param1-File.
*>
*>C  copy "wspyparam1.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Py param1 File    *
*>     Uses RRN = 1                         *
*>                                          *
*>  If moved to ACAS system file will be    *
*>    record 5 and if split for PR1 rec 6.  *
*>     amd only the FH will need a change & *
*>      possibly the DAL if all of Payroll  *
*>      is to be supported in Mysql         *
*> A decision to be made after testing.     *
*>                                          *
*>*******************************************
*>
*>  File size 767 bytes padded to 1024 by filler.
*>
*> 13/10/25 vbc - Created.
*>  Consider adding to system file as rec #5 after basic testing
*> 08/11/25 vbc - Rec  changed still 1024.
*> 11/11/25 vbc - Moved PR2 fields embedded within PR1 area to PR2 rec size the same.
*> 26/11/25 vbc - Added new field PY-PR2-Last-Employee-no - filler adjusted.
*> 28/11/25 vbc - Added new field PY-PR1-Tax-ID  to ident employer with IRS set
*>                as x(24) as format not known.
*> 09/03/26 vbc - PR2 fields changed from x to bin-short unsigned.
*> 27/03/26 vbc - Just-closed-year-ended chg unsign bin to x (Y/N)
*> 12/04/26 vbc - New fields added see note at end of copybook.
*>
 01  PY-Param1-Record.
     03  PY-PR1-Block.                         *> Size = 906
         05  PY-PR1-Company-Data.                 *> size 300
             07  PY-PR1-Co-Name       pic x(60). *> Applewood Computers  [ 60 ] ?
             07  PY-PR1-Trade-Name    pic x(32).
             07  PY-PR1-Co-Address-1  pic x(32). *> 17 Stag Green Avenue [ 30 ]
             07  PY-PR1-Co-Address-2  pic x(32). *> Hatfield             [ 30 ]
             07  PY-PR1-Co-Address-3  pic x(32). *> Hertfordshire        [ 30 ]
             07  PY-PR1-Co-Address-4  pic x(32). *> spaces
             07  PY-PR1-Co-Post-Code.
                 09  PY-PR1-Co-Zip    pic x(10).
                 09  PY-PR1-Co-State  pic xx.
             07  PY-PR1-Co-Phone      pic x(12). *> 01234-123456
             07  PY-PR1-Co-Email      pic x(30). *> vbcoen@gmail.com
             07  PY-PR1-Pay-Method    pic x.     *> C = Check or B Bank to Bank Transfer.
             07  PY-PR1-Payslip-Md    pic x.     *> P = Printed or E = Email attachment.
             07  PY-PR1-Tax-ID        pic x(24). *> Used for Employer ID for IRS  NEW 27/11/25
*>
*> Only set if PY-PR1-IRS-Used or PY-PR1-GL-Used  = "Y" <<<<<<<<<<<<<<<<<<<<<<<<<<
*>
         05  PY-PR1-Offset-Cash-Acct  binary-char unsigned.    *> def 1  another file rec 5 or 6 digits
         05  PY-PR1-Dflt-Gross-Acct   binary-char unsigned.    *>   DITTO
         05  PY-PR1-Dflt-Dist-Acct    binary-char unsigned.    *>  def 3
         05  PY-PR1-Max-Dist-Accts    binary-char unsigned.   *> rem 11/06/79 these aren't in pr1 file, Are now!
*>
         05  PY-PR1-Min-Wage          pic 9(5)v99    comp-3.  *>  def 0
         05  PY-PR1-Void-Check-Amt    pic 9(5)v99    comp-3.  *>  Applies to check and B2B { not issued - subject to validation ].
*>
         05  PY-PR1-Rate2-Factor      pic 9(5)v99    comp-3.  *> def 1.5
         05  PY-PR1-Rate3-Factor      pic 9(5)v99    comp-3.  *> def 2.0
         05  PY-PR1-Max-Pay-Factor    pic 9(5)v99    comp-3.  *> def 3.0
         05  PY-PR1-Dflt-Pay-Rate     pic 9(5)v99    comp-3.  *> def 1.0
         05  PY-PR1-Dflt-Vac-Rate     pic 9(5)v99    comp-3.  *> def 0.42
         05  PY-PR1-Dflt-SL-Rate      pic 9(5)v99    comp-3.  *> def 0.21
         05  PY-PR1-Dflt-Norm-Units   pic 9(5)v99    comp-3.  *> def 1  Regular
*>
         05  PY-PR1-Last-Day-Pay-Period  pic 9(8). *> temp entry ? from param entry *nix format
         05  PY-PR1-Void-Checks-Over-Max pic x.    *> def N      - Y or N
         05  PY-PR1-Rate4-Exclusion-Type pic 9.    *> def 1  (1..4)
         05  PY-PR1-Check-Printing-Used  pic x.    *> def Y (or N)
         05  PY-PR1-Check-History-Used   pic x.    *> def N      - or Y - WB (oundary)
         05  PY-PR1-S-Used               pic x.    *> def N      - or N Semi M
         05  PY-PR1-M-Used               pic x.    *> def Y      - Y  Month
         05  PY-PR1-W-Used               pic x.    *> Def N   "  - Y  Weekly
         05  PY-PR1-B-Used               pic x.    *> def N   "  - Y  Bi Month - WB
         05  PY-PR1-JC-Used              pic x.    *> def N      - Y
         05  PY-PR1-GL-Used              pic x.    *> def N      - or Y
         05  PY-PR1-IRS-Used             pic x.    *> del Y      - or N  - WB
         05  PY-PR1-Dflt-Pay-Interval    pic x.    *> def S  could be SMBW - S=Salary,W=Weekly, M=Monthly & B=Bi-Monthly
         05  PY-PR1-Dist-Used            pic x.    *> def N  was binary-char unsigned.    *> def Y ????? what
         05  PY-PR1-Currency-Sign        pic x.    *> Def "$"  --  NOT USED YET
         05  PY-PR1-OS-Delimiter         pic x.    *>   / for *nix and \ for windows Used via ACAS param - WB
         05  PY-PR1-Debugging            pic x.    *> Def N (or Y !
         05  PY-PR1-Hard-Delete          pic x.    *> Def N (or Y)
*>
*>  Where are these stored, if anywhere ?
*>
*> interval$(1)="SEMI-MONTHLY"
*> interval$(2)="MONTHLY"
*> interval$(3)="BIWEEKLY"
*> interval$(4)="WEEKLY"
*>
         05  PY-PR1-Dflt-HS-Type      pic x.     *> def S  Dflt-Pay-Type ??
         05  PY-PR1-B2B-File-Type     pic x.     *> C = CSV comma delimited) or T = Text file
         05  PY-PR1-Rate-Name         pic x(15)       occurs 4.   *> def  "REGULAR" "OVERTIME"
                                                                  *> def  "SPEC. OVERTIME" "COMMISSION"
         05  PY-PR1-Fed-ID            pic x(15). *> "FEDERAL ID"
         05  PY-PR1-State-ID          pic x(15). *> "STATE ID"
         05  PY-PR1-Local-ID          pic x(15). *> "LOCAL ID"
         05  PY-PR1-Date-Format       pic 9.     *> Def: 2=mm/dd/ccyy,  1=dd/mm/ccyy
*>                                                  ( Value reversed from BASIC code to match ACAS.
         05  PY-PR1-Date.                        *> WHAT IS THIS FOR ? - will ASSUME today for the BUT NEEDED - SO FAR NO.
*>                                                  moment defaulting to USA mode - ditto for other dates
             07  PY-PR1-Date-Mo       pic 99.    *> def 1
             07  PY-PR1-Date-Dy       pic 99.    *> def 2
             07  PY-PR1-Date-Yr       pic 9(4).  *> def 3 Added CC
         05  PY-PR1-Page-Lines-P      pic 99.    *> def 60  Portrait
         05  PY-PR1-Page-Lines-L      pic 99.    *> def 60  Landscape
         05  PY-PR1-Page-Width-P      pic 999.   *> def 132  -- Portrait paper = 80
         05  PY-PR1-Page-Width-L      pic 999.   *> def 132  -- landscape paper = 120
         05  PY-PR1-User-Prog-Used    pic x.     *>  N   ----  These three not used
         05  PY-PR1-User-Prog         pic x(8).  *> spaces
         05  PY-PR1-User-Prog-Desc    pic x(20). *> spaces
         05  PY-PR1-Max-Chk-Cats      binary-char.  *>     This block values to be determined
         05  PY-PR1-Max-Emp-Eds       binary-char.  *>  3  NEEDED <<   a number but not really neeeded as fields are exact #
         05  PY-PR1-Max-Ed-Cats       binary-char.  *>  55 NEEDS TO BE SET UP in param  SETUP NOT YET DONE - same for all these.
         05  PY-PR1-Max-Swt-Entries   binary-char.  *>            A / marks in use for any one line
         05  PY-PR1-Lo-Ded-Chk-Cat    binary-char.  *>
         05  PY-PR1-Hi-Ded-Chk-Cat    binary-char.  *>
         05  PY-PR1-Lo-Earn-Chk-Cat   binary-char.  *>
         05  PY-PR1-Hi-Earn-Chk-Cat   binary-char.  *>
         05  PY-PR1-Max-Sys-Eds       binary-char.  *> 5
*> filler here for WB alignment if needed,
         05  PY-PR1-Print-Control.
             07  PY-PR1-Print-Spool-Name  pic x(48). *> All 3 from ACAS system params
             07  PY-PR1-Print-Spool-Name2 pic x(48). *> but only 1st used (or is it)
             07  PY-PR1-Print-Spool-Name3 pic x(48). *>  consider creating a pdf file from prt-1
             07  PY-PR1-Print-Ctl-Flag    pic x.        *>  Font etc control needed/used (Def N)
             07  PY-PR1-Font-Small        pic x(32).
             07  PY-PR1-Font-Normal       pic x(32).
             07  PY-PR1-Font-Reset        pic x(32). *> + 97
             07  PY-PR1-Colour-1          pic x(32). *> + 129
             07  PY-PR1-Colour-2          pic x(32). *> + 161
             07  PY-PR1-Colour-Reset      pic x(32). *> + 193
*>
         05  PY-PR1-Quote-Char            pic x.    *> " or '
*> B2B field order : - etc
         05  PY-PR1-B2B-Fields.
             07  PY-PR1-B2B-Field-Order  pic 99   occurs 20.  *> 01 through 20  --  + 40 bytes
*> for fields ->
*>  Fixed Names -
*>   Co Acct #, Transfer Date,   Emp-No, Emp-Name, Emp-Addr1, 2, 3, 4, State, Zip
*>   Emo-SSN, Bank A/C. Pay Amount =  13 - Any more ?
*>
*>
     03  PY-PR2-Block.                        *> Size = 88  COULD BE REC 2 ? (+ filler = 640 or 768 etc) (RRN = 2). sizes wrong
         05  PY-PR2-Year              pic 9(4).  *> current year
         05  PY-PR2-Year-Next         pic 9(4).  *> Year + 1  --- New field
         05  PY-PR2-Last-Year-Ended   pic 9(4).  *> Used in pyperend only so far?????? { if no where else can kill it }
         05  PY-PR2-Last-SM-Apply-No  pic 9(4).  *> def 0
         05  PY-PR2-Last-WB-Apply-No  pic 9(4).  *> def 0
         05  PY-PR2-Hrs-Batch-No      pic 9(4).  *> def 0
         05  PY-PR2-Last-Day-Last-W   pic 9(8).  *> }
         05  PY-PR2-Last-Day-Last-B   pic 9(8).  *> }
         05  PY-PR2-Last-Day-Last-S   pic 9(8).  *> }  use todays to yyyymmdd
         05  PY-PR2-Last-Day-Last-M   pic 9(8).  *> }       error,  may be not ??????
         05  PY-PR2-Check-Date        pic 9(8).  *> }
         05  PY-PR2-Last-Employee-No  pic 9(8)   comp.    *>  ?? NEW for py010 data entry EXCLUDES check digit. allows for # = 64k
         05  PY-PR2-No-Active-Emps    binary-short unsigned.   *> def 0
         05  PY-PR2-No-Employees      binary-short unsigned.   *> def 0 - NEEDED ??
         05  PY-PR2-No-Of-SM-Applies  binary-short unsigned.   *> SIZE emough 65k ?  - 12/02/79 pr2.no.of.xx.applies% = number of sm, wb applies this quarter
         05  PY-PR2-No-Of-WB-Applies  binary-short unsigned.   *> SIZE emough 65k ?    DITTO
         05  PY-PR2-No-Accts          binary-char  unsigned.    *> def 4 = 4 accounts ? is it needed ??
         05  PY-PR2-Just-Closed-Year  pic x. *> pyperpend - wrong ? binary-short unsigned.
*>                    - 12/02/79 pr2.just.closed.year% = no applies run since year end close THIS DOES NOT MATCH UP - FIND THIS!!!!!!
         05  PY-PR2-940-Printed       pic x.     *> N  (or Y)
         05  PY-PR2-941-Printed       pic x.     *> N  (or Y)
         05  PY-PR2-W2-Printed        pic x.     *> N  (or Y)
         05  PY-PR2-Last-Q-Ended      pic 9.     *> 4 ( vals 1, 2, 3 or 4 )
         05  PY-PR2-Last-Check-No     pic 9(6). *> 000000     - 12/02/79 pr2.last.check.no$    = last check number written by PYCHECKS
*>
*> Chg this for resized file.
*>
     03  filler                       pic x(29).
*>
*> IPYPR2 - payroll chainging parameter record description
*>        12/02/79 pr2.no.of.xx.applies% number of sm, wb applies this quarter
*>        12/02/79 pr2.just.closed.year% no applies run since year end close
*>        12/02/79 pr2.last.check.no$    last check number written by PYCHECKS
*>
*> These need to be set up in py900 paran setup:::: === DONE
*>  Payroll param changes:
*>        2026/04/01 PY-PR1-Print-Ctl-Flag
*>        2026/04/01 PY-PR1-Font-Small
*>        2026/04/01 PY-PR1-Font-Normal
*>        2026/04/01 PY-PR1-Font-Reset
*>        2026/04/01 PY-PR1-Colour-1
*>        2026/04/01 PY-PR1-Colour-2
*>        2026/04/01 PY-PR1-Colour-Reset
*>
*>  Payroll param changes:    DONE
*>        2026/04/12 PY-PR1-Pay-Method
*>        2026/04/12 PY-PR1-Payslip-Md
*>        2026/04/12 PY-PR1-B2B-File-Type
*>        2026/04/12 PY-PR1-Quote-Char
*>        2026/04/12 B2B field layouts in fixed field orders
*>
*>
*>C  copy "fdpyemp.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Employee File    *
*>                                          *
*>*******************************************
*>   Record Size 508 Bytes
*>   see wspyemp.cob for later updates
*>
 fd  PY-Employee-File.
*>
*>C  copy "wspyemp.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Employee          *
*>           File                           *
*>     Uses Emp-No as key                   *
*>*******************************************
*>  File size 508 bytes.
*>
*> THESE FIELDS DEFINITIONS MAY NEED CHANGING - Needs WB alignments 12/04/26
*>
*> 29/10/25 vbc - Created.
*> 10/11/25 vbc - Field changes.
*> 20/11/25 vbc - Phone# 12 -> 13 reduced filler to 14 & removed dup phone field.
*> 28/11/25 vbc - Zip code, SSN sizes chg.  Date fiormats are all ccyymmdd.
*> 02/12/25 vbc - Fields with -Allow chgd from x to 99.size will be the same.
*> 17/03/26 vbc - Mcare-Exempt added - File size change ?
*>
 01  PY-Employee-Record.
     03  Emp-No                pic 9(7)   comp.
     03  Emp-Status            pic x.     *> A = Active, T = Terminated, L = On leave & Hidden D = Deleted
     03  Emp-HS-Type           pic x.     *> H = Hourly or S = Salaried
     03  Emp-Pay-Interval      pic x.     *> W, M, B ( Bi weekly), S (semi-monthly
     03  Emp-Taxing-State      pic xx.    *> USA state code
     03  Emp-Job-Code          pic xxx.   *> information only
     03  Emp-Start-Date        pic 9(8)   comp. *> date started ccyymmdd
     03  Emp-Birth-Date        pic 9(8)   comp. *> ccyymmdd
     03  Emp-Term-Date         pic 9(8)   comp. *> date left  ccyymmdd - (last date of pay ?)
     03  Emp-Sex               pic x.     *> M, F
     03  Emp-Marital           pic x.     *> S, M
     03  Emp-Pay-Freq          binary-char.     *> 52, 24 or same / 2 = 26 / 12 Subject to change when looking at basic code
     03  Emp-Next-Del          pic x.     *> No idea yet
     03  Emp-SSN               pic 9(9)   comp.  *> 000-00-0000 & one spare for growth Excludes "-"
     03  Emp-Cur-Apply-No      pic 99.    *>  9  or ??  2 bytes
     03  Emp-Name              pic x(32). *> last 1st & middle init -NO> 1st middle last (middle can be initial only
     03  Emp-Search-Name       pic x(32). *> Uses Emp-Name to create Last, Middle & First Name - INDEX 2
     03  Emp-Address-1         pic x(32).
     03  Emp-Address-2         pic x(32).
     03  Emp-Address-3         pic x(32).
     03  Emp-Address-4         pic x(32).
     03  Emp-Post-Code.                   *> UK = 8 Canada 7 incl space,
         05  Emp-Zip           pic x(10).  *> 5 & + 5
         05  Emp-State         pic xx.
     03  Emp-Phone-No          pic 9(11). *> 01234-123456 / (123)-456-7890 09/12/25 reduced from 13
     03  Emp-Email             pic x(30). *> vbcoen@btconnect.com  + 10
     03  Emp-Bank-Acct-No      pic x(24). *> Allows also for sortcode/acct # (6+8) & - between numbers )
     03  Emp-Rate4-Exclusion   pic 9.     *> 1 = all taxes, 2 = All taxes except FICA,
                                          *> 3 = All except FICA,SWT, LWT 4 = none
     03  Emp-Cal-Head-Of-House pic x.     *> Y or N for all these
     03  Emp-Cal-Ded-Allow     pic 99    comp.
     03  Emp-FWT-Allow         pic 99    comp.
     03  Emp-SWT-Allow         pic 99    comp.
     03  Emp-LWT-Allow         pic 99    comp.
     03  Emp-Pension-Used      pic x. *> Y or N
     03  Emp-Eic-Used          pic x. *> all Y or N
     03  Emp-FWT-Exempt        pic x. *>
     03  Emp-SWT-Exempt        pic x. *>
     03  Emp-LWT-Exempt        pic x. *>
     03  Emp-FICA-Exempt       pic x. *>
     03  Emp-SDI-Exempt        pic x. *>
     03  Emp-Co-FUTA-Exempt    pic x. *>
     03  Emp-Co-SUI-Exempt     pic x. *>
     03  Emp-Mcare-Exempt      pic x. *>
     03  Emp-Sys-Exempt        pic x    occurs 5.
     03  Emp-Rate              pic 9(5)v99   comp-3  occurs 4.
     03  Emp-Auto-Units        pic 999       comp-3.
     03  Emp-Normal-Units      pic 999       comp-3.
     03  Emp-Max-Pay           pic 9(6)v99   comp-3.
     03  Emp-Vac-Rate          pic 9(5)v99   comp-3.
     03  Emp-Vac-Accum         pic 9(5)v99   comp-3.
     03  Emp-Vac-Used          pic 9(5)v99   comp-3.
     03  Emp-SL-Rate           pic 9(5)v99   comp-3.
     03  Emp-SL-Accum          pic 9(5)v99   comp-3.
     03  Emp-SL-Used           pic 9(5)v99   comp-3.
     03  Emp-Comp-Accum        pic 9(5)v99   comp-3.
     03  Emp-Comp-Used         pic 9(5)v99   comp-3.
     03  Emp-Dist-Grp                   occurs 5.   *> Distribution account and %
         05  Emp-Dist-Acct     binary-char  unsigned.
         05  Emp-Dist-Pcent    pic 999v99      comp-3.
     03  Emp-ED-Grp                     occurs 3.  *> Should this be 5 or even 10 ?
         05  Emp-Ed-Used       pic x.   *> Y or N /
         05  Emp-Ed-Group.
             07  Emp-ED-Factor     pic 9(6)v99   comp-3.
             07  Emp-ED-Limit      pic 9(6)v99   comp-3.
             07  Emp-ED-Amt-Pcent  pic x.   *> A  or P /
             07  Emp-ED-Acct-No    binary-char  unsigned. *> /
             07  Emp-ED-Desc       pic x(15).  *> /
             07  Emp-ED-Earn-Ded   pic x.   *> D or E /
             07  Emp-ED-Exclusion  pic 9.   *> /
             07  Emp-ED-Limit-Used pic x.   *> Y or N
             07  Emp-ED-Chk-Cat    pic 99   comp.  *> /
     03  filler                    pic x(11).
*>
*>
*>C  copy "fdpypay.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Pay File         *
*>                                          *
*>*******************************************
*>   Record Size 28 Bytes
*>   see wspypay.cob for later updates
*>
 fd  PY-Pay-File.
*>
*>C  copy "wspypay.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Pay File          *
*>                                          *
*>     Uses Pay-Emp-No as key               *
*>*******************************************
*>  File size 24 bytes.
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 29/10/25 vbc - Created.
*> 10/04/26 vbc - Added xtra comments.
*> 14/04/26 vbc - Chg Interval to x, Extended to x from xx, Cat to 9 frm xx
*>                & repos size now 24.
*>
 01  PY-Pay-Record.
     03  Pay-Emp-No                   pic 9(7).
     03  Pay-Interval                 pic x.              *> w, m
     03  Pay-EFf-Date                 pic 9(8)      comp. *> ccyymmdd
     03  Pay-Apply-No                 pic 9(4)      comp.
     03  Pay-Reporting-Cat            pic 99        comp.  *> 01 - 50 via pyjourn, check its right ? for both see APPLY1, 2 & 3.
     03  Pay-Extended                 pic x.               *> is this right ? N or Y - false / true
     03  Pay-Units                    pic s9(5)v99  comp-3.
     03  Pay-Amt                      pic s9(5)v99  comp-3.
*>
 01  PY-Pay-Header.
     03  Pay-Hdr-No                   pic 9(7).           *> value zero.
     03  Pay-Hdr-Interval             pic x.              *> w, m
     03  Pay-Hdr-Last-Apply-No        pic 9(4)      comp.
     03  Pay-Hdr-Last-Day-of-Last-Per pic 9(8)      comp. *> ccyymmdd
     03  Pay-Hdr-Journal-Printed      pic x.              *> Y / N
     03  FILLER                       pic x(9).
*>
*>C  copy "fdpyact.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Account File     *
*>              Via IRS                     *
*>*******************************************
*>   Record Size 32 Bytes
*>   see wspyact.cob for later updates
*>
 fd  PY-Accounts-File.
*>
*>C  copy "wspyact.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Accounts File     *
*>     Uses Act-No as key                   *
*>*******************************************
*>  File size 34 bytes.
*>
*> 29/10/25 vbc - Created.
*> 31/10/25 vbc - Renamed act-no to act-gl-no & added act-no.
*>                This subject to using py account info instead
*>                of direct to GL. Note IRS uses 5 and GL 6 digits.
*> 05/11/25 vbc   Chg Act-No to pic 99.
*> 12/11/25 vbc - Chg Gl-No  to display from comp.
*> 16/04/26 vbc - Added Type & 1 char Cat/filler. where type / Cat
*>                is 0 = Cash/C, 1 = Liability/L & 4 = Expense/E.
*>
 01  PY-Accounts-Record.
     03  Act-No              pic 99.
     03  Act-Type            pic 9.       *> 0=Cash, 1=Liability, 4=Expense.
     03  Act-Cat             pic x.       *> C=Cash, L=Liability, E=Expense
*>                                           Otherwise used as a filler
     03  Act-GL-No           pic 9(6).
     03  Act-Desc            pic x(24).
*>
*>
*>C  copy "fdpyded.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Deductions File  *
*>                                          *
*>*******************************************
*>   Record Size 438 Bytes
*>   see wspyded.cob for later updates
*>
 fd  PY-System-Deduction-File.
*>
*>C  copy "wspyded.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Py Deduction File *
*>     Uses RRN = 1                         *
*>*******************************************
*>  File size 374 bytes 14/04/26
*> 25/10/25 vbc - Created.
*> 08/11/25 vbc - Rec size changed
*> 12/11/25 vbc - and again - less.
*> 15/11/25 vbc - again more + 9.
*> 28/12/25 vbc - Consider increasing table to support a.n.other new ded rates.
*> 16/01/26 vbc - Increased size by 2.
*> 14/04/26 vbc - Added flds Mcare, other-1 & 2 (incase) & repos for WB ?
*> 19/04/26 vbc - Removed others 1/2 replaced with Extras for -
*>                Used, Acct-No, Rate & Limit. File size increased.
*>
 01  PY-System-Deduction-Record.
     03  Ded-Services-Used.
         05  Ded-FWT-Used             pic x.    *> Y NEEDED ?
         05  Ded-SWT-Used             pic x.    *> Y needed ?
         05  Ded-LWT-Used             pic x.   *>  N
         05  Ded-FICA-Used            pic x.   *>  Y
         05  Ded-CO-FICA-Used         pic x.   *>
         05  Ded-SDI-Used             pic x.   *>
         05  Ded-CO-FUTA-Used         pic x.   *>
         05  Ded-CO-SUI-Used          pic x.   *>
         05  Ded-EIC-Used             pic x.   *>
         05  Ded-Mcare-Used           pic x.   *>
         05  Ded-Extras-Used          pic x   occurs 10.   *> Allows expansion
*>
     03  Ded-Acct-Numbers.
         05  Ded-FWT-Acct-No          pic 99.
         05  Ded-SWT-Acct-No          pic 99.
         05  Ded-LWT-Acct-No          pic 99.
         05  Ded-FICA-Acct-No         pic 99.
         05  Ded-CO-FICA-Acct-No      pic 99.
         05  Ded-SDI-Acct-No          pic 99.
         05  Ded-CO-FUTA-Acct-No      pic 99.
         05  Ded-CO-SUI-Acct-No       pic 99.
         05  Ded-EIC-Acct-No          pic 99.
         05  Ded-Mcare-Acct-No        pic 99.
         05  Ded-Extras-Acct-No       pic 99   occurs 10.    *> Allows expansion
*>
     03  Ded-Rates.
         05  Ded-FICA-Rate            pic 99v99    comp-3.
         05  Ded-CO-FICA-Rate         pic 99v99    comp-3.
         05  Ded-SDI-Rate             pic 99v99    comp-3.
         05  Ded-CO-FUTA-Rate         pic 99v99    comp-3.
         05  Ded-CO-SUI-Rate          pic 99v99    comp-3.
         05  Ded-EIC-Rate             pic 99v99    comp-3.
         05  Ded-EIC-Excess-Rate      pic 99v99    comp-3.
         05  Ded-Mcare-Rate           pic 99v99    comp-3.
         05  Ded-Extras-Rate          pic 99v99    comp-3  occurs 10.
*>
     03  Ded-FWT-Allowance-Amt        pic S9(5)v99   comp-3.
*>
     03  Ded-Limits.
         05  Ded-FICA-Limit           pic 9(5)v99  comp-3.
         05  Ded-CO-FICA-Limit        pic 9(5)v99  comp-3.
         05  Ded-SDI-Limit            pic 9(5)v99  comp-3.
         05  Ded-CO-FUTA-Limit        pic 9(5)v99  comp-3.
         05  Ded-CO-FUTA-Max-Credit   pic 9(5)v99  comp-3.
         05  Ded-CO-SUI-Limit         pic 9(5)v99  comp-3.
         05  Ded-EIC-Limit            pic 9(5)v99  comp-3.
         05  Ded-EIC-Excess-Limit     pic 9(5)v99  comp-3.
         05  Ded-Mcare-Limit          pic 9(5)v99  comp-3.
         05  Ded-Extras-Limit         pic 9(5)v99  comp-3  occurs 10.   *> Allows for expansion.
*>
     03  Ded-FWT-Mar              occurs 7.
         05  Ded-FWT-Mar-Cutoff       pic 9(5)v99  comp-3.
         05  Ded-FWT-Mar-Percent      pic 9(3)v99  comp-3.
*>
     03  Ded-FWT-Sin              occurs 7.
         05  Ded-FWT-Sin-Cutoff       pic 9(5)v99  comp-3.
         05  Ded-FWT-Sin-Percent      pic 9(3)v99  comp-3.
*>
     03  Ded-Sys-Entries-Used         pic 99.  *> allow for this block to be > 10
     03  Ded-Sys-Data-Blocks      occurs 5.
         05  Ded-Sys-Amt-Percent      pic x.   *>  A
         05  Ded-Sys-Chk-Cat          pic 99.  *>  7 ( 2 - 7 if Earn-Ded = E. 9 - 16 if Earn-Ded = D
         05  Ded-Sys-Earn-Ded         pic x.   *>  E
         05  Ded-Sys-Exclusion        pic 9.   *>  1 ( 1 - 4)
         05  Ded-Sys-Limit-Used       pic x.   *>  Y
         05  Ded-Sys-Used             pic x.   *>  N
         05  Ded-Sys-Desc             pic x(15).
         05  Ded-Sys-Acct-No          binary-char  unsigned.
         05  filler                   pic x.
         05  Ded-Sys-Factor           pic 9(5)v99  comp-3.
         05  Ded-Sys-Limit            pic 9(5)v99  comp-3.
*>
*>
*>C  copy "fdpychk.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Check File       *
*>                                          *
*>*******************************************
*>   Record Size 76 Bytes
*>   see wspychk.cob for later updates
*>
 fd  PY-Check-File.
*>
*>C  copy "wspychk.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Chk File          *
*>                                          *
*>     Uses Chk-Emp-No as key               *
*>*******************************************
*>  File size 76 bytes.
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 29/10/25 vbc - Created.
*> 02/02/26 vbc - One more Amt occurance = 16.
*> 11/04/26 vbc - Interval x -> 9.
*>
 01  PY-Chk-Record.
     03  Chk-Emp-No        pic 9(7).
     03  Chk-Check-No      pic 9(6)     comp.
     03  Chk-Amt           pic 9(5)v99  comp-3  occurs 16.
*>
 01  PY-Chk-Hdr-Record.
     03  Chk-Hdr-No               pic 9(7).   *> value zero
     03  Chk-hdr-Interval         pic 9.
     03  Chk-hdr-Apply-No         pic 9(4)    comp.
     03  Chk-hdr-Slow-From-Date   pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-Fast-From-Date   pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-To-Date          pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-Register-Printed pic x.
     03  Chk-hdr-Checks-Printed   pic x.
*> 24 ?
     03  FILLER                   pic x(52).
*>

*>
 fd  Print-File
     reports are Employee-Detailed-Journal-Report
                 Company-Summary
                 Ledger-Account-Summary.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "pyjourn (1.0.00)".  *> First release pre testing.
*>
*>  This will print 1 copy to CUPS print spool specified on line 3 override via setup at SOJ
*>
*>C  copy "print-spool-command.cob".     *> CHECK PRN file for content Landscape mode
*>
*> 2023/02/18 vbc - Added PP-Name and Print-File-Name - Landscape
*>
 01  Print-Report.
     03  filler          pic x(117)     value
     "lpr -r -o 'orientation-requested=4 page-left=21 page-top=24 " &   *> was 48 - 28/4/24 18mm from Top of page
     "page-right=10 sides=two-sided-long-edge cpi=12 lpi=8' -P ".
     03  PSN             pic x(48)      value "Smart_Tank_7300 ".  *> This is the Cups print spool, change it for yours
     03  PP-Name         pic x(24)      value "prt-1".      *> Don't change this line 18/02/23 was X(15)
*>
 01  PP-Print-File-Name  pic x(24)      value "prt-1".
*>
*>C  copy "wsmaps03.cob".
       >>source free
*>*********
*> maps03 *
*>*********
*> 23/04/09 vbc - Support for UK, USA, Intl formats
 01  maps03-ws.
     03  u-date          pic x(10).
     03  u-UK redefines u-date.
         05  u-days      pic 99.
         05  filler      pic x.
         05  u-month     pic 99.
         05  filler      pic x.
         05  u-year.
             07  u-cc    pic 99.
             07  u-yy    pic 99.
     03  u-USA redefines u-date.
         05  u-usa-month pic 99.
         05  filler      pic x.
         05  u-usa-days  pic 99.
         05  filler      pic x.
         05  filler      pic x(4).
     03  u-Intl redefines u-date.
         05  u-intl-year.
             07  u-intl-cc pic 99.
             07  u-intl-yy pic 99.
         05  filler        pic x.
         05  u-intl-month  pic 99.
         05  filler        pic x.
         05  u-intl-days   pic 99.
     03  u-bin           binary-long.
*>C  copy "wsfnctn.cob".
*>**********************************
*>                                 *
*>  File Access Control Functions  *
*>                                 *
*>**********************************
*> 28/05/16 vbc - Added RDB setup fields - socket, host, port to user, passwd, schema.
*> 25/08/16 vbc - Amended size of RDBMS-Socket from 32 to 64 chars.
*> 01/10/16 vbc - Changed WE-Error & Rrn to pic 999 / 9.  To see if it is the cause
*>                of No data in SYSTOT-REC bug after running sys4LD.
*> 29/10/16 vbc - FS-Action increased size from 20 to 22 for logest msg in sys002.
*>  7/12/16 vbc - Increased Access-Type to 99 from 9 for extra adhoc functions
*>                such as select x ORDER BY etc.
*>                Not used yet.
*> 22/12/16 vbc - Oops, previous chg should have been for File-Function.
*>                next-read-raw changed to 13.
*> 06/01/17 vbc - Increased size of rrn for GL. System to be recompiled.
*> 18/04/17 vbc - Added function Read-Next-Header (34) for SL020, 50, 140.
*> 21/04/18 vbc - Added ACAS-Path and Path-Work for scr save/dumps delete files).
*> 20/05/23 vbc - Added notes for read header for sl820.
*> 06/08/23 vbc - Activated  fn-not-greater-than (for Stock file).
*>
 01  File-Access.
     03  We-Error        pic 999.
     03  Rrn             pic 9(5)   comp.     *> increased from 9 for GL.
     03  Fs-Reply        pic 99.
     03  s1              pic x.               *> this is USED for some programs 28.05.18.
     03  Curs            pic 9(4).
     03  filler redefines Curs.
         05  Lin         pic 99.
         05  Cole        pic 99.
     03  Curs2           pic 9(4).
     03  filler redefines Curs2.
         05  Lin2        pic 99.
         05  Col2        pic 99.
*>
*> Holds path to current working dir - used for screen dump & restores.
*>
     03  ACAS-Path       pic x(525)     value spaces.
     03  Path-Work       pic x(525)     value spaces.
*>
     03  FS-Action       pic x(22)  value spaces.
*> current range 1 thru 3
*>     1 = Stock-Key (or only key), 2 = Stock-Abrev-Key, 3 = Stock-Desc
     03  Logging-Data.
         05  Accept-Reply    pic x      value space.
         05  File-Key-No     pic 9.
         05  ws-Log-System   pic 9      value zero.       *> loaded by caller of FHlogger
         05  ws-No-Paragraph pic 999.
         05  SQL-Err         pic x(5).
         05  SQL-Msg         pic x(512) value spaces.
         05  SQL-State       pic x(5).
         05  WS-File-Key     pic x(64)  value spaces.     *> loaded by caller of FHlogging increased to 64-- 30/12/16
         05  WS-Log-Where    pic x(231) value spaces.
         05  WS-Log-File-No  pic 99     value zeroes.     *> loaded by caller of FHlogger
         05  WS-Count-Rows   pic 9(7)   value zeroes.     *> used in Delete-All in valueMT
     03  RDB-Data.
         05  DB-Schema   pic x(12)  value spaces.
         05  DB-UName    pic x(12)  value spaces.
         05  DB-UPass    pic x(12)  value spaces.
         05  DB-Host     pic x(32)  value spaces.
         05  DB-Socket   pic x(64)  value spaces.
         05  DB-Port     pic x(5)   value spaces.
*>
*>  Helps to tell MT to move file record from the FD or the WS record. NOT YET USED
*>
     03  Main-Record-Move-Flag pic 9 value zero.
         88  MRMF-Move-FD           value 1.
         88  MRMF-Move-WS           value 2.
*>
*>   need to change next one if used in the DAL, e.g., move "66" ...
*>
     03  FA-RDBMS-Flat-Statuses.                        *> Comes from System-Record via acas0nn
         07  FA-File-System-Used  pic 9.
             88  FA-FS-Cobol-Files-Used        value zero.
             88  FA-FS-RDBMS-Used              value 1.
*>                 88  FA-FS-MySql-Used          value 1.  *> ditto
*>                 88  FA-FS-Oracle-Used         value 2.  *> THESE NOT IN USE
*>                 88  FA-FS-Postgres-Used       value 3.  *> ditto
*>                 88  FA-FS-DB2-Used            value 4.  *> ditto
*>                 88  FA-FS-MS-SQL-Used         value 5.  *> ditto
             88  FA-FS-Valid-Options           values 0 thru 1.    *> 5. (not in use unless 1-5)
         07  FA-File-Duplicates-In-Use pic 9.                      *> NO LONGER USED other than for a '6' = rdb.
             88  FA-FS-Duplicate-Processing    value 1.
*>
*> Block for File/table access via acas000 thru acas033 for IS files and rdbms
*> Also see RDBMS-Flat-Statuses in System-Record
*>
     03  File-Function   pic 99.
         88  fn-open            value 1.
         88  fn-close           value 2.
         88  fn-read-next       value 3.
         88  fn-read-indexed    value 4.
         88  fn-write           value 5.
         88  fn-Delete-All      value 6.       *> 10/10/16 - Delete all records.
         88  fn-re-write        value 7.
         88  fn-delete          value 8.
         88  fn-start           value 9.
*>
         88  fn-Write-Raw       value 15.
         88  fn-Read-Next-Raw   value 13.       *> 14/11/16 - Special 4 LD.
*>
         88  fn-Read-By-Name    value 31.       *> 15/01/17 for Salesled (SL160), could be used for GL ledger?
         88  fn-Read-By-Batch   value 32.       *> 08/02/17 for OTM3/5 (sl095/pl095)
         88  fn-Read-By-Cust    value 33.       *> 09/02/17 for OTM3 (sl110, 120, 190)
         88  fn-Read-Next-Header value 34.      *> 18/04/17 for Invoice (sl020, 50, 140, 820)
*>
     03  Access-Type     pic 9.                *> For rdbms 2 should cover all !!!
         88  fn-input           value 1.
         88  fn-i-o             value 2.
         88  fn-output          value 3.
         88  fn-extend          value 4.       *> not valid for ISAM
         88  fn-equal-to        value 5.
         88  fn-less-than       value 6.
         88  fn-greater-than    value 7.
         88  fn-not-less-than   value 8.
         88  fn-not-greater-than value 9.
*>
*>
*>C  copy "Test-Data-Flags.cob".           *> set sw-Testing to zero to stop logging.
*>
*>  This data is present in ALL ACAS modules.
*>   When testing comlete you can set SW-Testing to zero
*>    to stop the logging file being produced.
*>
 01 ACAS-DAL-Common-data.     *> For DAL processing.
*>
*> log file reporting for testing otherwise zero
*>
     03  SW-Testing               pic 9   value 1.    *>   zero.
         88  Testing-1                    value 1.
*>
*>  Testing only for displays ws-where etc  otherwise zero
*>
     03  SW-Testing-2             pic 9   value zero.
         88  Testing-2                    value 1.
*>
     03  Log-File-Rec-Written     pic 9(6) value zero.    *> in both acas0nn and a DAL.
*>
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

     03  WS-Rep-From-Date         pic x(10).   *> HAS TO BE SET UP
     03  WS-Rep-To-Date           pic x(10).
     03  WS-Check-Date            pic x(10).
     03  WS-Detail-Line           pic x.
     03  WS-Fast-and-Slow         pic x.
     03  WS-DR-CR                 pic xx.
     03  WS-First-Detail-Line     pic x.
     03  WS-Emp-From-No           pic 9(7).  *> } final footing totals
     03  WS-Emp-To-No             pic 9(7).  *> } ditto for Emp Detail
     03  WS-Exemptions            pic x(256).

 01  WS-Accumulators-2.
     03  WS-Dist-Out              pic s9(7)v99.        *> (1)     ditto ?
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
     03  WS-Total-Units           pic s9(7)v99       occurs 4.  *> Vie PY-PR1-Rate-Name occcurs 4
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
         05  filler          pic x(16) value "1REGULAR PAY".
         05  filler          pic x(16) value "1OVERTIME PAY".
         05  filler          pic x(16) value "1SPECIAL OT PAY".
         05  filler          pic x(16) value "1COMMISSION".
         05  filler          pic x(16) value "3VACATION TAKEN".  *>  NOT ON CHECKS
         05  filler          pic x(16) value "3SICK LVE TAKEN".  *>  NOT ON CHECKS
         05  filler          pic x(16) value "3COMP TIME TAKEN". *>  NOT ON CHECKS
         05  filler          pic x(16) value "3COMP TIME EARND". *>  NOT ON CHECKS
         05  filler          pic x(16) value "1BONUS".
         05  filler          pic x(16) value "1TIPS COLLECTED".
         05  filler          pic x(16) value "3ADVANCE".
         05  filler          pic x(16) value "1SICK PAY".
         05  filler          pic x(16) value "1VACATION PAY".
         05  filler          pic x(16) value "1OTHER EXCLD PAY".
         05  filler          pic x(16) value "3EXPENSE REIMB".
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
         05  filler          pic x(16) value "0SYS1".           *>  from sys1   FROM DED FILE
         05  filler          pic x(16) value "0SYS2".           *>  from sys2   FROM DED FILE
         05  filler          pic x(16) value "0SYS3".           *>  from sys3   FROM DED FILE
         05  filler          pic x(16) value "0SYS4".           *>  from sys4   FROM DED FILE
         05  filler          pic x(16) value "0SYS5".           *>  from sys5   FROM DED FILE
         05  filler          pic x(16) value "0EMP1".           *>  from emp1   FROM EMP FILE
         05  filler          pic x(16) value "0EMP2".           *>  from emp2   FROM EMP FILE
         05  filler          pic x(16) value "0EMP3".           *>  from emp3   FROM EMP FILE
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
*>
 01  Error-Code          pic 999.
*>
 01  COB-CRT-Status      pic 9(4)         value zero.
*>C      copy "screenio.cpy".
      *>  Copyright (C) 2008-2012, 2015-2016, 2019, 2021
      *>  Free Software Foundation, Inc.
      *>  Written by Roger While, Simon Sobisch
      *>
      *>  This file is part of GnuCOBOL.
      *>
      *>  The GnuCOBOL compiler is free software: you can redistribute
      *>  it and/or modify it under the terms of the GNU General Public
      *>  License as published by the Free Software Foundation, either
      *>  version 3 of the License, or (at your option) any later
      *>  version.
      *>
      *>  GnuCOBOL is distributed in the hope that it will be useful,
      *>  but WITHOUT ANY WARRANTY; without even the implied warranty of
      *>  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      *>  GNU General Public License for more details.
      *>
      *>  You should have received a copy of the GNU General Public
      *>  License along with GnuCOBOL.
      *>  If not, see <https://www.gnu.org/licenses/>.


      *>   Colors
       78  COB-COLOR-BLACK                  VALUE 0.
       78  COB-COLOR-BLUE                   VALUE 1.
       78  COB-COLOR-GREEN                  VALUE 2.
       78  COB-COLOR-CYAN                   VALUE 3.
       78  COB-COLOR-RED                    VALUE 4.
       78  COB-COLOR-MAGENTA                VALUE 5.
       78  COB-COLOR-YELLOW                 VALUE 6.
       78  COB-COLOR-WHITE                  VALUE 7.

      *>   mouse mask, apply to COB-MOUSE-FLAGS
       78  COB-AUTO-MOUSE-HANDLING          VALUE 1.
       78  COB-ALLOW-LEFT-DOWN              VALUE 2.
       78  COB-ALLOW-LEFT-UP                VALUE 4.
       78  COB-ALLOW-LEFT-DOUBLE            VALUE 8.
       78  COB-ALLOW-MIDDLE-DOWN            VALUE 16.
       78  COB-ALLOW-MIDDLE-UP              VALUE 32.
       78  COB-ALLOW-MIDDLE-DOUBLE          VALUE 64.
       78  COB-ALLOW-RIGHT-DOWN             VALUE 128.
       78  COB-ALLOW-RIGHT-UP               VALUE 256.
       78  COB-ALLOW-RIGHT-DOUBLE           VALUE 512.
       78  COB-ALLOW-MOUSE-MOVE             VALUE 1024.
       78  COB-ALLOW-ALL-SCREEN-ACTIONS     VALUE 16384. *> reserved

      *> Values that may be returned in CRT STATUS (or COB-CRT-STATUS)
      *> Normal return - Value 0000
       78  COB-SCR-OK                       VALUE  0.

      *>  Function keys - Values 1xxx
       78  COB-SCR-F1                       VALUE  1001.
       78  COB-SCR-F2                       VALUE  1002.
       78  COB-SCR-F3                       VALUE  1003.
       78  COB-SCR-F4                       VALUE  1004.
       78  COB-SCR-F5                       VALUE  1005.
       78  COB-SCR-F6                       VALUE  1006.
       78  COB-SCR-F7                       VALUE  1007.
       78  COB-SCR-F8                       VALUE  1008.
       78  COB-SCR-F9                       VALUE  1009.
       78  COB-SCR-F10                      VALUE  1010.
       78  COB-SCR-F11                      VALUE  1011.
       78  COB-SCR-F12                      VALUE  1012.
       78  COB-SCR-F13                      VALUE  1013.
       78  COB-SCR-F14                      VALUE  1014.
       78  COB-SCR-F15                      VALUE  1015.
       78  COB-SCR-F16                      VALUE  1016.
       78  COB-SCR-F17                      VALUE  1017.
       78  COB-SCR-F18                      VALUE  1018.
       78  COB-SCR-F19                      VALUE  1019.
       78  COB-SCR-F20                      VALUE  1020.
       78  COB-SCR-F21                      VALUE  1021.
       78  COB-SCR-F22                      VALUE  1022.
       78  COB-SCR-F23                      VALUE  1023.
       78  COB-SCR-F24                      VALUE  1024.
       78  COB-SCR-F25                      VALUE  1025.
       78  COB-SCR-F26                      VALUE  1026.
       78  COB-SCR-F27                      VALUE  1027.
       78  COB-SCR-F28                      VALUE  1028.
       78  COB-SCR-F29                      VALUE  1029.
       78  COB-SCR-F30                      VALUE  1030.
       78  COB-SCR-F31                      VALUE  1031.
       78  COB-SCR-F32                      VALUE  1032.
       78  COB-SCR-F33                      VALUE  1033.
       78  COB-SCR-F34                      VALUE  1034.
       78  COB-SCR-F35                      VALUE  1035.
       78  COB-SCR-F36                      VALUE  1036.
       78  COB-SCR-F37                      VALUE  1037.
       78  COB-SCR-F38                      VALUE  1038.
       78  COB-SCR-F39                      VALUE  1039.
       78  COB-SCR-F40                      VALUE  1040.
       78  COB-SCR-F41                      VALUE  1041.
       78  COB-SCR-F42                      VALUE  1042.
       78  COB-SCR-F43                      VALUE  1043.
       78  COB-SCR-F44                      VALUE  1044.
       78  COB-SCR-F45                      VALUE  1045.
       78  COB-SCR-F46                      VALUE  1046.
       78  COB-SCR-F47                      VALUE  1047.
       78  COB-SCR-F48                      VALUE  1048.
       78  COB-SCR-F49                      VALUE  1049.
       78  COB-SCR-F50                      VALUE  1050.
       78  COB-SCR-F51                      VALUE  1051.
       78  COB-SCR-F52                      VALUE  1052.
       78  COB-SCR-F53                      VALUE  1053.
       78  COB-SCR-F54                      VALUE  1054.
       78  COB-SCR-F55                      VALUE  1055.
       78  COB-SCR-F56                      VALUE  1056.
       78  COB-SCR-F57                      VALUE  1057.
       78  COB-SCR-F58                      VALUE  1058.
       78  COB-SCR-F59                      VALUE  1059.
       78  COB-SCR-F60                      VALUE  1060.
       78  COB-SCR-F61                      VALUE  1061.
       78  COB-SCR-F62                      VALUE  1062.
       78  COB-SCR-F63                      VALUE  1063.
       78  COB-SCR-F64                      VALUE  1064.
      *>  Exception keys - Values 2xxx
       78  COB-SCR-PAGE-UP                  VALUE  2001.
       78  COB-SCR-PAGE-DOWN                VALUE  2002.
       78  COB-SCR-KEY-UP                   VALUE  2003.
       78  COB-SCR-KEY-DOWN                 VALUE  2004.
       78  COB-SCR-ESC                      VALUE  2005.
       78  COB-SCR-PRINT                    VALUE  2006.
       78  COB-SCR-TAB                      VALUE  2007.
       78  COB-SCR-BACK-TAB                 VALUE  2008.
       78  COB-SCR-KEY-LEFT                 VALUE  2009.
       78  COB-SCR-KEY-RIGHT                VALUE  2010.
      *>  The following exception keys are currently *only* returned
      *>  on ACCEPT OMITTED
       78  COB-SCR-INSERT                   VALUE  2011.
       78  COB-SCR-DELETE                   VALUE  2012.
       78  COB-SCR-BACKSPACE                VALUE  2013.
       78  COB-SCR-KEY-HOME                 VALUE  2014.
       78  COB-SCR-KEY-END                  VALUE  2015.
      *>  Exception keys for mouse handling
       78  COB-SCR-MOUSE-MOVE               VALUE  2040.
       78  COB-SCR-LEFT-PRESSED             VALUE  2041.
       78  COB-SCR-LEFT-RELEASED            VALUE  2042.
       78  COB-SCR-LEFT-DBL-CLICK           VALUE  2043.
       78  COB-SCR-MID-PRESSED              VALUE  2044.
       78  COB-SCR-MID-RELEASED             VALUE  2045.
       78  COB-SCR-MID-DBL-CLICK            VALUE  2046.
       78  COB-SCR-RIGHT-PRESSED            VALUE  2047.
       78  COB-SCR-RIGHT-RELEASED           VALUE  2048.
       78  COB-SCR-RIGHT-DBL-CLICK          VALUE  2049.
       78  COB-SCR-SHIFT-MOVE               VALUE  2050.
       78  COB-SCR-SHIFT-LEFT-PRESSED       VALUE  2051.
       78  COB-SCR-SHIFT-LEFT-RELEASED      VALUE  2052.
       78  COB-SCR-SHIFT-LEFT-DBL-CLICK     VALUE  2053.
       78  COB-SCR-SHIFT-MID-PRESSED        VALUE  2054.
       78  COB-SCR-SHIFT-MID-RELEASED       VALUE  2055.
       78  COB-SCR-SHIFT-MID-DBL-CLICK      VALUE  2056.
       78  COB-SCR-SHIFT-RIGHT-PRESSED      VALUE  2057.
       78  COB-SCR-SHIFT-RIGHT-RELEASED     VALUE  2058.
       78  COB-SCR-SHIFT-RIGHT-DBL-CLICK    VALUE  2059.
       78  COB-SCR-CTRL-MOVE                VALUE  2060.
       78  COB-SCR-CTRL-LEFT-PRESSED        VALUE  2061.
       78  COB-SCR-CTRL-LEFT-RELEASED       VALUE  2062.
       78  COB-SCR-CTRL-LEFT-DBL-CLICK      VALUE  2063.
       78  COB-SCR-CTRL-MID-PRESSED         VALUE  2064.
       78  COB-SCR-CTRL-MID-RELEASED        VALUE  2065.
       78  COB-SCR-CTRL-MID-DBL-CLICK       VALUE  2066.
       78  COB-SCR-CTRL-RIGHT-PRESSED       VALUE  2067.
       78  COB-SCR-CTRL-RIGHT-RELEASED      VALUE  2068.
       78  COB-SCR-CTRL-RIGHT-DBL-CLICK     VALUE  2069.
       78  COB-SCR-ALT-MOVE                 VALUE  2070.
       78  COB-SCR-ALT-LEFT-PRESSED         VALUE  2071.
       78  COB-SCR-ALT-LEFT-RELEASED        VALUE  2072.
       78  COB-SCR-ALT-LEFT-DBL-CLICK       VALUE  2073.
       78  COB-SCR-ALT-MID-PRESSED          VALUE  2074.
       78  COB-SCR-ALT-MID-RELEASED         VALUE  2075.
       78  COB-SCR-ALT-MID-DBL-CLICK        VALUE  2076.
       78  COB-SCR-ALT-RIGHT-PRESSED        VALUE  2077.
       78  COB-SCR-ALT-RIGHT-RELEASED       VALUE  2078.
       78  COB-SCR-ALT-RIGHT-DBL-CLICK      VALUE  2079.
       78  COB-SCR-WHEEL-UP                 VALUE  2080.
       78  COB-SCR-WHEEL-DOWN               VALUE  2081.
      *>78 COB-SCR-WHEEL-LEFT               VALUE  2082.  *reserved*
      *>78 COB-SCR-WHEEL-RIGHT              VALUE  2083.  *reserved*
       78  COB-SCR-SHIFT-WHEEL-UP           VALUE  2084.
       78  COB-SCR-SHIFT-WHEEL-DOWN         VALUE  2085.
      *>78 COB-SCR-SHIFT-WHEEL-LEFT         VALUE  2086.  *reserved*
      *>78 COB-SCR-SHIFT-WHEEL-RIGHT        VALUE  2087.  *reserved*
       78  COB-SCR-CTRL-WHEEL-UP            VALUE  2088.
       78  COB-SCR-CTRL-WHEEL-DOWN          VALUE  2089.
      *>78 COB-SCR-CTRL-WHEEL-LEFT          VALUE  2090.  *reserved*
      *>78 COB-SCR-CTRL-WHEEL-RIGHT         VALUE  2091.  *reserved*
       78  COB-SCR-ALT-WHEEL-UP             VALUE  2092.
       78  COB-SCR-ALT-WHEEL-DOWN           VALUE  2093.
      *>78 COB-SCR-ALT-WHEEL-LEFT           VALUE  2094.  *reserved*
      *>78 COB-SCR-ALT-WHEEL-RIGHT          VALUE  2095.  *reserved*
      *>  Input validation - Values 8xxx
       78  COB-SCR-NO-FIELD                 VALUE  8000.
       78  COB-SCR-TIME-OUT                 VALUE  8001.
      *>  Other errors - Values 9xxx
       78  COB-SCR-FATAL                    VALUE  9000.
       78  COB-SCR-MAX-FIELD                VALUE  9001.
*>
*>C  copy "wstime.cob".
 01  ws-time.
     03  wsa-date.
       05  wsa-yy        pic 99.
       05  wsa-mm        pic 99.
       05  wsa-dd        pic 99.
     03  wsb-time.
       05  wsb-hh        pic 99.
       05  wsb-mm        pic 99.
       05  wsb-ss        pic 99.
       05  filler        pic xx.
     03  wsd-time.
       05  wsd-hh        pic 99.
       05  wsd-sa        pic x  value ":".
       05  wsd-mm        pic 99.
       05  wsd-sb        pic x  value ":".
       05  wsd-ss        pic 99.
*>
 01  wse-date-block.
     03  wse-date.
         05  wse-year    pic 9(4).
         05  wse-month   pic 99.
         05  wse-days    pic 99.
     03  WSE-Date-9 redefines wse-date
                         pic 9(8).
     03  wse-time.
         05  wse-hh      pic 99.
         05  wse-mm      pic 99.
         05  wse-ss      pic 99.
     03  filler          pic x(7).
*>

*>
 linkage section.
*>***************
*>
>>LISTING OFF   *> Just in case one day it works !!!
*>C  copy "wscall.cob".
*> 14/03/18 vbc - 1.01   WS-CD-Args for passing extra info to called process
*>                        that will help in a cron call by time via menu
*>                        program. picked by position within WS-Args.
*> 14/11/25 vbc - 1.02 - Chg WS-Term-Code from 9 to 99.
*>
 01  WS-Calling-Data.
     03  WS-Called       pic x(8).
     03  WS-Caller       pic x(8).
     03  WS-Del-Link     pic x(8).
     03  WS-Term-Code    pic 99.
*>                                 new 18/5/13
     03  WS-Process-Func pic 9.
     03  WS-Sub-Function pic 9.
     03  WS-CD-Args      pic x(13).    *> Changed / Added 14/03/18
*>
*>C  copy "wssystem.cob"   replacing System-Record by WS-System-Record.
*>
*>*******************************************
*>                                          *
*>  Record Definition For The System File   *
*>                                          *
*>*******************************************
*>  File size 1024 with fillers
*>   Cleared down update details 01/02/09 to 12/06/13
*>
*> 22/09/15 vbc - Added Param-Restrict (Access) within a current filler.
*>                Set this will stop display of option Z in sub-system menus.
*>                Need to detect actual user though when setup or could just use
*>                chown for sys002 to admin user?
*> 25/06/16 vbc - Added RDBMS-Port & needs RDBMS-Host, RDBMS-Socket.
*>                Increased 'System-data' from 384 to 512 bytes & removed O/E
*>                  Block (128) as it is unused.
*> 26/06/16 vbc - Updated MySQL Load scripts ACASDB.sql in ACAS/mysql.
*>                  Prima is yet to be done !!!
*> 19/10/16 vbc - Changed PL-Approp-AC in IRS block from 9(5) to 9(6) for GL
*>                support & reduced filler by 1.
*>                With IRS data mapped into ACAS the IRS block can reduce to 32 bytes
*>                Just need to change all of the IRS programs to use ACAS fields but
*>                also NEED to change the date processing to use same in rest of ACAS
*>                and not binary days since 01/01/2000 and hold dates in dd/mm/yy form.
*>                Added 2 88s to Op-System for IRS.
*> 27/10/16 vbc - Changed level-5 to IRS instead of omitted O/E.
*> 15/01/18 vbc - Added Stats-Date-Period with a filler & vers = 14.
*> 02/02/18 vbc - Replaced file-statuses with filler x(32).
*> 10/02/18 vbc - For PL-Approp-AC6 move filler to beginning of field as irs
*>                does not need the leading digit (uses only 5).
*> 17/03/18 vbc - Added SL-Invoice-Lines within last filler so gone from 45 to 43.
*> 18/03/18 vbc - Added false for Level-5 & 6, e.g., zero.
*> 06/06/18 vbc - Added six new fields as bin-long to support for G-L and IRS used at same time.
*>                RDBMS needs to be updated. Done 06/06/16 -> Mariadb backups.
*>                sys002 needs to be updated if implemented.
*>                systemMT needs to be updated (in un/load moves).
*> 03/06/20 vbc - Changes to some RDBMS values.
*> 10/12/22 vbc - Remove File-Duplicates-In-Use - not used.
*> 14/04/23 vbc - SL-Autogen added (& PL-Autogen) both using FILLER space.
*> 15/05/23 vbc - SL-Next-Rec and PL-Next-Rec bin-short unsigned for next Autogen record key.
*> 26/06/23 vbc - Added Company-Email repacing filler.
*> 09/09/23 vbc - Pre support for OE but as comments for now as will not be used in ACAS - pointless.
*> 10/09/23 vbc - Removed condition Payroll-No as not used.
*> 13/03/24 vbc - In fillers added fields SL-BO-Flag and Stk-BO-Active,
*> 18/12/24 vbc - Clean up remd out texts & added Co. Phone No reducing filler.
*> 14/11/25 vbc - Support for Payroll in use that replaces OE usage as not needed.
*>
 01
 WS-System-Record.
*>******************
*>   System Data   *
*>******************
     03  System-Data-Block.               *>  512 bytes (25/06/16)
 05
 WS-System-Record-Version-Prime


 binary-char.
 05
 WS-System-Record-Version-Secondary
 binary-char.
         05  Vat-Rates                    comp.
             07 Vat-Rate-1   pic 99v99.   *> Standard rate
             07 Vat-Rate-2   pic 99v99.   *> Reduced rate
             07 Vat-Rate-3   pic 99v99.   *> Minimal or exempt
             07 Vat-Rate-4   pic 99v99.   *> 2b used for local sales tax   Not UK
             07 Vat-Rate-5   pic 99v99.   *> 2b used for local sales tax   Not UK
         05  Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5.
         05  Cyclea          binary-char.  *> 99.
         05  Scycle Redefines cyclea  binary-char.
         05  Period          binary-char.  *> 99.
         05  Page-Lines      binary-char  unsigned. *> 999. Portrait / default
         05  Next-Invoice    binary-long. *> 9(8) comp.
         05  Run-Date        binary-long. *> 9(8) comp.
         05  Start-Date      binary-long. *> 9(8) comp.
         05  End-Date        binary-long. *> 9(8) comp.
         05  Suser.                       *> IRS
             07  Usera       pic x(32).
         05  User-Code       pic x(32).   *> encrypted username not used on OS versions so also b 4 client?
         05  Address-1       pic x(24).
         05  Address-2       pic x(24).
         05  Address-3       pic x(24).
         05  Address-4       pic x(24).
         05  Post-Code       pic x(12).   *> or ZipCode size should cover all countries
         05  Country         pic x(24).
         05  Print-Spool-Name pic x(48).
         05  Phone-No        pic x(12).  *> added 21/10/25 reducing filler.
         05  FILLER          pic x(20).
         05  Pass-Value      pic 9.
         05  Level.
             07  Level-1     pic 9.
                 88  G-L                    value 1.    *> General (Nominal) ledger
             07  Level-2     pic 9.
                 88  B-L                    value 1.    *> Purchase (Payables) ledger
             07  Level-3     pic 9.
                 88  S-L                    value 1.    *> Sales (Receivables) ledger
             07  Level-4     pic 9.
                 88  Stock                  value 1.    *> Stock Control (Inventory)
             07  Level-5     pic 9.
                 88  IRS                    value 1.    *> IRS used (instead of General).
                 88  IRS-No                 value zero. *> IRS NOT Used.
             07  Level-6     pic 9.
                 88  Payroll                value 1.    *> Payroll - USA
         05  Pass-Word       pic x(4).
         05  Host            pic 9.
             88  Multi-User                 value 1.
         05  Op-System       pic 9.
             88  valid-os-type              values 1 2 3 4 5 6.
             88  No-OS                      value zero.
             88  Dos                        value 1.
             88  Windows                    value 2.
             88  Mac                        value 3.
             88  Os2                        value 4.
             88  Unix                       value 5.
             88  Linux                      value 6.
             88  OS-Single                  values 1 2 4.
         05  Current-Quarter pic 9.
         05  RDBMS-Flat-Statuses.
             07  File-System-Used  pic 9.
                 88  FS-Cobol-Files-Used    value zero.
                 88  FS-MySql-Used          value 1.
                                          *> THESE NOT IN USE at this time
                 88  FS-RDBMS-Used          value 1.  *> Was generic
*>                 88  FS-Oracle-Used         value 3.  *> ditto   -  change values to order in which
*>                 88  FS-Postgres-Used       value 2.  *> ditto       they are implemented
*>                 88  FS-DB2-Used            value 4.  *> ditto        or made available
*>                 88  FS-MS-SQL-Used         value 5.  *> ditto
*>                 88  FS-ODBC-Used           value 6.  *> ditto
                 88  FS-Valid-Options       values 0 thru 1.    *> 5. (not in use unless 1-5)
             07  File-Duplicates-In-Use pic 9.           *> No longer in use
                 88  FS-Duplicate-Processing value 1.    *>  Ditto
         05  Maps-Ser.      *> Not needed in OpenSource version, = 9999 (No Maintenance Contract]
             07  Maps-Ser-xx pic xx.        *> Allows for 36^2  customers = 60,466,176
             07  Maps-Ser-nn binary-short.  *>     x  129600 - 2  - Very very large.
         05  Date-Form       pic 9.
             88  Date-Valid-Formats         values 1 2 3.
         05  Data-Capture-Used pic 9.
             88  DC-Cobol-Standard          value zero.
             88  DC-GUI                     value 1.
             88  DC-Widget                  value 2.
         05  RDBMS-DB-Name   pic x(12)      value "ACASDB".     *> change in setup
         05  RDBMS-User      pic x(12)      value "ACAS-User".  *> change in setup
         05  RDBMS-Passwd    pic x(12)      value "PaSsWoRd".   *> change in setup
         05  VAT-Reg-Number  pic x(11)      value spaces.
         05  Param-Restrict  pic x.                             *> Only via ACAS?
         05  RDBMS-Port      pic x(5)       value "3306".       *> change in setup
         05  RDBMS-Host      pic x(32)      value spaces.       *> change in setup
         05  RDBMS-Socket    pic x(64)      value spaces.       *> change in setup v3
         05  Stats-Date-Period pic 9(4).                      *> added 15/01/18.
         05  Company-Email   pic x(30).                         *> changed from filler 26/06/23
*>***************
*>   G/L Data   *
*>***************
     03  General-Ledger-Block.               *> 80 bytes
         05  P-C             pic x.
             88  Profit-Centres             value "P".
             88  Branches                   value "B".
         05  P-C-Grouped     pic x.
             88  Grouped                    value "Y".
         05  P-C-Level       pic x.
             88  Revenue-Only               value "R".
         05  Comps           pic x.
             88  Comparatives               value "Y".
         05  Comps-Active    pic x.
             88  Comparatives-Active        value "Y".
         05  M-V             pic x.
             88  Minimum-Validation         value "Y".
         05  Arch            pic x.
             88  Archiving                  value "Y".
         05  Trans-Print     pic x.
             88  Mandatory                  value "Y".
         05  Trans-Printed   pic x.
             88  Trans-Done                 value "Y".
         05  Header-Level    pic 9.                      *> Not directly used in sys002 but anywhere ?
         05  Sales-Range     pic 9.
         05  Purchase-Range  pic 9.
         05  Vat             pic x.
             88  Auto-Vat                   value "Y".
         05  Batch-Id        pic x.
             88  Preserve-Batch             value "Y".
         05  Ledger-2nd-Index pic x.                     *> But file uses SINGLE INDEX only & gl030 uses a table.
             88  Index-2                    value "Y".
         05  IRS-Instead     pic x.
             88  IRS-Used                   value "Y".
             88  IRS-Both-Used              value "B".   *> 26/11/16
         05  Ledger-Sec      binary-short.  *> 9(4) comp
         05  Updates         binary-short.  *> 9(4) comp
         05  Postings        binary-short.  *> 9(4) comp
         05  Next-Batch      binary-short.  *> 9(4) comp  should be unsigned used for all ledgers
         05  Extra-Charge-Ac binary-long.   *> 9(8) comp        NOTHING IS USING THIS FIELD IN SALES or PURCHASE
         05  Vat-Ac          binary-long.   *> 9(8) comp
         05  Print-Spool-Name2 pic x(48).
*>******************
*>   P(B)/L Data   *
*>******************
     03  Purchase-Ledger-Block.             *> 88 bytes
         05  Next-Folio      binary-long.   *> 9(8) comp
         05  BL-Pay-Ac       binary-long.   *> 9(8) comp
         05  P-Creditors     binary-long.   *> 9(8) comp
         05  BL-Purch-Ac     binary-long.   *> 9(8) comp
         05  BL-End-Cycle-Date binary-long. *> 9(8) comp
         05  BL-Next-Batch   binary-short.  *> 9(4) comp  should be unsigned - unused ?
         05  Age-To-Pay      binary-char.   *> 9(4) comp should be unsigned
         05  Purchase-Ledger pic x.
             88  P-L-Exists                 value "Y".
         05  PL-Delim        pic x.
         05  Entry-Level     pic 9.
         05  P-Flag-A        pic 9.
         05  P-Flag-I        pic 9.
         05  P-Flag-P        pic 9.
         05  PL-Stock-Link   pic x.
         05  Print-Spool-Name3 pic x(48).
         05  PL-Autogen      pic x          value space.        *> added 14/04/23 NOT USED YET
         05  PL-Next-Rec     binary-short unsigned.            *> 2 bytes 0 - 65k
         05  FILLER          pic x(7).
*>***************
*>   S/L Data   *
*>***************
     03  Sales-Ledger-Block.                *> 128 bytes
         05  Sales-Ledger    pic x.
             88  S-L-Exists                 value "Y".
         05  SL-Delim        pic x.
         05  Oi-3-Flag       pic x.         *> 'Y' used in sl060 why?
         05  Cust-Flag       pic x.
         05  Oi-5-Flag       pic x.
         05  S-Flag-Oi-3     pic x.         *> 'Z' when otm3 created, used in sl060 why? NO LONGER USED
         05  Full-Invoicing  pic 9.
         05  S-Flag-A        pic 9.         *> '1' used in sl060 why?
         05  S-Flag-I        pic 9.         *> '2' used in sl060 why?
         05  S-Flag-P        pic 9.
         05  SL-Dunning      pic 9.
         05  SL-Charges      pic 9.
         05  Sl-Own-Nos      pic x.
         05  SL-Stats-Run    pic 9.
         05  Sl-Day-Book     pic 9.
         05  invoicer        pic 9.
             88  I-Level-0                  value 0.  *> show totals only (no net & vat) not used?
             88  I-Level-1                  value 1.  *> Show net, vat
             88  I-Level-2                  value 2.  *> show Details + vat etc looks wrong in sl910 totals only (no net & vat)
             88  Not-Invoicing              value 9.  *> show totals only (no net & vat) but not found yet nor level 3 (see sl900)
         05  Extra-Desc      pic x(14).
         05  Extra-Type      pic x.
             88  Discount                   value "D".
             88  Charge                     value "C".
         05  Extra-Print     pic x.
         05  SL-Stock-Link   pic x.
         05  SL-Stock-Audit  pic x.
             88  Stock-Audit-On             value "Y".   *> Invoicing will create an audit record (15/05/13)
         05  SL-Late-Per     pic 99v99    comp.
         05  SL-Disc         pic 99v99    comp.
         05  Extra-Rate      pic 99v99    comp.
         05  SL-Days-1       binary-char.    *> 999  comp.
         05  SL-Days-2       binary-char.    *> 999  comp.
         05  SL-Days-3       binary-char.    *> 999  comp.
         05  SL-Credit       binary-char.    *> 999  comp.
         05  FILLER          binary-short.   *> No longer used.
         05  SL-Min          binary-short.   *> 9999  comp.
         05  SL-Max          binary-short.   *> 9999  comp.
         05  PF-Retention    binary-short.   *> 9999  comp.
         05  First-Sl-Batch  binary-short.   *> 9999  comp.   *>unused ?
         05  First-Sl-Inv    binary-long.    *> 9(8) comp.
         05  SL-Limit        binary-long.    *> 9(8) comp.
         05  SL-Pay-Ac       binary-long.    *> 9(8) comp.
         05  S-Debtors       binary-long.    *> 9(8) comp.
         05  SL-Sales-Ac     binary-long.    *> 9(8) comp.
         05  S-End-Cycle-Date binary-long.   *> 9(8) comp.
         05  SL-Comp-Head-Pick Pic x.
             88  SL-Comp-Pick               value "Y".
         05  SL-Comp-Head-Inv  pic x.
             88  SL-Comp-Inv                value "Y".
         05  SL-Comp-Head-Stat pic x.
             88  SL-Comp-Stat               value "Y".
         05  SL-Comp-Head-Lets pic x.
             88  SL-Comp-Lets               value "Y".
         05  SL-VAT-Printed  pic x.
             88  SL-VAT-Prints              value "Y".
         05  SL-Invoice-Lines pic 99.
         05  SL-Autogen      pic x          value space.        *> added 14/04/23
         05  SL-Next-Rec     binary-short unsigned.             *> 2 bytes 0 - 65k
         05  SL-BO-Flag      pic x          value space.      *> support for Back Ordering - may be = Y for true.
         05  SL-BO-Default   pic x.
         05  FILLER          pic X(14).                       *> was x (16)
*> GL overflow
         05  GL-BL-Pay-Ac    binary-long.    *> 9(8) comp    THESE 6 ADDED 06/06/18 to poss. support GL and IRS
         05  GL-P-Creditors  binary-long.    *> 9(8) comp    RUNNING at same time.
         05  GL-BL-Purch-Ac  binary-long.    *> 9(8) comp
         05  GL-SL-Pay-Ac    binary-long.    *> 9(8) comp.
         05  GL-S-Debtors    binary-long.    *> 9(8) comp.
         05  GL-SL-Sales-Ac  binary-long.    *> 9(8) comp.
*>***************
*> Stock Data   *
*>***************
*>
     03  Stock-Control-Block.                *> 88 bytes
         05  Stk-Abrev-Ref   pic x(6).
         05  Stk-Debug       pic 9.          *> T/F (1/0).
         05  Stk-Manu-Used   pic 9.          *> T/F (Bomp/Wip)
         05  Stk-OE-Used     pic 9.          *> T/F.
         05  Stk-Audit-Used  pic 9.          *> T/F.
         05  Stk-Mov-Audit   pic 9.          *> T/F.
         05  Stk-Period-Cur  pic x.          *> M=Monthly, Q=Quarterly, Y=Yearly
         05  Stk-Period-dat  pic x.          *>  --  ditto  --
         05  FILLER          pic x.          *> was stk-date-form
         05  Stock-Control   pic x.
             88  Stock-Control-Exists   value "Y".
         05  Stk-Averaging   pic 9.          *> T/F.
             88  Stock-Averaging        value 1.
         05  Stk-Activity-Rep-Run pic 9.     *> T/F.  =17 bytes 0=no, 1=add, 2=del, 3=both
         05  Stk-BO-Active   pic x.          *> was filler 13/03/24
         05  Stk-Page-Lines  binary-char unsigned.  *> 9999 comp. Taken from Print-Lines
         05  Stk-Audit-No    binary-char unsigned.  *> 9999 comp.
         05  FILLER          pic x(68).             *> 64    (just in case)
         05  Client             pic x(24). 	*> 		24      *> Not needed as will use suser
         05  Next-Post          pic 9(5).  	*> 		29                                                  N   5
         05  Vat-Rates2.                                             *> these can be replaced by the other VAT blk
             07  vat1           pic 99v99. 	*> 		33   *> Standard  changed from vat (11/06/13)
             07  vat2           pic 99v99. 	*> 		37   *> reduced 1 [not yet used]
             07  vat3           pic 99v99. 	*> 		41   *> reduced 2 [not yet used]
         05  Vat-Group redefines Vat-Rates2.
             07  Vat-Psent      pic 99v99    occurs 3.
         05  FILLER redefines PL-Approp-AC6.
             07  FILLER         pic 9.           *>                   loose leading char for IRS
             07  PL-Approp-AC   pic 9(5).        *>                   For IRS
         05  FILLER             pic x(59).       *>             128  Old fn-1 to 5 files
     03  IRS-Data-Block redefines IRS-Entry-Block.
         05  FILLER-Dummy4   pic x(128).
*>
*>>W Msg29 Caution: One or more replacing sources not found
*>C  copy "wsnames.cob".
*>
*> Sales, Purchase, Stock, General & now IRS for v3.3 with integrated IRS
*>    for use in xl150 and ??
*>
*>  Files used in Sales, Stock, Purchase, General & IRS
*> 17/11/16 vbc - Added IRS files + their renaming with irs prefix.
*> 04/12/16 vbc - Added irs055 sort file as file-38.
*> 09/05/23 vbc - Added PL & SL autogen (files04, 30 increased count to 38
*> 16/03/24 vbc - Added Sales Bo-Stk-Itm as file31  increased count to 39
*> 21/10/25 vbc - Added Payroll - USA/Canada - other files needed for elsewhere
*>                inc UK / Europe etc.
*>
 01  File-Defs.
     02  file-defs-a.
         03  pre-trans-name   pic x(532)  value "pretrans.tmp". *> gl071
         03  post-trans-name  pic x(532)  value "postrans.tmp". *> gl071
*>C  copy "file00.cob".    *> "system"
     03  file-0         pic x(532)        value "system.dat".
*>                        No file 1
*>C  copy "file02.cob".    *> "archive".
     03  file-2         pic x(532)        value "archive.dat".
*>C  copy "file03.cob".    *> "final".
     03  file-3         pic x(532)        value "final.dat".
*>C  copy "file04.cob".    *> "SLautogen"
     03  file-4         pic x(532)        value "slautogen.dat".
*>C  copy "file05.cob".    *> "ledger".
     03  file-5         pic x(532)        value "ledger.dat".
*>C  copy "file06.cob".    *> "posting".
     03  file-6         pic x(532)        value "posting.dat".
*>C  copy "file07.cob".    *> "batch".
     03  file-7         pic x(532)        value "batch.dat".
*>C  copy "file08.cob".    *> "postings2irs.dat"
     03  file-8         pic x(532)        value "postings2irs.dat".
*>C  copy "file09.cob".    *> "tmp-stock".
     03  file-9         pic x(532)        value "tmp-stock.dat".
*>C  copy "file10.cob".    *> "staudit".
     03  file-10        pic x(532)        value "staudit.dat".
*>C  copy "file11.cob".    *> "stockctl".
     03  file-11        pic x(532)        value "stockctl.dat".
*>C  copy "file12.cob".    *> "salesled".
     03  file-12        pic x(532)        value "salesled.dat".
*>C  copy "file13.cob".    *> "value.dat"
     03  file-13        pic x(532)        value "value.dat".
*>C  copy "file14.cob".    *> "delivery.dat"
     03  file-14        pic x(532)        value "delivery.dat".
*>C  copy "file15.cob".    *> "analysis.dat"
     03  file-15        pic x(532)        value "analysis.dat".
*>C  copy "file16.cob".    *> "invoice ".
     03  file-16        pic x(532)        value "invoice.dat".
*>C  copy "file17.cob".    *> "delinvno".
     03  file-17        pic x(532)        value "delinvno.dat".
*>C  copy "file18.cob".    *> "openitm2".
     03  file-18        pic x(532)        value "openitm2.dat".
*>C  copy "file19.cob".    *> "openitm3".
     03  file-19        pic x(532)        value "openitm3.dat".
*>C  copy "file20.cob".    *> "oisort".
     03  file-20        pic x(532)        value "oisort.wrk".
*>C  copy "file21.cob".    *> "work.tmp"
     03  file-21        pic x(532)        value "work.tmp".
*>C  copy "file22.cob".    *> "purchled"
     03  file-22        pic x(532)        value "purchled.dat".
*>C  copy "file23.cob".    *> "delfolio.dat"
     03  file-23        pic x(532)        value "delfolio.dat".
*>C  copy "file24.cob".    *> dummy to build file-02
     03  file-24        pic x(532)        value spaces.
*>                        No file 25
*>C  copy "file26.cob".    *> "pinvoice"
     03  file-26        pic x(532)        value "pinvoice.dat".
*>C  copy "file27.cob".    *> "poisort"
     03  file-27        pic x(532)        value "poisort.wrk".
*>C  copy "file28.cob".    *> "openitm4"
     03  file-28        pic x(532)        value "openitm4.dat".
*>C  copy "file29.cob".    *> "openitm5"
     03  file-29        pic x(532)        value "openitm5.dat".
*>C  copy "file30.cob".    *> "PLautogen.dat"
     03  file-30        pic x(532)        value "plautogen.dat".
*>C  copy "file31.cob".    *> "boStkitm.dat" NEw 16/03/24
     03  file-31        pic x(532)        value "bostkitm.dat".
*>C  copy "file32.cob".    *> "pay.dat"
     03  file-32        pic x(532)        value "pay.dat".
*>C  copy "file33.cob".    *> "cheque.dat"
     03  file-33        pic x(532)        value "cheque.dat".
         03  file-34          pic x(532)  value "irsacnts.dat".        *> IRS ex file 1  These 4 added 19/10/16 for IRS integration
         03  file-35          pic x(532)  value "irsdflt.dat".         *> IRS ex file 3  all name have 'irs' prefix.
         03  file-36          pic x(532)  value "irspost.dat".         *> IRS ex file 4
         03  file-37          pic x(532)  value "irsfinal.dat".        *> IRS ex file 5
         03  file-38          pic x(532)  value "postsort.dat".        *> IRS ex irs055 sort file.

*> Code for Payroll  AND INCREASE occurs both times
         03  file-39          pic x(532)  value "pyact.dat".               *> PY account
         03  file-40          pic x(532)  value "pychk.dat".               *> PY check / bacs
         03  file-41          pic x(532)  value "pycoh.dat".               *> PY company history
         03  file-42          pic x(532)  value "pyded.dat".               *> PY deduction {/ earnings}
         03  file-43          pic x(532)  value "pyemp.dat".               *> PY employee master
         03  file-44          pic x(532)  value "pyhis.dat".               *> PY employee (pay) history
         03  file-45          pic x(532)  value "pyhrs.dat".               *> PY pay trans
         03  file-46          pic x(532)  value "pypay.dat".               *> PY pay detail jrn + header ???
         03  file-47          pic x(532)  value "pypr1.dat".               *> PY param 1
         03  file-48          pic x(532)  value "pypr2.dat".               *> PY param 2
*> TABLES Blk 1
         03  file-49          pic x(532)  value "pycalm.dat".              *> PY  calx - x = s,m,h, x?
         03  file-50          pic x(532)  value "pycals.dat".              *> PY
         03  file-51          pic x(532)  value "pycalh.dat".              *> PY
         03  file-52          pic x(532)  value "pycalx.dat".              *> PY  california special tables ???
         03  file-53          pic x(532)  value "pylwt.dat".               *> PY  tax table ???
         03  file-54          pic x(532)  value "pyswtaa.dat".             *> PY  swt aa = State abbrev. code Only one used
         03  file-55          pic x(532)  value "pyglcoann.dat".           *> PY gl CoA transfer ??
         03  file-56          pic x(532)  value "pyglgjbss.dat".           *> PY  ???
*> Not sure about these two up/down
           03  file-57          pic x(532)  value "pycal.dat".             *> PY  ??? calm,s,h etc
*>
     02  filler         redefines file-defs-a.
         03  System-File-Names   pic x(532) occurs 58.            *> 39 chg for sales BO file plus py
     02  File-Defs-Count         binary-short value 58.           *> MUST be the same as above occurs
     02  File-Defs-os-Delimiter  pic x.                           *> if = \ or / then paths have been set.
*>
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
         05  col   2     pic 9(7)          source   Emp-No.
         05  col  10     pic x(32)         source   Emp-Search-Name.   *> but could be  Emp-Name.


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
         05  col  61     pic zz,zz9.99     source Emp-Comp-Accum.
         05  col  84                       value "Comp. Time Used:".
         05  col  99     pic zz,zz9.99     source Emp-Comp-Used.
*>
*>
 01  type control Footing Final line plus 2.
     03  col 1           pic x(34)         value "Total - Employee Account Records :".
     03  col 36          pic zzz9          source WS-Rec-Cnt.
     03  col 51                            value "Employee no range From: ".
     03  col 78          pic z(6)9         source WS-Emp-From-No.
     03  col 86                            value "To: ".
     03  col 89          pic Z(6)9         source WS-Emp-To-No.
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
     perform  ca020-From-Date-2-Formatted.
     start    PY-Pay-File FIRST.
     perform  forever
              read     PY-Pay-File at end
                       exit perform
              end-read
              move     Pay-Emp-No to Emp-No
              read     PY-Employee-File
              if       PY-Emp-Status not = "00"
                       exit perform
              end-if



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
 ca000-Routines               section.  *> May be enbedded ??
*>***********************************
*>
 ca000-6100                   section.
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
 ca000-7000                   section.
*>***********************************
*> Clear accumulators
     move     zeros to WS-Reg-Wages
                       WS-Other-Earn
                       WS-Gross
                       WS-FWT
                       WS-SWT
                       WS-LWT
                       WS-FICA
                       WS-SDI
                       WS-EIC
                       WS-Other-Ded
                       WS-Net
                       WS-Employer-Cost
                       WS-Tips
                       WS-Tips-Reported
                       WS-Co-Fica
                       WS-Co-Futa
                       WS-Co-SUI
                       WS-Comp-Earned
                       WS-Comp-Taken
                       WS-SL-Taken
                       WS-Vac-Taken.
     perform  varying F from 1 by 1 until F > 5
              move     zeros to  WS-SYS (F)
     end-perform.
     perform  varying F from 1 by 1 until F > 3
              move     zeros to  WS-EMP (F)
     end-perform.
     perform  varying F from 1 by 1 until F > 4
              move     zeros to  WS-Units (F)
     end-perform.
     move     "Y" to WS-Detail-Line.
*>
 ca000-8100                   section.
*>***********************************
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



 ca010-Check-Date-2-Formatted section.
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
 ca030-To-Date-2-Formatted    section.
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
*>C      copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
*>C                                         STATUS by PY-PR1-Status.
*> ***************************************************************
*> ** Author: Gary L. Cutler                                    **
*> **         CutlerGL@gmail.com                                **
*> ** Amendments Vincent B. Coen                                **
*> **         vbcoen@gmail.com                                  **
*> **                                                           **
*> ** This copybook defines an EVALUATE statement capable of    **
*> ** translating two-digit FILE-STATUS codes to a message.     **
*> **                                                           **
*> ** Use the REPLACING option to COPY to change the names of   **
*> ** the MSG and STATUS identifiers to                         **
*> ** the names your program needs.                             **
*> Such as replacing STATUS by fs-reply msg by exception-msg.   **
*>                                                              **
*> ** chg 09/08/23 vbc for missing statuses                     **
*> ** Chg 11/12/23 vbc for missing statuses                     **
*> ** Chg 10/04/25 vbc match all quotes & spacing/layout        **
*> ** chg to FREE format                                        **
*> ** Chg 24/08/25 vbc #91 description.                         **
*> ** Chg 15.11.25 vbc Replace all ' for "                      **
*> ***************************************************************
*>
 EVALUATE PY-PR1-Status
 WHEN "00" MOVE "Success                  " TO WS-Eval-Msg
 WHEN "02" MOVE "Success Duplicate        " TO WS-Eval-Msg
 WHEN "04" MOVE "Success Incomplete       " TO WS-Eval-Msg
 WHEN "05" MOVE "Success Optional, Missing" TO WS-Eval-Msg
 when "06" move "Multiple Records LS      " TO WS-Eval-Msg
 WHEN "07" MOVE "Success No Unit          " TO WS-Eval-Msg
 when "09" move "Success LS Bad Data      " TO WS-Eval-Msg
 WHEN "10" MOVE "End Of File              " TO WS-Eval-Msg
 WHEN "14" MOVE "Out Of Key Range         " TO WS-Eval-Msg
 WHEN "21" MOVE "Key Invalid              " TO WS-Eval-Msg
 WHEN "22" MOVE "Key Exists               " TO WS-Eval-Msg
 WHEN "23" MOVE "Key Not Exists           " TO WS-Eval-Msg
 WHEN "24" MOVE "Key Boundary violation   " TO WS-Eval-Msg
 WHEN "30" MOVE "Permanent Error          " TO WS-Eval-Msg
 WHEN "31" MOVE "Inconsistent Filename    " TO WS-Eval-Msg
 WHEN "34" MOVE "Boundary Violation       " TO WS-Eval-Msg
 WHEN "35" MOVE "File Not Found           " TO WS-Eval-Msg
 WHEN "37" MOVE "Permission Denied        " TO WS-Eval-Msg
 WHEN "38" MOVE "Closed With Lock         " TO WS-Eval-Msg
 WHEN "39" MOVE "Conflict Attribute       " TO WS-Eval-Msg
 WHEN "41" MOVE "Already Open             " TO WS-Eval-Msg
 WHEN "42" MOVE "Not Open                 " TO WS-Eval-Msg
 WHEN "43" MOVE "Read Not Done            " TO WS-Eval-Msg
 WHEN "44" MOVE "Record Overflow          " TO WS-Eval-Msg
 WHEN "46" MOVE "Read Error               " TO WS-Eval-Msg
 WHEN "47" MOVE "Input Denied             " TO WS-Eval-Msg
 WHEN "48" MOVE "Output Denied            " TO WS-Eval-Msg
 WHEN "49" MOVE "I/O Denied               " TO WS-Eval-Msg
 WHEN "51" MOVE "Record Locked            " TO WS-Eval-Msg
 WHEN "52" MOVE "End-Of-Page              " TO WS-Eval-Msg
 WHEN "57" MOVE "I/O Linage               " TO WS-Eval-Msg
 WHEN "61" MOVE "File Sharing Failure     " TO WS-Eval-Msg
 WHEN "71" MOVE "Bad Character LS         " TO WS-Eval-Msg
 WHEN "91" MOVE "Feature Not Available    " TO WS-Eval-Msg
          WHEN OTHER
 MOVE "Unknown File PY-PR1-Status      " TO WS-
*>
     END-EVALUATE.

*>>W Msg29 Caution: One or more replacing sources not found
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
      *>>>Info: Total Copy Depth Used = 03;  Caution messages issued =   2
