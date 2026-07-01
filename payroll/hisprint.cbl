       >>source free
*>****************************************************************
*>                  Employee History Reporting                   *
*>                                                               *
*>            Uses RW (Report writer for prints)                 +
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       hisprint.  *> to be renamed pynnn later.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 29/12/2025.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Employee History Reporting.
*>                       This program uses RW (Report Writer) - I hope, as
*>                         very rusty using it.
*>
*>                      Semi-sourced from Basic code from hisprint.
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.
*>**
*>    Functions Used:
*>**
*>    Files used :
*>                      pypr1.   Params
*>                      pyemp.   Employee Master.
*>                      pyhis.   Employee History.
*>
*>    Error messages used.   CHANGES NEEDED <<<<<<<<<<
*> System wide:
*>                      SY001, 3 10 - 13.
*> Program specific:
*>                      PY001 - 2.
*>                      PY804, 6, 8, 9.
*>**
*> Changes:
*> 29/12/2025 vbc - 1.0.00 Created - Started coding.
*> 19/01/2026 vbc          Mostly completed just final cleans for RW not that date
*>                         Company history is in formm ccyy/mm/dd - mostly for
*>                         testing so will need to create a new zznnn-convert
*>                         module to -> US format but code creating COH not yet
*>                         done.
*> 20/01/2026 vbc          Completed subject to testing -  none done yet.
*>**
*>*************************************************************************
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
*>================================
*>
 copy "envdiv.cob".
 SPECIAL-NAMES.
       CRT STATUS is COB-CRT-STATUS.
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
*>
 input-output            section.
 file-control.
 copy "selpyparam1.cob".
 copy "selpyemp.cob".
 copy "selpyhis.cob".
 copy "selpyded.cob".
 copy "selpycoh.cob".
*>
 copy "selprint.cob".    *> 132
*>
 data                    division.
*>================================
*>
 file section.
*>
 copy "fdpyparam1.cob".
 copy "fdpyemp.cob".
 copy "fdpyhis.cob".
 copy "fdpyded.cob".
 copy "fdpycoh.cob".
*>
 fd  Print-File
     reports are Employee-History-Report
                 Company-History-Report.
*>
 working-storage section.
*>-----------------------
 77  prog-name               pic x(17) value "hisprint (1.0.00)".  *> First release pre testing.
*>
*>  This will print 1 copy to CUPS print spool specified on line 3 override via setup at SOJ
*>
 copy "print-spool-command.cob".     *> CHECK PRN file for content Landscape mode
*>
 copy "wsmaps03.cob".
 copy "wsfnctn.cob".
*>
 copy "Test-Data-Flags.cob".           *> set sw-Testing to zero to stop logging.
*>                                        ABOVE SHOULD BE OFF
*> REMARK OUT ANY not IN USE
*>
 01  WS-Data.
     03  Menu-Reply          pic x.
     03  PY-PR1-Status       pic xx.
     03  PY-Emp-Status       pic xx.
     03  PY-His-Emp-Status   pic xx.
     03  PY-Ded-Status       pic xx.
     03  PY-Coh-Status       pic xx.
*>
     03  WS-Emp-Stat         pic x(12).
     03  WS-Max              binary-char  value zero. *> from PY-PR1-Max-Sys-Eds & MUST be created in PY setup
     03  WS-Lines-Per-Emp    binary-char  value 22.   *> lines per employee - NOT USED YET
*>
     03  WS-Reply            pic x.
     03  WS-Eval-Msg         pic x(25)    value spaces.
     03  WS-Env-Columns      pic 999      value zero.
     03  WS-Env-Lines        pic 999      value zero.
     03  WS-22-Lines         pic 99.
     03  WS-23-Lines         pic 99.
     03  WS-Lines            pic 99.
     03  A                   pic 99       value zero.
     03  B                   pic 99       value zero.
     03  C                   pic 99       value zero.
     03  WS-Page-Lines       binary-char unsigned value 56.   *> Narrow reports as system is for Landscape used.
     03  WS-Rec-Cnt          pic 99       value zero.
     03  WS-Page-Cnt         pic 999      value zero.
     03  WS-Line-Cnt         pic 999      value 90.   *> Force heads at start
*>
 01  WS-Test-Date            pic x(10).
 01  WS-Date-Formats.
     03  WS-Swap             pic 99.
     03  WS-Conv-Date        pic x(10).
     03  WS-Date             pic x(10)   value "99/99/9999".
     03  WS-UK redefines WS-Date.   *> Other optional format
         05  WS-Days         pic 99.
         05  filler          pic x.
         05  WS-Month        pic 99.
         05  filler          pic x.
         05  WS-Year         pic 9(4).
     03  WS-USA redefines WS-Date.  *> Default format
         05  WS-USA-Month    pic 99.
         05  filler          pic x.
         05  WS-USA-Days     pic 99.
         05  filler          pic x.
         05  filler          pic 9(4).
     03  WS-Intl redefines WS-Date.   *> Not used.
         05  WS-Intl-Year    pic 9(4).
         05  filler          pic x.
         05  WS-Intl-Month   pic 99.
         05  filler          pic x.
         05  WS-Intl-Days    pic 99.
