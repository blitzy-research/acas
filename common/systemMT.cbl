       >>source free
*>***********************************************
*>                                              *
*>                  System                      *
*>            File/Table RDB Handler            *
*>                                              *
*>***********************************************
*>
 identification division.
 Program-Id.            systemMT.
*>**
*> Author.              Vincent B Coen, FBCS, FIDM, FIDPM, CPL
*>                      for Applewood Computers.
*>**
*> Security.            Copyright (C) 2016 and later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License
*>                      v2.0. Only. See the file COPYING for details.
*>**
*> Remarks.             System  File RDB Handler using amended JC preSQL.
*>                      **********************************************
*>
*>                      This version uses an amended JC pre-Sql processor.
*>                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*>
*>                      This and associated modules relate to ACAS versions v3.02 and later.
*>
*>                      This modules does all file handling using RDB and is called
*>                      from the ACAS
*>                      System (as well as default, final and system-4) file handler acas000
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
*>                      acas000 - System  Cobol Handler.
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
*> 27/08/16 vbc -     Taken from systemMT with same versioning.
*> 18/09/16 vbc -     Temp added code to find out why a SQL error happens turned out
*>                    that using as a SL or PL delimiter a \ screws it up when processing
*>                    as it would need another '\'. There are others !
*>  '                  This could also be a problem for name and address fields.<<<<<
*>                    May be its to do with the windoz path type delim.
*>                    Solution do NOT use it.
*> 23/09/16 vbc - .06 Removed the lock/unlock as these are not needed with Mysql as
*>                    it will do itself when using select + update/delete according to
*>                    "Definitive guide to MySQL 5 page 254" see text :
*> Tips MySQL always executes individual commands in such a way that they cannot be
*> influenced by other commands. Therefore, no locking is necessary for a single command
*> UPDATE … WHERE id=1234 or DELETE …WHERE id=5678.
*> You need to execute locking only if you are executing several interdependent commands
*> during which another client should not alter the underlying data. Usually, that is the
*> case when you first execute a SELECT command and then process the resulting data with an
*> UPDATE or DELETE command.
*> LOCK and UNLOCK should not be used for InnoDB tables. With older versions of MySQL
*> (< 4.0.22), the locking mechanisms of MySQL and InnoDB can get in each other’s way. LOCK
*> also ends the current transaction, which is often an undesired outcome. Instead, use
*> transactions that block only individual records (instead of entire tables).
*> If you really wish to block an entire InnoDB table, there is available a new command,
*> since MySQL 5.0.3, namely, LOCK TABLE[S] TRANSACTIONAL.
*>
*>  REMEMBER to remove for all other DAL units.
*> 08/12/16 vbc - .07 Remove all moves for IRS flenames and system-op fields
*>                    as removed from file / table layouts.
*> 09/12/16 vbc - .08 Make functions 3 & 4 both read-next as in acas000 its indexed
*>                    and in the DAL it is next.
*>                .09 Close logging on fn-close issued at ba999-end.
*> 02/02/18 vbc - .10 Remed references to file-statuses as now filler.
*> 01/03/18 vbc - .11 Renamed error messages to SM901, SM004 as needed.
*> 20/03/18 vbc - .12 Added New field SL-Invoice-Lines to un/load routines (bb000 & bb100).
*> 06/06/18 VBC - .13 Added 6 new fields for un/load routines bb0 & 1 for GL a/cs.
*> 06/06/19 vbc - .14 Added in support for SQL-State to match up other MT routines.
*> 13/03/24 vbc - .15 New fields for System rec added that use filler areas
*>                    STK-BO-ACTIVE & SL-BO-FLAG.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>**
*>  Module USAGE
*>**************
*>
*>    On Entry:         Set up Linkage areas -
*>    ********              System-Record
*>                                   = Contents of data record to be written/read
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
*>                                            Produced by Mysql-1100-Db-Error in copy
*>                                            module mysql-procedure.
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
 copy "envdiv.cob".
*>
 input-output section.
 Data Division.
 Working-Storage Section.
 77  prog-name          pic x(18)    value "systemMT (3.3.00)".
*>
*> JC WS requirements here
*>
 77  ws-Where           pic x(512).
*>
*> SPECIAL for systemMT only (data conversion for SQL)
*>
 01  ws-maps-ser-x.
     03  ws-maps-xx     pic xx.
     03  ws-maps-nn     pic 9(4).
*>
*>  Used within presql generated code
*>
 01  WS-Reply           pic x           value space.
 01  WS-MYSQL-I         PIC S9(6) COMP.
 01  WS-MYSQL-EDIT      PIC -Z(18)9.9(9).
*>
*> The communication area for the MySQL database changed for free/mysql
*>
*>  jc preSQL MySQL stuff ends
*>
*> Metadata on primary and alternate keys...  from Prima DAL for System-REC
*>
 01  Table-Of-Keynames.
     03  filler         pic x(30) value 'SYSTEM-REC-KEY                '.
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
*>
 01  Error-Messages.
     03  SM901          pic x(31) value "SM901 Note error and hit return".
*>
*> /MYSQL VAR\
*>       ACASDB
*>       TABLE=SYSTEM-REC,HV
 COPY "mysql-variables.cpy".
