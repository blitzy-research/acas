       >>source free
*>****************************************************************
*>                                                               *
*>      S o r t e d   P o s t i n g    F i l e   H a n d l e r   *
*>                                                               *
*>****************************************************************
*>
 identification division.
 program-id.           irsubp.
*> Author.             Cobol conversion by Vincent B Coen
*>                     for Applewood Computers.
*>
*> Security.           Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                     Distributed under the GNU General Public License.
*>                     See the file COPYING for details.
*>
*> Remarks.            Sorted Posting File Handler as producd by irs055 (sort).
*>                     Called by irs050 and irs070.
*>
*> Version.            1.10 25/10/1982 Cis Cobol migration.
*>**
*> Changes.
*> 22/01/09 vbc - .11 Migration to Open/Gnu Cobol.
*> 15/02/09 vbc - .12 Produce error 99 if no input file.
*> 07/05/13 vbc -     Change file to line seq in line with 055.
*> 04/12/16 vbc - .13 Removed System-Record from call list but
*>                    added File-Defs as filename now file-38 to
*>                    force file into correct directory as possible bug.
*>                    As this FH is only for a temporary file it will
*>                    not be converted to also use a RDB table.
*>                    As it is only created and
*>                    used within irs055 for irs050.
*>                    Long term would be to just extract rdb rows in the
*>                    requested sorted order but as a primary sort field
*>                    is the date elements (dd/mm/yy) & the date is stored
*>                    as one column this cannot be done short of having
*>                    three new column to hold DD, MM & YY.
*>                    Hmm, might do it anyway but the sort is very quick!
*> 29/01/18 vbc - .14 Clean up copy books to use default dir BUT the
*>                    wspost.cob is in the irs dir as it is different.
*>                    So code is now to v3.02 standards - ish.
*> 10/02/18 vbc - .15 Removed o/p and writing as not used as the sort (irs055)
*>                    (writes out within sort verb).
*> 19/04/18 vbc -     Comment for .14 and wspost no longer applies as the posting
*>                    is now setup for irs and a different one from SL & PL.
*>                    All copy books are in the one directory.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
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
 environment division.
 copy  "envdiv.cob".
 input-output section.
 file-control.
*>
     select Sorted-Posting-File assign File-38   *> "postsort.dat"
                                organization line sequential
                                file status fs-reply.
*>
 data division.
 file section.
*>
 fd  Sorted-Posting-File.
*>
 01  Record-4.
     03  key-4           pic 9(5).
     03  post-code4      pic xx.
     03  post-date4      pic x(8).
     03  post-dr4        pic 9(5).
     03  post-cr4        pic 9(5).
     03  post-amount4    pic s9(7)v99  sign is leading.
     03  post-legend4    pic x(32).
     03  vat-ac-def4     pic 99.
     03  post-vat-side4  pic xx.
     03  vat-amount4     pic s9(7)v99   sign is leading.
*>
 working-storage section.
*>----------------------
*>
 linkage section.
*>--------------
*>
 copy "irswspost.cob".
 copy "wsfnctn.cob".
 copy "wsnames.cob".
*>
 procedure division using Posting-Record
                          File-Access
                          File-Defs.
*>======================================
*>
 Main.
*>---
*>
*>  Now have Open Input or output, Close, Read next.
*>  Keeping open output to clear the file but not currently used.
*>
     move     zero to we-error.
*>
     if       not fn-open
              go to Close-1.
*>
*>   Open the file.
*>
     if       fn-input
              open input  Sorted-Posting-File.
     if       fn-output
              open output Sorted-Posting-File.
     if       fs-reply not = zero
              move 99 to we-error.
*>
     go       to main-exit.
*>
 Close-1.
*>-----
*>
     if       fn-close
              close Sorted-Posting-File
              go to main-exit.
*>
     if       not fn-read-next
              move 99 to WE-Error
              go to Main-Exit.
*>
 Read-1.
*>------
*>
     read     Sorted-Posting-File record at end
              move 3 to we-error
              go to  main-exit.
     move     Record-4 to posting-record.
*>
 Main-Exit.   exit program.
*>********    ************
