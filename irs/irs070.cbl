       >>source free
*>*****************************************************************
*>                                                                *
*>     P o s t  F i l e    A m e n d m e n t    P r o g r a m     *
*>                                                                *
*>*****************************************************************
 identification division.
 program-id.            irs070.
*> Author.              Cobol conversion by Vincent B Coen, FIDPM FBCS 23/10/82
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Posting Amendment Program
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
*>                      irsubp       *> Stays as a Cobol file (temp Input file only) also used in irs050.
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
*>                      None.
*>**
*> Changes.
*>
*> 11/07/83 vbc - date vet 2 vet for month/day < 1,year < 70.
*> 13/07/83 vbc - reset save-sequ if post file changed.
*> 26/07/83 vbc - rewrite date vet routine.
*>  7/12/83 vbc - tidyup display.
*> 16/03/84 vbc - detect for incorrect entry on ac-def
*> 28/05/84 vbc - hilite display heads.
*> 14/04/85 vbc - test for default 31 32 0
*> 27/09/89 vbc - 2.53
*>                Mods for cobol/2.
*> 23/01/09 vbc - Migration to Open/Gnu Cobol as version 3.
*> 21/02/09 vbc - Added support for environment LINES and COLUMNS as needed. NOT
*> 22/02/09 vbc - Renamed the program
*> 28/02/09 vbc - change test for (= Y or y) to (= Y or = y)
*> 03/12/16 vbc - 3.02
*> 03/12/16 vbc - .07 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*> 20/12/16 vbc -     All irs progs call cpybk Proc-ZZ100-ACAS-IRS-Calls.
*> 29/01/18 vbc -     Removed unused error messages from WS.
*>                    Changed copies to use copybooks where poss. I.e.,
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 10/02/18 vbc - .08 Belated version update.
*> 10/02/18 vbc -     Renamed IR011-16 to IR911-16
*> 11/02/17 vbc - .09 Changed quit of posting from zero to ESCape to allow
*>                    for posting number of zero and no it should not happen but.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*> TODO.
*> 28/02/09 vbc     I MUST RELOOK AT THIS WITH THE POSTING MODULE TO CHECK
*>                  IF THIS MODULE IS DOING THE REVERSE AND ADD CORRECTLY
*>                   AS I AM A BIT DUBIOUS
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
 data division.
 file section.
 working-storage section.
 77  prog-name           pic x(16) value "irs070 (3.3.00)".
*>
 01  filler.
     03  a               binary-char     value zero.
     03  b               binary-char     value zero.
     03  c               binary-char     value zero.
     03  d               binary-char     value zero.
     03  e               binary-char     value zero.
*>
     03  menu-reply      pic 9.
     03  ws-reply        pic x.
*>
     03  counter         pic 9(5).
     03  ws-pass         pic x(4).
     03  y               pic 99.
     03  ws-type         pic xx.
     03  ws-default      pic s9(7)v99    value zero.
     03  ws-vat          pic s9(7)v99    value zero.
     03  ws-batch        pic s9(7)v99    value zero.
     03  ws-def-ac       pic s9(7)v99    value zero.
     03  input-account   pic s9(5).
     03  ws-vat-code     pic x.
     03  save-post       pic 9(5).
     03  save-key        pic 9(5).
     03  save-lin        pic 99.
     03  net-display     pic -(6)9.99.
     03  vat-display     pic -(6)9.99.
     03  display-amount  pic z(6)9.99.
     03  display-account pic zzzz9.
     03  error-flag      pic 9.
     03  ws-def-name     pic x(24).
     03  ws-vat-ac       pic x(20).
     03  display-legend  pic x(16).
*>
 copy "wsfnctn.cob".
*>
 copy "irswsnl.cob"       replacing nl-record      by WS-IRSNL-Record.
 copy "irswsdflt.cob"     replacing Default-Record by WS-IRS-Default-Record.
 copy "irswspost.cob".
*>
 01  date-fields.
     03  q               pic 9.