*>
 01  Error-Messages.   *> ANY NEEDED ???
*> System Wide
     03  SY001           pic x(46) value "SY001 Aborting run - Note error and hit Return".
     03  SY003           pic x(51) value "SY003 Aborting function - Note error and hit Return".
     03  SY010           pic x(46) value "SY010 Terminal program not set to length => 28".
     03  SY013           pic x(47) value "SY013 Terminal program not set to Columns => 80".
*>
*> Module General
*>
     03  PY001           pic x(45) value "PY001 Payroll Parameter file does not exist -".
     03  PY002           pic x(32) value "PY002 Read PARAM record Error = ".
*>
*> Module specific    <<<< REMOVE UNUSED
*>
     03  PY804           pic x(47) value "PY804 Unexpected end of Company History File = ".
     03  PY806           pic x(31) value "PY806 Employee File not Found -".
     03  PY808           pic x(32) value "PY808 Deduction File not found -".
     03  PY809           pic x(38) value "PY809 Company History File not found -".
*>
 01  Error-Code          pic 999.
*>
 01  COB-CRT-Status      pic 9(4)         value zero.
     copy "screenio.cpy".
*>
 copy "wstime.cob".
*>
 linkage section.
*>***************
*>
 copy "wscall.cob".
 copy "wssystem.cob"   replacing System-Record by WS-System-Record.
 copy "wsnames.cob".
*>
 01  To-Day              pic x(10).
*>
 Report section.
*>**************
*>
 RD  Employee-History-Report
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 5
     Last  Detail WS-Page-Lines.
*>
*> Print layouts to 132 cols Landscape
*>
 01  Report-Emp-Head Type is Page Heading.
     03  line + 1.
         05  col  50     pic x(40)   source UserA.
         05  col 110     pic x(10)   source U-Date.  *> IS this correct format ?
         05  col 122     pic x(8)    source WSD-Time.
     03  line + 1.
         05  col  1      pic x(17)   source Prog-Name.
         05  col 51      pic x(19)   value "ACAS Payroll System".
         05  col 124     pic x(5)    value "Page ".
         05  col 129     pic zz9     source Page-Counter.
     03  Line + 1.
         05  col 53      pic x(53)   value "Employee History Report".
*>
 01  Employee-Report-Foot Type Report Footing.
     03  line + 2.
         05  col 5      pic x(22)    value "Total Records printed ".
         05  col 28     pic zzz9     source WS-Rec-Cnt.
*>
 01  Employee-Detail type is detail.
     03  line 5.
         05  col  5      pic x(16)   value "Employee Number:".
         05  col 25      pic z(5)99  source Emp-No.
         05  col 35      pic x(5)    value "Name:".
         05  col 42      pic x(31)   source Emp-Name.
         05  col 75      pic x(12)   source WS-Emp-Stat.
*>
     03  line 6.
         05  col 10      pic x(15)       value "NET QTD INCOME:".
         05  col 26      pic zzz,zz9.99  source His-QTD-Net.
         05  col 45      pic x(15)       value "NET YTD INCOME".
         05  col 62      pic zzz,zz9.99  source His-YTD-Net.
*>
     03  line 8.
         05  col 17                  value "TAXABLE             OTHER              OTHER".
         05  col 94                  value "FICA             FEDERAL".
     03  line 9.
         05  col 18                  value "INCOME            TAXABLE            UNTAXED         " &
                                           "      TIPS            TAXABLE        WITHHOLDING".
*>
     03  line 10.
         05  col  2      pic x(10)       value "QTY AMOUNT".
         05  col 14      pic zzz,zz9.99  source His-QTD-Income-Taxable.
         05  col 33      pic zzz,zz9.99  source His-QTD-Other-Taxable.
         05  col 52      pic zzz,zz9.99  source His-QTD-Other-NonTaxable.
         05  col 71      pic zzz,zz9.99  source His-QTD-Tips.
         05  col 90      pic zzz,zz9.99  source His-QTD-Fica-Taxable.
         05  col 109     pic zzz,zz9.99  source His-QTD-FWT.
     03  line 11.
         05  col  2      pic x(10)       value "YTY AMOUNT".
         05  col 14      pic zzz,zz9.99  source His-YTD-Income-Taxable.
         05  col 33      pic zzz,zz9.99  source His-YTD-Other-Taxable.
         05  col 52      pic zzz,zz9.99  source His-YTD-Other-NonTaxable.
         05  col 71      pic zzz,zz9.99  source His-YTD-Tips.
         05  col 90      pic zzz,zz9.99  source His-YTD-Fica-Taxable.
         05  col 109     pic zzz,zz9.99  source His-YTD-FWT.
