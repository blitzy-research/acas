       >>source free
*>****************************************************************
*>                                                               *
*>                Date Validation & Conversion                   *
*>                                                               *
*>****************************************************************
*>
 identification   division.
*>========================
*>
*>**
      Program-Id.         maps04.
*>**
*>    Author.             V B Coen FBCS, FIDM, FIDPM, 31/10/1982
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Date Validation / Conversion.
*>                        Converts and checks Dates in 10 chars to/from
*>                        9(8) bin-long in form dd/mm/ccYY.
*>
*>                        Needs to look at all code using this to see
*>                        if conversion is needed instead of just storing
*>                         as CCYYMMDD.
*>**
*>    Version.            1.04 of 03/02/02 21:00.
*>                        1.11 of 12/03/09.
*>****
*>
*> changes:
*> 05/02/02 vbc - Converted to year 2k using dd/mm/YYYY.
*> 29/01/09 vbc - Migration to GNU Cobol & using intrinsic FUNCTIONs
*>                to do most of the work as v1.10 for MAPS04, to help
*>                reduce risk of format change problems in old programs.
*>
*> 19/10/16 vbc - THIS uses binary Dates from 31/12/1600 so is NOT usable
*>                 within IRS as is, but in any event uses Dates with CC
*>                 e.g., dd/mm/ccYY where as IRS uses dd/mm/YY.
*>                 but fixable within IRS itself.
*> 16/04/24 vbc       Copyright notice upDate superseding all previous notices.
*> 19/09/25 vbc - 3.3.00 Version upDate and builds reset.
*> 13/11/25 vbc          Capitalise vars, paragraphs etc.
*>
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was upDated 2024-04-16.
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
 environment      division.
*>========================
*>
 copy  "envdiv.cob".
 input-output     section.
*>-----------------------
*>
 data             division.
*>========================
 working-storage  section.
*>-----------------------
*>
 01  Date-Fields.
     03  Z                  pic 99 binary.
     03  Test-Date.
         05  TD-CCYY.
             07  TD-CC      pic 99.
             07  TD-YY      pic 99.
         05  TD-MM          pic 99.
         05  TD-DD          pic 99.
     03  Test-Date9 redefines Test-Date pic 9(8).
*>
 linkage          section.
*>-----------------------
*>
*>*********
*> maps04 *
*>*********
*>
 01  Mapa03-WS.
     03  A-Date             pic x(10).
     03  filler  redefines  A-Date.
       05  A-Days           pic 99.
       05  filler           pic x.
       05  A-Month          pic 99.
       05  filler           pic x.
       05  A-CCYY           pic 9(4).
       05  filler redefines A-CCYY.
           07  A-CC         pic 99.
           07  A-Year       pic 99.
     03  A-Bin              binary-long.
*>
 procedure        division using  Mapa03-WS.
*>=========================================
*>
*> if dd/mm/ccyy is bad A-Bin = zero,
*>   if entry A-Bin not zero then convert to dd/mm/ccyy
*>
     if       A-Bin  >  zero
              go to  WS-Unpack.
*>
     move     zero    to  Z.
     inspect  A-Date replacing all "." by "/".
     inspect  A-Date replacing all "," by "/".
     inspect  A-Date replacing all "-" by "/".
     inspect  A-Date tallying Z for all "/".
*>
*>  Very basic Testing here as FUNCTION Test-Date checks for
*>           February and leap years
*>
     if       Z not = 2 or
              A-Days not numeric or
              A-Month not numeric or
              A-CC   not numeric or
              A-Days < 01 or > 31 or
              A-Month < 01 or > 12
              go to Main-Exit.
*>
     move     A-CC    to TD-CC.
     move     A-Year  to TD-YY.
     move     A-Month to TD-MM.
     move     A-Days  to TD-DD.
*>
     if       FUNCTION Test-Date-YYYYMMDD (Test-Date9) not = zero *> Bad date
              go to Main-Exit.
*>
*>********************************************
*>       Date Validation & Conversion        *
*>       ============================        *
*>                                           *
*>  Requires Date input in A-Date as         *
*>  dd.mm.yy or dd.mm.ccyy & returns Date as *
*>      ccYYMMDD in  A-Bin                   *
*>  Date errors returned as A-Bin equal zero *
*>                                           *
*>********************************************
*>
     move     FUNCTION integer-of-Date (Test-Date9) to A-Bin.
     go       to Main-Exit.
*>
*>
*>*************************************
*>   Binary Date Conversion Routine   *
*>   ==============================   *
*>                                    *
*>  Requires CCYYMMDD input in A-Bin  *
*>  &  returns Date  in A-Date        *
*>  This way Dates can be compared    *
*>    as is                           *
*>*************************************
*>
 WS-Unpack.
     move     "00/00/0000" to A-Date.
     move     FUNCTION Date-of-integer (A-Bin) to Test-Date.  *> CCYYMMDD
     move     TD-CCYY to A-CCYY.
     move     TD-MM   to A-Month.
     move     TD-DD   to A-Days.          *> Now UK Date
*>
 Main-Exit.
     exit     program.
