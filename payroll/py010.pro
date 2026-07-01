       >>source free
*>****************************************************************
*>                       Employee   Entry                        *
*>                                                               *
*>                      This is in three passes namely :-        *
*>                      1. Primary Data incl. name & address etc.*
*>                      2. Earn/Ded & Cost.                      *
*>                      3. Rate Data.                            *
*>                      4. Emp History data entry/amend          *
*>                          from pyupdhis                        *
*>                                                               *
*>                      Each can be selected or                  *
*>                          options 1 & 2 as menu option 4  or.  *
*>                                  1, 2, 3 or 4.                *
*>                                                               *
*>                  MANUAL UPDATE NEEDED.                        *
*>                                                               *
*>  Option 4 only run if emp not had a pay run <<<<<<<<<<    NEEDS EXTRA CODING
*>    This program sets up Emp-Search-Name from Emp-Name         *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       py010.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 19/10/2025.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Employee data Entry.
*>                      This is in three passes namely :-
*>                      1. Primary Data included name & address etc.
*>                      2. Earn/Ded & Cost.
*>                      3. Rate Data.
*>                      4. Update Employee History.
*>
*>                      Each can be selected or
*>                          options 1 & 2 as menu option 4  or.
*>                                  1, 2 & 3.
*>
*>                      Semi-sourced from Basic code from *> empent.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.
*>                      (CBL_) ACCEPT_NUMERIC.c as static.
*>                      MAPS09.
*>**
*>    Functions Used:
*>                      CURRENT-DATE.
*>                      TEST-DATE-YYYYMMDD.
*>                      UPPER-CASE.
*>    Files used :
*>   Defined/Created
*>      X     X         pypr1.   Params
*>      X     X         pyded.   Deductions
*>      X               pyhrs.   Pay Hours Transactions  - NOT HERE THOUGH.
*>      X               pyemp.   Employee Master.
*>      X               pyhis.   Employee History.
*>      X               pyact.   Noninal Account. For IRS.
*>      X               pypay.   Pay Details.
*>      X               pychk.   Check / BACS.
*>      X               pycoh.   Company History.
*>      X      (NOT SS) pyswtss. State & Local withholding tables where ss = State Abbrev. One for each state, but ex Cal.
*>      X               pycals.  s = S,M or H.  One for each category Single, Married, Head of household.
*>      X               pylwt    Other deductions ????.
*>                      pycalx.  Special California table.    NOT for Canada
*>                      pytax.   Tax tables for UK and other countries that have income bands. - Only for UK
*>                               Includes records for NI etc.
*>
*>    Error messages used.
*> System wide:
*>                      SY001, 2, 3, 10, 13.
*> Program specific:
*>                      PY001, 2, 13, 15.
*>                      PY105. 108-110, 115, 119 - 121, 124-127, 129. 131-133, 135-141, 173-176, 180.
*>                      PY223, 229-231
*>**
*> Changes:
*> 20/09/2025 vbc - 1.0.00 Created - starting. Prior to testing.
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
*> 30/10/2025 vbc -        Still working on file rec layouts (ws)+ selects (sel)
*>                         & fd's (fd).
*> 05/11/2025 vbc -        Adding more SS for data input or display and menus.
*>                         Some of which may well go into another program.
*> 23/11/2025 vbc -    .01 Added support for GL for account nos, Testing for
*>                         reset numbers in IRS and GL when building default
*>                         accounts as they may well not exist AND test for
*>                         errors when writing accounts file which will cause an
*>                         abort of this initial creating file functions on first
*>                         using Payroll as a fatal condition.
*>                         Renamed zz section / paragraphs that are normal
*>                         functions into new names starting with ab000 etc
*>                         as very messy.
*>                         WARNING - Absolutely no testing done for GL as I have
*>                         no idea about USA GL CoA's. Might try and reseach
*>                         this at some point when coding completed.
*>                         IN which case these comments will be removed -
*>                         providing I remember.
*> 27/11/2025 vbc -    .02 Screen size now checked for Minimum of 28 lines.
*>                         All other programs wil do the same. Msg SY010 chgd.
*> 02/12/2025 vbc -        Coding completed BUT does need testing as expected.
*> 09/12/2025 vbc -        Increased minimum screen depth = 28 for func keys etc.
*> 10/12/2025 vbc -        Replaced test and on error + goto to use perform
*>                         forever etc - helps keep code neater.
*>
*>
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
*>C  copy "envdiv.cob".
 configuration section.
 source-computer.      Linux.
 object-computer.      Linux.
*> special-names.
*>     console is crt.
 SPECIAL-NAMES.
       CRT STATUS IS COB-CRT-STATUS.
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
*>C  copy "selpyhis.cob".
*>
*> Payroll History
*>
     select  PY-History-File
                             assign        File-45
                             access        dynamic
                             organization  indexed
                             record key is His-Emp-No
                             status        PY-His-Emp-Status.
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
*>C  copy "selpycoh.cob".
*>
*> Payroll Company History
*>
     select  PY-Comp-Hist-File
                             assign        File-41
                             access        dynamic
                             organization  relative
                             relative key  RRN    *> or Coh-Apply-No or ?
                             status        PY-Coh-Status.
*>
*> copy "selpycalx.cob".
*>
*> next 3 are all the same so can use only one stax
*>
*> copy "selpystax.cob".
*> copy "selpyswt.cob".
*> copy "selpylwt.cob".
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
*>  File size 624 bytes padded to 1024 by filler.
*>     RESIZE NEEDED 1/12/25
*>
*> 13/10/25 vbc - Created.
*>  Consider adding to system file as rec #5 after basic testing
*> 08/11/25 vbc - Rec  changed still 1024.
*> 11/11/25 vbc - Moved PR2 fields embedded within PR1 area to PR2 rec size the same.
*> 26/11/25 vbc - Added new field PY-PR2-Last-Employee-no - filler adjusted.
*> 28/11/25 vbc - Added new field PY-PR1-Tax-ID  to ident employer with IRS set
*>                as x(24) as format not known.
*> 09/03/26 vbc - PR2 fields changed from x to bin-short unsigned.
*>   WILL NEED RESIZING..
*>
 01  PY-Param1-Record.
     03  PY-PR1-Block.                         *> Size = 670
         05  PY-PR1-Company-Data.                 *> size 298
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
         05  PY-PR1-Void-Check-Amt    pic 9(5)v99    comp-3.
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
         05  PY-PR1-Check-History-Used   pic x.    *> def N      - or Y
         05  PY-PR1-S-Used               pic x.    *> def N      - or N Semi M
         05  PY-PR1-M-Used               pic x.    *> def Y      - Y  Month
         05  PY-PR1-W-Used               pic x.    *> Def N   "  - Y  Weekly
         05  PY-PR1-B-Used               pic x.    *> def N   "  - Y  Bi Month
         05  PY-PR1-JC-Used              pic x.    *> def N      - Y
         05  PY-PR1-GL-Used              pic x.    *> def N      - or Y
         05  PY-PR1-IRS-Used             pic x.    *> del Y      - or N
         05  PY-PR1-Dflt-Pay-Interval    pic x.    *> def S  could be SMBW - S=Salary,W=Weekly, M=Monthly & B=Bi-Monthly
         05  PY-PR1-Dist-Used            pic x.    *> def N  was binary-char unsigned.    *> def Y ????? what
         05  PY-PR1-Currency-Sign        pic x.    *> Def "$"
         05  PY-PR1-OS-Delimiter         pic x.    *>   / for *nix and \ for windows Used via ACAS param
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
         05  PY-PR1-Rate-Name         pic x(15)       occurs 4.   *> def  "REGULAR"
                                                                  *> def  "OVERTIME" "SPEC. OVERTIME" "COMMISSION"
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
         05  PY-PR1-Max-Ed-Cats       binary-char.  *>
         05  PY-PR1-Max-Swt-Entries   binary-char.  *>            A / marks in use for any one line
         05  PY-PR1-Lo-Ded-Chk-Cat    binary-char.  *>
         05  PY-PR1-Hi-Ded-Chk-Cat    binary-char.  *>
         05  PY-PR1-Lo-Earn-Chk-Cat   binary-char.  *>
         05  PY-PR1-Hi-Earn-Chk-Cat   binary-char.  *>
         05  PY-PR1-Max-Sys-Eds       binary-char.  *> 5
*>
         05  PY-PR1-Print-Spool-Name  pic x(48). *> All 3 from ACAS system params
         05  PY-PR1-Print-Spool-Name2 pic x(48). *> but only 1st used (or is it)
         05  PY-PR1-Print-Spool-Name3 pic x(48). *>     consider creating a pdf file from prt-1
*>
     03  PY-PR2-Block.                        *> Size = 94  COULD BE REC 2 ? (+ filler = 640 or 768 etc) (RRN = 2). sizes wrong
         05  PY-PR2-Year              pic 9(4).  *> current year
         05  PY-PR2-Year-Next         pic 9(4).  *> Year + 1  --- New field
         05  PY-PR2-Last-SM-Apply-No  pic 9(4).  *> def 0
         05  PY-PR2-Last-WB-Apply-No  pic 9(4).  *> def 0
         05  PY-PR2-Hrs-Batch-No      pic 9(4).  *> def 0
         05  PY-PR2-Last-Day-Last-W   pic 9(8).  *> }
         05  PY-PR2-Last-Day-Last-B   pic 9(8).  *> }
         05  PY-PR2-Last-Day-Last-S   pic 9(8).  *> }  use todays to yyyymmdd
         05  PY-PR2-Last-Day-Last-M   pic 9(8).  *> }       error,  may be not ??????
         05  PY-PR2-Check-Date        pic 9(8).  *> }
         05  PY-PR2-Last-Employee-No  pic 9(8)   comp.    *>  ?? NEW for py010 data entry EXCLUDES check digit. allows for # = 64k
         05  PY-PR2-No-Active-Emps    binary-short unsigned.   *> def 0 - NEEDED ??
         05  PY-PR2-No-Employees      binary-short unsigned.   *> def 0 - NEEDED ??
         05  PY-PR2-No-Of-SM-Applies  binary-short unsigned.   *> SIZE emough 65k ?  - 12/02/79 pr2.no.of.xx.applies% = number of sm, wb applies this quarter
         05  PY-PR2-No-Of-WB-Applies  binary-short unsigned.   *> SIZE emough 65k ?    DITTO
         05  PY-PR2-Just-Closed-Year  binary-short unsigned.   *>                    - 12/02/79 pr2.just.closed.year% = no applies run since year end close
         05  PY-PR2-No-Accts          binary-char  unsigned.    *> def 4 = 4 accounts ? is it needed ??
         05  PY-PR2-940-Printed       pic x.     *> N  (or Y)
         05  PY-PR2-941-Printed       pic x.     *> N  (or Y)
         05  PY-PR2-W2-Printed        pic x.     *> N  (or Y)
         05  PY-PR2-Last-Q-Ended      pic 9.     *> 4 ( vals 1, 2, 3 or 4 )
         05  PY-PR2-Last-Check-No     pic 9(15). *> 000000                - 12/02/79 pr2.last.check.no$    = last check number written by PYCHECKS
*>
     03  filler                       pic x(260).  *> could just be 768.
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
*> THESE FIELDS DEFINITIONS MAY NEED CHANGING
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
     03  filler                pic x(11).
*>
*>
*>C  copy "fdpyhis.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Employee History *
*>                 File                     *
*>                                          *
*>*******************************************
*>   Record Size 232 Bytes
*>   see wspyhis.cob for later updates
*>
 fd  PY-History-File.
*>
*>C  copy "wspyhis.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Employee          *
*>       History  File                      *
*>     Uses His-Emp-No as key               *
*>*******************************************
*>  File size 314 bytes.
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 29/10/25 vbc - Created.
*> 09/12/25 vbc - Added xtras DEDs for QTD & YTD
*> 17/03/26 vbc - MCare added for QTD & YTD.
*>
 01  PY-History-Record.
     03  His-Emp-No                    pic 9(7)   comp.
     03  His-QTD                                  comp-3.
         05  His-QTD-Income-Taxable    pic 9(7)v99.
         05  His-QTD-Other-Taxable     pic 9(7)v99.
         05  His-QTD-Other-NonTaxable  pic 9(7)v99.
         05  His-QTD-Fica-Taxable      pic 9(7)v99.
         05  His-QTD-Tips              pic 9(7)v99.
         05  His-QTD-Net               pic 9(7)v99.
         05  His-QTD-EIC               pic 9(7)v99.
         05  His-QTD-FWT               pic 9(7)v99.
         05  His-QTD-SWT               pic 9(7)v99.
         05  His-QTD-LWT               pic 9(7)v99.
         05  His-QTD-FICA              pic 9(7)v99.
         05  His-QTD-SDI               pic 9(7)v99.
         05  His-QTD-MCare             pic 9(7)v99.
         05  His-QTD-Sys               pic 9(7)v99  occurs 5.
         05  His-QTD-Emp               pic 9(7)v99  occurs 3.
         05  His-QTD-Units             pic 9(7)v99  occurs 4.
         05  His-QTD-Other-Ded         pic 9(7)v99.
         05  His-QTD-Extras            pic 9(7)v99  occurs 5. *> extra state/fed deductions enough ?
     03  His-YTD                                  comp-3.
         05  His-YTD-Income-Taxable    pic 9(7)v99.
         05  His-YTD-Other-Taxable     pic 9(7)v99.
         05  His-YTD-Other-NonTaxable  pic 9(7)v99.
         05  His-YTD-Fica-Taxable      pic 9(7)v99.
         05  His-YTD-Tips              pic 9(7)v99.
         05  His-YTD-Net               pic 9(7)v99.
         05  His-YTD-EIC               pic 9(7)v99.
         05  His-YTD-FWT               pic 9(7)v99.
         05  His-YTD-SWT               pic 9(7)v99.
         05  His-YTD-LWT               pic 9(7)v99.
         05  His-YTD-FICA              pic 9(7)v99.
         05  His-YTD-SDI               pic 9(7)v99.
         05  His-YTD-MCare             pic 9(7)v99.
         05  His-YTD-Sys               pic 9(7)v99  occurs 5.
         05  His-YTD-Emp               pic 9(7)v99  occurs 3.
         05  His-YTD-Units             pic 9(7)v99  occurs 4.
         05  His-YTD-Other-Ded         pic 9(7)v99.
         05  His-YTD-Extras            pic 9(7)v99  occurs 5. *> extra state/fed deductions enough ?
     03  filler                        pic x(4).
