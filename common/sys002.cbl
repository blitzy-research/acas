       >>source free
*>*****************************************************************
*>                                                                *
*>       S Y S T E M   F I L E   M A I N T E N A N C E            *
*>                                                                *
*>      Now includes initial file records/tables creation         *
*>          instead of needed to be in each sub system            *
*>                  as of v3.02.48                                *
*>                                                                *
*>*****************************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         sys002.
*>**
*>    Author.             Cis Cobol Conversion By Vincent Coen FBCS, FIDM, FIDPM, 31/10/82
*>                        for Applewood Computers.
*>                        Migration to OC / GunCobol January 2009 by Vincent Coen.
*>**
      Date-compiled.
*>**
*>    Security.           Copyright (C) 1976 - 2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            System File Maintenance  User Parameters.
*>**
*>    Version.            See Prog-Name in ws.
*>**
*>    Called Modules.
*>                        maps04
*>                        acas000   ->
*>                         systemMT DAL For RDB.
*>**
*>    Error messages used.
*> System Wide:
*>                        SY005.
*>                        SY006.
*>                        SY007.
*>                        SY008.
*>                        SY009.
*>                        SY010.  from Mapser.
*>                        SY044.      *> Not in use for OS versions.
*>                        SY045.      *> Not in use for OS versions.
*> Module Wide:
*>                        SY101.
*>                        SY102.
*>                        SY103.
*>                        SY104.
*>                        SY105.
*>                        SY106.
*>                        SY107.
*>                        SY108.
*>                        SY109.
*>                        SY110.
*>                        SY111.
*>                        SY902.
*>**
*>  Changes.
*> 06/01/85 vbc - Support gl workfiles as op-disk (1).
*> 07/01/85 vbc - Offer choice for print out.
*> 12/02/02 vbc - Y2K support.
*> 29/01/09 vbc - Migration to Open Cobol. Removed all security and
*>                encryption code & data as this code can go world wide.
*>                Now removed from all Accounts systems on SVN. Full copy
*>                now held on encrypt partition. Files back to flat.
*>                Removed op-disks as no longer used.
*> 29/03/09 vbc - Support for using IRS instead of GL.
*> 06/04/09 vbc - GL/IRS account capture in PL plus PL data clean up
*>                ditto SL accounts also captured. More info printed.
*> 08/04/09 vbc - Environment vars ACAS_IRS & LEDGERS reported on.
*> 02/05/09 vbc - Added Stock set up + very basic OE (in Stock params).
*> 12/05/09 vbc - Cosmetic on Stock printout.
*> 01/06/09 vbc - Added Sales and/or Purchase Stock link.
*> 02/06/09 vbc - Align P/L & S/L values and other little cleanups on report.
*> 04/06/09 vbc - .08 Fix audit no on screen to 999.
*> 06/06/09 vbc - .09 Adjust defaults for Todate period to Yearly.
*> 09/06/09 vbc - .10 Offer escape out of first screen to quit program.
*> 29/06/09 vbc - .11 Adust periods for Stock params.
*> 04/07/09 vbc - .12 Convert error msgs to ACAS std ie, SYnnn format.
*> 07/09/10 vbc - .14 Added lpi, cpi & page-top to CUPS lpr print command.
*> 14/09/10 vbc - .15 Added Cob Env variables presets
*>                    added ops-Data-2 data - print-spool-Name.
*> 15/09/10 vbc - .16 Force system-record initialize if not found.
*> 16/11/11 vbc - .17 Force case on accepting sl-own-nos, SL-Stock-Link, PL-Stock-Link and some others.
*>                .18 Added system wide print lines under system params after collecting company address.
*>                .19 Moved printed system wide print lines to User params.
*> 17/11/11 vbc - .20 Remove most of Payroll on Open source versions
*>                .21 In init of NEW system file, set file layout version to rec 1.
*>                .22 Page-lines not checked > 28.
*> 18/11/11 vbc - .23 If esc is entered on 1st screen, system-files was not closed
*> 19/11/11 vbc - .24 Force date format to be UK on creating new system rec 1 in case
*>                    user does not set it and open system file with lock.
*> 04/12/11 vbc - .25 Added Delivery on display and report for debugging but temp left as changeable.
*> 10/12/11 vbc - .26 Support for User Post code/Zip, Country and local tax (or vat rates 4 & 5)
*>                    Global support for date format and now set into common system data area,
*>                    raised system version to 3.01 to match across all ACAS sub systems.
*> 11/12/11 vbc - .27 Removed all proc for stk-Date-form from Stock data and replaced with just Date-Form in General.
*> 26/12/11 vbc - .28 Included common code (zz010, zz020) used by All ACAS modules needed as can be called
*>                     by any of the sub-systems. Called to dummy area but creates paths etc in WS.
*> 04/03/12 vbc - .29 Added support for Duplicate file type processing + MS SQL Server rdbms.
*>                    Added screen function control but only Standard Cobol in use.
*> 09/04/12 vbc - .30 Added RDBMS screens and reporting.
*> 17/04/13 vbc - .31 Added init for final record within system.dat.
*> 20/04/13 vbc - .32 Remarked out code to rebuild file paths etc as done in menus + format issue for delivery tag
*> 26/04/13 vbc - .33 Force writes for all record types, build paths by including code in .32
*> 27/04/13 vbc - .34 Make Stk-Page-Lines same as System Page-Lines if zero. Shouldt we only be using system lines?
*> 15/05/13 vbc - .35 Reworded screen for Stk-Activity-Rep-Run.
*> 20/05/13 vbc - .36 Added SL screen 2 for Print co. addr info on Invoices, Statements, Delivery, & letters
*>                    etc. Also added VAT print request in exist user data screen.
*>                .37 Bug in above in print layout.
*> 04/06/13 vbc - .38 Missing Name for Print Lines in user params print, adding spool names 2 & 3,
*>                    remove stk-page-lines as using system page-lines only.
*> 30/06/13 vbc - .38 Change printed rdbms password from SECRET to 'It's SECRET' just in case someone
*>                    assumes thats the password :)
*> 22/09/15 vbc - .39 Added support for Param-Restrict.
*> 25/06/16 vbc - .40 Added in the RDBMS fields Host, Socket, Port and with increased System-Data-Block
*>                    from 384 to 512 and removed the unused Order-Entry-Block.
*>                    System Record version changed from 1.1 to 1.2 > 1.3 (25/08/16).
*>                    Updated Ops data 3 to include new fields and likewise the report.
*> 17/07/16 vbc - .41 Added tests for content of "LC_TIME" when creating virgin param file.
*>                    Date type can still be over-ridden by user.
*>                    Uses "SET" to do so.
*> 25/08/16 vbc - .42 (& see .40 note) increased size of RDBMS-SOCKET from 32 to 64 so increased l5-Data-2
*>                    by 4 and likewise the screen area for it & increased rec version to 1.3.
*> 17/09/16 vbc - .43 When using initialize on new param file use 'with filler'.
*>                    initialise IRS-Entry-Block if chars 1 thru 10 = spaces
*>                    in preparation for usage at some point when I get round to it
*>                    but needed for rdbms load.
*>                    if  System-Record-Version-Prime is zero set to 1.
*>                    as old bug not cleared in data.
*> 18/09/16 vbc - .44 For PL & SL the delimiter MUST not be '\' or '/' if using
*>                    RDBMS (Mysql or Mariadb) if it is entered its changed to
*>                    the default '!' - they don't like it no idea why as cannot see
*>                    it in A manual as A problem. Also if space entered changed to '!'.
*>                    Finding this took 6 hours !!!
*> 19/09/16 vbc - .45 Removed cosmetic error on printing no addr4 with postcode,country.
*>                    Adding in RDB processing using DAL - systemLD .
*>                    Increased versioning from 3.01 to 3.02.
*>                    This program will directly use cobol files AND call the RDB DAL
*>                    as the system parameter file MUST be first accessed for RDB connect
*>                    data.
*> 29/09/16 vbc - .46 Forgot to perform systemMT-Close and spurious if test in rdb error test
*>                    was going to be some thing but have forgotten so remed out for now.
*>                    Also forgot to set up DB- vars from param files RDBMS vars.
*> 16/10/16 vbc - .47 Changes to support integrated irs that uses RDB with
*>                    normal param file (system) along with dflt replacing
*>                    irsub2, 3 & 5 with acasirs2, 3 & 5 along with
*>                    systemMT, dfltMT & finalMT .
*>                    This version can use Cobol files instead of rdb but
*>                    using the same directory for the rest of ACAS with IRS.
*>                    version will be 3.02.nnn for all new changes where
*>                    nnn is the build number as usual.
*>                    Reposition report for G/L with Question regarding
*>                    IRS Usage. Do need to NOT printout G/L only data if IRS used.
*>                    Cleaned up Address & Postcode on report if addr-4 space (.44).
*>                    Add space before prog name in reports for idiot printers
*>                    loosing 1st char on 2nd page
*>  2Badded -         New block instead of O/E for IRS unique data IF USED.
*> 29/10/16 vbc - .48 Added in all Mapser processing instead of being in each
*>                    of the sub systems e.g., General, Sales, Purchase, Stock & IRS.
*>                    REMEMBER TO REMOVE such code from those !!!
*> 26/11/16 vbc - .49 Added in system set up & screens from irs.
*>                    Modified request if IRS to be used to include :
*>                    YES | NO | BOTH
*>                    Printed out in place of redundant O/E.
*>                    Move first three ACAS vat rates to IRS vat1,2 & 3.
*> 09/12/16 vbc - .50 Put back disp " " to erase eol as display SC 01 and
*>                    erase eol does not work.  Bug in compiler?
*>                    Removed usage of ACAS_IRS replaced by ACAS_BIN in report.
*> 11/12/16 vbc - .51 Extra checks for temp sys rec size + setting file-key-no
*>                    before rewrite of system rec that was missing.
*> 25/04/17 vbc - .52 At start open param as input to test if exists not I/O
*>                    as it will create if not exist.
*> 15/01/18 vbc - .53 Added in User-Data date-form comment for start & end dates
*>                    and added WS-Year9 with WS-Year for new sys field
*>                    Stats-Date-Period filled from start date year as stats
*>                    work on 01 Jan to 31 Dec periods within sales, purch ledgers
*>                    clearing down at end of year and value moving this to last.
*> 31/01/18 vbc - .54 Amended comments for ledger-2nd-index as not used and
*>                    Cleaned up PC or Branch to indicate one or other or blank
*>                    Updated ACAS list of files and tables at WS-file-Names
*>                    notes for reference.
*> 03/02/18 vbc - .55 File dups removed.
*> 07/02/18 vbc - .56 Clean display for user-Data cycle msg with erase eol
*>                    Remove File Dup processing in user-Data accept checks
*>                    Give msgs for printing or not of Co. Name/addr on letters
*>                    invoices, statements and picking lists.
*>                    Removed processing for password, bit pointless with Linux
*>                    and Windows systems user security.
*>                .57 Under SL-Data added missing VAT-Ac and Next-Invoice.
*>                    Also test and set etc for both so extended data lines to 23.
*>                    Those 2 have been missing for 30+ years!
*>                    but not sure that Vat-ac is in use  anywhere so will check
*>                    against xref for all modules soon <<---
*> 10/02/18 vbc - .58 Add missing PL-Approp-AC6 capture and its flag &
*>                    print under System parameters.
*> 18/03/18 vbc - .59 Added new field in System params SL-Invoice-Lines.
*>                    Once supported this will allow the max lines per invoice
*>                    to be controlled by the user.
*>                    At the moment this count will be used on Invoices and
*>                    Picking / Packing lists.
*>                    This will not affect invoice entry or amend routines.
*>                    Added print item - Prt Max items in Inv. params. at aa8.
*> 09/04/18 vbc - .60 Tidy up SL data 1 screen as getting overwrites.
*> 13/04/18 vbc - .61 Fixed missing Env and op system info added restrict param
*>                    info.
*> 15/04/18 vbc - .62 Use WS for binary fields VAT-AC, Next-Invoice as GC
*>                    does NOT convert. There is more.......
*>                    So why does GC not handle them and do autoconversion ?
*> 28/04/18 vbc - .63 Remarked out in Stock section the removed audit stuff
*>                    that is now compulsory.
*> 01/06/20 vbc - .64 IN #53 did not add this field to report - added.
*>                    Underline pos. for System Parameters missing A *
*> 03/06/20 vbc - .65 Changed validation for RDBMS processing reporting to use
*>                    MySQL and not generic.
*> 07/12/22 vbc - .66 Chgd Vars A & B to pic 999 to keep GC v3.2 happy.
*>                    Add A para name for each section where there is A goto to
*>                    start of section as GC v3.2 complains.
*> 03/04/23 vbc - .67 Scrren bad pos. for comment re date types.
*> 20/04/23 vbc - .68 Updated file table as included 2 new files slautogn and plautogn
*>                    as files 04  &  30.
*> 26/06/23 vbc - .69 Added Company Email address collection and reporting.
*> 23/08/23 vbc       Restored code from nightly backup as wrongly overwritten , DER !
*> 10/09/23 vbc - .70 Added in OE to Mapser - currently no data entry needed for it.
*> 15/03/24 vbc - .71 Support for SL-BO-Flag and Stk-BO-Active. File size same.
*> 20/03/24 vbc - .72 Added SL-BO-Default.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 21/04/24 vbc   .73 BO defaults printed wrong (RH only). in SL-Params-Main added code
*>                    to zero 6 fields created since 2018 in filler area if any old
*>                    system params are around. Not sure they are used but...
*> 18/12/24 vbc   .74 Change default value for Page-Lines to 56 (Portrait).
*>                    Should have one for Landscape and not hard wired.
*>                    Display of line 22 cc40+ overwritten moved to Line 23.
*> 19/09/25 vbc - 3.3.00 Version update and builds reset.
*> 21/10/25 vbc - 3.3.01 Added Co. Phone no.
*> 25/11/25 vbc -    .02 Pre support for Payroll.
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
*> You should have received A copy of the GNU General Public License along
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
 file-control.
*>
 copy "selprint.cob".
 data                    division.
 file section.
*>-----------
*>
 copy "fdprint.cob".
 working-storage section.
*>----------------------
 77  Prog-Name            pic x(16)    value "SYS002 (3.3.02)".
 77  Error-Code           pic 999.
 77  Page-Nos             pic 99       value zero.
 77  OS-Delimiter         pic x        value "/".
 77  ACAS_BIN             pic x(512)   value spaces.  *> added
 77  ACAS_LEDGERS         pic x(500)   value spaces.
 77  Display-Blk          pic x(75)    value spaces.
 77  Arg-Number           pic 9        value zero.
 77  Z                    binary-char  value zero.
 77  Init-System-File-SW  pic 9        value zero.
 77  Init-Sys4-File-SW    pic 9        value zero.
 77  Init-Final-File-SW   pic 9        value zero.
 77  Init-Default-File-SW pic 9        value zero.
 77  WS-Saved-FS-Reply    pic 99.
 *>
*> Used For Changes In wssystem After Release
*>===========================================
*>  in case file layout upgrade is needed.
*>   Using A file update program.
*>
 copy "sys-params-versioning.cob".
*>
*>
*> Holds program parameter values from command line
*>
 01  Arg-Vals                          value spaces.
     03  Arg-Value       pic x(525)  occurs 2.
 01  Arg-Test            pic x(525)    value spaces.
