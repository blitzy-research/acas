*>
*> Payroll Pay Hours (USA)
*> Key in 2 parts, emp no and Trans-code
*>
     select  PY-Pay-Transactions-File
                             assign        file-45
                             access        dynamic
                             organization  indexed
                             record key is Hrs-Key
                             status        PY-Hrs-Status.
*>
