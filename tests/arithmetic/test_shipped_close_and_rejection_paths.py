"""THE TWO BEHAVIOURS A TABLE DUMP CANNOT SEE, LOCKED BY CALL SEQUENCE INSTEAD.

Findings MJ-07 and MJ-11. Both are anomaly locks rule R-4 requires, and neither can be
held by a state comparison, for the same structural reason: the behaviour under test is
a call that changes no row.

  * ANOMALY A-1, `[sales/sl060.cbl:L1172-L1178]` - the missing terminating period nests
    `GL-Posting-Close` inside `if IRS-Used OR IRS-Both-Used`, so in PURE GENERAL LEDGER
    mode the posting file is never closed. A CLOSE writes nothing. Adding the missing
    period - the single most likely well-meaning correction to that paragraph, and the
    likeliest slip in any fresh translation of it - changes which verbs are performed
    and changes NO TABLE. `tests/scenarios/test_clean_batch_post_sl.py` compares
    `GLPOSTING-REC` on both sides and passes either way, which makes it a witness that
    the two implementations agree rather than a lock on A-1.

  * ANOMALY A-4's SIBLING PATH, `[irs/irs030.cbl:L1630-L1634]` - the IR032 clean
    rejection. When the DEBIT account is missing the program reports and loops, writing
    no nominal row and no posting row. Its whole signature is an ABSENCE, and an absence
    is invisible in a diff of two runs that both produce it: a transcription that
    aborted the run instead of continuing, or that committed the debit anyway, is
    indistinguishable from the frozen one by any comparison of end state on the
    fixture this scenario seeds.

WHAT THIS FILE THEREFORE DOES. It drives the SHIPPED paragraphs - not a transcription of
them - with a recording stand-in in the module's `facade` slot, and asserts the sequence
of verbs performed. That is the observable the frozen behaviour actually differs in, and
it is the only one that discriminates. Each lock below was verified to FAIL against the
specific wrong implementation it exists to catch.

NOTHING HERE ASSERTS A FIGURE THE ORACLE HAS NOT ARBITRATED, and nothing here repairs
anything. A-1 is asserted in its DEFECTIVE form: the assertion is that in pure General
Ledger mode `gl_posting_close` is NOT performed. Rule R-4 is explicit - "a defect
reproduced is correct; a defect fixed is a failure" - so this file turns RED if the
period is added, which is the entire point of it.

INFRASTRUCTURE: NONE. No Docker, no MariaDB, no GnuCOBOL and no database connection.
The facade is replaced before any verb runs, so no handler and no driver is reached; the
only prerequisite is `data_dictionary/acas_posting_dictionary.json`, which the record
layer loads for its descriptors.

Agent Action Plan references: section 0.6.7 entries A-1 and A-4; section 0.6.5 on
rejection paths and their database effect; section 0.4.3, which permits this tier
`cobol` and `records` and requires a program import to be deferred into function scope.
"""

from __future__ import annotations

import contextlib
import importlib
import logging
import sys
import types
from collections.abc import Iterator, Mapping
from decimal import Decimal
from typing import Any, Final

import pytest

pytestmark = pytest.mark.arithmetic


#: The dotted names this file drives. Strings rather than imports, so nothing crosses
#: the tier boundary at COLLECTION time - Agent Action Plan section 0.4.3, and the
#: property `test_no_arithmetic_module_imports_a_program_or_dal_at_module_level` holds.
_SL060: Final[str] = "acas_posting.programs.sl060_invoice_posting"
_IRS030: Final[str] = "acas_posting.programs.irs030_posting"


#: Prefixes this tier must not leave resident, copied from the sibling shipped-paragraph
#: files so that one file's import cannot make another's freshness claim vacuous.
_TIER_ISOLATION_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
    "harness",
    "mysql",
    "numpy",
    "pandas",
    "sqlalchemy",
)


#: `to-day pic x(10)` in DD/MM/CCYY form, pinned so two runs are byte-identical.
_TO_DAY: Final[str] = "21/09/2025"

#: `88 IRS-Used value "Y".` and `88 IRS-Both-Used value "B".`
#: [copybooks/wssystem.cob:L179-L181]. The third state is the LITERAL SPACE the field is
#: declared `pic x` for, and it is what "pure General Ledger mode" means here - not the
#: absence of a value and not a token `N`, which the switch has no value for.
_IRS_USED: Final[str] = "Y"
_IRS_BOTH_USED: Final[str] = "B"
_IRS_NEITHER: Final[str] = " "

