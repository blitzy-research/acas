#!/usr/bin/env python3
"""Deterministic state capture: `SELECT * FROM <table> ORDER BY <primary key>`.

Stages 3 and 7 of the eight-stage parity protocol the harness exists to
run. Agent Action Plan section 0.3.2 fixes the stage order - "seed, run,
dump, normalize, reset, run, dump, diff" - and this module is both dumps.
Its whole mandate is one line of the plan's transformation map, section
0.4.1.7: "`SELECT * FROM <table> ORDER BY <primary key>` for the 22
in-scope tables".

It reads twenty-two tables of the frozen schema `mysql/ACASDB.sql`, one
after another on one connection, and writes one JSON file per table. It
computes nothing, canonicalises nothing and repairs nothing.

    [harness/docker-compose.yml:L44-L51]  the eight stages, in order
    [harness/docker-compose.yml:L268]     stage 3, the COBOL-side dump
    [harness/docker-compose.yml:L272]     stage 7, the Python-side dump

    stage 1  seed        harness/seed.sh          (COBOL *LD loaders)
    stage 2  run  COBOL  harness/run_cobol_scenario.sh
    stage 3  dump        THIS MODULE              -> $ACAS_OUT/.../cobol
    stage 4  normalize   harness/normalize.py
    stage 5  reset       harness/reset_db.sh      (+ re-seed)
    stage 6  run  Python harness/run_python_scenario.sh
    stage 7  dump        THIS MODULE              -> $ACAS_OUT/.../python
    stage 8  diff        harness/diff_states.py   -> MUST be EMPTY

THE DUMP IS DELIBERATELY DUMB
=============================
Agent Action Plan section 0.6.6 establishes why one `ORDER BY` on one
column is sufficient, verbatim:

    "All 22 in-scope tables have a single-column primary key and zero
    secondary indexes, and none contains a `TIMESTAMP` column, an
    `AUTO_INCREMENT` column, or a column-level `DEFAULT` ... Consequently
    the dump is `SELECT * FROM <table> ORDER BY <primary key>` with no
    tie-breaking logic, no timestamp masking and no surrogate-key
    remapping needed."

Every clause of that was re-verified against `mysql/ACASDB.sql` and
against a live `information_schema` before this module was written. So:

  * NO `ORDER BY` beyond the single primary-key column. No secondary
    sort, no `ORDER BY 1,2,3`, no row-hash tie-break.
  * NO timestamp masking - there are zero temporal columns in scope.
  * NO surrogate-key remapping - the schema's only `AUTO_INCREMENT`
    column is `STOCKAUDIT-REC`.`AUDIT-ID`, and that table is out of
    scope.
  * NO client-side re-sorting. Rows arrive primary-key-ordered from SQL
    and are written in that order, untouched.

The schema's only composite primary key, only `UNIQUE` constraint and
only `FOREIGN KEY` all belong to `PLPAY-RECrg01`, and its only secondary
indexes are three `KEY` clauses on `STOCK-REC` plus one on
`PLPAY-RECrg01`. Both tables are out of scope, which is why nothing in
scope needs special handling. `harness/reset_db.sh` asserts the same
invariant from the other side and says so at [harness/reset_db.sh:L301]
and [harness/reset_db.sh:L1751].

Every cleverness added here would be a place where a real behavioural
difference could hide. Agent Action Plan section 0.6.6 states the
guarantee that dumbness buys: "a non-empty diff is always a real
behavioral difference and never an artefact of the comparison."

THE ONE PLACE THE PROSE AND THE FROZEN SCHEMA DISAGREE
======================================================
The frozen artifact wins, always. Section 0.6.6's clause "none contains
... a column-level `DEFAULT`" is not quite true of the schema it
describes. There is exactly one, and it is in scope:

    [mysql/ACASDB.sql:L1219]   `PASS-WORD` char(4) NOT NULL DEFAULT '',

Confirmed to be the only one: over all thirty-three tables and seven
hundred and twenty columns, `information_schema.COLUMNS` returns exactly
one row with `COLUMN_DEFAULT IS NOT NULL`, and it is
`SYSTEM-REC`.`PASS-WORD`.

It changes nothing here. A column default applies only to an `INSERT`
that omits the column, and this module issues `SELECT` only, so section
0.6.6's determinism guarantee stands untouched. Rather than drop the
check or let it fail against the real schema, `KNOWN_COLUMN_DEFAULTS`
records this one verified default as a cited allowance and
`assert_table_structure` aborts on any OTHER column-level default. The
tripwire on frozen-schema tampering is kept; the false alarm is not.

FAITHFUL CAPTURE, NOT NORMALISATION
===================================
This module has zero canonicalisation jobs. `harness/normalize.py` has
exactly three: trailing spaces in fixed-width character columns, decimal
scale rendering, and the two-digit versus four-digit date text forms.
The split is deliberate and it is load-bearing.

Agent Action Plan section 0.6.2's width drift, verified end to end:

    [copybooks/wsledger.cob:L27]  03  Ledger-Name pic x(24).       24
    [common/nominalMT.cbl:L299]   HV-LEDGER-NAME PIC X(32).        32
    [mysql/ACASDB.sql:L127]       `LEDGER-NAME` char(32) NOT NULL, 32

And the bridge TRIMS TRAILING SPACES as it builds the SQL text, so the
COBOL side stores character columns trimmed while a Python data-access
layer writing padded values could store them padded:

    [common/nominalMT.cbl:L1065-L1067]
        STRING '`LEDGER-NAME`="' INTO WS-MYSQL-COMMAND ...
        STRING FUNCTION TRIM (HV-LEDGER-NAME,TRAILING) ...

That is not one stray call: `common/nominalMT.cbl` carries twenty-three
`FUNCTION TRIM` sites and `common/glpostingMT.cbl` twenty-nine. Whether
the difference is even observable then depends on the server's
`PAD_CHAR_TO_FULL_LENGTH` mode, which `harness/Dockerfile.mariadb`
deliberately leaves unset for exactly this reason.

So: capture what the driver returns, byte for byte, and let
`normalize.py` canonicalise. Trimming or padding here would hide a real
behavioural difference behind a helpful-looking transformation.

FACTS `harness/normalize.py` NEEDS, RECORDED HERE SO THE PAIR AGREES
===================================================================
  * FIXED-WIDTH COLUMNS. The schema declares 238 `char(...)` columns and
    ZERO `varchar(...)`; 177 of those 238 are in scope. In-scope width
    census: 79 x char(1), 12 x char(2), 6 x char(3), 5 x char(4),
    3 x char(5), 2 x char(6), 6 x char(7), 5 x char(8), 10 x char(10),
    1 x char(11), 4 x char(12), 6 x char(13), 1 x char(14),
    2 x char(15), 1 x char(16), 1 x char(18), 12 x char(24),
    5 x char(30), 10 x char(32), 3 x char(48), 1 x char(64),
    2 x char(96).
  * DECIMAL SCALE IS NOT UNIFORMLY 2. The schema carries 167 `DECIMAL`
    columns, 128 in scope, and the in-scope scales are: 55 x
    decimal(10,2), 44 x decimal(9,2), 15 x decimal(4,2), 8 x
    decimal(5,2), 4 x decimal(14,2), 1 x decimal(6,2) and 1 x
    decimal(5,0). Out of scope there are also `,4` scales. NEVER
    hard-code two places.
  * `char(8)` DOES NOT MEAN "DATE". The in-scope char(8) columns are
    `GLPOSTING-REC`.`POST-DAT`, `IRSPOSTING-REC`.`POST4-DAT` and
    `PSIRSPOST-REC`.`IRS-POST-DAT`, which are date text - but ALSO
    `PUITM5-REC`.`OI5-BATCH` and `SAITM3-REC`.`OI3-BATCH`, which are
    batch references. Any date handling in `normalize.py` must be driven
    by an explicit COLUMN ALLOW-LIST, never by a width or content
    heuristic.
  * NO EXTRA FILES IN THE OUTPUT DIRECTORY. `normalize.py` is invoked as
    `--in /out/cobol --out /out/cobol.norm`
    [harness/docker-compose.yml:L269], so it reads a directory. This
    module writes ONLY `<TABLE>.json` files there - no manifest, no log,
    no marker. Progress goes to stderr.

THE OUTPUT CONTRACT
===================
One file per table, named for the table exactly as the schema spells it,
hyphens included, for example `GLPOSTING-REC.json`. The object carries
five keys, in this insertion order and no others:

    {
      "table": "GLLEDGER-REC",
      "primary_key": "LEDGER-KEY",
      "columns": ["LEDGER-KEY", "LEDGER-TYPE", ... ],
      "row_count": 2,
      "rows": [
        [1, 1, "B", 1, "Sales Ledger Control", "1234.56", ... ],
        [2, 1, "B", 1, "VAT Control", "-99.99", ... ]
      ]
    }

  * `columns` is in schema ordinal order, taken from the cursor
    description of `SELECT *` and cross-checked against
    `information_schema`. It is never sorted.
  * `rows` is a list of lists in the order SQL returned them, which is
    primary-key ascending. Values are positionally aligned with
    `columns`.
  * `DECIMAL` becomes a canonical JSON STRING with the column's declared
    scale intact, rendered with `format(value, "f")` so exponent
    notation can never appear. Trailing zeros are NOT stripped here.
  * integers become JSON integers; `CHAR` becomes a JSON string exactly
    as the driver returned it, unpadded and untrimmed.
  * `row_count` is derived and asserted equal to `len(rows)`.
  * NO other key. No timestamp, no server version, no connection detail,
    no scenario name, no side - the file's PATH carries the scenario and
    the side.

TWO ACCEPTED OUTPUT LAYOUTS, BOTH FROM THE REPOSITORY'S OWN DOCUMENTATION
========================================================================
    <out-dir>/<scenario>/<side>/<TABLE>.json    --scenario NAME --side S
    <out>/<TABLE>.json                          --out DIR

The first is the layout the file specification for this module defines,
with `side` one of `cobol` or `python`. The second is the invocation the
committed Compose file publishes verbatim as the canonical eight-stage
recipe, `harness/dump_tables.py --out /out/cobol`
[harness/docker-compose.yml:L268]. Both are supported because both are
documented in this repository, and neither is a guess. `--out` names the
directory the `<TABLE>.json` files are written into directly; `--out-dir`
names the root under which `<scenario>/<side>/` is composed.

CONNECTION POLICY
=================
Credentials come from the environment `harness/docker-compose.yml`
already defines for the `gnucobol` service [L680-L685]: `ACAS_DB_HOST`,
`ACAS_DB_PORT`, `ACAS_DB_NAME`, `ACAS_DB_USER`, `ACAS_DB_PASSWORD` and
`ACAS_DB_SOCKET` (declared, and legitimately empty). They are never
logged, never echoed, never persisted and never allowed to influence a
single output byte; `ConnectionSettings.__repr__` redacts the password.

Widths are enforced because the COBOL side cannot carry more. The
`RDB-Data` group at [copybooks/wsfnctn.cob:L56-L62] declares
`DB-Schema pic x(12)`, `DB-UName pic x(12)`, `DB-UPass pic x(12)`,
`DB-Host pic x(32)`, `DB-Socket pic x(64)` and `DB-Port pic x(5)`. A
credential the bridge cannot hold would make the two sides connect as
different users, and two dumps taken as different users are not
comparable.

NO SESSION STATE IS SET. `harness/Dockerfile.mariadb` sets autocommit
off at SERVER level precisely so that every client inherits it
identically - the COBOL loaders, the bridges through `cobmysqlapi.o`,
the `mariadb` client in `seed.sh` and `reset_db.sh`, and the Python
driver here - and warns that a per-session setting "would let one side
of the diff differ from the other". This module therefore sets no
`autocommit`, no `sql_mode`, no `charset`, no collation and no
`PAD_CHAR_TO_FULL_LENGTH`: it reads the server as configured. Being
`SELECT`-only, the autocommit value cannot affect its output either way.
One consequence is worth having: with autocommit off the first `SELECT`
opens a read-only transaction, and under `REPEATABLE READ` all
twenty-two tables are then read from ONE consistent snapshot. The
transaction is released with a write-free `rollback()`, never a commit.

THE RULES CITED BELOW BY NUMBER
==============================
This project ships NO separate rules document - `review_rules` reports
"No user rules provided.", confirmed by a full read. The six binding
rules R-1 to R-6 are the Agent Action Plan's own, section 0.7.2, and
each section below names the one it satisfies. Where the plan is silent,
ordinary enterprise practice applies; nothing here is invented.

NUMERIC POLICY  (rule R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport. Agent
Action Plan section 0.5.1 extends the prohibition to this exact file,
verbatim: "No `pandas` and no `numpy` - both compute in binary floating
point by default, which is prohibited outright for accounting
computation. This exclusion is absolute, including for the harness dump
comparison, which uses ordered row sequences rather than dataframes."

So, structurally:

  * `pandas` and `numpy` are not imported here, for any reason. Neither
    is in `requirements.txt`, and `harness/Dockerfile.gnucobol` fails
    its own build if either is importable.
  * `float(...)` is never called on a database value, and no value is
    allowed to reach `float` by inference.
  * A `DECIMAL` is NEVER serialised as a JSON number. JSON numbers are
    IEEE-754 doubles in every consumer, so `"1234.56"` is written as
    text. Integers are written as JSON integers, which are exact for
    every integer width the schema uses - the widest in scope is
    `bigint(11)`, comfortably inside a 64-bit integer.
  * `render_value` DISPATCHES ON TYPE AND RAISES on anything unexpected
    rather than coercing it. A `float` raises `NumericPolicyError`
    naming the table, the column and the value; so does a non-finite
    `Decimal`. A `bool` raises too, because JSON `true` is not the
    integer the column holds. Silently rounding any of these would
    destroy the exactness the whole engagement rests on.
  * `assert_table_structure` additionally refuses a table carrying a
    `float`, `double` or `real` column, so the guard is structural as
    well as per value.

The schema supports all of this: it declares ZERO `FLOAT`, `DOUBLE` and
`REAL` columns. Its numeric census is 167 `DECIMAL`, 151 `INT`, 116
`TINYINT`, 23 `MEDIUMINT`, 22 `SMALLINT` and 3 `BIGINT`; in scope, 128
`DECIMAL`, 65 `INT`, 99 `TINYINT`, 21 `MEDIUMINT`, 20 `SMALLINT` and 3
`BIGINT`. The pinned driver `mysql-connector-python==26.7.0` was
measured against the live schema and hands `DECIMAL` back as
`decimal.Decimal` with the declared scale intact - `decimal(14,4)`
arrives as `Decimal("0.0000")` - and every integer width back as `int`.

NO COBOL AT RUNTIME, AND NO COUPLING TO THE SHIPPED PACKAGE  (rule R-1)
======================================================================
`harness/` is the compiled-COBOL oracle tree and a SIBLING of
`acas_posting/`. Agent Action Plan section 0.3.1 annotates it "the
compiled oracle; NEVER on the package import path" and states the
guarantee: "there is no import path from `acas_posting` to `harness`,
and the shipped artifact carries no COBOL, no `cobc` requirement and no
linkage to the bridge's C interface object."

  * THERE IS NO `harness/__init__.py` AND THERE MUST NEVER BE ONE. This
    is a plain module invoked BY PATH, and it is on `sys.path` only for
    the duration of its own run.
  * `acas_posting` is NOT imported here, in any form - not `dal`, not
    `records`, not `dictionary`. This module imports cleanly on a host
    where `acas_posting` is not installed at all, which is exactly the
    situation inside `harness/Dockerfile.gnucobol`.
  * No COBOL is invoked, no `cobc` is shelled out to, no compiled module
    is loaded and no child process is started.
  * Imports are confined to the standard library, `PyYAML` and the
    database driver, which is the permission Agent Action Plan section
    0.4.3 grants `harness/*`. The driver is imported LAZILY inside
    `connect`, so the pure functions - `render_value`, `write_dump`,
    `dump_path`, `_ident` - are usable, and unit-testable, with no
    driver installed and no database reachable.
  * `jsonschema` is not imported: it is not in `requirements.txt`.

NO SCHEMA CHANGE, STRICTLY SEQUENTIAL  (rule R-3)
=================================================
Agent Action Plan section 0.2.2 forbids "new tables, columns, indexes,
constraints, views, triggers or DDL statements" and any concurrency: "No
threads, no `asyncio`, no `multiprocessing`, no connection pooling.
Execution is strictly sequential."

  * This module issues `SELECT` only, against the twenty-two in-scope
    tables and against `information_schema`. It emits no `INSERT`,
    `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER` or `TRUNCATE`, creates
    no temporary table or view, and runs no `ANALYZE TABLE`. The single
    transaction-control statement it issues is a write-free `rollback()`
    that releases the read-only snapshot.
  * ONE connection, no pool. Tables are dumped one after another in a
    plain loop. There is no thread, no event loop, no process pool and
    no synchronisation primitive anywhere in this file.
  * It writes nothing under `$ACAS_REPO`, which the Compose file mounts
    read-only [harness/docker-compose.yml:L591] to keep the frozen
    artifact guarantee of section 0.8.1 structural.
  * It adds no validation of the DATA. The structural assertions check
    the SCHEMA - shape, keys, types - never a row's contents.

ANOMALIES ARE REPRODUCED, NEVER REPAIRED  (rule R-4)
====================================================
Agent Action Plan section 0.8.2, preserving the user's own requirement:
"A defect reproduced is correct; a defect fixed is a failure."

For a dump that means: DUMP WHAT IS THERE. The clearest case is the
plan's anomaly 7. `IRSPOSTING-REC` carries three columns that exist in
NO copybook - `POST4-DAY`, `POST4-MONTH` and `POST4-YEAR` - because the
bridge derives them from two-character slices of a date string under a
guard [common/irspostingMT.cbl:L982-L987]. When the guard does not hold
the slices are simply not moved, so the components keep the zero left by
the group `INITIALIZE` while `POST4-DAT` still holds the raw date text.
The row is internally inconsistent, and that is the specification.

Nothing here derives, back-fills, cross-checks or "repairs" those three
columns, and nothing rounds, re-scales, trims, pads or reformats any
other value. `render_value` is a type dispatch, not a transformation.

TRACEABILITY  (rule R-5)
========================
Every table, primary key and column count in `IN_SCOPE` is traceable to
`mysql/ACASDB.sql` and carries the `CREATE TABLE` line it was read from.
The same twenty-two triples appear independently in
[harness/reset_db.sh:L248-L271] and the same eleven out-of-scope names in
[harness/reset_db.sh:L276-L288]; the two were checked against each other
and against the schema.

The map cannot silently drift, because `assert_table_structure`
cross-checks it against `information_schema` on every run and aborts on
any disagreement, and because the column names taken from the cursor
description are compared with the ordinal order `information_schema`
reports.

DETERMINISM IS THE PRODUCT  (rule R-6)
======================================
Agent Action Plan section 0.8.5: "Two runs of the same scenario under the
same pinned clock produce byte-identical dumps, proven by
`tests/determinism/test_two_runs_byte_identical.py`."

NOT ONE BYTE OF NON-REPRODUCIBLE CONTENT MAY APPEAR IN A DUMP FILE.
There is no wall-clock timestamp, no hostname, no run identifier, no
elapsed time, no absolute path, no process id, no driver version, no
server version and no random ordering in the output - this module reads
no clock, no entropy source and no distribution metadata, and lists no
directory. Provenance, when wanted, belongs in a log outside the dump
tree.

Serialisation is pinned rather than left to a default: `indent=2`,
`ensure_ascii=True`, `sort_keys=False`, `separators=(",", ": ")`, LF
newlines, UTF-8, exactly one trailing newline, and the five keys always
in the same insertion order. `ensure_ascii=True` is deliberate - it
makes the bytes independent of any locale or filesystem-encoding
difference between the two runs, so do not "improve" it. Each file is
written to a temporary name in its own directory and moved into place
with `os.replace`, so a partial write can never be compared.

THE PUBLIC API
==============
`tests/conftest.py` is specified to provide "the seed/dump/normalize/diff
helpers so that no test reimplements the comparison protocol" (Agent
Action Plan section 0.4.3), which means it imports this module and calls
these functions directly. They are a library first and a command second.

    connect                    context manager over one read-only
                               connection, from the ACAS_DB_* environment
    connection_settings        the resolved settings, password redacted
    dump_table                 the dump object for one table
    dump_tables                the dump objects for many, sequentially
    write_dump / write_dumps   the deterministic serialiser
    dump_path                  either accepted output layout
    render_value               the value dispatch, on its own for testing
    assert_table_structure     the seven structural assertions
    resolve_tables             the table list, from the CLI selectors
    scenario_tables            the affected-table list from a scenario
    table_spec                 one table's frozen-schema facts
    build_parser / main        the command line; `main` RETURNS a code

`main` returns an exit status and never calls `sys.exit`, so a caller can
drive it in-process. The module guard raises `SystemExit(main())`.

EXIT CODES
==========
    0   every requested table was dumped and written
    80  usage - bad or contradictory command line
    81  precondition - environment or output directory
    82  database - unreachable, or credentials rejected
    83  scope - an out-of-scope or unknown table was requested
    84  drift - a structural assertion against the frozen schema failed
    85  numeric - the R-2 value guard tripped, or a NULL was fetched
    86  write - a dump file could not be written

FURTHER READING
===============
    mysql/ACASDB.sql                 the frozen schema; the source of the
                                     table, key and column inventory
    harness/docker-compose.yml       the eight stages and the environment
    harness/reset_db.sh              the same invariants, asserted from
                                     the database side
    harness/normalize.py             the three canonicalisation jobs
    harness/diff_states.py           the comparison; empty is the pass
    docs/migration/anomaly-log.md    the reproduced defects
    docs/migration/scenario-diff-evidence.md   the per-scenario evidence
"""

