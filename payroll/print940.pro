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
*>    Functions Used:   CURRENT-DATE
*>                      SYSTEM.
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
*>C  copy "envdiv.cob".
 configuration section.
 source-computer.      Linux.
 object-computer.      Linux.
*> special-names.
*>     console is crt.
*> SPECIAL-NAMES.
*>       CRT STATUS IS COB-CRT-STATUS.
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
*>
 fd  Print-File
     reports are 940-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "PRINT940 (1.0.00)".  *> First release pre testing. Prog name will be changed.
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
*> copy "wsmaps03.cob". *> NEEDED ?
*>C  copy "wsfnctn.cob".  *> NEEDED ?
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
*>C  copy "Test-Data-Flags.cob".  *> set sw-Testing to zero to stop logging.  *> NEEDED ?
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
 01  Error-Messages.   *>   CHANGE FOR PROG
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY002           pic x(31) value "SY002 Note error and hit Return".
*>     03  SY003           pic x(51) value "SY003 Aborting function - Note error and hit Return".
*>     03  SY004           pic x(20) value "SY004 Now Hit Return".
*>     03  SY005           pic x(18) value "SY005 Invalid Date".
*>     03  SY008           pic x(32) value "SY008 Note message & Hit Return ".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*>     03  SY014           pic x(30) value "SY014 Press return to continue".
*>
*> Module General ?
*>
     03  PY011           pic x(36) value "PY011 Re/Write PARAM record Error = ".
     03  PY012           pic x(32) value "PY012 Read PARAM record Error = ".
*>     03  PY013           pic x(39) value "PY013 See manual for NL accounts needed".
*>     03  PY014           pic x(29) value "PY014 To quit, use ESCape key".
*>     03  PY015           pic x(40) value "PY015 F1 for display of current accounts".
*>     03  PY016           pic x(40) value "PY016 No records to show, return to quit".
*>     03  PY017           pic x(45) value "PY017 No more records to show, return to quit".
*>     03  PY018           pic x(31) value "PY018 Write DED record Error = ".
     03  PY019           pic x(30) value "PY019 Read DED record Error = ".
*>     03  PY020           pic x(33) value "PY020 Rewrite DED record Error = ".
     03  PY021           pic x(30) value "PY021 Read CoH Record Error = ".

*>     03  PY119           pic x(20) value "PY119 Must be Y or N".
*>     03  PY120           pic x(38) value "PY120 Do you wish to Continue (Y/N) - ".
*>
*> Module specific
*>   from print940
*>
     03  PY581           pic x(24) value "PY581 PR2 File not found".
     03  PY582           pic x(24) value "PY582 COH File not found".
     03  PY583           pic x(24) value "PY583 DED File not found".
*>     03  PY584           pic x(45) value "PY584 System has not achieved Year End Status".
*>     03  PY585           pic x(28) value "PY585 Unable to write to PR2".
     03  PY586           pic x(24) value "PY586 HIS File not found".
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
      *>>>Info: Total Copy Depth Used = 03;  Caution messages issued =   2
