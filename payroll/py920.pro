       >>source free
*>****************************************************************
*>                  Account Number Maintenance                   *
*>                        and Reporting                          *
*>                                                               *
*>            Uses RW (Report writer for prints)                 *
*>                                                               *
*>     REMOVE UN-USED variables and procedure div routines *   <<<<<<
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       py920.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 19/10/2025.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Account number Maintanence.
*>                       This program uses RW (Report Writer).
*>
*>                      Semi-sourced from Basic code from fpyactent
*>                      into py900 - initial Parameter set up.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.
*>                      (CBL_) ACCEPT_NUMERIC.c as static. ->  NOT USED.
*>                      ACAS000               USER
*>                      ACAS008               USER
*>                      ACASIRSUB1            USER
*>                      ACASIRSUB3            USER
*>                      ACASIRSUB4            USER
*>                      ACASIRSUB5            USER
*>                      CBL_DELETE_FILE       SYSTEM
*>                      MAPS04                USER
*>                      SCR_DUMP              USER
*>                      SCR_RESTORE           USER
*>                      SYSTEM                SYSTEM
*>
*>**
*>    Functions Used:
*>                      UPPER-CASE
*>                      CURRENT-DATE.
*>    Files used :
*>                      pypr1.   Params
*>                      pyact.   Noninal Account. For IRS.
*>
*>    Error messages used.   CHANGES NEEDED <<<<<<<<<<
*> System wide:
*>                      SY001 - 3, 8, 10, 13, 14.
*> Program specific:
*>                      PY001 - 7.
*>                      PY101, 116 - 118, 125- 126.
*>                      IR911 - 916.  [ For IRS handling ]
*>**
*> Changes:
*> 20/09/2025 vbc - 1.0.00 Created - starting. Prior to testing.
*>                         After testing version will be set to v3.3.
*>                         WARNING: You MUST set the terminal program to be 80
*>                          cols wide and MORE than 25 lines deep and this is to
*>                          allow for the some of the extra lines beyond 24 to
*>                          be used as areas for the warning or error messages
*>                          to be displayed. 26 lines is the minimum.
*>                          This procedure must be applied at all times when
*>                          running Payroll.
*>                          For almost all terminal programs, can be achieved
*>                          by pulling the left and bottom edges of the terminal
*>                          screen with the mouse and holding right button and
*>                          pulling until the correct number is displayed, and
*>                          doing so, one at a time or pulling bottom right
*>                          corner.
*> 30/10/2025 vbc -        Still working on file rec layouts (ws) + selects(sel)
*>                         & fd's (fd).
*> 05/11/2025 vbc -        Adding more SS for data input or display and menus.
*>                         Some of which may well go into another program.
*> 21/11/2025 vbc -        Code taken from py900 Account processing ONLY.
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
*> 09/12/2025 vbc -        Increased minimum screen depth = 28.
*> 24/03/2026 vbc -    .03 Forgot to Read the param file as data is required.
*>
*>   REMEMBER, REMEMBER to change code in PY910 & PY920 to match these changes.
*>
*>*************************************************************************
*>
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
*>
*>C  copy "selprint.cob".
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
*>
 01  PY-Param1-Record.
     03  PY-PR1-Block.                         *> Size = 863
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
         05  PY-PR1-Max-Ed-Cats       binary-char.  *>
         05  PY-PR1-Max-Swt-Entries   binary-char.  *>            A / marks in use for any one line
         05  PY-PR1-Lo-Ded-Chk-Cat    binary-char.  *>
         05  PY-PR1-Hi-Ded-Chk-Cat    binary-char.  *>
         05  PY-PR1-Lo-Earn-Chk-Cat   binary-char.  *>
         05  PY-PR1-Hi-Earn-Chk-Cat   binary-char.  *>
         05  PY-PR1-Max-Sys-Eds       binary-char.  *> 5
*>
         05  PY-PR1-Print-Control.
             07  PY-PR1-Print-Spool-Name  pic x(48). *> All 3 from ACAS system params
             07  PY-PR1-Print-Spool-Name2 pic x(48). *> but only 1st used (or is it)
             07  PY-PR1-Print-Spool-Name3 pic x(48). *>  consider creating a pdf file from prt-1
             07  PY-PR1-Prnt-Ctl-Flag     pic x.        *>  Font etc control needed/used (Def N)
             07  PY-PR1-Font-Small        pic x(32).
             07  PY-PR1-Font-Normal       pic x(32).
             07  PY-PR1-Font-Reset        pic x(32). *> + 97
             07  PY-PR1-Colour-1          pic x(32). *> + 129
             07  PY-PR1-Colour-2          pic x(32). *> + 161
             07  PY-PR1-Colour-Reset      pic x(32). *> + 193
