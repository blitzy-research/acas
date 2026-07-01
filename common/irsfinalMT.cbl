       >>source free
*>***********************************************
*>                                              *
*>                   irsfinal                   *
*>               Table RDB Handler              *
*>                                              *
*> This is a modified variant of a DAL for irs  *
*>  as it uses reduced functions.               *
*>                                              *
*>***********************************************
*>
 identification division.
 Program-Id.            irsfinalMT.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License
*>                      v2.0. Only. See the file COPYING for details.
*>**
*> Remarks.             irsfinal  File RDB Handler using amended JC preSQL.
*>                      **********************************************
*>
*>                      This version uses an amended JC pre-Sql processor.
*>                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>**
*>  File Handling:
*>     Uses the Global Error / Access logging file within the acas0nn module.
*>**
*> Called by Modules:
*>                      acasirsub5 - irsfinal  Cobol Handler.
*>
*>**
*> Error Messages Used.
*>                      SM004 SQL Err no in 'mysql-procedures'
*>                      SM901 Note error and hit return.
*>**
*> Version.             1.00 17/06/2016.
*>
*>**
*> Changes.
*> 17/11/16 vbc - .08 Taken from irsdfltMT AND finalMT.
*> 30/12/16 vbc - .09 Now using Sql-State as well.
*>                    THIS is NOT having the sqlstate or errno between writes/rewrites
*>                     might be needed.
*> 01/03/18 vbc - .11 Renamed error messages to SM901, SM004 as needed.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>  Module USAGE see irsdflt for details.
*>**
 copy "ACAS-SQLstate-error-list.cob".
*>
*>********************************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 2024-04-16.
*>
*> These files and programs are part of the Applewood Computers Accounting
*> System and is Copyright (c) Vincent B Coen. 1976-2025 and later.
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
*>**********************************************************************************
*>
 environment division.
 copy "envdiv.cob".
*>
 input-output section.
 Data Division.
 Working-Storage Section.
 77  prog-name          pic x(20)    value "irsfinalMT (3.3.00)".
*>
*> JC WS requirements here
*>
 77  ws-Where           pic x(512).
*>
*>  Used within presql generated code
*>
 01  WS-Reply           pic x           value space.
 01  WS-MYSQL-I         PIC S9(6) COMP.
 01  WS-MYSQL-EDIT      PIC -Z(18)9.9(9).
 01  WS-Key             pic 99.
*>
*> The communication area for the MySQL database changed for free/mysql
*>
*>  jc preSQL MySQL stuff ends
*>
*> Metadata on primary and alternate keys...  from Prima DAL for IRSFINAL-REC
*>
 01  Table-Of-Keynames.
     03  filler         pic x(30) value 'IRS-FINAL-ACC-REC-KEY         '.
     03  filler         pic x(8)  value '00010001'. *> offset/length  as one byte (tinyint)
     03  filler         pic x(3)  value 'STR'. *> data type
 01  filler redefines table-of-keynames.
     03  keyOfReference occurs 1   indexed by KOR-x1.
         05  KeyName    pic x(30).
         05  KOR-Offset pic 9(4).
         05  KOR-Length pic 9(4).
         05  KOR-Type   pic XXX.                    *> Not used currently
*>
*> The START condition cannot be compounded, and it must use a
*> Key of Reference within the record. (These are COBOL rules...)
*> The interface defines which key and the relation condition.
*>
*>
 01  DAL-Data.
         05  MOST-Relation   pic xxx.                  *> valid are >=, <=, <, >, =
         05  Most-Cursor-Set pic 9    value zero.
             88  Cursor-Not-Active    value zero.
             88  Cursor-Active        value 1.
*>
*>  Variables common to all DALs
*>  ****************************
*>
 01  subscripts comp-5.
     12 J                pic s9(4).
     12 K                pic s9(4).
     12 L                pic s9(4).
*>
 01  Old-File-Function   pic 9 value zero.
*>
 01  work-fields.
     03  ws-saved-fs-reply pic 99.
     03  ws-env-lines    pic 999              value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
     03  ws-98-lines     binary-char unsigned value zero.
     03  ws-99-lines     binary-char unsigned value zero.
     03  ws-Rec-Cnt      binary-long unsigned value zero.
*>
 01  Temp-work-fields.
     03  Temp-SQL-Err    pic x(5).     *> 29/07/16
     03  A               pic 99      comp     value zero.
