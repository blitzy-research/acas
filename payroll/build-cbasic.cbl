       >>source free
*>****************************************************************
*>   Create  a new CBasic source from one with include directives
*>   Therefore creating a new source file with all copyboos(include) content
*>   included, which makes it easier to understand the basic source code.
*>   Could also be made to work for other basic dialects that use the include
*>   statement if required although some code changes may be required.
*>
*>****************************************************************
*>
 identification          division.
*>================================
*>
      program-id.       build-cbasic.
*>**
*>    Author.           Vincent B Coen FBCS, FIDM, FIDPM, 19/10/2025.
*>**
*>    Security.         Copyright (C) 2025 - 2026 & later, Vincent Bryan Coen.
*>                      Distributed under the GNU General Public License.
*>                      See the file COPYING for details.
*>**
*>    Remarks.          Using a Cbasic source program will add in all include files via
*>                      the #include statements finding such code in folder
*>                      ./includes.
*>
*>                      The program also accepts chars $, % and #, used preceding 'include'
*>                      i.e.,  #include "name", $include "name" and %include "name".
*>
*>            Call proc: build-cbasic arg1 arg2 arg3 arg4
*>                       Where arg1 = input file with ext
*>                             arg2 = Output file with ext
*>                             arg3 = Include source file extension, i.e. ".bas" or ".BAS"
*>                                     Where filename used in sources is without one,
*>                                    I.e.,  #include "cb-010" (# can also be $ or %.
*>                             arg4 = Include folder if not current (active) folder
*>                                    I.e.,  includes
*>                                    which is below current folder where the includes sources
*>                                    are found.
*>
*>  Program will search and found include files (having stripped off any quotes in the folder supplied
*>  as arg4). IT will NOT examine content of the copybook(include) files for more include statements
*>  This means that a 2nd or third pass may be required and or using the current folder if include
*>  files are reported as cannot be found.
*>
*> If it cannot find a include file it will write out to O/P file a msg of :
*>   SY006 Not Found includes/filename.bas Continuing
*>
*> so with three passes you could have 2 of these - you can ignore these if final pass
*> ends without errors as reported at EOJ  (End of Job).
*>
*>        Actual example of commands used :
*>
*>   Pass 1 :
*>  build-cbasic pyupdhis.bas pyupdhis.basa ".bas" includes
*>
*>   Pass 2 (if needed - as one or more include files may in turn also contain includes) and if SY006
*>    is issued :
*>
*>  build-cbasic pyupdhis.basa pyupdhis.basb ".bas"  includes
*>
*>   Pass 3 (If needed and all includes not found so need to search current folder)
*>  build-cbasic pyupdhis.basb pyupdhis.basc ".bas" " "
*>
*>  This last one will search only the current folder. Note that if it too contains files
*>   that in turn has includes another pass will be required.
*>
*>  Basically continue with extra passes untill there is no more warning of files not found.
*>
*>***
*>  To build program - install the gnucobol compiler via your Linux package manager OR
*>  go to sourceforge.net/p/gnucobol url, Files and install latest release which as of
*>  6th February 2026 is v3.2.
*>
*>  For Windows versions as well, go to Arnolds url at :
*>   https://www.arnoldtrembley.com/GnuCOBOL.htm
*>  Note running Linux using WSL2 under Windows v10 or v11 - use same procedure as for Linux,
*>   assuming a package manager is available.
*>
*> Once installed go to folder holding source of this program and enter :
*>  cobc -x build-cbasic.cbl  and this will compile program without a source listing
*>  otherwise for such a listing run
*>  cobc -x build-cbasic.cbl -T build-cbasic.prn
*>
*> It should compile without any warnings or errors being reported.
*>
*>**
*>    Version.          See Prog-Name In Ws.
*>**
*>    Called Modules.   None.
*>**
*>    Functions Used:
*>                      CONCATENATE
*>                      LOWER-CASE
*>                      SUBSTITUTE
*>                      TRIM
*>    Called Procedures:
*>                      CBL_CHECK_FILE_EXIST
*>
*>    Files used :      Basic source in, out, include file.
*>
*>    Error or Warning messages used.
*>                      See source code.
*>
*>    Program specific:
*>                      SY003, 5, 6 & 7. A few others without a # to ease reading src.
*>**
*> Changes:
*> 03/02/2026 vbc - 1.0.0 Created - starting. Prior to testing.
*> 05/02/2026 vbc -     3 Fix 3 set of bugs.
*>                      4 Minor adjustments for help
*> 06/02/2026 vbc         Testing completed and released with ACAS sources
*>                        and in gnucobol contrib folder under tools.
*>                      5 Tidy up, create common error msgs with a SY00 #
*>                        and remove unused variables etc.
*> 09/02/2026 vbc -    .6 Added warning msg SY007 if a include exist on included file
*>                        Check IPfile not the same as OPfile.
*> 24/02/2026 vbc -    .7 Clean up code base including bug in INC-File code.
*>
*>*************************************************************************
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 2024-04-16.
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
*> holder with your commercial plans and proposals to vbcoen@gmail.com.
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
 environment             division.
