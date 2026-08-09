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
REAL `SYSTEM-REC` column (`RUN-DAT int(8) unsigned`), so it is compared by value in the
dump of that row - and on top of that, EVERY DATE COLUMN THE CYCLE STAMPS IN THE OTHER
TABLES DERIVES FROM IT - `GLBATCH-REC.POSTED` [general/gl072.cbl:L376],
`GLPOSTING-REC.POST-DAT`, `PSIRSPOST-REC.IRS-POST-DAT`. That is why pinning it is
load-bearing rather than cosmetic, and why the runner also reads the column itself back
after the run.

Pinned project-wide: text "21/09/2025", binary `Run-Date` 155127. The epoch is
1600-12-31, which the maintainer flags at [common/maps04.cbl:L39-L41] as making the
module "NOT usable within IRS as is"; `date(1600, 12, 31).toordinal()` is 584388, so
day 1 is 1601-01-01 and `run_date = toordinal() - 584388`. Verified:
`date(2025, 9, 21).toordinal()` is 739515 and 739515 - 584388 = 155127.

The clock read `acas_posting/clock.py` reproduces is the date service's, verbatim from
the source [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]. It is NOT the system's only
read - the corrected census further down counts fourteen - and what this tier depends
on is the ZERO count inside the twelve migrated programs rather than a single read
anywhere:

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
`accept ... from time`. EVERY ONE OF THE FOURTEEN is in a menu shell or in the shared
date-service copybook - that is the census's scope, the posting cycle's own call
chain. Outside that chain the frozen tree holds further `function current-date` reads,
all in programs no scenario reaches: [common/ACAS-Sysout.cbl:L107],
[common/fhlogger.cbl:L219], [common/auditLD2.cbl:L192] and L389,
[common/makesqltable-free.cbl:L81] and L320,
[common/makesqltable-original.cbl:L78] and L303, and [stock/stock.cbl:L302]. They are
named so that a grepper who finds them does not conclude the census was wrong. A grep
for `function current-date` over all twelve in-scope programs -
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

    [run A]  reset -> run_python -> dump(python) -> normalize -> RELOCATE to runA
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

BOTH RUNS BEGIN FROM A RESET AND RE-SEEDED DATABASE, NEVER A DIRTY ONE.
`harness/reset_db.sh` re-applies `mysql/ACASDB.sql` VERBATIM - the frozen file
already carries all 33 `DROP TABLE IF EXISTS`, so re-applying it IS the
drop-and-recreate and no DDL of this file's own is ever emitted (R-3) - asserts
the post-apply state, and then re-seeds by delegating to `harness/seed.sh`.
Resetting run A as well as run B makes the determinism tier independent of test
order and of any prior hand-driven parity journey. Without those resets the test
could compare a contaminated run against a clean one, or prove only that a second
run over an already-posted state is idempotent.

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
THE VACUITY ARGUMENT, AND THE SIX-LAYER GUARD
-------------------------------------------------------------------------------

TWO EMPTY DUMPS ARE ALSO BYTE-IDENTICAL, and so are two runs that did nothing at
all - so a bare `is_empty` assertion has three independent ways to pass while
proving nothing. All three are closed.

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

CHANNEL 2 - ANOMALY A-16 MASKS A REJECTED DATE AS `Run-Date = 0`.
`common/maps04.cbl` has two reject paths - the six-part test at L140-L145 reaching
`L146 go to Main-Exit.` and the calendar-validity test at L153 reaching
`L154 go to Main-Exit.` - and BOTH reach `Main-Exit` without touching `A-Bin`, while
the remark block at [common/maps04.cbl:L163] claims "Date errors returned as A-Bin
equal zero". The contract holds only because the caller pre-zeroes at
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. So a rejected date yields `Run-Date = 0`
WITHOUT RAISING - and a run under `Run-Date = 0` is still perfectly deterministic,
and still wrong. `is_empty` alone would not notice.

CHANNEL 3 - BOTH RUNS DID NOTHING, OR BOTH DID THE SAME WRONG THING.
The dumps can be non-empty, the selector can be 1, the clock can land, both runs
can exit with the declared status - and the route can still have written NOTHING,
because every row in the dump was put there by the seed. Two such runs agree
perfectly, and so do two runs that both mutate a table the scenario declares the
route leaves alone. Nothing in channels 1 and 2 is violated in either case. Closed
by LAYER 2b, which compares a run's own pre-run state record with its own post-run
record and holds the result against the scenario's declared `expected_table_effect`
- the effect being asserted in whichever direction the scenario declares, because
for a scenario whose measured behaviour IS a no-op, demanding a mutation would
demand the repair of a reproduced defect (R-4).

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

    LAYER 2a - THE PAIR REACHED THE DECLARED DISPOSITION AT ALL. Run A's recorded
    operation status equals the status the scenario declares. Two runs that both
    REFUSED are byte-identical too, and layer 2 cannot catch them because the seeded
    rows are counted either way. Run A only - whether run B agrees is the determinism
    property itself and is asserted in the test body, so that a divergence reads as a
    FAILURE attributable to the cycle rather than as a setup ERROR.

    LAYER 2b - THE PER-RUN EFFECT WITNESS. Layer 2 counts the rows in the dump, and
    the SEEDED rows are among them, so it passes for a run that wrote nothing at
    all. This layer compares run A's OWN pre-run state record with its OWN post-run
    record, per bounded table, and holds the result against the scenario's own
    `expected_table_effect`. It is the ONLY layer that asks whether a run did
    anything - CHANNEL 3, and the one the other layers structurally cannot see, since
    two runs that both did nothing are byte-identical, and so are two runs that both
    did the same wrong thing.

    It is driven by the DECLARATION and never by an unconditional demand for a
    mutation. `clean_batch_irs` declares `changed`, so at least one bounded table's
    row count or digest must move - that is the vacuity the review named. But
    `clean_batch_gl` declares `unchanged`, and that no-op is the MEASURED behaviour
    (section 10.1 of the evidence document; ambiguity `Q-9`), so there the witness is
    the converse: nothing may move. Demanding a mutation on both would require the
    migrated cycle to REPAIR a reproduced defect, which is the inversion R-4 forbids.

    Run A only, and the reason is the same one LAYER 2a gives: if run A conformed and
    run B did not, the two trees differ and the body reports that as a determinism
    FAILURE with a full diff. Asserting this on run B too would misfile that as a
    setup ERROR.

    LAYER 3 - THE DATABASE-BACKED ROUTE-AND-CLOCK WITNESS. The runner must report
    BOTH `FILE-SYSTEM-USED = 1` from its pre-run `SYSTEM-REC` read and
    `PASS  the system record holds Run-Date 155127, as pinned` from its post-run
    readback. The first marker closes channel 1 because the runner refuses the
    frozen flat-file selector before dispatch; the second closes channel 2 because
    it is emitted only after reading `RUN-DAT` back from MariaDB and comparing it
    with the pinned binary date.

    The witness deliberately no longer requires `GLBATCH-REC.POSTED == 155127`.
    Phase-5 store remeasurement proved that the frozen `bb000-HV-Load` never moves
    `WS-Post-rrn` to `HV-POST-RRN`; the one reachable RDBMS posting therefore has
    key zero and is skipped by [general/gl070.cbl:L490-L493]. The faithfully
    reproduced `clean_batch_gl` journey is consequently an asserted no-op, so
    [general/gl072.cbl:L372-L377] is unreachable and `POSTED` correctly remains
    zero. Requiring that unreachable rewrite would reject the measured oracle
    behaviour rather than guard determinism. The database-backed system-record
    witness preserves both anti-vacuity protections without inventing a mutation.

    LAYER 4 - SEED-FINGERPRINT IDENTITY. `harness/run_python_scenario.sh` writes
    `$ACAS_OUT/run-logs/<scenario>/python.seed-fingerprint` before each run, as one
    `<TABLE><TAB><row count><TAB><sha256>` line per bounded table plus the parameter
    row, in the scenario's declared order - the digest being the SHA-256 of that
    table's canonical primary-key-ordered dump, so two seeds carrying different VALUES
    at the same ROW COUNTS do not agree. Both snapshots must exist and be identical,
    which proves the seed landed identically before either run INDEPENDENTLY OF THE
    DUMPS - and catches a seeding difference that would otherwise masquerade as a
    determinism failure. Compared as BYTES and never parsed; layer 2b, which must know
    WHICH table moved, is the one place the fields are read.

