# ACAS posting-cycle scenario diff evidence

This document records the **empty-diff evidence per mandated scenario** for the
migration of the ACAS posting cycle from COBOL to Python 3.12. It is the
evidence register for the acceptance criterion the Agent Action Plan (AAP)
states in §0.8.5, quoted here verbatim because every verdict below is measured
against it and nothing else:

> "seed identically through the maintainer's load programs, run the compiled
> cycle, dump the affected tables ordering-normalised, reset, run the Python
> cycle, dump again — and the diff **must be empty**."

The same section fixes how a failure is to be read, and this clause is what
makes the register worth keeping at all:

> "a non-empty diff is always a real behavioral difference and never an artefact
> of the comparison."

AAP §0.1.1 gives the operational definition of "exact" that the whole
engagement rests on:

> "the ordering-normalized diff of affected database tables after a Python run
> versus a COBOL run against an identical seed must be empty."

And §0.8.5 states the determinism criterion separately:

> "Two runs of the same scenario under the same pinned clock produce
> byte-identical dumps, proven by
> `tests/determinism/test_two_runs_byte_identical.py`."

This file is not a statement of intended behaviour and contains no prediction.
Every line marked as observed was produced by driving the compiled COBOL cycle
and the Python cycle from the same loader-built seed, normalising both captures,
and requiring an empty state diff. Where nothing was observed, the entry says
so in those words.

---

## 0. EVIDENCE STATUS — READ THIS BEFORE ANY OTHER SECTION

### 0.0 The verdict, in one place

| | |
|---|---|
| **Acceptance criterion** (AAP §0.1.1, §0.8.5) | an empty ordering-normalised diff of the affected tables, Python run versus **frozen** compiled run, from an identical seed |
| **Verdict** | **NOT MET, and not meetable from this checkout.** Nothing below is a frozen-parity claim |
| **Obstacle 1** | the frozen sources **do not compile**: `copybooks/ACAS-SQLstate-error-list.cob` is absent and 22 of the 28 generated `common/*MT.cbl` bridges `COPY` it. Re-measured **2026-08-07** and again **2026-08-08** on the code as committed: `build_oracle.sh` with no flags, byte-for-byte the checkout, **exit 74**, one `ACAS-SQLstate-error-list.cob: No such file or directory` per affected bridge, 22 bridges named, and **no attestation written** — so `reset_db.sh` then has nothing to verify and stops at 77 |
| **Obstacle 2** | the empty diffs below were produced against a **disclosed-transformed diagnostic** oracle — 41 transformed paths, 40 of them repairs to executable logic. Agreement with a repaired specification is not evidence about the frozen one |
| **Obstacle 3** | an **AAP-conformant seed cannot exist**: the AAP mandates autocommit OFF for seeding, no frozen loader reaches a `COMMIT`, so a fresh session sees zero rows. Re-measured 2026-08-07 in both windows — OFF: exit **76**, 0 rows in all 7 seeded tables; ON: exit **0**, 8 rows across 7 tables |
| **What IS established** | the ten-stage protocol runs end to end; the Python cycle agrees table-for-table with the diagnostic oracle on all eight committed scenarios; two Python runs under one pinned clock are byte-identical; the arithmetic, dictionary and traceability deliverables stand on their own. **Re-driven in full on 2026-08-08 from the committed tree by the documented commands** — all eight scenarios, all ten stages, stage 10 exit 0 with 0 bytes of stdout, 22 tables and 0 differences each, and the two stack-bound tiers at 8 and 106 passed with nothing errored or skipped (§8, §9.2, §12) |
| **Enforced, not merely disclosed** | `harness/reset_db.sh` exits **77 — EVIDENCE UNAVAILABLE** with no attested oracle — **re-measured 2026-08-08 on the shipped arrangement: exit 77 before a single table was dropped and before any connection was opened, "The frozen schema was NOT applied, so the database is untouched by this run"** — and against a transformed oracle it discloses **NO PARITY CLAIM** on every exit path that succeeds; `seed.sh` exits **76** rather than certifying a comparison of two empty databases. The 2026-08-07 measurement of that gate was taken through a `run_parity.sh` driver; the gate lives in `reset_db.sh`, which is the stage that destroys the database, so the refusal lands before the destruction rather than before the stage that would have caused it |
| **What a human must do** | obtain `copybooks/ACAS-SQLstate-error-list.cob` from the maintainer (§0.2), and settle the seeding authorisation (§0.3). Both are outside an implementing agent's authority — AAP §0.8.1 makes any diff touching `copybooks/*.cob` a defect in the migration, so the member may not be written here even from an authentic copy |

**Parity against the frozen COBOL specification is NOT established by this
document, and cannot presently be established from this repository.** Every empty
diff recorded below is a real measurement, and none of them is a parity claim
against the frozen checkout. Three independent, measured obstacles stand in the way,
and all three are now enforced by the tooling rather than left to a reader's diligence.

### 0.1 The three obstacles, each re-measured

**Obstacle 1 — the frozen oracle does not compile.** `harness/build_oracle.sh`
defaults to a zero-transformation build of the frozen sources. Measured on
2026-08-07, that build **fails with exit 74**: 22 of the 28 generated
`common/*MT.cbl` bridges `COPY "ACAS-SQLstate-error-list.cob"`, and that member is
absent from the checkout and from `presql2-latest.zip` alike. It is not fabricated,
because inventing a frozen source would breach R-3 and R-4; it must be supplied by
the maintainer. No attestation is written, and `harness/reset_db.sh` reports exit
**77 — EVIDENCE UNAVAILABLE**, a status deliberately distinct from the ones meaning
the two states differ. See README §8.7.

**Re-measured 2026-08-07, independently of the run that first recorded it, and with
the live diagnostic build left intact** — the four rows below are a **report of an
observed run rather than a retained artefact**, in this register's own sense (see
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) §17), and every one of them is
reproducible by the command in its own row — the verification build was directed at a
container-local `ACAS_BUILD` so that neither the existing build tree nor the retained
per-scenario captures on the `out` volume were disturbed. Observed, in order:

| Step | Observation |
|---|---|
| `build_oracle.sh` with no flags, `ACAS_BUILD` outside the live tree | announces *"frozen oracle: no source transformation applied; the build copy is byte-for-byte the checkout"* and *"verified by MEASUREMENT: zero source transformations"* |
| the same run's compile stage | **44 diagnostic lines** naming **22 distinct** `*MT.cbl` bridges, each `ACAS-SQLstate-error-list.cob: No such file or directory` — `analMT`, `auditMT`, `delfolioMT`, `deliveryMT`, `dfltMT`, `finalMT`, `glbatchMT`, `glpostingMT`, `irsdfltMT`, `irsfinalMT`, `irsnominalMT`, `irspostingMT`, `nominalMT`, `otm3MT`, `otm5MT`, `paymentsMT`, `sldelinvnosMT`, `slpostingMT`, `stockMT`, `sys4MT`, `systemMT`, `valueMT` |
| exit status | **74**, with *"FATAL: comp-common.sh produced 22 fatal diagnostic line(s)"* — the frozen script itself exits 0 regardless `[common/comp-common.sh:L59]`, `[comp-all.sh:L44-L45]`, which is why the scan and not the status is what detects the failure |
| `reset_db.sh` against an unattested build | **exit 77**, *"ORACLE UNAVAILABLE: no provenance attestation exists"*, *"THIS IS NOT A BEHAVIOURAL DIFFERENCE. Nothing was compared"*, then *"The frozen schema was NOT applied, so the database is untouched by this run"* — refused inside stage 1's own preconditions, before the first `DROP` and before any connection. **Re-measured 2026-08-08** on the shipped arrangement, with the gate in this stage; the 2026-08-07 measurement of the same refusal was made through a `run_parity.sh` driver |

**Why this cannot be closed from inside the repository.** The member is a frozen
source, and AAP §0.8.1 states that any diff touching `copybooks/*.cob` **is a defect
in the migration, regardless of how harmless it appears**. So even an authentic copy
may not be committed by an implementing agent: writing one here would be the
migration modifying the specification it is being measured against. It is a
maintainer action, and the one action that lifts the largest number of open items in
this project (see [`ambiguity-resolutions.md`](ambiguity-resolutions.md) §14.5, where
four class-A questions wait on exactly this).

**Obstacle 2 — the runs below used a transformed oracle.** They were produced
before the frozen build became the default, against a build carrying **41**
transformed paths. One of those (the missing-member shim) is measured
behaviour-neutral: translating `glpostingMT.cbl` with `cobc -C` under the
comment-only shim, a zero-byte member, and different comment text yields
byte-identical C, and the `COPY` site sits in the `IDENTIFICATION DIVISION` where
only comments are legal. The other **40** are not neutral — they repair `IF` scope,
connection lifetime, credential propagation and stale reply pairs, all executable
logic. A build carrying them has repaired the specification, so agreement with it
cannot show that the migration reproduces the frozen one.
`harness/reset_db.sh` now **refuses** such a build with exit 77 unless
`--accept-transformed-oracle` is given, and then discloses **NO PARITY CLAIM** on every
exit path — *"an empty diff drawn against this oracle would say the migrated cycle
matches a PATCHED system"* — while `tests/conftest.py` reports the oracle tiers
UNAVAILABLE rather than passing them unless `ACAS_ACCEPT_TRANSFORMED_ORACLE=1` asks
for the same diagnosis. No driver publishes an
`identical-against-diagnostic-oracle` claim string, because no driver exists, so the
disclosure — not a verdict token — is what records the distinction. See README §8.10.

**Obstacle 3 — an AAP-conformant seed cannot exist, and that is now a proof rather
than a pending task.** The seeding window defaults to the mode the AAP mandates
(autocommit **off**, §0.2.1.1/§0.4.1.7/§0.5.2). Measured under that default,
`clean_batch_gl` stage 1 exits **76**: seven loaders run, all return success, and all
seven seeded tables read **zero rows** — the frozen no-COMMIT defect, reproduced and
refused rather than papered over. The runs below were therefore also produced under an
explicitly declared seeding deviation (`ACAS_SEED_AUTOCOMMIT=on`), the only mode
measured to leave a durable row (8 rows across 7 tables). See README §9.4.

**Re-measured 2026-08-07, both windows, one session, shipped default first** — again a
report of an observed run rather than a retained artefact, reproducible by setting the
variable and re-running stage 1:

| Window | Loaders | Rows a FRESH session sees | `reset_db.sh` exit |
|---|---|---|---|
| `off` — the shipped default, AAP-literal | seven, all reporting success | **0** in every one of the seven seeded tables | **76** |
| `on` — the declared deviation | the same seven, same success | `SYSTEM-REC` 1, `SYSTOT-REC` 1, `GLBATCH-REC` 1, `GLLEDGER-REC` 4, `GLPOSTING-REC` 1 = **8 rows across 7 tables** | **0** |

**Why it is a proof.** Three facts compose, and the migration may change none of them:
the AAP mandates OFF for seeding and is the frozen specification of this work; **no
frozen loader commits** — zero live `perform aa020-Rollback` / `perform aa030-Commit`
sites across all 28 `common/*LD.cbl`, the sole `aa030-Commit` reference commented out
at `[common/irsdfltLD.cbl:L437]`; and MariaDB discards an uncommitted session at
disconnect. Therefore zero rows persist, necessarily. Issuing the missing `COMMIT` on
the loaders' behalf would repair the very defect this engagement exists to reproduce
(R-4), and the loaders are frozen. Two further checks in the same session rule the
shims out as a cause: the **build copy's** loaders carry zero live commit or rollback
performs too, and no entry in `build_oracle.sh`'s 41-path transform register touches a
transaction statement. So the seeding outcome is a property of the frozen loaders.

**What a human must decide — exactly one of two things, neither available to an
implementing agent:** either **the maintainer** supplies loaders that reach their own
`COMMIT`, fixing the frozen defect at its source, by the only party entitled to; or
**the project owner** authorises the `ACAS_SEED_AUTOCOMMIT=on` deviation in writing,
amending the premise AAP §0.5.2 rests on — a comment banner at
`[common/glbatchLD.cbl:L9-L13]` that cannot set the session mode, since the vendored C
interface exposes `MySQL_commit` and `MySQL_rollback` and no `MySQL_autocommit` at all.
Full argument and evidence: [`ambiguity-resolutions.md`](ambiguity-resolutions.md)
[`Q-10`](ambiguity-resolutions.md#q-10).

### 0.2 What the sections below therefore do and do not establish

| Claim | Status |
|---|---|
| The protocol executes end to end — ten stages, both cycles, dump, normalise, diff | **ESTABLISHED.** Observed, repeatedly, and reproducible |
| The Python cycle agrees, table for table, with a **disclosed-transformed diagnostic** oracle on all eight committed scenarios | **ESTABLISHED as measured.** This is what the empty diffs below are |
| The Python cycle reproduces the **frozen** COBOL specification | **NOT ESTABLISHED.** The frozen specification does not compile (Obstacle 1) |
| Two Python runs under one pinned clock are byte-identical | **ESTABLISHED.** It depends on neither obstacle — see §12 |
| A seeded oracle state can be produced in the AAP-mandated configuration | **PROVEN IMPOSSIBLE** on this checkout — §0.1's Obstacle 3 gives the three-fact proof, twice measured. Not a pending task but a decision awaiting a human (§0.3, Action 2) |

### 0.3 What a human must do to close this — two actions, in this order

**Action 1 (unblocks Obstacle 1, and with it Obstacle 2).** Obtain
`copybooks/ACAS-SQLstate-error-list.cob` from the maintainer and commit it to the
frozen tree. **An implementing agent may not do this**: AAP §0.8.1 makes any diff
touching `copybooks/*.cob` a defect in the migration regardless of how harmless it
appears, so the member must arrive as a maintainer commit rather than as migration
work — and it must not be reconstructed, however confidently, since the only thing
known about its contents is that they are comments (the `COPY` site is in the
`IDENTIFICATION DIVISION`). Then `harness/build_oracle.sh` with no flags either
succeeds — in which case re-run §15, every row below becomes a parity claim against
the frozen specification, and the four class-A questions in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) §14.5 become experiments that
can simply be run — or it fails for a new reason that is then the next finding.
**Nothing in this repository should be changed to make it pass.**

**Action 2 (unblocks Obstacle 3).** Settle the seeding authorisation, as §0.1's
Obstacle 3 sets out: either the maintainer supplies loaders that reach their own
`COMMIT`, or the project owner authorises `ACAS_SEED_AUTOCOMMIT=on` in writing as an
amendment to AAP §0.5.2's premise. Both are decisions rather than engineering, and
until one is taken the durable fixture remains a declared deviation whose results are
labelled as such.

**Why the order matters.** Action 2 alone changes nothing about parity: a durable seed
feeds a comparison that still has no frozen oracle to compare against. Action 1 alone
leaves the protocol able to build the specification but unable to seed it in the
mandated mode. Both are required for a frozen-parity result, which is why neither is
described here as progress toward one.

The measurements below are retained verbatim rather than deleted, because they are
observations and deleting them would destroy evidence. Read them as what they are.

## 1. Rules provenance

**There is no user rules document for this project.** The Agent Action Plan
states it directly in §0.7.1: *"No separate user rules document was provided for
this project."*

Do not go looking for a rules file; there is none, nothing has been invented to
fill the gap, and enterprise-standard best practice applies wherever the Agent
Action Plan is silent. [`ambiguity-resolutions.md`](ambiguity-resolutions.md) §1
carries the full arbitration of this point.

The six binding rules **R-1 … R-6** are nevertheless real and are treated as
binding. They live in the **Agent Action Plan, §0.7.2**, and are retrievable via
**`review_prompt`** — *not* via `review_rules`. AAP §0.7.1 is explicit that
"downstream execution agents that need the exact wording must read it there."

AAP §0.7.4 **C-5** records why both facts must be stated together rather than
either one alone:

> "claiming a rules document exists when it does not would send downstream
> agents to an empty source. Recording both facts is the only resolution that
> misleads no one."

### 1.1 The rules that govern this document

**R-6 — Compiled behavior is the tie-breaker** is the primary owner of this
register:

> "Where a semantic question is ambiguous, the compiled program's observed
> behavior decides it, and each such resolution must be documented rather than
> settled silently."

Two obligations follow, and they are symmetric. A result that was **not**
observed must never be presented as observed. A result that **was** observed
must never be suppressed, because suppressing it is precisely "settling it
silently". Section 3 records how that second obligation was discharged here.

**R-1 — No COBOL at runtime.**

> "The Python implementation must not execute, embed, or shell out to the COBOL
> programs. COBOL is the specification for the migration, not a runtime
> dependency of the result. The shipped artifact must run on a host with no
> COBOL compiler and no COBOL runtime present."

The compiled cycle is driven only by `harness/run_cobol_scenario.sh`, out of
process. AAP §0.7.4 **C-1**:

> "compiled COBOL is confined to `harness/`, invoked only as an out-of-process
> comparison and seeding utility by the test suites, and never appears on any
> import path or code path of `acas_posting/`."

And AAP §0.3.1: "there is no import path from `acas_posting` to `harness`."
Structurally enforced: `harness/` carries no `__init__.py` and `pyproject.toml`
packages `acas_posting*` only. Verified on the authoring host: `cobc` is absent
from the host itself; the compiler exists only inside the harness container
image.

**R-2 — Zero binary floating point.**

> "No accounting value may pass through a binary floating-point type at any
> point — not in computation, not in storage, not in transport."

Enforced mechanically rather than by convention. `DECIMAL` values travel through
every dump as canonical JSON strings, integers stay integers, and a `float`
anywhere in a dump makes the comparison exit **2** rather than pass. The frozen
schema contains zero `FLOAT`, `DOUBLE` or `REAL` columns. AAP §0.5.1:

> "No `pandas` and no `numpy` … This exclusion is absolute, including for the
> harness dump comparison, which uses ordered row sequences rather than
> dataframes."

**R-3 — No new validations, fields or schema changes; no concurrency.**

> "The migration may not add validation logic, add fields, or alter the database
> schema, and must not introduce concurrent execution."

`harness/reset_db.sh` re-applies `mysql/ACASDB.sql` verbatim and adds nothing.
Exactly one scenario runs at a time. AAP §0.7.4 **C-2** is the licence for this
document existing at all:

> "R-3 constrains the database, not the repository. Describing a schema in a
> committed artifact is orthogonal to altering it."

**R-4 — Legacy anomalies reproduced, never fixed.**

> "Defects present in the compiled behavior are part of the specification. A
> defect reproduced is a success; a defect fixed is a failure."

Several scenarios exist precisely to lock a defect in place, and each names the
anomaly it pins by id in [`anomaly-log.md`](anomaly-log.md). AAP §0.7.4 **C-3**:

> "Any 'improvement' destroys that property and cannot be detected as a
> regression by any downstream consumer, because there is no correct answer
> other than what the old system produced."

**R-5 — Full traceability.**

> "Every program must map to a module, every paragraph to a function, and every
> field to a data-dictionary entry, and the mapping must be recorded as a
> document rather than left implicit in the code."

Each scenario entry names the programs and Python modules it exercises and
cross-references [`traceability.md`](traceability.md) rather than restating it.

### 1.2 The freeze

AAP §0.8.1: "Any diff touching `common/*.cbl`, `common/*.scb`,
`copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`,
`irs/*.cbl` or `mysql/ACASDB.sql` is a defect in the migration, regardless of
how harmless it appears." Those files were read for this document and not
edited. The maintainer's `README.TXT`, `README`, `README.SVN`,
`README.nightly`, `Changelog` and `ACAS-Manuals/` are likewise never edited;
they are quoted and cross-referenced instead.

Build-only compatibility shims live solely under `$ACAS_BUILD` and never in the
checkout — see §5.4.

**AND THE ORACLE EVERY VERDICT BELOW WAS RENDERED AGAINST IS A
DISCLOSED-TRANSFORMED ONE.** `harness/build_oracle.sh` edits the **build copy** of
**41** frozen sources, and until this was disclosed the attestation published
`overrides-used=no` and nothing else, so an empty diff read as parity with the
untouched checkout. It is not. Every empty diff in this register is parity between
the migrated cycle and a compiled oracle whose sources differ from the checkout in
41 declared places, each one listed in `$ACAS_BUILD/oracle-attestation.txt` with its
frozen digest, its build digest and its reason, and each one a connectivity or `IF`-
scope repair without which the compiled cycle cannot reach MySQL at all — no
arithmetic statement, no `ROUNDED` site, no sort key, no control-total comparison and
no rejection path is touched. README §8.10 gives the four groups and the full
argument. The **checkout** is untouched: a `git diff` over the frozen paths is empty,
which is a different and weaker claim than the one this paragraph exists to correct.

## 2. Verdict vocabulary

Exactly four statuses are used in this register, and they are never blurred
into one another. Two qualifications attach to **every** use of the two `OBSERVED`
statuses, wherever they appear below, and are stated here once rather than repeated
per entry: the observation was made against the **disclosed-transformed DIAGNOSTIC
oracle** and never against the frozen specification (§0.1), and the artifacts it
produced live on the harness `out` volume outside the checkout (§9.3), so the status
is a **report of a run that was watched** rather than a retained repository artefact.
Neither status is a frozen-parity claim, and no reader should take one as one.

| Status | Meaning |
| --- | --- |
| **`EMPTY DIFF — OBSERVED`** | Two complete, attested normalised trees were compared and `harness/diff_states.py` returned **0** with **zero bytes** on stdout. This is the pass condition and the only one — against the diagnostic oracle, per the qualifications above. |
| **`NON-EMPTY DIFF — OBSERVED`** | The comparison returned **1**. A real behavioural difference. **No scenario in this register carries this status.** |
| **`HARNESS ERROR — COMPARISON NOT PERFORMED`** | The comparison returned **2**, or an earlier protocol stage failed. **Never** treated as parity. |
| **`PENDING — AWAITING ORACLE EXECUTION`** | Nothing was observed. Used for every claim this register does not have measured evidence for, and used without euphemism. |

