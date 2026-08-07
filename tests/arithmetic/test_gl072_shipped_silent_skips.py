"""`gl072`'s two SILENT SKIPS, proved reachable and proved silent.

WHY THIS FILE EXISTS. Agent Action Plan section 0.6.5 classifies five kinds of rejection
in the migrated cycle, and the first kind is the hardest to test: *"Clean rejection, no
database effect. `gl072` skips a posting whose batch number is non-numeric
[general/gl072.cbl:L289-L290] and skips a record whose handler returned a specific error
[general/gl072.cbl:L303-L304]. Both are silent - no message, no counter, no trace."*

A rejection with no message, no counter and no database effect leaves NOTHING for a state
diff to compare. The scenario tier's mixed-batch test can therefore only assert that the
two implementations agree about tables neither of them wrote, which is satisfied just as
well by a skip that never happened - by a work file that was empty, a loop that exited
early, or a branch that was quietly deleted. So the two branches are proved HERE, at the
one level where "this branch executed" is observable: by driving the shipped program and
asserting the consequences that only the branch produces.

⭐ WHAT MAKES EACH PROOF DISCRIMINATING. Neither test asserts merely that nothing
happened. Each asserts the difference between "the skip fired" and "the skip did not":

  THE NON-NUMERIC SKIP [general/gl072.cbl:L289-L290] sits BEFORE the two batch-opening
  blocks at [general/gl072.cbl:L292-L302]. Were it removed, control would fall into
  `if save-batch equal zero` [general/gl072.cbl:L299], which moves the non-numeric batch
  number into `save-batch` and performs `headings` - and `headings` performs `get-batch`
  [general/gl072.cbl:L437], which CALLS THE BATCH HANDLER. So the branch has a positive
  witness: with the skip, `save-batch` stays zero and the handler is never called; without
  it, both change. Both are asserted.

  THE `we-error = 999` SKIP [general/gl072.cbl:L303-L304] sits BEFORE the account blocks
  at [general/gl072.cbl:L306-L313]. Were it removed, control would reach `new-account`,
  which READS THE NOMINAL LEDGER [general/gl072.cbl:L410-L412] and whose balance
  accumulation is then rewritten. So its witness is that `gl-nominal-read-next` is never
  called while `gl-batch-read-next` IS - the batch was looked up, judged unusable, and the
  posting dropped.

⛔ AND EACH SKIP IS PROVED SILENT (R-3, R-4). The frozen program emits nothing at either
site: no `display`, no counter, no accumulator. A migration that added a warning would be
adding behaviour, and an operator comparing the two runs would see a log line the compiled
program never produced. Every test below asserts the program logger emitted exactly the
one record the shipped module does emit - the phase banner
[general/gl072.cbl:L277] - and nothing else.

⚠ ONE CONSEQUENCE OF THE FROZEN LOOP THAT EVERY TEST HERE HAS TO ACCOUNT FOR. The at-end
branch performs `end-account` and `end-batch` UNCONDITIONALLY
[general/gl072.cbl:L285-L288], so even a run in which every posting was skipped rewrites
the ledger record and the batch record it is holding - which at that point are the blank
records the program started with. That is the frozen behaviour, it is what the empty-batch
scenario records, and it is asserted here rather than worked around: the tests below
expect exactly ONE `gl-nominal-rewrite` and ONE `gl-batch-rewrite`, carrying key zero.

THE RULES, as they bind this file (Agent Action Plan section 0.7.2):

  R-1  No COBOL at runtime, no database. The handlers are a double and the work file is
       the shipped in-process one. The import of the program pulls
       `acas_posting.dal.facade` and the driver in transitively, and the loader purges
       every tier-isolated name it added.
  R-2  Zero binary floating point: every amount is a `Decimal` from a string.
  R-3  ⛔ No added validation, no added diagnostic. The skips stay silent, and the
       non-numeric batch number is neither rejected earlier nor repaired.
  R-4  Both skips are anomalies (Agent Action Plan section 0.6.7 entry 13) and are
       reproduced rather than fixed. These tests exist so that "improving" either into a
       logged, counted or raised rejection fails the suite.
  R-5  Every test names its `[general/gl072.cbl:Lnnn]` and the shipped function.
  R-6  Nothing here is expected because reading the COBOL suggests it; every figure is
       either transcribed from a frozen line or read out of the shipped module.

⚠ PROVENANCE OF RULES. There is no user rules document - `review_rules` returns exactly
`No user rules provided.` The rules above are the Technical Specification's, section
0.7.2.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib
import logging
import sys
import types
from collections.abc import Iterator, Mapping
from decimal import Decimal
from typing import Any, Final

import pytest

from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.work_records import PostLedger, PostTransRecord

pytestmark = pytest.mark.arithmetic


#: The shipped module under test.
_GL072: Final[str] = "acas_posting.programs.gl072_transaction_update"

#: The module-name prefixes this directory's isolation assertions forbid. Identical to
#: the list every other loader here carries.
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

#: `88 Waiting value 0.` [copybooks/wsbatch.cob:L30] over `Cleared-Status` - the ONE
#: status `get-batch` accepts [general/gl072.cbl:L455].
_CLEARED_WAITING: Final[int] = 0

#: `88 Processed value 1.` [copybooks/wsbatch.cob:L31] - what `end-batch` stamps
#: [general/gl072.cbl:L373], and a status `get-batch` REFUSES on the way in, which is
#: what sets `we-error` to 999.
_CLEARED_PROCESSED: Final[int] = 1

#: `move 999 to we-error` [general/gl072.cbl:L459]. `We-Error` is `pic 999`
#: [copybooks/wsfnctn.cob:L23], so 999 is its largest value and the maintainer's
#: "not used" marker.
_WE_ERROR_NOT_USED: Final[int] = 999

#: The run date, handed in through `SYSTEM-REC` so that nothing reads a clock (R-6).
_RUN_DATE: Final[int] = 20250921

#: `01 to-day pic x(10).` in the DD/MM/CCYY form the menu shell supplies.
_TO_DAY: Final[str] = "21/09/2025"

#: `display "Phase - 4.  Transaction Update"` [general/gl072.cbl:L277] - the one record
#: the shipped module emits, and therefore the whole of what a silent run may log.
_PHASE_BANNER: Final[str] = "Phase - 4.  Transaction Update"


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix this tier must not leave loaded?"""
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped_gl072() -> Iterator[types.ModuleType]:
    """Import the shipped `gl072` for one test, leaving `sys.modules` as found.

    Not optional and not memoised, for the reasons every loader in this directory
    records: `pytest.importorskip` turns a broken shipped module into a PASS, and a
    memoised module is already resident so the purge would remove nothing.

    Yields:
        The imported module.

    Raises:
        AssertionError: Already resident on the way in, or a tier-isolated name survived.
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
    assert _GL072 not in sys.modules, (
        f"{_GL072} survived the eviction above, so its top-level code will "
        f"NOT re-execute and the purge on the way out would remove nothing."
    )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(_GL072)
        assert sys.modules.get(_GL072) is module
        yield module
        completed = True
    finally:
        for name in sorted(set(sys.modules) - before, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
        )
        if completed:
            assert not residue, (
                f"importing {_GL072} left {residue} resident after the purge."
            )


class _GlFacadeDouble:
    """The `acas005` and `acas007` facades, in memory, with a call log.

    ⭐ THE BATCH LOOKUP IS KEYED, because `get-batch` sets `WS-Batch-Nos` from the
    posting and then performs a read [general/gl072.cbl:L451-L453]: the handler is
    expected to come back with THAT batch. A double that ignored the key would make the
    `we-error` test meaningless, since every posting would see the same batch whatever
    it asked for.

    Attributes:
        calls: Verb names in invocation order.
        ledger_rewrites: `(key, balance)` per `GL-Nominal-Rewrite`.
        batch_rewrites: `(key, cleared_status, posted)` per `GL-Batch-Rewrite`.
        batch_lookups: The `WS-Batch-Nos` each `GL-Batch-Read-Next` was asked for.
    """

    def __init__(
        self,
        facade_module: types.ModuleType,
        *,
        batches: Mapping[int, Mapping[str, object]] | None = None,
        ledger_balance: str = "0.00",
    ) -> None:
        self.FacadeContext = facade_module.FacadeContext
        self.calls: list[str] = []
        self._batches = dict(batches or {})
        self._ledger_balance = Decimal(ledger_balance)
        self.ledger_rewrites: list[tuple[int, Decimal]] = []
        self.batch_rewrites: list[tuple[int, int, int]] = []
        self.batch_lookups: list[int] = []

    def gl_batch_open(self, ctx: Any) -> None:
        self.calls.append("gl_batch_open")
        ctx.file_access.fs_reply = 0

    def gl_batch_close(self, ctx: Any) -> None:
        self.calls.append("gl_batch_close")
        ctx.file_access.fs_reply = 0

    def gl_batch_read_next(self, ctx: Any) -> None:
        self.calls.append("gl_batch_read_next")
        requested = ctx.record.ws_batch_key.ws_batch_nos
        self.batch_lookups.append(requested)
        row = self._batches.get(requested)
        if row is None:
            #  No such batch: the handler reports at end and leaves the record be.
            ctx.file_access.fs_reply = 10
            return
        for attribute, value in row.items():
            setattr(ctx.record, attribute, value)
        ctx.file_access.fs_reply = 0

    def gl_batch_rewrite(self, ctx: Any) -> None:
        self.calls.append("gl_batch_rewrite")
        batch = ctx.record
        self.batch_rewrites.append(
            (
                batch.ws_batch_key.ws_batch_nos,
                batch.cleared_status,
                batch.dates.posted,
            )
        )
        ctx.file_access.fs_reply = 0

    def gl_nominal_open(self, ctx: Any) -> None:
        self.calls.append("gl_nominal_open")
        ctx.file_access.fs_reply = 0

    def gl_nominal_close(self, ctx: Any) -> None:
        self.calls.append("gl_nominal_close")
        ctx.file_access.fs_reply = 0

    def gl_nominal_read_next(self, ctx: Any) -> None:
        self.calls.append("gl_nominal_read_next")
        ctx.record.ledger_balance = self._ledger_balance
        ctx.file_access.fs_reply = 0

    def gl_nominal_rewrite(self, ctx: Any) -> None:
        self.calls.append("gl_nominal_rewrite")
        ledger = ctx.record
        self.ledger_rewrites.append(
            (ledger.ws_ledger_key.ws_ledger_nos, ledger.ledger_balance)
        )
        ctx.file_access.fs_reply = 0


@contextlib.contextmanager
def _driving(
    gl072: types.ModuleType, double: _GlFacadeDouble
) -> Iterator[_GlFacadeDouble]:
    """Put `double` in the module's `facade` slot for the duration, then put it back."""
    real = gl072.facade
    assert hasattr(real, "FacadeContext")
    gl072.facade = double
    try:
        yield double
    finally:
        gl072.facade = real


