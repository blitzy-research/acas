       >>source free
*>***********************************************
*>                                              *
*>               Sales Payments                 *
*>             Table RDB Handler                *
*>                                              *
*>***********************************************
*>
 identification division.
 Program-Id.            paymentsMT.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License
*>                      v2.0. Only. See the file COPYING for details.
*>**
*> Remarks.             Sales Payments File RDB Handler using amended JC preSQL.
*>                      **********************************************
*>
*>                      This version uses an amended JC pre-Sql processor.
*>                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>                      THIS module handles two tables - primary and a secondary one
*>                      The primary (PLPAY-REC) has all columns that directly link to
*>                      Cobol file data that does not contain an occurs and
*>                      PLPAY-RECrg01 for up to 9 rows for those both using the
*>                      same key for the search but with an additional field holding
*>                      the table occurances value ( LEVEL-J ).
*>
*>                      THIS module will be a modal for the Invoicing tables.
*>
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>
*>                      This modules does all file handling using RDB and is called
*>                      from the ACAS
*>                      Sales Payments file handler acas032
*>                      which in turn is called
*>                      from each ACAS application module that requires file/RDB data handling.
*>
*>                      If RDBMS (Relational Database Management Systems) is in use it will be
*>                      called by the specific module to handle similar processing as a Cobol
*>                      flat file and will pass the equivalent
*>                      RDB (Relational Database) row as a Cobol file record (01 level) moving
*>                      row by row to the correct Cobol flat file fields as required.
*>
*>                      RDB DAL (Data Access Layer) modules are individually modified to handle:
*>                      MS SQL server, Mysql, DB2, Postgres and Oracle as available and tested.
*>                      These are contained in separate directories for each RDB, e.g.
*>                       'MSSQL' (MS SQL Server), 'Mysql', 'DB2', 'Postgres'. 'Oracle'.
*>                       You need to compile from the correct directory for the specific
*>                       RDB you will use and have installed along with all of the development
*>                       libraries and include files etc using the correct pre-compiler tool
*>                       to process the 'EXEC SQL' code converting to Cobol calls etc.
*>                       see the RDB specific ACAS notes.
*>
*>                      For specific SQL servers supported, the pre-compiler system is included
*>                       where ever possible but for some, copyright reasons may prevent
*>                       inclusion. In some cases for one specific RDB more than one precompiler
*>                       is used as an experiment to help find the ideal one to use.
*>
*>                      In addition:
*>                        If the system has been set up to (see the System File set up via the
*>                        main menu module for each sub system), it will also process BOTH flat
*>                        file  AND the correct rdb tables,
*>
*>                        it will write/delete/update etc to both but read from 1=Flat and be
*>                        overwritten by the rdb access if data is present.
*>                       This will help in transferring the Cobol flat files to rdb tables.
*>
*>                      If you wish to convert a running ACAS system over from Flat files
*>                      to RDBMS see below.
*>
*>                      Depending on the RDB you wish to use there is
*>                      also, included LMs (Load Modules) to convert each ISAM
*>                      (Indexed Sequential) file to the rdb database tables if you wish to
*>                      convert the system in one hit, without using the Duplicate file/RDB
*>                      processing procedures. These will also need to be compiled from the
*>                      specific LM directory that contains the rdb DAL modules.
*>                      These will be very RDB specific.
*>
*>**
*>  File Handling:
*>     Uses the Global Error / Access logging file within the acas0nn module.
*>**
*> Called by Modules:
*>                      acas032 - Sales Payments Cobol Handler.
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
*> 04/08/16 vbc - .01 Removed file action logging to sep. module ditto acas011.
*> 18/07/16 vbc - .02 Insert call for SQL error msg where missing and move
*>                    spaces / zero to SQL-Msg| Err and other little fixes/cleanups.
*>                    Remap all changes to the .scb source file.
*> 20/07/16 vbc - .03 Close logger if testing-1 set on table close.
*>                    branch to 999-end instead of 998-free when EOF on read next.
*>                    Seems to auto release if end of cursor data reached
*>                    and causes an abort ??
*> 24/07/16 vbc -     Taken from the stockMT sources with same versioning.
*> 30/07/16 vbc - .04 Change Open and Close to also show table name in operation.
*> 31/07/16 vbc - .05 Moved mv spaces/zero in Write to before insert.
*>                    Remove fhlogger file close in Process-Close.
*>                    Forgot error 989 so commented.
*> 10/01/17 vbc - .06 Taken from salesMT.
*>                    Updated to support rg table needs for all Fetch, Update,
*>                    Insert & Delete functions.
*> 11/01/17 vbc -     Added 800 series WE-Error messages for RG processing
*>                    for use with logging only.
*> 01/03/18 vbc - .11 Renamed error messages to SM901, SM004 as needed.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              WS-Pay-Record = Contents of data record to be written/read
*>                          File-Access = File-Function as needed.
*>                                        Access-Type   as needed.
*>                          File-Defs (File-Definitions) = Paths set up.
*>
*>    On Exit:          Linkage contains:
*>    *******               Record = containing a read data record or table row for both tables.
*>                          Fs-Reply = 0, 99 or other value where
*>                                     0  = Operation completed successfully
*>                                     10 = End of (Cobol) File returned to calling module only.
*>                                     21 = Invalid key on START OR key not found
*>                                     22 - Attempt to duplicate a key value.
*>                                     23 = Key not found.     from read indexed
*>                                     99 = Indicates an error see WE-Error, SQL-ERR/MSG for more info
*>                          WE-Error   0    = Operation completed successfully
*>
*>                                     999  = Not used here - Yet.
*>                                     998* = File-Key-No Out Of Range not 1, 2 or 3.
*>                                     997* = Access-Type wrong (< 5 or > 8)
*>                                     996* = File Delete key out of range (not = 1 or 2)
*>                                     995* = During Delete SQLSTATE not '00000' investigate using MSG-Err/Msg
*>                                            or row count not > 0
*>                                     994* = During Rewrite,                     ^^ see above ^^
*>                                     992* = Invalid Function requested in File-Function
*>                                     990* = Unknown and unexpected error, again ^^ see above ^^
*>                                     989* = Unexpected error on Read-Indexed, investigate as above.
*>                                     910* = Table locked > 5 seconds
*>                                     911* = Rdb Error during initializing,
*>                                            possibly can not connect to database
*>                                             Check connect data and
*>                                             see SQL-Err & SQL-MSG
*>                                     901  = File Def Record size not =< than ws record size
*>                                            Module needs ws definition changing to correct size
*>                                            FATAL, Stop using system, fix source code
*>                                            and recompile before using system again.
*>                                     8nn  = Processing on RG Table & rows.
*>                                     890  = Unknown and unexpected error, again ^^ see above on RG processing
*>                                     880  = Unexpected range error in Rg1 secondary key.
*>                                            Report to programming team.
*>                                     Other = any other rdbms errors see specific
*>                                             (Rdbms) manual
*>                          SQL-Err   = Error code from RDBMS is set if above 2 are non zero
*>                          SQL-Msg   = Non space providing more info if SQL-Err non '00000'
*>                                      * = FS-Reply = 99.
*>                          SQL-State = In support of SQL-Err for dup keys etc.
*>
 copy "ACAS-SQLstate-error-list.cob".
