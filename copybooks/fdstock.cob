*>*******************************************
*>                                          *
*>  File Definition For The Stock Control   *
*>                                          *
*>*******************************************
*> rec size 400 bytes (with fillers) 11/12/11 from 385
*> 02/06/09 vbc - Added PA code
*> 17/03/12 vbc - Field types chgd from bin long to comp still 400
*> 29/09/20 vbc - Removed sign(s) to match wsstock.cob
*> 07/02/24 vbc - Stock-Committed redefs Stock-Pre-Sales.
*> 30/03/24 vbc - New field Stock-Arrived-Date (within a filler).
*>                also updated wsstock.cob.
*>
 fd  Stock-File.
*>
 01  Stock-Record.
     03  Stock-Key                pic x(13).
     03  Stock-Abrev-Key          pic x(7).
     03  Stock-Suppliers-Group.
         05  Stock-Supplier-P1    pic x(7).                          *> Primary   Supplier
         05  Stock-Supplier-P2    pic x(7).                          *> Secondary Supplier
         05  Stock-Supplier-P3    pic x(7).                          *> Back Up   Supplier
     03  filler redefines Stock-Suppliers-Group.
         05  Stock-Suppliers      pic x(7)     occurs 3.  *> 41
     03  Stock-Desc               pic x(32).              *> 73
     03  Stock-Construct-Item     pic x(13).              *> 86
     03  Stock-Location           pic x(10).                         *> Mixed case
     03  Stock-PA-Code.
         05  Stock-pa-System      pic x.
         05  Stock-pa-Group.
             07  Stock-pa-First   pic x.
             07  Stock-pa-Second  pic x.
     03  Stock-SA-Code.
         05  Stock-sa-System      pic x.
         05  Stock-sa-Group.
             07  Stock-sa-First   pic x.
             07  Stock-sa-Second  pic x.
     03  Stock-Services-Flag      pic x.                  *> 103  flag 4 services, not product (Y/N)
     03  Stock-Last-Actual-Cost   pic 9(7)v99     comp-3. *> (5)
     03  Stock-Arrived-Date       pic 9(8)       comp.   *> Last arrived, NEW 30/03/24 - 112
     03  filler                   pic x(4).              *> was 8 (30/03/24) 116
     03  Stock-Construct-Bundle   pic 9(6)        comp.
     03  Stock-Under-Construction pic 9(6)        comp.
     03  Stock-Work-in-Progress   pic 9(6)        comp.
     03  Stock-ReOrder-Pnt        pic 9(6)        comp.
     03  Stock-Std-ReOrder        pic 9(6)        comp.
     03  Stock-Back-Ordered       pic 9(6)        comp.
     03  Stock-On-Order           pic 9(6)        comp.
     03  Stock-Held               pic 9(6)        comp.
     03  Stock-Pre-Sales          pic 9(6)        comp.   *> 36 = 152
     03  Stock-Committed redefines Stock-Pre-Sales
                                  pic 9(6)       comp.
     03  Stock-Retail             pic 9(7)v99     comp-3. *> 5    *> This 3 increased by 1 leading digit
     03  Stock-Cost               pic 9(7)v9999   comp-3. *> 6          Based on last Order Only
     03  Stock-Value              pic 9(9)v99     comp-3. *> 6 = 169
     03  Stock-Order-Due          pic 9(8)    comp.
     03  Stock-Order-Date         pic 9(8)    comp.   *> 177
     03  Stock-Mthly-Running-Totals.                 *> 16:    cleared at EOY cycle
         05  Stock-Adds           pic 9(8)    comp.  *> binary-long.
         05  Stock-Deducts        pic 9(8)    comp.  *> binary-long.
         05  Stock-Wip-Adds       pic 9(8)    comp.  *> binary-long.
         05  Stock-Wip-Deds       pic 9(8)    comp.  *> binary-long.
     03  Stock-History.
         05  Stock-History-Data.    *> 193:       zeroed for new year
             07  Stock-TD-Adds     pic 9(8)   comp  occurs 12.
             07  Stock-TD-Deds     pic 9(8)   comp  occurs 12.
             07  Stock-TD-Wip-Adds pic 9(8)   comp  occurs 12.
             07  Stock-TD-Wip-Deds pic 9(8)   comp  occurs 12.
     03  filler                   pic x(15).                           *> 400  expansion
