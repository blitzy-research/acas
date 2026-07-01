       >>source free
*>*************************************************************
*>                                                            *
*>              Chart  Of  Accounts  Maintenance              *
*>                                                            *
*>*************************************************************
*>
 identification          division.
*>================================
*>
*>**
      Program-Id.         gl030.
*>**
*>    Author.             GL was written by Simon Whine MBCS, on behalf of
*>                        Applewood Computers and its group of Companies.
*>                        All changes/migrations by:
*>                        Vincent B. Coen FBCS, FIDM, FIDPM.
*>                        Converted For Cis December 84,
*>                        For Applewood Computers.
*>                        Written to supplement IRS to support larger numbers for
*>                        accounts to 10 digits nominal and subnominals and money
*>                        amounts to 100M - 1 for customers requiring a
*>                        comparable? but cheaper product than Oracle financials.
*>                        Reduced down some point later in time for accnts 6
*>                        digits and reduced money amounts.
*>**
*>    Security.           Copyright (C) 1976-2026 and later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Chart of Accounts Maintenance.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called modules.     maps04.
*>                        GL030A    (Internal)
*>                        GL030B    (Internal)
*>                        GL030C    (Internal)
*>                        GL030E    (Internal)
*>                        GL030F    (Internal)
*>                        GL030G    (Internal)
*>                        acas005 ->
*>                         nominalMT
*>**
*>    Error messages used.
*>  System Wide:
*>                        SY008 Note message and hit return.
*>                        SY010 Terminal not set to =>24
*>  Module Wide:
*>                        GL031 A code for Establishment must be input
*>                        GL032 Error! Ledger Code must be not less than 1000
*>                        GL033 No Ledger File to update
*>                        GL034 Rewrite Error-01. Hit return to finish
*>                        GL035 Deletion Request Denied! Current Balance Not Zero
*>                        GL036 Ledger File Does Not Exist
*>                        GL037 Account has postings - Request rejected
*>                        GL038 Invalid! Code must be numeric or <n*>
*>                        GL039 Does not exist!
*>                        GL03A Requested account already exists
*>                        GL03B Got error on writing new GL record, reply=
*>**
*> Changes:
*> 29/01/09 vbc - Migration to Open Cobol.
*> 02/03/09 vbc - Added support for envs LINES and COLUMNS as needed.
*> 29/05/09 vbc - Support for Page-Lines instead of fixed number.
*> 07/09/10 vbc - .03 Mod lpr.
*> 18/12/11 vbc - .04 Support for dates other than UK & clean up msgs
*>                    Error msgs to GLnnn,
*>                    Support for path+filenames.
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 12/01/18 vbc - .05 Updated for v3.02 & FH & DALs.
*> 29/01/18 VBC - .06 Added alternate key with dups on ledger for ledger-name.
*>                    Remarked out in select as not used any where but could be
*>                    in alphabetic print report.  See what gets produced.
*> 20/05/18 vbc - .07 Heading lines adjusted for size of prog-name.
*> 23/05/18 vbc - .08 Displays during amend overwrites existing displayed data.
*>                    So going to take some time to fix..................
*>                    Might well be result from GC migration or ?.
*> 24/05/18 vbc - .09 gl030g (print in Name alpha order - Instead of using
*>                    alternative key for name on ledger will
*>                    create table for a/c no and Name and sort by name then
*>                    use it to get next ascending Name and read indexed a/c key.
*> 28/05/18 vbc - .10 Minor clean up in cursor placement when error msgs displayed
*>                    more may be needed.
*> 29/05/18 vbc - .11 Extra functions in Amend to support (based after selecting
*>                    a/c number -
*>                    Copy & Replace - Using F9 at Name Req, copy existing a/c info
*>                                     into a new a/c that is requested on new line.
*>                    Move           - Using F8 at Name Req. Move existing a/c to
*>                                     a new a/c deleting the original a/c, again
*>                                     with new a/c requested on new line.
*>                    USAGE: After accepting the Account/subnominal detail and
*>                           moving to Name accept
*>                            F8 or F9 do the above
*>                            Esc      Go back to a/c data to re-enter OR
*>                                     for zero quit.
*>                    Well thats the plan.
*> 30/05/18 vbc -     Renamed all warning & error msgs also in Manual.
*> 02/06/18 vbc - .12 Coding for .11 completed.
*> 04/06/18 vbc - .13 On Amend continue accept other fields by rmarking out level test
*>                    with skip to accept end & placed a little lower in code.
*> 06/06/18 vbc - .14 Start coding for import/export of CoA from a text file
*>                    same as in IRS. Helps in setting up specific types i.e.,
*>                    Limited Companies, Partnerships, Charities etc.
*> 12/11/21 vbc - .15 Re-align menu as it lost menu options after 3, hopefully now fixed.
*> 09/12/22 vbc - .16 Added para to start of section GL030H 4 GC 3.2 warning.
*> 05/06/23 vbc - .17 Change fdprint from x(132) to x(100) to clean up report size.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*> 16/11/25 vbc - 3.3.01 Added in(put)-Counter for inport/export CoA asexport giving
*>                       an error condition after last record read/written.
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
 environment             division.
*>===============================
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
*>  This is a Cobol text file that is In/Ex ported.
*>
     select  Saved-CoA      assign       Archive-Name
                            organization line sequential
                            status       fs-reply.
*>
 copy "selprint.cob".
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 fd  Saved-CoA.
 01  Export-CoA-Text.
     03  ECoA-Ledger-Key9  pic 9(8).
     03  ECoA-Ledger-Type  pic 9.
     03  ECoA-Ledger-Place pic x.
     03  ECoA-Ledger-Level pic 9.
     03  ECoA-filler       pic x.
     03  ECoA-Ledger-Name  pic x(24).
*>
 copy "fdprint.cob" replacing ==x(132)== by ==x(100)==.
*>
 working-storage section.
*>----------------------
*>
 77  prog-name           pic x(15)       value "GL030 (3.3.01)".
 copy "print-spool-command.cob".
 77  gate-sw             pic 9           value 1.  *> removed ALTER verb - obsolete.
     88  DoClear                         value 1.
     88  AskClear                        value 2.
*>
 copy "wsmaps03.cob".
 copy "glwspc.cob".
 copy "wsfnctn.cob".
 copy "wsledger.cob".
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
*>     03  WS-Ledger-Record       pic x.
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
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  work-fields.
     03  ws-reply        pic x.
     03  Ws-Menu         pic 9.
     03  Menu-Reply      pic x.
     03  ws-codes        pic x.
     03  ws-num          pic 9.
     03  line-cnt        binary-char     value zero.
     03  page-nos        binary-char     value zero.
     03  Counter         pic 9(4)        value zero.
     03  In-Counter      pic 9(4)        value zero.
     03  seek            pic x.
     03  a               pic 9.
     03  i               pic 9.
     03  xx              pic 99.
     03  y               pic 999.
     03  z               pic 99.
     03  est             pic 99.
     03  ws-ledger-desc  pic x(7).
     03  ws-place        pic x(13).
     03  Archive-Name    PIC X(32)     VALUE "glcoa-archived.txt".
*>
 *>    03  ws-env-columns  pic 999       value zero.
     03  ws-env-lines    pic 999       value zero.
     03  ws-lines        binary-char unsigned value zero.
 *>    03  ws-columns      binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
*>
*>     03  ws-show-lines   binary-char unsigned value zero.
*>     03  ws-amend-lines  binary-char unsigned value zero.
*>     03  ws-setup-lines  binary-char unsigned value zero.
*>     03  ws-accept-lines binary-char unsigned value zero.

 01  accept-terminator-array pic 9(4)   value zero.
     copy "screenio.cpy".
*>
 01  ws-Test-Date            pic x(10).
 01  ws-date-formats.
     03  ws-swap             pic xx.
     03  ws-Conv-Date        pic x(10).
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
 01  Error-Messages.
*> System Wide
     03  SY008           pic x(31) value "SY008 Note message & Hit return".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 24".
*> Module specific
     03  GL031           pic x(44) value "GL031 A code for Establishment must be input".
     03  GL032           pic x(51) value "GL032 Error! Ledger Code must be not less than 1000".
     03  GL033           pic x(30) value "GL033 No Ledger File to update".
     03  GL034           pic x(44) value "GL034 Rewrite Error-01. Hit return to finish".
     03  GL035           pic x(55) value "GL035 Deletion Request Denied! Current Balance Not Zero".
     03  GL036           pic x(32) value "GL036 Ledger File Does Not Exist".
     03  GL037           pic x(45) value "GL037 Account has postings - Request rejected".
     03  GL038           pic x(43) value "GL038 Invalid! Code must be numeric or <n*>".
     03  GL039           pic x(21) value "GL039 Does not exist!".
     03  GL03A           pic x(38) value "GL03A Requested account already exists".
     03  GL03B           pic x(50) value "GL03B Got error on writing new GL record, reply = ".
*>
 01  ledger-codes.
     03  name-test.
         05  first-char  pic x.
         05  filler      pic x(23).
     03  ledger-test     pic 9(5).
     03  ledger-check.
         05  ledger-first-four.
             07  ledger-first  pic 9.
             07  filler        pic 999.
         05  ledger-sub  pic 99.
     03  filler  redefines  ledger-check.
         05  filler      pic 9.
         05  header-1    pic 999.
         05  filler      pic 99.
     03  filler  redefines  ledger-check.
         05  filler      pic 99.
         05  header-2    pic 99.
         05  filler      pic 99.
     03  filler  redefines  ledger-check.
         05  filler      pic 999.
         05  header-3    pic 9.
         05  filler      pic 99.
     03  pc-code.
         05  pc-code1    pic x.
         05  pc-code2    pic x.
     03  numeric-key.
         05  filler      pic x(4)          value "0000".
         05  n-code      pic 9(6).
         05  n-pc        pic 99.
     03  truth           pic 9.
         88  a-true                        value  1.
         88  a-false                       value  0.
*>
     03  Save-N          pic 9(4).
     03  Save-S          pic 99.
     03  Save-H-1        pic 999.
     03  Save-H-2        pic 99.
     03  Save-H-3        pic 9.
     03  A-Test          pic x.
     03  Save-Type       pic 9.
     03  Save-Place      pic x.
     03  Save-Code       pic xx.
     03  Save-Lin        pic 99.
     03  Save-Ledger     pic 9(6).
     03  Ledger-N-2      pic 9(4)      value zero.  *> Used in zz200
     03  Ledger-S-2      pic 99        value zero.  *> Used in zz200
*>
     03  types.
         05  filler      pic x(7)      value "Header ".
         05  filler      pic x(7)      value "Detail ".
         05  filler      pic x(7)      value "Sales  ".
         05  filler      pic x(7)      value "Purch. ".
         05  filler      pic x(7)      value "Special".
     03  filler  redefines  types.
         05  ledger-desc pic x(7)       occurs  5.
*>
     03  account-placement.
       05  filler        pic x(13)     value "Direct Income".
       05  filler        pic x(13)     value "Direct Costs ".
       05  filler        pic x(13)     value "Sundry Income".
       05  filler        pic x(13)     value "Indirect Cost".
       05  filler        pic x(13)     value "Fixed Assets ".
       05  filler        pic x(13)     value "Current Asset".
       05  filler        pic x(13)     value "Current Liab.".
       05  filler        pic x(13)     value "Capital A/Cs ".
     03  filler  redefines  account-placement.
       05  place         pic x(13)      occurs  8.
*>
*>  Table for holding a/c keys and names sorted by name
*>   used by print alpha order process as Alt. key not set up.
*>
 01  WS-TBL-Ledgers                         value high-values.    *> so sorting keep unused to the end of table.
     03  WS-TBL-Group            occurs 2000.
         05  WS-TBL-Ledger pic 9(8).
         05  WS-TBL-Name   pic x(24).
*>
 01  WS-TBL-Ledgers-Size   pic s9(4)   comp value 2000.   *> as in above occurs and MUST be the same.
 01  WS-TBL-Entry-Cnt      pic s9(4)   comp value zero.
 01  WS-TBL-Sub            pic s9(4)   comp value zero.
*>
*> Hold old a/c rec when using F8 / F9.
*>
 copy "wsledger.cob"     replacing WS-Ledger-Record by Saved-Ledger-Record
                                 leading  ==Ledger==       by ==Saved-Ledger==
                                 ==Quarters==     by ==Saved-Quarters==
                                 WS-Ledger-Key    by WS-Saved-Ledger-Key
                                 WS-Ledger-Key9   by WS-Saved-Ledger-Key9
                                 WS-Ledger-Nos    by WS-Saved-Ledger-Nos.
*>
 01  print-lines.
     03  line-1.                   *> Len = 100
       05  l1-prog         pic x(15).
       05  filler          pic x(27)     value spaces.
       05  filler          pic x(17)     value "Chart of Accounts".
       05  filler          pic x(31)     value spaces.
       05  l1-date         pic x(10).
*>
     03  line-3.                   *> Len = 100
       05  l3-user         pic x(32).
       05  filler          pic x(60)     value spaces.
       05  filler          pic x(6)      value "Page -".
       05  l3-page         pic z9.
*>
     03  line-4.                   *> Len = 100
       05  filler          pic x(24)     value "----------Name----------".
       05  filler          pic x(36)     value "---Level---   Header       Detail   ".
       05  l4-filler-1     pic x(4)      value spaces.
       05  l4-filler-2     pic x(17)     value spaces.
       05  filler          pic x(19)     value "--Placement--".
*>
     03  line-5.                   *> Len = 100
       05  l5-name         pic x(24).
       05  l5-level-filler pic x(10).
       05  filler  redefines  l5-level-filler.
         07  l5-level      pic 9          occurs 10.
       05  filler          pic x(3)       value spaces.
       05  l5-header       pic zzz9.99    blank when zero.
       05  filler          pic x(7)       value spaces.
       05  l5-detail       pic zzz9.99    blank when zero.
       05  filler          pic x(6)       value spaces.
       05  l5-pc           pic b(5)z9     blank when zero.
       05  filler          pic x(10)      value spaces.
       05  l5-placement    pic x(13).
       05  filler          pic x(6)       value spaces.
*>
     03  line-6.                   *> Len = 100
       05  filler          pic x(36)     value "---Level---   Header       Detail   ".
       05  l6-filler-1     pic x(4)      value spaces.
       05  l6-filler-2     pic x(17)     value spaces.
       05  filler          pic x(43)     value "--Placement--      ----------Name----------".
*>
     03  line-7.                   *> Len = 100
       05  l7-level-filler pic x(10).
       05  filler  redefines  l7-level-filler.
         07  l7-level      pic x          occurs 10.
       05  filler          pic x(3)       value spaces.
       05  l7-header       pic zzz9.99    blank when zero.
       05  filler          pic x(7)       value spaces.
       05  l7-detail       pic zzz9.99    blank when zero.
       05  filler          pic x(6)       value spaces.
       05  l7-pc           pic b(5)z9     blank when zero.
       05  filler          pic x(10)      value spaces.
       05  l7-placement    pic x(13).
       05  filler          pic x(6)       value spaces.
       05  l7-name         pic x(24).
*>
     03  line-11.                   *> Len = 100
       05  l11-prog        pic x(15).
       05  filler          pic x(29)     value spaces.
       05  filler          pic x(14)     value "Profit Centres".
       05  filler          pic x(32)     value spaces.
       05  l11-date        pic x(10).
*>
     03  line-13.                   *> Len = 100
       05  l13-user        pic x(32).
       05  filler          pic x(60)     value spaces.
       05  filler          pic x(6)      value "Page -".
       05  l13-page        pic z9.
*>
     03  line-14.
       05  filler          pic x(36)     value "Number        Name".
*>
     03  line-15.
       05  l15-nos         pic z9.
       05  filler          pic x(10)     value spaces.
       05  l15-name        pic x(32).
*>
 01  dummy-record          pic x(128).
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  to-day                pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 init01 section.
*>*************
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
*>
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     Print-Spool-Name to PSN.
*>
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              display SY010    at 0101 with erase eos
              accept  ws-reply at 0133
              goback
     else
              move  ws-env-lines   to ws-lines
     end-if
     subtract 1 from ws-lines giving ws-23-lines.
     subtract 2 from ws-lines giving ws-22-lines.
     move     1  to File-Key-No.
*>
 Menu-Input.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Chart Of Account Utilities" at 0128 with foreground-color 2.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
     display  usera at 0301 with foreground-color 3.
*>
     display  "Select one of the following by number :- [ ] or by Function key" at 0801
                 with foreground-color 2.
*>
     move     10 to  lin.
     move     2  to  a.
*>
     if       Profit-Centres or Branches
              move  1  to  a
              perform displaya.
*>
     if       Profit-Centres    *>gl030a  Est  Opt=1
              display "Set-up or Amend Profit Centres" at curs with foreground-color 2
              add  1  to  lin.
*>
     if       Branches          *>gl030a  Est  Opt=1
              display "Set-up or Amend Branch Codes" at curs with foreground-color 2
              add  1  to  lin.
*>
      move     2  to  a.
     perform  displaya.         *> gl030b  Opt=2
     display  "Add New Accounts" at curs with foreground-color 2.
     add      1  to  lin.
*>
      move     3  to  a.
     perform  displaya.         *> gl030c  Opt=3
     display  "Amend/Delete Existing Accounts" at curs with foreground-color 2.
     add      1  to  lin.
*>
     if       index-2           *> gl030e  Opt=4  *> don't need the test as not using alt keys
              move  4  to  a
              perform displaya
              display "Print Alphabetic List" at curs with foreground-color 2
              add 1  to  lin.
*>
     move  5  to  a
     perform  displaya.         *> gl030f  Opt=5
     display  "Display Chart of Accounts" at curs with foreground-color 2.
     add      1  to  lin.
*>
     move  6  to  a
     perform  displaya.         *>         Opt=6
     display  "Print Chart of Accounts" at curs  with foreground-color 2.
     add      1  to  lin.
*>
     if       Profit-Centres     *> gl030g  PC OR Branches    Opt=7
               move  7  to  a
              perform displaya
              display "Print Report on Profit Centres" at curs with foreground-color 2
              add   1 to lin.
*>
     if       Branches
               move  7  to  a
              perform displaya
              display "Print Report on Branch Codes" at curs with foreground-color 2.
*>
     add      1  to  lin.
*>
     move  8  to  a
     perform  displaya.        *> gl030??   Import   opt=8
     display  "Import/Export Chart of Accounts from a Text file" at curs with foreground-color 2.
*>
     add      3  to  lin
     move     9  to  a.
*>
     perform  displaya.
     display  "Exit to system menu" at curs with foreground-color 2.
*>
     accept   ws-menu at 0843  with foreground-color 6 auto.
*>
     if       ws-menu = 9
           or Cob-Crt-Status = Cob-Scr-Esc
              go to  menu-exit.
*>
 *>    if       p-c = space           *> WHY ON EARTH IS THIS DONE ????
 *>             add  1  to  ws-menu.
*>
     if       ws-menu = 1         *> PC setup or Branch setup
           or Cob-Crt-Status = Cob-Scr-F1
              perform gl030a
              go to Menu-Input.
     if       ws-menu = 2         *> CoA set up
           or Cob-Crt-Status = Cob-Scr-F2
              perform gl030b
              go to Menu-Input.
     if       ws-menu = 3         *> Update CoA
           or Cob-Crt-Status = Cob-Scr-F3
              perform gl030c
              go to Menu-Input.
 *>    if       not  index-2
 *>             add  1  to  ws-menu.
     if       ws-menu = 4         *> Alpha listing
           or Cob-Crt-Status = Cob-Scr-F4
              perform gl030e
              go to Menu-Input.
     if       ws-menu = 5  or  = 6
           or Cob-Crt-Status = Cob-Scr-F5 or Cob-Scr-F6
              perform gl030f
              go to Menu-Input.
*>
     if       ws-menu = 7         *> Print PC or Branches
           or Cob-Crt-Status = Cob-Scr-F7
              perform gl030g.
     if       ws-menu = 8
           or Cob-Crt-Status = Cob-Scr-F8
              perform gl030h.
*>
     go       to Menu-Input.
*>
 menu-exit.
     goback.
*>
 displaya.
     move     1 to cole.
     display  "(" at curs with foreground-color 2.
     move     2 to cole.
     display  a at curs with foreground-color 2.
     move     3 to cole.
     display  ")" at curs with foreground-color 2.
     move     6 to cole.
*>
 gl030a section.       *> Set up Branches or PC (1)
*>*************
*>
 main.
     perform  GL-Nominal-Open-Input.          *> open input ledger-file.
     if       fs-reply not = zero
              perform  GL-Nominal-Open-Output      *>  open  output  ledger-file
              initialise WS-Ledger-Record with filler
              move low-values to ledger-name
              move  999999 to  WS-Ledger-nos
              move  99     to  ledger-pc
              move zeros to ledger-type Ledger-Place ledger-level
                   ledger-balance ledger-last ledger-q1 ledger-q2
                   ledger-q3 ledger-q4
              perform  GL-Nominal-Write.      *> write WS-Ledger-Record.
*>
 main-continue.
     perform  GL-Nominal-Close.               *> close ledger-file.
     perform  GL-Nominal-Open.                *> open i-o ledger-file.
*>
     move     999999 to  WS-Ledger-nos.
     move     zero   to  ledger-pc.
*>
     perform  GL-Nominal-Read-Indexed.   *> read ledger-file  record invalid  key
     if       fs-reply = 21
              move     255  to  we-error.
*>
     if       we-error = 255
              move  spaces  to  p-c-Branches
     else
              move  WS-Ledger-Record  to  p-c-Branches.
*>
     move     999999  to  pc-ledg.
     move     zero    to  pc-pc est.
*>
     set      pc  to  1.
     search   p-b-codes
              when p-b-codes (pc) = "E"  set est to pc.
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
*>
     if       Profit-Centres
              display "Set-Up for Profit Centres" at 0127 with foreground-color 2
      else
              display "Set-Up for Branches" at 0130 with foreground-color 2.
*>
 Est-Input.
     display  "Establishment Code :- [  ]" at 0401  with foreground-color 2.
     display  est at 0424 with foreground-color 2.
     accept   est at 0424 with foreground-color 3 update.
*>
     if       est = zero
           or Cob-Crt-Status = Cob-Scr-Esc
              display GL031 at 0501 with foreground-color 2
              go to Est-Input.
*>
     move     "E" to p-b-codes (est).
     display  space at 0501 with erase eol.
*>
 re-input.
     move     7  to  lin.
     move     1  to  cole y.
*>
 Loop.
     move     curs to curs2.
     display  y at curs2 with foreground-color 2.
     add      3 to col2.
     display  ". [" at curs2 with foreground-color 2.
     add      3 to col2.
     move     p-b-codes (y) to ws-codes.
     display  ws-codes at curs2 with foreground-color 3.
     add      1 to col2.
     display  "]" at curs2 with foreground-color 2.
     add      1  to  lin.
     add      1  to  y
     if       lin  <  ws-23-lines  and  y  <  100
              go to  Loop.
     if       y  <  100
              move  7  to  lin
              add  11  to  cole
              go to  Loop.
*>
     move     7  to  lin  cole.
     move     1  to  y.
*>
     display  "Enter <Y> to select the code. Space to de-select" &
              " the code.<Q> to finish" at line ws-23-lines col 1  with foreground-color 2.
*>
 Loop-2.
     if       p-b-codes (y) = "E"
              go to  Loop-2-return.
*>
 p-c-b-accept.
     move     p-b-codes (y) to ws-codes.
     accept   ws-codes at curs with foreground-color 3 update.
     move     function upper-case (ws-codes) to ws-codes.
     move     ws-codes to p-b-codes (y).
     if       ws-codes = "Q"
              move  space  to  p-b-codes (y)
              go to  p-c-b-end.
     if       p-b-codes (y) = space or = "Y"
              next sentence
       else
              go to  p-c-b-accept.
*>
 Loop-2-return.
     add      1  to  lin.
     add      1  to  y
     if       lin  <  ws-23-lines and  y  <  100
              go to  Loop-2.
     if       y  <  100
              move  7  to  lin
              add  11  to cole
              go to  Loop-2.
*>
 p-c-b-end.
     display  space at line ws-23-lines col 01 with erase eol.
     display  "Details OK to save ? (Y/N) :- [Y]" at line ws-23-lines col 01 with foreground-color 2.
     move     "Y"  to  ws-reply.
     accept   ws-reply at line ws-23-lines col 32 with foreground-color 6 update.
*>
     if       ws-reply = "N" or "n"
              go to  re-input.
*>
     move     spaces  to  WS-Ledger-Record.
     string   p-c-Branches  delimited  by size
              into  WS-Ledger-Record.
*>
     if       we-error = 255
              perform   write-ledger
     else
              perform   rewrite-ledger.
*>
     move     zero  to  we-error.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
*>
     if       Profit-Centres
              display "Name the Profit Centres" at 0128 with foreground-color 2
     else
              display "Name the Branches" at 0131 with foreground-color 2.
*>
     move     4  to  lin.
     move     1  to  y.
     move     zero to ledger-pc  ledger-type ledger-balance
                      ledger-last ledger-q1 ledger-q2 ledger-q3
                      ledger-q4.
*>
     move     space  to  Ledger-Place.
*>
 Loop-3.
     if       p-b-codes (y)  = space
              go to  Loop-3-return.
*>
     move     y  to  z.
     move     999999 to  WS-Ledger-Nos.
     move     z      to  ledger-pc.
*>
     perform  GL-Nominal-Read-Indexed.       *> read ledger-file  record  invalid key
     if       fs-reply = 21
              move  255  to  we-error.
*>
     if       we-error = 255
              move  spaces  to  ledger-name.
*>
 Loop-3-back.
     move     1 to cole.
     display  "Code - " at curs with foreground-color 2.
     move     8 to cole.
     display  y at curs with foreground-color 2.
     move     11 to cole.
     display  " Name :- [" at curs with foreground-color 2.
     move     45 to cole.
     display  "]" at curs with foreground-color 2.
     move     21 to cole.
     display  ledger-name at curs with foreground-color 2.
     accept   ledger-name at curs with foreground-color 3 update.
*>
     if       ledger-name = "QUIT" OR = "quit"
        or    cob-crt-status = cob-scr-esc
              go to  Loop-3-end.
*>
     if       we-error = 255
              and  ledger-name = space
              go to  Loop-3-back.
*>
     if       we-error = 255
              perform   write-ledger
     else
              perform   rewrite-ledger.
*>
     move     zero  to  we-error.
     add      1  to  lin.
*>
 Loop-3-return.
     add      1  to  y.
     if       y  >  99
              go to  Loop-3-end.
*>
     if       lin  <  ws-22-lines
              go to  Loop-3.
*>
     move     4  to  lin.
     move     1 to cole.
*>
 Loop-3-clear.
     display  space at curs with erase eol.
     add      1  to  lin.
     if       lin  <  ws-22-lines
              go to  Loop-3-clear.
*>
     move     4  to  lin.
     go       to Loop-3.
*>
 write-ledger.
     perform  GL-Nominal-Write.       *>  write WS-Ledger-Record.
*>
 rewrite-ledger.
     perform  GL-Nominal-Rewrite.     *> rewrite WS-Ledger-Record.
*>
 Loop-3-end.
     perform  GL-Nominal-Close.       *> close ledger-file.
*>
 main-exit.   exit section.
*>********    ****
*>
 gl030b section.    *> CoA set up for PC, Branch or none.
*>*************
*>
     perform  GL-Nominal-Open-Input.      *> open input ledger-file.
     if       fs-reply not = zero
              perform main in gl030a.
     perform  GL-Nominal-Close.           *> close ledger-file.
     perform  GL-Nominal-Open.            *> open i-o ledger-file.
*>
     if       not  Profit-Centres
          and not  Branches
              go to  by-pass-pc.
*>
     move     999999 to  WS-Ledger-Nos.
     move     zero   to  ledger-pc.
*>
     perform  GL-Nominal-Read-Indexed.      *> read ledger-file  record invalid  key
     if       fs-reply = 21
              move     255  to  we-error.
*>
     if       we-error = 255
              move  spaces  to  p-c-Branches
     else
              move  WS-Ledger-Record  to  p-c-Branches.
*>
     move     999999  to  pc-ledg.
     move     zero    to  pc-pc est.
*>
     set      pc  to  1.
     search   p-b-codes when  p-b-codes (pc)  =  "E"  set   est  to  pc.
*>
 by-pass-pc.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  to-day at 0171 with foreground-color 2.
*>
 get-input.
     display  "Chart of Accounts Set-Up" at 0129  with foreground-color 2.
     display  "Ledger    Sub" at 0401 with foreground-color 2.
*>
     if       Profit-Centres
              display "P/C" at 0417 with foreground-color 2.
     if       Branches
              display "Branch" at 0415 with foreground-color 2.
     display  "-----------Name-----------  Type  Placement  Level" at 0423 with foreground-color 2.
     move     6  to  lin.
*>
 Loop.
     move     1 to cole.
     display  "[    ]   [  ]" at curs with foreground-color 2.
*>
     if       Profit-Centres  or  Branches
              move 16 to cole
              display "[  ]" at curs with foreground-color 2.
*>
     move     23 to cole.
     display  "[" at curs with foreground-color 2.
     move     48 to cole.
     display  "]  [ ]      [ ]      [ ]" at curs with foreground-color 2.
*>
     move     zero  to  ledger-n ledger-s.
*>
 Accept-Ledger.
     move     2 to cole.
     accept   ledger-n at curs with foreground-color 3 update.
     if       ledger-n = zero
           or Cob-Crt-Status = Cob-Scr-Esc
              go to  main-end.
*>
     move     curs to curs2.
     add      1 to lin2.
     move     1 to col2.
     if       ledger-n  <  1000
              display GL032 at curs2  with foreground-color 2
              go to  Accept-Ledger.
*>
     display  space at curs2 with erase eol.
*>
     move     11 to cole.
     accept   ledger-s at curs with foreground-color 3 update.
*>
     move     WS-Ledger-Nos  to  ledger-check.
     if       ledger-first = sales-range
        or    purchase-range
              display "Invalid start number!" at curs2 with foreground-color 2 erase eol
              go to  Accept-Ledger.
*>
     if       ledger-first-four = "9999"
              display "<9999>  Is reserved!" at curs2 with foreground-color 2 erase eol
              go to  Accept-Ledger.
*>
 accept-pc.
     if       not Profit-Centres and not Branches
              move  zero  to  ledger-pc
              go to  accept-name.
*>
     move     spaces  to  pc-code.
     move     17 to cole.
     accept   pc-code at curs with foreground-color 2 update.
     perform  PC-Code-Check thru PC-Code-Check-exit.
*>
     if       a-false
              move 17 to col2
              display "Invalid! Code must be numeric or <n*>." at curs2 with foreground-color 2 erase eol
              go to  accept-pc.
*>
 accept-name.
     display  space at curs2 with erase eol.
     move     24 to cole.
     move     spaces to ledger-name.
     accept   ledger-name at curs with foreground-color 3 update.
*>
 accept-type.
     if       ledger-sub  not = zero
              go to  accept-end.
*>
     move     52 to cole.
     move     zero to ledger-type.
 *>    display  "0" at curs with foreground-color 2.
     accept   ledger-type at curs with foreground-color 3 update.
*>
     if       ledger-type  not = zero  and  1  and  9
              move 52 to col2
              display "Invalid type! [0,1 & 9]" at curs2 with foreground-color 2 erase eol
              go to  accept-type.
     display  space at curs2 with erase eol.
*>
 accept-placement.
     move     61 to cole.
     display  space at curs.
*>
     if       ledger-type  not = zero
              go to  accept-end.
*>
     move     space to ws-reply.
     accept   ws-reply at curs with foreground-color 3 update.
     move     function upper-case (ws-reply) to Ledger-Place.
     if       Ledger-Place  <  "A"  or  >  "Z"
              move 61 to col2
              display "Invalid Placement! [A - Z]" at curs2 with foreground-color 2 erase eol
              go to  accept-placement.
*>
     if       revenue-only  and  Ledger-Place >  "N"
       and    pc-code  not = "00"
              move 61 to col2
              display "PC/BR, Revenue only [A - N]"  at curs2 with foreground-color 2
              go to  Accept-Ledger.
*>
 accept-header.
     move     zero  to  ledger-level.
*>
     move     70 to cole col2.
 *>    display  space at curs.
     accept   ledger-level at curs with foreground-color 3 update.
*>
     if       ledger-level  <  1  or  >  4
              display "Invalid! [1 - 4]" at curs2 with foreground-color 2 erase eol
              go to  accept-header.
*>
 accept-end.
     move     zero  to  ledger-balance  ledger-last
                        ledger-q1       ledger-q2
                        ledger-q3       ledger-q4.
*>
     if       ledger-s  not = zero
              move  ledger-s  to  save-s
              perform  detail-check
       else
              perform  header-check.
*>
     move     52 to cole.
     display  ledger-type at curs with foreground-color 2.
     move     70 to cole.
     display  ledger-level at curs with foreground-color 2.
*>
     if       a-true
              go to  Accept-Ledger
       else
              go to  Loop-end.
*>
 detail-check.
     move     zero  to  ledger-sub.
     move     "D"  to  a-test.
*>
     perform  ledger-read.
*>
     move     space to  a-test.
     move     save-s  to  ledger-sub  ledger-s.
*>
     if       a-false
              move 1 to col2
              display "INVALID! Header Missing '1'" at curs2 with foreground-color 2 with erase eol
              move  1  to  truth
       else
              perform  ledger-read.
*>
     if       ledger-type  not = 9
              move  1  to  ledger-type.
*>
     move     zero  to  ledger-level.
*>
 header-check.
     if       header-1 = 0
              perform   ledger-read
              move      1  to  ledger-level.
*>
     if       header-1  not = 0
       and    header-2 = 0
              move      2  to  ledger-level
              move      header-1  to  save-h-1
              move      zero      to  header-1
              perform   ledger-read
              move      save-h-1  to  header-1
              if        a-true
                        perform  ledger-read
                 else
                        move 1 to col2
                        display "INVALID! Header Missing '2'" at curs2 with foreground-color 2 with erase eol
                        move  1  to  truth.
*>
     if       header-2  not = 0
       and    header-3 = 0
              move      3  to  ledger-level
              move      header-2  to  save-h-2
              move      zero      to  header-2
              perform   ledger-read
              move      save-h-2  to  header-2
              if        a-true
                        perform  ledger-read
                   else
                        move 1 to col2
                        display "INVALID! Header Missing '3'" at curs2 with foreground-color 2 with erase eol
                        move  1  to  truth.
*>
     if       header-3  not = 0
              move      4  to  ledger-level
              move      header-3  to  save-h-3
              move      zero      to  header-3
              perform   ledger-read
              move      save-h-3  to  header-3
              if        a-true
                        perform  ledger-read
               else
                        move 1 to col2
                        display "INVALID! Header Missing '4'" at curs2 with foreground-color 2 with erase eol
                        move  1  to  truth.
*>
 Loop-end.
     if       pc-code2 = "*"
              go to  multi-add.
*>
     move     pc-code  to  y.
     perform  ledger-write.
     go       to addition-end.
*>
 multi-add.
     move     zero  to  ledger-pc  y.
*>
     if       pc-code1 = "*"
              move  1  to  y
              perform  Loop-add  99  times
              go to  addition-end.
*>
     move     pc-code1  to  y.
     multiply y  by  10  giving  y.
*>
     if       y  >  0
              perform  Loop-add  10  times
       else
              add  1  to  y
              perform  Loop-add  9   times.
*>
     go       to addition-end.
*>
 Loop-add.
     if       p-b-codes (y) = "E"  or  "Y"
              perform  ledger-write.
*>
     add      1  to  y.
*>
 addition-end.
     move     zero  to  y.
     perform  ledger-write.
*>
     add      1 to  lin.
     move     1 to cole.
     display  space at curs with erase eol.
     display  space at line ws-23-lines col 01 with erase eol.
*>
     if       lin  <  ws-22-lines
              go to  Loop.
*>
     move     6  to  lin.
     move     1 to cole.
*>
 screen-clear.
     display  space at curs with erase eol.
     add      1  to  lin.
*>
     if       lin  <  ws-22-lines
              go to  screen-clear
      else
              move  6  to  lin
              go to  Loop.
*>
 main-end.
     perform  GL-Nominal-Close.     *> close ledger-file.
*>
 main-exit.   exit section.
*>********    ****
*>
 ledger-read.
*>**********
*>
*> Set status false initialy. If record exists set to true.
*>
     move     zero  to  truth.
     move     ledger-check  to  WS-Ledger-Nos.
     move     WS-Ledger-Nos  to  n-code.
*>
     if       pc-code2 = "*"
              move     "00"  to  n-pc
              move     "00"  to  ledger-pc
     else
              move     pc-code     to  n-pc  ledger-pc.

     move     WS-Ledger-Record  to  dummy-record.
     move     zero  to  we-error.
*>
     perform  GL-Nominal-Read-Indexed.      *> read ledger-file  record  invalid
     if       fs-reply = 21
              move  255  to  we-error.
     if       we-error  not = 255
              move  1  to  truth.
*>
     if       a-test = "D"
              move  Ledger-Place to  save-place
              if    ledger-type  numeric
                    move  ledger-type  to  save-type
              else
                    move  zero  to  save-type.
*>
     move     dummy-record  to  WS-Ledger-Record.
*>
     if       a-test = "D"
              move  save-type  to  ledger-type
              move  save-place to  Ledger-Place.
*>
 ledger-write.
     move     WS-Ledger-Nos  to  n-code.
     move     y to  n-pc  ledger-pc.
*>
     perform  GL-Nominal-Write.      *>  write WS-Ledger-Record.
*>
 PC-Code-Check.
     move     1  to  truth.
*>
     if       pc-code = spaces
              move  "00"  to  pc-code.
     if       pc-code = "**"
              go to  PC-Code-Check-exit.
*>
     if       pc-code  not <  "00"  and  not >  "99"
              go to  PC-Code-Check-exit.
*>
     if       pc-code2  not = "*"
              move   zero  to  truth
              go to  PC-Code-Check-exit.
*>
     if       pc-code1  not <  "0"  and  not >  "9"
              go to  pc-code-main-check
     else
              move   zero  to  truth
              go to  PC-Code-Check-exit.
*>
 pc-code-main-check.
     if       pc-code2  not = "*"
              move   pc-code  to  z
              if     p-b-codes (z) = "E"  or  "Y"
                     go to  PC-Code-Check-exit
                else
                     move   zero  to  truth
                     go to  PC-Code-Check-exit.
*>
     move     pc-code1  to  z.
     multiply z  by  10  giving  z.
     move     zero  to  truth.
*>
     if       z  >  0
              perform aloop  10  times
       else
              add  1  to  z
              perform aloop  9   times.
*>
     go       to PC-Code-Check-exit.
*>
 aloop.
     if       p-b-codes (z) = "E"  or  "Y"
              move  1  to  truth.
*>
     add      1  to  z.
*>
 PC-Code-Check-exit.
     exit.
*>
 gl030c section.      *> CoA update
*>*************
*>
*> New (29/05/18) Support for Esc, F8 and F9 on accept Name.
*>
     perform  GL-Nominal-Open-Input.      *> open input ledger-file as cant do I/O - it might create.
     if       fs-reply not = zero
              display space
              display GL033 at 0901 with foreground-color 2
              go to main-exit.
     perform  GL-Nominal-Close.     *> close ledger-file.
     perform  GL-Nominal-Open.            *> open i-o ledger-file.
*>
     if       not  Profit-Centres
       and    not  Branches
              go to  by-pass-pc.
*>
     move     999999  to  WS-Ledger-Nos.
     move     zero    to  ledger-pc.
*>
     perform  GL-Nominal-Read-Indexed.      *> read ledger-file  invalid key
     if       fs-reply = 21
              move  255  to  we-error.
*>
     if       we-error = 255
              move  spaces            to  p-c-Branches
       else
              move  WS-Ledger-Record  to  p-c-Branches.
*>
 by-pass-pc.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     perform  zz070-convert-date.                                    *> to users format.
     display  ws-date at 0171 with foreground-color 2.
*>
 get-input.
     display  "Chart Of Accounts Amend" at 0129 with foreground-color 2.
     display  "Ledger    Sub" at 0401 with foreground-color 2.
     if       Profit-Centres
              display "P/C" at 0417 with foreground-color 2.
     if       Branches
              display "Branch" at 0415 with foreground-color 2.
     display  "-----------Name-----------  Type  Placement  Level" at 0423 with foreground-color 2.
     move     6  to  lin.
*>
 Loop.
     move     1 to cole.
     display  "[    ]" at curs with foreground-color 2 erase eol.
     move     11 to cole.
     display  "[  ]" at curs with foreground-color 2.
*>
     if       Profit-Centres  or  Branches
              move 16 to cole
              display "[  ]" at curs with foreground-color 2.
*>
     move     23 to cole.
     display  "[" at curs with foreground-color 2.
     move     48 to cole.
     display  "]  [ ]      [ ]      [ ]" at curs with foreground-color 2.
*>
 Accept-Ledger.
     move     zeros to WS-Ledger-Nos.
     move     2 to cole.
     accept   ledger-n at curs with foreground-color 3 update.
*>
     if       ledger-n = zero
           or Cob-Crt-Status = Cob-Scr-Esc
              go to  main-end.
*>
     move     12 to cole.
     accept   ledger-s at curs with foreground-color 3 update.
*>
 accept-pc.
     move     lin to lin2.
     add      1 to lin2.
     if       not  Profit-Centres
          and not  Branches
              move  zero  to  pc-code
              go to  A-Test-Key.
*>
     move     17 to cole.
     accept   pc-code at curs with foreground-color 3 update.
     perform  PC-Code-Check thru PC-Code-Check-exit.
*>
     move     17 to col2.
     if       a-false
              display GL038 at curs2 with foreground-color 2
              go to  accept-pc.
*>
 A-Test-Key.
     display  space at curs2 with erase eol.
     move     1 to col2.
*>
     move     zero        to  we-error.
*>
     if       pc-code2 = "*"
              move  "A"  to  a-test
              move  pc-code  to  save-code
              move  "00"  to  pc-code.
     move     pc-code     to  ledger-pc.
*>
     perform  GL-Nominal-Read-Indexed.      *> read ledger-file  record  invalid key
     if       fs-reply = 21
              move  255  to  we-error.
*>
     if       we-error = 255
              move 1 to col2
              display WS-Ledger-Nos at curs2 with foreground-color 2
              move 7 to col2
              display "/"       at curs2 with foreground-color 2
              move 8 to col2
              display ledger-pc at curs2 with foreground-color 2
              move 11 to col2
              display GL039     at curs2 with foreground-color 2
              go to  Accept-Ledger.
     if       a-test = "A"
              move  save-code  to  pc-code
              move  space  to  a-test.
*>
     move     24 to col2 cole.
     display  "<+> = Delete, F9 = Copy/Replace, F8 = Move, ESC = Quit" at curs2 with foreground-color 2.
     accept   ledger-name at curs with foreground-color 3 update.
*>
     display  space at curs2 with erase eol.
     move     ledger-name  to  name-test.
     if       first-char = "+"
              perform  deletion
              go to    addition-end-2.
*>
     if       Cob-Crt-Status = Cob-Scr-Esc               *> Quit back to a/c accept.
              go to Loop.
     if      (Cob-Crt-Status = Cob-Scr-F9 or  Cob-Scr-F8)
         and (Ledger-Balance not = zero
          or  Ledger-Last not = zero)
              display GL037 at curs2 with foreground-color 2 erase eol
              go to Accept-Ledger.
     if       Cob-Crt-Status = Cob-Scr-F9
          or  Cob-Crt-Status = Cob-Scr-F8                *> move a/c to new a/c re
              perform  zz200-Copy-and-Move-Account
              go to Addition-End-2.

 accept-type.
     display  space at curs2 with erase eol.
     move     1 to col2.
     move     52 to cole col2.
     accept   ledger-type at curs with foreground-color 3 update.
*>
     if       ledger-type not = zero
          and not = 1
          and not = 9
              display "Invalid type!" at curs2 with foreground-color 2
              go to  accept-type.
*>
 accept-placement.
     display  space at curs2 with erase eol.
*>
     move     61 to cole col2.
     accept   Ledger-Place at curs with foreground-color 3 update.
     move     function upper-case (Ledger-Place) to Ledger-Place.
     if       Ledger-Place  <  "A"  or  >  "Z"
              display "Invalid Placement!" at curs2 with foreground-color 2
              go to  accept-placement.
*>
*>    Profit centres/Branches only valid for Revenue Accounts
*>
     if       revenue-only  and  Ledger-Place >  "N"
              and  ledger-pc  not = zero
              display "PC/BR, Revenue only"  at curs2 with foreground-color 2
              go to  Accept-Ledger.
*>
 accept-header.
     if       ledger-type not = zero
              go to accept-end
     else
              move zero to Ledger-Level
     end-if
     move     70 to cole col2.
     accept   ledger-level at curs with foreground-color 3 update.
     if       ledger-level  <  1  or  >  4
              display "Invalid!" at curs2 with foreground-color 2
              go to  accept-header.
     display  space at curs2 with erase eol.
*>
 accept-end.
*>
 Loop-end.
     if       pc-code2 = "*"
              go to  multi-add.
*>
     move     pc-code  to  y.
     perform  ledger-rewrite.
     go       to addition-end.
*>
 multi-add.
     move     zero  to  ledger-pc  y.
*>
     if       pc-code1 = "*"
              move  1  to  y
              perform  Loop-add  99  times
              go to  addition-end.
*>
     move     pc-code1  to  y.
     multiply y  by  10  giving  y.
*>
     if       y  >  0
              perform  Loop-add  10  times
       else
              add  1  to  y
              perform  Loop-add  9   times.
*>
     go       to addition-end.
*>
 Loop-add.
     if       p-b-codes (y) = "E"  or  "Y"
              perform  ledger-rewrite.
*>
     add      1  to  y.
*>
 addition-end.
     move     zero  to  y.
     perform  ledger-rewrite.
*>
 Addition-End-2.
     add      1  to  lin.
     move     1 to cole.
     display  space at curs with erase eol.
*>
     if       lin  <  ws-22-lines
              go to  Loop.
*>
     move     6  to  lin.
*>
 screen-clear.
     display  space at curs with erase eol.
     add      1  to  lin.
*>
     if       lin  <  ws-22-lines
              go to screen-clear
      else
              go to  Loop.
*>
 main-end.
     perform  GL-Nominal-Close.     *> close ledger-file.
*>
 main-exit.   exit section.
*>********    ****
*>
 deletion                section.   *> Delete entries in CoA
*>------------------------------
*>
 Loop-end.
     if       pc-code2 = "*"
              go to  multi-add.
*>
     move     pc-code  to  y.
     perform  ledger-delete.
     go       to addition-end.
*>
 multi-add.
     move     zero  to  ledger-pc  y.
*>
     if       pc-code1 = "*"
              move  1  to  y
              perform  Loop-add  99  times
              go to  addition-end.
*>
     move     pc-code1  to  y.
     multiply y  by  10  giving  y.
*>
     if       y  >  0
              perform  Loop-add  10  times
       else
              add  1  to  y
              perform  Loop-add  9   times.
     go       to addition-end.
*>
 Loop-add.
     if       p-b-codes (y) = "E"  or  "Y"
              perform  ledger-delete.
     add      1  to  y.
*>
 addition-end.
     move     zero  to  y.
     perform  ledger-delete.
     move     1  to  truth.
*>
 main-exit.   exit section.
*>********    ****
*>
 ledger-rewrite          section.
*>------------------------------
*>
     move     WS-Ledger-Nos  to  n-code.
     move     y           to  n-pc  ledger-pc.
*>
     perform  GL-Nominal-Rewrite.      *> rewrite WS-Ledger-Record.
     if       fs-reply not = zero
              display GL034    at line ws-23-lines col 01 with foreground-color 4
              display FS-Reply at line ws-23-Lines col 20 with foreground-color 4
              accept ws-reply  at line ws-23-lines col 46 with foreground-color 2
              perform  GL-Nominal-Write.      *>   write WS-Ledger-Record.
*>
 main-exit.   exit section.
*>********    ****
*>
*>
 ledger-delete           section.
*>------------------------------
*>
     move     WS-Ledger-Nos  to  n-code.
     move     y              to  n-pc
                                 ledger-pc.
*>
     if       ledger-balance  not = zero
              move  zero  to  truth
              display GL035   at line ws-lines col 01 with foreground-color 2
              go to  main-exit.
*>
     perform  GL-Nominal-Delete.  *> delete ledger-file  record.
*>
 main-exit.   exit section.
*>********    ****
*>
 gl030e section.       *> Produce Alphabetic sorted listing
*>*************
*>
*>  Now works with a pre-loaded (zz100) table of ledger acs and Names
*>
     perform  zz100-Load-Ledger-Table.       *> loads from ledgers and then sorted.
     perform  GL-Nominal-Open-Input.       *> open input  ledger-file.
     move     prog-name to l1-prog.
     if       fs-reply not = zero
              display GL035 at line ws-lines col 01 with foreground-color 2
              go to main-exit.
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
     display  "Chart Of Accounts Alphabetic Print" at 0123 with foreground-color 2.
*>
     move     zero  to  truth.
     open     output  print-file.
*>
     if       Profit-Centres
              move  "Profit Centre    "  to  l4-filler-2
     else
      if      Branches
              move  "    Branch       "  to  l4-filler-2
      else
              move  spaces               to  l4-filler-2.
*>
     move     ws-date  to  l1-date.
     move     zero    to  page-nos.
     move     usera   to  l3-user.
     perform  page-heading.
*>
*> New code 24/5/18 for table search then read indexed
*>
     move      zero to WS-TBL-Sub.
*>
 P-Loop.
     add      1 to WS-TBL-Sub
     if       WS-TBL-Sub > WS-TBL-Entry-Cnt
         or   WS-TBL-Ledger  (WS-TBL-Sub) = high-values
              go to End-Report
     end-if
     move     WS-TBL-Ledger (WS-TBL-Sub)  to WS-Ledger-Key9.
     perform  GL-Nominal-Read-Indexed.
     if       FS-Reply not = zero            *> cant read a record that should be present ??
              go to End-Report.
*>
     if       ledger-n = 9999
              go to  P-Loop.
*>
     move     spaces  to  l5-level-filler l5-placement l5-name.
     move     zero    to  l5-header       l5-detail    l5-pc z.
*>
     if       ledger-level = zero
              go to  Detail-Jump.
*>
     move     ledger-level  to  z.
     multiply z  by  2  giving  i.
     add      1  to  i.
     move     ledger-level  to  l5-level (i).
     move     WS-Ledger-Nos    to  n-code.
     divide   n-code  by  100   giving  l5-header.
*>
 Detail-Jump.
     if       ledger-level = zero
              move    WS-Ledger-Nos  to  n-code
              divide  n-code      by  100  giving  l5-detail.
*>
     perform  Compute-Placement.
     move     place (z)    to  l5-placement.
     move     ledger-pc    to  l5-pc.
     move     ledger-name  to  l5-name.
*>
     write    print-record  from  line-5 after 1.
     add      1 to line-cnt.
     if       line-cnt > Page-Lines
              perform  Page-Heading.
*>
     go       to p-loop.
*>
 Page-Heading.
     add      1  to  page-nos.
     move     page-nos  to  l3-page.
*>
     if       page-nos not = 1
              write print-record  from  line-1 after page
     else
              write print-record  from  line-1 after 1.
     write    print-record  from  line-3 after 1.
     write    print-record  from  line-4 after 2  lines.
*>
     move     spaces  to  print-record.
     write    print-record after 1.
     move     5 to line-cnt.
*>
 End-Report.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 Main-End.
*>*******
*>
     perform  GL-Nominal-Close.     *> close ledger-file.
*>
 Main-Exit.
     exit section.
*>
 Compute-Placement section.
*>------------------------
*>
     if       Ledger-Place  less  "E"
              move  1  to  z
     else
      if      Ledger-Place  less  "I"
              move  2  to  z
      else
       if     Ledger-Place  less  "K"
              move  3  to  z
       else
        if    Ledger-Place  less  "O"
              move  4  to  z
        else
         if   Ledger-Place  less  "R"
              move  5  to  z
         else
          if  Ledger-Place  less  "U"
              move  6  to  z
          else
           if Ledger-Place  less  "W"
              move  7  to  z
           else
              move  8  to  z.
*>
 main-exit.   exit section.
*>********    ****
*>
 gl030f section.         *> Display (5) or print (6) CoA
*>*************
*>
     move     prog-name to l1-prog.
     perform  GL-Nominal-Open-Input.             *> open input  ledger-file.
     if       fs-reply not = zero
              display space at 0101 with erase eos
              display GL036 at 0901 with foreground-color 2
              go to main-exit.
*>
 d-head-1.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
     display  "Chart Of Accounts Display" at 0127 with foreground-color 2.
*>
 d-head-end.
     move     zero  to  truth.
*>
 main-target.
     if       ws-menu = 6
              display "Print Out" at 0145 with foreground-color 2
              go to  print-out.
*>
     move     3  to  lin.
     perform  gl030f-screen-clear.
*>
     move     zero  to  ledger-n  ledger-s Ledger-PC.
*>
     display  "Enter the start Account - [      ]" at 0401 with foreground-color 2.
     if       Profit-Centres  or  Branches
              display "/  ]" at 0434 with foreground-color 2.
*>
     display  space at line ws-23-lines col 01 with erase eol.
     display  "Press <Esc> key to exit" at line ws-23-lines col 01 with foreground-color 2.
*>
     accept   WS-Ledger-Nos at 0428 with foreground-color 3 update.
     display  "                " at 0841 with foreground-color 2
*>
     if       cob-crt-status = cob-scr-esc
              move  "Q"  to  seek
              move  0  to  truth
              go to  main-end.
*>
     move     zero  to  ledger-pc.
*>
     if       Profit-Centres  or  Branches
              accept ledger-pc at 0435  with foreground-color 3 update.
*>
     move     WS-Ledger-Nos  to  save-ledger.
     move     WS-Ledger-Nos  to  n-code.
     move     ledger-pc   to  n-pc.
     move     4   to  lin.
     move     1   to  truth.
*>
*>     alter    gate  to  do-clear
 *>    move     1 to gate-sw.
     set      DoClear to true.
*>
     perform  display-chart.
*>
     move     1 to File-Key-No.
     set      fn-Not-Less-Than to true.
     perform  GL-Nominal-Start.  *> start ledger-file key not < ledger-key invalid key
     if       FS-Reply not = zero
              move  255  to  we-error.
*>
     if       we-error = zero
              perform  GL-Nominal-Read-Next      *>   read  ledger-file   next record  at end
              if     fs-reply = 10
                     move 255 to we-error.
*>
     if       we-error = 255
              display "No match found !" at 0841 with foreground-color 2
              go to  main-target.
*>
     move     zero  to  truth.
     add      2  to  lin.
*>
 main-loop.
     display  "<N> Next; <I> Next ignore same code; <C> Cont; <Q> Quit :- [I]"
                                            at line ws-23-lines col 01  with foreground-color 2.
     move     "I"  to  seek.
*>
     perform  display-chart.
     accept   seek at line ws-23-lines col 61 with foreground-color 3 update auto.
     move     function upper-case (seek) to seek.
*>
     if       seek = "Q"
              move  0  to  truth
              go to  main-end.
*>
 subsid-loop.
*>     alter    gate  to  ask-clear.
 *>    move     2 to gate-sw.
     set      AskClear to true.
*>
     perform  GL-Nominal-Read-Next.      *>  read     ledger-file  next record  at end
     if       fs-reply = 10
              move  255 to we-error.
*>
     if       we-error = 255
           or ledger-n = 9999
              go to  main-target.
*>
     if       seek = "I"
        and   WS-Ledger-Nos = save-ledger
              go to  subsid-loop.
*>
     move     WS-Ledger-Nos  to  save-ledger.
*>
     add      1  to  lin.
     if       lin = ws-22-lines
              perform ask-clear
       if     cob-crt-status = cob-scr-esc
*>              alter gate to do-clear
 *>             move 1 to gate-sw
              set  DoClear to true
              go to main-target
        else
              perform d-head-1
              move 4 to lin
              perform second-head
              move  6   to  lin.
*>
     if       seek  not = "C" and "I"
              go to  main-loop
        else
              perform  display-chart
              go to  subsid-loop.
*>
 print-out.
     open     output  print-file.
*>
     if       Profit-Centres
              move  "Profit Centre    "  to  l6-filler-2
     else
      if      Branches
              move  "   Branch       "   to  l6-filler-2
      else
              move  spaces               to  l6-filler-2.
*>
     move     to-day  to  l1-date.
     move     zero    to  page-nos.
     move     usera   to  l3-user.
     perform  page-heading.
*>
 p-loop.
     perform  GL-Nominal-Read-Next.      *>  read ledger-file  next record  at end
     if       fs-reply = 10
              move  255 to we-error.
*>
     if       we-error = 255
           or ledger-n = 9999
              go to  end-report.
*>
     move     spaces  to  l7-level-filler l7-placement l7-name.
     move     zero    to  l7-header l7-detail l7-pc z.
*>
     if       ledger-level = zero
              go to  detail-jump.
*>
     move     ledger-level  to  z.
     multiply z  by  2  giving  i.
     add      1  to  i.
     move     ledger-level  to  l7-level (i).
     move     WS-Ledger-Nos    to  n-code.
     divide   n-code  by  100   giving  l7-header.
     perform  Compute-Placement.
     move     place (z)    to  l7-placement.
*>
 detail-jump.
     if       ledger-level = zero
              move    WS-Ledger-Nos  to  n-code
              divide  n-code      by  100  giving  l7-detail.
*>
     move     ledger-pc     to  l7-pc.
     move     ledger-name  to  l7-name.
*>
     write    print-record  from  line-7 after 1.
     add      1 to line-cnt.
     if       line-cnt > Page-Lines
              perform  page-heading.
*>
     go       to p-loop.
*>
 page-heading.
     add      1  to  page-nos.
     move     page-nos  to  l3-page.
*>
     if       page-nos not = 1
              write print-record  from  line-1 after page
     else
              write print-record  from  line-1 after 1.
     write    print-record  from  line-3 after 1.
     write    print-record  from  line-6 after 2.
*>
     move     spaces  to  print-record.
     write    print-record after 1.
     move     5 to line-cnt.
*>
 end-report.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 main-end.
     perform  GL-Nominal-Close.     *> close ledger-file.
*>
 main-exit.   exit section.
*>********    ****
*>
 display-chart section.
*>--------------------
*>
*>  If true set-up headings else display a line of data
*>
     if       a-false
              go to  detail-display.
*>
 second-head.
     move     1 to cole.
     display  "Ledger    " at curs with foreground-color 2.
     move     11 to cole.
     display  "Sub    " at curs with foreground-color 2.
*>
     move     18 to cole.
     if       Profit-Centres
              display "  P/C   " at curs with foreground-color 2
     else
      if      Branches
              display "Branch  " at curs with foreground-color 2
      else
              display "        " at curs.
*>
     move     26 to cole.
     display  "<---------Name--------->    Type    Level --Placement--" at
                 curs with foreground-color 2.
*>
 main-pass.
     go       to main-exit.
*>
 detail-display.
     move     2 to cole.
     display  ledger-n at curs with foreground-color 2.
     move     11 to cole.
     display  ledger-s at curs with foreground-color 2.
     move     20 to cole.
     if       Profit-Centres or Branches
              display  ledger-pc at curs with foreground-color 2.
     move     25 to cole.
     display  ledger-name at curs with foreground-color 2.
*>
     if       ledger-type = 9
              subtract  4  from  ledger-type
      else
              add 1 to ledger-type.
*>
     move     53 to cole.
     if       ledger-type < 1 or > 5
              move "ERROR in type [1 - 4]?" to ws-ledger-desc
       else
              move ledger-desc (ledger-type) to ws-ledger-desc.
     display  ws-ledger-desc at curs with foreground-color 2.
*>
     if       ledger-level not =  zero
              move 64 to cole
              display ledger-level at curs with foreground-color 2
              perform  Compute-Placement
              move 68 to cole
              move place (z) to ws-place
              display ws-place at curs with foreground-color 2.
*>
 main-exit.   exit section.
*>********    ****
*>
 gl030f-screen-clear         section.
*>----------------------------------
*>
 gate.
     if       askclear
              go to ask-clear.
     if       doclear
              go to do-clear.
*>      go to  do-clear.
*>
 ask-clear.
*>
     display  "Press Return for next screen" at line ws-23-lines col 01
                with foreground-color 2 erase eol.
     accept   ws-reply at line ws-23-lines col 41 with foreground-color 2.
*>
 do-clear.
*>
*>     alter    gate  to  ask-clear.
*>     move     2 to gate-sw.
     set      AskClear to true.
     move     lin  to  save-lin.
*>
 Loop.
     move     1 to cole.
     display  space at curs with erase eol.
     add      1  to  lin.
     if       lin  <  ws-23-lines
              go to  Loop.
*>
     move     save-lin  to  lin.
*>
 main-exit.
     exit     section.
*>
 gl030g section.      *> PC report  OR Branches looking at menu ??
*>*************
*>
*>  LOOKS LIKE ONLY printing Establishments or are they PCs/Branches. need tests.
*>
     perform  GL-Nominal-Open-Input.           *> open input  ledger-file.
     if       fs-reply not = zero
              display space at 0101 with erase eos
              display GL036 at 0901 with foreground-color 2
              go to main-exit.
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
     display  "Profit Centres Report" at 0127 with foreground-color 2.
*>
     move     zero  to  truth.
     move     999999 to  WS-Ledger-Nos.
     move     zero   to  ledger-pc.
*>
     perform  GL-Nominal-Read-Indexed.      *>  read ledger-file  record invalid  key
     if       fs-reply = 21
              move     255  to  we-error.
*>
     if       we-error = 255
              move  spaces            to  p-c-Branches
       else
              move  WS-Ledger-Record  to  p-c-Branches.
*>
     move     999999  to  pc-ledg.
     move     zero    to  pc-pc est.
*>
     set      pc  to  1.
     search   p-b-codes when p-b-codes (pc) = "E"
              set   est  to  pc.
*>
 print-out.
     open     output  print-file.
*>
     move     to-day  to  l11-date.
     move     zero    to  page-nos.
     move     usera   to  l13-user.
     perform  page-heading.
*>
 p-loop.
     move     1  to  y.
*>
 Loop-3.
     if       p-b-codes (y)  = space
              go to  Loop-3-return.
*>
     move     zero   to  z.
     add      y      to  z.
     move     999999 to  WS-Ledger-Nos.
     move     z      to  ledger-pc.
*>
     perform  GL-Nominal-Read-Indexed.      *>  read ledger-file  record  invalid key
     if       fs-reply = 21
              move  255  to  we-error.
*>
     if       we-error = 255
              move  spaces  to  ledger-name.
*>
 Loop-3-back.
     move     ledger-pc    to  l15-nos.
     move     ledger-name  to  l15-name.
     write    print-record  from  line-15 after 1.
     add      1 to line-cnt.
     if       line-cnt > Page-Lines
              perform  page-heading.
     add      1  to  lin.
*>
 Loop-3-return.
     add      1  to  y.
     if       y  <  99
              go to  Loop-3.
*>
     go       to end-report.
*>
 page-heading.
     add      1  to  page-nos.
     move     page-nos  to  l13-page.
*>
     if       page-nos not = 1
              write print-record from line-1 after page
     else
              write print-record from line-1 after 1.
     write    print-record  from  line-13 after 1.
     write    print-record  from  line-14 after 2.
     move     spaces  to  print-record.
     write    print-record after 1.
     move     5 to line-cnt.
*>
 end-report.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 main-end.
     perform  GL-Nominal-Close.
*>
 main-exit.
     exit section.
*>
 gl030h section.      *> Import/Export CoA from text file al la irs010
*>*************
*>
*> First we need to ask import or export
*>
 GL030h-Main.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Import / Export CoA File" at 0129 with foreground-color 2.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
     display  usera at 0301 with foreground-color 3.
*>
     display  "Select one of the following by number :- [ ] or by Function key" at 0801 with foreground-color 2.
     display  "(1)    Export the Chart of Accounts"  at 1001 with foreground-color 2.
     display  "(2)    Import the Chart of Accounts"  at 1201 with foreground-color 2.
     display  "(9)    Exit to system menu"           at 1401 with foreground-color 2.
*>
     move     zero to ws-Menu.
     accept   ws-Menu at 0843  with foreground-color 6 auto.
*>
     if       ws-Menu = 9
           or Cob-Crt-Status = Cob-Scr-Esc
              go to  gl030h-Exit.
     if       ws-Menu = 1
              perform ea-Export-CoA.
     if       ws-Menu = 2
              perform fa-Import-CoA.
     go       to GL030h-Main.
*>
 gl030h-Exit.
     exit     section.
*>
 ea-Export-CoA section.
*>--------------------
*>
 ea010-Warning-Notice.
     display  "This process will export a copy of the current CoA (Chart of Accounts)"
                 at 0101 with foreground-color  cob-color-yellow erase eos.
     display  "overwriting any copy of the file if it exists."
                 at 0221 with foreground-color cob-color-yellow.
     display  "Continue Y/N [ ]"      at 0401 with background-color cob-color-red
                                         foreground-color cob-color-white.
*>
     move     space to Menu-Reply.
     accept   menu-reply at 0415.
     if       menu-reply = "N" or = "n"
              exit section
     end-if.
*>
     display  "File name to be created [12345678901234567890123456789012]"
                                 at 0601 with foreground-color cob-color-yellow.
     accept   Archive-Name at 0626 with update.
     if       Archive-Name = spaces or Cob-Crt-Status = Cob-Scr-Esc
              display "Quiting to Sub Menu" at 1001 with erase eol
              exit section.
*>
 ea020-Open-Output.
     open     Output Saved-CoA.
     if       fs-reply not = zero
              display  "Problem opening Export File, hit return to quit action" at 2301
              accept   ws-reply at 2360
              close    Saved-CoA
              exit section
     end-if.
*>
*> Open nominal ledger
*>
     move     zero to Counter
                      In-Counter.
     perform  GL-Nominal-Open-Input.
     if       FS-Reply not = zero
              display "Problem opening CoA, Hit return to quit action" at 2301
              accept  ws-reply at 2360
              perform  GL-Nominal-Close
              close    Saved-CoA
              exit section
     end-if.
*>
     perform  until FS-Reply not = zero     *> initially on open, and checked lower down
              perform GL-Nominal-Read-Next
              if   WS-Ledger-Key9 = 99999999    *> Dummy record ?
                   display "Got CoA trailer record"  at 1601
              end-if
              if   FS-Reply not = zero   or     *> eof
                   WS-Ledger-Key9 = 99999999    *> Dummy record ?
                   perform  GL-Nominal-Close
                   close    Saved-CoA
                   exit perform
              end-if
              add   1 to In-Counter
              initialise Export-CoA-Text
              move  WS-Ledger-Key9  to ECoA-Ledger-Key9
              move  Ledger-Type  to ECoA-Ledger-Type
              move  Ledger-Place to ECoA-Ledger-Place
              move  Ledger-Level to ECoA-ledger-Level
              move  Ledger-Name  to ECoA-Ledger-Name
              move  space        to ECoA-Filler
              move  zeros to FS-Reply
              write Export-CoA-Text
              if   FS-reply not = zero
                   display "Problem writing to Export File, Hit return to quit action" at 2301
                   display FS-Reply at 2359
                   accept  ws-reply at 2362
                   display Export-CoA-Text at 2401
                   perform  GL-Nominal-Close
                   close    Saved-CoA
                   exit perform     *> at least close files and get totals
              end-if
              add 1 to counter
     end-perform.
*>
*> Close file
*>
     display  "Total record count read in = "       at 1901.
     display  In-Counter                            at 1930.
     display  "Total record count written out = "   at 2001.
     display  Counter                               at 2034.
     display  "Note count & hit return to continue" at 2201.
     accept   ws-reply                              at 2237.
*>
     perform  GL-Nominal-Close.
     close    Saved-CoA.
*>
 ea999-exit.
     exit     section.
*>
 fa-Import-CoA section.
*>--------------------
 fa010-Warning-Notice.
*>
     display  "This process will import a CoA (Chart of Accounts) in TEXT format " at 0101
                 with foreground-color cob-color-yellow erase eos.
     display  "overwriting any existing G-L Chart of Accounts."    at 0201
                  with foreground-color cob-color-yellow.
     display  "This must only be done for a new set of accounts for a new business" at 0301
                  with foreground-color cob-color-yellow.
     display  "Otherwise, If you have not made a back up of it you should quit this process."
                   at 0401 with foreground-color cob-color-yellow.
     display  "Warning: This is NON RECOVERABLE, so think about it"       at 0714
                     with foreground-color cob-color-red.
     display  "Before responding (Y)es ensure you have a back copy of the original file"
                    at 0901 with   foreground-color cob-color-yellow.
     display  "Otherwise respond (N)o and then exit the main menu to do so."
                    at 1001 with foreground-color cob-color-yellow.
     display  "Continue Y/N [ ]"                                          at 1201
                     with background-color cob-color-red  foreground-color cob-color-white.
*>
     accept   menu-reply at 1215.
     if       menu-reply = "N" or = "n"
              move "1" to menu-reply
              exit section
     end-if.
*>
     display  "File name to be Imported [12345678901234567890123456789012]" at 1501 with
                 foreground-color cob-color-yellow.
     accept   Archive-Name at 1527 with foreground-color cob-color-yellow update.
     if       Archive-Name = spaces
           or Cob-Crt-Status = Cob-Scr-Esc
              display "Quiting to menu" at 1501 with erase eol
              exit section.
*>
 fa020-Open-Files.
     open     Input Saved-CoA.
     if       fs-reply not = zero
              display "Problem opening Import File, hit return to quit action" at 2301
              accept  ws-reply at 2360
              close    Saved-CoA
              exit section
     end-if.
*>
     perform  GL-Nominal-Open-Output.
     if       FS-Reply not = zero
              display "Problem opening Accounts for output, hit return to quit action" at 2301
              accept  ws-reply at 2365
              perform  GL-Nominal-Close
              close    Saved-CoA
              exit section
     end-if.
     move     zero to Counter
                      In-Counter.
*>
*>  Set all amounts to zero, cannot use initialize owing to presence of redefines
*>
     initialise WS-Ledger-Record with filler.
*>
 fa030-Read-Input.
     read     Saved-CoA record at end
              go to fa040-End-Of-Input.
*>
     add     1 to In-Counter.
     move    ECoA-Ledger-Key9   to WS-Ledger-Key9.
     move    ECoA-Ledger-Type   to Ledger-Type.
     move    ECoA-Ledger-Place  to Ledger-Place.
     move    ECoA-ledger-Level  to Ledger-Level.
     move    ECoA-Ledger-Name   to Ledger-Name.
*>
     perform  GL-Nominal-Write.
     if       FS-Reply not = zero
              display "Problem writing to Accounts, hit return to quit action" at 2301
              close    Saved-CoA
              perform  GL-Nominal-Close
              accept  ws-reply at 2365
              exit section
     end-if.

     add      1  to Counter.
     go       to fa030-Read-Input.
*>
 fa040-End-Of-Input.
     display  "Total record count read in = "       at 1901.
     display  In-Counter                            at 1930.
     display  "Total records created = "            at 2001.
     display  Counter                               at 2026.
     display  "Note count & hit return to continue" at 2201.
     accept   ws-reply                              at 2237.
*>
     close    Saved-CoA.
     perform  GL-Nominal-Close.
*>
 fa999-Exit.
     exit     section.

*>
 main-exit.
     exit section.
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   ws-test-date
*> output:  u-date/ws-date as uk date format
*>          u-bin not zero if valid date
*>
     inspect  ws-test-date replacing all "." by "/".
     inspect  ws-test-date replacing all "," by "/".
     inspect  ws-test-date replacing all "-" by "/".
*>
     move     ws-test-date to ws-date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-test-date.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz050-test-date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to ws-date.  *> swap Intl to UK form
     move     ws-test-date (1:4) to ws-Year.
     move     ws-test-date (6:2) to ws-Month.
     move     ws-test-date (9:2) to ws-Days.
*>
 zz050-test-date.
     move     ws-date to u-date.
     move     zero to u-bin.
     perform  maps03.
*>
 zz050-exit.
     exit     section.
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
     perform  maps03.
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
 zz070-Convert-Date        section.
*>********************************
*>
*>  Converts date in to-day to UK/USA/Intl date format
*>****************************************************
*> Input:   to-day
*> output:  ws-date as uk/US/Inlt date format
*>
     move     to-day to ws-date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> swap month and days
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
     move     to-day (7:4) to ws-Intl-Year.
     move     to-day (4:2) to ws-Intl-Month.
     move     to-day (1:2) to ws-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
 zz100-Load-Ledger-Table  section.
*>*******************************
*>
*>  Read the ledger file/table building the searchable table by name
*>   sorted by Name high-value will be present on both fields for unused entries.
*>
     perform  GL-Nominal-Open-Input.       *> open input  ledger-file.
     perform  varying WS-TBL-Entry-Cnt from 1 by 1
                    until FS-Reply not = zero
                      or   WS-TBL-Entry-Cnt >  WS-TBL-Ledgers-Size
              perform  GL-Nominal-Read-Next
              if       FS-Reply = 10
                       subtract 1 from WS-TBL-Entry-Cnt   *> was increased by 1 in perform
                       exit perform
              end-if
              if    WS-Ledger-Key9 = zeros
                    subtract 1 from WS-TBL-Entry-Cnt
                    exit perform cycle
              end-if
              move  WS-Ledger-Key9 to WS-TBL-Ledger  (WS-TBL-Entry-Cnt)
              move  Ledger-Name    to WS-TBL-Name    (WS-TBL-Entry-Cnt)
     end-perform.
     perform  GL-Nominal-Close.
     sort     WS-TBL-Group
               on ascending key WS-TBL-Name
                with duplicates.
*>
 zz100-Exit.
     exit     section.
*>
 zz200-Copy-and-Move-Account  section.
*>***********************************
*>
*>   Copy           - Using F9 at Name Req, copy existing a/c info
*>                    into a new a/c # that is requested on new line.
*>                    New a/c must not exist.
*>   Move           - Using F8 same but existing record is deleted.
*>
*>   USAGE: After accepting the Account/subnominal details and
*>          moving to new a/c, clearing
*>          Balance and last totals to zero as well as the quarter totals
*>          for the new a/c #.
*>          The old a/c # is kept.
*>          The New a/c must not exist.
*>
*>  at end we will continue with next line overwriting the update info line
*>   otherwise the line count might get confusing.
*>
 zz200-Start.
     move     1 to col2.
     Display  space at curs with erase eol.
*>
     display  "[    ]" at curs2 with foreground-color 2.
     move     11 to col2.
     display  "[  ]"   at curs2 with foreground-color 2.
*>
     move     zeros to Ledger-S-2
                       Ledger-N-2.
     move     2 to col2.
     accept   Ledger-N-2 at curs2 with foreground-color 3 update.
*>
     if       Ledger-N-2 = zero                          *> Check if user aborting copy/move request
           or Cob-Crt-Status = Cob-Scr-Esc
              go to  zz200-Exit.
*>
     move     12 to col2.
     accept   Ledger-S-2 at curs2 with foreground-color 3 update.
     if       Ledger-S-2 = zero                          *> Check if user aborting copy/move request
           or Cob-Crt-Status = Cob-Scr-Esc
              go to  zz200-Exit.
*>
     if       not  Profit-Centres
          and not  Branches
              move  zero  to  pc-code
     else
              move     17 to col2
              accept   pc-code at curs with foreground-color 3 update.
*>
*> So now to save the current ledger record, check that there is no rec for the new account
*>   before we can create new rec having cleared all totals.
*>   If Move was requested (F8) we will delete the original rec.
*>
     move     WS-Ledger-Record to Saved-Ledger-Record.
     if       Saved-Ledger-Balance not =  zero
          or  Saved-Ledger-Last not = zero
              display GL037    at line lin2 col  1 with erase eol
              display SY008    at line lin2 col 41
              accept  ws-reply at line lin2 col 74
              go to zz200-Exit.
*>
     move     Ledger-N-2   to Ledger-N.
     move     Ledger-S-2   to Ledger-S.
     move     PC-Code      to Ledger-PC.
*>
*> Now we could, check pc-code for 'AL'  then get all existing records with code = 00-99
*>   and move those as well, but one thing at a time but as is will have to be moved one
*>     at a time.
*>
     perform  GL-Nominal-Read-Indexed.                   *> read ledger-file  record  invalid key
     if       fs-reply = zero                            *>  Opps we found a record
              display GL03A    at line lin2 col  1 with erase eol
              display SY008    at line lin2 col 41
              accept  ws-reply at line lin2 col 74
              go to zz200-Exit.
*>
*>  All looks good so we can move rec.
*>
     move     Saved-Ledger-Record to WS-Ledger-Record.
     move     Ledger-N-2   to Ledger-N.
     move     Ledger-S-2   to Ledger-S.
     move     PC-Code      to Ledger-PC.
     initialise Saved-Quarters.
     perform  GL-Nominal-Write.
     if       fs-reply not = zero
              display "Got error on writing new GL record, reply=  " at line ws-22-lines col 1
              display FS-Reply  at line ws-22-lines col 43
              display SY008     at line ws-23-lines col 1
              accept  ws-reply  at line ws-23-lines col 33
              go to zz200-Exit.
*>
     if       Cob-Crt-Status = Cob-Scr-F8
              move     Saved-Ledger-Record to WS-Ledger-Record
              perform  GL-Nominal-Delete.
*>
 zz200-Exit.
     exit     section.
*>
 maps03       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
