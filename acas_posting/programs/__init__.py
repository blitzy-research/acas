"""ACAS posting cycle: one Python module per in-scope COBOL program.

`acas_posting.programs` is the business-logic layer of the COBOL-to-Python
3.12 migration of the ACAS batch posting cycle, and it is the ONLY place
business logic lives. Twelve COBOL programs are in scope, so this package
holds exactly twelve modules plus this marker: the folder is closed at
thirteen files.

The converse is equally binding. Picture-clause arithmetic, packed-decimal
(COMP-3), binary (COMP / BINARY-LONG) and SIGN LEADING display storage, MOVE
truncation and padding, 88-level condition-name evaluation and SORT key
ordering are implemented in `acas_posting.cobol` and never here. AAP 0.3.1,
verbatim:

    "`cobol/` contains no business logic and `programs/` contains no numeric
    primitives."

and, on why that split exists:

    "This split is what makes the arithmetic parity suite possible ... any
    parity failure localises immediately to one layer or the other."

PUBLIC SURFACE. AAP 0.3.3, verbatim:

    "Each `programs/*.py` module exposes a single `run(...)` entry mirroring
    its COBOL `PROCEDURE DIVISION USING` list, with the paragraph functions
    private to the module. Callers cannot reach into a program's internals,
    exactly as a COBOL `CALL` cannot."

Every paragraph function therefore carries a leading underscore. A caller
writes `from acas_posting.programs import gl070_transaction_pre_process` and
then calls `gl070_transaction_pre_process.run(...)`; nothing else in a
program module is public. This marker re-exports nothing and imports no
submodule of its own, so importing the package pulls in neither the
data-access layer nor any database driver.

PROGRAM -> MODULE TRACEABILITY (R-5). Line counts verified against the
frozen source.

  | COBOL program      | Lines | Python module                  | Boundary    |
  |--------------------|-------|--------------------------------|-------------|
  | general/gl051.cbl  |  1282 | gl051_batch_control_check      | PARTIAL (1) |
  | general/gl070.cbl  |   612 | gl070_transaction_pre_process  | whole (2)   |
  | general/gl071.cbl  |   182 | gl071_batch_sort               | whole (3)   |
  | general/gl072.cbl  |   498 | gl072_transaction_update       | whole (4)   |
  | general/gl080.cbl  |   750 | gl080_end_of_cycle             | whole (5)   |
  | sales/sl055.cbl    |   732 | sl055_invoice_extract_analysis | whole (8)   |
  | sales/sl060.cbl    |  1301 | sl060_invoice_posting          | whole (6)   |
  | sales/sl100.cbl    |   817 | sl100_cash_posting             | whole (8)   |
  | purchase/pl055.cbl |   635 | pl055_order_proof_extract      | whole (8)   |
  | purchase/pl060.cbl |  1155 | pl060_order_posting            | whole (6)   |
  | purchase/pl100.cbl |   798 | pl100_payment_posting          | whole (8)   |
  | irs/irs030.cbl     |  1733 | irs030_posting                 | PARTIAL (7) |

(1) gl051 PARTIAL: `batch-print` section 999 (L999-L1168) including
    `end-batch` L1096-L1134, the arithmetic paragraphs `net.` L788,
    `gross.` L793 and `get-description.` L799, and the account scaling at
    L603-L608 / L653-L658. Everything else in gl051 -- screen sections,
    accept loops, the batch-amendment dialog -- is out of scope.
(2) Whole posting path: Phase 1 batch check plus Phase 2 transaction
    pre-process.
(3) Whole program, a pure sort: zero arithmetic statements and zero `GO TO`
    sites.
(4) Whole program: Phase 4 transaction update.
(5) Whole program: Phase 2 archiving, Phase 3 transaction deletion and
    Phase 5 end-of-period processing.
(6) Whole program, including the IRS fan-out.
(7) irs030 PARTIAL: `Ledger-Postings-Add` L1569-L1730, plus `Net` section
    1544 and `Gross` section 1556 whose two ROUNDED VAT computes the posting
    path consumes. The rest of irs030 -- interactive posting entry,
    amendment, screen handling -- is out of scope.
(8) Whole program, no further qualification.

THREE LINKAGE SHAPES, not one. `run(...)` mirrors its program's
`PROCEDURE DIVISION USING` list, and the in-scope set has exactly three
shapes, named as the frozen source spells them:

  * GL, four parameters -- `ws-calling-data, system-record, to-day,
    file-defs`: gl051 L353-L356, gl070 L245-L248, gl071 L161-L164,
    gl072 L262-L265, gl080 L269-L272.
  * SL/PL, five parameters -- `ws-calling-data, system-record,
    system-record-4, to-day, file-defs`: sl055 L271-L275, sl060 L395-L399,
    sl100 L272-L276, pl055 L239-L243, pl060 L340-L344, pl100 L265-L269. The
    added parameter is literally `system-record-4` -- the fourth system
    record, sitting third in the list; the AAP's paraphrase
    `WS-System-Record-4` is not the source spelling.
  * IRS, three parameters and materially different -- `IRS-System-Params,
    WS-System-Record, File-Defs` at irs030 L552-L554. NO calling-data block
    and NO `to-day`, corroborated by irs030 carrying no `copy "wscall.cob"`
    at all. Its end-of-job question (irs030 L1715-L1724) gates a table
    truncation, so it is an explicit `run(...)` parameter with the COBOL
    default preserved, not a prompt.

PHASE ORDER, AND WHY THE NUMBERS LOOK WRONG. The cycle runs: Phase 1 batch
check (gl070 L284) -> Phase 2 transaction pre-process (gl070 L292) -> the
sort (gl071) -> Phase 4 transaction update (gl072 L274) -> Phase 2 archiving
(gl080 L316) or Phase 3 transaction deletion (gl080 L319) -> Phase 5
end-of-period (gl080 L336). The numbering is NOT sequential with execution:
deletion is labelled Phase 3 yet executes after Phase 4, gl080 re-displays
its own "Phase - 1. Batch Check" at L306, and it labels posting contraction
"Phase - 4." at L637. Each module's docstring keeps the labels exactly as the
screens print them, "so a maintainer is not misled" (AAP 0.6.4). (The AAP
cites gl072 L277 for the Phase 4 banner; the banner is verified at L274 in
the frozen source, L277 being `perform GL-Nominal-Open.`.) A hard gate
separates the phases: gl070 raising the terminate code on an open batch means
gl071 and gl072 never run at all, and that gate belongs to the CLI,
reproduced as an abort rather than a warning.

LAYERING (AAP 0.4.3). Modules in this package MAY import:

  * `acas_posting.records.*` -- the record dataclasses;
  * `acas_posting.dal.facade` and `acas_posting.dal.status` -- the verb
    vocabulary and the `FS-Reply` / `We-Error` status protocol;
  * `acas_posting.cobol.arithmetic`, `.move`, `.condition_names`, `.field`
    and `.picture`;
  * `acas_posting.dates` and `acas_posting.workfiles`;
  * the standard library: `decimal`, `logging`, `dataclasses`, `typing`.

Modules in this package MUST NOT import: `acas_posting.cli`; any
`acas_posting.dal.acas*` handler module directly;
`acas_posting.dal.connection`; `acas_posting.dal.cursor_state`; the
controlled-clock module at the package root;
`acas_posting.dictionary.generate`; the sibling compiled-oracle tree, which
is a sibling of `acas_posting` rather than a sub-package precisely so that
no import path to it exists; or any other module in this same package --
programs do not call programs, because sequencing is the CLI's job.

ONE EXCEPTION. `gl071_batch_sort` imports neither `acas_posting.dal.facade`
nor `acas_posting.dal.status`: the entire `COPY` list of general/gl071.cbl is
`envdiv.cob` L85, `wscall.cob` L155, `wssystem.cob` L156 and `wsnames.cob`
L157 -- no facade copybook and not even `wsfnctn.cob` -- and it performs zero
data-access verbs.

TWO FACADE ALIAS SETS, the most misreadable thing about this package
(AAP 0.6.5). Ten of the twelve programs `copy "Proc-ACAS-FH-Calls.cob"`
(gl051 L1281, gl070 L611, gl072 L497, gl080 L749, sl055 L731, sl060 L1300,
sl100 L816, pl055 L634, pl060 L1154, pl100 L797) and therefore call the
ENTITY-named vocabulary -- `facade.gl_batch_read_next(ctx)`,
`facade.value_rewrite(ctx)` -- testing the reply INLINE, because that
copybook defines no error-check paragraph among any of its 256 labels.
irs030 `copy`s "Proc-ZZ100-ACAS-IRS-Calls.cob" at L1732 and therefore calls
the HANDLER-named vocabulary -- `facade.acas008_read_next(ctx)`,
`facade.acasirsub1_read_indexed(ctx)` -- inheriting a per-handler error check
that, on an unrecoverable open failure, logs a handler-specific message,
performs that handler's `-Close`, and raises the shared abort that reproduces
COBOL `goback.` (Proc-ZZ100-ACAS-IRS-Calls.cob L320-L364). Choosing the
wrong alias set changes behaviour, not just names.

THE RULES THAT BIND THIS PACKAGE. `review_rules` reports no user rules
document for this project, so the binding constraints are the AAP's own six
(0.7.2), summarised here:

R-1 No COBOL at runtime. COBOL is the specification, never a runtime
    dependency: no module here spawns a process, loads a foreign library, or
    invokes the GnuCOBOL toolchain, and the shipped package runs on a host
    with no COBOL compiler installed. The frozen trees common/, copybooks/,
    general/, sales/, purchase/, irs/, stock/ and mysql/ are read as
    specification only and are never modified.
R-2 Zero binary floating point. Every monetary and quantity value is a
    `decimal.Decimal` quantized to the receiving field's digits, scale, sign
    and usage; COMP and BINARY-LONG fields are `int`. Those primitives live
    in `acas_posting.cobol`, which is exactly why the double truncation of
    the moving averages is reproducible at all.
R-3 No new validations, no new fields, no schema change, no concurrency.
    Validation is copied, never extended, and rejected transactions keep
    both their disposition and their effect on table state. Execution is
    strictly sequential -- no threads, no async runtime, no process pool, no
    connection pool -- matching the single-threaded COBOL.
R-4 Legacy anomalies are reproduced, never fixed. AAP 0.8.2, verbatim:
    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a
    defect fixed is a failure." Every reproduction site carries a
    `# ANOMALY A-<nn> [<path>:L<n>]` comment and
    docs/migration/anomaly-log.md is generated from those comments. So
    sl060's missing terminating period stays a nested conditional, gl080's
    quarter subscript stays unbounded, gl072's two silent skips stay silent,
    and irs030's half-posted double entry and its lost update on the two VAT
    control accounts are reproduced. Above all, the divergent moving-average
    idioms stay inside sl060, sl100, pl060 and pl100. AAP 0.6.1:
    "Normalising them into one helper would be the single easiest way to
    fail this migration."
R-5 Full traceability. The table above is this package's program-level
    contribution. Within each module, every paragraph of every in-scope
    section becomes a named private function -- AAP 0.7.4 C-4, verbatim:
    "every paragraph retains a named function even where its `GO TO` becomes
    a `continue`, a `break` or a `return`" -- and every transfer site
    carries a `# GO TO class N` annotation: class 1 loop-back becomes
    `continue`, class 2 forward terminator becomes `break` plus the
    post-loop block, class 3 section exit becomes `return`, class 4 sibling
    re-dispatch becomes a call plus an explicit `continue` or `return`. The
    seven in-scope `PERFORM ... THRU` sites (gl072 L300 and L304,
    sl100 L344, pl100 L336, irs030 L813, L831 and L832) become explicit
    function composition, hand-verified one site at a time.
R-6 Compiled behavior is the tie-breaker, and runs are deterministic. No
    module in this package reads a clock: all twelve in-scope programs
    contain zero clock reads, and the run date arrives purely through
    linkage as `to-day pic x(10)` and, at the stamping sites, as the system
    record's `Run-Date` (`05 Run-Date binary-long.`,
    copybooks/wssystem.cob L67). Pinning both observables happens at the CLI
    boundary only, which is why the controlled-clock module must never be
    imported here.
"""

from typing import Final

#: The twelve migrated program modules, in AAP 0.3.1 target-tree order --
#: not alphabetical, not grouped by ledger, not execution order. Each name is
#: a submodule of this package and must be imported explicitly; this marker
#: never imports them itself.
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
