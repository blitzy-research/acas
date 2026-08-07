"""THE END OF CYCLE - the one in-scope program no scenario had ever run.

Scenario `end_of_cycle_gl`, subsystem `general`, operation `gl_end_of_cycle`,
declared terminal status `expected_status: [0]`. It drives the full parity protocol
and asserts an EMPTY ordering-normalised diff across five bounded tables.

WHY THIS FILE EXISTS. Eight scenarios drove the posting cycle, the two trading
ledgers and the IRS fan-out. Not one of them ran `gl080`. So posting deletion, batch
stamping, the nominal-ledger quarter rollover and the cycle advance were carried by
arithmetic tests alone, with no state comparison behind them at all - and `gl080`
owns one of the FIVE `ROUNDED` stores in the whole migration
[general/gl080.cbl:L328], the only one of the five that a scenario can reach. The
other four are inside VAT computations [general/gl051.cbl:L791],
[general/gl051.cbl:L796], [irs/irs030.cbl:L1551], [irs/irs030.cbl:L1562] whose
results land in tables the General Ledger routes never touch.

It drives the REAL route. `gl_end_of_cycle` is general/general.cbl `load09.`
(L817-L821) dispatching `gl080` through the shared four-parameter `load00.`
(L711-L721). Both runners already implemented the operation - `acas_plan_gl_end_of_cycle`
in harness/run_cobol_scenario.sh and the `gl_end_of_cycle` row of
`ACAS_PY_OPERATION_MAP` in harness/run_python_scenario.sh - so what was missing was
never runner support. It was a scenario and this file.

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none
was provided, so there is no on-disk rules file and no reader should look for one.
The six binding rules R-1 to R-6 live in the Agent Action Plan itself, section
0.7.2. Summarised in this file's own words, and each named at the site that honours
it:

    R-1  No COBOL at runtime. This file NEVER imports `harness`; every harness
         module and runner is reached through tests/conftest.py's fixtures.
    R-2  Zero binary floating point. No float, no tolerance, no epsilon, no
         approximate comparison. Every dumped value is a `str` or an `int` and
         every comparison is `==` after a type check.
    R-3  No new validations, fields or schema changes; no concurrency. Nothing here
         asserts that a bounds check exists on the quarter subscript, and none may
         be added - see A-2 below. Strictly sequential.
    R-4  Legacy anomalies are reproduced, never fixed. TWO are asserted here as
         POSITIVE facts about the state, not merely described: A-3, the two
         disagreeing notions of the current quarter, and N-EDIT, the bridge's
         structural inability to render a minus sign. Each has a test whose
         failure means the anomaly stopped being reproduced.
    R-5  Full traceability. Every claim carries an inline `[<path>:L<n>]` citation.
    R-6  Compiled behaviour is the tie-breaker. An empty normalised diff is the
         pass condition; a diff that could not be performed is an ERROR, never a
         pass.

Where the Agent Action Plan is silent, enterprise-standard best practice applies.

-------------------------------------------------------------------------------
THE INVERTED PREMISE, AND WHAT IT FORBIDS
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.2, verbatim:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a defect
    fixed is a failure."

So no test below recomputes a balance, asserts that debits equal credits, or
predicts a value from the accounting meaning of the run. What the named tests DO
assert is the SHAPE of the mutation - which column moved and which did not - and
they assert it IDENTICALLY ON BOTH SIDES, reading the two normalised dumps the
protocol produced. That is a statement about observed behaviour, which is
permitted, rather than about correct accounting, which is not.

-------------------------------------------------------------------------------
WHY THE RUN REACHES PHASE 5, AND WHY THAT TOOK FOUR PINS
-------------------------------------------------------------------------------

`gl080` has five labelled phases that do not execute in labelled order, and four
separate conditions gate the last of them. A scenario that fell out early would
look exactly like a passing scenario while proving almost nothing, so
`test_every_pin_that_reaches_phase_five` asserts all four explicitly:

    1  THE BACKUP GATE. GL085/GL086/GL087 then an accept
       [general/gl080.cbl:L295-L302]. Escape, "A" or "a" means goback and NOTHING
       is written. `gl080_proceed: "Y"` sends the bare Return that reproduces the
       program's own `move space to keyed-reply` default.
    2  PHASE 1 MUST FIND NO UNFINISHED BATCH. `gl080a` sets `a` to 1 for any
       record of the current cycle that is `not status-closed and not processed`
       [general/gl080.cbl:L368-L392]; `a = 1` means GL088, GL012 and main-end.
       Batch 1 is seeded CLOSED and PROCESSED.
    3  ARCHIVING MUST BE OFF. `if archiving` [general/gl080.cbl:L315] selects
       Phase 2, which writes to a SEQUENTIAL ARCHIVE FILE outside the schema that
       no table dump can observe. `Arch` is a space - `88 Archiving value "Y"`
       [copybooks/wssystem.cob:L164-L165] - so Phase 3 runs instead and the
       evidence stays inside the comparison.
    4  THE PERIOD BOUNDARY MUST FALL EXACTLY HERE. `divide scycle by period
       giving a rounded` [general/gl080.cbl:L328] then `multiply a by period
       giving y` [general/gl080.cbl:L329], and only `scycle = y` survives. With
       period 1 and cyclea 1, `a` is 1 and `y` is 1.

PHASE 4 IS SKIPPED, and that is frozen behaviour rather than a choice:
`compress-post` opens with `if not FS-Cobol-Files-Used go to main-exit`, and
`file_system_used` is 1. Worth stating because the section it skips contains a
`stop run`, so a reader who assumed Phase 4 ran would expect a work file this run
never opens.

-------------------------------------------------------------------------------
THE TWO ANOMALIES THIS FILE PINS
-------------------------------------------------------------------------------

A-3 - TWO DISAGREEING NOTIONS OF THE CURRENT QUARTER. `gl080` computes a subscript
`a` from the divide at [general/gl080.cbl:L328] and separately maintains a rotating
counter `current-quarter` at [general/gl080.cbl:L345-L357]. Nothing reconciles
them. The seed sets `current-quarter` to 4 while `a` computes to 1, so Phase 5
writes each balance into `ledger-q (1)` - because the subscript says 1 - and ALSO
into `Ledger-Last` - because the counter says 4 - and leaves Q4, which the counter
names, untouched. `Ledger-Q pic s9(8)v99 comp-3 occurs 4` redefines Q1..Q4
[copybooks/wsledger.cob:L30-L36]. A migration that had "helpfully" used one value
for both would write Q4 instead of Q1, or would skip `Ledger-Last` entirely, and
`test_phase_five_wrote_q1_and_ledger_last_and_left_q2_q3_q4` fails on either.

A-2 - THE UNBOUNDED SUBSCRIPT is NOT exercised here, deliberately, and that is
recorded rather than left to inference. `move ledger-balance to ledger-q (a)`
[general/gl080.cbl:L345] has no bounds check, so a period and cycle that made `a`
exceed 4 would index past a four-element table. Driving that through the COMPILED
oracle would be an out-of-range write into adjacent storage whose effect is
undefined and unreproducible, which is precisely why AAP section 0.6.8 keeps such
questions in the arithmetic tier: tests/arithmetic covers the unbounded index
against the migrated primitive, and this scenario keeps `a` at 1. Nothing here
asserts that a bounds check exists, because adding one would breach R-3 and R-4.

N-EDIT - THE BRIDGE CANNOT RENDER A MINUS SIGN. Every bridge builds its SQL text by
MOVEing the host variable into `01 WS-MYSQL-EDIT PIC -Z(18)9.9(9).`
[common/nominalMT.cbl:L232] and then slicing digit windows out of it - `TRIM
(WS-MYSQL-EDIT(13:08))` for the integer part and `WS-MYSQL-EDIT(22:02)` for the
pence [common/nominalMT.cbl:L1074-L1086]. The sign occupies POSITION 1 and every
window starts at position 3 or later, so the sign is structurally unreachable. This
is NOT a copybook or column narrowing: `Ledger-Balance pic s9(8)v99 comp-3`
[copybooks/wsledger.cob:L28], `HV-LEDGER-BALANCE PIC S9(08)V9(02) COMP`
[common/nominalMT.cbl:L300] and `LEDGER-BALANCE decimal(10,2)` are all SIGNED. The
loss happens in the statement text, before any SQL executes - the same class as AAP
section 0.6.7 entry 11. The migrated side reproduces it on purpose
(`EDIT_FIELD_SIGN_IS_NEVER_RENDERED` in acas_posting/dal/acas005_gl_nominal.py), so
`test_anomaly_n_edit_still_drops_the_seeded_sign` is a standing check that the
reproduction is in force: a "helpful" fix that preserved the sign would make this
test fail.

-------------------------------------------------------------------------------
ONE RUN, MANY ASSERTIONS
-------------------------------------------------------------------------------

Every assertion below is a statement about ONE run's evidence, so the protocol is
driven once per module and the result is held in a module-lifetime cache. Running
it per assertion would seed, drive the oracle, dump, reset, drive the Python cycle,
dump and compare once per test against ONE shared database - which would make the
tests look independent when every one of them reads the same rows.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
#  THE SCENARIO, AND THE FACTS THIS FILE IS ABOUT.
#
#  Each constant restates something the scenario file declares, so that a scenario
#  edited into a different shape fails a NAMED test here rather than silently
#  changing what the parity verdict means.
# ---------------------------------------------------------------------------

# THE TIER MARK. `pytest -m scenario` is the documented way to select the state-parity
# tier, so a scenario file that carries no mark is invisible to the very command the
# documentation tells a reader to run. Only `scenario` is applied at module level: four
# tests below read nothing but the scenario file on disk and pass on a bare host, so a
# module-level `database`/`oracle` mark would claim they need a MariaDB and a built
# oracle. Those two marks are applied per test, on the seven that genuinely need the
# stack. This mirrors the convention in the other eight scenario files exactly.
pytestmark = pytest.mark.scenario

SCENARIO = "end_of_cycle_gl"

#: Tables that must come back WITH ROWS. `assert_non_vacuous` uses this: five tables
#: that agree because all five are empty would agree perfectly and prove nothing.
#: GLPOSTING-REC belongs here even though a reading of the source says Phase 3
#: deletes its row - see `test_phase_three_delete_walk_deletes_nothing`, which is the
#: measured finding this scenario produced.
SEEDED_TABLES = (
    "GLBATCH-REC",
    "GLLEDGER-REC",
    "GLPOSTING-REC",
    "SYSTEM-REC",
)

#: The batch key Phase 3 stamps, and the one it must leave alone. Both are composed
#: the way the frozen key is: `WS-Ledger pic 9` then `WS-Batch-Nos pic 9(5)`
#: [copybooks/wsbatch.cob:L15-L20], so batch 1 of the General Ledger is 100001.
BATCH_IN_CYCLE = 100001
BATCH_OTHER_CYCLE = 100002

#: The primary-key value EVERY GLPOSTING row carries, whatever rrn the seed
#: declares. ANOMALY N-RRN: the bridge's load paragraph moves thirteen fields
#: [common/glpostingMT.cbl:L1053-L1066] and never moves `WS-Post-rrn` into
#: `HV-POST-RRN` [common/glpostingMT.cbl:L282], so the host variable keeps the zero
#: `initialize` left it and POST-RRN - the primary key - is always 0. This is why
#: the scenario seeds exactly ONE posting: a second would collide on the key.
POSTING_RRN_UNDER_N_RRN = 0

#: The nominal account seeded with a NEGATIVE balance, for N-EDIT. `LEDGER-KEY` is
#: the scaled form: account 2000 with pc 0 becomes 200000.
LEDGER_KEY_SEEDED_NEGATIVE = 200000

#: What the seed declares, and what the run must leave behind. Held as strings
#: because that is what the dump holds for a `decimal` column - never a float (R-2).
SEEDED_QUARTERS = {
    100000: ("11.00", "22.00", "33.00", "44.00"),
    200000: ("111.00", "222.00", "333.00", "444.00"),
    220000: ("1111.00", "2222.00", "3333.00", "4444.00"),
}


# ---------------------------------------------------------------------------
#  THE ONE RUN.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _parity_cache() -> dict[str, object]:
    """A module-lifetime holder for the one parity run this file's assertions read.

    A module-scoped fixture cannot request `protocol`, which is function-scoped by
    design so that a bare host gets a precise SKIP per test rather than a
    session-wide error. So the cache is module-scoped and the run that fills it is
    function-scoped. A plain dict is correct: execution is strictly sequential
    (R-3), so there is no race to guard.

    Returns:
        An empty mapping on first use, then the same mapping for the module.
    """
    return {}


@pytest.fixture
def parity(protocol: object, _parity_cache: dict[str, object]) -> object:
    """Drive every protocol stage for this scenario ONCE and return the verdict.

    Args:
        protocol: tests/conftest.py's stage bundle. It applies the stack skip, so
            an unusable harness is a SKIP and never an error.
        _parity_cache: The module-lifetime holder.

    Returns:
        The `ParityRun`: every stage result in execution order, both run stages,
        the diff outcome and the artifact paths. `is_empty` is the pass condition.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed, or
            the comparison could not be performed. A pytest ERROR, never a pass.
    """
    if "run" not in _parity_cache:
        _parity_cache["run"] = protocol.run_scenario_parity(SCENARIO)
    return _parity_cache["run"]


@pytest.fixture
def dumps(parity: object, harness: object) -> dict[str, dict[str, object]]:
    """`{side: {table: dump}}` from the two NORMALISED trees the run produced.

    Neither the side labels nor the table list is written down locally: the sides
    come from harness/dump_tables.py's own `SIDES` and the tables from the
    scenario's declared affected-table list, which is how a comparison is bounded.

    Args:
        parity: The completed run, for its artifact paths and bounded table list.
        harness: The harness modules, loaded by explicit file path through conftest.
            The harness package is NEVER imported by name (R-1).

    Returns:
        The two sides' dumps, keyed by the harness's own side labels.

    Raises:
        Exception: harness/diff_states.py's own errors - a missing table file, an
            unreadable dump, a duplicate key, a null or a float. All are harness
            faults and pytest ERRORs.
    """
    diff_states = harness.diff_states
    out: dict[str, dict[str, object]] = {}
    for side in harness.dump_tables.SIDES:
        tree = parity.paths.normalized_dir(side)
        out[side] = {
            table: diff_states.load_dump(tree / diff_states.dump_filename(table))
            for table in parity.tables
        }
    return out


def _rows_by_key(dump: object) -> dict[object, dict[str, object]]:
    """Project one dump into `{primary key: {column: value}}`.

    A LOCALISER, NOT A COMPARATOR. The authoritative comparison is the diff stage
    and there is exactly one of it. This exists so a named assertion can say which
    COLUMN carries the property it is about instead of restating the verdict. It
    reads the dump's own `columns` and `primary_key`, so no ordinal and no key name
    is hard-coded here.

    Args:
        dump: One parsed dump object.

    Returns:
        The rows, keyed by primary-key value.
    """
    columns = list(dump["columns"])
    key_index = columns.index(dump["primary_key"])
    return {row[key_index]: dict(zip(columns, row)) for row in dump["rows"]}


# ---------------------------------------------------------------------------
#  THE PRECONDITIONS. No stack needed: a scenario definition is a file on disk, so
#  these collect and RUN on a bare host and fail loudly if the scenario is ever
#  edited into something that no longer reaches Phase 5.
# ---------------------------------------------------------------------------


def test_every_pin_that_reaches_phase_five(scenario_loader: object) -> None:
    """All four gating conditions, asserted rather than assumed.

    THE FALSE-PASS TRAP THIS CLOSES. Any one of these four pins, changed, makes
    `gl080` return early - and an early return still produces two dumps that agree,
    so the parity verdict alone cannot tell the difference between "the end-of-cycle
    ran and matched" and "the end-of-cycle declined to run, twice".

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`.
    """
    definition = scenario_loader(SCENARIO)

    assert definition["name"] == SCENARIO
    assert definition["subsystem"] == "general"
    assert definition["operation"] == "gl_end_of_cycle"
    assert definition["operations"] == [
        "gl_end_of_cycle"
    ], "this file is about one operation; a second would change what the diff means"

    # PIN 1 -- the backup gate is passed. "A" would goback before any write.
    assert definition["gl080_proceed"] == "Y", (
        "gl080_proceed must be Y; A aborts at [general/gl080.cbl:L295-L302] and "
        "gl080 then writes nothing at all"
    )

    system = definition["system"]

    # PIN 3 -- archiving off, so Phase 3 runs and the evidence stays in the schema.
    # Declared by ABSENCE of "Y": the switch is `Arch pic x` with `88 Archiving
    # value "Y"` [copybooks/wssystem.cob:L164-L165].
    seeded = definition["seed_records"]["system.dat"]["1"][0]
    assert seeded["Arch"] == " ", (
        "Arch must be a space so `if archiving` [general/gl080.cbl:L315] is FALSE. "
        "Phase 2 writes to a sequential archive file no table dump can observe."
    )

    # PIN 4 -- the period boundary falls exactly here: a = scycle/period = 1 and
    # y = a*period = 1, so `if scycle not = y go to main-end` does not fire.
    assert int(seeded["Cyclea"]) == 1
    assert int(seeded["Period"]) == 1
    assert int(system["cyclea"]) == 1
    assert int(system["period"]) == 1

    # A-3 is only OBSERVABLE because the counter disagrees with the subscript.
    assert int(seeded["Current-Quarter"]) == 4, (
        "Current-Quarter must be 4 so that Ledger-Last is written and the counter "
        "wraps 4 -> 5 -> 1, while the subscript computes to 1. Anomaly A-3 is "
        "visible in table state only when the two disagree."
    )

    # Phase 4 is skipped, and this is the field that skips it.
    assert int(system["file_system_used"]) == 1, (
        "file_system_used must be 1: compress-post returns immediately on "
        "`if not FS-Cobol-Files-Used`, and the section it skips contains a stop run"
    )


