       >>source free
*>*****************************************************************
*>                                                                *
*>                  T r i a l   B a l a n c e                     *
*>                                                                *
*>*****************************************************************
*>
 identification division.
*>***********************
*>
 program-id.            irs040.
*>
*> Author.              Cobol conversion by Vincent B Coen, FIDPM FBCS 23/10/82
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Trial Balance Display / Print.
*>**
*> Version.             See prog-name in ws.
*>**
*> Calls.               acasirsub1  ->
*>                       irsnominalMT
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
*>                      IR040 End of listing. Hit return for Menu.
*>**
*> Changes.
*> 25/03/83 vbc - Fix clear screen after display of balance 001110.
*> 25/07/83 vbc - Fix print err,preset accept data to zero.
*> 28/05/84 vbc - Hilite display heads.
*> 14/04/85 vbc - Change print to 79 chars.
*> 26/09/89 vbc - 2.53
*>                Mods for cobol/2.
*> 22/01/09 vbc - Migration to Open/Gnu Cobol as version 3
*> 15/02/09 vbc - Cosmetic bugs on accept.
*> 21/02/09 vbc - Added support for environment LINES and COLUMNS as needed.
*> 23/02/09 vbc - Rewritten code for handling Summary display & reports
*>                as original lost and was very broken. Now added into
*>                to the Open Source version.
*>                Print and Display very duplicated but left as is, as it
*>                makes it more readable than removal.
*>             >> If a count appears on the total print line at far left it
*>                means there is a logic errror. also shows for display to
*>                right of 'hit return for menu' <<<
*> 21/09/10 vbc - Added print spool.
*>                .12 fix for portrait printing
*> 02/12/16 vbc - 3.02
*>                .13 Added RDB support using acas000, acasirsub1.
*>                    RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*> 20/12/16 vbc -     All irs progs call cpybk Proc-ZZ100-ACAS-IRS-Calls.
*> 29/12/16 vbc - .14 Change performs to acasirsub1 to by para names - makes
*>                    it easier to see what the function is
*>                    (open, close, read-next).
*> 29/01/18 vbc - .15 Changed copies to use copybooks where poss. E.g.,
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 10/02/18 vbc - .16 Renamed IR011-16 to IR911-16 and others.
*> 01/05/18 vbc - .17 Change reporting to honour request to ignore zero balance
*>                    accounts same as for displays.
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
*>*******************
*>
 copy  "envdiv.cob".
*>
 input-output section.
 file-control.
*>
     select  print-file     assign "prt-1"
                            organization line sequential.
*>
 data division.
 file section.
*>
 fd  print-file.
*>
 01  print-record        pic x(80).
*>
 working-storage section.
*>
 77  prog-name           pic x(16)  value "irs040 (3.3.00)".
 copy "irsprint-spool-command-p.cob".
 01  filler.
     03  ws-env-lines    pic 999       value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-show-lines   binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-accept-lines binary-char unsigned value zero.