*>
*>   IS this header rec needed (Last-To-Date ? )
*>
 01  PY-History-Header.
     03  Hdr-His-No                    pic 9(7)   comp.     *> value zero.
     03  Hdr-His-Last-To-Date          pic 9(8)   comp.   *> ccyymmdd
     03  FILLER                        pic x(320).        *> Expansion ?
*>
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
*>  File size 32 bytes.
*>
*> 29/10/25 vbc - Created.
*> 31/10/25 vbc - Renamed act-no to act-gl-no & added act-no.
*>                This subject to using py account info instead
*>                of direct to GL. Note IRS uses 5 and GL 6 digits.
*> 05/11/25 vbc   Chg Act-No to pic 99.
*> 12/11/25 vbc - Chg Gl-No to display from comp.
*>
 01  PY-Accounts-Record.
     03  Act-No              pic 99.
     03  Act-GL-No           pic 9(6).
     03  Act-Desc            pic x(24).
*>
*>
*>C  copy "fdpycoh.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Company History  *
*>              File                        *
*>*******************************************
*>   Record Size 513 Bytes
*>   see wspycoh.cob for later updates
*>
 fd  PY-Comp-Hist-File.
*>
*>C  copy "wspycoh.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Company History   *
*>              File                        *
*>     Uses RRN         as  relative key    *
*>   BUT could be Apply-No                  *
*>*******************************************
*>  File size 513 bytes.    ?? resize <<<<<<<<
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 30/10/25 vbc - Created.
*> 04/12/25 vbc - Some fields chgd to 9 from x etc & get rid of tabs.
*>
 01  PY-Comp-Hist-Record.
  *>   03  RRN                      pic 9.              *> Possibly needs to use Apply-No
     03  Coh-Interval                 pic x.
     03  Coh-Starting-Up              pic x.              *> on 1st starting set to Y, after 1st apply set to N but is this CORRECT ?
*>                                                           Should the tests relate to specific Emp His / Emp records ?
*>
     03  Coh-Last-Apply-No            pic 9(4) comp.           *> Possibly the KEY and not RRN then can be removed if multiple records??
     03  Coh-QTD                                  comp-3.
         05  Coh-QTD-Income-Taxable   pic 9(7)v99.
         05  Coh-QTD-Other-Taxable    pic 9(7)v99.
         05  Coh-QTD-Other-NonTaxable pic 9(7)v99.
         05  Coh-QTD-Fica-Taxable     pic 9(7)v99.
         05  Coh-QTD-Tips             pic 9(7)v99.
         05  Coh-QTD-Net              pic 9(7)v99.
         05  Coh-QTD-Eic-Credit       pic 9(7)v99.
         05  Coh-QTD-Fwt-Liab         pic 9(7)v99.
         05  Coh-QTD-Swt-Liab         pic 9(7)v99.
         05  Coh-QTD-Lwt-Liab         pic 9(7)v99.
         05  Coh-QTD-Fica-Liab        pic 9(7)v99.
         05  Coh-QTD-Sdi-Liab         pic 9(7)v99.
         05  Coh-QTD-Co-Futa-Liab     pic 9(7)v99.
         05  Coh-QTD-Co-Fica-Liab     pic 9(7)v99.
         05  Coh-QTD-Co-Sui-Liab      pic 9(7)v99.
         05  Coh-QTD-Sys              pic 9(7)v99   occurs 5.
         05  Coh-QTD-Emp              pic 9(7)v99   occurs 3.
         05  Coh-QTD-Other-Ded        pic 9(7)v99.
         05  Coh-QTD-Units            pic 9(7)v99   occurs 4.
         05  Coh-QTD-Comp-Time-Earned pic 9(7)v99.
         05  Coh-QTD-Comp-Time-Taken  pic 9(7)v99.
         05  Coh-QTD-Vac-Earned       pic 9(7)v99.
         05  Coh-QTD-Vac-Taken        pic 9(7)v99.
         05  Coh-QTD-Sl-Earned        pic 9(7)v99.
         05  Coh-QTD-Sl-Taken         pic 9(7)v99.
     03  Coh-QTD                                  comp-3.
         05  Coh-YTD-Income-Taxable   pic 9(7)v99.
         05  Coh-YTD-Other-Taxable    pic 9(7)v99.
         05  Coh-YTD-Other-NonTaxable pic 9(7)v99.
         05  Coh-YTD-Fica-Taxable     pic 9(7)v99.
         05  Coh-YTD-Tips             pic 9(7)v99.
         05  Coh-YTD-Net              pic 9(7)v99.
         05  Coh-YTD-Eic-Credit       pic 9(7)v99.
         05  Coh-YTD-Fwt-Liab         pic 9(7)v99.
         05  Coh-YTD-Swt-Liab         pic 9(7)v99.
         05  Coh-YTD-Lwt-Liab         pic 9(7)v99.
         05  Coh-YTD-Fica-Liab        pic 9(7)v99.
         05  Coh-YTD-Sdi-Liab         pic 9(7)v99.
         05  Coh-YTD-Co-Futa-Liab     pic 9(7)v99.
         05  Coh-YTD-Co-Fica-Liab     pic 9(7)v99.
         05  Coh-YTD-Co-Sui-Liab      pic 9(7)v99.
         05  Coh-YTD-Sys              pic 9(7)v99   occurs 5.
         05  Coh-YTD-Emp              pic 9(7)v99   occurs 3.
         05  Coh-YTD-Other-Ded        pic 9(7)v99.
         05  Coh-YTD-Units            pic 9(7)v99   occurs 4.
         05  Coh-YTD-Comp-Time-Earned pic 9(7)v99.
         05  Coh-YTD-Comp-Time-Taken  pic 9(7)v99.
         05  Coh-YTD-Vac-Earned       pic 9(7)v99.
         05  Coh-YTD-Vac-Taken        pic 9(7)v99.
         05  Coh-YTD-Sl-Earned        pic 9(7)v99.
         05  Coh-YTD-Sl-Taken         pic 9(7)v99.
     03  Coh-Date                     pic 9(8)     comp    occurs 12.   *>  ccyymmdd
     03  Coh-Tax                      pic 9(7)v99  comp-3  occurs 12.
     03  Coh-Q-Taxes.
         05  Coh-Q-Tax                pic 9(7)v99  comp-3  occurs 4.
         05  Coh-Q-Fica-Tax           pic 9(7)v99  comp-3  occurs 4.
         05  Coh-Q-Co-Futa-Liab       pic 9(7)v99  comp-3  occurs 4.
     03  Coh-All-Q-Taxes redefines Coh-Q-Taxes.    *> Used in py930 for data I/P and ???
         05  Coh-All-Q-Tax            pic 9(7)v99  comp-3  occurs 12.
*>
*>
*>
*> copy "fdpycalx.cob".
*>
*> next 3 are all the same so can use only one stax
*>
*> copy "fdpystax.cob".
*> copy "fdpyswt.cob".
*> copy "fdpylwt.cob".
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(15) value "PY010 (1.0.02)".  *> First release pre testing.
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
*>C  copy "wsmaps09.cob".     *> customer-in for chk digit calc
*>*********
*> maps09 *
*>*********
*>
 01  maps09-ws.
     03  customer-code.
         05  customer-nos   pic x(6).
         05  check-digit    pic 9.
     03  maps09-reply       pic x.
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
*>C  copy "Test-Data-Flags.cob".  *> set sw-Testing to zero to stop logging.
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
*>
 01  WS-Data.
     03  Menu-Reply          pic x.
     03  WS-Saved-Menu-Reply pic x        value zero.  *> If options 4 or 5 selected & Menu-Reply copied to it.  NOT USED YET
     03  PY-PR1-Status       pic xx       value zero.
     03  PY-Act-Status       pic xx       value zero.
 *>    03  PY-Ded-Status       pic xx       value zero.  *> NOT Used ?
 *>    03  PY-Hrs-Status       pic xx       value zero.  *> NOT Used
     03  PY-Emp-Status       pic xx       value zero.
     03  PY-His-Emp-Status   pic xx       value zero.
     03  PY-Coh-Status       pic xx       value zero.
 *>    03  PY-Stax-Status      pic xx       value zero.    *> NOT Used
 *>    03  PY-Calx-Status      pic xx       value zero.  *> NOT Used
*>
     03  WS-Reply            pic x.
     03  WS-Eval-Msg         pic x(25)    value spaces.
     03  WS-Err-Msg          pic x(40)    value spaces.  *> Make large enough for longest SY msg
     03  WS-Env-Columns      pic 999      value zero.
     03  WS-Env-Lines        pic 999      value zero.
     03  WS-22-Lines         pic 99.
     03  WS-23-Lines         pic 99.
     03  WS-Lines            pic 99.
     03  A                   pic 99       value zero.
     03  B                   pic 99       value zero.
     03  C                   pic 999      value zero.   *> For search of states
     03  WS-Employee-In.
         05  WS-Employee-No  pic 9(6)     value zero.  *> excl chk digit
         05  WS-Emp-Chk-Dig  pic x.
     03  WS-Employee-Number  redefines WS-Employee-In
                             pic 9(7).
     03  WS-Saved-Emp-No     pic 9(7).
     03  WS-Recalculate      pic x         value "N".
*>
     03  WS-Starting-Up      pic x         value "N".  *> Set for a new Employee Entry so History can be added ONLY.
*>
     03  WS-Emp-Date         pic 99/99/9999.     *> Common date for accepting or display
 *>    03  WS-Emp-Birth-Date   pic 99/99/9999  value zero.
 *>    03  WS-Emp-Start-Date   pic 99/99/9999  value zero.
 *>    03  WS-Emp-Term-Date    pic 99/99/9999  value zero.
 *>    03  WS-Temp-Date.          *> can be mm/dd for usa or dd/mm. to/from WS-Date o/p filing ccyymmdd
 *>        05  WS-Temp-1st     pic 99.
 *>        05  filler          pic x.
 *>        05  WS-Temp-2nd     pic 99.
 *>        05  filler          pic x.
 *>        05  WS-Temp-Year    pic 9999.
     03  WS-Temp-SSN.
         05  WS-Temp-SSN-1st pic 999.
         05  filler          pic x     value "-".
         05  WS-Temp-SSN-2nd pic 99.
         05  filler          pic x     value "-".
         05  WS-Temp-SSN-3rd pic 9(4).
     03  WS-Temp-SSN-Orig redefines WS-Temp-SSN
                             pic 999/99/9999.
     03  WS-Temp-Name-1      pic x(28).   *> But all must be =< 32 chars
     03  WS-Temp-Name-2      pic x(28).
     03  WS-Temp-Name-3      pic x(28).
*>
     03  WS-Heading          pic x(40)    value "Payroll". *> for zz020-Headings
*>
*> The following for GC and screen with *nix NOT tested with Windows
*>  Only for F1 key and list of employees - MAY BE
*>
 01  wScreenName             pic x(256).
 01  wInt                    binary-long.
*>
*>  Temp vars used with ACCEPT_NUMERIC C routine    -- NEEDED HERE  --  NOT YET USED
*>
 01  WS-Temp-Numbers.
     03  WS-Temp-Amount      pic 9(7).99.
 *>    03  WS-Temp-Rate        pic 99.99.
     03  WS-Temp-Pcent-E     pic 999.99.
     03  WS-Temp-Pcent       pic 999v99.
 *>    03  WS-Temp-Percent     pic 99.99.  *>  NOT YET USED
 *>    03  WS-Temp-Limit       pic 99999.99.
 *>    03  WS-Temp-Factor      pic 99999.99.
 *>    03  WS-Temp-Act-No      pic 99.
 *>    03  WS-Temp-Used        pic x.
*>
*> preset at start of SS-Employee-Data-2 & accumulated
*>
 01  WS-PCent-Total          pic 999v99  value zero.
*>
*>  used in ca000
*>
 01  WS-Dflt-Chk-Cat         pic 99.
 01  WS-Dflt-Acct            pic 99.
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
*> Tables have data stored by Act-No so only can handle act-no > 0 and < 100
*>
 01  WS-Account-Table.
     03  WS-Act-Entries              occurs 99.
         05  WS-Act-GL-No        pic 9(6).
*>
*> Next one MUST be same size as the WS-Act-Entries occurs value.
 01  WS-Account-Table-Size   pic 99  value 99.
 01  WS-Account-Count        pic 99  value zero.  *> Table Entries in use NOT Really used
*>
 01  WS-State-Codes-Table.  *> Un Sorted
     03  WS-S                pic x(100) value "ALAKAZARCACOCTDEFLGA" &
                                              "HIIDILINIAKSKYLAMEMD" &
                                              "MAMIMNMSMOMTNENVNHNJ" &
                                              "NMNYNCNDOHOKORPARISC" &
                                              "SDTNTXUTVTVAWAWVWIWY".
     03  WS-States redefines WS-S    occurs 50
                                     Ascending key WS-Codes INDEXED BY QQ.
         05  WS-Codes        pic xx.
*>
 01  WS-Interval-Used        pic 99  occurs 4 values 52 26 24 12. *> from RATENT --  NOT YET USED
*>
 01  WS-Rates-Literals.  *> NOT NEEDED / NOT YET USED ? as in PY-PR1-Rate-Name (n) n= 1 - 4
     03  WS-Rates.
         05  filler          pic x(15)  value spaces.
         05  filler          pic x(15)  value spaces.
         05  filler          pic x(15)  value spaces.
         05  filler          pic x(15)  value spaces.
     03  WS-Rate-Lit redefines WS-Rates
                             pic x(15)  occurs 4.
*>
 01  Error-Messages.
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY002           pic x(31) value "SY002 Note error and hit Return".
     03  SY003           pic x(51) value "SY003 Aborting function - Note error and hit Return".
