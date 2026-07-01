       >>source free
*>
*>***************************************************
*>                                                  *
*>          IRS  System  Menu  Control              *
*>                                                  *
*>***************************************************
*>
 identification division.
 program-id.            irs.
*>
*> Author.              Cobol conversion by V B Coen, FIDPM FBCS 13/10/1982
*>                      for Applewood Computers.
*>**
 Date-Compiled.         Today.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             System Menu and System File Maintenance Program.
*>**
*> Function Keys Used.
*>                      F1 through F10 - Menu only.
*>**
*> Calls.
*>                      maps04.
*>                      sys002.
*>                      acas000   ->
*>                       systemMT
*>                      irs010
*>                      irs020
*>                      irs030
*>                      irs040
*>                      irs050
*>                      irs060
*>                      irs065 (sort)
*>                      irs070
*>                      irs080
*>                      irs085 (sort)
*>                      irs090.
*> All can call :
*>                      acas008  ->       { SL or PL postings  FH }
*>                       slpostingMT
*>                      acasirsub1  ->
*>                       irsnominalMT
*>                      acasirsub3 ->
*>                       irsdfltMT
*>                      acasirsub4 ->
*>                       postingMT
*>                      acasirsub5 ->
*>                       irsfinalMT
*>                      irsubp            { Sorted Postings - Original FH }
*>**
*> Error messages Used.
*>  System Wide
*>                      SM901 }
*>                      SM903 } Produced by DAL.
*>                      SM904 }
*>                      SY006.
*>                      SY007.
*>                      SY008.
*>                      SY009.
*>                      SY010.
*>                      SY011.
*>                      SY013.
*>                      IR901 }
*>                      IR902 } From FH.
*>                      IR911.
*>                      IR912 }
*>                      IR913 }
*>                      IR914 }
*>                      IR915 }
*>                      IR916 }
*>  Module Specific.
*>                      IR001.
*>**
*> Changes.
*>
*> 11/07/83 vbc - fix out of memory fault,build in date validation.
*> 25/07/83 vbc - hilite displays where needed.
*> 26/07/83 vbc - test for numeric in date vet routine.
*> 16/09/83 vbc - fix next post = zero.
*> 22/12/83 vbc - zeroise Menu-Reply before accept, 2 clr bug.
*> 28/12/83 vbc - new progs - irs080,085,090
*> 28/05/84 vbc - hilite display heads.
*> 14/04/85 vbc - fix bug in disp of prog-name in set-up.
*> 05/09/88 vbc - v2.53 Modify for cobol/2.
*> 15/01/09 vbc - start of conversion to open/Gnu cobol
*> 17/01/09 vbc - moving screens to screen section and adjust
*>                accept/displays.
*> 22/01/09 vbc - Migration to Open Cobol as version 3.
*> 20/02/09 vbc - Update date from todays on entry when dates differ.
*>                Generally added support environment LINES and COLUMNS
*>                within system but not needed for this module.
*> 22/02/09 vbc - Changed names of Account fixup  and Posting amaendment
*>                Programs to better reflect what they do.
*> 25/02/09 vbc - Support for OS type by asking user as no mechanism exists to
*>                obtain by Cobol code, Call backup script after getting 'X'
*>                if script found in current directory or ~/bin. Few more
*>                very minor bugs cleared.
*>                Changed progs, specs & manual to match.
*> 01/03/09 vbc - Transferred all code changes to commercial versions incl.
*>                MySQL and Oracle multi client/company versions.
*>                Include rewrite Final accounts into OOo exports for
*>                U.K. Company House and HMRC etc with all notes. Amend docs.
*> 14/09/10 vbc - Added Cob Env variables presets.
*> 21/09/10 vbc - .16 added test for Mac OSX
*>                    added print spool name processing.
*> 02/10/11 vbc - .17 Changed to Cbl-File-Details year to xx for OC v2.
*> 21/11/11 vbc - .18 Initialise system-record on system setup & add prelim code
*>                    for processing ACAS-IRS env variable but more needs to be done.
*> 02/05/16 vbc - .19 Changed cosmetic - 'OS/10' to 'OSX' on setup screen.
*> 19/10/16 vbc - .20 Repositioned processing for program environ args to
*>                    start of prog, adjust ACAS_IRS to 500 to match rest of ACAS.
*>                    IRS SYSTEM FILE DISCONTINUED FOR THE ACAS ONE.
*>
*> 20/10/16 vbc - .21 Introducing error messages into WS as literals in case
*>                    user needs to change to own language - as used in ACAS.
*>                    Using wsnames in copybooks for ALL progs in v3.02.
*>                    Update programs to v3.02 as RDB support added.
*>
*> 25/11/16 vbc - .22 Using acas param file to recreate the irs system-record.
*>                    After running specific modules [ irs030, ]
*>                    transfer specific data back -
*>                    Next-Post,
*>                    to ACAS param file and update record on file/table.
*>
*> 26/11/16 vbc - .23 Clear out all set up processes as now done in sys002.
*>                    Change all back up scripts to use the acas ones
*>                    as all Cobol file if used are in acas directory.
*>                    Removed maps01 & 99 processing - not needed.
*>                    Changed usage of Cbl-File-Details to File-Info (see .17)
*>
*> 27/11/16 vbc - .24 file-defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*>
*> 20/12/16 vbc -     All irs progs call cpybk Proc-ZZ100-ACAS-IRS-Calls.
*>
*> 30/12/16 vbc - .25 Added PL-App-Created & Approp to zz090 & zz095 (used in irs020).
*> 25/04/17 vbc - .26 Change init param open to Input as I/O creates if not exist.
*> 29/01/18 vbc - .27 Changed copies to use copybooks where poss.
*>                    Removed un-used error messages. IR011-16 are needed.
*> 05/02/18 vbc - .28 Dont close file pre calling sys002 as not open!!!
*> 07/02/18 vbc       Removed dead code for call maps03 - replaced with maps04
*>                     years ago.
*>                    Re-positioned Menu so that system set up is to ACAS norms as
*>                    option Z.
*> 08/02/18 vbc - .29 Force run of back up (but only if installed), prior to running
*>                    irs060 as it can be asked to do EOY processing on accounts.
*>                    This process changes nominal records, ie., clearing down and/or
*>                    moving data.
*>                    This process will also update any changed system data first
*>                    see para EOJ. Same as EOJ so will run again.
*> 09/02/18 vbc - .30 Added support for backup scripts for Pre and Post EOY processing.
*> 10/02/18 vbc - .31 Renamed IR011-16 to IR911-16 and others.
*> 11/03/18 vbc - .32 In aa005-Open-System remove the close, open I/O which
*>                    only used to read, Make option Z only available if
*>                    Param-Restrict <> "Y" & change menu title - same as all other
*>                    systems.
*>                    Removed password processing for O/S version as protection is
*>                    built in to *nix, Windows with user passwords and ACL for users
*>                    that require it.
*>                    Extra comments for script names.
*> 14/04/18 vbc - .33 Remark out code for reading in rdb system data as file will ALWAYS be up2date.
*>                    If System setup requested write out current sys record 1.
*> 22/05/18 vbc - .34 Small changes to the backup process at prerewrite as did not run.
*> 28/05/18 vbc - .35 Added ws fields for env. columns and lines to verify minimums.
*> 18/06/20 vbc -     Experimental unused CDF code removed.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 05/01/25 vbc   .36 Added get ACAS param rec (zz900) before saving irs param rec
*>                    and rewriting param rec - last 2 already present
*>                    but re-adjusted twice-ish.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*> TODO for O/S versions.
*>  1.           For UK users add code to support auto VAT returns ->
*>
*>  2.           Likewise for HMRC & Company House return via CT600
*>                 Having worked out how !!
*>                 Could just produce the figures displayed/printed for use in
*>                 the online data entry but will be get changed again ?
*>               But are we putting this into OS (Open Source) version
*>               as it requires on-going support ?
*>
*>  3.           Consider if need for multi date format usage as IRS only uses
*>               UK format (entry, display & print).
*>
*>*****************************************************************************
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
*>*******************
*>
 copy "envdiv.cob".
 data division.
