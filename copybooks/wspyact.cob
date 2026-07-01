*>*******************************************
*>                                          *
*>  Record Definition For Accounts File     *
*>     Uses Act-No as key                   *
*>*******************************************
*>  File size 34 bytes.
*>
*> 29/10/25 vbc - Created.
*> 31/10/25 vbc - Renamed act-no to act-gl-no & added act-no.
*>                This subject to using py account info instead
*>                of direct to GL. Note IRS uses 5 and GL 6 digits.
*> 05/11/25 vbc   Chg Act-No to pic 99.
*> 12/11/25 vbc - Chg Gl-No  to display from comp.
*> 16/04/26 vbc - Added Type & 1 char Cat/filler. where type / Cat
*>                is 0 = Cash/C, 1 = Liability/L & 4 = Expense/E.
*>
 01  PY-Accounts-Record.
     03  Act-No              pic 99.
     03  Act-Type            pic 9.       *> 0=Cash, 1=Liability, 4=Expense.
     03  Act-Cat             pic x.       *> C=Cash, L=Liability, E=Expense
*>                                           Otherwise used as a filler
     03  Act-GL-No           pic 9(6).
     03  Act-Desc            pic x(24).
*>