*>     03  SY004           pic x(20) value "SY004 Now Hit Return".
*>     03  SY005           pic x(18) value "SY005 Invalid Date".
*>     03  SY008           pic x(32) value "SY008 Note message & Hit Return ".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
*>     03  SY011           pic x(47) value "SY011 Error on systemMT processing, FS-Reply = ".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*>     03  SY014           pic x(30) value "SY014 Press return to continue".
*>
*> Module General ?
*>
     03  PY001           pic x(36) value "PY001 Re/Write PARAM record Error = ".
     03  PY002           pic x(32) value "PY002 Read PARAM record Error = ".

     03  PY013           pic x(43) value "PY013 Error Reading Company History File - ".

     03  PY015           pic x(52) value "PY015 History update Can not run after apply has run".  *> was PY929 (basic)
*>
*> Module specific
*>
*>  REMOVE UN-USED below and above.
*>
     03  PY105           pic x(31) value "PY105 Bad value for Date Format".
     03  PY108           pic x(38) value "PY108 Bad Exclusion code - Range 1 - 4".
     03  PY109           pic x(38) value "PY109 Bad Pay Interval - not = S,M,B,W".
     03  PY110           pic x(27) value "PY110 Pay Type not = H or S".
     03  PY115           pic x(52) value "PY115 E/D Must be D or E : E = Earning D = Deduction".
*>     03  PY117           pic x(28) value "PY117 Account does not exist".
*>     03  PY118           pic x(38) value "PY118 Account re/write failed - Status".
     03  PY119           pic x(20) value "PY119 Must be Y or N".
     03  PY120           pic x(44) value "PY120 Cannot open Accounts File, aborting : ".
     03  PY121           pic x(79) value "PY121 A/P must be A or P : A = flat Amount. P = Percentage of Gross Taxable pay".
*>     03  PY122           pic x(59) value "PY122 Chk Cat Must be 2-7 for Earnings, 9-16 for Deductions".  *> old PY360
*>     03  PY123           pic x(55) value "PY123 FWT Cutoffs & Percents Must be in Ascending order".      *> old PY356
     03  PY124           pic x(45) value "PY124 Account does not exist in Account Table".
     03  PY125           pic x(22) value "PY125 Accounts No > 99".
     03  PY126           pic x(51) value "PY126 Bad value in Account no field - Accounts file".
     03  PY127           pic x(44) value "PY127 Creating Check digit FAILED - Aborting".
*>     03  PY128           pic x(36) value "PY128 Error reading Employee file - ".
     03  PY129           pic x(29) value "PY129 State is invalid, Retry".
*>     03  PY130           pic x(37) value "PY130 Error creating Employee file - ".
     03  PY131           pic x(39) value "PY131 Error writing to Employee file - ".
     03  PY132           pic x(37) value "PY132 Error Reading History record - ".
     03  PY133           pic x(38) value "PY133 Error writing to History file - ".
     03  PY135           pic x(41) value "PY135 Error rewriting to Employee file - ".
     03  PY136           pic x(33) value "PY136 Error - Rate is over 100.00".
     03  PY137           pic x(36) value "PY137 Error - Rate Total is over 100".
     03  PY138           pic x(66) value "PY138 Check categories can be  2-7 (Earnings) or 9-16 (Deductions)".
     03  PY139           pic x(54) value "PY139 Payroll parameter File does not exist - Aborting".
     03  PY140           pic x(41) value "PY140 Run main menu option Y to create it".
     03  PY141           pic x(57) value "PY141 You can ONY create/update History if a NEW Employee".
*>
*> The CBASIC MESSAGES
*>
     03  PY173           pic x(40) value "PY173 That's not a valid employee number".
     03  PY174           pic x(63) value "PY174 Social security numbers must be of the format 000-00-0000".
     03  PY175           pic x(49) value "PY175 The only thing I know about sex is M  or  F".
     03  PY176           pic x(67) value "PY176 Employee status can be A(active), L(on leave) & T(terminated)".
     03  PY180           pic x(38) value "PY180 That's an unused employee number".
*>
*> from RATENT  NOT YET USED HERE
*>
*>     03  PY221           pic x(55) value "PY221 H and S  are the only valid entries at this field".
*>     03  PY222           pic x(56) value "PY222 That's not one of the pay intervals currently used".
     03  PY223           pic x(55) value "PY223 M and S  are the only valid entries at this field".
 *>    03  PY226           pic x(63) value "PY226 There are four tax exclusion types numbered one thru four". *> SEE 108
     03  PY229           pic x(66) value "PY229 This employee has been exempted from Federal Tax Withholding".
     03  PY230           pic x(64) value "PY230 This employee has been exempted from State Tax Withholding".
     03  PY231           pic x(64) value "PY231 This employee has been exempted from Local Tax Withholding".
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
*>C      copy "an-accept.ws".  *> Support WS for ACCEPT_NUMERIC routine
       *>1>>LISTING OFF
      *>
      *> copy book - an-accept.ws compatible for FREE and VARIABLE formats
      *>
       01  AN-ACCEPT-NUMERIC USAGE BINARY-SHORT.
           03  AN-LINE.
           03  AN-COLUMN.
           03  AN-MODE.
               88  AN-MODE-IS-NO-UPDATE          VALUE 0.
               88  AN-MODE-IS-UPDATE             VALUE 1.
           03  AN-FG.
               88  AN-FG-IS-BLACK                VALUE 0.
               88  AN-FG-IS-BLUE                 VALUE 1.
               88  AN-FG-IS-GREEN                VALUE 2.
               88  AN-FG-IS-CYAN                 VALUE 3.
               88  AN-FG-IS-RED                  VALUE 4.
               88  AN-FG-IS-MAGENTA              VALUE 5.
               88  AN-FG-IS-YELLOW               VALUE 6.
               88  AN-FG-IS-WHITE                VALUE 7.
           03  AN-BG.
               88  AN-BG-IS-BLACK                VALUE 0.
               88  AN-BG-IS-BLUE                 VALUE 1.
               88  AN-BG-IS-GREEN                VALUE 2.
               88  AN-BG-IS-CYAN                 VALUE 3.
               88  AN-BG-IS-RED                  VALUE 4.
               88  AN-BG-IS-MAGENTA              VALUE 5.
               88  AN-BG-IS-YELLOW               VALUE 6.
               88  AN-BG-IS-WHITE                VALUE 7.
           03  AN-FG2.
               88  AN-FG2-IS-BLACK               VALUE 0.
               88  AN-FG2-IS-BLUE                VALUE 1.
               88  AN-FG2-IS-GREEN               VALUE 2.
               88  AN-FG2-IS-CYAN                VALUE 3.
               88  AN-FG2-IS-RED                 VALUE 4.
               88  AN-FG2-IS-MAGENTA             VALUE 5.
               88  AN-FG2-IS-YELLOW              VALUE 6.
               88  AN-FG2-IS-WHITE               VALUE 7.
           03  AN-RETURN-CODE.
               88  AN-RETURN-CODE-VIA-ENTER      VALUE 0.
               88  AN-RETURN-CODE-VIA-PFKEY-01   VALUE 01. *> 1001
               88  AN-RETURN-CODE-VIA-PFKEY-02   VALUE 02.
               88  AN-RETURN-CODE-VIA-PFKEY-03   VALUE 03.
               88  AN-RETURN-CODE-VIA-PFKEY-04   VALUE 04.
               88  AN-RETURN-CODE-VIA-PFKEY-05   VALUE 05.
               88  AN-RETURN-CODE-VIA-PFKEY-06   VALUE 06.
               88  AN-RETURN-CODE-VIA-PFKEY-07   VALUE 07.
               88  AN-RETURN-CODE-VIA-PFKEY-08   VALUE 08.
               88  AN-RETURN-CODE-VIA-PFKEY-09   VALUE 09.
               88  AN-RETURN-CODE-VIA-PFKEY-10   VALUE 10.
               88  AN-RETURN-CODE-VIA-PFKEY-11   VALUE 11.
               88  AN-RETURN-CODE-VIA-PFKEY-12   VALUE 12.
               88  AN-RETURN-CODE-VIA-PFKEY-13   VALUE 13.
               88  AN-RETURN-CODE-VIA-PFKEY-14   VALUE 14.
               88  AN-RETURN-CODE-VIA-PFKEY-15   VALUE 15.
               88  AN-RETURN-CODE-VIA-PFKEY-16   VALUE 16.
               88  AN-RETURN-CODE-VIA-PFKEY-17   VALUE 17.
               88  AN-RETURN-CODE-VIA-PFKEY-18   VALUE 18.
               88  AN-RETURN-CODE-VIA-PFKEY-19   VALUE 19.
               88  AN-RETURN-CODE-VIA-PFKEY-20   VALUE 20.
               88  AN-RETURN-CODE-VIA-PFKEY-21   VALUE 21.
               88  AN-RETURN-CODE-VIA-PFKEY-22   VALUE 22.
               88  AN-RETURN-CODE-VIA-PFKEY-23   VALUE 23.
               88  AN-RETURN-CODE-VIA-PFKEY-24   VALUE 24.
               88  AN-RETURN-CODE-VIA-PFKEY-25   VALUE 25.
               88  AN-RETURN-CODE-VIA-PFKEY-26   VALUE 26.
               88  AN-RETURN-CODE-VIA-PFKEY-27   VALUE 27.
               88  AN-RETURN-CODE-VIA-PFKEY-28   VALUE 28.
               88  AN-RETURN-CODE-VIA-PFKEY-29   VALUE 29.
               88  AN-RETURN-CODE-VIA-PFKEY-30   VALUE 30.
               88  AN-RETURN-CODE-VIA-PFKEY-31   VALUE 31.
               88  AN-RETURN-CODE-VIA-PFKEY-32   VALUE 32.
               88  AN-RETURN-CODE-VIA-PFKEY-33   VALUE 33.
               88  AN-RETURN-CODE-VIA-PFKEY-34   VALUE 34.
               88  AN-RETURN-CODE-VIA-PFKEY-35   VALUE 35.
               88  AN-RETURN-CODE-VIA-PFKEY-36   VALUE 36.
               88  AN-RETURN-CODE-VIA-PFKEY-37   VALUE 37.
               88  AN-RETURN-CODE-VIA-PFKEY-38   VALUE 38.
               88  AN-RETURN-CODE-VIA-PFKEY-39   VALUE 39.
               88  AN-RETURN-CODE-VIA-PFKEY-40   VALUE 40.
               88  AN-RETURN-CODE-VIA-PFKEY-41   VALUE 41.
               88  AN-RETURN-CODE-VIA-PFKEY-42   VALUE 42.
               88  AN-RETURN-CODE-VIA-PFKEY-43   VALUE 43.
               88  AN-RETURN-CODE-VIA-PFKEY-44   VALUE 44.
               88  AN-RETURN-CODE-VIA-PFKEY-45   VALUE 45.
               88  AN-RETURN-CODE-VIA-PFKEY-46   VALUE 46.
               88  AN-RETURN-CODE-VIA-PFKEY-47   VALUE 47.
               88  AN-RETURN-CODE-VIA-PFKEY-48   VALUE 48. *> 1048
               88  AN-RETURN-CODE-VIA-PG-UP      VALUE 49. *> 2001
               88  AN-RETURN-CODE-VIA-PG-DOWN    VALUE 50. *> 2002
               88  AN-RETURN-CODE-VIA-TAB        VALUE 51. *> 2007
               88  AN-RETURN-CODE-VIA-BACK-TAB   VALUE 52. *> 2008
               88  AN-RETURN-CODE-VIA-ESCAPE     VALUE 99. *> 2005
           03  AN-ERROR-CODE.
               88  AN-ERROR-OK                   VALUE 0.
               88  AN-ERROR-NOT-EXTENDED-DISPLAY VALUE 4.
               88  AN-ERROR-S-ROW-OUT-OF-SCREEN  VALUE 8.
               88  AN-ERROR-S-COL-OUT-OF-SCREEN  VALUE 12.
               88  AN-ERROR-E-COL-OUT-OF-SCREEN  VALUE 16.
      *>
       *>>>LISTING ON
*>
*>  might be needed
*>
*> copy "wsfnctn.cob".
*> copy "wsmaps03.cob".    *> for maps04
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
*>
 01  To-Day              pic x(10).
*>
 screen section.
*>
 01  Display-Heads                background-color cob-color-black         *> NOT YET USED
                                  foreground-color 3
                                  erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2.
     03  value "Payroll Employee Data Entry (1/3)"    col 24.
     03  from  U-Date     pic x(10)          col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
*>
*>   Menu screen for Employee data entry
*>
 01  SS-Employee-Data-Menu    background-color cob-color-black
                              foreground-color cob-color-green
                              erase eos.
     03  from  Prog-Name  pic x(15)       line  1 col  1 foreground-color 2.
     03  value "Employee Data Emtry Menu"         col 29.
     03  from  U-Date     pic x(10)               col 71 foreground-color 2.
     03  from  Usera      pic x(32)       line  3 col  1.
     03  value "1. Employee Data Entry"   line  5 col 21 erase eos.
     03  value "2. Employee Earn/Ded and Cost Entry"
                                          line  6 col 21.
     03  value "3. Employee Rate Entry"   line  7 col 21.
     03  value "4. Employee History Entry" line 8 col 21.
     03  value "5. Data & Earn/Ded/Cost - Entry (options 1, 2 & 3)"
                                          line  9 col 21.
     03  value "6. All Data - Entry (options 1,2, 3 & 4)"
                                          line 10 col 21.
     03  value "X or Esc to quit menu option"
                                          line 11 col 21.
     03  value "Select Option  [ ]"       line 13 col 30.
     03  using Menu-Reply    pic x                col 46 foreground-color 3 auto.
*>
*> Employee data entry screens  AN is used so these are displayed only
*>
 01  SS-Employee-Data-1    background-color cob-color-black
                           foreground-color cob-color-green
                           erase eos.
     03  from  Prog-Name  pic x(15)                   line  1 col  1 foreground-color 2.
     03  value "Payroll Employee Data Entry (1/3)"            col 24.
     03  from  U-Date     pic x(10)                           col 71 foreground-color 2.
     03  from  Usera      pic x(32)                   line  3 col  1.