*>
     03  line 13.
         05  col 18                  value "STATE              LOCAL".
         05  col 111                 value "OTHER".
     03  line 14.
         05  col 15                  value "WITHHOLDING        WITHHOLDING             FICA".
         05  col 78                  value "SDI".
         05  col 97                  value "EIC".
         05  col 110                 value "DEDUCTIONS".
*>
     03  line 15.
         05  col  2                  value "QTD AMOUNT".
         05  col 14      pic zzz,zz9.99  source His-QTD-SWT.
         05  col 33      pic zzz,zz9.99  source His-QTD-LWT.
         05  col 52      pic zzz,zz9.99  source His-QTD-FICA.
         05  col 71      pic zzz,zz9.99  source His-QTD-SDI.
         05  col 90      pic zzz,zz9.99  source His-QTD-EIC.
         05  col 109     pic zzz,zz9.99  source His-QTD-Other-Ded.
     03  line 16.
         05  col  2                  value "YTD AMOUNT".
         05  col 14      pic zzz,zz9.99  source His-YTD-SWT.
         05  col 33      pic zzz,zz9.99  source His-YTD-LWT.
         05  col 52      pic zzz,zz9.99  source His-YTD-FICA.
         05  col 71      pic zzz,zz9.99  source His-YTD-SDI.
         05  col 90      pic zzz,zz9.99  source His-YTD-EIC.
         05  col 109     pic zzz,zz9.99  source His-YTD-Other-Ded.
*>
     03  line 18.
         05  col  8      value "SYSTEM E/D'S   QTD" present when PY-PR1-Max-SYS-Eds > 0.
         05  col 36      value "YTD"                present when PY-PR1-Max-SYS-Eds > 0.
         05  col 45      value "EMPLOYEE E/D'S"     present when PY-PR1-Max-Emp-Eds > 0.
         05  col 66      value "QTD"                present when PY-PR1-Max-Emp-Eds > 0.
         05  col 79      value "YTD"                present when PY-PR1-Max-Emp-Eds > 0.
         05  col 88      value "STANDARD RATE UNITS".
         05  col 109     value "QTD".
         05  col 122     value "YTD".
     03  line 19.
         05  col  1      pic x(15)       source Ded-Sys-Desc (1) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source His-QTD-Sys (1)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source His-YTD-Sys (1)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 43      pic x(15)       source Emp-ED-Desc (1)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 59      pic zzz,zz9.99  source His-QTD-Emp (1)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 72      pic zzz,zz9.99  source His-YTD-Emp (1)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (1).
         05  col 102     pic zzz,zz9.99  source His-QTD-Units (1).
         05  col 115     pic zzz,zz9.99  source His-YTD-Units (1).
     03  line 20. *>
         05  col  1      pic x(15)       source Ded-Sys-Desc (2) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source His-QTD-Sys (2)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source His-YTD-Sys (2)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 43      pic x(15)       source Emp-ED-Desc (2)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 59      pic zzz,zz9.99  source His-QTD-Emp (2)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 72      pic zzz,zz9.99  source His-YTD-Emp (2)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (2).
         05  col 102     pic zzz,zz9.99  source His-QTD-Units (2).
         05  col 115     pic zzz,zz9.99  source His-YTD-Units (2).
     03  line 21. *>
         05  col  1      pic x(15)       source Ded-Sys-Desc (3) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source His-QTD-Sys (3)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source His-YTD-Sys (3)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 43      pic x(15)       source Emp-ED-Desc (3)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 59      pic zzz,zz9.99  source His-QTD-Emp (3)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 72      pic zzz,zz9.99  source His-YTD-Emp (3)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (3).
         05  col 102     pic zzz,zz9.99  source His-QTD-Units (3).
         05  col 115     pic zzz,zz9.99  source His-YTD-Units (3).
     03  line 22.
         05  col  1      pic x(15)       source Ded-Sys-Desc (4)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source His-QTD-Sys (4)   present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source His-YTD-Sys (4)   present when PY-PR1-Max-SYS-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (4).
         05  col 102     pic zzz,zz9.99  source His-QTD-Units (4).
         05  col 115     pic zzz,zz9.99  source His-YTD-Units (4).
     03  line 23.
         05  col  1      pic x(15)       source Ded-Sys-Desc (5) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source His-QTD-Sys (5)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source His-YTD-Sys (5)  present when PY-PR1-Max-SYS-Eds > 0.
*>

*>  Reminder of how, etc also see st010rw-3.02.cbl in RW  or from IRS (RW folders)
 *>    03  WIP-Data    line plus 1
 *>           present when Stock-Services-Flag not = "Y"
 *>                    and (Stock-Construct-Bundle not = zero
 *>                     or Stock-Under-Construction not = zero
 *>                     or Stock-Work-in-Progress not = zero
 *>                     or Stock-Construct-Item not = spaces).
 *>        05  rd-Wip-Data col   1     pic x(132)  value spaces.
