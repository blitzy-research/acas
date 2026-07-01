*>
*> Payroll Employee (USA)
*>
     select  PY-Employee-File
                             assign               File-43
                             access               dynamic
                             organization         indexed
                             record key is        Emp-No
                             alternate record key Emp-Search-Name with duplicates
                             status               PY-Emp-Status.
*>