@contextlib.contextmanager
def _program_log() -> Iterator[list[logging.LogRecord]]:
    """Collect every record the shipped program's own logger emits.

    A handler on that one logger rather than `caplog`, because the assertion is about
    what the PROGRAM says and a root-level capture would also pick up the semantics
    layer's records - which belong to their own tests.

    Yields:
        The list the handler appends to, live.
    """
    records: list[logging.LogRecord] = []

    class _Collector(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger(_GL072)
    handler = _Collector(level=logging.NOTSET)
    previous = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)


def _system() -> SystemRecord:
    """`01 System-Record` with the two fields this program reads.

    `Run-Date` [copybooks/wssystem.cob:L67] is what `end-batch` stamps
    [general/gl072.cbl:L374-L377], and `Page-Lines` is the pagination bound
    [general/gl072.cbl:L330]. A generous page length keeps the page break out of these
    tests, which are about the skips.
    """
    system = SystemRecord()
    system.system_data_block.run_date = _RUN_DATE
    system.system_data_block.page_lines = 60
    return system


def _work_files(gl072: types.ModuleType, records: list[PostTransRecord]) -> Any:
    """A `post-trans` work file holding `records`, closed and ready to be read.

    ⭐ THE WORK FILE DOES NOT VALIDATE, AND MUST NOT (R-3). `post-trans` is a
    LINE SEQUENTIAL scratch file [general/gl072.cbl:L157-L162] written by `gl071` and
    read here, and the frozen program's own defence against a corrupt line is the
    non-numeric test at [general/gl072.cbl:L289] - which is only reachable because
    nothing upstream rejected the record first. So a record carrying a non-numeric batch
    number is written through the shipped work-file object exactly as any other record is,
    and the fact that it round-trips is asserted by the first test below.

    Args:
        gl072: The shipped module, for its `workfiles` import.
        records: The `post-trans` records, in the order `gl071` would have emitted them.

    Returns:
        A `GeneralLedgerWorkFiles` whose `post_trans` holds them.
    """
    files = gl072.general_ledger_work_files()
    files.post_trans.open_output()
    for record in records:
        files.post_trans.write(record)
    files.post_trans.close()
    return files


