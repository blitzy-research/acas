       >>source free
*>****************************************************************
*>                                                               *
*>                  Payroll         Start Of Day                 *
*>         This uses ACAS param file data for date format        *
*>                 Which SHOULD be the same as PY params         *
*>                   after running py900                         *
*>                                                               *
*>        IF NOT it is a BUG in py900                            *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         py000.
*>**
*>    Author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 1/11/82
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Payroll Start of Day Program.
*>
*>**
*>    Version.            See Prog-Name & date-comped in ws.
*>
*>    Called modules.     { maps01.  }         *> code remarked out for O/S versions.
*>                        maps04. (Replaces 3)
*>**
*>    Error messages used.
*>  System wide:
*>                        PY005
*>                        SY044.     Not used in O/S versions.
*>                        SY045.        -  -  Ditto  -  -
*>                        SY046.        -  -  Ditto  -  -
*>**
*> Changes:
*> 03/03/09 vbc -        Migration to Open Cobol v3.00.00.
*>                       Removed high security encryption code/modules
*>                       as cannot be passed out of the UK as source.
*> 18/11/11 vbc -    .01 Support for multi date formats (UK, USA, Intl)
*>                       Support for path+filenames (but not used in this module).
*> 09/12/11 vbc - 3.1.   Updated version to 3.01.nn
*> 11/12/11 vbc -    .02 Changed usage of Stk-Date-Form to the global field Date-Form making former redundent.
*> 24/10/16 vbc -    .03 ALL programs now using wsnames.cob in copybooks
*> 15/01/17 vbc -    .04 All programs upgraded to v3.02 for RDB processing.
*>                       Remarked out all maps01 procs for O/S versions.
*>                       Removed maps99 usage, abort msg made literal & remd out.
*> 16/04/24 vbc          Copyright notice update superseding all previous notices.
*> 28/07/25 vbc      .05 Force "/" for UK and USA into temp date field.
*> 20/09/25 vbc - 3.3.00 Version update and builds reset.
*> 14/10/25 vbc - 1.0.00 Taken from sl000 creating py000 & tidy up var names case.
*> 13/11/25 vbc - 1.0.01 Chg wsa-date test from 000000 to 00000000. Wow.
*>**
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> These files and programs is part of the Applewood Computers Accounting
*> System and is copyright (c) Vincent B Coen. 1976-2026 and later.
*>
*> This program is now free software; you can redistribute it and/or modify it
*> under the terms of the GNU General Public License as published by the
*> Free Software Foundation; version 3 and later as revised for personal
*> usage only and that includes for use within a business but without
*> repackaging or for Resale in any way.
*>
*> Persons interested in repackaging, redevelopment for the purpose of resale or
*> distribution in a rental mode must get in touch with the copyright holder
*> with your commercial plans and proposals to vbcoen@gmail.com.
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
 77  Prog-Name           pic x(15) value "PY000 (1.0.01)".
*> copy "wsmaps01.cob".
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 01  WS-Data.
     03  Menu-Reply      pic 9.
     03  WS-Reply        pic x.
     03  WSA-Date.
       05  WSA-cc        pic 99.
       05  WSA-yy        pic 99.
       05  WSA-mm        pic 99.
       05  WSA-dd        pic 99.
     03  WSB-Time.
       05  WSB-hh        pic 99.
       05  WSB-mm        pic 99.
       05  WSB-ss        pic 99.
       05  filler        pic xx.
     03  WSD-Time.
       05  WSD-hh        pic 99.
       05  WSD-c1        pic x  value ":".
       05  WSD-mm        pic 99.
       05  WSD-c2        pic x  value ":".
       05  WSD-ss        pic 99.
*>
 01  WS-Date-formats.
     03  WS-Swap             pic xx.
     03  WS-Date             pic x(10).
     03  WS-UK redefines WS-Date.
         05  WS-Days         pic xx.
         05  filler          pic x.
         05  WS-Month        pic xx.
         05  filler          pic x.
         05  WS-Year         pic x(4).
     03  WS-USA redefines WS-Date.
         05  WS-USA-Month    pic xx.
         05  filler          pic x.
         05  WS-USA-Days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  WS-Intl redefines WS-Date.
         05  WS-intl-Year    pic x(4).
         05  filler          pic x.
         05  WS-intl-Month   pic xx.
         05  filler          pic x.
         05  WS-intl-Days    pic xx.
*>
 01  Error-Messages.
*> System Wide
     03  PY005           pic x(18) value "PY005 Invalid Date".
 *>    03  SY044           pic x(66) value "SY044 The system has detected an un-authorised change of user-name".
 *>    03  SY045           pic x(60) value "SY045 Contact your supplier and do not use the system again!".
 *>    03  SY046           pic x(33) value "SY046 Unauthorised Usage Aborting".