*>
     03  output-reply    pic x.
     03  output-reply2   pic x.
     03  ws-reply        pic x.
     03  tipe            pic x          value "D".
         88  summary          value  "S".
         88  detaile          value  "D".
     03  empty           PIC X          value space.
         88  do-print         value  "Y".
         88  nodo-print       value  "N".
     03  counter         pic 99         value zero.
     03  total-dr        pic s9(7)v99   value zero.
     03  total-cr        pic s9(7)v99   value zero.
     03  sub-dr          pic s9(7)v99   value zero.
     03  sub-cr          pic s9(7)v99   value zero.
     03  work-dr         pic s9(7)v99   value zero.
     03  work-cr         pic s9(7)v99   value zero.
     03  main-cr         pic s9(7)v99 comp value zero.
     03  main-dr         pic s9(7)v99 comp value zero.
     03  main-ac         pic 9(5)       value zero.
     03  main-name       pic x(24)      value space.
     03  ws-sub-not      pic 9(4)       value zero.
     03  rstats          pic 9          value zero.
     03  flag            pic 9          value zero.
     03  line-cnt        pic 99   comp  value 99.
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
 copy "irswsnl.cob"   replacing NL-Record by WS-IRSNL-Record.
 copy "wsfnctn.cob".
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
 *>    03  WS-IRSNL-Record       pic x.   *> acasirsub1 in use.
     03  WS-IRS-Default-Record pic x.     *> acasirsub3 not in use.
     03  Posting-Record        pic x.     *> acasirsub4 not in use.
     03  WS-IRS-Posting-Record pic x.     *> acas008    not in use.
     03  Final-Record          pic x.     *> Table/File  not used in this program.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  filler.
     03  line-1.
       05  p-user        pic x(24).
       05  filler        pic x(5)     value spaces.
       05  p-report      pic x(8).
       05  l1-a          pic x(13)    value "Trial Balance".
       05  filler        pic x(5)     value spaces.
       05  p-date        pic x(8).
       05  P-Time        pic x(6)     value spaces.
       05  filler        pic xx       value spaces.
       05  l1-b          pic x(5)     value "Page ".
       05  p-page        pic zz9.
     03  line-3.
       05  p-client      pic x(24).
       05  l3-a          pic x(17)    value "    Start Date - ".
       05  p-start       pic x(8).
       05  l3-b          pic x(22)    value "           End Date - ".
       05  p-end         pic x(8).
     03  line-4.
       05  l4-a          pic x(37)    value " Account     ----------Name----------".
       05  filler        pic x(19)    value "   Type".
       05  l4-b          pic x(24)    value "   --Debit--   --Credit-".
     03  line-5.
       05  p-account     pic bzzzz9  blank when zero.
       05  filler        pic x(6)     value spaces.
       05  p-name        pic x(24).
       05  filler        pic x(4)     value spaces.
       05  p-legend      pic x(16).
       05  p-debit       pic z(8)9.99 blank when zero.
       05  p-credit      pic z(8)9.99 blank when zero.
     03  line-6.
       05  filler        pic x(57)    value spaces.
       05  l6-a          pic x(23)    value "=========== ===========".
     03  line-7.
       05  filler.
           07  l7-errcnt pic zzzz   blank when zero.
           07  filler    pic x(37)    value spaces.
       05  l7-a          pic x(15)    value "T o t a l      ".
       05  t-debit       pic z(8)9.99.
       05  t-credit      pic z(8)9.99.
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
     03  IR040          pic x(42) value "IR040 End of listing. Hit return for Menu.".
*>
 linkage section.
*>---------------
*>
 copy "irswssystem.cob"  *> IRS param record
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
*>*****************************************
*>
 init01 section.
*>**************
*>
*> first get date & user information..
*>
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines   to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-accept-lines.
     subtract 2 from ws-lines giving ws-22-lines.
     subtract 3 from ws-lines giving ws-show-lines.
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
 run-loop.
*>--------
*>
     move     zero  to  total-dr  total-cr ws-sub-not.
     display  prog-name       at 0101 with erase eos foreground-color 2.
     display  "Trial Balance" at 0131 with foreground-color 1 background-color 7.
     display  run-date        at 0173 with foreground-color 2.
*>
     display  "Summary or Detail <S> or <D>......[ ]" AT 0501 with foreground-color 2.
     display  "Zero balances to Print (Y/N)......[ ]" at 0701 with foreground-color 2.
     display  "Press <Return> to exit"                at 0741 with foreground-color 2.
     display  "Display or Print  <D> or <P>......[ ]" at 0901 with foreground-color 2.
*>
     move     spaces to output-reply2.
     accept   output-reply2  at 0536 with auto.
     move     function upper-case (output-reply2) to tipe.
     if       tipe = space
              go to main01-exit.
     if       not summary and not detaile
              go to run-loop.
     if       summary
              move  "Summary" to p-report
     else
              move  "Detail " to p-report.
*>
 ask-zero-bal.
     move     spaces to output-reply2.
     accept   output-reply2 at 0736 with auto.
     move     function upper-case (output-reply2) to empty.
     if       empty = space
              go to main01-exit.
     if       not do-print and not nodo-print
              go to ask-zero-bal.
*>
 output-select.
     move     spaces to output-reply2.
     accept   output-reply2 at 0936 with auto.
     move     function upper-case (output-reply2) to output-reply.
     if       output-reply not = "D" and not = "P"
              go to  output-select.
     move     suser      to p-user.
     move     client     to p-client.
     move     start-date to p-start.
     move     end-date   to p-end.
     move     run-date   to p-date.
     move     zero       to main-cr main-dr main-ac ws-sub-not.
     move     spaces     to main-name.
     if       output-reply = "D"
              go to  display-tb.
     if       output-reply = "P"
              go to  print-tb.
*>
*>------------------------------------------------------
*>                      Procedures
*>------------------------------------------------------
*>
 display-tb.
 *>    move     1  to  file-function access-type.
     perform  acasirsub1-Open-Input.
     move     zero to total-cr total-dr counter.
     move     1 to p-page.