def test_phase_one_cannot_find_an_unfinished_batch_in_the_cycle(
    scenario_loader: object,
) -> None:
    """PIN 2, and the proof that the cycle filter is what protects the run.

    `gl080a` sets `a` to 1 for any record of the CURRENT cycle that is `not
    status-closed and not processed` [general/gl080.cbl:L368-L392]. Batch 1 is
    closed and processed so it cannot trip that. Batch 2 IS open and waiting, in
    another cycle - seeded that way on purpose, so that `if bcycle not = scycle go
    to loop` is what keeps `a` at zero. If that filter were ever lost, `a` would
    become 1 and this whole scenario would produce a visibly different state.

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`.
    """
    batches = scenario_loader(SCENARIO)["seed_records"]["batch.dat"]
    assert len(batches) == 2

    in_cycle = next(b for b in batches if int(b["Bcycle"]) == 1)
    assert int(in_cycle["Batch-Status"]) == 1, "88 Status-Closed value 1"
    assert int(in_cycle["Cleared-Status"]) == 1, "88 Processed value 1"

    other = next(b for b in batches if int(b["Bcycle"]) != 1)
    assert int(other["Batch-Status"]) == 0, (
        "the other-cycle batch must be OPEN, so that only the bcycle filter "
        "prevents Phase 1 from raising a=1"
    )
    assert int(other["Cleared-Status"]) == 0, "88 Waiting value 0"