*>************
*>
 working-storage section.
*>----------------------
 77  Prog-Name            pic x(14)    value "IRS (3.3.00) ".
 77  z                    binary-short value zero.
 77  Call-Prog            pic x(6)     value spaces.
 77  Batch-Text           pic x(28)    value spaces.
 77  Script-Name          pic x(24)    value spaces.
 77  Script-Pre-EOY-Name  pic x(24)    value spaces.
 77  Script-Post-EOY-Name pic x(24)    value spaces.
 77  Run-Backup           pic x(512)   value spaces.  *> size changed
 77  Run-Pre-Backup       pic x(512)   value spaces.
 77  Run-Post-Backup      pic x(512)   value spaces.
 77  Full-Backup-Script   pic x(512)   value spaces.
 77  OS-Delimiter         pic x        value "/".
 77  ACAS_LEDGERS         pic x(500)   value spaces.
 77  ACAS_BIN             pic x(512)   value spaces.
 77  Arg-Number           pic 9        value zero.
 77  Init-System-File-SW  pic 9        value zero.
 77  Init-Sys4-File-SW    pic 9        value zero.
 77  Init-Final-File-SW   pic 9        value zero.
 77  Init-Default-File-SW pic 9        value zero.
*>
*>========================================================
*>  in case file layout upgrade is needed (system record ? ).
*>   Using a file update program.
*>
 copy "sys-params-versioning.cob".
