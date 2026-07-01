       >>source free
*>***********************************************
*>                                              *
*>                 IRS Postings                 *
*>            File/Table RDB Handler            *
*>                                              *
*>***********************************************
*>
 identification division.
 Program-Id.            irspostingMT.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License
*>                      v2.0. Only. See the file COPYING for details.
*>**
*> Remarks.             (IRS) Postings File RDB Handler using amended JC preSQL.
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
*>                      acasirsub4 - irsposting Cobol Handler. irsub4 replacement.
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
*> 15/11/16 vbc - .06 Taken from irsnominalMT & modified for IRS processing & based on
*>                    irsub4.
*> 22/12/16 vbc - .07 Changed to support fn-delete-all so that all
*>                    CoA can be cleared down (similarly to open output).
*>                    Forgot to add chg log for .06.
*> 30/12/16 vbc - .08 Now using Sql-State as well.
*> 31/12/16 vbc - .09 Added fields post4-day, post4-month, post4-year as new
*>                    columns so that sorting can occur within mysql as
*>                    selects. Pre-sort will need changes to cater if RDB
*>                    is in use. Only should apply to write/rewrite operations.
*>                    No changes needed for irspostingLD.
*>                .10 Force logging at end of rewrite process - missed.
*>                    On rewrite not setting post-key for logging.
*> 01/03/18 vbc - .11 Renamed error messages to SM901, SM004 as needed.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>  Module USAGE see irsdflt for details.
*>
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
*> copy "envdiv.cob".
*>
 input-output section.
 Data Division.
 Working-Storage Section.
 77  prog-name           pic x(22)    value "irspostingMT (3.3.00)".
*>
*> JC WS requirements here
*>
 77  ws-Where            pic x(512).
*>
*>  Used within presql generated code
*>
 01  WS-Reply            pic x           value space.
 01  WS-MYSQL-I          PIC S9(4) COMP.
 01  WS-MYSQL-EDIT       PIC -Z(18)9.9(9).
 *>
 *> TESING data
 *>
 01  ws-temp-ed          pic 9(10).
*>
*> The communication area for the MySQL database changed for free/mysql
*>
*>  jc preSQL MySQL stuff ends
*>
*> Metadata on primary and alternate keys...  from Prima DAL for IRSPOSTING-REC
*>
 01  Table-Of-Keynames.
     03  filler          pic x(30) value "KEY-4                         ". *> in RDB
     03  filler          pic x(8)  value "00010005". *> offset/length in ws rec
     03  filler          pic xxx   value "STR".      *> key is string
*>
 01  filler redefines table-of-keynames.
     03  keyOfReference occurs 1    indexed by KOR-x1.
         05 KeyName      pic x(30).
         05 KOR-Offset   pic 9(4).
         05 KOR-Length   pic 9(4).
         05 KOR-Type     pic XXX.                    *> Not used currently
*>
*> The START condition cannot be compounded, and it must use a
*> Key of Reference within the record. (These are COBOL rules...)
*> The interface defines which key and the relation condition.
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
 01  subscripts usage comp-5.
     12 J                pic s9(4).
     12 K                pic s9(4).
     12 L                pic s9(4).
*>
 01  work-fields.
     03  ws-env-lines    pic 999              value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
     03  ws-98-lines     binary-char unsigned value zero.
     03  ws-99-lines     binary-char unsigned value zero.
     03  ws-Rec-Cnt      binary-long unsigned value zero.
*>
 01  Error-Messages.
     03  SM901          pic x(31) value "SM901 Note error and hit return".
*>
*> /MYSQL VAR\
*>       ACASDB
*>       TABLE=IRSPOSTING-REC,HV
 COPY "mysql-variables.cpy".