#: `88 G-L value 1.` on `07 Level-1 pic 9.` [copybooks/wssystem.cob:L84-L85]. NOT on the
#: fan-out switch: pure General Ledger mode is the TWO-FIELD statement
#: `Level-1 = 1` AND `IRS-Instead = space`, which is exactly what makes A-1 observable.
_LEVEL_1_GENERAL_LEDGER: Final[int] = 1
_LEVEL_1_NOT_GENERAL_LEDGER: Final[int] = 0

#: `if we-error = 2` [irs/irs030.cbl:L1630] - the handler's "record not found". The
#: frozen test is EQUALITY with 2 and is deliberately not widened to "not = zero".
_WE_ERROR_RECORD_NOT_FOUND: Final[int] = 2
_WE_ERROR_SUCCESS: Final[int] = 0

#: `IR032` [irs/irs030.cbl:L1631] - the message identifier the clean rejection reports.
_IR032: Final[str] = "IR032"


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix this tier must not leave loaded?

    Args:
        name: A `sys.modules` key.

    Returns:
        Whether it is tier-isolated.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped(dotted_name: str) -> Iterator[types.ModuleType]:
    """Import a shipped program FOR REAL for one test, leaving `sys.modules` as found.

    NOT `pytest.importorskip`. A shipped module that cannot be imported is a FAILURE,
    not a skip: `mysql-connector-python==26.7.0` is a hard `requirements.txt` pin, so an
    installed tree always has it, and an anomaly lock that can vanish into a skip line
    is not a lock.

    NOT memoised. Eviction first, so the import really re-executes the module's
    top-level code and the purge afterwards really removes what it added.

    Args:
        dotted_name: The importable name.

    Yields:
        The imported module.

    Raises:
        AssertionError: The name survived the eviction, or residue survived the purge.
        ImportError: The module could not be imported. Deliberately not a skip.
    """
    for resident in sorted(
        (name for name in sys.modules if _is_tier_isolated_name(name)), reverse=True
    ):
        del sys.modules[resident]
    assert dotted_name not in sys.modules, (
        f"{dotted_name} survived the eviction, so its top-level code will not "
        f"re-execute and the purge below would remove nothing."
    )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(dotted_name)
        assert sys.modules.get(dotted_name) is module
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
            assert not residue, f"{dotted_name} left {residue} resident after the purge."


@contextlib.contextmanager
def _driving(module: types.ModuleType, double: object) -> Iterator[None]:
    """Put `double` in `module`'s `facade` slot for the duration, then put it back.

    Args:
        module: The shipped program module.
        double: The recording stand-in. It must publish `FacadeContext`, because the
            program builds its contexts through the same module attribute.

    Yields:
        Nothing; the block runs with the double installed.
    """
    real = module.facade
    assert hasattr(real, "FacadeContext")
    assert hasattr(double, "FacadeContext")
    module.facade = double
    try:
        yield
    finally:
        module.facade = real


@contextlib.contextmanager
def _program_log(logger_name: str) -> Iterator[list[logging.LogRecord]]:
    """Collect every record ONE shipped program's own logger emits.

    A handler on that one logger rather than `caplog`, so the semantics layer's records
    - which belong to their own tests - cannot be mistaken for the program's.

    Args:
        logger_name: The program module's dotted name, which is its logger name.

    Yields:
        The records, in emission order.
    """
    records: list[logging.LogRecord] = []

    class _Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger(logger_name)
    handler = _Collect()
    previous = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)


# ---------------------------------------------------------------------------
#  1.  ANOMALY A-1 - THE NESTED POSTING CLOSE IN `sl060`   (finding MJ-07)
#
#  [sales/sl060.cbl] `ca000-BL-Close section.` opens at L1158. The four lines that
#  matter, verbatim:
#
#      L1174       perform  GL-Batch-Close.                *>  close Batch-file.
#      L1175       if       IRS-Used OR IRS-Both-Used
#      L1176                perform SPL-Posting-Close      *>  close irs-post-file
#      L1177       if       IRS-Both-Used or G-L
#      L1178                perform GL-Posting-Close.      *>  close posting-file.
#
#  L1176 carries NO terminating period, so L1177's IF is NESTED INSIDE L1175's and the
#  single period at the end of L1178 closes BOTH. `GL-Posting-Close` therefore runs only
#  when
#
#      (IRS-Used OR IRS-Both-Used)  AND  (IRS-Both-Used OR G-L)
#
#  and in pure General Ledger mode the OUTER test is false, so it never runs at all.
#  The three sibling sites all HAVE the period - [purchase/pl060.cbl:L1031],
#  [sales/sl100.cbl:L694], [purchase/pl100.cbl:L675] - which is what makes A-1 an
#  accident of transcription rather than a house idiom.
#
#  A truth table over the two fields is the discriminating observable, and there is no
#  other: closing a file writes nothing.
# ---------------------------------------------------------------------------