*>
*>=========================================================================
*>  User changeable but may also need to be done system wide
*>    CUPS lpr command to spool print output & used for Linux, Unix & Mac.
*>                   Not standard in OS/2 but if so needs to be changed in
*>                   wssystem.cob and here (sys002).
*>
 copy "print-spool-command.cob".
 01  WS-Data.
     03  WS-Reply        pic x.
     03  A               binary-char.
     03  B               binary-char.
     03  AA-Size         pic 9(4)      value zero.
     03  BB-Size         pic 9(4)      value zero.
     03  P-Start         pic x(10)     value spaces.
     03  P-End           pic x(10)     value spaces.
     03  S-Pass-Word     pic x(4)      value spaces.
     03  To-Day          pic x(10)     value "dd/mm/yyyy".
     03  Used-Once       pic 9         value zero.
*>
     03  Option-List     pic x(60).        *> from stock.cbl
     03  wsmaps-ser.                       *>  ditto
         05  wsmaps-ser-xx pic xx.
         05  wsmaps-ser-nn pic 9(4).
*>
 01  filler.
     03  Num-1           pic z9.99.
     03  Num-1B          pic z9.99.
     03  Num-2           pic z(4)9.
     03  Num-3           pic 999.
     03  Num-4           pic z9.
     03  Num-5           pic z(6)9.
     03  Num-6           pic 9(5).
     03  Num-7           pic 9(8).
     03  Num-8           pic 9(6).
     03  Num-9           pic zz9.
     03  Temp-String     pic x(43).
     03  Temp-String2    pic x(20).
*>
*> Display fields from Binary data types.
*>
     03  WS-Next-Invoice pic 9(8).
     03  WS-Vat-AC       pic 9(6).
     03  WS-BL-Pay-Ac    pic 9(6).
     03  WS-P-Creditors  pic 9(6).
     03  WS-BL-Purch-Ac  pic 9(6).
     03  WS-SL-Limit     pic 9(7).
     03  WS-Next-Folio   pic 9(7).
     03  WS-Cyclea       pic 99.
*>
 01  WS-Test-Date            pic x(10).
 01  WS-Date-formats.
     03  WS-Swap             pic xx.
     03  WS-Conv-Date        pic x(10).
     03  WS-Date             pic x(10).
     03  WS-UK redefines WS-Date.
         05  WS-Days         pic xx.
         05  filler          pic x.
         05  WS-Month        pic xx.
         05  filler          pic x.
         05  WS-Year.
             07  WS-Year9    pic 9(4).               *> Added 15/01/18.
     03  WS-USA redefines WS-Date.
         05  WS-USA-Month    pic xx.
         05  filler          pic x.
         05  WS-USA-Days     pic xx.
         05  filler          pic x.
         05  filler          pic x(4).
     03  WS-Intl redefines WS-Date.
         05  WS-Intl-Year    pic x(4).
         05  filler          pic x.
         05  WS-Intl-Month   pic xx.
         05  filler          pic x.
         05  WS-Intl-Days    pic xx.
*>
 copy "wstime.cob".                                         *> used by ba000-Mapser (from stock.cbl)
*>
 01  WS-Locale              pic x(16)     value spaces.     *> Holds o/p from env var. LC_TIME but only uses 1st 5 chars
 01  WS-Local-Time-Zone     pic 9         value 3.          *> Defaults to International, See comments below !
*>
*> Set WS-Local-Time-Zone ^~^ to one of these 88 values according to
*>    your local requirements
*> NOTE Environment var. LC_TIME is checked for "en_GB" for UK (1)
*>                                          and "en_US" for USA (2)
*>   at start of program.
*>   For any other, you can add yours if different but let the Lead Programmer
*>     know, so it can be added to the master sources otherwise default will
*>      be Unix format
*>
*>    Note that 'implies' does NOT mean the program does anything e.g.,
*>        changes page sizing in the report.
*>
     88  LTZ-Unix                         value 3. *> ccyy/mm/dd  Also implies A4 Paper for prints
     88  LTZ-USA                          value 2. *> mm/dd/ccyy  [en_US] Also implies US Letter Paper for prints
     88  LTZ-UK                           value 1. *> dd/mm/ccyy  [en_GB] Also implies A4 Paper for prints
*>
*> copy "wsmaps01.cob".  *> Removed functions for paswords for O/S versions.
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "wssystem.cob".
*>
 01  WS-Temp-System-Record   pic x(1024).
*>
 copy "wsfinal.cob".
 copy "wssys4.cob".
 copy "wsdflt.cob".
*>
 01  accept-terminator-array pic 9(4)            value zero.
     copy "screenio.cpy".
*>
 01  Line-1.
     03  filler             pic x        value space.
     03  l1-Name            pic x(16).
     03  filler             pic x(34)    value spaces.
     03  filler             pic x(33)    value "S Y S T E M   P A R A M E T E R S".
     03  filler             pic x(26)    value spaces.
     03  Line-1-Date        pic x(10).
     03  filler             pic x(6)     value spaces.
     03  filler             pic x(4)     value "Page".
     03  l1-Page            pic z9.
*>
 01  Line-3a.
     03  filler             pic x(24)    value  spaces.
     03  filler             pic x(16)    value "User  Parameters".
     03  filler             pic x(40)    value  spaces.
     03  filler             pic x(16)    value "G/L   Parameters".
*>
 01  Line-3b.
     03  filler             pic x(24)    value  spaces.
     03  filler             pic x(16)    value "ACAS  Parameters".
     03  filler             pic x(40)    value  spaces.
     03  filler             pic x(16)    value "P/L   Parameters".
*>
 01  Line-3c.
     03  filler             pic x(24)    value  spaces.
     03  filler             pic x(16)    value "Inv.  Parameters".
     03  filler             pic x(40)    value spaces.
     03  filler             pic x(16)    value "S/L   Parameters".
*>
 01  Line-3d.
     03  filler             pic x(24)    value  spaces.
     03  filler             pic x(16)    value "Stock Parameters".
     03  filler             pic x(40)    value spaces.
     03  filler             pic x(16)    value "IRS   Parameters".
*>
 01  Line-3d2.
     03  filler             pic x(22)    value  spaces.
     03  filler             pic x(18)    value "Payroll Parameters".
     03  filler             pic x(40)    value spaces.
     03  filler             pic x(16)    value "RDMBS Parameters".
*>
 01  Line-3e.
     03  filler             pic x(23)    value spaces.
     03  filler             pic x(17)    value "System Parameters".
     03  filler             pic x(56)    value spaces.
*>
 01  Line-4.
     03  l4-part1.
         05  filler         pic x(24)    value  spaces.
         05  l4-part1-star  pic x(16)    value  all "*".
     03  l4-part2.
         05  filler         pic x(40)    value  spaces.
         05  l4-part2-star  pic x(16)    value  all "*".
*>
 01  Line-5.
     03  filler             pic x(10)    value  spaces.
     03  l5-files.
         05 l5-Name         pic x(17)    value  spaces.
         05 l5-Data-1       pic x(43)    value  spaces.
         05 filler  redefines  l5-Data-1.
            07  array-1     pic x        occurs  43.    *> 70
         05 l5-Data-2       pic x(62)    value  spaces.
         05 filler  redefines  l5-Data-2.
            07  array-2     pic x        occurs  62.
*>
*> spaxx is used in space clearing for displays.
*>
 01  Line-6.
     03  spaxx              pic x(51)    value  spaces.
     03  filler             pic x(30)    value  "End of System Parameter Report".
*>
 01  Line-7.
     03  filler             pic x(51)    value  spaces.
     03  filler             pic x(30)    value  all "=".
*>
*> Last updated 18/12/24.
*> 2023-04-20 vbc - Added SLautogn and PLautogn file04 & file30 for sales & Purchase
*>                  respectively for recurring invoices.
*> This was Effective 2024-03-15 :-
*> 2024-09-01 vbc - Added BOSTKITM file-31 handles Back Order records from Sales invoicing
*>                  Used in stock - st020 (stock additions), sl910 (sales invoicing) & sl970 BO reporting.
*> 2024-12-18 vbc - tidied up file 31 entry.
*>
*> This acts as A list of files used within the ACAS system so any changes,  update this block !!
*>       fillers with 'values space' can used for this purpose but could also be for SQL databases tables
*>  [File/system numbers with * do not use RDB] As unused or Temporary files used between processes / programs.
*>   C = Coding in progress.
*>   Y = Completed coding not dry tested yet.
*>   X = Completed with dry testing.
*>   - = Will not be converted as temp type files.
*>   ? = Not yet done.
*>   sp = Not used.  [ sp = space ]
*>
*>01  WS-file-Names.                       *>     FH DAL created ?
*>                Sys#  F#                          LD   created ?
*>    03  file00   0    10   value "system".      X X X *> Used by all systems: SL, PL, ST, GL, IRS
*>    03  filler             value "glwork".      - - - *>  DOES NOT APPEAR TO BE USED in general (maybe temp ?)
*>    03  file02   *    *    value "archive".     - - - *> General - Online and offline copies?
*>    03  file03   *    *    value "final".       - - - *> General temp file in gl120 P&L print
*>    03  file04   3    16   value "slautogn".    C - C *>   Sales Recurring invoices
*>    03  file05   2    11   value "ledger".      X X X *> General
*>    03  file06   2    12   value "posting".     X X X *> General & Sales & Purchase
*>    03  file07   2    13   value "batch".       X X X *> General & Sales & Purchase
*>    03  file08   1    15   value "postings2irs".X X X *>   Sales & Purchase
*>    03  file09   *    *    value "tmp-stock".   - - - *>  Stock temp file
*>    03  file10   5    13   value "staudit".     X X X *>  Stock
*>    03  file11   5    12   value "stockctl".    X X X *>  Stock - RDB
*>    03  file12   3    11   value "salesled".    X X X *>   Sales & Stock (used in??)
*>    03  file13   6    13   value "value".       X X X *>   Sales & Purchase
*>    03  file14   6    12   value "delivery".    X X X *>   Sales & Purchase
*>    03  file15   6    12   value "analysis".    X X X *>   Stock & Purchase
*>    03  file16   3    12   value "invoice ".    X X X *>   Sales
*>    03  file17   3    13   value "delinvno".    X X X *>   Sales
*>    03  file18   3*   14*  value "openitm2".    - - - *>   Sales  Temp file (sl055 -> sl060)
*>    03  file19   3    15   value "openitm3".    X X X *>   Sales
*>    03  file20   *    *    value "oisort".      - - - *>   Sales
*>    03  file21   *    *    value "work".        - - - *>   Sales, Purchase & General (temp)
*>    03  file22   4    11   value "purchled".    X X X *>   Purchase & Stock (used in??)
*>    03  file23   4    13   value "delfolio".    X X X *>   Purchase
*>    03  file24   *    *    value space.         - - - *> General - dummy for gl080
*>    03  filler             value space.               *>  UNUSED
*>    03  file26   4    12   value "pinvoice".    Y Y Y *>   Purchase
*>    03  file27   *    *    value "poisort".     - - - *>   Purchase
*>    03  file28   4*   14*  value "openitm4".    - - - *>   Purchase  temp file (pl055 -> pl060)
*>    03  file29   4    15   value "openitm5".    Y Y Y *>   Purchase
*>    03  file30   4    18   value "plautogn".    ? ? ? *>   Purchase Recurring invoices/folios
*>    03  file31   *    *    value "bostkitm"     - - - *>   Sales Back Orders [ File only as temp file ]
*>    03  file32   4    16   value "pay     ".    X X X *>   Purchase
*>    03  file33   *    *    value "cheque.dat".  ?     *>   Purchase  temp file.
*>  IRS files added 19/10/16 & 12/16 (38)
*>    03  file34   1    11   value "irsacnts.dat".X X X *>   IRS ex file 1 renamed
*>    03  file35   1    12   value "irsdflt.dat". X X X *>   IRS ex file 3 renamed
*>    03  file36   1    13   value "irspost.dat". X X X *>   IRS ex file 4 renamed
*>    03  file37   1    14   value "irsfinal.dat".X X X *>   IRS ex file 5 renamed
*>    03  file38   *    *    value "postsort.dat".- - - *>   IRS ex irs055 TEMP sort file.
*>
*> Code for Payroll  AND INCREASE occurs both times
*>    03  file-39         value "pyact".               *> PY account
*>    03  file-40         value "pychk".               *> PY check / bacs
*>    03  file-41         value "pycoh".               *> PY company history
*>    03  file-42         value "pyded".               *> PY deduction {/ earnings}
*>    03  file-43         value "pyemp".               *> PY employee master
*>    03  file-44         value "pyhis".               *> PY employee (pay) history
*>    03  file-45         value "pyhrs".               *> PY pay trans
*>    03  file-46         value "pypay".               *> PY pay detail jrn + header ???
*>    03  file-47         value "pypr1".               *> PY param 1
*>    03  file-48         value "pypr2".               *> PY param 2
*> TABLES Blk 1
*>    03  file-49         value "pycalm".              *> PY  calx - x = s,m,h, x?
*>    03  file-50         value "pycals".              *> PY
*>    03  file-51         value "pycalh".              *> PY
*>    03  file-52         value "pycalx".              *> PY  california special tables ???
*>    03  file-53         value "pylwt".               *> PY  tax table ???
*>    03  file-54         value "pyswtaa".             *> PY  swt aa = State abbrev. code Only one used
*>    03  file-55         value "pyglcoann".           *> PY gl CoA transfer ??
*>    03  file-56         value "pyglgjbss".           *> PY  ???
*> Not sure about these two up/down
  *>    03  file-57         value "pycal ".             *> PY  ??? calm,s,h etc
*>
*>     02  filler         redefines File-Defs-a.
*>         03  System-File-Names   pic x(532) occurs 58.            *> 58 chg for sales BO file plus py
*>     02  File-Defs-Count         binary-short value 58.           *> MUST be the same as above occurs
*>     02  File-Defs-os-Delimiter  pic x.                           *> if = \ or / then paths have been set.

*>
 01  Error-Messages.
*> System Wide
     03  SY005    pic x(18) value "SY005 Invalid Date".
     03  SY006    pic x(62) value "SY006 Program Arguments limited to two and you have specified ".
     03  SY007    pic x(35) value "SY007 Program arguments incorrect: ".
     03  SY008    pic x(31) value "SY008 Note message & Hit return".
     03  SY009    pic x(53) value "SY009 Environment variables not yet set up : ABORTING".
     03  SY010    pic x(59) value "SY010 Problem with opening system file. Hit return to clear".
     03  SY044    pic x(66) value "SY044 The system has detected an unauthorised change of user name.".
     03  SY045    pic X(40) value "SY045 Contact your Supplier or Sys Admin".
*> Module Specific
     03  SY101    pic x(21) value "SY101 Open I-O Err = ".
     03  SY102    pic x(19) value "SY102 Read Err 1 = ".
     03  SY103    pic x(22) value "SY103 Rewrite Err 1 = ".
     03  SY104    pic x(26) value "SY104 Fix and Press Enter".
     03  SY105    pic x(16) value "SY105 Lines > 28".
     03  SY106    pic x(34) value "SY106 Error on systemMT processing".
     03  SY107    pic x(32) value "SY107 Error on dfltMT processing".
     03  SY108    pic x(32) value "SY108 Error on sys4MT processing".
     03  SY109    pic x(33) value "SY109 Error on finalMT processing".
     03  SY110    pic x(29) value "SY110 Rerun Parameter Set up?".
     03  SY111    pic x(38) value "SY111 Print Spool Name must be defined".
*>
     03  SY902    pic x(32) value "SY902 Program Error: Temp rec = ".
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 linkage section.
*>==============
*>
 copy "wscall.cob".
*>
 copy "wsnames.cob".
*> So this block is not needed.
*>
 *> here deliberately and A dummy in linkage
