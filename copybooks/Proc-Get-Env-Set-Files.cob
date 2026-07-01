*>
*> 28/10/16 vbc - .00  Made a copybook to make it easier for maintenance
*>                     All msgs start with SY00.
*>                     Rem out all refs to ACAS_IRS as all files in same dir
*>                     after RDB conv and using ACAS system param file.
*> 14/03/18 vbc - .01  Accept more than one param in case cron running to force a
*>                     program to be run via the menu programs without user intervention.
*>                     This at least for running st020 and st040.
*>                     There may well be more.
*> 21/04/18 vbc - .02  Added xl150 called by sales and purchase.
*>                     New creates ACAS-Path with path/
*> 29/04/18 vbc - .03  Added extra test and display if error in program-get-args.
*> 24/05/18 vbc - .04  Changed method of getting program command line params as existing
*>                     is not working correctly.
*> 31/05/23 vbc - .05  USe TRIM when getting ACAS-LEDGER content.
*>
 zz010-Get-Env-Set-Files section.
*>******************************
*>
     accept   ACAS_LEDGERS from Environment "ACAS_LEDGERS".
     accept   ACAS_BIN     from Environment "ACAS_BIN".
*>
     if       ACAS_LEDGERS (1:1) = spaces
           or ACAS_BIN (1:1) = spaces
              display SY009   at 0505 with erase eos highlight
              display SY008   at 1210 with           foreground-color 3 highlight
              accept ws-reply at 1243
              stop run
     end-if
     if       ACAS_LEDGERS (1:1) = "\" or "/"          *> Its Windows or Linux/Unix/OSX
              move ACAS_LEDGERS (1:1) to OS-Delimiter      *> "  (4 editor kate)
     end-if.
*>
 zz010-GESF-Exit.
     exit     section.
*>
 zz020-Get-Program-Args      section.
*>**********************************
*>
     perform  zz010-Get-Env-Set-Files.          *> This must be set so get it 1st + need os-delimiter
*>
*> See if we have temporary overrides that have been supplied when calling program
*> Also possible are request to run specific progs via menu without user intervention.
*>  so allowing for 2 params on the line & here param 1 can be one of:
*>     'NONE', 'NULL', 'ACAS_LEDGERS='
*>
     move     spaces to Arg-Test
                        WS-CD-Args in WS-Calling-Data.
     move     1 to z.
     accept   Arg-Vals from command-line.
     unstring Arg-Vals delimited by space
               into Arg-Test
               with pointer z.
   *>  move     function upper-case (Arg-Test) to Arg-Test.
*>
 *>    accept   Arg-Number from argument-number.
 *>    if       Arg-Number = zero
 *>             go to zz020-Set-the-Paths.
*>
     if       Arg-Test (1:5) = spaces
              go to zz020-Set-the-Paths.
*>
 *>    if       Arg-Number > 2
 *>             display SY006      at 0101 with erase eos foreground-color 3
 *>             display Arg-Number at 0164 with           foreground-color 3
 *>             display SY008      at 1210 with           foreground-color 3 highlight
 *>             accept ws-reply    at 1243
 *>             stop run.
*>
 *>    accept   Arg-Value (1) from argument-value.
 *> MUST BE IN CASE SO..
 *>    move     function upper-case (Arg-Value (1)) to Arg-Test.
     if       Arg-Test (1:12) not = "ACAS_LEDGERS"
         and  Arg-Test (1:4) not = "NULL" and not = "NONE"
              display SY007           at 0101 with erase eos foreground-color 3
              display "Arg-No="       at 0501 with foreground-color 2
              display Arg-Number      at 0508 with foreground-color 2
              display "Arg Val="      at 0601 with foreground-color 2
              display Arg-Test (1:40) at 0609 with foreground-color 2
              display SY008           at 1210 with foreground-color 3 highlight
              accept ws-reply         at 1243
              stop run
     end-if
     if       Arg-Test (1:13) = "ACAS_LEDGERS="
              move FUNCTION TRIM (Arg-Test (14:487), TRAILING) to ACAS_LEDGERS  *> 31/05/23
     end-if
*>
*> arg-test can have one or more chars after 'stnnn' to control called programs processes
*>  the first is compulsory:
*>  For st040 it is 5 to clear period totals or month within year values down.
*>   2nd digit is what to clear 1 = period, 2 = month within year, 3 = both.
*>
     move     spaces to Arg-Test.
     unstring Arg-Vals delimited by space
               into Arg-Test
               with pointer z.
*>
     if       Arg-Test (1:4) not = spaces
 *>    if       Arg-Number = 2
 *>             accept   Arg-Value (2) from argument-value
 *>             move     function lower-case (Arg-Value (2)) to Arg-Test
   *>           move function lower-case (Arg-Test) to Arg-Test
              if       Arg-Test (1:5) = "st020" or "ST020"
                                   or = "st040" or "ST040"
                                   or = "xl150" or "XL150"
                       move function lower-case (Arg-Test (1:13)) to WS-CD-Args in WS-Calling-Data
              end-if
     end-if
*>
     if       ACAS_LEDGERS (1:1) = "\" or "/"   *> Its Windows or Linux/Unix/OSX "
              move ACAS_LEDGERS (1:1) to OS-Delimiter
     end-if.
*>
*>  Put absolute path with file names into the file-id areas over-writing filename.
*>    Note that count in perform is equal to number of files used in system & wsnames.cob held
*>       in File-Defs-Count
*>
 zz020-Set-the-Paths.
     if       function MODULE-CALLER-ID = "ACAS"      *> Called by ACAS main program
              go to zz020-Exit                        *> so done already
     end-if
     if       File-Defs-os-Delimiter = "\" or "/"     *> shows its been done already "
              go to zz020-Exit.
*>
*> Here updating by preceding each filename by the path in ACAS_LEDGERS
*>
     move     zero to z.
     perform  File-Defs-Count times
              add 1 to z
              move space to Arg-Test
              string ACAS_LEDGERS          delimited by space
                     OS-Delimiter          delimited by size
                     System-File-Names (z) delimited by space
                                             into Arg-Test
              end-string
              move     Arg-Test to System-File-Names (z)
     end-perform
     move     zero to z.
     move     OS-Delimiter to File-Defs-os-Delimiter.    *> in wsnames showing paths has been setup.
*>
     move     spaces to ACAS-Path.
     string   ACAS_LEDGERS          delimited by space
              OS-Delimiter          delimited by size
                                       into ACAS-Path.
*>
 zz020-Exit.
     exit   section.
*>
