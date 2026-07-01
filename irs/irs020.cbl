       >>source free
*>*********************************************************************
*>                                                                    *
*>  P O S T I N G    D E F A U L T S   F I L E    U T I L I T I E S   *
*>                                                                    *
*>*********************************************************************
*>
 identification division.
 program-id.            irs020.
*> Author.              Cobol Conversion by Vincent Bryan Coen. FIDPM FBCS
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Postings Default File Utilities Program.
*>                      Setup, Amend, Display and Print.
*> Function Keys Used.
*>                      F1 through F5 - Menu only.
*>**
*>**
*> Version.             See PROG-NAME in ws.
*>**
*> Calls.
*>                      acasirsub1  ->
*>                       irsnominalMT
*>                      acasirsub3 ->
*>                       irsdfltMT
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
*>                      IR020 Give Default to amend - [  ]  (Use 00 to quit)
*>                      IR021 Account not found. Try again!
*>                      IR022 Hit return to continue
*>                      IR023 End of listing. Hit return for Menu
*>                      IR024 You must Setup Chart of Accounts first (Selection no. 2)
*>                      IR025 You MUST set up accounts 30, 31 and 32
*>**
*> Changes.
*> 28/06/83 vbc - allow final a/c 2 b displayed before change.
*> 11/07/83 vbc - get default 30 on setup,force code.
*> 11/07/83 vbc - check if coa exists if not exit.
*> 25/07/83 vbc - fix print routine,set ans to 0 1st.
*> 15/09/83 vbc - clean up print layout.
*> 28/05/84 vbc - hilite disp heads.
*> 14/04/85 vbc - exclude finals & reduce print to 79 chars.
*> 26/09/89 vbc - 2.53
*>                mods for cobol/2 change print to 80 chars.
*> 21/01/09 vbc - Migration to Open/Gnu Cobol as version 3.
*> 21/02/09 vbc - Cosmetics in the displays for setup and amend
*> 21/09/10 vbc - Added print spool.
*>                .10 fix for portrait printing
*> 11/10/16 vbc - .11 Print out Finished A/C titles.
*> 01/12/16 vbc - 3.02
*>                .12 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*> 20/12/16 vbc -     All irs progs call copybook Proc-ZZ100-ACAS-IRS-Calls.
*> 25/12/17 vbc -     RW version available.
*> 29/01/18 vbc - .13 Changed copies to use copybooks where poss.
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 07/02/18 vbc - .14 Check for ESC on amend as well as zero entered.
*> 10/02/18 vbc - .15 Renamed IR011-16 to IR911-16 and others.
*> 12/02/18 vbc - .16 Changed PL-Approp from 5 to 6. Yes IRS uses 5 but GL is 6.
*> 14/02/18 vbc - .17 In Set up, check that def. acs 30 - 32 have been created
*>                    (non zero values) else display IR025, SY008
*>                    then switch to Amend mode.
*> 02/05/18 vbc - .18 Added Time to report (in Listing) & do this for most of the
*>                    reports in IRS as it is hard to work out the latest reports.
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
 copy  "envdiv.cob".
*>
 input-output section.
 file-control.
*>
     select  print-file     assign  "prt-1"
                            organization line sequential.
*>
 data division.
 file section.
*>
 fd  print-file.
 01  print-record.
     03  filler          pic x(80).
*>
 working-storage section.
 01  prog-name           pic x(16)    value "irs020 (3.3.00)".
 copy "irsprint-spool-command-p.cob".
*>
 01  filler.
     03  menu-reply      pic 9.
     03  ws-reply        pic x.
     03  input-type      pic x.
         88  sub-input        value  "Y".
     03  ws-pass         pic x(4).
     03  A               pic 99    comp value zero.      *> 4 Final print
     03  B               pic 99    comp value zero.      *> 4 Final print
     03  w               pic 99.
     03  y               pic 99.
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
     03  ws-acs          pic 9(5).
     03  ws-codes        pic xx.
     03  ws-codes2       pic xx.
     03  ws-vat          pic x.
     03  ws-vat2         pic x.
     03  filler                           value "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
         05  WS-Alpha-Cd1 pic x occurs 26.
*>
 copy  "irswsnl.cob"   replacing NL-Record by WS-IRSNL-Record.
 copy  "wsfnctn.cob".
 copy  "irswsdflt.cob" replacing Default-Record by WS-IRS-Default-Record.
*>
*>                  finals not in use at present but included ?
 copy  "irswsfinal.cob".
*>
 01  filler.
     03  line-1.
       05  p-user        pic x(24).
       05  filler        pic x(5)     value spaces.
       05  filler        pic x(25)    value "Incomplete Records System".
       05  filler        pic x(11)    value spaces.
       05  p-date        pic x(8).
       05  p-time        pic x(6)     value spaces.   *> BHH:MM
