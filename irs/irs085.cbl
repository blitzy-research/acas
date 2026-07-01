       >>source free
*>*****************************************************************
*>                                                                *
*>   Posting  File  Sort  By  Acct.No / Year / Month              *
*>                                                                *
*>*****************************************************************
 identification division.
 program-id.            irs085.
*>
*> Author.              V B COEN, FIDPM FBCS for Applewood Computers.
*>**
*> Security.            Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>
*>**
*> Remarks.             Posting File Code Sort.
*>**
*> Version.             See prog-name in ws.
*>**
*> Calls.
*>                      acasirsub3 ->
*>                       irsdfltMT
*>                      acasirsub4 ->
*>                       postingMT
*>**
*> Error messages used.
*>  System Wide
*>                      SY008.
*>                      IR911 }
*>                      IR912 }
*>                      IR913 }  FH
*>                      IR914 }
*>                      IR915 }
*>                      IR916 }
*>  Module Specific.   NONE.
*>**
*> Changes.
*>
*> 26/09/89 vbc - 2.53
*>                Mods for cobol/2.
*> 23/01/09 vbc - Migration to Open/Gnu Cobol as version 3.
*> 01/03/09 vbc - Get rid of displays with modern cpu speeds not needed.
*> 14/03/10 vbc - Cleanup multi field displays to comply with standards.
*> 03/12/16 vbc - 3.02
*> 03/12/16 vbc - .04 RDB support via acasirsub(1-5) & DALs and using
*>                    standard ACAS param file (system.dat) for info pickup
*>                    passed to IRS-System-Params (renamed from system-record).
*>                    Replaced all occurances of call "irsubn" by
*>                     perform acasirsubn
*>                    File-Defs  added to all irsnnn calls as 2nd param.
*>                    Clean up all msgs to use Pre-Defined ones system/module
*>                    wide across entire IRS system in compliance with all of
*>                    ACAS.
*> 20/12/16 vbc -     All irs progs call cpybk Proc-ZZ100-ACAS-IRS-Calls.
*> 29/01/18 vbc - .05 Changed error message to SYS008 and IR914
*>                    for missing posting data table / file.
*>                    Changed copies to use copybooks where poss. I.e.,
*>                    renamed print-spool-commandxxx & wsnl to irsprint-spool-command
*>                    & irswsnl as moved to copybooks dir.
*> 10/02/18 vbc - .06 Renamed IR011-16 to IR911-16 and others.
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
*>
 input-output section.
 file-control.
*>
 *>    select  posting-file    assign  post-file
 *>                            organization  indexed
 *>                            access  dynamic
 *>                            record  post-key
 *>                            status  fs-reply.
     select  output-file     assign  "workpost.tmp"
                             organization  sequential.
     select  sort-file       assign  "work.tmp".
*>
 data division.
 file section.
 *>
 *> fd  posting-file.
*>
 fd  output-file.
*>
 01  output-record.
     03  output-date     pic 99.
     03  output-account  pic 9(5)      comp.
     03  output-amount   pic s9(7)v99  comp.
*>
 sd  sort-file.
*>
 01  sort-record.
     03  sort-month      pic 99.
     03  sort-account    pic 9(5)        comp.
     03  sort-amount     pic s9(7)v99    comp.
*>
 working-storage section.
*>-----------------------
 77  prog-name           pic x(16) value "irs085 (3.3.00)".
 77  post-file           pic x(11).
 77  ws-reply            pic x     value space.
*>
 copy "wsfnctn.cob".
 copy "irswsdflt.cob"     replacing Default-Record by WS-IRS-Default-Record.
*>
 copy "irswspost.cob".
*>
 01  filler redefines Posting-Record.
     03  filler          pic 9(5).
     03  filler          pic xx.
     03  filler.
         05  filler      pic xxx.
         05  post-mm     pic 99.
         05  filler      pic xxx.
*>
 01  Dummies-For-Unused-FH-Calls.      *> IRS call blk at zz100-ACAS-IRS-Calls
     03  WS-IRSNL-Record       pic x.
 *>    03  WS-IRS-Default-Record pic x.
 *>    03  Posting-Record        pic x.
     03  Final-Record          pic x.
     03  WS-IRS-Posting-Record pic x.
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 01  Error-Messages.
*> System Wide
     03  SY008          pic x(32) value "SY008 Note message & Hit return ".
     03  IR911          pic x(47) value "IR911 Error on systemMT processing, Fs-reply = ".
     03  IR912          pic x(51) value "IR912 Error on irsnominalMT processing, Fs-reply = ".
     03  IR913          pic x(48) value "IR913 Error on irsdfltMT processing, Fs-reply = ".
     03  IR914          pic x(51) value "IR914 Error on irspostingMT processing, Fs-reply = ".
     03  IR915          pic x(49) value "IR915 Error on irsfinalMT processing, Fs-reply = ".
     03  IR916          pic x(50) value "IR916 Error on slpostingMT processing, Fs-reply = ".
*> Module specific.   None.
*>
 linkage section.
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
 procedure division using IRS-System-Params
                          WS-System-Record
                          File-Defs.
*>=========================================
*>
 init01 section.
*>**************
     move     3 to file-function.
     perform  acasirsub3.
     sort     sort-file on ascending key sort-account sort-month
                  input procedure is input-to-sort
                              giving output-file.
*>
 main-exit.   exit program.
*>********    ************
*>
 input-to-sort section.
*>---------------------
     perform  acasirsub4-Open-Input.
     if       fs-reply not zero
              display IR914    at 2301 with foreground-color 4 erase eol
              display fs-reply at 2352 with foreground-color 4
              display SY008    at 2401 with foreground-color 4 erase eol
              accept ws-reply  at 2434
              go to end-of-input.
*>
 process-input-record.
*>
     perform  acasirsub4-Read-Next.
     if       fs-reply = 10
              go to end-of-input.
*>
     move     post-mm to sort-month.
     move     post-amount to sort-amount.
*>
     move     post-cr to sort-account.
     release  sort-record.
*>
     multiply -1 by sort-amount.
     move     post-dr to sort-account.
     release  sort-record.
*>
     if       vat-ac-def = zero
              go to process-input-record.
     move     vat-amount to sort-amount.
     move     def-acs (vat-ac-def) to sort-account.
     release  sort-record.
*>
     go to    process-input-record.
*>
 end-of-input.
*>
     perform  acasirsub4-Close.
*>
 copy "Proc-ZZ100-ACAS-IRS-Calls.cob".
*>
