       >>source free
*>****************************************************************
*>               New  Payroll for USA                            *
*>         Parameter  Menu  &  Fixed  Data  Maintenance          *
*>           Based on CBASIC Code -ish.                          *
*> A lot of files defined here but not used can be REMOVED.          *<<
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
*> 31/03/2026 vbc -    .09 Added support for PRinter controls/fonts/colours etc
*>                         as menu option 2 and moving 2, 3 to 3 & 4 using
*>                         simple accept which may not be enough. ? <<<.
*> 12/04/2026 vbc -    .10 Extra field capture for csv fields etc.
*> 16/04/2026 vbc -    .11 Suport for new ACT file fields - Type & Cat for IRS & GL.
*>
*>   REMEMBER, REMEMBER to change code in PY910 & PY920 to match these changes
*>                      if needed.
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
 copy "envdiv.cob".
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
 copy "selpyparam1.cob".
 copy "selpyded.cob".
 copy "selpyhrs.cob".
 copy "selpyemp.cob".
 copy "selpyhis.cob".
 copy "selpyact.cob".
 copy "selpypay.cob".
 copy "selpychk.cob".
 copy "selpycoh.cob".
 copy "selpycalx.cob".
*>
*> Next 3 are all the same so can use only one stax - may be.
*>
 copy "selpystax.cob".
 copy "selpyswt.cob".
 copy "selpylwt.cob".
*>
 data                    division.
*>================================
*>
 file section.
*>
 copy "fdpyparam1.cob".
 copy "fdpyded.cob".
 copy "fdpyhrs.cob".
 copy "fdpyemp.cob".
 copy "fdpyhis.cob".
 copy "fdpyact.cob".
 copy "fdpypay.cob".
 copy "fdpychk.cob".
 copy "fdpycoh.cob".
 copy "fdpycalx.cob".
*>
*> next 3 are all the same so can use only one stax
*>
 copy "fdpystax.cob".
 copy "fdpyswt.cob".
 copy "fdpylwt.cob".
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(15) value "PY900 (1.0.11)".  *> First release pre testing.
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "Test-Data-Flags.cob".           *> set sw-Testing to zero to stop logging.
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
     03  D                   pic 99       value zero.
     03  F                   pic 99       value zero.
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
     03  WS-Dflt-Cash        binary-char unsigned   value 1.  *> via PY-PR1-Offset-Cash-Acct  CB is 011100 Cash Type 0/C.
     03  WS-Dflt-Liability   binary-char unsigned   value 2.  *> CB is 121100 Accrued Liability   Type 1/L.
     03  WS-Dflt-Expense     binary-char unsigned   value 3.  *> CB is 411100 Salary Expense      TYpe 4/E.
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
     03  PY127           pic x(20) value "PY127 Must be C or T".
     03  PY128           pic x(36) value "PY128 Bad value Field - Range 1 - 13".  *> May get extended to 20 max.
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
     copy "screenio.cpy".
*>
     copy "an-accept.ws".  *> Support WS for ACCEPT_NUMERIC routine
*>
 copy "wstime.cob".
*>  ACAS for IRS FH support CoA Ledgers
 copy "irswsnl.cob" replacing NL-Record by WS-IRSNL-Record.
