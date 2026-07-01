       >>source free
*>*****************************************************************
*>                                                                *
*>            ACAS  System  Menu                                  *
*>            ==================                                  *
*>                                                                *
*> NEED TO ADD ACAS SETUP Here that will call all of the          *
*>   programs used to set up the main primary files and           *
*>   RDB tables if used having made sure that they exist.         *
*>                                                                *
*> For rdb processing the rdb must have been:                     *
*>   Installed and set up with root and acas users set.           *
*>   The ACAS DB set up snd populated if needed.                  *
*>   Access to the ACAS DB tested for connection by the ACAS user *
*>    account.                                                    *
*>                                                                *
*>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>                                            *
*>  This program will call each of the main   *
*>   elements in ACAS via a menu              *
*>    such as irs, General, Stock,            *
*>         Sales, Purchase,                   *
*>     and for non O/S versions :             *
*>         Payroll, Epos, Order Entry.        *
*>    For on-line order entry systems, it is  *
*>    expected that the data export to ACAS   *
*>    been run using means outside the ACAS   *
*>    system.                                 *
*>*********************************************
*> It is not expected to use this module to   *
*>  run ACAS as most users will just load the *
*>  needed sub-system as they tend to be used *
*>  by differing departments however it does  *
*>  include access to the parameter set up    *
*>  processes where the sub systems have it   *
*>  made non available as set up in the       *
*>  parameter file.                           *
*>                                            *
*>  These extra file set ups for the moment   <
*>   must be run manually as there is no      *
*>   procedure to do it in auto mode:         *
*>  Also this program will set up the system  *
*>  parameter file & also the other required  *
*>   data files needed such as :              *
*>   IRS Ledgers                              *
*>    Using default COA file :                *
*>      coa-achived.txt                       *
*>     So a copy must be made as back up then *
*>      edit original to reflect your         *
*>      requirements FIRST and suggested      *
*>      changes are at PC directors names     *
*>      at lines starting T0018600286O also   *
*>      look at T0018200282O                  *
*>              T0019300293O                  *
*>              T0017900000O                  *
*>              T0010100000O & T0010200702O   *
*>      for the next few lines.               *
*> Remember you can always change these later *
*>   even delete some if there is no postings *
*> Next :                                     *
*>   IRS Defaults (may be) at least the       *
*>    VAT in and out presets.                 *
*>   again these can be altered at any time.  *
*>   Analysis for sales, purchase and stock.  *
*>    These are the standard defaults only &  *
*>     can be added to at any time.           *
*>   programs sl070 or pl070 can be run.      *
*> Where the system param file does not yet   *
*>   exist.                                   *
*>                                            *
*>******************************************************************
*> RDBMS support included for v3.02 and later                      *
*>                                                                 *
*>******************************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         ACAS.
*>**
*>    Author.             V.B.Coen FBCS, FIDM, FIDPM.
*>**
*>    Security.           Copyright (C) 1976-2026 Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            ACAS System Menu.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Calls:              Maps01
*>                        Maps04
*>                        Sys002
*>                        acas000   ->
*>                         systemMT
*>                        IRS
*>                        Purchase
*>                        Sales
*>                        General
*>                        Stock
*>
*> NOT on opensource:     OE
*> NOT on opensource:     Payroll
*> NOT on opensource:     EPOS
*> NOT on opensource      Project-Z
*>**
*>   Error messages.
*> System Wide    Used are
*>                        SY006.
*>                        SY007.
*>                        SY008.
*>                        SY009.
*>                        SY010.
*>                        SY013.
*> Module Specific.
*>                        SY011.
*>**
*>    Changes.
*> 04/10/11 vbc - .00 ACAS control program/module for OC v1.1 & v2.
*>                    This element MUST be compiled with -x and all the
*>                    main system programs compiled with -m.
*> 18/11/11 vbc - .03 Added IRS to menu but marked out until sorting out
*>                    env variables eg, ACAS_IRS and ACAS_LEDGERS
*>                    by adding the path to ALL file names
*>                    [ Done for v3.02. ]
*> 28/04/13 vbc - .04 Changed call to sub-systems without 'using'.
*> 09/08/13 vbc - .05 wsnames using copybook version that support entire
*>                    ACAS system but currently excluding IRS.
*>                    [ Done for v3.02 ]
*> 21/09/15 vbc - .06 Suport for setting up the parameter file within
*>                    and optionally removing the same for all sub systems.
*> 27/10/16 vbc - .07 Support for calling IRS as of v3.02.
*>                    Some coding in set paths so only done once &
*>                    and not in sales, purchase, stock, general & irs
*>                    when called by this program unit.
*>                    Full RDB support but this uses the cobol system file.
*> 09/11/16 vbc - .08 Updated coding to support call to sys002 in set up.
*>                    without mapser as now in sys002.
*> 08/12/16 vbc - .09 Merged RDB & IRS support. Mysql for v3.02.
*> 28/08/17 vbc - .10 Init. work for ACAS-Setup here but may move
*>                        to separate program.
*> 04/11/17 vbc - .11 Removed references to 'in copybook' for includes.
*>                    additional comments in regard to program purpose
*>                     and functions.
*> 08/03/18 vbc - .12 Removed Cancel after call to modules - not needed for
*>                    GC, Msg IR011 renamed SY011, added footnote to menu
*>                    selections.
*> 08/04/18 vbc - .13 Add in call to sl070 if running for 1st time to create Vale / Anal recs.
*> 28/05/18 vbc - .14 Added tests for terminal column and lines minima for => 80 / 24.
*> 24/09/18 vbc - .15 Set the wait msg at EOP to OFF.
*> 18/06/20 vbc - .16 On checking for term width,length & values wrong display
*>                    and redo test. Just aborted before if not => 80 x 24 !
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 26/12/24 vbc       Change menu ACCEPT to use UPPER and remove the function.
*> 31/08/25 vbc   .17 Removed from menu options of systems not available.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supercedes all prior copyright notices & was updated 2024-04-16.
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
*>******************************************************************************
*> SUPPORT / Maintainance Service:
*>===============================
*> Support for the ACAS system is available:
*>     Free via email on an as time is available basis ONLY.
*>
*>     Paid for [Normal] subscription, via email/phone as required
*>      by customer within normal office hours Monday through Friday
*>       10:00 - 17:00 UTC. Response times within 4* hours E&OE.
*>       This is currently  £250.00 per year.
*>
*>     Paid for [W/E] subscription, via email/phone as required by customer
*>       outside normal office hours and the weekend. Response within 2* hour
*>       E&OE.
*>       This is currently  £400.00 per year and includes Normal service.
*>       One weekend only fee is £225.00. By arrangement, <= 1 hour.
*>
*>  Email to vbcoen@gmail.com for details of subscriptions or for support
*>  with subject 'ACAS Bug' for support or 'ACAS subscription' for paid
*>   service.
*>
*>  * Response times are usually within one hour but can be longer subject to
*>  other outstanding issues. All issues marked as 'critical' are one hour.
*>  The above response times are for paid subscription service only.
*>
*>*************************************************************************
*>
 environment             division.