*>
*>    Definitions for the SYSTEM-REC Table
*>
       01  TP-SYSTEM-REC                         USAGE POINTER.
       01  TD-SYSTEM-REC.
           05  HV-SYSTEM-REC-KEY                 PIC  9(03) COMP.
           05  HV-SYSTEM-RECORD-VERSION-PRIME    PIC  9(03) COMP.
           05  HV-SYSTEM-RECORD-VERSION-SECON    PIC  9(03) COMP.
           05  HV-VAT-RATE-1                     PIC  9(02)V9(02) COMP.
           05  HV-VAT-RATE-2                     PIC  9(02)V9(02) COMP.
           05  HV-VAT-RATE-3                     PIC  9(02)V9(02) COMP.
           05  HV-VAT-RATE-4                     PIC  9(02)V9(02) COMP.
           05  HV-VAT-RATE-5                     PIC  9(02)V9(02) COMP.
           05  HV-CYCLEA                         PIC  9(03) COMP.
           05  HV-PERIOD                         PIC  9(03) COMP.
           05  HV-PAGE-LINES                     PIC  9(03) COMP.
           05  HV-NEXT-INVOICE                   PIC  9(10) COMP.
           05  HV-RUN-DAT                        PIC  9(10) COMP.
           05  HV-START-DAT                      PIC  9(10) COMP.
           05  HV-END-DAT                        PIC  9(10) COMP.
           05  HV-SUSER                          PIC X(32).
           05  HV-USER-CODE                      PIC X(32).
           05  HV-ADDRESS-1                      PIC X(24).
           05  HV-ADDRESS-2                      PIC X(24).
           05  HV-ADDRESS-3                      PIC X(24).
           05  HV-ADDRESS-4                      PIC X(24).
           05  HV-POST-CODE                      PIC X(12).
           05  HV-COMPANY-EMAIL                  PIC X(30).
           05  HV-COUNTRY                        PIC X(24).
           05  HV-PRINT-SPOOL-NAME               PIC X(48).
           05  HV-PASS-VALUE                     PIC  9(03) COMP.
           05  HV-LEVEL-1                        PIC  9(03) COMP.
           05  HV-LEVEL-2                        PIC  9(03) COMP.
           05  HV-LEVEL-3                        PIC  9(03) COMP.
           05  HV-LEVEL-4                        PIC  9(03) COMP.
           05  HV-LEVEL-5                        PIC  9(03) COMP.
           05  HV-LEVEL-6                        PIC  9(03) COMP.
           05  HV-PASS-WORD                      PIC X(4).
           05  HV-HOST                           PIC  9(03) COMP.
           05  HV-OP-SYSTEM                      PIC  9(03) COMP.
           05  HV-CURRENT-QUARTER                PIC  9(03) COMP.
           05  HV-FILE-SYSTEM-USED               PIC  9(03) COMP.
           05  HV-FILE-DUPLICATES-IN-USE         PIC  9(03) COMP.
           05  HV-MAPS-SER                       PIC X(6).
           05  HV-DATE-FORM                      PIC  9(03) COMP.
           05  HV-DATA-CAPTURE-USED              PIC  9(03) COMP.
           05  HV-RDBMS-DB-NAME                  PIC X(12).
           05  HV-RDBMS-USER                     PIC X(12).
           05  HV-RDBMS-PASSWD                   PIC X(12).
           05  HV-RDBMS-PORT                     PIC X(5).
           05  HV-RDBMS-HOST                     PIC X(32).
           05  HV-RDBMS-SOCKET                   PIC X(64).
           05  HV-VAT-REG-NUMBER                 PIC X(11).
           05  HV-PARAM-RESTRICT                 PIC X(1).
           05  HV-STATS-DATE-PERIOD              PIC X(4).
           05  HV-P-C                            PIC X(1).
           05  HV-P-C-GROUPED                    PIC X(1).
           05  HV-P-C-LEVEL                      PIC X(1).
           05  HV-COMPS                          PIC X(1).
           05  HV-COMPS-ACTIVE                   PIC X(1).
           05  HV-M-V                            PIC X(1).
           05  HV-ARCH                           PIC X(1).
           05  HV-TRANS-PRINT                    PIC X(1).
           05  HV-TRANS-PRINTED                  PIC X(1).
           05  HV-HEADER-LEVEL                   PIC  9(03) COMP.
           05  HV-SALES-RANGE                    PIC  9(03) COMP.
           05  HV-PURCHASE-RANGE                 PIC  9(03) COMP.
           05  HV-VAT                            PIC X(1).
           05  HV-BATCH-ID                       PIC X(1).
           05  HV-LEDGER-2ND-INDEX               PIC X(1).
           05  HV-IRS-INSTEAD                    PIC X(1).
           05  HV-LEDGER-SEC                     PIC  9(05) COMP.
           05  HV-UPDATES                        PIC  9(05) COMP.
           05  HV-POSTINGS                       PIC  9(05) COMP.
           05  HV-NEXT-BATCH                     PIC  9(05) COMP.
           05  HV-EXTRA-CHARGE-AC                PIC  9(10) COMP.
           05  HV-VAT-AC                         PIC  9(10) COMP.
           05  HV-PRINT-SPOOL-NAME2              PIC X(48).
           05  HV-NEXT-FOLIO                     PIC  9(10) COMP.
           05  HV-BL-PAY-AC                      PIC  9(10) COMP.
           05  HV-P-CREDITORS                    PIC  9(10) COMP.
           05  HV-BL-PURCH-AC                    PIC  9(10) COMP.
           05  HV-GL-BL-PAY-AC                   PIC  9(10) COMP.
           05  HV-GL-P-CREDITORS                 PIC  9(10) COMP.
           05  HV-GL-BL-PURCH-AC                 PIC  9(10) COMP.
           05  HV-GL-SL-PAY-AC                   PIC  9(10) COMP.
           05  HV-GL-S-DEBTORS                   PIC  9(10) COMP.
           05  HV-GL-SL-SALES-AC                 PIC  9(10) COMP.
           05  HV-BL-END-CYCLE-DAT               PIC  9(10) COMP.
           05  HV-BL-NEXT-BATCH                  PIC  9(05) COMP.
           05  HV-AGE-TO-PAY                     PIC  9(05) COMP.
           05  HV-PURCHASE-LEDGER                PIC X(1).
           05  HV-PL-DELIM                       PIC X(1).
           05  HV-ENTRY-LEVEL                    PIC  9(03) COMP.
           05  HV-P-FLAG-A                       PIC  9(03) COMP.
           05  HV-P-FLAG-I                       PIC  9(03) COMP.
           05  HV-P-FLAG-P                       PIC  9(03) COMP.
           05  HV-PL-STOCK-LINK                  PIC X(1).
           05  HV-PRINT-SPOOL-NAME3              PIC X(48).
           05  HV-PL-AUTOGEN                     PIC X(1).
           05  HV-PL-NEXT-REC                    PIC  9(05) COMP.
           05  HV-SALES-LEDGER                   PIC X(1).
           05  HV-SL-DELIM                       PIC X(1).
           05  HV-OI-3-FLAG                      PIC X(1).
           05  HV-CUST-FLAG                      PIC X(1).
           05  HV-OI-5-FLAG                      PIC X(1).
           05  HV-S-FLAG-OI-3                    PIC X(1).
           05  HV-FULL-INVOICING                 PIC  9(03) COMP.
           05  HV-S-FLAG-A                       PIC  9(03) COMP.
           05  HV-S-FLAG-I                       PIC  9(03) COMP.
           05  HV-S-FLAG-P                       PIC  9(03) COMP.
           05  HV-SL-DUNNING                     PIC  9(03) COMP.
           05  HV-SL-CHARGES                     PIC  9(03) COMP.
           05  HV-SL-OWN-NOS                     PIC X(1).
           05  HV-SL-STATS-RUN                   PIC  9(03) COMP.
           05  HV-SL-DAY-BOOK                    PIC  9(03) COMP.
           05  HV-INVOICER                       PIC  9(03) COMP.
           05  HV-EXTRA-DESC                     PIC X(14).
           05  HV-EXTRA-TYPE                     PIC X(1).
           05  HV-EXTRA-PRINT                    PIC X(1).
           05  HV-SL-STOCK-LINK                  PIC X(1).
           05  HV-SL-STOCK-AUDIT                 PIC X(1).
           05  HV-SL-LATE-PER                    PIC  9(02)V9(02) COMP.
           05  HV-SL-DISC                        PIC  9(02)V9(02) COMP.
           05  HV-EXTRA-RATE                     PIC  9(02)V9(02) COMP.
           05  HV-SL-DAYS-1                      PIC  9(05) COMP.
           05  HV-SL-DAYS-2                      PIC  9(05) COMP.
           05  HV-SL-DAYS-3                      PIC  9(05) COMP.
           05  HV-SL-CREDIT                      PIC  9(05) COMP.
           05  HV-SL-MIN                         PIC  9(05) COMP.
           05  HV-SL-MAX                         PIC  9(05) COMP.
           05  HV-PF-RETENTION                   PIC  9(05) COMP.
           05  HV-FIRST-SL-BATCH                 PIC  9(05) COMP.
           05  HV-FIRST-SL-INV                   PIC  9(10) COMP.
           05  HV-SL-LIMIT                       PIC  9(10) COMP.
           05  HV-SL-PAY-AC                      PIC  9(10) COMP.
           05  HV-S-DEBTORS                      PIC  9(10) COMP.
           05  HV-SL-SALES-AC                    PIC  9(10) COMP.
           05  HV-S-END-CYCLE-DAT                PIC  9(10) COMP.
           05  HV-SL-COMP-HEAD-PICK              PIC X(1).
           05  HV-SL-COMP-HEAD-INV               PIC X(1).
           05  HV-SL-COMP-HEAD-STAT              PIC X(1).
           05  HV-SL-COMP-HEAD-LETS              PIC X(1).
           05  HV-SL-VAT-PRINTED                 PIC X(1).
           05  HV-SL-INVOICE-LINES               PIC  9(03) COMP.
           05  HV-SL-AUTOGEN                     PIC X(1).
           05  HV-SL-NEXT-REC                    PIC S9(05) COMP.
           05  HV-STK-ABREV-REF                  PIC X(6).
           05  HV-STK-DEBUG                      PIC  9(03) COMP.
           05  HV-STK-MANU-USED                  PIC  9(03) COMP.
           05  HV-STK-OE-USED                    PIC  9(03) COMP.
           05  HV-STK-AUDIT-USED                 PIC  9(03) COMP.
           05  HV-STK-MOV-AUDIT                  PIC  9(03) COMP.
           05  HV-STK-PERIOD-CUR                 PIC X(1).
           05  HV-STK-PERIOD-DAT                 PIC X(1).
           05  HV-STOCK-CONTROL                  PIC X(1).
           05  HV-STK-AVERAGING                  PIC  9(03) COMP.
           05  HV-STK-ACTIVITY-REP-RUN           PIC  9(03) COMP.
           05  HV-STK-PAGE-LINES                 PIC  9(03) COMP.
           05  HV-STK-AUDIT-NO                   PIC  9(03) COMP.
           05  HV-CLIENT                         PIC X(24).
           05  HV-NEXT-POST                      PIC  9(08) COMP.
           05  HV-VAT1                           PIC  9(02)V9(02) COMP.
           05  HV-VAT2                           PIC  9(02)V9(02) COMP.
           05  HV-VAT3                           PIC  9(02)V9(02) COMP.
           05  HV-IRS-PASS-VALUE                 PIC  9(03) COMP.
           05  HV-SAVE-SEQU                      PIC  9(03) COMP.
           05  HV-SYSTEM-WORK-GROUP              PIC X(18).
           05  HV-PL-APP-CREATED                 PIC X(1).
           05  HV-PL-APPROP-AC                   PIC  9(08) COMP.
           05  HV-1ST-TIME-FLAG                  PIC  9(03) COMP.
           05  HV-PL-APPROP-AC6                  PIC  9(08) COMP.
           05  HV-SL-BO-FLAG                     PIC X(1).
           05  HV-STK-BO-ACTIVE                  PIC X(1).
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
 copy "wssystem.cob".
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
                            System-Record.   *>  Ws record
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
     move     spaces to WS-MYSQL-Error-Message
                        WS-MYSQL-Error-Number
                        WS-Log-Where
                        WS-File-Key
                        SQL-Msg
                        SQL-Err
                        SQL-State.
