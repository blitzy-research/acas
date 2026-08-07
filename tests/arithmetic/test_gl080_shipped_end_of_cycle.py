"""The SHIPPED `gl080` end-of-cycle program, driven paragraph by paragraph.

WHY THIS FILE EXISTS, STATED AS THE GAP IT CLOSES. `test_gl080_cycle_divide_rounded.py`
locks the arithmetic of `general/gl080.cbl`'s end-of-period block against a MODEL of that
block written inside the test file - `_end_of_period` - and it locks it thoroughly: the
`ROUNDED` divide, the round-trip gate, the sign drop, the silent overflow, the two cycle
resets and the ambient-context sabotage. What it cannot do is prove that
`acas_posting/programs/gl080_end_of_cycle.py` - the module the CLI actually dispatches -
still does any of it. Its brief forbids it from importing `acas_posting.programs`:

    Must NOT import: `acas_posting.dal.*`, `cli`, `programs`, `clock`, `dates`,
    `workfiles`, `harness`, `sqlalchemy`, `mysql.connector`, `numpy`, `pandas` ...

So the model and the shipped module could drift apart in either direction and every test
in that file would stay green. Deleting `rounded=True` from
[general/gl080.cbl:L328]'s reproduction, clamping the unbounded subscript into 1..4,
reconciling the two notions of quarter, reversing the two cycle-reset conjunctions,
stamping the batch before archiving it rather than after - none of those would be caught.
THIS FILE DRIVES THE SHIPPED MODULE, and every assertion below is an observation of the
module's own behaviour rather than of a transcription of it.

The two files are therefore complementary and neither is redundant: that one proves what
the frozen COBOL MEANS, this one proves that the SHIPPED PROGRAM DOES IT. Where they
assert the same figure they are meant to, and a divergence between them is exactly the
signal both exist to raise.

⭐ WHAT IS NOT CLOSED HERE, AND WHY. `gl080` is reached by no scenario in
`harness/scenarios/`, so no end-to-end diff covers it; that declination is recorded in
`docs/migration/ambiguity-resolutions.md` section 16.1 and it is bounded by the Agent
Action Plan rather than by preference. Section 0.3.1 fixes the scenario set at EIGHT
YAML definitions and eight test files, and section 0.8.5's mandated scenario set - clean
batch per ledger, mixed accepted-and-rejected, period-end totals, control-total mismatch
and empty batch - contains no end-of-cycle journey. Adding a ninth scenario would put
work outside the plan; driving the shipped program directly closes the coverage half of
the gap without doing that, and the state half stays recorded as a declination.

HOW THE MODULE IS DRIVEN. Two seams, both already in the shipped code and neither added
for the tests:

  (1) `run(...)` [acas_posting/programs/gl080_end_of_cycle.py] takes the frozen
      `PROCEDURE DIVISION USING` list - `ws-calling-data`, `system-record`, `to-day`,
      `file-defs` [general/gl080.cbl:L269-L272] - plus the three promoted interactive
      answers Agent Action Plan section 0.3.4 turns into parameters. Every test that
      cares about the ROUTE enters here, because entering anywhere else would prove
      the route by assuming it.
  (2) `_Gl080Storage` is the program's working storage as one object, and the module
      reaches every handler through the MODULE-GLOBAL name `facade`. A test that needs
      to see `st.a`, `st.y` or the flat archive file after the run builds the storage
      itself and calls the section function, exactly as the COBOL `perform` does.

⛔ NO DATABASE, NO COBOL, NO SUBPROCESS (R-1). The handlers are replaced by
`_GlFacadeDouble`, which serves rows out of a list and records what it was asked to do.
The two flat files the program declares - `fd archive` [general/gl080.cbl:L156] and
`fd work-file` [general/gl080.cbl:L170] - are already in-process objects in the shipped
module (`_ArchiveFile`, `_WorkFile`), so nothing touches a filesystem either. The import
of `acas_posting.programs.gl080_end_of_cycle` pulls `acas_posting.dal.facade` and the
pinned MySQL driver in transitively; `_shipped_gl080` removes every tier-isolated name it
added, so the three isolation assertions this directory carries
(`test_comp3_packed_decimal.py`, `test_comp_binary.py`, `test_pic_field_descriptors.py`)
keep holding whatever order the files run in.

THE RULES, AS THEY BIND THIS FILE (Agent Action Plan section 0.7.2):

  R-1  No COBOL at runtime. See above. No `harness` import, no subprocess, no FFI.
  R-2  Zero binary floating point. Every money figure below is a `Decimal` built from a
       string and every counter is an `int`. ⛔ no `float(`, no `pytest.approx`, no
       `math.isclose`, no tolerance.
  R-3  No new validations. ⭐⭐ THE QUARTER SUBSCRIPT STAYS UNBOUNDED and the two
       notions of quarter stay unreconciled. A test that asserted an `IndexError`,
       a clamp or a warning would be asserting a validation the frozen program does not
       perform.
  R-4  Anomalies reproduced, never fixed. This file locks ANOMALY A-2 (the unbounded
       subscript at [general/gl080.cbl:L328] and [general/gl080.cbl:L345]) and
       ANOMALY A-3 (two disagreeing notions of "current quarter",
       [general/gl080.cbl:L346] against [general/gl080.cbl:L355-L357]) IN THE SHIPPED
       MODULE, so that a future well-intentioned correction fails the suite.
  R-5  Traceability. Every test names the `[general/gl080.cbl:Lnnn]` it drives and the
       shipped function that reproduces it.
  R-6  Compiled behaviour is the tie-breaker. Where the compiled disposition is not
       settled the question is named - Q-19 for what an overrunning subscript writes
       past the record, Q-23 for the record-length stop - and the test asserts the
       SHIPPED behaviour without claiming the oracle has spoken.

Also binding - Agent Action Plan section 0.8.4: no timing assertion and no performance
measurement appears anywhere in this file. And section 0.8.1: the frozen COBOL, the
bridges, the copybooks and `mysql/ACASDB.sql` are read-only, and nothing here writes to
any of them.

THE FROZEN BLOCK THIS FILE DRIVES, verbatim from the checkout, so that a reader can
check every assertion below against the source without leaving the file::

     283  display  prog-name  at 0101 ...
     288  move     1  to  File-Key-No.
     289  move     zero  to  a.
     299  accept   keyed-reply  at 1065  with update auto.
     302  goback.                                  *> run NOT confirmed
     304  display  "Phase - 1.  Batch Check" ...
     305  perform  gl080a.
     308  if       a = 1
     313           go to  main-end.                *> batches outstanding
     315  if       archiving
     317           perform  gl080b               *> Phase 2, Transaction Archiving
     318  else
     320           perform  gl080c.              *> Phase 3, Transaction Deletion
     322  perform  compress-post.                *> Phase 4, Posting Contraction
     324  if       a = 9
     325      or   scycle <  period
     326           go to  main-end.
     328  divide   scycle by period giving a rounded.
     329  multiply a  by  period  giving  y.
     331  if       scycle not = y
     332           go to  main-end.
     334  add      1  to scycle.
     337  perform  GL-Nominal-Open.
     339  loop.
     342  perform  GL-Nominal-Read-Next.
     343  if       fs-reply = 10
     344           go to  loop-end.
     345  move     ledger-balance  to  ledger-q (a).
     346  if       current-quarter = 4
     347           move  ledger-balance  to  ledger-last.
     348  perform  GL-Nominal-Rewrite.
     349  go       to loop.
     351  loop-end.
     354  perform  GL-Nominal-Close.
     355  add      1  to  current-quarter.
     356  if       current-quarter = 5
     357           move  1  to  current-quarter.
     358  if       period = 3
     359      and  scycle > 12
     360           move 1 to scycle.
     361  if       period = 13
     362      and  scycle > 52
     363           move 1 to scycle.
     365  main-end.
     366  goback.

⚠ PROVENANCE OF RULES. There is no user rules document - `review_rules` returns exactly
`No user rules provided.` The six rules above are the Technical Specification's, section
0.7.2, and nothing has been invented to fill the gap.
"""

from __future__ import annotations

import ast
import contextlib
import dataclasses
import importlib
import inspect
import logging
import sys
import types
from collections.abc import Iterator, Mapping, Sequence
from decimal import Decimal
from typing import Any, Final

import pytest

from acas_posting.cobol import arithmetic
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import GlBatchRecord
from acas_posting.records.gl_ledger import WsLedgerRecord
from acas_posting.records.gl_posting import WsPostingRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  1.  THE IMPORT IS REAL, IT IS FRESH, AND IT LEAVES NOTHING RESIDENT
# ---------------------------------------------------------------------------

#: The shipped module under test. Named once so that a rename is a single edit and a
#: grep for the module finds this file.
_GL080: Final[str] = "acas_posting.programs.gl080_end_of_cycle"

#: The module-name prefixes this directory's own isolation assertions forbid. The same
#: list the sibling loaders carry, kept identical on purpose: a prefix that appears in
#: one list and not another is a hole.
_TIER_ISOLATION_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
    "harness",
    "mysql",
    "numpy",
    "pandas",
    "sqlalchemy",
    "yaml",
)

#: `fs-reply` for a successful handler call, `88 fn-Ok` in the shared vocabulary
#: [copybooks/wsfnctn.cob:L25]. Both flat files in `gl080` declare the SAME field as
#: their FILE STATUS [general/gl080.cbl:L140], [general/gl080.cbl:L146].
_FS_OK: Final[int] = 0

#: `if fs-reply = 10` - the at-end every read loop in the program tests
#: [general/gl080.cbl:L343], [general/gl080.cbl:L379], [general/gl080.cbl:L422],
#: [general/gl080.cbl:L456], [general/gl080.cbl:L577], [general/gl080.cbl:L613].
_FS_AT_END: Final[int] = 10

#: `88 Archived value 2.` [copybooks/wsbatch.cob:L32] - what BOTH the archiving and the
#: deletion walk stamp into `Cleared-Status` [general/gl080.cbl:L430],
#: [general/gl080.cbl:L585].
_CLEARED_ARCHIVED: Final[int] = 2

#: The run date the tests hand in through `SYSTEM-REC`, and therefore the value both
#: walks stamp into `Stored` [general/gl080.cbl:L431], [general/gl080.cbl:L586]. A fixed
#: figure, never `date.today()`: rule R-6's determinism requirement is that every date
#: arrives through linkage, and this file is one of its witnesses.
_RUN_DATE: Final[int] = 20250921

#: `01 to-day pic x(10).` [general/gl080.cbl:L267] in the DD/MM/CCYY form the menu
#: shell supplies [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]. Pinned for the same
#: reason.
_TO_DAY: Final[str] = "21/09/2025"

#: `88 Archiving value "Y".` [copybooks/wssystem.cob:L165] over `Arch pic x`
#: [copybooks/wssystem.cob:L164] - the switch [general/gl080.cbl:L315] tests to choose
#: phase 2 over phase 3.
_ARCHIVING: Final[str] = "Y"

#: Anything that is not `"Y"`. The frozen condition name has one value, so one
#: counter-example is the whole of the else arm.
_NOT_ARCHIVING: Final[str] = " "

#: `88 FS-Cobol-Files-Used value zero.` over `File-System-Used`
#: [copybooks/wssystem.cob]. ZERO means Cobol files, so a NON-zero value is the RDBMS
#: configuration every scenario in this migration runs in, and it is the value that
#: makes `compress-post` [general/gl080.cbl:L633-L635] leave immediately.
_FILE_SYSTEM_RDBMS: Final[int] = 1