*>

 RD  Company-History-Report
     control      Final
     Page Limit   WS-Page-Lines
     Heading      1
     First Detail 5
     Last  Detail WS-Page-Lines.
*>
 01  Company-Head  Type Page Heading.
*>
*> Print layouts to 132 cols Landscape
*>
     03  line  + 1.
         05  col  50     pic x(40)   source UserA.
         05  col 110     pic x(10)   source U-Date.
         05  col 122     pic x(8)    source WSD-Time.
     03  line + 1.
         05  col  1      pic x(17)   source Prog-Name.
         05  col 51      pic x(19)   value "ACAS Payroll System".
         05  col 124     pic x(5)    value "Page ".
         05  col 129     pic zz9     source Page-Counter.
     03  Line  + 1.
         05  col 53      pic x(53)   value "Company History Report".
*>
 01  Company-Detail-Lines-Block-1 type is detail.
     03  line 5.
         05  col 10      pic x(15)       value "NET QTD INCOME:".
         05  col 26      pic zzz,zz9.99  source Coh-QTD-Net.
         05  col 45      pic x(15)       value "NET YTD INCOME".
         05  col 62      pic zzz,zz9.99  source Coh-YTD-Net.
*>
     03  line 6.
         05  col 20                  value "TAXABLE           OTHER            OTHER".
         05  col 88                  value "FICA           FEDERAL          STATE".
     03  line 7.
         05  col 21                  value "INCOME          TAXABLE          UNTAXED       " &
                           	     "   TIPS           TAXABLE        WITHHOLDING     WITHHOLDING".
*>
     03  line + 1.
         05  col  2      pic x(10)       value "QTY AMOUNT".
         05  col 14      pic zzz,zz9.99  source Coh-QTD-Income-Taxable.
         05  col 31      pic zzz,zz9.99  source Coh-QTD-Other-Taxable.
         05  col 48      pic zzz,zz9.99  source Coh-QTD-Other-NonTaxable.
         05  col 65      pic zzz,zz9.99  source Coh-QTD-Tips.
         05  col 82      pic zzz,zz9.99  source Coh-QTD-Fica-Taxable.
         05  col 99      pic zzz,zz9.99  source Coh-QTD-FWT-Liab.
         05  col 116     pic zzz,zz9.99  source Coh-QTD-SWT-Liab.
     03  line + 1.
         05  col  2      pic x(10)       value "YTY AMOUNT".
         05  col 14      pic zzz,zz9.99  source Coh-YTD-Income-Taxable.
         05  col 31      pic zzz,zz9.99  source Coh-YTD-Other-Taxable.
         05  col 48      pic zzz,zz9.99  source Coh-YTD-Other-NonTaxable.
         05  col 65      pic zzz,zz9.99  source Coh-YTD-Tips.
         05  col 82      pic zzz,zz9.99  source Coh-YTD-Fica-Taxable.
         05  col 99      pic zzz,zz9.99  source Coh-YTD-FWT-Liab.
         05  col 116     pic zzz,zz9.99  source Coh-QTD-SWT-Liab.