*>
*>   As this is for only one row we will skip this ...
*>
*>   Now Test for valid key for start, read-indexed and delete
*>
*>    evaluate File-Function
 *>             when  4   *> fn-read-indexed
 *>             when  9   *> fn-start
 *>               if     File-Key-No not = 1
 *>                      move 998 to WE-Error       *> file seeks key type out of range        998
 *>                      move 99 to fs-reply
 *>                      go   to ba999-end
 *>               end-if
 *>             when     8  *> fn-delete
 *>               if     File-Key-No not = 1
 *>                      move 996 to WE-Error       *> file seeks key type out of range        996
 *>                      move 99 to fs-reply
 *>                      go   to ba999-end
 *>               end-if
 *>    end-evaluate.
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
        when  3        *> cobol is indexed but here its next
        when  4
              go to ba040-Process-Read-Next
        when  5
              go to ba070-Process-Write
        when  7
              go to ba090-Process-Rewrite
        when  other                          *> 6 is spare / unused
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
     move    "OPEN SYSTEM" to WS-File-Key
     move    zero   to Most-Cursor-Set
     go      to ba999-end.
*>
 ba030-Process-Close.
     if      Cursor-Active         *> this will not occur for the system rows/records
             perform ba998-Free.
*>
     move     2 to ws-No-Paragraph.
     move    "CLOSE SYSTEM" to WS-File-Key.
*>  /MYSQL CLOSE\
*>
*>    Close the Database
*>
           PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
*>  /MYSQL-END\
*>
     go      to ba999-end.
*>
 ba040-Process-Read-Next.    *> really only getting the one and only row
*>
*>   Here a SELECT first then fetch if no cursor active using lowest
*>    possible key of "000"
*>           [ SYSTEM-REC-KEY ]
*>
     if       Cursor-Not-Active
              set      KOR-x1 to 1                *> 1 = Primary, 2 = Abrev, 3 = Desc (NOT Delete function as can be dups)
              move     KOR-offset (KOR-x1) to K
              move     KOR-length (KOR-x1) to L
*>
              move     spaces to WS-Where
              move     1   to J
              string   "`"                   delimited by size
                       KeyName (KOR-x1)      delimited by space
                       "`"                   delimited by size
                       " > "                 delimited by size
                       "000"                 delimited by size
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
*>                    TABLE=SYSTEM-REC
           INITIALIZE WS-MYSQL-COMMAND
           STRING "SELECT * FROM "
             "`SYSTEM-REC`"
             " WHERE "
             ws-Where (1:J)        *> SYSTEM-REC-KEY > "000" ORDER BY SYSTEM-REC ASC
            ";"  X"00" INTO WS-MYSQL-COMMAND
           PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
           PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
           MOVE WS-MYSQL-RESULT TO TP-SYSTEM-REC
*>               /MYSQL-END\
           move    ">000" to WS-File-Key
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
                       go to ba998-Free        *> can clear the dup code after testing
              end-if
              move     1 to Most-Cursor-Set    *> should test if select worked first??????
     end-if.
*>
*>  If here cursor is set, so get the next row
*>
     move     spaces to WS-Log-Where.
     move     4 to ws-No-Paragraph.
*>      /MYSQL FETCH\
*>
*>    Fetch next record
*>
*>             TABLE=SYSTEM-REC
           MOVE TP-SYSTEM-REC TO WS-MYSQL-RESULT
           CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT
                    HV-SYSTEM-REC-KEY
                    HV-SYSTEM-RECORD-VERSION-PRIME
                    HV-SYSTEM-RECORD-VERSION-SECON
                    HV-VAT-RATE-1
                    HV-VAT-RATE-2
                    HV-VAT-RATE-3
                    HV-VAT-RATE-4
                    HV-VAT-RATE-5
                    HV-CYCLEA
                    HV-PERIOD
                    HV-PAGE-LINES
                    HV-NEXT-INVOICE
                    HV-RUN-DAT
                    HV-START-DAT
                    HV-END-DAT
                    HV-SUSER
                    HV-USER-CODE
                    HV-ADDRESS-1
                    HV-ADDRESS-2
                    HV-ADDRESS-3
                    HV-ADDRESS-4
                    HV-POST-CODE
                    HV-COMPANY-EMAIL
                    HV-COUNTRY
                    HV-PRINT-SPOOL-NAME
                    HV-PASS-VALUE
                    HV-LEVEL-1
                    HV-LEVEL-2
                    HV-LEVEL-3
                    HV-LEVEL-4
                    HV-LEVEL-5
                    HV-LEVEL-6
                    HV-PASS-WORD
                    HV-HOST
                    HV-OP-SYSTEM
                    HV-CURRENT-QUARTER
                    HV-FILE-SYSTEM-USED
                    HV-FILE-DUPLICATES-IN-USE
                    HV-MAPS-SER
                    HV-DATE-FORM
                    HV-DATA-CAPTURE-USED
                    HV-RDBMS-DB-NAME
                    HV-RDBMS-USER
                    HV-RDBMS-PASSWD
                    HV-RDBMS-PORT
                    HV-RDBMS-HOST
                    HV-RDBMS-SOCKET
                    HV-VAT-REG-NUMBER
                    HV-PARAM-RESTRICT
                    HV-STATS-DATE-PERIOD
                    HV-P-C
                    HV-P-C-GROUPED
                    HV-P-C-LEVEL
                    HV-COMPS
                    HV-COMPS-ACTIVE
                    HV-M-V
                    HV-ARCH
                    HV-TRANS-PRINT
                    HV-TRANS-PRINTED
                    HV-HEADER-LEVEL
                    HV-SALES-RANGE
                    HV-PURCHASE-RANGE
                    HV-VAT
                    HV-BATCH-ID
                    HV-LEDGER-2ND-INDEX
                    HV-IRS-INSTEAD
                    HV-LEDGER-SEC
                    HV-UPDATES
                    HV-POSTINGS
                    HV-NEXT-BATCH
                    HV-EXTRA-CHARGE-AC
                    HV-VAT-AC
                    HV-PRINT-SPOOL-NAME2
                    HV-NEXT-FOLIO
                    HV-BL-PAY-AC
                    HV-P-CREDITORS
                    HV-BL-PURCH-AC
                    HV-GL-BL-PAY-AC
                    HV-GL-P-CREDITORS
                    HV-GL-BL-PURCH-AC
                    HV-GL-SL-PAY-AC
                    HV-GL-S-DEBTORS
                    HV-GL-SL-SALES-AC
                    HV-BL-END-CYCLE-DAT
                    HV-BL-NEXT-BATCH
                    HV-AGE-TO-PAY
                    HV-PURCHASE-LEDGER
                    HV-PL-DELIM
                    HV-ENTRY-LEVEL
                    HV-P-FLAG-A
                    HV-P-FLAG-I
                    HV-P-FLAG-P
                    HV-PL-STOCK-LINK
                    HV-PRINT-SPOOL-NAME3
                    HV-PL-AUTOGEN
                    HV-PL-NEXT-REC
                    HV-SALES-LEDGER
                    HV-SL-DELIM
                    HV-OI-3-FLAG
                    HV-CUST-FLAG
                    HV-OI-5-FLAG
                    HV-S-FLAG-OI-3
                    HV-FULL-INVOICING
                    HV-S-FLAG-A
                    HV-S-FLAG-I
                    HV-S-FLAG-P
                    HV-SL-DUNNING
                    HV-SL-CHARGES
                    HV-SL-OWN-NOS
                    HV-SL-STATS-RUN
                    HV-SL-DAY-BOOK
                    HV-INVOICER
                    HV-EXTRA-DESC
                    HV-EXTRA-TYPE
                    HV-EXTRA-PRINT
                    HV-SL-STOCK-LINK
                    HV-SL-STOCK-AUDIT
                    HV-SL-LATE-PER
                    HV-SL-DISC
                    HV-EXTRA-RATE
                    HV-SL-DAYS-1
                    HV-SL-DAYS-2
                    HV-SL-DAYS-3
                    HV-SL-CREDIT
                    HV-SL-MIN
                    HV-SL-MAX
                    HV-PF-RETENTION
                    HV-FIRST-SL-BATCH
                    HV-FIRST-SL-INV
                    HV-SL-LIMIT
                    HV-SL-PAY-AC
                    HV-S-DEBTORS
                    HV-SL-SALES-AC
                    HV-S-END-CYCLE-DAT
                    HV-SL-COMP-HEAD-PICK
                    HV-SL-COMP-HEAD-INV
                    HV-SL-COMP-HEAD-STAT
                    HV-SL-COMP-HEAD-LETS
                    HV-SL-VAT-PRINTED
                    HV-SL-INVOICE-LINES
                    HV-SL-AUTOGEN
                    HV-SL-NEXT-REC
                    HV-STK-ABREV-REF
                    HV-STK-DEBUG
                    HV-STK-MANU-USED
                    HV-STK-OE-USED
                    HV-STK-AUDIT-USED
                    HV-STK-MOV-AUDIT
                    HV-STK-PERIOD-CUR
                    HV-STK-PERIOD-DAT
                    HV-STOCK-CONTROL
                    HV-STK-AVERAGING
                    HV-STK-ACTIVITY-REP-RUN
                    HV-STK-PAGE-LINES
                    HV-STK-AUDIT-NO
                    HV-CLIENT
                    HV-NEXT-POST
                    HV-VAT1
                    HV-VAT2
                    HV-VAT3
                    HV-IRS-PASS-VALUE
                    HV-SAVE-SEQU
                    HV-SYSTEM-WORK-GROUP
                    HV-PL-APP-CREATED
                    HV-PL-APPROP-AC
                    HV-1ST-TIME-FLAG
                    HV-PL-APPROP-AC6
                    HV-SL-BO-FLAG
                    HV-STK-BO-ACTIVE

