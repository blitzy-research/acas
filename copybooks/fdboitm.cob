*>*******************************************
*>                                          *
*>  File Definition For The BO Stk-Item     *
*>          File                            *
*>                                          *
*>*******************************************
*> rec size 72 bytes (with filler)
*> ws copy book - wsbostkitm.cob
*> 16/03/24 vbc - Created. [ DATES using days
*>                         since 1601.01.01 = 1
*> 20/03/24 vbc - Added Arrived-Flag within filler space.
*> 28/03/24 vbc - Added Inv-Type within filler area.
*> 07/04/24 vbc - Added missing Reference field + extra filler.
*> 19/04/24 vbc - Added BO-serial if BO extras due to non stock
*>                when processing BO on invoicing as same cust 'could' order
*>                same item again at a later time for a different order.
*>
 fd  BO-Stk-Itm-File.
*>
 01  BO-Stk-Itm-Record.
     03  BO-Cust-Itm-No.                   *> Primary Key
         05  BO-Stk-Cust-No  pic x(7).     *> Alt key 2
         05  BO-Stk-Item-No  pic x(13).    *> Alt Key 2
         05  BO-Serial       pic 99.       *> To avoid dups
     03  BO-Stk-PO           pic x(10).
     03  BO-Stk-Ref          pic x(10).
     03  BO-Stk-Orig-Inv-No  pic 9(8).
     03  BO-Stk-BO-Qty       pic 9(6).     *> 56
     03  BO-Stk-BO-Arr-Date  binary-long.
     03  BO-Stk-Order-Date   binary-long.  *> 64
     03  BO-Stk-Price        pic 9(7)v99 comp-3.  *> 69
     03  BO-Stk-Arrived-Flag pic x.
     03  BO-Stk-Inv-Type     pic 9.
     03  filler              pic x.        *> 72
*>