#: The Cobol-files configuration. Reachable, and phase 4 runs in it - see the
#: record-length stop, question Q-23.
_FILE_SYSTEM_COBOL: Final[int] = 0


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix this tier must not leave loaded?

    Matched as a package prefix - the exact name, or the name plus a dot - so a
    submodule cannot slip past and a merely similar name is not caught by accident.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped_gl080() -> Iterator[types.ModuleType]:
    """Import the shipped `gl080` module for one test, leaving `sys.modules` as found.

    ⭐ THE IMPORT IS NOT OPTIONAL AND IT IS NOT MEMOISED, for the reasons the sibling
    loaders in this directory record: `pytest.importorskip` turns the one failure this
    file exists to catch - a shipped module that cannot be imported at all - into a
    PASS, and a memoised module is already resident, so the purge on the way out would
    remove nothing and every freshness claim would be about a module that had never
    left. The pinned MySQL driver the skip reason used to blame is a hard requirement of
    `requirements.txt`, so its absence is a broken environment rather than a supported
    configuration.

    Yields:
        The imported module.

    Raises:
        AssertionError: The module was already resident on the way in, did not become
            resident, or a tier-isolated name survived the purge.
        ImportError: The module could not be imported. Deliberately NOT a skip.
    """
    #  EVICT FIRST, so the import below really runs the module's top-level code and the
    #  purge on the way out really removes what it added. Eviction rather than a "must be
    #  absent on the way in" assertion, because this tier's own helpers legitimately
    #  import program modules in function scope to drive the SHIPPED paragraphs, and an
    #  absence assertion makes the claim depend on which file ran first - the very
    #  fragility it exists to remove.
    for _resident in sorted(
        (_name for _name in sys.modules if _is_tier_isolated_name(_name)), reverse=True
    ):
        del sys.modules[_resident]
    assert _GL080 not in sys.modules, (
        f"{_GL080} survived the eviction above, so its top-level code will "
        f"NOT re-execute and the purge on the way out would remove nothing."
    )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(_GL080)
        assert sys.modules.get(_GL080) is module, (
            f"{_GL080} did not become resident under its own name, so nothing about a "
            f"fresh import has been established."
        )
        #  The transitive pull is the point of the purge: a program module reaches its
        #  handlers through `acas_posting.dal.facade`, which imports the driver.
        assert any(
            _is_tier_isolated_name(name) for name in set(sys.modules) - before
        ), (
            "importing the shipped program added no tier-isolated name at all, which "
            "would mean the module no longer reaches the data-access layer - the seam "
            "every test in this file drives."
        )
        yield module
        completed = True
    finally:
        added = set(sys.modules) - before
        for name in sorted(added, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
        )
        #  Only when the body itself succeeded, so a real failure is never masked by a
        #  second assertion about housekeeping.
        if completed:
            assert not residue, (
                f"importing {_GL080} left {residue} resident after the purge, so the "
                f"tier-isolation assertions in test_comp3_packed_decimal.py, "
                f"test_comp_binary.py and test_pic_field_descriptors.py would depend on "
                f"file order rather than on this loader."
            )


# ---------------------------------------------------------------------------
#  2.  THE HANDLER DOUBLE
#
#      The program reaches sixteen facade verbs across three entities, and every one
#      of them goes through the module-global name `facade`. Replacing that name is
#      the whole of the substitution: nothing is patched inside the program, no
#      function is wrapped, and the program cannot tell the difference because the
#      COBOL cannot either - a `CALL "acas005"` resolves at run time.
#
#      WHY THE VERBS ARE SPELLED OUT ONE BY ONE rather than answered by a catch-all.
#      A catch-all would keep working after a verb was renamed or dropped in the
#      shipped module, which is precisely a change this file should fail on. Defining
#      the sixteen explicitly makes the verb vocabulary a CHECKED FACT: an unexpected
#      attribute raises `AttributeError` out of the double and the test fails.
#
#      WHAT A REAL HANDLER DOES, and therefore what the double does. It MUTATES THE
#      CALLER'S RECORD IN PLACE - the bridge's unload paragraph moves host variables
#      into the `01` the caller passed [common/glpostingMT.cbl:L992-L998] - and it
#      writes its status into `Fs-Reply` on the shared `File-Access` block
#      [copybooks/wsfnctn.cob:L25]. It does NOT hand the record back as a return
#      value, and the shipped program reads no return value either, so the double
#      returns None: a program that started depending on a returned status would fail
#      here rather than pass quietly.
# ---------------------------------------------------------------------------


def _apply(record: object, values: Mapping[str, object]) -> None:
    """Move `values` into `record`, keyed by dotted attribute path.

    A dotted path because the record layouts are nested groups - `WS-Post-Key` inside
    `WS-Posting-Record` [copybooks/wspost.cob:L11-L14] - and the group names are part of
    the field's identity in the COBOL.

    Args:
        record: The `01` the handler was handed.
        values: Dotted attribute path to value, as a seeded row.
    """
    for dotted, value in values.items():
        target = record
        parts = dotted.split(".")
        for part in parts[:-1]:
            target = getattr(target, part)
        assert hasattr(target, parts[-1]), (
            f"the seeded row names {dotted!r}, which is not a field of "
            f"{type(record).__name__} - the record layer and this file disagree about "
            f"the layout, which is a real failure rather than a typo to route around."
        )
        setattr(target, parts[-1], value)


class _GlFacadeDouble:
    """The three General Ledger entity facades, in memory, with a call log.

    Attributes:
        calls: Every verb name in invocation order. THE ORDER IS AN ASSERTED FACT in
            several tests below, because the frozen program's phase order is one of
            the four things Agent Action Plan section 0.8.1 requires be preserved.
        ledger_rewrites: One snapshot per `GL-Nominal-Rewrite`, taken at the moment of
            the call. Snapshots rather than references, because the program reuses the
            same `01` for every row and a reference would show only the last one.
        batch_rewrites: One snapshot per `GL-Batch-Rewrite`.
        posting_deletes: The `(batch, post-number)` of every `GL-Posting-Delete`.
        posting_writes: The `(batch, post-number)` of every `GL-Posting-Write`.
    """

    def __init__(
        self,
        facade_module: types.ModuleType,
        *,
        batches: Sequence[Mapping[str, object]] = (),
        postings: Sequence[Mapping[str, object]] = (),
        ledgers: Sequence[Mapping[str, object]] = (),
    ) -> None:
        #  The real context class, not a stand-in: `_Gl080Storage.nominal_ctx()` and its
        #  two siblings build one per verb, and the parameter list they fill is the
        #  handler's five-argument `CALL` block [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57].
        #  Keeping the real class means those three methods are exercised for real.
        self.FacadeContext = facade_module.FacadeContext
        self.calls: list[str] = []
        self._rows: dict[str, list[Mapping[str, object]]] = {
            "batch": list(batches),
            "posting": list(postings),
            "ledger": list(ledgers),
        }
        self._cursor: dict[str, int] = {"batch": 0, "posting": 0, "ledger": 0}
        self.ledger_rewrites: list[dict[str, Any]] = []
        self.batch_rewrites: list[dict[str, Any]] = []
        self.posting_deletes: list[tuple[int, int]] = []
        self.posting_writes: list[tuple[int, int]] = []

    # -- the shared mechanics -------------------------------------------------

    def _log(self, verb: str, ctx: Any) -> None:
        self.calls.append(verb)
        ctx.file_access.fs_reply = _FS_OK

    def _open(self, verb: str, ctx: Any, entity: str) -> None:
        """An OPEN positions at the first record, which is why the cursor resets.

        `START`-less sequential access is what both walks use, and a real
        `GL-Batch-Open` followed by `GL-Batch-Read-Next` reads the FIRST row however
        many times the file has been opened. Phase 1 and phase 2 or 3 each open the
        batch file in turn [general/gl080.cbl:L376], [general/gl080.cbl:L419],
        [general/gl080.cbl:L574], so without the reset the second walk would see an
        exhausted file and every archiving and deletion test would pass by seeing
        nothing at all.
        """
        self._cursor[entity] = 0
        self._log(verb, ctx)

    def _read_next(self, verb: str, ctx: Any, entity: str) -> None:
        rows = self._rows[entity]
        position = self._cursor[entity]
        if position >= len(rows):
            self.calls.append(verb)
            ctx.file_access.fs_reply = _FS_AT_END
            return
        self._cursor[entity] = position + 1
        _apply(ctx.record, rows[position])
        self._log(verb, ctx)

    # -- GL-Nominal, handler acas005 -----------------------------------------

    def gl_nominal_open(self, ctx: Any) -> None:
        self._open("gl_nominal_open", ctx, "ledger")

    def gl_nominal_read_next(self, ctx: Any) -> None:
        self._read_next("gl_nominal_read_next", ctx, "ledger")

    def gl_nominal_rewrite(self, ctx: Any) -> None:
        ledger = ctx.record
        self.ledger_rewrites.append(
            {
                "key": ledger.ws_ledger_key.ws_ledger_nos,
                "balance": ledger.ledger_balance,
                "last": ledger.ledger_last,
                "quarters": (
                    ledger.quarters.ledger_q1,
                    ledger.quarters.ledger_q2,
                    ledger.quarters.ledger_q3,
                    ledger.quarters.ledger_q4,
                ),
                "occurs_view": tuple(ledger.quarters_table.ledger_q),
                "filler": ledger.filler_l37,
            }
        )
        self._log("gl_nominal_rewrite", ctx)

    def gl_nominal_close(self, ctx: Any) -> None:
        self._log("gl_nominal_close", ctx)

    # -- GL-Batch, handler acas007 -------------------------------------------

    def gl_batch_open(self, ctx: Any) -> None:
        self._open("gl_batch_open", ctx, "batch")

    def gl_batch_open_input(self, ctx: Any) -> None:
        self._open("gl_batch_open_input", ctx, "batch")

    def gl_batch_read_next(self, ctx: Any) -> None:
        self._read_next("gl_batch_read_next", ctx, "batch")

    def gl_batch_rewrite(self, ctx: Any) -> None:
        batch = ctx.record
        self.batch_rewrites.append(
            {
                "key": batch.ws_batch_key.ws_batch_nos,
                "cleared_status": batch.cleared_status,
                "batch_status": batch.batch_status,
                "stored": batch.dates.stored,
                "batch_start": batch.batch_start,
                "items": batch.items,
            }
        )
        self._log("gl_batch_rewrite", ctx)

    def gl_batch_close(self, ctx: Any) -> None:
        self._log("gl_batch_close", ctx)

    # -- GL-Posting, handler acas006 -----------------------------------------

    def gl_posting_open(self, ctx: Any) -> None:
        self._open("gl_posting_open", ctx, "posting")

    def gl_posting_open_input(self, ctx: Any) -> None:
        self._open("gl_posting_open_input", ctx, "posting")

    def gl_posting_open_output(self, ctx: Any) -> None:
        """`Open` plus `Output` EMPTIES the store, and the double empties it too.

        [copybooks/Proc-ACAS-FH-Calls.cob] publishes the verb and `acas006` honours it;
        the handler that turns it into a delete-every-row is `acas008`
        [common/acas008.cbl:L313-L319], and the same meaning applies here. Reached only
        by `compress-post` after `loop1` [general/gl080.cbl:L671], which the record-length
        stop at [general/gl080.cbl:L643-L649] currently pre-empts - so this arm is
        implemented for fidelity rather than exercised, and a test that reached it would
        see an emptied store rather than a surprise.
        """
        self._rows["posting"].clear()
        self._open("gl_posting_open_output", ctx, "posting")

    def gl_posting_read_next(self, ctx: Any) -> None:
        self._read_next("gl_posting_read_next", ctx, "posting")

    def gl_posting_write(self, ctx: Any) -> None:
        posting = ctx.record
        self.posting_writes.append(
            (posting.ws_post_key.batch, posting.ws_post_key.post_number)
        )
        self._log("gl_posting_write", ctx)

    def gl_posting_delete(self, ctx: Any) -> None:
        posting = ctx.record
        self.posting_deletes.append(
            (posting.ws_post_key.batch, posting.ws_post_key.post_number)
        )
        self._log("gl_posting_delete", ctx)

    def gl_posting_close(self, ctx: Any) -> None:
        self._log("gl_posting_close", ctx)

    # -- what the double DOES NOT publish ------------------------------------

    def verbs(self) -> tuple[str, ...]:
        """Every verb this double answers, sorted. Asserted as a set in section 3."""
        return tuple(
            sorted(
                name
                for name in dir(self)
                if name.startswith(("gl_nominal_", "gl_batch_", "gl_posting_"))
            )
        )


@contextlib.contextmanager
def _driving(
    gl080: types.ModuleType, double: _GlFacadeDouble
) -> Iterator[_GlFacadeDouble]:
    """Put `double` in the module's `facade` slot for the duration, then put it back.

    Done with an explicit try/finally rather than with `monkeypatch` so that the
    restoration happens INSIDE the `_shipped_gl080` block, before the module is purged,
    rather than after it in pytest's fixture teardown. The two orderings are both
    harmless today; this one cannot become harmful.

    Args:
        gl080: The shipped module.
        double: The stand-in.

    Yields:
        The same double, so a caller can write `with _driving(...) as calls:`.
    """
    real = gl080.facade
    assert hasattr(real, "FacadeContext"), (
        "the shipped module's `facade` global is not the data-access facade, so the "
        "seam this file drives has moved and every substitution below is meaningless."
    )
    gl080.facade = double
    try:
        yield double
    finally:
        gl080.facade = real


