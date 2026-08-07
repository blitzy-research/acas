"""The CLI boundary's failure paths, driven for real.

WHY THIS FILE EXISTS. The migration's command-line layer carries decisions that change
what runs and what a caller is told, and until now NO TEST IMPORTED `acas_posting.cli` at
all: the arithmetic tier reaches `cobol` and `records`, and the scenario tier reaches the
CLI only through the harness's runner script, which drives the SUCCESS path with a live
database. So every refusal, every short-circuit and every status code at the boundary was
unexercised - and each of them is a place where a wrong answer is silent rather than loud.

FIVE SEAMS, and each is one an operator or a scenario depends on:

  1. THE KEY-1 SYSTEM READ [acas_posting/cli/args.py, `aa010_get_system_recs`]. The menu
     shell reads `SYSTEM-REC` under `File-Key-No` 1 before it dispatches anything
     [general/general.cbl:L398-L418]. If that read fails, the migrated boundary logs, then
     CLOSES, then raises - and the pair it reports has to be THE READ'S, not the close's,
     because a close overwrites `Fs-Reply` on the same shared block
     [copybooks/wsfnctn.cob:L25]. Getting the order wrong turns a diagnosable failure into
     "FS-Reply 0".

  2. THE VERB VOCABULARY THE MENU STATE SELECTS. `irs/irs.cbl` copies the handler-named
     facade [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob] and drives `acas000` by its HANDLER
     name [irs/irs.cbl:L499, L512], while the General, Sales and Purchase menus copy the
     entity-named one [copybooks/Proc-ACAS-FH-Calls.cob]. The two are NOT interchangeable:
     the handler-named open family carries its own error check and can end the menu
     program outright. The selection is a one-field decision on the menu state, and this
     file asserts which state picks which.

  3. THE POSTING CYCLE'S TWO SHORT-CIRCUITS [acas_posting/cli/gl_post_cycle.py, `load08`].
     `gl070` raising term code 5 stops the cycle before `gl071` and `gl072`
     [general/general.cbl:L810-L811]; a SERIOUS error - above 7
     [general/general.cbl:L720-L721] - stops it wherever it happens. A cycle that ran
     `gl072` after `gl071` had failed would post from a work file that was never sorted,
     and `gl072` finds its accounts by SEQUENTIAL read [general/gl072.cbl:L410-L412], so
     the postings would go to the WRONG ACCOUNTS with no error at all.

  4. THE REQUIRED OPTIONS. Two routes refuse to run without an explicit answer: the
     General route needs `--run-date`, because rule R-6 forbids taking a date from the
     clock, and the IRS route needs `--clear-posting-file` or `--no-clear-posting-file`,
     because one of those answers DELETES EVERY ROW of the transfer table
     [irs/irs030.cbl:L1715-L1724]. An implied default for either would be an invented
     behaviour.

  5. THE CONFIGURATION CONTRACT'S STATUS CODES [acas_posting/cli/rdbms_params.py]. The
     frozen parameter reader publishes 8 for "no source" and 1 for "malformed"
     [common/acas-get-params.cbl:L37-L42], and the boundary surfaces the error's own code
     so a caller can tell "not configured" from "misconfigured" without parsing text.

⛔ NO DATABASE, NO COBOL, NO SUBPROCESS (R-1). Every test replaces the seam it is not
about: the system verbs are a triple of callables, the three General Ledger programs are
doubles, and no test resolves a real connection. The imports of `acas_posting.cli` pull
`acas_posting.dal.facade` and the pinned driver in transitively, so every loader purges
what it added and the tier's three isolation assertions keep holding whatever order the
files run in.

THE RULES, as they bind this file (Agent Action Plan section 0.7.2):

  R-1  No COBOL at runtime, no database.
  R-2  Zero binary floating point. Nothing here computes money; the one numeric family in
       play is exit statuses, which are `int`.
  R-3  ⛔ No added validation. The two required options are not a validation this
       migration invented - each replaces a frozen prompt that cannot be left
       unanswered - and the tests say so at the site.
  R-4  Reproduced, not repaired: the IRS route ABSORBS the facade copybook's `goback`
       [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] as a normal return, because that is
       what the frozen menu program does with it.
  R-5  Every test names the frozen line and the shipped function it drives.
  R-6  ⭐ The run date arrives through linkage and never from a clock, which is why
       `--run-date` is required rather than defaulted. Asserted here as a refusal.

⚠ PROVENANCE OF RULES. There is no user rules document - `review_rules` returns exactly
`No user rules provided.` The rules above are the Technical Specification's, section
0.7.2, and nothing has been invented to fill the gap.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Final

import pytest

pytestmark = pytest.mark.arithmetic


#: The module-name prefixes this directory's isolation assertions forbid.
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

#: `move 1 to File-Key-No` - the system parameter record [general/general.cbl:L399].
_KEY_PARAMS: Final[int] = 1

#: The defaults record, key 2 [general/general.cbl:L406].
_KEY_DEFAULTS: Final[int] = 2

#: The period-totals record, key 4 [general/general.cbl:L402].
_KEY_TOTALS: Final[int] = 4

#: `if ws-term-code = 5` - the abort gate [general/general.cbl:L810].
_ABORT_TERM_CODE: Final[int] = 5

#: `if ws-term-code > 7` - the serious-error threshold [general/general.cbl:L720].
_SERIOUS_THRESHOLD: Final[int] = 7

#: A run date in the DD/MM/CCYY form the menu shell supplies, pinned so that nothing
#: reads a clock (R-6).
_RUN_DATE_TEXT: Final[str] = "21/09/2025"

#: The six-variable deployment contract, complete, so that the SUCCESS path of
#: `aa010_get_system_recs` can run to its end: after the key-1 read the boundary binds the
#: connection parameters onto `SYSTEM-REC` [copybooks/wssystem.cob:L137-L144], and an
#: absent contract raises there rather than at the read. Supplied as a MAPPING rather than
#: exported, so the tests do not depend on the host's own environment and cannot leak one
#: of its values. Nothing here opens a connection.
_CONTRACT: Final[dict[str, str]] = {
    "ACAS_DB_HOST": "db.internal",
    "ACAS_DB_USER": "acas",
    #: A literal that is obviously not a credential, and is never asserted by value.
    "ACAS_DB_PASSWORD": "test-only",
    "ACAS_DB_NAME": "ACASDB",
    "ACAS_DB_PORT": "3306",
    "ACAS_DB_SOCKET": "",
}

#: `argparse`'s own status for a usage error. Not this project's choice, but it IS the
#: status an operator and a shell script see, so it is asserted rather than assumed.
_USAGE_ERROR_STATUS: Final[int] = 2


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix this tier must not leave loaded?"""
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped(*dotted_names: str) -> Iterator[tuple[types.ModuleType, ...]]:
    """Import shipped modules for one test, leaving `sys.modules` as found.

    Not optional and not memoised, for the reasons every loader in this directory
    records: `pytest.importorskip` turns a broken shipped module into a PASS, and a
    memoised module is already resident so the purge would remove nothing.

    Args:
        dotted_names: The importable names, in the order they are wanted.

    Yields:
        The imported modules, in the same order.

    Raises:
        AssertionError: A name was already resident on the way in, or survived the purge.
        ImportError: A module could not be imported. Deliberately NOT a skip.
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
    for name in dotted_names:
        assert name not in sys.modules, (
            f"{name} survived the eviction above, so this would not be a fresh "
            f"import and the purge on the way out would remove nothing."
        )
    before = frozenset(sys.modules)
    completed = False
    try:
        modules = tuple(importlib.import_module(name) for name in dotted_names)
        yield modules
        completed = True
    finally:
        for name in sorted(set(sys.modules) - before, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
        )
        if completed:
            assert not residue, f"{dotted_names} left {residue} resident after the purge."


class _SystemVerbDouble:
    """The three `acas000` verbs the menu shell drives, recording the keys it asked for.

    ⭐ THE KEY IS READ OFF THE SHARED BLOCK AT CALL TIME, which is the whole mechanism
    being tested: `_select_key` writes `File-Key-No` [copybooks/wsfnctn.cob:L44-L56] and
    the verb is then expected to act on THAT key. A double that took the key as an
    argument would test a different design.

    Attributes:
        opened: The `File-Key-No` at each `open_input`.
        read: The `File-Key-No` at each `read_indexed`.
        closed: The `File-Key-No` at each `close`.
        order: Every call in order, as `(verb, key)`.
    """

    def __init__(
        self,
        status_module: types.ModuleType,
        facade_module: types.ModuleType,
        *,
        read_replies: dict[int, tuple[int, int]] | None = None,
        close_reply: tuple[int, int] = (0, 0),
    ) -> None:
        self._status = status_module
        self._facade = facade_module
        self._read_replies = dict(read_replies or {})
        self._close_reply = close_reply
        self.opened: list[int] = []
        self.read: list[int] = []
        self.closed: list[int] = []
        self.order: list[tuple[str, int]] = []

    def _pair(self, ctx: Any, fs_reply: int, we_error: int) -> Any:
        ctx.file_access.fs_reply = fs_reply
        ctx.file_access.we_error = we_error
        return self._facade.StatusPair(fs_reply, we_error)

    def open_input(self, ctx: Any) -> Any:
        key = ctx.file_access.logging_data.file_key_no
        self.opened.append(key)
        self.order.append(("open_input", key))
        return self._pair(ctx, 0, 0)

    def read_indexed(self, ctx: Any) -> Any:
        key = ctx.file_access.logging_data.file_key_no
        self.read.append(key)
        self.order.append(("read_indexed", key))
        fs_reply, we_error = self._read_replies.get(key, (0, 0))
        return self._pair(ctx, fs_reply, we_error)

    def close(self, ctx: Any) -> Any:
        key = ctx.file_access.logging_data.file_key_no
        self.closed.append(key)
        self.order.append(("close", key))
        return self._pair(ctx, *self._close_reply)


def _install_verbs(args_module: types.ModuleType, double: _SystemVerbDouble) -> None:
    """Put `double` behind BOTH published vocabularies for the duration of a test.

    Both, because `_system_verbs` selects between two module-level triples and a test
    about the key sequence should not also depend on which vocabulary was chosen - the
    selection has its own test.

    Args:
        args_module: The shipped `cli.args`.
        double: The stand-in.
    """
    replacement = args_module._SystemVerbs(
        double.open_input,
        double.read_indexed,
        double.close,
        "double",
        "double",
    )
    args_module._ENTITY_NAMED_SYSTEM_VERBS = replacement
    args_module._HANDLER_NAMED_SYSTEM_VERBS = replacement


def _namespace(args_module: types.ModuleType) -> argparse.Namespace:
    """The parsed namespace `aa010_get_system_recs` reads its pins from.

    ⭐ BUILT BY THE SHIPPED ARGUMENT HELPERS, not hand-assembled. `_apply_cli_pins` reads
    `ns.date_form` and moves it into `pic 9` [copybooks/wssystem.cob:L127], so a
    hand-made namespace with `None` in that attribute fails inside the semantics layer
    rather than testing anything - and building the namespace the way the routes build it
    exercises `add_calling_data_arguments` and `add_gl_linkage_arguments` at the same
    time. The two helpers are exactly the pair `gl_post_cycle._build_parser` uses.

    Args:
        args_module: The shipped `cli.args`.

    Returns:
        The namespace, with the parser's own defaults in every attribute the boundary
        reads.
    """
    parser = argparse.ArgumentParser()
    args_module.add_calling_data_arguments(
        parser, default_caller=args_module.WS_CALLER_GENERAL
    )
    args_module.add_gl_linkage_arguments(parser)
    return parser.parse_args(["--run-date", _RUN_DATE_TEXT])


# ---------------------------------------------------------------------------
#  1.  THE KEY-1 SYSTEM READ - STATUS BEFORE CLOSE
# ---------------------------------------------------------------------------


def test_the_key_one_failure_reports_the_reads_pair_and_not_the_closes() -> None:
    """⭐ THE READ'S STATUS SURVIVES THE CLOSE THAT FOLLOWS IT.

    `Fs-Reply` and `We-Error` live on ONE shared `File-Access` block
    [copybooks/wsfnctn.cob:L22-L38] that every verb writes, so the close issued after a
    failed read OVERWRITES both. The shipped boundary captures the read's pair into a
    local and reports THAT [acas_posting/cli/args.py, `aa010_get_system_recs`], which is
    the only way an operator learns why the record could not be read.

    THE DOUBLE MAKES THE TWO PAIRS DIFFERENT ON PURPOSE: the read answers
    `FS-Reply 23 / WE-Error 121` - 23 being the ISAM "record not found" every handler
    reports for an absent key - and the close answers `0 / 0`, which is what a successful
    close reports. A boundary that read the block after closing would report `0 / 0`, and
    the message would say the record could not be read and that nothing was wrong.

    THE CLOSE STILL HAPPENS, and that is asserted too: the frozen menu closes the file on
    the failure path [general/general.cbl:L412-L418], and leaving it open would strand a
    handle for the rest of the process.
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(
            status, facade, read_replies={_KEY_PARAMS: (23, 121)}, close_reply=(0, 0)
        )
        _install_verbs(args, double)
        state = args.irs_menu_state()
        system_record = args._declared_system_record()

        with pytest.raises(args.SystemRecordUnavailableError) as unavailable:
            args.aa010_get_system_recs(
                system_record,
                state,
                args.FileDefs(),
                _namespace(args),
                args.resolve_clock(_RUN_DATE_TEXT),
                env={},
            )

        #  THE READ'S PAIR, carried on the exception.
        assert unavailable.value.fs_reply == 23
        assert unavailable.value.we_error == 121
        #  Both figures also appear in the message, because that is what an operator
        #  reads; and the key is named, because there are four of them.
        message = str(unavailable.value)
        assert "FS-Reply=23" in message
        assert "WE-Error=121" in message
        assert f"File-Key-No {_KEY_PARAMS}" in message

        #  The close happened, on key 1, AFTER the read.
        assert double.closed == [_KEY_PARAMS]
        assert double.order[-1] == ("close", _KEY_PARAMS)
        assert double.order[-2] == ("read_indexed", _KEY_PARAMS)
        #  And the shared block now holds the CLOSE's pair - which is precisely why the
        #  exception could not have been built from it.
        assert state.file_access.fs_reply == 0
        assert state.file_access.we_error == 0