*>
*>       During testing a log file will be created containing datetime stamp, task and return codes
*>       for FS-Reply, WE-Error & SQL-State with table used - in this case the Payments File.
*>       WARNING - This file could get large so needs manually deleting after examination.
*>
*>       NOTE that the value in SQL-State is the standard ANSI RDBMS error code to help keep
*>         DAL handler changes to a minimum when reusing code for other RDBs - hopefully
*>
*>        SHOULD THIS BE IN THE DAL ONLY ?  Only for RDB accessing.
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
 77  prog-name           pic x(22)    value "paymentsMT (3.3.00)".
*>
*> JC WS requirements here
*>
 77  ws-Where           pic x(512).
*>
*>  Used within presql generated code
*>
 01  WS-Reply           pic x           value space.
 01  WS-MYSQL-I         PIC S9(4) COMP.
 01  WS-MYSQL-EDIT      PIC -Z(18)9.9(9).
 *>
 *> TESING data
 *>
 01  ws-temp-ed          pic -9(10).
*>
*> The communication area for the MySQL database changed for free/mysql
*>
*>  jc preSQL MySQL stuff ends
*>
*> Metadata on primary and alternate keys...  from Prima DAL for PLPAY-REC
*>
 01  Table-Of-Keynames.
     03  filler         pic x(30) value 'PAY-KEY                       '.
     03  filler         pic x(8)  value '00010009'.  *> offset/length
     03  filler         pic x(3)  value 'STR'.       *> data type
 01  filler redefines table-of-keynames.
     03  keyOfReference occurs 1
                             indexed by KOR-x1.
         05  keyname    pic x(30).
         05  KOR-offset pic 9(4).
         05  KOR-length pic 9(4).
         05  KOR-Type   pic XXX.                    *> Not used currently
*>
*>  Start of RG (Repeat Groups)                        NOT USED - YET.
*> Metadata on Repeating Groups...
*>
 01  RG-Table.
     03  filler  pic x(30) value 'PLPAY-RECrg01'.   *> table name
     03  filler  pic s9(9) comp-5 value 9.          *> Max row count
     03  filler  pic s9(9) comp-5 value zero.       *> current row
*>
 01  filler redefines RG-Table.
     03  RG-Entry          occurs 1
                          indexed by RG-x1.
         05 RG-recname    pic x(30).
         05 RG-maxoccurs  pic s9(9) comp-5.
         05 RG-noloaded   pic s9(9) comp-5.        *> Number loaded.
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
     12 J                    pic s9(4).
     12 K                    pic s9(4).
     12 L                    pic s9(4).
     12 M                    pic s9(4).
 01  WS-Level-J              pic 9.
*>
 01  work-fields.
     03  ws-env-lines    pic 999              value zero.
     03  ws-lines        binary-char unsigned value zero.
     03  ws-22-lines     binary-char unsigned value zero.
     03  ws-23-lines     binary-char unsigned value zero.
     03  ws-98-lines     binary-char unsigned value zero.
     03  ws-99-lines     binary-char unsigned value zero.