*>
 01  Error-Messages.
     03  SM901          pic x(31) value "SM901 Note error and hit return".
*>
*> /MYSQL VAR\
*>       ACASDB
*>       TABLE=IRSFINAL-REC,HV
 COPY "mysql-variables.cpy".
*>
*>    Definitions for the IRSFINAL-REC Table
*>
       01  TP-IRSFINAL-REC                       USAGE POINTER.
       01  TD-IRSFINAL-REC.
           05  HV-IRS-FINAL-ACC-REC-KEY          PIC  9(03) COMP.
           05  HV-IRS-AR1                        PIC X(24).
           05  HV-IRS-AR2                        PIC X(1).
*> /MYSQL-END\

 Linkage Section.
*>**************
*>
*>**************************************************************
 copy "wsfnctn.cob".            *> File-Access
*>
*>**************************************************************
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
 copy "irswsfinal.cob".
*>
 screen section.
*>=============
*>
 01  Display-Message-1       foreground-color 2.
     03          value "WS-Where="      line 23 col  1.
     03  from WS-Where (1:J)           pic x(69)         col 10.
*>
 01  Display-Message-2       foreground-color 2.
     03      value "SM004 SQL Err No.=" line 4 col  1.    *> size 18 char
     03  using Ws-Mysql-Error-Number   pic x(4)          col 19.    *>      4       == 22
     03      value " Para="                              col 23.    *> size 6 char  == 28
     03  using WS-No-Paragraph         pic 9(3)          col 29.    *>      4       == 32
     03      value " SQL Cmd="                           col 32.    *>      9       == 41
     03  using Ws-Mysql-Command        pic x(199)         col 41.
     03      value "SQL Err Msg="       line 7 col  1.    *>      12
     03  using Ws-Mysql-Error-Message  pic x(67)        col 13.
*>
*>
 PROCEDURE DIVISION   using File-Access
                            ACAS-DAL-Common-data
                            Final-Record.   *>  Ws record
*>**********************************************
 ba-ACAS-DAL-Process  section.
     accept   ws-env-lines from lines.
     if       ws-env-lines < 24
              move  24 to ws-env-lines ws-lines
     else
              move  ws-env-lines to ws-lines
     end-if
*> Force Esc, PgUp, PgDown, PrtSC to be detected
     set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
     set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
 ba010-Initialise.
     move     zero   to We-Error                        *> as in irsub5
     move     spaces to WS-MYSQL-Error-Message
                        WS-MYSQL-Error-Number
                        WS-Log-Where
                        WS-File-Key
                        SQL-Msg
                        SQL-Err
                        SQL-State.
*>
*>   As this is for only one set of 32 rows we will skip this ...
*>
*>  Work out what is being requested and convert to action!!
*>
*>    This version uses the JC pre-Sql processor.
*>    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
     evaluate File-Function
        when  1
              go to ba020-Process-Open
        when  2
              go to ba030-Process-Close
        when  3
              go to ba040-Process-Read-Next
        when  5
              go to ba070-Process-Write
        when  7
              go to ba090-Process-Rewrite
        when  other                     *> others are unused
              go to ba100-Bad-Function
     end-evaluate.
*>
 ba020-Process-Open.
*>
*> To get here the calling program MUST have read the Cobol system record first.
*>

 *>
 *>  Manual process MYSQL INIT
 *>    then perform MYSQL-1000-OPEN  THRU MYSQL-1090-EXIT
 *>
     string   DB-Schema      delimited by space
              X"00"          delimited by size
                               into WS-MYSQL-BASE-NAME
     end-string.
     string   DB-Host        delimited by space
              X"00"          delimited by size
                               into WS-MYSQL-HOST-NAME
     end-string.
     string   DB-UName       delimited by space
              X"00"          delimited by size
                               into WS-MYSQL-IMPLEMENTATION
     end-string.
     string   DB-UPass       delimited by space
              X"00"          delimited by size
                               into WS-MYSQL-PASSWORD
     end-string.
     string   DB-Port        delimited by space
              X"00"          delimited by size
                               into WS-MYSQL-PORT-NUMBER
     end-string.
     string   DB-Socket      delimited by space
              X"00"          delimited by size
                               into WS-MYSQL-SOCKET
     end-string.
     move     1 to ws-No-Paragraph.
     PERFORM  MYSQL-1000-OPEN  THRU MYSQL-1090-EXIT.
     if       fs-reply not = zero
              go   to ba999-end.