def test_a_successful_key_one_read_closes_and_returns_without_raising() -> None:
    """The control: the same route with a read that succeeds.

    Without this, the test above would pass just as well if the boundary raised
    unconditionally - and a boundary that always raised would make every route unusable
    while the failure test stayed green. The success path is therefore asserted whole: no
    exception, the file closed exactly once, and the run date pinned onto the record from
    the controlled clock rather than from anywhere else (R-6).
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.irs_menu_state()
        system_record = args._declared_system_record()
        pinned = args.resolve_clock(_RUN_DATE_TEXT)

        args.aa010_get_system_recs(
            system_record, state, args.FileDefs(), _namespace(args), pinned, env=_CONTRACT
        )

        assert double.closed == [_KEY_PARAMS]
        assert system_record.system_data_block.run_date == pinned.run_date
        #  A non-zero binary run date, so the assertion above is not comparing two zeroes.
        assert pinned.run_date > 0

        #  ⭐ AND THE SUCCESS PATH CONTINUES PAST THE READ. `_apply_cli_pins` binds the
        #  six connection parameters onto the record it has just read
        #  [copybooks/wssystem.cob:L137-L144], which is why an absent contract fails HERE
        #  rather than at the read - the status-code tests in section 4 drive that half.
        #  Four of the six are asserted by value; the password is not, because a test
        #  that printed one would be a test that could leak one.
        assert system_record.system_data_block.rdbms_host.rstrip() == "db.internal"
        assert system_record.system_data_block.rdbms_user.rstrip() == "acas"
        assert system_record.system_data_block.rdbms_db_name.rstrip() == "ACASDB"
        assert system_record.system_data_block.rdbms_port.rstrip() == "3306"


def test_the_irs_menu_state_reads_key_one_and_nothing_else() -> None:
    """`irs/irs.cbl` reads ONE system record; the General menu reads three.

    The IRS menu state carries neither a totals record nor a defaults record
    [acas_posting/cli/args.py, `irs_menu_state`], and the two reads at keys 4 and 2 are
    guarded on their presence - so the IRS route touches key 1 only. A route that read
    keys 2 and 4 anyway would issue two reads against records the IRS subsystem does not
    have, and the extra traffic would appear in the handler's own log.

    ASSERTED AS THE ORDERED KEY SEQUENCE, not as a count, because the ORDER is the frozen
    menu's: open on key 1, then the other records, then BACK to key 1 for the read that
    matters, then close.
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.irs_menu_state()
        assert state.system_record_4 is None
        assert state.default_record is None

        args.aa010_get_system_recs(
            args._declared_system_record(),
            state,
            args.FileDefs(),
            _namespace(args),
            args.resolve_clock(_RUN_DATE_TEXT),
            env=_CONTRACT,
        )

        assert double.order == [
            ("open_input", _KEY_PARAMS),
            ("read_indexed", _KEY_PARAMS),
            ("close", _KEY_PARAMS),
        ]