*>
     03  line-3.
       05  p-client      pic x(24).
       05  filler        pic x(9)     value spaces.
       05  filler        pic x(16)    value "Posting Defaults".
       05  filler        pic x(23)    value spaces.
*>
     03  line-4.
       05  filler        pic x(64)    value
       "             A/C Nos     ------Description------    Code VAT".
*>
     03  line-5.
       05  filler        pic x(10)    value spaces.
       05  p-num         pic z9bb.
       05  p-ac          pic zzzz9b   blank when zero.
       05  filler        pic x(5)     value spaces.
       05  p-desc        pic x(25).
       05  filler        pic x(3)     value spaces.
       05  p-code        pic xx.
       05  filler        pic x(5)     value spaces.
       05  p-vat         pic x.
*>
     03  line-6.
         05  p-client-2  pic x(24).
         05  filler      pic x(9)     value spaces.
         05  filler      pic x(17)    value "Finished Accounts".
         05  filler      pic x(22)    value spaces.
*>
     03  line-7.
         05  filler      pic x(80)    value
         "    A/C       Heading               Sign" &
         "    A/C       Heading               Sign".

     03  line-8.
         05  filler      pic x(50)    value
         "   Type                                    Type".
*>
     03  line-9.
       04  filler occurs 2.
         05  filler      pic x(4)     value spaces.
         05  filler      pic x        value "<".
         05  Pos-1       pic x.
         05  filler      pic x        value ">".
         05  filler      pic xxx      value spaces.
         05  Par-1       pic x(24).
         05  filler      pic xxx      value spaces.
         05  filler      pic x        value "[".
         05  Par-2       pic x.
         05  filler      pic x        value "]".
*>
 01  All-My-Constants      pic 9(4).
     copy "screenio.cpy".
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
 *>    03  WS-IRSNL-Record       pic x.
 *>    03  WS-IRS-Default-Record pic x.
     03  Posting-Record        pic x.
     03  WS-IRS-Posting-Record pic x.
 *>    03  Final-Record          pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide      USED are :
     03  SY008          pic x(32) value "SY008 Note message & Hit return ".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, Fs-reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, Fs-reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, Fs-reply = ".
     03  IR914          pic x(51) value "IR914 Error on irspostingMT processing, Fs-reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, Fs-reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, Fs-reply = ".
*> Module specific  USED are :
     03  IR020          pic x(52) value "IR020 Give Default to amend - [  ]  (Use 00 to quit)".
     03  IR021          pic x(35) value "IR021 Account not found. Try again!".
     03  IR022          pic x(28) value "IR022 Hit return to continue".
     03  IR023          pic x(42) value "IR023 End of listing. Hit return for Menu ".
     03  IR024          pic x(62) value
                 "IR024 You must Setup Chart of Accounts first (Selection no. 2)".
     03  IR025          pic x(44) value "IR025 You MUST set up accounts 30, 31 and 32".
*>
 linkage section.
 copy  "irswssystem.cob"
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
 screen section.
*>--------------
 01  menu-screen-1             background-color cob-color-black
                               foreground-color cob-color-green.
     03  pic x(16) from prog-name          line 1 col 1   blank screen.
     03  value "Default File Utilities"    line 1 col 29
                               foreground-color cob-color-white
                               background-color cob-color-blue
                                        reverse-video.
     03  pic x(8) from run-date            line 1 col 73.
     03  value "Client -"                  line 3 col 1.
     03  pic x(29) from client             line 3 col 10
                               foreground-color cob-color-cyan.
     03  value "Start date -"              line 3 col 39.
     03  pic x(8) from start-date          line 3 col 52
                               foreground-color cob-color-cyan.
     03  value "End date -"                line 3 col 62.
     03  pic x(8) from end-date            line 3 col 73
                               foreground-color cob-color-cyan.
     03  value "Select the required function by number    ["
                                           line 5 col 1.
     03  pic x using menu-reply  auto      line 5 col 44
                               foreground-color cob-color-yellow.
     03  value "]"                         line 5 col 45.
     03  value "(1)  Set-Up Default Accounts" line  8 col 6.
     03  value "(2)  Amend  Default Accounts" line 10 col 6.
     03  value "(3)  Display the Defaults"    line 12 col 6.
     03  value "(4)  Print   the Defaults"    line 14 col 6.
     03  value "(5)  Set-Up Final Accounts"   line 17 col 6.
     03  value "(9)  Return to System Menu"   line 20 col 6.
     03  value "F1 to F5 = options 1 to 5;  Return to Accept " &
             "data;   Escape to quit"               line 23 col 1
                       highlight foreground-color cob-color-white.
*>
 01  Setup-Screen-1            background-color cob-color-black
                               foreground-color cob-color-green.
     03  pic x(16) from prog-name          line 1 col 1   blank screen.
     03  value "Default Accounts Setup"    line 1 col 29
                               foreground-color cob-color-white
                               background-color cob-color-blue
                                reverse-video.
     03  pic x(8) from run-date            line 1 col 73.
