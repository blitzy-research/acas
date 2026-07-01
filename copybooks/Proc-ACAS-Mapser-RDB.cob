*> Changes:
*> 25/04/17 vbc - 1.01 Added open input function to acas000-
*> 20/07/17 vbc - 1.02 Set accept default to "Y", adding warning for used
*>                     only once when creating the system parameter file.
*> 07/02/18 vbc - 1.03 Removed encryption for password and user name for O/S.
*> 09/02/18 vbc - 1.04 Updated param defaults on 1st set up BUT MORE MAY
*>                     BE MISSING.
*> 08/12/22 vbc - 1.05 For gc v3.2 added new para at start of ca000-Level-Setup
*>                     as it does not like a goto section name.
*> 23/08/23 vbc - 1.06 Commended out OE and Payroll processing and removed such
*>                     code for testing for them. Added extra comment regarding
*>                     check Company name and set default to Y for all systems.
*> 10/09/23 vbc - 1.07 Added OE as a sub system.
*> 21/04/24 vbc - 1.08 Added with filler to all initialise records.
*> 31/08/25 vbc   1.09 Removed OE - Not used as not needed - functions already
*>                     present.
*>
 ba000-mapser section.
*>*******************
*>
*> Encrypt/Decrypt coding and other security code removed for
*>    Open Source release
*>
     display  prog-name at 0101 with erase eos foreground-color 2.
     display  "ACAS System Setup Routine - Level 1" at 0122 with foreground-color 2.
     display  "If in doubt select ALL options as this process is only run once"
                                   at 0401 with foreground-color COB-COLOR-RED.
*>
*> Now Open System File for Output (overwriting any existing contents)
*>    This is writing to the Cobol param file ONLY.
*>     SO Force it.
*>
     move     "00" to FA-RDBMS-Flat-Statuses.     *> Force file processing in wsfnctn
*>                                                *> Yes also in mapser!
     perform  acas000-Open-Output.
     if       fs-reply not = zero
              display SY010 at 1101 with foreground-color 4
              accept ws-reply at 1154
              stop run
     end-if.
*>
     initialize System-Record with filler.                    *> In WS.
     move     ws-Sys-Record-Ver-Prime      to System-Record-Version-Prime.
     move     ws-Sys-Record-Ver-Secondary  to System-Record-Version-Secondary.
     move     zero to File-System-Used
                      File-Duplicates-In-Use.
     move     1 to date-form.                     *> default UK format
*>
 ba010-Capture-Data.
     display  "Enter the Company name :- [" at 1101 with foreground-color 2.
     display  "]" at 1160 with foreground-color 2.
*>
     accept   usera at 1128 with foreground-color 3 update.
*>
     display  "Please VERIFY that name is correct (Y/N) :- [ ] CHECK IT !" at 1301 with foreground-color 2.
     move     "N"  to  ws-reply.
     accept   ws-reply  at 1346 with foreground-color 6 update.
*>
     if       ws-reply not = "Y" and not = "y"
              go to ba010-Capture-Data
     end-if
 *>    move     "N" to encode.
 *>    move     usera to pass-name.
 *>    call     "maps01" using maps01-ws.
 *>    move     pass-name to user-code.
 *>    move     "P" to encode.
 *>    move     "pass" to pass-word of maps01-ws
 *>                       pass-word of system-record.
 *>    call     "maps01" using maps01-ws.
 *>    move     pass-word of maps01-ws  to  pass-word of system-record.
*>
     move     function current-date to wse-date-block.
     move     "00/00/0000" to u-date.
     move     wse-year  to u-year.
     move     wse-month to u-month.
     move     wse-days  to u-days.
     move     u-date    to to-day.
     move     zero      to u-bin.
     call     "maps04" using maps03-ws.
     move     u-bin  to run-date.
*>
*> Load basic defaults
*>
     move     1  to  Op-System.
     move     1  to  Sales-Range.
     move     2  to  Purchase-Range.
     move     1  to  Next-Batch.
     move     1  to  SL-Dunning
                     SL-Charges.
     move     1  to  Cyclea.
     move     2  to  Invoicer.
     move     20 to  Vat-Rate-1.
     move     5  to  Vat-Rate-2.
     move     30 to  SL-Credit.
     move     25 to  SL-Invoice-Lines.
     move     1  to  Period
                     Next-Invoice
                     Date-Form
                     Next-Folio
                     First-SL-Batch
                     First-SL-Inv
                     Next-Post.
     move     "!" to SL-Delim
                     PL-Delim.
     move     "N" to SL-Own-Nos.
     move     "Y" to SL-Stock-Link
                     SL-Stock-Audit               *> Not currently used in ST,  SL?
                     PL-Stock-Link.
     move     1  to  STK-Audit-Used
                     STK-Mov-Audit
                     STK-Averaging
                     STK-Audit-No.
*>
     perform  ca000-level-setup.                  *> set up what (sub) systems will be used
*>
     move     "00"  to FA-RDBMS-Flat-Statuses.    *> in fnctn (file-access)
     move     1 to File-Key-No.
     move     System-Record   to  WS-Temp-System-Record.
     perform  acas000-Write.
     move     1 to Init-System-File-SW.           *> in sys002
*>
     initialize Default-Record with filler.
     move     Default-Record  to System-Record.
     move     2 to File-Key-No.
     perform  acas000-Write.
     move     1 to Init-Default-File-SW.          *> in sys002
*>
     initialise Final-Record with filler.
     move     Final-Record    to System-Record.
     move     3 to File-Key-No.
     perform  acas000-Write.
     move     1 to Init-Final-File-SW.      *> in sys002