*>===============================
*>
 copy  "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 data  division.
*>=============
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(15)    value "ACAS (3.3.00)".
 77  z                   binary-char.
 77  OS-Delimiter        pic x        value "/".     *> Preset for Linux/unix etc
 77  ACAS_BIN            pic x(512)   value spaces.  *> added
 77  ACAS_LEDGERS        pic x(500)   value spaces.
 77  Arg-Number          pic 9        value zero.
*>========================================================
*>  in case file layout upgrade is needed.
*>   Using a file update program.
*>
 copy "sys-params-versioning.cob".
*>^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*> Holds program parameter values from command line
 01  Arg-Vals                         value spaces.
     03  Arg-Value       pic x(525)  occurs 2.
 01  Arg-Test            pic x(525)   value spaces.
*>
 01  ws-data.
     03  menu-reply      pic x          value "A".
     03  op-display      pic x(6).
*>
     03  ws-env-columns  pic 999       value zero.
     03  ws-env-lines    pic 999       value zero.
*>
     03  letters-upper   pic x(26)      value "ABCDEFGHIJKLMNOPQRSTUVWXYZ".
     03  letters.
         05  a-entry     pic x          occurs 26 indexed by q.
*>
     03  ws-reply        pic x.
     03  a               pic 99         comp.
     03  option-list     pic x(60).
     03  wsmaps-ser.
         05  wsmaps-ser-xx pic xx.
         05  wsmaps-ser-nn pic 9(4).