*>
 01  Setup-Screen-2Q.
     03  value "Client -"                  line 3 col  1.
     03  pic x(24) from client             line 3 col 10 foreground-color cob-color-cyan.
     03  value "Start date -"              line 3 col 39.
     03  pic x(8) from start-date          line 3 col 52 foreground-color cob-color-cyan.
     03  value "End date -"                line 3 col 62.
     03  pic x(8) from end-date            line 3 col 73 foreground-color cob-color-cyan.
     03  value "Add to Existing Defaults (Y/N) ? - ["
                                           line 5 col 1.
     03  pic x to ws-reply  auto           line 5 col 37 foreground-color cob-color-yellow.
     03  value "]"                         line 5 col 38.
     03  value "N.B. (1) If first time setup for this client an" &
               "swer no (N)"               line 7 col  1 background-color cob-color-red
                                                         foreground-color cob-color-white.
     03  value "(2) Answering no (N)"      line 8 col  6 background-color cob-color-red
                                                         foreground-color cob-color-white.
     03  value "destroys"                  line 8 col 27 foreground-color cob-color-white
                                                         background-color cob-color-red
                                                                blink reverse-video.
     03  value "the existing defaults"     line 8 col 36 background-color cob-color-red
                                                         foreground-color cob-color-white.
     03  value "Escape to quit;    Return to Accept data"
                                           line 23 col 1 highlight foreground-color cob-color-white.
*>
 01  Amend-Screen-1                                      background-color cob-color-black
                                                         foreground-color cob-color-green.
     03  pic x(16) from prog-name          line 1 col  1  blank screen.
     03  value "Default Accounts Amendments" line 1 col 28 foreground-color cob-color-white
                                                           background-color cob-color-blue
                                                                reverse-video.
     03  pic x(8) from run-date            line 1 col 73.
*> setup
 01  Setup-Amend-Screen-3                                 background-color cob-color-black
                                                          foreground-color cob-color-green.
     03  value "Client -"                  line  3 col  1.
     03  pic x(24) from client             line  3 col 10 foreground-color cob-color-cyan.
     03  value "Start date -"              line  3 col 39.
     03  pic x(8) from start-date          line  3 col 52 foreground-color cob-color-cyan.
     03  value "End date -"                line  3 col 62.
     03  pic x(8) from end-date            line  3 col 73 foreground-color cob-color-cyan.
     03  value "A/C Nos"                   line  5 col  4.
     03  value "Description"               line  5 col 14.
     03  value "Code VAT   A/C Nos"        line  5 col 33.
     03  value "Description"               line  5 col 54.
     03  value "Code VAT"                  line  5 col 73.
     03  value " "  erase eol              line  6 col 1.
     03  value "01 [00000]                      [AB] [C]" &
            "17 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "02 [00000]                      [AB] [C]" &
            "18 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "03 [00000]                      [AB] [C]" &
            "19 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "04 [00000]                      [AB] [C]" &
            "20 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "05 [00000]                      [AB] [C]" &
            "21 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "06 [00000]                      [AB] [C]" &
            "22 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "07 [00000]                      [AB] [C]" &
            "23 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "08 [00000]                      [AB] [C]" &
            "24 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "09 [00000]                      [AB] [C]" &
            "25 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "10 [00000]                      [AB] [C]" &
            "26 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "11 [00000]                      [AB] [C]" &
            "27 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "12 [00000]                      [AB] [C]" &
            "28 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "13 [00000]                      [AB] [C]" &
            "29 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "14 [00000]                      [AB] [C]" &
            "30 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "15 [00000]                      [AB] [C]" &
            "31 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
     03  value "16 [00000]                      [AB] [C]" &
            "32 [00000]                      [DE] [F]"
                                           line plus 1 col 1.
*> after display need to update cc1&2 with 1 - 16 & cc41&42 with 17 - 32
*>  cc4/44 = a/c-nos , vat 38/78, 33/73 code
*>
 01  Display-Screen-1                                     background-color cob-color-black
                                                          foreground-color cob-color-green.
     03  pic x(16) from prog-name          line  1 col  1      blank screen.
     03  value "Default Accounts Display"  line  1 col 27 foreground-color cob-color-white
                                                          background-color cob-color-blue
                                                                reverse-video.
     03  pic x(8) from run-date            line  1 col 73.