*>
     initialize System-Record-4 with filler.
     move     System-Record-4 to System-Record.
     move     4 to File-Key-No.
     perform  acas000-Write.
     move     1 to Init-Sys4-File-SW.       *> in sys002
     move     WS-Temp-System-Record to System-Record.   *> As system-rec will be processed against.
*>
     perform  acas000-Close.
*>
 ba999-exit.
     exit     section.
*>
 ca000-level-setup  section.
*>*************************
*>
 ca001-Main.
     move     "mp9999" to wsmaps-ser.         *> Open Source versions only.
     move     wsmaps-ser-xx to maps-ser-xx.   *> as others have extra functionality
     move     wsmaps-ser-nn to maps-ser-nn.
*>
     display  "Using General  Ledger (Y/N) ? :- [ ]"  at 1901 with foreground-color 2.
     display  "Using IRS             (Y/N) ? :- [ ]"  at 1941 with foreground-color 2.
     display  "Using Purchase Ledger (Y/N) ? :- [ ]"  at 2001 with foreground-color 2.
     display  "Using Stock Control   (Y/N) ? :- [ ]"  at 2041 with foreground-color 2.
     display  "Using Sales    Ledger (Y/N) ? :- [ ]"  at 2101 with foreground-color 2.
     display  "Using Invoicing  [SL] (Y/N) ? :- [ ]"  at 2141 with foreground-color 2.
 *>     display  "Using OE              (Y/N) ? :- [ ]"  at 2201 with foreground-color 2.
*>     display  "Using Payroll         (Y/N) ? :- [ ]"  at 2241 with foreground-color 2.
*>
     move     "Y" to ws-Reply.
     accept   ws-reply at 1935 with foreground-color 6 update.
     if       ws-reply = "Y" or "y"
              move  1  to  level-1    *> General
     else
              move zero to level-1
     end-if
*>
     move     "Y" to ws-Reply.
     accept   ws-reply at 1975 with foreground-color 6 update.
     if       ws-reply = "Y" or "y"
              move  1  to  Level-5      *> IRS
     else
              move zero to Level-5
     end-if
*>
     move     "Y" to ws-Reply.
     accept   ws-reply at 2035 with foreground-color 6 update.
     if       ws-reply = "Y" or "y"
              move  1  to  level-2    *> Purchase
     else
              move zero to level-2
     end-if
*>
     move     "Y" to ws-Reply.
     accept   ws-reply at 2075 with foreground-color 6 update.
     if       ws-reply = "Y" or "y"
              move  1  to  Level-4    *> Stock Control
     else
              move zero to Level-4
     end-if
*>
     move     "Y" to ws-Reply.
     accept   ws-reply at 2135 with foreground-color 6 update.
     if       ws-reply = "Y" or "y"
              move  1  to  level-3    *> Sales
     else
              move zero to level-3
     end-if
*>
     move     "Y" to ws-Reply.
     accept   ws-reply at 2175 with foreground-color 6 update.
     if       ws-reply = "Y" or "y"
              move  1  to  full-invoicing      *> Invoicing
     else
              move zero to full-invoicing
     end-if
*>
 *>    move     "Y" to ws-Reply.
 *>    accept   ws-reply at 2235 with foreground-color 6 update.
 *>    if       ws-reply = "Y" or "y"
 *>             move  1  to  level-6    *> OE
 *>    else
 *>             move zero to level-6
 *>    end-if
*>
     display  "Please confirm (Y/N) :- [ ] " at 2301 with foreground-color 2.
     move     spaces  to  option-list.
     move     1  to  a.
*>
     if       G-L
              string "General "      delimited by size into option-list pointer a.
*>
     if       B-L  and  G-L
              string "/ "            delimited by size into option-list pointer a.
*>
     if       B-L
              string "Purchase "     delimited by size into option-list pointer a.
*>
     if       (S-L  and  G-L)
        or    (S-L  and  B-L)
              string "/ "            delimited by size into option-list pointer a.
*>
     if       S-L
              string "Sales "        delimited by size into option-list pointer a.
*>
     if       S-L  and  Full-Invoicing = 1
              string  "/ Invoicing " delimited by size into option-list pointer a.
*>
     if       Stock
              string "/ Stock "      delimited by size into option-list pointer a.
*>
     if       IRS
              string "/ IRS"         delimited by size into option-list   pointer a.
*>
  *>    if       OE
  *>             string "/ OE"          delimited by size into option-list   pointer a.
*>
*>  option-list now max 60 chars used
*>
     move     space to ws-Reply.
     display  option-list at 2401 with foreground-color 2.
     accept   ws-reply at 2326 with foreground-color 6.
     if               ws-reply not = "Y" and not = "y"
              go to ca001-Main.
*>              go to ca000-level-setup.
*>
 ca999-exit.
     exit     section.
*>
 da000-Common-ACAS-Procs section.
*>******************************
*>
 acas000.
     call     "acas000" using
                                System-Record
                                File-Access
                                File-Defs
                                ACAS-DAL-Common-data.
*>
 acas000-Open.
*>     set      fn-open to true.
*>     set      fn-i-o  to true.
     move     1 to File-Function.
     move     2 to Access-Type.
     perform  acas000.
*>
 acas000-Open-Input.
     set      fn-open  to true.
     set      fn-Input to true.
     perform  acas000.
*>
 acas000-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas000.
*>
 acas000-Close.
*>     set      fn-Close to true.
     move     2 to File-Function.
     perform  acas000.
*>
 acas000-Read-Indexed.
     set      fn-Read-Indexed to true.
     perform  acas000.
*>
 acas000-Write.
*>     set      fn-Write to true.
     move     5 to File-Function.
     perform  acas000.
*>
 acas000-ReWrite.
     move     7 to File-Function.
*>     set      fn-re-write to true.
     perform  acas000.
*>