*> Now that ALL modules use the full version next can go.
*>
*> 01  dummy-File-Defs.    *>    Dummy for the sub-system main module to call
*>     03  filler      pic x(532) occurs 35.
*>     03  Filler      binary-short  value zero.
*>
 screen section.
*>=============
*>
*> All encryption sub-systems removed, ditto all high security code
*>
 01  Banner        foreground-color 2.
     03  pic x(16) from Prog-Name                  line  1 col  1.
     03  value "S y s t e m   S e t - U p"                 col 28.
     03  from line-1-Date  pic x(10)                       col 71.
     03  value "++++++++++"                        line  3 col  1.
     03  value "+Screen "                          line  4 col  1.
     03  screen-nos       pic 9                            col  9.
     03                   pic x value "+"                  col 10.
     03  value "++++++++++"                        line  5 col  1.
*>
 01  User-Data       foreground-color 2.
     03          value "Name"                      line  7 col  1.
     03          value "- {"                               col  9.
     03  from Usera       pic x(32)                        col 12.
     03          value "}"                                 col 44.
     03          value "Address - ["               line  8 col  1.
     03  using Address-1  pic x(24)                        col 12.
     03          value "]"                                 col 36.
     03          value "["                         line  9 col 11.
     03  using Address-2  pic x(24)                        col 12.
     03          value "]"                                 col 36.
     03          value "["                         line 10 col 11.
     03  using Address-3  pic x(24)                        col 12.
     03          value "]"                                 col 36.
     03          value "["                         line 11 col 11.
     03  using Address-4  pic x(24)                        col 12.
     03          value "]"                                 col 36.
     03          value "Post Code ["               line 12 col  1.
     03  using Post-Code  pic x(12)                        col 12.
     03          value "]"                                 col 24.
     03          value "Phone No. ["                       col 41.
     03  using Phone-No   pic x(12)                        col 52.
     03          value "]"                                 col 64.
     03          value "Country - ["               line 13 col  1.
     03  using Country    pic x(24)                        col 12.
     03          value "]"                                 col 36.
     03          value "Date Format   "            line 14 col  1.
     03          value "- ["                               col 15.
     03  using Date-Form  pic 9                            col 18.
     03          value "]"                                 col 19.
     03          value "  (1 = UK, 2 = USA, 3 = Intl)"     col 20.
     03          value "Controls the next 2 fields"        col 50.   *> 03/04/23 - bad pos.
     03          value "Period :  Start Date - ["  line 15 col  1.
     03  using P-Start    pic x(10)                        col 25.
     03          value "]"                                 col 35.
     03          value "End   Date - ["            line 16 col 11.
     03  using P-End      pic x(10)                        col 25.
     03          value "]"                                 col 35.
     03          value "Stats Year ["                      col 40.   *> 15/01/18.
     03  using Stats-Date-Period pic 9(4)                  col 52.
     03          value "]"                                 col 56.   *> 03/02/18
     03          value "System Print Lines   -"    line 17 col  1.
     03          value "["                                 col 24.
     03  using Page-Lines pic 999                          col 25.
     03          value "]"                                 col 28.
     03          value "  (for Laser = 056)"               col 30.
 *>    03          value "["                                 col 41.
 *>    03  using Page-Lines-Land pic 999                     col 42.  *> Page-Lines-Land needs to be created..
 *>    03          value "]"                                 col 45.
     03          value "Vat Rates : (1)"           line 18 col  1.
     03          value "- ["                               col 22.
     03  using vat-rate-1 pic 99.99                        col 25.
     03          value "]"                                 col 30.
     03          value "Local Tax : (4)"                   col 40.
     03          value "- ["                               col 57.
     03  using vat-rate-4 pic 99.99                        col 60.
     03          value "]"                                 col 65.
     03          value "(2)"                       line 19 col 13.
     03          value "- ["                               col 22.
     03  using vat-rate-2 pic 99.99                        col 25.
     03          value "]"                                 col 30.
     03          value "Local Tax : (5)"                   col 40.
     03          value "- ["                               col 57.
     03  using vat-rate-5 pic 99.99                        col 60.
     03          value "]"                                 col 65.
     03          value "(3)"                       line 20 col 13.
     03          value "- ["                               col 22.
     03  using vat-rate-3 pic 99.99                        col 25.
     03          value "]"                                 col 30.
     03          value "Current Cycle"                     col 40.
     03          value "- ["                               col 58.
     03  using WS-cyclea  pic 99                           col 61.
     03          value "]"                                 col 63.
     03          value "VAT Reg no - ["            line 21 col  1.
     03  using VAT-Reg-Number  pic x(11)                   col 15.
     03          value "]"                                 col 26.
     03          value " Printed ["                        col 27.
     03  using SL-VAT-Printed                              col 37.
     03          value "]"                                 col 38.
     03          value "Current Quarter"           line 21 col 40.
     03          value "- ["                               col 58.
     03  using current-quarter pic 99                      col 61.
     03          value "]"                                 col 63.
     03          value "Comp. Email Address ["   line 22 col  1.  *> 21 chars
     03  using Company-Email  pic x(30)                    col 22.
     03          value "]"                                 col 52.
*>     03          value "Pass-Word"                 line 22 col 60.
*>     03          value "- ["                               col 70.
*>     03  using S-Pass-Word pic x(4)                        col 73.
*>     03          value "]"                                 col 77.
     03          value "Data File Handling"        line 23 col  1.
     03          value "- ["                               col 22.
     03  using File-System-Used pic 9                      col 25.
     03          value "]"                                 col 26.
     03          value "(Range 0/1)"                       col 28. *> char 39
*>     03          value "(Range 0/5)"                       col 28.  *> NOT IN USE
     03          value "Cycle Period"                      col 41.  *> 12 chars
     03          value "- ["                               col 59.  *> 3 chars
     03  using period     pic 99                           col 62.  *> 2 chars
     03          value "] Wk=13, Mth=03"                   col 64.  *> 15 chars = 32
     03          value "Escape to quit"            line 24 col 02.
*>
 01  Verify-Screen   foreground-color 2.
     03         value "**************************" line 11 col 54.
     03          value "*"                         line 12 col 54.
     03          value "*"                                 col 79.
     03          value "*"                         line 13 col 54.
     03  verify-message  pic x(24)                         col 55.
     03          value "*"                                 col 79.
     03          value "*"                         line 14 col 54.
     03          value "*"                                 col 79.
     03          value "* OK to file (Y/N) - ["    line 15 col 54.
     03          value "] *"                               col 77.
     03          value "*"                         line 16 col 54.
     03          value "                        "          col 55.
     03          value "*"                                 col 79.
     03         value "**************************" line 17 col 54.
*>
 01  OPS-Data       foreground-color 2.
     03      value "Restrict ACAS Params access [" line 15 col 2.
     03  using Param-Restrict     pic X                    col 31.
     03          value "]  (Y/N)"                          col 32.
     03          value "Single/Multi-User - ["     line 17 col 02.
     03  using host      pic 9                     line 17 col 23.
     03          value "]  (0=Single, 1=Multi)"    line 17 col 24.
     03          value "Operating System "         line 19 col 02.
     03          value "- ["                       line 19 col 20.
     03  using op-system  pic 9                    line 19 col 23.
     03          value "]"                         line 19 col 24.
     03          value "(1=Dos, 2=Windows," &
          " 3=Mac, 4=OS/2, 5=Unix, 6=Linux)"       line 19 col 27.
     03          value "Data capture System "      line 21 col 02.
     03          value "- ["                               col 22.
     03  using Data-Capture-Used  pic 9                    col 25.
     03          value "] 0=Std, 1=GUI, 2=Widget"          col 26.
*>
 01  OPS-Data-2     foreground-color 2.
     03        value "Cups Print Spooler name 1 - [" line 21 col 02.
     03  using Print-Spool-Name  pic x(48)                 col 31.
     03        value "]"                                   col 79.
     03        value "Cups Print Spooler name 2 - [" line 22 col 02.
     03  using Print-Spool-Name2 pic x(48)                 col 31.
     03        value "]"                                   col 79.
     03        value "Cups Print Spooler name 3 - [" line 23 col 02.
     03  using Print-Spool-Name3 pic x(48)                 col 31.
     03        value "]"                                   col 79.
*>
 01  OPS-Data-3     foreground-color 2.
     03          value "RDB Schema name - ["        line 7 col 02.
     03  using RDBMS-DB-Name   pic x(12)                   col 21.
     03          value "] (ACASDB)"                        col 33.
     03          value "DB Username - ["            line 8 col 02.
     03  using RDBMS-User      pic x(12)                   col 17.
     03          value "]"                                 col 29.
     03          value "DB User Password - ["       line 9 col 02.
     03  using RDBMS-Passwd    pic x(12)                   col 22.
     03          value "] "                                col 34.
     03          value "RDB Host - ["              line 10 col 02.
     03  using RDBMS-Host      pic x(32)                   col 14.
     03          value "] {localhost}"                     col 46.
     03          value "RDB Socket - ["            line 11 col 02.
     03  using RDBMS-Socket    pic x(64)                   col 16.
     03          value "]"                                 col 80.
     03          value "RDB Port - ["              line 12 col 02.
     03  using RDBMS-Port      pic x(5)                    col 14.
     03          value "] {3306 }"                         col 19.
*>
 01  GL-Data   foreground-color 2.
     03        value "Profit Centres/Branches - [" line  7 col  1.
     03  using p-c       pic x                             col 28.
     03          value "]"                                 col 29.
     03          value "  (P or B or space)"               col 30.
     03          value "P.C./Branches Level"       line  8 col  1.
     03          value "- ["                               col 25.
     03  using p-c-level pic x                             col 28.
     03          value "]"                                 col 29.
     03          value "  (R=Revenue, Space)"              col 30.
     03        value "P.C./Branches Grouped ? - [" line  9 col  1.
     03  using p-c-grouped  pic x                          col 28.
     03          value "]"                                 col 29.
     03          value "  (Y=Grouped or Space)"            col 30.
     03          value "Comparatives ?"            line 10 col  1.
     03          value "- ["                               col 25.
     03  using comps     pic x                             col 28.
     03          value "]"                                 col 29.
     03          value "  (Y=Yes or Space)"                col 30.
     03          value "Ledger Name Index ?"       line 11 col  1.
     03          value "- ["                               col 25.
     03  using ledger-2nd-index pic x                      col 28.
     03          value "]"                                 col 29.
     03          value "  (Y=Yes or Space)"                col 30.
     03          value " [Not currently used]"             col 50.
     03          value "Minimum Validation ?"      line 12 col  1.
     03          value "- ["                               col 25.
     03  using m-v       pic x                             col 28.
     03          value "]"                                 col 29.
     03          value "  (Y=Yes or Space)"                col 30.
     03          value "Archiving ?"               line 13 col  1.
     03          value "- ["                               col 25.
     03  using arch      pic x                             col 28.
     03          value "]"                                 col 29.
     03          value "  (Y=Yes or Space)"                col 30.
     03          value "Sales Range"               line 14 col  1.
     03          value "- ["                               col 25.
     03  using Sales-Range pic 9                           col 28.
     03          value "]"                                 col 29.
     03          value "Purchase Range"            line 15 col  1.
     03          value "- ["                               col 25.
     03  using Purchase-Range pic 9                        col 28.
     03          value "]"                                 col 29.
     03        value "Automatic VAT Posting ? - [" line 16 col  1.
     03  using vat       pic x                             col 28.
     03          value "]"                                 col 29.
     03          value "  (Y=Yes or Space)"                col 30.
     03          value "Next Batch Number"         line 17 col  1.
     03          value "- ["                               col 21.
     03  using Num-6 pic 9(5)                              col 24.
     03          value "]"                                 col 29.
*>     03   value "----------"                       line 18 col  1.
     03        value "Use IRS instead of GL ? - [" line 19 col  1.
     03  using IRS-Instead                                 col 28.
     03          value "]"                                 col 29.
     03          value "  (Y=Yes | N=No) B=Both"           col 30.
*>
 01  PL-Data   foreground-color 2.
     03          value "Delimiter"                 line 14 col  1.
     03          value "- ["                               col 15.
     03  using PL-Delim pic x                              col 18.
     03          value "]"                                 col 19.
     03          value "Purch/Stock Link  ["       line 15 col  1.
     03  using PL-Stock-Link pic x                         col 20.
     03          value "]"                                 col 21.
     03          value "Next Folio Number ["       line 16 col  1.
     03  using WS-Next-Folio pic 9(8)                      col 20.
     03          value "]"                                 col 28.
     03          value "Next Batch Number ["       line 17 col  1.
     03  using BL-Next-Batch  pic 9(5)                     col 20.
     03          value "]"                                 col 25.
     03         value "Pay Account       ["        line 18 col  1.
     03  using WS-BL-Pay-Ac   pic 9(6)                     col 20.
     03          value "]"                                 col 26.
     03         value "Ledger Account    ["        line 19 col  1.
     03  using WS-BL-Purch-Ac pic 9(6)                     col 20.
     03          value "]"                                 col 26.
     03         value "Creditor Account  ["        line 20 col  1.
     03  using WS-P-Creditors   pic 9(6)                   col 20.
     03          value "]"                                 col 26.
*>
 01  SL-Data   foreground-color 2.
     03          value "Late Letters"              line  7 col  1.
     03          value "- ["                               col 15.
     03  using sl-dunning pic 9                            col 18.
     03          value "]"                                 col 19.
     03          value "  (1 = Yes or 0)"                  col 20.
     03          value "Late Charges"              line  8 col  1.
     03          value "- ["                               col 15.
     03  using sl-charges pic 9                            col 18.
     03          value "]"                                 col 19.
     03          value "  (1 = Yes or 0)"                  col 20.
     03          value "Credit Period - ["         line  9 col  1.
     03  using sl-credit pic 99                            col 18.
     03          value "]"                                 col 20.
     03          value "Discount"                  line 10 col 1.
     03          value "- ["                               col 15.
     03  using sl-disc pic 99.99                           col 18.
     03          value "]"                                 col 23.
     03          value "Min Late Bal"              line 11 col  1.
     03          value "- ["                               col 15.
     03  using sl-min pic 9(4)                             col 18.
     03          value "]"                                 col 22.
     03          value "Max Late Charge ["         line 12 col  1.
     03  using sl-max pic 9(4)                             col 18.
     03          value "]"                                 col 22.
     03          value "Credit Limit"              line 13 col  1.
     03          value "- ["                               col 15.
     03  using WS-SL-Limit pic 9(7)                        col 18.
     03          value "]"                                 col 25.
     03          value "Delimiter"                 line 14 col  1.
     03          value "- ["                               col 15.
     03  using sl-delim pic x                              col 18.
     03          value "]"                                 col 19.
     03          value "  (Address lines)"                 col 20.
     03          value "Own Inv. Nos"              line 15 col  1.
     03          value "- ["                               col 15.
     03  using sl-own-nos pic x                            col 18.
     03          value "]"                                 col 19.
     03          value "Next Invoice Number ["     line 16 col  1.
     03  using WS-Next-Invoice pic 9(8)                    col 22.
     03          value "]"                                 col 30.
     03          value "Items per Invoice - ["             col 41.
     03  using SL-Invoice-Lines pic 99                     col 62.
     03          value "]"                                 col 64.
     03          value "Late Charge % - ["         line 17 col  1.
     03  using sl-late-per pic 9.99                        col 18.
     03          value "]"                                 col 22.
     03          value "Next Batch Number ["       line 18 col  1.
     03  using first-sl-batch pic 9(5)                     col 20.
     03          value "]"                                 col 25.
     03          value "Sales/Stock Link  ["       line 19 col  1.
     03  using SL-Stock-Link  pic x                        col 20.
     03          value "]"                                 col 21.
     03          value "BO Link - ["                       col 25.
     03  using SL-BO-Flag     pic x                        col 36.
     03          value "]"                                 col 37.
     03          value "BO Default - ["                    col 45.
     03  using SL-BO-Default  pic x                        col 59.
     03          value "]"                                 col 60.
     03          value "Pay Account    -  ["       line 20 col  1.
     03  using SL-Pay-Ac      pic 9(6)                     col 20.
     03          value "]"                                 col 26.
     03          value "Ledger Account -  ["       line 21 col  1.
     03  using SL-Sales-Ac    pic 9(6)                     col 20.
     03          value "]"                                 col 26.
     03          value "Debtors Account - ["       line 22 col  1.
     03  using S-Debtors      pic 9(6)                     col 20.
     03          value "]"                                 col 26.
     03          value "VAT Account   - ["         line 23 col  1.
     03  using WS-VAT-ac         pic 9(6)                  col 18.
     03          value "]"                                 col 24.
