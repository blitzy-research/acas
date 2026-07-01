       >>source free
*>*********************************************
*> Dummy RDBMS support for v3.02 and later    *
*>        Where RDBMS is not wanted.          *
*>--------------------------------------------*
*>                                            *
*>  This will work for any RDBMS system.      *
*>                                            *
*>*********************************************
*>
 identification          division.
*>===============================
*>
*>**
      program-id.         dummmy.
*>**
*>    Author.             V.B.Coen FBCS, FIDM, FIDPM.
*>**
*>    Security.           Copyright (C) 2018-2025 & later, Vincent Bryan Coen.
*>                        Distributed under the GNU General Public License.
*>                        See the file COPYING for details.
*>**
*>    Remarks.            ACAS RDBMS dummy entry points
*>                        This module just includes dummy entry points
*>                        for all DAL units called throughout ACAS
*>                        where user does not want to use RDBMS but
*>                        only wishes to use Cobol files for all
*>                        processing.
*>
*>                        WARNING: If you wish to use rdbms later you will
*>                        need to recompile the ACAS system without this
*>                        module but with all modules names ending in MT.
*>**
*>    Version.            See Prog-Name In Ws.
*>**
*>    Calls:              All entry points are dummies.
*>**
*>    Error messages.     NONE, but all calls return 64.
*>**
*>    Changes.
*> 31/01/18 vbc - .00 ACAS dummy rdbms entry points to remove the need for
*>                    installation of the rdbms client package contains
*>                    the C packages all accesses Mysql or any other.
*> 25/06/23 vbc - .01 Added Autogen modules from Sales and Purchase.
*>                    Use ln to link folder common to each sub-system.
*> 16/04/24 vbc       Copyright notice update superseding all previous notices.
*> 19/09/25 vbc -3.3.00 Version update and builds reset.
*>
*>*************************************************************************
*>
*>  From copyright.cob.
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
*>******************************************************************************
*>
*> SUPPORT Service:
*>=================
*> Support for this system is available:
*>     Free via email on an as time is available basis ONLY.
*>     Paid for [Normal] subscription, via email/phone as required
*>      by customer within normal office hours Monday through Friday
*>       10:00 - 17:00. Response times within 4* hours E&OE.
*>       This is currently  £250.00 per year.
*>     Paid for [W/E] subscription, via email/phone as required by customer
*>       outside normal office hours and the weekend. Response within 1* hour
*>       E&OE.
*>       This is currently  £400.00 per year and includes Normal service.
*>       One weekend only fee is £225.00. By arrangement, <= 1 hour.
*>
*>  Email to vbcoen@gmail.com for details of subscriptions or for support
*>  with subject 'ACAS Bug' for support or 'ACAS subscription' for paid
*>   service.
*>
*>  Response times are usually within one hour but can be longer subject to
*>  other outstanding issues. All issues marked as 'critical' are one hour.
*>  The above response times are for paid subscription service only.
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
 data  division.
*>=============
*>
 working-storage section.
*>----------------------
 77  filler           pic x(15)    value "dummy (3.3.00)".
*>
 Linkage Section.
*>**************
*>
 copy "wsfnctn.cob".
*> Turn diags off regardless for this module.
 copy "Test-Data-Flags.cob"
             replacing ==03  SW-Testing               pic 9   value 1. ==
                 by    ==03  SW-Testing               pic 9   value zero. ==.
*>
 01  DUMMY-REC   pic x.
*>
 procedure division using File-Access
                          ACAS-DAL-Common-data
                          DUMMY-REC.
*>============================================
*>
 ACAS-Dummy-call-Group  Section.
*>
     entry    "analMT"       using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "auditMT"      using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "delfolioMT"   using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "deliveryMT"   using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "dfltMT"       using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "finalMT"      using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "glbatchMT"    using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "glpostingMT"  using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "irsdfltMT"    using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "irsfinalMT"   using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "irsnominalMT" using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "irspostingMT" using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "nominalMT"    using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "otm3MT"       using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "otm5MT"       using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "paymentsMT"   using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "plautogenMT"  using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "plinvoiceMT"  using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "purchMT"      using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "salesMT"      using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "slautogenMT"  using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "sldelinvnoMT" using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "slinvoiceMT"  using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "slpostingMT"  using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "stockMT"      using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "sys4MT"       using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "systemMT"     using  File-Access ACAS-DAL-Common-data DUMMY-REC.
     entry    "valueMT"      using  File-Access ACAS-DAL-Common-data DUMMY-REC.
*>
*> Error code = 64, in case caller expects a result.
*>
     move     99  to FS-Reply.
     move     999 to WE-Error.
     move     64 to RETURN-CODE.
     goback.
*>
