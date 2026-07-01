       >>source free
*>****************************************************************
*>               New  Payroll for USA                            *
*>         Parameter  Menu  &  Fixed  Data  Maintenance          *
*>           Based on CBASIC Code -ish.                          *
*> Some files defined here but not used can be REMOVED.          *<<
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       py900.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 19/10/2025.
*>**
*>    Security.         Copyright (C) 2025-2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Payroll Parameter Menus & Fixed Data.
*>                      Some of this code may well be moved to other modules.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.
*>                      (CBL_) ACCEPT_NUMERIC.c as static.
*>                      ACAS000,
*>                      ACAS008
*>                      acasirsub1 ->  [ For IRS Nominal ledgers ]
*>                        irsnominalMT  [ If using Mysql RDB etc ]
*>
*>                      acas005 ->     [ For GL nomial ledgers ]
*>                        nominalMT     [ If using Mysql RDB etc ]
*>                      CBL_DELETE_FILE
*>                      ACASIRSUB1, 3 - 5.
*>                      MAPS04
*>                      SCR_DUMP
*>                      SCR_RESTORE
*>**
*>    Functions Used:
*>                      CURRENT-DATE.
*>                      TEST-DATE-YYYYMMDD
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
*>                      SY001 - 5, 8, 10 - 14.
*> Program specific:
*>                      PY001 - 10.
*>                      PY101 - 124.
*>                      IR911 - 916.
*>**
*> Changes:
*> 20/09/2025 vbc - 1.0.00 Created - starting. Prior to testing.
*>                         After testing version will be set to v3.3.
*>                         WARNING: You MUST set the terminal program to be 80
*>                         cols wide and MORE than 25 lines deep and this is to
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
*> 27/11/2025 vbc -    .02 Screen size now checked for Minimum of 27 lines.
*>                         All other programs wil do the same. Msg SY010 chgd.
*> 28/11/2025 vbc -    .03 Added capture for Tax-ID.
*> 30/11/2025 vbc -    .04 Added State code and test for Co.State for validity.
*>                         chg some accept in 1st param SS for inline perform
*>                         but there are a lot so stopped.
*> 07/12/2025 vbc      .05 Changed and Added 2 + 2 fields in PY1- for Width-L,
*>                         Width-P, Lines-P, Lines-L & changed prog to support
*>                         them.
*> 09/12/2025 vbc -        Increased minimum screen depth = 28.
*> 19/01/2026 vbc -    .06 Param set up init set max-sys-ed = 5 & max-emp = 3
*> 02/02/2026 vbc -    .07 Added PR1 Hard Delete (Y/N) to params entry yo support
*>                         at end of year goign through Emp and His files and
*>                         Delete any with Emp-status = "D" likewise with History
*>                         record.  REMEMBER TO DO THIS at EOY processing.
*> 07/03/2026 vbc -    .08 Replace most of the if ... go to retry-n with inline
*>                         performs.
*>
*>   REMEMBER, REMEMBER to change code in PY910 & PY920 to match these changes
*>                      if needed.
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
*>
*> Here and in file section are a lot of file defs which are NOT used for py900
*> but present to check file record sizes when using cobc with -ftsymbols
*> they will be removed  once PY is completed or even before :)
*>
*> If any more files are needed they will be set up here for the same reason.
*>
*>C  copy "selpyparam1.cob".
*>
*> Payroll param-1 (USA)
*>
     select  PY-Param1-File  assign        File-47
                             access        dynamic
                             organization  is relative
                             relative key  is RRN
                             status        PY-PR1-Status.
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
*>C  copy "selpyhrs.cob".
*>
*> Payroll Pay Hours (USA)
*>
     select  PY-Pay-Transactions-File
                             assign        file-45
                             access        dynamic
                             organization  indexed
                             record key is Hrs-Emp-No
                             status        PY-Hrs-Status.
*>
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
*>C  copy "selpycalx.cob".
*>
*> Payroll Tax Withholdings California
*>
     select  PY-California-Tax-File
                             assign        File-52    *> pycalx
                             organization  sequential
                             status        PY-Calx-Status.
*>
*>
*> Next 3 are all the same so can use only one stax - may be.
*>
*>C  copy "selpystax.cob".
*>
*> Payroll Tax Withholdings Stax
*>
     select  PY-State-Tax-File
                             assign        File-54    *> pyswt {(ss)  = state code} not needed/used
                             organization  sequential
                             status        PY-Stax-Status.
*>
*>C  copy "selpyswt.cob".
*>
*> Payroll Tax Withholdings SWT
*>
     select  PY-SWT-Tax-File
                             assign        File-54    *> pyswt
                             organization  sequential
                             status        PY-SWT-Status.
*>
*>C  copy "selpylwt.cob".
*>
*> Payroll Tax Withholdings LWT
*>
     select  PY-LWT-Tax-File
                             assign        File-53    *> pylwt
                             organization  sequential
                             status        PY-LWT-Status.
*>
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
*>  File size 339 bytes ??   was 337
*> 25/10/25 vbc - Created.
*> 08/11/25 vbc - Rec size changed
*> 12/11/25 vbc - and again - less.
*> 15/11/25 vbc - again more + 9.
*> 28/12/25 vbc - Consider increasing table to support a.n.other new ded rates.
*> 16/01/26 vbc - Increased size by 2.
*>
 01  PY-System-Deduction-Record.
     03  Ded-FWT-Used             pic x.    *> Y NEEDED ?
     03  Ded-SWT-Used             pic x.    *> Y needed ?
     03  Ded-LWT-Used             pic x.   *>  N
     03  Ded-FICA-Used            pic x.   *>  Y
     03  Ded-CO-FICA-Used         pic x.   *>
     03  Ded-SDI-Used             pic x.   *>
     03  Ded-CO-FUTA-Used         pic x.   *>
     03  Ded-CO-SUI-Used          pic x.   *>
     03  Ded-EIC-Used             pic x.   *>
*>
     03  Ded-FWT-Allowance-Amt    pic S9(5)v99   comp-3.
*>
     03  Ded-FWT-Acct-No          pic 99.
     03  Ded-SWT-Acct-No          pic 99.
     03  Ded-LWT-Acct-No          pic 99.
     03  Ded-FICA-Acct-No         pic 99.
     03  Ded-CO-FICA-Acct-No      pic 99.
     03  Ded-SDI-Acct-No          pic 99.
     03  Ded-CO-FUTA-Acct-No      pic 99.
     03  Ded-CO-SUI-Acct-No       pic 99.
     03  Ded-EIC-Acct-No          pic 99.
*>19 ^
     03  Ded-FICA-Rate            pic 99v99    comp-3.
     03  Ded-FICA-Limit           pic 9(5)v99  comp-3.
     03  Ded-CO-FICA-Rate         pic 99v99    comp-3.
     03  Ded-CO-FICA-Limit        pic 9(5)v99  comp-3.
     03  Ded-SDI-Rate             pic 99v99    comp-3.
     03  Ded-SDI-Limit            pic 9(5)v99  comp-3.
     03  Ded-CO-FUTA-Rate         pic 99v99    comp-3.
     03  Ded-CO-FUTA-Limit        pic 9(5)v99  comp-3.
     03  Ded-CO-FUTA-Max-Credit   pic 9(5)v99  comp-3.
     03  Ded-CO-SUI-Rate          pic 99v99    comp-3.
     03  Ded-CO-SUI-Limit         pic 9(5)v99  comp-3.
     03  Ded-EIC-Rate             pic 99v99    comp-3.
     03  Ded-EIC-Limit            pic 9(5)v99  comp-3.
     03  Ded-EIC-Excess-Rate      pic 99v99    comp-3.
     03  Ded-EIC-Excess-Limit     pic 9(5)v99  comp-3.
*>34 +  28  + 50 = 112
     03  Ded-FWT-Mar                  occurs 7.
         05  Ded-FWT-Mar-Cutoff   pic 9(5)v99  comp-3.
         05  Ded-FWT-Mar-Percent  pic 9(3)v99  comp-3.
*>
     03  Ded-FWT-Sin                  occurs 7.
         05  Ded-FWT-Sin-Cutoff   pic 9(5)v99  comp-3.
         05  Ded-FWT-Sin-Percent  pic 9(3)v99  comp-3.
