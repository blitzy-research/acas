       >>source free
*>****************************************************************
*>                                                               *
*> P A S S - W O R D  /  N A M E    E N C O D E R                *
*>                                                               *
*>****************************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.        maps01.
*>**
*>    author.            Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM 31/10/82
*>                       For Applewood Computers.
*>**
*>    Security.          Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                       Distributed under the GNU General Public License.
*>                       See the file COPYING for details.
*>**
*>    Remarks.           Pass-Word / Name Encoder, OS version.
*>**
*>    version.           1.03 of 03/02/02 21:00.
*>****
*> Changes:
*> 29/01/2009 vbc -        Migration to Open Cobol-> GnuCobol.
  *>                       Simplify Password mechanism for export inc USA
*>                         & change to just four chars as don't think they can
*>                         cope with 256 - 1024 bytes.
*> 08/04/2018 vbc - 1.3.00 No longer used in O/S version.
*> 16/04/2024 vbc -        Copyright notice update superseding all previous notices.
*> 19/09/2025 vbc - 3.3.00 Version update and builds reset.
*>
*>*************************************************************************
*>
*> Copyright Notice.
*> ****************
*>
*> This notice supersedes all prior copyright notices & was updated 2024-04-16.
*>
*> These files and programs are part of the Applewood Computers Accounting
*> System and is Copyright (c) Vincent B Coen. 1976-2026 and later.
*>
*> This program is now free software; You can redistribute it and/or modify it
*> under the terms listed here and of the GNU General Public License as
*> published by the Free Software Foundation; version 3 and later as revised
*> for PERSONAL USAGE ONLY and that includes for use within a business but
*> EXCLUDES repackaging or for Resale, Rental or Hire in ANY way.
*>
*> Persons interested in repackaging, redevelopment for the purpose of resale or
*> distribution in a rental or hire mode must get in touch with the copyright
*> holder with Your commercial plans and proposals.
*>
*> ACAS is distributed in the hope that it will be useful, but WITHOUT
*> ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
*> FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
*> for more details. If it breaks, You own both pieces but I will endeavour
*> to fix it, providing You tell me about the problem.
*>
*> You should have received a copy of the GNU General Public License along
*> with ACAS; see the file COPYING.  If not, write to the Free Software
*> Foundation, 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
*>
*>*************************************************************************
*>
 environment             division.
*>===============================
*>
 copy  "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 data                    division.
*>===============================
*>
 working-storage section.
*>----------------------
*>
 01  ws-data.
     03  alpha           pic x(26)     value "CKQUAELSMWYIZJRPBXFVGNODTH".
     03  filla1  redefines  alpha.
         05  ar1         pic x         occurs  26 indexed by XX.
     03  alower          pic x(26)     value "ckquaelsmwyizjrpbxfvgnodth".
     03  filler  redefines  alower.
         05  ar1-l       pic x         occurs  26  indexed by a.
*>
     03  Pass-Word-Input.
         05  ar2         pic x         occurs  4.
     03  Pass-Word-Output.
         05  ar3         pic x         occurs  4.
*>
     03  Pass-name-Input.
         05  ar4         pic x         occurs  32.
     03  Pass-name-Output.
         05  ar5         pic x         occurs  32.
*>
 77  Q                   pic s9(5)      computational.
 77  Y                   pic s9(5)      computational.
 77  Z                   pic s9(5)      computational.
 77  Base                pic s9(5)      computational.
 linkage section.
*>--------------
*>
 copy  "wsmaps01.cob".
*>
 procedure division  using  maps01-ws.
*>===================================
*>
     if       not  Pass
              go to  encode-name.
*>
 encode-Pass.
     move     Pass-Word  to  Pass-Word-Input.
     move     1  to  Y.
*>
 loop.
     set      XX to  1.
     search   ar1  at end  go to  test-lower
                   when  ar1 (XX) = ar2 (Y)
                   set A to XX
                   go to  Set-Base.
*>
 test-lower.
     set      A  to  1.
     search   ar1-l  at end  go to  return-to-loop
                     when  ar1-l (A) = ar2 (Y)
                     go to  Set-Base.
*>
 Set-Base.
     multiply Y  by  Y  giving  Base.
     add      3  to  Base.
*>
     set      Z  to  A.
     add      Base  to  Z.
     subtract 26  from  Z.
*>
     if       Z  <  1
              multiply  Z  by  -1  giving  Z.
*>
     subtract Y  from  5  giving  Q.
     if       Z  not = zero
              move  ar1 (z)  to  ar3 (Q)
     else
              move  space    to  ar3 (Q).
*>
 return-to-loop.
     add      1  to  Y.
     if       Y  <   5    go to  loop.
*>
     move     Pass-Word-Output  to  Pass-Word.
     go       to main-exit.
*>
 encode-name.
     move     Pass-name  to  Pass-name-Input.
     move     1  to  Y.
*>
 loop-n.
     set      XX to  1.
     search   ar1  at end  go to  test-lower-n
                   when  ar1 (XX) = ar4 (Y)
                   set A to XX
                   go to  Set-Base-n.
*>
 test-lower-n.
     set      A  to  1.
     search   ar1-l  at end  go to  return-to-loop-n
                     when  ar1-l (A) = ar4 (Y)
                     go to  Set-Base-n.
*>
 Set-Base-n.
     add      Y  51  giving  Base.
     divide   Base  by  Y  giving  Base  rounded.
*>
     if       Base  >  25
              subtract  26  from  Base.
*>
     set      Z  to  A.
     add      Base  to  Z.
     subtract 27  from  Z.
*>
     if       Z  <  1
              multiply  Z  by  -1  giving  Z.
*>
     if       Z  >  26
              subtract  26  from  Z.
*>
     if       Z  not = zero
              move  ar1 (Z)  to  ar5 (Y)
     else
              move  space    to  ar5 (Y).
*>
 return-to-loop-n.
     add      1  to  Y.
     if       Y  <  32
              go to  loop-n.
*>
     move     Pass-name-Output  to  Pass-name.
*>
 main-exit.   exit program.
*>********    ************