*>
 copy "wstime.cob".
 copy "wsfnctn.cob".
 copy "wsmaps01.cob".
 copy "wsmaps03.cob".
 copy "wscall.cob".
 copy "wssys4.cob".
 copy "wsdflt.cob".
 copy "wsfinal.cob".
 copy "wsnames.cob".
*>
 copy "wssystem.cob"        *> NEW for v3.02
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
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide
     03  SY006           pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007           pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008           pic x(31) value "SY008 Note message & Hit return".
     03  SY009           pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 24".
     03  SY011           pic x(47) value "SY011 Error on systemMT processing, Fs-reply = ".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*> Module specific
*>
 01  to-day              pic x(10).
*>
 procedure division.
*>=================
*>
 ACAS-Main.
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
*>
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     set      ENVIRONMENT "COB_EXIT_WAIT"  to "N".
     move     function current-date to wse-date-block.
*>
 Get-Term-Settings.
     accept   ws-env-lines   from lines.
     if       ws-env-lines < 24
              display SY010    at 0101 with erase eos
              accept  ws-reply at 0133
              go to Get-Term-Settings.
     accept   ws-env-Columns from Columns.
     if       ws-Env-Columns < 80
              display SY013    at 0101 with erase eos
              accept  ws-reply at 0133
              go to Get-Term-Settings.
*>
*> Only needed for this program as all called subsystem does it.
*>
     perform  zz020-Get-Program-Args.
*>
 Open-System.
*>
*> First check if this is the first time system has been used & if so
*>  set up the ACAS system parameter file & table
*>  Then call the set up for :
*>   Analysis
*>   IRS ledger using the pre created COA-data file.
*>   IRS defaults  VAT in and out for UK usage << may be.
*>
*>
     move     zeros to File-System-Used
                       File-Duplicates-In-Use.  *> Force Cobol proc.
     move     1 to File-Key-No.
     perform  System-Open-Input.      *> as I/O
     if       fs-reply not = zero
              perform  System-Close
              move     zero to ws-term-code
              move     "sys002" to ws-called
              call     ws-called using ws-calling-data file-defs   *> and we use file00.
              if       ws-term-code > 7
                       stop run
              end-if
*>
*>  HERE to add the extra set up program calls.
*>
              move     1 to File-Key-No
              perform  System-Open-Input      *> as I/O
              if       fs-reply not = zero
                       display " " at 0101 with erase eos
                       display SY011     at 1201
                       accept Menu-Reply at 1260
                       stop run
              end-if
              perform  System-Close
*>
*>  Set up Value and Anal file / tables.
*>
              move     zero to ws-term-code
              move     1    to ws-Process-Func    *> Force finish after creating recs for SL and PL.
              move     "sl070" to ws-called
              call     ws-called using ws-calling-data file-defs
*>
*>  Any more pre-setups? if so, put here.
*>
     end-if.
     perform  System-Read-Indexed.
     perform  System-Close.
*>
     if       scycle = zero
              go to call-system-setup.
*>
     move     ACAS-Run-Date to u-bin.
     call     "maps04" using maps03-ws.
     move     u-date to to-day.
     perform  zz060-Convert-Date.
*>
 Display-Menu.
*>
     display  usera at 0101  with erase eos foreground-color 3.
     move     to-day to u-date.
     move     "ACAS" to ws-caller.
     move     spaces to ws-called ws-del-link menu-reply.
     move     zeros to ws-term-code.
     display  maps-ser-xx at 2474 with foreground-color 3.
     move     maps-ser-nn to curs2.
     display  curs2 at 2476  with foreground-color 3.
     display  "Copyright (c) 1976-" at 2401 with foreground-color 3.
     display  wse-year at 2420 with foreground-color 3.
     display  " Applewood Computers" at 2424 with foreground-color 3.
