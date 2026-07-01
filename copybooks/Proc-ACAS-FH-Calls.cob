*>>>LISTING OFF
*>
 zz080-ACAS-Processes      section.
*>********************************
*>
*> 18/04/17 vbc - 1.01 - Added new function Invoice-Read-Next-Header
*>                       for use with sl020, 050, 140.
*> 23/04/17 vbc - 1.02 - Added new calls for acas26 & 029 for P/L.
*> 25/04/17 vbc - 1.03 - Added acas000-Open-Input as open I/O will create if not exist
*>                       MUST WATCH OUT FOR THIS FOR THE OTHERS <<<<<
*> 12/01/18 vbc -      - IRS FH and DALs are not in this copybook although the IRS posting file
*>                       which is an optional input to IRS is as sl, pl, st can use it..
*> 16/01/18 vbc - 1.04 - Added Value-Delete-All for xl150.
*> 29/04/18 vbc - 1.05 - Changed all accessing other than open with 1st line of
*>                       move zero to Access-Type to keep logging clean.
*> 02/05/23 vbc - 1.06 - Add SLautogen & acas004, PLautogen & acas030
*> 09/05/23 vbc   1.07 - Above amended names to SL/PLautogen.
*> 14/08/23 vbc - 1.08 - Remove 'move zero to access-type for Start, it is set !!!
*>
 acas000.       *> System and dflt, final and system-record-4 NOTE that this FH only has four
 *>                                           parameters (no system-record from FD)
     call     "acas000" using System-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas004.       *> SLautogen
     move     1  to File-Key-No.
     call     "acas004" using System-Record
                              WS-Invoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas005.       *> GL Nominal Ledger
     move     1  to File-Key-No.
     call     "acas005" using System-Record
                              WS-Ledger-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas006.       *> GL Posting
     move     1  to File-Key-No.
     call     "acas006" using System-Record
                              WS-Posting-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas007.       *> GL Batch
     move     1  to File-Key-No.
     call     "acas007" using System-Record
                              WS-Batch-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas008.       *> SPL Posting
     move     1  to File-Key-No.
     call     "acas008" using System-Record
                              WS-IRS-Posting-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas010.       *> Stock Audit   Non ISAM type file/table
     move     1  to File-Key-No.
     call     "acas010" using System-Record
                              WS-Stock-Audit-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas011.       *> Stock    *> This one can use 3 File Key nos 1 - 3
     call     "acas011" using System-Record
                              WS-Stock-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas012.       *> Sales Ledger
     move     1  to File-Key-No.
     call     "acas012" using System-Record
                              WS-Sales-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas013.       *>  Value
     move     1  to File-Key-No.
     call     "acas013" using System-Record
                              WS-Value-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.

*>
 acas014.       *>  Delivery
     move     1  to File-Key-No.
     call     "acas014" using System-Record
                              WS-Delivery-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.

*>
 acas015.       *> Analysis
     move     1  to File-Key-No.
     call     "acas015" using System-Record
                              WS-Analysis-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas016.       *> Invoice
     move     1  to File-Key-No.
     call     "acas016" using System-Record
                              WS-Invoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas017.       *> DelInvNo
     move     1  to File-Key-No.
     call     "acas017" using System-Record
                              WS-Del-Inv-Nos-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas019.       *> Open-Item-3
     move     1  to File-Key-No.
     call     "acas019" using System-Record
                              WS-OTM3-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas022.       *> Purchase Ledger
     move     1  to File-Key-No.
     call     "acas022" using System-Record
                              WS-Purch-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas023.       *> Delete Folio
     move     1  to File-Key-No.
     call     "acas023" using System-Record
                              WS-Del-Inv-Nos-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
 acas026.       *> PInvoice
     move     1  to File-Key-No.
     call     "acas026" using System-Record
                              WS-PInvoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas029.       *> Open-Item-5
     move     1  to File-Key-No.
     call     "acas029" using System-Record
                              WS-OTM5-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas030.       *> PLautogen
     move     1  to File-Key-No.
     call     "acas030" using System-Record
                              WS-PInvoice-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-data.
*>
 acas032.       *> Purchase Payments
     move     1  to File-Key-No.
     call     "acas032" using System-Record
                              WS-Pay-Record
                              File-Access
                              File-Defs
                              ACAS-DAL-Common-Data.