*>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*> Holds program parameter values from command line
 01  Arg-Vals                         value spaces.
     03  Arg-Value       pic x(525)  occurs 2.
 01  Arg-Test            pic x(525)   value spaces.
*>
 01  Backup-Sw                    pic 9     value zero.
     88  Backup-Script-Found                value 1.
 01  Backup-Pre-Sw                pic 9     value zero.
     88  Backup-Pre-Script-Found            value 1.
 01  Backup-Post-Sw               pic 9     value zero.
     88  Backup-Post-Script-Found           value 1.
*>
*> Note that Linux scripts are used with OSX and other *nix systems.
*>
 01  Linux-Backup-Script-Name     pic x(24) value "acasbkup.sh".
 01  Linux-Pre-EOY-Script-Name    pic x(24) value "acasbkup-Pre-EOY.sh".
 01  Linux-Post-EOY-Script-Name   pic x(24) value "acasbkup-Post-EOY.sh".
 01  Windows-Backup-Script-Name   pic x(24) value "acasbkup.bat".
 01  Windows-Pre-EOY-Script-Name  pic x(24) value "acasbkup-Pre-EOY.bat".
 01  Windows-Post-EOY-Script-Name pic x(24) value "acasbkup-Post-EOY.bat   ".
 01  OS2-Backup-Script-Name       pic x(24) value "acasbkup.cmd".
 01  OS2-Pre-EOY-Script-Name      pic x(24) value "acasbkup-Pre-EOY.cmd".
 01  OS2-Post-EOY-Script-Name     pic x(24) value "acasbkup-Post-EOY.cmd".
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
*> the following for GC and screen
*>
 01  All-My-Constants        pic 9(4).
 copy "screenio.cpy".
*>
 01  ws-date-formats.
     03  ws-swap             pic xx.
     03  ws-date             pic x(10).
     03  ws-UK redefines ws-date.
         05  ws-days         pic xx.
         05  filler          pic x.
         05  ws-month        pic xx.
         05  filler          pic x.
         05  ws-year         pic x(4).
     03  ws-USA redefines ws-date.
         05  ws-usa-month    pic xx.
         05  filler          pic x.
         05  ws-usa-days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  ws-Intl redefines ws-date.
         05  ws-intl-year    pic x(4).
         05  filler          pic x.
         05  ws-intl-month   pic xx.
         05  filler          pic x.
         05  ws-intl-days    pic xx.
*>
 *> 01  date-fields.
 *>    03  q               pic s99     comp  value zero.
*>
 *>    03  days-in-month   pic x(24)  value "312831303130313130313031".
 *>    03  filler  redefines  days-in-month.
 *>        05  days        pic 99     occurs 12.
*>
 *>    03  ws-work1        pic s9(5)   comp.
 *>    03  ws-work2        pic s9(5)   comp.
*>
 copy "wsmaps03.cob".
 copy "wscall.cob".
 copy "wstime.cob".
 copy "wsfnctn.cob".
*>
 01  WS-Work-Fields.
     03  ws-pass         pic x(4)   value spaces.
     03  ws-spaces       pic x(18)  value spaces.   *> chgd from x10 for SY006 25/11/16
     03  Menu-Reply      pic x      value "1".      *> Force Run Date updating at SOJ.
     03  wsfile          pic x(12).                 *> Not used
     03  ws-reply        pic x.
     03  op-display      pic x(7).
     03  a               pic 99        comp.
     03  wsmaps-ser.                                *> Not used
         05  wsmaps-ser-xx pic xx.
         05  wsmaps-ser-nn pic 9(4).
*>
     03  ws-env-columns  pic 999       value zero.
     03  ws-env-lines    pic 999       value zero.
*>
*>  Holds data from system file (IRS-Entry-Block) to see if there has been any changes
*>    that necessitates the system record being updated.
*>
     03  WS-Next-Post       pic 9(5) value zero.  *> Holds current values from prog. start
     03  WS-Pass-Value      pic 9    value zero.  *>  Ditto
     03  WS-Save-Sequ       pic 9    value zero.  *>  Ditto but may not be needed.
     03  WS-First-Time-Flag pic 9    value zero.  *>  Ditto
     03  WS-System-Work-Group pic x(18)  value spaces. *>  Ditto - - - - - -
     03  WS-PL-App-Created  pic x    value space.
     03  WS-PL-Approp-AC    pic 9(5) value zero.
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
 copy "irswssystem.cob"
              replacing system-record  by IRS-System-Params. *> (01 level)