*>
 Conv-date.
*>
*> Convert from UK to selected form
*>
     if       Date-Form not > zero and < 4
              move 1 to Date-Form.
     if       Date-USA
              move u-date to ws-date
              move ws-days to ws-swap
              move ws-month to ws-days
              move ws-swap to ws-month
              move ws-date to u-date
     end-if
     if       Date-Intl
              move "ccyy/mm/dd" to ws-date   *> swap Intl to UK form
              move u-date (7:4) to ws-Intl-Year
              move u-date (4:2) to ws-Intl-Month
              move u-date (1:2) to ws-Intl-Days
              move ws-date to u-date
     end-if.
*>
 conv-date-end.
     display  u-date at 0171 with foreground-color 3.
*>
 Display-Go.
*>
     display  prog-name at 0301 with foreground-color 2.
     display  "ACAS System Menu" at 0333 with foreground-color 2.
*>
     accept   wsb-time from time.
     if       wsb-time not = "00000000"
              move wsb-hh to wsd-hh
              move wsb-mm to wsd-mm
              move wsb-ss to wsd-ss
              display "at " at 0355 with foreground-color 2
              display wsd-time at 0358 with foreground-color 2.
*>
     accept   wsa-date from date.
     if       wsa-date not = "000000"
              move wsa-yy to u-year
              move wsa-mm to u-month
              move wsa-dd to u-days
              display "on " at 0367 with foreground-color 2
              perform conv-date
              display u-date at 0370 with foreground-color 2.
*>
     display  "Select one of the following by letter  :- [ ]" at 0601 with foreground-color 2.
*>
     display  "(A)  Nominal Ledger (IRS)" at 1004 with foreground-color 2.
     display  "(D)  General Ledger"  at 1044 with foreground-color 2.
*>
     display  "(B)  Sales Ledger"    at 1104 with foreground-color 2.
     display  "(C)  Purchase Ledger" at 1144 with foreground-color 2.
*>
     display  "(E)  Stock Control"   at 1204 with foreground-color 2.
*>     display  "(J)* Project-Z        at  1244 with foreground-color 2.
*>
 *>    display  "(F)* Order Entry"     at 1304 with foreground-color 2.
 *>    display  "(G)* Payroll"         at 1344 with foreground-color 2.
*>
 *>    display  "(H)* Epos"            at 1404 with foreground-color 2.
     display  "(X)  Exit To system"  at 1444 with foreground-color 2.
*>
     display  "(Z)  System Setup"    at 1644 with foreground-color 2.
*>
 *>    display  "* = Not available for O/S versions" at 1844 with foreground-color 2.
*>
 accept-loop.
*>
     accept   menu-reply at 0644 with foreground-color 6 auto UPPER.
*>
     if       menu-reply = "X"
 *>              display " " at 0101 with erase eos
              go to pre-overrewrite.
*>
     move     zero to z.
     move     letters-upper to letters.
     set      q to 1
     search   a-entry
              when a-entry (q) = menu-reply
              set z to q.
     if       z = zero
              go to accept-loop.
*>
     go       to load-it.
*>
 call-system-setup.
*>****************
*>
*> MAYBE NEED TO ADD EXTRA TO SET UP OTHER DATA FILES inc. anal, stock
*>         IRS / GL, sales, purchase etc
*>
     move     zero to ws-term-code.
     move     "sys002" to ws-called.
     call     ws-called using ws-calling-data
                              file-defs.
     if       ws-term-code > 7
              stop run.
     go       to Open-System.
*>
 pre-overrewrite.     *> Don't need to save system data as done by called menu program.
 overrewrite.
*>
 overclose.
     goback.
*>
 load-it.
*>******
*>
     move     space to menu-reply.
