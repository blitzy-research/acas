       >>source free
*>***********************************************
*>                                              *
*>          Purchase Open-Item-File-5           *
*>             Table RDB Handler                *
*>                                              *
*>  WARNING:   the sort read (32) needs heavy   *
*>                  testing
*>             Likewise sort read (33)
*>***********************************************
*>
 identification division.
 Program-Id.            otm5MT.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License
*>                      v2.0. Only. See the file COPYING for details.
*>**
*> Remarks.             Sales Open-Item-File-5 File RDB Handler using amended JC preSQL.
*>                      **********************************************
*>
*>                      This version uses an amended JC pre-Sql processor.
*>                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>
*>                      This modules does all file handling using RDB and is called
*>                      from the ACAS
*>                      Sales Invoice file handler acas029
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
*>     Uses the Global Error / Access logging file within the FH acas0nn module
*>               and in all DALs.
*>**
*> Called by Modules:
*>                      acas029 - Sales Open-Item-File-5 Cobol Handler.
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
*> 27/01/17 vbc -     Taken from paymentsMT as uses a RG group.
*> 08/02/17 vbc -     Taken from slinvoiceMT for OTM5 removing RG proc.
*> 19/02/17 vbc - .07 Wrap quote around key in start same as read-indexed.
*> 07/01/18 vbc - .08 Taken from acas019 for 029.
*> 01/03/18 vbc - .11 Renamed error messages to SM901, SM004 as needed.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              WS-OTM5-Record = Contents of data record to be written/read
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
*>                                     911* = Rdb Error during initializing,
*>                                            possibly can not connect to database
*>                                             Check connect data and
*>                                             see SQL-Err & SQL-MSG
*>                                     910* = Table locked > 5 seconds
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
 77  prog-name           pic x(19)    value "otm5MT (3.3.00)".
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
 01  WS-Temp-ED-Row     pic 9(7).
*>
 01  WS-Temp-ED-Key.
     03  WS-Temp-Ed-Customer.
         05  WS-Temp-Ed-Supplier pic x(7).
     03  WS-Temp-Ed-Invoice  pic 9(8).
*>
 01  WS-Temp-ED-Batch.
     03  WS-Temp-ED-Batch-Nos  pic 9(5).
     03  WS-Temp-ED-Batch-Item pic 999.
 01  WS-Temp-ED-Batch9 redefines WS-Temp-ED-Batch
                            pic 9(8).
*>
*> The communication area for the MySQL database changed for free/mysql
*>
*>  jc preSQL MySQL stuff ends
*>
*> Metadata on primary keys...   for PUITM5-REC
*>
 01  Table-Of-KeyNames.
     03  filler         pic x(30) value 'OI5-KEY                       '.
     03  filler         pic x(8)  value '00010015'.  *> offset/length
     03  filler         pic x(3)  value 'STR'.       *> data type
 01  filler redefines Table-Of-KeyNames.
     03  KeyOfReference occurs 1
                             indexed by KOR-x1.
         05  keyname    pic x(30).
         05  KOR-offset pic 9(4).
         05  KOR-length pic 9(4).
         05  KOR-Type   pic XXX.                   *> Not used currently
*>
 01  DAL-Data.
     03  MOST-Relation     pic xxx.                *> valid are >=, <=, <, >, =
     03  Most-Cursor-Set   pic 9  value zero.
         88  Cursor-Not-Active    value zero.
         88  Cursor-Active        value 1.
     03  Most-Cursor-Set-2 pic 9  value zero.      *> RG 1 or special
         88  Cursor-Not-Active-2  value zero.
         88  Cursor-Active-2      value 1.
     03  Most-Cursor-Set-3 pic 9  value zero.      *> RG 2 or special
         88  Cursor-Not-Active-3  value zero.
         88  Cursor-Active-3      value 1.