*>
 copy "wsnames.cob".      *> Ditto
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
     03  WS-IRSNL-Record       pic x.
     03  WS-IRS-Default-Record pic x.
     03  Posting-Record        pic x.
     03  WS-IRS-Posting-Record pic x.
     03  Final-Record          pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  to-day              pic x(10).                   *> in acas format
*>
 01  WS-Temp-System-Rec  pic x(2048).   *> Size overkill
*>
 01  Error-Messages.
*> System Wide
     03  SY006          pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007          pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008          pic x(31) value "SY008 Note message & Hit return".
     03  SY009          pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY010          pic x(46) value "SY010 Terminal program not set to length => 24".
     03  SY011          pic x(47) value "SY011 Error on systemMT processing, Fs-reply = ".
     03  SY013          pic x(47) value "SY013 Terminal program not set to Columns => 80".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, Fs-reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, Fs-reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, Fs-reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, Fs-reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, Fs-reply = ".
*> Module specific
     03  IR001          pic x(51) value "IR001 Running Back up, prior to running EOY process".
*>
 screen section.
*>-------------
*>
 01  Menu-Screen-1                                       background-color cob-color-black
                                                         foreground-color cob-color-green.
     03  pic x(14) from prog-name          line  1 col 1     blank screen.
     03  value "IRS System Menu"                   col 34 foreground-color cob-color-green.
     03  pic x(8) from Run-Date                    col 73.  *> uses the IRS param rec.
     03  value "Client -"                  line  3 col 1.
     03  pic x(29) from Client                     col 10 foreground-color cob-color-cyan.
     03  value "Start date -"                      col 39.
     03  pic x(8) from Start-Date                  col 52 foreground-color cob-color-cyan.
     03  value "End date -"                        col 62.
     03  pic x(8) from End-Date                    col 73 foreground-color cob-color-cyan.
     03  value "Select the required function    ["
                                           line  5 col 1.
     03  pic x using Menu-Reply  auto              col 34 foreground-color cob-color-yellow.
     03  value "]"                                 col 35.
     03  value "(1)  Date Entry"           line  7 col 6.
     03  value "(2)  Accounts Set-Up & Maintenance"
                                           line  8 col 6.
     03  value "(3)  Default A/Cs Set-Up & Maintenance"
                                           line  9 col 6.
     03  value "(4)  Posting"              line 10 col 6.
     03  value "(5)  Trial Balance"        line 11 col 6.
     03  value "(6)  Audit Trail"          line 12 col 6.
     03  value "(7)  Accounts Production"  line 13 col 6.
     03  value "(8)  Posting Amendments"   line 14 col 6.
     03  value "(9)  Analysis Report"      line 15 col 6.
     03  value "(A)  Nominal File Fix up"  line 16 col 6.
     03  value "(X)  Exit to "             line 19 col 6.
     03  pic x(7)  from Op-Display                 col 19.
     03  pic x(28) from Batch-Text                 col 28 foreground-color 3.
*> displayed subject to param setting.
     03  value "(Z)  System Set-Up"        line 20 col 6.
     03  value "F1 to F10 = options 1 to A;  Return to Accept " &
             "data;  X or Escape to quit"  line 22 col 1
                                                highlight foreground-color cob-color-white.
     03  value "Copyright (c) 1976-"       line 24 col 01 foreground-color 3.
     03  pic 9(4)  from wse-year                   col 20 foreground-color 3.
     03  value " Applewood Computers"              col 24 foreground-color 3.
     03  pic xx    from maps-ser-xx                col 74 foreground-color 3.
     03  pic 9(4)  from curs2                      col 76 foreground-color 3.
*>
 procedure division.
*>*****************
*>
 irs-main section.
*>***************
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
*>
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     function current-date to wse-date-block.
     perform  zz020-Get-Program-Args.
*>
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              display SY010    at 0101 with erase eos
              accept  ws-reply at 0133
              goback.
     accept   ws-env-Columns from Columns.
     if       ws-Env-Columns < 80
              display SY013    at 0101 with erase eos
              accept  ws-reply at 0133
              goback.
*>
 aa005-Open-System.                    *> First get system param cobol file
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  acas000-open-Input.      *> as Input as I/o may create
     if       fs-reply not = zero
 *>             perform acas000-close
              move    "sys002" to ws-called     *> create param file by requesting info from user
              call    ws-called using ws-calling-data file-defs
              perform acas000-open
     end-if.