*> ACAS for  GL FH  support CoA Ledgers
 copy "wsledger.cob".
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob"   replacing System-Record by WS-System-Record.
 copy "wsnames.cob".
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
     03  value "2. Printer Controls" line  6 col  21 erase eos.
     03  value "3. Pay Intervals and Default Employee Payroll Data"
                                     line  7 col  21.
     03  value "4. Payroll System Configuration and GL Interface"
                                     line  8 col  21.
     03  value "N. Next - System Wide Deduction Menu. etc"
                                     line 10 col  21.
     03  value "X or Esc to quit menu option"
                                     line 12 col  21.
     03  value "Select Option  [ ]"
                                     line 14 col 30.
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
 01  SS-Param-1-Extra-Payroll-Details-1 background-color cob-color-black
                                        foreground-color cob-color-green
                                        erase eos.
     03  from  Prog-Name  pic x(15)  line  1 col  1 foreground-color 2.
     03  value "Payroll Parameter Set Up"    col 29.
     03  from  U-Date     pic x(10)          col 71 foreground-color 2.
     03  from  Usera      pic x(32)  line  3 col  1.
     03  value "Printer Controls needed (Y or N) ["   line  5 col  1.
     03  using PY-PR1-Print-Ctl-Flag pic x            line  5 col 35.
     03  value "]"                                    line  5 col 36.
     03  value "Code for Small  Font   ["             line  6 col  1.
     03  using PY-PR1-Font-Small     pic x(32)        line  6 col 25.
     03  value "]"                                    line  6 col 57.
     03  value "Code for Normal Font   ["             line  7 col  1.
     03  using PY-PR1-Font-Normal    pic x(32)        line  7 col 25.
     03  value "]"                                    line  7 col 57.
     03  value "Code for Reset  Font   ["             line  8 col  1.
     03  using PY-PR1-Font-Reset     pic x(32)        line  8 col 25.
     03  value "]"                                    line  8 col 57.
     03  value "Code for Colour 1      ["             line  9 col  1.
     03  using PY-PR1-Colour-1       pic x(32)        line  9 col 25.
     03  value "]"                                    line  9 col 57.
     03  value "Code for Colour 2      ["             line 10 col  1.
     03  using PY-PR1-Colour-2       pic x(32)        line 10 col 25.
     03  value "]"                                    line 10 col 57.
     03  value "Code for Colour Reset  ["             line 11 col  1.
     03  using PY-PR1-Colour-Reset   pic x(32)        line 11 col 25.
     03  value "]"                                    line 11 col 57.
*>
     03  value "B2B Formatting"                       line 13 col  1.
     03  value "File Type C = csv, T = Text [ ]"      line 14 col  1.
 *>    03  using PY-PR1-B2B-File-Type  pic x            line 14 col 30.
     03  value 'For csv quote Character ["]'          line 14 col 41.
*>     03  using PY-PR1-Quote-Char                      line 14 col 66.
     03  value "Values of Field order 99 x 20 - 00=Not used, Range 01 - 13"
                                                      line 16 col  1.
 *>    03  using PY-PR1-B2B-Field-Order (D) pic 99x            line 17 col  1  occurs 20.
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
     03  value "Account Type: [ / ] {0,1,4/C,L,E}"                     line  8 col 41.
     03  using Act-Type  pic 9                                         line  8 col 56 foreground-color 3.
     03  using Act-Cat   pic x                                         line  8 col 58 foreground-color 3.
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
     03  value "Entry #   Acct #  T/C   Description"                   line  6 col  1.
     03  from  Act-No    pic 99                                        line  7 col  2 foreground-color 3.
     03  from  Act-GL-No pic 9(6)                                      line  7 col 11 foreground-color 3.
     03  from  Act-Type  pic 9                                         line  7 col 19 foreground-color 3.
     03  value "/"                                                     line  7 col 20.
     03  from  Act-Cat   pic x                                         line  7 col 21 foreground-color 3.
     03  from  Act-Desc  pic x(24)                                     line  7 col 25 foreground-color 2.
*>
     03  Value "* Escape to quit Entry"                                line 22 col  1 foreground-color 6.
*>
*>
*> Stored here for inclusion in correct programs
*>