# PROVENANCE
# Every fact this module encodes comes from the frozen schema
# mysql/ACASDB.sql, the maintainer's own one-way COBOL-to-MySQL bridge
# (common/*MT.scb and common/*MT.cbl) and the record copybooks under
# copybooks/. Those trees are the specification for this migration and are
# never modified, reformatted, commented, relocated or built from here.
# Nothing below opens one of them: the locators are citations for a reader,
# which is what rule R-5 asks for.

from __future__ import annotations

import argparse
import difflib
import json
import os
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

# ---------------------------------------------------------------------------
#  THE FROZEN-SCHEMA INVENTORY  (rule R-5)
#
#  One entry per in-scope table: its single-column primary key, its declared
#  column count and the `CREATE TABLE` line of mysql/ACASDB.sql it was read
#  from. The same twenty-two triples appear independently at
#  [harness/reset_db.sh:L248-L271]; both were verified against the schema and
#  against a live information_schema, and `assert_table_structure` re-checks
#  every entry on every run so the map cannot silently drift.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TableSpec:
    """One in-scope table's frozen-schema facts.

    Attributes:
        primary_key: The single column the dump orders by. Agent Action
            Plan section 0.6.6 establishes that every in-scope table has
            exactly one, which is why no tie-break is needed.
        column_count: The declared number of columns, asserted before any
            row is read. A cheap, strong tripwire on schema tampering.
        schema_line: The `CREATE TABLE` line in `mysql/ACASDB.sql`, so a
            reader can go straight to the declaration.
    """

    primary_key: str
    column_count: int
    schema_line: int