*>
 aa010-Get-System-Recs.
     move     zeros to File-System-Used         *> again in case RDB setup
                       File-Duplicates-In-Use.  *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  acas000-Read-Indexed.        *> Read Cobol file
     if       fs-reply not = zero          *> should NOT happen
              perform acas000-close
              move    "sys002" to ws-called    *> create param file by requested info from user
              call    ws-called using ws-calling-data file-defs
              perform acas000-open
              go to aa010-Get-System-Recs
     end-if.
     move     WS-System-Record to WS-Temp-System-Rec.   *> save in case of sys-rec-4 overwrite
*>
*> BY PASS THIS CODE AS THE FILE WILL ALWAYS BE CURRENT.
*>
*>  We now have the param file along with RDB information so -
*>  Check if RDB in use & if so, close Cobol file and open
*>   and read the RDB system-rec but if recs do not exist
*>    write using the Cobol file versions.
*>
*>     if       File-System-Used NOT = zero      *> RDB in use ( could be values 1 thru 5 but currently only 1)
*>              move     File-System-Used to Arg-Number       *> save value from param in Cobol file
*>              move     zero to File-System-Used             *> so we can close the cobol file
*>              perform  acas000-Close                        *>  close cobol file
*>              move     Arg-Number to File-System-Used       *> restore value from param in cobol file
*>              move     "66" to FA-RDBMS-Flat-Statuses       *> Force RDB processing
*>              move     1 to File-Key-No
*>              perform  acas000-Open                         *> It could be values 1 thru 5 when the other RDB's are programmed for
*>              perform  acas000-Read-Indexed                 *> get the record from the RDB table
*>              if       fs-reply not = zero                  *> but if error we have a problem such as someone forgot to run system load modules.
*>                       move WS-Temp-System-Rec to WS-System-Record   *> restore saved cobol file rec
*>                       perform acas000-Write                *> So create RDB row in SYSTEM-REC from the Cobol file data
*>                       if      fs-reply not = zero          *> Here on, should not happen !
*>                               display SY011 at 2301
*>                               display fs-reply at 2348
*>                               display SY008    at 2401
*>                               accept  ws-Reply at 2432
*>                               perform acas000-Close
*>                               goback
*>                       end-if                              *> UNREMARKED THIS 11/03/18
*>              end-if
*>     end-if.
     perform  acas000-Close.            *> Release param file for others
*>
*>   So having read param file create the IRS param record in WS and this is the
*>    one that is passed to all irs programs
*>
     perform  zz090-Set-Up-IRS-System-Data.          *> dont forget to run zz095 after
*>
*>  Back to work.
*>
     move     ACAS-Run-Date to u-bin.
     call     "maps04" using maps03-ws.
     move     u-date to to-day.
*>
     if       ACAS-Op-System = zero
              move "O/S" to op-display.
     if       Linux    move "Linux"   to op-display
     else if  Windows  move "Windows" to op-display
     else if  Mac      move "Mac"     to op-display
     else if  Dos      move "Dos"     to op-display
     else if  OS2      move "OS/2"    to op-display
     else if  Unix     move "Unix"    to op-display.
*>
     if       Dos or Windows
              move Windows-Backup-Script-Name   to Script-Name
              move Windows-Pre-EOY-Script-Name  to Script-Pre-EOY-Name
              move Windows-Post-EOY-Script-Name to Script-Post-EOY-Name
     else if  OS2
              move OS2-Backup-Script-Name       to Script-Name
              move OS2-Pre-EOY-Script-Name      to Script-Pre-EOY-Name
              move OS2-Post-EOY-Script-Name     to Script-Post-EOY-Name
     else if  Linux or Unix or Mac
              move Linux-Backup-Script-Name     to Script-Name
              move Linux-Pre-EOY-Script-Name    to Script-Pre-EOY-Name
              move Linux-Post-EOY-Script-Name   to Script-Post-EOY-Name
     end-if.
*>
*> Test if script in users bin directory [ applies for processing Cobol files & RDB ]
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
*> Now for the pre and post EOY scripts
*>
     string   ACAS_BIN     delimited by space
              OS-Delimiter delimited by size
              Script-Pre-EOY-Name  delimited by space  into Run-Pre-Backup
     end-string
     call     "CBL_CHECK_FILE_EXIST" using Run-Pre-Backup
                                           File-Info
     if       Return-Code = zero
              move 1 to Backup-Pre-Sw
     end-if
     string   ACAS_BIN     delimited by space
              OS-Delimiter delimited by size
              Script-Post-EOY-Name  delimited by space  into Run-Post-Backup
     end-string
     call     "CBL_CHECK_FILE_EXIST" using Run-Post-Backup
                                           File-Info
     if       Return-Code = zero
              move 1 to Backup-Post-Sw
     end-if