*>
*>    Definitions for the IRSPOSTING-REC Table
*>
       01  TP-IRSPOSTING-REC                     USAGE POINTER.
       01  TD-IRSPOSTING-REC.
           05  HV-KEY-4                          PIC  9(08) COMP.
           05  HV-POST4-CODE                     PIC X(2).
           05  HV-POST4-DAT                      PIC X(8).
           05  HV-POST4-DAY                      PIC  9(03) COMP.
           05  HV-POST4-MONTH                    PIC  9(03) COMP.
           05  HV-POST4-YEAR                     PIC  9(03) COMP.
           05  HV-POST4-DR                       PIC  9(08) COMP.
           05  HV-POST4-CR                       PIC  9(08) COMP.
           05  HV-POST4-AMOUNT                   PIC S9(07)V9(02) COMP.
           05  HV-POST4-LEGEND                   PIC X(32).
           05  HV-VAT-AC-DEF4                    PIC  9(03) COMP.
           05  HV-POST4-VAT-SIDE                 PIC X(2).
           05  HV-VAT-AMOUNT4                    PIC S9(07)V9(02) COMP.
*> /MYSQL-END\
*>
 Linkage Section.
*>**************
*>
*>**********************************************************************
 copy "wsfnctn.cob".                         *> File-Access
*>
*>**********************************************************************
*>
 copy "Test-Data-Flags.cob".  *> set sw-testing to zero to stop logging.
*>
*>  Record definition for Cobol file here:
*>
 copy "irswspost.cob".
*>
 screen section.
*>=============
*>
 01  Display-Message-1       foreground-color 2.
     03          value "WS-Where="                line 23 col  1.
     03  from WS-Where (1:J)           pic x(69)          col 10.
*>
 01  Display-Message-2       foreground-color 2.
     03      value "SM004 SQL Err No.="            line 4 col  1.    *> size 18 char
     03  using Ws-Mysql-Error-Number   pic x(4)           col 19.    *>      4       == 22
     03      value " Para="                               col 23.    *> size 6 char  == 28
     03  using WS-No-Paragraph         pic 9(3)           col 29.    *>      4       == 32
     03      value " SQL Cmd="                            col 32.    *>      9       == 41
     03  using Ws-Mysql-Command        pic x(199)         col 41.
     03      value "SQL Err Msg="                  line 7 col  1.    *>      12
     03  using Ws-Mysql-Error-Message  pic x(67)          col 13.
*>
*>
 PROCEDURE DIVISION   using File-Access
                            ACAS-DAL-Common-data
                            Posting-Record.   *>  Ws record
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
*>
     move     zero   to We-Error                        *> as in irsub4
                        SQL-State
                        Fs-Reply.    *> for testing as in irsub4 Not used.
*>
     move     spaces to WS-MYSQL-Error-Message
                        WS-MYSQL-Error-Number
                        WS-Log-Where
                        WS-File-Key
                        SQL-Msg
                        SQL-Err.
*>
*>   Now Test for valid key for start, read-indexed and delete
*>      REMOVED as not used here
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
        when  4
              go to ba050-Process-Read-Indexed
        when  5
              go to ba070-Process-Write
*>
*> option 6 is a special to cleardown all data
*>
        when  6                              *> DELETE-ALL  Special
              go to ba085-Process-DELETE-ALL
        when  7
              go to ba090-Process-Rewrite
        when  8
              go to ba080-Process-Delete
        when  9
              go to ba060-Process-Start
        when  other
              go to ba100-Bad-Function
     end-evaluate.
*>
 ba020-Process-Open.
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
*> *> /MYSQL INIT\
*>       BASE=ACASDB
*>       IMPLEMENTATION=dev-prog-001
*>       PASSWORD=mysqlpass
*> *> /MYSQL-END\
*>
     move    "OPEN IRSPOSTING" to WS-File-Key
     move    zero   to Most-Cursor-Set
     go      to ba999-end.
*>
 ba030-Process-Close.
     if      Cursor-Active
             perform ba998-Free.