def test_affected_tables_are_in_scope_sorted_and_bound_the_comparison(
    scenario_loader: object, in_scope_table_names: object
) -> None:
    """The five tables, and why SYSTOT-REC is not a sixth.

    This list is the scenario's declared effect and the comparison is bounded by all
    22 in-scope tables - harness/diff_states.py
    carries no ignore-list, no tolerance list and no known-difference allowance - so
    the list IS the statement of what was verified.

    SYSTEM-REC is present, and it has to be: `gl080` ends at `main-end. goback.` and
    contains no System facade verb, so the cycle advance and the quarter wrap live in
    the LINKAGE record and are persisted by the menu exit
    [general/general.cbl:L656-L692], which the headless route reproduces as
    `args.overrewrite`. Without SYSTEM-REC in this list, the entire observable result
    of Phase 5's counter arithmetic would leave no trace in the comparison.

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`.
        in_scope_table_names: The 22 in-scope table names from the harness itself.
    """
    tables = scenario_loader(SCENARIO)["affected_tables"]

    assert tables == sorted(set(tables)), "sorted and unique, as every scenario is"
    for table in tables:
        assert table in tuple(in_scope_table_names), (
            f"{table} is not one of the 22 in-scope tables"
        )

    assert "SYSTEM-REC" in tables, (
        "SYSTEM-REC carries the ONLY record of the cycle advance and the quarter "
        "wrap, because gl080 writes neither itself"
    )
    assert "GLLEDGER-REC" in tables, "Phase 5 rewrites every nominal row"
    assert "GLPOSTING-REC" in tables, "Phase 3 deletes the cycle's postings"
    assert "GLBATCH-REC" in tables, "Phase 3 stamps the cycle's batches"
    assert "SYSTOT-REC" not in tables, (
        "excluded, and argued in the scenario file rather than configured in the "
        "differ: the menu sources System-Record-4 from the COBOL flat file alone "
        "[general/general.cbl:L402-L404] with the RDB read commented out at L434-L436, "
        "so with only the RDB seeded its exit returns sys4LD's four-spare sentinel "
        "[common/sys4LD.cbl:L368-L390] from 1.00 to 0.00. No in-scope program writes "
        "SYSTOT-REC on a General route."
    )