*>
     if       Menu-Reply = "1"
              call "irs000" using WS-System-Record   *> ACAS param record
                                  to-day
              end-call
     end-if.
*>
     move     run-date to u-bin.    *> from bin
     perform  maps04.
     move     u-date to to-day.     *>  to char
*>     perform  zz060-Convert-Date.   *> not pres here for stock but conv. date in ws-date THIS MIGHT BE AN ERROR <<<
*>                                                      menu uses the irs param file dates
 Main-Loop.
     move     space to Menu-Reply.
     move     maps-ser-nn to curs2.
     display  Menu-Screen-1.
     if       Param-Restrict = "N"
              display  spaces at 2001 with erase eol.
     accept   Menu-Screen-1.
 *>    move     function upper-case (Menu-Reply) to Menu-Reply.
     if       Menu-Reply = "1"
           or Cob-Crt-Status = Cob-Scr-F1
              call "irs000" using WS-System-Record
                                  to-day
              end-call
              perform zz090-Proc-Run-Date            *> updated by irs000
     end-if.
     if       Menu-Reply = "2"
           or Cob-Crt-Status = Cob-Scr-F2
              call   "irs010" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              go to main-loop.
     if       Menu-Reply = "3"
           or Cob-Crt-Status = Cob-Scr-F3
              call   "irs020" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              go to main-loop.
     if       Menu-Reply = "4"
           or Cob-Crt-Status = Cob-Scr-F4
              call   "irs030" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              go to main-loop.
     if       Menu-Reply = "5"
           or Cob-Crt-Status = Cob-Scr-F5
              call   "irs040" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              go to main-loop.
     if       Menu-Reply = "6"
           or Cob-Crt-Status = Cob-Scr-F6
              call   "irs050" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call  *> irs050 calls sort program irs055
              go to main-loop.
     if       Menu-Reply = "7"
           or Cob-Crt-Status = Cob-Scr-F7
              if     Backup-Pre-Script-Found  *> Back up before running in case EOY is run.
                     display IR001 at 2401 with foreground-color 4 erase eol
                     perform EOJ-Pre
                     display space at 2401 with erase eol
              end-if
              call   "irs065" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              call   "irs060" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              if     Backup-Post-Script-Found  *> Back up after running in case EOY was run.
                     display IR001 at 2401 with foreground-color 4 erase eol
                     display "Post " at 2431 with foreground-color 4
                     perform EOJ-Post
                     display space at 2401 with erase eol
              end-if
              go to main-loop.
     if       Menu-Reply = "8"
           or Cob-Crt-Status = Cob-Scr-F8
              call   "irs070" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              go to main-loop.
*>
     move     function upper-case (Menu-Reply) to Menu-Reply.
*>
     if       Menu-Reply = "9"
           or Cob-Crt-Status = Cob-Scr-F9
              call   "irs085" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              call   "irs090" using IRS-System-Params
                                    WS-System-Record   *> ACAS system rec.
                                    file-defs
              end-call
              go to main-loop.
*>
     if       Menu-Reply = "A"
           or Cob-Crt-Status = Cob-Scr-F10
              call   "irs080" using IRS-System-Params
                                  WS-System-Record   *> ACAS system rec.
                                  file-defs
              end-call
              go to main-loop.
*>
     if       Menu-Reply = "Z"
              move     "00" to  FA-RDBMS-Flat-Statuses  *> Force Cobol proc.
              move     zero to ws-term-code
              move     1 to File-Key-No
              perform  acas000-Open
              perform  acas000-Rewrite                           *> in case of any changes
              perform  acas000-Close
              move    "sys002" to ws-called     *> create param file by requesting info from user
              call    ws-called using ws-calling-data
                                      file-defs
              end-call
              go to aa005-Open-System.          *> Must re-read the param file & setup data
     if       Menu-Reply not = "X"
              and Cob-Crt-Status not = Cob-Scr-Esc
              go to main-loop.
*>
 EOJ.                                       *>  Cobol or RDB closed
     move     zeros to File-System-Used         *> again in case RDB setup
                       File-Duplicates-In-Use.  *> if sys002 just been run.
     move     "00" to  FA-RDBMS-Flat-Statuses.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  acas000-Open.
     perform  acas000-Read-Indexed.        *> Read Cobol file
     perform  acas000-Close.