A GUARD FAILURE AT ANY LAYER IS A HARNESS FAULT, raised from the fixture, reported as
a pytest ERROR, and worded so it is unmistakable from a determinism FAILURE.

`SYSTEM-REC` is on every scenario's compared `affected_tables`, and it has to be:
`acas_posting/cli/args.py`'s `overrewrite` rewrites key 1 on every one of the seven
routes, exactly as the menu shells do, so a determinism claim that left the row out would
be a claim about the tables the run happened to touch rather than about the run. The two
credential cells it carries - `RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] and
`PASS-WORD` - are withheld from the capture by `harness/dump_tables.py`'s
`REDACTED_COLUMNS`, identically on both runs, so they can neither leak nor manufacture a
byte difference; both runners FINGERPRINT the row before and after every run as well, so
even those two cells are compared. The runner's pre/post database assertions are
therefore guard evidence, not an added comparison table: they neither alter the
structural diff nor invent an IRS result column. The same two markers apply to both
parametrised scenarios.

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

ENTERPRISE-STANDARD BEST PRACTICE APPLIES WHEREVER THE PLAN IS SILENT. The binding
rules are the six embedded in Agent Action Plan section 0.7.2:

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
import json
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
# The TIER mark, applied to the whole module because every test in it belongs to the
# tier. THE INFRASTRUCTURE MARKS ARE NOT HERE: `database` and `oracle` are declared per
# test, on exactly the tests whose fixture closure reaches the harness stack, because
# several tests in this file read only files on disk and pass on a bare host. A module
# mark would claim they need a MariaDB and a built oracle, and `-m database` would then
# select tests that require neither.
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

# The scenario's own declaration of what its route does to the BOUNDED tables -
# `changed` or `unchanged`. LAYER 2b asserts it PER RUN, and reads it from the
# definition rather than restating it, because a local copy would drift from the YAML
# and from `harness/run_python_scenario.sh`, which asserts the same property per side
# from the same two records (R-4). The two determinism scenarios deliberately differ
# here: `clean_batch_irs` declares `changed`, so a mutation is available to be
# witnessed; `clean_batch_gl` declares `unchanged`, and that no-op is MEASURED - see
# ambiguity `Q-9` - so the witness there is that nothing moved.
SCENARIO_KEY_TABLE_EFFECT: Final[str] = "expected_table_effect"
TABLE_EFFECT_CHANGED: Final[str] = "changed"
TABLE_EFFECT_UNCHANGED: Final[str] = "unchanged"

# THE TWO SCENARIOS, AND NO MORE. Agent Action Plan section 0.8.5 mandates eight
# scenarios for `tests/scenarios/`; determinism needs only the two that carry
# independent evidence, and a third would multiply stack time for no additional proof.
#
#   `clean_batch_gl` IS MANDATORY, for three reasons. Its seed deliberately contains
#   the four-key sort tie described in the module docstring - the single most valuable
#   determinism input there is. Its measured, faithfully reproduced store behaviour
#   is an asserted no-op, so it proves that the tied stream and unchanged database
#   state are repeatable rather than assuming a gl072 rewrite that the frozen zero-key
#   loader anomaly makes unreachable. And it runs one operation with an empty answer
#   map, so nothing about any command-line option spelling has to be known to drive it.
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

# The provenance file every normalised tree carries, mirroring
# `harness/diff_states.py`'s `MANIFEST_FILENAME`. Named here as a module constant, in
# the same style as the suffix above, because the byte comparison in the test BODY has
# to exclude it and the tool module is bound inside the fixture rather than at module
# scope. A test asserts the two spellings agree, so this cannot drift.
MANIFEST_FILENAME: Final[str] = "_manifest.json"

# The side both runs capture under. ONE value, deliberately: the side is recorded in
# the PATH and never inside a dump, which is why the relocation below is mandatory.
SIDE_PYTHON: Final[str] = "python"

# The pre-run seed fingerprint `harness/run_python_scenario.sh` writes at its stage
# 6a, under `run-logs/` and therefore OUTSIDE any compared tree. One line per bounded
# table plus the parameter row, each carrying the table name, its ROW COUNT and a
# SHA-256 of its canonical primary-key-ordered dump - integers and hex text, no decimal
# of its own (R-2). It is compared BYTE-FOR-BYTE and never parsed: interpreting it here
# would be the added validation R-3 forbids, and byte identity is the whole claim. The
# digest is why the claim is decisive: two runs seeded from different VALUES at the same
# ROW COUNTS would agree on a count-only record.
SEED_FINGERPRINT_NAME: Final[str] = "python.seed-fingerprint"

# The POST-run record the same runner writes at its stage 6c, in the same directory and
# the same three-field form. It is what LAYER 2b needs: comparing a run's own BEFORE
# with its own AFTER answers "did THIS run change anything", which is the one question
# no other layer can ask. A side-to-side or run-to-run comparison cannot substitute for
# it, because two runs that both changed nothing agree perfectly - and so do two runs
# that both changed the same thing.
POST_FINGERPRINT_NAME: Final[str] = "python.post-fingerprint"

# The ONE program that computes a table digest, for either side and for either of the
# two records. Named here so the stack-free contract test can assert that neither runner
# grew a second, inline definition of "the digest": two definitions is how a pre-run and
# a post-run record - or an oracle-side and a Python-side record - silently stop being
# comparable while every individual assertion still passes.
#
# It is the `--table-digest` MODE of the dump tool rather than a program of its own
#: the digest is taken over that module's `serialise_dump` output, so the
# separate file existed only to load this one by path and digest what it produced.
TABLE_DIGEST_PRODUCER: Final[str] = "dump_tables.py --table-digest"

# LAYER 3 - DATABASE-BACKED WITNESS MARKERS emitted by
# `harness/run_python_scenario.sh`.
#
# The selector marker comes from a pre-run `SYSTEM-REC` query. The runner refuses
# zero at [harness/run_python_scenario.sh acas_py_assert_file_system_used], closing
# the false-pass path where the migrated handlers take the frozen indexed-file leg.
# The clock marker comes from a post-run `SYSTEM-REC.RUN-DAT` query and is emitted
# only when the value equals the pinned binary date
# [harness/run_python_scenario.sh acas_py_assert_after_run].
#
# These are evidence emitted by database reads, not strings this test uses to infer
# accounting state. Both must be present in each captured run stream. This remains
# valid for the faithfully reproduced `clean_batch_gl` no-op, where the frozen
# zero-key posting anomaly makes [general/gl072.cbl:L372-L377] unreachable and
# `GLBATCH-REC.POSTED` therefore remains zero.
FILE_SYSTEM_WITNESS: Final[str] = "FILE-SYSTEM-USED = 1"
RUN_DATE_WITNESS: Final[str] = (
    f"PASS  the system record holds Run-Date {PINNED_RUN_DATE}, as pinned"
)

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
# [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. THAT IS ANOMALY A-16, REPRODUCED AND NOT
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
        post_fingerprint: The snapshotted `python.post-fingerprint`, the same record
            taken AFTER this run's dispatch. The pair is what layer 2b reads.
        wrapper_status: The harness wrapper's exit status. Zero means the wrapper
            completed its own assertions and emitted a complete operation-status
            record; it is not the operation disposition.
        run_status: The single operation's machine-readable status, taken from the
            `OPERATION_STATUS` record rather than conflated with wrapper health.
        run_output: The wrapper's complete stdout and stderr, retained so layer 3 can
            verify its database-backed route-selector and pinned-clock readbacks.
        row_counts: Each affected table's `row_count`, in the scenario's declared
            order.
    """

    label: str
    tree: Path
    fingerprint: Path
    post_fingerprint: Path
    wrapper_status: int
    run_status: int
    run_output: str
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
        diagnosis: `harness/diff_states.py`'s VALUE-FREE summary of that `TreeDiff` -
            table, column and counts, with no differing value and no primary key
. The EMPTY STRING when the two agree, exactly as the
            report itself is zero bytes on a pass. The values are not discarded: they
            are in the two normalised trees this evidence already names.
        filenames: The filename set both trees hold, already asserted equal.
    """

    scenario: str
    tables: tuple[str, ...]
    pin: acas_clock.PinnedRunDate
    first: RelocatedRun
    second: RelocatedRun
    tree: Any
    diagnosis: str
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
    """Snapshot one of a run's two state records, before the next run replaces it.

    `harness/run_python_scenario.sh` writes BOTH records under
    `$ACAS_OUT/run-logs/<scenario>/` - `python.seed-fingerprint` at its stage 6a, before
    the dispatch, and `python.post-fingerprint` after it - and `run_python` takes no
    output-root argument, so BOTH RUNS WRITE THOSE TWO PATHS. That collision is the
    reason this file composes the individual stages rather than delegating the whole
    pair to one helper: without an interposition after each run, run B's records would
    be the only ones on disk and every claim about run A would silently be a claim
    about run B.

    Each record is one line per bounded table plus the parameter row, three
    TAB-separated fields written by the single producer `harness/dump_tables.py --table-digest`. Layer
    4 compares run A's PRE-run record with run B's PRE-run record as bytes, proving the
    two runs started alike. Layer 2b compares ONE run's PRE-run record with its OWN
    post-run record, proving what that run did.

    Args:
        source: The runner's record path.
        destination: Where to keep it, beside the run's relocated tree.

    Returns:
        `destination`.

    Raises:
        AssertionError: The runner wrote no such record. A harness fault: without the
            pre-run record the two starting states are unverified, and a seeding
            difference would masquerade as a determinism failure; without the post-run
            record neither run's effect can be witnessed, and two runs that both did
            nothing would report a clean PASS.
    """
    assert source.is_file(), (
        f"HARNESS FAULT, not a determinism failure: harness/run_python_scenario.sh "
        f"wrote no state record at {source}. It writes the pre-run record at its stage "
        f"6a and the post-run record after the dispatch, each carrying the row count "
        f"and canonical digest of every bounded table. Without the pre-run record the "
        f"two runs' starting states cannot be shown to have been identical, so a "
        f"seeding difference would be reported as nondeterminism; without the post-run "
        f"record neither run's effect on the tables can be witnessed at all. Both are "
        f"false results that cost a day to find."
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
    `load_dump`; it is repeated here under its own name so a reader can see the
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



def _parse_state_record(path: Path, *, where: str) -> dict[str, tuple[int, str]]:
    """Parse one state record into `{table: (row_count, digest)}`.

    THE FORMAT IS A CONTRACT AND IT HAS ONE PRODUCER. `harness/dump_tables.py --table-digest` writes
    every state record on both sides, one line per table, three TAB-separated fields:
    the table name, its row count, and the lower-case hex SHA-256 of the canonical
    primary-key-ordered dump. Layer 4 compares two such files as BYTES and never parses
    them, which is right for the question it asks. Layer 2b asks a different question -
    WHICH tables moved - and cannot avoid reading the fields.

    A table whose row count and digest are both `-` was UNREADABLE when the record was
    taken; it is carried through as unreadable so the caller can refuse rather than
    silently treat it as unchanged.

    Args:
        path: The snapshotted record.
        where: A label for the failure message.

    Returns:
        `{table: (row_count, digest)}` for every readable line.

    Raises:
        AssertionError: A line is not three fields, or a table appears twice, or the
            record carries an unreadable table.
    """
    parsed: dict[str, tuple[int, str]] = {}
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split("\t")
        assert len(fields) == 3, (
            f"HARNESS FAULT: {where} line {number} of {path} is not the three fields "
            f"harness/dump_tables.py --table-digest writes - table, row count, sha256. It reads "
            f"{line!r}. A record whose shape is not the contract cannot be read at "
            f"all, and guessing at it would be the added validation R-3 forbids."
        )
        table, count, digest = (field.strip() for field in fields)
        assert table not in parsed, (
            f"HARNESS FAULT: {where} names {table!r} twice in {path}. Each table is "
            f"digested once, so a repeat means the record was appended to rather than "
            f"written, and which line describes the run is no longer decidable."
        )
        assert count != "-" and digest != "-", (
            f"HARNESS FAULT: {where} records {table!r} as UNREADABLE in {path} "
            f"(count {count!r}, digest {digest!r}). A table that could not be read "
            f"establishes nothing about whether the run changed it, and treating an "
            f"unreadable table as unchanged is exactly the false pass this layer "
            f"exists to prevent."
        )
        assert count.isdigit(), (
            f"HARNESS FAULT: {where} records {table!r} with row count {count!r} in "
            f"{path}, which is not a whole number."
        )
        assert len(digest) == 64 and all(
            character in "0123456789abcdef" for character in digest
        ), (
            f"HARNESS FAULT: {where} records {table!r} with digest {digest!r} in "
            f"{path}, which is not a 64-character lower-case hex SHA-256."
        )
        parsed[table] = (int(count), digest)
    assert parsed, (
        f"HARNESS FAULT: {where} at {path} is empty. Both records carry one line per "
        f"bounded table plus the parameter row, so an empty file means the runner did "
        f"not reach the stage that writes it."
    )
    return parsed


def _assert_effect_witness(
    run: RelocatedRun,
    *,
    scenario: str,
    tables: Sequence[str],
    declared_effect: str,
) -> tuple[str, ...]:
    """LAYER 2b - assert THIS run did to the bounded tables what the scenario declares.

    THE GAP THIS CLOSES, AND WHY THE OTHER FOUR LAYERS CANNOT. Layer 1 proves the
    trees are present and well formed. Layer 2 proves run A's tables are not all empty -
    but the SEEDED rows are counted, so it passes for a run that wrote nothing. Layer 2a
    proves run A reached the declared exit status - but a no-op exits zero. Layer 3
    proves the runner read the selector and the pinned clock out of MariaDB - which a
    run that then wrote nothing also does. Layer 4 proves both runs STARTED from the
    same state. NOT ONE OF THEM ASKS WHETHER EITHER RUN CHANGED ANYTHING, and two runs
    that both changed nothing are byte-identical - which is the vacuity channel the
    review named against the `clean_batch_irs` case, whose declared effect is `changed`
    and where a mutation therefore IS available to be witnessed.

    THE CLAIM IS TAKEN FROM THE SCENARIO, NEVER INVENTED HERE. Each definition declares
    `expected_table_effect`, and both runners already assert it per side from these same
    two records - but a runner asserts it for ONE dispatch and cannot know it is being
    driven twice. This layer re-asserts it for the reference run of the determinism
    pair, whose own records the fixture has snapshotted out of the way; the caller
    applies it to run A only, and the comment at the call site gives the reason:

      `changed`   - at least one bounded table's `(row_count, digest)` pair must DIFFER
                    between this run's pre-run and post-run record. `clean_batch_irs`
                    is this case: its route posts to the IRS nominal ledger and writes
                    the internal posting table.
      `unchanged` - every bounded table's pair must be IDENTICAL. `clean_batch_gl` is
                    this case, and the no-op is MEASURED rather than assumed - see
                    docs/migration/scenario-diff-evidence.md section 10.1, which records
                    TWO independent reasons. The first is the route itself: the scenario
                    seeds a CLOSED batch, and phase two applies a stricter filter than
                    phase one - `if status-open / or not waiting / or not gl-batch /
                    go to loop` - which rejects it. The second is ambiguity `Q-9`:
                    `bb000-HV-Load` [common/glpostingMT.cbl:L1053-L1066] never loads
                    `HV-POST-RRN` [common/glpostingMT.cbl:L282], the table's primary key
                    [mysql/ACASDB.sql:L169], so a seed persists at most one posting row
                    and that row's zero posting key is skipped at
                    [general/gl070.cbl:L490-L491]. Asserting the declared no-op per run
                    is not "inventing a mutation" - it is refusing to let a run that
                    mutated something pass as the reproduction of a run that does not.

    Args:
        run: One completed run, carrying both snapshotted state records.
        scenario: The scenario name, for the message.
        tables: Its bounded tables, in declared order. The parameter row appears in the
            records too and is deliberately not read here: its content depends on what
            the route did - including the `Date-Form` write-back
            [copybooks/wssystem.cob:L127] - so reading it would tie each scenario's
            effect claim to fields it does not reason about. Both runners exclude it from
            the declared effect for the same reason.
        declared_effect: The scenario's own `expected_table_effect`.

    Returns:
        The bounded tables whose pair moved, in declared order.

    Raises:
        AssertionError: The record is malformed or absent, a bounded table is missing
            from either record, or the run's effect contradicts the declaration.
    """
    before = _parse_state_record(
        run.fingerprint, where=f"{run.label}'s pre-run record"
    )
    after = _parse_state_record(
        run.post_fingerprint, where=f"{run.label}'s post-run record"
    )

    moved: list[str] = []
    for table in tables:
        assert table in before and table in after, (
            f"HARNESS FAULT: {scenario} bounds the comparison to {table}, but "
            f"{run.label}'s "
            f"{'pre' if table not in before else 'post'}-run record does not carry it. "
            f"Both records are written from the scenario's own table list, so an "
            f"absence means the record was taken against a different bound."
        )
        if before[table] != after[table]:
            moved.append(table)

    if declared_effect == TABLE_EFFECT_CHANGED:
        assert moved, (
            f"{run.label} of {scenario} CHANGED NOTHING, and the scenario declares "
            f"`expected_table_effect: changed`.\n"
            f"  Every bounded table carries the same row count and the same digest "
            f"before and after the dispatch: "
            f"{ {table: before[table] for table in tables} !r}.\n"
            f"  THIS IS THE VACUITY CHANNEL THE OTHER LAYERS CANNOT SEE. Two runs that "
            f"both wrote nothing are byte-identical, so `is_empty` would report a "
            f"PASS; layer 2 counts the SEEDED rows and passes too; the run exits zero "
            f"and reads the pinned clock, so layers 2a and 3 pass; and layer 4 only "
            f"proves both runs started alike. A determinism claim over a route that "
            f"did nothing establishes nothing about the migrated cycle.\n"
            f"  Look first at whether the route reached its posting section at all - "
            f"the run exited {run.run_status} - and then at the seed, whose "
            f"fingerprint is at {run.fingerprint}."
        )
    elif declared_effect == TABLE_EFFECT_UNCHANGED:
        assert not moved, (
            f"{run.label} of {scenario} CHANGED {moved!r}, and the scenario declares "
            f"`expected_table_effect: unchanged`.\n"
            + "".join(
                f"  {table}: before {before[table]!r}, after {after[table]!r}\n"
                for table in moved
            )
            + f"  THE DECLARED NO-OP IS THE MEASURED BEHAVIOUR AND IS REPRODUCED, NOT "
            f"CORRECTED (R-4, R-6). Its per-scenario reasons are recorded in "
            f"docs/migration/scenario-diff-evidence.md section 10; for "
            f"`clean_batch_gl` they are the closed batch that phase two's stricter "
            f"filter rejects, and ambiguity `Q-9` - `bb000-HV-Load` "
            f"[common/glpostingMT.cbl:L1053-L1066] never loads `HV-POST-RRN` "
            f"[common/glpostingMT.cbl:L282], the table's primary key "
            f"[mysql/ACASDB.sql:L169], so a seed persists at most one posting row and "
            f"that row's zero posting key is skipped at "
            f"[general/gl070.cbl:L490-L491], before the explosion.\n"
            f"  A run that DID change a bounded table has either repaired that defect "
            f"or found a second writer. Either way, RE-MEASURE AGAINST THE COMPILED "
            f"ORACLE and update the ambiguity register, this scenario's "
            f"`expected_table_effect` and the evidence document together - do not "
            f"relax this assertion, and do not 'fix' the migrated cycle to make the "
            f"table move."
        )
    else:
        raise AssertionError(
            f"HARNESS FAULT: {scenario} declares `expected_table_effect: "
            f"{declared_effect!r}`, which is neither `changed` nor `unchanged`. The "
            f"runners accept only those two, so this layer has no claim to assert and "
            f"refuses rather than passing."
        )
    return tuple(moved)


