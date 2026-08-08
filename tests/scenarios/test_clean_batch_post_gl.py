"""GENERAL LEDGER CLEAN-BATCH STATE PARITY - the reference happy path.

Scenario `clean_batch_gl`, subsystem `general`, operation `gl_post_cycle`. One closed,
proofed General Ledger batch sitting in the pinned accounting cycle is posted end to
end, and the resulting table state must match the compiled COBOL oracle BYTE FOR BYTE
after normalisation. This is the FIRST of the scenario files and it establishes
the shape the other seven repeat.

THE ONLY PASS CONDITION IS AN EMPTY ORDERING-NORMALISED DIFF. Agent Action Plan
section 0.8.5, verbatim: "seed identically through the maintainer's load programs, run
the compiled cycle, dump the affected tables ordering-normalised, reset, run the Python
cycle, dump again - and the diff MUST BE EMPTY."

-------------------------------------------------------------------------------
THE INVERTED ENGINEERING PREMISE - IT GOVERNS EVERY ASSERTION BELOW
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.2, verbatim:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A DEFECT REPRODUCED IS CORRECT; A DEFECT FIXED
    IS A FAILURE."

So a test here that asserted CORRECT ACCOUNTING rather than OBSERVED BEHAVIOUR would
itself be a defect. Nothing below checks that the ledger balances, that a stamped
status equals one, or that a total is arithmetically right. Every assertion asks only
whether the migrated cycle produced what the compiled COBOL produced. Agent Action
Plan section 0.3.2 reinforces it: expected values come "from the compiled oracle, never
from reading the COBOL and reasoning about what it should produce" - which is also why
`test_the_stamped_batch_columns_agree_on_both_sides` is framed as "both sides agree" and
never as "the value is 1".  IT WAS ONCE NAMED
`test_batch_is_stamped_cleared_and_posted`, which asserted an OUTCOME the oracle
refutes on this route: the batch is NOT stamped here, because A-NEW-18 starves the
posting walk. A test name is read far more often than a test body, so a name that
states a false outcome is a false claim however careful the body is.

THE SIX BINDING RULES R-1 to R-6 live in Agent Action Plan section 0.7.2, and their
exact wording is retrievable from the requirements. Summarised, and each named at the
site that honours it:

    R-1  No COBOL at runtime. Nothing here imports `harness` - that tree is
         deliberately not a Python package and `pyproject.toml` excludes it from
         packaging, which is the STRUCTURAL enforcement. The three harness Python
         modules arrive only through `tests/conftest.py`'s explicit-path accessors,
         and the compiled oracle is reached only out of process, by the harness
         shell stages those accessors' siblings drive.
    R-2  Zero binary floating point. No `float`, no tolerance, no epsilon, no
         approximate comparison, no `pandas`, no `numpy`. The comparison is `==`
         after a type check: `1` against `"1"` IS a difference.
    R-3  No new validations, fields or schema changes; no concurrency. This file
         emits no DDL, adds no check the COBOL lacks, and is strictly sequential -
         no test-distribution plugin, no parallelism, no randomised ordering.
    R-4  Legacy anomalies are reproduced, never fixed. The anomalies this file locks
         are named below with their locators, and no assertion here tidies, coalesces
         or harmonises anything.
    R-5  Full traceability. Every anomaly number and every `[path:Lnnn]` locator this
         file exercises is named in this docstring AND at the assertion site.
    R-6  Compiled behaviour is the tie-breaker. An empty normalised diff is the pass
         condition; a diff exit status of 2 means the comparison could not be
         performed and is an ERROR, never a pass.

-------------------------------------------------------------------------------
THE COBOL ROUTE, AND THE HARD GATE
-------------------------------------------------------------------------------

The menu's own dispatch paragraph, `[general/general.cbl:L805-L815]` verbatim:

    805|  load08.
    808|       move     "gl070" to ws-called.
    809|       perform  load00.
    810|       if       ws-term-code = 5
    811|                go to display-menu.        <- THE HARD GATE
    812|       move     "gl071" to ws-called.
    813|       perform  load00.
    814|       move     "gl072" to ws-called.
    815|       go       to load00.

gl070 -> the `ws-term-code = 5` gate -> gl071 -> gl072. IN A CLEAN BATCH THE GATE DOES
NOT FIRE, so all three phases run; the scenario's `expected_status` is `0` for exactly
that reason. When it does fire - `move 5 to ws-term-code` at
`[general/gl070.cbl:L289]` - gl071 and gl072 NEVER RUN AT ALL, and the database effect
is the ABSENCE of everything they would have written. That is `control_total_mismatch`,
not this file.

WARNING - THE PHASE NUMBERING IS NOT SEQUENTIAL WITH EXECUTION. The programs label
their own phases on screen:

    "Phase - 1.  Batch Check"              [general/gl070.cbl:L284]
    "Phase - 2.  Transaction Pre-process"  [general/gl070.cbl:L292]
    "Phase - 4.  Transaction Update"       [general/gl072.cbl:L274]
    "Phase - 3.  Transaction Deletion"     [general/gl080.cbl:L319]
    "Phase - 5.  End of Period Processing" [general/gl080.cbl:L336]

DELETION IS LABELLED PHASE 3 BUT EXECUTES AFTER PHASE 4, and both of the gl080 phases
belong to `gl_end_of_cycle`, which is a DIFFERENT operation and appears in no scenario
file. Agent Action Plan section 0.6.4 requires this be recorded "in the module
docstrings so a maintainer is not misled", so it is stated here explicitly.

-------------------------------------------------------------------------------
THE CYCLE FILTER APPEARS TWICE, WITH DIFFERENT COMPANIONS
-------------------------------------------------------------------------------

Both passes over the batch file filter on the accounting cycle; the second adds status
conditions the first does not (Agent Action Plan section 0.6.4).

    Pass 1  general/gl070.cbl
    312|       if       bcycle not = scycle
    313|                go to  loop.
    314|       if       status-open
    315|                move  1  to  a.          <- raises the abort, does not skip

    Pass 2  general/gl070.cbl
    457|       if       bcycle not = scycle
    458|                go to  loop.
    460|       if       status-open
    461|             or not waiting
    462|             or not gl-batch
    463|                go to  loop.

"Collapsing the two passes into one would change which batches are pre-processed." The
seeded batch must therefore satisfy BOTH: `Bcycle` equal to `Cyclea`
[copybooks/wsbatch.cob:L34], `Batch-Status` 1 so `Status-Closed` holds
[copybooks/wsbatch.cob:L25-L27], `Cleared-Status` 0 so `Waiting` holds
[copybooks/wsbatch.cob:L29-L31], and `WS-Ledger` 1 so `GL-Batch` holds
[copybooks/wsbatch.cob:L15-L16].

-------------------------------------------------------------------------------
ACCOUNT-LEVEL TOTALS CLOSE BEFORE BATCH-LEVEL TOTALS
-------------------------------------------------------------------------------

    286|       read     post-trans  at end
    287|                perform  end-account          <- FIRST
    288|                perform  end-batch            <- SECOND
    289|                go to    end-run.

and the end-of-batch step is what stamps the batch, `[general/gl072.cbl:L372-L377]`:

    372|  end-batch.
    375|       move     1  to  cleared-status.
    376|       move     run-date  to  posted.
    377|       perform  GL-Batch-Rewrite.

"Inverting them would produce a batch marked posted with an unclosed final account."
`end-account` at `[general/gl072.cbl:L379]` is the only writer of the nominal ledger,
through `GL-Nominal-Rewrite` at `[general/gl072.cbl:L382]`.

-------------------------------------------------------------------------------
THE ANOMALIES THIS FILE LOCKS (R-5)
-------------------------------------------------------------------------------

A-14 - THE NOMINAL ACCOUNT IS LOCATED BY A SEQUENTIAL READ, so correctness depends
entirely on upstream sort order. `[general/gl072.cbl:L407-L408]`:

    407|       if       read-ledger not = "R"
    408|                perform  GL-Nominal-Read-Next.

gl072 finds the right account ONLY because gl071 emitted the stream in nominal-key
order. Perturb the sort and it SILENTLY posts to the wrong account - no error, no
diagnostic, wrong balances. It is never "optimised" into an indexed read: Agent Action
Plan section 0.8.4, "any performance work is therefore out of scope by construction,
not merely unrequested". The authoritative single-statement locator recorded in
docs/migration/anomaly-log.md is `[general/gl072.cbl:L408]`, with its guard at L407 and
its key move at `[general/gl072.cbl:L405]`.

A-13 - TWO ENTIRELY SILENT SKIPS, with no message, counter or trace:
`[general/gl072.cbl:L291-L292]` on a non-numeric batch number and
`[general/gl072.cbl:L306-L307]` on `we-error = 999`, with a second `we-error` site at
`[general/gl072.cbl:L348-L349]`. A clean batch trips none of them; the diff is what
proves that, and `mixed_accepted_rejected` is where they are exercised.

A-21 - FIELD-NAME COLLISIONS across three posting copybooks force qualified
references, at `[general/gl070.cbl:L497]`, `[general/gl070.cbl:L521]` and
`[general/gl070.cbl:L525]`. (The Agent Action Plan cites L510; L510 is an ordinary
unqualified `move post-cr to pre-ac.` and the verified sites are the three above.)

A-22 - A WRAPPER SECTION NAMED AFTER THE INTERFACE COPYBOOK while its exit label is
named after the called program: `maps03 section.` at `[general/gl070.cbl:L603]`,
`call "maps04" using maps03-ws.` at `[general/gl070.cbl:L606]` and `maps04-exit.` at
`[general/gl070.cbl:L608-L609]`. Preserved, never harmonised.

A-NEW-8 - `acas007` AND `acas008` DISAGREE ABOUT WHETHER `Open-Output` TRUNCATES.
`[common/acas007.cbl:L305-L312]` carries the same open-output special case as its
sibling BUT `set fn-delete-all to true` IS COMMENTED OUT AT L308 (and
`move zero to access-type` at L309), so GL-Batch `Open-Output` does NOT truncate
`GLBATCH-REC` on the RDB path - whereas `[common/acas008.cbl:L316]` is live and DOES
truncate `PSIRSPOST-REC`. Preserved on both sides, never harmonised (R-4).

A-15 - THE BATCH-RECORD LENGTH CONTRADICTION, `[copybooks/wsbatch.cob:L7-L9]`
verbatim:

    7|  *> 96 bytes 26/03/09
    8|  *> 98 bytes 20/12/11 (no, dont understand as I count 96)
    9|  *>   but function length (Batch-record) says 98?

Whether the declared length or the sum of the fields governs the record actually read
affects the alignment of the trailing fields, and only execution showed which - never
reasoning. Execution has now happened: `Q-4` in
`docs/migration/ambiguity-resolutions.md` is `RESOLVED BY ORACLE` (2026-08-07) and the
answer is NEITHER - both record copies measure 96, `FUNCTION LENGTH` agrees with the
field sum, and the 98 in the maintainer's note is false under GnuCOBOL 3.2.0.
`docs/migration/anomaly-log.md` correspondingly carries A-15 as `REPRODUCED - VALUE
MEASURED`. Measured is not fixed: the contradictory note stays in the frozen copybook
and nothing repairs it (R-4).

A-12 - CHARACTER-WIDTH DRIFT, the reason normalisation job 1 exists at all:
`Ledger-Name pic x(24)` at `[copybooks/wsledger.cob:L27]` becomes
`HV-LEDGER-NAME PIC X(32)` at `[common/nominalMT.cbl:L299]` and
`` `LEDGER-NAME` char(32) `` at `[mysql/ACASDB.sql:L127]`. The value is not corrupted;
the PADDING differs, and padding is visible in a table dump.

-------------------------------------------------------------------------------
THE gl071 SORT CONTRACT - A LOAD-BEARING ORDERING, NOT A DETAIL
-------------------------------------------------------------------------------

    172|       sort     sort-trans
    173|                on ascending key sort-batch
    174|                                 sort-ac
    175|                                 sort-pc
    176|                                 sort-post
    177|                using  pre-trans
    178|                giving post-trans.

WARNING - THE SD DECLARATION ORDER IS NOT THE KEY ORDER. The record is declared
`sort-batch, sort-post, sort-code, sort-date, sort-ac, sort-pc, sort-amount,
sort-legend` at `[general/gl071.cbl:L137-L144]`, while the keys are batch, AC, PC,
POST. There is NO `DUPLICATES IN ORDER` phrase, so the relative order of a tie on all
four keys is whatever GnuCOBOL 3.2 chooses. Under R-6 that was a question for the
oracle, and the oracle has ANSWERED it: `Q-SORT-TIE-ORDER` in
`docs/migration/ambiguity-resolutions.md` is `RESOLVED BY ORACLE` (2026-08-07) - the
compiled sort PRESERVES INPUT ORDER for equal keys, which is exactly what the Python
side's unconditionally stable sort produces. It is independently harmless here, because
gl072's only state mutation for a posting is the COMMUTATIVE add at
`[general/gl072.cbl:L331]`. gl071 is a PURE SORT: measured over the whole file, zero
facade verbs and zero arithmetic statements.

-------------------------------------------------------------------------------
THE THREE-LEG DOUBLE-ENTRY EXPLOSION THAT PRODUCED THE WORK FILE
-------------------------------------------------------------------------------

`[general/gl070.cbl:L495-L533]`. The DR leg is L501-L508; the CR leg is L510-L519 and
carries the UNCONDITIONAL `multiply pre-amount by -1 giving pre-amount.` at L517; the
VAT leg is L521-L532 and is written only when BOTH the VAT account and the VAT amount
are non-zero:

    521|       if       vat-ac of WS-Posting-Record = zero
    522|             or vat-amount = zero
    523|                go to  loop.

All three legs are written to the WORK FILE `pretrans.tmp`, never to a table: gl070's
only `write` statements are `write pre-trans-record.` at L508, L519 and L532.

-------------------------------------------------------------------------------
gl072 MUTATES EXACTLY TWO TABLES, AND `GLPOSTING-REC` IS AN UNCHANGED WITNESS
-------------------------------------------------------------------------------

gl072's FULL facade-verb census is eight verbs, and it was measured over the file
rather than assumed:

    GL-Batch-Open        [general/gl072.cbl:L276]
    GL-Nominal-Open      [general/gl072.cbl:L274]
    GL-Batch-Rewrite     [general/gl072.cbl:L377]
    GL-Nominal-Rewrite   [general/gl072.cbl:L382]
    GL-Nominal-Read-Next [general/gl072.cbl:L408]
    GL-Batch-Close       [general/gl072.cbl:L441]
    GL-Nominal-Close     [general/gl072.cbl:L442]
    GL-Batch-Read-Next   [general/gl072.cbl:L454]

ZERO `GL-Posting-*` VERBS. And gl070 is READ-ONLY throughout - every one of its facade
verbs is an `-Open-Input`, a `-Read-Next` or a `-Close`. So on the `gl_post_cycle`
route `GLPOSTING-REC` IS AN UNCHANGED WITNESS: it is on the affected-table list
PRECISELY so the diff proves it was not touched. Corroborated by the one-byte dummy
stub block at `[general/gl072.cbl:L135-L155]`, where `WS-Posting-Record` is declared
`pic x.` at `[general/gl072.cbl:L140]` purely to satisfy the linker; Agent Action Plan
section 0.4.3 records that block as a representation-only omission that maps to nothing
in Python.

THE ONLY POSTING MUTATION IN THE WHOLE CYCLE is `[general/gl072.cbl:L331]`:

    331|       add      post-amount  to  ledger-balance.

and `[general/gl072.cbl:L443]` `call "SYSTEM" using Print-Report.` is the spool-out
path Agent Action Plan section 0.2.2 excludes - it has no database effect and must
appear in no dump.

-------------------------------------------------------------------------------
WHAT THIS FILE DELIBERATELY DOES NOT DO
-------------------------------------------------------------------------------

It never constructs a command line, an argument vector or a child process; it
hard-codes no long option; it never imports the General Ledger command-line entry
module and never runs one of those modules as `__main__`. The long-option spellings of
the promoted parameters belong to the entry points, and
`harness/run_python_scenario.sh` owns the `acas_py_require_flag <module> <flag>` probe
against `--help` that FAILS with harness-fault status when one is absent. This
scenario promotes no interactive answer at all, so its definition declares no answer
key.

It reads no YAML itself and imports no YAML parser: `tests/conftest.py`'s
`scenario_definition` does that with `yaml.safe_load`. It re-declares neither the
22-table inventory nor any primary key: those come from `harness/dump_tables.py`
through the accessor. It reimplements no comparison, no normalisation and no dump
shape check. And it recomputes no ledger balance - that is arithmetic-tier work and
lives in `tests/arithmetic/`, which touches neither COBOL nor a database.

The four documents this file references - docs/migration/traceability.md,
docs/migration/anomaly-log.md, docs/migration/ambiguity-resolutions.md and
docs/migration/scenario-diff-evidence.md - are TEXTUAL REFERENCES ONLY. Nothing here
imports them, checks that they exist, or skips when they are absent.
"""