*>
     perform  zz095-Restore-IRS-System-Data.
     move     1 to File-Key-No.             *> now default to file processing
     move     "00" to FA-RDBMS-Flat-Statuses.    *> Now do file
     perform  acas000-Open.
     perform  acas000-Rewrite.         *> In case of any changes
     perform  acas000-Close.
     if       File-System-Used NOT = zero   *> Force RDB processing
              move     "66" to FA-RDBMS-Flat-Statuses
              perform  acas000-Open
              perform  acas000-Rewrite         *> In case of any changes
              perform  acas000-Close
     end-if
*>
     if       Backup-Script-Found
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
                       move Script-Name to Full-Backup-Script
                end-if
               end-if
              end-if
              call     "SYSTEM" using Full-Backup-Script
     end-if.
*>
 EOJ-End.
     goback.
*>
 EOJ-Pre.                                       *>  Cobol or RDB closed
*>
*> First save changed data in params
*>
     if       Backup-Pre-Script-Found
              move     zeros to File-System-Used         *> again in case RDB setup
                                File-Duplicates-In-Use  *> if sys002 just been run.
              move     "00" to  FA-RDBMS-Flat-Statuses  *> Force Cobol proc.
              move     1 to File-Key-No
              perform  acas000-Open
              perform  acas000-Read-Indexed
              perform  acas000-Close
              perform  zz095-Restore-IRS-System-Data
              move     1 to File-Key-No              *> now default to file processing
              move     "00" to FA-RDBMS-Flat-Statuses    *> Now for the file
              perform  acas000-Open
              perform  acas000-Rewrite
              perform  acas000-Close
              if       File-System-Used NOT = zero   *> Force RDB processing
                       move     "66" to FA-RDBMS-Flat-Statuses
                       perform  acas000-Open
                       perform  acas000-Rewrite
                       perform  acas000-Close
              end-if
*>
              if       Linux or Unix or Mac
                       string "nohup " delimited by size
                               Script-Pre-EOY-Name delimited by space
                               " 0</dev/null &>/dev/null &" delimited by size into Run-Pre-Backup
                       end-string
              else
               if      Dos or Windows
                       move Script-Pre-EOY-Name to Run-Pre-Backup
               else
                if     OS2
                       move Script-Pre-EOY-Name to Run-Pre-Backup
                end-if
               end-if
              end-if
              call     "SYSTEM" using Run-Pre-Backup
     end-if.
*>
 EOJ-Post.
*>
*> Changed data in params already saved (pre).
*>
     if       Backup-Post-Script-Found
              if       Linux or Unix or Mac
                       string "nohup " delimited by size
                               Script-Post-EOY-Name delimited by space
                               " 0</dev/null &>/dev/null &" delimited by size into Run-Post-Backup
                       end-string
              else
               if      Dos or Windows
                       move Script-Name to Run-Post-Backup
               else
                if     OS2
                       move Script-Name to Run-Post-Backup
                end-if
               end-if
              end-if
              call     "SYSTEM" using Run-Post-Backup
     end-if.
*>
 zz060-Convert-Date        section.
*>********************************
*>
*>  Converts date in binary to UK/USA/Intl date format
*>****************************************************
*> Input:   u-bin
*> output:  ws-date as uk/US/Inlt date format
*>          u-date & ws-Date = spaces if invalid date
*>
     perform  maps04.
     if       u-date = spaces
              move spaces to ws-Date
              go to zz060-Exit.
     move     u-date to ws-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     u-date (7:4) to ws-Intl-Year.
     move     u-date (4:2) to ws-Intl-Month.
     move     u-date (1:2) to ws-Intl-Days.
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
*>   New for IRS and RDB support.
*>
 zz090-Set-Up-IRS-System-Data  Section.
*>************************************
*>
 zz090-Start.
*> We will remap the ACAS param data to that for IRS changing date formats
*>  as needed. Likewise User name & address, VAT rates (1-3) as
*>   1=Std ([S]tandard), 2=[R]educed, 3=[Z]ero, Start & end dates,
*>   Client name, next posting no., 1st time flag, PL-Approp & create flag
*>    Pass value, sequence & work group. It is done by -
*>  Moving fields to the old IRS system file layout renamed IRS-System-Parms
*>    and this record is passed to all irs modules.
*>
*>  Likewise after running any changes are updated in the ACAS system record
*>    and written out.
*>  Should consider that if RDB in use then individual fields are only updated. <<< ?
*>
*>  At point of running this section the ACAS system parameter file must
*>    have been read into the (ACAS) System-Record with the IRS old system
*>      record renamed as IRS-System-Params and it is this that is passed
*>      to all programs,
*>      Which is exactly as it has always been and therefore minimising
*>        additional changes using the KISS principal.
*>
*>  YES I know these notes are more for me, to remind me to make sure it is DONE !
*>
*>   This block moves all IRS data from the ACAS primary data.
*>
     initialise IRS-System-Params with filler.