*>================================
*>
 copy "envdiv.cob".
 REPOSITORY.
       FUNCTION ALL INTRINSIC.
*>
 input-output            section.
 file-control.
      select  IFile    assign       IFile-Name
                       organization line sequential
                       status       Ifile-Status.
*>
      select  OFile    assign       OFile-Name
                       organization line sequential
                       status       Ofile-Status.
*>
      select  Inc-File assign       Inc-File-Name
                       organization line sequential
                       status       Inc-Status.
*>
 data                    division.
*>================================
*>
 file section.
*>
 fd  IFile.          *> Very long but enough for any - I hope,
 01  IFile-Record       pic x(120).
*>
 fd  OFile.
 01  OFile-Record       pic x(120).
*>
 fd  Inc-File.
 01  Inc-File-Record    pic x(120).
*>
 working-storage section.
*>-----------------------
 77  Prog-Name               pic x(19) value "build-cbasic v1.0.7".
*>
 01  WS-Data.
     03  Ifile-Status        pic xx     value zero.
     03  OFile-Status        pic xx     value zero.
     03  Inc-Status          pic xx     value zero.
*>
     03  IFile-Name          pic x(16).  *> Allows for arg name + ".bas"
     03  OFile-Name          pic x(16).
     03  Inc-File-Name       pic x(32).  *> Allows for include folder via arg4 name + /arg2 .bas
     03  A                   pic 999      value zero.
     03  B                   pic 999      value zero.
     03  C                   pic 999      value zero.
     03  D                   pic 999      value zero.
     03  F                   pic 9        value zero.   *> Length of Arg2 extention excl "."
     03  G                   pic 9        value zero.   *> Length of Arg2 so start of ext is (G - 2:3)
     03  Z                   binary-short value zero.  *> 32k size
     03  WS-Recs-In          binary-short value zero.
     03  WS-Recs-Out         binary-short value zero.
     03  WS-Recs-Included    binary-short value zero.
     03  WS-Recs-Rep-1       pic zz,zz9.
     03  WS-Recs-Rep-2       pic zz,zz9.
     03  WS-Recs-Rep-3       pic zz,zz9.
*>
     03  WS-Tab              pic x        value X"09". *> Tab char in basic source code to be swapped out
*>
 01  WS-Strings                           value spaces.
     03  WS-Word-1           pic x(32).
     03  WS-Word-2           pic x(32).
     03  WS-Word-3           pic x(32).
     03  WS-Temp-Record      pic x(120).
     03  WS-Ext-In           pic x(4).
     03  WS-Ext-Out          pic x(4).
     03  WS-Ext-Temp         pic x(4).
     03  WS-Ext-X.
         05  WS-Ext-Char     binary-char unsigned.
*>
 01  File-Info                           value zero.       *> Layout as per GNU v3 manual
     05 File-size        pic 9(18) comp.
     05 Mod-DD           pic 9(2)  comp. *> Mod date.
     05 Mod-MO           pic 9(2)  comp.
     05 Mod-YYYY         pic 9(4)  comp.
     05 Mod-HH           pic 9(2)  comp. *> Mod time
     05 Mod-MM           pic 9(2)  comp.
     05 Mod-SS           pic 9(2)  comp.
     05 filler           pic 9(2)  comp. *> Always 00
*>
 01  Arg1                pic x(16)  value spaces.  *> In file name
 01  Arg2                pic x(16)  value spaces.  *> Out file name
 01  Arg3                pic x(4)   value spaces.  *> Default extension ie ".bas" or ".BAS".
 01  Arg4                pic x(128) value spaces.  *> Path to include folder or space for current
*>
 01  Error-Messages.
     03  SY001           pic x(53) value "SY001 Aborting - Input and Output file names the same".
 *>    03  SY002           pic x(31) value "SY002 Note error and hit Return".
     03  SY003           pic x(66) value "SY003 Invalid params - needs In File, Out File, extname & incl Dir".
 *>    03  SY004           pic x(20) value "SY004 Now Hit Return".
     03  SY005           pic x(31) value "SY005 Failed to write source - ".
     03  SY006           pic x(16) value "SY006 Not Found ".
     03  SY007           pic x(45) value "SY007 An included file has itself, an include".