*>
 01  Finished-Account-Setup-Screen-1                      background-color cob-color-black
                                                          foreground-color cob-color-green.
     03  value "Client "                   line  1 col  1         blank screen.
     03  pic x(24) from client             line  1 col  8 foreground-color cob-color-cyan.
     03  value "Finished Accounts Setup"   line  1 col 34 foreground-color cob-color-white
                                                          background-color cob-color-blue
                                                                 reverse-video.
     03  pic x(8) from run-date            line  1 col 73.
     03  value "Trading and Profit & Loss Account              " &
               "   Balance Sheet"          line  3 col  4.
     03  value "--------Heading---------  Sign          -------" &
               "-Heading---------  Sign"   line  4 col 10.
     03  value "Income Accounts"           line  5 col  1.
     03  value "Fixed     Assets"          line  5 col 41.
     03  value "<A>   ["                   line  6 col  3.
     03  pic x(24) using ar1-1             line  6 col 10 foreground-color 3.
     03  value "] ["                       line  6 col 34.
     03  pic x     using ar2-1             line  6 col 37 foreground-color 3.
     03  value "]    <O>   ["              line  6 col 38.
     03  pic x(24) using ar1-15            line  6 col 50 foreground-color 3.
     03  value "] ["                       line  6 col 74.
     03  pic x     using ar2-15            line  6 col 77 foreground-color 3.
     03  value "]"                         line  6 col 78.
     03  value "<B>   ["                   line  7 col  3.
     03  pic x(24) using ar1-2             line  7 col 10 foreground-color 3.
     03  value "] ["                       line  7 col 34.
     03  pic x     using ar2-2             line  7 col 37 foreground-color 3.
     03  value "]    <P>   ["              line  7 col 38.
     03  pic x(24) using ar1-16            line  7 col 50 foreground-color 3.
     03  value "] ["                       line  7 col 74.
     03  pic x     using ar2-16            line  7 col 77 foreground-color 3.
     03  value "]"                         line  7 col 78.
     03  value "<C>   ["                   line  8 col  3.
     03  pic x(24) using ar1-3             line  8 col 10 foreground-color 3.
     03  value "] ["                       line  8 col 34.
     03  pic x     using ar2-3             line  8 col 37 foreground-color 3.
     03  value "]    <Q>   ["              line  8 col 38.
     03  pic x(24) using ar1-17            line  8 col 50 foreground-color 3.
     03  value "] ["                       line  8 col 74.
     03  pic x     using ar2-17            line  8 col 77 foreground-color 3.
     03  value "]"                         line  8 col 78.
     03  value "<D>   ["                   line  9 col  3.
     03  pic x(24) using ar1-4             line  9 col 10 foreground-color 3.
     03  value "] ["                       line  9 col 34.
     03  pic x     using ar2-4             line  9 col 37 foreground-color 3.
     03  value "]"                         line  9 col 38.
     03  value "Direct Cost Accounts"      line 10 col  1.
     03  value "Current Assets"            line 10 col 41.
     03  value "<E>   ["                   line 11 col  3.
     03  pic x(24) using ar1-5             line 11 col 10 foreground-color 3.
     03  value "] ["                       line 11 col 34.
     03  pic x     using ar2-5             line 11 col 37 foreground-color 3.
     03  value "]    <R>   ["              line 11 col 38.
     03  pic x(24) using ar1-18            line 11 col 50 foreground-color 3.
     03  value "] ["                       line 11 col 74.
     03  pic x     using ar2-18            line 11 col 77 foreground-color 3.
     03  value "]"                         line 11 col 78.
     03  value "<F>   ["                   line 12 col  3.
     03  pic x(24) using ar1-6             line 12 col 10 foreground-color 3.
     03  value "] ["                       line 12 col 34.
     03  pic x     using ar2-6             line 12 col 37 foreground-color 3.
     03  value "]    <S>   ["              line 12 col 38.
     03  pic x(24) using ar1-19            line 12 col 50 foreground-color 3.
     03  value "] ["                       line 12 col 74.
     03  pic x     using ar2-19            line 12 col 77 foreground-color 3.
     03  value "]"                         line 12 col 78.
     03  value "<G>   ["                   line 13 col  3.
     03  pic x(24) using ar1-7             line 13 col 10 foreground-color 3.
     03  value "] ["                       line 13 col 34.
     03  pic x     using ar2-7             line 13 col 37 foreground-color 3.
     03  value "]    <T>   ["              line 13 col 38.
     03  pic x(24) using ar1-20            line 13 col 50 foreground-color 3.
     03  value "] ["                       line 13 col 74.
     03  pic x     using ar2-20            line 13 col 77 foreground-color 3.
     03  value "]"                         line 13 col 78.
     03  value "<H>   ["                   line 14 col  3.
     03  pic x(24) using ar1-8             line 14 col 10 foreground-color 3.
     03  value "] ["                       line 14 col 34.
     03  pic x     using ar2-8             line 14 col 37 foreground-color 3.
     03  value "]"                         line 14 col 38.
     03  value "Sundry Income Accounts"    line 15 col  1.
     03  value "Current Liabilities"       line 15 col 41.
     03  value "<I>   ["                   line 16 col  3.
     03  pic x(24) using ar1-9             line 16 col 10 foreground-color 3.
     03  value "] ["                       line 16 col 34.
     03  pic x     using ar2-9             line 16 col 37 foreground-color 3.
     03  value "]    <U>   ["              line 16 col 38.
     03  pic x(24) using ar1-21            line 16 col 50 foreground-color 3.
     03  value "] ["                       line 16 col 74.
     03  pic x     using ar2-21            line 16 col 77 foreground-color 3.
     03  value "]"                         line 16 col 78.
     03  value "<J>   ["                   line 17 col  3.
     03  pic x(24) using ar1-10            line 17 col 10 foreground-color 3.
     03  value "] ["                       line 17 col 34.
     03  pic x     using ar2-10            line 17 col 37 foreground-color 3.
     03  value "]    <V>   ["              line 17 col 38.
     03  pic x(24) using ar1-22            line 17 col 50 foreground-color 3.
     03  value "] ["                       line 17 col 74.
     03  pic x     using ar2-22            line 17 col 77 foreground-color 3.
     03  value "]"                         line 17 col 78.
     03  value "Indirect Cost Accounts"    line 18 col  1.
     03  value "Capital Accounts"          line 18 col 41.
     03  value "<K>   ["                   line 19 col  3.
     03  pic x(24) using ar1-11            line 19 col 10 foreground-color 3.
     03  value "] ["                       line 19 col 34.
     03  pic x     using ar2-11            line 19 col 37 foreground-color 3.
     03  value "]    <W>   ["              line 19 col 38.
     03  pic x(24) using ar1-23            line 19 col 50 foreground-color 3.
     03  value "] ["                       line 19 col 74.
     03  pic x     using ar2-23            line 19 col 77 foreground-color 3.
     03  value "]"                         line 19 col 78.
     03  value "<L>   ["                   line 20 col  3.
     03  pic x(24) using ar1-12            line 20 col 10 foreground-color 3.
     03  value "] ["                       line 20 col 34.
     03  pic x     using ar2-12            line 20 col 37 foreground-color 3.
     03  value "]    <X>   ["              line 20 col 38.
     03  pic x(24) using ar1-24            line 20 col 50 foreground-color 3.
     03  value "] ["                       line 20 col 74.
     03  pic x     using ar2-24            line 20 col 77 foreground-color 3.
     03  value "]"                         line 20 col 78.
     03  value "<M>   ["                   line 21 col  3.
     03  pic x(24) using ar1-13            line 21 col 10 foreground-color 3.
     03  value "] ["                       line 21 col 34.
     03  pic x     using ar2-13            line 21 col 37 foreground-color 3.
     03  value "]    <Y>   ["              line 21 col 38.
     03  pic x(24) using ar1-25            line 21 col 50 foreground-color 3.
     03  value "] ["                       line 21 col 74.
     03  pic x     using ar2-25            line 21 col 77 foreground-color 3.
     03  value "]"                         line 21 col 78.
     03  value "<N>   ["                   line 22 col  3.
     03  pic x(24) using ar1-14            line 22 col 10 foreground-color 3.
     03  value "] ["                       line 22 col 34.
     03  pic x     using ar2-14            line 22 col 37 foreground-color 3.
     03  value "]    <Z>   ["              line 22 col 38.
     03  pic x(24) using ar1-26            line 22 col 50 foreground-color 3.
     03  value "] ["                       line 22 col 74.
     03  pic x     using ar2-26            line 22 col 77 foreground-color 3.
     03  value "]"                         line 22 col 78.
     03  value "P & L Appropriation Account ["  line 23 col  1.
     03  pic 9(6) using PL-Approp-AC6      line 23 col 30 foreground-color 3.
     03  value "]"                         line 23 col 36.