IN_SCOPE: Final[Mapping[str, TableSpec]] = {
    "ANALYSIS-REC": TableSpec("PA-CODE", 4, 31),
    "GLBATCH-REC": TableSpec("BATCH-KEY", 21, 80),
    "GLLEDGER-REC": TableSpec("LEDGER-KEY", 11, 122),
    "GLPOSTING-REC": TableSpec("POST-RRN", 14, 154),
    "IRSDFLT-REC": TableSpec("DEF-REC-KEY", 4, 189),
    "IRSFINAL-REC": TableSpec("IRS-FINAL-ACC-REC-KEY", 3, 214),
    "IRSNL-REC": TableSpec("KEY-1", 15, 238),
    "IRSPOSTING-REC": TableSpec("KEY-4", 13, 274),
    "PSIRSPOST-REC": TableSpec("IRS-POST-KEY", 10, 366),
    "PUINV-LINES-REC": TableSpec("IL-LINE-KEY", 14, 510),
    "PUINVOICE-REC": TableSpec("PINVOICE-KEY", 30, 545),
    "PUITM5-REC": TableSpec("OI5-KEY", 29, 596),
    "PULEDGER-REC": TableSpec("PURCH-KEY", 29, 646),
    "SAINV-LINES-REC": TableSpec("IL-LINE-KEY", 14, 809),
    "SAINVOICE-REC": TableSpec("SINVOICE-KEY", 31, 844),
    "SAITM3-REC": TableSpec("OI3-KEY", 28, 896),
    "SALEDGER-REC": TableSpec("SALES-KEY", 37, 945),
    "SYSDEFLT-REC": TableSpec("DEF-REC-KEY", 4, 1138),
    "SYSFINAL-REC": TableSpec("FINAL-ACC-REC-KEY", 2, 1163),
    "SYSTEM-REC": TableSpec("SYSTEM-REC-KEY", 169, 1186),
    "SYSTOT-REC": TableSpec("LEDGER-TOTALS-REC-KEY", 21, 1376),
    "VALUEANAL-REC": TableSpec("VA-CODE", 10, 1418),
}

# The eleven tables the posting cycle never touches, listed by NAME so a
# wrong request is refused with an explanation rather than with a
# not-found. Agent Action Plan section 0.2.2 enumerates them as
# "Eleven out-of-scope tables, all present in the frozen schema but never
# touched by the cycle". 22 + 11 = 33, the schema's full CREATE TABLE
# count. The same list is at [harness/reset_db.sh:L276-L288].
OUT_OF_SCOPE: Final[frozenset[str]] = frozenset(
    {
        "DELIVERY-REC",
        "PLPAY-REC",
        "PLPAY-RECrg01",
        "PUAUTOGEN-LINES-REC",
        "PUAUTOGEN-REC",
        "PUDELINV-REC",
        "SAAUTOGEN-LINES-REC",
        "SAAUTOGEN-REC",
        "SADELINV-REC",
        "STOCK-REC",
        "STOCKAUDIT-REC",
    }
)

# Deterministic iteration order for `--all-in-scope` and for the default
# selection: the table names, ascending. Sorted ONCE here, never per run,
# and never applied to rows (rule R-6 - rows keep SQL's order).
IN_SCOPE_TABLES: Final[tuple[str, ...]] = tuple(sorted(IN_SCOPE))

# 513, verified by summing the twenty-two declared column counts and again
# by counting them in mysql/ACASDB.sql. Exposed so a test can assert the
# whole inventory in one line.
EXPECTED_TOTAL_COLUMNS: Final[int] = sum(
    spec.column_count for spec in IN_SCOPE.values()
)

# The two sides of the comparison; the dump's path, never its content,
# records which one it is.
SIDES: Final[tuple[str, ...]] = ("cobol", "python")

# The dump object's key order. Fixed, and asserted by `write_dump` before
# anything is serialised (rule R-6).
DUMP_KEYS: Final[tuple[str, ...]] = (
    "table",
    "primary_key",
    "columns",
    "row_count",
    "rows",
)

# THE ONE COLUMN-LEVEL DEFAULT IN THE FROZEN SCHEMA.
#
#     [mysql/ACASDB.sql:L1219]  `PASS-WORD` char(4) NOT NULL DEFAULT '',
#
# Agent Action Plan section 0.6.6 says the in-scope tables carry none. The
# schema disagrees exactly once, and the frozen artifact wins. It is
# harmless here - a default applies only to an INSERT that omits the
# column, and this module issues SELECT only - so it is recorded as an
# allowance rather than removed as a check: `assert_table_structure`
# aborts on any OTHER column-level default, keeping the tamper tripwire
# without raising a false alarm against the real schema.
#
# The value is the rendering `information_schema.COLUMN_DEFAULT` returns,
# measured on MariaDB 10.11.7: the two-character string `''`. The empty
# string is accepted alongside it because other client or server versions
# render the same declaration that way.
KNOWN_COLUMN_DEFAULTS: Final[Mapping[tuple[str, str], frozenset[str]]] = {
    ("SYSTEM-REC", "PASS-WORD"): frozenset({"''", ""}),
}

# Column types that would break the determinism argument of Agent Action
# Plan section 0.6.6 - a temporal type could carry a wall-clock value into
# a dump - or the numeric policy of rule R-2. Verified absent from all
# twenty-two in-scope tables; asserted rather than trusted.
_FORBIDDEN_FLOAT_TYPES: Final[frozenset[str]] = frozenset(
    {"float", "double", "real"}
)
_FORBIDDEN_TEMPORAL_TYPES: Final[frozenset[str]] = frozenset(
    {"timestamp", "datetime", "date", "time", "year"}
)

# `information_schema.COLUMNS.EXTRA` substrings that would each defeat a
# clause of section 0.6.6. Verified: over all 720 columns of ACASDB the
# only non-empty EXTRA is `auto_increment` on `STOCKAUDIT-REC`.`AUDIT-ID`,
# and that table is out of scope. Matched as substrings, lower-cased, so
# only these three concerns abort - an unrelated future EXTRA value is
# reported, not fatal.
_FORBIDDEN_EXTRA_MARKERS: Final[tuple[str, ...]] = (
    "auto_increment",
    "generated",
    "on update",
)

# Exit codes. Documented in the module docstring and in the CLI epilogue,
# and deliberately in the same 80+ band the sibling harness scripts use so
# an operator reading a pipeline log sees one family.
EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 80
EX_PRECONDITION: Final[int] = 81
EX_DATABASE: Final[int] = 82
EX_SCOPE: Final[int] = 83
EX_DRIFT: Final[int] = 84
EX_NUMERIC: Final[int] = 85
EX_WRITE: Final[int] = 86

# The environment variables `harness/docker-compose.yml` defines for the
# `gnucobol` service [L680-L685]. The first five must be non-empty, which
# is the same requirement [harness/reset_db.sh:L335-L341] states;
# ACAS_DB_SOCKET is declared and legitimately empty (the service sets
# `ACAS_DB_SOCKET: ""`), meaning "connect over TCP".
_ENV_HOST: Final[str] = "ACAS_DB_HOST"
_ENV_PORT: Final[str] = "ACAS_DB_PORT"
_ENV_NAME: Final[str] = "ACAS_DB_NAME"
_ENV_USER: Final[str] = "ACAS_DB_USER"
_ENV_PASSWORD: Final[str] = "ACAS_DB_PASSWORD"
_ENV_SOCKET: Final[str] = "ACAS_DB_SOCKET"
_ENV_OUT: Final[str] = "ACAS_OUT"

# Field widths from the `RDB-Data` group at [copybooks/wsfnctn.cob:L56-L62].
# The COBOL side cannot carry a longer value, so a longer one here would
# make the two sides connect differently and their dumps incomparable.
_RDB_WIDTHS: Final[Mapping[str, int]] = {
    _ENV_NAME: 12,
    _ENV_USER: 12,
    _ENV_PASSWORD: 12,
    _ENV_HOST: 32,
    _ENV_SOCKET: 64,
    _ENV_PORT: 5,
}

# How many near-miss names an unknown-table message offers.
_SUGGESTION_LIMIT: Final[int] = 4

# The scenario key this module reads. Agent Action Plan section 0.4.1.7
# specifies each `harness/scenarios/*.yaml` carries "Seed data, inputs and
# the affected-table list per scenario"; these are the two spellings of
# that list, the underscored form and the hyphenated form the repository
# uses for every COBOL and SQL identifier. Both mean the same thing and
# only one may appear.
_SCENARIO_TABLE_KEYS: Final[tuple[str, ...]] = (
    "affected_tables",
    "affected-tables",
)


# ---------------------------------------------------------------------------
#  PROGRESS REPORTING
#
#  Stderr, and never stdout, so nothing this module says can be mistaken
#  for data; and never into the output directory, so nothing it says can
#  reach a dump file (rule R-6). No line carries a clock reading, a host
#  name, a process id or an elapsed time.
# ---------------------------------------------------------------------------

# Set once by `main` from --quiet. A module-level flag rather than a
# parameter threaded through every function, because there is exactly one
# process, one connection and one run (rule R-3, strictly sequential).
_QUIET: bool = False


def _progress(message: str) -> None:
    """Write one progress line to stderr, unless `--quiet` was given.

    Args:
        message: The line to write.
    """
    if _QUIET:
        return
    print(message, file=sys.stderr)


# ---------------------------------------------------------------------------
#  ERRORS
#
#  One root, so a caller can catch everything this module raises with a
#  single clause, and one subclass per distinct cause so a caller that
#  cares can tell them apart. Each also subclasses the builtin a caller
#  would naturally expect, which is the convention the sibling package
#  follows (see acas_posting/dictionary/loader.py).
#
#  Every message names the table, and where relevant the column and the
#  value, because a message that does not is a message an operator cannot
#  act on. No message ever contains a credential.
# ---------------------------------------------------------------------------


class DumpError(Exception):
    """Base class for every error this module raises."""


class UnknownTableError(DumpError, ValueError):
    """A requested name is not a table of the frozen schema at all."""


class TableNotInScopeError(DumpError, ValueError):
    """A requested table exists but the posting cycle never touches it.

    Agent Action Plan section 0.2.2 lists the eleven, and refusing them by
    name - rather than dumping them, or failing to find them - is what
    keeps a comparison bounded by the cycle actually being migrated.
    """


