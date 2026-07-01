*>
*> Payroll Deductions (USA)
*>
     select  PY-System-Deduction-File
                             assign        File-42
                             access        dynamic
                             organization  is relative
                             relative key  is RRN
                             status        PY-Ded-Status.
*>