class _Sl060CloseDouble:
    """The four facade verbs `ca000-BL-Close` performs, with a call log.

    Attributes:
        calls: Verb names in invocation order.
    """

    def __init__(self, facade_module: types.ModuleType) -> None:
        self.FacadeContext = facade_module.FacadeContext
        self.calls: list[str] = []

    def _served(self, verb: str, ctx: Any) -> None:
        self.calls.append(verb)
        #  Every verb reports success, so the fs-reply diagnostic at
        #  [sales/sl060.cbl:L1162-L1171] stays out of these tests: it is a DISPLAY with
        #  no control transfer and no table effect, and its own behaviour is not what
        #  A-1 is about.
        ctx.file_access.fs_reply = 0

    def gl_batch_write(self, ctx: Any) -> None:
        self._served("gl_batch_write", ctx)

    def gl_batch_close(self, ctx: Any) -> None:
        self._served("gl_batch_close", ctx)

    def spl_posting_close(self, ctx: Any) -> None:
        self._served("spl_posting_close", ctx)

    def gl_posting_close(self, ctx: Any) -> None:
        self._served("gl_posting_close", ctx)


def _sl060_state(sl060: types.ModuleType, *, irs_instead: str, level_1: int) -> Any:
    """A bound `sl060` state with the two fields the close paragraph reads.

    Args:
        sl060: The shipped module.
        irs_instead: `05 IRS-Instead pic x.` - "Y", "B" or the literal space.
        level_1: `07 Level-1 pic 9.` - 1 is `88 G-L`.

    Returns:
        The state.
    """
    from acas_posting import workfiles
    from acas_posting.records.calling_data import WsCallingData
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.otm3 import OiHeader
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.system_record_4 import SystemRecord4

    state = sl060._new_state(
        WsCallingData(),
        SystemRecord(),
        SystemRecord4(),
        _TO_DAY,
        FileDefs(),
        workfiles.open_item_work_file("otm2-in-memory", OiHeader),
    )
    state.system_record.general_ledger_block.irs_instead = irs_instead
    state.system_record.system_data_block.level.level_1 = level_1
    return state


#: The full truth table of `ca000-BL-Close`'s two nested tests, as the frozen nesting
#: produces it. `(irs_instead, level_1, spl_posting_close?, gl_posting_close?)`.
#:
#: ⭐ ROW 1 IS A-1. `IRS-Instead = space` and `Level-1 = 1` is pure General Ledger mode:
#: IF#3 would be TRUE on its own, and it is unreachable because IF#2 is false. THAT
#: UNREACHABILITY IS THE DEFECT, and it is what row 1 asserts.
_CLOSE_TRUTH_TABLE: Final[tuple[tuple[str, int, bool, bool], ...]] = (
    (_IRS_NEITHER, _LEVEL_1_GENERAL_LEDGER, False, False),
    (_IRS_NEITHER, _LEVEL_1_NOT_GENERAL_LEDGER, False, False),
    (_IRS_USED, _LEVEL_1_GENERAL_LEDGER, True, True),
    (_IRS_USED, _LEVEL_1_NOT_GENERAL_LEDGER, True, False),
    (_IRS_BOTH_USED, _LEVEL_1_GENERAL_LEDGER, True, True),
    (_IRS_BOTH_USED, _LEVEL_1_NOT_GENERAL_LEDGER, True, True),
)