*>      /MYSQL-END\
     end-call
*>
     if       return-code = -1     *> no more data so free cursor & return
              move 10 to fs-Reply WE-Error
              move    "EOF" to WS-File-Key
              move     zero to Most-Cursor-Set
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
                    initialize System-Record with filler
                    move    "EOF2" to WS-File-Key
              end-if
              move     zero to Most-Cursor-Set
              go to ba999-End
     end-if.
*>
     if       fs-reply = 10                        *> belts and braces
              move     zero to Most-Cursor-Set
              move    "EOF3" to WS-File-Key
              go to ba999-End
     end-if.
*>
     perform  bb100-UnloadHVs.       *> transfer/move HV vars to Record layout
     move     HV-SYSTEM-REC-KEY to WS-File-Key.     *> check but should be 1
     move     zero to fs-reply WE-Error.
     go       to ba999-end.
*>
 ba070-Process-Write.
     move     zero to WS-Mysql-Time-Step
                      WS-SQL-Retry.
     perform  bb000-HV-Load.                       *>  move System-Record fields to HV fields
     move     1 to WS-File-Key.
     move     zero to FS-Reply WE-Error SQL-State.
     move     spaces to SQL-Msg.
     move     zeroes to SQL-Err.             *> 03/10/16
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
                    if    SQL-Err (1:4) = "1062" or = "1022"    *> Dup key (rec already present)
                       or Sql-State = "23000"  *> Dup key (rec already present)
                          move 22 to fs-reply
                    else
                          move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
                    end-if
              end-if
     end-if
>>D   display " Looking in for "
>>D   display  WS-MYSQL-COMMAND (1:240).
     go       to ba999-End.
*>
 ba090-Process-Rewrite.
     move     zero to WS-Mysql-Time-Step
                      WS-SQL-Retry.
     perform  bb000-HV-Load.       *> Load up the HV fields from table record in WS
     move     1 to WS-File-Key.

     move     zero to FS-Reply WE-Error SQL-State.
     move     spaces to SQL-Msg.
     move     zeroes to SQL-Err.             *> 03/10/16
*>
     move     17 to ws-No-Paragraph.
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
*>              System-Record (K:L)       delimited by size
              "1"                   delimited by size    *> its record 1
              '"'                   delimited by size
                      into WS-Where
                        with pointer J
     end-string
     move     WS-Where (1:J)   to WS-Log-Where.    *>  For test logging
     perform  bb300-Update.
*>
>>D   display " Looking in for "
>>D   display  WS-MYSQL-COMMAND (1:240).
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
     move     zero   to FS-Reply WE-Error SQL-State.
     move     zero   to SQL-Err.
     move     spaces to SQL-Msg.
     go       to ba999-End.
*>
 ba100-Bad-Function.
*>
*> Houston; We have a problem
*>
     move     990 to WE-Error.
     move     99 to Fs-Reply.
     go       to ba999-End.
*>
*> /MYSQL PRO\
 COPY "mysql-procedures.cpy".
*> /MYSQL-END\
*>
 ba998-Free.
     move     18 to ws-No-Paragraph.
*>      /MYSQL FREE\
*>
*>    Free result array
*>
*>             TABLE=SYSTEM-REC
           MOVE TP-SYSTEM-REC TO WS-MYSQL-RESULT
           CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
*>      /MYSQL-END\
     move     zero to Most-Cursor-Set.
*>
 ba999-End.
     if       Testing-1
              perform Ca-Process-Logs
     end-if.
     if       fn-close
              move zero to File-Function
                           Access-Type              *> close log file
              perform  Ca-Process-Logs
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
     initialize TD-SYSTEM-REC.
     move     1                       to HV-SYSTEM-REC-KEY
     move     System-Record-Version-Prime     to HV-SYSTEM-RECORD-VERSION-PRIME
     move     System-Record-Version-Secondary to HV-SYSTEM-RECORD-VERSION-SECON
     move     Vat-Rate-1              to HV-VAT-RATE-1
     move     Vat-Rate-2              to HV-VAT-RATE-2
     move     Vat-Rate-3              to HV-VAT-RATE-3
     move     Vat-Rate-4              to HV-VAT-RATE-4
     move     Vat-Rate-5              to HV-VAT-RATE-5
     move     Cyclea                  to HV-CYCLEA
     move     Period                  to HV-PERIOD
     move     Page-Lines              to HV-PAGE-LINES
     move     Next-Invoice            to HV-NEXT-INVOICE
     move     Run-Date                to HV-RUN-DAT
     move     Start-Date              to HV-START-DAT
     move     End-Date                to HV-END-DAT
     move     Suser                   to HV-SUSER
     move     User-Code               to HV-USER-CODE
     move     Address-1               to HV-ADDRESS-1
     move     Address-2               to HV-ADDRESS-2
     move     Address-3               to HV-ADDRESS-3
     move     Address-4               to HV-ADDRESS-4
     move     Post-Code               to HV-POST-CODE
     move     Country                 to HV-COUNTRY
     move     Print-Spool-Name        to HV-PRINT-SPOOL-NAME
     move     Pass-Value              to HV-PASS-VALUE
     move     Level-1                 to HV-LEVEL-1
     move     Level-2                 to HV-LEVEL-2
     move     Level-3                 to HV-LEVEL-3
     move     Level-4                 to HV-LEVEL-4
     move     Level-5                 to HV-LEVEL-5
     move     Level-6                 to HV-LEVEL-6
     move     Pass-Word               to HV-PASS-WORD
     move     Host                    to HV-HOST
     move     Op-System               to HV-OP-SYSTEM
     move     Current-Quarter         to HV-CURRENT-QUARTER
     move     File-System-Used        to HV-FILE-SYSTEM-USED
     move     File-Duplicates-In-Use  to HV-FILE-DUPLICATES-IN-USE
*>
*> SPECIAL
*>
     move     Maps-Ser-xx to  WS-Maps-xx
     move     Maps-Ser-nn to  WS-Maps-nn
     move     ws-Maps-Ser-x           to HV-MAPS-SER
