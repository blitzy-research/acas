       >>source free
*>*****************************************************************
*>                                                                *
*>    N o m i n a l  F i x  u p   P r o g r a m                   *
*>                                                                *
*>*****************************************************************
 identification division.
 program-id.            irs080.
*>
*> Author.              V.B.Coen   FIDPM FBCS
*>                      Applewood Computers.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>
*>**
*> Remarks.             NL Fixup Program
*>**
*> Version.             See Prog-Name in WS.
*>**
*> Calls.               acasirsub1  ->
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
*>                      IR980 Invalid key 1 = nn
*>                      IR981 Invalid key 2 = nn
*>                      IR982 Make sure that you have backed up your data
*>                      IR983 Clearing Nominal Ledger of totals
*>                      IR984 To continue Y or N to quit
*>                      IR985 IRSUB1-31 returns
*>                      IR986 IRSUB1-32 returns
*>
*> Un-usual Messages:  Caused by data corruptions.
*>                     Restore from last known good backup
*>                      IR985 IRSUB1-31 returns nn  - Missing NL record for default 31.
*>                      IR986 IRSUB1-32 returns nn  -   DITTO but for default 32.
*>**
*> Changes.
*>
*> 11/07/83 vbc - Date vet 2 vet for month/day < 1,year < 70.
*> 13/07/83 vbc - Reset save-sequ if post file changed.
*> 26/07/83 vbc - Rewrite date vet routine.
*> 07/12/83 vbc - Tidyup display.
*> 16/02/84 vbc - Changed to irs080.
*> 28/05/84 vbc - Hilite display heads.
*> 26/09/89 vbc - 2.53
*>                Mods for Cobol/2.
*> 23/01/09 vbc - Migration to Open/Gnu Cobol as version 3
*> 21/02/09 vbc - Added support for environment LINES and COLUMNS as needed.
*> 07/04/09 vbc - Added colour to displays & replace direct NL file
*>                processing to using irsub1.
*> 14/03/10 vbc - Cleanup multi field displays to comply with standards.
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
*> 25/12/16 vbc - .15 Extra tests for rewrite when cleaning NL.
*> 29/01/18 vbc -     Removed unused error messages.
*>                    Changed copies to use copybooks where poss. I.e.,
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 07/02/18 vbc - .16 Cleanup starting msgs with accept for Y or N.
*> 10/02/18 vbc - .17 Renamed IR011-16 to IR911-16 and others.
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
 input-output section.
 file-control.
*>
 data division.
 file section.
*>
 working-storage section.
*>-----------------------
 77  prog-name           pic x(16) value "irs080 (3.3.00)".
*>
 01  filler.
     03  ws-reply        pic x.
*>
*>     03  ws-pass         pic x(1024).   *> Not used for O/S versions.
     03  ws-Pass         pic x(4).
     03  y               pic 99.
     03  error-flag      pic 9.
     03  post-record-cnt pic 9(5)    value zero.
*>
 copy "irswsnl.cob"       replacing      nl-record by WS-IRSNL-Record.
 copy "wsfnctn.cob".
 copy "irswsdflt.cob"     replacing Default-Record by WS-IRS-Default-Record.
 copy "irswspost.cob".
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
       05  nl32-owning     pic 9(5).
       05  nl32-sub-nominal pic 9(5).
     03  nl32-type         pic a.
     03  nl32-data.
       05  nl32-name       pic x(24).
       05  nl32-dr         pic 9(8)v99   comp.
       05  nl32-cr         pic 9(8)v99   comp.
       05  nl32-dr-last    pic 9(8)v99   comp  occurs  4.
       05  nl32-cr-last    pic 9(8)v99   comp  occurs  4.
       05  nl32-ac         pic a.
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
 *>    03  WS-IRSNL-Record       pic x.
 *>    03  WS-IRS-Default-Record pic x.
 *>    03  Posting-Record        pic x.
     03  Final-Record          pic x.     *> Dummied out as not used in program.
     03  WS-IRS-Posting-Record pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide.
     03  SY008          pic x(32) value "SY008 Note message & Hit return ".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, Fs-reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, Fs-reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, Fs-reply = ".
     03  IR914          pic x(51) value "IR914 Error on irspostingMT processing, Fs-reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, Fs-reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, Fs-reply = ".
*> Module specific  USED are :  49, 50, 56, 57
     03  IR980          pic x(22) value "IR980 Invalid key 1 = ".
     03  IR981          pic x(22) value "IR981 Invalid key 2 = ".
     03  IR982          pic x(50) value "IR982 Make sure that you have backed up your data".
     03  IR983          pic x(39) value "IR983 Clearing Nominal Ledger of totals".
     03  IR984          pic x(32) value "IR984 To continue Y or N to quit".
     03  IR985          pic x(24) value "IR985 IRSUB1-31 returns ".
     03  IR986          pic x(24) value "IR986 IRSUB1-32 returns ".
*>
 linkage section.
*>***************
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
 procedure division using IRS-System-Params
                          WS-System-Record
                          File-Defs.
*>=========================================
*>
 init01       section.
*>********************
*>
*> First get date & user information..
*>
     move     zero to save-sequ post-record-cnt.