*>
     03  PY-PR2-Block.                        *> Size = 97  COULD BE REC 2 ? (+ filler = 640 or 768 etc) (RRN = 2). sizes wrong
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
         05  PY-PR2-Last-Check-No     pic 9(15). *> 000000     - 12/02/79 pr2.last.check.no$    = last check number written by PYCHECKS
*>
     03  filler                       pic x(64).
*>
*> IPYPR2 - payroll chainging parameter record description
*>        12/02/79 pr2.no.of.xx.applies% number of sm, wb applies this quarter
*>        12/02/79 pr2.just.closed.year% no applies run since year end close
*>        12/02/79 pr2.last.check.no$    last check number written by PYCHECKS
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
*>
 fd  Print-File
     report Account-File-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(15) value "PY920 (1.0.03)".  *> First release pre testing.
*>
*>
*>  This will print 1 copy to CUPS print spool specified on line 3
*>
*>C  copy "print-spool-command-p.cob".     *> CHECK PRN file for content
*>
*> 2023/02/18 vbc - Added PP-Name and Print-File-Name - Portrait
*>
 01  Print-Report.
     03  filler          pic x(117)     value
     "lpr -r -o 'orientation-requested=3 page-left=36 page-top=24 " &
     "page-right=24 sides=two-sided-long-edge cpi=12 lpi=8' -P ".
     03  PSN             pic x(48)      value "Smart_Tank_7300 ".  *> This is the Cups print spool, change it for yours
     03  PP-Name         pic x(24)      value "prt-1".      *> Don't change this line 2023-02-18 chngd from 15
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
     03  PY-Act-Status       pic xx.
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
     03  WS-Page-Lines       binary-char unsigned value 56.   *> 16/12/24 as system is for Portrait and Landscape used.
     03  WS-Rec-Cnt          pic 99       value zero.
*>
*> The following for GC and screen with *nix NOT tested with Windows
*>
 01  wScreenName             pic x(256).
 01  wInt                    binary-long.
*>
 01  WS-Defaults.     *> From Cbasic dedant   Used in DED processing  < taken from ACT records
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
*> Next one MUST be same size as the WS-Act-Exist occurs.
 01  WS-Account-Table-Size   pic 99  value 99.
 01  WS-Account-Count        pic 99  value zero.
*>
 01  Error-Messages.
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY002           pic x(31) value "SY002 Note error and hit Return".
     03  SY003           pic x(51) value "SY003 Aborting function - Note error and hit Return".
*>     03  SY004           pic x(20) value "SY004 Now Hit Return".
*>     03  SY005           pic x(18) value "SY005 Invalid Date".
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
*>
*> Module specific    <<<< REMOVE UNUSED
*>
     03  PY101           pic x(31) value "PY101 Invalid option, try again".
*>     03  PY102           pic x(36) value "PY102 Bad Parameter Data - Try again".
*>     03  PY103           pic x(29) value "PY103 Bad value for Debugging".
*>     03  PY104           pic x(32) value "PY104 Bad value for Pay Interval".
*>     03  PY105           pic x(31) value "PY105 Bad value for Date Format".
*>     03  PY106           pic x(33) value "PY106 Bad value Qtr - Range 1 - 4".
*>     03  PY107           pic x(37) value "PY107 Bad value Lines - Range 40 - 89".
*>     03  PY108           pic x(38) value "PY108 Bad Exclusion code - Range 1 - 4".
*>     03  PY109           pic x(38) value "PY109 Bad Pay Interval - not = S,M,B,W".
*>     03  PY110           pic x(27) value "PY110 Pay Type not = H or S".
*>     03  PY111           pic x(28) value "PY111 GL Iface not = Y,N,I,B".
*>     03  PY112           pic x(33) value "PY112 Check printing not = Y or N".
*>     03  PY113           pic x(28) value "PY113 Void checks not Y or N".
*>     03  PY114           pic x(35) value "PY114 IRS not set to use, in Params".
*>     03  PY115           pic x(52) value "PY115 E/D Must be D or E : E = Earning D = Deduction". *> old PY358
     03  PY116           pic x(36) value "PY116 IRS Nominal # not found, Retry".
     03  PY117           pic x(28) value "PY117 Account does not exist".
     03  PY118           pic x(38) value "PY118 Account re/write failed - Status".
