*>
*> Payroll Check
*>
     select  PY-Check-File
                             assign        File-40
                             access        dynamic
                             organization  indexed
                             record key is Chk-Emp-No
                             status        PY-Chk-Status.
*>