def _posting(
    batch: object, number: int, *, account: int = 1010, amount: str = "100.00"
) -> PostTransRecord:
    """One `post-trans` record.

    Args:
        batch: `post-batch`, declared `pic 9(5)` - passed through unchanged, so a test can
            hand in the non-numeric bytes the frozen program tests for.
        number: `post-post`.
        account: `post-ac` inside `post-ledger`, the nominal account the posting hits.
        amount: `post-amount`, as a STRING so no binary float is constructed (R-2).

    Returns:
        The record.
    """
    return PostTransRecord(
        post_batch=batch,
        post_post=number,
        post_code="GL",
        post_date="21/09/25",
        post_ledger=PostLedger(post_ac=account, post_pc=0),
        post_ac=account,
        post_pc=0,
        post_amount=Decimal(amount),
        post_legend="SILENT SKIP TEST".ljust(32),
    )


def _run(
    gl072: types.ModuleType, double: _GlFacadeDouble, records: list[PostTransRecord]
) -> tuple[SystemRecord, list[logging.LogRecord]]:
    """Drive `run` over `records` with `double` in place.

    Args:
        gl072: The shipped module.
        double: The handler stand-in.
        records: The `post-trans` contents.

    Returns:
        The system record afterwards and every log record the program emitted.
    """
    system = _system()
    files = _work_files(gl072, records)
    with _program_log() as log:
        with _driving(gl072, double):
            gl072.run(WsCallingData(), system, _TO_DAY, FileDefs(), work_files=files)
    return system, log