def test_the_general_menu_state_reads_the_totals_and_defaults_records_first() -> None:
    """Keys 4 and 2 are read BEFORE the key-1 read the dispatch depends on.

    `general/general.cbl` reads the period totals and the defaults as well
    [general/general.cbl:L398-L410], and the order matters for one concrete reason: the
    handler has ONE record buffer that four bridges reinterpret
    [common/acas000.cbl:L311], so the key-1 read has to come LAST or the parameter record
    would be overwritten by whichever record was read after it.

    THE SALES AND PURCHASE STATE reads the totals but not the defaults, which is the
    third shape and is asserted in the same test so the three cannot drift apart.
    """
    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.general_menu_state()
        assert state.system_record_4 is not None
        assert state.default_record is not None

        args.aa010_get_system_recs(
            args._declared_system_record(),
            state,
            args.FileDefs(),
            _namespace(args),
            args.resolve_clock(_RUN_DATE_TEXT),
            env=_CONTRACT,
        )

        assert double.order == [
            ("open_input", _KEY_PARAMS),
            ("read_indexed", _KEY_TOTALS),
            ("read_indexed", _KEY_DEFAULTS),
            ("read_indexed", _KEY_PARAMS),
            ("close", _KEY_PARAMS),
        ]

    with _shipped(
        "acas_posting.cli.args", "acas_posting.dal.facade", "acas_posting.dal.status"
    ) as (args, facade, status):
        double = _SystemVerbDouble(status, facade)
        _install_verbs(args, double)
        state = args.slpl_menu_state()
        assert state.system_record_4 is not None
        assert state.default_record is None

        args.aa010_get_system_recs(
            args._declared_system_record(),
            state,
            args.FileDefs(),
            _namespace(args),
            args.resolve_clock(_RUN_DATE_TEXT),
            env=_CONTRACT,
        )

        assert double.order == [
            ("open_input", _KEY_PARAMS),
            ("read_indexed", _KEY_TOTALS),
            ("read_indexed", _KEY_PARAMS),
            ("close", _KEY_PARAMS),
        ]


def test_the_menu_state_selects_the_vocabulary_its_frozen_menu_copies() -> None:
    """⭐ ONE FIELD DECIDES WHICH FACADE PARAGRAPHS RUN, and it is not cosmetic.

    `irs/irs.cbl` copies [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob] and performs
    `acas000-open-Input` [irs/irs.cbl:L499]; the General, Sales and Purchase menus copy
    [copybooks/Proc-ACAS-FH-Calls.cob] and perform `System-Open-Input`. The IRS
    convention's open family carries a per-handler error check that can end the menu
    program outright, and the entity-named one has no such paragraph at all - so the two
    vocabularies differ in DISPOSITION and not only in name.

    Asserted through the shipped selector rather than by inspecting the constants, and
    with the copybook each triple names, because that name is the traceability claim
    (R-5).
    """
    with _shipped("acas_posting.cli.args") as (args,):
        irs = args._system_verbs(args.irs_menu_state())
        general = args._system_verbs(args.general_menu_state())
        slpl = args._system_verbs(args.slpl_menu_state())

        assert irs.copybook == "copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob"
        assert irs.paragraphs.startswith("acas000-")
        assert general.copybook == "copybooks/Proc-ACAS-FH-Calls.cob"
        assert general.paragraphs.startswith("System-")
        #  Sales and Purchase use the same vocabulary as General - the same triple
        #  object, so they cannot diverge.
        assert slpl == general
        assert irs != general
        #  And the flag that selects it is the menu state's own.
        assert args.irs_menu_state().handler_named_verbs is True
        assert args.general_menu_state().handler_named_verbs is False
        assert args.slpl_menu_state().handler_named_verbs is False