*>
     03  Ded-Sys-Entries-Used     pic 99.  *> allow for this block to be > 10
     03  Ded-Sys-Data-Blocks          occurs 5.
         05  Ded-Sys-Amt-Percent  pic x.   *>  A
         05  Ded-Sys-Chk-Cat      pic 99.  *>  7 ( 2 - 7 if Earn-Ded = E. 9 - 16 if Earn-Ded = D
         05  Ded-Sys-Earn-Ded     pic x.   *>  E
         05  Ded-Sys-Exclusion    pic 9.   *>  1 ( 1 - 4)
         05  Ded-Sys-Limit-Used   pic x.   *>  Y
         05  Ded-Sys-Used         pic x.   *>  N
         05  Ded-Sys-Desc         pic x(15).
         05  Ded-Sys-Acct-No      binary-char  unsigned.
         05  Ded-Sys-Factor       pic 9(5)v99  comp-3.
         05  Ded-Sys-Limit        pic 9(5)v99  comp-3.
*> Field count 112
*>
*>C  copy "fdpyhrs.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY Pay Transaction  *
*>              Hours  File                 *
*>                                          *
*>*******************************************
*>   Record Size ?? Bytes
*>   see wspyhrs.cob for later updates
*>
 fd  PY-Pay-Transactions-File.
*>
*>C  copy "wspyhrs.cob".
*>*******************************************
*>                                          *
*>  Record Definition For Pay Transactions  *
*>           File                           *
*>     Uses Hrs-Emp-No as key               *
*>*******************************************
*>  File size 19 bytes padded to 20 by filler.
*>
*> 28/10/25 vbc - Created.
*>
 01  PY-Pay-Transactions-Record.
     03  Hrs-Emp-No          pic 9(7).
     03  Hrs-Effective-Date  pic 9(8).    *> ccyymmdd
     03  Hrs-Rate            pic 9.
     03  Hrs-Units           pic s9(3)v99   comp-3.
 *>    03  Hrs-Deleted         pic x.    *> NEEDED ???
     03  filler              pic x.
*>
*> 14 bytes + filler of 6 = 20 to match. the next rec may not be needed ?
*>
 01  PY-Pay-Header-Record.
     03  Hrs-Head-Key        pic 9(7).     *> Always value zero.
     03  Hrs-No-Recs         binary-short unsigned.
     03  Hrs-Batch-No        binary-short unsigned.
     03  Hrs-Proof-No        binary-short unsigned.
     03  Hrs-Proofed         pic x.
     03  filler              pic x(6).
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
*>  File size 28 bytes.
*>
*> THESE FIELD DEFINITIONS MAY NEED CHANGING
*>
*> 29/10/25 vbc - Created.
*>
 01  PY-Pay-Record.
     03  Pay-Emp-No          pic 9(7).
     03  Pay-Interval        pic 9.
     03  Pay-EFf-Date        pic 9(8)       comp. *> ccyymmdd
     03  Pay-Apply-No        pic 9(4)       comp.
     03  Pay-Reporting-Cat   pic xx.           *> is this right ?
     03  Pay-Extended        pic xx.
     03  Pay-Units           pic s9(6)v99   comp-3.
     03  Pay-Amt             pic s9(6)v99   comp-3.
*>
 01  PY-Pay-Header.
     03  Pay-Hdr-No            pic 9(7).    *> value zero.
     03  Pay-Hdr-Interval      pic 9.
     03  Pay-Hdr-Last-Apply-No pic 9(4)    comp.
     03  Pay-Hdr-Journal-Pnt   pic 9(4)    comp.
     03  Pay-Hdr-Last-Day-of-Last-Per
                               pic 9(8)    comp.  *> ccyymmdd
     03  FILLER                pic x(12).

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
*>
 01  PY-Chk-Record.
     03  Chk-Emp-No        pic 9(7).
     03  Chk-Check-No      pic 9(6)     comp.
     03  Chk-Amt           pic 9(5)v99  comp-3  occurs 16.
*>
 01  PY-Chk-Hdr-Record.
     03  Chk-Hdr-No               pic 9(7).   *> value zero
     03  Chk-hdr-Interval         pic x.
     03  Chk-hdr-Apply-No         pic 9(4)    comp.
     03  Chk-hdr-Slow-From-Date   pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-Fast-From-Date   pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-To-Date          pic 9(8)    comp.  *> ccyymmdd
     03  Chk-hdr-Register-Printed pic x.
     03  Chk-hdr-Checks-Printed   pic x.
*> 24 ?
     03  FILLER                   pic x(52).
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
*>C  copy "fdpycalx.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY California File  *
*>                                          *
*>                                          *
*>*******************************************
*>   Record Size 116 Bytes
*>   see wspycalx.cob for later updates
*>
 fd  PY-California-Tax-File.
*>
*>C  copy "wspycalx.cob".
*>*******************************************
*>                                          *
*>  Record-Definition For California File   *
*>                                          *
*>     Sequential file                      *
*>*******************************************
*>  File size 116 bytes.
*>
*> THESE FIELDs DEFINITIONS WILL NEED CHANGING
*>
*> 30/10/25 vbc - Created-
*>
 01  PY-California-Tax-Record.
     03  PY-Calx-Cal-Estimated-Ded-Amt  pic s9(5)v99   comp-3.
     03  PY-Calx-Cal-Low-Income-Exempt  pic s9(5)v99   comp-3   occurs 4.
     03  PY-Calx-Cal-Standard-Deduction pic s9(5)v99   comp-3   occurs 4.
     03  PY-Calx-Cal-Tax-Credits                       comp-3   occurs 10.
         05  PY-Calx-Cal-Tax-Credit     pic s9(5)v99            occurs 2.
*>
*>
*>
*> next 3 are all the same so can use only one stax
*>
*>C  copy "fdpystax.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY State Tax File   *
*>                                          *
*>     Covers pyswt (ss), pylwt & pycal(s)  *
*>   ss=state code, s = m,s or H            *
*>  s = Single, M=Married, Head of house    *
*>                                          *
*>   file-54        file-49,50 or 51        *
*>                                          *
*>   Must decide how to deal with this, ie  *
*>   Only one state so ss not needed pycal  *
*>   cal (m,s,h  w neeed for weekly ?       *
*>  And pytax = for UK tax table maybe      *
*>                                          *
*>*******************************************
*>   Record Size 608 Bytes
*>   see wspystax.cob for later updates
*>
 fd  PY-State-Tax-File.   *> Covers for all state tables assuming only one
*>                           is ever in use at any one time for one business.
*>
*>C  copy "wspystax.cob".
*>*******************************************
*>                                          *
*> 3 tables LWT, SWT, stax should be using  *
*>    just the one table as all are present *
*>                                          *
*>  Record-Definition For State Tax File    *
*>                                          *
*>  agency% is 1 if SWT                     *
*>         and 2 if LWT                     *
*>             3 if CAL Single              *
*>             4 if CAL Married             *
*>             5 if CAL Head                *
*>  num.entries refers to the number of     *
*>  entries in withholding table NEEDED ?   *
*>                                          *
*>     Sequential file                      *
*>*******************************************
*>  File size 608 bytes.
*>
*> THESE FIELDs DEFINITIONS WILL NEED CHANGING
*>
*> 30/10/2025 vbc - Created-
*>
 01  PY-State-Tax-Record.
     03  PY-Stax-Withhold-Deduction-Amount  pic 9(6)      comp.               *> (agency)
     03  PY-Stax-Withhold-Num-Entries       pic 9(6)      comp.               *> %(agency) NEEDED ?
     03  PY-Stax-Agency                                   comp-3  occurs 5.
         05  PY-Stax-Withhold-Cutoff        pic s9(5)v99          occurs 15.  *> (,agency)
         05  PY-Stax-Withhold-Percent       pic s9(5)v99          occurs 15.  *> (,agency)
*>
*>
*>C  copy "fdpyswt.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY SWT File         *
*>                                          *
*>                                          *
*>*******************************************
*>   Record Size 608 Bytes
*>   see wspyswt.cob for later updates
*>
 fd  PY-SWT-Tax-File.
*>
*>C  copy "wspyswt.cob".
*>*******************************************
*>                                          *
*> 3 tables LWT, SWT, stax should be using  *
*>    just the one table as all are present *
*>                                          *
*>  Record-Definition For SWT Tax File      *
*>                                          *
*>  agency% is 1 if SWT                     *
*>         and 2 if LWT                     *
*>             3 if CAL Single              *
*>             4 if CAL Married             *
*>             5 if CAL Head                *
*>  num.entries refers to the number of     *
*>  entries in withholding table  NEEDED ?  *
*>                                          *
*>     Sequential file                      *
*>*******************************************
*>  File size 608 bytes.
*>
*> THESE FIELDs DEFINITIONS WILL NEED CHANGING
*>
*> 30/10/25 vbc - Created.
*>
 01  PY-SWT-Tax-Record.
     03  PY-SWT-Withhold-Deduction-Amount   pic 9(6)      comp.               *> (agency)
     03  PY-SWT-Withhold-Num-Entries        pic 9(6)      comp.               *> %(agency) NEEDED ?
     03  PY-SWT-Agency                                    comp-3  occurs 5.
         05  PY-SWT-Withhold-Cutoff         pic s9(5)v99          occurs 15.  *> (,agency)
         05  PY-SWT-Withhold-Percent        pic s9(5)v99          occurs 15.  *> (,agency)
*>
*>
*>C  copy "fdpylwt.cob".
*>*******************************************
*>                                          *
*>  File Definition For PY LWT File         *
*>                                          *
*>                                          *
*>*******************************************
*>   Record Size 608 Bytes
*>   see wspylwt.cob for later updates
*>
 fd  PY-LWT-Tax-File.
*>
*>C  copy "wspylwt.cob".
*>*******************************************
*>                                          *
*> 3 tables LWT, SWT, stax should be using  *
*>    just the one table as all are present *
*>                                          *
*>  Record-Definition For LWT Tax File      *
*>                                          *
*>  agency% is 1 if SWT                     *
*>         and 2 if LWT                     *
*>             3 if CAL Single              *
*>             4 if CAL Married             *
*>             5 if CAL Head                *
*>  num.entries refers to the number of     *
*>  entries in withholding table NEEDED ?   *
*>                                          *
*>     Sequential file                      *
*>*******************************************
*>  File size 608 bytes.
*>
*> THESE FIELDs DEFINITIONS WILL NEED CHANGING
*>
*> 30/10/25 vbc - Created.
*>
 01  PY-LWT-Tax-Record.
     03  PY-LWT-Withhold-Deduction-Amount   pic 9(6)      comp.               *> (agency)
     03  PY-LWT-Withhold-Num-Entries        pic 9(6)      comp.               *> %(agency) IS THIS NEEDED ?
     03  PY-LWT-Agency                                    comp-3  occurs 5.
         05  PY-LWT-Withhold-Cutoff         pic s9(5)v99          occurs 15.  *> (,agency)
         05  PY-LWT-Withhold-Percent        pic s9(5)v99          occurs 15.  *> (,agency)
*>
*>
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(15) value "PY900 (1.0.08)".  *> First release pre testing.
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
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.   *> Call blk at ZZ910-ACAS-Calls
     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
 *>    03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
     03  WS-Stock-Record        pic x.
     03  WS-Sales-Record        pic x.
     03  WS-Value-Record        pic x.
     03  WS-Delivery-Record     pic x.
     03  WS-Analysis-Record     pic x.
     03  WS-Del-Inv-Nos-Record  pic x.
     03  WS-Purch-Record        pic x.
     03  WS-Pay-Record          pic x.
     03  WS-Invoice-Record      pic x.
     03  WS-OTM3-Record         pic x.
     03  WS-PInvoice-Record     pic x.
     03  WS-OTM5-Record         pic x.
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at ab000-ACAS-IRS-Calls via ZZ100
     03  WS-IRS-Default-Record pic x.
     03  Posting-Record        pic x.
*>
 01  WS-Data.
     03  Menu-Reply          pic x.
     03  PY-PR1-Status       pic xx       value zero.
     03  PY-Ded-Status       pic xx       value zero.
     03  PY-Hrs-Status       pic xx       value zero.
     03  PY-Emp-Status       pic xx       value zero.
     03  PY-His-Emp-Status   pic xx       value zero.
     03  PY-Act-Status       pic xx.
     03  PY-Pay-Status       pic xx.
     03  PY-Chk-Status       pic xx.
     03  PY-Coh-Status       pic xx.
     03  PY-Stax-Status      pic xx.
     03  PY-Calx-Status      pic xx.
     03  PY-SWT-Status       pic xx.
     03  PY-LWT-Status       pic xx.
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
*>
     03  WS-Heading          pic x(40)    value "Payroll". *> for zz020-Headings
*>
     03  WS-Active-Currency  pic x.                  *> NOT YET USED
*> Taken from https://currencycalculate.com/list-of-currency-symbols
*>    There are many more that need UTF-8 etc.
*>
         88  WS-Euro                      value "¤".
         88  WS-Pound                     value "£".
         88  WS-Dollar                    value "$".
*>
*> The following for GC and screen with *nix NOT tested with Windows
*>
 01  wScreenName             pic x(256).
 01  wInt                    binary-long.
*>
 01  WS-Defaults.     *> From Cbasic dedant   Used in DED processing
*>                       : <<<<<<<<<<<< taken from ACT records
*>
     03  WS-Dflt-Cash        binary-char unsigned   value 1.  *> via PY-PR1-Offset-Cash-Acct  CB is 011100 Cash
     03  WS-Dflt-Liability   binary-char unsigned   value 2.  *> CB is 121100 Accrued Liability
     03  WS-Dflt-Expense     binary-char unsigned   value 3.  *> CB is 411100 Salary Expense
*>                                                                 Content from PY-PR1-Dflt-Dist-Acct after set up.
     03  WS-Dflt-Cost        binary-char unsigned   value 4.  *> CB is 131100 Accrued Payroll Costs Liability
*>
*>  Temp vars used with ACCEPT_NUMERIC C routine
*>
 01  WS-Temp-Numbers.
     03  WS-Temp-Rate        pic 99.99.
 *>    03  WS-Temp-Percent     pic 99.99.  *>  NOT YET USED
     03  WS-Temp-Limit       pic 99999.99.
     03  WS-Temp-Factor      pic 99999.99.
     03  WS-Temp-Act-No      pic 99.
     03  WS-Temp-Used        pic x.
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
 01  WS-Account-Table             value spaces.
     03  WS-Act-Exists       pic x   occurs 99.
*> Next one MUST be same size as the WS-Act-Exist occurs value.
 01  WS-Account-Table-Size   pic 99  value 99.
 01  WS-Account-Count        pic 99  value zero.  *> Entries in use
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
 01  Error-Messages.
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY002           pic x(31) value "SY002 Note error and hit Return".
     03  SY003           pic x(51) value "SY003 Aborting function - Note error and hit Return".
*>     03  SY004           pic x(20) value "SY004 Now Hit Return".
     03  SY005           pic x(18) value "SY005 Invalid Date".
     03  SY008           pic x(32) value "SY008 Note message & Hit Return ".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
*>     03  SY011           pic x(47) value "SY011 Error on systemMT processing, FS-Reply = ".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
     03  SY014           pic x(30) value "SY014 Press return to continue".
*>
*> Module General ?
*>
     03  PY001           pic x(36) value "PY001 Re/Write PARAM record Error = ".
     03  PY002           pic x(32) value "PY002 Read PARAM record Error = ".
     03  PY003           pic x(39) value "PY003 See manual for NL accounts needed".
     03  PY004           pic x(29) value "PY004 To quit, use ESCape key".
     03  PY005           pic x(40) value "PY005 F1 for display of current accounts".
     03  PY006           pic x(40) value "PY006 No records to show, return to quit".
     03  PY007           pic x(45) value "PY007 No more records to show, return to quit".
     03  PY008           pic x(31) value "PY008 Write DED record Error = ".
     03  PY009           pic x(30) value "PY009 Read DED record Error = ".
     03  PY010           pic x(33) value "PY008 Rewrite DED record Error = ".
*>
*> Module specific
*>
*>     03  PY101           pic x(31) value "PY101 Invalid option, try again".
*>     03  PY102           pic x(36) value "PY102 Bad Parameter Data - Try again".
     03  PY103           pic x(29) value "PY103 Bad value for Debugging".
     03  PY104           pic x(32) value "PY104 Bad value for Pay Interval".
     03  PY105           pic x(31) value "PY105 Bad value for Date Format".
     03  PY106           pic x(33) value "PY106 Bad value Qtr - Range 1 - 4".
     03  PY107           pic x(37) value "PY107 Bad value Lines - Range 40 - 89".
     03  PY108           pic x(38) value "PY108 Bad Exclusion code - Range 1 - 4".
     03  PY109           pic x(38) value "PY109 Bad Pay Interval - not = S,M,B,W".
     03  PY110           pic x(27) value "PY110 Pay Type not = H or S".
     03  PY111           pic x(28) value "PY111 GL Iface not = Y,N,I,B".
     03  PY112           pic x(33) value "PY112 Check printing not = Y or N".
     03  PY113           pic x(28) value "PY113 Void checks not Y or N".
*>     03  PY114           pic x(35) value "PY114 IRS not set to use, in Params".
     03  PY115           pic x(52) value "PY115 E/D Must be D or E : E = Earning D = Deduction". *> old PY358
     03  PY116           pic x(36) value "PY116 IRS Nominal # not found, Retry".
     03  PY117           pic x(28) value "PY117 Account does not exist".
     03  PY118           pic x(38) value "PY118 Account re/write failed - Status".
     03  PY119           pic x(20) value "PY119 Must be Y or N".
*>     03  PY120           pic x(44) value "PY120 Cannot open Accounts File, aborting : ".
     03  PY121           pic x(79) value "PY121 A/P must be A or P : A = flat Amount. P = Percentage of Gross Taxable pay". *> old PY359
     03  PY122           pic x(59) value "PY122 Chk Cat Must be 2-7 for Earnings, 9-16 for Deductions".  *> old PY360
     03  PY123           pic x(55) value "PY123 FWT Cutoffs & Percents Must be in Ascending order".      *> old PY356
     03  PY124           pic x(45) value "PY124 Account does not exist in Account Table".
     03  PY125           pic x(33) value "PY125 Cannot find that State code".
     03  PY126           pic x(28) value "PY126 Hard Delete not N or Y".
*>
*>  Support for IRS FH acasirsub1
*>
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, FS-Reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, FS-Reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, FS-Reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, FS-Reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, FS-Reply = ".
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

*>  ACAS for IRS FH support CoA Ledgers
*>C  copy "irswsnl.cob" replacing NL-Record by WS-IRSNL-Record.
*>*******************************************
*>                                          *
*>  Working Storage for the Nominal Ledger  *
*>                                          *
*>*******************************************
*> Chgd 16/01/09 money to 99M
*>
 01
 WS-IRSNL-Record.
     03  NL-Key.
         05  NL-Owning      pic 9(5).
         05  NL-Sub-Nominal pic 9(5).
     03  NL-Type            pic x.
         88  Owner                   value is "O".
         88  Sub                     value is "S".
     03  NL-Data.
         05  NL-Name        pic x(24).
         05  NL-DR          pic 9(8)v99   comp.
         05  NL-CR          pic 9(8)v99   comp.
         05  NL-DR-Last     pic 9(8)v99   comp  occurs  4.
         05  NL-CR-Last     pic 9(8)v99   comp  occurs  4.
         05  NL-AC          pic x.
     03  filler  redefines  NL-Data.
         05  NL-Pointer     pic 9(5).
*>
*>>W Msg29 Caution: One or more replacing sources not found
*> ACAS for  GL FH  support CoA Ledgers
*>C  copy "wsledger.cob".
*>*******************************************
*>                                          *
*>    WS definition for the General/Nominal *
*>             Ledger file                  *
*>                                          *
*>*******************************************
*> 27/01/09 vbc - file-id to select
*> 04/01/17 vbc - Taken from fdledger.
*> 07/01/17 vbc - Added new field ledger-key9.
*> 31/01/18 vbc - Resized to 126 bytes.
*>
 01  WS-Ledger-Record.
     03  WS-Ledger-Key.
         05  WS-Ledger-Nos    pic 9(6).
*>*******************************************
         05  filler  redefines  WS-Ledger-Nos.
             07  Ledger-n  pic 9(4).
             07  Ledger-s  pic 9(2).
*>*******************************************
         05  Ledger-PC     pic 9(2).
     03  WS-Ledger-Key9 redefines WS-Ledger-Key
                           pic 9(8).
     03  Ledger-Type       pic 9.
     03  Ledger-Place      pic x.
     03  Ledger-Level      pic 9.
     03  filler            pic x(5).
     03  Ledger-Name       pic x(24).
     03  Ledger-Balance    pic s9(8)v99   comp-3.
     03  Ledger-Last       pic s9(8)v99   comp-3.
     03  Quarters.
         05  Ledger-Q1     pic s9(8)v99   comp-3.
         05  Ledger-Q2     pic s9(8)v99   comp-3.
         05  Ledger-Q3     pic s9(8)v99   comp-3.
         05  Ledger-Q4     pic s9(8)v99   comp-3.
     03  filler redefines Quarters.
         05  Ledger-Q      pic s9(8)v99   comp-3   occurs  4.
     03  filler            pic x(50).
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
 01  Display-Heads                background-color cob-color-black
                                  foreground-color 3
                                  erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2.
     03  value "Payroll Parameter Set Up"    col 29.
     03  from  U-Date     pic x(10)          col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
*>
 *>    03  value "Copyright (c) 2025-" line 24 col  1 foreground-color 3.
 *>    03  from  wse-year              line 24 col 20 foreground-color 3.
 *>    03  value "Applewood Computers" line 24 col 25 foreground-color 3.
 *>    03  from maps-ser-xx            line 24 col 74 foreground-color 3. *> mp or MP
 *>    03  from curs2                  line 24 col 76 foreground-color 3. *> = 9999 - O/S version
*>
 01  SS-Param-Menu-1    background-color cob-color-black
                        foreground-color cob-color-green
                        erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2.
     03  value "Payroll Parameter Set Up"    col 29.
     03  from  U-Date     pic x(10)          col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
     03  value "1. Company ID and General Parameters"
                                     line  5 col  21 erase eos.
     03  value "2. Pay Intervals and Default Employee Payroll Data"
                                     line  6 col  21.
     03  value "3. Payroll System Configuration and GL Interface"
                                     line  7 col  21.
     03  value "N. Next - System Wide Deduction Menu. etc"
                                     line  9 col  21.
     03  value "X or Esc to quit menu option"
                                     line 11 col  21.
     03  value "Select Option  [ ]"
                                     line 13 col 30.
     03  using Menu-Reply    pic x           col 46 foreground-color 3.
*>
*>
 01  SS-Param-Menu-2    background-color cob-color-black
                        foreground-color cob-color-green
                        erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2 erase eos.
     03  value "Payroll Parameter Set Up"    col 29.
     03  from  U-Date     pic x(10)          col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
     03  value "            System Wide Deduction Menu"
                                     line  5 col  1 erase eos.
     03  value "1. Standard Deduction Rates"
                                     line  7 col 21.
     03  value "2. Federal Withholding Tax Table Entry"
                                     line  8 col 21.
     03  value "3. System Earning and Deduction Information"
                                     line  9 col 21.
     03  value "X or Esc to quit menu option"
                                     line 10 col 21.
     03  value "Select Option  [ ]"  line 13 col 21.
     03  using Menu-Reply    pic x           col 37 foreground-color 3.
*>
*>   NEW MENUS Here
*>
 *> 01  SS-Param-Menu-3    background-color cob-color-black   *> Assumes Heading already done
 *>                        foreground-color cob-color-green.


*>
*> Param data entry screens  AN is used so these are displayed only
*>
 01  SS-Param-1-Company-Details-1 background-color cob-color-black
                                  foreground-color cob-color-green
                                  erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2.
     03  value "Payroll Parameter Set Up"    col 29.
     03  from  U-Date     pic x(10)          col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
     03  value "---------------------------------------------------------------------------"
                                     line  5 col  1  erase eos.
     03  value "Pay Interval Used(S,M,W,B)  If more than one, Select menu screen 2      [ ]"
                                     line  6 col  1.
     03  value "Date Form (2=MM/DD/CCYY, 1=DD/MM/CCYY)  [ ]"
                                     line  7 col  1.
     03  value "Last Quarter Ended    [ ]"   col 51.
     03  value "Ending Day of Last Pay Period  [          ]       Current Year       [    ]"
                                     line  8 col 1.
     03  value "---------------------------------------------------------------------------"
                                     line  9 col  1.
     03  value "Company Trading Name [                                ]"
                                     line 10 col  1.
     03  value "Name (Full)  ["      line 11 col  1.
     03  value "]"                           col 75.
     03  value "Address 1 ["         line 12 col  1.
     03  value "]"                           col 44.
     03  value "Address 2 ["         line 13 col  1.
     03  value "] State ["                   col 44.
     03  value "]    Zip ["                  col 55.
     03  value "]"                           col 75.
     03  value "Address 3 ["         line 14 col  1.
     03  value "] Phone           ["         col 44.
     03  value "]"                           col 75.
     03  value "Address 4 ["         line 15 col  1.
     03  value "]"                           col 44.
     03  value "Email     ["         line 16 col  1.
     03  value "]"                           col 42.
     03  value "Govt Id        Federal                State                Local"
                                     line 17 col  1.
     03  value "Numbers   ["         line 18 col  1.
     03  value "]     ["                     col 27.
     03  value "]    ["                      col 49.
     03  value "]"                           col 70.
     03  value "IRS ID    [                        ]"
                                     line 19 col  1.
     03  value "---------------------------------------------------------------------------"
                                     line 20 col  1.
     03  value "Lines Per PageP ["   line 21 col  1.  *> chg 07/12/25 (data 18)
*>     03  value "]    Debugging Aid ["      col 20.
     03  value "]  Lines per PageL ["        col 20.  *> data cc40
     03  value "]    Debugging Aid ["        col 42.  *> data cc62
     03  value "] {N or Y} Hard Rec Delete ["
                                             col 44.
     03  value "] Y/N"                       col 75.
     03  value "Cols per Page - L [" line 22 col  1.  *> data cc20
     03  value "]  Cols Per Page - P ["      col 22.  *> data cc44
     03  value "]"                           col 46.

 *>    03  using PY-PR1-Dflt-Pay-Interval pic x line 05 col 74 foreground-color 3.
 *>    03  using PY-PR1-Date-Format   pic 9     line 06 col 42 foreground-color 3.
 *>    03  using PY-PR2-Last-Q-Ended  pic 9     line 07 col 74 foreground-color 3.
 *>    03  using WS-Date              pic x(10) line 08 col 33 foreground-color 3.
 *>    03  using PY-PR2-Year          pic 9(4)  line 08 col 71 foreground-color 3.
 *>    03  using PY-PR1-Trade-Name pic x(32)    line 10 col 23 foreground-color 3.
 *>    03  using PY-PR1-Co-Name pic x(60)       line 11 col 15 foreground-color 3.
 *>    03  using PY-PR1-Co-Address-1 pic x(32)  line 12 col 12 foreground-color 3.
 *>    03  using PY-PR1-Co-Address-2 pic x(32)  line 13 col 12 foreground-color 3.
 *>    03  using PY-PR1-Co-State     pic xx     line 13 col 53 foreground-color 3.
 *>    03  using PY-PR1-Co-Zip       pic x(10)  line 13 col 65 foreground-color 3.
 *>    03  using PY-PR1-Co-Address-3 pic x(32)  line 14 col 12 foreground-color 3.
 *>    03  using PY-PR1-Co-Phone     pic x(12)  line 14 col 63 foreground-color 3.
 *>    03  using PY-PR1-Co-Address-4 pic x(32)  line 15 col 12 foreground-color 3.
 *>    03  using PY-PR1-Co-Email pic x(30)      line 16 col 12 foreground-color 3.
 *>    03  using PY-PR1-Fed-ID   pic x(15)      line 18 col 12 foreground-color 3.
 *>    03  using PY-PR1-State-ID pic x(15)      line 18 col 34 foreground-color 3.
 *>    03  using PY-PR1-Local-ID pic x(15)      line 18 col 55 foreground-color 3.
 *>    03  using PY-PR1-Tax-ID   pic x(24)      line 19 col 12 foreground-color 3.
 *>    03  using PY-PR1-Page-Lines-L pic 99     line 21 col 18 foreground-color 3.
 *>    03  using PY-PR1-Page-Lines-P pic 99     line 21 col 40 foreground-color 3.
 *>    03  using PY-PR1-Debugging  pic x        line 21 col 62 foreground-color 3.
 *>    03  using PY-PR1-Hard-Delete             line 21 col 74.
 *>    03  using PY-PR1-Page-Width-L pic 99     line 22 col 20 foreground-color 3.
 *>    03  using PY-PR1-Page-Width-P pic 99     line 22 col 44 foreground-color 3.
*>
*> For param-2 use individual accepts etc.
*>
 01  SS-Param-2-Pay-Interval-Details  background-color cob-color-black
                                      foreground-color cob-color-green
                                      erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2.
     03  value "Parameter Entry 2 - Pay Periods" col 29.
     03  from  U-Date     pic 99/99/9999         col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
     03  value "    +-------------------------------------------------------------------+"
                                     line  5 col  1 erase eos.
     03  value "    |                        Pay  Interval  Usage                       |"
                                     line  6 col  1.
     03  value "    | Monthly      ["
                                     line  7 col  1.
 *>    03  using PY-PR1-M-Used  pic x          col 21 foreground-color 3.
     03  value "] End of Last Monthly Pay Period      ["
                                             col 22.
 *>    03  using PY-PR2-Last-Day-Last-M
 *>                             pic 99/99/9999 col 61 foreground-color 3. *>  but stored as ccyymmdd
     03  value "] |"                         col 71.
     03  value "    | Semi Monthly ["
                                     line  8 col  1.
 *>    03  using PY-PR1-S-Used  pic x  line  8 col 21 foreground-color 3.
     03  value "] End of Last Semi-Monthly Pay Period ["
                                             col 22.
 *>    03  using PY-PR2-Last-Day-Last-S pic 99/99/9999 line 08 col 61 foreground-color 3. *>  but stored as ccyymmdd
     03  value "] |"                         col 71.
     03  value "    | Biweekly     ["
                                     line  9 col  1.
 *>    03  using PY-PR1-B-Used  pic x     line 09 col 21 foreground-color 3.
     03  value "] End of Last Biweekly Pay Period     ["
                                             col 22.
 *>    03  using PY-PR2-Last-Day-Last-B pic 99/99/9999 line  9 col 61 foreground-color 3. *>  but stored as ccyymmdd
     03  value "] |"                         col 71.
     03  value "    | Weekly       ["
                                     line 10 col  1.
 *>    03  using PY-PR1-W-Used  pic x  line 10 col 21 foreground-color 3.
     03  value "] End of Last Weekly Pay Period       ["
                                             col 22.
 *>    03  using PY-PR2-Last-Day-Last-W pic 99/99/9999 col 61 foreground-color 3.  *> but stored as ccyymmdd
     03  value "] |"                   line 10 col 71.
     03  value "    +-------------------------------------------------------------------+"
                                     line 11 col  1.
     03  value "                     Default Employee  Values"
                                     line 12 col  1.
     03  value "-- Rate Name  -----------  Default  ------  Description  ---------"
                                     line 13 col  1.
     03  value " Vacation           Rate    [        ] (Units Earned per Pay Period)"
                                     line 14 col  1.
 *>    03  using PY-PR1-Dflt-Vac-Rate pic 9(5).99 line 14 col 30 foreground-color 3.  *> Cyan
     03  value " Sick Leave         Rate    [        ] (Units Earned per Pay Period)"
                                     line 15 col  1.
 *>    03  using PY-PR1-Dflt-SL-Rate  pic 9(5).99 line 15 col 30 foreground-color 3.
     03  value "1 [               ] Rate    [        ] (Dollars per Unit)"
                                     line 16 col  1.
 *>    03  using PY-PR1-Rate-Name (1) pic x(15) line 16 col  4 foreground-color 3. *> Regular
 *>    03  using PY-PR1-Dflt-Pay-Rate pic 9(5).99 line 16 col 30 foreground-color 3.
     03  value "2 [               ] Factor  [        ] (Rate 1 * Factor = Default Rate 2)"
                                     line 17 col  1.
 *>    03  using PY-PR1-Rate-Name (2) pic x(15) line 17 col  4 foreground-color 3. *> Overtime
 *>    03  using PY-PR1-Rate2-Factor  pic 9(5).99 line 17 col 30 foreground-color 3.
     03  value "3 [               ] Factor  [        ] (Rate 1 * Factor = Default Rate 3)"
                                     line 18 col  1.
 *>    03  using PY-PR1-Rate-Name (3) pic x(15) line 18 col  4 foreground-color 3. *> Spec. Overtime
 *>    03  using PY-PR1-Rate3-Factor  pic 9(5).99 line 18 col 30 foreground-color 3.
     03  value "4 [               ] Exclusion Type [ ] (Rate 4 can be Exempted from Taxes)"
                                     line 19 col  1.
 *>    03  using PY-PR1-Rate-Name (4) pic x(15) line 19 col  4 foreground-color 3. *> Commission
 *>    03  using PY-PR1-Rate4-Exclusion-Type pic 9 line 19 col 37 foreground-color 3.
     03  value "--------------------------------------------------------------------------"
                                     line 20 col  1.
     03  value " Default Pay Interval (any used Interval) [ ]  Max Pay Factor [        ]"
                                     line 21 col  1.
 *>    03  using PY-PR1-Dflt-Pay-Interval pic x line 21 col 43 foreground-color 3.
 *>    03  using PY-PR1-Max-Pay-Factor pic 9(5).99 line 21 col 64 foreground-color 3.
     03  value " Default Pay Type (H=Hourly, S=Salaried)  [ ]  Normal Units   [        ]"
                                     line 22 col 1.
 *>    03  using PY-PR1-Dflt-HS-Type   pic x line 22 col 43 foreground-color 3.
 *>    03  using PY-PR1-Dflt-Norm-Units pic 9(5).99 line 22 col 64 foreground-color 3.
*>
*> For param-3 use individual accepts etc.
*>
 01  SS-Param-3-GL-Details   background-color cob-color-black
                             foreground-color cob-color-green
                             erase eos.
     03  from  Prog-Name  pic x(15)      line  1 col  1 foreground-color 2.
     03  value "Parameter Entry 2 - GL"          col 29.
     03  from  U-Date     pic x(10)              col 71 foreground-color 2.
     03  from  Usera      pic x(32)      line  3 col  1.
     03  value "           General Ledger          |          Check Writing"              line  5 col  1   erase eos.
     03  value " GL Interface Used (Y,N,I,B)   [ ] | Computer Check Print (Y or N) [ ]"   line  6 col  1.
 *>    03  using PY-PR1-GL-Used              pic x                   line 6 col 33 foreground-color 3.
 *>    03  using PY-PR1-Check-Printing-Used  pic x                   line 6 col 69 foreground-color 3.
     03  value " Void Checks over Max (Y or N) [ ] | Maximum Amount     [99999.99]   |"   line  7 col  1.
 *>    03  using PY-PR1-Void-Checks-Over-Max pic x                   line 7 col 33 foreground-color 3.
 *>    03  using PY-PR1-Void-Check-Amt       pic 9(5).99             line 7 col 58 foreground-color 3.
     03  value " --------------------------------------------------------------------+"   line  8 col  1.
     03  value " |                       Payroll System Accounts                     |"   line  9 col  1.  *> Pg 41 - 43
     03  value " | Offset Cash  Account  [  ]      |  Default Dist Account   [  ]    |"   line 10 col  1.  *> pg 97/8
 *>    03  using PY-PR1-Offset-Cash-Acct  pic 99                     line 10 col 27 foreground-color 3.
 *>    03  using PY-PR1-Dflt-Dist-Acct    pic 99                     line 10 col 63 foreground-color 3.
 *> New one as can't find it being asked for.  PY-PR1-Dflt-Gross-Acct
     03  value " |                                 |  Default Gross Account  [  ]    |"   line 11 col  1.
 *>    03  using PY-PR1-Dflt-Gross-Acct   pic 99                     line 11 col 63 foreground-color 3.
     03  value " +-------------------------------------------------------------------+"   line 12 col  1.
     03  value " |  Note that IRS uses 5 and GL uses 6 digits} for nominal accounts  |"   line 13 col  1.
     03  value " +-------------------------------------------------------------------+"   line 14 col  1.
     03  value " | Distribute Employee Cost To  1-5 Gl Accounts (Y Or N)  [ ]        |"   line 15 col  1.
 *>    03  using PY-PR1-Dist-Used         pic x                      line 15 col 60 foreground-color 3.
     03  value " | (If N, One Account can be Entered per Employee)                   |"   line 16 col  1.
     03  value " +-------------------------------------------------------------------+"   line 17 col  1.
*>
*> DONE 09/11/25
*>
 01  SS-Param-4-Standard-Deduction-Rates background-color cob-color-black
                                         foreground-color cob-color-green
                                         erase eos.
     03  from  Prog-Name  pic x(15)                         line  1 col  1 foreground-color 2.
     03  value "Parameter Entry 2 - Rates"                          col 29.
     03  from  U-Date     pic x(10)                                 col 71 foreground-color 2.
     03  from  Usera      pic x(32)                         line  3 col  1.
     03  value "         Standard Deduction Rates"          line  4 col 15   erase eos.
     03  value "               Acct"                        line  6 col 15.
     03  value "        Used    No      Rate     Limit"     line  7 col 15.
     03  value "FWT:     [ ]   [  ]   "                     line  8 col 15.
     03  value "SWT:     [ ]   [  ]   "                     line  9 col 15.
     03  value "LWT:     [ ]   [  ]   "                     line 10 col 15.
     03  value "FICA:    [ ]   [  ]    [     ] [        ]"  line 11 col 15.
     03  value "Co FICA: [ ]   [  ]    [     ] [        ]"  line 12 col 15.
     03  value "SDI:     [ ]   [  ]    [     ] [        ]"  line 13 col 15.
     03  value "Co FUTA: [ ]   [  ]    [     ] [        ]"  line 14 col 15.
     03  value "FUTA Max State Credit: [     ]"             line 15 col 15.
     03  value "Co SUI:  [ ]   [  ]    [     ] [        ]"  line 16 col 15.
     03  value "EIC:     [ ]   [  ]    [     ] [        ]"  line 17 col 15.
     03  value "EIC Excess:            [     ] [        ]"  line 18 col 15.
*>
*> Done 09/11/25
*>
 01  SS-Param-5-Federal-Withholding-Tax-Table-Entry
                                       background-color cob-color-black
                                       foreground-color cob-color-green
                                       erase eos.
     03  from  Prog-Name  pic x(15)                         line  1 col  1 foreground-color 2.
     03  value "Parameter Entry 2 - Allowances"                     col 29.
     03  from  U-Date     pic x(10)                                 col 71 foreground-color 2.
     03  from  Usera      pic x(32)                         line  3 col  1.
     03  value "           Allowance Amount:  [        ]"        line 06 col 12.
     03  value "       M A R R I E D            S I N G L E"     line 08 col 12.
     03  value "    Wages Over  Percent     Wages Over  Percent" line 09 col 12.
     03  value "1.  [        ]  [     ]     [        ]  [     ]" line 10 col 12.
     03  value "2.  [        ]  [     ]     [        ]  [     ]" line 11 col 12.
     03  value "3.  [        ]  [     ]     [        ]  [     ]" line 12 col 12.
     03  value "4.  [        ]  [     ]     [        ]  [     ]" line 13 col 12.
     03  value "5.  [        ]  [     ]     [        ]  [     ]" line 14 col 12.
     03  value "6.  [        ]  [     ]     [        ]  [     ]" line 15 col 12.
     03  value "7.  [        ]  [     ]     [        ]  [     ]" line 16 col 12.
     03  value "    (Use Annual tables from IRS Circular 'E' only!)"  line 18 col 12.
*>
*> Working on it 9/11/25
*>
 01  SS-Param-6-System-Earning-and-Deduction-Information
                                       background-color cob-color-black
                                       foreground-color cob-color-green
                                       erase eos.
     03  from  Prog-Name  pic x(15)                                    line  1 col  1 foreground-color 2.
     03  value "Parameter Entry 2 - E/D Rates"                                 col 29.
     03  from  U-Date     pic x(10)                                            col 71 foreground-color 2.
     03  from  Usera      pic x(32)                                    line  3 col  1.
     03  value " Used  Earn/Ded Desc   E/D Acct. A/P  Factor   Limited  Limit      XLCD Cat"
                                                                       line  5 col 1.
     03  value " 1[ ][               ] [ ] [  ]  [ ] [        ]  [ ]   [        ]   [ ][  ]"
                                                                       line  6 col 1.
     03  value " 2[ ][               ] [ ] [  ]  [ ] [        ]  [ ]   [        ]   [ ][  ]"
                                                                       line  7 col 1.
     03  value " 3[ ][               ] [ ] [  ]  [ ] [        ]  [ ]   [        ]   [ ][  ]"
                                                                       line  8 col 1.
     03  value " 4[ ][               ] [ ] [  ]  [ ] [        ]  [ ]   [        ]   [ ][  ]"
                                                                       line  9 col 1.
     03  value " 5[ ][               ] [ ] [  ]  [ ] [        ]  [ ]   [        ]   [ ][  ]"
                                                                       line 10 col 1.
     03  value "Use Escape to finish data entry on field - Used"       line 22 col 5
                                                    foreground-color 3.
*>
*> Done 08/11/25
*>
 01  SS-Param-7-IRS-Nominal-Accounts   background-color cob-color-black
                                       foreground-color cob-color-green
                                       erase eos.
     03  from  Prog-Name  pic x(15)                                    line  1 col  1 foreground-color 2.
     03  value "Parameter Entry 2 - Accounts"                                  col 29.
     03  from  U-Date     pic x(10)                                            col 71 foreground-color 2.
     03  from  Usera      pic x(32)                                    line  3 col  1.
     03  value "    Account Entry"                                     line  4 col 29 erase eol.
     03  value "Record No      [  ] *"                                 Line  6 col  7.
     03  using Act-No    pic 99                                        line  6 col 23 foreground-color 3.
     03  value "Account Number:[      ] **"                            line  8 col  7.
     03  using Act-GL-No pic 9(6)                                      line  8 col 23 foreground-color 3.
     03  value "Account Name:  {                                 }"    line  9 col  7.
     03  using Act-Desc  pic x(24)                                     line  9 col 23 foreground-color 2.
     03  value "* Escape or zeros to quit Entry"                       line 11 col  1 foreground-color 6.
     03  value "** Is taken from the IRS accounts and HAS to have been set up already"
                                                                       line 13 col  1 foreground-color 6.
*>
*> Done 08/11/25
*>
 01  SS-Param-7-IRS-Show-Nominal-Accounts   background-color cob-color-black
                                            foreground-color cob-color-green
                                            erase eos.
     03  from  Prog-Name  pic x(15)                                    line  1 col  1 foreground-color 2.
     03  value "Parameter Entry 2 - Accounts"                                  col 29.
     03  from  U-Date     pic x(10)                                            col 71 foreground-color 2.
     03  from  Usera      pic x(32)                                    line  3 col  1.
     03  value "    Account Records"                                   line  4 col 29.
     03  value "Entry #   Acct #   Description"                        line  6 col  1 foreground-color 3.
     03  from  Act-No    pic 99                                        line  7 col  2 foreground-color 3.
     03  from  Act-GL-No pic 9(6)                                      line  7 col 11 foreground-color 3.
     03  from  Act-Desc  pic x(24)                                     line  7 col 20 foreground-color 2.
*>
     03  Value "* Escape to quit Entry"                                line 22 col  1 foreground-color 6.
*>
*>
*> Stored here for inclusion in correct programs
*>



*>  -----------------                            -------------------
*>
*>  5  Vacation Taken      18  Tips Reported         except FICA
*>  6  Sick Leave Taken    27  Advance Repay.
*>  7  Comp Time Taken     28  FWT Add-On         3  Subject to all taxes
*>  8  Comp Time Earned    29  SWT Add-On            and percent deductions
*> 10  Tips Collected      31  FICA Add-On
*>**
*>Y O U R  C O M P A N Y  N A M E                                         00/00/ccyy
*>                                Payroll System
*>                            Pay Transaction Entry                   Batch: nnn
*>
*>
*>
*>      Record Number [       ]---------------------------------------+
*>        |                                                           |
*>        |  Employee No.  [       ] employee name                    |
*>        |  Trans code    [  ]      description                      |
*>        |  Units         [            ]                             |
*>        |  Date          [          ]                               |
*>        |                                                           |
*>        +-----------------------------------------------------------+
*>
*>                    Display Employee Names [ ]
*>**
*>Y O U R  C O M P A N Y  N A M E                                           00/00/ccyy
*>                                Payroll System
*>                               Print Pay Checks
*>
*>
*>         Type ""Y"" or Press  Return  to Print a Test Form
*>         Type ""N"" When the Forms are properly aligned [ ]
*>
*>         The Last Check Printed was Check Number   nnnnnn
*>
*>         The Starting Check Number Will Be    [      ]
*>
*>
*>          Press the Escape key to Stop
*>          Press the Return key to Continue   [ ]
*>
*>          The Check Amount Exceeds The Maximum Allowed.
*>          This Check Will Be Voided.
*>
*>                   All Checks Have Been Printed
*>**
*>YOUR COMPANY NAME                                                00/00/ccyy
*>                                Payroll System
*>
*>       1. All Employees                  8. All Hourly Employees
*>       4. All Semi-Monthly Employees    11. All On-leave Employees
*>       5. All Monthly Employees         12. All Terminated Employees
*>       6. All Week Based Employees      13. All Deleted Employees
*>       7. All Month Based Employees     14. A Range Of Employees
*>
*>                  Enter Your Selection Number: [  ]
*>
*>                  Range From [       ] To [       ]
*>
*>                  Full Information or Single Line (F Or S) [ ]
*>**
*>YOUR COMPANY NAME                                                 00/00/ccyy
*>                                Payroll System
*>                               Print 941 Report
*>      company name                                                date qtr ended
*>      trade name
*>      address                                                     I.D. number
*>      address
*>      city                    state       zipcode
*>      Print Name And Address  [ ]
*>Number of Employees
*>Total Wages and Tips
*>Total Income Tax Withheld
*>Adjustment of Withheld Income Tax from Previous Quarters    [             ]
*>Adjusted Total of Income Tax Withheld                                     ]
*>Taxable FICA Wages Paid                     Times 12.26% =
*>Taxable Tips Reported                       Times  6.13% =
*>Total FICA Taxes                                            [             ]
*>Adjustment of FICA Taxes                                    [             ]
*>Adjusted Total of FICA Taxes                                [             ]
*>Total Taxes                                                 [             ]
*>Earned Income Credit                                        [             ]
*>Net Taxes                                                   [             ]

*>**    941b
*>Deposit per End  00/00/ccyy      Liability      Date       Amount
*>Overpayment From Previous Quarter.......................  [999999.99]
*> Month     | Days 8 Through 15   nnnnnnn.nn   [          ][         ]
*> Of        | Days 16 Through 22  nnnnnnn.nn   [          ][         ]
*> Quarter   | Days 23 Through End nnnnnnn.nn   [          ][         ]
*>   First Month Total:            nnnnnnn.nn
*> Month     | Days 8 Through 15   nnnnnnn.nn   [          ][         ]
*> Of        | Days 16 Through 22  nnnnnnn.nn   [          ][         ]
*> Quarter   | Days 23 Through End nnnnnnn.nn   [          ][         ]
*>   Second Month Total:           nnnnnnn.nn
*> Month     | Days 8 Through 15   nnnnnnn.nn   [          ][         ]
*> Of        | Days 16 Through 22  nnnnnnn.nn   [          ]
*> Quarter   | Days 23 Through End nnnnnnn.nn   [          ][         ]
*>   Third Month Total:            nnnnnnn.nn
*>Total For Quarter:               nnnnnnn.nn               [         ]
*>Final Deposit For Quarter:....................[          ][         ]
*>Total Deposits For Quarter:...............................[         ]
*>Overpayment:....                  Undeposited Taxes Due:..[         ]
*>**
*>YOUR COMPANY NAME                                                       00/00/ccyy
*>                              Print W-2 Report
*>
*> ------------------------------------+---------------------------------------
*>                                     |  Number Of Lines Between Forms  [  ]
*>      Enter Selection [ ]            |
*>                                     |  Starting Print Column          [  ]
*> ------------------------------------|--------------------------------------
*> Starting Employee Number [       ]  |
*>        Employee Number   [       ]  |           Print Test Form [ ]
*> Ending Employee Number   [       ]  |
*> ------------------------------------+--------------------------------------
*>
*>**
*>**
*>    Payroll System               (General Ledger)
*>  -----------------------  Account  ----------------------
*>     Reference No.    Name                          Number
*>           1          Cash                          011100
*>           2          Accrued Liability             121100
*>           3          Salary Expense                411100
*>           4          Accrued Payroll Costs Liab.   131100
*>**
*>     Payroll field limitations from Basic (with some changes) so subject to possible more change :
*>     Co Name:              60 characters maximum [ reduce to 32 or 40 ? ]
*>     Trading Name:         32 characters maximum
*>     Address:              4 lines of 30 characters each
*>     City:                 18 characters maximum  NOT USED as uses address lines 3 or 4.
*>     State:                Official two-character state abbreviation
*>     Zip:                   5 digit number only
*>     Govt Id Nos.:         10 digit number maximum } One or other
*>     N.I, Nos.:            10 digit number maximum }    dito
*>     Employee No.          7 numeric digits last being check modulus 11 ??.
*>     Vacation Rate:        99999.99 maximum entry [9(5)v99].
*>     S.L. Rate:            99999.99 maximum entry
*>     Rate 1, 2, 3 & 4
*>      Descriptive Name:    15 characters each
*>     Rate1 Default:        99999.99 maximum entry
*>     Rate2 Factor:         99999.99 maximum entry
*>     Rate3 Factor:         99999.99 maximum entry
*>     Max Pay Factor:       99999.99 maximum entry
*>     Normal Units:         99999.99 maximum entry
*>     Check Writing max Amount
*>      (Before Voiding):    9,999,999.99 max  [9(7)v99]. as set in params.
*>     Expense Account:      1 to 2 digit Payroll System Account
*>                           (Act Record) Reference Number
*>     Offset Cash Account:  1 to 2 digit Payroll System Account
*>                           (Act Record) Reference Number
*>     Default Dist Account: 1 to 2 digit Payroll System Account
*>                           (Act Record) Reference Number
*>     Check No.             999999. -- does any bamk use more ?
*> These not used in Cobol version --- As yet.
*>     User defined program name:
*>                           Valid 8 character CP/M filename;
*>                           Alpha numeric only and
*>                           must not start with a number.
*>     User Defined Program Desc:
*>                           30 characters maximum
*>**
*>
*> Where "aa" is the two character state abbreviation.  There are four
*> tax table files for California:
*>
*>   Merge into one.
*>
*>**
*>
*>    TRANSACTION     TRANSACTION         CHECK
*>       CODE            TYPE            CATEGORY
*>
*>        (0)         Rate0 Pay             1
*>        (1)         Rate1 Pay             2
*>        (2)         Rate2 Pay             3
*>        (3)         Rate3 Pay             4
*>        (4)         Rate4 Pay             5
*>        (5)         Vacation Taken
*>        (6)         Sick Leave Taken
*>        (7)         Comp Time Taken
*>        (8)         Comp Time Earned
*>        (9)         Bonus                 6
*>       (10)         Tips Collected        7
*>       (11)         Advance               6
*>       (12)         Sick Pay              6
*>       (13)         Vacation Pay          6
*>       (14)         Other Excluded Pay    6
*>       (15)         Expense Reimbursement 6
*>       (17)         Other Pay             6
*>       (18)         Tips Reported        14
*>       (27)         Advance Repay        14
*>       (28)         FWT Add-On            9
*>       (29)         SWT Add-On           10
*>       (30)         LWT Add-On           11
*>       (31)         FICA Add-On          12
*>
*>  (Figure 26.1 Transaction Codes and Check Categories)
*>**
*>          The Optional Reports
*>
*>       1. Account Print
*>       2. Employee Master Report
*>       3. Employee History Report
*>       4. Vacation Report
*>**
*> PRESETS USED in PY900 - - -
*>
*>        Standard Deduction Rates
*>
*>           Acct
*>
*>   FWT:     [Y]   [  2]
*>   SWT:     [Y]   [  2]
*>   LWT:     [N]   [  2]
*>   FICA:    [Y]   [  2]    [   6.13]  [   22,900.00]
*>   CO FICA: [Y]   [  4]    [   6.13]  [   22,900.00]
*>   SDI:     [N]   [  2]    [   1.00]  [    6,000.00]
*>   CO FUTA: [Y]   [  4]    [   3.40]  [    6,000.00]
*>   FUTA Max State Credit:  [   2.70]
*>   CO SUI:  [Y]   [  4]    [   0.00]  [    6,000.00]
*>   EIC:     [N]   [  2]    [  10.00]  [    5,000.00]
*>   EIC Excess:             [  12.50]  [    6,000.00]
*>
*>    (Figure 10.1: Default Standard Deduction Rates)
*>                          created in py900
*>--
*>        FEDERAL WITHHOLDING TAX TABLE ENTRY
*>**
*> The Payroll System did supply the current Federal withholding tax table.
*> Income tax withholding is based on the percentage method
*> (see IRS circular E, Employer's Tax Guide), using the
*> ANNUAL payroll period table. WARNING it is NOT up to date.
*>
*> The System Deduction Entry program (py900) lets you
*> change this table when needed.  See Chapter 22 for details.
*>**
*>
*>
*>     CUTOFF    PERCENT       CUTOFF   PERCENT
*>
*>     (Figure 10.2: Default Federal Tax Table)  via py900
*>**
*>         SYSTEM EARNING AND DEDUCTION INFORMATION
*>
*>   USED?    DESC       E/D ACCT A/P  FACTOR   LIMITED  LIMIT   XLCD CAT
*>
*>
*>    (Figure 10.3: Default System Earning and Deduction Information) via py900
*>**
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
*>
*>
  *>   perform  zz070-Convert-Date. *> o/p as WS-Date - NEEDED ??
*> now check for PY param file & rec.
*>
*>  At this point it is ASSUMED that payroll has run and copied system file
*>  record 1 into System-Record area. IF it does not exist it is created by
*>  forcing sys002 to run, for the first time of running.
*>
*>  If param file opened as output then using AN Input mode,
*>   assuming all number are zero as initialised. NEED TO TEST THIS that AN
*>    is working correctly for zeros.
*>
*> Sort the US states codes in alphabetic order
*>  ready for search all on WS-Codes
*>
     sort     WS-States on ascending key WS-Codes.

     move     1 to RRN.
     open     input PY-Param1-File.
     if       PY-PR1-Status not = "00"      *> Does not exist yet so lets create it & write rec
              close    PY-Param1-File
              open     output PY-Param1-File
              close    PY-Param1-File
              open     i-o PY-Param1-File
              set      AN-MODE-IS-NO-UPDATE to true
              perform  ab000-PY-Param-Set-Up  *> at end file will be opened as i-o also act file set up via IRS
              if       WS-Term-Code = 16
                       close    PY-Param1-File
                       goback
     else
              set      AN-MODE-IS-UPDATE to true
              close    PY-Param1-File
              open     i-o PY-Param1-File
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
                       display  space at line WS-23-lines col 1 with erase eos
                       display  SY001 at line WS-Lines col 1 foreground-color 4
                       goback
              end-if
     end-if.
     move     zero  to  Menu-Reply.
*>
*> REMEMBER TO REOPEN PARAM FILE AND CLOSE IT AFTER A REWRITE   <<<<<<<<-------
*> before all menus other than the first one
*>
 aa010-Param-Menu-1.
     move     maps-ser-nn to curs2.
     display  space at 0101 with erase eos.
     move     spaces to Menu-Reply.
 *>    display  Display-Heads.
     display  SS-Param-Menu-1.
     accept   SS-Param-Menu-1 AUTO UPDATE.
     move     UPPER-CASE (Menu-Reply) to Menu-Reply.
*>
     if       Menu-Reply = "N"         *> NEXT menu
              go to    aa020-Param-Menu-2-Starter.
*>
     if       Menu-Reply = "X"         *> Quit
        or    Cob-CRT-Status = Cob-Scr-Esc
              move     1 to RRN
              rewrite  PY-Param1-Record
              perform  aa125-Test-PR1-Status
              if       PY-PR1-Status not = "00"     *> E.g., 22, key exists
                       write    PY-Param1-Record
                       perform  aa125-Test-PR1-Status
              end-if
              close    PY-Param1-File
              move     zero to WS-Term-Code
              goback                        *> Quit program, we are done
     end-if.
 aa011-Retry-1.
*> Company ID & General params
     if       Menu-Reply = 1
              move     maps-ser-nn to curs2
 *>             display  Display-Heads
              display  space at 0101 with erase eos
              move     "00/00/0000" to WS-Date
              if       PY-PR1-Last-Day-Pay-Period (1:2) not = zeros
                       move     PY-PR1-Last-Day-Pay-Period (1:2) to WS-Days
                       move     PY-PR1-Last-Day-Pay-Period (3:2) to WS-Month
                       move     PY-PR1-Last-Day-Pay-Period (5:4) to WS-Year
              end-if
              display  SS-Param-1-Company-Details-1
   *>           accept   SS-Param-1-Company-Details-1 *> UPDATE
*>
              perform  forever
                       accept   PY-PR1-Dflt-Pay-Interval at 0674 foreground-color 3 UPDATE UPPER
                       if       PY-PR1-Dflt-Pay-Interval not = "S" and not = "M"
                           and                           not = "W" and not = "B"
                                move     PY104 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       else
                                display  spaces at line WS-23-Lines col 1 erase eos
                                exit     perform
                       end-if
              end-perform
              accept   PY-PR1-Date-Format       at 0742 foreground-color 3 UPDATE
              accept   PY-PR2-Last-Q-Ended      at 0774 foreground-color 3 UPDATE
              accept   WS-Date                  at 0833 foreground-color 3 UPDATE
              accept   PY-PR2-Year              at 0871 foreground-color 3 UPDATE
              accept   PY-PR1-Trade-Name        at 1023 foreground-color 3 UPDATE
              accept   PY-PR1-Co-Name           at 1115 foreground-color 3 UPDATE
              accept   PY-PR1-Co-Address-1      at 1212 foreground-color 3 UPDATE
              accept   PY-PR1-Co-Address-2      at 1312 foreground-color 3 UPDATE
              perform  forever
                       accept   PY-PR1-Co-State at 1353 foreground-color 3 UPDATE
                       MOVE     ZERO TO C
                       SET      QQ   TO 1
                       search   all  WS-States  *>  at end      move zero to C  ** NOT NEEDED ???
                                when  PY-PR1-Co-State = WS-Codes (QQ)
                                      SET   C to QQ
                       if       C = zero
                                display  PY125 at line WS-23-Lines col 1 foreground-color 4
                                                                         erase eol
                                exit perform cycle
                       else
                                display  space at line WS-23-Lines col 1 erase eol
                                exit perform
                       end-if
              end-perform
              accept   PY-PR1-Co-Zip            at 1365 foreground-color 3 UPDATE
              accept   PY-PR1-Co-Address-3      at 1412 foreground-color 3 UPDATE
              accept   PY-PR1-Co-Phone          at 1463 foreground-color 3 UPDATE
              accept   PY-PR1-Co-Address-4      at 1512 foreground-color 3 UPDATE
              accept   PY-PR1-Co-Email          at 1612 foreground-color 3 UPDATE
              accept   PY-PR1-Fed-ID            at 1812 foreground-color 3 UPDATE
              accept   PY-PR1-State-ID          at 1834 foreground-color 3 UPDATE
              accept   PY-PR1-Local-ID          at 1855 foreground-color 3 UPDATE
              accept   PY-PR1-Tax-ID            at 1912 foreground-color 3 UPDATE
              accept   PY-PR1-Page-Lines-P      at 2118 foreground-color 3 UPDATE  *> chgd 07/12/25
              accept   PY-PR1-Page-Lines-L      at 2140 foreground-color 3 UPDATE  *> new 07/12/25
*>
              perform  Forever
                       accept   PY-PR1-Debugging at 2162 foreground-color 3 UPDATE UPPER
                       if       PY-PR1-Debugging not = "N" and not = "Y"
                                move     PY103 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       exit     perform
              end-perform
              perform  Forever      *> new 02/02/26
                       accept   PY-PR1-Hard-Delete at 2174 foreground-color 3 UPDATE UPPER
                       if       PY-PR1-Hard-Delete not = "Y" and not = "N"
                                move     PY126 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       display  space at line WS-23-Lines col 1 erase eol
                       exit     perform
              end-perform
*>
              accept   PY-PR1-Page-Width-L      at 2220 foreground-color 3 UPDATE  *> chgd 07/12/25
              accept   PY-PR1-Page-Width-P      at 2244 foreground-color 3 UPDATE  *> chgd 07/12/25
*>
              if       PY-PR1-Date-Format < 1 or > 2
                       move     PY105 to WS-Err-Msg
                       perform  aa100-Bad-Data-Display
                       go to    aa011-Retry-1
              end-if
              if       PY-PR2-Last-Q-Ended < 1 or > 4
                       move     PY106 to WS-Err-Msg
                       perform  aa100-Bad-Data-Display
                       go to    aa011-Retry-1
              end-if
              if       (PY-PR1-Page-Lines-L < 40 or > 90)
                  or   (PY-PR1-Page-Lines-P < 40 or > 90)
                       move     PY107 to WS-Err-Msg
                       perform  aa100-Bad-Data-Display
                       go to    aa011-Retry-1
              end-if
*> can be dd/mm or dd/mm dont care - still works but 1st get rid of "/" etc
              move     WS-Days  to PY-PR1-Last-Day-Pay-Period (1:2)
              move     WS-Month to PY-PR1-Last-Day-Pay-Period (3:2)
              move     WS-Year  to PY-PR1-Last-Day-Pay-Period (5:4)
              perform  zz010-Test-YMD
              if       A not = zero
                       display  SY005 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                       display  "Last Day Pay Period" at line WS-23-Lines col 20 foreground-color 6
                       go  to aa011-Retry-1
              end-if
              move     1 to RRN
              rewrite  PY-Param1-Record               *> previous exists
              perform  aa125-Test-PR1-Status
              go to    aa010-Param-Menu-1.
*>
 aa012-Retry-2.
*> Pay intervals
     if       Menu-Reply = 2
              move     maps-ser-nn to curs2
  *>            display  Display-Heads
              display  space at 0101 with erase eos
              display  SS-Param-2-Pay-Interval-Details
              perform  forever
                       accept   PY-PR1-M-Used at 0721 foreground-color 3 UPPER UPDATE
                       move     "00/00/0000" to WS-Date          *> NEED TO TEST DATES
                       move     WSE-Year to WS-Year
                       move     12       to WS-Month
                       move     31       to WS-Days
                       if       PY-PR1-M-Used = "Y"
                                accept   WS-Date  at line 7 col 61  foreground-color 3 UPDATE
                                move     WS-Days  to PY-PR2-Last-Day-Last-M (1:2)
                                move     WS-Month to PY-PR2-Last-Day-Last-M (3:2)
                                move     WS-Year  to PY-PR2-Last-Day-Last-M (5:4)
                                perform  zz010-Test-YMD
                                if       A not = zero
                                         display  SY005 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                         display  "Last Day Last M" at line WS-23-Lines col 20 foreground-color 6
                                         exit perform cycle
                                end-if
                                display  space at line WS-23-Lines col 1 erase eos
                                exit  perform
                       end-if
              end-perform
              accept   PY-PR1-S-Used at 0821 foreground-color 3 UPPER UPDATE
              if       PY-PR1-S-Used = "Y"
                       perform  forever
                                accept   WS-Date  at line 8 col 61  foreground-color 3 UPDATE
                                move     WS-Days  to PY-PR2-Last-Day-Last-S (1:2)
                                move     WS-Month to PY-PR2-Last-Day-Last-S (3:2)
                                move     WS-Year  to PY-PR2-Last-Day-Last-S (5:4)
                                perform  zz010-Test-YMD
                                if       A not = zero
                                         display  SY005 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                         display  "Last Day Last S" at line WS-23-Lines col 20 foreground-color 6
                                         exit perform cycle
                                end-if
                                display  space at line WS-23-Lines col 1 erase eos
                                exit perform
                       end-perform
              end-if
              accept   PY-PR1-B-Used at 0921 foreground-color 3 UPPER UPDATE
              if       PY-PR1-B-Used = "Y"
                       perform  forever
                                accept   WS-Date  at line 9 col 61  foreground-color 3 UPDATE
                                move     WS-Days  to PY-PR2-Last-Day-Last-B (1:2)
                                move     WS-Month to PY-PR2-Last-Day-Last-B (3:2)
                                move     WS-Year  to PY-PR2-Last-Day-Last-B (5:4)
                                perform  zz010-Test-YMD
                                if       A not = zero
                                         display  SY005 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                         display  "Last Day Last B" at line WS-23-Lines col 20 foreground-color 6
                                         exit perform cycle
                                end-if
                                display  space at line WS-23-Lines col 1 erase eos
                                exit perform
                       end-perform
              end-if
              accept   PY-PR1-W-Used at 1021 foreground-color 3 UPPER UPDATE
              if       PY-PR1-W-Used = "Y"
                       perform  forever
                                accept   WS-Date  at 1061 foreground-color 3 UPDATE
                                move     WS-Days  to PY-PR2-Last-Day-Last-W (1:2)
                                move     WS-Month to PY-PR2-Last-Day-Last-W (3:2)
                                move     WS-Year  to PY-PR2-Last-Day-Last-W (5:4)
                                perform  zz010-Test-YMD
                                if       A not = zero
                                         display  SY005 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                         display  "Last Day Last W" at line WS-23-Lines col 20 foreground-color 6
                                         exit perform cycle
                                end-if
                                display  space at line WS-23-Lines col 1 erase eos
                                exit perform
                       end-perform
              end-if
*>
*>    Should all be using Cyan (3) for input
*>
              MOVE     14  TO AN-LINE
              MOVE     30  TO AN-COLUMN
              set      AN-MODE-IS-UPDATE TO TRUE
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Dflt-Vac-Rate
                                                     by REFERENCE AN-ACCEPT-NUMERIC
              perform  AN-Test-Status  *> not bother for all others as not used
*>
              MOVE     15  TO AN-LINE
              MOVE     30  TO AN-COLUMN
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Dflt-SL-Rate
                                                     by REFERENCE AN-ACCEPT-NUMERIC
*>
              accept   PY-PR1-Rate-Name (1) at 1604 foreground-color 3 UPDATE
              MOVE     16  TO AN-LINE
              MOVE     30  TO AN-COLUMN
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Dflt-Pay-Rate
                                                     by REFERENCE AN-ACCEPT-NUMERIC
*>
              accept   PY-PR1-Rate-Name (2) at 1704 foreground-color 3 UPDATE
              MOVE     17  TO AN-LINE
              MOVE     30  TO AN-COLUMN
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Rate2-Factor
                                                     by REFERENCE AN-ACCEPT-NUMERIC
*>
              accept   PY-PR1-Rate-Name (3) at 1804 foreground-color 3 UPDATE
              MOVE     18  TO AN-LINE
              MOVE     30  TO AN-COLUMN
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Rate3-Factor
                                                     by REFERENCE AN-ACCEPT-NUMERIC
*>
              accept   PY-PR1-Rate-Name (4) at 1904 foreground-color 3 UPDATE
              perform  forever
                       accept   PY-PR1-Rate4-Exclusion-Type at 1937 foreground-color 3 UPDATE
                       if       PY-PR1-Rate4-Exclusion-Type > 4
                                move     PY108 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       display  space at line WS-23-Lines col 1 erase eos
                       exit  perform
              end-perform
*>
              perform  forever
                       accept   PY-PR1-Dflt-Pay-Interval at 2144 foreground-color 3 UPDATE UPPER
                       if       PY-PR1-Dflt-Pay-Interval not = "S" and not = "M"
                                                     and not = "B" and not = "W"
                                move     PY109 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       display  space at line WS-23-Lines col 1 erase eos
                       exit perform
              end-perform
*>
              MOVE     21  TO AN-LINE
              MOVE     64  TO AN-COLUMN
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Max-Pay-Factor
                                                     by REFERENCE AN-ACCEPT-NUMERIC
*>
              perform  forever
                       accept   PY-PR1-Dflt-HS-Type at 2244 foreground-color 3 UPDATE UPPER
                       if       PY-PR1-Dflt-HS-Type not = "H" and not = "S"
                                move     PY110 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       display  space at line WS-23-Lines col 1 erase eos
                       exit perform
              end-perform
*>
              MOVE     22  TO AN-LINE
              MOVE     64  TO AN-COLUMN
              set      AN-MODE-IS-UPDATE TO TRUE
              call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Dflt-Norm-Units
                                                              by REFERENCE AN-ACCEPT-NUMERIC
              move     1 to RRN
              rewrite  PY-Param1-Record               *> Previously exists
              perform  aa125-Test-PR1-Status
              go to    aa010-Param-Menu-1.   *> go and Select another menu option
*>
 aa014-Retry-3.
*>  Payroll System Config and GL Interface
 *>    if       PY-PR1-IRS-Used = "I"
 *>             perform  acasirsub1-Open-Input
 *>     else
 *>       if    PY-PR1-GL-Used = "Y"
*>
     if       Menu-Reply = 3
              move     maps-ser-nn to curs2
 *>             display  Display-Heads
              display  space at 0101 with erase eos
              display  SS-Param-3-GL-Details
              move     zero to Error-Code
              perform  forever
                       accept   PY-PR1-GL-Used at 0633 foreground-color 3 UPPER UPDATE
                       if       PY-PR1-GL-Used not = "Y" and not = "N"
                                           and not = "B" and not = "I"
                                move     PY111 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       display  space at line WS-23-Lines col 1 erase eos
                       exit perform
              end-perform
              if       PY-PR1-GL-Used = "I" or = "B"
                       move     "Y" to PY-PR1-IRS-Used
              end-if
              perform  forever
                       accept   PY-PR1-Check-Printing-Used at 0669 foreground-color 3
                                                                   UPPER UPDATE
                       if       PY-PR1-Check-Printing-Used not = "Y" and not = "N"
                                move     PY112 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       display  space at line WS-23-Lines col 1 erase eos
                       exit perform
              end-perform
              perform  forever
                       accept   PY-PR1-Void-Checks-Over-Max at 0733 foreground-color 3 UPPER UPDATE
                       if       PY-PR1-Void-Checks-Over-Max not = "Y" and not = "N"
                                move     PY113 to WS-Err-Msg
                                perform  aa100-Bad-Data-Display
                                exit perform cycle
                       end-if
                       display  space at line WS-23-Lines col 1 erase eos
                       exit perform
              end-perform
              if       PY-PR1-Void-Checks-Over-Max = "Y"
                       set      AN-MODE-IS-UPDATE TO TRUE
                       if       PY-PR1-Void-Check-Amt = zeros
                                set      AN-MODE-IS-NO-UPDATE TO TRUE
                       end-if
                       MOVE     07  TO AN-LINE
                       MOVE     58  TO AN-COLUMN
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE PY-PR1-Void-Check-Amt
                                                              by REFERENCE AN-ACCEPT-NUMERIC
              end-if
*>
*> We NEED IRS (but NO CODE FOR  GL) for PY to work correctly.
*>
              if       PY-PR1-GL-Used = "I" or = "B"
                       MOVE     10  TO AN-LINE
                       MOVE     27  TO AN-COLUMN
                       move     PY-PR1-Offset-Cash-Acct  to WS-Temp-Act-No
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Act-No
                                                              by REFERENCE AN-ACCEPT-NUMERIC
                       if       (WS-Temp-Act-No = 0 or
                                                > WS-Account-Count)
                           or   WS-Act-Exists (WS-Temp-Act-No) not = "Y"
                                display  PY117 at 1701 erase eol foreground-color 6 BEEP
                                display  WS-Temp-Act-No at 1027 foreground-color 6
                                move     1 to Error-Code
                       end-if
                       move     WS-Temp-Act-No to PY-PR1-Offset-Cash-Acct
*>
                       MOVE     10  TO AN-LINE
                       MOVE     63  TO AN-COLUMN
                       move     PY-PR1-Dflt-Dist-Acct  to WS-Temp-Act-No
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Act-No
                                                              by REFERENCE AN-ACCEPT-NUMERIC
                       if       (WS-Temp-Act-No = 0 or
                                                > WS-Account-Count)
                           or   WS-Act-Exists (WS-Temp-Act-No) not = "Y"
                                display  PY117 at 1801 erase eol foreground-color 6 BEEP
                                display  WS-Temp-Act-No at 1063 foreground-color 6
                                move     1 to Error-Code
                       end-if
                       move     WS-Temp-Act-No to PY-PR1-Dflt-Dist-Acct
*>
                       MOVE     11  TO AN-LINE
                       MOVE     63  TO AN-COLUMN
                       move     PY-PR1-Dflt-Gross-Acct  to WS-Temp-Act-No
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Act-No
                                                              by REFERENCE AN-ACCEPT-NUMERIC
                       if       (WS-Temp-Act-No = 0 or
                                                > WS-Account-Count)
                           or   WS-Act-Exists (WS-Temp-Act-No) not = "Y"
                                display  PY117 at 1901 erase eol foreground-color 6 BEEP
                                display  WS-Temp-Act-No at 1163 foreground-color 6
                                move     1 to Error-Code
                       end-if
                       move     WS-Temp-Act-No to PY-PR1-Dflt-Gross-Acct
              end-if
*>
              if       PY-PR1-GL-Used = "I" or = "B"
                       perform  forever
                                accept   PY-PR1-Dist-Used at 1560 foreground-color 3  UPPER UPDATE
                                if       PY-PR1-Dist-Used not = "Y" and not = "N"
                                         move     PY119 to WS-Err-Msg
                                         perform  aa100-Bad-Data-Display
                                         exit perform cycle
                                end-if
                                display  space at line WS-23-Lines col 1 erase eos
                                exit perform
                       end-perform
              else
                       move     "N" to PY-PR1-Dist-Used
              end-if
              if       Error-Code not = zero
                       go to aa014-Retry-3
              end-if
              move     1 to RRN
              rewrite  PY-Param1-Record               *> Previously exists
              perform  aa125-Test-PR1-Status
              go to    aa010-Param-Menu-1.
*>
     go to    aa010-Param-Menu-1.
*>
 aa020-Param-Menu-2-Starter.
*>
*> open up files etc.
*>
     open     input    PY-System-Deduction-File.
     if       PY-Ded-Status not = "00"
              close    PY-System-Deduction-File
              open     output PY-System-Deduction-File
              close    PY-System-Deduction-File
              open     i-o PY-System-Deduction-File
              set      AN-MODE-IS-NO-UPDATE to true  *> TEST FOR INPUT MODE
              perform  ab070-PY-DED-Setup            *> any defaults and rewrites
     else
              close    PY-System-Deduction-File
              set      AN-MODE-IS-UPDATE to true
              open     i-o PY-System-Deduction-File
              move     1 to RRN
              read     PY-System-Deduction-File
              if       PY-Ded-Status not = "00"
                       perform aa115-Eval-Ded-Read
     end-if.                                         *>PY-Para file opened already
*>
 aa020-Param-Menu-2.  *> Menu 2 is for Deduction-file
*>
*> At this point Accounts, Deduction files are open - see above Menu-2-Starter.
*>
     move     maps-ser-nn to curs2.
 *>    display  Display-Heads.
     display  space at 0101 with erase eos.
     move     spaces to Menu-Reply.
     display  SS-Param-Menu-2.
     accept   SS-Param-Menu-2  AUTO UPPER.
     move     1 to RRN.
     move     UPPER-CASE (Menu-Reply) to Menu-Reply.
*>
     if       Menu-Reply = "X"         *> Quit
        or    Cob-CRT-Status = Cob-Scr-Esc
              move     1 to RRN
              rewrite  PY-System-Deduction-Record
              if       PY-Ded-Status not = "00"     *> E.g., 21 or 23, key not exists so create it
                       write    PY-System-Deduction-Record
                       if       PY-Ded-Status not = "00"   *> WE have a real problem :(
                                perform  aa110-Eval-Ded-Write
                       end-if
              end-if
              move     1 to RRN
              rewrite  PY-Param1-Record
              close    PY-Param1-File
              close    PY-System-Deduction-File
              close    PY-Accounts-File
              goback                        *> Quit program, we are done
     end-if.
     move     zero to Error-Code.
*> Standard Deduction Rates
 aa022-Retry-1.
     if       Menu-Reply = 1
              move     maps-ser-nn to curs2
 *>             display  Display-Heads
              display  space at 0101 with erase eos
              display  SS-Param-4-Standard-Deduction-Rates
              set      AN-MODE-IS-UPDATE TO TRUE
*>
              perform  forever
                       accept   Ded-FWT-Used  at 0825 foreground-color 3 UPPER UPDATE
                       if       Ded-FWT-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 0828 with foreground-color 6
                                exit perform cycle
                       end-if
                       exit     perform
              end-perform
              display  "  " at 0828  *> NEED TO TEST FOR GL = Y and for all act-no
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-FWT-Acct-No to WS-Temp-Act-No
                       move     8  to AN-Line
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-FWT-Acct-No
                                                   Act-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-FWT-Acct-No at 0831 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-FWT-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-FWT-Acct-No at 0831 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-FWT-Acct-No
              end-if
*>
              perform  forever
                       accept   Ded-SWT-Used  at 0925 foreground-color 3 UPPER UPDATE
                       if       Ded-SWT-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 0928 with foreground-color 6
                                exit perform cycle
                       end-if
                       exit     perform
              end-perform
              display  "  " at 0928
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-SWT-Acct-No to WS-Temp-Act-No
                       move     9  to AN-Line
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-SWT-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-SWT-Acct-No at 0931 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-SWT-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-SWT-Acct-No at 0931 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-SWT-Acct-No
              end-if
*>
              perform  forever
                       accept   Ded-LWT-Used  at 1025 foreground-color 3 UPPER UPDATE
                       if       Ded-LWT-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 1028 with foreground-color 6
                                exit perform cycle
                       end-if
                       exit     perform
              end-perform
              display  "  " at 1028
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-LWT-Acct-No to WS-Temp-Act-No
                       move     10 to AN-Line
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-LWT-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-LWT-Acct-No at 1031 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-LWT-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-LWT-Acct-No at 1031 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move    zeros to Ded-LWT-Acct-No
              end-if
*>
              perform  forever
                       accept   Ded-FICA-Used  at 1125 foreground-color 3 UPPER UPDATE
                       if       Ded-FICA-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 1128 with foreground-color 6
                                exit perform cycle
                       end-if
                       exit  perform
              end-perform
              display  "  " at 1128
              move     11 to AN-Line
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-FICA-Acct-No to WS-Temp-Act-No
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-FICA-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-FICA-Acct-No at 1131 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-FICA-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-FICA-Acct-No at 1131 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-FICA-Acct-No
              end-if
*>
              move     Ded-FICA-Rate  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-FICA-Rate
              move     Ded-FICA-Limit to WS-Temp-Limit
              perform  aa180-AN-Limit-1
              move     WS-Temp-Limit  to Ded-FICA-Limit
*>
              perform  forever
                       accept   Ded-CO-FICA-Used  at 1225 foreground-color 3 UPPER UPDATE
                       if       Ded-CO-FICA-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 1228 with foreground-color 6
                                exit  perform cycle
                       end-if
                       exit  perform
              end-perform
              display  "  " at 1228
              move     12 to AN-Line
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-CO-FICA-Acct-No to WS-Temp-Act-No
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-CO-FICA-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-CO-FICA-Acct-No at 1231 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-CO-FICA-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-CO-FICA-Acct-No at 1231 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-CO-FICA-Acct-No
              end-if
*>
              move     Ded-CO-FICA-Rate  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-CO-FICA-Rate
              move     Ded-CO-FICA-Limit to WS-Temp-Limit
              perform  aa180-AN-Limit-1
              move     WS-Temp-Limit  to Ded-CO-FICA-Limit
*>
              perform  forever
                       accept   Ded-SDI-Used  at 1325 foreground-color 3 UPPER UPDATE
                       if       Ded-SDI-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 1328 with foreground-color 6
                                exit perform cycle
                       end-if
                       exit  perform
              end-perform
              display  "  " at 1328
              move     13 to AN-Line
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-SDI-Acct-No to WS-Temp-Act-No
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-SDI-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-SDI-Acct-No at 1331 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-SDI-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-SDI-Acct-No at 1331 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-SDI-Acct-No
              end-if
*>
              move     Ded-SDI-Rate  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-SDI-Rate
              move     Ded-SDI-Limit to WS-Temp-Limit
              perform  aa180-AN-Limit-1
              move     WS-Temp-Limit  to Ded-SDI-Limit
*>
              perform  forever
                       accept   Ded-CO-FUTA-Used  at 1425 foreground-color 3 UPPER UPDATE
                       if       Ded-CO-FUTA-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 1428 with foreground-color 6
                                exit perform cycle
                       end-if
                       exit  perform
              end-perform
              display  "  " at 1428
              move     14 to AN-Line
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-CO-FUTA-Acct-No to WS-Temp-Act-No
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-CO-FUTA-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-CO-FUTA-Acct-No at 1431 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-CO-FUTA-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-CO-FUTA-Acct-No at 1431 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-CO-FUTA-Acct-No
              end-if
*>
              move     Ded-CO-FUTA-Rate  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-CO-FUTA-Rate
              move     Ded-CO-FUTA-Limit to WS-Temp-Limit
              perform  aa180-AN-Limit-1
              move     WS-Temp-Limit  to Ded-CO-FUTA-Limit
*>
              move     15 to AN-Line
              move     Ded-CO-FUTA-Max-Credit  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-CO-FUTA-Max-Credit
*>
              perform  forever
                       accept   Ded-CO-SUI-Used  at 1625 foreground-color 3 UPPER UPDATE
                       if       Ded-CO-SUI-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 1628 with foreground-color 6
                                exit  perform cycle
                       end-if
                       exit  perform
              end-perform
              display  "  " at 1628
              move     16 to AN-Line
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-CO-SUI-Acct-No to WS-Temp-Act-No
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-CO-SUI-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-CO-SUI-Acct-No at 1631 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-CO-SUI-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-CO-SUI-Acct-No at 1631 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-CO-SUI-Acct-No
              end-if
*>
              move     Ded-CO-SUI-Rate  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-CO-SUI-Rate
              move     Ded-CO-SUI-Limit to WS-Temp-Limit
              perform  aa180-AN-Limit-1
              move     WS-Temp-Limit  to Ded-CO-SUI-Limit
*>
              perform  forever
                       accept   Ded-EIC-Used  at 1725 foreground-color 3 UPPER UPDATE
                       if       Ded-EIC-Used not = "Y" and not = "N"
                                display  PY119 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                                display  "**"  at 1728 with foreground-color 6
                                exit perform cycle
                       end-if
                       display  space  line WS-23-Lines col 1 erase eol
                       exit  perform
              end-perform
              display  "  " at 1728
              move     17 to AN-Line
              if       PY-PR1-IRS-Used = "Y"
                  or   PY-PR1-GL-Used = "Y"
                       move     Ded-EIC-Acct-No to WS-Temp-Act-No
                       perform  aa160-AN-Act-1
                       move     WS-Temp-Act-No  to Ded-EIC-Acct-No
                       if       WS-Temp-Act-No > WS-Account-Count
                           or                  > WS-Account-Table-Size
                                display  PY124 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-CO-SUI-Acct-No at 1731 foreground-color 6
                                move     1 to Error-Code
                       else
                         if     WS-Act-Exists (Ded-EIC-Acct-No) not = "Y"
                                display  PY117 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                display  Ded-EIC-Acct-No at 1731 foreground-color 6
                                move     1 to Error-Code
                         end-if
                       end-if
              else
                       move     zeros to Ded-EIC-Acct-No
              end-if
*>
              move     Ded-EIC-Rate  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-EIC-Rate
              move     Ded-EIC-Limit to WS-Temp-Limit
              perform  aa180-AN-Limit-1
              move     WS-Temp-Limit  to Ded-EIC-Limit
*>
              move     18 to AN-Line
              move     Ded-EIC-Excess-Rate  to WS-Temp-Rate
              perform  aa170-AN-Percent-1
              move     WS-Temp-Rate  to Ded-EIC-Excess-Rate
              move     Ded-EIC-Excess-Limit to WS-Temp-Limit
              perform  aa180-AN-Limit-1
              move     WS-Temp-Limit  to Ded-EIC-Excess-Limit
*>
              move     1 to RRN
              rewrite  PY-System-Deduction-Record
              if       PY-Ded-Status not = "00"
                       perform  aa120-Eval-Ded-Rewrite
                       display  SY001 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                       accept   WS-Reply at line WS-23-Lines col 48 AUTO
                       close    PY-System-Deduction-File
                       close    PY-Accounts-File
                       close    PY-Param1-File
                       move     16 to WS-Term-Code
                       goback
              end-if
              if       Error-Code not = zero
                       go to aa022-Retry-1
              end-if
              go to aa020-Param-Menu-2
     end-if.
*>
*> Federal withholding  tax table entry - ie Ded-FWT-Mar (7) & Ded-FWT-Sin  (7)
 aa024-Retry-2.
     if       Menu-Reply = 2
              move     maps-ser-nn to curs2
  *>            display  Display-Heads
              display  space at 0101 with erase eos
              display  SS-Param-5-Federal-Withholding-Tax-Table-Entry
*>
              set      AN-MODE-IS-UPDATE TO TRUE
              move     6  to AN-Line
              move     Ded-FWT-Allowance-Amt to WS-Temp-Limit
              perform  aa190-AN-Limit-1
              move     WS-Temp-Limit to Ded-FWT-Allowance-Amt
*>
              move     9 to A
              move     zero to B
              perform  7 times
                       add      1  to A
                       add      1  to B
                       move     A   to AN-Line
*>
                       move     Ded-FWT-Mar-Cutoff (B) to WS-Temp-Limit
                       perform  aa200-AN-Limit-1     *> Col 17
                       move     WS-Temp-Limit to Ded-FWT-Mar-Cutoff (B)
*>
                       move     Ded-FWT-Mar-Percent (B)  to WS-Temp-Rate
                       perform  aa210-AN-Percent-1   *> col 29
                       move     WS-Temp-Rate  to Ded-FWT-Mar-Percent (B)
*>
                       move     Ded-FWT-Sin-Cutoff (B) to WS-Temp-Limit
                       perform  aa220-AN-Limit-1     *> col 41
                       move     WS-Temp-Limit to Ded-FWT-Sin-Cutoff (B)
*>
                       move     Ded-FWT-Sin-Percent (B)  to WS-Temp-Rate
                       perform  aa230-AN-Percent-1   *> col 53
                       move     WS-Temp-Rate  to Ded-FWT-Sin-Percent (B)
              end-perform
*>
*> Now check that they are in ascending order else rerun data capture
*>
              move     zero to Error-Code
              perform  varying A from 2 by 1 until A > 7
                       if       Ded-FWT-Mar-Cutoff  (A) <= Ded-FWT-Mar-Cutoff  (A - 1)
                           or   Ded-FWT-Mar-Percent (A) <= Ded-FWT-Mar-Percent (A - 1)
                           or   Ded-FWT-Sin-Cutoff  (A) <= Ded-FWT-Sin-Cutoff  (A - 1)
                           or   Ded-FWT-Sin-Percent (A) <= Ded-FWT-Sin-Percent (A - 1)
                                display  PY123 at line WS-23-Lines col 1 erase eol foreground-color 6 BEEP
                                move     1 to Error-Code
              end-perform
              if       Error-Code not = zero
                       go to aa024-Retry-2
              end-if
*>
*> OK its good.
*>
              move     1 to RRN
              rewrite  PY-System-Deduction-Record
              if       PY-Ded-Status not = "00"
                       perform  aa120-Eval-Ded-Rewrite
                       display  SY001 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                       accept   WS-Reply at line WS-23-Lines col 48 AUTO
                       close    PY-Accounts-File
                       close    PY-System-Deduction-File
                       move     16 to WS-Term-Code
                       goback
              end-if
              go to aa020-Param-Menu-2
     end-if.
*>
*> System Earnings & Ded. Info - ie Ded-Sys-Data-Blocks (10)
 aa026-Retry-3.
*>
*> WE NEED an escape if to skip input AND add count of entries used with new DED field.
*>

     if       Menu-Reply = 3
              move     maps-ser-nn to curs2
  *>            display  Display-Heads
              display  space at 0101 with erase eos
              display  SS-Param-6-System-Earning-and-Deduction-Information
              move     5   to A  *> line #
              move     zero to B *> data occurs pos
              move     zero to Error-Code
              set      AN-MODE-IS-UPDATE TO TRUE
              perform  5 times
                       add      1 to A
                       add      1 to B
                       move     A to AN-Line
                       accept   Ded-Sys-Used (B) at line A col 3 foreground-color 3 UPPER UPDATE
                       if       Cob-CRT-Status = Cob-Scr-Esc
                                exit perform
                       end-if
*>
                       if       Ded-Sys-Used (B) not = "Y"
                                             and not = "N"
                                display  Ded-Sys-Used (B) at line A col 3 foreground-color 6 BEEP blink
                                display  PY119 at line A + 7 col 1 foreground-color 6
                                move     1 to Error-Code
                       end-if
                       if       Ded-Sys-Used (B) = "N"
                                initialise Ded-Sys-Data-Blocks (B)
                                move     "N" to Ded-Sys-Used (B)
                                exit perform cycle
                       end-if
                       accept   Ded-Sys-Desc (B) at line A col 6 foreground-color 3 UPDATE
                       accept   Ded-Sys-Earn-Ded (B) at line A col 24 foreground-color 3 UPPER UPDATE
                       if       Ded-Sys-Earn-Ded (B) not = "D"
                                                 and not = "E"
                                display  Ded-Sys-Earn-Ded (B) at line A col 24 foreground-color 6 BEEP blink
                                display  PY115   at line A + 8 col 1 foreground-color 6
                                move     1 to Error-Code
                       end-if
*>
                       if       PY-PR1-IRS-Used = "Y"
                           or   PY-PR1-GL-Used = "Y"
                                move     Ded-Sys-Acct-No (B) to WS-Temp-Act-No
                                move     28 to AN-COLUMN
                                call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Act-No
                                                                       by REFERENCE AN-ACCEPT-NUMERIC
                                move     WS-Temp-Act-No  to Ded-Sys-Acct-No (B)
                                if       WS-Temp-Act-No > WS-Account-Count
                                   or                  > WS-Account-Table-Size
                                         display  PY124 at line A + 9 col 1 erase eol foreground-color 6 BEEP
                                         display  Ded-CO-SUI-Acct-No at 1631 foreground-color 6
                                         move     1 to Error-Code
                                else
                                 if      WS-Act-Exists (WS-Temp-Act-No) not = "Y"
                                         display  WS-Temp-Act-No at line A col 28 foreground-color 6 BEEP blink
                                         display  PY117 at line A + 10 col 1 foreground-color 6
                                         move     1 to Error-Code
                                 end-if
                                end-if
                       else
                                move     zeros to Ded-Sys-Acct-No (B)
                       end-if
*>
                       accept   Ded-Sys-Amt-Percent (B) at line A col 34 foreground-color 3 UPPER UPDATE
                       if       Ded-Sys-Amt-Percent (B) not = "A"
                                                    and not = "P"
                                move     1 to Error-Code
                                display  Ded-Sys-Amt-Percent (B) at line A col 34 foreground-color 6 BEEP blink
                                display  PY121   at line A + 11 col 1 foreground-color 6
                       end-if
                       move     Ded-Sys-Factor (B) to WS-Temp-Factor
                       move     38 to AN-COLUMN
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Factor
                                                              by REFERENCE AN-ACCEPT-NUMERIC
                       move     WS-Temp-Factor to Ded-Sys-Factor (B)
*>
                       accept   Ded-Sys-Limit-Used (B) at line A col 50 foreground-color 3 UPPER UPDATE
                       if       Ded-Sys-Limit-Used (B) not = "Y"
                                                   and not = "N"
                                display  PY119 at line A + 12 col 1 foreground-color 6
                                display  Ded-Sys-Limit-Used (B) at line A col 51 foreground-color 6 BEEP blink
                                move     1 to Error-Code
                       end-if
*>
                       move     Ded-Sys-Limit (B) to WS-Temp-Factor
                       move     56 to AN-COLUMN
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Factor
                                                              by REFERENCE AN-ACCEPT-NUMERIC
                       move     WS-Temp-Factor to Ded-Sys-Limit (B)
                       accept   Ded-Sys-Exclusion (B) at line A col 69 foreground-color 3 UPDATE
                       if       Ded-Sys-Exclusion (B) < 1 or > 4
                                display  PY108 at line A + 13 col 1 foreground-color 6
                                display  Ded-Sys-Exclusion (B) at line A col 69 foreground-color 6 BEEP blink
                                move     1 to Error-Code
                       end-if
                       move     Ded-Sys-Chk-Cat (B) to WS-Temp-Act-No
                       move     72 to AN-COLUMN
                       call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Act-No
                                                              by REFERENCE AN-ACCEPT-NUMERIC
                       move     WS-Temp-Act-No to Ded-Sys-Chk-Cat (B)
*>
                       if       Ded-Sys-Earn-Ded (B) = "D"
                          and   (Ded-Sys-Chk-Cat (B) < 9 or > 16)
                                display  PY122 at line A + 14 col 1 foreground-color 6
                                display  Ded-Sys-Earn-Ded (B) at line A col 24 foreground-color 6 BEEP blink
                                display  Ded-Sys-Chk-Cat (B)  at line A col 72 foreground-color 6 BEEP blink
                                move     1 to Error-Code
                       end-if   *> Yes they could be put together but if needs changing, leave them as is
                       if       Ded-Sys-Earn-Ded (B) = "E"
                          and   (Ded-Sys-Chk-Cat (B) < 2 or > 7)
                                display  PY122 at line A + 15 col 1 foreground-color 6
                                display  Ded-Sys-Earn-Ded (B) at line A col 24 foreground-color 6 BEEP blink
                                display  Ded-Sys-Chk-Cat (B)  at line A col 72 foreground-color 6 BEEP blink
                                move     1 to Error-Code
                       end-if
                       if       Error-Code not = zero
                                set      AN-MODE-IS-UPDATE to true
                                go to     aa026-Retry-3
                       end-if
*>
              end-perform
*>
*> Do we NEED to sort block removing unused entries etc.   <<<<<<<<<<
*>
              move     B to Ded-Sys-Entries-Used
              move     1 to RRN
              rewrite  PY-System-Deduction-Record
              if       PY-Ded-Status not = "00"
                       perform  aa120-Eval-Ded-Rewrite
                       display  SY001 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                       accept   WS-Reply at line WS-23-Lines col 48 AUTO
                       close    PY-Accounts-File
                       close    PY-System-Deduction-File
                       move     16 to WS-Term-Code
                       goback
              end-if
              go to aa020-Param-Menu-2
     end-if.
     go to    aa020-Param-Menu-2.
*>
 aa100-Bad-Data-Display.
     display  WS-Err-Msg at line WS-23-Lines col 1 erase eos.
     display  SY002      at line WS-Lines    col 1.
*>
 aa110-Eval-Ded-Write.
     perform  ZZ040-Evaluate-Message.
     display  PY008         at line WS-23-Lines col 1 with erase eos.  *> WRITE DED
     display  PY-Ded-Status at line WS-23-Lines col 34.
     display  WS-Eval-Msg   at line WS-23-Lines col 37.
     display  SY002         at line WS-Lines    col 1.
     accept   WS-Reply      at line WS-Lines    col 33 AUTO.
*>
 aa115-Eval-Ded-Read.
     perform  ZZ040-Evaluate-Message.
     display  PY009         at line WS-23-Lines col 1 with erase eos.  *> READ DED
     display  PY-Ded-Status at line WS-23-Lines col 34.
     display  WS-Eval-Msg   at line WS-23-Lines col 37.
     display  SY002         at line WS-Lines    col 1.
     accept   WS-Reply      at line WS-Lines    col 33 AUTO.
*>
 aa120-Eval-Ded-Rewrite.
     perform  ZZ040-Evaluate-Message.
     display  PY010         at line WS-23-Lines col 1 with erase eos.  *> WRITE DED
     display  PY-Ded-Status at line WS-23-Lines col 34.
     display  WS-Eval-Msg   at line WS-23-Lines col 37.
     display  SY002         at line WS-Lines    col 1.
     accept   WS-Reply      at line WS-Lines    col 33 AUTO.
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
 aa130-Act-File-Error.
     display  PY118 at line WS-23-Lines col 1 erase eos
                            foreground-color 6 BEEP.
     display  PY-Act-Status at line WS-23-Lines col 40.
     move     PY-Act-Status to PY-PR1-Status.
     perform  ZZ040-Evaluate-Message.
     display  WS-Eval-Msg   at line WS-23-lines col 42.
     display  SY003 at line WS-lines col 01 with foreground-color cob-color-red
                                                 erase eol BEEP.
     accept   WS-Reply at line WS-lines col 52 AUTO.
*>
 aa160-AN-Act-1.  *> DED Rates
 *>    MOVE   ??  10  TO AN-LINE.
     MOVE     31  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Act-No
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 aa170-AN-Percent-1.  *> DED Rates
 *>    MOVE    ?? 10  TO AN-LINE.
     MOVE     39  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Rate
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 aa180-AN-Limit-1.   *> DED Rates
 *>    MOVE     10  TO AN-LINE.
     MOVE     47  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Limit
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 aa190-AN-Limit-1.   *> FWT allow
     MOVE     44  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Limit
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 aa200-AN-Limit-1.   *> FWT Amount - Mar
     MOVE     17  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Limit
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 aa210-AN-Percent-1.  *> FWT Rate - Mar
     MOVE     29  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Rate
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 aa220-AN-Limit-1.   *> FWT Amt - Sin
     MOVE     41  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Limit
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 aa230-AN-Percent-1.  *> FWT Rate - Sin
     MOVE     53  TO AN-COLUMN.
     call     STATIC "ACCEPT_NUMERIC" using by REFERENCE WS-Temp-Rate
                                            by REFERENCE AN-ACCEPT-NUMERIC.
*>
 Menu-Ex.
     exit     program.
*>
*>
 ab000-PY-Param-Set-Up       section.
*>**********************************
*>
*> At this point we have the ACAS system param rec (1) via linkage
*>   and the PY param file does NOT exist.
*>
     initialise
              PY-Param1-Record with filler.
     if       Suser (1:4) not = spaces    *> make sure ACAS param is set up.
              perform ab010-Py-Param-Proc
              perform ab020-Py-Nominal-Accounts.  *> Test for act file exists etc
*>
 ab000-Exit.  exit section.
*>
 ab010-Py-Param-Proc         section.
*>**********************************
*>
*> Param file opened as output on first use, else i-o
*>
*> Start with name / address But sys address is shorter than PY.
*>   and is not compressed or with delimiters, unlike SL or PL
*>     customer or supplier addresses.
*>
*>  THIS IS SET TO USE IRS and not GL ledgers.
*>
     move     "N"           to PY-PR1-Debugging.
     move     Suser         to PY-PR1-Co-Name
                               PY-PR1-Trade-Name.   *> 32 chars only - Can be overwritten
     move     Address-1     to PY-PR1-Co-Address-1.
     move     Address-2     to PY-PR1-Co-Address-2.
     if       Address-3 (1:4) not = spaces
              move     Address-3 to PY-PR1-Co-Address-3.
     if       Address-4 (1:4) not = spaces
              move     Address-4 to PY-PR1-Co-Address-4.
     if       Post-Code (1:4) not = spaces
              move     Post-Code to PY-PR1-Co-Post-Code.  *> It contains State & ZIP
     if       Phone-No (1:4) not = spaces
              move     Phone-No  to PY-PR1-Co-Phone.
     if       Company-Email (1:4) not = spaces
              move     Company-Email to PY-PR1-Co-Email.
     move     File-Defs-os-Delimiter
                            to PY-PR1-OS-Delimiter.
*> Default as this is for the USA and may be Canada
     move     "$"           to PY-PR1-Currency-Sign.
     move     Page-Lines    to PY-PR1-Page-Lines-P.   *> Check these four !
     move     48            to PY-PR1-Page-Lines-L.
     move     80            to PY-PR1-Page-Width-P.
     move     132           to PY-PR1-Page-Width-L.    *> So far for Emp print
     move     1.5           to PY-PR1-Rate2-Factor.
     move     2.0           to PY-PR1-Rate3-Factor.
     move     3.0           to PY-PR1-Max-Pay-Factor.
     move     1.0           to PY-PR1-Dflt-Pay-Rate
                               PY-PR1-Dflt-Norm-Units.
     move     0.42          to PY-PR1-Dflt-Vac-Rate.
     move     0.21          to PY-PR1-Dflt-SL-Rate.
     move     1             to PY-PR1-Offset-Cash-Acct
                               PY-PR1-Rate4-Exclusion-Type.
     move     3             to PY-PR1-Dflt-Dist-Acct.
     move     4             to PY-PR2-Last-Q-Ended.
     move     3             to PY-PR1-Max-Emp-Eds.
     move     5             to PY-PR1-Max-Sys-Eds
                               PY-PR1-Max-Dist-Accts.
     move     "N"           to PY-PR1-S-Used
                               PY-PR1-B-Used
                               PY-PR1-W-Used
                               PY-PR1-Check-History-Used
                               PY-PR1-Check-Printing-Used  *> chg from Y
                               PY-PR1-Void-Checks-Over-Max
                               PY-PR1-JC-Used
                               PY-PR1-GL-Used
                               PY-PR1-Dist-Used    *> chg from Y
                               PY-PR2-940-Printed
                               PY-PR2-941-Printed
                               PY-PR2-W2-Printed.
     move     "Y"           to PY-PR1-M-Used
                               PY-PR1-IRS-Used
                               PY-PR2-Just-Closed-Year.
 *>    if       IRS-Both-Used
 *>             move     "Y"  to PY-PR1-GL-Used.
*>
     move     "S"           to PY-PR1-Dflt-Pay-Interval
                               PY-PR1-Dflt-HS-Type.
     move     "FEDERAL ID"  to PY-PR1-Fed-ID.
     move     "STATE ID"    to PY-PR1-State-ID.
     move     "LOCAL ID"    to PY-PR1-Local-ID.
     if       Date-Form > 0 and < 3  *> i.e., 1 or 2 (System Rec field) (3 = Intl *nix format)
              move     Date-Form  to PY-PR1-Date-Format.  *> This field may well be redundant
     move     3             to PY-PR1-Date-Yr.        *> Same for both UK abd USA
     if       Date-Form =  2 *> USA
              move     1    to PY-PR1-Date-Mo   *> DITTO
              move     2    to PY-PR1-Date-Dy
     else
              move     2    to PY-PR1-Date-Mo
              move     1    to PY-PR1-Date-Dy.
     move     WSE-Year      to PY-PR2-Last-Day-Last-W (1:4).   *> ccyymmdd
     move     WSE-Month     to PY-PR2-Last-Day-Last-W (5:2).
     move     WSE-Days      to PY-PR2-Last-Day-Last-W (7:2).
*>
     move     PY-PR2-Last-Day-Last-W  to                       *> stored as ccyymmdd
                               PY-PR2-Last-Day-Last-B   *> for all 4.
                               PY-PR2-Last-Day-Last-S
                               PY-PR2-Last-Day-Last-M.
*>
*> Width subject to change depending on report sizes used, etc.
*>
     move     120               to PY-PR1-Page-Width-L.
     move     80                to PY-PR1-Page-Width-P.
*>
     move     "Regular"         to PY-PR1-Rate-Name (1).
     move     "Overtime"        to PY-PR1-Rate-Name (2).
     move     "Spec. Overtime"  to PY-PR1-Rate-Name (3).
     move     "Commission"      to PY-PR1-Rate-Name (4).
*>
     move     Print-Spool-Name  to PY-PR1-Print-Spool-Name.  *> from System Rec fields
     move     Print-Spool-Name2 to PY-PR1-Print-Spool-Name2. *> ditto
     move     Print-Spool-Name3 to PY-PR1-Print-Spool-Name3. *> ditto
     move     WSE-Year          to PY-PR2-Year.
     add      WSE-Year 1    giving PY-PR2-Year-Next.
*>
     move     1 to RRN.
     write    PY-Param1-Record.
     if       PY-PR1-Status not = "00" *> shouldn't be as only just creating it
              rewrite  PY-Param1-Record
              perform  aa125-Test-PR1-Status
              display  space at line WS-23-lines col 1 with erase eos
              display  SY001 at line WS-Lines col 1 foreground-color 4
              close    PY-Param1-File
              move     16 to WS-Term-Code
              goback.
*>
     close    PY-Param1-File.      *> In case opened for output
     open     i-o PY-Param1-File.
*>
*>  Now to  get data blocks via SS.
*>
 ab010-Exit.  exit section.
*>
 ab020-Py-Nominal-Accounts   section.
*>**********************************
*>
*>  Set up delete file for screen save/restore if used via F1 key.
*>
     move     spaces to Path-Work.
     string   ACAS-Path       delimited by space
              "irs-temp.scr"  delimited by size
                                 into Path-Work.
*>
*>  Set up or Amend PY Account file where nominal accts taken
*>   from (1)  IRS or for GL.
*>
     if       PY-PR1-IRS-Used = "Y"      *> Primary & only option at this time
              perform  ab030-Using-IRS
     else
      if      PY-PR1-GL-Used = "Y"
          or  IRS-Both-Used           *> from ACAS system rec
              perform  ab050-Using-GL.
 *>             display  PY114   at line WS-Lines col 1 with erase eol foreground-color 4
 *>             display  SY002        at line WS-Lines col 1
 *>             accept   Accept-Reply at line WS-Lines col 33.
*>
     if       Return-Code = 16
           or WS-Term-Code = 16
              goback.
     go to    ab020-Exit.
*>
*> example calls  performs etc to remind me   <<<<<<<<<<<<<<
*> remove when tested
*>
     perform  acasirsub1-Open.

     perform  acasirsub1-Read-Indexed.

     perform  acasirsub1-Close.

 ab020-Exit.  exit section.
*>
 ab030-Using-IRS             section.
*>**********************************
*>
*> REMEMBER to save in WS-Dflt Cash (1), Liability (2),
*>                     WS-Dflt-Cost (4) & WS-Dflt-Expense ( PY-PR1-Dflt-Dist-Acct )
*>
     move     zero to Return-Code.
     perform  acasirsub1-Open-Input.
     if       WE-Error not = zero
              display  IR912    at line WS-23-lines col 01 with foreground-color cob-color-red erase eol
              display  "21" at line WS-23-lines col 52
              move     21 to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  WS-Eval-Msg at line WS-23-lines col 55
              display  SY003    at line WS-lines col 01 with foreground-color cob-color-red erase eol
              accept   WS-Reply at line WS-lines col 52 AUTO
              perform  acasirsub1-Close
              move     16 to Return-Code
              go       to ab030-Exit.                    *> Cannot continue.
*>
*>  NL nominal # preset only via IRS but numbers used are suspect.
*>   we test that these numers exist & if not, abort this function
*>  do the same if errors exist when writing record
*>  and if error happened clear the act file.
*>
*>  THEREFORE if file is zero size this routined failed regardless of what one of
*>  the four caused it.   BUT should not be happening :(
*>
     move     spaces to WS-Account-Table.         *> Init Table
     open     input    PY-Accounts-File.
     if       PY-Act-Status not = "00"
              close    PY-Accounts-File
              open     output PY-Accounts-File   *> set up the default accounts
              move     1 to ACT-No
              move     "Cash" to ACT-Desc
              move     00274  to ACT-GL-No
              perform  ab035-Find-IRS-Nominal-Acct
              if       we-error not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab030-Continued
              end-if
              move     2 to ACT-No
              move     "Accrued Liability" to ACT-Desc
              move     00180 to ACT-GL-No
              perform  ab035-Find-IRS-Nominal-Acct
              if       we-error not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab030-Continued
              end-if
              move     3 to ACT-No
              move     "Salary Expense" to ACT-Desc
              move     00315 to ACT-GL-No
              perform  ab035-Find-IRS-Nominal-Acct
              if       we-error not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab030-Continued
              end-if
              move     4 to ACT-No
              move     "Accrued Payroll Cost Lia" to ACT-Desc *> Liability
              move     00298 to ACT-GL-No
              perform  ab035-Find-IRS-Nominal-Acct
              if       we-error not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab030-Continued
              end-if
              move     4 to WS-Account-Count
*>
*> THIS does NOT mean that the nominals actually exist but that the four
*>  ACT accounts are on file
*>
     end-if.
*>
 ab030-Continued.
*>
     close    PY-Accounts-File.
     open     i-o PY-Accounts-File.
     move     maps-ser-nn to curs2.
     display  Display-Heads.
     display  SS-Param-7-IRS-Nominal-Accounts.
     display  PY003 at 1610 foreground-color 3. *> Warn about using manual
     display  PY004 at 2010 foreground-color 2. *> 2 quit use Escape.
     display  PY005 at 2210 foreground-color 2. *> 2 display current ACT entries.
     move     1 to File-Key-No.                 *> 1 = Primary
*>
 ab030-Get-Nominal.
     move     zeros to Act-No
                       Act-GL-No.
     move     spaces  to Act-Desc.
     perform  Forever
              accept   Act-No    at 0623 foreground-color 3 UPDATE
              if       Cob-CRT-Status = Cob-Scr-Esc
                       exit perform
              end-if
*>
*> Save screen, show the defaults then restore the prev. screen.
*>
              if       Cob-CRT-Status = Cob-Scr-F1
                       move     z"irs-temp.scr"  to wScreenName
                       call     "scr_dump"    using wScreenName
                                               returning wInt
                       perform  ab040-Show-Accts
                       call     "scr_restore" using wScreenName
                                               returning wInt
                       call     "CBL_DELETE_FILE" using Path-Work
                       move     zeros to Act-No
                       exit perform cycle
              end-if
*>
*> as the 4 have been created not checking for i-o errors
*>
              read     PY-Accounts-File key Act-No
              accept   Act-GL-No at 0823 foreground-color 3 UPDATE
              if       Cob-CRT-Status = Cob-Scr-Esc
                       exit perform
              end-if
*>
              perform  ab035-Find-IRS-Nominal-Acct
              if       we-error = zero
                       move     NL-Name to Act-Desc
              else
                       display  PY116 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                       exit perform cycle
              end-if
              display  space at  line WS-23-Lines col 1 erase eol
              display  Act-Desc  at 0923
*>
              evaluate Act-No
                       when 1 move Act-GL-No to WS-Dflt-Cash
                       when 2 move Act-GL-No to WS-Dflt-Liability
                       when 3 move Act-GL-No to WS-Dflt-Expense  *> ????
                       when 4 move Act-GL-No to WS-Dflt-Cost
                       when other    *> default ?
                              move PY-PR1-Dflt-Dist-Acct to  WS-Dflt-Expense
              end-evaluate
*>
              rewrite  PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       exit perform
              end-if
              move     "Y" to WS-Act-Exists (Act-No)
              exit perform cycle
     end-perform.
     close    PY-Accounts-File.
     perform  acasirsub1-Close.
*>
 ab030-Exit.  exit section.
*>
 ab035-Find-IRS-Nominal-Acct section.
*>**********************************
*>
     move     Act-GL-No to NL-Owning.
     move     zero      to NL-Sub-Nominal.
     perform  acasirsub1-Read-Indexed.
*>
 ab035-Exit.  exit section.
*>
 ab040-Show-Accts            section.
*>**********************************
*>
     move     maps-ser-nn to curs2.
     display  Display-Heads.
     display  SS-Param-7-IRS-Show-Nominal-Accounts.
     start    PY-Accounts-File First.
     if       PY-Act-Status not = "00"
              display  PY006 at line WS-23-Lines col 1 erase eos
              accept   WS-Reply at line WS-23-Lines col 42 AUTO
              go to ab040-Exit.
     move     6 to A.
     perform  forever
              add      1 to A
              if       A > WS-22-Lines
                       display  SY014 at line WS-23-Lines col 1 erase eol
                       accept   WS-Reply at line WS-23-Lines col 32 AUTO
                       display  Display-Heads
                       display  SS-Param-7-IRS-Show-Nominal-Accounts
                       move     7 to A
              end-if
              read     PY-Accounts-File next record at end
                       display PY007    at line WS-23-Lines col 1
                       accept  WS-Reply at line WS-23-Lines col 47 AUTO
                       close   PY-Accounts-File
                       open    i-o PY-Accounts-File
                       exit perform
              end-read
              display  Act-No    at line A col 2
              display  Act-GL-No at line A col 11
              display  Act-Desc  at line A col 20
              exit perform cycle
     end-perform.
*>
 ab040-Exit.  exit section.

 ab050-Using-GL              section.
*>**********************************
*>
*> REMEMBER to save in WS-Dflt Cash (1), Liability (2),
*>                     WS-Dflt-Cost (4) & WS-Dflt-Expense ( PY-PR1-Dflt-Dist-Acct )
*>
     move     zero to Return-Code.
     perform  GL-Nominal-Open-Input.
     if       FS-Reply not = zero
              display  IR912    at line WS-23-lines col 01 with foreground-color cob-color-red erase eol
              display  "21" at line WS-23-lines col 52
              move     21 to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  WS-Eval-Msg at line WS-23-lines col 55
              display  SY003    at line WS-lines col 01 with foreground-color cob-color-red erase eol
              accept   WS-Reply at line WS-lines col 52 AUTO
              perform  GL-Nominal-Close
              move     16 to Return-Code
              go       to ab030-Exit.                    *> Cannot continue.
*>
*>  NL nominal # preset only via IRS but numbers used are suspect.
*>   we test that these numers exist & if not, abort this function
*>  do the same if errors exist when writing record
*>  and if error happened clear the act file.
*>
*>  THEREFORE if file is zero size this routined failed regardless of what one of
*>  the four caused it.   BUT should not be happening :(
*>
     move     spaces to WS-Account-Table.         *> Init Table
     open     input    PY-Accounts-File.
     if       PY-Act-Status not = "00"
              close    PY-Accounts-File
              open     output PY-Accounts-File   *> set up the default accounts
              move     1 to ACT-No
              move     "Cash" to ACT-Desc
              move     00274  to ACT-GL-No
              perform  ab060-Find-GL-Nominal-Acct
              if       FS-Reply not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab050-Continued
              end-if
              move     2 to ACT-No
              move     "Accrued Liability" to ACT-Desc
              move     00180 to ACT-GL-No
              perform  ab060-Find-GL-Nominal-Acct
              if       FS-Reply not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab050-Continued
              end-if
              move     3 to ACT-No
              move     "Salary Expense" to ACT-Desc
              move     00315 to ACT-GL-No
              perform  ab060-Find-GL-Nominal-Acct
              if       FS-Reply not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab050-Continued
              end-if
              move     4 to ACT-No
              move     "Accrued Payroll Cost Lia" to ACT-Desc *> Liability
              move     00298 to ACT-GL-No
              perform  ab060-Find-GL-Nominal-Acct
              if       FS-Reply not = zero
                       move     zeros to ACT-GL-No
              else
                       move     "Y" to WS-Act-Exists (ACT-No)
              end-if
              write    PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       move     space to WS-Act-Exists (ACT-No)
                       close    PY-Accounts-File
                       open     output PY-Accounts-File
                       go to    ab050-Continued
              end-if
              move     4 to WS-Account-Count
*>
*> THIS does NOT mean that the nominals actually exist but that the four
*>  ACT accounts are on file but could have zero in ACT-GL-No
*>
     end-if.
*>
 ab050-Continued.
     close    PY-Accounts-File.
     open     i-o PY-Accounts-File.
     move     maps-ser-nn to curs2.
     display  Display-Heads.
     display  SS-Param-7-IRS-Nominal-Accounts.
     display  PY003 at 1610 foreground-color 3. *> Warn about using manual
     display  PY004 at 2010 foreground-color 2. *> 2 quit use Escape.
     display  PY005 at 2210 foreground-color 2. *> 2 display current ACT entries.
     move     1 to File-Key-No.                 *> 1 = Primary
*>
 ab050-Get-Nominal.
     move     zeros to Act-No
                       Act-GL-No.
     move     spaces  to Act-Desc.
     perform  Forever
              accept   Act-No    at 0623 foreground-color 3 UPDATE
              if       Cob-CRT-Status = Cob-Scr-Esc
                       exit perform
              end-if
*>
*> Save screen, show the defaults then restore the prev. screen.
*>
              if       Cob-CRT-Status = Cob-Scr-F1
                       move     z"irs-temp.scr"  to wScreenName
                       call     "scr_dump"    using wScreenName
                                               returning wInt
                       perform  ab040-Show-Accts
                       call     "scr_restore" using wScreenName
                                               returning wInt
                       call     "CBL_DELETE_FILE" using Path-Work
                       move     zeros to Act-No
                       exit perform cycle
              end-if
*>
*> as the 4 have been created not checking for i-o errors
*>
              read     PY-Accounts-File key Act-No
              accept   Act-GL-No at 0823 foreground-color 3 UPDATE
              if       Cob-CRT-Status = Cob-Scr-Esc
                       exit perform
              end-if
*>
              perform  ab060-Find-GL-Nominal-Acct
              if       FS-Reply = zero
                       move     Ledger-Name to Act-Desc
              else
                       display  PY116 at line WS-23-Lines col 1 foreground-color 6 BEEP erase eos
                       exit perform cycle
              end-if
              display  space at  line WS-23-Lines col 1 erase eol
              display  Act-Desc  at 0923
*>
              evaluate Act-No
                       when 1 move Act-GL-No to WS-Dflt-Cash
                       when 2 move Act-GL-No to WS-Dflt-Liability
                       when 3 move Act-GL-No to WS-Dflt-Expense  *> ????
                       when 4 move Act-GL-No to WS-Dflt-Cost
                       when other    *> default ?
                              move PY-PR1-Dflt-Dist-Acct to  WS-Dflt-Expense
              end-evaluate
*>
              rewrite  PY-Accounts-Record
              if       PY-Act-Status not = "00"
                       perform  aa130-Act-File-Error
                       exit perform
              end-if
              move     "Y" to WS-Act-Exists (Act-No)
              exit perform cycle
     end-perform.
     close    PY-Accounts-File.
     perform  GL-Nominal-Close.
*>
 ab050-Exit.  exit section.
*>
 ab060-Find-GL-Nominal-Acct  section.
*>**********************************
*> result in FS-Reply
*>
     move     Act-GL-No to WS-Ledger-Nos.
     move     zero      to Ledger-pc.
     perform  GL-Nominal-Read-Indexed.
*>
 ab060-Exit.  exit section.
*>
 ab070-PY-DED-Setup          section.
*>**********************************
*>
*> Use content from dedent.bas as src for init setups.
*>  Now preset values from dedent
*>
     initialise
              PY-System-Deduction-Record with FILLER.
*>
     move     "Y" to Ded-SWT-Used
                     Ded-FWT-Used
                     Ded-FICA-Used
                     Ded-CO-FICA-Used
                     Ded-CO-FUTA-Used
                     Ded-CO-SUI-Used.
     move     "N" to Ded-LWT-Used
                     Ded-SDI-Used
                     Ded-EIC-Used.
*>
*> Assuming WS presets now set up via ACT set up
*> #2 default cbasic - check it but ONLY if
*>  PY-PR1-IRS-Used or PY-PR1-GL-Used = "Y"
*>
     if       PY-PR1-IRS-Used = "Y"
          or  PY-PR1-GL-Used = "Y"
              move     WS-Dflt-Liability to Ded-FWT-Acct-No
                                            Ded-SWT-Acct-No
                                            Ded-LWT-Acct-No
                                            Ded-FICA-Acct-No
                                            Ded-SDI-Acct-No
                                            Ded-EIC-Acct-No
*> #4 default cbasic - check it
              move     WS-Dflt-Cost      to Ded-CO-FICA-Acct-No
                                            Ded-CO-FUTA-Acct-No
                                            Ded-CO-SUI-Acct-No.
*>
     perform  varying A from 1 by 1 until A > 5
              if       A > 5
                       exit perform
              end-if
              move     "N"             to Ded-Sys-Used (A)
              move     "E"             to Ded-Sys-Earn-Ded (A)
              move     "A"             to Ded-Sys-Amt-Percent (A)
              move     7               to Ded-Sys-Chk-Cat (A)
              move     1               to Ded-Sys-Exclusion (A)
              move     "Y"             to Ded-Sys-Limit-Used (A)
              if       PY-PR1-IRS-Used = "Y"
                   or  PY-PR1-GL-Used = "Y"
                       move     WS-Dflt-Expense to Ded-Sys-Acct-No (A)
              end-if
     end-perform.
*>
*> Other presets for allowances from dedend.bas but Out Of Date
*>  but changable in menu options
*>
     move     1000    to Ded-FWT-Allowance-Amt.
     move     2400    to Ded-FWT-Mar-Cutoff (1).
     move     6600    to Ded-FWT-Mar-Cutoff (2).
     move     10900   to Ded-FWT-Mar-Cutoff (3).
     move     15000   to Ded-FWT-Mar-Cutoff (4).
     move     19200   to Ded-FWT-Mar-Cutoff (5).
     move     23600   to Ded-FWT-Mar-Cutoff (6).
     move     28900   to Ded-FWT-Mar-Cutoff (7).
     move     15      to Ded-FWT-Mar-Percent (1).
     move     18      to Ded-FWT-Mar-Percent (2).
     move     21      to Ded-FWT-Mar-Percent (3).
     move     24      to Ded-FWT-Mar-Percent (4).
     move     28      to Ded-FWT-Mar-Percent (5).
     move     32      to Ded-FWT-Mar-Percent (6).
     move     37      to Ded-FWT-Mar-Percent (7).
*>
     move     1420    to Ded-FWT-Sin-Cutoff (1).
     move     3300    to Ded-FWT-Sin-Cutoff (2).
     move     6800    to Ded-FWT-Sin-Cutoff (3).
     move     10200   to Ded-FWT-Sin-Cutoff (4).
     move     14200   to Ded-FWT-Sin-Cutoff (5).
     move     17200   to Ded-FWT-Sin-Cutoff (6).
     move     22500   to Ded-FWT-Sin-Cutoff (7).
     move     15      to Ded-FWT-Sin-Percent (1).
     move     18      to Ded-FWT-Sin-Percent (2).
     move     21      to Ded-FWT-Sin-Percent (3).
     move     24      to Ded-FWT-Sin-Percent (4).
     move     26      to Ded-FWT-Sin-Percent (5).
     move     30      to Ded-FWT-Sin-Percent (6).
     move     39      to Ded-FWT-Sin-Percent (7).
*>
     move     6.13    to Ded-FICA-Rate.
     move     6.13    to Ded-CO-FICA-Rate.
     move     1       to Ded-SDI-Rate.
     move     3.4     to Ded-CO-FUTA-Rate.
     move     2.7     to Ded-CO-FUTA-Max-Credit.
     move     zero    to Ded-CO-SUI-Rate.
     move     10      to Ded-EIC-Rate.
     move     12.5    to Ded-EIC-Excess-Rate.
     move     25900   to Ded-FICA-Limit.
     move     25900   to Ded-CO-FICA-Limit.
     move     6000    to Ded-SDI-Limit.
     move     6000    to Ded-CO-FUTA-Limit
     move     6000    to Ded-CO-SUI-Limit.
     move     5000    to Ded-EIC-Limit.
     move     6000    to Ded-EIC-Excess-Limit.
*>
     move     1 to RRN.
     write    PY-System-Deduction-Record. *> Not created yet
     if       PY-Ded-Status not = "00"
              perform  aa110-Eval-Ded-Write
              display  SY001 at line WS-23-Lines col 1 foreground-color 6 BEEP
                                                       erase eos
              accept   WS-Reply at line WS-23-Lines col 48 AUTO
              close    PY-System-Deduction-File
              move     16 to WS-Term-Code
              goback   returning 16.
*>
 ab070-Exit.   exit section.
*>
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
     move     TEST-DATE-YYYYMMDD(WS-Test-YMD) to A.

 zz010-Exit.  exit section.
*>
*> zz020-Display-Heads         section.
*>**********************************
*>
*>     display  " " at 0101 with erase eos.
*>     display  Prog-Name              at 0101 with foreground-color 2.
*>     display  WS-Heading             at 0131 with foreground-color 2.
*>     move     To-Day to WS-Date.
*>     perform  zz070-Convert-Date.
*>     display  WS-Date                at 0171 with foreground-color 2.
*>
*> zz020-Exit.  exit section.
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
     exit     section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-Test-Date
*> output:  U-Date/WS-Date as uk date format
*>          U-Bin not zero if valid date
*>
*>     move     WS-Test-Date to WS-Date.
*>     if       Date-Form = zero
*>              move 1 to Date-Form.
*>     if       Date-UK
*>              go to zz050-Test-Date.
*>     if       Date-USA                *> swap month and days
*>              move WS-Days  to WS-Swap
*>              move WS-Month to WS-Days
*>              move WS-Swap  to WS-Month
*>              go to zz050-Test-Date.
*>*>
*>*> So its International date format
*>*>
*>     move     "dd/mm/ccyy" to WS-Date.  *> swap Intl to UK form
*>     move     WS-Test-Date (1:4) to WS-Year.
*>     move     WS-Test-Date (6:2) to WS-Month.
*>     move     WS-Test-Date (9:2) to WS-Days.
*>*>
*> zz050-Test-Date.
*>     move     WS-Date to U-Date.
*>     move     zero to U-Bin.
*>     perform  maps04.
*>*>
*> zz050-exit.
*>     exit     section.
*>
*> zz060-Convert-Date        section.
*>********************************
*>
*>  Converts date in binary to UK/USA/Intl date format
*>****************************************************
*> Input:   U-Bin
*> output:  WS-Date as uk/US/Inlt date format
*>          U-Date & WS-Date = spaces if invalid date
*>
*>     perform  maps04.
*>     if       U-Date = spaces
*>              move spaces to WS-Date
*>              go to zz060-Exit.
*>     move     U-Date to WS-Date.
*>*>
*>     if       Date-Form = zero
*>              move 1 to Date-Form.
*>     if       Date-UK
*>              go to zz060-Exit.
*>     if       Date-USA                *> swap month and days
*>              move WS-Days  to WS-Swap
*>              move WS-Month to WS-Days
*>              move WS-Swap  to WS-Month
*>              go to zz060-Exit.
*>
*> So its International date format
*>
*>     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
*>     move     U-Date (7:4) to WS-Intl-Year.
*>     move     U-Date (4:2) to WS-Intl-Month.
*>     move     U-Date (1:2) to WS-Intl-Days.
*>*>
*> zz060-Exit.
*>     exit     section.
*>
 zz070-Convert-Date          section.
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
 maps04.
*>******
*>
     call     "maps04"  using  Maps03-WS.
*>
 maps04-Exit. exit.
*>
*>C      copy "an-accept.pl".
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
*>
*>C      copy "Proc-ZZ100-ACAS-IRS-Calls.cob"
*>C           replacing LEADING ==zz100-== by ==ZZ900-==.
*>
 zz100-ACAS-IRS-Calls  section.
*>============================
*>
*>  USED THROUGHTOUT IRS but Map out by using a dummy 03 all
*>   unused acasirsubn routines [see 01  Dummies-For-Unused-FH-Calls].
*>
*> All of the calls to irsub1 - 5 remapped to acasirsub1 - 5.
*>        All require changes to code for param etc.
*>
*>  Uses messages:  IR911, IR912, IR913, IR915, IR916. (Was IR011 - 16.
*>
*>  Note irsub2 is replaced by acas000 with File-Key-No=1
*> ******************************************************
*>
*> acas000     =  System parameter file processing with File-Key-No=1
*>
*> Changes:
*> 29/04/18 vbc - 1.01 - Changed all accessing other than open with 1st line of
*>                       move zero to Access-Type to keep logging clean.
*>
 acas000.
*>
     move     1 to File-Key-No.               *> 1 = Primary as only used.
     call     "acas000" using
                                WS-System-Record
                                File-Access
                                File-Defs
                                ACAS-DAL-Common-data
     end-call.
*>
*> acas008     =  SL/PL Posting file processing
*>
 acas008.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acas008" using WS-System-Record
                              WS-IRS-Posting-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
*> acasirsub1  =  NL (Nominal Ledger) processing.
*>
 acasirsub1.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub1" using WS-System-Record
                                 WS-IRSNL-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*> acasirsub3  =  Dflit (Default) processing.
*>
 acasirsub3.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub3" using WS-System-Record
                                 WS-IRS-Default-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*> acasirsub4  =  Posting processing.
*>
 acasirsub4.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub4" using WS-System-Record
                                 Posting-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*> acasirsub5  =  Final processing.
*>
 acasirsub5.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub5" using WS-System-Record
                                 Final-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*>
 acas000-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas000.
     perform  acas000-Check-4-Errors.
*>
 acas000-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas000-Check-4-Errors.
     perform  acas000.
*>
 acas000-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas000.
*>
 acas000-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas000.
*>
 acas000-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas000.
*>
 acas000-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas000.
*>
 acas000-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acas000.
*>
*>
 acas008-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas008.
     perform  acas008-Check-4-Errors.
*>
 acas008-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas008.
     perform  acas008-Check-4-Errors.
*>
 acas008-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas008.
     perform  acas008-Check-4-Errors.
*>
 acas008-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas008.
*>
 acas008-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas008.
*>
 acas008-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas008.
*>
 acas008-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acas008.
*>
*>
 acasirsub1-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub1.
     perform  irsub1-Check-4-Errors.
*>
 acasirsub1-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub1.
     perform  irsub1-Check-4-Errors.
*>
 acasirsub1-Open-Output.
     set      fn-open  to true.
     set      fn-output to true.
     perform  acasirsub1.
     perform  irsub1-Check-4-Errors.
*>
 acasirsub1-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub1.
*>
 acasirsub1-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub1.
*>
 acasirsub1-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acasirsub1.
*>
 acasirsub1-Start.
     move     zero to Access-Type.
     set      fn-Start to true.
     perform  acasirsub1.
*>
 acasirsub1-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub1.
*>
 acasirsub1-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     perform  acasirsub1.
*>
 acasirsub1-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub1.
*>
*>
 acasirsub3-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub3.
     perform  irsub3-Check-4-Errors.
*>
 acasirsub3-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub3.
     perform  irsub3-Check-4-Errors.
*>
 acasirsub3-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub3.
*>
 acasirsub3-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub3.
*>
 acasirsub3-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub3.
*>
 acasirsub3-ReWrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub3.
*>
*>
 acasirsub4-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub4.
*>
 acasirsub4-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub4.
*>
 acasirsub4-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub4.
*>
 acasirsub4-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub4.
*>
 acasirsub4-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub4.
*>
 acasirsub4-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub4.
*>
*>
 acasirsub5-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub5.
     perform  irsub5-Check-4-Errors.
*>
 acasirsub5-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub5.
     perform  irsub5-Check-4-Errors.
*>
 acasirsub5-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub5.
*>
 acasirsub5-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub5.
*>
 acasirsub5-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub5.
*>
 acasirsub5-ReWrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub5.
*>
*>
 acas000-Check-4-Errors.
     if       fs-reply not = zero
              display IR911            at 0801   *> acas000/systemMT processing
              perform acas000-Close
              go to Open-Error-Continued
     end-if.
*>
 acas008-Check-4-Errors.
     if       fs-reply not = zero
              display IR916            at 0801   *> acas008/slpostingMT processing
              perform acas008-Close
              go to Open-Error-Continued
     end-if.
*>
 irsub1-Check-4-Errors.
     if       fs-reply not = zero
              display IR912            at 0801   *> acasirsub1/irsnominalMT processing
              perform  acasirsub1-Close
              go to Open-Error-Continued
     end-if.
*>
 irsub3-Check-4-Errors.
     if       fs-reply not = zero
              display IR913            at 0801   *> acasirsub3/irsdfltMT processing
              perform  acasirsub3-Close
              go to Open-Error-Continued
     end-if.
*>
 irsub5-Check-4-Errors.
     if       fs-reply not = zero
              display IR915            at 0801   *> acasirsub5/irsfinalMT processing
              perform  acasirsub5-Close
              go to Open-Error-Continued
     end-if.
*>
 Open-Error-Continued.   *> If here we cannot continue as its a major failure
     display  "Fs-reply = "    at 0901
     display  fs-reply         at 0912
     display  "WE-Error = "    at 1001
     display   WE-Error        at 1012
     display  SQL-Err          at 1101
     display  SQL-Msg          at 1201
     display  SY008            at 1301 with erase eol
     accept   Accept-Reply     at 1335.
     goback.
*>
 ZZ100-Exit.
     exit section.
*>>W Msg29 Caution: One or more replacing sources not found
  *>                  ==zz100-Exit== by ZZ900-Exit==.   *> FOR IRS handling CoA file.
*>
*>C      copy "Proc-ACAS-FH-Calls.cob"   *> FOR GL file handler CoA file.
*>C           replacing LEADING  ==ZZ080-== by ==ZZ910-==
*>C                     System-Record by WS-System-Record.
*>>>LISTING OFF
*>
 zz080-ACAS-Processes      section.
*>********************************
*>
*> 18/04/17 vbc - 1.01 - Added new function Invoice-Read-Next-Header
*>                       for use with sl020, 050, 140.
*> 23/04/17 vbc - 1.02 - Added new calls for acas26 & 029 for P/L.
*> 25/04/17 vbc - 1.03 - Added acas000-Open-Input as open I/O will create if not exist
*>                       MUST WATCH OUT FOR THIS FOR THE OTHERS <<<<<
*> 12/01/18 vbc -      - IRS FH and DALs are not in this copybook although the IRS posting file
*>                       which is an optional input to IRS is as sl, pl, st can use it..
*> 16/01/18 vbc - 1.04 - Added Value-Delete-All for xl150.
*> 29/04/18 vbc - 1.05 - Changed all accessing other than open with 1st line of
*>                       move zero to Access-Type to keep logging clean.
*> 02/05/23 vbc - 1.06 - Add SLautogen & acas004, PLautogen & acas030
*> 09/05/23 vbc   1.07 - Above amended names to SL/PLautogen.
*> 14/08/23 vbc - 1.08 - Remove 'move zero to access-type for Start, it is set !!!
*>
 acas000.       *> System and dflt, final and system-record-4 NOTE that this FH only has four
 *>                                           parameters (no system-record from FD)
 call

  "acas000" using WS-System-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas004.       *> SLautogen
     move     1  to File-Key-No.
 call

  "acas004" using WS-System-Record
                              WS-Invoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas005.       *> GL Nominal Ledger
     move     1  to File-Key-No.
 call

  "acas005" using WS-System-Record
                              WS-Ledger-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas006.       *> GL Posting
     move     1  to File-Key-No.
 call

  "acas006" using WS-System-Record
                              WS-Posting-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas007.       *> GL Batch
     move     1  to File-Key-No.
 call

  "acas007" using WS-System-Record
                              WS-Batch-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas008.       *> SPL Posting
     move     1  to File-Key-No.
 call

  "acas008" using WS-System-Record
                              WS-IRS-Posting-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas010.       *> Stock Audit   Non ISAM type file/table
     move     1  to File-Key-No.
 call

  "acas010" using WS-System-Record
                              WS-Stock-Audit-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas011.       *> Stock    *> This one can use 3 File Key nos 1 - 3
 call

  "acas011" using WS-System-Record
                              WS-Stock-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas012.       *> Sales Ledger
     move     1  to File-Key-No.
 call

  "acas012" using WS-System-Record
                              WS-Sales-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas013.       *>  Value
     move     1  to File-Key-No.
 call

  "acas013" using WS-System-Record
                              WS-Value-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.

*>
 acas014.       *>  Delivery
     move     1  to File-Key-No.
 call

  "acas014" using WS-System-Record
                              WS-Delivery-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.

*>
 acas015.       *> Analysis
     move     1  to File-Key-No.
 call

  "acas015" using WS-System-Record
                              WS-Analysis-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas016.       *> Invoice
     move     1  to File-Key-No.
 call

  "acas016" using WS-System-Record
                              WS-Invoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas017.       *> DelInvNo
     move     1  to File-Key-No.
 call

  "acas017" using WS-System-Record
                              WS-Del-Inv-Nos-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas019.       *> Open-Item-3
     move     1  to File-Key-No.
 call

  "acas019" using WS-System-Record
                              WS-OTM3-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas022.       *> Purchase Ledger
     move     1  to File-Key-No.
 call

  "acas022" using WS-System-Record
                              WS-Purch-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas023.       *> Delete Folio
     move     1  to File-Key-No.
 call

  "acas023" using WS-System-Record
                              WS-Del-Inv-Nos-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas026.       *> PInvoice
     move     1  to File-Key-No.
 call

  "acas026" using WS-System-Record
                              WS-PInvoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas029.       *> Open-Item-5
     move     1  to File-Key-No.
 call

  "acas029" using WS-System-Record
                              WS-OTM5-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas030.       *> PLautogen
     move     1  to File-Key-No.
 call

  "acas030" using WS-System-Record
                              WS-PInvoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas032.       *> Purchase Payments
     move     1  to File-Key-No.
 call

  "acas032" using WS-System-Record
                              WS-Pay-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
*>  These are for acas000
*>
 System-Open.
 *>    set      fn-open  to true.
     move     1  to File-Function.
 *>    set      fn-i-o to true.
     move     2 to Access-Type.
     perform  acas000.
*>
 System-Open-Input.
 *>    set      fn-open  to true.
     move     1  to File-Function.
 *>    set      fn-Input to true.
     move    1 to Access-Type.
     perform  acas000.
*>
 System-Open-Output.
 *>    set      fn-open  to true.
     move     1  to File-Function.
 *>    set      fn-Output to true.
     move    3 to Access-Type.
     perform  acas000.
*>
 System-Close.
     move     zero to Access-Type.
 *>    set      fn-Close to true.
     move     2  to File-Function.
     perform  acas000.
*>
 System-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas000.
*>
 System-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas000.
*>
 System-ReWrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acas000.
*>
*> These are for acas004
*>
 SLautogen-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas004.
*>
 SLautogen-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas004.
*>
 SLautogen-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas004.
*>
 SLautogen-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas004.
*>
 SLautogen-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas004.
*>
 SLautogen-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas004.
*>
 SLautogen-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas004.
*>
 SLautogen-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas004.
*>
 SLautogen-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas004.
*>
 SLautogen-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas004.
*>
 SLautogen-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas004.
*>
 SLautogen-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas004.
*>
*>  These are for acas005
*>
 GL-Nominal-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas005.
*>
 GL-Nominal-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas005.
*>
 GL-Nominal-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas005.
*>
 GL-Nominal-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas005.
*>
 GL-Nominal-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas005.
*>
 GL-Nominal-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas005.
*>
 GL-Nominal-Start.
     set      fn-Start to true.
     perform  acas005.
*>
 GL-Nominal-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas005.
*>
 GL-Nominal-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas005.
*>
 GL-Nominal-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas005.
*>
 GL-Nominal-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas005.
*>
*>  These are for acas006
*>
 GL-Posting-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas006.
*>
 GL-Posting-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas006.
*>
 GL-Posting-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas006.
*>
 GL-Posting-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas006.
*>
 GL-Posting-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas006.
*>
 GL-Posting-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas006.
*>
 GL-Posting-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas006.
*>
 GL-Posting-Start.
     set      fn-Start to true.
     perform  acas006.
*>
 GL-Posting-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas006.
*>
 GL-Posting-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas006.
*>
 GL-Posting-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas006.
*>
 GL-Posting-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas006.
*>
*>  These are for acas007
*>
 GL-Batch-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas007.
*>
 GL-Batch-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas007.
*>
 GL-Batch-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas007.
*>
 GL-Batch-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas007.
*>
 GL-Batch-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas007.
*>
 GL-Batch-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas007.
*>
 GL-Batch-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas007.
*>
 GL-Batch-Start.
     set      fn-Start to true.
     perform  acas007.
*>
 GL-Batch-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas007.
*>
 GL-Batch-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas007.
*>
 GL-Batch-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas007.
*>
 GL-Batch-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas007.
*>
*>  These are for acas008
*>
 SPL-Posting-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas008.
*>
 SPL-Posting-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas008.
*>
 SPL-Posting-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas008.
*>
 SPL-Posting-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas008.
*>
 SPL-Posting-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas008.
*>
 SPL-Posting-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas008.
*>
 SPL-Posting-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas008.
*>
 SPL-Posting-Start.
     set      fn-Start to true.
     perform  acas008.
*>
 SPL-Posting-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas008.
*>
 SPL-Posting-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas008.
*>
 SPL-Posting-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas008.
*>
 SPL-Posting-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas008.
*>
*>  These are for acas010
*>
 Stock-Audit-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas010.
*>
 Stock-Audit-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas010.
*>
 Stock-Audit-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas010.
*>
 Stock-Audit-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas010.
*>
 Stock-Audit-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas010.
*>
 Stock-Audit-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas010.
*>
 Stock-Audit-Start.
     set      fn-Start to true.
     perform  acas010.
*>
 Stock-Audit-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas010.
*>
 Stock-Audit-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas010.
*>
 Stock-Audit-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas010.
*>
 Stock-Audit-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas010.
*>
*> These are for acas011
*>
 Stock-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas011.
*>
 Stock-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas011.
*>
 Stock-Open-Output.
     set      fn-open to true.
     set      fn-output  to true.
     perform  acas011.
*>
 Stock-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas011.
*>
 Stock-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas011.
*>
 Stock-Start.
     set      fn-Start to true.
     perform  acas011.
*>
 Stock-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas011.
*>
 Stock-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas011.
*>
 Stock-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas011.
*>
 Stock-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas011.
*>
*> These are for acas012
*>
 Sales-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas012.
*>
 Sales-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas012.
*>
 Sales-Open-Output.
     set      fn-open to true.
     set      fn-output  to true.
     perform  acas012.
*>
 Sales-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas012.
*>
 Sales-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas012.
*>
 Sales-Start.
     set      fn-Start to true.
     perform  acas012.
*>
 Sales-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas012.
*>
 Sales-Read-Next-Sorted-By-Name.
     move     zero to Access-Type.
     set      fn-Read-By-Name to true.
     perform  acas012.
*>
 Sales-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas012.
*>
 Sales-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas012.
*>
 Sales-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas012.
*>
*>  These are for acas013
*>
 Value-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas013.
*>
 Value-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas013.
*>
 Value-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas013.
*>
 Value-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas013.
*>
 Value-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas013.
*>
 Value-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas013.
*>
 Value-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas013.
*>
 Value-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas013.
*>
 Value-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas013.
*>
 Value-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas013.
*>
 Value-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas013.
*>
*>  These are for acas014
*>
 Delivery-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas014.
*>
 Delivery-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas014.
*>
 Delivery-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas014.
*>
 Delivery-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas014.
*>
 Delivery-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas014.
*>
 Delivery-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas014.
*>
 Delivery-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas014.
*>
 Delivery-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas014.
*>
 Delivery-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas014.
*>
 Delivery-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas014.
*>
 Delivery-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas014.
*>
*> These are for acas015
*>
 Analysis-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas015.
*>
 Analysis-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas015.
*>
 Analysis-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas015.
*>
 Analysis-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas015.
*>
 Analysis-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas015.
*>
 Analysis-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas015.
*>
 Analysis-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas015.
*>
 Analysis-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas015.
*>
 Analysis-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas015.
*>
 Analysis-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas015.
*>
*> These are for acas016
*>
 Invoice-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas016.
*>
 Invoice-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas016.
*>
 Invoice-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas016.
*>
 Invoice-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas016.
*>
 Invoice-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas016.
*>
 Invoice-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas016.
*>
 Invoice-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas016.
*>
 Invoice-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas016.
*>
 Invoice-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas016.
*>
 Invoice-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas016.
*>
 Invoice-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas016.
*>
 Invoice-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas016.
*>
*> These are for acas017
*>
 DelInvNos-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas017.
*>
 DelInvNos-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas017.
*>
 DelInvNos-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas017.
*>
 DelInvNos-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas017.
*>
 DelInvNos-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas017.
*>
 DelInvNos-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas017.
*>
 DelInvNos-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas017.
*>
 DelInvNos-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas017.
*>
 DelInvNos-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas017.
*>
 DelInvNos-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas017.
*>
 DelInvNos-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas017.
*>
*> These are for acas019
*>
 OTM3-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas019.
*>
 OTM3-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas019.
*>
 OTM3-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas019.
*>
 OTM3-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas019.
*>
 OTM3-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas019.
*>
 OTM3-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas019.
*>
 OTM3-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas019.
*>
 OTM3-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas019.
*>
 OTM3-Read-Next-Sorted-By-Batch.
     move     zero to Access-Type.
     set      fn-Read-By-Batch to true.
     perform  acas019.
*>
 OTM3-Read-Next-Sorted-By-Cust.
     move     zero to Access-Type.
     set      fn-Read-By-Cust to true.
     perform  acas019.
*>
 OTM3-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas019.
*>
 OTM3-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas019.
*>
*> These are for acas022
*>
 Purch-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas022.
*>
 Purch-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas022.
*>
 Purch-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas022.
*>
 Purch-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas022.
*>
 Purch-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas022.
*>
 Purch-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas022.
*>
 Purch-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas022.
*>
 Purch-Read-Next-Sorted-ByName.
     move     zero to Access-Type.
     set      fn-Read-By-Name to true.
     perform  acas022.
*>
 Purch-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas022.
*>
 Purch-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas022.
*>
 Purch-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas022.
*>
*> These are for acas023
*>
 DelFolio-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas023.
*>
 DelFolio-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas023.
*>
 DelFolio-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas023.
*>
 DelFolio-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas023.
*>
 DelFolio-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas023.
*>
 DelFolio-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas023.
*>
 DelFolio-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas023.
*>
 DelFolio-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas023.
*>
 DelFolio-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas023.
*>
 DelFolio-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas023.
*>
 DelFolio-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas023.
*>
*> These are for acas026
*>
 PInvoice-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas026.
*>
 PInvoice-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas026.
*>
 PInvoice-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas026.
*>
 PInvoice-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas026.
*>
 PInvoice-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas026.
*>
 PInvoice-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas026.
*>
 PInvoice-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas026.
*>
 PInvoice-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas026.
*>
 PInvoice-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas026.
*>
 PInvoice-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas026.
*>
 PInvoice-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas026.
*>
 PInvoice-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas026.
*>
*> These are for acas029
*>
 OTM5-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas029.
*>
 OTM5-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas029.
*>
 OTM5-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas029.
*>
 OTM5-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas029.
*>
 OTM5-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas029.
*>
 OTM5-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas029.
*>
 OTM5-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas029.
*>
 OTM5-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas029.
*>
 OTM5-Read-Next-Sorted-By-Batch.
     move     zero to Access-Type.
     set      fn-Read-By-Batch to true.
     perform  acas029.
*>
 OTM5-Read-Next-Sorted-By-Cust.
     move     zero to Access-Type.
     set      fn-Read-By-Cust to true.
     perform  acas029.
*>
 OTM5-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas029.
*>
 OTM5-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas029.
*>
*>  02/05/23
*> These are for acas030 - PLautogen
*>
 PLautogen-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas030.
*>
 PLautogen-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas030.
*>
 PLautogen-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas030.
*>
 PLautogen-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas030.
*>
 PLautogen-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas030.
*>
 PLautogen-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas030.
*>
 PLautogen-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas030.
*>
 PLautogen-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas030.
*>
 PLautogen-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas030.
*>
 PLautogen-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas030.
*>
 PLautogen-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas030.
*>
 PLautogen-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas030.
*>
*> These are for acas032
*>
 Payments-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas032.
*>
 Payments-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas032.
*>
 Payments-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas032.
*>
 Payments-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas032.
*>
 Payments-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas032.
*>
 Payments-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas032.
*>
 Payments-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas032.
*>
 Payments-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas032.
*>
 Payments-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas032.
*>
 Payments-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas032.
*>
 Payments-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas032.
*>
 zz080-Exit.
     exit section.
*>
*>>>LISTING ON
*>>W Msg29 Caution: One or more replacing sources not found
*>
      *>>>Info: Total Copy Depth Used = 03;  Caution messages issued =   5