*>
 disp-head-1.
     display  line-1         at 0101 with foreground-color 2 erase eos.
     display  p-report       at 0130 with foreground-color 1 background-color 7.
     display  l1-a           at 0138 with foreground-color 1 background-color 7.
     display  line-3         at 0301 with foreground-color 3.
     display  "Start Date -" at 0329 with foreground-color 2.
     display  "End Date -"   at 0361 with foreground-color 2.
     display  line-4         at 0501 with foreground-color 2.
     display  "Enter <N> for next screen <X> to exit....[ ]"
                                at line ws-lines col 01 with foreground-color 2.
*>
 disp-head-end.
     move     6 to lin.
     move     zero to flag.
     add      1 to counter.
*>
 main-loop.
     if       we-error = 3
              go to total-display.
     perform  get-record.
     move     spaces to line-5.
     if       we-error = 3
              move zero to nl-owning nl-cr nl-dr
     end-if
     if       we-error = 3
         and  not summary
              go to total-display.
*>
     if       not summary
              go to its-not-summary.
*>
     if       nl-sub-nominal = zero       *> we have a main a/c
              perform
                   if    main-ac = zero   *> only for 1st nl record
                         exit perform
                   end-if
                   if    main-dr = main-cr and not do-print
                         exit perform
                   end-if
                   if    main-dr > main-cr
                         subtract main-cr from main-dr giving work-dr
                         move work-dr to p-debit
                         move zero to p-credit work-cr
                         add  work-dr  to  total-dr
                   else
                         subtract main-dr from main-cr giving work-cr
                         move work-cr to p-credit
                         move zero to p-debit work-dr
                         add  work-cr  to  total-cr
                   end-if
                   move  "Main" to p-legend
                   move  main-ac        to p-account
                   move  main-name      to p-name
                   move  nl-owning to main-ac
                   move  nl-name   to main-name
                   move  nl-dr     to main-dr
                   move  nl-cr     to main-cr
                   go to main-display-1
              end-perform
              move nl-owning to main-ac
              move nl-dr     to main-dr
              move nl-cr     to main-cr
              move nl-name   to main-name
              go to main-loop
     end-if
*>
     if       nl-sub-nominal not = zero
         and  nl-owning = main-ac
              add nl-dr to main-dr
              add nl-cr to main-cr
              go to main-loop.
*>
     if       nl-sub-nominal not = zero
              add nl-dr to main-dr
              add nl-cr to main-cr
              add 1 to ws-sub-not
              go to main-loop.
*>
 its-not-summary.
     if       nl-dr = nl-cr and not do-print
              go to main-loop.
*>
     if       nl-dr > nl-cr
              subtract  nl-cr from nl-dr giving work-dr
              move work-dr to p-debit
              move zero to p-credit work-cr
              add  work-dr  to  total-dr
     else
              subtract nl-dr from nl-cr giving work-cr
              move work-cr to p-credit
              move zero to p-debit work-dr
              add  work-cr  to  total-cr
     end-if
     if       nl-sub-nominal = zero
              move "Main" to p-legend
              move nl-owning to p-account
     else
              move "Sub"  to p-legend
              move nl-sub-nominal to p-account
     end-if
     move     nl-name to p-name.
*>
 main-display-1.
     move     1 to cole.
     display  line-5 at curs with foreground-color 3.
     move     zero  to  nl-dr nl-cr sub-dr sub-cr.
     if       we-error = 3
              go to  total-display.
     add      1  to  lin.
     if       lin  < ws-show-lines
              go to  main-loop.
     move     6  to  lin.
     accept   output-reply2 at line ws-lines col 43 with auto.
     move     function upper-case (output-reply2) to ws-reply.
     if       ws-reply = "X"
 *>             move 2  to  file-function
              perform  acasirsub1-Close
              go to  run-loop.
*>
 screen-clear.
     move     spaces to ws-reply.
     add      1 to counter.
     move     counter to p-page.
     perform  disp-head-1.
     go to    main-loop.
*>
 total-display.
     display  line-6 at line ws-show-lines col 01 with foreground-color 2.
     move     total-dr to t-debit.
     move     total-cr to t-credit.
     display  line-7 at line ws-22-lines col 01 with foreground-color 3.
     display  line-6 at line ws-accept-lines col 01 with foreground-color 2.
     display  " " at line ws-lines col 01 with erase eol.
 *>    display  "Press Return for menu" at line ws-lines col 01 with foreground-color 2.
     display  IR040 at line ws-lines col 01 with foreground-color 2.
     if       ws-sub-not not = zero                        *> was disp col 26
              display ws-sub-not at line ws-lines col 46 with foreground-color 3 highlight.
     accept   ws-reply at line ws-lines col 44.     *> was 23
 *>    move     2  to  file-function.
     perform  acasirsub1-Close.
     go to    run-loop.
