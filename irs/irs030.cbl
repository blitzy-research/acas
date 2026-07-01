       >>source free
*>*****************************************************************
*>                                                                *
*>                Transaction  Posting  Program                   *
*>                                                                *
*>*****************************************************************
 identification          division.
*>================================
*>
 program-id.            irs030.
*>
*> Author.              Cobol conversion by Vincent B Coen, FIDPM FBCS
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 1976-2026 and later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Posting program
*>**
*> Function Keys Used.
*>                      F1 to display Defaults on requesting default number.
*>                      F3 on accepting posting date to end batch input for current default.
*>                      SOME CODING PRESENT but no where completed as still not sure it
*>                       is needed for - - -
*>                      F9 on request for Default account will allow program to NOT use
*>                         the default method but to use initially entering a from and to
*>                         account number and this will be expanded if feasible to use a
*>                         entry method using first few letters of the descriptions of a
*>                         account.  This will involve a lot of changes possibly so will
*>                         be very experimental.
*>                         This option is will NOT be available anytime soon.
*>                      F4 is NOT YET AVAILABLE - not coded.
*>                      F9 is NOT YET AVAILABLE - not coded.
*>**
*> Version.             See prog-name in ws.
*>**
*> Calls.
*>                      acas008  ->   SL posting  FH.
*>                       slpostingMT
*>                      acasirsub1  ->
*>                       irsnominalMT
*>                      acasirsub3 ->
*>                       irsdfltMT
*>                      acasirsub4 ->
*>                       postingMT
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
*>                      IR030 End of listing. Hit return for Menu.
*>                      IR031 No Ledger Posting file found. Process Aborted
*>                      IR032 Invalid key 1 =
*>                      IR033 Invalid key 2 =
*>                      IR034 That Account now deleted!!!  Re-enter
*>                      IR035 VAT Account/s not present, Fix it. Now hit return
*>                      IR036 Amount not numeric. Re-Enter
*>                      IR037 That account does not exist. Re-enter
*>                      IR038 Posting & Default a/c must not be the same
*>                      IR039 Make sure that you have backed up your data
*>                      IR03A IRSUB1-31 returns
*>                      IR03B IRSUB1-32 returns
*>**
*> Changes.
*>
*>  11/7/83 vbc - Check response on correct account?,fix date vet
*>                to vet for zero day month,year < 70 & improve
*>                loop in accept post date routine.
*> 13/07/83 vbc - Clear save-sequ if updating post file.
*> 26/07/83 vbc - Rewrite date vet routines.
*> 07/12/83 vbc - Tidy up display.
*> 28/05/84 vbc - Hilite display heads.
*> 12/04/85 vbc - Check if posting to vat account direct.
*> 26/09/89 vbc - 2.53
*>                Mods for COBOL/2.
*> 09/10/89 vbc - Re-calc net amount if vat code = m & vat changed.
*> 28/12/89 vbc - Test for dflt a/c same as input a/c.
*> 22/01/09 vbc - Migration to Open/Gnu Cobol as version 3.
*> 21/02/09 vbc - Added support for environment LINES and COLUMNS as needed.
*> 24/02/09 vbc - Added change of default within postings at accept for
*>                post-date via test for F3 added from full version.
*> 07/04/09 vbc - .12 Added posting file from S.L. and P.L. as input to IRS.
*> 14/03/10 vbc - .13-5 Cleanup multi field displays to comply with standards.
*> 24/11/16 vbc - 3.02
*> 24/11/16 vbc - .16 Added RDB support using acas000, acasirsub1, 3 & 4.
*> 01/12/16 vbc - .17 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurrences of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*> 20/12/16 vbc -     All irs progs call copybook Proc-ZZ100-ACAS-IRS-Calls.
*> 17/09/17 vbc - .18 Change screen defaults at Setup-Amend-Screen-3 to show the
*>                    fixed data in place of an occurs 16 that does not work in GC.
*> 29/01/18 vbc - .19 Changed copies to use copybooks where poss.
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 10/02/18 vbc - .20 Renamed IR011-16 to IR911-16 and others.
*> 11/02/18 vbc - .21 Starting adding in support for 3 rates of Vat in postings.
*>                    WS-Vat-Rate/s.
*>                    In  Account-Input consider adding 2nd char in accept for
*>                    Vat-Rate entry ( 1 - 3 ) instead of the preset at start of
*>                    batch run??
*>                    Check Next-Post for zero and make it = 1.
*> 19/04/18 vbc - .22 Experimental to see if save/restore screens work when
*>                    processing request to display the defaults during postings
*>                    by using F1 so new code in initialization and show-default.
*> 20/04/18 vbc - .23 close NL if vat a/c's missing in Initialise-Main and remove close NL
*>                    on PL/SL posting file proc as closed at EOJ.
*>                    Init Initialise-Main used a for the vat rates is is now 3 so exits prog.
*>                    Change to use b and zeroise after - really dumb error.
*> 21/04/18 vbc - .24 With chg to wsfnctn set path of current dir so can del temp
*>                    screen save file.
*> 23/04/18 vbc - .25 Extra test with error/abort for open NL in init.
*>                    Add comment regarding usage of F1 and F3 then clear it.
*> 30/04/18 vbc - .26 Set Vat rate to 1 as default for I/O vat types.
*> 06/05/18 vbc - .27 Set up coding for support of temporary default 33 includes
*>                    changes to irswsdflt.cob to increase size from 32 to 33.
*>                    The 33rd entry is only used in THIS program as a temporary
*>                    addition and is deleted (not updating) the table.
*> 07/04/18 vbc - .28 Init. coding to support alternative data entry using F9 at
*>                    the default code request to switch to using account numbers
*>                    directly for posting of the 'to' and 'from' values and this
*>                    to be expanded to using search by account descriptions with
*>                    a list of descriptions that start with the character so far
*>                    entered. THIS WILL BE LATER ON as involves changes to the
*>                    way data is entered / accepted possibly by use of the
*>                    CBL_ Keyboard char acceptance routine/s which is a test.
*>                    THIS alternative option may start to be coded but will Not
*>                    initially be available to users until complete.
*> 13/05/18 vbc - .29 Init. code for support of temp default a/c 33
*>                    Replaced vars e for E1.
*> 31/03/23 vbc -     Manual states that F4 to search defaults based on account name
*>                    This is NOT yet coded in ANY way but the table is and
*>                    the init. load is -coded in if anything for testing code.
*>                    on COA-Search-Table. Nothing for actual search - more code
*>                    needed.   Display defaults is using F1  (and 99 at start).
*> 01/08/23 vbc - .30 Missing close acasirs1 before 2nd open in Initialise-Main
*>                    found when running in -d -g etc.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*> 05/10/25 vbc - 3.3.01 Check for postings2irs from SL/PL for auto update.
*>                       Bug using we-error for accept changed to WS-Reply
*>                       on error condition tests - clearly never happened.
*>                       NOT YET CODED.
*>**
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
*>====================
*>
 copy  "envdiv.cob".
 input-output section.
 data division.
*>=============
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(16) value "irs030 (3.3.01)".
*>
 01  filler.
     03  a               binary-char     value zero.
     03  b               binary-char     value zero.
     03  c               binary-char     value zero.
     03  d               binary-char     value zero.
     03  E1              binary-char     value zero.
     03  ws-env-lines    pic 999         value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-20-lines     binary-char unsigned value zero.
     03  ws-21-lines     binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
