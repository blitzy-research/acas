*>
*> Payroll History
*>
     select  PY-History-File
                             assign        File-45
                             access        dynamic
                             organization  indexed
                             record key is His-Emp-No
                             status        PY-His-Emp-Status.
*>