*> 	Transaction Codes                            Tax Exclusion Codes
*>  -----------------                            -------------------
*>
*>  0  Rate0 Pay	       12  Sick Pay	          1  Subject to all taxes
*>  1  Rate1 Pay	       13  Vacation Pay          and percent deductions
*>  2  Rate2 Pay	       14  Other Excl. Pay
*>  3  Rate3 Pay	       15  Exp. Reimburse.    2  Subject to all taxes
*>  4  Rate4 Pay	       17  Other Pay             and percent deductions
*>  5  Vacation Taken      18  Tips Reported         except FICA
*>  6  Sick Leave Taken    27  Advance Repay.
*>  7  Comp Time Taken     28  FWT Add-On         3  Subject to all taxes
*>  8  Comp Time Earned    29  SWT Add-On            and percent deductions
*>  9  Bonus	           30  LWT Add-On            except FWT, SWT, & LWT
*> 10  Tips Collected      31  FICA Add-On
*> 11  Advance	           50  Other Deds.	      4  Not subject to taxes or
*> 				  		                             percent deductions.
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
*>         The Computer Is Printing Check Number	nnnnnn
*>         The Check Is Payable To Employee Number	nnnnnnn
*>
*>          Press the Escape key to Stop
*>          Press the Return key to Continue   [ ]
*>
*>          The Check Amount Exceeds The Maximum Allowed.
*>          This Check Will Be Voided.
*>
*>                   All Checks Have Been Printed
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
*>		PYSWTaa.101
*>
*> Where "aa" is the two character state abbreviation.  There are four
*> tax table files for California:
*>
*>   Merge into one.
*>
*>	PYCALS.101	     [S=Single]
*>	PYCALM.101	     [M=Married]
*>	PYCALH.101	     [H=Head of Household]
*>	PYCALX.100
*>**
*>	PAYROLL SYSTEM TRANSACTION CODES
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
*>           Used?   No          Rate	       Limit
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
*>	      FEDERAL WITHHOLDING TAX TABLE ENTRY
*>
*>	       ALLOWANCE AMOUNT:  [ 1000.00]
*>
*>       M A R R I E D 	         S I N G L E
*>     CUTOFF    PERCENT       CUTOFF   PERCENT
*>1. [ 2,400.00] [15.00]	[ 1,420.00] [15.00]
*>2. [ 6,600.00] [18.00]	[ 3,300.00] [18.00]
*>3. [10,900.00] [21.00]	[ 6,800.00] [21.00]
*>4. [15,000.00] [24.00]	[10.200.00] [26.00]
*>5. [19,200.00] [28.00]	[14,200.00] [30.00]
*>6. [23,600.00] [32.00]	[17,200.00] [34.00]
*>7. [28,900.00] [37.00]	[22,500.00] [39.00]
*>
*>     (Figure 10.2: Default Federal Tax Table)  via py900
*>**
*>         SYSTEM EARNING AND DEDUCTION INFORMATION
*>
*>   USED?    DESC       E/D ACCT A/P  FACTOR   LIMITED  LIMIT   XLCD CAT
*>
*> 1. [N] [	           ] [E] [  ] [A] [	  0.00]   [Y] [	  0.00]   [1] [2]
*> 2. [N] [	           ] [E] [  ] [A] [	  0.00]   [Y] [	  0.00]   [1] [2]
*> 3. [N] [	           ] [E] [  ] [A] [	  0.00]   [Y] [	  0.00]   [1] [2]
*> 4. [N] [	           ] [E] [  ] [A] [	  0.00]   [Y] [	  0.00]   [1] [2]
*> 5. [N] [	           ] [E] [  ] [A] [	  0.00]   [Y] [	  0.00]   [1] [2]
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
 aa013-Print-Controls.
*>
     if       Menu-Reply = 2
              move     maps-ser-nn to curs2
              display  space at 0101 with erase eos    *> Clear anything not already done
              display  SS-Param-1-Extra-Payroll-Details-1
              accept   SS-Param-1-Extra-Payroll-Details-1
              initialise
                       PY-PR1-B2B-Fields