*>
 procedure division chaining Arg1
                             Arg2
                             Arg3
                             Arg4.
*>
 aa000-Main                  section.
*>**********************************
*> Force Esc, PgUp, PgDown, PrtSC to be detected
 *>    set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
 *>    set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
*>
*> Show the args 1, 2, 3 & 4 details if all spaces.
*>
     display  Prog-Name " Starting".
     if       Arg1 = spaces or
              Arg2 = spaces or
              Arg3 = spaces           *> arg4 can be spaces
              display  SY003
              display  space
              display  "Help for Program :"
              display  space
              display  "   Arg1 = Input File Name"
              display  "   Arg2 = Output File Name"
              display  "   Arg3 = Include source extention, ie '.bas' or '.BAS'"
              display  "   Arg3 =  Or ' ' if no extention used in src's"
              display  "   Arg4 = Include folder if not using active current one"
              display  " If any includes was in a include rerun program use the O/P file,"
              display  "  ie errors finding copybooks rerun using o/p as input etc"
              display  space
              goback.
*>
     if       Arg1 = Arg2    *> Check filenames not the same
              display  SY001
              goback.
*>
     move     1  to Z.                                     *> Not sure I want it.
     unstring Arg2     delimited by "." or
                                    " "
                        into WS-Ext-Temp    *> filename.abcd and d is the one we want
                             WS-Ext-Temp   *> Yes only interested in second one.
                           pointer Z.
     move     LENGTH (WS-Ext-Temp) to F.
     move     LENGTH (Arg2) to G.
     if       F not = 4
              display  "Arg2 length = " F " not = 4"
              display  "Aborting"
              goback.
*>
     move     Arg2 (4:1) to WS-Ext-X.    *> so can be A, a or 1 & adding 1
*>                                          to WS-Ext-Char make it B, b or 2.
*> Next -
*>  Following Should work for folders Soon find out ?
*>
     if       Arg4 (1:4) not = spaces   *> else all includes are in current folder
              call     "CBL_CHECK_FILE_EXIST" using Arg4
                                                    File-Info
              if       Return-Code not = zero
                       display  "Cannot find folder " Arg4
                       goback.
*>
*> set and test them
*>
     move     Arg1 to IFile-Name.
     move     Arg2 to OFile-Name.
     move     spaces to Inc-File-Name.
     if       Arg4 (1:4) not = spaces
              move     TRIM (Arg4) to Inc-File-Name.    *> ??
     open     Input Ifile.
     if       Ifile-Status not = "00"
              display  "Cannot find Input file - " Ifile-Name
              close    Ifile
              goback.
*>
     open     output Ofile.
     if       Ofile-Status not = "00"
              display  "Cannot create Output file - " Ofile-Status " for " Arg2
              close  Ofile
                     Ifile
              goback.
*>
     move     zeros to WS-Recs-In
                       WS-Recs-Out
                       WS-Recs-Included
*>  Can now get on with the job in hand.
*>
     perform  forever
              read     Ifile    at end
                       close    Ifile
                                Ofile
                       display  "EOC - Completed - Phase n"
                       move     WS-Recs-In       to WS-Recs-Rep-1
                       move     WS-Recs-Out      to WS-Recs-Rep-2
                       move     WS-Recs-Included to WS-Recs-Rep-3
                       display  "Src in  - " WS-Recs-Rep-1
                       display  "Src out - " WS-Recs-Rep-2
                       display  "Inc In  - " WS-Recs-Rep-3
                       goback
              end-read
              add      1 to WS-Recs-In
              move     1 to A               *> For unstring pointer
              move     SUBSTITUTE (Ifile-Record WS-Tab "    ") to WS-Temp-Record *> replace tabs to four spaces
              move     WS-Temp-Record to Ifile-Record
              unstring Ifile-Record   delimited by ' "' or space or quote
                                        into  WS-Word-3   *> -> Word-3 ["%,$,# &'include'" ]
                                              WS-Word-2   *> included FN
                                      pointer A
              end-unstring
*>
              move     TRIM (WS-Word-3 leading) to WS-Word-1         *> strip out any leading spaces
              if       LOWER-CASE (WS-Word-1 (2:7)) not = "include"  *> ignore 1st char
                       write    OFile-Record from IFile-Record
                       if       OFile-Status not = "00"
                                display   SY005 Ofile-Status
                                close    Ifile
                                         Ofile
                                goback
                       end-if
                       add      1 to WS-Recs-Out
                       exit     perform cycle
              end-if