@pytest.mark.parametrize(
    ("irs_instead", "level_1", "expect_spl", "expect_gl"),
    _CLOSE_TRUTH_TABLE,
    ids=[
        f"irs={'space' if irs else irs!r}-level1={level}"
        for irs, level, _, _ in _CLOSE_TRUTH_TABLE
    ],
)
def test_a1_the_posting_close_follows_the_nested_predicate(
    irs_instead: str, level_1: int, expect_spl: bool, expect_gl: bool
) -> None:
    """A-1's LOCK: `GL-Posting-Close` obeys the NESTED test, not a sibling one.

    Driven over the whole two-field truth table, because the defect is precisely a
    disagreement between the nested reading and the sibling reading, and they differ in
    exactly ONE row - `IRS-Instead = space` with `Level-1 = 1`. A test that exercised
    only the IRS states would pass against both readings and prove nothing.

    DO NOT ADD THE MISSING PERIOD to [sales/sl060.cbl:L1176]. This test exists so that
    doing so, or writing the "obviously correct" sibling `if` in a fresh translation of
    `ca000-BL-Close`, turns the suite RED instead of passing unnoticed (R-4).

    Args:
        irs_instead: The fan-out switch value.
        level_1: The installed-ledger level byte.
        expect_spl: Whether `SPL-Posting-Close` is performed.
        expect_gl: Whether `GL-Posting-Close` is performed.
    """
    with _shipped(_SL060) as sl060:
        double = _Sl060CloseDouble(sl060.facade)
        state = _sl060_state(sl060, irs_instead=irs_instead, level_1=level_1)
        with _driving(sl060, double):
            sl060._ca000_bl_close(state)

    #  The two UNCONDITIONAL verbs ran, whatever the switch says. L1161's write and
    #  L1174's close sit outside both tests, so their presence is what establishes that
    #  the paragraph ran at all and the absences below are real.
    assert double.calls[:2] == ["gl_batch_write", "gl_batch_close"], (
        f"the unconditional head of the paragraph did not run in source order; the "
        f"call log was {double.calls!r}. [sales/sl060.cbl:L1161] writes the batch and "
        f"L1174 closes it, and L1173's period is what makes L1174 unconditional."
    )

    assert ("spl_posting_close" in double.calls) is expect_spl, (
        f"IF#2 [sales/sl060.cbl:L1175] `if IRS-Used OR IRS-Both-Used` was evaluated "
        f"wrongly for IRS-Instead={irs_instead!r}: expected "
        f"spl_posting_close={expect_spl}, call log {double.calls!r}."
    )

    assert ("gl_posting_close" in double.calls) is expect_gl, (
        f"ANOMALY A-1 IS NOT REPRODUCED for IRS-Instead={irs_instead!r}, "
        f"Level-1={level_1}: expected gl_posting_close={expect_gl} and the call log "
        f"was {double.calls!r}.\n"
        f"  [sales/sl060.cbl:L1176] CARRIES NO TERMINATING PERIOD, so L1177's `if "
        f"IRS-Both-Used or G-L` is NESTED INSIDE L1175's `if IRS-Used OR "
        f"IRS-Both-Used` and the period at the end of L1178 closes both. "
        f"`GL-Posting-Close` therefore runs only when BOTH tests pass.\n"
        f"  IF THIS FAILED ON THE FIRST ROW - space / 1 - THE PERIOD HAS BEEN ADDED, "
        f"or the two tests have been written as siblings. That is a defect FIXED, "
        f"which rule R-4 makes a failure: 'a defect reproduced is correct; a defect "
        f"fixed is a failure.' Restore the nesting. Recorded as A-1 in "
        f"docs/migration/anomaly-log.md."
    )


def test_a1_the_nested_and_sibling_readings_differ_on_exactly_one_row() -> None:
    """The DETECTOR detects: the two readings disagree, and only in pure GL mode.

    Without this, the truth table above could be a table of the SIBLING reading and
    every row would still pass. So the two predicates are evaluated independently over
    the same six rows and required to disagree on exactly one - which is both the proof
    that the table discriminates and the statement of what A-1 costs.
    """
    disagreements: list[tuple[str, int]] = []
    for irs_instead, level_1, _, nested in _CLOSE_TRUTH_TABLE:
        #  The SIBLING reading - what the code would do WITH the period at L1176 - is
        #  IF#3 alone.
        sibling = irs_instead == _IRS_BOTH_USED or level_1 == _LEVEL_1_GENERAL_LEDGER
        if sibling != nested:
            disagreements.append((irs_instead, level_1))

    assert disagreements == [(_IRS_NEITHER, _LEVEL_1_GENERAL_LEDGER)], (
        f"the nested and sibling readings disagree on {disagreements!r}. A-1's whole "
        f"cost is that they disagree on PURE GENERAL LEDGER MODE and nowhere else - "
        f"which is why [purchase/pl060.cbl:L1031]'s identical statement WITH the "
        f"period is A-1's control, and why the sales clean-batch scenario is the only "
        f"journey on which the defect is even reachable."
    )