*>
     move     2 to ws-No-Paragraph.
     move    "CLOSE IRSPOSTING" to WS-File-Key.
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
*>  Uses 3 (instead of 10) as EOF flag in WE-Error per irsub4
*>
*>   Here a SELECT first then fetch if no cursor active using lowest
*>    possible key of "00000"
*>           [ KEY-1 ]
*>
     if       Cursor-Not-Active
              set      KOR-x1 to 1                *> 1 = Primary
              move     KOR-offset (KOR-x1) to K
              move     KOR-length (KOR-x1) to L
*>
              move     spaces to WS-Where
              move     1   to J
              string   "`"                   delimited by size
                       KeyName (KOR-x1)      delimited by space
                       "`"                   delimited by size
                       " >= "                 delimited by size   *> nom uses >
                       '"00000"'         delimited by size
                       ' ORDER BY '          delimited by size
                       "`"                   delimited by size
                       keyname (KOR-x1)      delimited by space
                       "`"                   delimited by size
                         ' ASC '              delimited by size
                                      into ws-Where
                                      with pointer J
              end-string
*>
              move     ws-Where (1:J)   to WS-Log-Where       *>  For test logging
              move     3 to ws-No-Paragraph
*>               /MYSQL SELECT\
*>
*>    Select rows
*>
*>                    TABLE=IRSPOSTING-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`IRSPOSTING-REC`"
             " WHERE "
             ws-Where (1:J)      *> KEY-1 > "00000" ORDER BY IRSPOSTING-REC ASC
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-IRSPOSTING-REC
*>               /MYSQL-END\
           move    "00000" to WS-File-Key
              if    Testing-2
                    display Display-Message-1 with erase eos
              end-if
*>
*>  It could be an empty table so test for it
*>
              if       WS-MYSQL-Count-Rows = zero
                       call  "MySQL_errno" using WS-MYSQL-Error-Number
                       call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                       move  WS-MYSQL-SqlState   to SQL-State
                       if    WS-MYSQL-Error-Number  not = "0  "    *> set non '0' if no rows ?
                             move WS-MYSQL-Error-Number to SQL-Err
                             call "MySQL_error" using WS-MYSQL-Error-Message
                             move WS-MYSQL-Error-Message to SQL-Msg
                       end-if       *> do not really need to do this meaning the above CALL
                       move 10 to fs-reply
    *>                   move 10 to WE-Error
                     move 3 to WE-Error                 *> as in irsub4
                       move    "No Data" to WS-File-Key
                       go to ba999-End       *> can clear the dup code after testing
              end-if
              set      Cursor-Active to true
              move     WS-MYSQL-Count-Rows to WS-Temp-Ed
              string   "> 0 got cnt=" delimited by size
                       WS-Temp-ED delimited by size
                       " recs"
                        into WS-File-Key
              end-string
              perform ba999-End                         *> log it
     end-if.
*>
 ba041-Reread.
*>
*>  If here cursor is set (even from start), so get the next row
*>
     move     spaces to WS-Log-Where.
     move     4 to ws-No-Paragraph.

     move zero to return-code.

*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=IRSPOSTING-REC
           MOVE TP-IRSPOSTING-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-KEY-4
                    HV-POST4-CODE
                    HV-POST4-DAT
                    HV-POST4-DAY
                    HV-POST4-MONTH
                    HV-POST4-YEAR
                    HV-POST4-DR
                    HV-POST4-CR
                    HV-POST4-AMOUNT
                    HV-POST4-LEGEND
                    HV-VAT-AC-DEF4
                    HV-POST4-VAT-SIDE
                    HV-VAT-AMOUNT4

*>      /MYSQL-END\
     end-call
*>
     if       return-code = -1                  *> no more data so free cursor & return
              move 10 to fs-Reply        *> WE-Error
            move 3 to WE-Error                       *> as in irsub4
              move    "EOF" to WS-File-Key
              set Cursor-Not-Active to true
              go to ba999-End
     end-if