def test_the_scenario_declares_a_changed_effect(scenario_loader: object) -> None:
    """`changed`, not `unchanged` - this is the only GL scenario that rewrites.

    Three of the five listed tables change. Declaring `unchanged` would make both
    runners assert the opposite of what happens, so this pins the declaration.

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`.
    """
    definition = scenario_loader(SCENARIO)
    assert definition["expected_table_effect"] == "changed"
    assert definition["expected_status"] == [0], (
        "gl080 sets no term code at all, which is why the gl_end_of_cycle route - "
        "unlike gl_post_cycle - has no term-code gate between its steps"
    )


# ---------------------------------------------------------------------------
#  THE VERDICT, AND THE NAMED FACTS BEHIND IT.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_end_of_cycle_state_parity(parity: object, protocol: object) -> None:
    """THE PASS CONDITION: an empty ordering-normalised diff over five tables.

    Args:
        parity: The completed run.
        protocol: The stage bundle, for its bound and disposition assertions.
    """
    assert tuple(parity.tables) == protocol.affected_tables(SCENARIO), (
        f"{SCENARIO}: the comparison was bounded by {list(parity.tables)} while the "
        f"scenario declares {list(protocol.affected_tables(SCENARIO))}."
    )

    protocol.assert_declared_statuses(
        parity,
        operations=tuple(protocol.definition(SCENARIO)["operations"]),
        declared=list(protocol.definition(SCENARIO)["expected_status"]),
        reference_only=True,
    )
    protocol.assert_seed_fingerprints_agree(parity)

    # SOMETHING WAS THERE TO COMPARE. Five empty tables agree perfectly.
    protocol.assert_non_vacuous(parity, tables_requiring_rows=SEEDED_TABLES)

    assert parity.is_empty, (
        f"{SCENARIO}: the two states differ. A non-empty diff is a real behavioural "
        f"difference, never an artefact of the comparison (AAP 0.6.6). Differing "
        f"tree: {parity.tree}"
    )


