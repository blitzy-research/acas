       >>source free
*>
*>          WARNING, WARNING: This program MUST NOT be used as is.
*>          ^^^^^^^^^^^^^^^^* ************************************
*>   It must be modified to match up to the input file used in
*>   the old stock control / Inventory systems, for which you will
*>   need access to the file layouts by field for all data being
*>   transferred to the new ACAS system.
*>
*>*************************************************************
*>                                                            *
*>               Stock Item File Importer                     *
*>                TEMPLATE program ONLY                       *
*>                                                            *
*>*************************************************************
*>
 identification          division.
*>================================
*>
*>**
      program-id.         st060.
*>**
*>    Author.             V.B.Coen, FBCS
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Stock Item File Importer.
*>                        This program can be used to import stock records from another
*>                        system or software package.
*>                        HOWEVER it will need to be modified to reflect the format
*>                        and layout of the old system.
*>                        Before any changes to this make a back up copy of the original
*>                        prior to any changes.
*>                        The form of the old data can vary as support for file created from
*>                        most can be imported including RDBMS such as MySQL and SqLite.
*>
*>                        We can undertake this service on
*>                        receipt of the first five records both as a file dump and a
*>                        full listing/s (containing as many of the data fields that is
*>                        used as possible as well as the full file to be imported.
*>                        If you have it, the record layout of the file from the
*>                        documentation of the old system or from their technical support
*>                        department if they are still in business.
*>                        Otherwise:
*>
*>                        It is recommended to create the five records using the lowest
*>                        values for the stock number eg, 0000000test1 though 000000test5
*>                        and all numeric fields 1234567 etc and likewise money fields with
*>                        say 123456.78 or 987654.32 etc. Also alphabetic fields eg, item
*>                        descriptions with 'abcdefghijklmnop' or 'mlkjihgfedcba' etc.
*>                        This will help in examining the file for the correct layout for
*>                        each field.
*>                        This is a chargeable service and is charged at the rate of
*>                        25 pounds sterling per hour with a maximum of eight hours but
*>                        the average is five. Contact via email to vbcoen@gmail.com.
*>                        --------------------------------------------------------------
*>
*>                        This program assumes that the supplier information is NOT
*>                        available on the old system and will use the value in
*>                        WS-Default-Supplier and you will need to manually add/change
*>                        them via Stock Record Amend having loaded up all suppliers in
*>                        Sales Ledger including the default one as set up in this program
*>                        as well as the analysis code for each record however
*>                        here you can leave it as the default code 'a1' for both sales
*>                        and purchase (see WS-Default-PA for Purchase and ws-Default-SA
*>                        for Sales. You can modify the source to different values prior
*>                        to compiling and running this program.
*>
*>                        YOU must run sl070 (Set-Up Sales Analysis Codes) or
*>                        pl070 (Set-Up Purchase Analysis Codes) to create the
*>                        Analysis data to the table if using rdbms instead of files
*>                        as it does not know if this exists but will know if the
*>                        file version exists.
*>
*>                        Also the default operation regarding stock item numbers and the
*>                        abbreviated number is for the Stock Item, use from old file,
*>                        abbreviated, Generate new starting with 0000001.
*>                        Here you should change to your requirements.
*>
*>                        WARNING, WARNING: This program MUST NOT be used as is.
*>                        ^^^^^^^^^^^^^^^^* ************************************
*>
*>                        It needs to be changed according the data file to be imported
*>                        as well as the field order in the imported file
*>                        & the contents of the block of fields just below prog-name in WS.
*>
*>                        You then need to test it to make sure that it is working correctly
*>                        before used in a live environment. It does not have any code in to
*>                        support duplicate records or rewrite on write error as a safe guard
*>                        to existing data.
*>
*>                        It is strongly recommended that all initial testing is only
*>                        conducted against a Cobol file before using RDB tables.
*>                        SO ENSURE you have the correct system params set up first.
*>                        Best to use in a test/development file area only.
*>
*>                        This program is called by the stock.cbl Menu so replace the '*'
*>                        from option F with space. - nice to do.
*>                        REMARK OUT THE first five lines end with GOBACK
*>                        at the beginning of the PROCEDURE DIVISION
*>                         that stop this program being used without modifications but if
*>                         called will produce error messages before returning to the menu.
*>
*>                        Now compile stock.cbl by running cobc -x stock.cbl
*>                        This should compile cleanly with no errors or warnings, if not fix
*>                        and recompile.
*>
*>                        After this process and assuming an import will no longer be needed,
*>                        recompile the original code of st060.cbl that will force a go back
*>                        to the menu if selected, or what ever else you like.
*>
*>                        Generally - this program will only need to be used ONCE.
*>**
*>    Version.            See prog-name in Ws.
*>**
*>    Called modules.
*>                        maps04 - Date testing and conversion.
*>                        SL070  - Analysis codes set up - Defaults only.
*>                        acas011 -> Stock file FH
*>                         stockMT - STOCK-REC RDB table.
*>**
*>    Error messages used.
*>                        ST000.
*>
*>                        ST601.
*>                        ST602.
*>                        ST603.
*>                        ST604.
*>**
*>    Changes:
*> 08/06/13 vbc - 3.01.37 Rewritten in Cobol from scratch via st010 & updated to v3.01.37.
*> 21/07/16 vbc - 3.02.01 Support for RDB tables. version updated to v3.02.
*> 24/10/16 vbc -     .02 ALL programs now using wsnames.cob in copybooks
*> 12/03/18 vbc -     .03 acasnnn copylib renaming acas000-open etc to comply with
*>                        rest of ACAS to (System-Open etc) removed unused field
*>                        WS var. error-code.
*> 14/03/18 vbc -     .04 Additional comments regarding modifications.
*>                        Chg ST000 to stock rec. More comments added.
*> 24/01/24 vbc -     .05 Added continue to inline performs clears warnings.
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
 input-output            section.
*>-------------------------------
*>
 file-control.
*>------------
*>
     select import-file             assign File-101
                                    organization sequential
                                    status fs-reply.
*>
 data                    division.
*>================================
*>
 file section.
*>------------
*>
 fd  Import-file.                     *> Assumes that this file is a comma delimited file
 01  Import-Record.                   *> eg, field-1,field2,field3 etc where alphanemerics are in quotes
     03  filler          pic x(512).    *> This needs changing to reflect actual + 2 bytes (if needed)
*>
 copy "wsstock.cob" replacing
                    WS-Stock-Record    by WS-Temp-Stock-Record
                    WS-Stock-Key       by WS-Temp-Stock-Key
                    WS-Stock-Abrev-Key by WS-Temp-Abrev-Key
                    WS-Stock-Desc      by WS-Temp-Stock-Desc
                    Stock-Mthly-Running-Totals
                                       by Tmp-Stock-Mthly-Running-Totals
                    Stock-History      by Tmp-Stock-History.
*>
 working-storage section.
*>-----------------------
*>
 77  prog-name           pic x(15)       value "ST060 (3.3.00)".
*>
*> START OF MODIFIABLE BLOCK IN WS -
*> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>   CHANGE THESE TO SUIT YOUR INSTALLATION STANDARDS.
*>     These are the defaults that will be used for all
*>      transferred stock records from the old system.
*>
 77  ws-Default-PA       pic xxx         value "Pa1".         *> Default Anal code for PL.
 77  ws-Default-SA       pic xxx         value "Sa1".         *> Default Anal code for SL.
 77  ws-Default-Supplier pic x(7)        value "A000011".     *> Default Supplier code.
 77  ws-Abrev-Value      pic 9(7)        value zero.          *> Default Abrev code.
*>
 77  Import-Mode         pic 9           value 1.        *> change to 2 if needed. currently for comma delimited
     88  Process-Comma                   value 1.        *> import a comma delimited file
     88  Process-Reg                     value 2.        *> import a text file containing Stock fields
*>
 77  ws-Hist-Reset-Flag  pic 9           value 1.        *> CHANGE to zero if importing these
     88  ws-Reset-Hist                   value 1.
*>
*> ENDS MODIFIABLE BLOCK IN WS.
*> ^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
 77  Evaluation-Msg      pic x(25)       value spaces.
 77  File-101            pic x(64)       value spaces.   *> NEEDS the file name for input see start of program.
 77  ws-Import-Date-Format pic 9         value 1.        *> UK date format, but change to one needed.
     88  ws-Date-UK                      value 1.  *> dd/mm/yyyy
     88  ws-Date-USA                     value 2.  *> mm/dd/yyyy
     88  ws-Date-Intl                    value 3.  *> yyyy/mm/dd
 77  ws-Test-Desc        pic x(36)       value spaces.        *> Used to clear quotes from alphanumeric fields
 77  ws-Delimiter-Found  pic x           value space.
*>
 77  ws-Record-Count     pic 9(7)        value zero.        *> read count
 77  ws-Write-Count      pic 9(7)        value zero.
 77  ws-Disp-Count       pic z(6)9.
*>
 01  ws-Number-X-8       pic x(8).
 01  ws-Number-X.
     03  ws-Number       pic 9(6)        value zero.
 01  ws-Amount-X-14      pic x(14).
 01  ws-Amount-X.
     03  ws-Amount       pic 9(13)       value zero.        *> In pence of 4 places eg 9(9)[v]9999
 01  ws-Chk-Number       pic 9(6).
 01  ws-Chk-Amount       pic 9(13).
 01  ws-Chk-Amount-V     redefines ws-Chk-Amount pic 9(9)v9(4).
 01  ws-Amount-Length    binary-char     value zero.
 01  ws-Pence-Length     binary-char     value zero.
 01  ws-Pounds-Length    binary-char     value zero.
*>
 01  work-fields.
     03  ws-reply        pic x.
     03  a               binary-char unsigned value zero.
     03  b               pic 9(4)   comp     value zero.
     03  c               pic 9(4)   comp     value zero.
     03  c2              pic 9(4)   comp     value zero.
     03  d               pic 9               value zero.     *> flag for decimal point
     03  e               pic 9               value zero.
     03  f               pic 99.
     03  ws-stock-dates.
         05  ws-Stock-Order-Date pic x(12).
         05  ws-Stock-Order-Due  pic x(12).
     03  ws-Test-Date    pic x(10).
*>
 01  ws-date-formats.            *> not yet used
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
 01  File-Info                          value zero.
     05 File-Size-Bytes  pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp.
     05 Mod-MO           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp.
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp. *> Always 00
*>
 copy "wsfnctn.cob".
 copy "wsmaps03.cob".
 copy "wsstock.cob".                    *>  replacing WS-Stock-Desc by Stock-Desc.
*>
*> REMARK OUT ANY IN USE
*>
 01  Dummies-4-Unused-ACAS-FH-Calls.      *> Call blk at zz080-ACAS-Calls
*>     03  System-Record          pic x.
     03  Default-Record         pic x.
     03  Final-Record           pic x.
     03  System-Record-4        pic x.
     03  WS-Ledger-Record       pic x.
     03  WS-Posting-Record      pic x.
     03  WS-Batch-Record        pic x.
     03  WS-IRS-Posting-Record  pic x.
     03  WS-Stock-Audit-Record  pic x.
*>     03  WS-Stock-Record        pic x.
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
 01  Error-Messages.
*> System Wide
     03  ST000           pic x(36) value "ST000 Error on Writing to Stock Rec.".
*> Module Specific
     03  ST601           pic x(42) value "ST601 Error on Open/Reading Import File - ".
     03  ST602           pic x(31) value "ST602 Note error and hit return".
     03  ST603           pic x(31) value "ST603 Note total and hit return".
     03  ST604           pic x(39) value "ST604 Note error and hit return to quit".
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
 01  to-day              pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 Declaratives.
*>
 File-Error-On-IF section.
*>
     use after error procedure on Import-File.
 a00-IF-Error-1.
     if       fs-reply not = zero
              perform  Eval-Status
              display  ST601          at 2301
              display  fs-reply       at 2337
              display  Evaluation-Msg at 2340
              display  ST602          at 2401
              accept   ws-reply       at 2433
              close Import-File
              set      fn-Close to true
              call     "acas011" using System-Record
                                       WS-Stock-Record
                                       File-Access
                                       File-Defs
                                       ACAS-DAL-Common-data
              end-call
     end-if      *> above MUST be a direct call as subs not accessable in GC
     exit    program.
*>
 Eval-Status.
*>==========
*>
     move     spaces to Evaluation-Msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by Evaluation-Msg.
*>
 main-exit.
     exit.
*>
 end declaratives.
*>
 aa000-Core              section.
*>******************************
*>
*>
*> After changing this program to match your requirements REMARK out (with *>)
*>  the next 5 non comment lines, ending with GOBACK.
*>
     display  "THIS PROGRAM MUST BE CHANGED BEFORE USE"
                    at 0101 with foreground-color 2  erase eos.
     display  ST604 at 0301 with foreground-color 2.
     accept   Accept-Reply at 0341.
     GOBACK.
*>
 aa010-Get-File-for-Import.
     perform  zz010-Display-Heading.
     display  "Provide full path and file name of file to be imported" at 0701 with foreground-color 2.
     accept   File-101 at 0902 with foreground-color 6 update.
     perform  ba000-Import-Stock.
     go       to aa999-exit.
*>
 a10-Stock-Error-1.
     if       fs-reply not = zero
              perform  Eval-Status-2
              display  ST000    at 2301 with foreground-color 4 highlight
              display  fs-reply at 2338 with foreground-color 4 highlight
              display  Evaluation-Msg at 2340
              display  ST602          at 2401
              accept   ws-reply       at 2433
              close    Import-File
              perform  Stock-Close
     end-if
     goback.
*>
 Eval-Status-2.
*>============
*>
     move     spaces to Evaluation-Msg.
 copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                     msg    by Evaluation-Msg.
*>
 maps04.
     call     "maps04" using maps03-ws.
*>
 aa999-Exit.
     goback.
*>
 ba000-Import-Stock      section.
*>******************************
*>
*> New for RDB - Create Analysis file and data if not exist.
*>
     if       FS-Cobol-Files-Used            *> Analysis file
              call  "CBL_CHECK_FILE_EXIST" using File-15
                                                 File-Info
              if    return-code not = zero          *> not = zero - No file found
                    move 1 to ws-Process-Func
                              ws-Sub-Function
                    call "sl070" using ws-Calling-Data
                                       System-Record
                                       To-Day
                                       File-Defs
              end-if
     end-if
     open     input Import-File.
     perform  Stock-Open.
*>
 ba010-Get-A-Record.
*>
*>  If stock item is =< 7 make both stock & Abrev the same otherwise create new Abrev key
*>  incremented by 1 from ws-Abrev-Value
*>
     initialize Import-Record.            *> Needed ? cant do any harm !
     move     spaces to ws-stock-dates.            *> NEEDED
*>
     read     Import-File record at end
              go to  ba998-Main-End.
     add      1 to ws-Record-Count.
     initialize WS-Stock-Record with filler.
     if       Process-Comma
              go to ba030-Process-Comma.
*>
 ba020-Process-Regular.
*>
*>  ************************************************************
*>  *  THIS NEEDS TO BE CHANGED TO REFLECT import file LAYOUT  *
*>  *                 DO NOT USE 'AS IS'                       *
*>  ************************************************************
*>
*>  Change this to match up with the import record format and note
*>   that the references to WS-Temp- name refer to the 01 redefines
*>   of the import-record which may well need to be replaced with
*>    another definition and the following code changed but hopefully
*>    you will get the idea.
*>
     move     corresponding WS-Temp-Stock-Record to WS-Stock-Record.
*>
*>  The above line will ONY work if the import file fields match up with the
*>  layout for the ACAS STock file and this is UNLIKELY but the above should not
*>  cause any harm but remarked it out and make changes below to match with the
*>  data structure of the import file.
*>
     move     WS-Temp-Stock-Key to WS-Stock-Key.
     perform  varying a from 13 by -1
                 until ws-Stock-Key (a:1) not = space
                                         OR a = 1
              continue
     end-perform
*>
     if       a < 8
              move ws-Temp-Stock-Key to WS-Stock-Abrev-Key
     else
              add   1              to ws-Abrev-Value
              move  ws-Abrev-Value to WS-Stock-Abrev-Key
     end-if
*>
*>  Instead of prev. if, when abrev key exists in imported record :
*>
*>     move     ws-Abrev-Key to WS-Stock-Abrev-Key.
*>
     move     ws-Temp-Stock-Desc to WS-Stock-Desc.
     if       ws-Reset-Hist
              initialize Stock-Mthly-Running-Totals
                         Stock-History
     end-if
*>
*>        ANY MORE MOVES NEEDED THEN HERE ??
*>
     perform  Stock-Write.
     add      1 to ws-Write-Count.
     go       to ba010-Get-A-Record.
*>
 ba030-Process-Comma.
*>
*>  ************************************************************
*>  *  THIS NEEDS TO BE CHANGED TO REFLECT import file LAYOUT  *
*>  *                 DO NOT USE 'AS IS'                       *
*>  ************************************************************
*>
     move     1 to b.
*>
*> Used if not abrev-key available in imput file so increment by 1 for each record
*>   No not the best. NOTE that both keys MUST NOT have duplicate keys
*>
     unstring Import-Record  delimited by "," into WS-Stock-Key count c pointer b.
     if       c not > 7
              move WS-Stock-Key to WS-Stock-Abrev-Key
     else
              add 1 to ws-Abrev-Value
              move ws-Abrev-Value to WS-Stock-Abrev-Key
    end-if
*>
*>  Here we are using a default supplier but if used on old file use rem'd unstring instead
*>
     move     ws-Default-Supplier to Stock-Supplier-P1 in WS-Stock-Record.
*>     unstring Import-Record  delimited by "," into Stock-Supplier-P1 in WS-Stock-Record pointer b.
*>
     unstring Import-Record  delimited by "," into ws-Test-Desc pointer b.
     if       ws-Test-Desc (1:1) = quote or "'" or "`"
              move ws-Test-Desc (1:1) to ws-Delimiter-Found
              perform varying c from 36 by -1 until c < 4
                                                 or ws-Test-Desc (c:1) = ws-Delimiter-Found
                       continue
              end-perform
              move ws-Test-Desc (2:c - 2) to WS-Stock-Desc
     else
              move ws-Test-Desc to WS-Stock-Desc
     end-if
     move     ws-Default-PA to Stock-PA-Code in WS-Stock-Record.
     move     ws-Default-SA to Stock-SA-Code in WS-Stock-Record.
     move     "N"           to Stock-Services-Flag in WS-Stock-Record.
*>
     move     zero to ws-Number ws-Number-X-8.
     unstring Import-Record  delimited by "," into ws-Number-X-8 count c pointer b.
     perform  zz025-Format-Number.
     move     ws-Chk-Number to Stock-ReOrder-Pnt in WS-Stock-Record.
*>
     move     zero to ws-Number ws-Number-X-8.
     unstring Import-Record  delimited by "," into ws-Number-X-8 count c pointer b.
     perform  zz025-Format-Number.
     move     ws-Chk-Number to Stock-Std-ReOrder in WS-Stock-Record.
*>
     move     zero to ws-Number ws-Number-X-8.
     unstring Import-Record  delimited by "," into ws-Number-X-8 count c pointer b.
     perform  zz025-Format-Number.
     move     ws-Chk-Number to Stock-Back-Ordered in WS-Stock-Record.
*>
     move     zero to ws-Number ws-Number-X-8.
     unstring Import-Record  delimited by "," into ws-Number-X-8 count c pointer b.
     perform  zz025-Format-Number.
     move     ws-Chk-Number to Stock-On-Order in WS-Stock-Record.
*>
     move     zero to ws-Number ws-Number-X-8.
     unstring Import-Record  delimited by "," into ws-Number-X-8 count c pointer b.
     perform  zz025-Format-Number.
     move     ws-Chk-Number to Stock-Held in WS-Stock-Record.
*>
     move     zero to ws-Number ws-Number-X-8.
     unstring Import-Record  delimited by "," into ws-Number-X-8 count c pointer b.
     perform  zz025-Format-Number.
     move     ws-Chk-Number to Stock-Pre-Sales in WS-Stock-Record.
*>
*> Formats of import amounts need to be examined and these changed to reflect it
*>  including ws- field sizes
*>  The move will truncate the source field as its a 9(9)v9999 moving to smaller fields
*>    but that is ok as digits trancated are zero but still check it after running
*>
     move     zero to ws-Amount ws-Amount-X-14.
     unstring Import-Record  delimited by "," into ws-Amount-X-14 count c pointer b.
     perform  zz030-Format-Amount.
     move     ws-Chk-Amount-V to Stock-Retail in WS-Stock-Record.
*>
     move     zero to ws-Amount ws-Amount-X-14.
     unstring Import-Record  delimited by "," into ws-Amount-X-14 count c pointer b.
     perform  zz030-Format-Amount.
     move     ws-Chk-Amount-V to Stock-Cost in WS-Stock-Record.
*>
*>  Note that LAST field in record must also be delimited by space
*>
     move     zero to ws-Amount ws-Amount-X-14.
     unstring Import-Record  delimited by "," or space into ws-Amount-X-14 count c pointer b.
     perform  zz030-Format-Amount.
     move     ws-Chk-Amount-V to Stock-Value in WS-Stock-Record.
*>
*>  Here for Due and order dates if present and they will be in quotes and dates are ASSUMED as 8 chars long
*>    So we will ignore the first and last chars (quote)
*>
     unstring Import-Record  delimited by "," or space into ws-Stock-Order-Date pointer b.
     move     ws-Stock-Order-Date (2:10) to ws-Test-Date.
     perform  zz050-Validate-Date.
     if       u-Bin not zero
              move u-bin to Stock-Order-Date in WS-Stock-Record
     end-if
*>
*> IF this is the LAST field in the record add 'or space' but if not can remove 'or space '
*>     Same applies above field
*>
     unstring Import-Record  delimited by "," or space into ws-Stock-Order-Due pointer b.
     move     ws-Stock-Order-Due (2:10) to ws-Test-Date.
     perform  zz050-Validate-Date.
     if       u-Bin not zero
              move u-bin to Stock-Order-Due in WS-Stock-Record
     end-if.
*>
 ba040-Write-Stock.
     perform  Stock-Write.
     add      1 to ws-Write-Count.
     go       to ba010-Get-A-Record.
*>
 ba998-Main-End.
     perform  Stock-Close.
     close    Import-File.
     move     ws-Record-Count to ws-Disp-Count.
     display  "Records Imported - " at 0601 with foreground-color 2 erase eos.
     display  ws-Disp-Count         at 0620 with foreground-color 2.
     move     ws-Write-Count  to ws-Disp-Count.
     display  "Records Written  - " at 0601 with foreground-color 2.
     display  ws-Disp-Count         at 0620 with foreground-color 2.
     display  ST603                 at 0801 with foreground-color 2.
     accept   ws-reply              at 0835.
*>
 ba999-Exit.
     exit     section.
*>
*>****************************************************
*>               Common Routines Block               *
*>****************************************************
*>
 zz010-Display-Heading      section.
*>*********************************
*>
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  usera at 0301 with foreground-color 3.
     perform  zz010-convert-date.
     display  u-date at 0171 with foreground-color 2.
*>
     display  "Stock File Importer" at 0124 with foreground-color 2.
     go       to zz010-Exit.
*>
 zz010-convert-date.
*>
*> Convert from UK to selected form
*>
     move     to-day to u-date.
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
 zz010-exit.
     exit     section.
*>
 zz025-Format-Number       section.
*>********************************
*>
*> C has char count
*>
     perform  zz027-Clean-Number.        *> remove any quotes if present
     move     zero to ws-Chk-Number.
     if       ws-Number-X not numeric
              go to zz025-Exit.
*>
     perform  varying d from 6 by -1 until c < 1
              move ws-Number (c:1) to ws-Chk-Number (d:1)
              subtract 1 from c
     end-perform.
*>
*>  Now have number right justified in ws-chk-number
*>
 zz025-Exit.
     exit     section.
*>
 zz027-Clean-Number        section.
*>********************************
*>
*> Check of number is in quotes and clear them otherwise move number
*>
     move     zeros to ws-Number.
     move     c to c2.
     if       ws-Number-X-8 (1:1) = quote or "'" or "`"
              move ws-Number-X-8 (1:1) to ws-Delimiter-Found
              perform varying c from 8 by -1 until c < 3
                                                 or ws-Number-X-8 (c:1) = ws-Delimiter-Found
                       continue
              end-perform
              move ws-Number-X-8 (2:c - 2) to ws-Number
     else
              move ws-Number-X-8 (1:c2) to ws-Number-X        *> now have unjustified number but not number?
     end-if
     if       ws-Number not numeric
              move zero to ws-Number
     end-if.
*>
 zz027-Exit.
     exit     section.
*>
 zz030-Format-Amount       section.
*>
*> A reminder of what we can get: 0.n 0.nn nnnn nn.n nn.nn
*> Source = ws-amount-X-14
*> target = ws-chk-amount
*>
     move     zeros to ws-Amount.
     move     c  to c2.
     if       ws-Amount-X-14 (1:1) = quote or "'" or "`"
              move ws-Amount-X-14 (1:1) to ws-Delimiter-Found
              perform varying c from c2 by -1 until c < 3        *> Should happen on 1st pass
                                                 or ws-Amount-X-14 (c:1) = ws-Delimiter-Found
                      continue
              end-perform
              move ws-Amount-X-14 (2:c2 - 2) to ws-Amount-X    *> got 9(9).9999 LEFT justified
              if   c = c2
                   subtract 2 from c2                *> including the '.'
              else                        *> We have problems with the data so quit
                 display "Problem with amount - "       at 1601 with foreground-color 3 highlight
                 display ws-Amount-X-14                 at 1623 with foreground-color 3
                 display "Has invalid quotes or other!" at 1638 with foreground-color 3 highlight
                 display ST604                          at 1701 with foreground-color 3
                 accept  ws-reply                       at 1741
                 close import-File
                 perform Stock-Close
                 stop run
              end-if
     else
              move ws-Amount-X-14 (1:c2) to ws-Amount-X        *> now have left justified number
     end-if
     move     c2 to ws-Amount-Length                *> including the '.'
     move     zero to e.                    *> test if we have a period
     inspect  ws-Amount-X tallying e for all ".".
     if       e not = zero                    *> We do, so find it
              perform  varying c from c2 by -1 until ws-Amount-X (c:1) = "."
                                                  or c < 2    *> cant be 1st char so this test should not happen !
                       continue
              end-perform
     end-if                            *> if c = 1 then no pounds & all is pence / dollars  cents etc
*>
*>  Now we know where the period is within ws-amount-X as c
*>  AND If e = zero we have whole number only
*>
     move     zeros to ws-Chk-Amount.
     if       e not zero
       and    c > 1
              compute f = c + 1                     *> 1st pence position
              compute ws-Pence-length = c2 - c      *> pence length
              compute ws-Pounds-Length = c - 1
              move ws-Amount (f:ws-Pence-Length)  to ws-Chk-Amount (10:ws-Pence-Length)
              move ws-Amount (1:ws-Pounds-Length) to ws-Chk-Amount (10 - ws-Pounds-Length:ws-Pounds-Length)
     end-if
     if       e = zero                                *> Only pounds and no pence or '.'
              move ws-Amount-Length to f
              move ws-Amount (1:f) to ws-Chk-Amount (10 - f:f)            *> got the pounds
     end-if
*>
*>  Test the data and if this appears its a possible program bug or a data problem
*>
     if     ws-Chk-Amount not numeric                        *> We have problems with the data so quit
            display "Problem with amount - " at 1601 with foreground-color 3 highlight
            display ws-Amount-X-14           at 1623 with foreground-color 3
            display "Has become - "          at 1638 with foreground-color 3 highlight
            display ws-Chk-Amount            at 1651 with foreground-color 3
            display ST604                    at 1701 with foreground-color 3
            accept  ws-reply                 at 1741
            close import-File
            perform Stock-Close
            stop run
     end-if.

 zz030-Exit.
     exit     section.
*>
 zz050-Validate-Date       section.
*>********************************
*>
*>  Converts USA/Intl to UK date format for processing and
*>   modified for Import data ws field.
*>========================================================
*> Input:   ws-test-date
*> output:  u-date/ws-date as uk date format
*>          u-bin not zero if valid date
*>
     move     ws-test-date to ws-date.
     if       ws-Import-Date-Format = zero
              move 1 to ws-Import-Date-Format.
     if       ws-Date-UK
              go to zz050-test-date.
     if       ws-Date-USA                *> swap month and days
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
     perform  maps04.
*>
 zz050-exit.
     exit     section.
*>
 copy "Proc-ACAS-FH-Calls.cob".
*>