from __future__ import annotations

import pytest

# The TIER mark, applied to the whole module because every test in it belongs to the
# tier. THE INFRASTRUCTURE MARKS ARE NOT HERE: `database` and `oracle` are declared per
# test, on exactly the tests whose fixture closure reaches the harness stack, because
# several tests in this file read only files on disk and pass on a bare host. A module
# mark would claim they need a MariaDB and a built oracle, and `-m database` would then
# select tests that require neither.
pytestmark = pytest.mark.scenario

SCENARIO = "clean_batch_gl"

# NOTHING HERE IMPORTS `tests/conftest.py`. Everything shared arrives through
# FIXTURES - `vocabulary` for the stack-free vocabulary and the pure helpers,
# `protocol` for the ten stages, `harness` for the three harness modules,
# `scenario_loader` for the parsed definition, `pinned_clock` for the pinned pair and
# `frozen_schema` for the declared column types. That is the house convention across
# this tree, and it is not cosmetic: a module-scope `import conftest` binds the whole
# scenario tier to pytest's default import mode, so a run under
# `--import-mode=importlib` fails at COLLECTION and takes every other scenario file
# down with it.
#
# EVERY EXPECTED VALUE THIS FILE CHECKS AGAINST IS EITHER A LOCAL BELOW OR ARRIVES
# THROUGH `vocabulary`, so there is no second authority to drift out of step with the
# scenario YAML.

# The three tables this scenario bounds the comparison by, in the declared order, and
# the two the seed fills. `GLPOSTING-REC` is the UNCHANGED WITNESS - `gl072` issues
# eight facade verbs and not one is a `GL-Posting-*` verb - so it is deliberately not
# among the tables required to hold rows by the non-vacuity guard: `posting.dat` does
# seed it, but the claim this file makes about it is asserted per value, against a
# separate capture of the seed, in `test_glposting_rec_is_an_unchanged_witness`.
BATCH_TABLE = "GLBATCH-REC"
LEDGER_TABLE = "GLLEDGER-REC"
POSTING_TABLE = "GLPOSTING-REC"

# THE TWO MENU-PERSISTED TABLES THIS SCENARIO ALSO BOUNDS. Added after measurement,
# not by assumption. The General menu's exit rewrites keys 1, 2 and 4
# [general/general.cbl:L656-L692] and the headless Python side has no menu, so the
# question is whether the two states nevertheless agree - and for keys 1 and 2 they
# do, byte for byte, all 169 SYSTEM-REC columns included. Leaving them out meant a
# system-record change this route did not intend could not be observed by anything,
# because this list is the declared effect; the comparison itself is bounded by all
# 22 in-scope tables.
# KEY 4 IS THE ONE THAT CANNOT BE COMPARED, and it is excluded below with its reason.
SYSTEM_TABLE = "SYSTEM-REC"
DEFAULTS_TABLE = "SYSDEFLT-REC"

# The tables that MUST come back with rows on both sides, or an empty diff over them
# proves nothing at all.
SEEDED_TABLES = (BATCH_TABLE, LEDGER_TABLE, POSTING_TABLE)

# This scenario drives exactly one operation, and declares one status for it.
OPERATION = "gl_post_cycle"
EXPECTED_STATUS = 0

# The only term code reachable on this route [general/gl070.cbl:L289], consumed by the
# hard gate at [general/general.cbl:L810-L811].
TERM_CODE_OPEN_BATCH = 5


# ---------------------------------------------------------------------------
#  THE SHARED EVIDENCE, AND WHY IT IS A FIXTURE
#
#  EVERY STAGE AND EVERY GUARD HAPPENS HERE, so that the two outcomes pytest can
#  report stay separable:
#
#  * a stage whose failure destroys the evidence - the seed, the reset, either
#  capture, either normalisation - and the comparison's own exit 2 raise
#  `HarnessFaultError`. Raised from a FIXTURE, pytest reports an ERROR: the
#  question was never asked.
#  * a genuine behavioural difference reaches the test body and fails an `assert`,
#  so pytest reports a FAILURE: the question was asked and answered.
#
#  In pytest an exception raised in a TEST BODY is reported FAILED whatever its type,
#  so preparation performed in a body destroys that distinction - and during bring-up,
#  when seed and reset failures are frequent, it sends a reader hunting for a
#  COBOL-versus-Python divergence that does not exist.
#
#  FUNCTION-SCOPED WITH A MODULE MEMO. The `protocol` fixture is function-scoped by
#  its own design, because it applies the stack skip per test, and pytest refuses to
#  let a module-scoped fixture depend on a function-scoped one. So the completed run
#  is memoised in the private mapping below - populated ONLY ON SUCCESS, so a
#  half-completed run is never served to a later test as though it were evidence -
#  which leaves every test below independent of ordering while performing the
#  destructive seed / run / reset / re-run sequence exactly ONCE rather than four
#  times. A `ParityRun` is frozen and all of its collections are tuples, so sharing it
#  is safe. Execution is strictly sequential (R-3), so a plain dict needs no lock.
# ---------------------------------------------------------------------------

_PARITY_RUNS: dict[str, object] = {}
_SEED_CAPTURES: dict[str, object] = {}