*>
*> /MYSQL INIT\
*>       BASE=ACASDB
*>       IMPLEMENTATION=dev-prog-001
*>       PASSWORD=mysqlpass
*> /MYSQL-END\
*>
     move    "OPEN IRS FINAL" to WS-File-Key
     move    zero   to Most-Cursor-Set
     go      to ba999-end.
*>
 ba030-Process-Close.
     if      Cursor-Active         *> this will not occur for the system rows/records
             perform ba998-Free.
*>
     move     2 to ws-No-Paragraph.
     move    "CLOSE IRS FINAL" to WS-File-Key.
*>  /MYSQL CLOSE\
*>
*>    Close the Database
*>
           PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
*>  /MYSQL-END\
*>
     go      to ba999-end.
*>
 ba040-Process-Read-Next.
*>
*> Getting the 26 rows for loading into one cobol rec
*>  having initialised record as some rows may not be present
*>   if Cobol record has no data for a heading.
*>    Same applies to the write process.
*>
*>   Here a SELECT first then fetch if no cursor active using lowest
*>    possible key of "000"
*>           [ IRS-FINAL-ACC-REC-KEY ]
*>
     if       Cursor-Not-Active
              set      KOR-x1 to 1
              move     KOR-offset (KOR-x1) to K
              move     KOR-length (KOR-x1) to L
*>
              move     spaces to WS-Where
              move     1   to J
              string   "`"                   delimited by size
                       KeyName (KOR-x1)      delimited by space
                       "`"                   delimited by size
                       " > "                 delimited by size
                       '"000"'             delimited by size
                       ' ORDER BY '          delimited by size
                       "`"                   delimited by size
                       KeyName (KOR-x1)      delimited by space
                       "`"                   delimited by size
                         ' ASC'              delimited by size
                                      into ws-Where
                                      with pointer J
              end-string
*>
              move     ws-Where (1:J)   to WS-Log-Where       *>  For test logging
              move     3 to ws-No-Paragraph
 *> IRS-FINAL-ACC-REC-KEY > "000" ORDER BY IRS-FINAL-ACC-REC-KEY ASC
*>               /MYSQL SELECT\
*>
*>    Select rows
*>
*>                    TABLE=IRSFINAL-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`IRSFINAL-REC`"
             " WHERE "
             ws-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-IRSFINAL-REC
*>               /MYSQL-END\
           move    "000" to WS-File-Key
              if    Testing-2
                    display Display-Message-1 with erase eos
              end-if
*>
*>  It could be an empty table so test for it
*>
              if       WS-MYSQL-Count-Rows = zero
                       call  "MySQL_errno" using WS-MYSQL-Error-Number
                       if    WS-MYSQL-Error-Number  not = "0  "    *> set non '0' if no rows ?
                             move WS-MYSQL-Error-Number to SQL-Err
                             call "MySQL_error" using WS-MYSQL-Error-Message
                             move WS-MYSQL-Error-Message to SQL-Msg
                       end-if       *> do not really need to do this meaning the above CALL
                       call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                       move  WS-MYSQL-SqlState   to SQL-State
                       move  10 to fs-reply
                       move  10 to WE-Error
                       move    "No Data" to WS-File-Key
                       go to ba998-Free        *> can clear the dup code after testing
              end-if
              move     1 to Most-Cursor-Set    *> should test if select worked first??????
     end-if.
*>
*>  If here cursor is set, so get all the (up to 26) rows in one hit
*>
     move     spaces to WS-Log-Where.
     move     4 to ws-No-Paragraph.
     initialize Final-Record with filler.
     perform  varying A from 1 by 1
                    until A > 26
 *>                      or return-code not = zero
*>       /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>              TABLE=IRSFINAL-REC
           MOVE TP-IRSFINAL-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-IRS-FINAL-ACC-REC-KEY
                    HV-IRS-AR1
                    HV-IRS-AR2

*>       /MYSQL-END\
      end-call