@pytest.mark.database
@pytest.mark.oracle
def test_phase_three_delete_walk_deletes_nothing(
    dumps: dict[str, dict[str, object]], scenario_loader: object
) -> None:
    """THE FINDING THIS SCENARIO PRODUCED: `del-process` deletes nothing.

    A reading of the source says otherwise. `del-process` walks the posting file and
    deletes every row of the closing cycle's batch, and the scenario seeds exactly
    such a row. MEASURED, on both sides: the row is still there afterwards, byte for
    byte.

    THE CHAIN, all of it inside the frozen bridge:

      WRITE  `move WS-Post-Key to HV-POST-KEY` [common/glpostingMT.cbl:L1054].
             WS-Post-Key is a GROUP of two `pic 9(5)` items
             [copybooks/wspost.cob:L14-L16]; HV-POST-KEY is `PIC 9(18) COMP`
             [common/glpostingMT.cbl:L283]. A group move carries the digit
             CHARACTERS, not the number, so batch 1 / post-number 1 - "0000100001" -
             lands in the column as a large unrelated integer.
      READ   `move HV-POST-KEY to WS-Post-Key` [common/glpostingMT.cbl:L1085] runs
             that backwards, so `batch` returns as digits of that integer and not
             as 1.
      SKIP   `if WS-Post-Key = zero or batch not = WS-Batch-Nos go to loop`. The key
             is not zero, but `batch` no longer equals the batch record's
             WS-Batch-Nos, so every row is skipped.

    WHY THIS TEST IS SHAPED AS AN ASSERTION AND NOT AS A NOTE. Rule R-4: a defect
    reproduced is correct and a defect fixed is a failure. If either side ever
    started deleting the row, that would be the anomaly fixed, and this test is what
    turns it red. It asserts the posting is IDENTICAL TO THE SEED, not merely
    present, so a partial rewrite would fail it too.

    Args:
        dumps: The two sides' normalised dumps.
        scenario_loader: For the seed declaration this row must still match.
    """
    seeded = scenario_loader(SCENARIO)["seed_records"]["posting.dat"][0]

    for side, tables in dumps.items():
        dump = tables["GLPOSTING-REC"]
        rows = _rows_by_key(dump)

        assert int(dump["row_count"]) == 1, (
            f"{side}: GLPOSTING-REC must still hold its one seeded row - the delete "
            f"walk skips it - and holds {dump['row_count']}"
        )
        assert POSTING_RRN_UNDER_N_RRN in rows, (
            f"{side}: the row's primary key must be {POSTING_RRN_UNDER_N_RRN}, "
            f"because anomaly N-RRN means POST-RRN is never loaded; keys are "
            f"{sorted(rows)}"
        )
        row = rows[POSTING_RRN_UNDER_N_RRN]

        # UNTOUCHED, not merely present. These four are what a delete-then-reinsert
        # or a partial rewrite would disturb.
        assert row["POST-LEGEND"] == seeded["Post-Legend"], (
            f"{side}: POST-LEGEND changed; the row should not have been written at "
            f"all. Got {row['POST-LEGEND']!r}, seeded {seeded['Post-Legend']!r}"
        )
        assert row["POST-AMOUNT"] == seeded["Post-Amount"], (
            f"{side}: POST-AMOUNT changed; got {row['POST-AMOUNT']!r}"
        )
        assert int(row["POST-DR"]) == int(seeded["Post-DR"])
        assert int(row["POST-CR"]) == int(seeded["Post-CR"])

        # THE CORRUPTED KEY ITSELF. Not a chosen value - it is whatever the group
        # move produces - so it is asserted as "not the declared batch number",
        # which is the property that makes the guard skip.
        stored_key = int(row["POST-KEY"])
        declared = int(seeded["Batch"]) * 100000 + int(seeded["Post-Number"])
        assert stored_key != declared, (
            f"{side}: POST-KEY holds {stored_key}, which equals the declared "
            f"batch/post-number composition {declared}. That would mean the group "
            f"move now carries the NUMBER rather than the characters - the anomaly "
            f"fixed rather than reproduced - and del-process would start deleting."
        )