@pytest.fixture
def parity(protocol, vocabulary):
    """All ten protocol stages for `clean_batch_gl`, run once and guarded.

    THE FOUR GUARDS BELOW ARE HARNESS-FAULT DETECTORS, NOT BEHAVIOURAL ASSERTIONS.
    Each catches a condition under which an EMPTY DIFF WOULD MEAN NOTHING, and none
    of them is visible in the verdict:

      1. THE BOUND. The comparison must be bounded by ALL 22 IN-SCOPE TABLES, which
         is the protocol. The scenario's own `affected_tables:` list is its DECLARED
         EFFECT and is checked separately, as a subset.
      2. THE STATUSES. Both run stages' ACTUAL exit statuses are read and classified.
         A run that aborted where this scenario expects success leaves both sides
         equally unwritten and the diff equally empty.
      3. THE SEED FINGERPRINTS. The two cycles must have started from the same
         recorded row counts, or the differences - or their absence - belong to the
         seed rather than to the cycles.
      4. NON-VACUITY. The tables this scenario seeds must come back WITH ROWS on both
         sides. Two dumps of zero rows are identical, so without this the headline
         passes against an entirely unseeded database.

    Args:
        protocol: Every protocol stage and both compositions, from `tests/conftest.py`.
            Requesting it applies the stack skip, so a host with no Docker, no MariaDB
            and no built oracle SKIPS with a precise reason and never errors.
        vocabulary: The stack-free vocabulary, for the operation name's own check.

    Returns:
        The `ParityRun`: every stage result in execution order, both run stages, the
        stage-10 verdict and the paths of every artifact.

    Raises:
        Skipped: The Compose stack is unusable.
        HarnessFaultError: A stage whose failure destroys the evidence failed, or the
            comparison could not be performed at all. A pytest ERROR, never a pass.
        AssertionError: A guard above failed - also a harness fault.
    """
    assert OPERATION in vocabulary.operations, (
        f"{SCENARIO} drives {OPERATION!r}, which is not one of the seven operations "
        f"both runners share: {', '.join(vocabulary.operations)}."
    )

    cached = _PARITY_RUNS.get(SCENARIO)
    if cached is None:
        cached = protocol.run_scenario_parity(SCENARIO)
        _PARITY_RUNS[SCENARIO] = cached
    run = cached

    # GUARD 1 - the bound, in the declared order.
    assert tuple(run.tables) == tuple(protocol.in_scope_tables()), (
        f"{SCENARIO}: the comparison was bounded by {list(run.tables)}, but the "
        f"protocol bounds it by ALL 22 IN-SCOPE TABLES, "
        f"{list(protocol.in_scope_tables())}. A narrower bound cannot reveal a "
        f"difference in anything the scenario did not expect to move - including the "
        f"system rows `overrewrite` writes on BOTH sides "
        f"[general/general.cbl:L656-L672]."
    )
    #  The scenario's `affected_tables` is its DECLARED EFFECT, not the bound. It must be
    #  a subset of the bound, or something the scenario claims to change went uncompared.
    assert set(protocol.affected_tables(SCENARIO)) <= set(run.tables), (
        f"{SCENARIO}: declares an effect on "
        f"{sorted(set(protocol.affected_tables(SCENARIO)) - set(run.tables))!r}, which the comparison never covered."
    )

    # GUARD 2 - the ORACLE's ACTUAL status, and both sides' classifications. Bounded
    # to the reference side on purpose: an oracle that did not run the cycle to
    # completion means this scenario was never set up as declared, which is a setup
    # ERROR, while a Python side that diverges from the oracle is a behavioural
    # regression and is reported as a FAILURE by
    # `test_python_reproduced_the_oracles_disposition`.
    #  BOTH SIDES DROVE THE SAME ORDERED OPERATION LIST. The
    #  comparison below is between one COBOL run and one Python run, and it means
    #  nothing unless the two drove the same work in the same order - an empty diff
    #  between a short run and a full one being the most dangerous false pass this tier
    #  can produce. Both runners resolve the list from the scenario itself and publish
    #  one status row per operation, so it is checked rather than assumed.
    protocol.assert_operations_driven(run, operations=(OPERATION,))

    protocol.assert_declared_statuses(
        run,
        operations=(OPERATION,),
        declared=list(protocol.definition(SCENARIO)["expected_status"]),
        reference_only=True,
    )

    # GUARD 3 - the two sides started from the same recorded state.
    protocol.assert_seed_fingerprints_agree(run)

    # GUARD 4 - something was actually there to compare.
    protocol.assert_non_vacuous(run, tables_requiring_rows=SEEDED_TABLES)

    return run


@pytest.fixture
def seed_baseline(protocol, parity, tmp_path_factory):
    """A THIRD tree: this scenario's PRISTINE SEEDED STATE, for the absence proof.

    Two sides that had both posted a witness table would agree perfectly and the diff
    would still be empty, so agreement alone cannot prove that a table was left
    untouched. What makes absence provable is a capture of the seed itself, taken
    through the same dump and normalisation stages so that the comparison against it
    is like for like.

    IT RUNS AFTER THE PARITY RUN, DELIBERATELY. The ten stages end with the Python
    side's state in the database; re-seeding here would destroy the state the parity
    run's own dumps were taken from - the dumps are already on disk, so nothing is
    lost - and leaves the database in the pristine seeded state this capture describes.

    Args:
        protocol: The protocol stages.
        parity: The completed run, so the ordering above is enforced by pytest rather
            than by convention.
        tmp_path_factory: For an output root of its own, so the capture can never
            overwrite either side of the comparison.

    Returns:
        The `ScenarioPaths` of the baseline capture; its `cobol_normalized` tree is
        the seeded state.

    Raises:
        HarnessFaultError: The seed, the dump or the normalisation failed. A pytest
            ERROR: without a trustworthy baseline the absence proof cannot be made.
    """
    cached = _SEED_CAPTURES.get(SCENARIO)
    if cached is not None:
        return cached

    baseline_root = tmp_path_factory.mktemp("gl-seed-baseline")
    side = protocol.vocabulary.sides[0]
    protocol.seed(SCENARIO).raise_for_status()
    protocol.dump(SCENARIO, side, out_dir=baseline_root).raise_for_status()
    protocol.normalize(SCENARIO, side, out_dir=baseline_root).raise_for_status()
    captured = protocol.paths(SCENARIO, out_root=baseline_root)
    _SEED_CAPTURES[SCENARIO] = captured
    return captured


def test_scenario_definition_preconditions(pinned_clock, vocabulary) -> None:
    """Assert the preconditions that make this scenario's verdict mean anything.

    Each one closes a real FALSE-PASS hole, each is cheap, and none needs the stack.
    The definition is read through `tests/conftest.py`'s `scenario_definition`, which
    parses it with `yaml.safe_load`; this file opens no YAML and imports no parser.

    Args:
        pinned_clock: The project-wide pinned run date. The fixture itself asserts
            that the pair equals the project's pinned text and binary observables, so
            referencing it is how the pinned values reach this test without a literal
            being retyped anywhere.
        vocabulary: `tests/conftest.py`'s stack-free bundle - the seven operations
            both runners share, the admissible term codes, the scenario keys the
            stages read, the fan-out states, the date forms and the pinned pair. It
            arrives as a FIXTURE so that this file imports nothing from that module.

    Raises:
        AssertionError: A precondition does not hold.
    """
    definition = vocabulary.definition(SCENARIO)

    # The scenario names itself, and the operation is one of the seven both runners
    # share. `subsystem` is DERIVED from the operation rather than re-declared here:
    # `conftest.OPERATIONS` maps gl_post_cycle to ("general", "H", "load08",
    # "general/general.cbl:L805-L815"), the menu paragraph quoted in this module's
    # docstring.
    assert definition["name"] == SCENARIO
    operation = definition["operation"]
    assert operation in vocabulary.operations, (
        f"{SCENARIO} declares operation {operation!r}, which is not one of the "
        f"seven the two runners share: {', '.join(vocabulary.operations)}."
    )
    subsystem, _menu_key, _paragraph, _locator = vocabulary.operations[operation]
    assert definition["subsystem"] == subsystem
    # One operation, declared as an ordered sequence. The Python runner reads this
    # key as a flat sequence of operation NAMES and prefers it over the singular
    # key; both must therefore resolve the same single operation.
    assert list(definition["operations"]) == [operation]

    # THE EXIT STATUS IS BEHAVIOURAL DATA, NOT PLUMBING NOISE. `expected_status` is
    # positional against `operations`, and `acas_posting/cli/args.py`'s
    # `exit_status_for(term_code)` returns 0 for 0 and THE TERM CODE ITSELF
    # otherwise. So 0 states that gl070 did NOT reach `move 5 to ws-term-code`
    # [general/gl070.cbl:L289], the hard gate at [general/general.cbl:L810-L811] did
    # not fire, and all three phases ran.
    assert list(definition["expected_status"]) == [0]
    assert 0 not in vocabulary.term_codes[operation], (
        "zero must not be an admissible term code, or 'no abort' and 'aborted' "
        "would be indistinguishable in the expected status."
    )
    # The only term code reachable on this route is 5. Both of the term-code-8 raise
    # sites - [sales/sl055.cbl:L344] and [purchase/pl055.cbl:L286] - sit inside
    # `if FS-Cobol-Files-Used` blocks [sales/sl055.cbl:L326],
    # [purchase/pl055.cbl:L266], so with file_system_used 1 neither is reachable at
    # all. `expected_status: 0` here is therefore provable rather than assumed.
    assert vocabulary.term_codes[operation] == (5,)

    # -------------------------------------------------------------------------
    # THE FALSE-PASS TRAP. [copybooks/wssystem.cob:L111-L114]:
    #  111         05  RDBMS-Flat-Statuses.
    #  112             07  File-System-Used  pic 9.
    #  113                 88  FS-Cobol-Files-Used    value zero.
    #  114                 88  FS-MySql-Used          value 1.
    # and the GL-Batch handler [common/acas007.cbl:L316-L320]:
    #  316       if       not FS-Cobol-Files-Used
    #  317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
    #  318                perform  ba-Process-RDBMS
    #  319                go to AA-Main-Exit
    #  320       end-if.
    # With File-System-Used = 0 the handler falls through to the COBOL-indexed path
    # and NEVER TOUCHES MySQL. Both dumps would come back empty, the comparison
    # would exit 0, and the result would be a SILENT FALSE PASS.
    # -------------------------------------------------------------------------
    system = definition["system"]
    assert system["file_system_used"] == 1, (
        "system.file_system_used must be 1 (FS-MySql-Used, "
        "[copybooks/wssystem.cob:L114]). At 0 the handlers take the COBOL-indexed "
        "path [common/acas007.cbl:L316-L320], never touch MySQL, and both dumps "
        "come back empty - which the differ reports as an EMPTY DIFF. That is a "
        "silent false pass, and it is the single most dangerous misconfiguration "
        "available to this scenario."
    )

    # THE PINNED CLOCK - two observables and only two. The date reaches every
    # in-scope program purely through linkage: `05  Run-Date  binary-long.`
    # [copybooks/wssystem.cob:L67] is a real SYSTEM-REC column and is therefore
    # VISIBLE IN A DUMP, and none of the twelve in-scope programs contains a clock
    # read. Pinning these two is what makes two runs byte-identical.
    clock = definition["clock"]
    assert clock["to_day"] == vocabulary.pinned_run_date_text
    assert clock["run_date"] == vocabulary.pinned_run_date_binary
    assert (clock["to_day"], clock["run_date"]) == (
        pinned_clock.to_day,
        pinned_clock.run_date,
    ), (
        "the scenario's pinned clock and the project-wide pinned clock disagree; a "
        "one-day shift in SYSTEM-REC.RUN-DAT would read as a posting difference."
    )
    # The flat mirrors the COBOL runner reads with its top-level-scalar reader must
    # carry the same values as the grouped block, or the two sides are pinned
    # differently and the diff is meaningless.
    assert definition[vocabulary.scenario_keys["run_date_text"]] == clock["to_day"]
    assert definition[vocabulary.scenario_keys["run_date_binary"]] == clock["run_date"]

    # THE IRS FAN-OUT SWITCH, PINNED EXPLICITLY. [copybooks/wssystem.cob:L179-L181]:
    #  179         05  IRS-Instead     pic x.
    #  180             88  IRS-Used                   value "Y".
    #  181             88  IRS-Both-Used              value "B".   *> 26/11/16
    # THREE states, and the third - a space, General Ledger only - HAS NO CONDITION
    # NAME AT ALL: both predicates are simply False. Agent Action Plan section 0.6.4:
    # "leaving it at a default would make the affected-table list ambiguous", so it
    # is pinned rather than defaulted. A YAML space reaches the CLI as the LITERAL
    # SPACE `--irs-instead ' '`; there is no `N` token, as that option's own help
    # states. The column therefore stores a space, and normalisation job 1 trims that
    # to the empty string on BOTH sides - correct, because it is applied identically.
    irs_instead_key = vocabulary.scenario_keys["irs_instead"]
    assert system[irs_instead_key] in vocabulary.irs_instead_states
    assert system[irs_instead_key] == vocabulary.irs_instead_states[0]
    assert (
        definition[vocabulary.scenario_keys["irs_instead"]]
        == system[vocabulary.scenario_keys["irs_instead"]]
    )

    # THE ACCOUNTING CYCLE. [copybooks/wssystem.cob:L62-L64]:
    #  62         05  Cyclea          binary-char.  *> 99.
    #  63         05  Scycle Redefines cyclea  binary-char.
    #  64         05  Period          binary-char.  *> 99.
    # The seeded batch's `Bcycle` [copybooks/wsbatch.cob:L34] must equal it, or
    # [general/gl070.cbl:L312-L313] skips the batch on BOTH passes and nothing is
    # posted at all - a run that looks clean and proves nothing.
    assert system["cyclea"] != 0, (
        "system.cyclea must be non-zero: `Scycle` redefines it "
        "[copybooks/wssystem.cob:L62-L63] and both cycle filters compare the "
        "batch's Bcycle against it [general/gl070.cbl:L312-L313, L457-L458]."
    )
    # `period` is pinned for completeness and is INERT on this route,
    # because the only consumer of the period is gl080 and `gl_end_of_cycle` appears
    # in no scenario file. That omission is deliberate and oracle-reversible; it is
    # recorded in docs/migration/ambiguity-resolutions.md rather than settled here.
    assert system["period"] != 0

    # The date presentation form, pinned in both the grouped block and its flat
    # mirror. UK dd/mm/yyyy, which is the form `to-day pic x(10)` carries above.
    assert system[vocabulary.scenario_keys["date_form"]] == vocabulary.date_forms[0]
    assert (
        definition[vocabulary.scenario_keys["date_form"]]
        == system[vocabulary.scenario_keys["date_form"]]
    )

    # THE SEED CONTRACT - four flat files, each a name the frozen loader script
    # recognises. system.dat drives the four-loader system block, in a fixed order
    # and unconditionally [common/masterLD.sh:L51-L87]; ledger.dat goes to nominalLD
    # [common/masterLD.sh:L103]; batch.dat to glbatchLD [common/masterLD.sh:L94];
    # posting.dat to glpostingLD [common/masterLD.sh:L109]. The remaining three map
    # one-to-one onto the affected tables.
    seed_files = tuple(definition[vocabulary.scenario_keys["seed_files"]])
    assert set(seed_files) == {
        "system.dat",
        "ledger.dat",
        "batch.dat",
        "posting.dat",
    }
    assert "system.dat" in seed_files, (
        "system.dat is effectively mandatory: without a system record the menu "
        "calls its interactive setup program [general/general.cbl:L385-L394] and "
        "the runner blocks on a terminal, and it is the file that carries Run-Date "
        "[copybooks/wssystem.cob:L67] and the fan-out switch "
        "[copybooks/wssystem.cob:L179-L181]."
    )
    seed = definition["seed"]
    assert tuple(seed["files"]) == seed_files
    assert seed["data_dir"] == definition["seed_dir"]

    # THE CREDENTIAL PRECONDITION, ASSERTED BY THE HARNESS AND NOT BY THIS TEST.
    # The COBOL takes its credentials from the SEEDED SYSTEM RECORD, not from the
    # environment: the shipped defaults are declared at
    # [copybooks/wssystem.cob:L137-L144] - database name, user and password each
    # `pic x(12)`, port `pic x(5)` at L142, host `pic x(32)` at L143, socket
    # `pic x(64)` at L144 - and every handler copies them into the shared connection
    # block [copybooks/wsfnctn.cob:L56-L62], where the user and password fields are
    # only TWELVE characters wide. The ACAS_DB_* environment the Python side uses
    # must EQUAL the RDBMS-* fields inside the seeded system.dat, or the two sides
    # address different servers and the diff is meaningless. That cannot be checked
    # from here, because the flat file lives under the harness data directory.

    # NO ANSWER KEY IS DECLARED, and that is the whole point: the GL posting cycle
    # asks nothing interactively, so promoting an answer it never consumes would add
    # an input the frozen cycle does not take (R-3). irs_clear_postings,
    # payment_post_confirm, gl080_proceed and disk_change_option belong to the IRS,
    # payment and end-of-cycle routes, and none of them is on this path.
    for answer_key in (
        vocabulary.scenario_keys["irs_clear_postings"],
        "payment_post_confirm",
        "gl080_proceed",
        "disk_change_option",
    ):
        assert answer_key not in definition, (
            f"{SCENARIO} declares the answer key {answer_key!r}, which the "
            f"gl_post_cycle route never consumes. Its presence would promote an "
            f"input the frozen cycle does not take."
        )