*>
*>  These are for acas000
*>
 System-Open.
 *>    set      fn-open  to true.
     move     1  to File-Function.
 *>    set      fn-i-o to true.
     move     2 to Access-Type.
     perform  acas000.
*>
 System-Open-Input.
 *>    set      fn-open  to true.
     move     1  to File-Function.
 *>    set      fn-Input to true.
     move    1 to Access-Type.
     perform  acas000.
*>
 System-Open-Output.
 *>    set      fn-open  to true.
     move     1  to File-Function.
 *>    set      fn-Output to true.
     move    3 to Access-Type.
     perform  acas000.
*>
 System-Close.
     move     zero to Access-Type.
 *>    set      fn-Close to true.
     move     2  to File-Function.
     perform  acas000.
*>
 System-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas000.
*>
 System-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas000.
*>
 System-ReWrite.
     move     zero to Access-Type.
     set      fn-re-write to true.
     perform  acas000.
*>
*> These are for acas004
*>
 SLautogen-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas004.
*>
 SLautogen-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas004.
*>
 SLautogen-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas004.
*>
 SLautogen-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas004.
*>
 SLautogen-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas004.
*>
 SLautogen-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas004.
*>
 SLautogen-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas004.
*>
 SLautogen-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas004.
*>
 SLautogen-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas004.
*>
 SLautogen-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas004.
*>
 SLautogen-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas004.
*>
 SLautogen-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas004.
*>
*>  These are for acas005
*>
 GL-Nominal-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas005.
*>
 GL-Nominal-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas005.
*>
 GL-Nominal-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas005.
*>
 GL-Nominal-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas005.
*>
 GL-Nominal-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas005.
*>
 GL-Nominal-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas005.
*>
 GL-Nominal-Start.
     set      fn-Start to true.
     perform  acas005.
*>
 GL-Nominal-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas005.
*>
 GL-Nominal-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas005.
*>
 GL-Nominal-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas005.
*>
 GL-Nominal-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas005.
*>
*>  These are for acas006
*>
 GL-Posting-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas006.
*>
 GL-Posting-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas006.
*>
 GL-Posting-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas006.
*>
 GL-Posting-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas006.
*>
 GL-Posting-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas006.
*>
 GL-Posting-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas006.
*>
 GL-Posting-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas006.
*>
 GL-Posting-Start.
     set      fn-Start to true.
     perform  acas006.
*>
 GL-Posting-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas006.
*>
 GL-Posting-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas006.
*>
 GL-Posting-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas006.
*>
 GL-Posting-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas006.
*>
*>  These are for acas007
*>
 GL-Batch-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas007.
*>
 GL-Batch-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas007.
*>
 GL-Batch-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas007.
*>
 GL-Batch-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas007.
*>
 GL-Batch-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas007.
*>
 GL-Batch-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas007.
*>
 GL-Batch-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas007.
*>
 GL-Batch-Start.
     set      fn-Start to true.
     perform  acas007.
*>
 GL-Batch-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas007.
*>
 GL-Batch-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas007.
*>
 GL-Batch-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas007.
*>
 GL-Batch-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas007.
*>
*>  These are for acas008
*>
 SPL-Posting-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas008.
*>
 SPL-Posting-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas008.
*>
 SPL-Posting-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas008.
*>
 SPL-Posting-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas008.
*>
 SPL-Posting-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas008.
*>
 SPL-Posting-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas008.
*>
 SPL-Posting-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas008.
*>
 SPL-Posting-Start.
     set      fn-Start to true.
     perform  acas008.
*>
 SPL-Posting-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas008.
*>
 SPL-Posting-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas008.
*>
 SPL-Posting-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas008.
*>
 SPL-Posting-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas008.
*>
*>  These are for acas010
*>
 Stock-Audit-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas010.
*>
 Stock-Audit-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas010.
*>
 Stock-Audit-Open-Output.
     set      fn-open   to true.
     set      fn-output to true.
     perform  acas010.
*>
 Stock-Audit-Open-Extend.
     set      fn-open   to true.
     set      fn-extend to true.
     perform  acas010.
*>
 Stock-Audit-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas010.
*>
 Stock-Audit-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas010.
*>
 Stock-Audit-Start.
     set      fn-Start to true.
     perform  acas010.
*>
 Stock-Audit-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas010.
