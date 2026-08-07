# ACAS posting cycle — the Python 3.12 migration

PLEASE READ: this file documents the Python 3.12 migration of the ACAS batch
posting cycle and the compiled-COBOL comparison oracle that arbitrates it. It
is the only file you need in order to build the oracle, seed a scenario, run
both cycles, diff the resulting state, run the three test tiers, and find the
four mandated deliverables.

It does **not** document the ACAS COBOL system. That is `README.TXT` (with
`README.nightly` for the nightly builds) and `Changelog`, and none of them is
edited by this migration — they are the maintainer's own record and this
migration cross-references them instead. See §15.

WARNING: this is a **behaviourally exact** migration, not a clean-up project,
and that inverts normal engineering judgement for the whole of it. A legacy
defect reproduced is correct. A legacy defect "fixed" on the Python side is a
parity failure, and 14 of the 22 known defects are locked in place by tests
precisely so that a well-meaning correction turns the suite red rather than
passing unnoticed. Read §2 (rule R-4) and §14 before changing anything.

There is **no user rules document for this project**. `review_rules` reports,
in full, `No user rules provided.` The six binding rules R-1 … R-6 come from
the Agent Action Plan (AAP) §0.7.2 and are restated in §2 below; where they are
silent, the work is held to enterprise-standard best practice and nothing has
been invented to fill the gap.

## Contents

