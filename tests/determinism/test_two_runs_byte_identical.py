"""TWO PYTHON RUNS OF ONE SCENARIO, UNDER ONE PINNED CLOCK, MUST BE BYTE-IDENTICAL.

THE PROOF OBLIGATION. Agent Action Plan section 0.8.5, acceptance criterion 4,
verbatim:

    "Determinism. Two runs of the same scenario under the same pinned clock produce
    byte-identical dumps, proven by
    `tests/determinism/test_two_runs_byte_identical.py`."

Agent Action Plan section 0.7.2 R-6 names this file, by path, as the proof
obligation for the controlled clock. It is the whole content of
`tests/determinism/`.

WHY IT IS A PREREQUISITE AND NOT A NICETY. Every other verification in this
migration compares one Python run against one compiled-COBOL run and demands an
EMPTY DIFF. If two *Python* runs of the same scenario could differ from each other,
an empty diff against the oracle would prove nothing whatever - a passing scenario
might simply have been lucky. This file closes that hole, and nothing else does.

A NON-EMPTY DIFF HERE MEANS SOMETHING CATEGORICALLY DIFFERENT FROM A NON-EMPTY DIFF
IN `tests/scenarios/`. There, it means the Python cycle diverges from the COBOL.
HERE IT MEANS THE PYTHON CYCLE IS NOT DETERMINISTIC - a far more serious defect,
because it invalidates every scenario result in the tree. The failure messages below
say so in those words, and they also re-label the report's fixed `cobol`/`python`
columns as run A and run B, because the compiled oracle is never executed here.

-------------------------------------------------------------------------------
THE TWO OBSERVABLES, AND WHY EXACTLY TWO SUFFICE
-------------------------------------------------------------------------------

The controlled clock pins two things and no more.

OBSERVABLE 1 - THE TEXT DATE. `to-day pic x(10)` in DD/MM/CCYY form, set at
[copybooks/Proc-ACAS-Mapser-RDB.cob:L77] - `move u-date to to-day.` A linkage
parameter, never a column.

OBSERVABLE 2 - THE BINARY RUN DATE. Declared verbatim at
[copybooks/wssystem.cob:L67]:

        05  Run-Date        binary-long. *> 9(8) comp.

set at [copybooks/Proc-ACAS-Mapser-RDB.cob:L80] - `move u-bin to run-date.` It is a
REAL `SYSTEM-REC` column (`RUN-DAT int(8) unsigned`) and is therefore VISIBLE IN A
TABLE DUMP, which is exactly why pinning it is load-bearing rather than cosmetic.

Pinned project-wide: text "21/09/2025", binary `Run-Date` 155127. The epoch is
1600-12-31, which the maintainer flags at [common/maps04.cbl:L39-L41] as making the
module "NOT usable within IRS as is"; `date(1600, 12, 31).toordinal()` is 584388, so
day 1 is 1601-01-01 and `run_date = toordinal() - 584388`. Verified:
`date(2025, 9, 21).toordinal()` is 739515 and 739515 - 584388 = 155127.

The one clock read `acas_posting/clock.py` reproduces, verbatim from the source
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]:

     72|      move     function current-date to wse-date-block.
     73|      move     "00/00/0000" to u-date.
     74|      move     wse-year  to u-year.
     75|      move     wse-month to u-month.
     76|      move     wse-days  to u-days.
     77|      move     u-date    to to-day.          <- OBSERVABLE 1
     78|      move     zero      to u-bin.           <- the anomaly-16 pre-zero
     79|      call     "maps04" using maps03-ws.
     80|      move     u-bin  to run-date.           <- OBSERVABLE 2

THE TWO ARE MUTUALLY CONSISTENT BY CONSTRUCTION. In normal menu operation the binary
run date is authoritative and the text is DERIVED from it -
[general/general.cbl:L465-L467]: `move run-date to u-bin.` / `call "maps04" using
maps03-ws.` / `move u-date to to-day.` So pinning `run_date = 155127` fully
determines `to_day`, and `test_clock_has_no_real_time_fallback` asserts both
directions.

WHY TWO SUFFICE. Agent Action Plan section 0.1.1: every one of the twelve in-scope
posting programs contains ZERO clock reads - the date arrives purely through linkage.
Agent Action Plan section 0.6.6 completes the argument, verbatim: "there is no hidden
time source, no random seed, and no ordering nondeterminism from a secondary index."

THE CORRECTED CLOCK-READ CENSUS, recorded so that a future grepper is not misled.
The Agent Action Plan speaks of "the single read in the whole call chain", and the
folder brief corrects that to "13 reads across 6 files". The MEASURED census over
this checkout is FOURTEEN sites across those same six files - the brief's own
enumeration in fact lists fourteen, so only its total was wrong:

    common/ACAS.cbl                       L353, L470, L478
    general/general.cbl                   L371, L551, L559
    sales/sales.cbl                       L323, L520, L528
    purchase/purchase.cbl                 L318, L514, L522
    irs/irs.cbl                           L480
    copybooks/Proc-ACAS-Mapser-RDB.cob    L72

By construct: six `move function current-date`, four `accept ... from date`, four
`accept ... from time`. EVERY ONE is in a menu shell or in the shared date-service
copybook, and a grep for `function current-date` over all twelve in-scope programs -
gl051, gl070, gl071, gl072, gl080, sl055, sl060, sl100, pl055, pl060, pl100,
irs030 - returns ZERO for each. So the Plan's phrasing is imprecise while its
conclusion is exactly right, and the two-observable design is sound.

THE CLOCK IS NOT OVER-ENGINEERED, AND NOTHING HERE OVER-ENGINEERS IT EITHER. Agent
Action Plan section 0.1.1 is explicit, so `acas_posting/clock.py` has no `Clock`
protocol or ABC, no production-versus-test pair, no monkeypatch hook, no global
mutable "current clock" singleton, no timezone model, and NO DEFAULT THAT RESOLVES TO
"NOW" - "not even a convenience one, not even guarded by a flag". This file builds
none of those and monkeypatches no time source. Instead it ASSERTS the absence, in
`test_clock_has_no_real_time_fallback`: if any code path could silently fall back to
the real system time, every other assertion in this file would be meaningless.

THE IRS ASYMMETRY, HONOURED RATHER THAN SMOOTHED. [irs/irs030.cbl:L552-L554],
verbatim:

    552|  procedure division using IRS-System-Params
    553|                           WS-System-Record
    554|                           File-Defs.

Neither `to-day` nor the calling-data block - the third of the three linkage shapes.
Yet the IRS route still needs a run date, because parameter 2 is the ordinary ACAS
system record carrying `Run-Date binary-long` [copybooks/wssystem.cob:L67]. "No run
date" never meant "no clock", and `clean_batch_irs` pins the same clock as
`clean_batch_gl` for exactly that reason.

-------------------------------------------------------------------------------
THE PROTOCOL THIS FILE RUNS - PYTHON ONLY
-------------------------------------------------------------------------------

    [run A]  seed  -> run_python -> dump(python) -> normalize -> RELOCATE to runA
    [run B]  reset -> run_python -> dump(python) -> normalize -> RELOCATE to runB
             diff(runA, runB)  =>  MUST BE EMPTY
             + a literal byte-for-byte comparison of the two trees

THE COMPILED COBOL ORACLE IS NOT INVOLVED AT ALL (R-1): no `run_cobol` stage, no
`--side cobol` dump, no `cobc`, no `cobcrun`, no FFI, and no `import harness` in any
form - the harness modules arrive only through `tests/conftest.py`'s explicit-path
loaders, exposed here as the `harness` fixture. Agent Action Plan section 0.7.2
licenses precisely this: "The compiled oracle exists only under `harness/` and is
consumed only by `tests/scenarios/*` and `tests/determinism/*` as an out-of-process
comparison."

RUN B BEGINS FROM A RESET AND RE-SEEDED DATABASE, NEVER A DIRTY ONE. `harness/
reset_db.sh` re-applies `mysql/ACASDB.sql` VERBATIM - the frozen file already carries
all 33 `DROP TABLE IF EXISTS`, so re-applying it IS the drop-and-recreate and no DDL
of this file's own is ever emitted (R-3) - asserts the post-apply state, and then
re-seeds by delegating to `harness/seed.sh`. Without the reset the test would prove
only that a second run over an already-posted state is idempotent, which is a
different and far weaker claim.

WHY THE STAGES ARE COMPOSED HERE RATHER THAN DELEGATED WHOLESALE. `tests/conftest.py`
also publishes `run_determinism_pair`, which composes the same stages with two
distinct output roots. This file composes the INDIVIDUAL stages instead, which is
what Agent Action Plan section 0.4.3 exposed them for, because one guard layer needs
a point of interposition BETWEEN the two runs: `run_python` takes no output-root
argument, so both runs write their seed fingerprint to the single path
`$ACAS_OUT/run-logs/<scenario>/python.seed-fingerprint` and run B overwrites run A's.
Layer 4 below therefore snapshots each fingerprint as its run finishes. No stage is
reimplemented - every one is called through the `protocol` fixture.

MANDATORY RELOCATION, AND THE HIGHEST-PROBABILITY DEFECT IN THIS FILE. The canonical
layout is `$ACAS_OUT/<scenario>/python.normalized/<TABLE>.json`, and BOTH runs use
the side label `python`, so run B overwrites run A in place. A test that skipped the
relocation would diff a tree against itself and pass vacuously forever. Each run's
normalised tree is therefore copied with `shutil.copytree` into
`tmp_path/run{A,B}.normalized` before the next stage can touch it, and the two
relocated paths are asserted to differ and to lie outside `$ACAS_OUT/<scenario>/`.
The suffix is not decorative: `harness/diff_states.py` refuses a tree whose name does
not end `.normalized` or `.norm` unless `allow_raw` is set, and `allow_raw` is a
debugging escape that produces no evidence. Independently,
`harness/diff_states.py` raises `SameTreeError` when both sides resolve to one
directory, calling it "a FALSE PASS" - a second line of defence this file does not
rely on but does not defeat either.

NOTHING IS WRITTEN OUTSIDE `tmp_path` AND `$ACAS_OUT`. `$ACAS_REPO` is mounted
read-only (`../:/repo:ro`), and Agent Action Plan section 0.8.1 makes any diff
touching the frozen trees a defect "regardless of how harmless it appears" - which
includes a stray `__pycache__`.

-------------------------------------------------------------------------------
THE THREE-WAY EXIT CONTRACT - `2` IS NEVER COLLAPSED INTO `0`
-------------------------------------------------------------------------------

`harness/diff_states.py` has exactly three statuses:

    0   the trees are identical, and stdout is EMPTY - zero bytes    -> PASS
    1   a real difference                                           -> FAILURE
    2   THE COMPARISON COULD NOT BE PERFORMED                        -> ERROR

Exit 1 is the strongest possible signal here, because both sides are the SAME
implementation. Exit 2 covers a missing tree, a missing table file, invalid JSON, a
missing or mis-ordered key, `row_count != len(rows)`, a ragged row, a duplicate
primary key, a `float` value (R-2) or a null value; it is NEVER a pass, because an
empty diff is the pass condition only when a comparison actually happened.

HOW `2` BECOMES A GENUINE pytest ERROR. In pytest an exception raised in a TEST BODY
is reported FAILED whatever its type; only an exception raised in a FIXTURE is
reported ERROR. So every preparation stage lives in the `determinism_pair` fixture -
the skip guard, seed, run, dump, normalize, the relocation, the fingerprint
snapshots, the well-formedness reads and all four guard layers - and ONLY the two
comparisons live in the test body. A harness fault is therefore an ERROR and a real
two-run difference is a FAILURE, and the two can never be confused. Nothing here
writes `except Exception: pass`, appends `|| true`, or treats a non-zero-but-not-1
status as success.

-------------------------------------------------------------------------------
BYTE-IDENTICAL MEANS BYTE-IDENTICAL, SO BOTH COMPARISONS ARE MADE
-------------------------------------------------------------------------------

`harness/dump_tables.py` and `harness/normalize.py` both serialise with
`json.dump(obj, fp, indent=2, ensure_ascii=True, sort_keys=False,
separators=(",", ": "))`, `newline="\\n"`, `encoding="utf-8"`, exactly one trailing
newline, written to a temporary file in the same directory and moved with
`os.replace`. The dump object carries exactly FIVE keys in fixed insertion order -
`table`, `primary_key`, `columns`, `row_count`, `rows` - and NO OTHERS: no timestamp,
no server version, no connection info, no scenario name, no side. THAT ABSENCE IS
WHAT MAKES A BYTE COMPARISON MEANINGFUL AT ALL; a single timestamp key would make
this file vacuous, which is why the key list AND its order are asserted explicitly
rather than assumed.

    1. STRUCTURAL - `diff_trees(runA, runB, affected)` -> `TreeDiff.is_empty`. This
       LOCALISES a difference to a table, a primary key and a column.
    2. LITERAL BYTES - every file in both trees compared with `filecmp.cmp(...,
       shallow=False)` and reported by `sha256`. This catches a serialisation-level
       difference the structural diff would normalise away: key order, indentation,
       the trailing newline, `ensure_ascii` drift, decimal rendering.

The comparison is EXACT. No tolerance, no epsilon, no `math.isclose`, no
`pytest.approx`, and no `float` anywhere (R-2): DECIMAL values arrive as canonical
JSON strings at the declared scale and integers as JSON integers. Rows align by
primary-key VALUE and never by position.

-------------------------------------------------------------------------------
THE VACUITY ARGUMENT, AND THE FOUR-LAYER GUARD
-------------------------------------------------------------------------------

TWO EMPTY DUMPS ARE ALSO BYTE-IDENTICAL, so a bare `is_empty` assertion has two
independent ways to pass while proving nothing. Both are closed.

CHANNEL 1 - THE STACK SILENTLY NEVER WROTE TO MySQL.
[copybooks/wssystem.cob:L111-L114], verbatim:

    111|          05  RDBMS-Flat-Statuses.
    112|              07  File-System-Used  pic 9.
    113|                  88  FS-Cobol-Files-Used    value zero.
    114|                  88  FS-MySql-Used          value 1.

Every handler gates its RDBMS path on `not FS-Cobol-Files-Used`. Confirmed
independently in two of them - [common/acas007.cbl:L316-L320] and
[common/acas008.cbl:L313-L319], where even the IRS `Open-Output`-to-`Delete-All`
conversion is gated the same way. With `File-System-Used = 0` the handlers fall
through to the COBOL indexed-file path and never touch MySQL, both dumps come back
empty, the comparison exits 0, and the run is a SILENT FALSE PASS. Every scenario
YAML pins `system.file_system_used: 1` precisely to prevent this.

CHANNEL 2 - ANOMALY 16 MASKS A REJECTED DATE AS `Run-Date = 0`.
`common/maps04.cbl` has two reject paths - the six-part test at L140-L145 reaching
`L146 go to Main-Exit.` and the calendar-validity test at L153 reaching
`L154 go to Main-Exit.` - and BOTH reach `Main-Exit` without touching `A-Bin`, while
the remark block at [common/maps04.cbl:L163] claims "Date errors returned as A-Bin
equal zero". The contract holds only because the caller pre-zeroes at
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. So a rejected date yields `Run-Date = 0`
WITHOUT RAISING - and a run under `Run-Date = 0` is still perfectly deterministic,
and still wrong. `is_empty` alone would not notice.

    LAYER 1 - STRUCTURAL PRESENCE. Both trees carry a complete manifest whose
    recorded digests match the files on disk and whose scenario identities agree
    (`verify_trees`); every affected table has a dump in BOTH trees; each dump passes
    the full well-formedness assertion (`load_dump`); the two trees hold the same set
    of filenames; and each dump's key list is exactly the five keys IN ORDER.

    LAYER 2 - CONTENT NON-VACUITY. The sum of `row_count` over run A's affected
    tables is greater than zero, with a message naming
    `system.file_system_used: 1` as the likeliest cause and citing
    [copybooks/wssystem.cob:L111-L114], [common/acas007.cbl:L316-L320] and
    [common/acas008.cbl:L313-L319].

    LAYER 3 - THE PINNED-CLOCK WITNESS, GENERAL LEDGER ONLY. At least one
    `GLBATCH-REC` row holds `POSTED == 155127`. Provenance, verbatim from
    [general/gl072.cbl:L372-L377]:

        372|  end-batch.
        375|      move     1  to  cleared-status.
        376|      move     run-date  to  posted.
        377|      perform  GL-Batch-Rewrite.

    and `mysql/ACASDB.sql` declares `POSTED` `int(8) unsigned NOT NULL` - an INTEGER
    column, which `harness/normalize.py`'s date-text job never touches, so 155127
    appears in the dump verbatim as a JSON integer. THIS ONE ASSERTION CLOSES BOTH
    VACUITY CHANNELS AT ONCE: it cannot hold if the run never wrote to MySQL, and it
    cannot hold if the clock degraded to 0.

    LAYER 4 - SEED-FINGERPRINT IDENTITY. `harness/run_python_scenario.sh` writes
    `$ACAS_OUT/run-logs/<scenario>/python.seed-fingerprint` before each run, as one
    `<TABLE> <count>` line per affected table in the scenario's declared order,
    integers only. Both snapshots must exist and be identical, which proves the seed
    landed identically before either run INDEPENDENTLY OF THE DUMPS - and catches a
    seeding difference that would otherwise masquerade as a determinism failure.

A GUARD FAILURE AT ANY LAYER IS A HARNESS FAULT, raised from the fixture, reported as
a pytest ERROR, and worded so it is unmistakable from a determinism FAILURE.

`SYSTEM-REC` is deliberately NOT used as a witness: it appears in no scenario's
`affected_tables`, because a census across all twelve in-scope programs found zero
`System-*` facade verbs. And no witness is invented for the IRS route -
`GLBATCH-REC` is not among `clean_batch_irs`'s affected tables and the IRS witness
column is oracle-arbitrated, a matter for `docs/migration/ambiguity-resolutions.md`.
Layer 3 is therefore expressed as a declarative mapping with only the verified
General Ledger entry populated, and every other scenario runs layers 1, 2 and 4.

-------------------------------------------------------------------------------
THE ONE REAL NONDETERMINISM RISK
-------------------------------------------------------------------------------

`gl072` locates the nominal-ledger account with a SEQUENTIAL read, so correctness
depends on upstream sort order. Verbatim:

    405|      move     post-ledger  to  WS-Ledger-Key.     <- INERT for a READ NEXT
    407|      if       read-ledger not = "R"
    408|               perform  GL-Nominal-Read-Next.

Perturbing the sort therefore causes SILENT MISPOSTING - no error, no diagnostic,
wrong balances. Ties are genuinely reachable: `gl070`'s three-leg double-entry
explosion [general/gl070.cbl:L495-L533] emits two legs sharing an identical
`(sort-batch, sort-ac, sort-pc, sort-post)` key whenever the VAT account equals the
credit account with matching profit centres, and `gl071`'s SORT carries NO
`WITH DUPLICATES IN ORDER` - verbatim at [general/gl071.cbl:L172-L178]:

    172|      sort     sort-trans
    173|               on ascending key sort-batch
    174|                                sort-ac
    175|                                sort-pc
    176|                                sort-post
    177|               using  pre-trans
    178|               giving post-trans.

So GnuCOBOL's tie order is an unmeasured ambiguity, and `clean_batch_gl`'s seed
CREATES such a tie on purpose. THE CORRECT FRAMING, and the reason this file exists:
ties are reachable and the COBOL sort's tie order is unspecified, BUT the accumulation
is commutative - `gl072`'s only per-posting state mutation is
[general/gl072.cbl:L331] `add post-amount to ledger-balance.` - and `gl072` issues
ZERO `GL-Posting-*` verbs, its `WS-Posting-Record` being a one-byte dummy in the
unused facade-stub block at [general/gl072.cbl:L135-L155], so `GLPOSTING-REC` is read
by `gl070` and never written and stands in the dump as an unchanged witness.
The dump is therefore INVARIANT under the tie, and a determinism test that seeds a tie
PROVES that invariance rather than assuming it. It does not detect a primary-key
flip, and no such claim is made: the tie cannot move `POST-RRN` or any other key.

FOUR AGENT-ACTION-PLAN LOCATOR DISCREPANCIES, recorded rather than quietly corrected
(R-5). Each was re-read in this checkout:

    1. The sequential nominal read. The Plan cites [general/gl072.cbl:L410-L412]. The
       verified locators are L405, L407 and L408; L410-L411 is a `tot-dr`/`tot-cr`
       RESET, not the read, and L405's key move is INERT for a `READ NEXT`.
    2. The `gl071` SORT. Some planning documents say L171-L177, which is off by one:
       L171 is a bare `*>` comment. The measured span is L172-L178. Note also that
       the key order `(batch, ac, pc, post)` is NOT the record's declaration order,
       which is `batch, post, code, date, ac, pc, amount, legend` at
       [general/gl071.cbl:L136-L144].
    3. The unused facade-stub block. The Plan cites L134-L153; the measured block runs
       from L135 (`01  Dummies-4-Unused-ACAS-FH-Calls.`) to L155
       (`03  WS-OTM5-Record         pic x.`), with `WS-Posting-Record` at L140.
    4. The clock-read census, corrected to fourteen sites above.

-------------------------------------------------------------------------------
GOVERNING RULES
-------------------------------------------------------------------------------

THERE IS NO USER RULES DOCUMENT. `review_rules` returns exactly "No user rules
provided.", and that one line is the complete document - so no rules file is to be
looked for, nothing is invented to fill the gap, and enterprise-standard best
practice applies wherever the Plan is silent. The binding rules are the six embedded
in Agent Action Plan section 0.7.2:

    R-1  No COBOL at runtime. Only the Python cycle is driven, out of process,
         through `harness/run_python_scenario.sh`. No `cobc`, no `cobcrun`, no
         `ctypes`, no `cffi`, no `run_cobol`, no `--side cobol`, never `import
         harness`, and never an `acas_posting.dal` internal.
    R-2  Zero binary floating point. No `float`, no float literal, no
         `pytest.approx`, no `math.isclose`, no tolerance, no `pandas`, no `numpy`.
         The ambient `decimal.getcontext()` is MUTATED only inside a
         `decimal.localcontext()` block, and is read outside one in exactly one
         place: to prove that the block restored it.
    R-3  No new validations, fields or schema changes, and no concurrency. No DDL,
         no `DROP DATABASE`, no `pytest-xdist` and no `-n`, no
         `PYTHONWARNINGS=error`, and `common/masterLD.sh` is never invoked - its own
         header says "THIS SCRIPT HAS NOT YET BEEN TESTED"
         [common/masterLD.sh:L4-L5] and it is not valid shell. Autocommit is OFF
         during seeding, per [common/glbatchLD.cbl:L9-L13]. Nothing is validated
         beyond the well-formedness reads and the four guard layers.
    R-4  Legacy anomalies reproduced, never fixed - AND INVERTED HERE. A difference
         between two Python runs is NOT a legacy anomaly; it is a NEW defect in the
         Python implementation. So no sorting, coalescing, key-normalisation,
         ignore-list or tolerance is ever added to make the two runs agree: that
         would conceal a new defect, which is the clearest possible inversion of the
         rule. The in-scope table inventory is read from
         `harness/dump_tables.py`'s `IN_SCOPE` and never restated.
    R-5  Full traceability. Every assertion cites the Plan section and the COBOL
         locators it rests on, and the four locator discrepancies above are flagged
         rather than silently corrected. `pytest-cov` is evidence, never a gate, and
         no `--cov-fail-under` is added.
    R-6  Compiled behavior is the tie-breaker, and THIS FILE IS THE NAMED PROOF
         OBLIGATION. Exactly two pinned observables; no clock abstraction, ABC,
         monkeypatch hook or singleton; and no default resolving to "now".
         `docs/migration/ambiguity-resolutions.md` and
         `docs/migration/scenario-diff-evidence.md` are referenced in prose only -
         neither exists yet and neither is this file's to create.

Agent Action Plan section 0.8.1 freezes the COBOL, the bridges, the copybooks and
`mysql/ACASDB.sql`: they are READ here - one harness script is read as text - and
never written. Agent Action Plan section 0.8.4 puts performance work out of scope by
construction, so there is no timing assertion, no `perf_counter`, and no duration
budget anywhere below.
"""