*>
 01  SL-Data-2   foreground-color 2.
     03  value "Select what report types, company details will be printed to"
                                                   line  7 col 01.
     03          value "    Invoices   - ["        line  8 col 01.
     03  using SL-Comp-Head-Inv   pic x                    col 19.
     03          value "]"                                 col 20.
     03          value "    Statements - ["        line  9 col 01.
     03  using SL-Comp-Head-Stat  pic x                    col 19.
     03          value "]"                                 col 20.
     03          value "  Late Letters - ["        line 10 col 01.
     03  using SL-Comp-Head-Lets  pic x                    col 19.
     03          value "]"                                 col 20.
     03          value "Delivery Notes - ["        line 11 col 01.
     03  using SL-Comp-Head-Pick  pic x                    col 19.
     03          value "]"                                 col 20.
*>
 01  Stock-Data   foreground-color 2.
     03          value "Debugging     "            line  7 col  1.
     03          value "- ["                               col 15.
     03  using stk-debug      pic 9                        col 18.
     03          value "]"                                 col 19.
     03          value "  (1 = Yes or 0)"                  col 20.
     03          value "Bomp/Wip used "            line  9 col  1.
     03          value "- ["                               col 15.
     03  using stk-Manu-Used  pic 9                        col 18.
     03          value "]"                                 col 19.
     03          value "  (1 = Yes or 0)"                  col 20.
*>
     03          value "Order Entry   "            line 10 col  1.
     03          value "- ["                               col 15.
     03  using stk-OE-Used    pic 9                        col 18.
     03          value "]"                                 col 19.
     03          value "  (1 = Yes or 0)"                  col 20.
*>
     03          value "Stock BO Flag "            line 11 col  1.
     03          value "- ["                               col 15.
     03  using Stk-BO-Active  pic x                        col 18.
     03          value "]"                                 col 19.
     03          value "  (Y = Yes or N)"                  col 20.
*>
 *> ALWAYS ON FOR BOTH.  14/03/18
*>     03          value "Audit Used    "            line 11 col  1.
*>     03          value "- ["                               col 15.
*>     03  using stk-Audit-Used pic 9                        col 18.
*>     03          value "]"                                 col 19.
*>     03          value "  (1 = Yes or 0)"                  col 20.
*>     03          value "Audit Movement"            line 12 col  1.
*>     03          value "- ["                               col 15.
*>     03  using stk-Mov-Audit  pic 9                        col 18.
*>     03          value "]"                                 col 19.
*>     03          value "  (1 = Yes or 0)"                  col 20.
     03          value "Current Period"            line 13 col  1.
     03          value "- ["                               col 15.
     03  using stk-Period-Cur pic x                        col 18.
     03          value "]"                                 col 19.
     03   value "  (W=Weekly, M=Monthly, Q=Quarterly)"     col 20. *>   14/03/18
     03          value "To Date Period"            line 14 col  1.
     03          value "- ["                               col 15.
     03  using stk-Period-Dat pic x                        col 18.  *> chk where used and how
     03          value "]"                                 col 19.
     03   value "  (M=Monthly, Q=Quarterly, Y=Yearly)"     col 20.
     03          value "Ave Valuation"             line 15 col  1.
     03          value "- ["                               col 15.
     03  using stk-Averaging  pic 9                        col 18.
     03          value "]"                                 col 19.
     03          value "  (1 = Yes or 0)"                  col 20.
     03          value "Next 2, See Manual First"  line 17 col  1.
     03          value "Activity Rep "             line 18 col  1.
     03          value "- ["                               col 15.
     03  using Stk-Activity-Rep-Run pic 9                  col 18.
     03          value "]"                                 col 19.
     03          value "  (0 = No or 1) leave as 0"        col 20.
     03          value "Audit Number "             line 19 col  1.
     03          value "- ["                               col 15.
     03  using Stk-Audit-No pic 999                        col 18.
     03          value "]"                                 col 21.
     03   value "  (if 1st time = 0, else leave as is)"    col 23.
*>
*>   IRS Screen  any other IRS data as other needed is from ACAS
*>      params already requested and/or created.
*>
 01  IRS-Data.
     03          value "IRS Client    Name - ["    line  7 col  1.
     03  using Client  pic x(24)                           col 23.
     03          value "]"                                 col 47.
     03          value "P/L Appropriation or Capital A/C ["
                                                   line  9 col  1.
     03  using PL-Approp-AC  pic 9(6)                      col 35.
     03          value "]"                                 col 41.
*>
 procedure division using WS-Calling-Data
                          File-Defs.
*>=======================================
*>
 init01   section.
*>*****
 Init01-Main.
*>
     if       Used-Once = zero                    *> Make sure we only do this once per run / caller program
              move 1 to Used-Once
              perform  zz020-Get-Program-Args.
*>
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
     display  Prog-Name at 0101 with foreground-color 2 erase eos.
     move     Prog-Name to l1-Name.
     display  "System Parameters" at 0130 with foreground-color 2.
*>
*>  Quick test that temp system rec =>  system-record.
*>
     move     function Length (WS-Temp-System-Record) to AA-Size.
     move     function length (System-Record)         to BB-Size.
     if       AA-Size < BB-Size
                       move spaces to Display-Blk
                       string SY902           delimited by size
                              AA-Size         delimited by size
                              " < "           delimited by size
                              "System-Rec = " delimited by size
                              BB-Size         delimited by size
                                         into Display-Blk
                       end-string
                       display Display-Blk at 2301 with erase eol     *> BUT WILL REMIND ME TO SET IT UP correctly
                       display SY008 at 2401 with erase eol
                       accept Accept-Reply at 2433
                       move   24 to Return-Code
                       goback                     *> not yet tested in callers
     end-if.
*>
*>  WE process for the Cobol parameter file first and if RDB in use
*>    copy/update the system record to the rdb SYSTEM-REC table
*>
     move     zero  to File-System-Used           *> In System-Record
                       File-Duplicates-In-Use.    *> Force Cobol proc.
     move     "00"  to FA-RDBMS-Flat-Statuses.    *> in fnctn (file-access)
     move     1 to File-Key-No.                   *> system record
     perform  acas000-Open-Input.                 *> as input as I/O will create if not present.
     if       fs-reply not = zero
 *>             perform acas000-close            *> Could produce an error, why ?
              perform ba000-mapser                *> Now done here instead of in caller,
              perform acas000-open                *>   see Proc-ACAS-Mapser-RDB.cob
     end-if.
     perform  acas000-Close.
     perform  acas000-Open.                       *> as I/O
     move     SY101 to fs-action.
     perform  disk-error-display.                 *> must now exist but JIC
*>
     move     1 to File-Key-No.                   *> system record read in as area may be overwritten
     perform  acas000-Read-Indexed.               *> Cobol file
     if       fs-reply not = zero
              move SY102 to FS-Action
              perform  disk-error-display         *> must now exist but JIC
              move 99 to fs-reply
              perform acas000-Close
              move   16 to Return-Code
              goback                              *> not yet tested for in callers
     end-if.
*>                                                *> Got Cobol param record.
     move     run-Date  to  u-bin.
     perform  zz060-Convert-Date.
     move     u-Date  to  To-Day.
     move     WS-Date to  WS-test-Date            *>  WS-Date and now WS-test-Date for display
                          Line-1-Date.            *>      and printing
     perform  User-Params.
     if       Cob-Crt-Status = Cob-Scr-Esc
              perform acas000-Close
              go to Main-Exit.
     perform  System-Params.
*>
     if       G-L
              perform  Gl-Params.
*>
     if       S-L
              perform  Sl-Params.
*>
     if       B-L
              perform  Pl-Params.
*>
     if       Stock
              perform  Stock-Params.
*>
     if       IRS-Entry-Block (1:10) = spaces
              initialise IRS-Entry-Block with filler
     end-if.
*>
     if       IRS
              perform IRS-Params
     end-if.
*>
*>   Omitted systems for O/S versions.
*>
*>     if       Payroll
*>              perform  Payroll-Params.
*>
*> Below unlinkely as no requests for such.
*>
*>     if       Project-Z
*>              perform Project-Z-Params.
*>     if       Auto-Vat-Returns
*>              perform Vat-Return-Params.
*>
     perform  Print-Params.
*>
*>-----------------------------------------------------------------------
*> WARNING: SL data and PL data reduced print, eg Not all data is printed
*>               - Consider make full?
*>-----------------------------------------------------------------------
*>
*>  Bypass security check for Open Source version
*>
     go       to Menu-Option.
*>
*>
*> now verify user name not changed.
*>
*>     move     usera  to  pass-Name.
*>     move     "N"  to  encode.
*>     call     "maps01"  using  maps01-ws.   *> OS modified version, reduced encrypted
*>              go to  menu-option.           *>   from 1024 bytes/char to 4, simple.
*>     if       pass-Name = user-code         *>  Dropped altogether.
*>
*> if here user name does not match encoded name. Possible
*> un-authorised usage.
*>
*>     display  " " at 0101 with erase eos.
*>     display  SY044 at 0501 with foreground-color 4.
*>     display  SY045 at 0601 with foreground-color 4.
*>     move     1 to Error-Code.
*>     call     "maps99" using Error-Code WS-Calling-Data.
*>     go       to Main-Exit.
*>
 Menu-Option.
     display  " " at 0101 with erase eos.
     if       System-Record-Version-Prime = zero
              move WS-Sys-Record-Ver-Prime to System-Record-Version-Prime
     end-if
*>
     move     System-Record to WS-Temp-System-Record.  *> Writing others will clears the record
*>
     move     1 to File-Key-No.               *> file still open.
     perform  acas000-Rewrite.                *> update system-record for Cobol file
     move     SY103 to fs-action.
     perform  disk-error-display.
*>
*>  Now check if we are doing RDB if not skip otherwise
*>  update / insert row to SYSTEM-REC before closing file so we
*>  dont lose the data in system-file.
*>
     perform  acas000-Close.                  *> cobol file
     if       FS-Cobol-Files-Used             *> In S-R, so no RDBMS in use
              go to We-Are-Done
     end-if
     if       File-System-Used = zero         *> Insurance
              go to We-Are-Done
     end-if.
*>
*>  First set up for RDB
*>
     move     zeros to FS-Reply WE-Error.
     move     RDBMS-DB-Name to DB-Schema.
     move     RDBMS-User    to DB-UName.
     move     RDBMS-Passwd  to DB-UPass.
     move     RDBMS-Port    to DB-Port.
     move     RDBMS-Host    to DB-Host.
     move     RDBMS-Socket  to DB-Socket.
*>
     move     "66" to FA-RDBMS-Flat-Statuses.     *> Force RDB processing in wsfnctn
     move     1 to File-Key-No.
     perform  acas000-Open.                       *> open rdb I/O
*>
*> THIS BLOCK INCLUDES TEST CODE
*>
     if       fs-reply not = zero                 *> might have made A mistake in the RDB params
              move    FS-Reply to WS-Saved-FS-Reply
              display "File status=" at 1301
              display FA-RDBMS-Flat-Statuses at 1313
              display "RDB data = " at 1401
              display RDBMS-DB-Name at 1501
              display RDBMS-User    at 1601
              display RDBMS-Passwd  at 1701
              display RDBMS-Port    at 1801
              display RDBMS-Host    at 1901
              display RDBMS-Socket  at 2001
              display SY106 at 2201  with erase eol
              display "Error was = " at 2301 with erase eol
              display WS-Saved-FS-Reply at 2313
              display "WE-Error=" at 2321
              display WE-Error at 2330
              display "on para = " at 2336
              display WS-No-Paragraph at 2347
              display SY110 at 2401 with erase eol
              perform acas000-Close
              accept  WS-Reply at 2433            *> Redo setup process?
              if      WS-Reply = "Y" or "y"
                      go to Init01-Main
              else
                      go to We-Are-Done           *> Allow user to work out whats wrong
     end-if.
*>
*> RDB now open so In RDB tables
*>
     move     WS-Temp-System-Record to System-Record.  *> restore param rec.
*>
     move     "66" to FA-RDBMS-Flat-Statuses.     *> Force RDB processing
     move     1 to File-Key-No.
     perform  acas000-Rewrite.
     perform  aa100-Check-4-Errors thru aa100-Exit.
     if       fs-reply not = zero             *> Creating RDB for 1st time
              perform acas000-write
              perform  aa100-Check-4-Errors thru aa100-Exit
     end-if
*>
*> This code block should never be run as SW's are always 0
*>
     if       Init-Default-File-SW = 1
              move    2 to File-Key-No
              move    Default-Record to System-Record
              perform acas000-Rewrite
              perform aa101-Check-4-Errors thru aa101-Exit
     end-if
     if       Init-Final-File-SW = 1
              move    3 to File-Key-No
              move    Final-Record to System-Record
              perform acas000-Rewrite
              perform aa103-Check-4-Errors thru aa103-Exit
     end-if
     if       Init-Sys4-File-SW = 1
              move    4 to File-Key-No
              move    System-Record-4 to System-Record
              perform acas000-Rewrite
              perform aa102-Check-4-Errors thru aa102-Exit
     end-if.
     perform  acas000-Close.
*>
 We-Are-Done.
*>
*>  Now write any RDB tables if flags say records created for dflt, final and sys4.
*>
     move     zero to WS-term-code.
     go       to Main-Exit.
*>
 Disk-Error-Display.
     if       fs-reply not = zero
              display fs-action at 0310
              display fs-reply at 0333
              display space at 0410
              display  SY104 at 2401
              accept   fs-reply at 2420
     end-if.
*> 05/02/18
*> Disk-Error.
*>     display  SY104 at 2401.
*>     accept   fs-reply at 2420.
*>
 Main-Exit.
     exit program.
*>
 User-Params      section.
*>=======================
*>
*>**************************************
*>  User Parameters Amendment Routine  *
*>**************************************
*>
 Main-User.
*>********
*>
     move     1 to screen-nos.
     display  " " at 0101 with erase eos.
     display  banner with erase eos.
     display  "User Data" at 0436 with foreground-color 2.
*>
     if       start-Date not = zero
              move  start-Date  to  u-bin
              perform zz060-Convert-Date
              move  WS-Date  to  P-Start
     else
              move spaces to P-Start
     end-if
     if       end-Date not = zero
              move  end-Date  to  u-bin
              perform zz060-Convert-Date
              move  WS-Date  to  P-End
     else
              move spaces to P-End
     end-if
 *>    move     spaces  to  pass-word of maps01-ws S-Pass-Word.
     move     Cyclea  to WS-Cyclea.
*>
     display  user-Data at 0101 with foreground-color 2.
