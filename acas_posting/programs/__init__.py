"""The migrated ACAS posting programs - one module per COBOL program.

Business logic lives only here. Each module exposes a `run(...)` entry whose
parameters mirror its program's `PROCEDURE DIVISION USING` list in order, with
the paragraph functions private to the module, so a caller cannot reach into a
program's internals any more than a COBOL `CALL` can.

All twelve program modules named in `__all__` - the inventory of Agent Action
Plan section 0.3.1 - ARE PRESENT in this package. Naming them here still imports
nothing: the marker deliberately performs no import, so that reaching this
package does not drag in twelve modules and, through them, the whole data-access
layer and a database driver. Import the module you need directly.

    gl051_batch_control_check       general/gl051.cbl - the control-total gate
                                    only [general/gl051.cbl:L1096-L1134]
    gl070_transaction_pre_process   general/gl070.cbl - phases 1 and 2
    gl071_batch_sort                general/gl071.cbl - a pure sort
    gl072_transaction_update        general/gl072.cbl - phase 4
    gl080_end_of_cycle              general/gl080.cbl - phases 3 and 5
    sl055_invoice_extract_analysis  sales/sl055.cbl
    sl060_invoice_posting           sales/sl060.cbl
    sl100_cash_posting              sales/sl100.cbl
    pl055_order_proof_extract       purchase/pl055.cbl
    pl060_order_posting             purchase/pl060.cbl
    pl100_payment_posting           purchase/pl100.cbl
    irs030_posting                  irs/irs030.cbl - `Ledger-Postings-Add`
                                    only [irs/irs030.cbl:L1569-L1730]

Two of the twelve are migrated only in part, and their boundaries are narrow
because both files are otherwise interactive: working from the file rather than
from the stated boundary would migrate several hundred lines that must not be.

Phase numbering is the programs' own and is not the execution order: deletion is
labelled phase 3 and runs after phase 4.

A program module may import `records`, `dal.facade`, the `cobol` semantics
primitives, `dates` and `workfiles`. It may not import `cli`, a `dal.acas*`
handler directly, or the compiled comparison oracle.
"""

from typing import Final

__all__: Final[tuple[str, ...]] = (
    "gl051_batch_control_check",
    "gl070_transaction_pre_process",
    "gl071_batch_sort",
    "gl072_transaction_update",
    "gl080_end_of_cycle",
    "sl055_invoice_extract_analysis",
    "sl060_invoice_posting",
    "sl100_cash_posting",
    "pl055_order_proof_extract",
    "pl060_order_posting",
    "pl100_payment_posting",
    "irs030_posting",
)
