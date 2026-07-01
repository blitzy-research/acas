       >>source free
*>******************************************************
*>                                                     *
*>               Payroll  System  Menu                 *
*>            For the USA and possibly Canada          *
*>                                                     *
*>    This software is being written so do not use.    *
*>                                                     *
*>      Payroll does not use DAL for access to Mysql   *
*>          at this time - may be later subject        *
*>              to user requests.                      *
*>          Although some basic design made to the SQL *
*>         tables from another application so will     *
*>         mod.                                        *
*>                                                     *
*>     SOME Programs in the MENU ARE NOT YET WRITTEN   *
*>         So selecting them WILL, RESULT IN ERRORS.   *
*>         if I forgot to remark out the load          *
*>     These have a * before entry.                    *
*>                                                     *
*>     Next to none have had ANY testing other than    *
*>     the primary paramater set ups including         *
*>     Employee, History, Co History etc.              *
*>                                                     *
*>  Still to do are :                                  *
*>    menu opts B, D, E, F, G, O.                      *
*>      as of 09/04/26.                                *
*>******************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.          payroll.
*>**
*>    Author.              V.B.Coen FBCS, FIDM, FIDPM.
*>**
*>    Security.            Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                         Distributed under the GNU General Public License.
*>                         See the file COPYING for details.
*>**
*>    Remarks.             Payroll System Menu for the USA.
*>**
*>    Version.             See Prog-Name In Ws.
*>**
*>    Calls:                     Maps04
*>                               acas000  System Parameter file ->
*>                                 systemMT  (DAL).
*>                                 and all of the pynnn modules:
*>                                PY 000, PY010,  030, 900, 920, 930
*>           In dev               PY 020, print941, w2, 940?     ?
*>
*>                               None of the below is written yet.
*>        NOT YET                 py 040, 050, 060, 055, 070, 080,
*>                                   085, 090, 095,
*>                            100, 110, 120, (115), 130, 140, 160, 170, 180, 190, 200,
*>                            910,  940, 950,
*>                            170   all are may be's, but many may well exist in the Menu (payroll).
*>                          Coding has started for very minor in 020 & 030
*>
*>   So far completed         payroll,
*>                            py000
*>                            py010      }  All prgram names could change yet.
*>                            py020
*>                            py030
*>                            py900,
*>                            py920.
*>                            py930,
*>                            hisprint,  }
*>                            vacprint,  }
*>                            empprint,  }  All subject to name changes to pynnn later.
*>                            pyrgstr.   }
*>                            print940   }  subject to mode changes for form formats etc
*>                            printw2    }  subject to mode changes for form formats etc
*>                            print941   }  subject to mode changes for form formats etc - NOT COMPLETE
*>                            pyjourn    Coding
*>                            pyjourn1    not started and may be added into journ subject to size etc.
*>
*>**
*>    Error messages used.
*> System Wide
*>                         SY006
*>                         SY007
*>                         SY008
*>                         SY009.
*>                         SY010.
*>                         SY011.
*>                         SY013.
*> Module Specific.
*>**
*>    Changes.
*> 13/10/2025 vbc - 1.0.00 Starting writing system from SSG CBASIC code and manuals.
*>                         Payroll uses its own parameter file as there is some
*>                         difficulty in adding Payroll into the existing parameter
*>                         file other than creating a new record (#6).
*>                         Version to be updated to ACAS current layout
*>                         on completing system testing.
*>                         IN OTHER WORDS NOT YET CAST IN STONE etc.
*>                         In fact no coding is as all subject to testing !
*>
*> 24/11/2025 vbc -    .01 Code testing if pyparam file not exist to call via
*>                         option 25 - py900.
*> 27/11/2025 vbc -    .02 Screen size now checked for Minimum of 28 lines.
*>                         All other programs wil do the same. Msg SY010 chgd.
*> 09/12/2025 vbc -        Increased minimum screen depth = 28.
*> 02/02/2026 vbc -        Added empprint into menu select etc.
*> 06/03/2026 vbc -        Added vacprint, hisprint, pyrgstr, py930
*> 24/03/2026 vbc -        Some programs Options B - G etc could require screen
*>                         length to be longer than 28 lines including other data
*>                         capture / entry programs if D/E etc increases beyond 5
*>                         such as support for MCare etc and yes there are others.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> These files and programs are part of the Applewood Computers Accounting
*> System and is Copyright (c) Vincent B Coen. 2025-2026 and later.
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
*>===============================
*>
 copy  "envdiv.cob".
 SPECIAL-NAMES.
       CRT STATUS IS COB-CRT-STATUS.
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
 input-output            section.
*>
 file-control.
 copy "selpyparam1.cob".
*>
 data  division.
*>
 file section.
  copy "fdpyparam1.cob".
*>
 working-storage section.
*>----------------------
 77  Prog-Name           pic x(16)    value "Payroll (1.0.02)". *> When tested make it v3.3.00
 77  Batch-Text          pic x(28)    value spaces.
 77  Script-Name         pic x(20)    value spaces.
 77  Run-Backup          pic x(512)   value spaces.  *> size changed
 77  Full-Backup-Script  pic x(512)   value spaces.
 77  OS-Delimiter        pic x        value "/".     *> Preset for *nix
 77  ACAS_BIN            pic x(512)   value spaces.  *> added
 77  ACAS_LEDGERS        pic x(500)   value spaces.
 77  Arg-Number          pic 9        value zero.
*>========================================================
*>  In case file layout upgrade is needed.
*>   Using a file layout update program.
*>
 copy "sys-params-versioning.cob".
*>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*> holds program parameter values from command line
 01  Arg-Vals                         value spaces.
     03  Arg-Value       pic x(525)      occurs 2.
 01  Arg-Test            pic x(525)   value spaces.
 01  Saved-CD-Args       pic x(13).
*>
 01  Backup-Sw           pic 9        value zero.
     88  Backup-Script-Found          value 1.
 01  Linux-Backup-Script-Name
                         pic x(20)    value "pyacasbkup.sh".
 01  WindoWS-Backup-Script-Name
                         pic x(20)    value "pyacasbkup.bat".  *> Not written
 01  OS2-Backup-Script-Name
                         pic x(20)    value "pyacasbkup.cmd".  *> Not written
*>
 01  File-Info                        value zero.       *> Layout as per GNU v3 manual
     05 File-Size-Bytes  pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp.    *> Mod date.
     05 Mod-MO           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp.    *> Mod time
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp. *> Always 00
*>
 01  WS-Data.
     03  Menu-Reply      pic x        value "A".
     03  Op-Display      pic x(7).
*>
     03  Letters-Upper   pic x(26)    value "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
     03  Letters.
         05  A-Entry     pic x          occurs 26 indexed by q.
*>
     03  WS-Reply        pic x.
     03  PY-PR1-Status-X.
         05  PY-PR1-Status pic 99     value zero.
     03  A               pic 99   comp.
     03  B               pic 99.
     03  C               pic 99.
     03  Z               binary-short value zero.
     03  wsMaps-Ser.
         05  wsMaps-Ser-xx pic xx.
         05  wsMaps-Ser-nn pic 9(4).
*>
     03  WS-Env-Columns  pic 999      value zero.
     03  WS-Env-Lines    pic 999      value zero.
*>
 copy "wsmaps03.cob".    *> for maps04
 copy "wscall.cob".
 copy "wstime.cob".
 copy "wsfnctn.cob".
 copy "wssystem.cob".
*> copy "wssys4.cob"   replacing System-Record-4 by WS-System-Record-4.  *> used by Load00/0
*> copy "wsdflt.cob".
*> copy "wsfinal.cob".
 copy "wsnames.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
*>     03  System-Record          pic x.
     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
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
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging via F.H.
*>
 01  WS-Test-Date            pic x(10).
 01  WS-Date-formats.
     03  WS-Swap             pic xx.
     03  WS-Conv-Date        pic x(10).
     03  WS-Date             pic x(10).
     03  WS-UK redefines WS-Date.
         05  WS-Days         pic xx.
         05  filler          pic x.
         05  WS-Month        pic xx.
         05  filler          pic x.
         05  WS-Year         pic x(4).
     03  WS-USA redefines WS-Date.
         05  WS-usa-Month    pic xx.
         05  filler          pic x.
         05  WS-usa-Days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  WS-Intl redefines WS-Date.
         05  WS-intl-Year    pic x(4).
         05  filler          pic x.
         05  WS-intl-Month   pic xx.
         05  filler          pic x.
         05  WS-intl-Days    pic xx.
*>
 01  Error-Code          pic 999.  *> Not  Used yet.
*>
 01  COB-CRT-Status      pic 9(4)         value zero.
     copy "screenio.cpy".
*>
 01  Error-Messages.
*> System Wide
     03  SY006           pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007           pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008           pic x(31) value "SY008 Note message & Hit return".
     03  SY009           pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
     03  SY011           pic x(47) value "SY011 Error on systemMT processing, FS-Reply = ".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*>
*> Module specific
*>
 01  To-Day              pic x(10).
*>
 procedure division.
*>=================
*>
 Payroll-Main.
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
*>
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
     perform  zz020-Get-Program-Args.
*>
 Open-System.                *> First get system param cobol file
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.
     if       FS-Reply not = zero
 *>             perform System-Close       called again in aa010
              move     "sys002" to WS-Called    *> create param file by requested info from user
              call     WS-Called using WS-Calling-Data
                                       File-Defs
              perform  System-Open        *>  ditto
     end-if.
*>
 aa010-Get-System-Recs.
     move     zeros to File-System-Used         *> again in case RDB setup
                       File-Duplicates-In-Use.  *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
 *>    move     5 to File-Key-No.                 *> Do when pre-testing complete
 *>    perform  System-Read-Indexed.              *> Read Cobol file payroll params if included
 *>    move     System-Record to PY-Param1-Record.
*>
     move     1 to File-Key-No.
     perform  System-Read-Indexed.             *> Read Cobol file params
     if       FS-Reply not = zero              *> should NOT happen as done in
              perform System-Close             *> open-system
              move    "sys002" to WS-Called    *> create param file by requested info from user
              call     WS-Called using WS-Calling-Data
                                       File-Defs
              perform  System-Open
              go to aa010-Get-System-Recs
     end-if.
*>
     perform  System-Close.
*>
*>   Back to work as we have the RDB rec if in use otherwise the Cobol one
*>    regardless the system file/table is now closed with recs saved in WS.
*>
     move     Run-Date to u-bin.          *> Set up by py000
     call     "maps04" using maps03-ws.
     move     U-Date to To-Day.
     perform  zz060-Convert-Date.  *> O/P = WS-Date
*>
 *>    if       not P-Y
 *>             set P-Y to true.
*>
     if       op-system = zero
              move "O/S" to Op-Display.
     if       linux   move "Linux"   To Op-Display
     else if  Windows move "Windows" To Op-Display
     else if  Mac     move "Mac"     To Op-Display
     else if  OS2     move "OS/2"    To Op-Display
     else if  unix    move "Unix"    To Op-Display
     else if  dos     move "Dos"     To Op-Display.
*>
     if       Dos or Windows
              move WindoWS-Backup-Script-Name to Script-Name
     else if  OS2
              move OS2-Backup-Script-Name to Script-Name
     else if  Linux or Unix or Mac
              move Linux-Backup-Script-Name to Script-Name.
*>
     string   ACAS_BIN     delimited by space
              OS-Delimiter delimited by size
              Script-Name  delimited by space  into Run-Backup
     end-string
     call     "CBL_CHECK_FILE_EXIST" using Run-Backup
                                           File-Info
     end-call
     if       Return-Code not = zero
*>          and Batch-Text (1:1) not = space
              move "No BackUp Script in Bin" to Batch-Text
     else
              move 1 to Backup-Sw
              string "Using "    delimited by size
                     Script-Name delimited by space into Batch-Text
     end-if
*>
     move     zeros to WS-Process-Func
                       WS-Sub-Function.
     if       Menu-Reply = "A"            *> menu run for 1st time in run unit ONLY
              go to Load01.
*>
*> now check for PY param file & rec  as we have system-rec.
*>
     open     input PY-Param1-File.
     if       PY-PR1-Status not = zero      *> Does not exist yet so lets create it etc
              close PY-Param1-File
              go to Load25.
     close    PY-Param1-File.
*>
 Display-Menu.
     display  Usera at 0101 with erase eos foreground-color 3.
     move     To-Day to U-Date.
     move     "payroll" to WS-Caller.
     move     spaces to WS-Called
                        WS-Del-Link
                        Menu-Reply.
     move     zeros to WS-Term-Code.
     move     Maps-Ser-nn to Curs2.
     display  Maps-Ser-xx at 2474 with foreground-color 3.
     display  Curs2 at 2476 with foreground-color 3.
     display  "Copyright (c) 2025-" at 2401 with foreground-color 3.
     display  WSE-Year at 2420 with foreground-color 3.
     display  " Applewood Computers" at 2424 with foreground-color 3.
*>
 Conv-Date.
*>
*> Convert from UK to selected form
*>
     if       Date-Form not > zero and < 4
              move 1 to Date-Form.
     if       Date-USA
              move U-Date to WS-Date
              move WS-Days to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap to WS-Month
              move WS-Date to U-Date
     end-if
     if       Date-Intl
              move "ccyy/mm/dd" to WS-Date   *> swap Intl to UK form
              move U-Date (7:4) to WS-Intl-Year
              move U-Date (4:2) to WS-Intl-Month
              move U-Date (1:2) to WS-Intl-Days
              move WS-Date to U-Date
     end-if.
*>
 Conv-Date-End.
     display  U-Date at 0171 with foreground-color 3.
*>
 Display-Go.
     display  prog-name at 0301 with foreground-color 2.
     display  "Payroll System Menu" at 0333 with foreground-color 2.
*>
     accept   wsb-time from time.
     if       wsb-time not = "00000000"
              move wsb-hh to wsd-hh
              move wsb-mm to wsd-mm
              move wsb-ss to wsd-ss
              display "at "    at 0355 with foreground-color 2
              display wsd-time at 0358 with foreground-color 2.
*>
     accept   wsa-Date from date.
     if       wsa-Date not = "000000"
              move wsa-yy to u-Year
              move wsa-mm to u-Month
              move wsa-dd to u-Days
              display "on " at 0367 with foreground-color 2
              perform Conv-Date
              display U-Date at 0370 with foreground-color 2.
*>
*>  Move out all printing of reports (+,*) to a sub menu with 1s marked Reports to > sub menu  <<<<<
*>
     display  "Select one of the following by letter  :- [ ]" at 0601 with foreground-color 2.
*>
     display  "(A)  Date Entry"                     at 0804 with foreground-color 2.  *> PY000 - done
     display  "(B)  Pay Transaction Entry"          at 0904 with foreground-color 2.  *> py020 was hrsent / pyhours ?
     display  "(C)  Pay Transaction Proof"           at 1004 with foreground-color 2.  *> py030 was hrsproof
     display  "(D) * Apply Payroll"                  at 1104 with foreground-color 2. *> apply1,2 & 3
     display  "(E) * Print Payroll Journal"          at 1204 with foreground-color 2. *> **  pyjourn & pyjourn1
     display  "(F) * Print Pay Checks/BACS"          at 1304 with foreground-color 2. *> 6 - ** pychecks
     display  "(G)  Print Payment Register"         at 1404 with foreground-color 2.  *> ** pyrgstr - pyrgstr
     display  "(H)  Account Entry"                  at 1504 with foreground-color 2.  *> 8 - py920 Option 1 of 2
*>                                                                                       - vis pyactent py920 - DONE
     display  "(I)  Deduction/Earning Entry"        at 1604 with foreground-color 2.  *> 9 - dedent - deden1, 2 & 3 - py900 - done
     display  "(J)  History Entry"                  at 1704 with foreground-color 2.  *> 10 - pyupdhis  cpt 19 pg 94  & 95
*>                                                                                           - py930 DONE
     display  "(K)  Employee Data Entry"            at 1804 with foreground-color 2.  *> 11 - empent  - py010 Was 24
     display  "(L)  Print Quarterly 941 Report"     at 1944 with foreground-color 2. *> 12 ** print941 was 15
     display  "(M)  End the Current Quarter"        at 0844 with foreground-color 2. *> 13 ** pyperend was 16 done pyperend
     display  "(M)  Print W2 Report"                at 0944 with foreground-color 2.  *> ** printw2 - DONE but needs data verification was 17
     display  "(O)  Print Yearly 940 Report"        at 1044 with foreground-color 2.  *> 15 ** print940  - DONE. was 18
     display  "(P)  End the Current Year"           at 1144 with foreground-color 2. *> pyperend ? was 19 done pyperend
     display  "(Q)  Print Employee Report"          at 1244 with foreground-color 2.  *> 17 - ** empprint  -  DONE as empprint
     display  "(R)  Print History Report"           at 1344 with foreground-color 2.  *> ** hisprint - hisprint - DONE as hisprint
     display  "(S)  Print Vacation Report"          at 1444 with foreground-color 2.  *> 19 ** vacprint - DONE as vacprint
     display  "(T)  Print Account List"             at 1544 with foreground-color 2.  *> 20 ** pyactprt -> PY920 - Option 2 of 2
     display  "(X)  Exit To "                       at 1644 with foreground-color 2.
     display  Op-Display                            at 1657 with foreground-color 2.  *> OS system
     display  batch-text                            at 1749 with foreground-color 2.
     display  "(Y)  Payroll Parameter Entry"        at 1844 with foreground-color 2.  *> py900 - done
 *>    if       Param-Restrict not = "Y"
              display  "(Z)  ACAS System Setup"     at 1944 with foreground-color 2.  *> Param Entry PAYROLL 1st
*>
 Accept-Loop.
     accept   Menu-Reply at 0644 with foreground-color 6 auto UPPER.
*>
     if       Menu-Reply = "X"
              go to Pre-Overrewrite.
*>
 *>    if       Menu-Reply = "Z" and
 *>             Param-Restrict = "Y"
 *>             display  "Not permitted" at 2331 with foreground-color 2
 *>             go to Display-Menu.
*>
     move     zero to Z.
     move     Letters-Upper to Letters.
     set      Q  to  1
     search   A-Entry
              when A-Entry (Q) = Menu-Reply
              set Z to Q.
     if       Z = zero
              go to Accept-Loop.
     go       to Load-It.
*>
 Call-System-Setup.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     zero to WS-Term-Code.
     move     1 to File-Key-No.
     perform  System-Open.
     perform  System-Rewrite.                           *> in case of any changes
     perform  System-Close.
*>
     move     "sys002" to WS-Called.
     call     WS-Called using WS-Calling-Data
                              File-Defs.                 *> and we only use file00
     if       WS-Term-Code > 7                           *> sys002 only terminates with 0
              stop run.
     go       to Open-System.
*>
 Pre-Overrewrite.
     if       not Backup-Script-Found
              go to Overrewrite.
*>
     if       Linux or Unix or Mac
              string "nohup " delimited by size
                      Run-Backup delimited by space
                    " 0</dev/null &>/dev/null &" delimited by size into Full-Backup-Script
              end-string
     else
      if      Dos or Windows
              move Script-Name to Full-Backup-Script
      else
       if     OS2
              move Script-Name to Full-Backup-Script.
     perform  Overrewrite.
     call     "SYSTEM" using Full-Backup-Script.
     goback.
*>
 Overrewrite.                                  *> save to RDB or file.  NEEDED FOR PAYROLL  ????
     if       File-System-Used NOT = zero   *> Force RDB processing
              move     "66" to FA-RDBMS-Flat-Statuses
              move     1 to File-Key-No
              perform  System-Open
              move     1 to File-Key-No
              perform  System-Rewrite
*>              move     5 to File-Key-No
*>              move     PY-Param1-Record to System-Record
*>              perform   System-Rewrite
              perform  System-Close
     end-if.
*>
*> Now do the same for the Cobol file.
*>
     move     zeros to File-System-Used         *>        NEEDED FOR PAYROLL  ????
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.   *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open.                       *> Open cobol file params as I/O
     move     1 to File-Key-No.
     perform  System-Rewrite.                    *> Update Cobol file params
     perform  System-Close.                      *> Close the Cobol param file.
*>
 OverClose.
     goback.
*>
 Load-It.
     move     space to Menu-Reply.  *>  NEED TO CHECK ALL THESE   <<<<<<<<
     go       to Load01 Load02 Load03 Loadsr Loadsr Loadsr Load07 *> 04 - apply1, 05 - pyjourn, 06 - pychecks
                 Load08 Load09 Load10 Load11 Load12 Load13 Load14
                 Load15 Load16 Load17 Load18 Load19 Load20 Loadsr
                 Loadsr Loadsr Loadsr Load25 Call-System-Setup
              depending on Z.
*>
 Loader.
     go       to Display-Menu.
*>
 Load00.
     move     zero to WS-Term-Code.
     call     WS-Called using WS-Calling-Data
                              System-Record   *>  ???? needed ????
               *>>>>>>>               PY-Param1-Record  *> NEEDED ???
                              To-Day
                              File-Defs
     end-call
 *>    if       WS-Term-Code < 8    NEEDED ????? py params need updated during payroll processing ???
 *>      and    (WS-Called = "py000" or "sl080" or "sl085" or "sl090" or "sl095"
 *>                                 or "sl100" or "sl115" or "sl200" or "sl910"
 *>                                 or "sl920" or "sl930" )                          *> 200 ??  930 ??
 *>             perform Overrewrite.     *> Update sys4 and system recs in case of changes.
     if       WS-Term-Code > 7      *> Got a serious (reported) error
              go to Overrewrite.
*>
 Load00-exit.
     go       to Display-Menu.
*>
 Load000.  *> Same as load00 for the moment    <<<<<<<<<<<<<<
*>
     move     zero to WS-Term-Code.
     call     WS-Called using WS-Calling-Data
                              System-Record
                              To-Day
                              File-Defs
     end-call
     if       WS-Term-Code < 8  *> for sl055 & 060, xl150    NEEDED FOR PAYROLL  ????
              perform Overrewrite.    *> Update sys4 and system recs in case of changes.
     if       WS-Term-Code > 7      *> = Got a serious (reported) error
              perform Overrewrite
              goback.
*>
 Load000-exit.
     go       to Display-Menu.
*>
 Load01.
     move     "py000" to WS-Called.
     go       to Load000.
*>
 Load02.
     move     "py020" to WS-Called.
     go       to Load000.

*>
 Load03.
     move     "py030" to WS-Called.
     go       to Load000.
*>
 Load04.
     move     "apply1" to WS-Called.
     go       to Load000.
*>
 Load05.
     move     "pyjourn" to WS-Called.
     go       to Load000.
*>
 Load06.
     move     "pychecks" to WS-Called.
     go       to Load000.
*>
 Load07.
     move     "pyrgstr" to WS-Called.
     go       to Load000.
*>
 Load08.
     move     "py920" to WS-Called.
     go       to Load000.
*>
 Load09.
     move     "py900" to WS-Called.
     go       to Load000.
*>
 Load10.
     move     "py930" to WS-Called.
     go       to Load000.
*>
 Load11.
     move     "py010" to WS-Called.
     go       to Load000.
*>
 Load12.
     move     "print941" to WS-Called.
     go       to Load000.
*>
 Load13.
     move     "pyperend" to WS-Called. *> Processing Quarter requested
     go       to Load000.
*>
 Load14.
     move     "printw2" to WS-Called.
     go       to Load000.
*>
 Load15.
     move     "print940" to WS-Called.
     go       to Load000.
*>
 Load16.
     move     "pyperend" to WS-Called.  *> Processing Year requested
     move     1  to WS-Process-Func.
     go       to Load000.
*>
 Load17.
     move     "empprint" to WS-Called.
     go       to Load000.
*>
 Load18.
     move     "hisprint" to WS-Called.
     go       to Load000.
*>
 Load19.
     move     "vacprint" to WS-Called.
     move     2  to WS-Process-Func.
     go       to Load000.
*>
 Load20.
     move     "py920" to WS-Called.
     go       to Load000.
*>
 Load21.
 *>    move     "" to WS-Called.
 *>    perform  Load000.
*>
 Load22.
 *>    move     "" to WS-Called.
 *>    go       to Load000.
*>
 Load24.
 *>    move     "" to WS-Called.
 *>    go       to Load000.
*>
 Load25.
     move     "py900" to WS-Called.  *> WRITTEN
     go       to Load000.
*>
 Loadsr.
     display  "Sorry not available" at 2331 with foreground-color 2.
     go       to Accept-Loop.
*>
 main-exit.
     goback.
*>
 copy "Proc-Get-Env-Set-Files.cob".
*>
 zz060-Convert-Date        section.
*>********************************
*>
*>  Converts date in binary to UK/USA/Intl date format
*>****************************************************
*> Input:   u-bin
*> output:  WS-Date as uk/US/Inlt date format
*>          U-Date & WS-Date = spaces if invalid date
*>
     perform  maps04.
     if       U-Date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     U-Date to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap Month and Days
              move WS-Days to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap to WS-Month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     U-Date (7:4) to WS-Intl-Year.
     move     U-Date (4:2) to WS-Intl-Month.
     move     U-Date (1:2) to WS-Intl-Days.
*>
 zz060-Exit.
     exit     section.
*>
 maps04       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