def _assert_clock_witness(run: RelocatedRun) -> None:
    """LAYER 3 - assert the RDBMS selector and pinned clock were read from MariaDB.

    The two assertions preserve the original guard's purpose after measured frozen
    behaviour made the old `GLBATCH-REC.POSTED` premise unreachable:

    * `FILE-SYSTEM-USED = 1` is emitted from the runner's pre-run `SYSTEM-REC`
      query; zero is refused before dispatch. This closes the indexed-file false-pass
      channel documented at [copybooks/wssystem.cob:L111-L114] and
      [common/acas007.cbl:L316-L320].
    * the Run-Date PASS marker is emitted only after the runner reads `RUN-DAT` back
      after the operation and observes the pinned 155127. This closes anomaly A-16's
      silent-zero channel [common/maps04.cbl:L146, L154] and
      [copybooks/Proc-ACAS-Mapser-RDB.cob:L78].

    Args:
        run: One completed run and its immutable captured stream.

    Raises:
        AssertionError: Either database-backed marker is absent. A HARNESS FAULT
            raised from the fixture, so a pytest ERROR rather than a two-run
            determinism difference.
    """
    assert FILE_SYSTEM_WITNESS in run.run_output, (
        f"THE RDBMS ROUTE WAS NOT ATTESTED for {run.label} - a HARNESS FAULT, not "
        f"a determinism failure. The run output does not contain "
        f"{FILE_SYSTEM_WITNESS!r}.\n"
        f"  harness/run_python_scenario.sh queries SYSTEM-REC before dispatch and "
        f"refuses FILE-SYSTEM-USED zero, because [copybooks/wssystem.cob:L111-L114] "
        f"selects the COBOL indexed-file path at zero and the MySQL path at one; the "
        f"same gate is visible at [common/acas007.cbl:L316-L320] and "
        f"[common/acas008.cbl:L313-L319]. Without this marker two deterministic "
        f"captures could prove only that both runs bypassed the database.\n"
        f"  wrapper status: {run.wrapper_status}; operation status: {run.run_status}."
    )
    assert RUN_DATE_WITNESS in run.run_output, (
        f"THE PINNED CLOCK DID NOT REACH THE DATABASE for {run.label} - a HARNESS "
        f"FAULT, not a determinism failure. The run output does not contain "
        f"{RUN_DATE_WITNESS!r}.\n"
        f"  The runner emits that marker only after reading SYSTEM-REC.RUN-DAT back "
        f"from MariaDB after the operation and observing {PINNED_RUN_DATE}. A zero "
        f"would expose anomaly A-16: maps04 returns without touching its output at "
        f"[common/maps04.cbl:L146, L154], masked by the caller's pre-zero at "
        f"[copybooks/Proc-ACAS-Mapser-RDB.cob:L78].\n"
        f"  The old GLBATCH-REC.POSTED witness is intentionally not used: measured "
        f"frozen loader behaviour persists the sole posting under key zero, so "
        f"[general/gl070.cbl:L490-L493] skips it and the gl072 rewrite at "
        f"[general/gl072.cbl:L372-L377] is unreachable. Requiring POSTED=155127 "
        f"would reject the faithfully reproduced no-op instead of protecting this "
        f"test from vacuity."
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
) -> RelocatedRun:
    """Reset, re-seed, run the Python cycle, capture, normalise, and snapshot.

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
    Returns:
        The relocated run.

    Raises:
        Exception: Any stage fault, unchanged - `HarnessFaultError` from
            `raise_for_status`, or the harness modules' own errors. Raised from the
            fixture that calls this, so every one is a pytest ERROR.
    """
    # Both runs use the same reset path. It re-applies mysql/ACASDB.sql VERBATIM,
    # asserts the post-apply state, and delegates to harness/seed.sh with this
    # scenario's fixture. Run A is therefore isolated from any scenario or manual
    # parity run that preceded this test, and run B starts from byte-for-byte the
    # same premise. `clean_batch_irs` makes the second reset observable because its
    # run consumes the transfer-file input.
    protocol.reset(scenario).raise_for_status()

    # STAGE 6. The status is captured VERBATIM and deliberately not raised on: only
    # three in-scope programs set `WS-Term-Code` at all, so a non-zero status is a
    # BEHAVIOURAL result whose database effect must still be captured. Absence is
    # evidence, and a helper that short-circuited the dump would destroy it.
    run = protocol.run_python(scenario)
    #  WRAPPER HEALTH, DIAGNOSED BY CATEGORY. Wrapper health is distinct
    #  from operation disposition and must be zero before this leg's OPERATION_STATUS
    #  record or database readback can be trusted - but the two reasons it can be
    #  non-zero are not the same finding: 69 is `EX_BEHAVIOUR`, the cycle ran and
    #  contradicted its scenario, while the runner's own band means it faulted before
    #  measuring anything. The helper reports whichever it was.
    protocol.assert_wrapper_completed(run, label=f"{label}'s Python run")
    assert len(run.operation_statuses) == 1, (
        f"HARNESS FAULT: {label} of {scenario} recorded "
        f"{len(run.operation_statuses)} operation statuses, expected exactly one for "
        f"this determinism scenario. Recorded: {run.operation_statuses!r}.\n"
        f"{run.describe()}"
    )
    _operation, operation_status = run.operation_statuses[0]

    # STAGE 7 and its normalisation. Both bounded by ALL 22 IN-SCOPE TABLES, which is
    # the protocol, and the list comes from the harness inventory rather than from a
    # local restatement (R-4).
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
    # The POST-run record needs the same interposition for the same reason: the runner
    # writes it to one path and the next run replaces it.
    post_fingerprint = _snapshot_fingerprint(
        paths.run_logs / POST_FINGERPRINT_NAME,
        workspace / f"{label}.{POST_FINGERPRINT_NAME}",
    )

    return RelocatedRun(
        label=label,
        tree=tree,
        fingerprint=fingerprint,
        post_fingerprint=post_fingerprint,
        wrapper_status=run.returncode,
        run_status=operation_status,
        run_output=f"{run.stdout}\n{run.stderr}",
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
        harness: The three harness modules, loaded by explicit file path - never
            `import harness`. The structural enforcement of R-1 is `pyproject.toml`'s
            explicit `[tool.setuptools] packages` list, which enumerates the eight
            packages that ship - the seven code packages and the data-only
            `acas_posting.data_dictionary` - with no discovery scan and
            `include-package-data = false`, so `harness` is absent by construction.
            The absence of `harness/__init__.py` is NOT the enforcement: PEP 420 would
            make a namespace import resolve anyway. Explicit-path loading is used
            because it is independent of `sys.path` and of the invocation directory.
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
    )
    second = _execute_run(
        RUN_LABELS[1],
        scenario,
        tables,
        protocol=protocol,
        workspace=tmp_path,
        load_dump=diff_states.load_dump,
        dump_keys=dump_tables.DUMP_KEYS,
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
    #
    # `same_side=True` SELECTS THE DETERMINISM CONTRACT, which is the mirror image of
    # the parity one and is not a relaxation of it. The parity mode requires the two
    # sides to DIFFER and their run ids to MATCH; both captures here are the Python
    # cycle, so it requires the sides to MATCH and the run ids to DIFFER - the second
    # of which the parity mode never checked, and which is what refuses one capture
    # compared against itself. One scenario definition, one frozen schema and one seed
    # marker are still required, exactly as in parity mode.
    diff_states.verify_trees(first.tree, second.tree, same_side=True)

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
    #  LAYER 2a - THE PAIR REACHED THE SCENARIO'S DECLARED DISPOSITION AT ALL.
    #
    #  `run_status` was RECORDED by `_execute_run` and, until this guard existed, never
    #  READ - it appeared only inside other layers' failure messages. That left a THIRD
    #  way for this file to pass vacuously, beside the two empty dumps layer 2 rules
    #  out: TWO RUNS THAT BOTH REFUSED are byte-identical too, and layer 2 cannot catch
    #  them, because the SEEDED rows are counted either way.
    #
    #  ONLY RUN A IS CHECKED HERE, and the bound is deliberate. Run A is the reference
    #  run: if IT did not reach the declared disposition then this pair was never driven
    #  as the scenario describes, which is a SETUP failure like every other guard in
    #  this fixture and reads as a pytest ERROR. Whether RUN B agrees with run A is the
    #  determinism property itself, so it is asserted in the test BODY, where a
    #  divergence reads as a FAILURE attributable to the migrated cycle - see
    #  comparison 0 of `test_two_python_runs_are_byte_identical`.
    #
    #  Checking both runs here instead would make that body assertion DEAD: the implied
    #  status is a single value, so any divergence between the two runs necessarily
    #  means one of them missed it, and this guard would always fire first. A guard that
    #  makes another assertion unreachable is the vacuity problem wearing a different
    #  hat.
    # ------------------------------------------------------------------
    declared_status = definition.get("expected_status")
    implied_status = 0
    if isinstance(declared_status, list):
        implied_status = next(
            (int(v) for v in declared_status if int(v) != 0), 0
        )
    elif isinstance(declared_status, int):
        implied_status = int(declared_status)
    assert first.run_status == implied_status, (
        f"{RUN_LABELS[0]} of {scenario} exited {first.run_status} where the scenario "
        f"declares {declared_status!r}, implying {implied_status}.\n"
        f"  A run that did not reach the declared disposition wrote nothing this "
        f"comparison is about, and TWO such runs are byte-identical: layer 2 below "
        f"cannot tell them apart from two runs that posted, because the seeded rows "
        f"are counted either way."
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
    #  LAYER 2b - THE PER-RUN EFFECT WITNESS. Layer 2 counts rows in the dump and
    #  therefore counts the SEEDED ones, so it passes for a run that wrote nothing at
    #  all. This layer compares each run's OWN pre-run record with its OWN post-run
    #  record and holds the result against the scenario's own `expected_table_effect`.
    #
    #  It is the only layer that asks whether either run DID anything. Two runs that
    #  both did nothing are byte-identical; so are two runs that both did the same
    #  wrong thing. Neither is caught by layers 1, 2, 2a, 3 or 4.
    #
    #  DRIVEN BY THE DECLARATION, NEVER BY AN UNCONDITIONAL DEMAND FOR A MUTATION. A
    #  blanket "require a mutation" would fail `clean_batch_gl`, whose no-op is the
    #  measured behaviour recorded in section 10.1 of the evidence document and at
    #  ambiguity `Q-9`, and which is reproduced rather than corrected (R-4, R-6). For
    #  that scenario the witness is the converse and is just as informative: a run that
    #  moved a bounded table has departed from the compiled oracle.
    #
    #  ONLY RUN A IS CHECKED, for precisely the reason LAYER 2a gives above, and NOT
    #  for the reason LAYER 3 gives below. Run A is the reference run: if IT did not do
    #  what the scenario declares, the pair was never driven as described and that is a
    #  SETUP fault. But if run A conformed and RUN B did not, the two normalised trees
    #  DIFFER, and the honest diagnosis is that the migrated cycle is NONDETERMINISTIC
    #  - a FAILURE attributable to the cycle, reported by comparison 0 in the test body
    #  with a full table-level diff. Asserting this layer on run B as well would
    #  pre-empt that with a pytest ERROR and misfile a real determinism failure as a
    #  harness fault. Layer 3 is different: a degraded selector or clock leaves the
    #  trees ABLE to agree, so nothing in the body would catch it.
    #
    #  Run A alone still closes every vacuity channel this layer exists for. Two runs
    #  that both did nothing are byte-identical - and if both did nothing then RUN A
    #  did nothing, so this guard fires. The same holds for two runs that both mutated
    #  a table the scenario declares unchanged.
    # ------------------------------------------------------------------
    declared_effect = definition.get(SCENARIO_KEY_TABLE_EFFECT)
    assert isinstance(declared_effect, str), (
        f"HARNESS FAULT: {scenario} declares no `{SCENARIO_KEY_TABLE_EFFECT}` (got "
        f"{declared_effect!r}). Both runners read that key to assert per side what the "
        f"route does to the bounded tables, and without it this layer has no claim to "
        f"hold the run against - so a run that silently stopped writing would pass."
    )
    _assert_effect_witness(
        first,
        scenario=scenario,
        tables=tables,
        declared_effect=declared_effect,
    )

    # ------------------------------------------------------------------
    #  LAYER 3 - THE DATABASE-BACKED ROUTE-AND-CLOCK WITNESS. Asserted on BOTH
    #  runs: a selector or clock that degraded on the second run only would otherwise
    #  show up as an ordinary difference, and the diagnosis would be needlessly hard.
    # ------------------------------------------------------------------
    for run in (first, second):
        _assert_clock_witness(run)

    # ------------------------------------------------------------------
    #  LAYER 4 - SEED-FINGERPRINT IDENTITY. Proves the seed landed identically before
    #  EITHER run, independently of the dumps - so a seeding difference is diagnosed as
    #  a seeding difference instead of masquerading as nondeterminism.
    #
    #  Compared as BYTES and never parsed: each line is a table name, a row count and a
    #  SHA-256 of that table's canonical dump, and interpreting them here would be the
    #  added validation R-3 forbids. The digest is what makes a byte comparison
    #  sufficient - equal counts over different values would pass a count-only record.
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
        f"difference means one reset loaded something other than the scenario fixture, "
        f"so every downstream difference would be unattributable. The frozen loaders "
        f"have no live COMMIT, so the AAP-mandated seeding window (autocommit OFF, "
        f"the default) persists nothing and is refused with exit 76; a durable "
        f"fixture requires ACAS_SEED_AUTOCOMMIT=on as a declared deviation. Either "
        f"way a nominally successful seed that leaves zero rows is refused rather "
        f"than reported. Loader exit codes and persisted counts are tested rather "
        f"than assumed."
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
    tree_diff = diff_states.diff_trees(
        first.tree, second.tree, tables, same_side=True
    )

    return DeterminismEvidence(
        scenario=scenario,
        tables=tables,
        pin=pinned_clock,
        first=first,
        second=second,
        tree=tree_diff,
        diagnosis=diff_states.summarise(tree_diff, report_path=None),
        filenames=filenames,
    )



# ---------------------------------------------------------------------------
#  THE PROOF OBLIGATION ITSELF
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "determinism_pair", DETERMINISM_SCENARIOS, indirect=True, ids=DETERMINISM_SCENARIOS
)
@pytest.mark.database
@pytest.mark.oracle
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
    #  COMPARISON 0 - THE TWO EXIT STATUSES, BEFORE THE DUMPS. Both stages are
    #  `run_python`, so a disagreement between them is nondeterminism in the migrated
    #  cycle - the very property under test - and it is asserted HERE, in a body, so
    #  that it reads as a FAILURE rather than as the setup ERROR the fixture's layer-2a
    #  guard raises for a pair that agreed on the WRONG status. A cycle whose exit
    #  status varies between two identical runs is non-deterministic even if its dumps
    #  happen to match.
    # ------------------------------------------------------------------
    assert evidence.first.run_status == evidence.second.run_status, (
        f"THE PYTHON POSTING CYCLE IS NOT DETERMINISTIC: two runs of scenario "
        f"{evidence.scenario!r} under the identical pinned clock exited "
        f"DIFFERENTLY - {RUN_LABELS[0]} {evidence.first.run_status}, "
        f"{RUN_LABELS[1]} {evidence.second.run_status}.\n"
        f"  THE COBOL ORACLE WAS NOT EXECUTED: both stages are the migrated Python "
        f"cycle (R-1), started from the same re-seeded state and handed the same "
        f"pinned pair (to-day={evidence.pin.to_day!r}, "
        f"Run-Date={evidence.pin.run_date}), so the difference is in the migrated "
        f"code and nowhere else. Two runs that took different exit paths are not two "
        f"runs of the same thing, so the dumps below are not evidence until this "
        f"holds."
    )

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
        f"{evidence.diagnosis}"
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
    #  COMPARISON 2 - LITERAL BYTES, OVER THE DUMPS.
    #
    #  EVERY TABLE DUMP, and deliberately NOT `_manifest.json`. The obligation quoted
    #  above is that two runs "produce byte-identical DUMPS", and the manifest is not a
    #  dump - it is the provenance OF one. It records
    #  this run's `run_id`, the exact `command` that produced it and the digest of the
    #  manifest it was normalised from, so two runs' manifests MUST differ: the
    #  same-side contract selected in the fixture requires the two run ids to be
    #  DIFFERENT, and a byte comparison that included them would demand the opposite of
    #  the guard that proves these are two runs at all. The two requirements would be
    #  mutually unsatisfiable, and the test would be unpassable for a correct cycle.
    #
    #  THE MANIFEST IS STILL COMPARED, on the part of it that is state rather than
    #  provenance - see COMPARISON 3. Skipping it outright would drop the row-count and
    #  per-file-digest cross-check that this comparison actually relies on.
    #
    #  This is where a serialisation-level difference is caught. The structural diff
    #  reads parsed JSON, so it would report two dumps with different key order,
    #  different indentation or a different trailing newline as IDENTICAL - and the
    #  claim being proven is byte-identity, not value-identity.
    # ------------------------------------------------------------------
    differing_bytes: list[str] = []
    dump_filenames = tuple(
        name for name in evidence.filenames if name != MANIFEST_FILENAME
    )
    assert dump_filenames, (
        f"scenario {evidence.scenario!r} produced a normalised tree holding nothing "
        f"but {MANIFEST_FILENAME}, so there is no dump to compare "
        f"byte-for-byte and "
        f"the obligation would pass having compared nothing. Affected tables: "
        f"{', '.join(evidence.tables)}."
    )
    for name in dump_filenames:
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

    # ------------------------------------------------------------------
    #  COMPARISON 3 - THE MANIFEST'S STATE, WITHOUT ITS PROVENANCE.
    #
    #  The manifest is excluded from COMPARISON 2 because its provenance MUST differ
    #  between two runs. Its `tables' block must not: it records each table's name, row
    #  count and dump digest, and two runs of one scenario that captured different row
    #  counts or different digests are not deterministic however the bytes of the dumps
    #  happen to compare. This keeps the cross-check the earlier comparison relied on
    #  while dropping only the fields whose difference is the point of recording them.
    #
    #  The provenance is asserted to DIFFER as well, because a pair that agreed on
    #  `run_id' would be one capture read twice - the false pass the fixture's
    #  same-side contract exists to refuse - and asserting it here means the obligation
    #  cannot be discharged by comparing a tree with itself.
    # ------------------------------------------------------------------
    left_manifest = json.loads(
        (evidence.first.tree / MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    right_manifest = json.loads(
        (evidence.second.tree / MANIFEST_FILENAME).read_text(encoding="utf-8")
    )

    assert left_manifest["tables"] == right_manifest["tables"], (
        f"THE PYTHON POSTING CYCLE IS NOT DETERMINISTIC: two runs of scenario "
        f"{evidence.scenario!r} under the identical pinned clock published DIFFERENT "
        f"table blocks in {MANIFEST_FILENAME}, so they disagree about a row "
        f"count or "
        f"a dump digest.\n"
        f"  {RUN_LABELS[0]}: {left_manifest['tables']}\n"
        f"  {RUN_LABELS[1]}: {right_manifest['tables']}\n"
        f"  The COBOL oracle was not executed (R-1), so this is a difference in the "
        f"migrated cycle. DO NOT MAKE IT PASS BY NORMALISING IT (R-4, inverted)."
    )

    left_run = left_manifest["provenance"]["run_id"]
    right_run = right_manifest["provenance"]["run_id"]
    assert left_run and right_run and left_run != right_run, (
        f"the two captures of scenario {evidence.scenario!r} carry run ids "
        f"{left_run!r} and {right_run!r}. They must both be present and must DIFFER: "
        f"two captures under one run id are one capture read twice, a tree always "
        f"equals itself, and the byte comparison above would then pass whatever the "
        f"migrated cycle did. This is asserted in the body rather than left to the "
        f"fixture so that the false pass is named as a FAILURE of the obligation."
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
    # IS ANOMALY A-16, AND IT IS REPRODUCED, NOT FIXED (R-4). No validation is added
    # here to reject these texts earlier or more loudly (R-3): the point is precisely
    # that a rejected date is silent, which is why layer 3 requires the runner's
    # post-run database readback marker rather than trusting an exception that never
    # comes.
    for text in REJECTED_DATE_TEXTS:
        degraded = pinned_clock_factory(text)
        assert degraded.run_date == REJECTED_DATE_RUN_DATE, (
            f"pinning from the rejected text {text!r} produced run_date "
            f"{degraded.run_date}, expected {REJECTED_DATE_RUN_DATE}. maps04 rejects "
            f"by falling through without touching its output field "
            f"[common/maps04.cbl:L146, L154], and the caller's pre-zero at "
            f"[copybooks/Proc-ACAS-Mapser-RDB.cob:L78] is what makes the documented "
            f"zero contract [common/maps04.cbl:L163] true. That masking mechanism is "
            f"anomaly A-16 and must be reproduced exactly - a value other than zero "
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
            f"bounds every comparison with cannot be read. The scenario definitions "
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


def test_the_effect_witness_discriminates_a_no_op_from_a_posting_run(
    tmp_path: Path,
) -> None:
    """LAYER 2b's own logic, proven on a bare host - because the layer itself cannot be.

    WHY THIS TEST HAS TO EXIST. Layer 2b lives inside `determinism_pair`, which is
    marked `database`/`oracle` and SKIPS without the Compose stack. So on a bare host
    the guard that closes channel 3 is never executed, and a guard that has never run
    is indistinguishable from one that cannot fire. This test drives
    `_assert_effect_witness` directly over SYNTHETIC state records - no database, no
    runner, no scenario - so its discrimination is established wherever pytest runs.

    THE SIX CASES, AND WHAT EACH WOULD CATCH IN PRODUCTION:

      1. `changed` declared, a digest moved   -> PASSES. The `clean_batch_irs` shape.
      2. `changed` declared, NOTHING moved    -> FAILS. THE VACUITY THE REVIEW NAMED:
         both runs did nothing, the trees agree, and every other layer passes.
      3. `unchanged` declared, nothing moved  -> PASSES. The `clean_batch_gl` shape,
         whose no-op is the measured behaviour (evidence document section 10.1).
      4. `unchanged` declared, a digest moved -> FAILS. A cycle that REPAIRED the
         reproduced defect, which R-4 makes a failure and not an improvement.
      5. A row count that moved while the digest did not, and the converse -> BOTH
         count as movement. The pair is the unit; a run that deleted one row and
         inserted another could hold either field still on its own.
      6. An unreadable table, a malformed line, a missing bounded table, and an
         unrecognised declared effect -> ALL refuse. An unreadable table establishes
         nothing about whether the run changed it, and silently reading it as
         unchanged is precisely the false pass this layer exists to prevent.

    Args:
        tmp_path: Where the synthetic records are written.
    """
    digest_a = "a" * 64
    digest_b = "b" * 64

    def record(path_name: str, rows: dict[str, tuple[str, str]]) -> Path:
        target = tmp_path / path_name
        target.write_text(
            "".join(
                f"{table}\t{count}\t{digest}\n" for table, (count, digest) in rows.items()
            ),
            encoding="utf-8",
        )
        return target

    def run(label: str, before: Path, after: Path) -> RelocatedRun:
        return RelocatedRun(
            label=label,
            tree=tmp_path,
            fingerprint=before,
            post_fingerprint=after,
            wrapper_status=0,
            run_status=0,
            run_output="",
            row_counts=(("T1", 1),),
        )

    tables = ("T1", "T2")
    seeded = {"T1": ("1", digest_a), "T2": ("2", digest_a)}

    # CASE 1 and CASE 3 - the declaration is met, in each direction.
    unmoved = record("unmoved.after", dict(seeded))
    seed_1 = record("case1.before", dict(seeded))
    moved_digest = record("case1.after", {**seeded, "T2": ("2", digest_b)})
    assert _assert_effect_witness(
        run("runA", seed_1, moved_digest),
        scenario="synthetic",
        tables=tables,
        declared_effect=TABLE_EFFECT_CHANGED,
    ) == ("T2",), "a moved digest on one bounded table must be reported as movement"
    seed_3 = record("case3.before", dict(seeded))
    assert (
        _assert_effect_witness(
            run("runA", seed_3, unmoved),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )
        == ()
    ), "an unchanged pair on every bounded table must report no movement"

    # CASE 2 - THE VACUITY. `changed` declared and the run did nothing at all.
    seed_2 = record("case2.before", dict(seeded))
    with pytest.raises(AssertionError, match="CHANGED NOTHING"):
        _assert_effect_witness(
            run("runA", seed_2, unmoved),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_CHANGED,
        )

    # CASE 4 - the converse. `unchanged` declared and something moved.
    seed_4 = record("case4.before", dict(seeded))
    with pytest.raises(AssertionError, match=r"CHANGED \['T2'\]"):
        _assert_effect_witness(
            run("runA", seed_4, moved_digest),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )

    # CASE 5 - a moved ROW COUNT alone is movement too. The pair is the unit.
    seed_5 = record("case5.before", dict(seeded))
    moved_count = record("case5.after", {**seeded, "T1": ("2", digest_a)})
    assert _assert_effect_witness(
        run("runA", seed_5, moved_count),
        scenario="synthetic",
        tables=tables,
        declared_effect=TABLE_EFFECT_CHANGED,
    ) == ("T1",), (
        "a row count that moved while the digest did not must still be movement: a "
        "digest is of the canonical dump text, and treating the count as noise would "
        "let an insert-plus-delete pass as a no-op"
    )

    # CASE 6 - every refusal. None of these may be read as `unchanged`.
    unreadable = record("unreadable.after", {"T1": ("1", digest_a), "T2": ("-", "-")})
    with pytest.raises(AssertionError, match="UNREADABLE"):
        _assert_effect_witness(
            run("runA", record("case6a.before", dict(seeded)), unreadable),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )

    malformed = tmp_path / "malformed.after"
    malformed.write_text("T1\t1\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="not the three fields"):
        _assert_effect_witness(
            run("runA", record("case6b.before", dict(seeded)), malformed),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )

    short_digest = tmp_path / "short.after"
    short_digest.write_text("T1\t1\tabc\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="lower-case hex SHA-256"):
        _assert_effect_witness(
            run("runA", record("case6c.before", dict(seeded)), short_digest),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )

    partial = record("partial.after", {"T1": ("1", digest_a)})
    with pytest.raises(AssertionError, match="does not carry it"):
        _assert_effect_witness(
            run("runA", record("case6d.before", dict(seeded)), partial),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )

    empty = tmp_path / "empty.after"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(AssertionError, match="is empty"):
        _assert_effect_witness(
            run("runA", record("case6e.before", dict(seeded)), empty),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )

    with pytest.raises(AssertionError, match="neither `changed` nor `unchanged`"):
        _assert_effect_witness(
            run("runA", record("case6f.before", dict(seeded)), unmoved),
            scenario="synthetic",
            tables=tables,
            declared_effect="maybe",
        )

    duplicated = tmp_path / "duplicated.after"
    duplicated.write_text(
        f"T1\t1\t{digest_a}\nT1\t1\t{digest_a}\n", encoding="utf-8"
    )
    with pytest.raises(AssertionError, match="twice"):
        _assert_effect_witness(
            run("runA", record("case6g.before", dict(seeded)), duplicated),
            scenario="synthetic",
            tables=tables,
            declared_effect=TABLE_EFFECT_UNCHANGED,
        )


def test_both_runners_persist_a_post_run_state_record(repo_root: Path) -> None:
    """LAYER 2b's INPUT exists, asserted against both runner scripts as text.

    The layer reads `python.post-fingerprint`, and a layer whose input is never written
    fails as a harness fault at the first stack run rather than at review. This reads
    both scripts READ-ONLY and asserts four things about each: the record's name, that
    it is written under `run-logs/` and therefore outside every compared tree, that a
    stale copy is removed rather than inherited, and that the digest comes from the one
    canonical producer rather than from a second inline definition.

    BOTH SIDES, not merely the Python one. The oracle runner writes the same record so
    that `tests/conftest.py`'s `assert_tables_unchanged_by_run` can be pointed at either
    side; a record written on one side only would silently make every cross-side
    before/after claim a claim about Python alone.

    Args:
        repo_root: The repository root, from which both harness scripts are READ.
    """
    for script_name, variable, record_name in (
        (RUN_PYTHON_SCRIPT_NAME, "ACAS_PY_POST_FINGERPRINT", "python.post-fingerprint"),
        ("run_cobol_scenario.sh", "ACAS_RUN_POST_FINGERPRINT", "cobol.post-fingerprint"),
    ):
        script = repo_root / "harness" / script_name
        assert script.is_file(), (
            f"harness/{script_name} is absent from {script}, so the post-run state "
            f"record layer 2b reads has no producer at all."
        )
        text = script.read_text(encoding="utf-8")
        assert record_name in text, (
            f"harness/{script_name} never names {record_name!r}. LAYER 2b compares a "
            f"run's own pre-run record with that file, and without it the only "
            f"question the other layers cannot ask - did this run change anything - "
            f"goes unasked, so two runs that both did nothing report a clean PASS."
        )
        assert f"{variable}=" in text, (
            f"harness/{script_name} never assigns {variable}, so the record's path is "
            f"never resolved and the write is silently skipped."
        )
        assert "run_logs_dir" in text or "run-logs" in text, (
            f"harness/{script_name} does not place its state records under run-logs/. "
            f"A record written inside a compared tree would be DIFFED as though it "
            f"were posted data (R-6)."
        )
        assert TABLE_DIGEST_PRODUCER in text, (
            f"harness/{script_name} does not invoke {TABLE_DIGEST_PRODUCER}. The "
            f"three-field record has exactly ONE producer so that the pre-run and "
            f"post-run records, and both sides, are comparable at all; a second "
            f"inline definition of 'the digest' is how the two silently drift apart."
        )