class SchemaDriftError(DumpError, RuntimeError):
    """The live schema does not match the frozen schema's declaration.

    Either `mysql/ACASDB.sql` was modified, which Agent Action Plan
    section 0.8.1 calls "a defect in the migration, regardless of how
    harmless it appears", or `IN_SCOPE` is wrong. Both stop the run.
    """


class NumericPolicyError(DumpError, TypeError):
    """A value would have to pass through binary floating point (rule R-2).

    Raised, never coerced. A `float` arriving here means the driver was
    configured wrongly, and silently rounding it would destroy the
    exactness the whole engagement rests on.
    """


class UnexpectedValueTypeError(DumpError, TypeError):
    """The driver returned a type no in-scope column can hold."""


class UnexpectedNullError(DumpError, ValueError):
    """A NULL was fetched from a schema that declares every column NOT NULL.

    Agent Action Plan section 0.6.2 explains why one cannot legitimately
    appear: each bridge load paragraph initialises the host-variable group
    first, "so unset fields become zero or space rather than SQL `NULL`".
    A NULL is therefore genuinely new information and is reported, not
    quietly rendered.
    """


class ConnectionConfigError(DumpError, RuntimeError):
    """The ACAS_DB_* environment is missing, malformed or out of range."""


class DriverUnavailableError(DumpError, RuntimeError):
    """The pinned database driver is not importable."""


class DumpWriteError(DumpError, OSError):
    """A dump file could not be written or moved into place."""


class ScenarioFileError(DumpError, ValueError):
    """A scenario definition does not carry a usable affected-table list."""


# ---------------------------------------------------------------------------
#  IDENTIFIER SAFETY
#
#  EVERY identifier in this schema is HYPHENATED - `ANALYSIS-REC`,
#  `LEDGER-NAME`, `IRS-POST-KEY`, `POST4-DAT` - so every one must be
#  backtick-quoted in every statement. Unquoted, `SELECT * FROM
#  ANALYSIS-REC` parses as a subtraction and fails.
#
#  Only two identifiers are ever interpolated into SQL here: a table name
#  and its primary-key column. Both are resolved through the allow-list
#  below FIRST, so no caller-supplied text ever reaches a statement.
#  Everything else - schema name, table name in the information_schema
#  lookups - is passed as a bound parameter.
# ---------------------------------------------------------------------------


# The primary-key columns, collected once. Kept separate from the table
# names so that `_ident` cannot be talked into quoting an arbitrary column.
_ALLOWED_KEY_COLUMNS: Final[frozenset[str]] = frozenset(
    spec.primary_key for spec in IN_SCOPE.values()
)


def table_spec(table: str) -> TableSpec:
    """Return the frozen-schema facts for `table`, or refuse the name.

    Args:
        table: A table name, spelled exactly as `mysql/ACASDB.sql`
            spells it, hyphens included and case-sensitive.

    Returns:
        The `TableSpec` recorded for that table.

    Raises:
        TableNotInScopeError: `table` is one of the eleven the posting
            cycle never touches (Agent Action Plan section 0.2.2).
        UnknownTableError: `table` is not a table of the frozen schema,
            or is not a string. The message offers near-miss names.
    """
    if not isinstance(table, str):
        raise UnknownTableError(
            f"a table name must be a string; got {type(table).__name__}."
        )

    spec = IN_SCOPE.get(table)
    if spec is not None:
        return spec

    if table in OUT_OF_SCOPE:
        raise TableNotInScopeError(
            f"{table!r} is one of the eleven tables the ACAS posting cycle "
            f"never touches, so it is never dumped: "
            f"{', '.join(sorted(OUT_OF_SCOPE))}. Agent Action Plan section "
            f"0.2.2 lists them as out of scope; dumping one would compare "
            f"state the migration does not produce. In scope are the "
            f"{len(IN_SCOPE)} tables listed in section 0.6.6."
        )

    suggestions = difflib.get_close_matches(
        table, IN_SCOPE_TABLES, n=_SUGGESTION_LIMIT, cutoff=0.6
    )
    hint = f" Did you mean {', '.join(suggestions)}?" if suggestions else ""
    raise UnknownTableError(
        f"{table!r} is not a table of the frozen schema mysql/ACASDB.sql, "
        f"which declares 33: the {len(IN_SCOPE)} in scope and the "
        f"{len(OUT_OF_SCOPE)} out of scope. Names are case-sensitive and "
        f"hyphenated exactly as the schema spells them.{hint}"
    )


def _ident(name: str) -> str:
    """Validate an identifier against the allow-list and backtick-quote it.

    The allow-list is the twenty-two in-scope table names together with
    their primary-key columns - the only identifiers this module ever
    places in a statement. Anything else is refused before it can reach
    SQL, which is why no quoting or escaping of arbitrary text is needed
    and none is offered.

    Args:
        name: The identifier to quote.

    Returns:
        The identifier wrapped in backticks, ready to interpolate.

    Raises:
        TableNotInScopeError: `name` is an out-of-scope table.
        UnknownTableError: `name` is not on the allow-list at all, or is
            not a string.
    """
    if not isinstance(name, str):
        raise UnknownTableError(
            f"an identifier must be a string; got {type(name).__name__}."
        )

    if name in IN_SCOPE or name in _ALLOWED_KEY_COLUMNS:
        return f"`{name}`"

    # Not on the allow-list. `table_spec` produces the right refusal for
    # an out-of-scope table and the right suggestions for a typo, and it
    # raises in every remaining case, so it is the whole error path.
    table_spec(name)
    raise UnknownTableError(  # pragma: no cover - unreachable by design
        f"{name!r} is not an identifier this module may place in a "
        f"statement."
    )


# ---------------------------------------------------------------------------
#  THE CONNECTION  (rules R-1, R-3, R-6)
#
#  ONE connection, read-only, no pool, strictly sequential. No session
#  state is set: harness/Dockerfile.mariadb configures autocommit at
#  SERVER level so that every client inherits it identically and warns
#  that a per-session setting "would let one side of the diff differ from
#  the other". Nothing here sets autocommit, sql_mode, charset, collation
#  or PAD_CHAR_TO_FULL_LENGTH.
#
#  The driver is imported LAZILY so that the pure functions of this module
#  - render_value, write_dump, dump_path, _ident, table_spec - import and
#  test with no driver installed and no database reachable.
# ---------------------------------------------------------------------------

_REDACTED: Final[str] = "***redacted***"


@dataclass(frozen=True, slots=True)
class ConnectionSettings:
    """Where to connect, resolved from the environment.

    A value object, deliberately without a `dsn` or `url` accessor: a
    connection string is the classic way a password reaches a log file.
    `__repr__` and `__str__` both redact the password, so the object is
    safe to interpolate into a diagnostic.

    Attributes:
        host: `ACAS_DB_HOST`; `mariadb` inside the Compose network.
        port: `ACAS_DB_PORT` as an integer; 3306 in the Compose service.
        database: `ACAS_DB_NAME`; `ACASDB`.
        user: `ACAS_DB_USER`.
        password: `ACAS_DB_PASSWORD`. Never logged, never persisted,
            never allowed to influence an output byte.
        socket: `ACAS_DB_SOCKET`, empty for TCP. The Compose service sets
            it empty explicitly [harness/docker-compose.yml:L685].
    """

    host: str
    port: int
    database: str
    user: str
    password: str
    socket: str

    def __repr__(self) -> str:
        """Return a representation with the password redacted."""
        return (
            f"{type(self).__name__}(host={self.host!r}, port={self.port!r}, "
            f"database={self.database!r}, user={self.user!r}, "
            f"password={_REDACTED!r}, socket={self.socket!r})"
        )

    __str__ = __repr__


def connection_settings(
    env: Mapping[str, str] | None = None,
) -> ConnectionSettings:
    """Resolve the ACAS_DB_* environment into connection settings.

    Args:
        env: The mapping to read; `os.environ` when omitted. Passing one
            explicitly is how a test drives this without touching the
            process environment.

    Returns:
        The resolved settings, with the password redacted in `repr`.

    Raises:
        ConnectionConfigError: A required variable is missing or empty, the
            port is not a positive integer, or a value is wider than the
            `RDB-Data` field that must carry it
            [copybooks/wsfnctn.cob:L56-L62].
    """
    source: Mapping[str, str] = os.environ if env is None else env

    required = (_ENV_HOST, _ENV_PORT, _ENV_NAME, _ENV_USER, _ENV_PASSWORD)
    missing = [
        name for name in required if not (source.get(name) or "").strip()
    ]
    if missing:
        raise ConnectionConfigError(
            f"the database environment is incomplete: "
            f"{', '.join(missing)} must be set and non-empty. "
            f"harness/docker-compose.yml defines all of them for the "
            f"gnucobol service [L680-L685], and "
            f"harness/reset_db.sh requires the same five "
            f"[L335-L341]. {_ENV_SOCKET} may be empty, which means "
            f"connect over TCP."
        )

    port_text = source[_ENV_PORT].strip()
    if not port_text.isdigit() or int(port_text) < 1 or int(port_text) > 65535:
        raise ConnectionConfigError(
            f"{_ENV_PORT} must be a decimal port number between 1 and "
            f"65535; got {port_text!r}. The Compose service sets "
            f'{_ENV_PORT}: "3306" [harness/docker-compose.yml:L681].'
        )

    settings = ConnectionSettings(
        host=source[_ENV_HOST].strip(),
        port=int(port_text),
        database=source[_ENV_NAME].strip(),
        user=source[_ENV_USER].strip(),
        password=source[_ENV_PASSWORD],
        socket=(source.get(_ENV_SOCKET) or "").strip(),
    )

    # The COBOL side cannot carry a wider value, so a wider one here would
    # make the two sides of the comparison connect differently - and two
    # dumps taken as different users are not comparable. The offending
    # VALUE is never echoed; only its length and its limit are.
    measured: tuple[tuple[str, str], ...] = (
        (_ENV_NAME, settings.database),
        (_ENV_USER, settings.user),
        (_ENV_PASSWORD, settings.password),
        (_ENV_HOST, settings.host),
        (_ENV_SOCKET, settings.socket),
        (_ENV_PORT, port_text),
    )
    for name, value in measured:
        limit = _RDB_WIDTHS[name]
        if len(value) > limit:
            raise ConnectionConfigError(
                f"{name} is {len(value)} characters long but the COBOL "
                f"side can carry at most {limit}: the RDB-Data group at "
                f"[copybooks/wsfnctn.cob:L56-L62] declares DB-Schema, "
                f"DB-UName and DB-UPass as pic x(12), DB-Host as x(32), "
                f"DB-Socket as x(64) and DB-Port as x(5). Both sides of "
                f"the comparison must use the same credentials, so use a "
                f"value the bridge can hold."
            )

    return settings


def _import_driver() -> Any:
    """Import the pinned database driver, lazily.

    Returns:
        The `mysql.connector` module.

    Raises:
        DriverUnavailableError: The driver is not importable.
    """
    try:
        import mysql.connector  # noqa: PLC0415 - lazy by design, see above
    except ImportError as exc:
        raise DriverUnavailableError(
            "mysql-connector-python is not importable, so no database "
            "connection can be opened. requirements.txt pins "
            "mysql-connector-python==26.7.0 and "
            "harness/Dockerfile.gnucobol installs that pin set. The pure "
            "functions of this module - render_value, write_dump, "
            "dump_path - do not need it."
        ) from exc
    return mysql.connector