*>     03  PY119           pic x(20) value "PY119 Must be Y or N".
*>     03  PY120           pic x(44) value "PY120 Cannot open Accounts File, aborting : ".
*>     03  PY121           pic x(79) value "PY121 A/P must be A or P : A = flat Amount. P = Percentage of Gross Taxable pay". *> old PY359
*>     03  PY122           pic x(59) value "PY122 Chk Cat Must be 2-7 for Earnings, 9-16 for Deductions".  *> old PY360
*>     03  PY123           pic x(55) value "PY123 FWT Cutoffs & Percents Must be in Ascending order".      *> old PY356
*>     03  PY124           pic x(45) value "PY124 Account does not exist in Account Table".
     03  PY125           pic x(43) value "PY125 Payroll Parameter file does not exist".
     03  PY126           pic x(32) value "PY126 Use menu option Y to do so".
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
*>     copy "an-accept.ws".  *> Support WS for ACCEPT_NUMERIC routine
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
 Report section.
*>**************
*>
 RD  Account-File-Report
     control    Final
     Page Limit Page-Lines
     Heading 1
     First Detail 8
     Last  Detail WS-Page-Lines.
*>
 01  Report-Head-Group Type Page Heading.
*> Print layouts to 80 cols Portrait
*>
     03  Line 1.
         05  col  1      pic x(17)   source Prog-Name.
         05  col 33      pic x(19)   value "Account File Report".
         05  col 73      pic x(5)    value "Page ".
         05  col 78      pic zz9     source Page-Counter.
*>
     03  line 2.
         05  col 33      pic x(19)   value "ACAS Payroll System".
*>
     03  line 3.
         05  col  1      pic x(40)   source UserA.
         05  col 62      pic x(10)   source U-Date.
         05  col 73      pic x(8)    source WSD-Time.
*>
     03  line 5.
         05  col  1      pic x(5)     value " Acct".
         05  col 11      pic x(6)     value "IRS/GL".
         05  col 30      pic x(6)     value "IRS/GL".
*>
     03  line 6.
         05  col  1      pic x(6)     value "Number".
         05  col 11      pic x(7)     value "Account".
         05  col 30      pic x(4)     value "Name".
*>
 01  Account-Detail type detail.  *> print every line
     03  line plus 1.
         05      col   3 pic z9       source Act-No.
         05      col  12 pic 9(6)     source Act-GL-No.
         05      col  30 pic x(24)    source Act-Desc.
*>
*>  Reminder of how, etc also see st010rw-3.02.cbl in RW  or from IRS (RW folders)
 *>    03  WIP-Data    line plus 1
 *>           present when Stock-Services-Flag not = "Y"
 *>                    and (Stock-Construct-Bundle not = zero
 *>                     or Stock-Under-Construction not = zero
 *>                     or Stock-Work-in-Progress not = zero
 *>                     or Stock-Construct-Item not = spaces).
 *>        05  rd-Wip-Data col   1     pic x(132)  value spaces.
*>
 01  type control Footing Final line plus 2.
     03  col 1           pic x(25)    value "Total - Account Records :".
     03  col 25          pic z9       source WS-Rec-Cnt.
*>
 01  type control Footing Final line plus 2.
     03  col 1           pic x(21)    value "*** End of Report ***".
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
 01  SS-Param-Menu-3    background-color cob-color-black
                        foreground-color cob-color-green
                        erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2.
     03  value "Account File Set Up"         col 29.
     03  from  U-Date     pic x(10)          col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
     03  value "1. Account File Maintenance"
                                     line  5 col  21 erase eos.
     03  value "2. Account File Report "
                                     line  6 col  21.
     03  value "X or Esc to quit menu option"
                                     line  7 col  21.
     03  value "Select Option  [ ]"  line  9 col 30.
     03  using Menu-Reply    pic x   line  9 col 46 foreground-color 3.
*>
*>   NEW MENUS Here
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
     move     WSE-HH  to  WSD-HH.
     move     WSE-MM  to  WSD-MM.
     move     WSE-SS  to  WSD-SS.
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
 *>    move     zeros to AN-Error-Code
 *>                      AN-Return-Code.
 *>    SET      AN-FG-IS-Green    to TRUE.
 *>    SET      AN-BG-IS-Black    to TRUE.
 *>    SET      AN-FG2-IS-Cyan    to TRUE.
 *>    SET      AN-Mode-IS-Update to TRUE.    *> could be AN-MODE-IS-NO-UPDATE to
