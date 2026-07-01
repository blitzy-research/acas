       >>source free
*>****************************************************************
*>              Recurring Invoice Processing                     *
*>                                                               *
*>           Auto  Generate Invoice  Menu & Maintenance          *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.         sl800.
*>**
*>    Author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, written 15/04/23
*>                        As can't find original code for AutoGen.
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 2023-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Auto Gen Invoice Menu.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     sl810 - Autogen Input, Amend ?
*>                        sl820 - Proof report
*>                        sl830 - Post - to INVOICE FILE
*>**
*>    Error messages used.
*>                        None
*>**
*> Changes:
*> 15/04/23 vbc - .00 Created from sl900, then hacked hard.
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
*>================================
*>
 copy "envdiv.cob".
*>
 data                    division.
*>================================
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(15) value "SL800 (3.3.00)".
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  ws-data.
     03  Menu-Reply          pic x.
     03  ws-reply            pic x.
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
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 01  to-day              pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
*>  Will need to support auto program load via sales to run sl830
*>   as SL Generate
*>
*>
 init01 section.
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
     perform  zz070-Convert-Date.
     move     ws-caller to ws-del-link.
     move     ws-called to ws-caller.
*>
 Menu-Return.
     move     zero  to  Menu-Reply.
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "Recurring (Autogen) Sales Invoicing Menu"  at 0127 with foreground-color 2.
 *>    Auto Generate Invoicing Menu" at 0127 with foreground-color 2.
     display  ws-date at 0171 with foreground-color 2.
*>
     display  "Select one of the following by number :- [ ]" at 0501 with foreground-color 2.
     display  "(1)  Enter / Amend Recurring Invoice"         at 0811 with foreground-color 2.
     display  "(2)  Proof Recurring Invoicing"               at 0911 with foreground-color 2.
     display  "(3)  Post Recurring Invoices"                 at 1011 with foreground-color 2.
*>
     display  "(X)  Return To System menu"                   at 1211 with foreground-color 2.
*>
 Menu-Input.
     accept   Menu-Reply at 0543 with foreground-color 6 auto UPPER.
*>
     if       Menu-Reply  = "X"
              go to Menu-Exit.
*>
     if       Menu-Reply  = 1
              move   Menu-Reply  to  pass-value
              move   "sl810" to ws-called
              go to Loadit.
*>
     if       Menu-Reply  = 2
              move   Menu-Reply  to  pass-value
              move   "sl820" to ws-called
              go to Loadit.
*>
     if       Menu-Reply  = 3
              move   Menu-Reply  to  pass-value
              move   "sl830" to ws-called
              go to Loadit.
*>
     go       to Menu-Return.
*>
 Loadit.
     call     ws-called using ws-calling-data
                              system-record
                              to-day
                              file-defs.
     if       Menu-Reply = 1       *> Need to do this to save the system file and dummy invoice #
              go to Menu-Exit.
     go       to Menu-Return.
*>
 Menu-Exit.
     move     zero        to pass-value.
     move     ws-caller   to ws-called.
     move     ws-del-link to ws-caller.
*>
 menu-ex.
     exit     program.
*>
*>********************************************************
*>      P R O C E D U R E S                              *
*>********************************************************
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