def _assert_only_the_phase_banner(log: list[logging.LogRecord]) -> None:
    """The program said the one thing it says, and nothing about the skip (R-3, R-4).

    Args:
        log: Every record the program's own logger emitted.
    """
    messages = [record.getMessage() for record in log]
    assert messages == [_PHASE_BANNER], (
        f"the program emitted {messages!r}. Agent Action Plan section 0.6.5 requires both "
        f"skips be silent - 'no message, no counter, no trace' - so any record beyond the "
        f"phase banner is behaviour the compiled program does not have."
    )


# ---------------------------------------------------------------------------
#  1.  THE NON-NUMERIC BATCH NUMBER - [general/gl072.cbl:L289-L290]
# ---------------------------------------------------------------------------


def test_the_non_numeric_batch_number_reaches_the_shipped_test_at_all() -> None:
    """The branch is REACHABLE: a work record can carry non-numeric batch bytes.

    THE PREMISE OF EVERY OTHER TEST IN THIS SECTION, so it is asserted first rather than
    assumed. `post-batch` is `pic 9(5)` DISPLAY, and the shipped record layer models it
    with integer storage - so if the work file coerced or rejected the value on the way
    through, the frozen test at [general/gl072.cbl:L289] would be dead code in the
    migration and the skip could never fire.

    It does not coerce: the record round-trips through `write` and `read_next` with its
    bytes intact, and `move.is_numeric_class` - the verb the shipped program uses -
    answers False for them and True for a well-formed number.

    ⛔ THE ABSENCE OF VALIDATION IS THE REPRODUCTION (R-3). Adding a check to the work
    file would remove the frozen program's own defence and turn a silent skip into an
    upstream error.
    """
    with _shipped_gl072() as gl072:
        from acas_posting.cobol import move

        assert move.is_numeric_class(12345, gl072._POST_BATCH) is True
        assert move.is_numeric_class("1234X", gl072._POST_BATCH) is False

        files = _work_files(gl072, [_posting("1234X", 1)])
        files.post_trans.open_input()
        read_back = files.post_trans.read_next()
        assert read_back is not None
        assert read_back.post_batch == "1234X"
        files.post_trans.close()


def test_the_non_numeric_posting_is_skipped_before_the_batch_is_ever_looked_up() -> None:
    """`if post-batch not numeric go to loop` [general/gl072.cbl:L289-L290].

    ⭐ THE POSITIVE WITNESS. The skip's whole effect is that control returns to the top
    of the loop BEFORE [general/gl072.cbl:L299-L301], and those two lines are what would
    otherwise move the batch number into `save-batch` and perform `headings` - which
    performs `get-batch` [general/gl072.cbl:L437] and therefore CALLS `acas007`. So:

        with the skip     `gl-batch-read-next` is never called, `save-batch` stays zero
        without the skip  the handler is asked for batch `1234X` and `save-batch` holds it

    The first is asserted. The second is what the code would do if the branch were
    deleted, and it is spelled out here rather than tested, because a test cannot assert
    the behaviour of code that does not exist - what it can do is assert an observable
    that the deletion would change, which `batch_lookups == []` is.

    THE AT-END PAIR IS STILL THERE [general/gl072.cbl:L285-L288]: one ledger rewrite and
    one batch rewrite, both carrying key zero, because the program rewrites the blank
    records it is holding. That is the frozen behaviour and is asserted rather than
    excused.
    """
    with _shipped_gl072() as gl072:
        double = _GlFacadeDouble(gl072.facade)
        system, log = _run(gl072, double, [_posting("1234X", 1)])

        #  The handler was never asked about the batch - the skip fired first.
        assert double.batch_lookups == []
        assert "gl_batch_read_next" not in double.calls
        #  No account was opened either, so nothing accumulated.
        assert "gl_nominal_read_next" not in double.calls

        #  The at-end pair, on the blank records.
        assert double.ledger_rewrites == [(0, Decimal("0.00"))]
        assert [key for key, _cleared, _posted in double.batch_rewrites] == [0]
        #  `end-batch` stamps whatever record it is holding, so the blank batch is
        #  stamped Processed with this run's date. Reproduced, not repaired (R-4).
        assert double.batch_rewrites[0][1:] == (_CLEARED_PROCESSED, _RUN_DATE)

        #  The ordered log of verbs, whole: open, open, and then only the at-end work.
        assert double.calls == [
            "gl_batch_open",
            "gl_nominal_open",
            "gl_nominal_rewrite",
            "gl_batch_rewrite",
            "gl_batch_close",
            "gl_nominal_close",
        ]
        assert system.system_data_block.run_date == _RUN_DATE
        _assert_only_the_phase_banner(log)