*>
 User-Data-Accept.
     accept   user-Data with update.
     if       Cob-Crt-Status = Cob-Scr-Esc
              go to Main-Exit.
*>
     if       Date-Form = 1
              display "    Using UK format dd/mm/ccyy  " at 1420 with erase eol foreground-color 3
     else
      if      Date-Form = 2
              display "    Using USA format mm/dd/ccyy " at 1420 with erase eol foreground-color 3
      else
       if     Date-Form = 3
              display "    Using Intl format ccyy/mm/dd" at 1420 with erase eol foreground-color 3
       else
              display "    Incorectly Set. You MUST set this"
                                        at 1420 with erase eol foreground-color 4 highlight
              move 1 to Date-Form.
*>
     if       P-Start not = spaces
              move  zero  to  u-bin
              move  P-Start  to  WS-test-Date
              perform zz050-Validate-Date
*>              call "maps04" using maps03-ws
              move  u-Date  to  P-Start
*>              move  u-Date (1:6) to IRS-Start-Date (1:6)
*>              move  u-Date (9:2) to IRS-Start-Date (7:2)  *> Omit CC in year for IRS
     end-if
     if       u-bin = zero
              display SY005 at 1540 with foreground-color 3 blink
              go to user-Data-accept
     else     display " " at 1540 with erase eol
              move  u-bin   to  start-Date
     end-if
*>
*> With start date known (year) we can set the stats-Date-period.
*>   MUST remember to update these 3 fields at end of years end in XL150
*>  Mind you it does 'ASSUME' that xl150 will run after EOY and before any new invoices.
*>  SO, consider putting in support code for this in invoicing programs as well.
*>
     move     WS-Year9  to Stats-Date-Period.
     display  Stats-Date-Period at 1652  with foreground-color 2 highlight.
*>
     if       P-End not = spaces
              move  zero  to  u-bin
              move  P-End  to  WS-test-Date
              perform zz050-Validate-Date
*>              call "maps04" using maps03-ws
              move  u-Date  to  P-End
*>              move  u-Date (1:6) to IRS-End-Date (1:6)
*>              move  u-Date (9:2) to IRS-End-Date (7:2)  *> Omit CC in year for IRS
     end-if
     if       u-bin = zero
              display SY005 at 1640 with foreground-color 3 blink
              go to user-Data-accept

     else     display " " at 1640 with erase eol
              move  u-bin   to  end-Date
     end-if
 *>    move     S-Pass-Word to pass-word in maps01-ws.
 *>    if       pass-word of maps01-ws not = spaces
 *>             move  "P"  to  encode
 *>             call  "maps01"  using  maps01-ws
 *>             move  pass-word of maps01-ws  to
 *>                   pass-word of System-Record
 *>    end-if
     if       period = 13
              display "Weekly     " at 2265 with foreground-color 3 erase eol
     else
      if      period = 6
              display "Fortnightly" at 2265 with foreground-color 3 erase eol
      else
              move  3  to  period
              display "Monthly    " at 2265 with foreground-color 3 erase eol
      end-if
     end-if.
*>
     if       Page-Lines not > 28
              move 56 to Page-Lines
              display SY105 at 1750 with foreground-color 3 blink
              go to user-Data-accept
     else
              display " " at 1750 with erase eol
     end-if
*>
     display  "   " at 2401 with erase eol.
     if       not FS-Valid-Options
              move zero to File-System-Used
              display "Range 0 thru 1 only   "  at 2410 with foreground-color 3 blink
*>              display "Range 0 thru 5 only   "  at 2410 with foreground-color 3 blink
     else
      if      FS-Cobol-Files-Used
              display "Cobol data files used "  at 2410 with foreground-color 3
       else
        if    FS-MySql-Used
              display "MySQL Rdbms used   "  at 2410 with foreground-color 3.
   *>     else
   *>      if     FS-RDBMS-Used
   *>             display "Rdbms is used  "  at 2410 with foreground-color 3
*>
*>       if     FS-Oracle-Used
*>              display "Oracle Rdbms used  "  at 2410 with foreground-color 3
*>        else
*>         if   FS-Postgres-Used
*>              display "Postgres Rdbms used"  at 2410 with foreground-color 3
*>         else
*>          if  FS-DB2-Used
*>              display "IBM DB2 Rdbms used "  at 2410 with foreground-color 3
*>          else
*>           if FS-MS-SQL-Used
*>              display "MS SQL Server used "  at 2410 with foreground-color 3.
*>
 *>    if       File-Duplicates-In-Use not = zero and not = 1
 *>             move zero to File-Duplicates-In-Use
 *>             display "Range 0 thru 1 only   "  at 2450 with foreground-color 3 blink
 *>    else
 *>     if      FS-Duplicate-Processing
 *>             display "Duplicate file processing used"      at 2441 with foreground-color 3
 *>     else
 *>             display "Duplicate file processing NOT used"  at 2441 with foreground-color 3.
*>
     move     function upper-case (SL-VAT-Printed) to SL-VAT-Printed.
     if       SL-VAT-Printed not = "Y" and not = "N"
              move "N" to SL-VAT-Printed
              display SL-VAT-Printed at 2137 with foreground-color 3 blink.
*>
     move     WS-Cyclea  to Cyclea.
     if       Cyclea not > zero
              display "Cycle Error"  at 2065 with foreground-color 3
              go to user-Data-accept
     else     display space at 2065 with erase eol.

     move     "   User Data Complete"  to verify-message.
*>
     display  verify-screen at 0101 with foreground-color 2.
*>
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 6.
     accept   WS-Reply at 1576 with foreground-color 6 update.
*>
     if       WS-Reply = "N" or "n"
              go to  main-user.
*>
 Main-Exit.
     exit     section.
*>
 System-Params           section.
*>==============================
*>
*>*****************************************
*>  System Parameters Amendment Routine   *
*>*****************************************
*>
 Ops-Main.
     move     2  to  screen-nos.
     display  " " at 0101 with erase eos.
     display  banner with erase eos.
     display  "OPS  Data 1" at 0436 with foreground-color 2.
     display  ops-Data at 0101 with foreground-color 2.
     accept   ops-Data with update.
*>
     if       host not = 0 and not = 1
              move 1 to  host
              display "Multi-user system assumed" at 1823 with foreground-color 3 blink
     else
      if      host = zero
              display "Single-user system       " at 1823 with foreground-color 3 blink
      else
              display "Multi-user system        " at 1823 with foreground-color 3 blink.
     move     function upper-case (Param-Restrict) to Param-Restrict.
     if       Param-Restrict not = "N" and not = "Y"
              move "N" to Param-Restrict.
     display  Param-Restrict at 1531 with foreground-color 3 blink.
     display  "]"            at 1532 with foreground-color 2.
*>
*> Clear long comment before overwriting
*>
     display  spaxx at 2000.
     if       host = zero  and (op-system  < 1 or > 6)
              move 1 to op-system
              display "MSDOS assumed" at 2023 with foreground-color 3 blink
      else
       if     host = 1
          and (op-system  < 2 or > 6)
              move 6 to op-system
              display "Linux assumed" at 2023 with foreground-color 3 blink
      else    if op-system = 1
              display "DOS"     at 2023 with foreground-color 3 blink
      else    if op-system = 2
              display "Windows" at 2023 with foreground-color 3 blink
      else    if op-system = 3
              display "Mac OSX" at 2023 with foreground-color 3 blink
      else    if op-system = 4
              display "OS/2"    at 2023 with foreground-color 3 blink
      else    if op-system = 5
              display "Unix"    at 2023 with foreground-color 3 blink
      else    if op-system = 6
              display "Linux"   at 2023 with foreground-color 3 blink.
*>
     if       op-system = 3 or = 5 or = 6
              if   Print-Spool-Name2 = spaces
                   move Print-Spool-Name to Print-Spool-Name2
              end-if
              if   Print-Spool-Name3 = spaces
                   move Print-Spool-Name to Print-Spool-Name3
              end-if
              display ops-Data-2
              accept  ops-Data-2 with update
              if Print-Spool-Name (1:1) = space
                 display " Print Spool Name must be defined" at 2402 with highlight foreground-color 3
              else
                 move Print-Spool-Name to PSN
              end-if
     end-if
*>
     if       DC-Cobol-Standard
              display "Cobol Standard Display  " at 2054 with foreground-color 3
     else
      if      DC-GUI
              display "Gui Display             " at 2054 with foreground-color 3
      else
       if     DC-Widget
              display "Widget Display          " at 2054 with foreground-color 3
       else
              display " Invalid - Std selected " at 2054 with foreground-color 3 highlight
              move zero to Data-Capture-Used.
*>
     if       Maps-Ser-xx = "mp" and Maps-Ser-nn = 9999
              display "Using (Free) Open Source Version of ACAS"   at 1501
                               with highlight foreground-color 3
     else
              display "Using Supported Commercial Version of ACAS" at 1501
                               with highlight foreground-color 3.
*>
     move     "    OPS Data 1 Complete "  to  verify-message.
     display  verify-screen at 0101 with foreground-color 2.
*>
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 6.
     accept   WS-Reply at 1576 with foreground-color 6 update.
     if       WS-Reply = "N" or = "n"
              go to  Ops-Main.
*>
     if       File-System-Used = zero
              go to Main-Exit.
*>
 Ops-Main-2.
*>
*> Requested RDB processing so get more info
*>
     move     3  to  screen-nos.
     display  " " at 0101 with erase eos.
     display  banner.
     display  "OPS  Data 2" at 0436 with foreground-color 2.
     display  ops-Data-3 at 0101 with foreground-color 2.
     accept   ops-Data-3 with update.
     if       RDBMS-DB-Name not = spaces
              display " Set"  at 0746 with foreground-color 3.
     if       RDBMS-User not = spaces
              display " Set"  at 0846 with foreground-color 3.
     if       RDBMS-Passwd not = spaces
              display " Set"  at 0946 with foreground-color 3
              display "************"                   at 0922.
     if       RDBMS-Host not = spaces
              display " Set          "  at 1046 with foreground-color 3.
     if       RDBMS-Socket not = spaces
              display "Set "   at 1177 with foreground-color 3.
     if       RDBMS-Port not = spaces
              display " Set"  at 1246 with foreground-color 3.
*>
     move     "    OPS Data 2 Complete "  to  verify-message.
     display  verify-screen at 0101 with foreground-color 2.
*>
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 6.
     accept   WS-Reply at 1576 with foreground-color 6 update.
     if       WS-Reply = "N" or = "n"
              go to  Ops-Main-2.
*>
 Main-Exit.
     exit section.
*>
 GL-Params               section.
*>==============================
*>
*>*************************************
*>  G/L Parameters Amendment Routine  *
*>*************************************
*>
 GL-Params-Main.
     move     4 to  screen-nos.
     display  " " at 0101 with erase eos.
     display  banner at 0101 with foreground-color 2.
     display  "G-L  Data" at 0436 with foreground-color 2.
     move     next-batch to Num-6.
     display  gl-Data at 0101 with foreground-color 2.
     accept   gl-Data with foreground-color 3 update.
     move     Num-6 to next-batch.
*>
     move     function upper-case (p-c) to p-c.
     if       profit-centres
              display "Profit centres selected" at 0732 with foreground-color 3 erase eol
     else
      if      branches
              display "Branches selected" at 0732 with foreground-color 3 erase eol
      else
              move  space  to  p-c
              display "Not selected  " at 0732    with foreground-color 3 erase eol
*>
     move     function upper-case (p-c-level) to p-c-level.
     if       p-c = space  and
              p-c-level not = space
              move  space  to  p-c-level
     end-if
     if       p-c not = space
              and  revenue-only
              display "Revenue A/cs only " at 0832 with foreground-color 3.
     if       p-c not = space
              and  not  revenue-only
              move space  to  p-c-level
              display "All A/cs          " at 0832 with foreground-color 3
     end-if
     move     function upper-case(p-c-grouped) to p-c-grouped.
     display  "1st digit of P.C./Branch " at 0932 with foreground-color 3.
     if       grouped
              display "is the group identifier" at 0957 with foreground-color 3
     else
              display "is not significant" at 0957 with foreground-color 3
              move  space  to  p-c-grouped
     end-if
     move     function upper-case (comps) to comps.
     if       comparatives
              display "Selected        " at 1032 with foreground-color 3
     else
              move  space  to  comps
              display "Not selected    " at 1032 with foreground-color 3
     end-if
     move     function upper-case (ledger-2nd-index) to ledger-2nd-index.
     if       index-2
              display "Selected        " at 1132 with foreground-color 3 erase eol
     else
              move  space  to  ledger-2nd-index
              display "Not selected    " at 1132 with foreground-color 3 erase eol
     end-if
     move     function upper-case (m-v) to m-v.
     if       minimum-validation
              display "Selected        " at 1232 with foreground-color 3
     else
              display "Not selected    " at 1232 with foreground-color 3
              move  space  to  m-v
     end-if
     move     function upper-case (arch) to arch.
     if       archiving
              display "Selected        " at 1332 with foreground-color 3
     else
              move  space  to  arch
              display "Not selected    " at 1332 with foreground-color 3
     end-if
     move     function upper-case (vat) to vat.
     if       auto-vat
              display "Selected        " at 1632 with foreground-color 3
     else
              move  space  to  vat
              display "Not selected    " at 1632 with foreground-color 3
     end-if
     move     function upper-case (IRS-Instead) to IRS-Instead.
     if       IRS-Used
              display "IRS Selected" at 1932 with foreground-color 3 erase eol
              set IRS to true
     else
       if     IRS-Both-Used
              display "Both selected" at 1932 with foreground-color 3 erase eol
              set IRS to true
       else
              display "Not selected" at 1932 with foreground-color 3 erase eol
              set IRS-No to true
     end-if
     move     "    G-L Data Complete  "  to  verify-message.
     display  verify-screen at 0101 with foreground-color 2.
*>
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 2.
     accept   WS-Reply at 1576 with foreground-color 6 update.
*>
     if       WS-Reply = "N" or = "n"
              go to  gl-params-Main.
*>
 Main-Exit.
     exit section.
*>
 IRS-Params               section.
*>==============================
*>
*>*************************************
*>  IRS Parameters Amendment Routine  *
*>*************************************
*>
     move     9 to  screen-nos.
     display  " " at 0101 with erase eos.
     display  banner        with erase eos.
     display  "IRS  Data" at 0436 with foreground-color 2.
     display  IRS-Data            with foreground-color 2.
     accept   IRS-Data            with foreground-color 3 update.
*>
*> Now move the param data collected and store in the IRS Data block.
*>    Most of which is in the ACAS data areas.
*>
*>     move     Op-System    to System-Ops.
     move     Vat-Rate-1   to Vat1.
     move     Vat-Rate-2   to Vat2.
     move     Vat-Rate-3   to Vat3.
     move     Client       to User-Code.  *> as its unused in O/S versions.
*>
     if       PL-Approp-AC6 > zero
              move  "1" to PL-App-Created.
*>
*> Clean up if not initialised correctly.
*>
     if      Next-Post not numeric
             move 1 to Next-Post.
     if      IRS-Pass-Value not numeric
             move zero to IRS-Pass-Value.
     if      Save-Sequ not numeric
             move zero to Save-Sequ.
*>
 IRS-Params-Exit.
     exit     section.
*>
 SL-Params               section.
*>==============================
*>
*>*************************************
*>  S/L Parameters Amendment Routine  *
*>*************************************
*>
 SL-Params-Main.
     move     5 to  screen-nos.
     display  " " at 0101 with erase eos.
     move     Next-Invoice  to WS-Next-Invoice.
     if       WS-Next-Invoice = zero                         *> GC does not convert for display
              move 1 to WS-Next-Invoice
     end-if
     move     VAT-AC   to WS-VAT-AC.                           *> Ditto
