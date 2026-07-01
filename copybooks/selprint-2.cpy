*>
*> removed org line seq as causing double line printing in OC CE
*>
*> 2023/02/18 vbc
*>  Special from original to support assign filename Print-File-Name in
*>   copybooks of print-spool-xxxxxxxx-2.cpy
*> 27/01/2024 vbc - Chgd to use LS
*>
       select  print-file     assign        PP-Print-File-Name
                             organization line sequential.
*>