1. [What this is, and what it is not](#1-what-this-is-and-what-it-is-not)
2. [The six binding rules](#2-the-six-binding-rules)
3. [What was migrated](#3-what-was-migrated)
4. [What was excluded, and why](#4-what-was-excluded-and-why)
5. [Repository layout added by this migration](#5-repository-layout-added-by-this-migration)
6. [Prerequisites](#6-prerequisites)
7. [Install](#7-install)
8. [Building the compiled COBOL oracle — the five-step bootstrap](#8-building-the-compiled-cobol-oracle--the-five-step-bootstrap)
9. [Seeding a scenario](#9-seeding-a-scenario)
10. [Running both cycles](#10-running-both-cycles)
11. [Diffing state — the verification protocol](#11-diffing-state--the-verification-protocol)
12. [Tests](#12-tests)
13. [The four mandated deliverables](#13-the-four-mandated-deliverables)
14. [WARNING: known risks and gotchas](#14-warning-known-risks-and-gotchas)
15. [Relationship to the maintainer's own documentation](#15-relationship-to-the-maintainers-own-documentation)

---

## 1. What this is, and what it is not

`acas_posting` is a Python 3.12 clone of the ACAS batch posting cycle: the
sequence that carries entered transaction batches through validation, the
batch-control gate, posting to the Sales, Purchase and General ledgers
including the IRS postings the cycle reaches, and the period-total and
control-account updates that close it.

It is a **clone**, not an improvement. "Exact" has exactly one operational
meaning here, and every acceptance decision is made against it:

> the ordering-normalized diff of affected database tables after a Python run
> versus a COBOL run against an identical seed must be empty.

The COBOL remains in the repository, unmodified, serving simultaneously as the
specification and as the comparison oracle. The two roles are separate in
practice: the specification is read, and the oracle is run out of process by
the harness under `harness/` and never by the shipped package.

What that buys, and what it costs:

- The Python cycle can replace the COBOL cycle without changing a single
  posted figure. That is the entire value of the exercise.
- Nothing is tidied on the way through. Truncation that loses pence still
  loses pence, a double entry that posts half of itself still posts half of
  itself, and an account located by sequential read is still located by
  sequential read. §14 lists the ones most likely to tempt a reader.
- The shipped package needs **no COBOL compiler and no COBOL runtime**. Only
  the oracle does.

The migration covers posting, batch, cycle, period and proof behaviour and
every effect either store sees. It does not reproduce the interactive
data-entry screens, the menus, or report formatting that has no database
effect — see §4 for the rule that decides each case.

---

## 2. The six binding rules

The rules live in the AAP §0.7.2, retrievable through `review_prompt` rather
than `review_rules`. Two sentences of the user's own requirements are preserved
verbatim by the AAP itself (§0.8.2) because paraphrasing loses their force, and
they are quoted here for the same reason.

On where field metadata comes from:

> "The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative
> record-layout ↔ table mapping — it is the data dictionary for this
> migration."

That makes `common/*MT.scb` and `common/*MT.cbl` the source of truth for field
metadata, **ahead of the copybooks** — §13 gives the three-column proof of why
that distinction is not academic.

On what counts as correct:

> "There is no test suite: compiled COBOL execution is the behavioral
> specification, defects included. A defect reproduced is correct; a defect
> fixed is a failure."

That is the reason the anomaly log and the oracle harness are first-class
deliverables rather than scaffolding.

### R-1 — No COBOL at runtime

COBOL is the specification for this migration, not a runtime dependency of the
result.

**Consequence.** The shipped `acas_posting` package contains no subprocess
call, no foreign-function interface, no linkage to `cobmysqlapi.o` and no
linkage to the MySQL client library the COBOL side needs. Every COBOL
construct is reimplemented natively: `acas_posting/cobol/` reimplements
picture-clause parsing, the six numeric storage classes, the arithmetic verbs,
`MOVE` truncation, condition-name evaluation and `SORT` key semantics; the
twenty `acas_posting/dal/acas*.py` modules reimplement each handler-and-bridge
pair as SQL against the frozen schema; and `acas_posting/dates.py` reimplements
the date module in full, 1600-12-31 ordinal epoch included, rather than calling
it `[common/maps04.cbl:L39-L41]`.

`harness/` is a **sibling** of `acas_posting/`, not a sub-package, and
`pyproject.toml` names an explicit packaging allow-list of `acas_posting` and
its six sub-packages. There is therefore no import path from the shipped
package to the harness, and the prohibition is structural rather than a matter
of discipline.

### R-2 — Zero binary floating point

No accounting value may pass through a binary floating-point type — not in
computation, not in storage, not in transport.

**Consequence.** All monetary and quantity arithmetic runs on
`decimal.Decimal` with an explicit context: an un-`ROUNDED` COBOL store
truncates toward zero, and only the five `ROUNDED` sites listed in §14 round.
Binary integer fields are Python `int`, never `Decimal` and never `float` —
which is exactly what makes the integer truncation in the moving averages
reproducible rather than merely described. `pandas` and `numpy` are prohibited
outright, **including for the harness dump comparison**, which uses ordered row
sequences instead.

The frozen schema corroborates the rule from the other end: it contains
**zero** `FLOAT`, `DOUBLE` and `REAL` columns anywhere, so a float can never
arrive from the database either. `acas_posting/dal/connection.py` pins the
driver's converter explicitly rather than relying on its default.

### R-3 — No new validations, fields or schema changes; no concurrency

**Consequence.** No DDL of any kind is emitted; `mysql/ACASDB.sql` is read and
never written; there is no Alembic and no other migration tool, because with
the schema frozen a migration tool has nothing legitimate to do and its
presence would invite drift. SQLAlchemy is used at **Core level only** —
`text()` statements on an explicit `Connection` — and there is no ORM entity
layer and no declarative metadata that could generate schema.

The record modules mirror their copybooks field for field with nothing added,
preserving even the misnamings. Validation is copied, never extended: the date
module's six-part reject test is reproduced exactly as written
`[common/maps04.cbl:L140-L146]`, and the two silent skips in the nominal update
stay silent `[general/gl072.cbl:L291-L292]`, `[general/gl072.cbl:L306-L307]`.

Execution is strictly sequential. No threads, no `asyncio`, no
`multiprocessing`, no connection pooling; no parallel test runner and no plugin
that reorders execution, because posting order is load-bearing and the state
diff is order-sensitive.

### R-4 — Legacy anomalies reproduced, never fixed

Defects present in the compiled behaviour are part of the specification.

**Consequence.** `docs/migration/anomaly-log.md` carries 22 canonical entries,
each citing its locator and naming the Python module that reproduces it.
**Fourteen are locked in by tests** so that a future well-intentioned
correction fails the suite rather than passing unnoticed. The load-bearing ones
are reproduced with deliberate care: the missing terminating period stays a
nested conditional and is explicitly not normalised against its three sibling
programs; the credit-note average path's missing counter increment is left
missing; the three mutually inconsistent moving-average guards remain three;
the unbounded quarter subscript is left unbounded; and the sign lost at the
bridge is still lost at the bridge.

Frozen-file defects are worked around, never repaired — see the `exit 0`
warning in §8 and the two reasons in §9.

### R-5 — Full traceability

**Consequence.** `docs/migration/traceability.md` carries three tables:
program → module for all twelve programs, paragraph → function for every
migrated section and paragraph with the `GO TO` class annotated at each
transfer site, and field → dictionary entry. The third is mechanised rather
than hand-maintained: `acas_posting/dictionary/generate.py` builds
`data_dictionary/acas_posting_dictionary.json` from the authoritative triple,
`acas_posting_dictionary.schema.json` validates the result, and
`acas_posting/dictionary/loader.py` lets every record field cite its dictionary
key at run time. `acas_posting/dal/facade.py` publishes both the entity-named
and the handler-named verb vocabularies over one implementation, so a reader
following either COBOL calling convention finds a correspondingly named Python
function. Deliberate omissions are recorded **as** omissions.

### R-6 — Compiled behaviour is the tie-breaker

Where a semantic question is ambiguous, the compiled program's observed
behaviour decides it, and each resolution is documented rather than settled
silently.

**Consequence.** `docs/migration/ambiguity-resolutions.md` records each
question, the experiment run against the oracle, and the resolution adopted;
`docs/migration/scenario-diff-evidence.md` records the per-scenario evidence.
The harness exists to make that arbitration mechanically available — a MariaDB
service at the exact server version the schema was produced by
`[mysql/ACASDB.sql:L5]`, a GnuCOBOL image at the version the maintainer targets
`[common/comp-common.sh:L9]`, and the seed, run, dump, normalise and diff tools
described in §8 to §11.

The corollary that matters most in day-to-day work: expected values in the
arithmetic tier are **captured from the compiled oracle**, never derived by
reading the COBOL and reasoning about what it ought to produce.

---

## 3. What was migrated

Twelve COBOL programs, one Python module each. The module name carries the
COBOL program name so that traceability is mechanical rather than a matter of
memory.

| COBOL program | Python module | Role in the cycle |
| --- | --- | --- |
| `general/gl051.cbl` | `acas_posting/programs/gl051_batch_control_check.py` | Batch proof and the control-total gate — **partial**, see below |
| `general/gl070.cbl` | `acas_posting/programs/gl070_transaction_pre_process.py` | Phase 1 batch check, Phase 2 transaction pre-process |
| `general/gl071.cbl` | `acas_posting/programs/gl071_batch_sort.py` | Batch sort into nominal-key order |
| `general/gl072.cbl` | `acas_posting/programs/gl072_transaction_update.py` | Phase 4 transaction update — posts to the nominal ledger |
| `general/gl080.cbl` | `acas_posting/programs/gl080_end_of_cycle.py` | Phase 3 transaction deletion, Phase 5 end-of-period |
| `sales/sl055.cbl` | `acas_posting/programs/sl055_invoice_extract_analysis.py` | Sales invoice extract and analysis-total build |
| `sales/sl060.cbl` | `acas_posting/programs/sl060_invoice_posting.py` | Sales invoice posting, including the IRS fan-out |
| `sales/sl100.cbl` | `acas_posting/programs/sl100_cash_posting.py` | Sales cash and receipt posting |
| `purchase/pl055.cbl` | `acas_posting/programs/pl055_order_proof_extract.py` | Purchase order proof extract |
| `purchase/pl060.cbl` | `acas_posting/programs/pl060_order_posting.py` | Purchase order posting, including the IRS fan-out |
| `purchase/pl100.cbl` | `acas_posting/programs/pl100_payment_posting.py` | Purchase payment posting |
| `irs/irs030.cbl` | `acas_posting/programs/irs030_posting.py` | IRS nominal-ledger posting — **partial**, see below |

Underneath them: 20 data-access modules `acas_posting/dal/acas*.py`, one per
frozen file handler rather than one per table, because the handlers are not
one-to-one with tables — `acas000` dispatches to four bridges by key number,
and both `acas016` and `acas026` own a header table plus a lines table.
Mirroring the handler boundary keeps the Python module set in exact
correspondence with the COBOL programs the traceability document has to map.

### The two partial boundaries — do not widen them

Two of the twelve are migrated **only in part**. Both files are otherwise
dominated by interactive code that is out of scope, so an agent working from
the file rather than from the stated boundary would migrate several hundred
lines that must not be migrated.

- **`general/gl051.cbl` — only the control-total gate**: the `batch-print`
  section §999 and its `end-batch` paragraph,
  `[general/gl051.cbl:L1096-L1133]`. The paragraph's closing
  `go to main-exit.` is `[general/gl051.cbl:L1134]`. Everything else in that
  1282-line program — screen sections, accept loops, the amendment dialogs — is
  out of scope.
- **`irs/irs030.cbl` — only `Ledger-Postings-Add`**:
  `[irs/irs030.cbl:L1569-L1733]`, which is the section that walks the transfer
  file and updates the IRS nominal ledger. `L1733` is the end of the file. The
  interactive posting-entry program around it is out of scope, with one
  exception noted in §4: the end-of-job question that decides whether the
  transfer file is cleared `[irs/irs030.cbl:L1715-L1724]` gates a database write
  and therefore becomes a CLI parameter.

The two VAT computes the posting path consumes, in the `Net` and `Gross`
sections `[irs/irs030.cbl:L1551]`, `[irs/irs030.cbl:L1562]`, are in scope for
the same reason: the posting path reads their result.

### Phase order, and the labelling quirk

The General Ledger cycle runs in this order:

1. batch check;
2. transaction pre-process;
3. sort;
4. transaction update;
5. transaction deletion and end-of-period processing.

The programs label their own phases on screen — "Phase - 1. Batch Check"
`[general/gl070.cbl:L284]`, "Phase - 2. Transaction Pre-process"
`[general/gl070.cbl:L292]`, "Phase - 4. Transaction Update"
`[general/gl072.cbl:L274]`, and both "Phase - 3. Transaction Deletion" and
"Phase - 5. End of Period Processing" inside `gl080`. **The labels are not
execution order**: deletion is labelled Phase 3 but executes after Phase 4.
The module docstrings say so, so that a maintainer reading the label is not
misled.

---

## 4. What was excluded, and why

Frozen — read as specification, **zero modifications of any kind**:

- all COBOL under `common/`, `general/`, `sales/`, `purchase/`, `irs/`,
  `stock/` and `copybooks/`;
- the bridge programs `common/*MT.scb` and `common/*MT.cbl`;
- the schema `mysql/ACASDB.sql`;
- the maintainer's build and load scripts, including `comp-all.sh`,
  `common/comp-common.sh` and `common/masterLD.sh`;
- `etc/ld.so.conf.d/gnucobol.conf`, and the three vendored source archives at
  the repository root.

Out of scope for migration:

- **Interactive data-entry, amendment, setup and menu programs** —
  `common/ACAS.cbl`, `general/general.cbl`, `sales/sales.cbl`,
  `purchase/purchase.cbl`, `irs/irs.cbl`, the `gl000`/`gl0x0`, `sl0x0`,
  `pl0x0` and `irs0x0` series, all of `general/gl051.cbl` **except** its
  control-total block, and all of `irs/irs030.cbl` **except**
  `Ledger-Postings-Add`.
- **Report formatting beyond database effects**, and the
  `call "SYSTEM" using Print-Report` spool-out path wherever it appears — it
  hands a report file to the operating system and touches no table.
- **Non-posting utilities** — `common/*UNL.cbl` (unload), `common/*RES.cbl`
  (restore), the table-maker and take-on programs, `common/dummy-rdbmsMT.cbl`,
  `common/sys002.cbl`, `common/fhlogger.cbl`, `common/ACAS-Sysout.cbl`, and the
  backup and PDF shell scripts.
- **Legacy-language artifacts** — `Basic-Code/` in its entirety, `payroll/`
  including `payroll/Basic-Code/` and `payroll/payroll_schema.sql`, and
  `home/vince/Installed-SW/`.
- **Subsystems the posting cycle does not reach** — `stock/`, the sales
  `sl800` autogen series, the purchase `pl800` series, `common/xl150.cbl`, and
  the sort-only satellites.
- **Eleven out-of-scope tables**, present in the frozen schema but never
  touched by the cycle: `STOCK-REC`, `STOCKAUDIT-REC`, `DELIVERY-REC`,
  `PUDELINV-REC`, `SADELINV-REC`, `SAAUTOGEN-REC`, `SAAUTOGEN-LINES-REC`,
  `PUAUTOGEN-REC`, `PUAUTOGEN-LINES-REC`, `PLPAY-REC` and `PLPAY-RECrg01`, with
  their eight bridges — `auditMT`, `deliveryMT`, `delfolioMT`,
  `sldelinvnosMT`, `stockMT`, `paymentsMT`, `plautogenMT` and `slautogenMT`.
  22 in scope plus 11 out of scope accounts for all 33 tables in the schema.
- **Schema evolution of any kind** — no new tables, columns, indexes,
  constraints, views, triggers or DDL statements, and no migration tooling.
- **Concurrency** — no threads, no `asyncio`, no `multiprocessing`, no
  connection pooling.
- **New surfaces** — no web tier, no REST API, no GUI, no ORM entity layer, no
  message queue, no caching layer.
- **Behaviour changes of any kind**, including bug fixes, added validations,
  improved error messages and "cleaned up" rounding.

### The three-way rule for presentation code

Screen statements are interleaved with business logic in the same paragraphs
throughout the frozen source, so removing the presentation layer needs a rule
rather than a judgement call. This one is applied uniformly, and it explains
most apparent omissions:

1. **A diagnostic `DISPLAY` with no database effect becomes a log record** at a
   severity matching the original's intent. It must not alter control flow and
   must never appear in a table dump.
2. **An `ACCEPT` that gates a database write becomes an explicit CLI
   parameter**, with the COBOL default preserved. The clearest case is the
   end-of-job question in the IRS posting section that decides whether the
   transfer file is cleared `[irs/irs030.cbl:L1715-L1724]`: answering yes
   performs an open-output that deletes every row, so the answer is a genuine
   input to the migrated program rather than decoration.
3. **An `ACCEPT` that merely pauses for acknowledgement is dropped**, since its
   only effect is to block a terminal. Where such a prompt sits inside an error
   path that then transfers control, **the control transfer is preserved** and
   only the pause is removed.

---

## 5. Repository layout added by this migration

Everything below is **added** at the repository root, alongside the existing
COBOL directories. **Nothing in the existing tree was relocated, renamed or
restructured** — a constraint that follows from the freeze on the COBOL source
and that also keeps the maintainer's own build scripts working unchanged.

```text
acas_posting/                 the migrated cycle. No COBOL, no subprocess call.
├── cli/                      7 batch entry points + argv binding
├── programs/                 the 12 program modules; business logic lives ONLY here
├── records/                  the record dataclasses, one per copybook
├── cobol/                    COBOL language semantics; ZERO business logic
├── dal/                      data access; SQL against the frozen schema, no ORM
├── dictionary/               the dictionary model, generator and runtime loader
├── __main__.py               `python -m acas_posting` — the router
├── clock.py                  the controlled clock: pins to-day AND Run-Date
├── dates.py                  common/maps04.cbl plus the zz050/zz060/zz070 wrappers
└── workfiles.py              pretrans.tmp / postrans.tmp as ordered sequences

data_dictionary/              the generated machine-readable dictionary + its JSON Schema
docs/migration/               traceability, anomaly log, ambiguity resolutions, diff evidence
tests/
├── arithmetic/               unit-level parity. No database, no COBOL, no Docker
├── scenarios/                end-to-end state parity. Needs the Compose stack
└── determinism/              two runs under one pinned clock must be byte-identical
harness/                      the compiled oracle. NEVER on the package import path
└── scenarios/                9 YAML definitions: the 8 mandated + end_of_cycle_gl
pyproject.toml                requires-python "==3.12.*", pinned deps, pytest config
requirements.txt              ALL THREE dependency sets, hash-pinned, in one file
README-python-migration.md    this file
```

### 5.1 Files present beyond the plan's illustrative tree, and their basis

Agent Action Plan §0.3.1 draws the target structure as a tree with `harness/`'s
scripts enumerated one by one. Reading that tree as an exhaustive whitelist is a
natural mistake and a code review made it, so the basis for every file outside it
is recorded here rather than left to be re-litigated.

**Scope is set by §0.2, whose job is defining scope, and §0.2 uses trailing
wildcards.** §0.2.1.2 lists `acas_posting/cli/*.py` and `harness/*`; §0.2.1.3
lists `harness/**`; and §0.4.4's wildcard table repeats
`acas_posting/cli/*.py`, adding that wildcards "are used only where a group is
genuinely uniform, and are always **trailing**." §0.3.1 is *Refactored Structure
Planning* — a plan of the structure — and §0.4.4 says outright that the harness
scripts "are listed individually in §0.4.1 rather than folded into a pattern,
**because each has a distinct source and a distinct set of changes**", which is a
statement about documentation granularity, not about exclusivity.

Four files sit outside the illustrative tree and inside those patterns:

| File | Covered by | Why it exists rather than being folded into a listed file |
| --- | --- | --- |
| `acas_posting/cli/rdbms_params.py` | `acas_posting/cli/*.py` (§0.2.1.2, §0.4.4) | The single process-boundary resolver for connection parameters and the fail-closed plaintext policy. §0.4.1.1 gives `cli/args.py` a different job — binding argv to `WS-Calling-Data` — and putting deployment security policy inside the argument binder would couple two concerns that are separately testable, and separately wrong when coupled |
| `harness/run_parity.sh` | `harness/*` (§0.2.1.2), `harness/**` (§0.2.1.3) | The ten-stage protocol driver. §0.8.5 defines acceptance as *seed → run compiled → dump → reset → run Python → dump → diff*, and §0.3.2 says explicitly that deterministic staged orchestration "justifies the rigid stage ordering baked into the harness scripts". One driver that cannot be run out of order **is** that design; the alternative is a documented sequence a human retypes, which is the failure mode §0.3.2 warns against |
| `harness/build_fixtures.sh` | `harness/*`, `harness/**` | Generates the seed flat files each scenario declares. §0.2.1.1 puts `common/masterLD.sh` and the `*LD.cbl` loaders in scope "as the specification for how the harness seeds a scenario", and §0.4.1.7 gives `harness/seed.sh` the job of reproducing that per-file contract — which presupposes the files exist. Something has to produce them |
| `harness/make_fixtures.py` | `harness/*`, `harness/**` | The generator `build_fixtures.sh` drives. It is separate because it emits COBOL, and emitting COBOL safely requires the literal-encoding guard that a shell script cannot express — see §12's note on generated-source safety |

**What was NOT retained on this reasoning.** The same review flagged
`requirements-harness.txt` and `requirements-dev.txt`, and those were **removed**,
because §0.2.1.2 names the dependency artifacts *without* a wildcard — exactly two
files, `pyproject.toml` and `requirements.txt` — and §0.5.1 states the inventory as
one table. A named list and a trailing wildcard are different instruments, and the
distinction is the whole reason four files were kept and two were not. §7 records
the consolidation.

Three structural decisions in that layout are load-bearing rather than
stylistic:

- **`harness/` is a sibling, not a sub-package.** The oracle must be reachable
  by the tests and unreachable from the shipped code. A sibling directory
  excluded from packaging enforces that structurally (R-1).
- **`cobol/` holds no business logic and `programs/` holds no numeric
  primitives.** That split is what makes the arithmetic tier possible: every
  picture-clause, packed-decimal, truncation and `MOVE` rule can be tested in
  isolation with no database and no scenario setup, and any parity failure then
  localises to one layer or the other.
- **Work files are in-process sequences**, not tables and not temporary files.
  `pretrans.tmp` and `postrans.tmp` are transient scratch files belonging to
  `gl071` `[copybooks/wsnames.cob:L15-L16]`, so nothing about them reaches the
  database and nothing about them appears in a table dump.

### 5.1 Four files the plan covers by wildcard rather than by name

The Agent Action Plan names most target files individually, but four are reached
only through its **trailing wildcards**. They are listed here explicitly, because
a reader comparing the tree against the plan's per-file tables will not find them
there and should not have to guess whether they were smuggled in.

| File | Covered by | Why it exists |
|---|---|---|
| `acas_posting/cli/rdbms_params.py` | §0.2.1.2 "Package and entry points: … `acas_posting/cli/*.py`", repeated in the §0.4.4 pattern table | The connection parameters the frozen COBOL reads from `~/ACAS/acas.param` and the `RDB-Data` block `[copybooks/wsfnctn.cob:L57-L64]`, including the carrier widths — `DB-Port` reaches the bridges through a FOUR-character carrier `[common/acas-get-params.cbl:L158]`, `[copybooks/mysql-variables.cpy:L91]`, while the stored width is five `[copybooks/wssystem.cob:L142]`. Keeping that in one module is what lets every client agree on it. |
| `harness/build_fixtures.sh` | §0.2.1.2 "Oracle harness: `harness/*`" | The frozen loaders read COBOL flat files, and most are `ORGANIZATION INDEXED` — a Berkeley DB Btree whose on-disk form belongs to the library version the image carries. Fixtures must therefore be **generated by compiled COBOL**, not hand-written. See §8.8. |
| `harness/make_fixtures.py` | §0.2.1.2 "Oracle harness: `harness/*`" | Generates the per-file COBOL writer that `build_fixtures.sh` compiles, from each scenario's `seed_records`, so no record layout is ever restated by hand. |
| `harness/run_parity.sh` | §0.2.1.2 "Oracle harness: `harness/*`" | The fail-closed ten-stage driver. The ordering *is* the evidence (§11.1), so a driver that aborts at the first non-zero and passes that status through verbatim is what stops a partial capture being carried forward. |

**The artifact boundary, measured rather than asserted.** Building the wheel and
listing it shows the boundary holds: the distribution contains **only**
`acas_posting/` and its `dist-info`. No `harness/`, no `tests/`, no `.cbl`,
`.cob` or `.scb`, and no `.sql`. `pyproject.toml` sets
`include-package-data = false` and names the two dictionary artifacts file by file
rather than by glob, so nothing that lands in the checkout can reach the wheel by
accident. `acas_posting.data_dictionary` is a **data directory, not an importable
package** — it holds no module and is mapped from the top-level
`data_dictionary/` through `[tool.setuptools.package-dir]`, reached only through
`importlib.resources`.

So of the four, exactly one ships — `rdbms_params.py`, which is a CLI module and
belongs in the package the plan describes — and the three harness files do not,
which is what R-1 requires of them.

### Import boundaries — the layering contract

This table is the contract. It keeps the dependency graph acyclic, keeps the
record layer a leaf, and keeps the harness off the shipped package's import
path.

| Module group | May import | Must not import |
| --- | --- | --- |
| `acas_posting/cobol/*.py` | `dictionary.loader` only | `records`, `dal`, `programs`, `cli`, `harness` |
| `acas_posting/records/*.py` | `cobol.field`, `dictionary.loader` | anything else — this layer is a leaf |
| `acas_posting/dal/acas*.py` | `dal.connection`, `dal.status`, `dal.cursor_state`, one `records` module | `programs`, `cli`, other `dal.acas*`, `harness` |
| `acas_posting/programs/*.py` | `records`, `dal.facade`, `cobol.arithmetic`, `cobol.move`, `cobol.condition_names`, `dates`, `workfiles` | `cli`, `dal.acas*` directly, `harness` |
| `acas_posting/cli/*.py` | `programs`, `clock`, `cli.args` | `dal.acas*` directly, `harness` |
| `tests/arithmetic/*` | `cobol`, `records` | `dal`, any database |
| `tests/scenarios/*` | `cli`, the shared harness helpers | `dal` internals |
| `harness/*` | the standard library, `PyYAML`, the driver | `acas_posting` internals other than the CLI |

---

## 6. Prerequisites

- **CPython 3.12.** `pyproject.toml` pins `requires-python = "==3.12.*"`, and
  the pin is deliberately tight. What matters is that this interpreter's
  `decimal` module is backed by the C `_decimal` implementation (`libmpdec`)
  rather than the pure-Python fallback: every monetary operation in the cycle
  passes through it, and truncation behaviour was verified on the interpreter in
  use rather than assumed. The AAP's reference interpreter was **3.12.3** with
  `libmpdec` 2.5.1; the interpreter this checkout is exercised on is 3.12.13.
  Both are C-backed. A pure-Python `decimal` build is not accepted as parity
  evidence, and 3.13 is outside the evidence entirely.
- **Docker Engine with Compose v2** — required **only** for the compiled oracle
  and the scenario and determinism tiers.
- **`openssl`** or an equivalent, if harness credentials have to be generated.

`tests/arithmetic/` needs **no Docker, no MariaDB and no GnuCOBOL**. It imports
only `acas_posting.cobol` and `acas_posting.records`, touches no database, and
runs anywhere a 3.12 interpreter runs.

---

## 7. Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
```

That one command installs all thirteen pinned distributions — **70 hashes across
13 pins**, every artifact verified. For editable development, which installs the
same pins through the manifest and lets you take one set at a time:

```bash
python -m pip install --no-build-isolation -e '.[test]'      # runtime + test
python -m pip install --no-build-isolation -e '.[harness]'   # runtime + harness
```

**Why one lock file rather than three.** Agent Action Plan §0.2.1.2 names exactly
two dependency artifacts — `pyproject.toml` and `requirements.txt` — and §0.5.1
states the inventory as one table covering all five named packages. This project
briefly carried `requirements-harness.txt` and `requirements-dev.txt` as well,
which added two manifests the plan does not name; they are consolidated into
`requirements.txt` as three labelled sections. Nothing was lost in the merge: the
sets are still pairwise disjoint, `pyproject.toml`'s optional-dependency groups
still map one-to-one onto the sections, and every pin and every hash carried over
unchanged.

The three dependency sets are pairwise disjoint and exact. Every direct
dependency, with its pin:

| Set | Package | Pin | Why it is here |
| --- | --- | --- | --- |
| runtime | `mysql-connector-python` | `26.7.0` | The only third-party module `acas_posting` imports. Materialises `DECIMAL` as `Decimal` and integer columns as `int`, never as a float (R-2) |
| runtime | `SQLAlchemy` | `2.0.51` | **Core level only** — `text()` statements on an explicit `Connection`. No ORM entity layer, no declarative metadata, no schema generation (R-3) |
| runtime | `greenlet` | `3.5.4` | SQLAlchemy's own requirement, pinned for reproducibility. Nothing imports it and nothing calls `create_async_engine` |
| runtime | `typing_extensions` | `4.16.0` | SQLAlchemy's own requirement, pinned for reproducibility |
| harness | `PyYAML` | `6.0.3` | Parses the nine scenario definitions under `harness/scenarios/` |
| dev | `pytest` | `9.1.1` | The test runner |
| dev | `pytest-cov` | `7.1.0` | Coverage as traceability evidence (R-5), **not** a quality gate |

`coverage`, `pluggy`, `iniconfig`, `packaging`, `Pygments` and the `setuptools`
build backend are pinned alongside them in `requirements.txt`'s section 3.

Two contracts worth stating because breaking either is a defect rather than a
preference:

- **Pin parity.** `pyproject.toml` and the three `requirements*.txt` files
  carry identical exact versions. A version that differs between them is a
  defect, not a variation.
- **Do not upgrade.** A driver or runtime change can move a stored penny, and
  the only acceptable proof of equivalence is an empty scenario diff against the
  compiled oracle. "Checking for newer" is not an improvement here.

Deliberately absent, and not to be added: `pandas` and `numpy` (R-2), any ORM
entity layer or migration tool (R-3), any async, thread-pool or
connection-pool helper (R-3), any parallel or randomising pytest plugin, and any
third-party date library — the date semantics being reproduced belong to a
specific COBOL program with a non-standard epoch, and a general-purpose library
would be *more correct than the specification*, which is the one outcome to
avoid.

---

## 8. Building the compiled COBOL oracle — the five-step bootstrap

### 8.1 Bring up the stack

The stack has two services: MariaDB at the server version the frozen schema was
produced by, and a GnuCOBOL builder and runner. The repository is mounted
**read-only** at `/repo`; the writable build tree is a named volume at `/build`.
No build and no run can therefore modify the frozen COBOL, bridges or schema.

Credentials have **no committed defaults** — every credential variable is
written `${VAR:?message}`, so an unset value makes Compose refuse to render
rather than provisioning a predictable account. `CLONE_INDEX` namespaces the
project, network and volumes so sibling checkouts cannot share one oracle's
state.

```bash
export CLONE_INDEX=001
export MARIADB_ROOT_PASSWORD="$(openssl rand -base64 24)"
export ACAS_DB_USER=acas
export ACAS_DB_PASSWORD="$(openssl rand -base64 9)"
docker compose -f harness/docker-compose.yml up -d mariadb
```

WARNING: keep the database name, user and password to **12 characters or
fewer**. `DB-Schema`, `DB-UName` and `DB-UPass` are `pic x(12)` in the frozen
connection block `[copybooks/wsfnctn.cob:L57-L59]`, so the COBOL side truncates
a longer value silently while the Python side sends it whole — and the two
cycles then authenticate differently. The harness refuses an over-long value up
front rather than letting it surface later as "credentials rejected".

WARNING: the database **port must be 1 to 9999**, not 1 to 65535. The value
travels through `LK-Port-Number pic x(4)`
`[common/acas-get-params.cbl:L158]` and `01 Ws-Mysql-Port-Number pic x(4)`
`[copybooks/mysql-variables.cpy:L91]`, and every bridge `STRING`s `DB-Port` into
the second of them `[common/glpostingMT.cbl:L410-L413]` — **four characters**. A
five-digit port such as `13306` therefore reaches the compiled cycle as `1330`
while the harness would probe, drive and dump the untruncated one, so the two
sides of the comparison would be talking to two different servers. `RDBMS-Port
pic x(5)` `[copybooks/wssystem.cob:L142]` is the *stored* width, not the
carrier. Every harness script and `harness/dump_tables.py` refuse anything wider
up front. Compose publishes `3306`.

### 8.1a The transport declaration — one key, one closed set

An isolated harness network has no TLS material, so every script and the shipped
package refuse a **non-loopback** target unless the operator either names a
certificate authority or declares the network isolated. There is exactly **one**
name for that declaration and **one** set of spellings for it:

| | |
|---|---|
| Key | `ACAS_DB_ALLOW_PLAINTEXT` |
| Yes | `1`, `true`, `yes`, `on` (case-insensitive) |
| No | `0`, `false`, `no`, `off`, or unset |
| Anything else | **refused** — the run stops and names the accepted spellings |
| Command line | `--db-allow-plaintext` on every route, which **outranks** the environment |
| Encrypted alternative | `ACAS_DB_TLS_CA` (plus `ACAS_DB_TLS_CERT` + `ACAS_DB_TLS_KEY` together) |

`harness/docker-compose.yml` sets it for the internal network. The five harness
scripts read it, and so does the shipped package, through one function —
`acas_posting/cli/rdbms_params.read_declared_flag`, which
`acas_posting/cli/args.py` also uses — so one exported value means one thing
everywhere. Writing `false` grants nothing, and unrecognised text stops the run
rather than resolving to either answer: this variable decides whether a
credential and every posted figure may cross a network in the clear, and only
the operator who typed it knows what was meant.

Define the runner shorthand used throughout §8 to §11:

```bash
C="docker compose -f harness/docker-compose.yml run --rm -T \
     -e ACAS_SEED_AUTOCOMMIT=on gnucobol"
```

`-T` is required on every scripted stage: a tty is allocated by default and a
piped stage would appear to hang. Redirect stdin from `/dev/null` as well when a
command is backgrounded.

⚠️ **`ACAS_SEED_AUTOCOMMIT=on` is REQUIRED, not a convenience.** Without it every
seeding stage — `harness/seed.sh`, `harness/reset_db.sh` and therefore stages 1
and 5 of the driver — exits **76**, "the seed reported success and left no rows".
That is not a harness bug: it is the reproduced legacy defect. The frozen loaders
reach **no** `COMMIT` and **no** `ROLLBACK` — across all 28 `common/*LD.cbl`
every `perform aa020-Rollback` is commented out, 78 sites and none live, and
`perform aa030-Commit` occurs exactly once anywhere, at
`[common/irsdfltLD.cbl:L437]`, commented out too — so with autocommit off they
report success and persist nothing. The maintainer recorded the same observation
himself at `[common/analLD.cbl:L442]`. Nothing in the harness issues the missing
`COMMIT`, because a defect fixed is a failure (R-4); the harness makes the
*operating precondition* explicit and refuses to seed silently without it. The
whole arbitration is question `Q-10` in
[`docs/migration/ambiguity-resolutions.md`](docs/migration/ambiguity-resolutions.md).

### 8.2 Build the oracle

One command:

```bash
$C /repo/harness/build_oracle.sh
```

To repeat a build while deliberately preserving the existing writable build
tree, or to resume at a step:

```bash
$C /repo/harness/build_oracle.sh --no-refresh
$C /repo/harness/build_oracle.sh --from 4
$C /repo/harness/build_oracle.sh --help
```

### 8.3 What the five steps are

`harness/build_oracle.sh` performs the bootstrap in this order, in a writable
build copy of the tree. The order is not negotiable — each step produces what
the next one links against.

**Step 1 — unpack the vendored `presql2-latest.zip`.** It expands to
`presql2-package/`. The archive itself is **never modified in the checkout**;
it is unpacked inside the container.

**Step 2 — compile the bridge's C interface object, `cobmysqlapi.o`.**

WARNING: this is the step that will otherwise waste your day. Every bridge,
handler and loader compile links an object file `cobmysqlapi.o` that provides
the C interface between COBOL and the MySQL client library —
`[common/comp-common.sh:L26]`, `[common/comp-common.sh:L32]`,
`[common/comp-common.sh:L34]`, `[common/comp-common.sh:L51]`, 56 compile lines
in total. **That object file is absent from the checkout, and no rule anywhere
in the repository builds it.** Following the compile scripts alone, the oracle
cannot be built at all: the build fails at link time with no obvious cause.

The rule was recovered from the vendored package, where
`presql2-package/cobmysqlapi38.sh` consists of exactly one line:

```bash
gcc -I/usr/local/mysql/include -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC
```

The object is then placed in each compile directory, because every frozen
compile links the bare filename `cobmysqlapi.o` resolved against the current
directory.

WARNING: the package also ships two **superseded** variants of that C source —
`presql2-package/old-apis/cobmysqlapi.005.c` and
`presql2-package/old-apis/cobmysqlapi3.c`. They must **NOT** be used. Only
`cobmysqlapi38.c` is current.

**Step 3 — build and install the `presql2` translator onto the PATH.** JC
preSQL **1.14f**. `presql2-package/presql2.sh` is a single line:

```bash
cobc -x presql2.cbl cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
```

`presql2-package/bldcopy2.sh` and `presql2-package/prtschema2.sh` follow the
same pattern, and `presql2-package/ACAS/comp-stockMT.sh` is a worked example
that compiles a bridge exactly as ACAS does:

```bash
cobc -m stockMT.COB cobmysqlapi.o -L/usr/local/mysql/lib -lmysqlclient -lz
```

The build script reproduces that worked example as a toolchain proof before
proceeding; `--skip-preflight-link` skips it.

WARNING: never invoke `presql2` without redirecting stdin. It prompts
interactively and will spin. It also truncates its output file *before*
validating its parameters, which is exactly why the build runs in a copy: doing
it inside the checkout would zero the 28 generated `common/*MT.cbl` bridges —
the authoritative record-layout-to-table mapping.

**Step 4 — run the maintainer's `common/comp-common.sh`, unmodified.** It runs
`presql2` over each `*MT.scb` `[common/comp-common.sh:L25]`, then compiles the
bridges, the 17 handlers, the loaders and the menu executables, each linking
`cobmysqlapi.o` with `-I ../copybooks -Wlinkage -L/usr/local/mysql/lib
-lmysqlclient -lz` `[common/comp-common.sh:L26]`. It also compiles
`accept_numeric.c` with `-lncursesw` `[common/comp-common.sh:L18]`, so the
image needs `ncursesw`.

**Step 5 — run `comp-all.sh`, unmodified.** It exports `COBCPY=../copybooks`
and `COB_COPY_DIR=../copybooks` `[comp-all.sh:L9-L10]`, then compiles the
sub-systems in the maintainer's own order `[comp-all.sh:L15-L32]`:

```text
common → general → irs → purchase → sales → stock
```

### 8.4 Toolchain versions — every one from repository evidence

| Component | Version | Evidence |
| --- | --- | --- |
| GnuCOBOL `cobc` | 3.2 final | `[common/comp-common.sh:L9]`, corroborated by `[README.TXT:L53]` |
| MariaDB server | 10.11.7-MariaDB | `[mysql/ACASDB.sql:L1]`, `[mysql/ACASDB.sql:L5]` |
| MariaDB Connector/C | 3.3.4 | vendored as `mariadb-connector-c-3.3.4-src.zip` |
| MySQL Connector/C | 6.1.11 | vendored as `mysql-connector-c-6.1.11-src.tar.gz` |
| JC preSQL (`presql2`) | 1.14f | vendored as `presql2-latest.zip`; the package's own `README.SVN` states it |
| Docker Compose | v2 specification | the harness must be runnable in local Docker |

### 8.5 Compiler flags — default arithmetic, and the harness must not alter it

A census of every compile invocation in the repository finds **no `-std=`
dialect selection**, **no `>>SET ARITHMETIC` directive in any source**, and **no
`binary-truncate` flag anywhere**. The compiler is therefore invoked with
default arithmetic, and the migration's truncation and rounding behaviour
depends on exactly that. **The harness must not change a single `cobc` flag.**

The flags actually used are diagnostic and linkage-related: `-Wlinkage`,
`-I ../copybooks`, `-m` for dynamically loadable modules, `-x` for executables,
`-L/usr/local/mysql/lib -lmysqlclient -lz`, `-T` for listings, and
`-Wno-goto-section`. That last one is worth noticing rather than skipping past:
the maintainer added it to suppress the warning about inter-section `GO TO`
`[common/comp-common.sh:L8-L9]`, which confirms that such transfers are
pervasive and intentional in this codebase rather than incidental.

The MySQL client must be installed under the prefix the frozen scripts expect,
`/usr/local/mysql`, and the image reproduces the repository's own runtime
loader search path `[etc/ld.so.conf.d/gnucobol.conf]`, in this order:

```text
/usr/local/lib/gnucobol
/usr/local/lib
/usr/local/mysql/lib
/usr/lib
```

### 8.6 WARNING: the compile scripts are not success signals

`common/comp-common.sh` ends in a bare, unconditional `exit 0`
`[common/comp-common.sh:L59]`, and `comp-all.sh` does the same
`[comp-all.sh:L45]` immediately after printing

```text
We Are all done but check for any error or warning messages
```

`[comp-all.sh:L44]`. Their exit status is therefore **not** a build-success
signal, and neither `set -e` nor `pipefail` can see a failed compile through
them. `harness/build_oracle.sh` scans the diagnostics itself, asserts that the
expected programs, handlers, loaders and `*MT` bridges are all present, and
fails closed.

These are frozen files. They are **worked around, never fixed** (R-4).

### 8.7 WARNING: one copybook is missing from the frozen archive

`copybooks/ACAS-SQLstate-error-list.cob` is **absent from the checkout** while
being `COPY`'d by dozens of frozen files, most of them `*MT` bridges. Left
alone, the majority of bridges fail to compile and the oracle cannot be built.

It is **not fabricated into the frozen tree**, because inventing a frozen source
file would breach R-3 and R-4. Instead `harness/build_oracle.sh` materialises an
idempotent, comments-only compatibility include under the writable build copy's
`copybooks/` directory — `harness/copybook-shims/ACAS-SQLstate-error-list.cob`.
Every frozen `COPY` site expands it inside the Identification Division's
Remarks paragraph, before any Data Division begins, so the include changes no
COBOL behaviour; the executable SQLSTATE handling lives elsewhere and is
untouched. The checkout's own `copybooks/` directory is never written.
`docs/migration/ambiguity-resolutions.md` §10.1 records this as a build blocker
resolved without touching the freeze.

### 8.8 Build the scenario fixtures

The frozen loaders read COBOL flat files, and most of them are `ORGANIZATION
INDEXED` or `RELATIVE` — on this toolchain an indexed file is a Berkeley DB
Btree whose on-disk form belongs to the library version the image carries, which
is measurable rather than assumable. So each scenario declares its **records**
as text under `seed_records`, and the builder generates a COBOL writer per file,
compiles it against the frozen copybooks, calls the frozen handler to write,
then reads every file back through the same definitions and refuses the build
unless the counts agree. No record layout is restated anywhere.

```bash
$C /repo/harness/build_fixtures.sh                 # all scenarios
$C /repo/harness/build_fixtures.sh clean_batch_gl  # one scenario
```

The fixture stage is **not optional**, and it comes second for that reason.
Generated fixtures and log files are owner-only; the builder refuses a result
carrying any group or other permission.

### 8.9 The provenance attestation, and why a partial build cannot produce evidence

Under R-6 the compiled COBOL *is* the specification, so which bytes were compiled
is not an operational detail — it is the identity of the specification itself. A
full run of `harness/build_oracle.sh` therefore ends by publishing a provenance
attestation at `$ACAS_BUILD/oracle-attestation.txt`, mode `0444`, as flat
TAB-separated `key<TAB>value` lines needing no parser:

| Recorded | Why it is recorded |
|---|---|
| `presql2-archive`, `presql2-sha256`, `presql2-pinned-sha256`, `presql2-matches-pin` | The translator in that archive turns every `*MT.scb` into the `*MT.cbl` bridge that is actually compiled. A different archive is a different specification. |
| `presql2-digest-override` | Whether `ACAS_PRESQL2_SHA256` was used to accept an archive other than the pinned one. |
| `cobmysqlapi-object`, `cobmysqlapi-sha256`, `cobmysqlapi-redirected`, `cobmysqlapi-provenance` | The C interface every bridge, handler and loader links. The vendored package also ships two **superseded** sources (`old-apis/cobmysqlapi.005.c`, `old-apis/cobmysqlapi3.c`) alongside the current `cobmysqlapi38.c`, so an object of unrecorded origin could be a build of either. |
| `cobc-version`, `cobc-path`, `cobc-sha256`, `cc-version`, `cc-path`, `cc-sha256` | A version string is what a compiler says about itself; the digest is what it is. |
| `module-count`, `module-set-sha256` | Every `*.so` under the six compile directories, sorted by path, each hashed, the listing hashed again. This is what binds the attestation to the artifacts. |
| `overrides-used` | The single verdict: `no` means this oracle may produce evidence. |

`harness/run_parity.sh` **requires** the attestation before stage 2 and refuses to
run the compiled cycle without it. It re-derives rather than trusts: it checks the
recorded archive digest equals the recorded pin, requires
`cobmysqlapi-provenance` to be one of the two legitimate values, and re-computes
the module-set digest from the modules **on disk** so that replacing a single
`.so` after the build is caught.

Two consequences to plan around:

- **`--only N` and `--from N` do not publish an attestation.** They are debugging
  modes and a partly-rebuilt tree is only partly this repository's. Build fully
  before producing evidence.
- **Setting `ACAS_PRESQL2_SHA256`, or pointing `ACAS_COBMYSQLAPI_OBJ` anywhere
  other than `/usr/local/lib/acas/cobmysqlapi.o`, permanently marks that build as
  unable to produce evidence.** The build still completes and still warns; the
  parity driver then refuses it. To replace either legitimately, make it a
  **reviewed source change** — update the vendored archive and
  `ACAS_PRESQL2_SHA256_EXPECTED` together in the same commit — rather than setting
  a variable at run time.

`ACAS_COBMYSQLAPI_OBJ` pointing at `/usr/local/lib/acas/cobmysqlapi.o` is **not**
an override. `harness/Dockerfile.gnucobol` exports that variable and builds the
object at that path from the vendored source with the recovered rule verbatim, so
reusing it is the normal case and is attested as
`image-built-from-vendored-source`.

`module-set-sha256` is **not** evidence of a reproducible build: three consecutive
clean builds of this tree were measured and produced three different set digests,
because `cobc` embeds build-varying material in the C it generates. The value
proves only that the modules on disk now are the ones the attestation describes —
which is precisely what the consumer needs, since it is about to execute them.

---

## 9. Seeding a scenario

Seeding is stage 1 of the protocol. It loads the COBOL flat files into `ACASDB`
through the maintainer's own frozen `common/*LD.cbl` loader programs, so that
both cycles start from identical state.

```bash
N=clean_batch_gl
S="/repo/harness/scenarios/$N.yaml"
$C /repo/harness/seed.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/seed.sh --help
```

`--seed-dir` exists because a scenario's own `seed_dir` resolves relative to the
scenario file, which lives inside the **read-only** checkout, so a built fixture
cannot live there. It says *where*, never *which*: the scenario's `seed_files`
list stays the sole authority on what must be present, and every declared name is
verified for presence and readability before a load program runs.

`harness/run_parity.sh` and `harness/reset_db.sh` **default** it to the canonical
fixture root — `$ACAS_FIXTURES`, or `$ACAS_DATA/fixtures` when that is unset, plus
the scenario name, which is exactly where `harness/build_fixtures.sh` writes — so
the option is only needed for a fixture built somewhere else. `harness/seed.sh`
itself takes no default, because it can be driven against an ambient data
directory with no scenario at all.

The **seeding window's autocommit mode** is likewise defaulted rather than
demanded: unset means the mode measured to be the only one in which the frozen
loaders leave a durable row. `ACAS_SEED_AUTOCOMMIT=off` selects the literal
reading of Agent Action Plan §0.5.2 and reproduces the frozen no-COMMIT defect,
under which seven loaders report success, the tables read empty and the
durability gate exits **76**. Both modes were measured; the arbitration is `Q-10`
in [`docs/migration/ambiguity-resolutions.md`](docs/migration/ambiguity-resolutions.md).

### 9.1 Why `common/masterLD.sh` is reproduced rather than invoked

The maintainer ships a driver script for exactly this job. The harness
reproduces its documented per-file contract instead of calling it, for three
reasons — the second decisive:

1. **Its author marks it untested.** `[common/masterLD.sh:L4-L5]` reads
   `THIS SCRIPT HAS NOT YET BEEN TESTED` under a row of carets, and the
   `Changelog` entry dated 2025-03-07 independently confirms it: "Revised
   scripts masterUNL.sh, masterRES.sh & masterLD and so far only tested
   masterUNL."
2. **It cannot execute at all.** All 24 loader lines
   `[common/masterLD.sh:L93-L116]` are written
   `if [ -e analysis.dat ];  then analLD fi`, omitting the mandatory `;` or
   newline before `fi`. `bash -n common/masterLD.sh` rejects the file outright:

   ```text
   common/masterLD.sh: line 124: syntax error: unexpected end of file
   ```

3. **It ends interactively**, with `less SYS-DISPLAY.log`, which a scripted
   stage cannot use.

The file is **frozen and is NOT fixed** — not repaired, not `sed`-ed, not copied
and patched, not sourced (R-3, R-4). Only its contract is reproduced, in valid
shell.

### 9.2 The contract that is reproduced

**First the system block, in fixed order, guarded by the existence of
`system.dat`** `[common/masterLD.sh:L50-L88]`:

```text
systemLD → sys4LD → finalLD → dfltLD
```

The order matters because a later loader reads what an earlier one wrote. The
frozen script aborts on `> 63` after the first three loaders and applies its own
**tighter** `!= 0` test after `dfltLD` `[common/masterLD.sh:L83]`; both
behaviours are reproduced as written rather than harmonised.

**Then each flat file is mapped to its loader.** The in-scope subset:

| Flat file | Loader |
| --- | --- |
| `system.dat` | `systemLD`, then `sys4LD`, `finalLD`, `dfltLD` |
| `batch.dat` | `glbatchLD` |
| `posting.dat` | `glpostingLD` |
| `ledger.dat` | `nominalLD` |
| `salesled.dat` | `salesLD` |
| `purchled.dat` | `purchLD` |
| `postings2irs.dat` | `slpostingLD` |
| `irsacnts.dat` | `irsnominalLD` |
| `irsdflt.dat` | `irsdfltLD` |
| `irsfinal.dat` | `irsfinalLD` |
| `irspost.dat` | `irspostingLD` |
| `analysis.dat` | `analLD` |
| `value.dat` | `valueLD` |
| `invoice.dat` | `slinvoiceLD` |
| `pinvoice.dat` | `plinvoiceLD` |
| `openitm3.dat` | `otm3LD` |
| `openitm5.dat` | `otm5LD` |

The frozen script's remaining mappings — `delfolio.dat`, `delinvno.dat`,
`delivery.dat`, `pay.dat`, `plautogen.dat`, `slautogen.dat`, `staudit.dat`,
`stockctl.dat` — load the eleven out-of-scope tables listed in §4 and are not
part of a posting-cycle seed.

### 9.3 Exit-code semantics the harness must check

The loaders signal failure through exit codes with documented meanings
`[common/masterLD.sh:L37-L39]`:

| Code | Meaning |
| --- | --- |
| `128` | RDBMS parameters are not set up in the ACAS system parameter file |
| `64` | the "use RDB" flag is not set |
| `16` | error writing data to the RDBMS |

**Anything above 63 aborts the load** — the frozen script's own note says as
much, and admits it never got round to trapping them consistently
`[common/masterLD.sh:L41]`. `harness/seed.sh` checks them explicitly instead of
assuming success.

It also adds one non-vacuity gate of its own, which is not a behaviour change
but a refusal to hand on an empty capture: **a seed that reports success and
leaves no rows is a failed seed.** The frozen loaders reach no `COMMIT`, so under
autocommit **off** their writes are not durable at all — a defect of the frozen
code, reported rather than repaired (R-4), and the reason the seeding window
defaults to autocommit **on** (see §9.4). The harness measures the seeded row
counts when the window closes and fails there, rather than letting an empty
capture reach a comparison whose pass condition is an empty diff.

### 9.4 Two operational constraints

- **The seeding window runs with autocommit ON, and that needs no flag.** This is
  the one place the harness knowingly departs from the letter of the Agent Action
  Plan, so it is stated plainly. The AAP requires autocommit **off** during
  seeding (§0.2.1.1, §0.5.2, §0.4.1.7) on the strength of
  `[common/glbatchLD.cbl:L9-L13]` — but that citation is a four-line **operator
  banner, not code**, and no COBOL program in the checkout can change the setting:
  the vendored `cobmysqlapi38.c` exposes `MySQL_commit` and `MySQL_rollback` and
  **not** `MySQL_autocommit`. The maintainer then superseded his own banner inside
  the same frozen files — `[common/glbatchLD.cbl:L386-L387]` "…otherwise as
  normally it is set to autocommit !!!!!" and `[common/glbatchLD.cbl:L453]` "These
  do not work during testing with mariadb - Non transactional model or autocommit
  set ON" — and commented out **every** call site, leaving 77 dead references
  across the 28 loaders and not one live `perform`.

  So under autocommit off the loaders persist **nothing**, and a seed that cannot
  persist makes the AAP's own pass condition (§0.8.5, an empty diff over a real
  comparison) unreachable. Rule R-6 makes compiled behaviour the arbiter, so
  **`ACAS_SEED_AUTOCOMMIT` defaults to `on`** and `harness/docker-compose.yml`
  declares it explicitly. The divergence is written up in full at
  `docs/migration/ambiguity-resolutions.md`.

  `ACAS_SEED_AUTOCOMMIT=off` still selects the **AAP-literal** window, because a
  reader must be able to run exactly what the plan describes. It will seed nothing
  and `harness/seed.sh` will exit **76** saying so — measured, not predicted.
  Nothing in the harness issues the `COMMIT` the frozen loaders omit (R-4).

  Either way the mode is a **window**: `harness/seed.sh` sets it, runs the
  loaders, then restores whatever the server had, however the run ends. Runtime
  application access — both cycles, and the reset — runs with autocommit **ON**,
  the mode `harness/Dockerfile.mariadb` declares; the reset and the COBOL runner
  each assert it, which is how a still-open seeding window is caught rather than
  silently changing what a run means.
- **The loaders must run from the ACAS data directory** holding the COBOL flat
  files `[common/masterLD.sh:L27-L28]`. The frozen script hard-codes
  `cd ~/ACAS` `[common/masterLD.sh:L45]`; the harness takes the directory as
  `--data-dir` instead, and records that as an explicit, documented deviation.

### 9.5 Resetting between the two runs

```bash
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/reset_db.sh --help
```

`harness/reset_db.sh` applies `mysql/ACASDB.sql` **verbatim** and emits **zero
DDL of its own** (R-3) — it does not need any, because the frozen dump already
carries a `DROP TABLE IF EXISTS` before each of its 33 `CREATE TABLE`
statements, so re-applying the frozen file *is* the drop-and-recreate. The file
is streamed unfiltered: no `sed`, no `awk`, no `iconv`, no local copy and no
`--default-character-set` override, so the dump's own charset caveat
`[mysql/ACASDB.sql:L9-L11]` is preserved rather than "fixed" (R-4).

For the same reason it is worth knowing what the frozen dump does to the session
it is replayed into, since `harness/Dockerfile.mariadb` applies it as-is:
`SET NAMES utf8mb4` `[mysql/ACASDB.sql:L16]`, `TIME_ZONE='+00:00'`
`[mysql/ACASDB.sql:L18]`, `UNIQUE_CHECKS=0` `[mysql/ACASDB.sql:L19]`,
`FOREIGN_KEY_CHECKS=0` `[mysql/ACASDB.sql:L20]` and
`SQL_MODE='NO_AUTO_VALUE_ON_ZERO'` `[mysql/ACASDB.sql:L21]`, with every table
defaulting to `utf8mb3` / `utf8mb3_general_ci`. It never drops the database
itself: `DROP DATABASE` and `CREATE DATABASE` appear nowhere in the frozen file
and dropping it would destroy the grants Compose established.

The reset is destructive, so it refuses to run until **three gates** are
satisfied. All three are asserted before the first connection is opened and
re-asserted immediately before the apply, and each either lets the run proceed
exactly as it would have or aborts it — no gate rewrites a statement, alters the
applied file or changes the seed, which is why they cost nothing under R-3/R-4:

| Gate | What it requires | How you satisfy it |
| --- | --- | --- |
| 1 | a **distinct administrative account**, not the application user | set **`ACAS_DB_ADMIN_USER`** (and its password) to something that differs from `ACAS_DB_USER`. There is deliberately **no fallback** to the application account, so that the application account can be granted only what the Python cycle needs |
| 2 | an **explicit, target-scoped consent token** | set **`ACAS_RESET_CONSENT`**, or pass **`--consent=`**, to exactly `DESTROY <schema>@<host>:<port>` for the target actually resolved. Comparison is exact and case-sensitive. A boolean `--yes` would not do: one inherited from a shell history is worth nothing, whereas a token naming the schema, host and port cannot be aimed at the wrong database by accident |
| 3 | a **disposable target** | the schema must be in the allow-list and the host a disposable host. Both lists are extendable by environment, because a deployment may legitimately name its throwaway database something else — but extending them is an explicit, reviewable act |

`--dry-run` **reports** the gates instead of enforcing them, and is the way to be
told the exact consent token a given target needs rather than guessing at it. Do
not weaken any of the three.

---

## 10. Running both cycles

Two runners, one per side of the comparison, driven with identical logical
inputs:

```bash
$C /repo/harness/run_cobol_scenario.sh  "$S"    # stage 2: the compiled cycle
$C /repo/harness/run_python_scenario.sh "$S"    # stage 6: the migrated cycle
```

Neither runner judges the accounting. Each drives, asserts its own
preconditions, observes and records; whether the two cycles agree is decided in
§11 from the two dumps.

**Neither runner takes the state capture either, and that is a property of the
protocol rather than an omission.** Capture ownership is single and it belongs to
stages 3 and 7, which run *after* the runner has exited — the only moment at which
the run status the capture's attestation carries is final. Each runner prints the
exact capture command instead, so a hand-driven run copies one line.

**`run_cobol_scenario.sh` drives ONE operation per invocation**, because the
compiled menus are one executable each and a second operation may live behind a
different menu. A scenario that declares more than one is therefore *refused*
unless `--operation` names which to run, rather than silently running the first —
that silence used to compare a compiled state produced with less work than the
migrated side did. `harness/run_parity.sh` supplies the operation, once per
declared operation, in the declared order, and pre-validates before stage 1 that
**both** runners can drive every one of them.

`harness/run_cobol_scenario.sh` drives the **menu executables** rather than the
posting programs, and that is deliberate. None of the twelve in-scope programs
is a main program: each is a `CALL`ed sub-program whose `PROCEDURE DIVISION
USING` list is made of group items, `cobcrun` can pass only string arguments,
and the posting programs are compiled `-m` as loadable modules rather than `-x`
executables — so no shell can invoke them directly. The four menu executables
are what construct those parameter blocks and `CALL` the sub-programs. Writing a
new COBOL driver was rejected outright: the COBOL tree is frozen (R-1, R-4).

### 10.1 The three linkage shapes — there are three, not one

The CLI entry points bind the actual linkage parameters, and the frozen source
has exactly three distinct shapes:

| Family | `PROCEDURE DIVISION USING` | Evidence |
| --- | --- | --- |
| General Ledger | `ws-calling-data`, `system-record`, `to-day`, `file-defs` | `[general/gl070.cbl:L245-L248]` |
| Sales and Purchase | the same four, plus the fourth system record `system-record-4` | `[sales/sl060.cbl:L395-L399]` |
| IRS | `IRS-System-Params`, `WS-System-Record`, `File-Defs` | `[irs/irs030.cbl:L552-L554]` |

The IRS shape is **materially different**: it takes **neither the calling-data
block nor the run date `to-day`**. Collapsing the three into one argument shape
would misrepresent the interface the migration is supposed to preserve.

### 10.2 The seven routes

`python -m acas_posting` is the router. It mirrors the system-selection menu of
`common/ACAS.cbl` with no screen output of any kind, and reads no clock.

```bash
python -m acas_posting general  post-cycle     --help
python -m acas_posting general  end-of-cycle   --help
python -m acas_posting sales    invoice-post   --help
python -m acas_posting sales    cash-post      --help
python -m acas_posting purchase order-post     --help
python -m acas_posting purchase payment-post   --help
python -m acas_posting irs      post           --help
```

Each route is also directly runnable as
`python -m acas_posting.cli.<module>`, and the two forms return the same status.
What each dispatches:

| Route module | Dispatches | Derived from |
| --- | --- | --- |
| `cli/gl_post_cycle.py` | `gl070`, the term-code-5 abort gate, `gl071`, `gl072` | `[general/general.cbl:L805-L815]` |
| `cli/gl_end_of_cycle.py` | `gl080` | `[general/general.cbl:L817-L821]` |
| `cli/sl_invoice_post.py` | `sl055`, then `sl060` | `[sales/sales.cbl:L756-L768]` |
| `cli/sl_cash_post.py` | `sl100` | `[sales/sales.cbl:L792-L796]` |
| `cli/pl_order_post.py` | `pl055`, then `pl060` | `[purchase/purchase.cbl:L752-L762]` |
| `cli/pl_payment_post.py` | `pl100` | `[purchase/purchase.cbl:L786-L790]` |
| `cli/irs_post.py` | `irs030`, plus the clear-transfer-file decision as a parameter | `[irs/irs.cbl:L666-L672]` |

#### The options each route requires, and why three of them have no default

⚠️ **Three routes will not run without an answer you have to supply, and one runs
destructively without one.** That asymmetry is not an oversight — it follows from
what the frozen prompt does. A prompt with **no defaultable answer** becomes a
required option, because inventing a default would be inventing the one answer
that silently enables every database write on the route. A prompt whose frozen
default *is* to proceed keeps that default, because changing it would be a
behaviour change (R-4).

| Route | Required options | Prompt-derived options and their defaults |
| --- | --- | --- |
| `general post-cycle` | `--run-date` | — |
| `general end-of-cycle` | `--run-date` | ⚠️ `--run-confirmed` / `--no-run-confirmed`, **defaulting to `--run-confirmed`**, and `--disk-change-option`, choices `{0, 9}`, **defaulting to `0`**. Both defaults **proceed**, so a bare command line writes. `[general/gl080.cbl:L295-L302]` moves `space` into the reply before the accept and aborts only on Esc or `A`/`a`; `[general/gl080.cbl:L545-L549]` exits on `9` and re-prompts on anything other than `0` |
| `sales invoice-post` | `--run-date` | — |
| `sales cash-post` | `--run-date`, **`--ok-to-post` / `--no-ok-to-post`** | none — the switch has **no default at all**, so the command exits `2` without it. The frozen prompt is `[sales/sl100.cbl:L311-L319]`: it accepts at `L314`, exits on `"NO"` at `L316-L317` and **re-prompts on anything that is not `"YES"`** at `L318-L319`, so a blank answer neither proceeds nor declines. It sits before the first `OTM3-Open` at `L321`, so declining reaches no file at all |
| `purchase order-post` | `--run-date` | — |
| `purchase payment-post` | `--run-date`, **`--ok-to-post` / `--no-ok-to-post`** | as above, from `[purchase/pl100.cbl:L303-L311]`: accept at `L306`, exit on `"NO"` at `L308-L309`, re-prompt on anything not `"YES"` at `L310-L311`, and the first `Purch-Open` only at `L313` |
| `irs post` | `--run-date`, **`--clear-posting-file` / `--no-clear-posting-file`** | none. `--clear-posting-file` **truncates the transfer table**: `[irs/irs030.cbl:L1720-L1724]` opens it for output, which the handler implements as *delete every row*. The accept at `[irs/irs030.cbl:L1717]` carries no `WITH UPDATE`, so the `[Y]` in the prompt is display text and a bare Enter re-prompts — which is exactly why there is no default here either |

A worked pair, safe form first:

```bash
# Declines the post. Returns before the first OTM3-Open, so it reaches no file
# and no write - the form to reach for when checking a scenario is wired up.
python -m acas_posting sales cash-post --run-date 21/09/2025 --no-ok-to-post

# WRITES. Posts the cash batch and updates the period totals.
python -m acas_posting sales cash-post --run-date 21/09/2025 --ok-to-post
```

The process exit status **is** `WS-Term-Code` itself
`[copybooks/wscall.cob:L10]`, surfaced unchanged and never re-encoded: `0` when
the operation completed, `5` when the General Ledger abort gate stopped the
cycle, above `7` when the operation reported a serious error, and `2` when the
router refused the selection.

The three ledgers have **three different gates, deliberately not harmonised**:
General tests `ws-term-code = 5` `[general/general.cbl:L810]`, Sales tests
`not = zero` `[sales/sales.cbl:L761]`, and Purchase has no gate at all — its
equivalent lines are commented out in the frozen source
`[purchase/purchase.cbl:L755-L758]`. Each gate belongs to its own route; the
router imposes none (R-4).

### 10.3 The abort gate is a hard gate, not a warning

This one changes which tables a run writes, so getting it wrong produces a
silently different result rather than an error.

A batch left open sets a status condition. `gl070` detects it and raises the
terminate code — `move 5 to ws-term-code` `[general/gl070.cbl:L289]` — and the
menu then tests that code and returns to the menu rather than continuing:
`if ws-term-code = 5 / go to display-menu` `[general/general.cbl:L810-L811]`.
The effect is that **`gl071` and `gl072` never run at all**, and the database
effect of the rejection is therefore *the absence* of everything those two
phases would have written.

`acas_posting/cli/gl_post_cycle.py` reproduces this as a hard phase boundary.

### 10.4 The controlled clock

`acas_posting/clock.py` pins exactly **two** observables and injects them at the
CLI boundary:

- the text date `to-day pic x(10)`, in **DD/MM/CCYY** form;
- the binary `Run-Date` `[copybooks/wssystem.cob:L67]`.

Nothing deeper is needed, and over-engineering it would be a mistake. **Every one
of the twelve in-scope posting programs contains zero clock reads** and receives
both date observables purely through linkage — that is the fact the whole design
rests on, and it was counted rather than assumed: `function current-date` appears
in none of `gl051`, `gl070`, `gl071`, `gl072`, `gl080`, `sl055`, `sl060`,
`sl100`, `pl055`, `pl060`, `pl100` or `irs030`.

⚠️ **The reads live one level up, and there are five of them in the cycle's call
chain, not one.** An earlier revision of this section called the date-service
copybook *"the single clock read in the entire call chain"*, following the Agent
Action Plan's own phrasing at §0.1.1. That is imprecise and a reader can
disprove it with one `grep`, so the census is given in full:

| Where | Locator | Role |
| --- | --- | --- |
| the shared date service | `[copybooks/Proc-ACAS-Mapser-RDB.cob:L72]` — `move function current-date to wse-date-block` | builds the text date, then calls the date module to derive the binary one `[copybooks/Proc-ACAS-Mapser-RDB.cob:L79-L80]` |
| the General menu | `[general/general.cbl:L371]` | reads the clock itself before dispatching |
| the Sales menu | `[sales/sales.cbl:L323]` | as above |
| the Purchase menu | `[purchase/purchase.cbl:L318]` | as above |
| the IRS menu | `[irs/irs.cbl:L480]` | as above |
| the system selector | `[common/ACAS.cbl:L353]` | reached before any menu, and out of scope itself |

Further reads exist in programs the posting cycle never reaches — the sysout and
logging helpers, two take-on utilities, the two `makesqltable` programs and the
Stock menu — and they are named in
[`docs/migration/anomaly-log.md`](docs/migration/anomaly-log.md) under **A-16**
rather than repeated here.

**None of that changes the conclusion, which is why the correction is worth
making rather than glossing.** Every one of those reads happens *above* the
migrated surface and reaches a migrated program only as the two linkage values.
Pinning those two values at the CLI boundary is therefore still sufficient to
make two runs byte-identical — the design is sound for a slightly different and
checkable reason than the one first given.

The module exposes `PinnedRunDate` with three constructors —
`pin_from_calendar_date`, `pin_from_to_day` and `pin_from_run_date` — plus
`verify_pin`, so a pin can be built from whichever observable a scenario
declares and then cross-checked. **There is no default that resolves to the
current time**: every route requires its run date as an argument.

### 10.5 Pin the IRS fan-out switch in every scenario

`IRS-Instead` is a single character in the system record, with condition names
for "IRS instead" and "IRS as well as" — `88 IRS-Used value "Y"` and
`88 IRS-Both-Used value "B"` `[copybooks/wssystem.cob:L179-L181]`. It is a
three-state switch, it is tested at three sites in each of the four Sales and
Purchase posting programs, and **its state changes which tables a run touches**.

Every scenario therefore pins it explicitly. Leaving it at a default would make
the affected-table list ambiguous, and an ambiguous affected-table list makes
the diff in §11 unattributable.

A consequence worth stating once: Sales and Purchase batches balance by
construction, so the **control-total mismatch scenario is
General-Ledger-specific**. There is no meaningful way to construct an unbalanced
sales batch.

---

## 11. Diffing state — the verification protocol

### 11.1 The stage order is the evidence

The protocol is a rigid sequence, not an ad-hoc comparison. **`harness/parity_stages.sh`
is the single definition of the ten stages and their labels**, and the driver
prints it on demand rather than restating it:

```bash
$C /repo/harness/run_parity.sh --print-stages
```

⚠️ **That is the shape; the count is ten.** The line above names the eight
*logical* steps and reads as nine because the reset appears once. The driver
numbers **ten**, because it counts the reset on both sides and makes the
publication check its own gate. Anywhere in this project's older prose that says
"eight-stage" or "the stage-8 diff", read **today's stage 10** — the diff. The
authority is `[harness/parity_stages.sh ACAS_PARITY_STAGES]`, which the driver
reads through `[harness/run_parity.sh ACAS_PARITY_STAGE_REGISTRY]` and prints under
`--help` in `[harness/run_parity.sh acas_parity_usage]`. And
**runner-local `Check n/8` labels are a different numbering entirely**:
`run_cobol_scenario.sh` and `run_python_scenario.sh` each print their own
preflight steps, which count that one script's internal checks. A runner's
`Check 8/8` is not the parity diff.

**An empty diff is the pass condition, and the only one.** A stage that exits
non-zero has produced no evidence, so re-seed rather than carry a partial
capture forward.

The recommended form is the fail-closed driver, because the ordering *is* the
evidence: it runs the stages in sequence and aborts at the first non-zero,
passing that stage's own exit status through verbatim rather than flattening
every failure into one code.

```bash
N=clean_batch_gl
S="/repo/harness/scenarios/$N.yaml"
$C /repo/harness/run_parity.sh "$S"                  # the fixture root is defaulted
$C /repo/harness/run_parity.sh --seed-dir "/data/fixtures/$N" "$S"   # or state it
$C /repo/harness/run_parity.sh --dry-run "$S"       # print the ten commands, run none
$C /repo/harness/run_parity.sh --print-stages       # the canonical registry, as TSV
$C /repo/harness/run_parity.sh --from 2 --to 2 "$S" # re-run one stage after a fix
$C /repo/harness/run_parity.sh --help
```

`--from`/`--to` name a range by stage NUMBER, which is why the numbering is part
of the contract rather than presentation. A resumed run refuses to mix attempts:
it rejects artifacts written under a different run id, so a stage cannot render a
verdict on a capture from an earlier attempt.

The driver's ten stages, which are the sequence above with the reset counted on
both sides and the publication check promoted to a gate of its own:

| Stage | Command | Job |
| --- | --- | --- |
| 1 | `harness/reset_db.sh` | schema, then seed the scenario |
| 2 | `harness/run_cobol_scenario.sh` | run the compiled COBOL cycle |
| 3 | `harness/dump_tables.py --side cobol` | capture the COBOL state |
| 4 | `harness/normalize.py --side cobol` | normalise that capture |
| 5 | `harness/reset_db.sh` | schema, then **re-seed the same scenario** |
| 6 | `harness/run_python_scenario.sh` | run the migrated Python cycle |
| 7 | `harness/dump_tables.py --side python` | capture the Python state |
| 8 | `harness/normalize.py --side python` | normalise that capture |
| 9 | — | assert both normalised trees are present and published |
| 10 | `harness/diff_states.py` | **an empty diff is the pass** |

Stages 1 and 5 are the same command on purpose: the second reset is what makes
the Python side's *starting* state the COBOL side's starting state rather than
the COBOL side's *ending* state.

Driving the stages by hand is still supported. ⚠️ **Note one difference from
the driver**: stage 1 below is spelled `reset_db.sh`, exactly as stage 5 is,
because that is what `run_parity.sh` runs. Substituting `seed.sh` seeds
*whatever the previous run left in the schema* — which usually still produces an
empty diff, and is the reason the mistake survives: the two sides agree on a
state neither of them established.

```bash
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_cobol_scenario.sh "$S"
$C python3 /repo/harness/dump_tables.py --scenario "$N" --side cobol --scenario-file "$S"
$C python3 /repo/harness/normalize.py   --scenario "$N" --side cobol
$C /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
$C /repo/harness/run_python_scenario.sh "$S"
$C python3 /repo/harness/dump_tables.py --scenario "$N" --side python --scenario-file "$S"
$C python3 /repo/harness/normalize.py   --scenario "$N" --side python
$C python3 /repo/harness/diff_states.py --scenario "$N" --scenario-file "$S"
```

`harness/diff_states.py` exits `0` with empty stdout for an empty diff, `1` for
a real behavioural difference, and `2` when the comparison could not be
performed at all. It also **refuses** a capture whose run stage did not attest
success, and refuses a pair that is empty on both sides — so a hand-driven run
fails closed instead of reporting that two empty captures were identical.

### 11.1a What the driver refuses before stage 1

Stages 1 and 5 **drop and re-apply the schema**. The driver is therefore stricter
about its target than the individual scripts are, and deliberately so: the scripts
are general administrative tools that document escape hatches for use outside
evidence production, whereas the driver produces the evidence and must not be
steerable by ambient configuration.

Before any stage runs, `harness/run_parity.sh` requires all of the following, and
each failure is refused up front rather than discovered mid-protocol:

| Requirement | Refused otherwise |
|---|---|
| `ACAS_DB_NAME` is exactly `ACASDB` | A different or differently-cased schema, or an unset one |
| `ACAS_DB_HOST` is one of `mariadb`, `127.0.0.1`, `localhost`, `::1` | Any other host, including one that merely resolves locally |
| `ACAS_DB_PORT` fits the frozen four-character carrier, `1..9999` | `0`, `99999`, or non-numeric text — the carrier is `pic x(4)` at `[common/acas-get-params.cbl:L158]` and `[copybooks/mysql-variables.cpy:L91]` |
| `ACAS_RESET_CONSENT`, if set, names *this* target | A token naming another database or host, or one missing the `DESTROY` prefix — so a token left in an environment cannot later authorise a different server |
| The server-side disposability sentinel is present | Absent — `harness/reset_db.sh` proves disposability against the server, not merely against the host name |
| **None** of `ACAS_DB_ALLOWED_SCHEMAS`, `ACAS_DB_DISPOSABLE_HOSTS`, `ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE`, `ACAS_RESET_ACKNOWLEDGE` is set | Any of them set, *even to a harmless value* |
| A full-build provenance attestation exists and is untainted (§8.9) | Absent, unreadable, override-tainted, or describing modules other than those on disk — checked only when stage 2 is in range |

The last bypass row is the sharpest of them, and the reason it is refused rather
than merely warned about: `ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE` suppresses **both**
the static disposable-target check and the server-side sentinel proof, so with it
set the evidence path would accept any reachable database.

These are refusals, not defaults to be overridden. There is no flag to disable
them, because a flag to disable them would be the hole they close.

`harness/docker-compose.yml` already supplies exactly the canonical values, so a
Compose run needs none of this configured by hand — which is the point. If the
driver refuses, the target is not the canonical one.

### 11.1b What a run RETAINS, and where

A verdict that lives only in a terminal is not evidence. Every run publishes the
following, atomically and mode `600`, under `$ACAS_OUT` — which the Compose file
sets to `/out`, backed by a named volume, so the artifacts outlive the container:

| Artifact | Carries |
| --- | --- |
| `<scenario>/verdict.json` | the machine-readable verdict, written on **both** outcomes: the scenario, the outcome, the exit code, the tables compared and differing, the run id, the seed marker digest, and the digests of the scenario file, the frozen schema, both run manifests and the diff report |
| `<scenario>/parity-result` | the driver's own claim for the run — the scenario, the run id, the claim, the stage range requested, the first failing stage's status, the behavioural status and the verdict state |
| `<scenario>/{cobol,python}.norm/_manifest.json` | each capture's provenance: run id, scenario-file digest, frozen-schema digest, the exact command, the producing tool's digest, the prior stage's manifest digest, and the run attestation it was taken under |
| `run-logs/<scenario>/<side>.run-status` | wrapper health, distinct from disposition, plus a per-operation status row for each declared operation |
| `run-logs/<scenario>/<side>.operation-status` | each operation's OWN observed disposition, in declared order |
| `run-logs/<scenario>/<side>.seed-fingerprint` | one row count per affected table, in the scenario's declared order, taken immediately before the drive |
| `run-logs/<scenario>/seed-identity` | the staged fixture marker digest both reset stages are required to agree on |
| `run-logs/<scenario>/cobol.log`, `cobol.plan` | the pty transcript and the resolved keystroke plan |

None of them lives inside a compared tree, so none can perturb a diff. The
committed record of which run produced which verdict is
[`docs/migration/scenario-diff-evidence.md`](docs/migration/scenario-diff-evidence.md),
and it cites these artifacts by digest.

**`verdict.json` is written on a difference too, not only on a pass.** That is
deliberate: an outcome that only records success cannot be used to demonstrate
that a difference was found and acted on.

### 11.2 Why the dump is trivially deterministic

The frozen schema turns out to be exceptionally well behaved for this purpose.
All **22 in-scope tables have a single-column primary key and zero secondary
indexes**, and none carries a `TIMESTAMP` column, an `AUTO_INCREMENT` column or
a column-level `DEFAULT`. The one `AUTO_INCREMENT` in the whole schema belongs
to `STOCKAUDIT-REC`, which is out of scope.

So the dump is exactly this, per table, and nothing more:

```sql
SELECT * FROM `<table>` ORDER BY `<primary-key>`;
```

No tie-breaking logic, no timestamp masking, no surrogate-key remapping.

THE COMPARISON IS BOUNDED BY ALL 22 IN-SCOPE TABLES. Pass `--all-in-scope` to
both `dump_tables.py` (stages 3 and 7) and `diff_states.py` (stage 10);
`harness/run_parity.sh` and `tests/conftest.py` already do. A scenario's
`affected_tables` is its **declared effect**, which the runners assert against —
it is *not* the bound, because a bound drawn from what a scenario expects to move
cannot show a difference in anything it did not expect to move, and an empty diff
is the single pass condition.

In particular `overrewrite.` `[general/general.cbl:L656-L672]` rewrites
`SYSTEM-REC` under key 1, `SYSDEFLT-REC` under key 2 and `SYSTOT-REC` under key
4, and **both** cycles perform it — `acas_posting/cli/args.py::overrewrite`
reproduces that RDB arm on every General route (keys 1, 2, 4) and every Sales and
Purchase route (keys 1, 4), while `irs_post` persists key 1 through the IRS
menu's own `EOJ.` shape — so those rows are comparable rather than a source of
false failure. A capture that omitted them could have reported an empty diff while
the run date, the allocators, the flags, the defaults or the period totals
differed.

`SYSTEM-REC` IS DUMPED WITH EXACTLY TWO CELLS WITHHELD, and only two.
`RDBMS-PASSWD char(12)` `[copybooks/wssystem.cob:L139]` and the frozen schema's
shorter `PASS-WORD` are the database's own password as seeded, and a dump is
`SELECT *`, so `harness/dump_tables.py`'s `REDACTED_COLUMNS` replaces those two
cells — on **both** sides — with one fixed marker. The row is still dumped and
still diffed, every other column byte for byte, so this is redaction and not an
ignore-list; withholding a secret symmetrically cannot conceal a difference in
anything the cycle computes. The row is **fingerprinted** as well, before and
after every run on both sides, and the two post-run digests are compared over all
169 columns including those two — see §11.5.

`--scenario-file` (narrow to the declared effect), `--tables` (one table by hand)
and `diff_states.py --all-tables` (the union of the two captures) are **debugging
aids, not the protocol**.

### 11.3 What the normaliser does, and what it must not do

`harness/normalize.py` has exactly three jobs, and each answers a specific
finding rather than being a general-purpose cleanup:

1. **Canonicalise trailing spaces in fixed-character columns.** This exists
   because of a genuine width drift: the nominal ledger name is 24 characters in
   the copybook, becomes a 32-character host variable
   `[common/nominalMT.cbl:L299]` and lands in a 32-character column
   `[mysql/ACASDB.sql:L127]`. The value is not corrupted, but the padding
   differs, and padding is visible in a dump.
2. **Canonicalise decimal scale rendering**, so a value stored at two decimal
   places compares equal regardless of how a driver chose to format it.
3. **Canonicalise the two-digit versus four-digit date text forms** that the
   schema stores side by side, against an explicit allow-list rather than a
   permissive pattern.

It does **not** make different stored values compare equal. That is the point of
keeping the list to three: because the normaliser cannot hide a difference, **a
non-empty diff is always a real behavioural difference and never an artefact of
the comparison.**

### 11.4 State fingerprints — the bound that is not a dump

Two questions the dump cannot answer: *did the two sides start from the same
seed?*, and *did this run change anything at all?* A dump answers neither, because
it is taken once and only after the run, and because two runs that both wrote
nothing produce identical dumps.

Both runners therefore write a **state fingerprint** twice — once immediately
before the dispatch and once immediately after — under
`$ACAS_OUT/run-logs/<scenario>/`, which is outside every compared tree so that no
fingerprint can itself be diffed as though it were posted data:

```text
run-logs/<scenario>/cobol.seed-fingerprint    run-logs/<scenario>/python.seed-fingerprint
run-logs/<scenario>/cobol.post-fingerprint    run-logs/<scenario>/python.post-fingerprint
```

Each is one line per table, three TAB-separated fields:

```text
<TABLE><TAB><row count><TAB><sha256 of the canonical primary-key-ordered dump>
```

**One producer, and only one.** `harness/table_digest.py` computes every digest
for both sides and both records. That matters more than it looks: two definitions
of "the digest" is exactly how a pre-run and a post-run record, or an oracle-side
and a Python-side record, silently stop being comparable while every individual
assertion still passes. A table that could not be read carries a hyphen in both
value fields — never a zero, because *could not be read* and *is empty* are
different facts, and a consumer must be able to refuse rather than treat the first
as the second.

**Why the digest and not the row count alone.** Two seeds carrying different
values at the same row counts agree on a count-only record. The digest is what
makes a byte comparison of two fingerprints a decisive statement about the seed.

**The fingerprint is the second of the two bounds on `SYSTEM-REC`.** The parameter
row is the one in-scope table that **both** cycles write on **every** route — see
§11.2's warning and ambiguity `Q-7` — so leaving it unobserved would be a real
coverage hole. It is therefore on **every** scenario's affected-table list and in
every capture, and the one problem a dump does have is solved where it arises
rather than by dropping the table: a dump is `SELECT *` and two of the record's 169
columns are credentials — `RDBMS-PASSWD char(12)`
`[copybooks/wssystem.cob:L139]` and `PASS-WORD` — so `harness/dump_tables.py`'s
`REDACTED_COLUMNS` withholds exactly those two cells inside `render_value`, keyed
by `(table, column)` and applied identically on both sides, which means the
redaction can neither leak a secret nor manufacture a difference. The other 167
columns are compared by value. Bounding the whole table out instead — the
alternative that was considered and rejected — would have taken those 167 with it,
and a bound drawn that way cannot reveal a difference in what it excludes.

The second-order worry was **measured** rather than assumed: the row's content
depends on what the route DID — the run-date stamp, the IRS allocator, the one-shot
latches, and `Date-Form`, which the frozen date sections write back
`[copybooks/wssystem.cob:L127]` — so declaring it could in principle tie a
scenario's effect claim to fields the scenario does not reason about. It does not:
**the digest holds on all four scenarios that declare `unchanged` and moves on every one
that declares `changed`.** That was measured over the eight scenarios that existed when
the measurement was taken — which is all four `unchanged` ones — and the ninth,
`end_of_cycle_gl`, declares `changed` and moves the row by construction, Phase 5
advancing the cycle and rotating the quarter counter. The fingerprint is kept
on top of the dump because it adds what the dump cannot — a SHA-256 over all 169
columns, the two withheld cells included, and a SHA-256 is not a disclosure.
`tests/conftest.py`'s `assert_system_record_parity` compares the two sides' post-run
digests, and each of the nine scenario tests calls it.

**What reads the pair.** `tests/conftest.py`'s `assert_seed_fingerprints_agree`
cross-checks the two sides' pre-run records; its `assert_tables_unchanged_by_run`
reads a side's pre-run record against its own post-run record; and the determinism
tier's LAYER 2b uses the same pair to establish that a run did what its scenario
declares, which is the one thing a two-run comparison cannot show on its own.

---

## 12. Tests

Three tiers, three markers, two very different infrastructure requirements. The
markers are registered in `pyproject.toml` under `[tool.pytest.ini_options]` and
`--strict-markers` is on, so a typo in a marker is an error rather than a silent
no-op.

| Tier | Files | Marker | Needs |
| --- | --- | --- | --- |
| `tests/arithmetic/` | 19 | `arithmetic` | nothing — no Docker, no MariaDB, no GnuCOBOL |
| `tests/scenarios/` | 8 | `scenario` | the Compose stack and a seeded database |
| `tests/determinism/` | 1 | `determinism` | the Compose stack |

Two further markers, `database` and `oracle`, record the finer-grained
requirement — a live MariaDB with the frozen schema applied, and a built
oracle — for tests that need one but not the other.

### 12.1 The arithmetic tier — runs anywhere

```bash
python -m pytest -m arithmetic
```

One test file per computation pattern: the field descriptors and the six storage
classes, `COMP-3` packed decimal, `COMP` binary, `SIGN LEADING` display,
`MOVE` truncation, un-`ROUNDED` truncation, `ROUNDED` half-up, the two VAT
formulations, the `gl080` cycle divide, the double-entry explosion, the
control-total comparison, the ledger-balance accumulation, and the derived IRS
date components — fourteen files. Two more are **structural** rather than
arithmetic and live in this tier for its defining property, which is not its
subject but its dependencies: it needs no database, no COBOL and no Docker, so it
runs anywhere. They are `test_shared_storage_and_dispatch_boundaries.py`, which
locks the storage and dispatch boundaries between the layers, and
`test_deployment_contract_boundaries.py`, which locks the transport-environment
contract, the driver deadlines, the IRS bind boundary and the cross-file reference
integrity of the documents and scenario definitions.

Four further files in this tier are not computation patterns but **shipped-module
drivers**, and they exist because a pattern test can pass against a correct local
transcription while the module that ships is wrong:

| File | What it drives, in-process |
| --- | --- |
| `test_gl080_shipped_end_of_cycle.py` | `gl080_end_of_cycle.py` — the `ROUNDED` cycle-to-period divide, the unbounded quarter subscript, the second rotating quarter counter, and the archive and deletion phases. **No scenario declares the `gl_end_of_cycle` operation**, so this is the only place the module is executed at all |
| `test_gl072_shipped_silent_skips.py` | `gl072_transaction_update.py` — both silent skips, each proven *reached* rather than inferred from end state |
| `test_shared_storage_and_dispatch_boundaries.py` | the shared storage emulation, the dispatch boundaries, and `acas008`'s four unconditionally refused verbs — all four through the entity-named vocabulary, and the rewrite additionally through the handler-named one, which is the only one of the four `Proc-ZZ100-ACAS-IRS-Calls.cob` declares. The other three handler-named aliases are asserted **absent**, since publishing them would make the facade this migration's invention rather than the copybook's |
| `test_cli_seams_and_failure_paths.py` | the `acas_posting/cli/` seams — the key-1 status-before-close path, the IRS handler-named verb selection and its `FacadeGoback` boundary, the `gl071` serious-error short-circuit, and the RDBMS-parameter absent and unusable statuses |

The methodological rule that governs the whole tier: **expected values are
captured from the compiled oracle**, never derived by reading the COBOL and
reasoning about what it should produce. A language change alters evaluation
semantics in ways code review does not reliably catch, which is precisely why
the oracle exists.

Many of these tests reach into one shipped paragraph of `acas_posting.programs`
or one pure function of `acas_posting.dal`, so that the anomalies R-4 requires be
**locked** — A-7, A-8, A-9, A-10, the `gl051` control-total gate and the `gl071`
sort order among them — are asserted against the code that ships rather than
against a re-transcription of it. Those imports happen inside the test body,
through a context manager that imports the module for real and then removes it
from `sys.modules` again — deliberately **not** behind `pytest.importorskip`,
because a soft import turns a broken shipped module into a SKIP, and a skipped
anomaly lock is indistinguishable from an absent one.

The tier still needs no database driver, and that is enforced rather than assumed.
Each loader **evicts** every tier-isolated name before it imports, purges every
name the import added on the way out, and then asserts that no tier-isolated name
survived — the isolated set being `acas_posting.cli`, `acas_posting.dal`,
`acas_posting.programs`, `harness`, `mysql`, `numpy`, `pandas`, `sqlalchemy` and
`yaml`. Nothing is memoised, and the eviction before the import is what makes the
residue check mean something: a cached entry is already resident, so the purge
would remove nothing and a "leaves no driver loaded" assertion would pass while
re-using an object that had never left — precisely the vacuity QA found. Eviction
rather than an assertion that the name is *absent* on the way in, because this
tier's own helpers legitimately import program modules in function scope to drive
the shipped paragraphs, and an absence check would make the claim depend on which
file happened to run first.

**They are mandatory and are never skipped.** An earlier revision guarded them
with `pytest.importorskip`, which let a host lacking the pinned driver report a
*passing* arithmetic tier while those anomaly locks silently vanished — the worst
possible failure mode for a suite whose job is to stop a defect being "fixed".
`mysql-connector-python` is a hard `[project.dependencies]` entry, so an installed
package always satisfies the import; if it ever does not, the tier **errors**
rather than skipping. There are now **zero** live `pytest.importorskip` calls in
the suite; the six textual occurrences that remain are comments recording this
history.

**There is no `xfail` anywhere in this tier, and there used to be eighteen.** Each
one asserted the *naive* reading of a question the oracle had not settled, so that a
change making the naive reading true would XPASS and turn the suite red. All
eighteen questions have since been measured against the compiled program, and every
one of those tests now asserts the MEASURED value as a fact — and, where the
measurement refuted a reading, asserts the refutation too. That is strictly
stronger: an `xfail` goes red only when the naive reading starts holding, whereas
asserting both the measurement and the refutation goes red the moment either half
changes. The measurements are recorded in
[`docs/migration/ambiguity-resolutions.md`](docs/migration/ambiguity-resolutions.md);
one question, `Q-EDITED-BLANK-WHEN-ZERO`, is recorded as
`MEASURED — DECLINED ON SCOPE`, because its answer is known and deliberately not
implemented — every picture it governs is a print-line item and report formatting
is out of scope.

### 12.2 The scenario tier — the state-parity proof

```bash
$C sh -lc 'cd /repo && python -m pytest -m scenario'
```

Each asserts an empty normalised diff for one scenario. There are **nine**, and
the ninth is deliberately distinguished from the other eight in the right-hand
column, because the count of what is committed and the count of what the plan
mandated are two different numbers and conflating them misrepresents both:

| Scenario | Test file | Basis |
| --- | --- | --- |
| clean batch post, General Ledger | `tests/scenarios/test_clean_batch_post_gl.py` | AAP §0.8.5 mandate |
| clean batch post, Sales | `tests/scenarios/test_clean_batch_post_sl.py` | AAP §0.8.5 mandate |
| clean batch post, Purchase | `tests/scenarios/test_clean_batch_post_pl.py` | AAP §0.8.5 mandate |
| clean batch post, IRS | `tests/scenarios/test_clean_batch_post_irs.py` | AAP §0.8.5 mandate |
| mixed accepted and rejected batch | `tests/scenarios/test_mixed_accepted_rejected_batch.py` | AAP §0.8.5 mandate |
| period-end totals update | `tests/scenarios/test_period_end_totals_update.py` | AAP §0.8.5 mandate |
| control-total mismatch rejection | `tests/scenarios/test_control_total_mismatch_rejection.py` | AAP §0.8.5 mandate |
| empty batch | `tests/scenarios/test_empty_batch.py` | AAP §0.8.5 mandate |
| General Ledger end of cycle | `tests/scenarios/test_end_of_cycle_gl.py` | **beyond the mandate** — see below |

"Clean batch post per ledger" is expanded into four cases because the four
ledgers exercise materially different code paths. As noted in §10.5, the
**control-total mismatch case is General-Ledger-specific**, since Sales and
Purchase batches balance by construction.

**Why there is a ninth.** The eight above discharge the mandate exactly: AAP
§0.8.5 asks for clean batch per ledger, mixed accepted-and-rejected, period-end
totals, control-total mismatch and empty batch, and **none of those five is an
end-of-period run**. The consequence was that `gl080` — one of the twelve
in-scope programs, and the owner of one of the migration's five `ROUNDED` stores
at `[general/gl080.cbl:L328]` — was covered by unit tests and by no state
comparison at all. `harness/scenarios/end_of_cycle_gl.yaml` closes that by
driving the real `gl_end_of_cycle` route, which is `general/general.cbl`'s
`load09.` dispatching `gl080`. It is an addition to the evidence, not a
reinterpretation of the mandate, so anywhere this documentation counts *the
mandated set* it still says eight.

### 12.3 The determinism tier

```bash
$C sh -lc 'cd /repo && python -m pytest -m determinism'
```

Two Python runs of one scenario under the same pinned clock must produce
byte-identical dumps. Determinism follows from §10.4 plus §11.2: there is no
hidden time source, no random seed, and no ordering nondeterminism from a
secondary index.

Both stack-backed tiers together:

```bash
$C sh -lc 'cd /repo && python -m pytest -m "scenario or determinism"'
```

Everything a bare host can run, which is the useful form while developing:

```bash
python -m pytest -m "not (scenario or determinism)"
```

### 12.4 Coverage

`pytest-cov` is present as **traceability evidence** that every traced module is
actually exercised (R-5). It is **not a quality gate**: there is deliberately
no `fail_under` and no `--cov` in `addopts`, because a coverage number never
decides whether this migration is correct. Only an empty scenario diff does.

Execution is never randomised and never parallelised. Posting order is
load-bearing and the comparison is order-sensitive, so no `xdist`, no
`pytest-randomly`, and no plugin that reorders collection.

---

## 13. The four mandated deliverables

### 13.1 The machine-readable data dictionary

- [`data_dictionary/acas_posting_dictionary.json`](data_dictionary/acas_posting_dictionary.json)
- [`data_dictionary/acas_posting_dictionary.schema.json`](data_dictionary/acas_posting_dictionary.schema.json)

Generated by `acas_posting/dictionary/generate.py` from the **authoritative
triple**: the copybook picture clause, the bridge host-variable declaration, and
the `CREATE TABLE` column definition. It currently carries 1061 entries covering
513 columns, 513 host variables, 1001 copybook fields and 46 work-file fields
across the 22 in-scope tables and 20 bridges. Regenerate or verify with:

```bash
python -m acas_posting.dictionary.generate --check
```

Field metadata is therefore **derived, not transcribed**, which eliminates an
entire class of error across several hundred fields, and every record field can
cite its dictionary key at run time through
`acas_posting/dictionary/loader.py`.

**Why the bridge is authoritative, with the decisive proof.** The internal IRS
posting table carries three columns — `POST4-DAY`, `POST4-MONTH` and
`POST4-YEAR` — that have **no counterpart in any copybook**. They exist only
because the bridge derives them from a date string under a guarded substring
rule `[common/irspostingMT.cbl:L982-L987]`, and when the guard fails the three
components stay zero while the raw date text is still stored, producing a row
that is internally inconsistent. A migration driven from the copybooks alone
would silently omit three columns of a posting table — and would also miss the
signed-to-unsigned narrowing that loses a value's sign *at the bridge*, before
any SQL executes.

### 13.2 Traceability

[`docs/migration/traceability.md`](docs/migration/traceability.md) — three
tables plus the supporting analysis: program → module for all twelve programs,
paragraph → function for every migrated section and paragraph with the `GO TO`
class annotated at each transfer site, and field → dictionary entry. It also
records the dual-alias facade as a **behavioural** difference rather than merely
a naming one, the three linkage shapes and the seven routes that bind them, the
three divergent abort gates, the five rejection classes, and the deliberate
omissions recorded **as** omissions.

### 13.3 The anomaly log

[`docs/migration/anomaly-log.md`](docs/migration/anomaly-log.md) — 22 canonical
entries, `A-1` … `A-22`, each with its locator, its sub-system and the Python
module that reproduces it.

**"Locked" is not one thing, and the register's §11 distinguishes four
relationships** because collapsing them into locked-or-not is what let three
entries be credited to tests that never asserted them:

| Relationship | Entries | Count |
| --- | --- | ---: |
| **Behaviour lock** — a test asserts the defect itself, so a future well-meaning "fix" turns the suite red. These are exactly the dagger (†) entries. | `A-1`, `A-2`, `A-3`, `A-4`, `A-5`, `A-7`, `A-8`, `A-9`, `A-10`, `A-11`, `A-13`, `A-14`, `A-19`, `A-21` | **14** |
| **State-level lock only** — the defect itself cannot be asserted, but a scenario asserts the state an unbroken defect must leave | `A-6` | **1** |
| **Record lock only** — a test asserts the anomaly reference is still carried on the field descriptor, so the *record* cannot be quietly deleted, without asserting a behaviour | `A-12`, `A-15`, `A-20` | **3** |
| **No lock of any kind** | `A-16`, `A-17`, `A-18`, `A-22` | **4** |

14 + 1 + 3 + 4 = **22**, no entry counted twice. The four with no lock are
recorded rather than asserted because their only observable is a comment, a name,
a dropped value or a behaviour that has not been proven for every caller — so no
state diff and no arithmetic assertion can see them. Each is nonetheless carried
at its reproduction site by a comment citing the same locator the register cites.

A handful of entries carry a `PENDING` status naming the ambiguity question that
still governs them. That is honest bookkeeping, not an oversight: the entry
records what has been measured and what has not.

### 13.4 Ambiguity resolutions and scenario diff evidence

- [`docs/migration/ambiguity-resolutions.md`](docs/migration/ambiguity-resolutions.md)
  — each semantic question that cannot be settled by reading, the experiment run
  against the compiled oracle, and the resolution adopted. `Q-1` the date
  module's reject contract, `Q-2` default arithmetic precision, `Q-3` a negative
  binary value through an unsigned host variable into an unsigned column, `Q-4`
  the batch record's length contradiction, `Q-5` the unexplained move, the
  `Q-5.1` … `Q-5.3` storage-semantics cluster, and the further questions
  discovered while writing the migration.
- [`docs/migration/scenario-diff-evidence.md`](docs/migration/scenario-diff-evidence.md)
  — the per-scenario evidence register, with an explicit verdict vocabulary that
  distinguishes an observed empty diff from anything merely expected. Nothing
  that was not observed is presented as observed, in either direction.

---

## 14. WARNING: known risks and gotchas

Read this section before changing anything. Every item below has cost somebody
time already, and most of them fail *silently*.

**The General Ledger has not been re-tested since the compiler migration.** The
maintainer says so himself: "I have not had any time to work with General at all
since it was migrated over to using the GnuCobol compiler (3.2 final) now some
years back" `[README.TXT:L51-L53]`. The same entry records that "all testing is
complete for IRS, Stock and Sales apart for some reports"
`[README.TXT:L50-L51]` while the Purchase ledger "is still undergoing system
testing" `[README.TXT:L45]`. Since the General Ledger contributes the majority
of the in-scope programs, expected values for GL scenarios must come **only from
the oracle** — never from the documentation, and never from reasoning about
intended behaviour. **If the compiled GL cycle behaves surprisingly, the
surprise is the specification.**

**Sort order is correctness, not performance.** `gl072` locates the
nominal-ledger row for a posting with a **sequential** read rather than an
indexed one `[general/gl072.cbl:L407-L408]`; it finds the correct account only
because `gl071` has already emitted the transaction stream in nominal-key order.
Perturb the sort and the program silently posts to the wrong account — no error,
no diagnostic, wrong balances. This must **not** be "optimised" into an indexed
read, however obviously faster that would be, and `gl071`'s output ordering is
asserted directly by a test rather than left to be caught indirectly by a state
diff.

**Truncation is the default; rounding is the annotated exception.** COBOL
`COMPUTE` truncates toward zero on store unless `ROUNDED` is written, and across
the entire in-scope cycle there are exactly **five** `ROUNDED` sites:

| Site | Statement |
| --- | --- |
| `[general/gl051.cbl:L791]` | VAT from net |
| `[general/gl051.cbl:L796]` | VAT from gross |
| `[general/gl080.cbl:L328]` | the cycle-to-period divide |
| `[irs/irs030.cbl:L1551]` | VAT from net |
| `[irs/irs030.cbl:L1562]` | VAT from gross |

Every other store truncates. Getting this backwards would corrupt essentially
every posted figure, which is why `acas_posting/cobol/arithmetic.py` makes
truncation the default path and rounding the explicitly annotated exception.
Two superseded, commented-out variants of the IRS computes survive beside the
live ones `[irs/irs030.cbl:L1550]`, `[irs/irs030.cbl:L1561]`; they are logged as
an anomaly, not resurrected.

**The three moving-average blocks disagree with each other, and must stay that
way.** The invoice path increments its activity counter before dividing
`[sales/sl060.cbl:L825-L827]`; the credit-note path in the same program **never
increments the counter at all** and additionally guards on the accumulator being
non-zero `[sales/sl060.cbl:L841-L843]`, which silently drops the first credit
note for a customer; and the cash path in a different program uses a third guard,
increments in a third position `[sales/sl100.cbl:L510]` and returns early on a
zero cleared date `[sales/sl100.cbl:L500-L501]`. Its divide is spelled the other
way round — `divide work-b by sales-pay-activety` `[sales/sl100.cbl:L511]`
against `divide sales-activety into work-2` `[sales/sl060.cbl:L827]` — and
computes the **same** quotient: `DIVIDE X INTO Y GIVING Z` and `DIVIDE Y BY X
GIVING Z` are both `Z = Y / X`, so the difference is **lexical**. The Agent
Action Plan describes this as "the opposite divide operand order", which is true
of the operand ORDER and not of the arithmetic; the divergence that must survive
the migration is the three guards and their differing counter handling.

On top of that the arithmetic truncates twice. The accumulator is declared with
**zero** decimal places `[sales/sl060.cbl:L206]` while the value added into it
carries two `[sales/sl060.cbl:L218]`, so pence are discarded on every
accumulation `[sales/sl060.cbl:L826]`; and the average field is a `binary-long`
integer `[copybooks/wssl.cob:L49]`, so the divide then discards the remainder as
well. Reproducing this requires modelling both field widths exactly — an
implementation that carried two decimals through would diverge from the oracle
on almost every invoice. **Normalising the three into one helper would be the
single easiest way to fail this migration.**

**`cobmysqlapi.o` has no build rule in the repository.** See §8.3 step 2. A
naive build from the compile scripts alone fails at link time with no obvious
cause. Use `harness/build_oracle.sh`.

**`copybooks/ACAS-SQLstate-error-list.cob` is missing from the frozen archive.**
See §8.7. Left alone, most `*MT` bridges fail to compile. It is handled with a
comments-only shim in the *build copy* and is **not** fabricated into the frozen
tree.

**The compile scripts always exit 0.** See §8.6. Their status is not a
build-success signal; scan the diagnostics.

**`common/masterLD.sh` is both untested and syntactically unrunnable.** See
§9.1. It is frozen and is not fixed; `harness/seed.sh` reproduces its contract.

**Rejections differ in their database effect, and a single generic rejection
path would fail the migration.** There are five distinct classes: a clean
rejection that leaves no trace at all `[general/gl072.cbl:L291-L292]`,
`[general/gl072.cbl:L306-L307]`; a run-aborting rejection whose database effect
is the *absence* of the later phases (§10.3); a **partial** effect, where the
IRS debit is rewritten before the credit account is even looked up so a missing
credit leaves an unbalanced debit and no posting record; a file-abandoning
rejection that still performs the end-of-job rewrites and closes, so the partial
state is committed rather than rolled back; and a **permanently failing facade
verb**, where the transfer-file handler rejects four of its published verbs
unconditionally at entry so a published `Rewrite` can never succeed. All five
are reproduced as they are.

**No scenario demonstrates a General Ledger balance moving, and an empty diff
from `clean_batch_gl` must not be read as if one did.** All three GL-route
scenarios — `clean_batch_gl`, `mixed_accepted_rejected` and
`control_total_mismatch` — end with every table unchanged. For
`control_total_mismatch` that is the whole point: the abort gate fires and AAP
§0.6.5 makes absence the expected effect. For the other two it is a **frozen
bridge defect**: `initialize TD-GLPOSTING-REC` never loads `HV-POST-RRN`
`[common/glpostingMT.cbl:L1053-L1066]` while `POST-RRN` is the table primary key
`[mysql/ACASDB.sql:L155,L169]`, so every non-fetch loader write targets the same
value and a seed can persist **at most one** `GLPOSTING-REC` row; and that row's
key does not survive the round trip in a form `gl070` will accept, because the
ten-byte group `WS-Post-Key` is moved into `HV-POST-KEY PIC 9(18) COMP`
`[common/glpostingMT.cbl:L283]` — over the maintainer's own recorded doubt about
that very field, `*> WARNING POST-KEY MAY WELL NEED CHANGING TO POST-RRN`
`[common/glpostingMT.cbl:L229]`. Measured after a run: `CLEARED-STATUS 0`,
`POSTED 0`, and all four ledger balances `0.00`, on **both** sides.
Reproducing that no-op is **correct** (R-4). What would be wrong is citing the
empty diff as posting parity. GL double-entry explosion and ledger accumulation
are covered by `tests/arithmetic/test_double_entry_explosion.py` and
`test_ledger_balance_accumulation.py` instead, and the shortfall against AAP
§0.8.5 for the General Ledger is recorded in §8.0 of
`docs/migration/scenario-diff-evidence.md`. Sales, Purchase, IRS and the
period-end route **do** move rows, so the limitation is specific to the GL
posting table rather than general.

**Two silent skips are genuinely silent.** `gl072` skips a posting whose batch
number is non-numeric `[general/gl072.cbl:L291-L292]` and skips a record whose
handler returned a specific error `[general/gl072.cbl:L306-L307]` — with no
message, no counter and no trace. Adding a warning would be an added behaviour
and therefore a defect (R-3).

**No performance work, by construction.** No performance target is named, and
the constraints preclude the usual levers: concurrency is forbidden, the schema
cannot gain an index, no caching layer may be introduced, and statement ordering
must match the original because the state diff is sensitive to it.
Exact-decimal arithmetic is inherently slower than binary floating point, **and
that trade is accepted without qualification.**

**Plaintext database transport is reproduced, and reported every time.** The
compiled program has no stronger policy, so the migration does not invent one;
the data-access layer requires the caller to declare the isolated-oracle
transport explicitly, so it fails closed rather than defaulting to plaintext.
Operators deploying against something other than the isolated oracle should
supply an encrypted transport policy where parity with that deployment permits
it.

### Shell gotchas that cost a session

- Always run a scripted stage with `-T` and redirect stdin from `/dev/null`;
  piping a Compose stage into `head` or `tail` can hang it.
- Never invoke `presql2` without redirecting stdin — it prompts and spins.
- `harness/diff_states.py` accepts only trees whose directory name ends in
  `.normalized` or `.norm`, so hand-built directory names will be refused.

---

## 15. Relationship to the maintainer's own documentation

The maintainer's documentation is **evidence, not editable prose**. None of it
is modified by this migration.

- **`README.TXT`** is the canonical document for the COBOL system: its release
  state, its features and its build and install procedure. It records the
  release as **v3.3 pre-final** in the entry dated **2025-09-21**, which is
  candid about its own limits — "This does not mean that all bugs have been
  found and all testing is complete" `[README.TXT:L39-L40]`. It opens by
  pointing at its own sibling, "The file README.nightly should also be read if
  using the last v3.2 code release" `[README.TXT:L1]`, and notes that its
  entries run newest-first, "Latest changes is at the TOP" `[README.TXT:L6]`.
- **`README`** is a **byte-identical duplicate** of `README.TXT` — both are
  14835 bytes and `cmp` reports no difference — and **`README.SVN`** contains
  only the line "See the file README." Both are noted here so that a reader
  meeting three similarly named files does not go looking for three different
  documents. Treat `README.TXT` as the canonical one.
- **`README.nightly`** documents the nightly builds.
- **`Changelog`** records the COBOL system's version history at system level:
  "Record for changes at system level - Also recorded in sub systems Changelog"
  `[Changelog:L1]`, including the entry dated **2025-09-20**, "3.3.00 Version
  update and builds reset." **This migration does not append its own history
  there.**
- **`ACAS-Manuals/`** holds the maintainer's LibreOffice / ODF manuals, and is
  likewise untouched.

The reason, in the AAP's own terms: these files "document the COBOL system and
its version history, and modifying them would misrepresent the maintainer's
record." Any diff that touches `README.TXT`, `README`, `README.SVN`,
`README.nightly`, `Changelog`, `comp-all.sh`, `common/`, `copybooks/`,
`general/`, `sales/`, `purchase/`, `irs/`, `stock/`, `mysql/ACASDB.sql`, `etc/`
or a vendored archive is a defect in the migration, regardless of how harmless
it appears.

### This document's history

Latest changes at the TOP, following the maintainer's date-first shape but with
a neutral attribution, since the migration work is not his.

```text
2026-08-04   *  ACAS Python migration
                Rewritten as the operator-facing entry point for the migration:
                the six binding rules with their practical consequences, the two
                partial migration boundaries with their line ranges, the three
                CLI linkage shapes, the five-step oracle bootstrap including the
                recovered cobmysqlapi.o build rule, the seeding contract and its
                exit codes, the ten-stage diff protocol and its registry, the
                three test tiers
                and the four mandated deliverables. Every claim about the frozen
                COBOL carries a verified [path:locator] citation.
                No maintainer document was modified.
```
