       >>source free
*>*****************************************************************
*>         Posting File  Sort By Code / Date / Transaction        *
*>*****************************************************************
 identification division.
 program-id.            irs055.
*> Author.              Cobol conversion by Vincent B Coen, AIDPM FBCS 23.10.82
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*> Remarks.             Posting File Code Sort.
*>                      Produces a temporary Cobol work file that
*>                      is used in irs050 & irs070.
*>**
*> Version.             See prog-name in ws.
*>**
*> Calls.               acasirsub4 ->
*>                       postingMT
*>**
*> Error messages used.
*>  System Wide
*>                      SY008.
*>                      IR911 }
*>                      IR912 }
*>                      IR913 }
*>                      IR914 }
*>                      IR915 }
*>                      IR916 }
*>  Module Specific.
*>                      IR061 Sort Failed =
*>**
*> Changes.
*> 22/01/09 vbc - Migration to Open/Gnu Cobol as version 3.
*> 26/09/89 vbc - 2.53
*> 03/12/16 vbc - 3.02
*> 01/12/16 vbc - .01 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*> 20/12/16 vbc -     All irs progs call cpybk Proc-ZZ100-ACAS-IRS-Calls.
*> 29/01/18 vbc - .02 Changed copies to use copybooks where poss. I.e.,
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 10/02/18 vbc - .03 Renamed IR011-16 to IR911-16
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
     select  output-file     assign  File-38     *> "postsort.dat"  *> sort O/P
                             organization line sequential.
     select  sort-file       assign  "work.tmp"
                             status fs-reply.
*>
 data division.
 file section.
*>
 fd  output-file.
*>
 01  output-record.
     03  output-key        pic 9(5).
     03  output-code       pic xx.
     03  output-date       pic x(8).
     03  output-dr         pic 9(5).
     03  output-cr         pic 9(5).
     03  output-amount     pic s9(7)v99  sign is leading.
     03  output-legend     pic x(32).
     03  out-vat-ac-def    pic 99.
     03  output-vat-side   pic xx.
     03  out-vat-amount    pic s9(7)v99  sign is leading.
*>
 sd  sort-file.
*>
 01  sort-record.
     03  sort-key        pic 9(5).
     03  sort-code       pic xx.
     03  sort-date.
         05  sort-days   pic xx.
         05  filler      pic x.
         05  sort-month  pic xx.
         05  filler      pic x.
         05  sort-year   pic xx.
     03  sort-dr         pic 9(5).
     03  sort-cr         pic 9(5).
     03  sort-amount     pic s9(7)v99  sign is leading.
     03  sort-legend     pic x(32).
     03  sort-vat-ac-def pic 99.
     03  sort-vat-side   pic xx.
     03  sort-vat-amount pic s9(7)v99  sign is leading.
*>
 working-storage section.
*>-----------------------
 77  prog-name           pic x(16) value "irs055 (3.3.00)".
 77  post-file           pic x(11).
*>
 copy "wsfnctn.cob".
 copy "irswspost.cob".
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
     03  WS-IRSNL-Record       pic x.   *> acasirsub1 not in use.
     03  WS-IRS-Default-Record pic x.     *> acasirsub3 not in use.
 *>    03  Posting-Record        pic x.     *> acasirsub4 in use.
     03  WS-IRS-Posting-Record pic x.     *> acas008    not in use.
     03  Final-Record          pic x.     *> Table/File  not used in this program.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide      USED are :
     03  SY008          pic x(32) value "SY008 Note message & Hit return ".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, Fs-reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, Fs-reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, Fs-reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, Fs-reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, Fs-reply = ".
*> Module specific  USED are : 14
     03  IR061          pic x(20) value "IR061 Sort Failed = ".
*>
 linkage section.
*>---------------
*>
 copy "irswssystem.cob"  *> IRS param record
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
 procedure division using IRS-System-Params
                          WS-System-Record
                          File-Defs.
*>=========================================
*>
 init01 section.
*>*************
*>
*>  For RDB would like to do a SELECT, ORDER BY but date field/column
*>    is not broken down as DD, DD, YY so cannot do it.
*>
     if       Save-Sequ  equal  1
              sort sort-file
                 on ascending key sort-code
                                  sort-year
                                  sort-month
                                  sort-days
                                  sort-key
              input procedure is  input-to-sort
              giving output-file.
*>
     if       Save-Sequ  equal  2
              sort sort-file
                 on ascending key sort-year
                                  sort-month
                                  sort-days
                                  sort-code
                                  sort-key
              input procedure is input-to-sort
              giving output-file.
*>
     if       Save-Sequ  equal  3
              sort  sort-file on ascending key sort-key
              input procedure is  input-to-sort
              giving output-file.
*>
     if       fs-reply not = zero
              display IR061    at 2301    *> Sort Failed
              display fs-reply at 2321
              display SY008    at 2410
              accept fs-reply  at 2445.
*>
 main-exit.
     exit     program.
*>
 input-to-sort section.
*>---------------------
*>
     perform  acasirsub4-Open-Input.     *> open     input  posting-file.
     if       FS-Reply not = zero
              go to End-Of-Input.
*>
 process-input-record.
*>
     perform  acasirsub4-Read-Next.      *> read     posting-file  next at end
     if       FS-Reply = 10
              go to  end-of-input.
*>
     release  sort-record  from  posting-record.
     go       to process-input-record.
*>
 end-of-input.
     perform  acasirsub4-Close.          *> close    posting-file.
*>
 Main-Exit.
     exit     section.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