def test_affected_tables_are_in_scope_and_alphabetical(harness, vocabulary) -> None:
    """Assert the affected-table list is exactly the three, in the declared order.

    THIS LIST IS THE SCENARIO'S DECLARED EFFECT, NOT THE COMPARISON BOUND - the
    comparison covers all 22 in-scope tables. There is no ignore-list, no
    tolerance-list and no "known difference" allowance anywhere in the diff path. The
    list still has to be right: it is what the runners assert changed or unchanged, so
    a wrong list stops asserting the effect this scenario exists to demonstrate.

    THE ORDER IS LOAD-BEARING. `harness/run_python_scenario.sh` writes its
    `<TABLE> <count>` seed-fingerprint lines in the list's DECLARED order and reports
    a harness fault when the two sides' fingerprints differ, and
    `harness/diff_states.py` reports its tables in that same order.

    Args:
        harness: The three harness Python modules, loaded by explicit file path
            (R-1). `IN_SCOPE` and every primary key are read from
            `harness/dump_tables.py` and are never re-declared here.
        vocabulary: The stack-free bundle. `affected_tables` delegates the reading and
            the in-scope check to `harness/dump_tables.py`, so the list is validated
            in exactly one place.

    Raises:
        AssertionError: The list is not the expected three, is not ascending, or
            names something that is not an in-scope table.
    """
    tables = vocabulary.affected_tables(SCENARIO)

    # GLBATCH-REC  - rewritten by gl072's end-batch [general/gl072.cbl:L372-L377].
    # GLLEDGER-REC - rewritten by gl072's end-account [general/gl072.cbl:L379-L382].
    # GLPOSTING-REC- READ ONLY on this route, and listed so the diff PROVES it.
    assert tables == (
        BATCH_TABLE,
        LEDGER_TABLE,
        POSTING_TABLE,
        DEFAULTS_TABLE,
        SYSTEM_TABLE,
    )

    # Ascending, which is both the declared order and the fingerprint order.
    assert list(tables) == sorted(tables)

    in_scope = harness.dump_tables.IN_SCOPE
    for table in tables:
        assert table in in_scope, (
            f"{table!r} is not one of the 22 in-scope tables "
            f"harness/dump_tables.py declares. The inventory has exactly one "
            f"definition in this repository and is never restated in a test."
        )
        # Every in-scope table has a SINGLE-COLUMN primary key and no secondary
        # index, which is what makes `SELECT * ... ORDER BY <primary key>` a total,
        # stable order with no tie-breaking (Agent Action Plan section 0.6.6).
        assert in_scope[table].primary_key

    # THE ELEVEN OUT-OF-SCOPE TABLES ARE NEVER DUMPED. One of them is the reason:
    # the schema's ONLY AUTO_INCREMENT column is `AUDIT-ID`
    # [mysql/ACASDB.sql:L1107], inside the out-of-scope STOCKAUDIT-REC, and an
    # auto-increment value would defeat the determinism argument outright.
    out_of_scope = harness.dump_tables.OUT_OF_SCOPE
    assert not set(tables) & set(out_of_scope)

    # THIS LIST IS THE DECLARED EFFECT, NOT THE COMPARISON BOUND - the capture and the
    # diff cover all 22 in-scope tables, and that is asserted in the fixture. BOUNDING
    # IS NOT IGNORING, AND WHICH SYSTEM TABLE FALLS ON WHICH SIDE OF THE DECLARED LINE
    # WAS MEASURED (rule R-6). A census over all twelve in-scope programs finds ZERO
    # `System-*` facade verbs, so no in-scope PROGRAM persists any of the four system
    # tables. What persists them is the MENU SHELL's exit path
    # [general/general.cbl:L656-L691]:
    #  656  overrewrite.
    #  657       if       File-System-Used NOT = zero
    #  659                move     1 to File-Key-No       <- KEY 1, SYSTEM-REC
    #  664                move     2 to File-Key-No       <- KEY 2
    #  667                move     4 to File-Key-No       <- KEY 4
    # writing keys 1, 2 and 4 to both stores - and `acas_posting/cli/args.py::overrewrite`
    # REPRODUCES IT, writing key 1 unconditionally, key 2 only when the route loaded the
    # defaults record and key 4 only when it loaded the totals record. EVERY ONE OF THE
    # SEVEN ROUTES CALLS IT, so key 1 is written on BOTH SIDES OF EVERY SCENARIO: the
    # General route writes keys 1, 2 and 4, Sales and Purchase write keys 1 and 4, and
    # the IRS route writes key 1 alone. The Python command line DOES do this - it carries
    # menu-exit persistence of its own - so the plausible claim that it "has no menu and
    # never does this" is false.
    #
    # Nor does the asymmetry mean all four system tables must be excluded as guaranteed
    # false failures. Measurement refutes that for keys 1 and 2: SYSTEM-REC and
    # SYSDEFLT-REC come back byte-identical on the two sides, so both are now DECLARED
    # above as well as compared.
    #
    # THE CREDENTIAL OBJECTION IS ANSWERED BY REDACTION, NOT BY EXCLUSION.
    # `RDBMS-PASSWD char(12)` is a SYSTEM-REC column [copybooks/wssystem.cob:L139] and a
    # dump is `SELECT *`, so a capture of the row would carry the database password into
    # the committed diff evidence. `harness/dump_tables.py`'s `REDACTED_COLUMNS` replaces
    # that cell and the frozen schema's shorter `PASS-WORD` cell - exactly those two, on
    # BOTH sides - with one fixed marker. The row is still dumped and still diffed, every
    # other column byte for byte, so this is not an ignore-list; withholding a secret
    # symmetrically cannot conceal a difference in anything the cycle computes.
    #
    # AND THE ROW IS FINGERPRINTED AS WELL, which is the stronger instrument rather than
    # the weaker one. Both runners digest it before and after every run - the runners
    # append it to the fingerprint list when a scenario has not declared it - and
    # `protocol.assert_system_record_parity` compares the two sides' post-run digests: a
    # parity check over all 169 columns, credential included, with nothing to leak
    # because a sha256 of a canonical dump is not the dump. `tests/conftest.py`'s
    # `PARAMETER_TABLE` carries the full reasoning, and the constant reaches this
    # STACK-FREE test as `vocabulary.parameter_table`.
    #
    # THE COUPLING OBJECTION WAS MEASURED RATHER THAN ASSUMED. The row's content depends
    # on what the route DID - the run-date stamp, the IRS allocator, the latches, and
    # `Date-Form`, which the frozen date sections write back
    # [copybooks/wssystem.cob:L127] - so counting it toward `expected_table_effect` could
    # in principle tie a scenario's effect claim to fields it does not reason about.
    # Measured, it does not: the digest moves on exactly the scenarios that declare
    # `changed` and holds on those that declare `unchanged`, which is why this scenario
    # can both declare the row and claim `unchanged`.
    #
    # KEY 4 IS DIFFERENT, AND ONLY KEY 4. The menu loads System-Record-4 from the
    # COBOL FLAT FILE alone [general/general.cbl:L402-L404] - the RDB read is
    # COMMENTED OUT at [general/general.cbl:L434-L436] - then writes that flat-sourced
    # copy into the RDB on the way out. This harness seeds only the RDB, and sys4LD
    # stamps 1 into all four spare fields whenever every real total is zero, under the
    # maintainer's own comment "See if we have an empty record, lets make sure it is
    # initialised" [common/sys4LD.cbl:L368-L390]. The seed therefore DECLARES
    # sl4-spare1..4 = "1.00" itself, so the exit writes back what it loaded; before
    # that, exactly those four columns differed and no others. Nothing in scope is
    # hidden: all nine period-total write sites are in the Sales and Purchase programs,
    # none of which runs here, and SYSTOT-REC is a DECLARED effect of clean_batch_sl,
    # clean_batch_pl and period_end_totals, whose key-4 seeds carry non-zero totals.
    # Note that the Sales and Purchase `overrewrite` paragraphs persist keys 1 and 4
    # only, NEVER key 2 [sales/sales.cbl:L628-L657], [purchase/purchase.cbl:L621-L650],
    # which is why SYSDEFLT-REC is declared by the General-family scenarios and by none
    # of the Sales or Purchase ones.
    #
    # SYSFINAL-REC is outside the declared effect on the simplest ground of all: no
    # menu writes it on this route and no in-scope program touches it anywhere in the
    # cycle. Both are still read and diffed, because the bound is all 22 in-scope
    # tables.
    for excluded in ("SYSFINAL-REC", "SYSTOT-REC"):
        assert excluded in in_scope, "both are in scope overall"
        assert excluded not in tables
    for compared in (SYSTEM_TABLE, DEFAULTS_TABLE):
        assert compared in tables, (
            f"{compared} is menu-persisted AND measured comparable, so it must be "
            f"bounded rather than excluded"
        )

    # AND THE PARAMETER TABLE IS FINGERPRINTED AS WELL AS DUMPED, which is what makes
    # its presence here a decision rather than an oversight. Asserted through the
    # protocol's own constant, so this test cannot drift away from what the runners
    # actually digest, and asserted to be DECLARED here rather than merely bounded: this
    # scenario names it, so the runners tally it toward `expected_table_effect` instead
    # of merely reporting it.
    assert vocabulary.parameter_table == "SYSTEM-REC"
    assert vocabulary.parameter_table in tables

    # The four autogen tables are never seeded and appear on no affected-table list,
    # because [sales/sales.cbl:L759] dispatches the out-of-scope sl830 on the COBOL
    # side only. Both runners assert after their run that all four are still empty;
    # that assertion lives in the runners, not here.
    for autogen in vocabulary.autogen_tables:
        assert autogen not in tables