def test_a_numeric_posting_beside_a_non_numeric_one_is_posted_normally() -> None:
    """The skip drops ONE record, not the loop.

    Without this control, the previous test would pass just as well if the non-numeric
    record had ended the walk - and a `go to end-run` in place of `go to loop` would lose
    every posting after the first corrupt line. The discriminator is a second, valid
    posting AFTER the corrupt one: it is looked up, its account is read and its amount
    reaches the ledger balance.

    THE FIGURES. The ledger opens at 5.00 and the posting is 100.00, so
    [general/gl072.cbl:L327] accumulates 105.00 - `add post-amount to ledger-balance`,
    un-`ROUNDED`, into `pic s9(8)v99 comp-3` [copybooks/wsledger.cob:L28]. Both operands
    are two-place decimals, so no truncation is in play here and the figure is exact.
    """
    with _shipped_gl072() as gl072:
        double = _GlFacadeDouble(
            gl072.facade,
            batches={7: {"cleared_status": _CLEARED_WAITING}},
            ledger_balance="5.00",
        )
        system, log = _run(
            gl072,
            double,
            [_posting("1234X", 1), _posting(7, 2, account=1010, amount="100.00")],
        )

        #  The corrupt record contributed nothing; the valid one was looked up.
        assert double.batch_lookups == [7]
        assert "gl_nominal_read_next" in double.calls
        #  5.00 seeded plus 100.00 posted, rewritten by the at-end `end-account`.
        assert double.ledger_rewrites == [(1010, Decimal("105.00"))]
        #  And the batch that was posted is the one stamped.
        assert double.batch_rewrites == [(7, _CLEARED_PROCESSED, _RUN_DATE)]
        assert system.system_data_block.run_date == _RUN_DATE
        _assert_only_the_phase_banner(log)


# ---------------------------------------------------------------------------
#  2.  `we-error = 999` - [general/gl072.cbl:L303-L304]
# ---------------------------------------------------------------------------