*>
     03  days-in-month   pic x(24)  value "312831303130313130313031".
     03  filler  redefines  days-in-month.
         05  days        pic 99     occurs 12.
     03  ws-work1        pic 9(5)             comp-3.
     03  ws-work2        pic 9(5)             comp-3.
     03  display-bin     pic zzzz9.
*>
 01  maps03-ws.
     03  u-date          pic x(8).
     03  filler  redefines  u-date.
       05  u-days        pic 99.
       05  filler        pic x.
       05  u-month       pic 99.
       05  filler        pic x.
       05  u-year        pic 99.
     03  u-bin           pic 9(5)   comp.
*>
 01  ws-amount-screen-display.
     03  ws-poundsd      pic 9(7).
     03  ws-period       pic x     value ".".
     03  ws-penced       pic v99.
 01  ws-amount-screen-accept redefines ws-amount-screen-display.
     03  ws-pound        pic 9(7).
     03  filler          pic x.
     03  ws-pence        pic v99.
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
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
 *>    03  WS-IRSNL-Record       pic x.
 *>    03  WS-IRS-Default-Record pic x.
 *>    03  Posting-Record        pic x.
     03  Final-Record          pic x.
     03  WS-IRS-Posting-Record pic x.
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
*> Module specific  USED are None.
*>
 linkage section.
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
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
*> first get date & user information..
*>
     move     zero to save-sequ.
*>
     move     3  to  file-function.
     perform  acasirsub3.           *> Defaults - Open input, Read,  Close
*>
     move     1  to  file-function.
     move     2  to  access-type.
     perform  acasirsub1.           *> NL - open i/o
*>
     move     1  to  file-function.
     move     2  to  access-type.
     perform  acasirsub4.           *> Postings - open i/o
*>
     display  " " at 0101 with erase eos.
     display  prog-name at 0101 with foreground-color 2.
     display  "Posting Correction" at 0131 with foreground-color 1 background-color 7.
     display  run-date at 0173 with foreground-color 2.
*>
 input-loop.
*>
     display  "Number   :  [     ]" at 0501 with foreground-color 2.
     display  "(ESC to quit)" at 0525 with foreground-color 2 erase eol.
     display  "Code     :  [  ]" at 0601 with foreground-color 2.
     display  "Date     :  [        ]" at 0701 with foreground-color 2.
     display  "Debit    :  [     ]" at 0801 with foreground-color 2.
     display  "Credit   :  [     ]" at 0901 with foreground-color 2.
     display  "Net      :  [          ]" at 1001 with foreground-color 2.
     display  " " at 1101       with erase eol foreground-color 2.
     display  "Narative :  [" at 1101 with foreground-color 2.
     display  "]" AT 1147             with foreground-color 2.
     display  "VAT Type :  [  ]" at 1201     with foreground-color 2.
     display  "(31-Input/32-Output)" at 1301 with foreground-color 2.
     display  "VAT Side :  [  ]" at 1401     with foreground-color 2.
     display  "VAT      :  [          ]" AT 1501 with foreground-color 2.
     display  "Enter code of <**> to delete" AT 2201 with foreground-color 2.
     display  "Enter number or ESC to exit" AT 2301 with foreground-color 2.
     move     zero to post-key.
     accept   post-key at 0514 with foreground-color 3 update.
 *>    if       post-key = zero
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to  End-of-Amend.
*>
*> now retrieve Posting Record
*>
     move     zero  to  we-error.
     move     4  to  file-function.
     perform  acasirsub4.
*>
     if       we-error = 2
              display "Posting does not exist!" at 0542 with foreground-color 2
              go to input-loop.
*>
     display  "Reversing posting. please wait"  at 0542 with foreground-color 2.