*>
     move     Date-Form               to HV-DATE-FORM
     move     Data-Capture-Used       to HV-DATA-CAPTURE-USED
     move     RDBMS-DB-Name           to HV-RDBMS-DB-NAME
     move     RDBMS-User              to HV-RDBMS-USER
     move     RDBMS-Passwd            to HV-RDBMS-PASSWD
     move     RDBMS-Port              to HV-RDBMS-PORT
     move     RDBMS-Host              to HV-RDBMS-HOST
     move     RDBMS-Socket            to HV-RDBMS-SOCKET
     move     VAT-Reg-Number          to HV-VAT-REG-NUMBER
     move     Param-Restrict          to HV-PARAM-RESTRICT
     move     P-C                     to HV-P-C
     move     P-C-Grouped             to HV-P-C-GROUPED
     move     P-C-Level               to HV-P-C-LEVEL
     move     Comps                   to HV-COMPS
     move     Comps-Active            to HV-COMPS-ACTIVE
     move     M-V                     to HV-M-V
     move     Arch                    to HV-ARCH
     move     Trans-Print             to HV-TRANS-PRINT
     move     Trans-Printed           to HV-TRANS-PRINTED
     move     Header-Level            to HV-HEADER-LEVEL
     move     Sales-Range             to HV-SALES-RANGE
     move     Purchase-Range          to HV-PURCHASE-RANGE
     move     Vat                     to HV-VAT
     move     Batch-Id                to HV-BATCH-ID
     move     Ledger-2nd-Index        to HV-LEDGER-2ND-INDEX
     move     Irs-Instead             to HV-IRS-INSTEAD
     move     Ledger-Sec              to HV-LEDGER-SEC
     move     Updates                 to HV-UPDATES
     move     Postings                to HV-POSTINGS
     move     Next-Batch              to HV-NEXT-BATCH
     move     Extra-Charge-Ac         to HV-EXTRA-CHARGE-AC
     move     Vat-Ac                  to HV-VAT-AC
     move     Print-Spool-Name2       to HV-PRINT-SPOOL-NAME2
     move     Next-Folio              to HV-NEXT-FOLIO
     move     BL-Pay-Ac               to HV-BL-PAY-AC
     move     P-Creditors             to HV-P-CREDITORS
     move     BL-Purch-Ac             to HV-BL-PURCH-AC
     move     GL-BL-Pay-Ac            to HV-GL-BL-PAY-AC
     move     GL-P-Creditors          to HV-GL-P-CREDITORS
     move     GL-BL-Purch-Ac          to HV-GL-BL-PURCH-AC
     move     BL-End-Cycle-Date       to HV-BL-END-CYCLE-DAT
     move     BL-Next-Batch           to HV-BL-NEXT-BATCH
     move     Age-To-Pay              to HV-AGE-TO-PAY
     move     Purchase-Ledger         to HV-PURCHASE-LEDGER
     move     PL-Delim                to HV-PL-DELIM
     move     Entry-Level             to HV-ENTRY-LEVEL
     move     P-Flag-A                to HV-P-FLAG-A
     move     P-Flag-I                to HV-P-FLAG-I
     move     P-Flag-P                to HV-P-FLAG-P
     move     PL-Stock-Link           to HV-PL-STOCK-LINK
     move     Print-Spool-Name3       to HV-PRINT-SPOOL-NAME3
     move     Sales-Ledger            to HV-SALES-LEDGER
     move     SL-Delim                to HV-SL-DELIM
     move     Oi-3-Flag               to HV-OI-3-FLAG
     move     Cust-Flag               to HV-CUST-FLAG
     move     Oi-5-Flag               to HV-OI-5-FLAG
     move     S-Flag-Oi-3             to HV-S-FLAG-OI-3
     move     Full-Invoicing          to HV-FULL-INVOICING
     move     S-Flag-A                to HV-S-FLAG-A
     move     S-Flag-I                to HV-S-FLAG-I
     move     S-Flag-P                to HV-S-FLAG-P
     move     SL-Dunning              to HV-SL-DUNNING
     move     SL-Charges              to HV-SL-CHARGES
     move     Sl-Own-Nos              to HV-SL-OWN-NOS
     move     SL-Stats-Run            to HV-SL-STATS-RUN
     move     Sl-Day-Book             to HV-SL-DAY-BOOK
     move     invoicer                to HV-INVOICER
     move     Extra-Desc              to HV-EXTRA-DESC
     move     Extra-Type              to HV-EXTRA-TYPE
     move     Extra-Print             to HV-EXTRA-PRINT
     move     SL-Stock-Link           to HV-SL-STOCK-LINK
     move     SL-Stock-Audit          to HV-SL-STOCK-AUDIT
     move     SL-Late-Per             to HV-SL-LATE-PER
     move     SL-Disc                 to HV-SL-DISC
     move     Extra-Rate              to HV-EXTRA-RATE
     move     SL-Days-1               to HV-SL-DAYS-1
     move     SL-Days-2               to HV-SL-DAYS-2
     move     SL-Days-3               to HV-SL-DAYS-3
     move     SL-Credit               to HV-SL-CREDIT
     move     SL-Min                  to HV-SL-MIN
     move     SL-Max                  to HV-SL-MAX
     move     SL-Invoice-Lines        to HV-SL-Invoice-Lines
     move     PF-Retention            to HV-PF-RETENTION
     move     First-Sl-Batch          to HV-FIRST-SL-BATCH
     move     First-Sl-Inv            to HV-FIRST-SL-INV
     move     SL-Limit                to HV-SL-LIMIT
     move     SL-Autogen              to HV-SL-AUTOGEN   *> 3 new ones 13/03/24
     move     SL-Next-Rec             to HV-SL-NEXT-REC
     move     SL-BO-Flag              to HV-SL-BO-FLAG
     move     SL-Pay-Ac               to HV-SL-PAY-AC
     move     S-Debtors               to HV-S-DEBTORS
     move     SL-Sales-Ac             to HV-SL-SALES-AC
     move     SL-Pay-Ac               to HV-SL-PAY-AC
     move     GL-S-Debtors            to HV-GL-S-DEBTORS
     move     GL-SL-Sales-Ac          to HV-GL-SL-SALES-AC
     move     GL-SL-Pay-Ac            to HV-GL-SL-PAY-AC
     move     S-End-Cycle-Date        to HV-S-END-CYCLE-DAT
     move     SL-Comp-Head-Pick       to HV-SL-COMP-HEAD-PICK
     move     SL-Comp-Head-Inv        to HV-SL-COMP-HEAD-INV
     move     SL-Comp-Head-Stat       to HV-SL-COMP-HEAD-STAT
     move     SL-Comp-Head-Lets       to HV-SL-COMP-HEAD-LETS
     move     SL-VAT-Printed          to HV-SL-VAT-PRINTED
     move     Stk-Abrev-Ref           to HV-STK-ABREV-REF
     move     Stk-Debug               to HV-STK-DEBUG
     move     Stk-Manu-Used           to HV-STK-MANU-USED
     move     Stk-OE-Used             to HV-STK-OE-USED
     move     Stk-Audit-Used          to HV-STK-AUDIT-USED
     move     Stk-Mov-Audit           to HV-STK-MOV-AUDIT
     move     Stk-Period-Cur          to HV-STK-PERIOD-CUR
     move     Stk-Period-dat          to HV-STK-PERIOD-DAT
     move     Stock-Control           to HV-STOCK-CONTROL
     move     Stk-Averaging           to HV-STK-AVERAGING
     move     Stk-Activity-Rep-Run    to HV-STK-ACTIVITY-REP-RUN
     move     Stk-Page-Lines          to HV-STK-PAGE-LINES
     move     Stk-Audit-No            to HV-STK-AUDIT-NO
     MOVE     Stk-BO-Active           TO HV-STK-BO-ACTIVE
     move     Client                  to HV-CLIENT
     move     Next-Post               to HV-NEXT-POST
     move     vat1                    to HV-VAT1
     move     vat2                    to HV-VAT2
     move     vat3                    to HV-VAT3
     move     IRS-Pass-Value          to HV-IRS-PASS-VALUE
     move     save-sequ               to HV-SAVE-SEQU
     move     system-work-group       to HV-SYSTEM-WORK-GROUP
     move     PL-App-Created          to HV-PL-APP-CREATED
     move     PL-Approp-AC            to HV-PL-APPROP-AC
     move     1st-Time-Flag           to HV-1ST-TIME-FLAG.
*>
 bb000-Exit.
     exit section.
*>
 bb100-UnloadHVs    Section.
*>*************************
*>
*>  Load the data buffer in the interface with data from the host variables.
*>
*> NULL fields must not be returned in the buffer. SQL filters each column to
*>  ensure it has a proper value.  This saves using indicator variables.
*>
     initialize System-Record with filler.