*>
 01  Error-Messages.
     03  SM901          pic x(31) value "SM901 Note error and hit return".
*>
*> /MYSQL VAR\
*>       ACASDB
*>       TABLE=PLPAY-REC,HV
*>       TABLE=PLPAY-RECrg01,HV1
 COPY "mysql-variables.cpy".
*>
*>    Definitions for the PLPAY-REC Table
*>
       01  TP-PLPAY-REC                          USAGE POINTER.
       01  TD-PLPAY-REC.
           05  HV-PAY-KEY                        PIC X(9).
           05  HV-PAY-CONT                       PIC X(1).
           05  HV-PAY-DAT                        PIC  9(10) COMP.
           05  HV-PAY-CHEQUE                     PIC  9(10) COMP.
           05  HV-PAY-SORTCODE                   PIC  9(10) COMP.
           05  HV-PAY-ACCOUNT                    PIC  9(10) COMP.
           05  HV-PAY-GROSS                      PIC S9(08)V9(02) COMP.
*>
*>    Definitions for the PLPAY-RECrg01 Table
*>
       01  TP-PLPAY-RECRG01                      USAGE POINTER.
       01  TD-PLPAY-RECRG01.
           05  HV1-PAY-FOLIO                     PIC  9(10) COMP.
           05  HV1-PAY-PERIOD                    PIC  9(03) COMP.
           05  HV1-PAY-VALUE                     PIC S9(10)V9(04) COMP.
           05  HV1-PAY-DEDUCT                    PIC S9(10)V9(04) COMP.
           05  HV1-PAY-INVOICE                   PIC X(10).
           05  HV1-LEVEL-J                       PIC  9(03) COMP.
           05  HV1-PAY-KEY                       PIC X(9).
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
 copy "wspay.cob".
*>
 screen section.
*>=============
*>
 01  Display-Message-1       foreground-color 2.
     03          value "WS-Where="               line 23 col  1.
     03  from WS-Where (1:J)           pic x(69)         col 10.
*>
 01  Display-Message-2       foreground-color 2.
     03      value "SM004 SQL Err No.="           line 4 col  1.
     03  using Ws-Mysql-Error-Number   pic x(4)          col 19.
     03      value " Para="                              col 23.
     03  using WS-No-Paragraph         pic 9(3)          col 29.
     03      value " SQL Cmd="                           col 32.
     03  using Ws-Mysql-Command        pic x(199)        col 41.
     03      value "SQL Err Msg="                 line 7 col  1.
     03  using Ws-Mysql-Error-Message  pic x(67)         col 13.
*>
*>
 PROCEDURE DIVISION   using File-Access
                            ACAS-DAL-Common-data
                            WS-Pay-Record.        *>  Ws record
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
     add      2 to ws-lines giving ws-99-lines.
     add      1 to ws-lines giving ws-98-lines.
*>
 ba010-Initialise.
*>
     move     zero   to SQL-State.

*>                        We-Error
*>                        Fs-Reply.
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
              go to ba085-Process-Delete-All
        when  7
              go to ba090-Process-Rewrite
        when  8
              go to ba080-Process-Delete
        when  9
              go to ba060-Process-Start
        when  other                          *> 6 is spare / unused
              go to ba100-Bad-Function
     end-evaluate.
*>
 ba020-Process-Open.             *> dry tested - no rg01 requirements.
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
     move    "OPEN PAYMENTS" to WS-File-Key
     set     Cursor-Not-Active to true
     go      to ba999-end.
*>
 ba030-Process-Close.             *> dry tested - no rg01 requirements.
     if      Cursor-Active
             perform ba998-Free.
*>
     move     2 to ws-No-Paragraph.
     move    "CLOSE PAYMENTS" to WS-File-Key.
*>  /MYSQL CLOSE\
*>
*>    Close the Database
*>
           PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
*>  /MYSQL-END\
     go      to ba999-end.
*>
 ba040-Process-Read-Next.             *> dry tested - Has rg01 requirements.