def _system(
    *,
    scycle: int,
    period: int,
    current_quarter: int = 1,
    arch: str = _NOT_ARCHIVING,
    file_system_used: int = _FILE_SYSTEM_RDBMS,
    date_form: int | None = None,
) -> SystemRecord:
    """`01 System-Record` [copybooks/wssystem.cob] with the seven fields `gl080` reads.

    Everything else keeps the record layer's own default, because a value this program
    never reads has no business being set by a test that claims to be about this program.

    Args:
        scycle: `05 Scycle Redefines Cyclea binary-char.` [copybooks/wssystem.cob:L63].
        period: `05 Period binary-char.` [copybooks/wssystem.cob:L64].
        current_quarter: `05 Current-Quarter pic 9.` [copybooks/wssystem.cob:L110] -
            ANOMALY A-3's rotating counter.
        arch: `05 Arch pic x.` [copybooks/wssystem.cob:L164].
        file_system_used: `File-System-Used`, which decides whether phase 4 runs.
        date_form: `05 Date-Form pic 9.` [copybooks/wssystem.cob:L127]. Left at the
            record layer's default when omitted, which is what makes the mutation at
            [general/gl080.cbl:L729-L730] observable.

    Returns:
        The record, ready to hand to `run`.
    """
    system = SystemRecord()
    system.system_data_block.scycle = scycle
    system.system_data_block.period = period
    system.system_data_block.current_quarter = current_quarter
    system.system_data_block.run_date = _RUN_DATE
    system.system_data_block.rdbms_flat_statuses.file_system_used = file_system_used
    system.general_ledger_block.arch = arch
    if date_form is not None:
        system.system_data_block.date_form = date_form
    return system


def _storage(
    gl080: types.ModuleType,
    system: SystemRecord,
    *,
    file_access: FileAccess | None = None,
    file_defs: FileDefs | None = None,
    a: int = 0,
    y: int = 0,
    run_confirmed: bool = True,
    disk_change_option: int = 0,
    archive_path_override: str | None = None,
) -> Any:
    """Build `_Gl080Storage` the way `run` builds it, so a test can watch the fields.

    ⭐ `a` AND `y` ARE PARAMETERS, not initialised constants. `[general/gl080.cbl:L324]`
    reads `a` BEFORE `[general/gl080.cbl:L328]` writes it, and `77 a pic 99 value zero.`
    [general/gl080.cbl:L183] means its incoming value is whatever the program left there -
    so a test unit that initialised it internally could not express the read-before-write
    at all. `run` itself passes zero, which is the `value zero` clause; a test that wants
    the guard pre-armed passes nine.

    Every record and both flat files come from the module's OWN classes, looked up as
    attributes rather than imported at file scope, which keeps this file's module-level
    imports inside the tier's `records`-only allowance.

    Args:
        gl080: The shipped module.
        system: The system record, from `_system`.
        file_access: The shared status block. A fresh one when omitted; pass your own to
            read `Fs-Reply` afterwards.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13]. A fresh one when omitted;
            pass your own to watch `disk-change` compose the archive path.
        a: `77 a pic 99.` on entry [general/gl080.cbl:L183].
        y: `77 y pic 99.` on entry [general/gl080.cbl:L182].
        run_confirmed: The promoted answer at [general/gl080.cbl:L299-L302].
        disk_change_option: The promoted option at [general/gl080.cbl:L545-L547].
        archive_path_override: The promoted path edit at [general/gl080.cbl:L555].

    Returns:
        The storage object.
    """
    access = file_access if file_access is not None else FileAccess()
    return gl080._Gl080Storage(
        ws_calling_data=WsCallingData(),
        system=system,
        to_day=_TO_DAY,
        file_defs=file_defs if file_defs is not None else FileDefs(),
        file_access=access,
        dal_common=AcasDalCommonData(),
        ledger=WsLedgerRecord(),
        batch=GlBatchRecord(),
        posting=WsPostingRecord(),
        a=a,
        y=y,
        ws_eval_msg=" " * 25,
        ws_date_formats=gl080.WsDateFormats(),
        archive=gl080._ArchiveFile(access),
        work_file=gl080._WorkFile(access),
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
        dal_options={},
    )


def _ledger_row(
    key: int, balance: str, *, last: str = "0.00"
) -> dict[str, object]:
    """One `GLLEDGER-REC` row for the double to serve.

    Args:
        key: `WS-Ledger-Nos` [copybooks/wsledger.cob:L15].
        balance: `Ledger-Balance pic s9(8)v99 comp-3` [copybooks/wsledger.cob:L28], as a
            STRING so that no binary float can be constructed on the way in (R-2).
        last: `Ledger-Last`, the field subscript zero lands on.

    Returns:
        The row, keyed by dotted attribute path.
    """
    return {
        "ws_ledger_key.ws_ledger_nos": key,
        "ledger_balance": Decimal(balance),
        "ledger_last": Decimal(last),
    }


def _batch_row(
    number: int,
    cycle: int,
    *,
    batch_status: int = 1,
    cleared_status: int = 1,
    items: int = 1,
) -> dict[str, object]:
    """One `GLBATCH-REC` row for the double to serve.

    The two status defaults are the ones that get PAST phase 1: `88 Status-Closed value
    1.` [copybooks/wsbatch.cob:L27] and `88 Processed value 1.`
    [copybooks/wsbatch.cob:L31] are both satisfied, so
    [general/gl080.cbl:L384-L386] does not set `a` to one. A test about the phase-1 gate
    passes something else deliberately.

    Args:
        number: `WS-Batch-Nos` [copybooks/wsbatch.cob:L14].
        cycle: `Bcycle`, compared against `Scycle` at [general/gl080.cbl:L380-L382].
        batch_status: `Batch-Status` [copybooks/wsbatch.cob:L25].
        cleared_status: `Cleared-Status` [copybooks/wsbatch.cob:L29].
        items: `Items` [copybooks/wsbatch.cob:L23].

    Returns:
        The row, keyed by dotted attribute path.
    """
    return {
        "ws_batch_key.ws_batch_nos": number,
        "bcycle": cycle,
        "batch_status": batch_status,
        "cleared_status": cleared_status,
        "items": items,
    }


def _posting_row(
    batch: int,
    number: int,
    *,
    amount: str = "100.00",
    dr: int = 1010,
    dr_pc: int = 11,
    cr: int = 2020,
    cr_pc: int = 22,
    vat_ac: int = 0,
    vat_pc: int = 0,
    vat_amount: str = "0.00",
    vat_side: str = "  ",
    code: str = "GL",
    date: str = "21/09/25",
    legend: str = "END OF CYCLE TEST",
) -> dict[str, object]:
    """One `GLPOSTING-REC` row for the double to serve.

    Args:
        batch: `Batch` inside `WS-Post-Key` [copybooks/wspost.cob:L13].
        number: `Post-Number` inside `WS-Post-Key` [copybooks/wspost.cob:L14].
        amount: `Post-Amount pic s9(8)v99` [copybooks/wspost.cob:L23], as a STRING (R-2).
        dr: `Post-DR` [copybooks/wspost.cob:L19].
        dr_pc: `DR-PC` [copybooks/wspost.cob:L20].
        cr: `Post-CR` [copybooks/wspost.cob:L21].
        cr_pc: `CR-PC` [copybooks/wspost.cob:L22].
        vat_ac: `VAT-AC` [copybooks/wspost.cob], zero suppresses the VAT leg at
            [general/gl080.cbl:L497-L499].
        vat_pc: `VAT-PC`.
        vat_amount: `VAT-Amount`, as a STRING (R-2). Zero also suppresses the VAT leg.
        vat_side: `Post-VAT-Side`, `"DR"` or `"CR"`, which decides which leg the VAT is
            added into [general/gl080.cbl:L475-L477], [general/gl080.cbl:L489-L491] and
            whether the VAT leg is negated [general/gl080.cbl:L505-L506].
        code: `Post-Code`.
        date: `Post-Date`.
        legend: `Post-Legend`.

    Returns:
        The row, keyed by dotted attribute path.
    """
    return {
        "ws_post_key.batch": batch,
        "ws_post_key.post_number": number,
        "post_code": code,
        "post_date": date,
        "post_legend": legend,
        "post_dr": dr,
        "dr_pc": dr_pc,
        "post_cr": cr,
        "cr_pc": cr_pc,
        "post_amount": Decimal(amount),
        "vat_ac": vat_ac,
        "vat_pc": vat_pc,
        "post_vat_side": vat_side,
        "vat_amount": Decimal(vat_amount),
    }


def _facade_verbs_the_module_calls(module: types.ModuleType) -> frozenset[str]:
    """Every `facade.<verb>` the shipped module names, read out of its own source.

    Read with `ast` rather than by importing and introspecting, because an attribute
    that is only reached down one branch would never show up in a trace of a single run,
    and the verb VOCABULARY is what this is about rather than the verbs one path happens
    to use.

    Args:
        module: The shipped module.

    Returns:
        The verb names, without `FacadeContext` and without anything private.
    """
    tree = ast.parse(inspect.getsource(module))
    return frozenset(
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "facade"
        and node.attr.startswith(("gl_nominal_", "gl_batch_", "gl_posting_"))
    )


@contextlib.contextmanager
def caplog_free() -> Iterator[list[logging.LogRecord]]:
    """Collect `acas_posting.cobol.move` records for the block, with no level games.

    A handler attached to the one logger rather than `caplog`, because `caplog` sets the
    ROOT level and this control test has to be sure it is not the level that made the
    list empty. The handler is removed in a `finally` so no test leaks a handler into
    another.

    Yields:
        The list the handler appends to, live.
    """
    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger("acas_posting.cobol.move")
    handler = _Collector(level=logging.NOTSET)
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


# ---------------------------------------------------------------------------
#  3.  THE SEAM ITSELF
#
#      Before any behaviour is asserted, the substitution has to be shown to be the
#      real one. If the program reached its handlers some other way, every test below
#      would be observing a double nobody consulted.
# ---------------------------------------------------------------------------


def test_the_program_reaches_every_handler_through_one_module_global() -> None:
    """`facade` is a module attribute, and replacing it replaces the whole call chain.

    The COBOL equivalent is that `CALL "acas005"` resolves at RUN TIME, by name, to
    whatever module the loader finds - which is why the migration can substitute the
    data-access layer without touching the program, and why this file can drive the
    shipped program with no database (R-1).

    Two facts, both checked rather than assumed: the name exists and carries the
    facade's own `FacadeContext`, and the module holds NO OTHER bound reference to a
    handler that a substitution would miss - every verb it names is spelled
    `facade.<verb>`, so there is exactly one seam.
    """
    with _shipped_gl080() as gl080:
        assert hasattr(gl080, "facade")
        assert hasattr(gl080.facade, "FacadeContext")

        #  A direct `from acas_posting.dal.facade import gl_batch_read_next` would bind
        #  the verb into the module's own namespace and slip past the substitution. None
        #  exists: the module names the verbs only through the `facade` attribute.
        module_level_verbs = sorted(
            name
            for name in vars(gl080)
            if name.startswith(("gl_nominal_", "gl_batch_", "gl_posting_"))
        )
        assert module_level_verbs == [], (
            f"{module_level_verbs} are bound directly into the program's namespace, so "
            f"replacing `facade` would not replace them and the handler substitution "
            f"this file rests on would be partial."
        )


def test_the_double_answers_exactly_the_verbs_the_program_names() -> None:
    """The double's verb set and the program's verb set are the same set.

    A double that answered MORE verbs than the program calls would be harmless but
    misleading; one that answered FEWER would make the first test to reach the missing
    verb fail with `AttributeError` far from the cause. Asserting set equality turns the
    vocabulary into a checked fact, so adding a seventeenth verb to the shipped program
    fails HERE, with a message that says which one.

    THE SIXTEEN, by entity: four on `GL-Nominal` (`acas005`), five on `GL-Batch`
    (`acas007`) and seven on `GL-Posting` (`acas006`)
    [copybooks/Proc-ACAS-FH-Calls.cob].
    """
    with _shipped_gl080() as gl080:
        double = _GlFacadeDouble(gl080.facade)
        named = _facade_verbs_the_module_calls(gl080)

        assert named, (
            "no `facade.<verb>` call was found in the shipped module's source, which "
            "would mean the program no longer reaches the data-access layer at all."
        )
        assert set(double.verbs()) == set(named), (
            f"the double answers {sorted(set(double.verbs()) - set(named))} the program "
            f"does not call, and does not answer "
            f"{sorted(set(named) - set(double.verbs()))} that it does."
        )
        assert len(named) == 16
        assert sum(1 for verb in named if verb.startswith("gl_nominal_")) == 4
        assert sum(1 for verb in named if verb.startswith("gl_batch_")) == 5
        assert sum(1 for verb in named if verb.startswith("gl_posting_")) == 7


# ---------------------------------------------------------------------------
#  4.  THE ROUTE - THE PHASE ORDER, DRIVEN THROUGH `run`
#
#      Agent Action Plan section 0.8.1 requires posting order and batch sequencing be
#      preserved exactly, and section 0.6.4 records that `gl080` labels its own phases
#      on screen in an order that is NOT the order of the numbers: deletion is
#      "Phase - 3" but runs after "Phase - 4"'s neighbour and before "Phase - 5". The
#      only way to lock a route is to assert the ordered call log of a real run.
# ---------------------------------------------------------------------------


