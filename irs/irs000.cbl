       >>source free
*>****************************************************************
*>                                                               *
*>              Incomplete Records  Start Of Day                 *
*>                                                               *
*>****************************************************************
*>
 identification division.
      program-id.       irs000.
*>**
*>    Author.           Cis Cobol Conversion By V B Coen FIDPM FBCS, 1/11/82
*>                      For Applewood Computers.
*>**
*>    Security.         Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          IRS Start of Day Program.
*>
*>**
*>    Version.          See prog-name & date-comped in ws.
*>**
*>    Called modules.
*>                      maps04. (Replaces 3)
*>**
*>    Error messages used.
*>                        IR005 Invalid Date
*>**
*> Changes:
*> 03/03/09 vbc - Migration to Open Cobol v3.00.00.
*> 18/11/11 vbc - .01 Support for multi date formats (UK, USA, Intl)
*>                    Support for path+filenames (but not used in this module).
*> 09/12/11 vbc -     Updated version to 3.01.nn
*> 11/12/11 vbc - .02 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 20/10/16 vbc - .03 Taken from sl000 (v3.02) for IRS.
*> 22/11/16 vbc - .04 Adjusted date msgs pos. 1> as adding in s.quote.
*>                    Changed field Run-Date to ACAS-Run-Date in ACAS
*>                    System-Rec at Chain-Menu.
*>                    Cleared out not used calls in 'Calls modules' above.
*> 30/11/16 vbc - .05 Minor changes to display layout and added Client in.
*> 29/01/18 vbc - .06 Changed copies to use copybooks where possible.
*>                    Removed un-used error messages & renamed IR005.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 28/07/25 vbc   .07 Force "/" for UK and USA into temp date field.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*> 13/11/25 vbc - 3.3.01 Chg wsa-date test from 000000 to 00000000. Wow.
*>**
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
 copy  "envdiv.cob".
 input-output            section.
 file-control.
 data                    division.
 file section.
 working-storage section.
*>----------------------
 77  prog-name           pic x(16) value "IRS000 (3.3.01)".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 01  ws-data.
     03  menu-reply      pic 9.
     03  ws-reply        pic x.
     03  wsa-date.
         05  wsa-cc      pic 99.
         05  wsa-yy      pic 99.
         05  wsa-mm      pic 99.
         05  wsa-dd      pic 99.
     03  wsb-time.
         05  wsb-hh      pic 99.
         05  wsb-mm      pic 99.
         05  wsb-ss      pic 99.
         05  filler      pic xx.
     03  wsd-time.
         05  wsd-hh      pic 99.
         05  wsd-c1      pic x  value ":".
         05  wsd-mm      pic 99.
         05  wsd-c2      pic x  value ":".
         05  wsd-ss      pic 99.
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
 01  Error-Messages.
*> System Wide
     03  IR005           pic x(18) value "IR005 Invalid Date".
*>
 01  error-code          pic 999.
*>
 linkage section.
*>==============
*>
 01  to-day              pic x(10).
 copy "wssystem.cob".  *> Use ACAS param record.
*>
 procedure  division using system-record
                           to-day.
*>======================================
*>
 main.
*>***
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
     move     to-day to u-date.
*>
     accept   wsa-date from date YYYYMMDD.
     if       wsa-date not = "00000000"
              move wsa-cc to u-cc
              move wsa-yy to u-yy
              move wsa-mm to u-month
              move wsa-dd to u-days.
*>
     move     u-date  to  to-day.    *> as dd/mm/ccyy - converted later.
*>
*> New for IRS
*>
 *>  ?? Any needed ??
*>
     display  "Client -"    at 0101 with foreground-color 2 erase eos.
     display  Client        at 0110 with foreground-color 3.
 *>    display  "User   -"  at 0301 with foreground-color 2.
 *>    display  usera       at 0310 with foreground-color 3.
     display  prog-name     at 0301 with foreground-color 2.
     display  "IRS - Start Of Day"
                            at 0332 with foreground-color 2
     display  maps-ser-xx   at 2474 with foreground-color 2.
     move     maps-ser-nn to curs2.
     display  curs2         at 2476 with foreground-color 2.
*>
     accept   wsb-time from time.
     if       wsb-time not = "00000000"
              move wsb-hh to wsd-hh
              move wsb-mm to wsd-mm
              move wsb-ss to wsd-ss
              display "at "    at 0660 with foreground-color 2
              display wsd-time at 0663 with foreground-color 2.
*>
 date-entry.
*>*********
*>
     if       Date-Form not > zero and < 4      *> If not yet set up.
              move 1 to Date-Form.
*>
*> Convert from UK to selected form
*>
     if       Date-UK or Date-USA
              move "/" to WS-Date (3:1)
                          WS-Date (6:1)
     end-if
     if       Date-USA
              move u-date to ws-date
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              move ws-date to u-date
     end-if
     if       Date-Intl
              move "ccyy/mm/dd" to ws-date  *> swap Intl to UK form
              move u-date (7:4) to ws-Intl-Year
              move u-date (4:2) to ws-Intl-Month
              move u-date (1:2) to ws-Intl-Days
              move ws-date to u-date
     end-if
*>
     if       Date-UK
              display "Enter today's date as dd/mm/yyyy - [          ]" at 0812 with
                                                                foreground-color 2.
     if       Date-USA
              display "Enter today's date as mm/dd/yyyy - [          ]" at 0812 with
                                                                foreground-color 2.
     if       Date-Intl
              display "Enter today's date as yyyy/mm/dd - [          ]" at 0812 with
                                                                foreground-color 2.
     display  u-date at 0848 with foreground-color 3.
     accept   u-date at 0848 with foreground-color 3 update.
*>
*> For IRS we will for the moment, remove CC in year or will we ?
*>
*> convert to the Standard - UK form
*>
     if       Date-USA
              move u-date to ws-date
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              move ws-date to u-date
     end-if
     if       Date-Intl
              move "dd/mm/ccyy" to ws-date   *> swap Intl to UK form
              move u-date (1:4) to ws-Year
              move u-date (6:2) to ws-Month
              move u-date (9:2) to ws-Days
              move ws-date to u-date
     end-if
*>
     move     zero  to  u-bin.
     call     "maps04"  using  maps03-ws.
*>
     if       u-bin = zero
              display IR005  at 0861 with foreground-color 4
              go to  date-entry
     else
              display " " at 0861 with erase eol
     end-if.
*>
*> Bypassed security 1 for OS version
*>
 chain-menu.
*>*********
*>
     move     u-bin  to  Run-Date.
     move     u-date to  to-day.
 *>    move     zero   to  ws-term-code.
*>
 main-exit.
     exit     program.