# ---------------------------------------------------------------------------
#  THE FIVE REJECTION CLASSES - none exercised here, and the taxonomy is
#  deliberate. Agent Action Plan section 0.8.1 requires that a rejected
#  transaction reach the same disposition AND leave the same effect on the
#  database, and "a single generic rejection path would fail this directive".
#  The five differ precisely in that second dimension:
#
#  1. CLEAN REJECTION, NO DATABASE EFFECT - the two entirely silent skips,
#  [general/gl072.cbl:L291-L292] on a non-numeric batch number and
#  [general/gl072.cbl:L306-L307] on `we-error = 999`, with a second
#  `we-error` site at [general/gl072.cbl:L348-L349]. No message, no
#  counter, no trace (A-13). Exercised by `mixed_accepted_rejected`.
#  2. RUN-ABORTING REJECTION - a control-total mismatch leaves the batch open,
#  gl070 raises 5 [general/gl070.cbl:L289], the menu gate
#  [general/general.cbl:L810-L811] returns to the menu, and gl071 and gl072
#  NEVER RUN. The database effect is THE ABSENCE of everything the later
#  phases would have written, and absence is evidence. Exercised by
#  `control_total_mismatch`.
#  3. PARTIAL DATABASE EFFECT - the IRS half-posted double entry
#  [irs/irs030.cbl:L1635-L1652] (A-4) and the lost update on the two VAT
#  control accounts, snapshotted at [irs/irs030.cbl:L1602] and
#  [irs/irs030.cbl:L1612] and rewritten from those snapshots at
#  [irs/irs030.cbl:L1704-L1708] (A-5). Exercised by `clean_batch_irs`.
#  4. FILE-ABANDONING REJECTION - a posting-record write failure jumps straight
#  to end of job [irs/irs030.cbl:L1673-L1678], which still performs the two
#  snapshot rewrites and the closes, so THE PARTIAL STATE IS COMMITTED, NOT
#  ROLLED BACK.
#  5. PERMANENTLY FAILING FACADE VERB - the transfer-file handler refuses four
#  of its published verbs unconditionally at entry, each answered with
#  `WE-Error 988` and `fs-reply 99` [common/acas008.cbl:L299-L307] (A-6), so
#  the published Rewrite verb can never succeed.
#
#  A CLEAN BATCH TRIPS NONE OF THEM. That is not asserted by inspecting a
#  counter - no counter exists - but by the empty diff over the three bounded
#  tables, which is the only evidence the specification affords.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_clean_batch_post_gl_state_parity(parity, harness) -> None:
    """THE HEADLINE. Drive all ten protocol stages and demand an EMPTY diff.

    The ten stages, in the exact order, and none skipped:

         1  harness/reset_db.sh, which delegates to harness/seed.sh
         2  harness/run_cobol_scenario.sh
         3  harness/dump_tables.py  --scenario clean_batch_gl --side cobol
         4  harness/normalize.py    --side cobol
         5  harness/reset_db.sh, the SAME command as stage 1
         6  harness/run_python_scenario.sh
         7  harness/dump_tables.py  --scenario clean_batch_gl --side python
         8  harness/normalize.py    --side python
         9  both captures verified published, in process
        10  harness/diff_states.py

    EIGHT LOGICAL STAGES, TEN NUMBERED ONES. Agent Action Plan section 0.3.2 fixes the
    order as "seed, run, dump, normalize, reset, run, dump, diff" - eight. The driver
    The PROTOCOL numbers ten, reading the list from
    `harness/normalize.py`, because it makes BOTH normalisations and the publication
    check explicit rather than implied. Nothing was added to the protocol; where older
    prose says "stage 8" it means today's stage 10, the diff. The runners' own
    `Check n/8' headings are their internal preflight checks and are not protocol
    stages.

    They are driven through `tests/conftest.py`'s `run_scenario_parity`, which is
    what makes Agent Action Plan section 0.4.3 true - "no test reimplements the
    comparison protocol". Nothing here iterates a row, re-implements `diff_table`,
    or builds a command line.

    ALWAYS DUMP, THEN DECIDE THE STATUS. The two run stages' exit codes are recorded
    and are never allowed to skip the dump that follows them, because Agent Action
    Plan section 0.6.5 says of a run-aborting rejection that "the database effect is
    therefore THE ABSENCE of everything the later phases would have written". For
    `clean_batch_gl` the expected status is 0 and no abort is expected, but the
    discipline is uniform across every scenario file and is written the same way
    in each.

    THE THREE EXIT CATEGORIES ARE KEPT DISTINCT. A harness fault - a bad command
    line, an unreachable database, an absent CLI flag, disagreeing seed fingerprints,
    `argparse`'s own exit 2 - means the question was never asked and is RAISED, so it
    surfaces as an error rather than reading as a difference. An observed disposition
    that contradicts the scenario's expectation is a BEHAVIOURAL DIFFERENCE and fails
    the assertion, with the dump still taken so the table diff can corroborate it.

    WHERE THE VERDICT IS RECORDED (R-6). This run's outcome belongs in
    docs/migration/scenario-diff-evidence.md, and any semantic question it raises in
    docs/migration/ambiguity-resolutions.md - never settled silently in the code. Two
    such questions touch this scenario, and BOTH have been measured rather than left
    open: `Q-4`, the batch-record length contradiction at
    [copybooks/wsbatch.cob:L7-L9], is `RESOLVED BY ORACLE` (2026-08-07) with the answer
    NEITHER - both copies measure 96 - and `Q-SORT-TIE-ORDER`, the relative order of
    records tying on all four of gl071's keys [general/gl071.cbl:L172-L178], is
    `RESOLVED BY ORACLE` (2026-08-07) with the compiled sort PRESERVING INPUT ORDER.
    Neither answer is hard-coded into an assertion below: a measured answer is a reason
    to expect agreement, never a substitute for observing it. The General Ledger caveat
    makes this
    non-negotiable: the maintainer records at [README.TXT:L50-L53] that testing is
    complete for IRS, Stock and Sales but that he has "not had any time to work with
    General at all since it was migrated over to using the GnuCobol compiler (3.2
    final)", and the General Ledger contributes the majority of the in-scope
    programs. So if the compiled cycle behaves surprisingly, THE SURPRISE IS THE
    SPECIFICATION - no expected value for this scenario may be derived from
    documentation or from reasoning about intent.

    THE BODY HOLDS ONLY THE VERDICT. Every stage, and all four harness-fault guards -
    the bound, both ACTUAL run statuses with their classifications, the two sides'
    seed fingerprints and non-vacuity - happened in the `parity` fixture, so a harness
    fault is a pytest ERROR while what is left here is the arbitration, and a genuine
    behavioural difference is a pytest FAILURE. The two can then never be confused,
    which is the whole point of the split: exit 2 must never read as "no differences".

    Args:
        parity: The completed, guarded `ParityRun`.
        harness: The three harness Python modules (R-1), for `render`.

    Raises:
        Skipped: The harness Compose stack is not usable; the reason names every
            missing precondition.
        AssertionError: The two normalised trees differ - a real behavioural
            difference between the compiled COBOL and the migrated cycle.
    """
    run = parity

    # THE PASS CONDITION, and the only one. `TreeDiff.is_empty` is a single cheap
    # question over a frozen dataclass; `render` reproduces the per-table findings
    # so the reader sees what actually differed rather than a bare False.
    assert run.is_empty, (
        f"{SCENARIO} produced a NON-EMPTY normalised diff, which Agent Action Plan "
        f"section 0.6.6 makes decisive: \"a non-empty diff is always a real "
        f"behavioral difference and never an artefact of the comparison\". The "
        f"comparison is exact - `==` after a type check, no tolerance, no epsilon, "
        f"no coercion, rows aligned by primary-key VALUE and never by position - so "
        f"the migrated cycle did not reproduce the compiled COBOL. Interrogate the "
        f"compiled oracle, reproduce whatever it does (a defect reproduced is "
        f"correct; a defect fixed is a failure), and record the arbitration in "
        f"docs/migration/ambiguity-resolutions.md.\n"
        f"{run.diagnose()}\n"
        f"{run.describe()}"
    )