A summary line is never a substitute for the exit code. Stage 10's own exit status is
the finding, and `harness/diff_states.py` prints *"identical"* only after returning 0
with zero bytes on stdout. Runs recorded here that were driven from one invocation
also carried a driver summary line and a `parity-result` file; both belonged to a
`run_parity.sh` that is not part of this tree, and `verdict.json` is the published
claim (§9.3).

## 3. The execution environment, and a recorded deviation from this file's brief

The authoring brief for this file was written on the premise — AAP §0.6.9 —
that "the authoring host lacks the COBOL compiler and container runtime", and it
therefore instructed that **every** diff result be recorded as
`PENDING — AWAITING ORACLE EXECUTION`, with the observed statuses reserved and
unused.

**That premise does not hold in the environment this file was actually written
in, and the difference was established by execution rather than by argument.**
Measured on the authoring host, and each fact re-checkable by the command named
beside it rather than by trusting a date:

- Docker Engine **29.7.0** is present, and the two-service harness stack
  (`harness/docker-compose.yml`) is running with MariaDB **10.11.7** healthy.
  — `docker version --format '{{.Server.Version}}'`
- `cobc` is **absent from the host**, exactly as R-1 requires. GnuCOBOL
  **3.2.0** exists only inside the harness builder image.
  — `command -v cobc` on the host returns nothing; `cobc --version` inside the
  builder service reports `cobc (GnuCOBOL) 3.2.0`
- The oracle **is built — and it is the DISCLOSED-TRANSFORMED DIAGNOSTIC build,
  never the frozen one** (§0.1: the frozen sources do not compile, and an unflagged
  `build_oracle.sh` exits **74**): 215 loadable modules, **29/29** `*MT` bridges,
  **28/28** loaders — `find /build -name '*.so' | wc -l`,
  `ls /build/common/*MT.so | wc -l` — and all **12** in-scope posting programs
  (`gl051`, `gl070`,
  `gl071`, `gl072`, `gl080`, `sl055`, `sl060`, `sl100`, `pl055`, `pl060`,
  `pl100`, `irs030`) and all **17** file handlers.

  On the bridge arithmetic, so the figures reconcile rather than appearing to
  disagree: the checkout holds **28** bridges of the migration's concern —
  **20** in scope and **8** out of scope — plus one test stub, which is why a
  build that compiles everything reports 29. The stub is out of scope and no
  scenario reaches it. On the table side the arithmetic is **22** in scope plus
  **11** out of scope for the **33** the frozen schema declares.
- The former global build blocker is cleared without touching the freeze — the
  missing `copybooks/ACAS-SQLstate-error-list.cob` is materialised as a
  comment-only shim under `$ACAS_BUILD/copybooks`, never in the checkout. See
  §10.1 of [`ambiguity-resolutions.md`](ambiguity-resolutions.md) for the
  reasoning and §8.7 of
  [`../../README-python-migration.md`](../../README-python-migration.md) for the
  operator's view. There is no "§5.4" in either document.
- All eight mandated scenarios were then driven through the complete protocol on
  **2026-08-04**, and all eight produced an empty diff. A ninth scenario,
  `end_of_cycle_gl`, was added afterwards to reach `gl080`, and on **2026-08-07**
  all **nine** were driven through the complete protocol and all nine produced an
  empty diff. §8 and §9 record the evidence. **THAT NINTH DEFINITION AND ITS TEST ARE NOT COMMITTED:** the Agent Action Plan's inventory names eight scenario definitions and eight scenario tests, and this tree is held to it. Everything recorded about that journey is kept because it was really driven; what a reader cannot do is re-run it from the committed set, and `gl080` consequently has **no table-state comparison** behind it.

Recording those comparisons as `PENDING` would therefore have been to
write down something untrue. It would also have breached **R-6**, which requires
that observed compiled behaviour decide a question and "be documented rather
than settled silently" — and suppressing a measured result is the definition of
settling it silently. It would additionally have contradicted the sibling
deliverable [`ambiguity-resolutions.md`](ambiguity-resolutions.md), which
already records `RESOLVED BY ORACLE` for questions closed by these same runs.

**The deviation is therefore this: the observed statuses are used, because the
comparisons were observed.** The brief's actual prohibition — never claim an
empty diff that was not observed — is honoured exactly, in both directions.
`PENDING — AWAITING ORACLE EXECUTION` remains in the vocabulary and is used
wherever this register genuinely has no measurement, which is §13.

Everything asserted as observed below was re-driven on the code as committed. §9
gives the commands and names every artifact a run writes; §8.1 and §10 give the
digests. Those artifacts live on the harness `out` volume, outside the checkout
(§9.3), so each digest is a **report of the run that was watched**: a future run of
the same protocol can reproduce it, but a reader of this repository cannot recompute
it from committed state.

## 4. The protocol

AAP §0.3.2 fixes the order as "seed, run, dump, normalize, reset, run, dump,
diff", and §0.8.5 restates it in full. Those are the **eight** logical stages
the AAP mandates:

| # | AAP stage | Command |
| ---: | --- | --- |
| 1 | seed | `harness/seed.sh` |
| 2 | run the compiled cycle | `harness/run_cobol_scenario.sh` |
| 3 | dump | `harness/dump_tables.py --scenario <name> --side cobol` |
| 4 | normalize | `harness/normalize.py` |
| 5 | reset | `harness/reset_db.sh` |
| 6 | run the Python cycle | `harness/run_python_scenario.sh` |
| 7 | dump | `harness/dump_tables.py --scenario <name> --side python` |
| 8 | diff | `harness/diff_states.py` |

The ordering is rigid rather than ad hoc for a reason AAP §0.3.2 records
directly: deterministic orchestration with explicit validation stages
outperforms unconstrained execution on migration work. So the stages are fixed
instead of improvised, and a later stage may never render a verdict on evidence
an earlier stage never produced.

### 4.1 The eight AAP stages as the harness's ten

The protocol executes **ten** stages. The ten are the AAP's eight with two mechanical
refinements and no change of substance. There is no driver script — no
`harness/run_parity.sh` — so the stages are run in order by the operator
(README §11.1) or composed by `tests/conftest.py::run_scenario_parity`, and each gate
lives in the stage that owns the state it protects:

| harness stage | Command | AAP stage |
| ---: | --- | --- |
| 1 | `harness/reset_db.sh <scenario>` — apply the frozen schema, then seed | 1 (`reset_db.sh` invokes `seed.sh`) |
| 2 | `harness/run_cobol_scenario.sh <scenario>` | 2 |
| 3 | `harness/dump_tables.py --side cobol --all-in-scope --scenario-file <scenario>` | 3 |
| 4 | `harness/normalize.py --side cobol` | 4 |
| 5 | `harness/reset_db.sh <scenario>` — apply and **re-seed** | 5 |
| 6 | `harness/run_python_scenario.sh <scenario>` | 6 |
| 7 | `harness/dump_tables.py --side python --all-in-scope --scenario-file <scenario>` | 7 |
| 8 | `harness/normalize.py --side python` | 4, applied to the second capture |
| 9 | both normalised trees are present and published | a precondition of 8 |
| 10 | `harness/diff_states.py --all-in-scope --scenario-file <scenario>` | 8 |

**`--all-in-scope` AND `--scenario-file` TOGETHER ON STAGES 3, 7 AND 10, ALWAYS.**
The two flags do different jobs and are not alternatives: `--all-in-scope` sets the
comparison bound to all 22 in-scope tables, and `--scenario-file` names the definition
whose sha256 becomes the `scenario_file_sha256` provenance field that stage 10 requires
to be present and equal on both sides. Omitting `--all-in-scope` does not fail — the
definition then also SELECTS, so the capture narrows to the scenario's declared
`affected_tables` and stage 10 reports, for `clean_batch_gl`, `identical - 5 table(s)
compared` instead of 22. Every row of §8 below was taken with both flags, which is why
each carries `22` in its bound column. `tests/conftest.py`'s composed protocol passes
both at the same three stages, so the hand-driven and composed routes are the same
protocol rather than two.

The two refinements: the AAP's single "normalize" stage is applied once per
side, so it appears twice; and the publication check is separated out so that a
partial capture cannot reach the comparison. `reset_db.sh` occupies stages 1 and
5 deliberately — they are the same command because the two cycles must start
from the same seed, and the second reset is what makes the Python side's
starting state the COBOL side's *starting* state rather than its *ending* state.

The driver **aborts at the first non-zero stage** and the run's exit status is
that stage's own, so a diagnosis is never flattened away. `--keep-going` exists
for diagnosing a broken harness and is explicitly not the protocol: a verdict
produced that way is not evidence.

**One stage is exempt from that rule, and the exemption is mandated.** It is
**stage 6 with exit 69 and nothing else**: the Python run
stage reporting that an operation's observed disposition contradicted the scenario's
declared one. There the protocol **continues** — deliberately, so the capture, the
normalisation and the diff all still happen and the divergence can be localised to a
table and a column rather than being reported only as a status. The rule is
implemented at `[tests/conftest.py RUN_PYTHON_BEHAVIOURAL_EXIT]` and
`[tests/conftest.py DISPOSITION_BEHAVIOURAL]`. The outcome is unaffected: it is
remembered, and **the result cannot be parity after it, whatever the diff says.**
Every other non-zero stage stops the run.

### 4.2 Seeding constraints

**`common/masterLD.sh` is never invoked**, for three independent and separately
verified reasons:

1. **It is syntactically unrunnable.** Its 24 loader lines at L93–L116 are
   written `if [ -e X.dat ];  then YLD fi`, omitting the mandatory `;` or
   newline before `fi`. `bash -n common/masterLD.sh` reports
   `common/masterLD.sh: line 124: syntax error: unexpected end of file` on a
   **123-line** file.
2. **Its own author marks it untested.** `[common/masterLD.sh:L4-L5]` reads
   `#   THIS SCRIPT HAS NOT YET BEEN TESTED`, corroborated verbatim at
   `[Changelog:L21-L22]`: "Revised scripts masterUNL.sh, masterRES.sh & /
   masterLD and so far only tested masterUNL."
3. **It ends in an interactive pager.** Its final statements are
   `less SYS-DISPLAY.log` then `exit 0`, which would block a non-interactive
   run indefinitely.

`harness/seed.sh` therefore reproduces the script's **per-file contract** at
`[common/masterLD.sh:L44-L115]` rather than delegating to it.

**Loader exit semantics are checked, not assumed.**
`[common/masterLD.sh:L37-L39]` documents them: **128** = parameters not set up,
**64** = RDBMS not set up, **16** = error writing data to the RDB. Anything
above **63** aborts the load. Note also the strict-versus-lenient asymmetry at
`[common/masterLD.sh:L83]`, where `dfltLD` alone is checked with
`if [ $rc != 0 ]` rather than against the threshold.

**`harness/reset_db.sh` re-applies the frozen schema, and the file's own shape
is what makes that sufficient.** `mysql/ACASDB.sql` contains **33**
`CREATE TABLE` and **33** `DROP TABLE IF EXISTS`, so re-applying the file *is*
the drop-and-recreate. It contains **zero** `CREATE DATABASE` and **zero** `USE`,
so the database name must be supplied on the client command line; and **zero**
`INSERT INTO`, so all data comes from the loaders.

### 4.3 The autocommit window — a measured operating precondition

AAP §§0.2.1.1, 0.4.1.7 and 0.5.2 require autocommit **off** during seeding, each
citing the banner at `[common/glbatchLD.cbl:L9-L12]`. Two measured facts bear on
that requirement and are recorded here because they changed how the protocol is
invoked:

- The cited lines are a four-line **comment banner** addressed to the operator
  ("This modules uses commit and rollback so you MUST ensure that autocommit is
  OFF in the rdb settings. It is as default set ON."), not an executable
  setting. The vendored C interface exposes `MySQL_commit` and `MySQL_rollback`
  and **no** `MySQL_autocommit`, so no COBOL program in the checkout can change
  the mode.
- There are no commit boundaries for a seeded state to depend on. Every
  `perform aa020-Rollback` in all 28 `common/*LD.cbl` loaders is commented out,
  and `perform aa030-Commit` occurs exactly once anywhere — at
  `[common/irsdfltLD.cbl:L437]`, commented out too.

Consequently, under the mandated OFF window the frozen loaders return success
and leave **zero** durable rows: MariaDB discards each session at disconnect.
`harness/seed.sh` measures this and exits **76** rather than letting an
all-empty capture reach the comparison, because an all-empty diff would certify
the migration exact having compared nothing at all. This was observed directly
while authoring this file: stage 1 failed with exit 76 and the report "every
load program reported success and the database holds NO rows in any of the 7
table(s) they write."

The resolution, recorded as an R-6 arbitration at `Q-10` in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md), scopes the requirement
to **seeding** and MEASURES autocommit **on** to be the only mode in which the
frozen loaders persist a row. Both modes were run against the compiled loaders:
under `off` all seven load programs return zero and a fresh session sees zero
rows in all seven seeded tables; under `on` the same seven return zero and a
fresh session sees eight rows across those seven tables. The return codes are
**identical** either way, so the mode is invisible to the frozen code.

**The measurement settles the behaviour; the AAP settles the default — and they
point opposite ways.** `on` is the only mode measured to leave a durable row;
`off` is the mode AAP §0.2.1.1, §0.4.1.7 and §0.5.2 mandate. Running those two
questions together is the easy error, so each outcome is stated separately:

- **`off` is the shipped default.** `ACAS_SEED_AUTOCOMMIT` unset selects `off` —
  [`harness/seed.sh acas_open_seed_autocommit_window`] resolves the unset variable
  to `off` on its `''|off|0|false|no` branch and refuses any other value with
  `EX_USAGE`; [`harness/seed.sh acas_assert_seed_durability`] is what then measures
  the result and refuses an empty seed. An explicit `off` states that default
  outright. The default is the AAP-mandated window *precisely because* it is the
  mode that always fails on an empty database: exit **76**, "every load program
  reported success and the database holds NO rows", is how this harness reproduces
  the frozen no-COMMIT defect end to end, which is what R-4 requires rather than a
  fault to configure away.
- **`on` is a declared deviation, requested per invocation.** Nothing pins it.
  `harness/docker-compose.yml` deliberately carries **no** `ACAS_SEED_AUTOCOMMIT`
  setting and neither Dockerfile carries an `ENV` or `ARG` for it — a pinned value
  would bake the deviation into every invocation and make it invisible in the
  command that ran — so the mandated default stays reachable through the harness
  for a reader who never opens `seed.sh`. Every command in §15 therefore passes
  `-e ACAS_SEED_AUTOCOMMIT=on` explicitly, and its absence from a command means
  that command seeded under the AAP-literal window and stopped at **76**. A fixture
  produced under the deviation is a working fixture, **not** AAP-conformant
  evidence: it is a **declared divergence from the letter of the Agent Action
  Plan** (§0.2.1.1, §0.4.1.7, §0.5.2), logged on every run and written up in full
  in the arbitration.

Runtime application access remains autocommit **on**, which both runners assert.
No harness code issues the COMMIT the frozen loaders omit — the defect is
reproduced and reported, never repaired (R-4).

Two tests hold that contract to the shipped scripts rather than to this prose:
`tests/arithmetic/test_comp_binary.py::test_the_seeding_window_defaults_to_the_aap_mandated_mode`
asserts the default, and `::test_no_harness_file_pins_the_seeding_window_to_the_deviation`
asserts that no Compose service or image bakes the deviation in. Either
arrangement — a different default, or a pin — fails the suite. A third,
`::test_no_document_claims_the_seeding_deviation_is_the_default`, reads the
documents in this directory and the top-level README so that the prose cannot
drift away from the scripts again. The full arbitration, including why the
deviation is available and why it is not the default, is `Q-10` in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md).

**Correction, recorded rather than quietly applied.** An earlier revision of this
section stated the opposite of all of the above — that `on` was "the shipped
default", that unset selected it, and that `harness/docker-compose.yml` declared
it explicitly "so no caller needs a flag to obtain a durable seed". That was
accurate for an earlier arrangement of the harness and became false when the
default moved to the AAP-mandated `off` and the Compose pin was removed; §15 of
this same document had already been corrected and pointed *here*, at the passage
that had not been. It is re-measured and rewritten rather than silently deleted,
because a reader who acted on the superseded text would have obtained an
all-empty capture and a stage-1 exit **76** with no idea why. Measured on this
checkout, three times: `harness/reset_db.sh` with the variable unset exits **76**,
and `harness/seed.sh` invoked directly against the freshly re-applied (therefore
empty) schema exits **76** as well; the same `reset_db.sh` command with
`-e ACAS_SEED_AUTOCOMMIT=on` exits **0**.

## 5. The verdict contract

### 5.1 `harness/diff_states.py` exit codes — the project's verdict

| Code | Meaning | Test outcome |
| --- | --- | --- |
| **`0`** | The two trees are identical. **stdout is EMPTY — zero bytes.** Not a banner, not "no differences found" — empty, because AAP §0.8.5 says the diff *must be empty*. | **PASS** |
| **`1`** | A real behavioural difference. A deterministic, **value-free** summary is written to stdout naming a mode-0600 report file and its SHA-256; no value ever reaches stdout. | **FAILURE** |
| **`2`** | The comparison **could not be performed** — a missing tree, a missing table file, a malformed dump, a shape mismatch, a `float` in the input, a duplicate primary key, wrong key order, `row_count != len(rows)`, a ragged row, or a `null` value. A diagnosis goes to stderr. | **ERROR — never a pass** |

**`2` is never conflated with `0`.** A run that treats "could not compare" as
"no differences" is the single worst bug available in this tree, and the tool
says so itself: an all-empty comparison — "nothing to compare, so nothing
differs" — is a **false pass**, and it is exit 2.

Two hardening properties matter to anyone reading the artifacts. With `--out`, a
**passing** run writes a **zero-byte** file, so the evidence distinguishes
"compared, and identical" from "never compared"; and any report already at that
path is deleted before the comparison begins, so a stale zero-byte file from an
earlier passing run cannot survive an error path and be misread as proof. And a
capture whose run stage did not attest a **completed** run is **refused**
outright unless `--allow-unattested` is passed, so carrying a partial capture
forward by hand fails closed rather than reporting a pass.

**What is not refused, and why that distinction earns its keep.** A run status is
evidence metadata, not a gate on one value, because a non-zero runner status has
two entirely different meanings. A missing fixture, an unreachable server or an
overrun deadline means the run *measured nothing*, so its capture is refused. But
`harness/run_python_scenario.sh` exiting **69** means every operation ran, every
post-run assertion was taken, and a disposition contradicted what the scenario
declares — the run *completed*, and the state it left **is** the finding. That
capture is compared, and its disposition is announced on stderr above the verdict
so an empty diff can never be read as an unqualified parity claim. Refusing it would
withhold the one artifact that says which tables, rows and columns differ, precisely
when a human most needs it.

### 5.2 Comparison discipline

Rows align by **primary-key value, never by position**. The comparison is
**exact**: no tolerance, no epsilon, no `math.isclose`, no case- or
whitespace-insensitive compare, no numeric coercion, **no ignore-list**, and no
"known difference" allowance. `1` versus `"1"` **is** a difference.

Directions are labelled distinctly — **`missing_in_python`** versus
**`missing_in_cobol`** — and the side labels are exactly **`cobol`** and
**`python`**, never "left" and "right", so a report cannot be read backwards.
`--max-differences N` truncates the output but prints the **true total** and
**never** changes the exit code.

Because `SYSTEM-REC` carries **169** columns, printing the column **ordinal**
beside its name is load-bearing rather than cosmetic: a bare column name in a
169-column row is not enough to locate a field by eye. Findings therefore carry
a 1-based `col[N]` ordinal in schema order, of the form:

```text
GLLEDGER-REC  row_count  cobol=12  python=11
GLLEDGER-REC  missing_in_python  LEDGER-KEY=1204
GLLEDGER-REC  LEDGER-KEY=1100  col[6] LEDGER-BALANCE
```

One refinement against the shape sketched in this file's brief, recorded rather
than glossed: the committed tool deliberately keeps **stdout value-free** and
writes the differing values themselves into the mode-0600 report, so a
difference line on stdout identifies the row and the column but does not print
the two figures. The implementation is authoritative; a register that reprinted
a format the tool does not emit would misdirect whoever next reads a failure.

### 5.3 The dump shape

`harness/dump_tables.py` emits exactly **five** keys, in a fixed insertion order,
and no others: **`table`**, **`primary_key`**, **`columns`**, **`row_count`**,
**`rows`**. `columns` is in schema **ordinal** order; `rows` is **primary-key
ascending**; `row_count == len(rows)`; `DECIMAL` values are present as canonical
JSON strings; there is **no `null`** and **no `float`**. Verified directly on a
capture from the runs in §9:

```text
KEYS: ['table', 'primary_key', 'columns', 'row_count', 'rows']
table: GLLEDGER-REC  primary_key: LEDGER-KEY  row_count: 4  len(rows): 4
row0: [100000, 1, '', 1, 'Bank current account',
       '0.00', '0.00', '0.00', '0.00', '0.00', '0.00']
any float: False    any null: False
```

The dump is simply `SELECT * FROM <table> ORDER BY <primary key>` — no
tie-breaking logic, no timestamp masking, no surrogate-key remapping — and it is
deterministic *by construction*, because the frozen schema is exceptionally
well behaved for the purpose. Re-measured for this document: all **22** in-scope
tables have a **single-column primary key** and **zero** secondary indexes;
there are **zero** `TIMESTAMP` columns; all **513** columns across those 22
tables are `NOT NULL`; and the file is **1459** lines.

`harness/dump_tables.py` also treats `--scenario-file`, `--tables` and
`--all-in-scope` as **mutually exclusive** and raises rather than guessing, so
every invocation names its scope.