*>
 01  Error-Code          pic 999.
*>
 linkage section.
*>==============
*>
 01  To-Day              pic x(10).
 copy "wsnames.cob".
 copy "wscall.cob".
 copy "wssystem.cob".
*>
 procedure  division using WS-calling-Data
                           System-Record
                           To-Day
                           File-Defs.
*>========================================
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
     move     To-Day to U-Date.
*>
     accept   WSA-Date from date YYYYMMDD.
     if       WSA-Date not = "00000000"
              move WSA-cc to U-cc
              move WSA-yy to U-yy
              move WSA-mm to U-Month
              move WSA-dd to U-Days.
*>
     move     U-Date  to  To-Day.
*>
     display  "Client -"  at 0101 with foreground-color 2 erase eos.
     display  Usera       at 0110 with foreground-color 3.
     display  Prog-Name   at 0301 with foreground-color 2.
     display  "Payroll  Start Of Day" at 0333 with foreground-color 2
     display  Maps-Ser-xx at 2474 with foreground-color 2.
     move     Maps-Ser-nn to Curs2.
     display  Curs2       at 2476 with foreground-color 2.
*>
     accept   WSB-Time from Time.
     if       WSB-Time not = "00000000"
              move WSB-hh to WSD-hh
              move WSB-mm to WSD-mm
              move WSB-ss to WSD-ss
              display "at " at 0360 with foreground-color 2
              display WSD-Time at 0363 with foreground-color 2.
*>
 Date-Entry.
     if       Date-Form not > zero and < 4
              move 1 to Date-Form.
*>
*> Convert from UK to selected form
*>
     if       Date-UK or Date-USA
              move "/" to WS-Date (3:1)
                          WS-Date (6:1)
     end-if
     if       Date-USA
              move U-Date to WS-Date
              move WS-Days to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap to WS-Month
              move WS-Date to U-Date
     end-if
     if       Date-Intl
              move "ccyy/mm/dd" to WS-Date  *> swap Intl to UK form
              move U-Date (7:4) to WS-Intl-Year
              move U-Date (4:2) to WS-Intl-Month
              move U-Date (1:2) to WS-Intl-Days
              move WS-Date to U-Date
     end-if
*>
     if       Date-UK
              display "Enter todays date as dd/mm/yyyy - [          ]" at 0812 with
                                                                foreground-color 2.
     if       Date-USA
              display "Enter todays date as mm/dd/yyyy - [          ]" at 0812 with
                                                                foreground-color 2.
     if       Date-Intl
              display "Enter todays date as yyyy/mm/dd - [          ]" at 0812 with
                                                                foreground-color 2.
     display  U-Date at 0847 with foreground-color 3.
     accept   U-Date at 0847 with foreground-color 3 update.
*>
*> convert to the Standard - UK form
*>
     if       Date-USA
              move U-Date   to WS-Date
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              move WS-Date  to U-Date
     end-if
     if       Date-Intl
              move "dd/mm/ccyy" to WS-Date   *> swap Intl to UK form
              move U-Date (1:4) to WS-Year
              move U-Date (6:2) to WS-Month
              move U-Date (9:2) to WS-Days
              move WS-Date      to U-Date
     end-if
*>
     move     zero  to  U-Bin.
     call     "maps04"  using  maps03-ws.
*>
     if       U-Bin = zero
              display PY005  at 0860 with foreground-color 4
              go to  Date-Entry
     else
              display " " at 0860 with erase eol.
*>
*> Bypassed security 1 & 2 for OS version
*>
     go       to Chain-Menu.
*>
*> Verify user name.
*>
 *>    move         UserA  to Pass-Name.
 *>    move         "N"   to  Encode.
 *>    call         "maps01"  using  maps01-ws.  *> Code changed for Src export from the UK
 *>    if           Pass-Name  =  User-Code
 *>                 go to  Chain-Menu.
*>
*> If here suspected Un-Authorised / Un-Licensed usage.
*>
 *>    display  " "    at 0101 with erase eos.
 *>    display  SY044  at 0501 with foreground-color 4 erase eos.
 *>    display  SY045  at 0701 with foreground-color 4.
*>
 *>    display  SY046  at 2401 with foreground-color 5 blinking.
 *>    go       to Main-Exit.
*>
 Chain-Menu.
     move     U-Bin  to  Run-Date.
     move     U-Date to  To-Day.
     move     zero to WS-Term-Code.
*>
 Main-Exit.
     exit     program.