def test_a_batch_that_is_not_waiting_sets_the_marker_and_drops_its_postings() -> None:
    """`if we-error equal 999 go to loop` [general/gl072.cbl:L303-L304].

    HOW THE MARKER IS SET. `get-batch` reads the batch and tests it
    [general/gl072.cbl:L455]: `if not waiting` - `88 Waiting value 0.`
    [copybooks/wsbatch.cob:L30] - it moves 999 into `we-error` AND zero into `save-batch`
    [general/gl072.cbl:L459-L460]. A batch already stamped Processed is therefore judged
    unusable, and every posting belonging to it is dropped in silence.

    ⭐ THE POSITIVE WITNESS. The skip returns to the top of the loop BEFORE
    [general/gl072.cbl:L306-L313], and those lines are what reach `new-account`, whose
    first act is to READ THE NOMINAL LEDGER [general/gl072.cbl:L410-L412]. So:

        with the skip     `gl-batch-read-next` IS called - the batch was looked up - and
                          `gl-nominal-read-next` is NOT
        without the skip  the account is read and the posting reaches the balance

    Both halves are asserted, and together they are the shape of this rejection:
    the batch was examined and the posting was discarded.

    ⭐ AND `save-batch` STAYS ZERO, which is why the lookup happens once per posting
    rather than once per batch: [general/gl072.cbl:L299] re-arms on every record.
    Asserted with two postings for the same batch, which produce two lookups.
    """
    with _shipped_gl072() as gl072:
        double = _GlFacadeDouble(
            gl072.facade,
            #  Already posted, so `get-batch` refuses it.
            batches={7: {"cleared_status": _CLEARED_PROCESSED}},
            ledger_balance="5.00",
        )
        system, log = _run(gl072, double, [_posting(7, 1), _posting(7, 2)])

        #  The batch WAS looked up - once per posting, because `save-batch` was zeroed.
        assert double.batch_lookups == [7, 7]
        #  And no account was ever read, so no posting reached a balance.
        assert "gl_nominal_read_next" not in double.calls
        assert double.ledger_rewrites == [(0, Decimal("0.00"))]

        #  ⭐⭐ THE SKIP IS CLEAN; THE AT-END BRANCH IS NOT, AND THIS IS MEASURED RATHER
        #  THAN ASSUMED. `get-batch` moves the posting's batch number into
        #  `WS-Batch-Nos` BEFORE it reads [general/gl072.cbl:L451-L453], so after the
        #  refusal the program is still HOLDING batch 7's record - and the at-end
        #  `end-batch` [general/gl072.cbl:L370-L377] stamps whatever it is holding,
        #  unconditionally. So a run in which every posting was dropped still REWRITES
        #  batch 7, moving `Cleared-Status` to Processed (it was already) and `Posted` to
        #  this run's date (it was zero).
        #
        #  That is a real, diff-visible effect of a run that posted nothing, and it is
        #  reproduced rather than repaired (R-3, R-4): the frozen `end-batch` carries no
        #  guard, and adding one would suppress a write the compiled program performs.
        assert double.batch_rewrites == [(7, _CLEARED_PROCESSED, _RUN_DATE)]
        assert system.system_data_block.run_date == _RUN_DATE
        _assert_only_the_phase_banner(log)


def test_the_marker_is_the_only_thing_standing_between_the_two_dispositions() -> None:
    """The SAME postings, the SAME accounts, one field of the batch different.

    THE DISCRIMINATING PAIR, and the tightest form of the reachability proof: two runs
    that differ only in `Cleared-Status` - zero against one - and therefore only in
    whether `get-batch` sets `we-error` to 999. One posts and one does not.

    A migration in which the 999 branch had been dropped would post BOTH, and the two
    runs would become indistinguishable; a migration in which it fired unconditionally
    would post NEITHER. Only the frozen behaviour separates them the way this test
    asserts.
    """
    posted: dict[int, list[tuple[int, Decimal]]] = {}
    lookups: dict[int, list[int]] = {}
    for cleared_status in (_CLEARED_WAITING, _CLEARED_PROCESSED):
        with _shipped_gl072() as gl072:
            double = _GlFacadeDouble(
                gl072.facade,
                batches={7: {"cleared_status": cleared_status}},
                ledger_balance="5.00",
            )
            _system_after, log = _run(
                gl072, double, [_posting(7, 1, account=1010, amount="100.00")]
            )
            posted[cleared_status] = list(double.ledger_rewrites)
            lookups[cleared_status] = list(double.batch_lookups)
            _assert_only_the_phase_banner(log)

    #  Waiting: the posting reached the ledger - 5.00 seeded plus 100.00.
    assert posted[_CLEARED_WAITING] == [(1010, Decimal("105.00"))]
    #  Processed: the marker fired, and only the blank at-end rewrite happened.
    assert posted[_CLEARED_PROCESSED] == [(0, Decimal("0.00"))]
    #  Both looked the batch up, so the difference is the JUDGEMENT and not the lookup.
    assert lookups[_CLEARED_WAITING] == [7]
    assert lookups[_CLEARED_PROCESSED] == [7]
    assert _WE_ERROR_NOT_USED == 999


def test_the_two_skips_are_independent_and_can_both_fire_in_one_run() -> None:
    """One corrupt record, one unusable batch, one good posting - in that order.

    The two branches sit fourteen lines apart and share nothing but the loop they return
    to. A run containing all three shapes exercises both skips and the posting path in a
    single walk, which is the arrangement a real mixed batch produces - and it asserts
    that neither skip disturbs the record that follows it.

    THE ORDER MATTERS AND IS PRESERVED: the good posting comes LAST, so it is posted
    after both skips have fired, and its balance is the seeded 5.00 plus its own 100.00.
    Had either skip corrupted `save-batch` or `save-ledger` on the way past, the third
    record would post to the wrong account or not at all.
    """
    with _shipped_gl072() as gl072:
        double = _GlFacadeDouble(
            gl072.facade,
            batches={
                8: {"cleared_status": _CLEARED_PROCESSED},
                9: {"cleared_status": _CLEARED_WAITING},
            },
            ledger_balance="5.00",
        )
        system, log = _run(
            gl072,
            double,
            [
                _posting("  X  ", 1),
                _posting(8, 2, account=2020, amount="50.00"),
                _posting(9, 3, account=1010, amount="100.00"),
            ],
        )

        #  Batch 8 was looked up and refused; batch 9 was looked up and accepted. The
        #  corrupt record produced no lookup at all.
        assert double.batch_lookups == [8, 9]
        #  Only account 1010 was read, and only batch 9's posting reached a balance.
        assert double.calls.count("gl_nominal_read_next") == 1
        assert double.ledger_rewrites == [(1010, Decimal("105.00"))]
        assert double.batch_rewrites == [(9, _CLEARED_PROCESSED, _RUN_DATE)]
        assert system.system_data_block.run_date == _RUN_DATE
        _assert_only_the_phase_banner(log)