*>
 Stock-Audit-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas010.
*>
 Stock-Audit-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas010.
*>
 Stock-Audit-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas010.
*>
*> These are for acas011
*>
 Stock-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas011.
*>
 Stock-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas011.
*>
 Stock-Open-Output.
     set      fn-open to true.
     set      fn-output  to true.
     perform  acas011.
*>
 Stock-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas011.
*>
 Stock-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas011.
*>
 Stock-Start.
     set      fn-Start to true.
     perform  acas011.
*>
 Stock-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas011.
*>
 Stock-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas011.
*>
 Stock-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas011.
*>
 Stock-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas011.
*>
*> These are for acas012
*>
 Sales-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas012.
*>
 Sales-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas012.
*>
 Sales-Open-Output.
     set      fn-open to true.
     set      fn-output  to true.
     perform  acas012.
*>
 Sales-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas012.
*>
 Sales-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas012.
*>
 Sales-Start.
     set      fn-Start to true.
     perform  acas012.
*>
 Sales-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas012.
*>
 Sales-Read-Next-Sorted-By-Name.
     move     zero to Access-Type.
     set      fn-Read-By-Name to true.
     perform  acas012.
*>
 Sales-Read-Indexed.
     move     zero to Access-Type.
     set      fn-Read-Indexed to true.
     perform  acas012.
*>
 Sales-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas012.
*>
 Sales-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas012.
*>
*>  These are for acas013
*>
 Value-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas013.
*>
 Value-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas013.
*>
 Value-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas013.
*>
 Value-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas013.
*>
 Value-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas013.
*>
 Value-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas013.
*>
 Value-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas013.
*>
 Value-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas013.
*>
 Value-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas013.
*>
 Value-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas013.
*>
 Value-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas013.
*>
*>  These are for acas014
*>
 Delivery-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas014.
*>
 Delivery-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas014.
*>
 Delivery-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas014.
*>
 Delivery-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas014.
*>
 Delivery-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas014.
*>
 Delivery-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas014.
*>
 Delivery-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas014.
*>
 Delivery-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas014.
*>
 Delivery-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas014.
*>
 Delivery-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas014.
*>
 Delivery-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas014.
*>
*> These are for acas015
*>
 Analysis-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas015.
*>
 Analysis-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas015.
*>
 Analysis-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas015.
*>
 Analysis-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas015.
*>
 Analysis-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas015.
*>
 Analysis-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas015.
*>
 Analysis-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas015.
*>
 Analysis-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas015.
*>
 Analysis-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas015.
*>
 Analysis-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas015.
*>
*> These are for acas016
*>
 Invoice-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas016.
*>
 Invoice-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas016.
*>
 Invoice-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas016.
*>
 Invoice-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas016.
*>
 Invoice-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas016.
*>
 Invoice-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas016.
*>
 Invoice-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas016.
*>
 Invoice-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas016.
*>
 Invoice-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas016.
*>
 Invoice-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas016.
*>
 Invoice-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas016.
*>
 Invoice-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas016.
*>
*> These are for acas017
*>
 DelInvNos-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas017.
*>
 DelInvNos-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas017.
*>
 DelInvNos-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas017.
*>
 DelInvNos-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas017.
*>
 DelInvNos-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas017.
*>
 DelInvNos-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas017.
*>
 DelInvNos-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas017.
*>
 DelInvNos-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas017.
*>
 DelInvNos-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas017.
*>
 DelInvNos-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas017.
*>
 DelInvNos-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas017.
*>
*> These are for acas019
*>
 OTM3-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas019.
*>
 OTM3-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas019.
*>
 OTM3-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas019.
*>
 OTM3-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas019.
*>
 OTM3-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas019.
*>
 OTM3-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas019.
*>
 OTM3-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas019.
*>
 OTM3-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas019.
*>
 OTM3-Read-Next-Sorted-By-Batch.
     move     zero to Access-Type.
     set      fn-Read-By-Batch to true.
     perform  acas019.
*>
 OTM3-Read-Next-Sorted-By-Cust.
     move     zero to Access-Type.
     set      fn-Read-By-Cust to true.
     perform  acas019.
*>
 OTM3-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas019.
*>
 OTM3-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas019.
*>
*> These are for acas022
*>
 Purch-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas022.