*>
*> Next for B2B o/p file format and order
*>
              accept   PY-PR1-B2B-File-Type at 1430 UPPER foreground-color 3
              if       PY-PR1-B2B-File-Type not = "C" and not = "T"
                       display  PY127  at line WS-23-Lines col 1 foreground-color 6 erase eos
                       go to aa013-Print-Controls
              else
                       display  spaces at line WS-23-Lines col 1 erase eos
              end-if
              accept   PY-PR1-Quote-Char at 1466 foreground-color 3
              move     1    to  F
                                D
              move     1700 to  Curs
              perform  forever
                       if       D > 13    *> Change if field count increase beyond 13
                                exit perform
                       end-if
                       if       D < 13
                                add      F 2  giving Cole
                                display  "," at line 17 col Cole foreground-color 2
                       end-if
                       accept   PY-PR1-B2B-Field-Order (D) at line 17 col F foreground-color 3
                       if       COB-CRT-Status = COB-SCR-ESC
                                exit perform
                       end-if
                       if       PY-PR1-B2B-Field-Order (D) > 13           *> Range 00 to 13, chg if field cnt increases beyond 13
                                display  PY128  at line WS-23-Lines col 1 foreground-color 6 erase eos
                                move     zeros to PY-PR1-B2B-Field-Order (D)
                                exit perform cycle
                       else
                                display  spaces at line WS-23-Lines col 1 erase eos
                       end-if
                       add      1 to D
                       add      3 to F
                       exit perform cycle
              end-perform
*>
              move     1 to RRN
              rewrite  PY-Param1-Record               *> previous exists
              perform  aa125-Test-PR1-Status
              go to    aa010-Param-Menu-1.
*>
 aa012-Retry-2.
*> Pay intervals
     if       Menu-Reply = 3
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
     if       Menu-Reply = 4
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
*>  We test that these numbers exist & if not, abort this function
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
 ab030-Get-Nominal.    *> Also see ab050 for GL
     perform  Forever
              move     zeros   to Act-No
                                  Act-GL-No
                                  Act-Type
              move     spaces  to Act-Desc
                                  Act-Cat
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
              accept   Act-Type  at 0856 foreground-color 3
              accept   Act-Cat   at 0858 foreground-color 3 UPPER
*>
*> These use FIXED positions for the four classes - Cash, Liab, Exp & Cost
*>
              evaluate Act-No
                       when 1 move Act-GL-No to WS-Dflt-Cash
                       when 2 move Act-GL-No to WS-Dflt-Liability
                       when 3 move Act-GL-No to WS-Dflt-Expense  *> ????
                       when 4 move Act-GL-No to WS-Dflt-Cost
                       when other    *> default ? Should this bit be done ?
                              move PY-PR1-Dflt-Dist-Acct to  WS-Dflt-Expense
              end-evaluate
*>
*>                could be using ACT-Cat for C=1,L=2,E=3 or #4  or
*>                               ACT-Type for 0.1.4 for #1,#2,#3 else #4
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
*>
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
     perform  Forever
              move     zeros   to Act-No
                                  Act-GL-No
                                  Act-Type
              move     spaces  to Act-Desc
                                  Act-Cat
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
              accept   Act-Type  at 0856 foreground-color 3
              accept   Act-Cat   at 0858 foreground-color 3 UPPER
*>
*> These use FIXED positions for the four classes - Cash, Liab, Exp & Cost
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
*>                could be using ACT-Cat for C=1,L=2,E=3 or #4  or
*>                               ACT-Type for 0.1.4 for #1,#2,#3 else #4
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
*>  Now preset values from dedent  NEEDS UPDATE FOR 2026 values
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
 ZZ040-Evaluate-Message      Section.
*>**********************************
*>
*> For PY-PR1 parameter file anfd other using PR-PR1-Status.
*>
     copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
                                        STATUS by PY-PR1-Status.
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
     copy "an-accept.pl".
*>
     copy "Proc-ZZ100-ACAS-IRS-Calls.cob"
          replacing LEADING ==zz100-== by ==ZZ900-==.
  *>                  ==zz100-Exit== by ZZ900-Exit==.   *> FOR IRS handling CoA file.
*>
     copy "Proc-ACAS-FH-Calls.cob"   *> FOR GL file handler CoA file.
          replacing LEADING  ==ZZ080-== by ==ZZ910-==
                    System-Record by WS-System-Record.
*>
