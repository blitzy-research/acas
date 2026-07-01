*>
 zz100-ACAS-IRS-Calls  section.
*>============================
*>
*>  USED THROUGHTOUT IRS but Map out by using a dummy 03 all
*>   unused acasirsubn routines [see 01  Dummies-For-Unused-FH-Calls].
*>
*> All of the calls to irsub1 - 5 remapped to acasirsub1 - 5.
*>        All require changes to code for param etc.
*>
*>  Uses messages:  IR911, IR912, IR913, IR915, IR916. (Was IR011 - 16.
*>
*>  Note irsub2 is replaced by acas000 with File-Key-No=1
*> ******************************************************
*>
*> acas000     =  System parameter file processing with File-Key-No=1
*>
*> Changes:
*> 29/04/18 vbc - 1.01 - Changed all accessing other than open with 1st line of
*>                       move zero to Access-Type to keep logging clean.
*>
 acas000.
*>
     move     1 to File-Key-No.               *> 1 = Primary as only used.
     call     "acas000" using
                                WS-System-Record
                                File-Access
                                File-Defs
                                ACAS-DAL-Common-data
     end-call.
*>
*> acas008     =  SL/PL Posting file processing
*>
 acas008.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acas008" using WS-System-Record
                              WS-IRS-Posting-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
*> acasirsub1  =  NL (Nominal Ledger) processing.
*>
 acasirsub1.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub1" using WS-System-Record
                                 WS-IRSNL-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*> acasirsub3  =  Dflit (Default) processing.
*>
 acasirsub3.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub3" using WS-System-Record
                                 WS-IRS-Default-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*> acasirsub4  =  Posting processing.
*>
 acasirsub4.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub4" using WS-System-Record
                                 Posting-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*> acasirsub5  =  Final processing.
*>
 acasirsub5.
*>
     move     1 to File-Key-No.               *> 1 = Primary
     call     "acasirsub5" using WS-System-Record
                                 Final-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
     end-call.
*>
*>
 acas000-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas000.
     perform  acas000-Check-4-Errors.
*>
 acas000-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas000-Check-4-Errors.
     perform  acas000.
*>
 acas000-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas000.
*>
 acas000-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas000.
*>
 acas000-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas000.
*>
 acas000-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas000.
*>
 acas000-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acas000.
*>
*>
 acas008-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas008.
     perform  acas008-Check-4-Errors.
*>
 acas008-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas008.
     perform  acas008-Check-4-Errors.
*>
 acas008-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas008.
     perform  acas008-Check-4-Errors.
*>
 acas008-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas008.
*>
 acas008-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas008.
*>
 acas008-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas008.
*>
 acas008-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acas008.
*>
*>
 acasirsub1-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub1.
     perform  irsub1-Check-4-Errors.
*>
 acasirsub1-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub1.
     perform  irsub1-Check-4-Errors.
*>
 acasirsub1-Open-Output.
     set      fn-open  to true.
     set      fn-output to true.
     perform  acasirsub1.
     perform  irsub1-Check-4-Errors.
*>
 acasirsub1-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub1.
*>
 acasirsub1-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub1.
*>
 acasirsub1-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acasirsub1.
*>
 acasirsub1-Start.
     move     zero to Access-Type.
     set      fn-Start to true.
     perform  acasirsub1.
*>
 acasirsub1-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub1.
*>
 acasirsub1-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     perform  acasirsub1.
*>
 acasirsub1-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub1.
*>
*>
 acasirsub3-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub3.
     perform  irsub3-Check-4-Errors.
*>
 acasirsub3-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub3.
     perform  irsub3-Check-4-Errors.
*>
 acasirsub3-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub3.
*>
 acasirsub3-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub3.
*>
 acasirsub3-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub3.
*>
 acasirsub3-ReWrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub3.
*>
*>
 acasirsub4-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub4.
*>
 acasirsub4-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub4.
*>
 acasirsub4-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub4.
*>
 acasirsub4-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub4.
*>
 acasirsub4-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub4.
*>
 acasirsub4-Rewrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub4.
*>
*>
 acasirsub5-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acasirsub5.
     perform  irsub5-Check-4-Errors.
*>
 acasirsub5-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acasirsub5.
     perform  irsub5-Check-4-Errors.
*>
 acasirsub5-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acasirsub5.
*>
 acasirsub5-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acasirsub5.
*>
 acasirsub5-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acasirsub5.
*>
 acasirsub5-ReWrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acasirsub5.
*>
*>
 acas000-Check-4-Errors.
     if       fs-reply not = zero
              display IR911            at 0801   *> acas000/systemMT processing
              perform acas000-Close
              go to Open-Error-Continued
     end-if.
*>
 acas008-Check-4-Errors.
     if       fs-reply not = zero
              display IR916            at 0801   *> acas008/slpostingMT processing
              perform acas008-Close
              go to Open-Error-Continued
     end-if.
*>
 irsub1-Check-4-Errors.
     if       fs-reply not = zero
              display IR912            at 0801   *> acasirsub1/irsnominalMT processing
              perform  acasirsub1-Close
              go to Open-Error-Continued
     end-if.
*>
 irsub3-Check-4-Errors.
     if       fs-reply not = zero
              display IR913            at 0801   *> acasirsub3/irsdfltMT processing
              perform  acasirsub3-Close
              go to Open-Error-Continued
     end-if.
*>
 irsub5-Check-4-Errors.
     if       fs-reply not = zero
              display IR915            at 0801   *> acasirsub5/irsfinalMT processing
              perform  acasirsub5-Close
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
 ZZ100-Exit.
     exit section.