*>
     03  line + 2.
         05  col 18                  value "LOCAL".
         05  col 45                  value "COMPANY".
         05  col 118                 value "OTHER".
     03  line + 1   *> 12.
         05  col 15                  value "WITHHOLDING       FICA".
         05  col 47                  value "FICA".
         05  col 62                  value "SDI".
         05  col 76                  value "EIC".
         05  col 89                  value "FUTA".
         05  col 104                 value "SUI".
         05  col 114                 value "DEDUCTIONS".
     03  line + 1.
         05  col  2                  value "QTD AMOUNT".
         05  col 13      pic zzz,zz9.99  source Coh-QTD-LWT-Liab.
         05  col 27      pic zzz,zz9.99  source Coh-QTD-FICA-Liab.
         05  col 41      pic zzz,zz9.99  source Coh-QTD-CO-FICA-Liab.
         05  col 55      pic zzz,zz9.99  source Coh-QTD-SDI-Liab.
         05  col 69      pic zzz,zz9.99  source Coh-QTD-EIC-Credit.
         05  col 83      pic zzz,zz9.99  source Coh-QTD-CO-FUTA-Liab.
         05  col 97      pic zzz,zz9.99  source Coh-QTD-CO-SUI-Liab.
         05  col 111     pic zzz,zz9.99  source Coh-QTD-Other-Ded.
     03  line + 1. *> 14.
         05  col  2                  value "YTD AMOUNT".
         05  col 13      pic zzz,zz9.99  source Coh-YTD-LWT-Liab.
         05  col 27      pic zzz,zz9.99  source Coh-YTD-FICA-Liab.
         05  col 41      pic zzz,zz9.99  source Coh-YTD-CO-FICA-Liab.
         05  col 55      pic zzz,zz9.99  source Coh-YTD-SDI-Liab.
         05  col 69      pic zzz,zz9.99  source Coh-YTD-EIC-Credit.
         05  col 83      pic zzz,zz9.99  source Coh-YTD-CO-FUTA-Liab.
         05  col 97      pic zzz,zz9.99  source Coh-YTD-CO-SUI-Liab.
         05  col 111     pic zzz,zz9.99  source Coh-YTD-Other-Ded.
     03  line + 2.  *>16.
         05  col  8      value "SYSTEM E/D'S   QTD" present when PY-PR1-Max-SYS-Eds > 0.
         05  col 36      value "YTD"                present when PY-PR1-Max-SYS-Eds > 0.
         05  col 45      value "EMPLOYEE E/D'S"     present when PY-PR1-Max-Emp-Eds > 0.
         05  col 66      value "QTD"                present when PY-PR1-Max-Emp-Eds > 0.
         05  col 79      value "YTD"                present when PY-PR1-Max-Emp-Eds > 0.
         05  col 88      value "STANDARD RATE UNITS".
         05  col 109     value "QTD".
         05  col 122     value "YTD".
     03  line + 1.
         05  col  1      pic x(15)       source Ded-Sys-Desc (1) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source Coh-QTD-Sys (1)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source Coh-YTD-Sys (1)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 43      pic x(15)       source Emp-ED-Desc (1)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 59      pic zzz,zz9.99  source Coh-QTD-Emp (1)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 72      pic zzz,zz9.99  source Coh-YTD-Emp (1)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (1).
         05  col 102     pic zzz,zz9.99  source Coh-QTD-Units (1).
         05  col 115     pic zzz,zz9.99  source Coh-YTD-Units (1).
     03  line + 1. *> 18
         05  col  1      pic x(15)       source Ded-Sys-Desc (2) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source Coh-QTD-Sys (2)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source Coh-YTD-Sys (2)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 43      pic x(15)       source Emp-ED-Desc (2)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 59      pic zzz,zz9.99  source Coh-QTD-Emp (2)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 72      pic zzz,zz9.99  source Coh-YTD-Emp (2)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (2).
         05  col 102     pic zzz,zz9.99  source Coh-QTD-Units (2).
         05  col 115     pic zzz,zz9.99  source Coh-YTD-Units (2).
     03  line + 1. *> 19
         05  col  1      pic x(15)       source Ded-Sys-Desc (3) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source Coh-QTD-Sys (3)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source Coh-YTD-Sys (3)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 43      pic x(15)       source Emp-ED-Desc (3)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 59      pic zzz,zz9.99  source Coh-QTD-Emp (3)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 72      pic zzz,zz9.99  source Coh-YTD-Emp (3)  present when PY-PR1-Max-Emp-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (3).
         05  col 102     pic zzz,zz9.99  source Coh-QTD-Units (3).
         05  col 115     pic zzz,zz9.99  source Coh-YTD-Units (3).
     03  line + 1.
         05  col  1      pic x(15)       source Ded-Sys-Desc (4)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source Coh-QTD-Sys (4)   present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source Coh-YTD-Sys (4)   present when PY-PR1-Max-SYS-Eds > 0.
         05  col 86      pic x(15)       source PY-PR1-Rate-Name (4).
         05  col 102     pic zzz,zz9.99  source Coh-QTD-Units (4).
         05  col 115     pic zzz,zz9.99  source Coh-YTD-Units (4).
     03  line + 1. *> 21
         05  col  1      pic x(15)       source Ded-Sys-Desc (5) present when PY-PR1-Max-SYS-Eds > 0.
         05  col 16      pic zzz,zz9.99  source Coh-QTD-Sys (5)  present when PY-PR1-Max-SYS-Eds > 0.
         05  col 29      pic zzz,zz9.99  source Coh-YTD-Sys (5)  present when PY-PR1-Max-SYS-Eds > 0.
*>
     03  line + 2. *> 23
         05  col 18          value "QUARTER-MONTH FWT AND FICA LIABILITY".
         05  col 73          value "TAX LIABILITIES BY QUARTER".
     03  line + 1.
         05  col 17          value "QTR-MONTH   DATE ENDED     AMOUNT".
         05  col 73          value "QTR         FWT         FICA          FUTA".
     03  line + 1. *> 25
         05  col 1  value " ".  *> blank line
*>
 01  Company-Detail-Lines-Block-2 type is detail.  *> in a perform varying A from 1 by 1 4 times
     03  line + 1.  *> 26 - 29
         05  col 21      pic z9          source A .  *>   %i
         05  col 29      pic 9(4)/99/99  source Coh-Date (A). *> i%     ccyymmdd so really need to convert
         05  col 40      pic zzz,zz9.99  source Coh-Tax (A).
         05  col 65      pic z9          source A.   *>   %i
         05  col 70      pic zzz,zz9.99  source Coh-Q-Tax (A).  *> occurs 4 times and ditto next 2
         05  col 83      pic zzz,zz9.99  source Coh-Q-Fica-Tax (A).
         05  col 97      pic zzz,zz9.99  source Coh-Q-Co-Futa-Liab (A).
