"""GENERAL LEDGER CLEAN-BATCH STATE PARITY - the reference happy path.

Scenario `clean_batch_gl`, subsystem `general`, operation `gl_post_cycle`. One closed,
proofed General Ledger batch sitting in the pinned accounting cycle is posted end to
end, and the resulting table state must match the compiled COBOL oracle BYTE FOR BYTE
after normalisation. This is the FIRST of the eight scenario files and it establishes
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
`test_batch_is_stamped_cleared_and_posted` is framed as "both sides agree" and never as
"the value is 1".

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none was
provided, so there is no on-disk rules file and no reader should look for one. The six
binding rules R-1 to R-6 live in the Agent Action Plan itself, section 0.7.2, and their
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
affects the alignment of the trailing fields, and only execution shows which. It is
carried as ambiguity `Q-4` and arbitrated against the compiled oracle, never resolved
by reasoning.

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
POST. There is NO `DUPLICATES IN ORDER` phrase, so a tie on all four keys has
unspecified relative order - carried as ambiguity `Q-SORT-TIE-ORDER`, and provably
harmless here because gl072's only state mutation for a posting is the COMMUTATIVE add
at `[general/gl072.cbl:L331]`. gl071 is a PURE SORT: measured over the whole file, zero
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
    GL-Nominal-Open      [general/gl072.cbl:L277]
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

import conftest

pytestmark = pytest.mark.scenario

SCENARIO = "clean_batch_gl"


def test_scenario_definition_preconditions(pinned_clock) -> None:
    """Assert the preconditions that make this scenario's verdict mean anything.

    Each one closes a real FALSE-PASS hole, each is cheap, and none needs the stack.
    The definition is read through `tests/conftest.py`'s `scenario_definition`, which
    parses it with `yaml.safe_load`; this file opens no YAML and imports no parser.

    Args:
        pinned_clock: The project-wide pinned run date. The fixture itself asserts
            that the pair equals `PINNED_RUN_DATE_TEXT` and `PINNED_RUN_DATE_BINARY`,
            so referencing it is how the pinned values reach this test without a
            literal being retyped anywhere.

    Raises:
        AssertionError: A precondition does not hold.
    """
    definition = conftest.scenario_definition(SCENARIO)

    # The scenario names itself, and the operation is one of the seven both runners
    # share. `subsystem` is DERIVED from the operation rather than re-declared here:
    # `conftest.OPERATIONS` maps gl_post_cycle to ("general", "H", "load08",
    # "general/general.cbl:L805-L815"), the menu paragraph quoted in this module's
    # docstring.
    assert definition["name"] == SCENARIO
    operation = definition["operation"]
    assert operation in conftest.OPERATIONS, (
        f"{SCENARIO} declares operation {operation!r}, which is not one of the "
        f"seven the two runners share: {', '.join(conftest.OPERATIONS)}."
    )
    subsystem, _menu_key, _paragraph, _locator = conftest.OPERATIONS[operation]
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
    assert 0 not in conftest.TERM_CODES[operation], (
        "zero must not be an admissible term code, or 'no abort' and 'aborted' "
        "would be indistinguishable in the expected status."
    )
    # The only term code reachable on this route is 5. Both of the term-code-8 raise
    # sites - [sales/sl055.cbl:L344] and [purchase/pl055.cbl:L286] - sit inside
    # `if FS-Cobol-Files-Used` blocks [sales/sl055.cbl:L326],
    # [purchase/pl055.cbl:L266], so with file_system_used 1 neither is reachable at
    # all. `expected_status: 0` here is therefore provable rather than assumed.
    assert conftest.TERM_CODES[operation] == (5,)

    # -------------------------------------------------------------------------
    # THE FALSE-PASS TRAP. [copybooks/wssystem.cob:L111-L114]:
    #     111         05  RDBMS-Flat-Statuses.
    #     112             07  File-System-Used  pic 9.
    #     113                 88  FS-Cobol-Files-Used    value zero.
    #     114                 88  FS-MySql-Used          value 1.
    # and the GL-Batch handler [common/acas007.cbl:L316-L320]:
    #     316       if       not FS-Cobol-Files-Used
    #     317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
    #     318                perform  ba-Process-RDBMS
    #     319                go to AA-Main-Exit
    #     320       end-if.
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
    assert clock["to_day"] == conftest.PINNED_RUN_DATE_TEXT
    assert clock["run_date"] == conftest.PINNED_RUN_DATE_BINARY
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
    assert definition[conftest.SCENARIO_KEY_RUN_DATE_TEXT] == clock["to_day"]
    assert definition[conftest.SCENARIO_KEY_RUN_DATE_BINARY] == clock["run_date"]

    # THE IRS FAN-OUT SWITCH, PINNED EXPLICITLY. [copybooks/wssystem.cob:L179-L181]:
    #     179         05  IRS-Instead     pic x.
    #     180             88  IRS-Used                   value "Y".
    #     181             88  IRS-Both-Used              value "B".   *> 26/11/16
    # THREE states, and the third - a space, General Ledger only - HAS NO CONDITION
    # NAME AT ALL: both predicates are simply False. Agent Action Plan section 0.6.4:
    # "leaving it at a default would make the affected-table list ambiguous", so it
    # is pinned rather than defaulted. A YAML space maps to the CLI token "N" while
    # the column still stores a space, and normalisation job 1 trims that to the
    # empty string on BOTH sides - correct, because it is applied identically.
    assert system[conftest.SCENARIO_KEY_IRS_INSTEAD] in conftest.IRS_INSTEAD_STATES
    assert system[conftest.SCENARIO_KEY_IRS_INSTEAD] == conftest.IRS_INSTEAD_GL_ONLY
    assert (
        definition[conftest.SCENARIO_KEY_IRS_INSTEAD]
        == system[conftest.SCENARIO_KEY_IRS_INSTEAD]
    )

    # THE ACCOUNTING CYCLE. [copybooks/wssystem.cob:L62-L64]:
    #     62         05  Cyclea          binary-char.  *> 99.
    #     63         05  Scycle Redefines cyclea  binary-char.
    #     64         05  Period          binary-char.  *> 99.
    # The seeded batch's `Bcycle` [copybooks/wsbatch.cob:L34] must equal it, or
    # [general/gl070.cbl:L312-L313] skips the batch on BOTH passes and nothing is
    # posted at all - a run that looks clean and proves nothing.
    assert system["cyclea"] != 0, (
        "system.cyclea must be non-zero: `Scycle` redefines it "
        "[copybooks/wssystem.cob:L62-L63] and both cycle filters compare the "
        "batch's Bcycle against it [general/gl070.cbl:L312-L313, L457-L458]."
    )
    # `period` is pinned for completeness and is INERT in all eight scenarios,
    # because the only consumer of the period is gl080 and `gl_end_of_cycle` appears
    # in no scenario file. That omission is deliberate and oracle-reversible; it is
    # recorded in docs/migration/ambiguity-resolutions.md rather than settled here.
    assert system["period"] != 0

    # The date presentation form, pinned in both the grouped block and its flat
    # mirror. UK dd/mm/yyyy, which is the form `to-day pic x(10)` carries above.
    assert system[conftest.SCENARIO_KEY_DATE_FORM] == conftest.DATE_FORM_UK
    assert (
        definition[conftest.SCENARIO_KEY_DATE_FORM]
        == system[conftest.SCENARIO_KEY_DATE_FORM]
    )

    # THE SEED CONTRACT - four flat files, each a name the frozen loader script
    # recognises. system.dat drives the four-loader system block, in a fixed order
    # and unconditionally [common/masterLD.sh:L51-L87]; ledger.dat goes to nominalLD
    # [common/masterLD.sh:L103]; batch.dat to glbatchLD [common/masterLD.sh:L94];
    # posting.dat to glpostingLD [common/masterLD.sh:L109]. The remaining three map
    # one-to-one onto the affected tables.
    seed_files = tuple(definition[conftest.SCENARIO_KEY_SEED_FILES])
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
        conftest.SCENARIO_KEY_IRS_CLEAR_POSTINGS,
        "payment_post_confirm",
        "gl080_proceed",
        "disk_change_option",
    ):
        assert answer_key not in definition, (
            f"{SCENARIO} declares the answer key {answer_key!r}, which the "
            f"gl_post_cycle route never consumes. Its presence would promote an "
            f"input the frozen cycle does not take."
        )


def test_affected_tables_are_in_scope_and_alphabetical(harness) -> None:
    """Assert the affected-table list is exactly the three, in the declared order.

    THIS LIST IS THE ONLY THING THAT BOUNDS THE COMPARISON. There is no ignore-list,
    no tolerance-list and no "known difference" allowance anywhere in the diff path,
    so if the list is wrong the verdict is wrong in one of the two dangerous
    directions: too narrow and a real difference is never looked at, too wide and a
    menu-shell side effect the migration does not reproduce reports a false failure.

    THE ORDER IS LOAD-BEARING. `harness/run_python_scenario.sh` writes its
    `<TABLE> <count>` seed-fingerprint lines in the list's DECLARED order and reports
    a harness fault when the two sides' fingerprints differ, and
    `harness/diff_states.py` reports its tables in that same order.

    Args:
        harness: The three harness Python modules, loaded by explicit file path
            (R-1). `IN_SCOPE` and every primary key are read from
            `harness/dump_tables.py` and are never re-declared here.

    Raises:
        AssertionError: The list is not the expected three, is not ascending, or
            names something that is not an in-scope table.
    """
    tables = conftest.scenario_affected_tables(SCENARIO)

    # GLBATCH-REC  - rewritten by gl072's end-batch [general/gl072.cbl:L372-L377].
    # GLLEDGER-REC - rewritten by gl072's end-account [general/gl072.cbl:L379-L382].
    # GLPOSTING-REC- READ ONLY on this route, and listed so the diff PROVES it.
    assert tables == ("GLBATCH-REC", "GLLEDGER-REC", "GLPOSTING-REC")

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

    # BOUNDING IS NOT IGNORING, and the exclusions below are bounding. A census over
    # all twelve in-scope programs finds ZERO `System-*` facade verbs, so no in-scope
    # program persists SYSTEM-REC, SYSDEFLT-REC, SYSFINAL-REC or SYSTOT-REC. What
    # does persist them is the MENU SHELL's exit path [general/general.cbl:L656-L691]:
    #     656  overrewrite.
    #     657       if       File-System-Used NOT = zero
    #     664                move     2 to File-Key-No       <- KEY 2
    #     667                move     4 to File-Key-No       <- KEY 4
    # writing keys 1, 2 and 4 to both stores. The Python command line has no menu and
    # never does this, so comparing those tables here would report a FALSE FAILURE.
    # (Verified divergence worth knowing: the Sales and Purchase `overrewrite`
    # paragraphs persist keys 1 and 4 only, NEVER key 2 - [sales/sales.cbl:L628-L657]
    # and [purchase/purchase.cbl:L621-L650] - which is why SYSDEFLT-REC appears on no
    # scenario's affected-table list at all. SYSTOT-REC is NOT blanket-excluded: it
    # is genuinely in scope for period_end_totals, whose nine period-total write
    # sites are its sole writers. The reasoning is shared, and the persistence
    # question is recorded in docs/migration/ambiguity-resolutions.md.)
    for excluded in ("SYSTEM-REC", "SYSDEFLT-REC", "SYSFINAL-REC", "SYSTOT-REC"):
        assert excluded in in_scope, "the four system tables are in scope overall"
        assert excluded not in tables

    # The four autogen tables are never seeded and appear on no affected-table list,
    # because [sales/sales.cbl:L759] dispatches the out-of-scope sl830 on the COBOL
    # side only. Both runners assert after their run that all four are still empty;
    # that assertion lives in the runners, not here.
    for autogen in conftest.AUTOGEN_TABLES:
        assert autogen not in tables


# ---------------------------------------------------------------------------
#  THE FIVE REJECTION CLASSES - none exercised here, and the taxonomy is
#  deliberate. Agent Action Plan section 0.8.1 requires that a rejected
#  transaction reach the same disposition AND leave the same effect on the
#  database, and "a single generic rejection path would fail this directive".
#  The five differ precisely in that second dimension:
#
#    1. CLEAN REJECTION, NO DATABASE EFFECT - the two entirely silent skips,
#       [general/gl072.cbl:L291-L292] on a non-numeric batch number and
#       [general/gl072.cbl:L306-L307] on `we-error = 999`, with a second
#       `we-error` site at [general/gl072.cbl:L348-L349]. No message, no
#       counter, no trace (A-13). Exercised by `mixed_accepted_rejected`.
#    2. RUN-ABORTING REJECTION - a control-total mismatch leaves the batch open,
#       gl070 raises 5 [general/gl070.cbl:L289], the menu gate
#       [general/general.cbl:L810-L811] returns to the menu, and gl071 and gl072
#       NEVER RUN. The database effect is THE ABSENCE of everything the later
#       phases would have written, and absence is evidence. Exercised by
#       `control_total_mismatch`.
#    3. PARTIAL DATABASE EFFECT - the IRS half-posted double entry
#       [irs/irs030.cbl:L1635-L1652] (A-4) and the lost update on the two VAT
#       control accounts, snapshotted at [irs/irs030.cbl:L1602] and
#       [irs/irs030.cbl:L1612] and rewritten from those snapshots at
#       [irs/irs030.cbl:L1704-L1708] (A-5). Exercised by `clean_batch_irs`.
#    4. FILE-ABANDONING REJECTION - a posting-record write failure jumps straight
#       to end of job [irs/irs030.cbl:L1673-L1678], which still performs the two
#       snapshot rewrites and the closes, so THE PARTIAL STATE IS COMMITTED, NOT
#       ROLLED BACK.
#    5. PERMANENTLY FAILING FACADE VERB - the transfer-file handler refuses four
#       of its published verbs unconditionally at entry, each answered with
#       `WE-Error 988` and `fs-reply 99` [common/acas008.cbl:L299-L307] (A-6), so
#       the published Rewrite verb can never succeed.
#
#  A CLEAN BATCH TRIPS NONE OF THEM. That is not asserted by inspecting a
#  counter - no counter exists - but by the empty diff over the three bounded
#  tables, which is the only evidence the specification affords.
# ---------------------------------------------------------------------------


def test_clean_batch_post_gl_state_parity(harness) -> None:
    """THE HEADLINE. Drive all eight protocol stages and demand an EMPTY diff.

    The eight stages, in the exact order, and none skipped:

        1  harness/seed.sh
        2  harness/run_cobol_scenario.sh
        3  harness/dump_tables.py  --scenario clean_batch_gl --side cobol
        4  harness/normalize.py
        5  harness/reset_db.sh
        6  harness/run_python_scenario.sh
        7  harness/dump_tables.py  --scenario clean_batch_gl --side python
        8  harness/diff_states.py

    They are driven through `tests/conftest.py`'s `run_scenario_parity`, which is
    what makes Agent Action Plan section 0.4.3 true - "no test reimplements the
    comparison protocol". Nothing here iterates a row, re-implements `diff_table`,
    or builds a command line.

    ALWAYS DUMP, THEN DECIDE THE STATUS. The two run stages' exit codes are recorded
    and are never allowed to skip the dump that follows them, because Agent Action
    Plan section 0.6.5 says of a run-aborting rejection that "the database effect is
    therefore THE ABSENCE of everything the later phases would have written". For
    `clean_batch_gl` the expected status is 0 and no abort is expected, but the
    discipline is uniform across all eight scenario files and is written the same way
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
    such questions already touch this scenario: `Q-4`, the batch-record length
    contradiction at [copybooks/wsbatch.cob:L7-L9], and `Q-SORT-TIE-ORDER`, the
    unspecified relative order of records tying on all four of gl071's keys
    [general/gl071.cbl:L172-L178]. The General Ledger caveat makes this
    non-negotiable: the maintainer records at [README.TXT:L50-L53] that testing is
    complete for IRS, Stock and Sales but that he has "not had any time to work with
    General at all since it was migrated over to using the GnuCobol compiler (3.2
    final)", and the General Ledger contributes the majority of the in-scope
    programs. So if the compiled cycle behaves surprisingly, THE SURPRISE IS THE
    SPECIFICATION - no expected value for this scenario may be derived from
    documentation or from reasoning about intent.

    Args:
        harness: The three harness Python modules (R-1), for `render`.

    Raises:
        Skipped: The harness Compose stack is not usable; the reason names every
            missing precondition.
        HarnessFaultError: A stage whose failure destroys the evidence failed, or a
            run stage returned a status nobody has classified.
        AssertionError: The two normalised trees differ - a real behavioural
            difference between the compiled COBOL and the migrated cycle.
    """
    conftest.requires_stack()

    definition = conftest.scenario_definition(SCENARIO)
    operation = definition["operation"]
    expected_status = list(definition["expected_status"])

    run = conftest.run_scenario_parity(SCENARIO)

    # The comparison was bounded by the scenario's own list, in its own order.
    assert run.tables == conftest.scenario_affected_tables(SCENARIO)

    # A HARNESS FAULT IS RAISED, NEVER ASSERTED. `classify_run` reports an
    # unrecognised status as a fault rather than quietly treating it as either of the
    # other two, because a status nobody has classified is a status nobody should
    # draw a conclusion from.
    for label, stage_result in (
        (conftest.SIDE_COBOL, run.cobol_run),
        (conftest.SIDE_PYTHON, run.python_run),
    ):
        disposition = conftest.classify_run(stage_result, operation=operation)
        if disposition == conftest.DISPOSITION_HARNESS_FAULT:
            raise conftest.HarnessFaultError(
                f"the {label} run stage could not be judged:\n"
                f"{stage_result.describe()}\n"
                f"  A harness fault means the question was never asked, so there "
                f"is no evidence to compare - `argparse` exit "
                f"{conftest.ARGPARSE_USAGE_EXIT} in particular means the runner "
                f"built a bad command line. It is reported as an error and never "
                f"as a behavioural difference."
            )

    # AN OBSERVED STATUS THAT CONTRADICTS THE SCENARIO IS A BEHAVIOURAL DIFFERENCE.
    # The dump has already been taken by this point, so the table diff below still
    # corroborates whatever actually happened.
    observed = [run.cobol_run.returncode, run.python_run.returncode]
    assert observed == expected_status * 2, (
        f"the two runs ended {observed} where {SCENARIO} expects "
        f"{expected_status} for each side. The term-code mapping is the identity, "
        f"so 5 means gl070 raised the open-batch abort "
        f"[general/gl070.cbl:L289] and the hard gate "
        f"[general/general.cbl:L810-L811] stopped the cycle before gl071 and gl072 "
        f"ever ran.\n{run.describe()}"
    )

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
        f"{harness.diff_states.render(run.tree)}\n"
        f"{run.describe()}"
    )


# ---------------------------------------------------------------------------
#  R-3 SEEDING AND SCHEMA CONSTRAINTS - documented here, implemented nowhere
#  here. This file emits no DDL and issues no statement of its own.
#
#    NO DDL. The seeded schema is mysql/ACASDB.sql applied VERBATIM. It already
#    carries all 33 `DROP TABLE IF EXISTS`, so re-applying it IS the
#    drop-and-recreate; the database name must be on the client command line
#    because the file has no `USE`. Census: 33 `CREATE TABLE`, 33 `DROP TABLE IF
#    EXISTS`, 0 real `ALTER TABLE`, 0 `CREATE INDEX`, 0 `CREATE DATABASE`, 0
#    `USE`, 0 `INSERT INTO`, 0 `FLOAT`/`DOUBLE`/`REAL`, 0 `TIMESTAMP`.
#
#    AUTOCOMMIT MUST BE OFF WHILE SEEDING, asserted as `0, 0` by
#    `conftest.assert_autocommit_off` and by harness/seed.sh, and SET by
#    harness/Dockerfile.mariadb alone. The batch loader says so itself,
#    [common/glbatchLD.cbl:L9-L12] verbatim:
#        9  *>  This modules uses commit and rollback so *
#       10  *>  you MUST ensure that autocommit is OFF   *
#       11  *>   in the rdb settings. It is as default   *
#       12  *>   set ON.                                 *
#
#    common/masterLD.sh IS NEVER INVOKED, for three verified reasons: its own
#    header says "THIS SCRIPT HAS NOT YET BEEN TESTED" [common/masterLD.sh:L4];
#    it is not valid shell - all 24 loader lines [common/masterLD.sh:L93-L116]
#    omit the `;` before `fi`, so `bash -n` rejects a 123-line file at line 124;
#    and it ends by paging SYS-DISPLAY.log through `less`, which would block a
#    non-interactive run forever. It is FROZEN AND NOT FIXED (R-3, R-4);
#    harness/seed.sh reproduces its documented per-file contract instead
#    [common/masterLD.sh:L44-L115] and checks the loader exit codes, whose values
#    above 63 abort the load.
#
#    R-4 ITEMS PRESERVED RATHER THAN FIXED: the `dfltLD` strict-versus-lenient
#    exit asymmetry, tested with `if [ $rc != 0 ]` at [common/masterLD.sh:L83]
#    where its three siblings tolerate up to 63; the charset caveat, where
#    [mysql/ACASDB.sql:L16] declares `SET NAMES utf8mb4` while all 33 tables
#    declare `DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci`; and the
#    `tinyint(1) unsigned` display-width quirk on GLBATCH-REC's `BATCH-STATUS`
#    [mysql/ACASDB.sql:L83] and `CLEARED-STATUS` [mysql/ACASDB.sql:L84].
#
#    STRICTLY SEQUENTIAL. No test-distribution plugin, no parallelism, no
#    randomised ordering: parallel scenario runs against one shared MariaDB
#    would break the seed/run/dump/reset/run/dump/diff protocol outright.
# ---------------------------------------------------------------------------


def test_diff_exit_contract_is_honoured(tmp_path, harness, frozen_schema) -> None:
    """The THREE-WAY exit contract: 0 is a pass, 1 is a failure, 2 IS NEVER A PASS.

        0  the trees are identical, and stdout is EMPTY - zero bytes, not a banner
           and not "no differences found"                                 -> PASS
        1  a real behavioural difference, with a deterministic report   -> FAILURE
        2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a missing table
           file, a malformed dump, a shape mismatch, a float in the input, a
           duplicate primary key, a wrong key order, `row_count != len(rows)`, a
           ragged row, a null value                                       -> ERROR

    A TEST THAT TREATED "COULD NOT COMPARE" AS "NO DIFFERENCES" IS THE SINGLE WORST
    BUG AVAILABLE IN THIS TREE, so the mapping is asserted directly rather than
    trusted. Rule R-6 makes an empty diff the pass condition ONLY when a comparison
    actually happened.

    IT ASSERTS NOTHING WHATEVER ABOUT THE MIGRATION. The two trees are SYNTHETIC:
    they are built from the frozen schema's own column lists, published through the
    dump stage's own writer and canonicalised by the real normalise stage, so the
    machinery under test is the shipped machinery - but a verdict taken from a
    hand-built tree is not protocol evidence, and none is claimed. That is also why
    this test needs no Compose stack and no compiled oracle: it is the one assertion
    in this file that genuinely executes on a bare host.

    Args:
        tmp_path: A private output root, so `$ACAS_OUT` is neither read nor needed.
        harness: The three harness Python modules (R-1).
        frozen_schema: The parsed `mysql/ACASDB.sql`, READ AND NEVER WRITTEN. It
            supplies every column name and declared type, so nothing is invented.

    Raises:
        AssertionError: An exit status, a stdout stream or a verdict did not match
            the contract.
    """
    dump_tables = harness.dump_tables
    normalize = harness.normalize
    diff_states = harness.diff_states

    tables = conftest.scenario_affected_tables(SCENARIO)
    paths = conftest.scenario_paths(SCENARIO, out_root=tmp_path)

    def publish(side: str, *, bend: bool) -> None:
        """Publish one synthetic side, then canonicalise it through stage 4.

        Args:
            side: `cobol` or `python`.
            bend: Alter exactly one non-key value of the first table, so the two
                sides differ in exactly one column of exactly one row.
        """
        dumps: dict[str, dict[str, object]] = {}
        for table in tables:
            columns = normalize.schema_columns(frozen_schema, table)
            specification = dump_tables.IN_SCOPE[table]
            row: list[object] = []
            for column in columns:
                declared = normalize.column_type(frozen_schema, table, column)
                if declared.kind == normalize.KIND_INTEGER:
                    row.append(0)
                elif declared.kind == normalize.KIND_DECIMAL:
                    # A DECIMAL reaches a dump as a canonical JSON STRING at the
                    # column's declared scale, never as a JSON number (R-2).
                    row.append("0")
                else:
                    row.append("")
            key_index = list(columns).index(specification.primary_key)
            row[key_index] = 1 if isinstance(row[key_index], int) else "1"
            if bend and table == tables[0]:
                victims = [
                    index for index in range(len(columns)) if index != key_index
                ]
                assert victims, (
                    f"{table} has only its primary-key column, so no non-key "
                    f"value can be altered to produce a difference."
                )
                victim = victims[0]
                row[victim] = 7 if isinstance(row[victim], int) else "7"
            # Built from the dump stage's OWN key vocabulary, in its own fixed
            # order, so the five-key shape is never transcribed by hand.
            dumps[table] = dict(
                zip(
                    dump_tables.DUMP_KEYS,
                    (table, specification.primary_key, list(columns), 1, [row]),
                    strict=True,
                )
            )
        dump_tables.publish_dumps(
            dumps,
            tmp_path,
            scenario=SCENARIO,
            side=side,
            selector=dump_tables.SELECTOR_SCENARIO_FILE,
        )
        conftest.normalize(SCENARIO, side, out_dir=tmp_path).raise_for_status()

    # ---- EXIT 0: identical, and NOT ONE BYTE on stdout -------------------
    publish(conftest.SIDE_COBOL, bend=False)
    publish(conftest.SIDE_PYTHON, bend=False)
    identical = conftest.diff(SCENARIO, out_dir=tmp_path)
    assert identical.result.returncode == diff_states.EX_IDENTICAL
    assert identical.is_empty is True
    assert identical.result.stdout == "", (
        f"an identical comparison must write ZERO BYTES to stdout - not a banner, "
        f"not \"no differences found\" - because the empty stream is itself the "
        f"pass signal. It wrote {identical.result.stdout!r}."
    )
    # A PASSING RUN WRITES A ZERO-BYTE REPORT, deliberately: the evidence document
    # must distinguish "compared, and identical" from "never compared", and an
    # existing empty file says the first while an absent file says nothing at all.
    assert identical.report.is_file()
    assert identical.report.stat().st_size == 0

    # ---- EXIT 1: one differing value is a real behavioural difference -----
    publish(conftest.SIDE_PYTHON, bend=True)
    different = conftest.diff(SCENARIO, out_dir=tmp_path)
    assert different.result.returncode == diff_states.EX_DIFFERENT
    assert different.is_empty is False
    assert different.tree.total_differences == 1
    # Stdout carries a value-free summary; the values themselves go to the 0600
    # report. Either way the stream is NOT empty, so exit 1 can never be mistaken
    # for exit 0.
    assert different.result.stdout != ""
    report = diff_states.render(different.tree)
    assert tables[0] in report
    # The two labels are `cobol` and `python`, never left and right.
    assert diff_states.LABEL_COBOL in report
    assert diff_states.LABEL_PYTHON in report

    # ---- EXIT 2: the comparison could not be performed -> RAISED ----------
    # An absent tree is the most dangerous input the comparison can be given,
    # because "nothing to compare" and "nothing differs" are one keystroke apart.
    for member in sorted(paths.python_normalized.iterdir()):
        member.unlink()
    paths.python_normalized.rmdir()
    with pytest.raises(conftest.HarnessFaultError) as raised:
        conftest.diff(SCENARIO, out_dir=tmp_path)
    assert str(diff_states.EX_ERROR) in str(raised.value)
    # AND THE STALE ZERO-BYTE REPORT IS GONE. The comparison invalidates the
    # accepted output the moment the path is known and before a single dump is read,
    # so a report surviving an error path can never be mistaken for proof that this
    # run passed.
    assert not paths.diff_report.exists()


# ---------------------------------------------------------------------------
#  NORMALISATION DOES EXACTLY THREE THINGS, AND THERE IS NO FOURTH. Every part
#  of it is delegated to harness/normalize.py; nothing is reimplemented or
#  extended here. The obligation runs both ways: remove the representation
#  artefacts, and NEVER make two genuinely different stored values compare
#  equal, so that Agent Action Plan section 0.6.6 holds.
#
#    JOB 1 - TRAILING SPACES IN FIXED-CHARACTER COLUMNS. `rstrip(" ")`, TRAILING
#    ONLY, ASCII U+0020 only, by DECLARED type including `char(1)`. Leading
#    spaces are CONTENT, because a COBOL alphanumeric MOVE is left-justified with
#    right padding. Motivated by A-12: `pic x(24)`
#    [copybooks/wsledger.cob:L27] becomes `PIC X(32)`
#    [common/nominalMT.cbl:L299] and `` `LEDGER-NAME` char(32) NOT NULL, ``
#    [mysql/ACASDB.sql:L127]. The schema declares 238 `char(` columns and zero
#    `varchar(`.
#
#    JOB 2 - DECIMAL SCALE RENDERING AT THE DECLARED SCALE, which is NOT
#    uniformly 2: 68 columns are (9,2), 57 are (10,2), 17 are (4,2), 12 are
#    (5,2), 4 are (14,2), 2 are (2,0), 2 are (14,4), plus singletons. A value
#    implying MORE places RAISES rather than rounds, because rounding there would
#    hide a real finding. GLBATCH-REC's four money columns are
#    `decimal(14,2) unsigned` [mysql/ACASDB.sql:L90-L93], matching the UNSIGNED
#    `pic 9(9)v99 comp-3` under the group at [copybooks/wsbatch.cob:L40-L44];
#    GLLEDGER-REC.LEDGER-BALANCE [mysql/ACASDB.sql:L128] derives from
#    `pic s9(8)v99 comp-3` [copybooks/wsledger.cob:L28].
#
#    JOB 3 - THE TWO- VERSUS FOUR-DIGIT DATE TEXT FORMS, under an EXPLICIT
#    FIVE-COLUMN ALLOW-LIST and nothing else: GLPOSTING-REC.POST-DAT,
#    IRSPOSTING-REC.POST4-DAT, PSIRSPOST-REC.IRS-POST-DAT,
#    SYSTEM-REC.STATS-DATE-PERIOD and SALEDGER-REC.SALES-STATS-DATE. `char(8)`
#    DOES NOT IMPLY DATE - PUITM5-REC.OI5-BATCH and SAITM3-REC.OI3-BATCH are
#    batch references and are excluded. And MOST in-scope "dates" are BINARY DAY
#    NUMBERS that job 3 must not touch: GLBATCH-REC's ENTERED, PROOFED, POSTED
#    and STORED are all `int(8) unsigned` [mysql/ACASDB.sql:L86-L89], from the
#    four `binary-long` fields at [copybooks/wsbatch.cob:L36-L39], so
#    [general/gl072.cbl:L376]'s `move run-date to posted` stamps an INTEGER and
#    not date text.
# ---------------------------------------------------------------------------


def test_dump_is_wellformed_on_both_sides(frozen_schema) -> None:
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
        frozen_schema: The parsed `mysql/ACASDB.sql`, read and never written.

    Raises:
        Skipped: The harness Compose stack is not usable.
        AssertionError: A dump is malformed, or its column list disagrees with the
            frozen schema.
    """
    conftest.requires_stack()

    run = conftest.run_scenario_parity(SCENARIO)

    for side, tree in (
        (conftest.SIDE_COBOL, run.paths.cobol_normalized),
        (conftest.SIDE_PYTHON, run.paths.python_normalized),
    ):
        for table in run.tables:
            path = tree / f"{table}.json"
            dump = conftest.read_dump(path)
            conftest.assert_dump_wellformed(
                dump, where=f"{side} {table} ({path})", schema=frozen_schema
            )


