"""Batch entry points for the migrated ACAS posting cycle.

Every migrated COBOL program is a `CALL`ed sub-program with a fixed parameter
list, so the command-line contract was already written - in the LINKAGE
SECTIONs. This package binds those parameters to `argv` and dispatches the
program modules in the order the menu shell does, with no screen output of any
kind.

Nine modules: `args`, plus the seven entry points named in `__all__` -
`gl_post_cycle`, `gl_end_of_cycle`, `sl_invoice_post`, `sl_cash_post`,
`pl_order_post`, `pl_payment_post`, `irs_post` - and this marker. `args` binds
`01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14], the run date and the system
records; reproduces the menu shells' `aa005-Open-System.`,
`aa010-Get-System-Recs.` and `overrewrite.` paragraphs and the IRS
`zz090`/`zz095` remap pair; and in its SECTION 0 reproduces the frozen
connection-parameter loader `common/acas-get-params.cbl`, whose six values reach
the handlers only through `SYSTEM-REC`. The seven entry points reach the store
only through it.

Three linkage shapes, not one
    General Ledger      four parameters: ws-calling-data, system-record, to-day,
                        file-defs [general/gl070.cbl:L245-L248]
    Sales / Purchase    five: the same four plus the system-record-4 totals
                        record [sales/sl060.cbl:L395-L399]
    IRS                 three: IRS-System-Params, WS-System-Record, File-Defs -
                        no calling-data block [irs/irs030.cbl:L552-L554]

Two ways to invoke a route, and they are equivalent.
`python -m acas_posting <group> <operation> ...` routes through
`acas_posting/__main__.py`, which reproduces common/ACAS.cbl's system-selection
menu and forwards every remaining argument unchanged;
`python -m acas_posting.cli.<module> ...` reaches the same `main` directly. The
router declares no linkage option of its own, because common/ACAS.cbl:L577 calls
each subsystem menu with its `USING` phrase commented out, so both forms parse
the same argv with the same parser and return the same status.

Two behaviours the entry points preserve. THE ABORT GATE IS HARD, NOT A WARNING:
a batch left open makes gl070 raise the terminate code [general/gl070.cbl:L289]
and the menu returns instead of continuing [general/general.cbl:L800-L814], so
gl071 and gl072 never run. And a prompt that gates a database write becomes an
argument with the COBOL default preserved - the end-of-job question that clears
the IRS transfer file [irs/irs030.cbl:L1715-L1724] is an input because its answer
truncates a table - while a prompt that only pauses for acknowledgement is
dropped, keeping the control transfer and losing only the pause.

The menu programs themselves - general/general.cbl, sales/sales.cbl,
purchase/purchase.cbl, irs/irs.cbl and common/ACAS.cbl - are frozen reference
sources and out of scope as programs: their screen I/O, their `depending on z`
dispatch tables and their `call "SYSTEM"` backup spool-out are not migrated. WHAT
IS MIGRATED FROM THEM IS THE STATE THEY CARRY ACROSS A DISPATCH, once, in `args`.
Agent Action Plan section 0.8.5 makes an empty ordering-normalised diff the
acceptance test, and SYSTOT-REC is written by nine period-total sites whose only
writer to the store is `overrewrite`, so that persistence is part of the cycle's
observable behaviour rather than menu decoration. Only the ISAM arm of each
paragraph has no counterpart, the migration having a single store.

This marker binds `__all__` and the `Final` used to type it. It imports no
submodule and performs no input or output.
"""

from __future__ import annotations

from typing import Final

# The seven entry points, in AAP 0.3.1 target-tree order with `args` first - not
# alphabetical and not execution order. These are MODULE NAMES recorded for
# traceability: listing a name here does NOT import it, and this marker never
# imports one. A caller imports the module explicitly, as
#     from acas_posting.cli import gl_post_cycle
# and then calls that module's own entry point.
#
# `args` carries two things a reader may expect to find elsewhere, and the reasons
# are in its own module docstring: SECTION 0 is the connection-parameter loader,
# because SYSTEM-REC is the only carrier by which a connection parameter reaches
# the data-access layer [common/acas008.cbl:L558-L563]; and the menu paragraphs
# live there because AAP 0.4.1.1 defines the seven routes to include what their
# dispatch paragraphs `perform`. `args` is the one module of this package that
# reaches the data-access layer, and it reaches it only through
# `acas_posting.dal.facade` - never a `dal.acas*` handler, the edge AAP 0.4.3
# forbids.
__all__: Final[tuple[str, ...]] = (
    "args",
    "gl_post_cycle",
    "gl_end_of_cycle",
    "sl_invoice_post",
    "sl_cash_post",
    "pl_order_post",
    "pl_payment_post",
    "irs_post",
)