def test_the_phases_run_in_the_frozen_order_on_the_deletion_route() -> None:
    """`run` drives phase 1, phase 3, phase 4's gate and phase 5, in that order.

    ENTERED THROUGH `run`, with the frozen four-parameter list
    [general/gl080.cbl:L269-L272], so the route is observed rather than assumed. The
    system record says NOT archiving [copybooks/wssystem.cob:L164-L165], so
    [general/gl080.cbl:L315-L320] takes the `else` arm and phase 3 runs.

    THE ASSERTED SEQUENCE, and what each entry is:

        gl_batch_open_input   376  phase 1 opens the batch file for input only
        gl_batch_read_next    378  the one seeded batch
        gl_batch_read_next    378  at end
        gl_batch_close        391  phase 1's post-loop block
        gl_batch_open         574  phase 3 opens it again, for update this time
        gl_batch_read_next    576
        gl_posting_open       604  del-process, per batch
        gl_posting_read_next  611
        gl_posting_delete     620  the batch's own posting
        gl_posting_read_next  611  at end
        gl_posting_close      582  back in gl080c, AFTER del-process returns
        gl_batch_rewrite      588  the stamp: archived, stored, batch-start zero
        gl_batch_read_next    576  at end
        gl_batch_close        593  phase 3's post-loop block
        gl_nominal_open       337  phase 5, only because the gate at 331 passed
        gl_nominal_read_next  342
        gl_nominal_rewrite    348
        gl_nominal_read_next  342  at end
        gl_nominal_close      354  loop-end

    ⭐ THE TWO OPENS OF THE BATCH FILE ARE BOTH REQUIRED AND ARE NOT THE SAME VERB.
    Phase 1 opens INPUT [general/gl080.cbl:L376] and phase 3 opens I-O
    [general/gl080.cbl:L574]; collapsing them into one open would let phase 1 rewrite,
    and dropping phase 1's close [general/gl080.cbl:L391] would leave the file open
    across a walk that reopens it.

    ⭐ `gl_posting_close` COMES AFTER THE DELETE WALK AND BEFORE THE BATCH REWRITE
    [general/gl080.cbl:L580-L588], which is the account-before-batch ordering Agent
    Action Plan section 0.6.4 names: the batch is stamped only once its postings are
    dealt with.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "123.45")],
        )
        access = FileAccess()
        with _driving(gl080, double):
            gl080.run(
                WsCallingData(),
                system,
                _TO_DAY,
                FileDefs(),
                file_access=access,
            )

        assert double.calls == [
            "gl_batch_open_input",
            "gl_batch_read_next",
            "gl_batch_read_next",
            "gl_batch_close",
            "gl_batch_open",
            "gl_batch_read_next",
            "gl_posting_open",
            "gl_posting_read_next",
            "gl_posting_delete",
            "gl_posting_read_next",
            "gl_posting_close",
            "gl_batch_rewrite",
            "gl_batch_read_next",
            "gl_batch_close",
            "gl_nominal_open",
            "gl_nominal_read_next",
            "gl_nominal_rewrite",
            "gl_nominal_read_next",
            "gl_nominal_close",
        ]
        #  Phase 4 did not run: `File-System-Used` is non-zero, so `not
        #  FS-Cobol-Files-Used` is true and [general/gl080.cbl:L633-L635] leaves at once.
        #  It has no verb of its own in the log, so the absence is asserted through the
        #  one verb it would have used first.
        assert "gl_posting_open_input" not in double.calls


def test_the_archiving_route_replaces_the_deletion_route() -> None:
    """`if archiving` takes phase 2 INSTEAD of phase 3, never as well.

    [general/gl080.cbl:L315-L320] is one `if`/`else`, so exactly one of `gl080b` and
    `gl080c` runs. The observable difference is the archive file: phase 2 writes flat
    rows before deleting the posting [general/gl080.cbl:L468-L508], phase 3 deletes
    without writing anything [general/gl080.cbl:L620].

    Both arms end the same way - the same three stamps and the same rewrite
    [general/gl080.cbl:L428-L433] against [general/gl080.cbl:L583-L588] - which is why
    the batch effect alone cannot tell them apart and the archive is what is asserted.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
        )
        storage = _storage(gl080, system)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  Phase 2's own verb, absent from phase 3's route: `gl080b` opens the archive
        #  and then the batch file for update [general/gl080.cbl:L411-L419].
        assert storage.archive.rows, (
            "the archiving arm wrote no flat archive row, so either the route took the "
            "deletion arm or arc-process stopped before its first write."
        )
        assert "gl_posting_delete" in double.calls
        assert double.batch_rewrites == [
            {
                "key": 7,
                "cleared_status": _CLEARED_ARCHIVED,
                "batch_status": 1,
                "stored": _RUN_DATE,
                "batch_start": 0,
                "items": 1,
            }
        ]


# ---------------------------------------------------------------------------
#  5.  THE ONE `ROUNDED` SITE, IN THE SHIPPED MODULE
#
#      [general/gl080.cbl:L328] is one of only FIVE `ROUNDED` sites in the whole
#      in-scope cycle (Agent Action Plan section 0.6.1), and the sibling file proves
#      what the statement means. What follows proves the shipped module still spells it
#      that way, by reading `a` out of the program's own storage after the call.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("scycle", "period", "expected_a", "truncated_a"),
    [
        #  2.5 -> 3 away from zero. Truncation would leave 2.
        (5, 2, 3, 2),
        #  3.5 -> 4. Truncation would leave 3.
        (7, 2, 4, 3),
        #  1.333... -> 1 either way: rounding DOWN is still rounding, and a case where
        #  the two agree belongs in the table so the discriminating cases are not the
        #  only ones exercised.
        (4, 3, 1, 1),
        #  50.5 -> 51, which still fits `pic 99`. Truncation would leave 50.
        (101, 2, 51, 50),
    ],
)
def test_the_shipped_divide_stores_the_rounded_quotient_into_a(
    scycle: int, period: int, expected_a: int, truncated_a: int
) -> None:
    """`divide scycle by period giving a rounded.` [general/gl080.cbl:L328], observed.

    ⭐ WHY `a` IS READ OUT OF THE STORAGE RATHER THAN INFERRED FROM THE ROUTE. On every
    row in the table the round-trip gate at [general/gl080.cbl:L331-L332] REJECTS, and
    it would reject under truncation too - the gate is an exact-divisibility test, so no
    inexact quotient can pass it whichever way it was rounded. The DISPOSITION therefore
    cannot distinguish the two rounding modes, and the sibling file's census says so.
    The stored value CAN: `st.a` is the program's own `77 a pic 99` and it holds 3 where
    truncation would have left 2. Driving `_gl080_main` with a storage the test owns is
    the only way to see it.

    Rule R-4's stake, from Agent Action Plan section 0.1.1: *"Every other store
    truncates. Getting this backwards would corrupt essentially every posted figure."*
    Here the direction is the annotated exception, and this is the assertion that keeps
    it annotated.
    """
    assert expected_a != truncated_a or scycle % period == 0 or scycle == 4, (
        "the table row claims nothing: rounding and truncation give the same answer and "
        "the quotient is not exact either, so state which case it covers."
    )
    with _shipped_gl080() as gl080:
        system = _system(scycle=scycle, period=period)
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1, "1.00")])
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == expected_a
        #  The product of the un-ROUNDED multiply at [general/gl080.cbl:L329], computed
        #  from the value above and stored into `77 y pic 99` - which is why 51 * 2 = 102
        #  arrives as 2 rather than as 102.
        assert storage.y == (expected_a * period) % 100
        #  The gate rejected, so the cycle was NOT advanced [general/gl080.cbl:L334] and
        #  phase 5 never opened the ledger [general/gl080.cbl:L337].
        assert system.system_data_block.scycle == scycle
        assert "gl_nominal_open" not in double.calls
        assert double.ledger_rewrites == []


@pytest.mark.parametrize(
    ("scycle", "period", "expected_a", "expected_scycle_after"),
    [
        #  12 / 3 = 4 exactly. `add 1 to scycle` gives 13, and then
        #  [general/gl080.cbl:L358-L360] resets a monthly cycle above twelve to one.
        (12, 3, 4, 1),
        #  9 / 3 = 3 exactly, and 10 is not above twelve, so no reset.
        (9, 3, 3, 10),
        #  6 / 2 = 3 exactly. Period two resets at neither three nor thirteen, so the
        #  cycle simply climbs - which is how `a` reaches the out-of-range band.
        (6, 2, 3, 7),
    ],
)
def test_the_round_trip_gate_admits_only_an_exact_multiple(
    scycle: int, period: int, expected_a: int, expected_scycle_after: int
) -> None:
    """The gate passes, so phase 5 runs and the cycle advances.

    `multiply a by period giving y` [general/gl080.cbl:L329] then `if scycle not = y`
    [general/gl080.cbl:L331] is exact divisibility expressed as a round trip. When it
    holds, four things follow in order and all four are asserted: the cycle is
    incremented [general/gl080.cbl:L334], the ledger is opened
    [general/gl080.cbl:L337], every row is rewritten [general/gl080.cbl:L348], and the
    trailing reset rules are applied [general/gl080.cbl:L358-L363].
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=scycle, period=period, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            ledgers=[_ledger_row(1010, "10.00"), _ledger_row(2020, "20.00")],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == expected_a
        assert storage.y == scycle
        assert system.system_data_block.scycle == expected_scycle_after
        assert double.calls.count("gl_nominal_open") == 1
        assert double.calls.count("gl_nominal_close") == 1
        assert [rewrite["key"] for rewrite in double.ledger_rewrites] == [1010, 2020]


def test_the_zero_divisor_reaches_the_shipped_divide_and_stores_nothing() -> None:
    """`period = 0` walks into [general/gl080.cbl:L328], and `a` does not move (Q-7).

    THE GUARD DOES NOT COVER IT. [general/gl080.cbl:L325] turns the block back only when
    `scycle < period`, and no non-negative cycle is below zero, so a zero period reaches
    the divide. What the compiled program then does is ANSWERED and is not what reading
    the statement suggests: GnuCOBOL 3.2 raises the SIZE ERROR condition, performs NO
    STORE and CONTINUES, so the receiving field keeps whatever it held. That is question
    Q-7, and the sibling file locks the semantics layer's half of it against
    `arithmetic.SizeErrorNoStore`.

    ⭐ WHAT THIS TEST ADDS is the half that file cannot reach: THE SHIPPED PROGRAM
    SURVIVES IT. `gl080_end_of_cycle` hands the verb the receiving field's previous value
    - `receiver_value=st.a` - which is what turns the condition into a no-store rather
    than into an exception, so the run continues to `main-end` and returns normally. A
    module that had called the verb WITHOUT `receiver_value` would abort the program
    here, and an operator would see a traceback where the compiled program prints
    nothing.

    ⛔ NOTHING IS GUARDED, CLAMPED OR SUBSTITUTED (R-3): the zero period is not
    validated on the way in, and the no-store leaves `a` holding the value the program
    itself put there at [general/gl080.cbl:L289].
    """
    with _shipped_gl080() as gl080:
        #  The guard at L325 is vacuous against a zero divisor, for every cycle a
        #  signed byte can hold on the non-negative side.
        for cycle in (0, 1, 5, 127):
            assert arithmetic.compare(cycle, 0) >= 0

        system = _system(scycle=4, period=0)
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1, "1.00")])
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            #  No `pytest.raises`: the point is that this RETURNS.
            gl080._gl080_main(storage)

        #  No store happened, so `a` still holds [general/gl080.cbl:L289]'s zero...
        assert storage.a == 0
        #  ... and [general/gl080.cbl:L329] then multiplied that zero by the zero
        #  period, which is a perfectly ordinary store of zero into `y`.
        assert storage.y == 0
        #  The gate compared 4 against 0 and turned the phase back, so the cycle was
        #  not advanced and the ledger was never opened.
        assert system.system_data_block.scycle == 4
        assert "gl_nominal_open" not in double.calls
        assert double.ledger_rewrites == []


# ---------------------------------------------------------------------------
#  6.  ANOMALY A-2 - THE UNBOUNDED QUARTER SUBSCRIPT, IN THE SHIPPED MODULE
#
#      `move ledger-balance to ledger-q (a).` [general/gl080.cbl:L345] against
#      `05 Ledger-Q pic s9(8)v99 comp-3 occurs 4.` [copybooks/wsledger.cob:L36].
#      `a` is the ROUNDED quotient and is NEVER bounds-checked, so an accounting cycle
#      that is not a small multiple of the period length indexes past a four-element
#      table.
#
#      ⛔⛔ DO NOT BOUNDS-CHECK, DO NOT CLAMP, DO NOT WARN (R-3, R-4). Every test in
#      this section asserts that the store HAPPENED and that the walk CONTINUED. The
#      shipped module resolves the subscript to a byte offset and stores into whichever
#      declared item those bytes belong to, which is what the compiled program does; a
#      Python `[a - 1]` would make `a = 0` write the LAST occurrence, a third behaviour
#      belonging to neither language.
#
#      THE DESTINATIONS, from [copybooks/wsledger.cob:L28-L37], and every one of them
#      is exercised below by a `(scycle, period)` pair that reaches it through the real
#      gate rather than by setting `a` directly:
#
#        a = 0        Ledger-Last, A REAL COLUMN      scycle 0, period -1
#        a = 1..4     the four quarters               scycle 12, period 3  -> 4
#        a = 5..12    the trailing filler, no column  scycle 5,  period 1  -> 5
#        a = 13..99   past the 126-byte record        scycle 99, period 1  -> 99
# ---------------------------------------------------------------------------


def test_an_in_range_subscript_writes_both_views_of_the_same_bytes() -> None:
    """`ledger-q (4)` and `Ledger-Q4` are one storage location, and both are written.

    In COBOL `Ledger-Q (a)` and `Ledger-Q1` through `Ledger-Q4` ARE THE SAME BYTES
    [copybooks/wsledger.cob:L30-L36]; in Python they are two dataclass views that do not
    alias, and the record layer deliberately declines to synchronise them because
    keeping a redefines in step would be behaviour in a record layout (R-3).

    ⭐ WHY THIS MATTERS RATHER THAN BEING A CURIOSITY. The `acas005` handler binds its
    columns from the FOUR NAMED FIELDS. A value written into the `occurs` view alone
    would never reach `GLLEDGER-REC` - phase 5's entire table effect would vanish with no
    error and no diagnostic. So the assertion is not "both views agree" for tidiness; it
    is "the view the handler reads was written".

    The subscript here is four, reached honestly: 12 / 3 = 4 exactly, so the gate at
    [general/gl080.cbl:L331] passes and phase 5 runs.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "123.45", last="9.99")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 4
        rewritten = double.ledger_rewrites
        assert len(rewritten) == 1
        #  The named view - what `acas005` binds `LEDGER-Q4` from.
        assert rewritten[0]["quarters"] == (
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("123.45"),
        )
        #  The `occurs` view - the one [general/gl080.cbl:L345] names.
        assert rewritten[0]["occurs_view"] == rewritten[0]["quarters"]
        #  `current-quarter` is one, so [general/gl080.cbl:L346-L347] did NOT fire and
        #  `Ledger-Last` still holds the seeded figure. ANOMALY A-3's independence, from
        #  the other side.
        assert rewritten[0]["last"] == Decimal("9.99")
        #  The balance itself is untouched by the statement: it is the SENDING field.
        assert rewritten[0]["balance"] == Decimal("123.45")