*>
 procedure division using IRS-System-Params
                          WS-System-Record
                          File-Defs.
*>*****************************************
*>
 init01  section.
*>--------------
*>
*> first get Date & User Information
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
     move     1 to File-Key-No.               *> 1 = Primary
*>
 main-loop.
*>----------
*>
     move     zero to menu-reply.
     display  menu-screen-1.
     accept   menu-screen-1.
     if       menu-reply = 1 or Cob-Crt-Status = Cob-Scr-F1
              perform Set-Up
     else
      if      menu-reply = 2 or Cob-Crt-Status = Cob-Scr-F2
              perform Amend
      else
       if     menu-reply = 3 or Cob-Crt-Status = Cob-Scr-F3
              perform Show
       else
        if    menu-reply = 4 or Cob-Crt-Status = Cob-Scr-F4
              perform Listing
        else
         if   menu-reply = 5 or Cob-Crt-Status = Cob-Scr-F5
              perform Set-Up-Finished
         else
         if   menu-reply = 9 or Cob-Crt-Status = Cob-Scr-Esc
              go to main01-exit.
     go       to main-loop.
*>
 main01-exit.
     goback.
*>
 Set-Up section.
*>-------------
*>
 Set-Up-Main.
     display  Setup-Screen-1.
     accept   Setup-Screen-2Q.
*>
 main-loop.
