*>*******************************************
*>                                          *
*>  Record Definition For Employee          *
*>           File                           *
*>     Uses Emp-No as key                   *
*>*******************************************
*>  File size 508 bytes.
*>
*> THESE FIELDS DEFINITIONS MAY NEED CHANGING - Needs WB alignments 12/04/26
*>
*> 29/10/25 vbc - Created.
*> 10/11/25 vbc - Field changes.
*> 20/11/25 vbc - Phone# 12 -> 13 reduced filler to 14 & removed dup phone field.
*> 28/11/25 vbc - Zip code, SSN sizes chg.  Date fiormats are all ccyymmdd.
*> 02/12/25 vbc - Fields with -Allow chgd from x to 99.size will be the same.
*> 17/03/26 vbc - Mcare-Exempt added - File size change ?
*>
 01  PY-Employee-Record.
     03  Emp-No                pic 9(7)   comp.
     03  Emp-Status            pic x.     *> A = Active, T = Terminated, L = On leave & Hidden D = Deleted
     03  Emp-HS-Type           pic x.     *> H = Hourly or S = Salaried
     03  Emp-Pay-Interval      pic x.     *> W, M, B ( Bi weekly), S (semi-monthly
     03  Emp-Taxing-State      pic xx.    *> USA state code
     03  Emp-Job-Code          pic xxx.   *> information only
     03  Emp-Start-Date        pic 9(8)   comp. *> date started ccyymmdd
     03  Emp-Birth-Date        pic 9(8)   comp. *> ccyymmdd
     03  Emp-Term-Date         pic 9(8)   comp. *> date left  ccyymmdd - (last date of pay ?)
     03  Emp-Sex               pic x.     *> M, F
     03  Emp-Marital           pic x.     *> S, M
     03  Emp-Pay-Freq          binary-char.     *> 52, 24 or same / 2 = 26 / 12 Subject to change when looking at basic code
     03  Emp-Next-Del          pic x.     *> No idea yet
     03  Emp-SSN               pic 9(9)   comp.  *> 000-00-0000 & one spare for growth Excludes "-"
     03  Emp-Cur-Apply-No      pic 99.    *>  9  or ??  2 bytes
     03  Emp-Name              pic x(32). *> last 1st & middle init -NO> 1st middle last (middle can be initial only
     03  Emp-Search-Name       pic x(32). *> Uses Emp-Name to create Last, Middle & First Name - INDEX 2
     03  Emp-Address-1         pic x(32).
     03  Emp-Address-2         pic x(32).
     03  Emp-Address-3         pic x(32).
     03  Emp-Address-4         pic x(32).
     03  Emp-Post-Code.                   *> UK = 8 Canada 7 incl space,
         05  Emp-Zip           pic x(10).  *> 5 & + 5
         05  Emp-State         pic xx.
     03  Emp-Phone-No          pic 9(11). *> 01234-123456 / (123)-456-7890 09/12/25 reduced from 13
     03  Emp-Email             pic x(30). *> vbcoen@btconnect.com  + 10
     03  Emp-Bank-Acct-No      pic x(24). *> Allows also for sortcode/acct # (6+8) & - between numbers )
     03  Emp-Rate4-Exclusion   pic 9.     *> 1 = all taxes, 2 = All taxes except FICA,
                                          *> 3 = All except FICA,SWT, LWT 4 = none
     03  Emp-Cal-Head-Of-House pic x.     *> Y or N for all these
     03  Emp-Cal-Ded-Allow     pic 99    comp.
     03  Emp-FWT-Allow         pic 99    comp.
     03  Emp-SWT-Allow         pic 99    comp.
     03  Emp-LWT-Allow         pic 99    comp.
     03  Emp-Pension-Used      pic x. *> Y or N
     03  Emp-Eic-Used          pic x. *> all Y or N
     03  Emp-FWT-Exempt        pic x. *>
     03  Emp-SWT-Exempt        pic x. *>
     03  Emp-LWT-Exempt        pic x. *>
     03  Emp-FICA-Exempt       pic x. *>
     03  Emp-SDI-Exempt        pic x. *>
     03  Emp-Co-FUTA-Exempt    pic x. *>
     03  Emp-Co-SUI-Exempt     pic x. *>
     03  Emp-Mcare-Exempt      pic x. *>
     03  Emp-Sys-Exempt        pic x    occurs 5.
     03  Emp-Rate              pic 9(5)v99   comp-3  occurs 4.
     03  Emp-Auto-Units        pic 999       comp-3.
     03  Emp-Normal-Units      pic 999       comp-3.
     03  Emp-Max-Pay           pic 9(6)v99   comp-3.
     03  Emp-Vac-Rate          pic 9(5)v99   comp-3.
     03  Emp-Vac-Accum         pic 9(5)v99   comp-3.
     03  Emp-Vac-Used          pic 9(5)v99   comp-3.
     03  Emp-SL-Rate           pic 9(5)v99   comp-3.
     03  Emp-SL-Accum          pic 9(5)v99   comp-3.
     03  Emp-SL-Used           pic 9(5)v99   comp-3.
     03  Emp-Comp-Accum        pic 9(5)v99   comp-3.
     03  Emp-Comp-Used         pic 9(5)v99   comp-3.
     03  Emp-Dist-Grp                   occurs 5.   *> Distribution account and %
         05  Emp-Dist-Acct     binary-char  unsigned.
         05  Emp-Dist-Pcent    pic 999v99      comp-3.
     03  Emp-ED-Grp                     occurs 3.  *> Should this be 5 or even 10 ?
         05  Emp-Ed-Used       pic x.   *> Y or N /
         05  Emp-Ed-Group.
             07  Emp-ED-Factor     pic 9(6)v99   comp-3.
             07  Emp-ED-Limit      pic 9(6)v99   comp-3.
             07  Emp-ED-Amt-Pcent  pic x.   *> A  or P /
             07  Emp-ED-Acct-No    binary-char  unsigned. *> /
             07  Emp-ED-Desc       pic x(15).  *> /
             07  Emp-ED-Earn-Ded   pic x.   *> D or E /
             07  Emp-ED-Exclusion  pic 9.   *> /
             07  Emp-ED-Limit-Used pic x.   *> Y or N
             07  Emp-ED-Chk-Cat    pic 99   comp.  *> /
     03  filler                    pic x(11).
*>