**`--all-in-scope`, all 22 tables, is THE PROTOCOL.** The recipe in README §11.1
passes it at stages 3 and 7 and `tests/conftest.py` passes it from `dump`; stage
10 diffs with `--all-in-scope`. The reason is that a bound drawn from what a
scenario *expects* to move cannot reveal a difference in anything it did not
expect to move, and an empty diff is the single pass condition (Agent Action Plan
section 0.8.5). The reason is **not** that only the COBOL side rewrites the
parameter tables — both sides do. `overrewrite.` `[general/general.cbl:L656-L672]`
rewrites `SYSTEM-REC` under key 1, `SYSDEFLT-REC` under key 2 and `SYSTOT-REC`
under key 4, and **both cycles perform it** —
`acas_posting/cli/args.py::overrewrite` reproduces that RDB arm, writing key 1
unconditionally, key 2 only when the route loaded the defaults record and key 4
only when it loaded the totals record, which reproduces the frozen per-route
divergence (General writes keys 1, 2 and 4; Sales and Purchase write keys 1 and 4
and never key 2 `[sales/sales.cbl:L338-L360]`, `[purchase/purchase.cbl:L333-L354]`),
while `irs_post` persists key 1 through the IRS menu's own `EOJ.` shape. `Q-7`
records that correction. So those rows are **comparable on both sides**, not a
source of false failure — and a capture that omitted them could have reported an
empty diff while the run date, the allocators, the flags, the defaults or the
period totals differed.

**`SYSTEM-REC` IS DUMPED WITH EXACTLY TWO CELLS WITHHELD.** A dump is `SELECT *`
and `RDBMS-PASSWD char(12)` `[copybooks/wssystem.cob:L139]` is one of its 169
columns, so a capture of the row would carry the database password into this
evidence set; `harness/dump_tables.py`'s `REDACTED_COLUMNS` replaces that cell and
the frozen schema's shorter `PASS-WORD` cell — exactly those two, on **both**
sides — with one fixed marker. The row is still dumped and still diffed, every
other column byte for byte, so this is redaction rather than an ignore-list, and
withholding a secret symmetrically cannot conceal a difference in anything the
cycle computes. The row is **fingerprinted** as well, on both sides and on every
scenario, and `tests/conftest.py`'s `assert_system_record_parity` compares the two
post-run digests over all 169 columns — the credential included, with nothing to
leak, because a sha256 of a canonical dump is not the dump.

A scenario's `affected_tables` is its **declared effect**, asserted against
`expected_table_effect` within each side; it is *not* the comparison bound.
`--scenario-file` (narrow to that declared effect), `--tables` (one table by
hand) and `diff_states.py --all-tables` (the union of whatever the two captures
hold) are **debugging aids, not the protocol**. The eleven out-of-scope tables
are never dumped.

> **RE-MEASUREMENT COMPLETE — the §8 register below is the 22-table one.**
> An earlier register recorded these scenarios under the NARROWER per-scenario
> bound, and it was correctly marked superseded rather than rewritten, because an
> empty diff over 3, 4, 10 or 14 tables does not establish an empty diff over 22.
> All eight scenarios have since been **re-run and re-recorded** under
> `--all-in-scope`, and §8 now reports that measurement and no other. The earlier
> narrower numbers are not reproduced here: keeping two registers side by side
> would invite the wrong one being cited. §8 states the bound in its own `Tables`
> column, which reads **22** for every row, so a future reader can tell at a
> glance which bound produced it.

### 5.4 Three corrections to the schema census

These are stated as measured rather than repeated as received, because each was
overstated somewhere upstream:

1. **There are no schema-evolution statements.** `grep` finds 66 `ALTER TABLE`
   hits, and **all 66 are mysqldump `/*!40000 … DISABLE KEYS */` and
   `ENABLE KEYS` comments**: filtering out comment lines returns **empty**.
   There are likewise **zero** `CREATE INDEX` statements.
2. **One column-level `DEFAULT` does exist.** `SYSTEM-REC.PASS-WORD` is
   `char(4) NOT NULL DEFAULT ''` at `[mysql/ACASDB.sql:L1219]`. The blanket
   claim that the schema has no column defaults is wrong; the claim that none of
   them perturbs a dump is right, because the loaders and both cycles write
   every column explicitly.
3. **The only `AUTO_INCREMENT` in the file is out of scope.**
   `STOCKAUDIT-REC.AUDIT-ID` at `[mysql/ACASDB.sql:L1107]` is the sole
   occurrence — **zero** for the in-scope 22, one for the file. That is one more
   concrete reason the eleven out-of-scope tables must never be dumped: a
   surrogate counter is exactly the kind of column that would differ between two
   runs for reasons that are not behavioural.

A fourth point of hygiene, not a correction: **primary-key names are not
globally unique.** `PUINV-LINES-REC` and `SAINV-LINES-REC` both use
`IL-LINE-KEY`, and `IRSDFLT-REC` and `SYSDEFLT-REC` both use `DEF-REC-KEY`. A
dump must therefore be keyed by table *as well as* key name; keying by key name
alone would silently collide two tables.

Finally, the build shims that made the oracle reachable, recorded here because they
touch the freeze question directly. **There are 41 of them, not one**, and every one is
published in the attestation with its frozen digest, its build digest and its reason —
see README §8.10 for the four groups and the paragraph in §1 for what that means for a
verdict. Naming a single shim would leave a reader to infer there were no others.

The one named here remains the clearest case, because it is the only shim that
CREATES a file rather than editing one: `copybooks/ACAS-SQLstate-error-list.cob` is
absent from the checkout while being `COPY`'d by 44 frozen files. Direct build
analysis established that the include contributes **comments only**, so
`harness/build_oracle.sh` materialises a semantically inert comment-only file
under `$ACAS_BUILD/copybooks` and adds that writable directory to the compiler's
copy path — and refuses it if it ever acquires text other than blank lines and COBOL
comments. This invents no SQLSTATE mapping and edits nothing under `copybooks/`.

The other forty are `IF`-scope repairs in six loaders and connection propagation and
ownership repairs across 25 handlers, three secondary loaders, both
`mysql-procedures` copybooks, `irs030` and the three menus. None alters an arithmetic
statement, a `ROUNDED` site, a sort key, a control-total comparison or a rejection
path, and the build's own completeness measurement makes it impossible to add a
forty-second without declaring it. Cross-reference **A-NEW-13** in
[`anomaly-log.md`](anomaly-log.md) and §10.1 of
[`ambiguity-resolutions.md`](ambiguity-resolutions.md).

### 5.5 `harness/normalize.py` — exactly three jobs, and there is no fourth

The tool says so in its own words: "the three canonicalisation jobs, and there
is no fourth".

**Job 1 — trailing spaces in fixed `char(n)` columns.** `rstrip(" ")`,
**trailing only** and **ASCII `U+0020` only**, applied by **declared type**
including `char(1)`. A COBOL alphanumeric `MOVE` is left-justified with right
padding, so **leading spaces are content** and must never be stripped. The
empirical motivation is that the bridge itself trims:
`[common/nominalMT.cbl:L1065-L1067]` uses
`FUNCTION TRIM (HV-LEDGER-NAME,TRAILING)`, and there are **23** `FUNCTION TRIM`
sites in `nominalMT.cbl` and **29** in `glpostingMT.cbl` — so the COBOL side
stores char columns trimmed while a Python data-access layer writing the padded
record field could store them padded. Cross-reference **A-12** and the 24→32
width drift at `[common/nominalMT.cbl:L299]` against
`[mysql/ACASDB.sql:L127]`.

Recorded honestly: through this harness's driver this job usually finds
**nothing** to do, because MariaDB strips trailing spaces from a `char` column
on read unless `PAD_CHAR_TO_FULL_LENGTH` is set and the harness server does not
set that mode either way. It is kept regardless — the width drift it answers is
real, server behaviour is a setting rather than a guarantee, and a capture taken
through a driver or server that *does* preserve padding must still compare equal.
A guard that mostly finds nothing is not a guard that does nothing.

**Job 2 — decimal values re-rendered at the column's DECLARED scale.** **Never
assume 2.** The measured census over the 167 `DECIMAL` columns:

| Declaration | Count |
| --- | ---: |
| `decimal(9,2)` | 68 |
| `decimal(10,2)` | 57 |
| `decimal(4,2)` | 17 |
| `decimal(5,2)` | 12 |
| `decimal(14,2)` | 4 |
| `decimal(2,0)` | 2 |
| `decimal(14,4)` | 2 |
| `decimal(6,2)`, `decimal(5,0)`, `decimal(11,4)`, `decimal(11,2)`, `decimal(10,4)` | 1 each |

Scales of 0 and 4 are both present, so a hard-coded two would corrupt seven
columns and silently mask differences in five more. A value carrying more
significant decimals than its column declares is an **error** — the tool raises
rather than rounding it away.

**Job 3 — two- versus four-digit date TEXT rendering, driven by an explicit
column allow-list of exactly five**, verified in the code:

| Column | Declared type |
| --- | --- |
| `GLPOSTING-REC.POST-DAT` | `char(8)` |
| `IRSPOSTING-REC.POST4-DAT` | `char(8)` |
| `PSIRSPOST-REC.IRS-POST-DAT` | `char(8)` |
| `SALEDGER-REC.SALES-STATS-DATE` | `char(4)` |
| `SYSTEM-REC.STATS-DATE-PERIOD` | `char(4)` |

`char(8)` does **not** imply "date". `PUITM5-REC.OI5-BATCH` and
`SAITM3-REC.OI3-BATCH` are batch references and are **explicitly excluded** in
the code, by name.

Most in-scope "dates" are not text at all but **binary day numbers**, and job 3
must not touch them: `GLBATCH-REC.ENTERED`, `PROOFED`, `POSTED` and `STORED` are
all `int(8) unsigned` at `[mysql/ACASDB.sql:L86-L89]`, derived from the four
`binary-long` fields at `[copybooks/wsbatch.cob:L36-L39]`, so
`[general/gl072.cbl:L376]`'s `move run-date to posted` stamps an **integer**, not
a date string.

Job 3 is **rendering only**: it never expands two digits to four nor contracts
four to two, and anything that does not match its canonical shape is passed
through **unchanged** and **reported** for the oracle to settle. See **`Q-8`** in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md), which is why: whether
`Post-Date (7:2)` holds a year or a century is settled on the Sales path and
open elsewhere.

**AAP §0.6.6 must be read both ways.** Normalisation removes representation
artefacts, **and** it must never make two genuinely different stored values
compare equal. **Over-normalising is as fatal as under-normalising** — the first
produces a false failure that wastes a run, the second produces a false pass that
certifies a defect. The three jobs are bounded, named and closed for that reason.

One further integrity property: the **set is the unit, not the file**. A source
tree must carry a `_manifest.json`, written last by the stage that published it;
a tree without one did not finish and is refused, because normalising a partial
capture carries it into a comparison that can pass. The manifest's scenario,
side, selector and run attestation are **inherited**, never re-judged, so the two
stages of one run cannot claim different identities.


## 6. Inputs pinned identically across all eight scenarios

### 6.1 The controlled clock — two observables, and why two suffice

| Observable | Value | Declaration |
| --- | --- | --- |
| Text date `to-day pic x(10)`, DD/MM/CCYY | **`21/09/2025`** | passed through linkage |
| Binary `Run-Date` | **`155127`** | `05 Run-Date binary-long.` at `[copybooks/wssystem.cob:L67]` |

The epoch is **1600-12-31**, which the date module's own remarks flag at
`[common/maps04.cbl:L39-L42]` as making it "NOT usable within IRS as is" because
IRS carries two-digit years. These two values are the constants
`PINNED_RUN_DATE_TEXT` and `PINNED_RUN_DATE_BINARY` in `tests/conftest.py`, where
the conversion `date(2025, 9, 21) -> 155127` is recorded as verified on the
target interpreter.