# ---------------------------------------------------------------------------
#  2.  THE POSTING CYCLE'S TWO SHORT-CIRCUITS
# ---------------------------------------------------------------------------


class _ProgramDouble:
    """One of the three General Ledger programs, recording that it was dispatched.

    Attributes:
        dispatched: Appended to on every `run`.
    """

    def __init__(
        self, name: str, log: list[str], *, term_code: int | None = None
    ) -> None:
        self._name = name
        self._log = log
        self._term_code = term_code

    def run(
        self,
        ws_calling_data: Any,
        system_record: Any,
        to_day: str,
        file_defs: Any,
        /,
        *,
        work_files: Any = None,
    ) -> Any:
        self._log.append(self._name)
        if self._term_code is not None:
            #  `move <n> to ws-term-code` - what a program does to report a
            #  disposition to the menu [copybooks/wscall.cob:L10].
            ws_calling_data.ws_term_code = self._term_code
        return work_files


@contextlib.contextmanager
def _programs(
    cycle: types.ModuleType, log: list[str], *, term_codes: dict[str, int]
) -> Iterator[None]:
    """Replace the three program modules `load08` dispatches, then restore them.

    The module-global names are the seam, exactly as they are for the program modules'
    `facade`: `load08` names `gl070_transaction_pre_process` and its two siblings, and a
    `CALL` in the frozen menu resolves by name at run time too.

    Args:
        cycle: The shipped `cli.gl_post_cycle`.
        log: The list every dispatch appends its program id to.
        term_codes: Program id to the term code that program reports, if any.

    Yields:
        None, for the duration.
    """
    originals = {
        "gl070_transaction_pre_process": cycle.gl070_transaction_pre_process,
        "gl071_batch_sort": cycle.gl071_batch_sort,
        "gl072_transaction_update": cycle.gl072_transaction_update,
    }
    identifiers = {
        "gl070_transaction_pre_process": "gl070",
        "gl071_batch_sort": "gl071",
        "gl072_transaction_update": "gl072",
    }
    try:
        for attribute, program_id in identifiers.items():
            setattr(
                cycle,
                attribute,
                _ProgramDouble(program_id, log, term_code=term_codes.get(program_id)),
            )
        yield
    finally:
        for attribute, original in originals.items():
            setattr(cycle, attribute, original)


def _gl_linkage(args: types.ModuleType) -> Any:
    """The four-parameter General Ledger linkage, built without a database.

    `bind_gl_linkage` resolves a connection contract, so it is not used here: what these
    tests are about is the dispatch sequence, and the linkage is a named tuple of four
    records.

    Args:
        args: The shipped `cli.args`.

    Returns:
        The linkage.
    """
    return args.GlLinkage(
        args._declared_calling_data(),
        args._declared_system_record(),
        _RUN_DATE_TEXT,
        args.FileDefs(),
    )


def test_all_three_phases_run_when_no_program_reports_a_disposition() -> None:
    """`load08` dispatches gl070, gl071 and gl072 in that order.

    THE CONTROL for the two short-circuit tests, and a claim in its own right: the order
    is load-bearing because `gl072` locates each posting's nominal account by SEQUENTIAL
    read [general/gl072.cbl:L410-L412] and therefore depends on `gl071` having emitted
    the stream in nominal-key order.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        linkage = _gl_linkage(args)
        with _programs(cycle, dispatched, term_codes={}):
            cycle.load08(linkage, menu_state=args.general_menu_state())

        assert dispatched == ["gl070", "gl071", "gl072"]
        assert linkage.calling_data.ws_term_code == 0


def test_the_abort_term_code_stops_the_cycle_before_gl071_and_gl072() -> None:
    """`if ws-term-code = 5 ... go to menu` [general/general.cbl:L810-L811].

    `gl070` raises 5 when it finds a batch left open [general/gl070.cbl:L289], and the
    frozen menu then returns WITHOUT dispatching the sort or the update. The database
    effect of the abort is therefore THE ABSENCE of everything those two would have
    written, which is Agent Action Plan section 0.6.5's second rejection class - and it
    only holds if the gate is a hard stop rather than a warning.

    ⭐ FIVE IS NOT A SERIOUS ERROR. `is_serious_error` tests ABOVE seven
    [general/general.cbl:L720], so the abort takes its own arm and not the error arm -
    asserted here by the term code surviving as 5 rather than being escalated.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        linkage = _gl_linkage(args)
        with _programs(cycle, dispatched, term_codes={"gl070": _ABORT_TERM_CODE}):
            cycle.load08(linkage, menu_state=args.general_menu_state())

        assert dispatched == ["gl070"]
        assert linkage.calling_data.ws_term_code == _ABORT_TERM_CODE
        assert args.is_serious_error(_ABORT_TERM_CODE) is False
        #  And the process status is the term code itself, so a shell script can tell an
        #  abort from a clean run [copybooks/wscall.cob:L10].
        assert args.exit_status_for(_ABORT_TERM_CODE) == _ABORT_TERM_CODE


def test_a_serious_error_from_gl071_stops_the_cycle_before_gl072() -> None:
    """⭐⭐ THE SHORT-CIRCUIT THAT PREVENTS SILENT MISPOSTING.

    `load00` tests `if ws-term-code > 7` after every dispatch
    [general/general.cbl:L720-L721], and `load08` returns as soon as one reports it. The
    consequence of getting this wrong is the worst kind in this codebase: `gl072` finds
    each posting's account with a SEQUENTIAL read [general/gl072.cbl:L410-L412], so
    running it after a FAILED sort posts to whatever account the unsorted stream happens
    to reach - with no error, no diagnostic and no way to tell from the tables that
    anything went wrong.

    THE SYSTEM RECORDS ARE STILL PERSISTED on the way out, because `load00`'s error arm
    performs the same `overrewrite` the menu's quit key does - so a failed cycle does not
    lose the parameter record. Asserted through a recorder rather than by writing to a
    database.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        persisted: list[object] = []
        original_overrewrite = args.overrewrite
        args.overrewrite = lambda *arguments, **keywords: persisted.append(arguments)
        try:
            linkage = _gl_linkage(args)
            with _programs(
                cycle, dispatched, term_codes={"gl071": _SERIOUS_THRESHOLD + 1}
            ):
                cycle.load08(linkage, menu_state=args.general_menu_state())
        finally:
            args.overrewrite = original_overrewrite

        assert dispatched == ["gl070", "gl071"]
        assert "gl072" not in dispatched
        assert linkage.calling_data.ws_term_code == _SERIOUS_THRESHOLD + 1
        assert args.is_serious_error(linkage.calling_data.ws_term_code) is True
        #  Exactly one persist, from `load00`'s error arm.
        assert len(persisted) == 1


def test_a_serious_error_from_gl070_stops_the_cycle_before_gl071() -> None:
    """The same gate at the FIRST dispatch, so the sort never runs either.

    `load08` checks the disposition after each of its two guarded dispatches, and a
    migration that checked only after the second would run `gl071` over a work file
    `gl070` had abandoned. Asserted separately because the two call sites are separate
    statements.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        persisted: list[object] = []
        original_overrewrite = args.overrewrite
        args.overrewrite = lambda *arguments, **keywords: persisted.append(arguments)
        try:
            linkage = _gl_linkage(args)
            with _programs(cycle, dispatched, term_codes={"gl070": 99}):
                cycle.load08(linkage, menu_state=args.general_menu_state())
        finally:
            args.overrewrite = original_overrewrite

        assert dispatched == ["gl070"]
        assert len(persisted) == 1
        assert args.exit_status_for(99) == 99