*>
*> No it should not happen but ..
*>
              if       return-code = -1     *> no more data so free cursor & return
                  or   A > 26 or = zero
                       move 10 to fs-Reply WE-Error
                       move    "EOF" to WS-File-Key
                       move     zero to Most-Cursor-Set
                       if       Testing-1                                      *> do for each row
                                perform Ca-Process-Logs
                       end-if
                       exit perform
              end-if
 *> return-code = zero    and
              if       HV-IRS-FINAL-ACC-REC-KEY = zero or > 26
                       move    "EOF3" to WS-File-Key
                       move    HV-IRS-FINAL-ACC-REC-KEY to WE-Error
                       move     zero to Most-Cursor-Set
                       if       Testing-1                                      *> do for each row
                                perform Ca-Process-Logs
                       end-if
                       exit perform
              end-if
*>
              move     HV-IRS-FINAL-ACC-REC-KEY to WS-File-Key
              if       WS-MYSQL-Count-Rows = zero
                       call  "MySQL_errno" using WS-MYSQL-Error-Number
                       if    WS-MYSQL-Error-Number  not = "0  "
                             call "MySQL_error" using WS-MYSQL-Error-Message
                             move 10 to fs-reply                     *> EOF equivilent !!
                             move 10 to WE-Error
                             move WS-MYSQL-Error-Number  to SQL-Err   *> Not really needed but help for testing
                             move WS-MYSQL-Error-Message to SQL-Msg   *>  ditto
                             move    "EOF2" to WS-File-Key
                       end-if
                       call     "MySQL_sqlstate" using WS-MYSQL-SQLstate
                       move     WS-MYSQL-SqlState   to SQL-State
                       move     zero to Most-Cursor-Set
                       if       Testing-1                                      *> do for each row
                                perform Ca-Process-Logs
                       end-if
                       exit perform
              end-if
              move     HV-IRS-AR1    to AR1 (HV-IRS-FINAL-ACC-REC-KEY)     *> KEY = table position
              move     HV-IRS-AR2    to AR2 (HV-IRS-FINAL-ACC-REC-KEY)
              if       Testing-1
                       perform Ca-Process-Logs
                       move     zeros to FS-Reply SQL-Err
                       move     spaces to SQL-Msg
              end-if
     end-perform                                                      *> Have all of the data
*>
     move     HV-IRS-FINAL-ACC-REC-KEY to WS-File-Key.
     move     zero to fs-reply WE-Error.
     go       to ba999-exit.  *> have written logs if testing
*>
 ba070-Process-Write.
     move     zero to WS-Mysql-Time-Step
                      WS-SQL-Retry.
*>
     move     zero to FS-Reply WE-Error
     move     spaces to SQL-Msg
     move     zero to SQL-Err
     move     10 to ws-No-Paragraph.
     perform  varying A from 1 by 1 until A > 26
 *>             if       AR1 (A) = spaces              *> dont write out blank data
 *>                 and  AR2 (A) = spaces
 *>                      exit perform cycle
 *>             end-if
              move     A        to HV-IRS-FINAL-ACC-REC-KEY
                                   WS-Key
              move     WS-Key   to WS-File-Key               *> will contain the record with problems
              move     AR1 (A)  to HV-IRS-AR1
              move     AR2 (A)  to HV-IRS-AR2
              perform  bb200-Insert
              if       WS-MYSQL-COUNT-ROWS not = 1
                       call  "MySQL_errno" using WS-MYSQL-Error-Number
                       call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                       move  WS-MYSQL-SqlState   to SQL-State
                       if    WS-MYSQL-Error-Number  not = "0  "  *> 14/12/16
                             call "MySQL_error" using Ws-Mysql-Error-Message
                             move WS-MYSQL-Error-Number  to SQL-Err
                             move WS-MYSQL-Error-Message to SQL-Msg
                             if    SQL-Err (1:4) = "1062"
                                              or = "1022"   *> Dup key (rec already present)
                                    or Sql-State = "23000"  *> Dup key (rec already present)
                                   move 22 to fs-reply
                             else
                                   move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
                             end-if
                       end-if
              end-if
              if       Testing-1
                       perform Ca-Process-Logs
   *>                    move     zeros to FS-Reply SQL-Err
   *>                    move     spaces to SQL-Msg
              end-if
              if       fs-reply not = zero
                       move fs-reply to ws-saved-fs-reply
                       move zero to fs-reply                   *> for next loop iteration
              end-if
     end-perform
     if       ws-saved-fs-reply not = zero                     *> restore last error
              move ws-saved-fs-reply to fs-reply
     end-if
     go       to ba999-Exit.
