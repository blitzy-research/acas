*>
*> Payroll Company History
*>
     select  PY-Comp-Hist-File
                             assign        File-41
                             access        dynamic
                             organization  relative
                             relative key  RRN    *> or Coh-Apply-No or ?
                             status        PY-Coh-Status.
*>
