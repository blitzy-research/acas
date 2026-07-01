       >>source free
*>***********************************************
*>                                              *
*>                  Stock Audit                 *
*>            File/Table RDB Handler            *
*>                                              *
*>***********************************************
*>
 identification division.
 Program-Id.            auditMT.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 and later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License
*>                      v2.0. Only. See the file COPYING for details.
*>**
*> Remarks.             Stock Audit File RDB Handler using amended JC preSQL.
*>                      ****************************************************
*>
*>                      This version uses an amended JC pre-Sql processor.
*>                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>
*>                      This modules does all file handling using RDB and is called
*>                      from the ACAS
*>                      Analysis  file handler acas010
*>                      which in turn is called
*>                      from each ACAS application module that requires file/RDB data handling.
*>
*>                      If RDBMS (Relational DataBase Management Systems) is in use it will be
*>                      called by the specific module to handle similar processing as a Cobol
*>                      flat file and will pass the equivelent
*>                      RDB (Relational DataBase) row as a Cobol file record (01 level) moving
*>                      row by row to the correct Cobol flat file fields as required.
*>
*>                      RDB DAL (Data Access Layer) modules are individually modified to handle:
*>                      MS SQL server, Mysql, DB2, Postgres and Oracle as available and tested.
*>                      These are contained in seperate directories for each RDB, eg
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
*>                      to RDBMS see below. However it is recommended to use the Duplicate
*>                      processing of files/table as outlined above where no or very low
*>                      data records exist:
*>
*>                      Depending on the RDB you wish to use there is
*>                      also, included LMs (Load Modules) to convert each ISAM
*>                      (Indexed Sequential) file to the rdb database tables if you wish to
*>                      convert the system in one hit, without using the Duplicate file/RDB
*>                      processing procedures. These will also need to be compiled from the
*>                      specific LM directory that contains the rdb DAL modules.
*>                      These will be very RDB specific.
*>
*>                      For a existing running ACAS system using the Load modules AND
*>                      not using the dup processing process as indicated above is the
*>                      recommended way to go.
*>**
*>  File Handling:
*>     Uses the Global Error / Access logging file within the acas0nn module.
*>**
*> Called by Modules:
*>                      acas015 - Analysis  Cobol Handler.
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
*> 04/08/16 vbc - .01 Removed file action logging to sep. module ditto acas010.
*> 18/07/16 vbc - .02 Insert call for SQL error msg where missing and move
*>                    spaces / zero to SQL-Msg| Err and other little fixes/cleanups.
*>                    Remap all changes to the .scb source file.
*> 20/07/16 vbc - .03 Close logger if testing-1 set on table close.
*>                    branch to 999-end instead of 998-free when EOF on read next.
*>                    Seems to auto release if end of cursor data reached
*>                    and causes an abort ??
*> 24/07/16 vbc -     Taken from the analMT sources with same versioning.
*> 30/07/16 vbc - .04 Change Open and Close to also show table name in operation.
*> 31/07/16 vbc - .05 Moved mv spaces/zero in Write to before insert.
*>                    Remove fhlogger file close in Process-Close.
*>                    Forgot error 989 so commented.
*> 18/02/17 vbc - .06 Removed lock / unlock coding.
*> 01/03/18 vbc - .11 Renamed error messages to SM901, SM004 as needed.
*> 20/03/18 vbc - .12 Changed to match glpostingMT for processing eqiv. of open output.
*> 21/03/18 vbc - .13 Added ba085-Delete-All changed from delfolioMT & update to be
*>                    similar codebase to other MTs. Other MTs also need going.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              Stock-Audit-Record = Contents of data record to be written/read
*>                          File-Access = File-Function as needed.
*>                                        Access-Type   as needed.
*>                          File-Defs (File-Definitions) = Paths set up.
*>
*>    On Exit:          Linkage contains:
*>    *******               Record = containing a read data record or table row
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
*>                                     994* = During Rewrite,                     ^^ see above ^^
*>                                     992* = Invalid Function requested in File-Function
*>                                     990* = Unknown and unexpected error, again ^^ see above ^^
*>                                     989* = Unexpected error on Read-Indexed, investigate as above.
*>                                     911* = Rdb Error during initializing,
*>                                            possibly can not connect to database
*>                                             Check connect data and
*>                                             see SQL-Err & SQL-MSG
*>                                     910* = Table locked > 5 seconds
*>                                     901  = File Def Record size not =< than ws record size
*>                                            Module needs ws definition changing to correct size
*>                                            FATAL, Stop using system, fix source code
*>                                            and recompile before using system again.
*>                                     Other = any other rdbms errors see specific
*>                                             (Rdbms) manual
*>                          SQL-Err  = Error code from RDBMS is set if above 2 are non zero
*>                          SQL-Msg  = Non space providing more info if SQL-Err non '00000'
*>                                     * = FS-Reply = 99.
*>
 copy "ACAS-SQLstate-error-list.cob".