def test_a1_is_not_observable_in_any_table_and_this_file_says_why() -> None:
    """The premise of this section: a CLOSE has no database effect (MJ-07).

    Stated as an assertion rather than left in a comment, because it is the reason the
    lock lives here and not in `tests/scenarios/test_clean_batch_post_sl.py`. Both
    posting-close verbs are pure lifecycle calls: neither takes a value, neither returns
    one, and the record area each is handed is the one the program is already holding.
    A run that performed them and a run that did not leave the same rows, so the
    scenario comparison is a WITNESS to the two sides agreeing and not a detector.
    """
    with _shipped(_SL060) as sl060:
        real = sl060.facade
        for verb in ("gl_posting_close", "spl_posting_close", "gl_batch_close"):
            assert hasattr(real, verb), f"the facade does not publish {verb}"

        #  The two runs that differ ONLY in whether the posting file was closed produce
        #  the same record areas. Compared field by field on the two records the close
        #  verbs are handed, so the claim is measured rather than asserted.
        import dataclasses

        observed = []
        for irs_instead in (_IRS_NEITHER, _IRS_USED):
            double = _Sl060CloseDouble(sl060.facade)
            state = _sl060_state(
                sl060,
                irs_instead=irs_instead,
                level_1=_LEVEL_1_GENERAL_LEDGER,
            )
            with _driving(sl060, double):
                sl060._ca000_bl_close(state)
            observed.append(
                (
                    "gl_posting_close" in double.calls,
                    dataclasses.astuple(state.ws_posting_record),
                    dataclasses.astuple(state.ws_irs_posting_record),
                )
            )

    #  The verb sets DIFFER ...
    assert observed[0][0] is False and observed[1][0] is True
    #  ... and the record areas the verbs were handed are IDENTICAL, so no dump of
    #  GLPOSTING-REC or PSIRSPOST-REC could tell the two runs apart.
    assert observed[0][1] == observed[1][1], (
        "the posting record differs between the two runs, which would mean a close "
        "verb mutates it - it does not, and if it ever did this section's premise "
        "would need re-deriving."
    )
    assert observed[0][2] == observed[1][2]


# ---------------------------------------------------------------------------
#  2.  THE IR032 CLEAN REJECTION IN `irs030`   (finding MJ-11)
#
#  [irs/irs030.cbl:L1626-L1634]. `Input-Loop` moves the transfer record's DEBIT account
#  into the nominal key, reads it, and then:
#
#      L1630       if       we-error = 2
#      L1631                display  IR032 ...
#      L1632                display  WS-IRS-Post-DR ...
#      L1633                accept   WS-Reply at 2340
#      L1634                go to    Input-Loop.
#
#  So a missing DEBIT account is a CLEAN REJECTION: report, and take the next transfer
#  record. Nothing is written - which is the whole difference from anomaly A-4 twenty
#  lines later, where the DEBIT is committed at L1641 BEFORE the CREDIT account is
#  looked up at L1647, leaving a half-posted double entry when the CREDIT is the one
#  that is missing.
#
#  THE TWO PATHS ARE ADJACENT, DIFFER IN THEIR DATABASE EFFECT, AND ARE EASY TO
#  CONFLATE. Agent Action Plan section 0.6.5 separates them for exactly that reason.
#  A fixture cannot: the missing-debit path writes nothing, so on any seed both a
#  faithful implementation and one that aborted the run - or that committed the debit
#  anyway and then failed - can be made to leave the same rows. Only the verb sequence,
#  and whether the NEXT record is still processed, tells them apart.
# ---------------------------------------------------------------------------