*>
*>     move     HV-SYSTEM-REC-KEY  not wanted and is always 1
*>
     move     HV-SYSTEM-RECORD-VERSION-PRIME  to System-Record-Version-Prime
     move     HV-SYSTEM-RECORD-VERSION-SECON  to System-Record-Version-Secondary
     move     HV-VAT-RATE-1                   to Vat-Rate-1
     move     HV-VAT-RATE-2                   to Vat-Rate-2
     move     HV-VAT-RATE-3                   to Vat-Rate-3
     move     HV-VAT-RATE-4                   to Vat-Rate-4
     move     HV-VAT-RATE-5                   to Vat-Rate-5
     move     HV-CYCLEA                       to Cyclea
     move     HV-PERIOD                       to Period
     move     HV-PAGE-LINES                   to Page-Lines
     move     HV-NEXT-INVOICE                 to Next-Invoice
     move     HV-RUN-DAT                      to Run-Date
     move     HV-START-DAT                    to Start-Date
     move     HV-END-DAT                      to End-Date
     move     HV-SUSER                        to Suser
     move     HV-USER-CODE                    to User-Code
     move     HV-ADDRESS-1                    to Address-1
     move     HV-ADDRESS-2                    to Address-2
     move     HV-ADDRESS-3                    to Address-3
     move     HV-ADDRESS-4                    to Address-4
     move     HV-POST-CODE                    to Post-Code
     move     HV-COUNTRY                      to Country
     move     HV-PRINT-SPOOL-NAME             to Print-Spool-Name
     move     HV-PASS-VALUE                   to Pass-Value
     move     HV-LEVEL-1                      to Level-1
     move     HV-LEVEL-2                      to Level-2
     move     HV-LEVEL-3                      to Level-3
     move     HV-LEVEL-4                      to Level-4
     move     HV-LEVEL-5                      to Level-5
     move     HV-LEVEL-6                      to Level-6
     move     HV-PASS-WORD                    to Pass-Word
     move     HV-HOST                         to Host
     move     HV-OP-SYSTEM                    to Op-System
     move     HV-CURRENT-QUARTER              to Current-Quarter
     move     HV-FILE-SYSTEM-USED             to File-System-Used
     move     HV-FILE-DUPLICATES-IN-USE       to File-Duplicates-In-Use
*>
*> SPECIAL
*>
     move     HV-MAPS-SER  to ws-Maps-Ser-x
     move     ws-Maps-xx  to Maps-Ser-xx
     move     WS-Maps-nn  to Maps-Ser-nn
*>
     move     HV-DATE-FORM                    to Date-Form
     move     HV-DATA-CAPTURE-USED            to Data-Capture-Used
     move     HV-RDBMS-DB-NAME                to RDBMS-DB-Name
     move     HV-RDBMS-USER                   to RDBMS-User
     move     HV-RDBMS-PASSWD                 to RDBMS-Passwd
     move     HV-RDBMS-PORT                   to RDBMS-Port
     move     HV-RDBMS-HOST                   to RDBMS-Host
     move     HV-RDBMS-SOCKET                 to RDBMS-Socket
     move     HV-VAT-REG-NUMBER               to VAT-Reg-Number
     move     HV-PARAM-RESTRICT               to Param-Restrict
     move     HV-P-C                          to P-C
     move     HV-P-C-GROUPED                  to P-C-Grouped
     move     HV-P-C-LEVEL                    to P-C-Level
     move     HV-COMPS                        to Comps
     move     HV-COMPS-ACTIVE                 to Comps-Active
     move     HV-M-V                          to M-V
     move     HV-ARCH                         to Arch
     move     HV-TRANS-PRINT                  to Trans-Print
     move     HV-TRANS-PRINTED                to Trans-Printed
     move     HV-HEADER-LEVEL                 to Header-Level
     move     HV-SALES-RANGE                  to Sales-Range
     move     HV-PURCHASE-RANGE               to Purchase-Range
     move     HV-VAT                          to Vat
     move     HV-BATCH-ID                     to Batch-Id
     move     HV-LEDGER-2ND-INDEX             to Ledger-2nd-Index
     move     HV-IRS-INSTEAD                  to Irs-Instead
     move     HV-LEDGER-SEC                   to Ledger-Sec
     move     HV-UPDATES                      to Updates
     move     HV-POSTINGS                     to Postings
     move     HV-NEXT-BATCH                   to Next-Batch
     move     HV-EXTRA-CHARGE-AC              to Extra-Charge-Ac
     move     HV-VAT-AC                       to Vat-Ac
     move     HV-PRINT-SPOOL-NAME2            to Print-Spool-Name2
     move     HV-NEXT-FOLIO                   to Next-Folio
     move     HV-BL-PAY-AC                    to BL-Pay-Ac
     move     HV-P-CREDITORS                  to P-Creditors
     move     HV-BL-PURCH-AC                  to BL-Purch-Ac
     move     HV-GL-BL-PAY-AC                 to GL-BL-Pay-Ac
     move     HV-GL-P-CREDITORS               to GL-P-Creditors
     move     HV-GL-BL-PURCH-AC               to GL-BL-Purch-Ac
     move     HV-BL-END-CYCLE-DAT             to BL-End-Cycle-Date
     move     HV-BL-NEXT-BATCH                to BL-Next-Batch
     move     HV-AGE-TO-PAY                   to Age-To-Pay
     move     HV-PURCHASE-LEDGER              to Purchase-Ledger
     move     HV-PL-DELIM                     to PL-Delim
     move     HV-ENTRY-LEVEL                  to Entry-Level
     move     HV-P-FLAG-A                     to P-Flag-A
     move     HV-P-FLAG-I                     to P-Flag-I
     move     HV-P-FLAG-P                     to P-Flag-P
     move     HV-PL-STOCK-LINK                to PL-Stock-Link
     move     HV-PRINT-SPOOL-NAME3            to Print-Spool-Name3
     move     HV-SALES-LEDGER                 to Sales-Ledger
     move     HV-SL-DELIM                     to SL-Delim
     move     HV-OI-3-FLAG                    to Oi-3-Flag
     move     HV-CUST-FLAG                    to Cust-Flag
     move     HV-OI-5-FLAG                    to Oi-5-Flag
     move     HV-S-FLAG-OI-3                  to S-Flag-Oi-3
     move     HV-FULL-INVOICING               to Full-Invoicing
     move     HV-S-FLAG-A                     to S-Flag-A
     move     HV-S-FLAG-I                     to S-Flag-I
     move     HV-S-FLAG-P                     to S-Flag-P
     move     HV-SL-DUNNING                   to SL-Dunning
     move     HV-SL-CHARGES                   to SL-Charges
     move     HV-SL-OWN-NOS                   to Sl-Own-Nos
     move     HV-SL-STATS-RUN                 to SL-Stats-Run
     move     HV-SL-DAY-BOOK                  to Sl-Day-Book
     move     HV-INVOICER                     to invoicer
     move     HV-EXTRA-DESC                   to Extra-Desc
     move     HV-EXTRA-TYPE                   to Extra-Type
     move     HV-EXTRA-PRINT                  to Extra-Print
     move     HV-SL-STOCK-LINK                to SL-Stock-Link
     move     HV-SL-STOCK-AUDIT               to SL-Stock-Audit
     move     HV-SL-LATE-PER                  to SL-Late-Per
     move     HV-SL-DISC                      to SL-Disc
     move     HV-EXTRA-RATE                   to Extra-Rate
     move     HV-SL-DAYS-1                    to SL-Days-1
     move     HV-SL-DAYS-2                    to SL-Days-2
     move     HV-SL-DAYS-3                    to SL-Days-3
     move     HV-SL-CREDIT                    to SL-Credit
     move     HV-SL-MIN                       to SL-Min
     move     HV-SL-MAX                       to SL-Max
     move     HV-SL-Invoice-Lines             to SL-Invoice-Lines
     move     HV-PF-RETENTION                 to PF-Retention
     move     HV-FIRST-SL-BATCH               to First-Sl-Batch
     move     HV-FIRST-SL-INV                 to First-Sl-Inv
     move     HV-SL-LIMIT                     to SL-Limit
     move     HV-SL-AUTOGEN                   to  SL-Autogen    *> 3 new ones 13/03/24
     move     HV-SL-NEXT-REC                  to  SL-Next-Rec
     move     HV-SL-BO-FLAG                   to  SL-BO-Flag
     move     HV-SL-PAY-AC                    to SL-Pay-Ac
     move     HV-S-DEBTORS                    to S-Debtors
     move     HV-SL-SALES-AC                  to SL-Sales-Ac
     move     HV-GL-SL-PAY-AC                 to GL-SL-Pay-Ac
     move     HV-GL-S-DEBTORS                 to GL-S-Debtors
     move     HV-GL-SL-SALES-AC               to GL-SL-Sales-Ac
     move     HV-S-END-CYCLE-DAT              to S-End-Cycle-Date
     move     HV-SL-COMP-HEAD-PICK            to SL-Comp-Head-Pick
     move     HV-SL-COMP-HEAD-INV             to SL-Comp-Head-Inv
     move     HV-SL-COMP-HEAD-STAT            to SL-Comp-Head-Stat
     move     HV-SL-COMP-HEAD-LETS            to SL-Comp-Head-Lets
     move     HV-SL-VAT-PRINTED               to SL-VAT-Printed
     move     HV-STK-ABREV-REF                to Stk-Abrev-Ref
     move     HV-STK-DEBUG                    to Stk-Debug
     move     HV-STK-MANU-USED                to Stk-Manu-Used
     move     HV-STK-OE-USED                  to Stk-OE-Used
     move     HV-STK-AUDIT-USED               to Stk-Audit-Used
     move     HV-STK-MOV-AUDIT                to Stk-Mov-Audit
     move     HV-STK-PERIOD-CUR               to Stk-Period-Cur
     move     HV-STK-PERIOD-DAT               to Stk-Period-dat
     move     HV-STOCK-CONTROL                to Stock-Control
     move     HV-STK-AVERAGING                to Stk-Averaging
     move     HV-STK-ACTIVITY-REP-RUN         to Stk-Activity-Rep-Run
     move     HV-STK-PAGE-LINES               to Stk-Page-Lines
     move     HV-STK-AUDIT-NO                 to Stk-Audit-No
     move     HV-STK-BO-ACTIVE                to Stk-BO-Active
     move     HV-CLIENT                       to Client
     move     HV-NEXT-POST                    to Next-Post
     move     HV-VAT1                         to vat1
     move     HV-VAT2                         to vat2
     move     HV-VAT3                         to vat3
     move     HV-IRS-PASS-VALUE               to IRS-Pass-Value
     move     HV-SAVE-SEQU                    to save-sequ
     move     HV-SYSTEM-WORK-GROUP            to system-work-group
     move     HV-PL-APP-CREATED               to PL-App-Created
     move     HV-PL-APPROP-AC                 to PL-Approp-AC
     move     HV-1ST-TIME-FLAG                to 1st-Time-Flag.
