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

## READ THIS FIRST: parity against the frozen COBOL is NOT established

**The acceptance criterion of this project has not been met from this checkout,
and no claim in this file should be read as saying otherwise.** The criterion is
the AAP's own (§0.1.1, §0.8.5): an empty ordering-normalised diff of the affected
tables after a Python run versus a **frozen** compiled run against an identical
seed. It cannot presently be produced, for a reason that is measured rather than
predicted: a build of the frozen sources exactly as committed **fails**, because
`copybooks/ACAS-SQLstate-error-list.cob` is absent from the checkout while 22 of
the 28 generated `common/*MT.cbl` bridges `COPY` it. The member is **not**
fabricated — inventing a frozen source would breach R-3 and R-4 — so it has to
come from the maintainer.

Read **[§8.7](#87-stop-the-frozen-oracle-cannot-be-built-from-this-checkout)**
before you read anything else about parity, then §9.4 for the second measured
obstacle (the frozen loaders never reach a `COMMIT`), then
[`docs/migration/scenario-diff-evidence.md`](docs/migration/scenario-diff-evidence.md)
§0, which is the evidence register and states, verdict by verdict, what has and
has not been established. **`harness/reset_db.sh` enforces this rather than
trusting a reader's diligence**: with no attested frozen oracle it stops at exit
**77 — EVIDENCE UNAVAILABLE** before it drops a table, a status deliberately
distinct from "the two states differ", and against a transformed diagnostic
oracle it discloses on every exit path that it marks every
verdict **NO PARITY CLAIM**.

WARNING: this migration **targets behavioural exactness** — it is not a clean-up
project, and that inverts normal engineering judgement for the whole of it. A
legacy defect reproduced is correct. A legacy defect "fixed" on the Python side is
a parity failure, and 15 of the 22 known defects are locked in place by tests
precisely so that a well-meaning correction turns the suite red rather than
passing unnoticed. Read §2 (rule R-4) and §14 before changing anything. What is
*established* today is the static and unit-level work — the arithmetic tier, the
determinism tier, the traceability and dictionary deliverables — plus agreement
with a **disclosed-transformed diagnostic** oracle; what is *not* established is
frozen parity, per §8.7.

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

- The *objective* is that the Python cycle can replace the COBOL cycle without
  changing a single posted figure. That is the entire value of the exercise —
  and it is a property to be **demonstrated**, by the empty diff quoted above,
  not asserted. On this checkout it is **not yet demonstrated against the frozen
  oracle** (§8.7), so read every statement here as describing what the code is
  built to do and what has actually been observed, which §8.7, §9.4 and
  [`docs/migration/scenario-diff-evidence.md`](docs/migration/scenario-diff-evidence.md)
  keep separate.
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
presence would invite drift. There is **no ORM entity layer and no declarative
metadata** of any kind — nothing in the package could generate schema even by
accident, because nothing in the package models the schema as objects. The data
access layer issues literal SQL over an explicit connection, and the only
statements it issues are `SELECT`, `INSERT`, `UPDATE` and `DELETE` against the
22 in-scope tables.

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
└── scenarios/                8 YAML definitions: exactly the 8 AAP §0.8.5 mandates
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

**Two MODES of listed files sit outside the illustrative tree and inside those
patterns.** Neither is a file of its own:

| Mode | Covered by | Why it exists rather than being folded away too |
| --- | --- | --- |
| `harness/seed.sh --build-fixtures` | `harness/*`, `harness/**` | Generates the seed flat files each scenario declares. §0.2.1.1 puts `common/masterLD.sh` and the `*LD.cbl` loaders in scope "as the specification for how the harness seeds a scenario", and §0.4.1.7 gives `harness/seed.sh` the job of reproducing that per-file contract — which presupposes the files exist. Something has to produce them |
| `harness/dump_tables.py --make-fixtures` | `harness/*`, `harness/**` | The generator `harness/seed.sh --build-fixtures` drives. It lives in `dump_tables.py` because that module already owns the record layout and a value's external form; it stays a distinct mode because it emits COBOL, and emitting COBOL safely requires the literal-encoding guard a shell script cannot express — see §12's note on generated-source safety |

**The ten-stage driver is NOT among them any longer.** `harness/run_parity.sh` was
the last file justified on this reasoning, and it is gone (finding M-06): the
Agent Action Plan's harness inventory names eleven files plus `scenarios/` and it was
not among them, and §0.8.5's acceptance sequence is satisfied by the stages themselves. Every gate it
uniquely owned moved into the stage that owns the state it protects and the
orchestration was already implemented in `tests/conftest.py` — §11.1 tabulates
where each went, and §11.1a is the operator's own ten-stage recipe.

**What was NOT retained on this reasoning.** The same review flagged
`requirements-harness.txt` and `requirements-dev.txt`, and those were **removed**,
because §0.2.1.2 names the dependency artifacts *without* a wildcard — exactly two
files, `pyproject.toml` and `requirements.txt` — and §0.5.1 states the inventory as
one table. A named list and a trailing wildcard are different instruments, and the
distinction is the whole reason these were kept and those two were not. §7 records
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

### 5.1 Three files the plan covers by wildcard rather than by name

The Agent Action Plan names most target files individually, but three are reached
only through its **trailing wildcards**. They are listed here explicitly, because
a reader comparing the tree against the plan's per-file tables will not find them
there and should not have to guess whether they were smuggled in.

There were more. `acas_posting/cli/rdbms_params.py` is now SECTION 0 of
`acas_posting/cli/args.py`; `harness/scenario_yaml.py` and
`harness/scenario_stream.py` are the shared parser and the `--scenario-stream` mode
of `harness/normalize.py`; `harness/parity_stages.sh` is `PARITY_STAGES` in that
same file, published through `--print-stages` and `--print-stage-shell`;
`harness/table_digest.py` is the `--table-digest` mode of
`harness/dump_tables.py`; `harness/build_fixtures.sh` and `harness/make_fixtures.py`
are the `--build-fixtures` mode of `harness/seed.sh` and the `--make-fixtures` mode
of `harness/dump_tables.py`; and `harness/run_parity.sh` is gone entirely, its gates
moved into `harness/reset_db.sh` and `harness/run_cobol_scenario.sh` and its
orchestration already present in `tests/conftest.py` (§11.1). Each was folded into
the listed file whose job it already shared, so the definitions are unchanged and
there are fewer paths to keep in step.

| File | Covered by | Why it exists |
|---|---|---|
| `harness/seed.sh --build-fixtures` | §0.2.1.2 "Oracle harness: `harness/*`" | The frozen loaders read COBOL flat files, and most are `ORGANIZATION INDEXED` — a Berkeley DB Btree whose on-disk form belongs to the library version the image carries. Fixtures must therefore be **generated by compiled COBOL**, not hand-written. See §8.8. |
| `harness/dump_tables.py --make-fixtures` | §0.2.1.2 "Oracle harness: `harness/*`" | Generates the per-file COBOL writer that `harness/seed.sh --build-fixtures` compiles, from each scenario's `seed_records`, so no record layout is ever restated by hand. |

**The artifact boundary, measured rather than asserted.** Building the wheel and
listing it shows the boundary holds: the distribution contains **only**
`acas_posting/` and its `dist-info`. No `harness/`, no `tests/`, no `.cbl`,
`.cob` or `.scb`, no `.sql`, and **no JSON** either. `pyproject.toml` constrains
discovery with `[tool.setuptools.packages.find]` — `include = ["acas_posting*"]`
against an explicit `exclude = ["harness*", "tests*", "docs*",
"data_dictionary*"]` — and sets `include-package-data = false`, so what ships is
the seven code packages and nothing that happens to be lying in the checkout.
**The generated dictionary is a top-level sibling and stays one:** Agent Action
Plan §0.3.1 fixes it at `data_dictionary/`, so it is neither relocated into the
package by a `package-dir` mapping nor carried as `package-data`, and
`acas_posting/dictionary/loader.py` resolves exactly that committed path. One
artifact, one location, no possibility of two copies disagreeing.

So neither mode ships: both belong to harness files, which is what R-1
requires of them. **The connection-parameter resolver is no longer among them.**
It used to be `acas_posting/cli/rdbms_params.py`; it is now SECTION 0 of
`acas_posting/cli/args.py`, because §0.4.1.1 gives that module the job of binding
the system records and the six `RDBMS-*` fields of `SYSTEM-REC` are part of
exactly that binding — they are the only carrier by which a connection parameter
reaches the handlers `[common/acas008.cbl:L558-L563]`. Every name it published is
published unchanged from `args`, so a caller's import moves and nothing else
about it does.

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
| `harness/*` | the standard library, `PyYAML`, the database driver | `acas_posting` internals other than the CLI |

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

| Set | Package | Pin | Why it is here | Imported? |
| --- | --- | --- | --- | --- |
| runtime | `mysql-connector-python` | `26.7.0` | The database driver. Materialises `DECIMAL` as `Decimal` and integer columns as `int`, never as a float (R-2) | **Yes** — in `dal/connection.py`, and it is the only third-party module `acas_posting` imports |
| runtime | `SQLAlchemy` | `2.0.51` | Declared because AAP §0.5.1 fixes the runtime closure at this name and this version | **No** — see the note below |
| runtime | `greenlet` | `3.5.4` | `SQLAlchemy`'s own requirement, named as such by AAP §0.5.1 | **No** |
| runtime | `typing_extensions` | `4.16.0` | `SQLAlchemy`'s own requirement | **No** |
| harness | `PyYAML` | `6.0.3` | Parses the eight scenario definitions under `harness/scenarios/` | Yes, by the harness only |
| dev | `pytest` | `9.1.1` | The test runner | Yes, by the tests only |
| dev | `pytest-cov` | `7.1.0` | Coverage as traceability evidence (R-5), **not** a quality gate | Yes, by the tests only |

`coverage`, `pluggy`, `iniconfig`, `packaging`, `Pygments` and the `setuptools`
build backend are pinned alongside them in `requirements.txt`'s section 3.

⚠️ **`SQLAlchemy` is declared and is not imported, and both halves are
deliberate.** This is the one place in the dependency set where what is
*declared* is wider than what is *executed*, so it is stated outright rather than
left to be inferred from either artifact alone.

**Declared, because the plan fixes the closure and the plan is frozen.** AAP
§0.5.1 states the runtime inventory as four names at exact versions —
`mysql-connector-python` 26.7.0, `SQLAlchemy` 2.0.51 and, in its own words,
*"Pulls `greenlet` 3.5.4 as a transitive dependency"*, with `typing_extensions`
travelling with it. A manifest may not narrow that closure on implementation
grounds, however sound those grounds are: aligning code to the plan is the
standing rule, and the plan is not editable by the implementation. All four are
therefore declared in `pyproject.toml`, pinned to the plan's versions, and
hash-verified in `requirements.txt` section 1.

**Not imported, because the code takes the other of two permitted paths.** An AST
census over `acas_posting/` yields exactly one third-party top-level module,
`mysql`. AAP §0.8.2 preserves the user requirement verbatim and it is an
either/or — *"MySQL access via `mysql-connector-python` or SQLAlchemy Core with no
ORM entity layer"* — while §0.5.1 calls `mysql-connector-python` *"Oracle's
official MySQL driver and the primary database path"* and §0.1.2's diagram labels
the edge *"SQLAlchemy Core / connector"*, an alternative rather than a stack. The
connector is the path taken, which is the one the plan itself calls primary.

**An earlier revision resolved the same tension the other way**, by deleting the
three pins from both manifests so that declared and imported coincided (finding
MJ-20). That removed a real defect — three artifacts had been describing the Core
boundary as *active* — but it also left the manifests narrower than the frozen
plan, which is finding DEP-01. The pins are restored; the false activity claims
are not. What replaced them is the sentence you are reading.

**What decided it was the frozen behaviour, not the tidier diagram.**
`acas_posting/dal/connection.py` does not merely open connections; it reproduces
the frozen bridges' *connection ownership*. It re-opens one specific connection
object in place, keeps a single process handle that handlers deliberately share,
and lets a handler opt out of sharing where the bridge it mirrors keeps its own
SQL state across `CALL`s — `acas_posting/dal/acas016_invoice.py` says exactly
that at its own call site. A SQLAlchemy `Engine` owns connection lifecycle by
design and offers no supported way to re-connect a given connection in place, so
routing this through one would mean reimplementing that ownership model on top of
an abstraction built to own it, and changing **which physical session a statement
runs on**. Under R-4 and R-6 that is a behavioural risk taken for the sake of a
claim, and an empty scenario diff is the only currency this project accepts.

R-2 loses nothing by the choice: the exact-decimal guarantee is enforced by
`AcasConverter` and a live per-connection probe, which are driver-level and are
what a Core boundary would have had to pass through `connect_args` in any case.

**R-3 still holds by construction rather than by trust.** What R-3 forbids is an
ORM entity layer, declarative metadata that could emit DDL against the frozen
schema, and async, thread or pool libraries — not the presence of a distribution
on disk. No file in this repository imports `sqlalchemy` or `greenlet`, and none
constructs an `Engine`, a `MetaData`, a `Table`, a mapped class, a `Session` or an
async engine, so no schema can be generated and no coroutine scheduled even by
accident. Two independent checks assert that rather than assuming it:

- `tests/arithmetic/test_pic_field_descriptors.py` censuses every import
  under `acas_posting/` and requires the imported third-party set to be exactly
  `{mysql}`; requires `pyproject.toml`'s declared runtime set to be exactly the
  plan's closure, no wider and no narrower; requires `requirements.txt` to pin
  precisely that closure; and requires no artifact to describe the Core boundary
  as *active*. The declared-but-not-imported set is pinned to exactly the three
  names the plan declares, so a fourth could not join them unnoticed.
- `harness/Dockerfile.gnucobol` asserts inside the built image that all four
  declared names are importable at these versions and that importing `SQLAlchemy`
  leaves `sqlalchemy.orm` unloaded. It also records a measured fact rather than an
  assumed one: `import sqlalchemy` *does* load `greenlet`, because SQLAlchemy 2.0
  imports its concurrency shim eagerly — which is why `greenlet` is in the closure
  at all, and which schedules nothing on its own because no file here imports
  either module or calls `create_async_engine`.

Two contracts worth stating because breaking either is a defect rather than a
preference:

- **Pin parity.** `pyproject.toml` and `requirements.txt` carry identical exact
  versions for every name, and neither carries a name the plan does not declare. A
  version that differs between them is a defect, not a variation.
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

### 7.1 Advisory review of every pinned component

"Do not upgrade" above is a real constraint, and it obliges this project to say
what it is carrying rather than to leave advisory status unexamined. Every
pinned component was reviewed at **its exact pinned version**, and the result is
recorded here — including the parts that are not clean.

**Reviewed 2026-08-07.** Method, so a reader can re-run it rather than trust it:

- **The PyPI closure** was queried against [OSV.dev](https://osv.dev)
  (`POST /v1/querybatch`, ecosystem `PyPI`, exact `version`). OSV answers *"is
  this version affected"*, so a clean answer is evidence about the pin, not
  about the project's history.
- **The toolchain** was queried against the NVD CVE API 2.0 — by
  `virtualMatchString` CPE where a CPE exists, so that NVD performs the
  version-range match itself, and by keyword otherwise. Keyword hits were then
  read out of each advisory's `configurations` block, because keyword search
  matches any advisory *mentioning* a product and most such hits name a
  different version line entirely.

**Part A — the PyPI closure: clean at every pin.** All fourteen
distributions — the thirteen in `requirements.txt` plus `pip` 26.2.1, which
performs the hash-verified install — returned **zero** applicable advisories at
their pinned versions: `mysql-connector-python` 26.7.0, `SQLAlchemy` 2.0.51,
`greenlet` 3.5.4, `typing_extensions` 4.16.0, `PyYAML` 6.0.3, `pytest` 9.1.1,
`pytest-cov` 7.1.0, `coverage` 7.15.2, `pluggy` 1.6.0, `iniconfig` 2.3.0,
`packaging` 26.2, `Pygments` 2.20.0, `setuptools` 83.0.0, `pip` 26.2.1.

**Part B — the toolchain: three clean, two carrying applicable advisories.**

| Component | Pinned | Recorded | Applicable to the pin | Basis |
|---|---|---|---|---|
| MariaDB Connector/C | 3.3.4 | 2 | **0** | CVE-2020-13249 is bounded `<3.1.8`; CVE-2015-3152 names MySQL Connector/C `<=6.1.2` and MariaDB server 5.5/10.0 — neither range contains 3.3.4 |
| MySQL Connector/C | 6.1.11 | 5 | **0** | CVE-2017-3635 is bounded `<=6.1.10`; CVE-2015-3152 `<=6.1.2`; CVE-2020-13249 is a different product; CVE-2026-60179/-60180 are Connector/**C++** 9.7.x. Independently: the harness builds **only** MariaDB Connector/C and presents it under the `libmysqlclient` name the frozen compile lines expect, so 6.1.11 is vendored in the checkout but never built or linked |
| GnuCOBOL | 3.2 | 6 | **0** | All six are CPE-pinned to exactly `gnucobol 2.2` with no upper bound extending to 3.x. All six also require *compiling crafted COBOL source*, and the only source this harness compiles is the frozen in-repository checkout |
| JC preSQL | 1.14f / presql2 2.22 | 0 | **0** | No advisory is recorded. That is the absence of a published advisory for a niche tool, **not** a statement that no defect exists |
| **CPython** | **3.12.13** | 12 | **10** | Two of the twelve carry `vulnerable=False` for the Python CPE — Python is named as a *platform*, and the flaws are Odoo (CVE-2020-29396) and Django (CVE-2021-32052). The other ten apply |
| **MariaDB server** | **10.11.7** | 9 | **6** | Every range contains 10.11.7 (`>=10.11.1 <10.11.17`, `<10.11.18`, `<=10.11.15`). Three are excluded on a measured precondition, below |

**Why the two are not remediated by upgrading, and where that reasoning stops.**
For MariaDB and GnuCOBOL the version *is* the specification, not a
configuration choice: R-6 makes compiled behaviour the arbiter, and §0.5.2 of
the plan derives both versions from repository evidence — the schema header
records the producing server, and the maintainer's own compile script names the
compiler. Changing either changes the oracle, which would invalidate the
evidence the whole migration rests on rather than improve it. `Dockerfile.gnucobol`
refuses a `--build-arg` override of the compiler version for exactly this reason.

That argument does **not** extend to CPython, and it should not be stretched to.
`requires-python = "==3.12.*"` pins the *series*, not the patch level, so moving
to the newest 3.12.x is permitted without touching the plan and is the
recommended action for any real deployment. Two honest caveats: NVD models these
advisories with a single bound against the 3.13/3.14 lines (`<3.13.10`,
`<3.13.13`, `<3.13.14`, `<=3.14.4`), which formally marks *every* 3.12.x
affected and does not model 3.12's security-only branch, so a later 3.12.x may
well carry the backport even though the recorded range still covers it; and any
interpreter change is a runtime change, so it is subject to the same empty-diff
proof as a driver change.

**What actually reduces the exposure here, measured rather than assumed.**

- **None of the ten CPython advisories is reachable.** They name `plistlib`,
  `xml.dom.minidom`, `xml.parsers.expat`/`ElementTree`, `base64`, `tarfile`,
  `http.cookies`, `html.parser`, `webbrowser` and `shutil.unpack_archive`. An
  AST import census across `acas_posting/`, `harness/` and `tests/` finds **zero
  imports of any of them and no call to `shutil.unpack_archive`** — consistent
  with §0.5.1 of the plan, which names the load-bearing standard-library
  modules as `decimal`, `datetime`, `dataclasses`, `argparse`, `pathlib`, `csv`
  and `json`. A test keeps that census honest, so a future import of one of
  these modules is a visible change rather than a silent one.
- **Three of the nine MariaDB advisories have an absent precondition.**
  CVE-2026-3494 requires the server audit plugin with `server_audit_events`
  configured, and CVE-2026-35549 requires the `caching_sha2_password` plugin —
  neither plugin is installed. CVE-2026-49261 requires Galera, and the server
  reports `wsrep_on = OFF` with `wsrep_provider = none`.
- **The remaining six MariaDB advisories are authenticated server-side flaws,
  and are residual.** They are contained rather than eliminated: the stack's
  network is `internal: true` with **no published port**, so the server is
  unreachable from the host; the only clients are the harness's own scripts; and
  the application account holds `SELECT, INSERT, UPDATE, DELETE` on `ACASDB`
  alone, with no global privilege beyond `USAGE`.

**What would change this verdict.** A new advisory against any pinned
distribution; a pin moving; the harness gaining a network path from outside the
project; or `acas_posting`, `harness` or `tests` importing one of the modules
named above. This register is a point-in-time record, and re-running the two
queries above is the way to refresh it — not editing the table by hand.

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

An isolated harness network has no TLS material, so a connection to it crosses a
network in the clear. **The two halves of this repository treat that differently,
on purpose, and the difference is rule R-3.**

* **The five harness scripts REFUSE** a non-loopback target unless the operator
  either names a certificate authority or declares the network isolated. They are
  test tooling with no COBOL counterpart, so a refusal there adds nothing to the
  migrated cycle.
* **The shipped package REPORTS and CONNECTS.** The compiled `Mysql-1000-Open`
  has exactly two outcomes — it connects, or it reports `(FS-Reply 99,
  We-Error 911)` `[copybooks/mysql-procedures.cpy:L60-L128]` — and it inspects
  neither the address it was given nor whose credentials it was handed. A
  pre-connect refusal is therefore a disposition the compiled system has not got,
  and R-3 forbids adding one. So **exact-parity mode is the default**: the
  exposure is logged at WARNING, named as CWE-319 (unencrypted hop) or CWE-798
  (the placeholder credentials of `[copybooks/wssystem.cob:L138-L139]`), returned
  as a finding by `dal.connection.audit_connection_policy` — and the connection is
  made, exactly where the compiled cycle makes it. Reporting is separate from
  acceptance.

There is exactly **one** name for the isolation declaration and **one** set of
spellings for it:

| | |
|---|---|
| Key | `ACAS_DB_ALLOW_PLAINTEXT` |
| Yes | `1`, `true`, `yes`, `on` (case-insensitive) |
| No | `0`, `false`, `no`, `off`, or unset |
| Anything else | **refused** — the run stops and names the accepted spellings |
| Command line | **none.** No route publishes an option for this. The frozen counterpart takes its settings from outside the command line `[common/acas-get-params.cbl:L30]`, and a certificate path in `argv` is a process-listing leak, so the deployment contract below is the only source |
| Encrypted alternative | `ACAS_DB_TLS_CA` (plus `ACAS_DB_TLS_CERT` + `ACAS_DB_TLS_KEY` together) |

`harness/docker-compose.yml` sets it for the internal network. The five harness
scripts read it, and so does the shipped package, through one function —
`read_declared_flag`, published by `acas_posting/cli/args.py` — so one exported
value means one thing everywhere. Writing `false` grants nothing, and unrecognised text stops the run
rather than resolving to either answer: this variable decides whether a
credential and every posted figure may cross a network in the clear, and only
the operator who typed it knows what was meant.

#### Hardened mode — opt-in, and not parity evidence

A production deployment that wants the refusal asks for it by name. Two keys, read
from the same contract, each switching one report into a refusal raised **before**
the connect:

| Key | Effect when set |
|---|---|
| `ACAS_DB_REQUIRE_TLS` | a non-local, unverified, undeclared target is refused instead of reported. Outranks `ACAS_DB_ALLOW_PLAINTEXT`: with both set the connection is refused |
| `ACAS_DB_REQUIRE_DECLARED_CREDENTIALS` | a row still carrying the frozen placeholder credentials is refused instead of reported, unless `ACAS_DB_ALLOW_PLACEHOLDER_CREDENTIALS` declares them intended |

Neither is set by the harness and neither is inherited. **A run made under either
is not behavioural-parity evidence** — a connection refused before it is attempted
writes nothing where the compiled program would have written — so use them for a
deployment, never for a comparison. `ACAS_DB_TLS_CA` is the third option and the
only one that changes no disposition at all: it encrypts and verifies rather than
refusing.

Define the runner shorthand used throughout §8 to §11:

```bash
C="docker compose -f harness/docker-compose.yml run --rm -T \
     -e ACAS_SEED_AUTOCOMMIT=on gnucobol"
```

`-T` is required on every scripted stage: a tty is allocated by default and a
piped stage would appear to hang. Redirect stdin from `/dev/null` as well when a
command is backgrounded.

⚠️ **`ACAS_SEED_AUTOCOMMIT=on` is REQUIRED to obtain a fixture, and it is a
declared deviation from the AAP.** The default is the AAP-mandated `off` (§9.4), and
without this flag every seeding stage — `harness/seed.sh`, `harness/reset_db.sh` and
therefore protocol stages 1 and 5 — exits **76**, "the seed reported success
and left no rows". That is not a harness bug: it is the reproduced legacy defect. The frozen loaders
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

### 8.7 STOP: the frozen oracle cannot be built from this checkout

**This is the single most important section in this document.** A build of the
frozen sources, exactly as committed and with nothing altered, **fails**. That is
measured, not predicted, and it is the default behaviour of
`harness/build_oracle.sh`:

```
$ docker compose -f harness/docker-compose.yml run --rm -T gnucobol \
      /repo/harness/build_oracle.sh
...
frozen oracle: no source transformation applied; the build copy is byte-for-byte the checkout
verified by MEASUREMENT: zero source transformations; the build copy is byte-for-byte the frozen checkout
...
    glpostingMT.cbl:160: error: ACAS-SQLstate-error-list.cob: No such file or directory
    glbatchMT.cbl:160:   error: ACAS-SQLstate-error-list.cob: No such file or directory
    nominalMT.cbl:175:   error: ACAS-SQLstate-error-list.cob: No such file or directory
    ... 22 bridges in total ...
FATAL: comp-common.sh produced 22 fatal diagnostic line(s).
harness/build_oracle.sh FAILED with exit code 74.
```

`copybooks/ACAS-SQLstate-error-list.cob` is **absent from the checkout and from
`presql2-latest.zip`**, while being `COPY`'d by 22 of the 28 generated
`common/*MT.cbl` bridges and by the same 22 `*MT.scb` sources — 44 frozen files.
Those bridges cannot compile, and the handlers that `CALL` them cannot reach a
table. (`dummy-rdbmsMT.cbl` has no `*MT.scb` and does not reference it, so it is
unaffected.)

**Consequence, stated plainly: on this checkout there is no frozen oracle, so no
parity evidence can be produced.** No attestation is written, and
`harness/reset_db.sh` reports exit **77 — EVIDENCE UNAVAILABLE** before stage 1
drops a table, a status deliberately distinct from "the two states differ".
Nothing was compared.

**The member is not fabricated.** It carries the SQLSTATE list the bridges
document, and inventing a frozen source file would breach both R-3 (no new
validations) and R-4 (reproduce, never fix). It must be supplied by the maintainer.

**And it may not be supplied by this migration even from an authentic copy.** AAP
§0.8.1 states that any diff touching `copybooks/*.cob` **is a defect in the
migration, regardless of how harmless it appears** — so the member has to arrive as a
maintainer commit, not as migration work. That single commit is also the highest-value
one available to this project: it lifts the four class-A questions in
`docs/migration/ambiguity-resolutions.md` §14.5 as well as this blocker.

**Re-measured 2026-08-07, non-destructively** — the verification build was pointed at
a container-local `ACAS_BUILD` so the live build tree and the retained per-scenario
captures were left untouched. Observed: *"frozen oracle: no source transformation
applied; the build copy is byte-for-byte the checkout"*, then **44** diagnostic lines
naming **22 distinct** bridges, then *"FATAL: comp-common.sh produced 22 fatal
diagnostic line(s)"* and **exit 74**. `harness/reset_db.sh` against an unattested
build then exited **77** with *"Nothing was compared"* — before it dropped a single
table, so no database was touched. `docs/migration/scenario-diff-evidence.md` §0.1 tabulates both.

#### 8.7.1 What the shim is, and what it is measured to do

An explicitly requested `--transformed-oracle` build **generates** an idempotent,
comments-only include under the **writable build copy**, at
`$ACAS_BUILD/copybooks/ACAS-SQLstate-error-list.cob` — 13 lines, not one of them a
statement. The checkout's own `copybooks/` is never written.

**It is generated, not committed** (finding M-03).
`[harness/build_oracle.sh acas_install_sqlstate_comment_shim]` emits the text, then
**re-reads what it wrote** and fails the build if a single line is neither blank nor a
`*>` comment, and logs a disclosure naming the absent archive member every time it
runs. There is deliberately no repository copy: the Agent Action Plan's harness
inventory does not name one, a committed file of that name is one a reader can mistake
for archive material, and writing the member into `copybooks/` would be a fabricated
frozen source whatever it contained (R-3, R-4, AAP §0.8.1). The transformation is
registered in `ACAS_SOURCE_TRANSFORMS`, so any build carrying it attests
`oracle-source-is-frozen no` and **no verdict from it is a parity claim**.

Its content provably does not matter. Translating `glpostingMT.cbl` to C with
`cobc -C` under three variants — the comment-only shim, a zero-byte member, and
arbitrary different comment text — yields a **byte-identical** translation every
time. Only the `COPY` resolving matters.

That is what the file's position predicts. The `COPY` sits at
`common/glpostingMT.cbl:160`, between `identification division.` (L9) and
`environment division.` (L201) — a region where only comments are legal — so the
absent member cannot have carried data or procedure code, and the executable
SQLSTATE handling is already present in the frozen `PROCEDURE DIVISION` (`move
WS-MYSQL-SqlState to SQL-State`, 8 sites in this bridge alone).

**So this transform is behaviour-neutral, and it is not why a transformed oracle
cannot be evidence.** The other **40** transformed paths are: they alter
executable logic in the handlers, loaders and menus. See §8.10.

`docs/migration/ambiguity-resolutions.md` §10.1 records the missing member as a
build blocker, and `docs/migration/scenario-diff-evidence.md` records the
resulting evidence position.

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
$C /repo/harness/seed.sh --build-fixtures                 # all scenarios
$C /repo/harness/seed.sh --build-fixtures clean_batch_gl  # one scenario
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
| `overrides-used` | Whether either IDENTITY substitution was used — a replacement preSQL archive, or a redirected `cobmysqlapi.o`. `no` means neither was. It says **nothing** about the source transformations below, and reading it as "this is the unmodified oracle" is the mistake the next three rows exist to prevent. |
| `oracle-source-is-frozen` | **The plain answer to "was this compiled from the frozen checkout?"** `yes` only when the build copy is byte-for-byte the checkout, derived from the register of transformations actually APPLIED rather than from the catalogue of ones available. A frozen build is now the default — and on this checkout it fails before any attestation is written (§8.7), so in practice an attestation exists only for an explicitly requested `--transformed-oracle` build, where this reads `no`. See §8.10. |
| `source-transforms`, `source-transform-set-sha256` | How many build-copy sources differ from the frozen checkout, and one digest over the whole disclosure so a consumer can compare two builds with a single value. |
| `source-transform` × N | One record per transformed path: `source-transform<TAB>path<TAB>frozen-sha256<TAB>build-sha256<TAB>reason`. Both digests are published so a reader can recompute either side and diff the two trees. |

`harness/reset_db.sh` **requires** the attestation at stages 1 and 5 and refuses to
set up the comparison without it. It re-derives rather than trusts: it checks the
recorded archive digest equals the recorded pin, requires
`cobmysqlapi-provenance` to be one of the two legitimate values, re-computes
the module-set digest from the modules **on disk** so that replacing a single
`.so` after the build is caught, and requires `oracle-source-is-frozen` to be
stated at all — an attestation silent on that question cannot support a claim
about the frozen specification.

**It refuses a transformed oracle.** `oracle-source-is-frozen=no` ends the run with
exit **77 — EVIDENCE UNAVAILABLE**, naming the transform count and the set digest
and saying in terms that nothing was compared. An absent attestation ends it the
same way, because the commonest reason for one on this checkout is that the default
frozen build failed (§8.7). Passing `--accept-transformed-oracle` proceeds anyway
for diagnosis, and then **every** verdict the run prints is marked
`identical-against-diagnostic-oracle` / **NO PARITY CLAIM**, however the comparison
turns out — an empty diff against a repaired specification says the migrated cycle
matches a patched system, which is not the question this protocol exists to answer.

Two consequences to plan around:

- **`--only N` and `--from N` do not publish an attestation.** They are debugging
  modes and a partly-rebuilt tree is only partly this repository's. Build fully
  before producing evidence.
- **Setting `ACAS_PRESQL2_SHA256`, or pointing `ACAS_COBMYSQLAPI_OBJ` anywhere
  other than `/usr/local/lib/acas/cobmysqlapi.o`, permanently marks that build as
  unable to produce evidence.** The build still completes and still warns;
  `harness/reset_db.sh` then refuses to set up a comparison against it. To replace either legitimately, make it a
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

### 8.10 A transformed oracle is opt-in, disclosed, and refused as evidence

**Read this before quoting any empty diff.** The default build applies **no**
transformation at all (§8.7). When `--transformed-oracle` is requested explicitly —
or `ACAS_ORACLE_ALLOW_TRANSFORMS=1` is set — `harness/build_oracle.sh` edits the
**build copy** of a declared set of frozen sources. The frozen checkout is never
written — every `.cbl`, `.cob`, `.cpy` and `.scb` under `common/`, `copybooks/`,
`general/`, `sales/`, `purchase/`, `irs/` and `stock/` is byte-for-byte as
committed, and a `git diff` over those paths is empty. What differs is `$ACAS_BUILD`.

There are **41** such files, every one listed in the attestation with its frozen
digest, its build digest and its reason. They fall into four groups:

| Group | Files | What is changed |
|---|---|---|
| Missing archive member (**1** file, behaviour-neutral) | `copybooks/ACAS-SQLstate-error-list.cob` | **Created.** The 22 frozen `*MT` bridges `COPY` it from their Remarks paragraphs and the checkout does not contain it. The shim is comment-only, and the build refuses it if it ever acquires executable text. Measured content-independent: the generated C is byte-identical with the shim, with a zero-byte member and with different comment text (§8.7.1). |
| `IF` scope | 6 loaders — `glbatchLD`, `glpostingLD`, `irsnominalLD`, `irspostingLD`, `nominalLD`, `otm5LD` | A period on the first `MOVE` of each flat-file open-error branch ends the `IF` sentence, so the diagnostic, `CLOSE` and `GOBACK` that follow run even after a **successful** open. The period is removed so the branch has the scope the surrounding source states. |
| Connection propagation and ownership | 25 handlers (`acas000`…`acas032`, `acasirsub1`…`acasirsub5`), 3 secondary loaders (`dfltLD`, `finalLD`, `sys4LD`), both `mysql-procedures` copybooks, `irs030`, and the three menus | The credential fields are copied into `File-Access` for a second caller, the reply pair is reset before each dispatch, the process connection survives one handler's close, the declared RDB mode survives the menu's flat-file mirror, and the IRS end-of-job keeps its connection until the transfer cleanup. |

**Why they exist.** Without them the compiled cycle does not reach MySQL: a loader
returns zero having loaded nothing, a second handler connects to a local socket
with blank credentials, or the menu's exit path silently reverts the run to indexed
files. They are what makes a **runnable diagnostic** oracle possible.

**Why that does not make them acceptable in evidence.** Under R-6 the compiled
program *is* the specification and under R-4 its defects are the thing being
reproduced. Forty of these transforms repair executable logic — `IF` scope,
connection lifetime, credential propagation, stale reply pairs — so a build
carrying them has repaired the specification. Comparing the migrated cycle against
a repaired specification cannot establish that the migration reproduces the frozen
one, which is why `harness/reset_db.sh` refuses such a build with exit 77 unless
`--accept-transformed-oracle` is given, and discloses **NO PARITY CLAIM** on every
exit path when it is.

**What they do not touch.** No arithmetic statement, no `ROUNDED` site, no sort
key, no control-total comparison, no rejection path and no posted value. Each one
is a connectivity or `IF`-scope repair, stated per file in the attestation.

**What that means for a verdict.** An empty diff obtained under
`--accept-transformed-oracle` is agreement between the migrated cycle and a
**disclosed-transformed, partly repaired** compiled oracle. It is not, and must not
be described as, parity with the untouched checkout.
`harness/reset_db.sh` prints that distinction on every exit path of a waived run —
*"an empty diff drawn against this oracle would say the migrated cycle matches a
PATCHED system"* — and `tests/conftest.py` reports the oracle tiers UNAVAILABLE
rather than passing them, unless `ACAS_ACCEPT_TRANSFORMED_ORACLE=1` asks for the
same diagnosis. A verdict obtained either way is a diagnosis, not `identical`.
**No result in this repository currently establishes parity against the frozen
specification**, because the frozen specification does not presently compile (§8.7).
`docs/migration/scenario-diff-evidence.md` states that position per scenario.

**The register cannot go stale.** On any build that refreshes the tree, the sources
are digested immediately before the shim block and immediately after it, and the
set of paths that changed must **equal** the declared register. A shim added
without a register entry fails the build; a register entry with no shim behind it
fails it too.

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

`harness/reset_db.sh` and `harness/seed.sh` **default** it to the canonical
fixture root — `$ACAS_FIXTURES`, or `$ACAS_DATA/fixtures` when that is unset, plus
the scenario name, which is exactly where `harness/seed.sh --build-fixtures` writes — so
the option is only needed for a fixture built somewhere else. `harness/seed.sh`
itself takes no default, because it can be driven against an ambient data
directory with no scenario at all.

The **seeding window's autocommit mode** is likewise defaulted rather than
demanded: unset means the mode Agent Action Plan §0.5.2 mandates, which is **off**.
It reproduces the frozen no-COMMIT defect, under which seven loaders report
success, the tables read empty and the durability gate exits **76**.
`ACAS_SEED_AUTOCOMMIT=on` requests the only mode measured to leave a durable row,
as an explicitly declared deviation that yields a working fixture rather than
AAP-conformant evidence. Both modes were measured; the arbitration is `Q-10`
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

- **The seeding window defaults to autocommit OFF, which is what the Agent Action
  Plan mandates — and in that mode this repository cannot produce a seeded state.**
  Both halves of that sentence matter, so both are stated plainly. The AAP requires
  autocommit **off** during seeding (§0.2.1.1, §0.5.2, §0.4.1.7) on the strength of
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
  comparison) unreachable.

  **That does not license changing the default.** The AAP is the frozen, agreed
  specification for this migration; a harness that quietly seeded in the other mode
  would leave a reader of a parity result unable to tell that the configuration had
  been changed underneath them. So **`ACAS_SEED_AUTOCOMMIT` defaults to `off`**,
  nothing in the harness pins it, and a default seed exits **76** — measured, not
  predicted: seven loaders run, all return success, all seven seeded tables read
  zero rows. Nothing in the harness issues the `COMMIT` the frozen loaders omit
  (R-4), because a defect fixed is a failure.

  **`ACAS_SEED_AUTOCOMMIT=on` requests the deviation explicitly**, per invocation,
  so it appears in the command that ran — which is why the runner shorthand in §8.1
  carries it. It is the only mode measured to leave a durable row (8 rows across 7
  tables for `clean_batch_gl`), and the loader return codes are identical under both
  modes, so the mode is invisible to the frozen code. That is why the deviation is
  available at all; it is not why it could be silent. A fixture seeded this way is
  usable for development and diagnosis and is **not** AAP-conformant evidence, and
  `harness/seed.sh` warns to that effect rather than describing it as though
  it were. The measurements are written up in full at
  `docs/migration/ambiguity-resolutions.md`.

  **This is a determinate impossibility, not an outstanding task, and it is worth
  saying which.** The AAP mandates OFF for seeding; **no** frozen loader reaches a
  `COMMIT` (zero live `perform aa020-Rollback` / `perform aa030-Commit` sites across
  all 28 `common/*LD.cbl`, the sole `aa030-Commit` reference commented out at
  `[common/irsdfltLD.cbl:L437]`); and MariaDB discards an uncommitted session at
  disconnect. Those three together mean an AAP-conformant durable seed **cannot
  exist** on this checkout, and the migration may change none of them. Re-measured
  2026-08-07 in both windows: `off` → exit 76 with 0 rows in all seven seeded tables,
  `on` → exit 0 with 8 rows across 7 tables. Closing it is therefore a **decision**,
  and exactly one of two: the maintainer supplies loaders that commit, or the project
  owner authorises the deviation in writing as an amendment to AAP §0.5.2's premise.
  `docs/migration/scenario-diff-evidence.md` §0.1 (Obstacle 3) and §0.3 (Action 2)
  carry the argument and the evidence.

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

**Both runners refuse a target that cannot prove it is throwaway**, and the reason
is worth stating plainly: *driving either cycle posts*. Nominal balances are
rewritten, batches are stamped cleared, and a scenario that answers the IRS
end-of-job question with `Y` clears `PSIRSPOST-REC` outright
(`common/acas008.cbl:L313-L319`). The schema name is no protection at all here —
the frozen `mysql/ACASDB.sql` gives *every* ACAS installation in existence the
name `ACASDB`, so a check that the target is called `ACASDB` distinguishes the
harness database from precisely nothing.

What both runners require instead is the same fact `harness/reset_db.sh` already
requires, read the same way by all three: a **server setting** that
`harness/Dockerfile.mariadb` writes into the server's own configuration, read back
with one query.

| | |
| --- | --- |
| variable | `@@report_host` |
| must start with | `ACAS-harness-disposable-oracle` |
| on a stock MariaDB | empty — the harness server is nobody's replica, so the setting has no other effect |

A client cannot fake it and a session cannot set it, so its presence is evidence
and its absence is a refusal with exit status **90** in both runners (the same
number and the same meaning `reset_db.sh` uses). It is deliberately a server
setting rather than a table or a column: rule **R-3** admits no added DDL, so a
gate that needed one would make the violation load-bearing.

If you are running against the harness Compose service you already satisfy this
and will see one line confirming it. If the marker is absent because the image
predates it, **rebuild rather than acknowledge**:

```bash
docker compose -f harness/docker-compose.yml build mariadb
```

The escape hatch exists, and it is deliberately **target-scoped** — it names the
exact target it authorises, so one left in an environment cannot later authorise a
different database:

```bash
# only when driving a genuinely disposable target the marker cannot reach
ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE='<user>@<host>:<port>/<schema>'   # COBOL runner
ACAS_PY_ACKNOWLEDGE_DESTRUCTIVE='<user>@<host>:<port>/<schema>'    # Python runner
```

Each runner prints the exact string its own target needs, so there is nothing to
guess at. **A protocol-bound run refuses both variables** — along with
`ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE`, `ACAS_RESET_ACKNOWLEDGE`,
`ACAS_DB_ALLOWED_SCHEMAS` and `ACAS_DB_DISPOSABLE_HOSTS` — because evidence
production may not be aimed by hand. Each stage refuses its own while
`ACAS_PARITY_RUN_ID` is bound (§11.1a). Refused rather than quietly unset: an
operator who set one deliberately is told the evidence driver will not honour it,
instead of being left believing it applied.

**Neither runner takes the state capture either, and that is a property of the
protocol rather than an omission.** Capture ownership is single and it belongs to
stages 3 and 7, which run *after* the runner has exited — the only moment at which
the run status the capture's attestation carries is final. Each runner prints the
exact capture command instead, so a hand-driven run copies one line.

**`run_cobol_scenario.sh` drives the WHOLE ORDERED OPERATION LIST IN ONE
INVOCATION**, and `--operation` is **repeatable** — `--operation NAME` may be
given more than once and the names are driven in the order given. Stage 2 is
built as a single argv with one `--operation` per declared operation, in
the declared order, and publishes `cobol.operation-status` with **one record per
operation**. It also validates, before it drives the first operation, that **both** runners can drive
every one of them. A scenario that declares operations without either a repeated
`--operation` or an `operations:` list is *refused* rather than having its first
operation silently run.

⚠️ **This section said "ONE operation per invocation" until finding MJ-04**, which
described the runner as it was before it learned the list. The distinction is not
cosmetic: under the old contract a four-operation scenario was driven by four
separate invocations, only the last of which published a disposition, so nothing
downstream could tell a clean run of four operations from a clean run of one
followed by three that aborted — and the record that *was* published described
operation one while the database held the effects of all four. The runner states
the same history in its own comment above its operation loop.

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

The protocol is a rigid sequence, not an ad-hoc comparison. **`harness/normalize.py`
is the single definition of the ten stages and their labels**, and it prints them on
demand rather than anything restating them:

```bash
$C /repo/harness/normalize.py --print-stages
```

⚠️ **That is the shape; the count is ten.** The line above names the eight
*logical* steps and reads as nine because the reset appears once. The protocol
numbers **ten**, because it counts the reset on both sides and makes the
publication check its own gate. Anywhere in this project's older prose that says
"eight-stage" or "the stage-8 diff", read **today's stage 10** — the diff. The
authority is `[harness/normalize.py PARITY_STAGES]`, read by shell through
`[harness/normalize.py parity_stage_shell]` and by everything else through
`--print-stages`. And
**runner-local `Check n/8` labels are a different numbering entirely**:
`run_cobol_scenario.sh` and `run_python_scenario.sh` each print their own
preflight steps, which count that one script's internal checks. A runner's
`Check 8/8` is not the parity diff.

**An empty diff is the pass condition, and the only one.** A stage that exits
non-zero has produced no evidence, so re-seed rather than carry a partial
capture forward.

**There is no driver script: the operator runs the ten stages, in order, stopping at
the first non-zero exit** (finding M-06). A `harness/run_parity.sh` used to run them
from one invocation and it is gone — the Agent Action Plan's harness inventory
(§0.3.1) names eleven harness files plus `scenarios/`, and that was not one of them.
**`harness/` now holds exactly those eleven files and the eight scenario definitions,
and nothing else.** Nothing it uniquely enforced was dropped. Each gate moved into **the stage that owns the state it
protects**, which is stronger than a wrapper rather than weaker, because a
hand-driven stage is now guarded exactly as a composed one is:

| What the deleted driver enforced | Where it is enforced now |
| --- | --- |
| The oracle-provenance attestation — **exit 77 EVIDENCE UNAVAILABLE** | `harness/reset_db.sh`, `acas_assert_oracle_attestation`, run **before the first `DROP`**, so a refusal leaves the database untouched |
| Every declared seed file exists, checked before the schema is dropped | `harness/reset_db.sh`, `acas_assert_seed_files`, before it takes the sequential lock |
| Every declared operation is driveable by **both** sides | `harness/run_cobol_scenario.sh`, `acas_assert_operations_supported_by_both_sides`, immediately after the operation list resolves — before the first operation produces state |
| Destructive-target bypasses refused on the evidence path | Each stage refuses **its own**, on any run carrying `ACAS_PARITY_RUN_ID`: `reset_db.sh::acas_assert_no_evidence_bypass` for the two allow-lists and the two acknowledgements, `run_cobol_scenario.sh::acas_assert_no_evidence_bypass` and `run_python_scenario.sh::acas_py_assert_no_evidence_bypass` for the drive-side pair |
| The ten stages in order, aborting at the first non-zero | The operator, following the table below. `tests/conftest.py::run_scenario_parity` composes the identical sequence for the scenario tier, stage by stage |
| The stage registry, printed on demand | `harness/normalize.py --print-stages` |
| The per-stage administrative-credential scrub | The **file set**: only `reset_db.sh` and the `seed.sh` it delegates to may hold the pair, and every other harness script `unset`s it at entry (§7.1, SEC-04) |
| The published parity claim | `harness/diff_states.py`'s own `verdict.json` (§11.4) |

⚠️ **One consequence of the relocation had to be repaired, and it was found by
measurement rather than by reading.** The gate now fires for anything that invokes
`reset_db.sh` — which includes `tests/conftest.py`'s stage 1 and stage 5. Setting
`ACAS_ACCEPT_TRANSFORMED_ORACLE=1`, the documented way to run the stack-bound tiers
against a diagnostic build, therefore un-skipped those tiers and then failed all
**73** of them at stage 1 on exit 77: two acknowledgements for one decision, and only
one of them given. `tests/conftest.py::_transformed_oracle_waiver` now translates the
variable into `reset_db.sh --accept-transformed-oracle`, **conditionally** — with the
variable unset the tiers skip and the flag is never passed, so a hand-driven or
unacknowledged run still meets exit 77. Both halves are locked by
`tests/arithmetic/test_pic_field_descriptors.py`'s
`test_the_reset_refuses_a_transformed_oracle_as_evidence`, including the negative
direction: a waiver passed unconditionally fails that test.

⚠️ **Four options are deliberately not carried forward.** Each is named so that
nobody hunts for it:

- **`--from` / `--to`** — resume a range by stage number. This was the sharpest of
  the four: stages 1–5 of one attempt and 6–10 of another produce a verdict over
  artifacts that were never one run. What replaces it is *re-run from stage 1*; the
  run-scoped artifact paths and `diff_states.py`'s run-id equality check mean a mixed
  pair now **fails closed** rather than being compared.
- **`--dry-run`** — print the ten commands and run none. The table and the block
  below **are** that command list.
- **`--keep-going`** — carry on past a failing stage. No replacement, by design: a
  verdict produced past a failing stage was never evidence.
- **the `parity-result` summary file** — replaced by `verdict.json`, which is the
  machine-readable claim `harness/diff_states.py` publishes on both outcomes.

⚠️ **There is exactly one exception to "stop at the first non-zero", and it is
deliberate** (finding MJ-05): **stage 6 exiting 69**, the Python run stage reporting
that an operation's observed disposition contradicted the scenario's declared one. In
that one case the run **continues**, so that the capture, the normalisation and the
diff still happen and can localise the divergence to a table and a column instead of
leaving only a status code. It is remembered rather than forgiven: **the result can
never be parity after it, whatever the diff reports.** The rule is implemented in
`[tests/conftest.py RUN_PYTHON_BEHAVIOURAL_EXIT]` and
`[tests/conftest.py DISPOSITION_BEHAVIOURAL]` for the composed protocol, and stated
here for a hand-driven one; every other non-zero status stops the run.

The ten stages, which are the logical sequence above with the reset counted on
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

#### The operator contract — the four things that bind the ten stages

⚠️ **Four requirements make a hand-driven run mean what a composed one means. Each
was implicit in the deleted driver, so each is now stated.**

**One — ONE run id across all ten stages.** `ACAS_PARITY_RUN_ID` is what makes ten
separate invocations one attempt. Export it once, before stage 1, and pass it to every
stage. Without it each runner derives its own `local-<hex>` id, and stage 10 then
**refuses the pair** — correctly, because `run_id` is one of the provenance fields
that must be equal before a single row is compared. It is also what marks the run as
the **evidence path**, so every destructive-target bypass is refused while it is
bound (§11.1b).

**Two — stages 2 and 6 must be pointed at the per-scenario staged data.** Stage 1
copies the declared fixture files into `$ACAS_DATA/<scenario>` and the frozen loaders
run there, so `system.dat` is in *that* directory and not in `/data`. Both run stages
therefore need `ACAS_DATA` **and** `ACAS_LEDGERS` set to it; `tests/conftest.py`'s
`scenario_runtime_environment` does exactly this for the composed protocol.

**Three — stage 1 is `reset_db.sh`, not `seed.sh`,** exactly as stage 5 is.
Substituting `seed.sh` seeds *whatever the previous run left in the schema* — which
usually still produces an empty diff, and is the reason the mistake survives: the two
sides agree on a state neither of them established.

**Four — `--all-in-scope` is REQUIRED on all three capture and comparison stages,
and omitting it silently narrows the evidence** (finding MJ-03). Pass
`--all-in-scope` *and* `--scenario-file` at stages 3, 7 and 10; the two flags do
different jobs. `--all-in-scope` sets the **comparison bound** to all 22 in-scope
tables, while `--scenario-file` supplies the **provenance digest** that
`diff_states.py` requires to match on both sides. Without `--all-in-scope` the bound
falls back to the scenario's own `affected_tables` — five tables for most scenarios —
so an "empty diff" would attest agreement over a quarter of the surface, and could
not show a difference in anything the scenario did not expect to move. AAP §0.8.5
makes an empty diff **the** pass condition, so the narrower bound would let a
scenario certify parity while a system row differed.

```bash
N=clean_batch_gl
S="/repo/harness/scenarios/$N.yaml"
R="parity-$(date -u +%Y%m%dT%H%M%SZ)"     # ONE id for all ten stages
D="/data/$N"                              # the per-scenario staged data
P="-e ACAS_PARITY_RUN_ID=$R"              # every stage
Q="$P -e ACAS_DATA=$D -e ACAS_LEDGERS=$D" # the two RUN stages, additionally

# 1  reset the schema and seed the scenario
$C $P /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
# 2  run the compiled COBOL cycle
$C $Q /repo/harness/run_cobol_scenario.sh "$S"
# 3  capture the COBOL state          4  normalise it
$C $P python3 /repo/harness/dump_tables.py --scenario "$N" --side cobol --all-in-scope --scenario-file "$S"
$C $P python3 /repo/harness/normalize.py   --scenario "$N" --side cobol
# 5  reset and RE-SEED the same scenario
$C $P /repo/harness/reset_db.sh --seed-dir "/data/fixtures/$N" "$S"
# 6  run the migrated Python cycle
$C $Q /repo/harness/run_python_scenario.sh "$S"
# 7  capture the Python state         8  normalise it
$C $P python3 /repo/harness/dump_tables.py --scenario "$N" --side python --all-in-scope --scenario-file "$S"
$C $P python3 /repo/harness/normalize.py   --scenario "$N" --side python
# 9  and 10: the comparison verifies both captures are published before it compares
#     a single row, so stage 9 is enforced by stage 10 rather than skipped
$C $P python3 /repo/harness/diff_states.py --scenario "$N" --all-in-scope --scenario-file "$S"
```

**Stage 9 has no command of its own by design.** `harness/diff_states.py` calls the
same `verify_trees` check before it compares anything and exits `2` rather than `0`
when either capture is unpublished or the two disagree on scenario, side, run
identity or seeded bytes. The composed protocol surfaces it as a numbered stage so a
failure is reported as *stage 9* instead of arriving as a comparison error; a
hand-driven run gets the identical guarantee one stage later.

**Every stage's exit status is meaningful and none should be flattened.** The bands
are per script: `seed.sh` 70–78, `reset_db.sh` 80–91 plus **77 EVIDENCE
UNAVAILABLE**, the two runners 70–79 plus 90, and the three Python tools 80–87 —
each documented under its own `--help`. Two statuses matter most while reading
evidence: **77** from stage 1 means *nothing was compared* (the oracle cannot
arbitrate), and **76** from a seed means the AAP-mandated autocommit-off window left
no durable row, which is the reproduced frozen defect and not a harness fault.

`harness/diff_states.py` exits `0` with empty stdout for an empty diff, `1` for
a real behavioural difference, and `2` when the comparison could not be
performed at all. It also **refuses** a capture whose run stage did not attest
success, and refuses a pair that is empty on both sides — so a hand-driven run
fails closed instead of reporting that two empty captures were identical.

### 11.1a What a protocol-bound run refuses before it acts

Stages 1 and 5 **drop and re-apply the schema**. An evidence run must therefore be
stricter about its target than an administrative one: the same scripts are general
tools that document escape hatches for use outside evidence production, and those
hatches must not be reachable when the run's output will be compared.

**The two roles are told apart by the run itself, not by a wrapper.** A protocol run
binds `ACAS_PARITY_RUN_ID` before stage 1 — `tests/conftest.py`'s `bound_run_id` for
the composed protocol, the operator's own `export` for a hand-driven one — and while
it is bound, each stage refuses every bypass it would otherwise honour
(`reset_db.sh::acas_assert_no_evidence_bypass` and the two runner gates beside it).
Unbound, the hatches remain, because then the script is the administrative tool and
not a stage. This is where the deleted driver's entry gate went (finding M-06), and
it is stronger there: the guard now travels with the stage, so a **hand-driven**
stage 1 is scoped exactly as a composed one is, which the driver could never do.

Every one of the following is required, and each failure is refused before the stage
acts rather than discovered part-way through:

| Requirement | Refused otherwise |
|---|---|
| `ACAS_DB_NAME` is exactly `ACASDB` | A different or differently-cased schema, or an unset one |
| `ACAS_DB_HOST` is one of `mariadb`, `127.0.0.1`, `localhost`, `::1` | Any other host, including one that merely resolves locally |
| `ACAS_DB_PORT` fits the frozen four-character carrier, `1..9999` | `0`, `99999`, or non-numeric text — the carrier is `pic x(4)` at `[common/acas-get-params.cbl:L158]` and `[copybooks/mysql-variables.cpy:L91]` |
| `ACAS_RESET_CONSENT`, if set, names *this* target | A token naming another database or host, or one missing the `DESTROY` prefix — so a token left in an environment cannot later authorise a different server |
| The server-side disposability sentinel is present | Absent — `harness/reset_db.sh` proves disposability against the server, not merely against the host name |
| **None** of `ACAS_DB_ALLOWED_SCHEMAS`, `ACAS_DB_DISPOSABLE_HOSTS`, `ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE`, `ACAS_RESET_ACKNOWLEDGE` is set | Any of them set, *even to a harmless value*, on a run carrying `ACAS_PARITY_RUN_ID` |
| **Neither** drive-side acknowledgement — `ACAS_RUN_ACKNOWLEDGE_DESTRUCTIVE`, `ACAS_PY_ACKNOWLEDGE_DESTRUCTIVE` — is set | Either set on a bound run: each lets its runner post into a server that never declared itself disposable, so a verdict would describe an unknown database |
| A full-build provenance attestation exists and is untainted (§8.9) | Absent, unreadable, override-tainted, or describing modules other than those on disk — checked by `reset_db.sh` **before the first `DROP`**, so a refusal leaves the database untouched |
| **The attestation says the oracle was compiled from the FROZEN checkout** — `oracle-source-is-frozen=yes` (§8.9) | `no`, with exit **77 — EVIDENCE UNAVAILABLE**, distinct from the statuses that mean the two states differ. `--accept-transformed-oracle` proceeds for diagnosis and marks every verdict **NO PARITY CLAIM**. On this checkout the default frozen build fails, so this is the ordinary outcome (§8.7) |

The reset-side acknowledgement is the sharpest of them, and the reason it is refused
rather than merely warned about: `ACAS_RESET_ACKNOWLEDGE_DESTRUCTIVE` suppresses
**both** the static disposable-target check and the server-side sentinel proof, so
with it set the evidence path would accept any reachable database.

These are refusals, not defaults to be overridden. There is no flag to disable
them, because a flag to disable them would be the hole they close.

`harness/docker-compose.yml` already supplies exactly the canonical values, so a
Compose run needs none of this configured by hand — which is the point. If a stage
refuses, the target is not the canonical one.

### 11.1b What a run RETAINS, and where

A verdict that lives only in a terminal is not evidence. Every run publishes the
following, atomically and mode `600`, under `$ACAS_OUT` — which the Compose file
sets to `/out`, backed by a named volume, so the artifacts outlive the container:

| Artifact | Carries |
| --- | --- |
| `<scenario>/verdict.json` | the machine-readable verdict, written on **both** outcomes: the scenario, the outcome, the exit code, the tables compared and differing, the run id, the seed marker digest, and the digests of the scenario file, the frozen schema, both run manifests and the diff report |
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

### 11.1c How long a run is RETAINED, what protects it, and how it is DISPOSED of

§11.1b says what a run publishes. This section says what happens to it afterwards,
because an evidence directory that accumulates indefinitely with nothing said about
its lifetime is a defect in its own right — and the contents are not neutral.

**What is actually in there, measured rather than assumed.** On this clone the
evidence volume holds **1410 files, 11.5 MB**, across nine scenario trees — the eight
committed scenarios plus the removed `end_of_cycle_gl`, whose retained tree is cited by
the evidence register and is therefore kept (see the retention rule below). Each
tree carries `cobol/`, `cobol.normalized/`, `python/`, `python.normalized/`,
`diff.txt` and `verdict.json`. The dumps are `SELECT *` over the
in-scope tables, so they contain **monetary amounts** and **the primary keys that
identify the accounts, customers and suppliers they belong to** — a `GLLEDGER-REC`
row, for instance, leads with its nominal account number. This is accounting data
extracted from the database, not a log of what the harness did.

**Protection while retained.** Four properties, each already enforced rather than
merely intended:

| Protection | How it is enforced |
| --- | --- |
| Every artifact is mode `600` | Written that way, atomically, by the producing script (§11.1b) |
| The volume is not reachable from the host filesystem | It is a Docker named volume, not a bind mount of a repository path, so nothing in the checkout can be made to contain it and no `git add` can capture it |
| It cannot be shared with, or destroyed by, a sibling clone | The name is `acas-harness-${CLONE_INDEX}-out`, and `CLONE_INDEX` is a **required** variable — Compose refuses to start without it rather than defaulting to a name another run owns |
| Nothing rotates, prunes or expires it | Deliberate. A verdict cannot be re-derived by re-reading the tree; it can only be re-produced by re-running the protocol against the same seed and the same oracle. Automatic deletion would therefore destroy evidence, not tidy it |

**Retention period.** Keep a scenario's tree **for as long as any document cites
it**. In this repository the citing document is
[`docs/migration/scenario-diff-evidence.md`](docs/migration/scenario-diff-evidence.md),
which references artifacts **by digest** — so a tree whose digests appear there is
load-bearing and must not be removed, and a tree superseded by a later run of the
same scenario, with the register updated to the new digests, no longer is. That
rule is deliberately tied to a citation rather than to a number of days: the
evidence exists to support specific published claims, and it stops being needed
exactly when no claim depends on it.

**Disposal is explicit and target-scoped.** Sibling clones each own their own
`out` volume, and this workspace root is shared, so a broad command destroys
another run's evidence:

```bash
# Release the volume first: a volume in use by a container cannot be removed.
docker compose -f harness/docker-compose.yml down

# Dispose of THIS clone's evidence, named exactly. CLONE_INDEX is required, so the
# name cannot silently widen to a sibling's.
docker volume rm "acas-harness-${CLONE_INDEX}-out"

# Verify: the target is gone and every sibling is untouched.
docker volume ls --format '{{.Name}}' | grep -- '-out$'
```

⚠️ **Never `docker volume prune`, never `docker volume rm $(docker volume ls -q)`,
and never `rm -rf` a host path under the shared workspace root.** All three reach
volumes and working trees this clone does not own. The clone-namespaced name is the
guard, and it only works if it is the thing you type.

To discard evidence but keep the built oracle and the fixtures, remove **only** the
`-out` volume as above; `-build` and `-data` are separate volumes and rebuilding
them is expensive. To reset a scenario's evidence without touching the others,
delete just that scenario's subtree inside the volume rather than the volume itself.

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
the recipe in §11.1a and `tests/conftest.py` both do. A scenario's
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

**One producer, and only one.** `harness/dump_tables.py --table-digest` computes every digest
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
`end_of_cycle_gl`, declared `changed` and moved the row by construction, its Phase 5
advancing the cycle and rotating the quarter counter — that scenario has since been
removed (findings M-09 and M-17), and the observation is recorded because it is what
established the `changed` half of the claim. The fingerprint is kept
on top of the dump because it adds what the dump cannot — a SHA-256 over all 169
columns, the two withheld cells included, and a SHA-256 is not a disclosure.
`tests/conftest.py`'s `assert_system_record_parity` compares the two sides' post-run
digests, and each of the eight scenario tests calls it.

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
| `tests/arithmetic/` | 14 | `arithmetic` | nothing — no Docker, no MariaDB, no GnuCOBOL |
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
date components — **fourteen files, which is exactly the set AAP §0.4.1.7 names**.

The tier once held twenty. Six further groups were written during QA remediation
and given files of their own, which put the directory outside the planned
inventory; each has since been **merged verbatim into the planned file that owns
its subject**, so the fourteen names are also the whole of the tier. No assertion
moved subject and none was lost — the collected test-name multiset was compared
before and after every merge and was identical each time. Two of the six are
**structural** rather than arithmetic and live in this tier for its defining
property, which is not its subject but its dependencies: it needs no database,
no COBOL and no Docker, so it runs anywhere. The other four are **shipped-module
drivers**, and they exist because a pattern test can pass against a correct local
transcription while the module that ships is wrong:

| Merged group | Now lives in | What it covers |
| --- | --- | --- |
| shared storage and dispatch boundaries (structural) | `test_comp_binary.py` §17–§23 | the shared storage emulation, the dispatch boundaries, and `acas008`'s four unconditionally refused verbs — all four through the entity-named vocabulary, and the rewrite additionally through the handler-named one, which is the only one of the four `Proc-ZZ100-ACAS-IRS-Calls.cob` declares. The other three handler-named aliases are asserted **absent**, since publishing them would make the facade this migration's invention rather than the copybook's |
| deployment-contract boundaries (structural) | `test_pic_field_descriptors.py` | the transport-environment contract, the driver deadlines, the IRS bind boundary and the cross-file reference integrity of the documents and scenario definitions |
| `gl080` end-of-cycle driver | `test_gl080_cycle_divide_rounded.py` | `gl080_end_of_cycle.py` — the `ROUNDED` cycle-to-period divide, the unbounded quarter subscript, the second rotating quarter counter, and the archive and deletion phases. **No scenario declares the `gl_end_of_cycle` operation**, so this is the only place the module is executed at all |
| `gl072` silent-skip driver | `test_ledger_balance_accumulation.py` | `gl072_transaction_update.py` — both silent skips, each proven *reached* rather than inferred from end state, and the empty work file's at-end path |
| CLI-seam driver | `test_control_total_comparison.py` | the `acas_posting/cli/` seams — the key-1 status-before-close path, the IRS handler-named verb selection and its `FacadeGoback` boundary, the `gl071` serious-error short-circuit, and the RDBMS-parameter absent and unusable statuses |
| close-and-rejection driver | `test_double_entry_explosion.py` | `sl060`'s nested `GL-Posting-Close` (anomaly A-1) and `irs030`'s IR032 clean rejection — two call sequences no table dump can observe |

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

Each asserts an empty normalised diff for one scenario. There are **eight**, and they
are exactly the eight AAP §0.8.5 mandates — the committed count and the mandated count
are the same number:

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

"Clean batch post per ledger" is expanded into four cases because the four
ledgers exercise materially different code paths. As noted in §10.5, the
**control-total mismatch case is General-Ledger-specific**, since Sales and
Purchase batches balance by construction.

⚠️ **There was a ninth, and it has been removed — with a cost worth stating.** The
eight above discharge the mandate exactly: AAP §0.8.5 asks for clean batch per ledger,
mixed accepted-and-rejected, period-end totals, control-total mismatch and empty batch,
and **none of those five is an end-of-period run**. A ninth definition,
`harness/scenarios/end_of_cycle_gl.yaml`, was therefore added beyond the mandate to
drive the real `gl_end_of_cycle` route — `general/general.cbl`'s `load09.` dispatching
`gl080` — with `tests/scenarios/test_end_of_cycle_gl.py` beside it, and it was measured
end to end.

Both files have been **deleted** (findings M-09 and M-17), because the Agent Action
Plan's inventory names eight scenario definitions and eight scenario tests and this tree
is held to that inventory. **The consequence, stated rather than glossed: `gl080` — one
of the twelve in-scope programs, and the owner of one of the migration's five `ROUNDED`
stores at `[general/gl080.cbl:L328]` — has no table-state comparison behind it.** What
remains is not nothing: anomaly **A-2** (the unbounded quarter subscript) and anomaly
**A-3** (the second, independent rotating quarter counter) are locked in the arithmetic
tier by `tests/arithmetic/test_gl080_cycle_divide_rounded.py`, and the three ambiguity
questions that once waited on an end-of-period scenario — `Q-GL080-DIVIDE-BY-ZERO`,
`Q-QUARTER-SUBSCRIPT` and `Q-2`'s fifth `ROUNDED` site — were each resolved by
**standalone compiled probes**, not by that scenario, so none of them reverts to open.
The retained measurement is kept as history in
[`docs/migration/scenario-diff-evidence.md`](docs/migration/scenario-diff-evidence.md)
and the removed definition's design is described in
[`docs/migration/ambiguity-resolutions.md`](docs/migration/ambiguity-resolutions.md)
§16.1, so whoever needs it next can rebuild it rather than re-derive it.

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

**The command.** One line, non-gating, runnable on a bare host:

```bash
python -m pytest -m arithmetic --cov --cov-report=term-missing:skip-covered
```

Add `--cov-report=html` for a browsable copy in `htmlcov/`, or
`--cov-report=xml` for `coverage.xml`. `[tool.coverage.run]` fixes the measured
tree as `source = ["acas_posting"]` with `branch = true` and omits `harness/*`
and `tests/*` — belt and braces for R-1 — and `[tool.coverage.html]` and
`[tool.coverage.xml]` fix the two destinations. All three of `.coverage`,
`coverage.xml` and `htmlcov/` are gitignored, so producing the evidence never
adds a tracked file.

**The recorded figure.** Measured on this checkout with the command above, on
CPython 3.12.13:

| | |
|---|---|
| Tests run | **1,219 passed**, 114 deselected (the stack-backed tiers) |
| `acas_posting` modules measured | **89 of 89** |
| Modules with **zero** coverage | **0** |
| Modules at 100 % | 18 |
| Statements | 15,293 of 31,865 |
| Branches | 1,529 of 6,874 |
| Overall, branch-inclusive | **43.4 %** |

**What that number is, and is not.** ⚠️ **Two of these figures moved, and the
movement is recorded rather than overwritten.** The row above read *1,217 passed
/ 126 deselected / 90 modules / one module at zero / 41.9 %* until the six
arithmetic groups added during QA remediation were merged into the fourteen
planned files (findings M-11 to M-16) and `cli/rdbms_params.py` was folded into
`cli/args.py` (M-01). Merging changed the deselection arithmetic and folding
removed a module, so the figures are re-measured here rather than carried.

**No module is at zero any more**, and the one that used to be — the dictionary
**generator** — is now reached at **24 %** by the merged deployment-contract
group, which reads it to close the traceability census. Its own exercise is
still the one that matters, because the generator's job is to be *run*:

```bash
python -m coverage run -m acas_posting.dictionary.generate --check
python -m coverage report --include='acas_posting/dictionary/generate.py'
```

Measured: `--check` exits **0** — the committed artifact is byte-reproducible
from the frozen sources — and the generator itself comes out at **90 %** of
1,707 statements with branch coverage on.

Every module in the package is now reached by the infrastructure-free tier,
which is the R-5 claim being evidenced: the traced modules are exercised, not
merely present. The 43.4 % is a *branch-inclusive* figure over a package whose
program modules are dominated by paths a state comparison drives rather than a
unit test — the scenario and determinism tiers, which this host cannot run and
which are therefore deselected above. Reading it as a quality score would be
reading it as the gate it is deliberately not.

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
the `CREATE TABLE` column definition. It currently carries 1067 entries covering
513 columns, 513 host variables, **1001 distinct physical copybook declarations**
through 1007 copybook-view entries — the two figures differ because an `OCCURS`
declaration bound by several columns yields one entry per occurrence, and
publishing both is what makes a missing declaration visible instead of masked
(finding M-18) — and 46 work-file fields
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
| **Behaviour lock** — a test asserts the defect itself, so a future well-meaning "fix" turns the suite red. These are exactly the dagger (†) entries. | `A-1`, `A-2`, `A-3`, `A-4`, `A-5`, `A-6`, `A-7`, `A-8`, `A-9`, `A-10`, `A-11`, `A-13`, `A-14`, `A-19`, `A-21` | **15** |
| **Record lock only** — a test asserts the anomaly reference is still carried on the field descriptor, so the *record* cannot be quietly deleted, without asserting a behaviour | `A-12`, `A-15`, `A-20` | **3** |
| **No lock of any kind** | `A-16`, `A-17`, `A-18`, `A-22` | **4** |

15 + 3 + 4 = **22**, no entry counted twice. The four with no lock are
recorded rather than asserted because their only observable is a comment, a name,
a dropped value or a behaviour that has not been proven for every caller — so no
state diff and no arithmetic assertion can see them. Each is nonetheless carried
at its reproduction site by a comment citing the same locator the register cites.

⚠️ **This table read `14 + 1 + 3 + 4` with `A-6` in a `state-level lock only` row of
its own, and it was the STALE of two disagreeing censuses** (finding MJ-12). The
register's §11 carries the reconciled one and this copy now matches it, verified by
extracting the dagger set from the register's twenty-two entry headings mechanically
rather than by reading: fifteen daggers, and they are exactly the fifteen above.
`A-6` moved into the behaviour-lock row because
`tests/arithmetic/test_comp_binary.py` now calls the
migrated `acas008` directly and asserts the measured `WE-Error 988` / `FS-Reply 99`
pair; its scenario-tier no-change assertion is a *second* lock on an
already-locked entry, not a category of its own. **The register is the authority for
this census**; a count here that disagrees with §11 is this copy being out of date.

⭐ **One entry's credit changed BASIS rather than category, and it is worth naming**
(findings MJ-07 and MJ-12). `A-1`'s behaviour-lock credit used to rest on a scenario
state comparison — and a state comparison cannot see it, because `GL-Posting-Close`
writes nothing, so adding the missing period left an identical dump and that test
passed either way. Its lock is now
`tests/arithmetic/test_double_entry_explosion.py`, which drives the shipped
paragraph and asserts the verb sequence across the whole `IRS-Instead` × `Level-1`
truth table; the scenario tests are recorded as **state witnesses**. Only direct
discriminating tests are credited as locks.

A handful of entries carry a `PENDING` status naming the ambiguity question that
still governs them. That is honest bookkeeping, not an oversight: the entry
records what has been measured and what has not. On the ambiguity side the
register's §13 now carries **no** `PENDING — AWAITING ORACLE EXECUTION` entry at
all: the last one, `Q-GL084-ACCEPT-SEMANTICS`, was measured on 2026-08-08 by a
standalone `cobc 3.2.0` probe over a real 24×80 pty — no fixture edited, no seed
invented — and its first answer reversed the reading the source suggested while
its second corrected `programs/gl080_end_of_cycle.py`.

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