def test_subscript_five_lands_in_the_trailing_filler_and_moves_no_column() -> None:
    """`a = 5` writes past the table, into `filler pic x(50)`, and nothing complains.

    ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345],
    [copybooks/wsledger.cob:L36-L37]. Reached with cycle 5 and period 1: 5 / 1 = 5
    exactly, so the round-trip gate PASSES and phase 5 runs with a subscript one past
    the end of a four-element table. Period one is the ordinary reason this happens -
    nothing resets the cycle for it [general/gl080.cbl:L358-L363], so the quotient
    climbs through the whole `pic 99` domain.

    ⭐ THE STORE IS DATABASE-INVISIBLE, WHICH IS WHY IT IS SILENT. `mysql/ACASDB.sql`
    gives `GLLEDGER-REC` eleven columns and none of them is that filler, so an
    out-of-range quarter store changes the record in memory, is rewritten, and moves NO
    COLUMN. That is exactly the shape of defect a state diff cannot see and a test must.

    ⛔ No `IndexError`, no clamp into 1..4, no warning, and the walk goes on to the next
    account - all four asserted.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=5, period=1, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            ledgers=[
                _ledger_row(1010, "50.00", last="9.99"),
                _ledger_row(2020, "60.00", last="8.88"),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 5
        first, second = double.ledger_rewrites
        #  Not one of the four quarters moved, in either view.
        assert first["quarters"] == (Decimal("0.00"),) * 4
        assert first["occurs_view"] == (Decimal("0.00"),) * 4
        #  Nor `Ledger-Last`, which is where subscript ZERO would have gone.
        assert first["last"] == Decimal("9.99")
        #  The six bytes of the packed value landed at the head of the fifty-byte
        #  filler, because occurrence five begins exactly where the table ends. The
        #  bytes are asserted as a length and a difference rather than as a literal
        #  image: the image is `move`'s business and is locked in its own file.
        default_filler = WsLedgerRecord().filler_l37
        assert len(first["filler"]) == len(default_filler)
        assert first["filler"] != default_filler
        assert first["filler"][6:] == default_filler[6:]
        #  THE WALK CONTINUED: the second account was read, stored into and rewritten
        #  with the same out-of-range subscript.
        assert [rewrite["key"] for rewrite in double.ledger_rewrites] == [1010, 2020]
        assert second["filler"] != default_filler
        assert second["quarters"] == (Decimal("0.00"),) * 4


def test_subscript_zero_overwrites_ledger_last_which_is_a_real_column() -> None:
    """`a = 0` writes `Ledger-Last` - the ONE out-of-range case with a table effect.

    ANOMALY A-2, its most consequential shape. `Ledger-Last`
    [copybooks/wsledger.cob:L29] sits IMMEDIATELY BEFORE `Quarters`
    [copybooks/wsledger.cob:L30] and is the same width as one occurrence, so occurrence
    zero lands squarely on it - and unlike the trailing filler, `LEDGER-LAST` IS A COLUMN
    of `GLLEDGER-REC`. An out-of-range subscript therefore CAN move the database, in
    silence, and this is the case that does it.

    HOW ZERO IS REACHED, and it needs a negative period. [general/gl080.cbl:L324-L325]
    only turns the block back when `a` is nine or `scycle < period`, so a zero quotient
    needs a cycle below one with a period below it - and `Period` is a SIGNED
    `binary-char` [copybooks/wssystem.cob:L64], so a negative value is inside its
    declared domain. Cycle zero with period minus one gives a quotient of zero, `y` of
    zero after the sign drop into `77 y pic 99`, and a gate that PASSES because zero
    equals zero.

    ⭐ THE DISCRIMINATOR: `current-quarter` is ONE here, so [general/gl080.cbl:L346-L347]
    did not fire. `Ledger-Last` therefore holds the balance for one reason only - the
    subscript-zero store. Were the shipped module to clamp the subscript into 1..4, the
    seeded 9.99 would survive and this test would fail, which is the point.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=0, period=-1, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "42.00", last="9.99")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 0
        assert storage.y == 0
        #  The gate passed, so the cycle was advanced - from zero to one.
        assert system.system_data_block.scycle == 1
        rewritten = double.ledger_rewrites
        assert len(rewritten) == 1
        #  THE COLUMN MOVED, and the four quarters did not.
        assert rewritten[0]["last"] == Decimal("42.00")
        assert rewritten[0]["quarters"] == (Decimal("0.00"),) * 4
        assert rewritten[0]["occurs_view"] == (Decimal("0.00"),) * 4
        #  And the filler - the OTHER out-of-range destination - was not touched either,
        #  so the store went to exactly one place.
        assert rewritten[0]["filler"] == WsLedgerRecord().filler_l37


def test_an_out_of_record_subscript_records_the_overrun_and_keeps_walking(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`a = 99` writes wholly past the 126-byte record, and the phase runs to the end.

    ANOMALY A-2 at its far end, and ⚠ AMBIGUITY Q-19: from occurrence thirteen the store
    runs beyond the record into WORKING-STORAGE that belongs to no table, and what the
    compiled program overwrites there is not defined by the record layout. GnuCOBOL
    compiled without bounds checking - and no compile line in this repository passes any
    such flag - stores into whatever follows and CONTINUES.

    THE SHIPPED MODULE'S CHOICE, which this test locks: reproduce the part of the store
    that lands inside the record - here, none of it - and record the overrun as a log
    line rather than raising. Both halves are asserted, because both are load-bearing:
    an exception would end phase 5 at the first oversized cycle and change the
    disposition of every account after it, and a silent no-op would hide the reproduced
    anomaly from the operator entirely.

    HOW 99 IS REACHED: cycle 99 with period 1 divides exactly, so the gate passes.
    `77 a pic 99` [general/gl080.cbl:L183] holds it without overflow.

    ⚠ WHAT IS NOT CLAIMED. This test does not say the compiled program leaves the record
    unchanged; it says the SHIPPED module does, and names Q-19 as the question that
    settles whether an overrunning run moves any of the twenty-two compared tables
    (R-6).
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=99, period=1, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            ledgers=[
                _ledger_row(1010, "3.00", last="1.11"),
                _ledger_row(2020, "4.00", last="2.22"),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with caplog.at_level(logging.ERROR, logger="acas_posting.cobol.move"):
            with _driving(gl080, double):
                gl080._gl080_main(storage)

        assert storage.a == 99
        #  BOTH accounts were rewritten: the walk did not stop at the first overrun.
        assert [rewrite["key"] for rewrite in double.ledger_rewrites] == [1010, 2020]
        #  And the cycle still advanced, so `loop-end` ran too.
        assert system.system_data_block.scycle == 100
        #  Nothing inside the record moved, because none of the six bytes fell inside it.
        blank = WsLedgerRecord()
        for rewrite in double.ledger_rewrites:
            assert rewrite["quarters"] == (Decimal("0.00"),) * 4
            assert rewrite["filler"] == blank.filler_l37
        assert [rewrite["last"] for rewrite in double.ledger_rewrites] == [
            Decimal("1.11"),
            Decimal("2.22"),
        ]

        #  THE OVERRUN WAS RECORDED, once per account, naming the statement and the
        #  subscript. A reproduction that could not be seen would be indistinguishable
        #  from a missing statement.
        overruns = [
            record
            for record in caplog.records
            if record.name == "acas_posting.cobol.move"
        ]
        assert len(overruns) == 2
        for record in overruns:
            message = record.getMessage()
            assert "general/gl080.cbl:L345" in message
            assert "99" in message
            #  The anomaly is named in the message, so an operator reading a log finds
            #  the register entry rather than a mystery.
            assert "A-2" in message


def test_the_in_range_store_records_nothing() -> None:
    """The overrun log line is a REPORT OF AN ANOMALY, not the statement's own trace.

    Without this, the previous test's log assertion would pass just as well if the
    shipped module logged on every store - and a log line on every account of every
    end-of-period run would be noise that hid the one case that matters. So the control
    is asserted: subscript four writes quarter four and says nothing.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1010, "5.00")])
        storage = _storage(gl080, system, a=0)
        with caplog_free() as records:
            with _driving(gl080, double):
                gl080._gl080_main(storage)

        assert storage.a == 4
        assert double.ledger_rewrites[0]["quarters"][3] == Decimal("5.00")
        assert records == []


# ---------------------------------------------------------------------------
#  7.  ANOMALY A-3 - TWO DISAGREEING NOTIONS OF "CURRENT QUARTER"
#
#      [general/gl080.cbl:L345] indexes the quarter table with `a`, the computed
#      quotient. THE VERY NEXT LINE [general/gl080.cbl:L346] tests `current-quarter`,
#      a completely different value maintained by an independent rotating counter at
#      [general/gl080.cbl:L355-L357]. Nothing keeps them in step.
#
#      ⛔ DO NOT RECONCILE THEM (R-3, R-4).
# ---------------------------------------------------------------------------


def test_the_rotating_counter_advances_independently_of_the_subscript() -> None:
    """`add 1 to current-quarter` [general/gl080.cbl:L355] ignores `a` entirely.

    The counter is advanced ONCE PER RUN in `loop-end`, after the walk, while `a` is
    computed once per run from the cycle and the period. They are two unrelated numbers
    that happen to be called the same thing, and this test drives a run where they
    differ by two.

    ANOMALY A-3 [general/gl080.cbl:L345], [general/gl080.cbl:L346],
    [general/gl080.cbl:L355-L357].
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=2)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "77.00", last="1.11")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  The subscript says quarter FOUR.
        assert storage.a == 4
        assert double.ledger_rewrites[0]["quarters"][3] == Decimal("77.00")
        #  The counter said TWO while the row was written, so
        #  [general/gl080.cbl:L346-L347] did not fire...
        assert double.ledger_rewrites[0]["last"] == Decimal("1.11")
        #  ... and afterwards the counter went to THREE, not to five and not to `a`.
        assert system.system_data_block.current_quarter == 3