*>
     display  post-code at 0614 with foreground-color 3.
     display  post-date at 0714 with foreground-color 3.
     display  post-dr at 0814   with foreground-color 3.
     display  post-cr at 0914   with foreground-color 3.
     move     post-amount  to  display-amount.
     display  display-amount at 1014 with foreground-color 3.
     display  post-legend at 1114    with foreground-color 3.
     display  vat-ac-def at 1214     with foreground-color 3.
     display  post-vat-side at 1414  with foreground-color 3.
     move     vat-amount  to  display-amount.
     display  display-amount at 1514 with foreground-color 3.
*>
*> now reverse the transaction
*>
*> processing for DR
*>
     move     post-dr to nl-owning.
     move     zero    to nl-sub-nominal.
     move     4       to file-function.
     perform  acasirsub1.
*>
     if       we-error equal 2
              move 1 to error-flag
              go to reverse-cr
     else
              move zero to error-flag
     end-if
     if       post-amount > zero
              add  post-amount  to  nl-cr
     else
              subtract  post-amount  from  nl-dr
     end-if
     if       post-vat-side = "CR"  and  vat-amount > 0
              add  vat-amount  to  nl-cr.
     if       post-vat-side = "CR"  and  vat-amount < 0
              subtract  vat-amount  from  nl-dr.
*>
     move     7  to  file-function.
     perform  acasirsub1.
*>
 reverse-cr.
*>
*> processing for CR
*>
     move     post-cr  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     if       we-error = 2
              move  1  to  error-flag
              go to  reverse-vat
     end-if
     if       post-amount > zero
              add  post-amount  to  nl-dr
     else
              subtract  post-amount  from  nl-cr
     end-if
     if       post-vat-side = "DR"  and  vat-amount > 0
              add  vat-amount  to  nl-dr.
*>
     if       post-vat-side = "DR"  and  vat-amount < 0
              subtract  vat-amount  from  nl-cr.
     move     7  to  file-function.
     perform  acasirsub1.
*>
 reverse-vat.
*>
*> processing for VAT
*>
     if       vat-ac-def = zero
              go to  reverse-end.
*>
     move     vat-ac-def  to  y.
     move     def-acs (y)  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     if       we-error = 2
              move  1  to  error-flag
              go to  reverse-end
     end-if
     if       post-vat-side = "CR"  and  vat-amount > 0
              add  vat-amount  to  nl-dr
     end-if
     if       post-vat-side = "DR"  and  vat-amount > 0
              add  vat-amount  to  nl-cr
     end-if
     if       post-vat-side = "CR"  and  vat-amount < 0
              add  vat-amount  to  nl-cr
     end-if
     if       post-vat-side = "DR"  and  vat-amount < 0
              add  vat-amount  to  nl-dr
     end-if
     move     7  to  file-function.
     perform  acasirsub1.
*>
 reverse-end.
*>
     display  "Correct the transaction       " at 0525 with foreground-color 2 erase eol.
*>
     display  "'**' Here, will delete transaction" at 0641 with foreground-color 4.
     accept   post-code  at 0614 with update foreground-color 3.
     if       post-code = "**"
              go to  post-delete.
     display  " " at 0641 with erase eol foreground-color 2.
 date-input.
     accept   post-date at 0714 with update foreground-color 3.
     perform  date-validate.
     if       u-bin = zero
              go to  date-input.
     accept   post-dr at 0814 with update foreground-color 3.
     accept   post-cr at 0914 with update foreground-color 3.
     move     1014 to curs2.
     move     post-amount to amt-ok.
     perform  accept-money.
     move     amt-ok to post-amount.
     accept   post-legend  at 1114 with update foreground-color 3.
 get-ac-def.
     accept   vat-ac-def at 1214 with update foreground-color 3.
     if       vat-ac-def not = zero and not = 31 and not = 32
              display "Error" at 1218 with foreground-color 4
              go to get-ac-def.
     display  "     " at 1218.
 get-vat-side.
     accept   post-vat-side at 1414 with update foreground-color 3.
     move     function upper-case (post-vat-side) to post-vat-side.
     if       post-vat-side not = "CR" and not = "DR"
              display "Error" at 1418 with foreground-color 4
              go to get-vat-side.
     display  "     " at 1418.
     move     1514 to curs2.
     move     vat-amount to amt-ok.
     perform  accept-money.
     if       amt-ok not = zero and
              vat-ac-def = zero
              display "Inconsistent" at 1525 with foreground-color 4
              go to get-ac-def.
     display  "            " at 1525.
     move     amt-ok to vat-amount.
