*>*******************************************
*>                                          *
*>          Stock Control record            *
*>                                          *
*>*******************************************
*> rec size 400 bytes (with fillers) 11/12/11
*> 02/06/09 vbc - Added PA code
*> 26/02/12 vbc - Chngd bins to comps 4 sql still 400
*> 01/07/16 vbc - Note that some programs use a 400 byte block to
*>                hold a copy of the record so if increased, these
*>                need to be changed through out the system.
*> 21/07/16 vbc - Remap Stock-History-Data content so each occurs 12
*>                instead of just Stock-History-Data.
*> 20/03/18 vbc - Total fields for period & year are now signed.
*> 27/06/20 vbc - Removed sign for all as trying to remove problems
*>                with accept comp signed fields in st010.
*> 07/02/24 vbc - Stock-Committed redefs Stock-Pre-Sales.
*> 30/03/24 vbc - New field Stock-Arrived-Date (within a filler)
*>                also updated fdstock.cob.
*> 04/02/25 vbc - Added WS- to Stock-Location.
*>
 01  WS-Stock-Record.
     03  WS-Stock-Key             pic x(13).
     03  WS-Stock-Abrev-Key       pic x(7).
     03  Stock-Suppliers-Group.
         05  Stock-Supplier-P1    pic x(7).                          *> Primary   Supplier
         05  Stock-Supplier-P2    pic x(7).                          *> Secondary Supplier
         05  Stock-Supplier-P3    pic x(7).                          *> Back Up   Supplier
     03  filler redefines Stock-Suppliers-Group.
         05  Stock-Suppliers      pic x(7)     occurs 3.  *> 41
     03  WS-Stock-Desc            pic x(32).              *> 73
     03  Stock-Construct-Item     pic x(13).              *> 86
     03  WS-Stock-Location        pic x(10).
     03  Stock-PA-Code.
         05  Stock-pa-System      pic x.
         05  Stock-pa-Group.
             07  Stock-pa-First   pic x.
             07  Stock-pa-Second  pic x.
     03  Stock-SA-Code.
         05  Stock-SA-System      pic x.
         05  Stock-SA-Group.
             07  Stock-SA-First   pic x.
             07  Stock-SA-Second  pic x.
     03  Stock-Services-Flag      pic x.                  *> 103  flag 4 services, not product (Y/N)
     03  Stock-Last-Actual-Cost   pic 9(7)v99     comp-3. *> (5) +1
     03  Stock-Arrived-Date       pic 9(8)       comp.   *> Last arrived, NEW 30/03/24 - 112
     03  filler                   pic x(4).              *> was 8 (30/03/24) 116
     03  Stock-Construct-Bundle   pic 9(6)       comp.  *> All signs removed 27/06/20
     03  Stock-Under-Construction pic 9(6)       comp.
     03  Stock-Work-in-Progress   pic 9(6)       comp.
     03  Stock-ReOrder-Pnt        pic 9(6)       comp.
     03  Stock-Std-ReOrder        pic 9(6)       comp.
     03  Stock-Back-Ordered       pic 9(6)       comp.
     03  Stock-On-Order           pic 9(6)       comp.
     03  Stock-Held               pic 9(6)       comp.
     03  Stock-Pre-Sales          pic 9(6)       comp.   *> 36 = 152
     03  Stock-Committed redefines Stock-Pre-Sales
                                  pic 9(6)       comp.
     03  Stock-Retail             pic 9(7)v99     comp-3. *> 5
     03  Stock-Cost               pic 9(7)v9999   comp-3. *> 6          Based on last Order Only
     03  Stock-Value              pic 9(9)v99     comp-3. *> 6 = 169
     03  Stock-Order-Due          pic 9(8)    comp.  *> binary-long unsigned.
     03  Stock-Order-Date         pic 9(8)    comp.  *> binary-long unsigned.   *> 177
     03  Stock-Mthly-Running-Totals.                    *> 16:    sign removed    cleared at EOY cycle
         05  Stock-Adds           pic 9(8)    comp.  *> binary-long.
         05  Stock-Deducts        pic 9(8)    comp.  *> binary-long.
         05  Stock-Wip-Adds       pic 9(8)    comp.  *> binary-long.
         05  Stock-Wip-Deds       pic 9(8)    comp.  *> binary-long.  *> 193
     03  Stock-History.
         05  Stock-History-Data.            *> 192:  zeroed for new year sign removed 27.06.20
             07  Stock-TD-Adds     pic 9(8)   comp    occurs 12. *> binary-long
             07  Stock-TD-Deds     pic 9(8)   comp    occurs 12. *> binary-long
             07  Stock-TD-Wip-Adds pic 9(8)   comp    occurs 12. *> binary-long
             07  Stock-TD-Wip-Deds pic 9(8)   comp    occurs 12. *> binary-long     *> 48 (x4) = 192 == 385
     03  filler                   pic x(15).                          *>400  expansion
*>