*>
 01  Company-Detail-Lines-Block-3 type is detail.  *> in a perform varying A from 5 by 1 8 times
     03  line + 1.  *> 29 -36
         05  col 21      pic z9          source A .  *>   %i
         05  col 29      pic 9(4)/99/99  source Coh-Date (A). *> i%     ccyymmdd so really need to convert
         05  col 40      pic zzz,zz9.99  source Coh-Tax (A).
*>

*>
*>  Reminder of how, etc also see st010rw-3.02.cbl in RW  or from IRS (RW folders)
 *>    03  WIP-Data    line plus 1
 *>           present when Stock-Services-Flag not = "Y"
 *>                    and (Stock-Construct-Bundle not = zero
 *>                     or Stock-Under-Construction not = zero
 *>                     or Stock-Work-in-Progress not = zero
 *>                     or Stock-Construct-Item not = spaces).
 *>        05  rd-Wip-Data col   1     pic x(132)  value spaces.
*>


 *> 01  type control Footing Final line plus 2.
 *>    03  col 1           pic x(25)    value "Total - Account Records :".
 *>    03  col 25          pic z9       source WS-Rec-Cnt.
*>
 *> 01  type control Footing Final line plus 2.
 *>    03  col 1           pic x(21)    value "*** End of Report ***".
*>
 procedure division using WS-Calling-Data  *> ACAS
                          WS-System-Record *> ACAS
                          To-Day           *> ACAS
                          File-Defs.       *> ACAS
*>
 aa000-Main                  section.
*>**********************************
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
     move     current-Date to WSE-Date-block.
     move     WSE-HH  to  WSD-HH.
     move     WSE-MM  to  WSD-MM.
     move     WSE-SS  to  WSD-SS.
     move     Print-Spool-Name to PSN.  *> set prt spool for o/p
*>
*> Error return codes :-
*>   WS-Term-Code :
*>    0 = No Errors
*>    1 = Missing files
*>    8 = Error with Lines < 28 or Column < 80
*>
*>   Return-Code :
*>    0 = No Errors.
*>    1 = No Payroll param file
*>    2 = No Company history file or record exists
*>    3 = No Deduction file or record exists
*>    4 = No Emp History file
*>    5 = No Employee file
*>    6 = No Param data record exists
*>
     perform  forever
              accept   WS-Env-Lines   from lines
              if       WS-Env-Lines < 28
                       display  SY010    at 0101 with erase eos
                       accept   WS-Reply at 0133
                       move     8 to WS-Term-Code
                       exit perform cycle
              end-if
              accept   WS-Env-Columns from Columns
              if       WS-Env-Columns < 80
                       display  SY013    at 0101 with erase eos
                       accept   WS-Reply at 0130
                       move     8 to WS-Term-Code
                       exit perform cycle
              end-if
     end-perform.
*>
*> Set up error message areas on screen - assumes terninal set for => 28 deep
*>  and must be 80 wide   BUT only needs depth of 24 or more.
*>
     subtract 2 from WS-Env-Lines giving WS-22-Lines.
     subtract 1 from WS-Env-Lines giving WS-23-Lines.
     move     WS-Env-Lines to WS-Lines.
     move     zero to WS-Term-Code.
*>
 aa010-Open-PY-Files.
*>
*> Check for files and Quit if any are missing or there is no data for Emp or History etc.
     open     input PY-Param1-File.
     if       PY-PR1-Status not = "00"      *> Does not exist yet so lets create it & write rec
              perform  ZZ040-Evaluate-Message
              display  PY001         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-PR1-Status at line WS-23-Lines col 47
              display  WS-Eval-Msg   at line WS-23-Lines col 50
              display  SY001         at line WS-Lines    col 1 foreground-color 2
              accept   Menu-Reply    at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 1   *> == no param file
     end-if.
*>
     move     1        to RRN.
     read     PY-Param1-File key RRN
     if       PY-PR1-Status not = "00"
              perform  ZZ040-Evaluate-Message
              display  PY002         at line WS-23-Lines col 1 with erase eos
              display  PY-PR1-Status at line WS-23-Lines col 33
              display  WS-Eval-Msg   at line WS-23-Lines col 36
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 AUTO
              close    PY-Param1-File
              move     1 to WS-Term-Code
              goback   returning 6
     end-if.
*>
     close    PY-Param1-File.   *> Record still in WS area
     move     zero  to  Return-Code.