*>
*>  Variables common to all DALs
*>  ****************************
*>
 01  subscripts usage comp-5.
     12 J                    pic s9(4).
     12 K                    pic s9(4).
     12 L                    pic s9(4).
*>
 01  WS-Body-Key             pic x(9).
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
*>       TABLE=PUITM5-REC,HV
 COPY "mysql-variables.cpy".
*>
*>    Definitions for the PUITM5-REC Table
*>
       01  TP-PUITM5-REC                         USAGE POINTER.
       01  TD-PUITM5-REC.
           05  HV-OI5-KEY                        PIC X(15).
           05  HV-OI5-SUPPLIER                   PIC X(7).
           05  HV-OI5-INVOICE                    PIC  9(10) COMP.
           05  HV-OI5-DAT                        PIC  9(10) COMP.
           05  HV-OI5-BATCH                      PIC X(8).
           05  HV-OI5-BATCH-NOS                  PIC X(5).
           05  HV-OI5-BATCH-ITEM                 PIC X(3).
           05  HV-OI5-TYPE                       PIC X(1).
           05  HV-OI5-REF                        PIC X(10).
           05  HV-OI5-ORDER                      PIC X(10).
           05  HV-OI5-HOLD-FLAG                  PIC X(1).
           05  HV-OI5-UNAPL                      PIC X(1).
           05  HV-OI5-P-C                        PIC S9(07)V9(02) COMP.
           05  HV-OI5-NET                        PIC S9(07)V9(02) COMP.
           05  HV-OI5-EXTRA                      PIC S9(07)V9(02) COMP.
           05  HV-OI5-CARRIAGE                   PIC S9(07)V9(02) COMP.
           05  HV-OI5-VAT                        PIC S9(07)V9(02) COMP.
           05  HV-OI5-DISCOUNT                   PIC S9(07)V9(02) COMP.
           05  HV-OI5-E-VAT                      PIC S9(07)V9(02) COMP.
           05  HV-OI5-C-VAT                      PIC S9(07)V9(02) COMP.
           05  HV-OI5-PAID                       PIC S9(07)V9(02) COMP.
           05  HV-OI5-STATUS                     PIC X(1).
           05  HV-OI5-DEDUCT-DAYS                PIC  9(03) COMP.
           05  HV-OI5-DEDUCT-AMT                 PIC S9(03)V9(02) COMP.
           05  HV-OI5-DEDUCT-VAT                 PIC S9(03)V9(02) COMP.
           05  HV-OI5-DAYS                       PIC  9(03) COMP.
           05  HV-OI5-CR                         PIC S9(10) COMP.
           05  HV-OI5-APPLIED                    PIC X(1).
           05  HV-OI5-DATE-CLEARED               PIC  9(10) COMP.
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
*>  Using the first record but not the 2nd as it uses occurs 40 but
*>   to reduce Ram usage get rid of the occurs, hopefully.
*>
 copy "plwsoi.cob" replacing OI-Header
               by WS-OTM5-Record.
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
                            WS-OTM5-Record.   *>  Ws record
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
              go to ba020-Process-Open         *> Coded / D.tested
        when  2
              go to ba030-Process-Close        *> Coded / D.tested
        when  3
              go to ba040-Process-Read-Next
        when  4
              go to ba050-Process-Read-Indexed
        when  5
              go to ba070-Process-Write
        when  7
              go to ba090-Process-Rewrite
        when  8
              go to ba080-Process-Delete
        when  9
              go to ba060-Process-Start     *> Uses Header table only
        when  32
              go to ba140-Process-Read-Next        *> Sorted-By-Batch (nos,item,type,date,inv)
        when  33
              go to ba150-Process-Read-Next        *> Sorted-By-Cust (cust,date,inv,type)
        when  other                            *> 6 is spare / unused
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
     move    "OPEN PL OTM5" to WS-File-Key
     set     Cursor-Not-Active to true
     go      to ba999-end.
