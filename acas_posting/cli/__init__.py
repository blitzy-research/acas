"""Batch entry points for the migrated ACAS posting cycle.

Every migrated COBOL program is a `CALL`ed sub-program with a fixed parameter
list, so the command-line contract was already written - in the LINKAGE
SECTIONs. This package binds those parameters to `argv` and dispatches the
program modules in the order the menu shell does, with no screen output of any
kind.

Present in this package
    args        binds `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14], the run
                date and the system records to command-line arguments, AND
                reproduces the menu shells' own `aa005-Open-System.`,
                `aa010-Get-System-Recs.` and `overrewrite.` paragraphs plus the
                IRS `zz090`/`zz095` remap pair - the boundary at which the stored
                system records are read before a dispatch and written back after
                it. The seven entry points reach the store only through it.
    rdbms_params
                reproduces the frozen connection-parameter loader.

The seven entry points, named in `__all__`
    gl_post_cycle, gl_end_of_cycle, sl_invoice_post, sl_cash_post,
    pl_order_post, pl_payment_post, irs_post.
Listing a name in `__all__` records the target tree for traceability; it does
not import anything, and this marker imports nothing. A caller reaches an entry
point explicitly, `from acas_posting.cli import gl_post_cycle`.

Two ways to invoke one, and they are equivalent
    `python -m acas_posting <group> <operation> ...` routes through
    `acas_posting/__main__.py`, which reproduces common/ACAS.cbl's
    system-selection menu - its four in-scope `load0N` paragraphs and the seven
    dispatch paragraphs behind them - and forwards every remaining argument to
    the route unchanged. `python -m acas_posting.cli.<module> ...` reaches the
    same `main` directly. The router declares no linkage option of its own,
    because common/ACAS.cbl:L577 calls each subsystem menu with its `USING`
    phrase commented out, so the two forms parse the same argv with the same
    parser and return the same status.

Three linkage shapes, not one
    General Ledger      ws-calling-data, system-record, to-day, file-defs
                        [general/gl070.cbl:L245-L248]
    Sales / Purchase    the same four plus the system-record-4 totals record
                        [sales/sl060.cbl:L395-L399]
    IRS                 IRS-System-Params, WS-System-Record, File-Defs - no
                        calling-data block and no run date at all
                        [irs/irs030.cbl:L552-L554]

Two behaviours the entry points must preserve
    * The abort gate. A batch left open makes gl070 raise the terminate code
      [general/gl070.cbl:L289], and the menu then returns rather than
      continuing [general/general.cbl:L800-L814], so gl071 and gl072 never run.
      That is a hard gate between phases, not a warning.
    * Prompts that gate a database write become arguments with the COBOL
      default preserved - the end-of-job question that clears the IRS transfer
      file [irs/irs030.cbl:L1715-L1724] is an input, because its answer
      truncates a table. Prompts that only pause for acknowledgement are
      dropped; where such a prompt sits in an error path, the control transfer
      is kept and only the pause goes.

The menu programs themselves - general/general.cbl, sales/sales.cbl,
purchase/purchase.cbl, irs/irs.cbl and common/ACAS.cbl - are frozen reference
sources and out of scope as programs. Their screen I/O, their
`go to load01 ... depending on z` dispatch tables and their `call "SYSTEM"`
backup spool-out are all deliberately not migrated.

WHAT IS MIGRATED FROM THEM IS THE STATE THEY CARRY ACROSS A DISPATCH. Each menu
loads the system records before its `CALL` and rewrites them afterwards, and both
halves ARE reproduced, once, in `acas_posting.cli.args`:
`aa010_get_system_recs`, `overrewrite`, and on the IRS route
`zz090_set_up_irs_system_data`, `zz095_restore_irs_system_data` and
`eoj_persist_irs_system_data`. Every route performs them with its own menu's key
set and its own menu's term-code gate. Agent Action Plan section 0.8.5 makes an
empty ordering-normalised diff the acceptance test, and SYSTOT-REC is written by
nine period-total sites whose only writer to the store is `overrewrite`, so the
persistence is part of the cycle's observable behaviour rather than menu
decoration. Only the ISAM arm of each paragraph has no counterpart, the migration
having a single store.

This marker binds `__all__` and the `Final` used to type it. It imports no
submodule and performs no input or output.
"""