*>---------
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to main-exit.
     if       function upper-case (ws-reply) = "N"
              perform  file-init.
     if       function upper-case (ws-reply) not = "Y" and not = "N"
              go to Set-Up-Main.
*>
     display  Setup-Screen-1.
     display  Setup-Amend-Screen-3.
     perform  varying w from 1 by 1 until w > 16
              add w 16 giving y
              move 1 to cole
              add 6 w giving lin
              display w at curs with foreground-color 2
              move 41 to cole
              display y at curs with foreground-color 2
     end-perform
     perform  Input-Headings.
*>
 get-input.
*>----------
*>
     display  w at curs with foreground-color 2.
     add      4  curs giving curs2.
     move     def-acs (w) to ws-acs.
     accept   ws-acs at curs2 with update foreground-color cob-color-cyan.
     move     ws-acs to def-acs (w).
     if       def-acs (w)  =  zero
              move 41  to  cole
              move 30  to  w
              move 20  to  lin
              go to get-input.
     move     def-acs (w)  to  nl-owning.
     move     zero  to  nl-sub-nominal.
*>
*> get code description.
*>
 *>    move     4  to  file-function.
     perform  acasirsub1-Read-Indexed.
     if       we-error  =  2
              go to get-input.
     add      10  curs giving curs2.
     display  nl-name at curs2  with foreground-color cob-color-cyan.
     add      22 to col2.
     display  "[  ]"  at curs2 with foreground-color 2.
     add      1 to col2.
     move     def-codes (w) to ws-codes.
*>
     if       w < 30
              accept ws-codes  at curs2 with update foreground-color 3
     else
      if      w = 30
              move "OB" to ws-codes
      else
       if     w = 31                        *> Purchases
              move "VI" to ws-codes
       else                                 *> must be 32 (sales).
              move "VO" to ws-codes.
*>
     move     function upper-case (ws-codes) to def-codes (w).
     add      32    curs giving curs2.
     add      1 to col2.
     display  ws-codes at curs2  with foreground-color cob-color-cyan.
     add      2 to col2.
*>
 vat-check.
*>----------
*>
     add      38    curs giving curs2.
     move     def-vat (w) to ws-vat2.
     if       w < 30
              accept ws-vat2 at curs2 with foreground-color 3
     else
              move "N" to ws-vat2
              display ws-vat2 at curs2 with foreground-color 3
     end-if
     move     function upper-case (ws-vat2) to ws-vat.
     move     ws-vat to def-vat (w).
     if       ws-vat not = "I" and not = "N" and not = "O"
              go to vat-check.
*>
     add      1  to  w.
     if       w  >  32
              go to end-input.
     if       w  =  17
              move 41  to  cole
              move 6   to  lin.
     add      1  to  lin.
     go       to get-input.
*>
 End-Input.
*>----------
*>
*> now close A/c file & write out defaults.
*>
 *>                                   move     2  to  file-function.
     perform  acasirsub1-Close.
 *>                                   move     5  to  file-function.
     perform  acasirsub3-Write.
*>
*>  Check that default a/cs 30, 31 & 32 have been set up.
*>
     if       def-acs (30) = zero
          or  def-acs (31) = zero
          or  def-acs (32) = zero
              display IR025 at 2301 with foreground-color 2 erase eol
              display SY008 at 2401 with foreground-color 2 erase eol
              accept  ws-reply at 2435
     end-if.
*>
     perform  amend.           *> Force Amendment mode.
*>
 main-exit.
     exit.
*>
 amend section.
*>-------------
*>
     display  Amend-Screen-1.
     display  Setup-Amend-Screen-3.
     perform  varying w from 1 by 1 until w > 16
              add w 16 giving y
              move 1 to cole
              add 6 w giving lin
              display w at curs with foreground-color 2
              move 41 to cole
              display y at curs with foreground-color 2
     end-perform
     perform  Input-Headings.
*>
 get-input.
*>----------
     move     zero to y.
     display  IR020 at 2420 with foreground-color 2 with erase eol.
     accept   y     at 2451 with update foreground-color cob-color-yellow.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to End-Input.
     if       y = zero
              go to end-input.
     if       y < 1 or > 32
              go to get-input.
     move     y to w.
     if       y > 16
              subtract 16 from y
              move 41 to cole
     else
              move 1 to cole
     end-if
     move     zero to lin.
     add      y 6 to lin.
     display  w at curs       with foreground-color 2.
     add      4 curs giving curs2.
     move     def-acs (w) to ws-acs.
     accept   ws-acs at curs2 with update foreground-color cob-color-cyan.
     move     ws-acs to def-acs (w).
     if       ws-acs = zero
              go to end-input.
     move     ws-acs to nl-owning.
     move     zero to nl-sub-nominal.