# ---------------------------------------------------------------------------
#  R-3 SEEDING AND SCHEMA CONSTRAINTS - documented here, implemented nowhere
#  here. This file emits no DDL and issues no statement of its own.
#
#  NO DDL. The seeded schema is mysql/ACASDB.sql applied VERBATIM. It already
#  carries all 33 `DROP TABLE IF EXISTS`, so re-applying it IS the
#  drop-and-recreate; the database name must be on the client command line
#  because the file has no `USE`. Census: 33 `CREATE TABLE`, 33 `DROP TABLE IF
#  EXISTS`, 0 real `ALTER TABLE`, 0 `CREATE INDEX`, 0 `CREATE DATABASE`, 0
#  `USE`, 0 `INSERT INTO`, 0 `FLOAT`/`DOUBLE`/`REAL`, 0 `TIMESTAMP`.
#
#  AUTOCOMMIT MUST BE OFF WHILE SEEDING, AND ONLY THERE. harness/seed.sh owns
#  that window and is the only place the mode is ever changed; every connection
#  outside it is runtime access, asserted as `1, 1` by
#  `conftest.assert_runtime_autocommit_on`, by harness/reset_db.sh and by
#  harness/run_cobol_scenario.sh, with harness/Dockerfile.mariadb declaring the
#  runtime mode. The scoping is the settled half of
#  docs/migration/ambiguity-resolutions.md#q-10. The batch loader's banner is
#  what the requirement derives from, [common/glbatchLD.cbl:L9-L12] verbatim:
#  9  *>  This modules uses commit and rollback so *
#  10  *>  you MUST ensure that autocommit is OFF   *
#  11  *>   in the rdb settings. It is as default   *
#  12  *>   set ON.                                 *
#
#  common/masterLD.sh IS NEVER INVOKED, for three verified reasons: its own
#  header says "THIS SCRIPT HAS NOT YET BEEN TESTED" [common/masterLD.sh:L4];
#  it is not valid shell - all 24 loader lines [common/masterLD.sh:L93-L116]
#  omit the `;` before `fi`, so `bash -n` rejects a 123-line file at line 124;
#  and it ends by paging SYS-DISPLAY.log through `less`, which would block a
#  non-interactive run forever. It is FROZEN AND NOT FIXED (R-3, R-4);
#  harness/seed.sh reproduces its documented per-file contract instead
#  [common/masterLD.sh:L44-L115] and checks the loader exit codes, whose values
#  above 63 abort the load.
#
#  R-4 ITEMS PRESERVED RATHER THAN FIXED: the `dfltLD` strict-versus-lenient
#  exit asymmetry, tested with `if [ $rc != 0 ]` at [common/masterLD.sh:L83]
#  where its three siblings tolerate up to 63; the charset caveat, where
#  [mysql/ACASDB.sql:L16] declares `SET NAMES utf8mb4` while all 33 tables
#  declare `DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci`; and the
#  `tinyint(1) unsigned` display-width quirk on GLBATCH-REC's `BATCH-STATUS`
#  [mysql/ACASDB.sql:L83] and `CLEARED-STATUS` [mysql/ACASDB.sql:L84].
#
#  STRICTLY SEQUENTIAL. No test-distribution plugin, no parallelism, no
#  randomised ordering: parallel scenario runs against one shared MariaDB
#  would break the seed/run/dump/reset/run/dump/diff protocol outright.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_python_reproduced_the_oracles_disposition(parity, protocol) -> None:
    """THE MIGRATED CYCLE EXITED AS THE ORACLE EXITED - the behavioural half.

    Read here, in a BODY, and deliberately not in the `parity` fixture. The oracle's
    status is the specification (rule R-6): whatever the compiled cycle exited with is
    correct by definition, so a Python side that exits differently is a regression in
    the migrated code. Asserting it during setup would report that regression as an
    ERROR in every test of this file, where it would be indistinguishable from a
    MariaDB that never came up - so the fixture bounds itself to the oracle side with
    `reference_only=True` and this test owns the comparison.

    Both statuses matter beyond agreeing. `gl_post_cycle` is the one operation with a
    term code - 5, the open-batch abort raised at [general/gl070.cbl:L289] and gated at
    [general/general.cbl:L810-L811] - so a clean batch exiting 5 would mean the three
    phases never all ran, `gl071` and `gl072` posted nothing, and the empty diff this
    file's headline test celebrates would be two equally unposted databases. Hence the
    declared status is asserted too, not just the equality.

    Args:
        parity: The completed ten-stage run.
        protocol: The stage bundle, for the cross-side guard and the dispositions.
    """
    declared = list(protocol.definition(SCENARIO)["expected_status"])
    assert declared == [EXPECTED_STATUS] * len(declared), (
        f"{SCENARIO}: the scenario declares {declared!r} where this file states "
        f"{EXPECTED_STATUS} for every operation. The two must not drift apart - a "
        f"local restatement that no longer matches the scenario file would let this "
        f"test pass against a route it is not describing."
    )

    disposition = protocol.assert_python_reproduced_disposition(
        parity, operations=(OPERATION,), declared=declared
    )
    assert disposition == protocol.vocabulary.disposition_success, (
        f"{SCENARIO}: the migrated cycle classified as {disposition!r}. On a CLEAN "
        f"batch every phase runs to completion, so the only admissible disposition is "
        f"{protocol.vocabulary.disposition_success!r}; "
        f"{protocol.vocabulary.disposition_behavioural!r} here would mean term code "
        f"{TERM_CODE_OPEN_BATCH} was raised and the posting phases were skipped."
    )
    assert TERM_CODE_OPEN_BATCH not in (
        parity.cobol_run.returncode,
        parity.python_run.returncode,
    ), (
        f"{SCENARIO}: term code {TERM_CODE_OPEN_BATCH} appeared on a route whose "
        f"batch is balanced and closed. It is the OPEN-BATCH abort, and it stops the "
        f"cycle before `gl071` and `gl072` run at all.\n{parity.describe()}"
    )


def test_diff_exit_contract_is_honoured(
    tmp_path, harness, frozen_schema, vocabulary, capsys
) -> None:
    """The THREE-WAY exit contract: 0 is a pass, 1 is a failure, 2 IS NEVER A PASS.

        0  the trees are identical, and stdout is EMPTY - zero bytes, not a banner
           and not "no differences found"                                 -> PASS
        1  a real behavioural difference, with a deterministic report   -> FAILURE
        2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a capture that
           attests nothing, a capture taken after a failed run           -> ERROR

    A TEST THAT TREATED "COULD NOT COMPARE" AS "NO DIFFERENCES" IS THE SINGLE WORST BUG
    AVAILABLE IN THIS TREE, so the mapping is exercised rather than trusted. Rule R-6
    makes an empty diff the pass condition ONLY when a comparison actually happened.

    DRIVEN THROUGH THE SHIPPED COMPARISON, AND THROUGH ONE IMPLEMENTATION.
    `tests/conftest.py`'s `assert_diff_exit_contract` publishes two synthetic sides with
    `harness/dump_tables.py`'s own writer, canonicalises them with `harness/normalize.py`
    and compares them with `harness/diff_states.py` - once for each of the four cases.
    THIS FILE USED TO ASSERT THE CONTRACT AGAINST MODULE CONSTANTS AND HAND-BUILT
    `TreeDiff` DATACLASSES, which passes whatever the comparison actually does: three
    integers being distinct says nothing about what the tool exits with, and a dataclass
    built in the test reports whatever the test put in it. The constants are still
    checked here, but only as a cheap corroboration of a contract the helper has just
    exercised end to end, over THIS scenario's own declared-effect bound - the five
    tables `affected_tables` names, which is the shape the caller's own scenario has.
    The end-to-end drive was written here first and was then lifted into
    `tests/conftest.py` unchanged, so that the other seven scenario files could stop
    asserting constants and share it. Nothing was weakened in the move: the helper
    drives the identical four cases against the same shipped stages.

    IT ASSERTS NOTHING WHATEVER ABOUT THE MIGRATION. The trees are SYNTHETIC, built from
    the frozen schema's own column lists, so the machinery under test is the shipped
    machinery - but a verdict taken from a hand-built tree is not protocol evidence, and
    none is claimed. That is also why this test needs no Compose stack and no compiled
    oracle: it executes on a bare host.

    Args:
        tmp_path: A private output root, so `$ACAS_OUT` is neither read nor needed and
            nothing is written into a compared tree.
        harness: The three harness Python modules (R-1).
        frozen_schema: The parsed `mysql/ACASDB.sql`, READ AND NEVER WRITTEN. It supplies
            every column name and declared type, so nothing is invented.
        vocabulary: The STACK-FREE bundle. Stages 4 and 8 are file-to-file
            transformations driven in process, which is what lets the whole contract be
            exercised on a bare host; it also publishes the helper.
        capsys: The two refusals' streams, which the helper drives through
            `diff_states.main` directly - the `diff` helper maps exit 2 to a harness
            fault by design, and here a refusal is the expected outcome.

    Raises:
        AssertionError: An exit status, a stdout stream or a verdict did not match the
            contract.
    """
    vocabulary.assert_diff_exit_contract(
        SCENARIO,
        out_dir=tmp_path,
        harness=harness,
        schema=frozen_schema,
        vocabulary=vocabulary,
        readouterr=capsys.readouterr,
    )

    # THE THREE STATUSES REMAIN DISTINCT AND KEEP THEIR DOCUMENTED VALUES. Cheap, and
    # worth stating separately: the helper above proved what the tool DOES, and this
    # proves the numbers a reader of the evidence document will see are the numbers this
    # file names. Collapsing "could not compare" into either of the other two is how a
    # false pass is manufactured.
    diff_states = harness.diff_states
    observed = (
        diff_states.EX_IDENTICAL,
        diff_states.EX_DIFFERENT,
        diff_states.EX_ERROR,
    )
    assert observed == (0, 1, 2), (
        f"the exit contract's three statuses must be 0, 1 and 2 in that order; the "
        f"comparison declares {observed!r}."
    )


# ---------------------------------------------------------------------------
#  NORMALISATION DOES EXACTLY THREE THINGS, AND THERE IS NO FOURTH. Every part
#  of it is delegated to harness/normalize.py; nothing is reimplemented or
#  extended here. The obligation runs both ways: remove the representation
#  artefacts, and NEVER make two genuinely different stored values compare
#  equal, so that Agent Action Plan section 0.6.6 holds.
#
#  JOB 1 - TRAILING SPACES IN FIXED-CHARACTER COLUMNS. `rstrip(" ")`, TRAILING
#  ONLY, ASCII U+0020 only, by DECLARED type including `char(1)`. Leading
#  spaces are CONTENT, because a COBOL alphanumeric MOVE is left-justified with
#  right padding. Motivated by A-12: `pic x(24)`
#  [copybooks/wsledger.cob:L27] becomes `PIC X(32)`
#  [common/nominalMT.cbl:L299] and `` `LEDGER-NAME` char(32) NOT NULL, ``
#  [mysql/ACASDB.sql:L127]. The schema declares 238 `char(` columns and zero
#  `varchar(`.
#
#  JOB 2 - DECIMAL SCALE RENDERING AT THE DECLARED SCALE, which is NOT
#  uniformly 2: 68 columns are (9,2), 57 are (10,2), 17 are (4,2), 12 are
#  (5,2), 4 are (14,2), 2 are (2,0), 2 are (14,4), plus singletons. A value
#  implying MORE places RAISES rather than rounds, because rounding there would
#  hide a real finding. GLBATCH-REC's four money columns are
#  `decimal(14,2) unsigned` [mysql/ACASDB.sql:L90-L93], matching the UNSIGNED
#  `pic 9(9)v99 comp-3` under the group at [copybooks/wsbatch.cob:L40-L44];
#  GLLEDGER-REC.LEDGER-BALANCE [mysql/ACASDB.sql:L128] derives from
#  `pic s9(8)v99 comp-3` [copybooks/wsledger.cob:L28].
#
#  JOB 3 - THE TWO- VERSUS FOUR-DIGIT DATE TEXT FORMS, under an EXPLICIT
#  FIVE-COLUMN ALLOW-LIST and nothing else: GLPOSTING-REC.POST-DAT,
#  IRSPOSTING-REC.POST4-DAT, PSIRSPOST-REC.IRS-POST-DAT,
#  SYSTEM-REC.STATS-DATE-PERIOD and SALEDGER-REC.SALES-STATS-DATE. `char(8)`
#  DOES NOT IMPLY DATE - PUITM5-REC.OI5-BATCH and SAITM3-REC.OI3-BATCH are
#  batch references and are excluded. And MOST in-scope "dates" are BINARY DAY
#  NUMBERS that job 3 must not touch: GLBATCH-REC's ENTERED, PROOFED, POSTED
#  and STORED are all `int(8) unsigned` [mysql/ACASDB.sql:L86-L89], from the
#  four `binary-long` fields at [copybooks/wsbatch.cob:L36-L39], so
#  [general/gl072.cbl:L376]'s `move run-date to posted` stamps an INTEGER and
#  not date text.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_dump_is_wellformed_on_both_sides(parity, protocol, frozen_schema) -> None:
    """Assert both sides' dumps have the shape the protocol guarantees.

    A malformed dump is exit 2 territory - the comparison could not be performed -
    and it must never be discovered as "no differences". The structural contract has
    exactly ONE definition in this repository, in `harness/diff_states.py`, and
    `tests/conftest.py`'s `assert_dump_wellformed` is the single way a test reaches
    it: exactly five keys in fixed insertion order and no others (`table`,
    `primary_key`, `columns`, `row_count`, `rows` - no timestamp, no server version,
    no scenario name and no side, because the side is recorded in the PATH);
    `columns` in schema ordinal order and never sorted; `primary_key` present among
    them; `row_count == len(rows)`; every row of `len(columns)` values, positionally
    aligned; no value a float (R-2); no value null; and no primary-key value twice.
    Passing `schema` additionally pins `columns` to the frozen schema's own ordinal
    order, which matters because ROWS ARE POSITIONAL: a column list in any other
    order has no meaningful alignment.

    DECIMAL values are canonical JSON STRINGS at the declared scale, never JSON
    numbers and never exponent notation; integers are JSON integers. The three tables
    checked are declared at [mysql/ACASDB.sql:L80-L103], [mysql/ACASDB.sql:L122-L135]
    and [mysql/ACASDB.sql:L154-L170], with 21, 11 and 14 columns respectively, and the
    column-count check is a cheap, strong tripwire on schema tampering.

    WHY NO VALUE MAY BE NULL, and why one is never coalesced: every column of the
    frozen schema is declared NOT NULL, and Agent Action Plan section 0.6.2 explains
    the mechanism - each bridge load paragraph initialises its host-variable group, so
    an unset field becomes zero or space rather than SQL NULL. A null is therefore
    GENUINELY NEW INFORMATION and is reported rather than tidied away (R-4).

    WHY THE ORDINAL ORDER MATTERS BEYOND PEDANTRY: character padding differs between
    the two sides by construction - A-12, `pic x(24)` at [copybooks/wsledger.cob:L27]
    against `PIC X(32)` at [common/nominalMT.cbl:L299] and `char(32)` at
    [mysql/ACASDB.sql:L127] - so normalisation job 1 is applied per column BY DECLARED
    TYPE. A column list in the wrong order would have job 1 applied to the wrong
    values and would still compare equal on both sides, which is the quiet kind of
    false pass this check exists to prevent.

    Args:
        parity: The completed, guarded `ParityRun` - produced in the fixture, so a
            stage fault here is an ERROR and not a malformed-dump FAILURE.
        protocol: The protocol bundle, for the single definition of the structural
            contract. Nothing about the shape is restated in this file.
        frozen_schema: The parsed `mysql/ACASDB.sql`, read and never written.

    Raises:
        Skipped: The harness Compose stack is not usable.
        AssertionError: A dump is malformed, or its column list disagrees with the
            frozen schema.
    """
    run = parity

    for side, tree in (
        (protocol.vocabulary.sides[0], run.paths.cobol_normalized),
        (protocol.vocabulary.sides[1], run.paths.python_normalized),
    ):
        for table in run.tables:
            path = tree / f"{table}.json"
            dump = protocol.read_dump(path)
            protocol.assert_dump_wellformed(
                dump, where=f"{side} {table} ({path})", schema=frozen_schema
            )