*>
*>   Here a SELECT first then fetch if no cursor active using lowest
*>    possible key of "000000000"
*>           [ PAY-KEY ]
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
                       " >= "                 delimited by size
                       '"000000000"'             delimited by size
                       ' ORDER BY '          delimited by size
                       "`"                   delimited by size
                       keyname (KOR-x1)      delimited by space
                       "`"                   delimited by size
                         ' ASC'              delimited by size
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
*>                    TABLE=PLPAY-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PLPAY-REC`"
             " WHERE "
             ws-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PLPAY-REC
*>               /MYSQL-END\
           move    "000000000" to WS-File-Key
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
                       move 10 to WE-Error        *> should be 0 'JIC' likewise the others
                       move    "No Data" to WS-File-Key
                       go to ba999-End       *> can clear the dup code after testing
              end-if                         *> We have data
              set      Cursor-Active to true
              move     WS-MYSQL-Count-Rows to WS-Temp-Ed
              string   "> 0 got cnt=" delimited by size
                       WS-Temp-ED delimited by size
                       " recs for PAY-RECORD Table"
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
     move     zero to return-code.
*>
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=PLPAY-REC
           MOVE TP-PLPAY-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-PAY-KEY
                    HV-PAY-CONT
                    HV-PAY-DAT
                    HV-PAY-CHEQUE
                    HV-PAY-SORTCODE
                    HV-PAY-ACCOUNT
                    HV-PAY-GROSS

*>      /MYSQL-END\
     end-call
*>
     if       return-code = -1     *> no more data so free cursor & return
              move 10 to fs-Reply
                         WE-Error      *> should be 0 likewise the others
              move    "EOF" to WS-File-Key
              set Cursor-Not-Active to true
              go to ba999-End
     end-if
*>
     if       WS-MYSQL-Count-Rows = zero   *> no data but should not happen here
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err   *> Not really needed but help for testing
                    move WS-MYSQL-Error-Message to SQL-Msg   *>  ditto
                    initialize WS-Pay-Record with filler
                   move    "EOF2" to WS-File-Key
              end-if
              move 10 to fs-reply                  *> EOF equivilent !!
              move 10 to WE-Error
              set Cursor-Not-Active to true
              go to ba999-End
     end-if.
*>
     if       fs-reply = 10                 *> should not happen as tested prior
              set Cursor-Not-Active to true
              move    "EOF3" to WS-File-Key
              go to ba999-End
     end-if.
*>
     perform  bb100-UnloadHVs.       *> transfer/move HV vars to Record layout
     perform  ba999-End.                                  *> log it
*>
*>  Now process Rg rows (1 to 9) - [bc050 used for both read-next and read-indexed]
*>
     perform  bc050-Process-Read-Indexed  thru bc059-Exit.
*>
     move     HV-PAY-KEY to WS-File-Key.
     move     zero to fs-reply WE-Error.
     go       to ba999-exit.
*>
 ba050-Process-Read-Indexed.             *> dry tested - Has rg01 requirements.
*>
*>  Now do on correct key within WHERE
*>  Sets up key and compare data
*>
     set      KOR-x1 to 1.      *> 1 = Primary
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     spaces to WS-Where
     move     1   to J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '="'                  delimited by size
              WS-Pay-Record (K:L)       delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     5 to ws-No-Paragraph
*>      /MYSQL SELECT\
*>
*>    Select rows
*>
*>             TABLE=PLPAY-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PLPAY-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PLPAY-REC
*>      /MYSQL-END\
*>
     if     WS-MYSQL-Count-Rows = zero
            move 23  to fs-Reply             *> could also be 21 or 14
            move zero to WE-Error
            go to ba998-Free
     end-if
     move     6 to ws-No-Paragraph
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=PLPAY-REC
           MOVE TP-PLPAY-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-PAY-KEY
                    HV-PAY-CONT
                    HV-PAY-DAT
                    HV-PAY-CHEQUE
                    HV-PAY-SORTCODE
                    HV-PAY-ACCOUNT
                    HV-PAY-GROSS

*>      /MYSQL-END\
     end-call
*>
     if       WS-MYSQL-Count-Rows not > zero
              call     "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    move 990 to WE-Error
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
              else
                    move 989  to WE-Error
                    move zero to SQL-Err
                    move spaces to SQL-Msg
              end-if
              move 23   to fs-reply
              move spaces to WS-File-Key
              go to ba998-Free
     end-if                        *> row count zero should show up as a MYSQL error ?
     perform bb100-UnloadHVs       *> transfer/move HV vars to ws-Record layout
     perform ba999-End.
*>
*>  Now process Rg rows (1 to 9) - [bc050 used for both read-next and read-indexed]
*>
     perform  bc050-Process-Read-Indexed  thru bc059-Exit.
*>
     move     HV-PAY-KEY to WS-File-Key.
     move     zero to FS-Reply WE-Error.
     perform  ba998-Free.                       *> Free cursor
     go       to ba999-Exit.
*>
 ba060-Process-Start.             *> No rg01 requirements & not used in P/L.
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
     evaluate Access-Type
              when  5                           *> fn-equal-to
                    move "=  " to MOST-Relation
              when  6                           *> fn-less-than
                    move "<  " to MOST-Relation
              when  7                           *> fn-greater-than
                    move ">  " to MOST-Relation
              when  8                           *> fn-not-less-than
                    move ">= " to MOST-Relation
              when  9                           *>  fn-not-greater-than [ not currently used in ACAS ]
                    move "<= " to MOST-Relation
     end-evaluate
*>
     move     spaces to WS-Where
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              MOST-relation         delimited by space
              '"'                   delimited by size
              WS-Pay-Record (K:L)       delimited by size
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
     move     WS-Pay-Record (K:L) to WS-File-Key
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
*>
     move     8 to ws-No-Paragraph
*>      /MYSQL SELECT\
*>
*>    Select rows
*>
*>             TABLE=PLPAY-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PLPAY-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PLPAY-REC
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
              end-if
              move 21 to fs-reply                  *> this may need changing for val in WE-Error!!
              move zero to WE-Error
     else
              move  zero to FS-Reply WE-Error
              move     WS-MYSQL-Count-Rows to WS-Temp-Ed
              string   MOST-relation
                       WS-Pay-Record (K:L)
                       " got " delimited by size
                       WS-Temp-ED delimited by size
                       " recs"
                        into WS-File-Key
              end-string
     end-if
     go       to ba999-end.
*>
*>  Now a read next will process a Fetch from cursor
*>
 ba070-Process-Write.             *> dry tested - Has rg01 requirements.
     perform  bb000-HV-Load.                       *>  move WS-Pay-Record fields to HV fields
     move     WS-PAY-KEY to WS-File-Key.
     move     zero to FS-Reply WE-Error SQL-State
     move     spaces to SQL-Msg
     move     zero to SQL-Err
     move     10 to ws-No-Paragraph.
     perform  bb200-Insert.
     if       WS-MYSQL-COUNT-ROWS not = 1
              call "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    if    SQL-Err (1:4) = "1062"
                                     or = "1022"   *> Dup key (rec already present)
                        or Sql-State = "23000"  *> Dup key (rec already present)
                          move 22 to fs-reply
                    end-if
              end-if
     end-if
     perform  ba999-End.
*>
*>  Now process Rg rows
*>
     perform  bc070-Process-Write thru bc070-Exit.
     go       to ba999-Exit.
*>
 ba080-Process-Delete.             *> dry tested - Has rg01 requirements.
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
              WS-Pay-Record (K:L)       delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-Pay-Record (K:L)  to WS-File-Key.
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     13 to ws-No-Paragraph.
*>      /MYSQL DELETE\
*>
*>    Delete a row
*>
*>             TABLE=PLPAY-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`PLPAY-REC`"
             " WHERE "
             WS-Where (1:J)
             X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>      /MYSQL-END\
     if       WS-MYSQL-COUNT-ROWS not = 1
              call "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
              end-if
              move 99 to fs-reply
              move 995 to WE-Error
              go to ba999-End
     else
              move spaces to SQL-Msg
              move zero   to SQL-Err
     end-if.
     perform  ba999-End.
*>
*>  Now process Rg rows
*>
     perform  bc080-Process-Delete thru bc080-Exit.
*>
     move     zero to FS-Reply WE-Error.
     go       to ba999-Exit.
*>
 ba085-Process-Delete-ALL.    *> THIS IS NON STANDARD
*>
*> This is the equivalent of :
*>           EXEC SQL
*>              DELETE
*>              FROM PLPAY-REC
*>           END-EXEC.
*>
*>  That creates the follwoing code from dbpre
*>
*>   MOVE LOW-VALUES TO SQLCA-STATEMENT
*>   STRING
*>     "DELETE " DELIMITED BY SIZE
*>     "FROM " DELIMITED BY SIZE
*>     "PLPAY-REC " DELIMITED BY SIZE
*>   INTO SQLCA-STATEMENT
*>   END-STRING
*>     CALL "MySQL_query" USING SQLCA-STATEMENT
*>   END-CALL
*>
*> So if this does not work it will be changed.
*>
     move     high-values  to WS-Pay-Supl-Key.
     move     99           to WS-Pay-Nos.
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
              WS-Pay-Record (K:L)    delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     spaces to WS-File-Key
     string   "Deleting back from " delimited by size
               WS-Pay-Key             delimited by size
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
*>             TABLE=PLPAY-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`PLPAY-REC`"
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
              end-if
              move 99 to fs-reply
              move 995 to WE-Error
              go to ba999-End
     else      *> of course there could be no data in table
              move spaces to SQL-Msg
              move zero   to SQL-Err
     end-if.
     move     zero to FS-Reply WE-Error.
     perform  ba999-End.
*>
*> Process RG data
*>
     perform  bc085-Process-Delete-ALL thru bc085-Exit.
     go       to ba999-Exit.
*>
 ba090-Process-Rewrite.             *> dry tested - Has rg01 requirements.
*>
     perform  bb000-HV-Load.       *> Load up the HV fields from table record in WS
     move     WS-PAY-KEY to WS-File-Key.
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
              WS-Pay-Record (K:L)       delimited by size
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
              end-if
              move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
              move 994 to WE-Error
              go to ba999-End
     end-if
     move     zero   to FS-Reply WE-Error.
     move     zero   to SQL-Err.
     move     spaces to SQL-Msg.
     perform  ba999-End.
*>
*>  Now process Rg rows
*>
     perform  bc070-Process-Write thru bc070-Exit.    *> does write & rewrite
     go       to ba999-Exit.
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
*>             TABLE=PLPAY-REC
           MOVE TP-PLPAY-REC TO WS-MYSQL-RESULT
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
     initialize TD-PLPAY-REC.
     move     WS-Pay-Key          to HV-PAY-KEY.
     move     WS-Pay-Cont         to HV-PAY-CONT.
     move     WS-Pay-Date         to HV-PAY-DAT.
     move     WS-Pay-Cheque       to HV-PAY-CHEQUE.
     move     WS-Pay-SortCode     to HV-PAY-SORTCODE.
     move     WS-Pay-Account      to HV-PAY-ACCOUNT.
     move     WS-Pay-Gross        to HV-PAY-GROSS.
*>
 bb000-Exit.
     exit section.
*>
 bb100-UnloadHVs    Section.
*>*************************
*>
*>  Load the data buffer in the interface with data from the host variables.
*>
     initialize WS-Pay-Record.
     move     HV-PAY-KEY          to WS-Pay-Key.
     move     HV-PAY-CONT         to WS-Pay-Cont
     move     HV-PAY-DAT          to WS-Pay-Date
     move     HV-PAY-CHEQUE       to WS-Pay-Cheque
     move     HV-PAY-SORTCODE     to WS-Pay-SortCode
     move     HV-PAY-ACCOUNT      to WS-Pay-Account
     move     HV-PAY-GROSS        to WS-Pay-Gross.
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
*>         TABLE=PLPAY-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'INSERT INTO '
                    '`PLPAY-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PAY-KEY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-CONT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PAY-CONT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-CHEQUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-CHEQUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-SORTCODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-SORTCODE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-ACCOUNT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-ACCOUNT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-GROSS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-GROSS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
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
*>      TABLE=PLPAY-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'UPDATE '
                    '`PLPAY-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PAY-KEY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-CONT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PAY-CONT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-CHEQUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-CHEQUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-SORTCODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-SORTCODE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-ACCOUNT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-ACCOUNT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-GROSS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAY-GROSS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
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
 bc000-RG-Process section.