class _Irs030Double:
    """The transfer file, the IRS nominal file and the posting file, in memory.

    Attributes:
        calls: Verb names in invocation order.
        rewrites: `(nl_owning, nl_dr, nl_cr)` per `acasirsub1-Rewrite`.
        writes: `Post-Key` per `acasirsub4-Write`.
        lookups: The `NL-Owning` each `acasirsub1-Read-Indexed` was asked for.
    """

    def __init__(
        self,
        facade_module: types.ModuleType,
        *,
        transfers: tuple[Mapping[str, object], ...] = (),
        missing_accounts: frozenset[int] = frozenset(),
    ) -> None:
        self.FacadeContext = facade_module.FacadeContext
        self.calls: list[str] = []
        self.rewrites: list[tuple[int, Decimal, Decimal]] = []
        self.writes: list[int] = []
        self.lookups: list[int] = []
        self._transfers = list(transfers)
        self._missing = missing_accounts

    def acas008_read_next(self, ctx: Any) -> None:
        """`acas008-Read-Next` - one transfer record, or at end."""
        self.calls.append("acas008_read_next")
        if not self._transfers:
            ctx.file_access.fs_reply = 10
            return
        row = self._transfers.pop(0)
        for attribute, value in row.items():
            setattr(ctx.record, attribute, value)
        ctx.file_access.fs_reply = 0
        ctx.file_access.we_error = _WE_ERROR_SUCCESS

    def acasirsub1_read_indexed(self, ctx: Any) -> None:
        """`acasirsub1-Read-Indexed` - the account, or `we-error = 2`."""
        self.calls.append("acasirsub1_read_indexed")
        requested = ctx.record.nl_key.nl_owning
        self.lookups.append(requested)
        if requested in self._missing:
            #  `we-error = 2` is the handler's RECORD NOT FOUND, and the frozen tests
            #  at [irs/irs030.cbl:L1630] and [:L1648] are EQUALITY with 2.
            ctx.file_access.we_error = _WE_ERROR_RECORD_NOT_FOUND
            ctx.file_access.fs_reply = 21
            return
        ctx.file_access.we_error = _WE_ERROR_SUCCESS
        ctx.file_access.fs_reply = 0
        ctx.record.nl_data.nl_dr = Decimal("0.00")
        ctx.record.nl_data.nl_cr = Decimal("0.00")

    def acasirsub1_rewrite(self, ctx: Any) -> None:
        """`acasirsub1-Rewrite` - persist one side of the double entry."""
        self.calls.append("acasirsub1_rewrite")
        record = ctx.record
        self.rewrites.append(
            (record.nl_key.nl_owning, record.nl_data.nl_dr, record.nl_data.nl_cr)
        )
        ctx.file_access.we_error = _WE_ERROR_SUCCESS
        ctx.file_access.fs_reply = 0

    def acasirsub4_write(self, ctx: Any) -> None:
        """`acasirsub4-Write` - the posting record."""
        self.calls.append("acasirsub4_write")
        #  `01 Posting-Record` [copybooks/irswspost.cob] names its key `Post-Key`;
        #  the COLUMN it lands in is `KEY-4` [mysql/ACASDB.sql], which is the
        #  bridge's renaming and not this record's field name.
        self.writes.append(ctx.record.post_key)
        ctx.file_access.we_error = _WE_ERROR_SUCCESS
        ctx.file_access.fs_reply = 0


def _irs030_ws(irs030: types.ModuleType) -> Any:
    """`irs030`'s working storage, bound with the two VAT snapshots zeroed.

    Args:
        irs030: The shipped module.

    Returns:
        The `_WorkingStorage`.
    """
    #  Each name from the module the SHIPPED program imports it from, so a record
    #  moving between modules breaks this helper rather than silently binding a
    #  different class: `WsIrsPostingRecord` is the SPL/IRS transfer layout in
    #  `spl_irs_posting`, NOT the internal posting record in `irs_posting`, and
    #  `AcasDalCommonData` lives with the test-data flags.
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.irs_dflt import WsIrsDefaultRecord
    from acas_posting.records.irs_nominal import WsIrsnlRecord
    from acas_posting.records.irs_posting import PostingRecord
    from acas_posting.records.irs_system import IrsSystemParams
    from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    return irs030._WorkingStorage(
        irs_system_params=IrsSystemParams(),
        ws_system_record=SystemRecord(),
        file_defs=FileDefs(),
        file_access=FileAccess(),
        dal_common=AcasDalCommonData(),
        ws_irsnl_record=WsIrsnlRecord(),
        ws_irs_default_record=WsIrsDefaultRecord(),
        posting_record=PostingRecord(),
        ws_irs_posting_record=WsIrsPostingRecord(),
        nl31_record=irs030._NlSnapshot(),
        nl32_record=irs030._NlSnapshot(),
        post_record_cnt=0,
        clear_posting_file=False,
        dal_options={},
    )