@pytest.mark.database
@pytest.mark.oracle
def test_glposting_rec_is_an_unchanged_witness(
    parity, seed_baseline, protocol
) -> None:
    """`GLPOSTING-REC` must be untouched - by BOTH sides, and against the seed.

    THE MEASURED CENSUS BEHIND THIS TEST. gl072 issues exactly eight facade verbs -
    `GL-Batch-Open` [general/gl072.cbl:L276], `GL-Nominal-Open`
    [general/gl072.cbl:L274], `GL-Batch-Rewrite` [general/gl072.cbl:L377],
    `GL-Nominal-Rewrite` [general/gl072.cbl:L382], `GL-Nominal-Read-Next`
    [general/gl072.cbl:L408], `GL-Batch-Close` [general/gl072.cbl:L441],
    `GL-Nominal-Close` [general/gl072.cbl:L442] and `GL-Batch-Read-Next`
    [general/gl072.cbl:L454] - and ZERO `GL-Posting-*` verbs. gl070 is read-only
    throughout, and gl071 issues no facade verb at all. So the posting table is on
    the affected-table list PRECISELY so that the diff proves it was not touched:
    listing it is the assertion, and omitting it would leave a whole table
    unexamined.

    Corroborated by the one-byte dummy stub block [general/gl072.cbl:L135-L155],
    where `WS-Posting-Record` is declared `pic x.` at [general/gl072.cbl:L140] purely
    so the linker resolves the facade copybook's full verb set. Agent Action Plan
    section 0.4.3 records that block as a representation-only omission that maps to
    nothing in Python, so a reader comparing the two files does not conclude
    something was lost.

    "IDENTICAL ON BOTH SIDES" AND "IDENTICAL TO THE SEED" ARE TWO DIFFERENT CLAIMS,
    and both are made. Two sides that had each written the same wrong rows would
    agree with one another perfectly, so the seed capture is what closes that hole.
    The seed is captured with the protocol's own stages - seed, dump, normalise -
    into a private root, and compared with `diff_trees_directly`. NOTE that
    `harness/diff_states.py` has exactly two labels and they are not configurable,
    so in those two comparisons `cobol` means THE SEED and `python` means the
    post-run state; that is stated rather than papered over.

    BOTH CAPTURES HAPPEN IN FIXTURES. The parity run and the seed baseline are
    prepared by `parity` and `seed_baseline`, so a failure to seed, dump or normalise
    is a pytest ERROR - during bring-up those failures are frequent, and reported from
    a body they would read as "the posting table was written", which is the opposite
    of what happened.

    Args:
        parity: The completed, guarded `ParityRun`.
        seed_baseline: The pristine seeded capture, under its own output root so that
            neither it nor the parity run can overwrite the other.
        protocol: The protocol bundle, for `diff_trees_directly` and the side labels.

    Raises:
        Skipped: The harness Compose stack is not usable.
        HarnessFaultError: A capture stage failed, so there is no evidence.
        AssertionError: The posting table was written by one of the two cycles.
    """
    run = parity
    witness = POSTING_TABLE
    assert witness in run.tables
    seeded = seed_baseline.cobol_normalized

    # CLAIM 1 - the two sides agree about the posting table.
    table_diff = next(
        (candidate for candidate in run.tree.tables if candidate.table == witness),
        None,
    )
    assert table_diff is not None, (
        f"the comparison reported no result for {witness}, so the table the diff "
        f"exists to exonerate was never looked at. The tables compared were "
        f"{[candidate.table for candidate in run.tree.tables]}."
    )
    assert table_diff.is_empty, (
        f"{witness} differs between the two sides ("
        f"{table_diff.total_differences} finding(s)), yet neither cycle should have "
        f"written it: gl072 issues zero GL-Posting-* verbs and gl070 is read-only "
        f"throughout.\n{run.describe()}"
    )

    # CLAIM 2 - neither side changed it AT ALL, measured against the seed.
    for label, produced in (
        (protocol.vocabulary.sides[0], run.paths.cobol_normalized),
        (protocol.vocabulary.sides[1], run.paths.python_normalized),
    ):
        against_seed = protocol.diff_trees_directly(seeded, produced, (witness,))
        assert against_seed.is_empty, (
            f"the {label} run changed {witness}, which no in-scope program of the "
            f"gl_post_cycle route writes. In this comparison the report's `cobol` "
            f"column is THE SEEDED STATE and its `python` column is the state after "
            f"the {label} run.\n{run.describe()}"
        )