*>
*> Clean up for old system files created pre 2018 fir new fields added
*> within filler as contains spaces in number fields. 21/04/24
*>
     if       GL-BL-Pay-Ac   > 99999 move zero to GL-BL-Pay-Ac.
     if       GL-P-Creditors > 99999 move zero to GL-P-Creditors.
     if       GL-BL-Purch-Ac > 99999 move zero to GL-BL-Purch-Ac.
     if       GL-SL-Pay-Ac   > 99999 move zero to GL-SL-Pay-Ac.
     if       GL-S-Debtors   > 99999 move zero to GL-S-Debtors.
     if       GL-SL-Sales-Ac > 99999 move zero to GL-SL-Sales-Ac.
*>
     move     SL-Limit to WS-SL-Limit.
*>
     display  banner.
     display  "S-L  Data 1" at 0436  with foreground-color 2.
     display  sl-Data.
     accept   sl-Data with foreground-color 2 update.
     move     WS-Next-Invoice to Next-Invoice.               *> GC does not convert for display
     move     WS-SL-Limit     to SL-Limit.

*>

     if       sl-dunning = 1
              display "Late letters selected    " at 0722 with foreground-color 3
     else
              move  zero  to  sl-dunning
              display "Late letters not selected" at 0722 with foreground-color 3.
*>
     if       sl-charges = 1
              display "Late charges selected    " at 0822 with foreground-color 3
     else
              move  zero  to  sl-charges
              display "Late charges not selected" at 0822 with foreground-color 3.
*>
     if       sl-delim = space
              display "Delimiter <!> assumed" at 1422
                          with foreground-color 2
              move  "!"  to  sl-delim
     end-if
     if       ( sl-Delim = "\"      *>"  just for kate
                     or = "/" )
          and FS-RDBMS-Used
              display "Delimiter <!> reset(RDB)" at 1422 with foreground-color 3
              move "!" to sl-Delim
     end-if
*>
     move     function upper-case (sl-own-nos) to sl-own-nos.
     if       SL-own-nos = "Y"
              display "Selected & Set" at 1528 with foreground-color 3
     else
              display "Unset         " at 1528 with foreground-color 3.
     if       Next-Invoice not = zero
              display "Set"    at 1632 with foreground-color 3
     else
              display "Unset"  at 1632 with erase eol foreground-color 3 blink.
*>
*> Clear text that will be overwritten by verify box & avoid A messing screen.
*>
     display  "                " at 1641 with erase eol.
*>
     move     function upper-case (SL-Stock-Link) to SL-Stock-Link.
     if       SL-Stock-Link = "Y" and Stock
              display "Selected & Set       " at 1940 with foreground-color 3 *> chg from 28 - 15/03/24
     else
              move "N" to SL-Stock-Link
              display "Unset and/or No Stock" at 1940 with foreground-color 3 blink. *> chg from 28 - 15/03/24
     move     function UPPER-CASE (SL-BO-Flag) to SL-BO-Flag.
     if       SL-BO-Flag not = "Y" and not = "N"
              move     "N" to SL-BO-Flag.
     if       SL-BO-Flag = "Y"
              display "Set   /"   at 1962  with foreground-color 3
     else
              display "Unset /" at 1962  with foreground-color 3 blink.
     move     function UPPER-CASE (SL-BO-Default) to SL-BO-Default.
     if       SL-BO-Default not = "Y" and not = "N"
              move     "N" to SL-BO-Default.
     if       SL-BO-Default = "Y"
              display "Set"     at 1970  with foreground-color 3
     else
              display "Unset"   at 1970  with foreground-color 3 blink.
*>
     if       sl-pay-ac not = zero
              display "Selected & Set" at 2028 with foreground-color 3
     else
              display "Unset" at 2028 with erase eol foreground-color 3 blink.
     if       sl-sales-ac not = zero
              display "Selected & Set" at 2128 with erase eol foreground-color 3
     else
              display "Unset" at 2128 with erase eol foreground-color 3 blink.
     if       S-Debtors not = zero
              display "Selected & Set" at 2228 with erase eol foreground-color 3
     else
              display "Unset" at 2228 with erase eol foreground-color 3 blink.
     move     WS-VAT-AC to VAT-AC.
     if       Vat-ac not = zero
              display "Selected & Set" at 2328 with erase eol foreground-color 3
     else
              display "Unset" at 2328 with erase eol foreground-color 3 blink.
     if       SL-Invoice-Lines = zero
              move 25 to SL-Invoice-Lines
     end-if
*>
     move     "    S-L Data Complete  "  to  verify-message.
     display  verify-screen at 0101 with foreground-color 2.
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 6.
     accept   WS-Reply at 1576 with foreground-color 6 update.
     if       WS-Reply = "N" or = "n"
              go to  sl-params-Main.
*>
 SL-Params-2.
     move     6 to  screen-nos.
     display  " " at 0101 with erase eos.
     display  banner.
     display  "S-L  Data 2" at 0436  with foreground-color 2.
     display  sl-Data-2 with erase eos.
     accept   sl-Data-2 with foreground-color 2 update.
*>
     move     function upper-case (SL-Comp-Head-Inv)  to SL-Comp-Head-Inv.
     move     function upper-case (SL-Comp-Head-Stat) to SL-Comp-Head-Stat.
     move     function upper-case (SL-Comp-Head-Lets) to SL-Comp-Head-Lets.
     move     function upper-case (SL-Comp-Head-Pick) to SL-Comp-Head-Pick.
*>
     if       SL-Comp-Head-Inv not = "Y" and not = "N"
              display "Error, set to N" at 0822 with foreground-color 4 highlight beep
              move "N" to SL-Comp-Head-Inv.
     if       SL-Comp-Head-Stat not = "Y" and not = "N"
              display "Error, set to N" at 0922 with foreground-color 4 highlight beep
              move "N" to SL-Comp-Head-Stat.
     if       SL-Comp-Head-Lets not = "Y" and not = "N"
              display "Error, set to N" at 1022 with foreground-color 4 highlight beep
              move "N" to SL-Comp-Head-Lets.
     if       SL-Comp-Head-Pick not = "Y" and not = "N"
              display "Error, set to N" at 1122 with foreground-color 4 highlight beep
              move "N" to SL-Comp-Head-Pick.
     if       SL-Comp-Head-Inv = "Y"
              display "Will be printed" at 0822 with erase eol foreground-color 3
     else     display "Will Not be printed" at 0822 with erase eol foreground-color 3.
     if       SL-Comp-Head-Stat = "Y"
              display "Will be printed" at 0922 with erase eol foreground-color 3
     else     display "Will Not be printed" at 0922 with erase eol foreground-color 3.
     if       SL-Comp-Head-Lets = "Y"
              display "Will be printed" at 1022 with erase eol foreground-color 3
     else     display "Will Not be printed" at 1022 with erase eol foreground-color 3.
     if       SL-Comp-Head-Pick = "Y"
              display "Will be printed" at 1122 with erase eol foreground-color 3
     else     display "Will Not be printed" at 1122 with erase eol foreground-color 3.
*>
     move     "  S-L Data 2 Complete  "  to  verify-message.
     display  verify-screen at 0101 with foreground-color 2.
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 6.
     accept   WS-Reply at 1576 with foreground-color 6 update.
     if       WS-Reply = "N" or = "n"
              go to  sl-params-2.
*>
 Main-Exit.
     exit section.
*>
 PL-Params               section.
*>==============================
*>
*>*************************************
*>  P/L Parameters Amendment Routine  *
*>*************************************
*>
 PL-Params-Main.
     move     7 to  screen-nos.
     display  " " at 0101 with erase eos.
     move     Next-Folio   to WS-Next-Folio.
     move     BL-Pay-AC    to BL-Pay-AC.
     move     P-Creditors  to WS-P-Creditors.
     move     BL-Purch-Ac  to WS-BL-Purch-Ac.
     display  banner.
     display  "P-L  Data" AT 0436 with foreground-color 2.
     display  pl-Data.
     accept   pl-Data with foreground-color 2 update.
