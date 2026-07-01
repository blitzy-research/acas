       >>source free
*>****************************************************************
*>                                                               *
*>        Transaction Menu  &  Fixed  Data  Maintenance          *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         pl180.
*>**
*>    Author.             S.J.Whine  Aidpm
*>                        Cis Conversion By V B Coen FBCS, FIDM, FIDPM, 18/04/84
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Invoice Menu & Fixed Data.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     None.
*>****
*>    Changes:
*>
*> 22/03/09 vbc - Migration to Open Cobol v3.00.00
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks
*> 10/01/18 vbc - .02 Updated to v3.02 but no coding changes required.
*> 27/07/23 vbc - .03 Chng menu option 9 to X as standard exit option.
*>                    Add option 9 for recurring invoice menu.
*>                    Only pl800 the menu option is coded.
*>                    This is not yet coded - awaiting testing of sales
*>                    version first (recurring) etc. Chg program title.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 23/08/25 vbc   .04 Remove options 2 - 5 as in main menu options D - H.
*> 24/08/25 vbc   .05 Changed description to Transactions.
*>                    Added message warning that VAT a/c is not checked in CoA.
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
 input-output            section.
*>-------------------------------
*>
 file-control.
*>------------
*>
 i-o-control.
*>-----------
*>
 data                    division.
*>================================
*>
 file section.
*>------------
 working-storage section.
*>-----------------------
 77  prog-name          pic x(15) value "PL180 (3.3.00)".
*>
 copy "wsfnctn.cob".
*>
 01  WS-data.
     03  menu-Reply      pic x.
     03  WS-Reply        pic x.
     03  WS-Next-Folio   pic 9(8).
     03  WS-vat-ac       pic 9(6).
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob". *> File-Defs
 copy "wsnames.cob".
*>
 01  to-day              pic x(10).
*>
 procedure division using WS-calling-data
                          system-record
                          to-day
                          file-defs.
*>=======================================
*>
 init01 section.
     move     WS-caller to WS-del-link.
     move     WS-called to WS-caller.
     if       Next-Folio = zero
              perform  Fixed-Data.
*>
 Menu-Return.
     move     zero  to  menu-Reply.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Transaction Sub-System Menu" at 0128 with foreground-color 2.
     display  to-day at 0171 with foreground-color 2.
*>
     display  "Select one of the following by number :- [ ]" at 0501 with foreground-color 2.
*>
     display  "(1)  Amend Transactions Fixed Data"    at 0811    with foreground-color 2.
 *>    display  "(2)  Enter Invoices" at 1011                with foreground-color 2.
 *>    display  "(3)  Amend Invoices" at 1211                with foreground-color 2.
 *>    display  "(4)  Delete Invoices" at 1411               with foreground-color 2.
 *>    display  "(5)  Invoice Proof Report" at 1611          with foreground-color 2.
     display  "(9)  Recurring Transaction Processing" at 1811  with foreground-color 2.
     display  "(X)  Return to System Menu" at 2011         with foreground-color 2.
*>
 Menu-Input.
     accept   menu-Reply at 0543 with foreground-color 6 auto UPPER.
     move     function upper-case (Menu-Reply) to Menu-Reply.
     if       menu-Reply = "X"
              go to  Menu-Exit.
     if       menu-Reply  =  1
              perform  Fixed-Data.
 *>    if       menu-Reply  = 2
 *>             move "pl020" to WS-called
 *>             go to loadit.
 *>    if       menu-Reply  = 3
 *>             move "pl030" to WS-called
 *>             go to loadit.
 *>    if       menu-Reply  =  4
 *>             move "pl040" to WS-called
 *>             go to loadit.
 *>    if       menu-Reply  =  5
 *>             move "pl050" to WS-called
 *>             go to loadit.
     if       menu-Reply  =  9
              move "pl800" to WS-called
              go to loadit.
     go       to Menu-Return.
*>
 loadit.
     call     WS-called using WS-calling-data
                              system-record
                              to-day
                              file-defs.
     go       to Menu-Return.
*>
 Menu-Exit.
     move     WS-caller   to WS-called.
     move     WS-del-link to WS-caller.
*>
 menu-Ex.
     goback.
*>******************************************
*>                  Procedures             *
*>******************************************
*>
 Fixed-Data              section.
*>===============================
*>
     display  prog-name at 0101 with foreground-color 2  erase eos.
     display  "Transaction Fixed Data" at 0131  with foreground-color 2.
     display  to-day at 0171 with foreground-color 2.
*>
     display  "Next Folio" at 0511 with foreground-color 2.
     display  "- [        ]" at 0545 with foreground-color 2.
*>
     if       G-L
              display "Vat Account" at 0711 with foreground-color 2
              display "- [      ]"  at 0745 with foreground-color 2.
*>
     display  "Details ok to file (Y/N) ...........[Y]" at 1011 with foreground-color 2.
     display  "Warning the Vat Account is Not checked that it exists in the CoA"
                                    at 1411 with foreground-color 4 highlight.
*>
 Data-Entry.
     move     Next-Folio to WS-Next-Folio.      *> Param file is updated by purchase menu on return
     display  WS-Next-Folio at 0548 with foreground-color 3.
     accept   WS-Next-Folio at 0548 with foreground-color 3 update
     move     WS-Next-Folio to Next-Folio.
     if       Next-Folio = zero
              go to  Data-Entry.
*>
     if       not  G-L
              go to  Confirmation.
*>
     move     vat-ac to WS-vat-ac.
     display  WS-vat-ac at 0748 with foreground-color 3.
     accept   WS-vat-ac at 0748 with foreground-color 3 update.
     move     WS-vat-ac to vat-ac.
*>
 Confirmation.
     move     "Y"  to  WS-Reply.
     accept   WS-Reply at 1048 with foreground-color 6 update.
     move     function upper-case (ws-Reply) to WS-Reply.
*>
     if       WS-Reply = "N"
              go to  Data-Entry.
     if       WS-Reply not = "Y"
              go to  Confirmation.
*>
 Main-Exit.   exit.
