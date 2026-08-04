# ACAS Python posting-cycle migration

PLEASE READ: this file documents the Python 3.12 migration and its comparison
harness. The maintainer's own [`README.TXT`](README.TXT), `README.nightly`, and
[`Changelog`](Changelog) still document the COBOL system and its release
history. They are evidence and are not edited by this migration.

WARNING: this is a behaviourally exact migration, not a clean-up project. A
legacy defect reproduced is correct. A legacy defect “fixed” on only the
Python side is a parity failure.

## What this is

`acas_posting` is a Python 3.12 clone of the ACAS batch posting cycle. “Exact”
has one operational meaning:

> the ordering-normalized diff of affected database tables after a Python run
> versus a COBOL run against an identical seed must be empty.

The COBOL remains in the repository, unmodified, serving simultaneously as
the specification and as the out-of-process comparison oracle. The shipped
Python package does not require a COBOL compiler or runtime.

The migration covers posting, batch, cycle, period, proof, and RDBMS effects.
It does not reproduce interactive data-entry screens, menu presentation, or
reports that have no database effect.

## The six binding rules

The rules live in the Agent Action Plan (AAP) §0.7.2. There is no separate
user-rules document.

### R-1 — No COBOL at runtime

The shipped `acas_posting` package contains no COBOL subprocess call, FFI, or
link to `cobmysqlapi.o`. `harness/` is a sibling, not a Python sub-package, and
the package manifest includes `acas_posting*` only. There is no import path
from the shipped package to the harness.

### R-2 — Zero binary floating point

All money and quantity arithmetic uses `decimal.Decimal`; binary integer
fields use Python `int`. `pandas` and `numpy` are prohibited, including in the
dump comparison. The frozen schema has no `FLOAT`, `DOUBLE`, or `REAL`
accounting column.

### R-3 — No new validation, fields, schema changes, or concurrency

The migration emits no DDL and has no schema migration tool. SQLAlchemy is
used at Core level only, with explicit statements and connections; there is
no ORM entity layer. Posting and tests are strictly sequential.

### R-4 — Legacy anomalies are reproduced, never fixed

> “There is no test suite: compiled COBOL execution is the behavioral
> specification, defects included. A defect reproduced is correct; a defect
> fixed is a failure.”

See [`docs/migration/anomaly-log.md`](docs/migration/anomaly-log.md). The
anomaly-locking tests deliberately fail if a well-meaning change normalises a
legacy defect away.

### R-5 — Full traceability

Every program maps to a module, every migrated paragraph maps to a function,
and every field maps to a data-dictionary entry. See
[`docs/migration/traceability.md`](docs/migration/traceability.md) and
[`data_dictionary/`](data_dictionary/).

### R-6 — Compiled behaviour is the tie-breaker

> “The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative
> record-layout ↔ table mapping — it is the data dictionary for this
> migration.”

Where reading leaves a semantic question open, the compiled program decides.
See
[`docs/migration/ambiguity-resolutions.md`](docs/migration/ambiguity-resolutions.md)
and
[`docs/migration/scenario-diff-evidence.md`](docs/migration/scenario-diff-evidence.md).

## What was migrated

| COBOL program | Python module |
| --- | --- |
| `gl051` | `acas_posting/programs/gl051_batch_control_check.py` |
| `gl070` | `acas_posting/programs/gl070_transaction_pre_process.py` |
| `gl071` | `acas_posting/programs/gl071_batch_sort.py` |
| `gl072` | `acas_posting/programs/gl072_transaction_update.py` |
| `gl080` | `acas_posting/programs/gl080_end_of_cycle.py` |
| `sl055` | `acas_posting/programs/sl055_invoice_extract_analysis.py` |
| `sl060` | `acas_posting/programs/sl060_invoice_posting.py` |
| `sl100` | `acas_posting/programs/sl100_cash_posting.py` |
| `pl055` | `acas_posting/programs/pl055_order_proof_extract.py` |
| `pl060` | `acas_posting/programs/pl060_order_posting.py` |
| `pl100` | `acas_posting/programs/pl100_payment_posting.py` |
| `irs030` | `acas_posting/programs/irs030_posting.py` |

Two boundaries are partial and must not be widened:

- `general/gl051.cbl`: only the control-total gate in `batch-print` §999
  and `end-batch`, `[general/gl051.cbl:L1096-L1134]`.
- `irs/irs030.cbl`: only `Ledger-Postings-Add`,
  `[irs/irs030.cbl:L1569-L1733]`.

The General Ledger execution order is:

1. batch check;
2. transaction pre-process;
3. sort;
4. transaction update;
5. deletion and end-of-period processing.

The labels in the source are not execution order: deletion is called Phase 3
but runs after Phase 4.

## What was excluded

The following remain outside the migration:

- all frozen COBOL, bridge, copybook, compile-script, and schema files;
- interactive data-entry, amendment, setup, and menu programs;
- report formatting with no database effect;
- non-posting utilities;
- the BASIC-family, Payroll, and Stock legacy trees;
- the eleven out-of-scope tables and eight out-of-scope bridges;
- schema evolution, new indexes, caching, and concurrency;
- a web tier, REST API, GUI, message queue, or ORM entity layer.

Presentation code follows three rules:

1. a diagnostic `DISPLAY` with no database effect becomes a log record;
2. an `ACCEPT` that gates a write becomes an explicit CLI parameter, preserving
   the COBOL default or lack of default;
3. an acknowledgement-only pause is dropped, but any control transfer in that
   error path is retained.

## Repository layout added by the migration

```text
acas_posting/
  cli/
  cobol/
  dal/
  dictionary/
  programs/
  records/
  __main__.py
  clock.py
  dates.py
  workfiles.py
data_dictionary/
docs/migration/
harness/
  scenarios/
tests/
  arithmetic/
  determinism/
  scenarios/
pyproject.toml
requirements.txt
requirements-harness.txt
requirements-dev.txt
README-python-migration.md
```

Nothing in the existing tree was relocated, renamed, or restructured.

### Import boundaries

| Area | May import | Must not import |
| --- | --- | --- |
| `acas_posting.cobol` | standard library | DAL, CLI, harness |
| `acas_posting.records` | `acas_posting.cobol` | DAL, CLI, harness |
| `acas_posting.dal` | records, dictionary, SQLAlchemy Core, MySQL connector | programs, CLI, harness, ORM entities |
| `acas_posting.programs` | records, COBOL helpers, DAL facades | CLI internals, harness |
| `acas_posting.cli` | programs, public DAL/record contracts, clock | harness |
| `tests/arithmetic` | COBOL helpers and records | database internals, harness runtime |
| `tests/scenarios` | shared protocol fixtures | reimplemented dump/diff logic |
| `tests/determinism` | shared protocol fixtures, clock, arithmetic | DAL internals, COBOL runtime calls |

## Prerequisites

- CPython **3.12**. `pyproject.toml` requires `==3.12.*`; 3.13 is outside
  the parity evidence. The AAP reference interpreter was 3.12.3 and the current
  harness run uses 3.12.13. Both use the C `_decimal` implementation; the
  pure-Python fallback is not accepted for parity evidence.
- Docker Engine and Compose v2, only for the compiled oracle and the
  scenario/determinism tiers.
- `openssl`, if credentials need to be generated.

The arithmetic tier needs no Docker, MariaDB, or GnuCOBOL.

## Install