*>
     open     input PY-Comp-Hist-File.   *> PY Company History - Coh
     if       PY-COH-Status not = zero
              move     PY-Coh-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY809         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-PR1-Status at line WS-23-Lines col 40
              display  WS-Eval-Msg   at line WS-23-Lines col 43
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Comp-Hist-File
              move     1 to WS-Term-Code
              goback   returning 2
     end-if.
     move     1 to RRN
     read     PY-Comp-Hist-File
     if       PY-COH-Status not = zero
              move     PY-Coh-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY804         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-PR1-Status at line WS-23-Lines col 48
              display  WS-Eval-Msg   at line WS-23-Lines col 51
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-Comp-Hist-File
              move     1 to WS-Term-Code
              goback   returning 2
     end-if.
     close    PY-Comp-Hist-File.  *> Only want the one record
*>
     open     input    PY-System-Deduction-File.  *> PY System Deductions
     if       PY-Ded-Status not = zero
              move     PY-Ded-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY808         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-PR1-Status at line WS-23-Lines col 34
              display  WS-Eval-Msg   at line WS-23-Lines col 37
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-System-Deduction-File
              move     1 to WS-Term-Code
              goback   returning 3
     end-if.
     move     1 to RRN.
     read     PY-System-Deduction-File.
     if       PY-Ded-Status not = zero
              move     PY-Ded-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY808         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-PR1-Status at line WS-23-Lines col 34
              display  WS-Eval-Msg   at line WS-23-Lines col 37
              display  SY001         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 48 auto
              close    PY-System-Deduction-File
              move     1 to WS-Term-Code
              goback   returning 3
     end-if.
     close    PY-System-Deduction-File.  *> Only want the one record
*>
     open     input    PY-History-File.   *> Emp History records
     if       PY-His-Emp-Status not = zero
              close    PY-Comp-Hist-File
              move     1 to WS-Term-Code
              goback   returning 4.     *> Abort as no emp data
*>
     open     input    PY-Employee-File.
     if       PY-Emp-Status not = zero
              move     PY-Emp-Status to PY-PR1-Status
              perform  ZZ040-Evaluate-Message
              display  PY806         at line WS-23-Lines col 1 foreground-color 4 erase eos
              display  PY-Emp-Status at line WS-23-Lines col 33 foreground-color 4
              display  WS-Eval-Msg   at line WS-23-Lines col 37
              display  SY003         at line WS-Lines    col 1
              accept   WS-Reply      at line WS-Lines    col 53 auto
              close    PY-Employee-File
              move     1 to WS-Term-Code
              goback   returning 5.
*>
     move     zeros to WS-Page-Cnt.
     move     90    to WS-Line-Cnt.
     perform  aa050-Report.
     close    PY-Employee-File.
     close    PY-History-File.
     goback.
*>
 aa000-Exit.  Exit section.
*>
 aa050-Report                section.
*>**********************************
*>
*> At this point Emp and Emp Hist files are opened for input.
*>  treat Emp recs as primary & his as secondary having init record
*>  pre reading and if emp not present produce zero for all fields etc.
*>
     open     output Print-File.
*>
     move     zero to WS-Rec-Cnt.
     subtract 1 from Page-Lines giving WS-Page-Lines.
     move     To-Day to U-Date.
*>
     initiate Employee-History-Report.
     perform  aa060-Produce-Employee-Report.
     terminate
              Employee-History-Report.
*>
     initiate Company-History-Report.
     perform  aa070-Produce-Company-Report.
     terminate
              Company-History-Report.
*>
     close    Print-File.
     close    PY-Employee-File
              PY-History-File.
*>
     call     "SYSTEM" using Print-Report.  *> Landscape
*>
 aa050-Exit.   exit section.
*>
 aa060-Produce-Employee-Report   section.
*>**************************************
*>
     move     zero to WS-Rec-Cnt.
     move     4     to WS-Max.
     if       PY-PR1-Max-Sys-Eds > WS-Max
              move     PY-PR1-Max-Sys-Eds to WS-Max. *> These are more a PY system default.
*>
     perform  forever
              read     PY-Employee-File next record
              if       PY-Emp-Status not = "00"   *> EOF
                       exit perform
              end-if
              add      1 to WS-Rec-Cnt
              move     Emp-No to His-Emp-No
              read     PY-History-File key His-Emp-No
              if       PY-His-Emp-Status not = zero   *> all 9's indicate rec missing - may be
                       initialise PY-History-Record
                         replacing numeric by 9
              end-if
              move     spaces to WS-Emp-Stat
              evaluate Emp-Status
                  when "A"
                       move "(Active)"     to WS-Emp-Stat
                  when "D"
                       move "(Deleted)"    to WS-Emp-Stat
                  when "L"
                       move "(On leave)"   to WS-Emp-Stat
                  when "T"
                       move "(Terminated)" to WS-Emp-Stat
                  when other
                       move "(UNKNOWN)"    to WS-Emp-Stat
              end-evaluate
*>
              generate Employee-Detail