*>
*>   Order is :
*>    A=irs=08 , B=sales=02 , C=purchase=03 , D=General=01 ,
*>    E=stock=04 ,
*>    F=none, G=none, H=none= 5,6,7 Not avail for O/S versions.
*>    X= , Z=setup=
*>
     go       to load08 load02 load03 load01
                 load04
                 loadsr2 loadsr2 loadsr2
                 loaderror loaderror loaderror loaderror
                 loaderror loaderror loaderror loaderror
                 loaderror loaderror loaderror loaderror
                 loaderror loaderror loaderror loaderror
                 loaderror call-system-setup
              depending on z.
*>
 loaderror.
*>--------
*>
     go       to display-menu.
*>
 load00.
*>-----
*>
     move     zero to ws-term-code.
     call     ws-called        *> using ws-calling-data system-record to-day.
     if       ws-term-code > 7
              go to overrewrite.
*>
 load00-exit.
*>
     go       to display-menu.
*>
 load01.
*>-----
*>
     move     "general" to ws-called.
     go       to load00.
*>
 load02.
*>-----
*>
     move     "sales" to ws-called.
     go       to load00.
*>
 load03.
*>-----
*>
     move     "purchase" to ws-called.
     go       to load00.
*>
 load04.
*>-----
*>
     move     "stock" to ws-called.
     go       to load00.
*>
 load05.
*>-----
*>
     move     "OE" to ws-called.
     go       to load00.
*>
 load06.
*>-----
*>
     move     "payroll" to ws-called.
     go       to load00.
*>
 load07.
*>-----
*>
     move     "epos" to ws-called.
     go       to load00.
*>
 load08.
*>-----
*>
     move     "irs" to ws-called.
     go       to load00.
*>
 load09.
 *>----
     move     "project-z" to ws-called.
     go       to load00.
 load23.
*>-----
*>
     go       to accept-loop.
*>
 loadsr.
*>-----
*>
     display  "Sorry, not available" at 2331 with foreground-color 2.
     go       to accept-loop.
*>
 loadsr2.
*>------
*>
     display  "* Sorry, available on O/S versions" at 2331 with foreground-color 2.
     go       to accept-loop.
*>
 main-exit.
     stop     run.
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
     perform  maps04.
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
 maps04       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
 zz100-ACAS-IRS-Calls  section.
*>============================
*>
*>  Note irsub2 is replaced by acas000 with File-Key-No=1
*> ******************************************************
*>
*> acas000     =  System parameter file processing with File-Key-No=1
*>
 acas000.
     move     1 to File-Key-No.         *> Only using system record (rrn = 1)
     call     "acas000" using
                                WS-System-Record
                                File-Access
                                File-Defs
                                ACAS-DAL-Common-data
     end-call.
*>
*> acas000     =  System parameter file processing with File-Key-No=1
*>
*>   Needs File-Key-No set to 1 (for system param record)
*>
 System-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas000.
     perform  System-Check-4-Errors.
*>
 System-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  System-Check-4-Errors.
     perform  acas000.
*>
 System-Close.
     set      fn-Close to true.
     perform  acas000.
*>
 System-Read-Next.
     set      fn-Read-Next to true.
     perform  acas000.
*>
 System-Read-Indexed.
     set      fn-Read-Indexed to true.
     perform  acas000.
*>
 System-Write.
     set      fn-Write to true.
     perform  acas000.
*>
 System-Rewrite.
     set      fn-re-write to true.
     perform  acas000.
*>
 System-Check-4-Errors.
     if       fs-reply not = zero
              display SY011            at 0801   *> acas000/systemMT processing
              perform System-Close
              go to Open-Error-Continued
     end-if.
*>
 Open-Error-Continued.   *> If here we cannot continue as its a major failure
     display  "Fs-reply = "    at 0901
     display  fs-reply         at 0912
     display  "WE-Error = "    at 1001
     display   WE-Error        at 1012
     display  SQL-Err          at 1101
     display  SQL-Msg          at 1201
     display  SY008            at 1301 with erase eol
     accept   Accept-Reply     at 1335.
     goback.
*>
 copy "Proc-Get-Env-Set-Files.cob".  *> Only uses ACAS_LEDGERS now
*>