*>************************************************************
*>     Demo-Flag set to 1 for generation of DEMO version     *
*>                                                           *
*>   This is not in use for the O/S (Open Source versions.   *
*>===========================================================*
     03  Demo-Flag       pic 9           value zero.
         88 Demo                         value 1.
*>===========================================================*
*>    above demo flag set to 1 for demo version              *
*>************************************************************
     03  rev-flag        pic 9           value zero.
     03  menu-reply      pic 9.
     03  WS-Reply        pic x.
     03  ws-pass         pic x(4).
     03  w               pic 99.
     03  y               pic 99.
     03  ws-type         pic xx.
     03  ws-type2        pic xx          value "DR".
     03  ws-default      pic s9(7)v99    value zero.
     03  ws-vat          pic s9(7)v99    value zero.
     03  ws-batch        pic s9(7)v99    value zero.
     03  ws-def-ac       pic s9(7)v99    value zero.
     03  input-account   pic s9(5).
     03  Accept-WS-Vat.
         05  ws-Vat-code pic x.      *>  As it was & it is P,M, sp.
         05  WS-Vat-Term pic 9.      *>  Will be 1, 2 or 3 (Std, Reduced, Zero).
*>
*> New for .28 07/04/18
*>
     03  WS-Posting-Method pic 9         value zero.
         88  WS-Posting-By-Default       value zero.
         88  WS-Posting-By-Account       value 1.
*>
*>
     03  post-true       pic z(4)9.
     03  save-post       pic 9(5).
     03  save-key        pic 9(5).
     03  save-lin        pic 99.
     03  net-display     pic z(6)9.99-.
     03  vat-display     pic z(6)9.99-.
     03  display-amount  pic z(6)9.99-.
     03  display-account pic zzzz9.
     03  ws-type-display pic xx.
     03  hold-post       pic 9(5).
     03  ws-acs          pic 9(5).
     03  ws-codes        pic xx.
     03  ws-vax          pic x.
     03  vat-flag        pic 9           value zero.
     03  vat-flag-2      pic 9           value zero.
     03  ws-spaces       pic x(80)       value spaces.
     03  ws-def-name     pic x(24).
     03  ws-vat-ac       pic x(20).
     03  display-legend  pic x(16).
*>
     03  Post-Record-Cnt pic 9(5)        value zero.
     03  WS-Vat-Rates                    value zero.  *> taken from IRS system rec.
         05  WS-Vat-Rate pic 99v99   occurs 3.
         05  WS-Vat-Rate-Disp
                         pic z9.99 occurs 3.
     03  WS-Vat-Current  pic 99v99       value zero.
     03  WS-VAT-Number   pic 9           value zero.
*>
*> the following for GC and screen with *nix NOT tested with Windows
*>
 01  wScreenName             pic x(256).
 01  wInt                    binary-long.
*>
 copy "wsfnctn.cob".
 copy "irswsnl.cob"   replacing NL-Record by WS-IRSNL-Record.
 copy "irswsdflt.cob" replacing Default-Record by WS-IRS-Default-Record.
 copy "irswspost.cob".
 copy "wspost-irs.cob".
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
 *>    03  WS-IRSNL-Record       pic x.   *> acasirsub1 in use.
 *>    03  WS-IRS-Default-Record pic x.   *> acasirsub3 in use.
 *>    03  Posting-Record        pic x.   *> acasirsub4 in use.
 *>    03  WS-IRS-Posting-Record pic x.   *> acas008    in use.
     03  Final-Record          pic x.    *> Table/File not used in this program.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  date-fields.
     03  q                 pic 9.
*>
     03  days-in-month     pic x(24)  value "312831303130313130313031".
     03  filler  redefines  days-in-month.
       05  days            pic 99     occurs 12.
*>
     03  ws-work1          pic 9(5)   comp-3.
     03  ws-work2          pic 9(5)   comp-3.
     03  display-bin       pic zzzz9.
*>
 01  maps03-ws.
     03  u-date          pic x(8).
     03  filler  redefines  u-date.
       05  u-days        pic 99.
       05  filler        pic x.
       05  u-month       pic 99.
       05  filler        pic x.
       05  u-year        pic 99.
     03  u-bin           pic 9(5)     comp.
*>
 01  ws-amount-screen-display.
     03  ws-poundsd      pic 9(7).
     03  ws-period       pic x     value ".".
     03  ws-penced       pic v99.
     03  ws-signd        pic x.
 01  ws-amount-screen-accept redefines ws-amount-screen-display.
     03  ws-pound        pic 9(7).
     03  filler          pic x.
     03  ws-pence        pic v99.
     03  ws-sign         pic x.
*>
 01  ws-amount-work.
     03  amt-wk-pds      pic s9(7).
     03  amt-wk-pence    pic v99.
 01  ws-amount-ok redefines ws-amount-work.
     03  amt-ok          pic s9(7)v99.
*>
 01  ws-num-dstring.
     03  ws-nstrg        pic 9(9).
 01  ws-dstrg.
     03  ws-dstrg-9      pic 99.
*>
 01  All-My-Constants    pic 9(4).
     copy "screenio.cpy".
*>
*>  Working Storage for NL Default rec 31
*>
 01  nl31-record.
     03  nl31-key.
         05  nl31-owning   pic 9(5).
         05  nl31-sub-nominal pic 9(5).
     03  nl31-type         pic a.
     03  nl31-data.
         05  nl31-name     pic x(24).
         05  nl31-dr       pic 9(8)v99   comp.
         05  nl31-cr       pic 9(8)v99   comp.
         05  nl31-dr-last  pic 9(8)v99   comp  occurs  4.
         05  nl31-cr-last  pic 9(8)v99   comp  occurs  4.
         05  nl31-ac       pic a.
*>
*>  Working Storage for NL Default rec 32
*>
 01  nl32-record.
     03  nl32-key.
         05  nl32-owning   pic 9(5).
         05  nl32-sub-nominal pic 9(5).
     03  nl32-type         pic a.
     03  nl32-data.
         05  nl32-name     pic x(24).
         05  nl32-dr       pic 9(8)v99   comp.
         05  nl32-cr       pic 9(8)v99   comp.
         05  nl32-dr-last  pic 9(8)v99   comp  occurs  4.
         05  nl32-cr-last  pic 9(8)v99   comp  occurs  4.
         05  nl32-ac       pic a.
*>
*>  Searchable Table holding CoA with desc in lowercase and as original.
*>
 01  COA-Search-Table.
     03  CoA-Table   occurs 500
                      ascending key CoA-Desc
                      indexed       CoA-Index.
         05  CoA-Account.
             07  CoA-Own   pic 9(5).
             07  CoA-Sub   pic 9(5).
         05  CoA-Desc      pic x(24).
         05  CoA-Orig-Desc pic x(24).
 01  CoA-Count             pic 999 comp     value zero.
 01  CoA-Found-Key         pic 999 comp     value zero.
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
     03  IR030          pic x(42) value "IR030 End of listing. Hit return for Menu.".
     03  IR031          pic x(51) value "IR031 No Ledger Posting file found. Process Aborted".
     03  IR032          pic x(22) value "IR032 Invalid key 1 = ".
     03  IR033          pic x(22) value "IR033 Invalid key 2 = ".
     03  IR034          pic x(43) value "IR034 That Account now deleted!!!  Re-enter".
     03  IR035          pic x(55) value "IR035 VAT Account/s not present, Fix it. Now hit return".
     03  IR036          pic x(34) value "IR036 Amount not numeric. Re-Enter".
     03  IR037          pic x(43) value "IR037 That account does not exist. Re-enter".
     03  IR038          pic x(48) value "IR038 Posting & Default a/c must not be the same".
     03  IR039          pic x(50) value "IR039 Make sure that you have backed up your data".
     03  IR03A          pic x(24) value "IR03A IRSUB1-31 returns ".
     03  IR03B          pic x(24) value "IR03B IRSUB1-32 returns ".
*>
 linkage section.
*>---------------
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
                        Vat        by VatCode
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
 Screen Section.
*>==============
*>
 01  heading-screen.
   02                                       background-color 0 foreground-color 6.
     03  pic x(16)      from  prog-name         line  1 col  1 foreground-color 2.
     03             value "Transaction Posting"         col 31 foreground-color 1
                                                               background-color 7.
     03  pic x(8)       from  run-date                  col 73 foreground-color 2.
     03             value "Default -"           line  2 col  1 foreground-color 2.
     03  pic z9         from  w                         col 11 foreground-color 3.
     03             value "Run is - "                   col 14 foreground-color 2.
     03  pic xx         from  ws-type-display           col 23 foreground-color 3.
     03  pic x(20)      from  ws-def-name               col 50 foreground-color 3.
     03  pic z(6)9.99-  from  ws-default                col 70 foreground-color 3.
     03             value "Client "             line  3 col  1 foreground-color 2.
     03  pic x(24)      from  client                    col  8 foreground-color 3.
     03             value "End Date "                   col 32 foreground-color 2.
     03  pic x(8)       from  end-date                  col 41 foreground-color 3.
     03  pic x(20)      from  ws-vat-ac                 col 50 foreground-color 3.
     03  pic z(6)9.99-  from  ws-vat                    col 70 foreground-color 3.
     03             value "Batch Total"         line  4 col 50 foreground-color 2.
     03  pic z(6)9.99-  from  ws-batch                  col 70 foreground-color 3.
*>
 01  Display-Screen-1                                          background-color cob-color-black
                                                               foreground-color cob-color-green.
     03  pic x(16)      from  prog-name         line 1 col  1       blank screen.
     03        value "Default Accounts Display" line 1 col 27
                                                               foreground-color cob-color-white
                                                               background-color cob-color-blue
                                                                    reverse-video.
     03  pic x(8)       from run-date           line 1 col 73.
*> setup this is to display the defaults
 01  Setup-Amend-Screen-3                                      background-color cob-color-black
                                                               foreground-color cob-color-green.
     03             value "Client -"            line  3 col  1.
     03  pic x(24)      from client             line  3 col 10 foreground-color cob-color-cyan.
     03             value "Start date -"        line  3 col 39.
     03  pic x(8)       from start-date         line  3 col 52 foreground-color cob-color-cyan.
     03             value "End date -"          line  3 col 62.
     03  pic x(8)       from end-date           line  3 col 73 foreground-color cob-color-cyan.
     03             value "A/C Nos"             line  5 col  4.
     03             value "Description"         line  5 col 14.
     03             value "Code VAT   A/C Nos"  line  5 col 33.
     03             value "Description"         line  5 col 54.
     03             value "Code VAT"            line  5 col 73.
     03             value " "  erase eol        line  6 col 1.
     03             value "01 [00000]                      [AB] [C]" &
                          "17 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "02 [00000]                      [AB] [C]" &
                          "18 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "03 [00000]                      [AB] [C]" &
                          "19 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "04 [00000]                      [AB] [C]" &
                          "20 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "05 [00000]                      [AB] [C]" &
                          "21 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "06 [00000]                      [AB] [C]" &
                          "22 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "07 [00000]                      [AB] [C]" &
                          "23 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "08 [00000]                      [AB] [C]" &
                          "24 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "09 [00000]                      [AB] [C]" &
                          "25 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "10 [00000]                      [AB] [C]" &
                          "26 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "11 [00000]                      [AB] [C]" &
                          "27 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "12 [00000]                      [AB] [C]" &
                          "28 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "13 [00000]                      [AB] [C]" &
                          "29 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "14 [00000]                      [AB] [C]" &
                          "30 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "15 [00000]                      [AB] [C]" &
                          "31 [00000]                      [DE] [F"
                                                line plus 1 col 1.
     03             value "16 [00000]                      [AB] [C]" &
                          "32 [00000]                      [DE] [F"
                                                line plus 1 col 1.
*>
*> after display need to update
*>  cc4/44 = a/c-nos , vat 38/78, 33/73 code
*> ] cc80
*>
 procedure division using IRS-System-Params
                          WS-System-Record
                          File-Defs.