*>
              exit perform cycle
     end-perform.
*>
 aa060-Exit.  exit section.
*>
 aa070-Produce-Company-Report section.
*>***********************************
*>
*> The RD section is more likely wrong <<<<<<<<<<<<<<<
*>
     move     zero to A.
     generate Company-Detail-Lines-Block-1.
     perform  4 times
              add      1 to A
              generate Company-Detail-Lines-Block-2
     end-perform.
     perform  8 times
              add      1 to A
              generate Company-Detail-Lines-Block-3
     end-perform.
*>
 aa070-Exit.  exit section.
*>
 zz020-Display-Heads         section.  *> NOT USED
*>**********************************
*>
     display  space at 0101 with erase eos.
     display  Prog-Name              at 0101 with foreground-color 2.
     display  "ACAS Payroll"         at 0131 with foreground-color 2.
     move     To-Day to WS-Date.
     perform  zz070-Convert-Date.
     display  WS-Date                at 0171 with foreground-color 2.
*>
 zz020-Exit.  exit section.
*>
 ZZ040-Evaluate-Message      Section.
*>**********************************
*>
*> For PY-PR1 parameter file anfd other using PR-PR1-Status.
*>
     copy "FileStat-Msgs-2.cpy" replacing MSG    by WS-Eval-Msg
                                        STATUS by PY-PR1-Status.
*>
 ZZ050-Eval-Msg-Exit.
     exit     section.
*>
 zz050-Validate-Date        section.  *> ALL THESE ARE NOT USED
*>*********************************
*>
*>  Converts USA/Intl to UK date format for processing.
*>*******************************
*> Input:   WS-Test-Date
*> output:  U-Date/WS-Date as uk date format
*>          U-Bin not zero if valid date
*>
     move     WS-Test-Date to WS-Date.
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz050-Test-Date.
     if       Date-USA                *> swap month and days
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              go to zz050-Test-Date.
*>
*> So its International date format
*>
     move     "dd/mm/ccyy" to WS-Date.  *> swap Intl to UK form
     move     WS-Test-Date (1:4) to WS-Year.
     move     WS-Test-Date (6:2) to WS-Month.
     move     WS-Test-Date (9:2) to WS-Days.
*>
 zz050-Test-Date.
     move     WS-Date to U-Date.
     move     zero to U-Bin.
     call     "maps04"  using  Maps03-WS.
*>
 zz050-exit.
     exit     section.
*>
 zz060-Convert-Date        section.
*>********************************
*>
*>  Converts date in binary to UK/USA/Intl date format
*>****************************************************
*> Input:   U-Bin
*> output:  WS-Date as uk/US/Inlt date format
*>          U-Date & WS-Date = spaces if invalid date
*>
     call     "maps04"  using  Maps03-WS.
     if       U-Date = spaces
              move spaces to WS-Date
              go to zz060-Exit.
     move     U-Date to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz060-Exit.
     if       Date-USA                *> swap month and days
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              go to zz060-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> swap Intl to UK form
     move     U-Date (7:4) to WS-Intl-Year.
     move     U-Date (4:2) to WS-Intl-Month.
     move     U-Date (1:2) to WS-Intl-Days.
*>
 zz060-Exit.
     exit     section.
*>
 zz070-Convert-Date          section.
*>**********************************
*>
*>  Converts date in To-Day to UK/USA/Intl date format using ACAS param
*>*********************************************************************
*> Input:   To-Day
*> output:  WS-Date as uk/US/Inlt date format
*>
     move     To-Day to WS-Date.
*>
     if       Date-Form = zero
              move 1 to Date-Form.
     if       Date-UK
              go to zz070-Exit.
     if       Date-USA                *> Swap month and days
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              go to zz070-Exit.
*>
*> So its International date format
*>
     move     "ccyy/mm/dd" to WS-Date.  *> Swap Intl to UK form
     move     To-Day (7:4) to WS-Intl-Year.
     move     To-Day (4:2) to WS-Intl-Month.
     move     To-Day (1:2) to WS-Intl-Days.
*>
 zz070-Exit.
     exit     section.
*>
*> For report but zz070 does mostly the same
*>
 zz080-Convert-Date  section.
*>**************************
*>
*> Convert from UK to selected form
*>
     move     To-Day to U-Date.
     if       Date-USA
              move U-Date   to WS-Date
              move WS-Days  to WS-Swap
              move WS-Month to WS-Days
              move WS-Swap  to WS-Month
              move WS-Date  to U-Date
     end-if.
     if       Date-Intl
              move "ccyy/mm/dd" to WS-date   *> swap Intl to UK form
              move U-Date (7:4) to WS-Intl-Year
              move U-Date (4:2) to WS-Intl-Month
              move U-Date (1:2) to WS-Intl-Days
              move WS-Date to U-Date
     end-if.
*>
 zz080-exit.
     exit     section.
*>