*>
 Purch-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas022.
*>
 Purch-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas022.
*>
 Purch-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas022.
*>
 Purch-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas022.
*>
 Purch-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas022.
*>
 Purch-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas022.
*>
 Purch-Read-Next-Sorted-ByName.
     move     zero to Access-Type.
     set      fn-Read-By-Name to true.
     perform  acas022.
*>
 Purch-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas022.
*>
 Purch-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas022.
*>
 Purch-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas022.
*>
*> These are for acas023
*>
 DelFolio-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas023.
*>
 DelFolio-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas023.
*>
 DelFolio-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas023.
*>
 DelFolio-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas023.
*>
 DelFolio-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas023.
*>
 DelFolio-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas023.
*>
 DelFolio-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas023.
*>
 DelFolio-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas023.
*>
 DelFolio-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas023.
*>
 DelFolio-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas023.
*>
 DelFolio-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas023.
*>
*> These are for acas026
*>
 PInvoice-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas026.
*>
 PInvoice-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas026.
*>
 PInvoice-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas026.
*>
 PInvoice-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas026.
*>
 PInvoice-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas026.
*>
 PInvoice-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas026.
*>
 PInvoice-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas026.
*>
 PInvoice-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas026.
*>
 PInvoice-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas026.
*>
 PInvoice-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas026.
*>
 PInvoice-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas026.
*>
 PInvoice-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas026.
*>
*> These are for acas029
*>
 OTM5-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas029.
*>
 OTM5-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas029.
*>
 OTM5-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas029.
*>
 OTM5-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas029.
*>
 OTM5-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas029.
*>
 OTM5-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas029.
*>
 OTM5-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas029.
*>
 OTM5-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas029.
*>
 OTM5-Read-Next-Sorted-By-Batch.
     move     zero to Access-Type.
     set      fn-Read-By-Batch to true.
     perform  acas029.
*>
 OTM5-Read-Next-Sorted-By-Cust.
     move     zero to Access-Type.
     set      fn-Read-By-Cust to true.
     perform  acas029.
*>
 OTM5-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas029.
*>
 OTM5-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas029.
*>
*>  02/05/23
*> These are for acas030 - PLautogen
*>
 PLautogen-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas030.
*>
 PLautogen-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas030.
*>
 PLautogen-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas030.
*>
 PLautogen-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas030.
*>
 PLautogen-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas030.
*>
 PLautogen-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas030.
*>
 PLautogen-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas030.
*>
 PLautogen-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas030.
*>
 PLautogen-Read-Next-Header.
     move     zero to Access-Type.
     set      fn-Read-Next-Header to true.
     perform  acas030.
*>
 PLautogen-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas030.
*>
 PLautogen-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas030.
*>
 PLautogen-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas030.
*>
*> These are for acas032
*>
 Payments-Open.
     set      fn-open to true.
     set      fn-i-o  to true.
     perform  acas032.
*>
 Payments-Open-Input.
     set      fn-open  to true.
     set      fn-input to true.
     perform  acas032.
*>
 Payments-Open-Output.
     set      fn-open  to true.
     set      fn-Output to true.
     perform  acas032.
*>
 Payments-Close.
     move     zero to Access-Type.
     set      fn-Close to true.
     perform  acas032.
*>
 Payments-Delete.
     move     zero to Access-Type.
     set      fn-Delete to true.
     move     1 to File-Key-No.
     perform  acas032.
*>
 Payments-Delete-All.
     move     zero to Access-Type.
     set      fn-Delete-All to true.
     move     1 to File-Key-No.
     perform  acas032.
*>
 Payments-Start.
     move     1 to File-Key-No.
     set      fn-Start to true.
     perform  acas032.
*>
 Payments-Read-Next.
     move     zero to Access-Type.
     set      fn-Read-Next to true.
     perform  acas032.
*>
 Payments-Read-Indexed.
     move     zero to Access-Type.
     move     1 to File-Key-No.
     set      fn-Read-Indexed to true.
     perform  acas032.
*>
 Payments-Write.
     move     zero to Access-Type.
     set      fn-Write to true.
     perform  acas032.
*>
 Payments-Rewrite.
     move     zero to Access-Type.
     set      fn-Re-write to true.
     perform  acas032.
*>
 zz080-Exit.
     exit section.
*>
*>>>LISTING ON