from __future__ import annotations

import dataclasses
import decimal
import filecmp
import hashlib
import inspect
import re
import shutil
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

import pytest

from acas_posting import clock as acas_clock
from acas_posting.cobol import arithmetic

# The tier label. REGISTERED ALREADY, in `pyproject.toml`'s `[tool.pytest.ini_options]
# markers` under `--strict-markers`, where its description records that it requires the
# Compose stack. Nothing here re-registers it, and this file adds no `pytest.ini` and no
# `markers =` of its own. Selectable as `pytest -m determinism` and
# `pytest -m "scenario or determinism"`.
pytestmark = pytest.mark.determinism


# ---------------------------------------------------------------------------
#  THE PINNED CLOCK, AND THE SCENARIO SET
# ---------------------------------------------------------------------------

# THE PROJECT-WIDE PINNED RUN DATE, restated here as the two literals the folder
# specification names so that `test_clock_has_no_real_time_fallback` can assert them
# without importing `tests/conftest.py` - the house convention across
# `tests/arithmetic/` is that conftest is reached through FIXTURES and never imported.
# These are not a second authority that could drift unnoticed: every stack-backed test
# below cross-checks them against the scenario's own declared `run_date_text` and
# `run_date_binary`, so a divergence between this file, `tests/conftest.py` and the
# scenario YAML fails loudly at the fixture (R-4).
PINNED_TO_DAY: Final[str] = "21/09/2025"
PINNED_RUN_DATE: Final[int] = 155127