Create an isolated Python environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
python -m pip install --require-hashes -r requirements-harness.txt
python -m pip install --require-hashes -r requirements-dev.txt
```

For editable development:

```bash
python -m pip install -e '.[test]'
```

The dependency sets are pairwise disjoint and exact:

- runtime: `mysql-connector-python==26.7.0`,
  `SQLAlchemy==2.0.51`, `greenlet==3.5.4`,
  `typing_extensions==4.16.0`;
- harness: `PyYAML==6.0.3`;
- test: `pytest==9.1.1`, `pytest-cov==7.1.0`, and their pinned
  reproducibility dependencies.

A version mismatch between a manifest dependency set and its corresponding
requirements file is a defect.

## Prepare the Compose stack

The stack has two services: MariaDB 10.11.7 and the GnuCOBOL 3.2 builder and
runner. Credentials have no committed defaults.

```bash
export MARIADB_ROOT_PASSWORD="$(openssl rand -base64 24)"
export ACAS_DB_USER=acas
export ACAS_DB_PASSWORD="$(openssl rand -base64 9)"
docker compose -f harness/docker-compose.yml up -d mariadb
```

Keep the application user and password within the frozen `pic x(12)` fields.
A longer value is truncated on the COBOL side and causes the two
implementations to authenticate differently.

Define the runner shorthand:

```bash
C="docker compose -f harness/docker-compose.yml run --rm -T gnucobol"
```

## Build the compiled COBOL oracle

The supported operator command is:

```bash
$C /repo/harness/build_oracle.sh
```

For a repeat build that deliberately preserves the existing writable build
tree:

```bash
$C /repo/harness/build_oracle.sh --no-refresh
```

`harness/build_oracle.sh` performs the five-step bootstrap in a writable
`$ACAS_BUILD`; the repository is mounted read-only:

1. unpack the vendored `presql2-latest.zip` as `presql2-package/`;
2. compile `cobmysqlapi38.c` to `cobmysqlapi.o` with the recovered rule:

   ```bash
   gcc -I/usr/local/mysql/include \
     -c cobmysqlapi38.c -o cobmysqlapi.o -fPIC
   ```

   Do not use `old-apis/cobmysqlapi.005.c` or
   `old-apis/cobmysqlapi3.c`.
3. build JC preSQL and its helpers using the vendored 1.14f package;
4. run the maintainer's `common/comp-common.sh` against the writable build
   copy;
5. run `comp-all.sh` in the maintainer's order:
   Common → General → IRS → Purchase → Sales → Stock.

The wrapper also installs idempotent build-copy compatibility shims. They
never edit a frozen source. One example is the missing
`ACAS-SQLstate-error-list.cob`, which is a comment-only include materialised
under `$ACAS_BUILD/copybooks`.

WARNING: the compile scripts are not reliable success signals.
`common/comp-common.sh` and `comp-all.sh` end in unconditional zero exits.
The wrapper therefore scans diagnostics, verifies the expected programs,
handlers, loaders, and `*MT` bridges, and fails closed.

The runtime loader search path is reproduced in this order:

```text
/usr/local/lib/gnucobol
/usr/local/lib
/usr/local/mysql/lib
/usr/lib
```

The MySQL client prefix must be `/usr/local/mysql`, and the image includes
ncursesw for `accept_numeric.c`.

## Build scenario fixtures

Fixture records are declared as quoted text in the scenario YAML. The builder
materialises the actual indexed/relative files through generated COBOL writers
compiled against the frozen definitions, then reads them back through those
same definitions.

Build all fixtures:

```bash
$C /repo/harness/build_fixtures.sh
```

Or one scenario:

```bash
$C /repo/harness/build_fixtures.sh clean_batch_gl
```

Generated fixtures, `SYS-DISPLAY.log`, and file-handler logs are restricted to
their owner. The builder refuses a result with any group/other permission.

### Why `common/masterLD.sh` is not run

There are three independent reasons:

1. its header says `THIS SCRIPT HAS NOT YET BEEN TESTED`
   `[common/masterLD.sh:L4-L5]`, corroborated by the 2025-03-07
   `Changelog` entry;
2. all 24 loader lines at L93-L116 omit the separator before `fi`, and
   `bash -n` rejects the file;
3. it ends with an interactive `less SYS-DISPLAY.log`.

The file is frozen and is not fixed. `harness/seed.sh` reproduces its
per-file contract instead.

The in-scope loader mapping includes:

| Flat file | Loader |
| --- | --- |
| `system.dat` | `systemLD`, `sys4LD`, `finalLD`, `dfltLD` |
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

The frozen loader status meanings are 128 for unset RDBMS parameters, 64 for
the RDBMS flag not set, and 16 for a write error; values above 63 abort the
load. The harness additionally refuses a nominally successful seed that
persists no rows.

## Run both cycles and diff

The recommended command is the fail-closed driver:

```bash
N=clean_batch_gl
S="/repo/harness/scenarios/$N.yaml"
$C /repo/harness/run_parity.sh \
  --seed-dir "/data/fixtures/$N" \
  "$S"