def test_anomaly_n_rrn_is_why_one_posting_is_the_maximum(
    scenario_loader: object, harness: object
) -> None:
    """ANOMALY N-RRN, pinned where it can be pinned: at the seed declaration.

    The anomaly cannot be observed in this scenario's POST-RUN state, because Phase
    3 empties the table - so it is pinned here instead, as the constraint that
    shapes the seed. `WS-Post-rrn pic 9(5)` [copybooks/wspost.cob:L13] is declared
    and is moved nowhere: the bridge's load paragraph
    [common/glpostingMT.cbl:L1053-L1066] moves thirteen fields and not that one, so
    `HV-POST-RRN` keeps the zero `initialize` gave it and POST-RRN, the primary key,
    is 0 for every row ever inserted.

    If that anomaly were ever "fixed" so that rrn reached the column, a second
    posting WOULD become possible and this test would be the reminder to extend the
    scenario. Until then, declaring two postings would silently produce one row and
    make the scenario claim more than it tests.

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`.
        harness: For the in-scope table vocabulary; the package is never imported
            by name (R-1).
    """
    postings = scenario_loader(SCENARIO)["seed_records"]["posting.dat"]
    assert len(postings) == 1, (
        "exactly one posting may be declared: anomaly N-RRN forces POST-RRN to 0 "
        "for every insert, and POST-RRN is the primary key, so a second declaration "
        "would collide and silently produce one row"
    )
    assert int(postings[0]["Batch"]) == 1, (
        "the one posting must belong to the CLOSING cycle's batch, so that Phase 3 "
        "deletes it and the empty table is evidence that del-process ran"
    )

    # The zero is a fact about the frozen bridge, so it is named as a constant here
    # and cited, rather than left as a magic number in an assertion message.
    assert POSTING_RRN_UNDER_N_RRN == 0
    assert "GLPOSTING-REC" in tuple(harness.dump_tables.IN_SCOPE_TABLES), (
        "GLPOSTING-REC must be one of the dumper's own in-scope tables"
    )


@pytest.mark.database
@pytest.mark.oracle
def test_phase_three_stamped_only_the_closing_cycles_batch(
    dumps: dict[str, dict[str, object]], scenario_loader: object
) -> None:
    """The three stamps, and the untouched neighbour.

    Phase 3 sets, per batch of the closing cycle: `move 2 to cleared-status` (88
    Archived), `move run-date to stored`, `move zero to batch-start`, then
    `GL-Batch-Rewrite`. The other cycle's batch must be exactly as seeded, which is
    what proves the `bcycle not = scycle` filter held.

    Args:
        dumps: The two sides' normalised dumps.
        scenario_loader: For the pinned run date the stamp must carry.
    """
    run_date = scenario_loader(SCENARIO)["run_date_binary"]

    for side, tables in dumps.items():
        rows = _rows_by_key(tables["GLBATCH-REC"])

        assert BATCH_IN_CYCLE in rows, f"{side}: the closing cycle's batch is missing"
        stamped = rows[BATCH_IN_CYCLE]
        assert int(stamped["CLEARED-STATUS"]) == 2, (
            f"{side}: CLEARED-STATUS must be 2 (88 Archived); got "
            f"{stamped['CLEARED-STATUS']}"
        )
        assert int(stamped["STORED"]) == int(run_date), (
            f"{side}: STORED must carry the pinned run date {run_date}; got "
            f"{stamped['STORED']}"
        )
        assert int(stamped["BATCH-START"]) == 0, (
            f"{side}: BATCH-START must be zeroed; got {stamped['BATCH-START']}"
        )

        assert BATCH_OTHER_CYCLE in rows, f"{side}: the other cycle's batch vanished"
        untouched = rows[BATCH_OTHER_CYCLE]
        assert int(untouched["CLEARED-STATUS"]) == 0, (
            f"{side}: the other cycle's batch must be untouched (88 Waiting), which "
            f"is what proves the bcycle filter held; got {untouched['CLEARED-STATUS']}"
        )
        assert int(untouched["BATCH-STATUS"]) == 0, f"{side}: still 88 Status-Open"
        assert int(untouched["STORED"]) == 0, f"{side}: never stamped"
        assert int(untouched["BATCH-START"]) == 1, f"{side}: never zeroed"