*>=========================================
*>
 Init-Main section.
*>*****************
*>
*> first get date & user information.
*>
     perform  Initialise-Main.
     if       a > zero                   *> Found errors in Tax/Vat accounts
              go to Main-Exit.
*>
*>  Test if postings2irs exist and recs > 0
*>
 *>    perform  ???????

*>
 Main-Loop.
     move     zero to w.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Transaction Posting"                       at 0131 with foreground-color 1 background-color 7.
     display  "Enter Run Option     -    [  ]"            at 0501 with foreground-color 2.
     display  "(<99>    Display Existing Defaults)"       at 0532 with foreground-color 2.
     display  "(<88>    Add to Existing Postings)"        at 0632 with foreground-color 2.
     display  "(<77>    Clear Existing Postings)"         at 0732 with foreground-color 2.
     display  "(<66>    Add PL or SL Postings from file)" at 0832 with foreground-color 2.
     display  "(<Return> to exit to System Menu)"         at 1032 with foreground-color 2.
*>
     accept   w at 0528 with foreground-color 3 update.
*>
 Main-Loop-Clear.
*>
*> close A/C file
*>
     if       w = zero
              perform acasirsub1-Close        *> call-irsub1
              go to Main-Exit.
*>
     if       w = 99
              perform  Show-Default.
     if       w = 77
              perform  file-init
              if   WS-Reply = "Z"
                   go to Main-Loop
              else
                   move  zero  to  next-post save-sequ
                   go to  get-default.
     if       w = 66
              move zero to save-sequ
              perform Ledger-Postings-Add.
     if       w not = 88
              go to  Main-Loop.
*>
 Get-Default.
     display  "Enter Default Number -    [  ]" at line ws-lines col 1
                                                with foreground-color 2 erase eol.
     display  "F1 to Display Defaults" at line WS-Lines col 41 with foreground-color 2.
*>
 Get-Default-1.
     accept   w  at line ws-lines col 28 with foreground-color 3.
*>
*> Save screen, show the defaults then restore the prev. screen.
*>
     if       Cob-Crt-Status = Cob-Scr-F1
              move     z"irs-temp.scr"  to wScreenName
              call     "scr_dump"    using wScreenName
                                             returning wInt
              perform  Show-Default
              call     "scr_restore" using wScreenName
                                                                                               returning wInt
              call     "CBL_DELETE_FILE" using Path-Work
              go to Get-Default.
*>
     if       w  <  1  or  >  33                *>  a/c 33 is temp default added 01/05/18
              go to  Get-Default.