*>
*> found a include so now use unstring for 'include then name and check end
*> (does not have .bas / BAS and add it then open inc file with arg3 + '/'
*> added (sticking to *nix)
*> if not found err msg & continue if poss.
*>
*>  Reminder for me
*>        WS-Word-2  = FN with ext = Arg1
*>              Arg1 = I/P FN with ext.
*>              Arg2 - O/P FN with ext.
*>              Arg3 = Include source extension, i.e. .bas or .BAS"
*>              Arg3 = "." if no extension used in src's"
*>              Arg4 = Include folder if not current one"
*>              Inc-File-Name = Incl FN with sub path if needed
*>
              move     spaces to WS-Word-3
                                 Inc-File-Name
              move     Length (WS-Word-2) to C            *> incl FN
              if       WS-Word-2 (C - 3:4) not = ".bas" and not = ".BAS"  *> Could be, use arg3
                       if       Arg4 (1:4) not = spaces            *> using folder for includes
                                move     CONCATENATE (TRIM (Arg4)  *> Could be spaces
                                                     "/"           *>  for use current folder
                                                     TRIM (WS-Word-2) *> FN
                                                     TRIM (Arg3))     *> .ext
                                      to  Inc-File-Name               *> = folder/FN
                       else                                    *> include files in current folder
                                move     CONCATENATE (TRIM (WS-Word-2) *> FN
                                                      TRIM (Arg3))     *> .ext
                                      to  Inc-File-Name                *> = folder/FN
                       end-if
              else                       *> CAN DROP THE LAST ELSE & MOVE IF this works
                       move     WS-Word-2 to Inc-File-Name
              end-if
  *>            display "looking for " Inc-File-Name   *> FOR TESTING ONLY
 *>       stop "Check & return"
              open     input Inc-File
              if       Inc-Status not = "00"  *> not found
                       display SY006 TRIM (Inc-File-Name) " continuing"
                       close Inc-File

                       if       Arg4 (1:4) not = spaces               *> This time use primary folder
                                move     CONCATENATE (TRIM (WS-Word-2) *> FN
                                                      TRIM (Arg3))     *> .ext
                                      to  Inc-File-Name                *> = folder/FN
                       end-if
                       open     input Inc-File
                       if       Inc-Status not = "00"  *> not found
                                display SY006 TRIM (Inc-File-Name) " continuing"
                                close Inc-File
                       end-if
*>
*>    Write out the input record to be used for another pass
*>
                       write    OFile-Record from IFile-Record
                       if       OFile-Status not = "00"
                                display  SY005  Ofile-Status
                                close    Ifile
                                         Ofile
                                goback
                       end-if
       *>                move     CONCATENATE (SY006
       *>                                     TRIM (Inc-File-Name)
       *>                                     " Continuing")
       *>                                        to OFile-Record
       *>                write    OFile-Record
       *>                if       OFile-Status not = "00"
       *>                         display  SY005 Ofile-Status
       *>                         close    Ifile
       *>                                  Ofile
       *>                                  Inc-File
       *>                         goback
       *>                end-if
       *>                add      1 to WS-Recs-Out
                       move     spaces to OFile-Record
                       exit     perform cycle
              end-if
              move     CONCATENATE ("Rem "        *> Use Rem to remark out a include line - top level
                                   IFile-Record)
                                       to OFile-Record
              write    OFile-Record
              if       OFile-Status not = "00"
                       display  SY005 Ofile-Status
                       close    Ifile
                                Ofile
                                Inc-File
                       goback
              end-if
              add      1 to WS-Recs-Out
              perform  Forever
                       read     Inc-File at end
                                close Inc-File
                                exit perform
                       end-read
                       move     SUBSTITUTE (Inc-File-Record WS-Tab "    ") to WS-Temp-Record
                       move     WS-Temp-Record to Inc-File-Record
                       add      1 to WS-Recs-Included
*>
*> test for includes and display so if true
*>
                       move     zero to B
                       inspect  Inc-File-Record
                                tallying B for LEADING "include"
                       if       B > zero
                                move     1 to D  *> Signifies more includes found
                                display  SY007   *> show warning of include
                       end-if
*>
                       write    OFile-Record from Inc-File-Record
                       if       OFile-Status not = "00"
               *> In case there are tab chars present a no go for LS files
                                display   SY005 Ofile-Status
                                display   "Data " OFile-Record (1:32)
                                close    Ifile
                                         Ofile
                                         Inc-File
                                goback
                       end-if
                       add      1 to WS-Recs-Out
                       exit   perform cycle
              end-perform

     end-perform.
*>