@contextmanager
def connect(
    settings: ConnectionSettings | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Iterator[Any]:
    """Open one read-only connection for the duration of the block.

    The single connection policy both the command line and
    `tests/conftest.py` use, so the two cannot drift apart. No pool, no
    thread, no retry loop and no session state (rule R-3): the server is
    read as `harness/Dockerfile.mariadb` configured it.

    On exit the transaction is released with `rollback()` and the
    connection is closed. `rollback` rather than `commit` because this
    module only ever reads: rolling back a read-only transaction writes
    nothing, and it releases the `REPEATABLE READ` snapshot that the first
    `SELECT` opened when autocommit is off.

    Args:
        settings: Where to connect. Resolved from `env` when omitted.
        env: The environment to resolve from; `os.environ` when omitted.

    Yields:
        An open DB-API connection.

    Raises:
        ConnectionConfigError: The environment is unusable.
        DriverUnavailableError: The pinned driver is not importable.
        DumpError: The server refused the connection. The message names
            the host, port, database and user - NEVER the password.
    """
    resolved = connection_settings(env) if settings is None else settings
    driver = _import_driver()

    # `raw=False` and `use_unicode=True` pin the driver's own conversion
    # rather than leaning on its defaults: DECIMAL must arrive as
    # decimal.Decimal and every integer width as int (rule R-2). No
    # converter class is installed, and no session variable is set. The
    # per-value guard in `render_value` then proves the pinning held.
    connect_kwargs: dict[str, Any] = {
        "host": resolved.host,
        "port": resolved.port,
        "database": resolved.database,
        "user": resolved.user,
        "password": resolved.password,
        "raw": False,
        "use_unicode": True,
    }
    if resolved.socket:
        connect_kwargs["unix_socket"] = resolved.socket

    try:
        connection = driver.connect(**connect_kwargs)
    except Exception as exc:  # driver-specific; re-raised as one of ours
        raise DumpError(
            f"could not connect to the ACAS database as user "
            f"{resolved.user!r} on {resolved.host}:{resolved.port} "
            f"(database {resolved.database!r}): {exc}"
        ) from exc

    try:
        yield connection
    finally:
        # Release the read-only snapshot, then close. Both are guarded:
        # a failure while tidying up must not mask the real error that
        # brought us here.
        try:
            connection.rollback()
        except Exception:  # noqa: BLE001 - tidy-up must not mask a failure
            pass
        try:
            connection.close()
        except Exception:  # noqa: BLE001 - tidy-up must not mask a failure
            pass


def _schema_name(connection: Any) -> str:
    """Return the schema the connection is using.

    Asked of the server rather than taken from the settings, so the
    `information_schema` assertions are made against the schema the rows
    actually come from.

    Args:
        connection: An open DB-API connection.

    Returns:
        The current database name.

    Raises:
        SchemaDriftError: The connection has no default database.
    """
    rows = _query(connection, "SELECT DATABASE()", ())
    name = rows[0][0] if rows and rows[0] else None
    if not name:
        raise SchemaDriftError(
            "the connection has no default database, so the frozen-schema "
            f"assertions cannot be made. Set {_ENV_NAME} (ACASDB)."
        )
    return str(name)


def _query(
    connection: Any,
    statement: str,
    parameters: Sequence[Any],
) -> list[tuple[Any, ...]]:
    """Run one read-only statement and return every row.

    Results are always fully consumed before the cursor is closed, which
    is what keeps a plain unbuffered cursor safe and keeps this module
    free of driver-specific cursor options.

    Args:
        connection: An open DB-API connection.
        statement: A `SELECT`. Nothing else is ever passed.
        parameters: Bound parameters, in the driver's `%s` style.

    Returns:
        The rows, in the order the server returned them.
    """
    cursor = connection.cursor()
    try:
        cursor.execute(statement, tuple(parameters))
        return list(cursor.fetchall())
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
#  THE STRUCTURAL ASSERTIONS  (rules R-2, R-5, R-6)
#
#  Seven checks, all against information_schema, all cheap, run before a
#  single row of a table is read. They exist because Agent Action Plan
#  section 0.6.6's determinism argument RESTS on seven properties of the
#  frozen schema, and a property the comparison depends on should be
#  asserted rather than trusted:
#
#    1. the table exists in the connected schema and is one of the 22
#    2. its primary key is a single column, and the expected one
#    3. its column count matches the frozen declaration
#    4. it carries no secondary index - only PRIMARY
#    5. no column is temporal, AUTO_INCREMENT, or carries a column-level
#       DEFAULT other than the one verified default of
#       [mysql/ACASDB.sql:L1219]
#    6. no column has a floating-point type
#    7. every column is NOT NULL
#
#  A failure means either mysql/ACASDB.sql was modified - which Agent
#  Action Plan section 0.8.1 calls a defect in the migration - or IN_SCOPE
#  is wrong. Either way the run stops rather than producing a dump nobody
#  can trust.
# ---------------------------------------------------------------------------

_COLUMN_QUERY: Final[str] = (
    "SELECT COLUMN_NAME, ORDINAL_POSITION, DATA_TYPE, IS_NULLABLE, "
    "COLUMN_DEFAULT, EXTRA "
    "FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
    "ORDER BY ORDINAL_POSITION"
)

_INDEX_QUERY: Final[str] = (
    "SELECT INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME "
    "FROM information_schema.STATISTICS "
    "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
    "ORDER BY INDEX_NAME, SEQ_IN_INDEX"
)


def assert_table_structure(
    connection: Any,
    table: str,
    *,
    schema: str | None = None,
) -> tuple[str, ...]:
    """Check one table against the frozen schema and return its columns.

    Args:
        connection: An open DB-API connection.
        table: The table to check. Refused unless it is one of the 22.
        schema: The schema to look in; asked of the server when omitted.

    Returns:
        The column names in `ORDINAL_POSITION` order - the order a
        `SELECT *` returns them in, and the order the dump records.

    Raises:
        TableNotInScopeError: `table` is out of scope.
        UnknownTableError: `table` is not a table of the frozen schema.
        SchemaDriftError: Any of the seven assertions failed. The message
            names the table and the specific expectation.
    """
    spec = table_spec(table)
    where = _schema_name(connection) if schema is None else schema

    columns = _query(connection, _COLUMN_QUERY, (where, table))

    # 1. Existence in the connected schema.
    if not columns:
        raise SchemaDriftError(
            f"table `{table}` is declared by mysql/ACASDB.sql at line "
            f"{spec.schema_line} but is not present in schema {where!r}. "
            f"Apply the frozen schema before dumping - "
            f"harness/reset_db.sh does that and re-seeds."
        )

    # 3. Column count. Checked early: a mismatch makes every later
    #    assertion's message misleading.
    if len(columns) != spec.column_count:
        raise SchemaDriftError(
            f"table `{table}` has {len(columns)} column(s) in schema "
            f"{where!r} but mysql/ACASDB.sql declares "
            f"{spec.column_count} at line {spec.schema_line}. The frozen "
            f"schema must not be modified (Agent Action Plan section "
            f"0.8.1); if it truly changed, IN_SCOPE in this module has to "
            f"be re-derived from it."
        )

    names: list[str] = []
    for name, ordinal, data_type, is_nullable, default, extra in columns:
        column = str(name)
        names.append(column)
        kind = str(data_type).lower()

        # 6. No floating-point column (rule R-2, structurally).
        if kind in _FORBIDDEN_FLOAT_TYPES:
            raise SchemaDriftError(
                f"column `{table}`.`{column}` has floating-point type "
                f"{kind!r}. No accounting value may pass through binary "
                f"floating point (rule R-2), and the frozen schema "
                f"declares zero FLOAT, DOUBLE and REAL columns."
            )

        # 5a. No temporal column: one could carry a wall-clock value into
        #     a dump and break the byte-identical guarantee (rule R-6).
        if kind in _FORBIDDEN_TEMPORAL_TYPES:
            raise SchemaDriftError(
                f"column `{table}`.`{column}` has temporal type {kind!r}. "
                f"Agent Action Plan section 0.6.6 records that no in-scope "
                f"table contains one, which is why the dump needs no "
                f"timestamp masking; a temporal column would make two runs "
                f"differ."
            )

        # 7. Every column NOT NULL. Agent Action Plan section 0.6.2: each
        #    bridge load paragraph initialises the host-variable group, so
        #    unset fields become zero or space rather than SQL NULL.
        if str(is_nullable).upper() != "NO":
            raise SchemaDriftError(
                f"column `{table}`.`{column}` is nullable. Every column of "
                f"the frozen schema is declared NOT NULL - "
                f"harness/reset_db.sh asserts the same from the database "
                f"side [L1878-L1891] - because the bridge writes zero or "
                f"space rather than NULL."
            )

        # 5b. AUTO_INCREMENT and generated columns. The only
        #     AUTO_INCREMENT in the whole schema is
        #     `STOCKAUDIT-REC`.`AUDIT-ID`, and that table is out of scope,
        #     so in scope this is a strict prohibition. An unrelated
        #     future EXTRA value is reported on stderr rather than being
        #     fatal, because only these three concerns affect the dump.
        extra_text = str(extra or "")
        lowered = extra_text.lower()
        for marker in _FORBIDDEN_EXTRA_MARKERS:
            if marker in lowered:
                raise SchemaDriftError(
                    f"column `{table}`.`{column}` carries EXTRA "
                    f"{extra_text!r}. Agent Action Plan section 0.6.6 "
                    f"relies on no in-scope column being AUTO_INCREMENT or "
                    f"generated, which is what lets the dump skip "
                    f"surrogate-key remapping."
                )
        if extra_text:
            _progress(
                f"note: `{table}`.`{column}` carries EXTRA {extra_text!r}, "
                f"which the frozen schema does not declare; it does not "
                f"affect the dump, so it is reported rather than fatal."
            )

        # 5c. Column-level DEFAULT. Exactly one exists in the frozen
        #     schema and it is allowed by name and by value; see
        #     KNOWN_COLUMN_DEFAULTS and [mysql/ACASDB.sql:L1219].
        if default is not None:
            allowed = KNOWN_COLUMN_DEFAULTS.get((table, column))
            rendered = str(default)
            if allowed is None or rendered not in allowed:
                raise SchemaDriftError(
                    f"column `{table}`.`{column}` has the column-level "
                    f"DEFAULT {rendered!r}. The frozen schema declares "
                    f"exactly one, `SYSTEM-REC`.`PASS-WORD` DEFAULT '' at "
                    f"[mysql/ACASDB.sql:L1219]; any other one means the "
                    f"schema has drifted from the frozen definition."
                )

        if int(ordinal) != len(names):
            raise SchemaDriftError(
                f"column `{table}`.`{column}` reports ORDINAL_POSITION "
                f"{ordinal} at position {len(names)} of the ordered "
                f"result. The dump records columns in schema ordinal "
                f"order, so a gap would misalign every row."
            )

    indexes = _query(connection, _INDEX_QUERY, (where, table))
    primary: list[str] = []
    secondary: set[str] = set()
    for index_name, _seq, column_name in indexes:
        if str(index_name) == "PRIMARY":
            primary.append(str(column_name))
        else:
            secondary.add(str(index_name))

    # 4. No secondary index. The only ones in the whole schema are three
    #    on `STOCK-REC` and one on `PLPAY-RECrg01`, both out of scope.
    if secondary:
        raise SchemaDriftError(
            f"table `{table}` carries secondary index(es) "
            f"{', '.join(sorted(secondary))}. Agent Action Plan section "
            f"0.6.6 records zero secondary indexes on the in-scope tables, "
            f"which is why ordering by the primary key alone is "
            f"sufficient and deterministic; the schema's only secondary "
            f"indexes belong to the out-of-scope STOCK-REC and "
            f"PLPAY-RECrg01."
        )

    # 2. A single-column primary key, and the expected column.
    if len(primary) != 1:
        raise SchemaDriftError(
            f"table `{table}` has a primary key of {len(primary)} "
            f"column(s) ({', '.join(primary) or 'none'}). Every in-scope "
            f"table has exactly one, which is why the dump needs no "
            f"tie-break; the schema's only composite primary key belongs "
            f"to the out-of-scope PLPAY-RECrg01."
        )
    if primary[0] != spec.primary_key:
        raise SchemaDriftError(
            f"table `{table}` is keyed on `{primary[0]}` but "
            f"mysql/ACASDB.sql declares `{spec.primary_key}` at line "
            f"{spec.schema_line}. Ordering by the wrong column would "
            f"reorder every row of the dump."
        )

    return tuple(names)


# ---------------------------------------------------------------------------
#  VALUE RENDERING  (rules R-2 and R-4)
#
#  A TYPE DISPATCH, NOT A TRANSFORMATION. Nothing here trims, pads,
#  rounds, re-scales or reformats: that is harness/normalize.py's job and
#  keeping it there is what makes a non-empty diff a real behavioural
#  difference rather than an artefact of the comparison.
#
#  What it does do is REFUSE. A float, a non-finite Decimal, a bool, a
#  NULL or an unrecognised type each raise, naming the table, the column
#  and the value, because every one of them means something upstream is
#  wrong and coercing it would hide that.
# ---------------------------------------------------------------------------

# The one encoding choice this module makes, and it is documented rather
# than implicit. All 33 tables are `DEFAULT CHARSET=utf8mb3`, a strict
# subset of UTF-8, so decoding a bytes value as UTF-8 is lossless. It is
# decoded STRICTLY - never with errors="replace" - because a byte sequence
# that is not valid UTF-8 could not have come from these tables and is
# genuinely new information.
_BYTES_ENCODING: Final[str] = "utf-8"


def render_value(value: object, *, table: str, column: str) -> str | int:
    """Render one fetched value for the dump, or refuse it.

    Args:
        value: The value the driver returned.
        table: The table it came from, for the error messages.
        column: The column it came from, for the error messages.

    Returns:
        `int` for every integer width the schema uses, or `str` for a
        `DECIMAL` (rendered with `format(value, "f")`, so the declared
        scale survives and exponent notation can never appear) and for
        character data (exactly as the driver returned it, unpadded and
        untrimmed).

    Raises:
        NumericPolicyError: `value` is a `float`, or a non-finite
            `Decimal`. Rule R-2 forbids binary floating point outright,
            and this module raises rather than rounding.
        UnexpectedValueTypeError: `value` is a `bool`, undecodable bytes,
            or a type no in-scope column can hold.
        UnexpectedNullError: `value` is `None`, which a schema declaring
            every column NOT NULL cannot legitimately produce.
    """
    # bool BEFORE int: bool is a subclass of int, and JSON `true` is not
    # the integer a tinyint column holds. No column can produce one, so
    # its appearance means the driver was reconfigured.
    if isinstance(value, bool):
        raise UnexpectedValueTypeError(
            f"`{table}`.`{column}` returned a bool ({value!r}). The dump "
            f"records integers as JSON integers; a bool would serialise "
            f"as true/false and no longer match the stored value. No "
            f"in-scope column can produce one."
        )

    # THE R-2 GUARD. A float here means the driver was configured wrongly,
    # and silently rounding it would destroy the exactness the whole
    # engagement rests on. The frozen schema declares zero FLOAT, DOUBLE
    # and REAL columns, so this is unreachable with the pinned driver -
    # which is exactly why it is an assertion and not a conversion.
    if isinstance(value, float):
        raise NumericPolicyError(
            f"`{table}`.`{column}` returned a binary floating-point value "
            f"({value!r}). No accounting value may pass through binary "
            f"floating point at any point (rule R-2). The frozen schema "
            f"declares zero FLOAT, DOUBLE and REAL columns and the pinned "
            f"driver returns DECIMAL as decimal.Decimal, so this means the "
            f"driver's type conversion was overridden. Nothing is coerced "
            f"here."
        )

    if isinstance(value, int):
        return value

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise NumericPolicyError(
                f"`{table}`.`{column}` returned the non-finite decimal "
                f"{value!r}. A DECIMAL column cannot hold NaN or infinity, "
                f"and neither has a faithful JSON rendering."
            )
        # `format(v, "f")` and not `str(v)`: str would render
        # Decimal("1E+2") in exponent notation, which no consumer of this
        # dump should have to parse. Trailing zeros are NOT stripped - the
        # declared scale is part of what is being captured, and scale
        # canonicalisation belongs to harness/normalize.py.
        return format(value, "f")

    if isinstance(value, str):
        return value

    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        try:
            return raw.decode(_BYTES_ENCODING)
        except UnicodeDecodeError as exc:
            raise UnexpectedValueTypeError(
                f"`{table}`.`{column}` returned {len(raw)} byte(s) that are "
                f"not valid {_BYTES_ENCODING}. All 33 tables are declared "
                f"DEFAULT CHARSET=utf8mb3, a strict subset of UTF-8, so a "
                f"value that will not decode cannot have come from them. "
                f"It is reported rather than replaced."
            ) from exc

    if value is None:
        raise UnexpectedNullError(
            f"`{table}`.`{column}` returned NULL, but every column of the "
            f"frozen schema is declared NOT NULL. Agent Action Plan "
            f"section 0.6.2: each bridge load paragraph initialises the "
            f"host-variable group, 'so unset fields become zero or space "
            f"rather than SQL NULL'. A NULL here is genuinely new "
            f"information and is reported, not rendered."
        )

    raise UnexpectedValueTypeError(
        f"`{table}`.`{column}` returned {type(value).__name__} "
        f"({value!r}), which no in-scope column can hold. The schema's "
        f"types are CHAR, DECIMAL and the integer widths TINYINT, "
        f"SMALLINT, MEDIUMINT, INT and BIGINT."
    )


# ---------------------------------------------------------------------------
#  THE DUMP
#
#      SELECT * FROM `<table>` ORDER BY `<primary key>`
#
#  and nothing more. No secondary sort, no tie-break, no client-side
#  re-ordering, no row filtering, no repair. Agent Action Plan section
#  0.4.1.7 specifies exactly this statement for exactly these 22 tables.
# ---------------------------------------------------------------------------


def dump_table(
    connection: Any,
    table: str,
    *,
    schema: str | None = None,
) -> dict[str, Any]:
    """Capture one table's full state as a dump object.

    Args:
        connection: An open DB-API connection.
        table: One of the 22 in-scope tables.
        schema: The schema to assert against; asked of the server when
            omitted.

    Returns:
        The dump object: `table`, `primary_key`, `columns`, `row_count`
        and `rows`, in that insertion order and with no other key.

    Raises:
        TableNotInScopeError: `table` is out of scope.
        UnknownTableError: `table` is not a table of the frozen schema.
        SchemaDriftError: A structural assertion failed, or the columns a
            `SELECT *` returned disagree with `information_schema`.
        NumericPolicyError: The rule R-2 value guard tripped.
        UnexpectedValueTypeError: A value had a type no column can hold.
        UnexpectedNullError: A NULL was fetched.
    """
    spec = table_spec(table)
    declared = assert_table_structure(connection, table, schema=schema)

    statement = (
        f"SELECT * FROM {_ident(table)} ORDER BY {_ident(spec.primary_key)}"
    )

    cursor = connection.cursor()
    try:
        cursor.execute(statement)
        # `columns` comes from the cursor description, which is the
        # table's declared order, and is NEVER sorted.
        description = cursor.description or ()
        columns = tuple(str(field[0]) for field in description)
        fetched = list(cursor.fetchall())
    finally:
        cursor.close()

    # The map cannot silently drift (rule R-5): what SELECT * returned is
    # compared with what information_schema declares, name for name and
    # position for position.
    if columns != declared:
        raise SchemaDriftError(
            f"`SELECT *` on `{table}` returned columns "
            f"{list(columns)} but information_schema declares "
            f"{list(declared)} in ordinal order. The dump aligns every row "
            f"positionally with the column list, so it cannot proceed on a "
            f"disagreement."
        )
    if len(columns) != spec.column_count:
        raise SchemaDriftError(
            f"`SELECT *` on `{table}` returned {len(columns)} column(s) but "
            f"mysql/ACASDB.sql declares {spec.column_count} at line "
            f"{spec.schema_line}."
        )

    rows: list[list[str | int]] = [
        [
            render_value(value, table=table, column=columns[position])
            for position, value in enumerate(row)
        ]
        for row in fetched
    ]

    for index, row in enumerate(rows):
        if len(row) != len(columns):
            raise SchemaDriftError(
                f"row {index} of `{table}` has {len(row)} value(s) for "
                f"{len(columns)} column(s); values are aligned with "
                f"`columns` by position, so the row cannot be recorded."
            )

    dump: dict[str, Any] = {
        "table": table,
        "primary_key": spec.primary_key,
        "columns": list(columns),
        "row_count": len(rows),
        "rows": rows,
    }

    # `row_count` is a convenience for a human reading a diff. It is
    # derived, so it is asserted rather than assumed.
    if dump["row_count"] != len(dump["rows"]):
        raise SchemaDriftError(  # pragma: no cover - unreachable by design
            f"row_count {dump['row_count']} does not equal the "
            f"{len(dump['rows'])} row(s) recorded for `{table}`."
        )

    return dump


def dump_tables(
    connection: Any,
    tables: Sequence[str],
    *,
    schema: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Capture several tables, one after another on the one connection.

    STRICTLY SEQUENTIAL (rule R-3): a plain loop, in the order given, on
    one connection. No thread, no pool, no batching. With autocommit off -
    which `harness/Dockerfile.mariadb` sets at server level - the whole
    loop reads from the single `REPEATABLE READ` snapshot the first
    `SELECT` opened, so the tables are mutually consistent.

    Args:
        connection: An open DB-API connection.
        tables: The tables to dump, in the order to dump them. Duplicates
            are refused rather than dumped twice.
        schema: The schema to assert against; resolved once when omitted.

    Returns:
        A mapping of table name to dump object, in the order dumped.

    Raises:
        UnknownTableError: A name is not a table of the frozen schema, or
            appears more than once.
        TableNotInScopeError: A name is out of scope.
        SchemaDriftError: A structural assertion failed.
        NumericPolicyError: The rule R-2 value guard tripped.
    """
    ordered = tuple(tables)
    seen: set[str] = set()
    for name in ordered:
        if name in seen:
            raise UnknownTableError(
                f"table {name!r} was requested more than once; each table "
                f"is dumped to one file, so a repeat is a mistake."
            )
        seen.add(name)

    where = _schema_name(connection) if schema is None else schema

    dumps: dict[str, dict[str, Any]] = {}
    for name in ordered:
        dumps[name] = dump_table(connection, name, schema=where)
    return dumps


# ---------------------------------------------------------------------------
#  SERIALISATION  (rule R-6)
#
#  The bytes are the product. Every parameter below is pinned rather than
#  left to a default, because the acceptance criterion of Agent Action
#  Plan section 0.8.5 is that two runs produce BYTE-IDENTICAL dumps.
#
#  ensure_ascii=True is deliberate: it makes the output bytes independent
#  of any locale or filesystem-encoding difference between the two runs.
#  Do not "improve" it to False.
# ---------------------------------------------------------------------------

_JSON_INDENT: Final[int] = 2
_JSON_SEPARATORS: Final[tuple[str, str]] = (",", ": ")

# One file per table, named for the table exactly as the schema spells it.
_DUMP_SUFFIX: Final[str] = ".json"

# The temporary name a dump is written under before `os.replace` moves it
# into place, so a partial write can never be compared. It is created in
# the SAME directory as its target, which is what makes the replace atomic.
_TEMP_PREFIX: Final[str] = "."
_TEMP_SUFFIX: Final[str] = ".json.tmp"


def dump_path(
    out: Path | str,
    table: str,
    *,
    scenario: str | None = None,
    side: str | None = None,
) -> Path:
    """Build the path a table's dump is written to.

    Both layouts this repository documents are supported:

        <out>/<scenario>/<side>/<TABLE>.json    scenario and side given
        <out>/<TABLE>.json                      neither given

    The second is the form the committed Compose file publishes as the
    canonical eight-stage recipe, `harness/dump_tables.py --out /out/cobol`
    [harness/docker-compose.yml:L268].

    Args:
        out: The output directory, or the root under which
            `<scenario>/<side>/` is composed.
        table: One of the 22 in-scope tables.
        scenario: The scenario name. Must be given with `side`.
        side: `cobol` or `python`. Must be given with `scenario`.

    Returns:
        The path, with no directory created.

    Raises:
        UnknownTableError: `table` is not a table of the frozen schema.
        TableNotInScopeError: `table` is out of scope.
        ValueError: `scenario` and `side` were not both given or both
            omitted, `side` is not one of `SIDES`, or `scenario` contains
            a path separator.
    """
    table_spec(table)

    if (scenario is None) != (side is None):
        raise ValueError(
            "scenario and side belong together: give both, for the "
            "<out-dir>/<scenario>/<side>/ layout, or neither, for the "
            "<out>/ layout of [harness/docker-compose.yml:L268]."
        )

    directory = Path(out)
    if scenario is not None and side is not None:
        if side not in SIDES:
            raise ValueError(
                f"side must be one of {', '.join(SIDES)}; got {side!r}. The "
                f"two sides of the comparison are the compiled COBOL oracle "
                f"and the Python cycle."
            )
        if not scenario or scenario in {".", ".."} or (
            set(scenario) & set("/\\")
        ):
            raise ValueError(
                f"scenario must be a plain directory name, not a path; got "
                f"{scenario!r}. It names a scenario such as "
                f"clean_batch_gl."
            )
        directory = directory / scenario / side

    return directory / f"{table}{_DUMP_SUFFIX}"


def write_dump(dump: Mapping[str, Any], path: Path | str) -> Path:
    """Serialise one dump object to `path`, deterministically and atomically.

    The five keys are written in `DUMP_KEYS` order, `indent=2`,
    `ensure_ascii=True`, `sort_keys=False`, separators `(",", ": ")`, LF
    newlines, UTF-8, and exactly one trailing newline. The file is written
    under a temporary name in the same directory and moved into place with
    `os.replace`, so `harness/normalize.py` can never read a partial file.

    Args:
        dump: A dump object, as `dump_table` returns.
        path: Where to write it. Parent directories are created.

    Returns:
        The path written.

    Raises:
        ValueError: `dump` does not carry exactly the five expected keys
            in the expected order, or `row_count` disagrees with `rows`.
        DumpWriteError: The file could not be written or moved.
    """
    keys = tuple(dump.keys())
    if keys != DUMP_KEYS:
        raise ValueError(
            f"a dump object must carry exactly the keys "
            f"{list(DUMP_KEYS)} in that order; got {list(keys)}. The key "
            f"order is part of the byte-identical guarantee (rule R-6), and "
            f"no other key may appear - not a timestamp, a server version "
            f"or a connection detail."
        )
    if dump["row_count"] != len(dump["rows"]):
        raise ValueError(
            f"row_count {dump['row_count']!r} does not equal the "
            f"{len(dump['rows'])} row(s) of table "
            f"{dump['table']!r}."
        )

    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DumpWriteError(
            f"could not create the output directory {target.parent}: {exc}"
        ) from exc

    temporary = target.parent / f"{_TEMP_PREFIX}{target.stem}{_TEMP_SUFFIX}"
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(
                dump,
                handle,
                indent=_JSON_INDENT,
                ensure_ascii=True,
                sort_keys=False,
                separators=_JSON_SEPARATORS,
            )
            # json.dump writes no trailing newline. Exactly one is added,
            # so every dump file ends the same way.
            handle.write("\n")
        os.replace(temporary, target)
    except OSError as exc:
        # Leave nothing half-written behind for normalize.py to read.
        try:
            temporary.unlink(missing_ok=True)
        except OSError:  # noqa: S110 - best effort; the real error follows
            pass
        raise DumpWriteError(
            f"could not write the dump for table {dump['table']!r} to "
            f"{target}: {exc}"
        ) from exc

    return target


def write_dumps(
    dumps: Mapping[str, Mapping[str, Any]],
    out: Path | str,
    *,
    scenario: str | None = None,
    side: str | None = None,
) -> tuple[Path, ...]:
    """Serialise several dump objects, one file each, sequentially.

    Args:
        dumps: A mapping of table name to dump object, as `dump_tables`
            returns.
        out: The output directory, or the root for the composed layout.
        scenario: The scenario name, for the composed layout.
        side: `cobol` or `python`, for the composed layout.

    Returns:
        The paths written, in the order written.

    Raises:
        ValueError: A dump object is malformed, or the layout arguments
            are inconsistent.
        DumpWriteError: A file could not be written.
    """
    written: list[Path] = []
    for table, dump in dumps.items():
        target = dump_path(out, table, scenario=scenario, side=side)
        written.append(write_dump(dump, target))
    return tuple(written)


# ---------------------------------------------------------------------------
#  THE TABLE LIST
#
#  Bound the comparison by the SCENARIO's affected-table list, not by
#  everything. There is a concrete reason, and it is a menu-shell side
#  effect: [general/general.cbl:L656-L691] rewrites SYSTEM-REC,
#  SYSDEFLT-REC and SYSTOT-REC to both the relational database and the
#  COBOL file when the operator leaves the menu with `X`. The Python
#  command line has no menu and performs no such rewrite, so comparing
#  those tables in a scenario that does not affect them would produce a
#  FALSE FAILURE.
#
#  SYSTOT-REC is genuinely in scope for the period-end scenario - Agent
#  Action Plan section 0.6.4 identifies nine period-total write sites,
#  "the sole writers of the totals record" - so the overlap is real and
#  belongs in docs/migration/ambiguity-resolutions.md rather than being
#  papered over here.
# ---------------------------------------------------------------------------


def scenario_tables(path: Path | str) -> tuple[str, ...]:
    """Read a scenario's affected-table list.

    Agent Action Plan section 0.4.1.7 specifies that each
    `harness/scenarios/*.yaml` carries "Seed data, inputs and the
    affected-table list per scenario". This reads that one list and
    nothing else: no seed data is interpreted and no input is validated,
    because interpreting a scenario's declared contents would be exactly
    the added validation rule R-3 forbids - which is the same reason
    `harness/seed.sh` accepts a scenario file without parsing it
    [harness/seed.sh:L1805-L1818].

    Either spelling of the key is accepted, `affected_tables` or
    `affected-tables`, but not both in one file.

    Args:
        path: The scenario definition to read.

    Returns:
        The table names, in the order the scenario lists them.

    Raises:
        ScenarioFileError: The file is missing, unreadable, not a mapping,
            carries neither key or both, or the list is empty or holds
            something that is not a table name.
        TableNotInScopeError: The list names an out-of-scope table.
        UnknownTableError: The list names something that is not a table.
    """
    try:
        import yaml  # noqa: PLC0415 - lazy, so the module imports without it
    except ImportError as exc:
        raise ScenarioFileError(
            "PyYAML is not importable, so a scenario definition cannot be "
            "read. requirements.txt pins PyYAML==6.0.3. Pass --tables "
            "instead to name the tables directly."
        ) from exc

    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScenarioFileError(
            f"could not read the scenario definition {source}: {exc}. The "
            f"canonical invocation passes a path such as "
            f"harness/scenarios/clean_batch_gl.yaml "
            f"[harness/docker-compose.yml:L266-L267]."
        ) from exc

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ScenarioFileError(
            f"the scenario definition {source} is not valid YAML: {exc}"
        ) from exc

    if not isinstance(document, Mapping):
        raise ScenarioFileError(
            f"the scenario definition {source} must be a mapping at the top "
            f"level; got {type(document).__name__}."
        )

    present = [key for key in _SCENARIO_TABLE_KEYS if key in document]
    if not present:
        raise ScenarioFileError(
            f"the scenario definition {source} carries no affected-table "
            f"list. Add one under {_SCENARIO_TABLE_KEYS[0]} (or "
            f"{_SCENARIO_TABLE_KEYS[1]}) naming the tables the scenario "
            f"affects, as Agent Action Plan section 0.4.1.7 specifies. "
            f"Alternatively pass --tables to name them on the command line."
        )
    if len(present) > 1:
        raise ScenarioFileError(
            f"the scenario definition {source} carries both "
            f"{present[0]} and {present[1]}. They mean the same thing, so "
            f"exactly one must be used."
        )

    declared = document[present[0]]
    if isinstance(declared, str) or not isinstance(declared, Sequence):
        raise ScenarioFileError(
            f"{present[0]} in {source} must be a list of table names; got "
            f"{type(declared).__name__}."
        )
    if not declared:
        raise ScenarioFileError(
            f"{present[0]} in {source} is empty. A scenario that affects no "
            f"table has nothing to compare; name at least one."
        )

    names: list[str] = []
    for entry in declared:
        if not isinstance(entry, str):
            raise ScenarioFileError(
                f"{present[0]} in {source} contains "
                f"{type(entry).__name__} ({entry!r}); every entry must be a "
                f"table name."
            )
        table_spec(entry)
        if entry in names:
            raise ScenarioFileError(
                f"{present[0]} in {source} names table {entry!r} more than "
                f"once."
            )
        names.append(entry)

    return tuple(names)


def resolve_tables(
    *,
    tables: str | None = None,
    scenario_file: Path | str | None = None,
    all_in_scope: bool = False,
) -> tuple[str, ...]:
    """Resolve the command line's table selectors into a table list.

    Exactly one selector may be given. When none is, every in-scope table
    is dumped, in name order - which is what the Compose file's
    `harness/dump_tables.py --out /out/cobol` [L268] asks for - and the
    caller is expected to warn, because bounding a comparison by the
    scenario is the protocol.

    Args:
        tables: A comma-separated list of table names.
        scenario_file: A scenario definition to read the list from.
        all_in_scope: Dump all 22 explicitly.

    Returns:
        The table names, in the order to dump them.

    Raises:
        ValueError: More than one selector was given, or `tables` is empty
            or names a table twice.
        ScenarioFileError: The scenario definition is unusable.
        TableNotInScopeError: A named table is out of scope.
        UnknownTableError: A named table is not a table of the schema.
    """
    chosen = [
        name
        for name, given in (
            ("--tables", tables is not None),
            ("--scenario-file", scenario_file is not None),
            ("--all-in-scope", bool(all_in_scope)),
        )
        if given
    ]
    if len(chosen) > 1:
        raise ValueError(
            f"{' and '.join(chosen)} were all given; they are alternative "
            f"ways of choosing the same list, so use exactly one."
        )

    if scenario_file is not None:
        return scenario_tables(scenario_file)

    if tables is not None:
        names = [part.strip() for part in tables.split(",")]
        names = [name for name in names if name]
        if not names:
            raise ValueError(
                "--tables was given but names no table. Pass a "
                "comma-separated list such as "
                "GLBATCH-REC,GLLEDGER-REC,GLPOSTING-REC."
            )
        resolved: list[str] = []
        for name in names:
            table_spec(name)
            if name in resolved:
                raise ValueError(
                    f"--tables names {name!r} more than once; each table is "
                    f"dumped to one file."
                )
            resolved.append(name)
        return tuple(resolved)

    # --all-in-scope, or nothing at all: the 22, in name order.
    return IN_SCOPE_TABLES


# ---------------------------------------------------------------------------
#  THE COMMAND LINE
#
#  Progress goes to STDERR only. Nothing is printed to stdout that could be
#  mistaken for data, and nothing at all is written into the output
#  directory except the <TABLE>.json files themselves, because
#  harness/normalize.py reads that directory
#  [harness/docker-compose.yml:L269].
#
#  `main` RETURNS an exit code and never calls sys.exit, so
#  tests/conftest.py can drive it in process.
# ---------------------------------------------------------------------------

_EPILOGUE: Final[str] = """\
layouts
  --scenario NAME --side {cobol|python} [--out-dir DIR]
      writes <DIR>/<NAME>/<side>/<TABLE>.json   (DIR defaults to $ACAS_OUT)
  --out DIR
      writes <DIR>/<TABLE>.json                 the form the canonical
      eight-stage recipe uses [harness/docker-compose.yml:L268]

environment
  ACAS_DB_HOST  ACAS_DB_PORT  ACAS_DB_NAME  ACAS_DB_USER  ACAS_DB_PASSWORD
  must be set and non-empty; ACAS_DB_SOCKET may be empty, meaning TCP.
  ACAS_OUT supplies the default for --out-dir. Credentials are never
  logged and never reach a dump file. The COBOL side cannot carry a
  database name, user or password longer than 12 characters, nor a host
  longer than 32 [copybooks/wsfnctn.cob:L56-L62].

exit codes
  0 dumped   80 usage   81 precondition   82 database
  83 scope    84 schema drift             85 numeric   86 write

this tool issues SELECT only, on one connection, sequentially, and writes
no byte of non-reproducible content: two runs against the same state
produce byte-identical files.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    `allow_abbrev=False` so that `--out` and `--out-dir` can never be
    confused with one another, and so no abbreviation of any option is
    silently accepted.

    Returns:
        The parser.
    """
    parser = argparse.ArgumentParser(
        prog="harness/dump_tables.py",
        allow_abbrev=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Capture ACAS posting-cycle table state deterministically: "
            "SELECT * FROM <table> ORDER BY <primary key> for the 22 "
            "in-scope tables of mysql/ACASDB.sql, one JSON file per table. "
            "Stages 3 and 7 of the eight-stage parity protocol."
        ),
        epilog=_EPILOGUE,
    )

    parser.add_argument(
        "--scenario",
        metavar="NAME",
        help=(
            "the scenario name, used only to build the output path "
            "<out-dir>/<scenario>/<side>/. Requires --side."
        ),
    )
    parser.add_argument(
        "--side",
        choices=SIDES,
        help=(
            "which side of the comparison this dump represents. Requires "
            "--scenario. The side is recorded in the PATH, never in a file."
        ),
    )
    parser.add_argument(
        "--out-dir",
        metavar="DIR",
        help=(
            "the root under which <scenario>/<side>/ is composed; defaults "
            "to $ACAS_OUT."
        ),
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        help=(
            "write <TABLE>.json directly into DIR. The form the canonical "
            "eight-stage recipe uses [harness/docker-compose.yml:L268]. "
            "Cannot be combined with --scenario, --side or --out-dir."
        ),
    )

    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--tables",
        metavar="TABLE[,TABLE...]",
        help=(
            "the explicit table list, comma separated, spelled exactly as "
            "mysql/ACASDB.sql spells it, hyphens included."
        ),
    )
    selection.add_argument(
        "--scenario-file",
        metavar="PATH",
        help=(
            "read the affected-table list from a harness/scenarios/*.yaml, "
            "under the key affected_tables (or affected-tables). This is "
            "the protocol: a comparison is bounded by the scenario."
        ),
    )
    selection.add_argument(
        "--all-in-scope",
        action="store_true",
        help=(
            "DEBUGGING AID, NOT THE PROTOCOL. Dumps all 22 in-scope tables. "
            "Bound a real comparison by the scenario's affected-table list "
            "instead: [general/general.cbl:L656-L691] rewrites SYSTEM-REC, "
            "SYSDEFLT-REC and SYSTOT-REC to both the relational database "
            "and the COBOL file when the operator leaves the menu with X, "
            "and the Python command line has no menu and performs no such "
            "rewrite, so comparing those tables in a scenario that does not "
            "affect them produces a FALSE FAILURE."
        ),
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress the per-table progress notes on stderr.",
    )

    return parser


def _resolve_output(
    arguments: argparse.Namespace,
    env: Mapping[str, str],
) -> tuple[Path, str | None, str | None]:
    """Work out where the dumps go.

    Args:
        arguments: The parsed command line.
        env: The environment, for `$ACAS_OUT`.

    Returns:
        The output root, the scenario name and the side. The last two are
        `None` for the `--out DIR` layout.

    Raises:
        ValueError: The layout arguments are contradictory or incomplete.
    """
    if arguments.out is not None:
        conflicting = [
            name
            for name, value in (
                ("--scenario", arguments.scenario),
                ("--side", arguments.side),
                ("--out-dir", arguments.out_dir),
            )
            if value is not None
        ]
        if conflicting:
            raise ValueError(
                f"--out names the output directory outright, so it cannot be "
                f"combined with {' or '.join(conflicting)}. Use either "
                f"`--out DIR` [harness/docker-compose.yml:L268] or "
                f"`--scenario NAME --side SIDE [--out-dir DIR]`."
            )
        return Path(arguments.out), None, None

    if arguments.scenario is None or arguments.side is None:
        raise ValueError(
            "give either `--out DIR`, or `--scenario NAME --side "
            f"{{{'|'.join(SIDES)}}}` for the "
            "<out-dir>/<scenario>/<side>/ layout. --scenario and --side "
            "belong together."
        )

    root = arguments.out_dir
    if root is None:
        root = env.get(_ENV_OUT)
    if not root:
        raise ValueError(
            f"neither --out-dir nor {_ENV_OUT} is set, so the output root is "
            f"unknown. The Compose service sets {_ENV_OUT}: /out "
            f"[harness/docker-compose.yml:L689]."
        )
    return Path(root), arguments.scenario, arguments.side


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return an exit code.

    Never calls `sys.exit`, so a test can drive it in process and inspect
    the code. Every failure is reported on stderr with the reason and the
    locator a reader would need, and mapped to one of the documented exit
    codes.

    Args:
        argv: The arguments; `sys.argv[1:]` when omitted.

    Returns:
        `EX_OK` on success, or one of `EX_USAGE`, `EX_PRECONDITION`,
        `EX_DATABASE`, `EX_SCOPE`, `EX_DRIFT`, `EX_NUMERIC`, `EX_WRITE`.
    """
    global _QUIET

    parser = build_parser()
    arguments = parser.parse_args(argv)
    _QUIET = bool(arguments.quiet)
    env: Mapping[str, str] = os.environ

    try:
        out, scenario, side = _resolve_output(arguments, env)
    except ValueError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_USAGE

    bounded = (
        arguments.tables is not None
        or arguments.scenario_file is not None
        or arguments.all_in_scope
    )
    try:
        tables = resolve_tables(
            tables=arguments.tables,
            scenario_file=arguments.scenario_file,
            all_in_scope=arguments.all_in_scope,
        )
    except (TableNotInScopeError, UnknownTableError) as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_SCOPE
    except ScenarioFileError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_PRECONDITION
    except ValueError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_USAGE

    if not bounded:
        # The Compose invocation gives no selector, so this path has to
        # work - but it is not the protocol, and saying so costs nothing.
        _progress(
            "note: no table selector given, so all "
            f"{len(IN_SCOPE_TABLES)} in-scope tables will be dumped. A real "
            "comparison should be bounded by the scenario's affected-table "
            "list (--scenario-file): [general/general.cbl:L656-L691] "
            "rewrites SYSTEM-REC, SYSDEFLT-REC and SYSTOT-REC on menu exit "
            "and the Python cycle has no menu, so an unbounded comparison "
            "can fail on a side effect the migration does not reproduce."
        )

    try:
        settings = connection_settings(env)
    except ConnectionConfigError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_PRECONDITION

    # The settings are safe to echo: __repr__ redacts the password.
    _progress(
        f"harness/dump_tables.py: SELECT * ORDER BY primary key for "
        f"{len(tables)} table(s) via {settings}"
    )

    try:
        with connect(settings) as connection:
            schema = _schema_name(connection)
            written: list[Path] = []
            total_rows = 0
            for table in tables:
                dump = dump_table(connection, table, schema=schema)
                target = dump_path(
                    out, table, scenario=scenario, side=side
                )
                written.append(write_dump(dump, target))
                total_rows += int(dump["row_count"])
                _progress(
                    f"  {table:<24} {dump['row_count']:>7} row(s)  "
                    f"{len(dump['columns']):>3} column(s)  -> {target}"
                )
    except DriverUnavailableError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_PRECONDITION
    except (TableNotInScopeError, UnknownTableError) as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_SCOPE
    except SchemaDriftError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_DRIFT
    except (
        NumericPolicyError,
        UnexpectedValueTypeError,
        UnexpectedNullError,
    ) as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_NUMERIC
    except DumpWriteError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_WRITE
    except ValueError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_USAGE
    except DumpError as exc:
        print(f"harness/dump_tables.py: {exc}", file=sys.stderr)
        return EX_DATABASE

    _progress(
        f"harness/dump_tables.py: wrote {len(written)} file(s), "
        f"{total_rows} row(s) in total, under {out}"
    )
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