*>
     move     WS-Next-Folio  to Next-Folio.
     if       pl-delim = space
              display "Delimiter <!> assumed" at 1422 with foreground-color 2
              move  "!"  to  pl-delim
     end-if
     if       (pl-Delim = "\" or = "/")        *> "
          AND FS-RDBMS-Used
              display "Delimiter <!> reset(RDB)" at 1422
                          with foreground-color 2
              move "!" to pl-Delim
     end-if
*>
     move     function upper-case (PL-Stock-Link) to PL-Stock-Link.
     if       PL-Stock-Link = "Y" and Stock
              display "Selected & Set" at 1528 with erase eol foreground-color 2
     else
              move "N" to PL-Stock-Link
              display "Unset and/or No Stock" at 1528 with erase eol foreground-color 3 blink.
*>
     move     WS-BL-Pay-AC  to BL-Pay-ac.
     if       BL-Pay-ac not = zero
              display "Selected & Set" at 1828 with erase eol foreground-color 2
     else
              display "Unset" at 1828 with erase eol foreground-color 3 blink.
     move     WS-BL-Purch-Ac  to BL-Purch-Ac.
     if       BL-Purch-ac not = zero
              display "Selected & Set" at 1928 with erase eol foreground-color 2
     else
              display "Unset" at 1928 with erase eol foreground-color 3 blink.
     move     WS-P-Creditors to P-Creditors.
     if       P-Creditors not = zero
              display "Selected & Set" at 2028 with erase eol foreground-color 2
     else
              display "Unset" at 2028 with erase eol foreground-color 3 blink.
*>
     move     "    P-L Data Complete"  to  verify-message.
     display  verify-screen at 0101 with foreground-color 2.
*>
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 6.
     accept   WS-Reply at 1576 with foreground-color 6 update.
*>
     if       WS-Reply = "N" or = "n"
              go to  pl-params-Main.
*>
 Main-Exit.
     exit section.
*>
 Stock-Params            section.
*>==============================
*>
*>***************************************
*>  Stock Parameters Amendment Routine  *
*>***************************************
*>
 Stock-Params-Main.
     move     8 to  screen-nos.
     display  " " at 0101 with erase eos.
     display  banner.
     display  "Stock Data" AT 0436 with foreground-color 2.
     display  Stock-Data.
     accept   Stock-Data with foreground-color 2 update.
*>
     if       Stk-Debug = 1
              display "    Set" at 0720 with erase eol   foreground-color 3
     else
              move zero to Stk-Debug
              display "    UnSet" at 0720 with erase eol foreground-color 3
     end-if
     if       Stk-Manu-Used = 1
              display "    Set" at 0920 with erase eol foreground-color 3
     else
              move zero to Stk-Manu-Used
              display "    UnSet" at 0920 with erase eol foreground-color 3
     end-if
     if       Stk-OE-Used = 1
              display "    Set" at 1020 with erase eol foreground-color 3
     else
              move zero to Stk-OE-Used
              display "    UnSet" at 1020 with erase eol foreground-color 3
     end-if
 *>    if       Stk-Audit-Used = 1
 *>             display "    Set" at 1120 with erase eol foreground-color 3
 *>    else
 *>             move zero to Stk-Audit-Used
 *>             display "    UnSet" at 1120 with erase eol foreground-color 3
 *>    end-if
 *>    if       Stk-Mov-Audit = 1
 *>             display "    Set" at 1220 with erase eol foreground-color 3
 *>    else
 *>             move zero to Stk-Mov-Audit
 *>             display "    UnSet" at 1220 with erase eol foreground-color 3
 *>    end-if
     move     function upper-case (Stk-Period-Cur) to Stk-Period-Cur.
     if       Stk-Period-Cur = "M"
              display "    Set to Monthly" at 1320 with erase eol foreground-color 3
     else
      if      Stk-Period-Cur = "Q"
              display "    Set to Quarterly" at 1320 with erase eol foreground-color 3
      else
 *>      if     Stk-Period-Cur = "W"
 *>             display "    Set to Weekly" at 1320 with erase eol foreground-color 3
 *>      else
              move "M" to Stk-Period-Cur
              display "    Unset: Has been set to Monthly" at 1320
                   with erase eol foreground-color 3 highlight.
*>
     move     function upper-case (Stk-Period-Dat) to Stk-Period-Dat.
     if       Stk-Period-Dat = "M"
              display "    Set to Monthly" at 1420 with erase eol foreground-color 3
     else
      if      Stk-Period-Dat = "Q"
              display "    Set to Quarterly" at 1420 with erase eol foreground-color 3
      else
       if     Stk-Period-Dat = "Y"
              display "    Set to Yearly" at 1420 with erase eol foreground-color 3
       else
              move "Y" to Stk-Period-Dat
              display "    Unset: Has been set to Yearly" at 1420
                                      with erase eol foreground-color 3 highlight.
*>
     if       Stk-Averaging = 1
              display "    Set" at 1520 with erase eol foreground-color 3
     else
              move zero to Stk-Averaging
              display "    UnSet" at 1520 with erase eol foreground-color 3
     end-if
*>
     if       Stk-Activity-Rep-Run = 1
              display "    Set" at 1820 with erase eol foreground-color 3
     else
              move zero to Stk-Activity-Rep-Run
              display "    UnSet" at 1820 with erase eol foreground-color 3
     end-if
     if       Stk-Audit-No  > 0 and < 99999
              display "  Set" at 1922 with erase eol foreground-color 3
     else
              move zero to Stk-Audit-No
              display "  Set to zero" at 1922 with erase eol foreground-color 4 highlight
     end-if
     move     function upper-case(Stk-BO-Active) to Stk-BO-Active.
     if       Stk-BO-Active = "Y"
              display "    Set"   at 1120 with erase eol foreground-color 3
     else
              display "    UnSet" at 1120 with erase eol foreground-color 3
     end-if
*>
     move     "  Stock Data Complete"  to  verify-message.
     display  verify-screen at 0101 with foreground-color 2.
*>
     move     "Y"  to  WS-Reply.
     display  WS-Reply at 1576 with foreground-color 6.
     accept   WS-Reply at 1576 with foreground-color 6 update.
*>
     if       WS-Reply = "N" or = "n"
              go to  Stock-Params-Main.
*>
 Main-Exit.
     exit section.
*>
 Print-Params            section.
*>==============================
*>
*>**********************************
*>  File Parameters Print Routine  *
*>**********************************
*>
     display  " " at 0101 with erase eos.
     display  "Do you want printed copy (Y/N) [ ]" at 1201  with foreground-color 2.
     move     "Y" to WS-Reply.
     accept   WS-Reply at 1233 with foreground-color 4 update.
     if       WS-Reply = "N" or = "n"
              go to Main-Exit.
*>
     open     output  print-file.
     move     Prog-Name to l1-Name.
     move     1 to page-nos.
     move     page-nos to l1-Page.
     write    print-record  from  Line-1 before 1.
     write    print-record  from  Line-3a after 1.
     write    print-record  from  Line-4 after 1.
*>
     move     spaces  to  Line-5.
     move     "Name"  to  l5-Name.
     move     usera   to  l5-Data-1.
     move     1 to Num-3.
     string   "Using IRS instead of GL - " delimited by size into l5-Data-2 pointer Num-3.
     if       irs-used
              string "Yes" delimited by size into l5-Data-2  pointer Num-3
              end-string
     else
              string "No" delimited by size into l5-Data-2   pointer Num-3
              end-string
     end-if
     write    print-record  from  Line-5 after 2.
*>
     move     "Address"  to  l5-Name.
     move     Address-1  to  l5-Data-1.
     if       profit-centres
              move  "Profit-Centres Selected"  to  l5-Data-2
     else
      if      branches
              move "Branches Selected"   to  l5-Data-2
      else
              move "Neither P/C or Branches Selected" to  l5-Data-2.
*>
     write    print-record  from  Line-5 after 1.
*>
     move     spaces     to  l5-Name  l5-Data-2.
     move     Address-2  to  l5-Data-1.
     if       not  profit-centres
        and   not  branches
              move spaces  to  l5-Data-2
     else
      if      revenue-only
              move  "Only for Revenue Accounts"  to  l5-Data-2
      else
              move  "For all Accounts"  to  l5-Data-2.
*>
     write    print-record  from  Line-5 after 1.
*>
     move     Address-3  to  l5-Data-1.
     if       not  profit-centres
        and   not  branches
              move spaces  to  l5-Data-2
     else
      if      grouped
              move  "P-C / Branches Grouped on 1st Digit" to  l5-Data-2
      else
              move  "P-C / Branches not Grouped" to  l5-Data-2.
*>
     write    print-record  from  Line-5 after 1.
*>
     if       Address-4 = spaces
              string   Post-Code      delimited by "  "
                       ", "           delimited by size
                       Country        delimited by "  "
                       ", "           delimited by size
                       Phone-No into l5-Data-1
              end-string
     else
              string   Address-4      delimited by "  "
                       ","            delimited by size
                       Post-Code      delimited by "  "
                       ","            delimited by size
                       Country        delimited by "  "
                       ", "           delimited by size
                       Phone-No into l5-Data-1    *> May run out of space in L5-Data-1
              end-string
     end-if
*>
     if       comparatives
              move "Comparative Figures Required"     to l5-Data-2
     else
              move "Comparative Figures not Required" to l5-Data-2.
*>
     write    print-record  from  Line-5 after 1.
*>
     if       Company-Email (1:8) not = spaces
              move     spaces to Line-5
              move     "Company Email" to L5-Name
              move     Company-Email  to L5-Data-1
              write    print-record  from  Line-5 after 1.
*>
     move     "Date Format" to l5-Name.
     if       Date-Form = 0 or 1
              move "UK Format" to l5-Data-1
              move 1 to Date-Form
     else
      if      Date-Form = 2
              move "USA Format" to l5-Data-1
      else    move "Intl Format" to l5-Data-1.
*>
     if       index-2
              move "Alphabetic Ledger Index Selected" to l5-Data-2
     else
              move "Alphabetic Ledger Index not Selected" to l5-Data-2.
*>
     write    print-record from Line-5 after 1.
*>
     move     start-Date  to  u-bin.
     perform  zz060-Convert-Date.
     move     "Period Start"  to  l5-Name.
     move     spaces to L5-Data-1.
     string   WS-Date                    delimited by size
              "     Statistics Year    " delimited by size
              Stats-Date-Period          delimited by size
                  into  l5-Data-1.
*>
     if       minimum-validation
              move  "Min. Validation During Data Entry" to  l5-Data-2
     else
              move  "Full Validation During Data Entry" to  l5-Data-2.
     write    print-record  from  Line-5 after 1.
*>
     move     end-Date  to  u-bin.
     perform  zz060-Convert-Date.
     move     WS-Date  to  l5-Data-1.
     move     "       End"  to  l5-Name.
*>
     if       archiving
              move "Transaction Archiving Selected" to l5-Data-2
     else
              move "Transactions Deleted at End of Cycle" to l5-Data-2.
     write    print-record  from  Line-5 after 1.
*>
     move     spaces to Line-5.
     move     vat-rate-1 to  Num-1.
     move     vat-rate-4 to  Num-1B.
     move     spaces     to l5-Data-1.
     if       SL-VAT-Printed = "Y"
              move  "(P) " to S-Pass-Word
     else
              move  "(NP)" to S-Pass-Word.
     string   Num-1          delimited by size
              " / "          delimited by size
              Num-1B         delimited by size
              "  VAT Reg: "  delimited by size
              VAT-Reg-Number delimited by size
              " "            delimited by size
              S-Pass-Word    delimited by size
                                 into l5-Data-1.
     move     spaces to S-Pass-Word.
     move     "VAT    Rate 1/4."  to  l5-Name.
*>
     if       Sales-Range = zero
              move  "No Reserved Sales Range"  to  l5-Data-2
     else
              move  "Sales Range most Significant Digit is - " to  l5-Data-2
              move  Sales-Range  to  array-2 (41).
     write    print-record  from  Line-5 after 1.
*>
     move     spaces to l5-Data-1.
     move     vat-rate-2  to  Num-1.
     move     vat-rate-5  to  Num-1B.
     string   Num-1   delimited by size
              " / "   delimited by size
              Num-1B  delimited by size
              "  Co. Phone:" delimited by size
              Phone-No      delimited by size
                                 into l5-Data-1.
*>     move     Num-1  to  l5-Data-1.
     move     "       Rate 2/5."  to  l5-Name.
*>
     if       Purchase-Range = zero
              move  "No Reserved Purchase Range" to  l5-Data-2
     else
              move  "Purchase Range Most Signif.  Digit is - " to  l5-Data-2
              move  Purchase-Range  to  array-2 (41).
     write    print-record  from  Line-5 after 1.
*>
     move     vat-rate-3  to  Num-1.
     move     Num-1  to  l5-Data-1.
     move     "       Rate 3."  to  l5-Name.
*>
     if       auto-vat
              move  "Auto VAT Posting Selected" to  l5-Data-2
     else
              move  "Manual VAT Posting Selected" to l5-Data-2
     end-if
     write    print-record  from  Line-5 after 1.
*>
     move     spaces  to  l5-Name  l5-Data-1.
     move     spaces  to  l5-Data-2.
     move     period  to  Num-2.
     move     1  to  Num-3.
     string   "Cycles per Quarter - "  delimited by size into  l5-Data-2  with  pointer  Num-3.
     string   Num-2  delimited by size into  l5-Data-2  with  pointer  Num-3.
*>
     move     current-quarter  to  Num-4.
     move     1  to  Num-3.
     move     "Current Quarter " to l5-Name.
     string   Num-4  delimited by size into  l5-Data-1  with  pointer  Num-3.
     write    print-record  from  Line-5 after 1.
*>
     move     spaces  to  l5-Data-2 l5-Data-1.
     move     next-batch  to  Num-2.
     move     1  to  Num-3.
     string   "Next Batch Number  - "  delimited by size into  l5-Data-2  with  pointer  Num-3.
     string   Num-2  delimited by size into  l5-Data-2  with  pointer  Num-3.
*>
     move     "Current Cycle" to l5-Name.
     move     cyclea to Num-4.
     move     1 to Num-3.
     string   Num-4 delimited by size into l5-Data-1 with pointer Num-3.
     write    print-record  from  Line-5 after 1  lines.
*>
     move     spaces  to  Line-5.
     move     "Print Lines" to l5-Name.
     move     Page-Lines to Num-9.
     move     Num-9 to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
*> End of User / G/L params, now ACAS & P/L params
*>
     move     spaces to l5-Data-2.
     write    print-record  from  Line-3b after 2.
     move     l4-part1 to print-record.
     write    print-record  from  Line-4  after 1.
*>
     move     "Address Delimiter" to l5-Data-2.
     move     pl-delim to array-2 (29).
*>
     move     "Environment"  to  l5-Name.
     if       multi-user
              move  "Multi User"  to  l5-Data-1
     else
              move  "Single User"  to  l5-Data-1
     end-if
     write    print-record  from  Line-5 after 2.
*>
     move     "Op. System"  to  l5-Name.
     move     spaces to Temp-String
                        Temp-String2
                        l5-Data-1.
     if       windows  move "Windows"   to  Temp-String
     else if  Dos      move "Dos"       to  Temp-String
     else if  os2      move "OS/2"      to  Temp-String
     else if  unix     move "Unix"      to  Temp-String
     else if  linux    move "Linux"     to  Temp-String.
     if       DC-Cobol-Standard
              move " & Cobol Standard" to Temp-String2
     else
      if      DC-GUI
              move " & Gui Display" to Temp-String2
      else
       if     DC-Widget
              move " & Widget Display" to Temp-String2.
*>
     string   Temp-String        delimited by space
              Temp-String2       delimited by "  "
                              into l5-Data-1.
*>
     move     "Next Batch Number" to l5-Data-2.
     move     25 to Num-3.
     move     bl-next-batch to Num-6.
     string   Num-6 delimited by size into l5-Data-2
                   with pointer Num-3.
     write    print-record from Line-5 after 1.
     move     "System version"  to  l5-Name.
     if       Maps-Ser-xx = "mp"
        and   Maps-Ser-nn = 9999
              move "Using (Free) Open Source Version of ACAS" to l5-Data-1
     else
              move "Using Commercial Version of ACAS"         to l5-Data-1
     end-if
     move     1 to Num-3.
     string   "Next Folio Number " delimited by size into l5-Data-2 pointer Num-3.
     if       Next-Folio = zero
              move 1 to Next-Folio.
     move     Next-Folio  to Num-7.
     add      3 to Num-3.
     string   Num-7 delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
     move     spaces to Line-5 Temp-String.
     if       not FS-Valid-Options
              move zero to File-System-Used.
     if       FS-Cobol-Files-Used
              move "Cobol Data Files Used"           to Temp-String
     else
 *>     if      FS-RDBMS-Used
 *>             move "Rdbms is used  "                 to Temp-String.
*>
     if       FS-MySql-Used
              move "MySQL Database Used"             to Temp-String.
*>     else
*>      if     FS-Oracle-Used
*>              move "Oracle Database Used"            to Temp-String
*>      else
*>       if    FS-Postgres-Used
*>             move "Postgres Database Used"          to Temp-String
*>       else
*>        if   FS-DB2-Used
*>             move "IBM DB2 Database Used"           to Temp-String
*>        else
*>         if  FS-MS-SQL-Used
*>             move "MS SQL Server Used"              to Temp-String.
*>
     if       File-Duplicates-In-Use not = zero and not = 1     *> no longer in use so clear it.
              move zero to File-Duplicates-In-Use
     end-if
     move     Temp-String  to l5-Data-1.
*>
     move     1 to Num-3.
     string   "Pay      Account " delimited by size into l5-Data-2 pointer Num-3.
     move     BL-Pay-Ac to Num-8.
     add      6 to Num-3.
     string   Num-8 delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
     move     spaces to Line-5.
     move     "Path to BIN" to l5-Name.
     move     ACAS_BIN  to l5-Data-1.
     if       l5-Data-1 = spaces
              move "UNSET Environment Variable" to l5-Data-1.
     move     1 to Num-3.
     string   "Ledger   Account " delimited by size into l5-Data-2 pointer Num-3.
     move     BL-Purch-Ac to Num-8.
     add      6 to Num-3.
     string   Num-8 delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
     move     spaces to Line-5.
     move     "Path to Ledgers" to l5-Name.
     move     ACAS_LEDGERS  to l5-Data-1.
     if       l5-Data-1 = spaces
              move "UNSET Environment Variable" to l5-Data-1.
     move     1 to Num-3.
     string   "Creditor Account " delimited by size into l5-Data-2 pointer Num-3.
     move     P-Creditors to Num-8.
     add      6 to Num-3.
     string   Num-8 delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
     move     spaces to Line-5.
     move     "Prt Spool Name 1" to l5-Name.
     if       not OS-Single
              move Print-Spool-Name to l5-Data-1
     else
              move "Not Used"       to l5-Data-1
     end-if
     move     1 to Num-3.
     string   "Stock Control Link " delimited by size into l5-Data-2 pointer Num-3.
     add      7 to Num-3.
     if       PL-Stock-Link = "Y" and Stock
              string "Yes" delimited by size into l5-Data-2 pointer Num-3
     else
              string "No" delimited by size into l5-Data-2 pointer Num-3
     end-if
     write    print-record from Line-5 after 1.
*>
     move     spaces to Line-5.
     move     "Prt Spool Name 2"     to l5-Name.
     if       not OS-Single
              move Print-Spool-Name2 to l5-Data-1
     else
              move "Not Used"        to l5-Data-1
     end-if
     write    print-record from Line-5 after 1.
*>
     move     spaces to Line-5.
     move     "Prt Spool Name 3"     to l5-Name.
     if       not OS-Single
              move Print-Spool-Name3 to l5-Data-1
     else
              move "Not Used"        to l5-Data-1
     end-if
     write    print-record from Line-5 after 1.
     move     spaces to Line-5.
     move     "Restrict Params"      to l5-Name.
     if       Param-Restrict = "Y"
              move "Yes" to l5-Data-1
     else
              move "No"  to L5-Data-1
     end-if
*>
*> End of ACAS Params now for S/L and Invoicing (if present)
*>
     write    print-record from Line-3c after 2.
     write    print-record from Line-4 after 1.
*>
     move     spaces to print-record.
     write    print-record after 1.
     move     3 to a.                           *> Invoice # + next inv #
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     1 to a.                           *> Late letters ?, Ext Chg desc, Ex disc. desc
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     2 to a.                           *> Late chgs ?, Ext chg rate, Ext. Disc Rate
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     4 to a.                           *> Credit period, Inv level
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     5 to a.                           *> Credit limit, Ext chg A/C, Ext. Disc A/C
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     6 to a.                           *> Std disc %, Vat #
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     7 to a.                           *> Min. late bal, prt Vat #?
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     8 to a.                           *> Max late chg
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     9 to a.                           *> Late chg rate
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     10 to a.                          *> Addr delim (SL & PL)
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     11 to a.                          *> Next batch #, Proforma Retn
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     12 to a.                          *> Next batch #, Proforma Retn
     perform  sl-print.
     write    print-record from Line-5 after 1.
     move     13 to a.                          *> Next batch #, Proforma Retn
     perform  sl-print.
     write    print-record from Line-5 after 1.
*>
     move     spaces to Line-5.
     move     "Company Heads Pri" to l5-Name.
     string   "nt on Delivery notes: " delimited by size
              SL-Comp-Head-Pick        delimited by size
                                              into l5-Data-1.
     move     1 to Num-3,
     string   "Stock Control Link " delimited by size into l5-Data-2 pointer Num-3.
     add      7 to Num-3.
     if       SL-Stock-Link = "Y" and Stock
              string "Yes" delimited by size into l5-Data-2 pointer Num-3
     else
              string "No" delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
     string   "nt on Invoices      : " delimited by size
              SL-Comp-Head-Inv         delimited by size
                                              into l5-Data-1.
     move     spaces to l5-Data-2.
     move     1 to Num-3.
     string   "Pay      Account " delimited by size into l5-Data-2 pointer Num-3.
     move     SL-Pay-Ac to Num-8.
     add      6 to Num-3.
     string   Num-8 delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
     string   "nt on Statements    : " delimited by size
              SL-Comp-Head-Stat        delimited by size
                                              into l5-Data-1.
     move     spaces to l5-Data-2.
     move     1 to Num-3.
     string   "Ledger   Account " delimited by size into l5-Data-2 pointer Num-3.
     move     SL-Sales-Ac to Num-8.
     add      6 to Num-3.
     string   Num-8 delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
     string   "nt on Late Letters  : " delimited by size
              SL-Comp-Head-Lets        delimited by size
                                              into l5-Data-1.
     move     spaces to l5-Data-2.
     move     1 to Num-3.
     string   "Debtors  Account " delimited by size into l5-Data-2 pointer Num-3.
     move     S-Debtors to Num-8.
     add      6 to Num-3.
     string   Num-8 delimited by size into l5-Data-2 pointer Num-3.
     write    print-record from Line-5 after 1.
*>
*> Delivery now redundant as done in another way, within customer record.
*>
*>     move     spaces to l5-Data-2.
*>     move     1 to Num-3.
*>     string   "Delivery Tag     " delimited by size into l5-Data-2 pointer Num-3.
*>     move     Delivery  to Num-8.
*>     add      6 to Num-3.
*>     string   Num-8 delimited by size into l5-Data-2 pointer Num-3.
*>     write    print-record from Line-5 after 1.
*>
*> Now for Stock
*>
*>  CHANGES : replaced O/E with IRS.
*>  so will ONLY print out the IRS specific params that are diff
*>     rest of ACAS - Client.
*>
     move     2 to page-nos.
     move     page-nos to l1-Page.
     write    print-record  from  Line-1 after page.
     write    print-record  from  Line-3d after 2.
     write    print-record  from  Line-4 after 1.
*>
     move     spaces to Line-5.
     move     "Debug Mode" to l5-Name.
     if       stk-debug = 1
              move "Yes" to l5-Data-1
     else
              move "No" to l5-Data-1.
*>
     string   "IRS Client       " delimited by size
              Client              delimited by "  "
                  into l5-Data-2.
     write    print-record from Line-5 after 2.
*>
     move     spaces to Line-5.
     move     "Manufacturing" to l5-Name.
     if       Stk-Manu-Used = 1
              move "Yes" to l5-Data-1
     else
              move "No" to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
     move     "Audit in Use" to l5-Name.
     if       Stk-Audit-Used = 1
              move "Yes" to l5-Data-1
     else
              move "No" to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
     move     "Movement Audits" to l5-Name.
     if       Stk-Mov-Audit = 1
              move "Yes" to l5-Data-1
     else
              move "No" to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
     move     "Current Period" to l5-Name.
     if       Stk-Period-Cur = "M"
              move "Monthly"   to l5-Data-1
     else if  Stk-Period-Cur = "Q"
              move "Quarterly" to l5-Data-1
     else if  Stk-Period-Cur = "Y"
              move "Yearly"    to l5-Data-1
     else     move "NOT SET"   to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
     move     "To Date Period" to l5-Name.
     if       Stk-Period-Dat = "M"
              move "Monthly"   to l5-Data-1
     else if  Stk-Period-Dat = "Q"
              move "Quarterly" to l5-Data-1
     else if  Stk-Period-Dat = "Y"
              move "Yearly"    to l5-Data-1
     else     move "NOT SET"   to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
     move     "Stock Averaging" to l5-Name.
     if       Stock-Averaging
              move "Yes" to l5-Data-1
     else     move "No"  to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
     move     "Current Audit No" to l5-Name.
     move     Stk-Audit-No to Num-7.
     move     Num-7 to l5-Data-1.
     write    print-record from Line-5 after 1.
*>
*>  Payroll
*>
     write    print-record  from  Line-3d2 after 2.
     move     "                      ******************" to l4-part1.
     write    print-record  from  Line-4 after 1.
*>
*>   No Payroll for Open Source version at this time 01/11/2025
*>
     move     spaces to Line-5.
     move     "Payroll in Use   " to l5-Name.
*>     if       Payroll-Used = 1
*>              move "Yes" to l5-Data-1
*>     else
              move "No" to l5-Data-1.
*>
     if       FS-RDBMS-Used
              move "RDBMS DB Schema " to l5-Data-2
              move RDBMS-DB-Name      to l5-Data-2 (17:12).    *> changed these back 4 char
     write    print-record from Line-5 after 2.
*>
     if       FS-RDBMS-Used
              move spaces to l5-Data-1    l5-Name
              move "RDB User Name   " to l5-Data-2
              move RDBMS-User         to l5-Data-2 (17:12)
              write print-record  from  Line-5 after 1
              move "RDB User Passwd " to l5-Data-2         *> Could remove these 4 lines
              move "It's SECRET"      to l5-Data-2 (17:12)
              move Line-3e (1:40)     to Line-5 (1:40)     *> System Params head
              write print-record  from  Line-5 after 1
     else
              write    print-record  from  Line-3e after 2.  *> & leave this freestanding
*>
     move     "                       *****************" to l4-part1.
     move     spaces to l4-Part2.                          *> clears righthand ******
     if       FS-RDBMS-Used
              move spaces to l5-Data-1    l5-Name
              move     "****************" to l5-files (15:16)
              move "RDB Host        " to l5-Data-2
              move RDBMS-Host         to l5-Data-2 (17:32)
              write print-record  from  Line-5 after 1
     else
              write    print-record  from  Line-4 after 1.
*>
     if       FS-RDBMS-Used
              move spaces to l5-Data-1    l5-Name
              move "RDB Socket      " to l5-Data-2
              move RDBMS-Socket       to l5-Data-2 (17:46)     *> ignoring last 17 chars of field.
              write print-record  from  Line-5 after 1.
*>
     move     all "*" to l4-part2-star
                         l4-part1-star.           *> in case it get run again
     move     spaces to Line-5.
*>
     move     "PL Approp A/C" to l5-Name.
     move     PL-Approp-AC6  to l5-Data-1.
*>
     if       FS-RDBMS-Used
              move "RDB Port        " to l5-Data-2
              move RDBMS-Port         to l5-Data-2 (17:5)
              write print-record  from  Line-5 after 1
     else
              write print-record from Line-5 after 2.
*>
*> End of params EOP.
*>
     write    print-record  from  Line-6 after 2.
     write    print-record  from  Line-7 after 1.
     close    print-file.
     call     "SYSTEM" using Print-Report.
*>
 Main-Exit.
     exit section.
*>
 SL-Print         section.
*>***********************
*>
     if       A < 1 or > 13
              go to Main-Exit.
     move     spaces to Line-5.
*>
     go       to aa1 aa2 aa3 aa4 aa5 aa6 aa7 aa8 aa9 aa10 aa11 aa12 aa13
                      depending on a.
*>
 aa1.
     if       sl-dunning = zero
              move "Dunning Letters not Selected" to l5-Data-2
     else
              move "Dunning Letters Selected" to l5-Data-2.
*> C or D
     if       extra-type = "C"
              move "Ext. Charge Desc" to l5-Name
              move extra-desc to l5-Data-1.
     if       extra-type = "D"
              move "Extra Disc. Desc" to l5-Name
              move extra-desc to l5-Data-1.
     go       to Main-Exit.
*>
 aa2.
     if       sl-charges = zero
              move "Late Charges not Selected" to l5-Data-2
     else
              move "Late Charges Selected" to l5-Data-2.
*> C or D
     move     extra-rate to Num-1.
     if       extra-type = "C"
              move "Ext. Charge Rate" to l5-Name
              move Num-1 to l5-Data-1.
     if       extra-type = "D"
              move "Ext. Disc. Rate" to l5-Name
              move Num-1 to l5-Data-1.
     go       to Main-Exit.
*>
 aa3.
     if       sl-own-nos = "N"
              move "Computer Generated Invoice Numbers Selected" to l5-Data-2
     else
              move "Manually Entered Invoice Numbers Selected"   to l5-Data-2.
*>
     move     "Next Inv. Number" to l5-Name.
     move     next-invoice to Num-7.
     move     Num-7 to l5-Data-1.
     go       to Main-Exit.
*>
 aa4.
     move     "Credit Period nn Days" to l5-Data-2.
     move     sl-credit  to  Num-4.
     move     15 to Num-3.
     string   Num-4 delimited by size into l5-Data-2 with pointer Num-3.
*>
     move     "Inv. Data Level" to l5-Name.
     move     invoicer to l5-Data-1.
     go       to Main-Exit.
*>
 aa5.
     move     "Standard Credit Limit" to l5-Data-2.
     move     sl-limit to Num-5.
     move     23 to Num-3.
     string   Num-5 delimited by size into l5-Data-2 with pointer Num-3.
*>
     move     extra-charge-ac to Num-8.              *> This from sl900 only but does not appear to be used any where.
     if       extra-type = "C"
              move "Extra Charge A/C" to l5-Name
              move Num-8 to l5-Data-1.
*>
     if       extra-type = "D"
              move "Extra Disc. A/C" to l5-Name
              move Num-8 to l5-Data-1.
     go       to Main-Exit.
*>
 aa6.
     move     "Standard Discount is   nn.nn%" to l5-Data-2.
     move     sl-disc to Num-1.
     move     24 to Num-3.
     string   Num-1 delimited by size into l5-Data-2 with pointer Num-3.
*>
     move     "VAT Account" to l5-Name.
     move     vat-ac to Num-8.
     move     Num-8 to l5-Data-1.
     go       to Main-Exit.
*>
 aa7.
     move     "Min. Late Balance" to l5-Data-2.
     move     sl-min to Num-2.
     move     25 to Num-3.
     string   Num-2 delimited by size into l5-Data-2 with pointer Num-3.
*>
     move     "Print VAT Nunber" to l5-Name.
     if       SL-VAT-Prints
              move     "Yes"     to l5-Data-1
     else
              move     "No "     to l5-Data-1.
     go       to Main-Exit.
*>
 aa8.
*>
     move     "Max. Late Charge" to l5-Data-2.
     move     sl-max to Num-2.
     move     25 to Num-3.
     string   Num-2 delimited by size into l5-Data-2 with pointer Num-3.
     move     "Prt Inv Max Itms"  to L5-Name.
     move     SL-Invoice-Lines     to Num-4.
     move     Num-4 to L5-Data-1.
     go       to Main-Exit.
*>
 aa9.
*>
     move     "Late Charge Rate       nn.nn%" to l5-Data-2.
     move     sl-late-per to Num-1.
     move     24 to Num-3.
     string   Num-1 delimited by size into l5-Data-2 with pointer Num-3.
     go       to Main-Exit.
*>
 aa10.
*>
*> Note these are S/L and P/L params
*>
     move     "Address Delimiter" to l5-Data-2.
     move     sl-delim to array-2 (29).
     go       to Main-Exit.
*>
 aa11.
     move     "Next Batch Number" to l5-Data-2.
     move     25 to Num-3.
     move     first-sl-batch to Num-6.
     string   Num-6 delimited by size into l5-Data-2 with pointer Num-3.
     move     "Proforma Retent." to l5-Name.
     move     pf-retention to Num-9.
     move     Num-9 to l5-Data-1.
     go       to Main-Exit.
*>
 aa12.  *> Right hand side only
     move     "BO Link " to l5-Data-2.
     move     27 to Num-3.
     if       SL-BO-Flag = "Y"
              string   "Yes" delimited by size  into L5-Data-2
                             with pointer Num-3
     else
              string   " No" delimited by size  into L5-Data-2
                             with pointer Num-3.
     go       to Main-Exit.
*>
 aa13.  *> Right hand side only
     move     "BO Default " to l5-Data-2.
     move     27 to Num-3.
     if       SL-BO-Default = "Y"
              string   "Yes" delimited by size  into L5-Data-2
                             with pointer Num-3
     else
              string   " No" delimited by size  into L5-Data-2
                             with pointer Num-3.
     go       to Main-Exit.
*>
 Main-Exit.
     exit     section.
*>
 copy "Proc-Get-Env-Set-Files.cob".
*>
 zz050-Validate-Date        section.
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-test-Date
*> output:  u-Date/ws-Date as uk date format
*>          u-bin not zero if valid date
*>
     inspect  WS-test-Date replacing all "." by "/".
     inspect  WS-test-Date replacing all "," by "/".
     inspect  WS-test-Date replacing all "-" by "/".
*>
     move     WS-test-Date to WS-Date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-test-Date.
     if       Date-USA                *> swap month and days
              move WS-Days to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap to WS-Month
              go to zz050-test-Date.
*>
*> So it's International date format
*>
     move     "dd/mm/ccyy" to WS-Date.  *> swap Intl to UK form
     move     WS-test-Date (1:4) to WS-Year.
     move     WS-test-Date (6:2) to WS-Month.
     move     WS-test-Date (9:2) to WS-Days.
*>
 zz050-test-Date.
     move     WS-Date to u-Date.
     move     zero to u-bin.
     perform  maps04.
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
*> output:  WS-Date as uk/US/Inlt date format
*>          u-Date & WS-Date = spaces if invalid date
*>          u-Date = UK date format, if not spaces
*>
     perform  maps04.
     if       u-Date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     u-Date to WS-Date.
*>
     if       Date-Form = zero or > 3
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move WS-Days to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap to WS-Month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     u-Date (7:4) to WS-Intl-Year.
     move     u-Date (4:2) to WS-Intl-Month.
     move     u-Date (1:2) to WS-Intl-Days.
*>
 zz060-Exit.
     exit     section.
*>
 Maps04       section.
*>*******************
*>
     call     "maps04"  using  maps03-ws.
*>
 maps04-exit.
     exit     section.
*>
 SystemMT-DAL section.
*>*******************
*>
 aa100-Check-4-Errors.
*>
*> System-Record - if any errors then msgs and exit module
*>
 *>    if       fs-reply not = zero
 *>        and  SQL-Err =
     if       fs-reply not = zero
              display SY106            at 0601 with erase eos  *> acas000/SystemMT processing
              display "Fs-reply = "    at 0701
              display fs-reply         at 0712
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
              display "SQL Err = "     at 0901
              display SQL-Err          at 0911
              display "Err Msg = "     at 1001
              display SQL-Msg (1:229)  at 1011
              display SY008 at 1301
              accept  Accept-Reply at 1335
              go to  aa100-Exit
     end-if.
*>
 aa100-Exit.
     Exit.
*>
 aa101-Check-4-Errors.
*>
*> Default-Record - if any errors then msgs and exit module
*>
 *>    if       fs-reply not = zero
 *>        and  SQL-Err =
     if       fs-reply not = zero
              display SY107            at 0601 with erase eos  *> acas000/DfltMT processing
              display "Fs-reply = "    at 0701
              display fs-reply         at 0712
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
              display "SQL Err = "     at 0901
              display SQL-Err          at 0911
              display "Err Msg = "     at 1001
              display SQL-Msg (1:229)  at 1011
              display SY008 at 1301
              accept  Accept-Reply at 1335
     end-if.
*>
 aa101-Exit.
     Exit.
*>
 aa102-Check-4-Errors.
*>
*> Sys4-Record - if any errors then msgs and exit module
*>
 *>    if       fs-reply not = zero
 *>        and  SQL-Err =
     if       fs-reply not = zero
              display SY108            at 0601 with erase eos  *> acas000/Sys4MT processing
              display "Fs-reply = "    at 0701
              display fs-reply         at 0712
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
              display "SQL Err = "     at 0901
              display SQL-Err          at 0911
              display "Err Msg = "     at 1001
              display SQL-Msg (1:229)  at 1011
              display SY008 at 1301
              accept  Accept-Reply at 1335
     end-if.
*>
 aa102-Exit.
     Exit.
*>
 aa103-Check-4-Errors.
*>
*> Final-Record - if any errors then msgs and exit module
*>
 *>    if       fs-reply not = zero
 *>        and  SQL-Err =
     if       fs-reply not = zero
              display SY109            at 0601 with erase eos  *> acas000/finalMT processing
              display "Fs-reply = "    at 0701
              display fs-reply         at 0712
              display "WE-Error = "    at 0801
              display WE-Error         at 0812
              display "SQL Err = "     at 0901
              display SQL-Err          at 0911
              display "Err Msg = "     at 1001
              display SQL-Msg (1:229)  at 1011
              display SY008 at 1301
              accept  Accept-Reply at 1335
     end-if.
*>
 aa103-Exit.
     Exit.
*>
 copy "Proc-ACAS-Mapser-RDB.cob". *>  uses ba000- etc  holds acas000 calls.
*>