*>
     if       WS-MYSQL-Count-Rows = zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move 10 to fs-reply                  *> EOF equivilent !!
 *>                   move 10 to WE-Error
                    move 3 to WE-Error                 *> as in irsub4
                    move WS-MYSQL-Error-Number  to SQL-Err   *> Not really needed but help for testing
                    move WS-MYSQL-Error-Message to SQL-Msg   *>  ditto
                    initialize Posting-Record with filler
              move    "EOF2" to WS-File-Key
              end-if
              set Cursor-Not-Active to true
              go to ba999-End
     end-if.
*>
     if       fs-reply = 10
              set Cursor-Not-Active to true
              move    "EOF3" to WS-File-Key
              go to ba999-End
     end-if.
     perform  bb100-UnloadHVs.       *> transfer/move HV vars to Record layout
*>
     move     HV-KEY-4 to WS-File-Key.
     move     zero to fs-reply WE-Error.
     go       to ba999-end.
*>
 ba050-Process-Read-Indexed.
*>
*>  Now do on correct key within WHERE
*>  Sets up key and compare data
*>
     set      KOR-x1 to 1.              *> 1 = only key
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     spaces to WS-Where
     move     1   to J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '="'                  delimited by size
              Posting-Record (K:L)  delimited by size
 *>             Post-Key
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if.
     move     5 to ws-No-Paragraph
*>      /MYSQL SELECT\
*>
*>    Select rows
*>
*>             TABLE=IRSPOSTING-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`IRSPOSTING-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-IRSPOSTING-REC
*>      /MYSQL-END\
*>
     if     WS-MYSQL-Count-Rows = zero
            move 21  to fs-Reply             *> could also be 23 or 14
            move 2 to we-error         *> from irsub4
            go to ba998-Free
     end-if
     move     6 to ws-No-Paragraph
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=IRSPOSTING-REC
           MOVE TP-IRSPOSTING-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-KEY-4
                    HV-POST4-CODE
                    HV-POST4-DAT
                    HV-POST4-DAY
                    HV-POST4-MONTH
                    HV-POST4-YEAR
                    HV-POST4-DR
                    HV-POST4-CR
                    HV-POST4-AMOUNT
                    HV-POST4-LEGEND
                    HV-VAT-AC-DEF4
                    HV-POST4-VAT-SIDE
                    HV-VAT-AMOUNT4

*>      /MYSQL-END\
     end-call
*>
     if       WS-MYSQL-Count-Rows not > zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    move 21 to fs-reply    *> from 23
 *>                   move 990 to WE-Error
                    move 2 to WE-Error                 *> as in irsub4
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move spaces to WS-File-Key
                    go to ba998-Free
              else
                    move 21   to fs-reply    *> from 23
 *>                   move 989  to WE-Error
                    move 2 to WE-Error                 *> as in irsub4
                    move zero to SQL-Err
                    move spaces to SQL-Msg
                    move spaces to WS-File-Key
                    go to ba998-Free
              end-if
     end-if                        *> row count zero should show up as a MYSQL error ?
     perform  bb100-UnloadHVs      *> transfer/move HV vars to ws-Record layout
     move     HV-KEY-4 to ws-temp-ed.
     move    ws-temp-ed to WS-File-Key.
*>
     move     zero to FS-Reply WE-Error.
     go       to ba998-Free.
*>
 ba060-Process-Start.
*>
*> THIS MINOR CHANGES FOR irsub4 START/READ NEXT using
*>   read-indexed = or not < or > or <  ???
*>
*>  Check for Param error 1st on start
*>
     if       access-type < 5 or > 8                   *> not using not < or not >
              move 99 to FS-Reply
              move 997 to WE-Error                     *> Invalid calling parameter settings     997
              go to ba999-end
     end-if
*>
*>  First clear any active cursors
*>
     if       Cursor-Active
              perform ba998-Free.
*>
*>  Now do Start on correct key before read-next  within WHERE
*>  Set up MOST-relation for condition test and key
*>
     set      KOR-x1 to 1.
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     spaces to MOST-Relation.
     move     1   to J.
     evaluate Access-Type     *>  x shows used in irs.
              when  5                           *>x fn-equal-to [also in sub4]
                    move "=  " to MOST-Relation
              when  6                           *> fn-less-than  [NOT in sub4]
                    move "<  " to MOST-Relation
              when  7                           *>x fn-greater-than [also in sub4]
                    move ">  " to MOST-Relation
              when  8                           *>x fn-not-less-than [also in sub4]
                    move ">= " to MOST-Relation
              when  9                           *> fn-not-greater-than [ not currently used in ACAS ]
                    move "<= " to MOST-Relation
     end-evaluate
*>
     move     spaces to WS-Where
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              MOST-relation         delimited by space
              '"'                   delimited by size
              Posting-Record (K:L)       delimited by size
              '"'                   delimited by size
              ' ORDER BY '          delimited by size
              "`"                   delimited by size
              keyname (KOR-x1)      delimited by space
              "`"                   delimited by size
                ' ASC  '            delimited by size
                             into WS-Where
                             with pointer J
     end-string
     move     WS-Where (1:J)  to WS-Log-Where.    *>  For test logging
     move     Posting-Record (K:L) to WS-File-Key.
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
*>
     move     8 to ws-No-Paragraph
