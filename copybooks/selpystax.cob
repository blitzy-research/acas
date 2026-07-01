*>
*> Payroll Tax Withholdings Stax
*>
     select  PY-State-Tax-File
                             assign        File-54    *> pyswt {(ss)  = state code} not needed/used
                             organization  sequential
                             status        PY-Stax-Status.
*>