*>
 ba030-Process-Close.             *> dry tested - no rg01 requirements.
     if      Cursor-Active
             perform ba998-Free.
*>
     move     2 to ws-No-Paragraph.
     move    "CLOSE PL OTM5" to WS-File-Key.
*>  /MYSQL CLOSE\
*>
*>    Close the Database
*>
           PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
*>  /MYSQL-END\
     go      to ba999-end.
*>
 ba040-Process-Read-Next.             *> dry test.. - Has rg01 requirements.
*>
*>   Here a SELECT first then fetch if no cursor active using lowest
*>    possible key of "000000000000000"
*>           [ OI-Key ]
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
                       '"000000000000000"'         delimited by size
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
*>                    TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PUITM5-REC`"
             " WHERE "
             ws-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PUITM5-REC
*>               /MYSQL-END\
           move    "000000000000000" to WS-File-Key
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
              move     WS-MYSQL-Count-Rows to WS-Temp-ED-Row
              string   "> 0 got cnt=" delimited by size
                       WS-Temp-ED-Row delimited by size
                       " recs for INVOICE-RECORD Table"
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
*>             TABLE=PUITM5-REC
           MOVE TP-PUITM5-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-OI5-KEY
                    HV-OI5-SUPPLIER
                    HV-OI5-INVOICE
                    HV-OI5-DAT
                    HV-OI5-BATCH
                    HV-OI5-BATCH-NOS
                    HV-OI5-BATCH-ITEM
                    HV-OI5-TYPE
                    HV-OI5-REF
                    HV-OI5-ORDER
                    HV-OI5-HOLD-FLAG
                    HV-OI5-UNAPL
                    HV-OI5-P-C
                    HV-OI5-NET
                    HV-OI5-EXTRA
                    HV-OI5-CARRIAGE
                    HV-OI5-VAT
                    HV-OI5-DISCOUNT
                    HV-OI5-E-VAT
                    HV-OI5-C-VAT
                    HV-OI5-PAID
                    HV-OI5-STATUS
                    HV-OI5-DEDUCT-DAYS
                    HV-OI5-DEDUCT-AMT
                    HV-OI5-DEDUCT-VAT
                    HV-OI5-DAYS
                    HV-OI5-CR
                    HV-OI5-APPLIED
                    HV-OI5-DATE-CLEARED

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
                    initialize WS-OTM5-Record with filler
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
     move     HV-OI5-KEY to WS-File-Key.
     move     zero to fs-reply WE-Error.
     go       to ba999-end.
*>
 ba050-Process-Read-Indexed.             *> dry test.. - Has rg01 requirements.
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
              WS-OTM5-Record (K:L)       delimited by size
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
*>             TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PUITM5-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PUITM5-REC
*>      /MYSQL-END\
*>
     if       WS-MYSQL-Count-Rows = zero
              move 23  to fs-Reply             *> could also be 21 or 14
              move zero to WE-Error
              go to ba998-Free
     end-if
     move     6 to ws-No-Paragraph
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=PUITM5-REC
           MOVE TP-PUITM5-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-OI5-KEY
                    HV-OI5-SUPPLIER
                    HV-OI5-INVOICE
                    HV-OI5-DAT
                    HV-OI5-BATCH
                    HV-OI5-BATCH-NOS
                    HV-OI5-BATCH-ITEM
                    HV-OI5-TYPE
                    HV-OI5-REF
                    HV-OI5-ORDER
                    HV-OI5-HOLD-FLAG
                    HV-OI5-UNAPL
                    HV-OI5-P-C
                    HV-OI5-NET
                    HV-OI5-EXTRA
                    HV-OI5-CARRIAGE
                    HV-OI5-VAT
                    HV-OI5-DISCOUNT
                    HV-OI5-E-VAT
                    HV-OI5-C-VAT
                    HV-OI5-PAID
                    HV-OI5-STATUS
                    HV-OI5-DEDUCT-DAYS
                    HV-OI5-DEDUCT-AMT
                    HV-OI5-DEDUCT-VAT
                    HV-OI5-DAYS
                    HV-OI5-CR
                    HV-OI5-APPLIED
                    HV-OI5-DATE-CLEARED

*>      /MYSQL-END\
     end-call
*>
     if       WS-MYSQL-Count-Rows not > zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
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
     perform  bb100-UnloadHVs      *> transfer/move HV vars to ws-Record layout
     move     HV-OI5-KEY to WS-File-Key.
     move     zero to FS-Reply WE-Error.
     perform  ba998-Free.                       *> Free cursor
     go       to ba999-End.
*>
 ba060-Process-Start.            *>  coded for header & lines [ NEEDED ? ].
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
*>  Set up MOST-relation for condition test and key on Header table.
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
              WS-OTM5-Record (K:L)       delimited by size
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
     move     WS-OTM5-Record (K:L) to WS-File-Key
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
*>
     move     8 to ws-No-Paragraph
*>      /MYSQL SELECT\
*>
*>    Select rows
*>
*>             TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PUITM5-REC`"
             " WHERE "
             WS-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PUITM5-REC
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
              move     WS-MYSQL-Count-Rows to WS-Temp-ED-Row
              string   MOST-relation
                       WS-OTM5-Record (K:L)
                       " got " delimited by size
                       WS-Temp-ED-Row delimited by size
                       " recs"
                        into WS-File-Key
              end-string
     end-if
     go       to ba999-end.
