       >>source free
*>*****************************************************************
*>                                                                *
*> A C C O U N T   F I L E    U T I L I T I E S    P R O G R A M  *
*>                                                                *
*>*****************************************************************
*>
 identification division.
 program-id.            irs010.
*> Author.              Cobol Conversion By Vincent B Coen, FIDPM FBCS 13/10/1982
*>                      for Applewood Computers.
*>**
 Date-Compiled.         Today.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Accounts File Utilities Program
*>                      Setup, Amend, Display, Print, Inport and Export.
*>**
*> Function Keys Used.
*>                      F1 through F6 - Menu only.
*>**
*> Calls.
*>                      acasirsub1  ->
*>                       irsnominalMT
*>**
*> Error messages used.
*>  System Wide
*>                      SM901 }
*>                      SM903 } Produced by DAL.
*>                      SM904 }
*>                      SY008 Note message & Hit return
*>                      IR901 }
*>                      IR902 } From FH.
*>                      IR911 } Error on systemMT processing, FS-Reply = nn
*>                      IR912 } Error on irsnominalMT processing, FS-Reply = nn
*>                      IR913 } Error on irsdfltMT processing, FS-Reply = nn
*>                      IR914 } Error on irspostingMT processing, FS-Reply = nn
*>                      IR915 } Error on irsfinalMT processing, FS-Reply = nn
*>                      IR916 } Error on slpostingMT processing, FS-Reply = nn
*>  Module Specific.
*>                      IR010 Record already exists re-enter!
*>                      IR011 Key is -
*>                      IR012 Enter <N> for Next screen or <X> to Quit.......[ ]
*>                      IR013 End of display. Hit return for Menu
*>**
*> Changes.
*>
*> 16/09/83 vbc - fix error on amend not clear input type.
*> 28/05/84 vbc - hilite display heads.
*> 14/04/85 vbc - change print to 79 chars.
*> 26/09/89 vbc - 2.53
*>                mods for cobol/2 & change printline to 80 chars.
*> 28/09/89 vbc - Force lower case to upper.
*> 18/01/09 vbc - Migration to Open/Gnu Cobol as version 3
*> 20/02/09 vbc - Added support for environment LINES and COLUMNS as needed.
*> 21/09/10 vbc - Added print spool.
*>                .05 fix for portrait printing
*> 21/11/11 vbc - .06 Added firsttime-flag proc to clear down prebuild CoA
*>                    prior to 1st usage and pre postings.
*> 29/04/13 vbc - .07 Added facility to export and import CoA as a template
*>                    in .txt format and export only as a cvf (common delimiter
*>                    form eg, chars,chars,chars,chars. Normal is text (.txt).
*> 03/05/13 vbc - .08 Clear bug on importing CoA from text file when processing
*>                    sub nominals
*> 04/05/13 vbc - .09 Tidy up displays for export/import of CoA
*>                .10 Change ws-amend-lines to ws-accept-lines in amend.
*> 05/05/13 vbc - .11 Changed opening sequence for CoA import to that for setup.
*> 22/11/16 vbc - 3.02
*>                .12 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*> 20/12/16 vbc -     All irs progs call copybook Proc-ZZ100-ACAS-IRS-Calls.
*> 17/09/17 vbc - .13 Adjust screen display at Setup-Amend-Screen-3 not to
*>                    have the occurs clause in as does not work in GC.
*>                    Well overdue cosmetic bug fix.
*> 29/01/18 vbc - .14 Changed copies to use copybooks where poss.
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 10/02/18 vbc - .15 Renamed IR011-16 to IR911-16 and others.
*> 11/02/18 vbc - .16 Change calls to acasirsubn to use verbs eg acasirsub1-Close.
*> 23/04/18 vbc - .17 Update menu for details of Function keys for opts 5 & 6.
*> 02/05/18 vbc - .18 Changed NL export to exclude Subs but it should be done by FH
*>                    so counting these and displayed at end. Should be zero !
*>                    Removed code that forced Sub if sub-nominal = zero as allowed
*>                    recs are Owner. Subs are only a pointer.
*> 02/05/18 vbc - .19 Added Time to report (in Listing) & do this for most of the
*>                    reports in IRS as it is hard to work out the latest reports.
*>                    Change title to Chart of Accounts instead of accounts
*>                    directory for display and printing.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
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
     select  print-file     assign       "prt-1"
                            organization line sequential.
*>
*>  This is a Cobol or text file that is imported.
*>
     select  Saved-CoA      assign       Archive-Name
                            organization line sequential
                            status       FS-Reply.
*>
 data division.
 file section.
*>
 fd  print-file.
*>
 01  print-record        pic x(80).
*>
 fd  Saved-CoA.
 01  Export-CoA-Text.
     03  ECoA-Data-Type  pic x.
     03  ECoA-Owning     pic 9(5).
     03  ECoA-Sub        pic 9(5).
     03  ECoA-nl-Type    pic x.
         88 ECoA-nl-sub-ac               value "S".
         88 ECoA-nl-owner                value "O".
     03  ECoA-nl-Name    pic x(24).
     03  ECoA-nl-AC      pic x.
*>
 01  Saved-CoA-Comma.
     03  ECoA-Data-TypeB pic x.
     03  Saved-CoA-Data  pic x(43).
*>
 working-storage section.
 77  prog-name           pic x(16)  value "irs010 (3.3.00)".
 copy "irsprint-spool-command-p.cob".
 77  menu-reply          pic x      value space.
*>
 01  work-fields.
     03  ws-reply        pic x.
     03  ws-reply2       pic x.
     03  ws-Export-Format pic x     value "T".
     03  input-type      pic x.
         88  sub-input        value "y" "Y".
     03  input-type2     pic x.
         88  sub-input2       value "y" "Y".
     03  counter         pic 9(4).
     03  ws-pass         pic x(4).
     03  nl-ac2          pic a.
     03  save-owning     pic 9(5).
     03  Save-Subs-Cnt   pic 9(5)   value zero.
     03  count2          pic 9.
     03  prt-file        pic x(11).
     03  Archive-Name    PIC X(32)     VALUE "coa-archived.txt".
     03  line-cnt        pic 99   comp value 99.
     03  ws-spaces                     value  spaces.
         05  ws-spaces78 pic x(78).
         05  filler      pic xx.
     03  p-owning        pic zzzzz blank when zero.
     03  p-sub           pic zzzzz blank when zero.
*>     03  ws-env-columns  pic 999       value zero.
     03  ws-env-lines    pic 999       value zero.
     03  ws-lines        binary-char unsigned value zero.
*>     03  ws-columns      binary-char unsigned value zero.
*>     03  ws-show-lines   binary-char unsigned value zero.
*>     03  ws-amend-lines  binary-char unsigned value zero.
     03  ws-setup-lines  binary-char unsigned value zero.
     03  ws-accept-lines binary-char unsigned value zero.
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
 01  File-Info                          value zero.       *> Layout as per GNU v2 manual
     05 File-Size-Bytes  pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp.
     05 Mod-MO           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp.
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp. *> Always 00
*>
 copy "wsfnctn.cob".
 copy "irswsnl.cob" replacing NL-Record by WS-IRSNL-Record.
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
     03  WS-IRS-Default-Record pic x.
     03  Posting-Record        pic x.
     03  Final-Record          pic x.
     03  WS-IRS-Posting-Record pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
*>  for date conversion from ACAS
*>
 copy "wsmaps03.cob".
     03  U-Date8           pic x(8).
*>
 01  print-lines.
     03  line-1.
         05  p-user        pic x(24).
         05  filler        pic x(4)    value spaces.
         05  l1-a          pic x(26)   value "Incomplete Records System".
         05  filler        pic x(12)   value spaces.
         05  p-date        pic x(8).
         05  P-Time        pic x(6)    value spaces.
     03  line-3.
         05  p-client      pic x(24).
         05  filler        pic x(7)    value spaces.
         05  L3-A          pic x(18)   value "Chart of Accounts".
         05  filler        pic x(22)   value spaces.
         05  l3-b          pic x(6)    value "Page -".
         05  p-page        pic zz9.
     03  line-4.
         05  filler        pic x(11)   value spaces.
         05  l4-a          pic x(56)   value
         "  Main A/C       Sub-Account     ------Description------".
         05  l4-b          pic x(12)   value "    A/C Type".
     03  line-6.
         05  filler        pic x(14)   value spaces.
         05  p6-owning     pic zzzz9   blank when zero.
         05  filler        pic x(12)   value spaces.
         05  p6-sub        pic zzzz9   blank when zero.
         05  filler        pic x(8)    value spaces.
         05  p-description pic x(24).
         05  filler        pic x(7)    value spaces.
         05  p-ac          pic x.
*>
 01  All-My-Constants      pic 9(4).
     copy "screenio.cpy".
*>
 01  Error-Messages.
*> System Wide
     03  SY008          pic x(32) value "SY008 Note message & Hit return ".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, FS-Reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, FS-Reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, FS-Reply = ".
     03  IR914          pic x(51) value "IR914 Error on irspostingMT processing, FS-Reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, FS-Reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, FS-Reply = ".
*> Module specific
     03  IR010          pic x(37) value "IR010 Record already exists re-enter!".
     03  IR011          pic x(9)  value "Key is - ".
     03  IR012          pic x(56) value
         "IR012 Enter <N> for Next screen or <X> to Quit.......[ ]".
     03  IR013          pic x(42) value "IR013 End of display. Hit return for Menu ".
*>
 linkage section.
*>---------------
*>
 copy "irswssystem.cob"
              replacing system-record  by IRS-System-Params. *> (01 level)
*>
 copy "wssystem.cob" in "../copybooks"    *> NEW for v3.02
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
 copy "wsnames.cob".  *> uses the full version
*>
 screen section.
*>--------------
 01  menu-screen-1                                      background-color cob-color-black
                                                        foreground-color cob-color-green.
     03  pic x(16) from prog-name          line 1 col  1    blank screen.
     03  value "Accounts File Utilities"   line 1 col 29 foreground-color cob-color-white
                                                         background-color cob-color-blue
                                                            reverse-video.
     03  pic x(8) from Run-Date            line 1 col 73.
     03  value "Client -"                  line 3 col  1.
     03  pic x(24) from Client             line 3 col 10 foreground-color cob-color-cyan.
     03  value "Start date -"              line 3 col 39.
     03  pic x(8) from Start-Date          line 3 col 52 foreground-color cob-color-cyan.
     03  value "End date -"                line 3 col 62.
     03  pic x(8) from End-Date            line 3 col 73 foreground-color cob-color-cyan.
     03  value "Select the required function by number    ["
                                           line 5 col  1.
     03  pic x using menu-reply  auto      line 5 col 44 foreground-color cob-color-yellow.
     03  value "]"                         line 5 col 45.
     03  value "(1)  Set-Up Chart of Accounts" line  8 col 6.
     03  value "(2)  Amend  Chart of Accounts" line 10 col 6.
     03  value "(3)  Display the Chart"    line 12 col 6.
     03  value "(4)  Print   the Chart"    line 14 col 6.
     03  value "(5)  Export  the Chart"    line 15 col 6.
     03  value "(6)  Import  the Chart"    line 16 col 6.
     03  value "(9)  Return to System Menu" line 18 col 6.
     03  value "F1 to F6 = options 1 to 6;  Return to Accept " &
             "data;   Escape to quit"      line 23 col 1 foreground-color cob-color-white
                                                               highlight.
*>
 01  Amend-Screen-1                                      background-color cob-color-black
                                                         foreground-color cob-color-green.
     03  pic x(16) from prog-name          line 1 col  1   blank screen.
     03  value "Chart of Accounts Amendments" line 1 col 28 foreground-color cob-color-white
                                                            background-color cob-color-blue
                                                                  reverse-video.
     03  pic x(8)  from run-date           line 1 col 73.
*>
 01  Setup-Screen-1                                      background-color cob-color-black
                                                         foreground-color cob-color-green.
     03  pic x(16) from prog-name          line 1 col  1          blank screen.
     03  value "Chart of Accounts Setup"   line 1 col 30 foreground-color cob-color-white
                                                         background-color cob-color-blue
                                                                  reverse-video.
     03  pic x(8) from run-date            line 1 col 73.
*>
 01  Setup-Screen-2Q.
     03  value "Client -"                  line  3 col  1.
     03  pic x(24) from client             line  3 col 10 foreground-color cob-color-cyan.
     03  value "Start date -"              line  3 col 39.
     03  pic x(8) from start-date          line  3 col 52 foreground-color cob-color-cyan.
     03  value "End date -"                line  3 col 62.
     03  pic x(8) from end-date            line  3 col 73 foreground-color cob-color-cyan.
     03  value "Add to Existing Chart (Y/N) ? - [" line 5 col 1.
     03  pic x to menu-reply  auto         line  5 col 34 foreground-color cob-color-yellow.
     03  value "]"                         line  5 col 35.
     03  value "N.B. (1) If first time setup for this client answer no (N)"
                                           line  7 col  1 background-color cob-color-red
                                                          foreground-color cob-color-white.
     03  value "(2) Answering no (N)"      line  8 col  6 background-color cob-color-red
                                                          foreground-color cob-color-white.
     03  value "destroys"                  line  8 col 27 foreground-color cob-color-white
                                                          background-color cob-color-red
                                                                reverse-video.
     03  value "the existing chart"        line  8 col 36 background-color cob-color-red
                                                          foreground-color cob-color-white.
     03  value "Escape to quit;    Return to Accept data"
                                           line 23 col  1  foreground-color cob-color-white
                                                                highlight.
*>
 01  Setup-Amend-Screen-3                                 background-color cob-color-black
                                                          foreground-color cob-color-green.
     03  value "Client -"                  line  3 col  1.
     03  pic x(24) from client             line  3 col 10 foreground-color cob-color-cyan.
     03  value "Start date -"              line  3 col 39.
     03  pic x(8) from start-date          line  3 col 52 foreground-color cob-color-cyan.
     03  value "End date -"                line  3 col 62.
     03  pic x(8) from end-date            line  3 col 73 foreground-color cob-color-cyan.
     03  value "Main A/C      Sub-Nominal       Sub-Account     " &
         "  Description          A/C Type" line  4 col  2 highlight.
     03  value " "  erase eol              line  5 col  1.
*>
*>  Remed out as does not work in GnuCobol and created by a
*>    perform  display in setup-display
*>
*>     03  occurs 16
*>         value "[     ]           [ ]             [     ]" &
*>         "   [                        ]   [ ]" line plus 1 col 2.
*>
 01  Display-Screen-1                                     background-color cob-color-black
                                                          foreground-color cob-color-green.
     03  pic x(24) from suser              line  1 col 1  blank screen.
     03  value "Incomplete Records System" line  1 col 28 foreground-color cob-color-white
                                                          background-color cob-color-blue
                                                                reverse-video.
     03  pic x(8) from run-date            line  1 col 73.
     03  value "Client -"                  line  3 col 1.
     03  pic x(24) from client             line  3 col 10 foreground-color cob-color-cyan.
     03  value "Chart of Accounts"         line  3 col 32.
     03  value "Page"                      line  3 col 73.
     03  pic zz9 from counter              line  3 col 78 foreground-color cob-color-cyan.
     03  value "  Main       Sub             Description         " &
               "     Type "                line  5 col 11 background-color cob-color-blue
                                                          foreground-color cob-color-white.
*>
 procedure division using IRS-System-Params
                          WS-System-Record
                          File-Defs.
*>*****************************************
*>
 inita  section.
*>
*>   first get Date & User Information.
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
 *>    accept   ws-env-columns from columns.
 *>    if       ws-env-columns < 80
 *>             move 80 to ws-env-columns ws-columns
 *>    else
  *>            move  ws-env-columns to ws-columns
 *>    end-if
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines   to ws-lines
     end-if.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
     accept   hdtime from time.
     if       hdtime not = "00000000"
              move hd-hh to hd2-hh
              move hd-mm to hd2-mm
              move HD2-Time  to P-Time.
*>
 main01-loop.
*>-----------
*>
*> First check if this is first time setting up a/cs
*>  if so does accounts exist in which case a/cs are from
*> inported from sample data and if so, offer to clear down
*>  all values before any thing else happens
*>
     if       First-Time-Flag = zero
              perform zz000-clear-NL
              if   menu-reply = "0"
                   move 1 to First-Time-Flag.
*>
     move     1 to File-Key-No.               *> 1 = Primary
*>
     move     "0" to menu-reply.
     display  Menu-Screen-1.
     accept   Menu-Screen-1.
*>
     if       menu-reply = 1  or Cob-Crt-Status = Cob-Scr-F1
              perform set-up
              go to main01-loop.
     if       menu-reply = 2  or Cob-Crt-Status = Cob-Scr-F2
              perform amend
              go to main01-loop.
     if       menu-reply = 3  or Cob-Crt-Status = Cob-Scr-F3
              perform show
              go to main01-loop.
     if       menu-reply = 4  or Cob-Crt-Status = Cob-Scr-F4
              perform listing
              go to main01-loop.
     if       menu-reply = 5  or Cob-Crt-Status = Cob-Scr-F5
              perform ea-Export-CoA
              go to main01-loop.
     if       menu-reply = 6  or Cob-Crt-Status = Cob-Scr-F6
              perform fa-Import-CoA
              go to main01-loop.
     if       menu-reply = 9  or Cob-Crt-Status = Cob-Scr-Esc
              go to main01-exit.
     go       to main01-loop.
*>
 main01-exit.
     exit     program.
*>
 set-up section.
*>--------------
*>
 main02.
*>-----
*>
     display  Setup-Screen-1.
     accept   Setup-Screen-2Q.
     subtract 1 from ws-lines giving ws-accept-lines.
*>
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to main02-exit.
     if       function upper-case (menu-reply) = "N"
              perform  file-init.
     if       function upper-case (menu-reply) = "Y" OR "N"
              move 2 to access-type
     else
              go to main02.
*>
*> Open the Nominal Ledger
*>
 *>    move     1  to  file-function.
     perform  acasirsub1-Open.
*>
     display  setup-screen-1.
     display  Setup-Amend-Screen-3.
     perform  setup-display.
     move     6  to  lin.
*>
*> screen refresh after using last data accept on screen might be screwed
*>   if so, perf setup-display
*>
 input02-loop.
*>-----------
     move     1 to cole.
     display  " [     ]           [ ]             [     ]   [      " &
              "                  ]   [ ]" at curs with
                                 foreground-color cob-color-green.
     if       sub-input
              go to input02-sub.
     move     zero  to  nl-owning nl-sub-nominal.
     move     3  to  cole.
     accept   nl-owning at curs with update foreground-color cob-color-yellow.
     if       nl-owning = zero
              go to main02-end.
     if       access-type = 3           *> file opened as output so key check bypassed
              go to jump02-1.
*>
*> check that key is unique
*>
 *>    move     4  to  file-function.    *> read indexed
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2             *> record not found
              display  ws-spaces78 at line ws-lines col 01
              go to jump02-1.
*>
*> Record already exists
*>
     move     47 to cole.
     display  nl-name at curs with foreground-color cob-color-yellow.
     move     curs to curs2.
     add      1 to lin2.
     move     1 to col2.
     display  IR010 at line ws-lines col 01 with blink reverse-video.
*> 2401
     go       to input02-loop.
*>
 jump02-1.
*>-------
*>
     move     21 to cole.
     accept   input-type2 at curs with update foreground-color cob-color-yellow.
     move     function upper-case (input-type2) to input-type.
     if       input-type not = "N" and not = "Y"
              go to jump02-1.
     move     47 to cole.
     move     spaces to nl-name.
     accept   nl-name at curs with update foreground-color cob-color-yellow.
*>
 jump02-1-1.
*>---------
     move     76 to cole.
     accept   nl-ac2 at curs with update foreground-color cob-color-yellow.
     move     function upper-case (nl-ac2) to nl-ac.
     if       nl-ac < "A" OR > "Z"
              go to jump02-1-1.
*>
*>  Output the record.
*>
     move     "O" to nl-type.
     move     1 to First-Time-Flag.
     go       to main02-output.
*>
 input02-sub.
*>----------
     move     zero to nl-sub-nominal.
     move     37 to cole.
     accept   nl-sub-nominal at curs with update foreground-color cob-color-yellow.
     if       nl-sub-nominal = zero
              move "N" to input-type
              subtract 1 from  lin
              go to main02-return.
*>
*> check that key is unique
*>
 *>    move     4 to file-function.
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2
              display ws-spaces78 at line ws-lines col 01
              go to jump02-2.
*>
*> Record already exists
*>
     display  nl-name at curs.
     display  IR010 at line ws-lines col 01 with blink reverse-video.
     display  IR011 at line ws-lines col 40 with blink reverse-video.
     display  nl-key at line ws-lines col 50 with foreground-color 3.
*> 2445
     go       to input02-sub.
*>
 jump02-2.
*>-------
     move     47 to cole.
     move     spaces to nl-name.
     accept   nl-name at curs with update foreground-color cob-color-yellow.
     move     "S" to nl-type.
*>
 main02-output.
*>------------
     move     zero  to  nl-dr           nl-cr
                        nl-dr-last (1)  nl-dr-last (2)
                        nl-dr-last (3)  nl-dr-last (4)
                        nl-cr-last (1)  nl-cr-last (2)
                        nl-cr-last (3)  nl-cr-last (4).
*>
 *>    move     5 to file-function.  *> write
     perform  acasirsub1-Write.
*>
 main02-return.
*>------------
*>
     add      1 to lin.
     move     1 to cole.
     display  ws-spaces  at curs.
     if       lin  <  ws-accept-lines
              go to input02-loop.
     move     6  to  lin.
*>
 return02-loop.
*>------------
     move     1 to cole.
     display  ws-spaces  at curs.
     add      1  to  lin.
     if       lin  <  ws-accept-lines
              go to return02-loop.
     move     6  to  lin.
     go       to input02-loop.
*>
 main02-end.
*>---------
*>
*> close nominal ledger
*>
  *>   move     2 to file-function.
     perform  acasirsub1-Close.
*>
 main02-exit.
     exit     section.
*>
 amend section.
*>-------------
*>
 main03.
*>
     display  Amend-screen-1.
     display  Setup-Amend-Screen-3.
     subtract 1 from ws-lines giving ws-accept-lines.
*>
 setup-display.
*>     subtract 3 from ws-lines giving ws-amend-lines.
     move     2 to cole
*>
*> display extra lines if above 24 line display (if lines = 24 this wont run)
*>
 *>    perform  varying lin from 22 by 1 until lin > ws-accept-lines
     perform  varying lin from 6 by 1 until lin > ws-accept-lines
              display "[     ]           [ ]             [     ]" &
                         "   [                        ]   [ ]" at curs
                                                with foreground-color cob-color-green
     end-perform.
*>
 main03-loop.
*>----------
*>
*> now open the nominal ledger
*>
 *>    move     2  to  access-type.
 *>    move     1  to  file-function.
     perform  acasirsub1-Open.
*>
 input03-headings.
*>---------------
*>
     move     6  to  lin.
*>
 input03-loop.
*>-----------
*>
     move     spaces to input-type.
     move     1 to cole.
     move     zero  to  nl-owning  nl-sub-nominal.
     move     3 to cole.
     accept   nl-owning  at curs with update foreground-color cob-color-yellow.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to main03-end.
     if       nl-owning = zero
              go to main03-end.
*>
*> check key.
*>
 *>    move     4  to  file-function.
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2
              go to input03-loop.
*>
*> if here record does exist
*>
     move     47 to cole.
     display  nl-name at curs with foreground-color cob-color-yellow.
*>
 jump03-1.
*>-------
     move     21 to cole.
     accept   input-type2 at curs with update foreground-color cob-color-yellow.
     move     function upper-case (input-type2) to input-type.
     if       input-type = "D"
              perform delete-record
              go to input03-loop.
     if       input-type = "N"
              go to jump03-1-0.
     if       input-type = "Y"
              go to input03-sub
     else
              go to jump03-1.
*>
 jump03-1-0.
*>---------
     move     47 to cole.
     accept   nl-name at curs with update foreground-color cob-color-yellow.
*>
 jump03-1-1.
*>---------
     move     76 to cole.
     accept   nl-ac2  at curs with update foreground-color cob-color-yellow.
     move     function upper-case (nl-ac2) to nl-ac.
*>
     if       nl-ac < "A" or > "Z"
              go to jump03-1-1.
*>
*> now output the record.
*>
     move     "O"  to  nl-type  input-type.
     go       to main03-output.
*>
 input03-sub.
*>----------
     move     zero  to  nl-sub-nominal.
     move     37 to cole.
     accept   nl-sub-nominal at curs with update foreground-color cob-color-yellow.
     if       nl-sub-nominal = zero
              move "N"  to  input-type
              subtract 1  from  lin
              go to main03-return.
*>
*> check that key is unique
*>
 *>    move     4  to  file-function.
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2
              go to jump03-2.
*>
*> if here record already exists
*>
     move     47 to cole.
     display  nl-name at curs with foreground-color cob-color-yellow.
     move     "O"  to  input-type.
     move     "O"  to  nl-type.
     accept   nl-name at curs with update foreground-color cob-color-yellow.
*>
 jump03-1-s.
*>---------
     move     76 to cole.
     accept   nl-ac2 at curs with update foreground-color cob-color-yellow.
     move     function upper-case (nl-ac2) to nl-ac.
     if       nl-ac < "A" or > "Z"
              go to jump03-1-s.
     go       to  main03-output.
*>
 jump03-2.
*>-------
     move     47 to cole.
     accept   nl-name at curs with update foreground-color cob-color-yellow.
     move     "S" to nl-type input-type.
     move     zero to nl-dr           nl-cr
                      nl-dr-last (1)  nl-dr-last (2)
                      nl-dr-last (3)  nl-dr-last (4)
                      nl-cr-last (1)  nl-cr-last (2)
                      nl-cr-last (3)  nl-cr-last (4).
*>
 main03-output.
*>------------
*>
     if       input-type = "S"
 *>             move 5  to  file-function
              perform  acasirsub1-Write
     else
 *>             move 7  to  file-function.
              perform  acasirsub1-Rewrite.
*>
 main03-return.
*>------------
     move     1 to cole.
     add      1  to  lin.
*>    display  ws-spaces at curs.
     if       lin  <  ws-accept-lines   *> 23
              go to input03-loop.
     move     6  to  lin.
*>
     perform  main03.
     go       to input03-headings.
*>
 main03-end.
*>---------
*>
*> close nominal ledger
*>
 *>    move     2  to  file-function.
     perform  acasirsub1-Close.
*>
 main03-exit.
     exit     section.
*>
 show section.
*>------------
*>
     move     zero to counter.
     move     7 to lin.
     subtract 2 from ws-lines giving ws-accept-lines.
*>
*> now open nominal ledger
*>
 *>    move     1  to  file-function  access-type.
     perform  acasirsub1-Open-Input.
     perform  main04-display.
     if       we-error = 1 *> no file
              go to main04-end.
*>
 main04-loop.
*>----------
*>
*> read next record
*>
 *>    move     3  to  file-function.
     perform  acasirsub1-Read-Next.
     if       we-error = 3
              go to main04-end.
     move     nl-owning      to p-owning.
     move     nl-sub-nominal to p-sub.
     if       nl-sub-nominal  not equal zero
              move zero to p-owning.
     move     12 to cole.
     display  p-owning at curs with foreground-color cob-color-cyan.
     add      11 to cole.
     display  p-sub  at curs with foreground-color cob-color-cyan.
     add      13 to cole.
     display  nl-name at curs with foreground-color cob-color-cyan.
     add      30 to cole.
     display  nl-ac at curs with foreground-color cob-color-cyan.
     add      1  to  lin.
     if       lin  <  ws-accept-lines  *> 22
              go to main04-loop.
*>
*> end of screen routine
*>
     display  IR012 at line ws-lines col 18 with foreground-color cob-color-yellow.
     move     space to ws-reply2.
     accept   ws-reply2 at line ws-lines col 72 with auto foreground-color cob-color-yellow.
     move     function upper-case (ws-reply2) to ws-reply.
     if       ws-reply = "X"
              go to    main04-end2.
     display  " " at 0101 with erase eos.
     move     7 to  lin.
     perform  main04-display.
     go to    main04-loop.
*>
 main04-display.
*>--------------
*>
     add      1 to counter.
     display  Display-Screen-1.
*>
 main04-end.
*>---------
*>
     display  IR013 at line ws-lines col 18
                                 with erase eol foreground-color cob-color-yellow.
     move     space to ws-reply.
     accept   ws-reply at line ws-lines col 61 with foreground-color cob-color-yellow.
*>
 main04-end2.
*>-----------
*>
*> Close file
*>
 *>    move     2 to file-function.
     perform  acasirsub1-Close.
*>
 main04-exit.
     exit     section.
*>
 listing section.
*>---------------
*>
 *>    display  space.
     move     run-date to p-date.
     move     client   to p-client.
     move     suser    to p-user.
     move     suser    to p-user.
*>
*> Open nominal ledger
*>
     move     zero to counter.
 *>    move     1  to  file-function  access-type.
     perform  acasirsub1-Open-Input.
     open     output  print-file.
     move     85 to line-cnt.
*>
     perform  until we-error = 3           *> yep, its also checked lower
 *>             move  3  to  file-function   *> read next record
              perform acasirsub1-Read-Next
              if   we-error = 3
                   exit perform
              end-if
              if   line-cnt > 80
                   add 1  to  counter
                   move  counter  to  p-page
                   if    counter not = 1
                         write print-record from line-1 after page
                   else
                         write print-record  from  line-1 after 1
                   end-if
                   write print-record  from  line-3 after 2
                   write print-record  from  line-4 after 2
                   move  spaces  to  print-record
                   write print-record after 1
                   move  6 to line-cnt
              end-if
              move  nl-owning      to p6-owning
              move  nl-sub-nominal to p6-sub
              if    nl-sub-nominal not = zero
                    move zero to  p6-owning
              end-if
              move  nl-name to  p-description
              move  nl-ac   to  p-ac
              write print-record from line-6 after 1
              add 1 to line-cnt
     end-perform
*>
*> Close file
*>
 *>    move     2  to  file-function.
     perform  acasirsub1-Close.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 list-exit.
     exit     section.
*>
 file-init section.
*>-----------------
*>
 *>    display  "Enter Pass-word - [    ]" at 0551 with foreground-color 2.
 *>    accept   ws-pass at 0570 with secure.
 *>    if       ws-pass = pass-word
 *>             move 1  to  file-function         *> Open output
 *>             move 3  to  access-type
              perform acasirsub1-Open-Output
 *>             move  2 to file-function           *> Close file
              perform acasirsub1-Close
*>     else
*>              move  "Z"  to  ws-reply
*>     end-if
     move     2 to access-type.              *> open i-o
*>
 main05-exit.
     exit     section.
*>
 delete-record section.
*>---------------------
*>
*> check key.
*>
 *>    move     4  to  file-function.
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2
              go to main06-exit.
 *>    move     8 to file-function.
     perform  acasirsub1-Delete.
     move     nl-owning  to  save-owning.
 *>    move     9 to file-function.
 *>    move     6 to access-type.
     set      fn-less-than to true.
     perform  acasirsub1-Start.
*>
 loop06.
*>-----
*>
     if       nl-owning  not = save-owning
              go to main06-exit.
 *>    move     8  to  file-function.
     perform  acasirsub1-Delete.
     move     nl-owning to save-owning.
     if       nl-sub-nominal not = zero
              move nl-sub-nominal to nl-owning
              move zero  to  nl-sub-nominal
              perform acasirsub1-Delete
              move save-owning  to nl-owning.
 *>    move     2  to  file-function.
     perform  acasirsub1-Close.
 *>    move     1  to  file-function.
 *>    move     2  to  access-type.
     perform  acasirsub1-Open.
 *>    move     9  to  file-function.
 *>    move     6  to  access-type.
     move     zero  to  nl-sub-nominal.
     set      fn-less-than to true.
     perform  acasirsub1-Start.
     if       we-error = zero
              go to loop06.
*>
 main06-exit.
     exit     section.
*>
 ea-Export-CoA section.
*>--------------------
*>
 ea010-Warning-Notice.
     display  "This process will export a copy of the current CoA (Chart of Accounts)"
                                                                   at 0101 with foreground-color cob-color-yellow erase eos.
     display  "overwriting any copy of the file if it exists."     at 0221 with foreground-color cob-color-yellow.
     display  "Continue Y/N [ ]"                                   at 0401 with background-color cob-color-red
                                                                                foreground-color cob-color-white.
*>
     move     space to Menu-Reply.
     accept   menu-reply at 0415.
     if       menu-reply = "N" or = "n"
              move "1" to menu-reply
              exit section
     end-if
*>
     display  "File name to be created [12345678901234567890123456789012]"
                                                                          at 0601 with foreground-color cob-color-yellow.
     accept   Archive-Name at 0626 with update.
     if       Archive-Name = spaces or Cob-Crt-Status = Cob-Scr-Esc
              display "Quiting to menu" at 1001 with erase eol
              exit section.
*>
     display  "Warning: Comma delimited files cannot be imported by this program"
                                                         at 0701 with foreground-color cob-color-yellow.
     display  "Format: T(xt) or (C)omma delimited?  [T]" at 0801 with foreground-color cob-color-yellow.
     move     "T" to ws-Export-Format.
     accept   ws-Export-Format  at 0839 with update.
     move     function upper-case (ws-Export-Format) to ws-Export-Format.
     if       ws-Export-Format not = "T" and not = "C"    *> space to quit
              exit section.
*>
 ea020-Open-Output.
     open     Output Saved-CoA.
     if       FS-Reply not = zero
              display "Problem opening Export File, hit return to quit action" at 2301
              accept  ws-reply at 2360
              exit section
     end-if
*>
*> Open nominal ledger
*>
     move     zero to counter.
     perform  acasirsub1-Open-Input.
*>
     move     ws-Export-Format to ECoA-Data-Type.
     perform  until we-error = 3      *> initially on open, and checked lower down
              perform acasirsub1-Read-Next
              if   we-error = 3       *> eof
                   exit perform
              end-if
              if   NL-Sub-Nominal = zero                   *> This should NOT happen
                and NL-Pointer numeric
                   add 1 to Save-Subs-Cnt                  *> so test for it by counting
                   exit perform cycle
              end-if
              if   ws-Export-Format = "T"
                   move  nl-Owning      to ECoA-owning
                   move  nl-Sub-Nominal to ECoA-sub
                   move  nl-Name to  ECoA-nl-name
                   move  nl-ac   to  ECoA-nl-ac
                   move  nl-Type to  ECoA-nl-Type
                   write Export-CoA-Text
                   if  FS-Reply not = zero
                       display "Problem writing to Export File, hit return to quit action" at 2301
                       accept  ws-reply at 2360
                       exit perform     *> at least close files and get totals
                   end-if
                   add 1 to counter
              else   *> = "C", comma delimited
                   string  nl-owning      delimited by size
                           ","            delimited by size
                           nl-sub-nominal delimited by size
                           ","            delimited by size
                         quote            delimited by size
                         nl-name          delimited by size
                         quote            delimited by size
                         ","              delimited by size
                         nl-ac            delimited by size
                         ","              delimited by size
                         nl-type          delimited by size
                         " "              delimited by size into Saved-CoA-Data
                   end-string
                   write Saved-CoA-Comma
                   if  FS-Reply not = zero
                       display "Problem writing to Export File, hit return to quit action" at 2301
                       accept  ws-reply at 2360
                       exit perform     *> at least close files and get totals
                   end-if
                   add 1 to counter
              end-if
     end-perform
*>
*> Close file
*>
     display  "Total record count written out = "   at 2001.
     display  Counter                               at 2034.
     display  "Total records found as SUBS    = "   at 2101.
     display  Save-Subs-Cnt                         at 2134.
     display  "Note count & hit return to continue" at 2201.
     accept   ws-reply                              at 2237.
*>
 *>    move     2  to  file-function.
     perform  acasirsub1-Close.
     close    Saved-CoA.
*>
 ea999-exit.
     exit     section.
*>
 fa-Import-CoA section.
*>--------------------
 fa010-Warning-Notice.
*>
*>*****************************************************
*> Although allowed for, comma delimited files        *
*> cannot not be used for input, but just in case     *
*>  However cvs files has not been coded.             *
*>*****************************************************
*>
     display  "This process will import a CoA (Chart of Accounts) in TEXT format " at 0101 with foreground-color cob-color-yellow erase eos.
     display  "overwriting any existing IRS Chart of Accounts."    at 0201 with foreground-color cob-color-yellow.
     display  "This must only be done for a new set of accounts for a new client." at 0301 with foreground-color cob-color-yellow.
     display  "Otherwise, If you have not made a back up of it you should quit this process."
                                                                          at 0401 with foreground-color cob-color-yellow.
     display  "Warning: This is NON RECOVERABLE, so think about it"       at 0714 with foreground-color cob-color-red.
     display  "Before responding (Y)es ensure you have a back copy of the original file"
                                                                          at 0901 with foreground-color cob-color-yellow.
     display  "Otherwise respond (N)o and then exit the main menu to do so."
                                                                          at 1001 with foreground-color cob-color-yellow.
     display  "Continue Y/N [ ]"                                          at 1201 with background-color cob-color-red
                                                                                       foreground-color cob-color-white.
*>
     accept   menu-reply at 1215.
     if       menu-reply = "N" or = "n"
              move "1" to menu-reply
              exit section
     end-if
*>
     display  "File name to be Imported [12345678901234567890123456789012]" at 1501 with foreground-color cob-color-yellow.
     accept   Archive-Name at 1527 with foreground-color cob-color-yellow update.
     if       Archive-Name = spaces
           or Cob-Crt-Status = Cob-Scr-Esc
              display "Quiting to menu" at 1501 with erase eol
              exit section.
*>
 fa020-Open-Files.
     open     Input Saved-CoA.
     if       FS-Reply not = zero
              display "Problem opening Import File, hit return to quit action" at 2301
              accept  ws-reply at 2360
              exit section
     end-if
*>
*> Open the Nominal Ledger
*>
 *>    move     1  to  file-function         *> Open output
 *>    move     3  to  access-type
     perform  acasirsub1-Open-Output.
     if       we-error = 1
              display "Problem opening Accounts for output, hit return to quit action" at 2301
              accept  ws-reply at 2365
              exit section
     end-if
 *>    move     2 to file-function           *> Close file
     perform  acasirsub1-Close.
 *>    move     2 to access-type.              *> open i-o
 *>    move     1 to File-Function.
     perform  acasirsub1-Open.
     if       we-error not = zero
              display "Problem opening Accounts for output, hit return to quit action" at 2301
              accept  ws-reply at 2365
              exit section
     end-if
     move     zero to Counter.
*>
*>  Set all amounts to zero, cannot use initialize owing to presence of redefines
*>
     move     zero  to  nl-dr           nl-cr
                        nl-dr-last (1)  nl-dr-last (2)
                        nl-dr-last (3)  nl-dr-last (4)
                        nl-cr-last (1)  nl-cr-last (2)
                        nl-cr-last (3)  nl-cr-last (4).
*>
 fa030-Read-Input.
     read     Saved-CoA record at end
              go to fa040-End-Of-Input.
*>
*>  Output the record if record type = T (Text) and check them all in case user has manually modified them.
*>
     if       ECoA-Data-Type not = "T"
              display "Error: Can only import a Text file (.txt) as exported by this program"
                                                 at 2001 with blink highlight
              display "Hit return for menu" at 2101
              accept  ws-reply at 2122
              exit section
     end-if
     move     ECoA-Owning  to nl-owning.
     move     ECoA-Sub     to nl-sub-nominal.
     if       ECoA-Sub = zero                *> In case user has modified file
              move "O" to ECoA-nl-Type
     else
              move "S" to ECoA-nl-Type
     end-if
     move     ECoA-nl-Type to nl-type.
     move     ECoA-nl-Name to nl-name.
     move     ECoA-nl-AC   to nl-ac.
*>
 *>    move     5  to  file-function. *> writing
     perform  acasirsub1-Write.
     add      1  to Counter.
     go       to fa030-Read-Input.
*>
 fa040-End-Of-Input.
     display  "Total records created = " at 2001.
     display  Counter                    at 2026.
     display  "Note count & hit return to continue" at 2201.
     accept   ws-reply                   at 2237.
*>
     close    Saved-CoA.
 *>    move     2 to file-function.                   *> close NL file
     perform  acasirsub1-Close.
*>
 fa999-Exit.
     exit     section.
*>
zz000-clear-NL section.
*>--------------------
*>
zz010-main.
*>--------
     call     "CBL_CHECK_FILE_EXIST" using file-34 File-Info.   *> accounts file
     if       Return-Code not = zero  *> file not found so not using a CoA from elsewhere for the 1st time
              move "0" to Menu-Reply
              exit section
     end-if
*>
*>    We now have the CoA but do we have any postings?
*>
     call     "CBL_CHECK_FILE_EXIST" using file-36 File-Info.   *> postings file
     if       Return-Code = zero    *> file found so flag is wrong so skip this process
              move "0" to Menu-Reply
              exit section
     end-if
*>
*>   We now have a CoA with NO posting file so we can clear, lets ask!
*>
     display  "This appears to be the first time you are running IRS and there is a"
                                                                          at 0101 with foreground-color cob-color-yellow erase eos.
     display  "set of accounts (Nominal Ledger) present"                  at 0221 with foreground-color cob-color-yellow.
     display  "Can I clear down all amounts from these, so that you can start with a clean"
                                                                          at 0401 with foreground-color cob-color-yellow.
     display  "set of accounts"                                           at 0533 with foreground-color cob-color-yellow.
     display  "Warning: This is NON RECOVERABLE, so think about it"       at 0714 with foreground-color cob-color-red.
     display  "Before responding (Y)es ensure you have a back copy of the original file"
                                                                          at 0901 with foreground-color cob-color-yellow.
     display  "Otherwise respond (N)o and then exit the main menu to do so."
                                                                          at 1001 with foreground-color cob-color-yellow.
     display  "Continue Y/N [ ]"                                          at 1201 with background-color cob-color-red
                                                                                       foreground-color cob-color-white.
*>
     accept   menu-reply at 1215.
     if       menu-reply = "N" or = "n"
              move "1" to menu-reply
              exit section
     end-if
*>
     display  "Wait while I clear the Chart of Accounts down " at 1501 with foreground-color cob-color-yellow blink.
*>
 *>    move     1 to file-function.
 *>    move     2 to access-type.                        *> open for i-o
     perform  acasirsub1-Open.
     if       we-error not = zero                        *> we have an error so close and quit
 *>             move 2 to file-function                    *>  but as we tested for the file, this SHOULD NOT happen
              perform  acasirsub1-Close
              move "1" to menu-reply                     *>  ok, we are done
              exit section
     end-if.
*>
 zz020-Read-A-Record.
*>------------------
*>
 *>    move     3 to file-function.                        *> read next
     perform  acasirsub1-Read-Next.
     if       we-error = 3                               *> EOF
 *>             move 2 to file-function                    *> close
              perform  acasirsub1-Close
              move "0" to menu-reply                     *>  ok, we are done
              exit section
     end-if
*>                                                           clear all amounts
     move     zero  to  nl-dr           nl-cr
                        nl-dr-last (1)  nl-dr-last (2)
                        nl-dr-last (3)  nl-dr-last (4)
                        nl-cr-last (1)  nl-cr-last (2)
                        nl-cr-last (3)  nl-cr-last (4).
*>
 *>    move     7 to file-function.                      *> rewrite (sub gives no error check)
     perform  acasirsub1-Rewrite.
     go       to zz020-Read-A-Record.
*>
zz030-Exit.
     exit     section.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
