       >>source free
*>********************************************
*>                                           *
*>  Get the ACAS RDBMS Params file contents  *
*>    storing in linkage area                *
*>                                           *
*>********************************************
*>
 identification division.
 program-id.             acas-get-params.
*>**
*>   author.             Vincent Bryan Coen, FBCS, FIDM, FIDPM, CPL.
*>                       For Applewood Computers.
*>**
*>   Security.           Copyright (C) 2023 - 2026 & later, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>   Remarks.            Used for ACAS v3.02 and later to load up
*>                       the rdbms params from acas.param file.
*>                       For use if the acas parameter file system.dat
*>                       does not current hold settings for RDB processing
*>                       so that the *LD programs can load up the tables from
*>                       the Cobol files.
*>
*> Processing:
*>
*>                       Called by any and all *LD modules as require via linkage;
*>
*>                       Uses Current directory only.
*>
*>                       If system.dat does not hold RDBMS params we check if
*>                       file acas.param exists and if so takes details from that.
*>                       JIC not testing for RDB but it exists etc - saves having
*>                       to change system.dat record just for loading DB's.
*>
*> Returns:
*>  Normal =
*>                       0 = Valid data read.
*>                       8 = No file found.
*>  Errors -
*>                       1 = No valid keyword terminator i.e., = or :
*>                       2 = Invalid Keyword - keyword not expected.
*>
*>**
*>   Version.            See prog-name in Ws.
*>**
*>   Called Modules.     NONE.
*>**
*>   Error messages used.
*>                       NONE.
*>**
*>   Changes.
*> 21/06/23 vbc - .00 Module creation.
*> 16/04/24 vbc       Copyright notice update superceding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>**
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supercedes all prior copyright notices & was updated 2024-04-16.
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
*>
 environment division.
*>===================
*>
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
     select OPTIONAL ACAS-Params  assign "acas.param"
                                  organisation line sequential
                                  status  FS-Reply.
*>
 data division.
*>============
*>
 file section.
*>-----------
*>
*> Format :  Keyword=variable - simple
*>
 FD  ACAS-Params
     recording mode variable.
*>
 01  ACAS-Params-Record  pic x(80).
*>
*> Thrse are NOT used in program - just to show record layout
*>
 01  APR-Variable-Size.
     03  APR-Keyword     pic x(8).   *> Varying between 6 and 8.
     03  APR-Equals      pic x.      *> always '='.
     03  APR-Value       pic x(64).  *>< variable size
*>
 working-storage section.
*>----------------------
 77  prog-name           pic x(20)    value "get-params (3.3.00)".
 77  FS-Reply            pic 99.
*>
 01  WS-RDB-Data.                           *> Temp data
     03  WS-RDB-Keyword  pic x(8).
     03  WS-RDB-Equal    pic x.
     03  WS-RDB-Value    pic x(64).
*>
 01  File-Info                        value zero.  *> Layout as per GNU v2 manual
     05 File-Size-Bytes  pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp.    *> Mod date.
     05 Mod-MO           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp.    *> Mod time
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp.    *> Always 00
*>
 linkage section.
*>--------------
*>
 01  LK-Return           pic 99       value zero.
*>
 01  LK-RDB-Vars                      value spaces.
     03  LK-Host-Name    pic x(64).
     03  LK-Implementation
                         pic x(64).
     03  LK-Password     pic x(64).
     03  LK-Base-Name    pic x(64).
     03  LK-Port-Number  pic x(4).
     03  LK-Socket       pic x(64).
*>
 procedure division using LK-Return
                          LK-RDB-Vars.
*>===================================
*>
 aa000-Main.
*>
*>*************************************************************************
*>  WOULD normally need cobmysqlapi39.c for Mysql & Mariadb DB handling.  *
*>  How ever done the hard way so this module is not dependent on other   *
*>    processes similar to as used for mysql/mariadb cobmysqlapi.         *
*>*************************************************************************
*>
     move     zero  to LK-Return.
     call     "CBL_CHECK_FILE_EXIST" using "acas.param"
                                           File-Info.
     if       Return-Code not = zero        *> = zero - file found
              move     8 to LK-Return
              goback.
*>
     initialise
              LK-RDB-Vars
              LK-Return.
     open     input ACAS-Params.
     perform  until FS-Reply not = zeros
              read     ACAS-Params at end
                       exit perform
              end-read
              if       FS-Reply not = zeros    *> JIC
                       exit perform
              end-if
              initialise
                       WS-RDB-Data
              unstring ACAS-Params-Record delimited by "="
                                                    or ":"
                                                    or space
                               into WS-RDB-Keyword
                                        DELIMITER IN WS-RDB-Equal
                                    WS-RDB-Value
              end-unstring
              if       WS-RDB-Equal not = "=" and not = ":"
                       move     1 to LK-Return
                       goback
              end-if
              evaluate WS-RDB-Keyword (1:6)
                       when     = "DBHOST"
                                move WS-RDB-Value to LK-Host-Name
                       when     = "DBUSER"
                                move WS-RDB-Value to LK-Implementation
                       when     = "DBPASS"
                                move WS-RDB-Value to LK-Password
                       when     = "DBNAME"
                                move WS-RDB-Value to LK-Base-Name
                       when     = "DBPORT"
                                move WS-RDB-Value to LK-Port-Number
                       when     = "DBSOCK"
                                move WS-RDB-Value to LK-Socket
                       when other
                                move 2 to LK-Return
                                goback
              end-evaluate
     end-perform.
     close     ACAS-Params.
     goback.
*>