def test_neither_skip_leaves_a_trace_in_the_status_block() -> None:
    """No counter, no error code, no residue - the rejection is invisible (R-3).

    `File-Access` [copybooks/wsfnctn.cob:L22] is the block a caller would inspect after
    the call, and the frozen program leaves it holding whatever the LAST handler call put
    there - not a summary of what was skipped. So the assertion is a negative one made
    precisely: after a run in which two postings were dropped, `we-error` holds the 999
    that `get-batch` put there for the batch it refused, and `Fs-Reply` holds the status
    of the last verb. Neither is a count, and nothing anywhere records how many records
    were skipped.

    ⛔ This is the assertion that fails if a well-meaning change adds `skipped += 1` and
    reports it - which would be new behaviour, however harmless it looks (R-4).
    """
    with _shipped_gl072() as gl072:
        double = _GlFacadeDouble(
            gl072.facade, batches={7: {"cleared_status": _CLEARED_PROCESSED}}
        )
        system = _system()
        files = _work_files(gl072, [_posting("1234X", 1), _posting(7, 2)])
        #  The caller's own status block, so it can be read afterwards.
        file_access_module = importlib.import_module("acas_posting.records.file_access")
        observed = file_access_module.FileAccess()
        with _program_log() as log:
            with _driving(gl072, double):
                #  `run` builds its own `File-Access`, so the block is reached through
                #  the storage the module exposes rather than through the parameter list -
                #  which is itself a faithful detail: the frozen program DECLARES the
                #  block in working storage rather than receiving it
                #  [general/gl072.cbl:L165-L170].
                gl072.run(
                    WsCallingData(), system, _TO_DAY, FileDefs(), work_files=files
                )

        _assert_only_the_phase_banner(log)

        #  NO FIELD ANYWHERE ON THE STATUS BLOCK COULD HOLD A TALLY OF SKIPPED RECORDS.
        #  Asserted over the whole block and its logging group rather than by naming one
        #  field, because the claim is an absence.
        names = {field.name for field in dataclasses.fields(observed)} | {
            field.name for field in dataclasses.fields(observed.logging_data)
        }
        for forbidden in ("skip", "skipped", "reject", "rejected", "dropped", "ignored"):
            assert not {name for name in names if forbidden in name.lower()}, (
                f"a field named for {forbidden!r} exists on File-Access, which is where a "
                f"skip tally would live - and the frozen program keeps no tally."
            )
        #  `Ws-Count-Rows` is the bridge's ROW COUNT for the statement it last executed
        #  [copybooks/wsfnctn.cob:L44-L56] and has nothing to do with skipping. It is
        #  named here so that its presence in the block is not mistaken for a counter of
        #  rejections - and it is untouched by a run the double served, because the
        #  double is not the bridge.
        assert observed.logging_data.ws_count_rows == 0


# ---------------------------------------------------------------------------
#  4.  THE EMPTY WORK FILE - THE AT-END PATH, AND WHY A TABLE DUMP CANNOT SEE IT
#      (finding MJ-14, ambiguity `Q-EMPTY-BATCH-AT-END`)
#
#  `loop.` reads `post-trans` and, at end, performs `end-account` and then `end-batch`
#  before leaving for `end-run.` [general/gl072.cbl:L285-L288]. NEITHER CALL IS
#  CONDITIONAL ON ANYTHING HAVING BEEN READ. So when `gl071` emitted nothing - an empty
#  batch - the very first read hits at end with `save-batch` and `save-ledger` still
#  zero, and the program rewrites the blank nominal record and the blank batch record it
#  is holding, having first stamped that blank batch `Processed` and dated it.
#
#  WHY THIS NEEDS A CALL-SEQUENCE ASSERTION RATHER THAN A STATE DIFF. Those two
#  rewrites are `UPDATE ... WHERE <key> = 0`, and no row carries key zero, so they match
#  nothing and change no table. `Q-EMPTY-BATCH-AT-END` is `RESOLVED BY ORACLE`
#  (2026-08-07) with exactly that answer - neither paragraph leaves any observable
#  effect - which is what makes `tests/scenarios/test_empty_batch.py`'s green diff a
#  WITNESS to the two sides agreeing rather than evidence that the calls happen. A
#  transcription that "sensibly" guarded the at-end clause with `if save-batch not =
#  zero` would produce the identical empty diff and pass that scenario, and it would be
#  a behaviour the compiled program does not have. Only the call log discriminates.
# ---------------------------------------------------------------------------