*>
*>  First for test of F9 = using to / from accounts instead of the default system.
*>   THIS IS NOT YET AVAILABLE.
*>  Need to consider do a different process as a new called routine to Replace
*>   existing code which in turn is a routine
*>

 *>    if       Cob-Crt-Status = Cob-Scr-F9
 *>             set   WS-Posting-By-Default to false     *> but could be WS-Posting-By-Account to true
 *>             go to ????
 *>    end-if

*>
*> get Default A/C
*>
     if       w = 33
              display  "Def. A/C Code - [12345]" at line ws-lines col 1
                                                with foreground-color 2 erase eol
              display  "Def. Post Code - [AB]"   at line ws-lines col 31
                                                with foreground-color 2
              display  "Def. VAT Code  - [I] {I, O, N}"    at line ws-lines col 55
                                                with foreground-color 2
              accept   Def-ACS (33)   at line ws-lines col 18
                                                with foreground-color 3 update
              accept   Def-Codes (33) at line ws-lines col 49
                                                with foreground-color 3 update
              accept   Def-VAT (33)   at line ws-lines col 73
                                                with foreground-color 3 update
     end-if
*>
     move     Def-ACS (w)  to  NL-Owning.
     move     zero         to  NL-Sub-Nominal.
     perform  acasirsub1-Read-Indexed.
*>
     if       WE-Error = 2
              display IR034 at line ws-lines col 34 with  erase eol foreground-color 2
              go to Get-Default-1.
*>
     if       w = 31 or = 32                             *> > 30
          or  NL-Owning = Def-ACS (31) or Def-ACS (32)
              move 1    to vat-flag
     else
              move zero to vat-flag.
*>
     display  NL-Name at line ws-lines col 01 with erase eol foreground-color 2.
     if       DEF-Vat (w) = "N"
              display "(No VAT)    " at line ws-lines col 26 with foreground-color 2
     else
      if      Def-Vat (w) = "O"
              display "(Output VAT - Sales)" at line ws-lines col 26 with foreground-color 2
      else
              display "(Input VAT - Purchases) " at line ws-lines col 26 with foreground-color 2.
*>
     move     NL-Name  to  WS-Def-Name.
*>
 Chk-Ans.
     display  "Correct Account (Y/N)....[ ]" at line ws-lines col 51 with foreground-color 2.
     accept   WS-Reply  at line ws-lines col 77 with foreground-color 3 UPPER.
     if       WS-Reply = "N"
              go to Get-Default.
     if       WS-Reply not = "Y"
              go to Chk-Ans.
*>
 Get-Vat-Rate.
*>
*> Currently not coded for vat rates 4 & 5.
*>
     move     1 to WS-Vat-Number.               *> Default, Standard rate
     if       Def-VAT (W) = "N"
              move   zero to WS-Vat-Current
              move   3    to WS-Vat-Number      *> Default zero rate - may be
     else
              move     1 to cole col2
              move     ws-23-lines to lin lin2
              display  space at curs with erase eol
              perform  varying WS-Vat-Number  from 1 by 1 until WS-Vat-Number > 3
                       display "Rate n [99.99]  " at curs with foreground-color 2
                       add  5 cole giving col2
                       display WS-Vat-Number      at curs2 with foreground-color 2
                       add  8 cole giving col2
                       display WS-Vat-Rate-Disp (WS-Vat-Number) at
                                                     curs2 with foreground-color 2
                       add 16 to cole
              end-perform
              display  "STD Vat rate to be used (1, 2 or 3) - [ ]" at line ws-lines col 1
                                                     with foreground-color 2 erase eol
              move    1  to WS-Vat-Number
              accept  WS-Vat-Number at line ws-lines col 40
                                                     with foreground-color 3 with update
              if      WS-Vat-Number < 1 or > 3
                      go to Get-Vat-Rate
              end-if
              move  WS-Vat-Rate (WS-Vat-Number) to WS-Vat-Current
              display  space at line ws-23-lines col 1 with erase eol
     end-if.
*>
*>          WS-VAT-Current = Vat rate to use for this batch.
*>
 Get-Char.
     display  "Enter Run Characteristic [  ]" at line ws-lines col 01 with erase eol
                                                                      foreground-color 2.
     display  "('DR' or 'CR') DR if entered a/c, is debited (TO)" at line ws-lines col 31
                                                                 with foreground-color 2.
     accept   ws-type2  at line ws-lines col 27 with foreground-color 3 update.
     move     function upper-case (ws-type2) to ws-type.
     if       ws-type not = "DR" and not = "CR"
              go to  Get-Char.
     display  space at line ws-lines col 01 with erase eol.
*>
*> now reverse posting type
*>
     move     ws-type to ws-type-display.
*>
     if       ws-type = "DR"
              move "CR" to ws-type
     else
              move "DR" to ws-type.
*>
*> Set-Up totals including VAT
*>
     subtract nl-cr from nl-dr giving ws-default.
*>
     if       def-vat (w) equal "N"
              move spaces to ws-vat-ac
              move zero  to ws-vat vat-ac-def
              go to Set-Up.
     if       def-vat (w) equal "O"
              move 32 to y
     else
              move 31 to y.
*>
*> Set-Up for VAT
*>
     move     def-acs (y) to nl-owning.
     move     y to vat-ac-def.
     move     zero to nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
*>
*> Error cannot occur as tested in initialization but JIC
*>
     if       we-error = 2
              display IR035 at line ws-lines col 01 with foreground-color cob-color-red erase eol
              accept WS-Reply at line ws-lines col 74
              display space   at line ws-lines col 01 with erase eol
              go to  Main-Exit.
*>
     subtract nl-dr  from  nl-cr  giving  ws-vat.
     move     nl-name  to  ws-vat-ac.
*>
 Set-Up.
     perform  acasirsub4-Open                   *> open i-o
     move     zero  to  ws-batch save-sequ.
 Set-Up-1.
     display  space at 0101 with erase eos.
 Set-Up-2.
     perform  Heading-ScreenP.
*>
     display  "--Date--  Account"                    at 0501 with foreground-color 2.
     display  "----Narrative----     Net       VAT"  at 0543 with foreground-color 2.
     move     6  to  lin.
     move     run-date  to  post-date.
*>
     if       next-post = zero
              move 1 to Next-Post.
     move     next-post  to  post-key.
     move     def-codes (w)  to  post-code .
     move     spaces  to  post-legend.
*>
 Input-Loop.
     display  "Date      - [        ]"      at line ws-21-lines col 01 with foreground-color 2.
     display  "Account                 -[     ]" at line ws-21-lines col 41 with foreground-color 2.
     display  "Narrative - ["               at line ws-22-lines col 01 with foreground-color 2.
     display  "]"                           at line ws-22-lines col 46 with foreground-color 2.
     add      1  post-key  giving  post-true.
*>
*>    The code below is for the demo version, if DEMO-FLAG set to 1
*>      but as this version is now Open Source the flag is zero
*> WARNING:: SET to 0 for use in normal system. <<<<<<<<<<<<
*>
     if       demo   and   post-true > 50
              display space
              display "Sorry only 50 postings allowed on DEMO system" at 1220
              display SY008   AT 1426
              accept WS-Reply at 1453
              perform End-Batch thru Batch-Close
              move zero to w
              go to Main-Loop-clear.