*>      /MYSQL SELECT\
*>
*>    Select rows
*>
*>             TABLE=IRSPOSTING-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`IRSPOSTING-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-IRSPOSTING-REC
*>      /MYSQL-END\
*>
     if       WS-MYSQL-Count-Rows not zero
              set Cursor-Active to true
     end-if
*>
     if       WS-MYSQL-Count-Rows = zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move 21 to fs-reply                  *> this may need changing for val in WE-Error!!
                    move 2 to we-error                     *> from irsub4
                    go to ba999-End
              end-if
     else
              move  zero to FS-Reply WE-Error
              move     WS-MYSQL-Count-Rows to WS-Temp-Ed
              string   MOST-relation
                       Posting-Record (K:L)
                       " got =" delimited by size
                       WS-Temp-ED delimited by size
                       " recs"
                        into WS-File-Key
              end-string
     end-if
     perform  ba999-end.                                 *> Log it
*>
*> Here we need FETCH as SELECT has been issued & cursor active
*>
     go to ba041-Reread.
*>
*> Changed to do start then read next
*>   As per irsub4 operations
*>
 ba070-Process-Write.
     perform  bb000-HV-Load.                       *>  move Posting-Record fields to HV fields
     move     Post-Key to WS-File-Key.
     move     zero to FS-Reply WE-Error SQL-State.
     move     spaces to SQL-Msg
     move     zero to SQL-Err
     move     10 to ws-No-Paragraph.
     perform  bb200-Insert.
     if       WS-MYSQL-COUNT-ROWS not = 1
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
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
     end-if.
     go       to ba999-End.       *> and log it
*>
 ba080-Process-Delete.
*>
     set      KOR-x1 to 1.
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     spaces to WS-Where
     move     1   to J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '="'                  delimited by size
              Posting-Record (K:L)    delimited by size
 *>             Post-Key
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     Posting-Record (K:L)  to WS-File-Key.
     move     WS-Where (1:J)   to WS-Log-Where.   *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     13 to ws-No-Paragraph.
*>      /MYSQL DELETE\
*>
*>    Delete a row
*>
*>             TABLE=IRSPOSTING-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`IRSPOSTING-REC`"
             " WHERE "
             WS-Where (1:J)
             X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>      /MYSQL-END\
     if       WS-MYSQL-COUNT-ROWS not = 1
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move 99 to fs-reply
                    move 995 to WE-Error
              end-if
              go to ba999-End                        *> and log it
     else
              move spaces to SQL-Msg
              move zero   to SQL-Err
     end-if.
     move     zero to FS-Reply WE-Error.
     go       to ba999-End.
*>
 ba085-Process-Delete-ALL.    *> THIS IS NON STANDARD
*>
*> This is the equivalent of :
*>           EXEC SQL
*>              DELETE
*>              FROM IRSPOSTING-REC
*>           END-EXEC.
*>
*>  That creates the follwoing code from dbpre
*>
*>   MOVE LOW-VALUES TO SQLCA-STATEMENT
*>   STRING
*>     "DELETE " DELIMITED SIZE
*>     "FROM " DELIMITED SIZE
*>     "IRSPOSTING-REC " DELIMITED SIZE
*>      INTO SQLCA-STATEMENT
*>   END-STRING
*>   CALL "MySQL_query" USING SQLCA-STATEMENT
*>   END-CALL
*>
*> So if this does not work it will be changed.
*>
     add      1  to Post-Key.         *> as its the last posting
*>
     set      KOR-x1 to 1
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     spaces to WS-Where
     move     1   to J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '<"'                  delimited by size
              Posting-Record (K:L)    delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     spaces to WS-File-Key
     string   "Deleting back from " delimited by size
               Post-Key             delimited by size
                      into WS-File-Key
     end-string                                   *> for logging
     move     WS-Where (1:J)   to WS-Log-Where.   *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     15 to ws-No-Paragraph.
*>      /MYSQL DELETE\
*>
*>    Delete a row
*>
*>             TABLE=IRSPOSTING-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`IRSPOSTING-REC`"
             " WHERE "
             WS-Where (1:J)
             X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>      /MYSQL-END\
     if       WS-MYSQL-COUNT-ROWS not > zero    *> Changed for delete-ALL
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move 99 to fs-reply
                    move 995 to WE-Error
              end-if
              go to ba999-End
     else      *> of course there could be no data in table
              move spaces to SQL-Msg
              move zero   to SQL-Err
     end-if.
     move     zero to FS-Reply WE-Error.
     go       to ba999-End.
*>
 ba090-Process-Rewrite.
*>
     perform  bb000-HV-Load.       *> Load up the HV fields from table record in WS
     move     Post-Key to WS-File-Key.
     move     17 to ws-No-Paragraph.
     set      KOR-x1 to 1            *> 1 = Primary
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     spaces to WS-Where
     move     1   to J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '="'                  delimited by size
              Posting-Record (K:L)       delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     perform  bb300-Update.
*>
     if       Testing-2
              display Display-Message-1 with erase eos
     end-if
*>
     if       WS-MYSQL-COUNT-ROWS not = 1
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
                    move 994 to WE-Error
              end-if
*>
              if       Testing-1
                       perform Ca-Process-Logs
              end-if
              go to ba092-Finish-1    *> ba999-exit  [ error ]
     end-if
     move     zero   to FS-Reply WE-Error.
     move     zero   to SQL-Err.
     move     spaces to SQL-Msg.
     perform  ba999-End           *>  for logging
     go       to ba092-Finish-1.  *> was ba999-exit.[normal finish]
*>
 ba092-Finish-1.
 ba093-Finish-2.
     go       to ba999-Exit.
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
*>             TABLE=IRSPOSTING-REC
           MOVE TP-IRSPOSTING-REC TO WS-MYSQL-RESULT
           CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
*>      /MYSQL-END\
     set      Cursor-Not-Active to true.
*>
 ba999-end.
*>  Any Clean ups before quiting    move data record ?????  do so at the start as well ??????
*>
     if       Testing-1
              perform Ca-Process-Logs
     end-if.
*>
 ba999-exit.
     exit program.
*>
 bb000-HV-Load      Section.
*>*************************
*>
*>  Load the Host variables with data from the passed record
*>
*> This Method loads the Host Variables for the Base table with
*> the data passed in the data-buffer.
*>
     initialize TD-IRSPOSTING-REC.
     move     Post-Key      to HV-KEY-4.
     move     Post-Code     to HV-POST4-CODE.
     move     Post-Date     to HV-POST4-DAT.
     move     Post-DR       to HV-POST4-DR.
     move     Post-CR       to HV-POST4-CR.
     move     Post-Amount   to HV-POST4-AMOUNT.
     move     Post-Legend   to HV-POST4-LEGEND.
     move     Vat-AC-Def    to HV-VAT-AC-DEF4.
     move     Post-Vat-Side to HV-POST4-VAT-SIDE.
     move     Vat-Amount    to HV-VAT-AMOUNT4.
*>
*> These added after new columns             created 31/12/16  - inhouse mysql & mariadb
*>  and yes they all should be numeric as a date is present
*>   but JIC (just in case).
*>
     if       Post-Date (1:2) numeric
              move     Post-Date (1:2) to HV-POST4-DAY.
     if       Post-Date (4:2) numeric
              move     Post-Date (4:2) to HV-POST4-MONTH.
     if       Post-Date (7:2) numeric
              move     Post-Date (7:2) to HV-POST4-YEAR.
*>
*> Loading HVs implies a non-Fetch action. RGs are handled separately for
*> all such actions so they must not be loaded here.
*>
 bb000-Exit.
     exit section.
*>
 bb100-UnloadHVs    Section.
*>*************************
*>
*>  Load the data buffer in the interface with data from the host variables.
*> (init moved lower)
*>
*> NULL fields must not be returned in the buffer. SQL filters each column to
*>  ensure it has a proper value.  This saves using indicator variables.
*>
     initialize Posting-Record.
*>
     move     HV-KEY-4            to Post-Key.
     move     HV-POST4-CODE       to Post-Code.
     move     HV-POST4-DAT        to Post-Date.
     move     HV-POST4-DR         to Post-DR.
     move     HV-POST4-CR         to Post-CR.
     move     HV-POST4-AMOUNT     to Post-Amount.
     move     HV-POST4-LEGEND     to Post-Legend.
     move     HV-VAT-AC-DEF4      to Vat-AC-Def.
     move     HV-POST4-VAT-SIDE   to Post-Vat-Side.
     move     HV-VAT-AMOUNT4      to Vat-Amount.
*>
*>  We do not need to unload POST4- DAY, MONTH or YEAR as only used
*>   in select statements instead of a sort.
*>
 bb100-Exit.
     exit section.
*>
 bb200-Insert Section.
*>*******************
*>
*>  /MYSQL INSERT\
*>
*>    Insert a row
*>
*>         TABLE=IRSPOSTING-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'INSERT INTO '
                    '`IRSPOSTING-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`KEY-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-KEY-4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-CODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-CODE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-DAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-DAY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-DAY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-MONTH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-MONTH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-YEAR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-YEAR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-DR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-DR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-CR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-CR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-AMOUNT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-AMOUNT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:02)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-LEGEND`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-LEGEND,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-AC-DEF4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-AC-DEF4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-VAT-SIDE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-VAT-SIDE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-AMOUNT4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-AMOUNT4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:02)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
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
*>      TABLE=IRSPOSTING-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'UPDATE '
                    '`IRSPOSTING-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`KEY-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-KEY-4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-CODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-CODE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-DAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-DAY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-DAY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-MONTH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-MONTH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-YEAR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-YEAR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-DR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-DR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-CR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-CR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-AMOUNT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POST4-AMOUNT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:02)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-LEGEND`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-LEGEND,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-AC-DEF4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-AC-DEF4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST4-VAT-SIDE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST4-VAT-SIDE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-AMOUNT4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-AMOUNT4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:02)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
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
end program irspostingMT.
