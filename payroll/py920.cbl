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
 copy "envdiv.cob".
 SPECIAL-NAMES.
       CRT STATUS is COB-CRT-STATUS.
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
*>
 input-output            section.
 file-control.
 copy "selpyparam1.cob".
 copy "selpyact.cob".
*>
 copy "selprint.cob".
*>
 data                    division.
*>================================
*>
 file section.
*>
 copy "fdpyparam1.cob".
 copy "fdpyact.cob".
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
 copy "print-spool-command-p.cob".     *> CHECK PRN file for content
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
     copy "screenio.cpy".
*>
*>     copy "an-accept.ws".  *> Support WS for ACCEPT_NUMERIC routine
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
     copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
                                        STATUS by PY-PR1-Status.
*>
     exit     section.
*>
 *>    copy "an-accept.pl".
*>
     copy "Proc-ZZ100-ACAS-IRS-Calls.cob"
          replacing LEADING ==ZZ100-== by ==ZZ900-==
                    LEADING ==zz100-== by ==ZZ900-==. *> FOR IRS file handler CoA file.
*>
     copy "Proc-ACAS-FH-Calls.cob"                    *> FOR GL  file handler CoA file.
          replacing LEADING  ==ZZ080-== by ==ZZ910-==
                    System-Record by WS-System-Record.
*>