def test_the_two_notions_of_quarter_can_disagree_in_both_directions() -> None:
    """Quarter one written while `Ledger-Last` is stamped as if it were year end.

    THE SHARPEST FORM OF A-3. `a` is one - the FIRST quarter - so
    [general/gl080.cbl:L345] writes `ledger-q (1)`, while `current-quarter` is four, so
    [general/gl080.cbl:L346-L347] ALSO writes `Ledger-Last`, the field that means "the
    closing balance of the year". The row therefore says both "this is the first quarter"
    and "this is the end of the year" at once, and the compiled program writes it exactly
    that way.

    Reached with cycle 3 and period 3: 3 / 3 = 1 exactly, so the gate passes with a
    subscript of one.

    ⛔ NOT RECONCILED (R-4): no test here asserts that the two agree, and no code is
    changed to make them.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=3, period=3, current_quarter=4)
        double = _GlFacadeDouble(
            gl080.facade, ledgers=[_ledger_row(1010, "88.00", last="1.11")]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 1
        rewritten = double.ledger_rewrites[0]
        #  Quarter ONE received the balance.
        assert rewritten["quarters"] == (
            Decimal("88.00"),
            Decimal("0.00"),
            Decimal("0.00"),
            Decimal("0.00"),
        )
        #  And `Ledger-Last` received it too, from the OTHER notion of quarter.
        assert rewritten["last"] == Decimal("88.00")
        #  The counter was four, so `loop-end` rolled it back to one
        #  [general/gl080.cbl:L356-L357] - while the cycle went 3 -> 4, nowhere near a
        #  reset.
        assert system.system_data_block.current_quarter == 1
        assert system.system_data_block.scycle == 4


@pytest.mark.parametrize(
    (
        "period",
        "scycle",
        "current_quarter",
        "expected_quarter_after",
        "expected_scycle_after",
    ),
    [
        #  Monthly accounting, cycle 12: the counter rolls 4 -> 1 and the cycle is reset
        #  from 13 to 1 by [general/gl080.cbl:L358-L360].
        (3, 12, 4, 1, 1),
        #  Monthly accounting, cycle 9: the counter climbs, and 10 is not above twelve so
        #  no cycle reset.
        (3, 9, 2, 3, 10),
        #  Weekly accounting at the year end: 52 / 13 = 4 exactly, the increment gives
        #  53, and 53 IS above 52, so [general/gl080.cbl:L361-L363] resets it.
        (13, 52, 4, 1, 1),
        #  Weekly accounting mid-year: 39 / 13 = 3, the increment gives 40, which is not
        #  above 52.
        (13, 39, 1, 2, 40),
        #  ⭐ ANY OTHER PERIOD NEVER RESETS. Period 1, cycle 6: the cycle climbs to 7 and
        #  keeps climbing on later runs, which is how `a` reaches the out-of-range band
        #  at all. THE TWO RESET RULES ARE THE ONLY TWO, and they are conjunctions.
        (1, 6, 3, 4, 7),
        #  Period 2, cycle 12: 12 is above twelve, but the period is not three, so the
        #  first conjunction fails and there is no reset. The conjunction is asserted by
        #  the absence.
        (2, 12, 4, 1, 13),
    ],
)
def test_the_counter_and_the_cycle_wrap_by_their_own_separate_rules(
    period: int,
    scycle: int,
    current_quarter: int,
    expected_quarter_after: int,
    expected_scycle_after: int,
) -> None:
    """`loop-end` [general/gl080.cbl:L354-L363], driven through the shipped module.

    FOUR STATEMENTS, THREE INDEPENDENT RULES, no `else` between them: the counter is
    incremented and wrapped at five, and the cycle is reset by two conjunctions that can
    never both hold because a period cannot be both three and thirteen. Merging them,
    turning either into an `else`, or inferring a reset for a period the source does not
    name would all be caught here.

    ANOMALY A-3 rides along in every row: `expected_quarter_after` is computed from
    `current_quarter` alone and never from `a`.
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=scycle, period=period, current_quarter=current_quarter
        )
        double = _GlFacadeDouble(gl080.facade, ledgers=[_ledger_row(1010, "1.00")])
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  Every row divides exactly, so the gate passed and `loop-end` was reached.
        assert storage.y == scycle
        assert system.system_data_block.current_quarter == expected_quarter_after
        assert system.system_data_block.scycle == expected_scycle_after
        #  A period cannot satisfy both reset conditions, whatever the cycle.
        assert arithmetic.compare(3, 13) != 0



# ---------------------------------------------------------------------------
#  8.  PHASE 1 - THE OUTSTANDING-BATCH GATE
#
#      `gl080a` [general/gl080.cbl:L368-L395] walks the batch file and sets `a` to one
#      if it finds a batch in this cycle that is neither closed nor processed;
#      [general/gl080.cbl:L308-L313] then stops the whole run. THE DETECTOR PREDICATE
#      IS NOT `gl070`'S: `gl070` tests one condition name [general/gl070.cbl:L314],
#      this program tests the conjunction of two negations
#      [general/gl080.cbl:L384-L386].
# ---------------------------------------------------------------------------


def test_an_outstanding_batch_stops_the_run_before_any_write() -> None:
    """`if a = 1 ... go to main-end` [general/gl080.cbl:L308-L313].

    An outstanding batch means the cycle is not ready to close, and the compiled program
    responds by returning - not by aborting, not by setting a term code, and not by
    writing anything. `gl080` never sets a term code at all, which is why its caller's
    `load00.` block has no `= 5` gate the way `load08` does
    [general/general.cbl:L711-L722].

    ⭐ EVERY LATER PHASE IS ABSENT, and that is the whole assertion: no batch rewrite,
    no posting delete, no archive row, no ledger verb and no cycle increment. A run that
    stopped later - after phase 3 had already deleted the postings, say - would leave the
    database in a state the compiled program never produces.

    THE BATCH SEEDED HERE fails BOTH negations: status zero is not
    `88 Status-Closed value 1` [copybooks/wsbatch.cob:L27] and cleared status zero is not
    `88 Processed value 1` [copybooks/wsbatch.cob:L31], so [general/gl080.cbl:L386] sets
    `a` to one.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12, batch_status=0, cleared_status=0)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, system, a=0)
        before = dataclasses.asdict(storage.ledger)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.a == 1
        #  Phase 1 and nothing else.
        assert double.calls == [
            "gl_batch_open_input",
            "gl_batch_read_next",
            "gl_batch_read_next",
            "gl_batch_close",
        ]
        assert double.batch_rewrites == []
        assert double.posting_deletes == []
        assert double.ledger_rewrites == []
        assert storage.archive.rows == ()
        #  The cycle did not move, so a later run sees the same cycle and can try again.
        assert system.system_data_block.scycle == 12
        #  And the ledger record the program carries was never touched.
        assert dataclasses.asdict(storage.ledger) == before


@pytest.mark.parametrize(
    ("batch_status", "cleared_status", "expected_a"),
    [
        #  Neither negation satisfied -> outstanding.
        (0, 0, 1),
        #  Closed but not processed -> the first negation fails, so the conjunction
        #  fails and `a` stays zero.
        (1, 0, 0),
        #  Processed but not closed -> the second negation fails.
        (0, 1, 0),
        #  Both -> the batch is finished with, and the run proceeds.
        (1, 1, 0),
    ],
)
def test_the_detector_needs_both_negations_at_once(
    batch_status: int, cleared_status: int, expected_a: int
) -> None:
    """`if not status-closed and not processed` [general/gl080.cbl:L384-L386].

    A CONJUNCTION OF TWO NEGATIONS, which is not the same as either negation alone and
    not the same as `gl070`'s single `if status-open` [general/gl070.cbl:L314]. The truth
    table is asserted whole, because three of its four rows let the run PROCEED and only
    one stops it - so a fix that turned the conjunction into a disjunction would stop
    runs the compiled program allows, and the failure would look like a business rule
    rather than like a defect.

    The section is driven directly rather than through `run`, because what is asserted is
    the detector's own output - `a` - and `_gl080_main` would then consume it.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[
                _batch_row(
                    7, 12, batch_status=batch_status, cleared_status=cleared_status
                )
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080a(storage)

        assert storage.a == expected_a
        #  The file was opened for INPUT and closed again, whichever way the test went.
        assert double.calls[0] == "gl_batch_open_input"
        assert double.calls[-1] == "gl_batch_close"


def test_the_detector_ignores_a_batch_from_another_cycle() -> None:
    """`if bcycle not = scycle go to loop` [general/gl080.cbl:L380-L382].

    The cycle filter comes FIRST, so a batch left open in a previous cycle does not block
    this cycle's close - and the status test is never reached for it. Asserted with a
    batch that WOULD be outstanding if it were examined: were the filter dropped, `a`
    would come back as one.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(9, 11, batch_status=0, cleared_status=0)],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080a(storage)

        assert storage.a == 0
        #  The row WAS read - the filter is inside the loop, not in the read.
        assert double.calls.count("gl_batch_read_next") == 2


# ---------------------------------------------------------------------------
#  9.  PHASE 2 - THE ARCHIVING WALK
#
#      `arc-process` [general/gl080.cbl:L445-L516] explodes every posting of the batch
#      into TWO OR THREE flat archive rows and then deletes the posting. The three legs
#      and their signs are the frozen source's, verbatim:
#
#        leg 1  DR side  arc-ac <- post-dr, arc-c-ac <- post-cr, amount POSITIVE,
#                        plus the VAT when `post-vat-side = "CR"`
#                        [general/gl080.cbl:L468-L479]
#        leg 2  CR side  the two accounts SWAPPED, plus the VAT when the side is "DR",
#                        then `multiply arc-amount by -1` [general/gl080.cbl:L481-L493]
#        leg 3  VAT      only when both `vat-ac` and `vat-amount` are non-zero, negated
#                        when the side is "CR" [general/gl080.cbl:L497-L508]
# ---------------------------------------------------------------------------


def test_the_archive_walk_writes_the_double_entry_and_the_vat_leg() -> None:
    """Three rows, three signs, one delete - `arc-process` in full.

    THE FIGURES, and every one of them is a consequence of a cited line rather than a
    choice: a posting of 100.00 with 17.50 of VAT on the CR side gives

        leg 1  arc-ac 1010 / 11   arc-c-ac 2020 / 22   amount  117.50
        leg 2  arc-ac 2020 / 22   arc-c-ac 1010 / 11   amount -100.00
        leg 3  arc-ac 3030 / 33   arc-c-ac 1010 / 11   amount  -17.50

    Leg 1 carries the VAT because the side is "CR" [general/gl080.cbl:L475-L477]; leg 2
    does NOT, because the same test at [general/gl080.cbl:L489-L491] asks for "DR", and it
    is then negated unconditionally [general/gl080.cbl:L493]; leg 3 is negated for the
    same "CR" reason [general/gl080.cbl:L505-L506].

    ⭐ LEG 3'S CONTRA ACCOUNT IS LEG 2'S, AND THAT IS NOT AN OVERSIGHT IN THIS TEST.
    [general/gl080.cbl:L501-L503] moves only `arc-ac`, `arc-pc` and `arc-amount` before
    the third `write`, so `arc-c-ac` and `arc-c-pc` still hold what leg 2 put there. The
    compiled program writes the record it has, fields and all, and so does the shipped
    module (R-4). Asserting the leftover is how a future "tidy-up" that cleared the
    contra fields gets caught.

    All four money figures are `Decimal` built from strings; nothing here goes near a
    binary float (R-2).
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                _posting_row(
                    7,
                    3,
                    amount="100.00",
                    vat_ac=3030,
                    vat_pc=33,
                    vat_amount="17.50",
                    vat_side="CR",
                )
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        rows = storage.archive.rows
        assert len(rows) == 3

        assert (rows[0].arc_batch, rows[0].arc_post) == (7, 3)
        assert (rows[0].arc_ac, rows[0].arc_pc) == (1010, 11)
        assert (rows[0].arc_c_ac, rows[0].arc_c_pc) == (2020, 22)
        assert rows[0].arc_amount == Decimal("117.50")

        assert (rows[1].arc_ac, rows[1].arc_pc) == (2020, 22)
        assert (rows[1].arc_c_ac, rows[1].arc_c_pc) == (1010, 11)
        assert rows[1].arc_amount == Decimal("-100.00")

        assert (rows[2].arc_ac, rows[2].arc_pc) == (3030, 33)
        #  The leftover contra, per the docstring.
        assert (rows[2].arc_c_ac, rows[2].arc_c_pc) == (1010, 11)
        assert rows[2].arc_amount == Decimal("-17.50")

        #  The posting's own fields are carried into all three rows unchanged
        #  [general/gl080.cbl:L464-L466].
        for row in rows:
            assert row.arc_code == "GL"
            assert row.arc_date == "21/09/25"
            assert row.arc_legend.rstrip() == "END OF CYCLE TEST"

        #  And then the posting is deleted, once, AFTER the last write
        #  [general/gl080.cbl:L510-L512].
        assert double.posting_deletes == [(7, 3)]
        assert double.calls.index("gl_posting_delete") > double.calls.index(
            "gl_posting_read_next"
        )