# The scenario's own keys for the pinned pair. `harness/run_cobol_scenario.sh` reads
# this file's YAML with a reader that accepts TOP-LEVEL keys only, which is why the
# scenarios publish flat mirrors of their `clock:` block; those flat keys are the ones
# read here.
SCENARIO_KEY_RUN_DATE_TEXT: Final[str] = "run_date_text"
SCENARIO_KEY_RUN_DATE_BINARY: Final[str] = "run_date_binary"

# THE TWO SCENARIOS, AND NO MORE. Agent Action Plan section 0.8.5 mandates eight
# scenarios for `tests/scenarios/`; determinism needs only the two that carry
# independent evidence, and a third would multiply stack time for no additional proof.
#
#   `clean_batch_gl` IS MANDATORY, for three reasons. Its seed deliberately contains
#   the four-key sort tie described in the module docstring - the single most valuable
#   determinism input there is. It is the ONLY route with a verified pinned-clock
#   witness, [general/gl072.cbl:L376] stamping `GLBATCH-REC.POSTED`. And it runs one
#   operation with an empty answer map, so nothing about any command-line option
#   spelling has to be known to drive it.
#
#   `clean_batch_irs` EARNS ITS PLACE BY TURNING THE RESET INTO A TEST-ENFORCED
#   REQUIREMENT. Its run EMPTIES `PSIRSPOST-REC`: [irs/irs030.cbl:L1720-L1724]
#   performs `acas008-Open-Output`, which [common/acas008.cbl:L313-L319] converts into
#   a `Delete-All` when `not FS-Cobol-Files-Used`. So run B would post nothing at all
#   unless the database is reset AND re-seeded first, and the row-count guard would
#   catch it. That is exactly why the reset is not a stylistic instruction here. It
#   also exercises the third linkage shape [irs/irs030.cbl:L552-L554] while still
#   needing the same pinned run date, the asymmetry the module docstring records.
DETERMINISM_SCENARIOS: Final[tuple[str, ...]] = ("clean_batch_gl", "clean_batch_irs")

# Where a scenario definition lives, relative to the repository root the `repo_root`
# fixture resolves. Needed only by the stack-free ordering assertion, which reads a
# definition directly rather than through the `protocol` fixture - `protocol` applies
# the stack skip guard, and that assertion must run on a bare host.
SCENARIO_DIR_NAME: Final[str] = "harness/scenarios"
SCENARIO_SUFFIX: Final[str] = ".yaml"

# THE TWO RUN LABELS. They are `runA`/`runB` and not `cobol`/`python`, because the
# oracle is not executed here; the `.normalized` suffix is REQUIRED, since
# `harness/diff_states.py` refuses a tree whose name does not end `.normalized` or
# `.norm` unless `allow_raw` is set - and `allow_raw` is a debugging escape whose
# verdict is not evidence.
RUN_LABELS: Final[tuple[str, str]] = ("runA", "runB")
NORMALIZED_SUFFIX: Final[str] = ".normalized"

# The side both runs capture under. ONE value, deliberately: the side is recorded in
# the PATH and never inside a dump, which is why the relocation below is mandatory.
SIDE_PYTHON: Final[str] = "python"

# The pre-run seed fingerprint `harness/run_python_scenario.sh` writes at its stage
# 6a, under `run-logs/` and therefore OUTSIDE any compared tree. Row counts only, all
# integers (R-2). It is compared BYTE-FOR-BYTE and never parsed: interpreting it here
# would be the added validation R-3 forbids, and byte identity is the whole claim.
SEED_FINGERPRINT_NAME: Final[str] = "python.seed-fingerprint"

# LAYER 3 - THE PINNED-CLOCK WITNESS, AS DECLARATIVE DATA, with only the verified
# General Ledger entry populated.
#
# `(table, column, expected)`. The General Ledger entry is provenanced verbatim at
# [general/gl072.cbl:L372-L377] - `move run-date to posted.` at L376 followed by
# `perform GL-Batch-Rewrite.` - and `mysql/ACASDB.sql` declares `POSTED` as
# `int(8) unsigned NOT NULL`, an INTEGER column that `harness/normalize.py`'s
# date-text canonicalisation never touches, so the pinned 155127 appears in the dump
# verbatim as a JSON integer.
#
# NO WITNESS IS INVENTED FOR THE IRS ROUTE, and the omission is deliberate rather
# than an oversight. `GLBATCH-REC` is not among `clean_batch_irs`'s affected tables,
# and which IRS column would carry the run date is an oracle-arbitrated question -
# a matter for `docs/migration/ambiguity-resolutions.md` (R-6), which does not exist
# yet and is not this file's to write. `SYSTEM-REC` is not available either: it
# appears in NO scenario's `affected_tables`, because a census across all twelve
# in-scope programs found zero `System-*` facade verbs, so `RUN-DAT` cannot be
# reached. A scenario absent from this mapping therefore runs layers 1, 2 and 4 only,
# and says so in its own diagnostics rather than silently skipping a check.
CLOCK_WITNESS: Final[Mapping[str, tuple[str, str, int]]] = {
    "clean_batch_gl": ("GLBATCH-REC", "POSTED", PINNED_RUN_DATE),
}

# THE DETERMINISM AND FREEZE BELT `harness/run_python_scenario.sh` SETS. Asserted
# here, never duplicated: this file sets none of them and modifies no script.
#
# The patterns tolerate the shell's optional quoting because the script really does
# quote some values and not others - `export PYTHONHASHSEED=0` is bare while
# `export LC_ALL='C.UTF-8'` is single-quoted - so a naive substring test would report
# a false absence for four of the seven.
#
# The last two of the first six are a FROZEN-ARTIFACT guarantee rather than a
# convenience: without `PYTHONDONTWRITEBYTECODE=1`, and without moving the working
# directory out of the read-only checkout, a stray `__pycache__` appears in
# `git status`, which Agent Action Plan section 0.8.1 makes a defect "regardless of
# how harmless it appears".
#
# `PYTHONSAFEPATH=1` is a seventh setting beyond the six the folder specification
# names, measured in the script and asserted because it is squarely on topic: it keeps
# the current directory off the front of the import path, so the run cannot silently
# import a same-named package from wherever it happened to be launched. A run that
# imported a different `acas_posting` would be deterministic and wrong.
DETERMINISM_BELT: Final[Mapping[str, str]] = {
    "PYTHONPATH=$ACAS_REPO": (
        r"^\s*export\s+PYTHONPATH=(['\"]?)\$\{?ACAS_REPO\}?\1\s*$"
    ),
    "PYTHONDONTWRITEBYTECODE=1": (
        r"^\s*export\s+PYTHONDONTWRITEBYTECODE=(['\"]?)1\1\s*$"
    ),
    "PYTHONHASHSEED=0": r"^\s*export\s+PYTHONHASHSEED=(['\"]?)0\1\s*$",
    "LC_ALL=C.UTF-8": r"^\s*export\s+LC_ALL=(['\"]?)C\.UTF-8\1\s*$",
    "LANG=C.UTF-8": r"^\s*export\s+LANG=(['\"]?)C\.UTF-8\1\s*$",
    "TZ=UTC": r"^\s*export\s+TZ=(['\"]?)UTC\1\s*$",
    "PYTHONSAFEPATH=1": r"^\s*export\s+PYTHONSAFEPATH=(['\"]?)1\1\s*$",
}

# The one setting that must be ABSENT. Promoting warnings to errors would be a new
# validation, which R-3 forbids; the script says so in its own comment and this
# asserts the comment is true of the code.
FORBIDDEN_BELT_SETTING: Final[str] = "PYTHONWARNINGS"

# The runner's own name, resolved under the `harness` directory the `repo_root`
# fixture reaches. READ AS TEXT, READ-ONLY.
RUN_PYTHON_SCRIPT_NAME: Final[str] = "run_python_scenario.sh"

# Every token whose presence in `acas_posting/clock.py` would mean some path could
# resolve to "now", to a random value or to the ambient environment. Matched
# case-sensitively against the module's own source, which is why `to_day` and
# `TO_DAY_SEED` cannot collide with `date.today`.
FORBIDDEN_CLOCK_TOKENS: Final[tuple[str, ...]] = (
    "datetime.now",
    ".utcnow",
    "date.today",
    "time.time",
    "time.localtime",
    "random",
    "uuid",
    "os.environ",
    "getenv",
    "socket.gethostname",
    "os.getpid",
)

# The two date texts `common/maps04.cbl` REJECTS, and the value a rejection leaves
# behind. "31/02/2025" passes the six-part test at [common/maps04.cbl:L140-L146] and
# fails the calendar check at [common/maps04.cbl:L153]; "rubbish" fails the six-part
# test outright. Both reach `Main-Exit` without touching the output field
# [common/maps04.cbl:L146, L154], and the documented zero contract
# [common/maps04.cbl:L163] holds only because the caller pre-zeroes at
# [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. THAT IS ANOMALY 16, REPRODUCED AND NOT
# FIXED (R-4): a rejected date is specified behaviour, so neither case may raise.
REJECTED_DATE_TEXTS: Final[tuple[str, ...]] = ("31/02/2025", "rubbish")
REJECTED_DATE_RUN_DATE: Final[int] = 0



# ---------------------------------------------------------------------------
#  THE RUN PAIR, AS ONE IMMUTABLE PIECE OF EVIDENCE
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class RelocatedRun:
    """One completed Python run, snapshotted where nothing can overwrite it.

    Frozen because a run's evidence that could be edited after the fact is not
    evidence.

    Attributes:
        label: `runA` or `runB`.
        tree: The relocated normalised tree, under the test's own `tmp_path`. Its name
            ends `.normalized`, which is what `harness/diff_states.py` accepts as
            proof that the representation artefacts have been canonicalised away.
        fingerprint: The snapshotted `python.seed-fingerprint`, taken before the
            NEXT run could overwrite the single path the runner writes it to.
        run_status: The run stage's exit status, VERBATIM. Never normalised: only
            three in-scope programs set a term code at all, so a non-zero status is a
            BEHAVIOURAL result whose database effect must still be captured.
        row_counts: Each affected table's `row_count`, in the scenario's declared
            order.
    """

    label: str
    tree: Path
    fingerprint: Path
    run_status: int
    row_counts: tuple[tuple[str, int], ...]

    @property
    def total_rows(self) -> int:
        """Every row across every affected table - the layer 2 quantity."""
        return sum(count for _table, count in self.row_counts)