*>
     move     ACAS-Pass-Word to Pass-Word.
     move     ACAS-Suser     to Suser.
     move     ACAS-Address-1 to Address-1.
     move     ACAS-Address-2 to Address-2.
     move     ACAS-Address-3 to Address-3.
     move     ACAS-Address-4 to Address-4.
     move     Vat-Rate-1     to Vat in IRS-System-Params.
     move     Vat-Rate-2     to Vat2.
     move     Vat-Rate-3     to Vat3.
     move     ACAS-Print-Spool-Name
                             to Print-Spool-Name.
     move     ACAS-Op-System to System-Ops.      *> but move this in as USED in menu ?
*>
*>  This block from IRS within ACAS param record at IRS-Entry-Block.
*>   Field names have been changed at the COPY verb to prevent duplicates.
*>
     move     IRS-Client            to Client.
     move     IRS-Next-Post         to Next-Post
                                       WS-Next-Post. *> used after irs030 run 4 update.
     move     IRS-Pass-Value        to Pass-Value
                                       WS-Pass-Value.
     move     IRS-Save-Sequ         to Save-Sequ
                                       WS-Save-Sequ.
     move     IRS-System-Work-Group to System-Work-Group
                                       WS-System-Work-Group.
     move     IRS-PL-App-Created    to PL-App-Created
                                       WS-PL-App-Created.
     move     IRS-PL-Approp-AC      to PL-Approp-AC
                                       WS-PL-Approp-AC.
     move     IRS-First-Time-Flag   to First-Time-Flag
                                       WS-First-Time-Flag.
*>
*>  We should have now populated the old IRS system record (layout) from ACAS params.
*>    So now convert the binary run, start & end date from binary days to x(8)
*>       by ignoring the cc subfield (century) as not used in IRS
*>
 zz090-Proc-Run-Date.
     move     ACAS-Run-Date to u-bin.
     perform  maps04.                             *> now have x(10) & dd/mm/ccyy
     string   u-date (1:6)     delimited by size
              u-date (9:2)     delimited by size  *> Only grab YY and not CC
                     into Run-Date                *> As IRS uses dd/mm/yy
     end-string.
*>
 zz090-Proc-Start-Date.
     move     ACAS-Start-Date to u-bin.
     perform  maps04.
     string   u-date (1:6)     delimited by size
              u-date (9:2)     delimited by size
                     into Start-Date
     end-string.
 zz090-Proc-End-Date.
     move     ACAS-End-Date to u-bin.
     perform  maps04.
     string   u-date (1:6)     delimited by size
              u-date (9:2)     delimited by size
                     into End-Date
     end-string.
*>
*> Done, now have run, start & end dates converted from bin to X(8) as dd/mm/yy
*>
 zz090-Exit.
     exit     section.
*>
 zz095-Restore-IRS-System-Data  Section.
*>************************************
*>
*>  EXPAND THIS IF NEEDED HAVING LOOKED AT IRS program conversion to RDB.
*>
*>  This block from IRS within ACAS param record at IRS-Entry-Block.
*>   Field names have been changed at the COPY verb to prevent duplicates.
*>
*>   We are testing the WS stored data obtained after reading the ACAS system record
*>    against the data in the IRS system params that may have been changed.
*>
     if       WS-Next-Post         not = Next-Post
              move     Next-Post  to IRS-Next-Post.  *> via irs030
*>                                                        & irs070
     if       WS-Pass-Value        not = Pass-Value
              move     Pass-Value to IRS-Pass-Value.
*>
     if       WS-Save-Sequ         not = Save-Sequ
              move     Save-Sequ  to IRS-Save-Sequ.
*>
     if       WS-System-Work-Group not = System-Work-Group
              move     System-Work-Group to IRS-System-Work-Group.
*>
     if       WS-First-Time-Flag    not = First-Time-Flag
              move     First-Time-Flag   to IRS-First-Time-Flag.
*>
     if       WS-PL-Approp-AC       not = PL-Approp-AC
              move     PL-Approp-AC    to IRS-PL-Approp-AC.
*>
     if       WS-PL-App-Created     not = PL-App-Created
              move     PL-App-Created  to IRS-PL-App-Created.
*>
 zz095-Exit.
     exit     section.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
 copy "Proc-Get-Env-Set-Files.cob".
*>
