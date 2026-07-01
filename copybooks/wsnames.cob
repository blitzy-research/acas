*>
*> Sales, Purchase, Stock, General & now IRS for v3.3 with integrated IRS
*>    for use in xl150 and ??
*>
*>  Files used in Sales, Stock, Purchase, General & IRS
*> 17/11/16 vbc - Added IRS files + their renaming with irs prefix.
*> 04/12/16 vbc - Added irs055 sort file as file-38.
*> 09/05/23 vbc - Added PL & SL autogen (files04, 30 increased count to 38
*> 16/03/24 vbc - Added Sales Bo-Stk-Itm as file31  increased count to 39
*> 21/10/25 vbc - Added Payroll - USA/Canada - other files needed for elsewhere
*>                inc UK / Europe etc.
*>
 01  File-Defs.
     02  file-defs-a.
         03  pre-trans-name   pic x(532)  value "pretrans.tmp". *> gl071
         03  post-trans-name  pic x(532)  value "postrans.tmp". *> gl071
 copy "file00.cob".    *> "system"
*>                        No file 1
 copy "file02.cob".    *> "archive".
 copy "file03.cob".    *> "final".
 copy "file04.cob".    *> "SLautogen"
 copy "file05.cob".    *> "ledger".
 copy "file06.cob".    *> "posting".
 copy "file07.cob".    *> "batch".
 copy "file08.cob".    *> "postings2irs.dat"
 copy "file09.cob".    *> "tmp-stock".
 copy "file10.cob".    *> "staudit".
 copy "file11.cob".    *> "stockctl".
 copy "file12.cob".    *> "salesled".
 copy "file13.cob".    *> "value.dat"
 copy "file14.cob".    *> "delivery.dat"
 copy "file15.cob".    *> "analysis.dat"
 copy "file16.cob".    *> "invoice ".
 copy "file17.cob".    *> "delinvno".
 copy "file18.cob".    *> "openitm2".
 copy "file19.cob".    *> "openitm3".
 copy "file20.cob".    *> "oisort".
 copy "file21.cob".    *> "work.tmp"
 copy "file22.cob".    *> "purchled"
 copy "file23.cob".    *> "delfolio.dat"
 copy "file24.cob".    *> dummy to build file-02
*>                        No file 25
 copy "file26.cob".    *> "pinvoice"
 copy "file27.cob".    *> "poisort"
 copy "file28.cob".    *> "openitm4"
 copy "file29.cob".    *> "openitm5"
 copy "file30.cob".    *> "PLautogen.dat"
 copy "file31.cob".    *> "boStkitm.dat" NEw 16/03/24
 copy "file32.cob".    *> "pay.dat"
 copy "file33.cob".    *> "cheque.dat"
         03  file-34          pic x(532)  value "irsacnts.dat".        *> IRS ex file 1  These 4 added 19/10/16 for IRS integration
         03  file-35          pic x(532)  value "irsdflt.dat".         *> IRS ex file 3  all name have 'irs' prefix.
         03  file-36          pic x(532)  value "irspost.dat".         *> IRS ex file 4
         03  file-37          pic x(532)  value "irsfinal.dat".        *> IRS ex file 5
         03  file-38          pic x(532)  value "postsort.dat".        *> IRS ex irs055 sort file.

*> Code for Payroll  AND INCREASE occurs both times
         03  file-39          pic x(532)  value "pyact.dat".               *> PY account
         03  file-40          pic x(532)  value "pychk.dat".               *> PY check / bacs
         03  file-41          pic x(532)  value "pycoh.dat".               *> PY company history
         03  file-42          pic x(532)  value "pyded.dat".               *> PY deduction {/ earnings}
         03  file-43          pic x(532)  value "pyemp.dat".               *> PY employee master
         03  file-44          pic x(532)  value "pyhis.dat".               *> PY employee (pay) history
         03  file-45          pic x(532)  value "pyhrs.dat".               *> PY pay trans
         03  file-46          pic x(532)  value "pypay.dat".               *> PY pay detail jrn + header ???
         03  file-47          pic x(532)  value "pypr1.dat".               *> PY param 1
         03  file-48          pic x(532)  value "pypr2.dat".               *> PY param 2
*> TABLES Blk 1
         03  file-49          pic x(532)  value "pycalm.dat".              *> PY  calx - x = s,m,h, x?
         03  file-50          pic x(532)  value "pycals.dat".              *> PY
         03  file-51          pic x(532)  value "pycalh.dat".              *> PY
         03  file-52          pic x(532)  value "pycalx.dat".              *> PY  california special tables ???
         03  file-53          pic x(532)  value "pylwt.dat".               *> PY  tax table ???
         03  file-54          pic x(532)  value "pyswtaa.dat".             *> PY  swt aa = State abbrev. code Only one used
         03  file-55          pic x(532)  value "pyglcoann.dat".           *> PY gl CoA transfer ??
         03  file-56          pic x(532)  value "pyglgjbss.dat".           *> PY  ???
*> Not sure about these two up/down
           03  file-57          pic x(532)  value "pycal.dat".             *> PY  ??? calm,s,h etc
*>
     02  filler         redefines file-defs-a.
         03  System-File-Names   pic x(532) occurs 58.            *> 39 chg for sales BO file plus py
     02  File-Defs-Count         binary-short value 58.           *> MUST be the same as above occurs
     02  File-Defs-os-Delimiter  pic x.                           *> if = \ or / then paths have been set.
*>