@pytest.mark.database
@pytest.mark.oracle
def test_phase_five_wrote_q1_and_ledger_last_and_left_q2_q3_q4(
    dumps: dict[str, dict[str, object]],
) -> None:
    """ANOMALY A-3, asserted as a positive fact about the state.

    Phase 5 writes `ledger-q (a)` with the subscript `a` and `Ledger-Last` under
    `if current-quarter = 4`, and NOTHING reconciles the two. Seeded with `a`
    computing to 1 and the counter at 4, the observable consequence is: Q1 takes the
    balance, Ledger-Last takes the balance, and Q4 - the quarter the COUNTER names -
    is left exactly as seeded.

    A migration that unified the two notions would write Q4 instead of Q1, or would
    not write Ledger-Last at all. Either makes this test fail, which is the point:
    a defect reproduced is correct and a defect fixed is a failure (R-4).

    Args:
        dumps: The two sides' normalised dumps.
    """
    for side, tables in dumps.items():
        rows = _rows_by_key(tables["GLLEDGER-REC"])
        assert set(rows) == set(SEEDED_QUARTERS), (
            f"{side}: expected the three seeded accounts, got {sorted(rows)}"
        )

        for key, (_q1, q2, q3, q4) in SEEDED_QUARTERS.items():
            row = rows[key]
            balance = row["LEDGER-BALANCE"]

            # The subscript wrote Q1.
            assert row["LEDGER-Q1"] == balance, (
                f"{side} account {key}: LEDGER-Q1 must hold the balance - the "
                f"subscript a is 1 - but holds {row['LEDGER-Q1']!r} against a "
                f"balance of {balance!r}"
            )
            # The counter wrote Ledger-Last.
            assert row["LEDGER-LAST"] == balance, (
                f"{side} account {key}: LEDGER-LAST must hold the balance, because "
                f"current-quarter was 4 when Phase 5 ran; holds {row['LEDGER-LAST']!r}"
            )
            # And the other three quarters are untouched - including Q4, which is
            # the quarter the counter named. That is A-3 in one line.
            assert row["LEDGER-Q2"] == q2, f"{side} account {key}: Q2 was disturbed"
            assert row["LEDGER-Q3"] == q3, f"{side} account {key}: Q3 was disturbed"
            assert row["LEDGER-Q4"] == q4, (
                f"{side} account {key}: Q4 must be UNTOUCHED. current-quarter was 4, "
                f"but the SUBSCRIPT was 1, and it is the subscript that indexes "
                f"ledger-q. Q4 holding the balance would mean the two notions had "
                f"been unified - anomaly A-3 fixed rather than reproduced."
            )


@pytest.mark.database
@pytest.mark.oracle
def test_the_cycle_advanced_and_the_quarter_counter_wrapped(
    dumps: dict[str, dict[str, object]],
) -> None:
    """The only trace Phase 5's counter arithmetic leaves anywhere.

    `add 1 to scycle` takes the cycle from 1 to 2. `add 1 to current-quarter` then
    `if current-quarter = 5 move 1 to current-quarter` takes the counter from 4
    through 5 to 1. Neither is written by `gl080`, which ends at `main-end. goback.`
    - both are persisted by the menu exit and by the Python route's
    `args.overrewrite`. So this test is what makes the rollover observable at all,
    and it is only possible because SYSTEM-REC is in the affected-table list.

    `Cyclea binary-char` and `Scycle Redefines cyclea binary-char`
    [copybooks/wssystem.cob:L62-L63] are the SAME BYTE, which is why the advance
    shows up in the CYCLEA column.

    Args:
        dumps: The two sides' normalised dumps.
    """
    for side, tables in dumps.items():
        rows = _rows_by_key(tables["SYSTEM-REC"])
        assert len(rows) == 1, f"{side}: SYSTEM-REC holds one row"
        row = next(iter(rows.values()))

        assert int(row["CYCLEA"]) == 2, (
            f"{side}: CYCLEA must have advanced 1 -> 2 by `add 1 to scycle`; got "
            f"{row['CYCLEA']}. Scycle redefines Cyclea, so they are one byte."
        )
        assert int(row["CURRENT-QUARTER"]) == 1, (
            f"{side}: CURRENT-QUARTER must have wrapped 4 -> 5 -> 1; got "
            f"{row['CURRENT-QUARTER']}"
        )
        assert int(row["PERIOD"]) == 1, f"{side}: PERIOD is an input and must not move"