@dataclasses.dataclass(frozen=True)
class DeterminismEvidence:
    """Two runs of one scenario, their comparison, and the guards that passed.

    Everything in here was produced inside the fixture, so any fault building it is a
    pytest ERROR. The test body only asks questions of it.

    Attributes:
        scenario: The scenario both runs used.
        tables: The affected-table list both runs were bounded by, in the scenario's
            declared order.
        pin: The pinned pair both runs received through linkage - the same object, so
            there is no question of the two having been pinned differently.
        first: Run A.
        second: Run B.
        tree: The `TreeDiff` between the two relocated trees. `is_empty` is THE PASS
            CONDITION.
        render: `harness/diff_states.py`'s own deterministic report for that
            `TreeDiff` - the EMPTY STRING when the two agree.
        filenames: The filename set both trees hold, already asserted equal.
    """

    scenario: str
    tables: tuple[str, ...]
    pin: acas_clock.PinnedRunDate
    first: RelocatedRun
    second: RelocatedRun
    tree: Any
    render: str
    filenames: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        """True when the two runs produced identical state."""
        return bool(self.tree.is_empty)


# ---------------------------------------------------------------------------
#  PRIVATE HELPERS. Small, local, and in THIS file - the tier holds exactly one
#  file, so a helper module is not an option (and would not be wanted).
# ---------------------------------------------------------------------------


def _relocate(source: Path, destination: Path) -> Path:
    """Copy a normalised tree somewhere the next run cannot overwrite it.

    THE SINGLE MOST IMPORTANT MECHANICAL STEP IN THIS FILE. Both runs capture under
    the side label `python`, so both write
    `$ACAS_OUT/<scenario>/python.normalized/` - run B overwrites run A in place. A
    test that skipped this would diff a tree against itself and pass vacuously
    forever.

    `shutil.copytree` is used rather than a move: leaving the original in place keeps
    the canonical evidence layout intact for an operator inspecting `$ACAS_OUT`, and
    a copy cannot be disturbed by the next stage.

    Args:
        source: The normalised tree the `normalize` stage just published.
        destination: Where to snapshot it. Its name must end `.normalized`.

    Returns:
        `destination`.

    Raises:
        AssertionError: The source is not a directory, or the destination name does
            not carry the suffix `harness/diff_states.py` requires. Raised from the
            fixture, so it is a pytest ERROR - a harness fault, not a determinism
            failure.
    """
    assert source.is_dir(), (
        f"HARNESS FAULT, not a determinism failure: the normalised tree {source} "
        f"is absent, so there is nothing to snapshot. The `normalize` stage reported "
        f"success, so its output should be here; a comparison whose inputs do not "
        f"exist cannot be performed, and 'could not compare' is never a pass (R-6)."
    )
    assert destination.name.endswith(NORMALIZED_SUFFIX), (
        f"HARNESS FAULT: the snapshot destination {destination.name!r} does not end "
        f"{NORMALIZED_SUFFIX!r}. harness/diff_states.py refuses a tree that is not "
        f"marked normalised unless `allow_raw` is set, and allow_raw is a debugging "
        f"escape whose verdict is not evidence - a raw dump still carries the "
        f"representation artefacts the normaliser exists to remove."
    )
    shutil.copytree(source, destination)
    return destination


def _snapshot_fingerprint(source: Path, destination: Path) -> Path:
    """Snapshot one run's pre-run seed fingerprint, before the next run replaces it.

    `harness/run_python_scenario.sh` writes it to
    `$ACAS_OUT/run-logs/<scenario>/python.seed-fingerprint` at its stage 6a, and
    `run_python` takes no output-root argument, so BOTH runs write that one path. This
    is the interposition point layer 4 needs, and the reason this file composes the
    individual stages rather than delegating the whole pair to one helper.

    Args:
        source: The runner's fingerprint path.
        destination: Where to keep it, beside the run's relocated tree.

    Returns:
        `destination`.

    Raises:
        AssertionError: The runner wrote no fingerprint. A harness fault: without it
            the two starting states are unverified, and a seeding difference would
            masquerade as a determinism failure.
    """
    assert source.is_file(), (
        f"HARNESS FAULT, not a determinism failure: harness/run_python_scenario.sh "
        f"wrote no seed fingerprint at {source}. Its stage 6a records the row count "
        f"of every affected table before the run, and without it the two runs' "
        f"starting states cannot be shown to have been identical - so a seeding "
        f"difference would be reported as nondeterminism, which is a false failure "
        f"that costs a day to find."
    )
    shutil.copyfile(source, destination)
    return destination


def _tree_filenames(tree: Path) -> tuple[str, ...]:
    """Every regular file in a tree, by name, ascending.

    Args:
        tree: The relocated normalised tree.

    Returns:
        The names, sorted so the comparison against the other tree is itself
        deterministic. Sorted rather than set-compared so a message can print them in
        a stable order.
    """
    return tuple(sorted(entry.name for entry in tree.iterdir() if entry.is_file()))