*>
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "Fixup Accounts File" at 0129 with foreground-color 1 background-color 7.
     display  run-date              at 0173  with foreground-color 2.
     display  IR982 at 0301    with foreground-color 4.
     display  IR984 at 0401    with foreground-color 4.
     accept   ws-reply at 0433.
     if       ws-reply not = "y" and not = "Y"
              exit program.
*>
     display  IR983  at 0101 with erase eos foreground-color 2.
*>
*>   Open I-O N/L.
*>
     move     1  to  file-function.
     move     2  to  access-type.
     perform  acasirsub1.
*>
 Clear-nl.
*>
*> Read next NL record
*>
     move     3 to file-function.
     perform  acasirsub1.
     if       we-error = 3
              go to Clear-end.
*> v3.02 code
     if        NL-DR = zero
          and  NL-CR = zero
               add  1 to post-record-cnt
               go   to Clear-NL
     end-if
     move     zero to nl-dr nl-cr.
*>
*> Rewrite rec
*>
     move     7 to file-function.
     perform  acasirsub1.
*>
*> New code for v3.02
*>
     if       not FS-Cobol-Files-Used
         and  WE-Error = 994
              display IR912 at 2201 with foreground-color 4
              display FS-Reply at 2252
              display "WE="    at 2255
              display WE-Error at 2258
              display "SQL="   at 2262
              display SQL-Err  at 2266
              display SQL-Msg  at 2301
              display SY008    at 2401
              accept ws-reply  at 2433
              perform acasirsub1-Close
              go to main99-exit
     end-if
     add      1 to post-record-cnt.
     go       to Clear-nl.
*>
 clear-end.
     display  "Cleared Nominal Ledger of totals" at 0201 with foreground-color 2.
     display  post-record-cnt at 0234.
     move     zero to post-record-cnt.
*>
*>   Get default record
*>
     move     3  to  file-function.
     perform  acasirsub3.
     display  "Got Default record" at 0301 with foreground-color 2.
*>
     move     def-acs (31)  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
     if       we-error not = zero
              display IR985 at 2301 with foreground-color 4 highlight
              display we-error at 2319 with foreground-color 4 highlight
              accept we-error at 2340
              stop run.
     move     WS-IRSNL-Record to nl31-record.
*>
     move     def-acs (32)  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
     if       we-error not = zero
              display IR986 at 2301 with foreground-color 4 highlight
              display we-error at 2319 with foreground-color 4 highlight
              accept we-error at 2340
              stop run.
     move     WS-IRSNL-Record to nl32-record.
*>
 repost.
*>-----
*>
*>   open    i/p post-file.
*>
     display  "Updating Nominal Ledger" at 0401 with foreground-color 2.
     move     1  to  file-function.
     move     1  to  access-type.
     perform  acasirsub4.
     if       we-error not = zero
              display "No Postings Available" at 2301 with foreground-color 2
              go to eoj.
*>
 input-loop.
*>
     move     zero  to  we-error.
     move     3  to  file-function.
     perform  acasirsub4.
     if       we-error = 3
              go to  eoj.
     add      1 to post-record-cnt.
*>
*> Processing for DR
*>
     move     post-dr  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
     if       we-error = 2
              display IR980   at 2301 with foreground-color 4 highlight
              display post-dr at 2323 with foreground-color 4 highlight
              accept we-error at 2340
              go to input-loop.
     add      post-amount  to  nl-dr.
     if       post-vat-side = "CR"
              add  vat-amount  to  nl-dr.
*>
*>  Rewrite
*>
     move     7  to  file-function.
     perform  acasirsub1.
*>
*> Processing for CR
*>
     move     post-cr  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
     if       we-error = 2
              display IR981   at 2301 with foreground-color 4 highlight
              display post-cr at 2323 with foreground-color 4 highlight
              accept we-error at 2340
              go to input-loop.
     add      post-amount  to  nl-cr.
     if       post-vat-side = "DR"
              add  vat-amount  to  nl-cr.
*>
     move     7  to  file-function.
     perform  acasirsub1.
*>
*> Processing for VAT
*>
     if       vat-ac-def = zero
              go to  input-loop.
*>
     if       vat-ac-def = 31
         and  post-vat-side = "CR"
              add  vat-amount  to  nl31-cr
     else
       if     vat-ac-def = 31
         and  post-vat-side = "DR"
              add  vat-amount  to  nl31-dr
       else
        if    vat-ac-def = 32
          and post-vat-side = "CR"
              add  vat-amount  to  nl32-cr
        else
         if   vat-ac-def = 32
          and post-vat-side = "DR"
              add  vat-amount  to  nl32-dr.
     go to    input-loop.
*>
 eoj.
*>
     move     7  to  file-function.
     move     nl31-record to WS-IRSNL-Record.
     perform  acasirsub1.
*>
     move     nl32-record to WS-IRSNL-Record.
     perform  acasirsub1.
*>
     move     2  to  file-function.
     perform  acasirsub4.
     perform  acasirsub1.
     display   " " at 0501 with erase eol.
     display  "Processing Complete on 12345 records" at 0501 with foreground-color 2.
     display  post-record-cnt at 0524 with foreground-color 2.
     display  "Note counts. messages and Hit return for menu" at 0701 with foreground-color 2.
     accept   ws-reply at 0747 with foreground-color 2.
*>
 main99-exit.
     exit     program.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