def test_glposting_rec_is_an_unchanged_witness(tmp_path) -> None:
    """`GLPOSTING-REC` must be untouched - by BOTH sides, and against the seed.

    THE MEASURED CENSUS BEHIND THIS TEST. gl072 issues exactly eight facade verbs -
    `GL-Batch-Open` [general/gl072.cbl:L276], `GL-Nominal-Open`
    [general/gl072.cbl:L277], `GL-Batch-Rewrite` [general/gl072.cbl:L377],
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

    Args:
        tmp_path: A private root for the seed capture, kept away from the parity
            run's own output so neither can overwrite the other.

    Raises:
        Skipped: The harness Compose stack is not usable.
        HarnessFaultError: A capture stage failed, so there is no evidence.
        AssertionError: The posting table was written by one of the two cycles.
    """
    conftest.requires_stack()

    witness = "GLPOSTING-REC"
    assert witness in conftest.scenario_affected_tables(SCENARIO)

    # THE SEED CAPTURE, taken first and through the protocol's own stages. The
    # `cobol` label here names the seeded state, not the oracle's output.
    conftest.seed(SCENARIO).raise_for_status()
    conftest.dump(SCENARIO, conftest.SIDE_COBOL, out_dir=tmp_path).raise_for_status()
    conftest.normalize(
        SCENARIO, conftest.SIDE_COBOL, out_dir=tmp_path
    ).raise_for_status()
    seeded = conftest.scenario_paths(SCENARIO, out_root=tmp_path).cobol_normalized

    # `run_scenario_parity` re-seeds at stage 1 from the same scenario fixture, so
    # the capture above and the two runs below all start from the same state.
    run = conftest.run_scenario_parity(SCENARIO)

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
        (conftest.SIDE_COBOL, run.paths.cobol_normalized),
        (conftest.SIDE_PYTHON, run.paths.python_normalized),
    ):
        against_seed = conftest.diff_trees_directly(seeded, produced, (witness,))
        assert against_seed.is_empty, (
            f"the {label} run changed {witness}, which no in-scope program of the "
            f"gl_post_cycle route writes. In this comparison the report's `cobol` "
            f"column is THE SEEDED STATE and its `python` column is the state after "
            f"the {label} run.\n{run.describe()}"
        )