*>
 bb100-Exit.
     exit section.
*>
 bb200-Insert Section.
*>*******************
*>
*>     move     zero to WS-Mysql-Time-Step
  *>                    WS-Mysql-Wait-Time
    *>                  WS-Mysql-Wait-Total.
*>  /MYSQL INSERT\
*>
*>    Insert a row
*>
*>         TABLE=SYSTEM-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'INSERT INTO '
                    '`SYSTEM-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-REC-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SYSTEM-REC-KEY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-RECORD-VERSION-PRIME`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SYSTEM-RECORD-VERSION-PRIME
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-RECORD-VERSION-SECONDAR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SYSTEM-RECORD-VERSION-SECON
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-RATE-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-5`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-5
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`CYCLEA`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-CYCLEA
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PERIOD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PERIOD
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAGE-LINES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAGE-LINES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-INVOICE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RUN-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-RUN-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`START-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-START-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`END-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-END-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SUSER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SUSER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`USER-CODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-USER-CODE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-1,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-2,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-3,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-4,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST-CODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST-CODE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COMPANY-EMAIL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COMPANY-EMAIL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COUNTRY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COUNTRY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PRINT-SPOOL-NAME`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PRINT-SPOOL-NAME,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PASS-VALUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PASS-VALUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-5`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-5
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-6`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-6
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PASS-WORD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PASS-WORD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`HOST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-HOST
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OP-SYSTEM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OP-SYSTEM
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`CURRENT-QUARTER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-CURRENT-QUARTER
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FILE-SYSTEM-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FILE-SYSTEM-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FILE-DUPLICATES-IN-USE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FILE-DUPLICATES-IN-USE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`MAPS-SER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-MAPS-SER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`DATE-FORM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-DATE-FORM
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`DATA-CAPTURE-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-DATA-CAPTURE-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-DB-NAME`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-DB-NAME,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-USER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-USER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-PASSWD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-PASSWD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-PORT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-PORT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-HOST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-HOST,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-SOCKET`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-SOCKET,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-REG-NUMBER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-VAT-REG-NUMBER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PARAM-RESTRICT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PARAM-RESTRICT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STATS-DATE-PERIOD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STATS-DATE-PERIOD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-C`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-P-C,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-C-GROUPED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-P-C-GROUPED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-C-LEVEL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-P-C-LEVEL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COMPS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COMPS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COMPS-ACTIVE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COMPS-ACTIVE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`M-V`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-M-V,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ARCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ARCH,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`TRANS-PRINT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-TRANS-PRINT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`TRANS-PRINTED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-TRANS-PRINTED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`HEADER-LEVEL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-HEADER-LEVEL
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SALES-RANGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SALES-RANGE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PURCHASE-RANGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PURCHASE-RANGE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-VAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BATCH-ID`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-BATCH-ID,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEDGER-2ND-INDEX`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-LEDGER-2ND-INDEX,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-INSTEAD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-IRS-INSTEAD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEDGER-SEC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEDGER-SEC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`UPDATES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-UPDATES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POSTINGS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POSTINGS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-BATCH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-CHARGE-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-EXTRA-CHARGE-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PRINT-SPOOL-NAME2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PRINT-SPOOL-NAME2,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-FOLIO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-FOLIO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-CREDITORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-CREDITORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-PURCH-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-PURCH-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-BL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-BL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-P-CREDITORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-P-CREDITORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-BL-PURCH-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-BL-PURCH-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-SL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-SL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-S-DEBTORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-S-DEBTORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-SL-SALES-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-SL-SALES-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-END-CYCLE-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-END-CYCLE-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-NEXT-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-NEXT-BATCH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AGE-TO-PAY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AGE-TO-PAY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PURCHASE-LEDGER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PURCHASE-LEDGER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-DELIM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-DELIM,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ENTRY-LEVEL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-ENTRY-LEVEL
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-FLAG-A`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-FLAG-A
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-FLAG-I`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-FLAG-I
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-FLAG-P`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-FLAG-P
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-STOCK-LINK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-STOCK-LINK,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PRINT-SPOOL-NAME3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PRINT-SPOOL-NAME3,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-AUTOGEN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-AUTOGEN,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-NEXT-REC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PL-NEXT-REC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SALES-LEDGER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SALES-LEDGER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DELIM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-DELIM,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI-3-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI-3-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`CUST-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-CUST-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI-5-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI-5-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-OI-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-S-FLAG-OI-3,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FULL-INVOICING`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FULL-INVOICING
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-A`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-FLAG-A
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-I`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-FLAG-I
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-P`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-FLAG-P
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DUNNING`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DUNNING
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-CHARGES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-CHARGES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-OWN-NOS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-OWN-NOS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-STATS-RUN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-STATS-RUN
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DAY-BOOK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAY-BOOK
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`INVOICER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-INVOICER
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-DESC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-EXTRA-DESC,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-TYPE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-EXTRA-TYPE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-PRINT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-EXTRA-PRINT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-STOCK-LINK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-STOCK-LINK,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-STOCK-AUDIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-STOCK-AUDIT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-LATE-PER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-LATE-PER
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`SL-DISC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DISC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`EXTRA-RATE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-EXTRA-RATE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`SL-DAYS-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAYS-1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DAYS-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAYS-2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DAYS-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAYS-3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-CREDIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-CREDIT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-MIN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-MIN
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-MAX`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-MAX
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PF-RETENTION`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PF-RETENTION
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FIRST-SL-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FIRST-SL-BATCH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FIRST-SL-INV`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FIRST-SL-INV
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-LIMIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-LIMIT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-DEBTORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-DEBTORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-SALES-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-SALES-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-END-CYCLE-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-END-CYCLE-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-PICK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-PICK,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-INV`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-INV,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-STAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-STAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-LETS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-LETS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-VAT-PRINTED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-VAT-PRINTED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-INVOICE-LINES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-INVOICE-LINES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-AUTOGEN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-AUTOGEN,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-NEXT-REC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-NEXT-REC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-ABREV-REF`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-ABREV-REF,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-DEBUG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-DEBUG
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-MANU-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-MANU-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-OE-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-OE-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-AUDIT-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-AUDIT-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-MOV-AUDIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-MOV-AUDIT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-PERIOD-CUR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-PERIOD-CUR,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-PERIOD-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-PERIOD-DAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STOCK-CONTROL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STOCK-CONTROL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-AVERAGING`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-AVERAGING
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-ACTIVITY-REP-RUN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-ACTIVITY-REP-RUN
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-PAGE-LINES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-PAGE-LINES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-AUDIT-NO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-AUDIT-NO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`CLIENT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-CLIENT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-POST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-POST
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`IRS-PASS-VALUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-IRS-PASS-VALUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SAVE-SEQU`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SAVE-SEQU
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-WORK-GROUP`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SYSTEM-WORK-GROUP,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-APP-CREATED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-APP-CREATED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-APPROP-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PL-APPROP-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`1ST-TIME-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-1ST-TIME-FLAG
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-APPROP-AC6`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PL-APPROP-AC6
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-BO-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-BO-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-BO-ACTIVE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-BO-ACTIVE,TRAILING)
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
 *>    move     zero to WS-Mysql-Time-Step
   *>                   WS-Mysql-Wait-Time
     *>                 WS-Mysql-Wait-Total.
