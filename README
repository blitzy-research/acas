The file README.nightly should also be read if using the last v3.2 code release.

For v3.3, updated nightly if any changes have occurred to code, manuals etc.
However all nightly build are now based only around v3.3.

Latest changes is at the TOP.

I therefore have issued the ACAS system as version v3.3.
This is reflected in cvs / svn source code versioning as code-v3.3 with a new
file reflecting this.

WARNING: The current version of ACAS built to the nightly archives is subject
to testing for all the new features listed above as well as some not so listed.
Including while testing to update the manuals to reflect current usage and
screen lay outs etc.

Offers to help in this endeavour would be gratefully received, and that can
include help on Testing, Document writing, updating, software updates and
programming new features if and as required.

I am, but only one person doing this work that originally had a team of 6
helping but as the ACAS system is now open source there is no funds to pay for
any such a team but in any event as I hit my 78 year birthday this
past June and my work load has some what dropped - brain power likewise :(

PLEASE READ: -
To help update software sources and manuals you need to be registered at
sourceforge so you can be added as a "updater" etc. Just send me a message with
an outline of the areas you wish to work on and an idea of your skill set.
Note all manuals are written using the free to obtain and use LibreOffice office
software that is available on all platforms e.g., Linux, OSX, Windows etc.
As these documents are created using the ODF (Open Document Format) they 'should'
be readable using Microsoft Office product from 2019 and onwards BUT I have not
tested this as I am not rich enough to obtain it to test.

2025-09-21   *  Vincent B. Coen
                With most testing completed although full system testing still
                in progress I have updated all source to v3.3 pre-final release
                including the manuals. This does not mean that all bugs have
                been found and all testing is complete. Any such will be updated
                for this version and as time allows (and I remember) I will back
                port all to the v3.2 version close to the same time. HOWEVER
                the latest version will always be v3.3 at any point in time.

                Purchase ledger is still undergoing system testing with more
                order transaction entries and entering both auto payments and
                manual one's with the various reports being run and checked.
                Hopefully concluding before the end of year if not sooner.

                As a point of interest all testing is complete for IRS, Stock
                and Sales apart for some reports. I have not had any time to
                work with General at all since it was migrated over to using the
                GnuCobol compiler (3.2 final) now some years back. On this, some
                logic needs changes to bring it inline with IRS processing at
                least to regards of posting processing and to retain all until
                end of year - as per IRS although this should not take a lot of
                time - I hope. General is more complex in setting up the CoA
                than for IRS as there are some special requirements for account
                number used for specific purposes and I need to get my head
                around these. It has been many years since I have even looked
                let alone played with it and will require examining the source
                code.

                Volunteers any one ?.
                It will require some accountancy knowledge.

2025-04-14   *  Vincent B. Coen
                All basic testing has completed for BO - Back Orders with the changed
                or new program namely :
                st020 - Stock Additions
                sl970 - BO reporting, Update, Manual record creation.
                sl910 - Invoice entry.

                Manuals - Sales Ledger updated for BO processing although some more
                          info might be needed.
                          Building the ACAS System - Minor updates.
                          System Set up procedures Updated, more needed ?

                Check for typo's etc.

2024-12-22   *  Vincent B. Coen
                To confirm all work on OE has terminated as the one missing function
                it had over ACAS was BO (Back Ordering) which has been added to ACAS
                although under testing mode at least for the invoicing
                program (sl910) as testing has finished for the other program changed
                (st020 - Stock Additions), to support it plus the one new program
                (sl970 BO Reporting and amendments).
                Very limited testing in sl970 amendments as it was an after thought
                mostly for use in testing but left in for users - just in case as the
                Sales Invoicing program (Sl910) after processing a BO record will
                delete it after being used/processed subject to user request.
                I.e., it only will offer to delete after an invoice has been created.

                Currently testing is in progress although slowly for the changes in
                SL910 Sales Invoicing to confirm all BO extra coding is working as
                expected and the rest of the system if nothing else than to add the
                needed data throughout the ACAS system for the testing. Additional
                testing (System) to validate that no changes made over the last year
                or two has effected the system functionality AND to help update the
                various manuals such as Sales, Purchase and the various others
                used to help set the system up, ACAS into etc.
                I am always looking for help with these manuals so all offers of
                help is greatly accepted and the only thing a volunteer needs is to be
                a registered member at Sourceforge so that you can be added as a
                valid updater of the ACAS sources.

2024-04-16   *  Vincent B. Coen
                Nightly builds updated on SF as well as in the cvs code base. I am
                trying to remember to keep this up to date at least on a weekly basis
                but cannot find a way of doing it in a automatic manner using Linux
                crontab process mostly cause by the need to input the password.

                Manuals are still being updated with new one's added.

                For Sales Ledger coding for Back order processing has been completed
                although needs to be tested  which is about to start. These extra
                processes includes changes to sl010, sl910 and new program sl970.
                Also in Stock control - st010 and st020.

                Recurring invoices programming has also been completed but again needs
                testing as well. There is also some coding for similar in Purchase
                ledger but is currently incomplete as the need for it here is
                undetermined.  Options ?

                I have added a new nightly file : OE-nightly.rar which is/was an
                experiment where the code was taken from an archived tandy website.
                I migrated the code over from RM Cobol v1.4 or about to GnuCobol and
                while testing have had to make a lot of changes to clear a lot of bugs
                mostly from the original code.

                While testing I found only one extra features present that was not in
                ACAS namely Back Order Processing but only to reporting stage nothing
                beyond. Hence the reason for putting the feature in ACAS Sales and
                Stock. The one other feature? that OE has is dealing with Salesmen and
                their commissions but as there is no actual Payroll system to link to
                it is a bit pointless and as there is no Payroll in ACAS, likewise.

                Why would any business want to pay people a commission taking orders
                over the telephone ?

                So, with that the only feature in OE that differs from ACAS I have now
                stopped doing any work on it but have made it available to any one who
                want to take a look at the code base and before you ask no, that is how
                I found it but remember in the late 70's micro's had very small amount
                of Ram to work with such as 640kB and floppy disks as there storage
                medium. So very tight when programming an application.
                There original ACAS code was also tightly packed but using separate
                modules to handle screen output and keyboard input was never
                considered as the Cobol compiler used did a reasonable job of it - MF
                CIS Cobol and may be we we had more experience of programming in Cobol.


2024-03-17   *  Vincent B. Coen
                Started work on changes to SL910, SL920 to support BO
                (Back Orders) in invoicing will need new program SL970 for
                reporting such actions.

2024-03-13   *  Vincent B. Coen
                Added fields in System record to support Back Ordering in
                System record area and Stock control and likewise in Stock rec.
                Applied to ACASDB.sql definitions etc including the DB master
                load. Change code in System rdbms loader, no need for stock.

2024-01-22   *  Vincent B. Coen
                Corrected typos in the item below :

2024-01-21   *  Vincent B. Coen
                For development and testing I am now using v3.2 final instead of
                playing with 3.3 A/Beta etc due to issues with building it using
                libtool v2.4.7 which is the version used in my system of Mageia
                v9 X64.

                As of today the licence for the ACAS system has been updated to
                reflect 2024 and some minor changes to the COPYRIGHT notice
                itself. For this, see any Cobol source files with the .cob
                extension but it is shown here for reference: --

                Comment regarding OE now removed as work has been terminated as
                it offers not extra functionality with BO added.
                So I will be returning to ACAS manual updates and system testing
                both for the new and existing features that are not very well
                reported on, as well as checking that the recurring invoice sub
                system works as required.

                For those that are not sure what "recurring" billing is - It is
                a system that allows for periodic invoicing such as yearly,
                quarterly, monthly etc, for specific services such as Rents,
                Subscriptions, monthly software usage fees etc. This clearly is
                more for service items and not notably a stock / product type
                facility. A very long time a go it was installed but a more
                basic facility and as no one was really happy with it so it was
                removed.

                The new version of this, is a total rewrite - sort of as many
                aspects are taken from the existing invoicing system but
                using a different data file that when such a charge is due a
                copy of the transaction is passed to the invoicing system and on
                to the invoice file for further processing within the invoicing
                sub system.

                Well that is the theory anyway, all subject to testing.

2022-12-08   *  Vincent B. Coen
                For development and testing am now using gnucobol v3.2 from
                the current svn stream and this version is issuing a warning
                about goto-section and these are a go to statement that goes
                to the start of the same section.
                So for all other than Stock an extra element is added to the
                compile commands in the scripts for both with and without rdbms
                (comp-no-rdbms.sh and comp.sh etc, for each ledger).
                but for stock as it only had three programs effected it was
                quick to just change the program sources in st030, st040 and
                st050. Same applies to sy002 and the same time I changed the
                dates of copyright notices AND the version numbers of changed
                programs.
                I have not yet found or received aa reason for this compiler
                change that is creating this warning message and as the code
                only does a goto within the section the logic is totally valid
                although if a goto was going outside the section to another
                it could present a problem but this does not happen.

                There is no other changes and none that effect any logic.

2020-06-23   *  Vincent B. Coen
                Added a CDF constant to turn ON or OFF file access
                logging  in common/fhlogger.cbl
                CURRENTLY it is ON, so after testing change it before
                recompiling the ACAS system.
                Happy 73rd to me and save paper !

All older notes now removed.


-- Start of CR notice --

 From copyright.cob.

 Copyright Notice.
 ****************

 These files and programs is part of the Applewood Computers Accounting
 System and is copyright (c) Vincent B Coen. 1976-2025 and later.

 This program is now free software; you can redistribute it and/or modify it
 under the terms of the GNU General Public License as published by the
 Free Software Foundation; version 3 and later as revised for personal
 usage only and that includes for use within a business but without
 repackaging or for Resale in any way.

 Persons interested in repackaging, redevelopment for the purpose of resale or
 distribution in a rental mode must get in touch with the copyright holder
 with your commercial plans and proposals.

 ACAS is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 for more details. If it breaks, you own both pieces but I will endeavour
 to fix it, providing you tell me about the problem.

 You should have received a copy of the GNU General Public License along
 with ACAS; see the file COPYING.  If not, write to the Free Software
 Foundation, 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.

-- end of CR notice --