*>
     display  "{Posting number :- "     at line ws-22-lines col 51 with foreground-color 2.
     display  post-true                 at line ws-22-lines col 70 with foreground-color 3.
     display  "}"                       at line ws-22-lines col 75 with foreground-color 2.
     display  "Amount    - [           ]" at line ws-23-lines col 1 with foreground-color 2.
     display  "VAT Code (P/M or space) - [ ]" at line ws-23-lines col 41 with foreground-color 2.
*>
     move     zeros to post-amount.
*>     move     zeros to input-account. *> so we can use the one previously input (date & desc. as well)
     display  post-date at line ws-21-lines col 14 with foreground-color 3.
*>
 Date-Inp.
     display  "F3 for new default" at line WS-Lines col 41  with foreground-color 2 erase eol.
     accept   post-date  at line ws-21-lines col 14 with foreground-color 3 update.
     if       cob-crt-status = COB-SCR-F3
              perform  End-Batch thru Batch-Close
              perform  Get-Default thru Set-Up
              perform  Set-Up-2
              move     next-post     to  post-key
              move     def-codes (w) to  post-code
              go to  Date-Inp
     end-if
     display  space at line WS-Lines col 41 with erase eol.          *> clear F3 comment.
     if       post-date = spaces
              go to End-Batch.
     perform  Date-Validate.
     if       u-bin = zero
              go to  Date-Inp.
     move     1 to cole.
     display  post-date at curs with foreground-color 3.
*>
 Account-Input.
     accept   input-account at line ws-21-lines col 67 with foreground-color 3 update.
     move     input-account to  display-account.
     if       input-account = zero
              go to  End-Batch.
     if       input-account < zero
              go to  account-input.
     if       Input-account = Def-acs (w)
              display IR038        at line ws-lines col 01 with foreground-color 2
              go to account-input
     else
              display ws-spaces at line ws-lines col 01.
     move     11 to cole.
     display  display-account at curs with foreground-color 3.
*>
     move     input-account to nl-owning.
     move     zero to nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
*>
     if       we-error = 2
              display IR037      at line ws-lines col 01 with foreground-color 2
              go to  account-input
     else
              display  ws-spaces at line ws-lines col 01.
     if       input-account = def-acs (31) or def-acs (32)
          or  vat-flag = 1
              move 1  to vat-flag-2
     else
              move zero to vat-flag-2.
*>
     display  "Amount    - [           ]"      at line ws-23-lines col 01 with foreground-color 2.
     display  "VAT Code (P/M or space) - [  ]" at line ws-23-lines col 41 with foreground-color 2.
*>
     move     18 to cole.
     display  nl-name at curs with foreground-color 3.
     display  post-legend at line ws-22-lines col 14 with foreground-color 3.
     accept   post-legend at line ws-22-lines col 14 with foreground-color 3 update.
     move     post-legend  to  display-legend.
     move     43 to cole.
     display  display-legend at curs with foreground-color 3.
*>
     move     ws-23-lines to lin2
     move     14 to col2.
     move     zero to amt-ok.
     if       vat-flag-2 = zero
              perform Accept-Money.
     if       amt-ok = zero
              go to Input-Loop.
     move     amt-ok to post-amount.
     move     post-amount to display-amount.
     move     61 to cole.
     display  display-amount at curs with foreground-color 3.
*>
     if       def-vat (w) equal "N"
              move zero to vat-amount  ws-vat
              go to Input-Tidy.
*>
 Vat-Input.
*>
*> Will need to consider accept of 2nd char for VAT rate setting (1 - 3).
*>   but slightly coded for at least in WS.
*>
     move     space to ws-vat-code.
     if       vat-flag-2 = 1
              move zero to vat-amount
              go to Vat-Input-Skip.
*>
     accept   ws-vat-code  at line ws-23-lines col 68 with foreground-color 3.
     move     function upper-case (ws-vat-code) to ws-vat-code.
     if       ws-vat-code = "P"
              perform  Net
     else
      if      ws-vat-code = "M"
              perform  Gross
      else
       if     ws-vat-code = space
              move zero to vat-amount
       else
              go to Vat-Input.
*>
 Vat-Input-Skip.
     move     post-amount  to  net-display.
     move     vat-amount   to  vat-display.
     move     61 to cole.
     display  net-display at curs with foreground-color 3.
     move     71 to cole.
     display  vat-display at curs with foreground-color 3.
*>
     move     vat-amount to amt-ok.
     move     curs to curs2.
     perform  Accept-Money2.
     if       vat-amount not = amt-ok
        and   ws-vat-code = "M"
              Add Vat-amount to Post-amount
              Subtract Amt-ok from Post-amount
              move post-amount to net-display
              move 61 to cole
              display net-display at curs with foreground-color 3.
     move     amt-ok to vat-amount.
     if       vat-amount < zero
              multiply vat-amount by -1 giving  vat-amount.
*>
     if       post-amount = zero  and
              vat-amount  = zero
              go to  Input-Loop.
*>
 Input-Tidy.
     if       ws-type = "CR" and post-amount > zero
              go to credit-tidy.
     if       ws-type = "DR" and post-amount < zero
              go to credit-tidy.
*>
*> processing for DR run
*>
     if       post-amount < zero
              move 1 to rev-flag
              multiply post-amount by -1 giving post-amount.
     move     def-acs (w) to post-dr.
     move     input-account to post-cr.
     if       rev-flag = 1
              subtract post-amount vat-amount from ws-batch.
     if       rev-flag not = 1
              add      post-amount vat-amount to ws-batch.
     move     "CR" to post-vat-side.
     add      post-amount vat-amount to ws-default.
     add      vat-amount             to ws-vat.
     add      post-amount            to nl-cr.
*>
*> now for traps
*>
     if       input-account = def-acs (w)
              subtract post-amount from ws-default.
*>
     if       def-vat (w) = "N"
              go to Input-End.
*>
     if       input-account = def-acs (y)
              add  post-amount  to  ws-vat.
*>
     go       to Input-End.
*>
 Accept-Money.
*>     move     zero to ws-poundsd amt-ok ws-penced.
     move     spaces to ws-amount-screen-accept.
*>     move     space to ws-sign.
     display  ws-amount-screen-display at curs2 with foreground-color 3.
     accept   ws-amount-screen-accept at curs2 with foreground-color 3.
     perform  Justify-Accept-Money.
     if       c > 1 or d > 1
*>     if       ws-pound not numeric
*>           or ws-pence not numeric
              display IR036 at line ws-lines col 01 with foreground-color 4
              go to Accept-Money
     else
              display "                            " at line ws-lines col 01
     end-if.
*>     move     ws-pound to amt-wk-pds.
*>     move     ws-pence to amt-wk-pence.
*>     if       ws-sign = "-"
*>              multiply -1 by amt-ok.
*>
 Accept-Money2.
     if       amt-ok negative
              move "-" to ws-sign else
              move space to ws-sign.
     move     amt-wk-pence to ws-pence.
     move     "." to ws-period.
     move     amt-wk-pds to ws-pound.
     accept   ws-amount-screen-accept at curs2 with foreground-color 3 update.
     perform  justify-Accept-Money.
     if       c > 1 or d > 1
              display IR036 at line ws-lines col 01 with foreground-color 4
              go to Accept-Money2
     else
              display "                            " at line ws-lines col 01
     end-if.
*>     move     ws-pound to amt-wk-pds.
*>     move     ws-pence to amt-wk-pence.
*>     if       ws-sign = "-"
*>              multiply -1 by amt-ok.
*>
 Justify-Accept-Money.