*>***********************
*>
*> This section contains mirror processes in ba000 section that act
*> in support of paragraph based process to only deal with the
*> RG ( Repeat Group ) segments of data.
*>
*>  Like ba000 processes they handle one action at a time and do not
*>  do multiple commands or row at once.  This may come later but only
*>   on a as needed basis.
*>
*>  So, bc050 processes the RG table for the held key obtained in
*>  ba040 & ba050.  Same applies to Rewrite, Write & Delete.
*>
*>   This form will be used to process the invoice files tables for
*>    both Sales & Purchase Ledgers.
*>
*>  Note that ws-No-Paragraph start at 51 for RG processing.
*>  Each bc para must end with a bc0n0-Exit
*>
 bc050-Process-Read-Indexed.    *> Dry chk complete.
*>
*>  This routine is called by for both Read-Next and Read-Indexed.
*>
*>    But first save the pointers [and we will restore at end].
*>
     move     WS-Mysql-Result     to WS-Mysql-Save-Result.     *> primary Tbl
     move     WS-Mysql-Count-Rows to WS-Mysql-Save-Count-Rows.
     move     zero to WS-Mysql-Count-Rows.
*>
*>  Use the Key for the primary table to get the RGs, up to 9.
*>
     set      KOR-x1 to 1.                    *> 1 = Primary
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
     move     spaces to WS-Where
     move     1   to J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '="'                  delimited by size
              WS-Pay-Record (K:L)    delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string.
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     51 to ws-No-Paragraph.
*>      /MYSQL SELECT\
*>
*>    Select rows
*>
*>             TABLE=PLPAY-RECrg01
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PLPAY-RECrg01`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PLPAY-RECRG01
*>      /MYSQL-END\
*>
*> Test for no data but this should not happen - Bug in code somewhere
*>  when inserting it. So we will do a log report for analysis.
*>
     if       WS-MYSQL-Count-Rows = zero    *> This should not happen as have to be > 0
              call    "MySQL_errno" using WS-MYSQL-Error-Number
              call    "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move    WS-MYSQL-SqlState   to SQL-State
              if      WS-MYSQL-Error-Number  not = "0  "    *> set non '0' if no rows ?
                      move WS-MYSQL-Error-Number to SQL-Err
                      call "MySQL_error" using WS-MYSQL-Error-Message
                      move WS-MYSQL-Error-Message to SQL-Msg
              end-if
              move    23  to fs-reply
              move    890 to WE-Error
              move    spaces to WS-File-Key
              string  "No RG1 Data for "
                      WS-Pay-Record (K:L)
                        into WS-File-Key
              end-string
              go      to bc058-Restore-Pointers  *> do ba999-end at end
     end-if
*>
     move     WS-MYSQL-Count-Rows to WS-Temp-Ed.
     string   "RG > 0 got cnt=" delimited by size
              WS-Temp-ED delimited by size
                 " recs, KEY="
              WS-Pay-Record (K:L)
                        into WS-File-Key
     end-string.
     perform ba999-End.                         *> log it & continue
*>
 bc051-Fetch-RG1.
*>
*>  Now get the data from RG table/s.
*>
     move     52 to ws-No-Paragraph
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=PLPAY-RECrg01
           MOVE TP-PLPAY-RECRG01 TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV1-PAY-FOLIO
                    HV1-PAY-PERIOD
                    HV1-PAY-VALUE
                    HV1-PAY-DEDUCT
                    HV1-PAY-INVOICE
                    HV1-LEVEL-J
                    HV1-PAY-KEY

*>      /MYSQL-END\
     end-call
*>
     if       WS-MYSQL-Count-Rows  > zero
              perform  bc100-UnloadHVs-rg1       *> transfer/move HV vars to ws-Record layout
              go to bc051-Fetch-RG1
     end-if
*>
*> No more rows for key
*>
     move     HV-PAY-KEY to WS-File-Key.
     move     zero to FS-Reply WE-Error.
     go       to bc058-Restore-Pointers.
*>
 bc058-Restore-Pointers.
*>
*> Restore the Primary table pointer & row count.
*>
     move     WS-Mysql-Save-Result to WS-Mysql-Result.     *> primary Tbl
     move     WS-Mysql-Save-Count-Rows to WS-Mysql-Count-Rows.
     perform  ba999-End.
*>
 bc059-Exit.  Exit.
*>
 bc070-Process-Write.
*>
*> Used for both ba070-Process-Write and ba090-Process-Rewrite
*>
     perform  varying  M from 1 by 1 until M > 9
              if       WS-Pay-Folio (M) = zeros
                  and  WS-Pay-Value (M) = zeros
                       exit perform cycle
              end-if
              perform  bc000-HV-Load-rg1               *>  move rg1 WS-Pay-Record (M) fields to HV fields
              move     M to WS-Level-J
              move     spaces to WS-File-Key
              string   WS-PAY-KEY   delimited by size
                       " RG = "       delimited by size
                       WS-Level-J   delimited by size
                             into WS-File-Key
              end-string
              move     zero to FS-Reply WE-Error
              move     spaces to SQL-Msg SQL-State
              move     zero to SQL-Err
              move     53  to ws-No-Paragraph
              if       fn-Write
                       perform  bc200-Insert-rg1
              else                                      *> fn-Re-write
                       perform  bc300-Update-rg1
              end-if
              if       WS-MYSQL-COUNT-ROWS not = 1
                       call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                       move  WS-MYSQL-SqlState   to SQL-State
                       if    Sql-State = "23000"
                             perform bc300-Update-rg1
                       end-if
                       if      WS-MYSQL-COUNT-ROWS not = 1
                               call  "MySQL_errno" using WS-MYSQL-Error-Number
                               call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                               move  WS-MYSQL-SqlState   to SQL-State
                               move  99 to fs-reply                  *> this may need changing for val in WE-Error!!
                               if    WS-MYSQL-Error-Number  not = "0  "
                                  or Sql-State = "23000"      *> Dup key (rec already present)
                                     call "MySQL_error" using Ws-Mysql-Error-Message
                                     move WS-MYSQL-Error-Number  to SQL-Err
                                     move WS-MYSQL-Error-Message to SQL-Msg
                                     if   Sql-State = "23000"      *> Dup key (rec already present)
                                       or SQL-Err (1:4) = "1062"
                                       or               = "1022"
                                          move 22 to fs-reply
                                     else
                                          move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
                                     end-if
                               end-if
                               move    spaces to WS-File-Key
                               move    M to WS-Temp-Ed
                               string  "Cant Re|WriteRG1 Data on "
                                       WS-Pay-Record (K:L)
                                       " RG="
                                       WS-Temp-Ed
                                           into WS-File-Key
                               end-string
                               perform ba999-End
                               exit perform cycle
                      end-if
              end-if
              perform ba999-End
     end-perform.
*>
 bc070-Exit.  Exit.
*>
 bc080-Process-Delete.
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
              WS-Pay-Record (K:L)       delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-Pay-Record (K:L)  to WS-File-Key.
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     54 to ws-No-Paragraph.           *> Delete all rows (9<=) for key
*>      /MYSQL DELETE\
*>
*>    Delete a row
*>
*>             TABLE=PLPAY-RECrg01
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`PLPAY-RECrg01`"
             " WHERE "
             WS-Where (1:J)
             X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>      /MYSQL-END\
*>
*>  We could have from 1 to 9 so this report is moot.
*>
     if       WS-MYSQL-COUNT-ROWS not > zero
              call "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
              end-if
              move spaces to WS-File-Key
              move WS-MYSQL-COUNT-ROWS to WS-Temp-Ed
              string "Delete for "
                     WS-Pay-Record (K:L)
                     " only found (rg01) "
                     WS-Temp-ED (7:4)
                     " Rows"
                          into WS-File-Key
              end-string
              go to ba999-End
     else
              move spaces to SQL-Msg SQL-State
              move zero   to SQL-Err
     end-if.
     move     zero to FS-Reply WE-Error.
     perform  ba999-End.
*>
 bc080-Exit.  Exit.
*>
 bc085-Process-Delete-ALL.    *> THIS IS NON STANDARD
*>
*> Processes RG rows - Called by ba085-
*>
*> This is the equivalent of :
*>           EXEC SQL
*>              DELETE
*>              FROM PLPAY-RECrg01
*>           END-EXEC.
*>
*>  That creates the follwoing code from dbpre
*>
*>   MOVE LOW-VALUES TO SQLCA-STATEMENT
*>   STRING
*>     "DELETE " DELIMITED SIZE
*>     "FROM " DELIMITED SIZE
*>     "PLPAY-RECrg01 " DELIMITED SIZE
*>   INTO SQLCA-STATEMENT
*>   END-STRING
*>     CALL "MySQL_query" USING SQLCA-STATEMENT
*>   END-CALL
*>
*> So if this does not work it will be changed.
*>
     move     high-values  to WS-Pay-Supl-Key.
     move     99           to WS-Pay-Nos.
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
              WS-Pay-Record (K:L)    delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     spaces to WS-File-Key
     string   "Deleting back from " delimited by size
               WS-Pay-Key             delimited by size
                      into WS-File-Key
     end-string                                   *> for logging
     move     WS-Where (1:J)   to WS-Log-Where.   *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     55  to ws-No-Paragraph.
*>      /MYSQL DELETE\
*>
*>    Delete a row
*>
*>             TABLE=PLPAY-RECrg01
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`PLPAY-RECrg01`"
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
     perform  ba999-End.
*>
 bc085-Exit.  Exit.
*>
 bc000-HV-Load-rg1 Section.
*>**************************
*>
*>  Load the Host variables with data from the passed record
*>
*> Accommodate Repeating Groups...
*> Now load the RG multi-rows into the 'OCCURS' fields of record.
*>
*> Loading RG table: PLPAY-RECrg01
*>
*> M MUST be set up by caller. where value is 1 thru 9.
*>
     move     WS-Pay-Key         to HV1-PAY-KEY.
     move     M                  to HV1-LEVEL-J.
     move     WS-Pay-Folio   (M) to HV1-PAY-FOLIO.
     move     WS-Pay-Period  (M) to HV1-PAY-PERIOD.
     move     WS-Pay-Value   (M) to HV1-PAY-VALUE.
     move     WS-Pay-Deduct  (M) to HV1-PAY-DEDUCT.
     move     WS-Pay-Invoice (M) to HV1-PAY-INVOICE.
*>
*> End of PLPAY-RECrg01 unload...
*> End of Repeating Group processing...
*>
 bc000-Exit.
     exit section.
*>
 bc100-UnloadHVs-rg1 Section.    *> Dry chk complete.
*>**************************
*>
*>  Load the data buffer in the interface with data from the host variables.
*>
*> Accommodate Repeating Groups...
*> Now unload the RG multi-rows into the 'OCCURS' fields of record.
*>
*> Unloading RG table: PLPAY-RECrg01
*>
     move     HV1-LEVEL-J      to  M.     *>  M = 1 thru 9.
     if       M < 1 or > 9                *> JIC
              move 880 to WE-Error
              move 99  to FS-Reply
              move spaces to SQL-Msg
              move M to ws-temp-ed
              string "2nd key out of Range = "
                     WS-Temp-ED
                        into SQL-Msg
              end-string              *> if neg. we have a serious problem !!
              perform ba999-End
              go to bc100-Exit
     end-if.
*>
     move     HV1-PAY-FOLIO    to  WS-Pay-FOLIO   (M).
     move     HV1-PAY-PERIOD   to  WS-Pay-PERIOD  (M).
     move     HV1-PAY-VALUE    to  WS-Pay-VALUE   (M).
     move     HV1-PAY-DEDUCT   to  WS-Pay-DEDUCT  (M).
     move     HV1-PAY-INVOICE  to  WS-Pay-INVOICE (M).
*>
*> End of PLPAY-RECrg01 unload...
*> End of Repeating Group processing...
*>
 bc100-Exit.
     exit section.
*>
 bc200-Insert-rg1 Section.
*>***********************
*>
*>  /MYSQL INSERT\
*>
*>    Insert a row
*>
*>         TABLE=PLPAY-RECrg01
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'INSERT INTO '
                    '`PLPAY-RECrg01` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-FOLIO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-FOLIO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-PERIOD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-PERIOD
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-VALUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-VALUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:04)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-DEDUCT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-DEDUCT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:04)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV1-PAY-INVOICE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-J`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-LEVEL-J
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV1-PAY-KEY,TRAILING)
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
 bc200-Exit.
     exit section.
*>
 bc300-Update-rg1 Section.
*>***********************
*>
     move     WS-PAY-KEY to WS-File-Key.
     move     56   to ws-No-Paragraph.
     set      KOR-x1 to 1            *> 1 = Primary
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     spaces to WS-Where
     move     1   to J
     move     M   to WS-Level-J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '="'                  delimited by size
              WS-Pay-Record (K:L)       delimited by size
              '"'                   delimited by size
              " AND "               delimited by size
              "`LEVEL-J`="          delimited by size
              WS-Level-J            delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
*>
*>  /MYSQL UPDATE\
*>
*>    Update a row
*>
*>      TABLE=PLPAY-RECrg01
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'UPDATE '
                    '`PLPAY-RECrg01` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-FOLIO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-FOLIO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-PERIOD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-PERIOD
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-VALUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-VALUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:04)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-DEDUCT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-PAY-DEDUCT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING "." INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING WS-MYSQL-EDIT(22:04)
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV1-PAY-INVOICE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-J`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV1-LEVEL-J
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAY-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV1-PAY-KEY,TRAILING)
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
 bc300-Exit.
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
end program paymentsMT.