*>
*> now test  the accounts
*>
     move     post-dr  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     if       we-error = 2
              go to  reverse-end.
*>
     move     post-cr  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     if       we-error = 2
              go to  reverse-end.
*>
     if       vat-ac-def = zero
              go to  jump-to-dr.
*>
     move     vat-ac-def  to  y.
     move     def-acs (y)  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     if       we-error = 2
              go to  reverse-end.
*>
 jump-to-dr.
*>
*> processing for DR
*>
     move     post-dr  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     add      post-amount  to  nl-dr.
     if       post-vat-side = "CR"
              add  vat-amount  to  nl-dr.
*>
     move     7  to  file-function.
     perform  acasirsub1.
*>
*> processing for CR
*>
     move     post-cr  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     add      post-amount  to  nl-cr.
     if       post-vat-side = "DR"
              add  vat-amount  to  nl-cr.
*>
     move     7  to  file-function.
     perform  acasirsub1.
*>
*> processing for vat
*>
     if       vat-ac-def = zero
              go to  rewrite-posting.
*>
     move     vat-ac-def  to  y.
     move     def-acs (y)  to  nl-owning.
     move     zero     to  nl-sub-nominal.
     move     4        to  file-function.
     perform  acasirsub1.
*>
     if       post-vat-side = "CR"
              add  vat-amount  to  nl-cr.
     if       post-vat-side = "DR"
              add  vat-amount  to  nl-dr.
*>
     move     7  to  file-function.
     perform  acasirsub1.
*>
*> now re-write posting
*>
 rewrite-posting.
*>
     move     7  to  file-function.
     perform  acasirsub4.
     go       to input-loop.
*>
 post-delete.
*>
     move     8  to  file-function.
     perform  acasirsub4.
     go       to input-loop.
*>
 End-of-Amend.
*>
     display  space.
     move     2  to  file-function.    *> Close Postings
     perform  acasirsub4.
     move     2  to  file-function.    *> Close NL
     perform  acasirsub1.
     display  "Renumber the postings (Y/N) - [ ]" at 0301 with foreground-color 2.
*>
 end-option.
*>
     accept   ws-reply at 0332 with foreground-color 6.
     move     function upper-case (ws-reply) to ws-reply.
*>
     if       ws-reply = "N"
              go to main99-exit.
*>
     if       ws-reply not = "Y"
              go to end-option.
*>
     display  "Sorting please wait." at 1331 with foreground-color 2.
*>
     move     2  to  pass-value save-sequ.
     call     "irs055" using IRS-System-Params
                             WS-System-Record
                             File-Defs.
*>
     move     zero to pass-value.
*>
     move     1  to  file-function.
     move     3  to  access-type.
     perform  acasirsub4.
*>
     move     1  to  access-type.
     call     "irsubp" using posting-record file-access File-Defs.
     move     zero  to  counter.
*>
 rewrite-loop.
*>
     move     3  to  file-function.
     call     "irsubp" using posting-record file-access File-Defs.
     if       we-error  not equal  zero
              go to  end-of-run.
*>
     add      1  to  counter.
     move     counter  to  post-key.
*>
     move     5  to  file-function.
     perform  acasirsub4.
*>
     go       to rewrite-loop.
*>
 end-of-run.
*>
     move     2  to  file-function.
     perform  acasirsub4.
     move     2  to  file-function.
     call     "irsubp" using posting-record file-access File-Defs.
*>
     add      1  post-key  giving  next-post.
*>
*> System file update done in irs at eoj
*>
 main99-exit.
     exit     program.
*>
 accept-money.
