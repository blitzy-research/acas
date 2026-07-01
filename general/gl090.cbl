       >>source free
*>***************************************************
*>                                                  *
*>                Trial  Balance                    *
*>                    Menu                          *
*>***************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         gl090.
*>**
*>    Author.             GL was written by Simon Whine MBCS, on behalf of
*>                        Applewood Computers and its group of Companies.
*>                        All changes/migrations by:
*>                        Vincent B. Coen FBCS, FIDM, FIDPM.
*>                        Converted From Cis January 1985,
*>                        For Applewood Computers.
*>                        Written to supplement IRS to support larger numbers for
*>                        accounts to 10 digits nominal and subnominals and money
*>                        amounts to 100M - 1 for customers requiring a
*>                        comparable? but cheaper product than Oracle financials.
*>                        Reduced down some point later in time for accnts 6
*>                        digits and reduced money amounts.
*>**
*>    Security.           Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Trial Balance Menu.
*>                        Both report types will abort if Ledger does not exist.
*>**
*>    Version.            See Prog-Name in Ws.
*>**
*>    Called Modules.     gl090b.
*>                        gl090a.
*>**
*>    Error messages used.
*>                        NONE
*>****
*> Changes:
*> 28/01/09 vbc - Migration to open Cobol.
*> 20/12/11 vbc - .03 Support for dates other than UK & clean up msgs
*>                    Error msgs to GLnnn,
*>                    Support for path+filenames.
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks.
*> 13/01/18 vbc - .04 Updated for v3.02 & FH & DALs but no code changes here.
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
 environment             division.
*>===============================
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 data                    division.
*>===============================
*>
 working-storage section.
*>----------------------
*>
 77  prog-name           pic x(15) value "gl090 (3.3.00)".
*>
 01  ws-data.
     03  menu-reply      pic 9.
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
*> 01  Error-Messages.
*> System Wide
*> Module specific
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  to-day             pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 menu-input.
*>*********
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Trial Balance" at 0135 with foreground-color 2.
     perform  zz070-convert-date.
     display  ws-date at 0171 with foreground-color 2.
     display  usera at 0301 with foreground-color 3.
*>
     display  "Select Option By Number :- [ ]" at 0801 with foreground-color 2.
     display  "(1)  Detailed Trial Balance" at 1001 with foreground-color 2.
*>
     if       profit-centres
              display "(2)  Profit Centre Trial Balance" at 1201 with foreground-color 2
     else
      if      branches
              display "(2)  Branch Trial Balance" at 1201 with foreground-color 2.
*>
     display  "(9)  Exit to system menu" at 1701 with foreground-color 2.
*>
     move     9 to menu-reply.
     accept   menu-reply at 0829 with foreground-color 7 update.
*>
     if       menu-reply = 1
              call "gl090b" using ws-calling-data
                                  system-record
                                  to-day
                                  file-defs.
*>
     if       menu-reply = 2
              call "gl090a" using ws-calling-data
                                  system-record
                                  to-day
                                  file-defs.
*>
     if       menu-reply not = 9
              go to  menu-input.
*>
 main-exit.
     goback.
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