*>                                             TRUE on first use.
*>
     move     1 to RRN.
     open     input PY-Param1-File.
     if       PY-PR1-Status not = "00"      *> Does not exist yet so lets create it & write rec
              move     1 to WS-Term-Code
              close    PY-Param1-File
              display  PY125 at line WS-22-Lines col 1 foreground-color 4 erase eos
              display  PY126 at line WS-23-Lines col 1 foreground-color 4
              display  SY001 at line WS-Lines    col 1 foreground-color 2
              accept   Menu-Reply at line WS-Lines col 48
              goback   returning 1   *> == no param file
     end-if.
     read     PY-Param1-File.
     if       PY-PR1-Status not = "00"
              display  PY002  at line WS-23-Lines col 1 foreground-color 6 erase eos
              display  PY-PR1-Status
                              at line WS-23-Lines col 33
              perform  ZZ040-Evaluate-Message
              display  WS-Eval-Msg   at line WS-23-lines col 36
              display  SY001         at line WS-Lines    col 1 foreground-color 2
              accept   Menu-Reply    at line WS-Lines    col 48
              goback   returning 1   *> == no param file
     end-if.
*>
     move     space to  Menu-Reply
     move     zero  to  Return-Code.
*>
*> REMEMBER TO REOPEN PARAM FILE AND CLOSE IT AFTER A REWRITE   <<<<<<<<-------
*> before all menus other than the first one
*>
 aa010-Menu.
     if       Return-Code = 16
              close    PY-Param1-File
              go to    aa000-Exit.
     display  space at 0101 with erase eos.
     display  SS-Param-Menu-3.
     accept   SS-Param-Menu-3.
     move     UPPER-CASE (Menu-Reply) to Menu-Reply.
     if       Menu-Reply = "X"
        or    Cob-CRT-Status = Cob-Scr-Esc
              close    PY-Param1-File
              goback.
     if       Menu-Reply = 1
              perform  ab020-Py-Nominal-Accounts
              go to    aa010-Menu.
     if       Menu-Reply = 2
              perform  aa050-Report
              go to    aa010-Menu.
     display  PY101 at  line WS-23-Lines col 1 erase eos foreground-color 6.
     go       to aa010-Menu.
*>
 aa000-Exit.  Exit section.
*>
 aa050-Report                section.
*>**********************************
*>
     open     input  PY-Accounts-File.
     if       PY-Act-Status not = "00"
              close    PY-Accounts-File
              display  PY117 at line WS-23-lines col 1 with foreground-color 4 highlight erase eos
              exit section
     end-if
     open     output Print-File.
*>
     move     zero to WS-Rec-Cnt.
     subtract 1 from Page-Lines giving WS-Page-Lines.
     move     To-Day to U-Date.
*>
     initiate Account-File-Report.
     perform  aa060-Produce-Report.
     terminate
              Account-File-Report.
     close    Print-File.
     close    PY-Accounts-File
     call     "SYSTEM" using Print-Report.
*>
 aa050-Exit.   exit section.
*>
 aa060-Produce-Report   section.
*>*****************************
*>
     move     zero to WS-Rec-Cnt.
     perform  forever
              read     PY-Accounts-File next record
              if       PY-Act-Status not = "00"   *> EOF
                       exit perform
              end-if
              add      1 to WS-Rec-Cnt
              generate Account-Detail
              exit perform cycle
     end-perform.
*>
 aa060-Exit.  exit section.
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
*>
 ab020-Py-Nominal-Accounts   section.   *> ab code from py900
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
 aa100-Bad-Data-Display.
     display  WS-Err-Msg at line WS-23-Lines col 1.
     display  SY002      at line WS-Lines    col 1.
*>
 aa110-Act-File-Error.
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
 Dummy-Ex.    exit.
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
     exit     section.
*>
 *>    copy "an-accept.pl".
*>
*>C      copy "Proc-ZZ100-ACAS-IRS-Calls.cob"
*>C           replacing LEADING ==ZZ100-== by ==ZZ900-==
*>C                     LEADING ==zz100-== by ==ZZ900-==. *> FOR IRS file handler CoA file.
*>C *>
*>C      copy "Proc-ACAS-FH-Calls.cob"                    *> FOR GL  file handler CoA file.
*>C           replacing LEADING  ==ZZ080-== by ==ZZ910-==
*>C                     System-Record by WS-System-Record.
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
*>
      *>>>Info: Total Copy Depth Used = 03;  Caution messages issued =   4