*>
*> get code description.
*>
 *>    move     4 to file-function.
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2
              go to get-input.
     add      10 curs giving curs2.
     display  nl-name at curs2 with foreground-color cob-color-cyan.
     add      22 to col2.
     display  "[  ]"  at curs2 with foreground-color 2.
     add      1 to col2.
     move     def-codes (w) to ws-codes.
     accept   ws-codes2 at curs2   with update foreground-color cob-color-cyan.
     move     function upper-case (ws-codes2) to ws-codes.
     move     ws-codes to def-codes (w).
     add      32 curs giving curs2.
     display  "[" at curs2 with foreground-color 2.
     add      1 to col2.
     display  ws-codes at curs2 with foreground-color cob-color-cyan.
     add      2 to col2.         *> this looks wrong should only be 1
     display  "]" at curs2 with foreground-color 2.
*>
 vat-check.
*>----------
*>
     add      38 curs giving curs2.
     move     def-vat (w) to ws-vat2.
     accept   ws-vat2 at curs2 with update foreground-color cob-color-cyan.
     move     function upper-case (ws-vat2) to ws-vat.
     move     ws-vat to def-vat (w).
     if       ws-vat not = "I"
                 and not = "N"
                 and not = "O"
              go to vat-check.
     go       to get-input.
*>
 end-input.
*>--------
*>
*>  Close A/c file & write out defaults.
*>
 *>    move     2 to file-function.
     perform  acasirsub1-Close.
 *>    move     5 to file-function.
     perform  acasirsub3-Write.
*>
 main-exit.
     exit.
*>
 Set-Up-Finished section.
*>----------------------
*>
*>   Final Accts not used on Open Source version but we can set then up
*>    as now added in to irs060 as a simplistic fix up.
*> Now get record, if 1st time get an initialised record so no errors.
*>
 *>    move     3  to  file-function.             *> open & read
     perform  acasirsub5-Read-Next.
*>
     if       we-error not = zero
              display IR915      at 2301 with foreground-color 4 erase eol
              display we-error   at 2350 with foreground-color 4 highlight
              display SY008      at 2401 with foreground-color 2 erase eol
              accept  menu-reply at 2432
              go to Set-Up-Finished-Exit
     end-if
 *>    move     1  to  file-function access-type.      *> open input Nominal
     perform  acasirsub1-Open-Input.
*>
 Setup-Fin-Retry.
     if       PL-App-Created not = "1"
              move zeros to PL-App-Created PL-Approp-AC
     end-if
     accept   Finished-Account-Setup-Screen-1.
     if       PL-Approp-AC not = zero
              move "1" to PL-App-Created
              move  PL-Approp-AC to nl-owning
              move  zero to nl-sub-nominal
 *>             move  4 to file-function                      *> Read indexed
              perform  acasirsub1-Read-Indexed
              if    we-error = 2
                    display IR021  at 2401 with foreground-color 4
                    display IR022  at 2437 with foreground-color 2
                    accept ws-reply at 2467
                    go to setup-fin-retry
              end-if
     end-if
*>
*> open, write out & close file
*>
 *>    move     5 to file-function.
     perform  acasirsub5-Write.    *> write and close Final
 *>    move     2 to file-function.                         *> close Nominal
     perform  acasirsub1-Close.
*>
 Set-Up-Finished-Exit.
     exit     section.
*>
 Show section.
*>------------
*>
     display  Display-Screen-1.
     display  Setup-Amend-Screen-3.
     perform  Input-Headings.
     display  " "      at 2301 with erase eol.
     display  IR023    at 2401 with foreground-color cob-color-white.
     move     space to ws-reply.
     accept   ws-reply at 2445.
*>
*> now close A/Cs File
*>
 *>    move     2 to file-function.
     perform  acasirsub1-Close.
*>
 main-exit.
     exit.
*>
 listing section.
*>---------------
*>
*>   Defaults
*>
     display  space at 0101 with erase eos.
     move     run-date to  p-date.
     move     client   to  p-client
                           p-Client-2.
     move     suser    to  p-user.
     accept   hdtime from time.
     if       hdtime not = "00000000"
              move hd-hh to hd2-hh
              move hd-mm to hd2-mm
              move HD2-Time  to P-Time.
*>
*> Open printer & Accounts files
*>
     open     output  print-file.
 *>    move     1  to  file-function  access-type.
     perform  acasirsub1-Open-Input.
*>
*>  Print Heads
*>
     write    print-record  from  line-1 after 1.
     write    print-record  from  line-3 after 2.
     write    print-record  from  line-4 after 2.
     move     spaces  to  print-record.
     write    print-record after 2.
*>
*>  get record
*>
 *>    move     3  to  file-function.
     perform  acasirsub3-Read-Next.
*>
*> Now print them
*>
     perform  varying w from 1 by 1 until w > 32
              move  w  to  p-num
              move  def-acs (w)  to  p-ac
              move  def-acs (w)  to  nl-owning
              move  zero  to  nl-sub-nominal
              if    def-acs (w)  =  zero
                    move spaces to  p-desc
                                    p-vat
                                    p-code
              else
 *>                   move 4  to  file-function   *>  get code description
                    perform acasirsub1-Read-Indexed
                    move nl-name to p-desc
                    move def-codes (w) to p-code
                    move def-vat (w)   to p-vat
              end-if
              write    print-record from line-5 after 1
     end-perform