*>
 print-tb.
     display  space at 0101 with erase eos.
     perform  print-tb-1 thru print-tb-exit.
     go to    run-loop.
*>
 print-tb-1.
     move     zero to total-cr total-dr.
     open     output  print-file.
     move     zero  to  flag  counter  rstats.
     perform  headings.
 *>    move     1  to  file-function access-type.
     perform  acasirsub1-Open-Input.
*>
 main-loop-p.
     if       we-error = 3
              go to main-end.
     perform  get-record.
     move     spaces to line-5.
     if       we-error = 3
              move zero to nl-owning nl-cr nl-dr
     end-if
     if       we-error = 3
         and  not summary
              go to main-end
     end-if
     if       not summary
              go to p-its-not-summary.
*>
     if       nl-sub-nominal = zero        *> we hame a main a/c
              perform
                   if    main-ac = zero    *> only for 1st nl record
                         exit perform
                   end-if
                   if    main-dr = main-cr and not do-print
                         exit perform
                   end-if
                   if    main-dr > main-cr
                         subtract main-cr from main-dr giving work-dr
                         move work-dr to p-debit
                         move zero to p-credit work-cr
                         add  work-dr  to  total-dr
                   else
                         subtract main-dr from main-cr giving work-cr
                         move work-cr to p-credit
                         move zero to p-debit work-dr
                         add  work-cr  to  total-cr
                   end-if
                   move  "Main" to p-legend
                   move  main-ac        to p-account
                   move  main-name      to p-name
                   move  nl-owning to main-ac
                   move  nl-name   to main-name
                   move  nl-dr     to main-dr
                   move  nl-cr     to main-cr
                   go to main-print-1
              end-perform
              move nl-owning to main-ac
              move nl-dr     to main-dr
              move nl-cr     to main-cr
              move nl-name   to main-name
              go to main-loop-p
     end-if
*>
     if       nl-sub-nominal not = zero
         and  nl-owning = main-ac
              add nl-dr to main-dr
              add nl-cr to main-cr
              go to main-loop-p.
*>
     if       nl-sub-nominal not = zero         *> this should not used
              add nl-dr to main-dr
              add nl-cr to main-cr
              add 1 to ws-sub-not               *> but just in case count usage but dont print
              go to main-loop-p.
*>
 p-its-not-summary.
     if       nl-dr = nl-cr and not do-print
              go to main-loop-p.
*>
     if       nl-dr  >  nl-cr
              subtract  nl-cr from nl-dr giving work-dr
              move  work-dr to p-debit
              move  zero to p-credit work-cr
              add   work-dr  to  total-dr
     else
              subtract  nl-dr from nl-cr giving work-cr
              move  work-cr to p-credit
              move  zero to p-debit work-dr
              add   work-cr  to  total-cr.
     if       nl-sub-nominal = zero
              move  "Main" to p-legend
              move  nl-owning to p-account
     else
              move  "Sub"  to p-legend
              move  nl-sub-nominal to p-account.
     move     nl-name to p-name.
*>
 main-print-1.
     write    print-record from line-5 after 1.
     add      1 to line-cnt.
     if       line-cnt > 75
              perform  headings.
     move     zero  to  nl-dr nl-cr sub-dr sub-cr.
     if       we-error = 3
              go to  main-end.
     go to    main-loop-p.
*>
 main-end.
     write    print-record from line-6 after 3.
     move     total-dr  to  t-debit.
     move     total-cr  to  t-credit.
     if       ws-sub-not not = zero           *> count for a logic error if none zero
              move ws-sub-not to l7-errcnt
     else
              move zero to l7-errcnt
     end-if
     write    print-record from line-7 after 1.
     write    print-record from line-6 after 1.
     close    print-file.
     call     "SYSTEM" using Print-Report.
 *>    move     2  to  file-function.
     perform  acasirsub1-Close.
*>
 print-tb-exit.
     exit.
*>
 main01-exit.
     exit     program.
*>
 headings section.
     add      1  to  counter.
     move     counter to p-page.
     if       counter = 1
              write print-record from line-1 after 1
     else
              write print-record from line-1 after page
     end-if
     write    print-record from line-3 after 2.
     write    print-record from line-4 after 2.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     6 to line-cnt.
*>
 main-exit.
     exit.
*>
 get-record section.
 *>    move     3  to  file-function.
     perform  acasirsub1-Read-Next.
*>
 main-exit.
     exit.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
