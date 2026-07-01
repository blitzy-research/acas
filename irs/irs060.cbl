       >>source free
*>*****************************************************************
*>                                                                *
*>      F I N A L   A C C O U N T S   P R O D U C T I O N         *
*>                                                                *
*>*****************************************************************

 identification division.
*>************************
*>
 program-id.            irs060.
*>
*> Author.              Cobol conversion by Vincent B Coen, FIDPM FBCS 24/10/82
*>                      for APPLEWOOD COMPUTERS.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>
*>**
*> Remarks.             P&L and Balance Sheet.
*>                      Input work file from irs065 sort.
*>**
*> Version.             See prog-name in ws.
*>**
*> Calls.
*>                      acasirsub1  ->
*>                       irsnominalMT
*>                      acasirsub3 ->
*>                       irsdfltMT
*>                      acasirsub4 ->
*>                       postingMT
*>                      acasirsub5 ->
*>                       irsfinalMT
*>**
*> Error messages used.
*>  System Wide
*>                      SM901 }
*>                      SM903 } Produced by DAL.
*>                      SM904 }
*>                      SY008.
*>                      IR901 }
*>                      IR902 } From FH.
*>                      IR911 }
*>                      IR912 }
*>                      IR913 }
*>                      IR914 }
*>                      IR915 }
*>                      IR916 }
*>  Module Specific.
*>                      IR060 Aborting End of year processing. Fix and rerun
*>                      IR061 Default A/C 30 or 31 Not setup
*>                      IR062 Failure to open Work File!!!!
*>                      IR063 Ledgers Incorrectly Coded! Aborting
*>                      IR064 Does not exist. Hit return, then Check & re-enter
*>                      IR065 (no ID)
*>                      nnnnn is a Sub-nominal account, you must specify a Main account only.
*>*
*> Original Error messages :
*>                       [This two will NOT appear if the defaults have been set up
*>                         correctly including accounts 30 and 31 (VAT/GST/sales Tax)]:-
*>                       IR061 Default A/C 30 or 31 Not setup - As specified
*>                             A/C 30 = O.T.B Control Account
*>                             A/C 31 = Vat Input
*>                             A/C 32 = Vat Output
*>                       (Default 31 A/C) does not exist..ABORTING
*>                                      - As this is tested prior
*>                                         It is more likely a bug
*>                                         by bad data in defaults.
*> Possible software bugs :
*>                       These have never appeared in testing or production
*>                       in over 30 years
*>                       but if they do, it indicates very serious errors
*>                       with the data or more importantly missing data.
*>                       It could indicate a problem with your hard drive
*>                       or *lack of free space
*>                       but definitely now, data corruption. More likely a Bug !
*>                        - or in other words - Have no idea why!
*>
*>                       PE 005946   Error within Read-End  - work file EOF
*>                                                            (sorted postings).
*>                       PE 009865   Error within line-total (bypass)
*>                                                          - Problem with workfile data.
*>                       PE 009610   Error within jump-back - Missing NL record.
*>                       *PE 014900  Error within pl-a      - Cannot rewrite record.
*>                       PE 015000   Error within pl-a-end  - Missing NL rec PL approp.
*>                       PE 015010   Error within pl-a-end  - PL approp not a Main a/c.
*>                                  [Last two should not occur as tested for earlier in
*>                                   the program].
*>                       PE 015100   Error within pl-a-end  - Cannot Rewrite record.
*>                       (Default 31 A/C) does not exist..ABORTING - Should not happen as
*>                                                                   previously tested for.
*>                       PE VAT01: Problems with CoA file - Bad coding
*>                                   Error within VAT-AC-TidyUp
*>                                                          - Fault in NL records.
*>                       *PE 015370: Problems with CoA file cant rewrite
*>                                   Error within VAT-AC-TidyUp (vat-c)
*>                                                          - Cannot Rewrite record.
*>                       *PE 015470: Problems on rewrite for CoA file
*>                                   Error within VAT-AC-TidyUp (vat-finalize)
*>                                                          - Cannot Rewrite record.
*>
*>                       IT IS RECOMMENDED THAT you restore your data from the
*>                       last good back up and rerun HAVING made a back up of
*>                       your CURRENT data files.
*>**
*> Changes.
*>  1/7/83  vbc - Improve running time, split prog into 2 (irs065)
*>                thru-put increased by 650%.
*>  2/7/83  vbc - Tidy up final reports, tb & fa.
*>  8/7/83  vbc - Correct date-validate routine, for end of year
*>                 and begining of new year.
*>  9/7/83  vbc - Fix end of year processing by adding new routine
*>                PL-Capital-AC-Tidyup.
*> 13/7/83  vbc - Reset save-sequ if changing post file.
*> 20/7/83  vbc - Reduce size of nl file.
*> 22/7/83  vbc - Fix ratios,fix eop processing.
*> 26/7/83  vbc - Rewrite date vet routine.
*> 10/8/83  vbc - Validate & reject if ness, p/l account earlier
*>                squash up vat a/cs,ditto code accounts same as
*>                P/L account at end of period processing.
*>  6/9/83  vbc - Fix bugs:- dont create otb post rec at eop;
*>                           in PL-Capital-AC-Tidyup, group add
*>                           all records with same type (ac);
*>                           check otb balance to zero.
*> 26/03/84 vbc - Y & P on report request 2 b reversed.
*> 28/05/84 vbc - Hilite display heads.
*> 14/04/85 vbc - Change print to 79 chars.
*> 26/09/89 vbc - 2.53
*>                Mods for cobol/2.
*> 23/01/09 vbc - Migration to Open Cobol as version 3.
*> 20/02/09 vbc - Centre client in reports.
*> 21/02/09 vbc - Added support for envs LINES and COLUMNS as needed.
*> 21/09/10 vbc - Added print spool.
*>                .11 fix for portrait printing
*> 16/12/13 vbc - .12 Removed security test/password prior to print report.
*> 12/10/16 vbc - .13 Added preload of PL-Approp-AC if PL-App-Created = 1.
*>                    Prep. of Finished A/Cs for all 9 groups.
*>                    Sub groups not used so only 1,5,9,11,15,18,21,23.
*>                    Are the others needed, such as 8,14,20,22,25,26 ? [for] :
*>                    ( 8) Gross Profit
*>                    (14) Net Profit
*>                    (20) Total Assets
*>                    (22) Net Current Assets
*>                    (25) Net Profits
*>                    (26) Net Current Assets
*> 04/12/16 vbc - v3.02 RDB
*> 04/12/16 vbc - .14 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*>                    Replace direct access (open,read,write,close) for NL
*>                    for FH & DAL. Must have been written before using FH
*>                    The temp. Work file is ALWAYS a Cobol file.
*> 20/12/16 vbc -     All irs progs call cpybk Proc-ZZ100-ACAS-IRS-Calls.
*> 29/01/18 vbc - .15 Added extra error / warning messages although most
*>                    have never appeared. msgs for Defaults A/C 30 or 31
*>                    being not present (missing) must be fixed by using the
*>                    correct program (irs020 - Defaults Maintenance.
*>                    Changed copies to use copybooks where poss. I.e.,
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 07/02/18 vbc - .16 Removed the pls wait while printing msg.
*> 08/02/18 vbc - .17 Remapped the NL Record-1 with NL-IRSWS-Record so no need
*>                    to issue move between them so only needed for NL-Record
*>                    as originally held in WS for a temp. rec.
*>                    This hopefully will ensure that there is no garbage data.
*>                    Should have done it the first time.
*> 10/02/18 vbc - .18 Moved many of the error/warning messages to IR0nn.
*> 10/02/18 vbc - .19 Renamed IR011-16 to IR911-16 and others.
*>                .20 After reading Work file move to Record-1 as this is the
*>                    same as same rec area for work file and nominal record.
*> 11/02/18 vbc - .21 Close sub1 before gobacks and print-file if open.
*> 12/02/18 vbc - .22 Y2K problem found when processing accounts of 1989-90 -
*>                    new WS field WS-Y2K-slide holding 70 if YY < slide, its 20nn
*>                    else its 19nn.
*>                    On accepting PL-Approp allow for zero to quit.
*> 26/03/18 vbc -     Added more notes on error messages including the PE ones.
*>                    Yep, PE = Program Error or ???
*> 02/05/18 vbc - .23 Added date/Time to report & do this for most of the
*>                    reports in IRS as it is hard to work out the latest reports.
*> 13/05/18 vbc - .24 Added extra field for use with Slide (see .22 note)
*>                    pre-coded if year is > 2068 and < 2100.
*>                    Code change will still be needed.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
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
*> holder with your commercial plans and proposals.
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
 environment division.
 copy "envdiv.cob".
*>
 input-output section.
 file-control.
*>
     select  work-file       assign "worksort.tmp"
                             organization sequential
                             status fs-reply.
*>
     select  print-file      assign "prt-1"
                             organization line sequential.
*>
 data division.
 file section.
*>
 fd  work-file.
*>
 01  work-record.
     03  work-key        pic 9(10).
     03  work-type       pic a.
     03  work-data.
         05 work-name    pic x(24).
         05 work-dr      pic 9(8)v99  comp.
         05 work-cr      pic 9(8)v99  comp.
         05 work-dr-last pic 9(8)v99  comp  occurs 4.
         05 work-cr-last pic 9(8)v99  comp  occurs 4.
         05 work-ac      pic a.
    03  filler  redefines work-data.
        05 work-pointer  pic 9(5).
*>
 fd  print-file.
*>
 01  print-record        pic x(79).
*>
 working-storage section.
 77  prog-name           pic x(16)    value "irs060 (3.3.00)".
 77  a                   binary-char  value zero.
 77  b                   binary-char  value zero.
 77  C                   binary-char  value zero.
 77  ws-client           pic x(24)    value spaces.
 77  Final-Acs-In-Use    pic 9        value zero.  *> 1 if true
*>
*> This one will need changing in year 2069 on and only used if processing
*>  data before 2000.
*>
 77  WS-Y2K-slide        pic 99       value 70.    *> dates below = 20 else 19.
 77  WS-Listing-CC       pic 99       value 19.    *> used in paragraph ML-2
*>
 copy "irsprint-spool-command-p.cob".
*>
 01  filler.
     03  w-date.
         05  filler      pic x(6).
         05  w-year      pic 99.
     03  ws-reply        pic x.
     03  total-1         pic s9(8)v99  comp occurs 26.
     03  total-2         pic s9(8)v99  comp occurs 26.
     03  level-11        pic s9(8)v99  comp value zero.
     03  level-12        pic s9(8)v99  comp value zero.
     03  level-21        pic s9(7)v99  comp value zero.
     03  level-22        pic s9(7)v99  comp value zero.
     03  net-1           pic s9(7)v99  comp value zero.
     03  net-2           pic s9(7)v99  comp value zero.
     03  PL-AC           pic 9(5)     value zero.
     03  letters         pic x(26)    value "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
     03  filler  redefines  letters.
         05  ar0         pic x       occurs  26  indexed by  w.
     03  j               pic 9.
     03  y               pic 99.
     03  z               pic 99.
     03  group-level     pic x.
         88  sub-total                value "T".
     03  work-1          pic s9(9)v99  comp value zero.
     03  work-2          pic s9(9)v99  comp value zero.
     03  work-3          pic s9(9)v99  comp value zero.
     03  PL-Title        pic x(40).
     03  PL-Rep-Type     pic x.
     03  PL-Rep-Type2    pic x.
     03  NL-File         pic x(11).
*>     03  WS-Pass         pic x(4).
     03  WS-Hypens       pic x(9)     value "---------".
     03  WS-Equals       pic x(9)     value "=========".
     03  WS-AC           pic x        value space.
     03  WS-AC2          pic x        value space.
     03  AC2             pic x.
*>
     03  hdtime                          value spaces.
         05  hd-hh       pic xx.
         05  hd-mm       pic xx.
         05  hd-ss       pic xx.
         05  hd-uu       pic xx.
     03  HD2-Time.
         05  filler      pic x     value spaces.
         05  hd2-hh      pic xx.
         05  filler      pic x     value ":".
         05  hd2-mm      pic xx.
*>
*>     03  WS-Pass         pic x(1024).  *> Not on OS versions.
*>     03  WS-Encript-Pass pic x(1024).
*>
 01  filler.
     03  line-1.
         05  filler      pic x(28)    value spaces.
         05  l1-client   pic x(24).
         05  filler      pic x(13)    value spaces.
         05  p-date      pic x(8).
         05  P-Time      pic x(6)     value spaces.
*>
     03  line-2.
         05  filler      pic x(20)    value spaces.
         05  l2-title    pic x(40).
         05  filler      pic x(19)    value spaces.
*>
     03  line-3.
       05  line-3a.
         07  filler      pic x(19).
         07  l3a-t1      pic x(20).
         07  l3a-date1   pic x(8).
         07  l3a-t2      pic xxxx.
         07  l3a-date2   pic x(8).
         07  filler      pic x(20).
       05  line-3b redefines line-3a.
         07  filler      pic x(25).
         07  l3b-t1      pic x(19).
         07  l3b-date    pic x(8).
         07  filler      pic x(27).
*>
     03  line-5.
       05  filler        pic x(34)    value spaces.
       05  l5-grp1b.
         07  l5-g1a      pic x(10)    value "--------20".
         07  l5-year1    pic 99       value zero.
         07  l5-g1c      pic x(8)     value all "-".
       05  l5-grp1 redefines l5-grp1b pic x(20).
       05  filler        pic x(5)     value spaces.
       05  l5-grp2b.
         07  l5-g2a      pic x(10)    value "--------20".
         07  l5-year2    pic 99       value zero.
         07  l5-g2c      pic x(8)     value all "-".
       05  l5-grp2 redefines l5-grp2b pic x(20).
*>
     03  line-7.
       05  filler        pic xx       value spaces.
       05  l7-name       pic x(27).
       05  filler        pic x(5)     value spaces.
       05  l7-sign1      pic x.
       05  l7-value1     pic z(6)9    blank when zero.
       05  l7-sign2      pic x.
       05  filler        pic xx       value spaces.
       05  l7-sign3      pic x.
       05  l7-value2     pic z(6)9    blank when zero.
       05  l7-sign4      pic x.
       05  filler        pic x(5)     value spaces.
       05  l7-sign5      pic x.
       05  l7-value3     pic z(6)9    blank when zero.
       05  l7-sign6      pic x.
       05  filler        pic xx       value spaces.
       05  l7-sign7      pic x.
       05  l7-value4     pic z(6)9    blank when zero.
       05  l7-sign8      pic x.
*>
     03  line-8.
       05  filler        pic x(34)    value spaces.
       05  l8-underline1 pic x(9).
       05  filler        pic x(2)     value spaces.
       05  l8-underline2 pic x(9).
       05  filler        pic x(5)     value spaces.
       05  l8-underline3 pic x(9).
       05  filler        pic x(2)     value spaces.
       05  l8-underline4 pic x(9).
*>
     03  line-9.
       05  l9-name       pic x(34).
       05  l9-sign1      pic x.
       05  l9-value1     pic z(6)9    blank when zero.
       05  l9-sign2      pic x.
       05  filler        pic x(16)    value spaces.
       05  l9-sign3      pic x.
       05  l9-value2     pic z(6)9    blank when zero.
       05  l9-sign4      pic x.
       05  filler        pic x(11)    value spaces.
*>
     03  line-10.
       05  l10-client    pic x(24).
       05  filler        pic x(6)     value spaces.
       05  filler        pic x(23)    value "    Sales Ratios    ".
       05  filler        pic x(18)    value "      Period To - ".
       05  l10-date      pic x(8).
*>
     03  line-11.
       05  l11-name      pic x(24).
       05  l11-ratio     pic zzz9.99.
*>
 copy "irswsfinal.cob".
*>
 copy "wsfnctn.cob".
 copy "irswspost.cob".
 copy "irswsdflt.cob"     replacing Default-Record by WS-IRS-Default-Record.
*>
 copy "irsfdwsnl.cob".               *> Record-1 from old FD
 copy "irswsnl.cob" replacing  ==nl-record== by ==WS-IRSNL-Record redefines Record-1==
                        leading ==NL-==  by ==FD-NL-==
                                   Owner by FD-NL-Owner.
*>
 copy "irswsnl.cob".                     *> needed for WS ( [NL]-Record ) previous code.
*>
*> read in and moved to old FD
*>
 01  maps03-ws.
     03  u-date          pic x(8).
     03  filler  redefines  u-date.
       05  u-days        pic 99.
       05  filler        pic x.
       05  u-month       pic 99.
       05  filler        pic x.
       05  u-year        pic 99.
     03  u-bin           pic s9(5)    comp.
*>
 01  date-fields.
     03  q                 pic s99    comp  value zero.
*>
     03  days-in-month     pic x(24)  value "312831303130313130313031".
     03  filler  redefines  days-in-month.
       05  days            pic 99     occurs 12.
*>
     03  ws-work1          pic s9(5)   comp.
     03  ws-work2          pic s9(5)   comp.
     03  save-date         pic s9(5)   comp.
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
  *>     03  WS-IRSNL-Record       pic x.
  *>     03  WS-IRS-Default-Record pic x.
  *>     03  Posting-Record        pic x.
  *>     03  Final-Record          pic x.
     03  WS-IRS-Posting-Record pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide      USED are : 08
     03  SY008          pic x(32) value "SY008 Note message & Hit return ".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, Fs-reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, Fs-reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, Fs-reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, Fs-reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, Fs-reply = ".
*> Module specific  USED are :
     03  IR060          pic x(52) value "IR060 Aborting End of year processing. Fix and rerun".
     03  IR061          pic x(36) value "IR061 Default A/C 30 or 31 Not setup".
     03  IR062          pic x(35) value "IR062 Failure to open Work File!!!!".
     03  IR063          pic x(41) value "IR063 Ledgers Incorrectly Coded! Aborting".
     03  IR064          pic x(55) value "IR064 Does not exist. Hit return, then Check & re-enter".
     03  IR065          pic x(62) value
                           "is a Sub-nominal account, you must specify a Main account only".
*>
 linkage   section.
*>****************
*>
 copy "irswssystem.cob"   *> IRS param record
              replacing system-record  by IRS-System-Params. *> (01 level)
*>
 copy "wssystem.cob"    *> NEW for v3.02
             replacing  System-Record by WS-System-Record
                        Run-Date   by ACAS-Run-Date     *> these 3 are in binary
                        Start-Date by ACAS-Start-Date   *> IRS expects as x(8)
                        End-Date   by ACAS-End-Date     *>  dd/mm/yy
                        suser      by ACAS-suser
                        Address-1  by ACAS-Address-1
                        Address-2  by ACAS-Address-2
                        Address-3  by ACAS-Address-3
                        Address-4  by ACAS-Address-4
                        Post-Code  by ACAS-Post-Code
                        Print-Spool-Name by ACAS-Print-Spool-Name
                        Pass-Value by ACAS-Pass-Value
                        Pass-Word  by ACAS-Pass-Word
                        OP-System  By ACAS-Op-System
                        Client     by IRS-Client
                        System-Ops by IRS-System-Ops
                        Next-Post  by IRS-Next-Post
                        Vat-Rates2 by IRS-Vat-Rates2
                        Vat1       by IRS-Vat1
                        Vat2       by IRS-Vat2
                        Vat3       by IRS-Vat3
                        Vat-Group  by IRS-Vat-Group
                        Vat-Psent  by IRS-Vat-Psent
                        Save-Sequ  by IRS-Save-Sequ
                        System-Work-Group by IRS-System-Work-Group
                        PL-App-Created by IRS-PL-App-Created
                        PL-Approp-AC   by IRS-PL-Approp-AC
                        1st-Time-Flag  by IRS-First-Time-Flag.
*>
 copy "wsnames.cob".
*>
 procedure division using IRS-System-Params       *> IRS sys rec
                          WS-System-Record        *> ACAS sys rec
                          File-Defs.
*>=========================================
*>
 init01   section.
*>***************
*>
     move     zero to y.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
     move     run-date   to p-date.
     accept   hdtime from time.
     if       hdtime not = "00000000"
              move hd-hh to hd2-hh
              move hd-mm to hd2-mm
              move HD2-Time  to P-Time.
*>
*> Fix up client to justified centre
*>
     move     client to ws-client.
     call     "C$JUSTIFY" using ws-client "C".
*>
 screen-heads.
*>
     display  prog-name                   at 0101 with erase eos foreground-color 2.
     display  "Final Accounts Production" at 0129 with foreground-color 1 background-color 7.
     display  run-date                    at 0173 with foreground-color 2.
*>
sh-ends.
*>
*> Password coding simplified /removed for O/S. versions.
*>     display  "Enter pass-word - [****]"  at 0501 with foreground-color 2.
*>     accept   ws-pass at 0520 with secure.
*>     if       ws-pass not = pass-word
*>              go to e-o-p-end.
*>
     perform  varying y from 1 by 1 until y > 26
              move zeros to total-1 (y) total-2 (y)
     end-perform
*>
*>  Get the Final record for Finished Accounts printing if not space.
*>
     move     3  to  file-function.                *> Open & Read next, close
     perform  acasirsub5.
*>
 ml-b.
*>---
*>
     display  "Enter comparative to use (0 to 4) -  [ ]" at 0801 with foreground-color 2.
     accept   j  at 0839 with foreground-color 3.
     if       j  <  0  or  >  4
              go to  ml-b.
*>
*> Get profit & loss report title
*>
     display  "Enter Profit & Loss Report Title     [" at 1001 with foreground-color 2.
     display  "]" at 1079 with foreground-color 2.
     move     "Profit and Loss Report" to pl-title.
     accept   pl-title at 1039 with update foreground-color 3.
*>
 ml-1.
*>---
*>
     display  "Period Report (P) or Year Report (Y) [ ]" at 1101 with foreground-color 2.
     accept   pl-rep-type2 at 1139 with foreground-color 6.
     move     function upper-case (pl-rep-type2) to pl-rep-type.
     if       pl-rep-type not = "P" and not = "Y"
              go to ml-1.
*>
 ml-2.
     display  "Use Finished Account Titles if set up ?  [ ]" at 1201 with foreground-color 2.
     move     "N" to ws-reply.
     accept   ws-reply  at 1243 with update foreground-color 6.
     move     function upper-case (ws-reply) to ws-reply.
     if       ws-reply not = "Y" and not = "N"
              go to ml-2.
     if       ws-reply = "Y"
              move  1   to Final-Acs-In-Use.
     move     space to ws-reply.
*>
     move     end-date to w-date   l10-date.
     move     w-year   to l5-year1 l5-year2.
     subtract 1  from  l5-year2.
*>
*> Check year for Y2K etc and adjust for dates within 19nn else 20
*>  Found when processing old accounts of 1989-1990. It could happen
*>   for others. This is for the listing heads.
*>   Need to increase to 20 else 21 after year 2069.
*>
     if       W-Year NOT < WS-Y2K-slide  *> (70)
              move WS-Listing-CC to L5-G1A (9:2)
                                    L5-G2A (9:2).
*>
     if       j = zero
              move spaces to l5-grp2.
*>    display  "Give Title 1 - [" at 1301 with foreground-color 2.
*>    display  "]"                at 1337 with foreground-color 2.
*>    display  l5-grp1            at 1317 with foreground-color 3.
*>    accept   l5-grp1            at 1317 with foreground-color 3 update.
*>    if       j not = zero
*>             display "2"        at 1312 with foreground-color 2
*>             display l5-grp2    at 1317 with foreground-color 3
*>             accept  l5-grp2    at 1317 with foreground-color 3 update.
*>
     display  "Checking Accounts Please Wait" at 1601 with foreground-color 2.
     open     input  work-file.
     if       fs-reply  not = zero
              display IR062 at 2401 with foreground-color 2
              display SY008   at 2441
              accept ws-reply at 2475
              close work-file
              goback.
*>
*> This section reads the sorted nominal ledger workfile with
*> main accounts only. the grand total for each A/C type
*> and its required comparative are calculated
*>
 Read-Loop.
*>--------
*>
     read     work-file at end
              go to  Read-End.
*>
     move     Work-Record to Record-1.
     set      w  to  1.
     move     function upper-case (ac) to ac2.
     search   ar0
              when  ar0 (w)  =  ac2
              go to  Accumulate.
     display  space.
     display  IR063  at 0501 with foreground-color 2.
     display  "ACCOUNT  - " at 0701          with foreground-color 2.
     display  owning at 0713                 with foreground-color 2.
     display  "/" at 0718                    with foreground-color 2.
     display  sub-nominal at 0719            with foreground-color 2.
     display  SY008    at 0801
     accept   ws-reply at 0835
     close    work-file.
     goback.
*>
 Accumulate.         *> Gets here then ac = A through Z.
*>---------
*>
     if       ac  <  "E"
              perform  CR-Total
              go to Read-Loop.
     if       ac  >  "D"  and  <  "I"
              perform  DR-Total
              go to Read-Loop.
     if       ac  = "I"  or  "J"
              perform  CR-Total
              go to Read-Loop.
     if       ac  >  "J"  and  <  "U"
              perform  DR-Total
              go to Read-Loop.
     if       ac  >  "T"
              perform  CR-Total.
     go       to Read-Loop.
*>
 Read-End.
*>-------
*>
     close    work-file.
*>
*> This section produces the P & L Report
*>
*> Reopen nominal ledger (work) & open print-file
*>
     open     input  work-file.
     open     output  print-file.
*>
*> Set up title lines
*>
     move     pl-title to l2-title.
     call     "C$JUSTIFY" using l2-title "C".
     move     spaces   to line-3.
     if       pl-rep-type = "Y"
              move end-date to l3b-date
              move "For the Year Ended " to l3b-t1
     else
              move "For the Period From " to l3a-t1
              move " to "                 to l3a-t2
              move start-date             to l3a-date1
              move end-date               to l3a-date2.
     move     ws-client to l1-client.
     move     client    to l10-client.
     write    print-record  from  line-1 after 1.
     write    print-record  from  line-2 after 2.
     write    print-record  from  line-3 after 2.
     write    print-record  from  line-5 after 2.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     1  to  y.
     read     work-file at end
              display "PE 005946" at 2401
              display SY008 at 2441
              accept ws-reply at 2475
              close work-file
                    print-file
              goback.
*>
 loop-1.
*>-----
*>
*>  Do account types A - D
*>
     move     "Total Income"  to  l7-name.
 loop-1B.
     perform  line-total.
     add      1  to  y.
     if       y  <  5
              go to  loop-1B.
     perform  group-total.
     move     level-11  to  level-21.
     move     level-12  to  level-22.
     move     zero  to  level-11  level-12.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     spaces  to  print-record.
     write    print-record after 1.
*>
 loop-2.
*>-----
*>
*>  Do account types E - H
*>
     move     "Less Total Direct Costs"  to  l7-name.
 loop-2B.
     perform  line-total.
     add      1  to  y.
     if       y  <  9
              go to  loop-2B.
     perform  group-total.
     subtract level-11  from  level-21.
     subtract level-12  from  level-22.
     move     level-21  to  level-11.
     move     level-22  to  level-12.
     move     "T"  to  group-level.
     move     "Gross Profit"  to  l7-name.
     move     ws-hypens to l8-underline2.
     if       j > zero
              move ws-hypens to l8-underline4.
     write    print-record from line-8 after 1.
     move     spaces  to  line-8.
     perform  group-total.
     move     zero  to  level-11  level-12.
     move     spaces  to  print-record  group-level.
     write    print-record after 1.
*>
 loop-3.
*>-----
*>
*>  Do account types I - J.
*>
     move     "Plus Sundry Income"  to  l7-name.
 loop-3B.
     perform  line-total.
     add      1  to  y
     if       y  <  11
              go to  loop-3B.
     perform  group-total.
     add      level-11  to  level-21.
     add      level-12  to  level-22.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     zero  to  level-11  level-12.
     move     spaces  to  print-record.
     write    print-record after 1.
*>
 loop-4.
*>-----
*>
*>  Do account types K - N.
*>
     move     "Less Total Indirect Costs"  to  l7-name.
 loop-4B.
     perform  line-total.
     add      1  to  y.
     if       y  <  15
              go to  loop-4B.
     perform  group-total.
     subtract level-11  from  level-21.
     subtract level-12  from  level-22.
     move     level-21  to  level-11  net-1.
     move     level-22  to  level-12  net-2.
     move     "T"  to  group-level.
     move     "Net Profit"  to  l7-name.
     move     ws-hypens to l8-underline2.
     if       j > zero
              move ws-hypens to l8-underline4.
     write    print-record from line-8 after 1.
     move     spaces to line-8.
     perform  group-total.
     move     space to  group-level.
     move     zero  to  level-11  level-12
                        level-21  level-22.
     move     ws-equals to l8-underline2.
     if       j > zero
              move ws-equals to l8-underline4.
     write    print-record from line-8 after 1.
     move     spaces to line-8.
*>
*> This section produces the balance sheet
*>
     write    print-record  from  line-1 after page.
     move     "             Balance Sheet              " to l2-title.
     write    print-record  from  line-2 after 2.
     write    print-record  from  line-3 after 2.
     write    print-record  from  line-5 after 2.
     move     spaces to line-8.
*>
 loop-5.
*>-----
*>
*>  Do account types O - Q.
*>
     move     "Fixed Asset Total"  to  l7-name.
 loop-5B.
     perform  line-total.
     add      1  to  y.
     if       y  <  18
              go to  loop-5B.
     perform  group-total.
     move     level-11  to  level-21.
     move     level-12  to  level-22.
     move     zero  to  level-11  level-12.
     move     spaces  to  print-record.
     write    print-record after 1.
*>
 loop-6.
*>-----
*>
*>  Do account types R - T
*>
     move     "Plus Total Current Assets"  to  l7-name.
 loop-6B.
     perform  line-total.
     add      1  to  y.
     if       y  <  21
              go to  loop-6B.
     perform  group-total.
     add      level-11  to  level-21.
     add      level-12  to  level-22.
     move     level-21  to  level-11.
     move     level-22  to  level-12.
     move     "T"  to  group-level.
     move     "Total Assets"  to  l7-name.
     move     ws-hypens to l8-underline2.
     if       j > zero
              move ws-hypens to l8-underline4.
     write    print-record from line-8 after 1.
     move     spaces to line-8.
     perform  group-total.
     move     zero  to  level-11  level-12.
     move     spaces to print-record  group-level.
     write    print-record after 1.
 loop-8.
*>-----
*>
*>  do account types U - V
*>
     move     "Less Current Liabilities"  to  l7-name.
 loop-8B.
     perform  line-total.
     add      1  to  y.
     if       y  <  23
              go to  loop-8B.
     perform  group-total.
     subtract level-11  from  level-21.
     subtract level-12  from  level-22.
     move     zero  to  level-11  level-12.
     move     level-21  to  level-11.
     move     level-22  to  level-12.
     move     ws-hypens to l8-underline2.
     if       j > zero
              move ws-hypens to l8-underline4.
     write    print-record from line-8 after 1.
     move     spaces to line-8.
     move     "T"  to  group-level.
     move     "Net Current Assets"  to  l7-name.
     perform  group-total.
     move     ws-equals to l8-underline2
     if       j > zero
              move ws-equals to l8-underline4.
     write    print-record from line-8 after 1.
     move     zero  to  level-11  level-12
                        level-21  level-22.
     move     spaces  to  print-record  group-level.
     move     spaces to l8-underline2 l8-underline4.
     write    print-record after 2.
 loop-9.
*>-----
*>
*>  Do account types W - Z
*>
     move     "Capital Account Total"  to  l7-name.
 loop-9B.
     perform  line-total.
     add      1  to  y.
     if       y  <  27
              go to  loop-9B.
     perform  group-total.
     write    print-record  from  line-8 after 1.
     move     level-11  to  level-21.
     move     level-12  to  level-22.
     move     zero  to  level-11  level-12.
     move     "Net Profits"  to  l7-name.
     move     spaces  to  line-8.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     net-1  to  level-11.
     move     net-2  to  level-12.
     perform  group-total.
     add      level-11  to  level-21.
     add      level-12  to  level-22.
     move     zero  to  level-11  level-12.
     move     level-21  to  level-11.
     move     level-22  to  level-12.
     move     "T"  to  group-level.
     move     "Net Current Assets"  to  l7-name.
     move     ws-hypens to l8-underline2.
     if       j > zero
              move ws-hypens to l8-underline4.
     write    print-record from line-8 after 1.
     move     spaces  to  line-8.
     perform  group-total.
     move     zero  to  level-11  level-12
                        level-21  level-22.
     move     ws-equals to l8-underline2.
     if       j > zero
              move ws-equals to l8-underline4.
     write    print-record from line-8 after 1.
     close    work-file.
*>
*> End of p&l and bal sheet reports
*>
     perform  ratio.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
*> End of sales ratio report
*>
     perform  screen-heads.
     display  "End of period processing outputs the current year f" &
              "igures to a comparative." at 0501 with foreground-color 2.
     display  "Revenue accounts are zeroed but Capital Accounts re" &
              "tain their value." at 0601 with foreground-color 2.
*>
 E-o-P-Option.
*>-----------
*>
     display  "Do you require end of period processing (Y/N) :- " at 0901 with foreground-color 2 erase eos.
     accept   ws-reply at 0950 with foreground-color 6.
     move     function upper-case (ws-reply) to ws-reply.
     if       ws-reply  = "N"
              go to  E-o-P-End.
     if       ws-reply not = "Y"
              go to  E-o-P-Option.
*>
*>    open input default-file and get record.
*>
     move     3 to file-function.
     perform  acasirsub3.
*>
 e-o-p-comp.
*>---------
*>
     display  "Comparative field to use - " at 1101 with foreground-color 2.
     accept   j  at 1128 with foreground-color 6.
     if       j  <  1  or  >  4
              go to  e-o-p-comp.
*>
 chk-defs.
*>-------
*>              30 = O.T.B , 31 = Vat Input (and 32 = Vat Output).
*>
     if       WE-Error not = zero
         or   FS-Reply not = zero
         or   def-acs (30) = zeros
         or   def-acs (31) = zeros          *> default 30 ?? or 31 not present
              display IR061 at 1201 with foreground-color 4
              display  SY008 at 1301
              accept   ws-reply at 1335
              goback.
*>
 Get-PL.
*>------
*>
     if      PL-App-Created = "1"
             move  PL-Approp-AC  to PL-AC
     end-if
     display "Enter P/L Appropriation or Capital A/C :- " at 1301 with foreground-color 2.
     display "(enter zero to quit)"  at 1360 with foreground-color 2.
     accept   pl-ac at 1343 with update foreground-color 3.
     if       pl-ac  = zero
              go to  E-o-P-End.
*>
 get-pl-rest.
*>----------
     display  "You have selected End of Period processing overwrit" &
              "ing comparative field - " at 1501 with foreground-color 2.
     display  j at 1577 with foreground-color 2.
     display  "with P/L or Capital A/C - " at 1601 with foreground-color 2.
     display  pl-ac at 1627 with foreground-color 2.
     display  "Is This Correct ? (Y/N) - " at 1701 with foreground-color 2.
     accept   ws-reply at 1727 with foreground-color 6.
     if       ws-reply not = "Y" and not = "y"
              go to  E-o-P-Option.
*>
     perform  acasirsub1-Open-Input.          *> was open input NL
     if       fs-reply not = zero
              display IR912   at 2001
              display IR060   at 2101
              display SY008   at 2201
              accept ws-reply at 2235 with foreground-color 2
              perform acasirsub1-Close
              go to E-O-P-End.
*>
     move     pl-ac  to  owning.
     move     zero   to  sub-nominal.
*>
     perform  acasirsub1-Read-Indexed.
     if       fs-reply not = zero
              display space at 0101 with erase eos
              display pl-ac at 0505 with foreground-color 2
              display IR064 at 0513 with foreground-color 2
              accept ws-reply at 0575 with foreground-color 2
              perform acasirsub1-Close
              go to get-pl.
*>
     if       tipe = "S"
              display space  at 0101 with erase eos
              display  pl-ac at 0501 with foreground-color 2
              display  IR065 at 0507 with foreground-color 2
              display SY008 at 0601
              accept ws-reply at 0635
              perform acasirsub1-Close
              go to get-pl.
*>
     display space at 0501 with erase eol.
     display space at 0601 with erase eol.
*>
     move     PL-AC to PL-Approp-AC.             *> save back to param file at EOJ.
     move     function upper-case (ac) to ws-ac2.
     move     ws-ac2 to ws-ac.
     perform  acasirsub1-Close.                  *> resets last read pointer.
     perform  acasirsub1-Open.                   *> As using read-next now.
*>
 loop-a.
*>-----
*>
     perform  acasirsub1-Read-Next.
     if       fs-reply = 10
              go to  e-o-p-fin.
*>
 by-pass.
*>------
*>
*>     Processing main A/C only
*>
     move     record-1  to  nl-record.       *> mv sorted rec to ws copy
     if       tipe = "S"                     *> was sub
              go to  loop-a.
     move     dr  to  dr-last (j)
     move     cr  to  cr-last (j).
     if       ac  <  "O"
              move  zero  to  dr  cr.
     perform  acasirsub1-Rewrite.             *>     rewrite  record-1.
*>
 loop-b.
*>-----
*>
     perform  acasirsub1-Read-Next.
     if       fs-reply = 10
              go to  e-o-p-fin.
     if       tipe = "S"
              go to loop-b.
     if       sub-nominal  = zero
              go to  by-pass.
     move     dr  to  dr-last (j)
     move     cr  to  cr-last (j).
     if       nl-ac  <  "O"
              move  zero  to  dr  cr.
     move     nl-ac  to  ac.
     perform  acasirsub1-Rewrite.             *>     rewrite  record-1.
     go       to loop-b.
*>
 e-o-p-fin.
*>--------
*>
     perform  VAT-AC-TidyUp.
     perform  PL-Capital-AC-Tidyup.
*>
     move     pl-ac  to  owning.
     move     zero   to  sub-nominal.
*>
 jump-back.
*>--------
*>
     perform  acasirsub1-Read-Indexed.
     if       fs-reply not = zero
              display "PE 009610" at 0505
              display SY008 at 0701
              accept ws-reply at 0733
              close work-file
              perform acasirsub1-Close
              goback.
     if       tipe  = "O"
              go to  update-pl.
     move     owning  to  sub-nominal.
     move     rec-pointer  to  owning.
     go       to jump-back.
*>
 update-pl.
*>--------
*>
     if       net-1  >  zero
              add  net-1  to  cr
     else
              add  net-1  to  dr.
     perform  acasirsub1-Rewrite.             *>     rewrite  record-1.
     perform  acasirsub1-Close.               *>     close    nl
     perform  Reset-Postings.
*>
 E-o-P-End.
     exit     program.
*>
 CR-Total     section.
*>-------------------
*>
     set      z to w.
     add      cr  to    total-1 (z).
     subtract dr  from  total-1 (z).
     if       j = zero
              go to main-exit.
     add      cr-last (j)  to    total-2 (z).
     subtract dr-last (j)  from  total-2 (z).
*>
 main-exit.   exit.
*>
 DR-Total     section.
*>-------------------
     set      z to w.
     add      dr  to    total-1 (z).
     subtract cr  from  total-1 (z).
     if       j = zero
              go to main-exit.
     add      dr-last (j)  to    total-2 (z).
     subtract cr-last (j)  from  total-2 (z).
*>
 main-exit.   exit.
*>
 Line-Total   section.
*>-------------------
*>
*>  This block is for the Finished Account titles ONLY
*>   If values are NON spaces (and applies to) the FIRST
*>     item in the sub group, the default Desc. will be overwritten
*>      from the Final file of same pointer (1,5,9,11,15,18,21,23).
*>
     if       Final-Acs-In-Use = 1
        and   ar1 (y) not = spaces
        and   (y = 1  or =  5 or =  9 or = 11
              or = 15 or = 18 or = 21 or = 23)
              move     ar1 (y)  to  l7-name
     end-if
*>
*> Back to normal Line Total Processing
*>
     multiply total-1 (y)  by  1  giving  l7-value1  rounded.
     if       j > zero
              multiply total-2 (y) by 1 giving l7-value3 rounded
              add total-2 (y)  to  level-12.
*>
     add      total-1 (y)  to  level-11.
     if       total-1 (y)  <  zero
              move  "("  to  l7-sign1
              move  ")"  to  l7-sign2
     else
              move  space  to  l7-sign1  l7-sign2.
*>
     if       total-2 (y)  <  zero and j > zero
              move  "("  to  l7-sign5
              move  ")"  to  l7-sign6
     else
              move  space  to  l7-sign5  l7-sign6.
     go       to by-pass.
*>
 loop-1.
*>
     read     work-file  at end
              go to  main-end.
*>
 by-pass.
*>
     if       ac  <   ar0 (y)
              display "PE 009865" at 2001
              display SY008 at 2411
              accept ws-reply at 2451
              go to  loop-1.
     if       ac > ar0 (y)
              go to main-end.
     move     record-1  to  nl-record.
     move     nl-name of nl-data to  l9-name.
*>
 loop-2.
*>
     read     work-file  at end
              go to  main-end.
*>
     if       sub-nominal  = zero
              perform  write-out
              go to  by-pass.
*>
     add      dr  to  nl-dr.
     add      cr  to  nl-cr.
     if       j = zero
              go to loop-2.
     add      dr-last (j)  to  nl-dr-last (j).
     add      cr-last (j)  to  nl-cr-last (j).
     go       to loop-2.
*>
 main-end.
*>---------
*>
     perform  write-out.
*>
*>    write    print-record  from  line-7 after 1.
*>
 main-exit.   exit.
*>
*>
 Group-Total  section.
*>--------------------
     multiply level-11  by  1  giving  l7-value2  rounded.
     if       j > zero
              multiply level-12 by 1 giving l7-value4 rounded.
*>
*>    if       not  sub-total
*>             multiply  level-11  by  1
*>                       giving  l7-value1  rounded
*>    if       j > zero
*>             multiply  level-12  by  1
*>                       giving  l7-value3  rounded.
     if       sub-total
              move  zero  to  l7-value1  l7-value3.
*>
     if       level-11  <  zero
              move  "("  to  l7-sign3
*>                            l7-sign1
              move  ")"  to  l7-sign4
*>                            l7-sign2
     else
              move  space  to  l7-sign3  l7-sign4.
*>
     if       level-12  <  zero and j > zero
              move  "("  to  l7-sign7
*>                            l7-sign5
              move  ")"  to  l7-sign8
*>                            l7-sign6
     else
              move  space  to  l7-sign7  l7-sign8.
     move     ws-hypens  to  l8-underline1.
     if       j > zero
              move ws-hypens to  l8-underline3.
     if       not  sub-total
              write  print-record  from  line-8 after 1.
     write    print-record  from  line-7 after 1.
*>
     move     spaces to l7-sign1 l7-sign2 l7-sign3 l7-sign4  l7-sign5
                        l7-sign6 l7-sign7 l7-sign8.
*>
     move     zero  to  l7-value1  l7-value2 l7-value3  l7-value4.
     move     spaces to line-8.
*>
 main-exit.   exit.
*>
 write-out    section.
*>-------------------
     if       nl-ac  <  "E"
              perform  cr-value.
     if       nl-ac  >  "D"  AND  <  "J"
              perform  dr-value.
     if       nl-ac  = "I"  OR  "J"
              perform  cr-value.
     if       nl-ac  >  "J"  AND  <  "U"
              perform  dr-value.
     if       nl-ac  >  "T"
              perform  cr-value.
     go       to main-print.
*>
 cr-value.
*>
     move     zero  to  work-1.
     move     zero  to  work-2.
     add      nl-cr to   work-1.
     subtract nl-dr from work-1.
*>
     if       j > zero
              add       nl-cr-last (j)  to    work-2
              subtract  nl-dr-last (j)  from  work-2.
*>
 dr-value.
*>
     move     zero  to  work-1.
     move     zero  to  work-2.
     add      nl-dr to   work-1.
     subtract nl-cr from work-1.
*>
     if       j > zero
              add       nl-dr-last (j)  to    work-2
              subtract  nl-cr-last (j)  from  work-2.
*>
 main-print.
*>
     if       work-1  = zero
       and    work-2  = zero
              go to  main-end.
*>
     if       l9-name = spaces
              go to main-end.
*>
     if       work-1  <  zero
              move  "("  to  l9-sign1
              move  ")"  to  l9-sign2
     else
              move  space  to  l9-sign1  l9-sign2.
*>
     if       work-2  <  zero and j > zero
              move  "("  to  l9-sign3
              move  ")"  to  l9-sign4
     else
              move  space  to  l9-sign3  l9-sign4.
*>
     multiply work-1  by  1  giving  l9-value1  rounded.
     if       j > zero
              multiply work-2 by 1 giving l9-value2 rounded.
*>
     write    print-record  from  line-9 after 1.
*>
 main-end.
*>
     move     spaces  to  l9-name.
     move     zero    to  work-1  work-2.
*>
 main-exit.   exit.
*>********    ****
*>
 ratio        section.
*>-------------------
*>
     write    print-record  from  line-1 after page.
     write    print-record  from  line-2 after 2.
     write    print-record  from  line-10 after 2.
     move     spaces  to  print-record.
     write    print-record after 1.
*>
     add      total-1 (1) total-1 (2) total-1 (3) total-1 (4) giving work-1.
     add      total-1 (5) total-1 (6) total-1 (7) total-1 (8) giving work-2.
     subtract work-2 from work-1 giving work-2.
     divide   work-1 by 100 giving work-3.
     divide   work-2 by work-3 giving l11-ratio rounded.
     move     "Gross Profit % to Sales"  to  l11-name.
     write    print-record  from  line-11 after 2  lines.
*>
     subtract total-1 (11) total-1 (12) total-1 (13) total-1 (14) from work-2.
     divide   work-2 by work-3 giving l11-ratio rounded.
     move     "Net Profit % to Sales"  to  l11-name.
     write    print-record  from  line-11 after  2  lines.
*>
 main-exit.   exit.
*>********    ****
*>
 date-validate section.
*>--------------------
*>
*>************************************************
*>                                               *
*>            date vet section.                  *
*>            =================                  *
*>                                               *
*>    format of date must be as follows:-        *
*>                                               *
*>       ddxmmxyy                                *
*>                                               *
*>    where x can only be one of the following:- *
*>                                               *
*>        / , . -                                *
*>                                               *
*>     and  dd = 1 thru [days in month]          *
*>          mm = 1 thru 12                       *
*>                                               *
*>************************************************
*>
     if       u-bin  >  zero
              go to  ws-unpack.
     move     zero to q.
     inspect  u-date replacing all "." by "/".
     inspect  u-date replacing all "," by "/".
     inspect  u-date replacing all "-" by "/".
     inspect  u-date tallying q for all "/".
*>
     if       q not = 2 or
              u-days  not numeric or
              u-month not numeric or
              u-year  not numeric or
              u-days  < 01 or > 31 or
              u-month < 01 or > 12
              go to main-exit.
*>
     if       u-days > 29 and u-month = 2
              go to main-exit.
*>
     divide   u-year by 4 giving save-date.
     multiply save-date by 4 giving q.
     if       u-month = 2 and
              u-days > 28 and
              q not = u-year
              go to main-exit.
*>
     if       u-days > days (u-month) and
              u-month not = 2
              go to main-exit.
*>
*>********************************************
*>                                           *
*>       date validation & conversion        *
*>       ============================        *
*>                                           *
*>                                           *
*>  requires  date input in u-date           *
*>  & returns  date as binary days since     *
*>    01/01/2000  in  u-bin                  *
*>  date errors returned as u-bin equal zero *
*>                                           *
*>********************************************
*>
     move     zero  to  u-bin.
     move     1     to  ws-work1.
     move     zero  to  ws-work2.
*>
     if       u-year not = zero
              compute u-bin = u-year * 365.
*>
     if       u-bin <   zero
              move  zero  to  u-bin
              go to  pack-end.
*>
 pack-loop-1.
     if       u-year  >  ws-work2
              add  1  to  u-bin
              add  4  to  ws-work2
              go to  pack-loop-1.
*>
     if       u-year =  ws-work2
       and    u-month  >  2
              add  1  to  u-bin.
*>
 pack-loop-2.
     if       u-month  >  12
              move  zero  to  u-bin
              go to pack-end.
     if       u-month  >  ws-work1
              add  days (ws-work1)  to  u-bin
              add  1  to  ws-work1
              go to pack-loop-2.
*>
     if       u-days  not  >  days (ws-work1)
              add  u-days  to  u-bin
              go to  pack-end.
     if       u-days   = 29
        and   u-month  = 2
        and   u-year   = ws-work2
              add  u-days  to   u-bin
     else
              move  zero  to u-bin.
*>
 pack-end.
     go       to main-exit.
*>
*>*************************************
*>                                    *
*>   binary date conversion routine   *
*>   ==============================   *
*>                                    *
*>                                    *
*>  requires  binary input in u-bin   *
*>  &  returns date  in u-date        *
*>                                    *
*>*************************************
*>
 ws-unpack.
*>========
*>
     move     u-bin  to  save-date.
*>
     move     "00/00/00"  to  u-date.
     move     zero  to  u-year.
     move     1  to  u-month.
     move     0  to  u-days.
     move     1  to  ws-work1.
     move     zero  to  ws-work2.
*>
 unpack-loop-1.
*>
     subtract 365  from  save-date.
*>
     if       save-date  >  zero
              add  1  to  u-year
     else
              add  365  to  save-date
              go to  unpack-loop-2.
*>
     if       u-year = ws-work2
          and save-date > 59
              add  4  to  ws-work2
              subtract  1   from  save-date.
*>
     if       save-date  = zero
              subtract  1  from  u-year
              move  365  to  save-date
              go to unpack-loop-2.
*>
     go       to unpack-loop-1.
*>
 unpack-loop-2.
*>
     if       save-date  = 365
              move  31  to   u-days
              move  12  to  u-month
              go to  unpack-end.
*>
 unpack-loop-3.
*>
     subtract days (ws-work1)  from  save-date.
*>
     if       save-date  >  zero
              add  1  to  ws-work1
              add  1  to  u-month
              go to  unpack-loop-3.
*>
     add      save-date  days (ws-work1)  to  u-days.
*>
 unpack-end.
*>
 main-exit.   exit.
*>********    ****
*>
 PL-Capital-AC-Tidyup  section.
*>****************************
 pl-start.
*>
     move     zero to nl-cr nl-dr.
     perform  acasirsub1-Close.       *> resets last read pointer
     perform  acasirsub1-Open.
*>
 pl-a.
*>---
*>
     perform  acasirsub1-Read-Next.
     if       fs-reply = 10
              go to pl-a-end.
     move     function upper-case (ac) to ac2.
     if       ac2 not = ws-ac
              go to pl-a.
     if       tipe = "S"
              go to pl-a.
*>
*>   Got record with same type as PL/capital record
*>
     move     ac2 to ac.
     add      cr to nl-cr.
     add      dr to nl-dr.
     move     zero to cr dr.
     perform  acasirsub1-Rewrite.             *>     rewrite  record-1.
     if       fs-reply not = zero
              display "PE 014900" at 2301
              display SY008 at 2401
              accept ws-reply at 2433
              perform acasirsub1-Close
              goback.
     go       to pl-a.
*>
 pl-a-end.
*>-------
*>
     move     pl-ac to owning.
     move     zero  to sub-nominal.
     perform  acasirsub1-Read-Indexed.
     if       fs-reply not = zero
              display "PE 015000" at 2301 erase eos
              display SY008 at 2401
              accept ws-reply at 2433
              perform acasirsub1-Close
              goback.
*>
*> These PE errors (above and below) should never happen but still must test for them . .
*>
     if       tipe = "S"
              display  pl-ac at 2201 with foreground-color 2 erase eos
              display  IR065 at 2207 with foreground-color 2
              display "PE 015010" at 2301
              display SY008 at 2441
              accept ws-reply at 2474
              perform acasirsub1-Close
              goback.
*>
     move     nl-dr to dr.
     move     nl-cr to cr.
     perform  acasirsub1-Rewrite.             *>     rewrite  record-1.
     if       fs-reply not = zeros
              display "PE 015100" at 2301
              display SY008 at 2401
              accept ws-reply at 2433
              perform acasirsub1-Close
              goback.
     go       to pl-exit.
*>
 pl-exit.     exit.
*>******      ****
*>
 VAT-AC-TidyUp         section.
*>****************************
 vat-a.
*>
     move     def-acs (31) to owning.    *> Vat Input
     move     zero    to sub-nominal.
*>
 vat-b.
*>----
*>
     perform  acasirsub1-Read-Indexed.
     if       fs-reply not = zero
              display space  at 0101 with erase eos
              display owning at 0501  with foreground-color 2
              display "(Default 31 A/C) does not exist..ABORTING" at 0507 with foreground-color 2
              display SY008  at 2441
              accept ws-reply at 2474
              perform  acasirsub1-Close       *> close nl
              goback.
*>
     if       tipe = "S" and
              rec-pointer = owning
              display space at 0101 with erase eos
              display "PE VAT01: Problems with CoA file - Bad coding" at 2301
              display SY008 at 2441
              accept ws-reply at 2474
              perform  acasirsub1-Close       *> close nl
              goback.
*>
*>    Get pointer to Sub nominal to find main a/c but again should not happen
*>
     if       tipe = "S"
              move rec-pointer to owning
              go to vat-b.
*>
*>    At this point, we have got the VAT control Main Account
*>
     move     record-1 to nl-record.
*>
 vat-c.
*>----
*>
     perform  acasirsub1-Read-Next.
     if       fs-reply = 10
              go to vat-finalize.
*>
     if       owning not = nl-owning
              go to vat-finalize.
*>
     if       tipe = "S"
              go to vat-c.
*>
     add      dr   to nl-dr.
     add      cr   to nl-cr.
     move     zero to dr  cr.
*>
     perform  acasirsub1-Rewrite.             *>     rewrite  record-1.
     if       fs-reply not = zero
              display "PE 015370: Problems with CoA file cant rewrite" at 2301
              display SY008 at 2401
              accept ws-reply at 2433
              perform acasirsub1-Close
              goback.
*>
     go       to vat-c.
*>
 vat-finalize.
*>-----------
*>
     move     nl-record to Record-1.
     perform  acasirsub1-Rewrite.             *>     rewrite  record-1.
     if       fs-reply not = zero
              display "PE 015470: Problems on rewrite for CoA file" at 2301
              display SY008 at 2401
              accept ws-reply at 2433
              perform acasirsub1-Close
              goback.
     go       to vat-exit.
*>
 vat-exit.
     exit.
*>
 Reset-Postings        section.
*>****************************
*>
*>  Clear posting file down then reading the NL generates new posting
*>   records for the BF elements found within the NL records.
*>
     perform  acasirsub1-Open-Input.    *>     open     input nl
     move     1 to file-function.
     move     3 to access-type.
*>
*>    open  output post-file.
*>
     perform  acasirsub4.               *>   was "irsub4"
     move     zero to u-bin pl-ac save-sequ.
     move     end-date to u-date.
     perform  date-validate.
     add      1 to u-bin.
     move     spaces to u-date.
     perform  date-validate.
     move     5 to file-function.
*>
 read-n.
*>
     perform  acasirsub1-Read-Next.
     if       fs-reply = 10
              go to main-end.
     if       nl-sub-ac
              go to read-n.
     if       cr = zero and
              dr = zero
              go to read-n.
*>
     if       dr = cr
              go to read-n.
*>
     if       dr > cr
              subtract cr from dr
              move zero to cr
       else
              subtract dr from cr
              move zero to dr.
*>
     move     u-date to post-date.
     move     spaces to post-vat-side.
     add      1 to pl-ac.
     move     pl-ac to post-key.
     move     def-codes (30) to post-code.
     move     zero to vat-ac-def vat-amount.
     move     "Balance Forward" to post-legend.
     move     def-acs (30) to post-cr post-dr.
     if       sub-nominal not = zero
              move sub-nominal to owning.
*>
     if       dr > zero
              move owning to post-dr
              move dr to post-amount
     else
      if      cr > zero
              move owning to post-cr
              move cr to post-amount.
*>
     if       def-acs (30) = post-cr and post-dr
              go to read-n.
*>
     move     5 to file-function.
     perform  acasirsub4.
     go       to read-n.
*>
 main-end.
     perform  acasirsub1-Close.
     move     2 to file-function.
     perform  acasirsub4.
     move     pl-ac to next-post.
*>
 main-exit.
     exit.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