# ---------------------------------------------------------------------------
#  3.  THE REQUIRED OPTIONS - AN OMISSION IS A USAGE ERROR, NOT A DEFAULT
# ---------------------------------------------------------------------------


def test_the_general_route_refuses_to_run_without_a_run_date() -> None:
    """⭐ THERE IS NO DEFAULT RUN DATE, and that is rule R-6 made operational.

    Every date the migrated cycle uses arrives through linkage
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80 is the ONE clock read in the whole call
    chain, and it lives in the menu shell]. If the CLI defaulted the run date to today,
    two runs of the same scenario would write different rows and the determinism
    requirement would be unenforceable - so `--run-date` is required and its omission is
    a usage error.

    ⛔ NOT AN ADDED VALIDATION (R-3). The frozen menu obtains the date before it
    dispatches anything [general/general.cbl:L371]; requiring it at the boundary is where
    that acquisition went, not a new rule.

    NOTHING IS DISPATCHED: the three program doubles record every call, and the list is
    empty, so the refusal happens during parsing and before any program is entered.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        dispatched: list[str] = []
        with _programs(cycle, dispatched, term_codes={}):
            with pytest.raises(SystemExit) as exited:
                cycle.main([])

        assert exited.value.code == _USAGE_ERROR_STATUS
        assert dispatched == []

        #  And the option IS declared required on the parser, which is what makes the
        #  status a usage error rather than a later failure.
        required = [
            action.option_strings
            for action in cycle._build_parser()._actions
            if action.required
        ]
        assert ["--run-date"] in required


def test_the_irs_route_requires_an_explicit_clear_posting_file_answer() -> None:
    """⭐⭐ ONE ANSWER DELETES EVERY ROW OF THE TRANSFER TABLE, so neither is defaulted.

    `irs030`'s end-of-job question [irs/irs030.cbl:L1715-L1724] decides whether the
    transfer file is cleared, and answering yes performs an open-output which for this
    handler is a MASS DELETE [common/acas008.cbl:L313-L319]. Agent Action Plan section
    0.3.4 promotes exactly this kind of prompt to a parameter *"with the COBOL default
    preserved"* - and the frozen program HAS NO DEFAULT: the `[Y]` in the prompt is
    display text, the accept carries no `WITH UPDATE`, and any reply that is neither Y nor
    N re-prompts, so a bare Enter cannot leave the loop.

    So the migrated route requires one of the two switches, and omitting both is a usage
    error rather than an implied yes. A defaulted yes would empty one of the compared
    tables on every run that forgot to say otherwise.
    """
    with _shipped("acas_posting.cli.irs_post", "acas_posting.cli.args") as (
        route,
        args,
    ):
        with pytest.raises(SystemExit) as exited:
            route.main(["--run-date", _RUN_DATE_TEXT])

        assert exited.value.code == _USAGE_ERROR_STATUS

        required = [
            action.option_strings
            for action in route._build_parser()._actions
            if action.required
        ]
        #  Both the run date and the destructive answer are required, and the switch is
        #  a paired boolean so that saying no is as explicit as saying yes.
        assert ["--run-date"] in required
        assert any("--clear-posting-file" in options for options in required)


def test_the_help_text_names_the_deletion_rather_than_burying_it() -> None:
    """The destructive answer says so, in the help an operator reads.

    Not a style assertion: the switch's help is the only place a run's most destructive
    input is explained, and the table it empties is named there by its own identifier so
    that an operator can check the scenario definition against it.
    """
    with _shipped("acas_posting.cli.irs_post") as (route,):
        help_text = route._build_parser().format_help()

        assert "PSIRSPOST-REC" in help_text
        assert "irs/irs030.cbl:L1716" in help_text
        assert "--no-clear-posting-file" in help_text


# ---------------------------------------------------------------------------
#  4.  THE CONFIGURATION CONTRACT'S STATUS CODES
# ---------------------------------------------------------------------------


def test_an_absent_contract_raises_the_frozen_no_source_code() -> None:
    """`move 8 to LK-Return` [common/acas-get-params.cbl:L174-L178].

    The frozen parameter reader answers 8 when there is no source to read, and the
    migrated resolver answers 8 when not one of the six `ACAS_DB_*` variables is set - the
    same refusal over the transport this migration uses. The environment is passed in as
    an empty mapping rather than manipulated, so the test does not depend on the host's own
    variables and cannot leak one.

    ⭐ THE MESSAGE NAMES THE SIX VARIABLES, because the operator's next action is to set
    them; and it carries NO VALUE, because a value could be a password.
    """
    with _shipped("acas_posting.cli.rdbms_params") as (rdbms_params,):
        assert rdbms_params.RDB_RETURN_NO_SOURCE == 8
        assert rdbms_params.RDB_RETURN_OK == 0

        with pytest.raises(rdbms_params.RdbmsParamError) as raised:
            rdbms_params.resolve_rdbms_params({})

        assert raised.value.return_code == rdbms_params.RDB_RETURN_NO_SOURCE
        message = str(raised.value)
        for variable in (
            "ACAS_DB_HOST",
            "ACAS_DB_USER",
            "ACAS_DB_PASSWORD",
            "ACAS_DB_NAME",
            "ACAS_DB_PORT",
            "ACAS_DB_SOCKET",
        ):
            assert variable in message


def test_a_present_contract_resolves_as_the_frozen_reader_would() -> None:
    """The control, and the frozen transformation with it.

    `UNSTRING ... delimited by "=" or ":" or space`
    [common/acas-get-params.cbl:L193-L199] means a value is CUT AT THE FIRST DELIMITER,
    and every bridge then extracts its own item `delimited by space`. So a value with a
    space in it does not fail - it is truncated, exactly as the frozen reader truncates
    it. Reproduced rather than rejected (R-3, R-4): a validation here would refuse a
    deployment the compiled system accepts.
    """
    with _shipped("acas_posting.cli.rdbms_params") as (rdbms_params,):
        resolved = rdbms_params.resolve_rdbms_params(
            {
                "ACAS_DB_HOST": "db.internal",
                "ACAS_DB_USER": "acas",
                "ACAS_DB_PASSWORD": "unused-by-this-test",
                "ACAS_DB_NAME": "ACASDB",
                "ACAS_DB_PORT": "3306",
                "ACAS_DB_SOCKET": "",
            }
        )

        assert resolved.host == "db.internal"
        assert resolved.user == "acas"
        assert resolved.database == "ACASDB"
        assert resolved.port == "3306"
        #  Only the socket may be empty - it means connect over TCP.
        assert resolved.socket == ""

        #  The frozen cut, asserted on the host rather than on the credential.
        cut = rdbms_params.resolve_rdbms_params(
            {"ACAS_DB_HOST": "db.internal extra words"}
        )
        assert cut.host == "db.internal"


def test_the_malformed_code_is_published_and_surfaced_but_never_raised_here() -> None:
    """⚠ 1 IS PART OF THE FROZEN SET AND NO PATH IN THIS MODULE RAISES IT.

    [common/acas-get-params.cbl:L37-L42] publishes four codes, of which the migrated
    resolver can express one: 8, "no source". The malformed code, 1, belongs to the frozen
    reader's `if WS-RDB-Equal not = "="` test [common/acas-get-params.cbl:L200-L203] -
    a keyword terminator that is neither `=` nor `:` - and an environment variable HAS no
    keyword terminator, so the condition cannot arise over this transport.

    THE HONEST STATEMENT OF THAT IS WHAT THIS TEST MAKES: the constant is 1, the boundary
    surfaces whatever code an error carries - so a future path that did raise 1 would be
    reported as 1 without another change - and the resolver's own refusal is 8. Claiming
    coverage of a malformed contract would be claiming a path that does not exist.
    """
    with _shipped("acas_posting.cli.rdbms_params", "acas_posting.cli.args") as (
        rdbms_params,
        args,
    ):
        assert rdbms_params.RDB_RETURN_MALFORMED == 1

        #  The boundary surfaces the code the error carries, whichever it is.
        malformed = rdbms_params.RdbmsParamError(
            rdbms_params.RDB_RETURN_MALFORMED,
            "a keyword terminator that is neither = nor : - the frozen L200-L203 case",
        )
        absent = rdbms_params.RdbmsParamError(
            rdbms_params.RDB_RETURN_NO_SOURCE, "no source"
        )
        assert args.boundary_exit_status(malformed) == 1
        assert args.boundary_exit_status(absent) == 8
        #  An error with no code at all falls back to the smallest status the frozen menu
        #  treats as serious, DERIVED rather than typed [general/general.cbl:L720].
        assert args.boundary_exit_status(RuntimeError("no code")) == (
            args.SERIOUS_ERROR_THRESHOLD + 1
        )


def test_a_configuration_failure_is_reported_as_its_own_status_and_runs_nothing() -> None:
    """`report_configuration_failure` returns the code, and the route returns it too.

    THE ROUTE IS DRIVEN, not the helper alone: `gl_post_cycle.main` catches the binder's
    error and returns the status, so an operator's shell sees 8 for "not configured". The
    binder is replaced with one that raises, which is deterministic - the alternative,
    emptying the process environment, would make the test depend on the host.

    NOTHING WAS RUN: the three program doubles record every dispatch and the list is
    empty. The error is raised while the six connection fields are still being resolved,
    before any database is contacted or any program entered, so a run that reports this
    has changed no table.
    """
    with _shipped("acas_posting.cli.gl_post_cycle", "acas_posting.cli.args") as (
        cycle,
        args,
    ):
        rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")
        dispatched: list[str] = []
        original_bind = args.bind_gl_linkage

        def refuse(*_arguments: object, **_keywords: object) -> object:
            raise rdbms_params.RdbmsParamError(
                rdbms_params.RDB_RETURN_NO_SOURCE,
                "no database connection contract is present in the environment",
            )

        args.bind_gl_linkage = refuse
        try:
            with _programs(cycle, dispatched, term_codes={}):
                status = cycle.main(["--run-date", _RUN_DATE_TEXT])
        finally:
            args.bind_gl_linkage = original_bind

        assert status == rdbms_params.RDB_RETURN_NO_SOURCE
        assert dispatched == []


# ---------------------------------------------------------------------------
#  5.  THE FACADE'S `goback`, ABSORBED AT THE IRS BOUNDARY
# ---------------------------------------------------------------------------


def test_the_irs_route_absorbs_the_facade_goback_as_a_normal_return() -> None:
    """`goback` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] ends the MENU program.

    ⭐ WHY THIS IS REPRODUCED RATHER THAN CAUGHT DEFENSIVELY (R-4). The IRS facade
    convention wraps each handler call in a per-handler error check, and on an
    unrecoverable open failure that check RETURNS FROM THE PROGRAM outright. `irs/irs.cbl`
    copies that same copybook [irs/irs.cbl:L1035], so the `goback` is a disposition of the
    menu program - and the migrated route reproduces it by absorbing `FacadeGoback` and
    returning zero, which is what a `goback` from a menu program yields.

    The General, Sales and Purchase convention has NO such paragraph
    [copybooks/Proc-ACAS-FH-Calls.cob contains none], so their routes do not absorb it -
    a behavioural difference between the two vocabularies rather than a naming one.

    THE NAME PATCHED HERE IS `bind_irs_route`, AND THAT MATTERS. The route binds ONCE,
    through `args.bind_irs_route`, which returns the linkage AND the snapshot its single
    `zz090` pass captured; `args.bind_irs_linkage` is the thin caller that keeps the
    three-operand shape available and delegates to it. Patching the delegate would leave
    the real binder in the route's path, so the run would fail resolving the deployment
    contract and this test would be measuring the wrong boundary.
    """
    with _shipped(
        "acas_posting.cli.irs_post", "acas_posting.cli.args", "acas_posting.dal.facade"
    ) as (route, args, facade):
        original_bind = args.bind_irs_route

        def goback(*_arguments: object, **_keywords: object) -> object:
            raise facade.FacadeGoback(
                "acas000 reported an unrecoverable open failure"
            )

        args.bind_irs_route = goback
        try:
            status = route.main(
                ["--run-date", _RUN_DATE_TEXT, "--no-clear-posting-file"]
            )
        finally:
            args.bind_irs_route = original_bind

        assert status == 0


def test_an_unexpected_failure_at_the_irs_boundary_is_not_absorbed() -> None:
    """Only the two frozen dispositions are handled; everything else propagates.

    Without this, the test above would be indistinguishable from a bare `except
    Exception` - and a boundary that swallowed every failure would report success for a
    run that did nothing. The route handles `FacadeGoback` because it has a frozen
    counterpart and `RdbmsParamError` because it carries a frozen return code; a
    `RuntimeError` has neither, so it reaches the caller.
    """
    with _shipped("acas_posting.cli.irs_post", "acas_posting.cli.args") as (
        route,
        args,
    ):
        original_bind = args.bind_irs_route
        marker = RuntimeError("not a frozen disposition")

        def explode(*_arguments: object, **_keywords: object) -> object:
            raise marker

        args.bind_irs_route = explode
        try:
            with pytest.raises(RuntimeError) as raised:
                route.main(
                    ["--run-date", _RUN_DATE_TEXT, "--no-clear-posting-file"]
                )
        finally:
            args.bind_irs_route = original_bind

        assert raised.value is marker


# ---------------------------------------------------------------------------
#  6.  THE END-OF-CYCLE ROUTE - `load09`, AND ITS THREE PROMOTED ANSWERS
#
#      `general/general.cbl` dispatches `gl080` from `load09.`
#      [general/general.cbl:L817-L820] through the same shared `load00.` block
#      [general/general.cbl:L711-L722]. The route carries the three interactive
#      answers Agent Action Plan section 0.3.4 promotes to parameters, and TWO OF THEM
#      DECIDE WHETHER THE DATABASE IS WRITTEN AT ALL - which is why the route refuses
#      to run until both have been stated.
# ---------------------------------------------------------------------------


class _Gl080Double:
    """`gl080`, recording the linkage and the three promoted answers it received.

    Attributes:
        calls: One entry per dispatch, as the keyword answers it was handed.
    """

    def __init__(self, log: list[dict[str, object]], *, term_code: int = 0) -> None:
        self._log = log
        self._term_code = term_code

    def run(
        self,
        ws_calling_data: Any,
        system_record: Any,
        to_day: str,
        file_defs: Any,
        /,
        *,
        run_confirmed: bool = True,
        disk_change_option: int = 0,
        archive_path_override: str | None = None,
        dal_options: Any = None,
    ) -> None:
        self._log.append(
            {
                "called": ws_calling_data.ws_called.strip(),
                "to_day": to_day,
                "run_confirmed": run_confirmed,
                "disk_change_option": disk_change_option,
                "archive_path_override": archive_path_override,
            }
        )
        ws_calling_data.ws_term_code = self._term_code


def test_the_end_of_cycle_route_hands_gl080_the_three_promoted_answers() -> None:
    """`load09` -> `load00` -> `gl080.run` [general/general.cbl:L817-L820].

    THE ROUTE IS DRIVEN, and what it forwards is asserted item by item, because each of
    the three answers changes what the program writes:

      `run_confirmed`          False returns before a single write
                               [general/gl080.cbl:L299-L302]
      `disk_change_option`     9 suppresses archiving AND end-of-period through the
                               shared `a` [general/gl080.cbl:L545], [general/gl080.cbl:L324]
      `archive_path_override`  moves where the flat archive rows are written
                               [general/gl080.cbl:L555]

    The program id and the run date are asserted with them: `set_called` moves the
    program name into `WS-Called` [copybooks/wscall.cob:L7] before the dispatch, and the
    run date is the text date the CLI pinned - never a clock (R-6).
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        original = route.gl080
        route.gl080 = _Gl080Double(dispatched)
        try:
            linkage = _gl_linkage(args)
            term_code = route.load09(
                linkage,
                menu_state=args.general_menu_state(),
                run_confirmed=False,
                disk_change_option=9,
                archive_path_override="/var/spool/acas-archive.dat",
            )
        finally:
            route.gl080 = original

        assert term_code == 0
        assert dispatched == [
            {
                "called": "gl080",
                "to_day": _RUN_DATE_TEXT,
                "run_confirmed": False,
                "disk_change_option": 9,
                "archive_path_override": "/var/spool/acas-archive.dat",
            }
        ]