*>
*>  Now a read next will process a Fetch from cursor ( or cursor-2 )
*>
 ba070-Process-Write.             *> dry test... - Has rg01 requirements.
     perform  bb000-HV-Load.                       *>  move WS-OTM5-Record fields to HV fields
     move     OI-Key to WS-File-Key.
     move     zero to FS-Reply
                      WE-Error
                      SQL-State.
     move     spaces to SQL-Msg
     move     zero to SQL-Err
     move     10 to ws-No-Paragraph.
     perform  bb200-Insert.
     if       WS-MYSQL-COUNT-ROWS not = 1
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              move  99 to fs-reply                  *> this may need changing for val in WE-Error!!
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using Ws-Mysql-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err
                    move WS-MYSQL-Error-Message to SQL-Msg
                    if    SQL-Err (1:4) = "1062"
                                     or = "1022"   *> Dup key
                          or Sql-State = "23000"   *> Dup key
                           move 22 to fs-reply
                    end-if
              end-if
     end-if
     go       to ba999-End.
*>
 ba080-Process-Delete.             *> dry tested. - Has rg01 requirements.
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
              WS-OTM5-Record (K:L)       delimited by size
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-OTM5-Record (K:L)  to WS-File-Key.
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     if    Testing-2
           display Display-Message-1 with erase eos
     end-if
     move     13 to ws-No-Paragraph.
*>      /MYSQL DELETE\
*>
*>    Delete a row
*>
*>             TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "DELETE FROM "
             "`PUITM5-REC`"
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
     go       to ba999-End.
*>
 ba090-Process-Rewrite.
     perform  bb000-HV-Load.       *> Load up the HV fields from table record in WS
     move     OI-Key to WS-File-Key.
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
              WS-OTM5-Record (K:L)       delimited by size
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
     move     zero   to FS-Reply
                        WE-Error
                        SQL-Err.
     move     spaces to SQL-Msg.
     go       to ba999-End.
*>
 ba140-Process-Read-Next.
*>
*>  Like 040 except we do order by B-Nos B-Item ASC, Type DES,
*>              Date Invoice ASC
*>
*>   Here a SELECT first then fetch if no cursor active 2 NOT using
*>   a key as by order
*>
     if       Cursor-Not-Active-2
              set      KOR-x1 to 1                *> 1 = Primary
              move     KOR-offset (KOR-x1) to K
              move     KOR-length (KOR-x1) to L