*>
*> Because GC has no numeric editing or justification on accept
*>      as of v1.1 beta on 16/02/09 and up to v3
*> input field 9(7).99- output 9(9)
*>
     move     zero to amt-ok c d.   *> c = neg flag,d = dec. flag,e = dig before '.'
     move     zero to ws-dstrg-9 ws-nstrg
     move     10 to b.      *> for num string 9 chars, if changed must also do below
     perform  varying a from 11 by -1 until a < 1
              if    ws-amount-screen-accept (a:1) = "-"
                and c = 1
                    move 2 to c                        *> set negative flag - twice
                    exit perform                       *> we have an error
              end-if
              if    ws-amount-screen-accept (a:1) = "."
                and d = 1
                    move 2 to d                        *> set decimal flag - twice
                    exit perform                       *> we have an error
              end-if
              if    ws-amount-screen-accept (a:1) = "-"
                    move 1 to c                        *> set negative flag
                    exit perform cycle
              end-if
              if    ws-amount-screen-accept (a:1) = "."
                    move 1 to d                        *> set decimal flag
                    subtract b from 10 giving E1    *> = 0, 1 or 2 dec. digits
                    exit perform cycle
              end-if
*>
*> Thats the allowed non numerics done
*>    below may need to test for 0 thru 9 instead
*>
              if    ws-amount-screen-accept (a:1) not numeric
                and b not = 10                  *> must be same as start value
                    move 3 to c                 *> if we have number already we can
                    exit perform                *> NOT have more
              end-if
              if    ws-amount-screen-accept (a:1) numeric
                    subtract 1 from b               *> 1st char is (10)
                    move ws-amount-screen-accept (a:1) to ws-num-dstring (b:1)
                    exit perform cycle
              end-if
     end-perform
     if       c < 2 and d < 2         *> these are errors
       if     E1 = 2
              divide ws-nstrg by 100 giving amt-ok
       else
        if    E1 = 1
              divide ws-nstrg by 10  giving amt-ok
        else
              move ws-nstrg to amt-ok
        end-if
       end-if
       if     c = 1
              multiply -1 by amt-ok
       end-if
     end-if .
*>
 Credit-Tidy.
*>
*> Processing for CR run
*>
     move     def-acs (w)  to  post-cr.
     move     input-account to  post-dr.
*>
     if       post-amount < zero
              move 1 to rev-flag
              multiply post-amount by -1 giving post-amount.
     if       rev-flag = 1
              subtract post-amount vat-amount from ws-batch.
     if       rev-flag not = 1
              add      post-amount vat-amount to   ws-batch.
     move     "DR"  to post-vat-side.
     subtract post-amount vat-amount from ws-default.
     subtract vat-amount             from ws-vat.
     add      post-amount to nl-dr.
*>
*> Now for traps
*>
     if       input-account = def-acs (w)
              add   post-amount  to  ws-default.
*>
     if       def-vat (w) = "N"
              go to  Input-End.
*>
     if       input-account = def-acs (y)
              add  post-amount  to  ws-vat.
*>
 Input-End.
     perform  Heading-ScreenP.
     perform  acasirsub1-Rewrite.                     *> Now write-out updated account
*>
*> Now write-out posting record
*>
 Input-End-1.
     if       rev-flag = 1
              multiply  post-amount  by  -1 giving  post-amount.
     if       rev-flag = 1
              multiply  vat-amount  by  -1 giving  vat-amount.
*>
     move     post-amount  to  net-display.
     move     vat-amount   to  vat-display.
     move     61 to cole.
     display  net-display at curs with foreground-color 3.
     move     71 to cole.
     display  vat-display at curs with foreground-color 3.
*>
     add      1  to  post-key.
     add      1  to  lin.
     if       rev-flag = 1
              multiply post-amount by -1 giving  post-amount.
     if       rev-flag = 1
              multiply vat-amount by -1 giving  vat-amount.
*>
     if       rev-flag = 1
              move  zero  to  rev-flag.
*>
     move     5  to  file-function.
     perform  acasirsub4.    *> write
*>
     if       lin  <  ws-20-lines  *> 20
              go to  Input-Loop.
     move     6  to  lin.
*>
 Clear-Screen.
     move     1 to cole.
     display  ws-spaces at curs.
     add      1  to  lin.
     if       lin  <  ws-20-lines  *> 20
              go to  Clear-Screen.
*>
     display  post-date       at 0601 with foreground-color 3.
     display  display-account at 0611 with foreground-color 3.
     display  nl-name         at 0618 with foreground-color 3.
     display  display-legend  at 0643 with foreground-color 3.
     display  net-display     at 0661 with foreground-color 3.
     display  vat-display     at 0671 with foreground-color 3.
*>
     move     7  to  lin.
     go       to Input-Loop.
*>
 End-Batch.
*>
*> Output totals including vat
*>
     move     def-acs (w)  to  nl-owning.
     move     zero         to  nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
*>
     if       ws-default < zero
              multiply  ws-default by -1 giving ws-default
              move ws-default to nl-cr
              move zero to nl-dr
     else
              move ws-default to nl-dr
              move zero to nl-cr.
*>
     perform  acasirsub1-Rewrite.
*>
     if       def-vat (w)  equal "N"
              go to   Batch-Close.
*>
*> Output for vat
*>
     move     def-acs (y)  to  nl-owning.
     move     zero  to  nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
*>
     if       ws-type = "DR"  and  ws-vat  >  zero
              move  ws-vat  to  nl-cr
              move  zero    to  nl-dr.
     if       ws-type = "DR"  and  ws-vat  <  .01
              move  ws-vat  to  nl-dr
              move  zero    to  nl-cr.
*>
     if       ws-type = "CR"  and  ws-vat  >  zero
              move  ws-vat  to  nl-cr
              move  zero    to  nl-dr.
     if       ws-type = "CR"  and  ws-vat  <  .01
              move  ws-vat  to  nl-dr
              move  zero    to  nl-cr.
*>
     perform  acasirsub1-Rewrite.
*>
 Batch-Close.
*>
*> Close files
*>
     perform  acasirsub4-Close.         *> Close
     move     post-key  to  next-post.  *> Now we update system rec for next-post
*>
*>  Written out by irs menu after EOJ
*>
 Batch-Close-Return.
*>
     go to    Main-Loop.
*>
 Heading-ScreenP.
*>
     display  heading-screen at 0101.
*>
 Main-Exit.
     goback.
*>
*>-------------------------------------------------
*>            Second Level Procedures
*>-------------------------------------------------
*>
*>  all below looks good. vbc 22/1/09
*>
 Input-Headings section.
*>----------------------
*>
     move     1  to  w  cole.
     move     7  to  lin.
*>
 Display-Existing.
     display  w at curs with foreground-color cob-color-green.
     add      4 curs giving curs2.
     move     def-acs (w) to ws-acs.
     display  ws-acs at curs2 with foreground-color cob-color-cyan.
     move     ws-acs to  nl-owning.
     move     zero  to  nl-sub-nominal.
     if       ws-acs not = zero
              perform  acasirsub1-Read-Indexed
              add  10 curs giving curs2
              display nl-name (1:22) at curs2 with foreground-color cob-color-cyan
     end-if