def test_a_serious_error_from_gl080_is_returned_and_persists_the_records() -> None:
    """`if ws-term-code > 7` [general/general.cbl:L720-L721], on the end-of-cycle route.

    `gl080` NEVER SETS A TERM CODE of its own - it returns [general/gl080.cbl:L366] where
    `gl070` raises 5 - so this arm is reached only when something below it does. It is
    asserted anyway, because `load00` is shared with the posting-cycle route and a change
    to the shared block would otherwise be caught on one route only.
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        persisted: list[object] = []
        original_program = route.gl080
        original_overrewrite = args.overrewrite
        route.gl080 = _Gl080Double(dispatched, term_code=_SERIOUS_THRESHOLD + 1)
        args.overrewrite = lambda *arguments, **keywords: persisted.append(arguments)
        try:
            linkage = _gl_linkage(args)
            term_code = route.load09(
                linkage,
                menu_state=args.general_menu_state(),
                run_confirmed=True,
                disk_change_option=0,
                archive_path_override=None,
            )
        finally:
            route.gl080 = original_program
            args.overrewrite = original_overrewrite

        assert term_code == _SERIOUS_THRESHOLD + 1
        assert args.exit_status_for(term_code) == term_code
        assert len(persisted) == 1


@pytest.mark.parametrize(
    "argv",
    [
        #  Neither destructive answer stated.
        ["--run-date", _RUN_DATE_TEXT],
        #  The confirm stated, the disk-change option not.
        ["--run-date", _RUN_DATE_TEXT, "--run-confirmed"],
        #  The disk-change option stated, the confirm not.
        ["--run-date", _RUN_DATE_TEXT, "--disk-change-option", "0"],
    ],
)
def test_the_end_of_cycle_route_refuses_until_both_answers_are_stated(
    argv: list[str],
) -> None:
    """⭐⭐ TWO ANSWERS DECIDE WHETHER POSTED TRANSACTIONS ARE DELETED.

    `--disk-change-option 0` proceeds, which deletes posted transactions, stamps every
    batch, rolls the ledger quarters over and increments the accounting cycle; 9 aborts
    and leaves the three tables as the seed left them. `--run-confirmed` decides whether
    the run happens at all. So the route requires BOTH to be stated explicitly, and an
    omission of either is argparse's usage error - status 2, indistinguishable from an
    omitted `--run-date`.

    ⛔ NOT A VALIDATION OF THE ANSWER (R-3). Both values are equally acceptable and
    neither is rejected; what is refused is SILENCE. Rejecting one of them would be a
    check the frozen program has not got, and defaulting either would answer a
    destructive question on the operator's behalf.

    NOTHING IS DISPATCHED: the double records every call and the list is empty, because
    `require_stated` runs after parsing and before anything is bound, connected or
    dispatched.
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        original = route.gl080
        route.gl080 = _Gl080Double(dispatched)
        try:
            with pytest.raises(SystemExit) as exited:
                route.main(argv)
        finally:
            route.gl080 = original

        assert exited.value.code == _USAGE_ERROR_STATUS
        assert dispatched == []