def _transfer(*, debit: int, credit: int, amount: str) -> dict[str, object]:
    """One transfer record, as `acas008-Read-Next` would deliver it.

    Args:
        debit: `WS-IRS-Post-DR`.
        credit: `WS-IRS-Post-CR`.
        amount: `WS-IRS-Post-Amount`, as a STRING so no binary float is built (R-2).

    Returns:
        The attribute values to set on the record area.
    """
    return {
        "ws_irs_post_dr": debit,
        "ws_irs_post_cr": credit,
        "ws_irs_post_amount": Decimal(amount),
        "ws_irs_vat_amount": Decimal("0.00"),
        "ws_irs_vat_ac_def": 0,
        "ws_irs_post_vat_side": " ",
    }


def test_ir032_a_missing_debit_account_writes_nothing_at_all() -> None:
    """THE CLEAN REJECTION: no nominal rewrite, no posting write (MJ-11).

    One transfer record whose DEBIT account is absent. The frozen path reports IR032 and
    loops [irs/irs030.cbl:L1630-L1634], so the run must reach the next read having
    written NOTHING - and in particular must not have committed the debit, which is what
    the ADJACENT missing-CREDIT path does twenty lines later as anomaly A-4.
    """
    with _shipped(_IRS030) as irs030:
        double = _Irs030Double(
            irs030.facade,
            transfers=(_transfer(debit=1010, credit=2020, amount="100.00"),),
            missing_accounts=frozenset({1010}),
        )
        ws = _irs030_ws(irs030)
        with _program_log(_IRS030) as log:
            with _driving(irs030, double):
                irs030._input_loop(ws)

    #  NOTHING WAS WRITTEN. Both absences asserted, because they are different claims:
    #  no nominal side was persisted, and no posting record was created.
    assert double.rewrites == [], (
        f"a nominal account was rewritten on the missing-DEBIT path: "
        f"{double.rewrites!r}. [irs/irs030.cbl:L1634] takes the next transfer record "
        f"BEFORE reaching the rewrite at L1641, so this path is a CLEAN rejection. "
        f"Committing the debit here would turn it into anomaly A-4, which is the "
        f"missing-CREDIT path and a different behaviour."
    )
    assert double.writes == [], (
        f"a posting record was written on the missing-DEBIT path: {double.writes!r}. "
        f"`acasirsub4-Write` is at [irs/irs030.cbl:L1670] and is unreachable from "
        f"L1634."
    )
    assert "acasirsub1_rewrite" not in double.calls
    assert "acasirsub4_write" not in double.calls

    #  THE DEBIT ACCOUNT WAS LOOKED UP, so the rejection is the one this test means and
    #  not a loop that never got started.
    assert double.lookups == [1010], (
        f"the debit account was not the only lookup: {double.lookups!r}. If the CREDIT "
        f"account was also read, control passed L1634 and this is not the clean path."
    )

    #  IT REPORTED, and reported the frozen identifier. The account number is
    #  deliberately withheld from the log (CWE-532) - the DISPOSITION is what is
    #  asserted, not the screen text.
    messages = [record.getMessage() for record in log]
    assert any(_IR032 in message for message in messages), (
        f"the clean rejection reported nothing recognisable; the log was {messages!r}. "
        f"[irs/irs030.cbl:L1631] displays IR032, and section 0.3.4 makes a diagnostic "
        f"with no database effect a log record."
    )


