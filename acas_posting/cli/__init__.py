"""ACAS batch posting cycle: the headless CLI batch entry points.

`acas_posting.cli` is the outermost layer of the COBOL-to-Python 3.12 migration
of the ACAS batch posting cycle. It holds the batch entry points that drive the
migrated programs, plus the binding of their linkage parameters, and nothing
else. Business logic lives only in `acas_posting.programs`.

WHAT THIS PACKAGE REPLACES
==========================
The four interactive COBOL menu shells - general/general.cbl, sales/sales.cbl,
purchase/purchase.cbl and irs/irs.cbl - together with the top-level
system-selection menu common/ACAS.cbl. All five are read as specification only:
AAP 0.2.2 lists every one of them as an out-of-scope interactive menu program.
What is migrated is their DISPATCH BEHAVIOUR - which program is called, with
which parameters, in which order, and under which abort gate - never the menu
programs themselves.

Their presentation layer is removed, not reimplemented. The menus drive a curses
screen section with inline `DISPLAY ... AT` and `ACCEPT ... AT` statements
interleaved through the dispatch paragraphs, and AAP 0.3.4 and 0.2.3 exclude
interactive screens, menus and report formatting from this migration - leaving
these batch entry points as the only interface. A diagnostic display with no
database effect becomes a log record; an `ACCEPT` that merely pauses for
acknowledgement is dropped; an `ACCEPT` that gates a database write becomes an
explicit parameter here, because its answer changes table state.

THE THREE LINKAGE SHAPES
========================
AAP 0.1.1: "The CLI contract is already written, in the LINKAGE SECTIONs." None
of the migrated programs is a main program; each is a CALLed sub-program with a
fixed parameter list, and there are exactly three distinct shapes - so this
package has three argument shapes, not one:

  Shape 1 - General Ledger, FOUR parameters:
      ws-calling-data, system-record, to-day, file-defs
      dispatched by general/general.cbl `load00.` L711-L721 (the CALL at
      L715-L718); callee signature e.g. general/gl070.cbl:L245-L248.

  Shape 2 - Sales and Purchase, FIVE parameters:
      ws-calling-data, System-Record, WS-System-Record-4, to-day, file-defs
      dispatched by sales/sales.cbl `load000.` L698-L712 (the CALL at
      L702-L706) and purchase/purchase.cbl `load000.` L691-L704 (L695-L699);
      callee signature e.g. sales/sl060.cbl:L395-L399, which names its third
      parameter `system-record-4`. FIVE, not four: the fourth system record is
      exactly what the Sales and Purchase shape adds to Shape 1.

  Shape 3 - IRS, THREE parameters:
      IRS-System-Params, WS-System-Record, file-defs
      dispatched inline from irs/irs.cbl `Main-Loop.` at L666-L672; callee
      signature irs/irs030.cbl:L552-L554. Materially different from the other
      two: NO calling-data block and NO `to-day`.

THE CONTROLLED CLOCK STOPS AT THIS BOUNDARY
===========================================
AAP 0.1.1: "inject them at the CLI boundary. No clock abstraction is needed
inside the migrated programs at all." Every in-scope posting program contains
zero clock reads and receives the run date purely through linkage, and the one
clock read in the whole call chain lives in the menu shells' date-service
copybook at copybooks/Proc-ACAS-Mapser-RDB.cob L72-L80. That block pins exactly
two observables, and so do these entry points: the text date `to-day pic x(10)`
in DD/MM/CCYY form (pinned at L77) and the binary `Run-Date` (L80; declared
`05 Run-Date binary-long.` at copybooks/wssystem.cob:L67). Nothing downstream
reads a clock, which is what makes two runs of one scenario byte-identical.

THIS MARKER IMPORTS NOTHING AND DOES NOTHING
============================================
Importing this module binds one name, `__all__`, and has no other observable
effect. It imports no sibling module, eagerly or lazily; it carries no lazy
`__getattr__` shim, no registry, no dispatch table and no convenience re-export
of `main` or `run`. It opens no connection and no file, creates no directory,
reads no process environment, configures no logging, starts nothing, and cannot
fail for an environmental reason.

That is a hard requirement rather than a matter of taste, because of who imports
it: the scenario test suites and `acas_posting.__main__`. A marker that pulled in
its siblings would drag the program layer, the data-access layer and a database
driver into every one of those imports, and the arithmetic parity tier's promise
that it touches no database and therefore runs anywhere would be broken on any
host without a database server.

THE RULES THAT BIND THIS FILE
=============================
`review_rules` reports no user rules document for this project, so the binding
constraints are the AAP's own six (0.7.2):

R-1 No COBOL at run time: nothing here spawns a child process, loads a foreign
    library or reaches the GnuCOBOL toolchain, and there is no import path from
    this package to the compiled comparison oracle - the oracle's own scripts
    invoke these entry points from outside, never the reverse.
R-2 No accounting value passes through a binary floating-point type.
R-3 No added validation, no added field, no schema change and no concurrency -
    no thread, no event loop, no worker process, no pool - so the abort gate
    between the General Ledger phases is a hard gate, not a warning.
R-4 Legacy behaviour is reproduced, never corrected. AAP 0.8.2, verbatim: "A
    defect reproduced is correct; a defect fixed is a failure."
R-5 Full traceability - see the footer below.
R-6 Compiled behaviour is the tie-breaker, so nothing here reads a clock or an
    entropy source or derives anything from its surroundings.
"""