*>
*>       During testing a log file will be created containing datetime stamp, task and return codes
*>       for both FS-Reply and WE-Error and table used - in this case the Stock File.
*>       WARNING - This file could get large so needs manually deleting after examination.
*>
*>       NOTE that the value in SQL-Err is the standard ANSI RDBMS error code to help keep
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
 77  prog-name           pic x(17)    value "auditMT (3.3.00)".
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
 01  ws-temp-ed          pic 9(10).
*>
*> The communication area for the MySQL database changed for free/mysql
*>
*>  jc preSQL MySQL stuff ends
*>
*> Metadata on primary and alternate keys...  from Prima DAL for STOCKAUDIT-REC
*>
 01  Table-Of-Keynames.            *> This is not used as table is really accessed as Seq
     03  filler         pic x(30) value 'AUDIT-ID                      '.
     03  filler         pic x(8)  value '00010008'. *> offset/length
     03  filler         pic x(3) value 'STR'. *> data type
 01  filler redefines table-of-keynames.
     03  keyOfReference occurs 1
                             indexed by KOR-x1.
         05  keyname    pic x(30).
         05  KOR-offset pic 9(4).
         05  KOR-length pic 9(4).
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
 01  subscripts usage comp-5.
     12 J                    pic s9(4).
     12 K                    pic s9(4).
     12 L                    pic s9(4).
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
*>       TABLE=STOCKAUDIT-REC,HV
 COPY "mysql-variables.cpy".
*>
*>    Definitions for the STOCKAUDIT-REC Table
*>
       01  TP-STOCKAUDIT-REC                     USAGE POINTER.
       01  TD-STOCKAUDIT-REC.
           05  HV-AUDIT-ID                       PIC  9(10) COMP.
           05  HV-AUDIT-KEY                      PIC X(14).
           05  HV-AUDIT-INVOICE-PO               PIC  9(10) COMP.
           05  HV-AUDIT-CR-FOR-INVOICE           PIC  9(10) COMP.
           05  HV-AUDIT-DESC                     PIC X(32).
           05  HV-AUDIT-PROCESS-DAT              PIC X(10).
           05  HV-AUDIT-REVERSE-TRANSACTION      PIC  9(03) COMP.
           05  HV-AUDIT-TRANSACTION-QTY          PIC S9(07) COMP.
           05  HV-AUDIT-UNIT-COST                PIC S9(06)V9(04) COMP.
           05  HV-AUDIT-STOCK-VALUE-CHANGE       PIC S9(08)V9(02) COMP.
           05  HV-AUDIT-NO                       PIC  9(08) COMP.
*> /MYSQL-END\

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
*> Generated by MOSTGEN from the COPY Book... The record buffer
*> This data buffer was derived from the C:\prim-acas1\SourceSets\PULEDGER.CBF
*> COPY book by MOSTGEN. It is hard coded here so you
*> can see which version of the Source Set was used.
*>
 01  STOCKAUDIT-REC.
     03  WS-Audit-ID               pic 9(8).      *> For RDBMS
     03  Audit-Key.
         05  Audit-Type            pic 9.
         05  Audit-Stock-Key       pic x(13).
     03  Audit-Invoice-PO          pic 9(8).
     03  Audit-Cr-for-Invoice      pic 9(8).
     03  Audit-Desc                pic x(32).
     03  Audit-Process-Date        pic x(10).
     03  Audit-Reverse-Transaction pic 9.          *> T/F (1/0)
     03  Audit-Transaction-Qty     pic s9(6).      *>         comp.
     03  Audit-Unit-Cost           pic s9(6)v9999. *>         comp-3.
     03  Audit-Stock-Value-Change  pic s9(8)v99.   *>         comp-3.  *> can be Negative
     03  Audit-No                  pic 9(5).       *>binary-char unsigned.