from __future__ import annotations

from typing import Final

# The ten modules of this package, in AAP 0.3.1 target-tree order - not
# alphabetical and not execution order. These are MODULE NAMES, recorded for
# documentation and traceability only: listing a name here does NOT import it,
# and this marker never imports one. A caller imports the module explicitly, as
#     from acas_posting.cli import gl_post_cycle
# and then calls that module's own entry point.
#
# AAP 0.3.1 names eight; `rdbms_params` is the ninth and is covered by the
# section's own `acas_posting/cli/*.py` wildcard (AAP 0.2.1.2, 0.4.4).
#
# `rdbms_params` exists because SYSTEM-REC is the only carrier by which a
# connection parameter reaches the data-access layer
# [common/acas008.cbl:L558-L563], and the frozen tree solves that with a named
# program of its own - common/acas-get-params.cbl, called by every
# common/*LD.cbl loader - which this module reproduces. `args` re-exports its one
# adapter, so no entry point imports it directly.
#
# THE MENU PARAGRAPHS LIVE IN `args` because the paragraphs the seven dispatch
# paragraphs `perform` are part of what AAP 0.4.1.1 defines those routes AS, and
# because AAP 0.3.1 names `args` as the module that binds the linkage those
# paragraphs fill. The shells read
# SYSTEM-REC, SYSDEFLT-REC and SYSTOT-REC before every `CALL`
# (general/general.cbl:L399-L460) and rewrite them afterwards
# (general/general.cbl:L656-L692), and that rewrite is the SOLE writer of the nine
# period totals AAP 0.6.4 enumerates. Since both rows are among the twenty-two
# tables the scenario comparison dumps (AAP 0.6.6), omitting either half makes the
# empty-diff acceptance condition of AAP 0.8.5 unreachable. It is the one module
# of this package that reaches the data-access layer, and it reaches it only
# through `acas_posting.dal.facade` - never a `dal.acas*` handler, which is the
# edge AAP 0.4.3 forbids.
__all__: Final[tuple[str, ...]] = (
    "args",
    "rdbms_params",
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
#   args (menu half) <- general/general.cbl  `aa005-Open-System.`  L385-L396,
#                       `aa010-Get-System-Recs.` L399-L460 and `overrewrite.`
#                       L656-L692; sales/sales.cbl L340-L404 and L628-L658;
#                       purchase/purchase.cbl L335-L398 and L621-L651;
#                       irs/irs.cbl `aa005-Open-System.` L494-L505,
#                       `aa010-Get-System-Recs.` L507-L552,
#                       `zz090-Set-Up-IRS-System-Data.` L907-L997,
#                       `zz095-Restore-IRS-System-Data.` L1000-L1032 and
#                       `EOJ.` L754-L771
#   rdbms_params     <- common/acas-get-params.cbl            L1-L224
#                       plus the six-statement `MOVE ... to RDBMS-*` block every
#                       loader performs after calling it, e.g.
#                       common/glbatchLD.cbl:L262-L267. Not a menu paragraph:
#                       this is the frozen tree's own connection-parameter
#                       loader, reproduced natively (R-1).
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
#   * ONLY THE COBOL-FILE ARM of the menus' `overrewrite`
#     (general/general.cbl:L674-L691, sales/sales.cbl:L644-L657,
#     purchase/purchase.cbl:L637-L649) and of the IRS `EOJ.`
#     (irs/irs.cbl:L765-L769). Their RDB arms ARE reproduced, by
#     `args.overrewrite` and `args.eoj_persist_irs_system_data`; the migration has
#     no ISAM store, so only one arm has a counterpart - see
#     args.RDBMS_STORE_SELECTOR_DIGIT;
#   * the pre-run backup spool-out
#     `call "SYSTEM" using Full-Backup-Script` (general/general.cbl:L650,
#     sales/sales.cbl:L625, purchase/purchase.cbl:L618, irs/irs.cbl:L790) -
#     excluded by AAP 0.2.2's spool-out exclusion and by R-1;
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