Two observables suffice because **both descend from one shared date service**, and
because the migrated programs read no clock at all.
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L72]` is
`move function current-date to wse-date-block.`, and the propagation is then
fully visible in the next eight lines:

- **L77** `move u-date to to-day.` — observable 1;
- **L78** `move zero to u-bin.` — the caller **pre-zero**;
- **L79** `call "maps04" using maps03-ws.`;
- **L80** `move u-bin to run-date.` — observable 2.

Every one of the twelve in-scope posting programs contains **zero** clock reads
and receives the date purely through linkage. There is no hidden time source, no
random seed, and no ordering nondeterminism from a secondary index. Pinning these
two values is therefore sufficient to make two runs byte-identical, and no clock
abstraction is needed inside the migrated programs at all.

**The service above is not the only clock read in the call chain.** The Agent Action
Plan's own phrasing at §0.1.1 — *"exactly one clock read in the entire COBOL call
chain"* — is disprovable with one `grep`, so the census is stated:
`function current-date` appears at `[copybooks/Proc-ACAS-Mapser-RDB.cob:L72]`
**and** once in each menu shell — `[general/general.cbl:L371]`,
`[sales/sales.cbl:L323]`, `[purchase/purchase.cbl:L318]`, `[irs/irs.cbl:L480]` —
**and** in the system selector reached before any of them,
`[common/ACAS.cbl:L353]`. Further reads exist in programs the cycle never
reaches; `docs/migration/anomaly-log.md` names them under **A-16**.

**The determinism argument is unaffected, which is why the correction is worth
making rather than glossing.** All six reads sit *above* the migrated surface,
every one of them feeds the same two linkage values, and the twelve migrated
programs read no clock. What the correction changes is only the claim's
checkability: "one read" fails a `grep`, "zero reads inside the twelve, with the
reads confined to the menus and the shared service they call" does not.

The pre-zero at L78 is what makes **A-16** observable. The date module leaves its
output field **untouched** on a rejected date, so the documented "errors return
zero" contract holds only because the caller zeroed the field first. **If a run
ends with `RUN-DAT = 0`, that is information — it must not be masked.** Both
runners therefore read the pinned value back out of the database after the run
rather than trusting the input; §9 records the assertion.

**The IRS exception, recorded honestly rather than smoothed over.**
`[irs/irs.cbl:L632-L634]` performs an **unconditional**
`move run-date to u-bin.` / `perform maps04.` / `move u-date to to-day.`
immediately before `Main-Loop.` at L637, with the maintainer's comment at L636
that the menu uses the IRS parameter file dates. And
`[copybooks/irswssystem.cob:L14]` declares `03 run-date pic x(8).` — that is
**text `dd/mm/yy`**, not the binary `Run-Date`. Separately, `irs030`'s posted date
comes **from the data, not the linkage**: `[irs/irs030.cbl:L1662]` is
`move WS-IRS-Post-Date to post-date.` The IRS route is therefore pinned by the
same two observables at the boundary, but the value that reaches an IRS posting
row is the seeded one.

### 6.2 The IRS fan-out switch — pinned explicitly in every scenario

The switch is `05 IRS-Instead pic x.` with `88 IRS-Used value "Y".` and
`88 IRS-Both-Used value "B".` at `[copybooks/wssystem.cob:L179-L181]`. It is
tested at 27 sites across the four Sales and Purchase posting programs — seven each
in `sl060`, `sl100` and `pl060` and six in `pl100` —
for example `[sales/sl060.cbl:L1039]`, `L1126` and `L1175`. AAP §0.6.4:

> "The scenario definitions must therefore pin this switch explicitly, since
> leaving it at a default would make the affected-table list ambiguous."

**All eight scenarios pin it to a single space**, `irs_instead: " "`. Two
subtleties are worth recording:

- **The third state has no condition name at all.** A space satisfies neither
  `IRS-Used` nor `IRS-Both-Used`, so both predicates are simply false. There is
  nothing to name and nothing named.
- **The CLI takes the character itself, and there is no `N` token.**
  `--irs-instead` accepts ONE character and its own help states that `Y` and `B`
  are the field's only condition names and that there is no third value "and in
  particular no `N`". So a YAML space or empty value reaches the command line as
  the **literal space**, `--irs-instead ' '`, and that is also the value written
  to `SYSTEM-REC.IRS-INSTEAD`. There is no token substitution and therefore no
  surface-form deviation to note: the character the scenario declares is the
  character the option carries and the character the column stores.
  `harness/normalize.py` trims the stored column identically on both sides, so a
  trailing space cannot become a diff either.
  **THE CHOICE SET IS NOT `{N, Y, B}` AND THERE IS NO SPACE-TO-`N` MAPPING**, and
  that distinction is not cosmetic: a reader who believed otherwise would type
  `--irs-instead N`, which stores the character `N` in the column and diverges from
  every scenario's seeded value.

### 6.3 Other pinned system values

| Field | Value | Why it is pinned |
| --- | --- | --- |
| `FILE-SYSTEM-USED` | `1` | Forces both cycles through the MySQL bridge. A zero here would route the COBOL side to indexed files and produce unchanged tables that look exactly like a correct result — the false-pass trap every scenario file names first. |
| `Cyclea` / `Scycle` | `1` | The accounting cycle both batch-file filters test. |
| `period` | `1` | Shared by all **eight**, and by the uncommitted ninth too, so no scenario differs by period. It is inert for the **cycle-to-period divide** at `[general/gl080.cbl:L328]` for TWO independent reasons, and a reader needs both: a period of one leaves that divide nothing to decide, AND no committed scenario drives `gl080` at all. A `period` of **0**, which is what `Q-GL080-DIVIDE-BY-ZERO` needed, is seeded by no committed scenario; that question was closed by a focused probe instead. |
| `date_form` | `1` | UK day-month-year. It governs the digit **order the COBOL reads**, never a reordering of the pinned text, which is passed through unchanged. |

## 7. Affected-table lists, seeds and answers

### 7.1 The declared order is load-bearing

Each scenario's `affected_tables` list bounds the comparison, and the state
fingerprint is written as `<TABLE><TAB><row count><TAB><sha256>` lines in the
list's **declared order**, plus one line for the fingerprint-only parameter row.
The digest is of the table's canonical primary-key-ordered dump, which is what
makes the record decisive: two seeds carrying **different values at the same row
counts** would agree on a count-only record. A single producer,
`harness/dump_tables.py --table-digest`, computes every digest for both sides and for both the
pre-run and the post-run record. A disagreement between the two sides'
pre-run fingerprints is a **harness fault** — exit **2** — and not a diff, because
two cycles that started from different states cannot be compared for behaviour at
all.

| Scenario | Affected tables (declared order) | Count |
| --- | --- | ---: |
| `clean_batch_gl` | `GLBATCH-REC`, `GLLEDGER-REC`, `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC` | 5 |
| `clean_batch_sl` | `ANALYSIS-REC`, `GLBATCH-REC`, `GLPOSTING-REC`, `PSIRSPOST-REC`, `SAINV-LINES-REC`, `SAINVOICE-REC`, `SAITM3-REC`, `SALEDGER-REC`, `SYSTEM-REC`, `SYSTOT-REC`, `VALUEANAL-REC` | **11** |
| `clean_batch_pl` | `ANALYSIS-REC`, `GLBATCH-REC`, `GLPOSTING-REC`, `PSIRSPOST-REC`, `PUINV-LINES-REC`, `PUINVOICE-REC`, `PUITM5-REC`, `PULEDGER-REC`, `SYSTEM-REC`, `SYSTOT-REC`, `VALUEANAL-REC` | **11** |
| `clean_batch_irs` | `IRSDFLT-REC`, `IRSNL-REC`, `IRSPOSTING-REC`, `PSIRSPOST-REC`, `SYSTEM-REC` | 5 |
| `mixed_accepted_rejected` | `GLBATCH-REC`, `GLLEDGER-REC`, `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC` | 5 |
| `period_end_totals` | `ANALYSIS-REC`, `GLBATCH-REC`, `GLPOSTING-REC`, `PSIRSPOST-REC`, `PUINV-LINES-REC`, `PUINVOICE-REC`, `PUITM5-REC`, `PULEDGER-REC`, `SAINV-LINES-REC`, `SAINVOICE-REC`, `SAITM3-REC`, `SALEDGER-REC`, `SYSTEM-REC`, `SYSTOT-REC`, `VALUEANAL-REC` | **15** |
| `control_total_mismatch` | `GLBATCH-REC`, `GLLEDGER-REC`, `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC` | 5 |
| `empty_batch` | `GLBATCH-REC`, `GLLEDGER-REC`, `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC` | 5 |
| `end_of_cycle_gl` *(not committed)* | `GLBATCH-REC`, `GLLEDGER-REC`, `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC` | 5 |

**Eight scenarios, 62 declared affected-table entries**, generated from the committed
`harness/scenarios/*.yaml` files rather than transcribed. The `end_of_cycle_gl` row above
is retained only as the record of what was measured before that definition was removed,
and is excluded from both figures. The union of the eight lists is **20** of the 22
in-scope tables. The two no scenario declares are **`SYSFINAL-REC`** and
**`IRSFINAL-REC`** — the final-accounts records, which the posting cycle reads but never
writes — and they are nonetheless COMPARED on every run, because stages 3, 7 and 10 are
bounded by all 22 rather than by the declared lists.

**The declared list is not the comparison bound.** It bounds the state FINGERPRINT
described above, and the runners assert the declared effect against it, but stages 3, 7
and 10 all pass `--all-in-scope`, so the diff is taken over all **22** in-scope tables.
A comparison bounded by what a scenario EXPECTS to move could not show a difference in
anything it did not expect to move, and AAP §0.8.5 makes an empty diff the single pass
condition.

Both lists that carry `PSIRSPOST-REC` on a Sales or Purchase route carry it even
though the fan-out is a space, precisely so that an unexpected fan-out write
would be caught rather than missed.

### 7.2 Seed flat files and driven answers

**The fixture directory is mechanical and the same shape for every scenario:**
`/data/fixtures/<scenario-name>`, built by `harness/seed.sh --build-fixtures` and passed
to the protocol as `--seed-dir /data/fixtures/<scenario-name>` — so
`clean_batch_gl` reads `/data/fixtures/clean_batch_gl`, and so on for all eight.
It is stated once here rather than repeated in each of §10's eight sections
because there is nothing per-scenario about it beyond the name. Two properties of
it are not mechanical and are worth stating: it lives **outside** the checkout,
because the checkout is mounted read-only as frozen specification (R-3) and a
scenario's own `seed_dir` would otherwise resolve inside it; and `--seed-dir`
changes **where** the declared files are read from and never **which** files are
required — the scenario's `seed_files` list below remains the sole authority, and
`system.dat` is mandatory in every one of them.

**Answers** are the frozen interactive prompts that gate a database write,
promoted to scenario keys. A dash means the scenario's route has no such prompt.
Note that `payment_post_confirm` covers **both** `sl_cash_post` and
`pl_payment_post`, which is why `period_end_totals` needs only one answer key for
its four operations.

| Scenario | Seed flat files | Answers |
| --- | --- | --- |
| `clean_batch_gl` | `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat` | — |
| `clean_batch_sl` | `system.dat`, `analysis.dat`, `value.dat`, `salesled.dat`, `invoice.dat`, `openitm3.dat` | — |
| `clean_batch_pl` | `system.dat`, `analysis.dat`, `value.dat`, `purchled.dat`, `pinvoice.dat`, `openitm5.dat` | — |
| `clean_batch_irs` | `system.dat`, `irsacnts.dat`, `irsdflt.dat`, `irsfinal.dat`, `irspost.dat`, `postings2irs.dat` | `irs_clear_postings: "Y"` |
| `mixed_accepted_rejected` | `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat` | — |
| `period_end_totals` | nine files spanning both Sales and Purchase: `system.dat`, `analysis.dat`, `value.dat`, `salesled.dat`, `invoice.dat`, `openitm3.dat`, `purchled.dat`, `pinvoice.dat`, `openitm5.dat` | `payment_post_confirm: "YES"` |
| `control_total_mismatch` | `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat` | — |
| `empty_batch` | `system.dat`, `ledger.dat`, `batch.dat` — **deliberately no `posting.dat`** | — |

### 7.3 The loader each flat file uses

Per `[common/masterLD.sh:L44-L115]`, which `harness/seed.sh` reproduces per file
rather than by delegation:

| Flat file | Loader | Target table |
| --- | --- | --- |
| `system.dat` | `systemLD`, then `sys4LD`, `finalLD`, `dfltLD` | `SYSTEM-REC`, `SYSTOT-REC`, `SYSFINAL-REC`, `SYSDEFLT-REC` |
| `batch.dat` | `glbatchLD` | `GLBATCH-REC` |
| `posting.dat` | `glpostingLD` | `GLPOSTING-REC` |
| `ledger.dat` | `nominalLD` | `GLLEDGER-REC` |
| `salesled.dat` | `salesLD` | `SALEDGER-REC` |
| `purchled.dat` | `purchLD` | `PULEDGER-REC` |
| `postings2irs.dat` | `slpostingLD` | `PSIRSPOST-REC` |
| `irsacnts.dat` | `irsnominalLD` | `IRSNL-REC` |
| `analysis.dat` | `analLD` | `ANALYSIS-REC` |
| `value.dat` | `valueLD` | `VALUEANAL-REC` |
| `invoice.dat` | `slinvoiceLD` | `SAINVOICE-REC`, `SAINV-LINES-REC` |
| `pinvoice.dat` | `plinvoiceLD` | `PUINVOICE-REC`, `PUINV-LINES-REC` |
| `openitm3.dat` | `otm3LD` | `SAITM3-REC` |
| `openitm5.dat` | `otm5LD` | `PUITM5-REC` |
| `irsdflt.dat` | `irsdfltLD` | `IRSDFLT-REC` |
| `irsfinal.dat` | `irsfinalLD` | `IRSFINAL-REC` |
| `irspost.dat` | `irspostingLD` | `IRSPOSTING-REC` |

A file the scenario does not declare is skipped and logged as skipped — the seed
log records `analysis.dat absent -> analLD not run` and so on — so a missing
fixture can never be mistaken for an empty table.

**Why the fixtures are built rather than committed.** The frozen loaders read
COBOL flat files, and fifteen of the seventeen are `ORGANIZATION INDEXED` or
`RELATIVE`; an indexed file on this toolchain is a Berkeley DB Btree whose
on-disk form belongs to the library version the image carries. The scenario files
therefore declare the **records** as text under `seed_records`, and
`harness/seed.sh --build-fixtures` builds the files from them by generating a COBOL
writer per file, compiling it against the **frozen** copybooks, calling the
**frozen** handler to write, then reading every file back through the same
definitions and refusing the build unless the counts agree. Nothing about the
layout is restated anywhere. `--seed-dir` says **where** the built fixtures live;
the scenario's own `seed_files` list remains the sole authority on **which** files
may be used.


## 8. Observed summary

Every row below was produced by the protocol in §4, driven first-hand on
**2026-08-07** through the then-current driver `harness/run_parity.sh`, all ten stages,
exit 0, with no stage skipped and no flag supplied beyond `--seed-dir`. The commands
are in §9. **That driver is not part of this tree**: the same ten stages are run in
order by the operator (README §11.1, "The operator contract") or composed by
`tests/conftest.py`, and every gate it enforced lives in the stage that owns the state
it protects. The rows are reported exactly as they were measured; only the way the
sequence is invoked differs.

**RE-OBSERVED THROUGH THE CURRENT ROUTE, and the figures held.** All eight were driven
again on **2026-08-08** with no driver script involved: three
(`clean_batch_gl`, `clean_batch_sl`, `empty_batch`) stage by stage through README
§11.1's operator recipe, and all eight in one invocation of the committed scenario tier
(`python3 -m pytest -m scenario`, **106 passed**, exit 0). Every run reached stage 10,
each published `verdict.json` with `"outcome": "identical"`, `"tables_compared": 22`,
`"tables_differing": 0` and a **zero-byte `diff.txt`**, and the per-side row totals
re-measured from the capture manifests reproduced this table's `COBOL rows` and
`Python rows` columns exactly — 8, 22, 18, 78, 10, 46, 8, 7, identical on both sides of
every row. The re-observation carried the same disclosure it must: the oracle is the
diagnostic build, so these are agreement measurements and **no parity claim**.

**EVERY ROW BELOW IS A REPORT OF AN OBSERVED RUN, NOT A RETAINED REPOSITORY
ARTEFACT.** The `verdict.json`, `diff.txt` and manifest files whose digests these rows
cite live on the harness `out` volume, which §14.1 keeps deliberately outside the
checkout — **nothing under `data_dictionary/`, `docs/` or `harness/` in this repository
contains them**, and no `git add` can capture them. A reader cannot open a digest cited
here; the reproducible claim is the command in §9, run against the same seed and the
same oracle. Treat the digests as the identity of a run that was watched, not as
evidence a later reader can re-verify from the repository alone.

**These rows measure agreement with a TRANSFORMED oracle, not with the frozen
specification, and the tooling now refuses to call such a run evidence.** See §0 for
the two measured obstacles and for what these rows do and do not establish. They are
retained verbatim because they are observations.

**The oracle that produced it is named, not assumed.** All eight runs executed the
same attested build — module-set digest
`d18b337fdccaa31f59037e90d829f14bd6b44a84c0a8b836a2353c35caad33ca` over **179**
`*.so` modules, `presql2` archive
`638db9530d2fe008fbb46cf8600b9406f6f780c9fc59d0e0c94e868b4d615475` matching its
pin, `cobmysqlapi.o`
`e5f13cd0b848001f0549cf9c69070c9031e1a360f26d440cf559d6a60d2d7242` attested
`image-built-from-vendored-source`, toolchain `cobc (GnuCOBOL) 3.2.0` and
`cc 13.3.0`, `overrides-used=no` — which records that neither IDENTITY substitution
was used and says nothing about the source transformations.
The driver of the day verified that attestation before stage 2 in every one of the
eight runs and re-derived the module-set digest from the modules on disk; `reset_db.sh`
performs the identical check at stages 1 and 5, before it drops a table; see README
§8.9. A digest is quoted here so that evidence can be tied to an oracle rather than to
a directory.

**The attestation those runs carried was version 1, which did not record the
source transformations at all.** The build now publishes
`oracle-source-is-frozen=no`, a transform count and one record per transformed path,
and `harness/reset_db.sh` prints the count and the transform-set digest when it
accepts such a build, on every exit path. Re-running any scenario reproduces the same empty diff with the
disclosure attached; the figures above are the measurement and the sentence they
belonged under was the omission. Read them together with the paragraph in §1.

**THE MODULE-SET DIGEST ABOVE IS A BUILD IDENTITY, NOT A BEHAVIOURAL FINGERPRINT,
and it no longer names the build in the volume.** The oracle image has been rebuilt
since those eight runs, so `d18b337f…` identifies the build that produced *those rows
on that date* and nothing else. Measured from `/build/oracle-attestation.txt` as it
stands now: `attestation-version 2`, `module-set-sha256`
`c061de9c95561b945896865dc5086fe3aded7bfd3c1eb6789ac7fe681b1e6aef`, `module-count 179`
— **the same 179 modules**, because the rebuild changed only the image's Python layer —
with `overrides-used no` and `oracle-source-is-frozen no`. A reader who re-runs today
should therefore expect the digest to differ from the one quoted above and should not
read that difference as invalidating this table.

**The empty diffs were re-observed on the rebuilt oracle rather than inherited.**
`clean_batch_gl` was re-driven through all ten stages, every stage exit 0, verdict
`identical` over 22 tables (run id `parity-3f6c5f5ac2ec4515`), and `clean_batch_sl`
likewise returned `identical` over 22 tables. Both carried the version-2 disclosure —
41 transformed paths, transform-set digest `88dcc5e9…` — and both dumps agreed on
`scenario_file_sha256`, the provenance field whose absence had previously stopped stage
10. That is what ties this table to the build now in the volume.

**ALL EIGHT WERE THEN RE-DRIVEN IN FULL, ON THE CODE AS COMMITTED, AND EVERY FIGURE
IN THE TABLE BELOW REPRODUCED.** Two of eight is a spot check; the register claims
eight. So on **2026-08-08** each of the eight committed scenarios was driven through
the ten stages of §4.1 by the operator recipe of README §11.1a — no driver script,
one `ACAS_PARITY_RUN_ID` bound through all ten stages of that scenario,
`-e ACAS_SEED_AUTOCOMMIT=on`, and `reset_db.sh --accept-transformed-oracle` at stages
1 and 5 — in a freshly created clone-namespaced stack, against a diagnostic oracle
built from this checkout. Every scenario returned, without exception:

- **stage 10 exit 0 with stdout of exactly 0 bytes** — both halves of the pass
  condition, checked separately;
- `verdict.json` `outcome identical`, **22 tables compared**, **0 differences**;
- `diff.txt` of **0 bytes**;
- `run_id`, `scenario_file_sha256` and `frozen_schema_sha256` **present and equal on
  both sides** — the three fields `PROVENANCE_MUST_MATCH` names, one of which is the
  field whose emptiness had previously stopped stage 10 for every scenario;
- per-side row totals equal to the `COBOL rows`/`Python rows` columns below on **every
  row** — 8, 22, 18, 78, 10, 46, 8 and 7 — with `control_total_mismatch` recording
  `operation_status gl_post_cycle 5` on both sides and `period_end_totals` its four
  operations in declared order, all 0.

The **standalone** stage-10 re-run of §9.2 was taken again over the same published
captures, for all eight, and returned exit 0 with 0 bytes of stdout each time. The
committed test tiers were re-run on the same code and the same oracle:
`pytest -m determinism` → **8 passed**, `pytest -m scenario` → **106 passed**, and the
two together → **114 passed**, with no error and nothing skipped.

The oracle that produced this campaign is named as the one above is:
`attestation-version 2`, module-set
`29fae9a6d1700e329b5f12c589b9ab276c858ad8a1fc44b167a267c4154c3a73` over **179**
`*.so` modules, `overrides-used no`, `oracle-source-is-frozen **no**`, **41**
transformed paths, transform-set digest
`1352755276e5fca45bb74cc0441dbd777ce6b4dc3cd2634305582eb6b75ca998`. That build was
then replaced in the volume — the default frozen build was re-measured on the same
checkout (Obstacle 1, §0.0), which refreshes the build tree and fails, and a
diagnostic oracle was rebuilt afterwards at module-set
`c55f6457dd7e5533c9fbfdc6319303ce82d1ae4aa400506e24b1c1c937e833e2`, again **179**
modules and again 41 transformed paths. Two successive builds of one checkout do not
share a module-set digest, for the reason the paragraph above gives: it is a build
identity, not a behavioural fingerprint. **This campaign
is therefore NOT a parity claim either**, for exactly the reason §0.1 gives: the
verdicts were obtained under `--accept-transformed-oracle`, which `reset_db.sh`
marks `NO PARITY CLAIM` on every exit path it takes. What the campaign establishes
is narrower and worth stating plainly — that the ten stages, the provenance binding
and the eight verdicts are reproducible **from the committed tree by the documented
commands**, which is the property a reader of this register is entitled to and the
one that had been lost.

| Scenario | Declared effect | Operation status | Tables | COBOL rows | Python rows | Diff status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `clean_batch_gl` | unchanged | 0 | **22** | 8 | 8 | **`EMPTY DIFF — OBSERVED`** |
| `clean_batch_sl` | changed | 0 | **22** | 22 | 22 | **`EMPTY DIFF — OBSERVED`** |
| `clean_batch_pl` | changed | 0 | **22** | 18 | 18 | **`EMPTY DIFF — OBSERVED`** |
| `clean_batch_irs` | changed | 0 | **22** | 78 | 78 | **`EMPTY DIFF — OBSERVED`** |
| `mixed_accepted_rejected` | unchanged | 0 | **22** | 10 | 10 | **`EMPTY DIFF — OBSERVED`** |
| `period_end_totals` | changed | 0, 0, 0, 0 | **22** | 46 | 46 | **`EMPTY DIFF — OBSERVED`** |
| `control_total_mismatch` | unchanged | **5** | **22** | 8 | 8 | **`EMPTY DIFF — OBSERVED`** |
| `empty_batch` | unchanged | 0 | **22** | 7 | 7 | **`EMPTY DIFF — OBSERVED`** |

`Tables` is **22 on every row** — the full in-scope set, not the declared effect.
The declared-effect lists in §7 range from **5 to 15** tables — 5, 11, 11, 5, 5, 15,
5, 5, read from the committed `harness/scenarios/*.yaml` and totalling **62** — and are
asserted *within* each side; they do not bound the capture or the diff. The row counts
are totals across all 22 tables, which is why they differ from the earlier narrower
register even for scenarios whose behaviour did not change.

#### 8.1 All eight rows re-driven, by hand, on the build now in the volume

**Every row of the table above was re-measured on 2026-08-08**, one scenario at a
time, by driving the ten stages of §4.1 by hand — no driver script, `--all-in-scope`
and `--scenario-file` both supplied at stages 3, 7 and 10 exactly as §4.1 now shows
them — on a freshly built oracle in a freshly seeded database. **All eight returned
`identical - 22 table(s) compared, no difference` with every stage at exit 0**, and
each side's capture published the same row total the table above records: 8, 22, 18,
78, 10, 46, 8 and 7 respectively. The declared operation statuses were unchanged too,
including `control_total_mismatch`'s **5** — the abort gate firing, which is the point
of that journey. The eight run identifiers were
`parity-20260808T192406-clean_batch_gl`, `…T192435-clean_batch_sl`,
`…T192458-clean_batch_pl`, `…T192522-clean_batch_irs`,
`…T192551-mixed_accepted_rejected`, `…T192622-period_end_totals`,
`…T192658-control_total_mismatch` and `…T192724-empty_batch`.

**The oracle those eight ran against, named rather than assumed:**
`attestation-version 2`, `cobc (GnuCOBOL) 3.2.0`, `module-count 179`,
`module-set-sha256 6ad8c70226096f5c1d974ede85cecfdd1e02f62f5b3eb26eaf40892ab28656ac`,
`overrides-used no`, `oracle-source-is-frozen no`,
`source-transform-set-sha256 1352755276e5fca45bb74cc0441dbd777ce6b4dc3cd2634305582eb6b75ca998`.
The module-set digest differs from both digests quoted earlier in this section for the
reason already given there — a build identity is not a behavioural fingerprint — and
the `oracle-source-is-frozen no` line is why §0 still stands: these are agreements
with a **disclosed-transformed** oracle, and this re-measurement does not upgrade them
into parity claims against the frozen specification.

**Why this subsection exists.** A register whose rows cannot be reproduced on the tree
that carries it is a claim rather than evidence, and the rows above had last been
driven through a driver script this tree no longer contains. Re-driving all eight on
the committed stages establishes that the register describes THIS checkout: the same
eight verdicts, the same eight row totals, through the commands §4.1 publishes. The
composed route was re-run in the same session and agrees — the whole corpus, arithmetic
plus all eight scenario modules plus determinism, is **1336 passed, 0 failed, 0
skipped** inside the stack.

#### The ninth journey, measured under the narrower bound — and not committed

**THAT NINTH DEFINITION AND ITS TEST ARE NOT COMMITTED:** the Agent Action Plan's inventory names eight scenario definitions and eight scenario tests, and this tree is held to it. Everything recorded about that journey is kept because it was really driven; what a reader cannot do is re-run it from the committed set, and `gl080` consequently has **no table-state comparison** behind it.

`end_of_cycle_gl` was added after the eight above had been re-measured, and it was
driven under the **declared-effect** bound rather than the 22-table one: 5 tables,
7 rows per side, operation status 0, `EMPTY DIFF — OBSERVED`. It has **not** been
re-measured at the 22-table bound, and that is said rather than implied — the row
belongs in this register because the journey was really driven, and the bound it
was driven under belongs beside it because the two rows are not comparable
figures. Re-running the ten stages over `harness/scenarios/end_of_cycle_gl.yaml`
under the current protocol is what would unify them, and that definition is not
committed, so nobody can do it from this checkout.

#### The earlier register, measured under the declared-effect bound

The eight rows above were re-measured at the 22-table bound. They were measured
FIRST under the **declared-effect** bound — the capture and the diff covered only
each scenario's own `affected_tables` — and that campaign is kept here rather than
overwritten, because its rows were really driven and its artifacts were really
published. **Each of its rows is identified by the run id its evidence was
published under, not by a date**: a date cannot be checked against anything,
whereas a run id is recorded in every artifact that run produced and can be read
back. The rows above are identified the same way where a run id was recorded, and
otherwise by the normalised-tree manifest digests quoted with each scenario in §7,
which are equally checkable.

| Scenario | Declared effect | Operation status | Tables | COBOL rows | Python rows | Run id | Diff status |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `clean_batch_gl` | unchanged | 0 | 3 | 6 | 6 | `parity-3a616c4d9705408c` | **`EMPTY DIFF — OBSERVED`** |
| `clean_batch_sl` | changed | 0 | 10 | 21 | 21 | `parity-53e923f47c8b4a83` | **`EMPTY DIFF — OBSERVED`** |
| `clean_batch_pl` | changed | 0 | 10 | 17 | 17 | `parity-62fc68042cf24e75` | **`EMPTY DIFF — OBSERVED`** |
| `clean_batch_irs` | changed | 0 | 4 | 50 | 50 | `parity-41d424b42c534c54` | **`EMPTY DIFF — OBSERVED`** |
| `mixed_accepted_rejected` | unchanged | 0 | 3 | 8 | 8 | `parity-c38285f9ca354767` | **`EMPTY DIFF — OBSERVED`** |
| `period_end_totals` | changed | 0, 0, 0, 0 | 14 | 45 | 45 | `parity-20dac0f23e634c22` | **`EMPTY DIFF — OBSERVED`** |
| `control_total_mismatch` | unchanged | **5** | 3 | 6 | 6 | `parity-babbabb4b455483b` | **`EMPTY DIFF — OBSERVED`** |
| `empty_batch` | unchanged | 0 | 3 | 5 | 5 | `parity-cf6383cb1624400e` | **`EMPTY DIFF — OBSERVED`** |

Eight scenarios, eight empty diffs, **`exit 0` on all eight**. The row counts are
per side and are equal on every row, which is a necessary but not sufficient
condition — the verdict is the row-by-row comparison, not the count. The counts are
lower than the 22-table register's for the same scenarios for exactly the reason the
bound differs: rows in tables outside the declared effect were never captured.

#### How the DECLARED lists changed, and why every table count above moved

The declared-effect lists were first recorded on 2026-08-04. Afterwards the tables
the menu shell rewrites on exit were brought inside each scenario's declared
effect, which added `SYSTEM-REC` to all of them and `SYSDEFLT-REC` to the General
Ledger ones. The deltas are uniform and each predicts its own row delta exactly,
because `SYSTEM-REC` holds one row in these seeds and `SYSDEFLT-REC` holds none:

| Scenario | declared then | declared now | what was added |
| --- | --- | --- | --- |
| `clean_batch_gl` | 3 tables | 5 | `SYSTEM-REC` + `SYSDEFLT-REC` |
| `clean_batch_sl` | 10 | 11 | `SYSTEM-REC` |
| `clean_batch_pl` | 10 | 11 | `SYSTEM-REC` |
| `clean_batch_irs` | 4 | 5 | `SYSTEM-REC` |
| `mixed_accepted_rejected` | 3 | 5 | `SYSTEM-REC` + `SYSDEFLT-REC` |
| `period_end_totals` | 14 | 15 | `SYSTEM-REC` |
| `control_total_mismatch` | 3 | 5 | `SYSTEM-REC` + `SYSDEFLT-REC` |
| `empty_batch` | 3 | 5 | `SYSTEM-REC` + `SYSDEFLT-REC` |
| `end_of_cycle_gl` *(since removed)* | — | 5 | the scenario itself was new |

**That total is a cross-check, not a decoration.** The eight committed lists hold
**62** `affected_tables` entries between them, counted from the YAML rather than
from any run log. The historical cross-check below was performed on the nine lists that
then existed and summed to 67 on both counts, and is left at the figures it was
performed on. Two unrelated
sources agreeing is what makes the figure a measurement instead of a
transcription.

### 8.0 What an empty diff here does and does not establish

Read with §13, which states the coverage limits. Two rows deserve a caveat
attached to them directly rather than left to a later section:

- **`clean_batch_gl` and `mixed_accepted_rejected` are empty diffs over a
  deliberate no-op, and are NOT evidence that GL posting arithmetic agrees.**
  The abort gate stays shut and all three phases run — the term code is `0`, which
  is itself a real and asserted result — but no ledger balance moves, because a
  frozen bridge defect means a seed can persist at most one `GLPOSTING-REC` row
  and that row's posting key does not survive the round trip in a form `gl070`
  will accept. `initialize TD-GLPOSTING-REC` never loads `HV-POST-RRN`
  `[common/glpostingMT.cbl:L1053-L1066]` while `POST-RRN` is the primary key
  `[mysql/ACASDB.sql:L155,L169]`, and the ten-byte group `WS-Post-Key` is moved
  into `HV-POST-KEY PIC 9(18) COMP` `[common/glpostingMT.cbl:L283]` over the
  maintainer's own recorded doubt about that field
  `[common/glpostingMT.cbl:L229]`. Reproducing the no-op is **correct** under R-4;
  citing it as posting parity would not be. Measured directly: after the run
  `GLBATCH-REC` still holds `CLEARED-STATUS 0` and `POSTED 0`, and all four
  `GLLEDGER-REC` balances are `0.00`, on **both** sides.
  The cause is recorded as anomaly **A-NEW-18**, working alias **`N-KEY`**, in
  [`anomaly-log.md`](anomaly-log.md), which carries the chain link by link with
  each link measured; it is named here by identifier rather than only derived,
  because a defect that is merely derived in passing is a defect nobody can cite.
  Consequence to state plainly: **no scenario in this register demonstrates a
  General Ledger balance moving**, so AAP §0.8.5's "clean batch post per ledger"
  is met for Sales, Purchase and IRS but only at the gate-and-term-code level for
  the General Ledger. The GL double-entry explosion and ledger accumulation are
  held by the arithmetic tier instead —
  `tests/arithmetic/test_double_entry_explosion.py` and
  `test_ledger_balance_accumulation.py` — and the open cursor/key-of-reference
  questions remain recorded in `ambiguity-resolutions.md`.
  **The shortfall is LOCKED rather than only narrated**, because narration alone
  would leave nothing to fail. An empty diff is symmetric — it passes whether
  the two sides agree on a no-op or on a balance movement — so it can be cited as
  evidence for neither.
  `tests/scenarios/test_clean_batch_post_gl.py::test_the_gl_route_leaves_the_measured_no_op_on_both_sides`
  therefore asserts the measured outcome **absolutely and per side**: every
  `GLLEDGER-REC` balance zero, the seeded `GLBATCH-REC` row unstamped, and at most
  one `GLPOSTING-REC` row with `POST-RRN` zero. If the frozen path ever changes, or
  a fixture begins reaching the posting walk, that test fails and this paragraph is
  re-examined instead of being inherited unread.
- **`control_total_mismatch`'s empty diff is the point of the scenario, not a
  weakness.** AAP §0.6.5 makes absence the expected database effect of a
  run-aborting rejection, and status `5` was asserted.

The other four rows — `clean_batch_sl`, `clean_batch_pl`, `clean_batch_irs` and
`period_end_totals` — do move rows: the seed-to-dump row deltas are +4, +2, +5 and
+11 respectively, so those diffs are empty over states that genuinely changed.

**FOUR NAMES, NOT FIVE.** Counting "The other **five** rows" by including "and, for
its rejection witness, `mixed_accepted_rejected`" sets five names against four deltas
and contradicts this same document elsewhere. Measured from the scenario files,
`mixed_accepted_rejected` declares `expected_table_effect: unchanged`, as do
`clean_batch_gl`, `control_total_mismatch` and `empty_batch`. Its rejection witness is
real, but what it witnesses is an **absence** of rows — which is precisely why it
belongs with the unchanged group and not here. `end_of_cycle_gl` was the fifth scenario
that declared `changed`; it is absent from the delta list because no re-measured
delta exists for it (§8 records `—`, and §10.9 carries its evidence), so it is named
here rather than given a fabricated figure. It is not committed, which leaves four
`changed` scenarios in the committed set.

The **harness wrapper status** is distinct from the **operation status**. A
wrapper exits 0 once it has verified that the operation produced the status the
scenario declares — including the behavioural status **5** in
`control_total_mismatch`, where a non-zero operation status is the correct
outcome and a zero would be the failure. Both sides recorded `wrapper_status 0`
and `behavioural 0` on all eight while `control_total_mismatch` recorded
`operation status 5` on both: the wrapper being healthy and the operation being
rejected are two different facts, and the artifacts state them separately.

`period_end_totals` is the row that proves the operation list is driven rather
than assumed. Its attestation records **four** ordered operations on **both**
sides — `1. sl_invoice_post=0`, `2. sl_cash_post=0`, `3. pl_order_post=0`,
`4. pl_payment_post=0` — spanning the Sales and Purchase menu executables, from
one seeded state, in one invocation per side.

### 8.1 The digests behind each row

Every row above is backed by a verdict manifest that names these values; each is
reproduced here truncated to 16 hex characters, and in full in the manifest.
`harness/diff_states.py` **refused to compare a single row** until the run id,
the scenario-file digest, the frozen-schema digest and the seed-marker digest
were present and equal on both captures, so the equalities below are enforced
rather than reported.

**THE TABLE BELOW WAS RE-MEASURED, and the values it replaces are gone rather than
annotated.** The eight rows of an earlier campaign published `scenario_file_sha256`
values — `a50865132df8658f…`, `0b87e710c8b29548…`, `63a872463825d681…`,
`c5be8d899a3d3f31…`, `aad64731a00f59cb…`, `feaea8ab20ba6465…`, `0661d2972920ee77…`
and `ff40cd124054322c…` — that no longer matched **any** committed definition, because
the scenario files were edited after those runs. By this section's own criterion the
evidence was stranded on every row, so re-driving was the only honest repair: quoting
a digest that cannot be recomputed is worse than quoting none. Every value below comes
from one invocation of the committed scenario tier —
`python3 -m pytest -m scenario` inside the `gnucobol` service, **106 passed, exit 0**
— which composes the identical ten stages per scenario.

| Scenario | Run id | Seed marker | Scenario file | COBOL manifest | Python manifest |
| --- | --- | --- | --- | --- | --- |
| `clean_batch_gl` | `pytest-86eca2ca889b4fc8` | `fdbf3391fa358afd…` | `4dc212c6ee8b67d5…` | `c0a9b6ac3c0c6e7b…` | `a00886406ef69ac3…` |
| `clean_batch_sl` | `pytest-6decf920987f4ff2` | `21aa862c20934250…` | `47bc51e09dd620a1…` | `7c4b26b15c208181…` | `bf076cf2f7e918e9…` |
| `clean_batch_pl` | `pytest-878f3b2549754221` | `82afd49c3d4bc8ce…` | `df6d10de7ac047a1…` | `36567667177ae696…` | `cd3b7356fbd5c9cd…` |
| `clean_batch_irs` | `pytest-57fcb70d80134c08` | `a7f84f8b33e8ae6c…` | `5630038bf1895866…` | `293afd176c0ad40e…` | `10c908d6f5ca2d1f…` |
| `mixed_accepted_rejected` | `pytest-73751efffdb344c2` | `b3b60f4774f55c7a…` | `685360d5d801de5a…` | `5b4ba3d3d4af3d0b…` | `ec8304a528815fc9…` |
| `period_end_totals` | `pytest-02be037ebf5440dc` | `c116b605a42f55c4…` | `f79d4760a70b490d…` | `6f27b8acab896a15…` | `f6384c0b1be2025d…` |
| `control_total_mismatch` | `pytest-9c33f2526ddf486b` | `773b5d7cba2841e1…` | `0b01e4ae7f6fe827…` | `385328068f3b715a…` | `7590ed201677d3c2…` |
| `empty_batch` | `pytest-f7d521b78afb432c` | `88a13288d7a92e43…` | `b3136a15473a0ec3…` | `cd3c7d5f82a0e717…` | `8a35b0be3e8fc037…` |

**Two of those columns are reader-checkable and three are not, and the difference is
worth naming before the properties below.** `Scenario file` and the frozen-schema
digest are functions of committed bytes, so a reader recomputes them with
`sha256sum` and needs nothing else. `Run id`, `Seed marker` and the two manifest
digests identify **one run**: the seed marker digests the staged fixture files, and a
manifest embeds the run id and the command, so both change on every invocation by
design. Do not read a differing manifest digest as a contradiction — read the
`Scenario file` column, which must match and does.

Four properties of that table are worth stating because each closes a way the
evidence could have been hollow:

- **The scenario-file digests match the definitions in this checkout.** Each
  `scenario_file_sha256` above equals the SHA-256 of the corresponding
  `harness/scenarios/*.yaml` **as committed** — verified for all eight by recomputing
  `sha256sum harness/scenarios/<scenario>.yaml` and comparing it to the value the run
  published, 8 of 8 equal — so these runs were driven by the scenario definitions a
  reader can open, byte for byte. This matters because editing a scenario file, even
  in a comment, changes the digest and would strand the evidence, which is exactly
  what had happened to the superseded values named above.
- **The frozen schema digest is one value across all eight**,
  `094e588226f650672c3781d1737d7bf8be30be048ce6a788df81800a19326ed0`, and it
  equals the SHA-256 of `mysql/ACASDB.sql` in this checkout. One schema, unaltered
  under the protocol, as AAP §0.8.1 requires.
- **The seed marker is equal across the two sides of every row and differs
  between scenarios.** Equality across sides is what makes "both cycles started
  from byte-for-byte the same state" a checked fact rather than an assumption.
  Difference between scenarios shows the eight are eight distinct fixtures.
- **The two manifest digests differ within every row**, necessarily — the two
  captures record different `side` values and different commands. It is the
  *provenance* fields that must agree, not the manifests as wholes.

One deliberate subtlety: `clean_batch_gl` and `control_total_mismatch` publish
the **same** pre-run row-count fingerprint, because both bound the same three GL
tables at the same counts, while their **seed markers differ**
(`3d57704b…` against `c928163b…`). That is precisely why the row-count
fingerprint is not the binding identity: two seedings of the same shape and
different values share it. The marker is a digest per seeded file, so it
separates them. The protocol requires both.

### 8.2 Term code 5 is the only observable term code, and that is provable

`[general/gl070.cbl:L289]` is `move 5 to ws-term-code`, raised when phase one
finds a batch left open. The menu tests it at `[general/general.cbl:L810-L811]`
— `if ws-term-code = 5 / go to display-menu.` — with the effect AAP §0.6.4
records: "`gl071` and `gl072` never run at all."

Term code **8**, the only other code the in-scope set can raise, is
**unreachable** in this harness, because both of its raise sites sit inside an
`if FS-Cobol-Files-Used` block: `[sales/sl055.cbl:L326]` wraps the raise at
L344, and `[purchase/pl055.cbl:L266]` wraps the raise at L286. With
`file_system_used` pinned to **1**, `FS-Cobol-Files-Used` is false and neither
raise can execute.

Therefore **5 is the only non-zero term code any scenario in this register can
observe**, and every other scenario's expected term code of `0` is *provable*
rather than assumed. That matters because it closes the false-pass route in which
a run silently took the flat-file path. Observed across the **nine** runs then
committed: the
eight single-operation scenarios plus `period_end_totals`' four operations are
**twelve** operations in total, and the declared status was `0` **eleven** times
and `5` exactly once. Over the committed **eight** the same census is **eleven**
operations, `0` ten times and `5` once; the difference is the single operation
the uncommitted ninth scenario contributed.
`acas_posting/cli/args.py`'s `exit_status_for(term_code)` returns `0` for `0` and
the term code itself otherwise.

For a run-aborting rejection AAP §0.6.5 states the database effect directly:

> "The database effect is therefore *the absence* of everything the later phases
> would have written."

**Absence is evidence.** An empty diff over the **22** in-scope tables that both
sides left alone is a real result, not a vacuous one, because the seed was
non-empty, the fingerprints matched, the clock was read back and the term code was
asserted. The bound matters to this claim: three tables left alone would say
nothing about the other nineteen, whereas twenty-two leaves nowhere for an
unexpected write to hide.

## 9. How the evidence was produced

The ten stages of §4.1 are driven for one scenario under one run id, bound to every
stage that publishes an artifact, stopping at the first non-zero — except at stage 6
with exit 69, where a behavioural difference is recorded and the run continues so the
diff can localise it, and after which the result can never be parity (§4.1). One
scenario at a time, sequentially — no `&`, no `xargs -P` (R-3).

**The runs recorded in §8 were invoked through a `harness/run_parity.sh` driver, which
is not part of this tree.** The command below is preserved as the historical record of
how those figures were produced; the equivalent today is the ten-stage recipe in README
§11.1, under "The operator contract", which is the same commands in the same order with
the run id and the staged data bound explicitly:

```bash
for s in clean_batch_gl clean_batch_sl clean_batch_pl clean_batch_irs \
         mixed_accepted_rejected period_end_totals control_total_mismatch \
         empty_batch end_of_cycle_gl; do
  /repo/harness/run_parity.sh \
      "/repo/harness/scenarios/$s.yaml" \
      --seed-dir "/data/fixtures/$s"
done
```

The loop is written over the names rather than over a glob so that adding or
removing a scenario file cannot silently change what this section claims was run.
It names **nine** because nine scenario files existed on the run date; the ninth,
`end_of_cycle_gl`, is not committed, so `harness/scenarios/*.yaml` — which is the
authority on how many scenarios exist — holds **eight**. The disagreement between the
two counts is that absence, not an error in either.

It carries **no** `ACAS_SEED_AUTOCOMMIT` setting, and on the run date that was
sufficient rather than optional: the shipped default then SELECTED the durable window,
so an unset variable seeded durably and the command listing is faithful to the run it
records. **That is no longer how the default reads, and the difference matters to
anyone re-running it.** The seeding window must be **on**: the frozen loaders reach
no `COMMIT` — every `perform aa030-Commit` in all 28 `common/*LD.cbl` loaders is
commented out — so under the AAP-mandated `off` window the seed leaves no durable row
and the gate refuses to carry an all-empty capture forward, exiting **76** rather than
proceeding. That window is now the **default**: `harness/seed.sh` resolves the unset
variable to `off`, nothing in `harness/docker-compose.yml` or either Dockerfile pins
the mode, and an explicit `ACAS_SEED_AUTOCOMMIT=on` is what reaches the durable one.
So the loop exactly as printed above would stop at stage 1 with exit 76. **The
equivalent command today therefore adds `-e ACAS_SEED_AUTOCOMMIT=on`**, exactly as
§15's reproduction commands do; §4.3 records the measurement behind the default and
why the deviation is requested per invocation rather than pinned. The flag is omitted
from the listing above only because the listing shows what this section's run actually
invoked, and it is stated here rather than left to be discovered.

To be exact about *why* the historical listing above omits it: on the run date
the harness defaulted to `on`, so omitting the flag was correct then and the
listing is a faithful record. The default was subsequently moved to the
AAP-mandated `off`, which is what makes the same listing insufficient now. An
earlier record of this section showed
the variable set explicitly, which was accurate for that earlier run; it is not shown
here because it was not used here, and a command listing that includes a setting the
run did not use — or one retro-fitted with a setting it lacked — is a command listing
a reader cannot trust.

It also carries no `--allow-unattested`: every run verified the oracle
attestation of README §8.9 before stage 2, which is why §8 can name the module-set
digest that produced it.

Every one of the **nine** journeys then committed completed **stages 1 through 10, all
exit 0**, and
printed the driver summary "the two states are IDENTICAL — an empty diff, which is
the pass condition and the only one (AAP section 0.8.5)" — `verdict state =
identical`. Each also published a retained `parity-result` record — `claim
identical`, `stages_requested 1 10`, `first_failing_stage_status 0`,
`behavioural_status 0` — written by the driver of the day, which is not part of this
tree. Those files remain on the volume because the runs produced them; nothing writes
one now, and `verdict.json` is the published claim.

### 9.1 The toolchain that produced it

| Component | Version | Where |
| --- | --- | --- |
| GnuCOBOL `cobc` | **3.2.0** | inside the builder image only; **absent from the host** (R-1) |
| CPython | **3.12.3** | recorded in every manifest's `provenance.python_version` |
| MariaDB | **10.11.7** | the version `mysql/ACASDB.sql` was produced by |

### 9.2 Stage 10 re-run standalone, with attestation enforced

Stage 10 was then re-run standalone for all nine then committed, deliberately **without**
`--allow-unattested`, so that the attestation requirement was enforced rather
than waived:

```bash
python3 /build/harness/diff_states.py \
    --scenario "$s" --out-dir /out \
    --scenario-file "/repo/harness/scenarios/$s.yaml"
```

Result for all nine: **exit 0 with stdout of exactly 0 bytes** — the diagnostics
go to stderr, so stdout carries the report and nothing else. Both halves of the
pass condition were therefore checked independently: the exit code *and* the
emptiness.

Two further observations from that re-run, both of them properties rather than
restatements:

- **`diff.txt` is 0 bytes on all eight**, and its recorded digest is
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` — which is
  the SHA-256 of the empty byte string. "Empty diff" is therefore literal here,
  not a turn of phrase: the report file has no contents, and the digest a reader
  can compute independently says so.
- **The verdict manifests were byte-identical to the ones the driven protocol had
  already published**, field for field, for all eight. Re-deriving a verdict from
  the retained captures reproduces it exactly, which is the determinism property
  observed at the artifact level rather than only inside a test.

**Re-measured on the code as committed, 2026-08-08, and one thing about the command
above needs saying.** The command was re-run verbatim over the captures of the
eight-scenario campaign recorded in §8, and returned **exit 0 with stdout of exactly
0 bytes for all eight**. But it carries no `--all-in-scope`, so what it compared was
each scenario's **declared effect** and not the protocol's bound: 5 tables for
`clean_batch_gl`, `clean_batch_irs`, `mixed_accepted_rejected`,
`control_total_mismatch` and `empty_batch`, 11 for `clean_batch_sl` and
`clean_batch_pl`, 15 for `period_end_totals`. The same eight captures compared at the
protocol's own bound — the form README §11 documents, and the only form whose verdict
is the pass condition of AAP §0.8.5 — returned **exit 0 with 0 bytes of stdout over 22
tables** for every one:

```bash
python3 /repo/harness/diff_states.py \
    --scenario "$s" --all-in-scope \
    --scenario-file "/repo/harness/scenarios/$s.yaml"
```

Both forms are recorded because both were run, and the difference between them is
the point: a narrower bound cannot show a difference in a table the scenario did not
expect to move, so the 22-table form is the one a reader should use and the one §8's
rows were measured under.

### 9.3 Where the run artifacts were written — and why none of them is in this repository

**Nothing in the table below is a committed artefact.** Every path is under
`$ACAS_OUT`, which is the Docker named volume `acas-harness-<CLONE_INDEX>-out`,
mode 600, deliberately outside the checkout (§14.1). The volume belongs to one
clone of one machine, so no `git add` can capture these files and a reader of this
repository cannot open them. What this section documents is therefore the *shape*
of what a run writes — the names, the fields and the run-id binding by which a
future run's artifacts can be tied back to a row of §8 — not a set of files the
reader is invited to inspect. Every digest quoted from them elsewhere in this file
is a report of an observed run, and §8's preamble says so in those terms.

| Artifact | What it carries |
| --- | --- |
| `<scenario>/verdict.json` | The machine-readable verdict: outcome, exit code, tables compared, differing and total differences, run id, the five digests of §8.1, and — from `verdict_version` 2 — the **oracle disposition** `oracle_source_is_frozen` with `source_transform_set_sha256`, copied verbatim from the compiled side's manifest provenance, itself copied from `$ACAS_BUILD/oracle-attestation.txt`. On this checkout it reads `no`, so **every verdict in this document carries its own NO-PARITY-CLAIM statement** rather than relying on the reset stage's shared log to carry it. `None` there means no attestation was reachable and is deliberately distinguishable from `yes` |
| `<scenario>/parity-result` | **Driver-composed runs only.** A `run_parity.sh` driver's retained claim, stages requested, first failing stage status, behavioural status and verdict path. No stage in this tree writes this file; `verdict.json` above is the published claim, and the trees recorded in §8 retain theirs because the runs really produced them |
| `<scenario>/diff.txt` | The report. **0 bytes on all eight** |
| `<scenario>/{cobol,python}/_manifest.json` | The dump-stage manifest per side |
| `<scenario>/{cobol,python}.normalized/_manifest.json` | The normalise-stage manifest per side — the two whose digests §8.1 lists, and the two stage 10 actually compared |
| `run-logs/<scenario>/{cobol,python}.run-status` | Wrapper status, behavioural status, seed digests and the ordered per-operation statuses |
| `run-logs/<scenario>/{cobol,python}.operation-status` | The ordered operation list and each operation's observed status |
| `run-logs/<scenario>/seed-identity` | The fixture marker digest the reset stage published, under this run id |

### 9.4 Assertions the runners made on every run

These are the non-vacuity guards. Each was observed **9/9** unless noted:

- `SYSTEM-REC` holds `Run-Date 155127`, read back **from the database** after the
  run — so the pinned clock is witnessed in stored state, not merely supplied.
- The fan-out switch still holds a space, before and after.
- `FILE-SYSTEM-USED = 1` pre-run, closing the flat-file false-pass route.
- The `Cyclea`/`Scycle` shared-storage view agrees, pre- and post-run.
- The autogen tables hold 0 rows — but **the two sides probe different sets,
  and one of them is conditional**, so this is the one bullet on the list that is
  not a flat 8/8. The **Python** runner counts all four on every run:
  `SAAUTOGEN-REC`, `SAAUTOGEN-LINES-REC`, `PUAUTOGEN-REC`, `PUAUTOGEN-LINES-REC`
  `[harness/run_python_scenario.sh ACAS_PY_AUTOGEN_TABLES]`, probed in
  `[harness/run_python_scenario.sh acas_py_assert_after_run]`. The **COBOL** runner counts only
  the Sales pair `[harness/run_cobol_scenario.sh ACAS_RUN_AUTOGEN_TABLES]`, and only when the
  subsystem is `sales` `[harness/run_cobol_scenario.sh acas_assert_after_run]` — so 2 tables on
  `clean_batch_sl` and `period_end_totals`, and none on the other six. That
  asymmetry is deliberate and matches the asymmetry it exists to bound: only the
  Sales menu calls `sl830`, and Purchase's equivalent call is commented out in the
  frozen source. A count that cannot be taken is **noted, not failed**, since the
  tables are out of scope and their absence is not this stage's business to
  repair. Bounding this by `count(*)` rather than by a dump is also necessary
  rather than stylistic: all four tables are out of scope, so
  `harness/dump_tables.py` refuses them with `EX_SCOPE = 83` — see
  [`ambiguity-resolutions.md`](ambiguity-resolutions.md) `Q-6`.
- The pre-run affected-table state is non-empty and canonically fingerprinted,
  and **both sides started from the same row counts and the same per-table
  digests** — the digest being what rules out equal counts over different values.
- The post-run state was fingerprinted with the same producer, and each side's
  observed effect matched the scenario's declared `expected_table_effect`.
- No bytecode cache directory was created inside the checkout.

And from `harness/reset_db.sh` at both reset stages: the frozen schema applied
verbatim; 33 tables recreated; all 33 empty before the seed; **no secondary index
on the 22 in-scope tables**; collation `utf8mb3_general_ci` intact on all 33; all
22 in-scope table shapes matching the frozen schema; **zero nullable columns**;
**zero binary floating-point columns**; autocommit still 1/1 after the apply; and
the schema durable in a fresh session.

## 10. Per-scenario evidence

**Read §0 first. Every observation in this section was made against the
DISCLOSED-TRANSFORMED DIAGNOSTIC oracle, never against the frozen specification, and
every digest it cites identifies a file on the harness `out` volume rather than a
retained repository artefact.** The entries are reports of runs that were watched; they
are not re-verifiable from this checkout.

Each entry records seed, pinned clock, pinned IRS fan-out, affected-table list,
expected and observed term code, the anomalies it **witnesses in state**, and its
diff status. The clock is `21/09/2025` / `Run-Date 155127` and the fan-out is a
single space in **all eight**, per §6; they are restated per entry because the brief
for this register requires each entry to stand alone.

**WITNESSED, NOT LOCKED — and blurring the line is the easy mistake.**
Every row in this section is an observation of **end state** from a parity run, so
what it establishes is that the two implementations AGREED — which is real evidence
and is why the rows are kept. It is not the same as a **lock**, which asserts the
defect itself so that repairing the defect turns the suite red. A state comparison is
**symmetric**: it passes whether the two sides agree on a defect or on a repair
applied to both, and for a defect with no state signature — a file close, a clean
rejection, an at-end rewrite on a key no row carries — it cannot distinguish them at
all. `anomaly-log.md` §11 is the authority for which test **owns** each anomaly, and
the rows below name the tier where a lock lives whenever the two differ. An earlier
revision of this section headed these rows "Anomalies locked" and, on two GL routes,
credited an anomaly while stating in the same sentence that it was *"not reached on
this route"* — which cannot both be true.

### 10.1 `clean_batch_gl`

- **Operation:** `gl_post_cycle` — `gl070`, the term-code gate, `gl071`,
  `gl072`, in that order.
- **Modules exercised:** `gl070_transaction_pre_process.py`,
  `gl071_batch_sort.py`, `gl072_transaction_update.py`, via
  `acas_posting/cli/gl_post_cycle.py`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat`.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space — neither `IRS-Used` nor
  `IRS-Both-Used`.
- **Affected tables:** the 5 of §7.1 — `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed term code:** 0.
- **Anomalies witnessed in state:** **A-14** (the sequential nominal read).
- **Named here but NOT witnessed by this route:** **A-NEW-8**. This route issues
  **no `Open-Output` on either General Ledger table** — the only such verb in the
  whole General Ledger family is `GL-Posting-Open-Output` in `gl080`
  `[general/gl080.cbl:L673]`, which belongs to `end_of_cycle_gl` and not to the
  posting cycle — so the batch row's survival witnesses nothing about it. The
  earlier text credited this route with witnessing A-NEW-8 on the reading that
  GL-Batch `Open-Output` leaves `GLBATCH-REC` intact; measurement contradicts that
  reading, and §15.3 of [`anomaly-log.md`](anomaly-log.md) records the correction.
  Asked for an `Open-Output`, `acas007` empties `GLBATCH-REC` of every key strictly
  below 999999 — nothing on this route asks it.
- **Named here but NOT witnessed by this route:** **A-13**, the two entirely silent
  skips. They are **not reached** — A-NEW-18 starves `gl070`, so `gl072` takes at end
  on its first read and never evaluates either skip — so calling A-13 "locked" by this
  route would contradict the same sentence that says it is unreached. Its lock is
  `tests/arithmetic/test_ledger_balance_accumulation.py`, which drives both branches
  directly with a facade double.
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 3 tables, 6 rows each side.

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`086715e6483c37860b7e980c3fc2a83079ce2f84889ba8312c91d178c91e5869`, Python
`288ddb8ebb9bf405393eaeb508b278485ff7163f9f29d209aa100f1542ca1681`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-3a616c4d9705408c`, compared COBOL
`1aad0c87164b81099c1de8a096530c3fc7d195ea42e9941644f1a9a8d0826fa4` against Python
`9d6ea9d748170fdb2e2081b5bd936a158bd8de6a9087e16b6e1ceee8b33a74ec`, and its `verdict.json` cites both.

**Why the effect is "unchanged", and why that is still evidence.** The scenario
seeds a **closed** batch. Phase one walks the batch file and raises the terminate
code only if it finds a batch left open, so nothing is raised and the term code
stays 0. Phase two then applies a *stricter* filter than phase one and rejects the
batch: `if status-open / or not waiting / or not gl-batch / go to loop`. Nothing
is posted, and all three tables are byte-state unchanged on both sides. The runner
asserted each one individually and then asserted the aggregate: "the deliberate
no-op/rejection left every affected table unchanged."

A second, measured reason the route is a no-op is recorded at **`Q-9`**:
compiled measurement established that the bridge's host-variable load does not
move `WS-Post-rrn` into `HV-POST-RRN`, so the one reachable posting is persisted
under key zero and skipped by the guards at
`[general/gl070.cbl:L490-L493]`. The end-batch rewrite at
`[general/gl072.cbl:L372-L377]` is consequently unreachable and `POSTED` remains
zero. **That is reproduced, not corrected** (R-4), and it is why the determinism
witness reads the pinned clock from `SYSTEM-REC.RUN-DAT` rather than demanding a
batch timestamp the zero-key posting can never reach.

### 10.2 `clean_batch_sl`

- **Operation:** `sl_invoice_post` — `sl055` then `sl060`.
- **Modules exercised:** `sl055_invoice_extract_analysis.py`,
  `sl060_invoice_posting.py`, via `acas_posting/cli/sl_invoice_post.py`.
- **Seed:** `system.dat`, `analysis.dat`, `value.dat`, `salesled.dat`,
  `invoice.dat`, `openitm3.dat`.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space, so the fan-out guards at
  `[sales/sl060.cbl:L1039]`, `L1126` and `L1175` are all false.
- **Affected tables:** the 11 of §7.1.
- **Expected and observed effect:** changed.
- **Expected and observed term code:** 0.
- **Anomalies witnessed in state:** **A-8** (double truncation of the
  moving average), **A-9** (the credit-note average that never increments its
  counter), **A-10** (three mutually inconsistent guards on one idiom), **A-11**
  (the signed value narrowed to an unsigned host variable and column), **A-12**
  (the bridge that trims), **A-18** (two percentage fields not carried into the
  IRS posting record).
- **A-1 is WITNESSED here and LOCKED elsewhere**, and the distinction carries the whole
  weight. This is the one route on which A-1 — the missing terminating period
  that swallows the General Ledger posting close in pure-GL mode — is even reachable,
  and `GLPOSTING-REC` agreeing on both sides is worth recording. But
  `GL-Posting-Close` **writes nothing**, so adding the missing period leaves an
  identical dump and this route passes either way. A-1's lock is
  `tests/arithmetic/test_double_entry_explosion.py`, which asserts the verb
  sequence over the full `IRS-Instead` × `Level-1` truth table.
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 10 tables, 21 rows each side.

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`f03b5f6d951a3f08398041672706e1c0e25cc906994bf2c0eaa20bbf4ed85d97`, Python
`95cf5c05463988f7e01063952b1dfbcf32b980e6106df8014bfaa630e40d0400`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-53e923f47c8b4a83`, compared COBOL
`43d89ba2daddfe7a47859f394c7bd058307bf6bb082c45632d948f94deda0b80` against Python
`92b4bb80e59108cb526c758f1af91b609ed6e3fb0c95db27f3ab29e8b280c0e5`, and its `verdict.json` cites both.

**The `sl830` asymmetry, and how it is closed rather than ignored.**
`[sales/sales.cbl:L759]` is `move "sl830" to WS-Called.` and it is dispatched
**before** `sl055`, so the autogen program runs on the COBOL side and has no
counterpart on the Python side. The autogen tables are never seeded and never
listed as affected. Both runners therefore **assert after the run** that the
autogen tables are still empty — the Python side counting all four, the COBOL side
counting the Sales pair `SAAUTOGEN-REC` and `SAAUTOGEN-LINES-REC`, which are the
two `sl830` could have written (§9.1 gives the locators for both probes and
explains why the sets differ). That assertion was **observed to hold**, with the
COBOL side recording it against the frozen requirement: "SAAUTOGEN-REC holds 0
rows — `sl830` was a no-op, as `[sales/sl830.cbl:L270-L272]` requires",
`[sales/sl830.cbl:L270]` being `goback.`. A **pre-run** gate makes the result
binding rather than lucky: the COBOL runner reads `SYSTEM-REC.SL-AUTOGEN` before
the run and refuses the scenario if it is `"Y"`, on the ground that the Sales
invoice path would then be non-deterministic. This closes **`Q-6`**, and the
closure is conditional on that switch-off state by construction. Purchase has no
such asymmetry: its `pl830` dispatch is commented out at
`[purchase/purchase.cbl:L755-L758]`.

**The probe is a `count(*)`, not a dump, and it has to be.** All four autogen
tables are among the eleven AAP §0.2.2 places out of scope, so
`harness/dump_tables.py` refuses every one of them with `EX_SCOPE = 83` — a
correct refusal, since the diff is defined over the tables a scenario declares.
`Q-6` in [`ambiguity-resolutions.md`](ambiguity-resolutions.md) records why that
impossible dump is the tempting proposal.

`PSIRSPOST-REC` ends the run with **0 rows on both sides**, which with the
fan-out pinned to a space is the correct outcome: no IRS posting is fanned out at
all. Empty on both sides is a pass; empty on one side only would be a real
failure.

### 10.3 `clean_batch_pl`

- **Operation:** `pl_order_post` — `pl055` then `pl060`.
- **Modules exercised:** `pl055_order_proof_extract.py`,
  `pl060_order_posting.py`, via `acas_posting/cli/pl_order_post.py`.
- **Seed:** `system.dat`, `analysis.dat`, `value.dat`, `purchled.dat`,
  `pinvoice.dat`, `openitm5.dat`.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space.
- **Affected tables:** the 11 of §7.1.
- **Expected and observed effect:** changed.
- **Expected and observed term code:** 0.
- **Anomalies witnessed in state:** **A-10**, **A-12** and **A-17**.
- **NOT witnessed by this route: `pl060`'s phase-1 OTM5 build.** The fixture's two
  open items reuse the invoice numbers `pinvoice.dat` carries, 1 and 2, and `OI5-KEY`
  is supplier plus invoice only `[copybooks/plwsoi5B.cob:L13-L15]`, so phase 1's
  `perform OTM5-Write` `[purchase/pl060.cbl:L522]` lands on keys the seed already
  occupies: fs-reply 22, and the program displays `PL130`
  `[purchase/pl060.cbl:L253,L527]`. Both sides seed identically and both take the
  identical duplicate-key path, so **the empty diff below is sound** — but the phase-1
  build itself is unobserved here, and the `PUITM5-REC` rows compared are the seeded
  ones as phase 2 left them. The Sales sibling avoids the collision by seeding invoice
  numbers 10 and 11; `[harness/scenarios/clean_batch_pl.yaml]` records why the same
  change is not applied to this fixture without a fresh protocol run to re-attest the
  digests below.
- **A-1's CONTROL route, witnessed not locked.** `pl060`'s terminating period **is**
  present at `[purchase/pl060.cbl:L1031]`, and that divergence from `sl060` is
  preserved rather than normalised — the three-to-one split across the four sibling
  sites is what makes A-1 an accident rather than an idiom. As on the Sales route, a
  close leaves no state, so this is a witness; the lock is the shipped-paragraph truth
  table named in §10.2.
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 10 tables, 17 rows each side.

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`4acc4f9dbd953d8934cacce1bcb3e0f383cc4237947bc2cf847c8e1b00830f82`, Python
`18b52b185b5ce192479f6f16d3c75bf523f23d9422166b541fb608e118038c3a`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-62fc68042cf24e75`, compared COBOL
`77a29fd34bc09865fdd87a6a68f7eacd406b90dfbed041c1dbc7c89a42a9206e` against Python
`9ca8630675d25b58090dbcee7f3ec109df4c88052867dd38e0c788f9be178d1f`, and its `verdict.json` cites both.

`Purch-SortCode` is seeded as `"0"`. Compiled probing established that the
`binary-long` caller storage is reinterpreted through the bridge's
`PIC 9(8) COMP` linkage without conversion, so a realistic six-digit sort code
exceeds the frozen `mediumint(6) unsigned` column. The zero is therefore the
**reachable store state** measured from the oracle, not a convenience and not a
correction to the migration. Cross-reference **`Q-3`**.

### 10.4 `clean_batch_irs`

- **Operation:** `irs_post` — `irs030`, `Ledger-Postings-Add` only.
- **Modules exercised:** `irs030_posting.py`, via
  `acas_posting/cli/irs_post.py`. This is the **third linkage shape**:
  `using IRS-System-Params, WS-System-Record, File-Defs`
  `[irs/irs030.cbl:L552-L554]` — no calling-data block and no run date.
- **Answer:** `irs_clear_postings: "Y"`.
- **Seed:** `system.dat`, `irsacnts.dat`, `irsdflt.dat`, `irsfinal.dat`,
  `irspost.dat`, `postings2irs.dat`.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127` at the boundary; but note
  §6.1 — `irs030`'s posted date comes from the data at
  `[irs/irs030.cbl:L1662]`.
- **Pinned IRS fan-out:** a single space. The IRS route is driven directly, not
  by fan-out.
- **Affected tables:** the 5 of §7.1 — `IRSDFLT-REC`, `IRSNL-REC`,
  `IRSPOSTING-REC`, `PSIRSPOST-REC`, `SYSTEM-REC`.
- **Expected and observed effect:** changed.
- **Expected and observed term code:** 0.
- **Anomalies witnessed in state:** **A-4** (half-posted double entry on a missing credit
  account), **A-5** (lost update on the two VAT control accounts), **A-6** (the
  published facade verb that can never succeed), **A-7** (the guarded date
  components and the partially-derived row), **A-19** (the superseded
  commented-out VAT computes).
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 4 tables, 50 rows each side.

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`394b906bb0938e0f7964fd60f39bec06970709de265e903a4eb6138fe3cdf51d`, Python
`06f83edb1fe68f0e95f5c8c5ac235c9345336c3597d99d2e782fc016e9b1f47e`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-41d424b42c534c54`, compared COBOL
`b0851b584cc87031cd2aacb471d6c8daa6d88e33c009867657b81e0a72656d0d` against Python
`e7dc55a38858657c155d0a901726eb063bc3fe725faa081b14869fab772872f7`, and its `verdict.json` cites both.

**The clear-transfer-file prompt is a real input with a real table effect, and
its shape is not what the display suggests.** At
`[irs/irs030.cbl:L1715-L1727]`: L1715 is the label `EOJ-q1.`, L1716 displays
"Can I clear the Ledgers Posting file? **[Y]**", and L1717 accepts the reply. But
L1718–L1719 are `if WS-Reply not = "Y" and not = "N" / go to EOJ-q1.` — so
**`[Y]` is a display hint, not a default, and an empty reply loops forever**.
Answering `Y` reaches `perform acas008-Open-Output` at **L1723**. The `accept` at
**L1725-L1726** is a pure acknowledgement pause and is **dropped** on the Python
side per AAP §0.3.4, since it has no database effect; the control flow around it
is preserved.

**The measured clear is threshold-bounded, and this corrects the source
reading.** `[common/acas008.cbl:L313-L319]` turns `Open-Output` into a
delete-all by `set fn-delete-all to true`, **conditional on
`and not FS-Cobol-Files-Used` at L315** — that is, in RDB mode only — and there
is a second, **unguarded** substitution at `[common/acas008.cbl:L571-L574]`.
Reading that alone says "every row is deleted". What the compiled bridge actually
does is bounded: the observed assertion was "the frozen clear predicate removed
every `PSIRSPOST-REC` row below key 9999999999; **6 higher-key row(s) remain** by
the compiled bridge's measured threshold `[common/slpostingMT.cbl:L849-L891]`".
`PSIRSPOST-REC` therefore ends with **6 rows on both sides**, and the diff is
empty. Per R-6 the measured behaviour is the specification and the source reading
is not; the general rule still stands — **`PSIRSPOST-REC` may legitimately end a
scenario empty, empty on both sides is a pass, and empty on one side only is a
real failure.**

**`acas007` reaches the same delete-all, and the divergence that survives is in the
BOUND rather than in the substitution.** At `[common/acas007.cbl:L305-L312]` the same
`Open-Output` shape appears with `set fn-delete-all to true` (L308) and
`move zero to access-type` (L309) both **commented out** — but that leaves `fn-Open`
with `fn-Output` intact as far as `ba015-Test-Ends`
`[common/acas007.cbl:L622-L631]`, whose `[ Backup code ]` performs the bridge and
then sets `fn-Delete-All` before falling through into the bridge again. MEASURED:
GL-Batch `Open-Output` returns `FS-Reply 0` / `WE-Error 0` and **empties
`GLBATCH-REC`** of every key strictly below its 999999 bound. What separates the two
handlers is that `glbatchMT` stores a six-digit key through a numeric move
`[common/glbatchMT.cbl:L1069]` — below its bound — while `slpostingMT` stores a
group-move image near 4.7e17 `[common/slpostingMT.cbl:L1001]`, far above the
`9999999999` bound its own delete-all composes. That is **A-NEW-8**: preserved,
never harmonised, and corrected against measurement in §15.3 of
[`anomaly-log.md`](anomaly-log.md), whose key-bound note carries the full table. No
scenario in this directory issues an `Open-Output` on GL-Batch, so the emptying is
reproduced in code and witnessed by a handler-level call rather than by any diff.

**`IRSFINAL-REC` is deliberately absent from the affected-table list.**
`[irs/irs030.cbl:L296]` declares
`03  Final-Record          pic x.    *> Table/File not used in this program.`,
and `acasirsub5` issues zero facade verbs in the migrated section. Listing it
would invite a comparison of a table neither cycle touches.

The six posting numbers are seeded as 1000 through 6000 so that they yield six
distinct measured relational keys rather than collapsing through the bridge
conversion.

### 10.5 `mixed_accepted_rejected`

- **Operation:** `gl_post_cycle`.
- **Modules exercised:** as `clean_batch_gl`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat` — two batches,
  one posting.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space.
- **Affected tables:** the 5 of §7.1 — `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed term code:** 0.
- **Anomalies witnessed in state:** none with a state signature. `Q-EMPTY-BATCH-AT-END`
  is `RESOLVED BY ORACLE` (2026-08-07) with the answer that **neither at-end paragraph
  leaves any observable effect**, so what this route establishes is that the two
  implementations agree on a run that writes nothing — which is exactly the parity claim
  §10.8 makes and no more.
- **Named here but NOT witnessed by this route:** **A-13**, the two entirely silent
  skips, which A-NEW-18 makes unreachable by any seed; and the at-end calls themselves,
  whose rewrites address key zero. Both are locked by
  `tests/arithmetic/test_ledger_balance_accumulation.py` — its merged silent-skip group
  for the skips, and
  `test_the_empty_work_file_still_performs_end_account_then_end_batch` for the at-end
  path.
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 3 tables, 8 rows each side.

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`46e9cbd1575c233cfad0a7fb18a7b861c238d48e02685d1f3e4b5db1dd3658de`, Python
`eb63dc2edd2cc616c4154e2b669485d04f86af05724cca5345e850ea5b42ab1e`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-c38285f9ca354767`, compared COBOL
`795f02edde66a2255bf69d7a7045fa649a7ac269cfd8e40bd4cbdb9fd133ba80` against Python
`47d795f31bd4c68bc009e4850d15163b5aedcd8b41aefea04a8954c3280a19f5`, and its `verdict.json` cites both.

**The two silent skips.** `[general/gl072.cbl:L291-L292]` is
`if post-batch not numeric / go to loop.`, and `[general/gl072.cbl:L306]` is
`if we-error equal 999` — with a **second** `we-error = 999` site at
`[general/gl072.cbl:L348]`. Both classes are **entirely silent**: no message, no
counter, no trace. **Adding a warning would be an added behaviour** and would
breach R-3 as well as R-4, so neither cycle emits one.

Recorded honestly about this scenario's reach: because `HV-POST-RRN` is not
loaded (§10.1, `Q-9`), the measured RDB loader can persist only one posting
primary key. The scenario therefore uses two batches and one posting and proves
the **reachable** no-op. It does **not** fabricate six independently addressable
postings merely to make both `gl072` skip sites execute — a fixture invented to
exhibit a path the store cannot reach would be evidence of nothing. The skip
sites remain locked by `tests/arithmetic` and by the anomaly register rather than
by this journey.

### 10.6 `period_end_totals`

- **Operations, in declared order:** `sl_invoice_post`, `sl_cash_post`,
  `pl_order_post`, `pl_payment_post` — the only scenario spanning two sub
  systems.
- **Modules exercised:** `sl055`, `sl060`, `sl100`, `pl055`, `pl060`, `pl100`
  modules via the four corresponding CLI entry points.
- **Answer:** `payment_post_confirm: "YES"`.
- **Seed:** the nine files of §7.2.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space.
- **Affected tables:** the 15 of §7.1.
- **Expected and observed effect:** changed.
- **Expected and observed term codes:** 0, 0, 0, 0.
- **Anomalies witnessed in state:** **A-8**, **A-9**, **A-10**, **A-11**, **A-12**,
  **A-17**, **A-20**.
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 14 tables, 45 rows each side.

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`9b3ec5ed22d5e54624fed19fbda59466498b4d4a6c466d5a243a1429f93b01cb`, Python
`cc15c818292d7651907b0f1044a9462c50e6d836f1a1e2084e234fd3088c8c32`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-20dac0f23e634c22`, compared COBOL
`0b0a13cbe437a63b2f08d4b2ad9e810434b00fdc1270e43d1339f0adff7110f1` against Python
`ad57d342abeb511f1ce69b86e20c280a2b40ccb16336a2286c96664f62794876`, and its `verdict.json` cites both.

The oracle driver runs four separate menu processes **without a reset between
them**, so the four operations accumulate as they do in production. Operation
one's seed attestation is preserved for the eventual COBOL dump. Open-item keys
are seeded above the header range, the Purchase sort code is reachable, and the
build-copy menu shim preserves `FILE-SYSTEM-USED = 1` in the flat mirror so that
the second and later menu processes cannot silently switch to indexed files.

**The nine period-total write sites, with their guards.** AAP §0.6.4 records that
these are "the sole writers of the totals record, which makes the
period-end-totals scenario verifiable by inspecting one table" — that table being
`SYSTOT-REC`. The guards decide which of the nine actually fire, so they are
recorded individually:

| # | Site | Guard |
| ---: | --- | --- |
| 1 | `[sales/sl055.cbl:L675]` → `sl-invoices-this-month` | `if ih-type = 2` at L674 (Invoice) |
| 2 | `[sales/sl055.cbl:L677]` → `sl-credit-notes-this-month` | `if ih-type = 3` at L676 (Credit Note) |
| 3 | `[sales/sl060.cbl:L641]` → `sl-credit-deductions` | **unconditional** |
| 4 | `[sales/sl060.cbl:L700]` → `sl-cn-unappl-this-month` | **unconditional, and OUTSIDE** the L695 `if FS-Cobol-Files-Used and File-18-Exists` print guard |
| 5 | `[sales/sl100.cbl:L404]` → `t-paid` **and** `sl-payments` | `if oi-type = 5` at L402 (Payment); **two receivers** |
| 6 | `[purchase/pl055.cbl:L582]` → `pl-invoices-this-month` | `if ih-type = 2` at L581 |
| 7 | `[purchase/pl055.cbl:L584]` → `pl-credit-notes-this-month` | `if ih-type = 3` at L583 |
| 8 | `[purchase/pl060.cbl:L628]` → `pl-cn-unappl-this-month` | **unconditional, and OUTSIDE** the L623 print guard |
| 9 | `[purchase/pl100.cbl:L396]` → `t-paid` **and** `pl-payments` | `if oi-type = 5` at L394; **two receivers** |

Type codes: `ih-type` 1 = Receipt, 2 = Invoice, 3 = Credit Note, 4 = Proforma;
`oi-type` 3 = Credit Note, 5 = Payment.

**Under `file_system_used: 1` the guarded print blocks never run, yet sites 4 and
8 still accumulate — which is precisely why `SYSTOT-REC` changes at all in RDB
mode.** Sites 4 and 8 sit after the print guard's terminating period, so the
guard scopes the three `write print-record` statements and not the `add`. An
implementation that indented the `add` into the guard would leave `SYSTOT-REC`
unchanged and the diff would catch it.

**`SYSTOT-REC` appears on three affected-table lists but is genuinely in scope
only here.** It is carried by `clean_batch_sl` and `clean_batch_pl` so that an
unexpected total write would be caught, but only this scenario drives enough of
the nine sites to change it. Cross-reference **`Q-7`**, which settles what the
menu shells' unconditional exit-path rewrite writes and why the affected-table
list must bound the comparison.

### 10.7 `control_total_mismatch`

- **Operation:** `gl_post_cycle`.
- **Modules exercised:** `gl070_transaction_pre_process.py` and the term-code
  gate. `gl071` and `gl072` are **not** reached.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat` — a batch left
  open.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space.
- **Affected tables:** the 5 of §7.1 — `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed term code:** **5** — the only non-zero in the register.
- **Wrapper status:** 0, after verifying the behavioural status.
- **Anomalies witnessed in state:** **A-15** (the batch record's declared length contradicts
  the sum of its fields; cross-reference **`Q-4`**).
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 3 tables, 6 rows each side.

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`3f373848afbae551130ebdcc0aa51b1ab495e35fe1a68e28b2c2112067d45ac6`, Python
`f1d3fa912512263a8d4402fc46dad9cc51778f220aa31c008a872ea3b522f348`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-babbabb4b455483b`, compared COBOL
`de4182440b543a6ce5b41107a2b1b6f34fc3c807e40483d14710b01da533a2de` against Python
`393971a5392fbee2432d7aa1bd57ddcffc41894481c3ebddc27e47f92a184b3a`, and its `verdict.json` cites both.

**This scenario is General-Ledger-specific, and necessarily so.** AAP §0.6.4
records that Sales and Purchase batches "balance by construction … there is no
meaningful way to construct an unbalanced sales batch." There is therefore no
Sales or Purchase counterpart to build.

**The control-total gate has two distinct failure modes, because the comparison
is a two-part conjunction.** `[general/gl051.cbl:L1117-L1118]` reads
`if input-gross = actual-gross` **and** `input-vat = actual-vat`, so a batch can
be rejected on **VAT alone** with the gross agreeing perfectly. And there are
**two paths to `batch-status = 0`**: the `not truet` early exit at
`[general/gl051.cbl:L1101-L1103]`, and the comparison failure at
`[general/gl051.cbl:L1121]`. A **third** exit at
`[general/gl051.cbl:L1099-L1100]` — `if z = 99 / go to main-exit.` — leaves
`batch-status` **unchanged**, which is a third outcome rather than a third
rejection.

**The gate's decisive ordering.** `[general/gl051.cbl:L1109]` is
`add actual-vat to actual-gross.` and it executes **before** the equality test,
because the entered figure is VAT-inclusive. Reversing these two steps would
reject every batch that carries VAT.

The `end-batch` paragraph spans `[general/gl051.cbl:L1096-L1134]`, beginning at
the `end-batch.` label; its last statement is
`go to main-exit.` at L1134.

**How the gate is reached.** `gl051` has **no CLI entry point** (§13), so this
journey does not call it. It reaches the control-total condition through
`gl070`'s detection of the open batch, which raises term code 5 at
`[general/gl070.cbl:L289]`; the menu then returns at
`[general/general.cbl:L810-L811]` and never dispatches `gl071` or `gl072`. The
**absence** of their writes is the expected database effect. On the compiled side
the driver additionally has to answer the `gl060a` page prompt, which has no
`AUTO` clause at `[general/gl070.cbl:L421]`, with `X` and a Return, then a second
Return for the end-report acknowledgement.

### 10.8 `empty_batch`

- **Operation:** `gl_post_cycle`.
- **Modules exercised:** as `clean_batch_gl`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat` — **deliberately no**
  `posting.dat`.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space.
- **Affected tables:** the 5 of §7.1 — `GLBATCH-REC`, `GLLEDGER-REC`,
  `GLPOSTING-REC`, `SYSDEFLT-REC`, `SYSTEM-REC`.
- **Expected and observed effect:** unchanged.
- **Expected and observed term code:** 0.
- **Named here but NOT witnessed by this route:** **A-NEW-8**. The seeded batch row
  is present at the end because **nothing on this route opens GL-Batch for output**,
  not because an `Open-Output` spared it: measurement shows `acas007` empties
  `GLBATCH-REC` of every key strictly below 999999 when it is asked. §15.3 of
  [`anomaly-log.md`](anomaly-log.md) records the corrected reading and §15's
  key-bound note carries the measured table.
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 3 tables, 5 rows each side
  (`GLPOSTING-REC` empty on both).

**Normalised-tree manifest SHA-256**, 22-table-bound run — COBOL
`0efd8063b6d3f575f2eeac815dee4564aa4d447ab485393077a0dfbc6c22e862`, Python
`b58e897e9023763d40274d192435d633f7eafe192cae017f8bcf97c56659df27`.
These are the two files stage 10 compared. The earlier declared-effect-bound run
of the same scenario, `parity-cf6383cb1624400e`, compared COBOL
`36008ab368a5779c576617170a25f735ad9bdb1c6c0c37bcb5bc24d2f0fd3813` against Python
`dc1939f74b51db210869076d6f9e4005a9ae8c34d8591d642524d49f29c0847c`, and its `verdict.json` cites both.

The scenario proves the whole protocol is stable over a batch with no posting
rows. It is emphatically **not** accepted merely because both posting tables are
empty — that would be the false pass §5.1 warns about. It is accepted because the
seeded batch and ledger rows are present and identical, both run attestations are
recorded, the file-system selector is 1, the clock reads back as pinned, and the
two seed fingerprints agree. `GLPOSTING-REC` being empty on both sides is one
observation among several, not the verdict.

### 10.9 `end_of_cycle_gl` — NOT COMMITTED, and its measurement retained

**THAT NINTH DEFINITION AND ITS TEST ARE NOT COMMITTED:** the Agent Action Plan's inventory names eight scenario definitions and eight scenario tests, and this tree is held to it. Everything recorded about that journey is kept because it was really driven; what a reader cannot do is re-run it from the committed set, and `gl080` consequently has **no table-state comparison** behind it.

**The one scenario that was not part of AAP §0.8.5's mandated set.** It existed
because the mandate asks for clean batch per ledger, mixed accepted-and-rejected,
period-end totals, control-total mismatch and empty batch, and **none of those five
is an end-of-period run** — which left `gl080` compared by nothing, and leaves it so
again. Its design is described in
[`ambiguity-resolutions.md`](ambiguity-resolutions.md) §16.1 so that whoever needs an
end-of-period comparison next can rebuild it rather than re-derive it. `gl080` is one
of the twelve in-scope programs and owns one of the migration's five `ROUNDED`
stores at `[general/gl080.cbl:L328]`, so that was the largest single gap in this
register's evidence.

- **Operation:** `gl_end_of_cycle` — the real route, `general/general.cbl`'s
  `load09.` dispatching `gl080` through the shared four-parameter block, not a
  shortcut that calls the program directly.
- **Modules exercised:** `acas_posting/cli/gl_end_of_cycle.py`,
  `acas_posting/programs/gl080_end_of_cycle.py`, and the General Ledger data-access
  modules `acas005_gl_nominal.py`, `acas006_gl_posting.py`, `acas007_gl_batch.py`
  and `acas000_system.py`.
- **Seed:** `system.dat`, `ledger.dat`, `batch.dat`, `posting.dat`.
- **Pinned clock:** `21/09/2025`, `Run-Date 155127`.
- **Pinned IRS fan-out:** a single space.
- **Affected tables:** `GLBATCH-REC`, `GLLEDGER-REC`, `GLPOSTING-REC`,
  `SYSDEFLT-REC`, `SYSTEM-REC`.
- **Expected and observed effect:** changed.
- **Expected and observed operation status:** 0.
- **Anomalies witnessed in state:** **A-3**, the two disagreeing notions of "current quarter"
  inside `gl080`, and **N-EDIT**, the bridge's structural inability to render a
  minus sign. The seed is engineered so both become visible in *table state* rather
  than only in a unit test; a seed tidied up to make the figures agree would defeat
  the file's purpose, since a defect reproduced is correct and a defect fixed is a
  failure (R-4).
- **Diff status:** **`EMPTY DIFF — OBSERVED`** — 5 tables, 7 rows each side.

**Manifest SHA-256** — COBOL
`4abdaac30c4c3a9410ae88368406d44bb18c2e751da8e08b24b7a7d3026f2516`, Python
`0c6834185edff1bf4ccca1f9a6899eca15843eebb0ad4a8526767b1727f5cf69`.

**Why the empty diff is not vacuous here.** Four of the five tables come back with
rows, and the run was additionally pinned by named assertions in the uncommitted
`tests/scenarios/test_end_of_cycle_gl.py`: that every gating condition which would
make `gl080` return early is still seeded as the scenario intends, that the Phase 3
delete walk deletes nothing, that only the closing cycle's batch was stamped, that
Phase 5 wrote quarter one and `Ledger-Last` while leaving quarters two, three and
four alone, and that the cycle advanced while the quarter counter wrapped. An early
return would also produce two agreeing dumps, so those preconditions are what
distinguish "the end-of-cycle path ran and matched" from "the end-of-cycle path
declined to run, twice".


## 11. Ordering dependencies the General Ledger journeys must respect

AAP §0.6.4 lists six ordering dependencies that must survive the migration. They
are recorded here because a state diff is the only thing that would catch a
violation of most of them, and one of them a state diff would catch only by luck.

**1. The sort feeds a sequential read — the strongest dependency in the cycle.**
`gl072` locates the nominal-ledger account for each posting with
`perform GL-Nominal-Read-Next` at **`[general/gl072.cbl:L408]`** — a
**sequential** read, not an indexed one. The lines immediately after it,
`if read-ledger not = "R"` at L410, are the *guard on the result*, not the read.
It finds the right account **only** because `gl071` has already emitted the stream
in nominal-key order. AAP §0.6.4:

> "Any change in sort stability or key composition produces silent misposting —
> no error, no diagnostic, wrong balances."

`gl071` contains a **single** `SORT`, at **`[general/gl071.cbl:L172-L178]`**, on
**four** ascending keys — `sort-batch`, `sort-ac`, `sort-pc`, `sort-post` — using
`pre-trans` and giving `post-trans`. Because misposting under a perturbed sort is
silent, `gl071`'s output ordering is asserted **directly** by a test rather than
being left for a state diff to notice. Cross-reference **A-14**, and
**`Q-SORT-TIE-ORDER`** for where the compiled sort places two records whose key
tuples are identical.

**2. VAT enters the control total before the comparison** — §10.7,
`[general/gl051.cbl:L1109]` before L1117–L1118.

**3. The abort chain is four links long and crosses three programs** — the open
batch sets the status condition, `gl070` raises 5 at
`[general/gl070.cbl:L289]`, the menu tests it at
`[general/general.cbl:L810-L811]`, and `gl071` and `gl072` never run. The Python
CLI reproduces this as a **hard gate between phases**, not a warning.

**4. Phase order is fixed, and the labels are not sequential with execution.**
The programs label their own phases on screen:

| Label | Locator | Executes |
| --- | --- | --- |
| "Phase - 1.  Batch Check" | `[general/gl070.cbl:L284]` | first |
| "Phase - 2.  Transaction Pre-process" | `[general/gl070.cbl:L292]` | second |
| "Phase - 4.  Transaction Update" | `[general/gl072.cbl:L274]` | fourth |
| "Phase - 3.  Transaction Deletion" | `[general/gl080.cbl:L319]` | **after** Phase 4 |
| "Phase - 5.  End of Period Processing" | `[general/gl080.cbl:L336]` | last |

**Deletion is labelled Phase 3 but executes after Phase 4**, and both labels live
in the same program. The module docstrings preserve the numbering so a maintainer
comparing the two trees is not misled.

**5. The cycle filter appears twice, with different companions.** Both passes over
the batch file filter on the accounting cycle, but the second adds status
conditions the first does not — `if status-open / or not waiting / or not
gl-batch / go to loop`. Collapsing the two passes into one would change which
batches are pre-processed at all, which is exactly what `clean_batch_gl` depends
on (§10.1).

**6. Account-level totals close before batch-level totals.** This one is easy to
get backwards from the source, so it is stated precisely. In **source** order the
`end-batch.` label at `[general/gl072.cbl:L372]` *precedes* `end-account.` at
`[general/gl072.cbl:L379]`. In **execution** order the opposite holds:
`perform end-account` immediately precedes `perform end-batch` at
`[general/gl072.cbl:L287-L288]` and again at `[general/gl072.cbl:L297-L298]`. The
end-of-batch step is what stamps the batch — `move 1 to cleared-status` at L375,
`move run-date to posted` at L376, `perform GL-Batch-Rewrite` at L377 — so
inverting them would produce a batch marked posted with an unclosed final account.

**`GLPOSTING-REC` is an unchanged witness on every General Ledger route.**
`gl072` issues **zero** `GL-Posting-*` verbs and `gl070` is read-only over the
table. Its presence on all four General Ledger affected-table lists is
deliberate: **an unchanged table is evidence too**, and a write appearing there
would be a behavioural difference the diff must catch.

## 12. Determinism evidence

The criterion, quoted verbatim in the front matter, is that two runs of the same
scenario under the same pinned clock produce byte-identical dumps.

`tests/determinism/test_two_runs_byte_identical.py` runs `clean_batch_gl` and
`clean_batch_irs` twice each under the same pinned clock, relocates run A before
run B can overwrite it, compares structurally, and then compares every
affected-table file **byte for byte**.

Observed first-hand on 2026-08-07, inside the `gnucobol` service
(`pytest -m determinism`), on the same code that produced §8. The figure below is a
report of that run, not a retained artefact — re-run the command to reproduce it:

```text
6 passed, 1047 deselected in 19.89s
```

Re-observed on **2026-08-08** on the code as committed, in the same service and
against the diagnostic oracle named in §8, alongside the eight-scenario campaign
recorded there:

```text
8 passed, 1332 deselected in 29.48s
```

The count moved from 6 to 8 because the tier gained two cases, not because a
determinism pair changed its verdict; the deselected figure moves with the total size
of the suite and is not a finding either way. Both pairs were `EMPTY DIFF — OBSERVED`
in both runs.

**Diff status: `EMPTY DIFF — OBSERVED`** for both determinism pairs.

**The comparison a determinism pair makes is not the parity comparison, and the
difference is deliberate.** `harness/diff_states.py`'s default mode requires the
two captures to name **different** sides and to carry the **same** run id, which
is exactly right for `cobol` against `python` and exactly wrong here, where both
captures are the Python cycle. So the pair is compared in the tool's same-side
mode, whose requirements are the mirror image: the sides must **match**, the run
ids must **differ**, and one scenario definition, one frozen schema and one seed
marker are still required. That mode is *stronger* than comparing the trees with
no provenance check — it adds a requirement the parity mode has no use for, that
the two run ids differ, which is what refuses a capture compared against itself.
It cannot be reached from the command line; only an in-process caller selects it.

For the same reason the byte comparison covers **every table dump and not
`_manifest.json`**. The obligation is byte-identical *dumps*, and the manifest is
the provenance of a dump rather than a dump: it records the run id, the exact
command and the digest of the manifest it was normalised from, so two runs'
manifests **must** differ. Requiring them to be byte-identical would contradict
the same-side requirement that the run ids differ, and the obligation would be
unsatisfiable for a correct cycle. The manifest is still compared, on the part of
it that is state — its `tables` block of names, row counts and per-dump digests
must be equal — and its run ids are asserted to differ, so neither the row-count
cross-check nor the false-pass guard is lost.

Why this holds rather than being hoped for: the in-scope programs contain **zero**
clock reads and take the date purely through linkage (§6.1); there is no random
seed; and there is no ordering nondeterminism from a secondary index, because all
22 in-scope tables have a single-column primary key and **no** secondary index
(§5.3, re-asserted by `reset_db.sh` on every run in §9.4).

A second corroboration is available at the artifact level, and it has to be stated
carefully, because the obvious formulation of it is **false for the manifests this
tree publishes**. The provenance block carries the **run id**
(`harness/normalize.py PROVENANCE_KEYS`), so **a manifest is deliberately not
reproducible across two runs** — two runs have two identities, and recording them is
the point. Manifests WERE byte-reproducible under an earlier manifest shape that
carried no run id, and the measurement is retained because it was really taken:
`clean_batch_gl` was driven twice and returned the identical pair, COBOL
`086715e6483c37860b7e980c3fc2a83079ce2f84889ba8312c91d178c91e5869` and Python
`288ddb8ebb9bf405393eaeb508b278485ff7163f9f29d209aa100f1542ca1681`, digest for
digest. That observation is kept because it happened; the claim built on it is
withdrawn, because the manifests it was true of no longer exist.

What *is* reproducible is the **verdict**: re-deriving stage 10 from the retained
captures of a completed run republished a `verdict.json` that was **byte-identical,
field for field** (§9.2). Same inputs, same verdict, independently of when it is
computed. That is the artifact-level form of the determinism the tier asserts.

The distinction matters beyond pedantry. A register that claimed byte-reproducible
manifests would be claiming something the provenance design makes impossible, and a
reader who checked it would find the claim false and have no way to tell whether the
migration or the documentation was wrong.

**All sixteen digests in §10 were replaced at this revision, and it is important
that this is not misread as determinism having failed.** The pairs recorded on
2026-08-04 no longer reproduce because the *inputs changed*: `SYSTEM-REC` and, for
the General Ledger scenarios, `SYSDEFLT-REC` were brought inside each comparison, so
each manifest now describes a larger table set and necessarily hashes differently.
Determinism is the claim that the *same* configuration reproduces. A digest is only
evidence while the configuration it was taken under is still current, which is why
they are republished here rather than carried forward.

The clock witness is deliberately **database-backed** rather than input-echoing:

- pre-run `SYSTEM-REC.FILE-SYSTEM-USED = 1`;
- post-run `SYSTEM-REC.RUN-DAT = 155127`.

This keeps the non-vacuity guard meaningful for the measured `clean_batch_gl`
no-op, where requiring `GLBATCH-REC.POSTED = 155127` would demand a frozen rewrite
the zero-key posting can never reach (§10.1).

### 12.1 The committed scenario tier

The **eight** committed journeys are also driven by the committed test tier, which adds the
per-scenario assertions of §9.4 on top of the diff. Two observations were made on
2026-08-07, of two different revisions of this tree, and both are recorded because
each explains the other's figure:

```text
$ python3 -m pytest -m scenario -q
107 passed in 89.98s
```

This read `93 passed in 162.72s` from the 2026-08-04 run. The growth to 107 is
the ninth scenario's eleven tests plus the seed-relative tests added to the eight;
the drop in wall time is the memoisation of one parity run per scenario module,
which removed the repeated runs that the earlier figure had paid for.

**Neither figure is this checkout's.** Both were taken from a tree carrying the ninth
scenario. Re-measured here, inside the `gnucobol` service with the transformed-oracle
acknowledgement bound, `python3 -m pytest -m "scenario or determinism" -q` reads **114
passed, 1222 deselected**, exit `0` — **106** scenario tests and **8** determinism
tests by collection. The 107 above is retained as the observation it was, not as a
claim about the eight committed scenarios.

The second observation, taken inside the `gnucobol` service over
`pytest -m "scenario or determinism"` on the revision that widened the capture
bound, read `99 passed, 954 deselected`. Its count rose from the same 93 for a
different reason: each scenario now asserts the capture bound against the in-scope
set **and** its declared effect as a subset of it, and `period_end_totals` gained
the bound assertion its docstring had promised but never made. Whole-suite figures
from that revision: **1035 passed, 0 failed, 18 xfailed** inside the service, and
**972 passed, 63 skipped, 18 xfailed** on a bare host, the skips being exactly the
stack-bound tiers. Both counts are superseded by any later revision of the tier;
the command above is what re-derives the current one.

Re-derived on **2026-08-08** on the code as committed, inside the `gnucobol` service
against the diagnostic oracle of §8:

```text
$ python3 -m pytest -m scenario -q
106 passed, 1234 deselected in 153.36s
```

The count is 106 rather than 107 because the ninth scenario and its module are not
committed (§8), and the tier now measures the eight that are. Nothing in it errored
or skipped, which is the material figure: at an earlier revision every one of these
modules ERRORED at the publication check because the capture stages named no scenario
definition and the provenance field stage 10 requires was empty on both sides.

That tier composes the ten stages in process, and it binds **one run id per protocol
run** exactly as a hand-driven run must. It has to: each stage is a separate process that derives its own
identity when none is supplied, so an unbound composition gave the two sides two
different ids and stage 10 refused the pair — correctly, since `run_id` is one of
the fields that must match before a single row is compared. The composed protocol
and the driven one are therefore the same protocol, which is what makes this tier
corroboration of §8 rather than a second, weaker measurement.

The elapsed times quoted above are incidental, and nothing is concluded from them
beyond the one comparison they were quoted for. They vary with host load, they are
not a property of the migration and a reader cannot check them — the pass counts,
the commands and the retained artifacts are what can be verified.

## 13. Coverage limits, stated explicitly

This is the part of the register that carries
**`PENDING — AWAITING ORACLE EXECUTION`** and the scope declinations. Nothing
below is claimed as covered.

- **`gl080` was driven by no scenario at all. It now is, so this limit has
  been withdrawn** — and it is rewritten rather than deleted, because a reader who
  met the old wording is entitled to see that it was retired rather than that they
  misremembered it. It said Phase 3 transaction deletion and Phase 5
  end-of-period processing were "not exercised by any of the eight", with the
  end-of-cycle path marked **`PENDING — AWAITING ORACLE EXECUTION`**.
  `harness/scenarios/end_of_cycle_gl.yaml` drove the real `gl_end_of_cycle`
  route — `general/general.cbl`'s `load09.` dispatching `gl080` — and §10.9
  records its observed empty diff; that definition is not committed, so the declination
  stands while the measurement is retained. The two arithmetic questions that sat behind
  the declination are also no longer open: **`Q-GL080-DIVIDE-BY-ZERO`** and
  **`Q-QUARTER-SUBSCRIPT`**, the latter being the unbounded quarter subscript of
  **A-2**, are both **`RESOLVED BY ORACLE`** as of 2026-08-07. Each was closed by
  a focused compiled probe rather than by this scenario, for the reason its own
  entry gives: their observables are a control-flow branch and a byte offset,
  which a probe exhibits directly and a table dump does not.
  **What genuinely does remain a limit:** `period: 1` is still the seeding in all
  eight scenario files, so the cycle-to-period divide at
  `[general/gl080.cbl:L328]` is exercised with a divisor of one and **a zero
  divisor is still driven by no scenario**. That narrower statement is the true
  one, and it is why `Q-GL080-DIVIDE-BY-ZERO` needed the probe.
- **`gl051` has no CLI entry point.** `control_total_mismatch` reaches the
  control-total gate indirectly, through `gl070`'s detection of the open batch and
  the menu's term-code boundary (§10.7). The gate's own arithmetic is exercised as
  a library function by `tests/arithmetic/test_control_total_comparison.py`, not
  by a scenario. Declination recorded at §16.2 of
  [`ambiguity-resolutions.md`](ambiguity-resolutions.md).
- **The autogen no-op assertion is observed, not assumed — with one asymmetry
  stated plainly.** §10.2 records the assertion holding, and §9.1 records what
  each side actually probed: the Python runner counted **all four** autogen tables
  on every run, the COBOL runner counted **the Sales pair only**, and only on the
  two Sales-subsystem scenarios. That is the correct bound for the question — only
  the Sales menu calls `sl830` — but it is **not** "all four on both sides", and
  saying so would overstate the probe. Had the probe not been driven at all, it
  would have been marked `PENDING — AWAITING ORACLE EXECUTION`; it is
  recorded as observed because it was observed, and its scope is recorded because
  the scope is narrower than the claim it supports.
- **Questions this register does not close.** The scenario journeys resolved
  `Q-6`, `Q-7` and `Q-10`, and partially resolved **`Q-9` alone**. Every other
  entry in [`ambiguity-resolutions.md`](ambiguity-resolutions.md) retains its own
  status — a green scenario does not close a question by association, and none is
  treated as closed here.
  **`Q-8` IS NOT A PARTIAL ALONGSIDE `Q-9`.** `Q-8` carries the whole-entry status
  `RESOLVED BY CONSTRUCTION`,
  settled by a census of the frozen `MOVE` sites shown in full in its own entry,
  and the register's §17 records it as the single entry holding that status.
  `Q-9` is the single **partial**. The mis-statement is corrected here rather than
  absorbed, because a consumer that describes an authority's status wrongly is exactly
  the defect to avoid, and this register is a consumer.
- **What remains open in `Q-9`, stated so no reader has to infer it.** The
  resolved half is the non-fetch **write** path: `initialize TD-GLPOSTING-REC`
  leaves `HV-POST-RRN` at zero, `bb000-HV-Load` never sets it
  (`common/glpostingMT.cbl:L1053-L1066`), and every loader write therefore targets
  the same primary key — which is why a scenario seed persists at most one
  `GLPOSTING-REC` row. The **open** half is the key of reference and the cursor
  order: whether `START`/`READ NEXT` follows the declared `POST-KEY`
  (`common/glpostingMT.scb:L232-L234`) or the schema's primary key `POST-RRN`
  (`mysql/ACASDB.sql:L155`, `:L169`), which the same bridge's own warning at
  `common/glpostingMT.scb:L229` says may need to change. **No journey in this
  register discriminates it, and none claims to.** Deciding it needs rows whose
  two orderings differ, and the measured single-row limit above makes that seed
  unreachable through the frozen loaders — so the question stays open rather than
  being answered from a degenerate walk. `acas_posting/dal/cursor_state.py` names
  the same open half at the entry that rests on it.
- **`empty_batch`'s green diff establishes agreement, not a value, and the
  distinction is the whole point of that scenario.** `Q-EMPTY-BATCH-AT-END` asks
  what `gl072`'s `end-batch` and `end-account` write when the very first read of
  the sorted work file hits at end, with `save-batch` still zero — it stamps the
  batch cleared and posted, or rewrites a zero-key record, or rewrites nothing.
  §10.8 records the two sides agreeing on whatever it is; it does **not** record
  which, and it could not — a green diff is symmetric and names no value. The
  question is settled **elsewhere and by other means**: a focused
  compiled probe made `Q-EMPTY-BATCH-AT-END` **`RESOLVED BY ORACLE`** (2026-08-07)
  in [`ambiguity-resolutions.md`](ambiguity-resolutions.md), with the answer that
  **neither paragraph leaves any observable effect**. That answer is the probe's,
  not this journey's, and the distinction is kept deliberately: this bullet still
  claims only agreement. Accordingly
  `tests/scenarios/test_empty_batch.py` continues to hard-code no expectation for
  `CLEARED-STATUS` or `POSTED`, even now that the value is known. An agreeing pair
  of values is real evidence of parity; crediting this journey with the
  measurement would be the fabrication this register exists to prevent.
- **Plaintext transport is permitted only because the compiled program applies no
  stronger check.** Every run reports it as a non-fatal finding naming CWE-319,
  and the harness fails closed unless the caller declares the isolated-oracle
  transport explicitly. It is a property of the harness network, not of the
  migration.

### 13.1 The General and Purchase risk — a caveat on expected values

The oracle these journeys compare against is the maintainer's **v3.3** stream —
`[README.TXT:L38]` records the source as updated to "v3.3 pre-final release", and
`[README.TXT:L43]` that "the latest version will always be v3.3 at any point in
time". Two of its sub systems carry the maintainer's own caveats, and those
caveats are the reason expected values for them may come only from the oracle.
`[README.TXT:L51-L53]`, verbatim:

> "I have not had any time to work with General at all since it was migrated over
> to using the GnuCobol compiler (3.2 final) now some years back."

And Purchase is recorded as still under test at `[README.TXT:L44-L47]`:

> "Purchase ledger is still undergoing system testing with more order transaction
> entries and entering both auto payments and manual one's with the various
> reports being run and checked."

with `[README.TXT:L50-L51]` confirming that testing is complete only for IRS,
Stock and Sales "apart for some reports".

Since General contributes the majority of the in-scope programs, **expected values
for the General and Purchase scenarios must come only from the compiled oracle** —
never from the documentation, and never from reasoning about intended behaviour.
AAP §0.6.9 puts it plainly:

> "If the compiled GL cycle behaves surprisingly, the surprise is the
> specification."

Every General and Purchase figure in §10 was captured from the oracle on that
basis. Several of the recorded outcomes — the `clean_batch_gl` no-op, the
zero-key posting, the seeded `Purch-SortCode` of `"0"` — are exactly the kind of
surprise this caveat anticipates, and each is reproduced rather than repaired.

## 14. Artifact layout

For each scenario `<name>`, under the harness output area:

```text
/out/<name>/cobol/                     the raw COBOL capture
/out/<name>/cobol.normalized/          the canonicalised COBOL capture
/out/<name>/python/                    the raw Python capture
/out/<name>/python.normalized/         the canonicalised Python capture
/out/<name>/diff.txt                   zero bytes on a pass
/out/<name>/verdict.json               the machine-readable verdict (§9.3)
/out/<name>/parity-result              DRIVER-COMPOSED RUNS ONLY: a run_parity.sh
                                       driver's claim. No stage writes it;
                                       verdict.json is the published claim (§9.3)
/out/run-logs/<name>/cobol.log
/out/run-logs/<name>/cobol.result
/out/run-logs/<name>/cobol.run-status
/out/run-logs/<name>/cobol.operation-status
/out/run-logs/<name>/cobol.seed-fingerprint    state, before the drive
/out/run-logs/<name>/cobol.post-fingerprint    the same record, after it
/out/run-logs/<name>/python.log
/out/run-logs/<name>/python.run-status
/out/run-logs/<name>/python.operation-status
/out/run-logs/<name>/python.seed-fingerprint   state, before the dispatch
/out/run-logs/<name>/python.post-fingerprint   the same record, after it
/out/run-logs/<name>/seed-identity     the fixture marker digest, per run id
```

**Every one of those files records the run id**, which is what lets a reader tie an
artifact back to a row of §8 and what lets stage 10 refuse two captures that are
not two halves of one attempt.

### 14.1 Retention and disposal of this tree

**This tree is evidence, and it carries accounting data.** The captures are
`SELECT *` over the in-scope tables, so they hold monetary amounts and the primary
keys identifying the accounts, customers and suppliers those amounts belong to.
Every file is written mode `600`, and the tree lives in a Docker named volume —
`acas-harness-<CLONE_INDEX>-out` — rather than under the checkout, so no `git add`
can capture it and no sibling clone shares it.

**Retain a scenario's tree for as long as this document cites it.** §8 and §10 cite
artifacts by digest, so a tree whose digests appear here is load-bearing. Once a
scenario has been re-run and its digests in this file updated, the superseded tree
is no longer cited and may be disposed of. Nothing rotates or expires it
automatically, deliberately: a verdict cannot be re-derived by re-reading the tree,
only re-produced by re-running the protocol against the same seed and the same
oracle, so automatic deletion would destroy evidence rather than tidy it.

**Disposal is target-scoped**, because sibling clones each own their own volume:

```bash
docker compose -f harness/docker-compose.yml down
docker volume rm "acas-harness-${CLONE_INDEX}-out"
```

Never `docker volume prune`, never `docker volume rm $(docker volume ls -q)`, and
never `rm -rf` a host path under the shared workspace root — each reaches evidence
this clone does not own. The full contract is in README-python-migration.md §11.1c.

The four fingerprints live under `run-logs/` and **never** inside a compared tree,
so none of them can be diffed as though it were posted data. Each is one line per
declared table plus the parameter row (§7.1). The two pairs answer two different
questions: *cobol.seed* against *python.seed* asks whether both sides started
alike, while a single side's *seed* against its own *post* asks whether that side
changed anything — which is the only way to tell a faithful no-op from a run that
never reached its posting section.

Each normalised tree carries one `<TABLE>.json` per affected table plus
`_manifest.json`, written **last**, so a tree is either complete or unmanifested
and never a mixture (§5.5). `period_end_totals` additionally carries one COBOL
transcript per operation after the first.

`diff.txt` being **zero bytes** is the machine-readable pass marker;
**absent** means no comparison completed, and **non-empty** means differences.
All credential-bearing and execution-data files are mode 0600 or live below an
owner-only directory.

## 15. Reproducing this evidence

Nothing here auto-builds or auto-runs; each stage is invoked explicitly.

```bash
# ACAS_SEED_AUTOCOMMIT=on is a DECLARED DEVIATION from the AAP-mandated seeding
# window (see section 0). Without it stage 1 exits 76, because the frozen loaders
# reach no live COMMIT and persist nothing. It is passed per invocation, and never
# pinned in harness/docker-compose.yml, so it appears in the command that ran.
#
# `run --rm -T`, NOT `exec -T`: `exec` requires an ALREADY-RUNNING container, and
# nothing in this document set starts the gnucobol service -- README section 8.1
# brings up mariadb only, so `exec` here failed with `service "gnucobol" is not
# running`, exit 1, from the documented starting state. `run --rm` starts a
# container per stage, waits for the mariadb dependency, and removes it after,
# which is what every other command in this document set uses.
C="docker compose -f harness/docker-compose.yml run --rm -T \
   -e PYTHONDONTWRITEBYTECODE=1 -e ACAS_SEED_AUTOCOMMIT=on gnucobol"

# once per image. THE DEFAULT IS A FROZEN BUILD, and on this checkout it FAILS with
# exit 74: 22 frozen common/*MT.cbl bridges COPY ACAS-SQLstate-error-list.cob, which
# the archive does not contain (README section 8.7). The member must NOT be
# fabricated (R-3, R-4). --transformed-oracle builds the diagnostic oracle instead,
# and every verdict obtained from it is marked NO PARITY CLAIM.
$C /repo/harness/build_oracle.sh                        # frozen: fails, exit 74
$C /repo/harness/build_oracle.sh --transformed-oracle    # diagnostic oracle

# once per scenario change
$C /repo/harness/seed.sh --build-fixtures

# one scenario, all ten stages in order, stopping at the first non-zero -- the
# recipe is README section 11.1. Against a transformed oracle STAGE 1 REFUSES
# with exit 77 EVIDENCE UNAVAILABLE unless --accept-transformed-oracle is given,
# which makes every capture from that run a diagnosis and no verdict a parity claim:
$C /repo/harness/reset_db.sh /repo/harness/scenarios/clean_batch_gl.yaml \
     --seed-dir /data/fixtures/clean_batch_gl --accept-transformed-oracle
#   ... then stages 2 through 10, each carrying the same bound ACAS_PARITY_RUN_ID
```

`-T` is required on every scripted stage: a tty is allocated by default and a
piped stage would appear to hang. **A seed-mode flag IS needed**: the commands in
§15 pass `-e ACAS_SEED_AUTOCOMMIT=on` because `harness/seed.sh` now defaults to the
AAP-mandated `off`, nothing pins the mode, and without the flag stage 1 exits 76
(§0, §4.3). `--seed-dir` also defaults to the canonical
fixture root `$ACAS_FIXTURES` — or `$ACAS_DATA/fixtures` — plus the scenario name,
which is exactly where `harness/seed.sh --build-fixtures` writes. Passing
The seeding window now DEFAULTS to the AAP-mandated `off`, under which the seed
exits **76** rather than producing an all-empty capture; the reproduction commands
in this section therefore pass `-e ACAS_SEED_AUTOCOMMIT=on` explicitly, which is a
declared deviation yielding a working fixture rather than AAP-conformant evidence.

An empty diff from stage 10 is the pass condition and the only one. A stage that
exits non-zero has produced no evidence, so re-seed rather than carrying a partial
capture forward.

## 16. Conclusion

**All eight committed scenarios carry `EMPTY DIFF — OBSERVED` against a
disclosed-transformed diagnostic oracle, and none of them carries a parity claim
against the frozen specification.** Read §0 before this section: the frozen oracle
does not compile on this checkout (exit 74, 22 bridges, a missing archive member),
so `harness/reset_db.sh` now reports exit 77 EVIDENCE UNAVAILABLE by default and
these rows were obtained under `--accept-transformed-oracle` conditions with a
declared seeding deviation. All eight correspond to AAP §0.8.5's mandated
set; what they establish is agreement with a
partly repaired specification, which is a genuine and useful measurement and is not
the acceptance criterion.

The results were obtained through the rigid protocol of §4, with the comparison
bounded by each scenario's declared affected-table list, the pass condition checked
as **both** exit 0 **and** zero-byte stdout, and attestation enforced rather than
waived.

**The tier figures are re-measured on this checkout rather than carried forward.**
Inside the `gnucobol` service, with the transformed-oracle acknowledgement bound,
`python3 -m pytest -m "scenario or determinism" -q` reads **114 passed, 1222
deselected** and exits `0`; collection splits that as **106** scenario tests and
**8** determinism tests. Earlier revisions of this file quoted `107` for the scenario
tier and `6` for the determinism tier, which were the counts of a tree that carried a
ninth scenario and a narrower determinism tier — those figures are superseded, and
the command above is what re-derives the current ones rather than any sentence here.

Every row of §8 is identified by the manifest digests published with its scenario in
§10, and by the run id where one was recorded; §9.3 names each retained artifact. So
no claim here rests on a date or on this document's own say-so: the digests can be
recomputed from the files they describe.

No frozen COBOL source, bridge, copybook, shell script or schema file was modified
to obtain any of it, and the maintainer's `README*`, `Changelog` and
`ACAS-Manuals/` are untouched.

**OF THE TWO BOUNDARIES RECORDED HERE, NEITHER IS CLOSED BY A COMMITTED ARTEFACT.**
`gl080` **was** exercised, by `end_of_cycle_gl` at §10.9, but that definition is not
committed — so the declination stands, with the measurement retained. See §13, where
the alternative wording is quoted rather than deleted. What holds whatever state the
scenario set is in: every scenario
seeds `period: 1`, so **a zero divisor for the cycle-to-period divide is driven by
no scenario**, and `Q-GL080-DIVIDE-BY-ZERO` was therefore settled by a focused
compiled probe instead, which carries it as **`RESOLVED BY ORACLE`** (2026-08-07) in
§13 rather than as a scenario result. The second boundary stands unchanged: **`gl051` has no CLI
entry point**, and its control-total gate is exercised as a library function rather
than by a scenario. **The ambiguity register's §13 no longer carries a
`PENDING — AWAITING ORACLE EXECUTION` entry at all**: its last one,
`Q-GL084-ACCEPT-SEMANTICS`, was measured on 2026-08-08 by a standalone `cobc 3.2.0`
probe over a real pty, which needed no seed and touched no fixture. The status stays in
that register's vocabulary for whatever genuinely has no measurement, and **this**
document still uses it heavily, because a register whose every line reads "pass" is
worth less than one that says accurately where it stops — and this one stops at the
frozen-oracle parity claim (§0).

## 17. Companion documents

- [`traceability.md`](traceability.md) — program → module, paragraph → function,
  field → dictionary entry.
- [`anomaly-log.md`](anomaly-log.md) — the reproduced legacy defects, with
  locators and reproducing modules.
- [`ambiguity-resolutions.md`](ambiguity-resolutions.md) — each semantic question,
  the oracle experiment, and the resolution adopted.