*>
*>  get code description
*>
     add      33 curs giving curs2.
     move     def-codes (w) to ws-codes.
     display  ws-codes at curs2 with foreground-color cob-color-cyan.
     add      5  to col2.
     move     def-vat (w) to ws-vax.
     display  ws-vax at curs2 with foreground-color cob-color-cyan.
     add      1 to col2.
     display  "]" at curs2 with foreground-color cob-color-green.
     add      1 to w.
     if       w > 32
              go to  Display-Existing-end.
     if       w = 17
              move 41 to cole
              move 6  to lin.
     add      1  to lin.
     go to    Display-Existing.
*>
 Display-Existing-End.
     move     1 to w  cole.
     move     7 to lin.
*>
 Main-Exit.   exit.
*>********    ****
*>
*>
 Date-Validate section.
*>---------------------
*>
*>  THESE Routines are NOT the same as the rest of ACAS -
*>    do not support other country formats.
*>  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>************************************************
*>                                               *
*>            Date Vet Section.                  *
*>            =================                  *
*>                                               *
*>    Format of date must be as follows:-        *
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
     move     zero to u-bin q.
     move     post-date to u-date.
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
              go to Main-Exit.
*>
     if       u-days > 29 and
              u-month = 2
              go to Main-Exit.
*>
     if       u-days > days (u-month) and
              u-month not = 2
              go to Main-Exit.
*>
     divide   u-year by 4 giving ws-work1.
     multiply ws-work1 by 4 giving ws-work2.
*>
     if       u-month = 2 and
              u-days > 28 and
              u-year not = ws-work2
              go to Main-Exit.
*>
     move     u-date to post-date.
*>
*>********************************************
*>                                           *
*>       date validation & conversion        *
*>       ============================        *
*>                                           *
*>                                           *
*>  requires  date input in u-date           *
*>  & returns  date as binary days since     *
*>    01/01/70  in  u-bin                    *
*>  date errors returned as u-bin equal zero *
*>                                           *
*>********************************************
*>
*>
     move     1     to  ws-work1.
     move     zero  to  ws-work2
                        u-bin.
*>
     if       u-year not = zero
              compute u-bin  = u-year * 365.
*>
     if       u-bin <   zero
              move  zero  to  u-bin
              go to  Pack-End.
*>
 Pack-Loop-1.
     if       u-year  >  ws-work2
              add  1  to  u-bin
              add  4  to  ws-work2
              go to  Pack-Loop-1.
*>
     if       u-year =  ws-work2
       and    u-month  >  2
              add  1  to  u-bin.
*>
 Pack-Loop-2.

     if       u-month  >  12
              move  zero  to  u-bin
              go to Pack-End.
     if       u-month  >  ws-work1
              add  days (ws-work1)  to  u-bin
              add  1  to  ws-work1
              go to Pack-Loop-2.
*>
     if       u-days  not  >  days (ws-work1)
              add  u-days  to  u-bin
              go to  Pack-End.
     if       u-days  = 29
        and   u-month = 2
        and   u-year  = ws-work2
              add  u-days  to   u-bin
     else
              move  zero  to u-bin.
 Main-Exit.
*>
 Pack-End.    exit.
*>********    ****
*>
 Initialise-Main    section.
*>**************************
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected   - new code for experiment
*>
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     display  space at 0101 with erase eos.
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines   to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-23-lines.
     subtract 2 from ws-lines giving ws-22-lines.
     subtract 3 from ws-lines giving ws-21-lines.
     subtract 4 from ws-lines giving ws-20-lines.
*>
*>  Set up delete file for screen save/restore.
*>
     move     spaces to Path-Work.
     string   ACAS-Path       delimited by space
              "irs-temp.scr"  delimited by size
                                 into Path-Work.
*>
     move     1 to File-Key-No.               *> 1 = Primary
*>
*> Test if the 2 vat accounts exist in defaults. if not, a non 0
*>
     move     3  to  file-function.
     perform  acasirsub3.  *>  call-irsub3.                 *> get default record
*>
*> Open A/C file
*>
     perform  acasirsub1-Open.                              *>  Open NL as I/O
     if       WE-Error not = zero
              display   IR912    at line ws-23-lines col 01 with foreground-color cob-color-red erase eol
              display   FS-Reply at line ws-23-lines col 52
              display   SY008    at line ws-lines col 01 with foreground-color cob-color-red erase eol
              accept    WS-Reply at line ws-lines col 38
              perform   acasirsub1-Close
              goback.                                       *> Cannot continue.
     move     zero to a.
*>
*> Make sure vat a/c exist
*>
     perform  varying y from 31 by 1 until y > 32
              move  def-acs (y) to nl-owning
              move  zero to nl-sub-nominal
              perform  acasirsub1-Read-Indexed
              if   we-error = 2
                   display IR035 at line ws-lines col 01 with foreground-color cob-color-red erase eol
                   accept WS-Reply at line ws-lines col 77
                   display space at line ws-lines col 01 with erase eol
                   add 1 to a
              end-if
     end-perform
     if       a > zero
              display "You will need to fix the VAT account problems before posting"
                              at 1201 with erase eos foreground-color 4
              display SY008   at 1401 with foreground-color 4
              accept WS-Reply at 1440
              perform  acasirsub1-Close
              go to Initialise-Main-Exit
     end-if.
*>
*> Get the three VAT rates into both WS tables (usage and edited display)
*>
     perform  varying b from 1 by 1 until b > 3
              move  VAT-Psent (b) to WS-Vat-Rate (b)
                                     WS-Vat-Rate-Disp (b)
     end-perform.
     move     zero to b.
*>
*>  Get CoA and store in CoA-Table for when using non default postings AND using description
*>   to search by.
*>
     perform  acasirsub1-Close.
     perform  acasirsub1-Open-Input.
     initialise COA-Search-Table.
     move     zeros to CoA-Count.
     move     zeros to CoA-Index.  *> NEEDED ?
     perform  varying CoA-Count from 1 by 1 until CoA-Count > 500  *> table size
                              or FS-Reply not = zero
              perform acasirsub1-Read-Next
              if      FS-Reply not = zero
                      exit perform
              end-if
              move    NL-Owning      to CoA-Own (CoA-Count)
              move    NL-Sub-Nominal to CoA-Sub (CoA-Count)
              move    NL-Name     to CoA-Orig-Desc  (CoA-Count)
              move    function lower-case (NL-Name)  to Coa-Desc  (CoA-Count)
     end-perform
     sort     COA-Table ascending key CoA-Desc.
*>
*>  We now have a sorted table sort by CoA-Desc(ription) as lower case so can use search all.
*>
*>
 Initialise-Main-Exit.
     exit.
*>
 Show-Default section.
*>--------------------
*>
     display  Display-Screen-1.
     display  Setup-Amend-Screen-3.
     perform  Input-Headings.
     display  ws-spaces at line ws-23-lines col 01 with erase eos.
     display  IR030 at line ws-lines col 01   with foreground-color cob-color-white.
     move     space to WS-Reply.
     accept   WS-Reply  at line ws-lines col 79.  *>   2479
*>
 main51-exit.
     exit.
*>
 file-init section.
*>-----------------
*>
     move     spaces to WS-Reply.  *> Make sure that you have backed etc
     display  IR039 at 0301 with foreground-color 4 highlight.
     display  " "    at 0401 with erase eol.