*>
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
                            STOCKAUDIT-REC.   *>  Ws record
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
*>     move     zero   to We-Error
*>                        Fs-Reply.
*>
     move     spaces to WS-MYSQL-Error-Message
                        WS-MYSQL-Error-Number
                        WS-Log-Where
                        WS-File-Key
                        SQL-Msg
                        SQL-Err
                        SQL-State.
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
     move    "OPEN AUDIT" to WS-File-Key
     move    zero   to Most-Cursor-Set
     go      to ba999-end.
*>
 ba030-Process-Close.
     if      Cursor-Active
             perform ba998-Free.
*>
     move     2 to ws-No-Paragraph.
     move    "CLOSE AUDIT" to WS-File-Key.
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
*>   Here a SELECT first then fetch if no cursor active using lowest
*>    possible key of zero  (numeric field)
*>           [ Audit-ID ]
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
                       " => "                 delimited by size     *> ????
                       '"00000000"'            delimited by size
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
*>                    TABLE=STOCKAUDIT-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`STOCKAUDIT-REC`"
             " WHERE "
             ws-Where (1:J)      *> WS-Audit-ID > "000" ORDER BY STOCKAUDIT-REC ASC
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-STOCKAUDIT-REC
*>               /MYSQL-END\
           move    "00000000" to WS-File-Key
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
                       if    WS-MYSQL-Error-Number (1:1) not = "0"    *> set non '0' if no rows ?
                             move WS-MYSQL-Error-Number to SQL-Err
                             call "MySQL_error" using WS-MYSQL-Error-Message
                             move WS-MYSQL-Error-Message to SQL-Msg
                       end-if       *> do not really need to do this meaning the above CALL
                       move 10 to fs-reply
                       move 10 to WE-Error
                       move    "No Data" to WS-File-Key
                       go to ba998-Free       *> can clear the dup code after testing
              end-if
              move     1 to Most-Cursor-Set    *> should test if select worked first??????
     end-if.
*>
*>  If here cursor is set, so get the next row
*>
     move     spaces to WS-Log-Where.
     move     4 to ws-No-Paragraph.
     move zero to return-code.
*>
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=STOCKAUDIT-REC
           MOVE TP-STOCKAUDIT-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-AUDIT-ID
                    HV-AUDIT-KEY
                    HV-AUDIT-INVOICE-PO
                    HV-AUDIT-CR-FOR-INVOICE
                    HV-AUDIT-DESC
                    HV-AUDIT-PROCESS-DAT
                    HV-AUDIT-REVERSE-TRANSACTION
                    HV-AUDIT-TRANSACTION-QTY
                    HV-AUDIT-UNIT-COST
                    HV-AUDIT-STOCK-VALUE-CHANGE
                    HV-AUDIT-NO

*>      /MYSQL-END\
     end-call
*>
     if       return-code = -1     *> no more data so free cursor & return
              move 10 to fs-Reply WE-Error
              move    "EOF" to WS-File-Key
              set Cursor-Not-Active to true
              go to ba999-End
     end-if