def test_batch_is_stamped_cleared_and_posted(frozen_schema) -> None:
    """The two columns `end-batch` stamps must AGREE BETWEEN THE TWO SIDES.

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
        frozen_schema: The parsed `mysql/ACASDB.sql`, used only to confirm the two
            columns exist and to locate them by name rather than by position.

    Raises:
        Skipped: The harness Compose stack is not usable.
        AssertionError: The two sides disagree about either stamped column.
    """
    conftest.requires_stack()

    table = "GLBATCH-REC"
    stamped = ("CLEARED-STATUS", "POSTED")
    for column in stamped:
        assert column in frozen_schema[table], (
            f"{table}.{column} is not declared by mysql/ACASDB.sql; the frozen "
            f"schema and this assertion have drifted apart."
        )

    run = conftest.run_scenario_parity(SCENARIO)

    def stamps(tree) -> dict[object, tuple[object, ...]]:
        """Read the two stamped columns of every row, keyed by primary-key VALUE.

        Args:
            tree: A normalised tree.

        Returns:
            `{primary-key value: (CLEARED-STATUS, POSTED)}`. Keyed by VALUE and never
            by position, exactly as the differ aligns rows.
        """
        dump = conftest.read_dump(tree / f"{table}.json")
        conftest.assert_dump_wellformed(dump, where=str(tree), schema=frozen_schema)
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
