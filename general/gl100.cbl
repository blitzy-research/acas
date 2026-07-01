       >>source free
*>*****************************************************************
*>                                                                *
*>           L E D G E R  P R I N T  P R E - S O R T              *
*>                                                                *
*>*****************************************************************
*> WARNING THIS uses ARCHIVING FROM a path that has a Usb memory stick
*>    or a specific directory (in which case it is up to the user
*>    to ensure that that directory is copied to a suitable medium)
*>    after processing.
*>********************************************************************
 identification          division.
*>===============================
*>
*>**
      program-id.         gl100.
*>**
*>    Author.             GL was written by Simon Whine MBCS, on behalf of
*>                        Applewood Computers and its group of Companies.
*>                        All changes/migrations by:
*>                        Vincent B. Coen FBCS, FIDM, FIDPM.
*>                        Converted From Cis January 85,
*>                        For Applewood Compuers.
*>                        Written to supplement IRS to support larger numbers for
*>                        accounts to 10 digits nominal and subnominals and money
*>                        amounts to 100M - 1 for customers requiring a
*>                        comparable? but cheaper product than Oracle financials.
*>                        Reduced down some point later in time for accnts 6
*>                        digits and reduced money amounts.
*>**
*>    Security.           Copyright (C) 1976-2026, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            Ledger Print - Pre-Sort.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Called Modules.     None
*>**
*>    Error messages used.
*>                        GL101 Enter <0> to signify change made or <9> to abort this run :- [ ]
*>                        GL105 Ensure Archive USB Memory Stick is in path
*>**
*>  Changes:
*> 28/01/09 vbc - Migration to Open Cobol.
*> 21/12/11 vbc - .01 Support for dates other than UK & clean up msgs
*>                    Error msgs to GLnnn,
*>                    Support for path+filenames.
*> 24/10/16 vbc - .   ALL programs now using wsnames.cob in copybooks.
*> 13/01/18 vbc - .02 Updated for v3.02 & FH & DALs.
*> 30/05/18 vbc - .03 Renamed all warning & error msgs also in Manual.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 20/09/25 vbc -3.3.00 Version update and builds reset.
*>
*> NOTE TESTING Code in the  disk-change  section
*> ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
 copy "envdiv.cob".
 input-output            section.
*>------------------------------
*>
 file-control.
*>-----------
*>
     select  archive    assign  file-2
                        access  sequential
                        status  fs-reply
                        organization  line sequential.
*>
     select  arch-out   assign  arc-out-name
                        access  sequential
                        status  fs-reply
                        organization  line sequential.
*>
     select  sort-file  assign file-21.
*>
 data                    division.
*>===============================
*>
 file section.
*>-----------
*>
 fd  archive.
*>
 01  arc-trans-record.
   03  arc-batch         pic 9(5).
   03  arc-post          pic 9(5).
   03  arc-code          pic xx.
   03  arc-date          pic x(8).
   03  arc-ac            pic 9(6).
   03  arc-pc            pic 99.
   03  arc-amount        pic s9(8)v99.
   03  arc-legend        pic x(32).
   03  arc-c-ac          pic 9(6).
   03  arc-c-pc          pic 99.
*>
 fd  arch-out.
*>
 01  arc-trans-out.
   03  out-batch         pic 9(5).
   03  out-post          pic 9(5).
   03  out-code          pic xx.
   03  out-date          pic x(8).
   03  out-ac            pic 9(6).
   03  out-pc            pic 99.
   03  out-amount        pic s9(8)v99.
   03  out-legend        pic x(32).
   03  out-c-ac          pic 9(6).
   03  out-c-pc          pic 99.
*>
 sd  sort-file.
*>
 01  srt-trans-srt.
   03  srt-batch         pic 9(5).
   03  srt-post          pic 9(5).
   03  srt-code          pic xx.
   03  srt-date          pic x(8).
   03  srt-ac            pic 9(6).
   03  srt-pc            pic 99.
   03  srt-amount        pic s9(8)v99.
   03  srt-legend        pic x(32).
   03  srt-c-ac          pic 9(6).
   03  srt-c-pc          pic 99.
*>
 working-storage section.
*>----------------------
*>
 77  prog-name           pic x(15)  value "gl100 (3.3.00)".
 copy "wsfnctn.cob".
*>
 77  a                   pic 9      value zero.
 77  keyed-reply         pic x      value space.
 77  ws-eval-msg         pic x(25)  value spaces.
*>
 01  Arg-Test            pic x(525) value spaces.
*>
 01  arc-out-name        pic x(532) value "workarc.tmp".
*>
 01  Error-Messages.
*> System Wide
*> Module specific
    03  GL101            pic x(70)  value "GL101 Enter <0> to signify change made or <9> to abort this run :- [ ]".
    03  GL105            pic x(48)  value "GL105 Ensure Archive USB Memory Stick is in path".
*>
 linkage section.
*>**************
*>
 copy "wscall.cob".
 copy "wssystem.cob".
 copy "wsnames.cob".
*>
 77  to-day              pic x(10).
*>
 procedure division using ws-calling-data
                          system-record
                          to-day
                          file-defs.
*>***************************************
*>
 gl100-Main section.
     display  prog-name at 0101 with foreground-color 2 erase eos.
     display  "Ledger Print - Sort" at 0131  with foreground-color 2.
*>
     perform  disk-change.
     if       a  equal  9   *> abort procedure
              move 5 to ws-term-code
              go to menu-exit.
*>
     open     input archive.
     if       fs-reply not = zero
              move 4 to ws-term-code
              go to menu-exit.
     close    archive.
*>
     sort     sort-file
              on ascending key  srt-ac
                                srt-pc
                                srt-batch
                                srt-post
              using   archive
              giving  arch-out.
*>
 menu-exit.
     goback.
*>
 disk-change  section.
*>-------------------
*>     Copied from gl080
*>     *****************
*>
*> Build path for archive file/s
*>    this set up for testing but need to change to accept
*>     path to usb memory stick (full path) but will work as is
*>       assuming users changes path and the system KNOWS about
*>         the memory stick
*>
     move     space to Arg-Test.             *> this lot needs checking !!!!!
     string   file-24        delimited by space
              "archives"     delimited by size
              file-defs-os-delimiter
                             delimited by size
                file-2      delimited by space
                            into Arg-Test.
     move     Arg-Test to file-2.
*>
*>  This is for the temp file used by gl105 (the Ledger Print)
*>
     move     space to Arg-Test.
     string   file-24        delimited by space
              "archives"     delimited by size
              file-defs-os-delimiter
                             delimited by size
              arc-out-name   delimited by space
                            into Arg-Test.
     move     Arg-Test to arc-out-name.
*>
     display  GL105 at 1201 with erase eol foreground-color 2.
     display  GL101 at 1301 with erase eol foreground-color 2.
*>
 accept-option.
     accept   a at 1369.
     if       a = 9
              go to  main-exit.
     if       a  not = zero
              go to  accept-option.
*>
*>  Hopefully can remove these after testing
*>
     display  "Current path/name is :" at 1401 with foreground-color 2 erase eol.
*>     display  file-2             at 1501 with foreground-color 2 erase eol.
     accept   file-2             at 1501 with foreground-color 2 update LOWER.
     if       file-2 (1:1) = space
              go to accept-option.
*>
 main-exit.   exit.
*>********    ****