from __future__ import annotations

from typing import Final

# The eight modules of this package, in AAP 0.3.1 target-tree order - not
# alphabetical and not execution order. These are MODULE NAMES, recorded for
# documentation and traceability only: listing a name here does NOT import it,
# and this marker never imports one. A caller imports the module explicitly, as
#     from acas_posting.cli import gl_post_cycle
# and then calls that module's own entry point.
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

# --- traceability ------------------------------------------------------------
#
# PACKAGE -> COBOL SOURCE (R-5)
#   acas_posting.cli  <-  general/general.cbl, sales/sales.cbl,
#   purchase/purchase.cbl, irs/irs.cbl, common/ACAS.cbl. All five are REFERENCE
#   only: frozen, read as specification, and out of scope as programs
#   (AAP 0.2.2). Any diff touching them is a defect in the migration.
#
# MODULE -> DISPATCH PARAGRAPH (spans measured against the frozen source)
#   gl_post_cycle    <- general/general.cbl    `load08.`     L805-L815
#                       gl070, then the `ws-term-code = 5` abort gate at
#                       L810-L811, then gl071, then gl072
#   gl_end_of_cycle  <- general/general.cbl    `load09.`     L817-L821  (gl080)
#   sl_invoice_post  <- sales/sales.cbl        `load07.`     L756-L768
#                       (sl055 then sl060, both through `load000.`)
#   sl_cash_post     <- sales/sales.cbl        `load11.`     L792-L796  (sl100)
#   pl_order_post    <- purchase/purchase.cbl  `load08.`     L752-L762
#                       (pl055 then pl060, both through `load000.`)
#   pl_payment_post  <- purchase/purchase.cbl  `load12.`     L786-L790  (pl100)
#   irs_post         <- irs/irs.cbl            `Main-Loop.`  L666-L672  (irs030)
#   args             <- copybooks/wscall.cob                 L6-L14
#                       `01 WS-Calling-Data`: WS-Called, WS-Caller, WS-Del-Link,
#                       WS-Term-Code, WS-Process-Func, WS-Sub-Function and
#                       WS-CD-Args (the last at L14, after the comment at L11)
#
# NOTE (label correction)
#   The Sales invoice-posting chain is `load07` (sales/sales.cbl L756-L768),
#   whose paragraph label carries the maintainer's own inline comment
#   `*> Sales trans posting` at sales/sales.cbl:L756. Two planning documents
#   label it `load08`; `load08` (L770-L774) actually dispatches sl080 (Payment
#   Input), which AAP 0.2.2 places out of scope. Do not "correct" `load07` back
#   to `load08`.
#
# OMISSIONS - recorded so that a reader comparing the two trees does not
# conclude something was lost (AAP 0.4.3):
#   * all menu screen I/O, the `display-menu` paragraph, and every `ACCEPT`
#     that merely pauses for acknowledgement;
#   * the `go to load01 ... load12 ... depending on z` dispatch tables
#     (general/general.cbl:L696-L704; common/ACAS.cbl:L558-L566, whose
#     `depending on z` phrase is at L565-L566);
#   * the menus' `overrewrite` persistence of System-Record, Default-Record and
#     WS-System-Record-4 (general/general.cbl:L656, sales/sales.cbl:L628,
#     purchase/purchase.cbl:L621) and the pre-run backup spool-out
#     `call "SYSTEM" using Full-Backup-Script` (general/general.cbl:L650,
#     sales/sales.cbl:L625, purchase/purchase.cbl:L618) - excluded by AAP
#     0.2.2's spool-out exclusion and by R-1;
#   * out-of-scope routes deliberately absent: the sl830 / pl830 autogen leg
#     (live at sales/sales.cbl:L759, already commented out at
#     purchase/purchase.cbl:L755-L758), general/general.cbl `load12.` L835-L855
#     (gl100 then gl105) and `load07.` L799-L803 (gl060), the Stock ledger
#     (common/ACAS.cbl:L606), the parameter-file set-up program sys002
#     (general/general.cbl:L628, common/ACAS.cbl:L534) and the end-of-cycle
#     driver xl150 (sales/sales.cbl:L881, purchase/purchase.cbl:L859);
#   * gl051's control-total gate has NO entry point in this package - AAP
#     0.4.1.1 lists none - so it is reached only as a library function,
#     `acas_posting.programs.gl051_batch_control_check`. The COBOL reaches the
#     whole interactive gl051 through general/general.cbl `load06.` L790-L797,
#     of which only the `end-batch` block (general/gl051.cbl L1096-L1133) is in
#     scope.
