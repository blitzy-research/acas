       >>source free
*>*****************************************************************
*>                                                                *
*>      N O M I N A L   L E D G E R   F I L E   S O R T           *
*>                                                                *
*>*****************************************************************
 identification division.
 program-id.            irs065.
*>
*> Author.              V.B. COEN
*>                      Cobol conversion by V B COEN. FIDPM FBCS 23.10.82
*>                      for APPLEWOOD COMPUTERS.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>
*>**
*> Remarks.             Nominal ledger file sort to (Cobol) work file
*>                      prior to running irs060.
*>                      This step needed for both Files and tables.
*>**
*> Version.             See prog-name in ws.
*>**
*> Calls.
*>                      acasirsub1  ->
*>                       irsnominalMT
*>**
*> Error messages used.
*>  System Wide
*>                      SM901 }
*>                      SM903 } Produced by DAL.
*>                      SM904 }
*>                      SY008.
*>                      IR901 }
*>                      IR902 } From FH.
*>                      IR911 }
*>                      IR912 } Only one possible.
*>                      IR913 }
*>                      IR914 }
*>                      IR915 }
*>                      IR916 }
*>  Module Specific.
*>                      None.
*>**
*> Changes.
*> 22/01/09 vbc - Migration to Open/Gnu Cobol as version 3.
*> 26/09/89 vbc - 2.53
*> 07/12/16 vbc - 3.02  For all RDB modules.
*>                .01 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*>                    Replace direct access (open,read,write,close) for NL
*>                    for FH & DAL. Must have been written before using FH
*>                    Replace Nominal-ledger open,close,read,write processing
*>                    to FH calls.
*>                    The temp. Work file is ALWAYS a Cobol file.
*> 20/12/16 vbc -     All irs progs call cpybk Proc-ZZ100-ACAS-IRS-Calls.
*> 29/01/18 vbc - .03 Removed unused error messages from WS.
*>                    Changed copies to use copybooks where poss. I.e.,
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 10/02/18 vbc - .04 Renamed messages IR011-16 to IR911-16
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
 environment division.
 copy  "envdiv.cob".
 input-output section.
 file-control.
*>
     select  output-file     assign  "worksort.tmp"
                             organization sequential.
     select  sort-file       assign  "work.tmp".
*>
 data division.
 file section.
*>
 fd  output-file.
*>
 01  output-record.
     03  output-key          pic 9(10).
     03  output-type         pic a.
     03  output-data.
         05  output-name     pic x(24).
         05  output-dr       pic 9(8)v99  comp.
         05  output-cr       pic 9(8)v99  comp.
         05  output-dr-last  pic 9(8)v99  comp  occurs 4.
         05  output-cr-last  pic 9(8)v99  comp  occurs 4.
         05  output-ac       pic a.
    03  filler  redefines output-data.
      05 output-pointer      pic 9(5).
*>
 sd  sort-file.
*>
 01  sort-record.
     03  sort-key            pic 9(10).
     03  sort-type           pic a.
     03  sort-data.
         05  sort-name       pic x(24).
         05  sort-amounts    pic 9(8)v99  comp  occurs 10.
         05  sort-ac         pic x.
*>
 working-storage section.
*>-----------------------
 77  prog-name           pic x(16) value "irs065 (3.3.00)".
 77  nl-file             pic x(11).
*>
 copy  "wsfnctn.cob".
*>
 copy "irswsnl.cob" replacing        nl-record by WS-IRSNL-Record.
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
 *>    03  WS-IRSNL-Record       pic x.  *> This one is  used.
     03  WS-IRS-Default-Record pic x.  *> As these are used for unused F.H. calls.
     03  Posting-Record        pic x.  *>   as dummies.
     03  Final-Record          pic x.
     03  WS-IRS-Posting-Record pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide      USED are : 08
     03  SY008          pic x(32) value "SY008 Note message & Hit return ".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, Fs-reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, Fs-reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, Fs-reply = ".
     03  IR914          pic x(51) value "IR914 Error on irspostingMT processing, Fs-reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, Fs-reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, Fs-reply = ".
*> Module specific  USED None.
*>
 linkage section.
*>---------------
*>
 copy "irswssystem.cob"   *> IRS param record
              replacing system-record  by IRS-System-Params. *> (01 level)
*>
 copy "wssystem.cob"    *> NEW for v3.02
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
 copy "wsnames.cob".
*>
 procedure division using IRS-System-Params *> IRS param
                          WS-System-Record  *> ACAS param
                          File-Defs.
*>=========================================
*>
 init01 section.
*>**************
*>
     sort     sort-file on  ascending  key  sort-ac
              input procedure is  input-to-sort
              giving output-file.
*>
 main-exit.   exit program.
*>
 input-to-sort section.
*>*********************
     perform  acasirsub1-Open-Input.          *> was open input NL
     if       fs-reply not = zero
              display IR912     at 2201
              display FS-Reply  at 2252
              display SY008     at 2401
              accept Accept-Reply at 2235
              open output output-file
              close output-file
              perform  acasirsub1-Close
              goback.
*>
 process-input-record.
*>
     perform  acasirsub1-Read-Next.
     if       fs-reply = 10
              go to  end-of-input.
*>
     if       Sub                          *> Only want owners
              go to process-input-record.
*>
     release  sort-record  from  WS-IRSNL-Record.
     go to    process-input-record.
*>
 end-of-input.
     perform  acasirsub1-Close.
*>
 Main-Exit.
     exit     section.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