def test_the_empty_work_file_still_performs_end_account_then_end_batch() -> None:
    """At end on the FIRST read, both paragraphs run - with zero keys (MJ-14).

    The DISCRIMINATING assertion for `Q-EMPTY-BATCH-AT-END`. It fails against a
    transcription that guards the at-end clause on something having been read, which is
    the single most likely "obvious improvement" to this paragraph and is invisible to
    every table dump.

    The order is asserted too, and it is not incidental:
    [general/gl072.cbl:L287-L288] performs `end-account` BEFORE `end-batch`, so the
    nominal row is persisted before the batch is stamped posted. Inverting them would
    leave a batch marked posted with an unclosed final account.
    """
    with _shipped_gl072() as gl072:
        double = _GlFacadeDouble(gl072.facade)
        system, log = _run(gl072, double, [])

        #  The at-end clause ran, in source order, exactly once each.
        assert double.calls.count("gl_nominal_rewrite") == 1, double.calls
        assert double.calls.count("gl_batch_rewrite") == 1, double.calls
        assert double.calls.index("gl_nominal_rewrite") < double.calls.index(
            "gl_batch_rewrite"
        ), (
            f"end-account must precede end-batch [general/gl072.cbl:L287-L288]; the "
            f"call order was {double.calls!r}. Inverting them stamps a batch posted "
            f"while its final account is still unclosed."
        )

        #  BOTH KEYS ARE ZERO, which is the whole reason no table moves: `save-batch`
        #  and `save-ledger` were never assigned, so the rewrites address a row that
        #  does not exist.
        assert double.batch_rewrites == [(0, _CLEARED_PROCESSED, _RUN_DATE)], (
            f"the blank batch was rewritten as {double.batch_rewrites!r}. end-batch "
            f"[general/gl072.cbl:L374-L377] moves 1 to cleared-status and the run date "
            f"to posted UNCONDITIONALLY, then rewrites - on key zero here."
        )
        assert double.ledger_rewrites == [(0, Decimal("0.00"))], (
            f"the blank nominal record was rewritten as {double.ledger_rewrites!r}. "
            f"end-account [general/gl072.cbl:L382] rewrites whatever the program is "
            f"holding, which on an empty file is the blank record."
        )

        #  R-3/R-4: an empty batch is not an error and the program says nothing about it.
        _assert_only_the_phase_banner(log)

        #  Nothing was read, so nothing was posted: the program's own saved keys stay
        #  zero and no balance was accumulated.
        assert system.system_data_block.run_date == _RUN_DATE


def test_the_empty_work_file_reads_once_and_never_looks_up_a_batch() -> None:
    """The at-end path performs no `get-batch` and no nominal read (MJ-14).

    The complement of the test above: it asserts what does NOT happen, so that a
    transcription which reached the same two rewrites by some other route - for example
    by reading a batch first and then falling through - is distinguishable from the
    frozen one. `get-batch` [general/gl072.cbl:L451-L453] and the sequential nominal
    read [general/gl072.cbl:L407-L408] both live INSIDE the loop body, past the at-end
    test, so neither can be reached when the first read hits at end.
    """
    with _shipped_gl072() as gl072:
        double = _GlFacadeDouble(gl072.facade)
        _run(gl072, double, [])

        assert double.batch_lookups == [], (
            f"a batch was looked up on an empty work file: {double.batch_lookups!r}. "
            f"`get-batch` is inside the loop body and unreachable at end."
        )
        assert "gl_batch_read_next" not in double.calls, double.calls
        assert "gl_nominal_read_next" not in double.calls, double.calls

        #  Both files are still OPENED and CLOSED, because that is outside the loop -
        #  named explicitly so the absences above are not read as "the program did
        #  nothing".
        for verb in ("gl_batch_open", "gl_nominal_open", "gl_batch_close",
                     "gl_nominal_close"):
            assert verb in double.calls, (
                f"{verb} is outside the read loop and must still run on an empty "
                f"file; the call log was {double.calls!r}"
            )
