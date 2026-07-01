       >>source free
*>****************************************************************
*>                       Employee   Entry                        *
*>                                                               *
*>                      This is in four passes namely :-         *
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
 copy "envdiv.cob".
 SPECIAL-NAMES.
       CRT STATUS IS COB-CRT-STATUS.
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
*>
 input-output            section.
 file-control.
 copy "selpyparam1.cob".
 copy "selpyemp.cob".
 copy "selpyhis.cob".
 copy "selpyact.cob".
 copy "selpycoh.cob".
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
 copy "fdpyparam1.cob".
 copy "fdpyemp.cob".
 copy "fdpyhis.cob".
 copy "fdpyact.cob".
 copy "fdpycoh.cob".
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
 copy "wsmaps03.cob".
 copy "wsmaps09.cob".     *> customer-in for chk digit calc
 copy "wsfnctn.cob".
*>
 copy "Test-Data-Flags.cob".  *> set sw-Testing to zero to stop logging.
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
*> Will need to be updated IF any noew states are added.
*>
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
     copy "screenio.cpy".
*>
     copy "an-accept.ws".  *> Support WS for ACCEPT_NUMERIC routine
*>
*>  might be needed
*>
*> copy "wsfnctn.cob".
*> copy "wsmaps03.cob".    *> for maps04
*>
 copy "wstime.cob".
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
     03  value "      |	    Name             [                                ]             |"  line  7 col  1.
     03  value "      |	    Address       1  [                                ]             |"  line  8 col  1.
     03  value "      |                   2  [                                ]             |"  line  9 col  1.
     03  value "      |                   3  [                                ]             |"  line 10 col  1.
     03  value "      |           City or 4  [                                ]             |"  line 11 col  1.
     03  value "      |                      State [  ]             Zip [     ]             |"  line 12 col  1.
     03  value "      |           Phone  [            ]                                     |"  line 13 col  1.
     03  value "      +---------------------------------------------------------------------+"  line 14 col  1.
     03  value "      Soc Sec No.   [            ]                |    Pension (Y/N)      [ ]"  line 15 col  1.
     03  value "      Bank Acct No. [                         ]   |    Job Code	        [   ]"  line 16 col  1.
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
     03  value "Autogen Units	        [        ] |  Head Of Household         (Y or N)[ ]"    line 16 col  1.
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
     copy "an-accept.pl".   *> and  perform  AN-Test-Status
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
     copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
                                          STATUS by PY-PR1-Status.
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