*>
     if       WS-MYSQL-Count-Rows = zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number (1:1) not = "0"
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move 10 to fs-reply                  *> EOF equivilent !!
                    move 10 to WE-Error
                    move WS-MYSQL-Error-Number  to SQL-Err   *> Not really needed but help for testing
                    move WS-MYSQL-Error-Message to SQL-Msg   *>  ditto
                    initialize STOCKAUDIT-REC with filler
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
     move     WS-Audit-ID to WS-File-Key.
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
              STOCKAUDIT-REC (K:L)       delimited by size
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
*>             TABLE=STOCKAUDIT-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`STOCKAUDIT-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-STOCKAUDIT-REC
*>      /MYSQL-END\
*>
     if     WS-MYSQL-Count-Rows = zero
            move 21  to fs-Reply             *> could also be 23 or 14
            move zero to WE-Error
            go to ba998-Free
     end-if
     move     6 to ws-No-Paragraph
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=STOCKAUDIT-REC
           MOVE TP-STOCKAUDIT-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-AUDIT-ID
                    HV-AUDIT-KEY
                    HV-AUDIT-INVOICE-PO
                    HV-AUDIT-CR-FOR-INVOICE
                    HV-AUDIT-DESC
                    HV-AUDIT-PROCESS-DAT
                    HV-AUDIT-REVERSE-TRANSACTION
                    HV-AUDIT-TRANSACTION-QTY
                    HV-AUDIT-UNIT-COST
                    HV-AUDIT-STOCK-VALUE-CHANGE
                    HV-AUDIT-NO

*>      /MYSQL-END\
     end-call
*>
     if       WS-MYSQL-Count-Rows not > zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number (1:1) not = "0"
                    move 21 to fs-reply    *> from 23
                    move 990 to WE-Error
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move spaces to WS-File-Key
                    go to ba998-Free
              else
                    move 21   to fs-reply    *> from 23
                    move 989  to WE-Error
                    move zero to SQL-Err
                    move spaces to SQL-Msg
                    move spaces to WS-File-Key
                    go to ba998-Free
              end-if
     end-if                        *> row count zero should show up as a MYSQL error ?
     perform  bb100-UnloadHVs      *> transfer/move HV vars to ws-Record layout
     move     WS-Audit-ID to WS-File-Key
     move     zero to FS-Reply WE-Error.
     go       to ba998-Free.
*>
 ba060-Process-Start.
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
              STOCKAUDIT-REC (K:L)       delimited by size
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
     move     STOCKAUDIT-REC (K:L) to WS-File-Key
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
*>
     move     8 to ws-No-Paragraph
*>      /MYSQL SELECT\
*>
*>    Select rows
*>
*>             TABLE=STOCKAUDIT-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`STOCKAUDIT-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-STOCKAUDIT-REC
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
              if    WS-MYSQL-Error-Number (1:1) not = "0"
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move 21 to fs-reply                  *> this may need changing for val in WE-Error!!
                    move zero to WE-Error
              end-if
     else
              move  zero to FS-Reply WE-Error
              move     WS-MYSQL-Count-Rows to WS-Temp-Ed
              string   MOST-relation
                       STOCKAUDIT-REC (K:L)
                       " got =" delimited by size
                       WS-Temp-ED delimited by size
                       " recs"
                        into WS-File-Key
              end-string
     end-if
     go       to ba999-end.
*>
*>  Now a read next will process a Fetch from cursor
*>
 ba070-Process-Write.
     perform  bb000-HV-Load.                       *>  move STOCKAUDIT-REC fields to HV fields
     move     WS-Audit-ID to WS-File-Key.
     move     zero to FS-Reply WE-Error SQL-State.
     move     spaces to SQL-Msg
     move     zero to SQL-Err
     move     10 to ws-No-Paragraph.
     perform  bb200-Insert.
     if       WS-MYSQL-COUNT-ROWS not = 1
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number (1:1) not = "0"
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
              STOCKAUDIT-REC (K:L)       delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     STOCKAUDIT-REC (K:L)  to WS-File-Key.
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     13 to ws-No-Paragraph.
*>      /MYSQL DELETE\
*>
*>    Delete a row
*>
*>             TABLE=STOCKAUDIT-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`STOCKAUDIT-REC`"
             " WHERE "
             WS-Where (1:J)
             X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>      /MYSQL-END\
     if       WS-MYSQL-COUNT-ROWS not = 1
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number (1:1) not = "0"
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move 99 to fs-reply
                    move 995 to WE-Error
              end-if
              go to ba999-End
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
*>              FROM STOCKAUDIT-REC
*>           END-EXEC.
*>
*>  That creates the follwoing code from dbpre
*>
*>   MOVE LOW-VALUES TO SQLCA-STATEMENT
*>   STRING
*>     "DELETE " DELIMITED SIZE
*>     "FROM " DELIMITED SIZE
*>     "STOCKAUDIT-REC " DELIMITED SIZE
*>   INTO SQLCA-STATEMENT
*>   END-STRING
*>   CALL "MySQL_query" USING SQLCA-STATEMENT
*>   END-CALL
*>
*> So if this does not work it will be changed.
*>
     move     99999999  to WS-Audit-ID.         *> as its the last posting
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
              STOCKAUDIT-REC (K:L)    delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     spaces to WS-File-Key
     string   "Deleting back from " delimited by size
               WS-Audit-ID             delimited by size
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
*>             TABLE=STOCKAUDIT-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`STOCKAUDIT-REC`"
             " WHERE "
             WS-Where (1:J)
             X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