*>
              move     spaces to WS-Where
              move     1   to J
              string   " ORDER BY "          delimited by size
                       "'OI5-INVOICE', 'OI5-DAT' ASC, "
                                             delimited by size
                       "'OI5-TYPE' DESC, "   delimited by size
                       "'OI5-BATCH-ITEM', 'OI5-BATCH-NOS' ASC "
                                             delimited by size
                                      into ws-Where
                                      with pointer J
              end-string
*>
              move     ws-Where (1:J)   to WS-Log-Where       *>  For test logging
              move     21 to ws-No-Paragraph
*>               /MYSQL SELECT\
*>
*>    Select rows
*>
*>                    TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PUITM5-REC`"
             " WHERE "
             ws-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PUITM5-REC
*>               /MYSQL-END\
              move     "Sorted" to WS-File-Key
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
                       move 10 to WE-Error
                       move    "No Data" to WS-File-Key
                       go to ba999-End       *> can clear the dup code after testing
              end-if
              set      Cursor-Active-2 to true
              move     WS-MYSQL-Count-Rows to WS-Temp-Ed-Row
              string   "> 0 got cnt=" delimited by size
                       WS-Temp-ED-Row delimited by size
                       " recs in sorted order"
                        into WS-File-Key
              end-string
              perform ba999-End                         *> log it
     end-if.
*>
 ba141-Reread.
*>
*>  If here cursor is set (even from start), so get the next row
*>
     move     spaces to WS-Log-Where.
     move     22 to ws-No-Paragraph.
     move zero to return-code.
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=PUITM5-REC
           MOVE TP-PUITM5-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-OI5-KEY
                    HV-OI5-SUPPLIER
                    HV-OI5-INVOICE
                    HV-OI5-DAT
                    HV-OI5-BATCH
                    HV-OI5-BATCH-NOS
                    HV-OI5-BATCH-ITEM
                    HV-OI5-TYPE
                    HV-OI5-REF
                    HV-OI5-ORDER
                    HV-OI5-HOLD-FLAG
                    HV-OI5-UNAPL
                    HV-OI5-P-C
                    HV-OI5-NET
                    HV-OI5-EXTRA
                    HV-OI5-CARRIAGE
                    HV-OI5-VAT
                    HV-OI5-DISCOUNT
                    HV-OI5-E-VAT
                    HV-OI5-C-VAT
                    HV-OI5-PAID
                    HV-OI5-STATUS
                    HV-OI5-DEDUCT-DAYS
                    HV-OI5-DEDUCT-AMT
                    HV-OI5-DEDUCT-VAT
                    HV-OI5-DAYS
                    HV-OI5-CR
                    HV-OI5-APPLIED
                    HV-OI5-DATE-CLEARED

*>      /MYSQL-END\
     end-call
*>
     if       return-code = -1     *> no more data so free cursor & return
              move 10 to fs-Reply WE-Error
              move    "EOF" to WS-File-Key
              set Cursor-Not-Active-2 to true
              go to ba999-End
     end-if
*>
     if       WS-MYSQL-Count-Rows = zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err   *> Not really needed but help for testing
                    move WS-MYSQL-Error-Message to SQL-Msg   *>  ditto
                    initialize WS-OTM5-Record with filler
                    move    "EOF2" to WS-File-Key
              end-if
              move 10 to fs-reply                  *> EOF equivilent !!
              move 10 to WE-Error
              set Cursor-Not-Active-2 to true
              go to ba999-End
     end-if.
*>
     if       fs-reply = 10
              set Cursor-Not-Active-2 to true
              move    "EOF3" to WS-File-Key
              go to ba999-End
     end-if.
*>
     perform  bb100-UnloadHVs.       *> transfer/move HV vars to Record layout
     move     HV-OI5-KEY to WS-File-Key.
     move     zero to fs-reply WE-Error.
     go       to ba999-end.
*>
 ba150-Process-Read-Next.
*>
*>  Like 040,140 except we do order by s-customer
*>                                     s-date
*>                                     s-invoice
*>                                     s-type ASC
*>
*>   Here a SELECT first then fetch if no cursor active 3 NOT using
*>   a key as by order
*>
     if       Cursor-Not-Active-3
              set      KOR-x1 to 1                *> 1 = Primary
              move     KOR-offset (KOR-x1) to K
              move     KOR-length (KOR-x1) to L
*>
              move     spaces to WS-Where
              move     1   to J
              string   " ORDER BY "          delimited by size
                       "'OI5-SUPPLIER', 'OI5-DAT', " delimited by size
                       "'OI5-INVOICE', 'OI5-TYPE' ASC "
                                             delimited by size
                                      into ws-Where
                                      with pointer J
              end-string
*>
              move     ws-Where (1:J)   to WS-Log-Where       *>  For test logging
              move     21 to ws-No-Paragraph
*>               /MYSQL SELECT\
*>
*>    Select rows
*>
*>                    TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`PUITM5-REC`"
             " WHERE "
             ws-Where (1:J)
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-PUITM5-REC
*>               /MYSQL-END\
             move    "Sorted" to WS-File-Key
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
                       move 10 to WE-Error
                       move    "No Data" to WS-File-Key
                       go to ba999-End       *> can clear the dup code after testing
              end-if
              set      Cursor-Active-3 to true
              move     WS-MYSQL-Count-Rows to WS-Temp-Ed-Row
              string   "> 0 got cnt=" delimited by size
                       WS-Temp-ED-Row delimited by size
                       " recs in sorted order"
                        into WS-File-Key
              end-string
              perform ba999-End                         *> log it
     end-if.
*>
 ba151-Reread.
*>
*>  If here cursor is set (even from start), so get the next row
*>
     move     spaces to WS-Log-Where.
     move     22 to ws-No-Paragraph.
     move zero to return-code.
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=PUITM5-REC
           MOVE TP-PUITM5-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-OI5-KEY
                    HV-OI5-SUPPLIER
                    HV-OI5-INVOICE
                    HV-OI5-DAT
                    HV-OI5-BATCH
                    HV-OI5-BATCH-NOS
                    HV-OI5-BATCH-ITEM
                    HV-OI5-TYPE
                    HV-OI5-REF
                    HV-OI5-ORDER
                    HV-OI5-HOLD-FLAG
                    HV-OI5-UNAPL
                    HV-OI5-P-C
                    HV-OI5-NET
                    HV-OI5-EXTRA
                    HV-OI5-CARRIAGE
                    HV-OI5-VAT
                    HV-OI5-DISCOUNT
                    HV-OI5-E-VAT
                    HV-OI5-C-VAT
                    HV-OI5-PAID
                    HV-OI5-STATUS
                    HV-OI5-DEDUCT-DAYS
                    HV-OI5-DEDUCT-AMT
                    HV-OI5-DEDUCT-VAT
                    HV-OI5-DAYS
                    HV-OI5-CR
                    HV-OI5-APPLIED
                    HV-OI5-DATE-CLEARED

*>      /MYSQL-END\
     end-call
*>
     if       return-code = -1     *> no more data so free cursor & return
              move 10 to fs-Reply WE-Error
              move    "EOF" to WS-File-Key
              set Cursor-Not-Active-3 to true
              go to ba999-End
     end-if
*>
     if       WS-MYSQL-Count-Rows = zero
              call  "MySQL_errno" using WS-MYSQL-Error-Number
              call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
              move  WS-MYSQL-SqlState   to SQL-State
              if    WS-MYSQL-Error-Number  not = "0  "
                    call "MySQL_error" using WS-MYSQL-Error-Message
                    move WS-MYSQL-Error-Number  to SQL-Err   *> Not really needed but help for testing
                    move WS-MYSQL-Error-Message to SQL-Msg   *>  ditto
                    initialize WS-OTM5-Record with filler
                    move    "EOF2" to WS-File-Key
              end-if
              move 10 to fs-reply                  *> EOF equivilent !!
              move 10 to WE-Error
              set Cursor-Not-Active-3 to true
              go to ba999-End
     end-if.
*>
     if       fs-reply = 10
              set Cursor-Not-Active-3 to true
              move    "EOF3" to WS-File-Key
              go to ba999-End
     end-if.
*>
     perform  bb100-UnloadHVs.       *> transfer/move HV vars to Record layout
     move     HV-OI5-KEY to WS-File-Key.
     move     zero to fs-reply WE-Error.
     go       to ba999-end.
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
*>             TABLE=PUITM5-REC
           MOVE TP-PUITM5-REC TO WS-MYSQL-RESULT
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
     initialize TD-PUITM5-REC.
*>
     move     OI-Invoice  to HV-OI5-INVOICE
                             WS-Temp-Ed-Invoice.
     move     OI-Supplier to HV-OI5-SUPPLIER
                             WS-Temp-Ed-Supplier.
     move     WS-Temp-Ed-Key  to HV-OI5-KEY
*>
     move     OI-B-Nos        to HV-OI5-BATCH-NOS
                                 WS-Temp-ED-Batch-Nos.
     move     OI-B-Item       to HV-OI5-BATCH-ITEM
                                 WS-Temp-ED-Batch-Item.
     move     WS-Temp-ED-Batch9 to HV-OI5-BATCH.
*>
     move     OI-Date         to HV-OI5-DAT
     move     OI-Type         to HV-OI5-TYPE
     move     OI-Ref          to HV-OI5-REF
     move     OI-Order        to HV-OI5-ORDER
     move     OI-Hold-Flag    to HV-OI5-HOLD-FLAG
     move     OI-Unapl        to HV-OI5-UNAPL
     move     OI-P-C          to HV-OI5-P-C
     move     OI-Net          to HV-OI5-NET
     move     OI-Extra        to HV-OI5-EXTRA
     move     OI-Carriage     to HV-OI5-CARRIAGE
     move     OI-Vat          to HV-OI5-VAT
     move     OI-Discount     to HV-OI5-DISCOUNT
     move     OI-E-Vat        to HV-OI5-E-VAT
     move     OI-C-Vat        to HV-OI5-C-VAT
     move     OI-Paid         to HV-OI5-PAID
     move     OI-Status       to HV-OI5-STATUS
     move     OI-Deduct-Days  to HV-OI5-DEDUCT-DAYS
     move     OI-Deduct-Amt   to HV-OI5-DEDUCT-AMT
     move     OI-Deduct-Vat   to HV-OI5-DEDUCT-VAT
     move     OI-Days         to HV-OI5-DAYS
     move     OI-CR           to HV-OI5-CR
     move     OI-Applied      to HV-OI5-APPLIED
     move     OI-Date-Cleared to HV-OI5-DATE-CLEARED.
*>
 bb000-Exit.
     exit section.
*>
 bb100-UnloadHVs    Section.
*>*************************
*>
*>  Load the data buffer in the interface with data from the host variables.
*>
     initialize WS-OTM5-Record.
*>
     move     HV-OI5-INVOICE       to OI-Invoice
     move     HV-OI5-SUPPLIER      to OI-Supplier
     move     HV-OI5-DAT           to OI-Date
*>
     move     HV-OI5-BATCH-NOS     to OI-B-Nos
     move     HV-OI5-BATCH-ITEM    to OI-B-Item
*>
     move     HV-OI5-TYPE          to OI-Type
     move     HV-OI5-REF           to OI-Ref
     move     HV-OI5-ORDER         to OI-Order
     move     HV-OI5-HOLD-FLAG     to OI-Hold-Flag
     move     HV-OI5-UNAPL         to OI-Unapl
     move     HV-OI5-P-C           to OI-P-C
     move     HV-OI5-NET           to OI-Net
     move     HV-OI5-EXTRA         to OI-Extra
     move     HV-OI5-CARRIAGE      to OI-Carriage
     move     HV-OI5-VAT           to OI-Vat
     move     HV-OI5-DISCOUNT      to OI-Discount
     move     HV-OI5-E-VAT         to OI-E-Vat
     move     HV-OI5-C-VAT         to OI-C-Vat
     move     HV-OI5-PAID          to OI-Paid
     move     HV-OI5-STATUS        to OI-Status
     move     HV-OI5-DEDUCT-DAYS   to OI-Deduct-Days
     move     HV-OI5-DEDUCT-AMT    to OI-Deduct-Amt
     move     HV-OI5-DEDUCT-VAT    to OI-Deduct-Vat
     move     HV-OI5-DAYS          to OI-Days
     move     HV-OI5-CR            to OI-CR
     move     HV-OI5-APPLIED       to OI-Applied
     move     HV-OI5-DATE-CLEARED  to OI-Date-Cleared.
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
*>         TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'INSERT INTO '
                    '`PUITM5-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-KEY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-SUPPLIER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-SUPPLIER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-INVOICE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-BATCH,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-BATCH-NOS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-BATCH-NOS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-BATCH-ITEM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-BATCH-ITEM,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-TYPE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-TYPE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-REF`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-REF,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-ORDER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-ORDER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-HOLD-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-HOLD-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-UNAPL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-UNAPL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-P-C`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-P-C
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
           STRING '`OI5-NET`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-NET
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
           STRING '`OI5-EXTRA`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-EXTRA
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
           STRING '`OI5-CARRIAGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-CARRIAGE
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
           STRING '`OI5-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-VAT
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
           STRING '`OI5-DISCOUNT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DISCOUNT
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
           STRING '`OI5-E-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-E-VAT
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
           STRING '`OI5-C-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-C-VAT
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
           STRING '`OI5-PAID`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-PAID
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
           STRING '`OI5-STATUS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-STATUS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DEDUCT-DAYS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DEDUCT-DAYS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DEDUCT-AMT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DEDUCT-AMT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
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
           STRING '`OI5-DEDUCT-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DEDUCT-VAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
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
           STRING '`OI5-DAYS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DAYS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-CR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-CR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-APPLIED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-APPLIED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DATE-CLEARED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DATE-CLEARED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
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
*>      TABLE=PUITM5-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'UPDATE '
                    '`PUITM5-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-KEY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-SUPPLIER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-SUPPLIER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-INVOICE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-BATCH,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-BATCH-NOS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-BATCH-NOS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-BATCH-ITEM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-BATCH-ITEM,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-TYPE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-TYPE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-REF`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-REF,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-ORDER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-ORDER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-HOLD-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-HOLD-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-UNAPL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-UNAPL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-P-C`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-P-C
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
           STRING '`OI5-NET`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-NET
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
           STRING '`OI5-EXTRA`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-EXTRA
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
           STRING '`OI5-CARRIAGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-CARRIAGE
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
           STRING '`OI5-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-VAT
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
           STRING '`OI5-DISCOUNT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DISCOUNT
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
           STRING '`OI5-E-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-E-VAT
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
           STRING '`OI5-C-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-C-VAT
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
           STRING '`OI5-PAID`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-PAID
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
           STRING '`OI5-STATUS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-STATUS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DEDUCT-DAYS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DEDUCT-DAYS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DEDUCT-AMT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DEDUCT-AMT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
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
           STRING '`OI5-DEDUCT-VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DEDUCT-VAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
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
           STRING '`OI5-DAYS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DAYS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-CR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-CR
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-APPLIED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI5-APPLIED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI5-DATE-CLEARED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OI5-DATE-CLEARED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
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
end program otm5MT.