*>  /MYSQL UPDATE\
*>
*>    Update a row
*>
*>      TABLE=SYSTEM-REC
           INITIALIZE WS-MYSQL-COMMAND
           MOVE 1 TO WS-MYSQL-I
           STRING 'UPDATE '
                    '`SYSTEM-REC` SET '
              INTO WS-MYSQL-COMMAND
              WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-REC-KEY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SYSTEM-REC-KEY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-RECORD-VERSION-PRIME`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SYSTEM-RECORD-VERSION-PRIME
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-RECORD-VERSION-SECONDAR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SYSTEM-RECORD-VERSION-SECON
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-RATE-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT-RATE-5`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-RATE-5
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`CYCLEA`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-CYCLEA
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PERIOD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PERIOD
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PAGE-LINES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PAGE-LINES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-INVOICE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-INVOICE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RUN-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-RUN-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`START-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-START-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`END-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-END-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SUSER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SUSER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`USER-CODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-USER-CODE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-1,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-2,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-3,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ADDRESS-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ADDRESS-4,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POST-CODE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-POST-CODE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COMPANY-EMAIL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COMPANY-EMAIL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COUNTRY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COUNTRY,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PRINT-SPOOL-NAME`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PRINT-SPOOL-NAME,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PASS-VALUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PASS-VALUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-4`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-4
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-5`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-5
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEVEL-6`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEVEL-6
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PASS-WORD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PASS-WORD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`HOST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-HOST
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OP-SYSTEM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-OP-SYSTEM
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`CURRENT-QUARTER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-CURRENT-QUARTER
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FILE-SYSTEM-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FILE-SYSTEM-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FILE-DUPLICATES-IN-USE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FILE-DUPLICATES-IN-USE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`MAPS-SER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-MAPS-SER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`DATE-FORM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-DATE-FORM
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`DATA-CAPTURE-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-DATA-CAPTURE-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-DB-NAME`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-DB-NAME,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-USER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-USER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-PASSWD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-PASSWD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-PORT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-PORT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-HOST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-HOST,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`RDBMS-SOCKET`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-RDBMS-SOCKET,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-REG-NUMBER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-VAT-REG-NUMBER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PARAM-RESTRICT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PARAM-RESTRICT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STATS-DATE-PERIOD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STATS-DATE-PERIOD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-C`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-P-C,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-C-GROUPED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-P-C-GROUPED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-C-LEVEL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-P-C-LEVEL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COMPS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COMPS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`COMPS-ACTIVE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-COMPS-ACTIVE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`M-V`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-M-V,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ARCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-ARCH,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`TRANS-PRINT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-TRANS-PRINT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`TRANS-PRINTED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-TRANS-PRINTED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`HEADER-LEVEL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-HEADER-LEVEL
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SALES-RANGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SALES-RANGE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PURCHASE-RANGE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PURCHASE-RANGE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-VAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BATCH-ID`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-BATCH-ID,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEDGER-2ND-INDEX`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-LEDGER-2ND-INDEX,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`IRS-INSTEAD`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-IRS-INSTEAD,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`LEDGER-SEC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-LEDGER-SEC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`UPDATES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-UPDATES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`POSTINGS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-POSTINGS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-BATCH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-CHARGE-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-EXTRA-CHARGE-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PRINT-SPOOL-NAME2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PRINT-SPOOL-NAME2,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-FOLIO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-FOLIO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-CREDITORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-CREDITORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-PURCH-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-PURCH-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-BL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-BL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-P-CREDITORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-P-CREDITORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-BL-PURCH-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-BL-PURCH-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-SL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-SL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-S-DEBTORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-S-DEBTORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`GL-SL-SALES-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-GL-SL-SALES-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-END-CYCLE-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-END-CYCLE-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`BL-NEXT-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-BL-NEXT-BATCH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`AGE-TO-PAY`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-AGE-TO-PAY
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PURCHASE-LEDGER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PURCHASE-LEDGER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-DELIM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-DELIM,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`ENTRY-LEVEL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-ENTRY-LEVEL
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-FLAG-A`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-FLAG-A
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-FLAG-I`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-FLAG-I
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`P-FLAG-P`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-P-FLAG-P
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-STOCK-LINK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-STOCK-LINK,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PRINT-SPOOL-NAME3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PRINT-SPOOL-NAME3,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-AUTOGEN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-AUTOGEN,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-NEXT-REC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PL-NEXT-REC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SALES-LEDGER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SALES-LEDGER,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DELIM`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-DELIM,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI-3-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI-3-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`CUST-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-CUST-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`OI-5-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-OI-5-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-OI-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-S-FLAG-OI-3,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FULL-INVOICING`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FULL-INVOICING
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-A`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-FLAG-A
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-I`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-FLAG-I
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-FLAG-P`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-FLAG-P
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DUNNING`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DUNNING
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-CHARGES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-CHARGES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-OWN-NOS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-OWN-NOS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-STATS-RUN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-STATS-RUN
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DAY-BOOK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAY-BOOK
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`INVOICER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-INVOICER
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-DESC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-EXTRA-DESC,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-TYPE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-EXTRA-TYPE,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`EXTRA-PRINT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-EXTRA-PRINT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-STOCK-LINK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-STOCK-LINK,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-STOCK-AUDIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-STOCK-AUDIT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-LATE-PER`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-LATE-PER
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`SL-DISC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DISC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`EXTRA-RATE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-EXTRA-RATE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`SL-DAYS-1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAYS-1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DAYS-2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAYS-2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-DAYS-3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-DAYS-3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-CREDIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-CREDIT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-MIN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-MIN
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-MAX`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-MAX
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PF-RETENTION`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PF-RETENTION
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FIRST-SL-BATCH`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FIRST-SL-BATCH
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`FIRST-SL-INV`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-FIRST-SL-INV
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-LIMIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-LIMIT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-PAY-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-PAY-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-DEBTORS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-DEBTORS
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-SALES-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-SALES-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`S-END-CYCLE-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-S-END-CYCLE-DAT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(11:10))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-PICK`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-PICK,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-INV`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-INV,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-STAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-STAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-COMP-HEAD-LETS`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-COMP-HEAD-LETS,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-VAT-PRINTED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-VAT-PRINTED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-INVOICE-LINES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-INVOICE-LINES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-AUTOGEN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-AUTOGEN,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-NEXT-REC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SL-NEXT-REC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(16:05))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-ABREV-REF`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-ABREV-REF,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-DEBUG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-DEBUG
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-MANU-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-MANU-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-OE-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-OE-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-AUDIT-USED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-AUDIT-USED
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-MOV-AUDIT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-MOV-AUDIT
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-PERIOD-CUR`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-PERIOD-CUR,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-PERIOD-DAT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-PERIOD-DAT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STOCK-CONTROL`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STOCK-CONTROL,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-AVERAGING`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-AVERAGING
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-ACTIVITY-REP-RUN`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-ACTIVITY-REP-RUN
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-PAGE-LINES`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-PAGE-LINES
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-AUDIT-NO`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-STK-AUDIT-NO
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`CLIENT`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-CLIENT,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`NEXT-POST`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-NEXT-POST
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`VAT1`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT1
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT2`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT2
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`VAT3`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-VAT3
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(19:02))
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
           STRING '`IRS-PASS-VALUE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-IRS-PASS-VALUE
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SAVE-SEQU`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-SAVE-SEQU
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SYSTEM-WORK-GROUP`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SYSTEM-WORK-GROUP,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-APP-CREATED`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-PL-APP-CREATED,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-APPROP-AC`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PL-APPROP-AC
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`1ST-TIME-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-1ST-TIME-FLAG
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`PL-APPROP-AC6`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           MOVE HV-PL-APPROP-AC6
             TO WS-MYSQL-EDIT
           STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08))
             INTO WS-MYSQL-COMMAND
             WITH POINTER WS-MYSQL-I end-string
           STRING '"' INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`SL-BO-FLAG`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-SL-BO-FLAG,TRAILING)
                  '"'
                   INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING ', 'INTO WS-MYSQL-COMMAND
           WITH POINTER WS-MYSQL-I end-string
*>
           STRING '`STK-BO-ACTIVE`="' INTO WS-MYSQL-COMMAND
                   WITH POINTER WS-MYSQL-I end-string
           STRING FUNCTION TRIM (HV-STK-BO-ACTIVE,TRAILING)
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
 end program systemMT.