*>      /MYSQL-END\
     if       WS-MYSQL-COUNT-ROWS not > zero    *> Changed for delete-ALL
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number (1:1) not = "0"
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
     move     17 to ws-No-Paragraph.
     set      KOR-x1 to 1            *> 1 = Primary, 2 = Abrev, 3 = Desc (NOT Delete function as can be dups)
     move     KOR-offset (KOR-x1) to K
     move     KOR-length (KOR-x1) to L
*>
     move     STOCKAUDIT-REC (K:L)  to WS-File-Key.
     move     spaces to WS-Where
     move     1   to J
     string   "`"                   delimited by size
              KeyName (KOR-x1)      delimited by space
              "`"                   delimited by size
              '="'                  delimited by size
              STOCKAUDIT-REC (K:L)       delimited by size
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
              if    WS-MYSQL-Error-Number (1:1) not = "0"
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
                    move 994 to WE-Error
              end-if
              go to ba999-End
     end-if
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
*>             TABLE=STOCKAUDIT-REC
           MOVE TP-STOCKAUDIT-REC TO WS-MYSQL-RESULT
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
     initialize TD-STOCKAUDIT-REC.
*>     move     Audit-Key                 to HV-Audit-Key
     move     Audit-Invoice-PO          to HV-Audit-Invoice-PO
     move     Audit-Cr-for-Invoice      to HV-Audit-Cr-for-Invoice
     move     Audit-Desc                to HV-Audit-Desc
     move     Audit-Process-Date        to HV-Audit-Process-Dat
     move     Audit-Reverse-Transaction to HV-Audit-Reverse-Transaction
     move     Audit-Transaction-Qty     to HV-Audit-Transaction-Qty
     move     Audit-Unit-Cost           to HV-Audit-Unit-Cost
     move     Audit-Stock-Value-Change  to HV-Audit-Stock-Value-Change
     move     Audit-No                  to HV-Audit-No.
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
     initialize STOCKAUDIT-REC.
*>     move     HV-Audit-Key                 to Audit-Key
     move     HV-Audit-Invoice-PO          to Audit-Invoice-PO
     move     HV-Audit-Cr-for-Invoice      to Audit-Cr-for-Invoice
     move     HV-Audit-Desc                to Audit-Desc
     move     HV-Audit-Process-Dat         to Audit-Process-Date
     move     HV-Audit-Reverse-Transaction to Audit-Reverse-Transaction
     move     HV-Audit-Transaction-Qty     to Audit-Transaction-Qty
     move     HV-Audit-Unit-Cost           to Audit-Unit-Cost
     move     HV-Audit-Stock-Value-Change  to Audit-Stock-Value-Change
     move     HV-Audit-No                  to Audit-No.

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
*>         TABLE=STOCKAUDIT-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'INSERT INTO '
                    '`STOCKAUDIT-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-ID`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-ID
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-AUDIT-KEY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-INVOICE-PO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-INVOICE-PO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-CR-FOR-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-CR-FOR-INVOICE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-DESC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-AUDIT-DESC,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-PROCESS-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-AUDIT-PROCESS-DAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-REVERSE-TRANSACTION`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-REVERSE-TRANSACTION
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-TRANSACTION-QTY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-TRANSACTION-QTY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-UNIT-COST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-UNIT-COST
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(15:06))
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
           STRING '`AUDIT-STOCK-VALUE-CHANGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-STOCK-VALUE-CHANGE
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
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-NO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-NO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
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
*>      TABLE=STOCKAUDIT-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'UPDATE '
                    '`STOCKAUDIT-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-ID`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-ID
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-AUDIT-KEY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-INVOICE-PO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-INVOICE-PO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-CR-FOR-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-CR-FOR-INVOICE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-DESC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-AUDIT-DESC,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-PROCESS-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-AUDIT-PROCESS-DAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-REVERSE-TRANSACTION`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-REVERSE-TRANSACTION
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-TRANSACTION-QTY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-TRANSACTION-QTY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(14:07))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-UNIT-COST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-UNIT-COST
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(15:06))
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
           STRING '`AUDIT-STOCK-VALUE-CHANGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-STOCK-VALUE-CHANGE
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
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AUDIT-NO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AUDIT-NO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
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
end program auditMT.
