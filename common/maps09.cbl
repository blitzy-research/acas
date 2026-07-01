       >>source free
*>*****************************************************************
*>                                                                *
*>         Check digit calulation and verification routine        *
*>                           MOD 11 only                          *
*>*****************************************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         maps09.
*>**
*>    author.             Cis Cobol Conversion By V B Coen FBCS, FIDM, FIDPM, 1/11/82
*>                        For Applewood Computers.
*>**
*>    Security.           Copyright (C) 1967-2026, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    remarks.            Check-Digit (Mod 11) / Calculation Verification.
*>**
*>    version.            1.02 of 08/11/82  01:30.
*>****
*> Changes:
*> 29/01/2009 vbc -        Migration to Open Cobol/GnuCobol.
*> 16/04/2024 vbc          Copyright notice update superseding all previous notices.
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
 environment             division.
*>===============================
*>
 copy  "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 data                    division.
*>===============================
 working-storage section.
*>----------------------
*>
 01  ws-data.
     03  Alpha           pic x(37)     value "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-".
     03  filler  redefines  Alpha.
         05  Ar1         pic x         occurs  37  indexed by Q.
     03  Work-Array.
         05  Array       pic x         occurs  6.
     03  Suma            pic s9(5).
*>
     77  A               pic s9(5)      comp.
     77  Y               pic s9(5)      comp.
     77  Z               pic s9(5)      comp.
 linkage section.
*>--------------
*>
 copy  "wsmaps09.cob".
*>
 procedure division  using  maps09-ws.
*>===================================
*>
 main.
     move     Customer-Nos  to  Work-Array.
     move     zero  to  Suma.
     perform  Addition-Loop through Addition-End
              varying A from 1 by 1 until A > 6.
*>
     if       Suma = zero
              move  "N"  to  maps09-reply
              go to  main-exit.
*>
     divide   Suma  by  11  giving  Z.
     compute  A  =  11 - (Suma - (11 * Z)).
*>
     if       maps09-reply = "C"
              move   A   to  Check-Digit
              move  "Y"  to  maps09-reply.
*>
     if       maps09-reply = "V"
       and    A = check-digit
              move  "Y"  to  maps09-reply.
*>
     go       to main-exit.
*>
 Addition-Loop.
     set      Q  to  1.
     search   Ar1  at end  go to  Addition-Error
              when Ar1 (Q) = Array (A)
                   go to  Addition-Do.
*>
 Addition-Error.
     move     zero  to  Suma.
     move     7     to  A.
     go to    Addition-End.
*>
 Addition-Do.
     set      Y  to  Q.
     compute  Z  =   Y * (8 - A).
     add      Z  to  Suma.
*>
 Addition-End.
     exit.
*>
 main-exit.   exit program.
*>********    ************