*>
 ba090-Process-Rewrite.
*>
     move     zero to WS-Mysql-Time-Step
                      WS-SQL-Retry.
     move     17 to ws-No-Paragraph.
     perform  varying A from 1 by 1 until A > 26
              move     A        to WS-Key
              move     WS-Key   to WS-File-Key               *> will contain the record with problems
                                   HV-IRS-FINAL-ACC-REC-KEY
              move     AR1 (A)  to HV-IRS-AR1
              move     AR2 (A)  to HV-IRS-AR2
*>
              set      KOR-x1 to 1            *> 1 = Primary, 2 = Abrev, 3 = Desc (NOT Delete function as can be dups)
              move     KOR-offset (KOR-x1) to K
              move     KOR-length (KOR-x1) to L
*>
              move     spaces to WS-Where
              move     1   to J
              string   "`"                   delimited by size
                       KeyName (KOR-x1)      delimited by space
                       "`"                   delimited by size
                       '="'                  delimited by size
*>                       Final-Record (K:L)       delimited by size
                       WS-Key                delimited by size *> use the real key for row
                       '"'                   delimited by size
                               into WS-Where
                                 with pointer J
              end-string
              move     WS-Where (1:J)   to WS-Log-Where    *>  For test logging
              perform  bb300-Update
*>
              if       Testing-2
                       display Display-Message-1 with erase eos
              end-if
*>
              if       WS-MYSQL-COUNT-ROWS not = 1
                       call  "MySQL_errno" using WS-MYSQL-Error-Number
                       call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                       move  WS-MYSQL-SqlState   to SQL-State
                       if    WS-MYSQL-Error-Number  not = "0   "
                             call "MySQL_error" using Ws-Mysql-Error-Message
                             move WS-MYSQL-Error-Number  to SQL-Err
                             move WS-MYSQL-Error-Message to SQL-Msg
                             move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
                             move 994 to WE-Error
                       end-if
              end-if
              if       Testing-1
                       perform Ca-Process-Logs
              end-if
     end-perform
*>
     move     zero   to FS-Reply WE-Error.
     move     zero   to SQL-Err.
     move     spaces to SQL-Msg.
     go       to ba999-exit.
*>
 ba100-Bad-Function.
*>
*> Houston; We have a problem
*>
     move     990 to WE-Error.
     move     99 to Fs-Reply.
     go       to ba999-end.
*>
*> /MYSQL PRO\
 COPY "mysql-procedures.cpy".
*> /MYSQL-END\
*>
 ba998-Free.
     move     20 to ws-No-Paragraph.
*>      /MYSQL FREE\
*>
*>    Free result array
*>
*>             TABLE=IRSFINAL-REC
           MOVE TP-IRSFINAL-REC TO WS-MYSQL-RESULT
           CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
*>      /MYSQL-END\
     move     zero to Most-Cursor-Set.
*>
 ba999-end.
*>
     if       Testing-1
              perform Ca-Process-Logs
     end-if.
*>
 ba999-exit.
     exit program.
*>
 bb200-Insert Section.
*>*******************
*>
*>  /MYSQL INSERT\
*>
*>    Insert a row
*>
*>         TABLE=IRSFINAL-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'INSERT INTO '
                    '`IRSFINAL-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-FINAL-ACC-REC-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-IRS-FINAL-ACC-REC-KEY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-AR1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-IRS-AR1,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-AR2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-IRS-AR2,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ";" INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING X"00" INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
       PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>  /MYSQL-END\
       .     *> period here
*>
 bb200-Exit.
     exit section.
*>
 bb300-Update Section.
*>*******************
*>
*>  /MYSQL UPDATE\
*>
*>    Update a row
*>
*>      TABLE=IRSFINAL-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'UPDATE '
                    '`IRSFINAL-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-FINAL-ACC-REC-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-IRS-FINAL-ACC-REC-KEY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-AR1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-IRS-AR1,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-AR2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-IRS-AR2,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING " WHERE "
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (WS-Where (1:J))
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
           STRING ";" X"00" INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>  /MYSQL-END\
       .     *> period here
*>
 bb300-Exit.
     exit section.
*>
 Ca-Process-Logs.
*>**************
*>
     call     "fhlogger" using File-Access
                               ACAS-DAL-Common-data.
*>
 ca-Exit.     exit.
*>
 end program irsfinalMT.
