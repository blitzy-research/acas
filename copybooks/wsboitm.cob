*>*******************************************
*>                                          *
*>          BO Stk-Item  record             *
*>                                          *
*>*******************************************
*> Rec size 72 bytes (with filler)
*> 16/03/24 vbc - Created. [ DATES using days
*>                         since 1601.01.01 = 1
*> 20/03/24 vbc - Added Arrived-Flag within filler space.
*> 28/03/24 vbc - Added Inv-Type within filler area.
*> 07/04/24 vbc - Added missing Reference field + extra filler.
*> 19/04/24 vbc - Added BO-serial if BO extras due to non stock
*>                when processing BO on invoicing as same cust 'could' order
*>                same item again at a later time for a different order.
*>
 01  WS-BO-Stk-Itm-Record.
     03  WS-BO-Cust-Itm-No.                   *> Primary Key
         05  WS-BO-Stk-Cust-No  pic x(7).     *> Alt key 2
         05  WS-BO-Stk-Item-No  pic x(13).    *> Alt Key 2
         05  WS-BO-Serial       pic 99.       *> To avoid dups
     03  WS-BO-Stk-PO           pic x(10).
     03  WS-BO-Stk-Ref          pic x(10).
     03  WS-BO-Stk-Orig-Inv-No  pic 9(8).
     03  WS-BO-Stk-BO-Qty       pic 9(6).     *> 56
     03  WS-BO-Stk-BO-Arr-Date  binary-long.
     03  WS-BO-Stk-Order-Date   binary-long.  *> 64
     03  WS-BO-Stk-Price        pic 9(7)v99 comp-3.  *> 69
     03  WS-BO-Stk-Arrived-Flag pic x.
     03  WS-BO-Stk-Inv-Type     pic 9.
     03  filler                 pic x.        *> 72
*>