*>------------
*>
     move     amt-wk-pence to ws-pence.
     move     "." to ws-period.
     move     amt-wk-pds to ws-pound.
     accept   ws-amount-screen-accept at curs2 with update foreground-color 3.
     perform  justify-accept-money.
     if       c > 1 or d > 1
              display "Amount not numeric. Re-Enter" at 2401 with foreground-color 4
              go to accept-money
     else
              display "                            " at 2401
     end-if .
*>     move     ws-pound to amt-wk-pds.
*>     move     ws-pence to amt-wk-pence.
*>
*>
 justify-accept-money.
*>*******************
*>
*> because OC has no numeric editing or justification on accept
*>      as of v1.1 beta on 16/02/09
*> input field 9(7).99- output 9(9)
     move     zero to amt-ok c d.   *> c = neg flag,d = dec. flag,e = dig before '.'
     move     10 to b.      *> for num string 9 chars, if changed must also do below
     perform  varying a from 10 by -1 until a < 1
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
                    subtract b from 10 giving e    *> = 0, 1 or 2 dec. digits
                    exit perform cycle
              end-if
*>
*> thats the allowed non numerics done
*>    below may need to test for 0 thru 9 instead
              if    ws-amount-screen-accept (a:1) not numeric
                and b not = 10                  *> must be same as start value
                    move 3 to c                 *> if we have number already we cannot
                    exit perform                *> NOT have more
              end-if
              if    ws-amount-screen-accept (a:1) numeric
                    subtract 1 from b               *> 1st char is (10)
                    move ws-amount-screen-accept (a:1) to ws-num-dstring (b:1)
                    exit perform cycle
              end-if
     end-perform
     if       c < 2 and d < 2         *> these are errors
       if     e = 2
              divide ws-nstrg by 100 giving amt-ok
       else
        if    e = 1
              divide ws-nstrg by 10  giving amt-ok
        else
              move ws-nstrg to amt-ok
        end-if
       end-if
       if     c = 1
              multiply -1 by amt-ok
       end-if
     end-if.
*>
 date-validate section.
*>---------------------
*>
*>*****************************************************************
*>                                                                *
*>     D A T E  V A L I D A T I O N  &  C O N V E R S I O N       *
*>                                                                *
*>*****************************************************************
*>
*>************************************************
*>                                               *
*>            DATEVET SECTION                    *
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
              go to main-exit.
*>
     if       u-days > 29 and
              u-month = 2
              go to main-exit.
*>
     if       u-days > days (u-month) and
              u-month not = 2
              go to main-exit.
*>
     divide   u-year by 4 giving ws-work1.
     multiply ws-work1 by 4 giving ws-work2.
*>
     if       u-month = 2 and
              u-days > 28 and
              u-year not = ws-work2
              go  to main-exit.
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
*>    01/01/2000  in  u-bin                  *
*>  date errors returned as u-bin equal zero *
*>                                           *
*>********************************************
*>
*>
     move     1     to  ws-work1.
     move     zero  to  ws-work2.
*>
     if       u-year > 0
              compute  u-bin = u-year * 365.
*>
     if       u-bin <   zero
              move  zero  to  u-bin
              go to  pack-end.
*>
 pack-loop-1.
*>
     if       u-year > ws-work2
              add  1  to  u-bin
              add  4  to  ws-work2
              go to  pack-loop-1.
*>
     if       u-year equal   ws-work2
       and    u-month > 2
              add  1  to  u-bin.
*>
 pack-loop-2.

     if       u-month > 12
              move  zero  to  u-bin
              go to pack-end.
     if       u-month > ws-work1
              add  days (ws-work1)  to  u-bin
              add  1  to  ws-work1
              go to pack-loop-2.
*>
     if       u-days  not > days (ws-work1)
              add  u-days  to  u-bin
              go to  pack-end.
     if       u-days  = 29
        and   u-month = 2
        and   u-year  = ws-work2
              add  u-days  to   u-bin
     else
              move  zero  to u-bin.
 main-exit.
*>
 pack-end.    exit.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