@pytest.mark.database
@pytest.mark.oracle
def test_anomaly_n_edit_still_drops_the_seeded_sign(
    dumps: dict[str, dict[str, object]],
) -> None:
    """ANOMALY N-EDIT: the bridge cannot render a minus sign, and still does not.

    The scenario seeds account 2000 with a balance of -2500.00. Every layer that
    could carry the sign does: the copybook field is `pic s9(8)v99 comp-3`
    [copybooks/wsledger.cob:L28], the host variable is `PIC S9(08)V9(02) COMP`
    [common/nominalMT.cbl:L300] and the column is `decimal(10,2)`. The sign is lost
    anyway, in the SQL TEXT, because the bridge renders through `01 WS-MYSQL-EDIT
    PIC -Z(18)9.9(9).` [common/nominalMT.cbl:L232] and every digit window it slices
    starts at position 3 or later while the sign sits at position 1
    [common/nominalMT.cbl:L1074-L1086].

    THIS TEST FAILS IF THE ANOMALY IS EVER FIXED, on either side, and that is
    deliberate (R-4). It is the only place in the suite where the sign loss is
    observed in real table state rather than against the migrated primitive alone.

    Args:
        dumps: The two sides' normalised dumps.
    """
    for side, tables in dumps.items():
        rows = _rows_by_key(tables["GLLEDGER-REC"])
        row = rows[LEDGER_KEY_SEEDED_NEGATIVE]

        for column in ("LEDGER-BALANCE", "LEDGER-Q1", "LEDGER-LAST"):
            value = row[column]
            assert isinstance(value, str), (
                f"{side}: a decimal column must arrive as a canonical string, "
                f"never a float (R-2); {column} is {type(value).__name__}"
            )
            assert not value.startswith("-"), (
                f"{side}: {column} holds {value!r}. The seed declared -2500.00 and "
                f"anomaly N-EDIT means the sign CANNOT survive the bridge's "
                f"WS-MYSQL-EDIT windows. A negative value here means the sign is "
                f"now being rendered - the anomaly fixed rather than reproduced, "
                f"which rule R-4 forbids."
            )

        assert row["LEDGER-BALANCE"] == "2500.00", (
            f"{side}: the absolute value is what reaches the column; got "
            f"{row['LEDGER-BALANCE']!r}"
        )


@pytest.mark.database
@pytest.mark.oracle
def test_system_record_parity_by_digest_as_well_as_by_dump(
    parity: object, protocol: object
) -> None:
    """THE PARAMETER ROW IS BOUNDED TWICE - by the dump, and by a digest of it.

    WHAT THIS CLOSES. An earlier draft kept `SYSTEM-REC` off every scenario's
    `affected_tables` and justified that by claiming no side writes it. That claim is
    FALSE: `acas_posting/cli/args.py`'s `overrewrite` reproduces
    [general/general.cbl:L656-L672] and every one of the seven routes calls it, so the
    parameter row is written on BOTH sides of every scenario. Until this assertion
    existed, a regression in that persistence produced an EMPTY DIFF and a green run.

    WHICH KEYS THIS ROUTE WRITES, AND WHY THIS SCENARIO IS THE ONE THAT MOVES THEM.
    `gl_end_of_cycle` binds `general_menu_state`, so `overrewrite` rewrites KEY 1
    (`SYSTEM-REC`), KEY 2 (`SYSDEFLT-REC`) and KEY 4 (`SYSTOT-REC`) - the widest of the
    three shapes. KEY 1 matters more here than on any other journey, because Phase 5 is
    what ADVANCES the cycle and rotates the quarter counter
    [copybooks/wssystem.cob:L127] - both of them columns of this row - so a regression in
    end-of-period bookkeeping lands here and nowhere else.

    IT IS DUMPED, WITH EXACTLY TWO CELLS WITHHELD. `SYSTEM-REC` is one of the 22
    in-scope tables every capture covers, so 167 of its 169 columns are compared by value
    like any other table's. The two exceptions are credentials - `RDBMS-PASSWD char(12)`
    [copybooks/wssystem.cob:L139] and `PASS-WORD` - and a capture is evidence that gets
    committed, so `harness/dump_tables.py`'s `REDACTED_COLUMNS` replaces those two cells
    with a fixed marker inside `render_value`, the one funnel every captured cell passes
    through. That is keyed by `(table, column)` and applied identically on both sides, so
    it cannot itself produce a difference.

    AND BOTH RUNNERS FINGERPRINT IT ANYWAY, before and after every run, which is what
    this test compares. A sha256 over the canonical primary-key-ordered dump covers all
    169 columns, credentials included, without being the dump - so the two withheld cells
    are still compared, inside a hash that leaks nothing. The credential columns come from
    the environment and are identical for both sides of one run, so they cannot
    manufacture a difference; anything that does differ is a difference in what the two
    cycles wrote. This scenario declares `changed`, and the row's digest is one of the
    things that moves on it.

    Args:
        parity: The completed, guarded run. The assertion needs its artifact layout, and
            taking the fixture is what orders this test after the two run stages rather
            than a comment claiming it.
        protocol: The protocol bundle. `assert_system_record_parity` is the ONE
            implementation of this comparison and lives in `tests/conftest.py`; nothing
            here reads a fingerprint file itself.

    Raises:
        Skipped: The harness Compose stack is not usable.
        AssertionError: A post-run record is missing or unreadable (a harness fault), or
            the two cycles left the parameter row in different states (a behavioural
            difference the table diff cannot see).
    """
    cobol_record, python_record = protocol.assert_system_record_parity(parity)

    # STATE WHAT WAS OBSERVED, so the test is not merely "the helper did not raise".
    # A zero-row parameter row would mean the seed never loaded system.dat, in which
    # case both sides agree on nothing at all and the digests would match vacuously.
    assert cobol_record.row_count == python_record.row_count == 1, (
        f"{SCENARIO}: the parameter row holds {cobol_record.row_count} row(s) on the "
        f"oracle side and {python_record.row_count} on the migrated side. system.dat "
        f"seeds EXACTLY ONE row for key 1, and two empty tables carry the same digest - "
        f"so without this check the parity claim above could pass on a database that "
        f"was never seeded."
    )