@pytest.mark.parametrize(
    ("vat_ac", "vat_amount"),
    [
        #  `if vat-ac equal zero` - the first disjunct [general/gl080.cbl:L497].
        (0, "17.50"),
        #  `or vat-amount = zero` - the second [general/gl080.cbl:L498].
        (3030, "0.00"),
        #  Both, which is the ordinary case for a posting that carries no VAT.
        (0, "0.00"),
    ],
)
def test_the_archive_walk_omits_the_vat_leg_when_either_vat_field_is_zero(
    vat_ac: int, vat_amount: str
) -> None:
    """`go to by-pass` [general/gl080.cbl:L497-L499] - two rows, not three.

    A DISJUNCTION, so either field alone suppresses the leg. The delete at
    [general/gl080.cbl:L511] still happens, because `by-pass` is where the jump lands
    and the delete is its only statement - so a posting with no VAT is archived as a
    plain double entry and removed exactly like one with VAT.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                _posting_row(
                    7,
                    1,
                    amount="60.00",
                    vat_ac=vat_ac,
                    vat_pc=33,
                    vat_amount=vat_amount,
                    vat_side="DR",
                )
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        rows = storage.archive.rows
        assert len(rows) == 2
        #  The side is "DR" here, so the VAT - where there is any - belongs to leg 2,
        #  which is also the negated one [general/gl080.cbl:L489-L493].
        expected_second = -(Decimal("60.00") + Decimal(vat_amount))
        assert rows[0].arc_amount == Decimal("60.00")
        assert rows[1].arc_amount == expected_second
        assert double.posting_deletes == [(7, 1)]


def test_the_archive_walk_skips_the_zero_key_and_a_foreign_batch() -> None:
    """`if WS-Post-Key = zero or batch not = WS-Batch-Nos go to loop`
    [general/gl080.cbl:L458-L460].

    Two filters in one condition, and the consequence of dropping either is a posting
    archived under the wrong batch or a placeholder row archived as if it were real.
    Asserted with three seeded postings of which exactly ONE belongs to the batch: the
    archive gets that one's rows and the deletes name that one only.

    ⭐ THE ZERO KEY IS THE WHOLE GROUP, not the batch alone: `WS-Post-Key` spans both
    `Batch` and `Post-Number` [copybooks/wspost.cob:L12-L14], so a row with batch zero
    and a NON-zero post number does not match the first disjunct - it is caught by the
    second instead, because zero is not this batch. Both shapes are seeded so that the
    group test cannot be mistaken for a test of `batch` alone.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                #  The whole key is zero - the first disjunct.
                _posting_row(0, 0, amount="1.00"),
                #  Another batch - the second disjunct.
                _posting_row(8, 1, amount="2.00"),
                #  Batch zero with a real post number: not the zero GROUP, but still not
                #  this batch.
                _posting_row(0, 5, amount="3.00"),
                #  The only one that belongs here.
                _posting_row(7, 9, amount="4.00"),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert double.posting_deletes == [(7, 9)]
        rows = storage.archive.rows
        assert len(rows) == 2
        assert rows[0].arc_amount == Decimal("4.00")
        assert rows[1].arc_amount == Decimal("-4.00")
        assert {row.arc_post for row in rows} == {9}


def test_the_extend_then_output_fallback_creates_the_archive_and_appends_to_it() -> None:
    """`open extend` then, on a non-zero status, `close` and `open output`
    [general/gl080.cbl:L411-L414].

    THE MAINTAINER'S OWN IDIOM, and his comment explains it: try to append, and if that
    fails create the file. Both arms are exercised, because they differ in exactly one
    observable - whether what was already in the file survives.

    ARM ONE, the fallback. A fresh archive does not exist, so `open extend` answers a
    non-zero file status; the shipped `_ArchiveFile` reports 35, the ISAM "file not
    found". The walk then writes its rows anyway, which is the whole point of the
    fallback: without it, `gl080b` would append to a file it never opened.

    ARM TWO, the append. An archive that already holds a row opens for extend
    successfully, and the pre-existing row is STILL THERE afterwards, followed by this
    run's. An `open output` that ran unconditionally would have truncated it - losing
    every previously archived cycle - and this assertion is what stands between the two.
    """
    with _shipped_gl080() as gl080:
        #  The premise of arm one, asserted rather than assumed: a file that has never
        #  been created answers `open extend` with a non-zero status.
        access = FileAccess()
        fresh = gl080._ArchiveFile(access)
        fresh.open_extend()
        assert access.fs_reply != _FS_OK

        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[_posting_row(7, 1, amount="5.00")],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)
        #  ARM ONE: the rows were written despite the failed extend.
        assert [row.arc_amount for row in storage.archive.rows] == [
            Decimal("5.00"),
            Decimal("-5.00"),
        ]

    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[_posting_row(7, 1, amount="5.00")],
        )
        storage = _storage(gl080, system, a=0)
        #  A previous cycle's archive: created, written and closed, so the file EXISTS.
        storage.archive.open_output()
        storage.archive.record.arc_batch = 999
        storage.archive.record.arc_amount = Decimal("11.11")
        storage.archive.write()
        storage.archive.close()

        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  ARM TWO: the earlier row survived and this run's two follow it.
        rows = storage.archive.rows
        assert len(rows) == 3
        assert (rows[0].arc_batch, rows[0].arc_amount) == (999, Decimal("11.11"))
        assert [row.arc_amount for row in rows[1:]] == [
            Decimal("5.00"),
            Decimal("-5.00"),
        ]


# ---------------------------------------------------------------------------
#  10.  PHASE 3 - THE DELETION WALK
# ---------------------------------------------------------------------------


def test_the_deletion_walk_deletes_the_batchs_postings_and_writes_no_archive_row() -> None:
    """`del-process` [general/gl080.cbl:L600-L625] - the same walk, without the archive.

    The two walks share their filters [general/gl080.cbl:L615-L617] and their stamps
    [general/gl080.cbl:L583-L588], and differ in that this one has no `write`. So the
    assertion that separates them is the EMPTY ARCHIVE, and the assertion that they
    share is the identical batch stamp - both are made here.

    THE POSTINGS ARE DELETED IN THE ORDER THEY ARE READ, which for a sequential walk is
    the order of the store. Asserted as a list rather than as a set: order is a
    behavioural fact here, not an incidental one.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=4, period=3, arch=_NOT_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 4)],
            postings=[
                _posting_row(7, 1),
                _posting_row(8, 1),
                _posting_row(7, 2),
                _posting_row(0, 0),
            ],
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert double.posting_deletes == [(7, 1), (7, 2)]
        assert storage.archive.rows == ()
        assert double.batch_rewrites == [
            {
                "key": 7,
                "cleared_status": _CLEARED_ARCHIVED,
                "batch_status": 1,
                "stored": _RUN_DATE,
                "batch_start": 0,
                "items": 1,
            }
        ]


def test_both_walks_stamp_the_batch_the_same_way() -> None:
    """[general/gl080.cbl:L428-L433] and [general/gl080.cbl:L583-L588], side by side.

    ⭐ `Cleared-Status` BECOMES 2, WHICH IS `88 Archived`
    [copybooks/wsbatch.cob:L32] - EVEN ON THE DELETION ROUTE, where nothing was archived
    at all. The name is wrong for what the deletion walk did, and the value is what the
    compiled program stores; both routes are asserted to store it so that a "fix" giving
    the deletion route a different status fails here (R-4).

    `Stored` receives `Run-Date` off the system record [copybooks/wssystem.cob:L67],
    which is the determinism requirement in miniature: the date arrives through linkage
    and no clock is read (R-6). `Batch-Start` is zeroed
    [general/gl080.cbl:L432], [general/gl080.cbl:L587].
    """
    stamps = []
    for arch in (_ARCHIVING, _NOT_ARCHIVING):
        with _shipped_gl080() as gl080:
            system = _system(scycle=4, period=3, arch=arch)
            double = _GlFacadeDouble(
                gl080.facade,
                batches=[_batch_row(7, 4)],
                postings=[_posting_row(7, 1)],
            )
            storage = _storage(gl080, system, a=0)
            with _driving(gl080, double):
                gl080._gl080_main(storage)
            stamps.append(double.batch_rewrites)

    archiving, deleting = stamps
    assert archiving == deleting
    assert archiving[0]["cleared_status"] == _CLEARED_ARCHIVED
    assert archiving[0]["stored"] == _RUN_DATE
    assert archiving[0]["batch_start"] == 0


# ---------------------------------------------------------------------------
#  11.  `disk-change` - THE PROMOTED OPTION, AND `a`'S SECOND ROLE
#
#      [general/gl080.cbl:L519-L559]. Agent Action Plan section 0.3.4 makes the accept
#      at [general/gl080.cbl:L545-L547] a parameter because its answer decides whether
#      the database is written: nine suppresses the archiving walk AND, through the
#      shared `a`, the whole of end-of-period processing.
# ---------------------------------------------------------------------------


def test_the_disk_change_abort_suppresses_archiving_and_end_of_period() -> None:
    """⭐ `a` CARRIES THE ABORT CODE ACROSS TWO PHASES - one field, two purposes.

    `accept-option` stores the answer into `a` [general/gl080.cbl:L545]. `gl080b` tests
    it immediately and leaves [general/gl080.cbl:L408-L409]; then
    [general/gl080.cbl:L324] tests THE SAME FIELD and turns end-of-period back too. So
    one operator answer stops two unrelated phases, through a field whose third use is
    the quarter subscript.

    THE DISCRIMINATING PAIR. Both runs below are identical except for the option, and
    the cycle and period are chosen so that end-of-period WOULD run: 12 / 3 = 4 exactly.
    With the option at zero the ledger is walked and the cycle advances; with it at nine
    neither happens. A module that had used a local variable for the `disk-change`
    answer - the obvious tidy-up - would archive nothing and then still run
    end-of-period, and the difference between the two runs would collapse.
    """
    with _shipped_gl080() as gl080:
        proceeding = _system(scycle=12, period=3, current_quarter=1, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, proceeding, a=0, disk_change_option=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert storage.archive.rows != ()
        assert double.ledger_rewrites != []
        #  13, then reset to 1 by the monthly rule.
        assert proceeding.system_data_block.scycle == 1

    with _shipped_gl080() as gl080:
        aborting = _system(scycle=12, period=3, current_quarter=1, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, aborting, a=0, disk_change_option=9)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  Nothing archived, nothing deleted, no batch stamped...
        assert storage.archive.rows == ()
        assert double.posting_deletes == []
        assert double.batch_rewrites == []
        #  ... and end-of-period did not run either, because `a` still holds the nine.
        assert storage.a == 9
        assert double.ledger_rewrites == []
        assert "gl_nominal_open" not in double.calls
        assert aborting.system_data_block.scycle == 12
        assert aborting.system_data_block.current_quarter == 1


@pytest.mark.parametrize("option", [1, 2, 5, 8, 10, 99])
def test_a_disk_change_option_outside_zero_and_nine_is_refused_before_any_write(
    option: int,
) -> None:
    """`if a not = zero go to accept-option` [general/gl080.cbl:L548-L549].

    THE DOMAIN IS EXACTLY {0, 9}, because every other value is sent back to the prompt
    and the prompt is not a parameter - so no third value can reach the statements below
    it. The shipped module refuses rather than proceeding, which is the CLI-boundary
    finding its own docstring records: a caller that passed 5 would otherwise silently
    get the "proceed" arm, which is the one answer the compiled program certainly does
    not give.

    ⛔ THIS IS NOT AN ADDED VALIDATION (R-3). The refusal replaces an unreachable state
    with an error at the boundary; it does not reject an input the compiled program
    accepts, because the compiled program never accepts one - it loops.

    NOTHING IS WRITTEN when it fires: the exception comes out of `disk-change`, which
    runs BEFORE the archive is opened [general/gl080.cbl:L411] and before the batch file
    is opened for update [general/gl080.cbl:L419].
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        storage = _storage(gl080, system, a=0, disk_change_option=option)
        with _driving(gl080, double):
            with pytest.raises(gl080.DiskChangeOptionNotAcceptable) as refused:
                gl080._gl080_main(storage)

        assert str(option) in str(refused.value)
        assert storage.archive.rows == ()
        assert double.batch_rewrites == []
        assert double.posting_deletes == []
        assert double.ledger_rewrites == []
        #  Phase 1 ran, because it comes first; phase 2 got as far as `disk-change`.
        assert "gl_batch_open_input" in double.calls
        assert "gl_batch_open" not in double.calls