```

It performs:

```text
reset + seed
run compiled COBOL
dump COBOL
normalise COBOL
reset + re-seed
run Python
dump Python
normalise Python
verify both manifests
diff
```

An empty diff is the only pass condition. A non-zero earlier stage produces
no parity claim.

The equivalent manual stages are documented at the top of
`harness/docker-compose.yml`, but the driver is preferred because it enforces
order and stops at the first failure.

### Three linkage shapes

The runners preserve three distinct call shapes:

- General Ledger:
  `ws-calling-data, system-record, to-day, file-defs`
  `[general/gl070.cbl:L245-L248]`;
- Sales and Purchase: the same plus the fourth system record
  `[sales/sl060.cbl:L395-L399]`;
- IRS: `IRS-System-Params, WS-System-Record, File-Defs`, with no
  calling-data block and no `to-day`
  `[irs/irs030.cbl:L552-L554]`.

### CLI routes

```text
python -m acas_posting general post-cycle
python -m acas_posting general end-of-cycle
python -m acas_posting sales invoice-post
python -m acas_posting sales cash-post
python -m acas_posting purchase order-post
python -m acas_posting purchase payment-post
python -m acas_posting irs post
```

The route modules dispatch:

- `gl_post_cycle.py`: `gl070`, hard term-code-5 gate, `gl071`, `gl072`;
- `gl_end_of_cycle.py`: `gl080`;
- `sl_invoice_post.py`: `sl055`, then `sl060`;
- `sl_cash_post.py`: `sl100`;
- `pl_order_post.py`: `pl055`, then `pl060`;
- `pl_payment_post.py`: `pl100`;
- `irs_post.py`: `irs030`, including the transfer-file clear decision.

A batch left open makes `gl070` set term code 5
`[general/gl070.cbl:L289]`. The menu returns before `gl071` and `gl072`
`[general/general.cbl:L810-L811]`. The Python route treats this as a hard
phase boundary, not a warning.

### Controlled clock

`acas_posting/clock.py` pins exactly two observables at the CLI boundary:

- `to-day pic x(10)` in DD/MM/CCYY form;
- binary `Run-Date` `[copybooks/wssystem.cob:L67]`.

Every in-scope posting program has zero clock reads. The menu/date-service
path supplies the values through
`[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]`. There is no default that
resolves to the current time.

Every scenario also pins `IRS-Instead` explicitly. Leaving this three-state
switch implicit would make the affected-table list ambiguous.

## State capture and normalisation

All 22 in-scope tables have a single-column primary key and no secondary
index. The dump is therefore:

```sql
SELECT * FROM `<table>` ORDER BY `<primary-key>`;
```

There is no timestamp masking or surrogate-key remapping.

`harness/normalize.py` has exactly three jobs:

1. trailing ASCII-space canonicalisation for fixed `CHAR` columns;
2. decimal rendering at the declared scale;
3. the explicit date-text allow-list.

It does not make different stored values compare equal. A non-empty diff is a
real behavioural difference.

## Tests

The arithmetic tier has 15 test files and needs no external service:

```bash
python -m pytest -m arithmetic
```

Expected arithmetic values are captured from compiled probes, never derived
by reading the COBOL and deciding what it ought to do.

The eight scenario files require the Compose stack:

```bash
$C sh -lc 'cd /repo && pytest -m scenario'
```

The scenarios cover clean GL, Sales, Purchase, and IRS posting; mixed
accepted/rejected input; period totals; control-total mismatch; and an empty
batch. The control-total mismatch is General-Ledger-specific because the
Sales and Purchase batches balance by construction.

The determinism tier runs two Python cycles from identical seeds and compares
both structurally and byte for byte:

```bash
$C sh -lc 'cd /repo && pytest -m determinism'
```

To run both stack-backed tiers:

```bash
$C sh -lc 'cd /repo && pytest -m "scenario or determinism"'
```

`pytest-cov` is traceability support, not a quality gate. No coverage
threshold is enforced.

## Mandated deliverables

- `data_dictionary/acas_posting_dictionary.json` and its JSON Schema:
  machine-readable field mapping generated from the copybook, bridge host
  variable, and `CREATE TABLE` definition. The bridge is authoritative; for
  example, the IRS posting bridge derives day, month, and year columns that
  exist in no copybook `[common/irspostingMT.cbl:L982-L987]`.
- `docs/migration/traceability.md`: program-to-module,
  paragraph-to-function, and field-to-dictionary mapping.
- `docs/migration/anomaly-log.md`: the canonical reproduced defects and
  additional measured candidates.
- `docs/migration/ambiguity-resolutions.md`: semantic questions and compiled
  arbitrations.
- `docs/migration/scenario-diff-evidence.md`: per-scenario observed parity
  evidence.

## WARNING: known risks and gotchas

- The maintainer states that General had not been exercised since its migration
  to GnuCOBOL 3.2 final, while Purchase was still under system testing
  (`README.TXT`, 2025-09-21). General and Purchase expected values therefore
  come only from the oracle. If the compiled GL cycle behaves surprisingly,
  the surprise is the specification.
- Sort order is correctness, not performance. `gl072` performs a sequential
  nominal-ledger read `[general/gl072.cbl:L408]` and depends on the stream
  emitted by `gl071`. Do not “optimise” it into a keyed lookup.
- Unrounded COBOL stores truncate toward zero. `ROUNDED` is exceptional and
  occurs only at the explicitly traced sites.
- The moving-average blocks disagree. Do not combine them into a common
  “clean” helper.
- `cobmysqlapi.o` has no build rule in the checkout. Use
  `harness/build_oracle.sh`.
- `common/masterLD.sh` is untested, syntactically invalid, and interactive.
  Use `harness/seed.sh` through the supported driver.
- There is no performance target. No concurrency, cache, or new index may be
  introduced, and exact decimal arithmetic is intentionally slower than
  binary floating point.
- Plaintext database transport is reproduced when explicitly permitted because
  the compiled program has no stronger policy. The harness reports it every
  time; production operators should supply an encrypted transport policy where
  parity with that deployment permits it.

## Relationship to the maintainer's documentation

`README.TXT` is canonical for the COBOL system. `README` is a byte-identical
duplicate, `README.SVN` points to it, and `README.nightly` describes nightly
builds. The 2025-09-21 entry calls the system v3.3 pre-final and explicitly
says testing was not complete.

`Changelog` records the COBOL system's system-level version history, including
the 2025-09-20 3.3.00 reset. The migration does not append its own history
there.

`ACAS-Manuals/` contains the maintainer's ODF manuals. It is also untouched.
These files document the COBOL system and its history; modifying them would
misrepresent the maintainer's record.
