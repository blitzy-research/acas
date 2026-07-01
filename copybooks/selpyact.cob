*>
*> Payroll Accounts
*>
     select  PY-Accounts-File
                             assign        File-39
                             access        dynamic
                             organization  indexed
                             record key is Act-No
                             status        PY-Act-Status.
*>