*>
*> Done so close files and spool report
*>
 *>    move     2  to  file-function.        *>  close a/cs file
     perform  acasirsub1-Close.
*>
*>  Now for Finished A/Cs
*>
 *>    move     3  to  file-function.             *> open & read
     perform  acasirsub5-Read-Next.
*>
     if       ar1-fields = spaces
              go to Print-Fini.
*>
     write    print-record  from  line-1 after page.
     write    print-record  from  line-6 after 2.
     move     spaces  to  print-record.
     if       PL-Approp-AC not = zeros
              string   "  P & L Appropriation Account ["
                       PL-Approp-AC
                       "]"  into Print-Record
              end-string
              write    print-record after 2
     end-if
     write    print-record  from  line-7 after 2.
     write    print-record  from  line-8 after 1.
     move     spaces  to  print-record.
     write    print-record after 1.
*>
*>  Now spit out the Finished a/c data
*>
     move     14 to B.
     perform  varying A from 1 by 1 until A > 13
              move ar1 (A) to PAR-1 (1)             *> Desc
              move ar1 (B) to PAR-1 (2)
              move ar2 (A) to PAR-2 (1)             *> Sign
              move ar2 (B) to PAR-2 (2)
              move WS-Alpha-CD1 (A) to POS-1(1)     *> A/c Type
              move WS-Alpha-CD1 (B) to POS-1(2)     *> As A - Z
              write  Print-Record from Line-9 after 1
              add 1 to B
     end-perform.
*>
 Print-Fini.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 list-exit.
     exit.
*>
 file-init section.
*>-----------------
*>
*> Remove password controls for O/S versions.
*>
*>     display  "Enter pass-word - [    ]" at 0551 with foreground-color 2.
*>     accept   ws-pass at 0570 with update secure.
*>     if       ws-pass not = pass-word
*>              move "Z" to ws-reply
*>              go to main-exit.
     initialize WS-IRS-Default-Record.
 *>    move     5 to file-function.
     perform  acasirsub3-Write.
*>
 main-exit.
     exit.
*>
 Input-Headings section.
*>---------------------
*>
*> Open & read the defaults
*>
 *>    move     3  to  file-function.
     perform  acasirsub3-Read-Next.
*>
*>  Test that dflt data exists [11/12/16] - bug finding ?
*>
     if       FS-Reply not = zero
              display IR913 at 2301
              display FS-Reply at 2349
              display IR022    at 2401
              accept  ws-reply at 2430
              go      to main01-exit in init01
     end-if.
     if       WS-IRS-Default-Record = spaces
              display IR913 at 2301
              display FS-Reply at 2350         *> 1 poss. more to show this is in use.
              display IR022    at 2401
              accept  ws-reply at 2430
              go      to main01-exit in init01
     end-if.
*>
*> Open N/L file
*>
 *>    move     1  to  file-function   access-type.
     perform  acasirsub1-Open-Input.
*>
     if       we-error not = zero
              display IR024 at 2301
              display IR022 at 2401       with foreground-color cob-color-white
              move space to ws-reply
              accept ws-reply at 2430
              go to main01-exit in init01.
*>
*> Now input existing defaults
*>
     move     1 to w  cole.   *> curs
     move     7 to lin.
     move     1 to File-Key-No.
*>
 display-existing.
*>-----------------
*>
     display  w at curs with foreground-color cob-color-green.
     add      4  curs giving curs2.
     move     def-acs (w) to ws-acs.
     display  ws-acs at curs2      with foreground-color cob-color-cyan.
     move     ws-acs to nl-owning.
     move     zero  to  nl-sub-nominal.
     if       ws-acs not = zero
 *>             move 4 to file-function
              perform acasirsub1-Read-Indexed
              add  10 curs giving curs2
              display nl-name (1:22) at curs2 with foreground-color cob-color-cyan
     end-if
*>
*> Get code description
*>
     add      33  curs giving curs2.
     move     def-codes (w) to ws-codes.
     display  ws-codes  at curs2     with foreground-color cob-color-cyan.
     add      5 to col2.
     move     def-vat (w) to ws-vat.
     display  ws-vat  at curs2       with foreground-color cob-color-cyan.
     add      1 to col2.
     display  "]" at curs2           with foreground-color cob-color-green.
     add      1  to  w.
     if       w  >  32
              go to display-existing-end.
     if       w  =  17
              move 41  to  cole
              move 6   to  lin.
     add      1  to  lin.
     go       to display-existing.
*>
 display-existing-end.
*>---------------------
*>
     move     1  to  w  cole.
     move     7  to  lin.
*>
 main-exit.
     exit.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