def test_the_archive_path_is_composed_and_a_blank_override_is_ignored() -> None:
    """`string ... into arg-test` then `move arg-test to file-2`
    [general/gl080.cbl:L530-L539].

    FOUR SOURCES, TWO DELIMITER FORMS. `file-24` and `file-2` are `delimited by space`,
    so each contributes up to its first space; the literal `"archives"` and the operating
    system's separator are `delimited by size`, so they contribute in full. With a base
    of `/opt/acas/` and a separator of `/` the result is
    `/opt/acas/archives/archive.dat`, and that string is then moved back over `file-2` -
    which is why the composition is observable at all.

    THE OVERRIDE, and its guard. [general/gl080.cbl:L550-L557] accepts an edited path and
    keeps it only `if file-2 (1:1) not = space`; a leading space means the operator
    pressed Enter and the composed path stands. Both arms asserted, because a module that
    dropped the guard would replace a working path with a blank one.

    ⛔ NO TABLE EFFECT EITHER WAY. The archive is a flat file, not a schema table, so
    nothing here reaches the comparison - which is precisely why it needs a test of its
    own.
    """
    base = "/opt/acas/"
    with _shipped_gl080() as gl080:
        file_defs = FileDefs()
        file_defs.file_defs_os_delimiter = "/"
        file_defs.file_defs_a.file_24 = base.ljust(len(file_defs.file_defs_a.file_24))
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(gl080, system, file_defs=file_defs, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert (
            storage.file_defs.file_defs_a.file_2.rstrip()
            == "/opt/acas/archives/archive.dat"
        )

    with _shipped_gl080() as gl080:
        file_defs = FileDefs()
        file_defs.file_defs_os_delimiter = "/"
        file_defs.file_defs_a.file_24 = base.ljust(len(file_defs.file_defs_a.file_24))
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(
            gl080,
            system,
            file_defs=file_defs,
            a=0,
            archive_path_override="/var/spool/acas-archive.dat",
        )
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert (
            storage.file_defs.file_defs_a.file_2.rstrip()
            == "/var/spool/acas-archive.dat"
        )

    with _shipped_gl080() as gl080:
        file_defs = FileDefs()
        file_defs.file_defs_os_delimiter = "/"
        file_defs.file_defs_a.file_24 = base.ljust(len(file_defs.file_defs_a.file_24))
        system = _system(scycle=4, period=3, arch=_ARCHIVING)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(
            gl080,
            system,
            file_defs=file_defs,
            a=0,
            #  A leading space: the operator accepted the composed path.
            archive_path_override=" /var/spool/ignored.dat",
        )
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert (
            storage.file_defs.file_defs_a.file_2.rstrip()
            == "/opt/acas/archives/archive.dat"
        )


# ---------------------------------------------------------------------------
#  12.  PHASE 4 - POSTING CONTRACTION, AND THE RECORD-LENGTH STOP
#
#      `compress-post` [general/gl080.cbl:L628-L708] copies every posting out to a work
#      file, re-creates the posting store and copies them back - a physical compaction
#      that only makes sense for indexed files. Its first statement is a configuration
#      test, and its second is a length comparison that STOPS THE RUN.
# ---------------------------------------------------------------------------


def test_phase_four_does_not_run_in_the_rdbms_configuration() -> None:
    """`if not FS-Cobol-Files-Used go to main-exit` [general/gl080.cbl:L633-L635].

    `88 FS-Cobol-Files-Used value zero` over `File-System-Used`, so a NON-zero value
    means an RDBMS - which is the configuration every scenario in this migration runs in.
    Phase 4 therefore leaves before it opens anything, and the whole of the compaction is
    dead code for a database run.

    ASSERTED BY ABSENCE, with the two verbs only phase 4 uses
    [general/gl080.cbl:L651-L652], [general/gl080.cbl:L671-L672] - and by the work file
    staying empty.
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=4, period=3, file_system_used=_FILE_SYSTEM_RDBMS
        )
        double = _GlFacadeDouble(
            gl080.facade, postings=[_posting_row(5, 1), _posting_row(5, 2)]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            gl080._compress_post(storage)

        assert double.calls == []
        assert storage.work_file.rows == ()
        assert double.posting_writes == []


def test_phase_four_stops_the_run_on_the_record_length_disagreement() -> None:
    """`stop run.` [general/gl080.cbl:L643-L649] - and it fires on EVERY Cobol-files run.

    ⚠ AMBIGUITY Q-23, and this test is what makes it visible rather than theoretical.
    The frozen guard is

        if function length (WS-Posting-Record) not =
           function length (work-file-record)   ... stop run.

    and the two are NOT equal: the posting record is 103 bytes and
    `work-file-record pic x(101)` [general/gl080.cbl:L173] is 101. So in the Cobol-files
    configuration `compress-post` reaches the comparison, finds a mismatch and ENDS THE
    RUN UNIT - phase 4 cannot complete, and neither can anything after it.

    ⛔ THE MISMATCH IS NOT REPAIRED (R-4). Padding the work record to 103, or comparing
    something else, would make a stop the compiled program performs disappear. What the
    shipped module does instead is raise its own `_StopRun`, whose message carries both
    lengths and the locator, so an operator sees the same halt with a reason attached.

    ⭐ WHY THE TWO FIGURES ARE ASSERTED. Q-23 asks when this can happen; the answer this
    test records is "whenever the run uses Cobol files", and it can only record that by
    naming the lengths. Were either declaration to change, this test would fail and the
    register entry would need revisiting - which is the correct outcome, not a nuisance.

    NOTHING IS WRITTEN BEFORE THE STOP: the guard precedes the posting open
    [general/gl080.cbl:L651] and the work-file open [general/gl080.cbl:L652].
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=4, period=3, file_system_used=_FILE_SYSTEM_COBOL
        )
        double = _GlFacadeDouble(
            gl080.facade, postings=[_posting_row(5, 1), _posting_row(5, 2)]
        )
        storage = _storage(gl080, system, a=0)
        with _driving(gl080, double):
            with pytest.raises(gl080._StopRun) as stopped:
                gl080._compress_post(storage)

        message = str(stopped.value)
        assert "103" in message
        assert "101" in message
        assert "general/gl080.cbl:L643-L649" in message
        #  Nothing was opened, nothing was copied and nothing was written back.
        assert double.calls == []
        assert storage.work_file.rows == ()
        assert double.posting_writes == []


def test_the_record_length_stop_propagates_out_of_the_whole_program() -> None:
    """`stop run` ends the RUN UNIT, so it is not caught on the way out either.

    [general/gl080.cbl:L322] performs `compress-post` from the middle of
    `gl080-Main`, between phase 3 and the end-of-period gate. A `stop run` there means
    the phases after it never execute - so the assertion is both that the exception
    reaches the caller of `run` and that end-of-period left no trace.

    This is the ONE place where the shipped program's disposition depends on the flat-file
    configuration, and a scenario cannot reach it: every scenario runs with an RDBMS. The
    test is therefore the only witness (R-6).
    """
    with _shipped_gl080() as gl080:
        system = _system(
            scycle=12,
            period=3,
            current_quarter=1,
            file_system_used=_FILE_SYSTEM_COBOL,
        )
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        with _driving(gl080, double):
            with pytest.raises(gl080._StopRun):
                gl080.run(
                    WsCallingData(),
                    system,
                    _TO_DAY,
                    FileDefs(),
                    file_access=FileAccess(),
                )

        #  Phase 3 had already run and stamped the batch - that state is real and is
        #  what the compiled program leaves behind too.
        assert double.batch_rewrites != []
        #  End-of-period never started.
        assert double.ledger_rewrites == []
        assert system.system_data_block.scycle == 12


# ---------------------------------------------------------------------------
#  13.  THE PROMOTED CONFIRM, THE DATE-FORM MUTATION, AND DETERMINISM
# ---------------------------------------------------------------------------


def test_an_unconfirmed_run_writes_nothing_at_all() -> None:
    """`accept keyed-reply` then `goback` [general/gl080.cbl:L299-L304].

    THE BACKUP QUESTION IS A GATE, not a courtesy: Escape or "A" returns before a single
    handler is called. Agent Action Plan section 0.3.4 promotes it to a parameter because
    its answer changes table state - here by preventing every change - and the default is
    the answer that proceeds.

    ZERO VERBS, which is a stronger claim than "no writes": phase 1 does not even open
    the batch file.
    """
    with _shipped_gl080() as gl080:
        system = _system(scycle=12, period=3, current_quarter=1)
        double = _GlFacadeDouble(
            gl080.facade,
            batches=[_batch_row(7, 12)],
            postings=[_posting_row(7, 1)],
            ledgers=[_ledger_row(1010, "1.00")],
        )
        with _driving(gl080, double):
            gl080.run(
                WsCallingData(),
                system,
                _TO_DAY,
                FileDefs(),
                file_access=FileAccess(),
                run_confirmed=False,
            )

        assert double.calls == []
        assert double.batch_rewrites == []
        assert double.ledger_rewrites == []
        assert system.system_data_block.scycle == 12


def test_the_run_fills_date_form_when_it_is_zero_and_leaves_a_set_value_alone() -> None:
    """`zz070-Convert-Date` [general/gl080.cbl:L719-L747] MUTATES the system record.

    ⭐ THE DISPLAY IS DROPPED AND THE STATEMENT IS NOT. [general/gl080.cbl:L285] performs
    the date conversion only so that [general/gl080.cbl:L286] can display the result, and
    presentation is out of scope (Agent Action Plan section 0.3.4) - but the section also
    writes `Date-Form` when that field is zero [general/gl080.cbl:L729-L730], and
    `Date-Form` IS A COLUMN of `SYSTEM-REC` [copybooks/wssystem.cob:L127]. Dropping the
    performed section with the display it fed would have removed a database effect.

    ⭐⭐ AND THIS IS WHY `SYSTEM-REC` IS FINGERPRINTED RATHER THAN LEFT UNWATCHED. The
    scenario harness records a digest of `SYSTEM-REC` on both sides precisely because
    routes like this one move it without meaning to; `tests/conftest.py`'s
    `PARAMETER_TABLE` carries the reasoning.

    Both arms: zero is filled with the UK form, and a value already set is left as it is
    - which is the `if` at [general/gl080.cbl:L729] rather than an unconditional move.
    """
    with _shipped_gl080() as gl080:
        unset = _system(scycle=4, period=3)
        assert unset.system_data_block.date_form == 0
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(gl080, unset, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        #  `1` is the UK form [copybooks/wssystem.cob], the default the section supplies.
        assert unset.system_data_block.date_form == 1
        #  And the converted text is the date that arrived through linkage, which is the
        #  determinism claim in one line (R-6).
        assert storage.ws_date_formats.ws_date == _TO_DAY

    with _shipped_gl080() as gl080:
        preset = _system(scycle=4, period=3, date_form=2)
        double = _GlFacadeDouble(gl080.facade)
        storage = _storage(gl080, preset, a=0)
        with _driving(gl080, double):
            gl080._gl080_main(storage)

        assert preset.system_data_block.date_form == 2


def test_two_runs_with_the_same_arguments_write_the_same_rows() -> None:
    """Determinism, at the program level (R-6).

    Every date this program uses arrives through linkage - the text date in `to_day` and
    the binary run date on the system record - and the module imports no clock. So two
    runs of the same scenario write the same rows, and the assertion is a whole-object
    comparison of everything the two runs produced: the ordered verb log, both rewrite
    lists, the deletes, the flat archive rows and the mutated system record.

    A comparison of SUMMARIES would let a difference hide; this compares the observations
    themselves, and the archive rows are compared as dataclasses so that every field of
    every row takes part.
    """
    outcomes = []
    for _ in range(2):
        with _shipped_gl080() as gl080:
            system = _system(scycle=12, period=3, current_quarter=4, arch=_ARCHIVING)
            double = _GlFacadeDouble(
                gl080.facade,
                batches=[_batch_row(7, 12), _batch_row(8, 11)],
                postings=[
                    _posting_row(
                        7, 1, amount="10.00", vat_ac=3030, vat_amount="1.75",
                        vat_side="CR",
                    ),
                    _posting_row(7, 2, amount="20.00"),
                ],
                ledgers=[_ledger_row(1010, "5.00"), _ledger_row(2020, "-6.00")],
            )
            storage = _storage(gl080, system, a=0)
            with _driving(gl080, double):
                gl080._gl080_main(storage)

            outcomes.append(
                {
                    "calls": list(double.calls),
                    "ledger_rewrites": list(double.ledger_rewrites),
                    "batch_rewrites": list(double.batch_rewrites),
                    "posting_deletes": list(double.posting_deletes),
                    "archive": [
                        dataclasses.asdict(row) for row in storage.archive.rows
                    ],
                    "system": dataclasses.asdict(system),
                    "a": storage.a,
                    "y": storage.y,
                }
            )

    first, second = outcomes
    assert first == second
    #  And the run was not vacuous: it archived, deleted, stamped and posted.
    assert first["archive"]
    assert first["posting_deletes"]
    assert first["batch_rewrites"]
    assert first["ledger_rewrites"]