def _digest(path: Path) -> str:
    """The SHA-256 of one file's bytes, for a reportable identity.

    Reads bytes and never text, so no decoding step can normalise a difference away.

    Args:
        path: The file.

    Returns:
        The hex digest.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_five_keys_in_order(
    dump: Mapping[str, Any], expected: Sequence[str], *, where: str
) -> None:
    """Assert one dump carries exactly the five keys, IN ORDER, and no others.

    THE VACUITY ARGUMENT, DEFENDED EXPLICITLY. A byte comparison of two dumps is
    meaningful only because a dump has no timestamp, no server version, no connection
    info, no scenario name and no side - a single such key would make this whole file
    pass trivially on every run. `harness/diff_states.py` makes the same check inside
    `load_dump`; it is repeated here under its own name so a reviewer can see the
    argument being defended rather than having to trust that it is made somewhere.

    Args:
        dump: The parsed dump object.
        expected: `harness/dump_tables.py`'s `DUMP_KEYS`, read from the module rather
            than restated (R-4).
        where: The file the dump came from, for the message.

    Raises:
        AssertionError: The key list or its order is wrong.
    """
    keys = tuple(dump.keys())
    assert keys == tuple(expected), (
        f"HARNESS FAULT: {where} carries the keys {list(keys)}; a dump must carry "
        f"exactly {list(expected)} IN THAT ORDER and no others - no timestamp, no "
        f"server version, no connection info, no scenario name and no side (the side "
        f"is recorded in the PATH). THE ABSENCE OF ANY SUCH KEY IS WHAT MAKES THIS "
        f"FILE'S BYTE COMPARISON MEANINGFUL: one timestamp key and two runs would "
        f"differ for a reason that has nothing to do with the accounting, or - worse "
        f"- a byte comparison would be quietly asserting nothing at all."
    )


def _row_counts(
    tree: Path,
    tables: Sequence[str],
    *,
    load_dump: Callable[[Path], Mapping[str, Any]],
    dump_keys: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    """Read every affected table's dump from one tree, asserting each is well formed.

    `load_dump` is `harness/diff_states.py`'s own reader-and-asserter, so the shape
    contract has exactly one implementation: five keys in order, an in-scope table,
    a single-column primary key present in `columns`, `row_count == len(rows)`, every
    row of the declared width, no duplicate primary key, NO NULL VALUE and NO `float`
    (R-2). Every one of those failures is the comparison's exit 2 - it is reported
    here as a pytest ERROR and never as a pass.

    Args:
        tree: The relocated normalised tree.
        tables: The affected tables, in the scenario's declared order.
        load_dump: `harness/diff_states.py`'s `load_dump`.
        dump_keys: `harness/dump_tables.py`'s `DUMP_KEYS`, read from the module and
            never restated here (R-4).

    Returns:
        `(table, row_count)` pairs in the scenario's order.

    Raises:
        AssertionError: A table's dump is absent from this tree, or its key list is
            not the five keys in order.
        Exception: `harness/diff_states.py`'s own errors, unchanged. They are not
            caught, wrapped or softened: a dump that cannot be trusted cannot produce
            a verdict.
    """
    counts: list[tuple[str, int]] = []
    for table in tables:
        path = tree / f"{table}.json"
        assert path.is_file(), (
            f"HARNESS FAULT, not a determinism failure: the scenario names "
            f"{table} among its affected tables but {path} is absent from the "
            f"{tree.name} tree. A table present in one tree and missing from the "
            f"other has no meaningful comparison, so this is exit 2 territory - the "
            f"comparison could not be performed - and is never treated as agreement."
        )
        dump = load_dump(path)
        _assert_five_keys_in_order(dump, dump_keys, where=str(path))
        counts.append((table, int(dump["row_count"])))
    return tuple(counts)



def _assert_clock_witness(
    scenario: str,
    tree: Path,
    *,
    load_dump: Callable[[Path], Mapping[str, Any]],
) -> None:
    """LAYER 3 - assert the pinned clock actually reached the database.

    THIS ONE ASSERTION CLOSES BOTH VACUITY CHANNELS AT ONCE. It cannot hold if the run
    never wrote to MySQL, because the witnessed row would not be there; and it cannot
    hold if the clock degraded to zero through anomaly 16, because the witnessed value
    would be 0 rather than the pinned day number. Two empty dumps are byte-identical
    and two zero-dated dumps are byte-identical, so without this the file could pass
    green while proving nothing.

    GENERAL LEDGER ONLY, BY DESIGN. `CLOCK_WITNESS` holds only the verified entry, so
    a scenario absent from it - `clean_batch_irs` - relies on layers 1, 2 and 4. The
    reason is recorded at `CLOCK_WITNESS` and is not an oversight: no non-GL witness
    column has been arbitrated against the compiled oracle, and inventing one would
    settle by assumption a question R-6 reserves for
    `docs/migration/ambiguity-resolutions.md`.

    Args:
        scenario: The scenario just run.
        tree: Its relocated normalised tree.
        load_dump: `harness/diff_states.py`'s `load_dump`.

    Raises:
        AssertionError: The witness table has no row carrying the pinned run date, or
            the witness column is not in the dump's column list. A HARNESS FAULT
            raised from the fixture, so a pytest ERROR - it is emphatically not a
            two-run difference.
    """
    witness = CLOCK_WITNESS.get(scenario)
    if witness is None:
        # Nothing to assert, and nothing silently skipped either: layers 1, 2 and 4
        # still ran, and the reason this route has no witness is documented in full at
        # `CLOCK_WITNESS`.
        return

    table, column, expected = witness
    dump = load_dump(tree / f"{table}.json")
    columns = list(dump["columns"])

    assert column in columns, (
        f"HARNESS FAULT: `{table}` has no `{column}` column in the {tree.name} "
        f"dump; its columns are {columns}. mysql/ACASDB.sql declares "
        f"`{column}` on `{table}`, and the column list is read in schema ordinal "
        f"order, so its absence means the frozen schema has been altered - which "
        f"Agent Action Plan section 0.8.1 makes a defect in the migration."
    )
    position = columns.index(column)
    observed = [row[position] for row in dump["rows"]]

    assert expected in observed, (
        f"THE PINNED CLOCK DID NOT REACH THE DATABASE - a HARNESS FAULT, not a "
        f"determinism failure. No `{table}` row in the {tree.name} tree carries "
        f"`{column}` == {expected}; the {len(observed)} value(s) present are "
        f"{observed}.\n"
        f"  Provenance: [general/gl072.cbl:L372-L377] - `end-batch.` at L372, "
        f"`move 1 to cleared-status.` at L375, `move run-date to posted.` at L376 "
        f"and `perform GL-Batch-Rewrite.` at L377 - so a posted batch MUST carry "
        f"the run date it was posted under. mysql/ACASDB.sql declares `{column}` as "
        f"`int(8) unsigned NOT NULL`, an integer column harness/normalize.py's "
        f"date-text canonicalisation never touches, so the pinned value appears "
        f"verbatim as a JSON integer.\n"
        f"  THIS GUARD EXISTS BECAUSE WITHOUT IT THIS FILE COULD PASS VACUOUSLY. "
        f"Two likely causes, both of which produce a perfectly deterministic and "
        f"perfectly worthless run:\n"
        f"    1. The scenario's `system.file_system_used` is not 1, so every handler "
        f"took the COBOL indexed-file path and NEVER TOUCHED MySQL - "
        f"[copybooks/wssystem.cob:L111-L114] declares "
        f"`88 FS-Cobol-Files-Used value zero`, and the gate is visible at "
        f"[common/acas007.cbl:L316-L320] and [common/acas008.cbl:L313-L319].\n"
        f"    2. The pinned date was REJECTED by maps04 and degraded to 0 without "
        f"raising - anomaly 16, [common/maps04.cbl:L146] and "
        f"[common/maps04.cbl:L154] falling through without touching the output "
        f"field, masked by the caller's pre-zero at "
        f"[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. A `{column}` of 0 here is that "
        f"defect, reproduced faithfully and detected deliberately."
    )


def _execute_run(
    label: str,
    scenario: str,
    tables: Sequence[str],
    *,
    protocol: Any,
    workspace: Path,
    load_dump: Callable[[Path], Mapping[str, Any]],
    dump_keys: Sequence[str],
    first: bool,
) -> RelocatedRun:
    """Seed (or reset), run the Python cycle, capture, normalise, and snapshot.

    THE STAGES ARE CALLED, NEVER REIMPLEMENTED. Each one comes from the `protocol`
    fixture, which is what Agent Action Plan section 0.4.3 built it for: "the seed,
    dump, normalize and diff helpers gathered in one place so that no test
    reimplements the comparison protocol".

    THE ORACLE IS NOT INVOLVED (R-1). There is no `run_cobol` call, no `--side cobol`
    dump, and nothing in this function reaches a COBOL program: the migrated cycle is
    driven out of process through `harness/run_python_scenario.sh` and that is all.

    Args:
        label: `runA` or `runB`, used for the snapshot directory name.
        scenario: The scenario to run.
        tables: Its affected tables, in declared order.
        protocol: The `protocol` fixture's stage bundle.
        workspace: The test's `tmp_path`, the only place outside `$ACAS_OUT` written.
        load_dump: `harness/diff_states.py`'s `load_dump`.
        dump_keys: `harness/dump_tables.py`'s `DUMP_KEYS`.
        first: True for run A, which SEEDS; False for run B, which RESETS.

    Returns:
        The relocated run.

    Raises:
        Exception: Any stage fault, unchanged - `HarnessFaultError` from
            `raise_for_status`, or the harness modules' own errors. Raised from the
            fixture that calls this, so every one is a pytest ERROR.
    """
    if first:
        # STAGE 1. The scenario is BINDING: harness/seed.sh stages this scenario's
        # declared `seed_files` into a fresh scenario-owned fixture, writes an
        # identity marker naming the files and their digests, and seeds from exactly
        # those. It invokes the maintainer's own *LD.cbl loaders and NEVER
        # common/masterLD.sh, whose header says "THIS SCRIPT HAS NOT YET BEEN TESTED"
        # [common/masterLD.sh:L4-L5] and which is not valid shell (R-3).
        protocol.seed(scenario).raise_for_status()
    else:
        # STAGE 5, AND IT IS WHAT MAKES THIS TEST MEAN WHAT IT CLAIMS. reset re-applies
        # mysql/ACASDB.sql VERBATIM - the frozen file already carries all 33
        # `DROP TABLE IF EXISTS`, so re-applying it IS the drop-and-recreate and no
        # DDL of this file's own is emitted (R-3) - asserts the post-apply state, and
        # then RE-SEEDS by delegating to harness/seed.sh with the same scenario
        # fixture. Run B therefore starts from byte-for-byte the state run A did.
        #
        # `clean_batch_irs` turns this from a stylistic instruction into a
        # test-enforced one: its own run EMPTIES `PSIRSPOST-REC` via
        # [irs/irs030.cbl:L1720-L1724] performing `acas008-Open-Output`, which
        # [common/acas008.cbl:L313-L319] converts into a `Delete-All`. Without the
        # re-seed run B would post nothing at all and layer 2's row-count guard would
        # fire.
        protocol.reset(scenario).raise_for_status()

    # STAGE 6. The status is captured VERBATIM and deliberately not raised on: only
    # three in-scope programs set `WS-Term-Code` at all, so a non-zero status is a
    # BEHAVIOURAL result whose database effect must still be captured. Absence is
    # evidence, and a helper that short-circuited the dump would destroy it.
    run = protocol.run_python(scenario)

    # STAGE 7 and its normalisation. Both bounded by the scenario's own definition, so
    # the table list comes from the scenario and never from a local restatement (R-4).
    protocol.dump(scenario, SIDE_PYTHON).raise_for_status()
    protocol.normalize(scenario, SIDE_PYTHON).raise_for_status()

    paths = protocol.paths(scenario)
    tree = _relocate(
        paths.normalized_dir(SIDE_PYTHON),
        workspace / f"{label}{NORMALIZED_SUFFIX}",
    )
    fingerprint = _snapshot_fingerprint(
        paths.run_logs / SEED_FINGERPRINT_NAME,
        workspace / f"{label}.{SEED_FINGERPRINT_NAME}",
    )

    return RelocatedRun(
        label=label,
        tree=tree,
        fingerprint=fingerprint,
        run_status=run.returncode,
        row_counts=_row_counts(
            tree, tables, load_dump=load_dump, dump_keys=dump_keys
        ),
    )



# ---------------------------------------------------------------------------
#  THE FIXTURE. EVERY PREPARATION STAGE LIVES HERE, AND NOTHING ELSE DOES.
#
#  In pytest an exception raised in a TEST BODY is reported FAILED whatever its type;
#  only an exception raised in a FIXTURE is reported ERROR. That distinction is the
#  entire mechanism by which the comparison's exit 2 - "the comparison could not be
#  performed" - stays separable from its exit 1 - "the two runs differ". So the skip
#  guard, both runs, both captures, both normalisations, the relocations, the
#  fingerprint snapshots, the well-formedness reads, all four guard layers AND the
#  structural comparison itself are performed below, while the test body asks only
#  whether the answer was empty.
#
#  Function-scoped, because each parametrised scenario needs its own two runs; and the
#  two runs are strictly sequential, which is not an implementation detail but the
#  property under test - running them concurrently against one shared MariaDB would
#  destroy it (R-3).
# ---------------------------------------------------------------------------


@pytest.fixture
def determinism_pair(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    protocol: Any,
    harness: Any,
    scenario_loader: Callable[[str], Mapping[str, Any]],
    pinned_clock: acas_clock.PinnedRunDate,
) -> DeterminismEvidence:
    """Run one scenario TWICE under the same pinned clock, guard it, and compare.

    Args:
        request: Supplies the scenario name through indirect parametrisation.
        tmp_path: The only location outside `$ACAS_OUT` written to. `$ACAS_REPO` is
            mounted read-only and Agent Action Plan section 0.8.1 makes any diff
            inside it a defect, so both relocated trees and both fingerprint
            snapshots live here.
        protocol: Every stage, from `tests/conftest.py`. It applies the stack skip
            guard itself, so a bare host SKIPS with a precise reason and never errors.
        harness: The three harness modules, loaded by explicit file path. NEVER
            `import harness` - there is no `harness/__init__.py` and `pyproject.toml`
            excludes `harness*` from packaging, which is the structural enforcement of
            R-1.
        scenario_loader: The scenario definition, parsed with `yaml.safe_load`.
        pinned_clock: The project-wide pinned pair, already asserted by
            `tests/conftest.py` to be the text `21/09/2025` and the binary 155127.

    Returns:
        The evidence, with the verdict already computed.

    Raises:
        Skipped: The Compose stack is unusable - a SKIP and never an error.
        AssertionError: A guard layer failed. A HARNESS FAULT.
        Exception: A stage fault or a malformed dump - the comparison's exit 2. Also a
            harness fault, and never a pass.
    """
    scenario: str = request.param
    diff_states = harness.diff_states
    dump_tables = harness.dump_tables

    # The affected-table list comes from the SCENARIO, in its own declared order, and
    # is validated against the in-scope inventory by harness/dump_tables.py. It is
    # never restated locally: a second copy of the table list would drift (R-4).
    tables = tuple(protocol.affected_tables(scenario))
    assert tables, (
        f"HARNESS FAULT: {scenario} declares no affected tables, so there is nothing "
        f"to compare. The affected-table list is how a comparison is BOUNDED, and an "
        f"unbounded or empty comparison is not a comparison."
    )

    # THE PIN IS ASSERTED, NOT ASSUMED, and it is asserted against the scenario's own
    # declaration as well as against the project default. Both runs receive this same
    # date through linkage - the twelve in-scope programs contain no clock read at all
    # - so if the scenario declared a different date from the one this file believes
    # is pinned, every downstream assertion here would be about the wrong run date.
    definition = scenario_loader(scenario)
    declared_text = definition.get(SCENARIO_KEY_RUN_DATE_TEXT)
    declared_binary = definition.get(SCENARIO_KEY_RUN_DATE_BINARY)
    pinned_pair = (pinned_clock.to_day, pinned_clock.run_date)
    assert (declared_text, declared_binary) == pinned_pair, (
        f"HARNESS FAULT: {scenario} declares the run date as "
        f"{declared_text!r}/{declared_binary!r} while the pinned clock carries "
        f"{pinned_clock.to_day!r}/{pinned_clock.run_date}. The two runs would still "
        f"be identical to each other, so this file would still pass - and it would be "
        f"measuring the wrong date. `to-day pic x(10)` "
        f"[copybooks/Proc-ACAS-Mapser-RDB.cob:L77] and `Run-Date binary-long` "
        f"[copybooks/wssystem.cob:L67] are the only two observables the cycle can "
        f"see, so they must agree everywhere or the pin means nothing."
    )

    # ------------------------------------------------------------------
    #  THE TWO RUNS. Sequential, and run A is snapshotted out of the way BEFORE run B
    #  is allowed to start - see `_relocate` for why that ordering is load-bearing.
    # ------------------------------------------------------------------
    first = _execute_run(
        RUN_LABELS[0],
        scenario,
        tables,
        protocol=protocol,
        workspace=tmp_path,
        load_dump=diff_states.load_dump,
        dump_keys=dump_tables.DUMP_KEYS,
        first=True,
    )
    second = _execute_run(
        RUN_LABELS[1],
        scenario,
        tables,
        protocol=protocol,
        workspace=tmp_path,
        load_dump=diff_states.load_dump,
        dump_keys=dump_tables.DUMP_KEYS,
        first=False,
    )

    # THE RELOCATION, PROVEN RATHER THAN TRUSTED. Both runs capture under the side
    # label `python` and therefore under one path, so a test that compared the
    # canonical trees would compare run B with itself and pass forever. These two
    # assertions are the proof that did not happen.
    canonical = protocol.paths(scenario).normalized_dir(SIDE_PYTHON)
    # The whole per-scenario capture area, not merely the normalised tree: a snapshot
    # anywhere beneath `$ACAS_OUT/<scenario>/` is exposed to the next run's stages.
    capture_area = canonical.parent
    assert first.tree != second.tree, (
        f"HARNESS FAULT: both runs were snapshotted to {first.tree}. Comparing a "
        f"tree with itself always reports an empty diff whatever the migration "
        f"produced - a FALSE PASS, and the single highest-probability defect this "
        f"file can carry."
    )
    for run in (first, second):
        assert run.tree != capture_area and capture_area not in run.tree.parents, (
            f"HARNESS FAULT: {run.label}'s snapshot {run.tree} still lies inside the "
            f"per-scenario capture area {capture_area}, which the NEXT run's dump and "
            f"normalise stages rewrite in place - both runs use the side label "
            f"{SIDE_PYTHON!r} and therefore the one path {canonical}. The snapshot "
            f"must live outside it, under the test's own tmp_path, or the comparison "
            f"is between one tree and itself and passes vacuously forever."
        )

    # ------------------------------------------------------------------
    #  LAYER 1 - STRUCTURAL PRESENCE.
    # ------------------------------------------------------------------
    # Both trees complete, every recorded digest matching the file on disk, and the two
    # manifests naming the SAME scenario. `verify_trees` is harness/diff_states.py's
    # own check and is the strongest single structural assertion available: a tree that
    # over-declares, under-declares or whose bytes have moved since publication is
    # refused here rather than diffed.
    diff_states.verify_trees(first.tree, second.tree)

    # The same set of filenames on both sides. A table file present in one tree and
    # absent from the other is a harness fault - the comparison cannot be performed -
    # and is emphatically not a value difference. `_manifest.json` is included: it
    # carries each table's row count and sha256, so its presence on both sides is part
    # of the completeness claim.
    filenames = _tree_filenames(first.tree)
    other_filenames = _tree_filenames(second.tree)
    assert filenames == other_filenames, (
        f"HARNESS FAULT, not a determinism failure: the two trees hold different "
        f"files. {RUN_LABELS[0]} holds {list(filenames)} and {RUN_LABELS[1]} holds "
        f"{list(other_filenames)}; only in {RUN_LABELS[0]}: "
        f"{sorted(set(filenames) - set(other_filenames))}; only in "
        f"{RUN_LABELS[1]}: {sorted(set(other_filenames) - set(filenames))}. A file "
        f"on one side and not the other leaves nothing to compare for that table."
    )

    # Both runs' per-table well-formedness and five-key order were already asserted
    # inside `_execute_run`; what remains is that the two agree on WHICH tables they
    # measured, in the scenario's order.
    assert tuple(t for t, _ in first.row_counts) == tuple(
        t for t, _ in second.row_counts
    ), (
        f"HARNESS FAULT: the two runs measured different table lists - "
        f"{[t for t, _ in first.row_counts]} versus "
        f"{[t for t, _ in second.row_counts]}. Both are bounded by the same "
        f"scenario definition, so a disagreement means the bound moved between runs."
    )

    # ------------------------------------------------------------------
    #  LAYER 2 - CONTENT NON-VACUITY. Two EMPTY dumps are also byte-identical.
    # ------------------------------------------------------------------
    assert first.total_rows > 0, (
        f"THE RUN WROTE NOTHING - a HARNESS FAULT, not a determinism failure. Every "
        f"affected table of {scenario} came back empty in {RUN_LABELS[0]}: "
        f"{list(first.row_counts)}.\n"
        f"  TWO EMPTY DUMPS ARE BYTE-IDENTICAL, so without this guard the comparison "
        f"would exit 0 and this file would report a SILENT FALSE PASS.\n"
        f"  THE LIKELIEST CAUSE IS `system.file_system_used` not being 1 in the "
        f"seeded system record. [copybooks/wssystem.cob:L111-L114] declares "
        f"`07 File-System-Used pic 9` with `88 FS-Cobol-Files-Used value zero` and "
        f"`88 FS-MySql-Used value 1`, and every handler gates its RDBMS path on "
        f"`not FS-Cobol-Files-Used` - see [common/acas007.cbl:L316-L320] and, for "
        f"the IRS transfer file, [common/acas008.cbl:L313-L319]. With the flag at "
        f"zero the handlers fall through to the COBOL indexed-file path and NEVER "
        f"TOUCH MySQL at all. Every scenario YAML pins `system.file_system_used: 1` "
        f"precisely to prevent this, and the seeded flat file must carry it too.\n"
        f"  A seeding failure or an aborted run would produce the same emptiness; the "
        f"run stage exited {first.run_status} and the seed fingerprint is at "
        f"{first.fingerprint}."
    )
    assert second.total_rows > 0, (
        f"RUN B WROTE NOTHING while run A wrote {first.total_rows} row(s) - a "
        f"HARNESS FAULT. Run B's counts are {list(second.row_counts)}.\n"
        f"  THIS IS THE SIGNATURE OF A MISSING RE-SEED rather than of "
        f"nondeterminism. `clean_batch_irs` in particular EMPTIES its own transfer "
        f"table: [irs/irs030.cbl:L1720-L1724] performs `acas008-Open-Output`, which "
        f"[common/acas008.cbl:L313-L319] converts into a `Delete-All`, so a second "
        f"run over the first run's leftover state has nothing to post. harness/"
        f"reset_db.sh re-applies mysql/ACASDB.sql verbatim AND re-seeds through "
        f"harness/seed.sh for exactly this reason; if it did not, the comparison "
        f"would be measuring idempotence and not determinism. Run B exited "
        f"{second.run_status}."
    )

    # ------------------------------------------------------------------
    #  LAYER 3 - THE PINNED-CLOCK WITNESS. Asserted on BOTH runs: a clock that
    #  degraded on the second run only would otherwise show up as an ordinary
    #  difference, and the diagnosis would be needlessly hard.
    # ------------------------------------------------------------------
    for run in (first, second):
        _assert_clock_witness(scenario, run.tree, load_dump=diff_states.load_dump)

    # ------------------------------------------------------------------
    #  LAYER 4 - SEED-FINGERPRINT IDENTITY. Proves the seed landed identically before
    #  EITHER run, independently of the dumps - so a seeding difference is diagnosed as
    #  a seeding difference instead of masquerading as nondeterminism.
    #
    #  Compared as BYTES and never parsed: the file is row counts only, all integers,
    #  and interpreting it here would be the added validation R-3 forbids.
    # ------------------------------------------------------------------
    assert filecmp.cmp(first.fingerprint, second.fingerprint, shallow=False), (
        f"THE TWO RUNS DID NOT START FROM THE SAME SEEDED STATE - a HARNESS FAULT, "
        f"not a determinism failure, and the distinction matters because the two look "
        f"identical in a table diff.\n"
        f"  {RUN_LABELS[0]} {first.fingerprint.name} "
        f"(sha256 {_digest(first.fingerprint)}):\n"
        f"{first.fingerprint.read_text(encoding='utf-8')}"
        f"  {RUN_LABELS[1]} {second.fingerprint.name} "
        f"(sha256 {_digest(second.fingerprint)}):\n"
        f"{second.fingerprint.read_text(encoding='utf-8')}"
        f"  harness/run_python_scenario.sh records the row count of every affected "
        f"table, in the scenario's declared order, immediately before each run. A "
        f"difference means the re-seed loaded something other than the fixture the "
        f"first seed staged, so every downstream difference would be unattributable. "
        f"Autocommit must be OFF while seeding - [common/glbatchLD.cbl:L9-L13]: "
        f"\"you MUST ensure that autocommit is OFF in the rdb settings\" - and the "
        f"loaders signal failure through exit codes that must be tested rather than "
        f"assumed."
    )

    # ------------------------------------------------------------------
    #  THE STRUCTURAL COMPARISON. Performed HERE so that its exit-2 failures - a
    #  missing tree, a malformed dump, a duplicate primary key, a null, a float - are
    #  pytest ERRORs, while its verdict is left for the test body to assert so that a
    #  real difference is a pytest FAILURE.
    #
    #  `allow_raw` is not passed: both trees are genuinely normalised and a raw-tree
    #  verdict would not be evidence. harness/diff_states.py independently refuses two
    #  paths that resolve to one directory, calling it a false pass.
    # ------------------------------------------------------------------
    tree_diff = diff_states.diff_trees(first.tree, second.tree, tables)

    return DeterminismEvidence(
        scenario=scenario,
        tables=tables,
        pin=pinned_clock,
        first=first,
        second=second,
        tree=tree_diff,
        render=diff_states.render(tree_diff),
        filenames=filenames,
    )



# ---------------------------------------------------------------------------
#  THE PROOF OBLIGATION ITSELF
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "determinism_pair", DETERMINISM_SCENARIOS, indirect=True, ids=DETERMINISM_SCENARIOS
)
def test_two_python_runs_are_byte_identical(
    determinism_pair: DeterminismEvidence,
) -> None:
    """THE NAMED PROOF OBLIGATION of Agent Action Plan section 0.8.5, criterion 4.

    "Two runs of the same scenario under the same pinned clock produce byte-identical
    dumps, proven by `tests/determinism/test_two_runs_byte_identical.py`." R-6 names
    this file by path for exactly this assertion.

    THIS BODY CONTAINS ONLY THE TWO COMPARISONS, and that is deliberate. Every stage,
    every guard layer and the comparison's own construction happened in the fixture, so
    a harness fault is a pytest ERROR; what is left here is the verdict, so a genuine
    two-run difference is a pytest FAILURE. The two can never be confused, which is the
    whole point of the split.

    BOTH COMPARISONS ARE MADE, because the claim is BYTE-identical and the two catch
    different things:

      1. The STRUCTURAL diff LOCALISES a difference to a table, a primary key and a
         column, which is what makes a failure actionable.
      2. The LITERAL byte comparison catches a serialisation-level difference the
         structural diff would normalise away - key order, indentation, the trailing
         newline, `ensure_ascii` drift, decimal rendering.

    Neither uses a tolerance. There is no epsilon, no `math.isclose`, no
    `pytest.approx` and no `float` anywhere (R-2): DECIMAL values arrive as canonical
    JSON strings and integers as JSON integers, and rows align by primary-key value
    rather than by position.

    AND NEITHER IS ALLOWED TO BE MADE TO PASS. R-4 is inverted here: a difference
    between two Python runs is not a legacy anomaly to be reproduced, it is a NEW
    defect in the Python implementation. So no sorting, coalescing,
    key-normalisation, ignore-list or tolerance is added to make the two runs agree -
    that would conceal a new defect, which is the clearest possible inversion of the
    rule.

    Args:
        determinism_pair: Two completed runs, guarded and compared.
    """
    evidence = determinism_pair

    # ------------------------------------------------------------------
    #  COMPARISON 1 - STRUCTURAL. `TreeDiff.is_empty` is the pass condition.
    # ------------------------------------------------------------------
    assert evidence.is_empty, (
        f"THE PYTHON POSTING CYCLE IS NOT DETERMINISTIC: two runs of scenario "
        f"{evidence.scenario!r} under the identical pinned clock "
        f"(to-day={evidence.pin.to_day!r}, Run-Date={evidence.pin.run_date}) produced "
        f"different database state. THIS INVALIDATES EVERY SCENARIO RESULT IN "
        f"tests/scenarios/, because an empty diff against the compiled oracle proves "
        f"nothing if the Python side can differ from itself.\n"
        f"\n"
        f"  THIS IS **NOT** A PYTHON-VERSUS-COBOL DIVERGENCE. The COBOL oracle was "
        f"not executed: no run_cobol stage, no --side cobol dump, no cobc and no "
        f"cobcrun (R-1). Both sides of this comparison are the migrated Python cycle.\n"
        f"\n"
        f"  READ THE REPORT'S COLUMNS AS **run A** AND **run B**. "
        f"harness/diff_states.py has exactly two labels, `cobol` and `python`, and "
        f"they are not configurable: here `cobol` is the FIRST run "
        f"({evidence.first.tree}) and `python` is the SECOND "
        f"({evidence.second.tree}).\n"
        f"\n"
        f"  {evidence.tree.total_differences} finding(s) across "
        f"{len(evidence.tree.differing)} table(s) of "
        f"{list(evidence.tables)}:\n"
        f"{evidence.render}"
        f"\n"
        f"  WHAT TO SUSPECT, in order. Anything that varies between two runs of the "
        f"same code over the same data: an unordered iteration whose result reaches a "
        f"stored value; a sort that is not stable, which "
        f"acas_posting/cobol/sortverb.py guarantees and cannot be asked not to; a "
        f"clock, a random source or an environment read that has crept in below the "
        f"CLI boundary. All four guard layers passed, so the run did write to MySQL, "
        f"the pinned clock did reach the database and both runs started from the same "
        f"seeded state - so this is a real difference in the cycle itself.\n"
        f"\n"
        f"  DO NOT MAKE THIS PASS BY NORMALISING IT (R-4, inverted). A difference "
        f"between two Python runs is a NEW defect, not a legacy anomaly, and adding a "
        f"sort, an ignore-list or a tolerance here would conceal it. Fix the cycle."
    )

    # ------------------------------------------------------------------
    #  COMPARISON 2 - LITERAL BYTES.
    #
    #  Every file in both trees, not only the affected-table dumps: `_manifest.json`
    #  carries each table's row count and sha256, so comparing it is a compact
    #  cross-check on the whole capture, and it holds no timestamp and no absolute path
    #  that could make it differ for a benign reason.
    #
    #  This is where a serialisation-level difference is caught. The structural diff
    #  reads parsed JSON, so it would report two dumps with different key order,
    #  different indentation or a different trailing newline as IDENTICAL - and the
    #  claim being proven is byte-identity, not value-identity.
    # ------------------------------------------------------------------
    differing_bytes: list[str] = []
    for name in evidence.filenames:
        left = evidence.first.tree / name
        right = evidence.second.tree / name
        if not filecmp.cmp(left, right, shallow=False):
            differing_bytes.append(
                f"    {name}\n"
                f"      {RUN_LABELS[0]} sha256 {_digest(left)}  "
                f"{left.stat().st_size} byte(s)\n"
                f"      {RUN_LABELS[1]} sha256 {_digest(right)}  "
                f"{right.stat().st_size} byte(s)"
            )

    assert not differing_bytes, (
        f"THE PYTHON POSTING CYCLE IS NOT DETERMINISTIC AT THE BYTE LEVEL: two runs "
        f"of scenario {evidence.scenario!r} under the identical pinned clock "
        f"(to-day={evidence.pin.to_day!r}, Run-Date={evidence.pin.run_date}) produced "
        f"normalised files that differ byte-for-byte. THIS INVALIDATES EVERY SCENARIO "
        f"RESULT IN tests/scenarios/.\n"
        f"\n"
        f"  THIS IS **NOT** A PYTHON-VERSUS-COBOL DIVERGENCE - the COBOL oracle was "
        f"not executed (R-1). Left is **run A** ({evidence.first.tree}), right is "
        f"**run B** ({evidence.second.tree}).\n"
        f"\n"
        f"  {len(differing_bytes)} file(s) differ:\n"
        + "\n".join(differing_bytes)
        + f"\n"
        f"\n"
        f"  NOTE THAT THE STRUCTURAL DIFF PASSED, so the two runs agree on every "
        f"VALUE and disagree only on how those values were WRITTEN. Both producers "
        f"serialise with json.dump(indent=2, ensure_ascii=True, sort_keys=False, "
        f"separators=(\",\", \": \")), newline=\"\\n\", encoding=\"utf-8\" and exactly "
        f"one trailing newline, so suspect key insertion order, indentation, the "
        f"trailing newline, ensure_ascii drift or decimal rendering scale. Agent "
        f"Action Plan section 0.8.5 asks for byte-identical dumps, so a value-only "
        f"agreement does not discharge the obligation."
    )



# ---------------------------------------------------------------------------
#  THE COMPANION ASSERTIONS.
#
#  None of these needs the Compose stack, so none carries the skip guard and all four
#  run on a bare host. The module-level `determinism` marker still applies, and that is
#  correct: the marker is a SELECTION label, not an infrastructure declaration, so
#  `pytest -m determinism` on a host with no Docker still exercises everything that can
#  be proven without one.
#
#  Each earns its place by asserting a property WITHOUT WHICH THE MAIN TEST WOULD BE
#  MEANINGLESS rather than merely wrong.
# ---------------------------------------------------------------------------


def test_clock_has_no_real_time_fallback(
    pinned_clock: acas_clock.PinnedRunDate,
    pinned_clock_factory: Callable[[str], acas_clock.PinnedRunDate],
) -> None:
    """R-6: the clock is injected at one boundary and NOTHING resolves to "now".

    THE PROPERTY WITHOUT WHICH THIS WHOLE FILE IS MEANINGLESS. If any path in
    `acas_posting/clock.py` could silently fall back to the real system time, two runs
    a second apart could differ for a reason that has nothing to do with the
    accounting - and, far worse, two runs in the same second would still agree, so the
    main test would pass while the property it claims to prove was false.

    Agent Action Plan section 0.1.1 requires the controlled clock "must not be
    over-engineered", so there is no `Clock` protocol, no ABC, no
    production-versus-test pair, no monkeypatch hook, no global mutable singleton, no
    timezone model and no default resolving to "now" - "not even a convenience one,
    not even guarded by a flag". This test asserts that absence STRUCTURALLY, which is
    the cheap and honest way to discharge R-6: nothing here monkeypatches time or
    builds an abstraction of its own.

    THE TWO OBSERVABLES ARE ASSERTED IN BOTH DIRECTIONS. Forward, text to binary, is
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]; reverse, binary to text, is
    [general/general.cbl:L465-L467]. The reverse direction is the authoritative one in
    normal operation - `Run-Date` is a `SYSTEM-REC` column and arrives from the
    database - so pinning 155127 fully determines `to_day`, and the epoch that links
    them is 1600-12-31 [common/maps04.cbl:L39-L41].

    Args:
        pinned_clock: The project-wide pinned pair.
        pinned_clock_factory: `pinned_clock_from`, so a second clock can be built
            without duplicating any conversion logic.
    """
    # Both observables, at their pinned values.
    assert pinned_clock.to_day == PINNED_TO_DAY, (
        f"the pinned text date is {pinned_clock.to_day!r}, expected "
        f"{PINNED_TO_DAY!r}. `to-day pic x(10)` is DD/MM/CCYY and is set at "
        f"[copybooks/Proc-ACAS-Mapser-RDB.cob:L77]."
    )
    assert pinned_clock.run_date == PINNED_RUN_DATE, (
        f"the pinned binary Run-Date is {pinned_clock.run_date}, expected "
        f"{PINNED_RUN_DATE}. `Run-Date binary-long` [copybooks/wssystem.cob:L67] "
        f"counts days from the 1600-12-31 epoch [common/maps04.cbl:L39-L41], so a "
        f"mismatch is an epoch regression - and because Run-Date is a SYSTEM-REC "
        f"column it would surface as a table difference rather than as an error."
    )

    # FORWARD, text to binary: the same conversion the menu shell's date block performs
    # at [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], built through the factory so
    # that no arithmetic is duplicated here.
    forward = pinned_clock_factory(PINNED_TO_DAY)
    assert (forward.to_day, forward.run_date) == (PINNED_TO_DAY, PINNED_RUN_DATE), (
        f"pinning from the text {PINNED_TO_DAY!r} produced "
        f"{forward.to_day!r}/{forward.run_date} rather than "
        f"{PINNED_TO_DAY!r}/{PINNED_RUN_DATE}. That is the forward direction of "
        f"[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], and it must agree with the "
        f"reverse direction below or the two observables are not one date."
    )

    # REVERSE, binary to text: [general/general.cbl:L465-L467], verbatim - `move
    # run-date to u-bin.` / `call "maps04" using maps03-ws.` / `move u-date to
    # to-day.` This is the direction that makes the two observables MUTUALLY
    # CONSISTENT BY CONSTRUCTION, and therefore the reason pinning one pins both.
    reverse = acas_clock.pin_from_run_date(PINNED_RUN_DATE)
    assert (reverse.to_day, reverse.run_date) == (PINNED_TO_DAY, PINNED_RUN_DATE), (
        f"unpacking the binary Run-Date {PINNED_RUN_DATE} produced "
        f"{reverse.to_day!r}/{reverse.run_date} rather than "
        f"{PINNED_TO_DAY!r}/{PINNED_RUN_DATE}. [general/general.cbl:L465-L467] "
        f"derives the text FROM the binary, so pinning the day number must fully "
        f"determine the text; a disagreement means the two observables could drift "
        f"apart within one run."
    )

    # NO ZERO-ARGUMENT ENTRY POINT EXISTS, so no call could mean "now". Checked over
    # the module's own published surface rather than over a list restated here, so a
    # newly added public callable is covered automatically.
    for name in acas_clock.__all__:
        published = getattr(acas_clock, name)
        if not callable(published):
            # `TO_DAY_SEED` is the literal "00/00/0000" the date block seeds `u-date`
            # with at [copybooks/Proc-ACAS-Mapser-RDB.cob:L73]. A constant cannot
            # resolve to anything, let alone to "now".
            continue
        signature = inspect.signature(published)
        required = [
            parameter.name
            for parameter in signature.parameters.values()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ]
        assert required, (
            f"acas_posting.clock.{name}{signature} can be called with NO ARGUMENTS. "
            f"A zero-argument entry point on a clock module is exactly the "
            f"convenience default R-6 forbids - it could only mean \"now\", and it "
            f"would make tests/determinism/ meaningless while still passing. The date "
            f"must be INJECTED at every entry point."
        )

    # NO TIME, RANDOM OR ENVIRONMENT SOURCE IS REACHABLE. A source-text assertion is
    # crude but it is the honest one: it cannot be satisfied by a code path that is
    # merely hard to reach, and it fails the moment such an import is added.
    source = inspect.getsource(acas_clock)
    present = [token for token in FORBIDDEN_CLOCK_TOKENS if token in source]
    assert not present, (
        f"acas_posting/clock.py mentions {present}, so some path there can reach the "
        f"real system time, a random source, the process environment or the host "
        f"identity. R-6 permits exactly two observables, both INJECTED: the text "
        f"`to-day` [copybooks/Proc-ACAS-Mapser-RDB.cob:L77] and the binary `Run-Date` "
        f"[copybooks/wssystem.cob:L67]. Any other source would make two runs of one "
        f"scenario differ for a reason unrelated to the accounting, and would silently "
        f"invalidate every result in tests/scenarios/."
    )

    # THE TWO DOCUMENTED DEGRADATIONS DO NOT RAISE, because they are SPECIFIED
    # BEHAVIOUR and not errors. `common/maps04.cbl` rejects a date by falling through
    # to `Main-Exit` WITHOUT TOUCHING its output field - the six-part test at
    # [common/maps04.cbl:L140-L146] and the calendar check at
    # [common/maps04.cbl:L153-L154] - while its own remarks claim "Date errors
    # returned as A-Bin equal zero" [common/maps04.cbl:L163]. The contract holds only
    # because the caller pre-zeroes at [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. THAT
    # IS ANOMALY 16, AND IT IS REPRODUCED, NOT FIXED (R-4). No validation is added
    # here to reject these texts earlier or more loudly (R-3): the point is precisely
    # that a rejected date is silent, which is why layer 3's witness exists to catch
    # the resulting zero rather than trusting an exception that never comes.
    for text in REJECTED_DATE_TEXTS:
        degraded = pinned_clock_factory(text)
        assert degraded.run_date == REJECTED_DATE_RUN_DATE, (
            f"pinning from the rejected text {text!r} produced run_date "
            f"{degraded.run_date}, expected {REJECTED_DATE_RUN_DATE}. maps04 rejects "
            f"by falling through without touching its output field "
            f"[common/maps04.cbl:L146, L154], and the caller's pre-zero at "
            f"[copybooks/Proc-ACAS-Mapser-RDB.cob:L78] is what makes the documented "
            f"zero contract [common/maps04.cbl:L163] true. That masking mechanism is "
            f"anomaly 16 and must be reproduced exactly - a value other than zero "
            f"means acas_posting/clock.py has stopped reproducing it, and a raised "
            f"exception would mean a validation had been ADDED (R-3, R-4)."
        )


def test_arithmetic_is_insulated_from_ambient_decimal_context() -> None:
    """R-2: the arithmetic layer's result cannot be moved by the CALLER's context.

    DETERMINISM AGAINST CALLER STATE, complementing determinism against time. If
    `acas_posting/cobol/arithmetic.py` read the ambient `decimal` context instead of
    entering its own, then whether a posted figure came out right would depend on what
    some unrelated caller had last set `getcontext().prec` to - a nondeterminism with
    no clock in it at all, and one no table diff would ever explain.

    THE ASSERTION IS AN INVARIANCE, WHICH IS WHY IT NEEDS NO ORACLE VALUE. Agent
    Action Plan section 0.3.2 requires expected values to come from the compiled
    oracle and never from reading the COBOL, so the sabotaged result is compared
    against the SAME operation's default-context result rather than against a
    hand-derived figure. A control comparison against the bare expression proves the
    sabotage is real, so the invariance cannot be vacuously true.

    THE OUT-OF-PROCESS CAVEAT, RECORDED SO THIS IS NOT MISREAD AS STRONGER THAN IT IS.
    The scenario runs happen in a CHILD interpreter, through
    `harness/run_python_scenario.sh`, so mutating this process's `decimal` context
    cannot reach them - a sabotage applied before a run would be a no-op that looked
    meaningful. It is therefore applied IN PROCESS, directly against the arithmetic
    layer, which is where the property actually lives. No environment variable, flag
    or other injection mechanism is invented to carry it into the subprocess: that
    would be a new surface and a new validation (R-3).

    The sabotage is applied inside `decimal.localcontext()`, so the ambient context is
    always restored however this test exits - a test that leaked `prec = 4` into the
    session would corrupt every arithmetic test that ran after it.
    """
    # A plain division, whose exact quotient is non-terminating, so the number of
    # digits retained is decided entirely by the context in force.
    def one_third() -> Decimal:
        return Decimal("1") / Decimal("3")

    # The VAT-from-GROSS expression SHAPE - `post - (post / ((rate + 100) / 100))` -
    # which is the compound form the two ROUNDED sites [general/gl051.cbl:L796] and
    # [irs/irs030.cbl:L1562] evaluate. Used because a compound expression has
    # intermediate results, which is precisely where an ambient precision would bite.
    # NOTE that no expected value is asserted for it: only that it does not move.
    def vat_from_gross_shape() -> Decimal:
        post = Decimal("1234.56")
        rate = Decimal("17.5")
        return post - (post / ((rate + Decimal(100)) / Decimal(100)))

    for expression in (one_third, vat_from_gross_shape):
        default = arithmetic.intermediate(expression)

        with decimal.localcontext():
            # Sabotage the AMBIENT context - the only place this file touches it, and
            # only ever inside a localcontext block (R-2).
            decimal.getcontext().prec = 4
            sabotaged = arithmetic.intermediate(expression)
            # The control: the identical expression evaluated OUTSIDE the arithmetic
            # layer, under the sabotage. If this equalled `default` the sabotage would
            # be a no-op and the invariance below would prove nothing.
            unprotected = expression()

        assert unprotected != default, (
            f"the sabotage did not bite: {expression.__name__} evaluates to "
            f"{unprotected} under an ambient precision of 4 and to {default} under "
            f"the default context, and those are equal. This assertion exists so that "
            f"the invariance check below cannot pass vacuously - pick an expression "
            f"whose result the context actually governs."
        )
        assert sabotaged == default, (
            f"acas_posting/cobol/arithmetic.py IS NOT INSULATED FROM THE AMBIENT "
            f"decimal CONTEXT. {expression.__name__} returned {sabotaged} with the "
            f"caller's precision set to 4 and {default} with the default context, so "
            f"the module is reading `decimal.getcontext()` rather than entering its "
            f"own. Its INTERMEDIATE_CONTEXT declares "
            f"prec={arithmetic.INTERMEDIATE_PRECISION} and is applied through "
            f"decimal.localcontext(), precisely so that a stored figure cannot depend "
            f"on unrelated caller state (R-2). Until this holds, two runs of one "
            f"scenario could differ for a reason no table diff would explain."
        )

    assert decimal.getcontext().prec != 4, (
        "the sabotaged precision leaked out of its decimal.localcontext() block and "
        "is still in force. Every arithmetic test that runs after this one would be "
        "computing at 4 significant digits, so the leak would look like a widespread "
        "arithmetic failure somewhere else entirely."
    )


def test_harness_runner_pins_the_determinism_environment(repo_root: Path) -> None:
    """The runner's determinism-and-freeze belt is ASSERTED here, never duplicated.

    `harness/run_python_scenario.sh` sets the whole belt once, so every child process
    inherits it. This test reads the script AS TEXT, READ-ONLY, and checks that each
    setting is really there - it sets none of them itself and modifies no script.

    WHY EACH ONE MATTERS. `PYTHONHASHSEED=0` stops set and dictionary iteration order
    varying between runs; `LC_ALL`/`LANG` stop text handling varying by locale; `TZ`
    stops anything time-shaped varying by zone. `PYTHONDONTWRITEBYTECODE=1` and the
    move to a working directory outside the checkout are a FROZEN-ARTIFACT guarantee
    rather than a convenience: without them a stray `__pycache__` appears in
    `git status`, and Agent Action Plan section 0.8.1 makes any diff inside the frozen
    trees a defect "regardless of how harmless it appears". `PYTHONPATH` and
    `PYTHONSAFEPATH` together fix WHICH `acas_posting` is imported - a run that
    imported a same-named package from wherever it was launched would be perfectly
    deterministic and completely wrong.

    AND ONE SETTING MUST BE ABSENT. `PYTHONWARNINGS=error` would promote warnings to
    failures, which is a new validation R-3 forbids; the script says so in its own
    comment, and this asserts the comment is true of the code.

    The patterns tolerate the shell's optional quoting because the script genuinely
    mixes the two forms - `export PYTHONHASHSEED=0` bare against
    `export LC_ALL='C.UTF-8'` quoted - so a naive substring test would report a false
    absence for four of the seven settings.

    Args:
        repo_root: The repository root, from which the harness script is READ.
    """
    script = repo_root / "harness" / RUN_PYTHON_SCRIPT_NAME
    assert script.is_file(), (
        f"harness/{RUN_PYTHON_SCRIPT_NAME} is absent from {script}. It is the only "
        f"way this tier reaches the migrated cycle - out of process, which is how R-1 "
        f"wants it reached - so without it no determinism evidence can be produced at "
        f"all."
    )

    text = script.read_text(encoding="utf-8")

    for setting, pattern in DETERMINISM_BELT.items():
        assert re.search(pattern, text, re.MULTILINE), (
            f"harness/{RUN_PYTHON_SCRIPT_NAME} does not export {setting}. It is part "
            f"of the determinism and freeze belt the runner sets once so that every "
            f"child inherits it; without it two runs of one scenario could differ for "
            f"a reason that has nothing to do with the accounting, which is exactly "
            f"the failure tests/determinism/ exists to rule out. This test ASSERTS "
            f"the setting and must never set it instead - a belt applied by the test "
            f"would not be applied by an operator running the script directly."
        )

    assert FORBIDDEN_BELT_SETTING not in text, (
        f"harness/{RUN_PYTHON_SCRIPT_NAME} mentions {FORBIDDEN_BELT_SETTING}. "
        f"Promoting warnings to errors is an ADDED VALIDATION, which R-3 forbids: it "
        f"would make a run fail on a diagnostic the frozen system tolerates, turning "
        f"a faithful reproduction into a reported defect."
    )

    # The working directory moves OUT of the read-only checkout before anything runs.
    # Together with PYTHONDONTWRITEBYTECODE this is what keeps `git status` clean.
    workdir_change = re.search(
        r"^\s*if\s+!\s+cd\s+--\s+\"\$ACAS_PY_WORKDIR\"", text, re.MULTILINE
    )
    assert workdir_change, (
        f"harness/{RUN_PYTHON_SCRIPT_NAME} does not change into its own writable "
        f"working directory before running. $ACAS_REPO is mounted read-only "
        f"(`../:/repo:ro`) and Agent Action Plan section 0.8.1 makes any diff inside "
        f"the frozen trees a defect however harmless it looks, so the run must work "
        f"from somewhere outside the checkout."
    )


def test_the_dump_order_is_total_and_stable_by_construction(
    repo_root: Path,
    harness: Any,
    frozen_schema: Mapping[str, Mapping[str, Any]],
) -> None:
    """No tie-breaking is needed in the dump, and none is permitted.

    THE ORDERING GUARANTEE THE BYTE COMPARISON RESTS ON. A dump is
    `SELECT * FROM <table> ORDER BY <primary key>`, with no tie-break, no timestamp
    masking and no surrogate-key remapping. That is total and stable only because the
    frozen schema is exceptionally well behaved: every in-scope table has a
    SINGLE-COLUMN primary key and there is no secondary index on any of them, so the
    ordering column is unique and the row order is fully determined. Agent Action Plan
    section 0.6.6 draws the conclusion this file depends on - "a non-empty diff is
    always a real behavioral difference and never an artefact of the comparison".

    Were a primary key composite, or were rows ordered by a non-unique column, two
    runs could return the same rows in different orders and the byte comparison would
    fail for a reason that is not a defect. Asserting the property here means such a
    failure can be read as a genuine one.

    THE INVENTORY IS READ FROM `harness/dump_tables.py`'s `IN_SCOPE` AND NEVER
    RESTATED. A second copy of the 22 names, their primary keys or their column counts
    would drift the moment either changed (R-4), and the drift would be invisible.

    Needs no stack: a scenario definition and the frozen schema are both files on
    disk, and `harness/dump_tables.py` reads a scenario's table list with a plain YAML
    parse.

    Args:
        repo_root: The repository root, from which the two scenario definitions are
            READ.
        harness: The three harness modules.
        frozen_schema: `mysql/ACASDB.sql` parsed to `{table: {column: type}}`. READ,
            never written.
    """
    dump_tables = harness.dump_tables
    schema_columns = harness.normalize.schema_columns

    # Bounded by the tables this tier actually compares, so the assertion is about the
    # evidence this file produces rather than about the schema in the abstract - but
    # every name is resolved and validated through the single in-scope inventory by
    # `scenario_tables`, and none is restated here (R-4).
    subject: list[str] = []
    for scenario in DETERMINISM_SCENARIOS:
        definition = repo_root / SCENARIO_DIR_NAME / f"{scenario}{SCENARIO_SUFFIX}"
        assert definition.is_file(), (
            f"the scenario definition {definition} is absent, so the table list it "
            f"bounds every comparison with cannot be read. The eight definitions "
            f"under harness/scenarios/ are what make a comparison bounded rather "
            f"than unbounded."
        )
        for table in dump_tables.scenario_tables(definition):
            if table not in subject:
                subject.append(table)

    assert subject, (
        "the two determinism scenarios name no affected tables between them, so this "
        "assertion would be vacuous. The affected-table list is how every comparison "
        "in this repository is bounded."
    )

    for table in subject:
        specification = dump_tables.IN_SCOPE[table]
        primary_key = specification.primary_key

        assert not set(primary_key) & set(", "), (
            f"`{table}`'s primary key is declared {primary_key!r}, which is not a "
            f"single column name. A dump orders by ONE column with no tie-break, so a "
            f"composite key would leave the row order undetermined and two runs could "
            f"return the same rows in different orders - a byte difference that is not "
            f"a defect. Agent Action Plan section 0.6.6 records that all 22 in-scope "
            f"tables have a single-column primary key, and this is the check on that."
        )

        columns = schema_columns(frozen_schema, table)
        assert primary_key in columns, (
            f"`{table}`'s primary key {primary_key!r} is not among its columns "
            f"{list(columns)} in mysql/ACASDB.sql. Rows are aligned on that column's "
            f"VALUE, so a key that is not a column leaves no alignment to make."
        )
        assert len(columns) == specification.column_count, (
            f"`{table}` has {len(columns)} column(s) in mysql/ACASDB.sql but "
            f"harness/dump_tables.py declares {specification.column_count} "
            f"[mysql/ACASDB.sql:L{specification.schema_line}]. Rows are POSITIONAL, so "
            f"a width disagreement means the two sides of any comparison are aligning "
            f"different columns - and Agent Action Plan section 0.8.1 makes an altered "
            f"schema a defect in the migration."
        )