*>
*> Removed from O/S versions.
*>
*>     display  "Enter Pass-word - [****]" AT 0432 with foreground-color 2.
*>     accept   ws-pass  at 0451 with secure.
*>     if       ws-pass not = pass-word
*>              move "Z"  to  WS-Reply
*>              go to  main52-exit.
*>
*>  Open output postings file/table
*>
     move     1  to  file-function.
     move     3  to  access-type.
     perform  acasirsub4.     *> call-irsub4.
     move     2  to  file-function.
     perform  acasirsub4.     *> call-irsub4.
*>
 main52-exit.
     exit.
*>
 Net section.
*>----------
*>
*> Calculate vat from net  - THIS MAY NEED A TEST FOR ONLY NON ZERO VAT RATES
*>                           before compute but look like comes to zero ?
*>
 *>     compute  vat-amount rounded =  post-amount *  vat  /  100.
     compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.
*>
 Main-Exita.
     exit.
*>
 Gross section.
*>------------
*>
*> calculate vat from gross
*>
 *>    compute  vat-amount rounded = post-amount - (post-amount / ( (vat + 100) / 100)).
     compute  vat-amount rounded =
              post-amount - (post-amount / ( (WS-Vat-Current + 100) / 100)).
     subtract vat-amount from post-amount.
*>
 Main-Exitb.
     exit.
*>
 Ledger-Postings-Add section.
*>--------------------------
*>
*> This routine processes the posting file produced from SL & PL updating the IRS NL
*>   accounts and copies the posting record to the internal IRS one.
*>
*>  Open input file, get vat a/cs for both Sales and Purchases and hold records
*>   some code bits from irs080
*>
     perform  acas008-Open-Input.      *>    open input irs-post-file.
     if       FS-Reply not = zero
              display IR031 at 2301 with foreground-color 2
              go to main99-exit.
*>
*>   Get default record
*>
     move     3  to  file-function.
     perform  acasirsub3.    *> call-irsub3.
*>
*>   Open I-O Nominal-Ledger.
*>
 *>    perform  acasirsub1-Open.      *> IT is opened in intialise-main
*>
*> Get default input and output tax accounts via acs 31 & 32 and save them.
*>
     move     def-acs (31) to nl-owning.
     move     zero         to nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
     if       we-error not = zero
              display IR03A at 2301 with foreground-color 4 highlight
              display we-error at 2319 with foreground-color 4 highlight
              accept WS-Reply at 2340
              go to main99-exit.
     move     WS-IRSNL-Record to nl31-record.
*>
     move     def-acs (32) to nl-owning.
     move     zero         to nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
     if       we-error not = zero
              display IR03B at 2301 with foreground-color 4 highlight
              display we-error at 2319 with foreground-color 4 highlight
              accept WS-Reply at 2340
              go to main99-exit.
     move     WS-IRSNL-Record to nl32-record.
*>
*>   open    i-o post-file.
*>
     display  "Updating Nominal Ledger" at 2401 with foreground-color 2.
     perform  acasirsub4-Open.         *> call-irsub4.
*>
 Input-Loop.
     perform  acas008-Read-Next.    *>    read  irs-post-file at end
     if       FS-Reply = 10
              go to EOJ.
     add      1 to Post-Record-Cnt.
*>
*> Processing for DR
*>
     move     WS-IRS-Post-DR to  nl-owning.
     move     zero           to  nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2
              display IR032          at 2301 with foreground-color 4 highlight
              display WS-IRS-Post-DR at 2325 with foreground-color 4 highlight
              accept WS-Reply        at 2340
              go to Input-Loop.
     add      WS-IRS-Post-Amount  to  nl-dr.
     if       ws-irs-post-vat-side = "CR"
              add  WS-IRS-Vat-Amount  to  nl-dr.
*>
*>  rewrite
*>
     perform  acasirsub1-Rewrite.
*>
*> Processing for CR
*>
     move     WS-IRS-Post-CR  to  nl-owning.
     move     zero            to  nl-sub-nominal.
     perform  acasirsub1-Read-Indexed.
     if       we-error = 2
              display IR033          at 2301 with foreground-color 4 highlight
              display WS-IRS-Post-CR at 2325 with foreground-color 4 highlight
              accept WS-Reply        at 2340
              go to Input-Loop.
     add      WS-IRS-Post-Amount  to  nl-cr.
     if       WS-irs-post-vat-side = "DR"
              add  WS-IRS-Vat-Amount  to  nl-cr.
*>
     perform  acasirsub1-Rewrite.
*>
*> Now add SL/PL posting to IRS post file
*>
     move     WS-IRS-Post-Code   to post-code.
     move     WS-IRS-Post-Date   to post-date.
     move     WS-IRS-Post-CR     to post-cr.
     move     WS-IRS-Post-DR     to post-dr.
     move     WS-IRS-Post-Amount to post-amount.
     move     WS-IRS-Post-Legend to post-legend.
     move     WS-IRS-Vat-AC-Def  to vat-ac-def.
     move     WS-IRS-Post-Vat-Side to post-vat-side.
     move     WS-IRS-Vat-Amount  to vat-amount.
     move     next-post to post-key.
     add      1 to next-post.
*>
     perform  acasirsub4-Write.
     if       we-error not = zero
              display IR914 at 2301 with foreground-color 2
              display WE-Error at 2352 with foreground-color 2
              accept WS-Reply at 2355
              go to EOJ.
*>
*> Processing for VAT
*>
     if       WS-IRS-Vat-AC-Def = zero
              go to  Input-Loop.
*>
     if       WS-IRS-Vat-AC-Def = 31
         and  WS-IRS-Post-Vat-Side = "CR"
              add  WS-IRS-Vat-Amount  to  nl31-cr
     else
       if     WS-IRS-Vat-AC-Def = 31
         and  WS-IRS-Post-Vat-Side = "DR"
              add  WS-IRS-Vat-Amount  to  nl31-dr
       else
        if    WS-IRS-Vat-AC-Def = 32
          and WS-IRS-Post-Vat-Side = "CR"
              add  WS-IRS-Vat-Amount  to  nl32-cr
        else
         if   WS-IRS-Vat-AC-Def = 32
          and WS-IRS-Post-Vat-Side = "DR"
              add  WS-IRS-Vat-Amount  to  nl32-dr.
     go       to Input-Loop.
*>
 EOJ.
*>
     move     nl31-record to WS-IRSNL-Record.
     perform  acasirsub1-Rewrite.
*>
     move     nl32-record to WS-IRSNL-Record.
     perform  acasirsub1-Rewrite.
*>
 *>    perform  acasirsub1-Close.                    *> Closed at EOJ
     perform  acasirsub4-Close.
     perform  acas008-Close.
     display  space at 1201 with erase eol.
     display  "Processing Complete on " Post-Record-Cnt " records".
EOJ-q1.
     display  "Can I clear the Ledgers Posting file? [Y]" at 1401 with erase eol.
     accept   WS-Reply at 1440 with foreground-color 6 UPPER.
     if       WS-Reply not = "Y" and not = "N"
              go to EOJ-q1.
     if       WS-Reply = "Y"
 *>             open output irs-post-file
 *>             close irs-post-file.
              perform acas008-Open-Output    *>         performs a acas008-Delete-All
              perform acas008-Close.
     display  "Note counts and any messages" at 1401 with erase eol.
     accept   WS-Reply at 1430.
     display  space at 1401 with erase eol.
*>
 main99-exit.
     exit     section.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