def test_ir032_processing_CONTINUES_to_the_next_transfer_record() -> None:
    """The rejection is a `GO TO Input-Loop`, NOT an abort (MJ-11).

    THE DISCRIMINATING HALF, and the reason the test above is not sufficient on its own:
    an implementation that ABORTED the run on a missing debit account would satisfy
    every "wrote nothing" assertion while being a different program. So two transfer
    records are served - the first with a missing debit, the second sound - and the
    SECOND must be posted in full.

    [irs/irs030.cbl:L1634] is `go to Input-Loop`, class 1 in the four-class taxonomy: a
    loop-back, which becomes `continue`. A `break` there would be class 2 and would end
    the walk.
    """
    with _shipped(_IRS030) as irs030:
        double = _Irs030Double(
            irs030.facade,
            transfers=(
                _transfer(debit=1010, credit=2020, amount="100.00"),
                _transfer(debit=3030, credit=4040, amount="250.00"),
            ),
            missing_accounts=frozenset({1010}),
        )
        ws = _irs030_ws(irs030)
        with _driving(irs030, double):
            irs030._input_loop(ws)

    #  THREE reads: the rejected record, the sound record, and the at-end that ends the
    #  walk. Two would mean the rejection ended it.
    assert double.calls.count("acas008_read_next") == 3, (
        f"the transfer file was read {double.calls.count('acas008_read_next')} "
        f"time(s); three are required - the rejected record, the sound record and the "
        f"at-end. Fewer means the missing debit ENDED the walk, which makes "
        f"[irs/irs030.cbl:L1634] a class-2 terminator instead of the class-1 loop-back "
        f"it is.\n  call log: {double.calls!r}"
    )

    #  The SECOND record was posted in full: both sides of the double entry and the
    #  posting record.
    assert [key for key, _, _ in double.rewrites] == [3030, 4040], (
        f"the sound record's double entry was not posted to both accounts: "
        f"{double.rewrites!r}. The debit is rewritten at [irs/irs030.cbl:L1641] and "
        f"the credit at [irs/irs030.cbl:L1660]."
    )
    assert len(double.writes) == 1, (
        f"the sound record produced {len(double.writes)} posting record(s); exactly "
        f"one is required [irs/irs030.cbl:L1670]."
    )

    #  And the counter counted BOTH records, because `add 1 to Post-Record-Cnt`
    #  [irs/irs030.cbl:L1623] precedes the account lookup and is therefore reached by
    #  the rejected record too. A display counter only - it reaches no table - and it is
    #  asserted here because it is the one field that distinguishes "the record was
    #  seen" from "the record was skipped before being counted".
    assert ws.post_record_cnt == 2, (
        f"Post-Record-Cnt is {ws.post_record_cnt}; it counts every record READ, and "
        f"[irs/irs030.cbl:L1623] sits BEFORE the missing-account test at L1630."
    )


def test_ir032_and_a4_are_different_paths_with_different_effects() -> None:
    """The missing-DEBIT and missing-CREDIT paths are not interchangeable (MJ-11).

    Both are "an account was not found", they are twenty lines apart, and they have
    OPPOSITE database effects: the debit path writes nothing, and the credit path leaves
    the debit already committed. Agent Action Plan section 0.6.5 separates them, and
    this test is what makes the separation checkable rather than a matter of reading.

    A-4 is asserted in its DEFECTIVE form - one rewrite, unbalanced, and no posting
    record. Rule R-4 forbids repairing it, and a transcription that looked the credit
    account up BEFORE committing the debit would be exactly that repair.
    """
    with _shipped(_IRS030) as irs030:
        #  Missing DEBIT.
        debit_double = _Irs030Double(
            irs030.facade,
            transfers=(_transfer(debit=1010, credit=2020, amount="100.00"),),
            missing_accounts=frozenset({1010}),
        )
        with _driving(irs030, debit_double):
            irs030._input_loop(_irs030_ws(irs030))

        #  Missing CREDIT - anomaly A-4.
        credit_double = _Irs030Double(
            irs030.facade,
            transfers=(_transfer(debit=1010, credit=2020, amount="100.00"),),
            missing_accounts=frozenset({2020}),
        )
        with _driving(irs030, credit_double):
            irs030._input_loop(_irs030_ws(irs030))

    #  The debit path: nothing.
    assert debit_double.rewrites == [] and debit_double.writes == []

    #  The credit path: THE DEBIT IS ALREADY COMMITTED, and there is no posting record -
    #  a half-posted double entry, which is anomaly A-4 exactly as recorded.
    assert [key for key, _, _ in credit_double.rewrites] == [1010], (
        f"ANOMALY A-4 IS NOT REPRODUCED. The missing-CREDIT path must leave the DEBIT "
        f"already rewritten, because [irs/irs030.cbl:L1641] commits it BEFORE the "
        f"credit account is looked up at L1647. Observed rewrites: "
        f"{credit_double.rewrites!r}.\n"
        f"  If this shows NO rewrite, the credit lookup has been moved ahead of the "
        f"debit commit - a defect FIXED, which rule R-4 makes a failure."
    )
    assert credit_double.writes == [], (
        f"the missing-credit path wrote a posting record: {credit_double.writes!r}. "
        f"[irs/irs030.cbl:L1652] leaves for the next record before L1670."
    )

    #  Stated as the comparison it is, so the asymmetry is the assertion rather than an
    #  observation about two separate numbers.
    assert len(credit_double.rewrites) > len(debit_double.rewrites), (
        "the two missing-account paths left the same database effect, so one of them "
        "has been made to behave like the other. They are deliberately different: "
        "section 0.6.5 classes the debit path as a CLEAN rejection and the credit path "
        "as a PARTIAL one."
    )