*>
*> Preset the WS-Emp fields firsr before accept-ing
*>
     03  value "   Employee Number [       |"                                                   line  5 col  1.
     03  value "      |   Employee           +----------------------------------------------+"  line  6 col  1.
     03  value "      |                   2  [                                ]             |"  line  9 col  1.
     03  value "      |                   3  [                                ]             |"  line 10 col  1.
     03  value "      |           City or 4  [                                ]             |"  line 11 col  1.
     03  value "      |                      State [  ]             Zip [     ]             |"  line 12 col  1.
     03  value "      |           Phone  [            ]                                     |"  line 13 col  1.
     03  value "      +---------------------------------------------------------------------+"  line 14 col  1.
     03  value "      Soc Sec No.   [            ]                |    Pension (Y/N)      [ ]"  line 15 col  1.
     03  value "      Birth Date    [          ]                  |    Taxing State      [  ]"  line 17 col  1.
     03  value "      Sex           [ ]                           |"                            line 18 col  1.
     03  value "      -----------------------------------------------------------------------"  line 19 col  1.
     03  value "      Start Date [          ]    |                Employment Status       [ ]"  line 20 col  1.
     03  value "      Term. Date [          ]    |       (A=Active, L=On Leave, T=Terminated)"  line 21 col  1.
*>
     03  value " F1 or Emp # All zeroes to enter new Employee "                                 line 23 col  1.
     03  value "  Escape to Quit"                                                               line 24 col  1.
     03  using Emp-Name         pic x(32)       line  7 col 21  foreground-color 3.
     03  using Emp-Address-1    pic x(32)       line  8 col 31  foreground-color 3.
     03  using Emp-Address-2    pic x(32)       line  9 col 31  foreground-color 3.
*>      03  using Emp-Address-3    pic x(32)       line 10 col 31  foreground-color 3.
     03  using Emp-Address-4    pic x(32)       line 11 col 31  foreground-color 3.
     03  using Emp-State        pic xx          line 12 col 37  foreground-color 3.
     03  using Emp-Zip          pic x(5)        line 12 col 58  foreground-color 3.
     03  using Emp-Phone-No     pic 9(13)       line 13 col 27  foreground-color 3.
     03  using Emp-SSN          pic x(12)       line 15 col 22  foreground-color 3.
     03  using Emp-Pension-Used pic x           line 15 col 76  foreground-color 3.
     03  using Emp-Bank-Acct-No pic x(25)       line 16 col 22  foreground-color 3.
     03  using Emp-Job-Code     pic xxx         line 16 col 74  foreground-color 3.
     03  using WS-Emp-Date      pic 99/99/9999  line 17 col 22  foreground-color 3.   *> NEEDS CONVERSION
     03  using Emp-Taxing-State pic xx          line 17 col 75  foreground-color 3.
     03  using Emp-Sex          pic x           line 18 col 22  foreground-color 3.
     03  using WS-Emp-Date      pic 99/99/9999  line 20 col 19  foreground-color 3.   *> NEEDS CONVERSION
     03  using Emp-Status       pic x           line 20 col 76  foreground-color 3.
 *>    03  using WS-Emp-Date      pic 99/99/9999  line 21 col 19  foreground-color 3.   *> NEEDS CONVERSION but zero.
*>
*> Employee Earn/Ded & Cost data entry screens  AN is used so these are displayed only
*>
 01  SS-Employee-Data-2    background-color cob-color-black
                           foreground-color cob-color-green
                           erase eos.
     03  from  Prog-Name  pic x(15)                            line  1 col  1 foreground-color 2.
     03  value "Payroll Employee Data Entry (2/3)"                     col 24.
     03  from  U-Date     pic x(10)                                    col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
*>
     03  value "Employee Earn/Ded and Cost"                                                      line  3 col 35.
     03  value " Empl No. [       ] Name {                                } SSN {           }"   line  5 col  1.
     03  value "  ---------------------------------------------------------------------------"   line  6 col  1.
     03  value "  ----- Cost Distribution ------      |    -------- Exemptions From --------"    line  7 col  1.
     03  value "        of Employee Gross             |              Tax Witholding"             line  8 col  1.
     03  value "        and Employer Cost             |  FICA Exempt [ ]  Federal Exempt [ ]"    line  9 col  1.
     03  value "  Account [  ]  Percent  [      ]     |  FUTA Exempt [ ]  State   Exempt [ ]"    line 10 col  1.
     03  value "  Account [  ]  Percent  [      ]     |  SUI  Exempt [ ]  Local   Exempt [ ]"    line 11 col  1.
     03  value "  Account [  ]  Percent  [      ]     |  SDI  Exempt [ ]"                        line 12 col  1.
     03  value "  Account [  ]  Percent  [      ]     |  ------------------------------------"   line 13 col  1.
     03  value "  Account [  ]  Percent  [      ]     |   Exemptions from System Deductions"     line 14 col  1.
     03  value "                Total    {nnn.nn}     |   1:[ ]  2:[ ]  3:[ ]  4:[ ]  5:[ ]"     line 15 col  1.
     03  value "  ---------------------------------------------------------------------------"   line 16 col  1.
     03  value "  ---------------  Employee  Specific  Deductions / Earnings   --------------"   line 17 col  1.
     03  value "   Used  Earn/Ded Desc   E/D Acct. A/P    Factor   Limited   Limit   Xcld Cat"   line 18 col  1.
     03  value "  1:[ ][               ] [ ] [  ]  [ ]  [999999.99]  [ ]   [999999.99][ ][  ]"   line 19 col  1. *> Xcld - 1 - 4
     03  value "  2:[ ][               ] [ ] [  ]  [ ]  [         ]  [ ]   [         ][ ][  ]"   line 20 col  1.
     03  value "  3:[ ][               ] [ ] [  ]  [ ]  [         ]  [ ]   [         ][ ][  ]"   line 21 col  1.
*>
*> Employee Rate Data entry screens  AN is used so these are displayed only
*>
 01  SS-Employee-Data-3    background-color cob-color-black
                           foreground-color cob-color-green
                           erase eos.
     03  from  Prog-Name  pic x(15)                                 line  1 col  1 foreground-color 2.
     03  value "Payroll Employee Data Entry (3/3)"                          col 24.
     03  from  U-Date     pic x(10)                                         col 71 foreground-color 2.
     03  from  Usera      pic x(32)                                 line  3 col  1.
*>
     03  value "Employee Rate Entry "                                                           line  3 col  35.
     03  value " Empl No. [       ] Name {                                } SSN {           }"  line  5 col  1.
     03  value "-----------------------------------+----------------------------------------"   line  6 col  1.
     03  value "   Pay Interval  And  Pay Rates    |           Tax  Witholding  "               line  7 col  1.
     03  value "Pay Type (H=Hourly,S=Salaried) [ ] |              Allowances  "                 line  8 col  1.
     03  value "Pay Interval (S=Semi-Monthly,  [ ] |  Marital Status(M=Married,S=Single)[ ]"    line  9 col  1.
     03  value "(M=Monthly, W=Weekly, B=Biweekly)  |          Federal  WH  Allowances  [  ]"    line 10 col  1.
     03  value "rate1 Desc.Name   Rate  [99999.99] |          State    WH  Allowances  [  ]"    line 11 col  1. *> Reg Pay Rate
     03  value "rate2 Desc.Name   Rate  [        ] |          Local    WH  Allowances  [  ]"    line 12 col  1. *> O-Time Pay Rate
     03  value "rate3 Desc.Name   Rate  [        ] |  Earned Income Credit Used (Y or N)[ ]"    line 13 col  1. *> Spec-O-Time Rate
     03  value "rate4 Desc.Name   Rate  [        ] |           State  of  California"           line 14 col  1. *> Comm Rate
     03  value "Rate 4 Tax Exclusion Type(1-4) [ ] |           Special   Information"           line 15 col  1.
     03  value "Normal Units            [        ] |  Special  Witholding Allowances   [  ]"    line 17 col  1.
     03  value "Maximum Pay            [         ] |--------------------------------------+"    line 18 col  1.
     03  value "     (Vac. And S.L.  Rates are units earned per pay Interval)"                  line 19 col  1.
     03  value "    Vacation   Rate     [        ] Accumulated  [99999.99] Used  [99999.99]"    line 20 col  1.
     03  value "    Sick Leave Rate     [        ] Accumulated  [        ] Used  [        ]"    line 21 col  1.
     03  value "    Compensatory Time              Accumulated  [        ] Used  [        ]"    line 22 col  1.
*>
*> removed from py930 as that updates Company History
*>
 01  SS-Employee-History-Data-1  background-color cob-color-black
                                 foreground-color cob-color-green
                                 erase eos.
     03  from  Prog-Name  pic x(15)                                      line  1 col  1 foreground-color 2.
     03  value "Employee History Maintenance"                                    col 29.
     03  from  U-Date     pic x(10)                                              col 71 foreground-color 2.
     03  from  Usera      pic x(32)                                      line  3 col  1.
     03  value "Update Employee History"                                 line  3 col 35.
*>     03  value "Emp No:[       ]"                                        line  6 col  1.
     03  value " Empl No. [       ] Name {                                } SSN {           }"   line  5 col 1.
     03  value "                         QTD Earnings By Tax Catagories"                         line  7 col 1.
     03  value "Income:[          ]  Other:[          ] No Taxes:[          ] Fica:[          ]" line  8 col 1.
     03  value "                Eic Credit:[          ]     Tips:[          ]  Net:[          ]" line  9 col 1.
     03  value "QTD Taxes Withheld:    Fwt:[          ]      Swt:[          ]  Lwt:[          ]" line 10 col 1.
     03  value "                      Fica:[          ]      Sdi:[          ]"                   line 11 col 1.
     03  value "                            QTD Earnings And Deductions"                         line 12 col 1.
     03  value "Sys: 1:[          ] 2:[          ] 3:[          ] 4:[          ] 5:[          ]" line 13 col 1.
     03  value "Emp: 1:[          ] 2:[          ] 3:[          ] Other Deductions:[          ]" line 14 col 1.
     03  value "Units By Pay Type:  1:[          ] 2:[          ] 3:[          ] 4:[          ]" line 15 col 1.
     03  value "                         YTD Earnings By Tax Catagories"                         line 16 col 1.
     03  value "Income:[          ]  Other:[          ] No Taxes:[          ] Fica:[          ]" line 17 col 1.
     03  value "                Eic Credit:[          ]     Tips:[          ]  Net:[          ]" line 18 col 1.
     03  value "YTD Taxes Withheld:    Fwt:[          ]      Swt:[          ]  Lwt:[          ]" line 19 col 1.
     03  value "                      Fica:[          ]      Sdi:[          ]"                   line 20 col 1.
     03  value "                            YTD Earnings and Deductions"                         line 21 col 1.
     03  value "Sys: 1:[          ] 2:[          ] 3:[          ] 4:[          ] 5:[          ]" line 22 col 1.
     03  value "Emp: 1:[          ] 2:[          ] 3:[          ] Other Deductions:[          ]" line 23 col 1.
     03  value "Units by Pay Type:  1:[          ] 2:[          ] 3:[          ] 4:[          ]" line 24 col 1.
*>
*> Here, so I record the line and column # for accepts and accept_numeric routine but
*>  will produce content in the SS display even if only zeros priot to all such verbs
*>
     03  from His-QTD-Income-Taxable    pic 9(7).99                          line  8 col 9.  *> all these for inital display
     03  from His-QTD-Other-Taxable     pic 9(7).99                          line  8 col 29. *> as all manually entered via
     03  from His-QTD-Other-NonTaxable  pic 9(7).99                          line  8 col 51. *>  accept_numeric routine
     03  from His-QTD-Fica-Taxable      pic 9(7).99                          line  8 col 69.
*>
     03  from His-QTD-EIC               pic 9(7).99                          line  9 col 29.
     03  from His-QTD-Tips              pic 9(7).99                          line  9 col 51.
     03  from His-QTD-Net               pic 9(7).99                          line  9 col 69.
*>
     03  from His-QTD-FWT               pic 9(7).99                          line 10 col 29.
     03  from His-QTD-SWT               pic 9(7).99                          line 10 col 51.
     03  from His-QTD-LWT               pic 9(7).99                          line 10 col 69.
*>
     03  from His-QTD-FICA              pic 9(7).99                          line 11 col 29.
     03  from His-QTD-SDI               pic 9(7).99                          line 11 col 51.
*>
     03  from His-QTD-Sys (1)           pic 9(7).99                          line 13 col  9.
     03  from His-QTD-Sys (2)           pic 9(7).99                          line 13 col 24.
     03  from His-QTD-Sys (3)           pic 9(7).99                          line 13 col 39.
     03  from His-QTD-Sys (4)           pic 9(7).99                          line 13 col 54.
     03  from His-QTD-Sys (5)           pic 9(7).99                          line 13 col 69.
*>
     03  from His-QTD-Emp (1)           pic 9(7).99                          line 14 col  9.
     03  from His-QTD-Emp (2)           pic 9(7).99                          line 14 col 24.
     03  from His-QTD-Emp (3)           pic 9(7).99                          line 14 col 39.
     03  from His-QTD-Other-Ded         pic 9(7).99                          line 14 col 69.
*>
     03  from His-QTD-Units (1)         pic 9(7).99                          line 15 col 24.
     03  from His-QTD-Units (2)         pic 9(7).99                          line 15 col 39.
     03  from His-QTD-Units (3)         pic 9(7).99                          line 15 col 54.
     03  from His-QTD-Units (4)         pic 9(7).99                          line 15 col 69.
*>
     03  from His-YTD-Income-Taxable    pic 9(7).99                          line 17 col  9.
     03  from His-YTD-Other-Taxable     pic 9(7).99                          line 17 col 29.
     03  from His-YTD-Other-NonTaxable  pic 9(7).99                          line 17 col 51.
     03  from His-YTD-Fica-Taxable      pic 9(7).99                          line 17 col 69.
*>
     03  from His-YTD-EIC               pic 9(7).99                          line 18 col 29.
     03  from His-YTD-Tips              pic 9(7).99                          line 18 col 51.
     03  from His-YTD-Net               pic 9(7).99                          line 18 col 69.
*>
     03  from His-YTD-FWT               pic 9(7).99                          line 19 col 29.
     03  from His-YTD-SWT               pic 9(7).99                          line 19 col 51.
     03  from His-YTD-LWT               pic 9(7).99                          line 19 col 69.
*>
     03  from His-YTD-FICA              pic 9(7).99                          line 20 col 29.
     03  from His-YTD-SDI               pic 9(7).99                          line 20 col 51.