@pytest.mark.database
@pytest.mark.oracle
def test_the_stamped_batch_columns_agree_on_both_sides(
    parity, protocol, frozen_schema
) -> None:
    """The two columns `end-batch` stamps must AGREE BETWEEN THE TWO SIDES.

     RENAMED FROM `test_batch_is_stamped_cleared_and_posted`. On this
    route the batch is NOT stamped: A-NEW-18 starves `gl070` so no work record is
    written, `gl072` takes at end on its first read, and the rewrite it performs
    addresses key zero. Measured after a real ten-stage run: `CLEARED-STATUS` 0 and
    `POSTED` 0 on the one seeded row. The old name asserted the opposite outcome, and
    `test_the_gl_route_leaves_the_measured_no_op_on_both_sides` below now pins what
    actually happens.

    `[general/gl072.cbl:L372-L377]` verbatim:

        372|  end-batch.
        375|       move     1  to  cleared-status.
        376|       move     run-date  to  posted.
        377|       perform  GL-Batch-Rewrite.

    and `end-account` runs FIRST [general/gl072.cbl:L286-L289], because inverting
    them "would produce a batch marked posted with an unclosed final account".

    THIS TEST ASSERTS AGREEMENT, NOT A VALUE. It deliberately does NOT assert that
    `CLEARED-STATUS` is 1 or that `POSTED` equals the pinned run date: Agent Action
    Plan section 0.8.2 makes the compiled program the specification, so the question
    is only ever whether the migrated cycle produced what the compiled COBOL
    produced. A test that demanded the arithmetically correct stamp would pass
    against a Python cycle that had "improved" on the COBOL, which is precisely the
    failure R-4 exists to prevent.

    `POSTED` IS AN INTEGER, NOT DATE TEXT. It is `int(8) unsigned`
    [mysql/ACASDB.sql:L88] from `binary-long` [copybooks/wsbatch.cob:L38], so
    normalisation job 3 does not touch it - and `CLEARED-STATUS` is
    `tinyint(1) unsigned` [mysql/ACASDB.sql:L84] from `pic 9`
    [copybooks/wsbatch.cob:L29], whose display width is one of the quirks preserved
    rather than fixed.

    Args:
        parity: The completed, guarded `ParityRun`.
        protocol: The protocol bundle, for the dump reader and the side labels.
        frozen_schema: The parsed `mysql/ACASDB.sql`, used only to confirm the two
            columns exist and to locate them by name rather than by position.

    Raises:
        Skipped: The harness Compose stack is not usable.
        AssertionError: The two sides disagree about either stamped column.
    """
    table = BATCH_TABLE
    stamped = ("CLEARED-STATUS", "POSTED")
    for column in stamped:
        assert column in frozen_schema[table], (
            f"{table}.{column} is not declared by mysql/ACASDB.sql; the frozen "
            f"schema and this assertion have drifted apart."
        )

    run = parity

    def stamps(tree) -> dict[object, tuple[object, ...]]:
        """Read the two stamped columns of every row, keyed by primary-key VALUE.

        Args:
            tree: A normalised tree.

        Returns:
            `{primary-key value: (CLEARED-STATUS, POSTED)}`. Keyed by VALUE and never
            by position, exactly as the differ aligns rows.
        """
        dump = protocol.read_dump(tree / f"{table}.json")
        protocol.assert_dump_wellformed(
            dump, where=str(tree), schema=frozen_schema
        )
        columns = list(dump["columns"])
        key_index = columns.index(dump["primary_key"])
        wanted = [columns.index(column) for column in stamped]
        return {
            row[key_index]: tuple(row[index] for index in wanted)
            for row in dump["rows"]
        }

    cobol_stamps = stamps(run.paths.cobol_normalized)
    python_stamps = stamps(run.paths.python_normalized)

    # Exact equality, with no tolerance and no coercion: a type mismatch - `1`
    # against `"1"` - IS a difference, here as in the differ itself.
    assert python_stamps == cobol_stamps, (
        f"the two sides disagree about the columns `end-batch` stamps "
        f"[general/gl072.cbl:L375-L377]. Read as {{{table} key: "
        f"({', '.join(stamped)})}}:\n"
        f"  cobol : {sorted(cobol_stamps.items(), key=repr)}\n"
        f"  python: {sorted(python_stamps.items(), key=repr)}\n"
        f"Whatever the compiled COBOL stamped is correct by definition; the "
        f"migrated cycle must reproduce it, not improve on it.\n{run.describe()}"
    )
    # The batch was actually reached. An empty table on both sides would satisfy the
    # equality above while proving nothing at all, which is the same false-pass shape
    # as `system.file_system_used = 0`.
    assert cobol_stamps, (
        f"{table} came back with no rows on the oracle side, so the stamping "
        f"assertion proved nothing. The seeded fixture must carry one General "
        f"Ledger batch: WS-Ledger 1 so GL-Batch holds "
        f"[copybooks/wsbatch.cob:L15-L16], Batch-Status 1 so Status-Closed holds "
        f"[copybooks/wsbatch.cob:L25-L27], Cleared-Status 0 so Waiting holds "
        f"[copybooks/wsbatch.cob:L29-L31], and Bcycle equal to Cyclea "
        f"[copybooks/wsbatch.cob:L34]."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_system_record_parity_by_digest_as_well_as_by_dump(parity: object, protocol: object) -> None:
    """THE PARAMETER ROW IS BOUNDED TWICE - by the dump, and by a digest of it.

    WHAT THIS CLOSES. The tempting shortcut is to keep `SYSTEM-REC` off every scenario's
    `affected_tables` on the ground that no side writes it. THAT GROUND IS FALSE:
    `acas_posting/cli/args.py`'s `overrewrite` reproduces
    [general/general.cbl:L656-L672] and every one of the seven routes calls it, so the
    parameter row is written on BOTH sides of every scenario. Until this assertion
    existed, a regression in that persistence produced an EMPTY DIFF and a green run.

    WHICH KEYS THIS ROUTE WRITES. `gl_post_cycle` binds `general_menu_state`, which
    carries BOTH the defaults record and the totals record, so `overrewrite` rewrites
    KEY 1 (`SYSTEM-REC`), KEY 2 (`SYSDEFLT-REC`) and KEY 4 (`SYSTOT-REC`) - the widest
    of the three shapes, and the same three the COBOL General menu writes
    [general/general.cbl:L659, L664, L667].

    IT IS DUMPED, WITH EXACTLY TWO CELLS WITHHELD. `SYSTEM-REC` is one of the 22
    in-scope tables every capture covers, so 167 of its 169 columns are compared by value
    like any other table's. The two exceptions are credentials - `RDBMS-PASSWD char(12)`
    [copybooks/wssystem.cob:L139] and `PASS-WORD` - and a capture is evidence that gets
    committed, so `harness/dump_tables.py`'s `REDACTED_COLUMNS` replaces those two cells
    with a fixed marker inside `render_value`, the one funnel every captured cell passes
    through. That is keyed by `(table, column)` and applied identically on both sides, so
    it cannot itself produce a difference. Bounding the whole table out instead - the
    alternative that was considered and rejected - removes the leak and takes 167
    genuinely-written columns with it, and a bound drawn that way cannot reveal a
    difference in what it excludes.

    AND BOTH RUNNERS FINGERPRINT IT ANYWAY, before and after every run, which is what
    this test compares. A sha256 over the canonical primary-key-ordered dump covers all
    169 columns, credentials included, without being the dump - so the two withheld cells
    are still compared, inside a hash that leaks nothing. The credential columns come from
    the environment and are identical for both sides of one run, so they cannot
    manufacture a difference; anything that does differ is a difference in what the two
    cycles wrote. MEASURED, so the second-order worry is stated with its limit: the row's
    content depends on what the route DID - the run-date stamp, the IRS allocator, the
    one-shot latches, and `Date-Form`, which the frozen date sections write back
    [copybooks/wssystem.cob:L127] - and the digest HOLDS on all four scenarios that
    declare `unchanged` and MOVES on every one that declares `changed`. That was measured
    over the eight committed scenarios, which is all four `unchanged` ones. THE `changed`
    HALF IS NOT COVERED BY ANY COMMITTED SCENARIO: it was established on a definition that
    declared `changed` and moved the row by construction, its Phase 5 advancing the cycle
    and rotating the quarter counter, and no scenario in `harness/scenarios/` does that.
    So declaring the row falsifies no effect claim; the digest is the belt to the dump's
    braces.

    Args:
        parity: The completed, guarded run. The assertion needs its
            artifact layout, and taking the fixture is what orders this test after the
            two run stages rather than a comment claiming it.
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


# ---------------------------------------------------------------------------
#  THE ACCEPTANCE CRITERION THIS ROUTE CANNOT MEET, PINNED RATHER THAN NARRATED
#
#
#  Agent Action Plan section 0.8.5 lists "clean batch post per ledger" among the
#  acceptance criteria, and for the General Ledger the natural reading of "post" is a
#  nominal-ledger balance moving. THIS ROUTE CANNOT DEMONSTRATE THAT, and the reason is
#  a frozen defect rather than a gap in the fixture: anomaly A-NEW-18 (working alias
#  `N-KEY`). `move WS-Post-Key to HV-POST-KEY` [common/glpostingMT.cbl:L1054] moves a
#  ten-byte GROUP into `PIC 9(18) COMP` [common/glpostingMT.cbl:L283], which is a byte
#  move rather than a numeric conversion, so the key does not survive the round trip in
#  a form `gl070` will accept and its guard `if batch not = WS-Batch-Nos`
#  [general/gl070.cbl:L492-L493] discards the row. Independently, the bridge never loads
#  `HV-POST-RRN` [common/glpostingMT.cbl:L1053-L1066] while `POST-RRN` is the primary
#  key [mysql/ACASDB.sql:L155,:L169], so a seed persists AT MOST ONE posting row.
#
#  WHY AN EMPTY DIFF IS NOT ENOUGH ON ITS OWN. The state-parity test above is symmetric:
#  it passes if the two sides agree, whether they agree on a no-op or on a balance
#  movement. So it cannot be cited as evidence for EITHER. This section makes the
#  measured outcome an ASSERTION, in absolute terms and on both sides, so that the
#  criterion's unavailability is a locked fact rather than a paragraph of prose - and so
#  that the day the frozen path changes, or a fixture starts reaching the posting walk,
#  this test fails and the shortfall is re-examined instead of being quietly inherited.
#
#  THIS IS NOT A CORRECTNESS CLAIM AND MUST NOT BE READ AS ONE. Nothing here says the
#  no-op is right. It says the compiled oracle produced it (measured, and recorded in
#  A-NEW-18's own step 5), so R-4 requires the migrated cycle to produce it too. The GL
#  arithmetic that this route therefore does NOT exercise is held by the arithmetic tier:
#  `tests/arithmetic/test_double_entry_explosion.py` for gl070's three-leg explosion and
#  `tests/arithmetic/test_ledger_balance_accumulation.py` for gl072's accumulation.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_the_gl_route_leaves_the_measured_no_op_on_both_sides(
    parity, protocol, frozen_schema
) -> None:
    """A-NEW-18's consequence, asserted ABSOLUTELY rather than by agreement.

    Three measured facts, each required on BOTH sides independently:

      * every `GLLEDGER-REC` balance is zero - no account moved;
      * the seeded `GLBATCH-REC` row is unstamped - `CLEARED-STATUS` and `POSTED` both
        zero, because `end-batch`'s rewrite addressed key zero;
      * at most one `GLPOSTING-REC` row exists - the never-loaded `HV-POST-RRN`.

    Each side is checked on its own, not against the other, which is exactly what the
    symmetric diff cannot do.

    Args:
        parity: The completed, guarded `ParityRun`.
        protocol: The protocol bundle, for the dump reader and the side labels.
        frozen_schema: The parsed `mysql/ACASDB.sql`, to locate columns by name.

    Raises:
        Skipped: The harness Compose stack is not usable.
        AssertionError: A side departed from the measured no-op - which means either
            the frozen path changed or the criterion has become reachable. Both are
            findings, not failures to paper over.
    """
    from decimal import Decimal  # noqa: PLC0415 - see the module docstring on R-2

    def column_values(tree, table: str, column: str) -> list[object]:
        """Every row's value for one column, in dump order.

        Args:
            tree: A normalised dump tree.
            table: The table name.
            column: The column name.

        Returns:
            The values.
        """
        dump = protocol.read_dump(tree / f"{table}.json")
        protocol.assert_dump_wellformed(dump, where=str(tree), schema=frozen_schema)
        index = list(dump["columns"]).index(column)
        return [row[index] for row in dump["rows"]]

    for side, tree in (
        #  Side labels from the protocol's own vocabulary, as every sibling test in
        #  this file does, so one place names them.
        (protocol.vocabulary.sides[0], parity.paths.cobol_normalized),
        (protocol.vocabulary.sides[1], parity.paths.python_normalized),
    ):
        #  1. NO BALANCE MOVED. Compared as `Decimal` against `Decimal`, because the
        #  column is `decimal(10,2)` and a string comparison would pass on "0" and fail
        #  on "0.00" for reasons that have nothing to do with the accounting.
        balances = column_values(tree, LEDGER_TABLE, "LEDGER-BALANCE")
        assert balances, (
            f"{side}: `{LEDGER_TABLE}` came back with no rows, so this assertion "
            f"proved nothing. The fixture must seed the nominal accounts the batch "
            f"references."
        )
        nonzero = [value for value in balances if Decimal(str(value)) != Decimal("0")]
        assert not nonzero, (
            f"{side}: `{LEDGER_TABLE}.LEDGER-BALANCE` is non-zero on {len(nonzero)} "
            f"row(s): {nonzero!r}.\n"
            f"  A BALANCE MOVED, AND ON THIS ROUTE ONE CANNOT. Anomaly A-NEW-18 "
            f"starves `gl070`: the corrupted `POST-KEY` fails the guard at "
            f"[general/gl070.cbl:L492-L493], no work record is written, and `gl072` "
            f"takes at end on its first read. If this now fails, DO NOT relax it - "
            f"either the frozen bridge changed, or the fixture has begun reaching the "
            f"posting walk, and in either case Agent Action Plan section 0.8.5's GL "
            f"acceptance criterion has become reachable and must be re-stated in "
            f"docs/migration/scenario-diff-evidence.md, harness/scenarios/clean_batch_gl.yaml "
            f"and A-NEW-18 together."
        )

        #  2. THE BATCH IS UNSTAMPED. `end-batch` ran - that is locked by
        #  tests/arithmetic/test_ledger_balance_accumulation.py's
        #  test_the_empty_work_file_still_performs_end_account_then_end_batch - and
        #  its rewrite addressed key zero, so the seeded row is untouched.
        cleared = column_values(tree, BATCH_TABLE, "CLEARED-STATUS")
        posted = column_values(tree, BATCH_TABLE, "POSTED")
        assert cleared and posted
        assert all(int(value) == 0 for value in cleared), (
            f"{side}: `{BATCH_TABLE}.CLEARED-STATUS` is {cleared!r}. `88 Waiting` is "
            f"value 0 [copybooks/wsbatch.cob:L29-L31], and a stamped batch would mean "
            f"`end-batch`'s rewrite [general/gl072.cbl:L375-L377] reached a real row - "
            f"which A-NEW-18 step 5 measured that it does not."
        )
        assert all(int(value) == 0 for value in posted), (
            f"{side}: `{BATCH_TABLE}.POSTED` is {posted!r} rather than the seeded zero."
        )

        #  3. AT MOST ONE POSTING ROW SURVIVED THE SEED. The never-loaded
        #  `HV-POST-RRN` is a different link of A-NEW-18 from the corrupted key, and
        #  it is asserted separately so a reader can tell which one moved.
        posting_keys = column_values(tree, POSTING_TABLE, "POST-RRN")
        assert len(posting_keys) <= 1, (
            f"{side}: `{POSTING_TABLE}` holds {len(posting_keys)} rows. The bridge "
            f"never loads `HV-POST-RRN` [common/glpostingMT.cbl:L1053-L1066] while "
            f"`POST-RRN` is the primary key [mysql/ACASDB.sql:L155,:L169], so every "
            f"loader write targets the same key and a second row is a duplicate. More "
            f"than one row means the loader path changed."
        )
        assert all(int(value) == 0 for value in posting_keys), (
            f"{side}: `{POSTING_TABLE}.POST-RRN` is {posting_keys!r}; the "
            f"never-loaded host variable leaves it at its `initialize` value."
        )