def test_the_end_of_cycle_refusal_names_what_each_answer_decides(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The refusal quotes the consequence, so an operator is told what they are choosing.

    `require_stated` puts each requirement's sentence into the message verbatim
    [acas_posting/cli/args.py], and the two sentences name the frozen lines and the three
    tables the destructive answer reaches. Asserted on the message rather than on the
    status, because the status alone tells an operator nothing about which answer is
    missing.
    """
    with _shipped("acas_posting.cli.gl_end_of_cycle", "acas_posting.cli.args") as (
        route,
        args,
    ):
        dispatched: list[dict[str, object]] = []
        original = route.gl080
        route.gl080 = _Gl080Double(dispatched)
        try:
            with pytest.raises(SystemExit):
                route.main(["--run-date", _RUN_DATE_TEXT])
        finally:
            route.gl080 = original

        message = capsys.readouterr().err
        assert "--run-confirmed" in message
        assert "--disk-change-option" in message
        #  The frozen locators, so the operator can read the statement being answered.
        assert "general/gl080.cbl:L295-L302" in message
        assert "general/gl080.cbl:L542-L549" in message
        #  And the three tables the proceeding answer reaches.
        for table in ("GLPOSTING-REC", "GLBATCH-REC", "GLLEDGER-REC"):
            assert table in message
        assert dispatched == []


# ---------------------------------------------------------------------------
#  MN-08 - THE PUBLIC CONTRACT HOLDS EACH NAME EXACTLY ONCE
#
#  `acas_posting.cli.args.__all__` is grouped by theme with explanatory comments, and
#  several of the menu paragraphs it publishes belong to more than one theme. A tuple is
#  not a set, so re-listing one under a second heading is a genuine duplicate in the
#  module's public contract - and an invisible one, because a duplicate in `__all__`
#  raises nothing, simply binding the name twice under `import *`. Seven names were
#  duplicated: `len(__all__)` read 72 against 65 distinct.
#
#  The module asserts this at import too. This test exists because that assert is
#  stripped under `python -O`, and because a test states the property where a reviewer
#  looks for properties.
def test_cli_args_publishes_each_public_name_once() -> None:
    """`args.__all__` holds no repeated entry, and exports nothing it lacks."""
    from acas_posting.cli import args

    names = list(args.__all__)
    repeated = sorted({name for name in names if names.count(name) > 1})
    assert not repeated, (
        f"acas_posting.cli.args.__all__ lists {len(names)} entries with only "
        f"{len(set(names))} distinct names. Repeated: {', '.join(repeated)}. "
        "A duplicate binds the name twice under `import *` and makes any count of the "
        "public surface wrong (MN-08)."
    )

    # A deduplication that dropped a name would be a silent narrowing of the public
    # surface, so every listed name must still resolve on the module.
    absent = sorted(name for name in names if not hasattr(args, name))
    assert not absent, (
        "acas_posting.cli.args.__all__ names attributes the module does not define, so "
        f"`from acas_posting.cli.args import *` would fail: {', '.join(absent)}"
    )

    # The seven names the duplication involved must still be exported - removing one
    # rather than deduplicating it would also make the count agree.
    formerly_duplicated = (
        "RDBMS_STORE_SELECTOR_DIGIT",
        "SYSTEM_FILE_KEY_DEFAULTS",
        "SYSTEM_FILE_KEY_PARAMS",
        "SYSTEM_FILE_KEY_TOTALS",
        "aa010_get_system_recs",
        "overrewrite",
        "zz095_restore_irs_system_data",
    )
    lost = sorted(name for name in formerly_duplicated if name not in names)
    assert not lost, (
        "these names were published twice and are now published zero times, which "
        f"narrows the public surface rather than tidying it: {', '.join(lost)}"
    )


def test_cli_args_import_star_binds_every_published_name() -> None:
    """`import *` succeeds and binds exactly the published set (MN-08).

    Exercises the contract the way a consumer would, so a `__all__` entry that names
    something unimportable is caught as the ImportError it would really be.
    """
    namespace: dict[str, Any] = {}
    exec("from acas_posting.cli.args import *", namespace)  # noqa: S102

    from acas_posting.cli import args

    bound = {name for name in namespace if not name.startswith("__")}
    assert bound == set(args.__all__), (
        "the names `import *` bound differ from `__all__`:\n"
        f"  only bound    : {sorted(bound - set(args.__all__))}\n"
        f"  only in __all__: {sorted(set(args.__all__) - bound)}"
    )


# ---------------------------------------------------------------------------
#  MN-05 - THE CLEAR ANSWER HAS NO DEFAULT, AND NOTHING SAYS IT DOES
#
#  `EOJ-q1` displays "Can I clear the Ledgers Posting file? [Y]"
#  [irs/irs030.cbl:L1716] and that `[Y]` looks like a default. It is not one: the accept
#  on the next line carries no `WITH UPDATE`, so the literal never reaches the field;
#  `WS-Reply pic x` is never set to "Y" anywhere in the program; and L1718-L1719 send
#  anything that is neither `Y` nor `N` back to the prompt, so a bare Enter RE-PROMPTS.
#
#  Answering `Y` reaches `acas008-Open-Output`, which for that handler DELETES EVERY ROW
#  of `PSIRSPOST-REC` [common/acas008.cbl:L313-L319]. So a default would not merely be
#  wrong, it would be the destructive answer applied to an operator who said nothing -
#  which is why the seam requires the answer, and why prose claiming otherwise is worth
#  a test rather than a correction alone. Three comment sites still claimed a `True`
#  default after the seam had stopped having one.
def test_the_clear_answer_is_required_at_both_layers() -> None:
    """Neither the program module nor the CLI can be driven without the answer."""
    import inspect

    from acas_posting.programs.irs030_posting import run

    parameter = inspect.signature(run).parameters["clear_posting_file"]
    assert parameter.default is inspect.Parameter.empty, (
        "irs030_posting.run gives clear_posting_file the default "
        f"{parameter.default!r}. The frozen prompt has no default -- the [Y] at "
        "[irs/irs030.cbl:L1716] is prompt text, the accept carries no WITH UPDATE, and "
        "L1718-L1719 re-prompt on anything but Y or N -- so a default here invents one, "
        "and answering Y deletes every row of PSIRSPOST-REC (MN-05, finding CLI-05)."
    )
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
        "clear_posting_file must stay keyword-only so a caller cannot supply the "
        "destructive answer positionally by accident."
    )


def test_no_module_claims_the_clear_answer_defaults_on() -> None:
    """No comment or docstring says clearing is on by default (MN-05).

    Read as text on purpose: the defect was prose disagreeing with the code, so the
    code assertion above cannot catch it and did not.
    """
    root = Path(__file__).resolve().parents[2]
    # Phrases that assert a live default. A sentence EXPLAINING that an earlier draft
    # had one, or that the file brief specifies one the module declines, is the
    # historical record and is not a claim about the seam - so those are exempted by
    # requiring the phrase to appear without a disclaiming neighbour on the same line.
    claims = (
        "on by default",
        "does default to `True`",
        "default is [Y]",
        "frozen default is [Y]",
        "defaults to clearing",
    )
    exempt = ("previous default", "was wrong", "invented", "brief gives", "brief also gives")

    offenders: list[str] = []
    for relative in (
        "acas_posting/cli/irs_post.py",
        "acas_posting/cli/args.py",
        "acas_posting/programs/irs030_posting.py",
    ):
        path = root / relative
        assert path.is_file(), f"a declared consumer is absent: {path}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            lowered = line.lower()
            if any(word in lowered for word in exempt):
                continue
            for claim in claims:
                if claim.lower() in lowered:
                    offenders.append(f"{relative}:{number}: {line.strip()[:92]}")
    assert not offenders, (
        "these lines claim the transfer-file clear defaults on, while the seam requires "
        "an explicit Y or N and the frozen prompt has no default at all (MN-05):\n  "
        + "\n  ".join(offenders)
    )