*>
     03  from His-YTD-Sys (1)           pic 9(7).99                          line 22 col  9.
     03  from His-YTD-Sys (2)           pic 9(7).99                          line 22 col 24.
     03  from His-YTD-Sys (3)           pic 9(7).99                          line 22 col 39.
     03  from His-YTD-Sys (4)           pic 9(7).99                          line 22 col 54.
     03  from His-YTD-Sys (5)           pic 9(7).99                          line 22 col 69.
*>
     03  from His-YTD-Emp (1)           pic 9(7).99                          line 23 col  9.
     03  from His-YTD-Emp (2)           pic 9(7).99                          line 23 col 24.
     03  from His-YTD-Emp (3)           pic 9(7).99                          line 23 col 39.
     03  from His-YTD-Other-Ded         pic 9(7).99                          line 23 col 69.
*>
     03  from His-YTD-Units (1)         pic 9(7).99                          line 24 col 24.
     03  from His-YTD-Units (2)         pic 9(7).99                          line 24 col 39.
     03  from His-YTD-Units (3)         pic 9(7).99                          line 24 col 54.
     03  from His-YTD-Units (4)         pic 9(7).99                          line 24 col 69.
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
     move     current-Date to WSE-Date-block.
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
*> Set up error message areas on screen
*>
     subtract 2 from WS-Env-Lines giving WS-22-Lines.
     subtract 1 from WS-Env-Lines giving WS-23-Lines.
     move     WS-Env-Lines to WS-Lines.
*>
*> Pre setup params for acept_numeric routine
*>
     move     zeros to AN-Error-Code
                       AN-Return-Code.
     SET      AN-FG-IS-Green    to TRUE.
     SET      AN-BG-IS-Black    to TRUE.
     SET      AN-FG2-IS-Cyan    to TRUE.
     SET      AN-Mode-IS-Update to TRUE.  *> could be AN-MODE-IS-NO-UPDATE to
*>                                            TRUE on first use.
     move     1 to RRN.
     open     i-o  PY-Param1-File.     *> i-o Will NOT create a file
     if       PY-PR1-Status not = "00"      *> Does not exist yet so back to menu and let user run create
              display  PY139 at line WS-22-Lines col 1 foreground-color 4
              display  PY140 at line WS-23-Lines col 1 foreground-color 4
              display  SY003 at line WS-Lines col 1 foreground-color 2
              accept   Menu-Reply at line WS-Lines col 53
              close    PY-Param1-File
              goback
     else
              set      AN-MODE-IS-UPDATE to true
              move     1 to RRN
              read     PY-Param1-File key RRN
              if       PY-PR1-Status not = "00"
                       perform  ZZ040-Evaluate-Message
                       display  PY002         at line WS-23-Lines col 1 with erase eos
                       display  PY-PR1-Status at line WS-23-Lines col 34
                       display  WS-Eval-Msg   at line WS-23-Lines col 37
                       display  SY001         at line WS-Lines    col 1
                       accept   WS-Reply      at line WS-Lines    col 48 AUTO
                       close    PY-Param1-File
                       goback
              end-if
     end-if.
     move     zero  to  Menu-Reply.
     close    PY-Param1-File.

*>
*> REMEMBER TO REOPEN PARAM FILE as I-O AND CLOSE IT AFTER A REWRITE   <<<<<<<<-------
*>
*>   JUST FOR A REMINDER
*> Tables have data stored by Act-No so only can handle act-no > 0 and < 100
*>
*>  Now, read in all account records storing details in WS-Account-Table
*>  as saves searching the file multiple times for same values.
*>  Will not bother with checking if GL # exist as that Should have been done
*>  already.
*>
 aa010-Read-in-Acts-Data.
     open     input    PY-Accounts-File.
     if       PY-ACT-Status not = "00"
              perform  aa135-Act-File-Open-Error
              go  to   aa998-Hard-Quit-All.
*>
     initialise
              WS-Account-Table.
     move     zeroes to WS-Account-Count.  *> Not used
     perform  forever
              read     PY-Accounts-File Next at end
                       exit perform
              end-read
              if       Act-No   > WS-Account-Table-Size
                       display  PY125 at line WS-22-Lines col 1 foreground-color 4 erase eos
                       display  SY001 at line WS-23-Lines col 1 foreground-color 4
                       accept   Menu-Reply at line WS-23-Lines col 48
                       go to    aa998-Hard-Quit-All         *> close Param & accounts files
              end-if
              if       Act-No < zero
                  or          > WS-Account-Table-Size       *> Otherwise table needs increasing
                       display  PY126 at line WS-22-Lines col 1 foreground-color 4 erase eos
                       display  SY001 at line WS-23-Lines col 1 foreground-color 4
                       accept   Menu-Reply at line WS-23-Lines col 48
                       go to    aa998-Hard-Quit-All
              end-if
              move     Act-GL-No  to  WS-Act-GL-No (Act-No)
              add      1 to WS-Account-Count                *> Might be useful !   NOT USED YET
              exit perform cycle
     end-perform.
*>
*> Now only need to do a simple search of table to confirm acct# exists
*>
     close    PY-Accounts-File.
*>
*> Next create Employee and Emp-History files if not exist yet and leave open as i-o
*>
     open     input PY-Employee-File.
     if       PY-Emp-Status not = zeros
              close  PY-Employee-File
              open   output PY-Employee-File
              close  PY-Employee-File
              open   i-o    PY-Employee-File
     else
              close  PY-Employee-File
              open   i-o    PY-Employee-File.
*>
     open     input  PY-History-File.
     if       PY-His-Emp-Status not = zeros
              close  PY-History-File
              open   output PY-History-File
              close  PY-History-File
              open   i-o    PY-History-File
     else
              close  PY-History-File
              open   i-o    PY-History-File.
*>
*> The Param file is closed now.   <<<<<<<<<<<<<<<
*>
     move     zero to Error-Code.    *> NEEDED / USED ?   <<<<<<<<
*>
*> sort the US states codes in alphabetic order
*>  ready for search all on WS-Codes
*>
     sort     WS-States on ascending key WS-Codes.
*>
 aa020-Menu-Selection.
 *>    display  SS-Employee-Data-Menu.
     accept   SS-Employee-Data-Menu.
     move     UPPER-CASE (Menu-Reply) to Menu-Reply
                                         WS-Saved-Menu-Reply.
     if       Menu-Reply = "X"         *> Quit
        or    Cob-CRT-Status = Cob-Scr-Esc
        or    Error-Code > zero
              move     1 to RRN
              open     i-o PY-Param1-File
              rewrite  PY-Param1-Record             *> recording last Employee #
              perform  aa125-Test-PR1-Status
              if       PY-PR1-Status not = "00"     *> E.g., 23 or 21 may be, key not exists SHOULD NOT HAPPEN
                       write    PY-Param1-Record    *>  as opened and read at start
                       perform  aa125-Test-PR1-Status
              end-if
              close    PY-Param1-File
                       PY-Employee-File
                       PY-History-File
              move     zero to WS-Term-Code
              goback                        *> Quit program, we are done
     end-if.
*>
     evaluate Menu-Reply
              when    = 5
                       perform  ba000-Process-Employee-Basics
                       perform  ca000-Process-Ded-Earn
                       perform  da000-Process-Rates
                       go  to   aa020-Menu-Selection
              when    = 6
                       perform  ba000-Process-Employee-Basics
                       perform  ca000-Process-Ded-Earn
                       perform  da000-Process-Rates
                       perform  ea000-Employee-History     *> only if NO pay run has occured for Employee
                       go  to   aa020-Menu-Selection
              when    = 1
                       perform  ba000-Process-Employee-Basics
                       go  to   aa020-Menu-Selection
              when    = 2
                       perform  ca000-Process-Ded-Earn
                       go  to   aa020-Menu-Selection
              when    = 3
                       perform  da000-Process-Rates
                       go  to   aa020-Menu-Selection
              when    = 4
                       perform  ea000-Employee-History     *> only if NO pay run has occured for Employee
                       go  to   aa020-Menu-Selection
     end-evaluate.
     go to    aa020-Menu-Selection.
