*>
*> Payroll Pay
*>
*> 22/04/26 vbc - Chg key to include Reporting-Cat as multi rec for emp-no.
*>
     select  PY-Pay-File
                             assign        File-46
                             access        dynamic
                             organization  indexed
                             record key is Pay-Emp-No-Cat
                             status        PY-Pay-Status.
*>