*>
*> aa100-Bad-Data-Display.
*>     display  WS-Err-Msg at line WS-23-Lines col 1.
*>     display  SY002      at line WS-Lines    col 1.
*>
 aa125-Test-PR1-Status.
     if       PY-PR1-Status not = "00"   *> WE have a real problem :(
              perform  ZZ040-Evaluate-Message
              display  PY001         at line WS-23-Lines col 1 with erase eos
              display  PY-PR1-Status at line WS-23-Lines col 37
              display  WS-Eval-Msg   at line WS-23-Lines col 40
              display  SY002         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 33 AUTO
     end-if.
*>
*> aa130-Act-File-Error.    *> USED ??
*>     display  PY118 at line WS-23-Lines col 1 erase eos
*>                            foreground-color 4 BEEP.
*>     display  PY-Act-Status at line WS-23-Lines col 40.
*>     move     PY-Act-Status to PY-PR1-Status.
*>     perform  ZZ040-Evaluate-Message.
*>     display  WS-Eval-Msg   at line WS-23-lines col 42.
*>     display  SY003 at line WS-lines col 01 with foreground-color cob-color-red
*>                                                 erase eol BEEP.
*>     accept   WS-Reply at line WS-lines col 52 AUTO.
*>
 aa135-Act-File-Open-Error.    *> USED
     display  PY120 at line WS-23-Lines col 1 erase eos
                            foreground-color 4 BEEP.
     display  PY-Act-Status at line WS-23-Lines col 46.
     move     PY-Act-Status to PY-PR1-Status.
     perform  ZZ040-Evaluate-Message.
     display  WS-Eval-Msg   at line WS-23-lines col 42.
     display  SY003 at line WS-lines col 01 with foreground-color cob-color-red
                                                 erase eol BEEP.
     accept   WS-Reply at line WS-lines col 52 AUTO.
*>
 aa140-Emp-Read-Error.
     display  PY180 at line WS-23-Lines col 1 erase eos
                            foreground-color 4 BEEP.
     display  PY-Emp-Status at line WS-23-Lines col 40.
     move     PY-Emp-Status to PY-PR1-Status.
     perform  ZZ040-Evaluate-Message.
     display  WS-Eval-Msg   at line WS-23-lines col 43.
     display  SY003 at line WS-lines col 01 with foreground-color cob-color-red
                                                 erase eol BEEP.
     accept   WS-Reply at line WS-lines col 52 AUTO.
*>
 aa145-Emp-Write-Error.
     display  PY131 at line WS-23-Lines col 1 erase eos
                            foreground-color 4 BEEP.
     display  PY-Emp-Status at line WS-23-Lines col 40.
     move     PY-Emp-Status to PY-PR1-Status.
     perform  ZZ040-Evaluate-Message.
     display  WS-Eval-Msg   at line WS-23-lines col 43.
     display  SY003 at line WS-lines col 01 with foreground-color cob-color-red
                                                 erase eol BEEP.
     accept   WS-Reply at line WS-lines col 52 AUTO.
*>
 aa150-His-Write-Error.
     display  PY133 at line WS-23-Lines col 1 erase eos
                            foreground-color 4 BEEP.
     display  PY-His-Emp-Status at line WS-23-Lines col 39.
     move     PY-His-Emp-Status to PY-PR1-Status.
     perform  ZZ040-Evaluate-Message.
     display  WS-Eval-Msg   at line WS-23-lines col 41.
     display  SY003 at line WS-lines col 01 with foreground-color cob-color-red
                                                 erase eol BEEP.
     accept   WS-Reply at line WS-lines col 52 AUTO.
*>
 aa155-Emp-Rewrite-Error.
     display  PY135 at line WS-23-Lines col 1 erase eos
                            foreground-color 4 BEEP.
     display  PY-Emp-Status at line WS-23-Lines col 42.
     move     PY-Emp-Status to PY-PR1-Status.
     perform  ZZ040-Evaluate-Message.
     display  WS-Eval-Msg   at line WS-23-lines col 44.
     display  SY003 at line WS-lines col 01 with foreground-color cob-color-red
                                                 erase eol BEEP.
     accept   WS-Reply at line WS-lines col 52 AUTO.
*>
 aa998-Hard-Quit-All.
     close    PY-Accounts-File.  *> full through
*>
 aa999-Hard-Quit-Param.
     close    PY-Param1-File.
     goback.
*>
*> JIC goback fails :(
*>
 Menu-Ex.
     exit     program.
*>
 ba000-Process-Employee-Basics section.
*>************************************
*> Remember param1 is closed.
*>
     initialise
              PY-Employee-Record
              WS-Employee-Number.
*>
     display  SS-Employee-Data-1.
*>
*> next is 9(7),  is enter zero for a new employee or using F1
*>
     accept   WS-Employee-Number at 0521  foreground-color 3 UPDATE.  *> 9(7)
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to ba999-Exit.
     if       Cob-Crt-Status = Cob-Scr-F1         *> New record requested
         or   WS-Employee-Number = zeros
              display  spaces at 2301 erase eos   *> Clear F1 & Esc message
              start    PY-Employee-File LAST
                       invalid key
                               move    zeros to WS-Employee-No
                       not invalid key
                               read    PY-Employee-File
                               if      Emp-No not = zeros
                                       move    Emp-No to WS-Employee-No
              end-start
              add      1 to WS-Employee-No        *> Use next #  9(6)
              move     WS-Employee-In to Customer-Code
*> Create check digit
              move     "C"  to  maps09-reply
              perform  Maps09
              if       Maps09-Reply not = "Y"     *> Should not happen Aborting, check for a bug in code here
                       display  PY127    at line WS-23-Lines col 1 foreground-color 4
                       display  SY003    at line WS-Lines col 1
                       accept   WS-Reply at line WS-lines col 53
                       close    PY-Employee-File
                                PY-History-File
                       goback   returning 3
              end-if
              move     WS-Employee-No     to PY-PR2-Last-Employee-No   *>excl chg digit BUT IS IT NEEDED ?
              move     Customer-Code      to WS-Employee-In
              initialise PY-Employee-Record
                         PY-History-Record
              perform  ba920-Init-Employee-Record
              move     WS-Employee-Number to Emp-No
                                             His-Emp-No
              display  Emp-No at 0521         *> incl chg digit
              write    PY-Employee-Record
              if       PY-Emp-Status not = zeros
                       perform  aa145-Emp-Write-Error
                       go to    ba999-Exit
              end-if
              write    PY-History-Record
              if       PY-His-Emp-Status not = zeros
                       perform  aa150-His-Write-Error
                       go to    ba999-Exit
              end-if
     else
              display  spaces at 2301 erase eos   *> Clear F1 & Esc message
              move     WS-Employee-Number to Emp-No
              read     PY-Employee-File key Emp-No
              if       PY-Emp-Status = 21 or = 23
                       display  PY180    at line WS-23-Lines col 1 foreground-color 4 erase eos
                       display  SY002    at line WS-Lines col 1
                       accept   FS-Reply at line WS-Lines col 33
                       go to    ba000-Process-Employee-Basics         *> Try again
              end-if
              if       PY-Emp-Status not = zeros
                       perform  aa140-Emp-Read-Error
                       go to ba999-Exit                        *> not a expected response so quit
              end-if
     end-if.
*>
*>  We now have a existing emp or are creating a new one
*>  so now to get all the data in UPDATE mode in case it exists
*>
     accept   Emp-Name         at line  7 col 21  foreground-color 3 UPDATE.
     move     spaces to WS-Temp-Name-1
                        WS-Temp-Name-2
                        WS-Temp-Name-3.
     unstring Emp-Name
                     delimited by space
                     into   WS-Temp-Name-1
                            WS-Temp-Name-2
                            WS-Temp-Name-3.
     string   WS-Temp-Name-3  delimited by " "
              WS-Temp-Name-1  delimited by " "
              WS-Temp-Name-2  delimited by " "
                       into  Emp-Search-Name.
*>
*> TEST to confirm correct operation
*>
     display  Emp-Search-Name at 2231.   *> TESTS THE ABOVE IS CORRECT.
*>
     accept   Emp-Address-1    at line  8 col 31  foreground-color 3 UPDATE.
     accept   Emp-Address-2    at line  9 col 31  foreground-color 3 UPDATE.
     accept   Emp-Address-3    at line 10 col 31  foreground-color 3 UPDATE.
     accept   Emp-Address-4    at line 11 col 31  foreground-color 3 UPDATE.
*>
*> REMINDER will need to use this next code block for other State tests
*>
     perform  forever
              accept   Emp-State        at line 12 col 37  foreground-color 3 UPDATE UPPER
              MOVE     ZERO TO C
              SET      QQ TO 1
              search   all WS-States  *>  at end      move zero to C
                       when  Emp-State = WS-Codes (QQ)
                            SET C to QQ
              end-search
              if       C = zero
                       display  PY129 at line WS-23-Lines col 1 foreground-color 4
                                                                erase eol
                       exit     perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit     perform
              end-if
     end-perform.
*>


     accept   Emp-Zip          at line 12 col 58  foreground-color 3 UPDATE.
     accept   Emp-Phone-No     at line 13 col 27  foreground-color 3 UPDATE.
     move     Emp-SSN   to WS-Temp-SSN-Orig         *> 888/99/9999 -> 999-99-9999
     move     "-" to WS-Temp-SSN-Orig (4:1)
                     WS-Temp-SSN-Orig (7:1).
*>
*> ABOVE MAY NOT WORK ????? <<<<<<<<<<<<<<<<<
*>
     perform  forever
              accept   WS-Temp-SSN-Orig at line 15 col 22  foreground-color 3 UPDATE
              if       WS-Temp-SSN-1st not numeric
                  or   WS-Temp-SSN-2nd not numeric
                  or   WS-Temp-SSN-3rd not numeric
                  or   WS-Temp-SSN-Orig (4:1) not = "-"
                  or   WS-Temp-SSN-Orig (7:1) not = "-"
                       display  PY174 at line WS-23-Lines col 1 foreground-color 4
                                                                erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit  perform
              end-if
     end-perform.
*>
     perform  forever
              accept   Emp-Pension-Used at line 15 col 76  foreground-color 3 UPPER UPDATE
              if       Emp-Pension-Used not = "Y"
                                    and not = "N"
                       display  PY119 at line WS-23-Lines col 1 foreground-color 4
                                                                erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
     end-perform.
*>
     accept   Emp-Bank-Acct-No at line 16 col 22  foreground-color 3 UPDATE.
     accept   Emp-Job-Code     at line 16 col 74  foreground-color 3 UPDATE.
*>
     move     "00/00/0000"   to WS-Emp-Date.             *> temp date for accepting etc
     move     Emp-Birth-Date to WS-Test-YMD.             *> ccyymmdd
     perform  ba900-Test-Date-1.
*>
     perform  forever
              move     1722  to Curs
              perform  ba910-Accept-Date
              if       A not = zero
                       display  PY105 at line WS-23-Lines col 1 foreground-color 4
                                                                erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       move     WS-Test-YMD to Emp-Birth-Date
                       exit perform
              end-if
     end-perform.
*>
     perform  forever
              accept   Emp-Taxing-State at line 17 col 75  foreground-color 3 UPDATE UPPER
              MOVE     ZERO TO C
              SET      QQ   TO 1
              search   all WS-States  *>  at end      move zero to C
                       when  Emp-Taxing-State = WS-Codes (QQ)
                            SET C to QQ
              if       C = zero
                       display  PY129 at line WS-23-Lines col 1 foreground-color 4
                                                                erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
*>
     perform  forever
              accept   Emp-Sex          at line 18 col 22  foreground-color 3 UPDATE UPPER
              if       Emp-Sex not = "M"
                           and not = "F"
                       display  PY175 at line WS-23-Lines col 1 foreground-color 4
                                                                erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
*>
     perform  forever
              accept   Emp-Status       at line 20 col 76  foreground-color 3 UPDATE UPPER
              if       Emp-Status = "A" or "L" or "T"
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              else
                       display  PY176 at line WS-23-Lines col 1 foreground-color 4
                                                                erase eol
                       exit perform cycle
              end-if
     end-perform.
*>
*> Ignoring Term date as just started :)
*>
*> Here not do a write as it was created prior to ba000 running.
*>
     rewrite  PY-Employee-Record.
     if       PY-Emp-Status not = zeros
              perform  aa155-Emp-Rewrite-Error  *> then ba999-exit
              move     zeros to WS-Saved-Emp-No
              go to    ba999-Exit
     else
              move     Emp-No to WS-Saved-Emp-No
     end-if
     go to    ba999-Exit.    *> End of this process
*>
 ba900-Test-Date-1.
     move     WS-Test-YMD (1:4) to  WS-Emp-Date (7:4).   *> ccyymmdd to mm/dd/ccyy or dd/mm/ccyy
     if       PY-PR1-Date-Format = 2   *> USA
              move     WS-Test-YMD (5:2) to  WS-Emp-Date (1:2)
              move     WS-Test-YMD (7:2) to  WS-Emp-Date (4:2)
     else
              move     WS-Test-YMD (5:2) to  WS-Emp-Date (4:2)
              move     WS-Test-YMD (7:2) to  WS-Emp-Date (1:2).      *> date converted to aa/bb/ccyy
*>
 ba910-Accept-Date.
     accept   WS-Emp-Date at line 17 col 22  foreground-color 3 UPDATE.    *>  pic 99/99/9999
     move     WS-Emp-Date to WS-Date.                               *> aa/bb/ccyy
     perform  zz010-Test-YMD.
*>
 ba920-Init-Employee-Record.
     move     Emp-No   to His-Emp-No.
     move     PY-PR1-Dflt-HS-Type      to Emp-HS-Type.
     move     PY-PR1-Dflt-Pay-Interval to Emp-Pay-Interval.
     move     "A"                      to Emp-Status.
     move     "N"                      to Emp-Sex.
     move     "S"                      to Emp-Marital.
*> No I do not understand this next block yet      <<<<<
     if       Emp-Pay-Interval = "W" or = "B"
              move     PY-PR2-Last-WB-Apply-No to Emp-Cur-Apply-No
              move     52          to Emp-Pay-Freq
     else
              move     24          to Emp-Pay-Freq.
              move     PY-PR2-Last-SM-Apply-No to Emp-Cur-Apply-No.
     if       Emp-Pay-Interval = "M" or = "B"
              divide   Emp-Pay-Freq by 2 giving Emp-Pay-Freq.
*>
     move     PY-PR1-Dflt-Pay-Rate to Emp-Rate (1).
     if       Emp-HS-Type = "H"
              move     PY-PR1-Rate2-Factor to Emp-Rate (2)
              move     PY-PR1-Rate3-Factor to Emp-Rate (3).
     move     PY-PR1-Dflt-Norm-Units  to Emp-Normal-Units.
     compute  Emp-Max-Pay = Emp-Rate (1) * PY-PR1-Max-Pay-Factor * Emp-Normal-Units.
     move     PY-PR1-Rate4-Exclusion-Type  to Emp-Rate4-Exclusion.
     move     "N"        to Emp-Eic-Used
                            Emp-Cal-Head-Of-House
                            Emp-Pension-Used
                            Emp-FWT-Exempt
                            Emp-SWT-Exempt
                            Emp-LWT-Exempt
                            Emp-FICA-Exempt
                            Emp-SDI-Exempt.
*>
     perform  varying  B from 1 by 1 until B > 5
              move     "N" to Emp-Sys-Exempt (B)
              move     PY-PR1-Max-Dist-Accts  to Emp-Dist-Acct (B)
              move     100                    to Emp-Dist-Pcent (B)
              if       B = 5
                       exit perform
              end-if
     end-perform.
     move     WSE-Date-9 to Emp-Start-Date.
     move     PY-PR1-Dflt-Vac-Rate to Emp-Vac-Rate.
     move     PY-PR1-Dflt-SL-Rate  to Emp-SL-Rate.
     perform  varying  B from 1 by 1 until B > 3
              move     "A"  to Emp-ED-Amt-Pcent (B)
              move     "D"  to Emp-ED-Earn-Ded (B)
              move     1    to Emp-ED-Exclusion (B)
              move     "N"  to Emp-ED-Limit-Used (B)
              move     PY-PR1-Dflt-Dist-Acct to Emp-ED-Acct-No (B)
              if       B = 3
                       exit perform
              end-if
     end-perform.
*>
*> Next, Is this Needed ?
*>
     perform  varying  B from 1 by 1 until B > 4
              move     PY-PR1-Rate-Name (B) to WS-Rate-Lit (B)
              if       B = 4
                       exit perform
              end-if
     end-perform.
*>
 ba920-exit.  exit.    *> Remove if another paragraph
*>
     go  to   ba999-Exit.
*>
 ba999-Exit.   exit section.
*>
 ca000-Process-Ded-Earn        section.
*>************************************
*> Remember param1 is closed.
*>
     display  SS-Employee-Data-2.
*> Use existing Emp-No but update
 ca010-Get-Emp-No.
     move     05 to AN-LINE.
     move     12 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Employee-Number
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to ca999-Exit.
     if       Emp-No not = WS-Employee-Number
              move     WS-Employee-Number  to Emp-No
              read     PY-Employee-File key Emp-No
              if       PY-Emp-Status not = zeros
                       display  PY173 at line WS-23-Lines foreground-color 4 erase eol
                       go to ca010-Get-Emp-No
              else
                       display  space at line WS-23-Lines erase eos.
*>
     display  Emp-Name at 0527.
     move     Emp-SSN to WS-Temp-SSN-Orig.
     inspect  WS-Temp-SSN-Orig replacing all "/" by "-".
     display  WS-Temp-SSN-Orig at 0566.
*>
 ca020-Get-Act-Pcents.
*>
*>  Process SS Left hand side first
*>
     move     09 to AN-LINE.         *> 1 before starting line
     move     zero to Error-Code.
     move     zero to WS-Pcent-Total. *> 2 accum Emp-Dist-Pcent 1 - 5
     perform  varying A from 1 by 1 until A > 5
              display  space at line WS-22-Lines erase eos   *> clear any prev msgs
              add      1 to AN-Line
              move     12 to AN-COLUMN
              move     Emp-Dist-Acct (A) to B
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE B
                                                     by REFERENCE AN-ACCEPT-NUMERIC
              if       B  not = zero
                  and  WS-Act-GL-No (B) = zeros
                       display  PY124 at line WS-22-lines col 1 foreground-color 4 erase eol
                       display  B at line AN-LINE col AN-COLUMN foreground-color 4
                       move     1 to Error-Code
              else
                       move     B to Emp-Dist-Acct (A)
              end-if
   *>                    go to ca020-Get-Acct-1
   *>           display  space at line WS-22-Lines erase eol
              move     06 to AN-LINE
              move     27 to AN-COLUMN
              move     Emp-Dist-Pcent (A) to WS-Temp-Pcent-E
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Pcent-E
*>                                                      by REFERENCE AN-ACCEPT-NUMERIC
              move     WS-Temp-Pcent-E to WS-Temp-Pcent
              if       WS-Temp-Pcent > 100.00
                       display  PY136 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       move     1 to Error-Code
              else
                       move     WS-Temp-Pcent to Emp-Dist-Pcent (A)
                       add      WS-Temp-Pcent to WS-PCent-Total
                       move     WS-PCent-Total to WS-Temp-Pcent-E
                       display  WS-Temp-Pcent-E at 1527
                       if       WS-PCent-Total > 100.00
                                display  WS-Temp-Pcent-E at 1527 foreground-color 4
                                display  PY137 at line WS-Lines col 1 foreground-color 4 erase eol
                                move     1 to Error-Code
                       end-if
              end-if
              if       Error-Code not = zero
 *>                      subtract 1 from A   *> Redo line
                       move     zero to Error-Code
                       go to    ca020-Get-Act-Pcents
              end-if
              if       A = 5
                       move     WS-Pcent-Total to WS-Temp-Pcent-E
                       display  WS-Temp-Pcent-E at 1527
                       if       WS-PCent-Total > 100.00
                                display  WS-Temp-Pcent-E at 1527 foreground-color 4
                                display  PY137 at line WS-Lines col 1 foreground-color 4 erase eol
  *>                              move     1 to Error-Code
                                go to  ca020-Get-Act-Pcents
                       end-if
                       exit perform
              end-if
     end-perform.
*>
 ca020-Process-Exempts.
     move     zero to Error-Code.
     accept   Emp-FICA-Exempt at 0955 foreground-color 3 UPPER UPDATE
     if       Emp-FICA-Exempt not = "Y" and not = "N"
              display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
              display  Emp-FICA-Exempt at 0955 foreground-color 4
              move     1 to Error-Code.
     accept   Emp-FWT-Exempt  at 0975 foreground-color 3 UPPER UPDATE
     if       Emp-FWT-Exempt not = "Y" and not = "N"
              display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
              display  Emp-FWT-Exempt at 0975 foreground-color 4
              move     1 to Error-Code.

     accept   Emp-Co-FUTA-Exempt at 1055 foreground-color 3 UPPER UPDATE
     if       Emp-Co-FUTA-Exempt not = "Y" and not = "N"
              display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
              display  Emp-FICA-Exempt at 1055 foreground-color 4
              move     1 to Error-Code.
     accept   Emp-SWT-Exempt at 1075 foreground-color 3 UPPER UPDATE
     if       Emp-SWT-Exempt not = "Y" and not = "N"
              display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
              display  Emp-SWT-Exempt at 1075 foreground-color 4
              move     1 to Error-Code.

     accept   Emp-Co-SUI-Exempt at 1155 foreground-color 3 UPPER UPDATE
     if       Emp-Co-SUI-Exempt not = "Y" and not = "N"
              display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
              display  Emp-Co-SUI-Exempt at 1155 foreground-color 4
              move     1 to Error-Code.
     accept   EMP-LWT-Exempt at 1174 foreground-color 3 UPPER UPDATE
     if       Emp-LWT-Exempt not = "Y" and not = "N"
              display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
              display  Emp-LWT-Exempt at 1075 foreground-color 4
              move     1 to Error-Code.

     accept   Emp-SDI-Exempt at 1255 foreground-color 3 UPPER UPDATE
     if       Emp-SDI-Exempt not = "Y" and not = "N"
              display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
              display  Emp-SDI-Exempt at 1255 foreground-color 4
              move     1 to Error-Code.
     if       Error-Code not = zero
              go to ca020-Process-Exempts.
*>
     move     46   to C  *> USe correct value >>>> <<<<
     move     zero to Error-Code
     perform  varying A from 1 by 1 until A > 5
              accept   Emp-Sys-Exempt (A) at line 15 col C foreground-color 3 UPPER UPDATE
              if       Emp-Sys-Exempt (A) not = "Y" and not = "N"
                       display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       display  Emp-Sys-Exempt (A) at line 15 col C foreground-color 4
                       move     1 to Error-Code
              end-if
              add      7  to C
              if       A = 5 and Error-Code = zero
                       exit perform
              end-if
              if       A = 5 and Error-Code not = zero
                       move     46 to C
                       move     zero to A
                       exit perform cycle   *> Yep could remove this one but in case of extra code
              end-if
              exit perform cycle
     end-perform.
*>
*> Emp specific Ded/Earn
*>
     move     18 to AN-LINE.
     perform  varying A from 1 by 1 until A > 3
              move     zero to Error-Code   *> working on a line by line basis
              add      1 to AN-LINE
              accept   Emp-Ed-Used (A) at line AN-LINE col 6 foreground-color 3 UPDATE UPPER
              if       Cob-CRT-Status = Cob-Scr-Esc
                       exit perform
              end-if
              if       Emp-Ed-Used (A) not = "Y" and not = "N"
                       display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       display  Emp-Ed-Used (A) at line AN-LINE col 6 foreground-color 4
                       move     1 to Error-Code
              end-if
              if       Emp-ED-Used (A) = "N"
                       initialise Emp-Ed-Group (A)
                       exit perform cycle   *> Check all 3 incase its an amend for one of them
              end-if
*>
*>  Now all fields are being used for this line
*>
              accept   Emp-ED-Desc (A)     at line AN-LINE col  9 foreground-color 3 UPDATE
              accept   Emp-ED-Earn-Ded (A) at line AN-LINE col 27 foreground-color 3 UPDATE UPPER
              if       Emp-Ed-Earn-Ded (A) not = "D" and not = "E"
                       display  PY115 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       display  Emp-Ed-Used (A) at line AN-LINE col 27 foreground-color 4
                       move     1 to Error-Code
              end-if
              if       Emp-ED-Earn-Ded (A) = "D"     *> Is this blk needed ?
                       move     16 to WS-Dflt-Chk-Cat
                       move      2 to WS-Dflt-Acct
              else
                       move      7 to WS-Dflt-Chk-Cat
                       move      3 to WS-Dflt-Acct
              end-if
*>
              if       Emp-ED-Chk-Cat (A) = zero
                       move     WS-Dflt-Chk-Cat to Emp-ED-Chk-Cat (A)
                       move     WS-Dflt-Acct    to Emp-ED-Acct-No (A)
              end-if
*>
              if       Emp-ED-Earn-Ded (A) = "D"
                       move     16 to Emp-ED-Chk-Cat (A)
                       move      2 to Emp-ED-Acct-No (A)
              else
                       move      7 to Emp-ED-Chk-Cat (A)
                       move      3 to Emp-ED-Acct-No (A)
              end-if
*>
              move     31 to AN-COLUMN
              move     Emp-ED-Acct-No (A) to B
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE B
                                                     by REFERENCE AN-ACCEPT-NUMERIC
              if       B  not = zero
                  and  WS-Act-GL-No (B) = zeros
                       display  PY124 at line WS-23-lines col 1 foreground-color 4 erase eol
                       display  B at line AN-LINE col AN-COLUMN foreground-color 4
                       move     1 to Error-Code
              else
                       move     B to Emp-ED-Acct-No (A)
              end-if
*>
              accept   Emp-ED-Amt-Pcent (A) at line AN-LINE col 37 foreground-color 3 UPDATE UPPER
              if       Emp-ED-Amt-Pcent (A) not = "A" and not = "P"
                       display  PY121 at line WS-23-lines col 1 foreground-color 4 erase eol
                       display  Emp-ED-Amt-Pcent (A) at line AN-LINE col 37 foreground-color 4
                       move     1 to Error-Code
              end-if
              move     42 to AN-COLUMN
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-ED-Factor (A)
                                                     by REFERENCE AN-ACCEPT-NUMERIC
              accept   Emp-ED-Limit-Used (A) at line AN-LINE col 55 foreground-color 3
              if       Emp-ED-Limit-Used (A) not = "Y" and not = "N"
                       display  Emp-ED-Limit-Used (A) at line AN-LINE col 55 foreground-color 4
                       display  PY119 at line WS-23-lines col 1 foreground-color 4 erase eol
                       move     1 to Error-Code
              end-if
              if       Emp-ED-Limit-Used (A) = "Y"
                       move     61 to AN-COLUMN
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-ED-Limit (A)
                                                              by REFERENCE AN-ACCEPT-NUMERIC
              end-if
              accept   Emp-ED-Exclusion (A) at line AN-LINE col 72 foreground-color 3 UPDATE
              if       Emp-ED-Exclusion (A) < 1 or > 4
                       display  Emp-ED-Exclusion (A) at line AN-LINE col 72 foreground-color 4
                       display  PY108 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       move     1 to Error-Code
              end-if
              move     75 to AN-COLUMN
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-ED-Chk-Cat (A)
                                                     by REFERENCE AN-ACCEPT-NUMERIC
              if       (Emp-ED-Chk-Cat (A) not < PY-PR1-Lo-Earn-Chk-Cat
                  and                      not > PY-PR1-Hi-Earn-Chk-Cat)
                or     (Emp-ED-Chk-Cat (A) not > PY-PR1-Hi-Ded-Chk-Cat
                  and                      not < PY-PR1-Lo-Ded-Chk-Cat)
                       next sentence
              else
                       display  Emp-ED-Chk-Cat (A) at line AN-LINE col 75 foreground-color 4
                       display  PY138 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       move     1 to Error-Code
              end-if
              if       Error-Code  not = zero
                       subtract 1 from A
              end-if
              exit perform cycle
     end-perform.
*>
*> Here not do a write as it was created prior to ba000 running.
*>
     rewrite  PY-Employee-Record.
     if       PY-Emp-Status not = zeros
              perform  aa155-Emp-Rewrite-Error  *> then ba999-exit
              move     zeros to WS-Saved-Emp-No
              go to    ca999-Exit
     else
              move     Emp-No to WS-Saved-Emp-No
     end-if.
*>
 ca999-Exit.   exit section.
*>
 da000-Process-Rates           section.
*>************************************
*> Remember param1 is closed.
*>
     display  SS-Employee-Data-3.
*> Use existing Emp-No but update
 da010-Get-Emp-No.
     move     05 to AN-LINE.
     move     12 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Employee-Number
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to da999-Exit.
     if       Emp-No not = WS-Employee-Number
              move     WS-Employee-Number  to Emp-No
              read     PY-Employee-File key Emp-No
              if       PY-Emp-Status not = zeros
                       display  PY173 at line WS-23-Lines foreground-color 4 erase eol
                       go to da010-Get-Emp-No
              else
                       display  space at line WS-23-Lines erase eos
              end-if
     end-if.
*>
     display  Emp-Name at 0527.
     move     Emp-SSN to WS-Temp-SSN-Orig.
     inspect  WS-Temp-SSN-Orig replacing all "/" by "-".
     display  WS-Temp-SSN-Orig at 0566.
*>
     perform  forever
              accept   Emp-HS-Type at 0833 foreground-color 3 UPDATE UPPER
              if       Emp-HS-Type not = "H" and not = "S"
                       display  Emp-HS-Type at 0833 foreground-color 4
                       display  PY110 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
     perform  forever
              accept   Emp-Pay-Interval at 0933 foreground-color 3 UPDATE UPPER
              if       Emp-Pay-Interval not = "S" and not "M" and not "W" and not "B"
                       display  Emp-Pay-Interval at 0933 foreground-color 4
                       display  PY109 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
     perform  forever
              accept   Emp-Marital at 0974 foreground-color 3 UPDATE UPPER
              if       Emp-Marital not = "S" and not "M"
                       display  Emp-Marital at 0974 foreground-color 4
                       display  PY223 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       exit perform cycle
              else
                       display space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
*>
     perform  forever
              move     Emp-FWT-Allow to A
              accept   A  at 1073 foreground-color 3 UPDATE
              if       Emp-FWT-Exempt = "Y"
                   and A not = zero
                       display  A at 1073 foreground-color 4
                       display  PY229 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       exit perform cycle
              else
                       display space at line WS-23-Lines col 1 erase eol
                       move     A to Emp-FWT-Allow
                       exit perform
              end-if
     end-perform.
*>
     display  PY-PR1-Rate-Name (1) at 1101.
     if       Emp-Rate (1) = zero
        and   Emp-HS-Type = "H"
              move     "Y" to WS-Recalculate
     else
              move     "N" to WS-Recalculate.
*>
     move     11 to AN-LINE.
     move     26 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Rate (1)
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     if       WS-Recalculate = "Y"
              compute Emp-Rate (2) = Emp-Rate (1) * PY-PR1-Rate2-Factor
              compute Emp-Rate (3) = Emp-Rate (1) * PY-PR1-Rate3-Factor
              compute Emp-Max-Pay  = Emp-Rate (1) * Emp-Normal-Units * PY-PR1-Max-Pay-Factor
     end-if.
*> This is in ratent (CBasic code) and no do not understand the reasoning for it.
*> ^^^^^
 *>   then emp.rate(2)= emp.rate(1)*pr1.rate2.factor: \
 *>    emp.rate(3)= emp.rate(1)*pr1.rate3.factor: \
 *>    emp.max.pay= emp.rate(1)*emp.normal.units*pr1.max.pay.factor: \
 *>    trash%=fn.put%(str$(emp.rate(2)), fld.rate2%): \
 *>    trash%=fn.put%(str$(emp.rate(3)), fld.rate3%): \
 *>    trash%=fn.put%(str$(emp.max.pay), fld.max.pay%)

*>
     perform  forever
              move     Emp-SWT-Allow to A           *> Don't overwrite if wrong
              accept   A at 1173 foreground-color 3 UPDATE
              if       Emp-SWT-Exempt = "Y"
                  and  A not = zero
                       display  A at 1173 foreground-color 4
                       display  PY230 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       move     A to Emp-SWT-Allow
                       exit perform
              end-if
     end-perform.
*>
*>
     display  PY-PR1-Rate-Name (2) at 1201.
     move     12 to AN-LINE.
 *>    move     26 to AN-COLUMN.  *> Same as previous
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Rate (2)
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
     perform  forever
              move     Emp-LWT-Allow to A
              accept   A at 1273 foreground-color 3 UPDATE
              if       Emp-LWT-Exempt = "Y"
                  and  A not = zero
                       display  A at 1273 foreground-color 4
                       display  PY231 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       move     A to Emp-LWT-Allow
                       exit perform
              end-if
     end-perform.
*>
*>
     display  PY-PR1-Rate-Name (3) at 1301.
     move     13 to AN-LINE.
 *>    move     26 to AN-COLUMN.  *> Same as previous
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Rate (3)
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
     perform  forever
              accept   Emp-Eic-Used at 1374 foreground-color 3 UPDATE UPPER
              if       Emp-Eic-Used not = "Y" and not = "N"
                       display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       display  Emp-Eic-Used at 1374 foreground-color 4
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
*>
     display  PY-PR1-Rate-Name (4) at 1401.
     move     14 to AN-LINE.
 *>    move     26 to AN-COLUMN.  *> Same as previous
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Rate (4)
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
     perform  forever
              accept   Emp-Rate4-Exclusion at 1533 foreground-color 3 UPDATE
              if       Emp-Rate4-Exclusion < 1 or > 4
                       display  Emp-Rate4-Exclusion at 1533 foreground-color 4
                       display  PY108 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
*>
     move     16 to AN-LINE.
 *>    move     26 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Auto-Units
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     perform  forever
              accept   Emp-Cal-Head-Of-House at 1674 foreground-color 3 UPDATE UPPER
              if       Emp-Cal-Head-Of-House not = "Y" and not = "N"
                       display  PY119 at line WS-23-Lines col 1 foreground-color 4 erase eol
                       display  Emp-Cal-Head-Of-House at 1674 foreground-color 4
                       exit perform cycle
              else
                       display  space at line WS-23-Lines col 1 erase eol
                       exit perform
              end-if
     end-perform.
*>
     move     17 to AN-LINE.
 *>    move     26 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Normal-Units
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     if       Emp-HS-Type = "H"
              compute Emp-Max-Pay = Emp-Rate (1) * Emp-Normal-Units * PY-PR1-Max-Pay-Factor.  *> ratent 5012
*>
     move     73 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Cal-Ded-Allow
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
     move     18 to AN-LINE.
     move     25 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Max-Pay
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
     move     20 to AN-LINE.
     move     26 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Vac-Rate
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     move     50 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Vac-Accum
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     move     67 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Vac-Used
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
     move     21 to AN-LINE.
     move     26 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-SL-Rate
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     move     50 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-SL-Accum
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     move     67 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-SL-Used
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
     move     22 to AN-LINE.
     move     50 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Comp-Accum
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     move     67 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE Emp-Comp-Used
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
*> Here not do a write as it was created prior to ba000 running.
*>
     rewrite  PY-Employee-Record.
     if       PY-Emp-Status not = zeros
              perform  aa155-Emp-Rewrite-Error  *> then ba999-exit
              move     zeros to WS-Saved-Emp-No
              go to    da999-Exit
     else
              move     Emp-No to WS-Saved-Emp-No
     end-if.
*>
 da999-Exit.   exit section.
*>
 ea000-Employee-History      section.
*>**********************************
*> Remember param1 is closed.
*>
     open     input PY-Comp-Hist-File.
     if       PY-Coh-Status not = zeros
              display  PY013 at line WS-23-Lines col 1 erase eos
                                        foreground-color 4 BEEP
              display  PY-COH-Status at line WS-23-Lines col 44
              move     PY-COH-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  WS-Eval-Msg   at line WS-23-lines col 47
              display  SY001 at line WS-lines col 01
                            with foreground-color cob-color-red erase eol BEEP
              accept   WS-Reply at line WS-lines col 52 AUTO.
              close    PY-Comp-Hist-File
              go to ea999-Exit.
*>
     move     1  to RRN.
     read     PY-Comp-Hist-File.
     if       PY-CoH-Status not = zero
              perform  zz100-Coh-Read-Error
              close    PY-Comp-Hist-File
                       PY-Param1-File
              goback   returning 2
     end-if.
*>
     if       Coh-Starting-Up = "N"    *> Not apply for pyupdpm,pyupdhis
              display  PY015 at line WS-23-Lines col 1 foreground-color 4
                                                       erase eos
              display  SY003 at line WS-Lines    col 1 foreground-color 4
              accept   WS-Reply at line WS-Lines col 53
  *>            close    PY-Comp-Hist-File
              go to    ea999-Exit.
*>
     display  SS-Employee-History-Data-1.
*>
*> Use existing Emp-No but update
 ea010-Get-Emp-No.
     move     05 to AN-LINE.
     move     12 to AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Employee-Number
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to ea999-Exit.
     if       Emp-No not = WS-Employee-Number
              move     WS-Employee-Number  to Emp-No
              read     PY-Employee-File key Emp-No
              if       PY-Emp-Status not = zeros
                       display  PY173 at line WS-23-Lines foreground-color 4 erase eol
                       go to ea010-Get-Emp-No
              else
                       display  space at line WS-23-Lines erase eos
              end-if
     end-if.
*>





     display  Emp-Name at 0527.
     move     Emp-SSN to WS-Temp-SSN-Orig.
     inspect  WS-Temp-SSN-Orig replacing all "/" by "-".
     display  WS-Temp-SSN-Orig at 0566.
*>
*> Emp history now and chg the emp # line for name and SSN
*>
*>   Now check that there is no history of a payment
*>   as cannot update history as totals will not be correct
*>   The History record should exist as created in option 1 but JIC
*>
     move     Emp-No to His-Emp-No.
     read     PY-History-File key His-Emp-No.
     if       PY-His-Emp-Status not = zeros
              display  PY132 at line WS-23-Lines col 1 foreground-color 4
              display  SY003 at line WS-Lines col 1
              accept   WS-Reply at line WS-Reply col 53
              go to    ea999-Exit.
*>
*> Now check there has been no payments.
*>
     if       His-QTD-Income-Taxable not = zero
         or   His-YTD-Income-Taxable not = zero
              display  PY141 at line WS-23-Lines col 1 foreground-color 4
              display  SY003 at line WS-Lines col 1
              accept   WS-Reply at line WS-Reply col 53
              go to    ea999-Exit.
*>
     move     8  to AN-Line.
     move     9  to AN-Column.
     set      AN-MODE-IS-NO-UPDATE to true.   *> all init fields.
*>
     move     His-QTD-Income-Taxable  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-Income-Taxable
     move     29 to AN-Column.
     move     His-QTD-Other-Taxable to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-Other-Taxable.
     move     51 to AN-Column.
     move     His-QTD-Other-NonTaxable to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-Other-NonTaxable.
     move     69 to AN-Column.
     move     His-QTD-Fica-Taxable to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-Fica-Taxable.
*>
     move     9  to AN-Line.
     move     29  to AN-Column.
     move     His-QTD-EIC to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-EIC.
     move     51 to AN-Column.
     move     His-QTD-Tips  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-Tips.
     move     69 to AN-Column.
     move     His-QTD-Net to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-Net.
*>
     move     10  to AN-Line.
     move     29  to AN-Column.
     move     His-QTD-FWT to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-FWT.
     move     51 to AN-Column.
     move     His-QTD-SWT  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-SWT.
     move     69 to AN-Column.
     move     His-QTD-LWT to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-LWT.
*>
     move     11  to AN-Line.
     move     29  to AN-Column.
     move     His-QTD-FICA to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-FICA.
     move     51 to AN-Column.
     move     His-QTD-SDI  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-QTD-SDI.
*>
     move     13  to AN-Line.
     move     zero to C.
     perform  varying AN-Column from 9 by 15 until AN-Column > 69
              add      1 to C
              move     His-QTD-Sys (C)  to  WS-Temp-Amount
              perform  ea100-Get-Amount
              move     WS-Temp-Amount to His-QTD-Sys (C)
              if       C = 5
                       exit perform
              end-if
              exit perform cycle
     end-perform.
*>
     move     14  to AN-Line.
     move     zero to C.
     perform  varying AN-Column from 9 by 15 until AN-Column > 39
              add      1 to C
              move     His-QTD-Emp (C)  to  WS-Temp-Amount
              perform  ea100-Get-Amount
              move     WS-Temp-Amount to His-QTD-Emp (C)
              if       C = 3
                       exit perform
              end-if
              exit perform cycle
     end-perform.
*>
     move     69  to AN-Column.
     move     His-QTD-Other-Ded to WS-Temp-Amount
     perform  ea100-Get-Amount
     move     WS-Temp-Amount to His-QTD-Other-Ded.
*>
     move     15  to AN-Line.
     move     zero to C.
     perform  varying AN-Column from 24 by 15 until AN-Column > 69
              add      1 to C
              move     His-QTD-Units (C)  to  WS-Temp-Amount
              perform  ea100-Get-Amount
              move     WS-Temp-Amount to His-QTD-Units (C)
              if       C = 4
                       exit perform
              end-if
              exit perform cycle
     end-perform.
*>
     move     17  to AN-Line.
     move     9  to AN-Column.
     move     His-YTD-Income-Taxable  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-Income-Taxable
     move     29 to AN-Column.
     move     His-YTD-Other-Taxable to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-Other-Taxable.
     move     51 to AN-Column.
     move     His-YTD-Other-NonTaxable to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-Other-NonTaxable.
     move     69 to AN-Column.
     move     His-YTD-Fica-Taxable to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-Fica-Taxable.
*>
     move     18  to AN-Line.
     move     29  to AN-Column.
     move     His-YTD-EIC to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-EIC.
     move     51 to AN-Column.
     move     His-YTD-Tips  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-Tips.
     move     69 to AN-Column.
     move     His-YTD-Net to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-Net.
*>
     move     19  to AN-Line.
     move     29  to AN-Column.
     move     His-YTD-FWT to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-FWT.
     move     51 to AN-Column.
     move     His-YTD-SWT  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-SWT.
     move     69 to AN-Column.
     move     His-YTD-LWT to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-LWT.
*>
     move     20  to AN-Line.
     move     29  to AN-Column.
     move     His-YTD-FICA to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-FICA.
     move     51 to AN-Column.
     move     His-YTD-SDI  to WS-Temp-Amount.
     perform  ea100-Get-Amount.
     move     WS-Temp-Amount to His-YTD-SDI.
*>
*>
     move     22  to AN-Line.
     move     zero to C.
     perform  varying AN-Column from 9 by 15 until AN-Column > 69
              add      1 to C
              move     His-YTD-Sys (C)  to  WS-Temp-Amount
              perform  ea100-Get-Amount
              move     WS-Temp-Amount to His-YTD-Sys (C)
              if       C = 5
                       exit perform
              end-if
              exit perform cycle
     end-perform.
*>
     move     23  to AN-Line.
     move     zero to C.
     perform  varying AN-Column from 9 by 15 until AN-Column > 39
              add      1 to C
              move     His-YTD-Emp (C)  to  WS-Temp-Amount
              perform  ea100-Get-Amount
              move     WS-Temp-Amount to His-YTD-Emp (C)
              if       C = 3
                       exit perform
              end-if
              exit perform cycle
     end-perform.
*>
     move     69  to AN-Column.
     move     His-YTD-Other-Ded to WS-Temp-Amount
     perform  ea100-Get-Amount
     move     WS-Temp-Amount to His-YTD-Other-Ded.
*>
     move     24  to AN-Line.
     move     zero to C.
     perform  varying AN-Column from 24 by 15 until AN-Column > 69
              add      1 to C
              move     His-YTD-Units (C)  to  WS-Temp-Amount
              perform  ea100-Get-Amount
              move     WS-Temp-Amount to His-YTD-Units (C)
              if       C = 4
                       exit perform
              end-if
              exit perform cycle
     end-perform.
*>
     rewrite  PY-History-Record.
     if       PY-His-Emp-Status not = zeros
              perform  aa150-His-Write-Error
              move     zeros to WS-Saved-Emp-No
              go to    ea999-Exit
     else
              move     Emp-No to WS-Saved-Emp-No
     end-if.
*>
     go       to  ea999-Exit.
*>
 ea100-Get-Amount.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Amount
                                            by REFERENCE AN-ACCEPT-NUMERIC.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to ea999-Exit.
*>
 ea-Dummy.    exit.
*>

*>
 ea999-Exit.   exit section.
*>
 zz010-Test-YMD              section.
*>**********************************
*>
     move     WS-Year  to WS-Test-YMD (1:4).
     if       PY-PR1-Date-Format = 2   *> test for USA - mmddyyyy - -> yyyymmdd
              move     WS-Days  to WS-Test-YMD (5:2)
              move     WS-Month to WS-Test-YMD (7:2)
     else
              move     WS-Days  to WS-Test-YMD (7:2)  *> test for UK - ddmmyyyy -> yyyymmdd
              move     WS-Month to WS-Test-YMD (5:2).
*>
     move     zero  to A.
     move     TEST-DATE-YYYYMMDD (WS-Test-YMD) to A.

 zz010-Exit.  exit section.
*>
*>
 zz030-Common-Routines       section.   *> Never called but holds common routines
*>**********************************
*>
*> Maps04.    *> NOT USED
*>******
*>
 *>    call     "maps04"  using  Maps03-WS.
*>
 *>maps04-Exit. exit.
*>
 Maps09.
*>*****
*>
     call     "maps09"  using  maps09-ws. *>  customer-code.
*>
 maps09-Exit. exit.
*>
*> Used for ACCEPT_NUMERIC after CAll Only
*>
*>C      copy "an-accept.pl".   *> and  perform  AN-Test-Status
      *>
      *> performed after calling "accept_numeric" routine
      *>
       AN-Test-Status.
           move     zeros to COB-CRT-STATUS.
           evaluate AN-Return-Code
                    when = zero
                             move     zero to COB-CRT-STATUS
                    when > zero and < 49 *> F1 thru F48
                             compute COB-CRT-STATUS = AN-Return-Code + 1000
                    when = 49            *> PAGE-UP - 2001
                             move     2001 to COB-CRT-STATUS
                    when = 50            *> PAGE-DOWN - 2002
                             move     2002 to COB-CRT-STATUS
                    when = 51            *> TAB    - 2007
                             move     2007 to COB-CRT-STATUS
                    when = 52            *> BACK-TAB - 2008
                             move     2008 to COB-CRT-STATUS
                    when = 99            *> ESCAPE - 2005
                             move     2005 to COB-CRT-STATUS
                    when other           *> No Others Coded For
                             move     9000 to COB-CRT-STATUS
           end-evaluate.
      *>
*>                                           ==============
*>
 zz030-Exit.  exit section.
*>
*>
 zz040-Evaluate-Message      Section.
*>**********************************
*>
*> For PY-PR1 parameter file anfd other using PR-PR1-Status.
*>
*>C      copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
*>C                                           STATUS by PY-PR1-Status.
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
 zz040-Eval-Msg-Exit.
     exit     section.
*>
 zz070-Convert-Date          section.  *>  NOT USED YET
*>**********************************
*>
*>  Converts date in To-Day to UK/USA/Intl date format using ACAS param
*>*********************************************************************
*> Input:   To-Day
*> output:  WS-Date as uk/US/Inlt date format
*>
     move     To-Day to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> Swap month and days
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> Swap Intl to UK form
     move     To-Day (7:4) to WS-Intl-Year.
     move     To-Day (4:2) to WS-Intl-Month.
     move     To-Day (1:2) to WS-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
 zz100-Coh-Read-Error.
     display  PY013 at line WS-23-Lines col 1 erase eos
                            foreground-color 4 BEEP.
     display  PY-COH-Status at line WS-23-Lines col 44.
     move     PY-COH-Status to PY-PR1-Status.
     perform  ZZ040-Evaluate-Message.
     display  WS-Eval-Msg   at line WS-23-lines col 47.
     display  SY001 at line WS-lines col 01 with foreground-color cob-color-red
                                                 erase eol BEEP.
     accept   WS-Reply at line WS-lines col 52 AUTO.
      *>>>Info: Total Copy Depth Used = 03;  Caution messages issued =   2
